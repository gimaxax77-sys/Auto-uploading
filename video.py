# 대본을 받아 이미지 + 내레이션 슬라이드쇼 영상을 만드는 도구
import asyncio
import glob
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile

import edge_tts
import imageio_ffmpeg
import requests
from dotenv import load_dotenv

from generate import write_script

load_dotenv()

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
MUSIC_DIR = "music"  # 여기에 배경음악 파일을 넣으면 자동으로 깔립니다.
MUSIC_VOLUME = 0.35  # 배경음악 음량(0~1). 내레이션이 잘 들리도록 작게.
# 대본 번호대로 배경음악 무드를 자동 배정합니다. music/<무드>/ 폴더의 곡을 씁니다.
# 아래에 없는 번호는 전부 "밝은"으로 갑니다. 폴더가 비면 music/ 공용에서 뽑습니다.
MOOD_WOONGJANG = (set(range(81, 86)) | set(range(96, 101)) | set(range(106, 116))
                  | set(range(131, 136)) | set(range(156, 176)))  # 명소·우주·자연·과학·경이·극한장소
MOOD_CHABUN = (set(range(1, 21)) | set(range(25, 31)) | set(range(36, 41))
               | set(range(46, 56)) | set(range(61, 66)) | set(range(76, 81)) | set(range(91, 96)))  # 동기부여·위로·감성
SUBTITLE = True  # 내레이션 문장을 자막으로 넣습니다.
FONT = "C:/Windows/Fonts/malgunbd.ttf"  # 맑은 고딕 굵게 (가독성)
FONT_SIZE = 90
WRAP = 12  # 한 줄 최대 글자 수. 넘으면 다음 줄로 넘깁니다.
SUB_TOP = 200  # 자막 위쪽 여백(px). 화면 상단에 배치합니다.
SUB_LAG = 0.1  # 단어별 자막 하이라이트를 소리보다 이 초만큼 늦춥니다(어긋남 보정).
LINE_SPACING = 4  # 줄 간격(px). 작을수록 줄이 붙습니다.
# 배경 밝기에 따라 고르는 자막 색. 밝으면 노란 글씨, 어두우면 흰 글씨+초록 테두리.
STYLE_BRIGHT = "fontcolor=yellow:borderw=6:bordercolor=black:shadowcolor=black@0.7:shadowx=3:shadowy=3"
STYLE_DARK = "fontcolor=white:borderw=6:bordercolor=0x00aa00:shadowcolor=black@0.7:shadowx=3:shadowy=3"
BRIGHT_THRESHOLD = 128  # 자막 영역 평균 밝기가 이 값보다 크면 밝은 배경으로 봅니다.
# 장면마다 이 순서로 번갈아 씁니다. 하나만 두면 그 음성만 씁니다.
VOICES = ["ko-KR-SunHiNeural", "ko-KR-InJoonNeural"]
# 음성 엔진: "edge"(무료) 또는 "google"(Neural2, 더 자연스러움, GOOGLE_TTS_API_KEY 필요).
TTS_ENGINE = "google"
# edge 음성 → 구글 음성 대응(여자/남자).
GOOGLE_VOICE_MAP = {"ko-KR-SunHiNeural": "ko-KR-Neural2-A", "ko-KR-InJoonNeural": "ko-KR-Neural2-C"}
RATE = "+25%"  # 내레이션 속도. +로 빠르게, -로 느리게 (예: "-10%").
RATE_LAST = "+8%"  # 마지막 장면(마무리)은 차분하게 느린 속도로 읽습니다.
GAP = 0.3  # 장면 사이 여백(초). 넘어갈 때 숨 쉬는 틈을 줍니다.
GAP_LAST = 0.8  # 마지막 장면 뒤 여백. 끝맺음이 급하지 않게 여운을 줍니다.
SIZE = (1080, 1920)  # 세로형 쇼츠
BROLL = True  # 켜면 장면마다 Pexels 세로 영상(B-roll)을 먼저 쓰고, 없으면 사진으로 폴백.

# 화면 연출효과 (입자 제외 전부)
EFFECTS = True  # False 로 두면 효과 없이 정지 사진으로 만듭니다.
ZOOM_END = 1.12  # 켄번즈: 장면 동안 이만큼 확대(1.0=없음).
DARKEN = 0.05  # 사진을 이만큼 어둡게(0~1). 자막 가독성 향상.
VIGNETTE = "PI/5"  # 가장자리 어둡게(비네팅) 강도.
SUB_FADE = 0.4  # 자막이 나타나는 시간(초).
XFADE = 0.4  # 장면 전환 겹침 시간(초).
FPS = 30


def read_script(path: str) -> list[dict]:
    """대본 파일을 읽습니다. 한 줄이 한 장면이고, 세로줄(|) 뒤는 이미지 검색어입니다."""
    scenes = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):  # 빈 줄과 # 로 시작하는 줄은 건너뜁니다.
                continue
            narration, _, query = line.partition("|")
            scenes.append({
                "narration": narration.strip(),
                "image_query": query.strip(),
            })
    if not scenes:
        raise ValueError(f"{path} 에서 읽을 장면이 없습니다.")
    return scenes


async def _narrate_async(text: str, path: str, voice: str, rate: str) -> list[tuple[float, float, str]]:
    """음성을 저장하면서 단어별 (시작초, 길이초, 단어) 목록을 모읍니다."""
    comm = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
    words = []
    with open(path, "wb") as f:
        async for ch in comm.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                words.append((ch["offset"] / 1e7, ch["duration"] / 1e7, ch["text"]))
    return words


def narrate_google(text: str, path: str, voice: str, rate: str) -> list[tuple[float, float, str]]:
    """구글 TTS(v1beta1)로 음성을 만들고 SSML 마크로 단어 타이밍을 받아옵니다."""
    import base64
    key = os.environ["GOOGLE_TTS_API_KEY"]
    gvoice = GOOGLE_VOICE_MAP.get(voice, "ko-KR-Neural2-A")
    speaking_rate = max(0.25, min(4.0, 1.0 + int(rate.replace("%", "").replace("+", "")) / 100))
    toks = text.split()

    def esc(s: str) -> str:  # SSML 특수문자 이스케이프
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    chirp = "Chirp" in gvoice  # Chirp 계열은 SSML 마크/타임포인트 미지원 → 평문 + 길이비례 추정
    body = {"voice": {"languageCode": "ko-KR", "name": gvoice},
            "audioConfig": {"audioEncoding": "MP3", "speakingRate": speaking_rate}}
    if chirp:
        body["input"] = {"text": text}
    else:
        ssml = "<speak>" + "".join(f'<mark name="w{i}"/>{esc(t)} ' for i, t in enumerate(toks))
        ssml += f'<mark name="w{len(toks)}"/></speak>'  # 마지막 단어의 끝 시각용
        body["input"] = {"ssml": ssml}
        body["enableTimePointing"] = ["SSML_MARK"]
    r = requests.post(
        f"https://texttospeech.googleapis.com/v1beta1/text:synthesize?key={key}",
        json=body, timeout=60,
    )
    r.raise_for_status()
    j = r.json()
    with open(path, "wb") as f:
        f.write(base64.b64decode(j["audioContent"]))
    starts = [tp["timeSeconds"] for tp in j.get("timepoints", [])]
    if len(starts) >= len(toks) + 1:  # 정확한 단어 타이밍(Neural2 등)
        return [(starts[i], max(0.05, starts[i + 1] - starts[i]), t) for i, t in enumerate(toks)]
    # 타임포인트 없음(Chirp): 실제 오디오 길이를 글자 수 비례로 나눠 추정합니다.
    total = media_duration(path)
    clen = sum(len(t) for t in toks) or 1
    words, acc = [], 0.0
    for t in toks:
        d = total * len(t) / clen
        words.append((acc, max(0.05, d), t))
        acc += d
    return words


def narrate(text: str, path: str, voice: str = VOICES[0], rate: str = RATE) -> list[tuple[float, float, str]]:
    """문장을 음성 파일로 만들고, 단어별 타이밍 목록을 돌려줍니다."""
    if TTS_ENGINE == "google" and os.environ.get("GOOGLE_TTS_API_KEY"):
        return narrate_google(text, path, voice, rate)
    return asyncio.run(_narrate_async(text, path, voice, rate))


def fetch_image(query: str, path: str) -> None:
    """검색어에 맞는 무료 스톡 사진을 내려받습니다."""
    res = requests.get(
        "https://api.pexels.com/v1/search",
        headers={"Authorization": os.environ["PEXELS_API_KEY"]},
        params={"query": query, "per_page": 1, "orientation": "portrait"},
        timeout=30,
    )
    res.raise_for_status()
    photos = res.json()["photos"]
    if not photos:
        raise ValueError(f"'{query}' 로 찾은 사진이 없습니다. 검색어를 바꿔보십시오.")
    with open(path, "wb") as f:
        f.write(requests.get(photos[0]["src"]["large2x"], timeout=60).content)


def fetch_video(query: str, path: str) -> bool:
    """검색어에 맞는 무료 세로 스톡 영상을 내려받습니다. 없으면 False(→사진 폴백)."""
    res = requests.get(
        "https://api.pexels.com/videos/search",
        headers={"Authorization": os.environ["PEXELS_API_KEY"]},
        params={"query": query, "per_page": 5, "orientation": "portrait"},
        timeout=30,
    )
    res.raise_for_status()
    best = None  # (점수, 링크). 세로이면서 1920 높이에 가까운 것을 고릅니다.
    for v in res.json().get("videos", []):
        for vf in v.get("video_files", []):
            wd, ht = vf.get("width") or 0, vf.get("height") or 0
            if ht <= wd or ht < 1000:  # 가로거나 너무 저해상도면 제외
                continue
            score = abs(ht - 1920) + (10000 if ht > 2600 else 0)  # 4K는 뒤로
            if best is None or score < best[0]:
                best = (score, vf["link"])
    if not best:
        return False
    with open(path, "wb") as f:
        f.write(requests.get(best[1], timeout=120).content)
    return True


def make_background(index: int, path: str) -> None:
    """Pexels 키가 없을 때 쓰는 대체 배경. 장면마다 색을 바꿉니다."""
    w, h = SIZE
    hue = (index * 47) % 360  # 장면마다 충분히 다른 색이 나오도록 47도씩 돌립니다.
    subprocess.run(
        [FFMPEG, "-y", "-f", "lavfi",
         "-i", f"color=c=gray:s={w}x{h}",
         "-vf", f"hue=h={hue}:s=1.4,gblur=sigma=40",
         "-frames:v", "1", path],
        check=True,
        capture_output=True,
    )


def wrap_text(text: str, width: int) -> str:
    """쉼표·마침표 뒤에서 줄을 나누고, 긴 줄은 띄어쓰기 기준으로 줄바꿈합니다."""
    lines = []
    # 쉼표(,)와 마침표(.) 뒤에서 줄을 끊습니다.
    for sentence in re.split(r"(?<=[,.])\s+", text.strip()):
        sentence = sentence.strip()
        if not sentence:
            continue
        line = ""
        for word in sentence.split():
            candidate = f"{line} {word}".strip()
            if len(candidate) > width and line:
                lines.append(line)
                line = word
            else:
                line = candidate
        if line:
            lines.append(line)
    return "\n".join(lines)


def image_brightness(image: str) -> int:
    """자막이 놓일 상단 영역의 평균 밝기(0~255)를 잽니다."""
    # 상단 45% 만 잘라 1픽셀로 줄이면 그 한 바이트가 평균 밝기입니다.
    r = subprocess.run(
        [FFMPEG, "-i", image, "-vf", "crop=iw:ih*0.45:0:0,scale=1:1",
         "-f", "rawvideo", "-pix_fmt", "gray", "-"],
        capture_output=True,
    )
    return r.stdout[0] if r.stdout else 128


def subtitle_style(image: str) -> str:
    """배경 밝기에 맞는 자막 색 스타일을 고릅니다."""
    return STYLE_BRIGHT if image_brightness(image) > BRIGHT_THRESHOLD else STYLE_DARK


def media_duration(path: str) -> float:
    """오디오/영상 파일의 길이(초)를 ffmpeg 출력에서 읽습니다."""
    info = subprocess.run([FFMPEG, "-i", path], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", info)
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def ass_time(t: float) -> str:
    """초를 ASS 시간표기 h:mm:ss.cs(센티초)로 바꿉니다."""
    cs = max(0, round(t * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


# 단어별 자막 스타일: 안 부른 단어=흰색, 부른 단어=노란색(굵은 검은 테두리로 어디서든 잘 보임).
_ASS_HEADER = (
    "[Script Info]\nScriptType: v4.00+\n"
    f"PlayResX: {SIZE[0]}\nPlayResY: {SIZE[1]}\nWrapStyle: 0\n\n"
    "[V4+ Styles]\n"
    "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
    "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
    "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
    f"Style: Def,Malgun Gothic,{FONT_SIZE},&H0000FFFF,&H00FFFFFF,&H00000000,&H80000000,"
    f"-1,0,0,0,100,100,0,0,1,6,2,8,80,80,{SUB_TOP},1\n\n"
    "[Events]\n"
    "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
)


def build_ass(words: list[tuple[float, float, str]], duration: float, path: str) -> None:
    """단어 타이밍으로 노래방식(부르는 단어가 노랗게 채워지는) ASS 자막을 만듭니다."""
    parts = [f"{{\\fad({int(SUB_FADE * 1000)},{int(SUB_FADE * 1000)})}}"]
    if SUB_LAG > 0:  # 하이라이트를 소리보다 살짝 늦춰 어긋남을 줄입니다.
        parts.append(f"{{\\kf{round(SUB_LAG * 100)}}} ")
    prev_end = 0.0
    for start, dur, word in words:
        gap_cs = round(max(0.0, start - prev_end) * 100)
        if gap_cs:  # 단어 사이 침묵만큼 하이라이트를 미룹니다.
            parts.append(f"{{\\kf{gap_cs}}} ")
        parts.append(f"{{\\kf{max(1, round(dur * 100))}}}{word} ")
        prev_end = start + dur
    text = "".join(parts).rstrip()
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(_ASS_HEADER)
        f.write(f"Dialogue: 0,{ass_time(0)},{ass_time(duration)},Def,,0,0,0,,{text}\n")


def render_clip(image: str | None, audio: str, out: str, subtitle: str = "", gap: float = GAP,
                words: list[tuple[float, float, str]] | None = None,
                video: str | None = None) -> None:
    """사진 한 장(또는 B-roll 영상)과 음성 하나를 붙여 장면 하나를 만듭니다."""
    w, h = SIZE
    duration = media_duration(audio) + gap  # 이 장면의 총 길이
    frames = max(1, round(duration * FPS))

    if video:
        # B-roll 영상: 실제 움직임이 있으니 켄번즈(zoompan) 없이 화면에 꽉 채우기만 합니다.
        vf = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}"
        if EFFECTS:
            vf += f",eq=brightness=-{DARKEN},vignette={VIGNETTE}"  # 어둡게 + 비네팅
    elif EFFECTS:
        # 켄번즈: 사진을 크게 키운 뒤 천천히 확대(zoompan)합니다.
        step = (ZOOM_END - 1.0) / frames
        vf = (
            f"scale={w * 2}:{h * 2}:force_original_aspect_ratio=increase,crop={w * 2}:{h * 2},"
            f"zoompan=z='min(zoom+{step:.6f},{ZOOM_END})':d={frames}"
            f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={FPS},"
            f"eq=brightness=-{DARKEN},vignette={VIGNETTE}"  # 어둡게 + 비네팅
        )
    else:
        vf = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}"

    subtitle_file = None
    if SUBTITLE and subtitle and words:
        # 단어별 자막: 단어 타이밍으로 ASS 자막을 만들어 ass 필터로 렌더합니다.
        subtitle_file = out + ".ass"
        build_ass(words, duration, subtitle_file)
        af = subtitle_file.replace("\\", "/").replace(":", "\\:")
        vf += f",ass='{af}'"
    elif SUBTITLE and subtitle:
        # (폴백) 단어 타이밍이 없으면 기존 통짜 자막을 씁니다.
        subtitle_file = out + ".txt"
        # newline="\n" 로 저장해야 윈도우식 \r\n 때문에 줄 사이가 벌어지지 않습니다.
        with open(subtitle_file, "w", encoding="utf-8", newline="\n") as f:
            f.write(wrap_text(subtitle, WRAP))
        font = FONT.replace(":", "\\:")  # 드라이브 문자 뒤 콜론 이스케이프
        tf = subtitle_file.replace("\\", "/").replace(":", "\\:")
        # 배경 밝기에 맞춰 색 선택. 영상 소스면 잴 이미지가 없어 어두운 배경용을 씁니다.
        style = subtitle_style(image) if image else STYLE_DARK
        # 자막이 나타날 때 페이드인, 장면 끝에서 페이드아웃 되어
        # 다음 장면 자막과 부드럽게 교체됩니다.
        fade = (
            f":alpha='min(1\\,min(t/{SUB_FADE}\\,({duration:.3f}-t)/{SUB_FADE}))'"
            if EFFECTS else ""
        )
        vf += (
            f",drawtext=fontfile='{font}':textfile='{tf}'"
            f":fontsize={FONT_SIZE}:{style}"
            f":line_spacing={LINE_SPACING}:x=(w-tw)/2:y={SUB_TOP}{fade}"
        )

    # 영상은 장면 길이에 맞게 반복(-stream_loop), 사진은 정지 반복(-loop 1).
    src = ["-stream_loop", "-1", "-i", video] if video else ["-loop", "1", "-i", image]
    try:
        subprocess.run(
            [
                FFMPEG, "-y", *src, "-i", audio,
                "-map", "0:v", "-map", "1:a",  # 영상은 0번, 내레이션은 1번에서
                "-vf", vf,
                # 음성 끝에 gap 초 만큼 무음을 붙여 장면 사이에 여백을 줍니다.
                "-af", f"apad=pad_dur={gap}",
                "-t", f"{duration:.3f}",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
                "-c:a", "aac", out,
            ],
            check=True,
            capture_output=True,
        )
    finally:
        if subtitle_file and os.path.exists(subtitle_file):
            os.remove(subtitle_file)


def fetch_music_jamendo(path: str) -> str:
    """Jamendo 에서 무료 음악 하나를 받고, 출처 표기 문구를 돌려줍니다."""
    res = requests.get(
        "https://api.jamendo.com/v3.0/tracks",
        params={
            "client_id": os.environ["JAMENDO_CLIENT_ID"],
            "format": "json",
            "limit": 1,
            "audioformat": "mp32",
            "order": "popularity_total",
            "tags": "instrumental",  # 가사 없는 곡이 배경음악에 어울립니다.
            "vocalinstrumental": "instrumental",
        },
        timeout=30,
    )
    res.raise_for_status()
    tracks = res.json()["results"]
    if not tracks:
        raise ValueError("Jamendo 에서 음악을 찾지 못했습니다.")
    t = tracks[0]
    with open(path, "wb") as f:
        f.write(requests.get(t["audio"], timeout=120).content)
    return f"음악: {t['name']} - {t['artist_name']} (Jamendo, CC BY)"


def mood_of(out: str) -> str:
    """출력 파일명 앞 번호로 배경음악 무드를 정합니다. 예: 01_아침.mp4 -> 차분"""
    m = re.match(r"(\d+)", os.path.basename(out))
    n = int(m.group(1)) if m else 0
    if n in MOOD_WOONGJANG:
        return "웅장"
    if n in MOOD_CHABUN:
        return "차분"
    return "밝은"


def voice_of(out: str) -> str:
    """영상 번호로 음성 하나로 통일. 홀수 편=여자(SunHi), 짝수 편=남자(InJoon)."""
    m = re.match(r"(\d+)", os.path.basename(out))
    n = int(m.group(1)) if m else 0
    return VOICES[0] if n % 2 == 1 else VOICES[1]


def pick_music(path: str, mood: str | None = None) -> str | None:
    """배경음악을 준비합니다. 무드 폴더 우선 → 공용 폴더 → Jamendo. 출처 문구를 돌려줍니다."""
    files = []
    if mood:  # music/<무드>/ 폴더에 곡이 있으면 그 안에서만 고릅니다.
        d = os.path.join(MUSIC_DIR, mood)
        files = glob.glob(os.path.join(d, "*.mp3")) + glob.glob(os.path.join(d, "*.m4a"))
    if not files:  # 무드 폴더가 비면 공용 music/ 에서 뽑습니다(끊기지 않게).
        files = glob.glob(os.path.join(MUSIC_DIR, "*.mp3")) + glob.glob(os.path.join(MUSIC_DIR, "*.m4a"))
    if files:
        chosen = random.choice(files)
        subprocess.run([FFMPEG, "-y", "-i", chosen, "-c", "copy", path],
                       check=True, capture_output=True)
        return None  # 내가 넣은 음악이니 출처 표기 불필요
    if os.environ.get("JAMENDO_CLIENT_ID"):
        return fetch_music_jamendo(path)
    return None  # 음악 없음


def add_music(video: str, music: str, out: str) -> None:
    """영상에 배경음악을 작게 깝니다. 음악이 길면 영상 길이에 맞춰 자릅니다."""
    subprocess.run(
        [FFMPEG, "-y", "-i", video, "-i", music,
         # 내레이션은 그대로, 음악은 MUSIC_VOLUME 으로 줄여 섞습니다.
         "-filter_complex",
         # normalize=0: 자동 감쇠를 꺼서 내레이션은 원래 크기, 음악만 MUSIC_VOLUME 로.
         f"[1:a]volume={MUSIC_VOLUME}[bg];[0:a][bg]amix=inputs=2:duration=first:normalize=0[a]",
         "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", out],
        check=True,
        capture_output=True,
    )


def concat(clips: list[str], out: str) -> None:
    """장면들을 그대로(전환 없이) 이어붙입니다."""
    listfile = os.path.join(os.path.dirname(clips[0]), "clips.txt")
    with open(listfile, "w", encoding="utf-8", newline="\n") as f:
        for c in clips:
            f.write(f"file '{os.path.basename(c)}'\n")
    subprocess.run(
        [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", listfile, "-c", "copy", out],
        check=True,
        capture_output=True,
    )


def concat_xfade(clips: list[str], out: str, t: float = XFADE) -> None:
    """장면들을 크로스페이드로 부드럽게 이어붙입니다."""
    if len(clips) == 1:
        shutil.copy(clips[0], out)
        return
    durs = [media_duration(c) for c in clips]
    inputs = []
    for c in clips:
        inputs += ["-i", c]

    v_filters, a_filters = [], []
    vlabel, alabel = "0:v", "0:a"
    acc = durs[0]
    for i in range(1, len(clips)):
        offset = acc - t
        vout, aout = f"v{i}", f"a{i}"
        v_filters.append(
            f"[{vlabel}][{i}:v]xfade=transition=fade:duration={t}:offset={offset:.3f}[{vout}]"
        )
        a_filters.append(f"[{alabel}][{i}:a]acrossfade=d={t}[{aout}]")
        vlabel, alabel = vout, aout
        acc += durs[i] - t

    filter_complex = ";".join(v_filters + a_filters)
    subprocess.run(
        [FFMPEG, "-y", *inputs, "-filter_complex", filter_complex,
         "-map", f"[{vlabel}]", "-map", f"[{alabel}]",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", out],
        check=True,
        capture_output=True,
    )


def make_video(scenes: list[dict], out: str) -> str:
    """장면 목록을 받아 완성된 영상 파일을 만듭니다."""
    # 키가 없거나 검색어가 비어 있으면 사진 대신 단색 배경을 씁니다.
    use_photos = bool(os.environ.get("PEXELS_API_KEY"))
    if not use_photos:
        print("  (PEXELS_API_KEY 가 없어 대체 배경을 씁니다)")

    voice = voice_of(out)  # 한 영상은 한 음성으로 통일(홀수 편=여자, 짝수 편=남자).
    with tempfile.TemporaryDirectory() as work:
        clips = []
        for i, scene in enumerate(scenes):
            audio = os.path.join(work, f"{i}.mp3")
            image = os.path.join(work, f"{i}.jpg")
            broll = os.path.join(work, f"{i}_b.mp4")
            clip = os.path.join(work, f"{i}.mp4")
            last = i == len(scenes) - 1  # 마지막 장면(마무리)
            query = scene["image_query"]
            print(f"  장면 {i + 1}/{len(scenes)} [{voice.split('-')[-1]}]: {scene['narration'][:24]}...")
            words = narrate(scene["narration"], audio, voice, RATE_LAST if last else RATE)
            gap = GAP_LAST if last else GAP

            video_src = None
            if BROLL and use_photos and query:
                try:  # 영상 먼저 시도. 실패하면 사진으로 폴백.
                    if fetch_video(query, broll):
                        video_src = broll
                except Exception as e:
                    print(f"    (B-roll 실패, 사진으로 대체: {e})")

            if video_src:
                render_clip(None, audio, clip, scene["narration"], gap, words, video=video_src)
            else:
                if use_photos and query:
                    fetch_image(query, image)
                else:
                    make_background(i, image)
                render_clip(image, audio, clip, scene["narration"], gap, words)
            clips.append(clip)

        joined = os.path.join(work, "joined.mp4")
        # 효과가 켜져 있으면 크로스페이드로, 아니면 그대로 이어붙입니다.
        (concat_xfade if EFFECTS else concat)(clips, joined)

        # 배경음악을 준비해 깝니다. 없으면 그대로 둡니다.
        music = os.path.join(work, "bgm.mp3")
        credit = pick_music(music, mood_of(out))
        if os.path.exists(music):
            add_music(joined, music, out)
            if credit:
                print(f"  {credit}")
        else:
            shutil.copy(joined, out)  # 임시폴더가 다른 드라이브일 수 있어 copy 사용
    return out


def main() -> None:
    if len(sys.argv) < 2:
        print("사용법: python video.py \"주제\" [장면수]      (AI가 대본 작성)")
        print("        python video.py --file 대본.txt      (대본 파일 사용)")
        sys.exit(1)

    if sys.argv[1] == "--file":
        scenes = read_script(sys.argv[2])
        print(f"대본 {len(scenes)}장면을 읽었습니다.")
    else:
        print("대본을 쓰는 중...")
        scenes = write_script(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 5)

    print("영상을 만드는 중...")
    print(f"\n완성: {make_video(scenes, 'out.mp4')}")


if __name__ == "__main__":
    main()

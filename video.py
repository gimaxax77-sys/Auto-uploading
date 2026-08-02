# 대본을 받아 이미지 + 내레이션 슬라이드쇼 영상을 만드는 도구
import asyncio
import functools
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
                  | set(range(131, 136)) | set(range(156, 206)))  # 명소·우주·자연·과학·경이·극한·바다·식물
MOOD_CHABUN = (set(range(1, 21)) | set(range(25, 31)) | set(range(36, 41))
               | set(range(46, 56)) | set(range(61, 66)) | set(range(76, 81)) | set(range(91, 96)))  # 동기부여·위로·감성
SUBTITLE = True  # 내레이션 문장을 자막으로 넣습니다.
FONT = "C:/Windows/Fonts/H2HDRM.TTF"  # HY헤드라인. 폭이 좁아 한 줄에 더 들어갑니다.
FONT_NAME = "HYHeadLine-Medium"  # ASS 자막이 참조하는 폰트 이름(시스템에 설치된 이름과 같아야 함)
FONT_SIZE = 90
WRAP = 12  # 한 줄 최대 글자 수. 넘으면 다음 줄로 넘깁니다.
SUB_TOP = 200  # 자막 위쪽 여백(px). 화면 상단에 배치합니다.
SUB_LAG = 0.1  # 단어별 자막 하이라이트를 소리보다 이 초만큼 늦춥니다(어긋남 보정).
LINE_SPACING = 4  # 줄 간격(px). 작을수록 줄이 붙습니다.
# ASS 스타일에는 행간 항목이 없어 libass 가 폰트 line-height 를 그대로 씁니다. HY헤드라인은
# 한글이 네모칸을 꽉 채워 줄이 붙어 버립니다(실측 여백 2px). 그래서 줄마다 Dialogue 를 따로
# 쓰고 이 간격으로 직접 내립니다. 글자 88px 기준으로 36px 가 뜹니다.
SUB_LINE_PITCH = 124
# 배경 밝기에 따라 고르는 자막 색. 밝으면 노란 글씨, 어두우면 흰 글씨+초록 테두리.
STYLE_BRIGHT = "fontcolor=yellow:borderw=6:bordercolor=black:shadowcolor=black@0.7:shadowx=3:shadowy=3"
STYLE_DARK = "fontcolor=white:borderw=6:bordercolor=0x00aa00:shadowcolor=black@0.7:shadowx=3:shadowy=3"
BRIGHT_THRESHOLD = 128  # 자막 영역 평균 밝기가 이 값보다 크면 밝은 배경으로 봅니다.
EMPHASIS_SIZE = 240  # 강조 문구(핵심 숫자) 글자 크기. 대본 3번째 칸에 적으면 화면 가운데 뜹니다.
EMPHASIS_PITCH = 1.22  # 강조 문구 줄 간격(글자 크기 배수). 1.0 이면 줄이 맞닿습니다.
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
# 마지막(반전) 장면 전용 연출. 앞 장면들과 달라야 반전이 반전으로 읽힙니다.
CLIMAX_CUT = 0.08   # 반전 진입은 크로스페이드 대신 사실상 하드컷.
CLIMAX_ZOOM = 0.10  # 켄번즈 확대량을 이만큼 더 줍니다(밀고 들어가는 느낌).
CLIMAX_DARKEN = 0.06  # 배경을 이만큼 더 어둡게 해 강조 문구만 남깁니다.
# 장면 전환 종류. 편 번호로 골라 편마다 다르게 넘어갑니다(전편 같은 fade 면 템플릿 티가 납니다).
# squeezev 는 이 ffmpeg 에서 해상도와 무관하게 죽으므로 절대 넣지 마십시오.
TRANSITIONS = [
    "circleopen", "circleclose", "vertopen", "vertclose", "horzopen", "horzclose", "radial",
    "diagtl", "diagtr", "diagbl", "diagbr",
    "smoothleft", "smoothright", "smoothup", "smoothdown",
    "fade", "fadefast", "fadeslow",
]
TRANSITION = TRANSITIONS[0]  # make_video 가 편 번호에 맞춰 바꿉니다.
FPS = 30


def read_script(path: str) -> list[dict]:
    """대본 파일을 읽습니다. 한 줄이 한 장면이고, 세로줄(|) 뒤는 이미지 검색어입니다."""
    scenes = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):  # 빈 줄과 # 로 시작하는 줄은 건너뜁니다.
                continue
            # 문장 | 검색어 | 강조문구(선택). 강조문구는 화면 가운데에 크게 박힙니다.
            narration, _, rest = line.partition("|")
            query, _, emphasis = rest.partition("|")
            scenes.append({
                "narration": narration.strip(),
                "image_query": query.strip(),
                "emphasis": emphasis.strip(),
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


# 카드 배경 팔레트(위/아래 색). 편 번호로 골라 편마다 다른 색이 나오게 합니다.
# 프레임 덧입히기 — 2026-07-28 현재 어느 대본에도 쓰지 않습니다(Gim 지시로 보류).
# 되살리려면 대본 검색어 앞에 "@frame " 을 붙이면 됩니다. 배경은 사진으로 받고
# 그 위에 테두리·무늬를 얹으며, 켄번즈는 자동으로 꺼집니다. 경위는 research.md 참고.
FRAME_MARK = "@frame"


def 사진_톤(img) -> tuple[int, int, int]:
    """사진에서 화면을 대표하는 색을 뽑습니다. 프레임 색을 여기에 맞춥니다."""
    import colorsys

    작게 = img.convert("RGB").resize((48, 48))
    화소 = list(작게.getdata())
    # 회색에 가까운 픽셀은 톤을 대표하지 못하므로 채도가 있는 쪽에 무게를 둡니다.
    뽑기 = sorted(화소, key=lambda p: (max(p) - min(p)) * (sum(p) / 3 + 40), reverse=True)
    상위 = 뽑기[:len(뽑기) // 6] or 화소
    r, g, b = (sum(c[i] for c in 상위) / len(상위) / 255 for i in range(3))
    hue, _, _ = colorsys.rgb_to_hsv(r, g, b)
    # 사진과 같은 계열이되 밝고 옅게 — 위에 얹혀도 사진을 죽이지 않습니다.
    return tuple(round(c * 255) for c in colorsys.hsv_to_rgb(hue, 0.28, 0.97))


def apply_frame(path: str, seed: int) -> None:
    """배경 사진 위에 무늬와 테두리를 덧입힙니다(사진은 그대로 비칩니다).

    배경을 통째로 갈아 끼우면 정보량이 줄어들어, 실사를 남기고 그 위에 얹습니다.
    무늬 색은 사진에서 뽑아 톤을 맞춥니다.
    """
    from PIL import Image, ImageDraw, ImageFilter

    w, h = SIZE
    바탕 = Image.open(path).convert("RGB").resize((w, h))
    톤 = 사진_톤(바탕)

    # 1) 무늬 — 화면 전체에 옅게. 편마다 종류가 달라지도록 씨앗으로 고릅니다.
    무늬 = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(무늬)
    선 = 톤 + (72,)
    FRAME_PATTERNS[seed % len(FRAME_PATTERNS)](d, w, h, 선)
    바탕 = Image.alpha_composite(바탕.convert("RGBA"),
                                무늬.filter(ImageFilter.GaussianBlur(0.8))).convert("RGB")

    # 2) 위아래를 어둡게 눌러 자막과 강조 글씨가 뜨게 만듭니다.
    그늘 = Image.new("L", (1, h), 0)
    px = 그늘.load()
    for y in range(h):
        t = y / (h - 1)
        px[0, y] = round(112 * max(0.0, 1 - t / 0.32) + 96 * max(0.0, (t - 0.64) / 0.36))
    바탕 = Image.composite(Image.new("RGB", (w, h), (0, 0, 0)), 바탕,
                          그늘.resize((w, h), Image.BILINEAR))

    # 3) 테두리 — 이중선에 네 모서리 강조. 화면에 '틀'을 만들어 줍니다.
    d = ImageDraw.Draw(바탕)
    m, m2 = 46, 68
    d.rectangle([m, m, w - m, h - m], outline=톤, width=6)
    d.rectangle([m2, m2, w - m2, h - m2], outline=톤, width=2)
    for x, y in ((m, m), (w - m, m), (m, h - m), (w - m, h - m)):
        sx = 1 if x == m else -1
        sy = 1 if y == m else -1
        d.line([(x, y), (x + 96 * sx, y)], fill=톤, width=14)
        d.line([(x, y), (x, y + 96 * sy)], fill=톤, width=14)
    바탕.save(path, quality=93)


def _무늬_동심원(d, w, h, 선):
    cx, cy = w // 2, int(h * 0.44)
    for r in range(170, 1500, 135):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=선, width=5)


def _무늬_사선(d, w, h, 선):
    for x in range(-h, w + h, 104):
        d.line([(x, 0), (x + h, h)], fill=선, width=5)


def _무늬_격자(d, w, h, 선):
    for y in range(0, h, 100):
        d.line([(0, y), (w, y)], fill=선, width=4)
    for x in range(0, w, 100):
        d.line([(x, 0), (x, h)], fill=선, width=4)


def _무늬_점(d, w, h, 선):
    for y in range(56, h, 104):
        for x in range(56, w, 104):
            d.ellipse([x - 8, y - 8, x + 8, y + 8], fill=선)


def _무늬_역사선(d, w, h, 선):
    for x in range(-h, w + h, 104):
        d.line([(x + h, 0), (x, h)], fill=선, width=5)


def _무늬_수직(d, w, h, 선):
    for x in range(0, w, 88):
        d.line([(x, 0), (x, h)], fill=선, width=5)


FRAME_PATTERNS = [_무늬_동심원, _무늬_사선, _무늬_격자, _무늬_점, _무늬_역사선, _무늬_수직]


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
    # WrapStyle 2 = 자동 줄바꿈 없음. libass 는 한글을 CJK 로 보아 어절 한가운데서도
    # 줄을 끊습니다("같은 만 / 원인데"). 그래서 자동 줄바꿈을 끄고 우리가 \N 을 넣습니다.
    f"PlayResX: {SIZE[0]}\nPlayResY: {SIZE[1]}\nWrapStyle: 2\n\n"
    "[V4+ Styles]\n"
    "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
    "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
    "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
    f"Style: Def,{FONT_NAME},{FONT_SIZE},&H0000FFFF,&H00FFFFFF,&H00000000,&H80000000,"
    f"-1,0,0,0,100,100,0,0,1,6,2,8,80,80,{SUB_TOP},1\n"
    # 강조 문구용. 화면 가운데에 큰 노란 글씨로 박아 스크롤을 멈추게 합니다.
    f"Style: Big,{FONT_NAME},{EMPHASIS_SIZE},&H0000D5FF,&H00FFFFFF,&H00000000,&H80000000,"
    "-1,0,0,0,100,100,0,0,1,10,4,5,60,60,60,1\n\n"
    "[Events]\n"
    "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
)


@functools.lru_cache(maxsize=8)
def _잰폰트(size: int):
    from PIL import ImageFont
    return ImageFont.truetype(FONT, size)


def 글자폭(text: str, size: int) -> int:
    """실제 폰트로 잰 글자 폭(px). 줄바꿈 지점을 정하는 데 씁니다."""
    bb = _잰폰트(size).getbbox(text)
    return (bb[2] - bb[0]) if bb else 0


단위 = ("원", "개", "년", "배", "도", "초", "분", "시간", "미터", "킬로", "살", "층", "회",
        "번", "자", "명", "마리", "퍼센트", "기압", "cm", "m", "km", "kg", "℃", "%")
기호 = (">", "<", "→", "←", "↔", "=", "vs", "·", "~")


def 어절_묶기(어절들: list[str]) -> list[str]:
    """갈라지면 어색한 어절을 한 덩어리로 붙입니다.

    "같은 만 원인데" 를 "같은" + "만 원인데" 로 묶어, 금액이 두 줄로 찢기지 않게 합니다.
    ">" 같은 기호는 앞뒤를 통째로 묶습니다.
    """
    덩어리: list[str] = []
    for w in 어절들:
        앞 = 덩어리[-1] if 덩어리 else ""
        수사끝 = bool(re.search(r"[\d만천억조십백]$", 앞))
        if 앞 and (
            w in 기호                                    # 기호는 앞과 붙인다
            or (앞.split()[-1] in 기호)                   # 기호 다음 어절도 함께
            or (수사끝 and w.startswith(단위))            # 숫자·수사 + 단위
        ):
            덩어리[-1] = f"{앞} {w}"
        else:
            덩어리.append(w)
    return 덩어리


def 어절_줄나눔(어절들: list[str], 최대폭: int, size: int) -> list[list[str]]:
    """공백으로 끊긴 어절만으로 줄을 나눕니다. 어절 한가운데서는 절대 끊지 않습니다."""
    줄, 현재 = [], []
    for w in 어절들:
        if 현재 and 글자폭(" ".join(현재 + [w]), size) > 최대폭:
            줄.append(현재)
            현재 = [w]
        else:
            현재.append(w)
    if 현재:
        줄.append(현재)
    return 줄


EMPHASIS_MIN = 96   # 강조 문구 최소 글자 크기
EMPHASIS_LINES = 2  # 강조 문구는 최대 이 줄 수까지만 허용합니다.


def 강조_배치(text: str) -> tuple[str, int]:
    """강조 문구를 두 줄 안에 들어가는 가장 큰 글자 크기로 배치합니다.

    240pt 로는 한글이 한 줄에 서너 자밖에 안 들어가 긴 문구가 네 줄로 쪼개집니다.
    문구 길이에 따라 크기를 낮춰 두 줄 안에 담고, 줄은 어절 경계에서만 끊습니다.
    """
    최대폭 = SIZE[0] - 120 - 30  # 좌우 여백 60씩, 굵게 처리로 번지는 몫 30
    어절 = 어절_묶기(text.split())
    size = EMPHASIS_SIZE
    while size > EMPHASIS_MIN:
        줄 = 어절_줄나눔(어절, 최대폭, size)
        # 줄 수뿐 아니라 각 줄이 화면 폭 안에 들어가는지도 봐야 합니다. 묶은 덩어리는
        # 쪼갤 수 없어서, 폭을 안 보면 화면 밖으로 삐져나갑니다.
        if len(줄) <= EMPHASIS_LINES and all(글자폭(" ".join(x), size) <= 최대폭 for x in 줄):
            break
        size -= 8
    줄 = 어절_줄나눔(어절, 최대폭, size)
    return "\\N".join(" ".join(x) for x in 줄), size


def build_ass(words: list[tuple[float, float, str]], duration: float, path: str,
              emphasis: str = "", climax: bool = False) -> None:
    """단어 타이밍으로 노래방식(부르는 단어가 노랗게 채워지는) ASS 자막을 만듭니다.

    줄마다 Dialogue 를 따로 씁니다. ASS 스타일에 행간 항목이 없어 한 Dialogue 안에서
    `\\N` 으로 줄을 나누면 폰트 line-height 그대로 붙어 버리기 때문입니다(실측 여백 2px).

    자막은 전환이 시작되기 전에 걷습니다. 자막을 클립에 구운 뒤 크로스페이드로 잇는 구조라,
    끝까지 남겨 두면 전환 동안 앞뒤 장면 자막이 겹쳐 보입니다.

    다만 **말이 끝나기 전에 걷히면 안 됩니다.** 편에 따라 XFADE(0.25~0.55)가 GAP(0.3)보다
    길어져 그런 일이 생깁니다. 그래서 마지막 단어가 끝날 때까지는 무조건 남깁니다
    (겹침을 조금 감수하더라도 말이 잘리는 쪽이 나쁩니다).
    """
    단어끝 = max((s + d for s, d, _ in words), default=0.0)
    끝 = min(duration, max(단어끝 + 0.15, duration - XFADE))
    줄들 = 어절_줄나눔([w for _, _, w in words], SIZE[0] - 160 - 30, FONT_SIZE)
    # 사라지는 시간은 짧게. 길면 전환에 걸쳐 잔상으로 남습니다.
    페이드 = f"{{\\fad({int(SUB_FADE * 1000)},200)}}"

    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(_ASS_HEADER)
        몫시작 = 0
        for li, 줄 in enumerate(줄들):
            몫, 몫시작 = words[몫시작:몫시작 + len(줄)], 몫시작 + len(줄)
            if not 몫:
                continue
            parts = [페이드]
            대기 = 몫[0][0] + SUB_LAG  # 이 줄 첫 단어가 나올 때까지 하이라이트를 미룹니다.
            if 대기 > 0:
                parts.append(f"{{\\kf{round(대기 * 100)}}} ")
            prev_end = 몫[0][0]
            for start, dur, word in 몫:
                gap_cs = round(max(0.0, start - prev_end) * 100)
                if gap_cs:  # 단어 사이 침묵만큼 하이라이트를 미룹니다.
                    parts.append(f"{{\\kf{gap_cs}}} ")
                parts.append(f"{{\\kf{max(1, round(dur * 100))}}}{word} ")
                prev_end = start + dur
            여백 = SUB_TOP + li * SUB_LINE_PITCH
            f.write(f"Dialogue: 0,{ass_time(0)},{ass_time(끝)},Def,,0,0,{여백},,"
                    f"{''.join(parts).rstrip()}\n")

        if emphasis:
            본문, size = 강조_배치(emphasis)
            줄목록 = 본문.split("\\N")
            간격 = round(size * EMPHASIS_PITCH)
            첫줄y = SIZE[1] // 2 - 간격 * (len(줄목록) - 1) // 2
            크기 = "" if size == EMPHASIS_SIZE else f"\\fs{size}"
            # 살짝 커지며 나타났다가 장면 끝까지 남습니다(\t = 시간에 따른 변화).
            # 반전 장면은 더 작게 시작해 더 크게 튀어나옵니다.
            팝 = ("\\fscx40\\fscy40\\t(0,200,\\fscx114\\fscy114)\\t(200,320,\\fscx100\\fscy100)"
                  if climax else
                  "\\fscx70\\fscy70\\t(0,260,\\fscx104\\fscy104)\\t(260,380,\\fscx100\\fscy100)")
            for li, 한줄 in enumerate(줄목록):
                효과 = (f"{{\\an5\\pos({SIZE[0] // 2},{첫줄y + li * 간격})"
                        f"\\fad(200,250){크기}{팝}}}")
                f.write(f"Dialogue: 1,{ass_time(0)},{ass_time(끝)},Big,,0,0,0,,{효과}{한줄}\n")


def render_clip(image: str | None, audio: str, out: str, subtitle: str = "", gap: float = GAP,
                words: list[tuple[float, float, str]] | None = None,
                video: str | None = None, emphasis: str = "", still: bool = False,
                climax: bool = False) -> None:
    """사진 한 장(또는 B-roll 영상)과 음성 하나를 붙여 장면 하나를 만듭니다.

    still=True 면 켄번즈 확대를 끕니다. 프레임을 덧입힌 장면은 확대하면 테두리가
    화면 밖으로 잘려 나가므로 그대로 보여야 합니다.
    climax=True 면 마지막 반전 장면입니다. 더 밀고 들어가고 더 어둡게 해 강조만 남깁니다.
    """
    w, h = SIZE
    duration = media_duration(audio) + gap  # 이 장면의 총 길이
    frames = max(1, round(duration * FPS))
    어둡게 = round(DARKEN + (CLIMAX_DARKEN if climax else 0), 3)
    확대 = round(ZOOM_END + (CLIMAX_ZOOM if climax else 0), 3)

    if still:
        vf = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}"
        if EFFECTS:
            vf += f",eq=brightness=-{어둡게},vignette={VIGNETTE}"
    elif video:
        # B-roll 영상: 실제 움직임이 있으니 켄번즈(zoompan) 없이 화면에 꽉 채우기만 합니다.
        vf = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}"
        if EFFECTS:
            vf += f",eq=brightness=-{어둡게},vignette={VIGNETTE}"  # 어둡게 + 비네팅
    elif EFFECTS:
        # 켄번즈: 사진을 크게 키운 뒤 천천히 확대(zoompan)합니다.
        step = (확대 - 1.0) / frames
        vf = (
            f"scale={w * 2}:{h * 2}:force_original_aspect_ratio=increase,crop={w * 2}:{h * 2},"
            f"zoompan=z='min(zoom+{step:.6f},{확대})':d={frames}"
            f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={FPS},"
            f"eq=brightness=-{어둡게},vignette={VIGNETTE}"  # 어둡게 + 비네팅
        )
    else:
        vf = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}"

    subtitle_file = None
    if SUBTITLE and subtitle and words:
        # 단어별 자막: 단어 타이밍으로 ASS 자막을 만들어 ass 필터로 렌더합니다.
        subtitle_file = out + ".ass"
        build_ass(words, duration, subtitle_file, emphasis, climax)
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


def 번호_of(out: str) -> int:
    """출력 파일명 앞 번호. 편마다 다른 화면·연출을 뽑는 씨앗으로 씁니다."""
    m = re.match(r"(\d+)", os.path.basename(out))
    return int(m.group(1)) if m else 0


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


def concat_xfade(clips: list[str], out: str, t: float = XFADE,
                 last_t: float | None = None) -> None:
    """장면들을 크로스페이드로 부드럽게 이어붙입니다.

    last_t 를 주면 마지막 전환만 그 길이로 넘깁니다. 반전 장면은 툭 끊고 들어가야
    반전으로 읽히므로 여기에 아주 짧은 값(CLIMAX_CUT)을 넣어 하드컷처럼 보이게 합니다.
    """
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
        막 = last_t is not None and i == len(clips) - 1
        tt = last_t if 막 else t
        # 짧은 전환에 circleopen 같은 도형 전환을 쓰면 튀어 보입니다. 컷은 fade 로 고정합니다.
        효과 = "fade" if 막 else TRANSITION
        offset = acc - tt
        vout, aout = f"v{i}", f"a{i}"
        v_filters.append(
            f"[{vlabel}][{i}:v]xfade=transition={효과}:duration={tt}"
            f":offset={offset:.3f}[{vout}]"
        )
        a_filters.append(f"[{alabel}][{i}:a]acrossfade=d={tt}[{aout}]")
        vlabel, alabel = vout, aout
        acc += durs[i] - tt

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

    # 편마다 확대량과 전환 길이를 조금씩 다르게 합니다. 전편이 똑같이 움직이면
    # "템플릿으로 찍어냈다"는 인상을 주고, 유튜브 비진정성 콘텐츠 정책이 그 점을 짚습니다.
    # 번호로 정하므로 다시 렌더해도 같은 값이 나옵니다(재현 가능).
    global ZOOM_END, XFADE, TRANSITION
    n = 번호_of(out)
    ZOOM_END = round(1.06 + (n * 7 % 13) / 100, 3)   # 1.06 ~ 1.18
    XFADE = round(0.25 + (n * 11 % 7) / 20, 2)       # 0.25 ~ 0.55
    TRANSITION = TRANSITIONS[n % len(TRANSITIONS)]   # 편마다 다른 전환
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

            # @frame 장면은 사진 위에 프레임을 덧입힙니다(현재 보류, 대본에 표시 없음).
            # 영상(B-roll)에는 덧입힐 수 없어 사진으로 받고 켄번즈를 끕니다.
            프레임 = query.startswith(FRAME_MARK)
            if 프레임:
                query = query[len(FRAME_MARK):].strip()
                if use_photos and query:
                    fetch_image(query, image)
                else:
                    make_background(i, image)
                apply_frame(image, 번호_of(out) + i)
                render_clip(image, audio, clip, scene["narration"], gap, words,
                            emphasis=scene.get("emphasis", ""), still=True, climax=last)
                clips.append(clip)
                continue

            video_src = None
            if BROLL and use_photos and query:
                try:  # 영상 먼저 시도. 실패하면 사진으로 폴백.
                    if fetch_video(query, broll):
                        video_src = broll
                except Exception as e:
                    print(f"    (B-roll 실패, 사진으로 대체: {e})")

            강조 = scene.get("emphasis", "")
            if video_src:
                render_clip(None, audio, clip, scene["narration"], gap, words,
                            video=video_src, emphasis=강조, climax=last)
            else:
                if use_photos and query:
                    fetch_image(query, image)
                else:
                    make_background(i, image)
                render_clip(image, audio, clip, scene["narration"], gap, words,
                            emphasis=강조, climax=last)
            clips.append(clip)

        joined = os.path.join(work, "joined.mp4")
        # 효과가 켜져 있으면 크로스페이드로, 아니면 그대로 이어붙입니다.
        # 마지막 전환만 하드컷으로 끊어 반전에 타격감을 줍니다.
        if EFFECTS:
            concat_xfade(clips, joined, last_t=CLIMAX_CUT)
        else:
            concat(clips, joined)

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

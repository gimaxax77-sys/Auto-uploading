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
MUSIC_VOLUME = 0.15  # 배경음악 음량(0~1). 내레이션이 잘 들리도록 작게.
SUBTITLE = True  # 내레이션 문장을 자막으로 넣습니다.
FONT = "C:/Windows/Fonts/malgunbd.ttf"  # 맑은 고딕 굵게 (가독성)
FONT_SIZE = 74
WRAP = 12  # 한 줄 최대 글자 수. 넘으면 다음 줄로 넘깁니다.
SUB_TOP = 200  # 자막 위쪽 여백(px). 화면 상단에 배치합니다.
LINE_SPACING = 4  # 줄 간격(px). 작을수록 줄이 붙습니다.
# 배경 밝기에 따라 고르는 자막 색. 밝으면 노란 글씨, 어두우면 흰 글씨+초록 테두리.
STYLE_BRIGHT = "fontcolor=yellow:borderw=6:bordercolor=black:shadowcolor=black@0.7:shadowx=3:shadowy=3"
STYLE_DARK = "fontcolor=white:borderw=6:bordercolor=0x00aa00:shadowcolor=black@0.7:shadowx=3:shadowy=3"
BRIGHT_THRESHOLD = 128  # 자막 영역 평균 밝기가 이 값보다 크면 밝은 배경으로 봅니다.
# 장면마다 이 순서로 번갈아 씁니다. 하나만 두면 그 음성만 씁니다.
VOICES = ["ko-KR-SunHiNeural", "ko-KR-InJoonNeural"]
RATE = "+25%"  # 내레이션 속도. +로 빠르게, -로 느리게 (예: "-10%").
GAP = 0.3  # 장면 사이 여백(초). 넘어갈 때 숨 쉬는 틈을 줍니다.
SIZE = (1080, 1920)  # 세로형 쇼츠


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


def narrate(text: str, path: str, voice: str = VOICES[0]) -> None:
    """문장을 음성 파일로 만듭니다."""
    asyncio.run(edge_tts.Communicate(text, voice, rate=RATE).save(path))


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
    """마침표 뒤에서 문장을 나누고, 긴 문장은 띄어쓰기 기준으로 줄바꿈합니다."""
    lines = []
    # 마침표 뒤에서 문장을 끊습니다.
    for sentence in re.split(r"(?<=\.)\s+", text.strip()):
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


def render_clip(image: str, audio: str, out: str, subtitle: str = "") -> None:
    """사진 한 장과 음성 하나를 붙여 장면 하나를 만듭니다."""
    w, h = SIZE
    # 사진을 세로 화면에 꽉 채우고 넘치는 부분은 잘라냅니다.
    vf = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}"

    subtitle_file = None
    if SUBTITLE and subtitle:
        # 자막 텍스트는 파일로 넘겨 따옴표·콜론 이스케이프 문제를 피합니다.
        subtitle_file = out + ".txt"
        # newline="\n" 로 저장해야 윈도우식 \r\n 때문에 줄 사이가 벌어지지 않습니다.
        with open(subtitle_file, "w", encoding="utf-8", newline="\n") as f:
            f.write(wrap_text(subtitle, WRAP))
        font = FONT.replace(":", "\\:")  # 드라이브 문자 뒤 콜론 이스케이프
        tf = subtitle_file.replace("\\", "/").replace(":", "\\:")
        style = subtitle_style(image)  # 배경 밝기에 맞춰 색을 고릅니다.
        vf += (
            f",drawtext=fontfile='{font}':textfile='{tf}'"
            f":fontsize={FONT_SIZE}:{style}"
            f":line_spacing={LINE_SPACING}:x=(w-tw)/2:y={SUB_TOP}"  # 가로 가운데, 상단 배치
        )

    try:
        subprocess.run(
            [
                FFMPEG, "-y", "-loop", "1", "-i", image, "-i", audio,
                "-vf", vf,
                # 음성 끝에 GAP 초 만큼 무음을 붙여 장면 사이에 여백을 줍니다.
                "-af", f"apad=pad_dur={GAP}",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
                "-c:a", "aac", "-shortest", out,
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


def pick_music(path: str) -> str | None:
    """배경음악을 준비합니다. 폴더 우선, 없으면 Jamendo. 출처 문구를 돌려줍니다."""
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
         f"[1:a]volume={MUSIC_VOLUME}[bg];[0:a][bg]amix=inputs=2:duration=first[a]",
         "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", out],
        check=True,
        capture_output=True,
    )


def concat(clips: list[str], out: str) -> None:
    """장면들을 하나의 영상으로 이어붙입니다."""
    listfile = os.path.join(os.path.dirname(clips[0]), "clips.txt")
    with open(listfile, "w", encoding="utf-8") as f:
        for c in clips:
            f.write(f"file '{os.path.basename(c)}'\n")
    subprocess.run(
        [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", listfile, "-c", "copy", out],
        check=True,
        capture_output=True,
    )


def make_video(scenes: list[dict], out: str) -> str:
    """장면 목록을 받아 완성된 영상 파일을 만듭니다."""
    # 키가 없거나 검색어가 비어 있으면 사진 대신 단색 배경을 씁니다.
    use_photos = bool(os.environ.get("PEXELS_API_KEY"))
    if not use_photos:
        print("  (PEXELS_API_KEY 가 없어 대체 배경을 씁니다)")

    with tempfile.TemporaryDirectory() as work:
        clips = []
        for i, scene in enumerate(scenes):
            audio = os.path.join(work, f"{i}.mp3")
            image = os.path.join(work, f"{i}.jpg")
            clip = os.path.join(work, f"{i}.mp4")
            voice = VOICES[i % len(VOICES)]  # 장면마다 음성을 번갈아 씁니다.
            print(f"  장면 {i + 1}/{len(scenes)} [{voice.split('-')[-1]}]: {scene['narration'][:24]}...")
            narrate(scene["narration"], audio, voice)
            if use_photos and scene["image_query"]:
                fetch_image(scene["image_query"], image)
            else:
                make_background(i, image)
            render_clip(image, audio, clip, scene["narration"])
            clips.append(clip)

        joined = os.path.join(work, "joined.mp4")
        concat(clips, joined)

        # 배경음악을 준비해 깝니다. 없으면 그대로 둡니다.
        music = os.path.join(work, "bgm.mp3")
        credit = pick_music(music)
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

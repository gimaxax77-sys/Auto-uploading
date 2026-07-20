# 대본을 받아 이미지 + 내레이션 슬라이드쇼 영상을 만드는 도구
import asyncio
import os
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
VOICE = "ko-KR-SunHiNeural"
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


def narrate(text: str, path: str) -> None:
    """문장을 음성 파일로 만듭니다."""
    asyncio.run(edge_tts.Communicate(text, VOICE, rate=RATE).save(path))


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


def render_clip(image: str, audio: str, out: str) -> None:
    """사진 한 장과 음성 하나를 붙여 장면 하나를 만듭니다."""
    w, h = SIZE
    subprocess.run(
        [
            FFMPEG, "-y", "-loop", "1", "-i", image, "-i", audio,
            # 사진을 세로 화면에 꽉 채우고 넘치는 부분은 잘라냅니다.
            "-vf", f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}",
            # 음성 끝에 GAP 초 만큼 무음을 붙여 장면 사이에 여백을 줍니다.
            "-af", f"apad=pad_dur={GAP}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
            "-c:a", "aac", "-shortest", out,
        ],
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
            print(f"  장면 {i + 1}/{len(scenes)}: {scene['narration'][:30]}...")
            narrate(scene["narration"], audio)
            if use_photos and scene["image_query"]:
                fetch_image(scene["image_query"], image)
            else:
                make_background(i, image)
            render_clip(image, audio, clip)
            clips.append(clip)
        concat(clips, out)
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

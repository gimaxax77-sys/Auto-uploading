# API 키 없이 ffmpeg 영상 조립이 실제로 되는지 확인하는 자체 점검
import os
import re
import subprocess
import tempfile

import video


def make_dummy(work, i):
    """단색 이미지와 무음 오디오를 만들어 둡니다(외부 API 불필요)."""
    image = os.path.join(work, f"{i}.jpg")
    audio = os.path.join(work, f"{i}.mp3")
    subprocess.run(
        [video.FFMPEG, "-y", "-f", "lavfi", "-i", f"color=c=blue:s=640x480",
         "-frames:v", "1", image],
        check=True, capture_output=True,
    )
    subprocess.run(
        [video.FFMPEG, "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
         "-t", "1", audio],
        check=True, capture_output=True,
    )
    return image, audio


def test_장면조립과_이어붙이기():
    with tempfile.TemporaryDirectory() as work:
        clips = []
        for i in range(2):
            image, audio = make_dummy(work, i)
            clip = os.path.join(work, f"{i}.mp4")
            video.render_clip(image, audio, clip)
            assert os.path.getsize(clip) > 0, f"장면 {i} 가 비어 있습니다"
            clips.append(clip)

        out = os.path.join(work, "out.mp4")
        video.concat(clips, out)
        assert os.path.getsize(out) > 0, "이어붙인 영상이 비어 있습니다"

        # 장면 2개(각 1초)를 붙였으니 대략 2초여야 합니다.
        # imageio-ffmpeg 에는 ffprobe 가 없어 ffmpeg 출력에서 길이를 읽습니다.
        info = subprocess.run(
            [video.FFMPEG, "-i", out], capture_output=True, text=True,
        ).stderr
        match = re.search(r"Duration: (\d+):(\d+):([\d.]+)", info)
        assert match, f"길이를 읽지 못했습니다:\n{info}"
        h, m, s = match.groups()
        duration = int(h) * 3600 + int(m) * 60 + float(s)
        assert 1.5 < duration < 3.0, f"길이가 {duration}초로 예상(약 2초)과 다릅니다"


def test_대본파일_읽기():
    with tempfile.TemporaryDirectory() as work:
        path = os.path.join(work, "s.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("# 주석은 무시\n\n첫 장면입니다. | autumn\n둘째 장면입니다.\n")

        scenes = video.read_script(path)
        assert len(scenes) == 2, f"장면이 2개여야 하는데 {len(scenes)}개입니다"
        assert scenes[0] == {"narration": "첫 장면입니다.", "image_query": "autumn"}
        # 검색어를 안 쓰면 비어 있어야 하고, 그러면 색 배경이 쓰입니다.
        assert scenes[1] == {"narration": "둘째 장면입니다.", "image_query": ""}


def test_빈_대본파일은_에러():
    with tempfile.TemporaryDirectory() as work:
        path = os.path.join(work, "empty.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("# 주석만 있음\n\n")
        try:
            video.read_script(path)
        except ValueError as e:
            assert "읽을 장면이 없습니다" in str(e)
        else:
            raise AssertionError("빈 대본인데 에러가 나지 않았습니다")


if __name__ == "__main__":
    test_장면조립과_이어붙이기()
    test_대본파일_읽기()
    test_빈_대본파일은_에러()
    print("통과")

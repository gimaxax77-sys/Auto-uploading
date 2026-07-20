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


if __name__ == "__main__":
    test_장면조립과_이어붙이기()
    print("통과")

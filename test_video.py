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
            f.write("# 주석은 무시\n\n첫 장면입니다. | autumn\n둘째 장면입니다.\n"
                    "셋째 장면입니다. | bamboo | 하루 90cm\n")

        scenes = video.read_script(path)
        assert len(scenes) == 3, f"장면이 3개여야 하는데 {len(scenes)}개입니다"
        assert scenes[0] == {"narration": "첫 장면입니다.", "image_query": "autumn", "emphasis": ""}
        # 검색어를 안 쓰면 비어 있어야 하고, 그러면 색 배경이 쓰입니다.
        assert scenes[1] == {"narration": "둘째 장면입니다.", "image_query": "", "emphasis": ""}
        # 세로줄 두 번째 뒤는 화면 가운데 크게 박히는 강조 문구입니다.
        assert scenes[2] == {"narration": "셋째 장면입니다.", "image_query": "bamboo",
                             "emphasis": "하루 90cm"}


def test_강조문구_어절_한가운데서_안_끊김():
    # libass 는 한글을 CJK 로 보아 아무 글자에서나 줄을 끊는다. 우리가 직접 나눠야 한다.
    최대폭 = video.SIZE[0] - 120 - 30
    for 문구 in ["같은 만 원인데", "가장 가까운 이웃 = 우주인", "3조 vs 2천억",
                "육지까지 2,600km", "3만℃", "안 그러면 자기를 녹인다"]:
        본문, size = video.강조_배치(문구)
        줄 = 본문.split("\\N")
        assert len(줄) <= video.EMPHASIS_LINES, f"{문구} 가 {len(줄)}줄"
        for l in 줄:
            assert video.글자폭(l, size) <= 최대폭, f"{문구} 의 '{l}' 이 화면을 넘침"
        # 붙여 놓으면 원문과 같아야 한다(글자가 사라지거나 늘면 안 됨)
        assert " ".join(줄).split() == 문구.split(), f"{문구} -> {본문}"

    # 금액과 기호는 갈라지지 않는다
    assert video.강조_배치("같은 만 원인데")[0].split("\\N")[-1] == "만 원인데"
    assert "\\N" not in video.강조_배치("나무 > 별")[0]

    # 어절 묶기 자체
    assert video.어절_묶기(["같은", "만", "원인데"]) == ["같은", "만 원인데"]
    assert video.어절_묶기(["나무", ">", "별"]) == ["나무 > 별"]
    assert video.어절_묶기(["빠른", "판단"]) == ["빠른", "판단"]  # 붙일 이유 없으면 그대로


def test_전환목록_안전():
    # squeezev 는 ffmpeg 이 접근 위반으로 죽는다. 목록에 들어가면 그 편 렌더가 통째로 실패한다.
    assert "squeezev" not in video.TRANSITIONS, "죽는 전환이 목록에 들어갔습니다"
    assert len(video.TRANSITIONS) == len(set(video.TRANSITIONS)), "전환 목록에 중복이 있습니다"
    assert video.TRANSITION in video.TRANSITIONS


def test_강조문구_자막파일에_들어감():
    with tempfile.TemporaryDirectory() as work:
        path = os.path.join(work, "s.ass")
        words = [(0.0, 0.5, "가"), (0.5, 0.5, "나")]
        video.build_ass(words, 2.0, path, "3만℃")
        내용 = open(path, encoding="utf-8").read()
        assert "Style: Big" in 내용, "강조용 스타일이 없습니다"
        assert "3만℃" in 내용, "강조 문구가 안 들어갔습니다"
        assert 내용.count("Dialogue:") == 2, "자막 줄과 강조 줄 2개여야 합니다"

        video.build_ass(words, 2.0, path)  # 강조를 안 주면 자막 한 줄만
        assert open(path, encoding="utf-8").read().count("Dialogue:") == 1


def test_자막_줄마다_행간을_띄운다():
    # ASS 스타일에는 행간 항목이 없어 한 Dialogue 에 \N 으로 나누면 줄이 맞닿는다(실측 2px).
    # 줄마다 Dialogue 를 따로 쓰고 MarginV 로 내리는지 확인한다.
    긴말 = [(i * 0.2, 0.2, w) for i, w in enumerate(["가나다라마"] * 8)]
    with tempfile.TemporaryDirectory() as work:
        path = os.path.join(work, "s.ass")
        video.build_ass(긴말, 5.0, path)
        줄 = [x for x in open(path, encoding="utf-8").read().splitlines()
              if x.startswith("Dialogue:")]
        assert len(줄) >= 2, "여러 줄로 쪼개져야 하는 문장이 한 줄로 나왔습니다"
        assert "\\N" not in "".join(줄), "\\N 으로 줄을 나누면 행간이 0 이 됩니다"
        # Dialogue: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text → MarginV 는 7번
        여백 = [int(x.split(",")[7]) for x in 줄]
        assert 여백[0] == video.SUB_TOP, f"첫 줄이 SUB_TOP 이 아닙니다: {여백[0]}"
        간격 = [b - a for a, b in zip(여백, 여백[1:])]
        assert all(g == video.SUB_LINE_PITCH for g in 간격), f"행간이 고르지 않습니다: {간격}"


def test_자막은_전환_시작_전에_걷힌다():
    # 자막을 클립에 구운 뒤 크로스페이드로 잇는 구조라, 끝까지 남기면 전환 동안 두 겹으로 보인다.
    with tempfile.TemporaryDirectory() as work:
        path = os.path.join(work, "s.ass")
        video.build_ass([(0.0, 0.5, "가")], 3.0, path, "강조")
        끝들 = {x.split(",")[2] for x in open(path, encoding="utf-8").read().splitlines()
                if x.startswith("Dialogue:")}
        assert len(끝들) == 1, "자막과 강조가 같은 시각에 걷혀야 합니다"
        끝 = 끝들.pop()
        assert 끝 == video.ass_time(3.0 - video.XFADE), f"전환 전에 안 걷힙니다: {끝}"

        # 말이 끝나기 전에 걷히면 안 된다. XFADE 가 GAP 보다 긴 편에서 실제로 났던 문제다.
        긴전환 = video.XFADE
        try:
            video.XFADE = 0.55
            video.build_ass([(0.0, 1.8, "가")], 2.1, path)  # 말은 1.8 에 끝, 2.1-0.55=1.55
            끝2 = [x.split(",")[2] for x in open(path, encoding="utf-8").read().splitlines()
                   if x.startswith("Dialogue:")][0]
            assert 끝2 == video.ass_time(1.95), f"말이 끝나기 전에 자막이 걷힙니다: {끝2}"
        finally:
            video.XFADE = 긴전환

        # 장면보다 길게 남기지 않는다.
        video.build_ass([(0.0, 0.2, "가")], 0.3, path)
        짧은끝 = [x.split(",")[2] for x in open(path, encoding="utf-8").read().splitlines()
                 if x.startswith("Dialogue:")][0]
        assert 짧은끝 == video.ass_time(0.3), f"장면 길이를 넘겼습니다: {짧은끝}"


def test_반전장면은_연출이_다르다():
    with tempfile.TemporaryDirectory() as work:
        보통, 반전 = os.path.join(work, "a.ass"), os.path.join(work, "b.ass")
        video.build_ass([(0.0, 0.5, "가")], 2.0, 보통, "강조", climax=False)
        video.build_ass([(0.0, 0.5, "가")], 2.0, 반전, "강조", climax=True)
        assert open(보통, encoding="utf-8").read() != open(반전, encoding="utf-8").read(), \
            "반전 장면인데 강조 연출이 같습니다"
        assert "\\fscx40" in open(반전, encoding="utf-8").read(), "반전 펀치인이 안 들어갔습니다"


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


def make_music(work, name="bgm.mp3"):
    """테스트용 무음이 아닌 톤 오디오를 만듭니다."""
    p = os.path.join(work, name)
    subprocess.run(
        [video.FFMPEG, "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=5", p],
        check=True, capture_output=True,
    )
    return p


def test_배경음악_합성():
    with tempfile.TemporaryDirectory() as work:
        # 음성이 들어간 장면 하나를 만듭니다.
        image, audio = make_dummy(work, 0)
        clip = os.path.join(work, "clip.mp4")
        video.render_clip(image, audio, clip)

        music = make_music(work)
        out = os.path.join(work, "with_music.mp4")
        video.add_music(clip, music, out)

        # 영상 트랙과 오디오 트랙이 둘 다 있어야 합니다.
        info = subprocess.run([video.FFMPEG, "-i", out], capture_output=True, text=True).stderr
        assert "Video:" in info and "Audio:" in info, f"트랙이 빠졌습니다:\n{info}"
        assert os.path.getsize(out) > 0


def test_폴더음악_우선():
    # music 폴더에 파일이 있으면 그걸 쓰고 출처 표기는 None 이어야 합니다.
    with tempfile.TemporaryDirectory() as work:
        old = os.getcwd()
        os.chdir(work)
        try:
            os.makedirs(video.MUSIC_DIR)
            make_music(work, os.path.join(video.MUSIC_DIR, "my.mp3"))
            out = os.path.join(work, "picked.mp3")
            credit = video.pick_music(out)
            assert credit is None, "폴더 음악은 출처 표기가 없어야 합니다"
            assert os.path.getsize(out) > 0, "폴더 음악이 준비되지 않았습니다"
        finally:
            os.chdir(old)


if __name__ == "__main__":
    test_장면조립과_이어붙이기()
    test_대본파일_읽기()
    test_강조문구_어절_한가운데서_안_끊김()
    test_전환목록_안전()
    test_강조문구_자막파일에_들어감()
    test_자막_줄마다_행간을_띄운다()
    test_자막은_전환_시작_전에_걷힌다()
    test_반전장면은_연출이_다르다()
    test_빈_대본파일은_에러()
    test_배경음악_합성()
    test_폴더음악_우선()
    print("통과")

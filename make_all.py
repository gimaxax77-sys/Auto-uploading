# scripts 폴더의 대본을 전부 영상으로 만드는 일괄 실행 도구
import glob
import os
import re
import sys

from video import make_video, read_script

SCRIPTS_DIR = "scripts"
OUTPUT_DIR = "output"


def script_num(path: str) -> int:
    m = re.match(r"(\d+)", os.path.basename(path))
    return int(m.group(1)) if m else 0


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    files = sorted(glob.glob(os.path.join(SCRIPTS_DIR, "*.txt")))
    if not files:
        print(f"{SCRIPTS_DIR} 폴더에 대본(.txt)이 없습니다.")
        sys.exit(1)

    # 인자 2개(시작 끝)를 주면 그 번호 구간만, 이미 있어도 덮어써서 재생성합니다.
    force = len(sys.argv) >= 3
    if force:
        lo, hi = int(sys.argv[1]), int(sys.argv[2])
        files = [f for f in files if lo <= script_num(f) <= hi]

    print(f"대본 {len(files)}개를 영상으로 만듭니다.\n")
    done, failed, skipped = [], [], []
    for i, path in enumerate(files, 1):
        name = os.path.splitext(os.path.basename(path))[0]
        out = os.path.join(OUTPUT_DIR, f"{name}.mp4")
        # 구간 지정(force)이 아니면, 이미 만든 영상은 건너뜁니다.
        if os.path.exists(out) and not force:
            skipped.append(name)
            continue
        print(f"[{i}/{len(files)}] {name}")
        try:
            scenes = read_script(path)
            make_video(scenes, out)
            done.append(name)
        except Exception as e:
            # 하나가 실패해도 나머지는 계속 만듭니다.
            print(f"  실패: {e}")
            failed.append(name)

    print(f"\n완료 {len(done)}개, 건너뜀 {len(skipped)}개, 실패 {len(failed)}개")
    if failed:
        print("실패 목록:", ", ".join(failed))


if __name__ == "__main__":
    main()

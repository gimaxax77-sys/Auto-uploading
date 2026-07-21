# output 폴더의 영상을 하루 N편씩 공개로 올리는 도구 (이미 올린 건 건너뜀)
import glob
import json
import os
import re
import sys

from youtube import upload

OUTPUT_DIR = "output"
LOG = "uploaded.json"  # 이미 올린 대본 이름 기록
DESC = "매일 짧게 보는 이야기. #shorts #동기부여 #꿀팁 #일상"


def load_log() -> set:
    if os.path.exists(LOG):
        return set(json.load(open(LOG, encoding="utf-8")))
    return set()


def save_log(done: set) -> None:
    with open(LOG, "w", encoding="utf-8") as f:
        json.dump(sorted(done), f, ensure_ascii=False, indent=0)


def title_of(name: str) -> str:
    """파일명에서 제목을 만듭니다. 예: 01_아침_마음가짐 -> 아침 마음가짐 #shorts"""
    base = re.sub(r"^\d+_", "", name).replace("_", " ")
    return f"{base} #shorts"


def main() -> None:
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    done = load_log()
    files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "*.mp4")),
                   key=lambda p: os.path.basename(p))

    todo = [f for f in files if os.path.splitext(os.path.basename(f))[0] not in done]
    if not todo:
        print("올릴 영상이 없습니다. 모두 업로드됨.")
        return

    batch = todo[:count]
    print(f"오늘 {len(batch)}편을 공개로 올립니다. (남은 미업로드: {len(todo)}편)\n")
    for f in batch:
        name = os.path.splitext(os.path.basename(f))[0]
        title = title_of(name)
        try:
            url = upload(f, title, DESC, private=False)
            print(f"  공개 완료: {title} -> {url}")
            done.add(name)
            save_log(done)  # 하나 올릴 때마다 기록(중간에 멈춰도 안전)
        except Exception as e:
            print(f"  실패: {name} - {e}")
            break

    print(f"\n누적 업로드: {len(done)} / {len(files)}편")


if __name__ == "__main__":
    main()

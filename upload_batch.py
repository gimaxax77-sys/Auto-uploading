# output 폴더의 영상을 하루 N편씩 공개로 올리는 도구 (이미 올린 건 건너뜀)
import glob
import json
import os
import random
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


def genre_of(path: str) -> str:
    """파일 번호로 대략의 장르를 반환합니다(연속 업로드 방지용)."""
    m = re.match(r"(\d+)", os.path.basename(path))
    n = int(m.group(1)) if m else 0
    if 101 <= n <= 105:
        return "반려"
    if 81 <= n <= 85 or 106 <= n <= 115:
        return "명소"
    if 141 <= n <= 155:
        return "심리"
    if 61 <= n <= 65:
        return "고사"
    if 91 <= n <= 100 or 131 <= n <= 135 or 156 <= n <= 185:
        return "자연"  # 자연원리·과학·경이·극한·바다
    if 21 <= n <= 35 or 56 <= n <= 75 or 86 <= n <= 90 or 116 <= n <= 130 or 136 <= n <= 140:
        return "생활"  # 꿀팁·돈·루틴·AI·직장
    return "마음"  # 동기부여·감성 등


def spread(items: list) -> list:
    """무작위로 섞되, 같은 장르가 연달아 오지 않게 재배치합니다."""
    items = items[:]
    random.shuffle(items)
    out, last = [], None
    while items:
        idx = next((i for i, x in enumerate(items) if genre_of(x) != last), 0)
        x = items.pop(idx)
        out.append(x)
        last = genre_of(x)
    return out


def main() -> None:
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    done = load_log()
    files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "*.mp4")),
                   key=lambda p: os.path.basename(p))

    todo = [f for f in files if os.path.splitext(os.path.basename(f))[0] not in done]
    if not todo:
        print("올릴 영상이 없습니다. 모두 업로드됨.")
        return

    todo = spread(todo)  # 장르 안 겹치게 랜덤 배치
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

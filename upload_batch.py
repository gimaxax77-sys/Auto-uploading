# output 폴더의 영상을 하루 N편씩 공개로 올리는 도구 (이미 올린 건 건너뜀)
import glob
import json
import os
import random
import re
import sys
from datetime import date

from youtube import upload

OUTPUT_DIR = "output"
SCRIPTS_DIR = "scripts"
LOG = "uploaded.json"  # 이미 올린 대본 이름 기록
STATE = "last_run.json"  # 오늘 몇 편 올렸는지(점검·상한용)
DAILY_MAX = 3  # 하루 상한. 손으로 돌리든 스케줄러가 돌리든 하루에 이 수를 넘지 않는다.


def scenes_of(name: str) -> list[tuple[str, str]]:
    """대본에서 (문장, 강조문구) 목록을 읽습니다. 없으면 빈 목록."""
    path = os.path.join(SCRIPTS_DIR, name + ".txt")
    if not os.path.exists(path):
        return []
    out = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "|" not in line:
            continue
        문장, _, 뒤 = line.partition("|")
        _, _, 강조 = 뒤.partition("|")
        out.append((문장.strip(), 강조.strip()))
    return out


def is_current(name: str) -> bool:
    """지금 채널 갈래(새 포맷)인지. 강조문구가 있는 대본만 올립니다.

    비공개로 내린 옛 갈래(동기부여·생활꿀팁 등)가 다시 올라가지 않게 막습니다.
    """
    return any(강조 for _, 강조 in scenes_of(name))


def desc_of(name: str) -> str:
    """대본에서 영상별 소개글을 만듭니다. 편마다 다른 글이 붙습니다."""
    scenes = scenes_of(name)
    if not scenes:
        return "지나쳤던 것들의 진짜 이유, 매일 하나씩.\n\n#Shorts #지식 #상식"
    본문 = "\n".join(문장 for 문장, _ in scenes)
    return f"{본문}\n\n지나쳤던 것들의 진짜 이유를 1분 안에.\n\n#Shorts #지식 #상식 #궁금증"


def tags_of(name: str) -> list[str]:
    """번호대에 맞는 태그를 붙입니다."""
    m = re.match(r"(\d+)", name)
    n = int(m.group(1)) if m else 0
    t = ["지식", "상식", "궁금증", "1분지식"]
    for rng, extra in (
        (range(91, 101), ["자연현상", "계절", "과학상식"]),
        (range(131, 136), ["과학상식", "신기한사실"]),
        (range(141, 156), ["심리학", "행동경제학", "우리몸"]),
        (range(156, 166), ["동물", "자연의신비", "지구"]),
        (range(166, 176), ["극한환경", "지구", "세계기록"]),
        (range(176, 186), ["바다", "해양", "지구"]),
        (range(186, 196), ["우주", "천문", "과학상식"]),
        (range(196, 206), ["식물", "나무", "자연의신비"]),
        (range(206, 216), ["음식", "생활과학", "요리상식"]),
    ):
        if n in rng:
            t += extra
    t.append(title_of(name))
    return t[:15]


def load_log() -> set:
    if os.path.exists(LOG):
        return set(json.load(open(LOG, encoding="utf-8")))
    return set()


def save_log(done: set) -> None:
    with open(LOG, "w", encoding="utf-8") as f:
        json.dump(sorted(done), f, ensure_ascii=False, indent=0)


def 오늘올린수() -> int:
    """오늘 이미 올린 편수. 날짜가 바뀌면 0부터 다시 셉니다."""
    if not os.path.exists(STATE):
        return 0
    try:
        s = json.load(open(STATE, encoding="utf-8"))
    except (ValueError, OSError):
        return 0
    return int(s.get("done", 0)) if s.get("date") == date.today().isoformat() else 0


def save_state(done: int) -> None:
    """오늘 누적 업로드 수를 기록합니다. check_upload.py 가 이 파일만 보고 판단합니다."""
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump({"date": date.today().isoformat(), "goal": DAILY_MAX, "done": done}, f)


# 번호대 -> 재생목록 이름. 올린 뒤 자동으로 담습니다(채널 페이지 정리 유지).
PLAYLISTS = [
    (set(range(96, 101)) | {132}, "하늘과 우주"),
    (set(range(186, 196)), "하늘과 우주"),
    ({99} | set(range(176, 186)), "바다의 비밀"),
    ({134} | set(range(156, 166)) | set(range(166, 176)), "자연이 숨긴 사실"),
    (set(range(196, 206)), "자연이 숨긴 사실"),
    (set(range(146, 151)), "우리 몸의 이유"),
    (set(range(141, 146)), "생각의 함정"),
    (set(range(151, 156)), "돈이 새는 이유"),
    ({131, 133, 135} | set(range(206, 216)), "생활 속 과학"),
]


def playlist_of(name: str) -> str:
    """이 영상이 들어갈 재생목록 이름. 없으면 빈 문자열."""
    m = re.match(r"(\d+)", name)
    n = int(m.group(1)) if m else 0
    for 번호들, 이름 in PLAYLISTS:
        if n in 번호들:
            return 이름
    return ""


def title_of(name: str) -> str:
    """파일명에서 제목을 만듭니다. 예: 01_아침_마음가짐 -> 아침 마음가짐

    세로 60초 이하면 유튜브가 알아서 쇼츠로 분류하므로 제목에 #shorts 를 붙이지
    않습니다(전수 확인함). 채널 목록에서 제목만 깔끔하게 보입니다.
    """
    return re.sub(r"^\d+_", "", name).replace("_", " ")


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
    if 91 <= n <= 100 or 131 <= n <= 135 or 156 <= n <= 205:
        return "자연"  # 자연원리·과학·경이·극한·바다·우주·식물
    if (21 <= n <= 35 or 56 <= n <= 75 or 86 <= n <= 90 or 116 <= n <= 130
            or 136 <= n <= 140 or 206 <= n <= 215):
        return "생활"  # 꿀팁·돈·루틴·AI·직장·음식과학
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


_재생목록_캐시: dict[str, str] = {}


def 담기(video_id: str, 이름: str) -> None:
    """올린 영상을 해당 재생목록에 담습니다. 없으면 만듭니다. 실패해도 업로드는 유지."""
    if not 이름:
        return
    try:
        from youtube import get_service
        svc = get_service()
        if not _재생목록_캐시:
            tok = None
            while True:
                r = svc.playlists().list(part="snippet", mine=True, maxResults=50, pageToken=tok).execute()
                for p in r["items"]:
                    _재생목록_캐시[p["snippet"]["title"]] = p["id"]
                tok = r.get("nextPageToken")
                if not tok:
                    break
        if 이름 not in _재생목록_캐시:
            p = svc.playlists().insert(part="snippet,status", body={
                "snippet": {"title": 이름, "defaultLanguage": "ko"},
                "status": {"privacyStatus": "public"}}).execute()
            _재생목록_캐시[이름] = p["id"]
        svc.playlistItems().insert(part="snippet", body={"snippet": {
            "playlistId": _재생목록_캐시[이름],
            "resourceId": {"kind": "youtube#video", "videoId": video_id}}}).execute()
        print(f"    재생목록 '{이름}' 에 담음")
    except Exception as e:
        print(f"    (재생목록 담기 실패, 업로드는 정상: {e})")


def pending() -> list[str]:
    """아직 안 올렸고, 지금 채널 갈래(새 포맷)인 영상 목록.

    업로드 대상 판정은 여기 한 곳에만 둡니다. 점검·알림도 이 함수를 씁니다
    (하루 목표를 두 곳에 적었다가 어긋난 7/26 사고와 같은 종류를 막습니다).
    """
    done = load_log()
    files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "*.mp4")),
                   key=lambda p: os.path.basename(p))
    return [f for f in files
            if os.path.splitext(os.path.basename(f))[0] not in done
            and is_current(os.path.splitext(os.path.basename(f))[0])]


def main() -> None:
    count = int(sys.argv[1]) if len(sys.argv) > 1 else DAILY_MAX
    # 손으로 미리 올린 날에도 스케줄러가 또 올려 하루치를 넘기지 않도록 상한을 겁니다.
    이미 = 오늘올린수()
    count = min(count, max(0, DAILY_MAX - 이미))
    if count == 0:
        print(f"오늘 이미 {이미}편을 올렸습니다. 하루 상한({DAILY_MAX}편)을 채웠으므로 건너뜁니다.")
        return
    done = load_log()
    files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "*.mp4")),
                   key=lambda p: os.path.basename(p))
    todo = pending()
    if not todo:
        print("올릴 영상이 없습니다. 모두 업로드됨.")
        return

    todo = spread(todo)  # 장르 안 겹치게 랜덤 배치
    batch = todo[:count]
    print(f"오늘 {len(batch)}편을 공개로 올립니다. "
          f"(오늘 이미 {이미}편 · 남은 미업로드 {len(todo)}편)\n")
    올린수 = 0
    for f in batch:
        name = os.path.splitext(os.path.basename(f))[0]
        title = title_of(name)
        try:
            url = upload(f, title, desc_of(name), private=False, tags=tags_of(name))
            print(f"  공개 완료: {title} -> {url}")
            담기(url.rsplit("/", 1)[-1], playlist_of(name))
            done.add(name)
            save_log(done)  # 하나 올릴 때마다 기록(중간에 멈춰도 안전)
            올린수 += 1
            save_state(이미 + 올린수)
        except Exception as e:
            print(f"  실패: {name} - {e}")
            break

    print(f"\n누적 업로드: {len(done)} / {len(files)}편")


if __name__ == "__main__":
    main()

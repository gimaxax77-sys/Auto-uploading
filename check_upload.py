# 밤 11시 업로드가 제대로 끝났는지 점검하고, 모자란 편수만 다시 올리는 도구
import json
import os
import sys
from datetime import date

STATE = "last_run.json"  # upload_batch.py 가 남기는 진행 상황
GOAL = 12  # 하루 목표 편수


def missing_count() -> int:
    """오늘 몇 편을 더 올려야 하는지 계산합니다. 0이면 정상 완료입니다."""
    if not os.path.exists(STATE):
        return GOAL  # 실행 흔적이 아예 없음

    try:
        s = json.load(open(STATE, encoding="utf-8"))
    except (ValueError, OSError):
        return GOAL  # 기록이 깨졌으면 오늘 실행이 없었던 것으로 본다

    # ponytail: 날짜만 비교하므로 자정 넘겨 점검하면 오판함. 점검은 23:10 고정이라 무해.
    if s.get("date") != date.today().isoformat():
        return GOAL  # 오늘 밤 실행이 통째로 실패한 것

    return max(0, min(GOAL, int(s.get("goal", GOAL)) - int(s.get("done", 0))))


def main() -> None:
    need = missing_count()
    stamp = date.today().isoformat()
    if need == 0:
        print(f"[점검 {stamp}] 정상 완료. 추가 업로드 없음.")
        return

    print(f"[점검 {stamp}] {need}편이 덜 올라갔습니다. 지금 이어서 올립니다.")
    import upload_batch

    sys.argv = ["upload_batch.py", str(need)]
    upload_batch.main()


if __name__ == "__main__":
    main()

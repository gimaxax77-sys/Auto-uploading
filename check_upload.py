# 밤 11시 업로드가 제대로 끝났는지 점검하고, 모자란 편수만 다시 올리는 도구
import json
import os
import sys
from datetime import date

import requests
from dotenv import load_dotenv

STATE = "last_run.json"  # upload_batch.py 가 남기는 진행 상황
# 하루 목표는 upload_batch 한 곳에서만 정합니다. 두 곳에 적으면 어긋납니다(7/26 사고).
from upload_batch import DAILY_MAX as GOAL, pending  # noqa: E402

load_dotenv()  # 텔레그램 토큰은 .env 에 둡니다(저장소에 올리지 않음)


def notify(text: str) -> None:
    """결과 한 줄을 텔레그램으로 보냅니다. 키가 없으면 아무 일도 하지 않습니다."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not (token and chat):
        return
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      data={"chat_id": chat, "text": text}, timeout=10)
    except Exception as e:
        # 알림이 실패해도 업로드 점검 자체는 정상으로 끝나야 합니다.
        print(f"(알림 전송 실패: {e})")


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
        notify(f"[1분 궁금증] {stamp} 업로드 {GOAL}편 정상 완료\n남은 대기열 {len(pending())}편")
        return

    print(f"[점검 {stamp}] {need}편이 덜 올라갔습니다. 지금 이어서 올립니다.")
    import upload_batch

    sys.argv = ["upload_batch.py", str(need)]
    upload_batch.main()

    남은 = missing_count()  # 재시도가 실제로 메웠는지 다시 잽니다
    if 남은 == 0:
        notify(f"[1분 궁금증] {stamp} {need}편이 빠져 있었으나 재시도로 복구했습니다\n"
               f"남은 대기열 {len(pending())}편")
    else:
        notify(f"[1분 궁금증] {stamp} 업로드 실패. {남은}편이 아직 안 올라갔습니다\n"
               f"upload_log.txt 를 확인해 주세요.")


if __name__ == "__main__":
    main()

# 밤 11시 업로드가 제대로 끝났는지 점검하고, 모자란 편수만 다시 올리는 도구
import os
import re
import sys
from datetime import date

LOG = "upload_log.txt"
START = re.compile(r"오늘 (\d+)편을 공개로 올립니다")
EXIT = re.compile(r"\[(\d{4}-\d{2}-\d{2})[^\]]*\] exit=(\d+)")


def missing_count() -> int:
    """오늘 몇 편을 더 올려야 하는지 계산합니다. 0이면 정상 완료입니다."""
    if not os.path.exists(LOG):
        return 12

    text = open(LOG, encoding="utf-8", errors="replace").read()
    starts = list(START.finditer(text))
    if not starts:
        return 12  # 실행 흔적이 아예 없음

    last = starts[-1]
    goal = int(last.group(1))
    block = text[last.end():]
    done = block.count("공개 완료:")
    ended = EXIT.search(block)
    today = date.today().isoformat()

    # 마지막 실행이 오늘이 아니면 = 오늘 밤 실행이 통째로 실패한 것
    # ponytail: 날짜만 비교하므로 자정 넘겨 점검하면 오판함. 점검은 23:10 고정이라 무해.
    if ended and ended.group(1) != today:
        return 12

    return max(0, goal - done)


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

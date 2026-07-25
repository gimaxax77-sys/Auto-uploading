# check_upload.missing_count 가 로그를 보고 모자란 편수를 맞게 세는지 확인
import os
import tempfile
from datetime import date, timedelta

import check_upload

오늘 = date.today().isoformat()
어제 = (date.today() - timedelta(days=1)).isoformat()


def 계산(로그: str) -> int:
    path = os.path.join(tempfile.gettempdir(), "t_upload_log.txt")
    open(path, "w", encoding="utf-8").write(로그)
    old, check_upload.LOG = check_upload.LOG, path
    try:
        return check_upload.missing_count()
    finally:
        check_upload.LOG = old
        os.remove(path)


완료 = f"오늘 12편을 공개로 올립니다.\n" + "  공개 완료: x\n" * 12 + f"[{오늘} 23:05:03.59] exit=0\n"
절반 = "오늘 12편을 공개로 올립니다.\n" + "  공개 완료: x\n" * 5  # 중간에 강제 종료(exit 줄 없음)
어제것 = "오늘 12편을 공개로 올립니다.\n" + "  공개 완료: x\n" * 12 + f"[{어제} 23:05:03.59] exit=0\n"

assert 계산(완료) == 0, "정상 완료면 추가 업로드 없음"
assert 계산(절반) == 7, "5편만 올라갔으면 7편 더"
assert 계산(어제것) == 12, "오늘 실행 흔적이 없으면 12편 전량"
assert 계산("") == 12, "로그가 비었으면 12편 전량"
print("통과: 4/4")

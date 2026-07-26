# check_upload.missing_count 가 진행 기록을 보고 모자란 편수를 맞게 세는지 확인
import json
import os
import tempfile
from datetime import date, timedelta

import check_upload

오늘 = date.today().isoformat()
어제 = (date.today() - timedelta(days=1)).isoformat()


def 계산(기록) -> int:
    path = os.path.join(tempfile.gettempdir(), "t_last_run.json")
    if 기록 is None:
        if os.path.exists(path):
            os.remove(path)
    elif isinstance(기록, str):
        open(path, "w", encoding="utf-8").write(기록)
    else:
        json.dump(기록, open(path, "w", encoding="utf-8"))
    old, check_upload.STATE = check_upload.STATE, path
    try:
        return check_upload.missing_count()
    finally:
        check_upload.STATE = old
        if os.path.exists(path):
            os.remove(path)


assert 계산({"date": 오늘, "goal": 12, "done": 12}) == 0, "정상 완료면 추가 업로드 없음"
assert 계산({"date": 오늘, "goal": 12, "done": 5}) == 7, "5편만 올라갔으면 7편 더"
assert 계산({"date": 어제, "goal": 12, "done": 12}) == 12, "오늘 실행 흔적이 없으면 12편 전량"
assert 계산({"date": 오늘, "goal": 7, "done": 7}) == 0, "점검이 이어올린 뒤 재점검하면 0"
assert 계산(None) == 12, "기록이 없으면 12편 전량"
assert 계산("깨진파일") == 12, "기록이 깨졌으면 12편 전량"
assert 계산({"date": 오늘, "goal": 99, "done": 0}) == 12, "하루 12편을 넘겨 올리지 않음"
print("통과: 7/7")

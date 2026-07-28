# analyze_video 의 주소 파싱과 자막 문장 합치기가 맞는지 확인
import analyze_video as a

for 입력, 기대 in [
    ("https://youtu.be/qEVZ7AgB7zI?si=abc", "qEVZ7AgB7zI"),
    ("https://www.youtube.com/watch?v=qEVZ7AgB7zI&t=10s", "qEVZ7AgB7zI"),
    ("https://www.youtube.com/shorts/qEVZ7AgB7zI", "qEVZ7AgB7zI"),
    ("https://www.youtube.com/embed/qEVZ7AgB7zI", "qEVZ7AgB7zI"),
    ("qEVZ7AgB7zI", "qEVZ7AgB7zI"),
]:
    assert a.video_id(입력) == 기대, f"{입력} -> {a.video_id(입력)}"


class 조각:
    def __init__(self, start, text):
        self.start, self.text = start, text


# 유튜브 자동자막은 문장 중간에서 토막납니다. 문장 단위로 다시 붙어야 합니다.
문장 = a.문장으로([
    조각(0.0, "클로드 돈을 번다는데 도대체 뭘로"),
    조각(2.6, "버는 걸까요? 저는 오백만 원을"),
    조각(4.7, "써 봤습니다."),
])
assert len(문장) == 2, f"문장이 2개여야 하는데 {len(문장)}개"
assert 문장[0][1] == "클로드 돈을 번다는데 도대체 뭘로 버는 걸까요?"
assert 문장[1][1] == "저는 오백만 원을 써 봤습니다."
assert 문장[0][0] == 0.0, "첫 문장 시작 시각은 첫 조각 시각"

# 문장부호가 없으면 통째로 한 덩어리로 둡니다(잘라 버리면 안 됩니다).
문장 = a.문장으로([조각(0.0, "부호가"), 조각(1.0, "없는 자막")])
assert 문장 == [(0.0, "부호가 없는 자막")], 문장

assert a.초표기(0) == "0:00" and a.초표기(75) == "1:15"
print("통과: 주소 5 · 문장합치기 2 · 시간표기 2")

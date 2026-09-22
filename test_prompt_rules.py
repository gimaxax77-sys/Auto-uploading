# 프롬프트 규칙층 점검 — longform_trial/gen.py build() 가 결함별 문장을 제 자리에만 얹는지 본다
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "longform_trial"))
from gen import ANCHOR, AIRBURST, ERA, NO_TEXT, ONE_HEAD, build  # noqa: E402

S = "cinematic film still, anamorphic widescreen, photorealistic"

# ④ 동물 낱말이 사람에게 붙는 것 — 떼어 놓는다(사람 머리에 뿔이 달린 실제 결함)
p = build("reindeer herders in fur clothes looking up in shock", S)
assert "reindeer herders" not in p.lower(), p
assert "herders with their reindeer" in p, p

# ②⑤ 사람이 나오면 «머리 하나»와 시대·민족을 박는다
assert ONE_HEAD in p and ERA in p

# 사람이 없는 장면에는 안 붙인다 — 프롬프트가 쓸데없이 길어지지 않게
land = build("aerial view of endless Siberian taiga at dawn, mist over dark pine forest", S)
assert ONE_HEAD not in land and ERA not in land, land

# ① 폭발은 언제나 공중이다
assert AIRBURST in build("a gigantic explosion flash in the air high above the forest", S)
assert AIRBURST in build("an airplane flying at the same height as a distant explosion", S)

# ⚠ «blast» 는 충격파를 뜻하는 자리가 많다 — 여기에 공중폭발 문장을 붙이면 그림이 틀어진다
assert AIRBURST not in build("thousands of trees being flattened at once by a wind blast", S)
assert AIRBURST not in build("a man being thrown off his chair by a blast of air", S)

# ② 이름난 인물은 묘사를 머리에 고정한다 — 가르는 기준은 영문이 아니라 한국어 내레이션이다
k1 = build("a scientist following lines of fallen trees with a compass", S, "쿨릭은 나무가 쓰러진 방향을 따라갔습니다.")
assert ANCHOR["쿨릭"] in k1
# 두 번 돌려도 한 번만 붙어야 한다
assert build(k1, S, "쿨릭은").count("Leonid Kulik, a Russian scientist") == 1, "고정 묘사가 두 번 붙었다"
# ⛔ 현대 연구자 장면에는 1908년 인물 얼굴이 붙으면 안 된다
assert ANCHOR["쿨릭"] not in build("a modern scientist watching a glowing 3D simulation", S, "오늘날 과학자들은")

# ③ 글자 금지와 화풍 지배는 모든 장면에
for q in (p, land, k1):
    assert NO_TEXT in q and "no other rendering style" in q

print("통과")

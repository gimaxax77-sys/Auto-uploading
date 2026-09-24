# 참조 이미지 시험 — klein 4B 가 참조 그림(ReferenceLatent)으로 같은 얼굴을 지키는지, 글 묘사만 쓴 경우와 나란히 비교한다
# 사용: python refprobe.py        (참조 1장 + 참조 사용 3장 + 글만 3장 + 비교 시트)
#       python refprobe.py two    (참조 2장 — 두 사람 한 장면 3컷 + 글만 3컷 + 비교 시트)
#       python refprobe.py face   (표정 4종 — 주인 참조·주인 글만·손님 참조 + 비교 시트)
import os, shutil, sys, time

import sample60 as S6
from gen import COMFY_OUT, NO_TEXT, STYLES, run, workflow

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "refprobe")
REF_IN = "refprobe_ref.png"          # ComfyUI/input 에 복사해 LoadImage 로 읽는다
W, H = 1536, 864
STYLE = STYLES["flat"]
# 구별점이 많은 인물로 잡는다 — 흉터·안경·머리 모양이 바뀌면 딴사람으로 바로 보인다
WHO = ("an elderly East Asian shopkeeper with silver hair tied in a small topknot, a thin white mustache, "
       "a scar across his left eyebrow, round amber-tinted spectacles and a dark green high-collared coat")
REF = f"Waist-up portrait of {WHO}, standing behind the wooden counter of a small cluttered curio shop, facing the viewer"
# 시대·장소·각도를 전부 바꾼다(«이름 없는 가게» 는 어느 시대에나 나타난다)
SCENES = [
    "standing in a bustling Joseon-era Korean market street at dawn, full body, side view",
    "sitting at a table in a candlelit 1920s European cafe at night, three-quarter view, holding a teacup",
    "walking under a black umbrella on a rainy modern city street with neon signs, medium shot from a low angle",
]


def tail(p):
    return f"{p}. {STYLE}. {NO_TEXT}"


def ref_wf(prompt, seed, tag, img=REF_IN):
    """gen.workflow 에 참조 그림을 얹는다 — 불러오기 → VAE 부호화 → ReferenceLatent 를 긍정 조건에 붙임"""
    wf = workflow(prompt, seed, W, H, tag)
    wf["20"] = {"class_type": "LoadImage", "inputs": {"image": img}}
    wf["21"] = {"class_type": "VAEEncode", "inputs": {"pixels": ["20", 0], "vae": ["3", 0]}}
    wf["22"] = {"class_type": "ReferenceLatent", "inputs": {"conditioning": ["4", 0], "latent": ["21", 0]}}
    wf["7"]["inputs"]["positive"] = ["22", 0]
    return wf


def main():
    os.makedirs(OUT, exist_ok=True)
    ref = os.path.join(OUT, "ref.png")
    if not os.path.exists(ref):
        run(workflow(tail(REF), 3000, W, H, "refprobe_ref"), ref)
    shutil.copy(ref, os.path.join(os.path.dirname(COMFY_OUT), "input", REF_IN))
    for k, scene in enumerate(SCENES, 1):
        # a = 참조 + 짧은 글(생김새를 글로 다시 안 적음) · b = 참조 없이 생김새 전부를 글로(지금 방식). 시드는 같게
        for kind, wf in (("a", ref_wf(tail(f"The same man as in the reference image, same face, hair, spectacles and coat, {scene}"), 3000 + k, f"refprobe_a{k}")),
                         ("b", workflow(tail(f"{WHO}, {scene}"), 3000 + k, W, H, f"refprobe_b{k}"))):
            dst = os.path.join(OUT, f"{kind}{k}.png")
            if os.path.exists(dst):
                continue
            t0 = time.time()
            run(wf, dst)
            print(f"{kind}{k} {time.time()-t0:.1f}s", flush=True)
    # 비교 시트 — 윗줄 참조+a1~a3 · 아랫줄 참조+b1~b3
    names = ["ref", "a1", "a2", "a3", "ref", "b1", "b2", "b3"]
    ins = [x for n in names for x in ("-i", os.path.join(OUT, f"{n}.png"))]
    fc = "".join(f"[{i}:v]scale=640:-1[v{i}];" for i in range(8)) + "".join(f"[v{i}]" for i in range(8)) + "xstack=inputs=8:layout=0_0|w0_0|w0+w1_0|w0+w1+w2_0|0_h0|w0_h0|w0+w1_h0|w0+w1+w2_h0"
    sheet = os.path.join(OUT, "sheet_ref.jpg")
    S6.sh(["ffmpeg", "-y", *ins, "-filter_complex", fc, "-frames:v", "1", "-q:v", "3", sheet])
    print(f"시트 {sheet} (윗줄 참조 사용 · 아랫줄 글만)")


# ── 참조 2장 — 두 사람이 한 장면에 나올 때 각자 얼굴을 지키는지, 서로 섞이지 않는지 ──────────────
# 성별·나이·색을 주인과 정반대로 잡아 섞이면 바로 보이게 한다
WHO2 = ("a young Korean woman with a short black bob haircut, a single red hairpin, freckles across her nose, "
        "wearing a mustard-yellow cardigan over a white blouse")
REF2 = f"Waist-up portrait of {WHO2}, standing in a plain sunlit room, facing the viewer"
REF2_IN = "refprobe_ref2.png"
DUO = [
    "the young woman places a small wooden box on the shop counter while the old shopkeeper leans in to look at it, inside the curio shop, medium shot",
    "the old shopkeeper hands the young woman a glowing pocket watch across the counter, close two-shot, warm lamplight",
    "the old shopkeeper and the young woman standing side by side outside the shop door on a snowy night street, full body",
]


def duo_wf(prompt, seed, tag):
    """참조 두 장을 ReferenceLatent 두 번 이어 붙인다(1번 = 주인, 2번 = 손님)"""
    wf = ref_wf(prompt, seed, tag)
    wf["23"] = {"class_type": "LoadImage", "inputs": {"image": REF2_IN}}
    wf["24"] = {"class_type": "VAEEncode", "inputs": {"pixels": ["23", 0], "vae": ["3", 0]}}
    wf["25"] = {"class_type": "ReferenceLatent", "inputs": {"conditioning": ["22", 0], "latent": ["24", 0]}}
    wf["7"]["inputs"]["positive"] = ["25", 0]
    return wf


def main2():
    ref, ref2 = os.path.join(OUT, "ref.png"), os.path.join(OUT, "ref2.png")
    if not os.path.exists(ref2):
        run(workflow(tail(REF2), 3100, W, H, "refprobe_ref2"), ref2)
    inp = os.path.join(os.path.dirname(COMFY_OUT), "input")
    shutil.copy(ref, os.path.join(inp, REF_IN))
    shutil.copy(ref2, os.path.join(inp, REF2_IN))
    for k, scene in enumerate(DUO, 1):
        a = ("The old shopkeeper is exactly the man from the first reference image and the young woman is exactly "
             f"the woman from the second reference image, each keeping their own face, hair and clothes; {scene}")
        b = f"The old shopkeeper is {WHO}. The young woman is {WHO2}. {scene}"
        for kind, wf in (("c", duo_wf(tail(a), 3100 + k, f"refprobe_c{k}")), ("d", workflow(tail(b), 3100 + k, W, H, f"refprobe_d{k}"))):
            dst = os.path.join(OUT, f"{kind}{k}.png")
            if os.path.exists(dst):
                continue
            t0 = time.time()
            run(wf, dst)
            print(f"{kind}{k} {time.time()-t0:.1f}s", flush=True)
    # 시트 — 윗줄 참조1·참조2·c1·c2·c3 · 아랫줄 참조1·참조2·d1·d2·d3
    names = ["ref", "ref2", "c1", "c2", "c3", "ref", "ref2", "d1", "d2", "d3"]
    ins = [x for n in names for x in ("-i", os.path.join(OUT, f"{n}.png"))]
    lay = "|".join(f"{'+'.join(f'w{j}' for j in range(i % 5)) or 0}_{'h0' if i >= 5 else 0}" for i in range(10))
    fc = "".join(f"[{i}:v]scale=640:-1[v{i}];" for i in range(10)) + "".join(f"[v{i}]" for i in range(10)) + f"xstack=inputs=10:layout={lay}"
    sheet = os.path.join(OUT, "sheet_duo.jpg")
    S6.sh(["ffmpeg", "-y", *ins, "-filter_complex", fc, "-frames:v", "1", "-q:v", "3", sheet])
    print(f"시트 {sheet} (윗줄 참조 2장 사용 · 아랫줄 글만)")


# ── 표정 — 참조가 무표정까지 복사해 감정이 굳는지. 주인(참조) · 주인(글만) · 손님(참조) 세 줄 ──────────
EXPR = [
    "laughing loudly with {p} mouth wide open and eyes squeezed shut, head tilted back",
    "crying, tears streaming down {p} cheeks, eyebrows raised in grief, mouth trembling",
    "furious, shouting with {p} mouth open, eyebrows sharply furrowed, fists clenched",
    "shocked, eyes wide open, mouth agape, both hands raised beside {p} face",
]


def main3():
    inp = os.path.join(os.path.dirname(COMFY_OUT), "input")
    shutil.copy(os.path.join(OUT, "ref.png"), os.path.join(inp, REF_IN))
    shutil.copy(os.path.join(OUT, "ref2.png"), os.path.join(inp, REF2_IN))
    shot = "close-up, inside the curio shop"
    for k, ex in enumerate(EXPR, 1):
        m, w = ex.format(p="his"), ex.format(p="her")
        jobs = (("s", ref_wf(tail(f"The same man as in the reference image, same face, hair, spectacles and coat, now {m}, {shot}"), 3200 + k, f"refprobe_s{k}")),
                ("t", workflow(tail(f"{WHO}, {m}, {shot}"), 3200 + k, W, H, f"refprobe_t{k}")),
                ("w", ref_wf(tail(f"The same woman as in the reference image, same face, hair, hairpin and cardigan, now {w}, {shot}"), 3200 + k, f"refprobe_w{k}", REF2_IN)))
        for kind, wf in jobs:
            dst = os.path.join(OUT, f"{kind}{k}.png")
            if os.path.exists(dst):
                continue
            t0 = time.time()
            run(wf, dst)
            print(f"{kind}{k} {time.time()-t0:.1f}s", flush=True)
    # 시트 — 줄마다 참조 + 표정 4장 (주인 참조 / 주인 글만 / 손님 참조)
    names = ["ref", "s1", "s2", "s3", "s4", "ref", "t1", "t2", "t3", "t4", "ref2", "w1", "w2", "w3", "w4"]
    ins = [x for n in names for x in ("-i", os.path.join(OUT, f"{n}.png"))]
    lay = "|".join(f"{'+'.join(f'w{j}' for j in range(i % 5)) or 0}_{'+'.join(f'h{j}' for j in range(0, i // 5 * 5, 5)) or 0}" for i in range(15))
    fc = "".join(f"[{i}:v]scale=640:-1[v{i}];" for i in range(15)) + "".join(f"[v{i}]" for i in range(15)) + f"xstack=inputs=15:layout={lay}"
    sheet = os.path.join(OUT, "sheet_expr.jpg")
    S6.sh(["ffmpeg", "-y", *ins, "-filter_complex", fc, "-frames:v", "1", "-q:v", "3", sheet])
    print(f"시트 {sheet} (줄: 주인 참조 · 주인 글만 · 손님 참조 / 열: 참조·웃음·울음·분노·놀람)")


if __name__ == "__main__":
    {"two": main2, "face": main3}.get(sys.argv[1] if sys.argv[1:] else "", main)()

# 참조 이미지 시험 — klein 4B 가 참조 그림(ReferenceLatent)으로 같은 얼굴을 지키는지, 글 묘사만 쓴 경우와 나란히 비교한다
# 사용: python refprobe.py   (참조 1장 + 참조 사용 3장 + 글만 3장 + 비교 시트)
import os, shutil, time

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


def ref_wf(prompt, seed, tag):
    """gen.workflow 에 참조 그림을 얹는다 — 불러오기 → VAE 부호화 → ReferenceLatent 를 긍정 조건에 붙임"""
    wf = workflow(prompt, seed, W, H, tag)
    wf["20"] = {"class_type": "LoadImage", "inputs": {"image": REF_IN}}
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


if __name__ == "__main__":
    main()

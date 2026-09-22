# z_image turbo 시험 — 승인받은 klein 시네마틱과 같은 프롬프트·해상도로 4장을 뽑아 나란히 비교한다
# 사용: python zprobe.py            (그림 4장 + 비교 시트)
import os, time

import sample60 as S6
from gen import run

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "zprobe")
KLEIN = os.path.join(HERE, "out", "s60", "img_cine")
STYLE = S6.MODELS["cine"]
W, H = 1920, 1088
# (장면, 컷) — 풍경·사람 얼굴·공중폭발·대량 디테일 네 가지로 약점을 갈라 본다
PICK = [(0, 0), (3, 1), (4, 0), (6, 0)]


def zwf(prompt, seed, steps=8):
    """z_image turbo — CLIPLoader type 은 flux/flux2 만 아니면 되고(comfy/sd.py:1869), 그러면 Qwen3-4B 가 z_image 경로로 붙는다"""
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_turbo_int8_convrot.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "lumina2", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": prompt}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": ""}},
        "6": {"class_type": "EmptySD3LatentImage", "inputs": {"width": W, "height": H, "batch_size": 1}},
        "7": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["6", 0],
                                                   "seed": seed, "steps": steps, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "zprobe"}},
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    for si, k in PICK:
        dst = os.path.join(OUT, f"{si:02d}_{k}.png")
        if os.path.exists(dst):
            continue
        p = S6.SHOTS[si][1][k][0]
        t0 = time.time()
        run(zwf(f"{p}. {STYLE}, no text, no letters, no watermark", 2000 + si * 10 + k), dst)
        print(f"{si:02d}_{k} {time.time()-t0:.1f}s", flush=True)
    # 비교 시트 — 위 klein, 아래 z_image
    row = lambda d: [os.path.join(d, f"{si:02d}_{k}.png") for si, k in PICK]
    ins = [x for p in row(KLEIN) + row(OUT) for x in ("-i", p)]
    fc = "".join(f"[{i}:v]scale=640:-1[v{i}];" for i in range(8)) + "".join(f"[v{i}]" for i in range(8)) + "xstack=inputs=8:layout=0_0|w0_0|w0+w1_0|w0+w1+w2_0|0_h0|w0_h0|w0+w1_h0|w0+w1+w2_h0"
    sheet = os.path.join(OUT, "sheet_zimage.jpg")
    S6.sh(["ffmpeg", "-y", *ins, "-filter_complex", fc, "-frames:v", "1", "-q:v", "3", sheet])
    print(f"시트 {sheet} · {os.path.getsize(sheet)/2**20:.1f}MB (윗줄 klein · 아랫줄 z_image)")


if __name__ == "__main__":
    main()

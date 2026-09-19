# 1단계 시험 — 장면 그림을 로컬 ComfyUI(FLUX.2 klein 4B distilled)로 만든다. 사용: python gen.py <화풍키> <장면번호들|all> [--w 1536 --h 864]
import json, os, shutil, sys, time, urllib.request
from tts import scenes

HOST = "http://127.0.0.1:8188"
COMFY_OUT = "D:/.CODE/AXdata/_TOOLS/ComfyUI/output"
HERE = os.path.dirname(os.path.abspath(__file__))
NO_TEXT = "no text, no letters, no words, no watermark"
STYLES = {
    "flat": "flat 2D cartoon illustration, clean bold outlines, simple shapes, soft muted color palette, educational documentary animation style",
    "book": "hand-drawn storybook illustration, ink lines with warm watercolor wash, textured paper, gentle cinematic lighting",
}


def api(path, body=None):
    req = urllib.request.Request(HOST + path, data=json.dumps(body).encode() if body else None, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def workflow(prompt, seed, w, h, tag):
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "flux-2-klein-4b-fp8.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "flux2", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "flux2-vae.safetensors"}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": prompt}},
        "5": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["4", 0]}},
        "6": {"class_type": "EmptyFlux2LatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "7": {"class_type": "CFGGuider", "inputs": {"model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0], "cfg": 1.0}},
        "8": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        "9": {"class_type": "Flux2Scheduler", "inputs": {"steps": 4, "width": w, "height": h}},
        "10": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "11": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["10", 0], "guider": ["7", 0], "sampler": ["8", 0], "sigmas": ["9", 0], "latent_image": ["6", 0]}},
        "12": {"class_type": "VAEDecode", "inputs": {"samples": ["11", 0], "vae": ["3", 0]}},
        "13": {"class_type": "SaveImage", "inputs": {"images": ["12", 0], "filename_prefix": tag}},
    }


def run(wf, dst):
    pid = api("/prompt", {"prompt": wf})["prompt_id"]
    while True:
        h = api(f"/history/{pid}").get(pid)
        if h and h.get("status", {}).get("completed"):
            img = next(iter(h["outputs"].values()))["images"][0]
            shutil.move(os.path.join(COMFY_OUT, img.get("subfolder", ""), img["filename"]), dst)
            return
        if h and h.get("status", {}).get("status_str") == "error":
            raise RuntimeError(json.dumps(h["status"])[:500])
        time.sleep(0.3)


def main(argv):
    opts = dict(zip(argv[2::2], argv[3::2]))
    style, pick = argv[0], argv[1]
    w, h = int(opts.get("--w", 1536)), int(opts.get("--h", 864))
    rows = scenes()
    ids = range(1, len(rows) + 1) if pick == "all" else [int(x) for x in pick.split(",")]
    out = os.path.join(HERE, "out", f"img_{style}")
    os.makedirs(out, exist_ok=True)
    log = open(os.path.join(HERE, "out", f"gen_{style}.tsv"), "a", encoding="utf-8")
    for i in ids:
        dst = os.path.join(out, f"{i:03d}.png")
        if os.path.exists(dst):
            continue
        prompt = f"{rows[i-1][2]}. {STYLES[style]}, {NO_TEXT}"
        t0 = time.time()
        run(workflow(prompt, 1000 + i, w, h, f"lf_{style}_{i:03d}"), dst)
        dt = time.time() - t0
        log.write(f"{i}\t{dt:.2f}\n"); log.flush()
        print(f"{i:03d} {dt:5.1f}s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])

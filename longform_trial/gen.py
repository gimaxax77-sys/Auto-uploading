# 1단계 시험 — 장면 그림을 로컬 ComfyUI(FLUX.2 klein 4B distilled)로 만든다. 사용: python gen.py <화풍키> <장면번호들|all> [--w 1536 --h 864]
import json, os, re, shutil, sys, time, urllib.request
from tts import scenes

HOST = "http://127.0.0.1:8188"
COMFY_OUT = "D:/.CODE/AXdata/_TOOLS/ComfyUI/output"
HERE = os.path.dirname(os.path.abspath(__file__))
NO_TEXT = "no text, no letters, no words, no numbers, no watermark, no signature, no caption"
STYLES = {
    "flat": "flat 2D cartoon illustration, clean bold outlines, simple shapes, soft muted color palette, educational documentary animation style",
    "book": "hand-drawn storybook illustration, ink lines with warm watercolor wash, textured paper, gentle cinematic lighting",
}

# ── 프롬프트 규칙층 ────────────────────────────────────────────────────────────
# 장면 설명에 조건별 문장을 얹어 되풀이되는 결함을 막는다. 방식(층을 순서대로 덧붙이기)은
# 아트스튜디오(09) app/services/gemini_service.py:160~210 에서 가져왔고 문장은 다큐용으로 다시 썼다.
# 막으려는 것 — ① 공중폭발을 지상폭발로 그림 ② 인물이 장면마다 딴사람 ③ 가짜 글자
#              ④ 동물 낱말이 사람에게 붙음(순록치기 → 머리에 뿔) ⑤ 시대·민족 이탈
ERA = ("Period and place: 1908 in the remote Siberian taiga of the Russian Empire, period-accurate clothing; "
       "any indigenous people are Evenki with East Asian facial features")
ONE_HEAD = ("each person has exactly one human head and one human body, "
            "no antlers, horns or animal ears on any person, no duplicated faces")
# 이 이야기의 폭발은 언제나 공중이다. ⚠ «blast» 는 충격파를 뜻하는 자리가 많아(바람·아래로 누르는) 방아쇠에서 뺐다.
AIRBURST = ("the explosion is a fireball hanging high in the open sky with clear air beneath it, "
            "never a mushroom cloud and never touching the ground")
# 이름난 인물은 묘사를 고정해 장면마다 같은 사람으로 나오게 한다(현황판 에셋 탭의 «머리글 고정»).
# ⚠ 영문 그림 설명에는 이름이 한 번도 안 나오고 «a scientist» 로만 적혀 있다(실측). 그래서 **한국어 내레이션**으로 가른다 —
#    영문의 scientist 로 가르면 현대 연구자 장면(132·186 등)에까지 1908년 인물 얼굴이 박힌다.
ANCHOR = {
    "쿨릭": "Leonid Kulik, a Russian scientist in his forties with a short dark beard, round wire-rimmed glasses, "
           "a heavy canvas field coat and a flat cap",
}
# 동물 낱말이 사람 낱말을 꾸미면 모델이 사람에게 뿔을 단다. 문장에서 떼어 놓는다.
SPLIT = [(r"\breindeer (herders?|people|men|women|families|tribe)\b", r"\1 with their reindeer")]
PEOPLE = (r"\b(people|persons?|m[ae]n|wom[ae]n|herders?|villagers?|crowd|famil(y|ies)|scientists?|hunters?"
          r"|witnesses?|children|boys?|girls?|workers?|soldiers?|peasants?|figures?)\b")
BLAST = r"\b(explosions?|fireballs?|detonations?|explod(es|ing))\b"


def build(desc, style, ko=""):
    """장면 설명·화풍·그 장면의 한국어 내레이션을 받아 최종 프롬프트를 만든다. 규칙층을 순서대로 얹는다."""
    p = desc.strip().rstrip(".")
    for pat, rep in SPLIT:
        p = re.sub(pat, rep, p, flags=re.I)
    for key, who in ANCHOR.items():
        if key in ko and who not in p:
            p = f"{who}. {p}"
    parts = [p, style]
    if re.search(PEOPLE, p, re.I):
        parts += [ONE_HEAD, ERA]
    if re.search(BLAST, p, re.I):
        parts.append(AIRBURST)
    parts += [NO_TEXT, f"entirely rendered as {style.split(',')[0]}, no other rendering style"]
    return ". ".join(parts)


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
        prompt = build(rows[i - 1][2], STYLES[style], rows[i - 1][1])
        t0 = time.time()
        run(workflow(prompt, 1000 + i, w, h, f"lf_{style}_{i:03d}"), dst)
        dt = time.time() - t0
        log.write(f"{i}\t{dt:.2f}\n"); log.flush()
        print(f"{i:03d} {dt:5.1f}s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])

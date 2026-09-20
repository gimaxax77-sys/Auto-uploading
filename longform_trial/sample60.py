# 롱폼 개선 60초 샘플 — 도입부(장면 1~14)를 빠른 컷·이펙트·효과음·그래픽 카드로 다시 만들어 음성·그림 모델을 비교한다
# 사용: python sample60.py tts | img <화풍> | build <화풍> <voice>
#       화풍 = doc(다큐 실사) · cine(영화 시네마틱) · arch(1908 흑백 기록사진) · klein(만화) · illu(애니)
#       voice = neural2 | hyunsu | injoon
import asyncio, os, subprocess, sys, time
import edge_tts
from gen import run, workflow as klein_wf

HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.join(HERE, "out", "s60")
FPS, W, H, GAP = 30, 1920, 1080, 0.15
MUSIC = os.path.join(HERE, "..", "music", "웅장")
FONT = "C\\:/Windows/Fonts/malgunbd.ttf"

# (문장, [(그림 설명, 이펙트)…], 카드) — 이펙트: push 밀기 · pan 옆으로 · punch 튕겨 확대 · flash 흰 번쩍 · shake 흔들림
SHOTS = [
    ("1908년 6월 30일 아침, 시베리아의 깊은 숲은 여느 날처럼 조용했습니다.",
     [("aerial view of endless Siberian taiga at dawn, mist over dark pine forest, a winding river", "push"),
      ("close-up of dew drops on pine needles, soft golden morning sun rays through the trees", "pan")], None),
    ("새들이 울고, 강물은 천천히 흘렀습니다.",
     [("two small birds singing on a pine branch at sunrise", "push"),
      ("a calm river flowing through the forest, reflections of the pale morning sky", "pan")], None),
    ("그리고 아침 7시 14분, 하늘이 둘로 갈라졌습니다.",
     [("an old brass pocket watch in a hand, early morning light", "punch"),
      ("the morning sky torn open by a blinding white streak of light, dark forest silhouette below", "flash")], None),
    ("태양보다 밝은 불덩이가 북쪽 하늘을 가로질렀습니다.",
     [("a huge blazing fireball streaking across the sky with a long burning trail, high above the taiga", "pan"),
      ("reindeer herders in fur clothes looking up in shock, faces lit by intense light", "punch")], "whoosh"),
    ("몇 초 뒤, 숲 위의 하늘에서 거대한 폭발이 일어났습니다.",
     [("a gigantic explosion high up in the sky far above the forest, a bright ball of fire floating in the air, the ground below untouched", "flash"),
      ("wide shot, blinding white light filling the whole sky above a tiny forest", "shake")], "boom"),
    ("폭풍 같은 바람이 사방으로 퍼져 나갔습니다.",
     [("a ring-shaped shockwave spreading outward through the air from a point high in the sky, clouds blown away", "shake"),
      ("violent wind bending pine trees, leaves and dust flying", "shake")], "rumble"),
    ("나무들이 한꺼번에 누웠습니다.",
     [("thousands of pine trees knocked flat, all pointing the same direction, smoke drifting", "shake"),
      ("close-up of a thick pine trunk snapping and falling", "punch")], None),
    ("쓰러진 숲의 넓이는 약 2,150제곱킬로미터였습니다.",
     [("aerial view of a vast flattened forest spreading in a huge butterfly shape, seen from very high", "card:area")], None),
    ("서울 전체 면적의 세 배가 넘는 크기입니다.",
     [("aerial view of a flattened forest stretching to the horizon", "card:seoul")], None),
    ("그런데 이상한 일이 있었습니다.",
     [("a lone explorer silhouette standing among fallen trees in mysterious fog", "push")], None),
    ("그렇게 큰 폭발이 있었는데, 땅에는 구덩이가 없었습니다.",
     [("the center of a flattened forest, flat ground with bare branchless trees still standing, no crater anywhere", "pan"),
      ("close-up of undisturbed mossy ground", "push")], None),
    ("하늘에서 떨어진 돌도, 쇳덩이도 찾을 수 없었습니다.",
     [("hands digging in swampy soil and finding nothing", "push"),
      ("an empty open palm holding only mud", "punch")], None),
    ("도대체 그날 아침, 시베리아 하늘에서는 무슨 일이 일어났을까요?",
     [("dramatic sky over the taiga with a faint glowing trail, mysterious mood", "push")], None),
    ("오늘은 지금까지도 과학자들이 토론을 이어가는 사건, 퉁구스카 대폭발 이야기입니다.",
     [("a bright burst of light in the sky over a dark silhouette forest, epic wide composition", "card:title")], "boom"),
]
CARDS = {   # 그래픽 카드 — 숫자는 그림이 아니라 글자로 넣는다(모델은 숫자를 가짜 글자로 그린다)
    "area": [("%{eif\\:min(2150\\,t*2150/1.0)\\:d}", 190, -60, "white"), ("제곱킬로미터", 70, 90, "0xFFD54A")],
    "seoul": [("서울 면적의", 70, -110, "white"), ("3배 이상", 170, 40, "0xFFD54A")],
    "title": [("퉁구스카 대폭발", 150, -20, "white"), ("1908 · 시베리아", 60, 110, "0xFFD54A")],
}
MODELS = {
    "klein": "flat 2D cartoon illustration, clean bold outlines, soft muted color palette, cinematic documentary animation style, dramatic lighting",
    "illu": "anime illustration, detailed painted background, cinematic lighting, dramatic atmosphere, masterpiece, best quality",
    # 실사 3종 — 같은 장면을 서로 다른 «느낌»으로 (2026-09-21, 만화풍 4편 불합격 후)
    "doc": "documentary photograph, shot on 35mm film, natural overcast daylight, muted earth tones, photojournalism, realistic textures, sharp focus, photorealistic",
    "cine": "cinematic film still, anamorphic widescreen, dramatic volumetric god rays, shallow depth of field, rich contrast, epic scale, color graded teal and warm amber, photorealistic, 8k",
    "arch": "vintage photograph taken in 1908, silver gelatin print, black and white, heavy film grain, soft period lens, slight sepia tone, aged paper edges, historical archive photo, photorealistic",
}
GRADE = {   # 조립 단계 색감 — 화풍마다 다르게
    "doc": "eq=saturation=0.92:contrast=1.04,vignette=PI/6,noise=alls=4:allf=t",
    "cine": "eq=saturation=1.22:contrast=1.12,vignette=PI/5,noise=alls=3:allf=t",
    "arch": "hue=s=0,eq=contrast=1.15:brightness=0.02,vignette=PI/4,noise=alls=7:allf=t",   # alls=14 는 53초에 806MB — 입자가 압축을 못 먹는다
}
NEG = "text, letters, words, watermark, signature, logo, lowres, blurry, bad anatomy, extra fingers"
VOICES = {"neural2": ("google", "ko-KR-InJoonNeural"), "hyunsu": ("edge", "ko-KR-HyunsuMultilingualNeural"), "injoon": ("edge", "ko-KR-InJoonNeural")}
RATE = "+10%"


def sh(args):
    r = subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if r.returncode:
        raise RuntimeError(r.stderr.decode("utf-8", "replace")[-1500:])


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]).strip())


def shots():
    return [(si, k, p, fx) for si, (_, ps, _) in enumerate(SHOTS) for k, (p, fx) in enumerate(ps)]


# ---- 음성 ----
def tts():
    sys.path.insert(0, os.path.dirname(HERE))
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(HERE), ".env"))
    from video import narrate_google
    for v, (eng, voice) in VOICES.items():
        d = os.path.join(S, "tts", v); os.makedirs(d, exist_ok=True)
        for i, (text, _, _) in enumerate(SHOTS):
            p = os.path.join(d, f"{i:02d}.mp3")
            if os.path.exists(p):
                continue
            if eng == "google":
                narrate_google(text, p, voice, RATE)
            else:
                asyncio.run(edge_tts.Communicate(text, voice, rate=RATE).save(p))
        print(v, f"{sum(dur(os.path.join(d, f'{i:02d}.mp3')) for i in range(len(SHOTS))):.1f}초")


# ---- 그림 ----
def illu_wf(prompt, seed, tag):
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "Illustrious-XL-v2.0.safetensors"}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": prompt}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": NEG}},
        "4": {"class_type": "EmptyLatentImage", "inputs": {"width": 1344, "height": 768, "batch_size": 1}},
        "5": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "positive": ["2", 0], "negative": ["3", 0], "latent_image": ["4", 0],
                                                    "seed": seed, "steps": 28, "cfg": 5.5, "sampler_name": "euler_ancestral", "scheduler": "normal", "denoise": 1.0}},
        "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "SaveImage", "inputs": {"images": ["6", 0], "filename_prefix": tag}},
    }


def img(model):
    d = os.path.join(S, f"img_{model}"); os.makedirs(d, exist_ok=True)
    for n, (si, k, p, fx) in enumerate(shots()):
        dst = os.path.join(d, f"{si:02d}_{k}.png")
        if os.path.exists(dst):
            continue
        prompt, t0 = f"{p}. {MODELS[model]}", time.time()
        if model == "illu":
            wf = illu_wf(prompt, 2000 + n, f"s60_{model}")
        else:
            w, h = (1920, 1088) if model in GRADE else (1536, 864)   # 실사는 원본을 크게 뽑는다
            wf = klein_wf(prompt + ", no text, no letters, no watermark", 2000 + n, w, h, f"s60_{model}")
            if model in GRADE:
                wf["9"]["inputs"]["steps"] = 8                        # 4스텝은 실사에서 뭉갠다(시험: 같은 시간에 더 선명)
        run(wf, dst)
        print(f"{model} {si:02d}_{k} {time.time() - t0:.1f}s", flush=True)


# ---- 조립 ----
def vf_for(fx, n, grade="eq=saturation=1.15:contrast=1.06,vignette=PI/5,noise=alls=6:allf=t"):
    base = f"scale={W*2}:{H*2}:flags=lanczos,"
    if fx == "push" or fx.startswith("card"):
        zp = f"zoompan=z='1+0.16*on/{n}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2'"
    elif fx == "pan":
        zp = f"zoompan=z='1.15':x='(iw-iw/zoom)*on/{n}':y='ih/2-ih/zoom/2'"
    elif fx == "punch":   # 0.3초 만에 확 당기고 천천히 더
        zp = f"zoompan=z='if(lt(on,9),1+0.25*on/9,1.25+0.05*(on-9)/{n})':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2'"
    else:                 # flash·shake — 커진 채로 흔든다(흔들림은 시간이 갈수록 잦아든다)
        a = 60 if fx == "shake" else 30
        zp = (f"zoompan=z='1.12':x='iw/2-iw/zoom/2+{a}*sin(on*2.1)*exp(-on/20)'"
              f":y='ih/2-ih/zoom/2+{a}*cos(on*2.7)*exp(-on/20)'")
    v = base + zp + f":d={n}:s={W}x{H}:fps={FPS}"
    if fx == "flash":
        v += ",fade=t=in:st=0:d=0.5:color=white"
    if fx.startswith("card"):   # 배경을 어둡게 흐리고 글자를 얹는다
        v += ",boxblur=12:2,eq=brightness=-0.25"
        for text, size, dy, col in CARDS[fx.split(":")[1]]:
            v += (f",drawtext=fontfile='{FONT}':text='{text}':fontsize={size}:fontcolor={col}:borderw=6:bordercolor=black"
                  f":x=(w-tw)/2:y=(h-th)/2+{dy}:alpha='min(1,t/0.3)'")
    return v + "," + grade + ",format=yuv420p"


def sfx(kind, path):
    """효과음을 ffmpeg 로 합성한다(갈색 소음 + 저역 통과 + 감쇠) — 외부 음원 없음"""
    spec = {"boom": ("brown", 2.5, "lowpass=f=160,volume=9", "afade=t=out:st=0.05:d=2.4"),
            "rumble": ("brown", 3.0, "lowpass=f=90,volume=7", "afade=t=in:d=0.3,afade=t=out:st=1.5:d=1.5"),
            "whoosh": ("pink", 1.4, "highpass=f=400,lowpass=f=3000,volume=2.5", "afade=t=in:d=0.9,afade=t=out:st=0.9:d=0.5")}[kind]
    sh(["ffmpeg", "-y", "-f", "lavfi", "-i", f"anoisesrc=color={spec[0]}:duration={spec[1]}:sample_rate=44100",
        "-af", f"{spec[2]},{spec[3]}", "-ac", "2", path])


def build(model, voice):
    work = os.path.join(S, f"build_{model}_{voice}"); os.makedirs(work, exist_ok=True)
    td = os.path.join(S, "tts", voice)
    lens = [dur(os.path.join(td, f"{i:02d}.mp3")) for i in range(len(SHOTS))]
    clips, subs, fx_at, acc = [], [], [], 0.0
    for si, (text, ps, snd) in enumerate(SHOTS):
        total = round((lens[si] + GAP) * FPS)          # 문장 길이를 프레임으로 — 컷들이 나눠 갖는다
        cuts = [total // len(ps) + (1 if k < total % len(ps) else 0) for k in range(len(ps))]
        for k, ((_, fx), n) in enumerate(zip(ps, cuts)):
            c = os.path.join(work, f"{si:02d}_{k}.mp4")
            sh(["ffmpeg", "-y", "-loop", "1", "-i", os.path.join(S, f"img_{model}", f"{si:02d}_{k}.png"), "-vf", vf_for(fx, n, *([GRADE[model]] if model in GRADE else [])),
                "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", c])
            clips.append(c)
        subs.append((acc, acc + lens[si], text))
        if snd:
            fx_at.append((snd, acc))
        acc += total / FPS
    with open(os.path.join(work, "clips.txt"), "w", encoding="utf-8") as f:
        f.writelines(f"file '{os.path.basename(c)}'\n" for c in clips)
    # 내레이션 — 문장마다 프레임 길이에 딱 맞춘 wav 를 잇는다(assemble.py 와 같은 방식)
    wavs = []
    for i, L in enumerate(lens):
        w = os.path.join(work, f"n{i:02d}.wav")
        sh(["ffmpeg", "-y", "-i", os.path.join(td, f"{i:02d}.mp3"), "-af", f"apad=whole_dur={round((L + GAP) * FPS) / FPS}", "-ar", "44100", "-ac", "2", w])
        wavs.append(w)
    with open(os.path.join(work, "narr.txt"), "w", encoding="utf-8") as f:
        f.writelines(f"file '{os.path.basename(w)}'\n" for w in wavs)
    narr = os.path.join(work, "narration.wav")
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(work, "narr.txt"), "-c", "copy", narr])
    # 자막 — 크게, 화면 아래
    ts = lambda t: f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"
    ass = os.path.join(work, "subs.ass")
    with open(ass, "w", encoding="utf-8") as f:
        f.write("[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\n\n[V4+ Styles]\n"
                "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginV\n"
                "Style: D,Malgun Gothic,60,&H00FFFFFF,&H00000000,&H90000000,1,1,5,2,2,70\n\n[Events]\nFormat: Layer, Start, End, Style, Text\n")
        f.writelines(f"Dialogue: 0,{ts(a)},{ts(b)},D,{t}\n" for a, b, t in subs)
    # 효과음 + 음악 + 내레이션 섞기
    ins, mix = ["-i", narr, "-i", sorted(os.path.join(MUSIC, x) for x in os.listdir(MUSIC) if x.endswith(".mp3"))[0]], ["[1:a]volume=1.0[n]", "[2:a]volume=0.12[m]"]
    labels = ["[n]", "[m]"]
    for j, (kind, at) in enumerate(fx_at):
        p = os.path.join(work, f"sfx_{kind}.wav"); sfx(kind, p)
        ins += ["-i", p]
        mix.append(f"[{3 + j}:a]adelay={int(at * 1000)}|{int(at * 1000)}[s{j}]"); labels.append(f"[s{j}]")
    subpath = ass.replace("\\", "/").replace(":", "\\:")
    fc = ";".join(mix) + f";{''.join(labels)}amix=inputs={len(labels)}:duration=first:normalize=0,alimiter=limit=0.89:level=false[a];[0:v]subtitles='{subpath}'[v]"
    final = os.path.join(S, f"s60_{model}_{voice}.mp4")
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(work, "clips.txt"), *ins, "-filter_complex", fc,
        "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "23" if model == "arch" else "18",   # 필름 입자는 압축을 못 먹어 용량이 터진다 — 입자가 가려 주므로 arch 만 낮춘다
        "-c:a", "aac", "-b:a", "192k", "-shortest", final])
    print(final, f"{dur(final):.1f}초 · 컷 {len(clips)}개 · 평균 {acc / len(clips):.2f}초")


if __name__ == "__main__":
    cmd = sys.argv[1]
    {"tts": lambda: tts(), "img": lambda: img(sys.argv[2]), "build": lambda: build(sys.argv[2], sys.argv[3])}[cmd]()

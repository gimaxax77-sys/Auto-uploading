# 20분 전편 — 승인받은 시네마틱 실사 화풍(60초 샘플)을 210장면 전체에 적용한다
# 사용: python build20.py tts | img | video
#   도입 1~14장면은 샘플에서 승인받은 그림·음성·카드·효과음을 그대로 재사용하고, 15~210장면만 새로 만든다
import glob, os, shutil, subprocess, sys, time
import sample60 as S6
from gen import build, run, workflow
from tts import scenes

sys.path.insert(0, r"D:\.CODE\AXdata\_TOOLS\content-archive")
from archive import archive

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
TTS = os.path.join(OUT, "tts20")            # 구글 Neural2 +10% (기존 out/tts 는 edge -5% 라 건드리지 않는다)
IMG = os.path.join(OUT, "img20_cine")
WORK = os.path.join(OUT, "build20")
MUSIC = os.path.join(HERE, "..", "music", "웅장")
TOPIC = "퉁구스카 대폭발"
FPS, W, H, GAP = S6.FPS, S6.W, S6.H, S6.GAP
STYLE, GRADE = S6.MODELS["cine"], S6.GRADE["cine"]
INTRO = len(S6.SHOTS)                        # 14 — 여기까지는 샘플 것을 쓴다
ROTATE = ["push", "pan", "punch", "pan", "push", "shake"]
FLASH = ("폭발", "번쩍", "빛이", "터졌", "불덩이")
SHAKE = ("흔들", "무너", "쓰러", "휘청", "부서")
BOOM = ("폭발했", "터졌", "폭발이")
RUMBLE = ("굉음", "울렸", "흔들렸", "지진")


def dur(p):
    return S6.dur(p)


def plan():
    """장면마다 (한국어, [(그림설명, 이펙트)…], 효과음) — 도입은 샘플 표, 나머지는 규칙으로 만든다"""
    rows, out = scenes(), list(S6.SHOTS)
    for i, (_, text, prompt) in enumerate(rows[INTRO:], INTRO + 1):
        d = dur(os.path.join(TTS, f"{i:03d}.mp3"))
        fx = ROTATE[i % len(ROTATE)]
        if any(w in text for w in FLASH):
            fx = "flash"
        elif any(w in text for w in SHAKE):
            fx = "shake"
        shots = [(prompt, fx)]
        if d >= 4.0:   # 긴 문장은 넓은 그림 + 클로즈업 두 컷으로 나눈다
            shots.append((prompt + ", extreme close-up detail shot", "pan" if fx != "pan" else "push"))
        snd = "boom" if any(w in text for w in BOOM) else ("rumble" if any(w in text for w in RUMBLE) else None)
        out.append((text, shots, snd))
    return out


# ---- 음성 ----
def tts():
    os.makedirs(TTS, exist_ok=True)
    sys.path.insert(0, os.path.dirname(HERE))
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(HERE), ".env"))
    from video import narrate_google
    src = os.path.join(OUT, "s60", "tts", "neural2")
    for i, (_, text, _) in enumerate(scenes(), 1):
        p = os.path.join(TTS, f"{i:03d}.mp3")
        if os.path.exists(p) and os.path.getsize(p) > 1000:
            continue
        if i <= INTRO:                                   # 샘플에서 이미 만든 것
            shutil.copyfile(os.path.join(src, f"{i-1:02d}.mp3"), p)
        else:
            narrate_google(text, p, "ko-KR-InJoonNeural", S6.RATE)
        print(f"{i:03d}", flush=True)
    ds = [dur(os.path.join(TTS, f"{i:03d}.mp3")) for i in range(1, len(scenes()) + 1)]
    print(f"장면 {len(ds)} · 합계 {sum(ds)/60:.1f}분 · 평균 {sum(ds)/len(ds):.2f}초")


# ---- 그림 ----
def img():
    os.makedirs(IMG, exist_ok=True)
    todo = [(si, k, p, text) for si, (text, ps, _) in enumerate(plan()) if si >= INTRO for k, (p, _) in enumerate(ps)]
    for n, (si, k, p, text) in enumerate(todo):
        dst = os.path.join(IMG, f"{si+1:03d}_{k}.png")
        if os.path.exists(dst):
            continue
        wf = workflow(build(p, STYLE, text), 5000 + si * 10 + k, 1920, 1088, "lf20")
        wf["9"]["inputs"]["steps"] = 8
        t0 = time.time()
        run(wf, dst)
        print(f"{si+1:03d}_{k} {time.time()-t0:.1f}s ({n+1}/{len(todo)})", flush=True)


def src_png(si, k):
    return (os.path.join(OUT, "s60", "img_cine", f"{si:02d}_{k}.png") if si < INTRO
            else os.path.join(IMG, f"{si+1:03d}_{k}.png"))


# ---- 조립 ----
def video():
    os.makedirs(WORK, exist_ok=True)
    rows = plan()
    lens = [dur(os.path.join(TTS, f"{i:03d}.mp3")) for i in range(1, len(rows) + 1)]
    clips, subs, fx_at, acc = [], [], [], 0.0
    for si, (text, ps, snd) in enumerate(rows):
        total = round((lens[si] + GAP) * FPS)
        cuts = [total // len(ps) + (1 if k < total % len(ps) else 0) for k in range(len(ps))]
        for k, ((_, fx), n) in enumerate(zip(ps, cuts)):
            c = os.path.join(WORK, f"{si+1:03d}_{k}.mp4")
            if not os.path.exists(c):
                S6.sh(["ffmpeg", "-y", "-loop", "1", "-i", src_png(si, k), "-vf", S6.vf_for(fx, n, GRADE),
                       "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", c + ".tmp.mp4"])
                os.replace(c + ".tmp.mp4", c)
            clips.append(c)
        subs.append((acc, acc + lens[si], text))
        if snd:
            fx_at.append((snd, acc))
        acc += total / FPS
    with open(os.path.join(WORK, "clips.txt"), "w", encoding="utf-8") as f:
        f.writelines(f"file '{os.path.basename(c)}'\n" for c in clips)
    # 내레이션 — 장면마다 클립 길이에 맞춘 wav 로 이어야 자막이 밀리지 않는다
    for i, L in enumerate(lens, 1):
        w = os.path.join(WORK, f"n{i:03d}.wav")
        if not os.path.exists(w):
            S6.sh(["ffmpeg", "-y", "-i", os.path.join(TTS, f"{i:03d}.mp3"), "-af", f"apad=whole_dur={round((L + GAP) * FPS) / FPS}",
                   "-ar", "44100", "-ac", "2", w])
    with open(os.path.join(WORK, "narr.txt"), "w", encoding="utf-8") as f:
        f.writelines(f"file 'n{i:03d}.wav'\n" for i in range(1, len(lens) + 1))
    narr = os.path.join(WORK, "narration.wav")
    S6.sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(WORK, "narr.txt"), "-c", "copy", narr])
    # 효과음 — 한 번에 섞어 «효과음 바닥» 한 줄로 만든다(최종 명령의 입력 수를 3개로 묶는다)
    bed = os.path.join(WORK, "sfxbed.wav")
    if fx_at:
        for kind in set(k for k, _ in fx_at):
            S6.sfx(kind, os.path.join(WORK, f"sfx_{kind}.wav"))
        ins, fc, lb = [], [], []
        for j, (kind, at) in enumerate(fx_at):
            ins += ["-i", os.path.join(WORK, f"sfx_{kind}.wav")]
            fc.append(f"[{j}:a]adelay={int(at*1000)}|{int(at*1000)}[s{j}]"); lb.append(f"[s{j}]")
        S6.sh(["ffmpeg", "-y", *ins, "-filter_complex", ";".join(fc) + f";{''.join(lb)}amix=inputs={len(lb)}:normalize=0,apad=whole_dur={acc}",
               "-ar", "44100", "-ac", "2", "-t", str(acc), bed])
    # 자막
    ts = lambda t: f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"
    ass = os.path.join(WORK, "subs.ass")
    with open(ass, "w", encoding="utf-8") as f:
        f.write("[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\n\n[V4+ Styles]\n"
                "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginV\n"
                "Style: D,Malgun Gothic,60,&H00FFFFFF,&H00000000,&H90000000,1,1,5,2,2,70\n\n[Events]\nFormat: Layer, Start, End, Style, Text\n")
        f.writelines(f"Dialogue: 0,{ts(a)},{ts(b)},D,{t}\n" for a, b, t in subs)
    # 음악 — 폴더 곡을 길이만큼 이어 붙인다
    with open(os.path.join(WORK, "music.txt"), "w", encoding="utf-8") as f:
        f.writelines(f"file '{os.path.abspath(p)}'\n" for p in sorted(glob.glob(os.path.join(MUSIC, "*.mp3"))) * 6)
    ins = ["-i", narr, "-f", "concat", "-safe", "0", "-i", os.path.join(WORK, "music.txt")]
    mix = ["[1:a]volume=1.0[n]", "[2:a]volume=0.10,aresample=44100[m]"]
    lb = ["[n]", "[m]"]
    if fx_at:
        ins += ["-i", bed]; mix.append("[3:a]volume=1.0[s]"); lb.append("[s]")
    subpath = ass.replace("\\", "/").replace(":", "\\:")
    fc = ";".join(mix) + f";{''.join(lb)}amix=inputs={len(lb)}:duration=first:normalize=0,alimiter=limit=0.89:level=false[a];[0:v]subtitles='{subpath}'[v]"
    final = os.path.join(OUT, "tunguska_cine.mp4")
    S6.sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(WORK, "clips.txt"), *ins,
           "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "192k", "-shortest", final])
    archive(final, TOPIC, "롱")
    print(f"{final} · {dur(final)/60:.1f}분 · {os.path.getsize(final)/2**20:.0f}MB · 컷 {len(clips)}개 · 평균 {acc/len(clips):.2f}초 · 효과음 {len(fx_at)}개")


if __name__ == "__main__":
    {"tts": tts, "img": img, "video": video}[sys.argv[1]]()

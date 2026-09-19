# 1단계 시험 — 장면 그림(켄번스) + 내레이션 + 음악 + 자막을 한 편으로 조립한다. 사용: python assemble.py <화풍키> [장면수]
import glob, os, subprocess, sys, time
from tts import scenes

sys.path.insert(0, r"D:\.CODE\AXdata\_TOOLS\content-archive")
from archive import archive  # 완성본을 H:\AX_Contents 에 복사 보관

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
MUSIC = os.path.join(HERE, "..", "music", "웅장")
TOPIC = "퉁구스카 대폭발"
FPS, W, H, GAP = 30, 1920, 1080, 0.45   # GAP = 장면 사이 숨(초)
MOVES = [   # 켄번스 네 가지를 돌려 쓴다. zoompan 떨림을 줄이려 4배로 키운 뒤 움직인다
    "z='1+0.10*on/{n}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2'",
    "z='1.10-0.10*on/{n}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2'",
    "z='1.08':x='(iw-iw/zoom)*on/{n}':y='ih/2-ih/zoom/2'",
    "z='1.08':x='(iw-iw/zoom)*(1-on/{n})':y='ih/2-ih/zoom/2'",
]


def sh(args):
    r = subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if r.returncode:
        raise RuntimeError(r.stderr.decode("utf-8", "replace")[-1500:])


def ts(t):
    h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def main(style, limit=None):
    rows = scenes()[: int(limit) if limit else None]
    durs = [float(l.split()[1]) for l in open(os.path.join(OUT, "durations.tsv"))][: len(rows)]
    work = os.path.join(OUT, f"clips_{style}"); os.makedirs(work, exist_ok=True)
    t0 = time.time()
    # 1) 장면 클립(무음) — 이미 있으면 건너뜀
    for i, d in enumerate(durs, 1):
        clip = os.path.join(work, f"{i:03d}.mp4")
        if os.path.exists(clip):
            continue
        n = round((d + GAP) * FPS)
        vf = f"scale={W*2}:{H*2}:flags=lanczos,zoompan={MOVES[i % 4].format(n=n)}:d={n}:s={W}x{H}:fps={FPS},format=yuv420p"
        sh(["ffmpeg", "-y", "-loop", "1", "-i", os.path.join(OUT, f"img_{style}", f"{i:03d}.png"), "-vf", vf,
            "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", clip + ".tmp.mp4"])
        os.replace(clip + ".tmp.mp4", clip)   # 중간에 죽어도 빈 클립이 «이미 있음»으로 남지 않게
    t_clips = time.time() - t0
    # 2) 내레이션 한 줄(장면마다 GAP 만큼 뒤에 무음)
    with open(os.path.join(work, "clips.txt"), "w", encoding="utf-8") as f:
        f.writelines(f"file '{i:03d}.mp4'\n" for i in range(1, len(durs) + 1))
    # 장면마다 음성을 클립 길이(프레임 수 / FPS)에 딱 맞춘 wav 로 늘여 PCM 으로 잇는다 — mp3 를 그냥 이으면 장면마다 앞뒤 여백이 쌓여 자막이 밀린다
    # (입력 210개를 한 명령줄에 늘어놓으면 윈도 명령줄 한도 32k자에 닿으므로 concat 목록으로)
    narr = os.path.join(OUT, "narration.wav")
    for i, d in enumerate(durs, 1):
        wav = os.path.join(work, f"{i:03d}.wav")
        if not os.path.exists(wav):
            sh(["ffmpeg", "-y", "-i", os.path.join(OUT, "tts", f"{i:03d}.mp3"), "-af", f"apad=whole_dur={round((d + GAP) * FPS) / FPS}",
                "-ar", "44100", "-ac", "2", wav])
    with open(os.path.join(work, "narr.txt"), "w", encoding="utf-8") as f:
        f.writelines(f"file '{i:03d}.wav'\n" for i in range(1, len(durs) + 1))
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(work, "narr.txt"), "-c", "copy", narr])
    # 3) 자막(ASS) — 장면 시작~끝, 화면 아래
    srt = os.path.join(work, "subs.ass"); acc = 0.0
    lines = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "", "[V4+ Styles]",
             "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginV",
             "Style: D,Malgun Gothic,54,&H00FFFFFF,&H00000000,&H80000000,1,1,4,1,2,60", "", "[Events]",
             "Format: Layer, Start, End, Style, Text"]
    for (_, text, _), d in zip(rows, durs):
        lines.append(f"Dialogue: 0,{ts(acc)},{ts(acc + d)},D,{text}"); acc += round((d + GAP) * FPS) / FPS
    open(srt, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    # 4) 음악 — 웅장 폴더 곡을 이어 붙여 길이를 채우고 작게 깐다
    tracks = sorted(glob.glob(os.path.join(MUSIC, "*.mp3")))
    with open(os.path.join(work, "music.txt"), "w", encoding="utf-8") as f:
        f.writelines(f"file '{os.path.abspath(p)}'\n" for p in tracks * 3)
    final = os.path.join(OUT, f"tunguska_{style}.mp4")
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(work, "clips.txt"), "-i", narr,
        "-f", "concat", "-safe", "0", "-i", os.path.join(work, "music.txt"),
        "-filter_complex", "[2:a]volume=0.07,aresample=44100[m];[1:a][m]amix=inputs=2:duration=first:normalize=0[a];"
        f"[0:v]subtitles='{srt.replace(chr(92), '/').replace(':', chr(92) + ':')}'[v]",
        "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "160k", "-shortest", final])
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", final]).strip())
    archive(final, TOPIC, "롱")
    print(f"{final} · {dur/60:.1f}분 · {os.path.getsize(final)/2**20:.0f}MB · 클립 {t_clips/60:.1f}분 · 전체 {(time.time()-t0)/60:.1f}분")


if __name__ == "__main__":
    main(*sys.argv[1:])

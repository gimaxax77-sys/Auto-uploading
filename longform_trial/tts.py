# 1단계 시험 — 장면별 내레이션을 edge-tts 로 만들고 길이를 잰다(out/tts/NNN.mp3, out/durations.tsv)
import asyncio, os, subprocess, sys
import edge_tts

VOICE, RATE = os.environ.get("LF_VOICE", "ko-KR-InJoonNeural"), os.environ.get("LF_RATE", "-5%")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "tts")


def scenes():
    rows = []
    for f in ("scenes_1.txt", "scenes_2.txt"):
        for line in open(os.path.join(HERE, f), encoding="utf-8"):
            if line.strip() and not line.startswith("#"):
                ch, text, prompt = line.rstrip("\n").split("|")
                rows.append((int(ch), text, prompt))
    return rows


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]).strip())


async def one(i, text, sem):
    p = os.path.join(OUT, f"{i:03d}.mp3")
    async with sem:
        for k in range(3):   # edge-tts 는 가끔 빈 응답 — 3번까지 다시
            try:
                if not (os.path.exists(p) and os.path.getsize(p) > 1000):
                    await edge_tts.Communicate(text, VOICE, rate=RATE).save(p)
                return dur(p)
            except Exception as e:
                print(i, "재시도", k, e, file=sys.stderr)
        raise RuntimeError(f"장면 {i} 음성 실패")


async def main():
    os.makedirs(OUT, exist_ok=True)
    rows = scenes()
    sem = asyncio.Semaphore(4)
    ds = await asyncio.gather(*(one(i, t, sem) for i, (_, t, _) in enumerate(rows, 1)))
    with open(os.path.join(HERE, "out", "durations.tsv"), "w", encoding="utf-8") as f:
        for i, d in enumerate(ds, 1):
            f.write(f"{i}\t{d:.3f}\n")
    print(f"장면 {len(ds)} · 합계 {sum(ds)/60:.1f}분 · 평균 {sum(ds)/len(ds):.2f}초 · 최소 {min(ds):.2f} · 최대 {max(ds):.2f}")


if __name__ == "__main__":
    asyncio.run(main())

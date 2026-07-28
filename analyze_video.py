# 유튜브 영상을 분석해 메타데이터·채널 성적·썸네일·자막을 한 번에 정리하는 도구
import os
import re
import sys
import urllib.request

OUT_DIR = "analysis"


def video_id(s: str) -> str:
    """유튜브 주소나 ID에서 영상 ID만 뽑습니다. youtu.be / watch?v= / shorts/ 모두 지원."""
    m = re.search(r"(?:youtu\.be/|watch\?v=|/shorts/|/embed/)([\w-]{11})", s)
    return m.group(1) if m else s.strip()


def 초표기(sec: float) -> str:
    return f"{int(sec) // 60}:{int(sec) % 60:02d}"


def 문장으로(조각들) -> list[tuple[float, str]]:
    """토막난 자막을 문장 단위로 합칩니다. 문장부호가 없으면 통째로 둡니다."""
    문장, 시작, 버퍼 = [], None, ""
    for s in 조각들:
        if 시작 is None:
            시작 = s.start
        버퍼 = (버퍼 + " " + s.text.strip()).strip()
        while True:
            m = re.search(r"[.?!]", 버퍼)
            if not m:
                break
            문장.append((시작, 버퍼[:m.end()].strip()))
            버퍼 = 버퍼[m.end():].strip()
            시작 = s.start
    if 버퍼:
        문장.append((시작 or 0.0, 버퍼))
    return 문장


def main() -> None:
    if len(sys.argv) < 2:
        print("사용법: python analyze_video.py <유튜브 주소 또는 ID>")
        sys.exit(1)
    vid = video_id(sys.argv[1])
    os.makedirs(OUT_DIR, exist_ok=True)

    from youtube import get_service
    svc = get_service()

    items = svc.videos().list(part="snippet,contentDetails,statistics", id=vid).execute()["items"]
    if not items:
        print(f"영상을 찾을 수 없습니다: {vid} (비공개·삭제·지역제한일 수 있습니다)")
        sys.exit(1)
    v = items[0]
    s, st, cd = v["snippet"], v["statistics"], v["contentDetails"]
    조회 = int(st.get("viewCount", 0))
    좋아요 = int(st.get("likeCount", 0))

    print("=" * 62)
    print(f"제목   : {s['title']}")
    print(f"채널   : {s['channelTitle']}")
    print(f"게시   : {s['publishedAt'][:10]}   길이: {cd['duration']}   카테고리: {s.get('categoryId')}")
    print(f"조회   : {조회:,}   좋아요: {좋아요:,} ({좋아요 / 조회 * 100:.1f}%)"
          if 조회 else f"조회   : {조회}")
    print(f"댓글   : {int(st.get('commentCount', 0)):,}   태그: {s.get('tags') or '없음'}")

    # 채널 최근 성적 — 이 영상이 특별한지 평소 수준인지 가늠합니다.
    ch = svc.channels().list(part="statistics,contentDetails", id=s["channelId"]).execute()["items"][0]
    cst = ch["statistics"]
    편수 = max(1, int(cst["videoCount"]))
    print(f"\n[채널] 구독 {int(cst['subscriberCount']):,} · 영상 {편수}편 · "
          f"총조회 {int(cst['viewCount']):,} · 편당 평균 {int(cst['viewCount']) // 편수:,}")
    up = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    ids = [i["contentDetails"]["videoId"] for i in
           svc.playlistItems().list(part="contentDetails", playlistId=up, maxResults=12).execute()["items"]]
    최근 = svc.videos().list(part="snippet,statistics,contentDetails", id=",".join(ids)).execute()["items"]
    print(f"  {'조회':>9} {'좋아요':>7} {'길이':>8}  제목")
    for x in 최근:
        xs = x["statistics"]
        print(f"  {int(xs.get('viewCount', 0)):>9,} {int(xs.get('likeCount', 0)):>7,} "
              f"{x['contentDetails']['duration'][2:]:>8}  {x['snippet']['title'][:36]}")

    # 썸네일 저장 — 문구와 디자인은 제목과 따로 노는 경우가 많아 꼭 봐야 합니다.
    thumb = max(s["thumbnails"].values(), key=lambda t: t.get("width", 0))
    tp = os.path.join(OUT_DIR, f"{vid}_thumb.jpg")
    urllib.request.urlretrieve(thumb["url"], tp)
    print(f"\n[썸네일] {thumb['width']}x{thumb['height']} -> {tp}")

    # 자막
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        api = YouTubeTranscriptApi()
        트랙 = list(api.list(vid))
        print(f"\n[자막] 트랙 {len(트랙)}개: " +
              ", ".join(f"{t.language_code}{'(자동)' if t.is_generated else ''}" for t in 트랙))
        코드 = next((t.language_code for t in 트랙 if t.language_code.startswith("ko")),
                   트랙[0].language_code)
        tr = api.fetch(vid, languages=[코드])
        조각 = tr.snippets if hasattr(tr, "snippets") else list(tr)
    except Exception as e:
        print(f"\n[자막] 가져오지 못했습니다: {e}")
        return

    문장 = 문장으로(조각)
    전체 = " ".join(t for _, t in 문장)
    총초 = max(x.start + x.duration for x in 조각)
    print(f"  문장 {len(문장)}개 · {len(전체):,}자 · 분당 {len(전체) / (총초 / 60):.0f}자")

    print("\n[도입 15초] — 훅이 여기서 결정됩니다")
    for t, x in 문장:
        if t > 15:
            break
        print(f"  {초표기(t):>5}  {x}")

    # 설명글의 타임라인을 챕터로 읽어, 구간별로 몇 초를 썼는지 봅니다.
    챕터 = re.findall(r"(\d{1,2}:\d{2})\s*[-–]\s*(.+)", s["description"])
    if 챕터:
        print("\n[챕터 배분]")
        초 = [int(a.split(":")[0]) * 60 + int(a.split(":")[1]) for a, _ in 챕터]
        for i, (t, 이름) in enumerate(챕터):
            끝 = int(초[i + 1] if i + 1 < len(초) else 총초)
            print(f"  {t:>6} ~ {초표기(끝):>5}  ({끝 - 초[i]:>3}초)  {이름.strip()[:40]}")

    경로 = os.path.join(OUT_DIR, f"{vid}_transcript.txt")
    with open(경로, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# {s['title']}\n# {s['channelTitle']} · {s['publishedAt'][:10]} · 조회 {조회:,}\n\n")
        for t, x in 문장:
            f.write(f"[{초표기(t)}] {x}\n")
    print(f"\n[저장] 자막 전문 -> {경로}")


if __name__ == "__main__":
    main()

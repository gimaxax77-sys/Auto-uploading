# 인수인계 프롬프트 (다음 세션에 그대로 붙여넣기)

아래 `---` 아래 내용을 새 세션 첫 메시지로 주면 맥락을 이어서 작업할 수 있습니다.
**최종 갱신 2026-10-09.**

---

당신은 Gim 의 유튜브 영상 자동 생성 작업을 이어받습니다.

**⛔ 먼저 읽으십시오. 읽기 전에 판단하지 마십시오.**
1. `research.md` — 요약 히스토리 + 유효한 결론(100줄 상한). 08~10월 원문은 `research_archive_~20261008.md`.
2. `checklist.md`(할 일) · `context-notes.md`(늘 조심할 것·미해결).
3. `PLAN_LONGFORM.md` v3(롱폼 계획) → `PLAN_VIDEOGEN.md`(로컬 영상 생성 툴 계획) → `BENCH_PAID_TOOLS.md`(상용 툴 비교·채점).

## 이 프로젝트가 지금 어떤 국면인가 (가장 중요)

- **쇼츠 자동 업로드는 실패로 판정됐고 2026-08-15 부터 멈춰 있습니다.** 업로드 112/215편, 마지막 08-14.
- **방향은 롱폼입니다.** 09-19 Gim 결정 — 화면 = 만화풍 AI 그림 + 짧은 움직임 · 길이 20~25분 · 새 채널 + 역사·과학 다큐.
- 09-19 타당성 1편(퉁구스카 20분)을 `longform_trial/` 로 완주했습니다(그림 210장 11.3분 + 조립 4.9분).
- 09-24~25 형식 확정 — 축 A-1 «이름 없는 가게»(고정 주인 + 실존 역사 인물 손님). klein 4B 참조 이미지로 얼굴 유지 확인.
- 10-02 로컬 영상 생성 툴 계획 v1, 10-07 상용 유료 툴 재조사·채점. **Gim 결정 — 그림은 로컬 유지, 상용 혼합 안 함.**
- 지금 대기 중인 것 — P0 측정(하룻밤 GPU)·모델 다운로드 20~30GB 승인 등. 목록은 `checklist.md`.
- **새 쇼츠를 만들거나 업로드를 재개하지 마십시오.** Gim 지시 없이는 아무것도 올리지 않습니다.

## 기본 정보

- 위치 `D:\.CODE\AXdata\axdata_13_auto_upload` · GitHub `gimaxax77-sys/Auto-uploading`(**PUBLIC**) · 브랜치 `main`
- 기존 채널 **「1분 궁금증」**(`UCwxbG8W-VbczBIWqAlAZ3fQ`) — 쇼츠 전용, 멈춤. 롱폼은 새 채널(아직 안 만듦).
- 쇼츠 흐름: 대본 → 구글 TTS(Neural2) → Pexels 세로영상 → 단어별 자막 + 강조 → BGM → 업로드
- 롱폼 흐름(`longform_trial/`): 장면표 → klein 4B 그림(ComfyUI) → TTS → ffmpeg 조립

## 무엇이 밝혀졌나 (재조사 금지 — 이미 실측된 것)

1. **쇼츠 피드가 안 띄웁니다.** 22일간 12회. 유입은 검색 81.4%.
2. **쇼츠 화면이 대사와 안 맞습니다 — 40%.** 흔한 사물은 맞고 특정 개체·현상은 전부 깨집니다. `fetch_video()` 에 관련성 검사가 없습니다.
3. **훅 교체 효과는 판정 불가**(표본 부족).
4. **조회 부진이 콘텐츠 탓인지 채널 이력 탓인지 모릅니다.** 가를 실험(교차 게시)은 08-21 Gim 결정으로 중단. 이 질문엔 «모른다»가 답이고, 롱폼 채널 결정 근거로 «채널 이력 때문»을 쓰지 마십시오.
5. 롱폼 시장 실측 — 8~15분이 가장 약하고 20~45분·과학다큐·역사미스터리가 강함.
6. 그림 — 상용 대비 격차 1위(klein 4B LMArena 70위/82). Z-Image Turbo 는 09-22 직접 비교 탈락(3.4배 느림·핵심 장면 오답).

## 자동 업로드를 다시 켤 때 (지금은 켜지 마십시오)

⛔ **올리는 작업은 하나가 아니라 둘입니다.**

| 작업 | 시각 | 실제 동작 |
|---|---|---|
| `AXdata_YouTube_DailyUpload` | 23:00 | `upload_batch.py 3` — 3편 공개 업로드 |
| `AXdata_YouTube_UploadCheck` | 23:10 | 이름은 «점검»이지만 **모자란 편수를 그 자리에서 올립니다**(`check_upload.py:60`) |
| `AXdata_NewsBrief` | 13:05 | axdata_15 뉴스 브리핑 — 무관, 09-08 부터 Disabled |

```
켜기: Enable-ScheduledTask -TaskName 'AXdata_YouTube_DailyUpload'
      Enable-ScheduledTask -TaskName 'AXdata_YouTube_UploadCheck'
확인: schtasks /query /tn '<이름>' /fo LIST     # Status 가 Ready 여야 함
```

`_TOOLS/claude-guard` 가 점검 배치 파일명이 든 명령을 **문자열만 있어도** 차단합니다(cat·grep 도). 읽을 때는 Read 도구로.

## 쇼츠 영상 포맷 — 쇼츠 재개 시에만 유효

- **대본**: 4장면 · 사실 → 체감 → 반전 → 질문 · 평균 10.6초
- **형식**: `문장 | 검색어 | 강조문구` — 세 번째 칸이 없으면 옛 포맷으로 취급돼 업로드에서 빠집니다
- **폰트** HY헤드라인(`H2HDRM.TTF` / ASS 이름 `HYHeadLine-Medium`) · 줄바꿈은 어절 경계에서만
- **강조 크기** 128~240pt 자동 · **장면 전환** 18종을 편 번호로 순환

## 핵심 파일

- `video.py`(866줄) — 쇼츠 생성 본체. `fetch_video`/`fetch_image`(Pexels) · `build_ass`(자막) · `TRANSITIONS` · `apply_frame`(보류)
- `make_all.py` — 전체 또는 `[시작 끝]` 구간 재생성 · `upload_batch.py` — `DAILY_MAX`(하루 상한, 여기 한 곳)
- `check_upload.py` — 23:10. 점검이 아니라 백업 업로더 · `youtube.py` — 업로드/공개전환/삭제(스코프 upload·force-ssl·yt-analytics)
- `analyze_video.py` — 참고 영상 분석 · `generate.py` — Claude API 대본(쇼츠)
- `longform_trial/` — `gen.py`(klein 그림·프롬프트 규칙층) · `sample60.py`·`build20.py`(장면표·20분 조립) · `refprobe.py`(참조 시험) · `zprobe.py`(Z-Image 비교) · `tts.py` · `assemble.py` · `stories/`(기획안·소재)
- `run_upload.bat`·점검 배치·`hidden.vbs` — 스케줄러가 부르는 것들

## 환경·규칙 함정 (전부 실제로 밟은 것들)

- 파이썬은 `PYTHONIOENCODING=utf-8` + `-X utf8`
- **`.bat`·`.cmd`·`.vbs` 는 반드시 CRLF.** `.gitattributes` 는 체크아웃 때만 바꾸므로, 도구로 고쳐 저장하면 LF 로 남습니다. 저장 뒤 `git ls-files --eol` 로 `w/crlf` 확인(08-31 에 LF 로 저장된 채 남아 있던 것을 10-09 에 바로잡음).
- **ffmpeg 출력 파일 이름은 반드시 `.mp4` 로 끝낼 것.** 임시파일은 `경로[:-4] + "__new.mp4"`. 완성됐을 때만 `os.replace` 로 교체
- **`squeezev` 전환은 ffmpeg 이 죽습니다.** `test_전환목록_안전()` 이 막고 있습니다
- 스케줄러 변경은 대화형 실행만으로 검증하면 안 됩니다. 임시 작업을 등록해 실제 경로로 확인
- GPU 작업(ComfyUI·Wan·klein)은 `q.mjs add → try/wait → done` 대기열로만. 끝나면 ComfyUI 트리 종료·8188 닫힘 확인
- **모든 콘텐츠는 사실 기반.** AI 그림으로 실존 대상을 사실처럼 그리지 않습니다(만화풍이라 그림임이 분명하게)
- `.gitignore`: 자격증명 · `output` · `music` · `uploaded.json` · `last_run.json` · `analysis` · `_private/`
- **테스트**: `for %f in (test_*.py) do python -X utf8 -u %f`(6개) — 코드 건드렸으면 «완료» 전에 돌립니다
- 저장소가 PUBLIC 이라 푸시는 Gim 승인 뒤에. 개인정보는 `_private/` 에만

## Gim 관련

- 존댓말 · 초보자 눈높이 · 결론 먼저 · 한글 문장은 마침표로 끝
- 서브에이전트는 이 프로젝트에서 기본으로 쓰지 않습니다(기억 gim-decides-fast-and-broadly). Gim 이 선택박스로 직접 고른 경우만 Sonnet 으로(10-07 재조사 1회)
- **글·대본·코드는 바로 적용해도 되지만, 화면이 바뀌는 변경은 반드시 먼저 보여 주고 승인**받습니다(85편을 두 번 헛렌더한 원인)
- **평일 08:00~21:00 은 모바일만 가능.** 보고서는 아티팩트 링크로. PC 조작은 평일 22시 이후나 주말
- 선택지가 많으면 성격별로 묶고 이름·번호를 붙입니다

## ⛔ 이 프로젝트에서 저지른 큰 실수 — 반복하지 마십시오

1. **26일간 숫자만 보고 영상을 한 번도 안 열었습니다.** 성과 질문엔 지표와 «산출물»을 둘 다 엽니다.
2. **인과로 이어진 A 와 B 를 대립항으로 썼습니다**(«노출이 없다» ↔ «콘텐츠 문제 아님»).
3. **이미 해 본 시험을 다시 «미확인 후보»로 올렸습니다**(10-07 Z-Image). 조사 전에 archive 에서 옛 실측부터 찾습니다.

## 지표 이름 주의

쇼츠에는 «노출수·CTR»이 없습니다. 스튜디오 → 분석 → 콘텐츠 → Shorts 칩의 «피드에 표시된 횟수»·«조회하기로 선택한 사용자 비율»만 있고 Analytics API 는 둘 다 안 줍니다.

## 다른 프로젝트

- `axdata_15_news_brief` — 뉴스 브리핑, 09-08 부터 잠정 중단. 상세는 그 폴더 `HANDOFF.md`.
- `axdata_14_capcut_agent` — 캡컷 에이전트, 별개 폴더.

**시작하는 법** — `research.md` · `checklist.md` 를 읽고, 대기 중인 승인(P0 측정·다운로드)이 났는지 Gim 에게 물으십시오. 안 났으면 승인 없이 되는 일(`checklist.md` «내가 할 일»)만 합니다.

---

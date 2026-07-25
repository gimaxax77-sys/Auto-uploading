# 인수인계 프롬프트 (다음 세션에 그대로 붙여넣기)

아래 `---` 아래 내용을 새 세션 첫 메시지로 주면, 맥락을 이어서 작업할 수 있습니다.

---

당신은 Gim의 YouTube 쇼츠 자동 생성·업로드 툴 작업을 이어받습니다. 먼저 저장소의 `research.md`, `PLAN.md`를 읽으세요.

## 프로젝트
- 위치: `D:\.CODE\AXdata\axdata_13` (작업은 이 폴더에서)
- GitHub: `gimaxax77-sys/Auto-uploading`, 브랜치 `atup`
- 흐름: 대본(txt) → 한국어 내레이션 → 배경(영상 우선/사진 폴백) → 단어별 자막 → 세로 쇼츠 → YouTube 자동 업로드

## 지금까지 완성
- **영상 185편**(`output/*.mp4`). 대본 `scripts/NNN_제목.txt`(한 줄=한 장면, `|` 뒤 영어 검색어).
  - 01~140 기본 · 141~155 심리/몸/돈심리 · 156~165 자연동물경이 · 166~175 극한장소 · 176~185 바다.
- **개선 반영**: 훅(첫 문장 궁금증형) · 음성 편별 통일(홀수=여자/짝수=남자) · 단어별 자막(ASS karaoke, 90pt) · BGM 무드폴더(`music/차분·웅장·밝은`, 볼륨 0.35) · B-roll(Pexels 세로영상, 없으면 사진).
- **TTS**: `video.py`의 `TTS_ENGINE` = 현재 `"google"`(Neural2, 더 부드러움). 신규 영상만 Neural2, 기존은 edge. `GOOGLE_TTS_API_KEY`는 `.env`.
- **YouTube**: OAuth "프로덕션"(만료 없음) + force-ssl 스코프 → 클로드가 공개↔비공개 전환·삭제 가능. 매일 밤 11시 **12편 자동 업로드**(`AXdata_YouTube_DailyUpload` → `run_upload.bat` → `upload_batch.py 12`). 업로드 순서는 **랜덤+장르 연속 방지**.

## 이어서 할 일 / 대기
1. **비공개 자연 10편(156~165)** — 검토용 비공개 업로드됨. Gim이 "공개 진행" 하면 `youtube.set_privacy`로 공개 전환. ID는 scratchpad `nature_private.json`(없으면 채널에서 조회).
2. **매일 업로드 자동 진행 중** — 미업로드분이 12편/일씩 공개됨. 개입 불필요.
3. **새 니치 콘텐츠** — Gim 요청 시 대본 생성(사실기반, 다큐 시리즈는 웅장 무드). 번호는 186부터 이어서.
4. **캡컷 에이전트**(별개 스펙, 토킹영상 자동편집) — 빌드/검토/접목 여부 Gim 결정 대기.

## 핵심 파일
- `video.py` — 생성 본체. 상단 상수(TTS_ENGINE/BROLL/FONT/MUSIC_VOLUME/MOOD_*/VOICES 등)로 조절. `narrate`(edge/google 분기), `narrate_google`(v1beta1 SSML 타임포인트), `fetch_video`(B-roll), `build_ass`(단어자막), `mood_of`/`voice_of`.
- `make_all.py` — 전체 또는 `[시작 끝]` 구간 재생성(구간 지정 시 덮어씀).
- `upload_batch.py` — 하루 N편 공개 업로드. `spread`/`genre_of`로 장르 안 겹치게 랜덤.
- `youtube.py` — 업로드/공개전환/삭제(force-ssl). `run_upload.bat` — 스케줄러가 부르는 배치.

## 환경·규칙 주의
- Windows PowerShell. Python 명령엔 `PYTHONIOENCODING=utf-8` + `-X utf8`(한글 깨짐 방지). 작업은 `axdata_13` 폴더에서.
- 대본/자막 파일은 `newline="\n"`로 저장.
- 이미지·영상 검색어는 Pexels에 흔한 안전한 단어로. 특정 대상 없으면 오해 없는 중립 이미지.
- **모든 콘텐츠 사실 기반**(추측·허구·오귀속 금지). 다큐 사실은 검증 후.
- 영상 렌더는 **로컬 4개 병렬이 상한**(CPU). `make_all.py A B`를 구간 나눠 병렬 실행.
- 커밋 후 `git push origin atup`. 자격증명·output·music·uploaded.json은 `.gitignore`.

## Gim 관련(전역 규칙도 참조: `D:\.CODE\.Claude\CLAUDE.md`)
- 존댓말, 초보자 눈높이, 결론 먼저, 한글 문장은 마침표로 끝.
- **결과물(영상 등)은 Gim이 요청할 때만 링크로**(미공개 업로드 → youtu.be). 모바일은 채팅 첨부 못 봄.
- **서브에이전트는 승인 게이트**: 쓰기 전 2줄 노티(규모+작업성격 / 사용량 흐름) 후 승인. 토큰 아낄 땐 클로드 직접(롣).
- 직접 PC 조작은 평일 밤 10시 이후/주말만. 낮엔 모바일.

먼저 `research.md`·`PLAN.md`를 읽고, 위 대기 1~4를 확인한 뒤 Gim에게 상태를 브리핑하세요.

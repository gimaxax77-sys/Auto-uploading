# 기획안 ① — 「634일」 섀클턴 인듀어런스 원정

> 상태: **기획안만.** 대본·그림 없음. 2026-09-23 작성.
> 형식: 20~25분 롱폼 · 만화풍 AI 그림 + 프로그램 모션 (PLAN_LONGFORM.md v3 §머리말 결정 ①②③)

---

## 0. 한 줄

배가 얼음에 으스러져 가라앉았고, 무전기도 구조 요청도 없었고, 634일이 지났는데 **28명이 한 명도 죽지 않고 돌아왔다.**

**훅(첫 15초)** — 「1915년 11월 21일, 남극 웨들해. 스물여덟 명이 자기들이 타고 온 배가 가라앉는 것을 지켜보고 있었습니다. 가장 가까운 사람이 있는 곳까지 1,600킬로미터. 그들이 어디에 있는지 아는 사람은 지구에 한 명도 없었습니다.」

## 1. 제목·썸네일 후보

| # | 제목 | 썸네일 문구 |
|---|---|---|
| 1 | 배가 가라앉았는데 28명 전원이 살아 돌아왔다 — 남극 634일 | **634일** / 생존자 28/28 |
| 2 | 구조 요청을 보낼 방법이 없었다 — 남극에 갇힌 634일 | 무전기 없음 |
| 3 | 인류 최악의 조난, 그런데 사망자 0명 | 사망 **0** |

⚠ 1번 권장. 「전원 생존」이 훅이자 결말 스포일러인데, **이 이야기는 결말을 먼저 말해야 20분을 버팁니다**(어떻게 살았나가 본문이라).

## 2. 사실 출처와 ⚠ 검증이 필요한 수치

- 주 출처: en.wikipedia.org/wiki/Imperial_Trans-Antarctic_Expedition · /wiki/Endurance_(1912_ship)
- 보조: 워슬리 『Shackleton's Boat Journey』 · 난파선 발견은 Falklands Maritime Heritage Trust 2022 발표.

**⛔ 대본에 쓰기 전에 반드시 확인할 것 넷.**

1. **「위험한 여행에 함께할 사람 구함…」 구인광고는 출처가 확인되지 않았습니다.** 가장 유명한 대목인데 **당시 신문에서 실물이 발견된 적이 없습니다.** → 쓰려면 반드시 「전해지는 이야기로는」이라고 못박거나 **아예 뺍니다.** 사실 기반 채널에서 이걸 사실처럼 읽으면 그 한 줄이 채널 신뢰를 깎습니다.
2. **제임스 케어드 항해 거리.** 문헌이 「800해리(약 1,480km)」와 「약 1,300km」로 갈립니다. 하나를 고르고 **영상 내내 같은 숫자**를 씁니다.
3. **썰매개 마릿수.** 69마리와 70마리가 섞여 나옵니다.
4. **보트 길이.** 22피트 6인치 = **6.9미터**. 「7미터가 안 되는 배」로 표현하면 안전합니다.

**확정 날짜(이건 갈리지 않습니다).**

| 날짜 | 일 |
|---|---|
| 1914-08-08 | 플리머스 출항 (1차대전 발발 직후) |
| 1914-12-05 | 사우스조지아 그리트비켄 출항 — **여기가 634일의 시작** |
| 1915-01-19 | 웨들해 부빙에 갇힘 |
| 1915-10-27 | 배 포기 |
| 1915-11-21 | 인듀어런스호 침몰 |
| 1916-04-09 | 부빙 붕괴, 보트 3척으로 탈출 |
| 1916-04-15 | 엘리펀트 섬 상륙 — **497일 만에 밟은 땅** |
| 1916-04-24 | 제임스 케어드 출항 (6명) |
| 1916-05-10 | 사우스조지아 킹하콘 만 도착 (17일) |
| 1916-05-20 | 산 넘어 스트롬니스 포경기지 도착 (36시간) |
| 1916-08-30 | 칠레 예초호가 엘리펀트 섬의 22명 구조 — **634일째** |

**계산 검산** — 1914-12-05 → 1916-08-30 = 634일. 1914-12-05 → 1916-04-15 = 497일. 영상 안에서 이 두 숫자만 씁니다.

## 3. 등장인물 — 고정 묘사(영문 앵커)

`gen.py` 의 ANCHOR 에 한국어 이름을 열쇠로 넣어 씁니다. **이 편에서 얼굴이 두 번 이상 나오는 사람만** 고정합니다(많이 고정할수록 프롬프트가 길어져 나머지가 흐려집니다).

| 이름(한국어 내레이션 기준) | 영문 고정 묘사 |
|---|---|
| 섀클턴 | a heavy-set British polar explorer in his early forties, broad square clean-shaven face, thick wool Burberry windproof jacket, wool balaclava pushed back |
| 워슬리 | a wiry New Zealand ship's captain in his forties, weathered narrow face with a short beard, wearing oilskins, holding a sextant |
| 크린 | a very tall broad-shouldered Irish sailor with a long face and a thick dark moustache, heavy knitted jumper |
| 블랙보로 | a thin twenty-year-old Welsh stowaway with a young beardless face, oversized borrowed coat |

⚠ **인물 일관성은 이 프로젝트에서 아직 검증되지 않았습니다.** 고정 묘사를 넣어도 같은 얼굴로 나오는지 확인된 적이 없습니다(퉁구스카 편에서 6장면 중 1장만 뽑아 봤습니다). **대본 승인 뒤 그림 단계 맨 처음에 섀클턴 4장을 나란히 뽑아 보고 판정합니다.** 여기서 깨지면 아래 「4-b」로 갑니다.

**4-b. 얼굴이 깨질 때의 대비책(미리 정해 둡니다).** 인물을 **뒷모습·실루엣·멀리서**로 그리는 비율을 늘립니다. 이 이야기는 방한복과 눈보라 덕에 **얼굴이 안 보여도 성립하는 몇 안 되는 소재**입니다. 이것이 이 소재를 1편으로 고른 이유입니다.

## 4. 화풍과 이 편 전용 규칙

- **화풍**: 만화풍 삽화 · 굵은 외곽선 · **한랭 한정 팔레트(청회색·흰색, 등불만 주황)**. 색을 묶으면 200장이 한 편처럼 보입니다.
- **이 편 전용 규칙층(그림 프롬프트에 조건부로 얹을 문장)**

| 조건 | 얹을 문장(요지) |
|---|---|
| 사람이 나오면 | 두꺼운 방한복·털모자·장갑, 맨손·맨얼굴 금지, 머리 하나, 1914~16년 복장 |
| 배가 나오면 | 세 돛대 목조 범선, 현대 선박·금속 선체 금지 |
| 얼음이 나오면 | **평평한 부빙 판**(빙산 절벽이 아님), 얼음 사이 검은 물길 |
| 개가 나오면 | 썰매개(허스키류), 늑대 아님, 하네스 착용 |
| 군중 | 인원은 28명 이하, 「수십 명」·군중 금지 |
| 항상 | 글자·숫자·워터마크 금지, 화풍 지배 문장 |

- **⛔ 그림으로 그리면 안 되는 것 → 프로그램 그래픽 카드로 뺍니다**: 항로 지도, 표류 궤적, 날짜 타임라인, 거리 비교(1,300km 가 어디서 어디까지인지), 기온 수치, 배 구조 단면.
  근거 — 퉁구스카 편에서 「시뮬레이션·비교 모형」 장면이 프롬프트 규칙으로도 안 고쳐졌습니다. **개념·도표는 그림 모델이 못 그립니다.**

## 5. 막 구성 — 22분 기준

초당 6.42자 · 장면 평균 5.3초(실측 기준선, PLAN_LONGFORM.md §1).

| 막 | 내용 | 분 | 대본 글자 | 장면 수 |
|---|---|---|---|---|
| 0 | 훅 | 0.3 | 120 | 4 |
| 1 | 출항 — 왜 갔나 | 2.7 | 1,040 | 31 |
| 2 | 갇힘 — 10개월의 표류 | 5.0 | 1,930 | 57 |
| 3 | 침몰과 얼음 위 5개월 | 4.0 | 1,540 | 45 |
| 4 | 보트 항해와 산 넘기 | 6.0 | 2,310 | 68 |
| 5 | 구조, 그 뒤, 그리고 2022년 | 4.0 | 1,540 | 45 |
| **합** | | **22.0** | **8,480** | **250** |

**분량 배분 근거** — 4막(보트 항해)이 가장 깁니다. 이 이야기의 클라이맥스가 거기 하나뿐이고, 2막(표류)은 사건이 적어 길게 끌면 이탈합니다. 2막은 「지루함 자체가 적」이라는 주제로 묶어 버팁니다.

## 6. 주요 장면 목록

형식: **번호 | 내레이션 요지 | 그림(영문) | 장면 수**
※ 아래는 **비트(beat)** 목록입니다. 대본 단계에서 각 비트가 표의 장면 수만큼 문장으로 쪼개집니다.

### 0막 — 훅 (4장면)

| # | 내레이션 요지 | 그림 | 장면 |
|---|---|---|---|
| 0-1 | 1915년 11월 21일, 스물여덟 명이 자기 배가 가라앉는 것을 보고 있었다 | men in furs standing on flat sea ice watching a wooden sailing ship's stern tilt into a black crack | 2 |
| 0-2 | 가장 가까운 사람까지 1,600km. 그들이 어디 있는지 아는 사람은 없었다 | **[그래픽 카드]** 남극 지도 위 점 하나와 거리 표시 | 1 |
| 0-3 | 그리고 634일 뒤, 스물여덟 명 전원이 살아서 돌아왔다 | a line of ragged bearded men walking up a wooden dock toward a whaling station | 1 |

### 1막 — 출항 (31장면)

| # | 내레이션 요지 | 그림 | 장면 |
|---|---|---|---|
| 1-1 | 1914년, 남극점은 이미 정복됐다. 남은 목표는 「횡단」이었다 | a flat white antarctic horizon with a single flag planted, empty | 3 |
| 1-2 | 아문센이 1911년 남극점에 먼저 닿았고, 스콧은 돌아오지 못했다 | two small sledging parties drawn far apart on white, one with a black-edged frame | 3 |
| 1-3 | 섀클턴의 계획 — 웨들해에서 로스해까지 3,000km를 걸어서 가로지른다 | **[그래픽 카드]** 남극 대륙 횡단 경로 | 2 |
| 1-4 | 대원 모집. ⚠ 유명한 구인광고는 출처가 확인되지 않았다 — 「전해지기로는」으로 처리하거나 뺀다 | a cramped London office with men queueing on a stairway | 3 |
| 1-5 | 뽑힌 28명 — 선장, 항해사, 목수, 요리사, 의사 둘, 생물학자, 사진사 | a group portrait of bearded men in wool sweaters on a ship's deck | 3 |
| 1-6 | 사진사 헐리 — 그가 남긴 유리건판이 이 이야기가 남은 이유다 | a man with a large wooden box camera on a tripod on deck | 2 |
| 1-7 | 1914년 8월, 1차 세계대전이 터졌다. 섀클턴은 배를 전쟁에 내놓겠다고 전보를 쳤다 | a telegram office, a man handing a slip over a counter | 3 |
| 1-8 | 해군의 답은 한 단어였다 — 「진행하라」 | **[그래픽 카드]** 전보 한 단어 | 1 |
| 1-9 | 배 이름은 인듀어런스, 견딘다는 뜻. 가문의 좌우명에서 따왔다 | a three-masted wooden barquentine at a quay, bow facing the viewer | 3 |
| 1-10 | 1914년 12월 5일, 사우스조지아를 떠났다. 여기서부터 날짜를 센다 | the ship leaving a bay between green-black mountains, whaling station behind | 3 |
| 1-11 | 포경선 선장들이 말렸다. 그해 얼음이 유난히 나쁘다고 | old whalers on a jetty pointing south, worried faces | 2 |
| 1-12 | 그래도 갔다 | the ship's stern receding between drifting ice floes | 3 |

### 2막 — 갇힘 (57장면)

| # | 내레이션 요지 | 그림 | 장면 |
|---|---|---|---|
| 2-1 | 6주 동안 얼음 사이를 비집고 1,600km를 나아갔다 | a wooden ship wedging through a narrow lead between flat ice floes, aerial view | 4 |
| 2-2 | 1915년 1월 19일, 목표를 150km 남기고 배가 멈췄다 | the ship stopped dead, ice closing around the hull, still water gone | 4 |
| 2-3 | 사방의 얼음이 붙어 버렸다. 배는 「초콜릿 속 아몬드처럼」 박혔다 | the ship frozen into a vast unbroken white plain, no water anywhere | 4 |
| 2-4 | 톱으로 잘라 보고, 끌로 깨 보고, 온몸으로 밀어도 소용없었다 | men with long ice saws and picks working around the hull, tiny against the ship | 4 |
| 2-5 | 2월, 섀클턴이 배를 「겨울 숙소」로 선언했다 | the deck roofed over with canvas, a stove pipe smoking | 3 |
| 2-6 | 여기서 이 이야기의 진짜 주제가 시작된다 — 적은 추위가 아니라 **지루함**이었다 | men sitting silently in a dim lamplit cabin, staring at nothing | 3 |
| 2-7 | 섀클턴은 하루 일과를 정했다. 시간을 지키게 했다 | men scrubbing decks in the ice, a strict routine | 3 |
| 2-8 | 얼음 위에서 축구를 했다 | men playing football on flat sea ice beside the trapped ship | 3 |
| 2-9 | 이발 대회, 연극, 음악회. 웃기려고 만든 일들이었다 | a row of grinning men with shaved heads in a lamplit cabin | 3 |
| 2-10 | 개집을 얼음 위에 지었다. 「개 호텔」이라 불렀다 | small snow kennels in rows on the ice, sled dogs in harness | 3 |
| 2-11 | 섀클턴은 불만이 생길 사람을 자기 텐트 옆에 뒀다 | **[그래픽 카드]** 텐트 배치도 — 누가 누구 옆인지 | 2 |
| 2-12 | 5월, 해가 지고 넉 달간 올라오지 않았다 | the ship under a completely dark sky, one lamp, green aurora overhead | 4 |
| 2-13 | 기온은 영하 30도 아래로 내려갔다 | **[그래픽 카드]** 월별 기온 그래프 | 2 |
| 2-14 | 그 사이 배는 얼음과 함께 북쪽으로 떠내려가고 있었다 | **[그래픽 카드]** 표류 궤적 지도 | 2 |
| 2-15 | 8월, 얼음이 움직이기 시작했다. 배가 밤마다 신음했다 | the hull squeezed by ice ridges rising against it, timbers bending | 4 |
| 2-16 | 10월, 얼음판 두 장이 배를 양쪽에서 눌렀다 | two great ice sheets crushing the ship's sides, deck buckling | 4 |
| 2-17 | 물이 들어왔다. 펌프질은 사흘을 버텼다 | men working a hand pump in knee-deep icy water below deck, lamplight | 3 |
| 2-18 | 10월 27일, 섀클턴이 배를 버리라고 말했다 | a man standing on tilting deck giving an order, men carrying bundles down onto ice | 2 |

### 3막 — 침몰과 얼음 위 다섯 달 (45장면)

| # | 내레이션 요지 | 그림 | 장면 |
|---|---|---|---|
| 3-1 | 얼음 위에 천막을 쳤다. 「오션 캠프」 | five small tents pitched on flat ice, the wrecked ship leaning in the distance | 4 |
| 3-2 | 섀클턴은 개인 소지품을 2파운드까지만 허용했다 | men laying watches, coins and books down onto the snow | 3 |
| 3-3 | 자기 금시계와 금화를 먼저 눈 위에 던졌다 | a man's gloved hand dropping a gold watch into snow, others watching | 3 |
| 3-4 | 대신 사진사의 유리건판 120장은 남기게 했다 | two men sorting glass photographic plates, smashing some, keeping a stack | 3 |
| 3-5 | 대신 밴조는 가져가게 했다 — 「정신의 약」이라고 했다 | a man holding a banjo among discarded belongings on the ice | 3 |
| 3-6 | 약한 개들과 배의 고양이는 총으로 죽였다. 목수는 끝내 용서하지 않았다 | a man walking away alone across ice, rifle lowered, dark sky | 3 |
| 3-7 | 11월 21일, 배가 가라앉았다. 섀클턴은 「가버렸다」고만 적었다 | the ship's stern rising then sliding into a black lead in the ice | 4 |
| 3-8 | 배를 끌고 걸어서 육지로 가려 했지만 하루에 1km도 못 갔다 | men in harness dragging a heavy lifeboat over broken ice ridges | 4 |
| 3-9 | 포기하고 다시 천막을 쳤다. 「페이션스 캠프」 — 인내 캠프 | tents on ice again, men sitting, doing nothing, flat grey light | 3 |
| 3-10 | 다섯 달 동안 한 일은 기다리는 것뿐이었다 | the same camp drawn small under a huge empty sky | 3 |
| 3-11 | 먹을 것이 떨어지자 남은 개들도 죽였다 | empty snow kennels, harnesses lying in a heap | 3 |
| 3-12 | 물개와 펭귄을 잡아 기름까지 태웠다 | men rendering blubber over a smoking stove on ice | 3 |
| 3-13 | 그 사이에도 얼음은 계속 북쪽으로 흘러갔다 | **[그래픽 카드]** 표류 궤적 — 캠프가 이동한 거리 | 2 |
| 3-14 | 1916년 4월 9일, 발밑의 얼음이 갈라졌다 | a crack splitting the camp, a tent half over black water | 4 |

### 4막 — 보트 항해 (68장면)

| # | 내레이션 요지 | 그림 | 장면 |
|---|---|---|---|
| 4-1 | 구명보트 세 척에 28명이 나눠 탔다 | three open wooden boats crowded with men pushing off from broken ice | 4 |
| 4-2 | 이레 동안 얼음물 위에 있었다. 앉은 채로 잤다 | men packed in an open boat, soaked, sleeping sitting up, ice all around | 4 |
| 4-3 | 물보라가 얼어붙어 보트가 무거워졌다 | a boat coated in thick ice, men chipping it off with knives | 3 |
| 4-4 | 마실 물이 없었다. 바닷물에 둘러싸인 채 목이 말랐다 | a man licking ice from an oar blade, cracked lips | 3 |
| 4-5 | 4월 15일, 엘리펀트 섬에 닿았다. 497일 만에 밟은 땅이었다 | men falling onto a black pebble beach under sheer dark cliffs | 4 |
| 4-6 | 어떤 사람은 자갈을 손에 쥐고 놓지 못했다 | a man kneeling, pouring black pebbles from hand to hand | 3 |
| 4-7 | 그런데 그 섬에는 아무도 오지 않는다. 항로에서 벗어나 있었다 | **[그래픽 카드]** 항로 지도 — 섬과 선박 항로의 거리 | 2 |
| 4-8 | 기다리면 전원 죽는다. 섀클턴은 구조를 부르러 가기로 했다 | a man looking out to sea from a beach, back to viewer | 3 |
| 4-9 | 목표는 사우스조지아. 7미터가 안 되는 보트로 1,300km 바다 | **[그래픽 카드]** 항로와 거리 | 2 |
| 4-10 | 그 바다는 지구에서 파도가 가장 높은 곳이다 | a tiny open boat at the bottom of a huge grey wave trough | 3 |
| 4-11 | 목수가 보트에 나무와 캔버스로 갑판을 덧댔다 | a carpenter nailing canvas over a boat's open top on a beach | 3 |
| 4-12 | 6명이 탔다. 섀클턴, 선장 워슬리, 크린, 목수, 선원 둘 | six men pushing a small decked boat into surf, others watching from shore | 3 |
| 4-13 | 남는 22명은 뒤집은 보트 두 척 밑에서 살았다 | men living under two upturned boats on a stone beach, smoke from a hole | 3 |
| 4-14 | 4월 24일 출항. 17일 동안 해를 네 번밖에 못 봤다 | the small boat alone in fog and spray, no horizon | 4 |
| 4-15 | 선장은 흔들리는 배 위에서 육분의로 해를 쟀다. 네 번의 관측이 전부였다 | a man braced by two others, holding a sextant up at a break in cloud | 4 |
| 4-16 | 한 번이라도 틀리면 섬을 지나쳐 대서양으로 나간다 | **[그래픽 카드]** 빗나갔을 때의 항로 | 2 |
| 4-17 | 다섯째 날, 하늘이 맑게 갠 줄 알았는데 파도였다 | an enormous wave wall filling the whole frame behind a tiny boat | 4 |
| 4-18 | 배가 물에 잠겼다가 떠올랐다. 물을 퍼내며 살아남았다 | men bailing frantically with a tin, boat half full of water | 3 |
| 4-19 | 5월 10일, 사우스조지아가 보였다. 그런데 상륙할 수 없었다 | black cliffs with surf exploding against them, boat held off | 3 |
| 4-20 | 폭풍 속에서 하루를 더 버티고 반대편 만에 들어갔다 | the battered boat sliding onto a small shingle cove | 3 |
| 4-21 | 문제가 남았다. 포경기지는 섬 반대편이었다 | **[그래픽 카드]** 섬 지형 — 상륙 지점과 기지 | 2 |
| 4-22 | 아무도 그 산을 넘은 적이 없었다. 지도조차 없었다 | jagged unmapped black-and-white mountains seen from below | 3 |
| 4-23 | 셋이 갔다. 나사를 신발 바닥에 박고 밧줄 하나를 들고 | three men fixing screws into boot soles by a fire | 3 |
| 4-24 | 36시간을 쉬지 않고 걸었다. 세 번 길이 막혀 되돌아왔다 | three tiny figures on a knife-edge snow ridge at dusk | 4 |
| 4-25 | 내려갈 길이 없자 밧줄을 깔고 미끄러져 내려갔다 | three men sliding down a steep snow slope together, rope coiled under them | 3 |
| 4-26 | 5월 20일 아침, 멀리서 기지의 기적 소리가 들렸다 | three ragged men stopping on a ridge, a distant whaling station below | 3 |

### 5막 — 구조와 그 뒤 (45장면)

| # | 내레이션 요지 | 그림 | 장면 |
|---|---|---|---|
| 5-1 | 기지장은 그들을 못 알아봤다. 2년 만에 죽은 줄 알았던 사람이 걸어 들어왔다 | a station manager staring at three filthy bearded men in a doorway | 4 |
| 5-2 | 섀클턴이 물은 첫 질문은 「전쟁은 끝났습니까」였다 | two men talking in a warm office, one still in rags | 3 |
| 5-3 | 답은 「아니요, 수백만 명이 죽었습니다」였다 | **[그래픽 카드]** 1916년 세계 — 그들이 모르던 2년 | 2 |
| 5-4 | 그리고 섀클턴은 곧바로 엘리펀트 섬으로 돌아가려 했다 | a man pointing at a chart, others shaking heads | 3 |
| 5-5 | 첫 번째 배는 얼음에 막혔다 | a small steamer stopped by pack ice | 3 |
| 5-6 | 두 번째도, 세 번째도 막혔다 | **[그래픽 카드]** 구조 시도 4회 — 날짜와 결과 | 2 |
| 5-7 | 그 사이 섬의 22명은 넉 달을 더 버티고 있었다 | men under an upturned boat, thin faces, one with bandaged foot | 4 |
| 5-8 | 스무 살 밀항자는 발가락을 모두 잃었다. 의사 둘이 보트 밑에서 수술했다 | a makeshift operation under an upturned boat by lamplight | 3 |
| 5-9 | 요리사는 매일 아침 「짐을 싸라, 오늘 대장이 온다」고 말하게 했다 | men rolling up bedding each morning, looking at the sea | 3 |
| 5-10 | 1916년 8월 30일, 네 번째 배가 얼음을 뚫었다 | a small tug appearing between ice, men on a beach running and waving | 4 |
| 5-11 | 섀클턴은 배 위에서 사람을 셌다. 스물둘. 전원이었다 | a man on a boat's bow counting figures on a beach, hand raised | 4 |
| 5-12 | 634일 만에, 28명 전원이 살아서 돌아왔다 | **[그래픽 카드]** 634일 타임라인 전체 | 2 |
| 5-13 | 그들은 남극을 횡단하지 못했다. 목표는 완전히 실패했다 | the unwalked antarctic interior, empty white | 3 |
| 5-14 | 그런데 지금 이 원정은 「리더십의 교과서」로 남았다 | the group portrait from act 1, now weathered | 3 |
| 5-15 | 섀클턴은 6년 뒤 같은 섬에서 심장마비로 죽었다. 그곳에 묻혔다 | a simple grave stone among mountains, ship's crew standing | 3 |
| 5-16 | 2022년, 난파선이 3,008미터 아래에서 발견됐다. 이름이 그대로 보였다 | a ship's stern on the dark seabed, the name plate lit by a submersible | 4 |
| 5-17 | 마무리 — 그들이 남긴 것은 기록이 아니라 「전원」이라는 숫자다 | a warm lamplit ship's cabin, empty, banjo leaning on a bunk | 4 |

**장면 수 검산** — 0막 4 · 1막 31 · 2막 57 · 3막 45 · 4막 68 · 5막 45 = **250**. §5 표와 일치합니다.

## 7. 확인하지 못한 것 · 남은 결정

- **인물 얼굴이 유지되는지 모릅니다.** 이 프로젝트에서 한 번도 검증된 적이 없습니다(§3).
- **그래픽 카드(지도·타임라인)를 만드는 코드가 아직 없습니다.** 위 목록에 **[그래픽 카드] 24장면**이 들어 있습니다. 퉁구스카 편에서는 이것을 그림 모델에 맡겼다가 실패했습니다. 대본 승인 뒤 **별도 결정**이 필요합니다.
- 음악·효과음은 이 기획안 범위 밖입니다.
- ⚠ **§2 의 네 가지 수치 확인이 대본보다 먼저입니다.**

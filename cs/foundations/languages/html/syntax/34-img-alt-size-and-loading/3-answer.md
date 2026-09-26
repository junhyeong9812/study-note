# html/syntax/34 — `img`: `alt`·`width`/`height`·`loading`/`decoding`/`fetchpriority` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** 받은 것이다. 블록은 캡처 조립기로 붙였다. 하네스는 [33번 주제](../33-output-progress-meter/3-answer.md)의 `## 실행 검증` 절에 있다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 렌더링 절(차원 속성 · `aspect-ratio` 번역 · 그림이 없을 때)과 [HTML-AAM](https://w3c.github.io/html-aam/) 의 `img` 대응·이름 계산으로 접지했다(앞 배치가 받아 둔 사본). ★ **`img` 요소 절 · 지연 로딩 · `fetchpriority` 절은 사본에 없다 — 그 셋의 명세층은 판정 보류.**\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다. ★ **시간은 재지 않았다.**
> ★★★ **본체는 로드 전후 격자와 요청 순서다** — 「움직인 칸」·「`load` 전에 요청이 간 칸」·「명세 열과 갈린 칸」을 스크립트가 센다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 움직인 칸 3 / 6(B · C · F) — 속성 둘이면 `"auto 300 / 150"` · D 는 안 움직였지만 `150×150` 으로 찌그러짐 · E 는 `150×75`

**출력**

```text
$ python3 html33b-run.py 격자 html33b-34-shift.html
  서버    받음  h/p300x150.png?k=A
  서버    받음  h/p300x150.png?k=B
  서버    받음  h/p300x150.png?k=C
  서버    받음  h/p300x150.png?k=D
  서버    받음  h/p300x150.png?k=E
  서버    받음  h/p300x150.png?k=F
  서버    풀어 줌
  서버    표지  끝
img                                             aspect-ratio 계산값   로드 전 상자    로드 뒤 상자    아래 요소가 움직였나
A width + height                                "auto 300 / 150"      300×150         300×150         아니오 (155 → 155)
B width 만                                      "auto"                300×0           300×150         예 (24 → 155)
C 없음                                          "auto"                0×0             300×150         예 (24 → 155)
D width + height · CSS width:100%               "auto 300 / 150"      150×150         150×150         아니오 (155 → 155)
E width + height · CSS width:100%; height:auto  "auto 300 / 150"      150×75          150×75          아니오 (80 → 80)
F 없음 · CSS width:100%; height:auto            "auto"                150×0           150×75          예 (24 → 80)
로드 전 complete = false · false · false · false · false · false · 로드 뒤 = true · true · true · true · true · true
움직인 칸 = 3 / 6
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- ★★★ **A · D · E**(속성 둘) — 로드 전부터 `aspect-ratio` 가 `"auto 300 / 150"` 이고 상자가 선다. **아래가 안 움직였다.**
- ★★★ **B · C · F**(속성 하나 · 없음) — `"auto"` · 로드 전 **높이 0** → 그림이 오며 **아래가 내려갔다**(`24 → 155` · `24 → 155` · `24 → 80`).
- ★★★ **D** — 속성의 `height: 150px`(차원 속성 표현 힌트)이 남아 **높이가 비율보다 먼저** 정해졌다 → `150×150`. **E** 는 `height:auto` 가 그 힌트를 덮어 비율이 높이를 정했다(A6).
- **A** — 칸을 넘친다(`300×150` 그대로). 속성은 크기다.

### 2. `위-eager`·`아래-eager` → `DOMContentLoaded` → `위-lazy` → (풀어 줌) → `load` → 스크롤 → `아래-lazy` · `load` 전 요청 3 / 4 · 우선순위 `Medium → High` / `Low` / `Medium` / `Low`

**출력**

```text
$ python3 html33b-run.py 격자 html33b-34-lazy.html
  서버    받음  h/p300x150.png?k=아래-eager
  서버    받음  h/p300x150.png?k=위-eager
  서버    표지  DOMContentLoaded
  서버    받음  h/p300x150.png?k=위-lazy
  서버    표지  두 틀 뒤
  서버    풀어 줌
  서버    표지  load
  서버    표지  스크롤 전
  서버    받음  h/p300x150.png?k=아래-lazy
  서버    표지  스크롤 뒤 아래-lazy load
  서버    표지  끝

img             DOMContentLoaded 전   load 전   스크롤 전   처음 우선순위 → 바뀐 우선순위
위-eager        예                    예        예          Medium → High
위-lazy         아니오                예        예          Low
아래-eager      예                    예        예          Medium
아래-lazy       아니오                아니오    아니오      Low
스크롤 전 complete = {"위e":true,"위l":true,"아래e":true,"아래l":false}
load 전에 요청이 간 칸 = 3 / 4
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- ★★★ **`eager` 둘은 `DOMContentLoaded` 전** — 파서가 만나는 대로 요청한다. 한참 아래여도 같다.
- ★★★ **첫 화면의 `lazy` 는 `DOMContentLoaded` 뒤**(두 틀 표지보다는 앞) — 레이아웃이 「화면 안」을 알려 준 뒤에야 나갔다. 우선순위 **`Low` 그대로.**
- ★★★ **한참 아래의 `lazy` 는 `load` 뒤 · 스크롤 뒤** — 스크롤 전 `complete` 가 `false` 인 것이 그 짝이다.
- ★★ **우선순위** — 화면 안 `eager` 만 `Medium → High` 로 올랐다. 한참 아래 `eager` 는 `Medium` 에 머물렀다.

### 3. 명세 열과 갈린 칸 0 / 18 — `alt` 없음: `image`·`""`·깨지면 16×16 · `alt=""`: `none`·무시·깨지면 0×0 · `alt="파란 사각형"`: `image`·그 글자·깨지면 글자 상자

**출력**

명세 열 파일 —

```javascript
// html33b-34-alt-spec.js
// 명세 열 — 칸마다 [허용되는 값…]
// 역할: HTML-AAM — img 는 image(ARIA 1.3 의 이름 · 옛 이름 img) · alt 가 공백뿐이면 none 또는 presentation
// 이름: HTML-AAM 「img 의 이름 계산」 — alt 를 쓴다(비어 있어도) · alt 가 없으면 title · 그것도 없으면 figcaption 조건 · 그 밖에는 이름 없음
// 그려진 것: Rendering 「Images」 — 그림이면 그림 · 그림이 아니고 alt 가 없으면 아이콘(글자 없이) · 글자를 나타내면 그 글자 · 아무것도 안 나타내면 0×0
const 명세 = {
  a1: { 역할: ["image", "img"], 이름: [""], 그림: ["그림"] },
  a2: { 역할: ["none", "presentation"], 이름: [""], 그림: ["그림"] },
  a3: { 역할: ["image", "img"], 이름: ["파란 사각형"], 그림: ["그림"] },
  b1: { 역할: ["image", "img"], 이름: [""], 그림: ["아이콘"] },
  b2: { 역할: ["none", "presentation"], 이름: [""], 그림: ["0×0"] },
  b3: { 역할: ["image", "img"], 이름: ["파란 사각형"], 그림: ["글자"] },
};
```

```text
$ python3 html33b-form.py page html33b-34-alt.html
img                                 상자        그려진 것 역할    이름            무시   naturalWidth
a1 파일 있음 · alt 없음             300×150     그림      image   ""              false  300
a2 파일 있음 · alt=""               300×150     그림      none    ""              true   300
a3 파일 있음 · alt="파란 사각형"    300×150     그림      image   "파란 사각형"   false  300
b1 파일 없음(404) · alt 없음        16×16       아이콘    image   ""              false  0
b2 파일 없음(404) · alt=""          0×0         0×0       none    ""              true   0
b3 파일 없음(404) · alt="파란 사각형" 94.09375×24 글자      image   "파란 사각형"   false  0
(그려진 것 = naturalWidth 가 있으면 그림 · 0×0 · alt 글자가 있으면 글자 · 나머지는 아이콘)
명세 열과 갈린 칸 = 0 / 18
(exit 0)
```

**왜 그런가**

- ★★★ **`alt=""` → `none` · 무시 `true`** — HTML-AAM 「공백뿐이면 `none` 또는 `presentation`」.
- ★★★ **`alt` 없음 → `image` · 이름 `""`** — 이름 계산에 `alt`·`title`·figcaption 이 다 없으니 **이름 없음.** 파일 이름은 이름 계산 단계에 **없다**(A8).
- ★★ **깨짐** — `alt` 없음 **16×16**(렌더링 절 「아이콘」 자리로 읽힌다) · `alt=""` **0×0**(「아무것도 안 나타내면 자연 크기 0」) · 글자 있음 **글자 상자**(「그 글자를 가진 구절 요소로」). ★ 폭 `94.09375` 는 **글꼴에 달린 칸**이다.

### 4. `high` 는 `High` · `low` 는 `Low` · 속성 없음과 `decoding` 둘은 `Medium → High` · 한참 아래 `high` 는 `High` / 순서는 한 가지가 아니다

**출력**

```text
$ python3 html33b-run.py 격자 html33b-34-prio.html
img                                 처음 우선순위 → 바뀐 우선순위
r1 (속성 없음)                      Medium → High
r2 fetchpriority=high               High
r3 fetchpriority=low                Low
r4 decoding=async                   Medium → High
r5 decoding=sync                    Medium → High
r6 fetchpriority=high · 한참 아래   High
풀어 주기 전에 서버가 받은 이미지 = 6 / 6  (★ 받은 순서는 판마다 흔들린다 — 따로 센다)
뒤늦게 온 요청 = 0
(exit 0)
```

```text
$ python3 html33b-tally.py 20
  6 판  r2 r1 r6 r4 r5 r3
  5 판  r2 r6 r1 r4 r5 r3
  4 판  r2 r1 r4 r6 r5 r3
  2 판  r1 r2 r4 r6 r5 r3
  1 판  r1 r2 r6 r4 r5 r3
  1 판  r1 r4 r2 r6 r3 r5
  1 판  r6 r2 r1 r4 r5 r3
판 = 20 · 순서의 가짓수 = 7
r3(fetchpriority=low)이 마지막인 판 = 19 / 20
r2(fetchpriority=high)가 r1(속성 없음)보다 먼저인 판 = 16 / 20
(exit 0)
```

**왜 그런가**

- ★★★ **`fetchpriority` 는 처음 우선순위를 바꿨다** — `high` 는 화면 밖이어도 `High`, `low` 는 끝까지 `Low`.
- ★★★ **`decoding` 은 요청 창에 흔적이 없다** — `async`·`sync` 모두 속성 없는 것과 같다(18-B · 부적용 — 받은 뒤의 이야기다).
- ★★★ **순서는 흔들린다** — 20 판의 가짓수가 1 이 아니다. `low` 가 거의 늘 마지막, `high` 가 대부분 속성 없는 것보다 먼저 — **「늘」이 아니다.** 한 판의 순서를 근거로 쓰면 안 된다(규칙 11).

### 5. 두 속성이 **둘 다** 있고 · 차원 값으로 파싱되고 · **퍼센트가 아닐 때** — `auto` 는 「원래 비율이 오면 그것, 오기 전에는 이 비율」

- 명세(렌더링) — 「`img` 의 dimension attribute source 의 `width`·`height` 는 차원 속성으로, 그리고 **aspect-ratio 로 번역된다(차원 규칙으로)**」 · 「차원 규칙으로 — 둘 다 있고, 차원 값 파싱이 에러가 아니고 **퍼센트를 돌려주지 않으면** `aspect-ratio: auto w / h` 의 표현 힌트」.
- `auto <ratio>` 의 CSS 뜻은 [CSS 31번](../../../css/syntax/31-intrinsic-sizing-and-aspect-ratio/2-summary.md) — 「원래 비율이 있으면 그것을, 없으면 이 비율을」. 로드 전엔 원래 비율이 없으니 **속성의 비율**이 쓰인다.

### 6. 높이는 속성의 **`height: 150px` 힌트**가 정한다 — 작성자 CSS 가 `width` 만 덮기 때문 · `height:auto` 를 더하면 비율이 높이를 정한다

- 속성 → 표현 힌트 **셋** — `width: 300px` · `height: 150px` · `aspect-ratio: auto 300 / 150`. 작성자 CSS `width:100%` 는 **첫째만** 이긴다.
- 높이가 정해진 상자에서 `aspect-ratio` 는 **쓸 데가 없다** — 그래서 `150×150`(A1 D).
- `height:auto` 가 둘째를 덮으면 **비율이 높이를 계산**한다 — `150×75`(A1 E).

### 7. 첫 화면의 그림 — 잰 것: 「`eager` 보다 늦게 · `DOMContentLoaded` 뒤에 요청」·「우선순위 `Low` 에서 안 오름」 / 말할 수 없는 것: 그것이 몇 ms · LCP 가 얼마나 나빠지나

- A2 의 `위-lazy` 가 근거다. **순서와 이름**은 안 흔들리는 칸이다.
- ★★★ 「LCP 가 나빠진다」는 **시간 주장**이고 이 판은 시간을 안 쟀다 — 서버가 그림을 **붙잡아 두는** 판이라 시간을 재도 뜻이 없다.

### 8. `alt` 없음 — `image`·이름 없음·깨지면 16×16 · `alt=""` — `none`·트리에서 무시·깨지면 0×0 / 파일 이름 — 이 판의 트리에는 **없다**(보조 기술이 따로 읽는지는 못 잰다)

- 트리의 이름은 `""` 였다(A3 `a1`·`b1`). HTML-AAM 이름 계산에 파일 이름 단계가 없다.
- 「스크린 리더가 파일 이름을 읽는다」는 **보조 기술 쪽의 동작**이다 — 이 판은 트리까지만 본다(못 잰 것).

### 9. `true` — 가르는 칸은 `naturalWidth`(깨지면 0)

- A3 — 깨진 셋도 `complete` 가 `true`, `naturalWidth` 는 `0`. `complete` 는 「**더 할 일이 없나**」다.

### 10. `eager` 둘은 `DOMContentLoaded` 앞 · 첫 화면 `lazy` 는 그 뒤 · `load` 는 세 장이 온 뒤 · 한참 아래 `lazy` 는 `load` 뒤 — `load` 는 **요청된 그림**만 기다린다

- [08번](../08-script-loading/2-summary.md) — `DOMContentLoaded` 는 파싱 끝(이미지를 안 기다림) · `load` 는 그 뒤.
- 한참 아래의 `lazy` 는 **`load` 때까지 요청되지 않았다** — 기다릴 것이 없었다(A2).

### 11. 번역 조건 — 명세 · 우선순위 이름 — 구현 · `alt=""` 의 역할 — 명세(HTML-AAM) · 깨진 그림의 크기 — 명세의 렌더링 절이 틀을 주고 **16×16 은 구현** · 서버 순서 — 관찰(흔들림)

- **명세** — `aspect-ratio` 번역 · 차원 속성 · `alt` 의 역할·이름 · 그림이 없을 때의 세 갈래.
- **구현(Chrome)** — `Low`/`Medium`/`High` 라는 이름과 승격 · 첫 화면 `lazy` 를 레이아웃 뒤에 · 아이콘 자리 16×16.
- **관찰** — 20 판의 순서 가짓수.
- **판정 보류** — 지연 로딩·`fetchpriority`·`decoding` 의 명세 절(사본 없음).

### 12. 정본 경계

- **`aspect-ratio` 의 `auto <ratio>` 뜻** — [CSS 31번](../../../css/syntax/31-intrinsic-sizing-and-aspect-ratio/2-summary.md).
- **`object-fit` 으로 자르기** — [CSS 44번](../../../css/syntax/44-backgrounds-and-object-fit/2-summary.md).
- **`srcset`/`sizes`** — [35번 주제](../35-srcset-and-sizes/2-summary.md).
- **스크립트로 직접 지연 로딩** — [web-api 35번](../../../../web-api/35-intersection-observer/2-summary.md)(`IntersectionObserver`).

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · 칸마다 **새 탭 · `Network.setCacheDisabled(true)` · `Emulation.setDeviceMetricsOverride`(1000×800 · DPR 1)**. **엔진은 이것 하나다.** 하네스는 [33번](../33-output-progress-meter/3-answer.md)의 `html33b-run.py`·`html33b-make-images.py`·`html33b-tally.py` 다.

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

★ **「로드 전」** — 이미지는 `h/` 경로라 서버가 **`/go` 가 올 때까지 응답하지 않는다.** 실행기가 `DOMContentLoaded` → 두 틀 → `__전()` → `/go` → `load` → `__뒤()` 순으로 부른다. 「로드 전 `complete` 가 여섯 다 `false`」가 그 확인 칸이다(A1).\
★ **순서 표지** — 페이지가 `fetch('/m?…')` 로 보내는 표지가 서버 로그에 **받은 순서대로** 찍힌다. 시각은 적지 않는다.

**흔들림 확인** — 캡처 세 판의 재대조는 [33번](../33-output-progress-meter/3-answer.md)의 `## 실행 검증` 에 있다. ★ **`34-prio-tally` 블록만 설계상 흔들린다** — 그 블록 전용 정규화 규칙 넷(순서 줄 · 가짓수 · 두 비율)을 더해 견줬다. 세 캡처의 두 비율 줄은 **「`r3` 마지막」 19 · 19 · 18 / 20 · 「`r2` 가 `r1` 보다 먼저」 16 · 18 · 19 / 20** 이었다 — 자릿수(「대부분」)만 주장한다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| **로드 전후 여섯 `img`** | 3 | 동작 방식 (1) · A1 |
| **요청 시점 네 `img`** | 3 | 동작 방식 (2) · A2 |
| **`alt` 격자 18 칸** | 3 | 동작 방식 (3) · A3 |
| **우선순위 여섯** | 3 | 동작 방식 (4) · A4 |
| **서버 순서** | 20 × 3 | 동작 방식 (4) · A4 |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| 첫 화면 `lazy` 의 요청 시점·우선순위 | `DOMContentLoaded` 뒤 · `Low` | 명세 사본에 지연 로딩 절이 없다 |
| 우선순위 이름과 승격 | `Medium → High` 등 | 브라우저의 스케줄러다 |
| 깨진 `alt` 없는 그림의 크기 | 16×16 | 명세는 「아이콘」까지만 |

**안 돌려 본 것** — ① **스크립트를 끈 문서의 `lazy`.** ② **지연 로딩의 거리 문턱.** ③ **`title`·figcaption 이 이름을 주는 판**(명세 문장만).

**못 잰 것** — ① **LCP·시간.** ② **`decoding` 의 디코드 때.** ③ **보조 기술이 `alt` 없는 그림에서 읽는 것.**

**부적용인 창** — **창 ① · ③ · ④ · ⑥**.

## 용어 풀이

- **붙잡기(`h/` 경로)** — 서버가 이미지 응답을 `/go` 까지 미루는 것. 「로드 전」을 확실히 잡으려고.
- **표지(`/m?…`)** — 페이지가 서버 로그에 순서를 박으려고 보내는 빈 요청.
- **처음 우선순위** — CDP `Network.requestWillBeSent` 의 `initialPriority`.

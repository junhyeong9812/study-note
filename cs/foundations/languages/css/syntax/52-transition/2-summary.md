# css/syntax/52 — `transition`: 전환 가능한 속성·타이밍 함수·지연·`transition-behavior` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [CSS Transitions Level 1](https://drafts.csswg.org/css-transitions-1/) (시작 조건·되돌리기·단축 순서) · [CSS Transitions Level 2](https://drafts.csswg.org/css-transitions-2/) (`transition-behavior`·`@starting-style`) · [CSS Easing Functions Level 1](https://drafts.csswg.org/css-easing-1/) (타이밍 함수). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 `demo` 블록 **4개 전부**를 **Google Chrome 151.0.7922.173** headless 에 띄우고, **CDP 로 실제 마우스를 움직여 `:hover` 를 발생시킨 뒤** 시간대별로 `getComputedStyle` 값을 샘플링했다.\
> 본문에 나오는 모든 시각별 값은 그 실측값이다(샘플 시각은 ±10ms 오차가 있다). **WebKit(Safari)은 이 머신에 없다** — Safari 관련 서술은 하지 않았다.
> **버전** — 전환 자체는 Baseline **widely**(newly 2015-09-30 → widely 2018-03-30). `linear()` 이징은 **widely**(newly 2023-12-11 → widely 2026-06-11). `transition-behavior` 와 `@starting-style` 는 **newly**(둘 다 2024-08-06, 아직 widely 아님) — 목록 README 의 지원 표와 `api.webstatus.dev` 조회 결과.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**전환 = 값이 바뀔 때 '순간이동' 대신 '걸어가게' 만드는 것이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 출발지 / 도착지 | 바뀌기 전 값 / 바뀐 뒤 값 |
| 걸어서 간다 | 두 값 사이를 **보간**해 매 프레임 중간값을 만든다 |
| 걷는 데 걸리는 시간 | `transition-duration` |
| 걷는 속도의 리듬 | `transition-timing-function` (등속? 처음에 빠르게? 계단?) |
| 출발 전 뜸들이기 | `transition-delay` |
| 어느 짐을 들고 갈지 | `transition-property` |
| **미리 신발을 신고 있어야 한다** | 값이 바뀌기 **전에** 그 요소에 `transition` 이 이미 걸려 있어야 한다 |

- 전환은 **내가 시작시키는 것이 아니다.** 어떤 이유로든 계산값이 바뀌면 브라우저가 알아서 건다.\
  `:hover`·클래스 토글·미디어 쿼리·JS 스타일 변경 전부 방아쇠가 된다.
- 그래서 "**신발을 언제 신고 있었나**"가 이 주제에서 가장 자주 나는 사고다.\
  `transition` 을 `:hover` 안에만 쓰면 들어갈 때는 걷고 **나올 때는 순간이동**한다.
- 걸어갈 수 없는 짐도 있다.\
  `height: auto` 처럼 **중간값을 만들 수 없는 값**은 전환이 아예 시작되지 않는다.

```text
값이 바뀐 순간

  전환이 없을 때            전환이 있을 때 (0.6s)
  +---------+              +---------+
  | #e2e8f0 |              | #e2e8f0 |
  +----|----+              +----|----+
       | 한 프레임              | 0.6초 동안 매 프레임 중간값
       v                       v   #d4dde8 -> #92a9e6 -> #446cdd -> ...
  +---------+              +---------+
  | #1d4ed8 |              | #1d4ed8 |
  +---------+              +---------+
```

실무에서 이게 터지는 자리는 **아코디언·드롭다운의 높이 애니메이션**이다.\
`height: 0` ↔ `height: auto` 로 짜면 열고 닫는 게 뚝 끊기는데, 에러도 경고도 없어서 "왜 내 CSS 만 안 되지"로 시간을 쓴다.

> **보간(interpolation)** — 시작값과 끝값 사이의 중간값을 만드는 것.\
> 예: `0px` 와 `100px` 사이의 30% 지점은 `30px`. `auto` 와 `100px` 사이의 30% 지점은 **만들 수 없다.**

> **계산값(computed value)** — 캐스케이드와 상속이 끝난 뒤 그 속성에 확정된 값. 전환은 **이 값이 바뀔 때** 걸린다.\
> 예: `width: 50%` 의 계산값은 `50%` 이고, 실제 픽셀은 그다음 단계에서 정해진다(목록의 **04번 주제**).

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 어떤 속성이 전환되고 **어떤 속성은 왜 아예 시작조차 안 하는가.**
2. `transition: 0.2s 1s` 에서 **어느 쪽이 지속이고 어느 쪽이 지연인가.**
3. 전환 도중에 마우스를 떼면 **어디서부터, 얼마 동안 되돌아가는가.**

## 동작 방식

### (1) 전환이 걸리는 조건 — 세 가지가 동시에 맞아야 한다

**언제 쓰나** — "전환이 안 걸린다"를 진단할 때. 거의 모든 사고가 이 세 줄 중 하나다.

```text
① 계산값이 바뀐다                 :hover · 클래스 토글 · 미디어 쿼리 · JS
        ↓
② 바뀌기 '전' 상태에 transition 이 걸려 있다
        ↓   (바뀐 뒤 상태에만 있으면 그 방향만 걸린다)
③ 그 속성의 두 값 사이에 중간값을 만들 수 있다
        ↓   (auto · none 같은 키워드는 못 만든다)
   전환 시작
        ↓
   duration 동안 매 프레임 중간값을 계산값 자리에 끼워 넣는다
        ↓
   끝나면 원래 계산값으로 넘긴다
```

그림 해설 (한 단계씩):

- ①은 **내가 시작시키는 것이 아니다.** 값이 바뀌는 모든 경로가 방아쇠다.
- ②가 가장 자주 틀린다 — `transition` 은 **기본 상태(변하기 전 규칙)에** 쓴다.
- ③이 「어디서 틀리나」의 본체다. **보간할 수 없으면 조용히 순간이동한다.**

비용 — 전환이 걸리는 동안 **매 프레임 그 속성이 속한 단계부터 파이프라인이 다시 돈다.**\
`transform`·`opacity` 는 합성만, `width`·`height`·`margin` 은 레이아웃부터다(목록의 **56번 주제**).

### (2) 무엇이 보간되나 — `auto` 는 왜 안 되나

**언제 쓰나** — 아코디언·드롭다운처럼 "펼치는" UI 를 짤 때.

```html demo
<div class="card auto">auto 로 펴기<br>둘째 줄</div>
<div class="card fixed">고정 px 로 펴기<br>둘째 줄</div>
<style>
  .card { width: 240px; height: 24px; overflow: hidden; margin: 8px;
          background: #e2e8f0; font: 15px/24px system-ui;
          transition: height 1s linear; }
  .auto:hover  { height: auto; }       /* auto 는 보간할 수 없다 */
  .fixed:hover { height: 48px; }
</style>
```

> **보이는 것** — 아래 상자(`fixed`)는 마우스를 올리면 1초에 걸쳐 24px → 48px 로 **부드럽게 펴지고**, 위 상자(`auto`)는 **전환 없이 즉시** 48px 로 튄다. 마우스를 떼면 `fixed` 는 1초에 걸쳐 접히고 `auto` 는 즉시 접힌다.\
> **바꿔 볼 것** — `.auto:hover` 의 `height: auto` → `height: 48px` → 두 상자가 똑같이 움직인다 · `transition: height 1s linear` → `grid-template-rows 1s linear` 로 바꾸고 `0fr`↔`1fr` 을 쓰면 → 내용 높이를 모르고도 전환할 수 있다(목록의 27번)

*(Chrome 151 headless 실측 — 마우스를 올린 뒤 시각별 `height`:)*

```text
            t=30ms     t=400ms    t=1300ms
  .fixed    24.8px     34px       48px        <- 1초에 걸쳐 선형으로 간다
  .auto     48px       48px       48px        <- 30ms 에 이미 끝나 있다
```

명세는 전환 가능 조건을 이렇게 정한다.

> property values are transitionable if they have an animation type that is neither not animatable nor discrete.

| 값의 종류 | 전환되나 | 예 |
|---|---|---|
| 길이·백분율·수 | **된다** | `10px` ↔ `100px` · `0` ↔ `1` |
| 색 | **된다** | `#e2e8f0` ↔ `#1d4ed8` |
| 변환·필터 함수 | **된다**(같은 함수 목록일 때) | `translateX(0)` ↔ `translateX(100px)` |
| `auto`·`none`·`fit-content` 같은 키워드 | **안 된다** | `height: 24px` ↔ `height: auto` |
| discrete 타입 | 기본은 **안 된다** | `display`·`visibility`·`font-family` |

- `auto` 가 안 되는 이유는 **중간값을 정의할 방법이 없기 때문**이다. `auto` 는 "내용에 맞춰라"라는 지시이지 수가 아니다.
- **에러가 나지 않는다.** 선언은 유효하고, 전환만 시작되지 않는다.

> **discrete 타입** — 중간값 없이 한 값에서 다른 값으로 **툭 바뀌는** 애니메이션 타입.\
> 예: `display: block` 과 `display: none` 사이에 "반쯤 none" 은 없다.

### (3) 네 부품 — 무엇을, 얼마나, 어떤 리듬으로, 언제부터

**언제 쓰나** — 전환을 처음 쓸 때. 네 개가 전부다.

```text
  transition-property         어느 속성을 전환할지        기본 all
  transition-duration         얼마나 오래                 기본 0s  <- 이게 0이면 아무 일도 안 난다
  transition-timing-function  어떤 리듬으로                기본 ease
  transition-delay            언제부터                    기본 0s
```

```html demo
<button class="btn">마우스를 올려 보세요</button>
<style>
  .btn { padding: 10px 20px; font: 16px system-ui; border: 0;
         background-color: #e2e8f0; color: #0f172a;
         transition: background-color .6s ease, color .6s ease; }
  .btn:hover { background-color: #1d4ed8; color: #ffffff; }
</style>
```

> **보이는 것** — 마우스를 올리면 0.6초에 걸쳐 배경이 밝은 회색에서 파랑으로, 글자가 거의 검정에서 흰색으로 **서서히** 바뀐다. 마우스를 떼면 같은 0.6초를 들여 되돌아온다. 변화는 **처음이 빠르고 끝이 느리다**(기본 `ease`).\
> **바꿔 볼 것** — `.6s` → `3s`(느리게) · `ease` → `linear`(등속으로 바뀌는 게 눈에 보인다) · `.btn:hover` → `.btn:hover, .btn:focus-visible`(키보드 Tab 으로도 되는지)

*(Chrome 151 headless 실측 — 마우스를 올린 뒤 시각별 `background-color`:)*

```text
  t=0        rgb(226, 232, 240)     출발
  t=50ms     rgb(212, 221, 238)
  t=150ms    rgb(146, 169, 230)
  t=300ms    rgb( 68, 108, 221)     <- 시간은 절반인데 색은 80% 왔다
  t=450ms    rgb( 37,  84, 217)
  t=700ms    rgb( 29,  78, 216)     도착 (#1d4ed8)
```

그림 해설 (한 단계씩):

- **시간 절반(300ms)에 이미 80% 를 왔다.** 빨간 채널로 재면 `(226-68) / (226-29) = 80.2%` 다.\
  이것이 기본값 `ease` 의 모양이다 — 등속이 아니다.
- `transition-property` 를 안 적으면 `all` 이라 **바뀌는 모든 속성**이 전환된다.\
  편하지만 **의도하지 않은 속성까지** 전환되고(레이아웃 속성이 섞이면 비싸다), 무엇이 전환되는지 읽어서 알 수 없게 된다.
- `transition-duration` 의 기본값은 **`0s`** 다. 그래서 `transition: background-color;` 처럼 시간을 빼면 **아무 일도 일어나지 않는다.**

### (4) 타이밍 함수 — 같은 시간, 다른 리듬

**언제 쓰나** — "움직이긴 하는데 느낌이 이상하다"를 고칠 때.

```html demo
<div class="lane"><i class="linear"></i><i class="ease"></i><i class="ei"></i><i class="st"></i></div>
<style>
  .lane { width: 320px; border: 2px solid #94a3b8; padding: 6px; }
  .lane i { display: block; width: 40px; height: 22px; margin: 4px 0;
            background: #1d4ed8;
            transition-property: margin-left; transition-duration: 2s; }
  .lane:hover i { margin-left: 260px; }
  .linear { transition-timing-function: linear; }
  .ease   { transition-timing-function: ease; }
  .ei     { transition-timing-function: ease-in; }
  .st     { transition-timing-function: steps(4, end); }
</style>
```

> **보이는 것** — 상자 안에 마우스를 올리면 막대 넷이 **동시에 출발해 2초 뒤 같은 자리에 도착**한다. 가는 모습이 다르다: `linear` 는 처음부터 끝까지 같은 속도, `ease` 는 빨리 출발해 천천히 도착, `ease-in` 은 거의 멈춘 듯 출발해 뒤로 갈수록 빨라지고, `steps(4, end)` 는 **네 번 뚝뚝 끊어져 점프**한다(출발 직후 0.5초 동안은 아예 안 움직인다).\
> **바꿔 볼 것** — `ease-in` → `ease-out`(반대 리듬) · `steps(4, end)` → `steps(4, start)`(출발하자마자 첫 계단을 밟는다) · `linear` → `linear(0, 0.6 40%, 1)`(꺾인 직선 — `linear()` 는 Baseline widely)

*(Chrome 151 headless 실측 — 마우스를 올린 뒤 시각별 `margin-left`(목표 260px):)*

| 시각 | `linear` | `ease` | `ease-in` | `steps(4, end)` |
|---|---|---|---|---|
| 50ms | 6.5px | 3.4px | 0.3px | **0px** |
| 500ms (25%) | 65.0px | 106.2px | 24.3px | 65px |
| 1000ms (50%) | 130.0px | 208.6px | 82.0px | 130px |
| 1500ms (75%) | 195.0px | 249.7px | 161.7px | 195px |
| 2300ms | 260px | 260px | 260px | 260px |

그림 해설 (한 단계씩):

- **넷 다 같은 2초에 같은 곳에 도착한다.** 다른 것은 **가는 도중의 위치**뿐이다.
- 절반 시점(1000ms)에 `ease` 는 **80% 를 왔고** `ease-in` 은 **32% 밖에 못 왔다.** 같은 duration 인데 체감 속도가 완전히 다르다.
- `steps(4, end)` 는 `linear` 와 **샘플 시각에서 우연히 같은 값**이 나왔다(500·1000·1500ms 가 마침 계단 경계다). 그 사이 시각에서는 다르다 — 50ms 에서 `linear` 는 6.5px, `steps` 는 **아직 0px** 다.

```text
0 ────────────────────────────────> 2s

linear   ────────────────────────   일정한 기울기
ease     ──╱‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾   빨리 오르고 완만하게 도착
ease-in  ___________╱────────────   느리게 시작해 가속
steps(4) ▁▁▁▁▄▄▄▄▆▆▆▆████████████   네 칸 계단
```

| 키워드 | 같은 뜻 | 쓰는 자리 |
|---|---|---|
| `linear` | `cubic-bezier(0, 0, 1, 1)` | 등속. 로딩 바·회전 |
| `ease` (기본값) | `cubic-bezier(.25, .1, .25, 1)` | 아무것도 안 정했을 때 |
| `ease-in` | `cubic-bezier(.42, 0, 1, 1)` | **나가는** 동작(화면 밖으로) |
| `ease-out` | `cubic-bezier(0, 0, .58, 1)` | **들어오는** 동작(사용자 입력에 대한 반응) |
| `ease-in-out` | `cubic-bezier(.42, 0, .58, 1)` | 제자리로 돌아오는 왕복 |
| `steps(n, 위치)` | — | 스프라이트·타이핑 효과·눈금 이동 |
| `linear(...)` | — | 꺾인 직선으로 복잡한 곡선 근사(튕김 등) |

*(위 표의 `cubic-bezier` 대응값은 [CSS Easing Functions Level 1](https://drafts.csswg.org/css-easing-1/) 의 키워드 정의다. 이 문서에서 네 키워드 전부를 따로 돌려 좌표까지 대조하지는 않았다 — 실측한 것은 `linear`·`ease`·`ease-in`·`steps(4, end)` 넷이다.)*

- **`ease-out` 을 기본으로 쓰라**는 조언이 흔한 이유: 사용자가 클릭한 뒤의 반응은 **즉시 시작해 부드럽게 멎는** 편이 빠르게 느껴진다.

### (5) `delay` 와 `duration` — 단축에서 순서로 갈린다

**언제 쓰나** — 툴팁처럼 "잠깐 기다렸다가" 나타나야 할 때.

```html demo
<div class="box">hover</div>
<style>
  .box { width: 100px; height: 80px; font: 14px/80px system-ui; text-align: center;
         background-color: #94a3b8;
         transition: background-color 0.2s linear 1s; }   /* 앞이 지속, 뒤가 지연 */
  .box:hover { background-color: #b91c1c; }
</style>
```

> **보이는 것** — 마우스를 올리면 **1초 동안 아무 일도 일어나지 않다가**, 그 뒤 0.2초에 걸쳐 회색에서 빨강으로 바뀐다. 두 시간 값 중 **앞이 `duration`, 뒤가 `delay`** 다.\
> **바꿔 볼 것** — `0.2s linear 1s` → `1s linear 0.2s` → 거의 바로 시작해 1초에 걸쳐 천천히 바뀐다 · 지연을 `-0.1s`(음수)로 → 전환이 **중간부터 시작한 것처럼** 튀어나온다

*(Chrome 151 headless 실측 — 마우스를 올린 뒤 시각별 `background-color`:)*

```text
  t=30ms    rgb(148, 163, 184)    출발색 그대로
  t=500ms   rgb(148, 163, 184)    아직 지연 구간
  t=900ms   rgb(148, 163, 184)    아직 지연 구간
  t=1150ms  rgb(176,  62,  67)    지연이 끝나고 움직이는 중
  t=1400ms  rgb(185,  28,  28)    도착 (#b91c1c)
```

명세가 단축의 순서를 이렇게 정한다.

> In the transition shorthand, the first time value is duration; the second time value is delay.

- 시간 값이 **하나뿐이면 무조건 `duration`** 이다. `transition: color 1s` 에는 지연이 없다.
- **음수 지연**은 "이미 그만큼 진행된 상태에서 시작"이다. 전환이 중간부터 튀어나온다.

### (6) 도중에 되돌리면 — 남은 만큼만 되돌아온다

**언제 쓰나** — 마우스가 요소 위를 스쳐 지나갈 때의 느낌을 설명해야 할 때.

명세에는 **되돌리기를 빠르게 하는 규칙**이 따로 있다(`reversing shortening factor`).

```text
2초짜리 전환, 0.6초(30%) 지점에서 마우스를 뗌

  순진한 모델                          실제 (명세)
  +-----------------------------+      +-----------------------------+
  | 현재 위치에서 출발해         |      | 현재 위치에서 출발해         |
  | 다시 2초를 쓴다             |      | 2초 x 30% = 0.6초만 쓴다     |
  |                             |      |                             |
  | -> 살짝 스쳤는데 되돌아오는  |      | -> 간 만큼만 되돌아온다      |
  |    데 2초가 걸린다          |      |                             |
  +-----------------------------+      +-----------------------------+
```

*(Chrome 151 headless 실측 — `transition: margin-left 2s linear`, 목표 200px, 기본 마진 6px:)*

```text
  마우스 올림 후 600ms   margin-left = 65.8px      (30% 지점)
  마우스 뗀 뒤  50ms     margin-left = 62.6px
                300ms    margin-left = 38.3px
                700ms    margin-left =  6px        <- 이미 원위치
```

- 되돌아오는 데 **약 600ms** 가 걸렸다 — 갈 때 쓴 시간과 같다. 2초가 아니다.
- 이 규칙이 없으면 목록 위를 마우스로 훑을 때 **뒤늦게 되돌아오는 잔상**이 길게 남는다.

비용 — 없다. 브라우저가 알아서 한다. 다만 **"되돌아오는 시간 = duration"이라고 가정한 JS 타이머는 어긋난다.**

### (7) 전환 값은 캐스케이드에서 가장 세다

**언제 쓰나** — "전환 중에 왜 내 `!important` 가 안 먹지"를 볼 때.

```text
캐스케이드 1단계 사다리 (일부)

  1. 전환(transition) 선언          <- 전환이 도는 동안의 값
  2. user-agent !important
  3. 사용자 !important
  4. 작성자 !important
  ...
```

- 전환이 도는 동안의 값은 **스타일시트의 선언이 아니라 엔진이 시간에 따라 만들어 내는 값**이라 사다리 맨 위에 있다.
- 그래서 전환 중에는 `!important` 로도 그 값을 덮지 못한다. 정본은 [01번 주제](../01-cascade-and-priority/2-summary.md).
- *(이 항목은 실행 확인하지 않았다 — 명세 기술만 옮겼다.)*

### (8) discrete 속성을 전환에 태우기 — `transition-behavior`

**언제 쓰나** — `display: none` 으로 숨기는 요소를 부드럽게 사라지게 하고 싶을 때.

```css
.disc { opacity: 1; transition: opacity 1s linear, display 1s allow-discrete; }
.disc.gone { opacity: 0; display: none; }
```

*(Chrome 151 headless 실측 — `.gone` 클래스를 붙인 뒤:)*

```text
  t=50ms    display: block   opacity: 0.95
  t=500ms   display: block   opacity: 0.50     <- 절반 지점에도 아직 block
  t=900ms   display: block   opacity: 0.10
  t=1300ms  display: none    opacity: 0        <- 끝나고 나서야 none
```

- `allow-discrete` 를 주면 `display` 가 **전환이 끝날 때까지 `block` 으로 버텨 준다.**\
  그래서 `opacity` 가 다 사라진 뒤에 상자가 없어진다.
- 반대 방향(없던 요소가 나타날 때)은 **`@starting-style`** 이 필요하다 — 시작값이 없으면 전환이 걸리지 않기 때문이다. 정본은 목록의 **57번 주제**.
- **둘 다 Baseline newly**(2024-08-06)다 — widely 가 아니므로 쓸 때 대체 경로를 생각한다.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 묻는 것 하나만 남겼다.

### 단축과 롱핸드

```css
/* 단축 — 순서는 자유롭지만 시간 값은 앞이 duration, 뒤가 delay */
transition: background-color 0.3s ease-out 0.1s;

/* 같은 뜻의 롱핸드 */
transition-property:        background-color;
transition-duration:        0.3s;
transition-timing-function:  ease-out;
transition-delay:           0.1s;

/* 여러 속성 — 쉼표로 나열 */
transition: opacity 0.2s linear, transform 0.4s ease-out 0.1s;
```

- **속성 이름과 시간 값의 위치는 자유**지만, **시간 값끼리는 순서가 의미를 갖는다.**
- 롱핸드를 쉼표 목록으로 쓰면 자리 수가 안 맞을 때 **앞에서부터 반복**된다 — 읽기 어려워지므로 단축 쪽을 권한다.

### ★ 단축은 안 적은 롱핸드를 초기값으로 되돌린다

```css
.lane i { transition: margin-left 2s; }      /* timing-function 을 ease 로 되돌린다 */
.linear { transition-timing-function: linear; }   /* (0,1,0) — 위 규칙 (0,1,1) 에 진다 */
```

- 위 조합은 **`linear` 가 안 먹는다.** 단축이 `transition-timing-function: ease` 를 함께 선언하는데, 그 규칙의 명시도가 더 높기 때문이다.
- 이 문서의 (4) demo 를 처음 쓸 때 실제로 이 함정에 걸렸고, **네 막대가 전부 `ease` 로 똑같이 움직이는 것을 측정에서 잡았다.**\
  그래서 demo 는 단축 대신 `transition-property` + `transition-duration` 롱핸드로 고쳤다.
- 단축 속성이 안 적은 하위 속성을 초기값으로 되돌리는 규칙은 [01번 주제](../01-cascade-and-priority/2-summary.md)의 「어디서 틀리나 5」와 같은 것이다.

### `transition-property` 의 값

```css
transition-property: all;                     /* 기본값 — 바뀌는 모든 속성 */
transition-property: none;                    /* 아무것도 전환하지 않는다 */
transition-property: opacity, transform;      /* 지정한 것만 */
```

- `all` 은 편하지만 **레이아웃 속성이 섞여 들어오면 비싸고**, 무엇이 전환되는지 코드만 봐서는 알 수 없다.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 여섯 다 **에러도 경고도 없이 조용하다.**

### 1. `transition` 을 `:hover` 안에만 쓴다

```css
.btn:hover { background-color: red; transition: background-color 1s linear; }   /* 한쪽만 */
```

```text
   마우스를 올릴 때                   마우스를 뗄 때
   +---------------------------+     +---------------------------+
   | :hover 규칙이 적용된다     |     | :hover 규칙이 사라진다     |
   | -> transition 도 있다      |     | -> transition 도 사라진다  |
   | -> 1초에 걸쳐 바뀐다       |     | -> 순간이동                |
   +---------------------------+     +---------------------------+
```

*(Chrome 151 headless 실측: 올릴 때는 500ms 에 `rgb(166, 96, 106)`(중간값)이었고, 뗄 때는 **50ms 에 이미** 원래 색 `rgb(148, 163, 184)` 이었다.)*

- 처방: `transition` 은 **기본 상태 규칙에** 쓴다. 들어올 때와 나갈 때 시간을 다르게 하고 싶을 때만 양쪽에 쓴다.

### 2. `height: auto` 를 전환하려 한다

(2)의 demo 가 그것이다. **에러 없이 순간이동한다.**\
대안: 높이를 아는 경우 고정 px, 모르면 `grid-template-rows: 0fr ↔ 1fr`(목록의 27번)이나 `transform: scaleY()`.

### 3. `transition-duration` 을 빼먹는다

```css
transition: background-color ease;    /* duration 기본값 0s -> 아무 일도 안 난다 */
```

선언은 유효하고 계산값도 남는다. **시간이 0 이라 전환이 눈에 안 보일 뿐이다.**

### 4. 단축이 타이밍 함수를 되돌린다

위 「문법」 절의 ★ 항목이다. 이 문서를 만들며 실제로 걸린 함정이고, **화면만 봐서는 "넷이 비슷해 보인다"로 넘어가기 쉽다.**\
값을 재 보고서야 넷이 전부 `ease` 였음을 알았다.

### 5. 나타나는 요소에 전환이 안 걸린다

`display: none` 이던 요소를 `block` 으로 만들면, **그 요소에는 "바뀌기 전 값"이 없다.**\
전환이 걸리려면 시작값이 있어야 하므로 `@starting-style` 이 필요하다(목록의 57번). Baseline **newly**.

### 6. 비싼 속성을 전환한다

```text
transform · opacity        -> 합성 단계만 다시 돈다        (싸다)
width · height · margin    -> 레이아웃부터 전부 다시 돈다   (비싸다)
box-shadow · filter        -> 페인트부터                   (중간)
```

"동작은 하는데 끊긴다"의 원인이 대개 이것이다. 어느 속성이 어느 단계를 다시 돌리는지는 목록의 **56번 주제**가 정본이다.

### 7. 모션 접근성을 잊는다

전정기관에 문제가 있는 사용자에게는 큰 움직임이 실제 증상을 일으킨다.\
`@media (prefers-reduced-motion: reduce)` 에서 **끄는 게 아니라 바꾼다**(이동을 페이드로). 정본은 목록의 **60번 주제**.

## 언제 쓰고 언제 안 쓰나

| 상황 | `transition` | 다른 것 |
|---|---|---|
| 상태 두 개 사이의 왕복(`:hover`·`:focus`·클래스 토글) | **쓴다** | |
| 중간 지점이 여럿인 움직임(0% → 50% → 100%) | 못 한다 | `@keyframes` (목록 53번) |
| 반복·무한 재생 | 못 한다 | `@keyframes` + `animation-iteration-count` |
| 요소가 나타나거나 사라지는 순간 | 그대로는 안 된다 | `@starting-style`·`allow-discrete` (57번) |
| 스크롤 진행에 맞춘 움직임 | 못 한다 | `animation-timeline` (58번) |
| 페이지 전체가 바뀌는 연출 | 못 한다 | 뷰 전환 (59번) |

판단 규칙 두 줄.

- **상태 A ↔ 상태 B 면 `transition`, 그 사이에 들를 곳이 있으면 `@keyframes`.**
- **`transform`·`opacity` 로 표현할 수 있으면 그쪽으로 옮긴다.** 같은 움직임이 훨씬 싸다.

## 핵심 문장

- 전환은 **계산값이 바뀔 때** 브라우저가 거는 것이고, 그러려면 **바뀌기 전 상태에 `transition` 이 이미 있어야 한다.**
- **보간할 수 없는 값은 전환이 시작조차 하지 않는다** — `auto`·`none` 이 대표다. 에러도 경고도 없다.
- 단축의 시간 값 둘 중 **앞이 `duration`, 뒤가 `delay`** 다. 하나뿐이면 `duration`.
- 타이밍 함수는 **도착 시각이 아니라 가는 도중의 위치**를 바꾼다 — 절반 시점에 `ease` 는 80%, `ease-in` 은 32% 를 간다(실측).
- 도중에 되돌리면 **간 만큼의 시간만** 써서 돌아온다(reversing shortening factor).
- 전환 값은 캐스케이드 사다리 **맨 위**라 `!important` 로도 못 덮는다.
- **단축 `transition` 은 안 적은 롱핸드를 초기값으로 되돌린다** — 뒤에 쓴 `transition-timing-function` 이 명시도에서 지면 조용히 무시된다.

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 52번) · 「버전·지원 기준」의 Baseline 표
- [`../01-cascade-and-priority/2-summary.md`](../01-cascade-and-priority/2-summary.md) — 전환 선언이 캐스케이드 사다리 맨 위에 있는 이유 · 단축 속성이 하위 속성을 되돌리는 규칙
- 목록의 **04번 주제**(값 처리 단계) — 전환이 어느 값(계산값)을 보고 걸리는지의 정본
- 목록의 **53번 주제**(`@keyframes` 와 `animation`) — 중간 지점이 여럿이거나 반복이 필요할 때
- 목록의 **54번 주제**(`transform` 2D) — 전환에 태우기 가장 싼 속성
- 목록의 **56번 주제**(렌더링 파이프라인과 `will-change`) — **어떤 속성이 비싼가의 정본**
- 목록의 **57번 주제**(`@starting-style`) — 나타나는 요소를 전환에 태우는 법
- 목록의 **60번 주제**(`prefers-reduced-motion`) — 모션 접근성
- [`reference/render-rules.md`](../../../../../../reference/render-rules.md) — 이 문서의 `demo` 블록 규칙

## 용어 풀이

- **전환(transition)** — 계산값이 바뀔 때 브라우저가 두 값 사이를 시간에 걸쳐 채워 주는 기능.
- **보간(interpolation)** — 시작값과 끝값 사이의 중간값을 만드는 것. 이게 안 되면 전환이 시작되지 않는다.
- **계산값(computed value)** — 캐스케이드·상속이 끝난 뒤 확정된 값. 전환은 이 값의 변화를 본다.
- **discrete 타입** — 중간값 없이 툭 바뀌는 애니메이션 타입. `display`·`visibility`·`font-family`.
- **`transition-property`** — 무엇을 전환할지. 기본값 `all`.
- **`transition-duration`** — 얼마나 오래. **기본값 `0s`** — 빼먹으면 아무 일도 안 난다.
- **`transition-timing-function`** — 가는 리듬. 기본값 `ease`(등속이 아니다).
- **`transition-delay`** — 언제부터. 단축에서 **두 번째** 시간 값.
- **`cubic-bezier(x1, y1, x2, y2)`** — 제어점 둘로 정의하는 곡선. `ease` 계열 키워드가 전부 이것의 별명이다.
- **`steps(n, 위치)`** — n 칸 계단으로 끊어 가는 함수. `end` 는 각 칸의 끝에서, `start` 는 시작에서 값이 바뀐다.
- **`linear(...)`** — 꺾인 직선을 나열해 복잡한 곡선을 근사하는 함수. Baseline widely.
- **reversing shortening factor** — 도중에 되돌릴 때 **간 만큼의 시간만** 쓰게 하는 명세 규칙.
- **`transition-behavior: allow-discrete`** — discrete 타입 속성도 전환 목록에 태우는 값. Baseline newly(2024-08-06).
- **`@starting-style`** — 나타나는 요소의 "바뀌기 전 값"을 정해 주는 규칙. Baseline newly(2024-08-06).

---

## [Claude 추가] 더 알면 좋은 것

- 전환은 **선언적**이라 JS 타이머와 어긋나기 쉽다.\
  끝나는 시점이 필요하면 `transitionend` 이벤트를 듣는다 — 단, 전환이 **시작조차 안 한 경우**에는 이벤트도 안 오므로 타임아웃 대비가 필요하다.
- `transition: all` 과 CSS 변수(`--x`)를 같이 쓰면 주의할 것이 있다.\
  `@property` 로 타입을 등록하지 않은 변수는 discrete 로 취급되어 **보간되지 않는다**(목록의 37번).
- `steps()` 의 둘째 인자는 `jump-start`/`jump-end`/`jump-none`/`jump-both` 로도 쓸 수 있고, `start`/`end` 는 각각 `jump-start`/`jump-end` 의 옛 이름이다.
- 같은 속성에 전환과 `@keyframes` 애니메이션이 동시에 걸리면 **애니메이션이 이긴다**\
  (캐스케이드 사다리에서 애니메이션 선언이 작성자 normal 보다 위에 있고, 전환 선언은 그 위에 있다 — 두 선언이 동시에 살아 있는 경우의 우선은 목록의 53번이 정본이다).
- 전환 중인 요소의 값을 JS 로 읽으면 **그 순간의 중간값**이 나온다.\
  이 문서의 모든 실측값이 그렇게 얻은 것이다 — `getComputedStyle` 은 전환의 현재 값을 돌려준다.

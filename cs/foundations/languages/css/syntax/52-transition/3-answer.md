# css/syntax/52 — `transition`: 전환 가능한 속성·타이밍 함수·지연·`transition-behavior` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 시각별 값은 Google Chrome 151.0.7922.173 headless 에서 실제로 측정한 것**이다.\
> CDP 로 실제 마우스를 움직여 `:hover` 를 발생시킨 뒤, 벽시계 기준 시각마다 `getComputedStyle` 을 읽었다(샘플 시각은 ±10ms 오차).\
> 규칙은 [CSS Transitions Level 1](https://drafts.csswg.org/css-transitions-1/) · [Level 2](https://drafts.csswg.org/css-transitions-2/) · [CSS Easing Functions Level 1](https://drafts.csswg.org/css-easing-1/) 로 접지했다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 이 버튼은 어떻게 바뀌는가

**실행 결과** (Chrome 151 headless — `#e2e8f0` → `#1d4ed8`, `.6s ease`)

```text
  t=0        rgb(226, 232, 240)
  t=50ms     rgb(212, 221, 238)
  t=150ms    rgb(146, 169, 230)
  t=300ms    rgb( 68, 108, 221)
  t=450ms    rgb( 37,  84, 217)
  t=700ms    rgb( 29,  78, 216)   = #1d4ed8 (도착)
```

**몇 초 만에 다 바뀌는가**

- **0.6초.** 700ms 샘플에서 이미 최종값이었다.

**뗐을 때도 같은 시간인가**

- **같다** — 끝까지 다 간 뒤에 떼면 그렇다.
- 다만 **도중에 떼면 다르다**. 간 만큼의 시간만 쓴다(6번).

**0.3초 시점에 몇 퍼센트쯤**

- **약 80%** 다.

```text
  빨간 채널로 계산
     출발 226 · 도착 29 · 0.3초 시점 68
     (226 - 68) / (226 - 29) = 158 / 197 = 80.2%

  시간은 50%  ->  거리는 80%
```

**50%가 아닌 이유**

- **기본 타이밍 함수 `ease` 는 등속이 아니기 때문**이다. `cubic-bezier(.25, .1, .25, 1)` 로 정의돼 있어 **초반이 빠르고 후반이 느리다.**
- `transition: … .6s;` 처럼 타이밍 함수를 안 적으면 `ease` 가 들어간다.\
  등속을 원하면 `linear` 를 명시해야 한다.

> **타이밍 함수(timing function / easing function)** — 경과 시간 비율을 진행 비율로 바꾸는 함수.\
> 예: 시간이 50% 지났을 때 `linear` 는 50%, `ease` 는 약 80% 를 간 것으로 계산한다.

### 2. 두 상자 중 어느 쪽이 부드러운가

**실행 결과** (Chrome 151 headless — 시각별 `height`)

```text
            t=30ms     t=400ms    t=1300ms
  .fixed    24.8px     34px       48px       <- 1초에 걸쳐 선형으로 간다
  .auto     48px       48px       48px       <- 30ms 에 이미 끝나 있다
```

**어느 쪽이 1초에 걸쳐 펴지는가**

- **`.fixed`** (`height: 48px`). 400ms 에 34px — 24 + (48-24)×0.4 = 33.6 으로 선형과 맞는다.

**다른 쪽은**

- **`.auto` 는 전환 없이 즉시 48px 로 튄다.** 전환이 걸린 게 아니라 **시작조차 하지 않았다.**
- `auto` 는 "내용에 맞춰라"라는 지시이지 수가 아니라서 **중간값을 정의할 수 없다.**

```text
  24px ─────?───── auto          24px ─────30px───── 48px
       중간값이 없다                   중간값이 있다
       -> 전환 시작 안 함              -> 전환 걸림
```

명세의 조건은 이렇다.

> property values are transitionable if they have an animation type that is neither not animatable nor discrete.

**에러나 경고가 찍히는가**

- **아무것도 안 찍힌다.** 선언은 문법상 유효하고 계산값도 정상이다.
- 그래서 "왜 내 CSS 만 안 되지"로 시간을 쓰게 된다 — **조용한 실패**다.

**내용 높이를 모르는 채로 펼치려면**

- **`grid-template-rows: 0fr` ↔ `1fr`** 을 전환한다(자식에 `overflow: hidden`).\
  `fr` 는 수라서 보간된다.
- *(Chrome 151 headless 실측: `grid-template-rows` 계산값이 `0px` → 500ms 에 `11.8px` → 1300ms 에 `48px` 로, 자식 높이가 0 → 12 → 48 로 따라 움직였다.)*
- 다른 수단: 높이를 아는 경우 고정 px · `transform: scaleY()`(내용도 같이 찌그러진다) · `max-height` 를 큰 값으로(앞부분이 비어 보인다).

### 3. 왜 들어갈 때만 부드러운가

**실행 결과** (Chrome 151 headless — `transition` 이 `:hover` 규칙에만 있는 경우)

```text
  올릴 때   t=50ms   rgb(150, 156, 176)    움직이는 중
            t=500ms  rgb(166,  96, 106)    중간값
            t=1100ms rgb(185,  28,  28)    도착
  뗄 때     t=50ms   rgb(148, 163, 184)    이미 원래 색
            t=500ms  rgb(148, 163, 184)
```

**올릴 때 전환이 걸리는가**

- **걸린다.** `:hover` 규칙이 적용되면서 `transition` 선언도 같이 적용되기 때문이다.

**뗄 때는**

- **순간이동한다.** 50ms 만에 이미 원래 색이었다.

```text
   마우스를 올릴 때                   마우스를 뗄 때
   +---------------------------+     +---------------------------+
   | :hover 규칙 적용           |     | :hover 규칙이 사라진다     |
   |  -> transition 도 적용     |     |  -> transition 도 사라진다 |
   |  -> 1초에 걸쳐 바뀐다      |     |  -> 전환할 규칙이 없다     |
   +---------------------------+     +---------------------------+
```

- 전환은 **값이 바뀌는 그 순간 요소에 `transition` 이 있어야** 걸린다.\
  뗄 때는 `transition` 선언 자체가 사라지므로 걸릴 게 없다.

**어느 규칙에 써야 양방향이 되는가**

- **기본 상태 규칙**에 쓴다.

```css
.btn { background-color: #94a3b8; transition: background-color 1s linear; }
.btn:hover { background-color: red; }
```

**들어올 때와 나갈 때 시간을 다르게 하려면**

- **양쪽에 다르게 쓴다.**

```css
.btn       { transition: background-color .4s ease-out; }  /* 나갈 때 */
.btn:hover { transition: background-color .15s ease-out; } /* 들어올 때 */
```

- 이것이 `:hover` 안에 `transition` 을 쓰는 **유일한 정당한 용법**이다.

### 4. 이 상자는 언제부터 언제까지 움직이는가

**실행 결과** (Chrome 151 headless — `transition: background-color 0.2s linear 1s`)

```text
  t=30ms    rgb(148, 163, 184)   출발색 그대로
  t=500ms   rgb(148, 163, 184)   아직 지연 구간
  t=900ms   rgb(148, 163, 184)   아직 지연 구간
  t=1150ms  rgb(176,  62,  67)   움직이는 중
  t=1400ms  rgb(185,  28,  28)   도착 (#b91c1c)
```

**0.5초 시점의 색**

- **출발색 그대로**(`#94a3b8`). 아직 지연 구간이다.

**시작·끝 시각**

- 시작 **1.0초**, 끝 **1.2초**.

```text
   0 ──────────── 1.0s ── 1.2s
     |<- delay ->|<-dur->|
        아무 일 없음   0.2초에 걸쳐 바뀐다
```

**어느 쪽이 지속이고 어느 쪽이 지연인가**

- **앞이 `duration`(0.2s), 뒤가 `delay`(1s)** 다.

명세의 규정.

> In the transition shorthand, the first time value is duration; the second time value is delay.

**시간 값을 하나만 쓰면**

- **`duration`** 이다. `transition: background-color 1s` 에는 지연이 없다(기본 `0s`).

**지연에 음수를 주면**

- **이미 그만큼 진행된 상태에서 시작한다.**
- *(Chrome 151 headless 실측: `transition: background-color 1s linear -0.5s` 에서 마우스를 올린 지 30ms 만에 색이 `rgb(168, 91, 101)` — 출발색과 도착색의 거의 중간 — 이었고, 600ms 에 도착했다. 총 이동 시간이 0.5초로 줄었다.)*
- 로딩 인디케이터의 여러 점을 **엇갈리게** 움직일 때 음수 지연을 쓴다.

### 5. 1초 시점에 넷은 어디에 있는가

**실행 결과** (Chrome 151 headless — 2초 동안 `margin-left` 0 → 260px)

| 시각 | `linear` | `ease` | `ease-in` | `steps(4, end)` |
|---|---|---|---|---|
| 50ms | 6.5px | 3.4px | 0.3px | **0px** |
| 500ms (25%) | 65.0px | 106.2px | 24.3px | 65px |
| 1000ms (50%) | 130.0px | **208.6px** | **82.0px** | 130px |
| 1500ms (75%) | 195.0px | 249.7px | 161.7px | 195px |
| 2300ms | 260px | 260px | 260px | 260px |

**2초 뒤 넷의 위치**

- **같다.** 넷 다 260px 에 도착한다. 타이밍 함수는 **도착 시각도 도착 지점도 바꾸지 않는다.**

**1초 시점의 최선두와 최후미**

- 가장 앞 — **`ease`** (208.6px, 80.2%)
- 가장 뒤 — **`ease-in`** (82.0px, 31.5%)
- `linear` 와 `steps(4, end)` 는 둘 다 130px 로 **우연히 같다** — 1000ms 가 마침 계단 경계라서다.\
  50ms 에서는 갈린다(6.5px 대 0px).

**50ms 시점의 `steps(4, end)`**

- **0px.** 아직 움직이지 않았다.
- `end`(= `jump-end`)는 **각 칸의 끝에서** 값이 바뀌므로 첫 0.5초 동안은 출발점에 머문다.

**`steps(4, start)` 로 바꾸면**

- **50ms 에 이미 65px** 다.
- *(Chrome 151 headless 실측: `steps(4, start)` 는 50ms→65px · 500ms→130px · 1000ms→195px · 1500ms→260px. `end` 판보다 정확히 한 칸씩 앞서 있다.)*

```text
  steps(4, end)                    steps(4, start)
  ▁▁▁▁▁▄▄▄▄▄▆▆▆▆▆████             ▄▄▄▄▄▆▆▆▆▆█████████
  출발 직후 0.5초는 제자리          출발하자마자 첫 칸을 밟는다
```

**시각을 바꾸는가, 위치를 바꾸는가**

- **도중의 위치만** 바꾼다. 출발 시각·도착 시각·도착 지점은 `duration`·`delay` 가 정한다.

### 6. 도중에 마우스를 떼면

**실행 결과** (Chrome 151 headless — `transition: margin-left 2s linear`, 기본 마진 6px, 목표 200px)

```text
  올린 뒤 600ms        margin-left = 65.8px    (30% 지점)
  뗀 뒤   50ms         margin-left = 62.6px
          300ms        margin-left = 38.3px
          700ms        margin-left =  6px      <- 이미 원위치
```

**몇 초가 걸리는가**

- **약 0.6초.** 2초가 아니다.

```text
   순진한 모델                          실제 (명세)
   +-----------------------------+     +-----------------------------+
   | 현재 위치 -> 원위치          |     | 현재 위치 -> 원위치          |
   | 다시 2초를 쓴다              |     | 2초 x 30% = 0.6초를 쓴다     |
   +-----------------------------+     +-----------------------------+
```

**명세의 어떤 규칙인가**

- **reversing shortening factor**(되돌리기 단축 계수)다.\
  진행 중인 전환이 반대로 뒤집히면, 새 전환의 duration 에 **그 계수를 곱해** 줄인다.
- 명세가 계수를 이렇게 정의한다.

> the absolute value, clamped to the range [0, 1], of the sum of: (1) the output of the timing function of the old transition at the time of the style change event, times the reversing shortening factor of the old transition, (2) 1 minus the reversing shortening factor of the old transition.

- 실측이 이것과 맞는다 — 30% 지점에서 뒤집었더니 2초 × 0.3 = 0.6초가 걸렸다.

**이 규칙이 없으면**

- 목록 위를 마우스로 빠르게 훑으면, **스쳐 지나간 항목마다 전체 duration 을 들여 되돌아오는 잔상**이 길게 남는다.
- 실제로 마우스가 이미 떠난 뒤에도 몇 초 동안 색이 남아 있게 된다.

**JS 타이머를 `duration` 으로 잡으면**

- **되돌아오는 경우에 먼저 끝난다.** 타이머는 2초를 기다리는데 전환은 0.6초에 끝난다.
- 그사이 사용자가 또 방향을 바꾸면 타이머가 겹쳐 상태가 어긋난다.
- 처방: 시간이 아니라 **`transitionend` 이벤트**를 듣는다. 단, **전환이 시작조차 안 한 경우에는 이벤트도 안 오므로** 타임아웃 대비가 필요하다.

### 7. 이 네 막대는 왜 똑같이 움직이는가

**실행 결과** (Chrome 151 headless — 문제가 있던 판)

```text
  t=  50ms  linear 2.09px   ease 2.09px   ei 2.09px   st 2.09px
  t= 500ms  linear 106.2px  ease 106.2px  ei 106.2px  st 106.2px
  t=1000ms  linear 210.7px  ease 210.7px  ei 210.7px  st 210.7px
                    ^ 넷이 한 값. 전부 ease 로 움직였다
```

**`.linear` 막대는 등속으로 움직이는가**

- **아니다.** 넷 다 `ease` 로 움직였다. 500ms(25%)에 106.2px = 40.9% 는 `ease` 의 값이다.

**무엇이 덮었는가**

- **단축 `transition: margin-left 2s` 가 `transition-timing-function: ease` 를 함께 선언한다.**\
  단축은 안 적은 하위 속성을 **초기값으로 되돌린다.**

**두 규칙의 명시도**

```text
  .lane i   { transition: margin-left 2s; }          (0, 1, 1)   <- 이긴다
  .linear   { transition-timing-function: linear; }  (0, 1, 0)

  transition-timing-function 바구니에서
  (0,1,1) 의 ease 가 (0,1,0) 의 linear 를 이긴다
```

- 명시도 계산은 [02번 주제](../02-specificity/2-summary.md), 단축이 하위 속성을 되돌리는 규칙은 [01번 주제](../01-cascade-and-priority/2-summary.md)가 정본이다.

**화면만 보고 알아챌 수 있는가**

- **어렵다.** 넷이 "비슷하게" 움직이는 것으로 보이고, 에러도 경고도 없다.
- **값을 재야 안다.** 이 문서를 만들면서 실제로 이 함정에 걸렸고, 시각별 `margin-left` 를 샘플링해서야 넷이 한 값인 것을 발견했다.
- 개발자 도구에서 `.linear` 의 `transition-timing-function` 선언에 **줄이 그어져 있는 것**으로도 확인할 수 있다.

**고치는 방법 두 가지**

1. **단축을 쓰지 않는다** — `transition-property`·`transition-duration` 롱핸드만 쓰면 타이밍 함수 자리는 비어 있고, 뒤의 클래스 규칙이 채운다.
2. **명시도를 맞추거나 올린다** — `.lane .linear` 나 `.lane i.linear` 로 쓰면 이긴다.

- 이 문서의 demo 는 1번을 택했다. **원인을 없애는 쪽**이라 나중에 읽는 사람이 명시도를 계산하지 않아도 된다.

### 8. 다른 주제와 잇기

**들르는 지점이 있는 움직임**

- **`@keyframes` + `animation`** 이다. `transition` 은 **상태 A ↔ B 두 점**만 안다.
- 반복·무한 재생·역방향 재생도 `animation` 쪽이다. 정본은 목록의 **53번 주제**.

**`display: none` 이던 요소가 나타날 때**

- 그 요소에는 **"바뀌기 전 값"이 없다.** 전환은 두 값 사이를 채우는 것이라 시작값이 없으면 걸리지 않는다.
- **`@starting-style`** 이 그 시작값을 지정해 준다. 사라질 때는 **`transition-behavior: allow-discrete`** 가 `display` 를 전환이 끝날 때까지 붙들어 준다.
- *(Chrome 151 headless 실측: `transition: opacity 1s linear, display 1s allow-discrete` 를 준 요소에 `display: none`·`opacity: 0` 을 적용하니 `display` 가 t=500ms 에도 여전히 `block` 이었고, t=1300ms 에 `none` 으로 바뀌었다. `opacity` 는 그동안 1 → 0.5 → 0.1 → 0 으로 내려갔다.)*
- 둘 다 Baseline **newly**(2024-08-06) — 정본은 목록의 **57번 주제**.

**전환 값을 `!important` 로 덮을 수 있는가**

- **없다.** 캐스케이드 1단계 사다리에서 **전환 선언이 맨 위**이고 작성자 `!important` 는 그 아래다.
- 이유: 전환 중의 값은 스타일시트의 선언이 아니라 **엔진이 시간에 따라 만들어 내는 값**이다. 시트가 덮을 수 있으면 전환 도중에 값이 튄다.
- 정본은 [01번 주제](../01-cascade-and-priority/2-summary.md). *(이 항목은 실행 확인하지 않았다 — 명세 기술만 옮겼다.)*

**`width` 대 `transform: scaleX()`**

```text
  width 를 전환                      transform 을 전환
  +----------------------------+     +----------------------------+
  | 매 프레임                  |     | 매 프레임                  |
  | 레이아웃 -> 페인트 -> 합성  |     | 합성만                     |
  | 형제·자식 배치가 다시 계산 |     | 그린 결과를 옮겨 놓는다    |
  +----------------------------+     +----------------------------+
   결과는 정확하지만 비싸다          싸지만 내용도 같이 늘어난다
```

- 어느 속성이 어느 단계를 다시 돌리는지는 목록의 **56번 주제**가 정본이다.

**모션 접근성에서 "끄는 것"이 최선이 아닌 이유**

- 전환을 통째로 없애면 **상태가 바뀐 것을 알아채지 못하는** 사용자가 생긴다. 움직임은 피드백이기도 하다.
- 그래서 `@media (prefers-reduced-motion: reduce)` 에서는 **끄는 게 아니라 바꾼다** — 큰 이동·확대·회전을 짧은 페이드로 대체한다.
- 정본은 목록의 **60번 주제**.

## 용어 풀이

- **전환(transition)** — 계산값이 바뀔 때 브라우저가 두 값 사이를 시간에 걸쳐 채워 주는 기능.
- **보간(interpolation)** — 시작값과 끝값 사이의 중간값을 만드는 것.
- **타이밍 함수** — 경과 시간 비율을 진행 비율로 바꾸는 함수. 도착 시각이 아니라 도중 위치를 바꾼다.
- **`ease`** — 기본 타이밍 함수. `cubic-bezier(.25, .1, .25, 1)` — 등속이 아니다.
- **`steps(n, end/start)`** — n 칸 계단. `end` 는 칸의 끝에서, `start` 는 칸의 시작에서 값이 바뀐다.
- **`duration` / `delay`** — 걸리는 시간 / 시작 전 기다리는 시간. 단축에서 **앞이 duration**.
- **음수 지연** — 이미 그만큼 진행된 상태에서 시작한다. 총 이동 시간이 그만큼 줄어든다.
- **reversing shortening factor** — 도중에 되돌릴 때 duration 을 진행률만큼 줄이는 명세 규칙.
- **discrete 타입** — 중간값 없이 툭 바뀌는 애니메이션 타입(`display`·`visibility`).
- **`transition-behavior: allow-discrete`** — discrete 속성도 전환 목록에 태우는 값. Baseline newly.
- **`@starting-style`** — 나타나는 요소의 시작값을 지정하는 규칙. Baseline newly.
- **`transitionend`** — 전환이 끝났을 때 나는 이벤트. **전환이 시작 안 하면 나지 않는다.**

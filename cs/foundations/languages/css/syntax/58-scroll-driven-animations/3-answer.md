# css/syntax/58 — 스크롤 연동 애니메이션: `animation-timeline`·`scroll()`/`view()`·`timeline-scope` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 수치는 Google Chrome 151.0.7922.173 headless 에서 실제로 스크롤을 움직여 측정한 것**이다.\
> `--virtual-time-budget` 은 쓰지 않았다. CDP 에 붙어 매 판 `Page.navigate` 로 다시 띄우고, 스크롤을 옮긴 뒤 **두 프레임을 기다렸다가** `getComputedStyle` 을 읽었다.\
> 규칙은 [Scroll-driven Animations Level 1](https://drafts.csswg.org/scroll-animations-1/) 로 접지했다.
> ⚠️ **이 기능은 Baseline `limited` 이고 Firefox 에 구현이 없다.** 아래 값은 전부 **Chrome 에서 그렇다**는 뜻이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 세 막대는 다르게 움직이는가

**출력** (Chrome 151 headless — 문서 3000 · 뷰포트 900×357 · 최대 스크롤 2643)

```text
  scrollY     duration:auto   duration:1s    duration:100s
        0          0px            0px             0px
      250     85.125px       85.125px        85.125px
      625    212.812px      212.812px       212.812px
     1250    425.641px      425.641px       425.641px
     1875    638.469px      638.469px       638.469px
     2500    851.297px      851.297px       851.297px
```

**`scrollY = 250` 에서의 폭**

- **셋 다 85.125px** 이다. 소수점까지 같다.

**무엇으로 계산된 값인가**

```text
  스크롤 비율   250 / 2643 = 9.459%
  키프레임 끝   width: 100% = 900px  (뷰포트 폭)
  결과          900 × 9.459% = 85.13px
```

- **순전히 스크롤 비율**이다. 시간이 끼어드는 자리가 없다.

**`currentTime` 의 단위**

```text
  a.constructor.name                       CSSAnimation
  a.timeline.constructor.name              ScrollTimeline
  a.currentTime                            "0%"        ★ 밀리초가 아니다
  a.effect.getComputedTiming().duration    "100%"      ★ auto 가 100% 로 계산된다
```

- **`%`** 다. 시간 기반이면 `0ms` 라고 나올 자리다.

**속도를 바꾸려면**

- `@keyframes` 의 **값**을 바꾸거나, `animation-range` 로 **구간을 좁힌다**(더 들어가면).\
  `animation-duration` 은 손댈 곳이 아니다.

### 2. 안 움직이는 네 가지는 서로 다른가

**출력**

```text
  경우                                  timeline 객체   currentTime  playState   width
  t2  scroll(root inline)               ScrollTimeline  null         running     40px
  t7  scroll(self block)                ScrollTimeline  null         running     40px
  t3  animation-timeline: none          null            0            finished    200px
  t6  animation-timeline: --nope        null            0            finished    200px
```

**40px 과 200px**

- **40px = t2·t7**(기본 스타일). **200px = t3·t6**(마지막 키프레임).

**끝 상태로 박히는 이유**

```text
  타임라인이 없다
        ↓
  애니메이션이 진행할 축이 없어 곧장 playState = "finished"
        ↓
  animation-fill-mode: both/forwards 가 '끝난 뒤 값'을 칠한다
        ↓
  마지막 키프레임(200px)이 화면에 박힌다
```

**두 무리가 갈리는 지점**

- **`timeline` 이 `null` 이냐**(모양 ②) **`currentTime` 이 `null` 이냐**(모양 ①)다.
- 모양 ① 은 「시계는 달렸는데 바늘이 안 읽힌다」 → 애니메이션이 **적용되지 않고** 기본 스타일이 보인다.
- 모양 ② 는 「시계 자체가 없다」 → **끝난 것으로 취급**되고 fill 이 칠한다.

**`fill-mode: none` 으로 바꾸면**

```text
  animation-timeline: none 일 때
    fill none       width=40px    (getAnimations() 에 객체조차 없다)
    fill forwards   width=200px
    fill backwards  width=40px    (객체 없음)
    fill both       width=200px
```

- **모양 ② 는 사라진다.** 끝 상태로 박히는 현상은 `forwards`/`both` 와 짝일 때만 난다.
- 모양 ① 은 `fill-mode` 와 무관하게 언제나 기본 스타일이다.

### 3. `view()` 의 0% 는 어느 스크롤 위치인가

**출력** (스크롤포트 300 · 요소 높이 100 · 요소 위치 600)

```text
  scrollTop     진행률       opacity
          0     -75%         0
        250     -12.5%       0
        300       0%         0
        350      12.5%       0.125
        500      50%         0.5
        650      87.5%       0.875
        700     100%         1
       1000     175%         1
```

**0% 와 100% 의 `scrollTop`**

- **0% = 300**(요소 위쪽 모서리가 스크롤포트 아래 모서리에 막 닿는 지점),\
  **100% = 700**(요소 아래쪽 모서리가 스크롤포트 위 모서리를 막 넘어가는 지점).

**구간의 길이**

- **스크롤포트 높이 + 요소 높이** = 300 + 100 = **400** 이다.

```text
    scrollTop 300                scrollTop 500              scrollTop 700
  +---------------+            +---------------+          +---------------+
  |               |            |               |          |  ■ 요소        |
  |               |            |  ■ 요소        |          |               |
  |  ■ 요소        |            |               |          |               |
  +---------------+            +---------------+          +---------------+
      0%                            50%                        100%
```

**`scrollTop = 0` 에서**

- **-75%** 다. 구간 시작(300) 까지 300px 이 남았고 `300 / 400 = 75%` 다. **진행률은 음수가 된다.**

**명세의 단서**

> Note: The 0% and 100% scroll positions are not always reachable, e.g. if the box is positioned at the start edge of the scrollable overflow rectangle, it might not be possible to scroll to < 32% progress.

- 요소가 내용 맨 위에 붙어 있으면 **0% 자리로 스크롤할 방법이 없다.**

### 4. `view-timeline-inset` 이 왜 안 먹는가

**출력**

```text
  선언                                                          구간
  animation-timeline: view();  view-timeline-inset: 50px;       300 ~ 700   ★ inset 무시
  animation-timeline: view(block 25%);                          375 ~ 625   ✓
  view-timeline-name: --v; view-timeline-inset: 50px;
    + animation-timeline: --v;                                  350 ~ 650   ✓
```

```text
  scrollTop     inset:50px(이름 형태)   inset 없음
        300      -16.667%                   0%
        350           0%                 12.5%
        500          50%                   50%
        650         100%                 87.5%
        700      116.667%                  100%
```

**적용되는가**

- **안 된다.** `view()` 만 쓴 쪽은 inset 없는 쪽과 **값이 완전히 같았다.**

**계산값에는**

- **`50px` 그대로 나온다.** 선언은 유효하고 살아 있다 — **아무도 그것을 안 읽을 뿐이다.**

**같은 효과를 내는 두 가지**

1. 익명이면 **함수 인자**로: `animation-timeline: view(block 25%)`
2. 이름을 붙여서: `view-timeline-name: --v` + `view-timeline-inset: 50px` + `animation-timeline: --v`

**어느 유형인가**

- **「세 창이 전부 정상인데 기준만 다른 것」**(제5의 상태)이다.\
  `cssRules` 에 담겼고, 선택자도 잡혔고, 계산값도 나온다. **틀린 것은 값이 아니라 「그 값을 누가 읽느냐」 하는 기준**이다.
- `view-timeline-inset` 은 타임라인을 **만드는 요소**의 속성인데, 익명 `view()` 에는 만드는 요소가 따로 없다.

### 5. 스크롤러 밖의 막대

**출력** (스크롤러 높이 300 · 내용 1200 · 최대 스크롤 900. 기본 40px, 키프레임 0→200px)

```text
  scrollTop      outA (--sc)    outB (nearest)   farA (scope 밖)
          0          0px            40px             200px
        150     33.328px            40px             200px
        300     66.656px            40px             200px
        600    133.328px            40px             200px
        900        200px            40px             200px
```

**실제로 움직이는 것**

- **`outA` 하나**다.

**안 움직이는 둘의 모양**

- **`outB` 는 40px 에 멈췄다** — 조상에 스크롤 컨테이너가 없어 `currentTime` 이 `null`(실패 모양 ①).
- **`farA` 는 200px 로 박혔다** — 이름을 못 찾아 타임라인이 `null`(실패 모양 ②). **「못 찾음」이 「끝 상태」로 보인다.**

**`timeline-scope` 를 지우면**

- `#outA` 도 **`farA` 쪽이 된다** — 이름 조회 범위 밖이라 `null` 타임라인이 되고 200px 로 박힌다.

**`timeline-scope` 는 타임라인을 만드는가**

- **아니다.** 이미 만들어진 이름의 **조회 범위만** 넓힌다. 만드는 것은 `scroll-timeline-name`/`view-timeline-name` 이다.

### 6. `scroll()` 의 인자

**둘 다 생략하면**

- **`scroll(nearest block)`** 이다.

**`nearest` 는 자기 자신을 포함하는가**

- **아니다.** 조상 중에서 찾는다. 자기 자신을 쓰려면 **`self`** 라고 따로 말해야 한다.
- 실측: 스크롤 컨테이너가 아닌 요소에 `scroll(self block)` 을 주면 `currentTime` 이 `null` 이 되고 기본 스타일이 보였다.

**`block`/`inline` 과 `y`/`x`**

- **쓰기 모드가 세로쓰기이거나 방향이 RTL 일 때** 갈린다. `block`/`inline` 은 글 흐름을 따르고 `y`/`x` 는 물리 축이다.\
  정본은 [32번 주제](../32-logical-properties-and-writing-mode/2-summary.md).

**붙을 스크롤 컨테이너가 없으면**

- **실패 모양 ①** — 타임라인 객체는 만들어지지만 `currentTime` 이 `null` 이고 애니메이션이 적용되지 않는다.\
  **기본 스타일이 보이고 에러는 없다.**

### 7. 만드는 속성과 쓰는 속성

**이름**

```text
  만드는 쪽   scroll-timeline-name / scroll-timeline-axis   (단축 scroll-timeline)
              view-timeline-name   / view-timeline-axis     (단축 view-timeline)
              + view-timeline-inset
  넓히는 쪽   timeline-scope
  쓰는 쪽     animation-timeline
```

**이름이 보이는 범위**

- 기본은 **자기 자신과 자손**이다. 그 밖(형제·바깥)에서 쓰려면 **공통 조상에 `timeline-scope`** 를 둬야 한다.

**`view()` 에 `nearest`/`root`/`self` 가 없는 이유**

- `view()` 의 주체는 **언제나 그 선언이 붙은 요소 자신**이기 때문이다.\
  `scroll()` 은 「어느 **스크롤러**를 볼까」를 고르지만, `view()` 는 「이 **요소**가 보이는 구간」이라 고를 것이 없다.\
  고를 수 있는 것은 축과 inset 둘뿐이다.

### 8. 지금 써도 되는가

**Baseline** (`api.webstatus.dev` 2026-09-23 조회)

```text
  Scroll-driven animations   status: limited
    chrome 2023-07-18 · chrome_android 2023-07-21 · edge 2023-07-21
    safari 2025-09-15 · safari_ios 2025-09-15
    firefox  — 없음
```

**빠져 있는 엔진**

- **Firefox** 다. Safari 는 2025-09 에 따라왔지만 **Baseline 은 여전히 limited** 다(모든 엔진이 채워져야 newly 가 된다).

**그 엔진에서 선언은**

- **조용히 버려진다.** `animation-timeline` 이라는 속성을 모르므로 선언 하나가 무시되고, **나머지 `animation-*` 은 그대로 남는다.**\
  그래서 `animation-duration` 이 있으면 **시간 기반으로 그냥 돌아 버린다** — 진행 막대가 혼자 한 번 채워지고 끝난다.

**써도 되는 연출 / 쓰면 안 되는 연출**

| 써도 된다 | 쓰면 안 된다 |
|---|---|
| 읽기 진행 막대 — 없어도 글은 읽힌다 | 콘텐츠를 **감췄다가** 보이는 등장 효과 |
| 기본이 「보이는 상태」인 시차·강조 | 내비게이션·버튼처럼 **동작에 필요한 것** |

- 규칙 하나로 줄이면 — **기본 상태를 「연출이 끝난 모습」으로 두고, 연출은 얹기만 한다.**

### 9. 대체 수단과의 관계

**만들 수 있는가**

- **있다.** `scroll` 이벤트나 `IntersectionObserver` 로 같은 연출을 짤 수 있고 **모든 엔진에서 돈다.**

**CSS 쪽이 공짜로 주는 것**

1. **되감기** — 스크롤을 올리면 그대로 거꾸로 간다. 코드가 없다.
2. **구간 밖 처리** — 진행률이 음수/100% 초과가 되고 `fill-mode` 가 알아서 붙든다.
3. **리사이즈 대응** — 스크롤포트나 요소 크기가 바뀌면 구간이 다시 계산된다.

**「더 빠르다」고 말하려면**

- **프레임 시간이나 메인 스레드 점유를 실제로 재야 한다.** **이 문서에서는 재지 않았고, 그래서 그렇게 적지 않았다.**
- 명세·구현이 노리는 것은 스타일 계산을 JS 왕복 없이 끝내는 것이지만, **그 목표와 측정값은 다른 것**이다.

### 10. 다른 주제와 잇기

**`transition` 을 스크롤에 묶을 수 있는가**

- **없다.** `animation-timeline` 은 `animation-*` 계열의 속성이다. 전환에는 대응하는 속성이 없다.
- 스크롤에 묶고 싶으면 **`@keyframes` 로 다시 써야** 한다. 정본은 [목록의 **53번 주제**](../53-keyframes-and-animation/).

**스크롤 컨테이너의 정본**

- [23번 주제](../23-overflow-and-scroll-containers/2-summary.md)다. `overflow` 값이 무엇일 때 스크롤 컨테이너가 되는지, 스크롤포트가 무엇인지가 거기 있다.

**모션에 민감한 사용자에게 안전한가**

- **절반만 안전하다.** 움직임이 **사용자의 손가락에 묶여 있으므로** 예상 못 한 자동 움직임은 없다.
- 하지만 **시차·확대·회전은 여전히 전정계를 자극한다.** 그리고 **`prefers-reduced-motion` 은 스크롤 연동을 자동으로 막아 주지 않는다** — 저자가 직접 걸러야 한다. 정본은 [60번 주제](../60-prefers-reduced-motion/2-summary.md).

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless(`--headless=new`). **엔진은 이것 하나다.**\
**Firefox 155.0.1 은 이 기능 자체가 미구현이고, 이 환경에서는 headless 산출도 조용히 실패한다** — 「두 엔진에서 확인했다」고 적지 않았다.

**스크롤을 어떻게 움직였나** — 두 방법을 **둘 다 던져 보고 둘 다 작동**했다. 본문 표는 재현이 쉬운 앞쪽 방법으로 냈고, demo 절에는 휠 결과도 같이 실었다.

```text
  ① Runtime.evaluate 로 scrollTo(0, y) / el.scrollTop = y
       -> 정확한 위치로 한 번에 간다. 표를 만들기 좋다.
  ② Input.dispatchMouseEvent(type:"mouseWheel", deltaY: n)
       -> 한 번에 정확히 n px 움직였다 (60 · 300 둘 다 확인).
  둘 다 '값을 읽기 전에 requestAnimationFrame 두 번'을 기다려야 한다.
```

```bash
google-chrome --headless=new --no-sandbox --disable-gpu --hide-scrollbars \
  --force-device-scale-factor=1 --remote-allow-origins=* \
  --remote-debugging-port=9334 --window-size=900,500 about:blank
# /json → webSocketDebuggerUrl → Page.enable/Runtime.enable → Page.navigate
# → Runtime.evaluate("scrollTo(0,y)") → rAF ×2 → getComputedStyle
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| duration auto/1s/100s × 스크롤 6지점 + 애니메이션 객체 | 1 | 동작 방식 (1) · A1 |
| 휠(`mouseWheel`) 300px × 4회 | 1 | 실행 검증 · A1 |
| 죽은 타임라인 7종 × 스크롤 5지점 (t1\~t7) | 1 | 동작 방식 (2)·(3) · A2 · A6 |
| `fill-mode` 4종 × 죽은 타임라인 3종 | 1 | 동작 방식 (2) · A2 |
| `timeline-scope` 격자(inA\~farA) × 스크롤 9지점 | 1 | 동작 방식 (4) · A5 · A7 |
| `view()` 진행률 × 스크롤 15지점 × 3종(`view()`/`inset`/`view(block 25%)`) | 1 | 동작 방식 (5)·(6) · A3 · A4 |
| 이름 붙인 `view-timeline-inset` 대조 | 1 | 동작 방식 (6) · A4 |
| demo — 스크롤 5지점 + 휠 3회 | 1 | demo |
| demo 「바꿔 볼 것」 ① duration 10s / ② inline 축 | 2 | demo |
| Baseline 조회 | 1 | 머리말 · A8 |
| **제출 직전 demo 재추출·재실행 대조** | 1 | 어긋남 0건 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| 이름을 못 찾을 때 **끝 키프레임이 칠해지는 것** | 200px | 명세 문구로 직접 확인하지 않은 **관찰**이다 |
| 비활성 타임라인에서 **기본 스타일**이 보이는 것 | 40px | 〃 |
| `currentTime` 직렬화 | `"0%"` / `null` | Web Animations 직렬화 세부 |
| 진행률 소수 | `16.6667%` | 부동소수 표현 |
| 최대 스크롤 | 문서 3000 · 뷰포트 357 → 2643 | 창 크기·스크롤바 설정에 달려 있다 |
| 휠 1회 이동량 | 지정한 deltaY 그대로 | 플랫폼 스크롤 설정에 달려 있다 |
| Baseline | limited · Firefox 미구현 | 2026-09-23 조회. `api.webstatus.dev` 는 **2차 집계**다 |

**안 돌려 본 것** — ① Firefox·Safari 에서의 재현(구현이 없거나 엔진이 없다). ② `animation-range` 와 이름 있는 구간(`entry`/`exit`/`contain`) — 「더 들어가면」에 **존재만** 적었고 값을 주장하지 않았다. ③ Web Animations API 의 `new ScrollTimeline(...)`.

**못 잰 것** — **비용**이다. 「스크롤 이벤트보다 싸다」를 말하려면 프레임 시간·메인 스레드 점유를 재야 하는데 headless 단일 실행으로는 신호 대 잡음이 확보되지 않는다. **그래서 본문에서 성능을 주장하지 않았고**(A9), 대신 **구현 난이도 차이**만 적었다.

## 용어 풀이

- **스크롤 연동 애니메이션** — 시간 대신 스크롤 진행을 타임라인으로 쓰는 애니메이션.
- **진행률 기반 타임라인** — 길이가 시간이 아니라 **100%** 인 타임라인. `currentTime` 이 `%` 로 나온다.
- **`animation-timeline`** — 애니메이션이 볼 타임라인을 정하는 속성. `auto`(시간)가 기본.
- **`scroll()`** — 익명 스크롤 진행 타임라인. 기본 인자는 `nearest block`.
- **`view()`** — 익명 뷰 진행 타임라인. 주체는 **언제나 그 요소 자신**이다.
- **스크롤포트** — 스크롤 컨테이너에서 실제로 보이는 창.
- **`timeline-scope`** — 타임라인 이름의 조회 범위를 조상까지 올리는 속성. **만들지는 않는다.**
- **`view-timeline-inset`** — 뷰 구간을 안쪽으로 줄이는 값. **이름 붙인 형태에서만 먹는다.**
- **비활성 타임라인** — 객체는 있는데 `currentTime` 이 `null` 인 상태. 애니메이션이 **적용되지 않는다.**
- **null 타임라인** — 타임라인 객체 자체가 없는 상태. 애니메이션이 `finished` 가 되고 **fill 이 끝 값을 칠한다.**

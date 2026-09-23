# css/syntax/58 — 스크롤 연동 애니메이션: `animation-timeline`·`scroll()`/`view()`·`timeline-scope` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Scroll-driven Animations Level 1](https://drafts.csswg.org/scroll-animations-1/) (`scroll()`·`view()`·진행률 정의·이름 조회) · [CSS Animations Level 2](https://drafts.csswg.org/css-animations-2/) (`animation-timeline`). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 수치는 **Google Chrome 151.0.7922.173** headless 에 띄우고 **CDP 로 실제로 스크롤을 움직여** 잰 것이다. `Runtime.evaluate` 의 `scrollTo`/`scrollTop` 대입과 `Input.dispatchMouseEvent(type:"mouseWheel")` **둘 다 던져 봤고 둘 다 작동했다**(휠은 한 번에 정확히 지정한 px 만큼 움직였다). 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> **엔진은 Chrome 하나다** — Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고 WebKit 은 없다. 「두 엔진에서 확인했다」고 적지 않는다.
> ⚠️ **버전 — Baseline `limited` 다.** `api.webstatus.dev` 를 **2026-09-23 에 직접 조회**한 값: Chrome 2023-07-18 · Edge 2023-07-21 · Safari 2025-09-15 · **Firefox 미구현.**\
> 그래서 이 문서는 「이렇게 쓰면 된다」로 쓰지 않았다. 「**Chrome 에서는 이렇게 된다 + 어디까지 믿을 수 있나**」로 읽는다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**애니메이션의 시계를 떼어 내고 그 자리에 스크롤 막대를 꽂는 것이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 영화 필름 | `@keyframes` — 0% 부터 100% 까지의 그림들 |
| **보통의 영사기** — 초당 몇 칸씩 저 혼자 돈다 | `animation-timeline: auto`(기본) — 시간이 진행률을 만든다 |
| **손으로 돌리는 영사기** — 내가 돌린 만큼만 간다 | `animation-timeline: scroll(...)` — 스크롤이 진행률을 만든다 |
| 필름을 몇 초짜리로 편집했나 | `animation-duration` — **손으로 돌릴 때는 아무 뜻이 없다** |
| 어느 손잡이를 잡나 | `scroll()` 의 인자 — `nearest`/`root`/`self`, 축 |
| 필름 한 칸이 **화면에 들어왔다 나가는 동안** | `view()` — 요소가 보이는 구간이 0\~100% |

```text
  animation-timeline: auto (기본)        animation-timeline: scroll(root block)

     시간                                    스크롤 위치
      |                                         |
      v                                         v
   +--------+                              +--------+
   | 진행률 |  0% -> 100%  (1초)            | 진행률 |  0% -> 100%  (맨 위 -> 맨 아래)
   +--------+                              +--------+
      |                                         |
      v                                         v
   @keyframes 의 중간값                      @keyframes 의 중간값
```

- **필름은 그대로다.** `@keyframes` 도 `animation-name` 도 안 바뀐다(정본은 [목록의 **53번 주제**](../53-keyframes-and-animation/)).\
  바뀌는 것은 **진행률을 무엇이 만드는가** 하나뿐이다.
- 그래서 **되감기가 공짜다.** 스크롤을 올리면 애니메이션이 거꾸로 간다 — 내가 코드를 쓸 일이 없다.
- 그래서 **`animation-duration` 이 의미를 잃는다.** 시간이 진행률을 안 만들기 때문이다.

> **진행률(progress)** — 애니메이션이 0% 에서 100% 사이 어디쯤 왔는지의 비율.\
> 예: 2초짜리 애니메이션의 1초 시점은 진행률 50%. 스크롤 타임라인에서는 **스크롤을 절반 내린 지점**이 50%.

> **스크롤 컨테이너(scroll container)** — `overflow` 가 내용을 잘라 스크롤을 만드는 상자. 정본은 [23번 주제](../23-overflow-and-scroll-containers/2-summary.md).\
> 예: `overflow-y: auto` 를 준 `div`, 그리고 문서 루트.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `animation-duration` 은 **정말 아무 일도 안 하나.** 1초와 100초가 같은가?
2. 붙일 스크롤 컨테이너가 없으면 **어떤 모양으로 실패하나.**
3. `view()` 의 0% 와 100% 는 **정확히 어느 스크롤 위치인가.**

## 동작 방식

### (1) ★ `animation-duration` 은 정말 무의미하다 — 실측

**언제 쓰나** — 「시간을 줄였는데 왜 안 빨라지지」를 볼 때. 첫 번째로 부딪히는 벽이다.

같은 `@keyframes grow { from { width: 0 } to { width: 100% } }` 를 **지속만 바꿔** 세 막대에 걸고,\
뷰포트(900×357, 문서 높이 3000 → 최대 스크롤 2643)를 굴리며 계산값을 읽었다.

```text
  scrollY     duration:auto   duration:1s    duration:100s
  -------     -------------   -----------    -------------
        0          0px            0px             0px
      250     85.125px       85.125px        85.125px
      625    212.812px      212.812px       212.812px
     1250    425.641px      425.641px       425.641px
     1875    638.469px      638.469px       638.469px
     2500    851.297px      851.297px       851.297px
```

그림 해설 (한 단계씩):

- **세 열이 소수점까지 같다.** 1초와 100초가 구별되지 않는다.
- 값은 **순전히 스크롤 비율**이다 — `250 / 2643 = 9.46%`, `900px × 9.46% = 85.13px`.
- 애니메이션 객체를 열어 봐도 같은 말을 한다.

```text
  a.constructor.name          CSSAnimation
  a.timeline.constructor.name ScrollTimeline       <- 시계가 바뀌었다
  a.currentTime               "0%"                 ★ 밀리초가 아니라 '%'
  a.effect.getComputedTiming().duration  "100%"    ★ auto 가 100% 로 계산된다
```

- **`currentTime` 의 단위가 `%` 다.** 시간 기반 애니메이션이면 `0ms` 라고 나올 자리다.\
  「시계를 갈아 끼웠다」가 비유가 아니라 **객체 수준의 사실**이다.

비용 — 없음. 다만 **`animation-duration` 을 조절해 속도를 바꾸려는 시도는 전부 헛일**이다.\
속도를 바꾸려면 `@keyframes` 의 값을 바꾸거나 `animation-range` 로 구간을 좁힌다.

### (2) ★★ 실패하는 모양이 **둘**이고, 하나는 반대쪽으로 튄다

**언제 쓰나** — 「막대가 안 움직인다」를 진단할 때. **이 주제에서 가장 나쁜 자리다.**

기본 너비 `40px`, 키프레임 `from { width: 0 } to { width: 200px }`, `animation-fill-mode: both` 로 고정하고\
타임라인만 바꿔 일곱 가지를 던졌다.

```text
  경우                                  timeline 객체   currentTime  playState   보이는 width
  ----------------------------------    -------------   -----------  ---------   ------------
  t1  scroll(root block)   (정상)        ScrollTimeline  "0%"         running     0 -> 900px
  t5  scroll(nearest block)(=루트)       ScrollTimeline  "0%"         running     t1 과 같음
  t2  scroll(root inline)  (가로 없음)   ScrollTimeline  ★ null       running     ★ 40px (기본값)
  t7  scroll(self block)   (자기가 아님) ScrollTimeline  ★ null       running     ★ 40px (기본값)
  t3  animation-timeline: none           ★ null          0            finished    ★ 200px (마지막 키프레임)
  t6  animation-timeline: --nope         ★ null          0            finished    ★ 200px (마지막 키프레임)
  t4  애니메이션 자체 없음                 —               —            —           40px
```

```text
      실패 모양 ①  '타임라인은 있는데 안 움직임'      실패 모양 ②  '타임라인이 아예 없음'
      +------------------------------+              +------------------------------+
      | timeline = ScrollTimeline    |              | timeline = null              |
      | currentTime = null           |              | playState = "finished"       |
      | -> 애니메이션이 적용 안 됨     |              | -> fill 이 마지막 키프레임 적용 |
      +------------------------------+              +------------------------------+
         화면: 기본 스타일 (안 움직임)                  화면: 100% 상태로 '멈춰 있음'
```

그림 해설 (한 단계씩):

- **모양 ①**(축이 안 움직이거나 `self` 가 스크롤 컨테이너가 아님) — `currentTime` 이 **`null`** 이라 애니메이션이 **적용되지 않는다.** 기본 스타일이 보인다.
- **모양 ②**(`none` 이거나 **이름을 못 찾음**) — 타임라인이 없어 애니메이션이 곧장 `finished` 가 되고, **`fill-mode` 가 마지막 키프레임을 칠한다.**\
  **오타 하나로 「처음」이 아니라 「끝」 상태가 화면에 박힌다.**
- 모양 ② 는 `fill-mode` 에 달려 있다. 실측:

```text
  animation-timeline: none 일 때 fill-mode 별
    none       width=40px    (getAnimations() 에 객체조차 없다)
    forwards   width=200px
    backwards  width=40px    (객체 없음)
    both       width=200px
```

- **에러도 경고도 없다.** `cssRules` 에 담겼고 선택자도 잡혔고 계산값도 나온다 — **창 ④(`getAnimations()`)의 `timeline`·`currentTime` 을 봐야** 갈린다.

비용 — 없음. 진단 비용만 든다.

### (3) `scroll()` 의 인자 — 어느 손잡이를, 어느 축으로

**언제 쓰나** — 익명 타임라인을 쓸 때. 인자 둘 다 생략할 수 있다.

```css
animation-timeline: scroll();                  /* = scroll(nearest block) */
animation-timeline: scroll(root block);
animation-timeline: scroll(self inline);
animation-timeline: scroll(nearest x);
```

```text
  스크롤러 고르기                     축 고르기
  ---------------                    ---------
  nearest  가장 가까운 조상 스크롤    block   글 흐름의 세로축 (기본)
           컨테이너 (기본)            inline  글 흐름의 가로축
  root     문서 루트                  y / x   물리적 축 (쓰기 모드와 무관)
  self     자기 자신
```

- **`nearest` 는 조상만 본다.** 자기 자신은 `self` 로 따로 말해야 한다.
- 실측에서 `scroll(nearest block)` 은 루트만 스크롤되는 문서에서 `scroll(root block)` 과 **값이 완전히 같았다.**
- **붙을 스크롤 컨테이너가 없으면** 위 (2) 의 **실패 모양 ①** 이다 — 실측: 스크롤되지 않는 문서 안의 요소에 `scroll(nearest block)` 을 주니 `currentTime` 이 `null` 이고 기본 스타일이 보였다.
- `block`/`inline` 과 `y`/`x` 의 차이는 쓰기 모드다. 정본은 [32번 주제](../32-logical-properties-and-writing-mode/2-summary.md).

비용 — 없음.

### (4) 이름 붙인 타임라인과 `timeline-scope`

**언제 쓰나** — 애니메이션할 요소가 **스크롤러 안에 없을 때.** 진행 막대가 대표적이다.

```text
  이름 조회는 '위'로만 간다

  #wrap  (timeline-scope: --sc)  <- 여기까지 올려 두면 형제들도 본다
   ├─ #sc   (scroll-timeline-name: --sc)      스크롤러
   ├─ #outA (animation-timeline: --sc)        ✓ 찾는다
   └─ #outB (animation-timeline: scroll(nearest))  ✗ 조상에 스크롤러가 없다
  #farA    (animation-timeline: --sc)         ✗ scope 밖이라 못 찾는다
```

실측 — 스크롤러 높이 300 · 내용 1200(최대 스크롤 900), 기본 너비 40px, 키프레임 0→200px:

```text
  scrollTop      outA (--sc)    outB (nearest)   farA (scope 밖)
  ---------      -----------    --------------   ---------------
          0          0px            40px             200px
        150     33.328px            40px             200px
        300     66.656px            40px             200px
        600    133.328px            40px             200px
        900        200px            40px             200px
```

그림 해설 (한 단계씩):

- **`outA` 만 움직였다.** `timeline-scope: --sc` 를 공통 조상에 올려 둔 덕이다.
- **`outB` 는 40px 에 멈췄다**(실패 모양 ①) — 조상 중에 스크롤 컨테이너가 없다.
- **`farA` 는 200px 로 박혔다**(실패 모양 ②) — 범위 밖이라 이름을 못 찾았고, `fill` 이 마지막 키프레임을 칠했다.\
  **「이름을 못 찾았다」가 「끝 상태」로 보인다** — 이 표가 (2) 의 위험을 실물로 보여 준다.

비용 — `timeline-scope` 는 **이름을 위로 올려 두는 선언일 뿐** 스크롤러를 만들지 않는다.\
`scroll-timeline-name`(그리고 `view-timeline-name`)이 실제로 타임라인을 **만드는** 쪽이다.

### (5) ★ `view()` 의 0% 와 100% 는 어디인가

**언제 쓰나** — 「화면에 들어오면 나타나는」 연출을 짤 때. **가장 많이 쓰는 형태**이고, 기준을 모르면 값이 안 맞는다.

명세의 정의부터.

> The startmost such scroll position represents 0% progress, and the endmost such scroll position represents 100% progress.

말로 풀면 — **요소가 스크롤포트와 겹치기 시작하는 순간이 0%, 완전히 벗어나는 순간이 100%** 다.

```text
  스크롤포트 높이 300 · 요소 높이 100 · 요소가 내용 맨 위에서 600 지점

    scrollTop 300                scrollTop 500              scrollTop 700
  +---------------+            +---------------+          +---------------+
  |               |            |               |          |  ■ 요소        |  <- 위로 빠져나감
  |               |            |  ■ 요소        |          |               |
  |  ■ 요소        | <- 아래에서 |               |          |               |
  +---------------+    막 들어옴 +---------------+          +---------------+
      진행률 0%                    진행률 50%                 진행률 100%

  구간 길이 = 700 - 300 = 400 = 스크롤포트 높이(300) + 요소 높이(100)
```

실측 (`view()` · `opacity` 를 0→1 로):

```text
  scrollTop     진행률       opacity
  ---------     --------     -------
          0     -75%         0          ★ 음수다 — 아직 시작 전
        250     -12.5%       0
        300       0%         0
        350      12.5%       0.125
        500      50%         0.5
        650      87.5%       0.875
        700     100%         1
       1000     175%         1          ★ 100% 를 넘는다 — 이미 지나감
```

그림 해설 (한 단계씩):

- **진행률이 음수도 되고 100% 를 넘기도 한다.** 구간 **밖**이라는 뜻이고, `fill-mode` 가 값을 붙든다.
- **구간 길이가 스크롤포트 높이 + 요소 높이**인 것이 핵심이다. 짧은 요소는 구간이 짧아 **빨리 지나간다.**
- 명세는 **0%/100% 에 도달 못 할 수 있다**고 못을 박는다 — 요소가 내용 맨 위에 붙어 있으면 그 앞 구간을 스크롤할 방법이 없다.

비용 — 없음.

### (6) `view-timeline-inset` — 구간을 안쪽으로 줄인다

**언제 쓰나** — 「화면 가장자리에 걸치자마자」가 아니라 「제대로 들어온 다음에」 시작하고 싶을 때.

★ **여기에 조용한 함정이 하나 있다. 던져서 확인했다.**

```text
  선언 형태                                                     결과
  ----------------------------------------------------------   -----------------------------
  animation-timeline: view();  view-timeline-inset: 50px;       ★ inset 이 무시된다 (구간 300→700 그대로)
  animation-timeline: view(block 25%);                          ✓ 먹는다 (구간 375→625)
  view-timeline-name: --v; view-timeline-inset: 50px;
    + animation-timeline: --v;                                  ✓ 먹는다 (구간 350→650)
```

실측 — 이름 붙인 형태로 `view-timeline-inset: 50px` 을 준 것과 안 준 것:

```text
  scrollTop     inset:50px      inset 없음
  ---------     -----------     ----------
        300      -16.667%            0%
        350           0%          12.5%
        400      16.667%            25%
        500          50%            50%
        600      83.333%            75%
        650         100%          87.5%
        700      116.667%          100%
```

그림 해설 (한 단계씩):

- **구간이 양쪽에서 50px 씩 줄어** 350\~650(길이 300)이 됐다. 원래는 300\~700(길이 400)이었다.
- **`view-timeline-inset` 은 타임라인을 「만드는」 쪽 요소의 속성**이다. 익명 `view()` 에는 만드는 요소가 따로 없으므로 **그 속성이 아무에게도 안 붙는다.**\
  익명으로 쓸 때는 **함수의 둘째 인자**(`view(block 25%)`)로 준다.
- **에러도 경고도 없다.** 계산값을 읽어도 `view-timeline-inset: 50px` 이 그대로 나온다 — **선언은 살아 있고 아무도 안 읽을 뿐이다.**

비용 — 없음.

## demo — 안쪽 스크롤러에 진행 막대 달기

```html demo
<div class="feed">
  <div class="bar"></div>
  <p>안쪽을 스크롤해 보세요</p><p>둘째 줄</p><p>셋째 줄</p>
  <p>넷째 줄</p><p>다섯째 줄</p><p>여섯째 줄</p>
</div>
<style>
  @keyframes grow { from { width: 0 } to { width: 100% } }
  .feed { width: 240px; height: 120px; overflow-y: auto;
          border: 1px solid #94a3b8; font: 14px system-ui; }
  .feed p { margin: 12px }
  .bar { position: sticky; top: 0; height: 6px; background: #1d4ed8;
         animation-name: grow; animation-duration: auto;
         animation-timing-function: linear; animation-fill-mode: both;
         animation-timeline: scroll(nearest block); }
</style>
```

> **보이는 것** — 상자 **안쪽**을 스크롤하면 맨 위의 파란 막대가 스크롤한 만큼 오른쪽으로 자란다.\
> 맨 위에서는 폭 0, 맨 아래에서는 상자 폭(240px)을 꽉 채운다. **스크롤을 올리면 그대로 되감긴다.**\
> 움직임은 **전적으로 손가락에 달려 있다** — 스크롤을 멈추면 막대도 멈춘다.\
> **바꿔 볼 것** — `animation-duration: auto` → `10s` 로 바꿔도 **값이 하나도 안 달라진다**(진행률이 시간에서 오지 않는다) · `scroll(nearest block)` → `scroll(nearest inline)` 로 바꾸면 **막대가 처음부터 끝까지 꽉 찬 채로 멈춰 있다**(가로 스크롤이 없어 타임라인이 비활성이 되고, 애니메이션이 적용되지 않아 기본 너비 100% 가 그대로 보인다)

*(Chrome 151 headless 실측 — 스크롤러 높이 120 · 내용 210 · 최대 스크롤 90:)*

```text
  scrollTop     bar.width
  ---------     ---------
          0       0px
         22      58.656px
         45     120px
         67     178.656px
         90     240px

  CDP 휠로 움직였을 때 (Input.dispatchMouseEvent, deltaY 60)
     휠 1회 -> scrollTop 60,  bar 159.984px
     휠 2회 -> scrollTop 90,  bar 240px      (더 내려갈 데가 없다)

  바꿔 볼 것 ① duration 10s  -> 0 / 45 / 90 에서 0px / 120px / 240px  (auto 와 동일)
  바꿔 볼 것 ② inline 축     -> 0 / 45 / 90 에서 전부 240px

  ★ 로드 직후 '첫 프레임 전'에는 240px(기본 너비)로 읽힌다 — 타임라인이 아직 한 번도 안 돌았기 때문이다.
    requestAnimationFrame 을 두 번 기다린 뒤부터 0px 로 잡힌다.
    (extract-demo-blocks.py --render 가 이 블록에서 225px 을 찍는 이유가 이것이다 —
     그 도구는 한 장만 찍으므로 시간이 걸린 블록을 못 본다고 스스로 보고한다.)
```

## 문법 — 형태와 규칙

CSS 는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태

```css
/* ① 타임라인 붙이기 */
animation-timeline: auto | none | <이름> | scroll(...) | view(...);

/* ② 익명 타임라인 */
scroll( [ nearest | root | self ]? [ block | inline | x | y ]? )
view(   [ block | inline | x | y ]? [ <inset> ]? )

/* ③ 타임라인 만들기 (이름 붙이기) */
scroll-timeline-name: --sc;   scroll-timeline-axis: block;
scroll-timeline: --sc block;                     /* 단축 */
view-timeline-name: --v;      view-timeline-axis: block;
view-timeline-inset: 50px;                       /* 이름 붙인 형태에서만 먹는다 */

/* ④ 이름을 위로 올리기 */
timeline-scope: --sc;
```

### 금지 사례 — 던져서 확인한 것

```css
/* ✗ 익명 view() 에 view-timeline-inset — 조용히 무시된다 */
animation-timeline: view();
view-timeline-inset: 50px;          /* 계산값에는 남는데 아무 효과가 없다 */

/* ✗ 이름 오타 — 에러가 아니라 '마지막 키프레임'이 화면에 박힌다 */
animation-timeline: --scrol;        /* --scroll 의 오타 */

/* ✗ animation-duration 으로 속도 조절 — 1s 든 100s 든 같다 */
```

### 어디서 헷갈리나

- **만드는 속성과 쓰는 속성이 다르다.** `scroll-timeline-name`/`view-timeline-name` 이 만들고, `animation-timeline` 이 쓴다.
- **`timeline-scope` 는 만들지 않는다.** 이미 만들어진 이름의 **조회 범위만** 넓힌다.
- **`scroll()` 은 스크롤러를, `view()` 는 요소를 본다.** `view()` 에는 `nearest`/`root`/`self` 자리가 없다 — 주체가 언제나 **그 요소 자신**이다.
- **`animation-timeline` 은 `animation` 단축에 포함되지 않는다.** 단축을 뒤에 쓰면 타임라인이 **초기화되지 않는 대신**, 순서에 따라 `animation-name` 등이 되돌아간다 — 롱핸드로 쓰는 편이 안전하다.

## 어디서 틀리나

### 1. ★★ 타임라인 이름을 오타 낸다

**「아무 일도 안 일어남」이 아니라 「끝 상태로 박힘」이 된다**(동작 방식 (2)·(4)).\
진행 막대라면 **처음부터 100% 로 꽉 찬 막대**가 보인다. 「원래 저렇게 생겼나 보다」로 넘어가기 딱 좋다.

### 2. `animation-duration` 으로 속도를 맞추려 한다

1초와 100초가 소수점까지 같았다. 속도는 `@keyframes` 값이나 `animation-range` 로 바꾼다.

### 3. 스크롤 컨테이너가 없는데 `scroll(nearest)` 를 쓴다

조상에 `overflow` 로 만든 스크롤 컨테이너가 없으면 `currentTime` 이 `null` 이 되고 **기본 스타일**이 보인다.\
무엇이 스크롤 컨테이너가 되는지는 [23번 주제](../23-overflow-and-scroll-containers/2-summary.md)가 정본이다.

### 4. 스크롤러 **밖**의 요소에 이름만 준다

`scroll-timeline-name` 은 **자기와 자손**에게만 보인다. 형제·바깥 요소가 쓰려면 **공통 조상에 `timeline-scope`** 가 필요하다.

### 5. 익명 `view()` 에 `view-timeline-inset` 을 준다

조용히 무시된다. 익명이면 **함수 인자**(`view(block 25%)`)로 줘야 한다(동작 방식 (6)).

### 6. `view()` 의 구간을 요소 높이만으로 계산한다

구간 길이는 **스크롤포트 높이 + 요소 높이**다. 실측에서 300 + 100 = 400 이었다.

### 7. Firefox 를 잊는다

**Baseline limited** 이고 **Firefox 에 구현이 없다.** 거기서는 `animation-timeline` 선언이 통째로 버려져\
**시간 기반 애니메이션이 그냥 돌거나**(`animation-duration` 이 있으면) **아무 일도 안 일어난다.**\
연출이 **없어도 읽히는 페이지**로 짜야 한다(진행 막대·등장 효과는 그래서 이 갈래에 잘 맞는다).

## 구현 세부사항 대 언어 보장

| 항목 | 누가 보장하나 |
|---|---|
| `view()` 의 0%/100% 정의 | **명세**(scroll-animations-1, 위 인용) |
| 0%/100% 에 **도달 못 할 수 있다** | **명세**(같은 절의 Note) |
| `scroll()` 의 기본 인자가 `nearest block` | **명세** |
| `animation-duration` 이 무의미한 것 | **명세**(진행률 기반 타임라인) + **Chrome 151 실측**(1s = 100s) |
| 이름을 못 찾을 때 **마지막 키프레임이 칠해지는 것** | **Chrome 151 관찰.** `fill-mode` 조합에 달려 있고 명세 문구로 직접 확인하지 않았다 |
| `currentTime` 이 `null` 일 때 **기본 스타일**이 보이는 것 | **Chrome 151 관찰** |
| `currentTime` 의 직렬화가 `"0%"` 인 것 | Web Animations 의 CSSUnitValue 직렬화 |
| 진행률 소수(`16.6667%`) | 부동소수 표현 |
| 이 기능의 지원 | **Baseline limited** — Firefox 미구현(2026-09-23 조회) |
| 합성 스레드에서 도는지 | **이 문서에서 재지 않았다.** 아래 「언제 쓰고 언제 안 쓰나」 참고 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓰나 | 왜 |
|---|---|---|
| 읽기 진행 막대 | **쓴다** | 없어도 글은 읽힌다 — limited 여도 안전한 갈래 |
| 화면에 들어오면 나타나는 카드 | **쓴다** — 단 `view()` | 〃. **기본 상태를 「보이는 것」으로** 두고 연출만 얹는다 |
| 시차(parallax) 배경 | 쓴다 | 〃 |
| 콘텐츠를 **감추는** 등장 효과 | **안 쓴다** | Firefox 에서 영영 안 나타날 수 있다 |
| 정확한 시각에 맞춰야 하는 연출 | 안 쓴다 | 진행률이 시간에서 오지 않는다. [목록의 **53번 주제**](../53-keyframes-and-animation/) |
| 스크롤 위치를 **읽어서 로직**을 돌리는 것 | 안 쓴다 | 그건 `IntersectionObserver` 의 일이다 |

**대체 수단과의 관계** — `scroll` 이벤트나 `IntersectionObserver` 로 같은 연출을 만들 수 있고, 그쪽은 **모든 엔진에서 돈다.**\
이 기능이 노리는 것은 **스타일 계산을 JS 왕복 없이 엔진 안에서 끝내는 것**이다.\
다만 **이 문서에서는 그 비용 차이를 재지 않았다** — 「더 빠르다」고 적지 않는다. 갈리는 지점은 **구현 난이도**다:\
되감기·구간 밖 처리·리사이즈 대응이 CSS 쪽에서는 공짜인데 JS 쪽에서는 전부 손으로 짜야 한다.

## 핵심 문장

- **바뀌는 것은 「진행률을 무엇이 만드는가」 하나뿐이다.** `@keyframes` 도 `animation-name` 도 그대로다.
- **`animation-duration` 은 무의미하다.** 1초와 100초가 소수점까지 같았다.
- **실패 모양이 둘이고, 하나는 「끝 상태」로 박힌다.** 이름 오타가 100% 상태를 화면에 고정시킨다.
- **`view()` 의 구간 길이는 스크롤포트 높이 + 요소 높이**다.
- **`view-timeline-inset` 은 이름 붙인 형태에서만 먹는다.** 익명이면 함수 인자로 준다.
- **Baseline limited · Firefox 미구현** — 없어도 읽히는 페이지에만 얹는다.

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 58번)
- [`../23-overflow-and-scroll-containers/2-summary.md`](../23-overflow-and-scroll-containers/2-summary.md) — **스크롤 컨테이너의 정본.**\
  무엇이 스크롤 컨테이너가 되는지·스크롤포트가 무엇인지는 **거기까지**,\
  여기는 **그 스크롤 위치를 타임라인으로 쓰는 것부터**.
- [목록의 **53번 주제**](../53-keyframes-and-animation/)(`@keyframes`·`animation`) — **애니메이션의 정본.**\
  키프레임·`fill-mode`·`direction`·`iteration` 은 거기, 여기는 **`animation-timeline` 한 축**만.
- [`../32-logical-properties-and-writing-mode/2-summary.md`](../32-logical-properties-and-writing-mode/2-summary.md) — `block`/`inline` 축과 `y`/`x` 축이 갈리는 이유.
- [`../52-transition/2-summary.md`](../52-transition/2-summary.md) — 두 값 사이만 오가는 쪽. 스크롤에 묶을 수 없다.
- [`../57-starting-style-and-entry-exit-transitions/2-summary.md`](../57-starting-style-and-entry-exit-transitions/2-summary.md) — 나타날 때의 전환. `view()` 와 목적이 겹치지만 방아쇠가 다르다.
- [`../60-prefers-reduced-motion/2-summary.md`](../60-prefers-reduced-motion/2-summary.md) — **모션 접근성의 정본.**\
  ★ 스크롤 연동 연출은 **사용자가 직접 굴리는 것**이라 성격이 다르지만, 시차·확대는 여전히 줄여야 한다. 판단은 거기.
- [`../../../../../../reference/render-rules.md`](../../../../../../reference/render-rules.md) — demo 블록 규칙.

## 용어 풀이

- **스크롤 연동 애니메이션(scroll-driven animation)** — 시간 대신 스크롤 진행을 타임라인으로 쓰는 애니메이션.
- **진행률 기반 타임라인(progress-based timeline)** — 길이가 시간이 아니라 **100%** 인 타임라인. `currentTime` 이 `%` 로 나온다.
- **`animation-timeline`** — 애니메이션이 어느 타임라인을 볼지 정하는 속성. `auto`(시간)가 기본.
- **`scroll()`** — 익명 스크롤 진행 타임라인. 인자는 `nearest`/`root`/`self` 와 축.
- **`view()`** — 익명 뷰 진행 타임라인. **요소가 스크롤포트와 겹치는 구간**이 0\~100%.
- **스크롤포트(scrollport)** — 스크롤 컨테이너에서 실제로 보이는 창. 정본은 23번 주제.
- **`scroll-timeline-name` / `view-timeline-name`** — 타임라인을 **만들고** 이름을 붙이는 속성.
- **`timeline-scope`** — 그 이름을 **조상까지 올려** 형제들도 찾을 수 있게 하는 속성. 타임라인을 만들지는 않는다.
- **`view-timeline-inset`** — 뷰 구간을 안쪽으로 줄이는 값. **이름 붙인 형태에서만 먹는다.**
- **비활성 타임라인(inactive timeline)** — 객체는 있는데 `currentTime` 이 `null` 인 상태. 애니메이션이 적용되지 않는다.

## 더 들어가면

- **`animation-range`**(`entry`·`exit`·`cover`·`contain` 같은 이름 있는 구간)로 「0\~100% 중 어디를 쓸지」를 좁힐 수 있다. 속도를 바꾸는 실질적인 수단이 이쪽이다. **이 문서에서는 재지 않았다.**
- Web Animations API 쪽에는 `new ScrollTimeline({ source, axis })`·`new ViewTimeline({ subject })` 가 있다. CSS 로 이름을 붙이지 않고 JS 에서 직접 만들 수 있다.
- `view()` 의 명세에는 `cover` 말고도 `contain`·`entry`·`exit` 이라는 **이름 있는 구간**이 정의돼 있다. 이 문서의 표는 전부 기본 구간(`cover`)이다.

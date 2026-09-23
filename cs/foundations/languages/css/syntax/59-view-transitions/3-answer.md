# css/syntax/59 — 뷰 전환: `view-transition-name`·`::view-transition-*` 의사 요소 트리 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 값은 Google Chrome 151.0.7922.173 headless 에서 실제로 전환을 돌려 측정한 것**이다.\
> `document.startViewTransition()` 이 **headless 에서 실제로 실행됐다** — `ready`·`finished` 가 resolve 됐고 의사 요소의 계산값이 읽혔다.\
> 규칙은 [CSS View Transitions Level 1](https://drafts.csswg.org/css-view-transitions-1/) · [Level 2](https://drafts.csswg.org/css-view-transitions-2/) 로 접지했다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 이 전환에서 의사 요소는 몇 개 생기는가

**출력** (Chrome 151 headless — `document.getAnimations()` 의 `pseudoElement`)

```text
  ::view-transition-group(root)   -ua-view-transition-group-anim-root   250ms
     키프레임  900×357 -> 900×357            ★ 아무것도 안 바뀌는데도 생긴다
  ::view-transition-group(card)   -ua-view-transition-group-anim-card   250ms
     키프레임  120×60 -> 300×160
  ::view-transition-old(root)     -ua-view-transition-fade-out          250ms  opacity 1 -> 0
  ::view-transition-new(root)     -ua-view-transition-fade-in           250ms  opacity 0 -> 1
  ::view-transition-old(card)     -ua-view-transition-fade-out          250ms
  ::view-transition-new(card)     -ua-view-transition-fade-in           250ms
  (+ old/new 마다 -ua-mix-blend-mode-plus-lighter 가 하나씩 더)
```

**몇 종인가**

- **6종**이다 — `group` 둘, `old` 둘, `new` 둘.

**`#plain` 은 어디에**

- **`root`** 에 들어간다. 이름이 없는 것은 **전부 `root` 한 장**으로 뭉친다.

**아무것도 안 바뀌어도 만들어지는가**

- **만들어진다.** `root` 의 group 애니메이션은 `900×357 → 900×357` 로 **변화가 0** 인데도 존재한다.

**이름을 지우면**

- **3종으로 준다** — `group(root)` · `old(root)` · `new(root)`. 실측으로 확인했다.

### 2. 트리를 그릴 수 있는가

```text
  :root (html)
    └─ ::view-transition                         position: absolute (실측)
         ├─ ::view-transition-group(root)
         │    └─ ::view-transition-image-pair(root)    isolation: isolate (실측)
         │         ├─ ::view-transition-old(root)      mix-blend-mode: plus-lighter
         │         └─ ::view-transition-new(root)      mix-blend-mode: plus-lighter
         └─ ::view-transition-group(card)
              └─ ::view-transition-image-pair(card)
                   ├─ ::view-transition-old(card)
                   └─ ::view-transition-new(card)
```

**위치·크기를 맡는 층**

- **`group`** 이다. 실측 키프레임이 `width`·`height`·`transform` 이었다.

**불투명도를 맡는 층**

- **`old`/`new`** 다. 키프레임이 `opacity 1→0` 과 `0→1` 이었다.

**`isolate` 를 쓰는 이유**

- `old` 와 `new` 가 **`plus-lighter` 로 섞이기** 때문이다. 이 혼합이 바깥 배경까지 물들면 안 된다.
- `isolation: isolate` 가 **혼합 범위를 `image-pair` 안으로 가둔다.** 정본은 [48번 주제](../48-blend-modes-and-isolation/2-summary.md).

> **`plus-lighter`** — 두 층의 값을 더하는 혼합. 두 그림의 불투명도 합이 1 이면 **중간에 어두워지거나 밝아지지 않고** 깨끗한 크로스페이드가 된다.

### 3. `duration` 을 어디에 주는가

**출력** (`::view-transition-group(card) { animation-duration: 1s }` 만 선언)

```text
  ::view-transition-group(card)        1s
  ::view-transition-image-pair(card)   1s
  ::view-transition-old(card)          1s
  ::view-transition-new(card)          1s
  ::view-transition-group(root)        0.25s
  ::view-transition-old(root)          0.25s

  실제 애니메이션
    ::view-transition-group(card) 1000ms · old(card) 1000ms · new(card) 1000ms
    ::view-transition-group(root)  250ms · old(root)   250ms · new(root)   250ms
```

**`::view-transition-old(card)` 의 값**

- **1s** 다. 선언하지 않았는데 따라왔다.

**상속되는 속성인가**

- **아니다.** `animation-duration` 은 상속 속성이 아니다.

**그런데 왜 따라오나**

- **UA 스타일시트가 `old`/`new` 에 `animation-duration: inherit` 을 명시해 두었기 때문**이다.\
  상속을 **속성의 성질로** 받는 게 아니라 **선언으로** 받는다.
- 덕분에 **`group` 하나만 건드리면 그 이름의 네 층이 같이 바뀐다.**

**`root` 쪽은**

- **0.25s 그대로**다. 이름이 다르므로 영향을 받지 않는다.

### 4. 기본 전환의 이징은 무엇인가

**기본 지속**

- **0.25초**(실제 애니메이션 250ms).

**두 창이 다를 때**

```text
  a.effect.getTiming().easing          "linear"    ← 효과 수준
  a.effect.getKeyframes()[0].easing    "ease"      ← 키프레임 수준  ★ 실제로 도는 것
```

- **키프레임 쪽**이 실제로 돈다.

**무엇으로 판정했는가**

```text
  1초짜리 group 전환, 폭 120px -> 300px (거리 180px)
    t=169ms (시간 16.9%)  ->  159.703px  (거리 22.1%)
```

- **시간 비율보다 거리 비율이 앞선다** → 등속이 아니다. `linear` 였다면 16.9% 지점에서 150.4px 이어야 한다.
- **한 창만 읽고 손계산하면 틀린다.** 값을 실제로 재서 반증했다.

### 5. 같은 이름이 둘이면

**출력**

```text
  vt.ready               rejected   InvalidStateError: Transition was aborted because of invalid state
  vt.updateCallbackDone  resolved
  vt.finished            resolved
  전환 뒤 카드 폭          120px      (DOM 변경은 적용됐다)
```

**`ready`**

- **reject 된다.** 오류는 **`InvalidStateError`**, 문구는 `Transition was aborted because of invalid state`.

**`updateCallbackDone` 과 `finished`**

- **둘 다 resolve 된다.** 실패가 아니라 **정상 종료**로 끝난다.

**DOM 변경은**

- **적용된다.** 콜백은 그대로 실행됐다.

**화면에서 알아챌 수 있는가**

- **거의 못 알아챈다.** 애니메이션만 없어지고 화면은 **툭** 바뀐다. 기능이 망가지지 않으므로 버그로 안 보인다.
- 그래서 **`vt.ready` 를 `catch` 하는 것이 유일한 안전망**이다.

### 6. 일부러 건너뛴 것과 구별할 수 있는가

**출력**

```text
  vt.skipTransition() 직후
    vt.ready      rejected: AbortError
    vt.finished   resolved
    카드 폭        300px  (DOM 변경 적용됨)
```

**`skipTransition()` 의 오류**

- **`AbortError`** 다.

**이름 충돌과 같은가**

- **다르다.** 이름 충돌은 **`InvalidStateError`** 였다.

```text
  건너뛴 이유          ready 의 오류 이름
  -----------------    ------------------
  skipTransition()     AbortError
  이름 충돌             InvalidStateError
```

**`finished` 는**

- **둘 다 resolve** 된다. 여기로는 절대 구별할 수 없다.

### 7. 전환 중에 진짜 요소는 어떤 상태인가

**출력** (`vt.ready` 직후, 전환이 도는 중에 진짜 `#card` 를 읽었다)

```text
  getComputedStyle(card).width        "300px"      ← 새 값
  getComputedStyle(card).visibility   "visible"
  card.getBoundingClientRect()        300 × 160    ← 새 값
```

**`width` 는**

- **새 값**이다. 화면에는 아직 작은 카드 그림이 떠 있는데도 그렇다.

**`getBoundingClientRect()` 는**

- 역시 **새 값**이다. 레이아웃은 이미 끝나 있다.

**`visibility` 는**

- **`visible`** 이다. 숨겨져 있지도 않다 — 다만 **그 자리는 의사 요소가 덮고 있다.**

**무엇으로 판정해야 하는가**

- **`document.getAnimations()`** 에 `-ua-view-transition-*` 이름의 애니메이션이 있는지로 본다.
- ★ 이것이 이 주제의 **제5의 상태**다 — 계산값도 좌표도 정상이고 **화면만 다르다.** 「계산값은 무엇이 선언됐나를 말하지 무엇이 보이나를 말하지 않는다.」

### 8. 멈추는 구간은 어디인가

**출력** (`startViewTransition()` 호출 시각 = 0)

```text
  t=15ms   첫 requestAnimationFrame
  t=17ms   콜백 진입                      ★ 같은 프레임이 아니라 다음 프레임
  t=17ms   콜백 안에서 잰 카드 폭 = 300px
  t=17ms   updateCallbackDone
  t=19ms   ready
  t=299ms  finished                        (250ms 애니메이션 + 준비 시간)
```

**같은 프레임에 실행되는가**

- **아니다.** 옛 화면을 먼저 찍어야 하므로 **다음 프레임**에 콜백이 들어온다.

**콜백 안에서 잰 좌표**

- **새 것**이다(300px). DOM 변경과 레이아웃이 그 안에서 끝난다.

**멈추는 것은 무엇인가**

- **화면 갱신(렌더링)** 이다. 레이아웃이 아니다.
- 이 환경에서 그 구간은 **약 2\~4ms**(콜백 17ms → ready 19ms)였다.

**콜백에서 서버를 기다리면**

- **그동안 옛 화면이 그대로 얼어 있다.** 스피너도 못 돈다 — 화면 갱신이 멈춰 있기 때문이다.
- 그래서 **데이터는 콜백 밖에서 먼저 받고, 콜백은 DOM 만 갈아 끼운다.**

### 9. 지금 써도 되는가

**Baseline** (`api.webstatus.dev` 2026-09-23 조회)

```text
  View transitions              status: newly   (저변 도달 2025-10-14)
    chrome 2023-03-07 · edge 2023-03-13 · safari 2024-09-16
    firefox 2025-10-14 · firefox_android 2025-10-14        ★ 마지막으로 따라온 엔진

  Cross-document view transitions   status: limited
    chrome 2024-06-11 · edge 2024-06-13 · safari 2024-12-11
    firefox  — 없음
```

**같은 문서 전환**

- **Baseline `newly`** 이고 **2025-10-14** 에 그렇게 됐다. Firefox 가 마지막으로 따라왔다.
- ★ **`limited` 인 것은 「문서 간 전환」 쪽이다** — 같은 문서 전환과 헷갈리기 쉬우니 목록의 두 행을 따로 읽어야 한다.

**문서 간 전환**

- **`limited`** 이고 **Firefox 에 없다.**

**같은 기능으로 다루면 안 되는 이유**

- **지원 폭이 다르다.** 같은 문법(`view-transition-name`·의사 요소)을 쓰기 때문에 한 덩어리로 보이지만,\
  문서 간 전환을 켜는 `@view-transition` 은 Firefox 에서 **조용히 무시**되고 페이지는 그냥 넘어간다.
- 기능이 깨지지는 않지만 **「전환이 된다」를 전제로 설계하면 안 된다.**

### 10. 다른 주제와 잇기

**제자리에서 색만 바뀌는 경우**

- **뷰 전환을 쓸 이유가 없다.** `transition` 한 줄이면 된다([52번 주제](../52-transition/2-summary.md)).
- 뷰 전환은 **DOM 이 갈아 끼워져 「같은 요소로 이어 그릴 수 없을 때」** 쓰는 것이다.

**겹침 순서는 `z-index` 를 따르는가**

- **아니다.** 전환 중에는 **의사 요소 트리의 순서**가 겹침을 정한다. 문서의 쌓임 맥락은 스냅숏 안에 굳어 있다.
- 바꾸려면 `::view-transition-group(<이름>)` 에 `z-index` 를 직접 준다. 쌓임 맥락 일반의 정본은 [22번 주제](../22-stacking-context-and-z-index/2-summary.md).

**진행률은 어디서 오는가**

- **시간**이다. UA 애니메이션이 250ms 짜리 시간 기반 애니메이션이다.
- 스크롤에서 오는 것은 [58번 주제](../58-scroll-driven-animations/2-summary.md).

**모션 접근성에서 특히 조심할 이유**

- **화면 전체가 한꺼번에 움직이는** 연출이라 전정계를 가장 강하게 자극하는 부류다.
- 이름을 준 요소가 화면을 가로지르며 커지는 것이 대표적이다. 줄이는 방법의 정본은 [60번 주제](../60-prefers-reduced-motion/2-summary.md).

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless(`--headless=new`). **엔진은 이것 하나다**(Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고, WebKit 은 없다).

**headless 에서 실제로 돌았나** — **돌았다.** 이것을 먼저 확인하고 시작했다.

```text
  typeof document.startViewTransition          "function"
  CSS.supports('view-transition-name','a')     true
  vt.ready                                     resolved
  vt.finished                                  resolved
  getComputedStyle(root,'::view-transition-group(card)').width   "120px" (ready 시점)
```

**의사 요소 트리를 어떻게 봤나** — 두 창을 같이 썼다.

```js
// 창 ① UA 가 만든 애니메이션에서 pseudoElement 를 뽑는다 — 트리의 '존재'가 보인다
document.getAnimations().map(a => ({
  name: a.animationName, pseudo: a.effect.pseudoElement,
  dur: a.effect.getTiming().duration,
  kf: a.effect.getKeyframes()
}));
// 창 ② 계산값 — 트리의 '스타일'이 보인다 (루트 요소에 물어야 한다)
getComputedStyle(document.documentElement, '::view-transition-group(card)').width;
```

```bash
google-chrome --headless=new --no-sandbox --disable-gpu --hide-scrollbars \
  --force-device-scale-factor=1 --remote-allow-origins=* \
  --remote-debugging-port=9334 --window-size=900,500 about:blank
# Runtime.evaluate(awaitPromise: true) 로 async 함수를 그대로 기다렸다
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| headless 지원 확인(`startViewTransition`·`CSS.supports`) | 1 | 실행 검증 |
| 이름 있음/없음 전환 + `getAnimations()` 전수 + 의사 요소 계산값 6항목 | 1 | 동작 방식 (1)·(3) · A1 · A2 |
| 전환 중 시각별 샘플(`group.width`·`old/new.opacity`) | 2 | 동작 방식 (2) · demo · A4 |
| `duration` 전파(`group` 만 1s) 계산값 6항목 + 애니메이션 10개 | 2 | 동작 방식 (2) · A3 |
| 이징 두 창 대조(`getTiming` 대 `getKeyframes`) | 1 | 동작 방식 (2) · A4 |
| 이름 충돌 — `ready`/`updateCallbackDone`/`finished` 3프라미스 | 1 | 동작 방식 (4) · A5 |
| `skipTransition()` — 같은 3프라미스 | 1 | A6 |
| `view-transition-name: none` 일 때 의사 요소 목록 | 2 | 동작 방식 (3) · A1 |
| 단계별 시각 + 전환 중 진짜 요소 읽기 | 1 | 동작 방식 (5) · A7 · A8 |
| demo 본판 + 「바꿔 볼 것」 ① 4s ② 이름 제거 | 3 | demo |
| Baseline 조회(같은 문서 · 문서 간) | 1 | 머리말 · A9 |
| **제출 직전 demo 재추출·재실행 대조** | 1 | 어긋남 0건 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| UA 애니메이션 이름 | `-ua-view-transition-fade-out` 등 | **구현 내부 이름이다.** 선택자·조건으로 쓰면 안 된다 |
| `::view-transition` 의 `position` | `absolute` | 명세 UA 시트와 대조하지 않은 관찰 |
| 오류 문구 | `Transition was aborted because of invalid state` | 오류 **이름**(`InvalidStateError`)은 명세, 문장은 구현 |
| 단계별 시각(17ms·19ms·299ms) | 한 판의 값 | 프레임 경계와 DOM 무게에 달려 있다 |
| 기본 지속 | 250ms | UA 시트 값 — 구현이 바꿀 수 있다 |
| Baseline | newly 2025-10-14 / 문서 간 limited | 2026-09-23 조회. `api.webstatus.dev` 는 **2차 집계**다 |

**안 돌려 본 것** — ① **문서 간 전환(`@view-transition`)**. 두 문서 사이의 탐색이 필요해 headless 한 판으로 재현하기 어렵다 — **존재와 Baseline 만** 적었고 동작을 주장하지 않았다. ② `view-transition-class`(Level 2). ③ Firefox·Safari 에서의 재현(엔진이 없다).

**못 잰 것** — **「레이아웃이 멈추는 구간」의 상한**이다. 이 문서의 2\~4ms 는 **DOM 변경이 클래스 토글 하나뿐인 최소 사례**의 값이다. 무거운 DOM 변경에서 그것이 얼마나 늘어나는지는 부하를 설계해야 하는데, 그러면 「무엇을 재는 실험인가」가 흐려진다. 그래서 **상한을 주장하지 않고 「콜백 무게에 비례한다」는 성질만** 적었다.

## 용어 풀이

- **뷰 전환(view transition)** — DOM 변경 전후의 화면을 스냅숏으로 떠서 애니메이션하는 기능.
- **스냅숏** — 그 순간의 렌더 결과를 이미지처럼 떠 둔 것.
- **`view-transition-name`** — 「따로 추적하라」는 이름표. 상속되지 않고 **한 시점에 하나만** 존재해야 한다.
- **`::view-transition-group(<이름>)`** — 위치·크기를 애니메이션하는 층.
- **`::view-transition-image-pair(<이름>)`** — 옛·새 그림을 겹쳐 드는 액자. `isolation: isolate`.
- **`::view-transition-old` / `-new`** — 옛·새 화면의 그림. 불투명도를 맡는다.
- **`plus-lighter`** — 두 층의 값을 더하는 혼합. 불투명도 합이 1 이면 깨끗한 크로스페이드가 된다.
- **`root`** — 이름을 안 준 나머지 전부가 묶이는 기본 이름.
- **`ready`** — 의사 요소 트리가 준비됐을 때 resolve 되는 프라미스. **실패가 드러나는 유일한 창.**
- **`InvalidStateError` / `AbortError`** — 이름 충돌로 죽은 경우 / `skipTransition()` 으로 건너뛴 경우.
- **`@view-transition`** — 문서 간 전환을 켜는 규칙. Baseline limited, Firefox 없음.

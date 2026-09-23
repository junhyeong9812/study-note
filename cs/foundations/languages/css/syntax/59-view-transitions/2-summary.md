# css/syntax/59 — 뷰 전환: `view-transition-name`·`::view-transition-*` 의사 요소 트리 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [CSS View Transitions Level 1](https://drafts.csswg.org/css-view-transitions-1/) (의사 요소 트리·이름·스냅숏) · [CSS View Transitions Level 2](https://drafts.csswg.org/css-view-transitions-2/) (`@view-transition`, 문서 간 전환). 열어서 확인한 것만 적었다.
> **실행 검증** — **돌았다.** `document.startViewTransition()` 이 **Google Chrome 151.0.7922.173 headless 에서 실제로 실행**되고 `ready`/`finished` 가 모두 resolve 됐다. 의사 요소 트리는 **`document.getAnimations()` 로 UA 가 만든 애니메이션을 읽어** 확인했고, 계산값은 `getComputedStyle(document.documentElement, '::view-transition-…')` 로 읽었다. 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> **엔진은 Chrome 하나다** — Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고 WebKit 은 없다. 「두 엔진에서 확인했다」고 적지 않는다.
> **버전** — `api.webstatus.dev` 를 **2026-09-23 에 직접 조회**한 결과 **같은 문서 뷰 전환은 Baseline `newly`**(저변 도달 2025-10-14)다 — Chrome 2023-03-07 · Safari 2024-09-16 · **Firefox 2025-10-14**. **문서 간 전환은 아직 `limited`**(Firefox 미구현)이고 이 편은 같은 문서 전환까지만 다룬다.\
> **문서 간 전환(`@view-transition`)은 여전히 `limited`** — Chrome 2024-06-11 · Safari 2024-12-11 · Firefox 없음. 이 문서는 **같은 문서 전환까지만** 다루고 문서 간은 존재와 Baseline 만 적는다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**바뀌기 직전 화면을 사진으로 찍어 두고, 바뀐 뒤 화면과 겹쳐 놓은 다음, 그 사진 둘을 애니메이션한다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 연극의 암전 | DOM 을 바꾸는 순간 — 화면 갱신이 잠깐 멈춘다 |
| 막이 내리기 직전 사진 | `::view-transition-old(<이름>)` — 옛 화면의 스냅숏 |
| 막이 오른 뒤 사진 | `::view-transition-new(<이름>)` — 새 화면 |
| 두 사진을 겹쳐 든 액자 | `::view-transition-image-pair(<이름>)` |
| 액자를 옮기고 늘이는 손 | `::view-transition-group(<이름>)` — 위치·크기를 애니메이션 |
| **배우에게 이름표를 붙인다** | `view-transition-name` — 이름이 붙은 것만 따로 논다 |
| 이름표가 없는 나머지 전부 | `root` 라는 이름 하나로 뭉뚱그려 크로스페이드 |

```text
  document.startViewTransition(콜백)

   ① 지금 화면을 찍는다 (이름 붙은 요소마다 따로 + 나머지는 root 한 장)
        ↓
   ② 콜백을 실행한다 — DOM 이 바뀐다 (화면 갱신은 이 동안 멈춰 있다)
        ↓
   ③ 바뀐 화면을 찍는다
        ↓
   ④ 두 벌의 사진으로 의사 요소 트리를 만들어 문서 위에 덮는다
        ↓
   ⑤ UA 애니메이션을 돌린다 (기본 0.25초 크로스페이드 + 위치·크기 보간)
        ↓
   ⑥ 끝나면 트리를 통째로 걷어낸다
```

- **내가 전환을 「선언」하는 것이 아니다.** JS 로 **시작 시점을 알려 줘야** 한다 — `startViewTransition()` 이 유일한 방아쇠다.
- **CSS 는 그 뒤부터 일한다.** 만들어진 의사 요소에 `animation`·`transform` 을 걸어 연출을 바꾼다.
- **사진이라는 것이 핵심이다.** 전환 중에 보이는 것은 **살아 있는 요소가 아니라 그려 둔 그림**이다.

> **스냅숏(snapshot)** — 그 순간의 렌더 결과를 이미지처럼 떠 둔 것. 그 뒤 원본이 바뀌어도 그림은 안 바뀐다.\
> 예: 카드가 커지는 전환에서, 작던 시절의 카드는 **이미 사라진 DOM 의 그림**으로 남아 페이드아웃한다.

> **의사 요소 트리** — 전환 동안에만 존재하는, 문서 어디에도 마크업이 없는 요소들의 묶음.\
> 예: `::view-transition-group(card)` 는 `card` 라는 이름이 붙은 요소 하나당 한 개씩 생겼다 사라진다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 전환 동안 **무엇이 화면에 있나.** 진짜 요소인가 그림인가?
2. 같은 `view-transition-name` 이 **둘이면 어떻게 되나.**
3. 「레이아웃이 멈추는 구간」이 **정말 있나, 얼마나 되나.**

## 동작 방식

### (1) ★ 의사 요소 트리 — 도식이 본체다

**언제 쓰나** — 전환 연출을 바꾸려 할 때. **어디에 선택자를 걸지가 전부**다.

실측 — 이름 `card` 를 준 상자 하나와 이름 없는 상자 하나를 두고 전환을 돌린 뒤,\
`document.getAnimations()` 로 UA 가 만든 애니메이션의 `effect.pseudoElement` 를 전부 뽑았다.

```text
  :root (html)
    └─ ::view-transition                         position: absolute (실측)
         ├─ ::view-transition-group(root)        ← 이름 없는 것 전부가 여기 뭉친다
         │    └─ ::view-transition-image-pair(root)     isolation: isolate (실측)
         │         ├─ ::view-transition-old(root)       mix-blend-mode: plus-lighter
         │         └─ ::view-transition-new(root)       mix-blend-mode: plus-lighter
         └─ ::view-transition-group(card)        ← view-transition-name: card 를 준 것
              └─ ::view-transition-image-pair(card)
                   ├─ ::view-transition-old(card)
                   └─ ::view-transition-new(card)
```

실행 중인 UA 애니메이션(실측 그대로):

```text
  ::view-transition-group(card)  -ua-view-transition-group-anim-card     250ms
     키프레임  width 120px,height 60px  ->  width 300px,height 160px
  ::view-transition-group(root)  -ua-view-transition-group-anim-root     250ms
     키프레임  900×357  ->  900×357        ★ 아무것도 안 바뀌는 애니메이션도 만들어진다
  ::view-transition-old(card)    -ua-view-transition-fade-out            250ms   opacity 1 -> 0
  ::view-transition-new(card)    -ua-view-transition-fade-in             250ms   opacity 0 -> 1
  ::view-transition-old/new(*)   -ua-mix-blend-mode-plus-lighter         250ms
```

그림 해설 (한 단계씩):

- **`group` 이 「움직임」을, `old`/`new` 가 「사라짐/나타남」을 맡는다.** 둘은 다른 의사 요소다.
- **`image-pair` 는 `isolation: isolate` 로 혼합을 가둔다.** `old`/`new` 가 `plus-lighter` 로 섞이는데, 그 혼합이 바깥으로 새면 안 되기 때문이다(정본은 [48번 주제](../48-blend-modes-and-isolation/2-summary.md)).
- **이름 없는 요소는 전부 `root` 한 장**에 들어간다. 실측에서 `view-transition-name` 을 지우니 의사 요소가 `root` 셋만 남았다.
- **아무것도 안 바뀌어도 애니메이션은 만들어진다**(`root` 의 900×357 → 900×357). 트리 모양은 변화 여부와 무관하다.

비용 — 이름 하나당 의사 요소 **넷**(group·image-pair·old·new)과 애니메이션 **넷**이 생긴다. 이름을 남발하면 그만큼 는다.

### (2) ★★ 기본 전환은 크로스페이드 — 그리고 `duration` 이 아래로 흐른다

**언제 쓰나** — 「0.25초가 너무 빠르다」를 고칠 때.

```text
  실측 — ::view-transition-group(card) { animation-duration: 1s } 만 선언했을 때의 계산값

    ::view-transition-group(card)        1s      ← 내가 선언한 곳
    ::view-transition-image-pair(card)   1s      ★ 따라왔다
    ::view-transition-old(card)          1s      ★ 따라왔다
    ::view-transition-new(card)          1s      ★ 따라왔다
    ::view-transition-group(root)        0.25s   ← 건드리지 않은 쪽은 그대로
    ::view-transition-old(root)          0.25s
```

- **`animation-duration` 은 상속되는 속성이 아니다.** 그런데 따라왔다.
- 이유는 **UA 스타일시트가 `old`/`new` 에 `animation-duration: inherit` 을 써 두었기 때문**이다.\
  덕분에 **`group` 하나만 건드리면 그 이름의 네 의사 요소가 같이 바뀐다.**
- 기본값은 **0.25초**이고 실제 애니메이션도 **250ms** 로 찍혔다.

★ **이징에는 관측 창이 둘 있고 답이 다르다.** 손으로 계산해 맞추려다 걸리는 자리다.

```text
  a.effect.getTiming().easing              "linear"    ← 효과 수준
  a.effect.getKeyframes()[0].easing        "ease"      ← 키프레임 수준  ★ 실제로 도는 것
```

- 실측 값이 등속이 아니었다 — 1초 전환의 169ms(16.9%) 시점에 폭이 **120 → 159.7px**(거리의 19.9%)였다.\
  **키프레임 쪽이 정답**이다. 효과 수준만 읽으면 `linear` 로 오해한다.

비용 — 없음.

### (3) `view-transition-name` 을 준 요소만 따로 논다

**언제 쓰나** — 「카드만 자라게 하고 나머지는 페이드」를 만들 때.

```text
  이름 있음                          이름 없음
  +---------------------------+     +---------------------------+
  | group(card) 가 따로 생김   |     | root 한 장에 섞여 들어감   |
  | 옛/새 크기를 보간해 '자란다'|     | 통째로 크로스페이드        |
  +---------------------------+     +---------------------------+
```

실측 — 같은 문서에서 이름만 지우고 다시 돌렸다.

```text
  이름 있을 때   group(root) · group(card) · old/new(root) · old/new(card)   (의사 요소 6종)
  이름 없을 때   group(root) · old/new(root)                                 (의사 요소 3종)
```

- **이름은 「이 요소를 따로 추적하라」는 표시**다. 이름이 있으면 옛 위치·크기에서 새 위치·크기로 **보간**된다.
- 그래서 **DOM 상의 자리가 바뀌어도 같은 이름이면 「그 요소가 옮겨간 것」으로 그려진다.** 목록에서 상세로 넘어가는 연출의 뼈대다.
- 이름은 **한 시점에 하나만** 존재해야 한다 — 다음 절이 그 이유다.

비용 — 이름을 준 요소는 **자기만의 쌓임 맥락처럼 따로 그려진다.** 전환 중에는 문서의 쌓임 순서가 아니라 **의사 요소 트리 순서**가 겹침을 정한다(정본은 [22번 주제](../22-stacking-context-and-z-index/2-summary.md)).

### (4) ★★ 이름이 겹치면 — 전환만 죽고 DOM 은 바뀐다

**언제 쓰나** — 「전환이 가끔 안 먹는다」를 볼 때. **목록 렌더링에서 가장 흔한 사고다.**

실측 — 두 요소에 같은 `view-transition-name: card` 를 준 뒤 전환을 돌렸다.

```text
  vt.ready               rejected   InvalidStateError: Transition was aborted because of invalid state
  vt.updateCallbackDone  resolved   ★ DOM 변경 콜백은 그대로 실행됐다
  vt.finished            resolved   ★ 실패가 아니라 '정상 종료'로 끝난다
  전환 뒤 실제 폭          120px      DOM 변경은 적용돼 있다
```

```text
  이름이 겹쳤을 때

   startViewTransition(콜백)
        ↓
   스냅숏을 뜨려다 '같은 이름이 둘'을 발견
        ↓
   전환을 건너뛴다 (ready 가 reject)
        ↓
   콜백은 그대로 실행 → DOM 은 바뀐다        ★ 화면은 그냥 '툭' 바뀐다
        ↓
   finished 는 resolve → 에러처럼 안 보인다
```

그림 해설 (한 단계씩):

- **화면은 애니메이션 없이 바뀐다.** 기능이 망가지지 않으므로 **버그로 안 보인다.**
- **`finished` 가 resolve 된다**는 것이 고약하다. `await vt.finished` 만 걸어 둔 코드는 **아무것도 눈치채지 못한다.**
- **잡으려면 `vt.ready` 를 봐야 한다.** 거기서만 `InvalidStateError` 가 나온다.
- `vt.skipTransition()` 으로 일부러 건너뛴 경우도 모양이 비슷하지만 **에러 이름이 다르다** — 실측에서 `ready` 가 **`AbortError`** 로 reject 됐다.

비용 — 없음. 진단 비용만 든다. **목록의 항목마다 고유한 이름**(`--card-3` 처럼)을 주는 것이 예방이다.

### (5) 한 프레임을 찍는 것 — 멈추는 구간은 얼마나 되나

**언제 쓰나** — 「전환을 걸었더니 버벅인다」를 판단할 때.

실측 — `startViewTransition()` 호출 시각을 0 으로 두고 각 단계를 찍었다.

```text
  t=15ms   첫 requestAnimationFrame 이 돈다
  t=17ms   콜백 진입                       ← 호출 프레임이 아니라 '다음 프레임'이다
  t=17ms   콜백 안에서 잰 카드 폭 = 300px   ★ DOM·레이아웃은 이미 새 값이다
  t=17ms   updateCallbackDone
  t=19ms   ready                            ← 의사 요소 트리가 준비됨
  t=299ms  finished                         ← 250ms 애니메이션 + 앞의 준비 시간
```

그리고 **전환이 도는 동안 진짜 요소를 읽어 봤다.**

```text
  getComputedStyle(card).width      "300px"      ← 이미 새 값
  getComputedStyle(card).visibility "visible"    ← 숨겨져 있지도 않다
  card.getBoundingClientRect()      300 × 160    ← 레이아웃도 새 값
```

그림 해설 (한 단계씩):

- **멈추는 것은 「화면 갱신」이지 「레이아웃」이 아니다.** 콜백 안에서 이미 새 좌표가 나온다.
- 이 환경에서 그 구간은 **약 2\~4ms**(콜백 17ms → ready 19ms)였다. **DOM 변경이 무거우면 그만큼 길어진다** — 그 사이 화면은 옛 그림으로 멈춰 있다.
- ★ **`getComputedStyle` 로는 「지금 전환 중」임을 알 수 없다.** 계산값은 벌써 새 값이고, 화면에만 스냅숏이 떠 있다.\
  **선언을 읽는 창과 화면을 보는 창이 여기서 갈린다** — 전환 중인지는 `document.getAnimations()` 에 `-ua-view-transition-*` 이 있는지로 안다.

비용 — **콜백을 가볍게 유지하는 것**이 이 기능의 유일한 성능 수칙이다. 콜백 안에서 네트워크를 기다리면 **그동안 화면이 얼어 있다.**

### (6) 문서 간 전환 — 존재와 Baseline 까지만

**언제 쓰나** — 멀티 페이지 앱에서 페이지를 넘길 때.

```css
/* 두 문서 모두에 선언해야 한다 */
@view-transition { navigation: auto; }
```

- JS 없이 **같은 출처의 문서 이동**에 전환을 건다. 나머지(`view-transition-name`·의사 요소 트리)는 같은 문법을 쓴다.
- ⚠️ **Baseline `limited` 다.** 2026-09-23 조회: Chrome 2024-06-11 · Safari 2024-12-11 · **Firefox 없음.**
- **이 문서에서는 실행하지 않았다.** 같은 문서 전환과 달리 두 문서의 탐색이 필요해 headless 한 판으로 재현하기 어렵다 — **존재와 Baseline 만** 적는다.

비용 — 미측정.

## demo — 이름이 붙은 것만 따로 자란다

```html demo
<button id="go">크기 바꾸기</button>
<div id="card">view-transition-name: card</div>
<style>
  #card { width: 120px; height: 60px; background: #1d4ed8; color: #fff;
          font: 13px system-ui; view-transition-name: card; }
  #card.big { width: 300px; height: 160px; background: #b91c1c; }
  ::view-transition-group(card) { animation-duration: 1s; }
</style>
<script>
  go.onclick = () => document.startViewTransition(() => card.classList.toggle('big'));
</script>
```

> **보이는 것** — 버튼을 누르면 파란 상자가 **1초에 걸쳐** 120×60 에서 300×160 으로 자라면서 색이 파랑에서 빨강으로 **겹쳐 바뀐다**(옛 그림이 흐려지고 새 그림이 진해진다). 다시 누르면 반대로 줄어든다.\
> 움직임은 **버튼을 눌러야만** 일어난다 — 안 누르면 아무것도 안 움직인다.\
> **바꿔 볼 것** — `animation-duration: 1s` → `4s` 로 늘리면 → 1.16초 시점에 아직 **207.9px** 로 가는 중이다 · `#card` 에서 `view-transition-name: card` 를 지우면 → 의사 요소가 `root` 셋만 생기고 **상자만 따로 자라는 대신 화면 전체가 크로스페이드**된다

*(Chrome 151 headless 실측 — `::view-transition-group(card)` 의 폭과 `old`/`new` 의 불투명도:)*

```text
  t=12ms     120px       old 1        new 0
  t=169ms    159.703px   old 0.779    new 0.221
  t=319ms    218.188px   old 0.454    new 0.546
  t=485ms    261.344px   old 0.215    new 0.785
  t=635ms    283.141px   old 0.094    new 0.906
  t=935ms    299.547px   old 0.002    new 0.998
  t=1101ms   (의사 요소 없음 — 트리가 걷혔다)

  전환 중 존재한 의사 요소 6종
    ::view-transition-group(root) · group(card)
    ::view-transition-old(root) · new(root) · old(card) · new(card)

  바꿔 볼 것 ① duration 4s        t=1157ms 에 207.875px (아직 진행 중)
  바꿔 볼 것 ② 이름 제거           의사 요소가 group(root)·old(root)·new(root) 셋뿐
```

## 문법 — 형태와 규칙

CSS 는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태

```css
/* ① 이름 붙이기 — 이것이 CSS 쪽의 전부다 */
.card { view-transition-name: card; }        /* none 이 기본 */

/* ② 의사 요소 — 루트 요소에 붙는다 */
::view-transition                            /* 전체를 덮는 컨테이너 */
::view-transition-group(<이름> | *)
::view-transition-image-pair(<이름> | *)
::view-transition-old(<이름> | *)
::view-transition-new(<이름> | *)

/* ③ 문서 간 전환 (Baseline limited) */
@view-transition { navigation: auto | none; }
```

```js
// ④ 방아쇠는 JS 하나뿐이다
const vt = document.startViewTransition(() => { /* DOM 변경 */ });
vt.ready               // 의사 요소 트리가 준비됨 — ★ 실패는 여기서만 보인다
vt.updateCallbackDone  // 콜백이 끝남
vt.finished            // 애니메이션까지 끝남
vt.skipTransition()    // 건너뛰기 (ready 가 AbortError 로 reject)
```

### 금지 사례 — 던져서 확인한 것

```css
/* ✗ 같은 이름을 둘 이상의 요소에 — 전환이 통째로 건너뛰어진다 */
.card-1, .card-2 { view-transition-name: card; }

/* ✗ ::view-transition-old(card) 에 duration 만 따로 주고 group 은 그대로 두기
      -> group 의 이동은 0.25초, 페이드만 길어져 따로 논다 */
```

```js
// ✗ await vt.finished 만 걸어 두기 — 이름 충돌을 영영 모른다 (finished 가 resolve 된다)
```

### 어디서 헷갈리나

- **의사 요소는 루트에 붙는다.** `getComputedStyle(el, '::view-transition-group(card)')` 이 아니라 **`document.documentElement`** 에 물어야 한다.
- **`old`/`new` 는 이미지다.** 그 안의 텍스트를 선택자로 잡을 수 없다 — 그림 한 장이다.
- **`group` 이 위치·크기, `old`/`new` 가 불투명도**다. 「안 움직인다」와 「안 사라진다」는 고칠 자리가 다르다.
- **`*` 를 쓸 수 있다.** `::view-transition-group(*)` 은 모든 이름에 걸린다.
- **`view-transition-name` 은 상속되지 않는다.** 자손에게 따로 줘야 한다.

## 어디서 틀리나

### 1. ★★ 같은 이름을 둘에 준다

**전환만 죽고 DOM 은 바뀐다.** `finished` 가 resolve 되므로 에러처럼 안 보인다(동작 방식 (4)).\
목록을 렌더할 때 `view-transition-name: card` 를 **모든 항목에** 주면 정확히 이 모양이 된다. 항목마다 고유 이름을 준다.

### 2. `vt.ready` 를 안 본다

실패가 드러나는 유일한 창이다. `ready` 를 `catch` 하지 않으면 **처리되지 않은 프라미스 거부**까지 같이 난다.

### 3. 콜백 안에서 기다린다

콜백이 끝날 때까지 **화면이 옛 그림으로 멈춰 있다**(동작 방식 (5)). 데이터는 **콜백 밖에서 먼저 받아 두고** 콜백은 DOM 만 갈아 끼운다.

### 4. `duration` 을 `old`/`new` 에만 준다

`group` 은 0.25초 그대로라 **이동은 빨리 끝나고 페이드만 늘어진다.** `group` 에 주면 `inherit` 으로 아래까지 따라온다.

### 5. 이징을 `getTiming().easing` 으로 읽는다

`linear` 로 나오지만 **실제로 도는 것은 키프레임 수준의 `ease`** 다(동작 방식 (2)). 손계산이 안 맞는다.

### 6. 전환 중인지를 계산값으로 판단한다

`getComputedStyle` 은 이미 **새 값**을 답한다. 화면에만 스냅숏이 떠 있다. 전환 중인지는 `document.getAnimations()` 로 본다.

### 7. 문서 간 전환을 같은 것으로 여긴다

`@view-transition` 은 **Baseline limited** 이고 Firefox 에 없다. 같은 문서 전환(newly)과 지원 폭이 다르다.

## 구현 세부사항 대 언어 보장

| 항목 | 누가 보장하나 |
|---|---|
| 의사 요소 트리의 **모양과 이름** | **명세**(css-view-transitions-1) |
| 이름이 없는 것이 `root` 로 묶이는 것 | **명세** |
| 같은 이름이 둘이면 전환을 **건너뛰는 것** | **명세** |
| 기본 지속 **0.25초**·크로스페이드 | **명세의 UA 스타일시트** — 다만 값은 구현이 바꿀 수 있다 |
| `old`/`new` 가 `duration` 을 **`inherit`** 하는 것 | **명세의 UA 스타일시트** + Chrome 151 실측 |
| UA 애니메이션 이름 `-ua-view-transition-fade-in` 등 | **Chrome 151 관찰.** `-ua-` 접두는 구현 내부 이름이다 — **선택자로 쓰지 마라** |
| `::view-transition` 의 `position: absolute` | **Chrome 151 관찰**(명세 UA 시트와 대조하지 않았다) |
| 오류 메시지 `InvalidStateError: Transition was aborted because of invalid state` | **Chrome 151 문구.** 오류 **이름**은 명세, 문장은 구현 |
| 콜백까지 17ms · ready 까지 19ms | **이 머신의 한 판**이다. 프레임 경계와 DOM 무게에 달려 있다 |
| 같은 문서 전환의 지원 | **Baseline newly**(2025-10-14, 2026-09-23 조회) |
| 문서 간 전환의 지원 | **Baseline limited** — Firefox 없음 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓰나 | 왜 |
|---|---|---|
| 목록 → 상세로 넘어가며 카드가 자라는 연출 | **쓴다** | 이 기능이 만들어진 이유다. 항목마다 **고유 이름** |
| 탭 전환·정렬 순서 변경 | **쓴다** | DOM 이 통째로 바뀌어도 이름으로 따라간다 |
| 다크 모드 토글 | 쓴다 | 이름 없이 `root` 크로스페이드만으로 충분 |
| 입력 중인 폼이 걸린 화면 | **안 쓴다** | 전환 중에는 스냅숏이라 **입력이 멈춘 것처럼 보인다** |
| 매우 잦은 갱신(실시간 목록) | 안 쓴다 | 매번 스냅숏을 뜨는 비용이 든다 |
| 두 값 사이만 오가는 상태 변화 | 안 쓴다 | [52번](../52-transition/2-summary.md)·[57번](../57-starting-style-and-entry-exit-transitions/2-summary.md) 주제로 충분하다 |

## 핵심 문장

- **전환 중에 보이는 것은 살아 있는 요소가 아니라 그려 둔 그림 두 장이다.**
- **`group` 이 위치·크기를, `old`/`new` 가 사라짐·나타남을 맡는다.** 고칠 자리가 다르다.
- **이름을 준 것만 따로 논다.** 나머지는 `root` 한 장에 뭉친다.
- **이름이 겹치면 전환만 죽고 DOM 은 바뀐다.** `finished` 가 resolve 되므로 `ready` 를 봐야 안다.
- **멈추는 것은 화면 갱신이지 레이아웃이 아니다.** 콜백 안에서 이미 새 좌표가 나온다.
- **같은 문서 전환은 Baseline newly, 문서 간은 limited** — 같은 기능처럼 다루지 않는다.

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 59번)
- [`../22-stacking-context-and-z-index/2-summary.md`](../22-stacking-context-and-z-index/2-summary.md) — **쌓임 맥락의 정본.**\
  `z-index` 와 쌓임 순서의 규칙은 **거기까지**, 여기는 **전환 중에는 문서의 쌓임이 아니라 의사 요소 트리 순서가 겹침을 정한다는 것**부터.
- [`../13-pseudo-elements-and-generated-content/2-summary.md`](../13-pseudo-elements-and-generated-content/2-summary.md) — 의사 요소 일반의 정본. `::view-transition-*` 은 **마크업이 없고 전환 중에만 존재**한다는 점이 다르다.
- [목록의 **53번 주제**](../53-keyframes-and-animation/)(`@keyframes`·`animation`) — 의사 요소에 거는 애니메이션의 문법은 거기.
- [48번 주제](../48-blend-modes-and-isolation/2-summary.md)(혼합 모드와 `isolation`) — `image-pair` 가 `isolate` 를 쓰는 이유.
- [`../52-transition/2-summary.md`](../52-transition/2-summary.md) · [`../57-starting-style-and-entry-exit-transitions/2-summary.md`](../57-starting-style-and-entry-exit-transitions/2-summary.md) — 같은 요소가 **제자리에서** 바뀌는 경우. 스냅숏을 안 뜬다.
- [`../58-scroll-driven-animations/2-summary.md`](../58-scroll-driven-animations/2-summary.md) — 진행률이 스크롤에서 오는 경우. 뷰 전환은 **시간 기반**이다.
- [`../60-prefers-reduced-motion/2-summary.md`](../60-prefers-reduced-motion/2-summary.md) — **모션 접근성의 정본.**\
  뷰 전환은 **화면 전체가 움직이는** 연출이라 특히 줄일 대상이다. 판단과 구체 형태는 거기.
- [`../../../../../../reference/render-rules.md`](../../../../../../reference/render-rules.md) — demo 블록 규칙.

## 용어 풀이

- **뷰 전환(view transition)** — DOM 변경 전후의 화면을 스냅숏으로 떠서 애니메이션하는 기능.
- **스냅숏** — 그 순간의 렌더 결과를 이미지처럼 떠 둔 것. 원본이 바뀌어도 안 바뀐다.
- **`view-transition-name`** — 「이 요소를 따로 추적하라」는 이름표. `none` 이 기본이고 상속되지 않는다.
- **`::view-transition`** — 전환 트리 전체를 덮는 컨테이너 의사 요소. 루트에 붙는다.
- **`::view-transition-group(<이름>)`** — 위치·크기를 애니메이션하는 층.
- **`::view-transition-image-pair(<이름>)`** — 옛·새 그림을 겹쳐 드는 액자. `isolation: isolate` 로 혼합을 가둔다.
- **`::view-transition-old(<이름>)` / `-new(<이름>)`** — 옛 화면·새 화면의 그림. 불투명도를 맡는다.
- **`root`** — 이름을 안 준 나머지 전부가 묶이는 기본 이름.
- **`startViewTransition()`** — 전환의 유일한 방아쇠. `ready`·`updateCallbackDone`·`finished` 세 프라미스를 준다.
- **`ready`** — 의사 요소 트리가 준비됐을 때 resolve. **실패가 드러나는 유일한 창.**
- **`@view-transition`** — 문서 간 전환을 켜는 규칙. Baseline limited.

## 더 들어가면

- `::view-transition-group(*)` 처럼 **`*` 로 전체에** 거는 형태가 있다. `:only-child` 로 「새 그림만 있는 경우」를 가르는 선택자도 명세에 있다.
- `view-transition-class`(Level 2)로 여러 이름에 **같은 연출을 묶어** 주는 방법이 있다. **이 문서에서는 다루지 않았다.**
- 전환 중의 겹침 순서는 **`::view-transition-group` 들의 생성 순서**로 정해지며, `z-index` 를 그 의사 요소에 직접 주어 바꿀 수 있다.
- 콜백이 프라미스를 돌려주면 **그것이 resolve 될 때까지 화면이 멈춘다.** 서버 왕복을 콜백 안에 넣지 않는 이유다.

# css/syntax/57 — `@starting-style` 과 진입·퇴장 전환: `display`/`overlay` 를 전환에 태우기 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 값은 Google Chrome 151.0.7922.173 headless 에서 실제로 측정한 것**이다.\
> CDP 로 `Input.dispatchMouseEvent` 를 던져 실제 마우스를 움직이고, `requestAnimationFrame` 마다 `getComputedStyle` 과 `getAnimations()` 를 읽었다(샘플 시각은 ±1프레임 오차).\
> 규칙은 [CSS Transitions Level 2](https://drafts.csswg.org/css-transitions-2/) · [CSS Position Level 4](https://drafts.csswg.org/css-position-4/) 로 접지했다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 이 드롭다운은 왜 열릴 때만 튀는가

**실행 결과** (Chrome 151 headless — `.a` 가 `@starting-style` 없는 쪽, `.b` 가 있는 쪽)

```text
  진입      t=7ms    a=1      b=0.017
            t=322ms  a=1      b=0.333
            t=622ms  a=1      b=0.633
            t=1088ms a=1      b=1

  퇴장      t=16ms   a=0.983  b=0.983   (display: block)
            t=616ms  a=0.383  b=0.383   (display: block)
            t=1066ms a=0      b=0       (display: none)
```

**1초에 걸쳐 나타나는가**

- **아니다. 첫 프레임(7ms)에 이미 `opacity: 1` 이다.** `getAnimations()` 도 빈 배열이었다 — 전환 객체가 아예 안 만들어졌다.

**뗐을 때는**

- **1초에 걸쳐 흐려진다.** 이때는 `opacity: 1` 이라는 **이전 값이 실제로 존재**하기 때문이다.

**무엇이 그 차이를 만드는가**

```text
  퇴장          이전 값 1  →  도착 값 0        두 값이 다르다  ->  전환 시작
  진입          이전 값 ??? →  도착 값 1        이전 값이 없다  ->  전환 없음
                      ^
        display: none 이던 요소는 렌더 트리에 없어서 '바뀌기 전 계산값' 자체가 없다
```

- 명세가 말하는 **before-change style 이 없는 상태**다. `@starting-style` 이 그 자리를 채워 준다.

**에러나 경고가 찍히는가**

- **아무것도 안 찍힌다.** CSS 는 에러가 없는 언어다 — 선언은 전부 유효하고 전환만 시작되지 않는다.

### 2. 한 프레임만 존재하는 상태를 무엇으로 보는가

**`getComputedStyle` 로 볼 수 있는가**

- **평소에는 못 본다.** 토글 전 세 상자의 계산값이 완전히 같았다.

```text
  b1 opacity=1 display=none · b2 opacity=1 display=none · b3 opacity=1 display=none
     (@starting-style 없음)     (바깥 형태 있음)            (중첩 형태 있음)
```

- 토글한 **같은 태스크 안에서** 바로 읽으면 딱 한 프레임 보이지만(`b2` 가 `"0"`), 다음 틱이면 이미 보간값이라 **재현되는 근거가 못 된다.**

**`cssRules` 에는**

```text
  CSSStyleRule          .box { … opacity: 1; display: none; transition: … }
  CSSStyleRule          .box.on { display: block; }
  CSSStartingStyleRule  @starting-style { #b2.on { opacity: 0; } }
  CSSStyleRule          #b3 { @starting-style { opacity: 0; } }
```

- **규칙이 담겼다는 것까지만** 알려 준다. 담겼는데 캐스케이드에서 지는 경우(A3 의 d2·d3)를 못 가른다.

**재현 가능하게 증명하려면**

- **`el.getAnimations()`** 를 읽는다. 빈 배열이면 전환이 시작조차 안 한 것이다.

```text
  b1 : []                                          <- 전환 없음
  b2 : CSSTransition(opacity) 키프레임 0:"0" -> 1:"1"
  b3 : CSSTransition(opacity) 키프레임 0:"0" -> 1:"1"
```

**엔진이 만든 값임을 어떻게 아는가**

- `getKeyframes()` 는 **엔진이 전환을 만들 때 확정한 시작·끝 값을 그대로** 돌려준다. 내가 해석하거나 계산해 넣을 자리가 없다.
- 그래서 이 주제의 진단 창은 **넷**이다 — `cssRules`(담겼나) · `querySelectorAll`(잡았나) · `getComputedStyle`(흔적 없음) · **`getAnimations()`(엔진이 실제로 쓴 값)**.

### 3. 이 둘 중 어느 쪽이 전환되는가

**출력** (Chrome 151 headless)

```text
  d1  일반 먼저 → starting 나중     키프레임 0:0.2 -> 1:0.8      ★ 걸린다
  d2  starting 먼저 → 일반 나중     (전환 없음)                  ★ 안 걸린다
```

**전환이 걸리는 쪽**

- **d1** 이다. 같은 명시도라면 **뒤에 쓴 쪽이 이긴다.**

**안 걸리는 쪽의 시작값**

- **0.8** — 도착값과 같아진다. 값이 안 바뀌었으니 전환이 시작될 이유가 없다.

**명세의 어떤 문장인가**

> The rules inside @starting-style cascade as any other grouped style rules without introducing any new ordering to the cascade, which means rules inside @starting-style do not necessarily win over those outside.

**습관으로 만들 규칙**

- **`@starting-style` 블록은 경쟁하는 일반 규칙보다 항상 뒤에 둔다.** 파일 맨 아래에 모아 두면 d2 사고가 구조적으로 안 난다.

### 4. 명시도와 중요도가 끼면

**출력**

```text
  d3  starting (0,1,0) vs 일반 (1,0,0)        (전환 없음)
  d4  starting (1,0,0) vs 일반 (0,1,0)        키프레임 0:0.2 -> 1:0.8
  d5  starting 에 !important, 일반은 평범      키프레임 0:0.2 -> 1:0.8
```

**전환이 걸리는 것은 몇 개인가**

- **둘**(d4·d5)이다. d3 은 명시도로 졌다.

**`@starting-style` 안이라는 사실은 어디에 끼어드나**

- **어디에도 안 끼어든다.** 그 점이 이 질문의 답 전부다.

**우선순위 네 단계**

```text
   레이어(@layer)  ->  중요도(!important)  ->  명시도  ->  소스 순서
```

- 보통의 캐스케이드와 **완전히 같다**([01번](../01-cascade-and-priority/2-summary.md)·[02번](../02-specificity/2-summary.md) 주제).

### 5. 이미 보이는 요소에 걸면

**출력** (처음부터 렌더돼 있던 `opacity: 1` 요소에 `@starting-style { opacity: 0 }` 을 주고 `.on`(`opacity: .5`)을 붙였다)

```text
  키프레임   0:1 -> 1:0.5     <- 시작값이 0 이 아니라 원래 값 1
  계산값     1
```

**시작값**

- **원래 있던 값(1)** 이다. `@starting-style` 은 **통째로 무시된다.**

**명세는 뭐라 부르나**

> If an element does not have a before-change style for a given style change event, the starting style is used instead of the before-change style to compare with the after-change style to start transitions.

- 조건은 **「before-change style 이 없을 때」** 하나다.

**실제로 쓰이는 두 경우**

1. **렌더되지 않던 요소가 렌더되기 시작할 때** — `display: none` → `block`, 팝오버·`<dialog>` 가 열릴 때.
2. **DOM 에 방금 꽂힌 요소** — JS 로 만들어 붙인 토스트 등.

### 6. 퇴장에서 `display` 는 언제 뒤집히는가

**출력** (0.6초 전환, 팝오버를 닫는 판)

```text
  t=14ms    display: block   opacity: 1
  t=314ms   display: block   opacity: 0.50     <- 50% 지점에도 block
  t=614ms   display: block   opacity: 0.0000117
  t=764ms   display: none    opacity: 0
```

**명세가 말하는 뒤집는 지점**

> When values with a discrete animation type are transitioned, they flip at 50% progress.

**실제로는**

- **끝난 뒤(≈764ms)에 `none` 이 됐다.** 50% 가 아니다.

**왜 예외인가**

```text
  50% 에서 뒤집으면           끝에서 뒤집으면
  +-------------------+       +-------------------+
  | 0.3초 뒤 사라짐    |       | 0.6초 내내 보임    |
  | 남은 0.3초는       |       | 다 사라진 뒤 none  |
  | 그릴 대상이 없다    |       |                   |
  +-------------------+       +-------------------+
        페이드가 반만 보인다        의도대로 보인다
```

- 한쪽 끝이 `display: none` 인 전환에서는 **「보이는 쪽」이 전 구간을 차지한다.** 나타날 때는 처음부터 `block`, 사라질 때는 끝까지 `block` 이다.
- 실제로 **나타날 때는 `display` 전환 객체가 만들어지지도 않았다** — 여는 판의 `getAnimations()` 는 `["opacity 0:0->1:1"]` 하나뿐이었고, 닫는 판에서만 `["display", "opacity", "overlay"]` 셋이 나왔다.

**`allow-discrete` 를 빼면**

- **15ms 에 이미 `display: none`·`opacity: 0`** 이었다. 퇴장 전환이 통째로 사라진다.

### 7. `overlay` 를 빼면 무엇이 달라지는가

**출력** (A = `overlay` 포함, B = 미포함. 둘 다 `display … allow-discrete` 는 있다)

```text
  hidePopover() 직후 만들어진 전환 목록
    A -> ["display", "opacity", "overlay"]
    B -> ["display", "opacity"]

     t        A (overlay/display)     B (overlay/display)
     16ms     auto/block              none/block      <- B 는 벌써 최상위 레이어 밖
     316ms    auto/block              none/block
     516ms    auto/block              none/block
     616ms    none/none               none/none
```

**뒤로 숨는 이유**

- `display` 는 붙들었지만 **최상위 레이어에서는 16ms 만에 내려왔다.** 그 뒤 0.6초 동안 B 는 **보통 요소**라서 조상의 쌓임 맥락·`overflow` 에 다시 갇힌다.

**저자가 값을 지정할 수 있는가**

- **없다.** `auto`/`none` 은 브라우저가 정하고, 저자는 **전환 목록에 태울 수만** 있다.

**무엇을 붙들어 주나**

- **최상위 레이어에 머무는 시간**이다. 「보이느냐」가 아니라 「어느 층에 그려지느냐」를 붙든다.

**지원 안 되는 엔진에서는**

- 그 한 줄이 **조용히 버려지고 나머지는 그대로 돈다.** 깨지지 않고 **퇴장 중 겹침만 달라진다.** Baseline **limited**(Chromium 전용, 2026-09-23 조회).

### 8. 두 형태는 정말 같은가

**결과는 같은가**

- **같다.** 실측에서 바깥 형태(`b2`)와 중첩 형태(`b3`)가 **같은 키프레임**(`0:"0" -> 1:"1"`)을 냈고, 시각별 값도 소수점까지 같았다.

```text
  t=100ms  b2=0.083327  b3=0.083327
  t=500ms  b2=0.483327  b3=0.483327
  t=1000ms b2=0.983327  b3=0.983327
```

**중첩 형태의 명시도**

- **바깥 규칙의 명시도**다. `#b3 { @starting-style { opacity: 0 } }` 의 선언은 `(1,0,0)` 으로 경쟁한다.

**CSSOM 에서의 차이**

```text
  바깥 형태   CSSStartingStyleRule :: @starting-style { #b2.on { opacity: 0; } }
  중첩 형태   CSSStyleRule         :: #b3 { @starting-style { opacity: 0; } }
```

- 바깥 형태만 **최상위에 `CSSStartingStyleRule` 로** 보인다. 중첩 형태는 `CSSStyleRule` 안에 들어가 있다.

### 9. 지금 써도 되는가

**Baseline** (`api.webstatus.dev` 2026-09-23 조회)

| 기능 | Baseline | 엔진별 |
|---|---|---|
| `@starting-style` | **newly** (2024-08-06) | Chrome 2023-09 · Safari 2024-05 · Firefox 2024-08 |
| `transition-behavior` | **newly** (2024-08-06) | Chrome 2023-09 · Safari 2024-03 · Firefox 2024-08 |
| `overlay` | **limited** | **Chrome·Edge 2023-09 뿐.** Firefox·Safari 없음 |

**가장 좁은 것**

- **`overlay`** 이고, Chromium 계열에만 있다.

**깨지는가, 조용히 다르게 도는가**

- **조용히 다르게 돈다.** 무효한 선언은 버려지고 나머지 규칙은 그대로 적용된다([07번 주제](../07-syntax-and-error-recovery/2-summary.md)의 오류 복구).
- 그래서 **진입 전환이 없으면 즉시 나타나고, 퇴장 전환이 없으면 즉시 사라진다** — 동작은 유지되고 연출만 없어진다. 대체 경로를 따로 짤 필요가 대개 없다.

### 10. 다른 주제와 잇기

**`height: auto` 아코디언**

- **안 걸린다.** `@starting-style` 은 **출발값을 만들어 줄 뿐**이고, `auto` 는 여전히 보간할 수 없다.
- 내용 높이를 모르는 채로 펴려면 `grid-template-rows: 0fr ↔ 1fr` 을 쓴다. 정본은 [52번 주제](../52-transition/2-summary.md)와 [27번 주제](../27-grid-track-sizing/2-summary.md).

**전환 중의 값을 `!important` 로 덮을 수 있는가**

- **없다.** 전환 중의 값은 캐스케이드 사다리의 **맨 위**에 있다. 정본은 [01번 주제](../01-cascade-and-priority/2-summary.md).
- 단 **시작 스타일을 정하는 단계는 다르다** — 거기서는 `!important` 가 평소대로 작동한다(A4 의 d5).

**여러 지점을 들르는 등장**

- **`@keyframes` + `animation`** 이다. 전환은 두 점만 안다. 정본은 [목록의 **53번 주제**](../53-keyframes-and-animation/).
- 애니메이션에는 `@starting-style` 이 필요 없다 — **시작값을 키프레임이 직접 들고 있다.**

**모션에 민감한 사용자에게는**

- 진입·퇴장의 **이동·확대는 줄이고 불투명도 전환만 남긴다.** 정본은 [60번 주제](../60-prefers-reduced-motion/2-summary.md).

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless(`--headless=new`). **엔진은 이것 하나다**(Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고, WebKit 은 없다).

**한 프레임 상태를 잡은 방법** — `--virtual-time-budget` 을 쓰지 않았다(가상 시간이 먼저 흘러 「아무 일도 안 일어남」이 찍힌다). CDP 에 붙어 매 판 `Page.navigate` 로 다시 띄우고, 토글 **직후 같은 태스크 안에서** `getAnimations()` 를 읽어 전환 객체와 키프레임을 회수했다.

```js
// 관측 하네스의 핵심 (57 전용)
window.go = function(){
  for (const id of ids) document.getElementById(id).classList.add('on');   // 토글
  for (const id of ids){                                                    // 같은 태스크 안에서
    const e = document.getElementById(id);
    anims[id] = e.getAnimations().map(a => ({
      cls: a.constructor.name, prop: a.transitionProperty,
      kf: a.effect.getKeyframes().map(k => k.offset + ':' + k.opacity)      // ★ 시작 스타일
    }));
  }
};
```

```bash
google-chrome --headless=new --no-sandbox --disable-gpu --hide-scrollbars \
  --force-device-scale-factor=1 --remote-allow-origins=* \
  --remote-debugging-port=9334 --window-size=900,500 about:blank
# /json → webSocketDebuggerUrl → Page.enable/Runtime.enable → Page.navigate → Runtime.evaluate
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 바깥·중첩·없음 세 상자 토글 + `cssRules`·`getAnimations()`·rAF 샘플 | 1 | 동작 방식 (1)·(2) · A1 · A2 · A8 |
| 캐스케이드 c1\~c5 (설계 오류로 폐기 — 도착값이 안 바뀌었다) | 1 | — (A3 의 전제를 다시 세움) |
| 캐스케이드 d1\~d5 (순서·명시도·중요도) | 1 | 동작 방식 (3) · A3 · A4 |
| 이미 렌더된 요소 + `@starting-style` | 2 | 동작 방식 (4) · A5 |
| 팝오버 열기/닫기 rAF 샘플(`opacity`/`display`/`overlay`) | 1 | 동작 방식 (5)·(7) · A6 |
| `overlay` 있음/없음 A·B 대조 (`popover=manual` 로 재실행) | 2 | 동작 방식 (6) · A7 |
| demo 진입·퇴장 (CDP 실제 마우스 이동) | 1 | demo · A1 |
| demo 「바꿔 볼 것」 ① `@starting-style` 을 앞으로 | 1 | demo |
| demo 「바꿔 볼 것」 ② `allow-discrete` 제거 | 1 | demo · A6 |
| Baseline 조회(`@starting-style`·`transition-behavior`·`overlay`) | 1 | 머리말 · A9 |
| **제출 직전 demo 재추출·재실행 대조** | 1 | 어긋남 0건 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| `getKeyframes()` 의 직렬화 | `opacity: "0"` / `"1"` | CSSOM 직렬화 세부 |
| 나타날 때 `display` 전환 객체를 **안 만드는 것** | 여는 판 `["opacity"]` | 결과는 명세와 맞지만 객체 생성은 구현 선택 |
| `display` 가 `none` 이 되는 시각 | 0.6초 전환에서 ≈764ms | 프레임 경계에 걸린다 |
| `overlay` 지원 | Chromium 전용 | Baseline limited — 버전이 오르면 다시 조회 |
| 보간 소수점(`0.0000117`) | — | 부동소수 표현 |
| Baseline 값 | 2026-09-23 조회 | `api.webstatus.dev` 는 **2차 집계**다 |

**한 번 헛다리를 짚은 것** — `overlay` A/B 대조의 첫 판에서 팝오버 둘을 `popover`(auto)로 만들었더니 **둘째를 열면서 첫째가 자동으로 닫혔다.** A 가 처음부터 `none/none` 으로 찍혀 「`overlay` 를 쓰면 안 열린다」로 읽힐 뻔했다. `popover=manual` 로 바꿔 재실행한 값이 본문의 것이다.

**안 돌려 본 것** — ① Firefox·Safari 에서의 재현(엔진이 없다). ② `content-visibility` 를 `allow-discrete` 로 태우는 것(「더 들어가면」에 **존재만** 적었고 값을 주장하지 않았다).

**못 잰 것** — 시작 스타일을 **`getComputedStyle` 로 재현 가능하게** 읽는 것. 토글과 같은 태스크에서는 한 번 읽히지만 다음 틱이면 이미 보간값이라 **같은 값이 두 번 나오지 않는다.** 그래서 본문의 근거는 전부 `getAnimations()` 쪽이고, 계산값 쪽은 「흔적이 없다」는 **부재의 근거**로만 썼다.

## 용어 풀이

- **시작 스타일(starting style)** — 이전 값이 없을 때 「바뀌기 전 값」 자리에 쓰이는 스타일.
- **`@starting-style`** — 시작 스타일을 선언하는 규칙. 바깥 형태와 중첩 형태가 있고 **캐스케이드는 평소와 같다.**
- **before-change style** — 값이 바뀌기 직전의 계산 스타일. 이것이 **없을 때만** 시작 스타일이 쓰인다.
- **discrete(이산) 타입** — 중간값 없이 툭 바뀌는 애니메이션 타입. 기본은 50% 에서 뒤집힌다.
- **`transition-behavior: allow-discrete`** — 이산 속성도 전환 목록에 태우는 값.
- **`overlay`** — 요소가 최상위 레이어에 있는지를 나타내는 속성. 저자는 **전환에 태울 수만** 있다.
- **최상위 레이어(top layer)** — 모든 쌓임 맥락 위에 따로 그려지는 층.
- **`getAnimations()`** — 그 요소의 애니메이션·전환 객체 목록. **빈 배열 = 전환이 시작 안 했다.**
- **`getKeyframes()`** — 전환 객체가 실제로 쓰는 시작·끝 값. 시작 스타일을 잡는 창.
- **`CSSStartingStyleRule`** — 바깥 형태 `@starting-style` 의 CSSOM 타입.
- **팝오버(popover)** — HTML `popover` 속성으로 최상위 레이어에 띄우는 요소. `popover=manual` 은 자동으로 안 닫힌다.

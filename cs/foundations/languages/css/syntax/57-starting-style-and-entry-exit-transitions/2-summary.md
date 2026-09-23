# css/syntax/57 — `@starting-style` 과 진입·퇴장 전환: `display`/`overlay` 를 전환에 태우기 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [CSS Transitions Level 2](https://drafts.csswg.org/css-transitions-2/) (`@starting-style`·`transition-behavior`·discrete 전환) · [CSS Position Level 4](https://drafts.csswg.org/css-position-4/) (`overlay`·최상위 레이어). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 값은 **Google Chrome 151.0.7922.173** headless 에 띄우고 **CDP 로 `Input.dispatchMouseEvent` 를 던져 실제 마우스를 움직인 뒤**, `requestAnimationFrame` 마다 `getComputedStyle` 과 **`element.getAnimations()`** 를 읽은 것이다. 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> **엔진은 Chrome 하나다** — Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고 WebKit 은 없다. 「두 엔진에서 확인했다」고 적지 않는다.
> **버전** — CSS 에 언어 버전은 없다. `@starting-style` 과 `transition-behavior` 는 Baseline **newly**(둘 다 2024-08-06, 아직 widely 아님). **`overlay` 는 Baseline `limited`** — Chromium 계열(Chrome/Edge 2023-09)뿐이고 Firefox·Safari 에 없다. `api.webstatus.dev` 를 **2026-09-23 에 직접 조회**한 값이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**전환은 「어디서 어디까지」를 알아야 걸린다. 처음 나타나는 요소에는 「어디서」가 없다.**

[52번 주제](../52-transition/2-summary.md)가 정본으로 정한 세 조건 중 셋째가 여기서 깨진다.\
`@starting-style` 은 그 없는 「어디서」를 **한 프레임짜리 가짜 출발점**으로 만들어 주는 규칙이다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 달리기 시합 | 전환 |
| 출발선 / 결승선 | 바뀌기 전 값(before-change style) / 바뀐 뒤 값 |
| **출발선이 안 그려져 있다** | 요소가 방금 나타나서 「이전 값」이 아예 없다 → 전환이 안 걸린다 |
| `@starting-style` | **출발선을 분필로 그려 주는 것** — 총성이 울리는 순간에만 존재한다 |
| `transition-behavior: allow-discrete` | 결승선을 통과할 때까지 **경기장 불을 안 끄는 것**(`display: none` 을 미룬다) |
| `overlay` | 그 불이 **무대 위 조명**이라는 것 — 최상위 레이어에 남아 있게 한다 |

```text
처음 나타나는 요소

  @starting-style 이 없을 때          @starting-style 이 있을 때
  +---------------------+            +---------------------+
  | display: none       |            | display: none       |
  | (렌더 트리에 없음)   |            | (렌더 트리에 없음)   |
  +----------|----------+            +----------|----------+
             |                                  | 한 프레임짜리 출발선
             |                                  v   opacity: 0
             |                       +---------------------+
             |                       | 시작 스타일(starting style)
             |                       +----------|----------+
             v 한 프레임                        v 1초 동안 보간
  +---------------------+            +---------------------+
  | opacity: 1 (툭)     |            | opacity: 1 (서서히)  |
  +---------------------+            +---------------------+
```

실무에서 이게 터지는 자리는 **드롭다운·토스트·모달**이다.\
닫힐 때는 잘 사라지는데 **열릴 때만 툭 튀어나온다**. 에러도 경고도 없다.

> **시작 스타일(starting style)** — 요소가 처음 렌더될 때 「바뀌기 전 값」 자리에 쓰이는 스타일.\
> 예: `@starting-style { opacity: 0 }` 이면 그 요소는 `opacity: 0` 에서 출발한 것처럼 전환한다.

> **최상위 레이어(top layer)** — 페이지의 모든 쌓임 맥락 위에 따로 그려지는 층. 모달·팝오버가 여기 올라간다.\
> 예: `z-index: 99999` 를 준 조상 안에 있어도 최상위 레이어에 올라간 요소가 위에 그려진다([22번 주제](../22-stacking-context-and-z-index/2-summary.md)).

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **한 프레임만 존재하는 상태를 무엇으로 관측하나.** 평소 계산값에는 흔적이 없다.
2. `@starting-style` 안의 선언은 **캐스케이드에서 어디에 오나.** 자동으로 이기나?
3. 퇴장(사라질 때)은 왜 진입보다 **부품이 하나 더** 필요한가.

## 동작 방식

### (1) ★★ 한 프레임짜리 상태를 어떻게 잡나 — 관측 창 네 개

**언제 쓰나** — 이 주제의 모든 실측이 여기에 기댄다. **방법부터 세우고 시작한다.**

CSS 는 에러가 없는 언어라 「안 걸렸다」와 「안 담겼다」와 「졌다」가 **화면상 증상이 같다.**\
선택자 묶음에서 쓴 「진단 3창」에 **넷째 창**을 더해야 이 주제가 잡힌다.

```text
  창 ①  document.styleSheets[0].cssRules
        -> CSSStartingStyleRule 로 담겼나?            (규칙이 살아 있나)

  창 ②  querySelectorAll(선택자).length
        -> 그 선택자가 요소를 잡나?                    (매치가 있나)

  창 ③  getComputedStyle(el).opacity
        -> 평소 계산값에 흔적이 있나?                  ★ 없다. 항상 도착값이다

  창 ④  el.getAnimations()[0].effect.getKeyframes()
        -> 전환 객체의 offset 0 키프레임 = 시작 스타일  ★ 여기서만 보인다
```

실측 — 세 상자에 같은 `transition` 을 주고 `display: none` → `block` 으로 토글한 직후:

```text
창 ①  cssRules 종류
  CSSStyleRule          .box { … opacity: 1; display: none; transition: … }
  CSSStyleRule          .box.on { display: block; }
  CSSStartingStyleRule  @starting-style { #b2.on { opacity: 0; } }       <- 바깥 형태
  CSSStyleRule          #b3 { @starting-style { opacity: 0; } }          <- 중첩 형태

창 ③  토글 '전' 계산값 — 셋이 완전히 같다
  b1 opacity=1 display=none · b2 opacity=1 display=none · b3 opacity=1 display=none

창 ④  토글 '직후' getAnimations()
  b1 : []                                            <- 전환 객체가 아예 없다
  b2 : CSSTransition(opacity)  키프레임 0:"0" -> 1:"1"
  b3 : CSSTransition(opacity)  키프레임 0:"0" -> 1:"1"
```

그림 해설 (한 단계씩):

- **창 ③ 은 이 주제에 쓸모가 없다.** 토글 전에는 셋 다 `opacity: 1` 이다 — 시작 스타일은 **평소 계산값에 아무 자국도 안 남긴다.**
- **창 ④ 가 결정적이다.** `getAnimations()` 가 빈 배열이면 **전환이 시작조차 안 한 것**이고,\
  `CSSTransition` 이 있으면 그 `getKeyframes()[0]` 이 **엔진이 실제로 쓴 시작값**이다.
- 창 ④ 는 값을 **해석해서 보여 주는 게 아니라 엔진이 만든 객체를 그대로** 준다. 손계산이 끼어들 자리가 없다.

★ **창 ③ 에도 딱 한 프레임 보인다.** 토글한 **같은 태스크 안에서** 바로 읽으면 `b2` 가 `"0"` 으로 읽힌다.\
하지만 `setTimeout(…, 0)` 한 번만 지나도 이미 보간값이라 **재현이 안 된다.** 재현되는 근거는 창 ④ 쪽이다.

비용 — 없음. 관측 수단일 뿐이다.

### (2) 두 가지 형태 — 바깥과 중첩

**언제 쓰나** — `@starting-style` 을 처음 쓸 때. 둘 다 같은 일을 한다.

```css
/* 바깥 형태 — 규칙을 통째로 감싼다 */
@starting-style {
  .drop { opacity: 0; }
}

/* 중첩 형태 — 규칙 안에 넣는다 (CSS 중첩, 14번 주제) */
.drop {
  opacity: 1;
  transition: opacity 1s linear;
  @starting-style { opacity: 0; }
}
```

- 실측에서 **둘의 결과가 완전히 같았다** — 위 창 ④ 의 `b2`(바깥)와 `b3`(중첩)가 같은 키프레임을 냈다.
- **중첩 형태의 명시도는 바깥 규칙의 명시도**다. `#b3 { @starting-style { … } }` 의 선언은 `(1,0,0)` 으로 경쟁한다.
- CSSOM 에서는 갈린다 — 바깥 형태만 `CSSStartingStyleRule` 로 **최상위에 보이고**, 중첩 형태는 `CSSStyleRule` 안에 들어간다(창 ①).

비용 — 없음. 취향이지만, **한 요소의 진입 전환은 중첩 형태가 읽기 쉽다**(선언이 한자리에 모인다).

### (3) ★★ 캐스케이드에서 어디에 오나 — **자동으로 이기지 않는다**

**언제 쓰나** — 「`@starting-style` 을 썼는데 아무 일도 안 난다」를 진단할 때. **이 주제에서 가장 자주 나는 사고다.**

명세가 못을 박아 뒀다.

> The rules inside @starting-style cascade as any other grouped style rules without introducing any new ordering to the cascade, which means rules inside @starting-style do not necessarily win over those outside.

실측 — 다섯 상자에 **명시도·순서·중요도만 바꿔** 던졌다. 모두 `.b{…transition:opacity 1s linear}` 를 공유한다.

```text
  경우                                        일반 선언      starting 선언   결과
  ----------------------------------------    -----------   -------------   ---------------------------
  d1  일반이 먼저, starting 이 나중 (0,1,0)     opacity:.8    opacity:.2      키프레임 0:0.2 -> 1:0.8  ★ 걸린다
  d2  starting 이 먼저, 일반이 나중 (0,1,0)     opacity:.8    opacity:.2      (전환 없음)              ★ 안 걸린다
  d3  starting (0,1,0) vs 일반 (1,0,0)         opacity:.8    opacity:.2      (전환 없음)
  d4  starting (1,0,0) vs 일반 (0,1,0)         opacity:.8    opacity:.2      키프레임 0:0.2 -> 1:0.8
  d5  starting 에 !important, 일반은 평범       opacity:.8    opacity:.2 !    키프레임 0:0.2 -> 1:0.8
```

그림 해설 (한 단계씩):

- **d1 과 d2 는 소스 순서만 다르다.** 뒤에 쓴 쪽이 이긴다 — 보통의 캐스케이드다.
- **d3 은 명시도로 졌다.** `@starting-style` 안에 있다고 봐주지 않는다.
- **d5 는 `!important` 가 이겼다.** 중요도도 평소대로 작동한다.
- 진 경우(d2·d3)는 **시작값 = 도착값**이 되어 **바뀐 값이 없으므로 전환이 아예 시작되지 않는다.**\
  창 ①·②·③ 이 전부 정상인데 전환만 없다 — **창 ④ 로만 보인다.**

```text
시작 스타일을 계산할 때의 사다리 (실측으로 확인한 순서)

   레이어(@layer)  ->  중요도(!important)  ->  명시도  ->  소스 순서
                          ↑
            @starting-style 안이라는 사실은 이 사다리에 끼어들지 않는다
```

비용 — 없음. 다만 **`@starting-style` 블록은 경쟁 규칙보다 뒤에 두는 것**을 습관으로 삼으면 d2 사고가 안 난다.

### (4) `@starting-style` 이 **적용되는 때**는 따로 있다

**언제 쓰나** — 「이미 보이는 요소의 클래스만 바꿨는데 왜 시작 스타일이 무시되나」를 볼 때.

실측 — 처음부터 `opacity: 1` 로 **렌더되어 있던** 요소에 `@starting-style { opacity: 0 }` 을 주고 `.on`(`opacity:.5`)을 붙였다.

```text
  키프레임   0:1 -> 1:0.5        <- 시작값이 0 이 아니라 '원래 있던 값' 1 이다
  계산값     1                   <- @starting-style 이 통째로 무시됐다
```

- 시작 스타일은 **「바뀌기 전 값이 없을 때만」** 쓰인다. 명세 표현 그대로다.

> If an element does not have a before-change style for a given style change event, the starting style is used instead of the before-change style to compare with the after-change style to start transitions.

- 그 조건은 실제로 둘이다 — **방금 렌더되기 시작했거나**(`display: none` → 렌더됨) **방금 DOM 에 꽂혔거나.**
- 이미 그려져 있던 요소에는 **이전 값이 있으므로** `@starting-style` 이 낄 자리가 없다.

비용 — 없음.

### (5) 퇴장은 왜 더 어렵나 — `display` 가 끊는다

**언제 쓰나** — 「사라질 때만 툭 없어진다」를 고칠 때.

```text
  퇴장 (display: none 으로 숨길 때)

  opacity 1 --------> 0        1초짜리 전환
     ^
     |  그런데 display: none 이 '첫 프레임에' 적용되면
     |  요소가 렌더 트리에서 빠져서
     +-- 전환이 그릴 대상 자체가 사라진다  -> 툭
```

`display` 는 **discrete 타입**이라 기본으로는 전환 목록에 못 들어간다(정본은 [52번 주제](../52-transition/2-summary.md)).\
`transition-behavior: allow-discrete` 가 그 문을 연다. 명세의 기본 규칙은 이렇다.

> When values with a discrete animation type are transitioned, they flip at 50% progress.

★ **그런데 `display` 는 50% 가 아니었다.** 실측(0.6초 전환, 팝오버를 닫는 판):

```text
  t=14ms    display: block   opacity: 1
  t=314ms   display: block   opacity: 0.50    <- 50% 지점에도 여전히 block
  t=614ms   display: block   opacity: 0.0000117
  t=764ms   display: none    opacity: 0       <- 다 끝나고 나서야 none
```

- 한쪽 끝이 `display: none` 인 전환은 **「보이는 쪽」이 전 구간을 차지한다.** 나타날 때는 처음부터, 사라질 때는 끝까지 `block` 이다.
- **나타날 때는 `display` 전환 객체가 아예 만들어지지 않았다** — 실측에서 팝오버를 여는 판의 `getAnimations()` 에는 `opacity` 하나뿐이었다(`["opacity 0:0->1:1"]`). 닫는 판에서만 셋이 나왔다(`["display", "opacity", "overlay"]`).

비용 — `allow-discrete` 를 빼면 **퇴장 전환이 통째로 없어진다.** 실측: 같은 문서에서 `display 1s allow-discrete` 만 빼니 마우스를 뗀 지 **15ms 에 이미 `display: none`·`opacity: 0`** 이었다.

### (6) `overlay` — 최상위 레이어에 **남아 있게** 하는 것

**언제 쓰나** — 팝오버·`<dialog>` 가 **닫히는 동안 뒤로 숨는** 현상을 볼 때.

`display` 를 붙들어도 문제가 하나 남는다. 최상위 레이어에서는 **즉시** 내려온다.

```text
  A : transition: opacity .6s, display .6s allow-discrete, overlay .6s allow-discrete
  B : transition: opacity .6s, display .6s allow-discrete            (overlay 없음)

  hidePopover() 직후 만들어진 전환 목록
    A -> ["display", "opacity", "overlay"]
    B -> ["display", "opacity"]

     t        A (overlay/display)     B (overlay/display)
     16ms     auto/block              none/block      <- B 는 벌써 최상위 레이어 밖
     316ms    auto/block              none/block
     516ms    auto/block              none/block
     616ms    none/none               none/none
```

그림 해설 (한 단계씩):

- **B 는 16ms 만에 `overlay: none` 이 됐다.** 아직 0.6초 동안 `block` 으로 보이지만 **최상위 레이어에서는 내려온 상태**다.
- 그 사이 B 는 보통 요소처럼 취급되므로 **조상의 쌓임 맥락·`overflow` 에 다시 갇힌다** — 페이드아웃 도중에 뒤로 숨거나 잘린다.
- `overlay` 는 **저자가 값을 정할 수 없는 속성**이다. `auto`/`none` 은 브라우저가 정하고, 저자는 **전환 목록에 태울 수만** 있다.

비용 — **`overlay` 는 Baseline `limited`(Chromium 전용)다.** 없는 엔진에서는 그 선언이 조용히 버려지고 나머지는 그대로 돈다 — **깨지지는 않고 퇴장 중 겹침만 달라진다.**

### (7) 팝오버·`<dialog>` 와 함께 쓰는 실무 형태

**언제 쓰나** — 실제 UI 에 붙일 때. **HTML 쪽 동작은 여기서 다루지 않는다**(`popover`·`<dialog>` 의 마크업은 HTML 갈래).

```css
[popover] {
  opacity: 1;
  transition: opacity .6s linear,
              display .6s allow-discrete,
              overlay .6s allow-discrete;
}
[popover]:not(:popover-open) { opacity: 0; }        /* 닫힌 상태 = 도착점 */
@starting-style { [popover]:popover-open { opacity: 0; } }   /* 열릴 때의 출발점 */
```

실측 — 위 형태를 그대로 띄워 `showPopover()` / `hidePopover()` 를 던졌다.

```text
  열기   t=2ms 0.028 → 152ms 0.278 → 302ms 0.528 → 452ms 0.778 → 602ms 1     (0.6초 페이드인)
  닫기   t=14ms 1 → 164ms 0.750 → 314ms 0.500 → 464ms 0.250 → 614ms ~0 → 764ms display:none
```

- 세 줄이 각각 다른 일을 한다 — **`opacity` 가 보이는 변화**, **`display` 가 시간 확보**, **`overlay` 가 층 유지**.
- `<dialog>` 도 형태가 같다(`:open` 을 쓴다). **`@starting-style` 은 최상위 레이어와 무관하다** — 그냥 「처음 렌더될 때」가 트리거다.

비용 — 세 속성을 다 쓰면 선언이 길다. **`opacity` 만으로 되는 요소**(최상위 레이어가 아닌 드롭다운)에는 `overlay` 를 빼도 된다.

## demo — 진입에서 갈리고 퇴장에서 만난다

```html demo
<div class="menu">이 상자에 마우스를 올려 보세요
  <div class="drop a">@starting-style 없음</div>
  <div class="drop b">@starting-style 있음</div>
</div>
<style>
  .menu { width: 240px; padding: 10px; background: #e2e8f0; font: 14px system-ui; }
  .drop { display: none; opacity: 0; margin-top: 6px; padding: 8px;
          background: #1d4ed8; color: #fff;
          transition: opacity 1s linear, display 1s allow-discrete; }
  .menu:hover .drop { display: block; opacity: 1; }
  @starting-style { .menu:hover .b { opacity: 0; } }
</style>
```

> **보이는 것** — 마우스를 올리면 **위 상자(`a`)는 즉시 선명하게 튀어나오고**, 아래 상자(`b`)는 1초에 걸쳐 서서히 나타난다.\
> 마우스를 떼면 **둘 다 똑같이** 1초에 걸쳐 흐려지다가 사라진다 — 퇴장은 `@starting-style` 과 무관하기 때문이다.\
> **바꿔 볼 것** — `@starting-style` 줄을 `.menu:hover .drop` 규칙 **앞으로** 옮기면 → `b` 도 `a` 처럼 즉시 튀어나온다(명시도가 같아 소스 순서로 진다) · `transition` 에서 `display 1s allow-discrete` 를 빼면 → 마우스를 뗀 순간 둘 다 **페이드 없이 즉시** 사라진다

*(Chrome 151 headless 실측 — CDP 로 실제 마우스를 움직였다. `a` / `b` 의 `opacity`:)*

```text
  진입      t=7ms    a=1      b=0.017      <- a 는 첫 프레임에 이미 끝나 있다
            t=322ms  a=1      b=0.333
            t=622ms  a=1      b=0.633
            t=1088ms a=1      b=1

  퇴장      t=16ms   a=0.983  b=0.983  (display: block)
            t=616ms  a=0.383  b=0.383  (display: block)
            t=1066ms a=0      b=0      (display: none)   <- 1초 뒤에야 none

  바꿔 볼 것 ① (@starting-style 을 앞으로)  t=9ms a=1 b=1        <- b 도 튄다
  바꿔 볼 것 ② (allow-discrete 제거) 퇴장    t=15ms a·b 모두 opacity 0 / display none
```

## 문법 — 형태와 규칙

CSS 는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태

```css
/* ① @starting-style — 두 형태 */
@starting-style { <선택자> { <선언들> } }     /* 바깥 */
<선택자> { … @starting-style { <선언들> } }   /* 중첩 */

/* ② transition-behavior — 값은 둘뿐 */
transition-behavior: normal | allow-discrete;

/* ③ 단축 안에서는 속성 이름 옆에 키워드로 */
transition: display 1s allow-discrete;

/* ④ 전환에 태울 수 있는 이산 속성(자주 쓰는 것) */
display · visibility · overlay · content-visibility
```

### 금지 사례 — 던져서 확인한 것

```css
/* ✗ @starting-style 안에 또 @starting-style — 명세가 금지 */
/* ✗ overlay 값을 저자가 지정하기 — auto/none 은 브라우저가 정한다 */
overlay: auto;            /* 저자 스타일에서는 무시된다 */

/* ✗ 이미 보이는 요소에 기대기 — 시작 스타일이 통째로 무시된다 (동작 방식 (4)) */
```

### 어디서 헷갈리나

- **`allow-discrete` 는 값이지 속성이 아니다.** 단축에서는 속성 이름과 같은 자리(`display 1s allow-discrete`)에 쓰고,\
  롱핸드로는 `transition-behavior: allow-discrete` 라고 **따로** 쓴다.
- **`transition-behavior` 는 속성별로 갈리지 않는다.** 롱핸드로 쓰면 `transition-property` 목록 **전체**에 같은 순서로 대응한다.
- `@starting-style` 은 **전환을 만들지 않는다.** `transition` 이 따로 걸려 있어야 한다 — **출발선만 그려 주는 것**이다.

## 어디서 틀리나

### 1. ★★ `@starting-style` 블록을 위에 써 놓는다

경쟁하는 일반 규칙보다 **앞에** 쓰면 같은 명시도에서 진다(동작 방식 (3) d2).\
**에러도 경고도 없고 `cssRules` 에도 멀쩡히 담겨 있다.** `getAnimations()` 가 빈 배열인 것으로만 보인다.

### 2. 명시도를 안 맞춘다

`@starting-style { .drop { opacity: 0 } }` 을 쓰고 도착 규칙은 `.menu:hover .drop { opacity: 1 }` 로 쓰면\
`(0,1,0)` 대 `(0,3,0)` 이라 **시작값이 도착값에 덮여** 전환이 안 걸린다. 위 demo 가 `@starting-style { .menu:hover .b { … } }` 로 쓴 이유다.

### 3. 퇴장에 `allow-discrete` 를 안 쓴다

진입만 고치고 끝내면 **사라질 때 툭 없어진다.** 실측: 15ms 만에 `display: none` 이었다.

### 4. `overlay` 를 빼먹고 팝오버가 「닫히다가 숨는다」고 한다

퇴장 0.6초 동안 **최상위 레이어에서만 먼저 내려온다.** `display` 는 `block` 이라 「보이는데 자리가 이상한」 상태가 된다.

### 5. 이미 렌더된 요소에 `@starting-style` 을 건다

토글 클래스만 바꾸는 경우에는 **이전 값이 이미 있으므로** 시작 스타일이 통째로 무시된다(동작 방식 (4)).\
이 경우는 `@starting-style` 이 아니라 **그냥 평범한 전환**으로 충분하다.

### 6. `height: auto` 를 같이 전환하려 한다

`@starting-style` 은 **출발값을 만들어 줄 뿐** 보간할 수 없는 값을 보간되게 만들지 못한다.\
`auto` 는 여전히 안 된다(정본은 [52번 주제](../52-transition/2-summary.md)).

### 7. Baseline 을 안 보고 `overlay` 를 필수로 쓴다

`overlay` 만 **`limited`(Chromium 전용)** 다. 없는 엔진에서는 그 한 줄이 조용히 버려진다 — **깨지지는 않지만 겹침이 달라진다.**

## 구현 세부사항 대 언어 보장

| 항목 | 누가 보장하나 |
|---|---|
| `@starting-style` 이 「이전 값이 없을 때만」 쓰인다 | **명세**(css-transitions-2, 위 인용) |
| `@starting-style` 안 선언이 **자동으로 이기지 않는다** | **명세**(위 인용) — 실측도 일치 |
| 이산 속성이 **50% 에서 뒤집힌다** | **명세**(css-transitions-2 Note) |
| `display`·`overlay` 가 퇴장에서 **끝까지 버틴다** | 명세의 특례 + **Chrome 151 실측**(t=614ms 에도 `block`) |
| 나타날 때 `display` **전환 객체가 아예 안 만들어진다** | **Chrome 151 관찰.** 결과는 명세와 맞지만 「객체를 안 만든다」는 구현 선택이다 |
| `getAnimations()` 키프레임의 **직렬화 형태**(`"0"` / `"1"`) | CSSOM 직렬화 세부 |
| `overlay` 지원 | **Chromium 전용**(Baseline limited, 2026-09-23 조회) |
| 샘플 시각 ±1프레임 오차 | 측정 환경 |

## 언제 쓰고 언제 안 쓰나

| 상황 | `@starting-style` | 함께 쓸 것 |
|---|---|---|
| `display: none` 에서 나타나는 드롭다운·토스트 | **쓴다** | 퇴장용 `display … allow-discrete` |
| JS 로 DOM 에 새로 꽂는 요소 | **쓴다** | 〃 |
| 팝오버·`<dialog>` | **쓴다** | `display` + **`overlay`** 둘 다 |
| 이미 보이는 요소의 클래스 토글 | **안 쓴다** | 평범한 `transition` 으로 충분 |
| 여러 지점을 들르는 등장 연출 | 안 쓴다 | `@keyframes`·`animation`([목록의 **53번 주제**](../53-keyframes-and-animation/)) |
| 스크롤 진행에 묶인 등장 | 안 쓴다 | [58번 주제](../58-scroll-driven-animations/2-summary.md) |

## 핵심 문장

- **전환은 두 값 사이를 채우는 것이고, 처음 나타나는 요소에는 「앞의 값」이 없다.**
- **`@starting-style` 은 그 없는 앞값을 한 프레임만 만들어 준다** — 평소 계산값에는 흔적이 없다.
- **그 선언은 캐스케이드에서 봐주는 것이 없다.** 순서·명시도·중요도로 그냥 진다.
- **퇴장은 부품이 하나 더 필요하다** — `display` 를 붙들 `allow-discrete`, 최상위 레이어를 붙들 `overlay`.
- **관측 창은 `getAnimations()` 다.** 빈 배열이면 전환이 시작조차 안 한 것이다.

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 57번)
- [`../52-transition/2-summary.md`](../52-transition/2-summary.md) — **전환의 정본.**\
  전환이 걸리는 세 조건·타이밍 함수·지연·되돌리기·`transition-behavior` 의 기본 뜻은 **거기까지**,\
  여기는 **「앞값이 없을 때」와 「퇴장에서 층까지 붙드는 것」부터**.
- [`../22-stacking-context-and-z-index/2-summary.md`](../22-stacking-context-and-z-index/2-summary.md) — 쌓임 맥락의 정본.\
  `overlay` 가 왜 필요한지는 **최상위 레이어가 쌓임 맥락 밖**이라는 거기 설명에 기댄다.
- [`../14-css-nesting/2-summary.md`](../14-css-nesting/2-summary.md) — 중첩 형태 `@starting-style` 이 쓰는 문법.
- [`../01-cascade-and-priority/2-summary.md`](../01-cascade-and-priority/2-summary.md) · [`../02-specificity/2-summary.md`](../02-specificity/2-summary.md) — 동작 방식 (3) 의 사다리.
- [목록의 **53번 주제**](../53-keyframes-and-animation/)(`@keyframes`·`animation`) — 여러 지점을 들르는 등장 연출은 그쪽.
- [`../58-scroll-driven-animations/2-summary.md`](../58-scroll-driven-animations/2-summary.md) — 진행률이 시간이 아니라 스크롤에서 오는 경우.
- [`../60-prefers-reduced-motion/2-summary.md`](../60-prefers-reduced-motion/2-summary.md) — **모션 접근성의 정본.**\
  진입·퇴장 연출을 선호에 맞춰 줄이는 판단은 거기.
- [`../../../../../../reference/render-rules.md`](../../../../../../reference/render-rules.md) — demo 블록 규칙.

## 용어 풀이

- **시작 스타일(starting style)** — 이전 값이 없을 때 「바뀌기 전 값」 자리에 쓰이는 스타일. `@starting-style` 로 정한다.
- **`@starting-style`** — 그 시작 스타일을 선언하는 규칙. 바깥 형태와 중첩 형태가 있다. Baseline newly(2024-08-06).
- **before-change style** — 값이 바뀌기 직전의 계산 스타일. 이게 없을 때만 시작 스타일이 쓰인다.
- **discrete(이산) 타입** — 중간값 없이 툭 바뀌는 애니메이션 타입. `display`·`visibility`·`overlay`.
- **`transition-behavior: allow-discrete`** — 이산 속성도 전환 목록에 태우는 값. Baseline newly(2024-08-06).
- **`overlay`** — 요소가 최상위 레이어에 있는지를 나타내는 속성. **저자가 값을 못 정하고 전환에만 태운다.** Baseline limited.
- **최상위 레이어(top layer)** — 모든 쌓임 맥락 위에 따로 그려지는 층. 팝오버·모달이 올라간다.
- **`getAnimations()`** — 그 요소에 지금 붙어 있는 애니메이션·전환 객체 목록. **빈 배열 = 전환이 시작 안 했다.**
- **`getKeyframes()`** — 전환 객체가 실제로 쓰는 시작·끝 값. 시작 스타일을 잡는 유일한 재현 가능한 창.
- **팝오버(popover)** — HTML 의 `popover` 속성으로 최상위 레이어에 띄우는 요소. `:popover-open` 으로 상태를 잡는다.

## 더 들어가면

- **`content-visibility` 도 이산 속성**이라 `allow-discrete` 로 태울 수 있다. 「접힌 영역을 부드럽게 펴는」 패턴에 쓰인다.
- `@starting-style` 은 **애니메이션(`@keyframes`)에는 쓸모가 없다.** 애니메이션은 시작값을 키프레임이 직접 들고 있어서 앞값이 필요 없다.
- `transitionstart` 이벤트가 나는지로도 「전환이 걸렸나」를 알 수 있지만, **안 걸렸을 때 아무 이벤트도 안 나므로** 「없음」을 증명하려면 타임아웃이 필요하다. `getAnimations()` 는 **동기적으로 없음을 보여 준다.**

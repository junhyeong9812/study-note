# css/syntax/15 — 박스 모델과 `box-sizing` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [CSS Box Model Level 3](https://drafts.csswg.org/css-box-3/) (네 겹 상자와 `margin`·`padding` 의 정본) · [CSS Box Sizing Level 3](https://drafts.csswg.org/css-sizing-3/) (`box-sizing`·`width`·`min-width`/`max-width`). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 `demo` 블록 **3개 전부**를 **Google Chrome 151.0.7922.173** headless 에 실제로 띄워 `getBoundingClientRect()` 로 치수를 재고 스크린샷으로 눈으로 확인했다.\
> 본문의 픽셀 값은 전부 그 실측값이다. **손으로 계산해 적은 수치는 없다.** **WebKit(Safari)은 이 머신에 없고 Firefox 는 이 환경에서 headless 스크린샷이 산출되지 않는다** — 크로스 브라우저 주장은 하지 않았다.
> **버전** — `box-sizing` 은 CSS 에 언어 버전이 없으므로 Baseline 으로 읽는다. `border-box` 는 오래전에 자리잡아 목록 README 의 지원 표에 별도 행이 없을 만큼 보편적이다.
> **여기서 다루지 않는 것** — 이 상자가 **어떤 배치 규칙 안에 놓이는가**는 [16번](../16-display-inner-outer/2-summary.md)·[17번](../17-block-formatting-context/2-summary.md), **마진이 서로 합쳐지는 규칙**은 [18번](../18-margin-collapsing/2-summary.md)이 정본이다. `min-content`/`fit-content`·`aspect-ratio` 같은 내재적 크기는 [목록의 **31번 주제**](../31-intrinsic-sizing-and-aspect-ratio/), 단위(`%`·`em`)는 [목록의 **33번 주제**](../33-length-units/)다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 치수는 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**상자 하나는 액자다. 그림·매트·액자틀·벽과의 거리, 네 겹이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 그림 자체 | **content** — 글자와 이미지가 들어가는 칸 |
| 그림과 액자틀 사이의 흰 매트 | **padding** — 배경색이 칠해지는 안쪽 여백 |
| 나무 액자틀 | **border** — 테두리 |
| 액자와 옆 액자 사이의 벽 | **margin** — 바깥 여백. 배경이 칠해지지 않는다 |
| 「이 액자 30cm 짜리」라고 할 때 무엇을 잰 값인가 | **`box-sizing`** — `width` 가 어느 칸까지를 가리키나 |

- 가게에서 "30cm 액자"라고 하면 **틀 바깥까지 30cm** 다. 이것이 `border-box` 다.
- 그런데 CSS 의 기본값은 **그림만 30cm**(`content-box`)이고, 매트와 틀은 그 바깥에 **더 붙는다**.
- 그래서 `width: 300px` 이라고 써 놓고 실제로 차지하는 폭이 **350px** 이 되는 일이 생긴다.\
  *(Chrome 151 headless 실측: `width:300px; padding:20px; border:5px` 에서 `content-box` 는 350px, `border-box` 는 300px.)*

```text
                       ← margin (배경 없음, 옆 상자와의 거리) →
  +---------------------------------------------------------+
  |                     border (5px)                         |
  |   +--------------------------------------------------+   |
  |   |                 padding (20px)                    |   |
  |   |   +------------------------------------------+    |   |
  |   |   |             content (300px)              |    |   |
  |   |   +------------------------------------------+    |   |
  |   +--------------------------------------------------+   |
  +---------------------------------------------------------+

  box-sizing: content-box   width 는 [content] 만        -> 실제 폭 350
  box-sizing: border-box    width 는 [border..border]    -> 실제 폭 300
  두 모드 어느 쪽에서도 margin 은 절대 포함되지 않는다.
```

실무에서 이게 터지는 자리는 **`width: 100%` 에 `padding` 을 같이 준 칸**이다.\
`content-box` 면 부모 폭 100% 에 패딩이 더 얹혀 **부모를 뚫고 나간다.**

> **콘텐츠 상자(content box)** — 글자·이미지가 실제로 놓이는 가장 안쪽 칸.\
> 예: `<p>` 안의 글이 줄바꿈되는 폭이 이 칸의 폭이다.

> **테두리 상자(border box)** — 테두리 바깥선까지의 칸. 화면에서 "이 상자"라고 부를 때 보통 이것이다.\
> 예: `getBoundingClientRect().width` 가 돌려주는 값이 이 칸의 폭이다.

> **마진 상자(margin box)** — 마진까지 포함한 칸. **배경이 칠해지지 않아 눈에 안 보인다.**\
> 예: 상자 둘 사이가 벌어져 보이면 그 빈 자리가 마진 상자의 일부다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `width: 300px` 이라고 썼을 때 **화면에서 실제로 몇 px 을 차지하는가** — 그리고 그 답이 하나가 아닌 이유.
2. `box-sizing` 이 **무엇을 포함하고 무엇을 절대 포함하지 않는가.**
3. `box-sizing` 이 **아무 일도 하지 않는 경우**는 언제인가.

## 동작 방식

### (1) 네 겹 — 안에서 밖으로

**언제 쓰나** — 상자 하나의 치수를 따질 때 언제나. 이 그림이 이 주제 전부의 좌표계다.

```text
  잴 수 있는 네 가지 폭 (padding 20 · border 5 · margin 30 일 때)

  content 폭      [                300                ]
  padding 폭   [20|                300                |20]   = 340
  border  폭 [5|20|                300                |20|5]  = 350
  margin  폭 [------30------][   border 폭 350   ][------30------] = 410
             ^ 배경이 여기부터            ^ 여기까지 칠해진다
```

그림 해설 (한 단계씩):

- **배경은 `border` 상자까지만 칠해진다.** 마진 칸은 뒤에 있는 것이 그대로 비친다.
- 그래서 "상자에 색이 있는데 사이가 벌어진다" = 그 빈 칸이 마진이다.
- `getBoundingClientRect()` 가 돌려주는 것은 **border 폭**이다. 마진은 그 안에 없다.

*(Chrome 151 headless 실측 — `width:300px; padding:20px; border:5px` 인 `content-box` 상자: `rect.width` = 350, `clientWidth`(padding 폭) = 340, 자식에게 `width:100%` 를 줘서 잰 content 폭 = 300.)*

비용 — 없다. 다만 **네 값이 서로 다른 칸을 가리킨다는 것**을 매번 의식해야 한다.

### (2) `content-box` — 기본값. `width` 는 그림만 잰다

**언제 쓰나** — 아무것도 선언하지 않았을 때. 즉 거의 언제나가 기본값이다.

```text
  width: 300px; padding: 20px; border: 5px  (box-sizing: content-box)

  선언                계산                       결과
  width = 300   ->   content 가 300              rect.width = 350
                     padding 20 은 그 바깥에
                     border 5 도 그 바깥에       (5+20+300+20+5)
```

- **`width` 는 "이 상자의 폭"이 아니라 "안쪽 그림의 폭"** 이라는 뜻이다.
- 그래서 패딩이나 테두리를 **나중에 추가하면 상자가 커진다.** 디자인이 밀리는 사고의 뿌리가 여기다.

### (3) `border-box` — `width` 가 테두리 바깥까지를 잰다

**언제 쓰나** — 칸 폭을 먼저 고정하고 안쪽 여백을 나중에 조절하고 싶을 때. 실무의 기본 선택이다.

```html demo
<div class="cb">content-box — width:300px</div>
<div class="bb">border-box — width:300px</div>
<div class="ruler"></div>
<style>
  .cb, .bb { width: 300px; padding: 20px; border: 5px solid #64748b;
             background: #bfdbfe; font: 14px system-ui; }
  .cb { box-sizing: content-box; }            /* 기본값 */
  .bb { box-sizing: border-box; margin-top: 8px; }
  .ruler { width: 300px; height: 6px; background: #ef4444; margin-top: 8px; }
</style>
```

> **보이는 것** — 똑같이 `width: 300px` 인데 **위 상자가 아래 상자보다 오른쪽으로 50px 더 나가 있다.** 맨 아래의 빨간 막대는 폭이 정확히 300px 인 자인데, **아래 상자의 오른쪽 끝과 딱 맞고 위 상자는 그 자를 넘어간다.** 두 상자의 높이와 안쪽 여백은 똑같다.\
> **바꿔 볼 것** — `.cb` 의 `padding: 20px` 을 `0` 으로 → 두 상자의 폭이 같아진다(패딩·테두리가 0 이면 두 모드가 같은 값이다) · `.bb` 의 `width: 300px` 을 `40px` 으로 → (6)을 보라

*(Chrome 151 headless 실측: `content-box` 상자 `rect.width` = **350**, `border-box` 상자 = **300**, 빨간 자 = 300. 두 상자의 높이는 둘 다 70px 로 같았다.)*

```text
  같은 width: 300px, 다른 box-sizing

  content-box                              border-box
  [5|20|--- 300 (content) ---|20|5]        [5|20|- 250 (content) -|20|5]
  <-------------- 350 -------------->      <--------- 300 --------->
       width 가 가리키는 칸 = 300               width 가 가리키는 칸 = 300
       (안쪽)                                   (바깥쪽)
```

- `border-box` 에서 **content 폭은 선언한 값에서 패딩·테두리를 뺀 나머지**가 된다.\
  *(같은 실측: `border-box` 부모 안에 `width:100%` 인 자식을 넣어 재니 **250px** 이었다 — 300 에서 패딩 40 과 테두리 10 이 빠진 값이다.)*
- 그래서 패딩을 늘려도 **바깥 치수는 그대로**이고 안쪽 글자 칸만 줄어든다.

### (4) `margin` 은 어느 모드에서도 포함되지 않는다

**언제 쓰나** — `width: 100%` 짜리 칸에 여백을 주려 할 때. 이 주제에서 가장 자주 나는 사고다.

```html demo
<div class="parent">
  <div class="fit">width:100% — 딱 맞는다</div>
  <div class="over">+ margin 20px — 밖으로 나간다</div>
</div>
<style>
  .parent { width: 300px; border: 2px dashed #ef4444; }
  .fit, .over { box-sizing: border-box; width: 100%; padding: 10px;
                border: 3px solid #64748b; background: #bfdbfe; font: 13px system-ui; }
  .over { margin: 8px 20px; }
</style>
```

> **보이는 것** — 위 상자는 빨간 점선 테두리 **안에 정확히 들어맞는다.** 아래 상자는 똑같이 `border-box; width: 100%` 인데 **왼쪽으로 20px 들여쓰인 채 오른쪽 점선을 20px 뚫고 나간다.** 폭은 둘 다 300px 로 같고, 위치만 오른쪽으로 밀렸다.\
> **바꿔 볼 것** — `.over` 의 `margin: 8px 20px` → `8px 0` → 위 상자와 똑같이 들어맞는다 · `width: 100%` 를 지우면(= `auto`) → 마진을 준 채로도 점선 안에 들어맞는다(아래 (5))

*(Chrome 151 headless 실측: 부모의 content 칸은 x=2\~302. `fit` 은 x=2, 폭 300 으로 오른쪽 끝이 302 에 딱 맞는다. `over` 는 x=22, 폭 **300 그대로**여서 오른쪽 끝이 322 — **점선 밖으로 20px**. `box-sizing: border-box` 가 마진을 먹어 주지 않는다.)*

- `border-box` 는 **padding 과 border 까지만** 끌어안는다. **`margin` 은 그 바깥이라 건드리지 않는다.**
- 그래서 `width: 100%` + `margin` 은 **어떤 `box-sizing` 으로도 안 맞는다.**\
  해법은 `width` 를 빼거나(= `auto`, (5)), `calc(100% - 40px)` 를 쓰거나, 부모에 패딩을 주는 것이다.

### (5) `width: auto` 면 `box-sizing` 은 아무 일도 하지 않는다

**언제 쓰나** — 블록 상자에 `width` 를 안 준 기본 상태. 실제 페이지의 대부분이 이 상태다.

```html demo
<div class="box">
  <div class="cb">content-box · width 선언 없음</div>
  <div class="bb">border-box · width 선언 없음</div>
</div>
<style>
  .box { width: 320px; border: 2px dashed #94a3b8; }
  .cb, .bb { padding: 20px; border: 5px solid #64748b; background: #bfdbfe; font: 13px system-ui; }
  .cb { box-sizing: content-box; }
  .bb { box-sizing: border-box; margin-top: 8px; }
</style>
```

> **보이는 것** — `box-sizing` 이 서로 다른데도 **두 상자의 왼쪽 끝·오른쪽 끝이 완전히 같다.** 둘 다 회색 점선 안을 꽉 채운다. (3)의 demo 와 다른 점은 **`width` 선언이 없다는 것 하나**다.\
> **바꿔 볼 것** — 두 상자에 `width: 200px` 을 추가 → 즉시 폭이 갈라진다(250 대 200) · `.box` 의 `width` 를 `500px` 로 → 두 상자가 같이 넓어진다

*(Chrome 151 headless 실측: 두 상자의 `rect.width` 가 **둘 다 320** — 한 픽셀도 다르지 않다. 안쪽 content 폭도 둘 다 270 으로 같다.)*

- `width: auto` 인 블록 상자는 **"남는 자리를 다 쓴다"** 는 규칙으로 폭이 정해진다.\
  즉 부모 폭에서 **마진·테두리·패딩을 빼고 남은 것**이 content 폭이 된다.
- 이 계산에는 `box-sizing` 이 끼어들 자리가 없다. **`box-sizing` 은 "선언한 `width` 숫자를 어느 칸에 배정하나"만 정하는데, 배정할 숫자가 없기 때문이다.**
- 그래서 `* { box-sizing: border-box }` 리셋이 **아무것도 망가뜨리지 않고 켜지는** 이유가 이것이다 — `width` 를 안 준 상자는 영향을 받지 않는다.

### (6) `border-box` 의 `width` 에는 하한이 있다

**언제 쓰나** — 좁은 칸에 패딩을 크게 줬는데 치수가 안 맞을 때.

```text
  box-sizing: border-box; padding: 20px; border: 5px
  -> 패딩·테두리만으로 이미 50px

  width: 50px  ->  content 0,  rect.width = 50   (딱 맞음)
  width: 40px  ->  content 0,  rect.width = 50   (선언을 무시하고 50)
```

*(Chrome 151 headless 실측: `width: 40px` 인 `border-box` 상자의 `rect.width` 가 **50**, `clientWidth` 가 40, `getComputedStyle().width` 도 `50px` 이었다. 선언한 40 은 어디에도 남지 않는다.)*

- content 폭은 **음수가 될 수 없어 0 에서 멈춘다.** 그 아래로는 상자가 더 줄지 않는다.
- 그래서 `border-box` 를 쓰면 **"칸이 안 줄어든다"** 는 증상이 생긴다 — 에러는 나지 않는다.

### (7) `min-width`/`max-width` 도 같은 칸을 잰다

**언제 쓰나** — 반응형에서 상·하한을 걸 때.

```text
  box-sizing: content-box;  width:100px; min-width:200px; padding:20px; border:5px
      -> min-width 가 content 를 200 으로 끌어올린다 -> rect.width = 250

  box-sizing: border-box;   같은 선언
      -> min-width 가 border 폭을 200 으로 끌어올린다 -> rect.width = 200
```

*(Chrome 151 headless 실측: 위 두 경우의 `rect.width` 가 각각 **250** 과 **200**. `max-width: 200px` 로 눌러 본 경우도 같은 값이 나왔다 — 250 과 200.)*

- **`min-width`·`max-width` 는 `width` 와 같은 칸을 잰다.** 한쪽만 `box-sizing` 밖에 있지 않다.
- 그래서 `border-box` 로 바꾸면 `max-width` 가 가리키던 폭도 같이 바뀐다 — **레이아웃 리셋을 나중에 넣으면 상한이 조용히 달라진다.**

## 문법 — 형태와 어디서 헷갈리나

CSS 는 문법 표면이 단순하므로 여기서는 **형태보다 헷갈리는 자리**를 적는다.

### 최소 형태

```css
.box {
  box-sizing: border-box;   /* content-box(기본) | border-box */
  width: 300px;             /* 이 숫자가 어느 칸을 가리키는지가 위 줄에 달려 있다 */
  padding: 20px;            /* 네 방향 한꺼번에 */
  border: 5px solid #64748b;
  margin: 30px;             /* box-sizing 과 무관 */
}
```

- `box-sizing` 의 값은 **두 개뿐**이다. `margin-box` 같은 값은 없다.
- `box-sizing` 은 **상속되지 않는다.** 그래서 리셋은 `* { box-sizing: border-box }` 처럼 전체 선택자로 쓴다.

### 헷갈리는 자리 — 「무엇의 몇 퍼센트인가」

| 선언 | 기준이 되는 칸 |
|---|---|
| `width: 50%` | **부모의 content 폭**의 50% |
| `padding: 10%` | **부모의 content 폭**의 10% — 위아래 패딩도 **폭** 기준이다 |
| `margin: 10%` | **부모의 content 폭**의 10% — 역시 폭 기준 |
| `height: 50%` | 부모의 content **높이**의 50% (부모 높이가 `auto` 면 적용되지 않는다) |

- **세로 방향 `padding`·`margin` 의 `%` 가 가로 폭을 기준으로 한다**는 것이 이 표에서 가장 자주 틀리는 칸이다.\
  `padding-top: 100%` 로 정사각형을 만드는 옛 관용구가 여기서 나왔다(오늘은 `aspect-ratio` 를 쓴다 — [목록의 **31번 주제**](../31-intrinsic-sizing-and-aspect-ratio/)).
- `%` 가 어느 단계에서 픽셀이 되는지는 [목록의 **04번 주제**](../04-value-processing-stages/), 단위 일반은 [목록의 **33번 주제**](../33-length-units/)가 정본이다.

### 금지에 가까운 형태

```css
.a { box-sizing: margin-box; }   /* 그런 값은 없다 — 선언 하나가 통째로 버려진다 */
.b { width: 100%; margin: 20px; box-sizing: border-box; }  /* 문법은 맞지만 (4)의 사고 */
```

- CSS 는 **에러가 없는 언어**다. 없는 값을 쓰면 **경고 없이 그 선언만 버려지고** 앞서 이긴 값이 그대로 남는다.\
  정본은 [목록의 **07번 주제**](../07-syntax-and-error-recovery/)(오류 복구).

## 구현 세부사항 대 언어 보장

★ **측정 도구도 거짓말을 한다.** 이 주제에서 가장 조심할 자리다.

```text
  box-sizing: border-box; width:300px; padding:20px; border:5px

  실제 content 폭            250   (자식에게 width:100% 를 줘서 잰 값)
  getBoundingClientRect().w  300   (border 폭)
  clientWidth                290   (padding 폭)
  getComputedStyle().width   300   ← content 폭이 아니다
```

*(Chrome 151 headless 실측. 같은 선언을 `content-box` 로 바꾸면 `getComputedStyle().width` 는 `300px`, `rect.width` 는 350 이다.)*

- **Chrome 151 에서 `getComputedStyle(el).width` 는 그 요소 자신의 `box-sizing` 기준으로 돌아온다.**\
  `content-box` 면 content 폭, `border-box` 면 border 폭이다. **두 요소의 `width` 문자열이 똑같이 `300px` 인데 실제 칸은 다르다.**
- 이것은 **이 브라우저에서 관찰한 것**이지 "CSS 가 그렇게 보장한다"가 아니다. 계산값 API 의 정본은 CSSOM 명세이고, 이 목록은 선언적 CSS 만 다룬다(README 의 「뺀 것」).
- **안전한 습관**: 치수를 확인할 때는 `getComputedStyle` 대신 `getBoundingClientRect()`(border 폭)와 `clientWidth`(padding 폭)를 함께 읽는다. 둘은 무엇을 재는지가 이름으로 고정돼 있다.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 넷 다 **에러 없이 조용히 어긋난다.**

### 1. `width: 100%` 에 `padding` 을 얹는다

```text
  잘못                                   맞게
  .col { width: 100%; padding: 20px; }   .col { box-sizing: border-box;
         (content-box)                          width: 100%; padding: 20px; }
  -> 부모를 40px 뚫고 나간다              -> 부모 안에 들어맞는다
```

가장 흔한 사고다. `border-box` 리셋이 널리 쓰이는 이유가 이 한 줄이다.

### 2. `border-box` 면 `margin` 도 들어간다고 생각한다

(4)의 실측이 답이다 — **안 들어간다.** `width: 100%` 에 좌우 마진을 주면 `border-box` 여도 넘친다.

### 3. `box-sizing` 을 바꿨는데 아무 일도 안 일어난다

(5)의 실측이 답이다 — **그 상자에 `width` 가 없으면 원래 아무 일도 안 한다.**\
"리셋을 넣었는데 레이아웃이 그대로다"는 고장이 아니라 정상이다.

### 4. 패딩을 키웠더니 글자 칸이 사라졌다

`border-box` 에서는 패딩이 커질수록 **content 가 줄어든다.** 0 에서 멈추고 그 뒤로는 상자가 (6)처럼 선언을 무시한다.\
`content-box` 였다면 대신 상자가 커졌을 것이다 — **어느 쪽이 "안전"한 것이 아니라 어느 쪽이 터지는 자리가 다르다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | `content-box` (기본) | `border-box` |
|---|---|---|
| 칸 폭을 먼저 고정하고 안쪽 여백을 조절 | 계산이 꼬인다 | **쓴다** |
| `width: 100%` 짜리 입력칸·버튼 | 넘친다 | **쓴다** |
| 그리드 칸을 `%` 로 나눈다 | 패딩 때문에 합이 안 맞는다 | **쓴다** |
| 안쪽 글자 칸의 폭을 정확히 고정해야 한다 | **쓴다** | content 가 패딩에 따라 변한다 |
| `width` 를 아예 안 주는 상자 | 차이 없음 | 차이 없음 |

판단 규칙 두 줄.

- **`width` 를 선언하는 상자에만 `box-sizing` 이 의미가 있다.** 안 주는 상자에는 아무 영향이 없다.
- **프로젝트 시작에 `* { box-sizing: border-box }` 를 깔면 대부분의 사고가 사라진다.** 다만 (7) 때문에 **나중에 넣으면 `min-width`/`max-width` 의 뜻이 조용히 달라진다** — 처음에 깔아야 한다.

## 핵심 문장

- 상자는 **content · padding · border · margin** 네 겹이고, **배경은 border 까지만** 칠해진다.
- `box-sizing` 은 **`width`/`height` 숫자를 어느 칸에 배정할지**만 정한다. `content-box` 는 안쪽 칸, `border-box` 는 테두리 바깥 칸이다.
- **`margin` 은 어느 모드에서도 포함되지 않는다** — `width: 100%` 에 좌우 마진을 주면 `border-box` 여도 넘친다.
- **`width: auto` 면 `box-sizing` 은 아무 일도 하지 않는다.** 배정할 숫자가 없기 때문이다.
- `min-width`/`max-width` 도 `width` 와 **같은 칸**을 잰다.
- `border-box` 의 `width` 는 **패딩+테두리 합보다 작아지지 않는다**(실측: 40 을 줘도 50).
- Chrome 151 의 `getComputedStyle().width` 는 **그 요소의 `box-sizing` 기준**으로 돌아온다 — content 폭이 아니다.

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 15번)
- [16번 주제](../16-display-inner-outer/2-summary.md)(`display` 의 내부/외부 값) — **이 상자가 바깥에서 어떻게 보이고 안을 어떻게 배치하는가**는 거기. 여기는 **치수가 정해지는 규칙**까지다
- [17번 주제](../17-block-formatting-context/2-summary.md)(서식 문맥) — 상자 **안의 일이 밖으로 새는지**는 거기
- [18번 주제](../18-margin-collapsing/2-summary.md)(마진 상쇄) — **마진 둘이 하나로 합쳐지는 규칙**은 거기. 여기는 **마진이 `box-sizing` 밖이라는 사실**까지다
- [목록의 **04번 주제**](../04-value-processing-stages/)(값 처리 단계) — `%`·`em` 이 **어느 단계에서 픽셀이 되는가**는 거기
- [목록의 **31번 주제**](../31-intrinsic-sizing-and-aspect-ratio/)(내재적 크기·`aspect-ratio`) — `min-content`/`fit-content` 같은 **"내용만큼"** 의 치수는 거기. 여기는 **고정 숫자를 준 경우**다
- [목록의 **33번 주제**](../33-length-units/)(길이 단위) — `%` 가 무엇의 비율인지의 정본
- [목록의 **07번 주제**](../07-syntax-and-error-recovery/)(오류 복구) — 없는 값이 **조용히 버려지는** 규칙
- [`reference/render-rules.md`](../../../../../../reference/render-rules.md) — 이 문서의 `demo` 블록 규칙

## 용어 풀이

- **콘텐츠 상자(content box)** — 글자·이미지가 놓이는 가장 안쪽 칸.
- **패딩 상자(padding box)** — content + padding. `clientWidth` 가 재는 칸이다.
- **테두리 상자(border box)** — padding 상자 + border. `getBoundingClientRect()` 가 재는 칸이다.
- **마진 상자(margin box)** — border 상자 + margin. 배경이 칠해지지 않아 눈에 안 보인다.
- **`box-sizing`** — `width`/`height` 숫자를 content 칸에 배정할지(`content-box`) border 칸에 배정할지(`border-box`) 정하는 속성. 값은 둘뿐이고 상속되지 않는다.
- **`width: auto`** — 폭을 선언하지 않은 상태. 블록 상자에서는 "부모에서 남는 자리를 다 쓴다"로 해결된다.
- **사용값(used value)** — 레이아웃이 실제로 쓴 픽셀 값. 선언한 값과 다를 수 있다(하한에 걸린 (6)이 그 예다). 정본은 [목록의 **04번 주제**](../04-value-processing-stages/).
- **`clientWidth`** — 요소의 padding 상자 폭(스크롤바 제외). 이 주제에서는 "안쪽 칸이 얼마나 남았나"를 재는 용도다.

---

## 더 들어가면

- **`box-sizing` 리셋의 정석 형태**는 `html { box-sizing: border-box } *, *::before, *::after { box-sizing: inherit }` 이다.\
  전체 선택자로 한 번에 박는 것보다 **컴포넌트 하나만 `content-box` 로 되돌릴 수 있다**는 점이 다르다.
- **테이블 셀과 대체 요소**(`<img>`·`<input>`)는 역사적으로 브라우저 기본 스타일시트가 다른 값을 쓴 적이 있다.\
  오늘은 리셋으로 덮는 것이 보통이지만, **폼 컨트롤은 기본 스타일이 엔진마다 달라** 치수를 재서 확인하는 편이 안전하다.
- **논리 속성**을 쓰면 `width`/`height` 대신 `inline-size`/`block-size` 가 된다.\
  `box-sizing` 은 그대로 적용되고, 글쓰기 방향이 바뀌면 **어느 축이 `inline-size` 인지**만 따라 돈다. 정본은 [목록의 **32번 주제**](../32-logical-properties-and-writing-mode/).
- `outline` 은 **네 겹 어디에도 속하지 않는다** — 레이아웃 공간을 전혀 차지하지 않고 상자 위에 그려진다.\
  포커스 링을 `border` 로 만들면 상자 치수가 흔들리는 이유가 이것이다. 정본은 [목록의 **46번 주제**](../46-borders-radius-outline-shadow/).

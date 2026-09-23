# css/syntax/44 — 배경과 대체 요소 맞춤 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [CSS Backgrounds and Borders Level 3](https://drafts.csswg.org/css-backgrounds-3/) (`background-*` 아홉 롱핸드와 레이어 규칙의 정본) · [CSS Images Level 3](https://drafts.csswg.org/css-images-3/) (`object-fit`·`object-position`·`contain`/`cover` 의 정본) · [CSS Backgrounds Level 4](https://drafts.csswg.org/css-backgrounds-4/) (`background-clip: text`). 열어서 확인한 것만 적었다.
> **실행 검증** — **Google Chrome 151.0.7922.173** headless 하나. 단축 분해를 `cssRules` 로 **10개 규칙** 받았고, 렌더 결과 **7장**을 스크린샷으로 찍어 **PNG 픽셀의 `(r,g,b)` 를 파이썬으로 읽어 칠해진 구간과 타일 위치를 좌표로 뽑았다.** 본문의 px 좌표는 전부 그 실측이다.
> **엔진은 Chrome 하나다** — Firefox 155 는 이 환경에서 headless 스크린샷이 산출되지 않는다. 크로스 브라우저는 **Baseline 데이터로만** 접지했고 「두 엔진에서 확인했다」고 적지 않았다.
> **버전** — `background-clip` = **widely**(2015-07-29) · `object-fit` = **widely**(low 2020-01-15 · high 2022-07-15) · `Gradients` = **widely**(2015-07-29) · ★ `background-clip: text` = **limited**(Chrome 120 / Safari 14 / **Firefox 는 접두사 없는 형태 미지원**) · ★ `background-attachment` = **limited**. `webstatus.dev` API 로 조회한 값이다(2026-09-23).
> **여기서 다루지 않는 것** — 이 배경이 칠해지는 **상자 네 겹 자체**는 [15번](../15-box-model-and-box-sizing/2-summary.md)이 정본이다. 배경으로 들어가는 **그라디언트 이미지**는 [45번](../45-gradients-and-interpolation/2-summary.md), 배경에 쓰는 **색 표기**는 [42번](../42-color-notation-and-spaces/2-summary.md)이 정본이다. **테두리와 `border-radius`** 는 [목록의 **46번 주제**](../46-borders-radius-outline-shadow/), **아래 레이어와 섞는 것**(`background-blend-mode`)은 [목록의 **48번 주제**](../48-blend-modes-and-isolation/), **잘라내기·마스킹**(`clip-path`·`mask`)은 [목록의 **49번 주제**](../49-clip-path-and-mask/)다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 수치는 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**배경은 유리창에 겹쳐 붙인 필름이고, 대체 요소 맞춤은 액자에 사진을 끼우는 것이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 유리창 | **요소의 상자** — [15번](../15-box-model-and-box-sizing/2-summary.md)의 네 겹 |
| 겹쳐 붙인 필름들 | **`background-image` 의 레이어들** — 쉼표로 여러 장 |
| 맨 뒤에 칠한 페인트 한 겹 | **`background-color`** — 레이어가 아니라 **언제나 맨 아래 한 장** |
| 필름을 창틀 어디에 맞춰 대나 | **`background-origin`** — 어디서 시작하나 |
| 창틀 밖으로 삐져나온 필름을 어디까지 남기고 자르나 | **`background-clip`** — 어디까지 보이나 |
| 액자 | **`<img>` 요소가 차지한 상자** |
| 액자에 끼운 사진 | **그 `<img>` 가 담은 실제 이미지** |
| 사진을 늘릴까 잘라낼까 | **`object-fit`** |

- **필름 두 장을 붙이면 먼저 쓴 것이 위다.** 직관과 반대다.\
  *(Chrome 151 실측: 빨강 레이어를 먼저, 파랑을 나중에 썼더니 둘이 겹친 자리가 `rgb(220, 38, 38)` 빨강이었다.)*
- **`background-origin` 과 `background-clip` 은 이름이 비슷하지만 하는 일이 정반대 방향**이다. 하나는 **시작점**, 하나는 **끝선**이다.
- **`object-fit` 은 배경이 아니다.** `<img>`·`<video>` 같은 **대체 요소**의 내용물에만 먹는다. `background-size` 와 **다른 층**이다.

```text
  배경 레이어 (먼저 쓴 것이 위)            대체 요소 (액자와 사진)

   ┌──────────────┐ ← 첫 번째 이미지        ┌──────────────┐ ← <img> 상자
   ├──────────────┤ ← 두 번째 이미지        │  ┌────────┐  │
   ├──────────────┤ ← 세 번째 이미지        │  │  사진   │  │ ← object-fit 이
   └──────────────┘ ← background-color      │  └────────┘  │    이 안쪽을 정한다
                       (언제나 맨 아래)      └──────────────┘
```

실무에서 이게 터지는 자리는 **아이콘 위에 그라디언트를 덮으려는 순간**이다.\
「그라디언트를 나중에 쓰면 위로 오겠지」 하고 쓰면 **아이콘이 그라디언트 위에 남는다.**

> **대체 요소(replaced element)** — 내용이 CSS 바깥에서 오는 요소. 브라우저가 그 내용물을 따로 그린다.\
> 예: `<img>`·`<video>`·`<iframe>`. `<div>` 는 대체 요소가 아니라서 `object-fit` 이 먹지 않는다.

> **배경 레이어(background layer)** — `background-image` 에 쉼표로 나열한 이미지 한 장과, 그것에 짝지어진 `position`·`size`·`repeat`·`origin`·`clip`·`attachment` 한 벌.\
> 예: 이미지를 둘 쓰면 `background-size` 도 쉼표로 둘 적어야 짝이 맞는다.

> **칠 영역(painting area)** — 배경이 실제로 칠해지는 범위. `background-clip` 이 정한다.\
> 예: `padding-box` 로 하면 테두리 아래는 안 칠해져 테두리가 뚫려 보인다.

> **위치 영역(positioning area)** — 배경 이미지의 좌표 `0 0` 이 어디인가. `background-origin` 이 정한다.\
> 예: `content-box` 로 하면 `0 0` 이 안쪽 내용 칸의 왼쪽 위 모서리다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 둔다.

1. 배경 이미지를 **여럿 쓰면 누가 위인가.** 그리고 `background-color` 는 그 줄에서 어디인가.
2. **`background-origin` 과 `background-clip` 은 무엇이 다른가** — 둘 다 `border-box`/`padding-box`/`content-box` 를 값으로 받는데.
3. `<img>` 를 상자에 맞추는 일은 왜 `background-size` 로 안 되나 — **무엇이 다른 층인가.**

## 동작 방식

### (1) `background` 단축이 푸는 아홉 가지

**언제 쓰나** — 단축 한 줄을 읽을 때마다. 무엇이 **조용히 초기화되는지**를 알아야 한다.

```text
  background: #eee url(dot.png) no-repeat right 10px bottom 20px / 40px 30px content-box padding-box;
              ─┬─  ─────┬────── ────┬──── ───────────┬────────── ────┬───── ─────┬───── ─────┬──────
               │        │           │                │               │           │           │
               │        │           │                │               │           │           └ clip
               │        │           │                │               │           └───────────── origin
               │        │           │                │               └──────────── size (/ 뒤)
               │        │           │                └──────────────────────────── position
               │        │           └───────────────────────────────────────────── repeat
               │        └───────────────────────────────────────────────────────── image
               └────────────────────────────────────────────────────────────────── color
```

실측 — 위 한 줄을 던져 롱핸드를 받았다.

```text
  background-image       url("data:image/gif;base64,...")
  background-position-x  right 10px
  background-position-y  bottom 20px
  background-size        40px 30px
  background-repeat      no-repeat
  background-origin      content-box
  background-clip        padding-box
  background-attachment  initial      ← 안 적으면 initial 로 리셋된다 ★
  background-color       rgb(238, 238, 238)
```

- ★ **단축은 안 적은 롱핸드를 전부 `initial` 로 되돌린다.** `background: red` 한 줄이 앞서 적어 둔 `background-image` 를 지운다.
- ★ **상자 값을 하나만 적으면 `origin` 과 `clip` 에 **둘 다** 들어간다.** 실측:

```text
  적은 것                          origin        clip
  -------------------------------  ------------  ------------
  background: padding-box red      padding-box   padding-box   ← 하나가 둘로
  background: content-box red      content-box   content-box   ← 하나가 둘로
  background: border-box padding-box red   border-box   padding-box   ← 둘이면 순서대로
```

- `position` 과 `size` 는 **`/` 로 갈린다.** `/` 없이 `40px 30px` 을 더 적으면 위치로 읽힌다.
- **`position-x`/`position-y` 는 롱핸드가 따로 있다.** `background-position` 은 그 둘의 단축이다.

비용 — 단축의 편리함 값이 **「안 적은 것이 리셋된다」** 는 규칙이다. 미디어 쿼리 안에서 한 조각만 바꾸려면 **롱핸드로 적어야 한다.**

### (2) ★ 레이어 순서 — 먼저 쓴 것이 위

**언제 쓰나** — 배경 이미지를 둘 이상 쓸 때마다. **직관과 반대라 반드시 실측으로 확인한다.**

```text
  background-image:
    linear-gradient(90deg, 빨강 0 100px, transparent 100px),   ← 첫째
    linear-gradient(90deg, 파랑 0 150px, transparent 150px);   ← 둘째

  겹치는 구간(0\~100px)에서 누가 보이나?
```

```text
  0px        100px      150px      200px
  ├───────────┼──────────┼──────────┤
  │ 빨강+파랑 │  파랑만  │  아무것도 │
  │  겹침     │          │   없음    │

  실측 픽셀 (y = 30)
    x=50   rgb(220, 38, 38)    ← 빨강. 첫째 레이어가 이겼다 ★
    x=120  rgb( 37, 99, 235)   ← 파랑. 여기는 둘째만 있다
    x=180  rgb(255, 255, 255)  ← 둘 다 투명. 페이지 배경이 보인다
```

```text
  쌓이는 순서 — 소스에 적은 순서가 위에서 아래로 내려간다

     소스 첫째  ───────────────  가장 위     (z 가 가장 높다)
     소스 둘째  ───────────────
     소스 셋째  ───────────────
     background-color ─────────  가장 아래  (레이어가 아니다. 언제나 맨 밑 한 장)
```

- **`background-color` 는 레이어 목록에 들어가지 않는다.** 쉼표로 여러 개 적을 수도 없고, 언제나 **모든 이미지 아래**에 한 장 깔린다.
- 실측: `background: url(a.png), url(b.png); background-color: blue;` 를 던졌더니 `background-image` 는 두 항목, `background-color` 는 `blue` 하나였다. **이미지 롱핸드는 전부 쉼표로 둘씩 짝지어졌고 색만 하나였다.**

비용 — 짝 맞추기가 번거롭다. 이미지를 둘 쓰면 `size`·`position`·`repeat` 도 **둘씩** 적어야 한다. 하나만 적으면 그 값이 반복 적용된다.

### (3) ★ `background-origin` 과 `background-clip` — 이름은 비슷, 일은 정반대

**언제 쓰나** — 배경이 테두리 밑으로 비쳐 보일 때, 이미지 위치가 예상과 어긋날 때. **이것이 이 주제의 과녁이다.**

같은 상자(`width:200px; height:100px; border:10px solid transparent; padding:20px`)에 한 번은 `origin` 만, 한 번은 `clip` 만 바꿔 던졌다.

```text
  상자의 가로 좌표 (테두리 10, 패딩 20)

   0    10        30                        230       250  260
   ├────┼─────────┼─────────────────────────┼──────────┼────┤
   │border│ padding │       content          │ padding  │border│
```

**`origin` 을 바꾸면 — 타일의 시작점이 움직인다. 칠 영역은 그대로.**

```text
  값             주황 점(16px 타일의 원)의 상자   칠해진 x 구간
  -------------  ------------------------------  --------------
  border-box     x  4..11,  y  4..11             0..259
  padding-box    x 14..21,  y 14..21             0..259
  content-box    x 34..41,  y 34..41             0..259
                    ↑ 시작 모서리가 0 → 10 → 30    ↑ 셋 다 똑같다
```

**`clip` 을 바꾸면 — 칠 영역이 잘린다. 타일 시작점은 그대로.**

```text
  값             칠해진 x 구간      테두리 띠(y=5)   패딩 띠(y=15)   내용 칸(y=45)
  -------------  ----------------  --------------  -------------  -------------
  border-box     0..259            칠해짐           칠해짐          칠해짐
  padding-box    10..249           안 칠해짐 ★      칠해짐          칠해짐
  content-box    30..229           안 칠해짐        안 칠해짐 ★     칠해짐
```

```text
  origin = 자 눈금의 0 을 어디에 두나        clip = 종이를 어디서 자르나

  ┌─────────────────────────┐              ┌─────────────────────────┐
  │ border                  │              │ border                  │
  │  ┌───────────────────┐  │              │  ┌───────────────────┐  │
  │  │ padding           │  │              │  │ padding           │  │
  │  │  ┌─────────────┐  │  │              │  │  ┌─────────────┐  │  │
  │  │  │ content     │  │  │              │  │  │ content     │  │  │
  │  │  └─────────────┘  │  │              │  │  └─────────────┘  │  │
  │  └───────────────────┘  │              │  └───────────────────┘  │
  └─────────────────────────┘              └─────────────────────────┘
     ↑    ↑    ↑                              └──────── 이 선까지만 칠한다
     세 자리 중 하나가 「0 0」이 된다
     (칠하는 범위는 안 바뀐다)
```

- **`origin` 은 「위치 영역」을, `clip` 은 「칠 영역」을 정한다.** 한 낱말로: **시작점 대 끝선**.
- **점선·반투명 테두리를 쓸 때 `clip` 이 눈에 띈다.** 실선 불투명 테두리면 테두리가 배경을 가려서 차이가 안 보인다.
- **`origin` 은 `background-attachment: fixed` 일 때 무시된다**(위치 영역이 뷰포트가 되기 때문).
- 실측에서 확인한 짝: **`origin` 을 셋 다 바꿔도 칠해진 구간은 `0..259` 로 같았고, `clip` 을 셋 다 바꿔도 타일 시작점은 안 움직였다.** 두 축이 완전히 독립이다.

비용 — 없다. 다만 **단축에서 상자 값을 하나만 적으면 둘 다 바뀐다**((1))는 것이 이 독립성을 가린다.

### (4) `background-clip: text` — 네 번째 값

**언제 쓰나** — 글자에 그라디언트를 입힐 때.

```text
  background-clip: text
     → 칠 영역이 「글자 모양」이 된다. 글자 바깥은 안 칠해진다.
     → 글자 자체는 color 로 칠해져 배경을 덮으므로
       color: transparent 를 같이 줘야 배경이 보인다 ★
```

실측 — 세 경우를 렌더해 **흰색이 아닌 픽셀 수**를 셌다.

```text
  선언                                   흰색 아닌 픽셀   왼쪽 위(5,10)        글자 속(25,40)
  -------------------------------------  --------------  -------------------  -----------------
  clip: text + color: transparent          2,718         rgb(255, 255, 255)   rgb(209, 35, 86) ★
  기본 clip(border-box)                   21,600         rgb(222, 31,  75)    rgb(  0,  0,  0)
  clip: text + color 기본(검정)             2,718         rgb(255, 255, 255)   rgb(  0,  0,  0) ★
```

- **`clip: text` 만 주면 글자가 여전히 검정**이다(셋째 줄). 배경은 글자 모양으로 잘려 있지만 **글자가 그 위를 덮는다.**
- `color: transparent` 를 같이 줘야 아래의 그라디언트가 드러난다(첫째 줄 — 글자 속 픽셀이 `rgb(209, 35, 86)` 이다).
- 첫째와 셋째의 **칠해진 픽셀 수가 2,718 로 똑같다** — 칠 영역은 같고 그 위를 덮는 글자색만 다르다는 증거다.
- **Chrome 151 에서 `-webkit-background-clip` 은 같은 속성의 별칭**이다(실측: 둘 다 계산값 `text`). 하지만 **Baseline 이 `limited`** 다 — 접두사 없는 `background-clip: text` 는 Firefox 가 아직 지원하지 않는다(webstatus.dev). **접두사를 같이 적는 편이 안전하다.**

비용 — 글자를 `transparent` 로 만들면 **배경 이미지가 안 뜨는 환경에서 글자가 사라진다.** `@supports` 로 감싸는 편이 좋다.

### (5) `background-size` — 세 가지 방식

**언제 쓰나** — 이미지 비율과 상자 비율이 다를 때. `cover`/`contain` 이 **무엇을 희생하는지**가 요점이다.

```text
  16×8 (2:1) 이미지를 120×120 상자에 넣는다.  background-position 은 기본값 0% 0%.

  값             그림이 놓인 칸              무엇을 했나
  -------------  -------------------------  -------------------------------
  auto           x 0..15,  y 0..7           자연 크기 그대로. 왼쪽 위에 붙었다
  100% 100%      x 0..119, y 0..119         비율을 무시하고 상자를 채웠다 (일그러진다)
  contain        x 0..119, y 0..59          짧은 쪽을 맞춘다. 아래 절반이 빈다
  cover          x 0..119, y 0..119         긴 쪽을 맞춘다. 좌우가 잘려 나간다
```

```text
  contain — 다 보이게, 여백이 남는다        cover — 꽉 차게, 잘린다
  ┌──────────────┐                          ┌──────────────┐
  │■■■■■■■■■■■■■■│ ← 그림                   │■■■■■■■■■■■■■■│
  │■■■■■■■■■■■■■■│                          │■■■■■■■■■■■■■■│ ← 그림이 상자보다
  ├──────────────┤                          │■■■■■■■■■■■■■■│    크다. 넘치는
  │   빈 칸      │                          │■■■■■■■■■■■■■■│    부분은 안 보인다
  └──────────────┘                          └──────────────┘
    아무것도 안 잘린다                        여백이 안 생긴다
```

- **`cover` 는 「잘려도 좋으니 채워라」, `contain` 은 「여백이 남아도 좋으니 다 보여라」** 다.
- **어디가 잘리고 어디가 비는지는 `background-position` 이 정한다.** 기본이 `0% 0%`(왼쪽 위)이라 실측에서 그림이 위쪽에 붙었다.
- **`cover`/`contain` 은 계산값이 키워드 그대로 남는다**(실측 — `contain`·`cover`). 실제 픽셀 치수는 **사용값** 단계다([04번](../04-value-processing-stages/2-summary.md)).

비용 — `cover` 는 **중요한 부분이 잘릴 수 있다.** 사람 얼굴이 든 이미지면 `background-position` 을 같이 조정해야 한다.

### (6) `background-repeat` — `space` 와 `round` 가 갈리는 자리

**언제 쓰나** — 타일이 상자 폭에 딱 안 떨어질 때. 넷의 차이가 여기서만 보인다.

**실측 조건** — 폭 **180px** 상자에 **50px** 타일. `180 / 50 = 3.6` 이라 딱 안 떨어진다.

```text
  값          타일 수   주황 점의 중심 간격   무엇을 희생했나
  ----------  --------  -------------------  -----------------------------
  repeat-x       4      50, 50, 46.5         마지막 타일이 잘렸다
  space          3      65, 65               타일 사이에 틈을 넣었다. 크기는 유지 ★
  round          4      45, 45, 45           타일을 줄였다(50 → 45). 틈은 없다 ★
  no-repeat      1      —                    한 장만
```

```text
  180px 안에 50px 타일을 어떻게 넣나

  repeat   [50][50][50][30↲]         마지막이 잘린다
  space    [50]  [50]  [50]          3장 + 틈 15px 씩.  크기 그대로
  round    [45][45][45][45]          4장. 45px 로 줄였다.  틈 없음
                                         ↑ 180/4 = 45
```

- **`space` 는 정수 개만 넣고 남는 폭을 틈으로 뿌린다.** 타일 크기를 **절대 안 바꾼다.**
- **`round` 는 타일 크기를 바꿔 정수 개로 맞춘다.** `3.6` 을 반올림해 `4` 개를 넣었고, `180/4 = 45` 로 줄였다.
- ★ **`round` 로 줄어든 크기는 `background-size` 계산값에 안 나온다** — 실측에서 네 경우 모두 계산값이 `40px 40px`(그 실험의 값) 그대로였다. **사용값 단계의 일**이라 계산값만 읽으면 못 본다([04번](../04-value-processing-stages/2-summary.md)과 같은 구조).

비용 — `round` 는 **이미지를 늘이거나 줄이므로 화질이 상한다.** `space` 는 틈이 생긴다.

### (7) `background-position` — 네 값 구문

**언제 쓰나** — 「오른쪽에서 10px 띄운 자리」처럼 모서리 기준으로 붙일 때.

```text
  실측 — 20px 타일을 200×60 상자에

  선언                                 계산값                                주황 점의 상자
  -----------------------------------  -----------------------------------  ---------------
  background-position: 10px 10px       10px 10px                            x 15..24
  background-position: right bottom    100% 100%                            x 185..194
  background-position: 100% 100%       100% 100%                            x 185..194
  background-position: right 10px bottom 10px   calc(100% - 10px) calc(100% - 10px)   x 175..184 ★
```

```text
  두 값 구문 vs 네 값 구문

  right bottom            →  오른쪽 아래 모서리에 딱 붙인다
  right 10px bottom 10px  →  오른쪽에서 10px, 아래에서 10px 안으로
                              ↑ "가장자리 키워드 + 거리" 가 한 쌍이다

  주의: 10px 10px 은 「왼쪽에서 10px, 위에서 10px」이다 (기본 기준이 left top)
```

- ★ **네 값 구문의 계산값이 `calc(100% - 10px)` 로 나온다**(실측). 「오른쪽에서 10px」이 그렇게 표현된다.
- **`%` 는 「이미지의 그 지점이 영역의 그 지점에 온다」는 뜻**이다. `100% 100%` 는 이미지의 오른쪽 아래가 영역의 오른쪽 아래에 맞는다는 것 — **「영역 폭의 100% 만큼 오른쪽으로 민다」가 아니다.**

비용 — 없다. 다만 `%` 의 뜻이 다른 속성과 달라서 자주 틀린다.

### (8) `background-attachment` — 위치 영역이 바뀐다

**언제 쓰나** — 스크롤해도 배경이 안 따라가게 할 때. **흔치 않게 「위치 영역」 자체를 갈아 치우는 값**이다.

```text
  값       위치 영역이 무엇인가
  -------  ---------------------------------------------
  scroll   요소의 상자 (기본값)
  local    요소의 내용 전체 (요소 안을 스크롤하면 따라 움직인다)
  fixed    ★ 뷰포트 — 요소의 상자가 아니다
```

실측 — 폭 100px 상자에 `linear-gradient(90deg, #e11d48, #2563eb)` 를 주고 값만 바꿨다.

```text
  값       x=2 의 픽셀           x=50               x=98
  -------  -------------------  -----------------  -------------------
  scroll   rgb(220, 30, 76)     rgb(130, 64, 154)  rgb( 40,  98, 232)   ← 100px 안에서 다 변했다
  local    rgb(220, 30, 76)     rgb(130, 64, 154)  rgb( 39,  98, 232)   ← scroll 과 같다
  fixed    rgb(223, 29, 73)     rgb(200, 38,  93)  rgb(177,  47, 113)   ★ 거의 안 변했다
```

- **`fixed` 는 그라디언트가 뷰포트 폭에 맞춰 늘어난다.** 그래서 100px 상자 안에는 **앞부분 한 조각만** 들어온다.
- `scroll` 과 `local` 은 스크롤하지 않은 한 장면에서는 **구분되지 않는다**(실측에서 픽셀이 1 단위 차이였다). 차이는 **요소 안을 스크롤할 때** 난다 — 이 실험으로는 **잴 수 없다.**
- ★ **Baseline 이 `limited`** 다(webstatus.dev). 특히 모바일에서 `fixed` 가 무시되는 구현이 있다고 알려져 있으나 **이 환경에서 확인하지 못했다.**

비용 — `fixed` 는 **스크롤마다 배경을 다시 그려야 해서 비싸다.** 그리고 **`background-origin` 을 무시한다.**

### (9) ★ `object-fit` — 배경이 아니라 대체 요소용

**언제 쓰나** — `<img>`·`<video>` 를 고정 크기 칸에 넣을 때. **`background-size` 와 다른 층이라는 것이 이 절의 과녁이다.**

```text
  두 층이 다르다

  <div> 에 background-image        <img> 에 src
   ┌──────────────┐                 ┌──────────────┐
   │              │                 │              │
   │  배경 그리기  │                 │  대체 내용물  │
   │  단계에서 그림 │                │  그리기 단계   │
   └──────────────┘                 └──────────────┘
   background-size 가 정한다         object-fit 이 정한다
   background-position 이 정한다     object-position 이 정한다
   ↑ 기본 0% 0% (왼쪽 위)            ↑ 기본 50% 50% (가운데)  ★ 기본값이 다르다
```

같은 **16×8 이미지**를 같은 **120×120 칸**에 넣고, 한쪽은 `<img>` 에 `object-fit`, 한쪽은 `<div>` 에 `background-size` 로 던졌다.

```text
  값의 이름이 같아도 결과가 다르다 — 기본 정렬이 다르기 때문이다

  object-fit: contain     그림이 x 0..119, y  30..89    ← 세로 가운데
  background-size: contain 그림이 x 0..119, y   0..59   ← 세로 위쪽 ★

  object-fit: none        그림이 x 52..67, y 56..63     ← 한가운데
  background-size: auto   그림이 x  0..15, y  0..7      ← 왼쪽 위 ★
```

```text
  cover 일 때 — 같은 키워드, 다른 픽셀 (y=60 가로줄)

  object-fit: cover        x=5  파랑 / x=55 파랑 / x=65 빨강 / x=115 빨강
                           → 가운데를 기준으로 좌우를 고르게 잘랐다
  background-size: cover   x=5  파랑 / x=55 파랑 / x=65 파랑 / x=115 파랑
                           → 왼쪽에 붙여 놓고 오른쪽을 잘랐다  ★
```

- **두 층의 기본 정렬이 다르다** — `object-position` 기본 `50% 50%`, `background-position` 기본 `0% 0%`.
- **`object-fit` 을 `<div>` 에 주면 아무 일도 안 일어난다.** 대체 요소가 아니기 때문이다 — 선언은 담기고 계산값도 나오지만 **그릴 내용물이 없다.**
- `scale-down` 은 **`none` 과 `contain` 중 더 작은 쪽**이다. 실측에서 16×8 이미지가 120×120 칸보다 작아 `none` 과 같은 결과(x 52..67)였다.
- **`<img>` 상자 자체의 크기는 `object-fit` 이 안 바꾼다** — 실측에서 다섯 값 전부 `rect` 가 `120x120` 이었다. 바뀌는 것은 **안에 든 그림**뿐이다.

비용 — 없다. 다만 **두 이름을 섞어 쓰면 기본 정렬 때문에 결과가 어긋난다.** `<img>` 에는 `object-position: 50% 50%` 가 기본이니 대개 그대로 두면 된다.

## 화면으로 — demo

### 먼저 쓴 레이어가 위다

```html demo
<div class=stack></div>
<style>
  .stack {
    width: 220px; height: 60px;
    background-image:
      linear-gradient(90deg, #dc2626 0 110px, transparent 110px),  /* 첫째 */
      linear-gradient(90deg, #2563eb 0 165px, transparent 165px);  /* 둘째 */
    background-repeat: no-repeat;
  }
</style>
```

> **보이는 것** — 가로로 긴 상자가 **왼쪽부터 빨강 → 파랑 → 아무것도 없음** 세 구간으로 나뉜다. 빨강 구간이 왼쪽 끝에서 110px, 파랑 구간이 거기서 165px 까지, 그 뒤는 페이지 바탕이다. **두 레이어가 겹치는 0\~110px 구간에서 나중에 쓴 파랑이 아니라 먼저 쓴 빨강이 보인다.**\
> **바꿔 볼 것** — 두 `linear-gradient` 줄의 순서를 바꾸면 → 겹치는 구간이 **파랑**이 된다 · 첫째의 `110px` 을 `220px` 로 → 파랑이 아예 안 보인다

*(Chrome 151 headless 실측 — y=30 에서 x=50 `rgb(220, 38, 38)`(빨강) · x=130 `rgb(37, 99, 235)`(파랑) · x=190 `rgb(255, 255, 255)`(바탕).)*

### `origin` 은 시작점, `clip` 은 끝선

```html demo
<div class=b style="background-origin:border-box;  background-clip:border-box"></div>
<div class=b style="background-origin:content-box; background-clip:border-box"></div>
<div class=b style="background-origin:content-box; background-clip:content-box"></div>
<style>
  .b { width: 180px; height: 70px; margin-bottom: 8px;
       border: 10px solid transparent; padding: 20px;
       background-color: #2563eb;
       background-image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAYAAADED76LAAAAH0lEQVR42mNgoBQwwhj/Oxj+o0hUQOSYCJlAuQLKAQAwZAMIRRDoMgAAAABJRU5ErkJggg==);
       background-repeat: no-repeat; background-size: 16px 16px; }
</style>
```

> **보이는 것** — 파란 상자 셋이 세로로 있다. **첫째와 둘째는 파란 칠의 크기가 똑같은데 주황 점의 자리만 다르다** — 첫째는 상자 맨 왼쪽 위 모서리, 둘째는 거기서 오른쪽 아래로 30px 들어온 자리다(여기까지가 `origin` 만 바뀐 짝). **둘째와 셋째는 주황 점이 같은 자리인데 파란 칠이 사방 30px 씩 작다**(여기가 `clip` 만 바뀐 짝). 곧 두 속성이 서로의 일을 전혀 건드리지 않는다.\
> **바꿔 볼 것** — `border: 10px solid transparent` 를 `10px dashed #000` 으로 → 셋째에서 테두리 틈으로 바탕이 비치는 것이 보인다 · 둘째의 `content-box` 를 `padding-box` 로 → 점이 14\~21px 자리로 온다

*(Chrome 151 headless 실측 — 상자는 240×130(내용 180×70 + 패딩 20 + 테두리 10). 주황 점의 상자: 첫째 x 4..11 y 4..11 / 둘째·셋째 x 34..41 y 34..41. 칠해진 구간: 첫째·둘째 x 0..239 y 0..129 / 셋째 x 30..209 y 30..99. 곧 `origin` 을 바꿔도 칠 구간은 안 변하고, `clip` 을 바꿔도 점의 자리는 안 변한다.)*

### 같은 `cover` 인데 결과가 다른 이유

```html demo
<img class=c src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAICAIAAAB/FOjAAAAAIUlEQVR42mMUW+zFQApgYiARMKomv8Yqsf2wNXVsGA4aAAepBDqJX/jvAAAAAElFTkSuQmCC">
<div class="c bg"></div>
<style>
  .c { width: 120px; height: 120px; display: inline-block; vertical-align: top;
       background-color: #e2e8f0; image-rendering: pixelated; }
  img.c  { object-fit: cover; }
  .bg { background-image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAICAIAAAB/FOjAAAAAIUlEQVR42mMUW+zFQApgYiARMKomv8Yqsf2wNXVsGA4aAAepBDqJX/jvAAAAAElFTkSuQmCC);
        background-size: cover; background-repeat: no-repeat; }
</style>
```

> **보이는 것** — 같은 그림(위쪽에 초록 띠, 아래는 왼쪽 절반 파랑·오른쪽 절반 빨강)을 담은 정사각형 칸 둘이 나란히 있다. **왼쪽 `<img>` 칸은 가운데 세로줄을 기준으로 왼쪽이 파랑, 오른쪽이 빨강으로 반반**이고, **오른쪽 `<div>` 칸은 아래쪽이 전부 파랑**이다. 둘 다 `cover` 인데 잘린 자리가 다르다 — `object-position` 의 기본은 가운데(`50% 50%`), `background-position` 의 기본은 왼쪽 위(`0% 0%`)이기 때문이다.\
> **바꿔 볼 것** — `.bg` 에 `background-position: center` 를 더하면 → 두 칸이 같아진다 · `object-fit: cover` 를 `contain` 으로 → 왼쪽 칸에 위아래 여백이 생긴다

*(Chrome 151 headless 실측 — y=60 가로줄에서 `<img>` 쪽은 x=5·55 가 `rgb(37, 99, 235)`(파랑), x=65·115 가 `rgb(220, 38, 38)`(빨강). `<div>` 쪽은 x=5·55·65·115 가 전부 `rgb(37, 99, 235)`(파랑). 두 칸의 `getBoundingClientRect()` 는 둘 다 `120x120` 이었다.)*

## 문법 — 형태와 규칙

CSS 는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태

```css
/* 단축 — 레이어마다 한 벌씩, 쉼표로 나눈다. color 는 마지막 레이어에만 */
background: url(a.png) no-repeat center / cover border-box padding-box,
            linear-gradient(#fff, #eee) repeat-x,
            #eee;

/* 롱핸드 — 미디어 쿼리 안에서 한 조각만 바꿀 때는 이쪽 */
background-image:      url(a.png), linear-gradient(#fff, #eee);
background-position:   center, 0 0;      /* 레이어 수만큼 */
background-size:       cover, auto;
background-repeat:     no-repeat, repeat-x;
background-origin:     content-box, padding-box;
background-clip:       padding-box, border-box;
background-attachment: scroll, scroll;
background-color:      #eee;             /* 쉼표가 없다. 언제나 하나 */

/* 대체 요소 — 배경과 다른 층 */
img { object-fit: cover; object-position: 50% 30%; }
```

### 금지 사례 — 안 되거나 조용히 어긋나는 형태

```css
background-color: red, blue;              /* 쉼표를 안 받는다. 선언째 버려진다 */
background: red; background-image: url(a); /* 순서가 반대면 단축이 이미지를 지운다 */
div { object-fit: cover; }                 /* 대체 요소가 아니라 아무 일도 안 일어난다 */
background: url(a) 10px 20px 40px 30px;    /* / 가 없으면 size 가 아니라 position 으로 읽힌다 */
```

### 어디서 헷갈리나 — 이름 여섯

| 이름 | 무엇인가 | 헷갈리는 짝 |
|---|---|---|
| `background-origin` | **시작점** — 이미지의 `0 0` 이 어디 | `background-clip` — **끝선** |
| `background-clip` | **칠 영역** — 어디까지 보이나 | `clip-path`([목록의 **49번 주제**](../49-clip-path-and-mask/)) — 요소 전체를 자른다 |
| `background-size: cover` | 상자를 채운다. **잘린다** | `object-fit: cover` — 같은 규칙, **기본 정렬이 가운데** |
| `background-repeat: space` | 정수 개 + 틈. **크기 유지** | `round` — 정수 개, **크기 변경** |
| `background-attachment: fixed` | **위치 영역이 뷰포트**가 된다 | `position: fixed` — 요소 자체가 고정된다 |
| `background-position: 100%` | 「이미지의 오른쪽 끝이 영역의 오른쪽 끝에」 | 「영역 폭만큼 오른쪽으로 민다」가 아니다 |

## 어디서 틀리나

### 1. 나중에 쓴 레이어가 위라고 생각한다

**먼저 쓴 것이 위다**((2) 실측 — 겹친 자리가 첫째 레이어 색이었다). `z-index` 나 쌓임 맥락과 직관이 반대다.

### 2. `background-color` 를 레이어로 센다

레이어가 아니다. 쉼표로 여러 개 적을 수 없고 **언제나 맨 아래 한 장**이다.

### 3. `origin` 과 `clip` 을 같은 것으로 본다

**독립이다**((3) 실측 — `origin` 셋을 바꿔도 칠 구간이 `0..259` 로 같았고, `clip` 셋을 바꿔도 타일 시작점이 안 움직였다).

### 4. 단축에 상자 값을 하나만 적고 `clip` 만 바꿨다고 생각한다

**`origin` 과 `clip` 둘 다 바뀐다**((1) 실측). 하나만 바꾸려면 롱핸드를 쓴다.

### 5. `background: red` 한 줄로 색만 바꾸려 한다

단축은 **안 적은 롱핸드를 전부 `initial` 로 되돌린다**. 앞서 적은 `background-image` 가 사라진다.

### 6. `background-clip: text` 만 주고 글자가 검정인 이유를 못 찾는다

**글자가 배경 위를 덮고 있다**((4) 실측 — 칠해진 픽셀 수는 같고 글자 속 색만 달랐다). `color: transparent` 를 같이 준다.

### 7. `round` 로 줄어든 타일 크기를 `getComputedStyle` 로 읽으려 한다

**안 나온다**((6) 실측 — 계산값이 선언값 그대로였다). 사용값 단계의 일이라 **픽셀을 재야** 안다.

### 8. `object-fit` 을 `<div>` 에 준다

대체 요소가 아니라 아무 일도 안 일어난다. 선언은 담기고 계산값도 나오므로 **진단 3창으로도 안 잡힌다.**

### 9. `object-fit: cover` 와 `background-size: cover` 가 같다고 본다

규칙은 같지만 **기본 정렬이 다르다**((9) 실측 — 같은 이미지·같은 칸에서 잘린 자리가 달랐다).

## 구현 세부사항 대 언어 보장

| 항목 | 누가 보장하나 | 근거 |
|---|---|---|
| **먼저 쓴 레이어가 위**인 것 | **언어 보장** | Backgrounds 3 의 레이어 순서 정의. 실측이 일치 |
| `background-color` 가 **맨 아래 한 장**인 것 | **언어 보장** | 〃 |
| `origin` 과 `clip` 이 **독립**인 것 | **언어 보장** | 각각 「위치 영역」·「칠 영역」으로 따로 정의돼 있다 |
| 단축에서 **상자 값 하나가 둘로 퍼지는** 것 | **언어 보장** | 단축 문법 정의. 실측 세 경우가 일치 |
| `space`/`round` 의 개수 계산(`floor` 대 반올림) | **언어 보장** | 실측: 3.6 에서 `space` 는 3개, `round` 는 4개 |
| `round` 로 줄어든 크기가 **계산값에 안 보이는** 것 | **CSSOM 직렬화 = 구현 표면** | 사용값 단계라 계산값에 안 나온다. [04번](../04-value-processing-stages/2-summary.md)의 구조와 같다 |
| 네 값 위치가 `calc(100% - 10px)` 로 **직렬화되는** 것 | **CSSOM 직렬화 형식** | 실측. 다른 엔진은 다른 문자열을 낼 수 있다 |
| `-webkit-background-clip` 이 **같은 속성의 별칭**인 것 | **구현(Chrome)** | 실측: 둘 다 계산값 `text`. **다른 엔진의 동작은 확인하지 못했다** |
| `background-clip: text` 를 **쓸 수 있는가** | **구현 — Baseline `limited`** | Chrome 120 / Safari 14. Firefox 는 접두사 없는 형태 미지원(webstatus.dev) |
| `background-attachment` 의 지원 | **구현 — Baseline `limited`** | webstatus.dev. **이 환경에서 모바일 동작은 확인하지 못했다** |
| `scroll` 과 `local` 의 차이 | **못 잰 것** ★ | 한 장면 스크린샷으로는 **측정 방법 자체가 성립하지 않는다**. 요소 안을 실제로 스크롤해야 갈린다 |

★ **「못 잰 것」은 「안 돌려 본 것」과 다르다.** `scroll` 대 `local` 은 던져서 픽셀까지 받았고(1 단위 차이로 같았다), **그 실험으로는 구분이 성립하지 않는다**는 것이 결과다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 안 쓸 것 |
|---|---|---|
| 카드 썸네일을 칸에 채운다 | `<img>` + `object-fit: cover` | 배경 이미지 — 대체 텍스트가 사라진다 |
| 장식용 무늬 | `background-image` | `<img>` — 스크린 리더가 읽는다 |
| 미디어 쿼리에서 배경 한 조각만 바꾼다 | 롱핸드 | 단축 — 나머지가 리셋된다 |
| 테두리 아래로 배경이 비치면 곤란하다 | `background-clip: padding-box` | `background-origin` — 칠 범위를 안 바꾼다 |
| 타일을 틈 없이 깔되 잘리면 곤란하다 | `background-repeat: round` | `space` — 틈이 생긴다 |
| 타일 크기가 중요하다 | `space` | `round` — 크기를 바꿔 버린다 |
| 글자에 그라디언트 | `background-clip: text` + `-webkit-` 접두사 + `@supports` | 접두사 없이 단독 — Baseline `limited` |
| 스크롤해도 안 따라오는 배경 | `background-attachment: fixed` | 성능이 중요한 화면 — 스크롤마다 다시 그린다 |
| 아이콘 위에 무늬를 덮는다 | **무늬를 먼저** 쓴다 | 나중에 쓰기 — 아래로 간다 |

## 핵심 문장

- **배경 레이어는 먼저 쓴 것이 위다.** `background-color` 는 레이어가 아니라 언제나 맨 아래 한 장이다.
- **`origin` 은 시작점, `clip` 은 끝선.** 완전히 독립이고, 단축에서 상자 값 하나를 적으면 둘 다 바뀐다.
- **`cover` 는 잘리고 `contain` 은 여백이 남는다.** 어디가 잘리는지는 `position` 이 정한다.
- **`space` 는 크기를 지키고 `round` 는 개수를 맞춘다.** `round` 로 줄어든 크기는 계산값에 안 보인다.
- **`object-fit` 은 대체 요소용이라 `background-size` 와 다른 층이다.** 기본 정렬이 가운데와 왼쪽 위로 다르다.

## 관련 자료

| 문서 | 경계 |
|---|---|
| [15 박스 모델과 `box-sizing`](../15-box-model-and-box-sizing/2-summary.md) | **그쪽이 네 겹 상자의 정본**이다. 여기는 **그 네 겹 중 어디에 칠하고 어디서 시작하나**부터 |
| [04 값 처리 단계](../04-value-processing-stages/2-summary.md) | **그쪽이 계산값·사용값의 정본**이다. 여기는 **`round`·`cover` 가 사용값 단계라 계산값에 안 보인다**는 사례까지 |
| [42 색 표기와 색 공간](../42-color-notation-and-spaces/2-summary.md) | **그쪽이 `background-color` 에 넣을 색 표기의 정본**이다 |
| [45 그라디언트와 보간 색 공간](../45-gradients-and-interpolation/2-summary.md) | **그쪽이 그라디언트 이미지 자체의 정본**이다. 여기는 **그것이 `background-image` 자리에 오는 레이어의 한 장**이라는 것까지 |
| [목록의 **46번 주제**](../46-borders-radius-outline-shadow/) (테두리·`border-radius`·그림자) | **테두리 자체**는 그쪽. 여기는 **테두리 아래를 칠하느냐**까지 |
| [목록의 **48번 주제**](../48-blend-modes-and-isolation/) (혼합 모드) | `background-blend-mode` 로 **레이어끼리 섞는 것**은 그쪽. 여기는 **누가 위인가**까지 |
| [목록의 **49번 주제**](../49-clip-path-and-mask/) (`clip-path`·`mask`) | **요소 전체를 잘라내는 것**은 그쪽. `background-clip` 은 **배경만** 자른다 |
| [목록의 **41번 주제**](../41-supports-feature-queries/) (`@supports`) | `background-clip: text` 가 `limited` 라 갈라야 할 때 |

## 용어 풀이

- **대체 요소(replaced element)** — 내용이 CSS 바깥에서 오는 요소. 예: `<img>`·`<video>`. `<div>` 는 아니라서 `object-fit` 이 안 먹는다.
- **배경 레이어(background layer)** — 이미지 한 장과 그것에 짝지어진 위치·크기·반복 등 한 벌. 예: 이미지를 둘 쓰면 `background-size` 도 쉼표로 둘 적는다.
- **칠 영역(painting area)** — 배경이 실제로 칠해지는 범위. 예: `clip: content-box` 로 하면 실측에서 x 30..229 만 칠해졌다.
- **위치 영역(positioning area)** — 배경 이미지의 `0 0` 이 어디인가. 예: `origin: content-box` 로 하면 타일이 x 34 에서 시작했다.
- **단축 속성(shorthand)** — 여러 롱핸드를 한 줄로 적는 속성. 예: `background` 는 아홉을 푼다. **안 적은 것은 `initial` 로 리셋된다.**
- **롱핸드(longhand)** — 단축이 푸는 개별 속성. 예: `background-origin`·`background-clip`.
- **타일링(tiling)** — 이미지를 반복해 면을 채우는 것. 예: `background-repeat: repeat`.
- **자연 크기(intrinsic size)** — 이미지가 원래 갖고 있는 픽셀 크기. 예: 실측 이미지의 `naturalWidth x naturalHeight` 는 16 x 8 이었다.
- **사용값(used value)** — 레이아웃이 끝나야 정해지는 실제 픽셀 값. 예: `round` 로 줄어든 타일 크기가 여기 있고 계산값에는 없다.
- **Baseline** — 주요 브라우저에 그 기능이 언제부터 다 들어갔는지를 나타내는 지표. 예: `object-fit` 은 `widely`, `background-clip: text` 는 `limited` 다.

## 더 들어가면

- **`background-repeat` 은 두 축을 따로 받는다.** `background-repeat: round space` 처럼 가로·세로에 다른 값을 줄 수 있다.
- **`background-position-x`/`-y` 는 따로 있는 롱핸드**다(실측 — 단축이 그 둘로 분해됐다). 한 축만 바꾸고 싶을 때 쓴다.
- **`background-blend-mode` 는 레이어끼리 섞는다** — [목록의 **48번 주제**](../48-blend-modes-and-isolation/)가 정본이다. 「누가 위인가」(여기)와 「어떻게 섞이나」(그쪽)가 갈린다.
- **`object-fit` 은 `<iframe>`·`<embed>` 에도 정의돼 있다.** 흔히 `<img>`·`<video>` 로만 배우지만 대체 요소 전반의 규칙이다.
- **`image-rendering: pixelated`** 는 작은 이미지를 크게 늘일 때 흐릿해지지 않게 한다 — 이 문서의 demo 가 16×8 이미지를 120px 로 키우면서 쓴 것이 그것이다.

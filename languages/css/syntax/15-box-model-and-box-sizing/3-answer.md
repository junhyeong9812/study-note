# css/syntax/15 — 박스 모델과 `box-sizing` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 치수는 Google Chrome 151.0.7922.173 headless 에서 실제로 렌더해 `getBoundingClientRect()`·`clientWidth` 로 잰 값**이다. 단위는 px 다.\
> **손으로 계산해 유도한 수치는 없다.** 규칙은 [CSS Box Model Level 3](https://drafts.csswg.org/css-box-3/) 과 [CSS Box Sizing Level 3](https://drafts.csswg.org/css-sizing-3/) 으로 접지했다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 이 상자는 화면에서 몇 px 을 차지하는가

**실행 결과** (Chrome 151 headless — 폭 500px 부모 안)

```text
.a (content-box)  rect.width = 350   clientWidth = 340   getComputedStyle().width = 300px   rect.height = 70
.b (border-box)   rect.width = 300   clientWidth = 290   getComputedStyle().width = 300px   rect.height = 70
```

**`.a` 의 `rect.width`**

- **350** 이다. `width: 300px` 이 **content 칸**만 가리키고, 패딩 20 과 테두리 5 가 좌우로 각각 더 붙는다.

**`.b` 의 `rect.width`**

- **300** 이다. `border-box` 에서는 `width` 가 **테두리 바깥까지**를 가리키므로 선언한 숫자가 곧 실제 폭이다.

**`.b` 의 content 폭**

- **250** 이다. 300 안에 패딩 40 과 테두리 10 이 들어가고 남은 칸이 글자 자리다.
- 재는 법: 자식에게 `width: 100%` 를 주고 그 자식의 `rect.width` 를 읽는다. **실측값이 250 이었다.**

**두 상자의 높이**

- **같다 — 둘 다 70.** `height` 를 선언하지 않았으므로 두 모드 모두 "내용 높이 + 패딩 + 테두리"로 똑같이 계산된다.
- `box-sizing` 은 **선언한 숫자가 있을 때만** 개입한다(4번을 보라).

> **테두리 상자(border box)** — 테두리 바깥선까지의 칸. `getBoundingClientRect()` 가 재는 칸이다.\
> 예: `width:300px; padding:20px; border:5px` 인 `content-box` 상자의 테두리 상자 폭은 350 이다.

### 2. 네 겹 중 어디까지 배경이 칠해지나

**배경이 칠해지는 칸**

- **`border` 상자까지**다. content · padding · border 세 겹에는 배경이 깔리고 **`margin` 칸에는 안 깔린다.**
- 그래서 마진 칸은 뒤에 있는 것(부모의 배경)이 그대로 비친다.

```text
  [ margin  ][ border ][ padding ][ content ][ padding ][ border ][ margin  ]
   배경 없음  <--------------- 배경이 칠해지는 범위 --------------->  배경 없음
```

**`getBoundingClientRect().width` 가 재는 칸**

- **border 상자.** 마진은 들어 있지 않다.

**`clientWidth` 가 재는 칸**

- **padding 상자**(스크롤바는 뺀다). 실측에서 `width:300px; padding:20px; border:5px` 인 `content-box` 상자가 `rect.width` 350 · `clientWidth` 340 이었다 — 차이 10 이 좌우 테두리다.

**벌어져 보이는데 배경이 안 칠해진 빈 자리**

- **마진**이다. (색이 있는 상자 둘 사이의 빈틈은 언제나 마진이다 — 패딩이면 색이 칠해져 있다.)
- 그 빈틈이 두 마진의 합이 아니라 **큰 쪽 하나**인 이유는 [18번](../18-margin-collapsing/2-summary.md)의 마진 상쇄다.

### 3. `border-box` 인데 부모를 뚫고 나간다

**실행 결과** (Chrome 151 headless — `.parent` 의 content 칸은 x=2\~302)

```text
마진 없는 형제   rect.x = 2    rect.width = 300   오른쪽 끝 302   (부모 안에 딱 맞음)
.child           rect.x = 22   rect.width = 300   오른쪽 끝 322   (부모 밖 20)
```

**`.child` 의 `rect.width`**

- **300.** 마진을 줬다고 상자가 줄어들지 않는다.

**부모 오른쪽 끝보다 몇 px 밖에 있나**

- **20px.** 왼쪽 마진 20 만큼 통째로 오른쪽으로 밀렸고 폭은 그대로다.

**`border-box` 가 막아 주지 못하는 이유**

- `box-sizing` 이 끌어안는 범위는 **padding 과 border 까지**다. **`margin` 은 그 바깥이라 정의상 포함되지 않는다.**
- `margin-box` 라는 값은 CSS 에 **없다.**

**고치는 법 두 가지**

- `width: 100%` 를 **지운다**(= `auto`). 그러면 남는 자리 계산에 마진이 먼저 빠지므로 저절로 맞는다.
- `width: calc(100% - 40px)` 로 마진 합을 직접 뺀다.
- (세 번째 길) 자식에 마진을 주지 말고 **부모에 패딩**을 준다. 실무에서는 이쪽이 가장 안전하다.

### 4. `box-sizing` 을 바꿨는데 아무 일도 안 일어난다

**실행 결과** (Chrome 151 headless — 부모 `width: 320px`, 자식에 `width` 선언 없음)

```text
content-box  rect.width = 320   content 폭 270
border-box   rect.width = 320   content 폭 270      ← 한 픽셀도 다르지 않다
```

**두 경우의 `rect.width`**

- **둘 다 320.** 차이가 없다.

**이유**

- `width: auto` 인 블록 상자는 **"부모의 content 폭에서 마진·테두리·패딩을 빼고 남은 것"** 으로 content 폭이 정해진다.
- 이 계산에는 **선언된 숫자가 등장하지 않는다.** `box-sizing` 은 "선언한 숫자를 어느 칸에 배정하나"를 정하는 속성인데, **배정할 숫자가 없다.**

```text
  width: 300px 일 때                     width: auto 일 때
  선언한 300 을 어디에 넣나?             넣을 숫자가 없다
   -> content 에 (content-box)            -> 남는 자리를 채운다
   -> border 까지에 (border-box)          -> box-sizing 이 낄 자리가 없다
```

**리셋이 건드리는 것과 안 건드리는 것**

- **건드린다** — `width`·`height`·`min-*`·`max-*` 를 **숫자나 `%` 로 선언한 상자.**
- **안 건드린다** — 치수를 선언하지 않은 상자. 페이지의 대부분이 여기다.
- 그래서 `* { box-sizing: border-box }` 는 **대부분을 그대로 두고 사고 나는 자리만 고친다.**

### 5. 선언한 `width` 가 무시되는 경우

**실행 결과** (Chrome 151 headless)

```text
box-sizing: border-box; width: 40px; padding: 20px; border: 5px
  rect.width = 50     clientWidth = 40     getComputedStyle().width = 50px
```

**`rect.width`**

- **50.** 선언한 40 이 아니다. 패딩 40 과 테두리 10 만으로 이미 50 이기 때문이다.

**content 폭**

- **0.** content 폭은 음수가 될 수 없어 0 에서 멈춘다.

**선언한 40px 은 어디로 갔나**

- **아무 데도 남지 않는다.** `getComputedStyle().width` 조차 `50px` 을 돌려준다.
- **에러도 경고도 없다.** CSS 는 값이 문법적으로 유효하면 받아들이고, 계산 결과가 하한에 걸리면 **조용히 하한을 쓴다.**
- 증상은 "칸이 더 안 줄어든다"로 나타난다. 원인을 찾으려면 **패딩·테두리 합을 먼저 세어 봐야** 한다.

### 6. `min-width` 는 어느 칸을 재는가

**실행 결과** (Chrome 151 headless — `width:100px; min-width:200px; padding:20px; border:5px`)

```text
content-box   rect.width = 250      (min-width 200 이 content 칸에 걸렸다)
border-box    rect.width = 200      (min-width 200 이 border 칸에 걸렸다)

같은 선언을 max-width: 200px 으로 눌러 봐도
content-box   rect.width = 250
border-box    rect.width = 200
```

**`content-box` 일 때**

- **250.** `min-width` 가 **content 폭**을 200 으로 끌어올리고, 거기에 패딩 40 과 테두리 10 이 더 붙는다.

**`border-box` 일 때**

- **200.** `min-width` 가 **테두리 상자 폭**을 200 으로 끌어올린다. 패딩과 테두리는 그 안에 들어간다.

**중간에 리셋을 새로 넣으면**

- `min-width`·`max-width` 가 **가리키는 칸이 통째로 바뀐다.** 실측대로라면 같은 `max-width: 200px` 이 250 을 뜻하다가 200 을 뜻하게 된다.
- **레이아웃이 조용히 좁아진다** — 선언은 한 글자도 안 바뀌었는데 결과가 달라지므로 원인 추적이 어렵다.
- 그래서 `border-box` 리셋은 **프로젝트 시작에 깔아야** 한다.

### 7. 계산값 API 를 믿어도 되는가

**실행 결과** (Chrome 151 headless — `box-sizing: border-box; width:300px; padding:20px; border:5px`)

```text
실제 content 폭             250   (자식에게 width:100% 를 줘서 잰 값)
getBoundingClientRect().w   300   (border 폭)
clientWidth                 290   (padding 폭)
getComputedStyle().width    300px ← content 폭이 아니다
```

**`getComputedStyle(el).width` 가 돌려주는 것**

- **`300px`.** 즉 **그 요소 자신의 `box-sizing` 기준 값**이다.
- 같은 선언을 `content-box` 로 바꾸면 이 값도 `300px` 인데, 그때는 **content 폭**을 뜻한다.\
  **두 요소의 `width` 문자열이 똑같은데 가리키는 칸이 다르다.**

**실제 content 폭과 같은가**

- **아니다.** 실제 content 폭은 250 이고 API 는 300 을 돌려줬다.
- 이것은 **이 브라우저에서 관찰한 결과**다. 계산값 API 의 정본은 CSSOM 명세이고 이 목록은 선언적 CSS 만 다루므로(README 의 「뺀 것」), **"CSS 가 그렇게 보장한다"로 읽으면 안 된다.**

**안전하게 읽는 법**

- `getBoundingClientRect().width`(**border 폭**)와 `clientWidth`(**padding 폭**)를 **함께** 읽는다.
- 이 둘은 **무엇을 재는지가 이름과 정의로 고정**돼 있어 `box-sizing` 에 따라 뜻이 바뀌지 않는다.
- content 폭이 꼭 필요하면 **자식에게 `width: 100%` 를 주고 그 자식을 재는** 것이 가장 확실하다(이 문서의 250 이 그렇게 잰 값이다).

### 8. `%` 와 다른 주제로 잇기

**실행 결과** (Chrome 151 headless)

```text
부모 width:400px, 높이 auto      .a { padding-top: 10% }  ->  rect.height = 40
부모 width:400px, height:200px   .a { padding-top: 10% }  ->  rect.height = 40   (같다)
부모 width:400px                 .b { margin-top: 10% }   ->  계산값 margin-top = 40px

inline 요소에 border: 10px   rect.width = 28.52 · 다음 형제의 x = 그만큼 밀림
inline 요소에 outline: 10px  rect.width = 9.2   · 다음 형제의 x = 전혀 안 밀림
```

**`padding-top: 10%` 는 무엇의 10% 인가**

- **부모의 content 폭**이다. 부모 높이를 200px 로 줘도 결과가 40 으로 **똑같았다** — 높이를 보지 않는다는 뜻이다.
- `margin-top: 10%` 도 같다(실측 계산값 40px).
- **세로 방향인데 가로를 기준으로 삼는다**는 것이 이 자리에서 가장 자주 틀리는 대목이다.

**정사각형 관용구의 오늘**

- `aspect-ratio` 로 대체된다. 정본은 [목록의 **31번 주제**](../31-intrinsic-sizing-and-aspect-ratio/)(내재적 크기·`aspect-ratio`).
- `padding-top: 100%` 관용구가 쓰였던 이유가 바로 위 규칙이다 — **폭 기준이라 폭에 비례하는 높이를 만들 수 있었다.**

**`outline` 은 네 겹 중 어디인가**

- **어디에도 속하지 않는다.** 실측에서 `outline: 10px` 을 준 요소의 `rect.width` 가 9.2 로 **테두리 없는 요소와 같았고**, 바로 뒤 요소의 x 좌표도 밀리지 않았다.
- 같은 자리에 `border: 10px` 을 주면 `rect.width` 가 28.52 로 커지고 뒤 요소가 밀린다.
- 그래서 포커스 링을 `border` 로 만들면 **포커스될 때마다 레이아웃이 흔들린다.** 정본은 [목록의 **46번 주제**](../46-borders-radius-outline-shadow/).

**상자가 바깥에서 어떻게 보이고 안을 어떻게 배치하는지**

- [16번 주제](../16-display-inner-outer/2-summary.md)(`display` 의 내부/외부 값)다.
- 이 문서는 **치수가 정해지는 규칙**까지이고, 그 상자가 어떤 흐름 안에 놓이는지는 16번, 그 안의 일이 밖으로 새는지는 [17번](../17-block-formatting-context/2-summary.md)이다.

## 용어 풀이

- **콘텐츠 상자(content box)** — 글자·이미지가 놓이는 가장 안쪽 칸. 직접 재려면 자식에게 `width: 100%` 를 준다.
- **패딩 상자(padding box)** — content + padding. `clientWidth` 가 재는 칸.
- **테두리 상자(border box)** — padding 상자 + border. `getBoundingClientRect()` 가 재는 칸.
- **마진 상자(margin box)** — border 상자 + margin. **배경이 칠해지지 않아** 눈에 안 보인다.
- **`box-sizing`** — 선언한 `width`/`height` 숫자를 content 칸에 배정할지 border 칸에 배정할지 정한다. 값은 `content-box`(기본)와 `border-box` 둘뿐이고 상속되지 않는다.
- **`width: auto`** — 폭 미선언 상태. 블록 상자에서는 "남는 자리를 다 쓴다"로 해결되며 `box-sizing` 이 개입하지 않는다.
- **하한(floor)** — content 폭이 0 아래로 못 내려가는 것. `border-box` 에서 `width` 선언이 무시되는 원인이다.
- **`outline`** — 상자 위에 그려지지만 **레이아웃 공간을 차지하지 않는** 선. 네 겹 어디에도 속하지 않는다.
- **사용값(used value)** — 레이아웃이 실제로 쓴 픽셀 값. 선언값과 다를 수 있다. 정본은 [목록의 **04번 주제**](../04-value-processing-stages/).

## 실행 검증

| 무엇을 | 어떻게 | 결과 |
|---|---|---|
| 두 모드의 실제 폭 | Chrome 151.0.7922.173 headless · `--dump-dom` + `getBoundingClientRect()` | `content-box` 350 / `border-box` 300 |
| content 폭 | `border-box` 부모 안에 `width:100%` 자식을 넣어 측정 | 250 |
| `margin` 이 `box-sizing` 밖 | `width:100%` + `margin: 8px 20px` 의 x 좌표·폭 | x 22, 폭 300 — 부모 밖 20 |
| `width: auto` 무의미 | 같은 부모 안에서 두 모드 비교 | 둘 다 320 (동일) |
| `border-box` 하한 | `width: 40px` + 패딩 20 + 테두리 5 | rect 50 · content 0 |
| `min-width`/`max-width` 의 칸 | 두 모드 대조 | 250 / 200 (둘 다) |
| 계산값 API | `getComputedStyle().width` 대 실제 content 폭 | 300px 대 250 — **다르다** |
| `%` 패딩의 기준 | 부모 높이를 바꿔 가며 `padding-top: 10%` 측정 | 높이와 무관하게 40 (폭 기준) |
| `outline` 의 공간 | inline 요소에 `border` / `outline` 각각 10px | 28.52 대 9.2 — outline 은 0 |
| demo 3개 | 각 블록을 `<!doctype>`·`<body>` 래퍼에 넣어 렌더 + 스크린샷 | 「보이는 것」 3건 모두 화면과 일치 |

**구현 의존 항목** — `getComputedStyle().width` 가 `box-sizing` 을 따라 달라지는 것은 **Chrome 151 에서 관찰한 것**이다. 브라우저가 바뀌면 이 칸을 다시 찍어야 한다.\
**엔진은 Chrome 하나다.** Firefox 155.0.1 은 이 환경에서 headless 스크린샷이 산출되지 않고 WebKit 은 이 머신에 없다 — **「두 엔진에서 확인했다」고 적지 않았다.**

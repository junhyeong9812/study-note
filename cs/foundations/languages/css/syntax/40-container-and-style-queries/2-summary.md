# css/syntax/40 — 컨테이너 쿼리와 스타일 쿼리 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [CSS Containment Module Level 3](https://drafts.csswg.org/css-contain-3/) 의 「Container Queries」·「`container-type`」·「Style Queries」 절. 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 값은 **Google Chrome 151.0.7922.173** headless 에 실제로 띄워 `getComputedStyle`·`cssRules` 로 읽은 것이다. **컨테이너 쿼리가 뷰포트와 무관하다는 것은 `--window-size` 를 500·780·1400 으로 바꿔 같은 문서를 세 번 띄워** 확인했다. 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> **엔진은 Chrome 하나다** — Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고 WebKit 은 없다. 「두 엔진에서 확인했다」고 적지 않는다.
> **버전** — CSS 에 언어 버전은 없다. 크기 컨테이너 쿼리는 Baseline **widely**(newly 2023-02-14 → widely 2025-08-14) · **스타일 쿼리는 newly**(2026-05-19, 아직 widely 아님) — `api.webstatus.dev` 조회 결과.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**컨테이너 쿼리는 「창밖」이 아니라 「내가 놓인 방」을 재는 자다.**

가구 배치에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 창밖 날씨를 본다 | 미디어 쿼리 — **뷰포트**([38번](../38-media-queries/2-summary.md)) |
| 이 가구가 놓인 **방의 크기**를 본다 | 컨테이너 쿼리 — **가장 가까운 조상 컨테이너** |
| 「이 방은 재도 됩니다」라는 허락 | `container-type: inline-size` — **선언해야 조회 대상이 된다** |
| 방에 이름표를 단다 | `container-name: sidebar` |
| 방을 재려면 방 크기가 **내용과 무관해야** 한다 | `size` 컨테인먼트 — 그 축의 크기가 억제된다 |
| 내가 나 자신의 방일 수는 없다 | **자기 자신은 조회할 수 없다.** 조상만 |
| 방에 붙은 메모를 읽는다 | 스타일 쿼리 — `@container style(--theme: dark)` |

- **같은 카드를 좁은 자리에 두면 좁게, 넓은 자리에 두면 넓게** 그리는 것이 목적이다.\
  미디어 쿼리로는 **같은 페이지 안에서 답을 갈라 줄 수 없다** — 뷰포트는 페이지에 하나뿐이기 때문이다.

```text
   실측 — 같은 뷰포트(500 / 780 / 1400px 세 번), 같은 .card 규칙

   +-- .box (width: 320px, container-type: inline-size) --+
   |   .card   배경 (226,232,240)   글자 14px              |   <- @container (min-width: 500px) 거짓
   +-------------------------------------------------------+

   +-- .box (width: 640px, container-type: inline-size) ----------------+
   |   .card   배경 (191,219,254)   글자 20px                           |   <- 참
   +---------------------------------------------------------------------+

   세 뷰포트에서 값이 한 글자도 안 바뀌었다. 뷰포트를 아예 안 본다는 증거다
```

실무에서 이게 터지는 자리는 **`container-type` 을 안 쓰고 `@container` 만 쓸 때**다.\
문법도 맞고 규칙도 `cssRules` 에 담겨 있는데 **아무 일도 안 일어난다.** 에러도 경고도 없다.

> **질의 컨테이너(query container)** — `container-type` 이 `normal` 이 아닌 요소. `@container` 가 잴 수 있는 대상.\
> 예: `container-type: inline-size` 를 선언한 `<div>`.

> **컨테인먼트(containment)** — 요소 안팎의 영향을 끊어 브라우저가 바깥을 다시 계산하지 않게 하는 것.\
> 예: `size` 컨테인먼트가 걸리면 **안의 내용이 바깥 크기에 기여하지 않는다.**

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **무엇이 조회 대상이 되는가.** 왜 `container-type` 을 선언해야 하고, 왜 자기 자신은 못 재는가.
2. **`size` 는 무엇을 대가로 요구하는가.** `inline-size` 와 무엇이 다른가.
3. **스타일 쿼리는 크기 쿼리와 같은 규칙을 따르는가.**

## 동작 방식

### (1) ★★ `container-type` 을 선언해야 조회 대상이 된다 — 첫 관문

**언제 쓰나** — `@container` 를 처음 쓸 때. **여기서 막히면 아무것도 안 보인다.**

```text
실측 — 같은 @container (min-width: 300px) 규칙, 부모 폭은 전부 400px

  부모의 선언                                   자손의 색
  ------------------------------------------    -------------------
  (아무것도 없음)                                rgb(0, 0, 0)      안 먹음
  container-type: inline-size                    rgb(21, 128, 61)  먹음
  container-type: size (+ height 지정)           rgb(21, 128, 61)  먹음
  container-name: box1  (container-type 없음)    rgb(0, 0, 0)      ★ 안 먹음
  container-type: inline-size + display: inline  rgb(0, 0, 0)      ★ 안 먹음
  container-type: inline-size + display: contents rgb(0, 0, 0)     ★ 안 먹음
  container-type: inline-size + display: table    rgb(0, 0, 0)     ★ 안 먹음
  container-type: inline-size + display: inline-block  rgb(21,128,61) 먹음

  그때 부모의 container-type 계산값
    선언 없음         -> "normal"
    container-name 만 -> "normal"      이름만으로는 컨테이너가 안 된다
```

```text
   규칙은 담겨 있다 — 조건을 평가할 컨테이너가 없을 뿐이다

   실측  CSSContainerRule 이 cssRules 에 전부 담겨 있다
         [" | (min-width: 300px)", "side | (min-width: 300px)", …]
         ^ containerName 이 빈 문자열이면 "이름 없는 컨테이너 아무거나"

   38번과 같은 모양이다 — "안 담겼다" 가 아니라 "담겼는데 조건이 거짓"
```

그림 해설 (한 단계씩):

- **기본값은 `normal`** 이고, 그것은 「**크기 조회 대상이 아님**」이다.
- **`container-name` 만으로는 컨테이너가 안 된다**(실측: 계산값이 `normal`). 이름은 **여러 컨테이너 중 고르는 수단**일 뿐이다.
- **박스를 안 만들거나 크기 컨테인먼트가 안 걸리는 `display` 값에서는 컨테이너가 안 된다.**
  실측에서 `inline`·`contents`·`table` 이 전부 실패했고 `inline-block` 은 됐다.
  ★ **그때도 `container-type` 계산값은 `inline-size` 그대로**였다 — **계산값만 읽어서는 실패를 못 본다.**
- 단축 `container: 이름 / 타입` 도 있다. 실측에서 `container: mybox / inline-size` 가 `container-name: mybox`·`container-type: inline-size` 로 풀렸다.

비용 — 선언 한 줄. **다만 그 선언이 컨테인먼트를 켠다**(아래 (3)).

### (2) ★ 자기 자신은 조회할 수 없다 — 조상만

**언제 쓰나** — 「컨테이너에 걸었는데 그 요소 자신은 안 바뀐다」를 만났을 때.

```text
실측
  .self { container-type: inline-size; width: 400px; color: #000 }
  @container (min-width: 300px) { .self { color: #b91c1c } }

    .self          = rgb(0, 0, 0)        ★ 자기 자신은 안 먹는다
    .self 의 자손  = rgb(21, 128, 61)    자손은 먹는다
```

```text
   왜 금지인가 — 순환이 생긴다

   .self 가 자기 크기로 자기 스타일을 바꾼다
      -> 스타일이 바뀌면 크기가 바뀐다
         -> 크기가 바뀌면 조건이 뒤집힌다
            -> 스타일이 다시 바뀐다  ...  무한 루프

   그래서 규칙은 "가장 가까운 '조상' 컨테이너" 로 고정돼 있다
```

```text
   실무의 우회 — 상자를 하나 더 둔다

   나쁜 배치                          좋은 배치
   <div class="card">                 <div class="card-wrap">   <- container-type 은 여기
     container-type: inline-size        <div class="card">      <- @container 로 바꾸는 것은 여기
     @container 로 나를 바꾸려 함       </div>
   </div>                             </div>
```

그림 해설 (한 단계씩):

- 컨테이너는 **자손에게만 보인다.** 자기 자신·형제·조상에게는 안 보인다.
- 그래서 컴포넌트를 컨테이너 쿼리로 만들려면 **래퍼를 하나 더** 둔다. 실무에서 가장 흔한 배치다.
- 중첩된 컨테이너가 여럿이면 **가장 가까운 조상**이 답한다.

```text
실측 — 바깥 900px, 안쪽 400px, 둘 다 container-type: inline-size

  @container (min-width: 300px) { .c6 { color: #15803d } }   -> 먹음   (400 >= 300)
  @container (min-width: 800px) { .c6 { background: … } }    -> 안 먹음
       .c6 background = rgba(0, 0, 0, 0)
       ^ 바깥이 900px 인데도 거짓이다. 가장 가까운 컨테이너(400px)만 본다
```

비용 — 래퍼 하나. 마크업이 한 겹 는다.

### (3) ★ `size` 는 그 축의 크기를 억제한다 — 대가가 있다

**언제 쓰나** — `height` 로도 조회하고 싶을 때. **가장 큰 대가가 붙는 자리다.**

```text
실측 — 안에 36px 짜리 자손이 하나 있는 400px 짜리 상자

  선언                              height    clientHeight   scrollHeight
  ------------------------------    -------   ------------   ------------
  (없음)                             36px      36             36
  container-type: inline-size        36px      36             36
  container-type: size               0px       0              36     ★
                                     ^^^^^^^^^^^^^^^^^^        ^^^^^^^^
                                     상자가 납작해졌다          내용은 그대로 있다
```

```text
   size 컨테인먼트가 하는 일

   그냥 상자                          container-type: size
   +---------------------+            +---------------------+  <- 높이 0
   |  내용 36px          |            |                     |
   |  -> 부모 높이 36px  |            +---------------------+
   +---------------------+              내용 36px 은 밖으로 넘친다
     내용이 크기를 정한다               "내용은 크기에 기여하지 않는다"
```

```text
   왜 억제가 필요한가 — 역시 순환이다

   높이를 조회한다  ->  자손 스타일이 바뀐다  ->  자손 높이가 바뀐다
                                                    -> 부모 높이가 바뀐다
                                                       -> 조회 결과가 뒤집힌다

   그래서 "높이를 재려면 높이가 내용과 무관해야 한다" 는 조건이 붙는다.
   inline-size 는 인라인 축(가로 쓰기에서 폭)만 재므로 이 문제가 없다
     — 폭은 원래 바깥이 정해 주는 축이기 때문이다
```

그림 해설 (한 단계씩):

- **`size` 를 쓰면 높이를 직접 정해야 한다.** 실측에서 `height: 100px` 을 준 쪽만 `(min-height: 10px)` 조회가 참이 됐고, 안 준 쪽은 높이가 0 이라 거짓이었다.
- **`inline-size` 가 기본 선택지**인 이유가 이것이다. 실무의 99% 는 폭만 재면 된다.
- ★ 실측에서 **`contain` 속성의 계산값은 `none` 이었다** — `container-type` 이 거는 컨테인먼트는 `contain` 에 안 비친다. `contain` 만 읽어서는 진단이 안 된다.

비용 — **`size` 는 레이아웃을 바꾼다.** 선언 한 줄이 상자를 납작하게 만든다. 이것이 이 주제에서 가장 비싼 대가다.

### (4) 이름과 조건 문법

**언제 쓰나** — 컨테이너가 여럿 겹칠 때.

```text
  container-type: inline-size            인라인 축만 잰다 (가로 쓰기에서 폭)
  container-type: size                   두 축 다 잰다 + 크기 억제
  container-type: normal                 기본. 크기 조회 대상이 아니다 (스타일 쿼리는 된다)
  container-name: side                   이름표
  container: side / inline-size          단축

  @container (min-width: 300px) { … }            이름 없음 -> 가장 가까운 컨테이너
  @container side (min-width: 300px) { … }       이름이 side 인 가장 가까운 조상
  @container (400px <= width <= 700px) { … }     범위 구문도 그대로 쓴다
  @container (min-width: 300px) and style(--t: d) { … }   섞어 쓸 수 있다

  실측 — 이름이 다른 규칙이 같은 컨테이너에 안 걸린다
    .n { container-type: inline-size; container-name: side; width: 400px }
    @container side (min-width: 300px) { … }  -> 먹음
```

그림 해설 (한 단계씩):

- **이름이 없으면 가장 가까운 컨테이너**를 본다. 이름을 주면 **그 이름을 가진 가장 가까운 조상**을 찾는다.
- 조건 문법은 **미디어 쿼리와 같다** — 범위 구문·`and`·`or`·`not` 이 그대로 쓰인다([38번 주제](../38-media-queries/2-summary.md)).
- 단, 쓸 수 있는 기능이 **크기 계열로 한정**된다(`width`·`height`·`inline-size`·`block-size`·`aspect-ratio`·`orientation`).

비용 — 없음.

### (5) 스타일 쿼리 — 규칙이 하나 다르다

**언제 쓰나** — 조상이 정한 테마·상태를 자손이 읽어야 할 때.

```text
실측 — @container style(--theme: dark) { .s { color: 초록 } }

  조상의 선언                                       자손의 색
  ----------------------------------------------    -------------------
  container-type: inline-size; --theme: dark         rgb(21, 128, 61)  먹음
  container-type: inline-size; --theme: light        rgb(0, 0, 0)      안 먹음
  ★ container-type 없음 ;  --theme: dark             rgb(21, 128, 61)  ★ 먹는다
  --theme: DARK  (대문자)                            rgb(0, 0, 0)      ★ 안 먹음
  등록한 <angle> 속성  --ang: 45deg                  rgb(29, 78, 216)  먹음
  style(--theme)  존재만 묻기, 조상이 정함           rgb(29, 78, 216)  먹음
  style(--theme)  존재만 묻기, 아무도 안 정함        rgb(0, 0, 0)      안 먹음
  style(color: red)  보통 속성                       ★ 조건이 거짓이었다
  not style(--theme: dark),  조상이 light            rgb(29, 78, 216)  먹음
  자기 자신에게 style(...) 로 걸기                   rgb(0, 0, 0)      ★ 안 먹음
```

```text
   크기 쿼리와 스타일 쿼리의 차이는 딱 하나

   +-----------------------------+-----------------------------+
   |        크기 쿼리             |        스타일 쿼리           |
   +-----------------------------+-----------------------------+
   | container-type 필요          | ★ 필요 없다                  |
   | 컨테인먼트가 켜진다          | 아무것도 안 켜진다           |
   | 자기 자신 조회 불가          | 자기 자신 조회 불가 (같다)   |
   | 가장 가까운 조상             | 가장 가까운 조상 (같다)      |
   +-----------------------------+-----------------------------+

   이유 — 스타일 값을 읽는 것은 레이아웃을 안 건드리므로 순환이 안 생긴다.
          그래서 모든 요소가 기본으로 "스타일 컨테이너" 다
```

그림 해설 (한 단계씩):

- ★ **`container-type` 없이 동작한다**(실측). 크기 쿼리의 첫 관문이 여기엔 없다.
- **값 비교는 토큰 단위이고 대소문자를 가린다** — `--theme: DARK` 는 `style(--theme: dark)` 에 안 걸렸다.
- **Chrome 151 에서 보통 속성은 안 된다.** `style(color: red)` 는 `cssRules` 에 담겼지만(`containerQuery = "style(color: red)"`) 조건이 거짓이었다.\
  ★ 명세는 보통 속성도 허용하지만 **구현이 커스텀 속성만 지원**한다 — 「명세가 허용하는데 구현이 안 하는」 자리다.
- **Baseline newly**(2026-05-19) 다. 되는 범위는 **커스텀 속성 조회까지**로 보고 쓴다.

비용 — 없음(컨테인먼트가 안 켜진다). 대신 지원 범위가 좁다.

### (6) 컨테이너 쿼리 단위는 여기가 아니다

**언제 쓰나** — `cqw`·`cqi` 를 쓰고 싶을 때.

```text
  cqw / cqh / cqi / cqb / cqmin / cqmax
     컨테이너의 크기를 기준으로 하는 길이 단위

  ★ 정본은 [목록의 **34번 주제**](../34-viewport-and-container-units/)(길이 단위와 상대 단위)다.
    여기서 쓸 결론은 하나뿐 —
    "이 단위도 container-type 이 선언된 조상이 있어야 기준이 생긴다"
```

- 단위 이야기는 [목록의 **34번 주제**](../34-viewport-and-container-units/)로 넘긴다. **여기는 조회 규칙만** 다룬다.

비용 — 없음.

## 문법 — 형태와 규칙

CSS 는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태

```css
.card-wrap { container-type: inline-size; container-name: card; }
@container card (min-width: 500px) { .card { display: grid; grid-template-columns: 1fr 2fr } }

.theme { --theme: dark; }
@container style(--theme: dark) { .badge { background: #111 } }
```

```js
[...document.styleSheets[0].cssRules]
  .filter(r => r.constructor.name === "CSSContainerRule")
  .map(r => [r.containerName, r.containerQuery])
getComputedStyle(el).containerType     // "normal" 이면 크기 조회 대상이 아니다
```

### 금지 사례 — 던져서 확인한 것

```css
.box { container-name: side; }                  /* 타입이 없으면 컨테이너가 아니다 (실측: normal) */
.box { container-type: inline-size; display: inline; }  /* 인라인 박스는 컨테이너가 못 된다 */
.self { container-type: inline-size; }
@container (min-width: 300px) { .self { … } }   /* 자기 자신은 조회 불가 */
.box { container-type: size; }                  /* height 를 안 주면 높이가 0 이 된다 */
@container style(color: red) { … }              /* Chrome 151 에서 조건이 항상 거짓 */
```

### 어디서 헷갈리나

- **`container-type` 이 관문이다.** 이름·단위·조건이 아무리 맞아도 이것이 없으면 아무 일도 안 일어난다.
- **자기 자신은 못 잰다.** 래퍼를 하나 더 둔다.
- **`size` 는 레이아웃을 바꾼다.** 특히 높이가 0 이 된다.
- **스타일 쿼리는 관문이 없다.** 크기 쿼리와 규칙이 다르다.
- **`contain` 계산값으로는 진단이 안 된다**(실측: `none`). `containerType` 을 읽는다.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 여섯 다 **에러 없이 조용히 어긋난다.**

### 1. `container-type` 없이 `@container` 만 쓴다

실측에서 `.c1` 이 검정 그대로였다. 규칙은 `cssRules` 에 **멀쩡히 담겨 있다.**\
증상은 「아무 일도 안 일어남」 하나뿐이라 조건 숫자를 계속 고치게 된다.\
**`getComputedStyle(부모).containerType` 이 `normal` 이면 그게 원인이다.**\
★ 다만 `inline-size` 라고 나와도 안심하면 안 된다 — `display` 가 `contents`·`table`·`inline` 이면
계산값은 `inline-size` 인데 **컨테이너가 아니다**(실측). 그때는 `display` 를 같이 읽는다.

### 2. `container-name` 만 주고 컨테이너가 됐다고 믿는다

실측에서 `container-name: box1` 만 준 요소의 `containerType` 이 **`normal`** 이었고, 자손 규칙이 안 걸렸다.\
이름은 **여럿 중에 고르는 수단**이지 자격이 아니다.

### 3. 컨테이너 자신에게 규칙을 건다

실측에서 `.self` 가 검정, 그 자손은 초록이었다. **한 글자 차이로 결과가 갈린다.**\
순환을 막으려고 명세가 금지한 것이라 **우회가 없다** — 래퍼를 둬야 한다.

### 4. 중첩 컨테이너에서 바깥 크기를 기대한다

실측에서 바깥이 900px 인데 `@container (min-width: 800px)` 가 **거짓**이었다.\
가장 가까운 컨테이너가 400px 이기 때문이다. **이름을 붙여 명시적으로 고르지 않으면 언제나 가장 가까운 것**이다.

### 5. `size` 를 썼다가 상자가 납작해진 것을 다른 원인으로 찾는다

실측에서 `container-type: size` 를 준 상자의 `height` 가 **`0px`** 였다(`scrollHeight` 는 36 이었다).\
「갑자기 레이아웃이 무너졌다」의 원인이 조회용으로 넣은 한 줄인데, **`contain` 계산값에도 안 비쳐서** 찾기 어렵다.

### 6. 스타일 쿼리가 크기 쿼리와 같은 규칙일 거라 가정한다

**관문이 없다.** 실측에서 `container-type` 없는 조상에 대해서도 `style(--theme: dark)` 가 **참**이 됐다.\
반대로 **보통 속성은 안 된다** — `style(color: red)` 는 담겼지만 거짓이었다. 둘 다 예상과 반대 방향이다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `container-type` 이 `normal` 이면 크기 조회 대상이 아닌 것 | **명세**(css-contain-3 「`container-type`」) |
| `container-name` 만으로는 컨테이너가 안 되는 것 | **명세**(같은 절) |
| 자기 자신을 조회할 수 없는 것 | **명세**(「Container Queries」 — 조상만) |
| 가장 가까운 조상 컨테이너가 답하는 것 | **명세**(같은 절) |
| `size` 가 크기 컨테인먼트를 거는 것 | **명세**(「Types of Containment」) |
| 인라인 박스가 컨테이너가 못 되는 것 | **명세**(컨테인먼트가 적용되지 않는 박스) |
| 스타일 쿼리에 `container-type` 이 필요 없는 것 | **명세**(「Style Queries」 — 모든 요소가 스타일 컨테이너) |
| **`style(color: red)` 가 거짓인 것** | **관찰**(Chrome 151). **명세는 보통 속성도 허용한다** — 구현 한계다 |
| **`contain` 계산값이 `none` 인 것** | **관찰**(Chrome 151). 직렬화·속성 분리 방식이다 |
| `container: a / b` 단축이 풀리는 형태 | **명세**(단축 정의) + 관찰 |
| Baseline — 크기 쿼리 widely 2025-08-14 · 스타일 쿼리 newly 2026-05-19 | **2차 집계**(`api.webstatus.dev`) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 같은 컴포넌트를 여러 자리에 재사용한다 | `@container` + 래퍼 | `@media`(같은 페이지에서 답을 못 가른다) |
| 페이지 전체 레이아웃 | `@media`([38번](../38-media-queries/2-summary.md)) | `@container` |
| 폭만 보면 된다 | `container-type: inline-size` | `size`(레이아웃을 바꾼다) |
| 높이도 봐야 한다 | `size` **+ 높이를 직접 지정** | `size` 만 |
| 컨테이너가 여럿 겹친다 | `container-name` 으로 명시 | 이름 없이(가장 가까운 것이 잡힌다) |
| 조상의 테마를 자손이 읽는다 | `@container style(--theme: dark)` | 클래스를 자손까지 내려 붙이기 |
| 보통 속성을 조회하고 싶다 | 커스텀 속성으로 옮겨 놓고 조회 | `style(color: red)`(Chrome 151 에서 거짓) |
| 컨테이너 기준 길이 | `cqi`·`cqw`(정본은 [목록의 **34번 주제**](../34-viewport-and-container-units/)) | `vw`(뷰포트 기준이다) |

판단 규칙 두 줄.

- **「이 답이 페이지마다 하나여야 하나, 자리마다 달라야 하나」를 묻는다.** 하나면 `@media`, 자리마다면 `@container`.
- **`size` 는 마지막 수단이다.** 폭으로 풀 수 있으면 `inline-size` 로 끝낸다.

## demo — 같은 뷰포트, 다른 결과

```html demo
<div class="box w320"><div class="card">좁은 컨테이너 안</div></div>
<div class="box w640"><div class="card">넓은 컨테이너 안</div></div>
<style>
  .box  { container-type: inline-size; border: 1px solid #94a3b8; margin-bottom: 8px; }
  .w320 { width: 320px } .w640 { width: 640px }
  .card { padding: 10px; font: 14px system-ui; background: #e2e8f0; }
  @container (min-width: 500px) { .card { background: #bfdbfe; font-size: 20px } }
</style>
```

> **보이는 것** — **완전히 같은 `.card` 규칙인데 위아래가 다르게 그려진다.** 위 카드는 회색 바탕에 작은 글씨(14px), 아래 카드는 파란 바탕에 큰 글씨(20px)다. 갈린 이유는 **감싼 상자의 폭**(320px 대 640px)뿐이다. **창을 아무리 넓히거나 좁혀도 이 둘의 관계는 안 바뀐다** — 뷰포트를 아예 안 보기 때문이다.\
> **바꿔 볼 것** — `.box` 의 `container-type: inline-size` 를 지우면 → **두 카드가 똑같이 회색·14px 이 된다**(조회할 컨테이너가 없어진다) · `.w320` 의 `width` 를 `520px` 로 올리면 → **위 카드도 파란 바탕·20px 이 된다**

*(Chrome 151 headless 실측, `--window-size` 를 500 · 780 · 1400 세 폭에서: **세 번 모두** `.w320 .card` 는 `background-color: rgb(226, 232, 240)` · `font-size: 14px`, `.w640 .card` 는 `rgb(191, 219, 254)` · `20px`.)*

## 핵심 문장

- **컨테이너 쿼리는 가장 가까운 조상 컨테이너를 잰다.** 뷰포트를 안 본다 — 실측에서 세 뷰포트에서 값이 한 글자도 안 바뀌었다.
- **`container-type` 이 첫 관문이다.** `normal` 이면 규칙이 담겨 있어도 아무 일도 안 일어난다. `container-name` 만으로는 안 된다.
- **자기 자신은 조회할 수 없다.** 순환을 막으려는 금지라 우회가 없고, 래퍼를 하나 더 둔다.
- **`size` 는 그 축의 크기를 억제한다.** 실측에서 상자 높이가 `36px` 에서 **`0px`** 이 됐다(`scrollHeight` 는 36 그대로).
- **중첩되면 언제나 가장 가까운 컨테이너**다. 바깥이 900px 여도 안쪽 400px 이 답한다.
- **스타일 쿼리는 관문이 없다.** `container-type` 없이 동작하고, 대신 **Chrome 151 에서 보통 속성은 거짓**이다.
- **`contain` 계산값으로는 진단이 안 된다**(실측: `none`). `containerType` 을 읽는다.

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 40번)
- [`../../../../../../history/web/03-HTML-CSS-진화.md`](../../../../../../history/web/03-HTML-CSS-진화.md) — **컨테이너 쿼리가 왜 「반응형의 다음 단계」인가의 정본.**\
  도입 맥락은 거기, 여기는 **컨테인먼트 요구·자기 조회 금지·스타일 쿼리라는 규칙**만.
- [`../38-media-queries/2-summary.md`](../38-media-queries/2-summary.md) — **조건 문법의 정본.**\
  범위 구문·`and`/`or`/`not`·조건이 거짓인 at-rule 이 `cssRules` 에 남는 것은 거기. 여기는 **무엇을 재는가**만.
- [`../39-color-scheme-and-preferences/2-summary.md`](../39-color-scheme-and-preferences/2-summary.md) — 스타일 쿼리로 **테마를 조상에서 읽는** 쪽의 짝.
- [`../37-at-property/2-summary.md`](../37-at-property/2-summary.md) — 등록한 커스텀 속성도 스타일 쿼리로 조회된다(실측: `style(--ang: 45deg)`).
- [`../07-syntax-and-error-recovery/2-summary.md`](../07-syntax-and-error-recovery/2-summary.md) — 모르는 at-rule 이 블록째 버려지는 것.\
  구형 브라우저에서 `@container` 블록이 통째로 사라지는 근거가 거기다.
- [`../17-block-formatting-context/2-summary.md`](../17-block-formatting-context/2-summary.md) — 서식 문맥이 안팎을 끊는 이야기.\
  컨테인먼트와 **목적은 닮았지만 수단이 다르다** — 거기는 배치 규칙, 여기는 「크기 기여를 끊는 것」.
- [목록의 **34번 주제**](../34-viewport-and-container-units/)(길이 단위) — **`cqw`·`cqi` 단위의 정본.** 여기는 조회 규칙만.
- [`../41-supports-feature-queries/2-summary.md`](../41-supports-feature-queries/2-summary.md) — `CSS.supports('at-rule(@container)')` 로 지원을 묻는 방법(실측: `true`).

## 용어 풀이

- **컨테이너 쿼리(container query)** — 조상 상자의 크기로 조건을 평가하는 `@container` 규칙.
- **질의 컨테이너(query container)** — `container-type` 이 `normal` 이 아닌 요소. 조회의 대상.
- **`container-type`** — `normal`(기본) · `inline-size` · `size`. **선언해야 크기 조회 대상이 된다.**
- **`container-name`** — 컨테이너 이름표. 이것만으로는 컨테이너가 되지 않는다.
- **컨테인먼트(containment)** — 안팎의 영향을 끊는 것. `size` 는 **내용이 크기에 기여하지 않게** 만든다.
- **인라인 축(inline axis)** — 글이 흐르는 방향. 가로 쓰기에서는 폭이다.
- **스타일 쿼리(style query)** — `@container style(…)`. 조상의 **속성값**으로 조건을 평가한다. Baseline **newly**.
- **`CSSContainerRule`** — `@container` 의 CSSOM 타입. `containerName`·`containerQuery` 를 읽을 수 있다.
- **컨테이너 쿼리 단위** — `cqw`·`cqi` 등. 정본은 [목록의 **34번 주제**](../34-viewport-and-container-units/).

## 더 들어가면

- **컨테이너 쿼리가 늦게 나온 이유가 순환 문제**다. 「자식 스타일이 부모 크기를 바꾸고, 그 크기가 다시 자식 스타일을 바꾼다」를 어떻게 끊을 것인가가 십 년 넘게 미뤄진 이유였고, 답이 **컨테인먼트**였다. 「재려면 먼저 끊어라」가 이 기능의 설계 전제다.
- **`display` 값이 자격을 정한다.** 실측에서 `contents`·`inline`·`table` 은 컨테이너가 못 됐고 `inline-block` 은 됐다.
  박스를 안 만들거나 크기 컨테인먼트가 안 걸리는 박스이기 때문이다([16번 주제](../16-display-inner-outer/2-summary.md)).
  ★ 셋 다 `container-type` 계산값은 `inline-size` 였다 — **조용히 실패하는 네 번째 얼굴**이다.
- **스타일 쿼리는 「상태를 DOM 대신 CSS 로 내려보내는」 길을 연다.** 지금까지는 부모의 상태를 자손이 알려면 클래스를 자손까지 붙여야 했는데, 커스텀 속성 하나면 상속으로 내려가고 자손이 그것을 읽는다. 다만 Baseline **newly** 이고 Chrome 151 에서도 **커스텀 속성만** 된다.
- **구형 브라우저에서는 `@container` 블록이 통째로 사라진다**([07번 주제](../07-syntax-and-error-recovery/2-summary.md)). 그래서 **기본 배치는 at-rule 밖에 두고 향상만 안에** 담는 배치가 그대로 유효하다.

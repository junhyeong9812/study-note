# css/syntax/40 — 컨테이너 쿼리와 스타일 쿼리 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 값은 Google Chrome 151.0.7922.173 headless 에서 질문의 코드를 그대로 돌려 읽은 것**이다.\
> **뷰포트 무관성은 `--window-size` 를 500 · 780 · 1400 으로 바꿔 세 번 띄워** 확인했다.\
> 규칙은 [CSS Containment Module Level 3](https://drafts.csswg.org/css-contain-3/) 로 접지했다.\
> **엔진은 Chrome 하나다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 무엇이 조회 대상이 되는가

**출력** (Chrome 151 headless)

```text
.c1 (container-type 없음)              rgb(0, 0, 0)        안 먹음
.c2 (container-name 만)                rgb(0, 0, 0)        안 먹음
.c3 (container-type: inline-size)      rgb(21, 128, 61)    먹음

.p2 container-type = "normal"
.p2 container-name = "side"

cssRules 의 CSSContainerRule
  [" | (min-width: 300px)", "side | (min-width: 300px)", " | (min-width: 800px)", …]
```

**세 문단의 색**

- `.c1` **검정** · `.c2` **검정** · `.c3` **초록**(`rgb(21, 128, 61)`).

**`.p2` 의 `container-type`**

- **`normal`** 이다. `container-name` 을 줘도 타입은 안 바뀐다 — **이름만으로는 컨테이너가 안 된다.**

**`cssRules` 에 담겨 있는가**

- **담겨 있다.** `CSSContainerRule` 이 전부 살아 있고 `containerQuery` 도 원문 그대로다.

**07번의 어느 상태인가**

```text
   07번이 가른 네 상태 중
     "담겼는데 값이 안 먹는 경우 — 조건이 거짓"
   에 해당한다.  38번의 @media (unknown) 와 같은 모양이다

   문법 문제가 아니므로 조건 숫자를 고쳐도 영영 안 된다
```

### 2. `display` 가 자격을 바꾸는가

**출력** (Chrome 151 headless)

```text
  선언                                   자손의 색            container-type 계산값
  -----------------------------------    -----------------    --------------------
  display: contents                      rgb(0, 0, 0)         inline-size
  display: inline-block                  rgb(21, 128, 61)     inline-size
  display: table                         rgb(0, 0, 0)         inline-size
  display: inline (별도 판)              rgb(0, 0, 0)         inline-size
```

**실제로 컨테이너가 되는 것**

- **`inline-block` 하나뿐**이다.

**안 되는 것들의 계산값**

- ★ **전부 `inline-size`** 다. **실패한 티가 안 난다.**\
  박스를 아예 안 만들거나(`contents`) 크기 컨테인먼트를 받지 않는 박스(`table`·`inline`)라서 자격이 없는 것인데, 속성값은 그대로 남는다.

**같이 읽어야 할 것**

- **`display` 계산값**이다.

```text
   진단 순서
     1) getComputedStyle(부모).containerType   "normal" 이면 여기서 끝
     2) getComputedStyle(부모).display         contents / table / inline 이면 자격 없음
     3) 조상 사슬을 따라 올라가며 1~2 반복      "가장 가까운" 컨테이너가 다른 것일 수 있다
```

### 3. 자기 자신은 조회할 수 있는가

**출력** (Chrome 151 headless)

```text
.self         = rgb(0, 0, 0)        ★ 자기 자신은 안 먹는다
.self 의 자손 = rgb(21, 128, 61)    자손은 먹는다
```

**`.self` 의 색**

- **검정**. 조건은 참인데(폭 400px ≥ 300px) 자기 자신에게는 안 걸린다.

**왜 금지했나**

```text
   .self 가 자기 크기로 자기 스타일을 바꾼다
      -> 스타일이 바뀌면 크기가 바뀐다
         -> 크기가 바뀌면 조건이 뒤집힌다
            -> 스타일이 다시 바뀐다  ...  끝나지 않는다
```

- **순환**이다. 레이아웃이 수렴하지 않으므로 명세가 아예 「**조상만**」으로 못 박았다.

**우회**

```text
   <div class="card-wrap">      <- container-type 은 여기
     <div class="card">         <- @container 로 바꾸는 것은 여기
     </div>
   </div>
```

- **래퍼를 하나 더 둔다.** 우회가 아니라 **정석 배치**다.

### 4. 중첩 컨테이너

**출력** (Chrome 151 headless)

```text
.c6 color            = rgb(21, 128, 61)     (min-width: 300px) 참
.c6 background-color = rgba(0, 0, 0, 0)     (min-width: 800px) 거짓
```

**두 값**

- `color` **초록** · `background-color` **투명**(적용 안 됨).

**왜 안 걸리나**

```text
   <div class="outer" 900px  container>
     <div class="inner" 400px  container>      <- 가장 가까운 조상
       <p class="c6">

   c6 의 컨테이너 = .inner (400px)
     (min-width: 300px)  400 >= 300  -> 참
     (min-width: 800px)  400 >= 800  -> 거짓
   .outer 의 900px 은 아예 안 본다
```

**바깥을 조회하려면**

- **이름을 붙인다.**

```css
.outer { container-type: inline-size; container-name: page; }
@container page (min-width: 800px) { .c6 { … } }
```

### 5. `size` 의 대가

**출력** (Chrome 151 headless — 질문의 코드 그대로)

```text
.a height = 36px      .a scrollHeight = 36
.b height = 0px       .b scrollHeight = 36      ★ 내용은 그대로 있다
@container (min-height: 10px) 를 높이 없는 size 컨테이너에 대고 -> 거짓 (자손이 검정)
```

**두 상자의 `height`**

- `.a` **`36px`** · `.b` **`0px`**.

**`.b` 의 `scrollHeight`**

- **36** 이다. **내용이 사라진 게 아니라 크기에 기여하지 않게 됐을 뿐**이다.

**왜 `size` 에만 붙나**

```text
   높이를 조회한다 -> 자손 스타일이 바뀐다 -> 자손 높이가 바뀐다
                                              -> 부모 높이가 바뀐다 -> 조회가 뒤집힌다

   inline-size 는 이 고리가 없다.
   폭(인라인 축)은 원래 바깥이 정해 주는 축이라, 자손이 바뀌어도 부모 폭이 안 변한다
```

**`(min-height: 10px)`**

- **거짓**이다. 높이를 직접 안 주면 `size` 컨테이너의 높이는 0 이 되므로, **높이 조회가 항상 거짓**이 된다.\
  `size` 를 쓸 거면 `height` 나 `aspect-ratio` 로 높이를 직접 정해야 한다.

### 6. 스타일 쿼리의 규칙

**출력** (Chrome 151 headless — 질문의 코드 그대로)

```text
.s1 (container-type 있음, --theme: dark)   rgb(21, 128, 61)    먹음
.s2 (container-type 없음, --theme: dark)   rgb(21, 128, 61)    ★ 먹는다
.s3 (--theme: DARK)                        rgb(0, 0, 0)        ★ 안 먹는다
```

**세 문단의 색**

- `.s1` **초록** · `.s2` **초록** · `.s3` **검정**.

**갈리는 규칙 하나**

- **`container-type` 이 필요 없다는 것** 하나뿐이다.\
  나머지는 같다 — **자기 자신 조회 불가**(실측), **가장 가까운 조상**, 조건 문법.

```text
   +-----------------------------+-----------------------------+
   |        크기 쿼리             |        스타일 쿼리           |
   +-----------------------------+-----------------------------+
   | container-type 필요          | ★ 필요 없다                  |
   | 컨테인먼트가 켜진다          | 아무것도 안 켜진다           |
   | 자기 자신 조회 불가          | 자기 자신 조회 불가 (같다)   |
   | 가장 가까운 조상             | 가장 가까운 조상 (같다)      |
   +-----------------------------+-----------------------------+
```

**왜 그 하나만 다른가**

- **스타일 값을 읽는 것은 레이아웃을 안 건드리므로 순환이 안 생긴다.**\
  크기 쿼리의 `container-type` 은 「재도 된다」는 허락이 아니라 **「재기 전에 끊겠다」는 선언**이었고, 스타일 쿼리는 끊을 게 없다.\
  그래서 **모든 요소가 기본으로 스타일 컨테이너**다.

**덤 — `.s3` 이 안 걸린 이유**

- 커스텀 속성 값은 **토큰 그대로 비교**되고 **대소문자를 가린다.** `DARK` 는 `dark` 가 아니다.

### 7. 스타일 쿼리로 보통 속성을 물을 수 있는가

**출력** (Chrome 151 headless)

```text
.x1 = rgb(0, 0, 0)                      조건이 거짓이었다
cssRules 의 containerQuery = "style(color: red)"      ★ 파싱은 됐다
```

**`.x1` 의 색**

- **검정**. 규칙이 적용되지 않았다.

**`cssRules` 와 `containerQuery`**

- **담겨 있다.** `containerQuery` 로 `"style(color: red)"` 가 그대로 읽힌다 — **문법 오류가 아니다.**

**명세인가 구현인가**

- **구현의 한계다.** css-contain-3 의 Style Queries 는 **보통 속성도 허용**하지만 Chrome 151 은 **커스텀 속성만** 평가한다.
- 「**명세가 허용하는데 구현이 안 하는**」 자리이므로, 명세를 읽은 것으로는 확인이 안 된다.

**실무의 대체**

- **커스텀 속성으로 옮겨 놓고 조회한다.**

```css
.panel { --tone: danger; color: red; }
@container style(--tone: danger) { .badge { … } }
```

### 8. 스타일 쿼리의 다른 형태들

**출력** (Chrome 151 headless)

```text
style(--theme)      조상이 --theme 을 정함   -> rgb(29, 78, 216)   참
style(--theme)      아무도 안 정함            -> rgb(0, 0, 0)       거짓
not style(--theme: dark)  조상이 light        -> rgb(29, 78, 216)   참
(min-width: 300px) and style(--theme: dark)   -> rgb(29, 78, 216)   참
style(--ang: 45deg) @property 로 등록한 <angle> -> rgb(29, 78, 216) 참
자기 자신에게 style(--theme: dark)             -> rgb(0, 0, 0)      거짓
```

**값을 빼면**

- **그 속성이 정해져 있는지**만 묻는다(존재 질의). 실측에서 정한 쪽은 참, 아무도 안 정한 쪽은 거짓이었다.

**`not` 과 `and`**

- **둘 다 쓸 수 있다.** 크기 조건과 스타일 조건을 한 줄에 섞는 것도 된다.

**등록한 커스텀 속성**

- **조회된다.** `@property --ang { syntax: "<angle>" … }` 로 등록한 속성이 `style(--ang: 45deg)` 에 걸렸다([37번 주제](../37-at-property/2-summary.md)).

**자기 자신**

- **안 걸린다.** 크기 쿼리와 같다 — 스타일 쿼리도 **조상만** 본다.

### 9. 뷰포트와 무관한가

**출력** (Chrome 151 headless — 같은 문서를 세 폭에서)

```text
  --window-size      .w320 .card                        .w640 .card
  ---------------    -------------------------------    -------------------------------
  500,400            bg rgb(226,232,240)  font 14px     bg rgb(191,219,254)  font 20px
  780,400            bg rgb(226,232,240)  font 14px     bg rgb(191,219,254)  font 20px
  1400,400           bg rgb(226,232,240)  font 14px     bg rgb(191,219,254)  font 20px
```

**달라지는가**

- **한 글자도 안 달라진다.** 컨테이너 쿼리는 뷰포트를 **아예 보지 않는다.**

**컨테이너 폭이 `%` 이면**

- **달라진다.** 그때 달라지는 것은 **컨테이너의 실제 폭**이지 조회 대상이 바뀌는 것이 아니다.\
  「무엇을 재는가」는 여전히 컨테이너 상자이고, 그 상자가 뷰포트에 연동돼 있을 뿐이다.

**같이 쓸 수 있는가**

- **쓸 수 있다.** 축이 다르므로 대체 관계가 아니다 — 페이지 골격은 `@media`, 컴포넌트는 `@container` 가 실무의 기본 배치다.

### 10. 다른 주제와 잇기

**조건 문법**

- **[38번 주제](../38-media-queries/2-summary.md)의 미디어 쿼리 문법**을 그대로 쓴다. 범위 구문(`(400px <= width <= 700px)`)·`and`·`or`·`not` 이 전부 같다.\
  다른 것은 **쓸 수 있는 기능 목록**뿐이다(크기 계열 + `style()`).

**구형 브라우저**

```text
   07번의 "모르는 at-rule 은 블록까지 통째로"

   @container (min-width: 500px) { .card { … } }
   ^^^^^^^^^^ 모르면 이 블록 전체가 cssRules 에 안 담긴다

   => 기본 배치는 at-rule 밖에, 향상만 안에
```

**`cqw`·`cqi` 의 정본**

- [목록의 **34번 주제**](../34-viewport-and-container-units/)(길이 단위)다. 여기는 **조회 규칙만** 다룬다.\
  여기서 쓸 결론은 하나 — **그 단위도 `container-type` 이 선언된 조상이 있어야 기준이 생긴다.**

**`CSS.supports('at-rule(@container)')`**

- 실측에서 **`true`** 였다. `@property` 도 `true` 였고, 모르는 것(`at-rule(@zzbogus)`)은 `false` 였다([41번 주제](../41-supports-feature-queries/2-summary.md)).

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless. **엔진은 이것 하나다**(Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고, WebKit 은 없다).

**하네스** — 37\~41 다섯 주제가 공유한 것이다. 이 주제는 **뷰포트를 바꿔도 값이 안 바뀌는 것**을 보이는 것이 측정의 절반이다.

```bash
# harness.sh body.html probes.js W H  (37~41 공유)
for w in 500 780 1400; do
  google-chrome --headless --disable-gpu --no-sandbox --window-size=$w,400 --dump-dom "$D/index.html"
done
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| `container-type` 유무·`container-name` 만·`size`·이름 있는 컨테이너 6경우 | 1 | 동작 방식 (1) · A1 |
| 질문 1의 코드 그대로(`.p1`·`.p2`·`.p3`) | 1 | A1 |
| `display` 4종(`contents`·`inline`·`inline-block`·`table`) × `container-type` | 2 | 동작 방식 (1) · A2 |
| 자기 자신 조회(크기) | 1 | 동작 방식 (2) · A3 |
| 중첩 컨테이너 900/400 두 조건 | 1 | 동작 방식 (2) · A4 |
| `size` 의 height·clientHeight·scrollHeight 3경우 | 2 | 동작 방식 (3) · A5 |
| 높이 없는 `size` 에 `(min-height: 10px)` | 1 | A5 |
| `contain` 계산값 확인 | 1 | 동작 방식 (3) |
| 스타일 쿼리 7경우(타입 유무·대소문자·등록 속성·존재 질의) | 2 | 동작 방식 (5) · A6 · A8 |
| `style(color: red)` + `containerQuery` 읽기 | 2 | 동작 방식 (5) · A7 |
| `not style(…)` · `(min-width) and style(…)` | 1 | A8 |
| 자기 자신 조회(스타일) | 1 | A6 · A8 |
| `container: mybox / inline-size` 단축 풀림 | 1 | 동작 방식 (1) |
| demo 를 500 · 780 · 1400 세 폭에서 | 3 | demo · A9 |
| demo 의 「바꿔 볼 것」 — `container-type` 제거 | 1 | demo |
| demo 의 「바꿔 볼 것」 — `.w320` 을 520px 로 | 1 | demo |
| **제출 직전 demo 재추출·재실행 대조** | 1 | 어긋남 0건 |
| `CSS.supports('at-rule(@container)')` | 1 | A10 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| `style(color: red)` 가 거짓인 것 | 조건 false | **명세는 허용한다.** 구현이 따라오면 바뀐다 |
| `contain` 계산값이 `none` 인 것 | `none` | 속성 분리·직렬화 방식이다 |
| `display: table` 이 컨테이너가 못 되는 것 | 자손 `rgb(0,0,0)` | 명세의 「컨테인먼트가 적용되는 박스」 목록에 달렸다 |
| Baseline | 크기 쿼리 widely 2025-08-14 · 스타일 쿼리 newly 2026-05-19 | 2차 집계(`api.webstatus.dev`) |

**안 돌려 본 것** — ① Firefox·Safari 에서의 재현(엔진이 없다). ② `cqw`·`cqi` 단위의 실제 계산(정본이 [목록의 **34번 주제**](../34-viewport-and-container-units/)라 여기서는 결론만 적고 값을 주장하지 않았다). ③ 세로 쓰기(`writing-mode: vertical-*`)에서 `inline-size` 가 높이를 가리키게 되는 경우 — 본문에서 「가로 쓰기에서」라고 한정해 적었다.

## 용어 풀이

- **컨테이너 쿼리** — 조상 상자의 크기로 조건을 평가하는 `@container` 규칙.
- **질의 컨테이너** — `container-type` 이 `normal` 이 아니고 **자격이 있는 박스인** 요소.
- **`container-type`** — `normal`·`inline-size`·`size`. 계산값이 `inline-size` 라도 `display` 때문에 실패할 수 있다.
- **`container-name`** — 이름표. 이것만으로는 컨테이너가 되지 않는다.
- **컨테인먼트** — 안팎의 영향을 끊는 것. `size` 는 내용이 크기에 기여하지 않게 만든다.
- **인라인 축** — 글이 흐르는 방향. 가로 쓰기에서는 폭.
- **스타일 쿼리** — `@container style(…)`. `container-type` 이 필요 없고, Chrome 151 에서는 커스텀 속성만 된다.
- **존재 질의** — `style(--x)` 처럼 값을 뺀 형태. 그 속성이 정해져 있는지만 묻는다.
- **`CSSContainerRule`** — `@container` 의 CSSOM 타입. `containerName`·`containerQuery` 를 읽는다.
- **순환(cycle)** — 조회 결과가 조회 대상을 바꾸는 고리. 자기 조회 금지와 `size` 억제의 이유.

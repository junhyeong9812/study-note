# css/syntax/13 — 의사 요소와 생성 콘텐츠: `::before`/`::after`/`::marker`/`::selection` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 계산값 · 모든 「담김/버림」 판정 · 모든 치수 · 접근성 트리 덤프는 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려 확인한 것**이다.\
> 계산값은 전부 `getComputedStyle(el, '<의사 요소>')` 로 읽었다 — **두 번째 인자가 있다.**\
> 명시도는 [02번 주제](../02-specificity/2-summary.md)의 두 판 방식(동점 경쟁자 · 한 칸 낮은 경쟁자)으로 고정했고, 경쟁자에도 같은 의사 요소를 붙였다.\
> 접근성 트리는 CDP 의 `Accessibility.getFullAXTree` 로 덤프했다.\
> 규칙은 [CSS Pseudo-Elements 4](https://drafts.csswg.org/css-pseudo-4/) · [CSS Lists 3](https://drafts.csswg.org/css-lists-3/) · [Selectors 4](https://drafts.csswg.org/selectors-4/) 로 접지했다. **엔진은 Chrome 하나다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 막대가 몇 개 보이는가

**실행 결과** (Chrome 151 headless)

```text
             ::before content   ::before width   기원 요소 offsetWidth
  #a(없음)   "none"             50px             8px
  #b(content:"")  "\"\""       50px             58px
```

**파란 막대는 몇 개인가**

- **1개.** `#b` 에만 생긴다.

**`getComputedStyle(a, '::before').width` 는**

- **`50px`** 을 돌려준다. 상자가 없는데도 값이 나온다.

**그 값이 근거가 되는가**

- **안 된다.** `getComputedStyle` 은 **선언이 계산된 결과**를 보여 줄 뿐, **상자가 만들어졌는지**는 말해 주지 않는다.
- 이 함정이 이 주제에서 가장 자주 나는 사고다.

**무엇으로 판정하는가**

- **치수다.** 기원 요소의 `offsetWidth`·`getBoundingClientRect()` 가 늘었는지 본다 — 8px 대 58px 로 **50px 차이**가 났다.
- 또는 스크린샷으로 픽셀을 센다.

### 2. 이 넷의 결과는 같은가 다른가

**실행 결과**

```text
  선언 없음        content 계산값 = none     offsetWidth = 8px    상자 ✘
  content: ""      content 계산값 = ""       offsetWidth = 58px   상자 ✔
  content: none    content 계산값 = none     offsetWidth = 8px    상자 ✘
  content: normal  content 계산값 = none     offsetWidth = 8px    상자 ✘
```

**상자가 생기는 것**

- **1개 — `content: ""` 뿐이다.**

**선언을 안 쓴 것과 `normal` 의 계산값**

- **둘 다 `none`** 이다.
- `content` 의 초깃값이 `normal` 이고, `::before`/`::after` 에서 `normal` 은 **`none` 으로 계산된다.** 그래서 「안 쓴 것」과 「`normal` 을 쓴 것」이 같아진다.

**`""` 와 `none` 이 다른 이유**

```text
   content 계산값이 none      ->  의사 요소를 「만들지 않는다」
   content 계산값이 ""        ->  만든다. 내용이 빈 것일 뿐이다
```

- 빈 문자열은 **내용이 없는 것**이지 **상자가 없는 것**이 아니다.
- 그래서 `content: ""` 에 `width`·`height`·`background` 를 주면 아이콘·구분선을 그릴 수 있다.

**화면만 보고 구분할 수 있는가**

- **안 된다.** 상자가 안 생기는 셋은 화면에서 완전히 똑같다.
- `content: ""` 도 치수나 배경을 안 주면 **폭 0 이라 안 보인다** — 그러면 넷이 전부 같아 보인다.

### 3. `content` 의 값이 계산값에 어떻게 남는가

**실행 결과**

```text
  content: attr(data-tag)         ->  "NEW"
  content: "★" / "별표"           ->  "★" / "별표"
  content: "[" counter(item) "] " ->  "[" counter(item) "] "
```

**셋의 계산값**

- `attr(data-tag)` → **`"NEW"`** — 속성 값이 이미 들어가 있다.
- `"★" / "별표"` → **`"★" / "별표"`** — 대체 텍스트까지 그대로.
- `"[" counter(item) "] "` → **`"[" counter(item) "] "`** — 함수가 **안 풀린 채** 남는다.

**이미 풀려 있는 쪽과 그 이유**

- **`attr()` 이 풀려 있다.**
- `attr()` 은 **그 요소의 속성 하나**만 보면 되므로 계산 시점에 값이 정해진다.
- `counter()` 는 **앞선 형제·조상의 카운터 상태**를 따라가야 정해지므로, 계산값 단계에서는 정할 수 없고 렌더 시점까지 미뤄진다.
- 렌더는 실제로 됐다 — 스크린샷에서 `[1] 가` · `[2] 나` · `[3] 다` 로 나왔다.\
  ★ **카운터 자체는 이 목록의 다른 자리다.** 여기서는 존재만 보이고 넘긴다.
- 같은 부류가 하나 더 있다 — `content: open-quote` 도 계산값에 `open-quote` 로 남고, 렌더·접근성 트리에는 `“` 가 들어간다.

**`/ "별표"` 는 남는가**

- **남는다.** 계산값 문자열에 `/` 와 함께 그대로 들어 있다.

**두 번째 인자를 빼면**

- **`normal`** 이 나온다 — 그것은 **기원 요소 자신의 `content` 값**이고, 의사 요소와는 다른 것이다.
- 값이 나오기 때문에 틀린 줄도 모르고 지나간다. **인자를 빼면 다른 것을 읽는다.**

### 4. 이 다섯 줄 중 살아남는 것은

**실행 결과** (`cssRules.length`)

```text
  div::before span   ->  버림
  p::before.cls      ->  버림
  p::before::after   ->  버림
  p::before:hover    ->  버림
  :is(p::before)     ->  담김   selectorText = ":is()"
```

**몇 줄이 담기는가**

- **1줄 — 마지막 줄뿐이다.**

**마지막 줄의 `selectorText`**

- **`:is()`** — **안이 비었다.**
- `:is()` 는 관용적 선택자 목록을 받으므로, 그 자리에서 무효한 `p::before` 를 조용히 빼고 **자기는 살아남았다.**
- 빈 `:is()` 는 아무것도 매치하지 않으므로 **규칙은 있고 효과는 없다.**
- 같은 함정을 `:has()` 쪽에서도 봤다([12번 주제](../12-has-relational-selector/2-summary.md) 7번).\
  대조로 `p::before:not(.x)` 는 **버려진다** — `:not()` 은 관용적이 아니기 때문이다.

**네 번째 줄에 대한 명세와 Chrome 151**

| | 뭐라고 하나 |
|---|---|
| **명세** | 어떤 의사 요소든 **사용자 동작 의사 클래스**(`:hover`·`:active` 등)가 뒤따를 수 있다. `::first-line:hover` 가 첫 줄에 마우스를 올렸을 때 맞는다는 **예까지 들어 놓았다** |
| **Chrome 151** | **버린다.** 의사 요소 8종 × `:hover`/`:active`/`:focus` = 24 조합을 전부 던졌고 **24개 모두** `cssRules` 에 안 담겼다 |

- 이 자리는 **명세와 구현이 갈린다.** 문서를 보고 쓰면 Chrome 151 에서는 규칙째 사라진다.
- 이 문서가 쓸 수 있는 말은 **「Chrome 151 에서는 안 된다」까지**다. 다른 엔진은 이 머신에서 확인할 수 없다.

**의사 요소는 어디에만 오는가**

- **복합 선택자의 맨 끝**이다. 명세가 「일반적으로 복잡 선택자의 마지막 복합 선택자 끝에 놓일 때만 유효하다」고 정한다.
- 예외는 **건별로 정한 것**뿐이다 — 실측에서 `p::before::marker`·`li::before::marker` 가 담겼다.

### 5. 어느 쪽이 이기는가

**실행 결과**

```text
  green 먼저 쓴 판   ->  ::before color = rgb(0, 128, 0)   green
  red 먼저 쓴 판     ->  ::before color = rgb(0, 128, 0)   green
```

**두 선택자의 `(A, B, C)`**

```text
  p.c1::before
   ├ p          C +1
   ├ .c1        B +1
   └ ::before   C +1        =  (0, 1, 2)

  section p::before
   ├ section    C +1
   ├ p          C +1
   └ ::before   C +1        =  (0, 0, 3)
```

**무슨 색인가**

- **green.** `(0,1,2) > (0,0,3)` — B 자리에서 이미 갈린다.

**순서를 바꾸면**

- **안 바뀐다.** 두 판 다 green 이었다.
- 동점이면 뒤에 쓴 쪽이 이기므로, **두 판이 같다는 것 자체가 동점이 아니라는 증거**다.
- C 를 아무리 모아도 B 하나를 못 이긴다 — 자리끼리 **올림이 없다**([02번 주제](../02-specificity/2-summary.md)).

**같은 자리에 들어가는가**

- **아니다.**
- **의사 클래스 → B 자리**(클래스와 같은 급) · **의사 요소 → C 자리**(타입과 같은 급).
- 실측 대조: `p:nth-child(1)::before` 와 `p.c1::before` 가 **둘 다 (0, 1, 2)** 였다.

### 6. 콜론 하나와 둘

**실행 결과**

```text
  p:before   담김   selectorText = "p::before"
  p:after    담김   selectorText = "p::after"
  p:first-line   담김   selectorText = "p::first-line"
  p:first-letter 담김   selectorText = "p::first-letter"
  p:marker   버림
  p:before 의 명시도 = (0, 0, 2)   (= p::before)
```

**고르는 것과 명시도**

- **둘 다 같다.** 고르는 것도 같고 명시도도 `(0, 0, 2)` 로 같다.

**`selectorText` 는**

- **`p::before`** — **콜론이 둘로 바뀌어 나온다.**
- 명세가 「파싱할 때 표준 이름으로 바뀌며, 선택자를 나타내는 **어떤 객체 모델에도 옛 이름이 남지 않는다**」고 정한 그대로다.

**콜론 하나로 쓸 수 있는 것**

- **넷뿐이다** — `::before`·`::after`·`::first-line`·`::first-letter`.
- CSS 레벨 2 에 있던 것들이고, 이미 쓰인 시트를 깨뜨릴 수 없어 **레거시 별칭**으로 남겨 뒀다.

**`p:marker` 는**

- **규칙째 버려진다.** `p:bogus-xyz` 와 같은 취급이다 — 파서에게는 「모르는 의사 클래스」다.
- 레거시 별칭은 **넷에만** 있다. `::marker`·`::selection`·`::placeholder`·`::backdrop` 에는 없다.

### 7. 선언은 있는데 안 먹는다

**실행 결과**

```text
  cssRules.length = 1
  cssRules[0].cssText
    #m1::marker { color: rgb(185, 28, 28); background: rgb(0, 0, 255); padding: 40px; }
  계산값 (getComputedStyle(li, '::marker'))
    color = rgb(185, 28, 28)      font-size = 28px      content = "◆ "
    background-color = rgba(0, 0, 0, 0)   padding-left = 0px   border-left-width = 0px
  li 높이 16px -> 27px   (글꼴이 실제로 커졌다)
```

**담기는가**

- **담긴다.** 선택자는 멀쩡하다.

**`cssText` 에 `background` 가 남아 있는가**

- **그대로 남아 있다.** `background: rgb(0, 0, 255)` 가 보인다.
- 곧 **파싱은 정상이었다.** 버려진 것은 선택자도 선언도 아니다.

**실제로 효과가 나는 것**

| 선언 | 효과 |
|---|---|
| `color` | ✔ |
| `font-size` | ✔ |
| `content` | ✔ |
| `background` | ✘ |
| `padding` | ✘ |
| `border` | ✘ |

- 명세가 그렇게 정한다 — **표지 상자에 실제로 적용되는 것**은 `content`·`text-combine-upright`·`unicode-bidi`·`direction`·모든 애니메이션/전환 속성뿐이고, 나머지는 **효과를 갖지 않아야 한다.**
- `color`·`font-size` 가 먹는 것은 **상속되는 텍스트 속성이 표지의 「내용」으로 상속돼서**다. **상자에 먹는 것과 내용에 상속되는 것은 다른 층이다.**

**둘을 무엇으로 구분하는가**

```text
   선택자가 버려졌다        속성이 안 먹었다
   cssRules 에 없다         cssRules 에 있다
                            cssText 에 선언도 그대로 있다
                            계산값만 초깃값이다
```

- **`cssRules` 를 보면 갈린다.** 그래서 진단은 늘 「담겼나」 → 「먹었나」 순서다.

### 8. 같은 선언에 다르게 답한다

**실행 결과**

```text
                     ::first-line        ::first-letter
  margin-left        0px                 30px
  padding-left       0px                 30px
  border-left-width  0px                 4px
  width              auto                auto
  display            inline              inline
  background-color   rgb(253, 224, 71)   rgb(253, 224, 71)
  color              rgb(185, 28, 28)    rgb(185, 28, 28)
```

**계산된 `margin-left`**

- `::first-line` → **`0px`**(안 먹는다) · `::first-letter` → **`30px`**(먹는다).

**둘 다 받는 속성**

- **글꼴 속성 · `color` · 배경 속성 · 텍스트 장식 계열 · 인라인 조판 속성.**
- 스크린샷으로도 확인했다 — 두 문단 모두 노란 배경과 빨간 글자가 나왔고, `::first-letter` 쪽만 첫 글자가 밀리고 왼쪽에 빨간 세로 선이 그어졌다.

**`::first-line` 이 여백을 안 받는 이유**

- **첫 줄이 무엇인지가 줄바꿈의 결과**인데, 여백을 주면 그 여백이 다시 줄바꿈을 바꿔 **순환**이 생기기 때문이다.
- `::first-letter` 는 첫 글자가 **줄바꿈과 무관하게 정해지고** 인라인 박스에 가까운 물건이라, 명세가 margin·padding·border·box-shadow 를 **명시적으로 허용**한다.

**하이라이트 의사 요소는**

- **더 좁다.** `color`·`background-color`·텍스트 장식 계열 정도만 받는다.
- 명세가 이유를 적어 놓았다 — 하이라이트는 **매우 동적인 환경에서 성능 좋게 칠해야** 하고, 렌더 결과가 UA 가 정하는 **하이라이트 영역의 정확한 경계에 의존하지 않아야** 하기 때문이다.

### 9. 상태가 필요한 것들은 어떻게 확인하는가

**실행 결과**

```text
  ::selection    선택 전 background-color = rgb(253, 224, 71)
                 선택 후 background-color = rgb(253, 224, 71)      <- 같다
  ::placeholder  value 비었을 때 color = rgb(21, 128, 61)
                 value 채운 뒤  color = rgb(21, 128, 61)           <- 같다
                 :placeholder-shown 매치 수  1 -> 0 -> 1
  ::backdrop     showModal() 전 background = rgba(1, 2, 3, 0.5)
                 showModal() 후 background = rgba(1, 2, 3, 0.5)    <- 같다
                 :modal 매치 수  0 -> 1
```

**`::selection` 은 다른 값을 주는가**

- **아니다. 똑같다.** 선택이 없어도 선언한 값을 돌려준다.

**`::placeholder` 는 바뀌는가**

- **안 바뀐다.** 자리표시 글자가 화면에서 사라져도 계산값은 그대로다.
- 상태를 관찰하려면 **`:placeholder-shown` 의 매치 수**를 봐야 한다 — 실측에서 1 → 0 → 1 로 정확히 움직였다.

**`showModal()` 전에 읽으면**

- **선언한 값이 그대로 나온다**(`rgba(1, 2, 3, 0.5)`). 모달이 열리지도 않았는데 그렇다.
- 상태는 **`:modal` 의 매치 수**로 확인했다 — 0 → 1.

**「지금 칠해져 있나」는 무엇으로 확인하는가**

- **렌더 결과다.** 이 주제에서는 스크린샷의 픽셀을 세어 확인했다.
- `::selection` 은 실제로 확인했다 — `Range` 로 문단을 선택한 뒤 찍은 스크린샷에서 **선택된 줄에만** `rgb(253, 224, 71)` 픽셀 **1,692개**와 글자색 `rgb(185, 28, 28)` 이 나왔고, 선택하지 않은 줄에는 노란 픽셀이 **0개**였다.
- ★ **`::placeholder` 와 `::backdrop` 의 렌더 결과는 이 문서에서 확인하지 않았다.** 계산값과 상태 의사 클래스까지만 봤다.

### 10. 생성 콘텐츠는 읽히는가

**실행 결과** (CDP `Accessibility.getFullAXTree` 덤프에서 뽑은 것)

```text
  paragraph #a
    StaticText '필수 '        <- ::before 가 만든 노드
    StaticText '이름'
  paragraph #b
    StaticText '별표'         <- ★ 이 아니라 대체 텍스트
    StaticText '별점'
  paragraph #e
    StaticText 'alt 빈 문자열'  <- '장식' 노드가 없다
```

**텍스트 노드가 생기는 것**

- **2개 — `#a` 와 `#b`.** `#e` 는 생기지 않는다.

**`#b` 에서 오르는 문자열**

- **`별표`** 다. 화면의 `★` 이 아니라 **대체 텍스트**가 오른다.

**「보조기기가 무시한다」는 맞는가**

- **아니다.** Chrome 151 의 접근성 트리에 **별도 `StaticText` 노드로 오른다.**
- 대조 실측: `content: "*"` 도 `StaticText '*'` 로 그대로 올랐다 — **별표가 그대로 읽힌다.**
- `content: url(1×1 GIF)` 는 **이름 없는 `image` 노드**가 됐다.

**순수 장식용 아이콘은**

```css
.deco::before { content: "◆" / ""; }
```

- **대체 텍스트를 빈 문자열로** 준다. 실측에서 `"장식" / ""` 은 접근성 트리에 **노드 자체가 안 생겼다.**
- 뜻이 있는 표시라면 반대로 `content: "*" / "필수 항목"` 처럼 **읽힐 말을 준다.**
- 이 문법의 Baseline 은 **newly 2024-07-09**(Chrome 77 · Safari 17.4 · Firefox 128) 이다.

### 11. 왜 그렇게 정해졌나

**`:has()` 에 만드는 제약**

- 의사 요소의 **존재 자체가 CSS 선언의 결과**이므로, `:has()` 로 그것을 질의하면 **순환**이 생긴다.

```text
   .card:has(::before) 를 허용한다면

   ::before 가 있나?    ->  .card 의 스타일을 봐야 안다
   .card 의 스타일은?   ->  이 규칙이 맞는지 봐야 안다
   이 규칙이 맞나?      ->  ::before 가 있나?      <-- 되돌아왔다
```

- 그래서 명세는 `:has-allowed pseudo-element` 로 따로 허용되지 않은 의사 요소를 `:has()` 인자에서 **금지**한다. 정본은 [12번 주제](../12-has-relational-selector/2-summary.md).

**`::first-line` 의 순환**

- 첫 줄이 어디까지인지는 **줄바꿈이 정한다.**
- 거기에 여백·테두리를 주면 **남는 폭이 줄어들어 줄바꿈이 달라지고**, 그러면 첫 줄의 범위가 달라져 여백이 다시 적용될 대상이 바뀐다.

**하이라이트를 좁게 제한한 이유**

- **성능**(매우 동적인 환경에서 즉시 칠해져야 한다)과 **상호운용성**(UA 가 정하는 하이라이트 영역의 정확한 경계에 렌더가 의존하면 안 된다).

**콜론 하나를 남긴 이유**

- **이미 쓰인 시트를 깨뜨릴 수 없기 때문이다.** CSS2 시절에는 의사 클래스와 의사 요소가 같은 표기였고, CSS2.1 에서 둘을 갈랐다.
- 그래서 **넷만** 레거시 별칭으로 남기고, 파싱 뒤에는 표준 이름으로 통일한다.
- **새로 쓸 때는 콜론 둘**을 쓴다. 남겨 둔 것은 선택지가 아니라 호환 장치다.

### 12. 다른 주제와 잇기

**`:is()` 안에서 규칙이 살아남는 이유**

- `:is()` 가 받는 것이 **관용적 선택자 목록**이라, 그 자리에서 무효한 항목만 조용히 빼고 자기는 유효하게 남기 때문이다.
- 그 결과가 `:is()` — **텅 빈 채로 아무것도 매치하지 않는다.**
- `:not()` 은 관용적이 아니라 **규칙째 버려진다.** 같은 자리에 넣어도 결과가 반대다.

**`:has()` 를 어디에 거는가**

```css
.card:has(img)::before { content: "🖼"; }   /* ✔ */
.card::before:has(img) { content: "🖼"; }   /* ✘ 규칙째 사라진다 */
```

- **기준 요소 쪽에** 걸고, 의사 요소는 **그 뒤 맨 끝**에 둔다.

**`::marker` 에 배경·여백이 필요하면**

- **`li::before` 로 직접 그린다.** 표지 상자를 쓰지 않고 생성 콘텐츠로 같은 자리를 만드는 것이다.
- `list-style: none` 으로 기본 표지를 끄고 `::before` 에 번호·아이콘을 넣는 형태가 그래서 흔하다.

**`limited` 만 보고 판단해도 되는가**

- **안 된다.** `limited` 는 「**집계가 잡은 엔진 전부에서 확인되지 않았다**」는 뜻이지 「못 쓴다」가 아니다.
- 실제로 `::marker` 와 `::selection` 이 둘 다 `limited` 인데, `::selection` 은 데스크톱 Safari 1.1 부터 있다고 같은 조회에 적혀 있다(빠진 것은 iOS Safari 행이다).
- 판단은 **내가 받쳐야 하는 브라우저 목록**으로 한다. 그리고 이 머신에는 **WebKit 이 없어 실행으로 반증할 수 없다** — 아는 것은 「집계가 그렇게 말한다」까지다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 headless (`--headless --disable-gpu --no-sandbox`).\
접근성 트리는 같은 Chrome 을 `--remote-debugging-port` 로 띄워 CDP `Accessibility.getFullAXTree` 로 덤프했다.\
Firefox 155.0.1 은 이 환경에서 headless 스크린샷이 산출되지 않아 **쓰지 않았다.** 「두 엔진에서 확인했다」고 적지 않았다.

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| `content` 유무와 상자 생성 | `offsetWidth` + `getComputedStyle(el, '::before')` | 4종 1회 | 8 / 58 / 8 / 8 px |
| `content` 값 9종의 계산값 | `getComputedStyle(el, '::before').content` | 1회 | 본문 (2)절 표 |
| `counter()` 렌더 | 스크린샷 400×300 | 1회 | `[1] 가` · `[2] 나` · `[3] 다` |
| `open-quote` | 계산값 + AX 덤프 | 1회 | 계산값 `open-quote`, 트리에 `“` |
| 선택자 위치 34종 | `style.sheet.cssRules.length` + `selectorText` | 1회 | 본문 (3)절 표 |
| 의사 요소 뒤 의사 클래스 **48 조합** | 〃 | 1회 | `:hover`/`:active`/`:focus` 24개 전부 버림 |
| 명시도 11행 | `getComputedStyle` 동점·한 칸 낮음 두 판 | 행마다 2판 | 본문 (5)절 표 |
| 명시도 직접 겨루기 5판 | 앞뒤 순서를 바꿔 두 판씩 | 5종 | 본문 (5)절 표 |
| `::marker` 속성 6종 | `cssText` + 계산값 + `li` 높이 | 1회 | 3종 먹고 3종 안 먹음, 16 → 27px |
| `::first-line` 대 `::first-letter` | 같은 선언 7종의 계산값 + 스크린샷 | 1회 | 본문 (6)절 표 |
| `::selection` 실제 렌더 | `Range` 선택 + 스크린샷 300×120 픽셀 계수 | 1회 | 노란 픽셀 1,692 / 0 |
| `::placeholder` 상태 | `value` 채우고 비우기 + `:placeholder-shown` | 1회 | 매치 수 1 → 0 → 1 |
| `::backdrop` 상태 | `showModal()` + `:modal` | 1회 | 매치 수 0 → 1 |
| 접근성 트리 | CDP `Accessibility.getFullAXTree` | 2회(5종 + 3종) | 본문 (8)절 표 |
| `demo` 블록 | `--dump-dom` + 스크린샷 320×100 | 1회 | 파란 픽셀 480개, **둘째 줄에만** |
| `demo` 의 「바꿔 볼 것」 3종 | 규칙만 갈아끼워 재측정 | 각 1회 | `none`·`normal` 둘 다 `content` 계산값이 `none`, `.bar::before` 는 두 줄 다 `""` |
| Baseline 7종 | `api.webstatus.dev/v1/features/<id>` | 각 1회 | 본문 「구현 세부사항 대 언어 보장」의 표 |

**구현 의존 항목** (버전이 오르면 다시 찍을 것)

- **의사 요소 뒤의 `:hover`·`:active`·`:focus`** — 명세는 허용하는데 Chrome 151 이 버린다. **다음 버전에서 다시 찍을 자리다.**
- `attr()` 이 계산값에 풀려 있고 `counter()`·`open-quote` 는 안 풀리는 것 — 계산 시점의 구현 선택이다.
- `selectorText` 의 직렬화 형태(`:is()` 가 비워지는 것) — Chrome 151 이 보여 준 것이다.
- 접근성 트리의 노드 역할·이름 — Chrome 의 표현이다. **스크린 리더가 실제로 어떻게 읽는지는 확인하지 않았다.**

**측정하지 않은 것 (「미실행」)**

- **Safari/WebKit 전체.** 이 머신에 없다. `::marker`·`::selection` 의 `limited` 판정은 **반증할 수 없었다.**
- **`::placeholder`·`::backdrop` 의 렌더 결과.** 계산값과 상태 의사 클래스까지만 봤다.
- **스크린 리더의 실제 낭독.** 접근성 트리 덤프까지만 봤다.
- **`::before::marker` 의 동작.** 파싱되는 것만 확인했다.
- **하이라이트의 캐스케이딩·상속 규칙**(css-pseudo-4 §3.5). 들어가지 않았다.
- **성능.** 이 주제에서 성능 주장을 하나도 하지 않았다.

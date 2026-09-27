# css/syntax/08 — 기본 선택자·조합자·속성 선택자 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 개수와 모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려 받은 것**이다.\
> 매치 개수는 `document.querySelectorAll(sel).length` 와 잡힌 노드의 `id`, 규칙 생존 여부는 `document.styleSheets[*].cssRules` 로 읽었다.\
> 규칙은 [Selectors Level 4](https://drafts.csswg.org/selectors-4/) 로, 지원 상태는 `api.webstatus.dev` 조회(2026-09-23)로 접지했다. **엔진은 Chrome 하나다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 조합자 넷은 각각 몇 개를 잡는가

**실행 결과** (Chrome 151 headless, 질문의 트리)

```text
  .wrap p     ->  4개   P1, P2, P3, P4
  .wrap > p   ->  3개   P1, P2, P4
  .hd + p     ->  1개   P1
  .hd ~ p     ->  3개   P1, P2, P4
  .x + .x     ->  0개
```

**넷은 각각 몇 개를 잡고, 어느 노드인가**

- 위 출력 그대로다. **`.wrap p` 4개 · `.wrap > p` 3개 · `.hd + p` 1개 · `.hd ~ p` 3개.**

```text
   section.wrap
    ├─ h2.hd      기준
    ├─ P1         자손 O  자식 O  인접 O  일반 O
    ├─ P2         자손 O  자식 O  인접 X  일반 O
    ├─ div.inner
    │   └─ P3     자손 O  자식 X  인접 X  일반 X
    └─ P4         자손 O  자식 O  인접 X  일반 O
```

**`P3` 이 잡히는 선택자와 안 잡히는 선택자**

- 잡히는 것: **`.wrap p`**(자손) 하나뿐이다.
- 안 잡히는 것: `.wrap > p`(한 칸만 내려간다) · `.hd + p`·`.hd ~ p`(**부모가 달라 형제가 아니다**).
- 갈리는 이유는 **깊이**(자손 대 자식)와 **부모가 같은가**(형제 여부) 두 가지다.

**`.x + .x` 는 몇 개인가**

- **0개.** `.x` 는 `P1`·`P3`·`P4` 셋인데 **서로 인접한 쌍이 없다.**
  - `P1` 의 다음 형제는 `P2`(클래스 없음)
  - `P3` 은 `div.inner` 안에 혼자 있다
  - `P4` 의 이전 형제는 `div.inner`

**`.hd ~ p` 가 `P3` 을 못 잡는 이유**

- **`P3` 은 `h2.hd` 의 형제가 아니라 조카다** — `~` 는 같은 부모를 가진 뒤쪽 형제만 본다.

### 2. 부모를 고르는 조합자는 무엇인가

**실행 결과**

```text
  document.querySelectorAll('p < section')
    -> SyntaxError: Failed to execute 'querySelectorAll' on 'Document':
       'p < section' is not a valid selector.
  document.querySelectorAll('p ! section')   -> 같은 SyntaxError
  document.querySelectorAll('p:parent')      -> 같은 SyntaxError

  스타일시트 실험
    .x, p < section { color: red }
    p ! section     { color: blue }
    .x              { color: green }
    cssRules 에 남은 것: ['.x']
```

**위쪽·앞쪽으로 가는 조합자는 몇 개인가**

- **0개.** 네 조합자는 **전부 아래 또는 뒤로만 간다** — 아래는 자손·자식, 뒤는 인접 형제·일반 형제다.

**`querySelectorAll('p < section')` 은 무엇을 돌려주는가**

- 아무것도 안 돌려준다 — **`SyntaxError` 예외를 던진다.** JS 에서는 시끄럽게 실패한다.

**CSS 파일 안에 쓰면 무슨 일이 일어나고 어떻게 확인하는가**

- **에러도 경고도 없이 규칙이 통째로 버려진다.** 화면에는 「아무 일도 안 일어난 것」으로만 보인다.
- 확인 방법은 **`document.styleSheets[0].cssRules` 를 읽어 그 선택자가 목록에 없는지 보는 것**이다.
- 위 실험에서 세 규칙 중 **`.x` 하나만** 남았다. `p < section` 이 섞인 첫 규칙은 `.x` 까지 같이 죽었다.

**그 제약을 뚫는 문법**

- **`:has()`** 다. 실측에서 `section:has(> p.x)` 가 `.wrap` 하나를 잡았다.
- 정본은 [목록의 **12번 주제**](../12-has-relational-selector/)다.

### 3. `~=` 와 `*=` 는 어디서 갈리는가

**실행 결과** (질문의 링크 넷)

```text
  [data-tags~="alpha"]   ->  2개   1("alpha beta"), 3("beta alpha")
  [data-tags*="alpha"]   ->  3개   1, 2("alphabet"), 3
  [data-tags^="alpha"]   ->  2개   1, 2
  [data-tags$="alpha"]   ->  1개   3
```

**`[data-tags~="alpha"]` 는 몇 개인가**

- **2개** — `"alpha beta"` 와 `"beta alpha"`.

**`[data-tags*="alpha"]` 는 몇 개인가**

- **3개** — 위 둘에 **`"alphabet"`** 이 더해진다.

**차이를 만드는 요소와 그 이유**

```text
   "alphabet"
     ~=  값을 공백으로 쪼갠다 -> ["alphabet"] -> "alpha" 라는 낱말이 없다 -> X
     *=  문자열 아무 데나 찾는다 -> "alphabet" 안에 "alpha" 가 있다      -> O
```

- 곧 **`~=` 는 낱말 단위, `*=` 는 글자 단위**다.
- `class` 를 속성 선택자로 고를 때 원하는 것은 거의 항상 `~=` 이고, 그건 그냥 `.alpha` 다.

**`^=` 와 `$=` 는 각각 몇 개인가**

- `^=` **2개** — `"alpha beta"`(alpha 로 시작) · `"alphabet"`(alpha 로 시작).
- `$=` **1개** — `"beta alpha"`(alpha 로 끝).

### 4. `|=` 는 접두사 매칭인가

**실행 결과**

```text
  [hreflang|="en"]   ->  3개   en-US, en, en-GB
  [hreflang^="en"]   ->  4개   en-US, en, en-GB, english
  [hreflang="en"]    ->  1개   en
```

**`[hreflang|="en"]` 은 몇 개인가**

- **3개.** `en-US` · `en` · `en-GB` 다. **`english` 는 안 잡힌다.**

**`^=` 와 답이 다른가, 어디서 갈리는가**

- **다르다.** `english` 에서 갈린다 — `^=` 는 잡고 `|=` 는 안 잡는다.

**`|=` 가 보는 경계 문자**

- **하이픈 `-`** 다. `[x|="v"]` 는 값이 **정확히 `v`** 이거나 **`v-` 로 시작**할 때만 맞는다.
- 언어 태그(`en-US`·`zh-Hant`)를 위해 만들어진 연산자다.

**`[hreflang="en"]` 은 몇 개인가**

- **1개.** 정확히 `en` 인 것뿐이다.

### 5. 대소문자는 어디서 구분되는가

**실행 결과**

```text
  DIV            -> 2개        div            -> 2개      (같다)
  .CapCase       -> 1개        .capcase       -> 0개
  #Mix           -> 1개        #mix           -> 0개
  [data-K="V"]   -> 1개        [data-k="V"]   -> 1개      (이름은 무시)
                               [data-k="v"]   -> 0개      (값은 구분)
                               [data-k="v" i] -> 1개
  input[type="checkbox"] -> 2개   input[type="CHECKBOX"] -> 2개
```

**각각 몇 개인가**

- `div` **2개**(타입 선택자는 대소문자 무시) · `.capcase` **0개** · `#mix` **0개** · `[data-k="V"]` **1개** · `[data-k="v"]` **0개**.

```text
   ┌──────────────────┬────────┐
   │ 타입 선택자      │ 무시   │
   │ 속성 "이름"      │ 무시   │
   │ 클래스           │ 구분   │
   │ ID               │ 구분   │
   │ 속성 "값"        │ 구분 * │  * HTML 이 지정한 일부 속성은 예외
   └──────────────────┴────────┘
```

**`input[type="CHECKBOX"]` 는 몇 개이고 누구의 규칙인가**

- **2개** — `type="CHECKBOX"` 와 `type="checkbox"` 둘 다 잡힌다.
- **HTML 의 규칙이다.** HTML 이 "이 속성의 값은 ASCII 대소문자를 무시하고 맞춘다"고 지정한 목록에 `type` 이 있다. CSS 의 기본 규칙(값은 구분)이 아니다.

**`i` 와 `s` 플래그**

- **`i`** — 값 비교에서 **대소문자를 무시하도록 강제**한다. `[data-k="v" i]` 가 `data-K="V"` 를 잡았다(1개).
- **`s`** — 값 비교에서 **대소문자를 구분하도록 강제**한다(HTML 의 예외 목록을 무시하고 싶을 때).

**Chrome 151 에서 `input[type="CHECKBOX" s]` 를 CSS 에 쓰면**

```text
  querySelectorAll  ->  SyntaxError: 'input[type="CHECKBOX" s]' is not a valid selector.

  스타일시트에 넣고 cssRules 를 읽으면
    input[type="CHECKBOX" s] { outline: 2px solid red }   <- 목록에 없다
    input[type="checkbox"]   { outline-offset: 3px }      <- 있다
    [data-k="v" i]           { color: rgb(1,2,3) }        <- 있다
  남은 규칙: ['input[type="checkbox"]', '[data-k="v" i]']
```

- **선택자 자체가 무효라 규칙이 통째로 사라진다.** 경고 한 줄 없다.
- Baseline 도 **limited** — Firefox 66 만 구현했다(2026-09-23 `api.webstatus.dev` 조회). **오늘 쓸 문법이 아니다.**

### 6. 무효한 선택자 하나가 어디까지 죽이는가

**실행 결과**

```text
  cssRules 에 남은 것: ['.x']      <- 1개
```

**몇 개가 남고 무엇인가**

- **1개.** 마지막에 따로 쓴 **`.x`** 규칙만 남았다.

**`.x` 가 첫 줄에서 살아남지 못한 이유**

- **선택자 목록(쉼표)은 전부 아니면 전무**이기 때문이다.
- `p < section` 하나가 무효라 `.x, p < section { color: red }` **규칙 전체**가 버려졌다. `.x` 가 멀쩡한 것과 무관하다.

**"인자 하나만 죽게" 바꾸는 문법**

- **`:is()`**(와 `:where()`)다. 관대한 목록(forgiving selector list)이라 모르는 인자만 버린다.
- 실측: `:is(.t, :unknownzz)` 는 살아남아 `cssRules` 에 **`:is(.t)`** 로 찍혔다. 정본은 [11번 주제](../11-is-where-not/2-summary.md).

**화면만 보고 진단할 수 있는가**

- **없다.** 규칙이 없는 것과 규칙이 있는데 졌던 것이 화면에서 똑같이 보인다.
- `cssRules` 를 읽는 것이 유일한 관측 창이다.

### 7. "선택자를 고쳤는데 안 바뀐다"를 어떻게 가르는가

**원인 후보 셋과 확인 방법**

```text
  (1) 규칙이 아예 안 담겼다   ->  document.styleSheets[0].cssRules        (08 · 07번)
  (2) 담겼는데 매치가 0개다   ->  document.querySelectorAll(sel).length   (08 · 09 · 10번)
  (3) 매치는 됐는데 졌다      ->  getComputedStyle(el).<속성>             (01 · 02 · 11번)
```

- **순서가 중요하다.** (1)을 건너뛰면 존재하지 않는 규칙의 명시도를 계산하게 된다.

**「무엇이 잡혔나」와 「그래서 이겼나」가 다른 질문인 이유**

- 앞엣것은 **선택자의 모양**만으로 정해지고 **셀 수 있다.**
- 뒤엣것은 **다른 규칙들과의 경쟁 결과**라 그 요소를 **읽어 봐야** 안다.
- 실측이 그 독립성을 보여 준다 — `p:is(.t, #zz)` 와 `p:where(.t, #zz)` 는 **둘 다 2개**를 잡는데 명시도는 `(1,0,1)` 과 `(0,0,1)` 로 갈린다([11번](../11-is-where-not/2-summary.md)).

**명시도를 올려도 효과가 없는 경우**

- 상대가 `!important`(1단계)이거나 `style=""`(3단계)이거나 더 나중 레이어(4단계)일 때다.
- 명시도는 **5단계**라 그 위에서 이미 끝난 승부는 못 뒤집는다. 진단 순서는 [01번](../01-cascade-and-priority/2-summary.md)이 정본이다.

### 8. 같은 요소를 고르면서 세기만 낮추려면

**`#nav` 와 `[id="nav"]` 는 같은 요소를 고르는가**

- **같다.** 매칭 결과가 완전히 같다.

**둘의 명시도**

- `#nav` = `(1, 0, 0)` · `[id="nav"]` = `(0, 1, 0)`.
- **정본은 [02번 주제](../02-specificity/2-summary.md)** 「손으로 세어 보기」 표다(거기서 두 판으로 실측했다).

**조합자는 어느 자리에 얼마를 보태는가**

- **아무 자리에도 안 보탠다** — `(0, 0, 0)` 이다.
- 그래서 `.a .b` 와 `.a > .b` 는 명시도가 같다.

**「그물 모양」과 「그물의 힘」의 독립성이 여기서 어떻게 드러나나**

- `#nav` 와 `[id="nav"]` 는 **모양이 완전히 같고 힘만 다르다.**
- 그래서 마크업에 ID 가 이미 있을 때 **`[id="nav"]` 로 써서 세기를 클래스 급으로 낮추는** 실용 기법이 성립한다.

### 9. `*` 는 무엇을 잡는가

**실행 결과**

```text
  *   ->  11개
        html, head, meta, body, section.wrap, h2.hd, P1, P2, div.inner, P3, P4
  section > * > p     ->  1개   P3
  section * p         ->  1개   P3
  .wrap *             ->  6개   hd, P1, P2, inner, P3, P4
```

**몇 개인가**

- **11개.**

**내가 쓴 태그가 아닌 것**

- **`html` · `head` · `meta` · `body`** 넷이다. 파서가 만들어 넣은 것들인데 `*` 는 이것도 잡는다.
- `* { box-sizing: border-box }` 같은 선언이 문서 전체에 깔리는 이유가 이것이다.

**`section > * > p` 는 몇 개인가**

- **1개** — `P3`. "`section` 의 자식의 자식인 `p`"이므로 `div.inner` 를 한 칸 건너뛴 것만 잡는다.

**`*` 의 명시도**

- **`(0, 0, 0)`** 이다. 전체 선택자는 아무 자리에도 안 보탠다([02번](../02-specificity/2-summary.md)).

### 10. ID 가 문서에 둘 있으면

**실행 결과**

```text
  <p id="dup">A</p><p id="dup">B</p>

  #dup    ->  2개   dup, dup
  p#dup   ->  2개
  #dup { color: rgb(7,7,7) }  ->  두 문단의 계산색이 모두 rgb(7, 7, 7)
```

**`#dup` 은 몇 개인가**

- **2개.** CSS 는 중복 ID 를 만나면 **전부** 잡는다.

**`#dup { … }` 는 둘 다에 먹는가**

- **먹는다.** 위 계산색이 둘 다 `rgb(7, 7, 7)` 이었다.

**"ID 는 유일해야 한다"는 누구의 규칙인가**

- **HTML 의 규칙**이다. CSS 선택자 명세는 유일성을 요구하지 않는다.
- 그래서 HTML 이 깨져도 CSS 는 조용히 동작한다 — **마크업 검증이 따로 필요한 이유**다.

**ID 선택자가 클래스 선택자와 다른 점은 매칭인가 명시도인가**

- **명시도다.** 매칭 규칙은 "그 속성 값이 같은가"로 동일하고, `#x` 가 `A` 자리 · `[id="x"]` 와 `.x` 가 `B` 자리라는 점만 다르다.

### 11. 상태를 속성 선택자로 고르면

**실행 결과** (Chrome 151 + CDP 로 실제 클릭)

```text
  <input id="c1" type="checkbox" checked>   <input id="c2" type="checkbox">

  초기        c1: [checked] O  :checked O      c2: [checked] X  :checked X
  c1 을 끄고
  c2 를 켠 뒤  c1: [checked] O  :checked X      c2: [checked] X  :checked O
```

**사용자가 `c1` 의 체크를 끄면 `[checked]` 는 여전히 맞는가**

- **맞는다.** 속성은 마크업에 그대로 남아 있다.

**같은 시점에 `:checked` 는**

- **안 맞는다.** 상태는 꺼졌다.

**갈리는 이유**

- `[checked]` 는 「**문서에 적힌 초기값**」이고 `:checked` 는 「**지금 상태**」다.\
  사용자 조작은 프로퍼티(상태)를 바꾸고 속성은 안 바꾼다.

**이 구분의 정본**

- [10번 주제](../10-state-and-form-pseudo-classes/2-summary.md)다. 같은 관계가 `option[selected]` 대 `option:checked`, `[disabled]` 대 `:disabled` 에도 있다.

## 용어 풀이

- **선택자(selector)** — 어떤 요소에 규칙을 걸지 고르는 식.
- **단순 선택자** — 더 못 쪼개는 조각. 타입 · 전체 · 클래스 · ID · 속성 · 의사 클래스.
- **복합 선택자** — 공백 없이 붙인 묶음(`p.x[href]`). **같은 한 요소**를 가리킨다.
- **복잡 선택자** — 조합자로 이은 것(`.wrap > p`).
- **선택자 목록** — 쉼표로 나열한 것. **하나가 무효면 전체가 버려진다.**
- **조합자** — 공백(자손) · `>`(자식) · `+`(인접 형제) · `~`(일반 형제). 명시도 기여 0.
- **자손 / 자식** — 아래 어느 깊이든 / 바로 한 칸 아래.
- **인접 형제 / 일반 형제** — 바로 다음 형제 하나 / 뒤쪽 형제 전부. **둘 다 뒤로만 간다.**
- **속성 선택자** — 속성으로 고르는 것. 명시도는 **B 자리**.
- **`~=` / `*=`** — 공백으로 쪼갠 **낱말** 매칭 / **부분 문자열** 매칭.
- **`|=`** — 값이 정확히 `v` 이거나 `v-` 로 시작. **하이픈 경계**를 본다.
- **`i` / `s` 플래그** — 값 비교의 대소문자 무시 / 구분을 강제. `s` 는 Chrome 151 에서 무효다.
- **무효 선택자** — 파서가 이해 못 한 선택자. CSS 는 **조용히 버린다.**
- **`cssRules`** — 스타일시트에 실제로 담긴 규칙 목록. 규칙이 버려졌는지 확인하는 유일한 관측 창.

## 실행 검증

**환경** — Google Chrome **151.0.7922.173** (`--headless --no-sandbox --disable-gpu`), 이 머신에 Firefox 155.0.1 도 있으나 **headless 스크린샷이 산출되지 않아 쓰지 않았다.** WebKit(Safari)은 없다. **이 문서의 모든 값은 Blink 단일 엔진의 관찰이다.**

| 무엇을 | 어떻게 | 몇 번 | 결과가 실린 곳 |
|---|---|---|---|
| 조합자 넷 · 단순 선택자 · `*` | `querySelectorAll().length` + 잡힌 노드 id | 12개 선택자 1회씩 | 정답 1 · 9 · 2-summary (1)(2) |
| 없는 조합자(`<`·`!`·`:parent`) | `querySelectorAll()` 예외 메시지 | 3개 | 정답 2 |
| 속성 연산자 여섯 + `i` 플래그 | `querySelectorAll().length` | 14개 선택자 1회씩 | 정답 3 · 4 |
| 대소문자 5종 | `querySelectorAll().length` | 8개 선택자 | 정답 5 |
| `s` 플래그 | `querySelectorAll()` 예외 + `cssRules` 대조 | 2경로 | 정답 5 |
| 무효 선택자의 폐기 범위 | 스타일시트 3규칙 주입 후 `cssRules` | 1회 | 정답 6 |
| 중복 ID | `querySelectorAll()` + `getComputedStyle` | 1회 | 정답 10 |
| `[checked]` 대 `:checked` | CDP `Input.dispatchMouseEvent` 클릭 후 `matches()` | 1회(초기·조작 후) | 정답 11 |
| `demo` 블록(속성 연산자) | 래퍼를 씌운 사본을 띄워 `getComputedStyle` + 스크린샷 | 원본 1 + 변형 2 | 2-summary (4) |

**구현 의존 항목** — 버전이 오르면 다시 찍어야 할 것들이다.

| 항목 | 왜 | 다시 찍을 것 |
|---|---|---|
| `s` 플래그가 `SyntaxError` 인 것 | Baseline **limited** — 명세에는 있고 구현이 없다. Chrome 이 구현하면 바뀐다 | 정답 5 의 두 출력 |
| `type` 값이 대소문자 무시로 맞는 것 | **HTML 명세가 정하는 목록**이라 CSS 버전과 무관하지만, 목록은 바뀔 수 있다 | 정답 5 의 `input[type=…]` 두 줄 |
| `cssRules` 의 `selectorText` 표기 | **직렬화 동작**이라 엔진마다·버전마다 문자열이 다를 수 있다 | 정답 6 |
| 조합자·속성 연산자의 매칭 규칙 | **명세 보장** — 버전이 올라도 안 바뀐다 | 다시 찍을 필요 없음 |

**안 돌려 본 것** — XML 문서에서 타입 선택자가 대소문자를 구분하는 것, 선택자 매칭 **성능**(오른쪽에서 왼쪽), `@namespace` 를 쓴 네임스페이스 구분자. 셋 다 이 문서에서 **결론으로 쓰지 않았다.**

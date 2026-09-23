# css/syntax/08 — 기본 선택자·조합자·속성 선택자 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Selectors Level 4](https://drafts.csswg.org/selectors-4/) 의 [§타입·전체 선택자](https://drafts.csswg.org/selectors-4/#type-selectors) · [§속성 선택자](https://drafts.csswg.org/selectors-4/#attribute-selectors) · [§조합자](https://drafts.csswg.org/selectors-4/#combinators) · [§대소문자](https://drafts.csswg.org/selectors-4/#attribute-case). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 매치 수는 **Google Chrome 151.0.7922.173** headless 에서 `document.querySelectorAll(...).length` 로 실제로 센 값이고, 규칙이 살아남았는지는 `document.styleSheets[0].cssRules` 로 확인했다. `demo` 블록 1개와 그 「바꿔 볼 것」도 브라우저에 띄워 확인했다.\
> **WebKit(Safari)은 이 머신에 없다** — Safari 관련 서술은 하지 않았다. **엔진은 Chrome 하나**이므로 크로스 브라우저는 Baseline 데이터로만 접지한다.
> **버전** — CSS 에 언어 버전은 없다. Baseline(2026-09-23 에 `api.webstatus.dev` 조회): 선택자 코어 **widely**(2015-07-29 → 2018-01-29) · 속성 선택자의 `i` 플래그 **widely**(2020-01-15 → 2022-07-15) · **`s` 플래그는 limited** — Firefox 66 만 구현했고 Chrome·Safari·Edge 에는 없다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 숫자는 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**선택자는 「그물」이고 명시도는 「그 그물의 힘」이다. 저울이 둘이다.**

비유 대응은 08\~11 네 주제 끝까지 이것 하나로 고정한다.

| 비유 | 실체 | 무엇으로 확인하나 |
|---|---|---|
| 그물의 **모양** | 어떤 요소가 걸리는가 | `document.querySelectorAll(sel).length` — **셀 수 있다** |
| 그물의 **힘** | 걸린 뒤 그 선언이 이겼는가 | `getComputedStyle(el).color` — **읽어야 안다** |
| 그물을 **못 던진다** | 선택자가 무효라 규칙이 버려졌다 | `document.styleSheets[0].cssRules` — **담겼는지 본다** |

- **「맞는 것을 고르나」와 「이겼나」는 다른 질문이다.**\
  `.a.b.c` 와 `#x` 는 같은 요소를 고를 수 있고(모양이 같다), 그래도 승부는 갈린다(힘이 다르다).
- 08번은 **모양**만 다룬다. 힘의 계산은 [02번](../02-specificity/2-summary.md)이 정본이고, 그 둘이 어긋나는 자리를 [11번](../11-is-where-not/2-summary.md)이 다룬다.
- **CSS 는 에러가 없는 언어다.** 무효한 선택자는 조용히 버려지고, 화면에는 「아무 일도 안 일어난 것」으로만 보인다.\
  그래서 셋째 줄 — `cssRules` 를 읽는 것 — 이 근거가 된다.

```text
   선언 한 줄                 브라우저가 하는 일                내가 볼 수 있는 것
   .wrap > p { color: red }
        |
        +--(1) 파싱 ---------> 선택자가 유효한가?  ------>  cssRules 에 담겼나
        |                         무효면 규칙 통째로 폐기
        +--(2) 매칭 ---------> 어느 노드가 걸리나  ------>  querySelectorAll().length
        |
        +--(3) 캐스케이드 ---> 그 선언이 이겼나    ------>  getComputedStyle()
```

실무에서 이게 터지는 자리는 「**선택자를 고쳤는데 화면이 그대로일 때**」다.\
①에서 죽었는지 ②에서 안 걸렸는지 ③에서 졌는지를 가르지 않으면, 셋 다 아닌 곳을 고치게 된다.

> **선택자(selector)** — 어떤 요소에 규칙을 걸지 고르는 식.\
> 예: `.wrap > p` 는 "`.wrap` 의 **직계 자식**인 `p`"를 고른다.

> **조합자(combinator)** — 선택자 조각을 이어 관계를 만드는 기호.\
> 예: `.wrap > p` 의 `>` 는 "바로 아래 자식"이라는 관계다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 둔다.

1. 조합자 넷(` `·`>`·`+`·`~`)이 **각각 어느 노드를 잡는가** — 같은 트리에서 세어 갈라 보일 수 있는가.
2. 속성 선택자의 연산자 여섯이 **어디서 갈리는가** — 특히 `~=`(낱말)와 `*=`(부분 문자열).
3. 대소문자는 **무엇이 구분하고 무엇이 안 하는가** — 타입·클래스·ID·속성 이름·속성 값이 전부 다르다.

## 예시 데이터 — 이 묶음이 공유하는 것

08\~11 은 전부 「**어느 노드가 왜 잡혔나**」를 세는 주제라, 트리를 눈에 박아 두고 시작한다.\
08 은 아래 두 판을 쓴다. 09·10·11 은 각자의 트리를 그 문서 첫머리에 다시 그린다.

**판 A — 조합자용 트리** (`08-tree.html`)

```text
section.wrap
 ├─ (1) h2.hd          "제목"
 ├─ (2) p.x#P1         "P1"
 ├─ (3) p#P2           "P2"
 ├─ (4) div.inner
 │        └─  p.x#P3   "P3"
 └─ (5) p.x#P4         "P4"

괄호 안 숫자는 .wrap 의 몇 번째 "요소" 자식인지다(텍스트 노드는 안 센다 — 09번).
```

**판 B — 속성 선택자용 링크 넷** (`08-attr.html`)

```text
 id   href                        hreflang    data-tags
 l1   /docs/guide.html            en-US       "alpha beta"
 l2   https://ex.com/a.PDF        en          "alphabet"
 l3   /docs/api.pdf               en-GB       "beta alpha"
 l4   mailto:x@y.z                english     "gamma"

 l2 의 확장자는 대문자 .PDF 이고, l4 의 hreflang 은 en 으로 시작하지만 english 다.
 이 두 개가 이 판의 함정 전부다.
```

## 동작 방식

### (1) 단순 선택자 넷 — 무엇을 이름으로 부르나

**언제 쓰나** — 그물의 가장 작은 조각을 만들 때. 조합자는 이것들을 잇는 접착제일 뿐이다.

```text
   판 A 에 던진 그물            걸린 노드                     개수
   *                          html head meta body
                              wrap hd P1 P2 inner P3 P4        11
   p                          P1 P2 P3 P4                       4
   .x                         P1 P3 P4                          3
   #P1                        P1                                1
   p.x                        P1 P3 P4                          3
```

- **`*` 는 문서의 모든 요소를 잡는다** — `html`·`head`·`meta` 까지다. 11개 중 4개는 내가 안 쓴 것이다.
- **`p.x` 처럼 붙여 쓰면** 「**둘 다**」다. 사이에 공백이 없으면 **같은 한 요소**를 가리킨다.
- `#P1` 은 하나만 잡는다 — 문서에서 ID 가 유일해야 한다는 것은 HTML 의 규칙이지 CSS 의 규칙이 아니다.\
  CSS 는 중복 ID 가 있으면 **전부** 잡는다.\
  *(Chrome 151 headless 실측: `<p id="dup">` 둘을 놓고 `#dup` 을 던지면 2개, `#dup { color: rgb(7,7,7) }` 도 둘 다에 먹었다.)*

비용 — 없다. 다만 `*` 는 「모든 요소」라는 뜻이라 `* { box-sizing: border-box }` 처럼 상속 밖 속성을 전부에 깔 때만 쓴다.

### (2) 조합자 넷 — 같은 트리에서 갈라 세기

**언제 쓰나** — "저 요소 **옆**의", "저 요소 **안**의"를 표현할 때.

```text
       .wrap p   (자손, 공백)        .wrap > p  (자식, >)
   section.wrap                    section.wrap
    ├─ h2                           ├─ h2
    ├─ P1  <=                       ├─ P1  <=
    ├─ P2  <=                       ├─ P2  <=
    ├─ div                          ├─ div
    │   └─ P3  <=  (손자도 잡힌다)   │   └─ P3     (건너뛴다)
    └─ P4  <=                       └─ P4  <=
          4개                              3개
```

```text
       .hd + p  (인접 형제, +)        .hd ~ p  (일반 형제, ~)
   section.wrap                    section.wrap
    ├─ h2.hd  (기준)                ├─ h2.hd  (기준)
    ├─ P1  <=  바로 다음 하나만      ├─ P1  <=
    ├─ P2                           ├─ P2  <=
    ├─ div                          ├─ div
    │   └─ P3                       │   └─ P3     (형제가 아니다)
    └─ P4                           └─ P4  <=
          1개                              3개
```

그림 해설 (한 단계씩):

- **공백(자손)은 깊이를 안 따진다.** `P3` 은 손자인데도 `.wrap p` 에 걸린다(4개).
- **`>`(자식)는 한 칸만 내려간다.** `P3` 이 빠져 3개다.
- **`+`(인접 형제)는 「바로 다음 하나」다.** `h2.hd` 뒤의 `P1` 만(1개).
- **`~`(일반 형제)는 「뒤쪽 형제 전부」다.** `P1`·`P2`·`P4` 셋인데 `P3` 은 아니다 — 부모가 다르면 형제가 아니다(3개).
- `.x + .x` 는 **0개**다. `.x` 는 `P1`·`P3`·`P4` 셋인데 그중 **서로 인접한 쌍이 없다**(`P1` 다음은 `P2`).

*(Chrome 151 headless 실측: `.wrap p` 4 · `.wrap > p` 3 · `.hd + p` 1 · `.hd ~ p` 3 · `.inner + p` 1 · `.x + .x` 0.)*

비용 — 없다. 명시도 관점에서도 **조합자는 `(0,0,0)`** 이다 — `.a .b` 와 `.a > .b` 는 세기가 같다([02번](../02-specificity/2-summary.md)).

### (3) 조합자가 갈 수 없는 방향 — 위와 왼쪽

**언제 쓰나** — "이 자식을 가진 부모"·"이 요소 **앞**의 형제"를 고르고 싶어졌을 때.

```text
           ?  부모로 올라가는 조합자      없다
   +-------+
   | 부모  |  <--- X
   +---+---+
       |
   +---+---+      +-------+      +-------+
   | 앞형제 | <-X- | 기준  | -+-> | 뒷형제 |   -> +  ~  는 있다
   +-------+      +---+---+      +-------+
                      |
                  +---+---+
                  | 자식  |                    -> 공백  >  는 있다
                  +-------+
```

- 네 조합자는 **전부 아래 또는 뒤로만** 간다. 위·앞으로 가는 조합자는 **문법에 없다.**
- 실제로 던져 보면 **문법 오류**다.

```text
  document.querySelectorAll('p < section')
    -> SyntaxError: 'p < section' is not a valid selector.
  document.querySelectorAll('p ! section')
    -> SyntaxError: 'p ! section' is not a valid selector.
  document.querySelectorAll('p:parent')
    -> SyntaxError: 'p:parent' is not a valid selector.
```

- 이 제약을 뚫는 것이 `:has()` 다 — `section:has(> p.x)` 는 실측에서 `.wrap` 하나를 잡았다.\
  정본은 [목록의 **12번 주제**](../12-has-relational-selector/)이고 여기서는 "08 의 조합자로는 못 한다"까지다.
- ★ 이게 **조용한 사고**가 되는 자리는 CSS 파일 안이다. JS 는 예외를 던지지만 **CSS 는 안 던진다** — 아래 (5).

비용 — 없다. 대신 마크업 설계에 부담이 간다. `:has()` 가 없던 시절 "부모에도 클래스를 하나 더 붙인다"가 관례였던 이유다.

### (4) 속성 선택자 — 연산자 여섯이 갈리는 자리

**언제 쓰나** — 클래스를 새로 붙일 수 없는 마크업(폼·링크·외부 위젯)을 고를 때.

```text
   [attr]            그 속성이 "있기만" 하면
   [attr="v"]        값이 정확히 v
   [attr~="v"]       값을 공백으로 쪼갠 "낱말" 중 하나가 v
   [attr|="v"]       값이 v 이거나 v- 로 시작       (언어 태그용)
   [attr^="v"]       값이 v 로 시작
   [attr$="v"]       값이 v 로 끝
   [attr*="v"]       값 아무 데나 v 가 부분 문자열로
```

판 B 에 던져 센 결과다.

| 그물 | 걸린 것 | 개수 | 왜 |
|---|---|---|---|
| `[hreflang]` | l1 l2 l3 l4 | 4 | 있기만 하면 |
| `[hreflang="en"]` | l2 | 1 | 정확히 `en` 인 것만 |
| `[hreflang\|="en"]` | l1 l2 l3 | 3 | `en` · `en-US` · `en-GB` — **`english` 는 아니다** |
| `[data-tags~="alpha"]` | l1 l3 | 2 | 낱말이 정확히 `alpha` 인 것 |
| `[data-tags*="alpha"]` | l1 l2 l3 | 3 | **`alphabet` 까지 잡힌다** |
| `[data-tags^="alpha"]` | l1 l2 | 2 | `alpha beta` · `alphabet` |
| `[data-tags$="alpha"]` | l3 | 1 | `beta alpha` |
| `[href^="/docs/"]` | l1 l3 | 2 | 경로 앞부분 |
| `[href$=".pdf"]` | l3 | 1 | **대문자 `.PDF` 는 안 잡힌다** |
| `[href*="docs"]` | l1 l3 | 2 | 어디에 있든 |

★ **`~=` 와 `*=` 가 갈리는 자리가 이 절의 과녁이다.**

```text
   data-tags="alpha beta"      data-tags="alphabet"
        |                            |
   공백으로 쪼갠다                 쪼갤 공백이 없다
   ["alpha", "beta"]              ["alphabet"]
        |                            |
   ~="alpha"  ->  걸린다          ~="alpha"  ->  안 걸린다
   *="alpha"  ->  걸린다          *="alpha"  ->  걸린다   <-- 여기가 갈린다
```

```html demo
<b data-tags="alpha beta">alpha beta</b>
<b data-tags="alphabet">alphabet</b>
<style>
  b { display: block; padding: 4px; margin: 4px; font: 16px system-ui; }
  [data-tags~="alpha"] { background: #dbeafe; }
  [data-tags*="alpha"] { outline: 2px solid #b91c1c; }
</style>
```

> **보이는 것** — 두 줄 다 **빨간 2px 테두리**가 생긴다(`*=` 는 둘 다 잡는다). 그런데 **파란 배경은 첫 줄에만** 있다 — `~=` 는 공백으로 나뉜 낱말이 정확히 `alpha` 인 것만 잡으므로 `alphabet` 은 빠진다. 조작은 없다, 뜨자마자 그 상태다.\
> **바꿔 볼 것** — `~=` → `|=` 로 바꾸면 **파란 배경이 둘 다 사라진다**(값이 `alpha` 도 `alpha-…` 도 아니다) · `~=` → `^=` 로 바꾸면 **파란 배경이 둘 다 생긴다**

*(Chrome 151 headless 실측: 원본 배경 `rgb(219, 234, 254)` / `rgba(0, 0, 0, 0)`, `|=` 판 둘 다 `rgba(0, 0, 0, 0)`, `^=` 판 둘 다 `rgb(219, 234, 254)`. 테두리는 세 판 모두 양쪽 다 `rgb(185, 28, 28) 2px solid`.)*

경계 두 가지도 던져서 확인했다.

```text
  [data-tags~="alpha beta"]   ->  0개   값에 공백이 들어가면 ~= 는 절대 안 맞는다
  [data-tags~=""]             ->  0개   빈 문자열도 절대 안 맞는다
```

비용 — 명시도는 **B 자리**(클래스와 같은 급)다. `[id="nav"]` 가 `#nav` 보다 약한 이유가 그것이다([02번](../02-specificity/2-summary.md)).

### (5) 대소문자 — 다섯 군데가 전부 다르다

**언제 쓰나** — "분명히 맞게 썼는데 안 잡힌다"를 진단할 때. 여기가 제일 많이 틀린다.

```text
   HTML 문서에서                       실측 (Chrome 151)
   ┌──────────────────────┬──────────┬───────────────────────────────┐
   │ 타입 선택자 div/DIV   │ 무시     │ DIV -> 2개,  div -> 2개 (같다) │
   │ 클래스 .CapCase      │ 구분     │ .capcase -> 0개                │
   │ ID #Mix              │ 구분     │ #mix -> 0개                    │
   │ 속성 "이름" data-K   │ 무시     │ [data-k="V"] -> 1개 (걸린다)   │
   │ 속성 "값"  "V"       │ 구분     │ [data-k="v"] -> 0개            │
   └──────────────────────┴──────────┴───────────────────────────────┘
```

- **그런데 값에도 예외가 있다.** HTML 이 "이 속성의 값은 대소문자를 무시하고 맞춘다"고 지정한 것들이 있다.

```text
  <input id="i1" type="CHECKBOX">
  <input id="i2" type="checkbox">

  input[type="checkbox"]   ->  2개   i1, i2
  input[type="CHECKBOX"]   ->  2개   i1, i2      <-- 둘 다 잡힌다
```

- `i` 플래그는 **내가 무시를 강제**한다 — `[data-k="v" i]` 는 `data-K="V"` 를 잡았다(1개).
- `s` 플래그는 **내가 구분을 강제**한다. **그런데 Chrome 151 에는 없다.**

```text
  document.querySelectorAll('input[type="CHECKBOX" s]')
    -> SyntaxError: 'input[type="CHECKBOX" s]' is not a valid selector.

  스타일시트에 세 규칙을 넣고 cssRules 를 읽었다
    input[type="CHECKBOX" s] { outline: 2px solid red }    <- 담기지 않았다
    input[type="checkbox"]   { outline-offset: 3px }       <- 담겼다
    [data-k="v" i]           { color: rgb(1,2,3) }         <- 담겼다

  남은 규칙: ['input[type="checkbox"]', '[data-k="v" i]']
```

- **에러 메시지도 콘솔 경고도 없다.** 규칙이 목록에서 그냥 사라진다 — CSS 에 에러가 없다는 말의 뜻이 이것이다.
- Baseline 도 같은 말을 한다 — `s` 플래그는 **limited**, Firefox 66 만 구현했다(2026-09-23 조회).

비용 — `i` 플래그는 그냥 쓰면 된다(widely). `s` 는 오늘 쓸 문법이 아니다.

### (6) 무효한 선택자 하나가 어디까지 죽이나

**언제 쓰나** — 오타·미지원 문법을 섞었을 때 피해 범위를 가늠할 때.

```text
   .x, p < section { color: red }     <- 목록에 무효한 것이 하나 섞였다
   p ! section     { color: blue }
   .x              { color: green }

   cssRules 에 남은 것:  ['.x']
```

- **선택자 목록(쉼표)은 전부 아니면 전무다.** `.x` 는 멀쩡한데 `p < section` 하나 때문에 **그 규칙이 통째로** 버려졌다.
- 그래서 마지막에 따로 쓴 `.x` 규칙만 살아남았다.
- 이 규칙을 **한 인자만 죽게 바꾸는 것**이 `:is()` 다 — [11번 주제](../11-is-where-not/2-summary.md)의 과녁이다.
- 파서가 무엇을 어디까지 버리는가의 정본은 [목록의 **07번 주제**](../07-syntax-and-error-recovery/)(CSS 구문과 오류 복구)다.

비용 — 없다. 대신 **진단이 어렵다.** 새 문법을 목록에 섞을 때는 규칙을 쪼개 두는 편이 안전하다.

## 문법 — 어디서 헷갈리나

CSS 는 문법 표면이 얇아서 「형태」보다 **헷갈리는 자리**를 적는 것이 값이 있다.

### 형태

```css
/* 붙여 쓰면 같은 한 요소 */
a.btn[href^="/"]:hover   { }

/* 띄우면 조상-자손 관계 */
.card  .title            { }

/* 쉼표는 "또는" — 서로 독립된 선택자들이다 */
h1, h2, h3               { }
```

### 헷갈리는 자리

- **공백이 조합자다.** `.a .b`(자손)와 `.a.b`(둘 다 가진 하나)는 **완전히 다르다.**
- **`>` `+` `~` 앞뒤 공백은 장식이다.** `.a>.b` 와 `.a > .b` 는 같다.
- **`~` 는 두 군데에 나온다.** 조합자 `a ~ b`(일반 형제)와 속성 연산자 `[x~="v"]`(낱말)은 다른 것이다.
- **`*` 는 조합자와 같이 쓸 수 있다.** `section > * > p` 는 "한 칸 건너뛴 손자 `p`" 하나(실측 1개)다.
- **속성 값의 따옴표는 대개 생략 가능하지만** `[href$=".pdf"]` 처럼 점·슬래시가 들어가면 **반드시** 따옴표를 쓴다.
- **플래그는 닫는 대괄호 안, 값 뒤에 공백을 두고** 쓴다 — `[href$=".pdf" i]`.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 여섯 다 **에러 없이 조용히 어긋난다.**

### 1. `~=` 를 쓸 자리에 `*=` 를 쓴다

```css
[class*="btn"] { }   /* btn-group, subtle-button, btnx 까지 전부 */
[class~="btn"] { }   /* class 목록에 낱말 btn 이 있는 것만 */
```

실측에서 `[data-tags*="alpha"]` 는 `alphabet` 을 잡았고 `[data-tags~="alpha"]` 는 안 잡았다.\
**`class` 를 속성 선택자로 고를 때 원하는 것은 거의 항상 `~=` 다**(그리고 그건 그냥 `.btn` 이다).

### 2. `|=` 가 접두사 매칭이라고 생각한다

```css
[hreflang|="en"] { }   /* en, en-US, en-GB  —  english 는 아니다 */
[hreflang^="en"] { }   /* english 도 잡는다 */
```

`|=` 는 **`-` 로 끊기는 경계**를 본다. 언어 태그 전용 연산자이고, 일반 접두사는 `^=` 다.

### 3. 대소문자가 어디서 구분되는지 뒤섞는다

```text
  .CapCase  에 .capcase 로 던지면 0개     (클래스는 구분)
  <DIV>     에 div      로 던지면 잡힌다  (타입은 무시)
  data-K="V" 에 [data-k="V"] 는 잡힌다   (이름은 무시)
             에 [data-k="v"] 는 0개      (값은 구분)
             단 type 같은 일부 HTML 속성은 값도 무시된다
```

**「HTML 이라 대소문자를 안 가린다」는 절반만 맞다.**

### 4. `s` 플래그를 「쓸 수 있는 문법」으로 안다

Chrome 151 에서는 **선택자 자체가 무효**라 규칙이 통째로 버려진다(위 (5) 의 `cssRules` 출력).\
Baseline 도 **limited**(Firefox 만)다. 값 구분이 필요하면 **속성 값을 마크업 쪽에서 정규화**한다.

### 5. `+` 를 "다음 요소"로, `~` 를 "모든 형제"로 외운다

```text
  .hd + p   ->  바로 다음 형제 "하나"  —  그것이 p 가 아니면 0개
  .hd ~ p   ->  "뒤쪽" 형제만  —  앞쪽 형제는 절대 안 잡힌다
```

둘 다 **뒤로만** 간다. 실측에서 `.hd ~ p` 는 3개였고 거기에 `P3`(조카)은 없다.

### 6. 「선택자를 고쳤는데 그대로다」를 한 가지 원인으로 본다

```text
  증상: 화면이 안 바뀐다
     ├─ (1) 규칙이 cssRules 에 없다        -> 선택자가 무효 (이 주제 (5)(6), 07번)
     ├─ (2) 규칙은 있는데 매치가 0개다      -> 그물 모양이 틀렸다 (이 주제)
     └─ (3) 매치는 되는데 졌다             -> 명시도·캐스케이드 (01·02번)
```

★ **셋을 가르는 데 드는 비용은 각각 한 줄이다** — `cssRules` · `querySelectorAll().length` · `getComputedStyle`.\
가르지 않고 고치면 **아무 데나 `!important` 를 붙이는 습관**으로 끝난다.

## 구현 세부사항 대 언어 보장

| 것 | 성격 | 근거 |
|---|---|---|
| 조합자 넷과 속성 연산자 여섯 | **명세 보장** | Selectors 4 §attribute-selectors · §combinators |
| 명시도에서 조합자가 0 인 것 | **명세 보장** | Selectors 4 §specificity ([02번](../02-specificity/2-summary.md)) |
| HTML 에서 타입 선택자가 대소문자 무시 | **HTML 문서에 한정된 보장** | XML 문서에서는 구분된다(이 머신에서 미실행) |
| `type` 값이 대소문자 무시로 맞는 것 | **HTML 명세가 정하는 목록** — CSS 규칙이 아니다 | 실측으로 Chrome 151 이 그렇다는 것만 확인 |
| `s` 플래그가 안 되는 것 | **구현 현황** — 명세에는 있다 | Baseline limited(Firefox 66) · Chrome 151 에서 SyntaxError |
| 무효 선택자가 버려지는 **범위** | **명세 보장**(목록 전체 폐기) | [목록의 **07번 주제**](../07-syntax-and-error-recovery/)가 정본 |

★ **「Chrome 에서 안 된다」와 「명세에 없다」를 섞지 않는다.** `s` 플래그는 명세에 있고 구현이 없는 쪽이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 컴포넌트 내부 요소 고르기 | 클래스 하나 | 자손 사슬 `.a .b .c` |
| 마크업을 못 고치는 위젯 | 속성 선택자 `[data-role="tab"]` | ID 선택자(명시도가 튄다) |
| 언어별 스타일 | `[lang\|="en"]` | `[lang^="en"]` |
| `class` 안의 낱말 하나 | `.btn` (또는 `[class~="btn"]`) | `[class*="btn"]` |
| 확장자별 아이콘 | `[href$=".pdf" i]` | `[href$=".pdf"]` 단독 |
| ID 가 이미 있는데 세기는 낮추고 싶다 | `[id="nav"]` | `#nav` |
| "이 자식을 가진 부모" | `:has()` ([목록의 **12번 주제**](../12-has-relational-selector/)) | 조합자로 시도 — **문법에 없다** |
| 리셋·기본값 | `:where(...)` (목록의 [11번](../11-is-where-not/2-summary.md)) | `*` 에 전부 깔기 |

판단 규칙 두 줄.

- **그물은 좁게, 짧게.** 자손 사슬은 마크업 구조에 스타일을 못박는다 — 구조가 바뀌면 조용히 안 걸린다.
- **안 걸릴 때는 세어 보라.** `querySelectorAll(sel).length` 를 한 번 찍는 것이 추측 열 번보다 싸다.

## 핵심 문장

- 선택자는 **그물 모양**을 정하고 명시도는 **그 그물의 힘**을 정한다 — 셀 수 있는 것과 읽어야 아는 것이 다르다.
- 조합자 넷은 **전부 아래 또는 뒤로만** 간다. 부모·앞형제로 가는 조합자는 문법에 없고, 던지면 `SyntaxError` 다.
- `~=` 는 **공백으로 쪼갠 낱말**, `*=` 는 **부분 문자열** — `alphabet` 하나가 둘을 가른다.
- `|=` 는 접두사가 아니라 **`-` 경계** 매칭이다. `english` 는 `[hreflang|="en"]` 에 안 걸린다.
- 대소문자는 **타입·속성 이름은 무시, 클래스·ID·속성 값은 구분** — 단 HTML 이 지정한 일부 속성 값(`type` 등)은 무시된다.
- `i` 플래그는 widely 이고 **`s` 플래그는 limited** — Chrome 151 에서는 선택자가 무효가 되어 **규칙이 통째로 버려진다.**
- 선택자 목록(쉼표)에 무효한 것이 **하나** 섞이면 **규칙 전체**가 버려진다. 이것을 인자 하나만 버리게 바꾸는 것이 `:is()` 다.

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 08번) · 「버전·지원 기준」의 Baseline 표
- [`../02-specificity/2-summary.md`](../02-specificity/2-summary.md) — **명시도 계산의 정본.** 여기서 만든 부품들이 `(A, B, C)` 중 어디에 들어가는지는 전부 거기다. **여기는 「무엇이 걸리나」까지, 거기는 「그래서 이겼나」부터.**
- [`../01-cascade-and-priority/2-summary.md`](../01-cascade-and-priority/2-summary.md) — 명시도가 동점일 때·명시도보다 위 단계에서 갈릴 때
- [`../09-structural-pseudo-classes/2-summary.md`](../09-structural-pseudo-classes/2-summary.md) — 같은 트리에서 **위치로** 고르는 의사 클래스. 여기는 이름·관계까지, 거기는 순번부터
- [`../10-state-and-form-pseudo-classes/2-summary.md`](../10-state-and-form-pseudo-classes/2-summary.md) — **상태로** 고르는 의사 클래스. 여기는 정적인 그물, 거기는 입력에 따라 켜졌다 꺼지는 그물
- [`../11-is-where-not/2-summary.md`](../11-is-where-not/2-summary.md) — 선택자를 **인자로 담는** 의사 클래스와 그 명시도·관대함
- [목록의 **07번 주제**](../07-syntax-and-error-recovery/)(CSS 구문과 오류 복구) — **무효한 것을 어디까지 버리나의 정본.** 여기서는 선택자 목록 단위까지만 다뤘다
- [목록의 **12번 주제**](../12-has-relational-selector/)(`:has()`) — 조합자로 못 가는 위·앞 방향을 여는 것
- [목록의 **13번 주제**](../13-pseudo-elements-and-generated-content/)(의사 요소) — `::before` 등은 요소를 고르는 게 아니라 **없던 상자를 만든다**
- [목록의 **14번 주제**](../14-css-nesting/)(중첩) — `&` 로 조합자를 중첩해 쓰는 형태
- [`reference/render-rules.md`](../../../../../../reference/render-rules.md) — 이 문서의 `demo` 블록 규칙

## 용어 풀이

- **선택자(selector)** — 어떤 요소에 규칙을 걸지 고르는 식.
- **단순 선택자(simple selector)** — 더 못 쪼개는 조각. 타입(`p`) · 전체(`*`) · 클래스(`.x`) · ID(`#x`) · 속성(`[a]`) · 의사 클래스(`:hover`).
- **복합 선택자(compound selector)** — 공백 없이 붙인 단순 선택자 묶음. `p.x[href]` — **같은 한 요소**를 가리킨다.
- **복잡 선택자(complex selector)** — 조합자로 이은 것. `.wrap > p`.
- **선택자 목록(selector list)** — 쉼표로 나열한 것. 하나가 무효면 **전체가 버려진다.**
- **조합자(combinator)** — 공백(자손) · `>`(자식) · `+`(인접 형제) · `~`(일반 형제). 명시도 기여는 0.
- **자손(descendant)** — 아래 어느 깊이든. **자식(child)** — 바로 한 칸 아래.
- **인접 형제(next-sibling)** — 바로 다음 형제 하나. **일반 형제(subsequent-sibling)** — 뒤쪽 형제 전부.
- **속성 선택자(attribute selector)** — 속성으로 고르는 것. 명시도는 **B 자리**(클래스와 같은 급).
- **`i` 플래그** — 속성 값을 대소문자 무시로 맞춘다. Baseline widely.
- **`s` 플래그** — 속성 값을 대소문자 구분으로 강제한다. Baseline **limited** — Chrome 151 에서 무효.
- **무효 선택자(invalid selector)** — 파서가 이해 못 한 선택자. CSS 는 에러를 안 던지고 **조용히 버린다.**
- **`cssRules`** — 스타일시트에 실제로 담긴 규칙 목록. 규칙이 버려졌는지 확인하는 유일한 관측 창.

## 더 들어가면

- **`*` 가 느리다는 옛말은 오늘 기준이 아니다.** 현대 엔진은 선택자를 **오른쪽에서 왼쪽으로** 매칭하므로 비용은 맨 오른쪽 조각이 지배한다. *(이 문서에서 성능은 측정하지 않았다 — 「안 재 봤다」.)*
- **`:scope`** 는 `element.querySelectorAll(':scope > p')` 처럼 **기준점을 그 요소로** 만든다. CSS 파일 안에서는 `@scope`([목록의 **06번 주제**](../06-scope/))가 그 자리를 맡는다.
- **`|` 하나짜리 네임스페이스 구분자**(`svg|circle`)는 `@namespace` 를 선언해야 쓸 수 있다. HTML 문서만 다루면 만날 일이 거의 없다.
- 속성 선택자로 **폼 상태**를 고르려 하면 대개 틀린다 — `[checked]` 는 **HTML 속성**(초기값)이고, 사용자가 켠 상태는 `:checked`(프로퍼티)다.\
  *(Chrome 151 headless 실측: `checked` 를 달고 뜬 체크박스를 사용자가 끄면 `[checked]` 는 **계속 맞고** `:checked` 만 꺼진다 — [10번 주제](../10-state-and-form-pseudo-classes/2-summary.md)에 전체 출력이 있다.)*

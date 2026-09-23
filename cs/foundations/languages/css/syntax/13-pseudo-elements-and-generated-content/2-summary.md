# css/syntax/13 — 의사 요소와 생성 콘텐츠: `::before`/`::after`/`::marker`/`::selection` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [CSS Pseudo-Elements Level 4](https://drafts.csswg.org/css-pseudo-4/) · [CSS Lists Level 3 §3.1.1 Properties Applying to `::marker`](https://drafts.csswg.org/css-lists-3/#marker-properties) · [Selectors Level 4 §3.6.3 Pseudo-classing Pseudo-elements](https://drafts.csswg.org/selectors-4/#pseudo-element-states) · [같은 문서 §16 Grammar](https://drafts.csswg.org/selectors-4/#grammar)(단일 콜론 레거시 조항). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 계산값·「담김/버림」 판정·접근성 트리는 **Google Chrome 151.0.7922.173** headless 에서 실제로 돌렸다.\
> 근거를 **세 층**으로 나눠 뽑았다 — ① `cssRules` 로 **규칙이 담겼나** ② `getComputedStyle(el, '::before')` 로 **무엇으로 계산됐나**(★ 두 번째 인자가 있다) ③ `offsetWidth`·스크린샷으로 **상자가 실제로 생겼나**.\
> 접근성 트리는 CDP 의 `Accessibility.getFullAXTree` 로 덤프했다.\
> **엔진은 Chrome 하나다.** Firefox 155.0.1 은 이 환경에서 headless 스크린샷이 산출되지 않으므로 **「두 엔진에서 확인했다」고 적지 않았다.** 크로스 브라우저는 Baseline 으로만 접지한다.
> **버전** — CSS 에 언어 버전은 없다. 2026-09-23 에 `api.webstatus.dev` 를 직접 조회한 Baseline 은 아래 「구현 세부사항 대 언어 보장」의 표에 있다. **`::marker` 와 `::selection` 이 `limited` 로 나온다** — 그 이유도 거기 적었다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 숫자는 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**의사 요소는 「대본에만 있는 배우」다. 대본 한 줄(`content`)을 주지 않으면 무대에 서지 않는다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 배우 | **의사 요소** — HTML 어디에도 없는 상자 |
| 대본 한 줄 | `content` 선언 |
| 무대에 선다 | 상자가 실제로 만들어진다 |
| 의상·조명 지시서 | `width`·`background` 같은 다른 선언 |
| 지시서는 접수됐는데 배우가 없다 | ★ `getComputedStyle` 은 값을 돌려주는데 **상자는 없다** |
| 무대에 설 수 있는 자리 | 선택자의 **맨 끝** 한 곳뿐 |
| 관객 명부 | **접근성 트리** — 배우가 거기 오르기도 하고 안 오르기도 한다 |

```text
   <p class="tag">중요</p>

   HTML 에는 이것뿐이다.          CSS 가 상자를 둘 더 만들 수 있다.

   ┌──────────────────────────────────────┐
   │  p.tag                               │
   │  ┌────────┐ ┌────────┐ ┌──────────┐  │
   │  │::before│ │ "중요" │ │ ::after  │  │
   │  └────────┘ └────────┘ └──────────┘  │
   │     ^ CSS 가 만든다      ^ CSS 가 만든다│
   └──────────────────────────────────────┘

   ★ 둘 다 content 를 선언했을 때만 존재한다
   ★ document.querySelector 로는 절대 잡히지 않는다 (DOM 에 없다)
```

- 「의사(pseudo)」라는 이름이 붙은 이유가 그대로다 — **문서 트리에 없는 것을 있는 척 가리킨다.**
- 그래서 **존재 자체가 CSS 선언의 결과**다. 이 성질이 다른 주제까지 흔든다 —\
  `:has()` 안에 의사 요소를 못 넣는 것도 여기서 온다(순환이 생긴다. [12번 주제](../12-has-relational-selector/2-summary.md)).
- 콜론 개수는 **의사 클래스(`:`)와 의사 요소(`::`)를 가르는 표시**다. 명시도 자리도 다르다.

실무에서 이게 터지는 자리는 **아이콘·배지·인용부호를 CSS 로 붙일 때**다.\
「왜 아이콘이 안 나오지」의 절반이 `content` 를 안 쓴 것이고, 나머지 절반은 **`::before` 를 선택자 중간에 쓴 것**이다.

> **의사 요소(pseudo-element)** — 문서 트리에 없는 가상의 상자를 가리키는 `::` 로 시작하는 선택자.\
> 예: `::before`(요소 안 맨 앞에 끼우는 상자) · `::marker`(목록 항목의 번호·점).

> **생성 콘텐츠(generated content)** — HTML 에 없는데 CSS 의 `content` 가 만들어 낸 내용.\
> 예: `.req::after { content: " *" }` 가 만드는 별표.

> **originating element(기원 요소)** — 의사 요소가 붙는 진짜 요소.\
> 예: `p::before` 의 기원 요소는 `p` 다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 의사 요소는 **언제 존재하고 언제 존재하지 않는가** — 그리고 그것을 어떻게 확인하는가.
2. 의사 요소는 **선택자의 어디에 쓸 수 있고, 명시도의 어느 자리에 들어가는가.**
3. 「**적용 가능한 속성이 제한된다**」가 실제로 무슨 일인가 — 선택자가 버려지는 것과 어떻게 다른가.

## 동작 방식

### (1) `content` 가 없으면 상자도 없다

**언제 쓰나** — 「`::before` 에 스타일을 다 줬는데 아무것도 안 보인다」일 때. 이 주제에서 가장 자주 나는 사고다.

```text
   선언                          계산                     렌더
   ┌─────────────────────┐      ┌──────────────────┐     ┌────────────┐
   │ .bar::before {      │      │ content: none    │     │            │
   │   width: 50px;      │ ───> │ width:   50px    │ ──> │  상자 없음 │
   │   height: 10px;     │      │ display: inline- │     │            │
   │   background: blue; │      │          block   │     │            │
   │ }                   │      └──────────────────┘     └────────────┘
   └─────────────────────┘        ^ 값은 다 있다            ^ 그런데 없다

   ★ 계산값이 나온다고 상자가 있는 게 아니다
```

실측이다 — 같은 선언에 `content` 만 바꿔 넣고 기원 요소의 `offsetWidth` 를 쟀다.\
기원 요소는 글자 하나(`A`)뿐인 `<span>` 이라 `::before` 가 붙으면 폭이 그대로 늘어난다.

```css
span::before { width: 50px; height: 10px; display: inline-block; background: #00f; }
```

| `content` 선언 | 계산된 `content` | 계산된 `width` | 기원 요소 `offsetWidth` | 상자가 생겼나 |
|---|---|---|---|---|
| (선언 없음) | `none` | `50px` | **8px** | ✘ |
| `content: ""` | `""` | `50px` | **58px** | ✔ |
| `content: none` | `none` | `50px` | **8px** | ✘ |
| `content: normal` | `none` | `50px` | **8px** | ✘ |

그림 해설 (한 단계씩):

- ★ **네 줄 전부 `width` 가 `50px` 로 계산된다.** `getComputedStyle` 은 상자가 없어도 값을 돌려준다 — **존재의 근거가 아니다.**
- **`content` 가 `none` 으로 계산되면 상자가 만들어지지 않는다.** 선언을 안 하면 초깃값이 `normal` 이고, `::before`/`::after` 에서 `normal` 은 **`none` 으로 계산된다.**
- **`content: ""` 는 다르다.** 빈 문자열이지만 `none` 이 아니므로 **상자는 생긴다.** 아이콘·구분선을 그릴 때 쓰는 형태가 이것이다.
- 확인 수단은 **계산값이 아니라 치수**다 — `offsetWidth`·`getBoundingClientRect()`·스크린샷.

비용 — 없다. 다만 **진단 비용은 개발자가 낸다.** 계산값만 보고 「선언은 들어갔는데」로 멈추면 원인을 못 찾는다.

```html demo
<p class="bar">content 를 선언하지 않았다</p>
<p class="bar has">content: "" 를 선언했다</p>
<style>
  p { font: 16px/1.6 system-ui, sans-serif; margin: 8px; }
  .bar::before { display: inline-block; width: 40px; height: 12px;
                 margin-right: 6px; background: #2563eb; }
  .has::before { content: ""; }
</style>
```

> **보이는 것** — 조작 없이 처음부터 이렇게 보인다. **아래 줄에만** 글자 앞에 가로 40px · 세로 12px 짜리 파란 막대가 붙는다. 두 줄이 `::before` 에 **똑같은 선언**(`width`·`height`·`background`)을 받았는데도 그렇다 — `content` 를 선언한 아래 줄에서만 상자가 생기기 때문이다. 위 줄에는 아무것도 없다.\
> **바꿔 볼 것** — `.has::before` 의 `content: ""` → `none`(막대가 **사라진다**) · → `normal`(**똑같이 사라진다** — `normal` 은 `none` 으로 계산된다) · `.has::before` 를 `.bar::before` 로(**두 줄 다** 막대가 생긴다)

*(Chrome 151 headless 실측: 스크린샷 320×100 에서 `rgb(37, 99, 235)` 픽셀 480개가 **둘째 줄에만** 있었다. `content: none`·`normal` 로 바꾼 판은 계산된 `content` 가 둘 다 `none` 이 됐다.)*

### (2) `content` 에 무엇을 넣을 수 있나

**언제 쓰나** — 생성 콘텐츠를 실제로 쓸 때.

```text
   content 가 받는 것

   "문자열"          ->  그 글자
   attr(속성명)      ->  그 속성의 값 (계산 시점에 풀린다)
   counter(이름)     ->  번호 (렌더 시점에 풀린다)
   url(...)          ->  이미지
   "글자" / "대체"   ->  글자 + 접근성용 대체 텍스트
   none              ->  상자를 만들지 않는다
   normal            ->  ::before/::after 에서는 none 으로 계산된다
```

실측 (Chrome 151 headless, `getComputedStyle(el, '::before').content`).

| 선언 | 계산된 값 | 메모 |
|---|---|---|
| `content: "[별]"` | `"[별]"` | 따옴표까지 포함해 돌려준다 |
| `content: attr(data-tag)` | `"NEW"` | ★ **속성 값이 계산 시점에 풀려 있다** |
| `content: none` | `none` | |
| `content: normal` | `none` | ★ `::before` 에서는 둘이 같다 |
| `content: url("data:image/gif;…")` | `url("data:image/gif;…")` | 이미지 |
| `content: "★" / "별표"` | `"★" / "별표"` | ★ **대체 텍스트는 계산값에 남는다** |
| `content: ""` | `""` | 상자는 생긴다 |
| `li::marker { content: "→ " }` | `"→ "` | 목록 표지도 `content` 로 바꾼다 |
| `content: "[" counter(item) "] "` | `"[" counter(item) "] "` | ★ **풀리지 않은 채로 남는다** |

그림 해설:

- **`attr()` 과 `counter()` 는 푸는 시점이 다르다.** `attr()` 은 계산값에 이미 풀려 있고, `counter()` 는 **함수 형태 그대로** 남는다. 카운터는 **문서 순서를 따라가며 렌더 시점에** 정해지기 때문이다.
- `counter()` 가 실제로 번호를 만드는 것은 스크린샷으로 확인했다 — `[1] 가` / `[2] 나` / `[3] 다` 로 나왔다.\
  ★ **카운터 자체는 이 목록의 다른 자리다.** 여기서는 **존재만 보이고 넘긴다.**
- **`/ "대체 텍스트"` 는 접근성용이다.** (8)절에서 접근성 트리로 확인한다.
- 의사 요소 없이 `getComputedStyle(el)` 만 부르면 `content` 는 **`normal`** 이다 — 기원 요소 자신의 값이지 의사 요소의 값이 아니다. **두 번째 인자를 빼면 다른 것을 읽는다.**

비용 — `attr()` 은 속성이 바뀌면 다시 계산된다. `counter()` 는 앞선 형제들을 세야 하므로 목록이 길면 그만큼 일이 는다. **둘 다 수치로 재지 않았다.**

### (3) 의사 요소는 선택자의 맨 끝에만 온다

**언제 쓰나** — `::before` 뒤에 뭔가를 더 붙이고 싶어질 때마다.

명세의 규칙은 한 줄이다 — **의사 요소는 복합 선택자의 맨 끝에만 유효하다.** 예외는 명세가 건별로 정한 것뿐이다.

```text
   p::before          ✔  맨 끝이다
   p::before:hover    ?  명세는 허용, Chrome 151 은 버린다  (아래 표)
   div::before span   ✘  뒤에 다른 요소가 왔다
   p::before.cls      ✘  뒤에 클래스가 왔다
   p::before::after   ✘  의사 요소를 둘 겹쳤다
```

던져서 확인한 전수 결과다 (Chrome 151 headless, `cssRules` 에 담겼나).

| 던진 것 | 결과 | `selectorText` |
|---|---|---|
| `p::before` | 담김 | `p::before` |
| `p:before` | 담김 | ★ `p::before` — **콜론이 둘로 바뀌어 나온다** |
| `p:after` / `p:first-line` / `p:first-letter` | 담김 | 각각 `::after`·`::first-line`·`::first-letter` |
| `p::marker` · `p::selection` · `p::placeholder` · `p::backdrop` | 담김 | 그대로 |
| `div::before span` | **버림** | — |
| `div::before > span` / `div::before + span` | **버림** | — |
| `p::before.cls` / `p::before#id` / `p::before[x]` | **버림** | — |
| `p::before::before` / `p::before::after` | **버림** | — |
| `p::first-line::before` / `p::first-letter::before` / `p::marker::before` | **버림** | — |
| `p::before::marker` / `li::before::marker` | **담김** | 그대로 — ★ 명세가 따로 허용한 조합 |
| `:not(p::before)` | **버림** | — |
| `:is(p::before)` / `:where(p::before)` | **담김** | ★ `:is()` / `:where()` — **안이 비었다** |
| `p:is(::before)` | **담김** | ★ `p:is()` — 역시 비었다 |
| `p::bogus-xyz` / `p:bogus-xyz` | **버림** | — |

그림 해설:

- ★ **`:is()`·`:where()` 안에 넣으면 규칙은 살고 내용만 증발한다.** 관용적 선택자 목록이 무효한 항목을 조용히 빼기 때문이다.\
  같은 함정을 `:has()` 쪽에서도 봤다([12번 주제](../12-has-relational-selector/2-summary.md) (4)절) — **관용적인 것이 관용적이지 않은 것을 삼킨다.**
- **`:not()` 은 관용적이지 않아서 규칙째 버려진다.** 같은 자리에 넣어도 결과가 반대다.
- `::before::marker` 가 담기는 것은 명세가 **하위 의사 요소**로 따로 허용했기 때문이다(css-pseudo-4 의 변경 이력에 그 조항이 있다).

#### 의사 요소 뒤의 의사 클래스 — 명세와 Chrome 151 이 갈린다

명세는 「**어떤 의사 요소든 논리 조합 의사 클래스와 사용자 동작 의사 클래스가 뒤따를 수 있다**」고 정한다.\
그리고 `::first-line:hover` 는 첫 줄에 마우스를 올렸을 때 맞는다고 **예까지 들어 놓았다.**

8종 × 6종 = **48 조합을 전부 던졌다.** 결과는 의사 요소 종류와 무관하게 셋으로 갈렸다.

| 뒤에 붙인 것 | Chrome 151 | 명세 |
|---|---|---|
| `:hover` · `:active` · `:focus` | **8종 전부 버림** | ★ 사용자 동작 의사 클래스는 **허용**한다고 적혀 있다 |
| `:is(.x)` · `:where(.x)` | 8종 전부 담김 — 단 **인자가 비워진다**(`:is()`) | 허용. 인자에 위치 제약이 전달되고, 관용적이라 조용히 빠진다 |
| `:not(.x)` | **8종 전부 버림** | 허용하지만 `:not()` 은 관용적이 아니라 무효 인자가 전체를 죽인다 |

- 첫 줄이 **명세와 구현이 갈린 자리**다. 「`::first-line:hover` 를 쓰면 된다」고 적힌 문서를 보고 쓰면 **Chrome 151 에서는 규칙째 사라진다.**
- 여기서 적을 수 있는 것은 **「Chrome 151 에서는 안 된다」까지**다. 다른 엔진은 이 머신에서 확인할 수 없다.

비용 — 없다. 단, **버려진 규칙은 개발자 도구에도 안 보인다.**

### (4) 콜론 하나와 둘

**언제 쓰나** — 남의 코드에서 `:before` 를 봤을 때.

```text
   CSS2 시절                     CSS2.1 이후
   :before  :after               ::before  ::after
   :first-line :first-letter     ::first-line ::first-letter
        ^                             ^
   의사 클래스와 구분이 안 됐다     콜론 둘로 갈라 놓았다

   ★ 이미 쓰인 시트를 깨뜨릴 수 없으므로
     옛 표기를 「레거시 별칭」으로 남겼다
```

- 명세의 조항은 이렇다 — **레벨 2 의 의사 요소 넷**(`::before`·`::after`·`::first-line`·`::first-letter`)은 **레거시 사유로** 콜론 하나로 쓸 수 있다.
- 그리고 「파싱할 때 표준 이름으로 바뀌며, **선택자를 나타내는 어떤 객체 모델에도 옛 이름이 남지 않는다**」고 못 박는다.
- 실측이 그대로다 — `p:before` 를 던지면 `selectorText` 가 **`p::before`** 로 돌아온다.
- ★ **넷뿐이다.** `:marker`·`:selection`·`:placeholder`·`:backdrop` 은 **없다** — 실측에서 `p:bogus-xyz` 와 같은 취급으로 버려진다(위 표의 마지막 줄과 같은 부류).

### (5) 명시도 — 의사 요소는 타입 선택자 하나로 센다

**언제 쓰나** — 의사 요소가 걸린 규칙이 다른 규칙에 지거나 이길 때.

★ **명시도 계산의 정본은 [02번 주제](../02-specificity/2-summary.md)다.** 세 자리 세는 법을 여기서 다시 쓰지 않는다.\
여기서 받아 올 결론은 한 줄이다 — **의사 클래스는 B 자리(클래스와 같은 급), 의사 요소는 C 자리(타입과 같은 급)다.**

```text
   p:nth-child(1)      p::before
     ^ 의사 클래스        ^ 의사 요소
     -> B 자리            -> C 자리
     (0, 1, 1)            (0, 0, 2)

   ★ 콜론 하나 차이로 들어가는 자리가 바뀐다
   ★ 그리고 자리끼리 올림이 없으므로 (0,1,1) > (0,0,2) 다
```

실측이다. 경쟁자에도 같은 의사 요소를 붙여 겨뤘고, 표의 값은 **의사 요소 몫 (0,0,1)을 포함한 합계**다.

| 선택자 | (A, B, C) | 왜 |
|---|---|---|
| `::before` | (0, 0, 1) | 앞이 비면 의사 요소 하나뿐 |
| `p::before` | (0, 0, 2) | `p` 1 + 의사 요소 1 — **둘 다 C** |
| `p:before` | (0, 0, 2) | ★ **콜론 개수는 명시도를 안 바꾼다** |
| `p::first-line` | (0, 0, 2) | 의사 요소 종류와 무관하다 |
| `p::selection` | (0, 0, 2) | 〃 |
| `p.c1::before` | (0, 1, 2) | 클래스가 B 로 들어간다 |
| `p:nth-child(1)::before` | (0, 1, 2) | ★ **의사 클래스도 B** — 위 줄과 값이 같다 |
| `#t1::before` | (1, 0, 1) | |
| `p:is(#t1)::before` | (1, 0, 2) | `:is()` 가 가장 센 인자로 치환 |
| `p:where(#t1)::before` | (0, 0, 2) | `:where()` 는 0 |
| `section p::before` | (0, 0, 3) | 타입 둘 + 의사 요소 하나 |

**직접 겨뤄 확인한 승부** (앞뒤 순서를 바꿔 두 판씩 — 동점이면 뒤에 쓴 쪽이 이기므로 두 판이 갈리면 동점이 아니다).

| 앞 | 뒤 | 이긴 쪽 |
|---|---|---|
| `p.c1::before` (0,1,2) | `section p::before` (0,0,3) | **`p.c1::before`** |
| `section p::before` (0,0,3) | `p.c1::before` (0,1,2) | **`p.c1::before`** |
| `p::before` (0,0,2) | `section p::before` (0,0,3) | `section p::before` |
| `p:nth-child(1)::before` (0,1,2) | `p.c1.c2::before` (0,2,2) | `p.c1.c2::before` |
| `p:before` (0,0,2) | `html body div section p::before` (0,0,5) | 긴 쪽 (두 판 다) |

- 첫 두 줄이 요점이다 — **순서를 뒤집어도 `p.c1::before` 가 이긴다.** C 를 아무리 모아도 B 하나를 못 이긴다.
- 그래서 **「의사 요소를 붙였으니 세졌겠지」가 틀린다.** 붙인 만큼 C 가 1 올라갈 뿐이다.

비용 — 없다.

### (6) 적용 가능한 속성이 제한된 것들

**언제 쓰나** — 「선언은 분명히 썼는데 그 속성만 안 먹는다」일 때.

★ 여기가 **선택자가 버려지는 것과 완전히 다른 층**이다.

```text
   선택자가 무효          속성이 안 먹음
   ┌────────────────┐    ┌──────────────────────────┐
   │ cssRules 에    │    │ cssRules 에 있다         │
   │ 아예 없다      │    │ cssText 에 선언도 그대로 │
   │                │    │ 그런데 계산값이 초깃값   │
   └────────────────┘    └──────────────────────────┘
     (3)절이 다룬 것        이 절이 다루는 것
```

#### `::marker` — 표지 상자에 먹는 속성이 정해져 있다

```css
#m1::marker { color: #b91c1c; font-size: 28px; content: "◆ ";
              background: #00f; padding: 40px; width: 200px; border: 5px solid #0f0; }
```

실측이다.

| | 선언 | `cssRules` 안의 `cssText` | 계산된 값 | 먹었나 |
|---|---|---|---|---|
| `color` | `#b91c1c` | 그대로 있다 | `rgb(185, 28, 28)` | ✔ |
| `font-size` | `28px` | 그대로 있다 | `28px` | ✔ |
| `content` | `"◆ "` | 그대로 있다 | `"◆ "` | ✔ |
| `background` | `#00f` | **그대로 있다** | `rgba(0, 0, 0, 0)` | ✘ |
| `padding` | `40px` | **그대로 있다** | `0px` | ✘ |
| `border` | `5px solid #0f0` | 그대로 있다 | `0px` | ✘ |

- **선언은 파싱됐고 시트에 남아 있다.** `cssRules[0].cssText` 가 `#m1::marker { color: rgb(185, 28, 28); background: rgb(0, 0, 255); padding: 40px; }` 로 그대로 나온다.
- **그런데 표지 상자에는 적용되지 않는다.** 경고도 에러도 없다.
- 명세가 그렇게 정한다 — 표지 상자(marker box)에 실제로 적용되는 것은 **`content`·`text-combine-upright`·`unicode-bidi`·`direction`·모든 애니메이션/전환 속성**뿐이고, 그 밖의 것은 「**효과를 갖지 않아야 한다**」고 적혀 있다.
- 글꼴·색 같은 **상속되는 텍스트 속성은 표지의 「내용」으로 상속돼** 효과가 난다 — 그래서 `color`·`font-size` 는 먹는다. **상자에 먹는 것과 내용에 상속되는 것이 다른 층이다.**
- 목록 항목이 아닌 요소에서는 `::marker` 의 `content` 가 표지를 만들지 않는다. 실측에서 `p::marker` 의 계산된 `content` 는 `normal` 이었다.

*(실측: `font-size: 28px` 를 준 `li` 의 높이가 16px → 27px 로 늘었다. 표지의 글꼴이 실제로 커졌다는 증거다.)*

#### `::first-line` 과 `::first-letter` — 같은 선언에 다르게 답한다

같은 여섯 선언을 둘에 똑같이 줬다.

```css
margin-left: 30px; padding-left: 30px; border-left: 4px solid #f00;
width: 50px; display: block; background: #fde047; color: #b91c1c;
```

| 계산된 값 | `::first-line` | `::first-letter` |
|---|---|---|
| `margin-left` | **`0px`** | `30px` |
| `padding-left` | **`0px`** | `30px` |
| `border-left-width` | **`0px`** | `4px` |
| `width` | `auto` | `auto` |
| `display` | `inline` | `inline` |
| `background-color` | `rgb(253, 224, 71)` | `rgb(253, 224, 71)` |
| `color` | `rgb(185, 28, 28)` | `rgb(185, 28, 28)` |

- **`::first-line` 은 여백·테두리를 받지 않는다.** 첫 줄은 **줄바꿈에 따라 매번 달라지는 것**이라, 여백을 주면 그 여백이 다시 줄바꿈을 바꾸는 순환이 생긴다.
- **`::first-letter` 는 받는다.** 명세가 `::first-letter` 에 적용되는 것으로 **margin·padding·border·box-shadow 를 명시**한다 — 첫 글자는 인라인 박스에 가까운 물건이기 때문이다.
- 둘 다 **글꼴·색·배경·텍스트 장식**은 받는다.
- 스크린샷으로도 확인했다 — `::first-letter` 쪽만 첫 글자가 오른쪽으로 밀리고 왼쪽에 빨간 세로 선이 그어진다.

#### 하이라이트 의사 요소 — 더 좁다

- `::selection` 같은 하이라이트 의사 요소는 명세가 **레이아웃에 영향을 주지 않는 것들만** 허용한다 — `color`·`background-color`·텍스트 장식 계열 등.
- 이유도 적혀 있다 — 하이라이트는 **매우 동적인 환경에서 성능 좋게 칠해야** 하고, 렌더 결과가 UA 가 정하는 하이라이트 영역의 정확한 경계에 **의존하지 않아야** 하기 때문이다.

비용 — 없다. 대신 **「안 먹는 속성」의 목록은 외울 것이 아니라 계산값으로 확인할 것**이다.

### (7) 상태가 필요한 것들 — 계산값이 거짓말한다

**언제 쓰나** — `::selection`·`::placeholder`·`::backdrop` 을 검증할 때.

```text
   getComputedStyle(el, '::selection')

   선택 전  ->  rgb(253, 224, 71)     <- 스타일 그대로 돌려준다
   선택 후  ->  rgb(253, 224, 71)     <- 똑같다

   ★ 「지금 칠해져 있나」는 이걸로 알 수 없다
```

실측이다.

| 의사 요소 | 상태 만들기 | `getComputedStyle` | 상태가 반영되나 | 실제로 확인한 방법 |
|---|---|---|---|---|
| `::selection` | `Range` 로 문단 전체 선택 | 선택 전후 **동일** | ✘ | ★ **스크린샷** — 선택된 줄에 `rgb(253, 224, 71)` 픽셀 1,692개, 글자 `rgb(185, 28, 28)`. 선택 안 한 줄에는 노란 픽셀 0 |
| `::placeholder` | `input.value` 채우기 | 채운 뒤에도 **동일** | ✘ | `:placeholder-shown` 매치 수가 **1 → 0 → 1** 로 바뀐다 |
| `::backdrop` | `dialog.showModal()` | 호출 전에도 **동일** | ✘ | `:modal` 매치 수가 **0 → 1** 로 바뀐다 |

- **셋 다 계산값은 상태와 무관하게 「선언한 값」을 돌려준다.** 「스타일이 읽히니까 지금 적용 중이겠지」는 틀린다 — (1)절의 `content` 없는 `::before` 와 **똑같은 함정**이다.
- **`::selection` 은 이 환경에서 실제로 렌더됐다.** headless 스크린샷으로 색을 세어 확인했으므로 **「미실행」이 아니다.**
- **`::placeholder`·`::backdrop` 의 「칠해진 화면」은 이 문서에서 확인하지 않았다** — 계산값과 상태 의사 클래스까지만 봤다. 그 사실을 「실행 검증」 절에 남겼다.

비용 — 없다.

### (8) 생성 콘텐츠는 접근성 트리에 어떻게 들어가나

**언제 쓰나** — `::before` 로 「필수」·「*」·아이콘을 붙일 때. **화면에만 보이고 읽히지 않으면 접근성 사고가 된다.**

Chrome 의 CDP `Accessibility.getFullAXTree` 로 덤프한 결과다. 다섯 문단에 각각 다른 `content` 를 줬다.

```text
   #a ::before  content: "필수 "                  #b ::before  content: "★" / "별표"
   #c ::before  content: url(1x1 GIF)             #d ::before  content: ""
   #e ::before  content: "장식" / ""
```

| 문단 | `content` | 접근성 트리에 나온 것 |
|---|---|---|
| `#a` | `"필수 "` | `StaticText '필수 '` — 요소 자신의 텍스트 **앞**에 별도 노드로 |
| `#b` | `"★" / "별표"` | ★ `StaticText '별표'` — **화면의 `★` 이 아니라 대체 텍스트가 오른다** |
| `#c` | `url(...)` | `image ''` — 이름 없는 이미지 노드 |
| `#d` | `""` | **아무 노드도 안 생긴다** |
| `#e` | `"장식" / ""` | ★ **아무 노드도 안 생긴다** — `장식` 이라는 StaticText 가 트리에 없다 |

```text
   접근성 트리 (실제 덤프에서 뽑은 것)

   paragraph  #a
     └ StaticText '필수 '        <- ::before 가 만든 것
     └ StaticText '이름'         <- 진짜 텍스트
   paragraph  #b
     └ StaticText '별표'         <- ★ 이 아니라 alt 가 올라갔다
     └ StaticText '별점'
   paragraph  #e
     └ StaticText 'alt 빈 문자열'  <- '장식' 은 없다
```

그림 해설:

- **생성 콘텐츠는 기본적으로 읽힌다.** 「CSS 로 넣은 것은 스크린 리더가 무시한다」는 말은 Chrome 151 에서는 **사실이 아니다.**
- **`/ "대체 텍스트"` 가 화면 글자를 대신한다.** 기호·이모지를 쓸 때 이 문법이 필요한 이유다.
- **`/ ""` 는 감춘다.** 순수 장식이면 이렇게 쓴다.
- 이것이 `alt-text-generated-content` 라는 이름으로 Baseline 에 잡혀 있다 — **newly 2024-07-09**(Chrome 77 · Safari 17.4 · Firefox 128). 「구현 세부사항 대 언어 보장」의 표에 있다.

비용 — 없다.

## 문법 — 형태와 규칙

CSS 는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다(§2-1 규칙 9).

### 형태

```css
.req::after     { content: " *"; color: #b91c1c; }      /* 뒤에 붙이기 */
.tag::before    { content: attr(data-tag); }            /* 속성 값 */
blockquote::before { content: open-quote; }             /* 인용부호 */
li::marker      { content: "→ "; color: #2563eb; }      /* 목록 표지 */
::selection     { background: #fde047; }                /* 선택 영역 */
input::placeholder { color: #737373; }                  /* 자리표시 글자 */
dialog::backdrop   { background: rgb(0 0 0 / .5); }     /* 모달 뒷배경 */
p::first-letter { font-size: 2em; float: left; }        /* 첫 글자 */
```

- `::before` 앞을 비우면 **암묵으로 `*` 가 붙는다** — `::before` 는 `*::before` 다.
- `::selection` 처럼 **문서 전체에 거는 것**은 앞을 비워 쓰는 것이 보통이다.

### 금지 사례 — 던지면 규칙째 사라지는 것

```css
div::before span  { }    /* 의사 요소 뒤에 다른 요소 */
p::before.cls     { }    /* 의사 요소 뒤에 클래스 */
p::before::after  { }    /* 의사 요소 둘 */
p::before:hover   { }    /* ★ 명세는 허용 — Chrome 151 은 버린다 */
p:marker          { }    /* 콜론 하나는 레벨 2 의 넷에만 허용 */
```

- 위 다섯 줄은 **전부 에러 없이 사라진다.**
- 넷째 줄은 **이 문서가 쓸 수 있는 말이 「Chrome 151 에서는 안 된다」까지**라는 것을 보여 주는 자리다.

### 상자를 만드는 것과 안 만드는 것

```css
.a::before { content: none; }   /* 상자 없음 */
.b::before { content: normal; } /* 상자 없음 — ::before 에서는 none 과 같다 */
.c::before { content: ""; }     /* 상자 있음 (빈 상자) */
```

- 셋을 눈으로 구분할 수 없다. **`offsetWidth` 로 쟀을 때만 갈린다**(8px / 8px / 58px).

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 여섯 다 **에러 없이 조용히 어긋난다.**

### 1. `content` 를 빼놓고 다른 선언만 한다

```css
.icon::before { width: 16px; height: 16px; background: url(...); }
```

- **아무것도 안 나온다.** `content` 가 없으면 상자가 만들어지지 않는다.
- `getComputedStyle(el, '::before').width` 는 **`16px` 을 돌려준다** — 그래서 「선언은 들어갔는데?」에서 멈춘다.
- 판정은 **치수로** 한다. 기원 요소의 `offsetWidth` 가 안 늘었으면 상자가 없다.

### 2. `getComputedStyle` 의 두 번째 인자를 빼먹는다

```js
getComputedStyle(el).content            // 'normal'  <- 기원 요소 자신의 값
getComputedStyle(el, '::before').content // '"[별]"'  <- 의사 요소의 값
```

- 인자를 빼면 **다른 것을 읽는다.** 값이 나오니까 틀린 줄도 모른다.
- `document.querySelector('p::before')` 같은 것은 **없다** — 의사 요소는 DOM 에 없다.

### 3. `::before` 를 선택자 중간에 쓴다

```css
.card::before .label { color: red; }   /* 규칙째 사라진다 */
```

- 의사 요소는 **맨 끝에만** 온다. 「`::before` 안의 무엇」이라는 것은 없다 — `::before` 는 내용을 `content` 로만 갖는다.
- 개발자 도구에도 안 나타나므로 「왜 안 먹지」로 오래 붙들게 된다.

### 4. 속성이 안 먹는 것을 선택자 문제로 오진한다

```css
li::marker { background: #00f; padding: 4px; }   /* 규칙은 살아 있다. 안 먹을 뿐 */
```

- `cssRules` 에도 있고 `cssText` 에도 그대로 있다. **선택자는 멀쩡하다.**
- 계산값을 읽어야 안다 — `background-color` 가 `rgba(0, 0, 0, 0)` 이고 `padding` 이 `0px` 이다.
- **「담겼나」와 「먹었나」는 다른 검사다.**

### 5. 화면에만 보이는 아이콘을 만든다

```css
.required::after { content: "*"; }
```

- 접근성 트리에 **`StaticText '*'`** 로 그대로 오른다 — 읽히기는 하는데 「별」이라고 읽힌다.
- 뜻을 주려면 `content: "*" / "필수 항목"`, 감추려면 `content: "*" / ""`.
- 실측에서 `"장식" / ""` 은 접근성 트리에 **노드 자체가 안 생겼다.**

### 6. `:before` 와 `::before` 가 다른 것이라고 생각한다

- **같다.** 명시도도 (0,0,2) 로 같고, `selectorText` 는 `::before` 로 통일돼 나온다.
- 콜론 하나로 쓸 수 있는 것은 **레벨 2 의 넷뿐**이다 — `::marker`·`::selection`·`::placeholder`·`::backdrop` 에는 없다.
- 새로 쓸 때는 **콜론 둘**을 쓴다. 옛 표기는 「깨뜨릴 수 없어서 남겨 둔 것」이지 선택지가 아니다.

## 구현 세부사항 대 언어 보장

| 항목 | 누가 보장하나 | 근거 |
|---|---|---|
| `content` 가 `none` 이면 상자가 없다 | **명세** | css-pseudo-4 — `::before`/`::after` 는 `content` 로 생성된다 |
| `::marker` 상자에 먹는 속성 목록 | **명세** | css-lists-3 §3.1.1 — 「only the following CSS properties actually apply to a marker box」 |
| 목록 항목이 아니면 `::marker` 의 `content` 가 `none` 으로 계산 | **명세** | 같은 절 |
| `::first-letter` 에 margin/padding/border 가 적용 | **명세** | css-pseudo-4 §2.2.4 의 적용 속성 목록 |
| 하이라이트 의사 요소의 속성 제한 | **명세** | css-pseudo-4 §3.2 |
| 콜론 하나는 **넷**에만 허용 | **명세** | Selectors 4 §16 — 「The four Level 2 pseudo-elements … for legacy reasons」 |
| 의사 요소는 복합 선택자의 **맨 끝**에만 | **명세** | Selectors 4 §16 의 주 |
| 의사 요소 뒤의 **사용자 동작 의사 클래스** | ★ **명세는 허용, Chrome 151 은 미구현** | Selectors 4 §3.6.3. 48 조합 실측에서 `:hover`/`:active`/`:focus` 가 전부 버려졌다 |
| `selectorText` 가 `:before` → `::before` 로 나오는 것 | **명세** | 「어떤 객체 모델에도 옛 이름이 남지 않는다」 |
| `attr()` 이 계산값에 풀려 있고 `counter()` 는 안 풀리는 것 | **관찰** | Chrome 151 에서 본 것이다. 계산 시점을 근거로 코드를 짜지 않는다 |
| 접근성 트리의 노드 이름·역할 | **관찰** | Chrome 의 AX 트리 덤프다. 스크린 리더마다 읽는 방식이 다르다 |

**Baseline** (2026-09-23 에 `api.webstatus.dev` 를 직접 조회한 값이다. 추측하지 않았다.)

| 기능 | Baseline | newly | widely | 메모 |
|---|---|---|---|---|
| `::first-line` | widely | 2015-07-29 | 2018-01-29 | |
| `::first-letter` | widely | 2015-07-29 | 2018-01-29 | |
| `::placeholder` | widely | 2020-01-15 | 2022-07-15 | |
| `::backdrop` | widely | 2022-03-14 | 2024-09-14 | |
| 생성 콘텐츠의 대체 텍스트(`"x" / "alt"`) | **newly** | 2024-07-09 | — | Chrome 77 · Safari 17.4 · Firefox 128 |
| `::marker` | **limited** | — | — | ★ 조회 결과에 **Safari 행이 없다**(Chrome 86 · Edge 86 · Firefox 80 만) |
| `::selection` | **limited** | — | — | ★ 조회 결과에 **iOS Safari 행이 없다**(데스크톱 Safari 1.1 은 있다) |

- ★ **`limited` 두 줄은 「없다」가 아니라 「집계에 안 잡혔다」로 읽는다.** `webstatus.dev` 는 **2차 집계**이고, 이 머신에 **WebKit 이 없어 실행으로 반증할 수 없다.**
- 그래서 **Safari 계열의 `::marker`·`::selection` 동작은 이 문서에서 「미실행」이다.** 아는 것은 「집계가 그렇게 말한다」까지다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 순수 장식(구분선·아이콘) | `::before { content: "" }` + 치수 | `<span>` 을 마크업에 더하기 |
| 뜻이 있는 표시(필수·필터 적용됨) | `content: "*" / "필수 항목"` | `content: "*"` 만 |
| 데이터 속성을 화면에 | `content: attr(data-x)` | JS 로 텍스트 노드 만들기 |
| 목록 번호·불릿 꾸미기 | `::marker { color; font; content }` | `::marker { background; padding }` — 안 먹는다 |
| 표지 상자에 배경·여백이 꼭 필요할 때 | `li::before` 로 직접 그리기 | `::marker` 로 우기기 |
| 첫 줄 강조 | `::first-line { color; background }` | `::first-line { margin; padding }` — 안 먹는다 |
| 첫 글자 드롭캡 | `::first-letter { font-size; float; margin }` | |
| 상태를 조건으로 의사 요소 바꾸기 | `.card:has(img)::before` | `.card::before:has(img)` — 사라진다([12번](../12-has-relational-selector/2-summary.md)) |
| 새로 쓰는 코드의 표기 | `::before` | `:before` |

판단 규칙 두 줄.

- **의사 요소는 「마크업을 더하지 않고 상자를 하나 얻는」 도구다.** 그 상자가 **내용을 가질 수 있는 것은 `content` 뿐**이라는 제약이 따라온다.
- **화면에 보인다고 읽히는 것도, 읽힌다고 뜻이 전달되는 것도 아니다.** 뜻이 있으면 대체 텍스트를 주고, 장식이면 감춘다.

## 핵심 문장

- 의사 요소는 **문서 트리에 없는 상자**다 — DOM 으로는 절대 잡히지 않고, **`content` 가 `none` 이 아닐 때만 존재한다.**
- **`getComputedStyle` 은 상자가 없어도 값을 돌려준다.** 존재의 근거는 계산값이 아니라 **치수**다(8px 대 58px).
- 계산값을 읽으려면 **두 번째 인자**가 필요하다 — `getComputedStyle(el, '::before')`. 빼면 기원 요소 자신을 읽는다.
- `content` 에서 **`normal` 은 `none` 으로 계산되고, `""` 는 상자를 만든다.** 셋의 차이는 눈으로 안 보인다.
- 의사 요소는 **복합 선택자의 맨 끝에만** 온다. 뒤에 클래스·요소·다른 의사 요소가 오면 **규칙째 사라진다.**
- 명시도에서 **의사 요소는 C 자리**(타입 급)이고 **의사 클래스는 B 자리**(클래스 급)다 — 콜론 개수가 자리를 가른다. 계산의 정본은 [02번 주제](../02-specificity/2-summary.md).
- `:before` 와 `::before` 는 **같다** — 레벨 2 의 넷만 레거시 별칭을 갖고, 파싱 뒤에는 콜론 둘로 통일된다.
- **「선택자가 버려진 것」과 「속성이 안 먹은 것」은 다른 층이다.** 앞엣것은 `cssRules` 에 없고, 뒤엣것은 `cssText` 에 그대로 있으면서 계산값만 초깃값이다.
- **생성 콘텐츠는 접근성 트리에 오른다.** `/ "대체"` 로 바꿔 읽히게 하고, `/ ""` 로 감춘다.

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 13번) · 「버전·지원 기준」의 Baseline 표
- [`../02-specificity/2-summary.md`](../02-specificity/2-summary.md) — ★ **명시도 계산의 정본.** (A, B, C) 를 세는 법은 전부 거기. **여기는 「의사 요소가 어느 자리에 들어가나」와 그 실측만** 싣는다
- [`../01-cascade-and-priority/2-summary.md`](../01-cascade-and-priority/2-summary.md) — 「선언이 이겼나」를 판정하는 캐스케이드 단계
- [`12-has-relational-selector`](../12-has-relational-selector/2-summary.md) — ★ 경계: **`:has()` 의 규칙은 거기**, **`:has()` 가 왜 의사 요소를 거부하는지의 이유(조건부 존재)는 여기**
- [`14-css-nesting`](../14-css-nesting/2-summary.md) — 중첩 안에서 의사 요소를 쓸 때의 `&` 규칙
- [목록의 **08번 주제**](../08-basic-selectors-and-combinators/)(기본 선택자·조합자) — ★ 경계: **복합 선택자·조합자의 정의는 거기까지**, **의사 요소가 그 안 어디에 놓일 수 있는지는 여기부터**
- [목록의 **09번 주제**](../09-structural-pseudo-classes/)(구조적 의사 클래스) · **10번 주제**(상태·폼 의사 클래스) — ★ 경계: **의사 「클래스」는 그쪽 둘이 정본**. 여기는 의사 「요소」만
- [목록의 **11번 주제**](../11-is-where-not/)(`:is()`·`:where()`·`:not()`) — 의사 요소를 그 안에 넣었을 때 내용이 증발하는 이유(관용적 목록)의 정본
- ★ **카운터**(`counter-reset`/`counter-increment`/`counter()`)는 이 목록의 다른 자리다. 여기서는 **`content` 가 받는 값의 하나로 존재만 보이고 넘겼다.**
- [`reference/render-rules.md`](../../../../../../reference/render-rules.md) — 이 문서의 `demo` 블록 규칙

## 용어 풀이

- **의사 요소(pseudo-element)** — 문서 트리에 없는 가상의 상자. `::` 둘로 시작한다. 명시도 C 자리.
- **의사 클래스(pseudo-class)** — 요소의 상태·위치를 가리키는 선택자. `:` 하나로 시작한다. 명시도 B 자리.
- **생성 콘텐츠(generated content)** — `content` 가 만들어 낸, HTML 에 없는 내용.
- **기원 요소(originating element)** — 의사 요소가 붙는 진짜 요소. `p::before` 의 기원 요소는 `p`.
- **표지 상자(marker box)** — 목록 항목 앞의 번호·점을 담는 상자. `::marker` 가 가리킨다.
- **하이라이트 의사 요소(highlight pseudo-element)** — 선택·검색·맞춤법 오류처럼 **겹쳐 칠해지는** 것들. `::selection` 이 대표.
- **레거시 별칭(legacy alias)** — 파싱할 때 표준 이름으로 바뀌는 옛 표기. `:before` → `::before`.
- **복합 선택자(compound selector)** — 조합자 없이 붙여 쓴 한 덩어리. `p.c1:hover` 가 하나다.
- **접근성 트리(accessibility tree)** — 브라우저가 보조기기에 넘기는, DOM 을 역할·이름으로 재구성한 트리.
- **대체 텍스트(alt text)** — `content: "★" / "별표"` 의 뒷부분. 화면 대신 접근성 트리에 오르는 문자열.
- **계산값(computed value)** — 상속·초깃값·단위 변환까지 끝낸 값. `getComputedStyle` 이 돌려주는 것.
- **Baseline** — 주요 브라우저 지원 정도 지표. `widely` / `newly` / `limited` 셋.

---

## 더 들어가면

- **`::before` 는 기원 요소의 「안쪽 맨 앞」이지 「앞」이 아니다.** 요소 바깥이 아니라 자식들 앞에 끼워진다 —\
  그래서 `p::before` 의 배경은 `p` 의 패딩 안쪽에서 시작한다.
- **`content` 에 `open-quote`/`close-quote` 를 쓸 수 있다.** 실측에서 계산값은 `open-quote` 로 **풀리지 않은 채** 남고(`counter()` 와 같은 부류다), 렌더 결과와 접근성 트리에는 `“`·`”` 가 들어갔다.\
  이것이 `quotes` 속성과 언어 설정을 어떻게 따라가는지는 **확인하지 않았다.**
- **의사 요소에도 의사 요소가 붙을 수 있다.** 실측에서 `p::before::marker` 와 `li::before::marker` 가 담겼다 — 명세가 `::before::marker`·`::after::marker` 를 유효로 만든 조항이 변경 이력에 있다. **동작은 확인하지 않았다.**
- **`::selection` 은 상속이 특이하다.** 명세에 하이라이트의 캐스케이딩·상속 규칙이 따로 있다(§3.5). 이 문서는 **거기까지 들어가지 않았다.**
- **`::marker` 의 Baseline 이 `limited` 인데 실무에서 널리 쓰이는 것**이 이 표의 한계를 보여 준다. Baseline 은 「**전 엔진에서 확인됐나**」이지 「쓸 만한가」가 아니다. 판단은 **내가 받쳐야 하는 브라우저 목록**으로 한다.

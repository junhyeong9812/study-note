# javascript/dom-style/07 — Constructable Stylesheets — 정리 (힌트)

> 출처 — study-site 항목 `javascript/constructable-stylesheets`(항목 데이터 `data/javascript/dom-style.json`) · 정답 코드 study-practice `javascript/dom-style/reference/constructable-stylesheets.js`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 브라우저 DOM API 를 쓰는 예제다 — 브라우저에서 확인한다.

## 한눈에 — 쉽게 말하면

**Constructable Stylesheet 는 「게시판에 붙이는 공지 한 장」이다.**
공지 한 장(시트 객체)을 먼저 써 두고, 게시판(문서나 Shadow DOM)의 「붙인 공지 목록」에 그 종이를 올리면 사람들이 그 규칙을 따른다.
종이에 적힌 글을 고쳐 쓰면, 그 종이가 붙은 모든 게시판에서 바뀐 글이 보인다.
목록에서 종이를 빼면 규칙도 함께 사라진다.
`CSSStyleSheet` 와 `adoptedStyleSheets` 도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 공지 한 장 | `new CSSStyleSheet()` 로 만든 시트 객체 |
| 공지에 적힌 글 | `replaceSync(css)` 로 넣은 CSS 규칙 |
| 게시판의 「붙인 공지 목록」 | `document.adoptedStyleSheets` (또는 `shadowRoot.adoptedStyleSheets`) |
| 글을 고쳐 쓰기 | 같은 객체에 `replaceSync` 를 다시 부르기 |
| 목록에서 종이 빼기 | `filter` 로 그 시트만 뺀 배열을 다시 할당 |

```text
  JS 안의 시트 객체                 채택 목록                  화면
 ┌──────────────────┐        ┌───────────────────┐
 │ sheet            │ ─────▶ │ [ ...기존, sheet ] │ ─────▶  규칙이 요소에 적용
 │  .item { ... }   │        └───────────────────┘
 └──────────────────┘
```

## 이 주제가 답하려는 질문

1. `<style>` 태그 없이 JavaScript 만으로 스타일시트를 만들어 붙이려면 무엇을 하나?
2. 이미 붙인 스타일을 바꾸거나 떼어 내려면 무엇을 하나?
3. 한 시트를 여러 곳(문서 · 여러 Shadow DOM)에 함께 쓰면 무엇이 좋은가?

## 동작 방식

### (1) 시트를 만들고 내용을 채운다

**언제 쓰나** — 스타일을 JS 코드 안에서 만들고 다룰 때.

```text
const sheet = new CSSStyleSheet();      →  빈 시트 객체가 생긴다 (아직 어디에도 안 붙음)
sheet.replaceSync(`.item { ... }`);     →  시트의 규칙 전체가 이 CSS 로 바뀐다
                                        →  화면은 그대로 (채택되지 않았으므로)
```

- `new CSSStyleSheet()` 는 `<style>` 태그 없이 스타일시트 객체를 만든다.
- `replaceSync(css)` 는 시트의 내용을 동기적으로, 통째로 교체한다.
- 시트를 만들고 채우는 것만으로는 아무 요소에도 적용되지 않는다.

> **Constructable Stylesheet** — 생성자(`new CSSStyleSheet()`)로 JS 에서 직접 만드는 스타일시트.\
> 예: `const sheet = new CSSStyleSheet();`

> **replaceSync** — 시트 내용을 주어진 CSS 문자열로 동기적으로 교체하는 메서드.\
> 예: `sheet.replaceSync('.a { color: red; }')`

### (2) 문서에 채택한다

**언제 쓰나** — 만든 시트를 실제로 화면에 적용할 때.

```text
document.adoptedStyleSheets = [
  ...document.adoptedStyleSheets,  →  지금 채택된 시트들을 펼쳐 새 배열에 담고
  sheet                            →  맨 뒤에 내 시트를 덧붙인 뒤
];                                 →  그 새 배열을 할당 → 규칙이 문서에 적용된다
```

- `adoptedStyleSheets` 는 「이 문서가 채택한 시트들」의 배열이다.
- 원본 주석은 「`adoptedStyleSheets` 에 할당해야 실제 문서에 스타일이 적용된다」고 말한다.
- 스프레드(`...`)로 기존 시트를 먼저 펼쳐 두기 때문에 다른 시트가 빠지지 않는다.
- 배열이므로 여러 시트를 조합해 붙일 수 있다.

> **adoptedStyleSheets** — 문서나 Shadow Root 가 채택한 Constructable Stylesheet 들의 배열.\
> 예: `document.adoptedStyleSheets = [base, theme];`

> **채택(adopt)** — 시트를 `adoptedStyleSheets` 배열에 넣어 그 범위에 적용되게 하는 일.\
> 예: 배열에 `sheet` 를 넣는 할당이 채택이다.

### (3) 같은 시트를 고쳐 쓴다

**언제 쓰나** — 이미 붙인 스타일을 다른 규칙으로 바꿀 때.

```text
sheet.replaceSync(`.item { 새 규칙 }`);   →  같은 객체의 내용만 바뀐다
(adoptedStyleSheets 는 손대지 않음)       →  배열 안의 객체가 바로 그 객체이므로
                                          →  채택된 모든 곳에 새 규칙이 반영된다
```

- 배열은 시트의 복사본이 아니라 시트 객체 자체를 가리킨다.
- 그래서 객체의 내용을 바꾸면 배열을 다시 할당하지 않아도 된다.
- 단, 고쳐 쓰는 대상이 **채택된 바로 그 객체**여야 한다.
  새 `CSSStyleSheet` 를 만들어 채우면 그것은 다른 종이다.

### (4) 떼어 낸다

**언제 쓰나** — 내 시트만 빼고 다른 시트는 남길 때.

```text
document.adoptedStyleSheets =
  document.adoptedStyleSheets.filter(s => s !== sheet);
      →  배열을 돌며 sheet 와 같은 객체를 모두 걸러 낸 새 배열을 만들고
      →  그 배열을 할당 → sheet 의 규칙이 문서에서 빠진다
```

- `filter` 는 조건을 통과한 원소만 담은 새 배열을 돌려준다.
- `s !== sheet` 를 통과하지 못하는 원소, 곧 `sheet` 와 같은 객체는 몇 개든 전부 빠진다.
- 시트 객체 자체는 변수 `sheet` 에 남아 있으므로 다시 채택할 수 있다.

### (5) 비동기 `replace()` 와 Shadow DOM

**언제 쓰나** — 교체를 Promise 로 다루고 싶을 때, 그리고 여러 컴포넌트가 스타일을 나눠 쓸 때.

```text
await sheet.replace(css);                   →  Promise 를 돌려준다 · 끝난 뒤 이어 간다
shadowA.adoptedStyleSheets = [sheet];       →  컴포넌트 A 가 채택
shadowB.adoptedStyleSheets = [sheet];       →  컴포넌트 B 도 같은 객체를 채택
sheet.replaceSync(newCss);                  →  A 와 B 가 함께 바뀐다
```

- `replace()` 는 `replaceSync()` 의 비동기 버전이며 Promise 를 돌려준다.
- Shadow Root 에도 `adoptedStyleSheets` 가 있다.
- Shadow DOM 의 스타일은 바깥과 격리되므로, 같은 시트를 여러 Shadow Root 에 채택하면 격리는 지키면서 규칙은 한 객체로 공유한다.

> **Shadow DOM** — 요소 안에 바깥과 스타일이 격리된 별도 DOM 트리를 붙이는 기능.\
> 예: `el.attachShadow({ mode: 'open' })` 로 만든 Shadow Root.

> **Promise** — 나중에 끝나는 작업의 결과를 나타내는 객체.\
> 예: `await sheet.replace(css)` 는 교체가 끝날 때까지 기다린다.

## 문법 — 형태와 규칙

```html demo
<div class="box">안녕</div>
<script>
  const s = new CSSStyleSheet();
  s.replaceSync('.box { padding: 8px; background: gold; }');
  document.adoptedStyleSheets = [...document.adoptedStyleSheets, s];
</script>
```

> **보이는 것** — 「안녕」이 금색 배경에 안쪽 여백을 가진 상자로 보인다 (코드에서 읽은 것 — 렌더 실측 아님)

- 만들기: `const sheet = new CSSStyleSheet();`
- 채우기(동기): `sheet.replaceSync(cssText);` — 내용 전체 교체.
- 채우기(비동기): `sheet.replace(cssText)` — Promise 를 돌려준다.
- 채택: `document.adoptedStyleSheets = [...document.adoptedStyleSheets, sheet];`
- Shadow DOM 에 채택: `shadowRoot.adoptedStyleSheets = [sheet];`
- 떼기: `document.adoptedStyleSheets = document.adoptedStyleSheets.filter(s => s !== sheet);`
- CSS 를 여러 줄로 쓸 때는 템플릿 리터럴(백틱 문자열)이 편하다.

## 어디서 틀리나

### 1. 만들고 채웠는데 아무것도 안 바뀐다

`replaceSync` 까지만 부르고 `adoptedStyleSheets` 에 넣지 않으면 시트는 어디에도 적용되지 않는다.
채택 전에 부른 `replaceSync` 는 내용만 바꿔 둘 뿐이다.

### 2. `[sheet]` 로 덮어써 다른 시트가 사라진다

`document.adoptedStyleSheets = [sheet]` 는 기존 배열을 버리고 내 시트 하나만 남긴다.
다른 코드가 붙여 둔 시트를 지키려면 `...document.adoptedStyleSheets` 로 먼저 펼친다.

### 3. 채택 코드를 여러 번 부르면 같은 시트가 여러 번 들어간다

채택 함수를 두 번 부르면 펼친 배열에 이미 `sheet` 가 있는데 또 `sheet` 를 덧붙인다.
JS 배열로만 보면 같은 객체가 두 번 들어간 꼴이다(브라우저가 이것을 어떻게 다루는지는 확인 필요).
떼어 낼 때 `filter(s => s !== sheet)` 는 같은 객체를 모두 걸러 내므로 몇 번 들어갔든 다 빠진다.

### 4. `replaceSync` 는 「덧붙이기」가 아니라 「통째 교체」다

두 번째 `replaceSync` 는 첫 번째 규칙에 더해지지 않고 그것을 대신한다.
이전 규칙에만 있던 선언은 사라진다.

### 5. `replace()` 를 부르고 바로 반영됐다고 가정한다

`replace()` 는 Promise 를 돌려주는 비동기 버전이다.
교체가 끝난 뒤의 일을 하려면 `await` 하거나 `.then` 에서 한다.
바로 반영이 필요하면 `replaceSync()` 를 쓴다.

### 6. 고칠 때마다 새 시트를 만든다

갱신 함수 안에서 `new CSSStyleSheet()` 를 다시 부르면, 채택된 객체와 다른 새 객체를 고치게 된다.
그래서 시트는 함수 밖에서 한 번 만들고 모든 함수가 같은 변수를 쓴다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `CSSStyleSheet` · `adoptedStyleSheets` · `replaceSync` · `replace` 가 있다 | 웹 표준(CSSOM) — JS 언어(ECMAScript)가 아니라 브라우저가 주는 API다 |
| `replaceSync` 는 동기, `replace` 는 Promise 를 돌려준다 | 웹 표준 (원본 팁) |
| 같은 시트 객체를 고치면 채택된 모든 곳에 반영된다 | 웹 표준 — 배열이 객체를 가리키기 때문 (원본 주석) |
| `filter` 는 조건을 통과한 원소만 담은 새 배열을 돌려준다 | JS 언어(ECMAScript) |
| 같은 시트가 배열에 두 번 들어갔을 때의 처리 | 확인 필요 |
| 지원하는 브라우저와 버전 | 이 문서에서 다루지 않음 (확인 필요) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 여러 Shadow DOM 컴포넌트가 같은 스타일을 나눠 쓴다 | 시트 하나를 만들어 각 `shadowRoot.adoptedStyleSheets` 에 채택 | 컴포넌트마다 `<style>` 복사 |
| 테마처럼 규칙 묶음을 통째로 바꾼다 | 같은 시트에 `replaceSync` | 새 시트를 만들어 매번 채택 |
| 내 시트만 떼고 나머지는 남긴다 | `filter(s => s !== sheet)` 재할당 | `adoptedStyleSheets = []` |
| 요소 하나의 속성 하나만 바꾼다 | `element.style` | 시트를 새로 만들기 |

## 핵심 문장

1. **`new CSSStyleSheet()` 로 만들고 `replaceSync` 로 채운다** — 아직 아무 데도 적용되지 않는다.
2. **`adoptedStyleSheets` 에 넣어야 적용된다** — 기존 배열을 펼쳐 덧붙이면 다른 시트를 지킨다.
3. **같은 객체를 고치면 채택된 모든 곳이 함께 바뀐다** — 재할당이 필요 없다.
4. **떼어 낼 때는 그 시트만 뺀 새 배열을 할당한다.**
5. **`replace()` 는 Promise 를 돌려주는 비동기 버전이다.**

## 관련 자료

- 원본에 관련 항목이 없다.
- 원본: study-site 항목 데이터 `data/javascript/dom-style.json` 의 `constructable-stylesheets`

## 용어 풀이

- **Constructable Stylesheet** — `new CSSStyleSheet()` 로 JS 에서 만드는 스타일시트.
- **`CSSStyleSheet`** — 스타일시트를 나타내는 객체의 생성자.
- **`replaceSync`** — 시트 내용을 동기적으로 통째 교체하는 메서드.
- **`replace`** — `replaceSync` 의 비동기 버전, Promise 를 돌려준다.
- **`adoptedStyleSheets`** — 문서나 Shadow Root 가 채택한 시트들의 배열.
- **채택(adopt)** — 시트를 `adoptedStyleSheets` 에 넣어 적용되게 하는 일.
- **Shadow DOM** — 스타일이 바깥과 격리된 별도 DOM 트리.
- **Shadow Root** — Shadow DOM 트리의 뿌리 노드.
- **Promise** — 나중에 끝나는 작업의 결과를 나타내는 객체.
- **스프레드(`...`)** — 배열의 원소를 펼쳐 다른 배열에 넣는 문법.
- **템플릿 리터럴** — 백틱으로 감싼, 여러 줄을 쓸 수 있는 문자열.

## 더 들어가면

- 채택된 시트는 문서의 `<style>` · `<link>` 시트보다 뒤에 놓인 것으로 취급되어, 특이도가 같으면 채택된 시트의 규칙이 이긴다고 알려져 있다 (확인 필요).
- 예전 구현에서는 `adoptedStyleSheets` 가 고정 배열이어서 `push` 가 막혀 있었고 재할당만 됐으며, 뒤의 구현은 `push` 같은 배열 조작도 받아들인다고 알려져 있다 (확인 필요).
- `replace` · `replaceSync` 안의 `@import` 규칙은 처리되지 않는다고 알려져 있다 (확인 필요).
- `sheet.insertRule` · `sheet.deleteRule` 로 규칙을 하나씩 넣고 뺄 수도 있다 (확인 필요).
- 시트는 그것을 만든 문서에만 채택할 수 있다는 제약이 있다고 알려져 있다 (확인 필요).

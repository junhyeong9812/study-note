# javascript/dom-style/07 — Constructable Stylesheets — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 이전 규칙은 남지 않고, 모서리가 둥근 사각형이 된다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
- `background: #8b5cf6` 는 남지 않는다.
- `.item` 은 모서리가 12px 둥근 사각형이 되고, 10도 기울고 1.15배로 커진다 (코드에서 읽은 것 — 렌더 실측 아님).
- 배경은 시트에서 빠졌으므로 페이지 CSS 의 `.item` 배경이 적용된다고 읽힌다 (원본에 근거 없음 — 추론).

**왜 그런가**
`replaceSync` 는 시트 내용을 덧붙이지 않고 통째로 교체한다.
두 번째 호출의 CSS 에 `background` 가 없으니 첫 번째 규칙의 배경은 사라진다.
`border-radius` 와 `transform` 은 새 값으로 바뀐다.
근거: 2-summary 「동작 방식 (1)」, 「어디서 틀리나 4」.

### 2. 0개 — 같은 객체는 몇 번 들어갔든 모두 걸러진다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`sheet` 는 하나도 남지 않는다.

**왜 그런가**
`applySheet` 를 두 번 부르면 JS 배열로 보면 `sheet` 가 두 번 덧붙는다(브라우저의 처리는 확인 필요).
하지만 `filter(s => s !== sheet)` 는 `sheet` 와 같은 객체를 모두 탈락시킨다.
그래서 들어간 횟수와 상관없이 다 빠진다.
근거: 2-summary 「동작 방식 (4)」, 「어디서 틀리나 3」.

### 3. Update 만으로는 바뀌지 않고, 이어진 Apply 의 규칙이 이긴다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
- Update 만 누른 직후 `.item` 의 겉모습은 그대로다 (코드에서 읽은 것 — 렌더 실측 아님).
- 이어서 Apply 를 누르면 Apply 의 규칙(보라 배경 원형, 1.1배)이 적용된다.

**왜 그런가**
Update 는 시트 내용만 바꿀 뿐 채택하지 않는다.
채택되지 않은 시트는 어디에도 적용되지 않는다.
Apply 는 먼저 `replaceSync` 로 내용을 Apply 의 CSS 로 통째 교체한 뒤 채택하므로, Update 에서 넣은 내용은 덮여 사라진다.
근거: 2-summary 「동작 방식 (1)」, 「어디서 틀리나 1 · 4」.

### 4. 배열이 시트 객체 자체를 가리키기 때문이다

채택 목록에는 시트의 복사본이 아니라 `sheet` 객체 자체가 들어 있다.
`updateSheet` 는 그 같은 객체의 내용을 `replaceSync` 로 바꾸므로, 채택된 모든 곳에 새 규칙이 바로 반영된다.
그래서 배열을 다시 할당할 필요가 없다.
단, 시트를 함수 밖에서 한 번만 만들어 같은 객체를 고쳐야 이 일이 성립한다.
근거: 2-summary 「동작 방식 (3)」, 「어디서 틀리나 6」.

### 5. 다른 곳에서 채택해 둔 시트를 잃지 않으려고

`[sheet]` 로 할당하면 기존 배열이 버려져 다른 코드가 붙여 둔 시트가 모두 빠진다.
`...document.adoptedStyleSheets` 로 기존 시트를 먼저 펼치면 그 시트들을 지킨 채 내 시트를 맨 뒤에 덧붙인다.
`adoptedStyleSheets` 가 배열이라 여러 시트를 조합할 수 있다는 점을 살리는 쓰임이다.
근거: 2-summary 「동작 방식 (2)」, 「어디서 틀리나 2」.

### 6. 기대하면 안 된다 — `replace()` 는 Promise 를 돌려주는 비동기 버전이다

`replace()` 는 교체가 끝났음을 Promise 로 알린다.
교체 뒤의 일은 `await sheet.replace(css)` 다음이나 `.then` 안에서 해야 한다.
부른 즉시 반영이 필요하면 동기 버전인 `replaceSync()` 를 쓴다.
근거: 2-summary 「동작 방식 (5)」, 「어디서 틀리나 5」.

### 7. 다시 쓸 수 있고, Apply 의 규칙이 다시 적용된다

Remove 는 채택 목록에서 시트를 뺄 뿐, 변수 `sheet` 에 담긴 객체는 그대로 남는다.
다시 Apply 를 누르면 `replaceSync` 가 내용을 Apply 의 CSS 로 교체하고 시트를 다시 채택한다.
그래서 Remove 직전에 Update 상태였더라도 Apply 의 규칙이 적용된다.
근거: 2-summary 「동작 방식 (4)」, 「동작 방식 (1)」.

### 8. 규칙을 한 객체로 공유해 한 번 고치면 열 곳이 함께 바뀐다

Shadow Root 에도 `adoptedStyleSheets` 가 있어 같은 시트 객체를 각 컴포넌트에 채택할 수 있다.
Shadow DOM 의 격리는 그대로 지키면서 규칙은 한 객체에 모인다.
그 시트에 `replaceSync` 를 한 번 부르면 채택한 모든 컴포넌트에 반영된다.
컴포넌트마다 `<style>` 을 넣으면 같은 CSS 가 열 벌 생기고, 바꿀 때도 열 곳을 고쳐야 한다.
근거: 2-summary 「동작 방식 (5)」, 「언제 쓰고 언제 안 쓰나」.

## 실습 정답

### 실습 1. 버튼 셋으로 스타일시트 붙이기 · 고치기 · 떼기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 시트 객체를 한 번만 만들어 함께 쓴다 | 맨 위 `const sheet = new CSSStyleSheet();` |
| 2. Apply 에서 내용을 동기 교체 | `applySheet` 의 `sheet.replaceSync(...)` |
| 3. 기존 시트를 유지하며 덧붙여 채택 | `document.adoptedStyleSheets = [...document.adoptedStyleSheets, sheet]` |
| 4. Update 는 같은 시트 내용만 교체 | `updateSheet` 의 `sheet.replaceSync(...)` (할당 없음) |
| 5. Remove 는 이 시트만 뺀 배열로 재할당 | `document.adoptedStyleSheets.filter(s => s !== sheet)` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`javascript/dom-style/reference/constructable-stylesheets.js`

```javascript
// [DOM 스타일 조작] Constructable Stylesheets
// 설명: new CSSStyleSheet()로 JavaScript에서 직접 스타일시트를 생성하고 adoptedStyleSheets로 문서나 Shadow DOM에 적용한다.
// 팁: replaceSync()는 동기적으로 스타일을 교체하고, replace()는 Promise를 반환하는 비동기 버전이다. adoptedStyleSheets는 배열이므로 여러 시트를 조합할 수 있다. Shadow DOM과 함께 사용하면 스타일 격리와 공유를 효율적으로 관리할 수 있다.

const sheet = new CSSStyleSheet();  // <style> 태그 없이 JS에서 직접 스타일시트 객체 생성

function applySheet() {  // 스타일시트를 처음 적용하는 함수
  sheet.replaceSync(`
    .item {
      background: #8b5cf6;
      color: white;
      border-radius: 50%;
      transform: scale(1.1);
      box-shadow: 0 4px 15px rgba(139,92,246,0.4);
    }
  `);  // replaceSync: 시트 내용을 동기적으로 교체 (즉시 반영)
  document.adoptedStyleSheets = [
    ...document.adoptedStyleSheets, sheet  // 기존 채택된 시트 배열에 새 시트 추가
  ];  // adoptedStyleSheets에 할당해야 실제 문서에 스타일 적용됨
}

function updateSheet() {  // 이미 채택된 시트의 규칙만 교체 → 재할당 불필요
  sheet.replaceSync(`
    .item {
      background: linear-gradient(135deg, #f43f5e, #fb923c);
      color: white;
      border-radius: 12px;
      transform: rotate(10deg) scale(1.15);
      box-shadow: 0 4px 15px rgba(244,63,94,0.4);
    }
  `);  // 같은 시트 객체를 갱신하면 adoptedStyleSheets에 적용된 모든 곳이 자동 반영
}

function removeSheet() {  // 문서에서 시트만 떼어내기
  document.adoptedStyleSheets =
    document.adoptedStyleSheets.filter(s => s !== sheet);  // 해당 시트만 제외한 새 배열로 재할당
}
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```html
<div id="demo-area" class="demo-area">
  <div class="item">A</div>
  <div class="item">B</div>
  <div class="item">C</div>
</div>
<button class="btn" onclick="applySheet()">Apply Constructable Sheet</button>
<button class="btn" onclick="updateSheet()">Update Sheet</button>
<button class="btn warn" onclick="removeSheet()">Remove Sheet</button>
```

```css
.demo-area { display: flex; gap: 12px; margin-bottom: 12px; }
.item { width: 60px; height: 60px; background: #e2e8f0; display: flex; align-items: center; justify-content: center; border-radius: 8px; font-weight: bold; font-size: 18px; transition: all 0.3s; }
.btn { padding: 8px 12px; border: none; background: #8b5cf6; color: white; border-radius: 4px; cursor: pointer; margin-right: 6px; font-size: 13px; }
.btn.warn { background: #ef4444; }
```

**실행 결과** — 실행하지 않음 — 브라우저 DOM API 를 쓰는 예제다 — 브라우저에서 확인한다.

**풀이 요점**
- 시트는 함수 밖에서 한 번 만들어야 세 함수가 같은 객체를 다룬다.
- `replaceSync` 는 통째 교체이므로 Apply 와 Update 의 CSS 가 서로 섞이지 않는다.
- 채택은 할당으로 하고, 스프레드로 기존 시트를 지킨다.
- Update 는 객체만 고치면 되므로 채택 목록을 다시 할당하지 않는다.
- Remove 의 `filter` 는 같은 시트를 모두 걸러 내므로 Apply 를 여러 번 눌렀어도 깨끗이 빠진다.
- 시작 코드는 CSS 를 상수로 빼 두었고 정답 코드는 `replaceSync` 안에 바로 적었다 — 하는 일은 같다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 DOM API 를 쓰는 예제다 — 브라우저에서 확인한다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

# javascript/dom-style/07 — Constructable Stylesheets — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. Apply 다음에 Update 를 누르면 (예측)

```javascript
// 질문용 발췌
const sheet = new CSSStyleSheet();
function applySheet() {
  sheet.replaceSync(`.item { background: #8b5cf6; border-radius: 50%; transform: scale(1.1); }`);
  document.adoptedStyleSheets = [...document.adoptedStyleSheets, sheet];
}
function updateSheet() {
  sheet.replaceSync(`.item { border-radius: 12px; transform: rotate(10deg) scale(1.15); }`);
}
// applySheet() → updateSheet() 차례로 부른다
```

- 마지막에 `.item` 에 걸린 규칙에는 `background: #8b5cf6` 가 남아 있는가?
- `.item` 은 둥근 원인가, 모서리가 둥근 사각형인가?

### 2. Apply 를 두 번 누른 뒤 Remove 를 누르면 (예측)

```javascript
// 질문용 발췌
applySheet();
applySheet();
document.adoptedStyleSheets =
  document.adoptedStyleSheets.filter(s => s !== sheet);
```

- 마지막 줄 뒤에 `document.adoptedStyleSheets` 안에 `sheet` 가 몇 개 남는가?

### 3. Apply 를 누르기 전에 Update 부터 누르면 (예측)

- Update 만 누른 직후 `.item` 의 겉모습은 바뀌는가?
- 이어서 Apply 를 누르면 Update 에서 넣은 규칙과 Apply 의 규칙 중 어느 것이 적용되는가?

### 4. `updateSheet` 에는 할당이 없는데도 화면이 바뀌는 까닭 (왜)

- `adoptedStyleSheets` 를 다시 할당하지 않았는데 새 규칙이 반영되는 까닭은 무엇인가?

### 5. 채택할 때 기존 배열을 펼쳐 넣는 까닭 (왜)

- `document.adoptedStyleSheets = [sheet]` 대신 `[...document.adoptedStyleSheets, sheet]` 로 쓰는 까닭은 무엇인가?

### 6. `replace()` 를 부른 바로 다음 줄 (경계)

- `sheet.replace(css)` 를 부르고 `await` 없이 다음 줄에서 새 규칙이 이미 들어갔다고 기대해도 되는가?

### 7. Remove 다음에 다시 Apply (경계)

- Remove 를 누른 뒤에도 `sheet` 객체를 다시 쓸 수 있는가, 그리고 그때 어떤 규칙이 적용되는가?

### 8. 여러 Shadow DOM 컴포넌트와 한 시트 (연결)

- 컴포넌트 열 개가 같은 스타일을 쓸 때, 컴포넌트마다 `<style>` 을 넣는 대신 시트 하나를 채택하면 무엇이 달라지는가?

## 실습

### 실습 1. 버튼 셋으로 스타일시트 붙이기 · 고치기 · 떼기

**만들 것** — 아이템 세 개(A · B · C)와 버튼 세 개가 있는 페이지에서, JS 로 만든 스타일시트 하나를 붙이고, 내용을 바꾸고, 떼어 내는 세 함수를 완성한다.

**요구 조건**
1. 스크립트 맨 위에서 스타일시트 객체를 **한 번만** 만들고, 세 함수가 모두 이 객체를 쓴다.
2. `applySheet()` 는 시트 내용을 `CSS_APPLY` 로 동기적으로 교체한다.
3. `applySheet()` 는 문서가 이미 채택한 시트들을 유지한 채 이 시트를 채택 목록 맨 뒤에 덧붙인다.
4. `updateSheet()` 는 같은 시트의 내용만 `CSS_UPDATE` 로 동기적으로 교체하고, 채택 목록은 건드리지 않는다.
5. `removeSheet()` 는 채택 목록에서 이 시트만 뺀 새 배열을 채택 목록으로 다시 할당한다.

**시작 코드**

```html
<div id="demo-area" class="demo-area">
  <div class="item">A</div>
  <div class="item">B</div>
  <div class="item">C</div>
</div>
<button class="btn" onclick="applySheet()">Apply Constructable Sheet</button>
<button class="btn" onclick="updateSheet()">Update Sheet</button>
<button class="btn warn" onclick="removeSheet()">Remove Sheet</button>

<style>
  .demo-area { display: flex; gap: 12px; margin-bottom: 12px; }
  .item { width: 60px; height: 60px; background: #e2e8f0; display: flex; align-items: center; justify-content: center; border-radius: 8px; font-weight: bold; font-size: 18px; transition: all 0.3s; }
  .btn { padding: 8px 12px; border: none; background: #8b5cf6; color: white; border-radius: 4px; cursor: pointer; margin-right: 6px; font-size: 13px; }
  .btn.warn { background: #ef4444; }
</style>

<script>
  // 시트에 넣을 CSS — 미리 채워 둔 꾸밈 값
  const CSS_APPLY = `
    .item {
      background: #8b5cf6;
      color: white;
      border-radius: 50%;
      transform: scale(1.1);
      box-shadow: 0 4px 15px rgba(139,92,246,0.4);
    }
  `;
  const CSS_UPDATE = `
    .item {
      background: linear-gradient(135deg, #f43f5e, #fb923c);
      color: white;
      border-radius: 12px;
      transform: rotate(10deg) scale(1.15);
      box-shadow: 0 4px 15px rgba(244,63,94,0.4);
    }
  `;

  // TODO: 스타일시트 객체를 하나 만든다

  function applySheet() {
    // TODO: 시트 내용을 CSS_APPLY 로 동기 교체
    // TODO: 기존 채택 시트를 유지한 채 이 시트를 덧붙여 채택
  }

  function updateSheet() {
    // TODO: 같은 시트의 내용만 CSS_UPDATE 로 교체 (채택 목록은 그대로)
  }

  function removeSheet() {
    // TODO: 이 시트만 뺀 새 배열을 채택 목록으로 다시 할당
  }
</script>
```

**확인 방법** — 브라우저로 열어 Apply → Update → Remove 를 차례로 누르며 아이템 모양이 바뀌었다가 처음으로 돌아오는지 본다.
개발자 도구 콘솔에서 단계마다 `document.adoptedStyleSheets.length` 를 찍어 시트가 들어가고 빠지는지 확인한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

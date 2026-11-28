# css/selectors/59 — || 열 결합자 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 원본 예제에서 칠해지는 셀 (예측)

```html
<!-- 질문용 발췌 -->
<colgroup>
  <col class="highlight-col" />
  <col />
</colgroup>
<tr><td>A1</td><td>B1</td></tr>
<tr><td>A2</td><td>B2</td></tr>
<!-- CSS: .col-demo .highlight-col { background: #dbeafe; } -->
```

- 연한 파란 배경으로 보이는 셀은 어느 것들인가?

### 2. 선택자가 `<col>` 을 골랐는데 셀이 칠해져 보이는 까닭 (왜)

- `.col-demo .highlight-col` 이 매칭하는 것은 `<td>` 가 아닌데, 왜 화면에서는 셀이 강조된 것처럼 보이나?

### 3. 자손 결합자로 열의 셀을 못 고르는 까닭 (왜)

- `col.highlight-col td` 는 왜 아무 셀도 고르지 못하나?

### 4. 미지원 브라우저와 쉼표 목록 (예측)

```css
/* 질문용 발췌 — 브라우저가 || 를 해석하지 못한다고 하자 */
col.price || td, .note { color: red; }
```

- 이 브라우저에서 `.note` 요소의 글자는 빨간색이 되나?

### 5. `<col>` 에 준 글자색 (경계)

- `<col class="x">` 에 `color: red` 를 주면, 그 열 셀의 글자가 빨간색으로 물려 내려가나?

### 6. `:nth-child()` 로 열을 흉내 낼 때의 한계 (경계)

- `td:nth-child(2)` 가 「두 번째 열」을 고른다는 가정은 어떤 표에서 깨지나?

### 7. `||` 와 다른 결합자의 차이 (연결)

- 공백 · `>` · `+` 결합자와 비교하면, `||` 가 따라가는 관계는 무엇이 다른가?

## 실습

### 실습 1. 2×2 표에서 첫 열만 강조하기

**만들 것** — 두 행 두 열 표를 만들고, `||` 대신 `<col>` 에 클래스를 달아 첫 열만 배경으로 강조한다.

**요구 조건**
1. 표에 `col-demo` 클래스를 단다.
2. 표 안에 `<colgroup>` 을 두고, 그 안에 `<col>` 두 개로 두 열을 정의한다.
3. 첫 번째 `<col>` 에만 `highlight-col` 클래스를 단다.
4. 두 행에 셀 `A1` · `B1` 과 `A2` · `B2` 를 넣는다.
5. 표의 이웃한 셀 테두리를 하나로 합친다.
6. 표 안의 `highlight-col` 클래스 요소를 고르는 선택자로 강조 배경 규칙을 완성한다.
7. 열 결합자 `||` 는 쓰지 않는다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>열 강조</title>
<style>
  .col-demo {
    /* TODO: 이웃한 셀 테두리를 합친다 */
    width: 200px;
  }
  .col-demo td {
    padding: 10px;
    border: 1px solid #e5e7eb;
    text-align: center;
  }
  /* TODO: 표 안의 강조 열(col)을 고르는 선택자 */ {
    background: #dbeafe;
  }
</style>
</head>
<body>
  <!-- TODO: 표에 클래스 달기 -->
  <table>
    <!-- TODO: colgroup 과 col 두 개, 첫 col 에 클래스 -->
    <tr><td>A1</td><td>B1</td></tr>
    <tr><td>A2</td><td>B2</td></tr>
  </table>
</body>
</html>
```

**확인 방법** — 브라우저로 열어 A1 · A2 가 있는 왼쪽 열만 배경이 칠해져 있고, 셀 테두리가 겹선 없이 한 줄인지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

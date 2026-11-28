# css/color-background/23 — print-color-adjust — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 두 상자를 화면에서 볼 때 (예측)

```css
/* 질문용 발췌 */
.economy { print-color-adjust: economy; background: #3b82f6; color: white; }
.exact   { print-color-adjust: exact;   background: linear-gradient(135deg, #f43f5e, #8b5cf6); color: white; }
```

- 인쇄하지 않고 브라우저 화면으로만 볼 때, 두 상자의 배경 표시는 어떻게 다른가?

### 2. 인쇄 미리보기에서 `economy` 상자의 배경 (예측)

- 위 `.economy` 상자를 인쇄 미리보기로 보면 파란 배경이 어떻게 되는가?

### 3. 부모에만 값을 적었을 때 (예측)

```html
<!-- 질문용 발췌 -->
<table style="print-color-adjust: exact">
  <tr><td style="background: red">위험</td></tr>
</table>
```

- `<td>` 에는 `print-color-adjust` 를 적지 않았다면, 이 칸을 인쇄할 때 적용되는 값은 무엇인가?

### 4. 기본값이 `exact` 가 아니라 `economy` 인 까닭 (왜)

- 브라우저가 기본으로 배경을 손봐도 되게 해 둔 까닭은 무엇인가?

### 5. 표준 이름과 함께 `-webkit-print-color-adjust` 도 적는 까닭 (왜)

- 표준 이름이 있는데도 접두사 붙은 옛 이름을 함께 적는 까닭은 무엇인가?

### 6. `economy` 에서 배경이 꼭 사라지나 (경계)

- `economy` 를 적은 요소는 인쇄 때 배경이 반드시 제거된다고 말할 수 있는가?

### 7. `economy` 에서 `exact` 로 부드럽게 바꾸기 (경계)

- `transition` 으로 `print-color-adjust` 값을 서서히 바꾸는 효과를 만들 수 있는가?

### 8. 그라디언트 배경과 `exact` (연결)

- `background: linear-gradient(...)` 로 만든 배경은 `exact` 가 지키는 「배경색/이미지」 가운데 어느 쪽에 드는가?

## 실습

### 실습 1. 인쇄 때 다르게 다뤄지는 두 상자 만들기

**만들 것** — 인쇄 최적화를 허용하는 상자와 화면 그대로 인쇄되는 상자를 하나씩 둔 페이지를 만든다.

**요구 조건**
1. 본문에 상자 두 개를 위아래로 둔다.
2. 첫 상자는 클래스 `economy` 이고 글은 「economy: 인쇄 시 브라우저가 최적화」다.
3. 둘째 상자는 클래스 `exact` 이고 글은 「exact: 화면 그대로 인쇄」다.
4. `.economy` 규칙에서 인쇄 최적화를 허용하는 값을 명시한다.
5. `.exact` 규칙에서 작성한 색을 그대로 인쇄하게 하는 값을 적는다.
6. 꾸밈(배경 · 글자색 · 여백 · 모서리 · 굵기)은 시작 코드에 있는 그대로 둔다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>print-color-adjust 연습</title>
<style>
  .economy {
    /* TODO: 인쇄 때 브라우저가 배경을 조정·제거해도 되게 하는 줄 */
    background: #3b82f6;
    color: white;
    padding: 16px;
    margin-bottom: 8px;
    border-radius: 8px;
    font-weight: bold;
  }
  .exact {
    /* TODO: 인쇄 때 작성한 색을 그대로 내보내게 하는 줄 */
    background: linear-gradient(135deg, #f43f5e, #8b5cf6);
    color: white;
    padding: 16px;
    border-radius: 8px;
    font-weight: bold;
  }
</style>
</head>
<body>
  <!-- TODO: economy 상자 -->
  <!-- TODO: exact 상자 -->
</body>
</html>
```

**확인 방법** — 브라우저로 열어 두 상자가 색을 띤 채 위아래로 놓였는지 본 뒤, 인쇄 미리보기를 열어 두 상자의 배경이 어떻게 다뤄지는지 비교한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

# css/box-model/42 — border-left-color — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 색을 적지 않은 왼쪽 테두리 (예측)

```css
/* 질문용 발췌 */
.a { color: blue; border-left: 4px solid; }
```

- 이 요소의 왼쪽 테두리는 무슨 색으로 그려지나?

### 2. 개별 속성 다음에 단축 속성 (예측)

```css
/* 질문용 발췌 */
.b { color: black; border-left-color: red; border-left: 4px solid; }
```

- 이 요소의 왼쪽 테두리는 무슨 색인가?

### 3. 색만 준 요소 (예측)

```css
/* 질문용 발췌 */
.c { border-left-color: red; padding: 16px; }
```

- 이 요소의 왼쪽에는 무엇이 보이나?

### 4. 글자색만 바꿨는데 테두리 색이 바뀌는 까닭 (왜)

- 테두리 색을 정하지 않은 요소에서 `color` 만 바꿨더니 왼쪽 테두리 색도 바뀌었다 — 왜 그런가?

### 5. 원본 예제가 단축 속성을 먼저 쓰는 까닭 (왜)

- 원본 예제가 `border-left: 4px solid;` 를 먼저 쓰고 `border-left-color` 를 그 뒤에 쓰는 까닭은 무엇인가?

### 6. 부모에만 준 테두리 색 (경계)

- 부모에 `border-left-color: red` 를, 자식에는 `border-left: 2px solid` 만 주면 자식의 왼쪽 테두리 색은 무엇을 따라가나?

### 7. `border-left-color` 와 `border-color` · `transition` (연결)

- 왼쪽 강조 줄의 색만 hover 때 서서히 바꾸려면 `border-color` 대신 `border-left-color` 를 고르고 무엇과 짝지으면 되나?

## 실습

### 실습 1. 왼쪽 강조 줄이 있는 상자 만들기

**만들 것** — 글자 한 줄이 든 상자에 왼쪽 테두리만 긋고, 그 색을 별도 속성으로 빨갛게 칠한다.

**요구 조건**

1. `box` 클래스의 `div` 하나에 `border-left-color` 라는 글자를 넣는다.
2. 왼쪽 테두리는 단축 속성 `border-left` 로 두께와 선 모양(실선)만 정하고, 색은 적지 않는다.
3. 왼쪽 테두리의 색은 `border-left-color` 로 따로, 빨간 계열 색으로 정한다.
4. 개별 속성이 단축 속성에 덮이지 않도록 선언 차례를 맞춘다.
5. 다른 세 변에는 테두리를 두지 않는다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>border-left-color</title>
<style>
  .box {
    /* TODO: 왼쪽 테두리 — 두께 4px 실선, 색은 쓰지 않는다 */
    /* TODO: 왼쪽 테두리 색만 #ef4444 로 따로 지정한다 */
    padding: 16px;
    background: #f8fafc;
  }
</style>
</head>
<body>
  <!-- TODO: box 클래스의 div 하나 -->
</body>
</html>
```

**확인 방법** — 브라우저로 열어 옅은 배경 상자의 왼쪽에만 빨간 세로줄이 있는지 본다. 두 TODO 줄의 차례를 바꿔 색이 글자색으로 돌아가는지도 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

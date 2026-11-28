# css/box-model/40 — border-right-color — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 단축 속성 다음에 색을 쓰면 (예측)

```css
/* 질문용 발췌 */
.box { color: black; border-right: 4px solid; border-right-color: #ef4444; }
```

- 이 박스의 오른쪽 테두리는 무슨 색인가?
- 위 · 아래 · 왼쪽 변에는 테두리가 있는가?

### 2. 순서를 뒤집으면 (예측)

```css
/* 질문용 발췌 */
.box { color: navy; border-right-color: #ef4444; border-right: 4px solid; }
```

- 이 박스의 오른쪽 테두리는 무슨 색인가?

### 3. 색만 지정한 박스 (예측)

```css
/* 질문용 발췌 */
.box { border-right-color: #ef4444; padding: 16px; }
```

- 이 박스의 오른쪽에 빨간 선이 보이는가?

### 4. 색을 지정하지 않은 테두리가 글자색이 되는 까닭 (왜)

- `border-right: 4px solid` 만 쓴 테두리가 글자색으로 칠해지는 까닭은 무엇인가?

### 5. 부모에 준 오른쪽 테두리 색 (경계)

- 부모에 `border-right-color` 를 주면 자식의 오른쪽 테두리 색도 그 색이 되는가?

### 6. `border-color` 와 `border-right-color` 의 범위 (연결)

- `border-color` 단축 속성과 비교하면 `border-right-color` 가 바꾸는 범위는 어디까지인가?

### 7. 글자색이 바뀔 때 기본값 테두리 (연결)

- 색을 지정하지 않은 오른쪽 테두리를 가진 요소에서 `:hover` 로 `color` 만 바꾸면 테두리 색은 어떻게 되는가?

### 8. 마우스를 올리면 오른쪽 색이 서서히 바뀌게 (경계)

- `border-right-color` 를 `transition` 으로 한 색에서 다른 색으로 부드럽게 바꿀 수 있는가?

## 실습

### 실습 1. 오른쪽 테두리만 빨간 박스 만들기

**만들 것** — 오른쪽에만 테두리가 있고, 그 테두리의 색을 `border-right-color` 로 따로 정한 박스 하나.

**요구 조건**
1. `.box` 에 `border-right` 단축 속성으로 오른쪽 테두리의 두께와 실선 모양만 주고, 색은 적지 않는다.
2. 그다음 줄에 `border-right-color` 로 오른쪽 테두리 색만 따로 정한다(값은 시작 코드 주석에 있다).
3. 두 줄의 순서를 지켜, 단축 속성이 색을 덮어쓰지 않게 한다.
4. 박스 안에는 글자 `border-right-color` 가 들어간다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>border-right-color</title>
<style>
  .box {
    /* TODO: 오른쪽 테두리 단축 — 두께 4px, 실선, 색은 생략 */
    /* TODO: 오른쪽 테두리 색만 따로 — #ef4444 */
    padding: 16px;
    background: #f8fafc;
  }
</style>
</head>
<body>
  <div class="box">border-right-color</div>
</body>
</html>
```

**확인 방법** — 파일을 브라우저로 열어 박스 오른쪽에만 빨간 세로줄이 있는지 본다. 두 TODO 줄의 순서를 바꿔 다시 열어 보고 색이 어떻게 달라지는지 비교한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

# css/layout/37 — column-rule — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 3단 컨테이너의 세로선 개수와 자리 (예측)

```css
/* 질문용 발췌 */
.multicol { column-count: 3; column-gap: 20px; column-rule: 2px solid #3b82f6; }
```

- 화면에 세로 구분선은 몇 개 그려지고, 각 선은 열 간격의 어디에 놓이는가?

### 2. 두께와 색만 준 구분선 (예측)

```css
/* 질문용 발췌 */
.multicol { column-count: 2; column-gap: 20px; column-rule: 4px #ef4444; }
```

- 이 컨테이너의 열 사이에 빨간 선이 보이는가?

### 3. 색을 뺀 구분선의 색 (예측)

- `color: #334155` 인 다단 컨테이너에 `column-rule: 1px dashed;` 만 주면 선은 무슨 색인가?

### 4. 구분선을 넣어도 열 너비가 그대로인 까닭 (왜)

- `column-rule` 을 새로 넣었는데 열 너비와 열 간격이 전혀 바뀌지 않는 이유는 무엇인가?

### 5. 값의 순서를 바꿔 쓰기 (경계)

- `column-rule: solid #3b82f6 2px;` 처럼 세 값의 순서를 바꿔 써도 같은 선이 되는가?

### 6. 안쪽 문단에 건 구분선 (경계)

- 다단 컨테이너 대신 그 안의 `p` 에만 `column-rule` 을 걸면 바깥 컨테이너의 열 사이에 선이 생기는가?

### 7. `border` 와의 차이 (연결)

- `border: 2px solid #3b82f6;` 와 `column-rule: 2px solid #3b82f6;` 는 값의 꼴이 닮았는데, 공간을 다루는 방식은 어떻게 다른가?

### 8. 선과 글 사이를 더 띄우려면 (연결)

- 구분선과 양옆 글자 사이를 더 넓히고 싶을 때 손댈 속성은 `column-rule` 의 두께인가, 다른 속성인가?

## 실습

### 실습 1. 세 열로 나눈 문단에 파란 구분선 긋기

**만들 것** — 문단 하나를 세 열로 나누고, 열 사이 간격 한가운데에 구분선을 그리는 페이지를 만든다.

**요구 조건**
1. `.multicol` 안의 문단이 세 열로 나뉘어 흐른다.
2. 열과 열 사이에 간격을 둔다 (값은 시작 코드의 TODO 주석에 있다).
3. 단축 속성 하나로 구분선의 두께 · 스타일 · 색을 한 번에 정한다 (값은 시작 코드의 TODO 주석에 있다).
4. 구분선은 열을 만든 `.multicol` 에 건다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>column-rule 연습</title>
<style>
  .multicol {
    /* TODO: 열 개수 3 */
    /* TODO: 열 간격 20px */
    /* TODO: 구분선 — 두께 2px, 실선, 색 #3b82f6 을 단축 속성 한 줄로 */
    background: #f1f5f9;
    padding: 16px;
    border-radius: 4px;
  }
  p {
    margin: 0;
  }
</style>
</head>
<body>
<div class="multicol">
  <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam.</p>
</div>
</body>
</html>
```

**확인 방법** — 브라우저로 열어 글이 세 열로 나뉘고, 열 사이 두 곳에 파란 세로선이 간격 한가운데에 있는지 본다. `column-rule` 줄을 지웠다 다시 넣어도 열 너비가 그대로인지 비교한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

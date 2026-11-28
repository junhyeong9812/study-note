# css/layout/42 — column-fill — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 높이 있는 3단에 `auto` 와 짧은 글 (예측)

```css
/* 질문용 발췌 */
.box { column-count: 3; column-fill: auto; height: 120px; }
/* 안에는 한 문장짜리 단락 하나 */
```

- 둘째 열과 셋째 열에는 무엇이 놓이나?

### 2. 높이를 지운 `auto` (예측)

```css
/* 질문용 발췌 */
.box { column-count: 3; column-fill: auto; }
/* 안에는 한 문장짜리 단락 하나 */
```

- 이 컨테이너의 열 채우기는 어느 값과 같은 모습이 되나?

### 3. 원본 예제의 설정을 바꾸면 (예측)

- 원본 예제에서 `column-fill: balance` 만 `auto` 로 바꾸면 글은 몇 번째 열들에 놓이나?

### 4. `auto` 가 높이를 필요로 하는 까닭 (왜)

- `column-fill: auto` 는 왜 컨테이너에 높이가 있어야 `balance` 와 다르게 동작하나?

### 5. 원본 예제의 문장과 설정이 어긋나는 까닭 (왜)

- 원본 예제의 문장이 말하는 「열이 고르게 차지 않는 모습」이 화면에 나오지 않는 까닭은 무엇인가?

### 6. `column-fill` 이 닿는 범위 (경계)

- 부모에 `column-fill: auto` 를 주면 그 안의 다단 자식 요소도 `auto` 가 되나?
- `auto` 에서 `balance` 로 바꿀 때 `transition` 으로 부드럽게 옮길 수 있나?
- `balance-all` 은 지금 믿고 쓸 수 있는 값인가?

### 7. 다른 다단 속성과의 관계 (연결)

- `column-count` 없이 `column-fill` 만 준 요소에서는 왜 값을 바꿔도 차이가 보이지 않나?
- `column-fill` 을 바꾸면 열 사이 간격이나 구분선도 바뀌나?

## 실습

### 실습 1. 짧은 글을 세 열에 고르게 펼치기

**만들 것** — 고정 높이의 다단 컨테이너 안에 짧은 문장 하나를 넣고, 그 문장이 세 열에 고르게 나뉘도록 만든다.

**요구 조건**
1. `.multicol` 을 세 개의 열을 가진 다단 컨테이너로 만든다.
2. 콘텐츠가 세 열에 균등하게 배분되도록 열 채우기 방식을 명시한다(기본값이지만 직접 적는다).
3. 컨테이너가 시작 코드에 채워 둔 고정 높이를 유지한다.
4. 단락의 기본 바깥 여백을 없앤다.
5. 컨테이너 안에는 짧은 영어 문장 하나를 담은 단락 하나만 둔다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>column-fill 연습</title>
<style>
  .multicol {
    /* TODO: 열을 세 개로 만든다 */
    /* TODO: 열에 고르게 배분하도록 채우기 방식을 적는다 */
    height: 120px;                   /* 고정 높이 — 지우지 않는다 */
    column-gap: 20px;
    column-rule: 1px solid #cbd5e1;
    background: #f1f5f9;
    padding: 16px;
    border-radius: 4px;
  }
  p {
    /* TODO: 기본 바깥 여백을 없앤다 */
  }
</style>
</head>
<body>
<div class="multicol">
  <p>Short text content that doesn't fill all columns evenly.</p>
</div>
</body>
</html>
```

**확인 방법** — 브라우저로 열어 문장이 세 열에 나뉘어 놓이는지 본다.
이어서 채우기 방식을 `auto` 로 바꿔 문장이 첫 열에만 몰리는지 견주어 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

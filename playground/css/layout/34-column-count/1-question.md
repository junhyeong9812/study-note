# css/layout/34 — column-count — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 문단 하나에 `column-count: 3` (예측)

```css
/* 질문용 발췌 */
.multicol { column-count: 3; column-gap: 20px; }
p { margin: 0; }
```

- `.multicol` 안에 긴 문단 하나가 있을 때, 글의 첫 부분과 둘째 부분은 화면의 어느 자리에 놓이나?

### 2. 넓은 컨테이너에 `column-width` 와 `column-count` 를 함께 (예측)

```css
/* 질문용 발췌 — 컨테이너 안쪽 너비는 1000px 이라 하자 */
.box { column-width: 200px; column-count: 2; }
```

- 이 컨테이너에는 열이 몇 개 생기나?

### 3. 아무것도 정하지 않은 다단 속성 (예측)

```css
/* 질문용 발췌 */
.box { column-count: auto; }
```

- 다른 다단 속성이 하나도 없다면, `.box` 의 내용은 몇 열로 놓이나?

### 4. `column-width` 와 함께 쓰면 `column-count` 가 최대 열 수가 되는 까닭 (왜)

- 왜 이 조합에서는 `column-count` 가 「정확한 열 수」가 아니라 「최대 열 수」로 동작하나?

### 5. 열 수를 바꿔도 HTML 은 그대로인 까닭 (왜)

- 2열을 4열로 바꿀 때 왜 문단을 나누는 HTML 수정이 필요 없나?

### 6. 받을 수 있는 값의 범위 (경계)

- `column-count: 0` 이나 `column-count: 2.5` 처럼 쓰면 어떻게 되나?

### 7. 자식 요소까지 다단이 되나 (경계)

- 3열 컨테이너 안의 자식 `div` 는 그 안의 내용을 다시 3열로 나누나?

### 8. 격자 3열과 다단 3열의 차이 (연결)

- 카드 여섯 장을 순서대로 놓을 때, 다단 3열과 격자 3열은 카드 읽는 순서가 어떻게 다른가?

## 실습

### 실습 1. 문단 하나를 3단으로 흘리기

**만들 것** — 문단 하나를 담은 회색 상자를 만들고, 그 글이 세 열로 나뉘어 흐르게 한다.

**요구 조건**
1. `.multicol` 컨테이너 안의 문단이 세 열로 나뉘어 흐른다.
2. 열과 열 사이에 간격을 둔다(값은 시작 코드 주석에 적힌 값).
3. 문단의 기본 바깥 여백을 없애, 글이 컨테이너의 안쪽 여백 바로 안에서 시작하게 한다.
4. 컨테이너의 배경 · 안쪽 여백 · 둥근 모서리는 시작 코드에 채워진 그대로 둔다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>column-count 연습</title>
<style>
  .multicol {
    /* TODO: 내용을 3개 열로 나눈다 */
    /* TODO: 열 사이 간격 20px */
    background: #f1f5f9;
    padding: 16px;
    border-radius: 4px;
  }
  p {
    /* TODO: 단락 기본 바깥 여백 제거 */
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

**확인 방법** — 브라우저로 열어 문단이 세 열로 나뉘어 왼쪽 열부터 위→아래로 이어지는지, 열 사이에 간격이 있는지 본다. 창 너비를 바꿔도 열이 3개인지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

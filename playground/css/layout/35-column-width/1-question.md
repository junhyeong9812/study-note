# css/layout/35 — column-width — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 기준보다 좁은 컨테이너 (예측)

```css
/* 질문용 발췌 */
.box { width: 120px; column-width: 150px; column-gap: 20px; }
```

- 이 상자의 글은 몇 열로 나뉘고, 그 열의 폭은 150px 과 견주어 어떤가?

### 2. 창을 넓혀 갈 때 (예측)

```css
/* 질문용 발췌 */
.multicol { column-width: 150px; column-gap: 20px; }  /* 폭은 창 크기를 따른다 */
```

- 창을 아주 좁은 폭에서 아주 넓은 폭까지 천천히 넓히면 열 수와 각 열의 폭은 어떻게 달라지나?

### 3. 「최소 너비」라 부르지 않는 까닭 (왜)

- `column-width` 의 값을 「최소 너비」가 아니라 「이상적 너비」라고 부르는 까닭은 무엇인가?

### 4. 열 수 대신 열 너비로 정하는 까닭 (왜)

- 열 수를 고정하지 않고 `column-width` 로 열 너비를 정하면 화면 폭이 다양할 때 무엇이 좋은가?

### 5. 0 이나 음수 (경계)

- `column-width: -100px` 처럼 양수가 아닌 길이를 주면 그 상자의 열 너비는 어떻게 정해지나?

### 6. 부모에 준 `column-width` (경계)

- 바깥 `div` 에 `column-width` 를 주면 그 안의 자식 `div` 내용도 저절로 다단으로 나뉘나?

### 7. `auto` 일 때의 주인 (연결)

- `column-width` 가 기본값 `auto` 일 때 열 너비를 정하는 것은 무엇인가?

### 8. `column-gap` 과의 관계 (연결)

- `column-gap` 을 크게 늘리면 같은 컨테이너 폭에서 들어가는 열 수에 어떤 영향이 가나?

## 실습

### 실습 1. 폭에 따라 열 수가 바뀌는 글 상자

**만들 것** — 문단 하나를 담은 상자를, 열 수를 직접 정하지 않고 이상적 열 너비만으로 여러 열에 흘려 보낸다.

**요구 조건**
1. `.multicol` 상자 안의 문단이 이상적 열 너비를 기준으로 여러 열로 나뉜다 — 열 수는 적지 않는다.
2. 열과 열 사이에 간격을 둔다.
3. 문단의 기본 바깥 여백을 없애 첫 열 머리에 빈 띠가 생기지 않게 한다.
4. 상자의 배경 · 안쪽 여백 · 둥근 모서리는 시작 코드에 이미 있으니 그대로 둔다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>column-width 실습</title>
<style>
  .multicol {
    /* TODO: 이상적 열 너비를 150px 로 */
    /* TODO: 열 간격을 20px 로 */
    background: #f1f5f9;
    padding: 16px;
    border-radius: 4px;
  }
  p {
    /* TODO: 문단의 기본 바깥 여백 없애기 */
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

**확인 방법** — 브라우저로 열고 창 폭을 좁혔다 넓혔다 하며 열 수가 바뀌는지, 첫 열 위에 빈 띠가 없는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

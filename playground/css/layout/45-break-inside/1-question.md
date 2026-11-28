# css/layout/45 — break-inside — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 긴 카드 1 이 든 2단 컨테이너 (예측)

```css
/* 질문용 발췌 — HTML 은 .multicol 안에 .card 셋, 카드 1 이 가장 길다 */
.multicol { column-count: 2; column-gap: 16px; }
.card { padding: 12px; margin-bottom: 8px; }
```

- `.card` 에 `break-inside` 를 주지 않았을 때 카드 1 이 두 열에 걸쳐 놓일 수 있는가?

### 2. 같은 코드에 `.card { break-inside: avoid; }` 를 더하면 (예측)

- 1번 코드에 이 한 줄을 더하면 카드 1 은 어떻게 놓이는가?

### 3. 컨테이너에만 건 `avoid` (경계)

- `.card` 대신 `.multicol` 에만 `break-inside: avoid` 를 걸면 카드가 열 경계에서 잘리는 것을 막을 수 있는가?

### 4. `avoid-column` 을 준 카드를 인쇄할 때 (경계)

- `break-inside: avoid-column` 만 준 카드는 인쇄할 때 페이지 경계에서도 잘리지 않는가?

### 5. 이미지와 캡션을 한 요소로 감싸는 까닭 (왜)

- 이미지와 캡션이 떨어지지 않게 하려면 왜 둘을 한 요소로 감싸고 그 요소에 `avoid` 를 걸어야 하는가?

### 6. `transition` 으로 바꾸는 `break-inside` (경계)

- `transition` 을 걸고 `break-inside` 를 `auto` 에서 `avoid` 로 바꾸면 배치가 서서히 바뀌는가?

### 7. `column-count` 와 `break-inside` 의 역할 나눔 (연결)

- 다단 레이아웃에서 끊을 자리를 만드는 속성과 그 자리를 피하라고 말하는 속성은 각각 어느 요소에 걸리는가?

## 실습

### 실습 1. 카드가 잘리지 않는 2단 레이아웃 만들기

**만들 것** — 카드 세 개를 두 열로 흘려 놓되, 어떤 카드도 두 열에 걸쳐 잘리지 않게 한다.

**요구 조건**
1. `.multicol` 컨테이너의 내용이 두 열로 나뉘어 흐른다.
2. 두 열 사이에 간격이 있다.
3. 컨테이너 안에 카드 세 개가 차례로 놓이고, 카드 1 의 글이 가장 길다.
4. 각 카드는 열 경계에서 둘로 쪼개지지 않는다.
5. 쪼개짐을 막는 규칙은 컨테이너가 아니라 카드에 건다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>break-inside 연습</title>
<style>
  .multicol {
    /* TODO: 두 열로 나눈다 */
    /* TODO: 열 사이 간격을 둔다 (예: 16px) */
    background: #f1f5f9;
    padding: 16px;
    border-radius: 4px;
  }
  .card {
    /* TODO: 카드 안쪽에서 열/페이지 나누기를 피한다 */
    background: white;
    padding: 12px;
    margin-bottom: 8px;
    border-radius: 4px;
    border: 1px solid #e2e8f0;
  }
</style>
</head>
<body>
<div class="multicol">
  <div class="card">Card 1 with longer content that should stay together.</div>
  <div class="card">Card 2 with content.</div>
  <div class="card">Card 3 with content.</div>
</div>
</body>
</html>
```

**확인 방법** — 브라우저로 열어 카드가 두 열에 나뉘어 놓이는지, 어느 카드도 열 경계에서 위아래로 잘리지 않는지 본다.
창 너비를 줄여 카드 1 이 길어지게 한 뒤에도 같은지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

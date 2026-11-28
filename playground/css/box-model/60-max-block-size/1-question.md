# css/box-model/60 — max-block-size — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 패딩이 있는 상자에 상한 60px (예측)

```css
/* 질문용 발췌 — 글은 60px 보다 훨씬 길다 */
.box { max-block-size: 60px; padding: 16px; overflow: auto; }
```

- 가로 쓰기에서 배경이 칠해지는 상자의 세로 크기는 몇 px 까지 자라는가?
- 다 보이지 않는 글은 어떻게 보게 되는가?

### 2. 세로 쓰기에서의 상한 (예측)

```css
/* 질문용 발췌 */
.box { writing-mode: vertical-rl; max-block-size: 60px; overflow: auto; }
```

- 이 상자에서 60px 상한은 너비와 높이 중 어느 쪽에 걸리는가?

### 3. `overflow` 를 지우면 (예측)

- 1번 상자에서 `overflow: auto;` 한 줄만 지우면 넘친 글은 어디에 그려지는가?

### 4. 같은 일을 하는 `max-height` 를 두고 논리 속성을 쓰는 이유 (왜)

- 가로 쓰기에서 둘이 같은데도 `max-block-size` 를 쓰는 까닭은 무엇인가?

### 5. 글이 짧을 때 (경계)

- `max-block-size: 60px` 인 상자에 한 줄짜리 짧은 글만 있으면 내용 영역은 60px 이 되는가?

### 6. 하한과 상한이 부딪치면 (경계)

- `min-block-size: 100px; max-block-size: 60px;` 를 함께 주면 블록 크기는 어떻게 정해지는가?

### 7. 부모의 상한과 자식 (경계)

- 부모에 `max-block-size` 를 주면 자식 요소에도 같은 상한이 걸리는가?

### 8. `max-inline-size` 와의 짝 (연결)

- 가로 쓰기에서 `max-inline-size` 는 어떤 물리 속성에 대응하며, `max-block-size` 와 무엇이 다른가?

## 실습

### 실습 1. 길이를 모르는 글을 상한 안에 가두기

**만들 것** — 긴 설명문 한 줄이 든 상자를 만들고, 블록 방향 크기에 상한을 걸어 넘친 글은 스크롤로 보게 한다.

**요구 조건**
1. `box` 클래스를 단 `div` 하나에 상자보다 긴 설명문을 넣는다.
2. 상자의 블록 방향 최대 크기를 물리 속성(`max-height`)이 아닌 논리 속성으로 60px 로 제한한다.
3. 내용이 상한을 넘으면 상자 안에 스크롤이 생기게 한다.
4. 배경·패딩·글자색·모서리 같은 꾸밈은 시작 코드에 있는 그대로 둔다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>max-block-size 연습</title>
<style>
.box {
  /* TODO: 블록 방향 최대 크기를 논리 속성으로 제한한다 */
  /* TODO: 넘치면 스크롤이 생기게 한다 */
  background: #3b82f6;
  padding: 16px;
  color: white;
  border-radius: 4px;
}
</style>
</head>
<body>
<div class="box">max-block-size는 블록 방향 최대 크기를 제한합니다. 넘치면 overflow에 따라 처리됩니다.</div>
</body>
</html>
```

**확인 방법** — 브라우저로 열고 창 너비를 좁혀 글이 여러 줄이 되게 한다. 상자가 일정 높이에서 멈추고 안쪽에 스크롤이 생기는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

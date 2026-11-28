# css/layout/21 — overflow-block — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 예제 상자에 긴 단락을 넣으면 (예측)

```css
/* 질문용 발췌 */
.box { overflow-block: auto; width: 200px; height: 60px; padding: 8px; }
p { margin: 0; }
/* .box 안에 여러 줄로 줄바꿈될 긴 <p> 하나 */
```

- 가로쓰기 기본 상태에서 이 상자에는 어떤 방향의 스크롤바가 생기는가?

### 2. 세로쓰기 상자에 `scroll` 을 주면 (예측)

```css
/* 질문용 발췌 */
.note { writing-mode: vertical-rl; width: 100px; overflow-block: scroll; }
```

- 이 상자의 스크롤바는 가로축과 세로축 가운데 어느 축에 생기는가?

### 3. 높이를 지운 예제 상자 (예측)

- 퀴즈 1 의 `.box` 에서 `height: 60px` 만 지우면 스크롤바는 어떻게 되는가?

### 4. `overflow-y` 가 있는데도 `overflow-block` 을 쓰는 까닭 (왜)

- 가로쓰기에서는 둘이 같은 일을 하는데, 왜 논리 속성을 따로 두는가?

### 5. 둘 다 잘라 내는 `hidden` 과 `clip` 이 나뉜 까닭 (왜)

- 화면에서는 똑같이 잘리는데 왜 두 값이 따로 있는가?

### 6. 부모에만 준 `overflow-block: hidden` (경계)

- 부모 상자에만 `overflow-block: hidden` 을 주면 그 안의 자식 상자에서 넘친 콘텐츠도 같은 규칙으로 처리되는가?

### 7. `visible` 에서 `auto` 로 부드럽게 바꾸기 (경계)

- `transition` 을 걸어 `overflow-block` 을 `visible` 에서 `auto` 로 서서히 바꿀 수 있는가?

### 8. `overflow-inline` 과의 관계 (연결)

- 가로쓰기 상자에서 `overflow-block` 과 `overflow-inline` 은 각각 어느 물리 속성의 자리를 맡는가?

## 실습

### 실습 1. 블록 방향으로만 넘겨 보는 메모 상자

**만들 것** — 고정 크기 상자 안에 긴 단락을 넣고, 블록 방향으로 넘칠 때만 스크롤바가 생기도록 논리 속성으로 넘침을 처리한다.

**요구 조건**
1. `.box` 상자는 너비와 높이가 고정되어 있어, 그 안의 긴 단락이 블록 방향으로 넘친다(크기 · 배경 · 테두리 값은 시작 코드에 있다).
2. `.box` 는 블록 방향으로 넘칠 때만 스크롤바를 보인다.
3. 넘침 처리는 물리 속성(`overflow-y`)이 아니라 블록 방향 논리 속성으로 쓴다.
4. 단락(`p`)의 기본 바깥 여백을 없애 첫 줄이 상자 안쪽 여백에 바로 붙게 한다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>overflow-block 연습</title>
<style>
  .box {
    /* TODO: 블록 방향으로 넘칠 때만 스크롤바가 생기게 한다 (논리 속성) */
    width: 200px;
    height: 60px;
    background: #f1f5f9;
    padding: 8px;
    border: 2px solid #3b82f6;
    border-radius: 4px;
  }
  p {
    /* TODO: 단락의 기본 바깥 여백을 없앤다 */
  }
</style>
</head>
<body>
<div class="box">
  <p>블록 방향으로 넘치는 긴 콘텐츠입니다. Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
</div>
</body>
</html>
```

**확인 방법** — 브라우저로 열어 상자 안에 단락 일부만 보이고 세로 스크롤로 나머지를 내려 볼 수 있는지 본다. 단락을 몇 글자로 줄여 넘치지 않게 했을 때 스크롤바가 사라지는지도 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

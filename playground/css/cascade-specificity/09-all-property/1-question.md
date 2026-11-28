# css/cascade-specificity/09 — all property — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 보통 블록 흐름 속 `h3` 에 `all: unset` (예측)

```html
<!-- 질문용 발췌 -->
<div style="font-size:16px; color:#334155;">
  <h3 style="all: unset;">제목</h3><span>뒤 글자</span>
</div>
```

- 「뒤 글자」는 「제목」과 같은 줄에 놓이나, 다음 줄로 내려가나?
- 「제목」의 글자 크기와 굵기는 어디서 온 값이 되나?

### 2. `align-self` 를 `all: revert` 앞에 적으면 (예측)

```css
/* 질문용 발췌 — .wrap 은 display: flex; flex-direction: column; 이고 align-items 는 정하지 않았다 */
.reset-btn {
  align-self: flex-start;
  all: revert;
}
```

- 이 버튼은 가로로 어떻게 놓이나?

### 3. 변수와 글 방향을 둔 요소에 `all: initial` (예측)

```css
/* 질문용 발췌 */
.theme { --accent: tomato; }
.card { direction: rtl; }
.card {
  all: initial;
  border: 2px solid var(--accent);
}
/* <div class="theme"><div class="card">…</div></div> */
```

- `.card` 의 테두리 색은 무엇이 되나?
- `.card` 의 글 방향은 어떻게 되나?

### 4. 리셋 용도로 `all: revert` 가 `all: unset` 보다 안전하다고 하는 까닭 (왜)
- 버튼에 두 키워드를 각각 주었을 때 남는 것의 차이로 설명하면 어떻게 되나?

### 5. 원본이 `cursor: text` 를 `all: unset` 뒤에 적은 까닭 (왜)
- 두 줄의 순서를 바꾸면 무엇이 달라지나?

### 6. 더 구체적인 선택자와 `all` 이 부딪칠 때 (경계)
- 같은 `h3` 에 `#title { color: red; }` 와 `.reset-heading { all: unset; }` 이 함께 걸리면 글자색은 어느 쪽 값이 되나?

### 7. 데모의 `.reset-heading` 은 정말 인라인으로 놓이나 (경계)
- flex 컨테이너의 자식인 이 제목에서 「display까지 inline으로 돌아감」이라는 주석은 화면 배치까지 맞는 말인가?

### 8. `unset` 과 상속의 관계 (연결)
- 같은 `all: unset` 아래에서 `color` 는 부모 값이 되고 `border` 는 사라지는 까닭을 상속 속성 · 비상속 속성으로 설명하면 어떻게 되나?

### 9. `revert` 와 `revert-layer` 가 물러나는 단위 (연결)
- 두 키워드는 각각 무엇을 한 단계 뒤로 돌리나?

## 실습

### 실습 1. 꾸민 요소와 `all` 로 되돌린 요소를 나란히 놓기

**만들 것** — 세로로 쌓인 데모 상자 안에 꾸민 제목 · `all: unset` 제목 · 꾸민 버튼 · `all: revert` 버튼을 차례로 두고 차이를 비교한다.

**요구 조건**
1. 데모 상자는 자식 넷을 세로로 쌓고 자식 사이에 간격을 둔다.
2. 첫 제목(`.styled-heading`)은 배경 · 왼쪽 강조선 · 큰 굵은 글자로 꾸민 제목이다.
3. 두 번째 제목(`.reset-heading`)은 한 선언으로 모든 속성을 `unset` 해 브라우저의 `h3` 기본 꾸밈까지 걷어낸다.
4. 같은 규칙에서 `all` 다음에 마우스 커서만 텍스트 커서로 다시 준다.
5. 첫 버튼(`.styled-btn`)은 파란 바탕 · 흰 글자 · 손가락 커서로 꾸미고 가로로 늘어나지 않게 시작점에 붙인다.
6. 두 번째 버튼(`.reset-btn`)은 한 선언으로 작성자 스타일을 걷어내 브라우저 기본 버튼 모양으로 되돌린다.
7. 되돌린 버튼도 가로로 늘어나지 않고 시작점에 붙도록, `all` 다음에 자체 정렬을 다시 준다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>all property 연습</title>
<style>
  .all-demo {
    padding: 20px;
    background: #f1f5f9;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .styled-heading {
    color: #1e293b;
    font-size: 24px;
    font-weight: 700;
    padding: 12px;
    background: #dbeafe;
    border-left: 4px solid #3b82f6;
    border-radius: 4px;
  }
  .reset-heading {
    /* TODO: 모든 속성을 한 번에 unset 한다 */
    /* TODO: 그 다음에 텍스트 커서만 다시 준다 */
  }
  .styled-btn {
    padding: 12px 24px;
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    align-self: flex-start;
  }
  .reset-btn {
    /* TODO: 브라우저 기본 버튼 스타일로 되돌린다 */
    /* TODO: 그 다음에 시작점 정렬을 다시 준다 */
  }
</style>
</head>
<body>
  <div class="all-demo">
    <h3 class="styled-heading">스타일된 제목 (before)</h3>
    <h3 class="reset-heading">all: unset 적용 (after)</h3>
    <button class="styled-btn">스타일된 버튼</button>
    <button class="reset-btn">all: revert 버튼</button>
  </div>
</body>
</html>
```

**확인 방법** — 파일을 브라우저로 열어, 두 번째 제목이 부모와 같은 크기의 보통 글자로 보이는지, 두 번째 버튼이 브라우저 기본 버튼 모양이면서 왼쪽 시작점에 붙어 있는지 본다. 개발자 도구에서 `.reset-btn` 의 `align-self` 를 지우거나 `all` 앞으로 옮겨 버튼이 가로로 늘어나는지도 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

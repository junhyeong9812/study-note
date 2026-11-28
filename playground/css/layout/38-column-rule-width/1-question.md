# css/layout/38 — column-rule-width — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 두께 3px 에 스타일을 쓰지 않으면 (예측)

```css
/* 질문용 발췌 */
.multicol {
  column-count: 3;
  column-rule-width: 3px;
  column-rule-color: #3b82f6;
}
```

- 열 사이에 파란 선이 보이는가?

### 2. 네 열에 실선을 주면 구분선은 몇 개 (예측)

```css
/* 질문용 발췌 */
.news {
  column-count: 4;
  column-rule: thick solid black;
}
```

- 화면에 그어지는 세로 구분선은 몇 개인가?

### 3. 두께와 스타일을 따로 둔 까닭 (왜)

- 두께 값이 있는데도 스타일이 `none` 이면 선이 안 보이는 것은 왜인가?

### 4. 음수 두께 (경계)

- `column-rule-width: -2px` 를 주면 그 선언은 어떻게 되고, 두께는 무엇이 남는가?

### 5. 두께를 전혀 주지 않을 때 (경계)

- `column-rule-style: solid` 만 주고 두께를 쓰지 않으면 선의 두께는 무엇인가?

### 6. 부모에 준 두께와 다단 자식 (경계)

- 부모에 `column-rule-width: 8px` 를 주고 자식 다단 요소에는 두께를 안 주면 자식의 선은 몇 px 짜리인가, 아니면 무엇인가?

### 7. 테두리 두께와 닮은 점 (연결)

- `column-rule-width` 와 `border-width` 는 값의 종류와 「보이려면 필요한 것」에서 어떻게 닮았는가?

### 8. 마우스를 올리면 두께를 바꾸는 규칙 (예측)

```css
/* 질문용 발췌 */
.multicol {
  column-count: 3;
  column-rule: 3px solid #3b82f6;
  transition: column-rule-width 0.3s;
}
.multicol:hover { column-rule-width: 10px; }
```

- 마우스를 올리는 순간 선의 굵기는 어떻게 변하는가?

## 실습

### 실습 1. 굵은 구분선이 있는 3단 글 상자

**만들 것** — 문단 하나를 세 열로 나누고, 열 사이에 굵은 파란 실선을 긋는다.

**요구 조건**
1. `.multicol` 안의 문단이 세 열로 나뉘어 흐른다.
2. 열 사이에 간격을 둔다 (값은 시작 코드의 TODO 주석에 있다).
3. 열 사이에 구분선이 실제로 보이도록 선의 모양을 실선으로 정한다.
4. 구분선의 두께를 키워드가 아닌 고정 길이로 정한다 (값은 TODO 주석에 있다).
5. 구분선의 색을 TODO 주석의 파란색으로 정한다.
6. 회색 배경 · 안쪽 여백 · 둥근 모서리 · 문단 마진 제거는 시작 코드에 이미 있으니 그대로 둔다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>column-rule-width 연습</title>
<style>
  .multicol {
    /* TODO: 열 3개 */
    /* TODO: 구분선 두께 3px */
    /* TODO: 구분선 모양 실선 */
    /* TODO: 구분선 색 #3b82f6 */
    /* TODO: 열 간격 20px */
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
  <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt.</p>
</div>
</body>
</html>
```

**확인 방법** — 브라우저로 열어 글이 세 열로 나뉘고 열 사이 두 곳에 굵은 파란 실선이 보이는지 본다. 모양(실선) 줄을 지웠을 때 선이 사라지는지도 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

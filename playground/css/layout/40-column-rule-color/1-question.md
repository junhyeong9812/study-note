# css/layout/40 — column-rule-color — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 구분선 색을 쓰지 않은 다단 컨테이너 (예측)

```css
/* 질문용 발췌 */
.multicol {
  column-count: 3;
  color: blue;
  column-rule-style: solid;
  column-rule-width: 2px;
}
```

- 이 요소의 열 구분선은 무슨 색으로 그려지나?

### 2. 부모에 구분선 색을 주고 자식이 다단일 때 (예측)

```css
/* 질문용 발췌 */
.outer { color: green; column-rule-color: red; }
.inner { column-count: 2; column-rule-style: solid; column-rule-width: 1px; }
```

- `.outer` 안에 든 `.inner` 의 구분선은 무슨 색인가?

### 3. 마우스를 올렸을 때의 색 바뀜 (예측)

```css
/* 질문용 발췌 */
.multicol { column-count: 3; column-rule: solid; column-rule-color: gray; transition: column-rule-color 0.3s; }
.multicol:hover { column-rule-color: red; }
```

- 마우스를 올리면 구분선 색은 회색에서 빨강으로 어떤 식으로 넘어가나?

### 4. 상속되지 않는데 「상속받는다」는 팁 (왜)

- 원본 데이터는 「상속: `False`」인데 팁은 「`color` 속성값을 상속받는다」고 한다 — 이 표현은 왜 오해를 부를 수 있나?

### 5. 기본값을 `currentcolor` 로 둔 쓸모 (왜)

- 구분선 색을 일부러 비워 두면 글자색을 바꿀 때 무엇이 편해지나?

### 6. 색만 정해서 되는 범위 (경계)

- `column-rule-color` 하나만으로 구분선의 두께나 실선 · 점선 모양까지 정할 수 있나?

### 7. 열이 나뉘지 않은 요소 (연결)

- `column-count` 없이 `column-rule-color` 만 준 요소에서 구분선을 기대할 수 없는 까닭은 열 구분선이 어디에 생기는 선이기 때문인가?

## 실습

### 실습 1. 빨간 구분선으로 나뉜 3단 글 상자 만들기

**만들 것** — 한 단락의 글을 세 열로 나누고, 열 사이에 빨간 실선 구분선을 그은 회색 상자를 만든다.

**요구 조건**
1. `.multicol` 상자의 내용이 세 열로 나뉜다.
2. 열 사이 구분선의 색을 빨강으로 정한다(값은 시작 코드 주석에 있다).
3. 구분선의 모양은 실선이다.
4. 구분선의 두께를 정한다(값은 시작 코드 주석에 있다).
5. 열과 열 사이에 간격을 둔다(값은 시작 코드 주석에 있다).
6. 단락의 기본 바깥 여백은 없앤 채로 둔다(시작 코드에 이미 있다).

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>column-rule-color 실습</title>
<style>
  .multicol {
    /* TODO: 3개 열로 나눈다 */
    /* TODO: 구분선 색 — #ef4444 */
    /* TODO: 구분선 모양 — 실선 */
    /* TODO: 구분선 두께 — 2px */
    /* TODO: 열 간격 — 20px */
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

**확인 방법** — 파일을 브라우저로 열어 글이 세 열로 나뉘고, 열 사이에 빨간 실선 두 줄이 보이는지 확인한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

# css/selectors/56 — > 자식 결합자 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 연녹색 규칙에 걸리는 `li` 의 개수 (예측)

```html
<!-- 질문용 발췌 -->
<style>
  .child-demo > li { background: #dcfce7; }
</style>
<ul class="child-demo">
  <li>직접 자식 1
    <ul><li>손자</li></ul>
  </li>
  <li>직접 자식 2</li>
</ul>
```

- 이 규칙에 매칭되는 `li` 는 몇 개이고, 어느 것인가?

### 2. 손자 규칙을 지우면 (예측)

```html
<!-- 질문용 발췌 -->
<style>
  .child-demo > li { background: #dcfce7; font-weight: bold; }
</style>
<ul class="child-demo">
  <li>직접 자식 1
    <ul><li>손자</li></ul>
  </li>
</ul>
```

- 「손자」 글자는 굵게 보이나, 보통 굵기로 보이나?
- 「손자」 줄 뒤에 보이는 색은 무엇인가?

### 3. 사이에 래퍼가 한 겹 끼면 (경계)

- `.card` 와 `p` 사이에 `section` 이 한 겹 끼어 있을 때 `.card > p` 는 그 `p` 를 고르나?

### 4. 긴 체인에서 스타일을 받는 쪽 (경계)

- `.child-demo > li > ul > li` 에서 실제로 스타일이 붙는 요소는 체인의 어느 것인가?

### 5. 정답 코드가 손자에 `font-weight: normal` 을 따로 적은 까닭 (왜)

- 손자는 `.child-demo > li` 에 매칭되지도 않는데 왜 굵기를 되돌려야 하나?

### 6. 「하위 컴포넌트 침투를 막는다」는 팁 (왜)

- `>` 가 하위 컴포넌트로의 스타일 침투를 막는 범위는 어디까지이고, 어디서 못 막나?

### 7. 띄어쓰기로 바꾸면 (연결)

- `.child-demo > li` 를 `.child-demo li` 로 바꾸면 어떤 `li` 가 새로 걸리나?

### 8. 바깥 `ul` 에만 준 값 (연결)

- `.child-demo` 에만 준 `list-style: none` 과 `padding: 0` 은 안쪽 `ul` 에도 효과가 있나?

## 실습

### 실습 1. 중첩 목록을 깊이별로 다르게 꾸미기

**만들 것** — 바깥 목록의 직접 자식과 그 안의 손자를 `>` 결합자만으로 구분해 서로 다르게 꾸민다.

**요구 조건**
1. 시작 코드의 HTML 구조(바깥 `ul.child-demo` 아래 `li` 두 개, 첫 `li` 안에 `ul` 과 손자 `li` 하나)를 그대로 쓴다.
2. `.child-demo` 목록의 기본 마커를 없애고 안쪽 여백을 0 으로 한다.
3. `.child-demo` 의 직계 자식 `li` 만 고르는 선택자를 써서 시작 코드에 준비된 카드 꾸밈(배경 · 여백 · 둥근 모서리 · 굵게)을 적용한다.
4. 직계 자식 `li` 의 직계 자식 `ul` 을 고르는 선택자를 써서 준비된 위쪽 여백을 적용한다.
5. 3단계 직계 체인으로 손자 `li` 를 골라 준비된 회색 배경을 적용하고, 물려받은 굵기를 보통 굵기로 되돌린다.
6. 띄어쓰기(자손 결합자)는 쓰지 않고 `>` 만 쓴다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>자식 결합자 연습</title>
<style>
  .child-demo {
    /* TODO: 기본 리스트 마커 제거 */
    /* TODO: 안쪽 여백 0 */
  }
  /* TODO: 아래 .todo-1 을 ".child-demo 의 직계 자식 li" 선택자로 바꾼다 */
  .todo-1 {
    padding: 10px;
    background: #dcfce7;
    margin: 4px 0;
    border-radius: 6px;
    font-weight: bold;
  }
  /* TODO: 아래 .todo-2 를 "직계 자식 li 의 직계 자식 ul" 선택자로 바꾼다 */
  .todo-2 {
    margin-top: 8px;
  }
  /* TODO: 아래 .todo-3 을 3단계 직계 체인의 손자 li 선택자로 바꾼다 */
  .todo-3 {
    background: #f3f4f6;
    /* TODO: 물려받은 굵기를 되돌린다 */
  }
</style>
</head>
<body>
  <ul class="child-demo">
    <li>직접 자식 1
      <ul>
        <li>손자</li>
      </ul>
    </li>
    <li>직접 자식 2</li>
  </ul>
</body>
</html>
```

**확인 방법** — 파일을 브라우저로 열어 「직접 자식 1 · 2」는 굵은 연녹색 카드, 「손자」는 보통 굵기의 회색 띠로 보이는지 본다. 목록 마커가 하나도 없어야 한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

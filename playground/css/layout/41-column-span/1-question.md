# css/layout/41 — column-span — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 스패너 뒤 문단이 시작하는 자리 (예측)

```css
/* 질문용 발췌 */
.multicol { column-count: 3; }
.spanning { column-span: all; }
/* HTML 차례: <p>A</p> <h3 class="spanning">제목</h3> <p>B</p> */
```

- 문단 B 의 첫 줄은 어느 열의 어느 높이에서 시작하나?

### 2. `column-span` 을 빼면 (예측)

```css
/* 질문용 발췌 */
.multicol { column-count: 3; }
.spanning { /* column-span 줄을 지웠다 */ background: #3b82f6; }
/* HTML 차례: <p>A</p> <h3 class="spanning">제목</h3> <p>B</p> */
```

- 제목 띠의 가로 폭은 무엇의 폭과 같아지나?

### 3. 섹션 제목에 이 속성이 쓸모 있는 까닭 (왜)
- 여러 섹션으로 된 다단 글에서 각 섹션 제목에 `column-span: all` 을 주면 읽기가 왜 나아지나?

### 4. 컨테이너가 아니라 안쪽 요소에 거는 까닭 (왜)
- `column-count` 는 컨테이너에 거는데 `column-span` 은 왜 안쪽 요소에 거나?

### 5. 두 열만 걸치려는 시도 (경계)
- `column-span: 2` 라고 쓰면 그 요소는 어떻게 배치되나?

### 6. 켜고 끄기에 `transition` 을 걸면 (경계)
- `column-span` 을 `none` 에서 `all` 로 바꿀 때 `transition` 으로 중간 단계를 볼 수 있나?

### 7. 부모가 가로지를 때의 자식 (연결)
- 부모에 `column-span: all` 을 걸면 자식의 `column-span` 계산값은 무엇이고, 자식은 왜 그래도 넓게 보이나?

### 8. 다단 컨테이너 밖의 요소 (연결)
- `column-count` 가 걸리지 않은 평범한 `div` 안의 제목에 `column-span: all` 을 주면 무엇이 달라지나?

## 실습

### 실습 1. 다단 글을 가로지르는 제목 만들기

**만들 것** — 문단 · 제목 · 문단으로 된 상자를 세 열로 나누고, 제목만 모든 열을 가로지르게 해서 내용을 위아래로 나눈다.

**요구 조건**
1. `.multicol` 컨테이너의 내용이 세 개의 열로 나뉘어 흐른다.
2. 열과 열 사이에 간격이 있다(간격 값은 시작 코드에 채워져 있다).
3. 제목 `h3.spanning` 은 열 하나에 갇히지 않고 모든 열을 가로지른다.
4. 그 결과 첫 문단은 제목 위의 열들에, 둘째 문단은 제목 아래의 새 열들에 놓인다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>column-span 연습</title>
<style>
  .multicol {
    /* TODO: 열 3개로 나눈다 */
    column-gap: 20px;
    background: #f1f5f9;
    padding: 16px;
    border-radius: 4px;
  }
  .spanning {
    /* TODO: 모든 열을 가로지르게 한다 */
    background: #3b82f6;
    color: white;
    padding: 8px 16px;
    border-radius: 4px;
    margin: 8px 0;
  }
</style>
</head>
<body>
<div class="multicol">
  <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
  <h3 class="spanning">Spanning Heading</h3>
  <p>Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
</div>
</body>
</html>
```

**확인 방법** — 브라우저로 열어 파란 제목 띠가 회색 상자 폭 전체를 채우는지, 첫 문단이 띠 위에 · 둘째 문단이 띠 아래에 있는지 본다. `column-span` 줄을 지웠다 다시 넣어 띠의 폭이 열 하나 폭과 상자 폭 사이에서 바뀌는지도 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

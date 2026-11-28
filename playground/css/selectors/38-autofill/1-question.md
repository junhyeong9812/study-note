# css/selectors/38 — :autofill — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 사용자가 이름을 직접 쳐 넣으면 (예측)

```css
/* 질문용 발췌 */
.af-input          { border: 2px solid #d1d5db; }
.af-input:autofill { border-color: #f59e0b; }
```

- 사용자가 자동완성 후보를 고르지 않고 키보드로 「kim」 을 쳐 넣었을 때 테두리는 무슨 색인가?

### 2. 자동완성 후보를 고른 순간의 테두리 (예측)

```css
/* 질문용 발췌 */
.af-input          { border: 2px solid #d1d5db; transition: all 0.2s; }
.af-input:autofill { border-color: #f59e0b; box-shadow: 0 0 0 1px #f59e0b; }
```

- 저장된 사용자 이름을 후보에서 골라 칸이 채워지면, 테두리와 그 둘레는 어떻게 바뀌나?

### 3. 배경을 바꿀 때 box-shadow 트릭이 필요한 까닭 (왜)

- 자동완성된 칸의 배경색을 바꾸는 데 `background` 대신 `box-shadow` 로 덮는 방법을 쓰는 까닭은 무엇인가?

### 4. `box-shadow: 0 0 0 1px` 로 배경을 덮을 수 있나 (경계)

- 원본 예제의 바깥 1px 그림자가 팁에서 말하는 「배경 덮기」 노릇을 못 하는 까닭은 무엇인가?

### 5. `autocomplete="username"` 을 다는 까닭 (왜)

- 예제의 `input` 에 `autocomplete="username"` 을 적어 두는 것은 `:autofill` 이 걸리는 일과 어떻게 이어지나?

### 6. 자동완성이 한 번도 일어나지 않는 칸 (경계)

- 저장된 값이 없거나 자동완성이 꺼진 칸에서 `:autofill` 규칙에만 중요한 안내를 넣으면 무엇이 문제인가?

### 7. `.af-input:autofill` 이 `.af-input` 을 이기는 까닭 (연결)

- 두 규칙이 같은 칸에 함께 걸릴 때 `border-color` 가 자동완성 규칙 쪽 값이 되는 것을 명시도로 설명하면 어떻게 되나?

### 8. `:autofill` 과 `:focus` 의 관계 (연결)

- `:autofill` 과 `:focus` 는 둘 다 의사 클래스인데, 무엇을 보고 고르는지가 어떻게 다르고 한 칸에 동시에 걸릴 수 있나?

## 실습

### 실습 1. 자동완성된 사용자 이름 칸만 강조하기

**만들 것** — 사용자 이름 입력 칸 하나를 두고, 브라우저가 자동완성으로 값을 채웠을 때만 배경 · 테두리 · 둘레 고리가 바뀌는 페이지를 만든다.

**요구 조건**
1. 클래스가 `af-input` 이고 `type` 이 `text`, `name` 이 `username` 인 `input` 하나를 두고, 자리표시 글로 「사용자 이름」을 보인다.
2. 브라우저가 이 칸을 「사용자 이름 칸」으로 알아보고 저장된 값을 채울 수 있도록 `autocomplete` 속성을 단다.
3. 평소 모양(여백 · 회색 테두리 · 둥근 모서리 · 글자 크기 · 너비)은 `.af-input` 규칙으로 정하고, 모든 속성 변화가 0.2초에 걸쳐 바뀌게 한다 — 이 규칙은 시작 코드에 채워져 있다.
4. 자동완성으로 값이 채워진 `.af-input` 에만 걸리는 선택자를 써서, 시작 코드의 강조 선언(배경 · 테두리 색 · 바깥 고리)이 그 상태에서만 적용되게 한다.
5. 직접 타이핑한 값에는 강조가 걸리지 않아야 한다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>:autofill 실습</title>
<style>
  .af-input {
    padding: 10px 14px;
    border: 2px solid #d1d5db;
    border-radius: 8px;
    font-size: 14px;
    width: 250px;
    transition: all 0.2s;
  }
  /* TODO: 아래 선택자 자리에 「자동완성으로 채워진 .af-input」만 고르는 선택자를 쓴다 */
  /* 선택자 */ {
    background: #fef3c7 !important;
    border-color: #f59e0b;
    box-shadow: 0 0 0 1px #f59e0b;
  }
</style>
</head>
<body>
  <!-- TODO: 브라우저가 사용자 이름으로 자동완성할 수 있게 속성을 하나 더 단다 -->
  <input class="af-input" type="text" name="username" placeholder="사용자 이름" />
</body>
</html>
```

**확인 방법** — 브라우저로 파일을 열고, 저장된 사용자 이름이 있으면 칸을 눌러 후보를 골라 채운 뒤 테두리 색이 바뀌는지 본다. 새로 고침한 뒤 같은 이름을 직접 쳐 넣었을 때는 테두리가 회색으로 남는지 비교한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

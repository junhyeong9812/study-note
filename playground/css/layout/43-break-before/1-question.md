# css/layout/43 — break-before — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 2단 상자 안의 제목에 `column` (예측)

```css
/* 질문용 발췌 */
.multicol { column-count: 2; }
.break { break-before: column; }
/* HTML: <div class="multicol"><p>A</p><h3 class="break">B</h3><p>C</p></div> */
```

- 왼쪽 열과 오른쪽 열에는 각각 무엇이 놓이는가?

### 2. 같은 상자에서 값을 `auto` 로 바꾸면 (예측)

```css
/* 질문용 발췌 */
.multicol { column-count: 2; }
.break { break-before: auto; }
```

- 제목 B 가 오른쪽 열 맨 위에서 시작한다고 장담할 수 있는가?

### 3. 장 제목에 `right` 를 주고 인쇄하면 (예측)

```css
/* 질문용 발췌 */
@media print {
  h2.chapter { break-before: right; }
}
```

- 인쇄했을 때 각 `h2.chapter` 는 어떤 페이지에서 시작하는가?

### 4. 컨테이너에 준 값이 자식에게 먹지 않는 까닭 (왜)

- `.multicol` 자체에 `break-before: column` 을 줘도 안쪽 h3 이 새 열로 가지 않는 까닭은 무엇인가?

### 5. `break-before` 에 트랜지션이 안 걸리는 까닭 (왜)

- `break-before` 를 `auto` 에서 `column` 으로 바꿀 때 `transition` 으로 부드럽게 넘어가지 않는 까닭은 무엇인가?

### 6. 피하기 값 셋이 막는 범위 (경계)

- `avoid` · `avoid-column` · `avoid-page` 는 각각 어떤 나누기까지 막는가?

### 7. `column-count` 가 없는 평범한 블록 (경계)

- 다단도 아니고 인쇄도 아닌 평범한 화면 블록 안의 요소에 `break-before: column` 을 주면 어떻게 되는가?

### 8. `page-break-before` · `column-count` 와의 관계 (연결)

- `break-before` 는 레거시 `page-break-before` 와 무슨 관계이고, `column-count` 와는 어떻게 함께 쓰이는가?

## 실습

### 실습 1. 2단 상자에서 제목을 둘째 열로 보내기

**만들 것** — 두 열짜리 상자 안에 문단 · 제목 · 문단을 차례로 넣고, 제목부터는 반드시 둘째 열에서 시작하게 한다.

**요구 조건**
1. `.multicol` 상자는 내용을 두 열로 나눠 흘린다.
2. 상자 안에는 차례로 문단(`First column content here.`), 제목 `h3.break`(`New Column`), 문단(`Second column content here.`)이 있다.
3. `h3.break` 바로 앞에서 열 나누기가 강제되어, 제목과 그 뒤 문단이 둘째 열 맨 위부터 놓인다.
4. 첫 문단은 첫 열에 혼자 남는다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>break-before 실습</title>
<style>
  .multicol {
    /* TODO: 두 열로 나눈다 */
    column-gap: 20px;
    background: #f1f5f9;
    padding: 16px;
    border-radius: 4px;
  }
  .break {
    /* TODO: 이 요소 앞에서 새 열로 넘긴다 */
    background: #3b82f6;
    color: white;
    padding: 4px 12px;
    border-radius: 4px;
    margin: 0 0 8px;
  }
</style>
</head>
<body>
<div class="multicol">
  <!-- TODO: 문단, h3.break 제목, 문단을 차례로 넣는다 -->
</div>
</body>
</html>
```

**확인 방법** — 브라우저로 열어, 왼쪽 열에는 첫 문단만 있고 파란 제목 `New Column` 이 오른쪽 열 맨 위에서 시작하는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

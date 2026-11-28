# css/cascade-specificity/02 — Cascade order — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 같은 선택자를 두 번 선언하면 (예측)

```css
/* 질문용 발췌 — <p class="note">…</p> 하나에 적용 */
.note { color: red; padding: 12px; }
.note { color: #3b82f6; }
```

- `p.note` 의 글자색은 두 값 중 어느 것인가?
- `p.note` 의 안쪽 여백은 얼마인가?

### 2. 서로 다른 선택자가 `padding` 을 노리면 (예측)

```css
/* 질문용 발췌 — <div class="cascade-demo"><p class="styled">…</p></div> */
.styled { padding: 12px; }
.cascade-demo p { padding: 16px; }
```

- `p.styled` 의 안쪽 여백은 얼마인가?
- 두 규칙의 위아래를 바꾸면 결과가 달라지나?

### 3. `:last-child` 규칙을 위로 올리면 (예측)

- `.cascade-demo p { margin-bottom: 8px; }` 와 `.cascade-demo p:last-child { margin-bottom: 0; }` 가 이 차례로 있을 때, 마지막 `p` 의 아래 바깥 여백은 얼마인가?
- `:last-child` 규칙을 `.cascade-demo p` 규칙보다 위로 옮기면 그 값은 어떻게 되나?

### 4. 한 속성에서 진 규칙의 나머지 선언 (왜)

- `.styled` 첫 규칙이 `color` 에서 졌는데도 그 규칙의 다른 선언이 쓰일 수 있는 까닭은 무엇인가?

### 5. 명시도 높은 일반 선언 대 명시도 낮은 `!important` 선언 (경계)

- 두 선언이 같은 속성에서 부딪히면 판정은 네 기준 중 어디에서 끝나나?

### 6. 원본 데모 `.multi` 가 보여 주는 범위 (경계)

- 원본 데모의 `.multi` 두 규칙은 「브라우저 기본 < 작성자 일반 < 작성자 !important」를 실제로 보여 주나?

### 7. 명시도 표기 `0,0,1,0` 과 `0,1,0` (연결)

- 원본 주석이 `.styled` 의 명시도를 두 가지로 적은 것은 어떤 표기 차이 때문인가?

### 8. 전환 · 애니메이션과 `!important` (연결)

- 원본 팁의 전체 순서에서 Transitions 와 Animations 는 `!important` 선언과 각각 어떤 위아래 관계에 놓이나?

## 실습

### 실습 1. 소스 순서와 명시도로 스타일 충돌 가리기

**만들 것** — 같은 선택자를 두 번 쓴 규칙끼리는 소스 순서로, 서로 다른 선택자끼리는 명시도로 승부가 나는 작은 데모 페이지를 만든다.

**요구 조건**
1. `.cascade-demo` 컨테이너 안에 `p.styled` 와 `p.multi` 두 단락을 둔다(마크업은 시작 코드에 있다).
2. `.styled` 규칙을 두 번 쓴다 — 먼저 쓴 규칙에는 글자색 빨강과 안쪽 여백을, 나중 규칙에는 글자색(파랑)만 둔다. 결과 글자색은 나중 규칙의 파랑이어야 한다.
3. `.multi` 규칙을 두 번 쓴다 — 먼저 쓴 규칙에는 글자색 회색을, 나중 규칙에는 글자색(보라)과 굵기 700 을 둔다. 결과는 보라색 굵은 글씨여야 한다.
4. 컨테이너 꾸밈(`.cascade-demo`)과 단락 공통 꾸밈(`.cascade-demo p`)은 시작 코드에 채워진 그대로 둔다.
5. 마지막 단락만 아래 바깥 여백을 없앤다 — `.cascade-demo p` 보다 명시도가 높은 선택자를 써서, 규칙의 위치와 상관없이 이기게 한다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>Cascade order 연습</title>
<style>
  /* TODO: .styled 첫 규칙 — 글자색 red, 안쪽 여백 12px */

  /* TODO: .styled 둘째 규칙 — 글자색 #3b82f6 만 */

  /* TODO: .multi 첫 규칙 — 글자색 gray */

  /* TODO: .multi 둘째 규칙 — 글자색 #8b5cf6, 굵기 700 */

  .cascade-demo {
    padding: 16px;
    background: #f1f5f9;
    border-radius: 8px;
  }
  .cascade-demo p {
    font-size: 18px;
    padding: 16px;
    background: white;
    border-radius: 6px;
    margin-bottom: 8px;
    border: 2px solid #e2e8f0;
  }

  /* TODO: 마지막 p 만 아래 바깥 여백 0 — .cascade-demo p 보다 명시도 높은 선택자로 */
</style>
</head>
<body>
  <div class="cascade-demo">
    <p class="styled">같은 명시도 → 나중 선언이 승리</p>
    <p class="multi">여러 스타일시트에서 온 스타일</p>
  </div>
</body>
</html>
```

**확인 방법** — 파일을 브라우저로 열어 첫 단락이 파란 글자, 둘째 단락이 보라색 굵은 글자인지, 둘째 단락 아래에 여백이 없는지 본다. 개발자 도구에서 각 단락을 골라 진 선언(빨강 · 회색 · `padding: 12px` · `margin-bottom: 8px`)에 줄이 그어져 있는지 확인한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

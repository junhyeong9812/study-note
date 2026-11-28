# css/layout/44 — break-after — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 제목에 `break-after: column` 을 준 2단 컨테이너 (예측)

```html
<!-- 질문용 발췌 -->
<div style="column-count: 2;">
  <h3 style="break-after: column;">First Section</h3>
  <p>First column content.</p>
  <p>Second column content.</p>
</div>
```

- 두 문단은 각각 어느 열에 놓이는가?

### 2. 나누기를 첫 문단으로 옮기면 (예측)

```html
<!-- 질문용 발췌 -->
<div style="column-count: 2;">
  <h3>First Section</h3>
  <p style="break-after: column;">First column content.</p>
  <p>Second column content.</p>
</div>
```

- 첫 열에는 어떤 요소들이 놓이는가?

### 3. 끊고 싶은 자리 앞 요소에 거는 까닭 (왜)
- 「문단부터 새 열」을 원할 때 왜 문단이 아니라 그 앞의 제목에 `break-after` 를 거는가?

### 4. 컨테이너에 건 `break-after: column` (경계)
- `.multicol` 자체에 `break-after: column` 을 걸면 안의 제목 · 문단 배치는 바뀌는가?

### 5. `avoid` 와 `avoid-column` 의 범위 (경계)
- 인쇄할 때 페이지 나누기를 피하고 싶다면 `avoid-column` 으로 충분한가?

### 6. 「방지」가 지켜지지 않는 경우 (경계)
- `break-after: avoid` 를 걸었는데도 그 요소 뒤에서 끊길 수 있는 상황은 어떤 경우인가?

### 7. `page-break-after` 와의 관계 (연결)
- `break-after` 는 옛 속성 `page-break-after` 와 어떤 관계이고, 무엇을 더 다룰 수 있는가?

### 8. `left` · `right` 가 의미를 갖는 출력 (연결)
- `break-after: right` 는 화면의 다단 레이아웃과 책 인쇄 중 어느 쪽과 이어지는 값인가?

## 실습

### 실습 1. 제목 다음 본문을 둘째 열에서 시작하는 2단 박스

**만들 것** — 제목 하나와 문단 둘이 든 2단 박스를 만들고, 제목 뒤에서 열을 강제로 나눠 제목만 첫 열에 두고 두 문단은 둘째 열에 오게 한다.

**요구 조건**
1. `.multicol` 컨테이너가 내용을 2개의 열로 나눠 흘린다.
2. 컨테이너 안에 제목 `First Section` 하나와 문단 두 개가 차례로 들어 있다.
3. 제목에 `break` 클래스를 단다.
4. `.break` 요소 뒤에서 열 나누기를 강제해, 제목 다음 내용이 다음 열에서 시작하게 한다.
5. 열 간격 · 배경 · 여백 · 둥근 모서리 · 제목 색 같은 꾸밈은 시작 코드에 있는 그대로 둔다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>break-after 연습</title>
<style>
  .multicol {
    /* TODO: 내용을 2개 열로 나눈다 */
    column-gap: 20px;
    background: #f1f5f9;
    padding: 16px;
    border-radius: 4px;
  }
  .break {
    /* TODO: 이 요소 뒤에서 열 나누기를 강제한다 */
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
  <h3>First Section</h3>   <!-- TODO: break 클래스를 단다 -->
  <p>First column content.</p>
  <p>Second column content.</p>
</div>
</body>
</html>
```

**확인 방법** — 파일을 브라우저로 열어 파란 제목만 왼쪽 열에 있고, 두 문단이 오른쪽 열 위부터 쌓이는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

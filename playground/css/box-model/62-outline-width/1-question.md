# css/box-model/62 — outline-width — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. `thick` 에 선 모양 `none` (예측)

```css
/* 질문용 발췌 */
.box { outline-width: thick; outline-style: none; outline-color: red; }
```

- 이 상자의 계산된 `outline-width` 는 얼마인가?
- 화면에 외곽선이 보이는가?

### 2. 부모만 두께를 준 경우 (예측)

```css
/* 질문용 발췌 */
.parent { outline-width: 8px; outline-style: solid; }
.child  { outline-style: solid; }
```

- `.child` 의 외곽선 두께는 어떤 값을 따르는가?

### 3. 예제가 `outline-style: solid` 를 꼭 함께 적은 까닭 (왜)

- 외곽선 두께만 보여 주려는 예제에서 `outline-style: solid` 를 함께 적어야 하는 까닭은 무엇인가?

### 4. 키워드 두께는 정확히 몇 px 인가 (경계)

- `thin` · `medium` · `thick` 의 실제 px 값은 어디까지 믿을 수 있는가?

### 5. `0.1em` 과 `1px` 의 차이 (경계)

- 글자 크기가 다른 두 요소에 같은 `outline-width: 0.1em` 을 주면 두께는 어떻게 되는가?

### 6. 두께와 `transition` (연결)

- 마우스를 올렸을 때 외곽선이 서서히 굵어지게 할 수 있는 까닭은 원본 재료의 어떤 성질과 이어지는가?

### 7. 외곽선 세 속성의 역할 분담 (연결)

- `outline-width` · `outline-style` · `outline-color` 는 외곽선의 무엇을 각각 맡는가?

## 실습

### 실습 1. 두께 4px 실선 외곽선을 가진 상자 만들기

**만들 것** — 「outline-width」라는 글자가 든 상자 하나에 두께가 정해진 실선 외곽선을 둘러 보인다.

**요구 조건**
1. `box` 클래스를 가진 `div` 하나에 `outline-width` 라는 글자를 넣는다.
2. 외곽선 두께를 길이값 `4px` 로 정한다.
3. 외곽선 모양을 실선으로 정해 두께가 0 으로 계산되지 않게 한다.
4. 외곽선 색 · 안쪽 여백 · 배경색은 시작 코드에 적힌 그대로 둔다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>outline-width - 요소의 외곽선 너비를 설정</title>
<style>
  .box {
    /* TODO: 외곽선 두께를 길이값으로 정한다 */
    /* TODO: 외곽선 모양을 실선으로 정한다 (none 이면 두께가 0 이 된다) */
    outline-color: #3b82f6;
    padding: 16px;
    background: #f8fafc;
  }
</style>
</head>
<body>
  <!-- TODO: box 클래스를 가진 div 에 글자 outline-width 를 넣는다 -->
</body>
</html>
```

**확인 방법** — 파일을 브라우저로 열어 상자 둘레에 파란 실선 외곽선이 보이는지 본다. 개발자 도구에서 `.box` 의 계산된 `outline-width` 가 4px 인지 확인하고, `outline-style` 줄을 지우면 0 으로 바뀌는지도 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

# css/color-background/22 — forced-color-adjust — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 값을 적지 않은 자식 상자 (예측)

```css
/* 질문용 발췌 */
.chart { forced-color-adjust: none; }
.chart .bar { background: #ef4444; }   /* forced-color-adjust 를 적지 않음 */
```

- 강제 색상 모드에서 `.bar` 의 배경색은 자동 조정되는가, 지정한 색이 남는가?

### 2. 속성을 아예 쓰지 않은 버튼 (예측)

```css
/* 질문용 발췌 */
button { background: #3b82f6; color: white; }
```

- 강제 색상 모드를 켜면 이 버튼의 색은 어떻게 되는가?

### 3. 두 상자를 평소 화면에서 비교하면 (예측)

```css
/* 질문용 발췌 */
.a { forced-color-adjust: auto; background: #3b82f6; }
.b { forced-color-adjust: none; background: #3b82f6; }
```

- 강제 색상 모드가 꺼진 평소 화면에서 `.a` 와 `.b` 는 어떻게 달라 보이는가?

### 4. `none` 을 색이 의미를 담을 때만 쓰라는 까닭 (왜)

- 모양이 흐트러지는 것을 막으려고 `none` 을 넓게 쓰면 왜 문제가 되는가?

### 5. `body` 에 `none` 을 적는 것이 위험한 까닭 (왜)

- `body` 하나에만 `none` 을 적었는데 왜 페이지 전체가 조정에서 빠지는가?

### 6. `auto` 에서 `none` 으로 바꾸는 전환 효과 (경계)

- `transition` 으로 `forced-color-adjust` 의 값이 서서히 바뀌게 만들 수 있는가?

### 7. `preserve-parent-color` 가 지키는 범위 (경계)

- `preserve-parent-color` 를 적은 요소에서 강제 색상 모드의 조정을 받지 않는 색은 어디까지인가?

### 8. `color` 의 상속과 견주기 (연결)

- `forced-color-adjust` 가 자식에게 퍼지는 방식은 `color` 속성이 자식에게 퍼지는 방식과 어떻게 닮았는가?

## 실습

### 실습 1. 강제 색상 모드에서 다르게 반응하는 두 상자

**만들 것** — 하나는 강제 색상 모드의 자동 조정을 받고, 다른 하나는 그라디언트 색을 그대로 지키는 상자 두 개를 만든다.

**요구 조건**
1. 클래스가 `auto-box` 인 상자와 `none-box` 인 상자를 위아래로 둔다. 각 상자의 글자는 자신이 어떤 값인지 설명한다.
2. `.auto-box` 에는 강제 색상 모드에서 색이 자동 조정된다는 값을 기본값에 기대지 않고 명시한다.
3. `.none-box` 에는 강제 색상 모드에서도 지정한 그라디언트와 글자색이 유지되도록 값을 적는다.
4. 배경 · 글자색 · 여백 · 둥근 모서리 같은 꾸밈 값은 시작 코드에 있는 그대로 둔다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>forced-color-adjust 실습</title>
<style>
  .auto-box {
    /* TODO: 강제 색상 모드에서 자동 조정을 받는 값을 명시한다 */
    background: #3b82f6;
    color: white;
    padding: 16px;
    margin-bottom: 8px;
    border-radius: 8px;
    font-weight: bold;
  }
  .none-box {
    /* TODO: 강제 색상 모드에서도 지정한 색을 유지하는 값을 적는다 */
    background: linear-gradient(135deg, #f43f5e, #8b5cf6);
    color: white;
    padding: 16px;
    border-radius: 8px;
    font-weight: bold;
  }
</style>
</head>
<body>
  <div class="auto-box">auto: 강제 색상 모드에서 조정됨</div>
  <div class="none-box">none: 원래 색상 유지</div>
</body>
</html>
```

**확인 방법** — 브라우저로 열어 평소에는 두 상자가 지정한 색으로 보이는지 본다. 강제 색상 모드를 켤 수 있는 환경이면 켜서 위 상자만 색이 바뀌고 아래 그라디언트 상자는 그대로인지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

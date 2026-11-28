# css/box-model/36 — border-right-style — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 예제에서 무늬 줄만 지우면 (예측)

```css
/* 질문용 발췌 */
.box {
  border-right-width: 3px;
  border-right-color: #3b82f6;
  padding: 16px;
}
```

- 이 박스의 오른쪽 변에 파란 선이 보이는가?

### 2. 네 값을 받은 `border-style` (예측)

```css
/* 질문용 발췌 */
.box { border-style: solid dashed dotted double; border-width: 3px; }
```

- 오른쪽 변은 어떤 무늬로 그려지는가?

### 3. 무늬만 쓰고 두께·색은 비워 두면 (예측)

```css
/* 질문용 발췌 */
.box { color: black; border-right-style: dotted; }
```

- 오른쪽 변에 선이 생긴다면, 두께와 색은 무엇으로 정해지는가?

### 4. 무늬를 hover 로 바꿀 때 전환이 먹지 않는 까닭 (왜)

- `transition` 을 걸어도 `solid` 에서 `dashed` 로 서서히 바뀌지 않는 이유는 무엇인가?

### 5. 부모에만 준 오른쪽 테두리 무늬와 자식 (경계)

- 부모에 `border-right-style: solid` 를 주면 그 안의 자식 요소는 오른쪽 테두리 무늬로 무엇을 갖는가?

### 6. `hidden` 과 `none` 이 갈리는 자리 (경계)

- 화면에서 똑같이 선이 없는 두 값이 다르게 대접받는 곳은 어디인가?

### 7. 개별 속성 셋과 단축 속성 (연결)

- 예제의 `border-right-style` · `border-right-width` · `border-right-color` 세 줄을 한 줄로 줄이면 어떤 속성을 쓰나?

### 8. 테두리가 박스 모델에서 놓이는 층 (연결)

- 오른쪽 테두리는 박스 모델의 content · padding · margin 가운데 어느 둘 사이에 놓이는가?

## 실습

### 실습 1. 오른쪽에만 점선 테두리를 두른 박스

**만들 것** — 글자 하나를 담은 박스를 만들고, 네 변 가운데 오른쪽 변에만 점선 테두리를 그린다.

**요구 조건**

1. `box` 클래스를 가진 `div` 하나에 `border-right-style` 이라는 글자를 넣는다.
2. 오른쪽 테두리의 무늬를 `border-right-style` 로 점선(`dotted`)으로 정한다.
3. 오른쪽 테두리의 두께와 색은 단축 속성이 아니라 개별 속성(`border-right-width` · `border-right-color`)으로 따로 정한다 — 값은 시작 코드의 주석에 있다.
4. 위 · 아래 · 왼쪽 변에는 테두리를 주지 않는다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>border-right-style</title>
<style>
  .box {
    /* TODO: 오른쪽 테두리 무늬를 점선으로 */
    /* TODO: 오른쪽 테두리 두께 — 3px */
    /* TODO: 오른쪽 테두리 색 — #3b82f6 */
    padding: 16px;
    background: #f8fafc;
  }
</style>
</head>
<body>
  <!-- TODO: box 클래스를 가진 div 하나 -->
</body>
</html>
```

**확인 방법** — 파일을 브라우저로 열어, 박스의 오른쪽 변에만 파란 점선이 있고 나머지 세 변에는 선이 없는지 본다. 무늬 줄을 주석 처리했을 때 선이 사라지는지도 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

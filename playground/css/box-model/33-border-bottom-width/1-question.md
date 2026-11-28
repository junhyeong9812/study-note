# css/box-model/33 — border-bottom-width — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 두께만 주고 스타일은 적지 않으면 (예측)

```css
/* 질문용 발췌 */
.box { border-bottom-width: 5px; border-bottom-color: #3b82f6; padding: 16px; }
```

- 이 박스 아래에 파란 선이 보이는가, 그리고 아래쪽 테두리가 차지하는 두께는 얼마인가?

### 2. 스타일만 주고 두께를 적지 않으면 (예측)

```css
/* 질문용 발췌 */
.line { border-bottom-style: solid; }
```

- 이 요소의 아래쪽 테두리 두께는 어떤 값으로 정해지는가?

### 3. 테두리가 붙은 박스의 바깥 높이 (예측)

```css
/* 질문용 발췌 */
.bar { height: 40px; padding: 0; border-bottom: 5px solid black; }  /* box-sizing 은 기본값 */
```

- 이 박스가 세로로 차지하는 바깥 높이는 몇 px 인가?

### 4. 스타일이 `none` 일 때 두께를 0 으로 보는 까닭 (왜)

- 두께 값을 분명히 적었는데도 스타일이 `none` 이면 두께를 0 으로 계산하는 규칙은 화면 배치에 어떤 의미가 있는가?

### 5. 두께로 쓸 수 있는 값의 경계 (경계)

- `border-bottom-width: -2px;` 를 적으면 어떻게 되는가?
- 정확히 2px 이 필요할 때 `thin` 대신 길이 값을 쓰는 것이 나은 까닭은 무엇인가?

### 6. 부모에 준 아래쪽 테두리 두께 (경계)

- 부모에 `border-bottom: 4px solid` 를 주면 그 안의 자식 요소도 4px 아래쪽 테두리를 갖는가?

### 7. 단축 속성 `border-bottom` 과의 순서 (연결)

- `border-bottom-width: 5px;` 를 적은 다음 줄에 `border-bottom: solid red;` 를 적으면 두께는 어떻게 되는가?

### 8. 호버 때 밑줄을 굵게 하는 애니메이션 (연결)

- 탭에 호버하면 `border-bottom-width` 를 0 에서 4px 로 전환(`transition`)할 때, 탭 아래 내용에는 무슨 일이 생기며 그 까닭은 박스 모델의 어느 규칙인가?

## 실습

### 실습 1. 아래쪽에만 굵은 파란 선이 있는 박스 만들기

**만들 것** — 글자가 든 박스 하나를 만들고, 아래쪽에만 두께를 정한 실선 테두리를 단다.

**요구 조건**
1. `body` 안에 `box` 클래스를 단 `div` 하나를 두고, 안에 글자 `border-bottom-width` 를 넣는다.
2. 아래쪽 테두리의 두께를 `border-bottom-width` 로 길이 값 5px 로 정한다.
3. 아래쪽 테두리의 선 모양을 실선으로 정해, 두께가 실제로 그려지게 한다.
4. 색 · 안쪽 여백 · 배경은 시작 코드에 채워진 값을 그대로 둔다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>border-bottom-width 연습</title>
<style>
  .box {
    /* TODO: 아래쪽 테두리 두께를 길이 값으로 정한다 */
    /* TODO: 아래쪽 테두리 선 모양을 정한다 (빠뜨리면 두께가 0 이 된다) */
    border-bottom-color: #3b82f6;
    padding: 16px;
    background: #f8fafc;
  }
</style>
</head>
<body>
  <!-- TODO: box 클래스를 단 div 를 넣는다 -->
</body>
</html>
```

**확인 방법** — 브라우저로 열어 박스 아래쪽에만 굵은 파란 실선이 있는지 본다. 두 번째 TODO 줄을 지웠을 때 선이 사라지는지도 확인한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

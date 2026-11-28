# css/box-model/38 — border-left-style — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 두께와 색만 준 왼쪽 테두리 (예측)

```css
/* 질문용 발췌 */
.box { width: 200px; border-left-width: 4px; border-left-color: red; }
```

- 이 박스의 왼쪽에 빨간 선이 보이는가?
- 이 박스의 바깥 폭은 몇 px 로 계산되는가?

### 2. hover 로 선 모양 바꾸기 (예측)

```css
/* 질문용 발췌 */
.box { border-left: 4px solid #3b82f6; transition: all 0.5s; }
.box:hover { border-left-style: dashed; }
```

- 마우스를 올리면 왼쪽 선은 0.5초 동안 어떤 식으로 바뀌는가?

### 3. 단축 속성과 개별 속성의 순서 (예측)

```css
/* 질문용 발췌 */
.a { border-left: 4px solid #333; border-left-style: dashed; }
.b { border-left-style: dashed; border-left: 4px solid #333; }
```

- `.a` 와 `.b` 의 왼쪽 선 모양은 각각 무엇인가?

### 4. `none` 이 있는데 `hidden` 을 따로 두는 까닭 (왜)

- 결과가 같아 보이는 `none` 과 `hidden` 이 왜 둘 다 필요한가?

### 5. 선 모양이 부드럽게 바뀌지 않는 까닭 (왜)

- `border-left-width` 는 서서히 바뀔 수 있는데 `border-left-style` 은 왜 그럴 수 없는가?

### 6. 부모에 준 왼쪽 테두리 모양의 범위 (경계)

- 부모 `div` 에 `border-left-style: solid` 와 두께 · 색을 주면, 그 안의 자식 `p` 들의 왼쪽에도 선이 생기는가?

### 7. 왼쪽 선과 박스 폭 (연결)

- `width: 200px` 인 박스에 4px 실선 왼쪽 테두리를 줄 때, 바깥 폭을 200px 로 묶어 두려면 어떤 속성을 함께 써야 하는가?

## 실습

### 실습 1. 왼쪽에만 실선 강조선이 있는 박스 만들기

**만들 것** — 글자가 든 박스 하나를 만들고, 그 박스의 왼쪽 변에만 실선 테두리가 보이게 한다.

**요구 조건**

1. 본문에 `box` 클래스를 단 `div` 하나를 두고, 안에 `border-left-style` 이라는 글자를 넣는다.
2. 그 박스의 왼쪽 테두리 모양을 `border-left-style` 로 실선(`solid`)으로 정한다.
3. 시작 코드에 채워 둔 왼쪽 테두리의 두께 · 색 선언과 여백 · 배경 선언은 그대로 둔다.
4. 위 · 오른쪽 · 아래 변에는 테두리를 주지 않는다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>border-left-style 연습</title>
<style>
  .box {
    /* TODO: 왼쪽 테두리의 모양을 실선으로 정한다 */
    border-left-width: 4px;
    border-left-color: #3b82f6;
    padding: 16px;
    background: #f8fafc;
  }
</style>
</head>
<body>
  <!-- TODO: box 클래스를 단 div 하나, 안 글자는 border-left-style -->
</body>
</html>
```

**확인 방법** — 파일을 브라우저로 열어 박스의 왼쪽에만 파란 실선이 있는지 본다. TODO 줄을 비운 채로 열어 선이 사라지는지도 비교해 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

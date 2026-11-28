# css/box-model/37 — border-bottom-style — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 굵기와 색만 준 상자 (예측)

```css
/* 질문용 발췌 */
.box { border-bottom-width: 3px; border-bottom-color: #3b82f6; padding: 16px; }
```

- 이 상자의 아래쪽에는 무엇이 보이나?

### 2. hover 에 transition 을 건 파선 (예측)

```css
/* 질문용 발췌 */
.box { border-bottom-style: dashed; border-bottom-width: 3px; transition: all 1s; }
.box:hover { border-bottom-style: solid; }
```

- 마우스를 올린 뒤 1초 동안 아래쪽 선은 어떻게 바뀌나?

### 3. `border-bottom-style` 이 부드럽게 전환되지 않는 까닭 (왜)

- 이 속성의 값이 transition 으로 부드럽게 넘어가지 못하는 까닭은 무엇인가?

### 4. `hidden` 이 `none` 과 따로 있는 까닭 (왜)

- 일반 요소에서 둘 다 「선 없음」인데 `hidden` 이 따로 있는 까닭은 무엇인가?

### 5. 부모에 준 아래 테두리 (경계)

- 부모에 `border-bottom-style: solid` 를 주면 그 효과가 자식 요소의 아래쪽까지 미치나?

### 6. 이 속성이 바꾸는 범위 (경계)

- `border-bottom-style` 하나로 위 · 왼 · 오른쪽 테두리까지 바꿀 수 있나?

### 7. 예제가 세 속성을 함께 쓰는 까닭 (연결)

- 예제는 왜 `border-bottom-style` · `border-bottom-width` · `border-bottom-color` 를 함께 쓰나?

### 8. 3D 효과 값 넷의 짝 (연결)

- `groove` · `ridge` · `inset` · `outset` 넷은 서로 어떤 짝을 이루나?

## 실습

### 실습 1. 아래쪽에만 실선이 있는 상자 만들기

**만들 것** — 글자가 든 상자 하나를 만들고, 그 아래쪽 변에만 실선 테두리를 그린다.

**요구 조건**
1. `class="box"` 인 `div` 하나에 글자 `border-bottom-style` 을 넣는다.
2. `.box` 의 아래쪽 테두리 모양을 실선으로 정한다.
3. 아래쪽 테두리의 굵기와 색은 시작 코드에 채워 둔 값을 그대로 쓴다.
4. 위 · 왼 · 오른쪽 변에는 선이 없어야 한다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>border-bottom-style</title>
<style>
  .box {
    /* TODO: 아래쪽 테두리의 모양을 실선으로 정한다 */
    border-bottom-width: 3px;
    border-bottom-color: #3b82f6;
    padding: 16px;
    background: #f8fafc;
  }
</style>
</head>
<body>
  <!-- TODO: class="box" 인 div 에 글자를 넣는다 -->
</body>
</html>
```

**확인 방법** — 브라우저로 열어 옅은 회색 상자의 아래쪽에만 파란 실선이 있는지 본다. TODO 를 채우기 전과 후를 비교해 선이 생기는지도 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

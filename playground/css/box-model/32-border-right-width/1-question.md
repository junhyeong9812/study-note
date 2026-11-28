# css/box-model/32 — border-right-width — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 두께만 적은 오른쪽 테두리 (예측)

```css
/* 질문용 발췌 */
.box { border-right-width: 5px; border-right-color: #3b82f6; }
```

- 이 상자의 오른쪽 테두리는 계산된 두께가 몇이고, 화면에 선이 보이나?

### 2. 상자 가로 바깥 너비 셈하기 (예측)

```css
/* 질문용 발췌 */
.box {
  box-sizing: content-box;
  width: 200px;
  padding: 16px;
  border-right-width: 5px;
  border-right-style: solid;
}
```

- 이 상자의 가로 바깥 너비(왼쪽 테두리 끝부터 오른쪽 테두리 끝까지)는 몇 px 인가?

### 3. 두께 다음에 단축 속성 (예측)

```css
/* 질문용 발췌 */
.box {
  border-right-width: 5px;
  border-right: solid red;
}
```

- 마지막에 적용되는 오른쪽 테두리 두께는 무엇인가?

### 4. 스타일이 `none` 이면 두께가 0 이 되는 까닭 (왜)

- 두께를 분명히 적었는데도 스타일을 안 정하면 테두리 몫의 공간조차 생기지 않는 까닭은 무엇인가?

### 5. 음수 두께와 키워드의 정확한 픽셀 (경계)

- `border-right-width: -2px` 는 받아들여지나, 안 되면 어떤 값이 남나?
- `thick` 이 어느 환경에서나 정확히 5px 이라고 믿어도 되나?

### 6. 부모의 오른쪽 테두리와 자식 (연결)

- 부모에 `border-right-width: 5px` 와 `solid` 를 주면 그 안의 자식 요소에도 오른쪽 테두리가 생기나?

### 7. 두께를 `transition` 으로 바꿀 때 (연결)

- 마우스를 올리면 오른쪽 테두리를 0 에서 5px 로 부드럽게 늘리려 할 때, 어떤 성질이 이를 가능하게 하고 무엇을 빠뜨리면 아무 변화도 안 보이나?

## 실습

### 실습 1. 오른쪽에만 테두리가 있는 상자

**만들 것** — 글자가 든 상자 하나를 만들고, 네 변 중 오른쪽 변에만 실선 테두리를 그린다.

**요구 조건**
1. `class="box"` 인 `div` 하나에 글자 `border-right-width` 를 넣는다.
2. 오른쪽 테두리의 두께를 롱핸드 `border-right-width` 로 길이 값 5px 로 정한다.
3. 오른쪽 테두리가 실제로 그려지도록 `border-right-style` 을 실선으로 정한다.
4. 다른 세 변에는 테두리를 두지 않는다(단축 속성 `border` · `border-right` 를 쓰지 않는다).

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>border-right-width</title>
<style>
  .box {
    /* TODO: 오른쪽 테두리 두께 */
    /* TODO: 오른쪽 테두리 스타일 */
    border-right-color: #3b82f6;
    padding: 16px;
    background: #f8fafc;
  }
</style>
</head>
<body>
  <!-- TODO: class="box" 인 div -->
</body>
</html>
```

**확인 방법** — 브라우저로 열어 상자의 오른쪽 가장자리에만 파란 세로선이 있는지 본다.
스타일 줄을 지웠을 때 선이 사라지는지도 확인한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

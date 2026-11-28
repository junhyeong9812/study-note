# css/layout/39 — column-rule-style — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 세 열 컨테이너의 구분선 개수 (예측)

```css
/* 질문용 발췌 */
.multicol {
  column-count: 3;
  column-rule-style: dashed;
  column-rule-width: 2px;
  column-rule-color: #3b82f6;
}
```

- 이 상자 안에 세로 구분선은 몇 개 그어지는가?
- 그 선은 어떤 모양인가?

### 2. 모양을 빼고 굵기와 색만 준 경우 (예측)

```css
/* 질문용 발췌 */
.multicol {
  column-count: 3;
  column-rule-width: 4px;
  column-rule-color: red;
}
```

- 열 사이에 빨간 선이 보이는가?

### 3. 예제 주석의 「점선」 (왜)

- 원본 예제가 `dashed` 옆에 「점선 스타일」이라고 적은 것을 왜 그대로 믿으면 안 되는가?

### 4. `hidden` 과 `none` (경계)

- 열 구분선에서 `hidden` 과 `none` 은 결과가 다른가?

### 5. 바깥 다단 상자 안의 안쪽 다단 상자 (경계)

- 바깥 다단 상자에만 `column-rule-style: solid` 를 주면, 그 안에 든 다단 상자의 열 사이에도 실선이 생기는가?

### 6. `transition` 으로 선 모양 바꾸기 (예측)

- `column-rule-style` 을 `solid` 에서 `dotted` 로 바꾸면서 `transition` 을 걸면, 선이 서서히 점선으로 변해 가는가?

### 7. `border-style` 과의 관계 (연결)

- `border-style` 을 이미 아는 사람에게 `column-rule-style` 의 값은 무엇과 같다고 설명하면 되는가?

### 8. 세 속성이 하나의 선을 만드는 방식 (연결)

- `column-rule-style` · `column-rule-width` · `column-rule-color` 는 열 구분선에서 각각 무엇을 맡는가?

## 실습

### 실습 1. 대시선으로 나뉜 3단 글 상자 만들기

**만들 것** — 단락 하나가 세 열로 흐르고, 열 사이에 대시선 구분선이 그어진 상자를 만든다.

**요구 조건**
1. `.multicol` 상자 안에 단락 하나를 둔다.
2. 상자의 내용이 세 열로 나뉘어 흐른다.
3. 열 사이 구분선이 대시선 모양으로 그어진다.
4. 구분선 굵기 · 색, 열 간격, 상자 배경 · 안쪽 여백 · 모서리는 시작 코드에 채워진 값을 쓴다.
5. 단락의 기본 바깥 여백을 없앤다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>column-rule-style 연습</title>
<style>
  .multicol {
    /* TODO: 내용을 세 열로 나눈다 */
    /* TODO: 열 구분선 모양을 대시선으로 */
    column-rule-width: 2px;
    column-rule-color: #3b82f6;
    column-gap: 20px;
    background: #f1f5f9;
    padding: 16px;
    border-radius: 4px;
  }
  p {
    /* TODO: 단락의 기본 바깥 여백 제거 */
  }
</style>
</head>
<body>
<div class="multicol">
  <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt.</p>
</div>
</body>
</html>
```

**확인 방법** — 브라우저로 열어 글이 세 열로 나뉘었는지, 열 사이에 파란 대시선이 두 줄 보이는지 본다. 모양 줄을 지우면 선이 사라지는지도 확인한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

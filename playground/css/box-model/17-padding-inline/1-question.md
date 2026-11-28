# css/box-model/17 — padding-inline — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 값 두 개를 준 가로 쓰기 박스 (예측)

```css
/* 질문용 발췌 */
.tag { writing-mode: horizontal-tb; padding-inline: 10px 30px; }
```

- 왼쪽과 오른쪽 안쪽 여백은 각각 몇 px 인가?

### 2. 세로 쓰기 박스에 준 `padding-inline` (예측)

```css
/* 질문용 발췌 */
.v { writing-mode: vertical-rl; padding-inline: 20px; }
```

- 20px 여백은 박스의 어느 두 면에 붙는가?

### 3. `padding-left` 와 `padding-right` 대신 쓰는 까닭 (왜)

- 결과가 같아 보이는 가로 쓰기에서도 `padding-inline` 을 쓰면 무엇을 얻는가?

### 4. 값을 넣을 수 있는 범위 (경계)

- `padding-inline: -10px` 나 값 세 개짜리 선언은 어떻게 처리되는가?

### 5. 퍼센트 값의 기준 (경계)

- `padding-inline: 10%` 의 10% 는 무엇의 10% 인가?

### 6. 원본 예제가 `display: inline-block` 을 쓰는 까닭 (왜)

- 이 줄을 빼고 기본 블록 `div` 로 두면 패딩을 확인하기가 왜 어려워지는가?

### 7. `padding-block` 과의 관계 (연결)

- 가로 쓰기에서 `padding-inline` 과 `padding-block` 은 각각 어느 면을 맡고, 둘을 합치면 무엇이 되는가?

### 8. 부모에 준 `padding-inline` 과 자식 (연결)

- 부모에 `padding-inline: 40px` 를 주면 그 안의 자식 박스도 같은 패딩을 갖게 되는가?

## 실습

### 실습 1. 인라인 · 블록 축 패딩을 준 파란 라벨 박스

**만들 것** — 글자 `padding-inline` 이 든 박스 하나를 만들고, 논리적 패딩 속성으로 안쪽 여백을 준다.

**요구 조건**

1. `class="box"` 인 `div` 하나에 글자 `padding-inline` 을 넣는다.
2. 인라인 축 양쪽 여백은 `padding-inline` 값 하나로, 블록 축 양쪽 여백은 `padding-block` 값 하나로 준다 (인라인 40px, 블록 16px).
3. `padding-left` · `padding-right` · `padding-top` · `padding-bottom` 같은 물리 방향 속성은 쓰지 않는다.
4. 박스가 줄 전체가 아니라 내용 폭 + 패딩만큼만 차지하게 표시 방식을 바꾼다.
5. 배경 · 글자색 · 모서리 꾸밈은 시작 코드에 있는 그대로 둔다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>padding-inline 실습</title>
<style>
.box {
  /* TODO: 인라인 축 양쪽 패딩 (값 하나) */
  /* TODO: 블록 축 양쪽 패딩 (값 하나) */
  background: #3b82f6;
  color: white;
  border-radius: 4px;
  /* TODO: 박스가 내용 폭만큼만 차지하게 */
}
</style>
</head>
<body>
<!-- TODO: class="box" 인 div 에 글자 padding-inline -->
</body>
</html>
```

**확인 방법** — 브라우저로 열어 파란 박스가 글자 폭에 맞게 줄어 있고, 글자 양옆 여백이 위아래 여백보다 넓은지 본다. 개발자 도구의 박스 모델 그림에서 좌우 40, 위아래 16 이 찍히는지 확인한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

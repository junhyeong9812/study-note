# css/box-model/46 — border-spacing — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 2열 3행 표에 `border-spacing: 8px` (예측)

```css
/* 질문용 발췌 — 표는 2열 3행 */
.table { border-collapse: separate; border-spacing: 8px; }
```

- 가로 방향으로 들어가는 간격은 몇 군데이고 합치면 몇 px 인가?
- 세로 방향으로 들어가는 간격은 몇 군데이고 합치면 몇 px 인가?

### 2. 값 두 개를 준 `border-spacing` (예측)

```css
/* 질문용 발췌 */
.table { border-collapse: separate; border-spacing: 4px 12px; }
```

- 열과 열 사이, 행과 행 사이의 간격은 각각 얼마인가?

### 3. `collapse` 로 바꾼 표 (예측)

```css
/* 질문용 발췌 */
.table { border-collapse: collapse; border-spacing: 20px; }
.table td { border: 2px solid #3b82f6; }
```

- 셀과 셀 사이에는 어떤 간격이 생기는가?

### 4. `collapse` 에서 `border-spacing` 이 무시되는 까닭 (왜)

- 테두리가 합쳐지는 모드에서는 왜 `border-spacing` 이 쓰일 자리가 없는가?

### 5. 간격을 셀 사이에만 두고 가장자리는 붙이기 (경계)

- `border-spacing` 하나만으로 셀 사이에만 간격을 두고 테이블 가장자리 쪽 간격은 0 으로 만들 수 있는가?

### 6. 값을 세 개 쓰면 (경계)

- `border-spacing: 4px 8px 12px;` 처럼 값을 셋 쓰면 그 선언은 어떻게 되는가?

### 7. `padding` 과 `border-spacing` 의 자리 (연결)

- 셀의 `padding` 과 테이블의 `border-spacing` 은 각각 셀 테두리의 어느 쪽 공간을 만들며, 머리 셀의 배경색은 둘 중 어디까지 칠해지는가?

## 실습

### 실습 1. 셀이 서로 떨어진 2열 표 만들기

**만들 것** — 머리 행 하나와 데이터 행 둘로 된 표를 만들고, 셀 테두리를 분리해 셀 사이와 표 가장자리에 같은 간격을 둔다.

**요구 조건**
1. 머리 셀 `A` · `B` 로 된 머리 행 하나와, `1` · `2` / `3` · `4` 데이터 셀로 된 행 둘을 갖는 2열 3행 표를 `class="table"` 로 만든다.
2. 셀 테두리가 이웃 셀과 합쳐지지 않고 셀마다 따로 그려지게 한다.
3. 셀 사이와 표 바깥 가장자리에 가로·세로 모두 8px 의 같은 간격을 둔다.
4. 표 너비와 셀 꾸밈(테두리 · 안쪽 여백 · 가운데 정렬 · 머리 셀 배경)은 시작 코드에 있는 그대로 둔다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>border-spacing 연습</title>
<style>
  .table {
    /* TODO: 셀 테두리를 분리 모드로 둔다 */
    /* TODO: 셀 사이(와 가장자리) 간격을 준다 */
    width: 100%;
  }
  .table th,
  .table td {
    border: 2px solid #3b82f6;
    padding: 8px;
    text-align: center;
  }
  .table th {
    background: #eff6ff;
  }
</style>
</head>
<body>
  <table class="table">
    <!-- TODO: 머리 행(A, B) -->
    <!-- TODO: 데이터 행 1(1, 2) -->
    <!-- TODO: 데이터 행 2(3, 4) -->
  </table>
</body>
</html>
```

**확인 방법** — 브라우저로 열어 파란 테두리 상자 6개가 서로 떨어져 있고, 표 가장자리와 바깥 셀 사이에도 같은 틈이 있는지 본다. `border-collapse` 를 `collapse` 로 바꿔 틈이 사라지는지도 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

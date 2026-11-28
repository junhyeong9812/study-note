# css/grid/26 — place-items — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 값을 하나만 준 `place-items` (예측)

```css
/* 질문용 발췌 */
.grid { display: grid; grid-template-columns: 1fr 1fr; grid-auto-rows: 100px; place-items: center; }
```

- 이 선언은 `align-items` 와 `justify-items` 를 각각 어떤 값으로 정하는가?
- 셀보다 작은 아이템은 셀 안의 어디에 놓이는가?

### 2. 값 두 개 `end start` (예측)

```css
/* 질문용 발췌 — 가로쓰기 한국어 문서 */
.grid { display: grid; grid-auto-rows: 100px; place-items: end start; }
```

- 셀보다 작은 아이템은 셀의 어느 구석에 놓이는가?

### 3. `center` 를 `stretch` 로 바꾸면 (예측)

```css
/* 질문용 발췌 — 아이템에는 width·height 가 없다 */
.grid { display: grid; grid-template-columns: 1fr 1fr; grid-auto-rows: 100px; place-items: stretch; }
```

- 아이템 상자의 크기는 셀과 비교해 어떻게 되는가?

### 4. 값 하나가 「정중앙」이 되는 까닭 (왜)

- `place-items: center` 하나만 써도 세로·가로 모두 가운데가 되는 것은 왜인가?

### 5. 셀이 아이템과 크기가 같을 때 (경계)

- 행 높이와 열 너비가 아이템 크기와 딱 같다면 `place-items` 값을 바꿨을 때 눈에 띄는 변화가 있는가?

### 6. 안쪽 그리드까지 닿나 (경계)

- 바깥 그리드 컨테이너에만 `place-items: center` 를 걸었을 때, 아이템 안에 따로 만든 그리드의 아이템들도 가운데로 정렬되는가?

### 7. 정렬 값을 전환으로 미끄러지게 (경계)

- `transition` 을 걸고 `place-items` 를 `start` 에서 `end` 로 바꾸면 아이템이 부드럽게 미끄러지는가?

### 8. `place-items` 와 `place-content` (연결)

- 「격자 전체를 컨테이너 한가운데로 모으기」와 「각 칸 안에서 아이템을 가운데 두기」는 각각 어느 속성의 일인가?

## 실습

### 실습 1. 네 아이템을 각 칸 정중앙에 놓는 2열 그리드

**만들 것** — 아이템 네 개를 2열 그리드에 배치하고, 각 아이템이 자기 칸의 정중앙에 오게 한다.

**요구 조건**
1. `.grid-container` 를 그리드 컨테이너로 만든다.
2. 열을 같은 비율의 두 칸으로 나눈다(`fr` 단위).
3. 행 높이는 시작 코드에 미리 채운 값을 그대로 둔다 — 이 값 때문에 칸이 아이템보다 커진다.
4. 단축 속성 하나로 아이템을 블록축·인라인축 모두 가운데에 둔다.
5. 아이템 네 개(1~4)는 각자 다른 배경색을 가진다(시작 코드에 채워져 있다).

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>place-items 실습</title>
<style>
  .grid-container {
    /* TODO: 그리드 컨테이너로 만든다 */
    /* TODO: 같은 비율의 두 열 */
    grid-auto-rows: 100px;
    /* TODO: 단축 속성 하나로 양 축 가운데 */
    gap: 8px;
    padding: 16px;
    background: #f1f5f9;
    border-radius: 8px;
  }

  .item {
    padding: 16px 24px;
    border-radius: 6px;
    font-weight: bold;
    font-size: 18px;
    color: white;
  }

  .item-1 { background: #3b82f6; }
  .item-2 { background: #8b5cf6; }
  .item-3 { background: #ec4899; }
  .item-4 { background: #f59e0b; }
</style>
</head>
<body>
  <div class="grid-container">
    <div class="item item-1">1</div>
    <div class="item item-2">2</div>
    <div class="item item-3">3</div>
    <div class="item item-4">4</div>
  </div>
</body>
</html>
```

**확인 방법** — 브라우저로 파일을 열어, 2열 2행 격자의 각 칸 정중앙에 색 상자 1·2·3·4 가 하나씩 놓였는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

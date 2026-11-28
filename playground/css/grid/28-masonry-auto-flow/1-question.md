# css/grid/28 — masonry-auto-flow — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 기본값으로 넷째 아이템을 놓으면 (예측)

```css
/* 질문용 발췌 — 지원 환경, gap 없음 */
.wall { display: grid; grid-template-columns: repeat(3, 1fr); grid-template-rows: masonry; }
/* 아이템 높이(DOM 순서): 1=100px, 2=40px, 3=60px, 4=50px */
```

- 4번 아이템은 몇 번째 열에, 위에서 몇 px 지점부터 놓이나?

### 2. 같은 아이템에 `next` 를 주면 (예측)

```css
/* 질문용 발췌 — 1번 문항과 같은 아이템 */
.wall { display: grid; grid-template-columns: repeat(3, 1fr); grid-template-rows: masonry; masonry-auto-flow: next; }
```

- 4번 아이템은 몇 번째 열에, 위에서 몇 px 지점부터 놓이나?

### 3. 메이슨리를 모르는 브라우저에서 (예측)

```css
/* 질문용 발췌 — 메이슨리 미지원 환경 */
.wall { display: grid; grid-template-columns: repeat(3, 1fr); grid-template-rows: masonry; masonry-auto-flow: pack; }
/* 아이템 높이: 1=100px, 2=40px, 3=60px, 4=50px */
```

- 4번 아이템은 어디에 놓이고, 2번 아이템 아래에는 무엇이 생기나?

### 4. `pack` 이 열의 아래 끝을 더 고르게 만드는 까닭 (왜)

- `pack` 이 `next` 보다 열들의 아래 끝 높이 차이를 줄이는 까닭은 무엇인가?

### 5. 원본이 프로덕션에서 JavaScript 라이브러리를 권하는 까닭 (왜)

- 이 속성을 두고 원본이 프로덕션에서 JavaScript 라이브러리를 권하는 까닭은 무엇인가?

### 6. 메이슨리 축 없이 쓴 `masonry-auto-flow` (경계)

- `grid-template-rows: masonry` 없이 평범한 그리드에 `masonry-auto-flow: next` 만 주면 배치가 바뀌나?

### 7. `grid-column: 3` 을 준 아이템의 차례 (경계)

- DOM 에서 셋째인 아이템에만 `grid-column: 3` 을 주면, `definite-first` 와 `ordered` 에서 그 아이템이 놓이는 차례는 어떻게 다른가?

### 8. 평범한 그리드의 빈칸 메우기와의 차이 (연결)

- 평범한 그리드에서 빈칸을 메우는 `grid-auto-flow: dense` 와 `masonry-auto-flow` 는 각각 어느 레이아웃의 무엇을 정하나?

## 실습

### 실습 1. 높이가 다른 다섯 카드를 세 열 벽돌로 쌓기

**만들 것** — 높이가 제각각인 아이템 다섯 개를 세 열에 메이슨리 방식으로 쌓는 페이지를 만든다.

**요구 조건**
1. `.grid-container` 를 그리드 컨테이너로 만든다.
2. 같은 너비의 열 3개를 `repeat` 와 `fr` 단위로 만든다.
3. 행 축을 메이슨리로 지정해 아이템이 열 안에서 위로 붙어 쌓이게 한다.
4. 셀 사이에 `8px` 간격을 둔다.
5. 아이템 다섯 개(높이가 서로 다름)를 DOM 순서 1~5 로 둔다 — 시작 코드에 이미 있다.
6. `masonry-auto-flow` 는 따로 적지 않아 기본값으로 배치되게 둔다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>masonry-auto-flow 연습</title>
<style>
  .grid-container {
    /* TODO: 그리드 컨테이너로 만든다 */
    /* TODO: 같은 너비의 열 3개 */
    /* TODO: 행 축을 메이슨리로 */
    /* TODO: 셀 사이 간격 */
    padding: 16px;
    background: #f1f5f9;
    border-radius: 8px;
  }
  .item {
    border-radius: 6px;
    font-weight: bold;
    font-size: 18px;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .item-1 { background: #3b82f6; }
  .item-2 { background: #8b5cf6; }
  .item-3 { background: #ec4899; }
  .item-4 { background: #f59e0b; }
  .item-5 { background: #10b981; }
</style>
</head>
<body>
  <div class="grid-container">
    <div class="item item-1" style="height:80px">1</div>
    <div class="item item-2" style="height:120px">2</div>
    <div class="item item-3" style="height:60px">3</div>
    <div class="item item-4" style="height:100px">4</div>
    <div class="item item-5" style="height:70px">5</div>
  </div>
</body>
</html>
```

**확인 방법** — 플래그를 켠 Firefox 에서 열어 4·5번이 짧은 열 밑에 위로 붙어 쌓이는지 보고, 다른 브라우저에서도 열어 평범한 3열 그리드(둘째 행에 4·5번)로 보이는지 비교한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

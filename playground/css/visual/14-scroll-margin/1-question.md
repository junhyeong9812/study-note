# css/visual/14 — scroll-margin — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 카드 2 에 스냅했을 때 카드의 자리 (예측)

```css
/* 질문용 발췌 */
.snap-container { scroll-snap-type: x mandatory; display: flex; overflow-x: auto; width: 200px; }
.snap-item { scroll-snap-align: start; scroll-margin: 0 16px; min-width: 180px; flex-shrink: 0; }
```

- 두 번째 카드에 스냅이 끝났을 때, 카드 2 의 왼쪽 모서리는 컨테이너 왼쪽 끝에서 몇 px 떨어져 있나?

### 2. 스크롤하지 않은 상태의 카드 사이 (예측)

```css
/* 질문용 발췌 */
.snap-item { scroll-snap-align: start; scroll-margin: 0 16px; min-width: 180px; flex-shrink: 0; }
```

- 카드 1 과 카드 2 사이에는 눈에 보이는 틈이 몇 px 생기나?

### 3. 처음 화면의 카드 1 (경계)

- 페이지를 막 열었을 때 카드 1 도 컨테이너 왼쪽 끝에서 16px 안쪽에 보이나?

### 4. `start` 정렬에서 오른쪽 16px 의 역할 (경계)

- `scroll-snap-align: start` 일 때 `scroll-margin: 0 16px` 의 오른쪽 16px 을 0 으로 바꾸면 카드 2 의 멈출 자리가 달라지나?

### 5. 원본이 컨테이너가 아닌 자식에 단 까닭 (왜)

- 원본 팁이 「개별 자식 요소의 스냅 위치를 미세 조정」하려면 `scroll-margin` 을 자식에 달라고 하는 까닭은 무엇인가?

### 6. 컨테이너에 `mandatory` 를 둔 까닭 (왜)

- 이 데모에서 `scroll-snap-type` 을 `x mandatory` 로 두지 않으면 `scroll-margin` 의 효과를 확인하기 어려워지는 까닭은 무엇인가?

### 7. `scroll-padding` 과 나란히 놓기 (연결)

- 컨테이너의 `scroll-padding` 과 자식의 `scroll-margin` 은 스냅 계산에서 각각 어느 상자를 바꾸나?

### 8. 이름에 margin 이 들어간 두 속성 (연결)

- 배치 속성 `margin` 과 `scroll-margin` 은 무엇이 바뀌는지에서 어떻게 다른가?

## 실습

### 실습 1. 카드 하나하나가 조금 안쪽에 멈추는 가로 스냅 캐러셀

**만들 것** — 색이 다른 숫자 카드 셋을 가로로 스크롤하는 좁은 컨테이너를 만들고, 스냅할 때 카드가 컨테이너 왼쪽 끝에서 조금 안쪽에 멈추게 한다.

**요구 조건**
1. 컨테이너는 카드를 가로로 늘어놓고, 넘치는 카드는 가로 스크롤로 보여 준다.
2. 카드는 컨테이너보다 넓어도 줄어들지 않는다.
3. 컨테이너는 가로 방향으로, 스크롤이 끝나면 반드시 스냅 위치에 멈춘다.
4. 각 카드는 자신의 시작 모서리를 컨테이너 시작 모서리에 맞춰 스냅한다.
5. 각 카드의 스냅 영역에 위아래 0, 좌우 16px 의 스크롤 마진을 준다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>scroll-margin 연습</title>
  <style>
    .snap-container {
      /* TODO: 가로 방향 강제 스냅 */
      /* TODO: 자식을 가로로 배치 */
      /* TODO: 가로 스크롤 */
      border-radius: 12px;
      width: 200px;
      margin: 20px auto;
    }
    .snap-item {
      /* TODO: 시작 모서리에 스냅 정렬 */
      /* TODO: 위아래 0, 좌우 16px 스크롤 마진 */
      min-width: 180px;
      height: 100px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 28px;
      font-weight: bold;
      /* TODO: 줄어들지 않게 */
      border-radius: 8px;
    }
  </style>
</head>
<body>
  <div class="snap-container">
    <div class="snap-item" style="background:#06b6d4">1</div>
    <div class="snap-item" style="background:#8b5cf6">2</div>
    <div class="snap-item" style="background:#f59e0b">3</div>
  </div>
</body>
</html>
```

**확인 방법** — 브라우저로 열어 가로로 스크롤하고 손을 뗀 뒤, 카드 2 가 컨테이너 왼쪽 끝에서 약간 안쪽에 멈추는지, 카드 사이에는 틈이 없는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

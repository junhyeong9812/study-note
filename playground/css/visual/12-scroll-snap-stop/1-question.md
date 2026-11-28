# css/visual/12 — scroll-snap-stop — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 카드 1 에서 세게 한 번 밀면 (예측)

```css
/* 질문용 발췌 */
.snap-container { scroll-snap-type: x mandatory; display: flex; overflow-x: auto; width: 180px; }
.snap-item { scroll-snap-align: start; scroll-snap-stop: always; min-width: 180px; flex-shrink: 0; }
```

- 카드가 세 장일 때, 카드 1 이 보이는 상태에서 아주 빠르게 한 번 스와이프하면 어느 카드에서 멈추는가?

### 2. 같은 코드에서 값을 `normal` 로 바꾸면 (예측)

- 1번 코드의 `scroll-snap-stop` 만 `normal` 로 바꾸고 똑같이 세게 밀면, 멈추는 곳에 대해 무엇을 말할 수 있는가?

### 3. 아무 값도 쓰지 않은 스냅 캐러셀 (예측)

- `scroll-snap-stop` 을 한 줄도 쓰지 않은 스냅 캐러셀은 `normal` 과 `always` 가운데 어느 쪽처럼 움직이는가?

### 4. 기본값을 건너뛰기 허용으로 두고 `always` 를 따로 둔 까닭 (왜)

- 모든 스냅 캐러셀이 늘 한 칸씩 멈추지 않고, `always` 를 골라서 켜게 해 둔 까닭은 무엇인가?

### 5. 컨테이너에만 `always` 를 달면 (경계)

- `.snap-container` 에만 `scroll-snap-stop: always` 를 쓰고 `.snap-item` 에는 쓰지 않으면, 카드들은 건너뛰기가 막히는가?

### 6. 스냅 설정 없이 이 속성만 쓰면 (경계)

- `scroll-snap-type` 과 `scroll-snap-align` 이 없는 가로 스크롤 목록에 `scroll-snap-stop: always` 만 걸면 무슨 일이 생기는가?

### 7. `mandatory` 와 `always` 는 무엇이 다른가 (연결)

- `scroll-snap-type` 의 `mandatory` 가 정하는 것과 `scroll-snap-stop: always` 가 정하는 것은 각각 무엇인가?

### 8. 카드에 `flex-shrink: 0` 과 컨테이너 너비만 한 `min-width` 를 준 까닭 (연결)

- 이 두 선언이 「한 번 밀면 한 장」이라는 `always` 의 효과와 어떻게 맞물리는가?

## 실습

### 실습 1. 한 장씩만 넘어가는 가로 캐러셀

**만들 것** — 숫자 카드 세 장이 가로로 놓인 좁은 창을 만들고, 아무리 빠르게 밀어도 카드가 한 장씩만 넘어가게 한다.

**요구 조건**

1. 1단계 — 컨테이너가 카드들을 가로 한 줄로 늘어놓는다.
2. 1단계 — 컨테이너는 가로로 넘친 부분을 스크롤로 볼 수 있게 한다.
3. 1단계 — 카드는 줄어들지 않고, 카드 한 장의 최소 너비가 컨테이너 너비와 같아 창에 한 장만 보인다.
4. 2단계 — 컨테이너가 가로 축으로 반드시 스냅하는 스냅 컨테이너가 된다.
5. 2단계 — 각 카드의 시작 가장자리가 스냅 포인트가 된다.
6. 3단계 — 빠르게 스와이프해도 각 카드에서 반드시 멈춰, 중간 카드를 건너뛰지 못한다.
7. 카드 안의 숫자는 가운데에 놓인다(시작 코드에 채워 둔 그대로 둔다).

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>scroll-snap-stop 연습</title>
  <style>
    .snap-container {
      /* TODO: 가로 축 강제 스냅 */
      /* TODO: 가로 배치 */
      /* TODO: 가로 스크롤 */
      border-radius: 12px;
      width: 180px;
      margin: 20px auto;
    }
    .snap-item {
      /* TODO: 시작점 스냅 정렬 */
      /* TODO: 건너뛰기 막기 */
      /* TODO: 최소 너비를 컨테이너와 같게 */
      height: 100px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 32px;
      font-weight: bold;
      /* TODO: 축소 방지 */
    }
  </style>
</head>
<body>
  <div class="snap-container">
    <div class="snap-item" style="background:#ef4444">1</div>
    <div class="snap-item" style="background:#f59e0b">2</div>
    <div class="snap-item" style="background:#10b981">3</div>
  </div>
</body>
</html>
```

**확인 방법** — 브라우저로 열어 창에 카드가 한 장만 보이는지 보고, 트랙패드나 터치로 세게 밀어도 1 → 2 → 3 으로 한 장씩만 넘어가는지 본다. `always` 를 `normal` 로 바꿔 세게 밀었을 때와 비교해 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

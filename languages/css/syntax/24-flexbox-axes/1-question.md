# css/syntax/24 — Flexbox: 주축·교차축과 정렬(`justify-*`/`align-*`) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **상자가 화면 어디에 놓일지 맞힐 수 있는지**를 묻는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 상자 셋은 어디에 놓이는가 (예측)

```css
.row { display: flex; height: 120px;
       justify-content: space-between;
       align-items: center; }
```

- 상자 셋은 가로로 어떻게 놓이는가?
- 세로로는 어디에 놓이는가?
- `align-items: center` 줄을 지우면 상자의 **높이**가 어떻게 되는가?
- `height: 120px` 를 지우면 `align-items: center` 는 무엇을 하는가?

### 2. `flex-direction` 만 바꿨을 때 (예측)

```css
/* 두 컨테이너에 똑같이 걸린 선언 */
.f { display: flex; width: 150px; height: 150px;
     justify-content: flex-end;
     align-items: flex-start; }
.row { flex-direction: row; }
.col { flex-direction: column; }
```

- `.row` 안의 아이템들은 어느 모서리에 붙는가?
- `.col` 안의 아이템들은 어느 모서리에 붙는가?
- 두 결과가 정반대 모서리인 이유를 축의 이름으로 설명할 수 있는가?
- `.col` 을 `column-reverse` 로 바꾸면 아이템의 위치와 세로 순서가 각각 어떻게 되는가?

### 3. `flex-start` 인데 왼쪽이 아니다 (예측)

```css
.f { display: flex; flex-direction: row-reverse;
     justify-content: flex-start; }
```

- `1`, `2`, `3` 세 아이템은 화면에 어떤 순서로 보이는가?
- `1` 은 어느 쪽 끝에 붙는가?
- `justify-content` 를 `flex-end` 로 바꾸면 무엇이 달라지는가?
- 스크린 리더가 읽는 순서와 키보드 Tab 순서는 뒤집히는가?

### 4. 주축과 교차축은 대칭인가 (경계)

- 아이템 하나만 교차축에서 다르게 놓으려면 무엇을 쓰는가?
- 아이템 하나만 주축에서 다르게 놓으려면 무엇을 쓰는가?
- `justify-self` 를 flex 아이템에 주면 어떤 일이 일어나는가?
- 이 비대칭이 생기는 이유를 "자유 공간"이라는 말로 설명할 수 있는가?

### 5. 어느 축에 어느 값을 쓸 수 있는가 (경계)

- `space-between` 을 `align-items` 에 주면 어떻게 되는가, 왜 그런가?
- `stretch` 를 `justify-content` 에 주면 어떻게 되는가, 왜 그런가?
- `justify-content` 와 `align-items` 의 **초기값**은 각각 무엇인가?
- 그 초기값이 flex 컨테이너에서 실제로 어떻게 동작하는가?

### 6. 정렬이 안 먹는 세 가지 경우 (예측)

```html
<div class="flex">
  <div class="wrap"><div class="child">A</div></div>
</div>
```

- `.flex` 에 준 `justify-content` 는 `.child` 를 움직이는가?
- `flex-wrap` 없이 `align-content` 를 주면 무슨 일이 일어나는가?
- 아이템 하나에 `margin-left: auto` 가 있으면 `justify-content: center` 는 어떻게 보이는가?
- 이 셋의 공통점은 무엇인가(에러가 나는가, 조용히 지나가는가)?

### 7. `row` 는 정말 "가로"인가 (연결)

```css
.f { display: flex; direction: rtl; justify-content: flex-start; }
```

- 이 컨테이너에서 아이템들은 왼쪽부터 채워지는가, 오른쪽부터 채워지는가?
- `writing-mode: vertical-rl` 을 주면 `flex-direction: row` 의 주축은 어느 방향이 되는가?
- `row`/`column` 을 "가로/세로"가 아닌 말로 다시 정의할 수 있는가?
- 값 이름이 `left`/`top` 이 아니라 `flex-start` 인 이유는 무엇인가?

### 8. 다른 주제와 잇기 (연결)

- 행과 열을 동시에 맞춰야 하는 레이아웃에서 flex 대신 무엇을 쓰고, 그때 `justify-self` 는 쓸 수 있는가?
- `flex-direction` 을 전환에 태우면 왜 비싼가?
- `gap` 대신 아이템 `margin` 으로 간격을 주면 `justify-content` 와 무엇이 달라지는가?
- 이 주제가 다루지 않는 "아이템의 크기가 정해지는 규칙"은 목록의 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

# css/syntax/20 — 부동(float)과 해제(clear) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ★ **이 주제의 답은 두 겹이다** — 「상자가 어디 있나」와 「줄이 어디 있나」를 **따로** 답하라.
> 한쪽만 답하면 절반만 맞은 것이다. 실측 환경: Chrome 151 headless.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 형제 블록은 밀리는가 (예측)

```html
<div style="display:flow-root; width:300px">
  <div style="float:left; width:120px; height:80px"></div>
  <div>블록 1</div> <div>블록 2</div> … <div>블록 5</div>
</div>
```

- 다섯 형제 블록의 `rect.x` 와 `rect.width` 는 각각 몇인가?
- 그 블록들 안의 **행 상자**는 어디에서 시작하는가?
- 다섯 중 몇 번째부터 행 상자가 왼쪽 끝으로 돌아오는가?
- 블록에 배경색을 주면 화면에서 무엇이 보이는가?

### 2. float 와 absolute 는 무엇이 다른가 (경계)

- 둘 다 「흐름에서 빠진다」고 하는데, **빠지는 정도**가 어떻게 다른가?
- 같은 컨테이너에서 행 상자의 시작 x 와 폭이 각각 어떻게 되는가?
- 어느 쪽이 부모 높이 계산에 참여하는가?
- 「텍스트가 감싸 돌게」 하려면 둘 중 무엇을 써야 하는가?

### 3. `<span>` 에 float 를 걸면 (예측)

```css
span { float: left; width: 200px; height: 44px; }
```

- `getComputedStyle(span).display` 는 무엇인가?
- `width`·`height` 가 먹는가 — float 를 안 걸었을 때와 비교하면?
- `width` 선언을 지우면 폭이 몇이 되는가(규칙 이름으로 답하라)?
- float 한 블록 요소에 `width` 를 안 주면 부모 폭을 다 쓰는가?

### 4. `clear` 는 무엇을 하는가 (예측)

```html
<div>
  <div style="float:left;  width:90px; height:70px"></div>
  <div style="float:right; width:90px; height:40px"></div>
  <div id="대상" style="height:20px"></div>
</div>
```

- `대상` 에 `clear` 를 안 주면 y 는 몇인가?
- `clear: right` 를 주면?
- `clear: left` 와 `clear: both` 는?
- `clear` 는 위쪽 float 만 보는가, 아래쪽 것도 보는가?

### 5. `clear` 와 마진이 같이 있으면 (예측)

```css
.target { clear: left; margin-top: 10px; }   /* float 의 밑변은 71 */
.other  { clear: left; margin-top: 120px; }
```

- 두 경우의 y 는 각각 몇인가?
- `getComputedStyle().marginTop` 은 각각 무엇을 돌려주는가?
- 그 계산값만 보고 「마진이 안 먹었다」로 판정해도 되는가?
- `clear` 가 만드는 그 세로 간격의 이름은 무엇인가?

### 6. 높이 붕괴 (왜)

```html
<div class="p"><div style="float:left; width:90px; height:60px"></div></div>
```

- `.p` 의 `rect.height` 는 몇인가(테두리 2px 씩 있다고 하자)?
- 그것이 버그가 아닌 이유를 float 의 정의로 설명할 수 있는가?
- 다음 형제 블록은 어디에 놓이며, 화면에서는 무엇이 보이는가?
- 이것을 막는 법의 **정본은 몇 번 주제**인가?

### 7. flex 항목의 `float` (예측)

```css
.flex { display: flex; }
.flex > .a { float: left; }
```

- `.a` 의 `rect.x`·`rect.width` 는 float 를 안 걸었을 때와 다른가?
- `getComputedStyle(.a).float` 는 무엇을 돌려주는가?
- 그 계산값으로 「먹었다」를 판정할 수 있는가?
- 이 사실은 진단 3창 중 **어느 창의 한계**인가?

### 8. 여럿을 띄우면 (예측)

```css
.col { width: 300px; }  .col i { float: left; width: 120px; height: 40px; }
```

- 세 개를 넣으면 각각 어디에 놓이는가?
- 왜 셋째가 내려가는가 — float 끼리는 겹치는가?
- 컨테이너를 500px 으로 키우면?
- 이 배치가 옛 그리드였다면, 무엇 때문에 문제가 됐는가?

### 9. 오늘 float 에 남은 용도 (왜)

- flex·grid 가 있는데도 float 가 할 수 있는 일 **하나**는 무엇인가?
- flex 로는 왜 그것이 안 되는가?
- 감싸는 모양을 사각형이 아니게 바꾸는 속성 이름은 무엇인가(이 주제 밖)?
- 옛 코드의 `float: left; width: 33.33%` 를 오늘 무엇으로 옮기는가?

### 10. 다른 주제로 잇기 (연결)

- float 가 미는 「행 상자」의 정본은 몇 번 주제인가?
- float 는 세로 마진 상쇄에 참여하는가 — 그 정본은 몇 번인가?
- float 옆 블록에 BFC 를 열면 무엇이 달라지는가(상자인가 줄인가)?
- `float: inline-start` 가 글쓰기 방향에 따라 뒤집히는 규칙의 정본은 몇 번인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

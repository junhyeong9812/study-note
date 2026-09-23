# css/syntax/28 — Grid 배치: 라인 번호·`span`·자동 배치 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — **항목이 격자의 몇 번 칸에 놓이는지**를 맞힐 수 있는지 묻는다.
> 선행: [**27번**](../27-grid-track-sizing/)(트랙 정의). 트랙이 이미 있다고 보고 그 위에 무엇을 놓는지만 묻는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 라인 번호가 세는 것 (예측)

```css
.g { display: grid; grid-template-columns: repeat(4, 100px); }
.a { grid-column: 1 / 3; }
.b { grid-column: 1 / span 2; }
.c { grid-column: -3 / -1; }
```

- `.a` 는 몇 칸을 덮는가?
- `.a` 와 `.b` 의 결과는 같은가 다른가?
- `.c` 는 어느 칸들을 덮는가?
- 4열 격자의 세로 라인은 몇 개이고 번호는 무엇부터 무엇까지인가?

### 2. 「두 칸」을 쓰는 세 가지 (경계)

- `grid-column: 1 / 2` 는 몇 칸인가?
- 끝을 생략한 `grid-column: 2` 는 몇 칸인가?
- `span 2` 와 `2` 는 각각 무엇을 뜻하는가?
- `grid-column: span 2 / 5` 는 어느 칸들인가?

### 3. 음수 라인과 암묵 트랙 (예측)

```css
.g { display: grid; grid-template-columns: 100px 100px;
     grid-auto-columns: 60px; }
.far { grid-column: 5; }     /* 이것 때문에 열이 늘어났다 */
.neg { grid-column: -1; }
```

- `.far` 때문에 `gridTemplateColumns` 계산값은 무엇이 되는가?
- `.neg` 는 그 늘어난 격자의 **오른쪽 끝**에 놓이는가?
- 음수 라인은 어느 격자를 기준으로 세는가?
- `grid-column: 1 / -1` 이 「보이는 전체」가 아닐 수 있는 경우는 언제인가?

### 4. 정의 안 한 자리에 놓으면 (예측)

```css
.g { display: grid; grid-template-columns: 100px 100px;
     grid-template-rows: 32px;
     grid-auto-columns: 60px; grid-auto-rows: 24px; }
.far { grid-column: 4 / 5; }
.low { grid-row: 3; }
```

- 에러가 나는가?
- `gridTemplateColumns` 와 `gridTemplateRows` 의 계산값은 각각 무엇인가?
- 이 일이 일어난 것을 화면만 보고 알 수 있는가?
- `grid-column: 11` 이라는 오타가 만드는 증상은 무엇인가?

### 5. 자동 배치의 커서 (예측)

```css
.g { display: grid; grid-template-columns: repeat(4, 100px); }
.w3 { grid-column: span 3; }   /* 첫 항목 A */
.w2 { grid-column: span 2; }   /* 둘째 항목 B */
/* 그 뒤에 C, D 가 온다 */
```

- A·B·C·D 는 각각 몇 행 몇 열에 놓이는가?
- 빈칸은 어디에 생기는가, 왜 메워지지 않는가?
- `grid-auto-flow: row dense` 를 주면 C 와 D 의 자리는 어떻게 바뀌는가?
- 배치 알고리즘의 네 단계를 순서대로 말할 수 있는가?

### 6. `dense` 의 대가 (연결)

- `dense` 는 마크업 순서를 바꾸는가?
- 스크린 리더와 키보드 Tab 이 읽는 순서는 무엇을 따르는가?
- 이 문제는 목록의 어느 주제의 어떤 속성과 같은 계열인가?
- `dense` 를 써도 되는 콘텐츠와 쓰면 안 되는 콘텐츠를 어떻게 가르는가?

### 7. 겹침 (예측)

```css
.p { grid-area: 1 / 1 / 2 / 3; background: red; }
.q { grid-area: 1 / 1 / 2 / 2; background: green; }   /* 마크업에서 뒤에 온다 */
```

- 두 항목은 겹치는가, 아니면 행이 하나 늘어나는가?
- 겹친다면 위에 보이는 것은 어느 쪽인가?
- 그것을 뒤집으려면 무엇을 쓰는가?
- flex 에서 같은 일을 하려면 무엇이 필요한가?

### 8. `grid-area` 의 네 값 (경계)

- `grid-area: 1 / 2 / 3 / 4` 의 네 값은 각각 무엇인가?
- 그 순서는 `margin` 의 네 값 순서와 같은가?
- 값을 둘만 쓰면(`grid-area: 2 / 1`) 무엇이 되는가?
- `grid-area` 에 이름 하나만 쓰는 형태는 어느 주제가 정본인가?

### 9. 무효한 값과 뒤집힌 값 (경계)

- `grid-column: 0` 은 유효한가?
- `grid-column: 2 / 1` 처럼 시작이 끝보다 뒤면 버려지는가?
- 그 사실을 `getComputedStyle` 만으로 알 수 있는가?
- 대조군을 깔고 확인하는 방법을 쓸 수 있는가?

### 10. Grid 에만 있는 정렬 (연결)

- `justify-self` 를 flex 아이템에 주면 어떻게 되는가?
- Grid 에서는 왜 그것이 성립하는가 — 「자유 공간」이라는 말로 설명하라
- `justify-items` 와 `justify-self` 는 각각 무엇을 정하는가?
- 정렬 어휘 전반의 정본은 목록의 몇 번 주제인가?

### 11. `grid-auto-flow: column` (경계)

- 커서가 어떻게 움직이는가?
- flex 의 `flex-direction: column` 과 무엇이 다른가?
- 명시 열이 둘뿐인 격자에 항목 5개를 넣고 `column` 흐름을 주면 계산값은 무엇이 되는가?
- 그때 `justify-content` 의 의미는 바뀌는가?

### 12. 다른 주제와 잇기 (연결)

- 이 격자의 트랙을 만드는 규칙은 목록의 몇 번 주제인가?
- 번호 대신 이름으로 놓는 것은 몇 번 주제인가?
- Grid 항목의 마진은 상쇄되는가, 그 정본은 몇 번 주제인가?
- 「명세가 보장하는 것」과 「Chrome 151 에서 관찰한 것」을 이 주제에서 하나씩 들 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

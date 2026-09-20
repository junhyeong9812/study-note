# css/syntax/52 — `transition`: 전환 가능한 속성·타이밍 함수·지연·`transition-behavior` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **몇 초 뒤에 무엇이 어디까지 가 있는지**를 묻는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 이 버튼은 어떻게 바뀌는가 (예측)

```css
.btn { background-color: #e2e8f0; transition: background-color .6s ease; }
.btn:hover { background-color: #1d4ed8; }
```

- 마우스를 올린 뒤 몇 초 만에 색이 다 바뀌는가?
- 마우스를 뗐을 때도 같은 시간이 걸리는가?
- 시간이 절반(0.3초) 지났을 때 색은 몇 퍼센트쯤 와 있는가?
- 그 답이 50%가 아닌 이유는 무엇인가?

### 2. 두 상자 중 어느 쪽이 부드러운가 (예측)

```css
.card { height: 24px; overflow: hidden; transition: height 1s linear; }
.auto:hover  { height: auto; }
.fixed:hover { height: 48px; }
```

- 두 상자 중 어느 쪽이 1초에 걸쳐 펴지는가?
- 다른 쪽은 어떻게 되는가?
- 콘솔에 에러나 경고가 찍히는가?
- 내용 높이를 모르는 채로 펼치는 전환을 만들려면 무엇을 쓸 수 있는가?

### 3. 왜 들어갈 때만 부드러운가 (경계)

```css
.btn:hover { background-color: red; transition: background-color 1s linear; }
```

- 마우스를 올릴 때 전환이 걸리는가?
- 마우스를 뗄 때는 어떻게 되는가, 왜 그런가?
- `transition` 은 어느 규칙에 써야 양방향이 되는가?
- 들어올 때와 나갈 때 시간을 다르게 하고 싶다면 어떻게 쓰는가?

### 4. 이 상자는 언제부터 언제까지 움직이는가 (예측)

```css
.box { background-color: #94a3b8;
       transition: background-color 0.2s linear 1s; }
.box:hover { background-color: #b91c1c; }
```

- 마우스를 올린 뒤 0.5초 시점의 색은 무엇인가?
- 변화가 시작되는 시각과 끝나는 시각은 각각 언제인가?
- 두 시간 값 중 어느 쪽이 지속이고 어느 쪽이 지연인가?
- 시간 값을 하나만 쓰면(`transition: background-color 1s`) 그것은 무엇이 되는가?
- 지연에 음수(`-0.5s`)를 주면 무슨 일이 일어나는가?

### 5. 1초 시점에 넷은 어디에 있는가 (예측)

```css
/* 네 막대가 동시에 출발해 2초 동안 260px 를 간다 */
.linear { transition-timing-function: linear; }
.ease   { transition-timing-function: ease; }
.ei     { transition-timing-function: ease-in; }
.st     { transition-timing-function: steps(4, end); }
```

- 2초 뒤 넷의 위치는 같은가 다른가?
- 1초(절반) 시점에 넷 중 가장 앞선 것과 가장 뒤진 것은 무엇인가?
- 출발 직후 50ms 시점에 `steps(4, end)` 는 어디에 있는가?
- `steps(4, end)` 를 `steps(4, start)` 로 바꾸면 50ms 시점이 어떻게 달라지는가?
- 타이밍 함수는 도착 **시각**을 바꾸는가, 도중의 **위치**를 바꾸는가?

### 6. 도중에 마우스를 떼면 (왜)

```css
.rev { transition: margin-left 2s linear; }
.rev:hover { margin-left: 200px; }
```

- 2초짜리 전환의 0.6초 지점에서 마우스를 떼면 되돌아오는 데 몇 초가 걸리는가?
- 그 값이 2초가 아닌 이유를 명세의 어떤 규칙으로 설명할 수 있는가?
- 이 규칙이 없으면 목록 위를 마우스로 훑을 때 무엇이 보이는가?
- `transitionend` 를 기다리는 JS 타이머를 `duration` 으로 잡으면 무엇이 어긋나는가?

### 7. 이 네 막대는 왜 똑같이 움직이는가 (경계)

```css
.lane i { transition: margin-left 2s; }
.linear { transition-timing-function: linear; }
.ease   { transition-timing-function: ease; }
```

- `.linear` 막대는 등속으로 움직이는가?
- 그렇지 않다면 무엇이 그것을 덮었는가?
- 두 규칙의 명시도는 각각 얼마인가?
- 화면만 보고 이 문제를 알아챌 수 있는가, 아니면 무엇을 해야 하는가?
- 고치는 방법 두 가지를 들 수 있는가?

### 8. 다른 주제와 잇기 (연결)

- 0% → 50% → 100% 로 들르는 지점이 있는 움직임은 무엇으로 만드는가?
- `display: none` 이던 요소가 나타날 때 전환이 안 걸리는 이유는 무엇이고, 무엇이 그것을 가능하게 했는가?
- 전환이 도는 동안의 값을 `!important` 로 덮을 수 있는가, 그 이유를 캐스케이드로 설명할 수 있는가?
- `width` 를 전환하는 것과 `transform: scaleX()` 를 전환하는 것은 무엇이 다른가?
- 모션에 민감한 사용자를 위해 전환을 "끄는 것"이 왜 최선이 아닌가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

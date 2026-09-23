# css/syntax/53 — `@keyframes` 와 `animation`: 단축·반복·채우기 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **몇 초 시점에 무엇이 얼마인지**를 묻는다.
> 선행은 [52번 주제](../52-transition/2-summary.md)다. 「전환으로는 못 하는 것」을 먼저 떠올리고 시작하라.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 전환과 무엇이 갈리는가 (연결)

- 전환은 무엇이 있어야 시작되고, 애니메이션은 무엇이 있어야 시작되는가?
- 전환으로 만들 수 없는 움직임 네 가지를 들 수 있는가?
- 전환이 끝나면 요소는 어디에 있고, 애니메이션이 끝나면 어디에 있는가?
- 같은 속성을 `!important` 로 덮으려 할 때 전환과 애니메이션의 답이 왜 반대인가?

### 2. 양 끝을 안 적으면 어디서 출발하는가 (예측)

```css
.q { width: 120px; animation: half 4s linear; }
@keyframes half { 50% { width: 400px } }
```

- 0초 시점의 폭은 얼마인가?
- 2초 시점의 폭은 얼마인가?
- 4초가 다 됐을 때 폭은 얼마인가?
- `@keyframes only100 { to { width: 400px } }` 로 바꾸면 1초 시점은 얼마인가?
- 브라우저는 안 적은 키프레임을 **무엇을 기준으로** 만드는가?

### 3. 이 단축 세 줄은 각각 무엇이 되는가 (예측)

```css
.s1 { animation: w 2s 1s linear paused; }
.s2 { animation: 1s 2s linear w paused; }
.s3 { animation: w 3s linear paused; }
```

- 셋의 `animation-duration` 과 `animation-delay` 는 각각 얼마인가?
- 이름을 맨 뒤에 써도 되는 이유는 무엇이고, 시간 값만 순서를 따지는 이유는 무엇인가?
- 세 줄 모두 `animation-fill-mode` 는 무엇이 되는가?
- `animation: pulse infinite;` 라고만 쓰면 화면에서 무슨 일이 일어나는가?

### 4. 네 막대는 언제 어디에 있는가 (예측)

```css
/* 기본 폭 100px · from 50px · to 250px · 지연 1s · 지속 2s */
.none { animation: w 2s linear 1s 1 normal none; }
.fwd  { animation: w 2s linear 1s 1 normal forwards; }
.bwd  { animation: w 2s linear 1s 1 normal backwards; }
.both { animation: w 2s linear 1s 1 normal both; }
```

- 0.5초 시점(지연 중)에 넷의 폭은 각각 얼마인가?
- 3.5초 시점(끝난 뒤)에 넷의 폭은 각각 얼마인가?
- 2초 시점(움직이는 중)에 넷은 같은가 다른가?
- 지연을 `0s` 로 바꾸면 네 값 중 어느 둘을 **구분할 수 없게** 되는가?

### 5. `alternate` 를 두 번 돌리면 어디서 멈추는가 (예측)

```css
@keyframes w { from { width: 40px } to { width: 280px } }
.n { animation: w 1s linear 0s 2 normal    forwards; }
.a { animation: w 1s linear 0s 2 alternate forwards; }
```

- 2.3초 시점에 두 막대의 폭은 각각 얼마인가?
- 1.5초 시점의 값이 둘 다 비슷하게 나오는데, 그때 둘은 각각 무엇을 하고 있는가?
- `forwards` 를 붙였는데 `.a` 가 시작값에서 끝나는 이유를 한 문장으로 설명할 수 있는가?
- 반복을 `3` 으로 바꾸면 `.a` 는 어디서 끝나는가?

### 6. 이 애니메이션은 왜 절반까지 느린가 (예측)

```css
@keyframes perkf {
  from { width: 0px;   animation-timing-function: ease-in }
  50%  { width: 100px; animation-timing-function: linear }
  to   { width: 200px }
}
/* 4초 linear 로 재생한다 */
```

- 0.5초 시점의 폭은 전부 `linear` 인 경우와 비교해 큰가 작은가?
- 2.5초 시점은 어떤가?
- 키프레임 안에 쓴 타이밍 함수는 **어느 구간**에 적용되는가?
- `to` 블록 안에 타이밍 함수를 써 두면 무슨 일이 일어나는가?

### 7. 누가 이기는가 (경계)

```css
#p { width: 10px !important; animation: gw 4s linear -2s paused; }
#q { width: 10px;            animation: gw 4s linear -2s paused; }
@keyframes gw { from { width: 0px } to { width: 400px } }
```

- `#p` 와 `#q` 의 폭은 각각 얼마인가?
- 같은 상황에서 전환(`transition`)이었다면 답이 어떻게 달라지는가?
- 캐스케이드 사다리에서 전환 선언·작성자 `!important`·애니메이션 선언의 순서를 적을 수 있는가?
- `@keyframes` 안에 `!important` 를 쓰면 그 선언은 **어떤 상태**가 되는가 — 지는가, 사라지는가?

### 8. 같은 이름을 두 번 쓰면 (예측)

```css
#x { width: 10px; height: 14px; animation: dup 4s linear -2s paused; }
@keyframes dup { from { width: 0px }   to { width: 400px } }
@keyframes dup { from { height: 10px } to { height: 60px } }
```

- `#x` 의 폭과 높이는 각각 얼마인가?
- `document.styleSheets[…].cssRules` 에는 `@keyframes` 가 몇 개 담겨 있는가?
- 두 악보는 합쳐지는가, 한쪽만 사는가?
- 한 요소에 `animation: k1 …, k2 …` 로 둘을 걸고 둘 다 `width` 를 건드리면 누가 이기는가?

### 9. 선언은 멀쩡한데 아무 일도 안 난다 (경계)

```css
@keyframes real { from { width: 60px } to { width: 300px } }
#b { animation: typoo 4s linear; }
```

- `cssRules` 에 악보가 담겨 있는가?
- `getComputedStyle(#b).animationName` 은 무엇을 돌려주는가?
- `getComputedStyle(#b).width` 는 무엇인가?
- 이 증상은 진단 3창(`cssRules` → `querySelectorAll` → `getComputedStyle`) 중 어디에서 잡히는가?
- 잡히지 않는다면 **네 번째 창**으로 무엇을 쓰는가?

### 10. 진행률을 고정해 재는 법 (왜)

```css
.probe { animation: grow 4s linear -1s paused; }
```

- 이 선언은 악보의 몇 % 지점에서 멈춘 상태인가?
- 왜 `animation-delay` 를 음수로 주면 그렇게 되는가?
- `el.getAnimations()[0].currentTime = 4000` 으로 끝 시각을 세팅했는데 폭이 원래 값으로 돌아왔다 — 왜인가?
- 시간이 걸린 실험을 `--virtual-time-budget` 으로 재면 무엇이 찍히는가?

### 11. 멈출 방법 (경계)

```css
#x   { animation: w 2s linear infinite alternate paused; }
#x:hover { animation-play-state: running; }
```

- 마우스를 올리기 전 `width` 는 얼마인가?
- 마우스를 1.6초쯤 올렸다가 떼면 막대는 처음 자리로 돌아가는가, 그 자리에 서는가?
- `paused` 와 「애니메이션을 지우는 것」은 무엇이 다른가?
- 모션에 민감한 사용자를 위한 처리는 어느 주제가 정본인가?

### 12. 다른 주제와 잇기 (연결)

- 커스텀 속성 `--angle` 을 애니메이션했더니 중간이 없고 계단 하나만 나온다 — 무엇이 빠졌는가?
- 같은 움직임을 `left` 로 만들 때와 `transform` 으로 만들 때 무엇이 다른가, 그 정본은 어느 주제인가?
- 애니메이션에 `transform` 을 쓰면 그 요소에 딸려 오는 **부작용** 두 가지는 무엇인가?
- 스크롤 진행에 맞춰 움직이게 하려면 무엇을 쓰는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

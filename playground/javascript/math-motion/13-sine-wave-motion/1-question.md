# javascript/math-motion/13 — Sine Wave Motion — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 시간이 흐를 때 물결 모양이 흘러가는 방향 (예측)

```javascript
// 질문용 발췌 — 점 i 는 왼쪽(0)에서 오른쪽(24)으로 놓인다
const phase = (i / dotCount) * Math.PI * 2;
const x = (i + 0.5) / dotCount * cw;
const y = cy + amp * Math.sin(t * freq + phase);
```

- t 가 커질 때 화면의 물결 모양은 왼쪽과 오른쪽 중 어느 쪽으로 흘러가 보이는가?

### 2. 점의 크기 배율이 오가는 범위 (예측)

```javascript
// 질문용 발췌
const scale = 0.7 + 0.3 * Math.sin(t * freq + phase);
```

- `scale` 이 가질 수 있는 가장 작은 값과 가장 큰 값은 무엇인가?
- 점이 가장 클 때 화면에서 위쪽과 아래쪽 중 어디에 있는가?

### 3. 주파수 슬라이더가 2 일 때의 왕복 시간 (예측)

- `freq` 가 2 일 때 점 하나가 한 번 왕복해 제자리로 돌아오는 데 대략 몇 초가 걸리는가?

### 4. `time` 에 0.001 을 곱하는 까닭 (왜)

- `animate(time)` 안에서 `time` 을 그대로 쓰지 않고 `time * 0.001` 로 바꾸는 까닭은 무엇인가?

### 5. `transform` 에 `translate(-50%, -50%)` 를 다시 적는 까닭 (왜)

- CSS 에 이미 `translate(-50%, -50%)` 가 있는데 자바스크립트에서 `scale` 과 함께 또 적는 까닭은 무엇인가?

### 6. 움직이는 도중 주파수를 바꾸면 (경계)

- 애니메이션이 한참 돈 뒤 주파수 슬라이더를 움직이면 점들의 움직임이 매끄럽게 이어지는가, 그렇지 않다면 왜 그런가?

### 7. 진폭을 가장 크게 올렸을 때 (경계)

- 높이 250 인 컨테이너에서 진폭을 최대 80 으로 올리면 점의 중심은 컨테이너 안에 머무는가?

### 8. 점 25개에 위상을 나눠 주는 것과 진행파 (연결)

- 각 점은 제자리에서 위아래로만 움직이는데, 왜 화면에는 물결이 옆으로 흘러가는 것처럼 보이는가?

### 9. CSS `@keyframes` 와 자바스크립트 사인파 (연결)

- 이 예제를 CSS `@keyframes` 만으로 만들려 할 때 어떤 부분이 어려워지는가?

## 실습

### 실습 1. 사인파를 따라 출렁이는 점 25개

**만들 것** — 컨테이너 안에 가로로 늘어선 점 25개가 사인파를 따라 위아래로 출렁이며 물결처럼 흐르고, 진폭 · 주파수 슬라이더로 크기와 빠르기를 실시간으로 바꾸는 애니메이션을 만든다.

**요구 조건**

1단계 — 준비

1. 컨테이너, 진폭 슬라이더, 주파수 슬라이더, 두 값 표시 요소를 id 로 찾아 변수에 담는다.
2. 점 25개를 `div` 로 만들어 `sine-dot` 클래스를 주고, 번호에 따라 색을 바꿔 컨테이너에 넣고 배열에 모은다.
3. 각 슬라이더의 `input` 이벤트에서 옆의 표시 요소 글자를 슬라이더 값으로 바꾼다.

2단계 — 매 프레임 계산 (`animate(time)`)

4. 밀리초 시각을 초로 바꾼다.
5. 두 슬라이더 값을 숫자로 읽어 진폭과 주파수로 쓴다.
6. 컨테이너 높이의 절반을 세로 중심으로, 컨테이너 너비를 가로 길이로 읽는다.
7. 점마다 위상을 번호에 비례해 0 ~ 2π 로 균등하게 나눈다.
8. 점의 가로 자리를 컨테이너 너비를 25칸으로 나눈 각 칸의 한가운데로 정한다.
9. 점의 세로 자리를 「중심 + 진폭 × sin(시간 × 주파수 + 위상)」으로 정한다.
10. 같은 사인 값으로 크기 배율을 「0.7 + 0.3 × sin(…)」으로 정한다.
11. 가로 · 세로 자리를 `left` · `top` 에 쓰고, 가운데 정렬과 크기 배율을 함께 `transform` 에 쓴다.
12. 함수 끝에서 다음 프레임을 예약하고, 맨 처음에도 한 번 예약해 시작한다.

**시작 코드**

```html
<div class="sine-container" id="sineContainer"></div>
<p class="info">사인파를 따라 움직이는 물결 패턴</p>
<div class="controls">
  <label>진폭: <input type="range" id="sineAmp" min="10" max="80" value="40"><span id="sineAmpVal">40</span></label>
  <label>주파수: <input type="range" id="sineFreq" min="0.5" max="5" step="0.1" value="2"><span id="sineFreqVal">2</span></label>
</div>
<style>
  .sine-container { position: relative; width: 100%; height: 250px; background: #0f172a; border-radius: 8px; overflow: hidden; }
  .sine-dot { position: absolute; width: 16px; height: 16px; border-radius: 50%; transform: translate(-50%, -50%); }
</style>
<script src="sine-wave-motion.js"></script>
```

```javascript
// sine-wave-motion.js
const container = document.getElementById('sineContainer');
// TODO: 진폭 · 주파수 슬라이더와 두 값 표시 요소를 찾는다

const dotCount = 25;
const dots = [];

for (let i = 0; i < dotCount; i++) {
  // TODO: div 를 만들고 sine-dot 클래스를 준다
  const hue = (i / dotCount) * 200 + 180;
  dot.style.background = `hsl(${hue}, 70%, 55%)`;
  dot.style.boxShadow = `0 0 10px hsla(${hue}, 70%, 55%, 0.4)`;
  // TODO: 컨테이너에 넣고 dots 에 모은다
}

// TODO: 슬라이더를 움직이면 옆 숫자를 바꾼다

function animate(time) {
  // TODO: 밀리초 → 초
  // TODO: 진폭 · 주파수를 숫자로 읽는다
  // TODO: 세로 중심과 가로 길이를 읽는다

  dots.forEach((dot, i) => {
    // TODO: 위상 (0 ~ 2π 균등)
    // TODO: x (칸의 한가운데)
    // TODO: y = 중심 + 진폭 * sin(시간 * 주파수 + 위상)
    // TODO: scale = 0.7 + 0.3 * sin(같은 각도)
    // TODO: left · top · transform 에 쓴다
  });
  // TODO: 다음 프레임 예약
}
// TODO: 애니메이션 시작
```

**확인 방법** — HTML 파일을 브라우저로 열어, 점 25개가 물결 모양으로 출렁이며 옆으로 흘러가는지, 아래로 내려간 점이 더 크게 보이는지, 슬라이더를 움직이면 옆 숫자와 함께 흔들림의 폭 · 빠르기가 바뀌는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

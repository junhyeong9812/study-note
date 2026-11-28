# javascript/math-motion/13 — Sine Wave Motion — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 물결은 오른쪽에서 왼쪽으로 흘러간다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

물결 모양은 왼쪽으로 흘러가 보인다.

**왜 그런가**

- 모든 점의 각도는 `t * freq` 만큼 똑같이 커진다.
- 오른쪽 점(i 가 큰 점)일수록 `phase` 가 커서 각도가 앞서 있다.
- 그래서 어떤 높이(예: 가장 아래)에 오른쪽 점이 먼저 닿고, 그 왼쪽 점이 조금 뒤에 닿는다.
- 같은 높이가 오른쪽에서 왼쪽으로 옮겨 가므로 물결이 왼쪽으로 흐르는 것처럼 보인다.
- 근거: 2-summary 「동작 방식 (3)」.

### 2. 0.4 ~ 1.0, 가장 클 때는 가장 아래

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

가장 작은 값은 0.4, 가장 큰 값은 1.0 이다.
가장 클 때 점은 화면 아래쪽 끝에 있다.

**왜 그런가**

- `Math.sin` 은 -1 ~ 1 이므로 `0.7 + 0.3 × (-1) = 0.4`, `0.7 + 0.3 × 1 = 1.0` 이다.
- 원본 주석의 「0.7~1.0」은 sin 이 0 이상인 절반만 본 것이다.
- 크기와 위치가 같은 각도를 쓰므로, sin 이 1 일 때 크기는 1.0 이고 y 는 `cy + amp` 로 가장 크다.
- 화면 좌표는 y 가 클수록 아래이므로, 가장 큰 점은 가장 아래에 있다.
- 근거: 2-summary 「동작 방식 (4)」 · 「동작 방식 (5)」 · 「어디서 틀리나 6, 7」.

### 3. 약 3.14 초

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

약 3.14 초(π 초)다.

**왜 그런가**

- 각도가 2π 커져야 한 번 왕복한다.
- 각도는 1초에 `freq` 라디안씩 커지므로 주기는 `2π / freq` 다.
- `freq` 가 2 이면 2π / 2 = π ≈ 3.14 초다.
- 「주파수 2」를 「1초에 2번」으로 읽으면 0.5 초라고 틀리게 답한다.
- 근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 4」.

### 4. 밀리초를 초로 바꿔 빠르기를 알맞게 맞추려고

`requestAnimationFrame` 이 넘겨주는 `time` 은 밀리초다.
그대로 각도에 쓰면 1초에 각도가 1000배 커져 움직임이 알아볼 수 없을 만큼 빨라진다.
0.001 을 곱해 초로 바꾸면 `freq` 가 「1초에 몇 라디안」이라는 뜻이 되어, 슬라이더 범위 0.5 ~ 5 가 눈에 보이는 빠르기가 된다.
근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 1」.

### 5. 스크립트의 `transform` 이 CSS 의 `transform` 을 통째로 대신하기 때문

`dot.style.transform` 에 값을 쓰면 CSS 규칙의 `transform` 값은 쓰이지 않는다.
`scale(...)` 만 쓰면 `translate(-50%, -50%)` 가 사라져 점의 왼쪽 위 모서리가 (x, y) 에 놓인다.
그러면 점의 중심이 계산한 자리에서 반 점만큼 어긋난다.
그래서 가운데 정렬과 크기 배율을 한 값에 함께 적는다.
근거: 2-summary 「어디서 틀리나 3」 · 「문법 — 형태와 규칙」.

### 6. 매끄럽지 않을 수 있다 — 각도가 한꺼번에 건너뛴다

각도를 매 프레임 `t * freq + phase` 로 새로 계산하기 때문이다.
`freq` 가 바뀌는 순간 각도는 `t × (바뀐 양)` 만큼 한꺼번에 달라진다.
t 는 페이지가 열린 뒤 흐른 초라서 오래 돌았을수록 그 차이가 커지고, 점이 곡선의 엉뚱한 자리로 건너뛴다.
진폭은 각도와 상관없이 폭만 바꾸므로 이런 건너뜀이 생기지 않는다 (원본에 근거 없음 — 추론).
근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 5」.

### 7. 머문다 — 45 ~ 205 사이

`cy` 는 250 / 2 = 125 다.
진폭 80 이면 점의 중심은 125 - 80 = 45 에서 125 + 80 = 205 사이를 오간다.
둘 다 0 ~ 250 안이므로 중심은 컨테이너 안에 머문다.
점 지름이 16 이고 크기 배율이 1.0 이하라서 가장자리까지 넉넉하다.
근거: 2-summary 「동작 방식 (4)」.

### 8. 이웃한 점이 같은 움직임을 조금씩 늦게 되풀이하기 때문

각 점은 제자리에서 같은 진폭 · 같은 빠르기로 오르내린다.
다만 위상이 0 ~ 2π 로 나뉘어 있어, 같은 순간에 점마다 사인 곡선의 다른 자리에 있다.
그래서 가로로 늘어놓으면 곡선 한 마디가 그려지고, 시간이 흐르면 같은 높이가 이웃 점으로 차례차례 넘어간다.
점은 옆으로 가지 않는데 모양이 옆으로 옮겨 가는 것, 이것이 진행파다.
근거: 2-summary 「동작 방식 (3)」.

### 9. 정확한 사인 곡선 · 실시간 값 바꾸기 · 점마다 다른 위상 · 파형 합치기

이 항목의 팁대로 `@keyframes` 로도 비슷한 왕복은 만들 수 있다.
그러나 사인 곡선을 그대로 따르게 하기, 슬라이더로 진폭 · 빠르기를 즉시 바꾸기, 25개 점에 계산한 위상을 나눠 주기, 여러 사인파를 더해 복잡한 파형 만들기는 자바스크립트가 더 유연하다.
근거: 2-summary 「어디서 틀리나 8」 · 「언제 쓰고 언제 안 쓰나」.

## 실습 정답

### 실습 1. 사인파를 따라 출렁이는 점 25개

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 요소 찾기 | `container` · `ampSlider` · `freqSlider` · `ampVal` · `freqVal` 의 `document.getElementById` |
| 2. 점 25개 만들기 | `for` 고리의 `document.createElement('div')` · `dot.className = 'sine-dot'` · `hue` · `container.appendChild(dot)` · `dots.push(dot)` |
| 3. 슬라이더 표시 갱신 | `ampSlider.addEventListener('input', …)` · `freqSlider.addEventListener('input', …)` |
| 4. 밀리초 → 초 | `const t = time * 0.001` |
| 5. 진폭 · 주파수 읽기 | `parseFloat(ampSlider.value)` · `parseFloat(freqSlider.value)` |
| 6. 세로 중심 · 가로 길이 | `container.offsetHeight / 2` · `container.offsetWidth` |
| 7. 위상 나누기 | `const phase = (i / dotCount) * Math.PI * 2` |
| 8. 가로 자리 | `const x = (i + 0.5) / dotCount * cw` |
| 9. 세로 자리 | `const y = cy + amp * Math.sin(t * freq + phase)` |
| 10. 크기 배율 | `const scale = 0.7 + 0.3 * Math.sin(t * freq + phase)` |
| 11. 스타일 쓰기 | `dot.style.left` · `dot.style.top` · `` dot.style.transform = `translate(-50%, -50%) scale(${scale})` `` |
| 12. 프레임 예약 · 시작 | `animate` 끝의 `requestAnimationFrame(animate)` · 맨 아래 `requestAnimationFrame(animate)` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`javascript/math-motion/reference/sine-wave-motion.js`

```javascript
// [수학 & 모션 공식] Sine Wave Motion
// 설명: 사인 함수로 주기적 왕복 운동. 파도, 호흡, 펄스 효과의 기본
// 팁: amplitude=크기, frequency=빠르기, phase=시작 오프셋. 여러 사인파를 합치면 복잡한 파형 생성 가능. CSS로도 @keyframes로 유사한 효과를 만들 수 있지만 JS가 더 유연.

// 파도 점들이 표시될 영역
const container = document.getElementById('sineContainer');
// 진폭 슬라이더 (파도 크기)
const ampSlider = document.getElementById('sineAmp');
// 주파수 슬라이더 (빠르기)
const freqSlider = document.getElementById('sineFreq');
// 슬라이더 값 표시
const ampVal = document.getElementById('sineAmpVal');
const freqVal = document.getElementById('sineFreqVal');

// 가로로 배치할 점 개수
const dotCount = 25;
const dots = [];

// 25개 점 DOM 요소 생성 (색상은 인덱스에 따라 변화)
for (let i = 0; i < dotCount; i++) {
  const dot = document.createElement('div');
  dot.className = 'sine-dot';
  // hue 180~380 → 청록부터 빨강까지 (실제로는 360 wrap)
  const hue = (i / dotCount) * 200 + 180;
  dot.style.background = `hsl(${hue}, 70%, 55%)`;
  dot.style.boxShadow = `0 0 10px hsla(${hue}, 70%, 55%, 0.4)`;
  container.appendChild(dot);
  dots.push(dot);
}

// 슬라이더 값 변경 시 표시 갱신
ampSlider.addEventListener('input', () => ampVal.textContent = ampSlider.value);
freqSlider.addEventListener('input', () => freqVal.textContent = freqSlider.value);

// 매 프레임 사인 함수로 점들의 y 좌표 갱신
function animate(time) {
  // ms → 초
  const t = time * 0.001;
  // 현재 진폭, 주파수 읽기
  const amp = parseFloat(ampSlider.value);
  const freq = parseFloat(freqSlider.value);
  // 컨테이너 가로/세로 중심
  const cy = container.offsetHeight / 2;
  const cw = container.offsetWidth;

  dots.forEach((dot, i) => {
    // 각 점마다 다른 위상(0~2PI 균등 분할) → 진행파 형태
    const phase = (i / dotCount) * Math.PI * 2;
    // x 좌표는 컨테이너에 균등 분배 ((i+0.5)/n 으로 양 끝 여백 포함)
    const x = (i + 0.5) / dotCount * cw;
    // y = 중심 + 진폭 * sin(시간*주파수 + 위상) → 위아래 진동
    const y = cy + amp * Math.sin(t * freq + phase);
    // 크기도 sin으로 변동: 0.7~1.0 사이 (호흡감)
    const scale = 0.7 + 0.3 * Math.sin(t * freq + phase);
    dot.style.left = x + 'px';
    dot.style.top = y + 'px';
    // 중앙 정렬 + 스케일
    dot.style.transform = `translate(-50%, -50%) scale(${scale})`;
  });
  requestAnimationFrame(animate);
}
// 애니메이션 시작
requestAnimationFrame(animate);
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```html
<div class="sine-container" id="sineContainer"></div>
<p class="info">사인파를 따라 움직이는 물결 패턴</p>
<div class="controls">
  <label>진폭: <input type="range" id="sineAmp" min="10" max="80" value="40"><span id="sineAmpVal">40</span></label>
  <label>주파수: <input type="range" id="sineFreq" min="0.5" max="5" step="0.1" value="2"><span id="sineFreqVal">2</span></label>
</div>
```

```css
.sine-container { position: relative; width: 100%; height: 250px; background: #0f172a; border-radius: 8px; overflow: hidden; }
.sine-dot { position: absolute; width: 16px; height: 16px; border-radius: 50%; transform: translate(-50%, -50%); }
```

**실행 결과** — 실행하지 않음 — 브라우저 DOM API 를 쓰는 예제다 — 브라우저에서 확인한다.

**풀이 요점**

- 핵심 한 줄은 `y = cy + amp * Math.sin(t * freq + phase)` 다 — 중심 + 진폭 × sin(시간 × 빠르기 + 위상).
- 위상을 `(i / dotCount) * 2π` 로 나눠 주는 것이 점 하나의 흔들림을 물결로 바꾸는 열쇠다.
- 같은 사인 값을 크기에도 써서 아래로 내려간 점이 커지는 호흡감을 낸다 — 범위는 0.4 ~ 1.0 이다.
- 슬라이더와 컨테이너 크기를 매 프레임 다시 읽으므로 값 바꾸기 · 창 크기 바꾸기가 바로 반영된다.
- `transform` 을 스크립트로 쓸 때는 `translate(-50%, -50%)` 를 함께 적어야 점의 중심이 (x, y) 에 맞는다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 DOM API 를 쓰는 예제다 — 브라우저에서 확인한다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

# javascript/math-motion/12 — Momentum / Inertia — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `velX` 는 9.5, `posX` 는 209.5

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`velX = 10 × 0.95 = 9.5` 다.
그다음 `posX = 200 + 9.5 = 209.5` 다.

**왜 그런가**
관성 구간에서는 속도에 마찰을 **먼저** 곱하고, 줄어든 속도만큼 위치를 옮긴다.
그래서 놓은 뒤 첫 이동도 10 이 아니라 9.5 다.
근거: 2-summary 「동작 방식 (2)」.

### 2. `posX` 는 50, `velX` 는 4.75

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
마찰: `velX = -10 × 0.95 = -9.5`.
이동: `posX = 55 + (-9.5) = 45.5`.
검사: `45.5 - 50 = -4.5 < 0` 이라 벽을 넘었다.
반사: `posX = 50`, `velX = -9.5 × -0.5 = 4.75`.

**왜 그런가**
카드 왼쪽 가장자리(중심 − 절반 폭)가 0 보다 작아졌으므로 가장자리를 벽에 붙이도록 중심을 `hw` 로 되돌린다.
음수 `bounce` 를 곱해 방향이 오른쪽(양수)으로 바뀌고 빠르기는 절반이 된다.
근거: 2-summary 「동작 방식 (3)」.

### 3. 이론상 190 px

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
매 프레임 이동량은 `10 × 0.95`, `10 × 0.95²`, … 이다.
합은 `v₀ × f / (1 − f) = 10 × 0.95 / 0.05 = 190` 이다.
참고로 60 프레임 뒤 속도는 `10 × 0.95⁶⁰ ≈ 0.46` 정도로, 이미 거의 멈춘 것처럼 보일 만큼 작다(직접 계산한 값).

**왜 그런가**
같은 비율로 줄어드는 지수 감쇠라 이동량의 합은 등비급수가 되고, 무한히 더해도 유한한 값에 수렴한다.
속도는 정확히 0 이 되지 않지만 총거리는 190 을 넘지 않는다.
근거: 2-summary 「동작 방식 (2)」.

### 4. 곱해도 속도가 그대로이기 때문이다

`friction` 이 1 이면 `velX *= 1` 이 속도를 바꾸지 않으므로 매 프레임 같은 거리만큼 계속 움직인다 — 멈추는 계기는 벽 반사의 `bounce` 뿐이다.
`friction` 이 0 이면 첫 프레임에 속도가 0 이 되어 그 뒤로 위치가 변하지 않는다 — 놓는 즉시 선다.
그래서 팁은 그 사이의 0.95~0.98 을 자연스럽다고 한다.
근거: 2-summary 「동작 방식 (2)」 · 「문법 — 형태와 규칙」의 값 표.

### 5. 잡아도 카드가 멈추지 않거나, 잡자마자 엉뚱하게 날아갈 수 있다

`mousemove` 가 아직 한 번도 오지 않은 동안 `velX`, `velY` 에는 미끄러지던 때의 속도가 남아 있다.
잡았다가 마우스를 움직이지 않고 바로 놓으면 그 옛 속도로 다시 미끄러진다 — 「잡으면 선다」는 느낌이 깨진다.
잡는 순간 0 으로 지우면, 잡은 뒤에 새로 잰 변위만 관성의 출발 속도가 된다.
근거: 2-summary 「동작 방식 (1)」. (뒤 시나리오는 원본에 근거 없음 — 추론)

### 6. 미끄러진다

마우스를 멈추면 `mousemove` 가 일어나지 않으므로 `velX`, `velY` 는 마지막으로 움직였을 때의 변위로 남는다.
놓는 순간 `dragging` 만 `false` 가 되고 속도는 그대로라, 카드는 그 옛 속도로 미끄러진다.
근거: 2-summary 「어디서 틀리나 3」.

### 7. 나갈 수 있고, 놓은 첫 프레임에 경계로 순간 이동한다

벽 검사는 `if (!dragging)` 안에만 있으므로 끄는 동안 위치는 마우스를 따라 어디로든 간다.
컨테이너가 `overflow: hidden` 이라 밖으로 나간 부분은 잘려 보인다.
놓은 첫 프레임에 벽 검사가 돌아 위치를 경계로 되돌리고, 그 축의 속도에 `bounce` 를 곱한다.
근거: 2-summary 「어디서 틀리나 4」 · 「동작 방식 (3)」.

### 8. 둘이 합쳐져 좌표가 중심이 되고, 그래서 가장자리는 「중심 ± 절반 크기」다

`left` · `top` 은 카드의 왼쪽 위 모서리를 정하는데, `translate(-50%, -50%)` 가 카드를 자기 크기의 절반만큼 왼쪽 위로 되돌려 `posX`, `posY` 가 중심이 된다.
그래서 벽 검사는 중심에서 절반 폭 `hw` · 절반 높이 `hh` 를 더하고 빼서 가장자리를 구한다.
회전을 넣을 때 `translate` 를 빠뜨리면 좌표가 모서리로 바뀌어 이 검사가 어긋난다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 7」.

## 실습 정답

### 실습 1. 던지면 미끄러지고 벽에서 튕기는 카드

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 위치를 가운데에서 시작 | `let posX = container.offsetWidth / 2;` · `let posY = container.offsetHeight / 2;` |
| 2. 속도 · 드래그 여부 · 직전 좌표 | `let velX = 0, velY = 0;` · `let dragging = false;` · `let prevMouseX = 0, prevMouseY = 0;` |
| 3. 마찰 · 반사 상수 | `const friction = 0.95;` · `const bounce = -0.5;` |
| 4. 잡기 | `card.addEventListener('mousedown', …)` — `dragging = true`, `velX = 0`, `prevMouseX = e.clientX`, `card.style.cursor = 'grabbing'` |
| 5. 끌기 | `window.addEventListener('mousemove', …)` — `if (!dragging) return;`, `velX = dx`, `posX += dx`, `prevMouseX = e.clientX` |
| 6. 놓기 | `window.addEventListener('mouseup', …)` — `dragging = false`, `cursor = 'grab'` |
| 7. 마찰 → 이동 | `animate()` 의 `if (!dragging)` 안 `velX *= friction;` · `posX += velX;` |
| 8. 넷 벽 반사 | `if (posX - hw < 0) { posX = hw; velX *= bounce; }` 외 세 줄 |
| 9. 위치 · 회전 적용 | `card.style.left` · `card.style.top` · `` `translate(-50%, -50%) rotate(${velX * 0.5}deg)` `` |
| 10. 표시줄 | `Math.hypot(velX, velY)` · `readout.textContent = …toFixed(1)…` |
| 11. 반복과 시작 | `requestAnimationFrame(animate);` · 마지막 줄 `animate();` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`javascript/math-motion/reference/momentum-inertia.js`

```javascript
// [수학 & 모션 공식] Momentum / Inertia
// 설명: 드래그 후 놓으면 관성으로 미끄러지며 마찰로 감속. 자연스러운 제스처 인터랙션
// 팁: friction 0.95~0.98이 자연스러움. 0에 가까우면 즉시 멈추고 1이면 영원히 미끄러짐. 벽 반사에는 속도를 음수로 뒤집고 bounce 계수(0~1)를 곱함.

// 카드를 드래그할 영역
const container = document.getElementById('inertiaContainer');
// 드래그 가능한 카드 요소
const card = document.getElementById('inertiaCard');
// 디버깅 텍스트
const readout = document.getElementById('inertiaReadout');

// 카드 위치 (컨테이너 가운데에서 시작)
let posX = container.offsetWidth / 2;
let posY = container.offsetHeight / 2;
// 속도 벡터 (px/frame)
let velX = 0, velY = 0;
// 드래그 중 여부
let dragging = false;
// 직전 마우스 좌표 (속도 계산용)
let prevMouseX = 0, prevMouseY = 0;
// 마찰 계수: 매 프레임 속도에 곱함 (0.95 = 5% 감속)
const friction = 0.95;
// 벽에 부딪힐 때 반사 계수: 음수로 방향 반전, 0.5는 절반 에너지 손실
const bounce = -0.5;

// 카드 마우스다운 → 드래그 시작
card.addEventListener('mousedown', (e) => {
  dragging = true;
  // 잡는 순간 속도 초기화
  velX = 0;
  velY = 0;
  // 직전 좌표 시작값
  prevMouseX = e.clientX;
  prevMouseY = e.clientY;
  card.style.cursor = 'grabbing';
});

// 마우스 이동 중 속도 계산 + 위치 갱신
window.addEventListener('mousemove', (e) => {
  if (!dragging) return;
  // 직전 마우스와의 변위 = 속도 (프레임당 이동 픽셀)
  const dx = e.clientX - prevMouseX;
  const dy = e.clientY - prevMouseY;
  velX = dx;
  velY = dy;
  // 변위만큼 카드 위치 이동
  posX += dx;
  posY += dy;
  // 직전 좌표 업데이트
  prevMouseX = e.clientX;
  prevMouseY = e.clientY;
});

// 마우스 업 → 관성 이동만 남김
window.addEventListener('mouseup', () => {
  dragging = false;
  card.style.cursor = 'grab';
});

// 매 프레임 물리 업데이트
function animate() {
  // 드래그 중이 아닐 때만 관성 적용
  if (!dragging) {
    // 매 프레임 속도에 마찰 곱해 점차 감속 (지수 감쇠)
    velX *= friction;
    velY *= friction;
    // 속도만큼 위치 이동
    posX += velX;
    posY += velY;

    // 벽 충돌 검사용 컨테이너 크기와 카드 절반 크기
    const cw = container.offsetWidth;
    const ch = container.offsetHeight;
    const hw = 50, hh = 70;
    // 왼쪽 벽: 위치를 경계로 고정 + 속도 반전(반사) + 감쇠
    if (posX - hw < 0) { posX = hw; velX *= bounce; }
    // 오른쪽 벽
    if (posX + hw > cw) { posX = cw - hw; velX *= bounce; }
    // 위쪽 벽
    if (posY - hh < 0) { posY = hh; velY *= bounce; }
    // 아래쪽 벽
    if (posY + hh > ch) { posY = ch - hh; velY *= bounce; }
  }

  // 위치 적용
  card.style.left = posX + 'px';
  card.style.top = posY + 'px';
  // 중앙 정렬 + 속도에 비례한 회전 (운동 방향감 표현)
  card.style.transform = `translate(-50%, -50%) rotate(${velX * 0.5}deg)`;

  // 속도 크기(스칼라) 계산
  const speed = Math.hypot(velX, velY);
  // 디버깅 표시
  readout.textContent = `velocity: (${velX.toFixed(1)}, ${velY.toFixed(1)}) | speed: ${speed.toFixed(1)}px/frame`;
  // 다음 프레임
  requestAnimationFrame(animate);
}
// 애니메이션 시작
animate();
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```html
<div class="inertia-container" id="inertiaContainer">
  <div class="inertia-card" id="inertiaCard">
    <div class="card-content">드래그 후 놓기</div>
  </div>
</div>
<p class="info">카드를 드래그하고 놓으면 관성으로 미끄러집니다</p>
<div class="readout" id="inertiaReadout">velocity: 0</div>
```

```css
.inertia-container { position: relative; width: 100%; height: 300px; background: #0f172a; border-radius: 8px; overflow: hidden; }
.inertia-card { position: absolute; width: 100px; height: 140px; background: linear-gradient(135deg, #3b82f6, #8b5cf6); border-radius: 12px; left: 50%; top: 50%; transform: translate(-50%, -50%); cursor: grab; user-select: none; display: flex; align-items: center; justify-content: center; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
.inertia-card:active { cursor: grabbing; }
.card-content { color: white; font-size: 12px; text-align: center; pointer-events: none; }
```

**실행 결과** — 실행하지 않음 — 브라우저 DOM API 를 쓰는 예제다 — 브라우저에서 확인한다.

**풀이 요점**
- 드래그 중에는 「변위 = 속도」를 계속 덮어써, 놓는 순간의 마지막 변위가 관성의 출발 속도가 된다.
- 관성 구간의 순서는 마찰 → 이동 → 벽 검사다.
- 벽 반사는 위치를 경계로 되돌리는 것과 속도에 음수 `bounce` 를 곱하는 것이 한 쌍이다.
- 화면 반영과 `requestAnimationFrame` 예약은 `if (!dragging)` 바깥에 두어, 드래그 중에도 카드가 매 프레임 마우스를 따라 그려지게 한다.
- `transform` 을 새로 쓸 때마다 `translate(-50%, -50%)` 를 함께 적어야 `posX`, `posY` 가 중심으로 남는다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 DOM API 를 쓰는 예제다 — 브라우저에서 확인한다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

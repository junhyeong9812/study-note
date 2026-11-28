# javascript/math-motion/12 — Momentum / Inertia — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 놓는 순간 `velX` 가 10 이면 다음 한 프레임 (예측)

```javascript
// 질문용 발췌 — 놓은 직후, dragging 은 false, 카드는 벽에서 멀다
let posX = 200, velX = 10;
const friction = 0.95;
velX *= friction;
posX += velX;
```

- 이 두 줄이 한 번 돈 뒤 `velX` 와 `posX` 는 각각 얼마인가?

### 2. 왼쪽 벽 가까이에서 한 프레임 (예측)

```javascript
// 질문용 발췌 — 카드 절반 폭 hw = 50, dragging 은 false
let posX = 55, velX = -10;
const friction = 0.95, bounce = -0.5, hw = 50;
velX *= friction;
posX += velX;
if (posX - hw < 0) { posX = hw; velX *= bounce; }
```

- 이 프레임이 끝났을 때 `posX` 와 `velX` 는 각각 얼마인가?

### 3. `velX` 10 으로 놓은 뒤 멈출 때까지의 거리 (예측)

- `friction = 0.95`, 벽이 없다고 할 때 카드가 가로로 미끄러지는 총거리는 이론상 몇 px 인가?

### 4. `friction` 이 1 이면 왜 영원히 미끄러지나 (왜)

- 매 프레임 하는 계산을 근거로, `friction` 이 1 일 때와 0 일 때 카드가 각각 어떻게 되는지 왜 그런가?

### 5. 카드를 잡는 순간 속도를 0 으로 지우는 까닭 (왜)

- `mousedown` 에서 `velX`, `velY` 를 0 으로 두지 않으면 어떤 일이 생길 수 있는가?

### 6. 빠르게 끌다가 멈춘 채 놓기 (경계)

- 빠르게 끌다가 마우스를 멈추고 잠시 뒤 놓으면, 카드는 제자리에 서는가, 미끄러지는가?

### 7. 드래그 중에 카드를 컨테이너 밖까지 끌면 (경계)

- 드래그 중 카드가 컨테이너 밖으로 나갈 수 있는가, 그리고 놓은 첫 프레임에 무슨 일이 생기는가?

### 8. `posX` 가 카드 중심이 되는 까닭 (연결)

- `left` · `top` 과 `translate(-50%, -50%)` 는 벽 검사의 `hw` · `hh` 와 어떻게 이어지는가?

## 실습

### 실습 1. 던지면 미끄러지고 벽에서 튕기는 카드

**만들 것** — 컨테이너 안의 카드를 마우스로 끌다 놓으면 관성으로 미끄러지며 마찰로 서고, 벽에 닿으면 튕겨 나오게 한다.
아래 표시줄에 속도와 빠르기를 매 프레임 보여 준다.

**요구 조건**

1단계 — 상태
1. 카드 위치 `posX`, `posY` 는 컨테이너 가운데(폭 · 높이의 절반)에서 시작한다.
2. 속도 `velX`, `velY` 는 0, 드래그 여부 `dragging` 은 `false`, 직전 마우스 좌표 `prevMouseX`, `prevMouseY` 는 0 으로 시작한다.
3. 마찰 계수 `friction` 은 0.95, 반사 계수 `bounce` 는 -0.5 인 상수로 둔다.

2단계 — 드래그
4. 카드에서 `mousedown` 이 일어나면 드래그를 시작하고, 속도를 0 으로 지우고, 지금 마우스 좌표(`clientX`, `clientY`)를 직전 좌표로 적고, 커서를 `grabbing` 으로 바꾼다.
5. `window` 의 `mousemove` 에서는 드래그 중일 때만, 직전 좌표와의 변위를 속도로 적고, 그 변위만큼 위치를 옮기고, 직전 좌표를 갱신한다.
6. `window` 의 `mouseup` 에서는 드래그를 끝내고 커서를 `grab` 으로 되돌린다.

3단계 — 매 프레임 물리
7. `animate()` 는 드래그 중이 아닐 때만 속도에 마찰을 곱한 뒤 그 속도만큼 위치를 옮긴다.
8. 이어서 컨테이너 크기와 카드 절반 크기(`hw`, `hh`)로 넷 벽을 각각 검사해, 넘었으면 위치를 경계로 되돌리고 그 축의 속도에 `bounce` 를 곱한다.

4단계 — 화면 반영
9. 매 프레임 카드의 `left` · `top` 에 위치를 넣고, `transform` 은 중앙 정렬 `translate(-50%, -50%)` 에 `velX` 의 절반만큼(도 단위)의 회전을 더한다.
10. 표시줄에 `velocity: (velX, velY) | speed: 빠르기px/frame` 꼴로 소수 한 자리까지 적는다 — 빠르기는 `Math.hypot` 으로 구한다.
11. `requestAnimationFrame` 으로 다음 프레임을 예약하고, 처음에 `animate()` 를 한 번 불러 시작한다.

**시작 코드**

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

```javascript
const container = document.getElementById('inertiaContainer');
const card = document.getElementById('inertiaCard');
const readout = document.getElementById('inertiaReadout');

// TODO: 위치 · 속도 · 드래그 여부 · 직전 마우스 좌표
// TODO: friction, bounce 상수

card.addEventListener('mousedown', (e) => {
  // TODO: 드래그 시작, 속도 초기화, 직전 좌표 기록, 커서 변경
});

window.addEventListener('mousemove', (e) => {
  // TODO: 드래그 중일 때만 변위 = 속도, 위치 이동, 직전 좌표 갱신
});

window.addEventListener('mouseup', () => {
  // TODO: 드래그 끝, 커서 되돌리기
});

function animate() {
  if (!dragging) {
    // TODO: 마찰 → 이동
    const cw = container.offsetWidth;
    const ch = container.offsetHeight;
    const hw = 50, hh = 70; // 카드 절반 크기 (미리 채움)
    // TODO: 넷 벽 검사 — 경계로 되돌리고 속도 × bounce
  }

  // TODO: left · top · transform(translate + rotate) 적용
  // TODO: Math.hypot 으로 빠르기 → 표시줄 갱신
  // TODO: 다음 프레임 예약
}
// TODO: 시작
```

**확인 방법** — 세 조각을 한 HTML 파일에 넣어 브라우저로 연다.
카드를 끌다 놓았을 때 미끄러지며 느려지는지, 벽에서 반대로 튕기는지, 표시줄의 `speed` 가 0 쪽으로 줄어드는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

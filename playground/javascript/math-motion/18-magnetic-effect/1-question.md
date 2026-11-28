# javascript/math-motion/18 — Magnetic Effect — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 거리 0 · 60 · 120 에서의 끌림 크기 (예측)

```javascript
// 질문용 발췌 — threshold = 120, strength = 0.35
const factor = 1 - (dist / threshold);
states[i].targetX = dx * strength * factor;
```

- 마우스가 버튼 중심에서 오른쪽으로만 0, 60, 120 떨어져 있을 때 각각 `targetX` 는 얼마인가?
- 셋 가운데 버튼이 가장 크게 끌리는 곳은 어디인가?

### 2. 오른쪽 60 에서의 readout 문자열 (예측)

```javascript
// 질문용 발췌 — 마우스가 첫 버튼 중심에서 정확히 오른쪽 60, 위아래 0
readout.textContent = `distance: ${Math.round(dist)}px | factor: ${factor.toFixed(2)} | offset: (${states[i].targetX.toFixed(1)}, ${states[i].targetY.toFixed(1)})`;
```

- `readout` 에는 어떤 문자열이 적히는가?

### 3. 목표 10 을 향한 첫 두 프레임 (예측)

```javascript
// 질문용 발췌 — x 는 0 에서 시작, targetX 는 10 으로 고정
states[i].x = lerp(states[i].x, states[i].targetX, 0.15);
```

- 첫 프레임과 둘째 프레임 뒤 `x` 는 각각 얼마인가?

### 4. CSS `:hover` 로는 이 효과를 만들 수 없는 까닭 (왜)

- `:hover` 가 아는 정보와 이 효과가 필요로 하는 정보는 무엇이 다른가?

### 5. 목표 위치와 현재 위치를 나눠 두는 까닭 (왜)

- `mousemove` 핸들러에서 `transform` 을 바로 쓰지 않고 `targetX` 와 `x` 를 따로 두는 까닭은 무엇인가?

### 6. 임계 거리 밖으로 나간 뒤의 버튼 (경계)

- 마우스가 임계 거리 안에 있다가 밖으로 나가면 버튼 위치와 인라인 글로우는 각각 어떻게 되는가?
- 거리가 정확히 `threshold` 와 같을 때는 어느 쪽 분기로 가는가?

### 7. 보라색 두 번째 버튼에 다가갈 때의 글로우 (연결)

- CSS 에 보라색 `:hover` 그림자 규칙이 있는데도 임계 거리 안에서 두 번째 버튼의 그림자 색이 무엇이 되는지, 캐스케이드 규칙으로 설명하면?

### 8. `factor` 를 빼고 원본 공식만 쓰면 생기는 일 (경계)

- `offset = (mouse - center) * strength` 만 쓰면 거리가 `threshold` 를 막 넘는 순간 무엇이 문제가 되는가?

### 9. 이벤트와 프레임 루프의 역할 나눔 (연결)

- 이 효과에서 `mousemove` 와 `requestAnimationFrame` 은 각각 무엇을 맡고, 마우스가 멈춰도 버튼이 계속 움직일 수 있는 것은 어느 쪽 덕분인가?

## 실습

### 실습 1. 마우스 쪽으로 끌리는 자석 버튼 두 개

**만들 것** — 버튼 두 개가 마우스가 가까이 오면 그쪽으로 끌려가고, 멀어지면 부드럽게 제자리로 돌아오게 한다. 첫 버튼의 거리 · factor · 오프셋을 글자로 보여 준다.

**요구 조건**

1단계 — 준비
1. 컨테이너, 그 안의 `.magnetic-btn` 버튼들, `readout` 요소를 찾아 둔다.
2. `lerp(a, b, t)` 함수를 만든다.
3. 버튼 수만큼 `{ x, y, targetX, targetY }` 상태 객체를 모두 0 으로 만들어 배열에 둔다.

2단계 — 마우스 이동으로 목표 계산
4. `window` 의 `mousemove` 에서 버튼마다 `getBoundingClientRect` 로 중심을 구한다.
5. 중심에서 마우스까지의 `dx` · `dy` 와 `Math.hypot` 직선 거리를 구한다.
6. 거리가 `threshold` 보다 작으면 `factor = 1 - dist / threshold` 를 구하고, 목표를 `변위 × strength × factor` 로 정한다.
7. 그 경우 버튼의 글로우를 `factor` 에 따라 정한다(시작 코드에 있는 줄).
8. 그 경우 첫 번째 버튼이면 `readout` 에 거리 · factor · 목표 오프셋을 적는다(시작 코드에 있는 줄).
9. 거리가 `threshold` 이상이면 목표를 0 으로 되돌린다.

3단계 — 프레임 루프
10. `animate` 에서 버튼마다 현재 위치를 목표 쪽으로 `lerp`(비율 0.15) 한다.
11. 현재 위치를 `transform: translate(...)` 로 적용한다.
12. `requestAnimationFrame` 으로 다음 프레임을 예약하고, 처음 한 번 `animate()` 를 불러 시작한다.

**시작 코드**

```html
<div class="magnetic-container" id="magneticContainer">
  <button class="magnetic-btn" id="magneticBtn"><span>Hover Me</span></button>
  <button class="magnetic-btn secondary" id="magneticBtn2"><span>Me Too</span></button>
</div>
<p class="info">버튼 근처로 마우스를 가져가면 자석처럼 끌려옵니다</p>
<div class="readout" id="magneticReadout">distance: - | offset: (0, 0)</div>

<style>
  .magnetic-container { display: flex; align-items: center; justify-content: center; gap: 80px; height: 250px; background: #0f172a; border-radius: 8px; }
  .magnetic-btn { padding: 16px 36px; background: #3b82f6; color: white; border: none; border-radius: 12px; font-size: 16px; font-weight: 600; cursor: pointer; transition: box-shadow 0.3s; position: relative; }
  .magnetic-btn.secondary { background: #8b5cf6; }
  .magnetic-btn:hover { box-shadow: 0 0 30px rgba(59,130,246,0.4); }
  .magnetic-btn.secondary:hover { box-shadow: 0 0 30px rgba(139,92,246,0.4); }
</style>
<script src="magnetic-effect.js"></script>
```

```javascript
// magnetic-effect.js
const container = document.getElementById('magneticContainer');
const btns = container.querySelectorAll('.magnetic-btn');
const readout = document.getElementById('magneticReadout');

// TODO: lerp(a, b, t)

// TODO: 버튼마다 { x, y, targetX, targetY } 상태 배열

const threshold = 120;
const strength = 0.35;

window.addEventListener('mousemove', (e) => {
  btns.forEach((btn, i) => {
    // TODO: 버튼 중심 (cx, cy)
    // TODO: dx, dy, dist

    if (/* TODO: 임계 거리 안인가 */ false) {
      // TODO: factor, states[i].targetX, states[i].targetY
      btn.style.boxShadow = `0 0 ${30 + factor * 20}px rgba(59,130,246,${0.2 + factor * 0.3})`;
      if (i === 0) readout.textContent = `distance: ${Math.round(dist)}px | factor: ${factor.toFixed(2)} | offset: (${states[i].targetX.toFixed(1)}, ${states[i].targetY.toFixed(1)})`;
    } else {
      // TODO: 목표를 원위치로
    }
  });
});

function animate() {
  btns.forEach((btn, i) => {
    // TODO: 현재 위치를 목표 쪽으로 lerp
    // TODO: transform 적용
  });
  // TODO: 다음 프레임 예약
}
// TODO: 루프 시작
```

**확인 방법** — HTML 파일을 브라우저로 열고 버튼 근처로 마우스를 천천히 가져간다. 버튼이 마우스 쪽으로 기울고, 멀어지면 천천히 돌아오며, 첫 버튼 근처에서 `readout` 의 숫자가 바뀌는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

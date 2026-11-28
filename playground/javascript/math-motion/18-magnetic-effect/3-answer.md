# javascript/math-motion/18 — Magnetic Effect — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 0 · 10.5 · 0 — 중간 거리 60 에서 가장 크게 끌린다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- 거리 0: `dx = 0` 이라 `0 × 0.35 × 1 = 0`.
- 거리 60: `factor = 1 - 60/120 = 0.5`, `60 × 0.35 × 0.5 = 10.5`.
- 거리 120: `dist < threshold` 가 거짓이라 `else` 로 가서 `targetX = 0`.
- 가장 크게 끌리는 곳은 거리 60 이다.

**왜 그런가**
크기는 `d × 0.35 × (1 − d/120)` 이다.
`d` 가 작으면 앞쪽 `d` 가 작고, `d` 가 크면 뒤쪽 `factor` 가 작아서 양 끝이 0 이 된다.
그래서 가운데에서 가장 커진다.
근거: 2-summary 「동작 방식 (3)」.

### 2. `distance: 60px | factor: 0.50 | offset: (10.5, 0.0)`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
distance: 60px | factor: 0.50 | offset: (10.5, 0.0)
```

**왜 그런가**
`dist = Math.hypot(60, 0) = 60` 이고 `Math.round` 해도 60 이다.
`factor = 0.5` 를 `toFixed(2)` 하면 `0.50` 이다.
`targetX = 60 × 0.35 × 0.5 = 10.5` 를 `toFixed(1)` 하면 `10.5` 이다.
`targetY = 0 × … = 0` 을 `toFixed(1)` 하면 `0.0` 이다.
근거: 2-summary 「동작 방식 (3)」 · 「동작 방식 (4)」.

### 3. 1.5, 그다음 2.775 — 남은 거리의 15% 씩 다가간다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- 1프레임: `0 + (10 − 0) × 0.15 = 1.5`.
- 2프레임: `1.5 + (10 − 1.5) × 0.15 = 1.5 + 1.275 = 2.775`.

**왜 그런가**
`lerp` 는 매번 「지금 위치에서 남은 거리의 `t` 만큼」 간다.
남은 거리는 프레임마다 0.85 배가 되므로 처음엔 빠르고 갈수록 느려진다.
근거: 2-summary 「동작 방식 (5)」.

### 4. `:hover` 는 위에 있나 없나만 안다

`:hover` 는 포인터가 요소 위에 있는지 없는지 두 상태만 안다.
이 효과는 버튼 밖에서의 거리와 마우스의 방향(`dx` · `dy`)이 필요하다.
좌표와 거리는 JS 의 `mousemove` 이벤트(`e.clientX` · `e.clientY`)로만 얻는다.
근거: 2-summary 「어디서 틀리나 1」.

### 5. 부드럽게 따라가고, 마우스가 멈춰도 돌아오게 하려고

핸들러에서 바로 `transform` 을 쓰면 위치가 이벤트마다 뚝뚝 바뀐다.
또 마우스가 멈추면 이벤트도 멈춰서 천천히 돌아오는 움직임을 만들 수 없다.
목표만 핸들러에서 정하고, 루프가 `lerp` 로 현재를 목표 쪽으로 조금씩 옮기면 둘 다 해결된다.
근거: 2-summary 「동작 방식」 첫 그림 · 「어디서 틀리나 3」.

### 6. 위치는 돌아오고 글로우는 남는다 · 경계 값은 `else`

- `else` 가 목표를 0 으로 만들므로 루프가 버튼을 천천히 제자리로 되돌린다.
- `boxShadow` 는 `else` 에서 건드리지 않으므로 마지막 인라인 그림자가 그대로 남는다(코드에서 읽은 것 — 렌더 실측 아님).
- 조건이 `dist < threshold` 이므로 거리가 정확히 `threshold` 이면 `else` 로 간다 — 그 자리의 `factor` 는 0 이라 결과는 같다.

근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 4」 · 「어디서 틀리나 6」.

### 7. 파란색 — 인라인 스타일이 스타일시트 규칙을 이긴다

임계 거리 안에서는 JS 가 `btn.style.boxShadow` 에 `rgba(59,130,246, …)` 파란 그림자를 넣는다.
이것은 인라인 스타일이라 `!important` 없는 `.secondary:hover` 규칙보다 우선한다.
그래서 보라색 버튼도 파란 글로우가 된다(코드에서 읽은 것 — 렌더 실측 아님).
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 5」 · 「구현 세부사항 대 언어 보장」.

### 8. 경계를 넘는 순간 목표가 크게 뛴다

`factor` 가 없으면 거리 119 에서 오프셋이 약 `119 × 0.35 ≈ 41.65` 이다.
120 을 넘으면 곧바로 0 이 된다.
목표가 한 번에 크게 바뀌어 효과가 툭 켜지고 꺼지는 느낌이 된다.
`factor` 를 곱하면 경계에서 오프셋이 0 으로 모여 이음매가 없어진다.
근거: 2-summary 「어디서 틀리나 2」 · 「동작 방식 (2)」.

### 9. 이벤트는 목표, 루프는 현재 — 계속 움직이는 건 루프 덕분

`mousemove` 는 마우스가 움직일 때만 불리며 목표(`targetX` · `targetY`)와 글로우 · `readout` 을 정한다.
`requestAnimationFrame` 루프는 매 프레임 불리며 `lerp` 로 현재 위치를 옮기고 `transform` 을 적용한다.
마우스가 멈춰도 루프는 계속 돌기 때문에 버튼이 목표까지 마저 움직인다.
근거: 2-summary 「동작 방식」 첫 그림 · 「동작 방식 (5)」.

## 실습 정답

### 실습 1. 마우스 쪽으로 끌리는 자석 버튼 두 개

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 요소 찾기 | `container` · `btns` (`querySelectorAll('.magnetic-btn')`) · `readout` |
| 2. `lerp` | `function lerp(a, b, t) { return a + (b - a) * t; }` |
| 3. 버튼별 상태 | `const states = Array.from(btns).map(() => ({ x: 0, y: 0, targetX: 0, targetY: 0 }))` |
| 4. 버튼 중심 | `btn.getBoundingClientRect()` → `cx` · `cy` |
| 5. 변위와 거리 | `dx` · `dy` · `Math.hypot(dx, dy)` |
| 6. factor 와 목표 | `if (dist < threshold)` · `factor = 1 - (dist / threshold)` · `states[i].targetX = dx * strength * factor` |
| 7. 글로우 | `btn.style.boxShadow = …` |
| 8. 첫 버튼 readout | `if (i === 0) readout.textContent = …` |
| 9. 밖이면 원위치 목표 | `else { states[i].targetX = 0; states[i].targetY = 0; }` |
| 10. 현재 → 목표 lerp | `states[i].x = lerp(states[i].x, states[i].targetX, 0.15)` |
| 11. transform 적용 | `` btn.style.transform = `translate(...)` `` |
| 12. 루프 예약과 시작 | `requestAnimationFrame(animate)` · `animate()` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`javascript/math-motion/reference/magnetic-effect.js`

```javascript
// [수학 & 모션 공식] Magnetic Effect
// 설명: 마우스가 가까이 오면 요소가 끌려가는 자석 효과. 버튼, CTA에 활용
// 팁: threshold 내에서 거리에 비례하는 factor를 계산하고, 마우스 오프셋에 곱함. lerp으로 부드럽게 전환. CSS의 :hover만으로는 불가능하고 JS mousemove가 필요.

// 자석 버튼들이 있는 컨테이너
const container = document.getElementById('magneticContainer');
// 모든 자석 버튼 요소
const btns = container.querySelectorAll('.magnetic-btn');
// 첫 번째 버튼의 디버깅 정보를 표시
const readout = document.getElementById('magneticReadout');

// 선형 보간 (위치 부드럽게 변경할 때 사용)
function lerp(a, b, t) { return a + (b - a) * t; }

// 각 버튼별 현재 위치(x,y)와 목표 위치(targetX,targetY) 보관
const states = Array.from(btns).map(() => ({ x: 0, y: 0, targetX: 0, targetY: 0 }));

// 자석 효과 발동 거리 (px): 이 거리 내에서만 끌어당김
const threshold = 120;
// 끌어당기는 강도 (0.35 = 거리의 35%만 따라감)
const strength = 0.35;

// 전역 마우스 이동: 모든 버튼이 거리 계산
window.addEventListener('mousemove', (e) => {
  btns.forEach((btn, i) => {
    // 버튼의 화면상 위치/크기
    const rect = btn.getBoundingClientRect();
    // 버튼 중심 X
    const cx = rect.left + rect.width / 2;
    // 버튼 중심 Y
    const cy = rect.top + rect.height / 2;
    // 마우스와 버튼 중심의 변위
    const dx = e.clientX - cx;
    const dy = e.clientY - cy;
    // 직선 거리
    const dist = Math.hypot(dx, dy);

    // 임계 거리 내일 때만 자석 효과
    if (dist < threshold) {
      // 거리가 가까울수록 1, 임계점에선 0이 되는 비율
      const factor = 1 - (dist / threshold);
      // 목표 오프셋 = 변위 * 강도 * 거리 비율 (가까울수록 강하게 끌림)
      states[i].targetX = dx * strength * factor;
      states[i].targetY = dy * strength * factor;
      // 가까울수록 글로우 효과 강해짐
      btn.style.boxShadow = `0 0 ${30 + factor * 20}px rgba(59,130,246,${0.2 + factor * 0.3})`;
      // 첫 번째 버튼만 디버깅 정보 표시
      if (i === 0) readout.textContent = `distance: ${Math.round(dist)}px | factor: ${factor.toFixed(2)} | offset: (${states[i].targetX.toFixed(1)}, ${states[i].targetY.toFixed(1)})`;
    } else {
      // 임계 거리 밖이면 원위치로 복귀 목표
      states[i].targetX = 0;
      states[i].targetY = 0;
    }
  });
});

// 매 프레임 lerp으로 현재 위치를 목표 위치로 부드럽게 이동
function animate() {
  btns.forEach((btn, i) => {
    // 현재 위치를 목표 위치 쪽으로 15%씩 이동 (부드러운 추적)
    states[i].x = lerp(states[i].x, states[i].targetX, 0.15);
    states[i].y = lerp(states[i].y, states[i].targetY, 0.15);
    // CSS translate로 위치 적용
    btn.style.transform = `translate(${states[i].x}px, ${states[i].y}px)`;
  });
  // 다음 프레임
  requestAnimationFrame(animate);
}
// 애니메이션 루프 시작
animate();
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```html
<div class="magnetic-container" id="magneticContainer">
  <button class="magnetic-btn" id="magneticBtn">
    <span>Hover Me</span>
  </button>
  <button class="magnetic-btn secondary" id="magneticBtn2">
    <span>Me Too</span>
  </button>
</div>
<p class="info">버튼 근처로 마우스를 가져가면 자석처럼 끌려옵니다</p>
<div class="readout" id="magneticReadout">distance: - | offset: (0, 0)</div>
```

```css
.magnetic-container { display: flex; align-items: center; justify-content: center; gap: 80px; height: 250px; background: #0f172a; border-radius: 8px; }
.magnetic-btn { padding: 16px 36px; background: #3b82f6; color: white; border: none; border-radius: 12px; font-size: 16px; font-weight: 600; cursor: pointer; transition: box-shadow 0.3s; position: relative; }
.magnetic-btn.secondary { background: #8b5cf6; }
.magnetic-btn:hover { box-shadow: 0 0 30px rgba(59,130,246,0.4); }
.magnetic-btn.secondary:hover { box-shadow: 0 0 30px rgba(139,92,246,0.4); }
```

**실행 결과** — 실행하지 않음 — 브라우저 DOM API 를 쓰는 예제다 — 브라우저에서 확인한다.

**풀이 요점**
- 이벤트는 `window` 에 단다 — 버튼 밖의 근처에서도 거리를 재야 한다.
- `factor` 는 임계 거리 안에서만 계산한다 — 밖에서는 음수가 된다.
- 목표 오프셋은 `변위 × strength × factor` 라서 방향은 항상 마우스 쪽이고 크기는 중간 거리에서 가장 크다.
- 핸들러는 목표만 바꾸고, `transform` 은 `animate` 안에서만 쓴다.
- `lerp(…, 0.15)` 가 남은 거리의 15% 씩 다가가게 해 들어올 때도 돌아갈 때도 부드럽다.
- 인라인 `boxShadow` 는 `else` 에서 되돌리지 않으므로 밖으로 나가도 남는다 — 원본 코드의 동작 그대로다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 DOM API 를 쓰는 예제다 — 브라우저에서 확인한다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

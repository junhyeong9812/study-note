# animation/advanced-effects/01 — Interactive Particle Field — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 0개 — 캔버스 안의 어떤 점도 반경 100 안에 들지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

마우스가 캔버스를 떠나면 밀려나는 파티클은 없다(0개).
캔버스 안에서 `(-999, -999)` 에 가장 가까운 점은 `(0, 0)` 이고, 그 거리도 √(999² + 999²) ≈ 1413 이다.

**왜 그런가**

파티클 위치는 0~400, 0~300 안에 갇혀 있다.
그래서 모든 점과 `(-999, -999)` 의 거리가 `MOUSE_RADIUS` 100 보다 훨씬 크다.
조건 `dist < MOUSE_RADIUS` 가 모두 거짓이 되어 밀어내기가 일어나지 않는다.
근거: 2-summary 「동작 방식 (3)」.

### 2. 거리 40 이면 0.25 — 0 에 가까우면 0.5, 80 이면 선이 없다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- 거리 40: `(1 − 40/80) × 0.5 = 0.5 × 0.5 = 0.25`.
- 거리가 0 에 아주 가까울 때: `(1 − 0) × 0.5` 에 다가가 0.5 에 가깝다(가장 진함).
- 거리 80: 조건이 `dist < 80` 이라 거짓이므로 선을 긋지 않는다(식에 넣어도 0).

**왜 그런가**

`1 − dist / 80` 은 거리 0 에서 1, 거리 80 에서 0 이 되는 비율이다.
여기에 0.5 를 곱했으므로 알파는 0.5 를 넘지 않는다.
근거: 2-summary 「동작 방식 (4)」.

### 3. 점점 느려져 거의 멈춘다 — 60 프레임 뒤 약 0.30 배

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

매 프레임 속도에 0.98 이 곱해지므로 속도는 계속 줄어든다.
60 프레임 뒤에는 0.98⁶⁰ ≈ 0.30 배다.
마우스를 대지 않으면 점들은 결국 거의 멈춘다.
몇 초 걸리는지는 프레임 빈도에 따라 달라진다.

**왜 그런가**

속도를 늘리는 코드는 마우스 밀어내기뿐이다.
벽 반사(`vx *= -1`)는 부호만 바꾸고 크기는 그대로 둔다.
그래서 마우스가 없으면 줄어들기만 한다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 8」.

### 4. CSS 로 늘어난 크기를 그리기 해상도로 되돌리려고

캔버스의 그리기 좌표는 속성 `width="400"` 기준이지만, 화면에 보이는 폭은 CSS `width: 100%` 가 정한다.
둘이 다르면 화면 1px 이 그리기 좌표 1 과 같지 않다.
`W / rect.width` 를 곱해야 마우스 위치가 파티클과 같은 좌표계에 놓이고, 실제로 마우스가 있는 자리의 점이 밀린다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 4」.

### 5. 0 으로 나누어 `NaN` 이 생기는 것을 막으려고

밀어내기는 `dx / dist` 로 방향을 구한다.
마우스와 점이 정확히 겹치면 `dist` 가 0 이라 `0 / 0 = NaN` 이 된다.
`NaN` 이 속도에 들어가면 그 점의 위치 계산이 모두 `NaN` 이 되어 점이 망가진다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 6」.

### 6. 캔버스는 그린 것을 기억하지 않고, 나중에 그린 것이 위에 덮인다

- `clearRect`: 캔버스는 앞 프레임 그림을 그대로 남긴다. 지우지 않으면 앞 장의 점과 선이 겹겹이 쌓인다.
- 점을 나중에: 나중에 그린 것이 위에 덮이므로, 점을 선 뒤에 그려야 점이 선 끝을 덮어 선 위에 보인다.

근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (4)」 · 「어디서 틀리나 5」.

### 7. 3160 번 → 19900 번, 약 6.3 배

- 80개: 80 × 79 ÷ 2 = 3160 번.
- 200개: 200 × 199 ÷ 2 = 19900 번.
- 19900 ÷ 3160 ≈ 6.3 배다.

모든 쌍을 한 번씩 재는 O(n²) 계산이라, 점 수의 배율(2.5)보다 비교 수의 배율이 훨씬 크다.
원본 팁이 「200개 이하 권장 · 연결선 계산은 O(n²)」를 경고하는 까닭이다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 1 · 2」.

### 8. 그런 줄은 없다 — 이 코드는 밀어내기만 한다

속도에 더하는 방향은 `dx = p.x - mouse.x`, 곧 마우스에서 점으로 향하는(멀어지는) 쪽뿐이다.
원본 설명의 「끌려온다」에 해당하는 코드는 없다.
끌려오게 하려면 더하는 부호를 바꾸는 등 다른 코드가 필요하다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 3」.

### 9. 벽 밖에서 방향만 번갈아 바뀌며 갇힐 수 있다

벽을 넘은 점은 속도가 뒤집히지만, 다음 프레임에도 아직 벽 밖이면 다시 뒤집힌다.
그러면 안으로 돌아오지 못하고 벽 밖에서 왔다 갔다 할 수 있다.
위치를 가두는 줄이 점을 곧바로 캔버스 안으로 돌려놓아 이 일을 막는다.
근거: 2-summary 「어디서 틀리나 7」 · 「동작 방식 (2)」.

### 10. 점은 DOM 요소가 아니다 — IIFE 는 스코프 가두기 · 클로저와 이어진다

- CSS `@keyframes`: 캔버스에 그린 점은 HTML 요소가 아니라 픽셀일 뿐이라 선택자로 고를 수 없다. 그래서 스크립트가 매 프레임 직접 지우고 다시 그린다.
- `(function() { ... })();`: 즉시 실행 함수로, 안의 `const` 들을 함수 스코프에 가둬 전역 이름과 부딪히지 않게 한다. `animate` 가 그 안의 `particles` · `mouse` 를 계속 쓰는 것은 클로저다.

근거: 2-summary 「동작 방식 (1)」 · 「문법 — 형태와 규칙」.

## 실습 정답

### 실습 1. 마우스를 피하는 파티클 필드 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1단계 — 컨텍스트 · 해상도 · 먼 곳의 마우스 | `canvas.getContext('2d')` · `const W = canvas.width, H = canvas.height` · `const mouse = { x: -999, y: -999 }` |
| 2단계 — 마우스 좌표 환산 | `mousemove` 리스너 안 `getBoundingClientRect()` · `(e.clientX - rect.left) * (W / rect.width)` |
| 2단계 — 마우스 이탈 | `mouseleave` 리스너 안 `mouse.x = -999; mouse.y = -999;` |
| 3단계 — 파티클 생성 | `Array.from({ length: PARTICLE_COUNT }, ...)` · `(Math.random() - 0.5) * 0.8` |
| 4단계 — 밀어내기 | `if (dist < MOUSE_RADIUS && dist > 0)` · `p.vx += (dx / dist) * 0.3` |
| 4단계 — 마찰 · 이동 · 반사 · 가두기 | `p.vx *= 0.98` · `p.x += p.vx` · `p.vx *= -1` · `Math.max(0, Math.min(W, p.x))` |
| 5단계 — 연결선 | `for (let j = i + 1; ...)` · `if (dist < CONNECT_DIST)` · `moveTo` · `lineTo` · `strokeStyle` · `stroke()` |
| 6단계 — 점 | 세 번째 `for (const p of particles)` 안 `ctx.arc(p.x, p.y, 2, 0, Math.PI * 2)` · `fill()` |
| 7단계 — 루프 | `ctx.clearRect(0, 0, W, H)` · `requestAnimationFrame(animate)` · 마지막 `animate();` |
| 7단계 — 감싸기 | `(function() { ... })();` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`animation/advanced-effects/reference/particle-field.html`

```html
<!-- HTML5 문서 선언 -->
<!DOCTYPE html>
<!-- 한국어 페이지 -->
<html lang="ko">
<head>
  <!-- 문자 인코딩 -->
  <meta charset="utf-8">
  <!-- 브라우저 탭 제목 -->
  <title>Interactive Particle Field - 마우스에 반응하는 파티클 시스템. 점들이 가까이 있으면 선으로 연결되고, 마우스를 피하거나 끌려온다.</title>
  <!--
    [고급 이펙트] Interactive Particle Field
    설명: 마우스에 반응하는 파티클 시스템. 점들이 가까이 있으면 선으로 연결되고, 마우스를 피하거나 끌려온다.

    팁: requestAnimationFrame으로 루프. 파티클 수가 많으면 성능 저하 - 200개 이하 권장. 연결선 계산은 O(n^2)이므로 주의.
  -->
  <style>
    /* #particles: 파티클이 그려지는 캔버스 - 어두운 배경 + crosshair 커서로 인터랙티브 표시 */
    #particles {
      background: #0f172a;           /* 어두운 남색 (점이 잘 보이도록) */
      border-radius: 8px;            /* 모서리 둥글게 */
      width: 100%;                   /* 부모 가득 (실제 픽셀은 width 속성과 분리) */
      cursor: crosshair;             /* 십자 커서 (조준점 느낌) */
      display: block;                /* 인라인 여백 제거 */
    }
  </style>
</head>
<body>
  <!-- 파티클을 그리는 캔버스 (실제 해상도 400x300) -->
  <canvas id="particles" width="400" height="300"></canvas>
  <script>(function() {
    const canvas = document.getElementById('particles');
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    const mouse = { x: -999, y: -999 };
    const PARTICLE_COUNT = 80;
    const CONNECT_DIST = 80;
    const MOUSE_RADIUS = 100;

    canvas.addEventListener('mousemove', (e) => {
      const rect = canvas.getBoundingClientRect();
      mouse.x = (e.clientX - rect.left) * (W / rect.width);
      mouse.y = (e.clientY - rect.top) * (H / rect.height);
    });
    canvas.addEventListener('mouseleave', () => { mouse.x = -999; mouse.y = -999; });

    const particles = Array.from({ length: PARTICLE_COUNT }, () => ({
      x: Math.random() * W,
      y: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.8,
      vy: (Math.random() - 0.5) * 0.8
    }));

    function animate() {
      ctx.clearRect(0, 0, W, H);
      for (const p of particles) {
        const dx = p.x - mouse.x;
        const dy = p.y - mouse.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < MOUSE_RADIUS && dist > 0) {
          p.vx += (dx / dist) * 0.3;
          p.vy += (dy / dist) * 0.3;
        }
        p.vx *= 0.98;
        p.vy *= 0.98;
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > W) p.vx *= -1;
        if (p.y < 0 || p.y > H) p.vy *= -1;
        p.x = Math.max(0, Math.min(W, p.x));
        p.y = Math.max(0, Math.min(H, p.y));
      }
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < CONNECT_DIST) {
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = 'rgba(59,130,246,' + (1 - dist / CONNECT_DIST) * 0.5 + ')';
            ctx.stroke();
          }
        }
      }
      for (const p of particles) {
        ctx.beginPath();
        ctx.arc(p.x, p.y, 2, 0, Math.PI * 2);
        ctx.fillStyle = '#60a5fa';
        ctx.fill();
      }
      requestAnimationFrame(animate);
    }
    animate();
  })();</script>
</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
#particles {
  background: #0f172a;
  border-radius: 8px;
  width: 100%;
  cursor: crosshair;
  display: block;
}
```

```javascript
(function() {
  const canvas = document.getElementById('particles');
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  const mouse = { x: -999, y: -999 };
  const PARTICLE_COUNT = 80;
  const CONNECT_DIST = 80;
  const MOUSE_RADIUS = 100;

  canvas.addEventListener('mousemove', (e) => {
    const rect = canvas.getBoundingClientRect();
    mouse.x = (e.clientX - rect.left) * (W / rect.width);
    mouse.y = (e.clientY - rect.top) * (H / rect.height);
  });
  canvas.addEventListener('mouseleave', () => { mouse.x = -999; mouse.y = -999; });

  const particles = Array.from({ length: PARTICLE_COUNT }, () => ({
    x: Math.random() * W,
    y: Math.random() * H,
    vx: (Math.random() - 0.5) * 0.8,
    vy: (Math.random() - 0.5) * 0.8
  }));

  function animate() {
    ctx.clearRect(0, 0, W, H);
    for (const p of particles) {
      const dx = p.x - mouse.x;
      const dy = p.y - mouse.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < MOUSE_RADIUS && dist > 0) {
        p.vx += (dx / dist) * 0.3;
        p.vy += (dy / dist) * 0.3;
      }
      p.vx *= 0.98;
      p.vy *= 0.98;
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0 || p.x > W) p.vx *= -1;
      if (p.y < 0 || p.y > H) p.vy *= -1;
      p.x = Math.max(0, Math.min(W, p.x));
      p.y = Math.max(0, Math.min(H, p.y));
    }
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < CONNECT_DIST) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = 'rgba(59,130,246,' + (1 - dist / CONNECT_DIST) * 0.5 + ')';
          ctx.stroke();
        }
      }
    }
    for (const p of particles) {
      ctx.beginPath();
      ctx.arc(p.x, p.y, 2, 0, Math.PI * 2);
      ctx.fillStyle = '#60a5fa';
      ctx.fill();
    }
    requestAnimationFrame(animate);
  }
  animate();
})();
```

**실행 결과** — 실행하지 않음 — 브라우저 DOM API 를 쓰는 예제다 — 브라우저에서 확인한다.

**풀이 요점**

- 한 프레임은 「지우기 → 옮기기 → 선 → 점 → 다음 예약」 차례다.
- 마우스 좌표는 `W / rect.width` · `H / rect.height` 로 그리기 좌표에 맞춘다.
- 밀어내기는 단위 벡터 × 0.3 을 속도에 더하는 것이고, `dist > 0` 이 0 으로 나누기를 막는다.
- 마찰 0.98 때문에 마우스 없이는 점들이 서서히 멈춘다.
- 안쪽 고리를 `j = i + 1` 부터 돌려 쌍마다 한 번만 재지만, 여전히 O(n²) 이다.
- 점을 선 뒤에 그려야 점이 선 위에 보인다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 DOM API 를 쓰는 예제다 — 브라우저에서 확인한다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

# animation/advanced-effects/01 — Interactive Particle Field — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 마우스가 캔버스를 떠난 뒤의 밀어내기 (예측)

```javascript
// 질문용 발췌
canvas.addEventListener('mouseleave', () => { mouse.x = -999; mouse.y = -999; });
// ... animate() 안, 파티클마다
const dx = p.x - mouse.x;
const dy = p.y - mouse.y;
const dist = Math.sqrt(dx * dx + dy * dy);
if (dist < MOUSE_RADIUS && dist > 0) { /* 밀어내기 */ }
```

- 마우스가 캔버스(400×300)를 떠난 뒤, 밀려나는 파티클은 몇 개인가?
- 그렇게 되는 까닭이 되는 거리는 어느 정도인가?

### 2. 두 점 사이 거리에 따른 선의 진하기 (예측)

```javascript
// 질문용 발췌  (CONNECT_DIST = 80)
if (dist < CONNECT_DIST) {
  ctx.strokeStyle = 'rgba(59,130,246,' + (1 - dist / CONNECT_DIST) * 0.5 + ')';
}
```

- 두 점의 거리가 40 이면 선의 알파(투명도) 값은 얼마인가?
- 거리가 0 에 아주 가까울 때와 정확히 80 일 때는 각각 어떻게 되나?

### 3. 마우스를 한 번도 올리지 않고 두면 (예측)

```javascript
// 질문용 발췌  (파티클마다, 매 프레임)
p.vx *= 0.98;
p.vy *= 0.98;
p.x += p.vx;
p.y += p.vy;
```

- 마우스를 대지 않고 오래 두면 파티클의 움직임은 어떻게 되나?
- 60 프레임 뒤 속도는 처음 속도의 대략 몇 배인가?

### 4. 마우스 좌표에 `W / rect.width` 를 곱하는 까닭 (왜)

- 이벤트의 `clientX - rect.left` 를 그대로 쓰지 않고 `W / rect.width` 를 곱하는 까닭은 무엇인가?

### 5. 밀어내기 조건에 `dist > 0` 이 붙은 까닭 (왜)

- `dist < MOUSE_RADIUS` 만으로 부족하고 `dist > 0` 을 함께 검사하는 까닭은 무엇인가?

### 6. 프레임 맨 앞의 `clearRect` 와 「선 다음에 점」 차례 (왜)

- `animate` 맨 앞에서 `clearRect` 를 부르는 까닭은 무엇인가?
- 점을 연결선보다 나중에 그리는 까닭은 무엇인가?

### 7. 파티클을 80개에서 200개로 늘리면 (경계)

- 연결선을 위해 거리를 재는 횟수는 한 프레임에 몇 번에서 몇 번으로 바뀌나?
- 점 수가 2.5 배일 때 비교 횟수는 대략 몇 배가 되나?

### 8. 원본 설명의 「마우스에 끌려온다」 (경계)

- 이 코드에서 파티클이 마우스 쪽으로 끌려오게 만드는 줄은 어디인가?

### 9. 벽 반사만 하고 위치를 가두지 않으면 (경계)

- `Math.max(0, Math.min(W, p.x))` 줄을 빼면 벽을 넘은 점에 어떤 일이 생길 수 있나?

### 10. CSS 애니메이션 · 즉시 실행 함수와의 다리 (연결)

- 이 효과의 점 하나하나를 CSS `@keyframes` 로 움직일 수 없는 까닭은 무엇인가?
- 코드 전체를 `(function() { ... })();` 로 감싼 것은 어떤 개념과 이어지나?

## 실습

### 실습 1. 마우스를 피하는 파티클 필드 만들기

**만들 것** — 어두운 캔버스에 점 80개가 떠다니고, 가까운 점끼리 선으로 이어지며, 마우스를 대면 근처 점이 밀려나는 효과를 만든다.

**요구 조건**

1. 1단계 — 준비: 캔버스에서 2D 컨텍스트를 얻고, 그리기 해상도(속성 `width` · `height`)를 `W` · `H` 로 읽는다. 마우스 위치는 처음에 캔버스에서 먼 곳으로 둔다.
2. 2단계 — 마우스 좌표: 캔버스 위에서 마우스가 움직이면 화면 좌표를 캔버스의 그리기 좌표로 환산해(CSS 로 늘어난 비율을 되돌려) `mouse` 에 넣는다.
3. 2단계 — 마우스 이탈: 마우스가 캔버스를 벗어나면 `mouse` 를 다시 먼 곳으로 보낸다.
4. 3단계 — 파티클 생성: `PARTICLE_COUNT` 개의 `{ x, y, vx, vy }` 를 만든다. 위치는 캔버스 안 무작위, 속도는 축마다 −0.4 이상 0.4 미만 무작위다.
5. 4단계 — 밀어내기: 매 프레임 파티클마다 마우스와의 거리를 재고, `MOUSE_RADIUS` 미만이며 0 이 아니면 마우스 반대 방향의 단위 벡터에 0.3 을 곱해 속도에 더한다.
6. 4단계 — 이동: 속도에 0.98 을 곱하고, 위치에 속도를 더한다. 위치가 경계를 넘으면 그 축의 속도를 뒤집고, 위치를 캔버스 안으로 가둔다.
7. 5단계 — 연결선: 모든 쌍을 한 번씩만 비교해 거리가 `CONNECT_DIST` 미만이면 선을 긋는다. 투명도는 `(1 − 거리 / CONNECT_DIST) × 0.5` 다.
8. 6단계 — 점: 선을 다 그린 뒤 파티클마다 반지름 2 인 원을 채운다.
9. 7단계 — 루프: 매 프레임 처음에 캔버스 전체를 지우고, 끝에서 다음 프레임을 예약한다. 처음 한 번은 직접 호출해 시작한다.
10. 7단계 — 감싸기: 스크립트 전체를 즉시 실행 함수로 감싼다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>Interactive Particle Field</title>
  <style>
    #particles {
      background: #0f172a;
      border-radius: 8px;
      width: 100%;
      cursor: crosshair;
      display: block;
    }
  </style>
</head>
<body>
  <canvas id="particles" width="400" height="300"></canvas>
  <script>
  // TODO(7단계): 아래 전체를 즉시 실행 함수로 감싼다
    const canvas = document.getElementById('particles');
    const ctx = null; // TODO(1단계): 2D 컨텍스트 얻기
    const W = 0, H = 0; // TODO(1단계): 캔버스의 그리기 해상도 읽기
    const mouse = { x: 0, y: 0 }; // TODO(1단계): 처음엔 캔버스에서 먼 곳
    const PARTICLE_COUNT = 80;
    const CONNECT_DIST = 80;
    const MOUSE_RADIUS = 100;

    // TODO(2단계): mousemove — 화면 좌표를 그리기 좌표로 환산해 mouse 에 넣기
    // TODO(2단계): mouseleave — mouse 를 먼 곳으로 보내기

    const particles = []; // TODO(3단계): PARTICLE_COUNT 개의 { x, y, vx, vy }

    function animate() {
      // TODO(7단계): 캔버스 전체 지우기

      for (const p of particles) {
        // TODO(4단계): 반경 안이면 마우스 반대 방향으로 밀기
        // TODO(4단계): 마찰 → 이동 → 벽 반사 → 가두기
      }

      // TODO(5단계): 모든 쌍을 한 번씩 비교해 가까우면 선 긋기
      //   선 색: 'rgba(59,130,246,' + 투명도 + ')'

      for (const p of particles) {
        // TODO(6단계): 반지름 2 인 원 채우기 — 색 '#60a5fa'
      }

      // TODO(7단계): 다음 프레임 예약
    }
    // TODO(7단계): 첫 프레임 시작
  </script>
</body>
</html>
```

**확인 방법** — 파일을 브라우저로 연다. 점들이 떠다니다 서서히 느려지는지, 가까운 점끼리 선이 이어지고 멀어지면 흐려지는지, 마우스를 대면 근처 점이 바깥으로 밀려나는지, 마우스를 빼면 밀어내기가 멈추는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

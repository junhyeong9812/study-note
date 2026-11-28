# javascript/math-motion/18 — Magnetic Effect — 정리 (힌트)

> 출처 — study-site 항목 `javascript/magnetic-effect`(항목 데이터 `data/javascript/math-motion.json`) · 정답 코드 study-practice `javascript/math-motion/reference/magnetic-effect.js`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 브라우저 DOM API 를 쓰는 예제다 — 브라우저에서 확인한다.

## 한눈에 — 쉽게 말하면

**마그네틱 효과는 「냉장고 자석이 손가락 쪽으로 살짝 딸려 오는 것」이다.**
손가락이 멀면 자석은 꿈쩍하지 않는다.
손가락이 일정 거리 안으로 들어오면 자석이 손가락 쪽으로 조금 기운다.
손가락을 치우면 자석은 천천히 제자리로 돌아간다.
마우스와 버튼도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 손가락 | 마우스 포인터 (`e.clientX`, `e.clientY`) |
| 냉장고 자석 | 버튼 요소 |
| 자석이 반응하는 거리 | `threshold` (임계 거리) |
| 얼마나 세게 끌리나 | `strength` (강도) |
| 천천히 기울고 천천히 돌아오기 | `lerp` 로 매 프레임 조금씩 다가가기 |

```text
        멀다 (dist >= threshold)          가깝다 (dist < threshold)

   ●마우스                                     ●마우스
                                              ↗
          [버튼]  ← 제자리               [버튼]→  ← 마우스 쪽으로 조금 이동
```

## 이 주제가 답하려는 질문

1. 마우스가 버튼에서 얼마나 떨어져 있는지 어떻게 재나?
2. 거리에 따라 버튼을 「얼마나」 움직일지 어떻게 정하나?
3. 버튼이 툭 튀지 않고 부드럽게 따라가게 하려면 어떻게 하나?
4. 왜 CSS `:hover` 만으로는 만들 수 없나?

## 동작 방식

전체 흐름은 두 갈래로 나뉜다.
`mousemove` 이벤트는 「목표 위치」만 계산한다.
`requestAnimationFrame` 루프는 「현재 위치」를 목표 쪽으로 조금씩 옮겨 화면에 그린다.

```text
 mousemove (마우스가 움직일 때만)          animate (매 프레임, 쉬지 않고)
 ┌──────────────────────────────┐        ┌───────────────────────────────┐
 │ 버튼 중심 계산                │        │ x = lerp(x, targetX, 0.15)    │
 │ dx, dy, dist 계산             │ target │ y = lerp(y, targetY, 0.15)    │
 │ dist < threshold ?            │ ─────▶ │ transform = translate(x, y)   │
 │   target = d * strength * f   │        │ requestAnimationFrame(animate)│
 │   아니면 target = 0           │        └───────────────────────────────┘
 └──────────────────────────────┘
```

> **목표 위치(target)** — 버튼이 결국 가 있어야 할 오프셋.\
> 예: `states[i].targetX = 10.5` 이면 버튼은 오른쪽으로 10.5만큼 가 있고 싶다.

### (1) 버튼 중심과 마우스 사이의 거리 재기

**언제 쓰나** — 마우스가 움직일 때마다 버튼마다 한 번씩 잰다.

```text
const rect = btn.getBoundingClientRect();
cx = rect.left + rect.width / 2      ─┐
cy = rect.top  + rect.height / 2     ─┴─▶ 버튼 중심 (cx, cy)
dx = e.clientX - cx                  ─┐
dy = e.clientY - cy                  ─┴─▶ 중심에서 마우스까지의 변위
dist = Math.hypot(dx, dy)            ───▶ 직선 거리 √(dx² + dy²)
```

- `getBoundingClientRect()` 는 요소의 화면(뷰포트) 기준 위치와 크기를 준다.
- 왼쪽 끝에 너비의 절반을 더하면 가로 중심이 된다.
- `e.clientX` · `e.clientY` 도 같은 뷰포트 기준 좌표라서 둘을 바로 뺄 수 있다.
- `dx` · `dy` 는 부호가 있다 — 마우스가 오른쪽이면 `dx > 0`, 위쪽이면 `dy < 0` 이다.
- `Math.hypot(dx, dy)` 는 피타고라스 정리로 직선 거리를 낸다.

> **변위** — 방향과 크기를 함께 가진 차이(여기서는 중심 → 마우스).\
> 예: 마우스가 중심보다 오른쪽 30, 아래 40 이면 변위는 `(30, 40)`, 거리는 50.

> **뷰포트** — 브라우저 창에서 지금 보이는 영역.\
> 예: `clientX = 0` 은 보이는 영역의 왼쪽 끝이다.

### (2) 임계 거리 안에서만 끌기 — factor

**언제 쓰나** — 가까울 때만 반응하고, 경계에서 툭 끊기지 않게 할 때.

```text
dist < threshold ?
   예  → factor = 1 - dist / threshold     (가운데 1, 경계 0)
   아니오 → target = 0                      (원위치로 돌아갈 목표)

dist:    0 ──────── 60 ──────── 120(threshold)
factor:  1.0        0.5         0.0
```

- `factor` 는 거리가 0 이면 1, `threshold` 에 닿으면 0 이 되는 비율이다.
- 경계 근처에서 `factor` 가 0 에 가까우므로 효과가 0 에서 부드럽게 시작한다.
- 조건이 `<` 이므로 거리가 정확히 `threshold` 이면 `else` 쪽(목표 0)으로 간다.

> **임계 거리(threshold)** — 효과가 켜지는 경계 거리.\
> 예: `threshold = 120` 이면 중심에서 120 안쪽에서만 끌린다.

### (3) 목표 오프셋 공식

**언제 쓰나** — 버튼을 마우스 쪽으로 「얼마나」 옮길지 정할 때.

```text
targetX = dx * strength * factor
targetY = dy * strength * factor

크기 = dist * strength * (1 - dist/threshold)
     (strength = 0.35, threshold = 120 일 때)

dist   0  →  0 * 0.35 * 1.0  = 0
dist  60  → 60 * 0.35 * 0.5  = 10.5   ← 가장 크다
dist 120  →  경계 — 0
```

- 원본의 공식은 `distance < threshold ? offset = (mouse - center) * strength : offset = 0` 이다.
- 정답 코드는 여기에 `factor` 를 한 번 더 곱해 경계에서 부드럽게 만든다.
- 방향은 `dx` · `dy` 의 부호를 그대로 따르므로 버튼은 항상 마우스 쪽으로 움직인다.
- `strength = 0.35` 는 「변위의 35% 까지」라는 뜻이고, `factor` 가 곱해지면 그보다 작아진다.
- 크기 `d × 0.35 × (1 − d/120)` 은 `d` 가 0 일 때도 0, 120 일 때도 0 이다.
- 그래서 가운데 지점인 `d = 60` 에서 가장 크게 끌린다(10.5).
- 즉 마우스가 버튼 한가운데 있을 때는 오히려 끌림이 없다.

### (4) 글로우와 디버깅 표시

**언제 쓰나** — 가까울수록 시각 피드백을 강하게 줄 때.

```text
boxShadow = `0 0 ${30 + factor*20}px rgba(59,130,246,${0.2 + factor*0.3})`
  factor 0 → 흐림 반경 30, 불투명도 0.2
  factor 1 → 흐림 반경 50, 불투명도 0.5
```

- `factor` 가 커질수록 그림자가 넓어지고 진해진다.
- 이 값은 `btn.style.boxShadow` 로 넣으므로 인라인 스타일이다.
- 인라인 스타일은 스타일시트의 일반 규칙(`!important` 가 없는 것)보다 이긴다.
- CSS 에 `transition: box-shadow 0.3s` 가 있으므로 그림자 변화는 0.3초에 걸쳐 바뀐다(코드에서 읽은 것 — 렌더 실측 아님).
- 첫 번째 버튼(`i === 0`)만 `readout` 에 거리 · factor · 오프셋을 적는다.
- 그 문자열은 `Math.round(dist)` · `factor.toFixed(2)` · `targetX.toFixed(1)` 로 자릿수를 맞춘다.

> **인라인 스타일** — 요소의 `style` 속성(또는 `el.style.xxx`)에 직접 넣은 스타일.\
> 예: `btn.style.boxShadow = '...'` 는 `<button style="box-shadow: ...">` 와 같다.

### (5) lerp 로 부드럽게 따라가기

**언제 쓰나** — 목표가 갑자기 바뀌어도 화면 위치는 천천히 따라가게 할 때.

```text
lerp(a, b, t) = a + (b - a) * t

프레임마다: x = lerp(x, targetX, 0.15)   → 남은 거리의 15% 만큼 다가감

target = 10, x 시작 = 0
 1프레임: 0     + (10 - 0)     * 0.15 = 1.5
 2프레임: 1.5   + (10 - 1.5)   * 0.15 = 2.775
 n프레임 뒤 남은 거리 = 10 × 0.85ⁿ
```

- 한 번에 목표로 가지 않고 남은 거리의 일정 비율만 간다.
- 그래서 처음엔 빠르고 목표에 가까워질수록 느려진다.
- 목표가 0 이 되면 같은 방식으로 천천히 원위치로 돌아온다.
- `transform: translate(x, y)` 로 옮기므로 레이아웃 자리는 그대로이고 그려지는 위치만 바뀐다.
- `requestAnimationFrame(animate)` 를 함수 끝에서 다시 불러 매 프레임 이 일을 되풀이한다.

> **lerp(선형 보간)** — 두 값 사이를 비율 `t` 만큼 잇는 계산.\
> 예: `lerp(0, 10, 0.15)` 는 `1.5`.

> **requestAnimationFrame** — 브라우저가 다음 화면을 그리기 직전에 콜백을 불러 주는 함수.\
> 예: 콜백 안에서 자기 자신을 다시 넘기면 프레임마다 도는 루프가 된다.

## 문법 — 형태와 규칙

최소 예제(버튼 하나):

```javascript
const btn = document.querySelector('.magnetic-btn');
const s = { x: 0, y: 0, tx: 0, ty: 0 };
const lerp = (a, b, t) => a + (b - a) * t;

window.addEventListener('mousemove', (e) => {
  const r = btn.getBoundingClientRect();
  const dx = e.clientX - (r.left + r.width / 2);
  const dy = e.clientY - (r.top + r.height / 2);
  const dist = Math.hypot(dx, dy);
  const f = dist < 120 ? 1 - dist / 120 : 0;
  s.tx = dx * 0.35 * f;
  s.ty = dy * 0.35 * f;
});

(function loop() {
  s.x = lerp(s.x, s.tx, 0.15);
  s.y = lerp(s.y, s.ty, 0.15);
  btn.style.transform = `translate(${s.x}px, ${s.y}px)`;
  requestAnimationFrame(loop);
})();
```

- 버튼마다 상태 `{ x, y, targetX, targetY }` 를 따로 둔다 — 버튼이 여럿이면 `Array.from(btns).map(...)` 으로 같은 개수만큼 만든다.
- 이벤트는 버튼이 아니라 `window` 에 단다 — 버튼 밖의 근처에서도 거리를 재야 하기 때문이다.
- 이벤트 핸들러는 목표만 고치고, 실제 `transform` 은 루프에서만 쓴다.
- `factor = 1 - dist / threshold` 는 `dist < threshold` 일 때만 계산한다(밖에서는 음수가 되기 때문이다).
- `lerp` 의 `t` 는 0~1 사이다 — 클수록 빨리 따라간다.

| 이름 | 정답 코드의 값 | 뜻 |
|---|---|---|
| `threshold` | `120` | 효과가 켜지는 거리 |
| `strength` | `0.35` | 변위의 몇 % 까지 끌리나 |
| `lerp` 의 `t` | `0.15` | 프레임마다 남은 거리의 몇 % 를 가나 |
| 글로우 반경 | `30 + factor*20` | 가까울수록 넓게 |
| 글로우 불투명도 | `0.2 + factor*0.3` | 가까울수록 진하게 |

## 어디서 틀리나

### 1. CSS `:hover` 로 하려는 실수

원본의 팁: CSS 의 `:hover` 만으로는 불가능하고 JS `mousemove` 가 필요하다.
`:hover` 는 「포인터가 요소 위에 있다 / 없다」 두 상태만 안다.
마우스의 좌표도, 버튼 밖에서의 거리도 알 수 없다.
그래서 「거리에 비례해 마우스 쪽으로」 움직이는 값을 만들 수 없다.

### 2. factor 를 빼먹어 경계에서 툭 튄다

원본의 팁: threshold 안에서 거리에 비례하는 factor 를 계산하고 마우스 오프셋에 곱한다.
공식 `(mouse - center) * strength` 만 쓰면 거리 119 에서 오프셋 약 41.65, 거리 120 에서 0 이 된다.
경계를 넘는 순간 목표가 크게 뛴다.
`factor` 를 곱하면 경계에서 오프셋이 0 으로 모여 이음매가 사라진다.

### 3. mousemove 에서 transform 을 바로 쓴다

원본의 팁: lerp 으로 부드럽게 전환한다.
핸들러에서 `transform` 을 바로 바꾸면 버튼이 마우스를 따라 뚝뚝 끊겨 움직인다.
또 마우스가 멈추면 이벤트도 멈추므로 「천천히 돌아오기」를 할 주체가 없다.
목표와 현재를 나누고 루프에서 lerp 하는 까닭이 이것이다.

### 4. 마우스가 멀어진 뒤에도 글로우가 남는다

`else` 쪽은 `targetX` · `targetY` 만 0 으로 되돌린다.
`btn.style.boxShadow` 는 되돌리지 않는다.
그래서 임계 거리 밖으로 나가도 마지막으로 넣은 인라인 그림자가 그대로 남는다(코드에서 읽은 것 — 렌더 실측 아님).
게다가 인라인 스타일이라 CSS 의 `:hover` 그림자 규칙보다 이긴다.

### 5. 두 번째 버튼도 파란 글로우가 된다

글로우 색은 `rgba(59,130,246, …)` 로 고정돼 있다.
`.secondary` 버튼은 보라색 배경이고 CSS `:hover` 그림자도 보라색이지만, 임계 거리 안에서 넣은 인라인 그림자는 파란색이다(코드에서 읽은 것 — 렌더 실측 아님).
버튼마다 색을 다르게 하려면 색을 버튼별로 골라야 한다.

### 6. 정확히 경계 거리

조건이 `dist < threshold` 이므로 `dist === threshold` 이면 끌리지 않는다.
어차피 그 자리에서 `factor` 는 0 이라 결과는 같다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `Math.hypot(dx, dy)` 가 √(dx²+dy²) 를 준다 | JavaScript 언어 명세(ECMAScript) |
| `toFixed` · `Math.round` 의 자릿수 처리 | JavaScript 언어 명세 |
| `getBoundingClientRect` · `clientX` 가 뷰포트 기준이다 | 웹 플랫폼 표준(브라우저 API) — 언어가 아니다 |
| `requestAnimationFrame` 이 다음 그리기 전에 콜백을 부른다 | 웹 플랫폼 표준 — 몇 번 불리는지(초당 횟수)는 브라우저와 화면에 따라 다르다 |
| 인라인 스타일이 일반 스타일시트 규칙보다 이긴다 | CSS 캐스케이드 규칙 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 눈에 띄어야 하는 CTA 버튼 몇 개 | 마그네틱 효과 | 화면의 모든 버튼에 일괄 적용 |
| 포인터가 「위에 있나」만 중요 | CSS `:hover` | mousemove 거리 계산 |
| 부드럽게 따라오고 돌아오기 | 목표/현재 분리 + lerp 루프 | 핸들러에서 `transform` 직접 쓰기 |
| 경계에서 자연스럽게 시작 | `factor = 1 - dist/threshold` 곱하기 | `(mouse - center) * strength` 만 쓰기 |
| 위치 이동 | `transform: translate` | 레이아웃을 바꾸는 `left` · `top` (원본에 근거 없음 — 추론) |

## 핵심 문장

1. **거리는 버튼 중심과 마우스의 변위로 잰다** — `getBoundingClientRect` 로 중심을, `Math.hypot` 으로 거리를 낸다.
2. **목표 오프셋 = 변위 × strength × factor** — factor 는 가운데 1, 경계 0 이다.
3. **그래서 끌림은 중심도 경계도 아닌 중간 거리에서 가장 크다.**
4. **mousemove 는 목표만, rAF 루프는 lerp 로 현재를 목표 쪽으로** — 부드러움은 이 분리에서 나온다.
5. **`:hover` 는 위에 있나 없나만 알기 때문에 이 효과에는 JS 가 필요하다.**

## 관련 자료

- `lerp` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `distance-2d` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `smooth-cursor-following` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/javascript/math-motion.json` 의 `magnetic-effect`

## 용어 풀이

- **마그네틱 효과** — 포인터가 가까이 오면 요소가 그쪽으로 끌려가는 인터랙션.
- **임계 거리(threshold)** — 효과가 켜지는 경계 거리.
- **강도(strength)** — 변위 가운데 몇 비율만큼 따라가나.
- **factor** — 거리를 0~1 로 바꾼 비율, 가까울수록 1.
- **변위** — 중심에서 마우스까지의 방향 있는 차이 `(dx, dy)`.
- **뷰포트** — 브라우저 창에서 지금 보이는 영역.
- **`getBoundingClientRect`** — 요소의 뷰포트 기준 위치와 크기를 주는 메서드.
- **`Math.hypot`** — 인자들의 제곱합의 제곱근을 주는 함수.
- **lerp(선형 보간)** — `a + (b - a) * t`, 두 값 사이를 비율로 잇는 계산.
- **`requestAnimationFrame`** — 다음 그리기 직전에 콜백을 불러 주는 브라우저 함수.
- **인라인 스타일** — 요소의 `style` 에 직접 넣은 스타일.
- **`translate`** — 레이아웃 자리는 두고 그려지는 위치만 옮기는 `transform` 함수.

## 더 들어가면

- `getBoundingClientRect` 는 `transform` 이 적용된 뒤의 상자를 돌려준다(확인 필요). 그렇다면 버튼이 옮겨진 만큼 중심도 같이 움직여서, 정답 코드의 오프셋은 「원래 자리」가 아니라 「지금 자리」 기준으로 계산된다 — 끌림이 공식보다 약간 줄어드는 되먹임이 생긴다(확인 필요).
- `t = 0.15` 를 프레임마다 쓰면 화면 주사율이 높을수록 더 빨리 따라간다(확인 필요). 경과 시간으로 `t` 를 보정하는 방식(`1 - Math.pow(1 - t, dt * 60)` 같은 꼴)이 쓰인다(확인 필요).
- 루프는 아무것도 움직이지 않아도 계속 돈다. 목표와 현재가 충분히 가까우면 멈추고, mousemove 때 다시 시작하는 최적화가 가능하다.
- 마우스가 창 밖으로 나가면 `mousemove` 가 오지 않아 목표가 그대로 남을 수 있다. `mouseleave`(문서 기준)에서 목표를 0 으로 돌리는 처리를 덧붙이기도 한다(확인 필요).
- 터치 기기에는 hover 개념이 없어 이 효과가 거의 의미가 없다(확인 필요). `prefers-reduced-motion` 설정을 존중해 효과를 끄는 것도 고려한다(확인 필요).

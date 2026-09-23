# css/syntax/48 — 혼합 모드와 `isolation` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다. ★ **답을 `(r,g,b)` 세 숫자로 적어라** — 「어두워진다」는 답이 아니다.
> ★ 공식을 외워 계산하는 것이 이 주제의 인출이다. `multiply` 는 **채널별 곱 ÷ 255**.
> ★ 이 주제에서 `getComputedStyle` 은 **거짓 안심**을 준다. 계산값이 `multiply` 여도 화면은 원색일 수 있다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 공식을 손으로 따라가라 (예측)

```css
.bd  { background: #3399cc; }                          /* (51,153,204) */
.src { background: #cc6633; mix-blend-mode: multiply; } /* (204,102,51) — .bd 의 자식 */
```

- 겹친 자리의 픽셀은 무엇인가 — 세 채널을 각각 계산해 보라.
- `multiply` 를 `screen` 으로 바꾸면 무엇이 되는가?
- `difference` 로 바꾸면?
- `darken` 과 `lighten` 은 각각 무엇이 되는가?

### 2. backdrop 이 하나가 아니다 (예측)

```css
.stage .left  { background: #3399cc; }   /* 왼쪽 절반 */
.stage .right { background: #66cc33; }   /* 오른쪽 절반 */
.band { background: #cc6633; mix-blend-mode: multiply; }  /* 둘을 가로지르는 띠 */
```

- 띠의 **왼쪽** 픽셀은 무엇인가?
- 띠의 **오른쪽** 픽셀은 무엇인가?
- `mix-blend-mode` 가 섞는 대상은 「부모」인가 「바로 뒤 형제」인가 「뒤쪽 전부」인가?
- 그 범위의 경계는 무엇이 정하는가?

### 3. 손잡이 두 개 (예측)

```css
.a, .b { background-image: linear-gradient(#cc6633, #cc6633);
         background-color: #3399cc; }        /* 페이지 배경은 #ffcc00 */
.a { background-blend-mode: multiply; }
.b { mix-blend-mode: multiply; }
```

- `.a` 의 픽셀은 무엇인가 — 무엇과 무엇을 섞은 값인가?
- `.b` 의 픽셀은 무엇인가 — 무엇과 무엇을 섞은 값인가?
- `.a` 에서 `background-color` 를 `transparent` 로 바꾸면 무엇이 되는가?
- `background-blend-mode` 는 요소 바깥을 보는가?

### 4. 한 줄로 혼합을 끈다 (예측)

```css
.page { background: #ffcc00; }
.g    { }                       /* .page 의 자식, 배경 없음 */
.src  { background: #6699ff; mix-blend-mode: multiply; }   /* .g 의 자식 */
```

- `.src` 의 픽셀은 무엇인가?
- `.g` 에 `isolation: isolate` 를 넣으면 무엇이 되는가?
- `.src` 자신에게 `isolation: isolate` 를 넣으면 무엇이 되는가?
- `.page` 에 `isolation: isolate` 를 넣으면 무엇이 되는가 — 왜 그런가?

### 5. `isolation` 을 안 썼는데 격리된다 (예측)

부모에 아래 여섯을 각각 붙이고 같은 `multiply` 자식을 렌더한다.

```css
/* (1) 없음  (2) opacity: .999  (3) filter: brightness(1)
   (4) transform: translateZ(0)  (5) will-change: opacity
   (6) position: relative; z-index: 0  (7) mix-blend-mode: normal */
```

- 일곱 중 **섞이는** 것은 몇 번인가?
- 격리되는 것들의 공통점은 한 낱말로 무엇인가?
- `opacity: .999` 처럼 **화면이 안 바뀌는 값**도 격리를 만드는가?
- 이 사실이 실무에서 만드는 대표 사고는 무엇인가?

### 6. 공식이 안 통하는 자리 (경계)

- 12개 모드 중 **채널별로 따로 계산되는** 모드를 분리 가능 모드라 한다. 아닌 것 넷은 무엇인가?
- `multiply` 를 **흰 배경** 위에서 테스트하면 무엇이 보이는가 — 왜 그런가?
- `screen` 을 **검정 배경** 위에서 테스트하면?
- backdrop 과 source 가 채널마다 보색(`Cs = 255 - Cb`)이면 `color-dodge` 는 무엇이 되는가?

### 7. `overlay` 를 손으로 (예측)

- `overlay(Cb, Cs)` 는 `hard-light` 로 어떻게 표현되는가 — 인자 순서에 주의하라.
- `Cb = 51`, `Cs = 204` 일 때 `overlay` 의 R 채널은 무엇인가?
- `Cb = 153`, `Cs = 102` 일 때 G 채널은?
- `overlay` 와 `hard-light` 의 결과가 서로 다른 이유를 한 문장으로.

### 8. 조용히 버려지는 선언 (왜)

```css
.x { mix-blend-mode: multiplyy; background-blend-mode: 50%; isolation: isolated; }
```

- 「진단 3창」 각각에서 무엇이 보이는가?
- 규칙 자체는 살아남는가?
- 세 계산값은 각각 무엇이 되는가?
- 이 주제에는 **3창을 전부 통과하는데 화면이 다른** 제4의 상태가 있다. 무엇인가?

### 9. 값은 몇 개 쓰나 (경계)

- `mix-blend-mode` 에 값을 여러 개 쓸 수 있는가?
- `background-blend-mode` 는?
- 배경 레이어가 하나뿐인데 `background-blend-mode: multiply` 를 걸면 무슨 일이 일어나는가?
- `isolation` 의 값 둘은 무엇인가?

### 10. 다른 주제로 잇기 (연결)

- 혼합의 경계를 정하는 것은 무엇이고, 그 정본은 몇 번 주제인가?
- [47번](../47-filter-and-backdrop-filter/2-summary.md)의 backdrop root 와 여기의 격리는 같은 축인가 — 무엇이 그것을 갈랐는가?
- 배경 레이어가 쌓이는 순서의 정본은 몇 번 주제인가?
- 알파를 어떻게 합칠지(합성 연산자)를 CSS 에서 만질 수 있는 표면은 어느 속성이고 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

# css/syntax/56 — 렌더링 파이프라인과 `will-change`: 무엇이 합성만으로 도는가 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [53번](../53-keyframes-and-animation/2-summary.md)과 [54번](../54-transform-2d-and-origin/2-summary.md)이다.
> ★ 이 주제에서는 **「무엇으로 쟀나」를 못 답하면 그 답은 근거가 없는 것**이다. 도구까지 같이 답하라.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 네 공정과 그 순서 (왜)

- 브라우저가 화면 한 장을 만들 때 거치는 네 공정을 순서대로 적을 수 있는가?
- 레이아웃이 다시 돌면 그 뒤 공정도 도는가, 안 도는가?
- 이 네 이름은 명세 용어인가 구현 용어인가?
- 「이 속성을 애니메이션해도 되나」를 판단하는 규칙을 한 줄로 적을 수 있는가?

### 2. 무엇으로 재는가 (경계)

- 두 애니메이션의 비용 차이를 스크린샷으로 판정할 수 있는가, 왜인가?
- CDP `Performance.getMetrics` 에서 이 주제에 쓸 수 있는 카운터 세 개를 들 수 있는가?
- 그 카운터로 **페인트** 횟수를 알 수 있는가, 없다면 무엇을 더 써야 하는가?
- 측정에서 「신호가 잡음보다 크다」를 무엇으로 확인했는가?

### 3. 이 열세 속성은 각각 어디부터 도는가 (예측)

```text
width · height · left · margin-left · font-size
color · box-shadow · border-radius
filter · visibility · background-color
transform · opacity
```

- 2초 동안 애니메이션했을 때 `RecalcStyleCount` 와 `LayoutCount` 가 **둘 다 0** 인 것은 무엇인가?
- `LayoutCount` 는 0 인데 `Paint` 이벤트는 도는 것은 무엇인가?
- `RecalcStyleCount` 는 도는데 `Paint`·`RasterTask` 가 0 인 것은 무엇인가?
- 여섯 카운터가 **전부 0** 인데 `RasterTask` 만 도는 것은 무엇인가, 그 결과가 왜 뜻밖인가?
- `visibility` 는 값이 한 번만 뒤집히는데 왜 스타일 재계산이 120번 도는가?

### 4. 같은 움직임의 비용 (예측)

```css
@keyframes byleft { to { left: 292px } }
@keyframes bytfm  { to { translate: 288px } }
```

- 두 막대의 화면 x 좌표는 시각마다 같은가 다른가?
- 2초 동안 각각의 `LayoutCount` 는 얼마인가?
- 눈으로 둘을 구분할 수 있는가?
- 이 실험에서 「정지 대조군」을 둔 이유는 무엇인가?

### 5. `will-change` 는 무엇을 하는가 (예측)

```css
.a { animation: move 2s linear infinite alternate; }               /* transform */
.b { animation: move 2s linear infinite alternate; will-change: transform; }
.c { animation: slide 2s linear infinite alternate; }              /* left */
.d { animation: slide 2s linear infinite alternate; will-change: left; }
```

- 넷의 `RecalcStyleCount`·`LayoutCount` 는 각각 얼마인가?
- `will-change` 가 지표를 바꾼 자리가 있는가?
- 「애니메이션이 끊긴다」의 처방으로 `will-change` 가 맞는가, 아니면 무엇이 맞는가?
- 명세는 `will-change` 사용에 대해 무엇을 경고하는가?

### 6. `will-change` 의 대가 (연결)

- `will-change: transform` 하나로 생기는 것 둘은 무엇이고, 각각의 정본은 어느 주제인가?
- `will-change: opacity` 와 `will-change: transform` 중 3D 를 깨뜨리는 것은 어느 쪽인가?
- 그 차이를 한 문장의 규칙으로 말할 수 있는가?
- `will-change` 를 쓴다면 언제 켜고 언제 꺼야 하는가?

### 7. `contain` 은 얼마나 줄이는가 (예측)

```css
/* 뒤에 3000줄이 있는 문서에서 상자 높이를 2초 동안 애니메이션한다 */
.wrap { }                       /* 대조군 */
.wrap { contain: layout; }
.wrap { contain: size; height: 320px; }
.wrap { contain: strict; height: 320px; }
```

- 네 경우의 `LayoutDuration` 은 각각 대략 얼마인가?
- `contain: layout` 혼자서 효과가 있었는가, 없다면 왜인가?
- 어느 값이 붙어야 벽이 서는가?
- 같은 움직임을 `transform` 으로 만들면 `LayoutDuration` 은 얼마인가?
- 그 사실이 `contain` 의 자리를 어떻게 정해 주는가?

### 8. `contain: strict` 의 대가 (예측)

```css
.card { width: 220px; border: 2px solid; padding: 6px; font: 14px/20px system-ui; }
.strict { contain: strict; }
```

- 글 두 줄이 든 두 상자의 높이는 각각 얼마인가?
- 아래 상자의 글자는 보이는가?
- 그 높이가 어떤 계산에서 나오는가?
- 높이를 모르는 카드에는 무엇을 써야 하는가?

### 9. 못 잰 것 (경계)

- 「`will-change` 를 남용하면 레이어가 늘어 메모리를 쓴다」를 이 환경에서 측정했는가?
- CDP `LayerTree` 도메인으로 무엇을 시도했고 결과가 어땠는가?
- `--disable-gpu` 를 빼면 달라졌는가?
- 측정하지 못한 주장을 문서에 어떻게 적어야 하는가?

### 10. 다른 주제와 잇기 (연결)

- [52번](../52-transition/2-summary.md)의 「비싼 속성을 전환한다」가 이 문서의 어느 표를 가리키는가?
- `transform` 이 레이아웃을 안 바꾼다는 것을 좌표로 보인 주제는 어디인가?
- `contain: paint` 와 `overflow: hidden` 은 같은 일을 하는데 3D 에서 결과가 달랐다 — 어떻게 달랐는가?
- 이 주제의 표를 외우는 것과 재는 법을 외우는 것 중 어느 쪽이 나은가, 왜인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

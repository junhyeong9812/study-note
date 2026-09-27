# css/syntax/47 — `filter` 와 `backdrop-filter` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다. ★ **답을 픽셀 값이나 좌표로 적어라** — 「흐려진다」·「어두워진다」는 답이 아니다.
> ★ 이 주제에서 `getComputedStyle` 은 거의 아무것도 증명하지 못한다. **화면을 읽었다고 답하라.**

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 순서만 바꿨다 (예측)

```css
.ab { background: #cc3366; filter: brightness(2) invert(1); }
.ba { background: #cc3366; filter: invert(1) brightness(2); }
```

- `#cc3366` 은 `(204, 51, 102)` 이다. `.ab` 의 바탕 픽셀은 무엇인가?
- `.ba` 는 무엇인가?
- 두 값이 갈리는 근본 원인은 무엇인가?
- `brightness(2)` 를 `brightness(1)` 로 바꾸면 두 값은 어떻게 되는가?

### 2. 순서가 안 갈리는 쌍도 있는가 (예측)

```css
.p { background: #cc3366; filter: grayscale(1) invert(1); }
.q { background: #cc3366; filter: invert(1) grayscale(1); }
```

- 두 픽셀은 같은가 다른가 — 같다면 무슨 값인가?
- 왜 그런가(두 함수의 정의에서 설명해 보라)?
- `grayscale(1)` 만 걸면 `(204,51,102)` 이 무엇이 되는가?
- `grayscale(1) hue-rotate(90deg)` 와 그 역순은 같은가 — 다르다면 얼마나 다른가?

### 3. 흐림을 숫자로 재라 (예측)

```css
.bar  { width: 300px; height: 60px;
        background: linear-gradient(to right, #000 0 150px, #fff 150px 300px); }
.blur { filter: blur(4px); }
```

- `.bar` 만 있을 때 경계에서 값이 0 도 255 도 아닌 구간의 폭은 몇 px 인가?
- `filter: blur(4px)` 를 걸면 그 폭은 몇 px 이 되는가?
- `blur(12px)` 이면?
- 선언한 길이와 띠 폭의 관계는 **보장인가 관찰인가**?

### 4. 화면이 안 바뀌는데 무엇이 망가지나 (예측)

```css
.host { position: absolute; left: 400px; top: 90px; width: 200px; height: 150px;
        filter: brightness(1); }
.fx   { position: fixed; left: 0; top: 0; }   /* .host 의 자식 */
```

- `.fx` 의 `getBoundingClientRect()` 는 `(0,0)` 인가 다른 값인가?
- `.fx.offsetParent` 는 무엇인가?
- `window.scrollTo(0, 300)` 뒤 `.fx` 의 좌표는 무엇이 되는가?
- `filter: brightness(1)` 을 `filter: none` 으로 바꾸면 무엇이 달라지는가?

### 5. `z-index: 9999` 가 안 먹는다 (예측)

```css
.wrap  { position: absolute; filter: brightness(1); }
.up    { position: absolute; z-index: 9999; background: #dc2626; }  /* .wrap 의 자식 */
.over  { position: absolute; z-index: 1; background: #2563eb; }     /* .wrap 의 형제 */
```

- `.up` 과 `.over` 가 겹치는 좌표의 픽셀은 빨강인가 파랑인가?
- `.wrap` 에서 `filter` 를 빼면 무엇이 되는가?
- `filter` 말고 같은 결과를 내는 선언을 셋 이상 대라.
- 이 현상의 정본 주제는 몇 번인가?

### 6. 그림자 둘 — 무엇을 따라가나 (예측)

```css
.a { box-shadow: 14px 14px 0 #dc2626; }              /* 투명 구석이 있는 PNG */
.b { filter: drop-shadow(14px 14px 0 #dc2626); }     /* 같은 PNG */
```

- 이미지의 **투명한** 부분에 대응하는 그림자 자리의 픽셀은 `.a` 에서 무엇인가?
- `.b` 에서는 무엇인가?
- `drop-shadow` 에 `spread` 값을 쓸 수 있는가?
- `.b` 를 쓰면 `.a` 에 없던 어떤 부작용이 따라오는가?

### 7. `backdrop-filter` 가 안 먹는다 (경계)

- `backdrop-filter` 는 무엇을 읽어서 흐리는가 — 자기 배경인가 뒤에 깔린 것인가?
- 조상에 `opacity: .999` 가 있으면 어떻게 되는가?
- 조상에 `isolation: isolate` 가 있으면 어떻게 되는가?
- 이 셋 중 어느 것이 **명세 근거**이고 어느 것이 **관찰**인가?

### 8. 함수 목록의 문법 (경계)

- 함수 여러 개는 무엇으로 잇는가 — 공백인가 쉼표인가?
- 목록 안의 함수 하나가 오타면 그 함수만 죽는가, 목록 전체가 죽는가?
- `blur(4)` 처럼 단위를 빼면 어떻게 되는가?
- `hue-rotate(90)` 은 유효한가?

### 9. `blur(0)` 과 `none` 의 차이 (왜)

- 두 선언의 **픽셀** 결과는 같은가?
- 두 선언의 **쌓임 맥락**은 같은가?
- 두 선언의 **포함 블록** 효과는 같은가?
- 그래서 필터 애니메이션의 시작값으로 `blur(0)` 을 쓰면 무엇이 문제인가?

### 10. 다른 주제로 잇기 (연결)

- `filter` 가 만드는 쌓임 맥락은 [48번](../48-blend-modes-and-isolation/2-summary.md)에서 무엇으로 쓰이는가?
- `filter` 와 같은 포함 블록 부작용을 내는 다른 속성은 무엇이고 몇 번 주제인가?
- 색 하나만 바꾸고 싶을 때 `filter` 대신 무엇을 쓰고 몇 번 주제인가?
- 요소를 임의 모양으로 잘라내려면 무엇을 쓰고 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

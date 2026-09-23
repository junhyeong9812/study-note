# css/syntax/55 — 3D 변환: `perspective`·`transform-style`·`backface-visibility` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [54번 주제](../54-transform-2d-and-origin/2-summary.md)다 — 함수 순서와 `transform-origin` 은 거기서 온다.
> 이 주제의 답에서 **계산값을 근거로 쓰면 틀린다.** 좌표나 픽셀로 답하라.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 원근이 없으면 무엇이 보이는가 (예측)

```css
b { width: 140px; height: 80px; transform: rotateY(50deg); }
```

- 이 상자의 `getBoundingClientRect()` 폭은 원래 폭보다 큰가 작은가?
- 화면에서 사다리꼴로 보이는가, 직사각형으로 보이는가?
- 계산값 `transform` 은 어떤 형태로 나오는가?
- 사다리꼴로 만들려면 무엇을 더해야 하는가?

### 2. 부모에 주기 대 자기에게 주기 (예측)

```css
.par            { perspective: 400px; }
.par b          { transform: rotateY(50deg); }
.slf b          { transform: perspective(400px) rotateY(50deg); }
/* 둘 다 부모(300x120) 안 왼쪽에 치우친 120x80 상자 */
```

- 두 상자의 `getBoundingClientRect()` 폭은 같은가 다른가?
- 두 상자의 **높이**는 같은가 다른가, 왜 그런가?
- `.par b` 의 계산값 `transform` 은 `perspective` 없는 경우와 같은가 다른가?
- 계산값만 보고 「원근이 걸렸나」를 판정할 수 있는가?
- 카드 여러 장을 **한 공간에 있는 것처럼** 보이게 하려면 어느 쪽을 쓰는가?

### 3. 소실점을 옮기면 (예측)

```css
.w { perspective: 300px; }          /* perspective-origin 을 바꿔 본다 */
.w b { width: 120px; height: 80px; transform: rotateY(50deg); }
```

- `perspective-origin` 을 안 적었을 때의 계산값은 무엇인가?
- `0 0` 과 `100% 100%` 를 줬을 때 상자의 rect 폭은 각각 어떻게 달라지는가?
- 폭이 몇 배까지 갈리는가?
- `perspective-origin` 은 부모에 쓰는가 자식에 쓰는가?

### 4. 손자는 정면을 볼 수 있는가 (예측)

```css
.scene { perspective: 400px; }
.mid   { transform: rotateY(45deg); }          /* preserve-3d 를 줄 때와 안 줄 때 */
.mid i { transform: rotateY(-45deg) translateZ(40px); }
```

- `transform-style` 을 안 줬을 때 손자의 rect 폭은 큰가 작은가?
- `preserve-3d` 를 줬을 때는 어떻게 되는가?
- 손자의 `rotateY(-45deg)` 는 `flat` 일 때 무엇을 하고 있는 것인가?
- `transform-style` 의 초기값은 무엇인가?

### 5. 무엇이 `preserve-3d` 를 깨뜨리는가 (경계)

- `overflow: hidden`·`overflow: auto`·`overflow-x: hidden` 중 깨뜨리는 것은 몇 개인가?
- `opacity: 0.99` 와 `opacity: 1` 중 깨뜨리는 것은 어느 쪽인가?
- `will-change: transform` 과 `will-change: opacity` 중 깨뜨리는 것은 어느 쪽이고, 그 이유를 한 문장으로 말할 수 있는가?
- `contain: paint` 는 깨뜨리는가?
- 깨뜨리는 선언들의 **공통점**을 한 문장으로 말할 수 있는가?
- 깨졌는지를 `getComputedStyle(el).transformStyle` 로 판정할 수 있는가?

### 6. 카드 뒤집기의 부품 (예측)

```css
.scene { perspective: 600px; }
.card  { transform-style: preserve-3d; }
.card:hover 시 transform: rotateY(180deg);
.card i { backface-visibility: hidden; }
.b      { transform: rotateY(180deg); }
```

- `.card` 에서 `transform-style: preserve-3d` 를 빼면 뒤집었을 때 무슨 색이 보이는가?
- `.card i` 에서 `backface-visibility: hidden` 을 빼면 무엇이 보이는가?
- `backface-visibility` 는 부모에 주는가 각 면에 주는가, 부모에 주면 어떻게 되는가?
- 뒷면(`.b`)에 미리 `rotateY(180deg)` 를 주는 이유는 무엇인가?

### 7. `z-index` 로 앞뒤를 바꿀 수 있는가 (경계)

```css
.sc   { perspective: 800px; transform-style: preserve-3d; }
.red  { transform: translateZ(0); }
.blue { transform: translateZ(-100px); z-index: 99; }
```

- 두 상자가 겹친 자리에는 무슨 색이 보이는가?
- `z-index: 99` 는 효과가 있는가?
- `.sc` 의 `transform-style` 을 `flat` 으로 바꾸면 어떻게 되는가?
- 3D 공간에서 앞뒤를 바꾸려면 무엇을 바꿔야 하는가?

### 8. 이 함수 목록은 왜 원근이 안 걸리는가 (경계)

```css
transform: rotateY(45deg) perspective(400px);
```

- 원근이 제대로 걸리는가?
- 왜 그런지 함수 적용 순서로 설명할 수 있는가, 그 정본은 어느 주제인가?
- 올바른 순서는 무엇인가?

### 9. 계산값을 믿으면 왜 틀리는가 (왜)

- 평탄화된 요소의 `getComputedStyle(el).transformStyle` 은 무엇을 돌려주는가?
- 그러면 평탄화 여부는 무엇으로 판정해야 하는가?
- 같은 구조의 함정이 [54번](../54-transform-2d-and-origin/2-summary.md)에도 있었다 — 무엇이었는가?
- 「계산값은 무엇을 말하고 무엇을 말하지 않는가」를 한 문장으로 말할 수 있는가?

### 10. 다른 주제와 잇기 (연결)

- `perspective` 를 준 요소에 딸려 오는 부작용 둘은 무엇이고, 각각의 정본은 어느 주제인가?
- 평탄화를 일으키는 선언 목록과 **쌓임 맥락을 만드는 선언 목록**은 얼마나 겹치는가?
- 안쪽을 잘라야 하는 3D 카드를 만들려면 어떻게 해야 하는가?
- 3D 연출에서 모션 접근성을 다루는 정본은 어느 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

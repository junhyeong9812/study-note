# css/syntax/39 — 사용자 선호와 다크 모드: `prefers-color-scheme`·`color-scheme` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — **무엇이 바뀌고 무엇이 안 바뀌는지를 픽셀 단위로 맞히는 것**이 인출이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 선호만 바꾸면 화면이 바뀌는가 (예측)

```html
<p>저자 CSS 가 한 글자도 없는 문서</p>
```

- 사용자 선호를 dark 로 바꾸고 이 문서를 띄우면 페이지 바탕은 무슨 색인가?
- `matchMedia("(prefers-color-scheme: dark)").matches` 는 무엇인가?
- 둘의 답이 갈리는 이유를 한 문장으로 말할 수 있는가?

### 2. `color-scheme` 이 바꾸는 것 (예측)

```html
<div class="light"><input value="x"><button>b</button></div>
<div class="dark"><input value="x"><button>b</button></div>
<style>
  .light { color-scheme: light }
  .dark  { color-scheme: dark }
</style>
```

- 두 `<input>` 의 `background-color` 는 각각 무엇인가?
- 두 `<button>` 의 `background-color` 는 각각 무엇인가?
- 이 블록에는 색 선언이 몇 개 있는가?
- `:root` 에 같은 선언을 걸면 추가로 무엇이 바뀌는가?

### 3. 서브트리에만 걸었을 때 안 바뀌는 것 (경계)

```html
<div class="dark"><p>글자</p></div>
<style> .dark { color-scheme: dark } </style>
```

- 이 `<p>` 의 `color` 는 무엇인가?
- `.dark` 의 `background-color` 는 무엇인가?
- 그 결과 화면은 어떤 어중간한 상태가 되는가?
- 왜 `color` 는 안 따라오는가?

### 4. `light-dark()` 는 무엇을 보는가 (예측)

```html
<p class="a">A</p>
<p class="b">B</p>
<style>
  .a { color: light-dark(#b91c1c, #15803d); }
  .b { color-scheme: light dark; color: light-dark(#b91c1c, #15803d); }
</style>
```

- 사용자 선호가 **dark** 일 때 두 문단은 각각 무슨 색인가?
- 사용자 선호가 **light** 일 때는?
- `light-dark()` 가 묻는 것을 명세 용어로 무엇이라 하는가?
- `color-scheme: only light` 를 걸면 선호가 dark 여도 어느 쪽이 나오는가?

### 5. 선호를 바꾸는 방법 (경계)

- `--force-dark-mode` 로 띄우면 `prefers-color-scheme: dark` 가 참이 되는가?
- 이 환경에서 실제로 선호를 바꾼 수단은 무엇이었는가?
- 그 수단에서 dark 에 해당하는 값은 0 인가 1 인가?
- 플래그를 던진 뒤 무엇을 읽어서 「먹었다」를 확인해야 하는가?

### 6. 둘 다 거짓인 상태 (경계)

- `prefers-color-scheme` 이 dark 도 light 도 아닌 상태가 있는가?
- 그 상태에서 `@media (prefers-color-scheme: light) { … }` 만 써 둔 페이지는 어떻게 보이는가?
- 그래서 기본값은 어디에 두어야 하는가?

### 7. 색을 뒤집으면 무엇이 깨지나 (예측)

```css
html { filter: invert(1) hue-rotate(180deg); }
```

- 페이지에 있는 사진은 어떻게 되는가?
- `box-shadow` 로 그린 그림자는 어떻게 되는가?
- 뒤집힌 그림자가 시각적으로 무엇으로 읽히는가?
- 대비비는 보존되는가?

### 8. 정석 배치 (왜)

- 다크 모드를 지원할 때 루트에 먼저 무엇을 선언하는가?
- 내가 칠한 색을 두 벌로 만드는 방법 두 가지는 무엇이고 각각 언제 쓰는가?
- 사용자가 직접 테마를 고르는 토글을 만들 때 **색 말고** 무엇을 같이 바꿔야 하는가?
- 첫 페인트에서 흰 화면이 번쩍이는 것을 막는 방법은 무엇인가?

### 9. 다른 선호 기능들 (연결)

- `prefers-reduced-motion`·`prefers-contrast`·`forced-colors` 는 각각 무엇을 뜻하는가?
- 그중 하나는 다른 둘과 성질이 다르다 — 무엇이 어떻게 다른가?
- `forced-colors` 모드에서 「빨간 테두리로 오류를 표시하는 UI」는 어떻게 되는가?
- 이 셋의 정본은 어느 주제인가?

### 10. 다른 주제와 잇기 (연결)

- `prefers-color-scheme` 은 38번의 어느 문법 규칙을 그대로 따르는가?
- `color-scheme` 이 바꾸는 층은 캐스케이드 출처 사다리의 어디인가?
- `color-scheme` 은 상속되는데 `color` 는 왜 안 따라오는가 — 03번의 어느 개념인가?
- 조상 요소의 테마를 자손이 읽어 스타일을 바꾸려면 40번의 무엇을 쓰는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

# css/syntax/40 — 컨테이너 쿼리와 스타일 쿼리 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — **무엇이 조회 대상이 되고 무엇이 안 되는지**를 맞히는 것이 인출이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 무엇이 조회 대상이 되는가 (예측)

```html
<div class="p1"><p class="c1">A</p></div>
<div class="p2"><p class="c2">B</p></div>
<div class="p3"><p class="c3">C</p></div>
<style>
  p { color: #000 }
  .p1 { width: 400px }
  .p2 { width: 400px; container-name: side }
  .p3 { width: 400px; container-type: inline-size }
  @container (min-width: 300px) { .c1, .c2, .c3 { color: #15803d } }
</style>
```

- 세 문단은 각각 무슨 색인가?
- `.p2` 의 `container-type` 계산값은 무엇인가?
- 규칙 자체는 `cssRules` 에 담겨 있는가?
- 이 실패는 07번의 어느 상태에 해당하는가?

### 2. `display` 가 자격을 바꾸는가 (예측)

```css
.k1 { container-type: inline-size; display: contents; width: 400px }
.k2 { container-type: inline-size; display: inline-block; width: 400px }
.k3 { container-type: inline-size; display: table; width: 400px }
```

- 셋 중 실제로 컨테이너가 되는 것은 무엇인가?
- 안 되는 것들의 `container-type` 계산값은 무엇인가?
- 그래서 진단할 때 무엇을 같이 읽어야 하는가?

### 3. 자기 자신은 조회할 수 있는가 (예측)

```html
<div class="self">나</div>
<style>
  .self { container-type: inline-size; width: 400px; color: #000 }
  @container (min-width: 300px) { .self { color: #b91c1c } }
</style>
```

- `.self` 는 무슨 색인가?
- 왜 명세가 이것을 금지했는가?
- 실무에서 이 제약을 어떻게 우회하는가?

### 4. 중첩 컨테이너 (예측)

```html
<div class="outer"><div class="inner"><p class="c6">x</p></div></div>
<style>
  .outer { container-type: inline-size; width: 900px }
  .inner { container-type: inline-size; width: 400px }
  @container (min-width: 300px) { .c6 { color: #15803d } }
  @container (min-width: 800px) { .c6 { background: #fecaca } }
</style>
```

- `.c6` 의 `color` 와 `background-color` 는 각각 무엇인가?
- 바깥 컨테이너가 900px 인데 왜 두 번째 규칙이 안 걸리는가?
- 바깥을 명시적으로 조회하려면 무엇을 해야 하는가?

### 5. `size` 의 대가 (예측)

```html
<div class="a"><div class="kid">36px 짜리 자손</div></div>
<div class="b"><div class="kid">36px 짜리 자손</div></div>
<style>
  .a { width: 400px }
  .b { width: 400px; container-type: size }
</style>
```

- 두 상자의 `height` 는 각각 얼마인가?
- `.b` 의 `scrollHeight` 는 얼마인가?
- 왜 `size` 에만 이 억제가 붙고 `inline-size` 에는 안 붙는가?
- `@container (min-height: 10px)` 를 `.b` 에 대고 쓰면 참인가 거짓인가?

### 6. 스타일 쿼리의 규칙 (예측)

```html
<div class="t1"><p class="s1">A</p></div>
<div class="t2"><p class="s2">B</p></div>
<div class="t3"><p class="s3">C</p></div>
<style>
  p { color: #000 }
  .t1 { container-type: inline-size; --theme: dark }
  .t2 { --theme: dark }
  .t3 { container-type: inline-size; --theme: DARK }
  @container style(--theme: dark) { .s1, .s2, .s3 { color: #15803d } }
</style>
```

- 세 문단은 각각 무슨 색인가?
- 스타일 쿼리와 크기 쿼리가 갈리는 규칙은 정확히 무엇 하나인가?
- 왜 그 하나만 다른가?

### 7. 스타일 쿼리로 보통 속성을 물을 수 있는가 (경계)

```css
.a1 { container-type: inline-size; width: 400px; color: red }
@container style(color: red) { .x1 { color: #1d4ed8 } }
```

- `.a1` 안의 `.x1` 은 무슨 색인가?
- 그 규칙은 `cssRules` 에 담겨 있는가? `containerQuery` 로 무엇이 읽히는가?
- 이것은 명세의 한계인가 구현의 한계인가?
- 실무에서는 무엇으로 대신하는가?

### 8. 스타일 쿼리의 다른 형태들 (경계)

- `@container style(--theme)` 처럼 값을 빼면 무엇을 묻는 것인가?
- `not style(...)` 과 `(min-width: 300px) and style(...)` 은 쓸 수 있는가?
- 등록한 커스텀 속성(`@property`)도 조회되는가?
- 자기 자신에게 스타일 쿼리를 걸면 어떻게 되는가?

### 9. 뷰포트와 무관한가 (예측)

- 같은 문서를 뷰포트 500px · 780px · 1400px 에서 띄우면 컨테이너 쿼리 결과가 달라지는가?
- 컨테이너의 폭이 `%` 로 정해져 있으면 그 답이 달라지는가?
- 미디어 쿼리와 컨테이너 쿼리를 한 페이지에서 같이 쓸 수 있는가?

### 10. 다른 주제와 잇기 (연결)

- `@container` 의 조건 문법은 어느 주제의 문법을 그대로 쓰는가?
- 구형 브라우저에서 `@container { … }` 안의 스타일은 어떻게 되는가 — 07번의 어느 규칙인가?
- `cqw`·`cqi` 단위의 정본은 어느 주제인가?
- `CSS.supports('at-rule(@container)')` 는 무엇을 돌려주는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

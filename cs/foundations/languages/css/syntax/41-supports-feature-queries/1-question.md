# css/syntax/41 — `@supports` 기능 질의 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — **질의 결과와 실제 동작이 갈리는 자리**를 맞히는 것이 인출이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 진단 도구가 거짓말하는 자리 (예측)

```html
<a class="f14"><span>무슨 색?</span></a>
<p class="f7">무슨 색?</p>
<style>
  p, span { color: #000 }
  :is(.f14, ::zzbogus) span { color: #1d4ed8 }
  @supports selector(:is(.a, ::zzbogus)) { .f7 { color: #b91c1c } }
</style>
```

- `CSS.supports('selector(:is(.a, ::zzbogus))')` 는 무엇을 돌려주는가?
- `.f14 span` 과 `.f7` 은 각각 무슨 색인가?
- 시트에 담긴 첫 규칙의 `selectorText` 는 무엇인가?
- 왜 질의와 실제 동작이 갈리는가 — 명세가 정한 이유는 무엇인가?

### 2. `:where()`·`:not()` 도 같은가 (경계)

- `CSS.supports('selector(:where(.a, ::zzbogus))')` 는 무엇인가?
- `CSS.supports('selector(:not(.a, ::zzbogus))')` 는 무엇인가?
- 「매칭에서 관대한 것」과 「질의에서 관대한 것」의 짝은 같은가?
- 그래서 진단은 무엇으로 해야 하는가?

### 3. 언제 `@supports` 가 필요한가 (예측)

```html
<p class="g1">A</p>
<div class="g2"><i>x</i><i>y</i></div>
<div class="g3"><i>x</i><i>y</i></div>
<style>
  .g1 { color: #15803d; color: zzbogus(1); }

  .g2 { display: flex; gap: 8px }
  .g2 { display: zzgrid; grid-template-columns: 1fr 1fr }

  @supports (display: zzgrid) { .g3 { display: zzgrid; grid-template-columns: 1fr 1fr } }
  .g3 { display: flex; gap: 8px }
</style>
```

- `.g1` 은 무슨 색인가? `@supports` 가 필요한가?
- `.g2` 의 `display` 와 `grid-template-columns` 는 각각 무엇인가?
- `.g3` 의 같은 두 값은 무엇인가?
- 둘의 차이를 만든 것은 무엇인가?

### 4. 폴백을 어디에 두는가 (왜)

- `@supports not (display: grid) { .x { display: flex } }` 로 폴백을 쓰면 어떤 브라우저에서 깨지는가?
- 왜 깨지는가 — 07번의 어느 규칙인가?
- 안전한 배치는 무엇인가?

### 5. 항상 참인 조건 (예측)

```css
@supports (--x: anything)     { .a { color: #15803d } }
@supports (color: var(--x))   { .b { color: #15803d } }
@supports (foo)               { .c { color: #15803d } }
@supports (zz-prop: 1)        { .d { color: #15803d } }
```

- 네 블록 중 적용되는 것은 무엇인가?
- 참이 되는 것들이 참인 이유는 무엇인가?
- 그래서 「커스텀 속성을 지원하나」를 `@supports` 로 물을 수 있는가?
- 못 묻는다면 타입을 고정하는 수단은 무엇인가?

### 6. 프렐류드가 무효하면 (예측)

```css
@supports zzz nonsense { .g4 { color: #b91c1c } }
.g5 { color: #15803d }
```

- `.g4` 와 `.g5` 는 각각 무슨 색인가?
- 그 `@supports` 는 `cssRules` 에 있는가?
- 회복 지점은 어디인가?

### 7. 명시도와 순서 (예측)

```html
<p class="h1" id="hid1">A</p>
<p class="h2">B</p>
<p class="h3">C</p>
<style>
  #hid1 { color: #1d4ed8 }
  @supports (display: grid) { .h1 { color: #b91c1c } }

  @supports (display: grid) { .h2 { color: #b91c1c } }
  .h2 { color: #1d4ed8 }

  .h3 { color: #1d4ed8 }
  @supports (display: grid) { .h3 { color: #b91c1c } }
</style>
```

- 세 문단은 각각 무슨 색인가?
- `@supports` 는 캐스케이드의 무엇을 바꾸는가?
- 그래서 폴백과 향상 중 어느 쪽을 먼저 써야 하는가?

### 8. 다섯 형태 (경계)

- `@supports` 가 물을 수 있는 다섯 형태는 각각 무엇인가?
- `CSS.supports` 의 두 호출 형태는 무엇이 다른가?
- `CSS.supports('bogus)(')` 는 예외를 던지는가?
- `at-rule(@container)` 질의는 이 브라우저에서 되는가? Baseline 은 무엇인가?

### 9. 웹폰트 (경계)

- `font-format()` 과 `font-tech()` 는 각각 무엇을 묻는가?
- `@font-face` 의 `src` 목록은 `@supports` 없이도 폴백이 되는가?
- 모르는 `format()` 이 붙은 항목은 네트워크 요청이 나가는가?
- `font-tech(color-COLRv1)` 이 참인 것과 COLRv1 의 Baseline 은 같은 이야기인가?

### 10. 다른 주제와 잇기 (연결)

- 「모르는 선언은 그 줄만 버려진다」와 「`@supports` 로 가른다」는 각각 어느 단위를 다루는가?
- 조건이 거짓인 `@supports` 는 `cssRules` 에 남는가 — 38번의 무엇과 같은가?
- `@media`·`@container`·`@supports` 는 각각 무엇을 기준으로 조건을 평가하는가?
- 규칙 안에 `@supports` 를 중첩하면 파서가 무엇을 덧붙이는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

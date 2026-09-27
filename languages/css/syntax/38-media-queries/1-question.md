# css/syntax/38 — 미디어 쿼리: 문법·범위 구문·논리 연산 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — **뷰포트 폭을 주고 참/거짓을 맞히는 것**이 인출이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 경계는 어느 쪽에 포함되는가 (예측)

```html
<p class="a">A</p><p class="b">B</p><p class="c">C</p>
<style>
  p { background: #e2e8f0 }
  @media (max-width: 600px) { .a, .c { background: #fecaca } }
  @media (min-width: 600px) { .b, .c { background: #bfdbfe } }
</style>
```

- 뷰포트가 **599px** 일 때 세 문단의 배경은 각각 무엇인가?
- 뷰포트가 **600px** 일 때는?
- 뷰포트가 **601px** 일 때는?
- 600px 에서 `.c` 의 승자를 정한 것은 캐스케이드의 몇 단계인가?

### 2. 겹침을 없애는 방법 (왜)

- 중단점을 `max-width: 599px` / `min-width: 600px` 으로 잡으면 겹침이 사라지는가?
- 그 방법이 확대·고DPI 환경에서 남기는 틈은 무엇인가?
- 오늘 권장되는 정공법은 무엇이고, 왜 옛 표기로는 그것을 못 하는가?

### 3. 모르는 기능을 만나면 (예측)

```html
<p class="a1">A1</p><p class="a2">A2</p>
<style>
  p { color: #000 }
  @media (totally-unknown-zz: 1) { .a1 { color: #b91c1c } }
  @media (min-width: bogus)      { .a2 { color: #b91c1c } }
</style>
```

- 두 문단은 무슨 색인가?
- `document.styleSheets[0].cssRules.length` 는 몇인가?
- 두 규칙의 `conditionText` 에는 무엇이 들어 있는가?
- 이것은 07번의 「모르는 at-rule」과 같은 이야기인가 다른 이야기인가?

### 4. `not` 의 결합 범위 (예측)

```css
@media not all and (min-width: 1px) { .a3 { color: #b91c1c } }
@media not (min-width: 99999px)     { .c3 { color: #15803d } }
```

- 뷰포트 800px 에서 `.a3` 과 `.c3` 은 각각 무슨 색인가?
- `not all and (min-width: 1px)` 을 괄호로 풀어 쓰면 어떤 모양인가?
- 모르는 미디어 기능을 `not` 으로 감쌌을 때 왜 위험한가?

### 5. 쉼표와 `or` (경계)

- `@media (a), (b)` 와 `@media ((a) or (b))` 의 차이는 무엇인가?
- 최상위에 `or` 키워드를 쓸 수 있는가?
- `@media zzunknown, (min-width: 1px)` 은 뷰포트 800px 에서 적용되는가?
- 그 성질은 선택자의 무엇과 닮았는가?

### 6. 미디어 타입 (예측)

- `@media tv and (min-width: 1px)` 은 오늘 화면에서 적용되는가?
- `@media { .x { … } }` 처럼 조건을 아예 비우면 어떻게 되는가?
- `only screen` 의 `only` 는 평가에 영향을 주는가?
- 타입을 안 쓰면 무엇으로 취급되는가?

### 7. 미디어 쿼리는 무엇을 바꾸는가 (예측)

```html
<p class="a11" id="id-a11">무슨 색?</p>
<style>
  #id-a11 { color: #1d4ed8 }
  @media (min-width: 1px) { .a11 { color: #b91c1c } }
</style>
```

- 뷰포트 800px 에서 이 문단은 무슨 색인가?
- 미디어 쿼리는 캐스케이드 6단계 중 어디에 작용하는가?
- 명시도가 같은 두 규칙이 하나는 `@media` 안, 하나는 밖에 있으면 무엇이 승자를 정하는가?
- 「모바일 우선으로 `min-width` 를 오름차순으로 쓴다」는 관례가 이 규칙에서 어떻게 나오는가?

### 8. 범위 구문의 대응 (경계)

- `(min-width: 400px) and (max-width: 700px)` 을 범위 구문 한 줄로 쓰면?
- `(600px <= width)` 는 `(width >= 600px)` 과 같은가?
- 범위 구문에만 있고 옛 표기에는 없는 연산자는 무엇인가?
- `(width >= calc(100px + 100px))` 를 담아 `mediaText` 로 읽으면 무엇이 나오는가?

### 9. 중첩과 `@import` (경계)

- `@media` 안에 `@media` 를 넣으면 두 조건은 어떻게 합쳐지는가?
- 규칙 안에 `@media` 를 넣으면 파서가 무엇을 덧붙이는가?
- `@media (min-width: 1px) { @import url("a.css"); }` 는 어떻게 되는가?
- `<link media="print">` 로 건 시트는 화면에서 내려받는가?

### 10. 다른 주제와 잇기 (연결)

- 미디어 쿼리와 컨테이너 쿼리는 각각 무엇을 기준으로 조건을 평가하는가?
- 「브라우저가 이 문법을 아는가」를 묻고 싶으면 무엇을 쓰는가?
- 조건이 거짓인 `@media` 를 진단할 때 「진단 3창」에 무엇을 더해야 하는가?
- 헤드리스에서 잰 `(hover: hover)` 값을 사람의 브라우저 값으로 옮겨 적으면 왜 틀리는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

# css/syntax/03 — 상속: 상속되는 속성과 `inherit`/`initial`/`unset`/`revert`/`revert-layer` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **무엇이 남는지 맞힐 수 있는지**를 묻는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 이 자식은 무슨 색인가 (예측)

```html
<div class="parent"><p class="child">무슨 색?</p></div>
<style>
  .parent { color: #b91c1c; }
  p       { color: #15803d; }
</style>
```

- 이 문단의 `color` 는 무엇이 되는가?
- `p` 선언의 명시도가 `(0,0,1)` 로 가장 약한데도 이기는 이유는 무엇인가?
- 「상속이 선언보다 약하다」는 설명은 왜 틀린 표현인가?
- `p` 선언을 지우면 무슨 색이 되는가?

### 2. 상속처럼 보이는데 상속이 아닌 것 (예측)

```html
<div id="par"><p id="kid">자식</p></div>
<style>
  #par { color: #b91c1c; border: 4px solid #1d4ed8; width: 300px; text-decoration: underline; }
</style>
```

- `#kid` 의 `border-top-color` 는 무엇인가? 그 값이 상속의 증거가 **아닌** 이유는?
- `#kid` 의 `width` 가 `300px` 로 나오는 것은 상속인가?
- `#kid` 의 `text-decoration-line` 은 무엇인가? 화면에는 밑줄이 보이는데 왜 그 값인가?
- `opacity: 0.5` 를 부모에 주면 자식의 `opacity` 계산값은 얼마인가?

### 3. 네 키워드를 한 줄씩 말하라 (경계)

- `inherit` · `initial` · `unset` · `revert` 가 각각 **무엇으로** 되돌리는가?
- `unset` 이 상속되는 속성과 아닌 속성에서 각각 무엇이 되는가?
- 이 넷 중 **브라우저 기본 스타일**로 돌아가는 것은 어느 것인가?
- `revert` 와 `revert-layer` 의 **단위**는 각각 무엇인가?

### 4. `revert` 와 `initial` 이 갈리는 자리 (예측)

```html
<div id="d1">A</div><div id="d2">B</div>
<strong id="g1">C</strong><strong id="g2">D</strong>
<style>
  #d1 { display: revert; }      #d2 { display: initial; }
  #g1 { font-weight: revert; }  #g2 { font-weight: initial; }
</style>
```

- 네 요소의 `display`·`font-weight` 계산값을 각각 예측하라.
- `div` 에 `display: initial` 을 주면 왜 `block` 이 아닌가?
- `li { display: initial }` 을 주면 화면에서 무엇이 사라지는가?
- 이 둘이 **같은 값을 내는** 속성은 어떤 조건을 만족하는 속성인가?

### 5. 버튼 셋 중 어느 것이 버튼처럼 보이나 (예측)

```html
<div class="bar">
  <button class="p">기본</button>
  <button class="u">all: unset</button>
  <button class="r">all: revert</button>
</div>
<style>
  .bar { color: #b91c1c; font-family: Georgia, serif; font-size: 18px; }
  .u { all: unset; }
  .r { all: revert; }
</style>
```

- 셋 중 회색 테두리 버튼으로 보이는 것은 어느 것인가?
- `all: unset` 을 건 버튼의 `color` 와 `font-family` 는 무엇이 되는가?
- `all: unset` 을 `all: initial` 로 바꾸면 무엇이 더 달라지는가?
- 서드파티 위젯의 내 스타일만 걷어내려 할 때 셋 중 무엇을 골라야 하는가?

### 6. 상속되지 않는 속성에 `inherit` 을 쓰면 (경계)

```html
<div class="box"><p class="t">테두리 색은?</p></div>
<style>
  .box { border: 4px solid #1d4ed8; color: #b91c1c; }
  .t   { border: 4px solid #15803d; border-color: inherit; }
</style>
```

- `.t` 의 `border-top-color` 는 무엇인가?
- `border-color` 는 상속되지 않는 속성인데 `inherit` 이 유효한 이유는 무엇인가?
- 같은 자리에 `unset` 을 쓰면 무엇이 되는가? `initial` 이면?
- 이 셋의 결과가 갈리는 이유를 `currentColor` 로 설명할 수 있는가?

### 7. `revert-layer` 는 무엇을 지우는가 (예측)

```html
<p class="r1">1</p><p class="r2">2</p>
<style>
  @layer base, theme;
  @layer base  { .r1 { color: #b91c1c; } }
  @layer theme { .r1 { color: revert-layer; } }

  @layer base  { .r2 { color: #b91c1c; } }
  @layer base  { .r2 { color: revert-layer; } }
</style>
```

- 두 문단의 색을 각각 예측하라.
- `.r2` 가 `.r1` 과 다른 결과를 내는 이유는 무엇인가?
- 레이어에 들어 있지 않은 규칙에서 `revert-layer` 를 쓰면 무엇과 같아지는가?
- 다크 테마 레이어만 무르고 싶을 때 `initial` 대신 이것을 쓰는 이유는 무엇인가?

### 8. 이 선언들은 살아남는가 (경계)

```css
.x { margin: 10px inherit; padding: 4px; }
.y { color: initial red; background-color: gold; }
.z { all: red; }
```

- 세 규칙에서 **실제로 적용되는 선언**은 각각 무엇인가?
- 무효한 선언이 버려질 때 에러가 나는가, 콘솔에 무엇이 찍히는가?
- 「버려졌다」를 눈이 아니라 **값으로** 확인하려면 무엇을 읽어야 하는가?
- 전역 키워드를 값의 **일부**로 못 쓰는 규칙을 한 줄로 말할 수 있는가?

### 9. 전역 선택자가 상속에 하는 일 (왜)

```css
* { font-family: "DejaVu Sans", sans-serif; }
.card { font-family: Georgia, serif; }
```

- `.card` 안에 있는 `<p>` 의 `font-family` 는 무엇이 되는가?
- 상속되는 속성을 `*` 로 선언하면 그 속성의 상속에 무슨 일이 일어나는가?
- `* { box-sizing: border-box }` 는 왜 같은 문제를 일으키지 않는가?
- 상속의 출발점을 `*` 가 아니라 `:root` 나 `body` 에 거는 이유는 무엇인가?

### 10. 다른 주제와 잇기 (연결)

- 부모가 `font-size: 20px; letter-spacing: 0.1em` 이고 자식이 `font-size: 10px` 일 때 자식의 `letter-spacing` 은 얼마인가?
- 그 답이 「자식이 물려받는 것은 부모의 계산값이다」와 어떻게 이어지는가?
- `display: contents` 로 상자를 없앤 요소는 상속을 끊는가?
- 커스텀 속성(`--brand`)이 이 주제의 상속 규칙에서 예외인 점은 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

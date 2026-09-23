# css/syntax/13 — 의사 요소와 생성 콘텐츠: `::before`/`::after`/`::marker`/`::selection` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 「상자가 생기나」·「그 자리에 쓸 수 있나」·「그 속성이 먹나」 셋이 과녁이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 막대가 몇 개 보이는가 (예측)

```html
<span id="a">A</span>
<span id="b">A</span>
<style>
  span::before { width: 50px; height: 10px; display: inline-block; background: blue; }
  #b::before   { content: ""; }
</style>
```

- 파란 막대는 몇 개 보이는가?
- `getComputedStyle(a, '::before').width` 는 무엇을 돌려주는가?
- 그 값이 「상자가 있다」의 근거가 되는가, 안 되는가?
- 상자가 실제로 생겼는지는 무엇으로 판정하는가?

### 2. 이 넷의 결과는 같은가 다른가 (예측)

```css
.a::before { }                    /* content 선언 없음 */
.b::before { content: ""; }
.c::before { content: none; }
.d::before { content: normal; }
```

- 넷 중 상자가 생기는 것은 몇 개이고 어느 것인가?
- `content` 를 아예 안 쓴 것과 `normal` 을 쓴 것의 계산값은 무엇인가?
- `""` 와 `none` 은 왜 다르게 동작하는가?
- 네 경우를 화면만 보고 구분할 수 있는가?

### 3. `content` 의 값이 계산값에 어떻게 남는가 (예측)

```css
#p2::before { content: attr(data-tag); }        /* data-tag="NEW" */
#p6::before { content: "★" / "별표"; }
#li::before { content: "[" counter(item) "] "; }
```

- 셋의 `getComputedStyle(el, '::before').content` 는 각각 무엇인가?
- `attr()` 과 `counter()` 중 계산값에서 **이미 풀려 있는** 것은 어느 쪽인가, 왜인가?
- `/ "별표"` 부분은 계산값에 남는가?
- `getComputedStyle(el)` 처럼 두 번째 인자를 빼면 `content` 는 무엇이 되는가?

### 4. 이 다섯 줄 중 살아남는 것은 (예측)

```css
div::before span  { color: red; }
p::before.cls     { color: red; }
p::before::after  { color: red; }
p::before:hover   { color: red; }
:is(p::before)    { color: red; }
```

- `cssRules` 에 담기는 것은 몇 줄인가?
- 마지막 줄의 `selectorText` 를 읽으면 무엇이 나오는가?
- 네 번째 줄에 대해 **명세**와 **Chrome 151** 은 각각 뭐라고 하는가?
- 의사 요소는 복합 선택자의 어디에만 올 수 있는가?

### 5. 어느 쪽이 이기는가 (예측)

```html
<div><section><p class="c1">본문</p></section></div>
<style>
  p.c1::before      { content: "A"; color: green; }
  section p::before { content: "A"; color: red; }
</style>
```

- 두 선택자의 `(A, B, C)` 를 각각 계산할 수 있는가?
- 글자는 무슨 색인가?
- 두 규칙의 순서를 바꾸면 결과가 바뀌는가?
- 의사 요소와 의사 클래스는 명시도의 같은 자리에 들어가는가?

### 6. 콜론 하나와 둘 (경계)

- `p:before` 와 `p::before` 는 고르는 것이 같은가, 명시도가 같은가?
- `selectorText` 를 읽으면 `p:before` 는 무엇으로 나오는가?
- 콜론 하나로 쓸 수 있는 의사 요소는 몇 개이고 어느 것들인가?
- `p:marker` 라고 쓰면 어떻게 되는가?

### 7. 선언은 있는데 안 먹는다 (예측)

```css
li::marker { color: red; font-size: 28px; content: "◆ ";
             background: blue; padding: 40px; border: 5px solid lime; }
```

- 이 규칙은 `cssRules` 에 담기는가?
- `cssRules[0].cssText` 에 `background` 선언이 남아 있는가?
- 여섯 선언 중 실제로 효과가 나는 것은 어느 것들인가?
- 「선택자가 버려진 것」과 「속성이 안 먹는 것」은 무엇으로 구분하는가?

### 8. 같은 선언에 다르게 답한다 (예측)

```css
p::first-line   { margin-left: 30px; padding-left: 30px; border-left: 4px solid red; background: yellow; }
p::first-letter { margin-left: 30px; padding-left: 30px; border-left: 4px solid red; background: yellow; }
```

- 두 의사 요소의 계산된 `margin-left` 는 각각 얼마인가?
- 둘 다 받는 속성은 무엇인가?
- `::first-line` 이 여백·테두리를 안 받는 이유를 한 문장으로 설명할 수 있는가?
- 하이라이트 의사 요소(`::selection`)는 이 둘보다 넓은가 좁은가?

### 9. 상태가 필요한 것들은 어떻게 확인하는가 (경계)

- `getComputedStyle(p, '::selection')` 은 선택 전과 후에 다른 값을 주는가?
- `input.value` 를 채웠을 때 `::placeholder` 의 계산값은 바뀌는가?
- `dialog.showModal()` 을 부르기 **전에** `::backdrop` 의 계산값을 읽으면 무엇이 나오는가?
- 그렇다면 「지금 실제로 칠해져 있나」는 무엇으로 확인하는가?

### 10. 생성 콘텐츠는 읽히는가 (예측)

```css
#a::before { content: "필수 "; }
#b::before { content: "★" / "별표"; }
#e::before { content: "장식" / ""; }
```

- 셋 중 접근성 트리에 텍스트 노드가 생기는 것은 몇 개인가?
- `#b` 에서 트리에 오르는 문자열은 `★` 인가 `별표` 인가?
- 「CSS 로 넣은 것은 보조기기가 무시한다」는 말은 맞는가?
- 순수 장식용 아이콘은 어떻게 써야 하는가?

### 11. 왜 그렇게 정해졌나 (왜)

- `::before` 의 존재가 CSS 선언에 달려 있다는 사실이 `:has()` 에 어떤 제약을 만드는가?
- `::first-line` 에 여백을 허용하면 무슨 순환이 생기는가?
- 명세가 하이라이트 의사 요소의 속성을 좁게 제한한 이유로 드는 것은 무엇인가?
- 콜론 하나짜리 표기를 없애지 않고 남겨 둔 이유는 무엇인가?

### 12. 다른 주제와 잇기 (연결)

- 의사 요소를 `:is()` 안에 넣었을 때 규칙이 살아남는 이유는 무엇인가?
- 「조건에 따라 `::before` 를 바꾸고 싶다」면 `:has()` 를 어디에 거는가?
- `::marker` 에 배경과 여백이 꼭 필요하면 무엇으로 대신하는가?
- Baseline 이 `limited` 라는 것만 보고 「쓰면 안 된다」고 판단해도 되는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

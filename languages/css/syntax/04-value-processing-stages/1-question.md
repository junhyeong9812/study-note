# css/syntax/04 — 값 처리 단계: 지정값·계산값·사용값·실제값 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 계산이 화면에 안 보이므로 **값을 맞히는 것**이 인출이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `width: 50%` 하나를 네 단계로 관통시켜라 (예측)

```html
<div id="wrap" style="width:400px">
  <p id="half" style="width:50%">…</p>
</div>
```

- `#half` 의 `width` 는 지정값·계산값·사용값·실제값에서 각각 무엇인가?
- `%` 가 계산값 단계에서 아직 `%` 인 이유는 무엇인가?
- 이 네 단계 중 **레이아웃이 끼어드는 자리**는 어디와 어디 사이인가?
- `getComputedStyle(half).width` 는 무엇을 돌려주는가?

### 2. 같은 코드가 다른 값을 돌려준다 (예측)

```html
<p id="a" style="width:50%">보인다</p>
<p id="b" style="width:50%; display:none">안 보인다</p>
```

- `getComputedStyle(a).width` 와 `getComputedStyle(b).width` 는 각각 무엇인가?
- 두 값이 갈리는 **조건**을 한 문장으로 말하라.
- `width` 대신 `color`·`letter-spacing` 을 읽으면 같은 현상이 일어나는가?
- 이 차이가 `parseFloat` 를 쓰는 코드에서 어떤 버그로 나타나는가?

### 3. `getComputedStyle` 은 어느 단계를 보여 주는가 (경계)

- 이 함수가 돌려주는 값의 **정식 이름**은 무엇인가?
- 사용값을 돌려주는 속성 무리와 계산값을 돌려주는 속성 무리를 각각 셋씩 들라.
- 그 갈림의 기준을 한 문장으로 말할 수 있는가?
- 이 함수를 반복 호출하는 것이 비싼 경우는 언제이고 왜인가?

### 4. `em` 은 어디서 픽셀이 되는가 (예측)

```html
<div id="parent"><p id="child">…</p></div>
<style>
  #parent { font-size: 20px; text-indent: 2em; letter-spacing: 0.1em; line-height: 1.5; }
  #child  { font-size: 10px; }
</style>
```

- `#child` 의 `text-indent`·`letter-spacing`·`line-height` 를 각각 예측하라.
- 셋 중 하나만 자식에서 다시 계산되는데, 그것이 무엇이고 왜인가?
- 「자식이 부모의 `em` 을 다시 계산하지 않는다」를 위 값으로 증명하라.
- `line-height` 를 `1.5em` 으로 바꾸면 자식 값은 얼마가 되는가?

### 5. 중첩된 `em` 은 어떻게 되는가 (예측)

```html
<ul class="em"><li>1단계<ul><li>2단계<ul><li>3단계</li></ul></li></ul></li></ul>
<style>
  .em, .em ul { font-size: 1.5em; }
</style>
```

- 루트 글꼴이 `16px` 일 때 세 단계의 `font-size` 를 각각 예측하라.
- `font-size: 1.5em` 은 왜 곱해지는데 `letter-spacing: 0.4em` 은 안 곱해지는가?
- `1.5em` 을 `1.5rem` 으로 바꾸면 세 값은 어떻게 되는가?
- 컴포넌트 안 여백에 `em` 을 쓰는 것과 `rem` 을 쓰는 것의 대가는 각각 무엇인가?

### 6. 이 세 창구는 같은 것을 묻는가 (경계)

```js
getComputedStyle(el).width
el.getBoundingClientRect().width
el.offsetWidth
```

- `width: 200px; padding: 15px; border: 5px` 인 요소에서 셋은 각각 무엇을 돌려주는가?
- `box-sizing: border-box` 로 바꾸면 무엇이 달라지는가?
- `transform: scale(2)` 를 걸면 셋 중 어느 것이 두 배가 되는가?
- 레이아웃 계산에 `offsetWidth` 를 쓰면 안 되는 이유는 무엇인가?

### 7. 실제값이 보이는 자리 (예측)

```css
#frac { width: 100.6px; }
.third { width: 33.333%; }   /* 부모 333px */
```

- 렌더된 `#frac` 의 `getComputedStyle().width` 와 `getBoundingClientRect().width` 는 각각 무엇인가?
- 같은 요소를 `display: none` 으로 만들어 읽으면 무엇이 나오는가? 왜 달라지는가?
- `.third` 셋을 더하면 부모 폭 `333px` 이 되는가?
- 이 수치가 「명세가 보장하는 것」인가 「이 브라우저의 구현 세부」인가?

### 8. 세로 마진의 `%` 는 무엇의 비율인가 (예측)

```css
#wrap { width: 400px; }         /* 높이는 auto */
#box  { margin: 10%; }
```

- `#box` 의 `margin-top` 과 `margin-left` 는 각각 얼마인가?
- 상하 마진의 `%` 가 높이가 아니라 폭을 기준으로 삼는 이유는 무엇인가?
- 이 규칙이 네 단계 중 어느 단계의 일인가?
- 「`padding-top: 56.25%` 로 16:9 비율 상자 만들기」 관행이 왜 성립하는지 같은 규칙으로 설명할 수 있는가?

### 9. `transform` 을 숨겨진 요소에서 읽으면 (예측)

```html
<div id="t" style="width:200px; transform:translateX(50%); display:none"></div>
```

- `getComputedStyle(t).transform` 은 무엇을 돌려주는가?
- `display: none` 을 `visibility: hidden` 으로 바꾸면 무엇이 나오는가?
- 이 값이 사용값인지 계산값인지 판별하고 그 근거를 말하라.
- 애니메이션 시작 전에 요소를 숨겨 두고 현재 변환을 읽는 코드는 어디서 깨지는가?

### 10. 다른 주제와 잇기 (연결)

- 자식이 물려받는 것은 네 단계 중 어느 판이고, 왜 나머지 셋은 아닌가?
- `width: auto` 가 전환(`transition`)되지 않는 이유를 이 주제의 용어로 설명할 수 있는가?
- `getComputedStyle` 이 `line-height: 1.5` 에 `"30px"` 을 돌려주는데도 「계산값은 숫자 1.5」라고 말할 수 있는 근거는 무엇인가?
- 무효한 값(`width: 10`)은 이 네 단계 중 어디에서 걸러지는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

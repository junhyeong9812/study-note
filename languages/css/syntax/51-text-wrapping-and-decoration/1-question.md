# css/syntax/51 — 텍스트 줄바꿈·서식·장식: `word-break`·`overflow-wrap`·`text-wrap`·`text-decoration` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**이고, 답은 거의 전부 **줄 수**다 —
> 「되나 안 되나」가 아니라 「**몇 줄이 되나 · 어디서 끊기나**」를 묻는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 이 셋은 각각 몇 줄이 되는가 (예측)

```css
.b    { width: 240px; font: 16px/24px sans-serif; }
.all  { word-break: break-all; }
.word { overflow-wrap: break-word; }
```

```html
<div class="b">The ThisIsAnExtremelyLongUnbreakableToken ends.</div>
<div class="b all">The ThisIsAnExtremelyLongUnbreakableToken ends.</div>
<div class="b word">The ThisIsAnExtremelyLongUnbreakableToken ends.</div>
```

- 셋의 줄 수는 각각 몇인가?
- 어느 것이 상자를 뚫는가?
- `break-all` 과 `break-word` 는 줄 수가 같은가, 다른가? 왜인가?
- 첫 줄에 `The` 만 남는 것은 어느 쪽인가?

### 2. `min-content` 상자의 폭은 얼마가 되는가 (예측)

```css
span { display: inline-block; width: min-content; font: 16px/24px sans-serif; }
.bw  { overflow-wrap: break-word; }
.aw  { overflow-wrap: anywhere; }
```

```html
<span class="bw">Hydroelectric plant</span>
<span class="aw">Hydroelectric plant</span>
```

- 두 상자의 폭은 같은가?
- `break-word` 쪽은 `overflow-wrap` 을 아예 안 쓴 것과 같은가?
- `anywhere` 쪽 상자의 폭은 무엇으로 정해지는가?
- flex 아이템에 `anywhere` 를 걸면 어떤 일이 생기는가?

### 3. 한국어에서 셋은 어떻게 갈리는가 (예측)

```css
.k { width: 110px; font: 16px/24px sans-serif; }
```

```html
<div class="k">줄바꿈기회는 브라우저가 스스로 정하는 것이다</div>          <!-- 기본 -->
<div class="k" style="word-break: break-all">같은 문장</div>
<div class="k" style="word-break: keep-all">같은 문장</div>
```

- 셋의 줄 수는 각각 몇인가?
- `기본` 과 `break-all` 은 다른가?
- `keep-all` 이 줄을 더 쓰는가 덜 쓰는가?
- 상자를 190px 로 넓히면 셋의 관계가 어떻게 바뀌는가?

### 4. `hyphens` 세 값은 어떻게 갈리는가 (예측)

```html
<div style="width:100px; hyphens:none">extra&shy;ordi&shy;narily compli&shy;cated</div>
<div style="width:100px; hyphens:manual">같은 텍스트</div>
<div style="width:100px; hyphens:auto">같은 텍스트</div>
<div style="width:100px; hyphens:auto" lang="en-US">extraordinarily complicated</div>
```

- 앞의 셋은 각각 몇 줄인가?
- 소프트 하이픈이 없는 넷째는 몇 줄인가?
- `lang` 을 `de` 로 바꾸면 달라지는가?
- 여기서 「잴 수 있었던 것」과 「못 잰 것」은 각각 무엇인가?

### 5. `text-wrap: balance` 는 언제 아무 일도 안 하는가 (예측)

```css
div { width: 260px; font: 16px/24px sans-serif; text-wrap: balance; }
```

- 4줄짜리 문단에서 `balance` 는 무엇을 바꾸는가?
- 10줄짜리 문단에서는?
- 경계는 몇 줄인가?
- 그 숫자는 명세가 정한 것인가?

### 6. `text-overflow: ellipsis` 는 언제 찍히는가 (예측)

```css
.el { width: 150px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.a  { white-space: normal; }
.b  { overflow: visible; }
.c  { text-overflow: clip; }
```

- 네 상자 중 `…` 이 찍히는 것은 어느 것인가?
- `white-space: normal` 인 상자는 어떻게 보이는가?
- `overflow: visible` 인 상자는?
- 두 줄짜리 말줄임을 이 속성으로 만들 수 있는가?

### 7. 이 자손은 밑줄을 끌 수 있는가 (예측)

```css
.dec { text-decoration: underline wavy #c00 3px; }
.off { text-decoration: none; color: #06c; }
.ib  { display: inline-block; color: #06c; }
```

```html
<p class="dec">바깥 <span class="off">자손이 껐다</span> 바깥</p>
<p class="dec">바깥 <span class="ib">원자 인라인</span> 바깥</p>
```

- 두 줄의 화면은 같은가 다른가?
- 두 자손의 `getComputedStyle(...).textDecorationLine` 은 각각 무엇인가?
- 계산값이 같은데 화면이 다른 이유는 무엇인가?
- 자손이 `text-decoration-line: line-through` 를 주면 무엇이 보이는가?

### 8. 왜 `overflow: hidden` 으로는 안 되는가 (왜)

- 긴 URL 이 상자를 뚫는 근본 원인은 무엇인가?
- `overflow: hidden` 을 걸면 무엇이 달라지고 무엇이 안 달라지는가?
- 고치는 속성은 무엇이고, 그것이 파이프라인의 어느 단계에서 끼어드는가?

### 9. `white-space` 와 `text-wrap` 은 어떤 관계인가 (경계)

- `white-space: pre-wrap` 의 계산값을 두 롱핸드로 쪼개면 각각 무엇인가?
- `white-space-collapse: preserve` 만 썼을 때 `white-space` 는 무엇으로 읽히는가?
- `white-space: nowrap` 뒤에 `text-wrap: balance` 를 쓰면 줄바꿈이 막히는가?
- 그 이유는 캐스케이드인가 단축인가?

### 10. `word-wrap` 과 `overflow-wrap` 은 무엇이 다른가 (경계)

- 두 속성은 다른 것인가?
- `word-break: break-word` 라고 쓰면 무슨 일이 일어나는가?
- 「값 이름이 비슷한데 속성이 다른」 짝을 셋 들 수 있는가?

### 11. 다른 주제와 잇기 (연결)

- 같은 문장의 줄 수가 머신마다 다를 수 있는 이유는 무엇인가?
- `font: 16px sans-serif` 한 줄이 줄 수에 영향을 주는가?
- 이 문서가 「줄 수」까지만 다루고 「줄 높이」를 다루지 않는 이유는 무엇인가?
- `anywhere` 가 `min-content` 를 바꾸는 것은 어느 주제와 이어지는가?
- `text-decoration` 의 전파가 상속과 다른 점을 한 문장으로 말할 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

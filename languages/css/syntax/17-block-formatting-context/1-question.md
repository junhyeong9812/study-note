# css/syntax/17 — 서식 문맥(BFC) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **상자의 높이와 폭이 몇이 될지 맞힐 수 있는지**를 묻는다.
> ★ **「눈으로 보이는 것」과 「rect 가 말하는 것」이 다른 문항이 둘 있다.** 어느 쪽을 묻는지 잘 읽어라.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. BFC 는 무엇을 차단하는가 (왜)

- BFC 를 한 문장으로 정의할 수 있는가?
- BFC 가 차단하는 것 **셋**을 댈 수 있는가?
- `display: bfc` 라는 선언이 없는 이유는 무엇인가?
- 「BFC 를 열어라」를 직접 뜻하는 값 **하나**는 무엇인가?

### 2. 이 부모의 높이는 몇인가 (예측)

```css
.p { width: 240px; border: 2px solid #000; }      /* 높이 선언 없음 */
.f { float: left; width: 80px; height: 50px; }
```

```html
<div class="p"><div class="f"></div></div>
```

- `.p` 의 `rect.height` 는 몇인가?
- `.p` 에 `display: flow-root` 를 주면 몇이 되는가?
- 그 차이가 생기는 이유를 float 의 성질로 설명할 수 있는가?
- 이 부모 바로 뒤에 오는 형제 상자는 어디에 놓이는가?

### 3. 이 상자는 얼마나 넓은가 (예측)

```css
.col { width: 300px; border: 2px solid #000; display: flow-root; }
.f   { float: left; width: 100px; height: 34px; }
.t   { background: pink; }            /* 그냥 블록 */
.t2  { background: pink; display: flow-root; }
```

- `.t` 의 `rect.width` 와 `rect.x` 는 각각 몇인가?
- `.t2` 는 각각 몇인가?
- 화면에서는 둘이 비슷해 보일 수 있다 — **무엇이 밀린 것**이고 **무엇은 안 밀린 것**인가?
- 이 차이를 눈으로 구분하려면 무엇을 봐야 하는가?

### 4. `overflow` 네 값 중 BFC 가 아닌 것 (경계)

```css
.a { overflow: hidden; }
.b { overflow: auto; }
.c { overflow: scroll; }
.d { overflow: clip; }
```

- 넷 중 BFC 를 만들지 **않는** 것은 무엇인가?
- 그 값이 예외인 이유를 「스크롤 컨테이너」라는 말로 설명할 수 있는가?
- "`overflow` 가 `visible` 이 아니면 BFC" 라는 요약은 어디서 깨지는가?
- 바르게 고친 한 문장은 무엇인가?

### 5. `flow-root` 대 `overflow: hidden` (예측)

```css
.p   { width: 160px; height: 40px; border: 2px solid #000; }
.big { width: 240px; height: 34px; }      /* 부모보다 넓다 */
```

- `.p` 가 `display: flow-root` 일 때와 `overflow: hidden` 일 때, **`.big` 의 `rect.width`** 는 각각 몇인가?
- 화면에서는 무엇이 다른가?
- 「잘렸다」를 `getBoundingClientRect()` 로 잴 수 있는가?
- `overflow: scroll` 로 바꾸면 부모의 높이에 무슨 일이 생기는가?

### 6. `flow-root` 를 줬는데 안 막힌다 (경계)

```html
<div class="prev">앞 형제 (margin-bottom: 30px)</div>
<div class="root" style="display: flow-root; margin-top: 30px">
  <div class="child" style="margin-top: 40px">자식</div>
</div>
```

- 자식의 40px 마진은 `.root` 밖으로 새는가?
- `.root` 자신의 30px 위 마진은 앞 형제의 30px 아래 마진과 상쇄되는가?
- BFC 루트는 **누구의** 구성원인가?

### 7. 어느 선언이 BFC 를 여는가 (경계)

- `position: absolute` 는 BFC 를 여는가?
- `display: inline-block` 은 어떤가?
- `contain: layout` 은 어떤가?
- 이 목록이 잡다해 보이는 이유를 한 문장으로 설명할 수 있는가?

### 8. 옛 관용구를 오늘 다시 쓴다면 (연결)

- `::after { content: ""; display: block; clear: both }` 는 무엇을 하려던 것인가?
- 그것을 오늘 한 줄로 대체하면 무엇인가?
- `overflow: hidden` 으로 같은 일을 할 때 생기는 부작용 **둘**은 무엇인가?
- `flow-root` 를 두 값 `display` 로 풀어 쓰면 무엇인가?

### 9. 다른 주제와 잇기 (연결)

- float 가 **무엇을 밀어내고 `clear` 가 무엇을 하는지**의 정본은 목록의 몇 번 주제인가?
- 마진이 합쳐지는 규칙 자체와 막는 법 전수의 정본은 몇 번 주제인가?
- BFC 와 **쌓임 맥락**은 같은 것인가?
- flex 항목에 마진 상쇄가 없는 이유를 이 주제의 말로 설명할 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

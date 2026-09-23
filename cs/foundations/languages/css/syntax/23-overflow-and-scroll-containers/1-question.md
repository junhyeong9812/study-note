# css/syntax/23 — 오버플로·스크롤 컨테이너·스크롤바 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ★ **「잘리나」·「스크롤 컨테이너인가」·「스크롤바가 보이나」 세 질문에 따로 답하라.**
> 셋을 한 낱말로 묶으면 `hidden` 과 `clip` 을 영영 못 가른다. 실측 환경: Chrome 151 headless.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 다섯 값의 세 가지 성질 (예측)

```css
.box { width: 200px; height: 80px; border: 2px solid; }  /* 내용은 320×200 */
```

- `visible`·`hidden`·`clip`·`auto`·`scroll` 각각 **잘리는가**?
- 각각 **스크롤 컨테이너**인가?
- 각각 `clientWidth` 는 몇인가?
- 세 질문의 답이 **모두 같은 값**은 무엇인가?

### 2. `hidden` 과 `clip` 을 가르는 한 줄 (예측)

```js
box.scrollTop = 200;
console.log(box.scrollTop);
```

- `overflow: hidden` 이면 출력은?
- `overflow: clip` 이면?
- `clientWidth`·`offsetWidth`·`scrollWidth`·`scrollHeight` 는 두 경우에 다른가?
- 화면(스크린샷)으로 둘을 구분할 수 있는가?

### 3. 한 축만 주면 (예측)

```css
.a { overflow-x: hidden; overflow-y: visible; }
.b { overflow-x: clip;   overflow-y: visible; }
.c { overflow-x: hidden; overflow-y: clip; }
```

- `.a` 의 `getComputedStyle().overflowY` 는 무엇인가?
- `.b` 는?
- `.c` 의 `overflowY` 는?
- 이 규칙이 왜 있는지 한 문장으로 설명할 수 있는가?

### 4. `hidden` 이 딸려 오게 하는 것 (연결)

- 깊숙한 자식이 포커스를 받으면 `overflow: hidden` 상자에 무슨 일이 일어나는가?
- 자손의 `position: sticky` 는 어떻게 되는가?
- BFC 는 열리는가 — 그 정본은 몇 번 주제인가?
- `clip` 으로 바꾸면 셋 중 몇 개가 사라지는가?

### 5. 스크롤바가 먹는 자리 (예측)

```css
.p { overflow: auto; width: 200px; height: 80px; border: 2px solid; }
```

- 내용이 안 넘칠 때 `clientWidth`·`offsetWidth` 는 각각 몇인가?
- 내용이 넘칠 때는?
- 그 차이가 레이아웃에서 어떻게 드러나는가?
- `scrollbar-gutter: stable` 을 주면 두 경우가 각각 몇이 되는가?

### 6. `clip` 에만 있는 것 (경계)

- `overflow-clip-margin` 은 무엇을 하는가?
- `overflow: hidden` 에 같은 선언을 주면 어떻게 되는가?
- 「자르되 살짝은 넘치게」가 필요한 실무 상황을 하나 들 수 있는가?
- `clip` 을 쓰면 잃는 것은 무엇인가?

### 7. 「사라졌다」를 가르기 (연결)

- 드롭다운이 안 보인다. 원인 후보 **둘**은 무엇인가?
- 둘을 화면만 보고 가르는 방법은?
- 「잘렸나」를 `getBoundingClientRect()` 로 판정할 수 있는가?
- 그러면 무엇으로 재는가?

### 8. `sticky` 를 살리는 처방 (연결)

```html
<div style="overflow:auto; height:200px">
  <div style="overflow:hidden">            <!-- 여기가 문제다 -->
    <div style="position:sticky; top:0">머리</div>
```

- 머리가 왜 안 붙는가?
- 한 글자만 고쳐 살리는 방법은?
- 그것이 동작하는 이유는 무엇인가?
- `sticky` 규칙 자체의 정본은 몇 번 주제인가?

### 9. 목적에 맞는 값 고르기 (왜)

- 「자르기만 하면 된다」 → 무엇을 쓰나?
- 「BFC 만 필요하다」 → 무엇을 쓰나, 왜 `overflow` 가 아닌가?
- 「스크롤은 되되 레이아웃은 안 튀게」 → 무엇을 조합하나?
- `hidden` 이 「어중간한 값」이라고 불리는 이유는?

### 10. 다른 주제로 잇기 (연결)

- `overflow` 는 쌓임 맥락을 만드는가 — 그 정본은 몇 번인가?
- `clientWidth` 와 `offsetWidth` 가 재는 칸의 정본은 몇 번인가?
- `overflow: clip` 이 BFC 를 안 여는 이유를 이 주제의 낱말로 설명할 수 있는가?
- 스크롤 스냅·`overscroll-behavior` 는 이 편에서 다루는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

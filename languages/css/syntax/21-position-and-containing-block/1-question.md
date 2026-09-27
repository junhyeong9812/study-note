# css/syntax/21 — `position` 다섯 값과 포함 블록 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ★ **모든 답을 「포함 블록이 무엇인가」로 환원해서 적어라.** 「왼쪽 위로 간다」는 답이 아니다 —
> **무엇의** 왼쪽 위인지가 이 주제의 전부다. 실측 환경: Chrome 151 headless.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 다섯 값이 자리를 남기는가 (예측)

```html
<div class="row"><i>1</i><i class="x">2</i><i>3</i></div>
<!-- .x 에 top:20px; left:30px 을 주고 position 만 바꿔 본다. 각 i 는 높이 24 -->
```

- `static` · `relative` · `absolute` 에서 `.x` 는 각각 어디에 그려지는가?
- 세 경우에서 **형제 `3`** 의 y 는 각각 얼마인가?
- 컨테이너의 높이는 세 경우에서 같은가 다른가?
- `static` 에서 `top: 20px` 은 어떤 에러를 내는가?

### 2. `absolute` 는 어느 상자를 기준으로 재는가 (예측)

```css
.anc { position: relative; margin: 20px; border: 10px solid; padding: 30px;
       width: 300px; height: 160px; }
.kid { position: absolute; top: 0; left: 0; }
```

- `.kid` 의 `rect.x`·`rect.y` 는 각각 몇인가?
- 그 값은 **테두리 상자**·**패딩 상자**·**콘텐츠 상자** 중 무엇의 원점인가?
- 같은 조상 안에서 `.kid` 에 `left: 50%` 를 주면 `rect.x` 는 몇인가?
- **보통 블록**에 `width: 50%` 를 주면 폭은 몇인가 — 두 `50%` 가 같은가?

### 3. 위로 아무도 없으면 (경계)

```css
/* 조상 중 position 이 static 이 아닌 것이 하나도 없다 */
.kid { position: absolute; top: 20px; left: 30px; }
```

- `.kid` 는 어디에 붙는가 — 그 기준의 이름은 무엇인가?
- 그 기준의 **크기**는 무엇과 같은가?
- 그 기준의 **원점**은 어디인가 — 스크롤하면 따라 움직이는가?
- `fixed` 였다면 무엇이 달라지는가?

### 4. `fixed` 가 화면에 안 붙는다 (예측)

```html
<div style="transform: translateX(0)">
  <div style="position: fixed; top: 0; left: 0">나</div>
</div>
```

- 이 `fixed` 는 화면 왼쪽 위에 붙는가?
- `translateX(0)` 은 아무것도 안 옮기는 값인데 왜 영향을 주는가?
- 같은 효과를 내는 선언을 **다섯 개 이상** 대 보라.
- 그중 `opacity: 0.5` 는 포함되는가?

### 5. 두 목록은 같은가 (경계)

- **포함 블록을 바꾸는 선언**과 **쌓임 맥락을 만드는 선언**은 같은 목록인가?
- `opacity: 0.99` 는 각각에 해당하는가?
- `position: relative; z-index: 1` 은?
- 「`fixed` 가 안 붙는다」와 「`z-index` 가 안 먹는다」를 같은 원인으로 진단해도 되는가?

### 6. `sticky` 가 안 붙는다 (예측)

```html
<div style="overflow:auto; height:120px">
  <div style="overflow:???">
    <div style="position:sticky; top:0">머리</div>
    <div style="height:400px"></div>
  </div>
</div>
```

- 가운데 래퍼가 `visible` 일 때 머리는 붙는가?
- `hidden` 일 때는?
- **`clip`** 일 때는 — `hidden` 과 결과가 같은가 다른가?
- 왜 그렇게 갈리는가(한 문장으로)?

### 7. `overflow: hidden` 은 스크롤 컨테이너인가 (예측)

```js
box.scrollTop = 200;   // box 는 overflow: hidden, 내용은 넘친다
```

- 이 대입 뒤 `box.scrollTop` 은 몇인가?
- `overflow: clip` 이면?
- `sticky` 가 `hidden` 안에서 동작하는 것과 이 결과는 어떻게 이어지는가?
- 스크롤바는 보이는가?

### 8. `inset` 단축 (예측)

```css
.a { position: relative; inset: 10px auto auto 40px; }
.b { position: absolute; inset: 0; }
```

- `.a` 는 원래 자리에서 어느 방향으로 몇 px 옮겨지는가?
- `inset` 의 네 값 순서는 무엇과 같은가?
- `.b` 는 폭·높이를 안 줬는데 크기가 정해지는가 — 왜?
- `relative` 에서 `left` 와 `right` 를 둘 다 주면 어느 쪽이 이기는가?

### 9. 잘림과 포함 블록 (연결)

```css
.box { overflow: hidden; position: relative; }   /* 안에 absolute 자식과 fixed 자식 */
```

- `absolute` 자식은 `.box` 밖으로 삐져나온 부분이 잘리는가?
- `fixed` 자식은?
- 그 차이의 원인을 **포함 블록**으로 설명할 수 있는가?
- 「잘렸나」를 `getBoundingClientRect()` 로 판정할 수 있는가 — 아니면 무엇으로 재는가?

### 10. 다른 주제로 잇기 (연결)

- `absolute` 와 `float` 는 「흐름에서 빠진다」가 같은데 **행 상자**에 대해서는 무엇이 다른가?
- `%` 가 포함 블록을 만나 풀리는 단계의 이름은 무엇이며 정본은 몇 번 주제인가?
- `position: absolute` 는 BFC 를 여는가 — 그 정본은 몇 번인가?
- 「누가 위에 그려지나」의 정본은 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

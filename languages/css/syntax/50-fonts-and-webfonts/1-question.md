# css/syntax/50 — 글꼴과 웹폰트: `font` 단축·`@font-face`·`font-display`·가변 폰트 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 다만 글꼴은 **환경에 달렸으므로**,
> 「무슨 글꼴로 그려지나」가 아니라 「**어떻게 알아내나 · 무엇이 되돌아가나**」를 묻는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 이 셋 중 실제로 어느 글꼴이 쓰였는가 (예측)

```css
.a { font-family: Georgia; }
.b { font-family: Georgia, serif; }
.c { font-family: Georgia, monospace; }
```

- Georgia 가 깔려 있지 않은 머신에서 셋은 각각 무엇으로 그려지는가?
- `.a` 와 `.b` 는 같은 글꼴로 그려지는가?
- `getComputedStyle(el).fontFamily` 는 셋에 대해 각각 무엇을 돌려주는가?
- 그 값으로 「Georgia 가 쓰였나」를 판정할 수 있는가?

### 2. 이 한 줄 뒤에 무엇이 남는가 (예측)

```css
.a { font-style: italic; font-weight: 700; font-variant-caps: small-caps;
     line-height: 2; font-size: 30px; font-family: serif; }
.b { font: 16px sans-serif; }
```

- `class="a b"` 인 요소의 `font-style`·`font-weight`·`font-variant-caps`·`line-height` 계산값은 각각 무엇인가?
- 그렇게 되는 것은 `.b` 의 명시도가 더 세기 때문인가?
- `font` 단축이 값을 **받지도 못하는데 되돌리기만 하는** 속성에는 무엇이 있는가?
- `.b` 를 `font-size: 16px; font-family: sans-serif;` 두 줄로 바꾸면 무엇이 달라지는가?

### 3. 이 다섯 줄 중 살아남는 것은 몇 개인가 (예측)

```css
#a { font: 16px serif; }
#b { font: bold italic 16px serif; }
#c { font: italic 16px; }
#d { font: 16px/1.4 serif bold; }
#e { font: sans-serif 16px; }
```

- 각 줄의 `cssRules[...].style.cssText` 는 무엇인가?
- 버려진 줄은 앞에서 정해 둔 값을 되돌리는가, 그대로 두는가?
- 「`font:` 를 썼는데 아무것도 안 바뀐다」와 「`font:` 를 썼더니 다 날아갔다」 중 어느 쪽이 문법 오류인가?

### 4. 이 한 요소는 몇 개의 글꼴로 그려지는가 (예측)

```css
@font-face { font-family: BoxOnly; src: url(...); }   /* A~Z 글리프만 들어 있다 */
.mix { font: 40px BoxOnly, serif; }
```

```html
<p class="mix">ABC abc</p>
```

- `ABC` 와 `abc` 는 같은 글꼴로 그려지는가?
- 그 판단은 요소 단위로 내려지는가, 글자 단위로 내려지는가?
- 한글 페이지에서 `font-family: Inter` 만 쓰면 한글은 어떻게 되는가?
- 그것은 버그인가?

### 5. 폰트가 4초 뒤에 도착하면 다섯 값은 각각 무엇을 보여 주는가 (예측)

```css
@font-face { font-family: F1; src: url(slow.woff2); font-display: block; }
@font-face { font-family: F2; src: url(slow.woff2); font-display: swap; }
@font-face { font-family: F3; src: url(slow.woff2); font-display: fallback; }
@font-face { font-family: F4; src: url(slow.woff2); font-display: optional; }
```

- 0.8초 시점에 글자가 **보이는** 것은 어느 것들인가?
- 4.6초 시점에 **웹폰트로** 그려져 있는 것은 어느 것들인가?
- 폰트가 1.5초 만에 왔다면 `optional` 은 바뀌는가?
- 이 넷 중 「레이아웃이 절대 안 흔들리는」 것은 무엇이고, 그 대가는 무엇인가?

### 6. `font-weight: 450` 은 어떻게 그려지는가 (예측)

```css
/* (가) 가변 폰트를 @font-face 로 불러온 경우 */
@font-face { font-family: V; src: url(var.woff2); font-weight: 100 800; }
.a { font-family: V; font-weight: 450; }

/* (나) 같은 가변 폰트가 OS 에 설치돼 있는 경우 */
.b { font-family: Ubuntu; font-weight: 450; }
```

- (가)의 폭은 400 과 500 사이에 오는가?
- (나)도 그러한가?
- `font-variation-settings: "wght" 450` 은 (가)·(나)에서 각각 먹는가?
- 이 차이를 만드는 것은 CSS 인가 OS 인가?

### 7. 왜 `getComputedStyle` 로는 판정이 안 되는가 (왜)

- `font-family` 의 계산값은 무엇으로 규정돼 있는가?
- `--dump-dom` 으로 뽑아 확인하는 자동화 스크립트가 왜 같은 함정에 빠지는가?
- 대신 쓸 수 있는 판정 방법은 무엇이고, 왜 센티넬이 둘 이상 필요한가?

### 8. `document.fonts.check("16px Georgia")` 는 무엇에 답하는가 (경계)

- Georgia 가 없는 머신에서 이 값은 무엇인가?
- 세상에 없는 이름 `Zzzznope` 를 넣으면 무엇이 나오는가?
- `false` 가 나오는 경우는 언제인가?
- 이 함수로 「설치돼 있나」를 물을 수 있는가?

### 9. `@font-face` 만 써 두면 무슨 일이 일어나는가 (경계)

- 파일은 내려받히는가?
- `document.fonts` 에서 그 face 의 `status` 는 무엇인가?
- `@font-face` 는 글꼴을 **적용**하는가?

### 10. `format()` 에 오타가 나면 어디까지 사라지는가 (경계)

- `format("wofff2")` 로 잘못 적으면 그 `src` 항목만 사라지는가, 규칙 전체가 사라지는가?
- 콘솔에 무엇이 찍히는가?
- 반대로 `ttf` 파일에 `format("woff2")` 를 붙이면 어떻게 되는가?
- 이것을 진단하는 창구는 「진단 3창」 중 어느 것인가?

### 11. 왜 `font-variation-settings` 보다 `font-weight` 를 쓰라고 하는가 (왜)

- `font` 단축과 어떤 관계가 있는가?
- 상속될 때 무엇이 문제가 되는가?
- 그 글꼴에 `wght` 축이 없으면 둘은 각각 어떻게 되는가?
- `font-feature-settings` 대 `font-variant-*` 도 같은 이유인가?

### 12. 다른 주제와 잇기 (연결)

- 글꼴 속성이 상속되는 대표라는 사실이 「목록을 어디에 한 번 쓰나」에 어떤 답을 주는가?
- `font: 16px serif` 가 `font-size` 를 바꾸면, 그 아래의 `em` 값들은 어느 단계에서 다시 계산되는가?
- `font:` 의 잘못된 순서가 버려지는 것은 CSS 의 어떤 일반 규칙인가?
- `font` 단축이 `line-height` 를 되돌리면 행 상자에 무엇이 달라지는가?
- 어느 글꼴로 그리는지가 정해져야 다음 주제에서 무엇을 정할 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

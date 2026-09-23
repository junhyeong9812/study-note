# css/syntax/43 — `color-mix()` 와 상대 색 구문 — 질문

> 먼저 답해 보고, 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).
> 예측형은 **출력을 먼저 적고** 이유를 적는다. 기준: **Google Chrome 151.0.7922.173** headless.
> 색은 눈으로 구분이 안 되므로 답에 **RGB 수치**를 적는다 — 「탁한 색」은 답이 아니다.
> 선행: [42번 색 표기와 색 공간](../42-color-notation-and-spaces/1-question.md).

### 1. 같은 두 색을 다른 공간에서 섞으면 (예측)

```css
.a { background: color-mix(in srgb,        #ff0000, #00ffff); }
.b { background: color-mix(in srgb-linear, #ff0000, #00ffff); }
.c { background: color-mix(in oklab,       #ff0000, #00ffff); }
.d { background: color-mix(in hsl,         #ff0000, #00ffff); }
```

네 칸의 **픽셀 RGB** 를 각각 적어라.\
**보색을 반씩 섞으면 회색이 된다**는 말은 넷 중 어느 것에 대해 참인가.\
회색이 안 되는 것들은 **왜 안 되는지** 좌표계로 설명해라.

### 2. `in` 을 빼면 (예측)

```css
.a { background: color-mix(srgb, red, blue); }
.b { background: color-mix(in srgb, red, blue); }
```

두 규칙의 `cssText` 를 적어라. 화면에서는 무엇이 보이나.\
**진단 3창 중 어느 창으로 잡히나.**

### 3. `cssText` 에서 사라지는 것 (예측)

```css
.a { background: color-mix(in oklab, red, blue); }
.b { background: color-mix(in srgb, red, blue); }
.c { background: color-mix(in hsl shorter hue, red, cyan); }
.d { background: color-mix(in hsl longer hue, red, cyan); }
```

넷의 `cssText` 를 적어라. **넷 중 둘은 내가 적은 것과 다르게 나온다.** 어느 둘이고 왜 그런가.

### 4. 비율을 둘 다 적으면 (예측)

```css
.a { background: color-mix(in srgb, red, blue); }
.b { background: color-mix(in srgb, red 20%, blue 20%); }
.c { background: color-mix(in srgb, red 150%, blue); }
```

셋의 **계산값**과 **흰 배경 위 픽셀 RGB** 를 적어라.\
`.b` 가 `.a` 보다 연하게 보인다면 **무엇이 달라진 것인가.**

### 5. `longer hue` 가 하는 일 (예측)

```css
.a { background: color-mix(in hsl shorter hue, red, blue); }
.b { background: color-mix(in hsl longer hue,  red, blue); }
```

두 칸의 픽셀 RGB 를 적어라.\
그리고 **빨강과 청록**(각도 차가 정확히 180도)으로 같은 실험을 하면 두 칸이 어떻게 되는지 예측해라.

### 6. 상대 색 구문에서 조용히 죽는 선언 (예측)

```css
.a { background: hsl(from #3b82f6 h s calc(l + 20%)); }
.b { background: hsl(from #3b82f6 h s calc(l + 20));  }
.c { background: oklch(from #3b82f6 calc(l + 0.2) c h); }
```

셋의 `cssText` 를 적어라. **하나는 빈 문자열이다.** 어느 것이고 왜인가.\
그리고 `.b` 의 `20` 과 `.c` 의 `0.2` 가 **왜 다른 수인지** 답해라.

### 7. `from` 뒤에 무엇을 넣을 수 있나 (경계)

`oklch(from … l c h)` 의 `…` 자리에 hex·`var(--c)`·다른 색 함수를 넣을 수 있나. **바깥 함수와 `from` 뒤 색의 공간이 달라도 되나.**

### 8. `rgb(from red calc(255 - r) g b)` 는 무슨 색인가 (예측)

계산값을 적어라. **그리고 그 계산값의 함수 이름이 `rgb(` 가 아닌 이유**를 말해라.

### 9. 흰색과 섞기와 `l` 올리기의 차이 (왜)

「이 색을 연하게」를 `color-mix(in oklab, var(--c) 80%, white)` 로 하는 것과 `oklch(from var(--c) calc(l + 0.15) c h)` 로 하는 것은 **결과가 어떻게 다른가.** 어느 쪽이 무엇을 잃나.

### 10. `color-mix()` 와 `mix-blend-mode` 는 무엇이 다른가 (연결)

둘 다 「섞는다」인데 **무엇을 섞는가**가 다르다. 그 차이가 **`getComputedStyle` 로 결과를 읽을 수 있느냐**에 어떻게 나타나나.

### 11. 셋을 섞으려면 (경계)

`color-mix()` 에는 인자가 둘뿐이다. 색 셋을 섞으려면 어떻게 적나.

### 12. 둘 중 무엇을 먼저 쓰나 (경계)

`color-mix()` 와 상대 색 구문의 **Baseline 상태**를 각각 적고, 지원 폭이 중요한 프로젝트에서 **어느 쪽을 기본으로 삼아야 하는지** 답해라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|---|---|---|---|
| | | | |

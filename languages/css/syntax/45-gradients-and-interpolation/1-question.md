# css/syntax/45 — 그라디언트와 보간 색 공간 — 질문

> 먼저 답해 보고, 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).
> 예측형은 **출력을 먼저 적고** 이유를 적는다. 기준: **Google Chrome 151.0.7922.173** headless.
> ★ **이 주제는 계산값으로 답할 수 없다.** 답에 **픽셀 RGB** 를 적는다 — 「보라색이 된다」는 답이 아니다.
> 선행: [42번 색 표기와 색 공간](../42-color-notation-and-spaces/1-question.md) · [44번 배경과 대체 요소 맞춤](../44-backgrounds-and-object-fit/1-question.md).

### 1. 위치를 안 적으면 어디에 놓이나 (예측)

```css
.a { background: linear-gradient(90deg, red, lime, blue); }
```

400px 폭에서 x = 0 · 100 · 200 의 픽셀 RGB 를 적어라.\
**세 정지점이 각각 몇 % 에 놓였는가.**

### 2. 앞선 것보다 작은 위치를 적으면 (예측)

```css
.a { background: linear-gradient(90deg, red 0%, lime 80%, blue 20%); }
```

400px 폭에서 20% · 75% · 80% · 90% 지점의 픽셀 RGB 를 적어라.\
`blue 20%` 는 **버려지나, 옮겨지나.** 그 결과 80% 자리는 어떤 모양이 되나.\
그리고 **`getComputedStyle().backgroundImage` 에는 `20%` 가 남아 있나.**

### 3. 정지점 둘을 같은 자리에 두면 (예측)

```css
.a { background: linear-gradient(90deg, red 50%, blue 50%); }
.b { background: linear-gradient(90deg, red 0 25%, lime 25% 50%, blue 50% 100%); }
```

`.a` 의 25% · 50% 픽셀을 적어라. **중간색이 있나.**\
`.b` 의 계산값은 정지점이 **몇 개**로 펴지나.

### 4. ★ 같은 두 색, 다른 보간 공간 (예측)

```css
.a { background: linear-gradient(in srgb 90deg, red, blue); }
.b { background: linear-gradient(in srgb-linear 90deg, red, blue); }
.c { background: linear-gradient(in oklab 90deg, red, blue); }
.d { background: linear-gradient(in hsl 90deg, red, blue); }
.e { background: linear-gradient(in hsl longer hue 90deg, red, blue); }
```

다섯의 **50% 지점 픽셀 RGB** 를 적어라.\
그중 **빨강에도 파랑에도 없는 색**이 나오는 것은 어느 것이고 왜인가.\
**중간이 가장 어두운 것**과 **가장 밝은 것**은 각각 어느 것인가.

### 5. 보간 힌트 (예측)

```css
.a { background: linear-gradient(90deg, red, blue); }
.b { background: linear-gradient(90deg, red, 20%, blue); }
```

두 경우의 **50% 지점 픽셀**을 적어라. 힌트가 무엇을 옮겼나.\
힌트에는 왜 색을 안 적나.

### 6. ★ `transparent` 로 페이드하면 회색이 끼나 (예측)

```css
/* 검정 배경 위 */
.a { background: linear-gradient(90deg, red, transparent); }
.b { background: linear-gradient(90deg, red, rgb(255 0 0 / 0)); }
.c { background: linear-gradient(90deg, red, rgb(0 0 255 / 0)); }
```

셋의 50% 픽셀을 적어라. **셋이 같은가 다른가.**\
같다면 그것이 무엇을 증명하나. 그리고 **「`rgb(R G B / 0)` 으로 고쳐라」는 조언이 이 브라우저에서 무엇을 바꾸나.**

### 7. ★ 그런데 회색 띠는 지금도 생긴다 (예측)

```css
/* 배경이 #9ca3af = rgb(156, 163, 175) 인 곳 */
.a { background: linear-gradient(90deg, #e11d48, transparent, #2563eb); }
```

50% 지점의 픽셀을 예측해라. **왜 그 값인가.**\
6번의 답과 모순되지 않는 이유를 한 줄로 말해라. 그리고 **고치는 법**을 적어라.

### 8. 그라디언트는 색인가 이미지인가 (예측)

```css
.a { background-color: linear-gradient(red, blue); }
.b { background-image: linear-gradient(90deg, red 0 50%, blue 50% 100%);
     background-size: 40px 20px; }
.c { background-image: repeating-linear-gradient(90deg, red 0 20px, blue 20px 40px); }
```

`.a` 의 `cssText` 를 적어라.\
`.b` 와 `.c` 의 x = 1 · 25 · 100 · 300 픽셀을 각각 적어라. **둘이 같은가.**

### 9. `radial-gradient` 의 기본 모양 (예측)

200×100 상자에 `radial-gradient(red, blue)` 를 주면 왼쪽 가장자리(5,50)와 위 가장자리(100,5)의 색이 **비슷한가 크게 다른가.**\
`circle` 을 붙이면 어떻게 달라지나.

### 10. 계산값으로 이 주제를 검증할 수 있나 (경계)

`linear-gradient(in oklab 90deg, red, blue)` 의 계산값을 적어라.\
그 문자열에서 **중간색을 알 수 있나.** 이 주제의 유일한 근거는 무엇인가.

### 11. 줄무늬를 만드는 두 가지 (연결)

`background-size` + 하드 스톱과 `repeating-linear-gradient` — 둘 중 **어느 쪽이 더 싼가**, 그리고 왜인가.

### 12. `in <공간>` 을 못 읽는 브라우저에서는 (경계)

`linear-gradient(in oklch 90deg, red, blue)` 의 Baseline 상태를 적고, **지원 안 하는 브라우저에서 무슨 일이 일어나는지** 답해라. 그림이 아예 안 나오나.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|---|---|---|---|
| | | | |

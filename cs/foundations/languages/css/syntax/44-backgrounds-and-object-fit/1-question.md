# css/syntax/44 — 배경과 대체 요소 맞춤 — 질문

> 먼저 답해 보고, 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).
> 예측형은 **출력을 먼저 적고** 이유를 적는다. 기준: **Google Chrome 151.0.7922.173** headless.
> 위치·크기 답에는 **px 좌표**를 적는다 — 「위쪽에 붙는다」는 답이 아니다.
> 선행: [15번 박스 모델과 `box-sizing`](../15-box-model-and-box-sizing/1-question.md).

### 1. 단축이 푸는 아홉 가지 (예측)

```css
.a { background: #eee url(dot.png) no-repeat right 10px bottom 20px / 40px 30px content-box padding-box; }
```

이 한 줄이 설정하는 롱핸드 아홉 개를 **이름과 값으로** 적어라.\
그중 **내가 적지 않았는데 값이 들어간 것**이 있나. 있다면 무엇으로 들어갔나.

### 2. 상자 값을 하나만 적으면 (예측)

```css
.a { background: padding-box red; }
.b { background: border-box padding-box red; }
```

두 규칙의 `background-origin` 과 `background-clip` 을 각각 적어라.\
**`clip` 만 바꾸고 싶었다면 어떻게 적어야 하나.**

### 3. 배경 레이어 둘이 겹치면 누가 보이나 (예측)

```css
.stack {
  width: 220px; height: 60px;
  background-image:
    linear-gradient(90deg, #dc2626 0 110px, transparent 110px),
    linear-gradient(90deg, #2563eb 0 165px, transparent 165px);
  background-repeat: no-repeat;
}
```

x = 50 · 130 · 190 세 자리의 **픽셀 RGB** 를 적어라.\
그리고 `background-color: yellow` 를 더하면 **어느 구간이 노랗게 되는가.**

### 4. `origin` 과 `clip` 을 하나씩 바꾸면 (예측)

```css
.b { width: 180px; height: 70px; border: 10px solid transparent; padding: 20px;
     background-color: #2563eb;
     background-image: url(dot.png);   /* 16px 타일, no-repeat */ }
```

`background-origin` 을 `border-box` → `content-box` 로 바꿨을 때 **무엇이 움직이고 무엇이 안 움직이나.**\
`background-clip` 을 `border-box` → `content-box` 로 바꿨을 때는?\
두 답을 **「타일의 시작 좌표」와 「칠해진 구간」** 두 축으로 갈라 적어라.

### 5. `space` 와 `round` (예측)

폭 **180px** 상자에 **50px** 타일을 깐다. `180 / 50 = 3.6` 이다.

```css
.a { background-repeat: space; }
.b { background-repeat: round; }
```

두 경우의 **타일 개수**와 **타일 사이 중심 간격**을 적어라.\
그리고 `round` 로 줄어든 타일 크기를 **`getComputedStyle().backgroundSize` 로 읽을 수 있나.**

### 6. 같은 `cover` 인데 결과가 다르다 (예측)

**16×8** 이미지를 **120×120** 칸에 넣는다.

```css
img { object-fit: cover; }
div { background-size: cover; background-image: url(같은이미지); }
```

두 칸의 **y = 60 가로줄**에서 x = 5 · 55 · 65 · 115 의 픽셀이 각각 무슨 색 계열인지 적어라.\
**둘이 다르다면 왜 다른가.**

### 7. `background-clip: text` 만 주면 (예측)

```css
.t { background-image: linear-gradient(90deg, #e11d48, #2563eb);
     background-clip: text; }
```

화면에 무엇이 보이나. **글자는 무슨 색인가.** 그라디언트를 보려면 무엇을 더 적어야 하나.

### 8. `background: red` 한 줄의 부작용 (왜)

```css
.card { background-image: url(pattern.png); }
.card.on { background: red; }
```

`.card.on` 에서 무늬가 사라진다. 왜인가. 무늬를 유지하면서 색만 바꾸려면?

### 9. `object-fit` 을 `<div>` 에 주면 (경계)

아무 일도 안 일어난다. **진단 3창으로 이 사고를 잡을 수 있나** — 세 창이 각각 무엇을 보여 주는지 답해라.

### 10. `background-attachment: fixed` 가 바꾸는 것 (예측)

폭 100px 상자에 `linear-gradient(90deg, #e11d48, #2563eb)` 를 주고 `attachment` 만 `scroll` → `fixed` 로 바꿨다.\
상자 안에서 **색이 얼마나 변하는지** 어떻게 달라지나. 왜 그런가.

### 11. `background-position: right 10px bottom 10px` 의 계산값 (예측)

계산값 문자열을 적어라. 그리고 `background-position: 100% 100%` 가 「영역 폭의 100% 만큼 오른쪽으로 민다」가 **아닌** 이유를 말해라.

### 12. 썸네일은 `<img>` 인가 배경인가 (연결)

카드 목록의 썸네일을 `<img> + object-fit: cover` 로 할 때와 `background-image + background-size: cover` 로 할 때, **결과 화면은 같게 만들 수 있다.** 그래도 어느 쪽을 골라야 하나 — 무엇이 기준인가.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|---|---|---|---|
| | | | |

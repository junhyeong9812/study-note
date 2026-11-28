# css/responsive/12 — Aspect Ratio Boxes — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 폭 320px 박스에 16 / 9 (예측)

```css
/* 질문용 발췌 */
.video { width: 320px; aspect-ratio: 16 / 9; }
```

- 이 박스의 높이는 몇 px 인가?

### 2. 비율 박스에 `max-height` 를 더하면 (예측)

```css
/* 질문용 발췌 */
.box { width: 400px; aspect-ratio: 16 / 9; max-height: 150px; }
```

- 이 박스의 폭과 높이는 각각 얼마이고, 16:9 모양이 유지되나?

### 3. 높이만 정한 4 / 3 박스 (예측)

```css
/* 질문용 발췌 */
.thumb { height: 90px; aspect-ratio: 4 / 3; }
```

- 이 박스의 폭은 몇 px 으로 계산되나?

### 4. 옛 핵이 `padding-top: 56.25%` 를 쓴 까닭 (왜)

- 세로 여백인 `padding-top` 을 퍼센트로 주면 왜 높이가 폭에 비례하게 되고, 56.25% 는 어디서 나온 수인가?

### 5. `width` 와 `height` 를 둘 다 지정한 박스 (경계)

- 두 길이가 다 정해진 박스에 `aspect-ratio` 를 주면 비율은 어떤 역할을 하나?

### 6. `.ar-inner` 에 `height: 100%` 를 준 까닭 (왜)

- 예제에서 비율은 `.ar-box` 가 갖는데 라벨용 `.ar-inner` 에 `width: 100%; height: 100%` 를 주는 것은 왜 필요한가?

### 7. 반응형 그리드와 비율 박스 (연결)

- `repeat(auto-fit, minmax(120px, 1fr))` 그리드의 컨테이너가 넓어져 칸 폭이 늘면, 각 비율 박스의 높이와 모양은 어떻게 되나?

### 8. 비율을 지키며 크기를 제한하려면 (경계)

- 비율 박스가 너무 커지지 않게 막고 싶을 때 높이 쪽 제약 대신 무엇으로 조절하는 편이 비율을 지키나?

## 실습

### 실습 1. 네 가지 비율 박스와 코드 예시 판 만들기

**만들 것** — 16:9 · 4:3 · 1:1 · 21:9 네 박스를 반응형 그리드에 늘어놓고, 그 아래 `aspect-ratio` 와 옛 `padding-top` 핵의 사용 예를 보여 주는 코드 판을 둔다.

**요구 조건**

1. 1단계(그리드) — 네 박스는 그리드로 놓이고, 각 칸은 최소 폭을 지키면서 컨테이너 폭에 맞춰 한 줄의 칸 수가 자동으로 바뀐다.
2. 2단계(비율) — 각 박스는 `height` 를 쓰지 않고 `aspect-ratio` 만으로 높이가 정해진다: 16:9 · 4:3 · 21:9 는 `가로 / 세로` 꼴로 쓴다.
3. 1:1 박스는 숫자 하나만 쓰는 꼴로 정사각형을 만든다.
4. 3단계(안쪽) — 각 박스 안의 라벨 요소는 박스의 폭과 높이를 꽉 채우고, 라벨 글자는 가로 · 세로 가운데에 놓인다.
5. 바깥 박스는 둥근 모서리 밖으로 안쪽 배경이 삐져나오지 않게 자른다.
6. 4단계(코드 판) — 코드 판은 `aspect-ratio` 예 세 줄과 `padding-top` 핵 예를 공백과 줄바꿈 그대로 보여 준다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>Aspect Ratio Boxes</title>
<style>
  .ar-demo { font-family: system-ui, sans-serif; }
  .ar-grid {
    /* TODO: 그리드로 만들고, 칸은 최소 120px · 남는 공간은 나눠 갖게 자동 배치 */
    gap: 12px;
    margin-bottom: 12px;
  }
  .ar-box {
    border-radius: 8px;
    /* TODO: 자식이 둥근 모서리 밖으로 나가지 않게 */
  }
  .ratio-16-9 { /* TODO: 16:9 */ }
  .ratio-4-3  { /* TODO: 4:3 */ }
  .ratio-1-1  { /* TODO: 정사각형(숫자 하나) */ }
  .ratio-21-9 { /* TODO: 21:9 */ }
  .ar-inner {
    /* TODO: 부모를 꽉 채우기 */
    /* TODO: 라벨을 가로 · 세로 가운데로 */
    font-weight: 700;
    font-size: 14px;
    color: white;
  }
  .ratio-16-9 .ar-inner { background: linear-gradient(135deg, #3b82f6, #1d4ed8); }
  .ratio-4-3 .ar-inner  { background: linear-gradient(135deg, #8b5cf6, #6d28d9); }
  .ratio-1-1 .ar-inner  { background: linear-gradient(135deg, #10b981, #059669); }
  .ratio-21-9 .ar-inner { background: linear-gradient(135deg, #f59e0b, #d97706); }
  .ar-code { background: #1e293b; border-radius: 8px; padding: 14px; }
  .ar-code code {
    font-size: 11px;
    color: #e2e8f0;
    /* TODO: 공백 · 줄바꿈을 그대로 보이기 */
    line-height: 1.5;
    display: block;
  }
</style>
</head>
<body>
<div class="ar-demo">
  <div class="ar-grid">
    <div class="ar-box ratio-16-9"><div class="ar-inner">16 : 9</div></div>
    <div class="ar-box ratio-4-3"><div class="ar-inner">4 : 3</div></div>
    <div class="ar-box ratio-1-1"><div class="ar-inner">1 : 1</div></div>
    <div class="ar-box ratio-21-9"><div class="ar-inner">21 : 9</div></div>
  </div>
  <div class="ar-code">
    <code><!-- TODO: aspect-ratio 예(.video · .thumbnail · .avatar)와 padding-top 핵 예(.old-ratio)를 적는다 --></code>
  </div>
</div>
</body>
</html>
```

**확인 방법** — 브라우저로 열어 네 박스의 모양이 각각 16:9 · 4:3 · 정사각형 · 21:9 인지 보고, 창 폭을 줄였다 늘였을 때 한 줄의 칸 수와 박스 크기는 바뀌어도 모양은 그대로인지, 코드 판의 줄바꿈과 들여쓰기가 살아 있는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

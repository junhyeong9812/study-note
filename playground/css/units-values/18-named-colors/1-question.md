# css/units-values/18 — Named colors — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. `papayawhip` 칸의 글자색과 그림자 (예측)

```css
/* 질문용 발췌 */
.swatch { color: white; font-weight: 600; text-shadow: 0 1px 2px rgba(0,0,0,0.2); }
.swatch.dark { color: #1e293b; text-shadow: none; }
```

```html
<!-- 질문용 발췌 -->
<div class="swatch dark" style="background: papayawhip">papayawhip</div>
```

- 이 칸의 글자색과 그림자는 어느 규칙의 값을 따르는가?
- 이 칸의 `font-weight` 는 어떤 값인가?

### 2. `flex: 1` 인 칸 세 개 (예측)

```css
/* 질문용 발췌 */
.row { display: flex; gap: 8px; }
.swatch { flex: 1; }
```

- `.row` 안에 `.swatch` 가 세 개 있으면 세 칸의 너비는 서로 어떤 관계인가?

### 3. 클래스 배경과 인라인 배경이 부딪치면 (예측)

```html
<!-- 질문용 발췌 -->
<style>.swatch { background: gray; }</style>
<div class="swatch" style="background: coral">coral</div>
```

- 이 칸의 배경은 어떤 색이 되는가?

### 4. 여섯 칸 중 `papayawhip` 칸에만 `dark` 를 붙인 이유 (왜)

- 다른 다섯 칸은 흰 글자인데 왜 `papayawhip` 칸만 글자색을 바꾸는가?

### 5. 프로덕션에서는 이름 색상 대신 디자인 토큰을 권하는 이유 (왜)

- 이름을 직접 쓰는 편이 짧은데도 왜 프로덕션에서는 변수(토큰)를 권하는가?

### 6. 이름을 마음대로 지어 쓸 수 있나 (경계)

- `background: banana;` 처럼 목록에 없는 단어를 쓰면 그 단어가 색이 되는가?

### 7. 이름 하나로 색을 조금만 바꿀 수 있나 (경계)

- `coral` 보다 살짝 어두운 색이 필요할 때, 이름 색상만으로 해결할 수 있는가?

### 8. 이름 색상과 CSS 변수는 어떻게 같이 쓰이나 (연결)

- 이름 색상을 디자인 토큰 방식으로 쓰려면 이름을 어디에 두고 어떻게 가져다 쓰는가?

## 실습

### 실습 1. 이름 색상 견본판 만들기

**만들 것** — 이름 색상 여섯 개를 3칸짜리 줄 두 개에 견본(스와치)으로 늘어놓고, 각 칸에 그 색 이름을 글자로 적는다.

**요구 조건**
1. 바깥 상자 `.named-demo` 안에 `.row` 줄 두 개를 둔다.
2. 첫 줄의 세 칸은 각각 `tomato` · `cornflowerblue` · `mediumseagreen` 을, 둘째 줄의 세 칸은 `slateblue` · `coral` · `papayawhip` 을 배경색으로 쓴다.
3. 배경색은 칸마다 인라인 `style` 속성으로 이름 색상을 써서 준다.
4. 각 칸의 글자는 그 칸의 색 이름이다.
5. `.row` 안의 칸들은 가로로 놓이고, 칸 사이에 간격이 있다.
6. 한 줄의 칸들은 남는 너비를 똑같이 나눠 같은 너비가 된다.
7. 두 줄 사이에는 간격이 있고, 마지막 줄 아래에는 여백이 없다.
8. 모든 칸의 기본 글자는 흰색이고 그림자가 있다.
9. 매우 옅은 `papayawhip` 칸에만 `dark` 클래스를 붙여 어두운 글자 · 그림자 없음으로 바꾼다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>Named colors</title>
<style>
.named-demo {
  padding: 16px;
  background: #f1f5f9;
  border-radius: 8px;
}

.row {
  /* TODO: 칸을 가로로 놓는다 */
  gap: 8px;
  margin-bottom: 8px;
}

/* TODO: 마지막 줄의 아래 여백을 없앤다 (선택자와 선언 모두) */

.swatch {
  /* TODO: 남는 너비를 칸끼리 똑같이 나눈다 */
  padding: 16px 8px;
  border-radius: 6px;
  color: white;
  font-weight: 600;
  font-size: 13px;
  text-align: center;
  text-shadow: 0 1px 2px rgba(0,0,0,0.2);
}

.swatch.dark {
  color: #1e293b;
  text-shadow: none;
}
</style>
</head>
<body>
<div class="named-demo">
  <div class="row">
    <!-- TODO: 각 칸의 style 에 글자와 같은 이름의 색을 배경으로 준다 -->
    <div class="swatch" style="">tomato</div>
    <div class="swatch" style="">cornflowerblue</div>
    <div class="swatch" style="">mediumseagreen</div>
  </div>
  <div class="row">
    <div class="swatch" style="">slateblue</div>
    <div class="swatch" style="">coral</div>
    <!-- TODO: 옅은 칸에 어두운 글자용 클래스를 더한다 -->
    <div class="swatch" style="">papayawhip</div>
  </div>
</div>
</body>
</html>
```

**확인 방법** — 파일을 브라우저로 열어, 3칸짜리 줄 두 개가 같은 너비로 늘어섰는지, 칸마다 이름과 같은 색이 칠해졌는지, `papayawhip` 칸만 어두운 글자인지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

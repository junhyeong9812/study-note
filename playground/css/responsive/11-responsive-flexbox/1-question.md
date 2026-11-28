# css/responsive/11 — Responsive Flexbox — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 600px 컨테이너의 사이드바와 메인 (예측)

```css
/* 질문용 발췌 — padding 없음 */
.layout  { display: flex; flex-wrap: wrap; gap: 8px; width: 600px; }
.sidebar { flex: 1 1 150px; }
.main    { flex: 2 1 250px; }
```

- 사이드바와 메인의 너비는 각각 몇 px 인가?
- 메인의 너비는 사이드바의 정확히 두 배인가?

### 2. 같은 두 박스를 380px 컨테이너에 (예측)

```css
/* 질문용 발췌 — padding 없음 */
.layout  { display: flex; flex-wrap: wrap; gap: 8px; width: 380px; }
.sidebar { flex: 1 1 150px; }
.main    { flex: 2 1 250px; }
```

- 두 박스는 몇 줄에 놓이고, 각각의 너비는 몇 px 인가?

### 3. 카드 넷을 330px 컨테이너에 (예측)

```css
/* 질문용 발췌 — padding 없음, 카드 4장 */
.cards { display: flex; flex-wrap: wrap; gap: 8px; width: 330px; }
.card  { flex: 1 1 100px; }
```

- 줄마다 카드가 몇 장씩 놓이고, 카드 4의 너비는 몇 px 인가?

### 4. 미디어 쿼리 없이 줄 수가 바뀌는 까닭 (왜)

- 이 패턴에는 `@media` 가 하나도 없는데 화면 폭에 따라 한 줄에 놓이는 아이템 수가 바뀌는 까닭은 무엇인가?

### 5. 「basis 가 컨테이너보다 크면 줄바꿈된다」는 팁의 범위 (경계)

- basis 가 컨테이너보다 큰 아이템 하나는 어디에 놓이고, 그 너비는 basis 와 비교해 어떻게 되나?

### 6. `flex-wrap` 을 빠뜨리면 (경계)

- 1번의 `.layout` 에서 `flex-wrap: wrap` 만 지우고 폭을 380px 로 줄이면 두 박스는 어떻게 놓이나?

### 7. 간격을 `margin` 이 아니라 `gap` 으로 주는 까닭 (왜)

- 줄바꿈되는 카드들의 간격을 각 카드의 `margin-right` 로 주면 왜 번거로운가?

### 8. 미디어 쿼리와 이 패턴의 자리 나누기 (연결)

- 줄바꿈 패턴만으로 부족해 미디어 쿼리가 여전히 필요한 경우는 어떤 경우인가?

## 실습

### 실습 1. 사이드바 + 메인과 균등 카드를 미디어 쿼리 없이 반응형으로

**만들 것** — 창 폭에 따라 사이드바와 메인이 나란히 또는 위아래로 놓이고, 카드 넷이 한 줄에 놓이는 개수가 바뀌는 데모 페이지를 만든다.
미디어 쿼리는 쓰지 않는다.

**요구 조건**

1단계 — 데모 루트
1. 데모 루트(`.rf-demo`)는 flex 컨테이너로, 두 섹션과 코드 박스를 세로로 쌓는다.
2. 루트의 자식 사이 간격은 `gap` 으로 준다(값은 시작 코드 주석에 있다).

2단계 — 사이드바 + 메인 (`.rf-flex-auto`)
3. 컨테이너는 flex 컨테이너이고, 넘치면 다음 줄로 넘긴다.
4. 두 박스 사이 간격은 `gap` 으로 준다.
5. 사이드바(`.rf-item`)는 grow 1 · shrink 1 · basis 150px 이다.
6. 메인(`.rf-item.main`)은 grow 2 · shrink 1 · basis 250px 로, 사이드바의 값을 덮어쓴다.
7. 창이 넓으면 둘이 한 줄에 놓이고 메인이 남는 공간을 더 받으며, 좁으면 위아래로 나뉜다.

3단계 — 균등 카드 (`.rf-flex-cards`)
8. 카드 넷을 담은 컨테이너는 flex 컨테이너이고, 넘치면 다음 줄로 넘긴다.
9. 카드 사이 간격은 `gap` 으로 준다.
10. 모든 카드(`.rf-card`)는 grow · shrink 가 1이고 basis 가 100px 라, 남는 공간을 똑같이 나눈다.

4단계 — 코드 박스
11. 맨 아래 코드 박스에 이 패턴의 CSS 요약을 줄바꿈과 공백을 살린 채 보인다(내용은 시작 코드에 있다).

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>Responsive Flexbox 연습</title>
<style>
  .rf-demo {
    font-family: system-ui, sans-serif;
    /* TODO: flex 컨테이너로 만들고 세로로 쌓는다 */
    /* TODO: 간격 14px 를 gap 으로 */
  }
  .rf-section { background: #f1f5f9; border-radius: 8px; padding: 12px; }
  .rf-label { font-size: 12px; font-weight: 700; color: #475569; margin-bottom: 8px; }
  .rf-flex-auto {
    /* TODO: flex 컨테이너 + 줄바꿈 허용 */
    /* TODO: 간격 8px 를 gap 으로 */
  }
  .rf-item {
    background: #8b5cf6; color: white; padding: 16px; border-radius: 6px;
    font-weight: 600; font-size: 13px; text-align: center;
    /* TODO: grow · shrink · basis 를 flex 한 줄로 */
  }
  .rf-item.main {
    background: #3b82f6;
    /* TODO: 메인의 grow · shrink · basis */
  }
  .rf-flex-cards {
    /* TODO: flex 컨테이너 + 줄바꿈 허용 */
    /* TODO: 간격 8px 를 gap 으로 */
  }
  .rf-card {
    background: #10b981; color: white; padding: 16px; border-radius: 6px;
    text-align: center; font-weight: 600; font-size: 13px;
    /* TODO: 카드의 grow · shrink · basis */
  }
  .rf-code { background: #1e293b; border-radius: 8px; padding: 14px; }
  .rf-code code { font-size: 11px; color: #e2e8f0; white-space: pre; line-height: 1.5; display: block; }
</style>
</head>
<body>
<div class="rf-demo">
  <div class="rf-section">
    <div class="rf-label">flex-wrap + flex-basis 자동 줄바꿈</div>
    <div class="rf-flex-auto">
      <div class="rf-item">사이드바</div>
      <div class="rf-item main">메인 콘텐츠</div>
    </div>
  </div>
  <div class="rf-section">
    <div class="rf-label">균등 분배 카드 (미디어 쿼리 없이)</div>
    <div class="rf-flex-cards">
      <div class="rf-card">카드 1</div>
      <div class="rf-card">카드 2</div>
      <div class="rf-card">카드 3</div>
      <div class="rf-card">카드 4</div>
    </div>
  </div>
  <div class="rf-code">
    <code>/* 사이드바 + 메인: 자동 줄바꿈 */
.layout { display: flex; flex-wrap: wrap; }
.sidebar { flex: 1 1 200px; } /* 최소 200px */
.main { flex: 2 1 400px; }    /* 2배 비율 */

/* 균등 카드: 최소 150px 보장 */
.cards { display: flex; flex-wrap: wrap; gap: 12px; }
.card { flex: 1 1 150px; }</code>
  </div>
</div>
</body>
</html>
```

**확인 방법** — 파일을 브라우저로 열고 창 폭을 넓혔다 좁혔다 하면서, 사이드바와 메인이 한 줄에서 두 줄로 바뀌는지, 카드가 한 줄에 놓이는 개수가 바뀌고 마지막 줄 카드가 넓어지는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

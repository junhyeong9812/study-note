# css/responsive/08 — Mobile-first vs Desktop-first — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. mobile-first 예를 너비 900px 에서 보면 (예측)

```css
/* 질문용 발췌 */
.nav { flex-direction: column; }
@media (min-width: 768px)  { .nav { flex-direction: row; } }
@media (min-width: 1024px) { .nav { gap: 24px; } }
```

- 너비 900px 에서 `.nav` 의 `flex-direction` 과 `gap` 은 각각 무엇이 되는가?

### 2. desktop-first 예를 너비 500px 에서 보면 (예측)

```css
/* 질문용 발췌 */
.nav { flex-direction: row; gap: 24px; }
@media (max-width: 1023px) { .nav { gap: 12px; } }
@media (max-width: 767px)  { .nav { flex-direction: column; } }
```

- 너비 500px 에서 참인 쿼리는 몇 개이고, `.nav` 의 `flex-direction` 과 `gap` 은 무엇이 되는가?

### 3. 경계 바로 위 · 아래 (예측)
- 1번의 mobile-first 예에서 너비가 정확히 768px 일 때와 767px 일 때 `flex-direction` 은 각각 무엇인가?

### 4. 두 접근법이 쓰는 조건이 다른 까닭 (왜)
- mobile-first 는 `min-width` 를, desktop-first 는 `max-width` 를 쓰는 까닭은 무엇인가?

### 5. 원본이 꼽은 desktop-first 의 단점 (왜)
- 기본을 데스크톱으로 두면 왜 모바일에서 오버라이드가 늘어나는가?

### 6. `min-width` 블록의 순서를 뒤집으면 (경계)
- mobile-first 에서 `min-width: 1024px` 블록을 `min-width: 768px` 블록보다 앞에 적으면, 어떤 경우에 결과가 깨지고 어떤 경우에 멀쩡한가?

### 7. desktop-first 쪽 경계가 767 · 1023 인 까닭 (경계)
- desktop-first 예가 `max-width: 768px` 대신 `max-width: 767px` 을 쓰지 않았다면, 어느 너비에서 무슨 일이 생기는가?

### 8. mobile-first 와 점진적 향상 (연결)
- mobile-first 의 「작은 화면부터 쌓아 올리기」는 점진적 향상이라는 설계 방식과 어떻게 이어지는가?

## 실습

### 실습 1. 두 접근법을 나란히 비교하는 카드 만들기

**만들 것** — mobile-first 와 desktop-first 를 두 칼럼으로 나란히 놓고, 칼럼마다 뱃지 · CSS 코드 예 · 장단점 목록을 보여 주는 비교 페이지를 만든다.
창이 좁아지면 두 칼럼이 위아래로 줄을 바꾼다.

**요구 조건**
1. 비교 영역(`.mf-comparison`)은 두 칼럼을 flex 로 가로로 늘어놓고, 칼럼 사이에 간격을 두며, 자리가 모자라면 다음 줄로 넘긴다.
2. 각 칼럼(`.mf-col`)은 남은 폭을 같은 비율로 나눠 갖되, 정해진 최소 폭 아래로는 줄어들지 않는다 — 그래서 창이 좁으면 줄바꿈이 일어난다.
3. 첫 칼럼에는 `mobile-first` 클래스, 둘째 칼럼에는 `desktop-first` 클래스를 붙여 테두리 색으로 구분한다.
4. 칼럼 맨 위의 뱃지(`.mf-badge`)는 글자 폭만큼만 차지한다. 둘째 칼럼의 뱃지에는 `df` 클래스를 더 붙인다.
5. 첫 칼럼의 코드 블록에는 기본(세로) → 768 이상에서 가로 → 1024 이상에서 간격 넓힘의 세 단계를 `min-width` 쿼리로 적는다.
6. 둘째 칼럼의 코드 블록에는 기본(가로 + 넓은 간격) → 1023 이하에서 간격 좁힘 → 767 이하에서 세로의 세 단계를 `max-width` 쿼리로 적는다.
7. 코드 블록 안의 글(`.mf-code code`)은 공백과 줄바꿈을 그대로 보존하고, 블록 요소로 보인다.
8. 장단점 목록(`.mf-pros`)은 flex 로 항목을 세로로 쌓고 항목 사이에 간격을 둔다. 첫 칼럼의 항목은 `pro`, 둘째 칼럼의 항목은 `con` 클래스다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>Mobile-first vs Desktop-first</title>
<style>
  .mf-demo { font-family: system-ui, sans-serif; }
  .mf-comparison {
    /* TODO: 가로 flex 배치 · 칼럼 간격 12px · 좁으면 줄바꿈 */
  }
  .mf-col {
    /* TODO: 같은 비율로 늘어나기 · 최소 폭 220px */
    background: #f8fafc;
    border-radius: 10px;
    padding: 14px;
    border: 2px solid #e2e8f0;
  }
  .mf-col.mobile-first { border-color: #22c55e; }
  .mf-col.desktop-first { border-color: #f59e0b; }
  .mf-badge {
    /* TODO: 글자 폭만 차지하게 */
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 700;
    background: #dcfce7;
    color: #166534;
    margin-bottom: 10px;
  }
  .mf-badge.df { background: #fef3c7; color: #92400e; }
  .mf-code { background: #1e293b; border-radius: 6px; padding: 10px; margin-bottom: 10px; }
  .mf-code code {
    font-size: 11px;
    color: #e2e8f0;
    line-height: 1.5;
    /* TODO: 공백 · 줄바꿈 보존, 블록으로 보이게 */
  }
  .mf-pros {
    /* TODO: flex 세로 쌓기 · 항목 간격 4px */
  }
  .pro, .con { font-size: 11px; padding: 4px 8px; border-radius: 4px; }
  .pro { background: #dcfce7; color: #166534; }
  .con { background: #fef3c7; color: #92400e; }
</style>
</head>
<body>
<div class="mf-demo">
  <div class="mf-comparison">
    <div class="mf-col mobile-first">
      <div class="mf-badge">Mobile-first (권장)</div>
      <div class="mf-code">
        <code><!-- TODO: 기본 세로 → min-width 768 가로 → min-width 1024 간격 --></code>
      </div>
      <div class="mf-pros">
        <div class="pro">성능: 모바일에서 불필요한 CSS 로드 최소화</div>
        <div class="pro">점진적 향상(Progressive Enhancement)</div>
        <div class="pro">핵심 콘텐츠 우선 설계</div>
      </div>
    </div>
    <div class="mf-col desktop-first">
      <div class="mf-badge df">Desktop-first</div>
      <div class="mf-code">
        <code><!-- TODO: 기본 가로+간격 → max-width 1023 간격 좁힘 → max-width 767 세로 --></code>
      </div>
      <div class="mf-pros">
        <div class="con">모바일에서 불필요한 CSS 오버라이드 증가</div>
        <div class="con">레거시 프로젝트 마이그레이션에 적합</div>
        <div class="con">데스크톱 중심 디자인 시 직관적</div>
      </div>
    </div>
  </div>
</div>
</body>
</html>
```

**확인 방법** — 브라우저로 파일을 열어 두 칼럼이 나란히 놓이는지, 코드 블록의 줄바꿈 · 들여쓰기가 그대로 보이는지 확인한다. 창 폭을 줄여 두 칼럼이 위아래로 줄을 바꾸는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

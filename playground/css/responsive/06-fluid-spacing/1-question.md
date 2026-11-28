# css/responsive/06 — Fluid Spacing — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 뷰포트 400px 에서 카드 패딩 (예측)

```css
/* 질문용 발췌 — 1rem = 16px 로 가정 */
.fs-card { padding: clamp(0.75rem, 0.5rem + 1vw, 1.5rem); }
```

- 뷰포트 폭이 400px 일 때 카드의 패딩은 몇 px 인가?
- 뷰포트를 300px 로 줄이면 그 값은 어떻게 되나?

### 2. 아주 넓은 화면에서 카드 사이 간격 (예측)

```css
/* 질문용 발췌 — 1rem = 16px 로 가정 */
.fs-section { gap: clamp(0.75rem, 0.5rem + 1.5vw, 2rem); }
```

- 뷰포트 폭이 2000px 일 때 카드 사이 간격은 몇 px 인가?

### 3. 스케일의 중간 단계 (예측)

```css
/* 질문용 발췌 — 1rem = 16px 로 가정 */
:root { --space-m: clamp(1rem, 0.7rem + 1.5vw, 2rem); }
.section { gap: var(--space-m); }
```

- 뷰포트 폭이 1000px 일 때 `.section` 의 `gap` 은 몇 px 인가?

### 4. 가운데 값에 `rem` 과 `vw` 를 섞는 까닭 (왜)

- 가운데 값을 `1.5vw` 하나가 아니라 `0.5rem + 1.5vw` 처럼 고정값과 비례값의 합으로 쓰는 까닭은 무엇인가?

### 5. 미디어 쿼리 없이도 「부드럽다」고 하는 까닭 (왜)

- 미디어 쿼리로 여백을 바꾸는 방식과 비교해 `clamp()` 방식이 부드럽게 변한다고 하는 까닭은 무엇인가?

### 6. 좁은 사이드바 안의 카드 (경계)

- 카드를 담은 상자가 아주 좁아도 창이 넓으면 `vw` 기반 여백이 크게 잡히는 까닭은 무엇인가?

### 7. 카드가 다음 줄로 내려가는 조건 (경계)

- 예제에서 카드가 다음 줄로 넘어가게 만드는 것은 `clamp()` 인가, 다른 속성인가?

### 8. 커스텀 프로퍼티 스케일과 여러 속성 (연결)

- `--space-l` · `--space-m` 같은 스케일을 `padding` · `gap` · `margin` 에 함께 걸어 두면 레이아웃 전체에 어떤 이점이 생기나?

## 실습

### 실습 1. 뷰포트에 따라 여백이 변하는 카드 섹션

**만들 것** — 카드 셋을 담은 섹션에서, 섹션의 안쪽 여백 · 카드 사이 간격 · 카드 안쪽 여백 · 제목 아래 여백이 모두 `clamp()` 로 뷰포트 폭을 따라 변하게 한다.
아래에는 간격 스케일 예시를 보여 주는 코드 상자를 둔다.

**요구 조건**

1. 1단계 — 섹션(`.fs-section`)은 flex 컨테이너가 되어 카드를 가로로 늘어놓고, 한 줄에 다 들어가지 않으면 다음 줄로 넘긴다.
2. 1단계 — 카드(`.fs-card`)는 남는 공간을 서로 같은 비율로 나눠 가진다.
3. 1단계 — 카드는 최소 폭 120px 아래로 줄지 않는다(그보다 좁아질 상황이면 줄바꿈된다).
4. 2단계 — 섹션의 카드 사이 간격은 `clamp()` 로 0.75rem ~ 2rem 사이를 오가며, 가운데 값은 `0.5rem + 1.5vw` 다.
5. 2단계 — 섹션의 안쪽 여백은 `clamp()` 로 1rem ~ 2.5rem 사이를 오가며, 가운데 값은 `0.5rem + 2vw` 다.
6. 2단계 — 카드의 안쪽 여백은 `clamp()` 로 0.75rem ~ 1.5rem 사이를 오가며, 가운데 값은 `0.5rem + 1vw` 다.
7. 2단계 — 카드 제목 아래 여백은 `clamp()` 로 4px ~ 10px 사이를 오가며, 가운데 값은 `2px + 0.5vw` 다.
8. 3단계 — 코드 상자에는 `--space-s` · `--space-m` · `--space-l` 스케일과 그 사용 예가 공백 · 줄바꿈을 보존한 채 보인다(시작 코드에 채워 둠).

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>Fluid Spacing</title>
<style>
  .fluid-spacing-demo {
    font-family: system-ui, sans-serif;
  }
  .fs-section {
    /* TODO: flex 컨테이너로 만들고 줄바꿈을 허용한다 */
    /* TODO: 카드 사이 간격을 clamp() 로 유동화한다 */
    /* TODO: 섹션 안쪽 여백을 clamp() 로 유동화한다 */
    background: #f1f5f9;
    border-radius: 12px;
    margin-bottom: 12px;
  }
  .fs-card {
    /* TODO: 남는 공간을 같은 비율로 나눠 갖게 한다 */
    /* TODO: 최소 폭을 정한다 */
    background: white;
    /* TODO: 카드 안쪽 여백을 clamp() 로 유동화한다 */
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  }
  .fs-card-title {
    font-weight: 700;
    font-size: 14px;
    color: #1e293b;
    /* TODO: 제목 아래 여백을 clamp() 로 유동화한다 */
  }
  .fs-card-text {
    font-size: 12px;
    color: #64748b;
    line-height: 1.5;
  }
  .fs-code {
    background: #1e293b;
    border-radius: 8px;
    padding: 14px;
  }
  .fs-code code {
    font-size: 11px;
    color: #e2e8f0;
    white-space: pre;
    line-height: 1.6;
    display: block;
  }
</style>
</head>
<body>
<div class="fluid-spacing-demo">
  <div class="fs-section">
    <div class="fs-card">
      <div class="fs-card-title">카드 1</div>
      <div class="fs-card-text">패딩이 뷰포트에 따라 변합니다</div>
    </div>
    <div class="fs-card">
      <div class="fs-card-title">카드 2</div>
      <div class="fs-card-text">카드 간 간격도 유동적입니다</div>
    </div>
    <div class="fs-card">
      <div class="fs-card-title">카드 3</div>
      <div class="fs-card-text">미디어 쿼리 없이 부드러운 전환</div>
    </div>
  </div>
  <div class="fs-code">
    <code>/* Fluid spacing scale */
--space-s: clamp(0.5rem, 0.3rem + 1vw, 1rem);
--space-m: clamp(1rem, 0.7rem + 1.5vw, 2rem);
--space-l: clamp(1.5rem, 1rem + 2.5vw, 3rem);

.section { padding: var(--space-l); gap: var(--space-m); }</code>
  </div>
</div>
</body>
</html>
```

**확인 방법** — 브라우저로 열고 창 폭을 천천히 줄였다 늘린다.
카드 사이 · 섹션 안쪽 · 카드 안쪽 · 제목 아래 여백이 계단 없이 함께 변하는지, 아주 좁거나 아주 넓을 때는 더 변하지 않는지 본다.
개발자 도구의 계산된 스타일(Computed)에서 `padding` · `gap` 값이 범위 안에 있는지 확인한다.
창을 충분히 좁히면 카드가 다음 줄로 넘어가는지도 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

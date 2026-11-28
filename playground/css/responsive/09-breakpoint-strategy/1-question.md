# css/responsive/09 — Breakpoint Strategy — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 마커 하나의 가운데는 어디에 오나 (예측)

```html
<!-- 질문용 발췌 -->
<div class="bp-markers" style="position: relative; width: 500px;">
  <div class="bp-mark" style="position: absolute; left: 40%; transform: translateX(-50%);">768px</div>
</div>
```

- 마커 상자의 가로 가운데는 `.bp-markers` 왼쪽 끝에서 몇 px 떨어진 곳에 오나?
- `transform` 줄을 지우면 그 자리에 오는 것은 마커의 어느 부분인가?

### 2. 구간 비율과 640px 마커 좌표 (예측)

```css
/* 질문용 발췌 */
.bp-bar { display: flex; }
.bp-segment.mobile { flex: 2.4; }
.bp-segment.tablet, .bp-segment.laptop,
.bp-segment.desktop, .bp-segment.wide { flex: 1.6; }
/* 640px 마커는 left: 24% */
```

- Mobile 구간은 막대 폭의 몇 % 쯤을 차지하나?
- 640px 마커는 Mobile 과 Tablet 의 경계 위에 정확히 오나?

### 3. `min-width: 768px` 의 경계 (경계)

- 뷰포트 너비가 정확히 768px 일 때 `@media (min-width: 768px)` 안의 규칙은 적용되나, 안 되나?

### 4. 디바이스 대신 콘텐츠로 값을 고르는 까닭 (왜)

- 기기 너비 목록이 아니라 콘텐츠가 깨지는 지점을 브레이크포인트로 잡아야 하는 까닭은 무엇인가?

### 5. 커스텀 프로퍼티 대신 Sass 변수 · custom media 를 권하는 까닭 (왜)

- 원본 팁이 브레이크포인트 값을 CSS 커스텀 프로퍼티로 관리하기 어렵다고 하는 까닭은 무엇인가?

### 6. 브레이크포인트를 늘릴수록 (경계)

- 원본이 보는 적정 개수는 몇 개이고, 그보다 많아지면 무엇이 어려워지나?

### 7. 데모 막대를 눈금자로 읽어도 되나 (경계)

- 데모의 마커 좌표(0 · 24% · 40% · 56% · 72% · 88%)는 px 값에 비례하는 눈금인가?

### 8. Tailwind 기본값과 Marcotte 의 조언 (연결)

- Tailwind 기본 브레이크포인트를 쓰는 일과 「창을 줄여 깨지는 지점을 찾으라」는 조언은 한 프로젝트 안에서 어떻게 이어지나?

## 실습

### 실습 1. 브레이크포인트 눈금 · 팁 · 코드 예시를 한 화면에 그리기

**만들 것** — Tailwind 기본 브레이크포인트를 색 막대와 눈금 마커로 보이고, 그 아래 브레이크포인트 전략 팁 세 개와 값 관리 코드 예시를 놓는 정적 페이지.

**요구 조건**

1단계 — 눈금 막대
1. `.bp-bar` 안 다섯 구간(Mobile · Tablet · Laptop · Desktop · Wide)이 한 줄로 가로로 늘어선다.
2. 각 구간의 라벨은 구간 안에서 가로 · 세로 가운데에 놓인다.
3. Mobile 구간은 나머지 구간보다 1.5배 넓고, 나머지 네 구간은 서로 같은 폭이다(`flex` 비율로).

2단계 — 눈금 마커
4. `.bp-markers` 가 마커들의 절대 배치 기준 상자가 된다.
5. 마커는 여섯 개다 — `0` 하나와, Tailwind 기본 브레이크포인트 다섯 개(값과 `sm` ~ `2xl` 이름을 두 줄로).
6. 마커는 인라인 `left` 백분율 0 · 24% · 40% · 56% · 72% · 88% 에 차례로 놓인다.
7. 각 마커는 자기 폭의 절반만큼 왼쪽으로 옮겨, `left` 좌표가 마커의 가운데가 되게 한다.

3단계 — 팁 상자
8. 팁 상자 세 개가 세로로 쌓인다.
9. 팁 내용은 차례로 — 값 관리(커스텀 프로퍼티는 어렵고 Sass 변수 · PostCSS custom media 를 쓴다) · 콘텐츠가 깨지는 지점에 설정(그 구절은 `strong` 으로 강조) · 적정 개수 3~5개.

4단계 — 코드 예시
10. `@custom-media` 로 `--sm` · `--md` · `--lg` 를 `min-width` 조건으로 정의한 세 줄과, 같은 세 값을 Sass 변수 `$bp-sm` · `$bp-md` · `$bp-lg` 로 둔 세 줄을 각각 주석 제목 아래에 쓴다.
11. 코드 상자 안의 공백과 줄바꿈이 쓴 그대로 보인다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>Breakpoint Strategy</title>
<style>
  .bp-demo { font-family: system-ui, sans-serif; }
  .bp-scale { margin-bottom: 16px; }
  .bp-bar {
    height: 36px; border-radius: 8px; overflow: hidden;
    /* TODO: 구간을 가로로 늘어놓는다 */
  }
  .bp-segment {
    color: white; font-size: 11px; font-weight: 600;
    /* TODO: flex 로 라벨을 가로·세로 가운데에 */
  }
  .bp-segment.mobile  { background: #ef4444; /* TODO: 폭 비율 */ }
  .bp-segment.tablet  { background: #f59e0b; /* TODO: 폭 비율 */ }
  .bp-segment.laptop  { background: #22c55e; /* TODO: 폭 비율 */ }
  .bp-segment.desktop { background: #3b82f6; /* TODO: 폭 비율 */ }
  .bp-segment.wide    { background: #8b5cf6; /* TODO: 폭 비율 */ }
  .bp-markers {
    height: 36px; margin-top: 4px;
    /* TODO: 마커들의 좌표 기준 상자 */
  }
  .bp-mark {
    font-size: 10px; color: #64748b; text-align: center; line-height: 1.3;
    /* TODO: 기준 상자 안 절대 배치 + 자기 폭 절반만큼 왼쪽으로 */
  }
  .bp-mark strong { color: #1e293b; }
  .bp-tips {
    gap: 4px; margin: 40px 0 12px;
    /* TODO: 팁을 세로로 쌓는다 */
  }
  .bp-tip {
    font-size: 12px; padding: 6px 10px; background: #eff6ff;
    border-left: 3px solid #3b82f6; border-radius: 0 4px 4px 0; color: #1e3a5f;
  }
  .bp-code { background: #1e293b; border-radius: 8px; padding: 14px; }
  .bp-code code {
    font-size: 11px; color: #e2e8f0; line-height: 1.5; display: block;
    /* TODO: 공백·줄바꿈을 그대로 보존 */
  }
</style>
</head>
<body>
<div class="bp-demo">
  <div class="bp-scale">
    <div class="bp-bar">
      <div class="bp-segment mobile"><span>Mobile</span></div>
      <div class="bp-segment tablet"><span>Tablet</span></div>
      <div class="bp-segment laptop"><span>Laptop</span></div>
      <div class="bp-segment desktop"><span>Desktop</span></div>
      <div class="bp-segment wide"><span>Wide</span></div>
    </div>
    <div class="bp-markers">
      <div class="bp-mark" style="left: 0"><strong>0</strong></div>
      <!-- TODO: sm ~ 2xl 마커 다섯 개 (값은 <strong>, <br> 다음에 이름) -->
    </div>
  </div>
  <div class="bp-tips">
    <!-- TODO: 팁 상자 세 개 (.bp-tip) -->
  </div>
  <div class="bp-code">
    <code><!-- TODO: custom media 세 줄 + Sass 변수 세 줄 --></code>
  </div>
</div>
</body>
</html>
```

**확인 방법** — 파일을 브라우저로 열어, 다섯 색 구간이 한 줄로 서 있는지, 마커 숫자가 좌표를 가운데로 두고 놓였는지, 팁 셋이 세로로 쌓였는지, 코드 상자의 줄바꿈이 쓴 그대로인지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

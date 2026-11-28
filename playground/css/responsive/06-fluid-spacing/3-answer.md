# css/responsive/06 — Fluid Spacing — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 400px 에서 12px, 300px 에서도 12px — 최솟값에 묶인다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

400px: 가운데 값 = 0.5rem + 1vw = 8px + 4px = 12px.
최솟값 0.75rem(12px)과 같으므로 12px 이다.
300px: 가운데 값 = 8px + 3px = 11px.
최솟값 12px 보다 작으므로 12px 로 묶인다.

**왜 그런가**

`clamp()` 는 가운데 값이 최솟값보다 작으면 최솟값을 쓴다.
카드 패딩은 뷰포트 400px 에서 바닥에 닿으므로, 그보다 좁아져도 더 줄지 않는다.
근거: 2-summary 「동작 방식 (1)」의 표 · 「동작 방식 (2)」의 「최소에 닿는 폭」.

### 2. 32px — 최댓값에 묶인다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

가운데 값 = 0.5rem + 1.5vw = 8px + 30px = 38px.
최댓값 2rem(32px)보다 크므로 32px 이다.

**왜 그런가**

`clamp()` 는 가운데 값이 최댓값을 넘으면 최댓값을 쓴다.
이 `gap` 은 뷰포트 1600px 에서 이미 32px 에 닿으므로, 그 위로는 창을 넓혀도 그대로다.
근거: 2-summary 「동작 방식 (2)」의 표.

### 3. 26.2px — 범위 안이라 가운데 값을 그대로 쓴다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

가운데 값 = 0.7rem + 1.5vw = 11.2px + 15px = 26.2px.
범위 16px ~ 32px 안이므로 26.2px 이다.

**왜 그런가**

`var(--space-m)` 자리에 `clamp(...)` 식이 그대로 들어가고, 그 자리에서 지금의 뷰포트 폭으로 계산된다.
값이 최솟값과 최댓값 사이면 `clamp()` 는 가운데 값을 바꾸지 않는다.
근거: 2-summary 「동작 방식 (3)」.

### 4. 바닥과 기울기를 따로 정하고, 글꼴 설정도 따르게 하려고

`rem` 부분은 직선의 출발 높이(바닥)를, `vw` 부분은 기울기를 정한다.
둘을 섞으면 「어느 폭에서 최솟값 · 최댓값에 닿는지」를 원하는 대로 맞출 수 있다.
또 `rem` 이 섞여 있으면 사용자가 브라우저 글꼴을 키울 때 여백도 함께 커진다.
`vw` 만 쓰면 화면 폭만 따르고 글꼴 설정은 무시한다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 5」.

### 5. 정해 둔 폭에서 뛰지 않고 모든 폭에서 조금씩 변하기 때문에

미디어 쿼리는 브레이크포인트에서 값이 한 번에 바뀌는 계단 모양이다.
`clamp()` 의 가운데 값은 뷰포트 폭에 비례하는 직선이라, 최솟값 · 최댓값 사이에서는 폭이 1px 바뀔 때마다 여백도 조금씩 바뀐다.
그래서 뛰는 지점이 없다.
근거: 2-summary 「동작 방식 (4)」.

### 6. `vw` 는 상자가 아니라 브라우저 창의 폭을 기준으로 하기 때문에

`1vw` 는 뷰포트 폭의 1% 다.
카드를 담은 상자의 폭은 계산에 들어가지 않는다.
그래서 창이 넓으면 좁은 사이드바 안에서도 여백이 크게 잡힌다.
근거: 2-summary 「어디서 틀리나 4」.

### 7. 다른 속성 — `flex-wrap: wrap` 과 `min-width: 120px` 이다

`clamp()` 는 간격의 크기만 바꾼다.
카드는 `flex: 1` 로 공간을 나눠 갖다가, 120px 아래로 줄어야 할 상황이 되면 `flex-wrap: wrap` 때문에 다음 줄로 넘어간다.
다만 `gap` 이 커지면 한 줄에 필요한 폭이 늘므로 줄바꿈 시점에 간접적으로 영향을 준다.
근거: 2-summary 「동작 방식 (5)」.

### 8. 모든 여백이 같은 단계 · 같은 비율로 함께 줄고 늘어난다

스케일을 쓰면 「큰 여백」은 모두 같은 `--space-l` 을, 「중간 여백」은 모두 같은 `--space-m` 을 따른다.
그래서 여백마다 바닥에 닿는 폭이 제각각이 되는 일이 줄고, 단계 하나를 고치면 그것을 쓰는 모든 곳이 한꺼번에 바뀐다.
`padding` · `gap` · `margin` 을 모두 유동화해 두면 어느 하나만 고정되어 어긋나 보이는 일도 막는다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 1」 · 「어디서 틀리나 3」.

## 실습 정답

### 실습 1. 뷰포트에 따라 여백이 변하는 카드 섹션

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 섹션을 flex 로, 줄바꿈 허용 | `.fs-section { display: flex; flex-wrap: wrap; }` |
| 2. 카드가 공간을 같은 비율로 나눔 | `.fs-card { flex: 1; }` |
| 3. 카드 최소 폭 | `.fs-card { min-width: 120px; }` |
| 4. 카드 사이 간격 유동 | `.fs-section { gap: clamp(0.75rem, 0.5rem + 1.5vw, 2rem); }` |
| 5. 섹션 안쪽 여백 유동 | `.fs-section { padding: clamp(1rem, 0.5rem + 2vw, 2.5rem); }` |
| 6. 카드 안쪽 여백 유동 | `.fs-card { padding: clamp(0.75rem, 0.5rem + 1vw, 1.5rem); }` |
| 7. 제목 아래 여백 유동 | `.fs-card-title { margin-bottom: clamp(4px, 2px + 0.5vw, 10px); }` |
| 8. 스케일 예시 상자 | `.fs-code code { white-space: pre; display: block; }` 와 `<code>` 안의 `--space-s/m/l` 글 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/responsive/reference/fluid-spacing.html`

```html
<!-- DOCTYPE: HTML5 -->
<!DOCTYPE html>
<!-- 한국어 문서 -->
<html lang="ko">
<!-- 메타데이터 -->
<head>
<!-- UTF-8 -->
<meta charset="utf-8">
<!-- 탭 제목 -->
<title>Fluid Spacing - clamp()로 뷰포트 크기에 따라 자연스럽게 변하는 여백과 패딩을 설정한다. 브레이크포인트 없이 부드러운 반응형 간격 구현.</title>
<!--
  [반응형 디자인] Fluid Spacing
  설명: clamp()로 뷰포트 크기에 따라 자연스럽게 변하는 여백과 패딩을 설정한다. 브레이크포인트 없이 부드러운 반응형 간격 구현.

  팁: CSS 커스텀 프로퍼티로 spacing scale을 정의하면 일관된 간격 시스템을 유지할 수 있다. utopia.fyi에서 spacing scale도 자동 생성 가능. gap, padding, margin 모두에 clamp()를 적용하면 레이아웃이 자연스럽게 축소/확대된다.
-->
<style>
  /* .fluid-spacing-demo: 데모 루트 */
  .fluid-spacing-demo {
    font-family: system-ui, sans-serif;   /* 시스템 폰트 */
  }
  /* .fs-section: 카드들을 담는 섹션 - 패딩과 gap을 clamp로 유동화 */
  .fs-section {
    display: flex;                        /* flex 컨테이너 */
    flex-wrap: wrap;                      /* 좁아지면 줄바꿈 */
    gap: clamp(0.75rem, 0.5rem + 1.5vw, 2rem); /* 카드 사이 간격: 12px ~ 32px 사이에서 뷰포트에 따라 유동 */
    padding: clamp(1rem, 0.5rem + 2vw, 2.5rem); /* 섹션 패딩: 16px ~ 40px 사이 유동 */
    background: #f1f5f9;                  /* 옅은 슬레이트 배경 */
    border-radius: 12px;                  /* 둥근 모서리 */
    margin-bottom: 12px;                  /* 코드 박스와 간격 */
  }
  /* .fs-card: 개별 카드 - 패딩도 유동적 */
  .fs-card {
    flex: 1;                              /* 동일 비율로 가용 공간 분배 */
    min-width: 120px;                     /* 최소 폭 120px - 더 좁아지면 줄바꿈 */
    background: white;                    /* 흰 배경 */
    padding: clamp(0.75rem, 0.5rem + 1vw, 1.5rem); /* 12px ~ 24px 사이 유동 패딩 */
    border-radius: 8px;                   /* 둥근 모서리 */
    box-shadow: 0 1px 3px rgba(0,0,0,0.08); /* 약한 그림자 */
  }
  /* .fs-card-title: 카드 제목 */
  .fs-card-title {
    font-weight: 700;                     /* 굵게 */
    font-size: 14px;                      /* 약간 큰 본문 */
    color: #1e293b;                       /* 어두운 색 */
    margin-bottom: clamp(4px, 2px + 0.5vw, 10px); /* 제목과 본문 사이 간격도 유동: 4 ~ 10px */
  }
  /* .fs-card-text: 카드 본문 */
  .fs-card-text {
    font-size: 12px;                      /* 작은 본문 */
    color: #64748b;                       /* 회색 */
    line-height: 1.5;                     /* 줄 간격 */
  }
  /* .fs-code: 코드 예시 박스(다크) */
  .fs-code {
    background: #1e293b;                  /* 어두운 배경 */
    border-radius: 8px;                   /* 둥근 모서리 */
    padding: 14px;                        /* 내부 여백 */
  }
  /* .fs-code code: 코드 텍스트 */
  .fs-code code {
    font-size: 11px;                      /* 작은 폰트 */
    color: #e2e8f0;                       /* 밝은 글자 */
    white-space: pre;                     /* 공백/개행 보존 */
    line-height: 1.6;                     /* 줄 간격 */
    display: block;                       /* 블록 표시 */
  }
</style>
</head>
<body>
<!-- 데모 루트 -->
<div class="fluid-spacing-demo">
  <!-- 카드 섹션(유동 패딩과 gap 적용) -->
  <div class="fs-section">
    <!-- 카드 1 -->
    <div class="fs-card">
      <!-- 제목 -->
      <div class="fs-card-title">카드 1</div>
      <!-- 설명 -->
      <div class="fs-card-text">패딩이 뷰포트에 따라 변합니다</div>
    </div>
    <!-- 카드 2 -->
    <div class="fs-card">
      <!-- 제목 -->
      <div class="fs-card-title">카드 2</div>
      <!-- 설명 -->
      <div class="fs-card-text">카드 간 간격도 유동적입니다</div>
    </div>
    <!-- 카드 3 -->
    <div class="fs-card">
      <!-- 제목 -->
      <div class="fs-card-title">카드 3</div>
      <!-- 설명 -->
      <div class="fs-card-text">미디어 쿼리 없이 부드러운 전환</div>
    </div>
  </div>
  <!-- 코드 예시 -->
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

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.fluid-spacing-demo { font-family: system-ui, sans-serif; }
.fs-section { display: flex; flex-wrap: wrap; gap: clamp(0.75rem, 0.5rem + 1.5vw, 2rem); padding: clamp(1rem, 0.5rem + 2vw, 2.5rem); background: #f1f5f9; border-radius: 12px; margin-bottom: 12px; }
.fs-card { flex: 1; min-width: 120px; background: white; padding: clamp(0.75rem, 0.5rem + 1vw, 1.5rem); border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.fs-card-title { font-weight: 700; font-size: 14px; color: #1e293b; margin-bottom: clamp(4px, 2px + 0.5vw, 10px); }
.fs-card-text { font-size: 12px; color: #64748b; line-height: 1.5; }
.fs-code { background: #1e293b; border-radius: 8px; padding: 14px; }
.fs-code code { font-size: 11px; color: #e2e8f0; white-space: pre; line-height: 1.6; display: block; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**

- 유동 여백은 넷 다 「`rem` 바닥 + `vw` 기울기」를 `clamp()` 로 가둔 꼴이다.
- `gap` 은 약 267px, 나머지 셋은 400px 에서 최솟값에 닿고, 넷 다 1600px 에서 최댓값에 닿는다(1rem = 16px 가정).
- 제목 아래 여백만 `px` 으로 써서 루트 글꼴 크기를 따르지 않는다.
- 줄바꿈은 `clamp()` 가 아니라 `flex-wrap: wrap` 과 `min-width` 가 만든다.
- 코드 상자의 `--space-s/m/l` 스케일은 글로 보여 줄 뿐, 이 데모의 CSS 에는 적용되지 않았다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

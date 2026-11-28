# css/responsive/09 — Breakpoint Strategy — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 가운데는 200px 에 온다 — `transform` 이 없으면 왼쪽 끝이 온다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

마커의 가로 가운데는 `.bp-markers` 왼쪽 끝에서 200px 떨어진 곳에 온다.
`transform` 줄을 지우면 200px 자리에 오는 것은 마커의 **왼쪽 끝**이다.

**왜 그런가**

`left: 40%` 의 백분율은 기준 상자(`position: relative` 인 `.bp-markers`) 폭 기준이라 500 × 0.4 = 200px 이다.
`left` 는 마커의 왼쪽 끝을 그 좌표에 둔다.
`translateX(-50%)` 의 백분율은 마커 자기 폭 기준이라, 자기 폭의 절반만큼 왼쪽으로 옮겨 가운데가 200px 에 맞는다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 6」.

### 2. Mobile 은 약 27.3% — 640px 마커(24%)와 경계가 어긋난다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

Mobile 구간은 막대 폭의 약 27.3% 를 차지한다.
640px 마커는 경계 위에 정확히 오지 않고, 경계보다 3% 남짓 왼쪽에 놓인다.

**왜 그런가**

`flex` 값의 합은 2.4 + 1.6 × 4 = 8.8 이다.
Mobile 폭은 2.4 / 8.8 ≈ 0.273, 곧 약 27.3% 다.
마커는 `left: 24%` 에 가운데가 오므로 경계(27.3%)와 맞지 않는다.
2.4 : 1.6 = 1.5 이므로 「Mobile 이 1.5배 넓다」는 원본 주석은 맞다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 5」. 경계가 어긋난다는 판단은 코드를 읽어 계산한 것이다(원본에 근거 없음 — 추론).

### 3. 적용된다 — `min-width` 는 경계값을 포함한다

`min-width: 768px` 는 「너비 768px **이상**」일 때 참이므로 정확히 768px 에서도 규칙이 적용된다.
그래서 「768px 부터 바뀐다」고 읽는다.
근거: 2-summary 「동작 방식 (1)」 · 「문법 — 형태와 규칙」.

### 4. 기기 너비는 계속 바뀌고, 그 사이 너비에서도 콘텐츠가 깨지기 때문이다

기기 너비는 기기마다 다르고 새 기기가 나올 때마다 바뀌어, 기기 목록에 맞춘 값은 금방 낡는다.
사용자는 기기 너비 「사이」의 어떤 너비로도 볼 수 있어서, 기기에 맞춘 값으로는 그 사이에서 깨지는 곳을 놓친다.
콘텐츠가 실제로 깨지는 지점을 값으로 삼으면 어느 너비에서도 깨지지 않게 된다 — Ethan Marcotte 의 「창을 줄여 깨지는 지점을 찾으라」는 조언이다.
근거: 2-summary 「동작 방식 (2)」.

### 5. 미디어 쿼리 조건 안에서는 `var()` 를 쓸 수 없기 때문이다

커스텀 프로퍼티는 요소에 적용되는 값이고, 미디어 쿼리 조건은 요소와 상관없이 판단된다.
그래서 `@media (min-width: var(--bp-md))` 처럼 쓸 수 없다.
Sass 변수와 PostCSS `@custom-media` 는 빌드 때 숫자로 바뀌므로 값을 한 곳에 모아 두고도 미디어 쿼리에 넣을 수 있다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 4」.

### 6. 3~5개 — 많아지면 유지보수가 어려워진다

원본은 3~5개를 적정으로 본다.
브레이크포인트가 하나 늘 때마다 확인하고 고쳐야 할 레이아웃이 하나 늘어 유지보수가 어려워진다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 3」.

### 7. 아니다 — px 비례가 아닌 개념 그림이다

마커 좌표는 16%씩 고르게 벌어지지만, 값의 차이는 640 → 768 이 128px, 768 → 1024 가 256px 로 고르지 않다.
게다가 0 → 640 구간은 24% 인데 640 → 768 구간도 16% 를 차지한다.
그래서 이 막대는 「어떤 이름의 구간이 차례로 있다」를 보이는 그림이지 px 눈금자가 아니다.
근거: 2-summary 「어디서 틀리나 5」.

### 8. 기본값으로 출발하고, 창을 줄여 찾은 지점으로 조정한다

Tailwind 기본값(640 · 768 · 1024 · 1280 · 1536)은 가장 보편적인 출발점이다.
그 위에서 창을 줄여 가며 레이아웃이 깨지는 지점을 찾고, 기본값이 그 지점과 어긋나면 값을 옮기거나 합친다.
결과 값은 3~5개로 유지하고 Sass 변수나 `@custom-media` 한 곳에 모은다.
근거: 2-summary 「동작 방식 (2)」 · 「언제 쓰고 언제 안 쓰나」 · 「핵심 문장」.

## 실습 정답

### 실습 1. 브레이크포인트 눈금 · 팁 · 코드 예시를 한 화면에 그리기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 다섯 구간을 가로로 | `.bp-bar { display: flex; }` |
| 2. 라벨을 가로 · 세로 가운데에 | `.bp-segment { display: flex; align-items: center; justify-content: center; }` |
| 3. Mobile 1.5배 · 나머지 같은 폭 | `.bp-segment.mobile { flex: 2.4; }` · 나머지 넷 `flex: 1.6;` |
| 4. 마커의 기준 상자 | `.bp-markers { position: relative; }` |
| 5. 마커 여섯 개(값 + 이름) | `.bp-markers` 안 `.bp-mark` 여섯 개 · `<strong>640px</strong><br>sm` 꼴 |
| 6. `left` 백분율 좌표 | 인라인 `style="left: 0"` · `24%` · `40%` · `56%` · `72%` · `88%` |
| 7. 좌표가 가운데가 되게 | `.bp-mark { position: absolute; transform: translateX(-50%); }` |
| 8. 팁 세로로 쌓기 | `.bp-tips { display: flex; flex-direction: column; gap: 4px; }` |
| 9. 팁 세 개의 내용 | `.bp-tip` 세 개 · 둘째 팁의 `<strong>콘텐츠가 깨지는 지점</strong>` |
| 10. custom media 세 줄 + Sass 변수 세 줄 | `.bp-code code` 안 `@custom-media --sm …` · `$bp-sm: 640px;` 등 |
| 11. 공백 · 줄바꿈 보존 | `.bp-code code { white-space: pre; display: block; }` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/responsive/reference/breakpoint-strategy.html`

```html
<!-- DOCTYPE 선언: HTML5 문서임을 브라우저에 알림 -->
<!DOCTYPE html>
<!-- html 루트, lang=ko: 한국어 페이지 -->
<html lang="ko">
<!-- head: 메타데이터 영역 -->
<head>
<!-- 문자 인코딩: UTF-8 -->
<meta charset="utf-8">
<!-- 브라우저 탭 제목 -->
<title>Breakpoint Strategy - 일반적인 브레이크포인트 값과 프로젝트에 맞는 설정 전략. 디바이스가 아닌 콘텐츠 기반으로 브레이크포인트를 결정하는 것이 핵심.</title>
<!--
  [반응형 디자인] Breakpoint Strategy
  설명: 일반적인 브레이크포인트 값과 프로젝트에 맞는 설정 전략. 디바이스가 아닌 콘텐츠 기반으로 브레이크포인트를 결정하는 것이 핵심.

  팁: Tailwind 기본 브레이크포인트(640, 768, 1024, 1280, 1536)가 가장 보편적이다. 하지만 프로젝트 콘텐츠를 기준으로 조정하는 것이 이상적. 브라우저 창을 줄여가며 레이아웃이 깨지는 지점을 브레이크포인트로 잡으라는 Ethan Marcotte의 조언이 유효하다.
-->
<style>
  /* .bp-demo: 데모 전체 컨테이너 - 시스템 폰트 적용 */
  .bp-demo {
    font-family: system-ui, sans-serif;   /* OS 시스템 폰트 사용 (가독성, 성능 우수) */
  }
  /* .bp-scale: 브레이크포인트 시각화 영역의 외곽 박스 */
  .bp-scale {
    margin-bottom: 16px;                  /* 다음 영역과의 간격 16px */
  }
  /* .bp-bar: 가로로 펼쳐진 색상 바(디바이스 구간 표시용) */
  .bp-bar {
    display: flex;                        /* 자식들을 가로 배치 */
    height: 36px;                         /* 막대 높이 36px */
    border-radius: 8px;                   /* 모서리 둥글게 8px */
    overflow: hidden;                     /* 자식의 색상이 모서리 밖으로 삐져나오지 않도록 자름 */
  }
  /* .bp-segment: 색상 바의 각 구간(모바일/태블릿/...) 공통 스타일 */
  .bp-segment {
    display: flex;                        /* 내부 라벨을 flex로 가운데 정렬하기 위함 */
    align-items: center;                  /* 세로 중앙 정렬 */
    justify-content: center;              /* 가로 중앙 정렬 */
    color: white;                         /* 글자색 흰색 */
    font-size: 11px;                      /* 작은 라벨 폰트 */
    font-weight: 600;                     /* 약간 굵게 */
  }
  /* .bp-segment.mobile: 모바일 구간 - 가장 좁은 화면 영역 표시 */
  .bp-segment.mobile {
    flex: 2.4;                            /* flex-grow 2.4: 다른 구간보다 1.5배 넓게 */
    background: #ef4444;                  /* 빨간색 */
  }
  /* .bp-segment.tablet: 태블릿 구간 */
  .bp-segment.tablet {
    flex: 1.6;                            /* flex-grow 1.6 */
    background: #f59e0b;                  /* 주황색 */
  }
  /* .bp-segment.laptop: 랩탑 구간 */
  .bp-segment.laptop {
    flex: 1.6;                            /* flex-grow 1.6 */
    background: #22c55e;                  /* 초록색 */
  }
  /* .bp-segment.desktop: 데스크톱 구간 */
  .bp-segment.desktop {
    flex: 1.6;                            /* flex-grow 1.6 */
    background: #3b82f6;                  /* 파란색 */
  }
  /* .bp-segment.wide: 와이드 구간(가장 큰 화면) */
  .bp-segment.wide {
    flex: 1.6;                            /* flex-grow 1.6 */
    background: #8b5cf6;                  /* 보라색 */
  }
  /* .bp-markers: 색상 바 아래 픽셀 표시(640px 등)를 띄우기 위한 영역 */
  .bp-markers {
    position: relative;                   /* 자식 absolute 기준 컨텍스트 */
    height: 36px;                         /* 마커 영역 높이 */
    margin-top: 4px;                      /* 바와의 간격 4px */
  }
  /* .bp-mark: 개별 픽셀 마커(절대 위치로 % 좌표에 배치) */
  .bp-mark {
    position: absolute;                   /* 부모 .bp-markers 기준 절대 배치 */
    font-size: 10px;                      /* 매우 작은 폰트 */
    color: #64748b;                       /* 슬레이트 회색 */
    text-align: center;                   /* 중앙 정렬 */
    transform: translateX(-50%);          /* 자기 폭의 절반만큼 좌측 이동 → left가 정확한 중앙 좌표가 됨 */
    line-height: 1.3;                     /* 줄 간격 */
  }
  /* .bp-mark strong: 마커 안 픽셀 수치 강조 부분 */
  .bp-mark strong {
    color: #1e293b;                       /* 어두운 슬레이트 색 - 픽셀값을 두드러지게 */
  }
  /* .bp-tips: 팁 박스들의 컨테이너 */
  .bp-tips {
    display: flex;                        /* flex 컨테이너 */
    flex-direction: column;               /* 세로 정렬 */
    gap: 4px;                             /* 팁 사이 간격 4px */
    margin: 40px 0 12px;                  /* 위 40, 아래 12 - 마커 영역과 충분한 간격 확보 */
  }
  /* .bp-tip: 개별 팁 박스(왼쪽 파란 보더 강조) */
  .bp-tip {
    font-size: 12px;                      /* 본문보다 약간 작게 */
    padding: 6px 10px;                    /* 안쪽 여백 */
    background: #eff6ff;                  /* 매우 옅은 파랑 배경 */
    border-left: 3px solid #3b82f6;       /* 좌측 파란 띠 */
    border-radius: 0 4px 4px 0;           /* 우측만 둥글게(좌측은 띠와 맞물려 각짐) */
    color: #1e3a5f;                       /* 진한 파랑 */
  }
  /* .bp-code: 코드 예시 박스(다크 테마) */
  .bp-code {
    background: #1e293b;                  /* 어두운 배경 */
    border-radius: 8px;                   /* 모서리 둥글게 */
    padding: 14px;                        /* 내부 여백 */
  }
  /* .bp-code code: 박스 내부 코드 텍스트 */
  .bp-code code {
    font-size: 11px;                      /* 작은 코드 폰트 */
    color: #e2e8f0;                       /* 밝은 회색 글자 */
    white-space: pre;                     /* 공백/줄바꿈을 그대로 보존 */
    line-height: 1.5;                     /* 코드 가독성을 위한 줄 간격 */
    display: block;                       /* 블록으로 표시(줄바꿈 보존) */
  }
</style>
<!-- /head -->
</head>
<!-- body: 시각 요소 영역 -->
<body>
<!-- 데모 루트 컨테이너 -->
<div class="bp-demo">
  <!-- 브레이크포인트 시각화 영역 -->
  <div class="bp-scale">
    <!-- 색상 구간 막대 -->
    <div class="bp-bar">
      <!-- 모바일 구간 -->
      <div class="bp-segment mobile"><span>Mobile</span></div>
      <!-- 태블릿 구간 -->
      <div class="bp-segment tablet"><span>Tablet</span></div>
      <!-- 랩탑 구간 -->
      <div class="bp-segment laptop"><span>Laptop</span></div>
      <!-- 데스크톱 구간 -->
      <div class="bp-segment desktop"><span>Desktop</span></div>
      <!-- 와이드 구간 -->
      <div class="bp-segment wide"><span>Wide</span></div>
    </div>
    <!-- 픽셀 마커 영역(0, 640, 768, ...) -->
    <div class="bp-markers">
      <!-- 0 위치 마커 -->
      <div class="bp-mark" style="left: 0"><strong>0</strong></div>
      <!-- 640px 마커 (sm) -->
      <div class="bp-mark" style="left: 24%"><strong>640px</strong><br>sm</div>
      <!-- 768px 마커 (md) -->
      <div class="bp-mark" style="left: 40%"><strong>768px</strong><br>md</div>
      <!-- 1024px 마커 (lg) -->
      <div class="bp-mark" style="left: 56%"><strong>1024px</strong><br>lg</div>
      <!-- 1280px 마커 (xl) -->
      <div class="bp-mark" style="left: 72%"><strong>1280px</strong><br>xl</div>
      <!-- 1536px 마커 (2xl) -->
      <div class="bp-mark" style="left: 88%"><strong>1536px</strong><br>2xl</div>
    </div>
  </div>
  <!-- 팁 목록 -->
  <div class="bp-tips">
    <!-- 팁 1: 변수 관리 권장 -->
    <div class="bp-tip">CSS 커스텀 프로퍼티로 관리하기 어려움 → Sass 변수 또는 PostCSS custom media 사용</div>
    <!-- 팁 2: 콘텐츠 기준 결정 -->
    <div class="bp-tip">디바이스에 맞추지 말고, <strong>콘텐츠가 깨지는 지점</strong>에 브레이크포인트 설정</div>
    <!-- 팁 3: 적정 개수 -->
    <div class="bp-tip">3~5개가 적정. 너무 많으면 유지보수 어려움</div>
  </div>
  <!-- 코드 예시 박스 -->
  <div class="bp-code">
    <code>/* CSS custom media (PostCSS) */
@custom-media --sm (min-width: 640px);
@custom-media --md (min-width: 768px);
@custom-media --lg (min-width: 1024px);

/* Sass 변수 */
$bp-sm: 640px;
$bp-md: 768px;
$bp-lg: 1024px;</code>
  </div>
</div>

<!-- /body -->
</body>
<!-- /html -->
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.bp-demo { font-family: system-ui, sans-serif; }
.bp-scale { margin-bottom: 16px; }
.bp-bar { display: flex; height: 36px; border-radius: 8px; overflow: hidden; }
.bp-segment { display: flex; align-items: center; justify-content: center; color: white; font-size: 11px; font-weight: 600; }
.bp-segment.mobile { flex: 2.4; background: #ef4444; }
.bp-segment.tablet { flex: 1.6; background: #f59e0b; }
.bp-segment.laptop { flex: 1.6; background: #22c55e; }
.bp-segment.desktop { flex: 1.6; background: #3b82f6; }
.bp-segment.wide { flex: 1.6; background: #8b5cf6; }
.bp-markers { position: relative; height: 36px; margin-top: 4px; }
.bp-mark { position: absolute; font-size: 10px; color: #64748b; text-align: center; transform: translateX(-50%); line-height: 1.3; }
.bp-mark strong { color: #1e293b; }
.bp-tips { display: flex; flex-direction: column; gap: 4px; margin: 40px 0 12px; }
.bp-tip { font-size: 12px; padding: 6px 10px; background: #eff6ff; border-left: 3px solid #3b82f6; border-radius: 0 4px 4px 0; color: #1e3a5f; }
.bp-code { background: #1e293b; border-radius: 8px; padding: 14px; }
.bp-code code { font-size: 11px; color: #e2e8f0; white-space: pre; line-height: 1.5; display: block; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**

- 막대 폭 나누기는 `flex` 비율 한 가지로 끝난다 — 2.4 : 1.6 이 1.5배다.
- 마커는 「기준 상자 `relative` + 마커 `absolute` + `left` 백분율」로 놓고, `translateX(-50%)` 로 가운데를 좌표에 맞춘다.
- 마커 좌표는 개념 그림이라 구간 경계와 정확히 맞지 않는다(2.4/8.8 ≈ 27.3% 대 24%). (코드에서 읽은 것 — 렌더 실측 아님)
- 코드 예시의 두 꼴(`@custom-media` · Sass 변수)은 모두 `var()` 를 못 쓰는 미디어 쿼리에 값을 한 곳에서 넣는 방법이다.
- `white-space: pre` 가 없으면 `<code>` 안 줄바꿈이 공백 하나로 합쳐진다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

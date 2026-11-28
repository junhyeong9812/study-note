# css/responsive/05 — Fluid Typography — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 22px — 이상적 값이 범위 안에 있어 그대로 쓰인다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
이상적 값은 `1rem + 2vw` = 16px + 300 × 0.02 = 16 + 6 = 22px 이다.
최소 `1.25rem` 은 20px, 최대 `2.5rem` 은 40px 이다.
22px 은 20 ~ 40 사이이므로 22px 이 쓰인다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`clamp()` 는 이상적 값을 먼저 계산하고 범위 안이면 그대로 쓴다.
제목은 뷰포트 200px ~ 1200px 에서 움직이는데 300px 은 그 안이다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (2)」 · 「동작 방식 (4)」.

### 2. 320px 에서는 14px(최소), 1600px 에서는 18px(최대)

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
이상적 값은 `0.75rem + 0.5vw` = 12px + 너비 × 0.005 이다.
320px: 12 + 1.6 = 13.6px → 최소 `0.875rem`(14px) 보다 작아 14px 이 쓰인다.
1600px: 12 + 8 = 20px → 최대 `1.125rem`(18px) 보다 커 18px 이 쓰인다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
본문은 뷰포트 400px ~ 1200px 에서만 변한다.
320px 은 그보다 좁아 찬물 쪽 멈춤쇠에, 1600px 은 그보다 넓어 뜨거운 쪽 멈춤쇠에 붙는다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (4)」.

### 3. `0.8rem + 1vw`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
기울기 = (24 − 16) / (1120 − 320) = 8 / 800 = 0.01 → × 100 하면 `1vw`.
출발점 = 16 − 0.01 × 320 = 16 − 3.2 = 12.8px → 12.8 / 16 = `0.8rem`.
그래서 `clamp(1rem, 0.8rem + 1vw, 1.5rem)` 이 된다.
확인: 320px 에서 12.8 + 3.2 = 16px, 1120px 에서 12.8 + 11.2 = 24px 로 양 끝이 맞는다.

**왜 그런가**
이상적 값은 「출발점 + 기울기 × 너비」 직선이고, 원본 팁의 공식은 양 끝 두 점을 지나는 직선을 구하는 식이다.
근거: 2-summary 「동작 방식 (3)」.

### 4. `rem` 몫이 있어야 사용자 글꼴 설정이 반영된다

`3vw` 만 쓰면 범위 안의 글자 크기가 뷰포트 너비에만 묶여, 사용자가 기본 글꼴 크기를 키워도 따라 커지지 않는다.
`1rem + 2vw` 는 `1rem` 몫이 루트 글자 크기를 따라 바뀌므로 사용자 설정이 반영된다.
원본 팁도 이상적 값은 보통 `rem + vw` 조합을 쓰고, `rem` 기반이면 사용자 폰트 크기 설정이 반영된다고 한다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 1」.

### 5. 미디어 쿼리는 계단, `clamp()` 는 비탈

미디어 쿼리 방식은 브레이크포인트에서만 크기가 바뀌므로 창을 넓히면 글자가 몇 단계로 툭툭 뛴다.
`clamp()` 방식은 이상적 값이 뷰포트 너비에 비례하는 직선이라 최소 ~ 최대 구간 안에서 끊김 없이 커진다.
그래서 「브레이크포인트 없이 부드러운 반응형」이 된다.
근거: 2-summary 「한눈에」 그림 · 「언제 쓰고 언제 안 쓰나」 · 원본 설명.

### 6. 약 533px 에서 약 1333px 사이

이상적 값은 9.6px + 너비 × 0.003 이다(1rem = 16px).
최소 11.2px 에 닿는 너비: (11.2 − 9.6) / 0.003 ≈ 533px.
최대 13.6px 에 닿는 너비: (13.6 − 9.6) / 0.003 ≈ 1333px.
그보다 좁으면 11.2px, 넓으면 13.6px 에 고정된다.
근거: 2-summary 「동작 방식 (4)」 표 · 「어디서 틀리나 3」.

### 7. 루트 글자 크기가 16px 이 아니게 되면 틀린다

`1.25rem` 과 `2.5rem` 을 20px · 40px 로 옮긴 것은 1rem = 16px 을 가정한 계산이다.
사용자가 브라우저 기본 글꼴을 바꾸면 1rem 이 달라지고 범위도 함께 바뀐다(예: 1rem = 20px 이면 25px ~ 50px).
1rem = 16px 은 브라우저 기본값일 뿐 명세가 보장하지 않는다.
근거: 2-summary 「어디서 틀리나 2」 · 「구현 세부사항 대 언어 보장」.

### 8. `.formula-code` 는 그대로, `.fluid-heading` 은 따라 커진다

`.formula-code` 는 `font-size: 12px` 고정이라 사용자 설정과 뷰포트 어느 쪽도 따라가지 않는다.
`.fluid-heading` 은 최소 · 최대 · 이상적 값의 출발점이 모두 `rem` 이라 루트 글자 크기를 따라 커진다(`2vw` 몫만 그대로다).
근거: 2-summary 「동작 방식 (5)」 그림 · 「어디서 틀리나 5」.

## 실습 정답

### 실습 1. 제목 · 본문 · 캡션이 화면 너비를 따라 커지는 유동 타이포 데모

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 루트 안에 예시 상자와 공식 상자 | `div.fluid-type-demo` > `div.fluid-example` · `div.fluid-formula` |
| 2. 제목 · 본문 · 캡션 | `h2.fluid-heading` · `p.fluid-body` · `span.fluid-caption` |
| 3. 제목의 유동 크기 | `.fluid-heading { font-size: clamp(1.25rem, 1rem + 2vw, 2.5rem); }` |
| 4. 본문의 유동 크기 | `.fluid-body { font-size: clamp(0.875rem, 0.75rem + 0.5vw, 1.125rem); }` |
| 5. 캡션의 유동 크기 | `.fluid-caption { font-size: clamp(0.7rem, 0.6rem + 0.3vw, 0.85rem); }` |
| 6. 공식 상자의 제목과 코드 | `div.formula-title` 「clamp() 구조」 · `code.formula-code` |
| 7. 공백 · 줄바꿈 보존 블록 | `.formula-code { white-space: pre; display: block; }` |
| 8. 미디어 쿼리 없음 | `<style>` 안에 `@media` 가 없다 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/responsive/reference/fluid-typography.html`

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
<title>Fluid Typography - clamp() 함수로 뷰포트 크기에 따라 자연스럽게 변하는 폰트 크기를 설정한다. 브레이크포인트 없이 부드러운 반응형 타이포그래피 구현.</title>
<!--
  [반응형 디자인] Fluid Typography
  설명: clamp() 함수로 뷰포트 크기에 따라 자연스럽게 변하는 폰트 크기를 설정한다. 브레이크포인트 없이 부드러운 반응형 타이포그래피 구현.

  팁: clamp(최소, 이상적, 최대) 형식에서 이상적 값은 보통 rem + vw 조합을 쓴다. 계산 공식: preferred = minSize + (maxSize - minSize) * (100vw - minViewport) / (maxViewport - minViewport). 도구(utopia.fyi)를 사용하면 편하다. rem 기반으로 작성하면 사용자 폰트 크기 설정도 반영된다.
-->
<style>
  /* .fluid-type-demo: 루트 컨테이너 */
  .fluid-type-demo {
    font-family: system-ui, sans-serif;   /* 시스템 폰트 */
  }
  /* .fluid-example: 유동 타이포 예시 박스 */
  .fluid-example {
    background: #f8fafc;                  /* 매우 옅은 배경 */
    border-radius: 12px;                  /* 둥근 모서리 */
    padding: 24px;                        /* 안쪽 여백 */
    margin-bottom: 16px;                  /* 코드 박스와 간격 */
  }
  /* .fluid-heading: 유동 제목 - 뷰포트에 따라 크기 변화 */
  .fluid-heading {
    font-size: clamp(1.25rem, 1rem + 2vw, 2.5rem); /* 20px ~ 40px 사이 유동(뷰포트 비례) */
    color: #1e293b;                       /* 어두운 색 */
    margin: 0 0 12px 0;                   /* 위/좌/우 0, 아래 12px */
    line-height: 1.2;                     /* 큰 제목용 좁은 줄 간격 */
  }
  /* .fluid-body: 유동 본문 텍스트 */
  .fluid-body {
    font-size: clamp(0.875rem, 0.75rem + 0.5vw, 1.125rem); /* 14px ~ 18px 사이 유동 */
    color: #475569;                       /* 회색 톤 */
    line-height: 1.6;                     /* 본문 가독성용 넉넉한 줄 간격 */
    margin: 0 0 8px 0;                    /* 아래 여백 */
  }
  /* .fluid-caption: 유동 캡션 */
  .fluid-caption {
    font-size: clamp(0.7rem, 0.6rem + 0.3vw, 0.85rem); /* 11.2px ~ 13.6px 사이 유동 */
    color: #94a3b8;                       /* 옅은 회색 */
  }
  /* .fluid-formula: clamp 공식 설명 박스(다크) */
  .fluid-formula {
    background: #1e293b;                  /* 어두운 배경 */
    border-radius: 8px;                   /* 둥근 모서리 */
    padding: 14px;                        /* 내부 여백 */
  }
  /* .formula-title: 공식 박스 제목 */
  .formula-title {
    font-size: 12px;                      /* 작은 폰트 */
    font-weight: 700;                     /* 굵게 */
    color: #f59e0b;                       /* 호박색 강조 */
    margin-bottom: 8px;                   /* 코드와 간격 */
  }
  /* .formula-code: 공식 코드 표시 */
  .formula-code {
    font-size: 12px;                      /* 코드 폰트 */
    color: #e2e8f0;                       /* 밝은 회색 글자 */
    white-space: pre;                     /* 공백/개행 보존 */
    line-height: 1.6;                     /* 줄 간격 */
    display: block;                       /* 블록 */
  }
</style>
</head>
<body>
<!-- 데모 루트 -->
<div class="fluid-type-demo">
  <!-- 유동 타이포 예시 -->
  <div class="fluid-example">
    <!-- 유동 제목 -->
    <h2 class="fluid-heading">유동적 제목</h2>
    <!-- 유동 본문 -->
    <p class="fluid-body">이 텍스트는 뷰포트 크기에 따라 자연스럽게 크기가 변합니다. 미디어 쿼리 없이 clamp() 하나로 최소, 이상적, 최대 크기를 지정합니다.</p>
    <!-- 유동 캡션 -->
    <span class="fluid-caption">캡션 텍스트</span>
  </div>
  <!-- clamp() 공식 설명 박스 -->
  <div class="fluid-formula">
    <!-- 박스 제목 -->
    <div class="formula-title">clamp() 구조</div>
    <!-- 공식 코드 -->
    <code class="formula-code">font-size: clamp(최소값, 이상적값, 최대값);

/* 예시 */
font-size: clamp(1rem, 0.5rem + 2vw, 2.5rem);
           ↑         ↑              ↑
      16px 이하   뷰포트 비례     40px 이상
      로 줄지 않음  크기 계산     으로 커지지 않음</code>
  </div>
</div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.fluid-type-demo { font-family: system-ui, sans-serif; }
.fluid-example { background: #f8fafc; border-radius: 12px; padding: 24px; margin-bottom: 16px; }
.fluid-heading { font-size: clamp(1.25rem, 1rem + 2vw, 2.5rem); color: #1e293b; margin: 0 0 12px 0; line-height: 1.2; }
.fluid-body { font-size: clamp(0.875rem, 0.75rem + 0.5vw, 1.125rem); color: #475569; line-height: 1.6; margin: 0 0 8px 0; }
.fluid-caption { font-size: clamp(0.7rem, 0.6rem + 0.3vw, 0.85rem); color: #94a3b8; }
.fluid-formula { background: #1e293b; border-radius: 8px; padding: 14px; }
.formula-title { font-size: 12px; font-weight: 700; color: #f59e0b; margin-bottom: 8px; }
.formula-code { font-size: 12px; color: #e2e8f0; white-space: pre; line-height: 1.6; display: block; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 세 글자 단계마다 `clamp()` 를 따로 주어 최소 · 최대와 기울기(`2vw` · `0.5vw` · `0.3vw`)를 다르게 한다.
- 세 값 모두 `rem` 을 섞어 사용자 글꼴 설정이 반영되게 한다.
- 1rem = 16px 일 때 제목은 200px ~ 1200px, 본문은 400px ~ 1200px, 캡션은 약 533px ~ 1333px 너비에서 실제로 변한다.
- 공식 상자의 `12px` 글자는 일부러 고정으로 두어 유동 글자와 대비된다.
- `white-space: pre` 가 없으면 공식 코드의 줄바꿈과 화살표 정렬 공백이 하나로 합쳐진다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

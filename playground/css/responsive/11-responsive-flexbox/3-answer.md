# css/responsive/11 — Responsive Flexbox — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 사이드바 214px, 메인 378px — 두 배가 아니다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

basis 합은 150 + 250 + 8(gap) = 408px 로 600px 이하라 한 줄에 놓인다.
남는 공간은 600 − 408 = 192px 다.
grow 몫 1:2 로 나누면 사이드바 +64px, 메인 +128px 다.
그래서 사이드바 214px, 메인 378px 이고, 378 은 214 의 두 배(428)가 아니다.

**왜 그런가**

grow 는 최종 너비가 아니라 **남는 공간**을 나누는 몫이다.
basis 가 서로 다르므로 최종 너비 비율은 1:2 가 되지 않는다.
근거: 2-summary 「동작 방식 (2)」, 「어디서 틀리나 2」.

### 2. 두 줄 — 둘 다 380px

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

basis 합 408px 가 380px 를 넘으므로 메인이 다음 줄로 넘어간다.
1줄의 사이드바는 혼자라 남는 230px 를 다 받아 380px 가 된다.
2줄의 메인도 혼자라 남는 130px 를 다 받아 380px 가 된다.

**왜 그런가**

두 basis 는 각각 380px 보다 작지만, 한 줄에 담긴 basis 와 gap 의 **합**이 넘쳐 줄바꿈된다.
줄을 나눈 뒤에는 줄마다 따로 grow 로 남는 공간을 채운다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (3)」.

### 3. 1줄에 셋, 2줄에 하나 — 카드 4는 330px

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

1줄: 100 + 8 + 100 + 8 + 100 = 316px ≤ 330px 라 셋이 들어가고, 넷째를 더하면 424px 로 넘친다.
1줄의 남는 14px 를 셋이 똑같이 나눠 각각 약 104.67px 다.
2줄의 카드 4는 혼자라 남는 230px 를 다 받아 330px 가 된다.

**왜 그런가**

나눔은 줄마다 따로 하므로 마지막 줄의 외톨이가 줄 폭 전체를 차지한다.
근거: 2-summary 「동작 방식 (3)」, 「어디서 틀리나 4」.

### 4. 줄에 들어가는지를 basis 합과 컨테이너 폭으로 정하기 때문이다

컨테이너 폭은 화면 폭을 따라 바뀐다.
`flex-wrap: wrap` 컨테이너는 아이템의 basis 와 gap 을 더해 가다 폭을 넘는 순간 다음 줄을 시작한다.
그래서 폭이 넓으면 한 줄에 많이, 좁으면 적게 놓인다 — 화면 폭마다 규칙을 따로 쓸 필요가 없다.
근거: 2-summary 「한눈에」 · 「동작 방식 (1)」 · 원본 팁(미디어 쿼리 없이 반응형 사이드바).

### 5. 혼자 한 줄에 놓이고, shrink 1 이면 basis 보다 작아진다

basis 가 컨테이너보다 큰 아이템은 다른 아이템과 같은 줄에 담길 수 없어 혼자 한 줄을 차지한다.
그 줄에서도 폭이 모자라므로 `flex-shrink: 1` 이면 줄 폭에 맞게 basis 보다 작게 줄어든다.
즉 팁의 「줄바꿈된다」는 혼자 한 줄이 된다는 데까지만 맞고, basis 는 최소 폭을 보장하지 않는다.
줄바꿈의 실제 조건은 개별 basis 가 아니라 한 줄의 basis + gap 합이다.
근거: 2-summary 「동작 방식 (4)」, 「어디서 틀리나 1 · 3」.

### 6. 한 줄에 남은 채 둘 다 줄어든다

`flex-wrap` 의 기본값은 `nowrap` 이라 줄바꿈이 일어나지 않는다.
두 박스는 380px 한 줄에 그대로 놓이고, 모자란 폭을 `flex-shrink` 로 메우며 basis 보다 좁아진다.
근거: 2-summary 「동작 방식 (1)」, 「어디서 틀리나 5」.

### 7. 줄 끝 아이템을 미리 알 수 없어 군더더기 여백이 생기기 때문이다

`margin-right` 는 줄 끝 아이템에도 붙어 줄 오른쪽에 여백이 남는다.
줄바꿈 위치는 화면 폭마다 바뀌므로 「어느 카드가 줄 끝인가」를 CSS 로 미리 골라 margin 을 뺄 수 없다.
그래서 음수 margin 으로 상쇄하는 margin 핵이 필요했다.
`gap` 은 아이템 사이와 줄 사이에만 생겨 이 문제가 없다.
근거: 2-summary 「동작 방식 (5)」, 「어디서 틀리나 6」 · 원본 팁.

### 8. 줄바꿈 말고 다른 변화가 폭에 따라 필요할 때다

줄바꿈 패턴이 바꾸는 것은 「한 줄에 몇 개 놓이나」뿐이다.
화면 폭에 따라 순서를 바꾸거나, 무언가를 숨기거나, basis 같은 값 자체를 바꾸려면 미디어 쿼리가 필요하다.
원본 설명이 「flex-wrap과 미디어 쿼리 조합」이라고 한 것도 이런 경우를 함께 다룬다는 뜻으로 읽을 수 있다 (원본에 근거 없음 — 추론).
근거: 2-summary 「언제 쓰고 언제 안 쓰나」, 「어디서 틀리나 8」.

## 실습 정답

### 실습 1. 사이드바 + 메인과 균등 카드를 미디어 쿼리 없이 반응형으로

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 루트가 세로로 쌓는 flex 컨테이너 | `.rf-demo { display: flex; flex-direction: column; }` |
| 2. 루트 자식 간격 | `.rf-demo { gap: 14px; }` |
| 3. 사이드바 + 메인 컨테이너가 줄바꿈 | `.rf-flex-auto { display: flex; flex-wrap: wrap; }` |
| 4. 두 박스 간격 | `.rf-flex-auto { gap: 8px; }` |
| 5. 사이드바 grow 1 · shrink 1 · basis 150px | `.rf-item { flex: 1 1 150px; }` |
| 6. 메인 grow 2 · shrink 1 · basis 250px | `.rf-item.main { flex: 2 1 250px; }` |
| 7. 넓으면 한 줄, 좁으면 위아래 | `flex-wrap: wrap` + 두 basis 의 합 |
| 8. 카드 컨테이너가 줄바꿈 | `.rf-flex-cards { display: flex; flex-wrap: wrap; }` |
| 9. 카드 간격 | `.rf-flex-cards { gap: 8px; }` |
| 10. 카드가 남는 공간을 똑같이 | `.rf-card { flex: 1 1 100px; }` |
| 11. 코드 박스에 줄바꿈 · 공백 살리기 | `.rf-code code { white-space: pre; display: block; }` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/responsive/reference/responsive-flexbox.html`

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
<title>Responsive Flexbox - flex-wrap과 미디어 쿼리 조합으로 유연한 반응형 레이아웃을 구현한다. flex-basis와 flex-grow를 활용한 자동 줄바꿈 패턴.</title>
<!--
  [반응형 디자인] Responsive Flexbox
  설명: flex-wrap과 미디어 쿼리 조합으로 유연한 반응형 레이아웃을 구현한다. flex-basis와 flex-grow를 활용한 자동 줄바꿈 패턴.

  팁: flex: 1 1 <basis>에서 basis가 컨테이너보다 크면 자동으로 줄바꿈된다. 이 패턴으로 미디어 쿼리 없이 반응형 사이드바 레이아웃을 만들 수 있다. gap과 함께 사용하면 margin 핵으로 간격을 만들 필요가 없다.
-->
<style>
  /* .rf-demo: 데모 루트 - 섹션을 세로로 쌓음 */
  .rf-demo {
    font-family: system-ui, sans-serif;   /* 시스템 폰트 */
    display: flex;                        /* flex 컨테이너 */
    flex-direction: column;               /* 세로 정렬 */
    gap: 14px;                            /* 섹션 간격 */
  }
  /* .rf-section: 데모 섹션 */
  .rf-section {
    background: #f1f5f9;                  /* 옅은 배경 */
    border-radius: 8px;                   /* 둥근 모서리 */
    padding: 12px;                        /* 안쪽 여백 */
  }
  /* .rf-label: 섹션 라벨 */
  .rf-label {
    font-size: 12px;                      /* 작은 폰트 */
    font-weight: 700;                     /* 굵게 */
    color: #475569;                       /* 회색 */
    margin-bottom: 8px;                   /* 콘텐츠와 간격 */
  }
  /* .rf-flex-auto: 자동 줄바꿈 flex 컨테이너(사이드바 + 메인) */
  .rf-flex-auto {
    display: flex;                        /* flex */
    flex-wrap: wrap;                      /* 자식 basis가 폭을 넘으면 줄바꿈 */
    gap: 8px;                             /* 자식 간격 */
  }
  /* .rf-item: 사이드바/메인 박스 공통 */
  .rf-item {
    background: #8b5cf6;                  /* 보라색 */
    color: white;                         /* 흰 글자 */
    padding: 16px;                        /* 안쪽 여백 */
    border-radius: 6px;                   /* 둥근 모서리 */
    font-weight: 600;                     /* 약간 굵게 */
    font-size: 13px;                      /* 폰트 */
    flex: 1 1 150px;                      /* grow:1 shrink:1 basis:150px - 150px 미만이면 줄바꿈 */
    text-align: center;                   /* 중앙 정렬 */
  }
  /* .rf-item.main: 메인 콘텐츠(더 큰 비율) */
  .rf-item.main {
    flex: 2 1 250px;                      /* grow:2(2배), shrink:1, basis:250px - 사이드바보다 2배 차지 */
    background: #3b82f6;                  /* 파란색 */
  }
  /* .rf-flex-cards: 균등 카드 컨테이너 */
  .rf-flex-cards {
    display: flex;                        /* flex */
    flex-wrap: wrap;                      /* 줄바꿈 허용 */
    gap: 8px;                             /* 카드 간격 */
  }
  /* .rf-card: 균등 분배 카드 */
  .rf-card {
    flex: 1 1 100px;                      /* 최소 100px 보장, 가용 공간 균등 분배 */
    background: #10b981;                  /* 초록색 */
    color: white;                         /* 흰 글자 */
    padding: 16px;                        /* 안쪽 여백 */
    border-radius: 6px;                   /* 둥근 모서리 */
    text-align: center;                   /* 중앙 정렬 */
    font-weight: 600;                     /* 약간 굵게 */
    font-size: 13px;                      /* 폰트 */
  }
  /* .rf-code: 코드 박스(다크) */
  .rf-code {
    background: #1e293b;                  /* 어두운 배경 */
    border-radius: 8px;                   /* 둥근 모서리 */
    padding: 14px;                        /* 내부 여백 */
  }
  /* .rf-code code: 코드 텍스트 */
  .rf-code code {
    font-size: 11px;                      /* 작은 폰트 */
    color: #e2e8f0;                       /* 밝은 글자 */
    white-space: pre;                     /* 공백/개행 보존 */
    line-height: 1.5;                     /* 줄 간격 */
    display: block;                       /* 블록 */
  }
</style>
</head>
<body>
<!-- 데모 루트 -->
<div class="rf-demo">
  <!-- 섹션 1: 사이드바 + 메인 자동 줄바꿈 -->
  <div class="rf-section">
    <!-- 라벨 -->
    <div class="rf-label">flex-wrap + flex-basis 자동 줄바꿈</div>
    <!-- 자동 줄바꿈 컨테이너 -->
    <div class="rf-flex-auto">
      <!-- 사이드바(작은 비율) -->
      <div class="rf-item">사이드바</div>
      <!-- 메인 콘텐츠(2배 비율) -->
      <div class="rf-item main">메인 콘텐츠</div>
    </div>
  </div>
  <!-- 섹션 2: 균등 카드 -->
  <div class="rf-section">
    <!-- 라벨 -->
    <div class="rf-label">균등 분배 카드 (미디어 쿼리 없이)</div>
    <!-- 균등 카드 컨테이너 -->
    <div class="rf-flex-cards">
      <!-- 카드 1 -->
      <div class="rf-card">카드 1</div>
      <!-- 카드 2 -->
      <div class="rf-card">카드 2</div>
      <!-- 카드 3 -->
      <div class="rf-card">카드 3</div>
      <!-- 카드 4 -->
      <div class="rf-card">카드 4</div>
    </div>
  </div>
  <!-- 코드 예시 박스 -->
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

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.rf-demo { font-family: system-ui, sans-serif; display: flex; flex-direction: column; gap: 14px; }
.rf-section { background: #f1f5f9; border-radius: 8px; padding: 12px; }
.rf-label { font-size: 12px; font-weight: 700; color: #475569; margin-bottom: 8px; }
.rf-flex-auto { display: flex; flex-wrap: wrap; gap: 8px; }
.rf-item { background: #8b5cf6; color: white; padding: 16px; border-radius: 6px; font-weight: 600; font-size: 13px; flex: 1 1 150px; text-align: center; }
.rf-item.main { flex: 2 1 250px; background: #3b82f6; }
.rf-flex-cards { display: flex; flex-wrap: wrap; gap: 8px; }
.rf-card { flex: 1 1 100px; background: #10b981; color: white; padding: 16px; border-radius: 6px; text-align: center; font-weight: 600; font-size: 13px; }
.rf-code { background: #1e293b; border-radius: 8px; padding: 14px; }
.rf-code code { font-size: 11px; color: #e2e8f0; white-space: pre; line-height: 1.5; display: block; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**

- 줄바꿈의 열쇠는 컨테이너의 `flex-wrap: wrap` 과 아이템의 `flex-basis` 두 가지다.
- 메인이 `.rf-item.main` 으로 `.rf-item` 의 `flex` 를 덮어써서 basis 와 grow 가 사이드바보다 크다.
- grow 2 는 남는 공간의 몫이라 메인이 사이드바의 정확히 두 배 너비가 되지는 않는다.
- 카드는 모두 같은 `flex: 1 1 100px` 라 한 줄 안에서는 같은 너비지만, 마지막 줄에 혼자 남은 카드는 줄 폭을 다 채운다.
- 모든 간격을 `gap` 으로 줘서 줄 끝 여백을 따로 처리하지 않는다.
- 코드 박스의 숫자(200px · 400px · 150px · 12px)는 데모의 실제 값과 다르다 — 패턴만 같다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

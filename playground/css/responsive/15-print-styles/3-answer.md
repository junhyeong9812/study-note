# css/responsive/15 — Print Styles — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 화면에서는 빨간 「메뉴」, 인쇄에서는 사라진다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

화면에서는 「메뉴」가 빨간 글자로 보인다.
인쇄 미리보기에서는 「메뉴」가 공간째 사라지고 「본문」이 위로 올라온다.

**왜 그런가**

- `.no-print { color: red; }` 는 매체를 가리지 않으므로 화면에도 적용된다.
- `@media print` 블록은 인쇄 매체일 때만 켜지므로 화면에서는 건너뛴다.
- 인쇄 때는 `display: none !important` 가 더해져 상자를 만들지 않는다.
- 근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (2)」.

### 2. `href` 가 있는 링크만 주소가 붙는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

첫 링크는 「예제 (https://example.com)」로 찍힌다.
둘째 링크는 「링크 텍스트」 그대로 찍힌다.

**왜 그런가**

- `a[href]` 는 `href` 속성을 가진 `a` 만 고른다.
- 첫 링크는 해당하여 `::after` 가 `" ("` · `attr(href)` 값 · `")"` 를 이어 붙인다.
- 둘째 링크는 `href` 가 없어 선택되지 않는다 — 원본 데모의 `.print-link` 와 같은 상황이다.
- 근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 2」.

### 3. 제목은 표와 함께 다음 쪽으로 넘어간다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

브라우저가 요청을 따르면 `h2` 는 첫 쪽에 남지 않고, 표와 함께 둘째 쪽 맨 위부터 찍힌다.
표는 둘로 잘리지 않고 둘째 쪽에 한 덩어리로 놓인다.

**왜 그런가**

- 표는 첫 쪽에 다 들어가지 않고, `break-inside: avoid` 가 표 안쪽에서 나누지 말라고 요청하므로 통째로 다음 쪽으로 간다.
- 그러면 `h2` 와 표 사이에서 쪽이 나뉘게 되는데, `h2` 의 `break-after: avoid` 가 그 자리의 나눔을 피하라고 요청한다.
- 그래서 `h2` 도 다음 쪽으로 따라가 제목이 홀로 남는 일이 없어진다.
- 다만 `avoid` 는 요청이므로 결과는 브라우저가 따를 수 있는 범위에서다.
- 근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 5」.

### 4. 인쇄 규칙은 「마지막 결정」이라 우선순위 다툼을 끝내는 것이 목적에 맞다

- 인쇄 규칙은 화면 규칙 위에 더해지는데, 화면 규칙 중에는 더 구체적인 선택자나 인라인 스타일이 있을 수 있다.
- `!important` 를 붙이면 어디서 무엇이 덮어쓰는지 따지지 않고 「종이에서는 반드시 이렇게」를 확정할 수 있다.
- 인쇄 블록은 인쇄 때만 켜지므로 화면 규칙을 고치기 어렵게 만들지도 않는다.
- 「유일한 상황」이라는 말은 원본의 권고(관례)이지 언어 규칙이 아니다.
- 근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 3」 · 「구현 세부사항 대 언어 보장」.

### 5. 종이에서는 누를 수 없고, 잉크를 아끼고 또렷해야 하기 때문이다

- 링크 주소: 종이에서는 링크를 누를 수 없으니 글자만으로는 목적지를 알 수 없다 — 그래서 `attr(href)` 로 주소를 뒤에 찍는다.
- 배경 제거: 화면용 어두운 배경은 종이에서 잉크만 많이 먹는다.
- 검정 글자: 옅은 색 글자는 종이에서 흐리게 찍히므로 검정으로 통일해 읽기 쉽게 한다.
- 근거: 2-summary 「한눈에」 · 「동작 방식 (3)」 · 「동작 방식 (4)」.

### 6. 사라지지 않는다 — 데모의 `@media print` 는 글자일 뿐이다

- 정답 코드의 `@media print { … }` 는 `<code>` 태그 안의 글자이지 `<style>` 안의 규칙이 아니다.
- `<style>` 의 `.no-print` 는 빨간 배경 · 취소선 · 흐림으로 「빠질 것」을 화면에 표시만 한다.
- 그래서 미리보기에서도 내비게이션 줄은 그대로 찍힌다고 읽힌다 (코드에서 읽은 것 — 렌더 실측 아님).
- 실제로 숨기려면 `<style>` 안에 `@media print { .no-print { display: none !important; } }` 를 넣어야 한다.
- 근거: 2-summary 「어디서 틀리나 1」.

### 7. 남지 않는다 — `!important` 작성자 규칙이 인라인 스타일을 이긴다

- `style="background: yellow"` 는 중요 표시가 없는 인라인 스타일이다.
- `!important` 가 붙은 작성자 규칙은 일반 선언과 중요 표시 없는 인라인 스타일보다 우선한다.
- 인쇄 때 `@media print` 가 켜지면 `background: none !important` 가 이겨 배경이 걷힌다.
- 근거: 2-summary 「동작 방식 (4)」 · 「구현 세부사항 대 언어 보장」.

### 8. 모두 「조건이 맞을 때만 규칙을 켠다」는 같은 장치다

- `@media print` 블록과 `<link media="print">` 파일은 같은 일을 하는 두 꼴이다 — 규칙을 CSS 안에 모으느냐 별도 파일로 나누느냐의 차이다.
- 반응형에서 쓰는 `@media (max-width: …)` 도 같은 미디어 쿼리 문법이지만, 조건이 「인쇄 매체」가 아니라 「화면 너비」다.
- 그래서 화면 크기에 따라 바꿀 때는 너비 쿼리를, 종이에서만 바꿀 때는 `print` 를 쓴다.
- 근거: 2-summary 「동작 방식 (1)」 · 「언제 쓰고 언제 안 쓰나」 · 「어디서 틀리나 7」. 너비 쿼리와의 비교는 (원본에 근거 없음 — 추론).

## 실습 정답

### 실습 1. 인쇄 스타일 안내 카드 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 페이지 모형에 제목 · 내비 · 본문 · 푸터 차례 | `.print-page` 안의 `.print-header` · `.print-nav` · `.print-content` · `.print-footer` |
| 2. 본문의 단락과 주소를 글자로 적은 링크 | `.print-content` 안의 `<p>` · `<a class="print-link">링크 텍스트 (https://example.com)</a>` |
| 3. 내비 · 푸터에 `no-print` | `class="print-nav no-print"` · `class="print-footer no-print"` |
| 4. 취소선 + 흐림 | `.no-print { text-decoration: line-through; opacity: 0.6; }` |
| 5. 규칙 다섯 개, 이름은 `<strong>` | `.print-rules` 안의 `.print-rule` 다섯 개 · `<strong>숨기기</strong>` 등 |
| 6. 세로로 쌓고 간격 | `.print-rules { display: flex; flex-direction: column; gap: 4px; }` |
| 7. `@media print` 예시 코드 | `.print-code` 안의 `<code>@media print { … }</code>` |
| 8. 블록 · 공백 보존 | `.print-code code { white-space: pre; display: block; }` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/responsive/reference/print-styles.html`

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
<title>Print Styles - @media print를 활용하여 인쇄에 최적화된 스타일을 적용한다. 불필요한 요소 숨기기, 링크 URL 표시, 배경색 제어 등.</title>
<!--
  [반응형 디자인] Print Styles
  설명: @media print를 활용하여 인쇄에 최적화된 스타일을 적용한다. 불필요한 요소 숨기기, 링크 URL 표시, 배경색 제어 등.

  팁: print 스타일은 별도 파일로 분리하거나(<link media="print">) @media print 블록으로 작성한다. !important를 적극 사용해도 괜찮은 유일한 상황이다. @page로 여백을 제어하고, orphans/widows로 텍스트 분리를 방지한다. Ctrl+P로 미리보기하며 개발한다.
-->
<style>
  /* .print-demo: 데모 루트 */
  .print-demo {
    font-family: system-ui, sans-serif;   /* 시스템 폰트 */
  }
  /* .print-preview: 인쇄 미리보기 영역 */
  .print-preview {
    margin-bottom: 12px;                  /* 다음 영역과 간격 */
  }
  /* .print-page: 인쇄될 페이지 모형 */
  .print-page {
    background: white;                    /* 흰 종이 느낌 */
    border: 2px solid #e2e8f0;            /* 옅은 보더 */
    border-radius: 4px;                   /* 모서리 살짝 둥글게 */
    padding: 16px;                        /* 안쪽 여백 */
    box-shadow: 4px 4px 0 #e2e8f0;        /* 종이 그림자 효과 */
    max-width: 300px;                     /* 최대 폭 - 페이지 느낌 */
  }
  /* .print-header: 인쇄 페이지 제목(인쇄됨) */
  .print-header {
    font-weight: 700;                     /* 굵게 */
    font-size: 16px;                      /* 본문보다 큼 */
    color: #1e293b;                       /* 어두운 색 */
    margin-bottom: 8px;                   /* 본문과 간격 */
    border-bottom: 1px solid #1e293b;     /* 하단 구분선 */
    padding-bottom: 4px;                  /* 구분선과 텍스트 간격 */
  }
  /* .print-nav, .print-footer: 인쇄 시 숨겨질 영역 공통 */
  .print-nav,
  .print-footer {
    font-size: 11px;                      /* 작은 폰트 */
    padding: 4px 8px;                     /* 패딩 */
    border-radius: 4px;                   /* 둥근 모서리 */
  }
  /* .no-print: 인쇄 시 숨김 표시(시각적으로 빨간 줄긋기) */
  .no-print {
    background: #fecaca;                  /* 옅은 빨강 */
    color: #991b1b;                       /* 진한 빨강 */
    text-decoration: line-through;        /* 취소선 */
    opacity: 0.6;                         /* 흐리게 */
    margin: 4px 0;                        /* 위아래 간격 */
  }
  /* .print-content: 인쇄될 본문 영역 */
  .print-content {
    font-size: 12px;                      /* 본문 폰트 */
    color: #374151;                       /* 진한 회색 */
    line-height: 1.6;                     /* 줄 간격 */
    margin: 8px 0;                        /* 위아래 간격 */
  }
  /* .print-link: 인쇄 시 URL이 노출되는 링크 */
  .print-link {
    color: #1d4ed8;                       /* 진한 파랑 */
    font-size: 11px;                      /* 작은 폰트 */
  }
  /* .print-rules: 인쇄 규칙 목록 컨테이너 */
  .print-rules {
    display: flex;                        /* flex */
    flex-direction: column;               /* 세로 정렬 */
    gap: 4px;                             /* 항목 간격 */
    margin-bottom: 12px;                  /* 코드와 간격 */
  }
  /* .print-rule: 개별 규칙 항목 */
  .print-rule {
    font-size: 11px;                      /* 작은 폰트 */
    padding: 6px 10px;                    /* 패딩 */
    background: #f1f5f9;                  /* 옅은 배경 */
    border-left: 3px solid #64748b;       /* 좌측 회색 띠 */
    border-radius: 0 4px 4px 0;           /* 우측만 둥글게 */
    color: #334155;                       /* 진한 회색 */
  }
  /* .print-rule strong: 규칙 항목 내 강조 텍스트 */
  .print-rule strong {
    color: #1e293b;                       /* 더 어둡게 강조 */
  }
  /* .print-code: 코드 박스(다크) */
  .print-code {
    background: #1e293b;                  /* 어두운 배경 */
    border-radius: 8px;                   /* 둥근 모서리 */
    padding: 14px;                        /* 내부 여백 */
  }
  /* .print-code code: 코드 텍스트 */
  .print-code code {
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
<div class="print-demo">
  <!-- 인쇄 미리보기 -->
  <div class="print-preview">
    <!-- 인쇄 페이지 모형 -->
    <div class="print-page">
      <!-- 페이지 제목 -->
      <div class="print-header">페이지 제목</div>
      <!-- 인쇄 시 숨겨질 내비게이션 -->
      <div class="print-nav no-print">내비게이션 (숨겨짐)</div>
      <!-- 인쇄될 콘텐츠 영역 -->
      <div class="print-content">
        <!-- 본문 단락 -->
        <p>인쇄될 콘텐츠 영역</p>
        <!-- URL이 함께 인쇄되는 링크 -->
        <a class="print-link">링크 텍스트 (https://example.com)</a>
      </div>
      <!-- 인쇄 시 숨겨질 푸터 -->
      <div class="print-footer no-print">푸터 (숨겨짐)</div>
    </div>
  </div>
  <!-- 인쇄 규칙 목록 -->
  <div class="print-rules">
    <!-- 규칙: 숨기기 -->
    <div class="print-rule"><strong>숨기기</strong> — nav, footer, .sidebar, button, .no-print</div>
    <!-- 규칙: 링크 URL 노출 -->
    <div class="print-rule"><strong>링크 URL</strong> — a[href]::after { content: " (" attr(href) ")"; }</div>
    <!-- 규칙: 배경 제거 -->
    <div class="print-rule"><strong>배경 제거</strong> — background: none !important;</div>
    <!-- 규칙: 텍스트 색상 -->
    <div class="print-rule"><strong>텍스트 색상</strong> — color: #000 !important;</div>
    <!-- 규칙: 페이지 나누기 -->
    <div class="print-rule"><strong>페이지 나누기</strong> — break-before, break-after, break-inside: avoid;</div>
  </div>
  <!-- 코드 예시 박스 -->
  <div class="print-code">
    <code>@media print {
  nav, footer, .sidebar, .no-print {
    display: none !important;
  }
  body { font-size: 12pt; color: #000; }
  a[href]::after {
    content: " (" attr(href) ")";
    font-size: 0.8em; color: #666;
  }
  h2, h3 { break-after: avoid; }
  table, figure { break-inside: avoid; }
  @page { margin: 2cm; }
}</code>
  </div>
</div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.print-demo { font-family: system-ui, sans-serif; }
.print-preview { margin-bottom: 12px; }
.print-page { background: white; border: 2px solid #e2e8f0; border-radius: 4px; padding: 16px; box-shadow: 4px 4px 0 #e2e8f0; max-width: 300px; }
.print-header { font-weight: 700; font-size: 16px; color: #1e293b; margin-bottom: 8px; border-bottom: 1px solid #1e293b; padding-bottom: 4px; }
.print-nav, .print-footer { font-size: 11px; padding: 4px 8px; border-radius: 4px; }
.no-print { background: #fecaca; color: #991b1b; text-decoration: line-through; opacity: 0.6; margin: 4px 0; }
.print-content { font-size: 12px; color: #374151; line-height: 1.6; margin: 8px 0; }
.print-link { color: #1d4ed8; font-size: 11px; }
.print-rules { display: flex; flex-direction: column; gap: 4px; margin-bottom: 12px; }
.print-rule { font-size: 11px; padding: 6px 10px; background: #f1f5f9; border-left: 3px solid #64748b; border-radius: 0 4px 4px 0; color: #334155; }
.print-rule strong { color: #1e293b; }
.print-code { background: #1e293b; border-radius: 8px; padding: 14px; }
.print-code code { font-size: 11px; color: #e2e8f0; white-space: pre; line-height: 1.5; display: block; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**

- 이 데모는 인쇄 규칙을 **보여 주는** 안내 카드다 — `@media print` 는 `<code>` 안의 글자이고 실제로 켜지지 않는다.
- `.no-print` 는 실제 숨김 대신 취소선 · 흐림으로 「인쇄 때 빠질 것」을 화면에 표시한다.
- 링크에 `href` 가 없고 주소를 글자로 적었으므로, `a[href]::after` 가 붙일 결과를 손으로 흉내 낸 것이다.
- `white-space: pre` 가 없으면 코드 상자의 들여쓰기와 줄바꿈이 한 줄로 뭉개진다.
- 실제 인쇄 동작을 보려면 `<code>` 안의 규칙을 `<style>` 안에도 넣고 Ctrl+P 미리보기로 확인한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

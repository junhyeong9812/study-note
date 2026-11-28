# css/responsive/15 — Print Styles — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. `.no-print` 를 단 메뉴의 화면과 인쇄 (예측)

```html
<!-- 질문용 발췌 -->
<nav class="no-print">메뉴</nav>
<p>본문</p>
<style>
  .no-print { color: red; }
  @media print { .no-print { display: none !important; } }
</style>
```

- 화면에서 「메뉴」는 어떻게 보이고, 인쇄 미리보기에서는 어떻게 되나?

### 2. `href` 가 있는 링크와 없는 링크를 인쇄하면 (예측)

```html
<!-- 질문용 발췌 -->
<a href="https://example.com">예제</a>
<a class="print-link">링크 텍스트</a>
<style>
  @media print { a[href]::after { content: " (" attr(href) ")"; } }
</style>
```

- 인쇄 미리보기에서 두 링크는 각각 어떤 글자로 찍히나?

### 3. 쪽 끝에 걸린 제목과 그 뒤의 표 (예측)

```css
/* 질문용 발췌 */
@media print {
  h2 { break-after: avoid; }
  table { break-inside: avoid; }
}
```

- 첫 쪽 맨 아래에 `h2` 한 줄만 겨우 들어가고 바로 뒤 표는 그 쪽에 다 들어가지 않을 때, 브라우저가 이 요청을 따르면 `h2` 와 표는 어느 쪽에 찍히나?

### 4. 인쇄 스타일에서 `!important` 를 쓰는 까닭 (왜)

- 평소에는 꺼리는 `!important` 를 인쇄 규칙에서는 적극 써도 된다고 하는 까닭은 무엇인가?

### 5. 종이에서 링크 주소를 드러내고 배경을 걷는 까닭 (왜)

- 인쇄할 때 링크 뒤에 주소를 붙이고 배경을 없애며 글자를 검정으로 바꾸는 까닭은 각각 무엇인가?

### 6. 정답 코드 데모를 Ctrl+P 로 미리보기 하면 (경계)

- 원본 데모 페이지를 그대로 인쇄 미리보기 하면 「내비게이션 (숨겨짐)」 줄이 정말 사라지나?

### 7. 인라인 스타일 배경과 인쇄 규칙 (경계)

- `<div style="background: yellow">` 에 대해 `@media print { div { background: none !important; } }` 가 있으면 인쇄에서 노란 배경이 남나?

### 8. `@media print` 와 다른 미디어 쿼리 · 별도 파일 (연결)

- `@media print` 블록, `<link media="print">` 파일, 반응형에서 쓰는 화면 너비 미디어 쿼리는 서로 어떤 관계인가?

## 실습

### 실습 1. 인쇄 스타일 안내 카드 만들기

**만들 것** — 인쇄될 페이지 모형(빠질 부분 표시 포함), 인쇄 규칙 다섯 가지 목록, `@media print` 예시 코드 상자를 한 화면에 늘어놓은 안내 카드를 만든다.

**요구 조건**

1단계 — 페이지 모형

1. `.print-preview` 안의 `.print-page` 에 위에서부터 제목(`.print-header`), 내비게이션(`.print-nav`), 본문(`.print-content`), 푸터(`.print-footer`)를 차례로 놓는다.
2. 본문 안에는 단락 하나와 링크(`.print-link`) 하나를 둔다 — 링크 글자 안에 주소를 괄호로 직접 적어 인쇄된 모습을 흉내 낸다.
3. 내비게이션과 푸터에는 `no-print` 클래스를 함께 단다.
4. `.no-print` 는 화면에서 취소선이 그어지고 흐리게 보여 「인쇄 때 빠질 것」임을 드러낸다.

2단계 — 규칙 목록

5. `.print-rules` 안에 `.print-rule` 다섯 개(숨기기 · 링크 URL · 배경 제거 · 텍스트 색상 · 페이지 나누기)를 두고, 각 규칙 이름은 `<strong>` 으로 강조한 뒤 쓰는 꼴을 적는다.
6. `.print-rules` 는 항목을 세로 한 줄로 쌓고 항목 사이에 간격을 둔다.

3단계 — 코드 상자

7. `.print-code` 안의 `<code>` 에 `@media print` 블록 예시를 적는다 — 숨기기(`nav, footer, .sidebar, .no-print`), `body` 의 글자 크기와 색, `a[href]::after` 로 주소 붙이기, `h2, h3` 의 `break-after: avoid`, `table, figure` 의 `break-inside: avoid`, `@page` 여백을 담는다.
8. `<code>` 는 블록으로 그려지고, 적은 공백과 줄바꿈이 그대로 보존된다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>Print Styles</title>
<style>
  .print-demo { font-family: system-ui, sans-serif; }
  .print-preview { margin-bottom: 12px; }
  .print-page { background: white; border: 2px solid #e2e8f0; border-radius: 4px; padding: 16px; box-shadow: 4px 4px 0 #e2e8f0; max-width: 300px; }
  .print-header { font-weight: 700; font-size: 16px; color: #1e293b; margin-bottom: 8px; border-bottom: 1px solid #1e293b; padding-bottom: 4px; }
  .print-nav, .print-footer { font-size: 11px; padding: 4px 8px; border-radius: 4px; }
  .no-print {
    background: #fecaca; color: #991b1b; margin: 4px 0;
    /* TODO: 취소선을 긋고 흐리게 만든다 */
  }
  .print-content { font-size: 12px; color: #374151; line-height: 1.6; margin: 8px 0; }
  .print-link { color: #1d4ed8; font-size: 11px; }
  .print-rules {
    margin-bottom: 12px;
    /* TODO: 항목을 세로로 쌓고 항목 사이에 4px 간격을 둔다 */
  }
  .print-rule { font-size: 11px; padding: 6px 10px; background: #f1f5f9; border-left: 3px solid #64748b; border-radius: 0 4px 4px 0; color: #334155; }
  .print-rule strong { color: #1e293b; }
  .print-code { background: #1e293b; border-radius: 8px; padding: 14px; }
  .print-code code {
    font-size: 11px; color: #e2e8f0; line-height: 1.5;
    /* TODO: 공백과 줄바꿈을 보존하고 블록으로 그린다 */
  }
</style>
</head>
<body>
<div class="print-demo">
  <div class="print-preview">
    <div class="print-page">
      <!-- TODO: 제목 · 내비게이션(no-print) · 본문(단락 + 링크) · 푸터(no-print) -->
    </div>
  </div>
  <div class="print-rules">
    <!-- TODO: .print-rule 다섯 개 (숨기기 · 링크 URL · 배경 제거 · 텍스트 색상 · 페이지 나누기) -->
  </div>
  <div class="print-code">
    <code><!-- TODO: @media print 블록 예시 --></code>
  </div>
</div>
</body>
</html>
```

**확인 방법** — 브라우저로 열어 내비게이션과 푸터에 취소선이 그어져 흐린지, 규칙 다섯 개가 세로로 쌓였는지, 코드 상자 안의 들여쓰기와 줄바꿈이 그대로 보이는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

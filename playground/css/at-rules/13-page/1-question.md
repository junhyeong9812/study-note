# css/at-rules/13 — @page — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 기본 규칙과 `:first` 가 겹치면 (예측)

```css
/* 질문용 발췌 */
@page { size: A4; margin: 2cm; }
@page :first { margin-top: 4cm; }
```

- 세 페이지짜리 문서를 인쇄하면 1쪽의 위쪽 · 왼쪽 여백은 각각 얼마인가?
- 2쪽의 위쪽 여백은 얼마인가?

### 2. 같은 파일을 화면과 인쇄 미리보기에서 (예측)

```css
/* 질문용 발췌 */
@page { size: A4; margin: 2cm; }
.print-preview { border: 2px dashed #d1d5db; }
@media print { .print-preview { border: none; } }
```

- 브라우저 화면에서 이 상자의 점선 테두리는 어떻게 되나?
- 인쇄 미리보기에서 이 상자의 점선 테두리는 어떻게 되나?

### 3. 화면에서는 `@page` 가 왜 아무 일도 안 하나 (왜)
- `@page { margin: 2cm; }` 를 넣어도 화면 모양이 그대로인 까닭은 무엇인가?

### 4. 인쇄 때 테두리를 없애는 규칙이 왜 `@page` 가 아니라 `@media print` 안에 있나 (왜)
- `.print-preview` 의 테두리를 없애는 선언을 `@page` 안에 두지 않는 까닭은 무엇인가?

### 5. 페이지 의사 클래스가 고르는 범위 (경계)
- `@page :left` 와 `@page :right` 는 각각 몇 번째 페이지들에 적용되나?
- `@page :blank` 는 어떤 페이지에 적용되나?

### 6. 「이 장(章) 제목은 항상 새 페이지에서」 (경계)
- 이 요구를 `@page` 규칙만으로 처리할 수 있나, 없다면 무엇을 써야 하나?

### 7. 인쇄용 CSS 의 세 도구 (연결)
- `@page` · `@media print` · `break-before`/`break-after` 는 인쇄 레이아웃에서 각각 무엇을 맡나?

## 실습

### 실습 1. 인쇄용 페이지 설정과 인쇄 전용 스타일 붙이기

**만들 것** — 안내 상자 하나가 있는 HTML 문서에 인쇄용 페이지 규칙과 인쇄 전용 스타일을 붙인다.

**요구 조건**
1. 인쇄하면 모든 페이지가 A4 크기가 되고, 사방 여백이 2cm 가 되게 한다.
2. 첫 페이지만 위쪽 여백을 4cm 로 늘리고, 나머지 방향의 여백은 기본 규칙을 따르게 한다.
3. 안내 상자는 화면에서는 점선 테두리를 그대로 보이고, 인쇄할 때만 테두리가 없어지게 한다.
4. 위 세 규칙은 모두 하나의 `<style>` 안에 둔다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>@page 연습</title>
  <style>
    /* TODO: 모든 인쇄 페이지에 적용되는 규칙 — 크기와 사방 여백 */

    /* TODO: 첫 페이지에만 적용되는 규칙 — 위쪽 여백만 */

    .print-preview {
      padding: 20px;
      background: white;
      border: 2px dashed #d1d5db;
      border-radius: 8px;
      text-align: center;
      color: #6b7280;
    }

    /* TODO: 인쇄할 때만 .print-preview 의 테두리를 없애는 규칙 */
  </style>
</head>
<body>
  <div class="print-preview">인쇄 미리보기 (Ctrl+P로 확인)</div>
</body>
</html>
```

**확인 방법** — 브라우저로 파일을 열어 화면에서 점선 상자가 보이는지 확인한다. 그다음 `Ctrl+P` 로 인쇄 미리보기를 열어 테두리가 사라졌는지, 첫 페이지의 위쪽 여백이 다른 방향보다 넓은지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

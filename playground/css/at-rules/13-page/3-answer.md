# css/at-rules/13 — @page — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 1쪽은 위 4cm · 왼쪽 2cm, 2쪽은 위 2cm

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- 1쪽: 위쪽 여백 4cm, 왼쪽 여백 2cm.
- 2쪽: 위쪽 여백 2cm.

**왜 그런가**

기본 `@page` 가 모든 페이지에 사방 2cm 를 준다.
`@page :first` 는 첫 페이지에만 붙고, `margin-top` 하나만 선언하므로 1쪽의 위쪽만 4cm 로 바뀐다.
1쪽의 왼쪽은 선언되지 않았으니 기본 규칙의 2cm 를 쓴다.
2쪽은 `:first` 에 해당하지 않아 기본 규칙만 적용된다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 3」.

### 2. 화면에서는 점선이 있고, 인쇄 미리보기에서는 사라진다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- 화면: 점선 테두리가 보인다 (코드에서 읽은 것 — 렌더 실측 아님).
- 인쇄 미리보기: 테두리가 없다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**

화면에서는 `@media print` 안의 규칙이 적용되지 않으므로 `.print-preview` 의 점선 테두리가 그대로 남는다.
`@page` 도 화면에는 영향을 주지 않는다.
인쇄할 때는 `@media print` 안의 `border: none;` 이 적용되어 테두리가 사라진다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (4)」.

### 3. 화면에는 「페이지」가 없기 때문이다

`@page` 는 인쇄할 때 내용이 나뉘어 담기는 페이지 박스(종이)를 설정하는 인쇄 전용 규칙이다.
화면은 하나로 이어진 면이라 페이지 박스가 없고, 규칙이 적용될 곳도 없다.
그래서 결과는 인쇄 미리보기나 실제 인쇄에서만 볼 수 있다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 1」.

### 4. `@page` 는 종이를 다루고 요소를 꾸미지 않기 때문이다

`@page` 의 선언은 페이지 박스의 크기와 여백 같은 종이의 성질에 적용된다.
`.print-preview` 의 테두리는 문서 안 요소의 모양이므로 선택자 규칙으로 바꿔야 한다.
이 규칙을 인쇄할 때만 적용하려면 `@media print` 안에 둔다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 2」.

### 5. `:left` 는 짝수, `:right` 는 홀수, `:blank` 는 빈 페이지

- `:left` — 왼쪽(짝수) 페이지들.
- `:right` — 오른쪽(홀수) 페이지들.
- `:blank` — 내용이 없는 빈 페이지.

근거: 2-summary 「동작 방식 (3)」의 의사 클래스 표 · 「어디서 틀리나 5」.

### 6. `@page` 만으로는 안 되고, 제목 요소에 `break-before` 를 준다

`@page` 는 페이지의 크기와 여백을 정할 뿐, 어디서 페이지를 나눌지는 정하지 않는다.
페이지 나누기는 요소에 주는 `break-before` · `break-after` 가 제어한다.
「제목 앞에서 새 페이지」라면 제목 요소에 `break-before` 를 준다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 4」.

### 7. 종이 · 요소 모양 · 나눌 자리

- `@page` — 종이(페이지 박스)의 크기와 여백, 특정 페이지의 덮어쓰기.
- `@media print` — 인쇄할 때만 적용할 요소 스타일(테두리 없애기, 숨기기 등).
- `break-before` · `break-after` — 요소 앞 · 뒤에서 페이지를 나누는 지시.

원본 팁이 셋을 함께 쓰라고 권하는 까닭도 이 역할 나눔 때문이다.
근거: 2-summary 「동작 방식 (4)」 · 「핵심 문장」.

## 실습 정답

### 실습 1. 인쇄용 페이지 설정과 인쇄 전용 스타일 붙이기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 모든 페이지 A4 · 사방 여백 2cm | `@page { size: A4; margin: 2cm; }` |
| 2. 첫 페이지만 위쪽 여백 4cm | `@page :first { margin-top: 4cm; }` |
| 3. 인쇄할 때만 안내 상자 테두리 없애기 | `@media print { .print-preview { border: none; } }` |
| 4. 하나의 `<style>` 안에 두기 | `<head>` 안의 `<style>` 블록 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/at-rules/reference/page.html`

```html
<!DOCTYPE html>
<!-- DOCTYPE 선언: HTML5 문서임을 알림 -->
<html lang="ko">
<!-- html 루트 요소: 문서 언어를 한국어로 지정 -->
<head>
  <!-- head: 메타데이터/스타일 영역 -->
  <meta charset="utf-8">
  <!-- meta charset: 문자 인코딩을 UTF-8로 지정 -->
  <title>@page - 인쇄 시 페이지의 레이아웃을 설정한다. 마진, 크기, 방향 등을 지정할 수 있다.</title>
  <!-- title: 브라우저 탭 제목 -->
  <!--
    [At-규칙] @page
    설명: 인쇄 시 페이지의 레이아웃을 설정한다. 마진, 크기, 방향 등을 지정할 수 있다.
    구문: @page [<name>] [:<pseudo>] { <declarations> }
    팁: @page는 인쇄 전용이다. @media print와 함께 사용하여 인쇄 친화적 레이아웃을 만들자. break-before, break-after로 페이지 나누기를 제어할 수 있다.
  -->
  <style>
    /* @page: 인쇄 시 모든 페이지에 적용되는 페이지 박스 규칙 */
    @page {
      size: A4;               /* 인쇄 페이지 크기 - A4 */
      margin: 2cm;            /* 페이지 사방 여백 - 2cm */
    }

    /* @page :first: 인쇄 시 첫 번째 페이지에만 적용되는 규칙 (의사 클래스) */
    @page :first {
      margin-top: 4cm;        /* 첫 페이지 위쪽 여백만 4cm로 늘림 - 표지 등에 활용 */
    }

    /* .print-preview: 인쇄 미리보기 안내 박스 */
    .print-preview {
      padding: 20px;                  /* 사방 20px 내부 여백 */
      background: white;              /* 배경색 - 흰색 */
      border: 2px dashed #d1d5db;     /* 점선 회색 테두리 2px */
      border-radius: 8px;             /* 모서리 8px 둥글게 */
      text-align: center;             /* 텍스트 가운데 정렬 */
      color: #6b7280;                 /* 글자색 - 회색 */
    }

    /* @media print: 인쇄 출력일 때만 적용되는 미디어 쿼리 */
    @media print {
      /* .print-preview: 인쇄 시 점선 테두리 제거 */
      .print-preview {
        border: none;         /* 인쇄용으로 테두리 숨김 */
      }
    }
  </style>
</head>
<body>
  <!-- body: 화면에 보이는 콘텐츠 -->
  <div class="print-preview">인쇄 미리보기 (Ctrl+P로 확인)</div>
  <!-- 인쇄 미리보기 안내 박스 - Ctrl+P로 @page 효과 확인 -->
</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
@page { size: A4; margin: 2cm; }
@page :first { margin-top: 4cm; }

.print-preview { padding: 20px; background: white; border: 2px dashed #d1d5db; border-radius: 8px; text-align: center; color: #6b7280; }
@media print { .print-preview { border: none; } }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 이름 · 의사 클래스가 없는 `@page` 는 모든 페이지에 적용되는 기본 규칙이다.
- `@page :first` 에는 바꿀 속성(`margin-top`)만 쓴다 — 나머지 여백은 기본 규칙에서 온다.
- 화면용 점선 테두리는 `.print-preview` 에 그대로 두고, 인쇄용 변경만 `@media print` 안에 둔다.
- `@page` 안에 요소 스타일을 넣지 않는다 — 종이 설정과 요소 스타일은 맡는 곳이 다르다.
- 결과는 화면이 아니라 인쇄 미리보기에서 확인한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

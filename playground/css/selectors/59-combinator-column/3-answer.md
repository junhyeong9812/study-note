# css/selectors/59 — || 열 결합자 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. A1 과 A2 — 첫 열의 셀이 칠해져 보인다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
A1 · A2 가 연한 파란 배경으로 보이고, B1 · B2 는 배경이 없다.
(코드에서 읽은 것 — 렌더 실측 아님)

**왜 그런가**
`highlight-col` 클래스는 첫 번째 `<col>` 에만 있다.
그 `<col>` 은 1열을 정의하고, 1열에 놓인 셀은 각 행의 첫 `td` 인 A1 · A2 다.
`<col>` 의 배경이 그 열 셀 뒤에 비쳐 보인다.
근거: 2-summary 「동작 방식 (3)」.

### 2. `<col>` 의 배경이 그 열 셀 뒤에 깔리기 때문이다

선택자는 `<col>` 요소 자신에 배경을 준다.
그 배경이 같은 세로줄에 놓인 셀들 아래로 비쳐서, 화면에서는 셀이 칠해진 것처럼 보인다.
셀을 고른 것이 아니라 열 정의 요소를 꾸민 것이다.
근거: 2-summary 「동작 방식 (3)」.

### 3. `<td>` 는 `<col>` 의 자손이 아니기 때문이다

공백 결합자는 「왼쪽 요소 안에 든 오른쪽 요소」를 찾는다.
`<col>` 은 `<colgroup>` 안의 빈 요소이고, `<td>` 의 부모는 `<tr>` 이다.
둘은 문서 트리에서 조상·자손이 아니어서 매칭되는 `td` 가 없다.
근거: 2-summary 「동작 방식 (1)」, 「어디서 틀리나 2」.

### 4. 빨간색이 되지 않는다 — 규칙 전체가 버려진다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`.note` 의 글자색은 바뀌지 않는다.

**왜 그런가**
CSS 는 해석하지 못하는 선택자가 있으면 그 규칙을 통째로 버린다.
쉼표로 묶은 선택자 목록에서 하나만 무효여도 목록 전체가 무효다.
`col.price || td` 가 무효이므로 같은 규칙의 `.note` 도 함께 버려진다.
근거: 2-summary 「동작 방식 (4)」, 「어디서 틀리나 5」.

### 5. 물려 내려가지 않는다 — 상속은 문서 트리를 따른다

상속은 부모 → 자식으로 흐르고, `<td>` 의 부모는 `<tr>` 이다.
`<col>` 은 셀의 조상이 아니라서 `color` 가 셀로 상속되지 않는다.
원본 예제도 `<col>` 에 배경만 준다.
근거: 2-summary 「어디서 틀리나 3」.

### 6. `colspan` 으로 병합된 셀이 있는 표에서 깨진다

`:nth-child(2)` 는 행 안에서 두 번째 형제 셀을 고를 뿐이다.
앞 셀이 `colspan="2"` 면 두 번째 형제 셀은 실제로 세 번째 열에 놓인다.
그래서 형제 순서와 열 위치가 어긋난다.
근거: 2-summary 「어디서 틀리나 4」.

### 7. 다른 결합자는 문서 트리를, `||` 는 표 격자(세로줄)를 따라간다

공백은 자손, `>` 는 자식, `+` 는 바로 다음 형제 — 모두 문서 트리의 관계다.
`||` 는 트리에서 이어지지 않은 `<col>` 과 `<td>` 를 「같은 열에 놓였다」는 표 격자 관계로 잇는다.
근거: 2-summary 「동작 방식 (2)」.

## 실습 정답

### 실습 1. 2×2 표에서 첫 열만 강조하기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 표에 `col-demo` 클래스 | `<table class="col-demo">` |
| `<colgroup>` 안에 `<col>` 두 개 | `<colgroup>` · `<col class="highlight-col" />` · `<col />` |
| 첫 `<col>` 에만 `highlight-col` | `<col class="highlight-col" />` |
| 두 행에 A1 · B1 / A2 · B2 | 두 `<tr>` 의 `<td>` 들 |
| 이웃한 테두리 합치기 | `.col-demo { border-collapse: collapse; }` |
| 강조 열 선택자로 배경 규칙 | `.col-demo .highlight-col { background: … }` |
| `\|\|` 를 쓰지 않는다 | 스타일 어디에도 `\|\|` 가 없다 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/selectors/reference/combinator-column.html`

```html
<!DOCTYPE html>
<!-- 문서 타입 선언: HTML5 -->
<html lang="ko">
<head>
<meta charset="utf-8">
<title>|| 열 결합자 - 테이블의 특정 열에 속하는 셀을 선택한다. (실험적 기능, 브라우저 지원 제한적)</title>
<!--
  [선택자] || 열 결합자
  설명: 테이블의 특정 열에 속하는 셀을 선택한다. (실험적 기능, 브라우저 지원 제한적)
  구문: col || td { }
  팁: 열 결합자(||)는 아직 실험적 기능이며 브라우저 지원이 거의 없다. 현재는 <col> 요소에 클래스를 적용하는 방식을 사용하자.
-->
<style>
  /* .col-demo: class 속성에 col-demo를 가진 테이블 매칭 */
  .col-demo {
    border-collapse: collapse;   /* 인접 셀 테두리 합치기 */
    width: 200px;                /* 테이블 너비 200px */
  }
  /* .col-demo td: .col-demo의 자손 td 매칭 */
  .col-demo td {
    padding: 10px;               /* 안쪽 여백 10px */
    border: 1px solid #e5e7eb;   /* 1px 회색 테두리 */
    text-align: center;          /* 가운데 정렬 */
  }
  /* .col-demo .highlight-col: .col-demo 자손 중 highlight-col 클래스 매칭 (col 요소) */
  .col-demo .highlight-col {
    background: #dbeafe;         /* 강조 열의 연한 파란 배경 */
  }
</style>
</head>
<body>
  <table class="col-demo">
    <!-- 열 정의 그룹 -->
    <colgroup>
      <!-- 첫 번째 열 (강조됨) -->
      <col class="highlight-col" />
      <!-- 두 번째 열 -->
      <col />
    </colgroup>
    <!-- 첫 번째 행 -->
    <tr><td>A1</td><td>B1</td></tr>
    <!-- 두 번째 행 -->
    <tr><td>A2</td><td>B2</td></tr>
  </table>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.col-demo { border-collapse: collapse; width: 200px; }
.col-demo td { padding: 10px; border: 1px solid #e5e7eb; text-align: center; }
.col-demo .highlight-col { background: #dbeafe; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- `.col-demo .highlight-col` 이 고르는 것은 `<col>` 이고, 그 배경이 1열 셀 뒤에 비쳐 보인다.
- 열 정의는 `<colgroup>` 안 `<col>` 로 하고, 셀은 여전히 `<tr>` 안에 둔다.
- `<col>` 의 순서가 곧 열의 순서다 — 첫 `<col>` 이 첫 열이다.
- 원본 팁대로 실험적 `||` 대신 `<col>` 클래스 방식을 썼다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

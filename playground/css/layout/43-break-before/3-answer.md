# css/layout/43 — break-before — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 왼쪽 열에 A 만, 오른쪽 열에 B 와 C

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

왼쪽 열에는 문단 A 만 놓인다.
오른쪽 열 맨 위에 제목 B 가 오고, 그 아래에 문단 C 가 이어진다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**

`column` 은 요소 앞에서 열 나누기를 강제하는 값이다.
첫 열에 공간이 남아 있어도 h3 앞에서 끊으므로, h3 과 그 뒤 내용은 다음 열로 간다.
근거: 2-summary 「동작 방식 (1)」.

### 2. 장담할 수 없다 — 브라우저가 정한다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

제목 B 가 왼쪽 열 아래쪽에 남을 수도, 오른쪽 열로 넘어갈 수도 있다.

**왜 그런가**

`auto` 는 나누기를 허용하지만 강제하지 않는 기본값이다.
어디서 자를지는 브라우저가 열 높이에 맞춰 정한다.
근거: 2-summary 「동작 방식 (3)」.

### 3. 매번 오른쪽 페이지에서 시작한다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

각 장 제목 앞에서 페이지가 넘어가고, 그 다음 페이지가 오른쪽 페이지가 되도록 강제된다.
그래서 장 제목은 오른쪽 페이지에서 시작한다.

**왜 그런가**

`right` 는 「다음 페이지가 오른쪽 페이지가 되도록 강제」하는 값이다.
`@media print` 안에 있으니 페이지가 있는 인쇄에서 적용된다.
근거: 2-summary 「동작 방식 (1)」 · 「문법」의 값 표.

### 4. 상속되지 않고, 컨테이너 자신의 앞자리에 대한 지시라서

`break-before` 는 상속되지 않는다.
컨테이너에 준 값은 컨테이너 자신 앞에서의 나누기만 다루고 안쪽 h3 에는 내려가지 않는다.
새 열에서 시작할 요소(h3)에 직접 줘야 한다.
근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 3」.

### 5. 애니메이션 가능 속성이 아니라서 — 키워드 사이에 중간값이 없다

`break-before` 는 애니메이션 가능 속성이 아니다.
값이 `auto` · `column` 같은 키워드라, 둘 사이의 「반쯤 나눈 상태」 같은 중간값이 없다.
값을 바꾸면 곧바로 새 값이 적용된다.
근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 6」.

### 6. `avoid` 는 전부, `avoid-column` 은 열만, `avoid-page` 는 페이지만

- `avoid` — 요소 앞의 모든 나누기를 막는다.
- `avoid-column` — 열 나누기만 막는다.
- `avoid-page` — 페이지 나누기만 막는다.

셋 다 「가능하면 자르지 마라」는 요청이라, 내용이 너무 길면 어딘가에서는 잘린다 (원본에 근거 없음 — 추론).
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 5」.

### 7. 아무 변화가 없다

열 나누기는 다단 컨테이너 안에서만 일어난다.
평범한 화면 블록에는 끊을 열이 없으므로 요소는 평소처럼 이어서 놓인다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 4」.

### 8. 현대적 대체 · 다단 맥락을 만드는 짝

`break-before` 는 레거시 `page-break-before` 의 현대적 대체다.
옛 속성이 페이지 나누기 중심이었다면, `break-before` 는 페이지와 열 나누기를 한 속성으로 다룬다.
`column-count` 는 상자를 다단으로 만들어 열 나누기가 일어날 맥락을 만든다.
그 안의 요소에 `break-before: column` 을 주면 그 요소 앞에서 열이 끊긴다.
근거: 2-summary 「어디서 틀리나 1 · 2」 · 「동작 방식 (4)」.

## 실습 정답

### 실습 1. 2단 상자에서 제목을 둘째 열로 보내기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 두 열로 나눠 흘린다 | `.multicol { column-count: 2; }` |
| 2. 문단 · 제목 · 문단의 차례 | `<div class="multicol">` 안의 `<p>` · `<h3 class="break">` · `<p>` |
| 3. 제목 앞에서 열 나누기 강제 | `.break { break-before: column; }` |
| 4. 첫 문단이 첫 열에 혼자 남는다 | `break-before: column` 이 h3 앞에서 열을 끊은 결과 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/layout/reference/break-before.html`

```html
<!DOCTYPE html>
<!-- HTML5 문서 선언 -->
<html lang="ko">
<head>
<meta charset="utf-8">
<title>break-before - 요소 앞에서의 페이지, 열 또는 영역 나누기를 제어합니다</title>
<!--
  [레이아웃] break-before
  설명: 요소 앞에서의 페이지, 열 또는 영역 나누기를 제어합니다
  구문: break-before: auto | avoid | always | column | page | left | right | avoid-page | avoid-column
  팁: 레거시 page-break-before 속성의 현대적 대체입니다. 다단 레이아웃에서 열 나누기를 제어할 때 break-before: column을 사용하세요.
-->
<style>
  /* .multicol: 2단 다단 컨테이너 */
  .multicol {
    column-count: 2;             /* 2개 열 */
    column-gap: 20px;            /* 열 간격 */
    background: #f1f5f9;         /* 회색 배경 */
    padding: 16px;               /* 안쪽 여백 */
    border-radius: 4px;          /* 모서리 둥글게 */
  }
  /* .break: 이 요소 앞에서 새 열로 강제 분리 */
  .break {
    break-before: column;        /* 이 요소 직전에 열 나누기 강제 */
    background: #3b82f6;         /* 파란 배경 */
    color: white;                /* 흰 글자 */
    padding: 4px 12px;           /* 안쪽 여백 */
    border-radius: 4px;          /* 모서리 둥글게 */
    margin: 0 0 8px;             /* 아래 여백만 */
  }
</style>
</head>
<body>
<!-- 두 번째 제목이 새 열에서 시작 -->
<div class="multicol">
  <p>First column content here.</p>
  <h3 class="break">New Column</h3>          <!-- 이 앞에서 열 분리 -->
  <p>Second column content here.</p>
</div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.multicol {
  column-count: 2;
  column-gap: 20px;
  background: #f1f5f9;
  padding: 16px;
  border-radius: 4px;
}
.break {
  break-before: column;
  background: #3b82f6;
  color: white;
  padding: 4px 12px;
  border-radius: 4px;
  margin: 0 0 8px;
}
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- `column-count: 2` 가 있어야 열 나누기가 일어날 맥락이 생긴다.
- `break-before` 는 컨테이너가 아니라 새 열에서 시작할 `h3.break` 에 준다.
- `column` 은 강제 값이라, 첫 열에 자리가 남아도 h3 앞에서 끊는다.
- 다단에서 열을 넘길 때는 `page` 나 `page-break-before` 가 아니라 `column` 을 쓴다.
- 색 · 여백 · 둥근 모서리는 꾸밈일 뿐 나누기와 상관없다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

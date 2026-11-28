# css/layout/44 — break-after — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 두 문단 모두 둘째 열에 놓인다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
첫 열에는 `h3` 만 있고, `First column content.` 와 `Second column content.` 는 둘 다 둘째 열에 위아래로 쌓인다. (코드에서 읽은 것 — 렌더 실측 아님)

**왜 그런가**
`break-after: column` 은 `h3` 뒤의 경계에서 열 나누기를 강제한다.
첫 열에 자리가 남아 있어도 `h3` 직후에 끊기므로, 다음 형제인 첫 문단부터 둘째 열에서 시작한다.
열이 둘뿐이라 나머지 문단도 둘째 열에 이어진다.
근거: 2-summary 「동작 방식 (2)」.

### 2. 첫 열에는 제목과 첫 문단이 놓인다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
첫 열에는 `h3` 와 `First column content.` 가 있고, `Second column content.` 만 둘째 열에서 시작한다. (코드에서 읽은 것 — 렌더 실측 아님)

**왜 그런가**
나누기는 `break-after` 를 건 요소의 **뒤**에서 일어난다.
이번에는 첫 문단에 걸었으므로 첫 문단까지는 첫 열에 남고, 그 다음 형제부터 넘어간다.
근거: 2-summary 「어디서 틀리나 1」.

### 3. `break-after` 는 요소 뒤의 경계를 끊기 때문이다

「문단부터 새 열」은 「제목과 문단 사이에서 끊어라」와 같은 말이다.
`break-after` 는 건 요소와 그 다음 내용 사이를 다루므로, 그 경계의 앞쪽 요소인 제목에 건다.
문단에 걸면 문단 뒤에서 끊겨 한 칸 늦어진다.
근거: 2-summary 「핵심 문장 1」 · 「어디서 틀리나 1」.

### 4. 바뀌지 않는다 — 상속되지 않고 컨테이너 자기 뒤에만 걸린다

`break-after` 의 상속은 `False` 라서 자식 `h3` · `p` 는 값을 물려받지 않는다.
컨테이너에 건 선언은 컨테이너 자신과 그 다음 내용 사이 경계에만 해당하므로, 안의 열 배치는 기본값 `auto` 처럼 브라우저가 알아서 나눈다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 2」.

### 5. 충분하지 않다 — `avoid-column` 은 열 나누기만 피한다

`avoid-column` 은 열 나누기만 피하고 페이지 나누기는 막지 않는다.
페이지 나누기를 피하려면 `avoid-page`, 둘 다 피하려면 `avoid` 를 쓴다.
근거: 2-summary 「동작 방식 (3)」 · 「문법 — 형태와 규칙」의 값 표.

### 6. 내용이 한 열 · 한 페이지에 다 들어가지 않아 다른 끊을 자리가 없을 때

방지는 「끊을 자리를 고를 때 여기는 피해 달라」는 요청이다.
피할 다른 자리가 없으면 브라우저가 그 자리에서도 끊을 수 있다.
원본은 「모든 나누기를 방지합니다」라고 적지만, 「되도록 피함」으로 읽는 편이 안전하다.
근거: 2-summary 「어디서 틀리나 3」 (원본에 근거 없음 — 추론).

### 7. `page-break-after` 의 현대적 대체이며, 열 · 영역 나누기까지 다룬다

원본 팁대로 `break-after` 는 레거시 `page-break-after` 를 대체한다.
옛 속성은 이름처럼 페이지만 다루지만, `break-after` 는 `column` · `avoid-column` 처럼 열 나누기까지 한 속성으로 고른다.
근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 5」.

### 8. 책 인쇄 — 왼쪽 · 오른쪽 페이지가 있는 출력과 이어진다

`left` · `right` 는 페이지 나누기를 강제하면서 다음 페이지가 왼쪽 또는 오른쪽 페이지가 되게 한다.
왼쪽 · 오른쪽 페이지는 책을 펼친 면에서 생기는 개념이라, 열만 있는 화면의 다단 레이아웃과는 맞물리지 않는다.
근거: 2-summary 「동작 방식 (2)」 · 「언제 쓰고 언제 안 쓰나」 (원본에 근거 없음 — 추론).

## 실습 정답

### 실습 1. 제목 다음 본문을 둘째 열에서 시작하는 2단 박스

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 2개 열로 나눠 흘린다 | `.multicol { column-count: 2; }` |
| 2. 제목 하나 · 문단 둘을 차례로 | `<div class="multicol">` 안의 `<h3>` · `<p>` · `<p>` |
| 3. 제목에 `break` 클래스 | `<h3 class="break">First Section</h3>` |
| 4. 제목 뒤에서 열 나누기 강제 | `.break { break-after: column; }` |
| 5. 꾸밈은 그대로 | `.multicol` 의 `column-gap` · `background` · `padding` · `border-radius`, `.break` 의 `background` · `color` · `padding` · `border-radius` · `margin` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/layout/reference/break-after.html`

```html
<!DOCTYPE html>
<!-- HTML5 문서 선언 -->
<html lang="ko">
<head>
<meta charset="utf-8">
<title>break-after - 요소 뒤에서의 페이지, 열 또는 영역 나누기를 제어합니다</title>
<!--
  [레이아웃] break-after
  설명: 요소 뒤에서의 페이지, 열 또는 영역 나누기를 제어합니다
  구문: break-after: auto | avoid | always | column | page | left | right | avoid-page | avoid-column
  팁: 레거시 page-break-after 속성의 현대적 대체입니다.
-->
<style>
  /* .multicol: 2단 다단 컨테이너 */
  .multicol {
    column-count: 2;             /* 2개 열로 나눔 */
    column-gap: 20px;            /* 열 사이 간격 */
    background: #f1f5f9;         /* 회색 배경 */
    padding: 16px;               /* 안쪽 여백 */
    border-radius: 4px;          /* 모서리 둥글게 */
  }
  /* .break: 이 요소 뒤에서 새 열로 강제 분리 */
  .break {
    break-after: column;         /* 이 요소 다음에 열 나누기 강제 */
    background: #3b82f6;         /* 파란 배경 */
    color: white;                /* 흰 글자 */
    padding: 4px 12px;           /* 안쪽 여백 */
    border-radius: 4px;          /* 모서리 둥글게 */
    margin: 0 0 8px;             /* 아래 여백만 */
  }
</style>
</head>
<body>
<!-- 제목 다음에서 열을 나눠 본문이 다음 열에서 시작 -->
<div class="multicol">
  <h3 class="break">First Section</h3>      <!-- 이 뒤에서 열 분리 -->
  <p>First column content.</p>
  <p>Second column content.</p>
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
  break-after: column;
  background: #3b82f6;
  color: white;
  padding: 4px 12px;
  border-radius: 4px;
  margin: 0 0 8px;
}
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 다단 흐름(`column-count: 2`)이 있어야 열 나누기가 의미를 갖는다.
- `break-after: column` 은 끊고 싶은 경계의 앞 요소인 `h3` 에 건다.
- 상속되지 않으므로 컨테이너가 아니라 `.break` 요소 자체에 건다.
- 결과로 첫 열에는 제목만, 둘째 열에는 두 문단이 온다. (코드에서 읽은 것 — 렌더 실측 아님)
- `margin: 0 0 8px` 은 제목 아래 여백만 남기는 꾸밈이라 나누기 동작과는 따로다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

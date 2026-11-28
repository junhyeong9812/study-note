# css/layout/45 — break-inside — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 놓일 수 있다 — `auto` 는 카드 내부의 나누기를 허용한다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`break-inside` 가 없으면 카드는 기본값 `auto` 다.
브라우저가 열 높이를 맞추려고 끊을 자리를 고를 때 카드 1 의 안쪽도 후보가 된다.
그래서 카드 1 의 윗부분은 왼쪽 열, 아랫부분은 오른쪽 열에 놓일 수 있다 (코드에서 읽은 것 — 렌더 실측 아님).
실제로 걸칠지는 내용 길이와 열 너비에 따라 달라진다.

**왜 그런가**
`auto` 는 「나누기를 허용한다」는 값이고 기본값이다.
근거: 2-summary 「동작 방식 (1)」 · 「문법 — 형태와 규칙」의 값 표.

### 2. 카드 1 이 한 열 안에 온전히 놓인다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
카드 안쪽이 끊을 후보에서 빠지므로, 끊는 자리는 카드 앞이나 뒤로 밀린다.
카드 1 은 잘리지 않고 한 열에 통째로 들어간다 (코드에서 읽은 것 — 렌더 실측 아님).
어느 열에 들어갈지, 다른 카드가 어떻게 나뉠지는 내용 높이에 달려 있다.

**왜 그런가**
`avoid` 는 요소 내부의 모든 나누기를 막는다.
근거: 2-summary 「동작 방식 (2)」.

### 3. 막을 수 없다 — `break-inside` 는 상속되지 않는다

컨테이너에 건 값은 카드에게 내려가지 않으므로 카드는 여전히 `auto` 다.
카드 안쪽에서 열 나누기가 일어날 수 있는 상태가 그대로 남는다.
카드를 지키려면 `.card` 에 직접 건다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 1」.

### 4. 보장되지 않는다 — `avoid-column` 은 열 나누기만 막는다

`avoid-column` 은 열 경계에서만 카드를 지킨다.
인쇄에서 생기는 페이지 나누기는 막지 않으므로 쪽 끝에서 카드가 끊길 수 있다.
화면의 열과 인쇄의 페이지를 함께 지키려면 `avoid` 를 쓴다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 3」.

### 5. `break-inside` 는 한 요소의 「안쪽」만 지키기 때문이다

이 속성은 요소 내부에서 끊어도 되는지를 정한다.
이미지와 캡션이 따로 떨어진 형제라면 둘 사이는 어느 한 요소의 내부가 아니므로 지킬 대상이 없다.
둘을 한 요소로 감싸면 둘 사이가 그 요소의 내부가 되고, `avoid` 가 그 사이의 나누기를 막는다.
근거: 2-summary 「어디서 틀리나 2」 (원본 팁).

### 6. 서서히 바뀌지 않는다 — 애니메이션 가능한 속성이 아니다

`break-inside` 는 애니메이션 되지 않으므로 `transition` 이 중간 단계를 만들지 못한다.
값은 즉시 바뀌고 배치도 한 번에 바뀐다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 5」.

### 7. `column-count` 는 컨테이너에, `break-inside` 는 자식 요소에 건다

`column-count` 를 준 컨테이너가 내용을 여러 열로 나누어 끊을 자리(열 경계)를 만든다.
`break-inside` 는 그 안에 흐르는 자식 요소에 걸려, 자기 안쪽은 끊을 자리로 쓰지 말라고 말한다.
책꽂이 비유로는 칸을 나누는 것이 컨테이너, 「찢지 마시오」 딱지가 붙는 것이 책이다.
근거: 2-summary 「한눈에 — 쉽게 말하면」의 대응표 · 「문법 — 형태와 규칙」의 규칙.

## 실습 정답

### 실습 1. 카드가 잘리지 않는 2단 레이아웃 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 내용이 두 열로 흐른다 | `.multicol { column-count: 2; }` |
| 2. 두 열 사이 간격 | `.multicol { column-gap: 16px; }` |
| 3. 카드 셋이 차례로, 카드 1 이 가장 길다 | `<div class="multicol">` 안의 `.card` 세 개 (`Card 1 with longer content…`) |
| 4. 카드가 열 경계에서 쪼개지지 않는다 | `.card { break-inside: avoid; }` |
| 5. 규칙은 카드에 건다 | `break-inside` 가 `.multicol` 이 아니라 `.card` 선택자 안에 있다 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/layout/reference/break-inside.html`

```html
<!DOCTYPE html>
<!-- HTML5 문서 선언 -->
<html lang="ko">
<head>
<meta charset="utf-8">
<title>break-inside - 요소 내부에서의 페이지, 열 또는 영역 나누기를 제어합니다</title>
<!--
  [레이아웃] break-inside
  설명: 요소 내부에서의 페이지, 열 또는 영역 나누기를 제어합니다
  구문: break-inside: auto | avoid | avoid-page | avoid-column | avoid-region
  팁: 다단 레이아웃에서 카드나 이미지+캡션 같은 관련 콘텐츠가 분리되지 않도록 할 때 break-inside: avoid를 사용하세요.
-->
<style>
  /* .multicol: 2단 다단 컨테이너 */
  .multicol {
    column-count: 2;             /* 2개 열 */
    column-gap: 16px;            /* 열 간격 */
    background: #f1f5f9;         /* 회색 배경 */
    padding: 16px;               /* 안쪽 여백 */
    border-radius: 4px;          /* 모서리 둥글게 */
  }
  /* .card: 내부에서 절대 분리되지 않는 카드 */
  .card {
    break-inside: avoid;         /* 카드 내부에서 열/페이지 나누기 회피 */
    background: white;           /* 흰 배경 */
    padding: 12px;               /* 안쪽 여백 */
    margin-bottom: 8px;          /* 아래 여백 */
    border-radius: 4px;          /* 모서리 둥글게 */
    border: 1px solid #e2e8f0;   /* 연회색 테두리 */
  }
</style>
</head>
<body>
<!-- 카드가 두 열에 걸쳐 잘리지 않게 함 -->
<div class="multicol">
  <div class="card">Card 1 with longer content that should stay together.</div>
  <div class="card">Card 2 with content.</div>
  <div class="card">Card 3 with content.</div>
</div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.multicol {
  column-count: 2;
  column-gap: 16px;
  background: #f1f5f9;
  padding: 16px;
  border-radius: 4px;
}
.card {
  break-inside: avoid;
  background: white;
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 4px;
  border: 1px solid #e2e8f0;
}
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 열을 만드는 일(`column-count` · `column-gap`)은 컨테이너가, 쪼개짐을 막는 일(`break-inside`)은 카드가 맡는다.
- `break-inside` 는 상속되지 않으므로 컨테이너에 걸면 카드가 지켜지지 않는다.
- `avoid` 를 쓰면 열 나누기뿐 아니라 인쇄할 때의 페이지 나누기도 피한다.
- 카드 1 을 가장 길게 둔 것은 `auto` 였다면 잘리기 쉬운 상황을 만들어 `avoid` 의 효과를 보기 위해서다.
- 배경 · 여백 · 테두리 값은 꾸밈이고, 배울 핵심은 `column-count` · `column-gap` · `break-inside` 세 줄이다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

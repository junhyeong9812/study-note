# css/layout/41 — column-span — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 제목 아래, 첫 열의 맨 위에서 새로 시작한다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
문단 B 는 제목 띠 바로 아래, 왼쪽 첫 열의 맨 위에서 시작한다.
제목 위쪽 열에 빈 공간이 있어도 그리로 올라가지 않는다.

**왜 그런가**
`column-span: all` 인 제목은 흐름을 위아래 두 덩어리로 끊는다.
제목 뒤의 내용은 제목 아래에서 열1부터 다시 나뉘어 담긴다 (2-summary 「동작 방식 (2)」 · 「어디서 틀리나 2」).

### 2. 열 하나의 폭과 같아진다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
제목 띠는 세 열 중 하나의 폭만 차지하고, 문단 A · 제목 · 문단 B 가 한 줄기로 이어져 열들에 나뉘어 담긴다.
보이는 것: 좁은 파란 띠가 어느 한 열 안에 끼어 있다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
기본값 `none` 에서는 제목도 흐름의 한 조각이라 열 하나 안에서 흐른다 (2-summary 「동작 방식 (1)」).

### 3. 섹션마다 「제목 → 그 섹션만의 열들」 차례로 묶이기 때문이다

제목이 흐름을 끊으므로, 앞 섹션의 내용은 제목 위 열들에서 끝나고 다음 섹션은 제목 아래에서 새 열로 시작한다.
제목이 없거나 열 안에 갇혀 있으면 앞 섹션의 끝과 다음 섹션의 시작이 같은 열에 섞인다.
근거: 2-summary 「어디서 틀리나 5」 · 「동작 방식 (2)」 (원본 팁: 섹션 제목에 유용하다).

### 4. 열은 컨테이너가 만들고, 가로지를지는 각 요소가 정하기 때문이다

`column-count` 는 상자의 내용을 몇 열로 나눌지 정하는 컨테이너의 일이다.
`column-span` 은 그 열들 속의 한 요소가 「나는 열을 무시하고 폭 전체를 쓰겠다」고 선언하는 일이다.
그래서 컨테이너에 걸면 원하는 제목은 여전히 열 안에 갇힌다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 1」.

### 5. 선언이 무시되어 기본값 `none` 처럼 열 하나 안에 남는다

문법은 `none | all` 두 키워드뿐이라 숫자 값은 무효이고, 무효인 선언은 무시된다.
일부 열만 걸치는 배치는 이 속성으로 만들 수 없다.
근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 3」.

### 6. 볼 수 없다

`column-span` 은 애니메이션 가능하지 않은 속성이다.
`transition` 을 걸어도 중간 단계가 생기지 않는다 (원본에 근거 없음 — 추론: 값이 즉시 바뀐다).
근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 4」.

### 7. 자식의 계산값은 `none` 이지만, 이미 폭 전체를 쓰는 부모 안에 있어서 넓게 보인다

`column-span` 은 상속되지 않으므로 자식에게 `all` 이 이어지지 않는다.
하지만 자식은 모든 열을 가로지르는 부모 상자 안에 놓이므로, 부모의 넓은 폭 안에서 배치된다.
근거: 2-summary 「문법 — 형태와 규칙」의 상속 규칙 · 「용어 풀이」의 상속.

### 8. 보이는 변화가 없다

다단 컨테이너가 아니면 가로지를 열이 없다.
`column-span` 은 다단 컨테이너 안의 요소에서만 의미가 있다.
근거: 2-summary 「동작 방식 (3)」 · 「언제 쓰고 언제 안 쓰나」.

## 실습 정답

### 실습 1. 다단 글을 가로지르는 제목 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 내용이 세 열로 나뉜다 | `.multicol { column-count: 3; }` |
| 2. 열 사이 간격 | `.multicol { column-gap: 20px; }` |
| 3. 제목이 모든 열을 가로지른다 | `.spanning { column-span: all; }` |
| 4. 첫 문단은 위, 둘째 문단은 아래 열들 | HTML 차례 `<p>` → `<h3 class="spanning">` → `<p>` 와 `column-span: all` 의 흐름 끊기 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/layout/reference/column-span.html`

```html
<!DOCTYPE html>
<!-- HTML5 문서 선언 -->
<html lang="ko">
<head>
<meta charset="utf-8">
<title>column-span - 요소가 다단 레이아웃의 모든 열에 걸쳐 배치될지 설정합니다</title>
<!--
  [레이아웃] column-span
  설명: 요소가 다단 레이아웃의 모든 열에 걸쳐 배치될지 설정합니다
  구문: column-span: none | all
  팁: column-span: all인 요소는 다단 컨텐츠를 위아래로 분리합니다. 섹션 제목에 유용합니다.
-->
<style>
  /* .multicol: 3단 컨테이너 */
  .multicol {
    column-count: 3;             /* 3개 열 */
    column-gap: 20px;            /* 열 간격 */
    background: #f1f5f9;         /* 회색 배경 */
    padding: 16px;               /* 안쪽 여백 */
    border-radius: 4px;          /* 모서리 둥글게 */
  }
  /* .spanning: 모든 열을 가로지르는 요소 */
  .spanning {
    column-span: all;            /* 모든 열에 걸쳐 배치. 위아래 콘텐츠를 분리 */
    background: #3b82f6;         /* 파란 배경 */
    color: white;                /* 흰 글자 */
    padding: 8px 16px;           /* 안쪽 여백 */
    border-radius: 4px;          /* 모서리 둥글게 */
    margin: 8px 0;               /* 위아래 여백 */
  }
</style>
</head>
<body>
<!-- 가로지르는 제목이 다단 콘텐츠를 분할 -->
<div class="multicol">
  <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
  <h3 class="spanning">Spanning Heading</h3>     <!-- 모든 열을 가로지름 -->
  <p>Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
</div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.multicol {
  column-count: 3;
  column-gap: 20px;
  background: #f1f5f9;
  padding: 16px;
  border-radius: 4px;
}
.spanning {
  column-span: all;
  background: #3b82f6;
  color: white;
  padding: 8px 16px;
  border-radius: 4px;
  margin: 8px 0;
}
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 열을 만드는 `column-count` 는 컨테이너 `.multicol` 에, 가로지르기 `column-span: all` 은 안쪽 `h3.spanning` 에 건다.
- 스패너가 흐름을 끊어 첫 문단은 제목 위 열들에, 둘째 문단은 제목 아래 새 열들에 놓인다.
- `column-span` 줄을 지우면 제목은 기본값 `none` 이 되어 열 하나 폭 안에 갇힌다.
- 배경 · 글자색 · 안쪽 여백 · 둥근 모서리 · `margin` 은 꾸밈이고, 이 주제의 핵심은 두 줄(`column-count` · `column-span`)이다.
- 보이는 결과(파란 띠가 회색 상자 폭 전체를 채움)는 코드에서 읽은 것이다 (코드에서 읽은 것 — 렌더 실측 아님).

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

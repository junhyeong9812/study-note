# css/layout/40 — column-rule-color — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 파란색 — 기본값 `currentcolor` 가 글자색을 따른다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

구분선은 파란색(`blue`)으로 그려진다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**

`column-rule-color` 를 쓰지 않았으므로 기본값 `currentcolor` 가 들어간다.
`currentcolor` 는 이 요소의 `color` 값을 가리키고, 그 값이 `blue` 다.
근거: 2-summary 「동작 방식 (2)」.

### 2. 초록 — 구분선 색은 상속되지 않고 자기 `color` 를 따른다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`.inner` 의 구분선은 빨강이 아니라 초록(`green`)이다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**

`column-rule-color` 는 상속되지 않으므로 `.outer` 의 `red` 는 `.inner` 로 넘어가지 않는다.
그래서 `.inner` 의 값은 기본값 `currentcolor` 다.
`color` 는 상속되므로 `.inner` 의 `color` 는 `green` 이고, `currentcolor` 가 그 값을 가리킨다.
근거: 2-summary 「동작 방식 (3)」.

### 3. 0.3초 동안 중간 색을 거쳐 서서히 바뀐다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

마우스를 올리면 구분선 색이 회색에서 빨강으로 0.3초에 걸쳐 부드럽게 넘어간다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**

`column-rule-color` 는 애니메이션 가능한 속성이라 `transition` 이 두 색 사이를 중간값으로 이어 준다.
중간 색이 정확히 어떻게 섞이는지는 색 보간 규칙과 브라우저 구현에 달려 있다 (확인 필요).
근거: 2-summary 「동작 방식 (4)」, 「구현 세부사항 대 언어 보장」.

### 4. 실제로는 부모 값을 넘겨받는 것이 아니라 자기 `color` 를 참조하기 때문이다

「상속받는다」는 말은 부모의 `column-rule-color` 값이 자식에게 넘어간다는 뜻으로 읽히기 쉽다.
실제로는 기본값 `currentcolor` 가 **그 요소 자신의** `color` 값을 가리킬 뿐이다.
그 `color` 가 부모에게서 상속된 값일 수는 있지만, 상속된 것은 `color` 이지 `column-rule-color` 가 아니다.
그래서 부모에 `column-rule-color` 를 줘도 자식 구분선 색은 바뀌지 않는다.
근거: 2-summary 「어디서 틀리나 2」.

### 5. 글자색만 바꾸면 구분선 색이 따라 바뀐다

기본값 `currentcolor` 는 그 요소의 `color` 를 따라간다.
그래서 `color` 하나만 바꿔도 글자와 구분선이 함께 바뀐다.
같은 색 값을 두 군데 하드코딩해 따로 맞출 필요가 없다.
근거: 2-summary 「동작 방식 (2)」, 「어디서 틀리나 3」, 「언제 쓰고 언제 안 쓰나」.

### 6. 정할 수 없다 — 색만 맡는다

`column-rule-color` 는 구분선의 색만 정한다.
모양은 `column-rule-style`, 두께는 `column-rule-width` 가 맡는다.
원본 예제가 세 속성을 함께 쓰는 것도 그래서다.
근거: 2-summary 「동작 방식 (1)」, 「문법 — 형태와 규칙」, 「어디서 틀리나 1」.

### 7. 구분선은 이웃한 두 열 「사이」에 생기는 선이기 때문이다

열 구분선은 이웃한 두 열 사이에 그어진다.
`column-count` 같은 다단 설정이 없으면 열이 하나뿐이라 「사이」가 없다.
그러니 색을 정해도 칠할 선이 없다.
열이 3개면 사이는 2곳이라 구분선도 2줄이다.
근거: 2-summary 「동작 방식 (1)」, 「어디서 틀리나 4」.

## 실습 정답

### 실습 1. 빨간 구분선으로 나뉜 3단 글 상자 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 내용이 세 열로 나뉜다 | `.multicol { column-count: 3; }` |
| 2. 구분선 색을 빨강으로 | `.multicol { column-rule-color: #ef4444; }` |
| 3. 구분선 모양은 실선 | `.multicol { column-rule-style: solid; }` |
| 4. 구분선 두께 | `.multicol { column-rule-width: 2px; }` |
| 5. 열 사이 간격 | `.multicol { column-gap: 20px; }` |
| 6. 단락 기본 여백 제거 | `p { margin: 0; }` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/layout/reference/column-rule-color.html`

```html
<!DOCTYPE html>
<!-- HTML5 문서 선언 -->
<html lang="ko">
<head>
<meta charset="utf-8">
<title>column-rule-color - 다단 레이아웃에서 열 구분선의 색상을 설정합니다</title>
<!--
  [레이아웃] column-rule-color
  설명: 다단 레이아웃에서 열 구분선의 색상을 설정합니다
  구문: column-rule-color: <color>
  팁: 기본값은 currentcolor로, 요소의 color 속성값을 상속받습니다.
-->
<style>
  /* .multicol: 빨간 구분선이 있는 3단 컨테이너 */
  .multicol {
    column-count: 3;             /* 3개 열 */
    column-rule-color: #ef4444;  /* 빨간 구분선 색 */
    column-rule-style: solid;    /* 실선 */
    column-rule-width: 2px;      /* 두께 2px */
    column-gap: 20px;            /* 열 간격 */
    background: #f1f5f9;         /* 회색 배경 */
    padding: 16px;               /* 안쪽 여백 */
    border-radius: 4px;          /* 모서리 둥글게 */
  }
  /* p: 단락 기본 마진 제거 */
  p {
    margin: 0;                   /* 기본 마진 제거 */
  }
</style>
</head>
<body>
<!-- 빨간 구분선으로 분리된 3단 -->
<div class="multicol">
  <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt.</p>
</div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.multicol {
  column-count: 3;
  column-rule-color: #ef4444;
  column-rule-style: solid;
  column-rule-width: 2px;
  column-gap: 20px;
  background: #f1f5f9;
  padding: 16px;
  border-radius: 4px;
}
p {
  margin: 0;
}
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 이 항목의 핵심 줄은 `column-rule-color: #ef4444;` 하나다 — 구분선의 색만 정한다.
- 색 하나로는 구분선이 완성되지 않으므로 `column-rule-style` 과 `column-rule-width` 를 함께 준다.
- `column-count: 3` 이 열을 나눠야 구분선이 들어갈 「열 사이」가 생긴다 — 열 셋이면 선은 두 줄이다.
- `column-rule-color` 를 지우면 기본값 `currentcolor` 가 되어 상자의 글자색과 같은 색 선이 된다.
- 배경 · 안쪽 여백 · 둥근 모서리는 꾸밈일 뿐 구분선 색과는 관계가 없다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

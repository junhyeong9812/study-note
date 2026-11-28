# css/layout/37 — column-rule — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 선은 2개, 각 간격의 한가운데

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

세로선은 2개다.
각 선은 20px 간격의 한가운데에 놓인다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**

열이 셋이면 열 사이 간격은 둘이고, 구분선은 간격마다 하나씩 그려진다.
원본 팁대로 선은 `column-gap` 의 중앙에 그려진다.
첫 열과 마지막 열의 바깥쪽에는 간격이 없으므로 선도 없다.
근거: 2-summary 「동작 방식 (1)」.

### 2. 보이지 않는다 — 스타일이 기본값 `none`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

빨간 선은 보이지 않는다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**

스타일 자리를 비웠으므로 기본값 `medium none currentcolor` 의 `none` 이 쓰인다.
`none` 은 선을 그리지 않으므로 두께와 색을 줘도 나타나지 않는다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 1」.

### 3. 글자색 `#334155` 를 따른다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

선 색은 `#334155` 다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**

색을 빼면 기본값 `currentcolor` 가 쓰이고, `currentcolor` 는 그 요소의 `color` 값이다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 5」.

### 4. 구분선은 공간을 차지하지 않는다

구분선은 레이아웃 계산에 끼어들지 않고, 이미 정해진 열 간격 위에 덧그려질 뿐이다.
열 너비와 간격은 `column-count` · `column-gap` · 컨테이너 너비로 정해지므로 선을 넣어도 바뀌지 않는다.
근거: 2-summary 「동작 방식 (2)」 (원본 팁 「구분선은 공간을 차지하지 않습니다」).

### 5. 된다 — `||` 는 순서를 묻지 않는다

문법의 `||` 는 세 값 중 하나 이상을 순서 상관없이 각각 한 번까지 쓴다는 뜻이다.
그래서 `solid #3b82f6 2px` 도 2px 파란 실선이다.
근거: 2-summary 「동작 방식 (3)」 · 「문법 — 형태와 규칙」.

### 6. 생기지 않는다 — 상속되지 않고, 선은 열을 만든 요소가 그린다

`column-rule` 은 상속되지 않는다.
열 사이 선은 열을 만든 다단 컨테이너의 열 간격에 그려지므로, 안쪽 `p` 에 걸어서는 바깥 열 사이에 선이 생기지 않는다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 4」.

### 7. `border` 는 공간을 차지하고, `column-rule` 은 차지하지 않는다

두 속성 모두 두께 · 스타일 · 색을 한 줄에 쓰는 꼴이다.
그러나 `column-rule` 은 열 간격 가운데에 덧그려질 뿐 공간을 차지하지 않는다.
`border` 는 요소의 테두리로서 박스 크기 계산에 들어가 자리를 차지한다 (원본에 근거 없음 — 추론).
근거: 2-summary 「동작 방식 (2)」 · 「언제 쓰고 언제 안 쓰나」.

### 8. `column-gap` 을 넓힌다

구분선은 공간을 차지하지 않으므로 두께를 키워도 글과 선 사이가 벌어지지 않는다.
선은 간격 한가운데에 있으니, 간격(`column-gap`)을 넓히면 선 양옆의 여백이 함께 넓어진다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 2」.

## 실습 정답

### 실습 1. 세 열로 나눈 문단에 파란 구분선 긋기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 문단이 세 열로 흐른다 | `.multicol { column-count: 3; }` |
| 열 사이에 간격을 둔다 | `.multicol { column-gap: 20px; }` |
| 단축 속성 하나로 두께 · 스타일 · 색 | `.multicol { column-rule: 2px solid #3b82f6; }` |
| 구분선은 `.multicol` 에 건다 | `column-rule` 이 `.multicol` 규칙 안에 있다 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/layout/reference/column-rule.html`

```html
<!DOCTYPE html>
<!-- HTML5 문서 선언 -->
<html lang="ko">
<head>
<meta charset="utf-8">
<title>column-rule - 다단 레이아웃에서 열 사이의 구분선을 설정하는 단축 속성입니다</title>
<!--
  [레이아웃] column-rule
  설명: 다단 레이아웃에서 열 사이의 구분선을 설정하는 단축 속성입니다
  구문: column-rule: <column-rule-width> || <column-rule-style> || <column-rule-color>
  팁: column-rule은 열 사이의 간격(column-gap) 중앙에 그려집니다. 구분선은 공간을 차지하지 않습니다.
-->
<style>
  /* .multicol: 단축 속성으로 구분선을 설정한 3단 */
  .multicol {
    column-count: 3;             /* 3개 열 */
    column-gap: 20px;            /* 열 간격 */
    column-rule: 2px solid #3b82f6;  /* 두께/스타일/색 단축 지정 */
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
<!-- 단축 속성으로 그린 구분선 -->
<div class="multicol">
  <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam.</p>
</div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.multicol {
  column-count: 3;
  column-gap: 20px;
  column-rule: 2px solid #3b82f6;
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
- 열을 만드는 `column-count` 가 있어야 `column-rule` 이 그릴 열 사이가 생긴다.
- `column-rule: 2px solid #3b82f6;` 한 줄이 두께 · 스타일 · 색 셋을 모두 정한다.
- 스타일 `solid` 를 빼면 기본값 `none` 이 되어 선이 사라진다.
- 선은 20px 간격의 한가운데에 그려지고, 공간을 차지하지 않아 열 너비를 바꾸지 않는다.
- 상속되지 않으므로 `p` 가 아니라 열을 만든 `.multicol` 에 건다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

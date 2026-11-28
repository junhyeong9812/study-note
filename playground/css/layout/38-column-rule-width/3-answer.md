# css/layout/38 — column-rule-width — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 보이지 않는다 — 스타일이 없으면 두께는 소용없다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
세 열로는 나뉘지만 열 사이에 선은 보이지 않는다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`column-rule-style` 을 쓰지 않아 선을 그리지 않는 상태(`none`)로 남는다.
원본 팁대로 스타일이 `none` 이면 두께 값이 있어도 구분선은 표시되지 않는다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 1」.

### 2. 세 개 — 열 사이에만 그어진다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
두꺼운 검은 세로선이 세 개 보인다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
구분선은 이웃한 두 열 「사이」에만 그어지고 바깥 가장자리에는 없다.
열이 네 개면 사이는 세 곳이므로 선도 세 개다.
`column-rule` 단축 속성에 스타일 `solid` 가 들어 있으므로 선이 보인다.
근거: 2-summary 「동작 방식 (1)」 · 「핵심 문장 5」.

### 3. 선을 그릴지는 스타일이 정하고, 두께는 굵기만 정하기 때문이다

두께는 「이미 그리기로 한 선」의 굵기를 바꾸는 손잡이다.
선을 그릴지 말지는 `column-rule-style` 이 정하므로, 그것이 `none` 이면 굵기를 정할 선 자체가 없다.
근거: 2-summary 「동작 방식 (1) · (2)」 · 「핵심 문장 1 · 2」.

### 4. 선언이 무시되고 기본값 `medium` (또는 이전 값)이 남는다

`<length>` 는 음수를 받지 않으므로 `-2px` 는 잘못된 값이다.
CSS 는 잘못된 값의 선언을 무시하므로 그 줄이 없는 것처럼 되고, 앞서 준 값이 없으면 기본값 `medium` 이 남는다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 3」.

### 5. 기본값 `medium` — 기본 두께의 선

두께를 쓰지 않으면 기본값 `medium` 이 쓰인다.
스타일이 `solid` 이므로 선은 보이고, 굵기는 기본 두께다.
근거: 2-summary 「문법 — 형태와 규칙」 의 값 표.

### 6. 8px 가 아니라 기본값 `medium` 이다

`column-rule-width` 는 상속되지 않는다.
부모의 8px 는 자식에게 내려가지 않으므로 자식은 자기 기본값 `medium` 을 쓴다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 4」.

### 7. 같은 키워드 셋을 쓰고, 둘 다 스타일이 있어야 보인다

둘 다 `thin` · `medium` · `thick` 키워드와 길이 값을 받는다.
둘 다 두께만으로는 선이 보이지 않고 스타일(`column-rule-style` / 테두리 스타일)이 `none` 이 아니어야 그려진다.
차이는 그려지는 자리다 — 테두리는 요소 가장자리, 구분선은 열 사이다.
근거: 2-summary 「문법 — 형태와 규칙」 · 「언제 쓰고 언제 안 쓰나」.

### 8. 0.3초에 걸쳐 3px 에서 10px 로 점점 굵어진다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
마우스를 올리면 선이 한 번에 바뀌지 않고 0.3초 동안 3px → 10px 로 부드럽게 굵어지며, 내리면 다시 3px 로 돌아간다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`column-rule-width` 는 애니메이션 가능한 속성이라 두 길이 사이를 `transition` 이 보간한다.
근거: 2-summary 「동작 방식 (4)」.

## 실습 정답

### 실습 1. 굵은 구분선이 있는 3단 글 상자

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 세 열로 나뉜다 | `.multicol { column-count: 3; }` |
| 2. 열 사이 간격 | `column-gap: 20px;` |
| 3. 선 모양을 실선으로 | `column-rule-style: solid;` |
| 4. 두께를 고정 길이로 | `column-rule-width: 3px;` |
| 5. 선 색을 파랑으로 | `column-rule-color: #3b82f6;` |
| 6. 배경 · 여백 · 모서리 · 마진 | `background` · `padding` · `border-radius` · `p { margin: 0; }` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/layout/reference/column-rule-width.html`

```html
<!DOCTYPE html>
<!-- HTML5 문서 선언 -->
<html lang="ko">
<head>
<meta charset="utf-8">
<title>column-rule-width - 다단 레이아웃에서 열 구분선의 두께를 설정합니다</title>
<!--
  [레이아웃] column-rule-width
  설명: 다단 레이아웃에서 열 구분선의 두께를 설정합니다
  구문: column-rule-width: thin | medium | thick | <length>
  팁: column-rule-style이 none이면 두께 값이 있어도 구분선이 표시되지 않습니다.
-->
<style>
  /* .multicol: 굵은 구분선이 있는 3단 */
  .multicol {
    column-count: 3;             /* 3개 열 */
    column-rule-width: 3px;      /* 구분선 두께 3px */
    column-rule-style: solid;    /* 실선 */
    column-rule-color: #3b82f6;  /* 파란 색 */
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
<!-- 두꺼운 파란 구분선으로 나뉜 3단 -->
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
  column-rule-width: 3px;
  column-rule-style: solid;
  column-rule-color: #3b82f6;
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
- 이 주제의 핵심 줄은 `column-rule-width: 3px` 이지만, 혼자서는 선이 보이지 않는다.
- `column-rule-style: solid` 가 선을 그리게 만들고, 이 줄을 지우면 두께가 있어도 선이 사라진다.
- 열이 셋이므로 구분선은 열 사이 두 곳에만 그어진다.
- `thick` 대신 `3px` 를 쓴 것은 정확한 굵기를 고정하려는 선택이다.
- 세 줄(`width` · `style` · `color`)은 `column-rule: 3px solid #3b82f6` 한 줄로 줄일 수 있다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

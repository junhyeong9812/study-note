# css/layout/39 — column-rule-style — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 구분선은 두 개, 모양은 대시선

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
열 1·2 사이와 열 2·3 사이에 하나씩, 모두 두 개의 파란 대시선이 그어진다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
구분선은 이웃한 열 사이에만 생기므로 열이 3개면 사이는 2개다.
`dashed` 는 값 표에서 「대시선」이다.
근거: 2-summary 「동작 방식 (1)」 · 「문법 — 형태와 규칙」의 값 표.

### 2. 선이 보이지 않는다 — 모양이 기본값 `none` 이다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
열은 세 개로 나뉘지만 열 사이에 빨간 선은 보이지 않는다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`column-rule-style` 을 적지 않아 기본값 `none` 이 쓰이고, `none` 은 「구분선 없음」이다.
그릴 선이 없으니 굵기와 색은 효과가 없다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 1」.

### 3. 같은 원본의 값 목록이 `dashed` 를 「대시선」으로 적었기 때문이다

원본 값 목록은 `dotted` = 점선, `dashed` = 대시선으로 나눠 적었다.
그 기준이면 주석의 「점선」은 `dotted` 와 헷갈린 표현이고, 실제로 그려지는 것은 대시선이다.
근거: 2-summary 「어디서 틀리나 2」.

### 4. 다르지 않다 — 둘 다 선이 없다

원본은 `hidden` 을 「구분선 숨김 (`none` 과 동일)」로 적었다.
열 구분선에서는 둘 다 선이 그려지지 않는다고 보면 된다.
근거: 2-summary 「문법 — 형태와 규칙」의 값 표 · 「어디서 틀리나 3」.

### 5. 생기지 않는다 — 상속되지 않는 속성이다

`column-rule-style` 은 상속이 `False` 다.
안쪽 다단 상자는 기본값 `none` 을 쓰므로 그 열 사이에는 선이 없다.
안쪽에도 선이 필요하면 안쪽 상자에 따로 적어야 한다.
근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 4」.

### 6. 서서히 변하지 않는다 — 중간 모양 없이 바뀐다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
실선이 반쯤 끊기는 등의 중간 단계 없이, 모양이 단번에 점선으로 바뀐다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`column-rule-style` 은 애니메이션 가능이 `False` 인 속성이라 두 값 사이를 이어 줄 중간 값이 없다.
근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 5」.
바뀌는 정확한 시점은 원본에 없다 (원본에 근거 없음 — 추론).

### 7. `border-style` 의 값과 같다

팁대로 `border-style` 과 동일한 값들을 쓴다.
`dotted` · `dashed` · `solid` · `double` · `groove` · `ridge` · `inset` · `outset` · `none` · `hidden` 을 테두리 대신 열 사이 선에 쓴다고 설명하면 된다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 6」.

### 8. 모양 · 굵기 · 색을 나눠 맡는다

`column-rule-style` 은 모양(펜의 종류), `column-rule-width` 는 굵기, `column-rule-color` 는 색을 맡는다.
셋이 합쳐 선 하나가 되는데, 모양이 `none` 이면 나머지 둘이 있어도 선이 없다.
근거: 2-summary 「한눈에」 비유 대응표 · 「동작 방식 (1)」·「(2)」.

## 실습 정답

### 실습 1. 대시선으로 나뉜 3단 글 상자 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| `.multicol` 상자 안에 단락 하나 | `<div class="multicol"><p>…</p></div>` |
| 내용이 세 열로 흐름 | `.multicol { column-count: 3; }` |
| 열 사이 대시선 | `.multicol { column-rule-style: dashed; }` |
| 굵기 · 색 · 간격 · 배경 · 여백 · 모서리 | `column-rule-width` · `column-rule-color` · `column-gap` · `background` · `padding` · `border-radius` |
| 단락 기본 바깥 여백 제거 | `p { margin: 0; }` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/layout/reference/column-rule-style.html`

```html
<!DOCTYPE html>
<!-- HTML5 문서 선언 -->
<html lang="ko">
<head>
<meta charset="utf-8">
<title>column-rule-style - 다단 레이아웃에서 열 구분선의 스타일을 설정합니다</title>
<!--
  [레이아웃] column-rule-style
  설명: 다단 레이아웃에서 열 구분선의 스타일을 설정합니다
  구문: column-rule-style: none | hidden | dotted | dashed | solid | double | groove | ridge | inset | outset
  팁: border-style과 동일한 값들을 사용합니다.
-->
<style>
  /* .multicol: 점선 구분선이 있는 3단 */
  .multicol {
    column-count: 3;             /* 3개 열 */
    column-rule-style: dashed;   /* 점선 스타일 */
    column-rule-width: 2px;      /* 두께 2px */
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
<!-- 파란 점선 구분선으로 나뉜 3단 -->
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
  column-rule-style: dashed;
  column-rule-width: 2px;
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
- 핵심 두 줄은 `column-count: 3;` 과 `column-rule-style: dashed;` 다.
- 시작 코드에 굵기와 색이 이미 있어도 모양 줄이 없으면 선이 보이지 않는다 — 기본값이 `none` 이기 때문이다.
- 열이 셋이므로 구분선은 열 사이 두 곳에만 생긴다.
- 정답 코드 주석의 「점선 스타일」은 값 표 기준으로 「대시선」이 맞다.
- `p { margin: 0; }` 은 단락의 기본 바깥 여백 때문에 첫 열 위쪽이 벌어지지 않게 한다 (원본에 근거 없음 — 추론).

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

# css/color-background/23 — print-color-adjust — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 화면에서는 차이가 없다 — 둘 다 배경이 보인다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
파란 상자와 분홍→보라 그라디언트 상자가 둘 다 배경색을 띤 채 보인다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`print-color-adjust` 는 인쇄 때 브라우저의 배경 최적화 여부를 정하는 속성이다.
화면 표시는 바꾸지 않으므로 두 값의 차이는 인쇄에서만 드러난다.
근거: 2-summary 「어디서 틀리나 1」 · 「문법 — 형태와 규칙」의 데모.

### 2. 브라우저 판단에 달렸다 — 조정되거나 제거될 수 있다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
파란 배경은 그대로 남을 수도, 조정되거나 빠질 수도 있다.
어느 쪽인지는 브라우저가 정한다.

**왜 그런가**
`economy` 는 「인쇄 최적화를 위해 배경 등을 조정/제거해도 된다」는 허락이다.
결과를 하나로 못 박지 않으므로 코드만 읽어서는 「반드시 사라진다」고 말할 수 없다.
근거: 2-summary 「동작 방식 (1)」.

### 3. `exact` — 부모에게서 물려받는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`<td>` 에 적용되는 값은 `exact` 다.
따라서 빨간 배경은 작성한 대로 인쇄된다.

**왜 그런가**
`print-color-adjust` 는 상속된다.
`<td>` 에 값이 없으므로 `<tr>` 을 거쳐 `<table>` 의 `exact` 를 받는다.
근거: 2-summary 「동작 방식 (3)」.

### 4. 인쇄 최적화(잉크 절약 등)를 기본으로 허용하려고

배경 대부분은 꾸밈이라 인쇄에서 빠져도 내용 전달에 문제가 없다.
그래서 기본은 브라우저가 배경을 조정 · 제거해 인쇄를 최적화할 수 있게 둔다.
색이 정보인 경우에만 작성자가 `exact` 로 막으면 된다.
근거: 2-summary 「동작 방식 (1)」 · 「언제 쓰고 언제 안 쓰나」.

### 5. 옛 이름만 아는 브라우저와의 호환을 위해

원본 팁이 말하듯 구형 `-webkit-print-color-adjust` 도 함께 지정해야 호환성이 확보된다.
표준 이름을 모르는 브라우저는 접두사 판을 읽고, 둘 다 아는 브라우저는 뒤에 적은 표준 값을 쓴다.
근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 5」.

### 6. 말할 수 없다 — `economy` 는 허용일 뿐이다

`economy` 는 브라우저가 배경을 조정하거나 제거하는 것을 허용한다.
실제로 지우는지, 어떻게 바꾸는지는 브라우저 구현이 정한다.
근거: 2-summary 「어디서 틀리나 3」 · 「구현 세부사항 대 언어 보장」.

### 7. 만들 수 없다 — 애니메이션 가능하지 않은 속성이다

원본 데이터에 애니메이션 가능이 `False` 로 적혀 있다.
`transition` 이나 `@keyframes` 로 두 값 사이를 옮겨 가는 효과는 이 속성으로 만들 수 없다.
게다가 값이 바꾸는 것은 인쇄 동작이라 화면에서 「서서히 바뀌는」 모습도 없다.
근거: 2-summary 「문법 — 형태와 규칙」.

### 8. 배경 이미지 쪽이다

`linear-gradient()` 는 CSS 에서 배경 이미지로 취급된다.
`exact` 는 배경색과 배경 이미지를 모두 유지하므로, 원본 예제의 `.exact` 그라디언트도 작성한 대로 인쇄된다.
근거: 2-summary 「동작 방식 (2)」.

## 실습 정답

### 실습 1. 인쇄 때 다르게 다뤄지는 두 상자 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 상자 두 개를 위아래로 둔다 | `<body>` 안의 `<div>` 두 개 |
| 첫 상자 클래스 `economy` · 글 | `<div class="economy">economy: 인쇄 시 브라우저가 최적화</div>` |
| 둘째 상자 클래스 `exact` · 글 | `<div class="exact">exact: 화면 그대로 인쇄</div>` |
| 인쇄 최적화 허용을 명시 | `.economy { print-color-adjust: economy; }` |
| 작성한 색 그대로 인쇄 | `.exact { print-color-adjust: exact; }` |
| 꾸밈은 그대로 | 두 규칙의 `background` · `color` · `padding` · `margin-bottom` · `border-radius` · `font-weight` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/color-background/reference/print-color-adjust.html`

```html
<!DOCTYPE html>
<!-- 문서 타입 선언: HTML5 -->
<html lang="ko">
<!-- 문서 루트: 한국어 페이지 -->
<head>
<!-- 메타 영역 시작 -->
<meta charset="utf-8">
<!-- 문자 인코딩: UTF-8 -->
<title>print-color-adjust - 인쇄 시 브라우저의 배경색/이미지 최적화(제거) 여부를 제어</title>
<!-- 브라우저 탭 제목 -->
<!--
  [색상 & 배경] print-color-adjust
  설명: 인쇄 시 브라우저의 배경색/이미지 최적화(제거) 여부를 제어
  구문: print-color-adjust: economy | exact
  팁: 배경색이 정보 전달에 필수적인 표/차트에 exact를 사용. 구형 -webkit-print-color-adjust도 함께 지정하면 호환성 확보.
-->
<style>
  /* .economy: 인쇄 시 잉크 절약을 허용 */
  .economy {
    print-color-adjust: economy;   /* economy: 브라우저가 배경 등을 잉크 절약을 위해 제거 가능 (기본) */
    background: #3b82f6;           /* 파란 배경 */
    color: white;                  /* 흰 글씨 */
    padding: 16px;                 /* 내부 여백 16px */
    margin-bottom: 8px;            /* 아래 여백 8px */
    border-radius: 8px;            /* 모서리 둥글기 8px */
    font-weight: bold;             /* 굵은 글씨 */
  }
  /* .exact: 인쇄 시 화면 그대로 출력 강제 */
  .exact {
    print-color-adjust: exact;     /* exact: 화면 색상을 그대로 인쇄 (배경 유지) */
    background: linear-gradient(135deg, #f43f5e, #8b5cf6);  /* 135도 그라디언트(분홍→보라) */
    color: white;                  /* 흰 글씨 */
    padding: 16px;                 /* 내부 여백 16px */
    border-radius: 8px;            /* 모서리 둥글기 8px */
    font-weight: bold;             /* 굵은 글씨 */
  }
</style>
</head>
<body>
  <!-- economy 모드 -->
  <div class="economy">economy: 인쇄 시 브라우저가 최적화</div>
  <!-- exact 모드 -->
  <div class="exact">exact: 화면 그대로 인쇄</div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.economy { print-color-adjust: economy; background: #3b82f6; color: white; padding: 16px; margin-bottom: 8px; border-radius: 8px; font-weight: bold; }
.exact { print-color-adjust: exact; background: linear-gradient(135deg, #f43f5e, #8b5cf6); color: white; padding: 16px; border-radius: 8px; font-weight: bold; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 이 실습에서 채울 핵심 줄은 `print-color-adjust` 두 줄뿐이다.
- `economy` 는 기본값이라 생략해도 같지만, 비교를 위해 명시했다.
- 그라디언트는 배경 이미지라 `exact` 가 함께 지킨다.
- 화면에서는 두 상자가 똑같이 색을 띠므로, 차이는 인쇄 미리보기에서 확인한다.
- 실제로 쓸 때는 `.exact` 에 `-webkit-print-color-adjust: exact;` 를 함께 적으면 호환성이 넓어진다 (정답 코드에는 없다).

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

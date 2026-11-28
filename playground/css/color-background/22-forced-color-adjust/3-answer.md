# css/color-background/22 — forced-color-adjust — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 지정한 색이 남는다 — 부모의 `none` 을 상속한다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`.bar` 의 배경은 자동 조정되지 않고 지정한 색이 남는다. (코드에서 읽은 것 — 렌더 실측 아님)

**왜 그런가**
`forced-color-adjust` 는 상속되는 속성이다.
`.bar` 는 값을 적지 않았으므로 부모 `.chart` 의 `none` 을 물려받는다.
근거: 2-summary 「동작 방식 (4)」.

### 2. 자동 조정되어 시스템 색으로 바뀐다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
작성자가 지정한 파란 배경 · 흰 글씨 대신 강제 색상 모드의 색으로 보인다. (코드에서 읽은 것 — 렌더 실측 아님)

**왜 그런가**
값을 적지 않으면 기본값 `auto` 가 적용되고, `auto` 는 강제 색상 모드에서 색을 자동 조정한다.
근거: 2-summary 「동작 방식 (1)」 · 「문법 — 형태와 규칙」의 기본값.

### 3. 평소 화면에서는 차이가 없다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
두 상자 모두 같은 파란 배경으로 보인다. (코드에서 읽은 것 — 렌더 실측 아님)

**왜 그런가**
이 속성은 강제 색상 모드가 켜져 있을 때만 효과가 난다.
모드가 꺼져 있으면 `auto` 도 아무것도 조정하지 않는다.
근거: 2-summary 「어디서 틀리나 3」.

### 4. 사용자가 필요해서 고른 색을 빼앗기 때문이다

강제 색상 모드는 대개 구분하기 쉬운 색이 필요한 사람이 켠다.
`none` 을 붙인 요소는 그 색 묶음의 도움을 받지 못하므로, 넓게 쓸수록 읽기 어려운 영역이 늘어난다.
그래서 원본의 팁은 그라디언트 · 데이터 시각화처럼 색이 의미를 담아 바뀌면 안 될 때만 쓰라고 한다.
근거: 2-summary 「어디서 틀리나 1」.

### 5. 상속되어 모든 자손에게 퍼지기 때문이다

`body` 의 `none` 은 값을 적지 않은 모든 자손이 이어받는다.
결국 글자 · 버튼까지 자동 조정에서 빠진다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 2」.

### 6. 만들 수 없다

`forced-color-adjust` 는 애니메이션 가능하지 않은 속성이다.
`auto` 와 `none` 사이에 중간 단계가 없으므로 `transition` 을 걸어도 서서히 바뀌지 않는다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 4」.

### 7. `color` 하나뿐이다

`preserve-parent-color` 는 `color` 만 부모의 값을 이어받게 하고, 배경 등 나머지 색은 `auto` 처럼 자동 조정한다.
모든 색을 지키려면 `none` 이 필요하다.
근거: 2-summary 「동작 방식 (3)」 · 「문법 — 형태와 규칙」의 값 표.

### 8. 둘 다 상속되는 속성이라 같은 규칙으로 퍼진다

`color` 를 부모에 적으면 값을 적지 않은 자식이 그 색을 이어받듯, `forced-color-adjust` 도 부모의 값을 자식이 이어받는다.
자식에 값을 다시 적으면 그 자식부터 달라지는 것도 같다.
근거: 2-summary 「동작 방식 (4)」의 용어 풀이.

## 실습 정답

### 실습 1. 강제 색상 모드에서 다르게 반응하는 두 상자

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 두 상자를 위아래로 두고 글자로 값 설명 | `<div class="auto-box">` · `<div class="none-box">` |
| `.auto-box` 에 자동 조정 값을 명시 | `.auto-box { forced-color-adjust: auto; }` |
| `.none-box` 는 지정한 색 유지 | `.none-box { forced-color-adjust: none; }` |
| 꾸밈 값은 그대로 | `.auto-box` · `.none-box` 의 `background` · `color` · `padding` · `margin-bottom` · `border-radius` · `font-weight` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/color-background/reference/forced-color-adjust.html`

```html
<!DOCTYPE html>
<!-- 문서 타입 선언: HTML5 -->
<html lang="ko">
<!-- 문서 루트: 한국어 페이지 -->
<head>
<!-- 메타 영역 시작 -->
<meta charset="utf-8">
<!-- 문자 인코딩: UTF-8 -->
<title>forced-color-adjust - 강제 색상 모드(고대비 모드 등)에서 요소의 색상 조정 방식을 설정</title>
<!-- 브라우저 탭 제목 -->
<!--
  [색상 & 배경] forced-color-adjust
  설명: 강제 색상 모드(고대비 모드 등)에서 요소의 색상 조정 방식을 설정
  구문: forced-color-adjust: auto | none | preserve-parent-color
  팁: none은 그라디언트/데이터 시각화 등 색상이 의미를 담고 있어 변경되면 안 되는 경우에만 사용. 남용 시 접근성 저해.
-->
<style>
  /* .auto-box: 강제 색상 모드에서 자동 조정 허용 */
  .auto-box {
    forced-color-adjust: auto;     /* auto: 강제 색상 모드 시 시스템 색상으로 변경 (기본) */
    background: #3b82f6;           /* 파란 배경 */
    color: white;                  /* 흰 글씨 */
    padding: 16px;                 /* 내부 여백 16px */
    margin-bottom: 8px;            /* 아래 여백 8px */
    border-radius: 8px;            /* 모서리 둥글기 8px */
    font-weight: bold;             /* 굵은 글씨 */
  }
  /* .none-box: 강제 색상 모드에서도 원래 색상 유지 */
  .none-box {
    forced-color-adjust: none;     /* none: 강제 색상 모드 무시, 지정한 색을 유지 */
    background: linear-gradient(135deg, #f43f5e, #8b5cf6);  /* 135도 그라디언트(분홍→보라) */
    color: white;                  /* 흰 글씨 */
    padding: 16px;                 /* 내부 여백 16px */
    border-radius: 8px;            /* 모서리 둥글기 8px */
    font-weight: bold;             /* 굵은 글씨 */
  }
</style>
</head>
<body>
  <!-- auto: 시스템 색상에 맞춰 조정 -->
  <div class="auto-box">auto: 강제 색상 모드에서 조정됨</div>
  <!-- none: 원본 색상 유지 -->
  <div class="none-box">none: 원래 색상 유지</div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.auto-box { forced-color-adjust: auto; background: #3b82f6; color: white; padding: 16px; margin-bottom: 8px; border-radius: 8px; font-weight: bold; }
.none-box { forced-color-adjust: none; background: linear-gradient(135deg, #f43f5e, #8b5cf6); color: white; padding: 16px; border-radius: 8px; font-weight: bold; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- `auto` 는 기본값이라 생략해도 같지만, 비교를 위해 명시했다.
- `none` 은 색이 의미를 담는 그라디언트 상자 하나에만 좁게 적었다.
- 평소 화면에서는 두 상자의 차이가 `forced-color-adjust` 때문에 생기지 않는다 — 차이는 강제 색상 모드에서만 드러난다.
- 상속되는 속성이므로, 상자 안에 자식을 넣으면 그 자식도 상자의 값을 따른다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

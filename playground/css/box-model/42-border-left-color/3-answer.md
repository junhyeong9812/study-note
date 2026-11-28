# css/box-model/42 — border-left-color — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 파랑 — 기본값 `currentcolor` 가 글자색을 따른다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
왼쪽 테두리는 파란색 4px 실선으로 그려진다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`border-left` 에 색을 적지 않았으므로 `border-left-color` 는 기본값 `currentcolor` 가 된다.
`currentcolor` 는 이 요소의 `color` 인 `blue` 다.
근거: 2-summary 「동작 방식 (2)」.

### 2. 검정 — 뒤의 단축 속성이 색을 되돌린다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
왼쪽 테두리는 빨강이 아니라 글자색인 검정으로 그려진다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`border-left: 4px solid;` 는 적지 않은 색을 기본값 `currentcolor` 로 되돌린다.
같은 규칙에서 뒤에 쓴 선언이 이기므로 앞의 `red` 는 지워진다.
근거: 2-summary 「동작 방식 (3)」.

### 3. 아무 테두리도 없다 — 선 모양이 `none` 이다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
왼쪽에 빨간 줄은 보이지 않고 여백만 있다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`border-left-color` 는 색만 정하고 선을 만들지 않는다.
`border-left-style` 이 기본값 `none` 이라 칠할 선이 없다.
근거: 2-summary 「동작 방식 (4)」.

### 4. 테두리 색이 `currentcolor` 였기 때문이다

색을 정하지 않은 테두리는 기본값 `currentcolor`, 곧 「요소의 현재 텍스트 색상」을 쓴다.
그래서 `color` 가 바뀌면 테두리 색도 같이 바뀐다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 1」.

### 5. 단축 속성을 뒤에 쓰면 색이 지워지기 때문이다

`border-left` 는 두께 · 선 모양을 정하면서 적지 않은 색을 `currentcolor` 로 되돌린다.
개별 속성 `border-left-color` 를 그 뒤에 써야 색이 살아남는다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 3」.

### 6. 자식 자신의 글자색(`currentcolor`)을 따라간다

`border-left-color` 는 상속되지 않으므로 부모의 `red` 는 자식에게 가지 않는다.
자식의 테두리 색은 기본값 `currentcolor` 이고, 이는 자식의 `color` 다.
`color` 는 상속되므로 부모의 글자색이 자식 테두리에 비칠 수 있다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 4」.

### 7. `transition: border-left-color` 와 짝짓는다

`border-color` 는 네 변을 다 바꾸므로 왼쪽만 바꾸려면 `border-left-color` 를 쓴다.
`border-left-color` 는 애니메이션 가능한 속성이라 `transition: border-left-color .3s` 같은 선언과 `:hover` 의 새 색으로 서서히 바꿀 수 있다.
근거: 2-summary 「동작 방식 (5)」 · 「언제 쓰고 언제 안 쓰나」.

## 실습 정답

### 실습 1. 왼쪽 강조 줄이 있는 상자 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| `box` 클래스 `div` 에 글자 | `<div class="box">border-left-color</div>` |
| 단축 속성으로 두께 · 선 모양만 | `.box { border-left: 4px solid; }` |
| 색은 따로 빨간 계열로 | `border-left-color: #ef4444;` |
| 선언 차례 | `border-left` 다음 줄에 `border-left-color` |
| 다른 세 변엔 테두리 없음 | `border-left` 만 쓰고 `border` · `border-color` 를 쓰지 않음 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/box-model/reference/border-left-color.html`

```html
<!DOCTYPE html> <!-- HTML5 문서 선언 -->
<html lang="ko"> <!-- 문서 언어를 한국어로 지정 -->
<head> <!-- 문서 메타정보 영역 -->
<meta charset="utf-8"> <!-- 문자 인코딩 UTF-8 설정 -->
<title>border-left-color - 요소의 왼쪽 테두리 색상을 설정</title> <!-- 브라우저 탭 제목 -->
<!--
  [박스 모델] border-left-color
  설명: 요소의 왼쪽 테두리 색상을 설정
  구문: border-left-color: <color>
  팁: 기본값은 currentcolor.
-->
<style>
  /* .box: 왼쪽 테두리 색상 시연 박스 */
  .box {
    border-left: 4px solid;        /* 왼쪽 테두리 단축. 4px 실선. 색상 미지정 */
    border-left-color: #ef4444;    /* 왼쪽 테두리 색상을 빨간색(#ef4444)으로 별도 지정 */
    padding: 16px;                 /* 박스 내부 사방 16px 여백 */
    background: #f8fafc;           /* 배경색 매우 옅은 회색(#f8fafc) */
  }
</style>
</head>
<body>
  <div class="box">border-left-color</div> <!-- 왼쪽 테두리 색상이 적용된 박스 -->

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.box { border-left: 4px solid; border-left-color: #ef4444; padding: 16px; background: #f8fafc; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- `border-left: 4px solid;` 는 색을 적지 않아 이 순간 색이 `currentcolor` 다.
- 바로 다음 줄의 `border-left-color: #ef4444;` 가 색만 덮어쓴다.
- 두 줄의 차례를 바꾸면 단축 속성이 색을 되돌려 글자색 줄이 된다.
- 선 모양 `solid` 가 있어야 색이 보인다.
- `padding` · `background` 는 꾸밈일 뿐 이 속성과 관계없다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

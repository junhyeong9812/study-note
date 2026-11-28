# css/box-model/41 — border-bottom-color — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 파란색 — 기본값 `currentcolor` 가 글자 색을 가리킨다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
아래쪽 테두리는 blue 로 그려진다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
단축 속성에 색이 없으니 `border-bottom-color` 는 초깃값 `currentcolor` 가 된다.
`currentcolor` 는 이 요소의 `color` 인 blue 다.
근거: 2-summary 「동작 방식 (2)」.

### 2. 검정 — 뒤의 단축 속성이 색을 되돌린다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
아래쪽 테두리는 red 가 아니라 black 이다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`border-bottom: 4px solid;` 는 빠진 색을 초깃값 `currentcolor` 로 다시 맞춘다.
이 줄이 `border-bottom-color: red` 보다 뒤에 있어 이기고, `currentcolor` 는 `color` 인 black 이다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 2」.

### 3. 보이지 않는다 — 선 스타일이 없다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
빨간 선은 보이지 않는다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`border-bottom-color` 는 색만 정하고, 테두리 스타일은 기본 `none` 이라 그릴 선이 없다.
근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 3」.

### 4. 글자 색과 테두리 색이 한 번에 함께 바뀐다

테두리 색을 따로 적지 않았다면 `color` 한 곳만 바꿔도 테두리가 같은 색으로 따라온다.
글자 색과 같은 값을 두 군데 하드코딩해서 어긋나는 일을 막는다.
근거: 2-summary 「동작 방식 (2)」 · 「언제 쓰고 언제 안 쓰나」.

### 5. 단축 속성으로 두께 · 스타일을 주고, 색만 뒤에서 덮으려고

`border-bottom: 4px solid;` 는 색을 생략했으므로 색을 `currentcolor` 로 맞춘다.
그 다음 줄의 `border-bottom-color: #ef4444` 가 뒤에 있으니 이겨서 아래쪽 선이 빨강이 된다.
원본 주석도 「색상은 미지정이라 currentcolor 또는 아래에서 덮어씀」이라고 적는다.
근거: 2-summary 「동작 방식 (3)」.

### 6. 받지 않는다 — 아래쪽 한 변만이다

`border-bottom-color` 는 아래쪽 테두리의 색만 정한다.
위 · 왼 · 오른쪽은 각자의 값(지정이 없으면 `currentcolor`)을 그대로 쓴다.
반대로 나중에 쓴 `border-color` 는 네 변을 다 바꾸므로 아래쪽 색도 덮을 수 있다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 5」.

### 7. 자식의 기본값 `currentcolor` 가 상속된 `color` 를 가리키기 때문

자식은 `border-bottom-color` 를 물려받지 않고 자기 초깃값 `currentcolor` 를 쓴다.
그런데 `color` 는 상속되므로 자식의 `color` 가 부모 색이 되고, `currentcolor` 가 그 값을 가리킨다.
그래서 결과적으로 부모 글자 색이 자식 테두리에 나타난다.
근거: 2-summary 「동작 방식 (4)」.

### 8. 「애니메이션 가능」한 색 속성 + `transition`

이 속성은 애니메이션 가능하다 — 두 색 사이를 중간 색으로 보간할 수 있다.
그래서 `transition: border-bottom-color …` 를 걸고 `:hover` 에서 색을 바꾸면 서서히 바뀐다.
근거: 2-summary 「동작 방식 (5)」.

## 실습 정답

### 실습 1. 아래쪽에만 빨간 선이 있는 상자 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| `box` 클래스 `div` 하나, 글자 `border-bottom-color` | `<div class="box">border-bottom-color</div>` |
| 단축 속성으로 두께 · 실선만, 색 없음 | `.box { border-bottom: 4px solid; }` |
| 단축 속성 뒤에 아래쪽 색 지정 | `border-bottom-color: #ef4444;` (단축 줄 다음) |
| 여백 · 배경은 시작 코드대로 | `padding: 16px;` · `background: #f8fafc;` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/box-model/reference/border-bottom-color.html`

```html
<!DOCTYPE html> <!-- HTML5 문서 선언 -->
<html lang="ko"> <!-- 문서 언어를 한국어로 지정 -->
<head> <!-- 문서 메타정보 영역 -->
<meta charset="utf-8"> <!-- 문자 인코딩 UTF-8 설정 -->
<title>border-bottom-color - 요소의 아래쪽 테두리 색상을 설정</title> <!-- 브라우저 탭 제목 -->
<!--
  [박스 모델] border-bottom-color
  설명: 요소의 아래쪽 테두리 색상을 설정
  구문: border-bottom-color: <color>
  팁: 기본값은 currentcolor.
-->
<style>
  /* .box: 아래쪽 테두리 색상 시연 박스 */
  .box {
    border-bottom: 4px solid;       /* 아래쪽 테두리 단축. 4px 두께 실선. 색상은 미지정이라 currentcolor 또는 아래에서 덮어씀 */
    border-bottom-color: #ef4444;   /* 아래쪽 테두리 색상을 빨간색(#ef4444)으로 별도 지정 */
    padding: 16px;                  /* 박스 내부 사방 16px 여백 */
    background: #f8fafc;            /* 배경색 매우 옅은 회색(#f8fafc) */
  }
</style>
</head>
<body>
  <div class="box">border-bottom-color</div> <!-- 아래쪽 테두리 색상이 적용된 박스 -->

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.box { border-bottom: 4px solid; border-bottom-color: #ef4444; padding: 16px; background: #f8fafc; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 단축 속성 `border-bottom` 이 두께 · 스타일을 주고, 생략된 색은 `currentcolor` 로 맞춰진다.
- `border-bottom-color` 가 그 뒤 줄에 있어서 색을 빨강으로 덮는다.
- 두 줄의 차례를 바꾸면 단축 속성이 색을 `currentcolor` 로 되돌려 선이 글자 색이 된다.
- 테두리 스타일(`solid`)이 있어야 색이 실제 선으로 보인다.
- 위 · 왼 · 오른쪽에는 테두리를 주지 않았으므로 아래쪽 선 하나만 남는다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

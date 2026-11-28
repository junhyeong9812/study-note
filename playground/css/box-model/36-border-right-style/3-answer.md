# css/box-model/36 — border-right-style — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 보이지 않는다 — 무늬가 기본값 `none` 이라 두께가 0 이 된다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
오른쪽 변에 선이 없고, 옅은 박스와 여백만 남는다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`border-right-style` 을 쓰지 않았으므로 기본값 `none` 이 그대로다.
무늬가 `none` 이면 그 변의 두께는 0 으로 계산되어, 3px 과 파란색을 정해도 그릴 선이 없다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 1」.

### 2. `dashed` — 네 값 가운데 두 번째가 오른쪽이다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
오른쪽 변은 파선(`dashed`)으로 그려진다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`border-style` 에 값을 넷 주면 위 → 오른쪽 → 아래 → 왼쪽, 시계 방향으로 들어간다.
첫 값 `solid` 는 위, 두 번째 `dashed` 가 오른쪽, `dotted` 는 아래, `double` 은 왼쪽이다.
근거: 2-summary 「동작 방식 (3)」.

### 3. 두께는 `medium`, 색은 `currentcolor`(여기서는 검정)

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
오른쪽 변에 검은 점선이 기본 두께로 그려진다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
무늬가 `none` 이 아니므로 테두리가 켜진다.
두께와 색은 선언이 없으니 각자의 기본값을 쓴다 — 두께는 `medium`, 색은 `currentcolor` 이고, `currentcolor` 는 글자색 `black` 을 가져온다.
`medium` 이 정확히 몇 px 인지는 브라우저가 정한다 (확인 필요).
근거: 2-summary 「동작 방식 (1)」 · 「구현 세부사항 대 언어 보장」.

### 4. 무늬 값은 discrete 라 중간 단계가 없다

`solid` 와 `dashed` 사이에 「반쯤 파선」 같은 값이 없어서, 시간을 나눠 보간할 수 없다.
그래서 이 속성은 애니메이션 불가이고, 전환을 걸어도 값이 한 번에 바뀐다.
부드러운 효과가 필요하면 무늬는 고정하고 색이나 두께를 바꾼다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 2」(원본 팁).

### 5. 자식은 기본값 `none` 을 갖는다 — 상속되지 않는다

`border-right-style` 은 상속되지 않는 속성이다.
부모의 값이 자식에게 옮아가지 않으므로, 자식은 선언이 없으면 기본값 `none` 이 되어 오른쪽 선이 없다.
자식에게도 선이 필요하면 자식 선택자에 따로 써야 한다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 3」.

### 6. 표의 테두리 병합(`border-collapse: collapse`)에서 갈린다

화면에서는 둘 다 선을 그리지 않는다.
표에서 이웃 칸의 테두리를 한 줄로 합칠 때, `hidden` 은 우선순위가 높아 그 자리의 테두리를 없앤다.
`none` 은 그렇지 않아서, 이웃 칸이 준 테두리가 남을 수 있다.
근거: 2-summary 「동작 방식 (2)」 · 「언제 쓰고 언제 안 쓰나」.

### 7. `border-right` 단축 속성 — 예: `border-right: 3px dotted #3b82f6;`

`border-right` 는 오른쪽 변의 두께 · 무늬 · 색을 한 줄에 묶는다.
단, 단축 속성은 적지 않은 부분을 기본값으로 되돌리므로, 무늬를 빠뜨리면 `none` 이 되어 선이 사라진다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 4」.

### 8. padding 과 margin 사이

테두리는 padding 바깥, margin 안쪽에 놓인다.
그래서 예제의 `padding: 16px` 은 글자와 점선 사이의 간격이 된다.
근거: 2-summary 「용어 풀이」의 「테두리」.

## 실습 정답

### 실습 1. 오른쪽에만 점선 테두리를 두른 박스

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| `box` 클래스 `div` 하나에 글자 넣기 | `<div class="box">border-right-style</div>` |
| 오른쪽 무늬를 점선으로 | `.box { border-right-style: dotted; }` |
| 두께와 색을 개별 속성으로 | `border-right-width: 3px;` · `border-right-color: #3b82f6;` |
| 나머지 세 변에는 테두리 없음 | `.box` 에 다른 변의 `border-*-style` 선언이 없다(기본값 `none`) |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/box-model/reference/border-right-style.html`

```html
<!DOCTYPE html> <!-- HTML5 문서 선언 -->
<html lang="ko"> <!-- 문서 언어를 한국어로 지정 -->
<head> <!-- 문서 메타정보 영역 -->
<meta charset="utf-8"> <!-- 문자 인코딩 UTF-8 설정 -->
<title>border-right-style - 요소의 오른쪽 테두리 스타일을 설정</title> <!-- 브라우저 탭 제목 -->
<!--
  [박스 모델] border-right-style
  설명: 요소의 오른쪽 테두리 스타일을 설정
  구문: border-right-style: <line-style>
  팁: discrete 값이라 부드러운 전환 불가.
-->
<style>
  /* .box: 오른쪽 테두리 스타일 시연 박스 */
  .box {
    border-right-style: dotted;      /* 오른쪽 테두리 스타일 점선(dotted). 종류: none/solid/dashed/dotted/double/groove/ridge/inset/outset */
    border-right-width: 3px;         /* 오른쪽 테두리 두께 3px */
    border-right-color: #3b82f6;     /* 오른쪽 테두리 색상 파란색(#3b82f6) */
    padding: 16px;                   /* 박스 내부 사방 16px 여백 */
    background: #f8fafc;             /* 배경색 매우 옅은 회색(#f8fafc) */
  }
</style>
</head>
<body>
  <div class="box">border-right-style</div> <!-- 오른쪽 테두리 스타일이 적용된 박스 -->

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.box { border-right-style: dotted; border-right-width: 3px; border-right-color: #3b82f6; padding: 16px; background: #f8fafc; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**

- 세 박자 가운데 무늬(`border-right-style`)가 스위치다 — 이 줄이 없으면 나머지 두 줄은 아무것도 그리지 않는다.
- 다른 세 변은 아무것도 쓰지 않아 기본값 `none` 이므로 선이 없다.
- 개별 속성 세 줄은 `border-right: 3px dotted #3b82f6;` 한 줄과 같은 일을 한다.
- `padding` 은 글자와 점선 사이 간격이 되고, `background` 는 테두리 안쪽 박스를 보이게 해 오른쪽 선이 눈에 띄게 한다.
- `dotted` 를 다른 값(`dashed` · `double` · `groove` 등)으로 바꿔 보며 무늬 차이를 확인할 수 있다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

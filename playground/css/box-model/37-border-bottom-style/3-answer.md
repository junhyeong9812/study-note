# css/box-model/37 — border-bottom-style — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 아래쪽 선이 보이지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`border-bottom-style` 을 쓰지 않았으므로 기본값 `none` 이 적용된다.
`none` 은 「테두리 없음」이라 굵기 3px · 파란 색을 정했어도 아래쪽 선이 그려지지 않는다.

**왜 그런가**

선의 모양이 「안 그음」이면 굵기와 색은 쓰일 데가 없다.
근거: 2-summary 「동작 방식 (2)」, 「어디서 틀리나 1」.

### 2. 중간 모양 없이 어느 순간 한 번에 실선으로 바뀐다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

1초 동안 파선이 점점 실선이 되는 모습은 없다.
파선 상태로 있다가 어느 시점에 한 번에 실선으로 바뀐다.
바뀌는 정확한 시점은 이 문서의 재료로 정할 수 없다 (원본에 근거 없음 — 추론).

**왜 그런가**

`border-bottom-style` 은 discrete 값이라 `dashed` 와 `solid` 사이의 중간 값이 없다.
근거: 2-summary 「동작 방식 (3)」, 원본 팁.

### 3. 값이 이름(키워드)이라 중간 값을 계산할 수 없기 때문이다

`solid` · `dashed` 같은 값은 숫자가 아니라 이름이다.
「반쯤 실선」 같은 중간 단계가 없으니 discrete 값이고, 애니메이션 가능 여부가 `False` 다.
근거: 2-summary 「동작 방식 (3)」.

### 4. 표의 테두리 병합에서 우선순위가 높기 때문이다

일반 요소에서는 `hidden` 과 `none` 이 같다.
하지만 표에서 이웃 칸의 테두리를 합칠 때 `hidden` 은 우선순위가 높아 맞닿은 선을 확실히 감춘다.
근거: 2-summary 「문법 — 형태와 규칙」 값 표, 「어디서 틀리나 3」.

### 5. 미치지 않는다 — 부모의 아래쪽에만 선이 생긴다

상속이 `False` 라서 자식은 부모의 값을 물려받지 않고 기본값 `none` 을 쓴다.
자식에도 선이 필요하면 자식에게 따로 준다.
근거: 2-summary 「동작 방식 (4)」.

### 6. 바꿀 수 없다 — 아래쪽 한 변만 바꾼다

이름에 `bottom` 이 든 속성은 아래쪽 변만 다룬다.
나머지 세 변은 기본값이나 따로 준 값을 그대로 쓴다.
근거: 2-summary 「동작 방식 (1)」, 「어디서 틀리나 5」.

### 7. 모양 · 굵기 · 색을 셋이 나눠 맡기 때문이다

`border-bottom-style` 은 모양만, `border-bottom-width` 는 굵기, `border-bottom-color` 는 색을 정한다.
모양이 `none` 이 아니어야 선이 그려지고, 그 선의 굵기와 색은 다른 두 속성이 정한다.
근거: 2-summary 「한눈에」 대응표, 「동작 방식 (1)」.

### 8. `groove` ↔ `ridge`, `inset` ↔ `outset` 이 서로 반대다

`groove` 는 안으로 파인 효과, `ridge` 는 밖으로 돌출된 효과다.
`inset` 은 요소가 묻힌 효과, `outset` 은 요소가 돌출된 효과다.
근거: 2-summary 「문법 — 형태와 규칙」 값 표.

## 실습 정답

### 실습 1. 아래쪽에만 실선이 있는 상자 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| `class="box"` 인 `div` 에 글자 넣기 | `<div class="box">border-bottom-style</div>` |
| 아래쪽 테두리 모양을 실선으로 | `.box { border-bottom-style: solid; }` |
| 굵기 · 색은 채워 둔 값 그대로 | `border-bottom-width` · `border-bottom-color` 줄 |
| 다른 세 변에는 선 없음 | `bottom` 속성만 쓰고 다른 변은 기본값 `none` 그대로 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/box-model/reference/border-bottom-style.html`

```html
<!DOCTYPE html> <!-- HTML5 문서 선언 -->
<html lang="ko"> <!-- 문서 언어를 한국어로 지정 -->
<head> <!-- 문서 메타정보 영역 -->
<meta charset="utf-8"> <!-- 문자 인코딩 UTF-8 설정 -->
<title>border-bottom-style - 요소의 아래쪽 테두리 스타일을 설정</title> <!-- 브라우저 탭 제목 -->
<!--
  [박스 모델] border-bottom-style
  설명: 요소의 아래쪽 테두리 스타일을 설정
  구문: border-bottom-style: <line-style>
  팁: discrete 값이라 부드러운 전환 불가.
-->
<style>
  /* .box: 아래쪽 테두리 스타일 시연 박스 */
  .box {
    border-bottom-style: solid;     /* 아래쪽 테두리 스타일을 실선(solid)으로 지정. 종류: none/solid/dashed/dotted/double/groove/ridge/inset/outset */
    border-bottom-width: 3px;       /* 아래쪽 테두리 두께 3px */
    border-bottom-color: #3b82f6;   /* 아래쪽 테두리 색상 파란색(#3b82f6) */
    padding: 16px;                  /* 박스 내부 사방 16px 여백 */
    background: #f8fafc;            /* 배경색 매우 옅은 회색(#f8fafc) */
  }
</style>
</head>
<body>
  <div class="box">border-bottom-style</div> <!-- 아래쪽 테두리 스타일이 적용된 박스 -->

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.box { border-bottom-style: solid; border-bottom-width: 3px; border-bottom-color: #3b82f6; padding: 16px; background: #f8fafc; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 시작 코드는 굵기와 색만 있어 선이 안 보인다 — 기본값 `none` 때문이다.
- `border-bottom-style: solid;` 한 줄이 들어가야 아래쪽 선이 그려진다.
- `bottom` 이 든 속성만 썼으므로 위 · 왼 · 오른쪽은 선 없이 남는다.
- 화면에 보이는 모습은 코드에서 읽은 것이다 (코드에서 읽은 것 — 렌더 실측 아님).

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

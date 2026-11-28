# css/box-model/38 — border-left-style — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 선은 보이지 않고, 바깥 폭은 200px 이다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- 왼쪽에 빨간 선은 보이지 않는다 (코드에서 읽은 것 — 렌더 실측 아님).
- 바깥 폭은 200px 로 계산된다.

**왜 그런가**

- `border-left-style` 을 적지 않았으므로 기본값 `none` 이다.
- style 이 `none` 이면 그 변의 두께는 0 으로 계산되므로, 4px 도 폭에 더해지지 않는다.
- 근거: 2-summary 「동작 방식 (2)」, 「어디서 틀리나 2」.

### 2. 중간 모습 없이 한 번에 파선으로 바뀐다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- 실선이 서서히 파선으로 변하는 모습은 없다.
- 실선에서 파선으로 건너뛰듯 바뀐다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**

- 선 모양은 discrete 값이라 `solid` 와 `dashed` 사이의 사이값이 없다.
- 원본 팁 「discrete 값이라 부드러운 전환 불가」 그대로다.
- 근거: 2-summary 「동작 방식 (5)」, 「어디서 틀리나 1」.

### 3. `.a` 는 파선, `.b` 는 실선

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- `.a` 의 왼쪽 선은 `dashed`(파선)다.
- `.b` 의 왼쪽 선은 `solid`(실선)다.

**왜 그런가**

- 같은 규칙 안에서는 뒤에 쓴 선언이 이긴다.
- `.a` 는 단축 속성 뒤에 개별 속성이 와서 모양만 `dashed` 로 다시 정한다.
- `.b` 는 단축 속성 `border-left` 가 뒤에 와서 모양을 `solid` 로 덮는다.
- 근거: 2-summary 「문법 — 형태와 규칙」의 쓰기 표, 「어디서 틀리나 3」.

### 4. 병합된 표에서 이웃 테두리를 확실히 이기기 위해서다

- 보통 요소에서는 `none` 과 `hidden` 모두 「선 없음」이다.
- `border-collapse: collapse` 로 이웃 칸이 한 선을 나눠 쓸 때, `none` 은 이웃의 `solid` 에 지지만 `hidden` 은 우선순위가 높아 그 선을 지운다.
- 그래서 「표에서 이 선만큼은 반드시 없애라」는 뜻을 따로 표현할 값이 필요하다.
- 근거: 2-summary 「동작 방식 (4)」, 「어디서 틀리나 5」.

### 5. 선 모양에는 사이값이 없기 때문이다

- 두께는 숫자라 4px 과 8px 사이에 5px · 6px 같은 중간값을 만들 수 있다.
- 선 모양은 `solid` · `dashed` 같은 이름이라 「반쯤 점선」 같은 중간값을 만들 수 없다.
- 그래서 모양은 discrete 하게 바뀌고, 부드러운 효과는 두께나 색으로 낸다.
- 근거: 2-summary 「동작 방식 (5)」, 「언제 쓰고 언제 안 쓰나」.

### 6. 생기지 않는다 — 상속되지 않는다

- `border-left-style` 은 상속되지 않는 속성이다.
- 부모의 왼쪽 변에만 선이 생기고, 자식 `p` 들의 style 은 기본값 `none` 그대로다.
- 자식마다 선이 필요하면 자식 선택자에 직접 준다.
- 근거: 2-summary 「문법 — 형태와 규칙」 규칙 불릿, 「어디서 틀리나 4」.

### 7. `box-sizing: border-box`

- 기본 `content-box` 에서는 테두리 두께가 `width` 바깥에 더해져 바깥 폭이 204px 이 된다.
- `box-sizing: border-box` 를 주면 `width` 가 테두리까지 포함해 재므로 바깥 폭이 200px 로 묶인다.
- 근거: 2-summary 「어디서 틀리나 6」.

## 실습 정답

### 실습 1. 왼쪽에만 실선 강조선이 있는 박스 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| `box` 클래스 `div` 하나, 글자 `border-left-style` | `<div class="box">border-left-style</div>` |
| 왼쪽 테두리 모양을 실선으로 | `.box { border-left-style: solid; }` |
| 두께 · 색 · 여백 · 배경 선언 유지 | `border-left-width` · `border-left-color` · `padding` · `background` 줄 |
| 다른 세 변에는 테두리 없음 | `border-top/right/bottom-*` 을 쓰지 않음 → 기본값 `none` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/box-model/reference/border-left-style.html`

```html
<!DOCTYPE html> <!-- HTML5 문서 선언 -->
<html lang="ko"> <!-- 문서 언어를 한국어로 지정 -->
<head> <!-- 문서 메타정보 영역 -->
<meta charset="utf-8"> <!-- 문자 인코딩 UTF-8 설정 -->
<title>border-left-style - 요소의 왼쪽 테두리 스타일을 설정</title> <!-- 브라우저 탭 제목 -->
<!--
  [박스 모델] border-left-style
  설명: 요소의 왼쪽 테두리 스타일을 설정
  구문: border-left-style: <line-style>
  팁: discrete 값이라 부드러운 전환 불가.
-->
<style>
  /* .box: 왼쪽 테두리 스타일 시연 박스 */
  .box {
    border-left-style: solid;       /* 왼쪽 테두리 스타일 실선. 종류: none/solid/dashed/dotted/double/groove/ridge/inset/outset */
    border-left-width: 4px;         /* 왼쪽 테두리 두께 4px */
    border-left-color: #3b82f6;     /* 왼쪽 테두리 색상 파란색(#3b82f6) */
    padding: 16px;                  /* 박스 내부 사방 16px 여백 */
    background: #f8fafc;            /* 배경색 매우 옅은 회색(#f8fafc) */
  }
</style>
</head>
<body>
  <div class="box">border-left-style</div> <!-- 왼쪽 테두리 스타일이 적용된 박스 -->

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.box { border-left-style: solid; border-left-width: 4px; border-left-color: #3b82f6; padding: 16px; background: #f8fafc; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**

- 비워 둔 핵심은 `border-left-style: solid;` 한 줄이다.
- 이 줄이 없으면 두께와 색이 있어도 선은 생기지 않는다(기본값 `none`).
- `border-left-*` 만 썼으므로 나머지 세 변은 `none` 그대로라 왼쪽에만 선이 생긴다.
- 한 줄로 줄이고 싶으면 `border-left: 4px solid #3b82f6;` 단축 속성으로 같은 결과를 낼 수 있다.
- 강조선에 hover 효과를 더한다면 모양 대신 색이나 두께를 전환해야 부드럽게 보인다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

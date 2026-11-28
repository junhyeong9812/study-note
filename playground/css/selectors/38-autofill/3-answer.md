# css/selectors/38 — :autofill — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 회색 그대로 — 직접 친 값에는 `:autofill` 이 걸리지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
테두리는 `.af-input` 규칙의 회색(`#d1d5db`) 그대로다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`:autofill` 은 값이 있느냐가 아니라 브라우저가 자동완성으로 채웠느냐를 보는 조건이다.
사용자가 직접 친 값에는 그 상태가 붙지 않으므로 `.af-input:autofill` 규칙은 걸리지 않는다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 4」.

### 2. 0.2초에 걸쳐 주황 테두리로 바뀌고 바깥에 1px 주황 고리가 생긴다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
테두리가 회색에서 주황(`#f59e0b`)으로 0.2초 동안 바뀌고, 테두리 바깥에 1px 주황 고리가 생긴다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
후보를 고르면 브라우저가 값을 채우고 칸이 `:autofill` 상태가 된다.
그러면 자동완성 규칙이 함께 걸려 `border-color` 와 `box-shadow` 가 덧입혀진다.
평소 규칙의 `transition: all 0.2s` 가 남아 있으므로 바뀌는 속성이 0.2초에 걸쳐 변한다.
`box-shadow: 0 0 0 1px` 은 흐림 없는 바깥 그림자라 고리처럼 보인다.
근거: 2-summary 「동작 방식 (3)」.

### 3. 브라우저가 기본 배경색을 강제해서 `background` 가 지는 일이 있기 때문이다

원본 팁에 따르면 Chrome 등 브라우저는 자동완성 때 기본 배경색을 강제로 적용한다.
그래서 작성자의 `background` 가 보이지 않을 수 있다.
`box-shadow` 트릭은 배경색 자체를 바꾸려 하지 않고, 배경 **위**에 `inset` 그림자 층을 깔아 가린다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 1」.

### 4. 바깥 그림자는 테두리 밖에 그려져 배경에 닿지 않는다

`inset` 이 없는 그림자는 요소 테두리 바깥에 그려진다.
칸 안쪽의 배경은 그대로 남으므로 덮기 노릇을 못 한다.
배경을 덮으려면 `inset` 을 붙이고 퍼짐 값을 칸보다 크게 준다(`inset 0 0 0 1000px 색`).
원본의 1px 그림자는 테두리를 강조하는 고리일 뿐이다.
근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (3)」 · 「어디서 틀리나 3」.

### 5. 칸의 종류를 알려 주어 자동완성이 일어날 자리를 분명히 한다

`autocomplete="username"` 은 브라우저에게 「이 칸은 사용자 이름 칸」이라고 알려 주는 힌트다.
`:autofill` 은 브라우저가 값을 채워야 걸리므로, 브라우저가 어떤 저장값을 넣을지 판단할 단서가 있어야 그 상태가 생길 길이 열린다.
다만 실제로 제안하고 채울지는 브라우저가 정한다 — 힌트일 뿐 보장은 아니다.
근거: 2-summary 「동작 방식 (1)」 · 「구현 세부사항 대 언어 보장」.

### 6. 그 규칙이 영영 걸리지 않아 안내가 보이지 않는다

자동완성이 일어나지 않으면 칸에 `:autofill` 상태가 붙을 일이 없다.
그러면 그 규칙에 넣은 내용도 한 번도 적용되지 않는다.
그래서 `:autofill` 규칙은 덧입힘 장식으로만 쓰고, 꼭 필요한 정보는 평소 규칙이나 별도 문구에 둔다.
근거: 2-summary 「어디서 틀리나 5」 · 「언제 쓰고 언제 안 쓰나」.

### 7. 클래스 하나 + 의사 클래스 하나가 클래스 하나보다 점수가 높다

의사 클래스는 명시도를 셀 때 클래스와 같은 무게다.
`.af-input:autofill` 은 클래스 둘 무게, `.af-input` 은 클래스 하나 무게다.
그래서 겹치는 `border-color` 는 자동완성 규칙의 주황이 이긴다.
겹치지 않는 `padding` · `width` · `transition` 은 평소 규칙 값이 그대로 남는다.
근거: 2-summary 「동작 방식 (3)」.

### 8. 고르는 기준(누가 · 무엇을 했나)이 다르고, 동시에 걸릴 수 있다

둘 다 HTML 에 적히지 않은 상태를 보고 고르는 의사 클래스다.
`:focus` 는 칸이 입력 포커스를 받은 상태를, `:autofill` 은 브라우저가 자동완성으로 값을 채운 상태를 본다.
후보를 고른 뒤에도 커서가 그 칸에 머물러 있으면 두 상태가 함께 성립하므로 두 규칙이 동시에 걸릴 수 있다.
근거: 2-summary 「동작 방식 (1)」의 의사 클래스 용어 풀이. 두 상태가 동시에 걸린다는 부분은 (원본에 근거 없음 — 추론).

## 실습 정답

### 실습 1. 자동완성된 사용자 이름 칸만 강조하기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. `af-input` 클래스의 텍스트 입력 칸, 자리표시 글 | `<input class="af-input" type="text" name="username" … placeholder="사용자 이름" />` |
| 2. 사용자 이름 칸임을 브라우저에 알림 | `autocomplete="username"` |
| 3. 평소 모양과 0.2초 전이 | `.af-input { … transition: all 0.2s; }` |
| 4. 자동완성된 칸에만 강조 | `.af-input:autofill { background … ; border-color … ; box-shadow … }` |
| 5. 직접 친 값에는 강조 없음 | `:autofill` 조건 자체 — 브라우저가 채운 상태에서만 매칭 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/selectors/reference/autofill.html`

```html
<!DOCTYPE html>
<!-- 문서 타입 선언: HTML5 -->
<html lang="ko">
<head>
<meta charset="utf-8">
<title>:autofill - 브라우저가 자동완성으로 값을 채운 input 요소에 적용된다.</title>
<!--
  [선택자] :autofill
  설명: 브라우저가 자동완성으로 값을 채운 input 요소에 적용된다.
  구문: input:autofill { }
  팁: Chrome 등 브라우저는 자동완성 시 기본 배경색을 강제 적용한다. 이를 제거하려면 box-shadow로 덮는 트릭을 사용할 수 있다.
-->
<style>
  /* .af-input: class 속성에 af-input을 가진 요소 매칭 */
  .af-input {
    padding: 10px 14px;          /* 안쪽 여백: 위아래 10px, 좌우 14px */
    border: 2px solid #d1d5db;   /* 2px 회색 테두리 */
    border-radius: 8px;          /* 8px 둥근 모서리 */
    font-size: 14px;             /* 글자 크기 14px */
    width: 250px;                /* 너비 250px */
    transition: all 0.2s;        /* 모든 속성 변화에 0.2초 전이 */
  }
  /* .af-input:autofill: .af-input 중 브라우저 자동완성으로 값이 채워진 상태 매칭 */
  .af-input:autofill {
    background: #fef3c7 !important; /* 자동완성 시 노란색 배경 강제 적용 */
    border-color: #f59e0b;          /* 자동완성 시 주황색 테두리 */
    box-shadow: 0 0 0 1px #f59e0b;  /* 1px 주황색 그림자로 강조 */
  }
</style>
</head>
<body>
  <!-- 자동완성될 수 있는 사용자명 입력 필드 -->
  <input class="af-input" type="text" name="username" autocomplete="username" placeholder="사용자 이름" />

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.af-input { padding: 10px 14px; border: 2px solid #d1d5db; border-radius: 8px; font-size: 14px; width: 250px; transition: all 0.2s; }
.af-input:autofill { background: #fef3c7 !important; border-color: #f59e0b; box-shadow: 0 0 0 1px #f59e0b; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 핵심은 선택자 `.af-input:autofill` 한 줄이다 — 콜론을 띄우지 않고 붙여 써야 「그 칸이 자동완성된 상태」라는 뜻이 된다.
- `autocomplete="username"` 이 있어야 브라우저가 이 칸에 무엇을 채울지 판단하기 쉽다.
- 평소 규칙에 `transition` 이 있으므로 자동완성 순간의 색 변화가 0.2초에 걸쳐 일어난다.
- 정답의 `background: #fef3c7 !important` 는 브라우저가 기본 배경을 강제하면 보이지 않을 수 있다 (확인 필요) — 배경까지 확실히 바꾸려면 `box-shadow: inset 0 0 0 1000px …` 로 덮는다.
- 정답의 `box-shadow: 0 0 0 1px` 은 바깥 고리라서 배경 덮기가 아니라 테두리 강조다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

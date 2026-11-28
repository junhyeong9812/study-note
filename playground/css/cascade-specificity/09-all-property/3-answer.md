# css/cascade-specificity/09 — all property — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 「뒤 글자」와 한 줄에 붙고, 크기 · 굵기는 부모를 따른다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
- 「제목」과 「뒤 글자」는 같은 줄에 이어진다 (코드에서 읽은 것 — 렌더 실측 아님).
- 글자 크기는 부모의 `16px`, 굵기는 부모의 보통 굵기, 글자색은 부모의 색이 된다.
- 위아래 여백도 없다.

**왜 그런가**
- `display` 는 비상속 속성이라 `unset` 이면 초깃값 `inline` 이 된다.
- 부모가 flex 가 아닌 보통 블록이라 블록화가 일어나지 않고, 인라인인 `h3` 뒤에 `span` 이 그대로 이어진다.
- `font-size` · `font-weight` · `color` 는 상속 속성이라 `unset` 이면 부모 값을 받는다.
- 브라우저가 `h3` 에 주던 큰 글자 · 굵기 · 여백은 모두 덮인다.
- 근거: 2-summary 「동작 방식 (2)」, 「어디서 틀리나 1」.

### 2. `align-self` 가 지워져 버튼이 가로로 늘어난다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
- 버튼은 시작점에 붙지 않고 컨테이너 가로폭을 꽉 채우도록 늘어난다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
- 같은 블록에서는 뒤의 선언이 이긴다.
- 뒤에 온 `all: revert` 가 `align-self` 까지 덮는다.
- 브라우저 기본 버튼 스타일에는 `align-self` 가 없으니 값은 초깃값 `auto` 가 된다.
- `auto` 는 부모 정렬을 따르고, 정렬을 정하지 않은 세로 flex 컨테이너는 아이템을 가로로 늘린다.
- 원본이 `align-self: flex-start` 를 `all: revert` 뒤에 둔 것이 이 때문이다.
- 근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (3)」, 「어디서 틀리나 4」.

### 3. 테두리는 `tomato`, 글 방향은 `rtl` 그대로다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
- 테두리 색은 `tomato` 다.
- 글 방향은 `rtl` 로 남는다.

**왜 그런가**
- `all` 은 커스텀 속성을 건드리지 않는다.
- 그래서 `.theme` 에서 물려받은 `--accent` 가 살아 있고 `var(--accent)` 는 `tomato` 로 풀린다.
- `border` 는 `all: initial` 뒤에 적었으니 같은 블록 순서에서 이긴다.
- `direction` 도 `all` 이 건드리지 않는 속성이라 앞 규칙의 `rtl` 이 그대로 쓰인다.
- 근거: 2-summary 「동작 방식 (1)」, 「어디서 틀리나 7」.

### 4. `unset` 은 버튼다운 모양까지 지우고, `revert` 는 브라우저 기본 모양을 남긴다

- `all: unset` 은 비상속 속성을 모두 초깃값으로 보낸다.
- 그래서 버튼의 테두리 · 바탕 · 안쪽 여백 같은 브라우저 기본 꾸밈까지 사라지고 `display` 도 `inline` 이 된다.
- `all: revert` 는 작성자 선언만 없던 셈 치고 브라우저 기본 스타일로 물러난다.
- 그래서 「누를 수 있는 버튼으로 보이는 모양」이 남는다.
- 리셋의 목적이 대개 「내가 입힌 꾸밈 걷어내기」라서 `revert` 가 더 안전하다.
- 근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (3)」, 「언제 쓰고 언제 안 쓰나」.

### 5. 순서를 바꾸면 `all: unset` 이 `cursor` 까지 지운다

- 같은 선언 블록에서는 뒤에 적은 선언이 이긴다.
- `all` 은 `cursor` 도 포함하는 단축 속성이다.
- `cursor: text` 를 앞에 두면 뒤의 `all: unset` 이 그것을 `unset` 으로 덮는다.
- 「모두 지운 뒤 필요한 것만 다시 준다」는 순서가 이 규칙에서 나온다.
- 근거: 2-summary 「동작 방식 (1)」, 「어디서 틀리나 4」.

### 6. `#title` 의 빨강이 남는다

- `all` 은 속성마다 보통 선언으로 펼쳐질 뿐 특별한 우선권이 없다.
- `color` 를 두고 겨루면 `#title` (1,0,0) 이 `.reset-heading` (0,1,0) 보다 명시도가 높다.
- 그래서 글자색은 빨강이고, 다른 속성은 `all: unset` 이 정한 값이 된다.
- 근거: 2-summary 「동작 방식 (1)」, 「어디서 틀리나 5」.

### 7. 지정값은 `inline` 이지만 flex 아이템이라 블록처럼 놓인다

- `all: unset` 으로 `display` 가 `inline` 이 되는 것까지는 맞다.
- 그러나 이 제목은 `display: flex` 인 `.all-demo` 의 자식, 곧 flex 아이템이다.
- flex 아이템의 `display` 는 블록 수준으로 바뀌어(blockify) 배치된다.
- 그래서 이 데모에서는 제목이 버튼과 한 줄로 붙지 않고 따로 한 줄을 차지할 것으로 읽힌다 (코드에서 읽은 것 — 렌더 실측 아님).
- 원본 주석은 「inline으로 돌아감」이 화면 배치에도 그대로 드러나는 것처럼 읽혀 의심스럽다.
- 근거: 2-summary 「어디서 틀리나 2」.

### 8. `color` 는 상속 속성, `border` 는 비상속 속성이기 때문이다

- `unset` 은 속성의 성질에 따라 갈린다.
- 상속 속성은 `inherit` 처럼 부모 값을 받으니 `color` 는 부모 글자색이 된다.
- 비상속 속성은 `initial` 처럼 초깃값을 받는다.
- `border` 의 초깃값은 테두리 없음이라 테두리가 사라진다.
- 근거: 2-summary 「동작 방식 (2)」, 「문법 — 형태와 규칙」 표.

### 9. `revert` 는 출처를, `revert-layer` 는 캐스케이드 레이어를 한 단계 돌린다

- `revert` 는 작성자 출처의 선언을 없던 셈 치고 사용자 · 브라우저 출처의 값으로 물러난다.
- `revert-layer` 는 `@layer` 로 나눈 작성자 스타일에서 지금 레이어만 없던 셈 치고 바로 앞 레이어의 값을 쓴다.
- 그래서 레이어를 쓰는 코드에서 한 층만 물리고 싶으면 `revert-layer`, 작성자 스타일 전체를 물리고 싶으면 `revert` 다.
- 근거: 2-summary 「동작 방식 (3)」, 「언제 쓰고 언제 안 쓰나」.

## 실습 정답

### 실습 1. 꾸민 요소와 `all` 로 되돌린 요소를 나란히 놓기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 자식 넷을 세로로 쌓고 간격 두기 | `.all-demo { display: flex; flex-direction: column; gap: … }` |
| 2. 꾸민 첫 제목 | `.styled-heading { color · font-size · font-weight · padding · background · border-left · border-radius }` |
| 3. 한 선언으로 모든 속성 `unset` | `.reset-heading { all: unset; }` |
| 4. `all` 다음에 텍스트 커서 | `.reset-heading { … cursor: text; }` |
| 5. 꾸민 첫 버튼, 시작점에 붙이기 | `.styled-btn { … cursor: pointer; align-self: flex-start; }` |
| 6. 브라우저 기본 버튼으로 되돌리기 | `.reset-btn { all: revert; }` |
| 7. `all` 다음에 자체 정렬 다시 주기 | `.reset-btn { … align-self: flex-start; }` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/cascade-specificity/reference/all-property.html`

```html
<!DOCTYPE html>
<!-- 문서 타입 선언: HTML5 -->
<html lang="ko">
<!-- HTML 루트: 문서 언어를 한국어로 지정 -->
<head>
<!-- 메타 정보 영역 -->
<meta charset="utf-8">
<!-- 문자 인코딩: UTF-8 -->
<title>all property - 모든 CSS 속성을 한 번에 초기화하는 단축 속성. unicode-bidi, direction, 커스텀 속성을 제외한 모든 속성에 initial, inherit, unset, revert를 적용</title>
<!--
  [캐스케이드 & 명시도] all property
  설명: 모든 CSS 속성을 한 번에 초기화하는 단축 속성. unicode-bidi, direction, 커스텀 속성을 제외한 모든 속성에 initial, inherit, unset, revert를 적용
  구문: all: initial | inherit | unset | revert | revert-layer;
  팁: all: unset은 요소를 완전히 '빈 캔버스'로 만듦 — display까지 초기화되므로 주의. all: revert가 대부분의 리셋 용도에 더 안전.
-->
<style>
  /* .all-demo: 데모 컨테이너 (특이도 0,1,0) */
  .all-demo {
    padding: 20px;              /* 안쪽 여백 20px */
    background: #f1f5f9;        /* 배경: 연한 회색 */
    border-radius: 8px;         /* 모서리 둥글게 8px */
    display: flex;              /* 자식을 flex로 배치 */
    flex-direction: column;     /* 세로 방향 정렬 */
    gap: 12px;                  /* 자식 간 간격 12px */
  }
  /* .styled-heading: 일반적으로 스타일링된 제목 (특이도 0,1,0) */
  .styled-heading {
    color: #1e293b;             /* 글자색: 진한 네이비 */
    font-size: 24px;            /* 글자 크기 24px */
    font-weight: 700;           /* 굵기 700 (Bold) */
    padding: 12px;              /* 안쪽 여백 12px */
    background: #dbeafe;        /* 배경: 연한 파랑 */
    border-left: 4px solid #3b82f6; /* 왼쪽 테두리 강조선 */
    border-radius: 4px;         /* 모서리 둥글게 4px */
  }
  /* .reset-heading: all: unset으로 모든 스타일 제거 (특이도 0,1,0) */
  .reset-heading {
    all: unset;                 /* 모든 속성 초기화 — display까지 inline으로 돌아감 */
    cursor: text;               /* 필요한 것만 다시 추가 (텍스트 커서) */
  }
  /* .styled-btn: 일반적인 버튼 스타일 (특이도 0,1,0) */
  .styled-btn {
    padding: 12px 24px;         /* 상하 12px, 좌우 24px */
    background: #3b82f6;        /* 배경: 파랑 */
    color: white;               /* 글자색: 흰색 */
    border: none;               /* 테두리 제거 */
    border-radius: 8px;         /* 모서리 둥글게 8px */
    font-size: 16px;            /* 글자 크기 16px */
    font-weight: 600;           /* 굵기 600 */
    cursor: pointer;            /* 마우스 포인터 손가락 모양 */
    align-self: flex-start;     /* flex 컨테이너에서 자체 정렬: 시작점 */
  }
  /* .reset-btn: all: revert로 브라우저 기본 버튼 스타일로 복원 (특이도 0,1,0) */
  .reset-btn {
    all: revert;                /* 작성자 스타일을 무시하고 브라우저 기본 버튼으로 복원 */
    align-self: flex-start;     /* revert 이후에도 flex 정렬은 유지 */
  }
</style>
</head>
<body>
<!-- 문서 본문 -->
  <div class="all-demo">
    <!-- 데모 영역: all 속성 비교 -->
    <h3 class="styled-heading">스타일된 제목 (before)</h3>
    <!-- 일반적으로 스타일링된 제목 -->
    <h3 class="reset-heading">all: unset 적용 (after)</h3>
    <!-- all: unset이 적용되어 모든 스타일이 사라진 제목 -->
    <button class="styled-btn">스타일된 버튼</button>
    <!-- 커스텀 스타일 버튼 -->
    <button class="reset-btn">all: revert 버튼</button>
    <!-- all: revert로 브라우저 기본 버튼으로 복원 -->
  </div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.all-demo { padding: 20px; background: #f1f5f9; border-radius: 8px; display: flex; flex-direction: column; gap: 12px; }
.styled-heading {
  color: #1e293b;
  font-size: 24px;
  font-weight: 700;
  padding: 12px;
  background: #dbeafe;
  border-left: 4px solid #3b82f6;
  border-radius: 4px;
}
.reset-heading {
  all: unset;            /* 모든 속성 초기화 */
  cursor: text;           /* 필요한 것만 다시 추가 */
}
.styled-btn {
  padding: 12px 24px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  align-self: flex-start;
}
.reset-btn {
  all: revert;           /* 브라우저 기본 버튼 스타일로 복원 */
  align-self: flex-start;
}
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 배울 핵심은 `.reset-heading` 과 `.reset-btn` 두 규칙뿐이다 — 각각 `all` 한 줄과 다시 줄 속성 한 줄이다.
- `all: unset` 은 제목에서 브라우저의 `h3` 꾸밈(큰 글자 · 굵기 · 여백)을 걷어내고 글자색 · 크기는 부모를 따르게 한다.
- `.reset-heading` 은 처음부터 `.styled-heading` 의 규칙을 받지 않으니, 파란 배경이 없는 것은 `all` 의 효과가 아니다.
- `all: revert` 는 작성자 꾸밈을 걷고 브라우저 기본 버튼 모양을 남긴다 — 구체적인 모양은 브라우저마다 다르다.
- 다시 줄 속성(`cursor` · `align-self`)은 같은 블록에서 반드시 `all` 뒤에 둔다 — 앞에 두면 `all` 이 덮는다.
- 데모의 제목은 flex 아이템이라 `display` 가 `inline` 이 되어도 블록처럼 한 줄을 차지할 것으로 읽힌다 (코드에서 읽은 것 — 렌더 실측 아님).

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

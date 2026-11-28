# css/visual/04 — caret-color — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 청록(`teal`) — 부모의 값이 상속된다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
캐럿은 `teal` 이다.
입력된 글자는 `#333` 이다.

**왜 그런가**
`caret-color` 는 상속되는 속성이다.
`input` 은 `caret-color` 를 따로 쓰지 않았으므로 부모 `.form` 의 `teal` 을 물려받는다.
`color: #333` 은 글자색을 정할 뿐, 물려받은 캐럿 색을 덮지 않는다.
근거: 2-summary 「동작 방식 (2)」.

### 2. 대개 파랑 — `auto` 는 보통 글자색을 따른다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
캐럿은 대개 파란색이다.

**왜 그런가**
`caret-color` 를 쓰지 않았으므로 기본값 `auto` 가 쓰인다.
원본은 `auto` 를 「브라우저 기본 색상, 보통 `currentColor`」라고 설명한다.
`currentColor` 는 이 요소의 `color` 인 파랑이다.
다만 「보통」이므로 정확한 색은 브라우저가 고른다.
근거: 2-summary 「동작 방식 (1)」 · 「구현 세부사항 대 언어 보장」.

### 3. 캐럿은 핑크, 글자는 거의 검정

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
캐럿은 `#f43f5e`(핑크)이고, 새로 쓴 글자는 `#111` 이다.

**왜 그런가**
원본 팁대로 `caret-color` 는 `contenteditable` 요소에도 적용된다.
`caret-color` 는 캐럿만 칠하고, 글자색은 `color` 가 따로 정한다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 1 · 6」.

### 4. 「입력 중」 신호를 한 색으로 묶어 일관성을 준다

캐럿은 포커스가 있을 때만 깜빡이므로, 캐럿과 `:focus` 테두리는 같은 순간에 함께 나타난다.
둘을 같은 브랜드 색으로 맞추면 「지금 여기에 입력 중」이라는 신호가 한 색으로 통일된다.
원본 팁의 「브랜드 컬러와 통일하면 디테일한 UX 향상」을 테두리까지 넓힌 것이다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 5」.

### 5. 캐럿 하나로는 포커스 위치를 알리기 부족하다

`outline: none` 은 브라우저가 그리던 기본 포커스 외곽선을 지운다.
그러면 키보드로 이동하는 사람은 지금 어느 칸에 있는지 알기 어려워진다.
캐럿은 가는 막대라 눈에 잘 안 띌 수 있어 그 역할을 혼자 맡기기 어렵다.
그래서 원본 정답 코드는 `:focus` 테두리 색 변화로 지운 외곽선을 대신한다.
근거: 2-summary 「어디서 틀리나 7」.

### 6. 바꿀 수 없다 — 캐럿의 색만 다룬다

`caret-color` 의 대상은 글을 쓸 자리에서 깜빡이는 캐럿뿐이다.
placeholder 의 색은 그대로이고, 마우스 포인터의 모양은 `cursor` 의 일이다.
근거: 2-summary 「어디서 틀리나 2 · 3」 · 「문법 — 형태와 규칙」.

### 7. 브라우저가 고르는 값이다

원본은 `auto` 를 「브라우저 기본 색상」이라 하고 「보통 `currentColor`」라고만 적는다.
「보통」이라는 말대로 하나로 못 박힌 색이 아니라 브라우저가 고른다.
그래서 「`auto` 는 늘 검정」처럼 외우면 틀린다.
근거: 2-summary 「어디서 틀리나 4」 · 「구현 세부사항 대 언어 보장」.

### 8. `auto` 면 따라가고, 고정 색이면 따라가지 않는다

`caret-color: auto`(기본값)이면 캐럿은 보통 `currentColor`, 곧 글자색을 따른다 — 글자색을 바꾸면 캐럿도 바뀐다.
`caret-color: #f43f5e` 처럼 색을 지정하면 캐럿은 그 색에 고정된다 — 글자색을 바꿔도 캐럿은 그대로다.
반대로 `caret-color: currentColor` 를 직접 쓰면 글자색을 따라가게 명시할 수도 있다.
근거: 2-summary 「동작 방식 (1)」 · 「언제 쓰고 언제 안 쓰나」.

## 실습 정답

### 실습 1. 브랜드 색 캐럿이 깜빡이는 입력 칸 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 한 줄 입력 칸 + 안내 문구 | `<input class="styled-input" type="text" placeholder="여기를 클릭하세요" />` |
| 2. 캐럿이 브랜드 색 | `.styled-input { caret-color: #f43f5e; }` |
| 3. 기본 포커스 외곽선 지우기 | `.styled-input { outline: none; }` |
| 4. 포커스 때 테두리를 캐럿과 같은 색으로 | `.styled-input:focus { border-color: #f43f5e; }` |
| 5. 테두리 색 변화를 부드럽게 | `.styled-input { transition: border-color 0.2s; }` |
| 6. 블록으로 가로 가운데 | `.styled-input { display: block; margin: 30px auto; }` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/visual/reference/visual--caret-color.html`

```html
<!DOCTYPE html>
<!-- 문서 타입 선언: HTML5 -->
<html lang="ko">
<!-- 문서 언어: 한국어 -->
<head>
  <meta charset="utf-8">
  <!-- 문자 인코딩: UTF-8 -->
  <title>caret-color - 텍스트 입력 커서(캐럿)의 색상을 설정합니다</title>
  <!--
    [시각 효과] caret-color
    설명: 텍스트 입력 커서(캐럿)의 색상을 설정합니다
    구문: caret-color: auto | <color>
    팁: 브랜드 컬러와 통일하면 디테일한 UX 향상. contenteditable 요소에도 적용 가능.
  -->
  <style>
    /* .styled-input: 브랜드 컬러 캐럿 입력 필드 */
    .styled-input {
      caret-color: #f43f5e;                       /* 입력 커서(깜빡이는 막대) 색을 핑크로 - 브랜드 색상 일관성 */
      border: 2px solid #e2e8f0;                  /* 연회색 테두리 */
      padding: 12px 16px;                         /* 위아래 12px, 좌우 16px */
      border-radius: 8px;                         /* 모서리 둥글게 */
      font-size: 16px;                            /* 글자 16px - 모바일 줌 방지 임계값 */
      width: 220px;                               /* 너비 220px */
      display: block;                             /* 블록 - 가로 중앙 정렬 가능 */
      margin: 30px auto;                          /* 위아래 30px, 가로 중앙 */
      outline: none;                              /* 기본 포커스 외곽선 제거 (커스텀 스타일로 대체) */
      transition: border-color 0.2s;              /* 테두리 색 변화 0.2초 부드럽게 */
    }
    /* .styled-input:focus: 포커스 시 테두리도 핑크 */
    .styled-input:focus {
      border-color: #f43f5e;                      /* 포커스 시 캐럿과 동일한 핑크로 - 일관성 */
    }
  </style>
</head>
<body>
  <!-- 브랜드 색상 캐럿 입력 데모 -->
  <input class="styled-input" type="text" placeholder="여기를 클릭하세요" />
  <!-- 클릭하면 핑크 캐럿이 깜빡임 -->

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.styled-input { caret-color: #f43f5e; border: 2px solid #e2e8f0; padding: 12px 16px; border-radius: 8px; font-size: 16px; width: 220px; display: block; margin: 30px auto; outline: none; transition: border-color 0.2s; }
.styled-input:focus { border-color: #f43f5e; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 이 주제의 핵심 줄은 `caret-color: #f43f5e;` 하나다 — 캐럿만 칠하고 글자색은 건드리지 않는다.
- `:focus` 의 `border-color` 를 캐럿과 같은 값으로 두어 「입력 중」 신호를 한 색으로 묶는다.
- `outline: none` 으로 기본 외곽선을 지운 대신, 테두리 색 변화가 포커스 표시를 맡는다.
- `transition` 은 `border-color` 만 대상으로 하므로 테두리 색 변화가 0.2초에 걸쳐 보간된다.
- `display: block` 이어야 `margin: 30px auto` 의 좌우 `auto` 로 가로 가운데 정렬이 된다.
- 클릭 뒤 보이는 모습(핑크 캐럿 · 핑크 테두리)은 코드에서 읽은 것이다 (코드에서 읽은 것 — 렌더 실측 아님).

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

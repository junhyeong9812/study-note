# css/responsive/14 — Responsive Table Patterns — 정리 (힌트)

> 출처 — study-site 항목 `css/responsive-table`(항목 데이터 `data/css/responsive.json`) · 정답 코드 study-practice `css/responsive/reference/responsive-table.html`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

## 한눈에 — 쉽게 말하면

**넓은 테이블을 좁은 화면에 넣는 일은 「긴 족자를 좁은 벽에 거는 일」이다.**
족자를 거는 방법은 세 가지다.
첫째, 족자를 그대로 두고 옆으로 밀어 가며 본다(가로 스크롤).
둘째, 족자를 잘라 한 장씩 카드로 만들어 위아래로 붙인다(카드형 변환).
셋째, 덜 중요한 부분을 접어서 감춘다(열 숨기기).
반응형 테이블도 똑같은 구조다.
화면이 좁아질 때 테이블을 밀어서 볼지, 쪼갤지, 줄일지를 고르는 문제다.

| 비유 | 실체 |
|---|---|
| 긴 족자 | 열이 많은 `<table>` |
| 좁은 벽 | 모바일 화면(뷰포트) |
| 옆으로 밀어 보기 | 래퍼에 `overflow-x: auto` |
| 잘라서 카드로 붙이기 | `display: block` + `td::before` + `data-label` |
| 접어서 감추기 | 우선순위 낮은 열에 `display: none` |
| 「옆에 더 있음」 표시 | 그라데이션 오버레이 |

```text
넓은 테이블 ─┬─ (1) 그대로 두고 래퍼가 가로 스크롤   [이름|직급|부서|입사…] →
             ├─ (2) 행마다 카드로 쪼갠다            ┌이름  김철수┐
             │                                      │직급  시니어│
             │                                      └──────────┘
             └─ (3) 덜 중요한 열을 숨긴다           [이름|직급|부서]
```

## 이 주제가 답하려는 질문

1. 화면보다 넓은 테이블을 페이지 전체를 넘치게 하지 않고 어떻게 보여 주나?
2. 표의 한 행을 「키: 값」 꼴의 카드로 바꾸려면 HTML 과 CSS 에 무엇이 필요한가?
3. 열이 너무 많을 때 어떤 열을 어떻게 감추나?
4. 가로 스크롤을 쓰면서 「옆에 더 있다」는 것을 사용자에게 어떻게 알리나?

## 동작 방식

### (1) 가로 스크롤 — 래퍼가 넘침을 떠안는다

**언제 쓰나** — 표의 꼴(열과 행의 격자)을 그대로 지켜야 하고, 가장 적은 코드로 끝내고 싶을 때 쓴다.
세 패턴 가운데 가장 간단하다.

```text
입력 코드
  .rt-scroll-wrap { overflow-x: auto; }
  .rt-table { width: 100%; min-width: 400px; }
  th, td { white-space: nowrap; }

무엇이 일어나나
  ① 래퍼 폭 = 300px (좁은 화면)
  ② 테이블 폭 = width 100% → 300px 이지만 min-width 400px 이 더 크다 → 400px
  ③ 셀 안 글자는 nowrap 이라 줄을 바꿔 폭을 줄이지 못한다
  ④ 테이블(400px)이 래퍼(300px)보다 100px 넓다 → 래퍼에 가로 스크롤이 생긴다

결과
  ┌── 래퍼 300px ──┐
  │이름|직급|부서|입│사일|이메일   ← 밀어서 본다
  └────────────────┘
  페이지 전체는 넘치지 않는다
```

① 테이블을 감싼 `div` 가 화면 폭을 따른다.
② `width: 100%` 는 부모 폭을 채우라는 뜻이지만 `min-width` 가 하한을 건다 — 둘이 부딪치면 하한이 이긴다.
③ `white-space: nowrap` 이 셀 글자의 줄바꿈을 막아, 브라우저가 열을 좁히는 길을 끊는다.
④ 넘친 만큼은 래퍼 안에서만 스크롤된다 — 넘침이 래퍼에 갇히므로 페이지 전체가 옆으로 흔들리지 않는다.

> **오버플로(overflow)** — 내용이 상자보다 커서 상자 밖으로 넘치는 상태다.\
> 예: 300px 래퍼 안의 400px 테이블은 100px 넘친다.

래퍼가 넓으면(예: 800px) `width: 100%` 가 800px 이 되어 `min-width` 보다 크다.
이때 테이블은 래퍼를 정확히 채우고 넘침이 없으므로 `overflow-x: auto` 는 스크롤바를 만들지 않는다.
`auto` 는 「넘칠 때만 스크롤」이라는 뜻이기 때문이다.

정답 코드의 래퍼에는 `-webkit-overflow-scrolling: touch;` 도 있다.
원본 주석은 이것을 「iOS 부드러운 관성 스크롤」이라 설명한다.
이 속성의 지위는 아래 「구현 세부사항 대 언어 보장」에서 따로 다룬다.

```html demo
<div style="width:260px; overflow-x:auto; border:1px solid #cbd5e1;">
  <table style="width:100%; min-width:400px; border-collapse:collapse;">
    <tr><th style="white-space:nowrap">이름</th><th style="white-space:nowrap">직급</th><th style="white-space:nowrap">부서</th><th style="white-space:nowrap">입사일</th><th style="white-space:nowrap">이메일</th></tr>
    <tr><td style="white-space:nowrap">김철수</td><td style="white-space:nowrap">시니어</td><td style="white-space:nowrap">개발</td><td style="white-space:nowrap">2020-03</td><td style="white-space:nowrap">kim@co.kr</td></tr>
  </table>
</div>
```

> **보이는 것** — 260px 상자 안에 테이블 앞부분만 보이고, 상자 안에서 옆으로 밀면 나머지 열이 나온다 (코드에서 읽은 것 — 렌더 실측 아님)

### (2) 스크롤 힌트 — 그라데이션 오버레이

**언제 쓰나** — 가로 스크롤 패턴을 쓸 때 함께 쓴다.
원본 팁은 「사용자가 스크롤 가능성을 인지하지 못할 수 있으므로 시각적 힌트를 추가한다」고 말한다.

```text
입력 코드
  래퍼에 position: relative
  래퍼::after 를 오른쪽 끝에 겹쳐, 투명 → 배경색 그라데이션

무엇이 일어나나
  ① 스크롤바가 눈에 잘 안 띄면 사용자는 오른쪽에 열이 더 있는지 모른다
  ② 오른쪽 끝 글자가 흐려지며 잘린 듯 보인다
  ③ 「잘려 있다 = 더 있다」는 신호가 된다

결과
  │이름|직급|부서|입░░│  ← 오른쪽이 흐려진다
```

① 문제의 뿌리는 「스크롤할 수 있음」이 화면에 드러나지 않는다는 점이다.
② 겹친 층(`::after`)이 끝부분을 덮어 흐리게 만든다.
③ 흐림은 내용이 계속된다는 시각 단서다.
겹친 층이 클릭과 터치를 가로채지 않도록 `pointer-events: none` 을 함께 주는 것이 보통이다.

> **오버레이(overlay)** — 다른 요소 위에 덮어 겹쳐 그리는 층이다.\
> 예: 래퍼 오른쪽 끝을 덮는 반투명 그라데이션 띠.

원본 예제 코드에는 이 힌트가 들어 있지 않다 — 팁으로만 나온다.

### (3) 카드형 변환 — 표의 칸을 블록으로 풀어 쌓는다

**언제 쓰나** — 모바일에서 한 행을 한눈에 읽게 하고 싶을 때 쓴다.
원본 라벨은 이것을 「모바일 최적」이라 부른다.

```text
입력 코드 (원본 코드 박스의 CSS)
  @media (max-width: 640px) {
    table, thead, tbody, th, td, tr { display: block; }
    td::before { content: attr(data-label); font-weight: bold; }
  }
  <td data-label="이름">김철수</td>

무엇이 일어나나
  ① 화면 폭이 640px 이하일 때만 블록 안 규칙이 켜진다
  ② 표 요소가 전부 블록이 된다 → 격자가 풀리고 위에서 아래로 쌓인다
     tr 하나 = 덩어리 하나, 그 안의 td 하나 = 한 줄
  ③ 각 td 앞에 ::before 가 생기고, 그 글자는 그 td 의 data-label 값이다

결과
  이름김철수
  직급시니어      ← 굵은 라벨 + 값, 한 줄씩
  ...
```

① `@media (max-width: 640px)` 는 뷰포트 폭이 640px 이하일 때만 안쪽 규칙을 적용하는 조건이다.
② 표 요소들은 원래 `table` · `table-row` · `table-cell` 같은 표 전용 표시 방식으로 격자를 이룬다 — 이것을 `block` 으로 바꾸면 격자 계산이 사라지고 보통 블록처럼 차례로 쌓인다.
③ `content: attr(data-label)` 은 그 요소의 `data-label` 속성 값을 글자로 꺼내 `::before` 의 내용으로 쓴다.

> **의사 요소(pseudo-element)** — HTML 에 없는 가상의 조각을 CSS 가 만들어 붙이는 것이다. `::before` 는 요소 내용의 맨 앞에 붙는다.\
> 예: `td::before { content: "★"; }` 는 모든 셀 글자 앞에 ★ 을 붙인다.

> **`data-*` 속성** — 개발자가 이름을 지어 요소에 붙이는 사용자 정의 속성이다.\
> 예: `<td data-label="부서">개발</td>`.

**왜 `data-label` 이 꼭 필요한가.**
블록으로 풀린 `td` 는 더는 자기 열의 `th` 와 짝을 이루지 않는다.
CSS 는 「같은 열 헤더의 글자」를 가져올 방법이 없고, 가져올 수 있는 것은 그 요소 자신의 속성뿐이다.
그래서 라벨을 **모든 `td` 에 하나씩 복사해 두어야** 한다.
`data-label` 이 없는 `td` 에서는 `attr(data-label)` 이 빈 문자열이 되어 라벨 없이 값만 나온다.

**`thead` 를 그대로 두면.**
원본 코드 박스의 CSS 는 `thead` 를 숨기지 않는다.
그러면 `thead` 의 `th` 들도 블록이 되어 표 맨 위에 「이름 / 직급 / 부서 …」가 한 줄씩 쌓인 목록으로 남는다.
라벨은 이미 각 `td` 앞에 붙으므로 이 헤더 목록은 겹치는 정보가 된다.
보통은 헤더를 화면에서 감추는 규칙을 하나 더 둔다.

**데모의 패턴 2 는 이 CSS 를 쓰지 않는다.**
데모 화면의 카드는 `<table>` 이 아니라 `div` 로 직접 짠 카드(`.rt-card` · `.rt-row` · `.rt-key`)다.
그리고 데모 CSS 에는 `@media` 가 없다.
그래서 데모에서는 화면 폭과 상관없이 패턴 1 의 표와 패턴 2 의 카드가 늘 나란히 보인다.
「화면이 좁아지면 표가 카드로 바뀐다」는 동작은 코드 박스에 글자로 적힌 CSS 의 몫이고, 데모가 그 변환을 실제로 해 보이지는 않는다.

데모 카드의 한 줄(`.rt-row`)은 `display: flex` + `justify-content: space-between` 이다.
자식이 둘(키 `span`, 값 `span`)이므로 남는 공간이 둘 사이로 들어가 키는 왼쪽 끝, 값은 오른쪽 끝에 붙는다.
`.rt-row:last-child` 는 카드의 마지막 줄에서만 아래 구분선을 지운다.

```html demo
<div style="border:1px solid #e2e8f0; padding:10px; width:220px;">
  <div style="display:flex; justify-content:space-between; border-bottom:1px solid #f1f5f9;"><b>이름</b><span>김철수</span></div>
  <div style="display:flex; justify-content:space-between;"><b>직급</b><span>시니어</span></div>
</div>
```

> **보이는 것** — 카드 안에 「이름 … 김철수」, 「직급 … 시니어」가 두 줄로, 키는 왼쪽 끝 값은 오른쪽 끝에 놓인다 (코드에서 읽은 것 — 렌더 실측 아님)

### (4) 열 숨기기 — 덜 중요한 열을 접는다

**언제 쓰나** — 열이 많고, 그중 일부는 모바일에서 없어도 될 때 쓴다.
원본 팁은 「우선순위가 낮은 열을 모바일에서 `display: none` 으로 숨기는 것도 방법」이라고 말한다.

```text
입력 코드
  @media (max-width: 640px) {
    th:nth-child(5), td:nth-child(5) { display: none; }
  }

무엇이 일어나나
  ① 좁은 화면에서만 규칙이 켜진다
  ② 다섯째 열의 헤더 칸과 데이터 칸이 함께 빠진다
  ③ 남은 네 열로 표가 다시 계산된다

결과
  [이름|직급|부서|입사일]     ← 이메일 열이 사라진다
```

① 넓은 화면에서는 모든 열이 그대로다.
② 헤더(`th`)와 데이터(`td`)를 **같이** 숨겨야 한다.
한쪽만 숨기면 남은 쪽이 칸 하나를 덜 갖게 되어 헤더와 값이 한 칸씩 어긋난다.
③ `display: none` 은 요소를 배치에서 아예 빼므로 그 열이 차지하던 폭도 사라진다.

원본 예제 코드에는 열 숨기기 코드가 없다 — 팁으로만 나온다.
다만 데모 카드가 표의 다섯 열 가운데 이메일을 빼고 네 항목만 보이는 것은 같은 생각(덜 중요한 정보는 모바일에서 뺀다)을 보여 준다.

## 문법 — 형태와 규칙

세 패턴을 한 파일에 모은 최소 예제다(직접 쓴 것이다).

```css
/* (1) 가로 스크롤 + (2) 힌트 */
.table-wrap { overflow-x: auto; position: relative; }
.table-wrap table { width: 100%; min-width: 400px; }
.table-wrap th, .table-wrap td { white-space: nowrap; }
.table-wrap::after {
  content: ""; position: absolute; top: 0; right: 0; bottom: 0; width: 24px;
  background: linear-gradient(to right, transparent, white);
  pointer-events: none;
}

@media (max-width: 640px) {
  /* (4) 열 숨기기 */
  th:nth-child(5), td:nth-child(5) { display: none; }
}
```

```css
/* (3) 카드형 변환 — (1) 과 함께 쓰지 않고 골라 쓴다 */
@media (max-width: 640px) {
  table, thead, tbody, th, td, tr { display: block; }
  td::before { content: attr(data-label); font-weight: bold; }
}
```

- 가로 스크롤은 테이블이 아니라 **테이블을 감싼 요소**에 `overflow-x` 를 준다.
- 테이블이 넘치게 하려면 「줄어들 수 없게」 만들어야 한다 — `min-width` 와 `white-space: nowrap` 이 그 역할이다.
- 카드형 변환은 HTML 쪽에 `data-label` 을 `td` 마다 적어야 완성된다.
- 미디어 쿼리 바깥의 규칙은 모든 화면에, 안쪽 규칙은 조건이 맞을 때만 적용된다.

정답 코드에 나오는 속성과 값을 모으면 다음과 같다.

| 속성 · 선택자 | 값 | 하는 일 |
|---|---|---|
| `overflow-x` | `auto` | 가로로 넘칠 때만 스크롤 수단을 만든다 |
| `-webkit-overflow-scrolling` | `touch` | 원본 주석: iOS 관성 스크롤 (지위는 아래 표 참고) |
| `width` / `min-width` | `100%` / `400px` | 부모를 채우되 400px 아래로는 줄지 않는다 |
| `border-collapse` | `collapse` | 이웃한 셀의 테두리를 한 줄로 합친다 |
| `white-space` | `nowrap` | 셀 글자의 줄바꿈을 막아 열 폭을 지킨다 |
| `white-space` | `pre` | 코드 박스에서 공백과 줄바꿈을 그대로 둔다 |
| `tr:hover td` | 배경 변경 | 마우스를 올린 행의 셀을 강조한다 |
| `justify-content` | `space-between` | 카드 줄에서 키는 왼쪽, 값은 오른쪽 끝 |
| `:last-child` | `border-bottom: none` | 마지막 줄의 구분선만 없앤다 |
| `@media (max-width: 640px)` | — | 640px 이하에서만 안쪽 규칙을 켠다 |
| `display` | `block` | 표 요소를 보통 블록으로 바꿔 격자를 푼다 |
| `content` | `attr(data-label)` | 속성 값을 의사 요소의 글자로 쓴다 |
| `display` | `none` | 열(또는 헤더)을 배치에서 뺀다 |

## 어디서 틀리나

### 1. 테이블에 `overflow-x` 를 준다
넘침을 가두는 것은 감싼 상자다.
`overflow-x: auto` 는 테이블을 감싼 래퍼에 둔다.

### 2. 래퍼만 두고 테이블이 줄어든다
래퍼가 있어도 테이블이 줄어들 수 있으면 넘침이 생기지 않는다.
브라우저는 셀 글자를 줄바꿈해 열을 좁히고 표를 화면에 우겨 넣는다.
`min-width` 와 `white-space: nowrap` 으로 줄어들 길을 막아야 스크롤 패턴이 성립한다.

### 3. 스크롤할 수 있다는 것을 사용자가 모른다
원본 팁: 가로 스크롤이 가장 간단하지만 사용자가 스크롤 가능성을 인지하지 못할 수 있다.
그래서 그라데이션 오버레이 같은 시각 힌트를 덧붙인다.
오버레이가 터치를 막지 않도록 `pointer-events: none` 을 챙긴다.

### 4. 카드형 변환에서 `data-label` 을 빼먹는다
원본 팁: 카드형 변환은 `data-label` 속성과 `td::before` 의사 요소를 조합해 구현한다.
`data-label` 이 없는 `td` 는 라벨 없이 값만 나온다.
라벨 글자는 HTML 의 모든 `td` 에 복사해야 하므로, 헤더를 고치면 `data-label` 도 함께 고쳐야 한다.

### 5. 블록으로 푼 뒤 `thead` 를 그대로 둔다
원본 코드 박스의 CSS 만으로는 헤더 칸들이 맨 위에 세로 목록으로 남는다.
각 `td` 앞에 이미 라벨이 붙으니 헤더는 감추는 편이 보통이다.

### 6. 열을 숨길 때 `th` 와 `td` 중 하나만 숨긴다
원본 팁: 열이 많으면 우선순위 낮은 열을 모바일에서 `display: none` 으로 숨긴다.
헤더와 데이터 칸을 같이 숨기지 않으면 열이 어긋난다.

### 7. 데모가 화면 폭에 따라 바뀐다고 기대한다
데모 CSS 에는 미디어 쿼리가 없고 패턴 2 는 `div` 로 짠 카드다.
변환 CSS 는 코드 박스 안의 글자일 뿐 적용되지 않는다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `overflow-x: auto` 는 넘칠 때만 스크롤 수단을 만든다 | CSS 명세 |
| 스크롤바가 늘 화면에 보이는지 | 브라우저 · 운영체제 (스크롤할 때만 보이는 환경이 있다 — 그래서 힌트가 필요하다) (확인 필요) |
| `-webkit-overflow-scrolling: touch` 가 iOS 관성 스크롤을 켠다 | 원본 주석의 주장. `-webkit-` 접두사가 붙은 비표준 속성이라 WebKit(iOS Safari) 구현의 일이다. 최신 iOS 에서는 관성 스크롤이 기본이라 이 선언이 효과가 없다는 말이 있다 (확인 필요) |
| `min-width` 가 `width` 와 부딪치면 `min-width` 가 이긴다 | CSS 명세 |
| `attr()` 로 가리킨 속성이 없으면 빈 문자열이 된다 | CSS 명세 (확인 필요) |
| 표 요소에 `display: block` 을 주면 격자가 풀린다 | CSS 명세 (표시 방식이 바뀐다) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 열끼리 비교가 중요한 표(가격표 · 시간표) | 가로 스크롤 + 그라데이션 힌트 | 카드형 변환 (열 비교가 어려워진다) |
| 행 하나가 한 대상(사람 · 주문)이고 따로 읽힌다 | 카드형 변환 | 좁은 화면에서 표를 억지로 줄여 글자가 여러 줄로 쪼개지게 두기 |
| 열이 많고 몇 개는 모바일에 없어도 된다 | 열 숨기기 (`th` · `td` 함께) | 핵심 열 숨기기 |
| 가장 빨리 끝내야 한다 | 가로 스크롤 | `data-label` 을 손으로 모든 칸에 다는 일 |

## 핵심 문장

1. **가로 스크롤은 넘침을 래퍼에 가두는 방법이다** — 래퍼에 `overflow-x: auto`, 테이블에는 줄어들지 않게 `min-width` 와 `nowrap`.
2. **스크롤은 눈에 안 띌 수 있다** — 그라데이션 오버레이로 「옆에 더 있음」을 알린다.
3. **카드형 변환은 표를 블록으로 풀고 라벨을 의사 요소로 붙인다** — 라벨은 `td` 마다 `data-label` 로 들고 있어야 한다.
4. **열 숨기기는 `display: none` 으로 헤더와 데이터를 함께 뺀다.**
5. **원본 데모는 패턴을 나란히 보여 줄 뿐** 화면 폭에 따라 바뀌지 않는다 — 변환은 코드 박스의 CSS 가 맡는다.

## 관련 자료

- 원본에 관련 항목이 없다.
- 원본: study-site 항목 데이터 `data/css/responsive.json` 의 `responsive-table`

## 용어 풀이

- **반응형 테이블** — 화면 폭에 맞춰 보여 주는 방식을 바꾸는 표.
- **뷰포트** — 브라우저에서 페이지가 그려지는 보이는 영역.
- **래퍼(wrapper)** — 어떤 요소를 감싸는 바깥 상자.
- **오버플로(overflow)** — 내용이 상자보다 커서 넘치는 상태.
- **`overflow-x`** — 가로 넘침을 어떻게 처리할지 정하는 속성.
- **`min-width`** — 요소 폭의 하한.
- **`white-space: nowrap`** — 글자를 줄바꿈하지 않게 하는 값.
- **`border-collapse: collapse`** — 이웃한 셀 테두리를 하나로 합치는 값.
- **미디어 쿼리** — 화면 폭 같은 조건이 맞을 때만 규칙을 켜는 `@media` 블록.
- **의사 요소** — CSS 가 만들어 붙이는 가상 조각(`::before` · `::after`).
- **`data-*` 속성** — 개발자가 이름을 지어 붙이는 사용자 정의 속성.
- **`attr()`** — 요소의 속성 값을 CSS 안으로 꺼내는 함수.
- **오버레이** — 요소 위에 덮어 그리는 층.
- **`pointer-events: none`** — 그 요소가 클릭 · 터치를 받지 않고 아래로 흘려보내게 하는 값.
- **`:last-child`** — 부모의 마지막 자식에만 맞는 선택자.
- **`justify-content: space-between`** — flex 아이템을 양 끝에 붙이고 남는 공간을 사이에 나누는 값.

## 더 들어가면

- 표 요소에 `display: block` 을 주면 일부 브라우저 · 스크린리더 조합에서 표의 의미(행 · 열 관계)가 사라진다는 보고가 있다. 이를 메우려고 `role="table"` · `role="row"` · `role="cell"` 을 명시하기도 한다 (확인 필요).
- 카드형 변환에서 헤더를 감출 때 `display: none` 대신 화면에서만 감추고 스크린리더에는 남기는 「시각적 숨김」 기법을 쓰기도 한다 (확인 필요).
- 스크롤 그림자 힌트를 `background-attachment: local` 을 이용해 실제 스크롤 위치에 따라 나타났다 사라지게 만드는 기법이 있다 (확인 필요).
- 첫 열(이름)을 `position: sticky; left: 0` 으로 고정해 가로 스크롤 중에도 어느 행인지 보이게 하는 방법이 있다 (확인 필요).
- 미디어 쿼리 대신 컨테이너 쿼리로 「테이블이 놓인 상자의 폭」에 맞춰 바꾸는 방법도 있다 (확인 필요).

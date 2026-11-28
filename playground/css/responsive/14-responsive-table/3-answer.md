# css/responsive/14 — Responsive Table Patterns — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 테이블은 400px, 래퍼 안에 가로 스크롤이 생긴다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
테이블 폭은 400px 이고, 300px 래퍼 안에서 100px 만큼 넘쳐 래퍼에 가로 스크롤이 생긴다.
페이지 전체가 옆으로 넘치지는 않는다.

**왜 그런가**
`width: 100%` 는 300px 을 원하지만 `min-width: 400px` 이 하한을 걸고, 둘이 부딪치면 하한이 이긴다.
`nowrap` 때문에 셀 글자가 줄바꿈으로 폭을 줄이지도 못한다.
넘침은 `overflow-x: auto` 를 가진 래퍼에 갇힌다.
근거: 2-summary 「동작 방식 (1)」.

### 2. 테이블은 800px, 스크롤바는 생기지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
테이블 폭은 래퍼를 채운 800px 이고, 넘침이 없으므로 가로 스크롤바가 생기지 않는다.

**왜 그런가**
`width: 100%` 가 800px 로 `min-width` 400px 보다 크므로 하한이 끼어들 일이 없다.
`overflow-x: auto` 는 넘칠 때만 스크롤 수단을 만든다.
근거: 2-summary 「동작 방식 (1)」 · 「구현 세부사항 대 언어 보장」.

### 3. 첫 칸은 굵은 「이름」 + 김철수, 둘째 칸은 라벨 없이 「시니어」

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
두 `td` 는 블록이 되어 위아래 두 줄로 쌓인다.
첫 줄은 `::before` 가 붙여 준 굵은 「이름」 바로 뒤에 「김철수」가 온다.
둘째 줄은 `data-label` 이 없어 `attr(data-label)` 이 빈 문자열이 되므로 「시니어」만 나온다.

**왜 그런가**
375px 은 `max-width: 640px` 조건을 만족해 블록 규칙이 켜진다.
`content: attr(data-label)` 은 그 `td` 자신의 속성만 읽는다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 4」.

### 4. 스크롤할 수 있다는 사실이 화면에 잘 드러나지 않기 때문이다

스크롤바가 눈에 띄지 않으면 사용자는 오른쪽에 열이 더 있다는 것을 모르고 지나칠 수 있다.
끝부분을 흐리게 덮는 그라데이션은 「잘려 있다 = 더 있다」는 단서가 된다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 3」 (원본 팁).

### 5. 블록으로 풀린 `td` 는 `th` 와 짝을 잃고, CSS 는 자기 속성만 꺼낼 수 있기 때문이다

`display: block` 으로 격자가 풀리면 `td` 와 같은 열의 `th` 사이의 대응이 사라진다.
`attr()` 은 그 요소 자신의 속성 값만 가져올 수 있어 다른 요소(헤더)의 글자를 끌어올 길이 없다.
그래서 라벨을 모든 `td` 에 `data-label` 로 복사해 둔다.
근거: 2-summary 「동작 방식 (3)」 「왜 `data-label` 이 꼭 필요한가」.

### 6. 헤더와 값이 한 칸씩 어긋난다

헤더 줄은 네 칸, 데이터 줄은 다섯 칸이 되어 열의 짝이 맞지 않는다.
숨긴 열 뒤쪽의 값은 엉뚱한 헤더 아래에 놓이거나 헤더 없는 칸이 생긴다.
`th` 와 `td` 를 함께 숨겨야 한다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 6」.

### 7. 바뀌지 않는다 — 데모에는 미디어 쿼리가 없고 카드는 `div` 로 짠 것이다

데모 CSS 어디에도 `@media` 가 없어 화면 폭이 규칙을 바꾸지 않는다.
패턴 2 의 카드는 `<table>` 이 아니라 `.rt-card` · `.rt-row` 같은 `div` 로 직접 만든 것이다.
표를 카드로 바꾸는 CSS 는 코드 박스 안에 글자로만 적혀 있어 적용되지 않는다.
그래서 두 패턴은 어떤 폭에서도 늘 나란히 보인다.
근거: 2-summary 「동작 방식 (3)」 「데모의 패턴 2 는 이 CSS 를 쓰지 않는다」 · 「어디서 틀리나 7」.

### 8. 표 맨 위에 헤더 칸들이 한 줄씩 쌓인 목록으로 남는다

그 CSS 는 `thead` · `th` 에도 `display: block` 만 주고 숨기지는 않는다.
그래서 「이름 / 직급 / 부서 / 입사일 / 이메일」이 맨 위에 세로로 쌓인다.
각 `td` 앞에 이미 라벨이 붙으므로 이 목록은 겹치는 정보이고, 보통은 헤더를 감추는 규칙을 더한다.
근거: 2-summary 「동작 방식 (3)」 「`thead` 를 그대로 두면」 · 「어디서 틀리나 5」.

### 9. `display: flex` + `justify-content: space-between` 이다

`.rt-row` 는 flex 컨테이너이고 자식은 키 `span` 과 값 `span` 둘이다.
`space-between` 은 첫 아이템을 시작 끝, 마지막 아이템을 끝 쪽 끝에 붙이고 남는 공간을 아이템 사이에 나눈다.
아이템이 둘뿐이라 남는 공간이 전부 둘 사이에 들어가, 키는 왼쪽 끝 값은 오른쪽 끝에 놓인다.
근거: 2-summary 「동작 방식 (3)」 · 「문법 — 형태와 규칙」 표.

## 실습 정답

### 실습 1. 반응형 테이블 패턴 데모 페이지 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 세 덩어리를 세로로 쌓기 | `.rt-demo { display: flex; flex-direction: column; gap: 14px; }` |
| 2. 섹션마다 라벨 | `<div class="rt-label">패턴 1: …</div>` · `<div class="rt-label">패턴 2: …</div>` |
| 3. 넘칠 때만 가로 스크롤하는 래퍼 | `<div class="rt-scroll-wrap">` + `.rt-scroll-wrap { overflow-x: auto; }` |
| 4. iOS 관성 스크롤 접두사 | `.rt-scroll-wrap { -webkit-overflow-scrolling: touch; }` |
| 5. 부모 폭 채우기 + 최소 폭 | `.rt-table { width: 100%; min-width: 400px; }` |
| 6. 셀 테두리 합치기 | `.rt-table { border-collapse: collapse; }` |
| 7. 줄바꿈 금지 · 헤더 왼쪽 정렬 | `.rt-table th { text-align: left; white-space: nowrap; }` · `.rt-table td { white-space: nowrap; }` |
| 8. 다섯 열 두 행 | `<thead>` 의 `th` 다섯 개 · `<tbody>` 의 `tr` 두 개 |
| 9. 행 hover 강조 | `.rt-table tr:hover td { background: #f1f5f9; }` |
| 10. 카드 세로 쌓기 | `.rt-cards { display: flex; flex-direction: column; gap: 8px; }` |
| 11. 카드 = 한 사람, 네 항목 | `.rt-card` 두 개, 각 안에 `.rt-row` 네 개(이름 · 직급 · 부서 · 입사일) |
| 12. 키 왼쪽 끝 · 값 오른쪽 끝 | `.rt-row { display: flex; justify-content: space-between; }` |
| 13. 마지막 줄만 구분선 없음 | `.rt-row:last-child { border-bottom: none; }` |
| 14. 코드 박스에 변환 CSS 글자 | `<div class="rt-code"><code>/* 패턴 1: 가로 스크롤 */ … }</code></div>` |
| 15. 공백 · 줄바꿈 보존, 블록 | `.rt-code code { white-space: pre; display: block; }` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/responsive/reference/responsive-table.html`

```html
<!-- DOCTYPE: HTML5 -->
<!DOCTYPE html>
<!-- 한국어 문서 -->
<html lang="ko">
<!-- 메타데이터 -->
<head>
<!-- UTF-8 -->
<meta charset="utf-8">
<!-- 탭 제목 -->
<title>Responsive Table Patterns - 모바일에서 넓은 테이블을 처리하는 여러 패턴: 가로 스크롤, 카드형 변환, 열 숨기기 등.</title>
<!--
  [반응형 디자인] Responsive Table Patterns
  설명: 모바일에서 넓은 테이블을 처리하는 여러 패턴: 가로 스크롤, 카드형 변환, 열 숨기기 등.

  팁: 가로 스크롤이 가장 간단하지만 사용자가 스크롤 가능성을 인지하지 못할 수 있으므로 시각적 힌트(그라데이션 오버레이)를 추가한다. 카드형 변환은 data-label 속성과 td::before 의사 요소를 조합하여 구현한다. 열이 많으면 우선순위가 낮은 열을 모바일에서 display: none으로 숨기는 것도 방법이다.
-->
<style>
  /* .rt-demo: 데모 루트 */
  .rt-demo {
    font-family: system-ui, sans-serif;   /* 시스템 폰트 */
    display: flex;                        /* flex */
    flex-direction: column;               /* 세로 정렬 */
    gap: 14px;                            /* 섹션 간격 */
  }
  /* .rt-section: 섹션 박스 */
  .rt-section {
    background: #f8fafc;                  /* 옅은 배경 */
    border-radius: 8px;                   /* 둥근 모서리 */
    padding: 12px;                        /* 안쪽 여백 */
  }
  /* .rt-label: 섹션 라벨 */
  .rt-label {
    font-size: 12px;                      /* 작은 폰트 */
    font-weight: 700;                     /* 굵게 */
    color: #475569;                       /* 회색 */
    margin-bottom: 8px;                   /* 콘텐츠와 간격 */
  }
  /* .rt-scroll-wrap: 가로 스크롤 래퍼(테이블이 넘치면 스크롤) */
  .rt-scroll-wrap {
    overflow-x: auto;                     /* 가로 오버플로우 시 스크롤 */
    -webkit-overflow-scrolling: touch;    /* iOS 부드러운 관성 스크롤 */
    border-radius: 6px;                   /* 둥근 모서리 */
  }
  /* .rt-table: 테이블 - 모바일에서 가로 스크롤되도록 min-width 지정 */
  .rt-table {
    width: 100%;                          /* 부모 폭 채움 */
    min-width: 400px;                     /* 최소 폭 - 모바일에서 가로 스크롤 발생 트리거 */
    border-collapse: collapse;            /* 인접 셀 보더 합치기 */
    font-size: 12px;                      /* 작은 폰트 */
  }
  /* .rt-table th: 헤더 셀 */
  .rt-table th {
    background: #1e293b;                  /* 어두운 배경 */
    color: white;                         /* 흰 글자 */
    padding: 8px 12px;                    /* 셀 패딩 */
    text-align: left;                     /* 좌측 정렬 */
    white-space: nowrap;                  /* 줄바꿈 금지 - 가로 폭 유지 */
  }
  /* .rt-table td: 데이터 셀 */
  .rt-table td {
    padding: 8px 12px;                    /* 셀 패딩 */
    border-bottom: 1px solid #e2e8f0;     /* 행 구분선 */
    white-space: nowrap;                  /* 줄바꿈 금지 */
  }
  /* .rt-table tr:hover td: 행 호버 강조 */
  .rt-table tr:hover td {
    background: #f1f5f9;                  /* 호버 시 옅은 배경 */
  }
  /* .rt-cards: 카드형 변환 컨테이너(모바일 최적) */
  .rt-cards {
    display: flex;                        /* flex */
    flex-direction: column;               /* 세로 정렬 */
    gap: 8px;                             /* 카드 간격 */
  }
  /* .rt-card: 한 행을 나타내는 카드 */
  .rt-card {
    background: white;                    /* 흰 배경 */
    border: 1px solid #e2e8f0;            /* 옅은 보더 */
    border-radius: 8px;                   /* 둥근 모서리 */
    padding: 10px;                        /* 내부 여백 */
  }
  /* .rt-row: 카드 안의 한 항목(키-값 한 쌍) */
  .rt-row {
    display: flex;                        /* flex */
    justify-content: space-between;       /* 키는 좌측, 값은 우측 끝 */
    padding: 4px 0;                       /* 위아래 패딩 */
    font-size: 12px;                      /* 작은 폰트 */
    border-bottom: 1px solid #f1f5f9;     /* 행 구분선 */
  }
  /* .rt-row:last-child: 마지막 행은 구분선 제거 */
  .rt-row:last-child {
    border-bottom: none;                  /* 보더 제거 */
  }
  /* .rt-key: 항목 키(왼쪽) */
  .rt-key {
    font-weight: 600;                     /* 약간 굵게 */
    color: #64748b;                       /* 회색 */
  }
  /* .rt-code: 코드 박스(다크) */
  .rt-code {
    background: #1e293b;                  /* 어두운 배경 */
    border-radius: 8px;                   /* 둥근 모서리 */
    padding: 14px;                        /* 내부 여백 */
  }
  /* .rt-code code: 코드 텍스트 */
  .rt-code code {
    font-size: 11px;                      /* 작은 폰트 */
    color: #e2e8f0;                       /* 밝은 글자 */
    white-space: pre;                     /* 공백/개행 보존 */
    line-height: 1.5;                     /* 줄 간격 */
    display: block;                       /* 블록 */
  }
</style>
</head>
<body>
<!-- 데모 루트 -->
<div class="rt-demo">
  <!-- 섹션 1: 가로 스크롤 패턴 -->
  <div class="rt-section">
    <!-- 라벨 -->
    <div class="rt-label">패턴 1: 가로 스크롤 (가장 간단)</div>
    <!-- 스크롤 래퍼 -->
    <div class="rt-scroll-wrap">
      <!-- 테이블 -->
      <table class="rt-table">
        <!-- 헤더 -->
        <thead>
          <!-- 헤더 행 -->
          <tr>
            <!-- 컬럼: 이름 -->
            <th>이름</th>
            <!-- 컬럼: 직급 -->
            <th>직급</th>
            <!-- 컬럼: 부서 -->
            <th>부서</th>
            <!-- 컬럼: 입사일 -->
            <th>입사일</th>
            <!-- 컬럼: 이메일 -->
            <th>이메일</th>
          </tr>
        </thead>
        <!-- 본문 -->
        <tbody>
          <!-- 데이터 행 1 -->
          <tr>
            <!-- 이름 -->
            <td>김철수</td>
            <!-- 직급 -->
            <td>시니어</td>
            <!-- 부서 -->
            <td>개발</td>
            <!-- 입사일 -->
            <td>2020-03</td>
            <!-- 이메일 -->
            <td>kim@co.kr</td>
          </tr>
          <!-- 데이터 행 2 -->
          <tr>
            <!-- 이름 -->
            <td>이영희</td>
            <!-- 직급 -->
            <td>주니어</td>
            <!-- 부서 -->
            <td>디자인</td>
            <!-- 입사일 -->
            <td>2023-01</td>
            <!-- 이메일 -->
            <td>lee@co.kr</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
  <!-- 섹션 2: 카드형 변환 패턴 -->
  <div class="rt-section">
    <!-- 라벨 -->
    <div class="rt-label">패턴 2: 카드형 변환 (모바일 최적)</div>
    <!-- 카드 목록 -->
    <div class="rt-cards">
      <!-- 카드 1: 김철수 -->
      <div class="rt-card">
        <!-- 이름 행 -->
        <div class="rt-row"><span class="rt-key">이름</span><span>김철수</span></div>
        <!-- 직급 행 -->
        <div class="rt-row"><span class="rt-key">직급</span><span>시니어</span></div>
        <!-- 부서 행 -->
        <div class="rt-row"><span class="rt-key">부서</span><span>개발</span></div>
        <!-- 입사일 행 -->
        <div class="rt-row"><span class="rt-key">입사일</span><span>2020-03</span></div>
      </div>
      <!-- 카드 2: 이영희 -->
      <div class="rt-card">
        <!-- 이름 행 -->
        <div class="rt-row"><span class="rt-key">이름</span><span>이영희</span></div>
        <!-- 직급 행 -->
        <div class="rt-row"><span class="rt-key">직급</span><span>주니어</span></div>
        <!-- 부서 행 -->
        <div class="rt-row"><span class="rt-key">부서</span><span>디자인</span></div>
        <!-- 입사일 행 -->
        <div class="rt-row"><span class="rt-key">입사일</span><span>2023-01</span></div>
      </div>
    </div>
  </div>
  <!-- 코드 예시 박스 -->
  <div class="rt-code">
    <code>/* 패턴 1: 가로 스크롤 */
.table-wrap {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

/* 패턴 2: 카드형 변환 */
@media (max-width: 640px) {
  table, thead, tbody, th, td, tr {
    display: block;
  }
  td::before {
    content: attr(data-label);
    font-weight: bold;
  }
}</code>
  </div>
</div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.rt-demo { font-family: system-ui, sans-serif; display: flex; flex-direction: column; gap: 14px; }
.rt-section { background: #f8fafc; border-radius: 8px; padding: 12px; }
.rt-label { font-size: 12px; font-weight: 700; color: #475569; margin-bottom: 8px; }
.rt-scroll-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; border-radius: 6px; }
.rt-table { width: 100%; min-width: 400px; border-collapse: collapse; font-size: 12px; }
.rt-table th { background: #1e293b; color: white; padding: 8px 12px; text-align: left; white-space: nowrap; }
.rt-table td { padding: 8px 12px; border-bottom: 1px solid #e2e8f0; white-space: nowrap; }
.rt-table tr:hover td { background: #f1f5f9; }
.rt-cards { display: flex; flex-direction: column; gap: 8px; }
.rt-card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; }
.rt-row { display: flex; justify-content: space-between; padding: 4px 0; font-size: 12px; border-bottom: 1px solid #f1f5f9; }
.rt-row:last-child { border-bottom: none; }
.rt-key { font-weight: 600; color: #64748b; }
.rt-code { background: #1e293b; border-radius: 8px; padding: 14px; }
.rt-code code { font-size: 11px; color: #e2e8f0; white-space: pre; line-height: 1.5; display: block; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 가로 스크롤은 래퍼의 `overflow-x: auto` 와 테이블이 줄어들지 못하게 하는 `min-width` · `nowrap` 이 짝을 이뤄야 성립한다.
- `tr:hover td` 처럼 행에 hover 를 걸고 배경은 칸(`td`)에 칠한다.
- 데모의 카드는 `div` 로 직접 짠 것이라, 표를 카드로 바꾸는 CSS 는 코드 박스에 글자로만 있다.
- 카드 한 줄은 flex 의 `space-between` 으로 키와 값을 양 끝에 나누고, `:last-child` 로 마지막 구분선만 지운다.
- 코드 박스의 `white-space: pre` 가 없으면 CSS 글자의 줄바꿈과 들여쓰기가 한 줄로 뭉개진다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

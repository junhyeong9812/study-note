# css/responsive/14 — Responsive Table Patterns — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 300px 래퍼 안의 테이블 (예측)

```css
/* 질문용 발췌 */
.wrap { width: 300px; overflow-x: auto; }
.wrap table { width: 100%; min-width: 400px; }
.wrap th, .wrap td { white-space: nowrap; }
```

- 테이블의 실제 폭은 몇 px 이 되고, 래퍼에는 무엇이 생기는가?

### 2. 래퍼를 800px 로 넓히면 (예측)

```css
/* 질문용 발췌 */
.wrap { width: 800px; overflow-x: auto; }
.wrap table { width: 100%; min-width: 400px; }
```

- 테이블 폭은 몇 px 이고, 가로 스크롤바는 생기는가?

### 3. 640px 이하 화면에서 `data-label` 이 빠진 칸 (예측)

```html
<!-- 질문용 발췌 — 아래 CSS 가 적용된 상태, 뷰포트 375px -->
<style>
@media (max-width: 640px) {
  table, thead, tbody, th, td, tr { display: block; }
  td::before { content: attr(data-label); font-weight: bold; }
}
</style>
<tr><td data-label="이름">김철수</td><td>시니어</td></tr>
```

- 두 `td` 는 각각 화면에 어떤 글자로 나타나는가?

### 4. 가로 스크롤에 그라데이션 오버레이를 덧붙이는 까닭 (왜)
- 스크롤만으로도 내용을 다 볼 수 있는데 왜 시각 힌트를 따로 넣는가?

### 5. 라벨을 `td` 마다 `data-label` 로 복사해 두는 까닭 (왜)
- 같은 열의 `th` 에 이미 라벨이 있는데 왜 CSS 가 그것을 쓰지 못하는가?

### 6. 열을 숨길 때 헤더 칸만 숨기면 (경계)
- 다섯째 열의 `th` 만 `display: none` 으로 숨기고 `td` 는 두면 표는 어떻게 깨지는가?

### 7. 원본 데모를 넓은 화면에서 열었을 때의 패턴 2 (경계)
- 데모 화면에서 패턴 2 의 카드가 화면 폭에 따라 표로 바뀌는가, 그 판단의 근거는 무엇인가?

### 8. 원본 코드 박스의 변환 CSS 에서 `thead` 의 운명 (경계)
- 그 CSS 만 적용하면 640px 이하에서 헤더 칸들은 어디에 어떤 모양으로 남는가?

### 9. 카드 한 줄의 키와 값을 양 끝에 붙이는 방법 (연결)
- `.rt-row` 의 어떤 flex 설정이 키를 왼쪽 끝, 값을 오른쪽 끝에 두며, 그것은 어떻게 동작하는가?

## 실습

### 실습 1. 반응형 테이블 패턴 데모 페이지 만들기

**만들 것** — 같은 직원 데이터를 「가로 스크롤 표」와 「카드 목록」 두 패턴으로 나란히 보여 주고, 카드형 변환 CSS 를 코드 박스에 글자로 보여 주는 한 장짜리 HTML 페이지.

**요구 조건**

1단계 — 큰 배치
1. 루트 `.rt-demo` 는 세 덩어리(섹션 1 · 섹션 2 · 코드 박스)를 위에서 아래로 쌓는다.
2. 두 섹션은 맨 위에 패턴 이름 라벨을 단다(「패턴 1: 가로 스크롤 (가장 간단)」, 「패턴 2: 카드형 변환 (모바일 최적)」).

2단계 — 패턴 1: 가로 스크롤
3. 테이블을 스크롤 래퍼 `.rt-scroll-wrap` 로 감싸고, 래퍼는 가로로 넘칠 때만 스크롤된다.
4. 래퍼에 iOS 관성 스크롤용 접두사 속성을 선언한다.
5. 테이블은 부모 폭을 채우되 최소 폭(시작 코드 주석의 값)을 두어, 래퍼가 좁으면 래퍼 안에서 넘친다.
6. 이웃한 셀의 테두리를 하나로 합친다.
7. 헤더 칸과 데이터 칸 모두 글자가 줄바꿈되지 않고, 헤더 칸 글자는 왼쪽 정렬이다.
8. 표는 이름 · 직급 · 부서 · 입사일 · 이메일 다섯 열, 김철수 · 이영희 두 행이다.
9. 행에 마우스를 올리면 그 행의 데이터 칸 배경이 바뀐다.

3단계 — 패턴 2: 카드 목록
10. 카드 목록 `.rt-cards` 는 카드를 위에서 아래로 쌓는다.
11. 카드 하나는 한 사람이고, 이름 · 직급 · 부서 · 입사일 네 항목(이메일 제외)을 한 줄씩 담는다.
12. 한 줄 `.rt-row` 안에서 키(`.rt-key`)는 왼쪽 끝, 값은 오른쪽 끝에 놓인다.
13. 카드의 마지막 줄에서만 아래 구분선이 없다.

4단계 — 코드 박스
14. 코드 박스 `.rt-code` 안 `code` 에 가로 스크롤 CSS(`.table-wrap`)와 640px 이하 카드형 변환 CSS(`display: block` · `td::before` · `attr(data-label)`)를 글자로 보여 준다.
15. 코드 글자는 공백과 줄바꿈이 그대로 보존되고, 블록으로 놓인다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>Responsive Table Patterns 연습</title>
<style>
  .rt-demo {
    font-family: system-ui, sans-serif;
    gap: 14px;
    /* TODO: 자식들을 세로로 쌓는 flex 설정 */
  }
  .rt-section { background: #f8fafc; border-radius: 8px; padding: 12px; }
  .rt-label { font-size: 12px; font-weight: 700; color: #475569; margin-bottom: 8px; }
  .rt-scroll-wrap {
    border-radius: 6px;
    /* TODO: 가로로 넘칠 때만 스크롤 */
    /* TODO: iOS 관성 스크롤 접두사 속성 */
  }
  .rt-table {
    font-size: 12px;
    /* TODO: 부모 폭 채우기, 최소 폭 400px, 셀 테두리 합치기 */
  }
  .rt-table th {
    background: #1e293b; color: white; padding: 8px 12px;
    /* TODO: 왼쪽 정렬, 줄바꿈 금지 */
  }
  .rt-table td {
    padding: 8px 12px; border-bottom: 1px solid #e2e8f0;
    /* TODO: 줄바꿈 금지 */
  }
  /* TODO: 행에 마우스를 올리면 그 행의 td 배경을 #f1f5f9 로 바꾸는 규칙 */
  .rt-cards {
    gap: 8px;
    /* TODO: 카드를 세로로 쌓는 flex 설정 */
  }
  .rt-card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; }
  .rt-row {
    padding: 4px 0; font-size: 12px; border-bottom: 1px solid #f1f5f9;
    /* TODO: 키는 왼쪽 끝, 값은 오른쪽 끝 */
  }
  /* TODO: 마지막 .rt-row 의 아래 구분선 없애기 */
  .rt-key { font-weight: 600; color: #64748b; }
  .rt-code { background: #1e293b; border-radius: 8px; padding: 14px; }
  .rt-code code {
    font-size: 11px; color: #e2e8f0; line-height: 1.5;
    /* TODO: 공백·줄바꿈 보존, 블록으로 */
  }
</style>
</head>
<body>
<div class="rt-demo">
  <div class="rt-section">
    <div class="rt-label">패턴 1: 가로 스크롤 (가장 간단)</div>
    <!-- TODO: 아래 테이블을 .rt-scroll-wrap 래퍼로 감싼다 -->
    <table class="rt-table">
      <thead><tr><th>이름</th><th>직급</th><th>부서</th><th>입사일</th><th>이메일</th></tr></thead>
      <tbody>
        <tr><td>김철수</td><td>시니어</td><td>개발</td><td>2020-03</td><td>kim@co.kr</td></tr>
        <!-- TODO: 이영희 행 (주니어 · 디자인 · 2023-01 · lee@co.kr) -->
      </tbody>
    </table>
  </div>
  <div class="rt-section">
    <div class="rt-label">패턴 2: 카드형 변환 (모바일 최적)</div>
    <div class="rt-cards">
      <div class="rt-card">
        <div class="rt-row"><span class="rt-key">이름</span><span>김철수</span></div>
        <div class="rt-row"><span class="rt-key">직급</span><span>시니어</span></div>
        <div class="rt-row"><span class="rt-key">부서</span><span>개발</span></div>
        <div class="rt-row"><span class="rt-key">입사일</span><span>2020-03</span></div>
      </div>
      <!-- TODO: 이영희 카드 -->
    </div>
  </div>
  <div class="rt-code">
    <code><!-- TODO: 가로 스크롤 CSS 와 카드형 변환 CSS 를 글자로 --></code>
  </div>
</div>
</body>
</html>
```

**확인 방법** — 브라우저로 열고 창(또는 개발자 도구의 기기 모드)을 400px 보다 좁게 줄인다.
패턴 1 의 표가 섹션 안에서만 옆으로 밀리는지, 행에 마우스를 올리면 배경이 바뀌는지, 카드의 키와 값이 양 끝에 붙고 마지막 줄에만 구분선이 없는지, 코드 박스의 CSS 가 줄바꿈 그대로 보이는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

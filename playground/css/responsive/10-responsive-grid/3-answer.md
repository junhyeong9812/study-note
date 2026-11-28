# css/responsive/10 — Responsive Grid Layout — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 열 4개, 아이템 하나 94px — 넷째 열은 비어 있다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- 열 개수: 4열이면 4×80 + 3×8 = 352 ≤ 400, 5열이면 5×80 + 4×8 = 432 > 400 이므로 4열이다.
- 한 열 너비: (400 − 3×8) ÷ 4 = 94px.
- 아이템 1·2·3 이 94px 열에 놓이고, 넷째 열은 빈 채로 94px 를 차지한다.

**왜 그런가**

반복 횟수는 각 열을 최소값 80px 로 치고 `gap` 까지 더해 세며, 정해진 열들이 `1fr` 로 남는 너비를 고르게 나눈다.
`auto-fill` 은 빈 열을 그대로 두므로 오른쪽에 빈 공간이 남는다.
근거: 2-summary 「동작 방식 (1)」·「동작 방식 (2)」.

### 2. 아이템 하나 128px — 빈 열이 접혀 셋이 나눠 갖는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- 열은 처음에 똑같이 4개로 세어진다.
- 넷째 열은 아이템이 없어 0 으로 접히고 옆 틈도 함께 접힌다.
- 남은 3열이 (400 − 2×8) ÷ 3 = 128px 씩 나눠 갖는다.

**왜 그런가**

`auto-fit` 은 아이템이 하나도 없는 열을 0 너비로 접으므로, `1fr` 이 남은 공간을 아이템이 있는 열에만 나눈다.
근거: 2-summary 「동작 방식 (2)」.

### 3. 둘의 모습이 같다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- 둘 다 94px 짜리 4열이 되고, 아이템은 4·4·2 개씩 세 줄로 놓인다.
- 마지막 줄의 빈 두 칸은 둘 다 그대로 비어 있다.

**왜 그런가**

「빈 열」은 그 열 전체에 아이템이 하나도 없는 열이다.
아이템이 10개면 네 열 모두에 아이템이 들어가므로 접을 빈 열이 없고, `auto-fill` 과 `auto-fit` 의 차이가 사라진다.
근거: 2-summary 「동작 방식 (2)」·「어디서 틀리나 1」.

### 4. 열 개수를 컨테이너 너비로 브라우저가 다시 세기 때문이다

`auto-fill`/`auto-fit` 을 반복 횟수로 쓰면 「들어가는 만큼」 열을 만든다.
창을 좁혀 컨테이너가 좁아지면 n×최소 + (n−1)×gap ≤ 너비 를 만족하는 n 이 작아져 열이 줄고, 넘친 아이템은 다음 줄로 간다.
너비마다 열 개수를 따로 적을 필요가 없다.
근거: 2-summary 「동작 방식 (1)」.

### 5. `1fr` 은 그 자체로 길이가 정해지지 않은 값이기 때문이다

`1fr` 은 「남는 공간의 몫」이라, 열 개수가 정해지기 전에는 얼마인지 알 수 없다.
그래서 길이가 정해진 최소값 `80px` 로 열 하나의 크기를 치고 몇 개가 들어가는지 센 뒤, 남는 너비를 `1fr` 로 나눈다.
근거: 2-summary 「동작 방식 (1)」. (원본에 근거 없음 — 추론)

### 6. 앞쪽은 20px 넘치고, 뒤쪽은 60px 열 하나로 들어간다

- `minmax(80px, 1fr)`: 열은 적어도 하나 생기고 최소 80px 라서 60px 상자 밖으로 20px 넘친다.
- `minmax(min(80px, 100%), 1fr)`: `min(80px, 60px)` = 60px 가 최소값이 되어 열 하나가 60px 로 딱 들어간다.
- 넓은 컨테이너에서는 `min()` 이 80px 를 고르므로 평소 동작은 그대로다.

근거: 2-summary 「동작 방식 (3)」·「어디서 틀리나 2」.

### 7. 미디어 쿼리는 화면을 보고, 이 방식은 상자를 본다

미디어 쿼리는 뷰포트 너비를 기준으로 하므로, 화면이 넓으면 사이드바 안에서도 「넓은 화면용」 열 수를 적용해 칸이 비좁아지거나 넘칠 수 있다.
`repeat(auto-fit, minmax(…))` 은 그리드 컨테이너 너비로 열을 세므로, 좁은 사이드바 안에서는 같은 화면이라도 열이 적어진다.
근거: 2-summary 「어디서 틀리나 4」·「동작 방식 (1)」.

## 실습 정답

### 실습 1. `auto-fill` 과 `auto-fit` 을 나란히 비교하는 데모

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 루트가 섹션들을 세로로 쌓고 띄운다 | `.rg-demo { display: flex; flex-direction: column; gap: … }` |
| 2. 섹션마다 라벨과 아이템 세 개 | `.rg-section` 안의 `.rg-label` 과 `.rg-item` 1·2·3 |
| 3. 그리드 컨테이너 + 칸 간격 | `.rg-grid { display: grid; gap: … }` |
| 4. 최소 80px · 최대 `1fr` | 두 규칙의 `minmax(80px, 1fr)` |
| 5. 빈 열을 남긴다 | `.rg-grid.auto-fill { grid-template-columns: repeat(auto-fill, …) }` |
| 6. 빈 열을 접는다 | `.rg-grid.auto-fit { grid-template-columns: repeat(auto-fit, …) }` |
| 7. 예시 코드를 공백·줄바꿈 그대로 | `.rg-code code { white-space: pre; display: block; }` 와 `<code>` 내용 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/responsive/reference/responsive-grid.html`

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
<title>Responsive Grid Layout - CSS Grid의 auto-fill, auto-fit, minmax()를 조합하여 미디어 쿼리 없이 자동으로 반응하는 그리드 레이아웃을 구현한다.</title>
<!--
  [반응형 디자인] Responsive Grid Layout
  설명: CSS Grid의 auto-fill, auto-fit, minmax()를 조합하여 미디어 쿼리 없이 자동으로 반응하는 그리드 레이아웃을 구현한다.

  팁: auto-fill은 남은 공간에 빈 트랙을 만들고, auto-fit은 빈 트랙을 0으로 축소해 아이템이 공간을 채운다. 아이템이 적을 때 차이가 드러난다. minmax(최소크기, 1fr)에서 최소크기가 컨테이너보다 크면 오버플로우가 발생하므로 min(최소크기, 100%)를 쓰는 것이 안전하다.
-->
<style>
  /* .rg-demo: 데모 루트 */
  .rg-demo {
    font-family: system-ui, sans-serif;   /* 시스템 폰트 */
    display: flex;                        /* flex */
    flex-direction: column;               /* 세로 정렬 */
    gap: 14px;                            /* 섹션 간격 */
  }
  /* .rg-section: 섹션 박스 */
  .rg-section {
    background: #f1f5f9;                  /* 옅은 배경 */
    border-radius: 8px;                   /* 둥근 모서리 */
    padding: 12px;                        /* 안쪽 여백 */
  }
  /* .rg-label: 섹션 라벨 */
  .rg-label {
    font-size: 12px;                      /* 작은 폰트 */
    font-weight: 700;                     /* 굵게 */
    color: #475569;                       /* 회색 */
    margin-bottom: 8px;                   /* 콘텐츠와 간격 */
  }
  /* .rg-grid: 그리드 컨테이너 공통 */
  .rg-grid {
    display: grid;                        /* 그리드 */
    gap: 8px;                             /* 트랙 간격 */
  }
  /* .rg-grid.auto-fill: auto-fill 모드 - 빈 트랙 유지 */
  .rg-grid.auto-fill {
    grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); /* 80px 이상 트랙을 가득 채움(아이템 부족 시 빈 트랙 유지) */
  }
  /* .rg-grid.auto-fit: auto-fit 모드 - 빈 트랙을 0으로 축소 */
  .rg-grid.auto-fit {
    grid-template-columns: repeat(auto-fit, minmax(80px, 1fr)); /* 80px 이상 트랙, 빈 트랙은 0으로 → 아이템이 공간 모두 차지 */
  }
  /* .rg-item: 그리드 아이템 */
  .rg-item {
    background: #3b82f6;                  /* 파란색 */
    color: white;                         /* 흰 글자 */
    padding: 16px;                        /* 안쪽 여백 */
    border-radius: 6px;                   /* 둥근 모서리 */
    text-align: center;                   /* 중앙 정렬 */
    font-weight: 700;                     /* 굵게 */
    font-size: 14px;                      /* 폰트 */
  }
  /* .rg-code: 코드 박스(다크) */
  .rg-code {
    background: #1e293b;                  /* 어두운 배경 */
    border-radius: 8px;                   /* 둥근 모서리 */
    padding: 14px;                        /* 내부 여백 */
  }
  /* .rg-code code: 코드 텍스트 */
  .rg-code code {
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
<div class="rg-demo">
  <!-- 섹션 1: auto-fill - 빈 트랙 유지 -->
  <div class="rg-section">
    <!-- 라벨 -->
    <div class="rg-label">auto-fill: 빈 트랙 유지</div>
    <!-- auto-fill 그리드 -->
    <div class="rg-grid auto-fill">
      <!-- 아이템 1 -->
      <div class="rg-item">1</div>
      <!-- 아이템 2 -->
      <div class="rg-item">2</div>
      <!-- 아이템 3 -->
      <div class="rg-item">3</div>
    </div>
  </div>
  <!-- 섹션 2: auto-fit - 빈 트랙 축소 -->
  <div class="rg-section">
    <!-- 라벨 -->
    <div class="rg-label">auto-fit: 빈 트랙 축소 → 아이템 확장</div>
    <!-- auto-fit 그리드 -->
    <div class="rg-grid auto-fit">
      <!-- 아이템 1 -->
      <div class="rg-item">1</div>
      <!-- 아이템 2 -->
      <div class="rg-item">2</div>
      <!-- 아이템 3 -->
      <div class="rg-item">3</div>
    </div>
  </div>
  <!-- 코드 예시 박스 -->
  <div class="rg-code">
    <code>/* 미디어 쿼리 없이 반응형 그리드 */
.grid {
  display: grid;
  grid-template-columns:
    repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}</code>
  </div>
</div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.rg-demo { font-family: system-ui, sans-serif; display: flex; flex-direction: column; gap: 14px; }
.rg-section { background: #f1f5f9; border-radius: 8px; padding: 12px; }
.rg-label { font-size: 12px; font-weight: 700; color: #475569; margin-bottom: 8px; }
.rg-grid { display: grid; gap: 8px; }
.rg-grid.auto-fill { grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); }
.rg-grid.auto-fit { grid-template-columns: repeat(auto-fit, minmax(80px, 1fr)); }
.rg-item { background: #3b82f6; color: white; padding: 16px; border-radius: 6px; text-align: center; font-weight: 700; font-size: 14px; }
.rg-code { background: #1e293b; border-radius: 8px; padding: 14px; }
.rg-code code { font-size: 11px; color: #e2e8f0; white-space: pre; line-height: 1.5; display: block; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**

- 두 그리드의 차이는 반복 횟수 키워드 하나(`auto-fill` 대 `auto-fit`)뿐이다.
- 아이템을 셋만 둔 것이 핵심이다 — 넓은 창에서 열이 셋보다 많이 들어가야 빈 열이 생겨 차이가 보인다.
- 창을 좁혀 들어가는 열이 셋 이하가 되면 빈 열이 없어져 두 그리드가 같아진다.
- `minmax(80px, 1fr)` 은 열 개수를 80px 와 `gap` 으로 세고, 남는 너비를 `1fr` 로 나눈다.
- 코드 상자의 예시는 아주 좁은 상자에서 넘칠 수 있다 — 안전하게 하려면 `minmax(min(150px, 100%), 1fr)` 로 쓴다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

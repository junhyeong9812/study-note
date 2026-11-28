# css/responsive/08 — Mobile-first vs Desktop-first — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 900px 에서는 `row` 이고 `gap` 은 정해지지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`flex-direction: row` 이고, `gap` 은 이 코드가 정하지 않으므로 아이템 사이에 따로 간격이 생기지 않는다.

**왜 그런가**
- 쿼리 밖의 `column` 이 먼저 깔린다.
- 900 ≥ 768 이므로 첫 쿼리가 참이고, 나중에 나온 `row` 가 `column` 을 덮는다.
- 900 < 1024 이므로 둘째 쿼리는 거짓이라 `gap: 24px` 은 적용되지 않는다.
- 근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (4)」.

### 2. 500px 에서는 두 쿼리가 다 참 — `column` + `gap: 12px`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
참인 쿼리는 2개이고, `flex-direction: column`, `gap: 12px` 이 된다.

**왜 그런가**
- 기본으로 `row` 와 `gap: 24px` 이 깔린다.
- 500 ≤ 1023 이므로 첫 쿼리가 참이 되어 `gap` 이 12px 로 덮인다.
- 500 ≤ 767 이므로 둘째 쿼리도 참이 되어 `flex-direction` 이 `column` 으로 덮인다.
- 두 쿼리는 서로 다른 속성을 건드리므로 둘 다 살아남는다.
- 같은 너비에서 mobile-first 예는 `gap` 이 없다 — 두 예가 같은 결과가 아닌 지점이다.
- 근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (4)」.

### 3. 768px 은 `row`, 767px 은 `column`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
768px 에서는 `row`, 767px 에서는 `column` 이다.

**왜 그런가**
- `min-width: 768px` 은 너비가 768 **이상**일 때 참이고, 경계값 768 을 포함한다.
- 767 은 768 보다 작으므로 쿼리가 거짓이고, 기본값 `column` 이 남는다.
- 근거: 2-summary 「문법 — 형태와 규칙」의 표와 불릿.

### 4. 기본이 어느 끝에 있느냐에 따라 「바꿀 방향」이 정해진다

mobile-first 는 가장 좁은 화면을 기본으로 두므로, 그보다 **넓은** 화면에서만 규칙을 더해야 한다 — 「너비가 N 이상」인 `min-width` 가 그 조건이다.
desktop-first 는 가장 넓은 화면을 기본으로 두므로, 그보다 **좁은** 화면에서만 덮어써야 한다 — 「너비가 N 이하」인 `max-width` 가 그 조건이다.
근거: 2-summary 「한눈에 — 쉽게 말하면」 · 「동작 방식 (1)(2)」.

### 5. 모바일은 기본값에서 가장 먼 끝이라 덮어쓸 것이 가장 많다

desktop-first 에서 기본 스타일은 데스크톱용이다.
화면이 좁아질수록 참인 `max-width` 쿼리가 늘어나고, 가장 좁은 모바일에서는 모든 쿼리가 참이 되어 기본값을 여러 번 덮어쓴다.
원본 예에서도 500px 에서는 `gap` 과 `flex-direction` 둘 다 덮어쓰인다(퀴즈 2).
mobile-first 는 모바일이 기본이라 모바일에서는 덮어쓸 것이 없다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 5」.

### 6. 두 블록이 같은 속성을 정할 때만 깨진다

- 깨지는 경우: 두 블록이 같은 속성을 다른 값으로 정하면, 1024px 이상에서는 두 쿼리가 모두 참이고 명시도가 같으므로 나중에 적힌 768px 쪽 값이 이긴다 — 넓은 화면용 값이 사라진다.
- 멀쩡한 경우: 원본 예처럼 768px 블록은 `flex-direction` 만, 1024px 블록은 `gap` 만 건드리면 충돌이 없어 순서가 바뀌어도 결과가 같다.
- 미디어 쿼리는 명시도를 올려 주지 않으므로 소스 순서가 결정한다.
- 근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 2」.

### 7. 정확히 768px 에서 두 방식의 경계가 겹친다

`max-width: 768px` 으로 적으면 768px 에서도 `column` 쿼리가 참이 된다.
그러면 mobile-first 예라면 이미 `row` 가 되었을 768px 에서 desktop-first 쪽은 `column` 으로 남아, 두 방식의 전환 지점이 1px 어긋난다.
같은 파일에서 `min-width: 768px` 과 함께 쓰면 768px 에서 두 쿼리가 동시에 참이 되어 소스 순서에 따라 결과가 갈린다.
`min-width` · `max-width` 는 둘 다 경계값을 포함하므로, 겹치지 않게 하려면 1 작은 값(767 · 1023)을 쓴다.
근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 3」.

### 8. 가장 제한된 환경(좁은 화면)이 바탕이고, 넓어질수록 더한다

점진적 향상은 제한된 환경에서 핵심이 먼저 돌아가게 하고, 여유 있는 환경에서 꾸밈 · 기능을 더하는 설계다.
mobile-first 는 좁은 화면에서 핵심 콘텐츠를 담은 기본 스타일을 완성하고, `min-width` 쿼리로 넓은 화면에서만 가로 배치 · 넓은 간격을 더한다.
즉 CSS 의 쿼리 구조가 그 설계 방식을 그대로 옮긴 꼴이다 — 원본도 장점으로 「점진적 향상」과 「핵심 콘텐츠 우선 설계」를 함께 든다.
근거: 2-summary 「언제 쓰고 언제 안 쓰나」의 용어 풀이 · 「핵심 문장 5」.

## 실습 정답

### 실습 1. 두 접근법을 나란히 비교하는 카드 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 가로 flex · 칼럼 간격 · 줄바꿈 | `.mf-comparison { display: flex; gap: 12px; flex-wrap: wrap; }` |
| 2. 같은 비율 · 최소 폭 | `.mf-col { flex: 1; min-width: 220px; }` |
| 3. 칼럼 구분 클래스 | `.mf-col.mobile-first` · `.mf-col.desktop-first` 의 `border-color` |
| 4. 뱃지는 글자 폭만 · `df` 변형 | `.mf-badge { display: inline-block; }` · `.mf-badge.df` |
| 5. mobile-first 코드 예 | 첫 칼럼 `<code>` 안의 `.nav` 기본 + `@media (min-width: 768px)` + `@media (min-width: 1024px)` |
| 6. desktop-first 코드 예 | 둘째 칼럼 `<code>` 안의 `.nav` 기본 + `@media (max-width: 1023px)` + `@media (max-width: 767px)` |
| 7. 공백 보존 · 블록 | `.mf-code code { white-space: pre; display: block; }` |
| 8. 목록 세로 쌓기 · `pro` / `con` | `.mf-pros { display: flex; flex-direction: column; gap: 4px; }` · `.pro` · `.con` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/responsive/reference/mobile-first-vs-desktop-first.html`

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
<title>Mobile-first vs Desktop-first - CSS를 작성할 때 모바일 기본 → 큰 화면 확장(mobile-first) 또는 데스크톱 기본 → 작은 화면 축소(desktop-first) 중 어떤 접근법을 택할지 비교.</title>
<!--
  [반응형 디자인] Mobile-first vs Desktop-first
  설명: CSS를 작성할 때 모바일 기본 → 큰 화면 확장(mobile-first) 또는 데스크톱 기본 → 작은 화면 축소(desktop-first) 중 어떤 접근법을 택할지 비교.

  팁: 모바일 퍼스트가 업계 표준이다. min-width 미디어 쿼리를 사용하고 작은 화면부터 스타일을 쌓아 올린다. 모바일 트래픽이 전체의 50% 이상인 현실을 반영한 접근법이다. Tailwind CSS 등 프레임워크도 모바일 퍼스트를 기본으로 채택하고 있다.
-->
<style>
  /* .mf-demo: 데모 루트 */
  .mf-demo {
    font-family: system-ui, sans-serif;   /* 시스템 폰트 */
  }
  /* .mf-comparison: 모바일 퍼스트와 데스크톱 퍼스트 비교 영역(가로 2칼럼) */
  .mf-comparison {
    display: flex;                        /* 가로 배치 */
    gap: 12px;                            /* 칼럼 간격 */
    flex-wrap: wrap;                      /* 좁아지면 줄바꿈 */
  }
  /* .mf-col: 한 칼럼(접근법 하나) */
  .mf-col {
    flex: 1;                              /* 동일 비율 */
    min-width: 220px;                     /* 최소 폭 - 좁아지면 줄바꿈 */
    background: #f8fafc;                  /* 옅은 배경 */
    border-radius: 10px;                  /* 둥근 모서리 */
    padding: 14px;                        /* 안쪽 여백 */
    border: 2px solid #e2e8f0;            /* 기본 보더 */
  }
  /* .mf-col.mobile-first: 모바일 퍼스트 칼럼 강조 */
  .mf-col.mobile-first {
    border-color: #22c55e;                /* 초록 보더 */
  }
  /* .mf-col.desktop-first: 데스크톱 퍼스트 칼럼 강조 */
  .mf-col.desktop-first {
    border-color: #f59e0b;                /* 주황 보더 */
  }
  /* .mf-badge: 칼럼 상단 뱃지(권장 표시) */
  .mf-badge {
    display: inline-block;                /* 자기 폭만 */
    padding: 4px 10px;                    /* 뱃지 패딩 */
    border-radius: 6px;                   /* 둥근 모서리 */
    font-size: 12px;                      /* 작은 폰트 */
    font-weight: 700;                     /* 굵게 */
    background: #dcfce7;                  /* 옅은 초록 */
    color: #166534;                       /* 진한 초록 */
    margin-bottom: 10px;                  /* 코드와 간격 */
  }
  /* .mf-badge.df: 데스크톱 퍼스트 뱃지(주황 톤) */
  .mf-badge.df {
    background: #fef3c7;                  /* 옅은 주황 */
    color: #92400e;                       /* 진한 주황 */
  }
  /* .mf-code: 코드 블록(다크) */
  .mf-code {
    background: #1e293b;                  /* 어두운 배경 */
    border-radius: 6px;                   /* 둥근 모서리 */
    padding: 10px;                        /* 내부 여백 */
    margin-bottom: 10px;                  /* 장단점 목록과 간격 */
  }
  /* .mf-code code: 코드 텍스트 */
  .mf-code code {
    font-size: 11px;                      /* 작은 폰트 */
    color: #e2e8f0;                       /* 밝은 글자 */
    white-space: pre;                     /* 공백/개행 보존 */
    line-height: 1.5;                     /* 줄 간격 */
    display: block;                       /* 블록 */
  }
  /* .mf-pros: 장단점 목록 컨테이너 */
  .mf-pros {
    display: flex;                        /* flex */
    flex-direction: column;               /* 세로 정렬 */
    gap: 4px;                             /* 항목 간격 */
  }
  /* .pro, .con: 장점/단점 항목 공통 스타일 */
  .pro,
  .con {
    font-size: 11px;                      /* 작은 폰트 */
    padding: 4px 8px;                     /* 안쪽 여백 */
    border-radius: 4px;                   /* 둥근 모서리 */
  }
  /* .pro: 장점 - 초록 톤 */
  .pro {
    background: #dcfce7;                  /* 옅은 초록 */
    color: #166534;                       /* 진한 초록 */
  }
  /* .con: 단점/주의 - 주황 톤 */
  .con {
    background: #fef3c7;                  /* 옅은 주황 */
    color: #92400e;                       /* 진한 주황 */
  }
</style>
</head>
<body>
<!-- 데모 루트 -->
<div class="mf-demo">
  <!-- 두 접근법 비교 -->
  <div class="mf-comparison">
    <!-- 모바일 퍼스트 칼럼 -->
    <div class="mf-col mobile-first">
      <!-- 권장 뱃지 -->
      <div class="mf-badge">Mobile-first (권장)</div>
      <!-- 코드 예시 -->
      <div class="mf-code">
        <code>/* 기본: 모바일 */
.nav { flex-direction: column; }

/* 확장: 태블릿 이상 */
@media (min-width: 768px) {
  .nav { flex-direction: row; }
}

/* 확장: 데스크톱 이상 */
@media (min-width: 1024px) {
  .nav { gap: 24px; }
}</code>
      </div>
      <!-- 장점 목록 -->
      <div class="mf-pros">
        <!-- 장점 1 -->
        <div class="pro">성능: 모바일에서 불필요한 CSS 로드 최소화</div>
        <!-- 장점 2 -->
        <div class="pro">점진적 향상(Progressive Enhancement)</div>
        <!-- 장점 3 -->
        <div class="pro">핵심 콘텐츠 우선 설계</div>
      </div>
    </div>
    <!-- 데스크톱 퍼스트 칼럼 -->
    <div class="mf-col desktop-first">
      <!-- 데스크톱 퍼스트 뱃지 -->
      <div class="mf-badge df">Desktop-first</div>
      <!-- 코드 예시 -->
      <div class="mf-code">
        <code>/* 기본: 데스크톱 */
.nav { flex-direction: row; gap: 24px; }

/* 축소: 태블릿 이하 */
@media (max-width: 1023px) {
  .nav { gap: 12px; }
}

/* 축소: 모바일 이하 */
@media (max-width: 767px) {
  .nav { flex-direction: column; }
}</code>
      </div>
      <!-- 단점/주의 목록 -->
      <div class="mf-pros">
        <!-- 단점 1 -->
        <div class="con">모바일에서 불필요한 CSS 오버라이드 증가</div>
        <!-- 단점 2 -->
        <div class="con">레거시 프로젝트 마이그레이션에 적합</div>
        <!-- 단점 3 -->
        <div class="con">데스크톱 중심 디자인 시 직관적</div>
      </div>
    </div>
  </div>
</div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.mf-demo { font-family: system-ui, sans-serif; }
.mf-comparison { display: flex; gap: 12px; flex-wrap: wrap; }
.mf-col { flex: 1; min-width: 220px; background: #f8fafc; border-radius: 10px; padding: 14px; border: 2px solid #e2e8f0; }
.mf-col.mobile-first { border-color: #22c55e; }
.mf-col.desktop-first { border-color: #f59e0b; }
.mf-badge { display: inline-block; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 700; background: #dcfce7; color: #166534; margin-bottom: 10px; }
.mf-badge.df { background: #fef3c7; color: #92400e; }
.mf-code { background: #1e293b; border-radius: 6px; padding: 10px; margin-bottom: 10px; }
.mf-code code { font-size: 11px; color: #e2e8f0; white-space: pre; line-height: 1.5; display: block; }
.mf-pros { display: flex; flex-direction: column; gap: 4px; }
.pro, .con { font-size: 11px; padding: 4px 8px; border-radius: 4px; }
.pro { background: #dcfce7; color: #166534; }
.con { background: #fef3c7; color: #92400e; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 비교 영역 자체는 미디어 쿼리 없이 `flex-wrap: wrap` 과 칼럼의 `min-width` 만으로 좁은 창에서 줄을 바꾼다 — 두 칼럼이 최소 폭을 지킬 자리가 없으면 다음 줄로 넘어간다 (코드에서 읽은 것 — 렌더 실측 아님).
- `<code>` 안의 CSS 는 화면에 보여 줄 **글**일 뿐, 페이지에 적용되는 스타일이 아니다.
- `white-space: pre` 가 없으면 코드 글의 줄바꿈 · 들여쓰기가 한 줄로 뭉개진다.
- 둘째 칼럼의 목록도 클래스는 `.mf-pros` 를 그대로 쓰고, 항목 클래스만 `con` 으로 바꿔 톤을 다르게 한다.
- `con` 칸의 둘째 · 셋째 항목은 내용상 단점이 아니라 desktop-first 를 고를 만한 상황이다(2-summary 「어디서 틀리나 6」).

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

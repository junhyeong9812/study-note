# css/cascade-specificity/04 — !important — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 색은 `.styled` 의 파랑, 크기는 ID 의 18px, 굵기는 `.styled` 의 700

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- 글자색: `#3b82f6`(파랑) — `.styled` 의 `!important` 선언.
- 글자 크기: `18px` — `#high-spec` 의 일반 선언.
- 굵기: `700` — `.styled` 의 일반 선언.

화면에는 18px 크기의 굵은 파란 글자가 보인다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**

`color` 는 두 규칙이 겨루지만 `.styled` 쪽만 `!important` 이므로 명시도(1,0,0 대 0,1,0)를 따지기 전에 승부가 난다.
`font-size` 와 `font-weight` 는 겨룰 상대가 없으므로 각자 선언한 값이 그대로 적용된다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (2)」.

### 2. 빨강 — `!important` 끼리는 다시 명시도로 겨룬다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

글자색은 `red` 가 된다.

**왜 그런가**

둘 다 `!important` 이므로 그 우위는 상쇄되고, 일반 선언처럼 명시도로 겨룬다.
ID `#a`(1,0,0) 가 클래스 `.b`(0,1,0) 보다 높으므로 빨강이 이긴다.
근거: 2-summary 「동작 방식 (3)」.

### 3. 주황 — 명시도까지 같으면 나중에 나온 선언이 이긴다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

글자색은 `orange` 가 된다.

**왜 그런가**

둘 다 `!important` 이고 둘 다 클래스 하나(0,1,0)라 명시도가 같다.
그러면 스타일시트에서 나중에 나온 `.y` 의 선언이 이긴다.
HTML 의 `class="y x"` 에 적은 클래스 차례는 판정과 상관없다.
근거: 2-summary 「동작 방식 (3)」 · 「문법 — 형태와 규칙」의 표.

### 4. `!important` 와 캐스케이드 승부가 선언 하나 단위로 나기 때문이다

캐스케이드는 규칙 전체가 아니라 속성 하나하나를 두고 승자를 고른다.
`#high-spec` 규칙은 `color` 한 속성에서만 `.styled` 의 `!important` 선언에 졌다.
`font-size` 는 이 문단에 다른 선언이 없으므로 겨룰 상대 없이 적용된다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 1」.

### 5. 다른 `!important` 선언이 필요하다 — 일반 선언으로는 명시도를 아무리 높여도 못 덮는다

`!important` 선언을 덮으려면 같은 속성에 `!important` 를 붙이고, 명시도로 이기거나(높거나) 명시도가 같을 때 나중에 나와야 한다.
일반 선언은 선택자를 길게 써서 명시도를 높여도 `!important` 칸에 들어가지 못하므로 이길 수 없다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 3」.

### 6. 일반 선언으로는 덮을 수 없어, 덮으려는 쪽도 `!important` 를 붙이게 되기 때문이다

한 곳에 `!important` 를 붙이면, 그 값을 바꾸려는 다음 사람은 일반 선언으로 이길 수 없다.
그래서 또 `!important` 를 붙이고, 그러면 `!important` 끼리 다시 명시도 싸움이 벌어진다.
결국 피하려던 명시도 문제가 한 칸 위에서 되풀이되고, 어느 값이 왜 이기는지 추적하기 어려워진다.
근거: 2-summary 「동작 방식 (4)」.

### 7. 「반드시 그렇게 되어야 하는」 경우와 「고칠 수 없는 코드」를 덮는 경우라서다 — 그 밖에는 명시도 구조를 고친다

`.hidden` 은 붙이는 순간 어떤 다른 규칙과 상관없이 숨겨져야 하는 유틸리티 클래스라, 명시도에 지면 안 된다.
서드파티 CSS 는 직접 고칠 수 없으므로 덮는 수단으로 `!important` 를 쓸 수밖에 없는 경우가 있다.
내 코드 안에서 규칙이 먹지 않는 것은 선택자 설계의 문제이므로, 명시도 구조를 정리하는 것이 올바른 해결책이다.
근거: 2-summary 「어디서 틀리나 4」 · 「언제 쓰고 언제 안 쓰나」.

## 실습 정답

### 실습 1. 명시도 낮은 클래스가 ID 를 이기는 데모 카드 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 데모 상자 안에 문단 셋 | `<div class="imp-demo">` 와 그 안의 `<p>` 셋 |
| 2. 첫 문단에 id 와 class 를 함께 | `<p id="high-spec" class="styled">` |
| 3. ID 규칙은 색과 크기, 클래스 규칙은 다른 색과 굵기 | `#high-spec { color; font-size }` · `.styled { color; font-weight }` |
| 4. 클래스 규칙의 글자색만 `!important` | `.styled { color: #3b82f6 !important; }` |
| 5. 크기는 ID, 굵기는 클래스 값이 그대로 | `#high-spec` 의 `font-size` · `.styled` 의 `font-weight` (둘 다 `!important` 없음) |
| 6. `.danger` · `.warning` 은 일반 선언으로 색 | `.danger { color … }` · `.warning { color … }` |
| 7. 카드 꾸밈과 마지막 문단 여백 제거 | `.imp-demo p` · `.imp-demo p:last-child { margin-bottom: 0; }` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/cascade-specificity/reference/important.html`

```html
<!DOCTYPE html>
<!-- 문서 타입 선언: HTML5 -->
<html lang="ko">
<!-- HTML 루트: 문서 언어를 한국어로 지정 -->
<head>
<!-- 메타 정보 영역 -->
<meta charset="utf-8">
<!-- 문자 인코딩: UTF-8 -->
<title>!important - 선언에 !important를 붙이면 명시도를 무시하고 최우선 적용된다. 하지만 !important끼리 충돌하면 다시 명시도 규칙을 따르며, 유지보수를 극도로 어렵게 만든다</title>
<!--
  [캐스케이드 & 명시도] !important
  설명: 선언에 !important를 붙이면 명시도를 무시하고 최우선 적용된다. 하지만 !important끼리 충돌하면 다시 명시도 규칙을 따르며, 유지보수를 극도로 어렵게 만든다
  구문: property: value !important;
  팁: !important의 정당한 사용: 유틸리티 클래스(.hidden { display: none !important }), 서드파티 CSS 오버라이드. 그 외에는 명시도 구조를 개선하는 것이 올바른 해결책.
-->
<style>
  /* #high-spec: ID 선택자 — 명시도 1,0,0 (높은 명시도) */
  #high-spec {
    color: red;                 /* 글자색 빨강 — 일반 규칙은 .styled !important에 짐 */
    font-size: 18px;            /* 글자 크기 18px (충돌 없음 → 적용됨) */
  }

  /* .styled: 클래스 선택자 — 명시도 0,1,0이지만 !important로 ID를 이김 */
  .styled {
    color: #3b82f6 !important;  /* 일반 규칙을 모두 무시하고 강제 적용. 디버깅 어려워지므로 마지막 수단 */
    font-weight: 700;           /* 굵기 700 (일반 규칙) */
  }

  /* .imp-demo: 데모 컨테이너 (특이도 0,1,0) */
  .imp-demo {
    padding: 16px;              /* 안쪽 여백 16px */
    background: #f1f5f9;        /* 배경 연한 회색 */
    border-radius: 8px;         /* 모서리 둥글게 8px */
  }
  /* .imp-demo p: 자손 결합자 — 명시도 0,1,1 */
  .imp-demo p {
    padding: 14px;              /* 안쪽 여백 14px */
    margin-bottom: 8px;         /* 아래 외부 여백 8px */
    background: white;          /* 배경 흰색 */
    border-radius: 6px;         /* 모서리 둥글게 6px */
    border: 2px solid #e2e8f0;  /* 테두리 회색 2px */
  }
  /* .imp-demo p:last-child: 가상 클래스 추가 — 명시도 0,2,1 */
  .imp-demo p:last-child {
    margin-bottom: 0;           /* 마지막 p 아래 여백 제거 */
  }
  /* .danger: 위험 텍스트 (특이도 0,1,0) */
  .danger {
    color: #ef4444;             /* 글자색 빨강 */
    font-weight: 600;           /* 굵기 600 */
  }
  /* .warning: 경고 텍스트 (특이도 0,1,0) */
  .warning {
    color: #f59e0b;             /* 글자색 주황 */
    font-weight: 600;           /* 굵기 600 */
    font-size: 14px;            /* 글자 크기 14px */
  }
</style>
</head>
<body>
<!-- 문서 본문 -->
  <div class="imp-demo">
    <!-- !important 데모 컨테이너 -->
    <p id="high-spec" class="styled">ID 선택자 (0,1,0,0) vs .styled !important</p>
    <!-- ID(1,0,0) vs 클래스 !important — !important가 명시도를 무시하고 승리 → 파랑 적용 -->
    <p class="danger">!important는 다른 !important로만 덮을 수 있다</p>
    <!-- 빨강 위험 메시지 -->
    <p class="warning">⚠️ !important 남용 = 유지보수 지옥</p>
    <!-- 주황 경고 메시지 -->
  </div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
/* ID 선택자: 0,1,0,0 — 높은 명시도 */
#high-spec { color: red; font-size: 18px; }

/* 클래스: 0,0,1,0 — 낮은 명시도이지만 !important로 승리 */
.styled { color: #3b82f6 !important; font-weight: 700; }

.imp-demo { padding: 16px; background: #f1f5f9; border-radius: 8px; }
.imp-demo p { padding: 14px; margin-bottom: 8px; background: white; border-radius: 6px; border: 2px solid #e2e8f0; }
.imp-demo p:last-child { margin-bottom: 0; }
.danger { color: #ef4444; font-weight: 600; }
.warning { color: #f59e0b; font-weight: 600; font-size: 14px; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**

- 핵심 줄은 `.styled` 의 `color: #3b82f6 !important;` 하나다 — 이것만으로 명시도 0,1,0 이 1,0,0 을 이긴다.
- `!important` 는 `color` 선언에만 붙였으므로 `#high-spec` 의 `font-size: 18px` 은 그대로 살아남는다.
- `font-weight: 700` 에는 `!important` 가 필요 없다 — 겨룰 상대가 없기 때문이다.
- 둘째 · 셋째 문단은 일반 선언만 쓰므로, 그 색을 바꾸고 싶으면 선택자 구조로 해결하면 된다.
- 첫 문단은 18px 크기의 굵은 파란 글자, 둘째는 빨강, 셋째는 작은 주황 글자로 보인다 (코드에서 읽은 것 — 렌더 실측 아님).

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

# css/cascade-specificity/02 — Cascade order — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 글자색은 나중 규칙의 `#3b82f6`, 여백은 12px

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- 글자색은 `#3b82f6`(파랑)이다.
- 안쪽 여백은 12px 이다 (발췌에 다른 규칙이 없다는 전제).

**왜 그런가**

- 두 규칙은 출처(작성자 일반) · 레이어(없음) · 명시도(0,1,0)가 모두 같아서 마지막 기준인 소스 순서까지 내려간다.
- 소스 순서에서는 나중에 나온 둘째 규칙이 이긴다.
- `padding` 은 둘째 규칙에 없어 겨룰 상대가 없으므로 첫 규칙의 12px 가 그대로 쓰인다 — 판정은 속성 단위다.
- 화면에서는 파란 글자로 보일 것이다 (코드에서 읽은 것 — 렌더 실측 아님).
- 근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (2)」.

### 2. 16px — 명시도에서 승부가 나서 순서와 무관하다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- `p.styled` 의 안쪽 여백은 16px 이다.
- 두 규칙의 위아래를 바꿔도 16px 그대로다.

**왜 그런가**

- `.styled` 는 0,1,0, `.cascade-demo p` 는 클래스 하나에 요소 하나라 0,1,1 이다.
- 출처와 레이어가 같으니 명시도에서 갈리고, 0,1,1 이 이긴다.
- 명시도에서 승부가 났으므로 소스 순서는 아예 보지 않는다.
- 원본 정답 코드의 주석 「padding 12px (충돌 없음 → 적용됨)」은 바로 이 충돌을 놓친 것이다.
- 근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 3」.

### 3. 0 — 위로 옮겨도 0 이다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- 마지막 `p` 의 아래 바깥 여백은 0 이다.
- `:last-child` 규칙을 위로 옮겨도 0 이다.

**왜 그런가**

- `.cascade-demo p:last-child` 는 클래스 1 · 가상 클래스 1 · 요소 1 이라 0,2,1, `.cascade-demo p` 는 0,1,1 이다.
- 가운데 자리에서 2 > 1 이므로 명시도에서 승부가 난다.
- 그래서 소스 순서는 판정에 쓰이지 않고, 규칙을 어디에 두든 결과는 같다.
- 근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 7」.

### 4. 판정이 속성 단위로 따로 이뤄지기 때문이다

캐스케이드는 규칙 하나를 통째로 이기거나 지게 만들지 않는다.
요소마다, 속성마다 후보 선언을 따로 모아 겨룬다.
`.styled` 첫 규칙의 `color` 는 둘째 규칙의 `color` 와 겨뤄 졌지만, 같은 규칙의 `padding` 은 `padding` 후보들 사이에서 따로 판정받는다.
그래서 진 것은 `color: red` 선언 하나뿐이다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 2」.

### 5. 첫 기준인 「출처와 중요도」에서 끝난다 — `!important` 쪽이 이긴다

`!important` 는 명시도를 올리는 장치가 아니라 중요도를 바꾼다.
중요도는 캐스케이드가 가장 먼저 보는 기준이라, 여기서 갈리면 `@layer` · 명시도 · 소스 순서는 보지 않는다.
원본 팁의 순서에서도 `!important` 선언 단계는 일반 선언 단계보다 위다.
그래서 일반 선언의 명시도가 아무리 높아도 `!important` 선언이 이긴다(같은 작성자 출처라는 전제).
근거: 2-summary 「동작 방식 (4)」 · 「핵심 문장 4」.

### 6. 아니다 — 같은 출처 · 같은 명시도의 소스 순서 비교일 뿐이다

두 `.multi` 규칙은 같은 `<style>` 안에 있고 둘 다 `!important` 가 없다.
둘 다 작성자 일반 · 레이어 없음 · 명시도 0,1,0 이라 소스 순서에서 승부가 난다.
결국 `.styled` 와 같은 것을 한 번 더 보여 주는 셈이다.
주석의 「브라우저 기본 < 작성자 일반 < 작성자 !important」나 「여러 스타일시트」라는 문구를 실제로 보이려면 `!important` 선언이나 브라우저 기본 스타일과 겨루는 예가 있어야 한다.
근거: 2-summary 「어디서 틀리나 4」.

### 7. 인라인 `style` 자리를 앞에 두느냐 빼느냐의 차이다

`0,0,1,0` 은 맨 앞에 인라인 `style` 속성 자리를 둔 네 자리 표기다.
`0,1,0` 은 그 자리를 빼고 (ID, 클래스 류, 요소 류)만 적은 세 자리 표기다.
둘 다 「클래스 하나」라는 같은 명시도를 나타낸다.
근거: 2-summary 「어디서 틀리나 5」.

### 8. Transitions 는 `!important` 보다 위, Animations 는 `!important` 보다 아래다

원본 팁의 전체 순서는 1) Transitions 2) `!important` 3) Animations 4) 일반 선언이다(위가 더 셈).
그래서 전환 중인 값은 `!important` 선언까지 이긴다.
애니메이션 중인 값은 `!important` 선언에는 지지만 일반 선언은 이긴다.
근거: 2-summary 「동작 방식 (4)」의 표.

## 실습 정답

### 실습 1. 소스 순서와 명시도로 스타일 충돌 가리기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 컨테이너 안 두 단락 | `<div class="cascade-demo">` 안의 `<p class="styled">` · `<p class="multi">` |
| 2. `.styled` 두 번 — 나중 글자색이 이김 | 첫 `.styled { color: red; padding: 12px; }` · 둘째 `.styled { color: #3b82f6; }` |
| 3. `.multi` 두 번 — 보라색 굵은 글씨 | 첫 `.multi { color: gray; }` · 둘째 `.multi { color: #8b5cf6; font-weight: 700; }` |
| 4. 컨테이너 · 단락 공통 꾸밈 | `.cascade-demo { … }` · `.cascade-demo p { … }` |
| 5. 마지막 단락 아래 여백 없애기(명시도로) | `.cascade-demo p:last-child { margin-bottom: 0; }` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/cascade-specificity/reference/cascade-order.html`

```html
<!DOCTYPE html>
<!-- 문서 타입 선언: HTML5 -->
<html lang="ko">
<!-- HTML 루트: 문서 언어를 한국어로 지정 -->
<head>
<!-- 메타 정보 영역 -->
<meta charset="utf-8">
<!-- 문자 인코딩: UTF-8 -->
<title>Cascade order - CSS 캐스케이드의 우선순위 결정 순서: 1) 출처와 중요도 2) @layer 순서 3) 명시도 4) 소스 코드 순서. 같은 명시도라면 나중에 선언된 스타일이 적용된다</title>
<!--
  [캐스케이드 & 명시도] Cascade order
  설명: CSS 캐스케이드의 우선순위 결정 순서: 1) 출처와 중요도 2) @layer 순서 3) 명시도 4) 소스 코드 순서. 같은 명시도라면 나중에 선언된 스타일이 적용된다
  구문: 출처 > @layer > 명시도 > 소스 순서
  팁: 캐스케이드 전체 순서: 1) Transitions 2) !important (UA > user > author > @layer) 3) Animations 4) 일반 (author @layer > author > user > UA). 출처가 같으면 명시도, 그것도 같으면 소스 순서.
-->
<style>
  /* 같은 명시도(0,0,1,0)에서 소스 순서 비교 */
  /* .styled (먼저 선언): 명시도 0,1,0 — 같은 명시도면 나중 규칙에게 짐 */
  .styled {
    color: red;                 /* 글자색 빨강 — 아래 규칙에 의해 덮여서 무효 */
    padding: 12px;              /* 안쪽 여백 12px (충돌 없음 → 적용됨) */
  }
  /* .styled (나중 선언): 명시도 동일 0,1,0 — 소스 순서가 늦어 승리 */
  .styled {
    color: #3b82f6;             /* 글자색 파랑 — 같은 명시도면 나중 선언이 이김 */
  }

  /* 브라우저 기본 < 작성자 일반 < 작성자 !important */
  /* .multi (먼저): 작성자 일반 스타일 — 아래에서 덮임 */
  .multi {
    color: gray;                /* 글자색 회색 — 다음 규칙으로 덮임 */
  }
  /* .multi (나중): 같은 명시도 0,1,0이지만 소스 순서로 승리 */
  .multi {
    color: #8b5cf6;             /* 글자색 보라 — 나중 선언이 적용 */
    font-weight: 700;           /* 굵기 700 (Bold) */
  }

  /* .cascade-demo: 데모 컨테이너 (특이도 0,1,0) */
  .cascade-demo {
    padding: 16px;              /* 안쪽 여백 16px */
    background: #f1f5f9;        /* 배경: 연한 회색 */
    border-radius: 8px;         /* 모서리 둥글게 8px */
  }
  /* .cascade-demo p: 자손 결합자 — 명시도 0,1,1 */
  .cascade-demo p {
    font-size: 18px;            /* 글자 크기 18px */
    padding: 16px;              /* 안쪽 여백 16px */
    background: white;          /* 배경: 흰색 */
    border-radius: 6px;         /* 모서리 둥글게 6px */
    margin-bottom: 8px;         /* 아래 외부 여백 8px */
    border: 2px solid #e2e8f0;  /* 테두리 2px 회색 */
  }
  /* .cascade-demo p:last-child: 가상 클래스 추가 — 명시도 0,2,1 (.cascade-demo p보다 우선) */
  .cascade-demo p:last-child {
    margin-bottom: 0;           /* 마지막 p는 아래 여백 제거 */
  }
</style>
</head>
<body>
<!-- 문서 본문 -->
  <div class="cascade-demo">
    <!-- 캐스케이드 순서 데모 컨테이너 -->
    <p class="styled">같은 명시도 → 나중 선언이 승리</p>
    <!-- .styled 두 번 선언: 나중 선언 color #3b82f6 적용 -->
    <p class="multi">여러 스타일시트에서 온 스타일</p>
    <!-- .multi 두 번 선언: 나중 선언 color #8b5cf6 + font-weight 700 적용 -->
  </div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
/* 같은 명시도(0,0,1,0)에서 소스 순서 비교 */
.styled { color: red; padding: 12px; }      /* 먼저 선언 */
.styled { color: #3b82f6; }                 /* 나중 선언 — 승리! */

/* 브라우저 기본 < 작성자 일반 < 작성자 !important */
.multi { color: gray; }                     /* 작성자 스타일 */
.multi { color: #8b5cf6; font-weight: 700; } /* 나중 선언 — 승리 */

.cascade-demo { padding: 16px; background: #f1f5f9; border-radius: 8px; }
.cascade-demo p { font-size: 18px; padding: 16px; background: white; border-radius: 6px; margin-bottom: 8px; border: 2px solid #e2e8f0; }
.cascade-demo p:last-child { margin-bottom: 0; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- `.styled` · `.multi` 는 각각 같은 선택자를 두 번 써서 출처 · 레이어 · 명시도를 모두 같게 만들었고, 그래서 소스 순서(나중 것)로 승부가 난다.
- 둘째 규칙에 없는 속성(`.styled` 의 `padding`)은 겨룰 상대가 없어 첫 규칙 값이 남는다 — 판정은 속성 단위다.
- 다만 `p.styled` 에는 `.cascade-demo p`(0,1,1)의 `padding: 16px` 도 닿아, 명시도에서 0,1,0 인 `.styled` 의 12px 를 이긴다 — 정답 코드 주석의 「충돌 없음 → 적용됨」과 달리 코드를 읽으면 16px 가 된다 (코드에서 읽은 것 — 렌더 실측 아님).
- `:last-child` 를 덧붙여 명시도를 0,2,1 로 올렸기 때문에 규칙의 위치와 상관없이 `margin-bottom: 0` 이 이긴다.
- `.multi` 는 주석과 달리 출처나 `!important` 를 비교하지 않는다 — 같은 작성자 일반 선언 두 개의 소스 순서 비교다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

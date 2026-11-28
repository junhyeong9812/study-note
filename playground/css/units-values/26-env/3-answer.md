# css/units-values/26 — env() — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 0px — 변수가 정의돼 있으면 fallback 은 쓰이지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
위쪽 안쪽 여백은 0px 이다.

**왜 그런가**
`env()` 는 먼저 변수가 정의돼 있는지 본다.
`safe-area-inset-top` 이 0px 로 정의돼 있으므로 그 0px 을 쓴다.
44px 은 변수가 정의되지 않았을 때만 쓰인다.
근거: 2-summary 「동작 방식 (1)」, 「어디서 틀리나 2」.

### 2. 0px 일 때 16px, 44px 일 때 44px

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
- inset 0px → `max(16px, 0px)` → 16px.
- inset 44px → `max(16px, 44px)` → 44px.

**왜 그런가**
`env()` 는 길이를 돌려주므로 `max()` 의 한 인자가 된다.
`max()` 는 둘 중 큰 값을 고르므로, 노치가 없으면 최소 여백 16px 이, 노치가 있으면 가려지는 폭이 골라진다.
근거: 2-summary 「동작 방식 (3)」.

### 3. meta 태그가 없으면 페이지가 안전 영역 안에만 그려진다

`viewport-fit=cover` 는 페이지가 노치 · 홈 표시줄 밑까지 화면 전체를 덮겠다는 선언이다.
이 선언이 없으면 페이지가 처음부터 안전 영역 안에 놓이므로 안쪽으로 밀어 줄 폭이 생기지 않는다.
그래서 원본 팁은 `env()` 를 이 meta 태그와 함께 써야 동작한다고 말한다.
근거: 2-summary 「동작 방식 (2)」, 「어디서 틀리나 1」. (밀어 줄 폭이 생기지 않는 까닭은 원본에 근거 없음 — 추론)

### 4. fallback 은 「최소값」이 아니라 「변수가 없을 때의 대체값」이다

변수가 0px 으로 정의된 화면에서는 `env(safe-area-inset-left, 16px)` 가 0px 이 된다.
그러면 「최소 16px」 조건이 깨진다.
`max(16px, env(safe-area-inset-left))` 는 값이 0이어도 16px 을 고르므로 최소 여백을 지킨다 — 원본 팁이 min/max 와의 조합을 권하는 까닭이다.
근거: 2-summary 「동작 방식 (1)」, 「동작 방식 (3)」, 「어디서 틀리나 2」.

### 5. 쓰이지 않는다 — 선언 전체가 버려진다

`env()` 를 모르는 브라우저는 그 선언을 해석하지 못해 통째로 버리므로, 안의 44px 도 함께 버려진다.
대비하려면 `env()` 선언 앞에 평범한 값(예: `padding-top: 44px;`)을 먼저 적고, 그 아래에 `env()` 선언을 둔다.
지원하는 브라우저는 뒤 선언으로 덮어쓰고, 지원하지 않는 브라우저는 앞 선언을 남긴다.
근거: 2-summary 「어디서 틀리나 3」 (그 절에 확인 필요 표시가 있다).

### 6. 읽을 수 없다 — `env()` 의 변수는 브라우저가 정의한다

`env()` 로 읽는 이름은 사용자 에이전트가 정의한 것뿐이다.
작성자가 만든 `--notch-gap` 은 사용자 정의 속성이라 `var(--notch-gap)` 으로 읽는다.
근거: 2-summary 「문법 — 형태와 규칙」의 규칙, 「어디서 틀리나 4」.

### 7. `env()` 는 브라우저가, `var()` 는 작성자가 값을 정의한다

`env()` 는 브라우저가 기기 상황(노치 폭 등)을 보고 정의한 값을 읽는다.
`var()` 는 작성자가 `--이름` 으로 정의한 사용자 정의 속성을 읽는다.
둘 다 「이름으로 값을 가져와 속성 값 자리에 넣고, 두 번째 인자로 대체값을 줄 수 있다」는 점은 닮았다.
근거: 2-summary 「언제 쓰고 언제 안 쓰나」, 「어디서 틀리나 4」. (fallback 형태가 닮았다는 서술은 원본에 근거 없음 — 추론)

## 실습 정답

### 실습 1. 안전 영역 패딩을 두른 어두운 카드

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 세 겹 구조와 단락 · 코드 예 | `<div class="env-demo">` › `<div class="safe-area">` › `<div class="content">` › `<p>` · `<code>` |
| 2. 방향별 padding 을 `env()` 로 | `.safe-area` 의 `padding-top` · `padding-bottom` · `padding-left` · `padding-right` |
| 3. 네 fallback | `env(safe-area-inset-top, 44px)` · `env(safe-area-inset-bottom, 34px)` · `env(safe-area-inset-left, 16px)` · `env(safe-area-inset-right, 16px)` |
| 4. 꾸밈 유지 | `.env-demo` · `.safe-area` 의 배경 · 모서리 · `overflow`, `.content` · `.content p` · `.content code` 규칙 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/units-values/reference/env.html`

```html
<!DOCTYPE html>                              <!-- HTML5 문서 타입 선언 -->
<html lang="ko">                              <!-- 문서 언어를 한국어로 지정 -->
<head>
<meta charset="utf-8">                       <!-- 문자 인코딩을 UTF-8로 설정 -->
<title>env() - 사용자 에이전트(브라우저)가 정의한 환경 변수를 참조하는 함수. 주로 모바일의 safe-area-inset 값에 사용</title>
<!--
  [CSS 단위 & 값] env()
  설명: 사용자 에이전트(브라우저)가 정의한 환경 변수를 참조하는 함수. 주로 모바일의 safe-area-inset 값에 사용
  구문: env(<variable>, <fallback>?)
  팁: viewport-fit=cover 메타 태그와 함께 사용해야 동작. max(16px, env(safe-area-inset-left))처럼 min/max와 조합 권장.
-->
<style>
/* .env-demo: env() 시연 컨테이너 */
.env-demo {
  padding: 16px;                              /* 안쪽 여백 */
  background: #f1f5f9;                        /* 연한 배경 */
  border-radius: 8px;                         /* 모서리 둥글기 */
}

/* .safe-area: 모바일 안전 영역 패딩 적용 */
.safe-area {
  background: #1e293b;                        /* 어두운 배경 */
  border-radius: 16px;                        /* 모서리 둥글기 */
  overflow: hidden;                           /* 자식 넘침 차단 */
  padding-top: env(safe-area-inset-top, 44px);            /* 상단 안전 영역 (없으면 44px) */
  padding-bottom: env(safe-area-inset-bottom, 34px);      /* 하단 안전 영역 (없으면 34px) */
  padding-left: env(safe-area-inset-left, 16px);          /* 왼쪽 안전 영역 (없으면 16px) */
  padding-right: env(safe-area-inset-right, 16px);        /* 오른쪽 안전 영역 (없으면 16px) */
}

/* .content: 안전 영역 안의 콘텐츠 박스 */
.content {
  background: #334155;                        /* 한 단계 밝은 어두운 배경 */
  border-radius: 8px;                         /* 모서리 둥글기 */
  padding: 20px;                              /* 안쪽 여백 */
}

/* .content p: 본문 단락 */
.content p {
  color: white;                               /* 흰 글자 */
  font-size: 14px;                            /* 글자 크기 */
  margin-bottom: 8px;                         /* 아래 간격 */
}

/* .content code: 인라인 코드 */
.content code {
  color: #67e8f9;                             /* 청록 글자 */
  font-size: 13px;                            /* 작은 글자 */
  background: #1e293b;                        /* 더 어두운 배경 */
  padding: 4px 8px;                           /* 안쪽 여백 */
  border-radius: 4px;                         /* 모서리 둥글기 */
}
</style>
</head>
<body>
<div class="env-demo">                        <!-- env() 시연 -->
  <div class="safe-area">                     <!-- 안전 영역 패딩 -->
    <div class="content">                     <!-- 콘텐츠 -->
      <p>safe-area-inset을 활용한 레이아웃</p>     <!-- 설명 -->
      <code>padding: env(safe-area-inset-top, 20px)</code>     <!-- 코드 예 -->
    </div>
  </div>
</div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.env-demo { padding: 16px; background: #f1f5f9; border-radius: 8px; }
.safe-area { background: #1e293b; border-radius: 16px; overflow: hidden; padding-top: env(safe-area-inset-top, 44px); padding-bottom: env(safe-area-inset-bottom, 34px); padding-left: env(safe-area-inset-left, 16px); padding-right: env(safe-area-inset-right, 16px); }
.content { background: #334155; border-radius: 8px; padding: 20px; }
.content p { color: white; font-size: 14px; margin-bottom: 8px; }
.content code { color: #67e8f9; font-size: 13px; background: #1e293b; padding: 4px 8px; border-radius: 4px; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 네 방향은 변수가 따로 있으므로 `padding` 단축 속성 하나가 아니라 방향별 선언 네 줄로 쓴다.
- fallback 은 변수가 정의되지 않았을 때만 쓰인다 — 정답 코드 주석의 「없으면 44px」은 「변수가 정의되지 않았으면」으로 읽는다.
- 변수가 0으로 정의된 화면이라면 위 여백이 0이 될 수 있다(확인 필요). 최소 여백을 지키려면 `max(16px, env(safe-area-inset-left))` 꼴로 바꾼다.
- 정답 코드에는 `viewport-fit=cover` meta 태그가 없다. 실제 노치 화면에서 효과를 보려면 그 meta 태그를 `<head>` 에 더해야 한다(원본 팁).
- `<code>` 안의 `env(safe-area-inset-top, 20px)` 는 화면에 보여 주는 글자일 뿐 스타일로 적용되지 않는다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

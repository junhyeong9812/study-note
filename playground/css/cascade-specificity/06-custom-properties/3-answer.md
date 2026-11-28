# css/cascade-specificity/06 — CSS Custom Properties (변수) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 배경은 `.dark` 의 값, 모서리는 `:root` 의 값

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`background` 는 `.dark` 가 준 `#60a5fa`, `border-radius` 는 `:root` 의 `8px` 이 된다.

**왜 그런가**

버튼의 부모 카드가 `.dark` 로 `--primary` 를 직접 선언했으므로 버튼은 그 값을 물려받는다.
`.dark` 는 `--radius` 를 다시 정하지 않았으므로 `html` 에서부터 내려온 `:root` 값이 그대로 버튼까지 물려진다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 4」.

### 2. `crimson` — 형제에게는 변수가 물려지지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`.note` 의 글자색은 `crimson` 이다.

**왜 그런가**

`--accent` 는 `.warning` 과 그 자손에게만 상속되고, 형제인 `.note` 에는 닿지 않는다.
`.note` 에서 `--accent` 는 정의되지 않은 변수이므로 `var()` 의 대체값이 쓰인다.
근거: 2-summary 「동작 방식 (3)」 · 「문법 — 형태와 규칙」의 대체값 규칙.

### 3. 10px 도 20px 도 아니다 — 초기값으로 떨어진다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`padding` 은 초기값인 0 이 된다.

**왜 그런가**

`--gap` 은 정의되어 있으므로 대체값 `20px` 은 쓰이지 않는다.
캐스케이드는 뒤에 온 `padding: var(--gap, 20px)` 를 이미 골랐으므로 앞의 `10px` 으로 돌아가지 않는다.
`red` 를 끼운 값은 `padding` 에 맞지 않아 계산된 값 시점에 무효가 되고, `padding` 은 상속되지 않는 속성이라 초기값이 된다.
근거: 2-summary 「어디서 틀리나 3」. (초기값이 0 이라는 점은 `padding` 의 일반 지식이다 — 원본에 근거 없음 — 추론)

### 4. 커스텀 속성은 기본으로 상속되고 `:root` 는 모든 요소의 조상이다

`:root` 는 문서 루트 `html` 이므로 모든 요소의 조상이다.
커스텀 속성은 기본으로 상속되므로, 중간 요소가 덮어쓰지 않는 한 그 값이 어떤 깊이의 자손까지 물려진다.
근거: 2-summary 「동작 방식 (2)」 · 원본 팁.

### 5. 명시도 겨루기가 아니라 「직접 선언 대 상속값」이다

`:root` 는 `html` 에, `.dark` 는 두 번째 카드에 붙는다 — 같은 요소를 두고 다투지 않는다.
다크 카드 입장에서 `.dark` 의 `--bg` 는 자기가 직접 선언한 값이고, `:root` 의 값은 부모에게서 물려받은 값이다.
직접 선언한 값은 물려받은 값보다 늘 앞선다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 2」.

### 6. 상속은 위에서 아래로만 흐르기 때문이다

`.dark` 가 준 값은 그 요소와 자손에게만 상속된다.
첫 번째 카드는 형제, `.theme-demo` 는 부모라서 `.dark` 의 영향 아래에 있지 않고 계속 `:root` 값을 본다.
그래서 같은 HTML 의 두 카드가 서로 다른 테마로 설 수 있다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 1」.

### 7. `initial-value` 를 본다

상속이 꺼졌으므로 자손은 `html` 의 값을 물려받지 않는다.
자손이 직접 선언하지 않았다면 등록할 때 준 `initial-value` 가 그 요소의 값이 된다.
원본 팁의 「상속되므로 `:root` 에 두면 전역」은 등록하지 않은 변수에만 맞는 말이다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 5」.

### 8. 클래스를 붙였다 떼거나 변수 값만 바꾼다 — 참조하는 쪽은 그대로다

JS 는 요소에 `dark` 클래스를 토글하거나 `style.setProperty('--primary', …)` 로 변수 값을 넣는다.
변수 값이 바뀌면 캐스케이드가 다시 일어나 `var()` 를 쓰는 모든 속성이 새 값으로 계산된다.
`.card` · `.btn` 은 색을 직접 갖지 않고 변수 이름만 참조하므로 고칠 줄이 없다.
근거: 2-summary 「동작 방식 (4)」.

## 실습 정답

### 실습 1. 같은 HTML 로 라이트/다크 카드 나란히 세우기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1단계 — 다섯 변수 정의 | `:root { --bg; --text; --primary; --surface; --radius }` |
| 2단계 — 네 변수만 다시 정의 | `.dark { --bg; --text; --primary; --surface }` |
| 3단계 — 카드의 배경 · 글자색 · 모서리 · 테두리 색 | `.card` 의 `background: var(--bg)` · `color: var(--text)` · `border-radius: var(--radius)` · `border: 1px solid var(--surface)` |
| 4단계 — 버튼의 배경 · 모서리 | `.card .btn` 의 `background: var(--primary)` · `border-radius: var(--radius)` |
| 5단계 — 두 번째 카드에만 `dark` | `<div class="card dark">` |
| 가로로 같은 너비 | `.theme-demo { display: flex; gap }` · `.card { flex: 1 }` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/cascade-specificity/reference/custom-properties.html`

```html
<!DOCTYPE html>
<!-- 문서 타입 선언: HTML5 -->
<html lang="ko">
<!-- HTML 루트: 문서 언어를 한국어로 지정 -->
<head>
<!-- 메타 정보 영역 -->
<meta charset="utf-8">
<!-- 문자 인코딩: UTF-8 -->
<title>CSS Custom Properties (변수) - --로 시작하는 커스텀 속성을 정의하고 var()로 참조하는 CSS 변수 시스템. 테마, 반복 값 관리, 동적 스타일링에 핵심</title>
<!--
  [캐스케이드 & 명시도] CSS Custom Properties (변수)
  설명: --로 시작하는 커스텀 속성을 정의하고 var()로 참조하는 CSS 변수 시스템. 테마, 반복 값 관리, 동적 스타일링에 핵심
  구문: --<name>: <value>;
property: var(--<name>, <fallback>);
  팁: 커스텀 속성은 상속되므로 :root에 정의하면 전역 사용 가능. @property로 타입, 초기값, 상속 여부를 명시적으로 선언할 수 있다.
-->
<style>
  /* :root: 문서 루트(html). 전역 테마 변수 정의 (특이도 0,1,0) */
  :root {
    --bg: #ffffff;              /* 배경색 변수: 흰색 */
    --text: #1e293b;            /* 글자색 변수: 진한 네이비 */
    --primary: #3b82f6;         /* 주요 색상 변수: 파랑 */
    --surface: #f1f5f9;         /* 표면 색상 변수: 연한 회색 */
    --radius: 8px;              /* 모서리 반경 변수: 8px */
  }

  /* .dark: 다크 테마 — 같은 변수명을 새 값으로 덮어 컴포넌트 영향 (특이도 0,1,0) */
  .dark {
    --bg: #1e293b;              /* 다크: 배경을 진한 네이비로 */
    --text: #f1f5f9;            /* 다크: 글자색을 밝은 회색으로 */
    --primary: #60a5fa;         /* 다크: 주요 색상을 밝은 파랑으로 */
    --surface: #334155;         /* 다크: 표면 색상을 회색 네이비로 */
  }

  /* .theme-demo: 테마 데모 컨테이너 (특이도 0,1,0) */
  .theme-demo {
    display: flex;              /* flex 레이아웃 */
    gap: 16px;                  /* 자식 간 간격 16px */
    padding: 16px;              /* 안쪽 여백 16px */
    background: #f8fafc;        /* 배경 매우 연한 회색 */
    border-radius: 8px;         /* 모서리 둥글게 8px */
  }
  /* .card: 카드 — 변수 사용 (특이도 0,1,0) */
  .card {
    flex: 1;                    /* 가용 공간 비율 1 */
    background: var(--bg);      /* 배경: --bg 변수 (라이트=흰색, 다크=네이비) */
    color: var(--text);         /* 글자색: --text 변수 */
    padding: 20px;              /* 안쪽 여백 20px */
    border-radius: var(--radius); /* 모서리: --radius 변수 (8px) */
    border: 1px solid var(--surface); /* 테두리: --surface 변수 */
  }
  /* .card h3: 카드 안 제목 (특이도 0,1,1) */
  .card h3 {
    margin-bottom: 8px;         /* 아래 외부 여백 8px */
    font-size: 18px;            /* 글자 크기 18px */
  }
  /* .card p: 카드 안 본문 (특이도 0,1,1) */
  .card p {
    margin-bottom: 16px;        /* 아래 외부 여백 16px */
    font-size: 14px;            /* 글자 크기 14px */
    opacity: 0.8;               /* 투명도 80% */
  }
  /* .card .btn: 카드 안 버튼 (특이도 0,2,0) */
  .card .btn {
    background: var(--primary); /* 배경: --primary 변수 (라이트=파랑, 다크=밝은 파랑) */
    color: white;               /* 글자색 흰색 */
    border: none;               /* 테두리 제거 */
    padding: 8px 20px;          /* 상하 8px, 좌우 20px */
    border-radius: var(--radius); /* 모서리: --radius 변수 */
    font-size: 14px;            /* 글자 크기 14px */
    font-weight: 600;           /* 굵기 600 */
    cursor: pointer;            /* 마우스 포인터 손가락 모양 */
  }
</style>
</head>
<body>
<!-- 문서 본문 -->
  <div class="theme-demo">
    <!-- 테마 데모 컨테이너 -->
    <div class="card">
      <!-- 라이트 테마 카드 — :root 변수 사용 -->
      <h3>라이트 테마</h3>
      <!-- 라이트 테마 제목 -->
      <p>CSS 변수로 테마 전환</p>
      <!-- 본문 -->
      <button class="btn">버튼</button>
      <!-- 라이트 버튼: --primary 파랑 -->
    </div>
    <div class="card dark">
      <!-- 다크 테마 카드 — .dark 클래스로 변수 덮어쓰기 -->
      <h3>다크 테마</h3>
      <!-- 다크 테마 제목 -->
      <p>같은 HTML, 변수만 변경</p>
      <!-- 본문 -->
      <button class="btn">버튼</button>
      <!-- 다크 버튼: --primary 밝은 파랑 -->
    </div>
  </div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
:root {
  --bg: #ffffff;
  --text: #1e293b;
  --primary: #3b82f6;
  --surface: #f1f5f9;
  --radius: 8px;
}

.dark {
  --bg: #1e293b;
  --text: #f1f5f9;
  --primary: #60a5fa;
  --surface: #334155;
}

.theme-demo { display: flex; gap: 16px; padding: 16px; background: #f8fafc; border-radius: 8px; }
.card {
  flex: 1;
  background: var(--bg);
  color: var(--text);
  padding: 20px;
  border-radius: var(--radius);
  border: 1px solid var(--surface);
}
.card h3 { margin-bottom: 8px; font-size: 18px; }
.card p { margin-bottom: 16px; font-size: 14px; opacity: 0.8; }
.card .btn {
  background: var(--primary);
  color: white;
  border: none;
  padding: 8px 20px;
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**

- 컴포넌트 규칙(`.card` · `.btn`)에는 색이 하나도 없고 변수 이름만 있다 — 테마는 변수 정의 쪽에서만 바뀐다.
- `.dark` 는 다크 카드 요소에 직접 선언되어, 그 카드와 안쪽 버튼 · 제목 · 문단에만 새 값이 퍼진다.
- `--radius` 를 `.dark` 에서 빼 두었기 때문에 두 카드의 모서리는 `:root` 값으로 같다.
- `:root` 와 `.dark` 의 명시도(둘 다 0,1,0)는 결과를 가르지 않는다 — 가르는 것은 상속 대 직접 선언이다.
- 보이는 결과(왼쪽 밝은 카드, 오른쪽 어두운 카드)는 코드에서 읽은 것이다 (코드에서 읽은 것 — 렌더 실측 아님).

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

# css/cascade-specificity/07 — Custom Properties scope — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 폴백 회색 `#94a3b8` — 카드 밖에는 `--accent` 가 없다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`.outside` 안의 `.badge` 배경은 `#94a3b8` (회색)이다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`.badge` 의 조상은 `.outside` → `.scope-demo` → `body` → `html(:root)` 이다.
이 가운데 `--accent` 를 선언한 요소가 없다.
`.card-a` 는 형제 쪽 가지라 값이 오지 않는다.
정의된 값이 없으니 `var()` 의 두 번째 인자인 폴백이 쓰인다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (3)」.

### 2. 바깥은 `crimson`, 카드 A 안은 파랑 — 폴백은 쓰이지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`.outside` 안의 `.badge` 는 `crimson`, `.card-a` 안의 `.badge` 는 `#3b82f6` (파랑)이다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`:root` 의 선언은 문서 전체로 상속된다.
그래서 `.outside` 안에서도 `--accent` 가 정의되어 있고, 폴백은 정의가 없을 때만 쓰이므로 무시된다.
`.card-a` 안에서는 더 가까운 조상 `.card-a` 가 같은 이름을 다시 선언해 `crimson` 을 덮는다.
근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (3)」 · 「어디서 틀리나 3」.

### 3. 안쪽 `.bar` 는 보라, 바깥 `.bar` 는 파랑 — 가장 가까운 조상이 이긴다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`.card-b` 안의 `.bar` 는 `#8b5cf6` (보라), `.card-a` 바로 아래의 `.bar` 는 `#3b82f6` (파랑)이다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
안쪽 `.bar` 의 조상 가운데 `--accent` 를 선언한 요소는 `.card-b` 와 `.card-a` 둘이다.
가장 가까운 `.card-b` 가 위에서 내려온 파랑을 덮어써 보라를 물려준다.
`.card-a` 바로 아래의 `.bar` 는 `.card-b` 의 자손이 아니므로 파랑을 받는다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 2」.

### 4. `var()` 는 그 요소가 물려받은 값을 읽기 때문이다

`.badge` 규칙은 값을 직접 갖지 않고 `var(--accent)` 로 「물려받은 `--accent`」를 읽으라고만 적는다.
카드 A 안의 뱃지는 `.card-a` 에서 파랑을, 카드 B 안의 뱃지는 `.card-b` 에서 보라를 물려받는다.
그래서 규칙 하나가 놓인 컴포넌트에 따라 다른 색을 낸다.
근거: 2-summary 「동작 방식 (2)」.

### 5. 뱃지 · 바는 카드 밖에도 놓이기 때문이다

`.badge` · `.bar` 선택자는 카드 안팎 어디서나 매칭된다 — 원본에서도 `.outside` 안에 뱃지가 있다.
카드 밖에는 `--accent` 가 없으므로 폴백이 있어야 안전하게 동작한다 (원본 팁).
`.card-a h4, .card-b h4` 는 늘 카드 안에서만 매칭되므로 `--accent` 를 반드시 물려받는다.
근거: 2-summary 「어디서 틀리나 4」 · 「동작 방식 (3)」.

### 6. 읽을 수 없다 — 형제는 상속의 길 밖에 있다

상속은 선언된 요소에서 자손으로만 흐른다.
카드 B 안의 요소는 카드 A 의 자손이 아니므로 `.card-a` 의 `--accent-light` 를 받지 못한다.
두 카드가 함께 써야 하는 값이면 공통 조상이나 `:root` 로 올린다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 1」.

### 7. 컴포넌트 안에 다른 컴포넌트를 넣었을 때다

형제 컴포넌트 사이는 격리되지만, 자손 쪽으로는 막히지 않는다.
카드 안에 넣은 안쪽 컴포넌트가 같은 이름을 다시 선언하지 않으면 바깥 카드의 값을 그대로 물려받는다.
즉 「컴포넌트 내에서만」은 「그 컴포넌트와 모든 자손에서」라는 뜻이다.
근거: 2-summary 「어디서 틀리나 2」 · 「동작 방식 (2)」.

### 8. 명시도가 높은 `.card-a.dark` 의 값이 내려간다

`--accent: …;` 도 보통 선언이라 한 요소에서 경쟁하면 캐스케이드로 이긴 쪽이 정해진다.
`.card-a.dark` 는 (0,2,0), `.card-a` 는 (0,1,0) 이므로 `.card-a.dark` 가 이긴다.
이긴 값이 그 카드의 `--accent` 가 되고, 자손은 그 값을 물려받는다.
근거: 2-summary 「동작 방식 (4)」.

## 실습 정답

### 실습 1. 같은 이름의 변수로 두 카드에 다른 강조색 입히기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. `:root` 에 `--global-radius` 선언 | `:root { --global-radius: 6px; }` |
| 2. 카드 · `.outside` 의 모서리가 전역 변수를 읽음 | `.card-a, .card-b` 와 `.outside` 의 `border-radius: var(--global-radius)` |
| 3. `.card-a` 의 파랑 계열 변수 | `.card-a { --accent; --accent-light }` |
| 4. `.card-b` 의 보라 계열 변수 | `.card-b { --accent; --accent-light }` |
| 5. 카드 배경 · 테두리 | `.card-a, .card-b` 의 `background: var(--accent-light)` · `border: 2px solid var(--accent)` |
| 6. 카드 제목 글자색 | `.card-a h4, .card-b h4 { color: var(--accent) }` |
| 7. 뱃지 · 바의 폴백 | `.badge` · `.bar` 의 `background: var(--accent, #94a3b8)` |
| 8. `.outside` 에 `--accent` 없음 | `.outside` 규칙에 `--accent` 선언이 없음 · `<div class="outside">` 안의 `.badge` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/cascade-specificity/reference/custom-properties-scope.html`

```html
<!DOCTYPE html>
<!-- 문서 타입 선언: HTML5 -->
<html lang="ko">
<!-- HTML 루트: 문서 언어를 한국어로 지정 -->
<head>
<!-- 메타 정보 영역 -->
<meta charset="utf-8">
<!-- 문자 인코딩: UTF-8 -->
<title>Custom Properties scope - 커스텀 속성은 CSS 상속을 따르므로 선언된 요소와 그 자식에서만 사용 가능. 컴포넌트 스코프 변수를 만들어 격리된 스타일링이 가능</title>
<!--
  [캐스케이드 & 명시도] Custom Properties scope
  설명: 커스텀 속성은 CSS 상속을 따르므로 선언된 요소와 그 자식에서만 사용 가능. 컴포넌트 스코프 변수를 만들어 격리된 스타일링이 가능
  구문: .component { --local-var: value; }
.component .child { property: var(--local-var); }
  팁: 컴포넌트의 루트 요소에 --변수를 정의하면 해당 컴포넌트 내에서만 적용. var()의 폴백 값을 활용하면 변수가 없는 컨텍스트에서도 안전하게 동작.
-->
<style>
  /* :root: 문서 루트(html). 전역 변수 선언 위치 (특이도 0,1,0) */
  :root {
    --global-radius: 6px;       /* 전역 변수: 모든 자식이 상속 가능 */
  }

  /* .card-a: 카드 A 컴포넌트 — 자체 스코프 변수 (특이도 0,1,0) */
  .card-a {
    --accent: #3b82f6;          /* 카드 A 전용 강조색: 파랑 (이 컴포넌트 안에서만 유효) */
    --accent-light: #dbeafe;    /* 카드 A 전용 밝은 강조색 */
  }
  /* .card-b: 카드 B 컴포넌트 — 같은 변수명이지만 다른 값 (스코프 격리) */
  .card-b {
    --accent: #8b5cf6;          /* 카드 B 전용 강조색: 보라 */
    --accent-light: #ede9fe;    /* 카드 B 전용 밝은 강조색 */
  }

  /* .scope-demo: 데모 최상위 컨테이너 (특이도 0,1,0) */
  .scope-demo {
    display: flex;              /* flex 레이아웃 */
    gap: 12px;                  /* 자식 간 간격 12px */
    padding: 16px;              /* 안쪽 여백 16px */
    background: #f1f5f9;        /* 배경 연한 회색 */
    border-radius: 8px;         /* 모서리 둥글게 8px */
    flex-wrap: wrap;            /* 자식이 넘치면 줄 바꿈 */
  }
  /* .card-a, .card-b: 두 카드 공통 스타일 (특이도 각각 0,1,0) */
  .card-a, .card-b {
    flex: 1;                    /* 가용 공간 비율 1 */
    min-width: 180px;           /* 최소 너비 180px */
    padding: 16px;              /* 안쪽 여백 16px */
    background: var(--accent-light); /* 배경: 각 카드의 --accent-light 변수 사용 */
    border: 2px solid var(--accent); /* 테두리: 각 카드의 --accent 변수 사용 */
    border-radius: var(--global-radius); /* 모서리: :root의 전역 변수 상속 */
  }
  /* .card-a h4, .card-b h4: 카드 내부 제목 (특이도 0,1,1) */
  .card-a h4, .card-b h4 {
    color: var(--accent);       /* 글자색: 부모 카드의 --accent 변수 (상속) */
    font-size: 14px;            /* 글자 크기 14px */
    margin-bottom: 12px;        /* 아래 외부 여백 12px */
  }
  /* .badge: 뱃지 — var의 폴백 값 시연 (특이도 0,1,0) */
  .badge {
    display: inline-block;      /* 인라인 블록 */
    background: var(--accent, #94a3b8); /* --accent가 없으면 회색 폴백 사용 */
    color: white;               /* 글자색 흰색 */
    padding: 4px 12px;          /* 상하 4px, 좌우 12px */
    border-radius: 999px;       /* 완전한 둥근 캡슐 모양 */
    font-size: 13px;            /* 글자 크기 13px */
    font-weight: 600;           /* 굵기 600 */
    margin-bottom: 8px;         /* 아래 외부 여백 8px */
  }
  /* .bar: 진행 바 — 폴백 값 활용 (특이도 0,1,0) */
  .bar {
    height: 6px;                /* 높이 6px */
    background: var(--accent, #94a3b8); /* --accent 없으면 회색 폴백 */
    border-radius: 3px;         /* 모서리 둥글게 3px */
  }
  /* .outside: 카드 밖의 컨테이너 — --accent 정의 없음, 폴백 발동 (특이도 0,1,0) */
  .outside {
    flex-basis: 100%;           /* flex 항목 기본 너비 100% */
    padding: 12px;              /* 안쪽 여백 12px */
    background: white;          /* 배경 흰색 */
    border-radius: var(--global-radius); /* 전역 변수 사용 */
    border: 1px dashed #cbd5e1; /* 점선 회색 테두리 */
  }
</style>
</head>
<body>
<!-- 문서 본문 -->
  <div class="scope-demo">
    <!-- 데모 컨테이너 -->
    <div class="card-a">
      <!-- 카드 A: --accent 파랑 스코프 -->
      <h4>카드 A (--accent: 파랑)</h4>
      <!-- 카드 A 제목: --accent 파랑 상속 -->
      <div class="badge">Badge</div>
      <!-- 카드 A 안의 뱃지: 파란 배경 -->
      <div class="bar"></div>
      <!-- 카드 A 안의 바: 파란 배경 -->
    </div>
    <div class="card-b">
      <!-- 카드 B: --accent 보라 스코프 -->
      <h4>카드 B (--accent: 보라)</h4>
      <!-- 카드 B 제목: --accent 보라 상속 -->
      <div class="badge">Badge</div>
      <!-- 카드 B 안의 뱃지: 보라 배경 -->
      <div class="bar"></div>
      <!-- 카드 B 안의 바: 보라 배경 -->
    </div>
    <div class="outside">
      <!-- 스코프 밖 컨테이너: --accent 정의 없음 -->
      <div class="badge">밖의 Badge (폴백 적용)</div>
      <!-- 폴백 회색이 적용된 뱃지 -->
    </div>
  </div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
:root {
  --global-radius: 6px;
}

.card-a {
  --accent: #3b82f6;
  --accent-light: #dbeafe;
}
.card-b {
  --accent: #8b5cf6;
  --accent-light: #ede9fe;
}

.scope-demo { display: flex; gap: 12px; padding: 16px; background: #f1f5f9; border-radius: 8px; flex-wrap: wrap; }
.card-a, .card-b { flex: 1; min-width: 180px; padding: 16px; background: var(--accent-light); border: 2px solid var(--accent); border-radius: var(--global-radius); }
.card-a h4, .card-b h4 { color: var(--accent); font-size: 14px; margin-bottom: 12px; }
.badge { display: inline-block; background: var(--accent, #94a3b8); color: white; padding: 4px 12px; border-radius: 999px; font-size: 13px; font-weight: 600; margin-bottom: 8px; }
.bar { height: 6px; background: var(--accent, #94a3b8); border-radius: 3px; }
.outside { flex-basis: 100%; padding: 12px; background: white; border-radius: var(--global-radius); border: 1px dashed #cbd5e1; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 변수 선언은 `:root` · `.card-a` · `.card-b` 세 곳뿐이고, 나머지 규칙은 `var()` 로 읽기만 한다.
- 두 카드는 같은 이름 `--accent` · `--accent-light` 를 쓰지만 형제라 값이 섞이지 않는다.
- 카드 자신도 자기 `border` 에 `var(--accent)` 를 쓴다 — 선언한 요소 자신에서도 읽을 수 있다.
- `.badge` · `.bar` 만 폴백을 단다 — 카드 밖에도 놓일 수 있는 부품이기 때문이다.
- `.outside` 안의 뱃지가 회색이 되려면 `:root` 를 포함한 어떤 조상에도 `--accent` 가 없어야 한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

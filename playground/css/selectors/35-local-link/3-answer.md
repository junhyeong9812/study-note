# css/selectors/35 — :local-link — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 「섹션 1」만 녹색 — 같은 문서를 가리키기 때문이다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
원본 설명대로라면 「섹션 1」은 녹색, 「외부 링크」는 회색이다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`#section1` 은 `page.html#section1` 로 풀려 문서 부분이 현재 URL 과 같고, `https://example.com` 은 다른 문서다.
다만 프래그먼트까지 비교하는 구현이라면 주소창에 `#section1` 이 없을 때 「섹션 1」도 회색일 수 있다 — 2-summary 「어디서 틀리나 3」.
근거: 2-summary 「동작 방식 (1)」.

### 2. 굵어지지 않는다 — 규칙 전체가 버려진다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`:local-link` 를 모르는 브라우저에서는 호버해도 글자가 굵어지지 않는다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
쉼표로 묶은 선택자 목록에서 하나라도 무효면 CSS 는 규칙 전체를 건너뛴다.
그래서 멀쩡한 `.ll-link:hover` 까지 함께 사라진다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 2」.

### 3. 페이지마다 「현재」 표시를 손으로 옮겨 달 필요가 없다

브라우저가 링크의 목적지와 현재 문서 URL 을 비교해 알아서 골라 주므로, 같은 네비게이션 코드를 모든 페이지에 그대로 써도 현재 페이지 링크만 강조된다.
`.current` 클래스는 페이지마다 어느 링크에 붙일지 사람이나 서버가 정해야 한다.
근거: 2-summary 「동작 방식 (3)」.

### 4. 지원하지 않는 브라우저에서는 강조가 아예 사라지기 때문이다

지원이 제한적이고, 모르는 브라우저는 그 규칙을 통째로 무시하므로 현재 페이지 표시가 보이지 않는다.
꼭 보여야 하면 `.current` 클래스나 `aria-current="page"` 속성 선택자 같은 방법을 함께 둔다.
근거: 2-summary 「어디서 틀리나 1」 · 「언제 쓰고 언제 안 쓰나」.

### 5. 현재 문서가 바로 `https://example.com` 일 때다

매칭 기준은 「외부냐 아니냐」가 아니라 「목적지 URL 이 현재 문서 URL 과 같으냐」다.
같은 `<nav>` 를 `https://example.com` 문서에 두면 그 링크가 현재 위치가 되어 매칭된다.
근거: 2-summary 「어디서 틀리나 5」 · 「동작 방식 (1)」.

### 6. 초안이 프래그먼트까지 같아야 한다고 적는 것으로 보이기 때문이다

Selectors Level 4 초안은 링크 목적지에 프래그먼트가 있으면 현재 URL 의 프래그먼트도 같아야 한다고 적는 것으로 보인다 (확인 필요).
그 읽기대로라면 `page.html` 에서는 `#section1` 링크가 매칭되지 않고 `page.html#section1` 에서만 매칭된다.
근거: 2-summary 「어디서 틀리나 3」.

### 7. `:local-link` 는 링크 자신, `:target` 은 목적지 섹션

`:local-link` 는 하이퍼링크의 출발점인 `<a href="#section1">` 에 걸린다.
`:target` 은 URL 프래그먼트와 같은 `id` 를 가진 요소, 곧 `id="section1"` 인 섹션에 걸린다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 4」.

### 8. `href` 가 없으면 링크가 아니기 때문이다

`:local-link` 는 하이퍼링크의 출발점에만 매칭되는데, `href` 없는 `<a>` 는 가리키는 목적지가 없어 링크로 치지 않는다.
비교할 목적지 URL 자체가 없으므로 후보에서 빠진다.
근거: 2-summary 「동작 방식 (2)」.

## 실습 정답

### 실습 1. 현재 위치를 강조하는 네비게이션

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 링크를 가로 한 줄로, 사이에 간격 | `.ll-nav { display: flex; gap: 8px; }` |
| 2. 같은 페이지 앵커 「섹션 1」 | `<a href="#section1" class="ll-link">섹션 1</a>` |
| 3. 외부 사이트 「외부 링크」 | `<a href="https://example.com" class="ll-link">외부 링크</a>` |
| 4. 밑줄 없는 회색 버튼 기본 모양 | `.ll-link { … text-decoration: none; background: … }` |
| 5. 현재 페이지 링크만 녹색 · 흰 글자 · 굵게 | `.ll-link:local-link { background: …; color: white; font-weight: bold; }` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/selectors/reference/local-link.html`

```html
<!DOCTYPE html>
<!-- 문서 타입 선언: HTML5 -->
<html lang="ko">
<head>
<meta charset="utf-8">
<title>:local-link - 현재 페이지와 같은 URL을 가리키는 링크에 적용된다 (같은 페이지 내 앵커 링크 등).</title>
<!--
  [선택자] :local-link
  설명: 현재 페이지와 같은 URL을 가리키는 링크에 적용된다 (같은 페이지 내 앵커 링크 등).
  구문: selector:local-link { }
  팁: 주의: :local-link는 아직 브라우저 지원이 제한적이다. 네비게이션에서 현재 페이지 링크를 하이라이트할 때 유용하다.
-->
<style>
  /* .ll-nav: class 속성에 ll-nav를 가진 요소 매칭 */
  .ll-nav {
    display: flex;               /* 플렉스 컨테이너 */
    gap: 8px;                    /* 자식 간 간격 8px */
  }
  /* .ll-link: class 속성에 ll-link를 가진 요소 매칭 */
  .ll-link {
    padding: 8px 16px;           /* 안쪽 여백 위아래 8, 좌우 16 */
    border-radius: 6px;          /* 6px 둥근 모서리 */
    text-decoration: none;       /* 밑줄 제거 */
    background: #f3f4f6;         /* 회색 배경 */
    color: #374151;              /* 진한 회색 텍스트 */
  }
  /* .ll-link:local-link: .ll-link 중 현재 페이지 URL을 가리키는 링크 매칭 */
  .ll-link:local-link {
    background: #22c55e;         /* 녹색 배경으로 현재 위치 강조 */
    color: white;                /* 흰색 텍스트 */
    font-weight: bold;           /* 굵게 */
  }
</style>
</head>
<body>
  <nav class="ll-nav">
    <!-- 같은 페이지 내 앵커 링크 (:local-link 매칭) -->
    <a href="#section1" class="ll-link">섹션 1</a>
    <!-- 외부 사이트 링크 (:local-link 매칭 안 됨) -->
    <a href="https://example.com" class="ll-link">외부 링크</a>
  </nav>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.ll-nav { display: flex; gap: 8px; }
.ll-link { padding: 8px 16px; border-radius: 6px; text-decoration: none; background: #f3f4f6; color: #374151; }
.ll-link:local-link { background: #22c55e; color: white; font-weight: bold; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 배울 핵심은 `.ll-link:local-link` 한 줄 — 클래스와 의사 클래스를 붙여 「네비 링크이면서 현재 문서를 가리키는 것」만 고른다.
- `#section1` 은 현재 문서로 풀리고, `https://example.com` 은 다른 문서라 기본 회색으로 남는다.
- 두 규칙이 겹치는 `background` · `color` 는 더 구체적인 `.ll-link:local-link` 가 이긴다.
- `:local-link` 규칙을 다른 선택자와 쉼표로 묶지 않았기 때문에, 지원하지 않는 브라우저에서도 기본 버튼 모양은 살아 있다.
- 프래그먼트 비교 방식에 따라 주소창의 `#section1` 유무가 결과를 바꿀 수 있다 (확인 필요).

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

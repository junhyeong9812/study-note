# css/selectors/56 — > 자식 결합자 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 2개 — 「직접 자식 1」과 「직접 자식 2」

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
매칭되는 `li` 는 「직접 자식 1」과 「직접 자식 2」 두 개다.
「손자」 `li` 는 매칭되지 않는다.

**왜 그런가**
`>` 는 `li` 의 바로 위 부모가 `.child-demo` 인지만 본다.
손자 `li` 의 부모는 class 가 없는 안쪽 `ul` 이라 조건에 맞지 않는다.
다만 손자는 연녹색 `li` 안에 들어 있어서, 화면에서는 그 연녹색이 뒤에 비쳐 보일 수 있다(매칭과는 다른 이야기다). (코드에서 읽은 것 — 렌더 실측 아님)
근거: 2-summary 「동작 방식 (1)」.

### 2. 굵게 보이고, 뒤로 연녹색이 비친다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
「손자」 글자는 굵게 보인다.
「손자」 줄 뒤에는 부모 `li` 의 연녹색이 보인다. (코드에서 읽은 것 — 렌더 실측 아님)

**왜 그런가**
`font-weight` 는 상속되는 속성이라 부모 `li` 의 `bold` 가 안쪽 `ul` 을 거쳐 손자까지 내려간다.
`background` 는 상속되지 않아 손자의 배경은 투명이다.
투명한 손자 뒤로 그것을 감싼 부모 `li` 의 연녹색이 보인다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 2」.

### 3. 고르지 않는다 — 한 겹만 끼어도 끊긴다

`.card > p` 는 `p` 의 바로 위 부모가 `.card` 여야 한다.
`section` 이 끼면 `p` 의 부모는 `section` 이므로 매칭되지 않는다.
근거: 2-summary 「어디서 틀리나 3」.

### 4. 맨 오른쪽 `li`(손자)

스타일을 받는 것은 언제나 맨 오른쪽 선택자에 맞는 요소다.
앞의 `.child-demo > li > ul` 은 그 손자 `li` 가 어디에 있어야 하는지를 정하는 조건일 뿐이다.
근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 4」.

### 5. 매칭은 막혀도 굵기는 상속으로 내려오기 때문이다

`>` 가 막는 것은 규칙이 손자에 직접 걸리는 것뿐이다.
`font-weight: bold` 는 부모 `li` 에서 상속으로 손자까지 흘러 들어온다.
그래서 손자 규칙에서 `font-weight: normal` 로 직접 되돌려야 보통 굵기가 된다.
근거: 2-summary 「동작 방식 (3)」.

### 6. 직접 매칭은 막지만 상속되는 속성은 못 막는다

`>` 를 쓰면 바깥 컴포넌트의 규칙이 안쪽 컴포넌트의 요소에 직접 걸리지 않는다 — 이 범위에서는 팁이 맞다.
그러나 `font-weight` · `color` 처럼 상속되는 속성은 바깥 요소에서 안쪽으로 그대로 흘러 들어간다.
또 안쪽 요소의 배경이 투명하면 바깥 배경이 비쳐 보인다.
근거: 2-summary 「어디서 틀리나 1 · 2」.

### 7. 「손자」 `li` 가 새로 걸린다

띄어쓰기는 깊이와 상관없이 `.child-demo` 안의 `li` 를 모두 고른다.
그래서 「직접 자식 1 · 2」에 더해 「손자」도 걸려 세 개가 된다.
근거: 2-summary 「동작 방식 (4)」.

### 8. `list-style` 은 닿고 `padding` 은 닿지 않는다

`list-style` 은 상속되는 속성이라 안쪽 목록의 마커도 사라진다.
`padding` 은 상속되지 않아 안쪽 `ul` 은 브라우저 기본 들여쓰기를 그대로 가진다.
근거: 2-summary 「어디서 틀리나 5」.

## 실습 정답

### 실습 1. 중첩 목록을 깊이별로 다르게 꾸미기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. HTML 구조 | `<ul class="child-demo">` 아래 `li` 두 개, 첫 `li` 안의 `ul` > `li`(손자) |
| 2. 마커 제거 · 안쪽 여백 0 | `.child-demo { list-style: none; padding: 0; }` |
| 3. 직계 자식 `li` 카드 꾸밈 | `.child-demo > li { … font-weight: bold; }` |
| 4. 직계 자식 `ul` 위쪽 여백 | `.child-demo > li > ul { margin-top: … }` |
| 5. 손자 회색 배경 · 굵기 되돌리기 | `.child-demo > li > ul > li { background: …; font-weight: normal; }` |
| 6. `>` 만 쓰기 | 네 선택자 모두 `>` 로만 이어짐 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/selectors/reference/combinator-child.html`

```html
<!DOCTYPE html>
<!-- 문서 타입 선언: HTML5 -->
<html lang="ko">
<head>
<meta charset="utf-8">
<title>> 자식 결합자 - 첫 번째 요소의 직접 자식인 두 번째 요소만 선택한다.</title>
<!--
  [선택자] > 자식 결합자
  설명: 첫 번째 요소의 직접 자식인 두 번째 요소만 선택한다.
  구문: A > B { }
  팁: 컴포넌트 스타일링 시 > 결합자를 사용하면 하위 컴포넌트에 스타일이 침투하는 것을 방지할 수 있다.
-->
<style>
  /* .child-demo: class 속성에 child-demo를 가진 요소 매칭 */
  .child-demo {
    list-style: none;            /* 기본 리스트 마커 제거 */
    padding: 0;                  /* 안쪽 여백 0 */
  }
  /* .child-demo > li: .child-demo의 직계 자식 li만 매칭 (손자 li는 제외) */
  .child-demo > li {
    padding: 10px;               /* 안쪽 여백 10px */
    background: #dcfce7;         /* 연녹색 배경 */
    margin: 4px 0;               /* 위아래 4px 마진 */
    border-radius: 6px;          /* 6px 둥근 모서리 */
    font-weight: bold;           /* 굵게 */
  }
  /* .child-demo > li > ul: 직계 자식 li의 직계 자식 ul 매칭 */
  .child-demo > li > ul {
    margin-top: 8px;             /* 위쪽 마진 8px */
  }
  /* .child-demo > li > ul > li: 3단계 직계 자식 체인의 li 매칭 (손자 li) */
  .child-demo > li > ul > li {
    background: #f3f4f6;         /* 손자는 회색 배경 */
    font-weight: normal;         /* 굵기 정상 */
  }
</style>
</head>
<body>
  <ul class="child-demo">
    <!-- 직접 자식 li (연녹색) -->
    <li>직접 자식 1
      <!-- 중첩 ul -->
      <ul>
        <!-- 손자 li (회색) -->
        <li>손자</li>
      </ul>
    </li>
    <!-- 직접 자식 li (연녹색) -->
    <li>직접 자식 2</li>
  </ul>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.child-demo { list-style: none; padding: 0; }
.child-demo > li { padding: 10px; background: #dcfce7; margin: 4px 0; border-radius: 6px; font-weight: bold; }
.child-demo > li > ul { margin-top: 8px; }
.child-demo > li > ul > li { background: #f3f4f6; font-weight: normal; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- `.child-demo > li` 는 손자 `li` 를 고르지 않는다 — 부모가 `.child-demo` 가 아니기 때문이다.
- 깊이마다 `>` 를 하나씩 더해 1 · 2 · 3단계를 따로 짚었다.
- 손자의 `font-weight: normal` 은 상속으로 내려온 `bold` 를 되돌리는 줄이다.
- 손자의 회색 배경은 투명한 배경 뒤로 부모의 연녹색이 비치는 것을 덮는다.
- `list-style: none` 은 상속으로 안쪽 목록까지 닿지만, `padding: 0` 은 바깥 `ul` 에만 적용된다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

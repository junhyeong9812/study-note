# css/at-rules/14 — @color-profile — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 아니다 — 배경은 여전히 내장 `display-p3` 을 쓴다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
주석을 풀어도 `.cp-demo` 의 배경은 그 ICC 파일과 상관없이 내장 Display P3 색 공간으로 칠해진다.

**왜 그런가**
정의한 이름은 `--display-p3` 이고, 배경은 `--` 없는 `display-p3` 을 부른다.
`--` 가 없는 이름은 내장 색 공간을 가리키므로 정의한 프로파일이 쓰이지 않는다.
쓰게 하려면 `color(--display-p3 0.2 0.5 1)` 로 적어야 한다.
게다가 주소도 예시용이라 실제 파일이 아니다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 1 · 4」

### 2. 같은 색이 아니다 — 숫자의 뜻을 색 공간이 정한다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
두 상자 모두 파란색 계열이지만 같은 색이 아니다.

**왜 그런가**
`0.2 0.5 1` 은 「그 색 공간에서의 채널 비율」이다.
기준이 Display P3 와 sRGB 로 다르므로 가리키는 실제 색도 다르다.
화면에서 그 차이가 얼마나 보이는지는 화면이 넓은 영역을 낼 수 있느냐에 달려 있다 (코드에서 읽은 것 — 렌더 실측 아님).
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 5」

### 3. 아무것도 달라지지 않는다

`@color-profile` 은 색 공간을 정의해 등록할 뿐이다.
`color(--brand …)` 로 부르는 선언이 없으면 어떤 요소의 색도 바뀌지 않는다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 2」

### 4. 파일 없이 바로 쓸 수 있기 때문이다

내장 색 공간(`display-p3` · `srgb` · `rec2020`)은 브라우저에 이미 정의되어 있어 정의 규칙도, ICC 파일 다운로드도, 경로 관리도 필요 없다.
원본의 팁도 내장 색 공간과 `color()` 가 더 실용적이라고 말하고, 원본 예제도 그렇게 한다.
근거: 2-summary 「어디서 틀리나 3」 · 「언제 쓰고 언제 안 쓰나」

### 5. 내장 색 공간 이름과 구별하기 위해서다

`color()` 의 첫 자리에는 내장 이름(`display-p3` 등)도 오고 정의한 이름도 온다.
`--` 로 시작하면 「사용자가 정의한 것」임이 드러나 내장 이름과 겹치지 않는다.
그래서 `--display-p3` 과 `display-p3` 이 다른 이름으로 공존할 수 있다.
근거: 2-summary 「동작 방식 (2)」 (구별 목적이라는 설명은 원본에 근거 없음 — 추론)

### 6. 내장 목록에 없는 특정 프로파일이 꼭 필요할 때다

인쇄용 프로파일처럼 `display-p3` · `srgb` · `rec2020` 같은 내장 색 공간에 없는 색 공간을 정확히 따라야 할 때 ICC 파일을 `src` 로 불러온다.
그 밖의 넓은 영역 색은 내장 색 공간으로 충분하다.
근거: 2-summary 「동작 방식 (1)」 · 「언제 쓰고 언제 안 쓰나」

### 7. 「외부 파일 + 이름 등록 → 다른 속성에서 이름으로 사용」이 같다

`@font-face` 는 `src` 로 글꼴 파일을 불러와 이름을 붙이고, `font-family` 에서 그 이름으로 쓴다.
`@color-profile` 은 `src` 로 ICC 파일을 불러와 `--이름` 을 붙이고, `color()` 에서 그 이름으로 쓴다.
둘 다 정의 규칙만으로는 화면이 바뀌지 않는다.
근거: 2-summary 「동작 방식 (1) · (2)」 (`@font-face` 와의 대응은 원본에 근거 없음 — 추론)

## 실습 정답

### 실습 1. 넓은 색 영역의 파란 상자 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| `cp-demo` 상자와 글자 | `<div class="cp-demo">Wide Gamut Color</div>` |
| `display-p3` 의 `0.2 0.5 1` 배경 | `.cp-demo { background: color(display-p3 0.2 0.5 1); }` |
| 주석으로 막은 `@color-profile` 규칙 | `/* @color-profile --display-p3 { src: url(…); } */` |
| 흰 굵은 글씨 | `.cp-demo` 의 `color` · `font-weight` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/at-rules/reference/color-profile.html`

```html
<!DOCTYPE html>
<!-- DOCTYPE 선언: HTML5 문서임을 알림 -->
<html lang="ko">
<!-- html 루트 요소: 문서 언어를 한국어로 지정 -->
<head>
  <!-- head: 메타데이터/스타일 영역 -->
  <meta charset="utf-8">
  <!-- meta charset: 문자 인코딩을 UTF-8로 지정 -->
  <title>@color-profile - ICC 색상 프로파일을 정의하여 color() 함수에서 사용할 수 있게 한다. 넓은 색 영역(wide gamut)을 지원한다.</title>
  <!-- title: 브라우저 탭 제목 -->
  <!--
    [At-규칙] @color-profile
    설명: ICC 색상 프로파일을 정의하여 color() 함수에서 사용할 수 있게 한다. 넓은 색 영역(wide gamut)을 지원한다.
    구문: @color-profile --<name> { src: url(<icc-file>); }
    팁: ICC 프로파일을 직접 로드하는 대신 CSS의 내장 색 공간(display-p3, srgb, rec2020 등)과 color() 함수를 사용하는 것이 더 실용적이다.
  -->
  <style>
    /* @color-profile --display-p3: ICC 프로파일 파일을 불러와 사용자 정의 색 공간을 정의 (개념 시연 - 주석 처리) */
    /* @color-profile --display-p3 {
      src: url('https://example.com/Display-P3.icc');
    } */

    /* .cp-demo: 넓은 색 영역(P3) 색상으로 채워진 데모 박스 */
    .cp-demo {
      padding: 20px;                              /* 사방 20px 내부 여백 */
      background: color(display-p3 0.2 0.5 1);    /* color() 함수: display-p3 색 공간에서 R0.2 G0.5 B1.0 (sRGB 영역을 넘는 선명한 파랑) */
      color: white;                               /* 글자색 - 흰색 */
      border-radius: 8px;                         /* 모서리 8px 둥글게 */
      font-weight: bold;                          /* 글자 굵게 */
    }
  </style>
</head>
<body>
  <!-- body: 화면에 보이는 콘텐츠 -->
  <div class="cp-demo">Wide Gamut Color</div>
  <!-- 넓은 색 영역 색상이 적용된 박스 -->
</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
/* @color-profile --display-p3 {
  src: url('https://example.com/Display-P3.icc');
} */

.cp-demo { padding: 20px; background: color(display-p3 0.2 0.5 1); color: white; border-radius: 8px; font-weight: bold; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 색 공간은 `color()` 의 첫 자리 이름이 정한다 — 여기서는 내장 `display-p3` 이다.
- `@color-profile` 규칙은 정의 형태만 보이려고 주석으로 둔다.
- 주석 속 이름 `--display-p3` 은 배경의 `display-p3` 과 다른 이름이라 풀어도 배경에 쓰이지 않는다.
- 원본 팁대로 ICC 파일 없이 내장 색 공간만으로 넓은 영역의 색을 지정했다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

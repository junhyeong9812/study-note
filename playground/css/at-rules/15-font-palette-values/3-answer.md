# css/at-rules/15 — @font-palette-values — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 바뀌지 않는다 — 정의만 있고 적용이 없다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
🎨 는 정의 전과 같은 색으로 그려진다.

**왜 그런가**
`@font-palette-values` 는 이름 붙은 팔레트를 정의할 뿐이다.
`.fpv-demo` 에 `font-palette: --custom-palette;` 가 없으니 그 팔레트를 쓰는 글자가 없다.
근거: 2-summary 「동작 방식 (2)」, 「어디서 틀리나 1」.

### 2. 0번 · 2번은 내장 팔레트 0의 색 그대로다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
1번 색만 새 색으로 그려지고, 0번 색과 2번 색은 내장 팔레트 0번에 있던 색 그대로 그려진다.
(대상 폰트가 쓰이고 팔레트를 지원하는 환경일 때 — 렌더 실측 아님)

**왜 그런가**
`base-palette: 0` 이 출발점을 정하고, `override-colors` 는 적힌 번호만 바꾼다.
적지 않은 번호는 출발 팔레트의 색을 물려받는다.
근거: 2-summary 「동작 방식 (3)」.

### 3. 평소 이모지 색 그대로다 — 둘 다 주석이다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
연회색 둥근 상자 안에 24px 글자로 「🎨 컬러 폰트 팔레트」가 보이고, 🎨 는 그 환경의 기본 이모지 색 그대로다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
팔레트 정의도, `font-palette` 적용 줄도 주석 안에 있어 브라우저는 둘 다 읽지 않는다.
남은 것은 `font-size` · `padding` · `background` · `border-radius` 꾸밈뿐이다.
근거: 2-summary 「동작 방식 (2)」 마지막 줄.

### 4. 색 번호의 뜻이 폰트마다 다르기 때문이다

「0번 색」이 무엇을 칠하는지는 폰트가 정한다.
같은 번호가 한 폰트에선 얼굴색이고 다른 폰트에선 배경색일 수 있으니, 정의는 하나의 대상 폰트에 묶여야 뜻이 생긴다.
또 정의의 `font-family` 와 실제로 그려지는 폰트가 맞아야 팔레트가 연결된다.
근거: 2-summary 「동작 방식 (4)」, 「어디서 틀리나 4 · 5」.

### 5. 앞은 팔레트 번호, 뒤는 색 번호다

`base-palette: 0` 의 0 은 「폰트 안의 첫 번째 팔레트」다.
`override-colors: 0 #ff6b6b` 의 0 은 「고른 팔레트 안의 첫 번째 색」이다.
둘 다 0부터 세지만 세는 대상이 다르다.
근거: 2-summary 「동작 방식 (3)」, 「어디서 틀리나 3」.

### 6. 아무 변화가 없다

단색 폰트에는 바꿀 내장 팔레트가 없다.
게다가 그 글자는 정의의 대상 폰트('Noto Color Emoji')로 그려지지 않으니 팔레트가 연결되지도 않는다.
원본 팁대로 이 규칙은 주로 컬러 이모지 폰트나 OpenType-SVG 폰트에서 쓰인다.
근거: 2-summary 「동작 방식 (4)」, 「어디서 틀리나 2」.

### 7. 둘 다 이름 붙은 정의를 만들고 속성으로 불러 쓴다

`@keyframes 이름` 은 움직임을 정의하고 `animation-name: 이름` 으로 불러야 움직인다.
`@font-palette-values --이름` 은 팔레트를 정의하고 `font-palette: --이름` 으로 불러야 색이 바뀐다.
둘 다 정의만으로는 화면이 바뀌지 않는다.
근거: 2-summary 「동작 방식 (2)」.

## 실습 정답

### 실습 1. 컬러 이모지 팔레트를 정의하고 적용하는 데모 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| `fpv-demo` 문단 | `<p class="fpv-demo">🎨 컬러 폰트 팔레트</p>` |
| `--custom-palette` 정의 | `@font-palette-values --custom-palette { … }` (주석 안) |
| 대상 폰트 | `font-family: 'Noto Color Emoji';` |
| 출발 팔레트 0 | `base-palette: 0;` |
| 0번 · 1번 색 바꾸기 | `override-colors: 0 #ff6b6b, 1 #4ecdc4;` |
| 팔레트 적용 | `.fpv-demo` 안의 `/* font-palette: --custom-palette; */` |
| 개념 시연으로 주석 처리 | 정의 블록 전체와 `font-palette` 줄을 감싼 `/* … */` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/at-rules/reference/font-palette-values.html`

```html
<!DOCTYPE html>
<!-- DOCTYPE 선언: HTML5 문서임을 알림 -->
<html lang="ko">
<!-- html 루트 요소: 문서 언어를 한국어로 지정 -->
<head>
  <!-- head: 메타데이터/스타일 영역 -->
  <meta charset="utf-8">
  <!-- meta charset: 문자 인코딩을 UTF-8로 지정 -->
  <title>@font-palette-values - 컬러 폰트의 색상 팔레트를 커스터마이즈한다. 폰트에 내장된 색상을 오버라이드할 수 있다.</title>
  <!-- title: 브라우저 탭 제목 -->
  <!--
    [At-규칙] @font-palette-values
    설명: 컬러 폰트의 색상 팔레트를 커스터마이즈한다. 폰트에 내장된 색상을 오버라이드할 수 있다.
    구문: @font-palette-values --<name> { font-family: <family>; override-colors: <index> <color>; }
    팁: 주로 컬러 이모지 폰트나 OpenType-SVG 폰트에서 사용된다. base-palette로 기본 팔레트를 선택하고 override-colors로 개별 색상을 변경할 수 있다.
  -->
  <style>
    /* @font-palette-values --custom-palette: 컬러 폰트의 내장 팔레트를 커스텀 색상으로 덮어쓰는 정의 (개념 시연 - 주석 처리) */
    /* @font-palette-values --custom-palette {
      font-family: 'Noto Color Emoji';
      base-palette: 0;
      override-colors: 0 #ff6b6b, 1 #4ecdc4;
    } */

    /* .fpv-demo: 커스텀 폰트 팔레트 적용 예시 박스 */
    .fpv-demo {
      font-size: 24px;             /* 글자 크기 24px */
      padding: 16px;               /* 사방 16px 내부 여백 */
      background: #f3f4f6;         /* 배경색 - 연회색 */
      border-radius: 8px;          /* 모서리 8px 둥글게 */
      /* font-palette: --custom-palette; */ /* 위에서 정의한 팔레트 적용 (주석 처리됨) */
    }
  </style>
</head>
<body>
  <!-- body: 화면에 보이는 콘텐츠 -->
  <p class="fpv-demo">🎨 컬러 폰트 팔레트</p>
  <!-- 컬러 폰트 팔레트 데모 문단 -->
</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
/* @font-palette-values --custom-palette {
  font-family: 'Noto Color Emoji';
  base-palette: 0;
  override-colors: 0 #ff6b6b, 1 #4ecdc4;
} */

.fpv-demo { font-size: 24px; padding: 16px; background: #f3f4f6; border-radius: 8px; /* font-palette: --custom-palette; */ }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 정의(`@font-palette-values`)와 적용(`font-palette`)은 따로 쓰고 같은 `--` 이름으로 잇는다.
- `base-palette` 는 팔레트 번호, `override-colors` 의 앞 숫자는 색 번호다.
- 여러 색은 `번호 색` 쌍을 쉼표로 이어 한 줄에 적는다.
- 정답 코드는 두 부분이 주석이라 화면에는 꾸밈만 적용된 상자가 보인다.
- 주석을 풀어도 대상 폰트가 쓰이고 팔레트를 지원하는 환경이어야 색 변화가 보인다 (원본에 근거 없음 — 추론).

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

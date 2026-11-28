# css/at-rules/12 — @counter-style — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 다섯째는 🔴, 여섯째는 🟡 — 처음으로 돌아간다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
1~4번째가 🔴 🟡 🟢 🔵 를 쓰고, 5번째는 🔴, 6번째는 🟡 가 붙는다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`cyclic` 은 심볼을 순환 반복한다.
심볼이 넷이므로 넷째 다음에는 목록의 처음으로 돌아가 다시 쓴다.
근거: 2-summary 「동작 방식 (2)」.

### 2. 폴백 스타일이 만든다 — `fixed` 는 기호를 한 번씩만 쓴다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
1~4번째는 🔴 🟡 🟢 🔵 이고, 5번째와 6번째는 이모지가 아닌 폴백 스타일의 마커가 붙는다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`fixed` 는 심볼을 한 번만 사용하고 그 이후에는 폴백으로 전환된다.
심볼 넷을 다 쓴 뒤의 번호는 이 카운터 스타일이 맡지 않는다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 2」.

### 3. `[🔴] ` — `prefix` + 기호 + `suffix`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
첫째 항목의 마커 문자열은 `[🔴] ` (끝에 공백 한 칸)이다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
마커는 `prefix` 문자열, 기호, `suffix` 문자열을 차례로 이어 붙여 만든다.
`'['` + `'🔴'` + `'] '` 이므로 괄호로 감싼 이모지 뒤에 공백이 온다.
근거: 2-summary 「동작 방식 (4)」.

### 4. 정의는 만드는 법일 뿐, 목록에 붙이는 일은 `list-style-type` 이 한다

`@counter-style` 은 이름 붙은 카운터 스타일을 등록할 뿐 어느 목록에 쓸지는 정하지 않는다.
목록이 마커를 그릴 때는 `list-style-type` 에 적힌 이름을 찾아 그 규칙을 쓴다.
이름을 부르지 않으면 목록은 원래의 기본 마커를 그대로 쓴다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 1」.

### 5. 마커가 들어갈 공간을 확보하려고

원본 코드 주석이 밝히듯 `padding-left: 40px` 는 마커 공간을 확보하는 들여쓰기다.
이모지 마커는 숫자 한 글자보다 넓을 수 있으므로 왼쪽 여백을 넉넉히 둔다.
근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 5」.

### 6. `cyclic` 을 고른다 — 다만 마커로는 순서를 읽을 수 없다

항목 수가 정해지지 않았다면 `cyclic` 이어야 끝까지 직접 정한 기호만 나온다.
`fixed` 는 기호를 다 쓴 뒤 폴백으로 넘어가 다른 모양이 섞인다.
대신 `cyclic` 은 같은 마커를 되풀이하므로(심볼이 넷이면 1번과 5번이 같다) 마커만 보고 몇 번째인지 알 수 없다.
근거: 2-summary 「어디서 틀리나 2 · 3」 · 「언제 쓰고 언제 안 쓰나」.

### 7. 보장하지 않는다 — 생김새는 글꼴과 운영체제가 정한다

CSS 가 정하는 것은 「어느 번호에 어느 심볼 문자열을 붙이나」까지다.
그 문자열이 화면에서 어떤 그림으로 보일지는 글꼴과 운영체제에 달렸다.
근거: 2-summary 「구현 세부사항 대 언어 보장」.

### 8. 하나는 정의, 하나는 사용 — 이름으로 이어진다

`@counter-style` 은 `system` · `symbols` · `prefix` · `suffix` · `range` 로 마커를 만드는 규칙을 정의하고 이름을 붙인다.
`list-style-type` 은 목록이 어떤 카운터 스타일로 마커를 그릴지 고른다.
둘을 잇는 것은 `@counter-style` 뒤에 지은 이름이며, `list-style-type` 에 같은 이름을 적어야 연결된다.
근거: 2-summary 「동작 방식 (1)」 · 「문법 — 형태와 규칙」.

## 실습 정답

### 실습 1. 이모지 네 개를 돌려 쓰는 목록 마커 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| `emoji-counter` 카운터 스타일 정의 | `@counter-style emoji-counter { … }` |
| 심볼을 순환 반복 | `system: cyclic;` |
| 🔴 🟡 🟢 🔵 네 심볼 | `symbols: '🔴' '🟡' '🟢' '🔵';` |
| 마커 뒤 공백 한 칸 | `suffix: ' ';` |
| `.custom-counter` 가 이 스타일을 씀 | `.custom-counter { list-style-type: emoji-counter; }` |
| 네 항목이 차례로 네 색 마커를 받음 | `<ol class="custom-counter">` 안의 `<li>` 넷 + `cyclic` 순서 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/at-rules/reference/counter-style.html`

```html
<!DOCTYPE html>
<!-- DOCTYPE 선언: HTML5 문서임을 알림 -->
<html lang="ko">
<!-- html 루트 요소: 문서 언어를 한국어로 지정 -->
<head>
  <!-- head: 메타데이터/스타일 영역 -->
  <meta charset="utf-8">
  <!-- meta charset: 문자 인코딩을 UTF-8로 지정 -->
  <title>@counter-style - 사용자 정의 카운터(목록 번호매기기) 스타일을 만든다.</title>
  <!-- title: 브라우저 탭 제목 -->
  <!--
    [At-규칙] @counter-style
    설명: 사용자 정의 카운터(목록 번호매기기) 스타일을 만든다.
    구문: @counter-style <name> { system: <type>; symbols: <symbols>; }
    팁: system: cyclic은 심볼을 순환 반복한다. system: fixed는 한 번만 사용하고 이후에는 폴백으로 전환된다.
  -->
  <style>
    /* @counter-style emoji-counter: 이모지를 순환시키는 사용자 정의 목록 카운터 */
    @counter-style emoji-counter {
      system: cyclic;                       /* 시스템 타입: cyclic - 심볼들을 순환 반복하며 사용 */
      symbols: '🔴' '🟡' '🟢' '🔵';         /* 사용할 심볼 목록 - 빨/노/초/파 원 이모지 */
      suffix: ' ';                          /* 심볼과 항목 텍스트 사이의 구분자 - 공백 1칸 */
    }

    /* .custom-counter: 사용자 정의 카운터를 적용한 ol 목록 */
    .custom-counter {
      list-style-type: emoji-counter;       /* 위에서 정의한 emoji-counter를 마커로 사용 */
      padding-left: 40px;                   /* 왼쪽 40px 들여쓰기 - 마커 공간 확보 */
    }

    /* .custom-counter li: 목록 항목 스타일 */
    .custom-counter li {
      padding: 6px 0;                       /* 위아래 6px 여백 - 항목 간 간격 */
      font-size: 16px;                      /* 글자 크기 16px */
    }
  </style>
</head>
<body>
  <!-- body: 화면에 보이는 콘텐츠 -->
  <ol class="custom-counter">
    <!-- 이모지 마커가 순환 적용된 ordered list -->
    <li>첫 번째</li>
    <!-- 1번째 항목 - 빨강 마커 -->
    <li>두 번째</li>
    <!-- 2번째 항목 - 노랑 마커 -->
    <li>세 번째</li>
    <!-- 3번째 항목 - 초록 마커 -->
    <li>네 번째</li>
    <!-- 4번째 항목 - 파랑 마커 -->
  </ol>
</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
@counter-style emoji-counter {
  system: cyclic;
  symbols: '🔴' '🟡' '🟢' '🔵';
  suffix: ' ';
}

.custom-counter { list-style-type: emoji-counter; padding-left: 40px; }
.custom-counter li { padding: 6px 0; font-size: 16px; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- `@counter-style` 블록은 규칙을 정의할 뿐이고, `list-style-type: emoji-counter;` 가 있어야 목록에 적용된다.
- `system: cyclic` 이므로 항목이 넷을 넘어도 심볼이 처음부터 다시 돈다.
- `symbols` 의 나열 차례가 그대로 마커 차례가 된다.
- `suffix: ' '` 이 이모지와 항목 글자 사이의 간격을 만든다.
- `padding-left` 는 넓은 이모지 마커가 들어갈 자리를 확보한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

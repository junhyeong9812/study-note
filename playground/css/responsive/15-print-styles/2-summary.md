# css/responsive/15 — Print Styles — 정리 (힌트)

> 출처 — study-site 항목 `css/print-styles`(항목 데이터 `data/css/responsive.json`) · 정답 코드 study-practice `css/responsive/reference/print-styles.html`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

## 한눈에 — 쉽게 말하면

**인쇄 스타일은 「발표 자료를 종이 유인물로 뽑을 때 따로 다듬는 일」이다.**
화면용 슬라이드에는 넘기기 버튼, 메뉴, 어두운 배경이 있다.
그대로 종이에 뽑으면 버튼은 눌리지 않고, 배경은 잉크만 먹고, 링크는 어디로 가는지 알 수 없다.
그래서 유인물용으로는 버튼을 지우고, 배경을 흰색으로 바꾸고, 링크 옆에 주소를 적는다.
웹 페이지도 똑같은 구조다.
화면 스타일은 그대로 두고, 인쇄할 때만 켜지는 규칙 묶음(`@media print`)을 하나 더 둔다.

| 비유 | 실체 |
|---|---|
| 화면용 슬라이드 | 평소의 CSS(화면 스타일) |
| 유인물용 수정본 | `@media print { … }` 블록 또는 `<link media="print">` 파일 |
| 버튼 · 메뉴 지우기 | `nav, footer, .no-print { display: none !important; }` |
| 링크 옆에 주소 적기 | `a[href]::after { content: " (" attr(href) ")"; }` |
| 어두운 배경 걷어내기 | `background: none !important;` · `color: #000 !important;` |
| 종이 여백 · 쪽 나누기 | `@page { margin: … }` · `break-before` · `break-after` · `break-inside` |

```text
          같은 HTML
              │
     ┌────────┴────────┐
  화면에 그릴 때     인쇄할 때(Ctrl+P)
     │                 │
  화면 규칙만       화면 규칙 + @media print 규칙
     │                 │
  메뉴·배경·색 있음   메뉴 숨김 · 배경 없음 · 검정 글자 · 링크 주소 표시
```

## 이 주제가 답하려는 질문

1. 같은 페이지를 화면과 종이에서 다르게 보이게 하려면 규칙을 어디에 써야 하나?
2. 종이에서 쓸모없는 것(메뉴 · 버튼 · 푸터)은 어떻게 빼나?
3. 종이에서는 클릭할 수 없는 링크의 목적지를 어떻게 알려 주나?
4. 제목만 한 쪽 끝에 남거나 표가 두 쪽으로 잘리는 일을 어떻게 막나?

## 동작 방식

### (1) 인쇄 때만 켜지는 규칙 — `@media print`

**언제 쓰나** — 화면 모습은 그대로 두고, 인쇄 결과만 바꾸고 싶을 때.

```text
입력 코드                                  무엇이 일어나나                     결과
.nav { color: red; }                    → 화면 · 인쇄 모두에 적용            → 화면: 빨간 메뉴
@media print {                          → 매체가 print 일 때만 블록이 켜짐    → 인쇄: 메뉴 없음
  .nav { display: none !important; }
}
```

- 브라우저는 페이지를 그릴 매체(media)가 무엇인지 안다.
- 화면에 그릴 때는 `@media print` 블록 안의 규칙을 건너뛴다.
- 인쇄(또는 인쇄 미리보기)를 할 때는 그 블록이 켜져 평소 규칙 위에 더해진다.
- 그래서 화면 규칙을 고치지 않고도 인쇄 결과만 바꿀 수 있다.

> **`@media print`** — 인쇄 매체일 때만 안쪽 규칙을 적용하는 미디어 쿼리.\
> 예: `@media print { .sidebar { display: none; } }`

같은 일을 별도 파일로도 할 수 있다.

```html
<link rel="stylesheet" href="print.css" media="print">
```

- `media="print"` 가 달린 스타일시트는 인쇄할 때만 적용된다.
- 블록으로 쓰든 파일로 나누든 하는 일은 같다 — 규칙을 어디에 모아 둘지의 차이다.

### (2) 숨기기 — 종이에서 쓸모없는 요소 빼기

**언제 쓰나** — 내비게이션 · 푸터 · 사이드바 · 버튼처럼 종이에서는 누를 수도 없고 읽을 필요도 없는 것을 뺄 때.

```text
입력 코드                                         무엇이 일어나나                     결과
@media print {                                 → 인쇄 때 해당 요소의 상자를        → 그 자리가 비고
  nav, footer, .sidebar, button, .no-print {      아예 만들지 않음                    아래 내용이 당겨 올라옴
    display: none !important;
  }
}
```

- 태그 이름(`nav` · `footer` · `button`)으로 흔한 것을 한꺼번에 고른다.
- 태그로 고를 수 없는 것은 `.no-print` 같은 표시용 클래스를 HTML 에 달아 고른다.
- `display: none` 은 공간까지 없애므로 빈 자리가 남지 않는다.

> **`.no-print`** — 「인쇄 때 빼라」는 뜻으로 개발자가 붙이는 클래스 이름(관례일 뿐 브라우저가 아는 이름은 아니다).\
> 예: `<div class="print-nav no-print">…</div>`

### (3) 링크 주소 드러내기 — `a[href]::after` 와 `attr()`

**언제 쓰나** — 종이에서는 링크를 누를 수 없으니, 링크 글자 뒤에 실제 주소를 찍어 주고 싶을 때.

```text
입력 코드                                    무엇이 일어나나                          결과(인쇄)
<a href="https://example.com">예제</a>    → a[href] 에 해당 (href 속성이 있다)       → 예제 (https://example.com)
a[href]::after {                          → 링크 내용 뒤에 가상 요소를 만들고
  content: " (" attr(href) ")";             href 값을 읽어 괄호로 감싼 글자를 넣음
}
```

- `a[href]` 는 「`href` 속성을 **가진** `a`」만 고른다 — `href` 가 없는 `a` 는 해당하지 않는다.
- `::after` 는 요소 내용의 맨 뒤에 글자를 덧붙이는 가상 요소다.
- `attr(href)` 는 그 요소의 `href` 속성 값을 글자로 꺼낸다.
- `content` 에서 `" ("` · `attr(href)` · `")"` 는 이어 붙여진다.
- 원본 예시는 덧붙인 주소를 `font-size: 0.8em; color: #666;` 으로 조금 작고 옅게 만든다.

> **`attr()`** — 요소의 속성 값을 `content` 에 글자로 넣는 CSS 함수.\
> 예: `content: attr(href);`

> **가상 요소(pseudo-element)** — HTML 에는 없지만 CSS 가 만들어 그리는 요소.\
> 예: `::before` · `::after`

### (4) 배경과 색 — 잉크를 아끼고 읽기 쉽게

**언제 쓰나** — 화면용 어두운 배경 · 옅은 회색 글자가 종이에서 잉크를 낭비하거나 흐리게 찍힐 때.

```text
입력 코드                                    무엇이 일어나나                       결과(인쇄)
@media print {                            → 배경을 모두 걷어 냄                  → 흰 종이 위에
  * { background: none !important;        → 글자색을 모두 검정으로 덮어씀           검정 글자만 남음
      color: #000 !important; }
  body { font-size: 12pt; }               → 글자 크기를 종이 단위(pt)로 정함
}
```

- 화면 규칙이 아무리 구체적이어도 `!important` 가 붙은 인쇄 규칙이 이긴다.
- `!important` 가 붙은 작성자 규칙은 HTML 의 `style="…"` 인라인 스타일(중요 표시가 없는 것)보다도 우선한다.
- 그래서 「무엇이 어디서 덮어쓰는지」 따질 필요 없이 인쇄 결과를 확정할 수 있다.
- 원본 팁은 이를 두고 「`!important` 를 적극 사용해도 괜찮은 유일한 상황」이라고 말한다.

> **`!important`** — 선언의 우선순위를 높여 다른 일반 선언과 인라인 스타일을 이기게 하는 표시.\
> 예: `display: none !important;`

> **`pt`(포인트)** — 인쇄에서 흔히 쓰는 길이 단위.\
> 예: `font-size: 12pt;`

### (5) 페이지 나누기 · 여백 — `break-*`, `orphans`/`widows`, `@page`

**언제 쓰나** — 종이 한 쪽의 끝에서 내용이 어색하게 잘리는 것을 막고, 종이 여백을 정할 때.

```text
입력 코드                              무엇이 일어나나                                 결과(인쇄)
h2, h3 { break-after: avoid; }      → 제목 바로 뒤에서 쪽이 나뉘는 것을 피하라고 요청   → 제목이 다음 내용과 같은 쪽에 놓임
table, figure {                     → 요소 안쪽에서 쪽이 나뉘는 것을 피하라고 요청       → 표 · 그림이 한 덩어리로 다음 쪽에
  break-inside: avoid; }
@page { margin: 2cm; }              → 종이 한 쪽의 바깥 여백을 정함                     → 사방 2cm 여백
```

- `break-before` 는 요소 **앞**, `break-after` 는 요소 **뒤**, `break-inside` 는 요소 **안쪽**의 쪽 나눔을 다룬다.
- `avoid` 는 「여기서 나누지 마라」는 요청이다 — 브라우저가 가능한 범위에서 따른다.
- 제목에 `break-after: avoid` 를 주면, 제목만 한 쪽 맨 아래에 홀로 남고 본문이 다음 쪽에서 시작하는 일을 피한다.
- `@page` 는 요소가 아니라 「종이 한 쪽」 자체에 거는 규칙이다.
- `orphans` 와 `widows` 는 문단이 두 쪽으로 갈릴 때 쪽 끝 · 쪽 머리에 남는 줄 수의 최소값을 정해, 한두 줄만 따로 떨어지는 것을 막는다.

> **`@page`** — 인쇄된 종이 한 쪽의 크기 · 여백 등을 정하는 at-규칙.\
> 예: `@page { margin: 2cm; }`

> **`orphans` / `widows`** — 쪽이 나뉠 때 앞쪽 끝 / 뒤쪽 머리에 남아야 하는 최소 줄 수.\
> 예: `p { orphans: 3; widows: 3; }`

### (6) 개발할 때 — 인쇄 미리보기로 확인

- 원본 팁은 Ctrl+P 로 인쇄 미리보기를 띄워 가며 개발하라고 한다.
- 실제 종이를 뽑지 않아도 `@media print` 가 켜진 모습을 미리보기에서 볼 수 있다.

## 문법 — 형태와 규칙

```html demo
<nav class="no-print">메뉴 · 로그인</nav>
<h2>보고서 제목</h2>
<p>본문입니다. 자세한 내용은 <a href="https://example.com">예제 사이트</a>를 보세요.</p>
<style>
  nav { background: #1e293b; color: #e2e8f0; padding: 8px; }
  @media print {
    nav, footer, .sidebar, button, .no-print { display: none !important; }
    body { font-size: 12pt; color: #000; }
    * { background: none !important; }
    a[href]::after { content: " (" attr(href) ")"; font-size: 0.8em; color: #666; }
    h2, h3 { break-after: avoid; }
    table, figure { break-inside: avoid; }
    @page { margin: 2cm; }
  }
</style>
```

> **보이는 것** — 화면에서는 어두운 메뉴 띠 아래 제목과 본문이 보이고, 인쇄 미리보기에서는 메뉴가 사라지고 링크 뒤에 「(https://example.com)」이 작게 붙는다 (코드에서 읽은 것 — 렌더 실측 아님)

원본이 정리한 인쇄 규칙 다섯 가지:

| 규칙 | 쓰는 꼴 | 하는 일 |
|---|---|---|
| 숨기기 | `nav, footer, .sidebar, button, .no-print { display: none !important; }` | 종이에서 쓸모없는 요소를 공간째 뺀다 |
| 링크 URL | `a[href]::after { content: " (" attr(href) ")"; }` | 링크 글자 뒤에 주소를 괄호로 덧붙인다 |
| 배경 제거 | `background: none !important;` | 배경색 · 배경 그림을 걷어 잉크를 아낀다 |
| 텍스트 색상 | `color: #000 !important;` | 글자를 검정으로 통일해 또렷하게 찍는다 |
| 페이지 나누기 | `break-before` · `break-after` · `break-inside: avoid;` | 쪽이 어디서 나뉠지 조절한다 |

규칙:

- 인쇄 규칙은 `@media print { … }` 블록 안에 쓰거나 `<link media="print">` 로 불러오는 별도 파일에 쓴다.
- 블록 안의 규칙은 화면 규칙을 지우지 않고 그 **위에** 더해진다 — 덮어쓰고 싶은 속성만 다시 적는다.
- `a[href]` 처럼 속성 선택자를 써서 `href` 가 있는 링크만 고른다.
- `content` 안의 문자열과 `attr()` 은 띄어 쓰면 이어 붙여진다.
- 쪽 나눔 속성(`break-*`)은 강제가 아니라 요청이다.
- 원본 예시는 `@page` 를 `@media print` 블록 안에 둔다.

## 어디서 틀리나

### 1. 이 데모의 `.no-print` 는 실제로 숨겨지지 않는다

- 원본 예제(정답 코드)의 `@media print { … }` 는 `<code>` 태그 안에 들어간 **글자**일 뿐, `<style>` 안의 규칙이 아니다.
- `<style>` 에서 `.no-print` 가 하는 일은 빨간 배경 · 취소선 · 흐림으로 「인쇄 때 빠질 것」을 **화면에 표시**하는 것뿐이다.
- 그래서 이 데모 페이지를 Ctrl+P 로 미리보기 해도 내비게이션과 푸터는 그대로 찍힌다고 읽힌다 (코드에서 읽은 것 — 렌더 실측 아님).
- 원본 주석 「인쇄 시 숨겨질 내비게이션」은 데모가 **흉내 내는** 동작을 말한다 — 실제로 숨기려면 `<style>` 안에 `@media print` 규칙을 넣어야 한다.

### 2. 데모의 링크에는 `href` 가 없다

- 정답 코드의 `<a class="print-link">링크 텍스트 (https://example.com)</a>` 에는 `href` 속성이 없다.
- 주소는 `::after` 가 붙인 것이 아니라 글자로 직접 적어 「인쇄된 모습」을 흉내 낸 것이다.
- 설령 `a[href]::after` 규칙이 켜져 있어도 `href` 가 없는 이 `a` 는 선택되지 않는다.

### 3. `!important` 를 화면 규칙에까지 퍼뜨린다

- 원본 팁의 「`!important` 를 적극 사용해도 괜찮은」 범위는 인쇄 스타일 안이다.
- 인쇄 규칙은 「무엇이 어디서 덮어쓰든 종이에서는 이렇게」라는 마지막 결정이어서 우선순위 다툼을 끝내는 것이 목적에 맞는다.
- 화면 규칙에서 쓰면 나중에 덮어쓰기가 어려워진다 — 그 점은 인쇄 스타일 바깥의 일반 원칙이다.
- 「유일한 상황」이라는 말은 원본의 의견이다 — 언어가 정한 규칙이 아니다.

### 4. 인쇄 블록에 화면 규칙을 통째로 다시 쓴다

- `@media print` 는 화면 규칙 위에 **더해지는** 것이라 바꿀 속성만 쓰면 된다.
- 숨기기 · 배경 · 색 · 링크 · 쪽 나눔처럼 종이에서 달라져야 하는 것만 모은다.

### 5. `avoid` 를 「반드시」로 믿는다

- `break-inside: avoid` · `break-after: avoid` 는 브라우저에 하는 요청이다.
- 브라우저가 따를 수 없는 경우가 있을 수 있으니 미리보기로 확인한다.

### 6. 화면에서만 보고 끝낸다

- 인쇄 규칙은 화면에서는 전혀 켜지지 않으므로, 화면만 보면 잘못된 규칙도 「괜찮아 보인다」.
- 원본 팁대로 Ctrl+P 미리보기를 열어 두고 고친다.

### 7. 파일로 나눌지 블록으로 쓸지 헷갈린다

- 원본 팁: `<link media="print">` 로 별도 파일을 두거나 `@media print` 블록으로 쓴다 — 둘 다 같은 일을 한다.
- 인쇄 규칙이 많으면 파일로, 몇 줄이면 기존 CSS 안의 블록으로 두는 식으로 고른다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `@media print` 블록은 인쇄 매체에서만 적용된다 | CSS 명세(미디어 쿼리) |
| `<link media="print">` 스타일시트는 인쇄 때만 적용된다 | HTML · CSS 명세 |
| `a[href]` 는 `href` 가 있는 `a` 만 고른다 · `attr(href)` 가 속성 값을 `content` 에 넣는다 | CSS 명세(선택자 · 생성 콘텐츠) |
| `!important` 작성자 선언이 일반 선언과 인라인 스타일을 이긴다 | CSS 명세(캐스케이드) |
| `break-*: avoid` 가 실제로 얼마나 지켜지나 | 브라우저 구현 — 요청일 뿐 결과는 브라우저마다 다를 수 있다 (확인 필요) |
| `orphans` / `widows` 지원 범위 | 브라우저 구현 (확인 필요) |
| `!important` 를 「적극 사용해도 괜찮은 유일한 상황」 | 원본의 권고(관례) — 언어 보장 아님 |
| Ctrl+P 로 인쇄 미리보기가 열린다 | 브라우저 · 운영체제의 단축키 관례 — CSS 와 무관 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 메뉴 · 푸터 · 버튼을 종이에서 빼기 | `@media print` 안의 `display: none !important` | 화면 규칙에서 `display: none`(화면에서도 사라진다) |
| 태그로 고를 수 없는 요소를 빼기 | HTML 에 `.no-print` 를 달고 그 클래스를 숨김 | 요소마다 개별 선택자를 늘어놓기 |
| 종이에서 링크 목적지 알리기 | `a[href]::after { content: " (" attr(href) ")"; }` | HTML 에 주소를 직접 두 번 적기 |
| 어두운 배경 · 옅은 글자 | `background: none !important` · `color: #000 !important` | 화면 테마를 그대로 인쇄 |
| 제목이 쪽 끝에 홀로 남음 | `h2, h3 { break-after: avoid; }` | 빈 줄 · 여백으로 위치 맞추기 |
| 표 · 그림이 두 쪽으로 잘림 | `table, figure { break-inside: avoid; }` | 표를 이미지로 바꾸기 |
| 종이 여백 | `@page { margin: … }` | `body` 의 `padding` 으로 흉내 |
| 화면 너비에 따라 바꾸기 | `@media (max-width: …)` 등 화면 미디어 쿼리 | `@media print`(인쇄 전용이다) |

## 핵심 문장

1. **`@media print` 는 같은 HTML 에 「인쇄 때만 켜지는 규칙」을 더한다** — 화면 모습은 건드리지 않는다.
2. **인쇄 스타일의 네 가지 일은 숨기기 · 링크 주소 드러내기 · 배경과 색 정리 · 쪽 나눔 조절이다.**
3. **인쇄 규칙은 마지막 결정이라 `!important` 로 우선순위 다툼을 끝내도 된다** — 원본의 권고다.
4. **`break-*: avoid` · `orphans` · `widows` 는 종이 위에서 어색하게 잘리는 것을 막는 요청이고, `@page` 는 종이 한 쪽의 여백을 정한다.**
5. **인쇄 규칙은 화면에서 보이지 않으니 인쇄 미리보기로 확인한다.**

## 관련 자료

- 원본에 관련 항목이 없다.
- 원본: study-site 항목 데이터 `data/css/responsive.json` 의 `print-styles`

## 용어 풀이

- **`@media print`** — 인쇄 매체일 때만 안쪽 규칙을 켜는 미디어 쿼리.
- **미디어 쿼리** — 매체 종류나 화면 조건에 따라 규칙을 켜고 끄는 CSS 문법.
- **`<link media="print">`** — 인쇄 때만 적용되는 별도 스타일시트를 불러오는 꼴.
- **`.no-print`** — 인쇄에서 뺄 요소에 개발자가 붙이는 관례적 클래스 이름.
- **`display: none`** — 요소의 상자를 만들지 않아 공간째 없애는 값.
- **`!important`** — 선언의 우선순위를 높이는 표시.
- **인라인 스타일** — HTML 태그의 `style="…"` 속성에 직접 쓴 스타일.
- **속성 선택자 `a[href]`** — 지정한 속성을 가진 요소만 고르는 선택자.
- **가상 요소 `::after`** — 요소 내용 뒤에 CSS 가 만드는 가짜 요소.
- **`content`** — 가상 요소에 넣을 글자를 정하는 속성.
- **`attr()`** — 요소의 속성 값을 글자로 꺼내는 함수.
- **`pt`** — 인쇄에서 흔히 쓰는 길이 단위(포인트).
- **`break-before` / `break-after` / `break-inside`** — 요소 앞 / 뒤 / 안쪽의 쪽 나눔을 다루는 속성.
- **`avoid`** — 「여기서 쪽을 나누지 마라」는 요청 값.
- **`@page`** — 종이 한 쪽에 거는 at-규칙(여백 등).
- **`orphans` / `widows`** — 쪽이 나뉠 때 앞쪽 끝 / 뒤쪽 머리에 남을 최소 줄 수.
- **인쇄 미리보기** — 실제로 뽑지 않고 인쇄 결과를 화면에 보여 주는 브라우저 기능.

## 더 들어가면

- 많은 브라우저는 인쇄 대화상자의 「배경 그래픽 인쇄」 같은 선택을 켜지 않으면 배경을 기본으로 찍지 않는다 (확인 필요).
- 배경색을 일부러 찍어야 할 때 `print-color-adjust: exact`(옛 이름 `-webkit-print-color-adjust`)를 쓰는 방법이 있다 (확인 필요).
- `break-before: page` 처럼 `avoid` 대신 `page` 값을 주면 그 자리에서 쪽을 강제로 나누라는 요청이 된다 (확인 필요).
- 옛 속성 이름 `page-break-before` · `page-break-after` · `page-break-inside` 가 지금의 `break-*` 와 같은 일을 한다 (확인 필요).
- 개발자 도구에는 인쇄 매체를 흉내 내는(emulate) 기능이 있어, 미리보기 창 없이 `@media print` 를 켠 모습을 볼 수 있다 (확인 필요).
- `a[href^="#"]` 처럼 페이지 안 이동용 링크는 주소를 찍어도 쓸모가 없어 제외하는 경우가 있다 (확인 필요).
- 요소 하나가 한 쪽보다 길면 `break-inside: avoid` 를 지킬 방법이 없어 결국 나뉜다 (확인 필요).
- `@page` 를 `@media print` 안에 넣는 것이 모든 브라우저에서 같은 결과를 내는지는 따로 확인한다 (확인 필요).

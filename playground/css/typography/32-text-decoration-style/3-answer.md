# css/typography/32 — text-decoration-style — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 아무 선도 보이지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
단락 아래에 선이 그려지지 않는다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`text-decoration-style` 은 선의 모양만 정하고, 그릴 선 종류(`underline` 등)는 정하지 않는다.
그릴 선이 없으니 모양을 입힐 대상도 없다.
근거: 2-summary 「동작 방식 (1)」, 「어디서 틀리나 1」.

### 2. 실선 밑줄 — 단축 속성이 모양을 `solid` 로 되돌린다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`.note` 에는 점선이 아닌 실선 밑줄이 그어진다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
뒤에 온 단축 속성 `text-decoration: underline;` 은 적지 않은 모양을 기본값 `solid` 로 되돌린다.
그래서 앞줄의 `dotted` 가 덮인다.
근거: 2-summary 「동작 방식 (3)」, 「어디서 틀리나 2」.

### 3. 실선 밑줄 — 모양은 상속되지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`.child` 의 밑줄은 이중선이 아닌 실선이다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`text-decoration-style` 은 상속이 `False` 라 부모의 `double` 이 자식에게 이어지지 않는다.
게다가 자식의 단축 속성은 모양을 적지 않았으므로 모양이 `solid` 로 정해진다.
부모는 선 종류를 정하지 않았으니 부모 쪽 선도 없다.
근거: 2-summary 「동작 방식 (3)」 · 「동작 방식 (4)」, 「어디서 틀리나 6」.

### 4. 물결선은 평범한 밑줄과 한눈에 구별되어 「틀림」의 표지로 굳어졌다

실선 밑줄은 링크 같은 평범한 표시로 이미 널리 쓰여, 오류 표시로 쓰면 뜻이 섞인다.
물결선은 다른 모양과 확연히 달라 「여기 문제가 있다」는 신호로 읽히고, 원본 팁대로 맞춤법 오류 표시에 자주 쓰인다.
반대로 평범한 강조에 물결선을 쓰면 사용자가 오류로 오해한다.
근거: 2-summary 「어디서 틀리나 3」, 「언제 쓰고 언제 안 쓰나」.
(「한눈에 구별된다」는 까닭 풀이는 원본에 근거 없음 — 추론)

### 5. 서서히 변하지 않고 단번에 바뀐다

원본 데이터에서 이 속성의 애니메이션 가능은 `False` 다.
실선과 물결선 사이의 중간 모양이 없으므로 `transition` 을 걸어도 상태가 바뀌는 순간 모양이 바로 바뀐다.
근거: 2-summary 「동작 방식 (4)」, 「어디서 틀리나 5」.

### 6. 선 종류가 「어디에」, `text-decoration-style` 이 「어떤 모양」 — 단축 속성은 둘을 한 줄에 함께 정한다

「어디에 선을 긋나」는 `underline` · `overline` · `line-through` 같은 선 종류가 정한다.
「어떤 모양으로」는 `text-decoration-style` 이 정한다.
`text-decoration` 단축 속성은 `underline wavy` 처럼 둘을 한 줄에 함께 적는 길이며, 모양을 빼면 `solid` 로 되돌린다.
근거: 2-summary 「한눈에 — 쉽게 말하면」, 「동작 방식 (1)」 · 「동작 방식 (3)」.

### 7. `dotted` 는 점, `dashed` 는 짧은 선분

`dotted` 는 점이 이어진 선, `dashed` 는 짧은 선분이 이어진 선이다.
dot(점)과 dash(줄표)라는 이름 뜻으로 구별한다.
점의 간격이나 선분의 길이는 이 속성이 정하지 않는다.
근거: 2-summary 「동작 방식 (2)」, 「어디서 틀리나 4」, 「구현 세부사항 대 언어 보장」.

## 실습 정답

### 실습 1. 다섯 가지 밑줄 모양 늘어놓기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 단락 다섯 개에 클래스를 하나씩 단다 | `<p class="solid">` … `<p class="wavy">` |
| 단축 속성 한 줄로 `underline` 과 모양을 함께 정한다 | `.solid { text-decoration: underline solid; }` · `.double { … underline double; }` · `.dotted { … underline dotted; }` · `.dashed { … underline dashed; }` · `.wavy { … underline wavy; }` |
| 글자가 자기 밑줄 모양의 이름을 보여 준다 | `Solid 실선` · `Double 이중선` · `Dotted 점선` · `Dashed 파선` · `Wavy 물결선` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/typography/reference/text-decoration-style.html`

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>text-decoration-style - 텍스트 장식 선의 스타일을 설정</title>
  <!--
    [타이포그래피] text-decoration-style
    설명: 텍스트 장식 선의 스타일을 설정
    구문: text-decoration-style: solid | double | dotted | dashed | wavy
    팁: wavy는 맞춤법 오류 표시에 자주 사용. 스타일은 text-decoration 단축 속성에서도 설정 가능.
  -->
  <style>
    /* .solid: 단일 실선 */
    .solid {
      text-decoration: underline solid;   /* 단축형: line=underline, style=solid */
      font-size: 18px;                    /* 본문 크기 */
      margin-bottom: 4px;                 /* 다음 단락과 간격 */
    }

    /* .double: 이중선 */
    .double {
      text-decoration: underline double;  /* 두 줄로 표시 */
      font-size: 18px;                    /* 본문 크기 */
      margin-bottom: 4px;                 /* 다음 단락과 간격 */
    }

    /* .dotted: 점선 */
    .dotted {
      text-decoration: underline dotted;  /* 점으로 이루어진 선 */
      font-size: 18px;                    /* 본문 크기 */
      margin-bottom: 4px;                 /* 다음 단락과 간격 */
    }

    /* .dashed: 파선(짧은 대시) */
    .dashed {
      text-decoration: underline dashed;  /* 짧은 선분으로 이루어진 선 */
      font-size: 18px;                    /* 본문 크기 */
      margin-bottom: 4px;                 /* 다음 단락과 간격 */
    }

    /* .wavy: 물결선 (맞춤법 오류 시 자주 사용) */
    .wavy {
      text-decoration: underline wavy;    /* 물결 모양 선 */
      font-size: 18px;                    /* 본문 크기 */
    }
  </style>
</head>
<body>
  <!-- 실선 -->
  <p class="solid">Solid 실선</p>
  <!-- 이중선 -->
  <p class="double">Double 이중선</p>
  <!-- 점선 -->
  <p class="dotted">Dotted 점선</p>
  <!-- 파선 -->
  <p class="dashed">Dashed 파선</p>
  <!-- 물결선 -->
  <p class="wavy">Wavy 물결선</p>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.solid { text-decoration: underline solid; font-size: 18px; margin-bottom: 4px; }
.double { text-decoration: underline double; font-size: 18px; margin-bottom: 4px; }
.dotted { text-decoration: underline dotted; font-size: 18px; margin-bottom: 4px; }
.dashed { text-decoration: underline dashed; font-size: 18px; margin-bottom: 4px; }
.wavy { text-decoration: underline wavy; font-size: 18px; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 모든 클래스가 `underline` 을 함께 적는다 — 선 종류가 없으면 모양은 보이지 않는다.
- 단축 속성 안에 모양을 적었으므로 「모양이 `solid` 로 되돌려지는」 문제가 생기지 않는다.
- `.solid` 의 `solid` 는 기본값이라 빼도 같은 모양이 되지만, 다섯 값을 나란히 비교하려고 적어 두었다.
- `font-size` · `margin-bottom` 은 꾸밈 값일 뿐 장식선의 모양과는 상관없다.
- 마지막 `.wavy` 는 맞춤법 오류 표시에 쓰이는 물결 밑줄의 꼴이다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

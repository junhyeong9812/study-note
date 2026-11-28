# css/typography/36 — text-emphasis-style — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 다르지 않다 — 채움을 빼면 `filled` 다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
두 선택자 모두 글자마다 속이 채워진 점 마크가 붙는다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
채움 축을 생략하면 `filled` 가 기본이다.
그래서 `dot` 은 `filled dot` 과 같은 선언이 된다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 1」.

### 2. 첫 글자 ★ 만 쓰인다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
글자마다 ★ 가 붙고, ☆ 는 쓰이지 않는다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
커스텀 문자열은 첫 번째 문자만 마크로 쓰인다.
번갈아 찍거나 두 기호를 함께 찍는 기능은 없다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 2」.

### 3. 「안쪽 글자」에도 속 빈 원이 붙는다 — 상속

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
「앞 글자」와 「안쪽 글자」 모두 글자마다 ○ 마크가 붙는다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`text-emphasis-style` 은 상속되는 속성이다.
`span` 은 자기 값을 갖지 않으므로 부모 `p` 의 `open circle` 을 물려받는다.
근거: 2-summary 「동작 방식 (4)」.

### 4. 애니메이션 불가 속성이라 중간 모양이 없다

이 속성의 애니메이션 가능 여부는 `False` 다.
점과 원 사이의 중간 단계가 정의되지 않으므로 보간할 값이 없다.
그래서 `transition` 이 걸려 있어도 새 모양으로 즉시 바뀐다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 6」.

### 5. 문법 위반이라 선언이 버려진다

`<string>` 은 키워드 조합과 `|` 로 나뉜 다른 갈래다.
문자열에 `filled` · `open` 을 붙일 수 없으므로 이 선언은 무효이고 통째로 버려진다.
그 결과 상속값이나 앞선 규칙의 값이 그대로 남는다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 3」.

### 6. 순서 바꾸기는 되고, 채움 키워드 둘은 무효다

`circle open` 은 `open circle` 과 같다 — 두 축은 `||` 로 묶여 순서가 자유롭다.
`filled open dot` 은 채움 축에서 둘을 골라 문법 위반이므로 선언이 버려진다.
근거: 2-summary 「동작 방식 (1)」 · 「문법 — 형태와 규칙」 · 「어디서 틀리나 4」.

### 7. 그 낱말을 감싼 요소에 `none` 을 준다

`color` 처럼 이 속성도 상속되어 문단 안 모든 자식에 퍼진다.
상속은 자식이 자기 값을 가지면 멈추므로, 그 낱말을 `span` 등으로 감싸 `text-emphasis-style: none` 을 주면 그 부분만 마크가 빠진다.
부모 값을 지우면 문단 전체의 강조가 사라진다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 5」 · 「언제 쓰고 언제 안 쓰나」.

### 8. 글자 하나하나를 방점처럼 강조할 때

밑줄은 문장을 따라 줄 하나로 강조한다.
`text-emphasis-style` 은 글자마다 마크를 하나씩 붙여, 방점처럼 낱말의 각 글자를 짚어 강조한다.
그래서 글자 단위 강조가 필요하면 `text-emphasis-style`, 줄로 긋는 강조면 밑줄을 고른다.
근거: 2-summary 「한눈에 — 쉽게 말하면」 · 「언제 쓰고 언제 안 쓰나」.

## 실습 정답

### 실습 1. 세 가지 강조 마크 단락 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 채워진 점 마크 | `.filled-dot { text-emphasis-style: filled dot; }` |
| 비어 있는 원 마크 | `.open-circle { text-emphasis-style: open circle; }` |
| 문자열 ★ 마크 | `.custom { text-emphasis-style: '★'; }` |
| 글자 크기 · 단락 간격 유지 | 각 선택자의 `font-size` · `margin-bottom` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/typography/reference/text-emphasis-style.html`

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>text-emphasis-style - 텍스트 강조 마크의 형태를 설정</title>
  <!--
    [타이포그래피] text-emphasis-style
    설명: 텍스트 강조 마크의 형태를 설정
    구문: text-emphasis-style: none | [filled | open] || [dot | circle | double-circle | triangle | sesame] | <string>
    팁: filled/open을 생략하면 filled가 기본. 커스텀 문자열은 첫 번째 문자만 사용됨.
  -->
  <style>
    /* .filled-dot: 채워진 점 강조 */
    .filled-dot {
      text-emphasis-style: filled dot;   /* 채워진 점 모양 */
      font-size: 20px;                   /* 본문 크기 */
      margin-bottom: 12px;               /* 다음 단락과 간격 */
    }

    /* .open-circle: 비어 있는 원 강조 */
    .open-circle {
      text-emphasis-style: open circle;  /* 외곽선만 있는 원 */
      font-size: 20px;                   /* 본문 크기 */
      margin-bottom: 12px;               /* 다음 단락과 간격 */
    }

    /* .custom: 사용자 지정 문자(첫 글자만 사용됨) */
    .custom {
      text-emphasis-style: '★';          /* 임의 문자열을 마크로 사용 (첫 글자 ★) */
      font-size: 20px;                   /* 본문 크기 */
    }
  </style>
</head>
<body>
  <!-- 채워진 점 -->
  <p class="filled-dot">Filled dot ●</p>
  <!-- 비어 있는 원 -->
  <p class="open-circle">Open circle ○</p>
  <!-- 사용자 지정 별 -->
  <p class="custom">Custom ★</p>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.filled-dot { text-emphasis-style: filled dot; font-size: 20px; margin-bottom: 12px; }
.open-circle { text-emphasis-style: open circle; font-size: 20px; margin-bottom: 12px; }
.custom { text-emphasis-style: '★'; font-size: 20px; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- `filled dot` 은 `dot` 만 써도 같은 결과다 — 채움 축 생략은 `filled`.
- `open circle` 의 `open` 은 생략하면 안 된다 — 빼면 채워진 원이 된다.
- `'★'` 는 문자열 갈래라 `filled` · `open` 을 붙이지 않는다.
- 문자열은 첫 글자만 쓰이므로 한 글자만 주면 된다.
- 마크 모양 외의 꾸밈(`font-size` · `margin-bottom`)은 이 속성과 무관하다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

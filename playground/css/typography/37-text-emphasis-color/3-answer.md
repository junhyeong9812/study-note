# css/typography/37 — text-emphasis-color — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 글자는 짙은 색 그대로, 마크만 빨강

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
글자는 `#111827`(짙은 색), 채워진 점 마크는 `#ef4444`(빨강)이다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`text-emphasis-color` 는 마크의 색만 정하고 `color` 는 건드리지 않는다.
글자색은 `p` 에 정한 `#111827` 그대로 남는다.
근거: 2-summary 「동작 방식 (2)」.

### 2. 마크는 글자색(짙은 색)이 된다 — 빨강이 덮인다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
마크는 빨강이 아니라 글자색 `#111827` 로 칠해진다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`text-emphasis` 는 모양과 색을 함께 정하는 단축 속성이다.
색을 적지 않았으므로 색을 기본값 `currentcolor` 로 되돌린다.
뒤에 쓴 선언이 이기므로 앞의 빨강은 무시되고, `currentcolor` 는 `color` 인 `#111827` 이 된다.
근거: 2-summary 「어디서 틀리나 2」 · 「문법 — 형태와 규칙」.

### 3. 아무것도 파랗게 보이지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
파랑으로 칠해진 것은 없고, 단락은 평범한 글자로만 보인다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`text-emphasis-color` 는 이미 있는 마크에 색을 칠할 뿐 마크를 만들지 않는다.
마크 모양(`text-emphasis`)을 주지 않았으니 칠할 대상이 없다.
근거: 2-summary 「어디서 틀리나 1」.

### 4. 기본값 `currentcolor` 가 `color` 를 가리키기 때문이다

마크 색을 정하지 않으면 기본값 `currentcolor` 가 쓰인다.
`currentcolor` 는 「지금 이 요소의 `color` 값」이므로 `color` 가 바뀌면 마크 색도 그 값을 따라간다.
근거: 2-summary 「동작 방식 (1)」.

### 5. 시각적 대비 효과를 얻으려는 것이다

원본 팁대로, 마크를 글자와 다른 색으로 칠하면 강조 부분이 더 뚜렷하게 눈에 띈다.
다만 마크는 작아서, 글자와 비슷한 색이면 그 효과가 거의 드러나지 않는다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 3」.

### 6. 부모의 색을 물려받는다

`text-emphasis-color` 는 상속되는 속성이다.
`span` 이 마크 색을 따로 정하지 않았으므로 부모 `p` 에 정한 색이 `span` 의 마크 색이 된다.
`span` 만 다른 색으로 하려면 `span` 에 직접 적는다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 5」.

### 7. 할 수 있다 — 애니메이션 가능한 속성이다

원본 재료에 이 속성은 애니메이션 가능(`True`)으로 적혀 있다.
그래서 `transition: text-emphasis-color 0.3s` 처럼 쓰면 두 색 사이의 중간 색을 거치며 바뀐다.
근거: 2-summary 「동작 방식 (4)」.

### 8. `color` 는 글자, `text-emphasis` 는 마크 모양, `text-emphasis-color` 는 마크 색 — 마크에는 `text-emphasis` 가 꼭 있어야 한다

- `color` — 글자 자체의 색을 정한다.
- `text-emphasis` — 글자마다 붙는 마크의 모양을 정한다(단축 속성이라 색도 함께 받는다).
- `text-emphasis-color` — 그 마크의 색만 정한다. 안 정하면 `currentcolor` 로 `color` 를 따른다.

마크가 보이려면 모양을 주는 `text-emphasis` 가 있어야 한다.
근거: 2-summary 「한눈에」 대응표 · 「문법 — 형태와 규칙」 · 「어디서 틀리나 1」.

## 실습 정답

### 실습 1. 빨간 점과 파란 원 강조 마크 달기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. `.red` · `.blue` 두 단락 | `<p class="red">빨간 강조 마크</p>` · `<p class="blue">파란 강조 마크</p>` |
| 2. `.red` 에 채워진 점 마크 | `.red { text-emphasis: filled dot; }` |
| 3. `.red` 마크만 빨강 | `.red { text-emphasis-color: #ef4444; }` (`color` 는 없음) |
| 4. `.blue` 에 채워진 원 마크 | `.blue { text-emphasis: filled circle; }` |
| 5. `.blue` 마크만 파랑 | `.blue { text-emphasis-color: #3b82f6; }` (`color` 는 없음) |
| 6. 색은 단축 속성 뒤에 | 두 규칙 모두 `text-emphasis` 줄 다음 줄에 `text-emphasis-color` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/typography/reference/text-emphasis-color.html`

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>text-emphasis-color - 텍스트 강조 마크의 색상을 설정</title>
  <!--
    [타이포그래피] text-emphasis-color
    설명: 텍스트 강조 마크의 색상을 설정
    구문: text-emphasis-color: <color>
    팁: 강조 마크 색상을 텍스트와 다르게 설정하여 시각적 대비 효과를 줄 수 있음.
  -->
  <style>
    /* .red: 빨간 점 강조 마크 */
    .red {
      text-emphasis: filled dot;             /* 채워진 점 마크 */
      text-emphasis-color: #ef4444;          /* 마크 색만 빨강 (글자색은 그대로) */
      font-size: 20px;                       /* 본문 크기 */
      margin-bottom: 12px;                   /* 다음 단락과 간격 */
    }

    /* .blue: 파란 원 강조 마크 */
    .blue {
      text-emphasis: filled circle;          /* 채워진 원 마크 */
      text-emphasis-color: #3b82f6;          /* 마크 색=파랑 */
      font-size: 20px;                       /* 본문 크기 */
    }
  </style>
</head>
<body>
  <!-- 빨간 점 강조 -->
  <p class="red">빨간 강조 마크</p>
  <!-- 파란 원 강조 -->
  <p class="blue">파란 강조 마크</p>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.red { text-emphasis: filled dot; text-emphasis-color: #ef4444; font-size: 20px; margin-bottom: 12px; }
.blue { text-emphasis: filled circle; text-emphasis-color: #3b82f6; font-size: 20px; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 마크를 만드는 것은 `text-emphasis` 이고, `text-emphasis-color` 는 그 마크에 색만 칠한다.
- 두 규칙 모두 `color` 를 쓰지 않으므로 글자색은 원래 색 그대로다.
- `text-emphasis` 를 먼저 쓰고 색을 뒤에 써야 단축 속성이 색을 기본값으로 되돌리지 않는다.
- `font-size` · `margin-bottom` 은 꾸밈 값이라 이 주제와 무관하다.
- 마크 색을 지우면 두 단락의 마크는 기본값 `currentcolor` 로 글자색을 따르게 된다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

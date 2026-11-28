# css/typography/45 — initial-letter — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 3줄 높이의 L, 본문 첫 3줄은 그 오른쪽으로 비켜 흐른다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
첫 글자 L 이 굵게, 본문 3줄 높이로 커진다.
본문 첫 3줄은 L 의 오른쪽에서 시작하고, 4줄부터는 단락 왼쪽 끝부터 이어진다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`::first-letter` 가 첫 글자만 고르고, `initial-letter: 3` 의 숫자 하나는 「첫 글자가 차지할 줄 수」다.
3줄을 차지한 글자 옆 자리를 본문이 비켜 흐른다.
근거: 2-summary 「동작 방식 (1)」.

### 2. 크기는 3줄, 가라앉는 깊이는 2줄 — 1줄만큼 위로 솟는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
첫 숫자 `3` 이 크기(3줄 높이), 둘째 숫자 `2` 가 싱크(2줄만 가라앉음)다.
그래서 글자의 남는 1줄 높이는 첫 줄 위로 솟고, 본문은 2줄만 글자 옆을 비켜 흐른다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`<number> <integer>` 꼴은 크기와 싱크를 따로 정한다.
크기가 싱크보다 크면 그 차이가 위로 남는다 (원본에 근거 없음 — 추론).
근거: 2-summary 「동작 방식 (2)」.

### 3. 드롭캡이 생기지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
첫 글자는 본문과 같은 크기로 보인다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`initial-letter` 의 적용 대상은 `::first-letter` 이고, 상속되지 않는다.
단락에 적은 값을 첫 글자 의사 요소가 물려받지 않으니 드롭캡이 될 것이 없다.
근거: 2-summary 「어디서 틀리나 1」 · 「문법 — 형태와 규칙」.

### 4. 큰 글자를 본문 줄에 딱 맞춰 앉히려는 것이다

드롭캡은 「본문 몇 줄 높이」로 보여야 줄과 어긋나지 않는다.
픽셀로 크기를 손수 맞추면 본문 글자 크기나 줄 간격이 바뀔 때마다 다시 계산해야 한다.
줄 수로 적으면 크기가 언제나 본문의 줄에 맞춰진다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 2」.

### 5. 「3줄 높이」의 한 줄 자체가 높아지기 때문이다

`initial-letter: 3` 의 기준은 본문 한 줄의 높이다.
`line-height` 를 키우면 한 줄이 높아지고, 그 줄 3개를 합친 높이도 커진다.
값은 그대로라도 단위인 「줄」이 커졌으니 글자가 커진다.
근거: 2-summary 「동작 방식 (3)」(정답 코드 주석 「드롭캡 줄 수와 함께 동작」).

### 6. 중간 단계 없이 한 번에 바뀐다

`initial-letter` 는 애니메이션할 수 없는 속성이다.
`transition` 을 걸어도 `normal` 과 `3` 사이를 이어 그리지 않고, 값이 바뀌는 순간 드롭캡이 생긴다.
근거: 2-summary 「어디서 틀리나 3」 · 「문법 — 형태와 규칙」.

### 7. 굵고 파란, 보통 크기의 첫 글자가 된다

CSS 는 이해하지 못하는 선언만 버리고 나머지를 적용한다.
그래서 `initial-letter: 3` 만 빠지고, 같은 규칙의 `font-weight` · `color` · `margin-right` 는 그대로 남는다.
근거: 2-summary 「어디서 틀리나 4」 · 「구현 세부사항 대 언어 보장」.

### 8. 「첫 글자」를 따로 고를 태그가 HTML 에 없기 때문이다

단락 HTML 에는 첫 글자만 감싼 요소가 없다.
`::first-letter` 가 그 첫 글자를 요소처럼 골라 주어야 `initial-letter` 를 비롯한 꾸밈을 걸 자리가 생긴다.
그래서 두 가지는 원본 팁대로 짝을 이뤄 쓴다.
근거: 2-summary 「동작 방식 (1)」 · 「용어 풀이」.

## 실습 정답

### 실습 1. 잡지 꼴 드롭캡 단락 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 첫 글자만 고르는 선택자 | `.dropcap::first-letter` |
| 2. 본문 3줄 높이의 드롭캡 | `initial-letter: 3;` |
| 3. 굵기 · 강조색 · 오른쪽 여백 유지 | `.dropcap::first-letter` 안의 `font-weight` · `color` · `margin-right` |
| 4. 본문 크기 · 줄 간격 · 폭 | `.dropcap` 의 `font-size` · `line-height` · `max-width` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/typography/reference/initial-letter.html`

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>initial-letter - 첫 글자를 드롭캡(큰 첫 글자) 스타일로 표시</title>
  <!--
    [타이포그래피] initial-letter
    설명: 첫 글자를 드롭캡(큰 첫 글자) 스타일로 표시
    구문: initial-letter: normal | <number> [<integer>]
    팁: ::first-letter 의사 요소에 적용. 잡지/신문 스타일의 드롭캡 효과에 유용. 브라우저 지원 확인 필요.
  -->
  <style>
    /* .dropcap::first-letter: 단락 첫 글자에만 드롭캡 적용 */
    .dropcap::first-letter {
      initial-letter: 3;       /* 첫 글자가 3줄 높이로 확장됨 (드롭캡 크기) */
      font-weight: bold;       /* 첫 글자를 강조하기 위한 굵기 */
      color: #3b82f6;          /* 파란색 강조 */
      margin-right: 4px;       /* 첫 글자 오른쪽 여백 */
    }

    /* .dropcap: 단락 본문 스타일 */
    .dropcap {
      font-size: 16px;         /* 본문 크기 */
      line-height: 1.6;        /* 줄 간격 (드롭캡 줄 수와 함께 동작) */
      max-width: 320px;        /* 가독성을 위한 폭 제한 */
    }
  </style>
</head>
<body>
  <!-- 드롭캡 단락: 첫 글자 L이 3줄 높이로 표시됨 -->
  <p class="dropcap">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation.</p>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.dropcap::first-letter { initial-letter: 3; font-weight: bold; color: #3b82f6; margin-right: 4px; }
.dropcap { font-size: 16px; line-height: 1.6; max-width: 320px; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 드롭캡은 단락이 아니라 `::first-letter` 에 건다 — 상속되지 않기 때문이다.
- `initial-letter: 3` 의 `3` 은 픽셀이 아니라 본문 줄 수다.
- 첫 글자에 `font-size` 를 주지 않아도 크기는 줄 수와 본문 `line-height` 가 정한다.
- 꾸밈(굵기 · 색 · 여백)은 같은 `::first-letter` 규칙에 함께 두면, 이 속성을 모르는 브라우저에서도 꾸밈만은 남는다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

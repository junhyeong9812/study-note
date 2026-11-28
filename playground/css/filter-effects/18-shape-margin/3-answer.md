# css/filter-effects/18 — shape-margin — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. float 가 없으면 글은 원 옆으로 흐르지 않고 박스 아래로 내려간다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`.shape` 는 보통 블록처럼 한 줄을 차지하고, 문단 글은 그 아래에서 시작한다.
`shape-outside` 와 `shape-margin` 은 아무 효과를 내지 않는다(코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`shape-outside` 는 float 요소에만 적용되고, `shape-margin` 은 그 도형 위에서만 일한다.
float 가 없으니 흐름 경계 자체가 생기지 않는다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 2」.

### 2. 박스는 네모로 보이고, 글은 넓어진 원 경계를 따라 흐른다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
보라색 박스는 80px 네모로 그려진다.
글줄의 왼쪽 끝은 여전히 원(과 16px 띠, margin box 한계까지)을 따라 휜다(코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`shape-outside` 와 `shape-margin` 은 글 흐름만 바꾸고 그리기에는 관여하지 않는다.
박스를 원으로 그리는 일은 `clip-path` 몫인데 그것이 빠졌다.
근거: 2-summary 「동작 방식 (4)」.

### 3. 약 8px — margin box 가 먼저 막는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
원의 오른쪽 가장자리는 80px 지점이다.
`shape-margin: 16px` 로 넓힌 원은 96px 지점까지 뻗지만, margin box 의 오른쪽 끝은 80 + 8 = 88px 지점이다.
그래서 원 한가운데 높이에서 글은 88px 에서 시작하고, 틈은 약 8px 가 된다(코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
원본 팁대로 `shape-margin` 은 margin box 보다 클 수 없어, 넘치는 부분이 잘린다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 3」. 88px 계산은 원본 코드의 값으로 한 추론이다 (원본에 근거 없음 — 추론).

### 4. 하나는 흐름만, 하나는 그리기만 바꾸기 때문이다

`shape-outside` 는 글이 흐를 경계를 원으로 만들지만 박스는 네모로 그려진 채다.
`clip-path` 는 박스를 원으로 잘라 그리지만 글 흐름에는 관여하지 않는다.
「원이 보인다」와 「글이 원을 따라 흐른다」를 둘 다 얻으려면 각각을 맡은 속성을 함께 써야 한다.
근거: 2-summary 「동작 방식 (4)」.

### 5. `margin` 은 사각형으로만 넓혀 곡선을 따른 고른 틈을 못 만든다

`margin` 은 박스를 네모 그대로 넓힐 뿐이다.
`shape-margin` 은 도형 모양을 따라 같은 두께의 띠를 두르므로 원 둘레 어디서나 틈이 고르다.
다만 넓어진 띠는 margin box 를 넘지 못하므로, `margin` 은 띠가 뻗을 공간을 마련해 주는 역할을 한다.
근거: 2-summary 「어디서 틀리나 5」 · 「동작 방식 (3)」.

### 6. 달라지지 않는다

`shape-margin` 은 `shape-outside` 로 정한 도형의 바깥 여백이다.
띠를 두를 도형이 없으니 간격에 아무 영향이 없다.
간격을 원하면 보통의 `margin` 을 쓴다.
근거: 2-summary 「어디서 틀리나 1」 · 「언제 쓰고 언제 안 쓰나」.

### 7. 애니메이션은 되지만, 부모에 준 값은 자식에게 전해지지 않는다

`shape-margin` 은 애니메이션 가능하므로 `:hover` 에서 값을 키우고 `transition` 을 걸면 틈이 서서히 넓어진다.
하지만 상속되지 않으므로 부모에 준 값은 자식 float 에 적용되지 않고, float 요소 자신에게 줘야 한다.
근거: 2-summary 「문법 — 형태와 규칙」 · 「핵심 문장 5」.

## 실습 정답

### 실습 1. 원형 도형을 여유 있게 감싸 흐르는 문단 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 컨테이너 안에 도형 블록과 문단 | `<div class="wrap">` 안의 `<div class="shape">` · `<p>` |
| 도형을 왼쪽에 띄워 글이 오른쪽으로 | `.shape { float: left; }` |
| 흐름 경계를 박스 크기에 맞춘 원으로 | `shape-outside: circle(50%);` |
| 원 경계를 바깥으로 16px 넓히기 | `shape-margin: 16px;` |
| 눈에도 원으로 보이게 자르기 | `clip-path: circle(50%);` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/filter-effects/reference/shape-margin.html`

```html
<!DOCTYPE html>
<!-- 문서 타입을 HTML5로 선언 -->
<html lang="ko">
  <!-- 문서 언어를 한국어로 설정 -->
  <head>
    <meta charset="utf-8">
    <!-- 문자 인코딩을 UTF-8로 지정 -->
    <title>shape-margin - shape-outside로 정의된 도형의 바깥 여백을 설정합니다</title>
    <!-- 브라우저 탭 제목 -->
    <!--
      [필터 & 효과] shape-margin
      설명: shape-outside로 정의된 도형의 바깥 여백을 설정합니다
      구문: shape-margin: <length-percentage>
      팁: 텍스트가 도형에 너무 가까이 붙지 않도록 여유 공간을 줌. margin-box보다 클 수 없음.
    -->
    <style>
      /* .wrap: shape-outside가 적용된 도형과 텍스트가 함께 흐를 컨테이너 */
      .wrap {
        max-width: 300px;                           /* 최대 너비 300px */
        margin: 20px auto;                          /* 상하 20px / 수평 중앙 */
        font-size: 14px;                            /* 글자 크기 14px */
        line-height: 1.6;                           /* 줄 간격 1.6배 */
        color: #374151;                             /* 진회색 텍스트 */
      }
      /* .shape: 원형 도형 + 텍스트와의 간격 16px 확보 */
      .shape {
        float: left;                                /* 왼쪽 floating (shape-outside는 float 필수) */
        width: 80px;                                /* 너비 80px */
        height: 80px;                               /* 높이 80px */
        shape-outside: circle(50%);                 /* 텍스트가 감쌀 도형: 원(반지름 50%) */
        shape-margin: 16px;                         /* 도형 바깥쪽으로 16px 여유 → 텍스트가 원에 너무 붙지 않음 */
        clip-path: circle(50%);                     /* 시각적으로도 원으로 잘라냄 (shape-outside는 시각 출력에 영향 없음) */
        background: #8b5cf6;                        /* 보라 배경 */
        margin-right: 8px;                          /* 박스 모델상의 우측 여백 8px */
      }
    </style>
  </head>
  <body>
    <!-- 원형 도형 주위로 텍스트가 감싸되, 16px 여유를 두고 흐름 -->
    <div class="wrap">
      <!-- 시각적 원형 + shape-outside 원형 + 16px 여유 -->
      <div class="shape"></div>
      <!-- 도형을 감싸는 더미 텍스트 -->
      <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
    </div>
  </body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.wrap { max-width: 300px; margin: 20px auto; font-size: 14px; line-height: 1.6; color: #374151; }
.shape { float: left; width: 80px; height: 80px; shape-outside: circle(50%); shape-margin: 16px; clip-path: circle(50%); background: #8b5cf6; margin-right: 8px; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- `float: left` 가 없으면 `shape-outside` 도 `shape-margin` 도 일하지 않는다.
- `shape-outside` 가 흐름 경계를, `shape-margin` 이 그 경계 바깥의 여유를 맡는다.
- `clip-path` 는 그리기만 맡으므로 흐름용 원과 같은 `circle(50%)` 를 따로 준다.
- `margin-right: 8px` 가 margin box 의 오른쪽 끝을 정해, `shape-margin` 이 그 너머로는 뻗지 못한다.
- `shape-margin` 을 `0` 으로 바꿔 비교하면 이 속성이 만드는 틈을 눈으로 확인할 수 있다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

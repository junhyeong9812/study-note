# css/typography/43 — text-shadow — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 글자와 같은 navy, 오른쪽 아래, 선명

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

그림자는 navy 색이고, 글자에서 오른쪽으로 3px, 아래로 3px 옮겨진 자리에 놓인다.
흐림 값이 없으므로 가장자리는 선명하다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**

색을 생략하면 기본이 `currentcolor` 라 글자색 `navy` 를 따른다.
두 오프셋이 양수라 오른쪽 · 아래로 이동하고, 세 번째 값(흐림)을 빼면 0 이다.
근거: 2-summary 「문법 — 형태와 규칙」 · 「동작 방식 (1)」.

### 2. 맨 위는 빨강(`#ef4444`)

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

글자 바로 뒤 맨 위 층은 빨강, 그 아래 파랑, 맨 아래 초록이다.
글자 오른쪽 아래로 빨강 · 파랑 · 초록 띠가 1px 씩 드러난다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**

쉼표 목록의 첫 그림자가 맨 위에 그려지고 뒤로 갈수록 아래에 깔린다.
오프셋이 1 · 2 · 3px 로 늘어나므로 아래 장은 위 장에 가려지고 남은 1px 만 보인다.
근거: 2-summary 「동작 방식 (3)」. (쌓임 순서는 원본에 근거 없음 — CSS 명세에 기댄 서술)

### 3. 「끝」만 그림자가 없다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

「첫 문단」과 「둘째 문단」에는 회색 그림자가 생기고, `span` 안의 「끝」에는 그림자가 없다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**

`text-shadow` 는 상속되므로 `div` 에 건 값을 두 `p` 가 물려받는다.
`span` 은 `none` 을 직접 지정해 상속된 값을 끊는다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 5」.

### 4. 흐림이 글자 밖으로 사방에 번지기 때문이다

오프셋이 0 이면 그림자는 글자 바로 뒤, 같은 자리에 놓인다.
흐림 반경이 그 그림자의 가장자리를 사방으로 고르게 번지게 하므로 글자 둘레에 빛무리가 생긴다.
한쪽으로 치우친 오프셋이 없으니 「그림자」가 아니라 「빛」처럼 보인다.
근거: 2-summary 「동작 방식 (4)」, 원본 팁 「네온 효과는 offset 0, blur만 크게 설정」.

### 5. 진한 중심과 넓은 외곽을 함께 얻으려고

흐림을 크게 하면 그림자가 넓어지지만 그만큼 옅어진다.
작은 흐림(10px)은 글자 가까이 진한 빛을, 큰 흐림(40px)은 멀리 퍼지는 옅은 빛을 맡는다.
세 장을 겹치면 안쪽은 진하고 바깥으로 갈수록 옅어지는 빛무리가 된다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 4」.

### 6. 아무것도 보이지 않는다

옮기지도 번지지도 않은 그림자는 글자와 정확히 같은 자리, 같은 모양으로 글자 뒤에 깔린다.
그림자는 글자 뒤에 그려지므로 글자에 완전히 가려진다.
근거: 2-summary 「어디서 틀리나 2」 · 「동작 방식 (4)」.

### 7. 자리를 차지하지 않는다 — 겹치거나 잘릴 수 있다

그림자는 레이아웃에 공간을 만들지 않는다.
그래서 크게 번진 그림자는 이웃 요소 위로 겹치거나, `overflow: hidden` 인 부모의 가장자리에서 잘릴 수 있다.
근거: 2-summary 「어디서 틀리나 6」. (원본에 근거 없음 — CSS 명세에 기댄 서술)

### 8. `box-shadow` — `text-shadow` 는 글자에만 그려진다

`text-shadow` 는 글자 윤곽을 본떠 그림자를 만들므로 박스 테두리에는 그림자가 생기지 않는다.
카드처럼 요소의 박스 자체에 그림자를 주려면 `box-shadow` 를 쓴다.
근거: 2-summary 「언제 쓰고 언제 안 쓰나」 · 「용어 풀이」.

## 실습 정답

### 실습 1. 네 가지 글자 그림자 견본 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1단계 흐림 없는 회색 그림자 | `.basic { text-shadow: 2px 2px #94a3b8; }` |
| 2단계 흐림 + 반투명 검정 | `.blur { text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }` |
| 3단계 세 색 계단 그림자 | `.multi { text-shadow: 1px 1px #ef4444, 2px 2px #3b82f6, 3px 3px #22c55e; }` |
| 4단계 오프셋 0 네온 세 겹 | `.neon { text-shadow: 0 0 10px #8b5cf6, 0 0 20px #8b5cf6, 0 0 40px #8b5cf6; }` |
| 공통 꾸밈 · 네온 글자색 | 각 규칙의 `font-size` · `font-weight` · `margin-bottom`, `.neon` 의 `color` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/typography/reference/text-shadow.html`

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>text-shadow - 텍스트에 그림자 효과를 추가</title>
  <!--
    [타이포그래피] text-shadow
    설명: 텍스트에 그림자 효과를 추가
    구문: text-shadow: <offset-x> <offset-y> [<blur-radius>] [<color>]
    팁: 쉼표로 구분하여 여러 그림자를 중첩 가능. 네온 효과는 offset 0, blur만 크게 설정.
  -->
  <style>
    /* .basic: 단순 오프셋 그림자 (블러 없음) */
    .basic {
      text-shadow: 2px 2px #94a3b8;   /* offset-x=2px, offset-y=2px, blur 생략(0), color=회색 */
      font-size: 28px;                /* 효과를 보기 위한 큰 크기 */
      font-weight: bold;              /* 굵게 강조 */
      margin-bottom: 8px;             /* 다음 단락과 간격 */
    }

    /* .blur: 블러가 추가된 부드러운 그림자 */
    .blur {
      text-shadow: 2px 2px 4px rgba(0,0,0,0.3);  /* offset 2/2, blur 4px, 검정 30% 투명도 */
      font-size: 28px;                            /* 동일 크기 */
      font-weight: bold;                          /* 굵게 */
      margin-bottom: 8px;                         /* 다음 단락과 간격 */
    }

    /* .multi: 쉼표로 구분된 여러 그림자 중첩 */
    .multi {
      text-shadow: 1px 1px #ef4444, 2px 2px #3b82f6, 3px 3px #22c55e;  /* RGB 3색을 순차 오프셋해 입체감 */
      font-size: 28px;                                                   /* 동일 크기 */
      font-weight: bold;                                                 /* 굵게 */
      margin-bottom: 8px;                                                /* 다음 단락과 간격 */
    }

    /* .neon: offset 0 + 큰 blur로 네온 발광 효과 */
    .neon {
      text-shadow: 0 0 10px #8b5cf6, 0 0 20px #8b5cf6, 0 0 40px #8b5cf6; /* 동일 색상 그림자를 다른 blur로 겹쳐 발광 효과 */
      font-size: 28px;                                                    /* 동일 크기 */
      font-weight: bold;                                                  /* 굵게 */
      color: #c4b5fd;                                                     /* 본문 글자색을 옅게 해 네온 느낌 강조 */
    }
  </style>
</head>
<body>
  <!-- 기본 그림자 -->
  <p class="basic">Basic Shadow</p>
  <!-- 블러 그림자 -->
  <p class="blur">Blurred Shadow</p>
  <!-- 다중 그림자 -->
  <p class="multi">Multiple Shadows</p>
  <!-- 네온 발광 -->
  <p class="neon">Neon Glow</p>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.basic { text-shadow: 2px 2px #94a3b8; font-size: 28px; font-weight: bold; margin-bottom: 8px; }
.blur { text-shadow: 2px 2px 4px rgba(0,0,0,0.3); font-size: 28px; font-weight: bold; margin-bottom: 8px; }
.multi { text-shadow: 1px 1px #ef4444, 2px 2px #3b82f6, 3px 3px #22c55e; font-size: 28px; font-weight: bold; margin-bottom: 8px; }
.neon { text-shadow: 0 0 10px #8b5cf6, 0 0 20px #8b5cf6, 0 0 40px #8b5cf6; font-size: 28px; font-weight: bold; color: #c4b5fd; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**

- 오프셋 두 개는 꼭 쓰고, 흐림을 빼면 `.basic` 처럼 선명한 그림자가 된다.
- `.blur` 는 세 번째 길이로 흐림을, `rgba` 로 반투명을 준다.
- `.multi` 는 쉼표로 세 장을 잇고, 첫 장(빨강)이 맨 위에 그려진다.
- `.neon` 은 오프셋 0 이라 흐림이 없으면 보이지 않는다 — 흐림을 키우며 같은 색을 겹친다.
- 네온 글자색을 옅게 두면 글자가 광원처럼 보인다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

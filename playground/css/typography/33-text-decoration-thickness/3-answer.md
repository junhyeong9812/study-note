# css/typography/33 — text-decoration-thickness — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. px 는 그대로, em 과 % 는 두 배

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
         18px 일 때   36px 일 때
.a 2px   2px          2px
.b 0.1em 1.8px        3.6px
.c 10%   1.8px        3.6px
```

**왜 그런가**
`px` 는 고정 길이라 글자 크기와 상관없다.
`em` 은 그 요소의 `font-size` 의 배수라 0.1 × 18 = 1.8, 0.1 × 36 = 3.6 이다.
이 속성의 `%` 는 `font-size` 기준이라 10% 도 같은 계산이 된다.
근거: 2-summary 「동작 방식 (3)」.

### 2. 아무 장식도 보이지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
글자 아래에 선이 없다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
이 속성은 이미 있는 장식 선의 두께만 정한다.
`text-decoration: underline` 으로 선을 켜지 않았으니 두께를 적용할 대상이 없다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 1」.

### 3. 0.3초 동안 서서히 굵어지고, 뗄 때 서서히 돌아온다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
마우스를 올리면 밑줄이 1px 에서 4px 로 0.3초에 걸쳐 굵어지고, 떼면 같은 시간에 걸쳐 1px 로 돌아간다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
이 속성은 애니메이션 가능한 속성이다.
`transition` 이 두께를 걸어 두었으므로 두 길이 사이의 중간값을 이어 그린다.
근거: 2-summary 「동작 방식 (4)」.

### 4. 글자 크기를 따라 두께가 자동으로 맞춰지기 때문이다

em 과 % 는 그 요소의 `font-size` 를 기준으로 계산된다.
그래서 큰 제목에는 굵은 밑줄이, 작은 본문에는 가는 밑줄이 같은 비율로 붙는다.
px 를 쓰면 같은 두께가 큰 글자에는 가늘어 보이고 작은 글자에는 굵어 보일 수 있어, 크기마다 값을 따로 적어야 한다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 2」(원본 팁).

### 5. 기본값 auto — 브라우저가 정하므로 같다고 기대할 수 없다

지정하지 않으면 기본값 `auto` 가 쓰이고, `auto` 는 브라우저가 적절한 두께를 결정한다.
실제 몇 px 로 그릴지는 브라우저 구현에 달려 있어 어디서나 같다는 보장이 없다.
정확한 두께가 필요하면 `<length>` 로 직접 정한다.
근거: 2-summary 「동작 방식 (2)」 · 「구현 세부사항 대 언어 보장」.

### 6. 자식의 값은 기본값 auto 다

이 속성은 상속되지 않는다.
그래서 부모의 3px 이 자식의 값으로 넘어가지 않고, 자식에게 따로 주지 않으면 자식의 값은 기본값 `auto` 다.
근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 6」.

### 7. 각 문단이 쓰는 글꼴과 연결된다

`from-font` 는 글꼴에 지정된 두께를 쓰는 값이다.
두 문단의 글꼴이 다르면 글꼴마다 정해 둔 두께가 다르므로 밑줄 두께도 달라질 수 있다.
글꼴이 바뀌면 같은 CSS 라도 결과가 바뀐다.
근거: 2-summary 「동작 방식 (2)」 · 「구현 세부사항 대 언어 보장」.

### 8. text-decoration 은 선의 종류, thickness 는 그 선의 굵기

`text-decoration: underline` 은 「밑줄을 그린다」를 정한다.
`text-decoration-thickness` 는 그렇게 그린 선의 굵기를 정한다.
둘은 짝으로 쓰이며, 원본 예제의 세 클래스도 모두 밑줄을 켜고 두께를 따로 지정한다.
근거: 2-summary 「한눈에 — 쉽게 말하면」 · 「동작 방식 (1)」.

## 실습 정답

### 실습 1. 두께가 다른 밑줄 세 단락 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 세 단락에 밑줄 장식 | `.thin` · `.medium` · `.thick` 의 `text-decoration: underline` |
| 2. 두께는 이 속성으로만, 글자 크기는 같게 | 세 클래스의 `text-decoration-thickness` · 모두 `font-size: 18px` |
| 3. 얇게 · 중간 · 두껍게 | `.thin` 1px · `.medium` 3px · `.thick` 5px |
| 4. 고정 길이 단위 | `px` 로 쓴 세 두께 값 |
| 5. 크기 · 간격 유지 | `font-size: 18px` · `margin-bottom: 4px` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/typography/reference/text-decoration-thickness.html`

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>text-decoration-thickness - 텍스트 장식 선의 두께를 설정</title>
  <!--
    [타이포그래피] text-decoration-thickness
    설명: 텍스트 장식 선의 두께를 설정
    구문: text-decoration-thickness: auto | from-font | <length> | <percentage>
    팁: em이나 %를 사용하면 font-size에 비례하여 자동 조절. 호버 효과에 두께 변경 애니메이션 가능.
  -->
  <style>
    /* .thin: 얇은 밑줄 */
    .thin {
      text-decoration: underline;            /* 밑줄 장식 활성화 */
      text-decoration-thickness: 1px;        /* 선 두께 1px (절대값) */
      font-size: 18px;                       /* 본문 크기 */
      margin-bottom: 4px;                    /* 다음 단락과 간격 */
    }

    /* .medium: 중간 굵기 밑줄 */
    .medium {
      text-decoration: underline;            /* 밑줄 장식 */
      text-decoration-thickness: 3px;        /* 선 두께 3px */
      font-size: 18px;                       /* 본문 크기 */
      margin-bottom: 4px;                    /* 다음 단락과 간격 */
    }

    /* .thick: 두꺼운 밑줄 */
    .thick {
      text-decoration: underline;            /* 밑줄 장식 */
      text-decoration-thickness: 5px;        /* 선 두께 5px */
      font-size: 18px;                       /* 본문 크기 */
    }
  </style>
</head>
<body>
  <!-- 얇은 밑줄 -->
  <p class="thin">Thin (1px) 얇은 밑줄</p>
  <!-- 중간 밑줄 -->
  <p class="medium">Medium (3px) 중간 밑줄</p>
  <!-- 두꺼운 밑줄 -->
  <p class="thick">Thick (5px) 두꺼운 밑줄</p>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.thin { text-decoration: underline; text-decoration-thickness: 1px; font-size: 18px; margin-bottom: 4px; }
.medium { text-decoration: underline; text-decoration-thickness: 3px; font-size: 18px; margin-bottom: 4px; }
.thick { text-decoration: underline; text-decoration-thickness: 5px; font-size: 18px; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 두께는 선이 있어야 보이므로 각 클래스에 `text-decoration: underline` 을 먼저 둔다.
- 글자 크기를 셋 다 같게 두어 차이가 오직 `text-decoration-thickness` 에서 나오게 했다.
- 두께를 `px` 로 썼으므로 글자 크기를 바꿔도 밑줄 두께는 1 · 3 · 5px 그대로다.
- 크기가 다른 글자에 같은 비율로 쓰고 싶다면 `em` 이나 `%` 로 바꾸면 된다.
- 세 단락은 위에서 아래로 밑줄이 점점 굵어진다 (코드에서 읽은 것 — 렌더 실측 아님).

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

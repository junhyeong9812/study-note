# css/units-values/04 — % — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 콘텐츠 너비 100px, `padding-top` 40px — 둘 다 부모 너비 기준

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- `width: 25%` → 400 × 0.25 = 100px.
- `padding-top: 10%` → 부모 높이 1000px 이 아니라 너비 400px 기준이라 400 × 0.1 = 40px.

**왜 그런가**

`width` 의 `%` 는 부모 콘텐츠 너비를 기준으로 한다.
`padding` 의 `%` 는 위쪽 방향이어도 부모 너비(`inline-size`)를 기준으로 한다.
부모의 `height: 1000px` 은 두 값 어디에도 쓰이지 않는다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (2)」.

### 2. 부모 높이가 `auto` 라 `height: 100%` 도 `auto` 가 된다 — 글자 한 줄 높이

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`.box` 의 높이는 자기 내용, 곧 「글자 한 줄」의 높이로 정해진다.
파란 배경은 글자 한 줄 높이만큼만 칠해진다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**

`.wrap` 은 높이를 밝히지 않았으므로 높이가 `auto` 다.
`auto` 높이는 자식 내용으로 정해지므로, 자식이 그 높이의 100% 를 구하려 하면 서로를 기다리는 고리가 생긴다.
그래서 자식의 `height: 100%` 는 `auto` 로 계산된다.
근거: 2-summary 「동작 방식 (3)」 경우 ②.

### 3. 324px — 부모 바깥 오른쪽 끝을 12px 넘는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- 콘텐츠 너비: 300 × 1 = 300px.
- 테두리 바깥 너비: 300 + 12(왼쪽 `padding`) + 12(오른쪽 `padding`) = 324px.
- 자식은 부모 콘텐츠 영역의 왼쪽 끝(부모 바깥 왼쪽 끝에서 12px 안)에서 시작한다.
- 그래서 오른쪽 끝은 12 + 324 = 336px 지점이고, 부모 바깥 끝(12 + 300 + 12 = 324px)보다 12px 밖이다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**

기본 상자 모델에서 `width` 는 콘텐츠 영역만 정하고 `padding` 은 그 바깥에 더해진다.
원본 주석의 「100% = 300px」은 콘텐츠 너비 이야기이고 박스 전체 너비가 아니다.
근거: 2-summary 「어디서 틀리나 3」 · 「어디서 틀리나 4」.

### 4. 네 방향을 한 기준으로 맞추고, 높이와의 순환을 피하려고

- 네 방향이 모두 부모 너비 하나를 기준으로 하면 `padding: 5%` 한 줄로 사방이 같은 여백이 된다.
- 블록 높이는 보통 내용으로 정해지고 그 높이에 `padding` 이 들어간다. 세로 여백을 높이 기준으로 잡으면 높이와 여백이 서로를 정하는 고리가 생긴다.

근거: 2-summary 「동작 방식 (2)」 (원본에 근거 없음 — 추론).

### 5. 부모에 명시적 높이가 있어야 하고, 고정 높이를 만날 때까지 거슬러 올라간다

- 부모가 `200px` 같은 명시적 높이를 가져야 `height: 100%` 가 그 값을 채운다.
- 부모 높이도 `%` 라면, 그 부모의 부모 높이가 또 명시적이어야 한다. 고정 높이를 가진 조상에 닿을 때까지 사슬이 이어져야 한다.
- 사슬 중간에 `auto` 가 하나라도 끼면 그 아래의 `%` 높이는 `auto` 로 계산된다.

근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 2」.

### 6. 45px — 비율이 곱해진다

- 자식: 20 × 1.5 = 30px.
- 손자: 부모인 자식의 30px 이 기준이라 30 × 1.5 = 45px.
- 처음 20px 에서 보면 2.25배가 된다.

근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 5」.

### 7. `%` 는 따라 늘고 `px` 는 그대로다

- `width: 50%` 인 자식은 150px 에서 300px 로 늘어난다. 기준인 부모 너비가 바뀌었기 때문이다.
- `width: 150px` 인 자식은 부모와 상관없이 150px 그대로다.
- 그래서 부모 크기에 맞춰 비율을 유지할 때는 `%`, 크기가 변하면 안 될 때는 `px` 를 쓴다.

근거: 2-summary 「한눈에 — 쉽게 말하면」 · 「언제 쓰고 언제 안 쓰나」.

## 실습 정답

### 실습 1. 부모 너비의 50% · 75% · 100% 막대 쌓기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 부모 하나 안에 막대 세 개를 위에서 아래로 쌓기 | `<div class="parent">` 안의 `div` 세 개 (블록이라 차례로 쌓인다) |
| 첫째 막대 = 부모 너비의 절반 | `.child-50 { width: 50%; }` |
| 둘째 막대 = 부모 너비의 4분의 3 | `.child-75 { width: 75%; }` |
| 셋째 막대 = 부모 너비 전부 | `.child-100 { width: 100%; }` |
| 너비는 `%` 단위로만 | 세 규칙의 `width` 값 `50%` · `75%` · `100%` |
| 막대 안에 비율 글자 | `<div class="child-50">50%</div>` 등 세 요소의 글자 |
| 첫째 · 둘째 막대 아래 간격 | `.child-50` · `.child-75` 의 `margin-bottom` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/units-values/reference/percent.html`

```html
<!DOCTYPE html>                              <!-- HTML5 문서 타입 선언 -->
<html lang="ko">                              <!-- 문서 언어를 한국어로 지정 -->
<head>
<meta charset="utf-8">                       <!-- 문자 인코딩을 UTF-8로 설정 -->
<title>% - 부모 요소를 기준으로 한 백분율 단위. width는 부모 너비 기준, height는 부모 높이 기준, font-size는 부모 font-size 기준 등 속성마다 기준이 다르다</title>
<!--
  [CSS 단위 & 값] %
  설명: 부모 요소를 기준으로 한 백분율 단위. width는 부모 너비 기준, height는 부모 높이 기준, font-size는 부모 font-size 기준 등 속성마다 기준이 다르다
  구문: <number>%
  팁: padding/margin의 %는 항상 부모의 너비(inline-size) 기준. height: 100%가 동작하려면 부모에 명시적 높이가 필요.
-->
<style>
/* .parent: 부모 컨테이너 — 자식의 % 기준점 */
.parent {
  width: 300px;                               /* 부모 너비 300px → 자식 %의 기준 */
  padding: 12px;                              /* 안쪽 여백 12px */
  background: #f1f5f9;                        /* 연한 배경 */
  border-radius: 8px;                         /* 모서리 둥글기 8px */
}

/* .child-50: 부모 너비의 50% */
.child-50 {
  width: 50%;                                 /* 부모 300px의 50% = 150px */
  padding: 12px;                              /* 안쪽 여백 12px */
  margin-bottom: 8px;                         /* 아래 간격 */
  background: #3b82f6;                        /* 파란색 배경 */
  color: white;                               /* 흰 글자 */
  border-radius: 4px;                         /* 모서리 둥글기 */
  text-align: center;                         /* 가운데 정렬 */
  font-weight: 600;                           /* 굵은 글자 */
}

/* .child-75: 부모 너비의 75% */
.child-75 {
  width: 75%;                                 /* 부모 300px의 75% = 225px */
  padding: 12px;                              /* 안쪽 여백 */
  margin-bottom: 8px;                         /* 아래 간격 */
  background: #8b5cf6;                        /* 보라색 배경 */
  color: white;                               /* 흰 글자 */
  border-radius: 4px;                         /* 모서리 둥글기 */
  text-align: center;                         /* 가운데 정렬 */
  font-weight: 600;                           /* 굵은 글자 */
}

/* .child-100: 부모 너비의 100% (꽉 채움) */
.child-100 {
  width: 100%;                                /* 부모 300px의 100% = 300px */
  padding: 12px;                              /* 안쪽 여백 */
  background: #ef4444;                        /* 빨간색 배경 */
  color: white;                               /* 흰 글자 */
  border-radius: 4px;                         /* 모서리 둥글기 */
  text-align: center;                         /* 가운데 정렬 */
  font-weight: 600;                           /* 굵은 글자 */
}
</style>
</head>
<body>
<div class="parent">                          <!-- 300px 부모 -->
  <div class="child-50">50%</div>             <!-- 150px -->
  <div class="child-75">75%</div>             <!-- 225px -->
  <div class="child-100">100%</div>           <!-- 300px -->
</div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.parent { width: 300px; padding: 12px; background: #f1f5f9; border-radius: 8px; }
.child-50 { width: 50%; padding: 12px; margin-bottom: 8px; background: #3b82f6; color: white; border-radius: 4px; text-align: center; font-weight: 600; }
.child-75 { width: 75%; padding: 12px; margin-bottom: 8px; background: #8b5cf6; color: white; border-radius: 4px; text-align: center; font-weight: 600; }
.child-100 { width: 100%; padding: 12px; background: #ef4444; color: white; border-radius: 4px; text-align: center; font-weight: 600; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- `%` 의 기준은 `.parent` 의 `width: 300px`, 곧 부모의 콘텐츠 너비다. 부모의 `padding` 은 기준에 들지 않는다.
- 세 막대의 콘텐츠 너비는 150px · 225px · 300px 이 된다.
- 각 막대에 `padding: 12px` 이 더해지므로 박스 전체는 174px · 249px · 324px 이고, `.child-100` 은 부모 바깥으로 12px 넘친다. 딱 맞추려면 `box-sizing: border-box` 를 준다.
- `.parent` 의 `width` 만 바꾸면 세 막대가 모두 비율대로 따라 바뀐다 — `%` 를 쓰는 까닭이다.
- `margin-bottom` 은 고정 값이라 부모 크기와 상관없다. `%` 로 쓴다면 부모 너비 기준이 된다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

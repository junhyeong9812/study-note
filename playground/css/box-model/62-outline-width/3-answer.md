# css/box-model/62 — outline-width — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 계산된 두께는 0 — 외곽선은 보이지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

계산된 `outline-width` 는 0 이고, 외곽선은 보이지 않는다.

**왜 그런가**

`outline-style` 이 `none` 이면 `outline-width` 는 적힌 값(`thick`)과 상관없이 0 으로 계산된다.
선이 그려지지 않으니 `outline-color: red` 도 화면에 드러나지 않는다.
근거: 2-summary 「동작 방식 (2)」, 「어디서 틀리나 1」.

### 2. 자식은 부모의 8px 를 물려받지 않고 기본값 `medium` 을 쓴다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`.child` 의 두께는 기본값 `medium`(보통 3px)이다.

**왜 그런가**

`outline-width` 는 상속되지 않는다.
`.child` 에는 두께가 적혀 있지 않으므로 기본값 `medium` 이 쓰인다.
`outline-style: solid` 가 있으니 두께가 0 으로 바뀌지도 않는다.
근거: 2-summary 「동작 방식 (3)」.

### 3. 선 모양이 `none` 이면 두께가 0 으로 계산되기 때문이다

`outline-style` 이 `none` 이면 `outline-width` 는 0 으로 계산된다.
두께 4px 를 눈으로 보이려면 선 모양을 `solid` 처럼 `none` 이 아닌 값으로 정해야 한다.
정답 코드의 주석도 「style이 none이면 너비가 0이 됨」이라고 적는다.
근거: 2-summary 「동작 방식 (2)」.

### 4. 「대략」일 뿐 — 정확한 값은 브라우저가 정한다

원본은 `thin` 을 「보통 1px」, `medium` 을 「보통 3px」, `thick` 을 「보통 5px」로만 적었다.
즉 정확한 px 는 보장되지 않고 브라우저(구현)에 달려 있다.
두께를 픽셀 단위로 맞춰야 하면 길이값을 쓴다.
근거: 2-summary 「동작 방식 (1)」, 「구현 세부사항 대 언어 보장」, 「어디서 틀리나 2」.

### 5. 글자 크기에 비례해 두께가 서로 달라진다

`em` 은 글자 크기를 기준으로 하는 상대 단위다.
글자가 큰 요소일수록 `0.1em` 의 실제 길이가 커져 외곽선이 더 굵다.
`1px` 같은 고정 길이는 글자 크기와 상관없이 같은 두께다.
근거: 2-summary 「동작 방식 (1)」, 「어디서 틀리나 4」.

### 6. 「애니메이션 가능」이라는 성질 덕분이다

원본 재료에서 `outline-width` 는 애니메이션이 된다.
두 두께 사이의 중간값을 만들 수 있으므로 `transition: outline-width …` 를 걸면 1px → 4px 처럼 서서히 굵어진다.
근거: 2-summary 「동작 방식 (4)」.

### 7. 두께 · 모양 · 색으로 나눠 맡는다

`outline-width` 는 두께, `outline-style` 은 선의 모양(실선 등, `none` 이면 선 없음), `outline-color` 는 색을 맡는다.
셋 중 `outline-style` 이 `none` 이면 두께가 0 이 되어 나머지 둘이 드러나지 않는다.
근거: 2-summary 「한눈에 — 쉽게 말하면」, 「핵심 문장 1」.

## 실습 정답

### 실습 1. 두께 4px 실선 외곽선을 가진 상자 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| `box` 클래스 `div` 에 글자 넣기 | `<div class="box">outline-width</div>` |
| 외곽선 두께를 길이값으로 | `.box { outline-width: 4px; }` |
| 외곽선 모양을 실선으로 | `.box { outline-style: solid; }` |
| 색 · 여백 · 배경 그대로 | `outline-color` · `padding` · `background` 줄 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/box-model/reference/outline-width.html`

```html
<!DOCTYPE html> <!-- HTML5 문서 선언 -->
<html lang="ko"> <!-- 문서 언어를 한국어로 지정 -->
<head> <!-- 문서 메타정보 영역 -->
<meta charset="utf-8"> <!-- 문자 인코딩 UTF-8 설정 -->
<title>outline-width - 요소의 외곽선 너비를 설정</title> <!-- 브라우저 탭 제목 -->
<!--
  [박스 모델] outline-width
  설명: 요소의 외곽선 너비를 설정
  구문: outline-width: <length> | thin | medium | thick
  팁: outline-style이 none이면 outline-width가 0으로 계산됨.
-->
<style>
  /* .box: 외곽선 너비 시연 박스 */
  .box {
    outline-width: 4px;          /* 외곽선 두께 4px. 키워드(thin/medium/thick) 또는 길이값 */
    outline-style: solid;        /* 외곽선 스타일 실선 (style이 none이면 너비가 0이 됨) */
    outline-color: #3b82f6;      /* 외곽선 색상 파란색(#3b82f6) */
    padding: 16px;               /* 박스 내부 사방 16px 여백 */
    background: #f8fafc;         /* 배경색 매우 옅은 회색(#f8fafc) */
  }
</style>
</head>
<body>
  <div class="box">outline-width</div> <!-- 외곽선 너비가 적용된 박스 -->

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.box { outline-width: 4px; outline-style: solid; outline-color: #3b82f6; padding: 16px; background: #f8fafc; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 핵심 줄은 `outline-width: 4px;` 하나다 — 두께를 길이값으로 정확히 준다.
- `outline-style: solid;` 가 없으면 두께가 0 으로 계산되어 4px 가 보이지 않는다.
- 색은 `outline-color` 가 따로 맡으므로 두께 줄과 섞지 않는다.
- 4px 대신 `thin` · `medium` · `thick` 을 넣어 보면 키워드 두께의 차이를 비교할 수 있다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

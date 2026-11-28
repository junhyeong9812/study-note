# css/box-model/33 — border-bottom-width — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 선은 보이지 않고 두께는 0 이다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
파란 선은 보이지 않고, 아래쪽 테두리 두께는 0 으로 계산된다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`border-bottom-style` 을 적지 않았으므로 기본값 `none` 이다.
스타일이 `none` 이면 너비가 0 으로 계산된다는 규칙 때문에 5px 은 쓰이지 않는다.
근거: 2-summary 「동작 방식 (2)」, 「어디서 틀리나 1」.

### 2. 기본값 `medium` — 보통 3px

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
두께는 기본값 `medium` 으로 정해지고, 이는 보통 3px 이다.

**왜 그런가**
`border-bottom-width` 의 기본값은 `medium` 이다.
스타일이 `solid` 라 두께가 0 으로 바뀌지 않으므로 기본값이 그대로 쓰인다.
`medium` 의 정확한 px 은 원본이 「보통 3px」이라 적은 값이다.
근거: 2-summary 「동작 방식 (1)」, 「문법 — 형태와 규칙」 값 표.

### 3. 45px

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
바깥 높이는 40 + 0 + 5 = 45px 이다.

**왜 그런가**
기본 `box-sizing: content-box` 에서 `height` 는 내용 영역의 높이다.
아래쪽 테두리 5px 은 그 바깥에 더해진다.
근거: 2-summary 「동작 방식 (3)」.

### 4. 보이지 않는 선이 자리를 차지하지 않게 한다

스타일이 `none` 이면 그려질 선이 없다.
그런데도 두께가 남아 있다면 보이지 않는 선이 박스 높이를 늘리고 주변 요소를 밀어낼 것이다.
두께를 0 으로 보면 「선이 없으면 자리도 없다」가 성립한다.
근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (3)」 (규칙의 의미 해석은 원본에 근거 없음 — 추론).

### 5. 음수는 허용되지 않아 무시되고, 키워드는 px 이 고정이 아니다

- `-2px` 은 원본이 「양수 길이 값」만 허용하므로 잘못된 값이고, 그 선언은 무시되어 앞서 적용되던 값이 남는다.
- `thin` 의 1px 은 원본이 「보통」이라 적은 값이라 정확한 두께로 믿을 수 없다 — 정확한 두께가 필요하면 길이 값을 쓴다.

근거: 2-summary 「문법 — 형태와 규칙」, 「어디서 틀리나 3」, 「구현 세부사항 대 언어 보장」.

### 6. 갖지 않는다 — 상속되지 않는다

`border-bottom-width` 는 상속되지 않는다.
자식은 자기 기본값(`medium`)을 쓰지만, 스타일도 기본값 `none` 이라 두께는 0 이 되어 선이 없다.
근거: 2-summary 「동작 방식 (4)」, 「어디서 틀리나 5」.

### 7. 두께가 `medium` 으로 되돌아간다

뒤에 온 단축 속성 `border-bottom` 이 width · style · color 를 한꺼번에 다시 정한다.
두께를 빠뜨렸으므로 두께는 `medium` 으로 되돌려지고, 앞의 5px 은 덮인다.
5px 을 살리려면 개별 속성을 단축 속성 뒤에 적는다.
근거: 2-summary 「문법 — 형태와 규칙」, 「어디서 틀리나 2」.

### 8. 아래 내용이 4px 까지 밀려 내려간다

`border-bottom-width` 는 애니메이션할 수 있어 0 에서 4px 까지 사이값을 거치며 굵어진다.
테두리 두께는 박스 크기에 더해지므로, 두께가 커지는 동안 탭의 바깥 높이도 늘고 아래 내용이 함께 밀린다.
흔들림을 피하려면 두께를 처음부터 고정하고 색만 바꾼다.
근거: 2-summary 「동작 방식 (3)」 · 「동작 방식 (4)」, 「어디서 틀리나 4」.

## 실습 정답

### 실습 1. 아래쪽에만 굵은 파란 선이 있는 박스 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| `box` 클래스 `div` 와 글자 | `<div class="box">border-bottom-width</div>` |
| 아래쪽 두께를 길이 값으로 | `.box { border-bottom-width: 5px; }` |
| 아래쪽 선 모양을 실선으로 | `.box { border-bottom-style: solid; }` |
| 색 · 여백 · 배경 유지 | `border-bottom-color` · `padding` · `background` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/box-model/reference/border-bottom-width.html`

```html
<!DOCTYPE html> <!-- HTML5 문서 선언 -->
<html lang="ko"> <!-- 문서 언어를 한국어로 지정 -->
<head> <!-- 문서 메타정보 영역 -->
<meta charset="utf-8"> <!-- 문자 인코딩 UTF-8 설정 -->
<title>border-bottom-width - 요소의 아래쪽 테두리 너비를 설정</title> <!-- 브라우저 탭 제목 -->
<!--
  [박스 모델] border-bottom-width
  설명: 요소의 아래쪽 테두리 너비를 설정
  구문: border-bottom-width: <line-width>
  팁: border-bottom-style이 none이면 너비가 0으로 계산됨.
-->
<style>
  /* .box: 아래쪽 테두리 너비 시연 박스 */
  .box {
    border-bottom-width: 5px;       /* 아래쪽 테두리 두께 5px. 키워드(thin/medium/thick) 또는 길이값 가능 */
    border-bottom-style: solid;     /* 아래쪽 테두리 스타일 실선 (style이 없으면 너비가 0이 됨) */
    border-bottom-color: #3b82f6;   /* 아래쪽 테두리 색상 파란색(#3b82f6) */
    padding: 16px;                  /* 박스 내부 사방 16px 여백 */
    background: #f8fafc;            /* 배경색 매우 옅은 회색(#f8fafc) */
  }
</style>
</head>
<body>
  <div class="box">border-bottom-width</div> <!-- 아래쪽 테두리 너비가 적용된 박스 -->

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.box { border-bottom-width: 5px; border-bottom-style: solid; border-bottom-color: #3b82f6; padding: 16px; background: #f8fafc; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 핵심 줄은 `border-bottom-width: 5px;` 와 `border-bottom-style: solid;` 의 짝이다.
- 스타일 줄을 빼면 스타일이 기본값 `none` 이 되어 두께가 0 으로 계산되고, 선이 사라진다.
- 두께를 길이 값으로 적었으므로 키워드처럼 브라우저마다 달라질 여지가 없다.
- 위·왼쪽·오른쪽 스타일은 기본값 `none` 이라 아래쪽에만 선이 생긴다 (코드에서 읽은 것 — 렌더 실측 아님).
- 같은 결과를 `border-bottom: 5px solid #3b82f6;` 단축 속성 한 줄로도 낼 수 있다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

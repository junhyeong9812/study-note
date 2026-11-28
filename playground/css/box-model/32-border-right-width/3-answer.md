# css/box-model/32 — border-right-width — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 두께 0 — 선이 보이지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`border-right-style` 을 적지 않았으므로 스타일은 기본값 `none` 이다.
스타일이 `none` 이면 너비가 0 으로 계산되므로, 선언된 5px 과 상관없이 계산된 두께는 0 이고 선도 보이지 않는다.

**왜 그런가**
2-summary 「동작 방식 (2)」와 「어디서 틀리나 1」 — 원본 팁: 「border-right-style이 none이면 너비가 0으로 계산됨」.

### 2. 237px

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`content-box` 에서 `width: 200px` 은 내용 영역만이다.
왼쪽 테두리는 스타일이 없어 0, 안쪽 여백은 양쪽 16px 씩, 오른쪽 테두리는 `solid` 라서 5px 이 살아 있다.
0 + 16 + 200 + 16 + 5 = 237px 이다.

**왜 그런가**
2-summary 「동작 방식 (3)」 — 기본 상자에서는 padding 과 border 가 `width` 바깥에 더해진다.

### 3. 기본값 `medium` 으로 돌아간다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
단축 속성 `border-right` 에 두께가 빠져 있으므로 두께 조각은 기본값 `medium` 으로 다시 정해진다.
뒤에 쓴 선언이 이기므로 앞의 5px 은 사라지고 두께는 `medium`(보통 3px)이다.

**왜 그런가**
2-summary 「동작 방식 (4)」 · 「어디서 틀리나 4」 — 단축 속성은 적지 않은 조각을 기본값으로 되돌린다.

### 4. 두께는 그려질 선이 있을 때만 의미가 있다

스타일 기본값이 `none` 이고, 스타일이 `none` 이면 브라우저는 두께를 0 으로 계산한다.
계산된 값이 0 이므로 박스 모델에 더해질 테두리 몫도 0 이 되어 공간이 생기지 않는다.
근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (3)」.
「선이 없으면 두께도 없다」는 설계 의도는 원본이 직접 설명하지 않았다 (원본에 근거 없음 — 추론).

### 5. 음수는 무시되고, 키워드 px 은 「보통」일 뿐이다

- 값은 양수 길이여야 하므로 `-2px` 은 받아들여지지 않고 선언 전체가 무시된다.
  다른 선언이 없다면 기본값 `medium` 이, 앞서 적용되던 값이 있으면 그 값이 남는다.
- 원본은 `thick` 을 「보통 5px」 라고만 적었다 — 정확한 픽셀이 필요하면 길이 값을 직접 쓴다.

근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 2 · 5」 · 「구현 세부사항 대 언어 보장」.

### 6. 생기지 않는다 — 상속되지 않는다

`border-right-width` 는 상속되지 않으므로 자식 요소의 오른쪽 테두리 두께는 기본값 그대로다.
스타일도 상속되지 않아 자식의 스타일은 `none` 이므로 자식에게는 선이 없다.
근거: 2-summary 「동작 방식 (5)」 · 「문법 — 형태와 규칙」.

### 7. 애니메이션 가능 성질 — 스타일을 빠뜨리면 안 보인다

`border-right-width` 는 애니메이션 가능하므로 0 과 5px 사이의 중간 두께로 보간된다.
하지만 `border-right-style` 을 `solid` 같은 값으로 정하지 않으면 스타일이 `none` 이라 두께가 늘 0 으로 계산되어 변화가 보이지 않는다.
근거: 2-summary 「동작 방식 (5)」 · 「동작 방식 (2)」.

## 실습 정답

### 실습 1. 오른쪽에만 테두리가 있는 상자

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| `class="box"` 인 `div` 에 글자 | `<div class="box">border-right-width</div>` |
| 오른쪽 두께를 길이 값으로 | `.box { border-right-width: 5px; }` |
| 오른쪽 선이 그려지게 실선 | `.box { border-right-style: solid; }` |
| 다른 세 변에는 테두리 없음 | 단축 속성 없이 `border-right-*` 롱핸드만 사용 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/box-model/reference/border-right-width.html`

```html
<!DOCTYPE html> <!-- HTML5 문서 선언 -->
<html lang="ko"> <!-- 문서 언어를 한국어로 지정 -->
<head> <!-- 문서 메타정보 영역 -->
<meta charset="utf-8"> <!-- 문자 인코딩 UTF-8 설정 -->
<title>border-right-width - 요소의 오른쪽 테두리 너비를 설정</title> <!-- 브라우저 탭 제목 -->
<!--
  [박스 모델] border-right-width
  설명: 요소의 오른쪽 테두리 너비를 설정
  구문: border-right-width: <line-width>
  팁: border-right-style이 none이면 너비가 0으로 계산됨.
-->
<style>
  /* .box: 오른쪽 테두리 너비 시연 박스 */
  .box {
    border-right-width: 5px;        /* 오른쪽 테두리 두께 5px. 키워드(thin/medium/thick) 또는 길이값 */
    border-right-style: solid;      /* 오른쪽 테두리 스타일 실선 */
    border-right-color: #3b82f6;    /* 오른쪽 테두리 색상 파란색(#3b82f6) */
    padding: 16px;                  /* 박스 내부 사방 16px 여백 */
    background: #f8fafc;            /* 배경색 매우 옅은 회색(#f8fafc) */
  }
</style>
</head>
<body>
  <div class="box">border-right-width</div> <!-- 오른쪽 테두리 너비가 적용된 박스 -->

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.box { border-right-width: 5px; border-right-style: solid; border-right-color: #3b82f6; padding: 16px; background: #f8fafc; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 두께(`border-right-width`)와 스타일(`border-right-style`)을 함께 적어야 선이 생긴다.
- 스타일 줄을 빼면 두께가 0 으로 계산되어 선이 사라진다.
- 롱핸드만 썼기 때문에 위 · 아래 · 왼쪽 변은 스타일이 `none` 인 채로 남아 선이 없다.
- `content-box` 이므로 오른쪽 5px 이 상자 바깥 너비에 더해진다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

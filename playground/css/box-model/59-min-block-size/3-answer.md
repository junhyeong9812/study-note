# css/box-model/59 — min-block-size — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 132px — 최소값 100px 에 위아래 padding 이 더해진다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

콘텐츠 영역은 글 한 줄보다 큰 100px 로 끌어올려진다.
여기에 위 16px · 아래 16px 의 padding 이 붙어 테두리까지 132px 이다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**

`box-sizing` 기본값 `content-box` 에서 최소값은 콘텐츠 영역에 걸리고 padding 은 그 바깥에 더해진다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 3」.

### 2. 100px 을 넘어 글 20줄 높이만큼 늘어난다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

박스의 세로 크기는 글 20줄이 차지하는 높이가 된다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**

브라우저는 max(콘텐츠가 원하는 크기, 최소값)을 고른다.
최소값은 바닥일 뿐 천장이 아니다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 2」.

### 3. 쓰기 방향이 바뀌어도 같은 축을 따라가게 하려고

`min-height` 는 언제나 물리적인 세로를 막는다.
`min-block-size` 는 블록 방향을 막으므로 쓰기 모드가 바뀌면 그에 맞는 물리 방향으로 따라간다.
그래서 가로 쓰기 · 세로 쓰기 문서에 같은 CSS 를 쓸 수 있다.
근거: 2-summary 「동작 방식 (2)」 · 「언제 쓰고 언제 안 쓰나」.

### 4. 너비다

`vertical-rl` 에서는 줄이 오른쪽에서 왼쪽으로 쌓이므로 블록 방향이 가로다.
따라서 200px 은 박스 너비의 바닥이 되어 `min-width` 처럼 동작한다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 1」.

### 5. 자식은 부모 값을 물려받지 않고 자기 기본값을 쓴다

원본 재료에서 상속이 `False` 다.
부모의 최소 크기는 부모 박스에만 걸린다.
근거: 2-summary 「문법 — 형태와 규칙」.

### 6. 최소 크기가 만든 여유 공간의 세로 가운데에 글자를 놓는다

`min-block-size: 100px` 이 박스를 글보다 높게 만들어 세로로 빈 공간이 생긴다.
`display: flex` 의 기본 방향 `row` 에서 교차축은 세로이고, `align-items: center` 가 아이템을 교차축 가운데에 둔다.
그래서 글자가 100px 안의 세로 가운데에 온다.
근거: 2-summary 「동작 방식 (4)」.

### 7. 한 속성에 기본값이 두 개로 적혀 있어서

원본은 「기본값: `0`」이라고 적고, 값 목록에서는 「`auto` — 기본값」이라고 적는다.
기본값은 하나여야 하므로 둘 중 하나는 틀렸고, 원본만으로는 어느 쪽인지 가릴 수 없다 (확인 필요).
근거: 2-summary 「어디서 틀리나 4」 · 「구현 세부사항 대 언어 보장」.

### 8. 고정은 `block-size`, 상한은 `max-block-size`

`min-block-size` 는 아래 한도만 두므로 콘텐츠가 많으면 늘어난다.
딱 고정하려면 `block-size`, 위 한도를 두려면 `max-block-size` 를 쓴다.
근거: 2-summary 「어디서 틀리나 2」 · 「언제 쓰고 언제 안 쓰나」.

## 실습 정답

### 실습 1. 최소 블록 크기를 가진 파란 박스 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| `box` 클래스 `div` 에 글 넣기 | `<div class="box">min-block-size</div>` |
| 블록 방향 최소 크기 100px | `.box { min-block-size: 100px; }` |
| flex 컨테이너로 만들기 | `.box { display: flex; }` |
| 글자를 세로 가운데에 | `.box { align-items: center; }` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/box-model/reference/min-block-size.html`

```html
<!DOCTYPE html>                                                <!-- HTML5 문서 선언 -->
<html lang="ko">                                              <!-- 루트 요소, 한국어 문서 -->
<head>                                                        <!-- 문서 메타정보 영역 -->
<meta charset="utf-8">                                        <!-- 문자 인코딩 UTF-8 -->
<title>min-block-size - 블록 방향의 최소 크기를 설정하는 논리적 속성</title>
<!--
  [박스 모델] min-block-size
  설명: 블록 방향의 최소 크기를 설정하는 논리적 속성
  구문: min-block-size: auto | <length> | <percentage> | min-content | max-content | fit-content
  팁: 가로 쓰기에서 min-height에 매핑.
-->
<style>
/* .box: 블록축 최소 크기 시연 */
.box {
  min-block-size: 100px;           /* 블록축 최소 크기 100px - horizontal-tb면 min-height와 동일 */
  background: #3b82f6;             /* 배경색: 파란색 */
  padding: 16px;                   /* 안쪽 여백 16px */
  color: white;                    /* 글자색: 흰색 */
  border-radius: 4px;              /* 모서리 4px 둥글게 */
  display: flex;                   /* 플렉스 컨테이너 */
  align-items: center;             /* 교차축 가운데 정렬 */
}
</style>
</head>
<body>
<div class="box">min-block-size</div>                         <!-- 최소 블록축 크기 박스 -->

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.box { min-block-size: 100px; background: #3b82f6; padding: 16px; color: white; border-radius: 4px; display: flex; align-items: center; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**

- 핵심은 `min-block-size: 100px` 한 줄이다 — 가로 쓰기 문서라서 `min-height: 100px` 와 같은 축을 막는다.
- `padding: 16px` 이 바깥에 더해지므로 박스의 겉 세로 크기는 100px 보다 크다 (코드에서 읽은 것 — 렌더 실측 아님).
- `display: flex` 의 교차축이 세로이므로 `align-items: center` 가 글자를 세로 가운데에 놓는다.
- 글을 여러 줄로 늘리면 박스는 100px 을 넘어 커진다 — 최소값은 바닥일 뿐이다.
- `writing-mode: vertical-rl` 을 더하면 같은 선언이 너비의 바닥으로 바뀌는 것을 비교해 볼 수 있다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

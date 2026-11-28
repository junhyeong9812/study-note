# css/box-model/60 — max-block-size — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 92px 까지 자라고, 나머지 글은 상자 안 스크롤로 본다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
내용 영역은 60px 에서 멈춘다.
위아래 패딩 16px 씩이 더해져 배경 영역은 92px 이 된다.
넘친 글은 `overflow: auto` 때문에 상자 안 스크롤 막대로 넘겨 본다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
가로 쓰기에서 블록 방향은 세로라 상한이 높이에 걸린다.
`box-sizing` 기본값 `content-box` 에서는 상한이 내용 영역에만 걸리고 패딩은 바깥에 더해진다.
근거: 2-summary 「동작 방식 (1)」「(2)」「(4)」.

### 2. 너비에 걸린다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`vertical-rl` 에서는 줄이 오른쪽에서 왼쪽으로 쌓이므로 블록 방향이 가로다.
그래서 60px 상한은 내용 영역의 너비에 걸리고, 넘친 줄은 가로 스크롤로 보게 된다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
논리적 속성은 물리 방향이 아니라 블록·인라인 방향으로 말하므로, 쓰기 방향을 바꾸면 걸리는 축이 바뀐다.
근거: 2-summary 「동작 방식 (3)」. (원본에 근거 없음 — 추론: 원본은 가로 쓰기의 매핑만 적었다)

### 3. 상자 아래로 삐져나와 그려진다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
상자(배경)는 여전히 92px 에서 멈춘다.
`overflow` 기본값 `visible` 이라 넘친 글은 파란 배경 아래 바깥까지 그려지고, 뒤따르는 요소와 겹칠 수 있다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
상한은 상자의 크기만 묶고 내용을 줄이지 않는다.
넘친 내용의 처리는 `overflow` 몫이다.
근거: 2-summary 「동작 방식 (2)」, 「어디서 틀리나 2」.

### 4. 쓰기 방향이 바뀌어도 「줄이 쌓이는 방향」의 상한이라는 뜻이 유지되기 때문이다

`max-height` 는 언제나 물리적 세로에 걸린다.
세로 쓰기로 바꾸면 줄이 쌓이는 방향은 가로가 되므로 `max-height` 로는 원래 의도(글이 늘어나는 방향을 막기)가 어긋난다.
`max-block-size` 는 쓰기 방향을 따라가므로 같은 CSS 를 그대로 쓸 수 있다.
근거: 2-summary 「동작 방식 (3)」, 「언제 쓰고 언제 안 쓰나」.

### 5. 되지 않는다 — 내용이 필요한 만큼만 차지한다

상한은 「넘지 못하게」 할 뿐 크기를 정하지 않는다.
블록 크기는 min(필요 크기, 60px) 이므로 짧은 글이면 그 글 높이만큼만 된다.
항상 60px 이어야 한다면 `block-size` 를 쓴다.
근거: 2-summary 「동작 방식 (1)」, 「어디서 틀리나 4」.

### 6. 하한이 이겨 100px 이 된다

상한과 하한이 충돌하면 `min-block-size` 가 `max-block-size` 를 이긴다.
`min-height` 와 `max-height` 의 관계와 같다.
근거: 2-summary 「동작 방식 (5)」.

### 7. 걸리지 않는다 — 상속되지 않는 속성이다

원본 재료에 상속이 `False` 로 적혀 있다.
자식이 부모 안에 갇혀 보인다면 그것은 부모의 크기와 `overflow` 때문이다.
근거: 2-summary 「문법 — 형태와 규칙」, 「어디서 틀리나 5」.

### 8. `max-width` 에 대응하고, 한 줄 안 글자가 흐르는 방향의 상한이다

가로 쓰기에서 인라인 방향은 가로, 블록 방향은 세로다.
그래서 `max-inline-size` ≈ `max-width`, `max-block-size` ≈ `max-height` 이다.
둘은 같은 박스의 서로 다른 축을 맡는 짝이다.
근거: 2-summary 「동작 방식 (3)」.

## 실습 정답

### 실습 1. 길이를 모르는 글을 상한 안에 가두기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| `box` 클래스 `div` 에 긴 설명문 | `<div class="box">max-block-size는 …</div>` |
| 블록 방향 최대 크기를 논리 속성으로 60px 제한 | `.box { max-block-size: 60px; }` |
| 넘치면 상자 안에 스크롤 | `.box { overflow: auto; }` |
| 꾸밈은 그대로 | `.box` 의 `background` · `padding` · `color` · `border-radius` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/box-model/reference/max-block-size.html`

```html
<!DOCTYPE html>                                                <!-- HTML5 문서 선언 -->
<html lang="ko">                                              <!-- 루트 요소, 한국어 문서 -->
<head>                                                        <!-- 문서 메타정보 영역 -->
<meta charset="utf-8">                                        <!-- 문자 인코딩 UTF-8 -->
<title>max-block-size - 블록 방향의 최대 크기를 설정하는 논리적 속성</title>
<!--
  [박스 모델] max-block-size
  설명: 블록 방향의 최대 크기를 설정하는 논리적 속성
  구문: max-block-size: none | <length> | <percentage> | min-content | max-content | fit-content
  팁: 가로 쓰기에서 max-height에 매핑.
-->
<style>
/* .box: 블록축 최대 크기 제한 시연 */
.box {
  max-block-size: 60px;            /* 블록축 최대 크기 60px - horizontal-tb면 max-height와 동일 */
  overflow: auto;                  /* 콘텐츠가 넘치면 자동 스크롤 표시 */
  background: #3b82f6;             /* 배경색: 파란색 */
  padding: 16px;                   /* 안쪽 여백 16px */
  color: white;                    /* 글자색: 흰색 */
  border-radius: 4px;              /* 모서리 4px 둥글게 */
}
</style>
</head>
<body>
<div class="box">max-block-size는 블록 방향 최대 크기를 제한합니다. 넘치면 overflow에 따라 처리됩니다.</div>  <!-- 최대 크기 제한 박스 -->

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.box { max-block-size: 60px; overflow: auto; background: #3b82f6; padding: 16px; color: white; border-radius: 4px; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 핵심은 `max-block-size: 60px` 와 `overflow: auto` 두 줄이다.
- 가로 쓰기에서 이 상한은 `max-height: 60px` 와 같은 일을 한다.
- `padding: 16px` 가 바깥에 더해져 배경은 최대 92px 까지 자란다(`content-box` 기준).
- `overflow` 를 빼면 넘친 글이 상자 아래로 삐져나온다.
- 글이 짧아 한두 줄이면 상한은 아무 일도 하지 않는다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

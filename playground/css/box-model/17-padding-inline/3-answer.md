# css/box-model/17 — padding-inline — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 왼쪽 10px, 오른쪽 30px

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
첫째 값 10px 이 `padding-inline-start`, 둘째 값 30px 이 `padding-inline-end` 가 된다.
가로 쓰기에서 글은 왼쪽에서 시작하므로 왼쪽 10px, 오른쪽 30px 이다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
값 두 개의 순서는 「start, end」다.
`horizontal-tb` 에서 start 는 왼쪽, end 는 오른쪽이다.
근거: 2-summary 「동작 방식 (2)」.

### 2. 위와 아래

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
위 20px, 아래 20px 여백이 생기고 왼쪽 · 오른쪽에는 이 속성의 여백이 붙지 않는다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`vertical-rl` 에서는 글자가 위에서 아래로 흐르므로 인라인 축이 세로다.
`padding-inline` 은 인라인 축의 양쪽이므로 위 · 아래가 된다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 1」.

### 3. 쓰기 방향이 바뀌어도 여백이 글의 흐름을 따라간다 — 그리고 한 줄로 끝난다

`padding-inline` 은 물리 방향이 아니라 글의 흐름으로 정하는 논리적 속성이다.
`writing-mode` 가 바뀌면 코드를 고치지 않아도 여백이 새 인라인 축에 붙는다.
또 단축 속성이라 두 줄(`padding-left` + `padding-right`)을 한 줄로 줄인다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (3)」 · 「언제 쓰고 언제 안 쓰나」.

### 4. 둘 다 잘못된 선언이라 무시된다

`<length>` · `<percentage>` 모두 음수가 허용되지 않는다.
값은 1~2개만 받으므로 세 개짜리도 잘못된 선언이다.
잘못된 선언은 적용되지 않아 그 속성은 다른 규칙이나 기본값 `0` 을 따른다.
근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 3 · 4」.

### 5. 포함 블록의 인라인 크기의 10%

요소 자신의 폭이 아니라 포함 블록(보통 부모의 내용 영역)의 인라인 크기가 기준이다.
가로 쓰기에서 부모 폭이 400px 이면 양쪽 각 40px 이다.
근거: 2-summary 「문법 — 형태와 규칙」의 값 표 · 「어디서 틀리나 5」.

### 6. 블록 `div` 는 줄 전체 폭을 차지해 끝 쪽 여백이 배경에 묻히기 때문이다

블록 박스는 내용이 짧아도 줄 끝까지 늘어나 배경이 칠해진다.
그러면 끝 쪽 40px 여백이 남는 빈 공간과 구분되지 않는다.
`inline-block` 은 박스를 내용 폭 + 패딩으로 줄여 여백 크기가 박스 크기로 드러난다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 6」.

### 7. `padding-inline` 은 좌우, `padding-block` 은 위아래 — 합치면 네 면 모두

가로 쓰기에서 인라인 축은 가로, 블록 축은 세로다.
그래서 `padding-inline` 이 왼 · 오른, `padding-block` 이 위 · 아래를 맡는다.
둘을 함께 쓰면 네 면의 패딩을 모두 논리적 속성으로 정한다.
근거: 2-summary 「동작 방식 (4)」.

### 8. 갖지 않는다 — 상속되지 않는다

`padding-inline` 은 상속되지 않는 속성이다.
부모의 패딩은 부모 박스 안쪽에 공간을 만들 뿐, 자식의 `padding-inline` 은 기본값 `0` 그대로다.
근거: 2-summary 「문법 — 형태와 규칙」.

## 실습 정답

### 실습 1. 인라인 · 블록 축 패딩을 준 파란 라벨 박스

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| `class="box"` 인 `div` 와 글자 | `<div class="box">padding-inline</div>` |
| 인라인 축 양쪽 여백 값 하나 | `.box { padding-inline: 40px; }` |
| 블록 축 양쪽 여백 값 하나 | `.box { padding-block: 16px; }` |
| 물리 방향 속성 쓰지 않기 | `.box` 규칙에 `padding-left` 등이 없음 |
| 내용 폭만큼만 차지 | `.box { display: inline-block; }` |
| 꾸밈 그대로 | `background` · `color` · `border-radius` 줄 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/box-model/reference/padding-inline.html`

```html
<!DOCTYPE html>                                                <!-- HTML5 문서 선언 -->
<html lang="ko">                                              <!-- 루트 요소, 한국어 문서 -->
<head>                                                        <!-- 문서 메타정보 영역 -->
<meta charset="utf-8">                                        <!-- 문자 인코딩 UTF-8 -->
<title>padding-inline - 인라인 방향(가로 쓰기에서 좌우)의 안쪽 여백을 설정하는 논리적 단축 속성</title>
<!--
  [박스 모델] padding-inline
  설명: 인라인 방향(가로 쓰기에서 좌우)의 안쪽 여백을 설정하는 논리적 단축 속성
  구문: padding-inline: <length> | <percentage>
  팁: writing-mode에 따라 매핑 방향이 달라짐. 1~2개 값을 지정 가능 (start, end).
       1값=양쪽 동일, 2값=start/end 분리.
-->
<style>
/* .box: 인라인축 양쪽(좌우) 패딩 단축 시연 */
.box {
  padding-inline: 40px;            /* 인라인축 시작/끝 모두 40px - horizontal-tb면 padding-left+padding-right */
  padding-block: 16px;             /* 블록축 양쪽 모두 16px - horizontal-tb면 padding-top+padding-bottom */
  background: #3b82f6;             /* 배경색: 파란색 */
  color: white;                    /* 글자색: 흰색 */
  border-radius: 4px;              /* 모서리 4px 둥글게 */
  display: inline-block;           /* 인라인 블록 - 패딩 효과 시각화 */
}
</style>
</head>
<body>
<div class="box">padding-inline</div>                         <!-- 인라인축 양쪽 패딩 박스 -->

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.box { padding-inline: 40px; padding-block: 16px; background: #3b82f6; color: white; border-radius: 4px; display: inline-block; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**

- `padding-inline: 40px` 은 값이 하나라 인라인 축 시작 · 끝에 똑같이 40px 이 들어간다.
- 가로 쓰기가 기본이므로 이 박스에서는 좌우 40px, 위아래 16px 가 된다.
- `padding-block` 과 짝지어 네 면을 모두 논리적 속성으로 정했다.
- `display: inline-block` 이 박스를 글자 폭에 맞춰 줄여 패딩 크기가 눈에 보이게 한다.
- `.box` 에 `writing-mode: vertical-rl` 을 더하면 같은 코드로 여백이 위아래 40px 쪽으로 옮겨 간다 (코드에서 읽은 것 — 렌더 실측 아님).

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

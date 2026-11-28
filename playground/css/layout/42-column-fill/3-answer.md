# css/layout/42 — column-fill — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 아무것도 놓이지 않는다 — 첫 열에 다 들어간다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
한 문장이 첫 열에 모두 놓이고, 둘째 · 셋째 열은 비어 있다.

**왜 그런가**
`auto` 는 첫 열을 높이 끝까지 채운 뒤에야 다음 열로 넘긴다.
한 문장은 높이 안에 다 들어가므로 넘길 것이 없다.
근거: 2-summary 「동작 방식 (2)」.

### 2. `balance` 와 같은 모습이 된다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
문장이 세 열에 고르게 나뉘어 놓인다.

**왜 그런가**
높이가 없으면 「한 열이 가득 찼다」의 기준이 없다.
그래서 열 높이를 콘텐츠에 맞춰 고르게 정하고, 결과가 `balance` 와 같아진다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 1」.

### 3. 첫 번째 열에만 놓인다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
원본 예제에는 `height: 120px` 이 이미 있으므로, `auto` 로 바꾸면 짧은 문장은 첫 열에 모두 들어가고 나머지 두 열은 빈다(코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
높이가 있는 상태의 `auto` 는 순차 채우기다.
한 문장이 120px 높이를 넘칠 만큼 길지 않으므로 둘째 열로 넘어가지 않는다.
근거: 2-summary 「어디서 틀리나 3」 · 「동작 방식 (2)」.

### 4. 「한 열을 끝까지」의 끝을 정하는 것이 높이라서

`auto` 는 앞 열을 끝까지 채우고 넘치는 부분만 다음 열로 보내는 규칙이다.
그 「끝」이 컨테이너의 높이다.
높이가 없으면 끝이 없으니 열 높이를 고르게 정할 수밖에 없고, 그래서 `balance` 와 같아진다.
근거: 2-summary 「동작 방식 (3)」.

### 5. 설정이 `balance` 라서 고르게 나뉘기 때문이다

원본 예제는 `column-fill: balance` 를 쓴다.
`balance` 는 짧은 글도 세 열에 비슷한 양씩 나누므로, 뒤쪽 열이 비는 모습이 생기지 않는다.
문장이 말하는 모습을 보려면 `auto` 로 바꿔야 한다.
근거: 2-summary 「어디서 틀리나 3」.

### 6. 상속 안 됨 · 애니메이션 안 됨 · `balance-all` 은 미지원

- 상속되지 않으므로 자식 요소는 부모의 `auto` 를 물려받지 않고, 따로 주지 않으면 기본값 `balance` 다.
- 애니메이션 가능 값이 `False` 라서 `transition` 으로 부드럽게 옮길 수 없다.
- `balance-all` 은 원본이 미지원으로 적은 값이라 믿고 쓸 수 없다(지원 범위는 확인 필요).

근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 4 · 5」.

### 7. `column-fill` 은 「나누는 방식」만 정한다

- `column-count` 가 없으면 다단 컨테이너가 아니어서 열이 하나뿐이다.
  나눌 열이 없으니 나누는 방식이 달라도 차이가 보이지 않는다.
- 열 사이 간격은 `column-gap`, 구분선은 `column-rule` 이 정한다.
  `column-fill` 을 바꿔도 이 둘은 그대로다.

근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 2」.

## 실습 정답

### 실습 1. 짧은 글을 세 열에 고르게 펼치기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 세 개의 열을 가진 다단 컨테이너 | `.multicol { column-count: 3; }` |
| 균등 배분을 명시 | `.multicol { column-fill: balance; }` |
| 고정 높이 유지 | `.multicol { height: 120px; }` |
| 단락의 기본 바깥 여백 제거 | `p { margin: 0; }` |
| 짧은 문장 단락 하나 | `<div class="multicol"><p>Short text content …</p></div>` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/layout/reference/column-fill.html`

```html
<!DOCTYPE html>
<!-- HTML5 문서 선언 -->
<html lang="ko">
<head>
<meta charset="utf-8">
<title>column-fill - 다단 레이아웃에서 콘텐츠가 열에 배분되는 방식을 설정합니다</title>
<!--
  [레이아웃] column-fill
  설명: 다단 레이아웃에서 콘텐츠가 열에 배분되는 방식을 설정합니다
  구문: column-fill: auto | balance | balance-all
  팁: column-fill: auto가 동작하려면 다단 컨테이너에 높이(height)가 설정되어야 합니다. 높이가 없으면 balance와 동일하게 동작합니다.
-->
<style>
  /* .multicol: 3단 + 균형 분배 */
  .multicol {
    column-count: 3;             /* 3개 열 */
    column-fill: balance;        /* 열 높이를 균등 분배 */
    height: 120px;               /* 고정 높이 */
    column-gap: 20px;            /* 열 사이 간격 */
    column-rule: 1px solid #cbd5e1;  /* 열 구분선 */
    background: #f1f5f9;         /* 회색 배경 */
    padding: 16px;               /* 안쪽 여백 */
    border-radius: 4px;          /* 모서리 둥글게 */
  }
  /* p: 단락 기본 마진 제거 */
  p {
    margin: 0;                   /* 기본 마진 제거 */
  }
</style>
</head>
<body>
<!-- 짧은 텍스트가 세 열에 균형 있게 분배됨 -->
<div class="multicol">
  <p>Short text content that doesn't fill all columns evenly.</p>
</div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.multicol {
  column-count: 3;
  column-fill: balance;
  height: 120px;
  column-gap: 20px;
  column-rule: 1px solid #cbd5e1;
  background: #f1f5f9;
  padding: 16px;
  border-radius: 4px;
}
p {
  margin: 0;
}
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- `column-count: 3` 이 있어야 요소가 다단 컨테이너가 되고, 그때부터 `column-fill` 이 뜻을 갖는다.
- `column-fill: balance` 는 기본값이라 생략해도 같지만, 명시하면 의도가 드러난다.
- 높이가 있어도 `balance` 는 높이까지 채우지 않고 세 열에 고르게 나눈다 — 아래쪽이 남아 보일 수 있다(코드에서 읽은 것 — 렌더 실측 아님).
- 같은 코드에서 `auto` 로만 바꾸면 높이가 이미 있으므로 문장이 첫 열에 몰린다 — 두 값의 차이를 견주기 좋은 짝이다.
- `column-gap` · `column-rule` · 배경 · 여백은 꾸밈이며 열 채우기 방식과는 따로 논다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

# css/grid/28 — masonry-auto-flow — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 열2, 40px 지점부터 — 가장 짧은 열로 간다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
1·2·3번이 열1·열2·열3에 놓인 뒤 열 길이는 100 · 40 · 60 이다.
기본값 `pack` 은 가장 짧은 열을 고르므로 4번은 열2 의 2번 아래, 위에서 40px 지점부터 90px 까지 놓인다.

**왜 그런가**
`pack` 은 열의 현재 길이를 비교해 가장 빈 트랙에 넣는다.
근거: 2-summary 「동작 방식 (2)」.
(코드에서 읽은 것 — 렌더 실측 아님)

### 2. 열1, 100px 지점부터 — 직전 열의 다음 열로 간다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
직전 아이템 3번이 열3 에 있으므로 다음 열은 한 바퀴 돌아 열1 이다.
4번은 1번 아래, 위에서 100px 지점부터 150px 까지 놓인다.

**왜 그런가**
`next` 는 열 길이를 보지 않고 DOM 순서대로 다음 트랙에 넣는다.
근거: 2-summary 「동작 방식 (3)」.
(코드에서 읽은 것 — 렌더 실측 아님)

### 3. 둘째 행 첫 칸 — 2번 아래에는 빈칸이 생긴다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`masonry` 값을 모르는 브라우저는 그 선언을 버리고, 모르는 `masonry-auto-flow` 도 버린다.
평범한 그리드가 되어 1·2·3번이 첫 행, 4번이 둘째 행 첫 칸(열1)에 놓인다.
첫 행 높이는 가장 높은 1번(100px)에 맞춰지므로 2번(40px) 아래에 60px, 3번(60px) 아래에 40px 의 빈칸이 생긴다.

**왜 그런가**
CSS 는 잘못된 선언을 무시하고 나머지를 적용하며, 평범한 그리드의 행 높이는 그 행의 가장 큰 아이템을 따른다.
근거: 2-summary 「동작 방식 (5)」.
(코드에서 읽은 것 — 렌더 실측 아님)

### 4. 매번 가장 짧은 열을 채우기 때문이다

`pack` 은 아이템마다 열들의 현재 길이를 비교해 가장 짧은 열에 붙인다.
짧은 열이 계속 먼저 자라니 열 사이 차이가 벌어지지 않는다.
`next` 는 길이를 보지 않고 돌아가며 넣으므로 긴 열에도 또 쌓일 수 있다.
다만 `pack` 도 차이를 줄일 뿐 없애지는 않는다.
근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (3)」 · 「어디서 틀리나 3」.

### 5. 실험적 기능이라 일반 방문자 화면에서는 동작하지 않기 때문이다

원본 팁에 따르면 이 기능은 실험적이고, Firefox 에서도 `layout.css.grid-template-masonry-value.enabled` 플래그를 켜야 쓸 수 있다.
일반 방문자는 플래그를 켜지 않으므로 평범한 그리드로 보이게 된다.
그래서 모든 사용자에게 같은 벽돌 배치를 보이려면 JavaScript 라이브러리가 필요하다.
근거: 2-summary 「어디서 틀리나 1」 · 「동작 방식 (5)」.

### 6. 바뀌지 않는다

`masonry-auto-flow` 는 메이슨리 레이아웃에서의 배치만 정한다.
`grid-template-rows: masonry` 가 없으면 메이슨리 축이 없으니 할 일이 없다.
평범한 그리드의 자동 배치를 바꾸려면 `grid-auto-flow` 를 써야 한다.
근거: 2-summary 「어디서 틀리나 2」.

### 7. `definite-first` 는 먼저, `ordered` 는 셋째 차례에 놓는다

`definite-first` 에서는 위치가 지정된 그 아이템을 다른 아이템보다 먼저 열3 에 놓고, 나머지를 `pack`/`next` 규칙대로 놓는다.
`ordered` 에서는 1번 → 2번 → 그 아이템(열3) → … 처럼 DOM 순서대로 하나씩 놓는다.
차례가 달라지면 다른 아이템이 보는 열 길이가 달라지므로 나머지 배치도 바뀔 수 있다.
근거: 2-summary 「동작 방식 (4)」.

### 8. `dense` 는 평범한 그리드의 빈칸 메우기, `masonry-auto-flow` 는 메이슨리 축의 열 고르기다

`grid-auto-flow: dense` 는 행 트랙이 있는 평범한 그리드에서 자동 배치를 바꿔 앞쪽 빈칸을 메운다.
`masonry-auto-flow` 는 `grid-template-rows: masonry` 로 만든 메이슨리 레이아웃에서 다음 아이템이 들어갈 열을 고른다.
메이슨리에는 행 트랙 자체가 없어 아이템이 열 안에서 위로 바짝 붙으므로, 메우는 것이 아니라 붙일 열만 고른다.
근거: 2-summary 「동작 방식 (1)」 · 「언제 쓰고 언제 안 쓰나」 · 「어디서 틀리나 2」.

## 실습 정답

### 실습 1. 높이가 다른 다섯 카드를 세 열 벽돌로 쌓기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 그리드 컨테이너 | `.grid-container { display: grid; }` |
| 같은 너비 열 3개 | `grid-template-columns: repeat(3, 1fr);` |
| 행 축을 메이슨리로 | `grid-template-rows: masonry;` |
| 셀 사이 간격 | `gap: 8px;` |
| 높이가 다른 아이템 다섯 개 | `.item-1` ~ `.item-5` 의 인라인 `style="height:…"` |
| 기본값으로 배치 | `masonry-auto-flow` 선언 없음 → `pack` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/grid/reference/masonry-auto-flow.html`

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>masonry-auto-flow - 메이슨리(벽돌) 레이아웃에서 아이템의 배치 방식을 설정합니다 (실험적)</title>
<!--
  [그리드] masonry-auto-flow
  설명: 메이슨리(벽돌) 레이아웃에서 아이템의 배치 방식을 설정합니다 (실험적)
  구문: masonry-auto-flow: [ pack | next ] || [ definite-first | ordered ]
  팁: masonry-auto-flow는 아직 실험적 기능입니다. Firefox에서 layout.css.grid-template-masonry-value.enabled 플래그로 사용 가능합니다. 프로덕션에서는 JavaScript 라이브러리 사용을 권장합니다.
-->
<style>
  /* .grid-container: 행 축이 masonry → 핀터레스트 스타일 벽돌 쌓기 */
  .grid-container {
    display: grid;                          /* CSS Grid 활성화 */
    grid-template-columns: repeat(3, 1fr);  /* 3열, 각 1fr */
    grid-template-rows: masonry;            /* 행 축을 메이슨리로 (높이가 다른 아이템을 빈틈 없이 쌓음, 실험적) */
    gap: 8px;                               /* 셀 사이 간격 */
    padding: 16px;                          /* 내부 여백 */
    background: #f1f5f9;                    /* 배경색 */
    border-radius: 8px;                     /* 모서리 둥글게 */
  }

  /* .item: 셀 공통 스타일 */
  .item {
    border-radius: 6px;                     /* 모서리 둥글게 */
    font-weight: bold;                      /* 굵은 글씨 */
    font-size: 18px;                        /* 글자 크기 */
    color: white;                           /* 글자색 */
    display: flex;                          /* 플렉스 정렬 */
    align-items: center;                    /* 세로 가운데 */
    justify-content: center;                /* 가로 가운데 */
  }

  /* 아이템별 배경색 (높이는 인라인 스타일로 다양화) */
  .item-1 { background: #3b82f6; }
  .item-2 { background: #8b5cf6; }
  .item-3 { background: #ec4899; }
  .item-4 { background: #f59e0b; }
  .item-5 { background: #10b981; }
</style>
</head>
<body>
  <!-- 5개 아이템: 높이가 모두 다름 → 메이슨리에서 빈틈 없이 쌓임 -->
  <div class="grid-container">
    <div class="item item-1" style="height:80px">1</div>   <!-- 높이 80 -->
    <div class="item item-2" style="height:120px">2</div>  <!-- 높이 120 -->
    <div class="item item-3" style="height:60px">3</div>   <!-- 높이 60 -->
    <div class="item item-4" style="height:100px">4</div>  <!-- 높이 100 -->
    <div class="item item-5" style="height:70px">5</div>   <!-- 높이 70 -->
  </div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.grid-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: masonry;
  gap: 8px;
  padding: 16px;
  background: #f1f5f9;
  border-radius: 8px;
}
.item {
  border-radius: 6px;
  font-weight: bold;
  font-size: 18px;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
}
.item-1 { background: #3b82f6; }
.item-2 { background: #8b5cf6; }
.item-3 { background: #ec4899; }
.item-4 { background: #f59e0b; }
.item-5 { background: #10b981; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 정답 코드는 `masonry-auto-flow` 를 적지 않았으므로 기본값 `pack` 으로 배치된다.
- `pack` 이면 1~3번 뒤 열 길이가 88 · 128 · 68(간격 포함)이라 4번은 열3, 그다음 5번은 열1 로 간다 (원본에 근거 없음 — 추론, 코드에서 읽은 것 — 렌더 실측 아님).
- `masonry-auto-flow: next` 를 더하면 4번은 열1, 5번은 열2 로 가서 결과가 달라진다 (코드에서 읽은 것 — 렌더 실측 아님).
- 미지원 브라우저에서는 `grid-template-rows: masonry` 가 버려져 1·2·3 / 4·5 의 평범한 두 행이 된다.
- 주석의 「빈틈 없이」는 열 안의 위쪽 이야기이며, 열들의 아래 끝은 맞지 않는다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

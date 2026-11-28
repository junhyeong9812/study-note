# css/grid/26 — place-items — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 두 속성 모두 `center` — 아이템은 셀 정중앙

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`align-items: center` 와 `justify-items: center` 로 펼쳐진다.
셀보다 작은 아이템은 세로·가로 모두 가운데, 곧 셀 정중앙에 놓인다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
두 번째 값이 생략되면 첫 번째 값이 두 축에 쓰인다.
행 100px, 열 `1fr` 로 셀에 남는 자리가 있어 가운데 정렬이 드러난다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (3)」.

### 2. 셀 왼쪽 아래

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
아이템은 셀의 왼쪽 아래 구석에 놓인다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
첫 값 `end` 는 `align-items`(블록축 = 가로쓰기에서 세로)로 가서 셀 아래 끝이 된다.
둘째 값 `start` 는 `justify-items`(인라인축 = 가로)로 가서 셀 왼쪽이 된다.
근거: 2-summary 「동작 방식 (2)」.

### 3. 아이템이 셀을 꽉 채운다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
아이템 상자가 늘어나 셀 크기와 같아진다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
값 표에서 `stretch` 는 「양 축 모두 늘림」이다.
아이템에 너비·높이가 정해져 있지 않으니 두 축으로 셀을 채우도록 늘어난다.
근거: 2-summary 「문법 — 형태와 규칙」 값 표.

### 4. 생략된 두 번째 값이 첫 값을 따르기 때문이다

`place-items` 는 `align-items` 와 `justify-items` 의 단축 속성이고, 두 번째 값은 생략할 수 있다.
생략하면 `center` 가 두 속성에 모두 들어가 세로 가운데 + 가로 가운데 = 정중앙이 된다.
근거: 2-summary 「동작 방식 (1)」.

### 5. 변화가 보이지 않는다

정렬은 셀 안에 남는 자리 위에서 아이템을 어디 둘지 정하는 일이다.
셀과 아이템 크기가 같으면 남는 자리가 0 이라 어느 값이든 위치가 같다.
원본 예제가 `grid-auto-rows: 100px` 로 셀을 아이템보다 크게 만든 까닭이 이것이다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 3」.

### 6. 닿지 않는다 — 상속되지 않는다

`place-items` 는 상속이 `False` 다.
안쪽 그리드는 자기 `place-items` 가 따로 없으면 기본값 `normal` 로 동작한다.
가운데로 두려면 안쪽 그리드 컨테이너에도 따로 건다.
근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 4」.

### 7. 미끄러지지 않고 한 번에 바뀐다

`place-items` 는 애니메이션 가능하지 않으므로 값 사이를 보간하지 않는다.
`start` 에서 `end` 로 바뀌는 순간 아이템이 새 위치로 곧장 옮겨진다.
근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 5」.

### 8. 격자 전체는 `place-content`, 칸 안은 `place-items`

`place-content` 는 트랙 자체를 컨테이너 안에서 정렬하므로 격자 전체를 한가운데로 모은다.
`place-items` 는 각 셀 안에서 아이템의 위치를 정하므로 칸마다 아이템을 가운데 둔다.
원본 팁이 이 둘을 혼동하지 말라고 짚는다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 1」.

## 실습 정답

### 실습 1. 네 아이템을 각 칸 정중앙에 놓는 2열 그리드

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 그리드 컨테이너로 만든다 | `.grid-container { display: grid; }` |
| 2. 같은 비율의 두 열 | `grid-template-columns: 1fr 1fr;` |
| 3. 칸이 아이템보다 큰 행 높이 | `grid-auto-rows: 100px;` |
| 4. 단축 속성 하나로 양 축 가운데 | `place-items: center;` |
| 5. 아이템마다 다른 배경색 | `.item-1` ~ `.item-4` 의 `background` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/grid/reference/grid--place-items.html`

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>place-items - align-items와 justify-items의 단축 속성입니다</title>
<!--
  [그리드] place-items
  설명: align-items와 justify-items의 단축 속성입니다
  구문: place-items: <align-items> <justify-items>?
  팁: place-items: center는 그리드에서 셀 내부의 아이템을 정중앙에 배치합니다. place-content와 혼동하지 마세요 - place-content는 트랙 자체를 정렬합니다.
-->
<style>
  /* .grid-container: 셀 내부 아이템을 양 축 가운데 배치 */
  .grid-container {
    display: grid;                          /* CSS Grid 활성화 */
    grid-template-columns: 1fr 1fr;         /* 2열 (각 1fr) */
    grid-auto-rows: 100px;                  /* 행 높이 100px (셀이 아이템보다 큼) */
    place-items: center;                    /* align-items + justify-items 모두 center */
    gap: 8px;                               /* 셀 사이 간격 */
    padding: 16px;                          /* 내부 여백 */
    background: #f1f5f9;                    /* 배경색 */
    border-radius: 8px;                     /* 모서리 둥글게 */
  }

  /* .item: 셀 공통 스타일 (셀보다 작은 사이즈) */
  .item {
    padding: 16px 24px;                     /* 내부 여백 */
    border-radius: 6px;                     /* 모서리 둥글게 */
    font-weight: bold;                      /* 굵은 글씨 */
    font-size: 18px;                        /* 글자 크기 */
    color: white;                           /* 글자색 */
  }

  /* 아이템별 배경색 */
  .item-1 { background: #3b82f6; }
  .item-2 { background: #8b5cf6; }
  .item-3 { background: #ec4899; }
  .item-4 { background: #f59e0b; }
</style>
</head>
<body>
  <!-- 4개 아이템이 각 셀 정중앙에 배치됨 -->
  <div class="grid-container">
    <div class="item item-1">1</div>
    <div class="item item-2">2</div>
    <div class="item item-3">3</div>
    <div class="item item-4">4</div>
  </div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.grid-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-auto-rows: 100px;
  place-items: center;
  gap: 8px;
  padding: 16px;
  background: #f1f5f9;
  border-radius: 8px;
}
.item {
  padding: 16px 24px;
  border-radius: 6px;
  font-weight: bold;
  font-size: 18px;
  color: white;
}
.item-1 { background: #3b82f6; }
.item-2 { background: #8b5cf6; }
.item-3 { background: #ec4899; }
.item-4 { background: #f59e0b; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 핵심 줄은 `place-items: center;` 하나다 — `align-items` 와 `justify-items` 가 모두 `center` 가 된다.
- `grid-auto-rows: 100px` 과 `1fr 1fr` 열이 셀을 아이템보다 크게 만들어 가운데 정렬이 드러난다.
- 아이템에는 너비·높이가 없고 `padding` 만 있어 셀보다 작은 상자가 된다.
- `gap` 은 셀 사이 간격일 뿐 셀 안 정렬과는 무관하다.
- 격자 전체를 옮기려 했다면 `place-content` 를 써야 했다 — 이 과제는 칸 안 정렬이다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

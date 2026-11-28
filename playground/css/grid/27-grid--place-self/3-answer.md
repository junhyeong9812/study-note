# css/grid/27 — place-self — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 2행 1열 셀의 우하단

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
2열 그리드에서 아이템은 1행에 1·2번, 2행에 3·4번이 놓이므로 셋째 아이템은 2행 1열 셀에 있다.
`place-self: end` 는 값 하나라 세로 · 가로 모두 끝 쪽이 되어 그 셀의 우하단에 내용 크기로 놓인다(가로쓰기 · 왼쪽→오른쪽 문서 기준).

**왜 그런가**
값이 하나면 `align-self` 와 `justify-self` 에 같은 값이 들어간다 — 2-summary 「동작 방식 (1)」.
`end` 는 양 축 끝 정렬이다 — 2-summary 「동작 방식 (3)」.
2열 그리드에서 아이템이 행을 채워 나가는 순서는 원본 데모의 배치에서 읽은 것이다.

### 2. 세로 가운데, 가로 끝(오른쪽)

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
첫째 값 `center` 가 세로(블록축)로, 둘째 값 `end` 가 가로(인라인축)로 들어가 셀의 오른쪽 가장자리 세로 가운데에 놓인다.

**왜 그런가**
값이 둘이면 첫째가 `align-self`, 둘째가 `justify-self` 다 — 2-summary 「동작 방식 (1)」 · 「(2)」.

### 3. `.a` 는 정중앙, `.b` 는 좌상단

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`.a` 는 `place-self` 를 안 줬으니 기본값 `auto` 라 부모의 `place-items: center` 를 따라 셀 정중앙에 놓인다.
`.b` 는 자기 값 `start` 가 부모 값 대신 쓰여 셀 좌상단에 놓인다.

**왜 그런가**
`auto` 는 부모의 `place-items` 를 따르고, 자기 값을 주면 그 아이템에서만 부모 값을 이긴다 — 2-summary 「동작 방식 (4)」.

### 4. 한 점에 붙이느냐, 셀을 채우느냐의 차이다

`center` 는 아이템을 셀의 가운데 한 점에 붙이므로 아이템은 셀을 채우지 않고 내용 크기로 놓인다.
`stretch` 는 셀을 채우도록 아이템을 늘린다.
그래서 원본 데모에서 4번(`stretch`)만 셀 전체를 차지한다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 3」.

### 5. `align` 이 블록축, `justify` 가 인라인축을 맡기 때문이다

문법이 `<align-self> <justify-self>?` 순서로 정해져 있다.
`align` 은 블록축(가로쓰기 문서의 세로), `justify` 는 인라인축(가로)을 맡으므로 「세로 가로」 순서가 된다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 1」.

### 6. 옮길 수 없다 — 자기 셀 안에서만 움직인다

`place-self` 는 이미 정해진 셀 안에서의 위치와 크기만 바꾼다.
어느 셀에 놓일지는 바꾸지 않고, 이웃 아이템도 밀지 않는다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 4」.

### 7. 같은 속성을 물려받는 게 아니라 다른 속성의 값을 참조한다

CSS 상속은 자식이 부모의 **같은 속성** 값을 물려받는 것이고, `place-self` 는 상속되지 않는다.
`auto` 는 부모의 **다른 속성**인 `place-items` 의 값을 보고 그대로 따르는 것이다.
원본이 이것을 「상속」이라 부른 것은 말이 겹친 것이라, 같은 원본의 「상속: False」와 어긋나 보인다.
근거: 2-summary 「어디서 틀리나 5」 · 「동작 방식 (4)」.

## 실습 정답

### 실습 1. 네 아이템을 각자 다르게 셀 안에 놓기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 2열 그리드 · 행 높이 고정 · 컨테이너 정렬 없음 | `.grid-container { display: grid; grid-template-columns: 1fr 1fr; grid-auto-rows: … }` (정렬 속성 없음) |
| 아이템에 너비 · 높이 없음 | `.item { … }` (padding · 글꼴 · 색만) |
| 1번 좌상단 | `.item-1 { place-self: start; }` |
| 2번 정중앙 | `.item-2 { place-self: center; }` |
| 3번 우하단 | `.item-3 { place-self: end; }` |
| 4번 셀 전체 | `.item-4 { place-self: stretch; }` |
| 단축 속성 하나로 | 각 줄의 `place-self` 값 하나 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/grid/reference/grid--place-self.html`

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>place-self - align-self와 justify-self의 단축 속성입니다</title>
<!--
  [그리드] place-self
  설명: align-self와 justify-self의 단축 속성입니다
  구문: place-self: <align-self> <justify-self>?
  팁: 그리드에서 place-self: center를 사용하면 해당 아이템만 셀의 정중앙에 배치됩니다. 두 값을 지정하면 세로/가로를 각각 제어합니다.
-->
<style>
  /* .grid-container: 컨테이너에는 정렬 지정 안 함, 각 아이템이 자기 자리에서 다르게 정렬 */
  .grid-container {
    display: grid;                          /* CSS Grid 활성화 */
    grid-template-columns: 1fr 1fr;         /* 2열 (각 1fr) */
    grid-auto-rows: 100px;                  /* 행 높이 100px */
    gap: 8px;                               /* 셀 사이 간격 */
    padding: 16px;                          /* 내부 여백 */
    background: #f1f5f9;                    /* 배경색 */
    border-radius: 8px;                     /* 모서리 둥글게 */
  }

  /* .item: 셀 공통 스타일 */
  .item {
    padding: 12px 16px;                     /* 내부 여백 */
    border-radius: 6px;                     /* 모서리 둥글게 */
    font-weight: bold;                      /* 굵은 글씨 */
    font-size: 13px;                        /* 글자 크기 */
    color: white;                           /* 글자색 */
  }

  /* 아이템별로 다른 자기 정렬 적용 */
  .item-1 { background: #3b82f6; place-self: start; }   /* 좌상단 정렬 */
  .item-2 { background: #8b5cf6; place-self: center; }  /* 셀 정중앙 */
  .item-3 { background: #ec4899; place-self: end; }     /* 우하단 정렬 */
  .item-4 { background: #f59e0b; place-self: stretch; } /* 셀 전체로 확장 */
</style>
</head>
<body>
  <!-- 4개 아이템이 각자 다른 위치/크기로 배치되는 데모 -->
  <div class="grid-container">
    <div class="item item-1">1</div>
    <div class="item item-2">2 (place-self: center)</div>
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
  gap: 8px;
  padding: 16px;
  background: #f1f5f9;
  border-radius: 8px;
}
.item {
  padding: 12px 16px;
  border-radius: 6px;
  font-weight: bold;
  font-size: 13px;
  color: white;
}
.item-1 { background: #3b82f6; place-self: start; }
.item-2 { background: #8b5cf6; place-self: center; }
.item-3 { background: #ec4899; place-self: end; }
.item-4 { background: #f59e0b; place-self: stretch; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 값 하나만 주면 세로 · 가로 양쪽에 같은 정렬이 들어간다.
- 컨테이너에 정렬을 안 줬으니 각 아이템의 `place-self` 가 그대로 드러난다.
- `start` · `center` · `end` 아이템은 내용 크기로 줄고, `stretch` 아이템만 셀을 채운다.
- 아이템에 너비 · 높이를 주지 않아야 `stretch` 가 셀을 채운다. (원본에 근거 없음 — 추론)
- 「좌상단 · 우하단」은 가로쓰기 · 왼쪽→오른쪽 문서를 기준으로 한 말이다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |

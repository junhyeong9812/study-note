# css/syntax/26 — flex 줄바꿈·`gap`·`order` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 좌표를 맞히거나, **무엇이 안 바뀌는지**를 맞히는 것을 묻는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 넘치면 알아서 줄바꿈되는가 (예측)

```css
.c { display: flex; width: 300px; }
.c i { flex: 0 0 120px; }   /* 항목 셋 = 360px */
```

- 항목 셋은 한 줄에 놓이는가, 두 줄에 놓이는가?
- 셋째 항목의 오른쪽 끝은 몇 px 인가?
- `flex-wrap: wrap` 을 켜면 어떻게 바뀌는가 — 컨테이너 높이까지 답하라.
- `wrap-reverse` 는 무엇을 뒤집는가 — 항목 순서인가 줄 쌓임 방향인가?

### 2. 줄이 여럿일 때 크기 해결 (연결)

- 자유 공간은 컨테이너 전체에서 한 번 계산되는가, 줄마다 계산되는가?
- 그래서 카드 그리드의 **마지막 줄**에서 무슨 일이 생기는가?
- 열 수를 정확히 맞춰야 하는 레이아웃에 flex 를 쓰면 안 되는 이유는 무엇인가?

### 3. ★ `align-items` 와 `align-content` (예측)

```css
.c { display: flex; flex-wrap: wrap; width: 260px; height: 200px; }
/* 항목 넷의 높이는 20 / 60 / 20 / 40 이고 두 줄에 나뉜다 */
```

- `align-content: center` 만 줬을 때 네 항목의 y 좌표는?
- `align-items: center` 만 줬을 때 네 항목의 y 좌표는?
- 두 결과에서 **같은 줄의 두 항목의 y 가 같은가 다른가** — 그것이 무엇을 말해 주는가?
- 아무것도 안 줬을 때 줄의 높이는 왜 자연 높이보다 커지는가?

### 4. ★★ `align-content` 가 안 먹는 조건 (경계)

```css
/* 컨테이너 260×200, 항목 하나(높이 20). 줄은 어느 경우든 하나뿐이다. */
.a { display: flex; flex-wrap: nowrap; align-content: center; }
.b { display: flex; flex-wrap: wrap;   align-content: center; }
```

- `.a` 에서 항목의 y 는 몇인가?
- `.b` 에서 항목의 y 는 몇인가?
- 둘을 가르는 것은 「줄이 몇 개인가」인가, 「`flex-wrap` 값이 무엇인가」인가?
- 두 경우 `getComputedStyle(c).alignContent` 는 각각 무엇을 돌려주는가 — 그것으로 진단이 되는가?
- 한 줄짜리 컨테이너에서 세로 가운데를 맞추려면 무엇을 써야 하는가?

### 5. `gap` 과 마진은 무엇이 다른가 (예측)

```css
/* 컨테이너 300px, 항목 셋 flex: 1 1 0 */
.g   { gap: 20px; }
.m i { margin-right: 20px; }
```

- `.g` 의 세 항목의 `[왼쪽→오른쪽]` 좌표는?
- `.m` 의 세 항목의 좌표는 — 셋째 항목의 오른쪽 끝은 컨테이너 끝과 같은가?
- `margin: 0 10px` 로 바꾸면 무엇이 더 달라지는가?
- flex 항목끼리 마진 상쇄가 일어나는가 — 그래서 `margin: 0 10px` 셋의 사이 간격은 몇 px 인가?

### 6. `gap` 은 고정 간격인가 (예측)

```css
/* 컨테이너 300px, 항목 셋 flex: 0 0 60px */
.c { gap: 20px; justify-content: space-between; }
```

- 세 항목의 좌표는? 실제 간격은 몇 px 인가?
- `gap` 은 「고정 간격」인가 「최소 간격」인가?
- 같은 것을 `margin-right: 20px` 로 했다면 좌표가 어떻게 달라지는가?

### 7. 줄바꿈에서의 `gap` (경계)

```css
.c { display: flex; flex-wrap: wrap; width: 260px; gap: 10px 20px; }
.c i { flex: 0 0 110px; height: 30px; }   /* 항목 넷 */
```

- `10px` 와 `20px` 는 각각 어느 방향인가?
- 네 항목의 (x, y) 좌표는?
- 컨테이너 높이는 몇 px 인가?
- `row-gap` 은 줄이 하나일 때 무슨 일을 하는가?

### 8. ★ `order` 가 바꾸는 것과 안 바꾸는 것 (예측)

```html
<nav>
  <a href="#" id="A">A</a>
  <a href="#" id="B">B</a>
  <a href="#" id="C" class="first">C</a>
</nav>
<style> nav { display: flex } .first { order: -1 } </style>
```

- 화면 왼쪽부터의 순서는 무엇인가?
- `nav.querySelector('a:first-child')` 가 잡는 것은 누구인가?
- `nav.textContent` 는 무엇인가?
- `Tab` 키를 세 번 누르면 포커스는 어떤 순서로 가는가?
- 이 중 `order` 가 실제로 바꾼 것은 무엇 하나인가?

### 9. `order` 와 겹침 (예측)

```css
/* 항목 둘이 40px 겹치게 배치 (width 120, margin-right -40) */
.swap i:nth-child(1) { order: 1; }
```

- `order` 가 없을 때 겹친 구간에서 **위에 보이는** 것은 1 인가 2 인가?
- `order: 1` 을 첫 항목에 주면 어느 쪽이 위가 되는가?
- 둘 다에 `position: relative; z-index: 0` 을 줘도 결과가 같은가?
- 이 사실이 실무에서 만드는 함정은 무엇인가?

### 10. 유효하지 않은 값 (경계)

```css
.c  { gap: -10px; }
.i  { order: 1.5; }
.i2 { order: -1; }
.c2 { flex-wrap: reverse; }
```

- 넷 중 살아남는 것은 무엇인가?
- 버려진 것들은 에러를 내는가 — 어떻게 확인하는가?
- `gap` 은 컨테이너에 주는가 항목에 주는가?

### 11. 다른 주제와 잇기 (연결)

- 정렬 값(`flex-start`·`space-between` 등)의 뜻 자체는 목록의 몇 번 주제가 정본인가?
- 항목 하나의 크기가 정해지는 규칙은 몇 번 주제인가?
- 열을 정확히 맞춰야 하는 레이아웃은 무엇으로 옮기는가?
- `order` 가 건드리는 「누가 위인가」의 정본은 몇 번 주제인가?
- `place-content` 는 무엇의 단축이고 값의 순서는 어떻게 되는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

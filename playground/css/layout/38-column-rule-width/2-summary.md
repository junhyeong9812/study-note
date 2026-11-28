# css/layout/38 — column-rule-width — 정리 (힌트)

> 출처 — study-site 항목 `css/column-rule-width`(항목 데이터 `data/css/layout.json`) · 정답 코드 study-practice `css/layout/reference/column-rule-width.html`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

## 한눈에 — 쉽게 말하면

**`column-rule-width` 는 「신문 지면의 세로 칸막이 선을 얼마나 굵게 긋나」다.**
신문은 기사 한 편을 여러 단으로 나눠 싣고, 단과 단 사이에 세로 줄을 긋는다.
그 세로 줄의 굵기만 정하는 손잡이가 `column-rule-width` 다.
CSS 다단 레이아웃도 똑같은 구조다.
글을 여러 열로 흘리고, 열 사이 틈에 구분선을 긋고, 그 선의 두께를 이 속성이 정한다.

> **다단 레이아웃** — 한 요소의 내용을 신문처럼 여러 열로 나눠 흘리는 배치 방식이다.\
> 예: `column-count: 3` 을 준 `div` 안의 문단은 세 열로 나뉘어 흐른다.

> **열 구분선(column rule)** — 다단 레이아웃에서 이웃한 두 열 사이에 긋는 세로 선이다.\
> 예: `column-rule-style: solid` 를 주면 열 사이에 실선이 생긴다.

| 비유 | 실체 |
|---|---|
| 신문 지면 | 다단 컨테이너 (`.multicol`) |
| 단 | 열 (`column-count` 로 개수를 정함) |
| 단 사이 여백 | `column-gap` |
| 세로 칸막이 선의 굵기 | `column-rule-width` |
| 선의 모양(실선 · 점선) | `column-rule-style` |
| 선의 잉크 색 | `column-rule-color` |

```text
 ┌──────────────────────────────────────────┐
 │  열 1        ┃   열 2        ┃   열 3     │
 │  글 글 글    ┃   글 글 글    ┃   글 글    │
 │  글 글 글    ┃   글 글 글    ┃   글 글    │
 └──────────────────────────────────────────┘
               ↑               ↑
        이 선의 굵기 = column-rule-width
```

## 이 주제가 답하려는 질문

1. 열 구분선의 두께는 어떤 값으로 정하나?
2. 두께를 줬는데 선이 안 보이는 것은 왜인가?
3. 두께 하나로 선이 그려지나, 아니면 다른 속성이 함께 있어야 하나?
4. 두께는 상속되나, 애니메이션되나?

## 동작 방식

### (1) 두께는 세 속성 중 하나일 뿐이다

**언제 쓰나** — 다단 레이아웃의 열 사이에 선을 긋고, 그 굵기를 바꾸고 싶을 때 쓴다.

```text
column-count: 3            → 내용이 세 열로 나뉜다
column-rule-style: solid   → 열 사이에 선을 「그린다」고 정한다
column-rule-width: 3px     → 그 선의 굵기를 3px 로 정한다
column-rule-color: 파랑    → 그 선의 색을 정한다
        ↓
결과: 세 열 사이 두 곳에 굵기 3px 의 파란 실선
```

- 첫째 줄이 다단 컨테이너를 만든다.
- 둘째 줄이 선을 그릴지 말지와 모양을 정한다.
- 셋째 줄은 이미 그리기로 한 선의 굵기만 바꾼다.
- 넷째 줄은 그 선의 색을 정한다.
- 열이 세 개면 열 「사이」는 두 곳이므로 선도 두 개다 — 바깥 가장자리에는 선이 없다.

### (2) 스타일이 `none` 이면 두께는 아무 일도 하지 않는다

**언제 쓰나** — 두께를 줬는데 선이 안 보일 때 가장 먼저 확인할 자리다.

```text
column-rule-width: 3px
column-rule-style: (쓰지 않음 → none)
        ↓
선을 그리지 않기로 정해져 있다
        ↓
결과: 두께 값이 있어도 구분선이 보이지 않는다
```

- `column-rule-style` 을 쓰지 않으면 선을 그리지 않는 상태(`none`)로 남는다(확인 필요 — 원본에는 style 의 기본값이 적혀 있지 않다).
- 원본 팁 그대로, 스타일이 `none` 이면 두께 값이 있어도 구분선은 표시되지 않는다.
- 그래서 두께만 바꿔서는 선이 생기지 않고, 스타일을 함께 줘야 한다.

### (3) 값의 종류 — 키워드 셋과 길이

**언제 쓰나** — 정확한 굵기가 필요하면 길이를, 대충의 굵기면 키워드를 쓴다.

```text
thin   → 얇은 선
medium → 기본 두께 (아무것도 안 주면 이것)
thick  → 두꺼운 선
3px    → 정확히 그 길이만큼
-2px   → 음수 불가 → 선언이 잘못된 값으로 버려진다
```

- 키워드 셋은 「얇다 ≤ 보통 ≤ 두껍다」의 순서만 정한다.
- 길이는 고정 길이이고 음수를 받지 않는다.
- CSS 는 잘못된 값을 가진 선언을 무시하므로, 음수를 주면 그 줄이 없는 것처럼 되어 이전 값(또는 기본값 `medium`)이 남는다.

### (4) 상속되지 않고, 애니메이션된다

**언제 쓰나** — 부모 · 자식 모두 다단일 때, 또는 마우스를 올리면 선이 굵어지는 효과를 만들 때다.

```text
부모 .outer { column-rule-width: 8px }
  └ 자식 .inner { column-count: 2; column-rule-style: solid }
        ↓  상속 안 됨
결과: 자식의 선 두께는 8px 가 아니라 기본값 medium

.multicol { transition: column-rule-width 0.3s }
.multicol:hover { column-rule-width: 10px }
        ↓  애니메이션 가능
결과: 올리는 동안 선이 3px → 10px 로 점점 굵어진다
```

- 상속이 `False` 이므로 부모의 값은 자식에게 내려가지 않는다.
- 애니메이션 가능이 `True` 이므로 두 길이 사이를 `transition` 으로 부드럽게 옮길 수 있다.

```html demo
<div style="column-count:3; column-gap:20px; column-rule-style:solid; column-rule-width:thick; column-rule-color:#3b82f6; padding:16px; background:#f1f5f9;">
  <p style="margin:0">신문처럼 세 열로 나뉜 글이다. 열 사이에 두꺼운 파란 세로선이 그어진다. 선은 열 사이 두 곳에만 있다.</p>
</div>
```

> **보이는 것** — 회색 상자 안에서 글이 세 열로 나뉘고, 열 사이 두 곳에 두꺼운 파란 세로선이 보인다 (코드에서 읽은 것 — 렌더 실측 아님)

## 문법 — 형태와 규칙

```css
.multicol {
  column-count: 3;
  column-gap: 20px;
  column-rule-style: solid;    /* 이것이 없으면 아래 두께는 소용없다 */
  column-rule-width: 3px;      /* 또는 thin | medium | thick */
  column-rule-color: #3b82f6;
}

/* 같은 뜻의 단축 속성 */
.multicol2 {
  column-count: 3;
  column-rule: 3px solid #3b82f6;
}
```

| 값 | 뜻 |
|---|---|
| `thin` | 얇은 구분선 |
| `medium` | 기본 두께의 구분선 (기본값) |
| `thick` | 두꺼운 구분선 |
| `<length>` | 고정 길이의 두께 — 음수 불가 |

- 문법: `column-rule-width: thin | medium | thick | <length>`.
- 기본값: `medium`.
- 상속: 안 됨.
- 애니메이션: 됨.
- `column-rule` 단축 속성은 두께 · 스타일 · 색을 한 줄에 묶는다.
- 두께는 테두리 두께(`border-width`)와 같은 키워드 셋(`thin` · `medium` · `thick`)을 쓰고, 스타일 없이는 보이지 않는다는 점도 테두리와 닮았다.

> **단축 속성** — 여러 속성을 한 줄에 묶어 쓰는 속성이다.\
> 예: `column-rule: 3px solid blue` 는 두께 · 스타일 · 색을 한꺼번에 준다.

## 어디서 틀리나

### 1. 두께만 주고 스타일을 빼먹는다

원본 팁: `column-rule-style` 이 `none` 이면 두께 값이 있어도 구분선이 표시되지 않는다.
두께 · 색을 아무리 고쳐도 선이 안 보이면 스타일부터 본다.

### 2. 다단이 아닌 요소에 준다

열 구분선은 열 「사이」에 그어지므로 열이 하나뿐이면 그을 자리가 없다.
`column-count` (또는 다단을 만드는 다른 속성)가 없는 요소에 주면 아무것도 보이지 않는다.

### 3. 음수 길이를 준다

`<length>` 는 음수를 받지 않는다.
`-3px` 같은 값을 주면 선언이 무시되고 기본값 `medium` 이 남는다.

### 4. 부모에 주고 자식에서 기대한다

상속되지 않으므로 다단 컨테이너마다 직접 준다.

### 5. 키워드의 정확한 px 을 가정한다

원본은 `thin` · `medium` · `thick` 을 얇다 · 기본 · 두껍다로만 설명하고 픽셀 값을 적지 않는다.
픽셀까지 맞춰야 하는 디자인이면 길이 값을 쓴다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 스타일이 `none` 이면 두께가 있어도 선이 안 보인다 | CSS 명세 (원본 팁) |
| 기본값 `medium` · 상속 안 됨 · 애니메이션 가능 | CSS 명세 (원본 재료) |
| `thin` ≤ `medium` ≤ `thick` 의 순서 | CSS 명세 |
| 각 키워드가 정확히 몇 px 인가 | 원본에 없음 — 브라우저 · 명세 판에 따라 다를 수 있음 (확인 필요) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 다단 글의 열 사이 선 굵기만 바꾸기 | `column-rule-width` | `border-*` (열 사이에 그어지지 않는다) |
| 굵기 · 모양 · 색을 한 번에 | `column-rule` 단축 | 세 줄 나눠 쓰기(되지만 길다) |
| 정확한 픽셀 굵기 | 길이 값 (`3px`) | `thin` · `thick` 키워드 |
| 선을 아예 없애기 | `column-rule-style: none` | `column-rule-width` 만 줄이기 |

## 핵심 문장

1. **`column-rule-width` 는 열 구분선의 굵기만 정한다** — 선을 그릴지는 `column-rule-style` 이 정한다.
2. **스타일이 `none` 이면 두께는 보이지 않는다.**
3. **값은 `thin` · `medium`(기본) · `thick` 또는 음수가 아닌 길이다.**
4. **상속되지 않고, 두께 변화는 애니메이션된다.**
5. **선은 열 사이에만 그어진다** — 열이 N 개면 선은 N−1 개다.

## 관련 자료

- [column-rule](../37-column-rule/2-summary.md)
- [column-rule-style](../39-column-rule-style/2-summary.md)
- [column-rule-color](../40-column-rule-color/2-summary.md)
- 원본: study-site 항목 데이터 `data/css/layout.json` 의 `column-rule-width`

## 용어 풀이

- **다단 레이아웃** — 내용을 여러 열로 나눠 흘리는 배치 방식.
- **열 구분선(column rule)** — 이웃한 두 열 사이의 세로 선.
- **`column-count`** — 열의 개수를 정하는 속성.
- **`column-gap`** — 열 사이 간격을 정하는 속성.
- **`column-rule-style`** — 구분선의 모양(실선 · 점선 등, 또는 `none`)을 정하는 속성.
- **`column-rule-color`** — 구분선의 색을 정하는 속성.
- **`column-rule`** — 두께 · 스타일 · 색을 묶은 단축 속성.
- **단축 속성** — 여러 속성을 한 줄에 묶은 속성.
- **상속** — 부모의 값이 자식에게 자동으로 내려가는 것.
- **`<length>`** — `px` · `em` 처럼 단위가 붙은 길이 값.

## 더 들어가면

- 구분선은 자리를 차지하지 않고 `column-gap` 의 가운데에 그려진다고 알려져 있다 — 선이 간격보다 두꺼우면 열 내용과 겹칠 수 있다 (확인 필요).
- 최근 명세 판은 `thin` · `medium` · `thick` 을 1px · 3px · 5px 로 정해 둔다는 서술이 있다 (확인 필요).
- `column-rule-style` 이 `none` 이나 `hidden` 이면 계산된 두께 자체가 0 이 된다는 규칙이 `border-width` 와 같은 꼴로 있다 (확인 필요).
- 두께에 백분율은 받지 않는 것으로 알려져 있다 (확인 필요).

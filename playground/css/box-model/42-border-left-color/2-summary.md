# css/box-model/42 — border-left-color — 정리 (힌트)

> 출처 — study-site 항목 `css/border-left-color`(항목 데이터 `data/css/box-model.json`) · 정답 코드 study-practice `css/box-model/reference/border-left-color.html`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

## 한눈에 — 쉽게 말하면

**`border-left-color` 는 「공책 왼쪽 여백선의 펜 색」이다.**
여백선을 긋겠다고 정해야(선 모양) 펜 색이 의미가 있다.
펜 색을 따로 고르지 않으면 지금 글씨를 쓰는 펜 색(글자색)으로 긋는다.
CSS 박스의 왼쪽 테두리도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 공책 한 쪽 | 요소의 박스 |
| 왼쪽 여백선 | 왼쪽 테두리(`border-left`) |
| 여백선을 긋기로 정함 | `border-left-style` 이 `none` 이 아님 |
| 여백선의 펜 색 | `border-left-color` |
| 글씨 쓰는 펜 색 | `color` (= `currentcolor`) |

```text
┌──────────────────────┐
█  border-left-color   │   █ = 왼쪽 테두리 (이 색만 border-left-color 가 정한다)
█                      │   나머지 세 변은 손대지 않는다
└──────────────────────┘
```

## 이 주제가 답하려는 질문

1. 왼쪽 테두리 하나의 색만 어떻게 따로 바꾸나?
2. 색을 지정하지 않으면 테두리는 무슨 색이 되나?
3. 단축 속성 `border-left` 와 함께 쓰면 어느 쪽이 이기나?
4. 테두리 색은 상속되나, 애니메이션되나?

## 동작 방식

### (1) 왼쪽 변 하나의 색만 정한다

**언제 쓰나** — 카드 · 인용문 · 알림 상자의 왼쪽에 강조 줄을 긋고 그 색만 바꾸고 싶을 때.

```text
입력:  .box { border-left: 4px solid; border-left-color: #ef4444; }
  → 왼쪽 테두리: 두께 4px, 실선 (border-left 가 정함)
  → 왼쪽 테두리 색: #ef4444 (border-left-color 가 덮어씀)
결과:  왼쪽에만 빨간 4px 줄 (코드에서 읽은 것 — 렌더 실측 아님)
```

- 첫 줄의 단축 속성이 두께와 선 모양을 정한다.
- 색을 빼고 썼으므로 이 순간 색은 기본값 `currentcolor` 가 된다.
- 다음 줄의 `border-left-color` 가 색만 빨간색으로 다시 정한다.
- 위 · 오른쪽 · 아래 테두리는 아무 영향도 받지 않는다.

> **테두리(border)** — 박스의 padding 바깥, margin 안쪽을 두르는 선이다.\
> 예: `border-left: 4px solid` 는 왼쪽 변에만 4px 실선을 긋는다.

### (2) 기본값 `currentcolor` — 글자색을 따라간다

**언제 쓰나** — 테두리 색을 글자색과 늘 맞추고 싶을 때. 색을 일부러 비워 두면 된다.

```text
입력:  .tag { color: green; border-left: 3px solid; }
  → border-left-color 를 아무도 정하지 않음 → 기본값 currentcolor
  → currentcolor = 이 요소의 color = green
결과:  왼쪽 테두리가 초록 (코드에서 읽은 것 — 렌더 실측 아님)
```

- 원본의 팁이 바로 이것이다: 기본값은 `currentcolor`.
- `currentcolor` 는 「이 요소의 현재 텍스트 색상」이다.
- 그래서 나중에 `color` 만 바꿔도 테두리 색이 함께 바뀐다.

> **currentcolor** — 그 요소의 `color` 계산값을 가리키는 색 키워드다.\
> 예: `color: navy` 인 요소에서 `border-left-color: currentcolor` 는 남색이다.

### (3) 단축 속성과 쓰는 차례

**언제 쓰나** — `border-left` 와 `border-left-color` 를 한 규칙에 같이 쓸 때.

```text
입력 A:  border-left: 4px solid;  border-left-color: red;
  → 단축이 색을 currentcolor 로 맞춤 → 다음 줄이 red 로 덮음
결과 A:  빨강

입력 B:  border-left-color: red;  border-left: 4px solid;
  → red 로 정함 → 단축이 (색을 안 썼으니) currentcolor 로 되돌림
결과 B:  글자색
```

- 단축 속성은 적지 않은 하위 값도 기본값으로 되돌린다.
- 같은 규칙 안에서는 뒤에 쓴 선언이 이긴다.
- 그래서 개별 속성은 단축 속성 **뒤에** 쓴다 — 원본 예제의 순서가 이것이다.

> **단축 속성(shorthand)** — 여러 개별 속성을 한 줄로 정하는 속성이다.\
> 예: `border-left` 는 왼쪽 테두리의 두께 · 선 모양 · 색을 한꺼번에 정한다.

### (4) 선 모양이 없으면 색은 보이지 않는다

**언제 쓰나** — 「색을 줬는데 테두리가 안 보인다」를 고칠 때.

```text
입력:  .x { border-left-color: red; }
  → border-left-style 은 기본값 none
  → 선이 없으니 두께도 0 으로 계산됨
결과:  아무 테두리도 안 보임 (코드에서 읽은 것 — 렌더 실측 아님)
```

- `border-left-color` 는 색만 정하지 선을 만들지는 않는다.
- 선 모양(`solid` 등)이 있어야 색이 칠해질 자리가 생긴다.

### (5) 상속되지 않고, 애니메이션된다

**언제 쓰나** — 부모 · 자식 관계에서 테두리 색을 예상할 때, 그리고 hover 때 색을 부드럽게 바꿀 때.

```text
입력:  .card { border-left: 4px solid #94a3b8; transition: border-left-color .3s; }
       .card:hover { border-left-color: #ef4444; }
  → 색 값끼리는 중간값을 계산할 수 있다 (애니메이션 가능)
결과:  마우스를 올리면 회색에서 빨강으로 서서히 바뀜 (코드에서 읽은 것 — 렌더 실측 아님)
```

- 원본 데이터: 상속 `False`, 애니메이션 가능 `True`.
- 상속되지 않으므로 부모에 준 `border-left-color` 는 자식 테두리에 넘어가지 않는다.
- 다만 자식의 기본값 `currentcolor` 는 자식의 `color` 를 따르고, `color` 는 상속되는 속성이라 결과적으로 부모의 글자색이 비칠 수 있다.

## 문법 — 형태와 규칙

```html demo
<p class="note">왼쪽에만 색 있는 줄</p>
<style>
  .note {
    color: #1e293b;
    border-left: 6px solid;          /* 두께 + 선 모양, 색은 비움 */
    border-left-color: #3b82f6;      /* 왼쪽 테두리 색만 파랑 */
    padding: 8px 12px;
  }
</style>
```

> **보이는 것** — 진한 글자의 문단 왼쪽에 파란 굵은 세로줄이 하나 있다 (코드에서 읽은 것 — 렌더 실측 아님)

| 항목 | 값 |
|---|---|
| 문법 | `border-left-color: <color>` |
| 기본값 | `currentcolor` |
| 상속 | 안 됨 |
| 애니메이션 | 됨 |

| 값 | 뜻 |
|---|---|
| `<color>` | CSS 색상 값 — `#ef4444`, `rgb(...)`, `red`, `transparent` 등 |
| `currentcolor` | 요소의 현재 텍스트 색상 |

- 값은 하나만 받는다(왼쪽 한 변의 색이므로).
- 선이 보이려면 `border-left-style` 이 `none` · `hidden` 이 아니어야 한다.
- 단축 속성과 같이 쓰면 단축 속성 뒤에 쓴다.

## 어디서 틀리나

### 1. 기본값을 잊는다

원본 팁: 기본값은 `currentcolor`.
색을 안 줬는데 테두리가 검게 나온다면, 그건 「테두리 기본색이 검정」이라서가 아니라 글자색이 검정이라서다.
글자색을 바꾸면 테두리도 따라 바뀐다는 점을 놓치기 쉽다.

### 2. 색만 주고 선 모양을 안 준다

`border-left-color` 하나만 쓰면 선 모양이 `none` 이라 아무것도 보이지 않는다.

### 3. 단축 속성을 뒤에 써서 색이 지워진다

`border-left-color: red;` 다음에 `border-left: 4px solid;` 를 쓰면 색이 `currentcolor` 로 돌아간다.

### 4. 상속될 거라 믿는다

부모에 준 `border-left-color` 는 자식에게 가지 않는다.
자식 테두리 색이 부모와 같아 보인다면 대개 상속된 `color` 를 `currentcolor` 가 따라간 것이다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 기본값이 `currentcolor` 다 | CSS 명세 (원본 데이터와 일치) |
| 상속되지 않는다 · 애니메이션된다 | CSS 명세 (원본 데이터와 일치) |
| 단축 속성이 빠진 하위 값을 기본값으로 되돌린다 | CSS 명세 (원본에 근거 없음 — 추론) |
| 왼쪽 테두리와 위 · 아래 테두리가 만나는 모서리의 경계 모양 · 안티에일리어싱 | 브라우저 렌더링 (확인 필요) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 왼쪽 강조 줄의 색만 바꾸기 | `border-left-color` | `border-color` (네 변이 다 바뀜) |
| 처음부터 왼쪽 줄을 한 번에 정의 | `border-left: 4px solid red` | 세 개별 속성을 따로따로 |
| 테두리를 글자색과 늘 맞추기 | 색을 비우거나 `currentcolor` | 글자색과 같은 고정 색을 두 번 적기 |
| hover 때 줄 색만 부드럽게 변경 | `transition: border-left-color` | `transition: all` (원치 않는 속성까지 움직임) |

## 핵심 문장

1. **`border-left-color` 는 왼쪽 테두리 한 변의 색만 정한다** — 다른 변과 두께 · 선 모양은 그대로다.
2. **기본값은 `currentcolor`** — 색을 안 주면 글자색을 따라간다.
3. **선 모양이 없으면 색은 보이지 않는다** — 색은 선을 만들지 않는다.
4. **단축 속성 `border-left` 는 색을 되돌린다** — 개별 속성은 그 뒤에 쓴다.
5. **상속되지 않고, 애니메이션된다.**

## 관련 자료

- `border-color` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `border-left` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [border-left-style](../38-border-left-style/2-summary.md)
- 원본: study-site 항목 데이터 `data/css/box-model.json` 의 `border-left-color`

## 용어 풀이

- **테두리(border)** — padding 바깥, margin 안쪽을 두르는 선.
- **`border-left`** — 왼쪽 테두리의 두께 · 선 모양 · 색을 한 번에 정하는 단축 속성.
- **`border-left-style`** — 왼쪽 테두리의 선 모양(`solid` · `dashed` · `none` 등).
- **`currentcolor`** — 그 요소의 `color` 값을 가리키는 색 키워드.
- **단축 속성** — 여러 개별 속성을 한 줄로 정하는 속성.
- **상속** — 부모의 값이 자식에게 기본으로 넘어가는 것.
- **애니메이션 가능** — 두 값 사이 중간값을 계산해 `transition` · `animation` 으로 서서히 바꿀 수 있다는 뜻.

## 더 들어가면

- 쓰기 방향에 따라 변을 고르는 논리 속성 `border-inline-start-color` 가 있다 — 가로쓰기 · 왼→오 문서에서는 왼쪽 변과 같다 (확인 필요).
- `border-color` 에 값을 넷 주면 위 · 오른쪽 · 아래 · 왼쪽 차례이므로 네 번째 값이 왼쪽 색이다 (확인 필요).
- `transparent` 를 주면 선의 자리(두께)는 남고 색만 투명해져, 레이아웃을 흔들지 않고 테두리를 숨길 수 있다 (확인 필요).
- `currentcolor` 를 기본값으로 둔 채 `color` 를 transition 하면 테두리 색도 함께 바뀌어 보인다 (확인 필요).

# css/box-model/38 — border-left-style — 정리 (힌트)

> 출처 — study-site 항목 `css/border-left-style`(항목 데이터 `data/css/box-model.json`) · 정답 코드 study-practice `css/box-model/reference/border-left-style.html`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

## 한눈에 — 쉽게 말하면

**`border-left-style` 은 「공책 왼쪽 여백선을 어떤 펜으로 긋나」를 정하는 속성이다.**
공책 왼쪽에 세로줄을 그으려면 펜 종류(실선 · 점선 · 두 줄)를 먼저 골라야 한다.
펜을 고르지 않으면 굵기와 색을 정해 두어도 줄은 그어지지 않는다.
요소의 왼쪽 테두리도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 공책 한 장 | 요소의 박스 |
| 왼쪽 세로줄 | 왼쪽 테두리(border-left) |
| 펜 종류 | `border-left-style` 값 |
| 펜 굵기 | `border-left-width` |
| 잉크 색 | `border-left-color` |
| 펜을 안 고름 | 기본값 `none` → 줄이 없다 |

```text
  왼쪽 테두리
     │
     ▼
   ┃ ┌──────────────────────┐
   ┃ │ padding               │
   ┃ │   내용(content)        │
   ┃ └──────────────────────┘
   ▲
   style = 선 모양 (solid ┃ / dashed ╏ / dotted ⋮ / double ‖ …)
```

> **테두리(border)** — 박스의 padding 바깥, margin 안쪽을 두르는 선이다.\
> 예: `border-left-style: solid` 는 이 선의 왼쪽 변을 실선으로 만든다.

## 이 주제가 답하려는 질문

1. 왼쪽 변 하나에만 테두리 모양을 주려면 무엇을 쓰나?
2. 고를 수 있는 선 모양은 무엇이 있고, `none` 과 `hidden` 은 어떻게 다른가?
3. 두께와 색만 주고 모양을 주지 않으면 왜 테두리가 보이지 않나?
4. 모양을 바꿀 때 왜 부드럽게 넘어가지 않나?

## 동작 방식

### (1) 왼쪽 변 하나에만 선 모양을 정한다

**언제 쓰나** — 인용문 · 알림 상자 · 선택된 메뉴처럼 왼쪽에만 강조 선을 그을 때 쓴다.

```text
입력                                  무엇이 일어나나                  결과
.box {                               왼쪽 변의 style = solid          왼쪽에만 4px 파란 실선
  border-left-style: solid;    ──▶   왼쪽 변의 width = 4px     ──▶   위·오른쪽·아래 변은
  border-left-width: 4px;            왼쪽 변의 color = 파랑            style 이 none 이라 선 없음
  border-left-color: #3b82f6;
}
```

- 이 세 선언은 모두 「왼쪽 변」 하나만 건드린다.
- 나머지 세 변의 style 은 기본값 `none` 그대로다.
- 그래서 왼쪽에만 선이 생긴다 (코드에서 읽은 것 — 렌더 실측 아님).

> **변(side)** — 박스 테두리의 네 쪽(top · right · bottom · left) 가운데 하나다.\
> 예: `border-left-*` 는 left 변만 다룬다.

### (2) style 이 없으면 선도 없다

**언제 쓰나** — 「두께와 색을 줬는데 테두리가 안 보인다」는 문제를 풀 때 이 규칙을 떠올린다.

```text
입력                               무엇이 일어나나                       결과
.box {                            style = none(기본값)                  왼쪽 선이 없다
  border-left-width: 4px;   ──▶   style 이 none 이면 변의 실제     ──▶   (4px 도 차지하지 않는다)
  border-left-color: red;         두께는 0 으로 계산된다
}
```

- 기본값이 `none` 이므로 style 을 적지 않으면 「선 없음」이다.
- CSS 규칙상 style 이 `none` 이나 `hidden` 이면 그 변의 두께는 지정값과 상관없이 0 으로 계산된다.
- 그래서 width 와 color 는 style 이 있어야 의미가 생긴다.

> **계산값(computed value)** — 브라우저가 선언을 해석해 최종으로 정한 값이다.\
> 예: `border-left-width: 4px` 라도 style 이 `none` 이면 계산값은 `0` 이다.

### (3) 값마다 선 모양이 다르다

**언제 쓰나** — 강조 선의 느낌(단정한 실선 · 가벼운 점선 · 입체감)을 고를 때.

```text
값        모양(개념도)        뜻
none      (없음)             테두리 없음 — 기본값
hidden    (없음)             none 과 같지만 표 병합 때 우선순위가 높다
solid     ┃                 실선
dashed    ╏                 파선(짧은 선의 이어짐)
dotted    ⋮                 점선
double    ‖                 이중선
groove    ▒ 안으로 파임       안으로 파인 3D 효과
ridge     ▒ 밖으로 솟음       밖으로 돌출된 3D 효과
inset     ▒ 묻힘              요소가 묻힌 효과
outset    ▒ 튀어나옴          요소가 돌출된 효과
```

- `groove` · `ridge` · `inset` · `outset` 은 선의 밝은 쪽과 어두운 쪽을 나눠 입체처럼 보이게 하는 값이다.
- 「안으로 파였나 · 솟았나」는 선 하나에 대한 느낌이고, `inset` · `outset` 은 요소 전체가 묻히거나 솟은 느낌을 낸다.

> **3D 효과 테두리** — 색을 밝은 쪽과 어두운 쪽으로 나눠 그려 입체처럼 보이게 한 테두리다.\
> 예: `groove` 는 홈을 판 것처럼 보인다.

### (4) `hidden` 과 `none` — 표에서만 갈린다

**언제 쓰나** — `border-collapse: collapse` 로 이웃 칸의 테두리를 합친 표에서 특정 선을 확실히 지울 때.

```text
입력                                     무엇이 일어나나                        결과
table { border-collapse: collapse; }    두 칸이 한 선을 나눠 쓴다
td.a { border-left-style: hidden; } ──▶ 이웃 칸이 solid 를 줘도           ──▶  그 선은 없어진다
td.b { border-right-style: solid; }     hidden 이 우선순위가 높아 이긴다
```

- 보통의 요소에서는 `none` 과 `hidden` 이 똑같이 「선 없음」이다.
- 테두리가 병합된 표에서는 `hidden` 이 다른 스타일보다 우선한다.
- `none` 은 이웃 칸의 선에 진다.

> **테두리 병합(border-collapse)** — 표에서 이웃한 칸의 테두리를 한 선으로 합치는 방식이다.\
> 예: `table { border-collapse: collapse; }`

### (5) 모양은 「뚝」 바뀐다

**언제 쓰나** — hover 때 선 모양을 바꾸는 효과를 만들 때 기대치를 정한다.

```text
입력                                      무엇이 일어나나                     결과
.box { border-left-style: solid;          solid 와 dashed 사이에는           중간 모양 없이
       transition: all .5s; }      ──▶    「반쯤 점선」 같은 중간값이   ──▶   바로 바뀐다
.box:hover { border-left-style: dashed; } 없다(discrete 값)
```

- 선 모양은 숫자가 아니라 이름(키워드)이라 사이값을 만들 수 없다.
- 원본은 이 속성을 「애니메이션 가능: 아님」으로 적고, 팁에서 「discrete 값이라 부드러운 전환 불가」라고 한다.
- 부드럽게 보이게 하려면 숫자 속성(두께 · 색)을 전환해야 한다.

> **discrete 값** — 중간 단계 없이 한 값에서 다른 값으로 건너뛰는 값이다.\
> 예: `solid` → `dashed` 는 사이값이 없다.

## 문법 — 형태와 규칙

```html demo
<div class="note">왼쪽에만 점선</div>
<style>
  .note {
    border-left-style: dotted;   /* 선 모양 */
    border-left-width: 4px;      /* 선 두께 */
    border-left-color: #10b981;  /* 선 색 */
    padding: 12px;
  }
</style>
```

> **보이는 것** — 글자 상자의 왼쪽에만 초록 점선이 세로로 생긴다 (코드에서 읽은 것 — 렌더 실측 아님).

- 형태: `border-left-style: <line-style>`.
- 값은 한 개만 받는다.
- 기본값은 `none` 이다.
- 상속되지 않는다 — 부모에 줘도 자식 요소의 왼쪽 변에는 선이 생기지 않는다.
- 애니메이션 · 전환으로 부드럽게 바꿀 수 없다(discrete).

| 값 | 뜻 |
|---|---|
| `none` | 테두리 없음 (기본값) |
| `solid` | 실선 |
| `dashed` | 파선 |
| `dotted` | 점선 |
| `double` | 이중선 |
| `groove` | 안으로 파인 3D 효과 |
| `ridge` | 밖으로 돌출된 3D 효과 |
| `inset` | 요소가 묻힌 효과 |
| `outset` | 요소가 돌출된 효과 |
| `hidden` | `none` 과 같음, 표 병합 시 우선순위 높음 |

같은 일을 하는 다른 쓰기:

| 쓰기 | 건드리는 것 |
|---|---|
| `border-left-style: solid` | 왼쪽 변의 모양만 |
| `border-left: 4px solid #3b82f6` | 왼쪽 변의 두께 · 모양 · 색을 한 번에 (생략한 것은 초기값으로 되돌린다) |
| `border-style: solid` | 네 변 모두의 모양 |

> **단축 속성(shorthand)** — 여러 개별 속성을 한 줄로 정하는 속성이다.\
> 예: `border-left` 는 `border-left-width` · `border-left-style` · `border-left-color` 를 함께 정한다.

## 어디서 틀리나

### 1. 부드럽게 바꾸려 해도 안 된다

- 원본 팁: 「discrete 값이라 부드러운 전환 불가.」
- `transition` 을 걸어도 `solid` 에서 `dashed` 로 가는 중간 모습은 없다.
- 부드러운 효과가 필요하면 `border-left-color` 나 `border-left-width` 를 전환한다.
- 원본의 「애니메이션 가능: False」는 「보간(사이값 계산)이 안 된다」는 뜻으로 읽는다. 키프레임 애니메이션에서 값이 중간 시점에 한 번 바뀌는 식으로 다뤄질 수는 있다(확인 필요).

### 2. 두께 · 색만 주고 모양을 빠뜨린다

- 기본값이 `none` 이라 선이 생기지 않는다.
- 이때 두께도 0 으로 계산되므로 박스 폭도 늘지 않는다.

### 3. 단축 속성이 뒤에서 덮는다

- `border-left-style: dotted;` 다음에 `border-left: 4px solid red;` 를 쓰면 단축 속성이 style 을 `solid` 로 다시 정한다.
- 개별 속성을 살리려면 단축 속성 **뒤에** 쓴다.

### 4. 상속을 기대한다

- 상속되지 않으므로 부모 하나에 주고 자식들 모두에 선이 생기길 기대하면 안 된다.
- 자식마다 선이 필요하면 자식 선택자에 직접 준다.

### 5. `hidden` 을 `none` 과 다르게 기대한다

- 보통 요소에서는 둘의 결과가 같다.
- 차이는 병합된 표에서 이웃 테두리와 겨룰 때만 생긴다.

### 6. 박스 폭이 늘어난다

- 기본 `box-sizing: content-box` 에서 테두리 두께는 `width` 바깥에 더해진다.
- `width: 200px` 에 왼쪽 4px 선을 주면 박스의 바깥 폭은 204px 이 된다(padding 이 없을 때).
- 폭을 고정하고 싶으면 `box-sizing: border-box` 를 쓴다.

> **box-sizing** — `width` 가 내용만 재는지(content-box), 테두리 · padding 까지 재는지(border-box) 정하는 속성이다.\
> 예: `box-sizing: border-box` 면 테두리가 생겨도 바깥 폭은 `width` 그대로다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 기본값 `none` · 상속 안 됨 · 값 목록 | CSS 명세 |
| style 이 `none` · `hidden` 이면 두께 계산값이 0 | CSS 명세 |
| 병합된 표에서 `hidden` 이 우선 | CSS 명세(표 테두리 병합 규칙) |
| 사이값 없이 바뀐다(discrete) | CSS 명세 |
| `groove` · `ridge` · `inset` · `outset` 의 정확한 밝기 · 색 나눔 | 브라우저 구현에 맡겨진 부분이 있다(확인 필요) |
| `dashed` · `dotted` 의 점 · 선 간격 | 브라우저 구현(확인 필요) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 왼쪽 강조선의 모양만 바꾸기 | `border-left-style` | `border-style`(네 변이 다 바뀐다) |
| 왼쪽 선을 한 번에 다 정하기 | `border-left` 단축 | 세 개별 속성을 흩어 쓰기 |
| hover 때 부드러운 강조 | `border-left-color` · `border-left-width` 전환 | `border-left-style` 전환 |
| 병합 표에서 한 선을 확실히 지우기 | `hidden` | `none` |
| 폭이 늘면 안 되는 레이아웃 | `box-sizing: border-box` 와 함께 | content-box 그대로 |

## 핵심 문장

1. **`border-left-style` 은 왼쪽 변 하나의 선 모양만 정한다** — 기본값은 `none` 이다.
2. **모양이 `none` 이면 두께 · 색을 줘도 선은 없다** — 두께도 0 으로 계산된다.
3. **`hidden` 은 `none` 과 같지만 병합된 표에서 이긴다.**
4. **모양은 사이값이 없어 부드럽게 바뀌지 않는다** — 부드러운 효과는 두께나 색으로 낸다.
5. **상속되지 않고, 단축 속성 `border-left` 에 덮일 수 있다.**

## 관련 자료

- `border-style` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `border-left` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `border-left-width` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/css/box-model.json` 의 `border-left-style`

## 용어 풀이

- **테두리(border)** — padding 과 margin 사이를 두르는 선.
- **변(side)** — 테두리의 네 쪽 가운데 하나.
- **계산값(computed value)** — 브라우저가 최종으로 정한 속성값.
- **3D 효과 테두리** — 밝은 쪽과 어두운 쪽을 나눠 입체처럼 그린 테두리.
- **테두리 병합(border-collapse)** — 표에서 이웃 칸의 테두리를 한 선으로 합치는 방식.
- **discrete 값** — 사이값 없이 건너뛰는 값.
- **단축 속성(shorthand)** — 여러 개별 속성을 한 줄로 정하는 속성.
- **상속(inheritance)** — 부모의 속성값이 자식에게 그대로 넘어가는 것.
- **box-sizing** — `width` 가 어디까지 재는지 정하는 속성.

## 더 들어가면

- `double` 은 두 선과 그 사이 틈을 합쳐 두께를 채우므로, 두께가 아주 얇으면(예: 1~2px) 두 줄로 보이지 않을 수 있다(확인 필요).
- `groove` · `ridge` · `inset` · `outset` 은 `border-left-color` 를 바탕으로 밝은 색과 어두운 색을 만들어 쓴다. 검은색처럼 극단적인 색이면 입체감이 약해질 수 있다(확인 필요).
- 최근 명세에는 discrete 속성도 전환에 참여시키는 `transition-behavior: allow-discrete` 가 있다. 그래도 사이값이 생기는 것은 아니고, 바뀌는 시점만 정해진다(확인 필요).
- 쓰기 방향에 따라 바뀌는 논리 속성 `border-inline-start-style` 이 있다. 왼쪽에서 오른쪽으로 쓰는 문서에서는 왼쪽 변에 해당한다(확인 필요).
- 테두리를 박스 크기에 넣지 않고 선만 긋고 싶으면 `box-shadow` 의 안쪽 그림자나 `outline` 을 대신 쓰기도 한다(확인 필요).

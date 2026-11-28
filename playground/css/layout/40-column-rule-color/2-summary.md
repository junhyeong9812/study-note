# css/layout/40 — column-rule-color — 정리 (힌트)

> 출처 — study-site 항목 `css/column-rule-color`(항목 데이터 `data/css/layout.json`) · 정답 코드 study-practice `css/layout/reference/column-rule-color.html`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

## 한눈에 — 쉽게 말하면

**`column-rule-color` 는 「신문 지면의 세로 줄에 쓸 잉크 색」이다.**
신문은 한 면을 여러 단으로 나누고, 단 사이에 가는 세로 줄을 긋는다.
그 줄을 어떤 잉크로 그을지만 정하는 것이 이 속성이다.
줄의 굵기와 모양(실선 · 점선)은 다른 사람이 정한다.
따로 잉크를 고르지 않으면, 그 지면의 글자를 찍은 잉크를 그대로 쓴다.
CSS 다단 레이아웃도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 신문 한 면 | 다단 컨테이너(`column-count` 가 붙은 요소) |
| 단 | 열(column) |
| 단 사이 세로 줄 | 열 구분선(column rule) |
| 줄의 잉크 색 | `column-rule-color` |
| 줄의 굵기 · 모양 | `column-rule-width` · `column-rule-style` |
| 글자 잉크를 그대로 씀 | 기본값 `currentcolor` |

```text
┌──────────────────────────────────────┐
│  글자 글자  ┃  글자 글자  ┃  글자 글자  │
│  글자 글자  ┃  글자 글자  ┃  글자 글자  │
│  글자       ┃  글자       ┃            │
└──────────────────────────────────────┘
               ↑            ↑
         이 세로 줄의 「색」만 column-rule-color 가 정한다
```

## 이 주제가 답하려는 질문

1. 다단 레이아웃의 열 구분선 색은 어떻게 정하나?
2. 색을 따로 정하지 않으면 구분선은 무슨 색이 되나?
3. 이 속성은 상속되나, 애니메이션되나?
4. 색 하나만 정하면 구분선이 완성되나, 다른 무엇이 더 필요한가?

## 동작 방식

### (1) 색을 직접 정하기

**언제 쓰나** — 구분선을 글자색과 다른 색으로 눈에 띄게(또는 은은하게) 하고 싶을 때 쓴다.

```text
입력 코드                          무엇이 일어나나                     결과
.multicol {                      3개 열로 나눈다                     열 3개
  column-count: 3;          ──▶  열 사이 구분선의 색을 빨강으로   ──▶  빨간 세로선 2개
  column-rule-color: #ef4444;    선 모양은 실선, 두께는 2px           (열 사이에만)
  column-rule-style: solid;
  column-rule-width: 2px;
}
```

1. `column-count: 3` 이 내용을 세 열로 흘려 나눈다.
2. 열이 셋이면 열 사이는 둘이므로, 구분선도 두 줄이 생길 자리가 있다.
3. `column-rule-color` 가 그 두 줄의 색을 `#ef4444`(빨강)로 정한다.
4. `column-rule-style` 과 `column-rule-width` 가 선의 모양과 두께를 정한다.
5. 세 속성은 각자 한 가지만 맡는다 — 색 속성은 모양이나 두께를 바꾸지 않는다.

### (2) 색을 정하지 않으면 — 기본값 `currentcolor`

**언제 쓰나** — 글자색과 구분선 색을 늘 맞춰 두고 싶을 때, 일부러 색을 비워 둔다.

```text
입력 코드                          무엇이 일어나나                       결과
.multicol {                      column-rule-color 가 없다           구분선이 파란색
  color: blue;              ──▶  → 기본값 currentcolor           ──▶ (글자색과 같음)
  column-rule-style: solid;      → 이 요소의 color 값(blue)을 쓴다
}
```

1. `column-rule-color` 를 쓰지 않았으니 기본값 `currentcolor` 가 들어간다.
2. `currentcolor` 는 「이 요소의 `color` 값」을 가리키는 키워드다.
3. 이 요소의 `color` 가 `blue` 이므로 구분선은 파란색이 된다.
4. 나중에 `color` 만 바꿔도 구분선 색이 함께 바뀐다.

> **currentcolor** — 그 요소의 `color` 속성 값을 그대로 가리키는 CSS 색 키워드.\
> 예: `color: green` 인 요소에서 `currentcolor` 는 초록이다.

### (3) 상속되지 않는다 — 그런데 왜 부모 색을 따라가는 것처럼 보이나

**언제 쓰나** — 부모에 준 구분선 색이 자식 다단 컨테이너에 퍼질지 판단할 때 떠올린다.

```text
입력 코드                              무엇이 일어나나                          결과
.outer { color: green;            .inner 의 column-rule-color 는         .inner 의 구분선:
         column-rule-color: red; } ──▶ 상속 안 됨 → 기본값 currentcolor ──▶  초록
.inner { column-count: 2;             .inner 의 color 는 상속됨(green)       (빨강 아님)
         column-rule-style: solid; }
```

1. 원본 데이터에 「상속: `False`」로 적혀 있다 — `.outer` 의 `red` 는 `.inner` 로 넘어가지 않는다.
2. 그래서 `.inner` 의 `column-rule-color` 는 기본값 `currentcolor` 다.
3. `color` 는 상속되는 속성이라 `.inner` 의 `color` 는 `.outer` 에서 받은 `green` 이다.
4. 결국 `.inner` 의 구분선은 `currentcolor` → `green` 이 된다.
5. 「부모를 따라간 것」처럼 보이지만, 실제로 따라간 것은 `color` 이고 구분선 색은 자기 `color` 를 참조했을 뿐이다.

> **상속** — 부모 요소에 준 속성 값이 자식 요소에 자동으로 넘어가는 것.\
> 예: `color` 는 상속되어 부모에 준 글자색이 자식 글자에도 적용된다.

### (4) 애니메이션 가능

**언제 쓰나** — 마우스를 올렸을 때 구분선 색을 부드럽게 바꾸고 싶을 때 쓴다.

```text
입력 코드                                   무엇이 일어나나               결과
.multicol { column-rule-color: gray;     색 값 사이를 중간값으로   ──▶ 회색 → 빨강으로
            transition: column-rule-color   이어 그린다                   서서히 바뀐다
                        0.3s; }
.multicol:hover { column-rule-color: red; }
```

1. 원본 데이터에 「애니메이션 가능: `True`」로 적혀 있다.
2. 그래서 `transition` 에 이 속성을 지정하면 두 색 사이를 단계적으로 이어 바꾼다.
3. 뚝 끊겨 바뀌지 않고, 지정한 시간 동안 섞인 색들을 거친다.

## 문법 — 형태와 규칙

```html demo
<div class="cols">
  <p>첫 문단의 글이 세 열로 흘러 들어간다. 열 사이에는 구분선이 그어진다. 구분선의 색만 바꿔 본다.</p>
</div>
<style>
  .cols {
    column-count: 3;
    column-gap: 24px;
    column-rule-style: dashed;
    column-rule-width: 1px;
    column-rule-color: hsl(220 70% 50%);
  }
  p { margin: 0; }
</style>
```

> **보이는 것** — 글이 세 열로 나뉘고, 열 사이에 파란 계열의 1px 점선(dashed) 두 줄이 보인다. (코드에서 읽은 것 — 렌더 실측 아님)

- 꼴은 `column-rule-color: <color>` 하나다.
- `<color>` 자리에는 색을 나타내는 값이면 무엇이든 온다 — 키워드 · hex · `rgb()` · `hsl()` 등.
- 기본값은 `currentcolor` 다.
- 상속되지 않는다.
- 애니메이션(전환)할 수 있다.
- 색만 정한다 — 선의 모양은 `column-rule-style`, 두께는 `column-rule-width` 가 맡는다.
- 열이 있어야 구분선이 생길 자리가 있다 — `column-count` 같은 다단 설정과 함께 쓴다.

| 값 | 뜻 | 예 |
|---|---|---|
| `<color>` | 구분선의 색 (키워드, hex, rgb, hsl 등) | `red` · `#ef4444` · `rgb(239 68 68)` · `hsl(0 84% 60%)` |
| `currentcolor` (기본값) | 이 요소의 `color` 값과 같은 색 | `color: navy` 면 구분선도 남색 |

> **다단 레이아웃** — 한 요소의 내용을 신문처럼 여러 세로 열로 나눠 흘리는 CSS 배치 방식.\
> 예: `column-count: 3` 을 주면 글이 세 열로 나뉜다.

> **열 구분선(column rule)** — 다단 레이아웃에서 이웃한 두 열 사이에 그어지는 세로 선.\
> 예: 열이 3개면 열 사이는 2곳이라 구분선도 2줄이다.

## 어디서 틀리나

### 1. 「색을 줬는데 선이 안 보인다」

`column-rule-color` 는 색만 정한다.
선의 모양(`column-rule-style`)과 두께(`column-rule-width`)는 다른 속성이다.
원본 예제가 색 · 스타일 · 두께 세 속성을 함께 쓰는 것도 그 때문이다.
선이 안 보이면 색보다 먼저 스타일과 두께가 정해져 있는지 본다.

### 2. 팁의 「상속받습니다」라는 말

원본 팁: 「기본값은 `currentcolor` 로, 요소의 `color` 속성값을 상속받습니다.」
원본의 주장 → 기본값이 `currentcolor` 이고 그 결과 `color` 값을 따른다는 내용은 맞다.
왜 의심스러운가 → 같은 원본 데이터에 「상속: `False`」로 적혀 있다.
「상속받는다」는 표현은 부모에게서 값을 넘겨받는다는 뜻으로 읽히기 쉽다.
실제로는 **자기 자신의** `color` 값을 참조하는 것이다.
자기 `color` 가 부모에게서 상속된 값일 수는 있지만, 그것은 `color` 의 상속이지 `column-rule-color` 의 상속이 아니다.
그래서 부모에 `column-rule-color: red` 를 줘도 자식 다단 요소의 구분선은 빨강이 되지 않는다(「동작 방식 (3)」).

### 3. `color` 를 바꿨더니 구분선 색도 바뀌었다

구분선 색을 따로 주지 않았다면 정상이다.
기본값 `currentcolor` 가 `color` 를 따라가기 때문이다.
글자색만 바꾸고 구분선은 그대로 두고 싶으면 `column-rule-color` 를 명시한다.

### 4. 열이 하나뿐인데 구분선 색을 준다

구분선은 이웃한 두 열 **사이**에 생긴다.
열이 나뉘지 않은 요소에는 구분선이 들어갈 자리가 없다.
`column-count` 같은 다단 설정이 먼저다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 기본값이 `currentcolor` 다 | CSS 명세의 속성 정의 (원본 데이터와 일치) |
| 상속되지 않는다 | CSS 명세의 속성 정의 (원본 데이터와 일치) |
| 애니메이션할 수 있다 | CSS 명세의 속성 정의 (원본 데이터와 일치) |
| 전환 중 중간 색이 정확히 어떻게 섞이나 | 명세의 색 보간 규칙 · 브라우저 구현 (확인 필요) |
| 화면에서 선이 정확히 몇 픽셀 어디에 그려지나 | 브라우저 렌더링 (렌더 실측 아님) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 구분선을 글자와 다른 색으로 강조 | `column-rule-color` 에 색 명시 | 글자색 `color` 를 바꾸는 것 |
| 글자색과 구분선을 늘 같게 | 기본값 `currentcolor` 를 그대로 둠 | 같은 값을 두 번 하드코딩 |
| 선의 굵기 · 모양 바꾸기 | `column-rule-width` · `column-rule-style` | `column-rule-color` |
| 마우스를 올리면 선 색이 부드럽게 변하기 | `transition` + `column-rule-color` | 색 대신 선을 지웠다 그렸다 하기 |
| 다단이 아닌 일반 박스의 테두리 색 | 테두리 관련 속성 | `column-rule-color` |

## 핵심 문장

1. **`column-rule-color` 는 다단 레이아웃의 열 구분선 색만 정한다** — 모양 · 두께는 다른 속성이 맡는다.
2. **기본값은 `currentcolor` 라서, 비워 두면 그 요소의 글자색을 따른다.**
3. **상속되지 않는다** — 부모 색을 따라가 보이는 것은 `color` 가 상속된 결과다.
4. **애니메이션할 수 있어서** `transition` 으로 색을 부드럽게 바꿀 수 있다.
5. **구분선은 열 사이에 생기므로** 먼저 열을 나눠야 색도 의미가 있다.

## 관련 자료

- [column-rule](../37-column-rule/2-summary.md)
- [column-rule-width](../38-column-rule-width/2-summary.md)
- [column-rule-style](../39-column-rule-style/2-summary.md)
- 원본: study-site 항목 데이터 `data/css/layout.json` 의 `column-rule-color`

## 용어 풀이

- **다단 레이아웃** — 내용을 신문처럼 여러 세로 열로 나눠 흘리는 배치 방식.
- **열(column)** — 다단 레이아웃에서 나뉜 세로 칸 하나.
- **열 구분선(column rule)** — 이웃한 두 열 사이의 세로 선.
- **`column-count`** — 내용을 몇 개의 열로 나눌지 정하는 속성.
- **`column-gap`** — 열과 열 사이의 간격을 정하는 속성.
- **`column-rule-style`** — 구분선의 모양(실선 · 점선 등)을 정하는 속성.
- **`column-rule-width`** — 구분선의 두께를 정하는 속성.
- **`currentcolor`** — 그 요소의 `color` 값을 가리키는 색 키워드.
- **상속** — 부모에 준 속성 값이 자식에 자동으로 넘어가는 것.
- **애니메이션 가능** — 두 값 사이를 `transition` · `animation` 으로 중간값을 거쳐 바꿀 수 있는 성질.
- **`<color>`** — CSS 에서 색을 나타내는 값의 종류(키워드 · hex · `rgb()` · `hsl()` 등).

## 더 들어가면

- `column-rule-style` 의 기본값은 `none` 이라서, 스타일을 주지 않으면 색과 두께가 있어도 선이 그려지지 않는다 (확인 필요).
- 구분선은 열 간격(`column-gap`) 한가운데에 그려지고, 선 자체는 레이아웃 공간을 차지하지 않는다 — 선이 간격보다 두꺼우면 열 내용과 겹칠 수 있다 (확인 필요).
- 색 · 스타일 · 두께를 한 줄로 쓰는 단축 속성 `column-rule` 이 있다 — 예: `column-rule: 2px solid #ef4444` (확인 필요).
- 테두리 색(`border-color`)도 기본값이 `currentcolor` 라서, 비워 두면 글자색을 따르는 점이 닮았다 (확인 필요).
- 반투명 색(`rgb(0 0 0 / 0.2)` 처럼 알파가 있는 값)으로 구분선을 은은하게 만드는 방식도 흔히 쓴다 (확인 필요).

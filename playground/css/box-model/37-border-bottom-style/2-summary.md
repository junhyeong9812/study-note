# css/box-model/37 — border-bottom-style — 정리 (힌트)

> 출처 — study-site 항목 `css/border-bottom-style`(항목 데이터 `data/css/box-model.json`) · 정답 코드 study-practice `css/box-model/reference/border-bottom-style.html`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

## 한눈에 — 쉽게 말하면

**`border-bottom-style` 은 「공책 줄의 모양을 고르는 도장」이다.**
공책 한 줄 아래에 밑줄을 긋는다고 하자.
밑줄을 실선으로 그을지, 점선으로 그을지, 아예 긋지 않을지를 먼저 골라야 한다.
펜 굵기와 잉크 색은 따로 정하지만, 모양을 「긋지 않음」으로 두면 굵기와 색을 아무리 정해도 줄은 안 생긴다.
CSS 상자의 아래쪽 테두리도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 밑줄의 모양(실선 · 점선 · 안 그음) | `border-bottom-style` 값 |
| 펜 굵기 | `border-bottom-width` |
| 잉크 색 | `border-bottom-color` |
| 밑줄을 긋지 않은 상태 | 기본값 `none` |

```text
┌──────────────────────┐
│  border-bottom-style │   ← 위 · 왼 · 오른쪽은 건드리지 않는다
└──────────────────────┘
━━━━━━━━━━━━━━━━━━━━━━━━   ← 아래쪽 한 변의 「모양」만 이 속성이 정한다
```

## 이 주제가 답하려는 질문

1. 요소의 아래쪽 테두리 한 변만 어떤 모양으로 그릴 수 있나?
2. 아무것도 정하지 않으면 아래쪽 테두리는 어떻게 되나?
3. 모양을 바꾸는 것을 애니메이션으로 부드럽게 넘길 수 있나?
4. `none` 과 `hidden` 은 무엇이 다른가?

## 동작 방식

### (1) 아래쪽 한 변의 모양을 고른다

**언제 쓰나** — 제목 밑줄이나 목록 구분선처럼 아래쪽에만 선을 두고 싶을 때 쓴다.

```text
입력 코드                              무엇이 일어나나                       결과
.box {                                 아래쪽 변의 모양 = 실선               아래쪽에만 3px 파란 실선
  border-bottom-style: solid;   ──▶    아래쪽 변의 굵기 = 3px         ──▶    위 · 왼 · 오른쪽은 선 없음
  border-bottom-width: 3px;            아래쪽 변의 색 = #3b82f6
  border-bottom-color: #3b82f6;
}
```

- 첫째, `border-bottom-style: solid` 가 아래쪽 변을 「그린다, 실선으로」로 정한다.
- 둘째, `border-bottom-width` 와 `border-bottom-color` 가 그 선의 굵기와 색을 정한다.
- 셋째, 이 셋은 모두 이름에 `bottom` 이 들어간 속성이라 다른 세 변에는 손대지 않는다.

> **테두리(border)** — 요소의 안쪽 여백(padding) 바깥을 두르는 선이다.\
> 예: `.box` 의 회색 배경 바로 아래에 그어진 파란 선.

```html demo
<div class="box">border-bottom-style</div>
<style>
  .box { border-bottom-style: solid; border-bottom-width: 3px; border-bottom-color: #3b82f6; padding: 16px; background: #f8fafc; }
</style>
```

> **보이는 것** — 옅은 회색 상자 아래쪽에만 파란 실선이 있고 나머지 세 변에는 선이 없다 (코드에서 읽은 것 — 렌더 실측 아님)

### (2) 기본값 `none` — 정하지 않으면 선이 없다

**언제 쓰나** — 굵기와 색을 줬는데 선이 안 보일 때 원인을 찾는 데 쓴다.

```text
입력 코드                              무엇이 일어나나                       결과
.box {                                 style 을 안 씀 → 기본값 none          아래쪽 선이 없다
  border-bottom-width: 3px;     ──▶    none = 「테두리 없음」          ──▶    굵기 · 색은 쓰이지 않는다
  border-bottom-color: #3b82f6;
}
```

- 첫째, `border-bottom-style` 의 기본값은 `none` 이다.
- 둘째, `none` 은 「테두리 없음」이라 선을 그리지 않는다.
- 셋째, 그래서 굵기와 색만 정한 상자에는 아래쪽 선이 나타나지 않는다.

### (3) 값이 「뚝뚝」 바뀐다 — discrete

**언제 쓰나** — `:hover` 에 `transition` 을 걸어 선 모양을 바꿀 때 기대치를 맞추는 데 쓴다.

```text
입력 코드                              무엇이 일어나나                       결과
.box { border-bottom-style: dashed;    dashed 와 solid 사이에는              중간 모양 없이
       transition: all 1s; }    ──▶    「중간 값」이 없다              ──▶    어느 순간 한 번에 바뀐다
.box:hover { border-bottom-style: solid; }
```

- 첫째, 이 속성의 값은 `solid` · `dashed` 같은 이름(키워드)이다.
- 둘째, 숫자처럼 「절반쯤 실선」을 계산할 수 없어서 애니메이션 가능 여부가 `False` 다.
- 셋째, 그래서 `transition` 을 걸어도 부드럽게 변하지 않고 단번에 바뀐다.

> **discrete(이산) 값** — 중간 단계가 없어 한 값에서 다른 값으로 건너뛰기만 하는 값이다.\
> 예: `dashed` 와 `solid` 사이에는 「반쯤 파선」이 없다.

### (4) 상속되지 않는다

**언제 쓰나** — 부모에 준 테두리가 자식에게도 생길지 판단할 때 쓴다.

```text
입력 코드                              무엇이 일어나나                       결과
.parent { border-bottom-style: solid; }  상속 False                         부모 아래에만 선
<div class="parent">            ──▶    자식은 기본값 none 그대로     ──▶    자식에는 선 없음
  <div>자식</div>
</div>
```

- 첫째, 상속이 `False` 라서 자식은 부모의 값을 물려받지 않는다.
- 둘째, 자식은 자기 기본값 `none` 을 쓴다.

> **상속(inheritance)** — 부모 요소에 준 값이 자식 요소에도 저절로 적용되는 것이다.\
> 예: `color` 는 상속되지만 `border-bottom-style` 은 상속되지 않는다.

## 문법 — 형태와 규칙

```css
/* 최소 예제 — 직접 쓴 것 */
h2 {
  border-bottom-style: dashed;  /* 아래쪽 변만 파선 */
  border-bottom-width: 2px;
  border-bottom-color: gray;
}
td.cut {
  border-bottom-style: hidden;  /* 표에서 테두리 충돌 시 우선 */
}
```

- 형태는 `border-bottom-style: <line-style>` 이다.
- `<line-style>` 자리에는 아래 표의 키워드 하나를 쓴다.
- 기본값은 `none`, 상속은 안 되고, 애니메이션으로 부드럽게 바뀌지 않는다.

| 값 | 뜻 | 덧붙임 |
|---|---|---|
| `none` | 테두리 없음 | 기본값 |
| `solid` | 실선 | 가장 흔한 밑줄 |
| `dashed` | 파선 | 짧은 선분이 이어진다 |
| `dotted` | 점선 | 점이 이어진다 |
| `double` | 이중선 | 선이 두 줄 |
| `groove` | 안으로 파인 3D 효과 | `ridge` 와 반대 |
| `ridge` | 밖으로 돌출된 3D 효과 | `groove` 와 반대 |
| `inset` | 요소가 묻힌 효과 | `outset` 과 반대 |
| `outset` | 요소가 돌출된 효과 | `inset` 과 반대 |
| `hidden` | `none` 과 동일 | 테이블 테두리 병합 시 우선순위가 높다 |

> **키워드 값** — 숫자가 아니라 이름으로 정해진 값이다.\
> 예: `solid` · `dotted`.

## 어디서 틀리나

### 1. 굵기와 색만 주고 선이 안 보인다

기본값이 `none` 이라 스타일을 정하지 않으면 선이 그려지지 않는다.
선을 보이게 하려면 `border-bottom-style` 에 `none` · `hidden` 이 아닌 값을 꼭 준다.

### 2. `transition` 으로 선 모양이 부드럽게 바뀌길 기대한다

원본 팁: discrete 값이라 부드러운 전환이 불가능하다.
`dashed` 에서 `solid` 로 가는 중간 모양은 없고 한 번에 바뀐다.
부드럽게 보이고 싶다면 숫자 값인 다른 속성(색 · 굵기 등)을 함께 바꾸는 방법을 생각한다.

### 3. `hidden` 을 `none` 과 완전히 같다고 본다

일반 요소에서는 둘 다 「선 없음」이다.
다만 표의 이웃 칸끼리 테두리를 합칠 때(테이블 병합) `hidden` 은 우선순위가 높아 이웃 칸의 선까지 감춘다.
`none` 은 그런 힘이 없다.

> **테이블 테두리 병합** — 표의 이웃 칸이 맞닿은 테두리를 한 줄로 합쳐 그리는 방식이다.\
> 예: 두 칸이 맞닿은 선을 두 겹이 아니라 한 겹으로 그린다.

### 4. 부모에 주면 자식에도 생긴다고 생각한다

상속이 `False` 다.
자식에 선이 필요하면 자식에게 따로 준다.

### 5. 다른 변까지 바뀐다고 생각한다

이름에 `bottom` 이 있는 속성은 아래쪽 한 변만 바꾼다.
위 · 왼 · 오른쪽은 각자 기본값(`none`)이나 따로 준 값을 그대로 쓴다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 기본값 `none`, 상속 안 됨, discrete | CSS 명세가 정한 속성 정의 (원본 재료 기준) |
| `none` · `solid` 등 10개 키워드의 뜻 | CSS 명세가 정한 키워드 (원본 재료 기준) |
| `groove` · `ridge` · `inset` · `outset` 의 정확한 명암 색 | 명세는 효과의 성격만 정하고 실제 명암 계산은 브라우저가 정한다 (확인 필요) |
| `dashed` · `dotted` 의 선분 · 점 간격 | 브라우저 렌더링 방식에 달렸다 (확인 필요) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 제목 아래에만 구분선 | `border-bottom-style: solid` + 굵기 · 색 | 네 변 모두 바꾸는 속성 |
| 아래 선을 점선 · 파선으로 | `dashed` · `dotted` | 이미지로 선 그리기 |
| hover 시 선 모양을 부드럽게 바꾸기 | 색 · 굵기처럼 숫자로 변하는 속성 | `border-bottom-style` 의 transition |
| 표에서 특정 칸 아래 선을 확실히 감추기 | `hidden` | `none`(이웃 칸 선이 남을 수 있다) |
| 자식에게도 같은 밑줄 | 자식에게 따로 지정 | 부모에만 주고 상속 기대 |

## 핵심 문장

1. **`border-bottom-style` 은 아래쪽 한 변의 「모양」만 정한다** — 다른 세 변은 건드리지 않는다.
2. **기본값이 `none` 이라 스타일 없이는 선이 없다** — 굵기 · 색만으로는 안 보인다.
3. **값은 이름이라 discrete 다** — transition 으로 부드럽게 바뀌지 않는다.
4. **`hidden` 은 `none` 과 같지만 표 테두리 병합에서 이긴다.**
5. **상속되지 않는다** — 자식은 자기 값을 따로 받는다.

## 관련 자료

- `border-style` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `border-bottom` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [border-bottom-width](../33-border-bottom-width/2-summary.md)
- 원본: study-site 항목 데이터 `data/css/box-model.json` 의 `border-bottom-style`
## 용어 풀이

- **테두리(border)** — 요소의 padding 바깥을 두르는 선.
- **line-style** — 테두리 모양 키워드(`solid` · `dashed` 등)의 묶음 이름.
- **기본값** — 아무것도 지정하지 않았을 때 속성이 갖는 값.
- **상속** — 부모의 값이 자식에게 저절로 적용되는 것.
- **discrete(이산) 값** — 중간 단계 없이 건너뛰기만 하는 값.
- **transition** — 속성 값이 바뀔 때 시간을 두고 넘어가게 하는 CSS 기능.
- **테이블 테두리 병합** — 표의 이웃 칸 테두리를 한 줄로 합쳐 그리는 방식.
- **키워드 값** — 숫자 대신 이름으로 정해진 값.

## 더 들어가면

- 스타일이 `none` 이나 `hidden` 이면 `border-bottom-width` 의 계산된 값이 0 이 되어 상자 높이에도 선 두께가 더해지지 않는다고 알려져 있다 (확인 필요).
- discrete 속성에 transition 을 걸면 진행 중간쯤에서 값이 바뀐다고 알려져 있으나, 브라우저와 `transition-behavior` 설정에 따라 다를 수 있다 (확인 필요).
- `double` 은 선 두 줄과 사이 틈이 들어갈 만큼 굵어야(대략 3px 이상) 이중선으로 보인다 (확인 필요).
- `border-bottom: 3px solid #3b82f6;` 처럼 단축 속성 `border-bottom` 으로 굵기 · 모양 · 색을 한 번에 쓸 수 있다 (확인 필요).
- `groove` · `ridge` · `inset` · `outset` 의 명암은 `border-bottom-color` 를 바탕으로 밝고 어둡게 계산된다 (확인 필요).

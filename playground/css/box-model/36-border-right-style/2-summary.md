# css/box-model/36 — border-right-style — 정리 (힌트)

> 출처 — study-site 항목 `css/border-right-style`(항목 데이터 `data/css/box-model.json`) · 정답 코드 study-practice `css/box-model/reference/border-right-style.html`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

## 한눈에 — 쉽게 말하면

**`border-right-style` 은 「액자의 오른쪽 틀에 어떤 무늬의 선을 두를지」를 정하는 속성이다.**
액자 틀은 네 변으로 나뉘어 있고, 오른쪽 변의 무늬만 따로 고를 수 있다.
실선으로 할지, 점선으로 할지, 틀을 아예 두르지 않을지를 고른다.
무늬를 고르지 않으면 두께와 색을 아무리 정해 두어도 틀은 생기지 않는다.
CSS 의 박스 테두리도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 액자 | 요소의 박스 |
| 오른쪽 틀 | 오른쪽 테두리(border-right) |
| 틀의 무늬 | `border-right-style` 의 값 |
| 틀의 두께 | `border-right-width` |
| 틀의 색 | `border-right-color` |
| 틀을 두르지 않음 | `none` (기본값) |

```text
 ┌──────────────────┐ ┊
 │                  │ ┊  ← 오른쪽 변만 dotted
 │  내용 + padding   │ ┊
 │                  │ ┊
 └──────────────────┘ ┊
   위·아래·왼쪽: none (선 없음)
```

## 이 주제가 답하려는 질문

1. 오른쪽 테두리 하나만 무늬를 바꾸려면 무엇을 쓰나?
2. 두께와 색을 정했는데 테두리가 안 보이는 것은 왜인가?
3. 고를 수 있는 무늬는 무엇이고, `none` 과 `hidden` 은 어떻게 다른가?
4. 이 속성은 자식에게 물려지나, 그리고 부드럽게 바뀌나?

## 동작 방식

### (1) 테두리는 세 박자로 그려진다 — 무늬 · 두께 · 색

**언제 쓰나** — 오른쪽 변에 선을 긋고 싶을 때 가장 먼저 정해야 하는 값이 무늬다.

```text
입력 코드                                  무엇이 일어나나                    결과
border-right-style: dotted;   ─┐
border-right-width: 3px;       ├──▶ 무늬가 none 이 아니므로        ──▶ 오른쪽에 3px 파란 점선
border-right-color: #3b82f6;  ─┘    두께·색이 실제로 쓰인다

border-right-width: 3px;      ─┐
border-right-color: #3b82f6;   ├──▶ 무늬가 기본값 none 그대로     ──▶ 오른쪽 선이 없다
(style 을 안 씀)              ─┘    → 두께가 0 으로 계산된다
```

- 테두리 한 변은 무늬(`style`) · 두께(`width`) · 색(`color`) 세 값으로 이루어진다.
- 무늬의 기본값은 `none` 이다.
- 무늬가 `none` 이면 그 변의 두께는 0 으로 계산되어, 두께와 색을 정해도 선이 그려지지 않는다.
- 그래서 세 박자 가운데 무늬가 「켜는 스위치」 노릇을 한다.
- 무늬만 정하고 두께와 색을 안 쓰면, 두께는 기본값 `medium`, 색은 기본값 `currentcolor`(글자색)로 그려진다.

> **기본값(initial value)** — 아무 선언이 없을 때 속성이 갖는 값.\
> 예: `border-right-style` 의 기본값은 `none` 이다.

> **`currentcolor`** — 그 요소의 `color`(글자색)를 그대로 가져다 쓰라는 키워드.\
> 예: 글자색이 검정이면 테두리도 검정이 된다.

### (2) 무늬는 열 가지 가운데 하나다

**언제 쓰나** — 구분선 · 강조선 · 입체 느낌 단추처럼 선의 모양이 의미를 가질 때 고른다.

```text
입력 값          무엇이 일어나나                결과
none     ──▶ 선을 그리지 않는다            ──▶ 테두리 없음
solid    ──▶ 끊김 없는 한 줄               ──▶ 실선
dashed   ──▶ 짧은 선분을 이어 붙인다        ──▶ 파선
dotted   ──▶ 점을 이어 붙인다              ──▶ 점선
double   ──▶ 선을 두 줄로 나눈다           ──▶ 이중선
groove   ──▶ 색을 밝고 어둡게 나눠 칠한다   ──▶ 안으로 파인 홈
ridge    ──▶ groove 의 반대 음영          ──▶ 밖으로 솟은 둑
inset    ──▶ 박스가 묻힌 듯 칠한다          ──▶ 요소가 들어간 느낌
outset   ──▶ 박스가 솟은 듯 칠한다          ──▶ 요소가 튀어나온 느낌
hidden   ──▶ none 처럼 그리지 않는다        ──▶ 테두리 없음(표 병합 때 우선)
```

- `groove` · `ridge` · `inset` · `outset` 은 3D 처럼 보이게 하는 무늬다.
- 이 네 가지는 테두리 색을 밝은 쪽과 어두운 쪽으로 나눠 음영을 만든다.
- `hidden` 은 화면에서는 `none` 과 같다.
- 차이는 표에서 이웃 칸의 테두리를 하나로 합칠 때(`border-collapse: collapse`) 드러난다 — 합쳐지는 테두리 가운데 `hidden` 이 우선순위가 높아, 그 자리의 테두리를 없앤다.

> **테두리 병합(border-collapse)** — 표에서 이웃한 칸의 테두리를 한 줄로 합치는 방식.\
> 예: `table { border-collapse: collapse; }` 이면 두 칸 사이에 선이 하나만 남는다.

### (3) 같은 자리를 건드리는 다른 속성과 겹칠 때

**언제 쓰나** — 단축 속성과 섞어 쓰거나, 네 변을 한꺼번에 정한 뒤 오른쪽만 바꿀 때.

```text
입력 코드                                    무엇이 일어나나                            결과
border-style: solid dashed dotted double; ──▶ 값 넷은 위·오른쪽·아래·왼쪽 차례     ──▶ 오른쪽 = dashed
border-right: 3px dotted #3b82f6;         ──▶ 두께·무늬·색을 한 줄에 넣은 단축 속성 ──▶ 오른쪽 = 3px 파란 점선
border-style: solid;                      ──▶ 네 변 모두 solid                    ──┐
border-right-style: dashed;               ──▶ 뒤에 나온 선언이 오른쪽만 덮어쓴다   ──┴▶ 오른쪽만 dashed
```

- `border-style` 에 값을 넷 주면 시계 방향(위 → 오른쪽 → 아래 → 왼쪽)으로 들어간다. 두 번째 값이 오른쪽이다.
- `border-right` 는 오른쪽 변의 두께 · 무늬 · 색을 한 번에 정하는 단축 속성이다.
- 같은 선택자 안에서는 나중에 쓴 선언이 이긴다. 단축 속성을 뒤에 쓰면 앞의 `border-right-style` 이 덮인다.

> **단축 속성(shorthand)** — 여러 개별 속성을 한 줄에 묶어 정하는 속성.\
> 예: `border-right` 는 `border-right-width` · `border-right-style` · `border-right-color` 를 묶는다.

### (4) 물려주지 않고, 부드럽게 바뀌지 않는다

**언제 쓰나** — 부모 · 자식에 테두리를 나눠 줄 때나 hover 효과를 만들 때 이 두 성질을 떠올린다.

```text
입력 코드                                무엇이 일어나나                       결과
.parent { border-right-style: solid; } ──▶ 상속되지 않는 속성              ──▶ 자식은 기본값 none
.child  { }                                                                  (자식에 선 없음)

.box       { border-right-style: solid; transition: all 1s; }
.box:hover { border-right-style: dashed; }
                                       ──▶ 값 사이에 중간 단계가 없다      ──▶ 한 번에 바뀐다
                                           (discrete)                         (서서히 바뀌지 않음)
```

- 상속되지 않으므로, 부모에 준 오른쪽 테두리는 자식에게 옮아가지 않는다.
- 무늬 값은 「실선의 40% 쯤 된 점선」 같은 중간값이 없다.
- 그래서 애니메이션 가능 여부가 「불가」이고, 전환을 걸어도 부드럽게 바뀌지 않는다.

> **상속(inheritance)** — 부모에 준 값이 자식에게 저절로 옮아가는 성질.\
> 예: `color` 는 상속되지만 `border-right-style` 은 상속되지 않는다.

> **discrete** — 값 사이에 중간 단계가 없어 이어서 보간할 수 없는 값.\
> 예: `solid` 와 `dashed` 사이의 「반쯤 dashed」는 없다.

## 문법 — 형태와 규칙

```text
border-right-style: <line-style>
<line-style> = none | hidden | dotted | dashed | solid | double | groove | ridge | inset | outset
```

```html demo
<div class="box">오른쪽만 점선</div>
<style>
  .box {
    padding: 16px;
    background: #f8fafc;
    border-right-style: dotted;
    border-right-width: 3px;
    border-right-color: #3b82f6;
  }
</style>
```

> **보이는 것** — 옅은 회색 박스의 오른쪽 변에만 파란 점선이 서 있고, 나머지 세 변에는 선이 없다 (코드에서 읽은 것 — 렌더 실측 아님)

| 값 | 뜻 | 비고 |
|---|---|---|
| `none` | 테두리 없음 | 기본값. 두께가 0 으로 계산된다 |
| `solid` | 실선 | 가장 흔한 구분선 |
| `dashed` | 파선 | 짧은 선분의 줄 |
| `dotted` | 점선 | 점의 줄 |
| `double` | 이중선 | 두 줄이 보이려면 두께가 넉넉해야 한다 |
| `groove` | 안으로 파인 3D 효과 | 색을 밝게·어둡게 나눠 칠한다 |
| `ridge` | 밖으로 돌출된 3D 효과 | `groove` 의 반대 |
| `inset` | 요소가 묻힌 효과 | 박스 전체가 들어간 느낌 |
| `outset` | 요소가 돌출된 효과 | 박스 전체가 솟은 느낌 |
| `hidden` | `none` 과 동일 | 표 테두리 병합 때 우선순위가 높다 |

- 기본값: `none`.
- 상속: 안 된다.
- 애니메이션: 안 된다(discrete).
- 값은 하나만 받는다. 네 변을 한꺼번에 정하려면 `border-style` 을 쓴다.

## 어디서 틀리나

### 1. 두께와 색만 주고 무늬를 빠뜨린다

`border-right-width: 3px; border-right-color: blue;` 만 쓰면 선이 나오지 않는다.
무늬의 기본값이 `none` 이라 두께가 0 으로 계산되기 때문이다.
테두리가 안 보이면 가장 먼저 무늬가 정해졌는지 본다.

### 2. 전환으로 무늬를 부드럽게 바꾸려 한다

원본의 팁 그대로 — discrete 값이라 부드러운 전환이 불가능하다.
`transition` 을 걸어도 `solid` → `dashed` 는 한 번에 바뀐다.
부드러운 효과가 필요하면 무늬는 고정하고, 서서히 바뀔 수 있는 색이나 두께를 바꾼다.

### 3. 부모에 준 테두리가 자식에게도 생길 거라 여긴다

상속되지 않으므로 자식은 기본값 `none` 을 갖는다.
자식에도 오른쪽 선이 필요하면 자식 선택자에 따로 쓴다.

### 4. 단축 속성이 뒤에서 덮어쓴다

`border-right-style: dotted;` 뒤에 `border-right: 3px blue;` 처럼 무늬를 뺀 단축 속성을 쓰면, 빠진 무늬가 기본값 `none` 으로 되돌아간다.
단축 속성은 적지 않은 부분을 기본값으로 다시 채운다.
단축 속성을 쓸 때는 무늬까지 함께 적거나, 개별 속성을 단축 속성 뒤에 둔다.

### 5. `hidden` 을 `none` 과 다른 「숨긴 테두리」로 오해한다

화면에서는 둘 다 선이 없다.
`hidden` 의 차이는 표의 테두리 병합에서만 나타난다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 기본값 `none` · 상속 안 됨 · 애니메이션 불가 | CSS 명세 |
| 무늬가 `none` 이면 두께가 0 으로 계산된다 | CSS 명세 |
| `hidden` 이 표 병합에서 우선한다 | CSS 명세 |
| `medium` 두께가 실제로 몇 px 인가 | 브라우저가 정한다 (확인 필요) |
| `groove` · `ridge` · `inset` · `outset` 의 밝은·어두운 색이 정확히 어떤 색인가 | 브라우저가 정한다 (확인 필요) |
| 점선의 점 모양(둥근 점인지 네모 점인지)과 간격 | 브라우저가 정한다 (확인 필요) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 오른쪽 변의 무늬만 바꾼다 | `border-right-style` | 네 변을 모두 건드리는 `border-style` |
| 오른쪽 선의 두께·무늬·색을 한 번에 정한다 | `border-right` 단축 속성 | 세 개별 속성을 흩어 쓰기 |
| 메뉴 항목 사이 세로 구분선 | `border-right-style: solid` | 빈 요소를 끼워 넣어 선 흉내 |
| hover 때 선이 서서히 바뀌는 효과 | `border-right-color` · `border-right-width` 전환 | `border-right-style` 전환 |
| 병합된 표에서 특정 칸 경계를 확실히 지운다 | `hidden` | `none`(다른 칸의 테두리에 질 수 있다) |

## 핵심 문장

1. **`border-right-style` 은 오른쪽 변의 선 무늬를 정하고, 기본값은 `none` 이다.**
2. **무늬가 `none` 이면 두께·색을 정해도 선이 없다** — 무늬가 테두리의 스위치다.
3. **상속되지 않고 애니메이션되지 않는다** — 값이 discrete 라 전환이 한 번에 일어난다.
4. **`hidden` 은 화면에선 `none` 과 같지만, 표 테두리 병합에서 우선한다.**
5. **`border-style` 의 두 번째 값과 `border-right` 단축 속성도 같은 자리를 정한다** — 나중 선언이 이긴다.

## 관련 자료

- `border-style` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `border-right` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [border-right-width](../32-border-right-width/2-summary.md)
- 원본: study-site 항목 데이터 `data/css/box-model.json` 의 `border-right-style`

## 용어 풀이

- **테두리(border)** — 박스의 padding 바깥, margin 안쪽에 놓이는 선.
- **기본값(initial value)** — 선언이 없을 때 속성이 갖는 값.
- **상속(inheritance)** — 부모의 값이 자식에게 저절로 옮아가는 성질.
- **discrete** — 중간 단계가 없어 보간할 수 없는 값.
- **전환(transition)** — 속성값이 바뀔 때 시간을 들여 서서히 바뀌게 하는 기능.
- **단축 속성(shorthand)** — 여러 개별 속성을 한 줄로 정하는 속성.
- **개별 속성(longhand)** — 단축 속성이 묶는 낱낱의 속성.
- **`currentcolor`** — 요소의 글자색을 가져다 쓰는 키워드.
- **`medium`** — 테두리 두께의 기본 키워드.
- **테두리 병합(border-collapse)** — 표에서 이웃 칸의 테두리를 한 줄로 합치는 방식.

## 더 들어가면

- `double` 은 두 줄과 그 사이 틈의 합이 테두리 두께가 되도록 그린다고 알려져 있다. 두께가 1~2px 처럼 얇으면 두 줄로 보이지 않고 실선처럼 보일 수 있다 (확인 필요).
- 최근 CSS 에는 discrete 속성도 전환에 참여시키는 `transition-behavior: allow-discrete` 가 있다. 그래도 중간값이 생기는 것은 아니고, 바뀌는 순간을 정할 뿐이다 (확인 필요).
- `@keyframes` 애니메이션에서는 discrete 값이 구간의 중간쯤에서 뒤바뀐다고 알려져 있다 (확인 필요).
- 쓰기 방향을 따르는 논리 속성 `border-inline-end-style` 은 가로 쓰기 · 왼쪽→오른쪽 문서에서 오른쪽 변과 같은 자리를 가리킨다 (확인 필요).
- 표 병합에서 충돌을 푸는 차례는 대략 `hidden` 이 가장 강하고, 그다음 두께가 두꺼운 쪽, 그다음 무늬 차례라고 정해져 있다 (확인 필요).

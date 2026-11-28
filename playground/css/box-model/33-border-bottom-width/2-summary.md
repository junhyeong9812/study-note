# css/box-model/33 — border-bottom-width — 정리 (힌트)

> 출처 — study-site 항목 `css/border-bottom-width`(항목 데이터 `data/css/box-model.json`) · 정답 코드 study-practice `css/box-model/reference/border-bottom-width.html`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

## 한눈에 — 쉽게 말하면

**`border-bottom-width` 는 「공책 밑줄 펜의 굵기」다.**
펜 굵기를 아무리 굵게 골라도, 밑줄을 긋기로 하지 않으면 종이에는 아무 선도 남지 않는다.
CSS 의 아래쪽 테두리도 똑같은 구조다.
굵기(`border-bottom-width`)는 선을 긋기로 했을 때(`border-bottom-style` 이 `none` 이 아닐 때)에만 실제 두께가 된다.

> **테두리(border)** — 요소의 안쪽 여백(padding)과 바깥 여백(margin) 사이에 놓이는 선이다.\
> 예: `border-bottom: 1px solid gray;` 는 아래쪽에만 회색 실선을 긋는다.

| 비유 | 실체 |
|---|---|
| 펜 굵기 | `border-bottom-width` |
| 밑줄을 긋기로 함 / 안 함 | `border-bottom-style` 이 `solid` 등 / `none` |
| 펜 색 | `border-bottom-color` |
| 밑줄이 그어지는 자리 | 박스의 아래 가장자리 |

```text
┌──────────────────────┐
│  padding             │
│     내용(content)     │
│                      │
└══════════════════════┘  ← 아래쪽 테두리: 두께 = border-bottom-width
```

## 이 주제가 답하려는 질문

1. 아래쪽 테두리의 두께는 어떤 값으로 정하나 — 길이와 키워드는 무엇이 다른가?
2. 두께를 적었는데도 선이 안 보이는 것은 왜인가?
3. 두께를 바꾸면 박스의 크기와 주변 배치는 어떻게 달라지나?
4. 아무것도 적지 않았을 때, 부모에게 적었을 때, 애니메이션할 때는 어떻게 되나?

## 동작 방식

### (1) 두께 값이 정해지는 길

**언제 쓰나** — 아래쪽 선의 굵기만 따로 조절하고 싶을 때 쓴다(탭 메뉴의 밑줄, 제목 아래 구분선 등).

```text
border-bottom-width: 5px;          → 길이 값 → 그대로 5px
border-bottom-width: thin;         → 키워드  → 브라우저가 정한 얇은 두께 (보통 1px)
border-bottom-width: medium;       → 키워드  → 중간 두께 (보통 3px)
border-bottom-width: thick;        → 키워드  → 두꺼운 두께 (보통 5px)
(아무것도 안 적음)                  → 기본값 medium
```

- 길이 값은 적은 그대로 두께가 된다.
- 키워드는 브라우저가 정한 두께로 바뀐다 — 원본은 「보통 1px / 3px / 5px」라고 적었다.
- 아무것도 적지 않으면 기본값 `medium` 이 쓰인다.

> **키워드 값** — 숫자 대신 이름으로 적는 CSS 값이다.\
> 예: `thin`, `medium`, `thick`.

### (2) 스타일이 `none` 이면 두께는 0

**언제 쓰나** — 「두께를 줬는데 선이 안 보인다」를 풀 때 이 규칙을 떠올린다.

```text
입력:  border-bottom-width: 5px;
       (border-bottom-style 은 적지 않음 → 기본값 none)

계산:  style 이 none 인가? → 예 → 두께를 0 으로 계산

결과:  아래쪽 테두리 없음, 박스 높이에도 더해지지 않음
```

- 먼저 두께 5px 이 선언된다.
- 스타일을 적지 않았으므로 아래쪽 스타일은 기본값 `none` 이다.
- 원본 팁대로 스타일이 `none` 이면 너비가 0 으로 계산된다.
- 그래서 선도 보이지 않고 차지하는 자리도 없다.

> **계산값(computed value)** — 선언된 값을 브라우저가 규칙에 따라 정리한 뒤의 값이다.\
> 예: 스타일이 `none` 일 때 `border-bottom-width: 5px` 의 계산값은 0 이다.

### (3) 두께는 박스의 크기에 더해진다

**언제 쓰나** — 테두리를 넣었더니 아래 요소가 밀려 내려갈 때 이 규칙으로 설명한다.

```text
box-sizing: content-box (기본)

  내용 높이 40px
+ padding 위·아래 0
+ 아래 테두리 5px
= 바깥 높이 45px      → 아래에 있는 요소가 5px 더 내려간다
```

- 기본 `box-sizing: content-box` 에서 `height` 는 내용 영역의 높이다.
- 테두리 두께는 그 바깥에 더해진다.
- 그래서 두께를 키울수록 박스가 차지하는 높이가 늘고, 뒤따르는 요소가 밀린다.
- `box-sizing: border-box` 로 두면 `height` 안에 테두리가 포함되어 바깥 높이는 그대로이고 내용 영역이 줄어든다.

> **box-sizing** — `width` · `height` 가 어느 영역의 크기를 뜻하는지 정하는 속성이다.\
> 예: `content-box` 는 내용 영역만, `border-box` 는 테두리까지 포함한 크기를 뜻한다.

### (4) 상속되지 않고, 애니메이션된다

**언제 쓰나** — 부모·자식에 테두리를 줄 때, 호버 때 밑줄을 굵게 바꿀 때 쓴다.

```text
.parent { border-bottom: 4px solid; }
   └ .child  → 상속 안 됨 → 자기 기본값(medium, style none → 0) → 선 없음

.tab { border-bottom: 2px solid; transition: border-bottom-width .3s; }
.tab:hover { border-bottom-width: 6px; }
   → 2px 에서 6px 로 두께가 사이값을 거치며 변한다
```

- 원본에 따르면 상속은 `False` 다 — 부모의 두께가 자식에게 내려가지 않는다.
- 원본에 따르면 애니메이션 가능은 `True` 다 — 두께는 길이로 계산되므로 사이값을 만들 수 있다.
- 다만 (3) 처럼 두께가 박스 크기에 더해지므로, 두께를 애니메이션하면 아래 요소도 함께 들썩인다.

## 문법 — 형태와 규칙

```html demo
<div class="a">thin</div>
<div class="b">5px solid</div>
<div class="c">5px 인데 style 없음</div>
<style>
  div { padding: 8px; margin-bottom: 12px; background: #f8fafc; }
  .a { border-bottom-style: solid; border-bottom-width: thin; }
  .b { border-bottom-style: solid; border-bottom-width: 5px; border-bottom-color: #3b82f6; }
  .c { border-bottom-width: 5px; }
</style>
```

> **보이는 것** — `.a` 는 얇은 밑줄, `.b` 는 굵은 파란 밑줄, `.c` 는 밑줄 없이 배경만 있는 박스다 (코드에서 읽은 것 — 렌더 실측 아님).

형태: `border-bottom-width: <line-width>`

| 값 | 뜻 | 메모 |
|---|---|---|
| `<length>` | 양수 길이 값 | `5px`, `0.2em` 등. 음수는 허용되지 않는다 |
| `thin` | 얇은 테두리 | 보통 1px |
| `medium` | 중간 테두리 | 보통 3px · **기본값** |
| `thick` | 두꺼운 테두리 | 보통 5px |

- 기본값은 `medium` 이다.
- 상속되지 않는다.
- 애니메이션할 수 있다.
- 실제로 그려지려면 `border-bottom-style` 이 `none` 이 아니어야 한다.
- 허용되지 않는 값(예: 음수 길이)을 적으면 그 선언은 무시되고, 앞서 적용되던 값이 그대로 남는다.
- `border-bottom: 5px solid blue` 같은 단축 속성도 두께를 정한다 — 단축 속성에서 두께를 빼면 두께는 `medium` 으로 되돌려진다.

> **단축 속성(shorthand)** — 여러 개별 속성을 한 줄로 한꺼번에 정하는 속성이다.\
> 예: `border-bottom` 은 아래쪽의 width · style · color 를 함께 정한다.

## 어디서 틀리나

### 1. 두께만 주고 스타일을 빠뜨린다

원본 팁: `border-bottom-style` 이 `none` 이면 너비가 0 으로 계산된다.
스타일의 기본값이 `none` 이므로, `border-bottom-width` 만 적으면 선이 생기지 않는다.
두께·스타일·색은 세트로 적거나 `border-bottom` 단축 속성으로 한 번에 적는다.

### 2. 단축 속성이 앞서 적은 두께를 덮는다

```css
.x { border-bottom-width: 5px; border-bottom: solid red; }
```

뒤의 `border-bottom` 이 두께를 따로 적지 않았으므로 두께가 `medium` 으로 되돌아간다.
개별 속성은 단축 속성 **뒤에** 적어야 살아남는다.

### 3. 키워드 두께를 정확한 px 로 믿는다

`thin` · `medium` · `thick` 의 1px · 3px · 5px 은 원본이 「보통」이라고 적은 값이다.
정확한 두께가 필요하면 길이 값을 쓴다.

### 4. 두께를 바꿨더니 레이아웃이 흔들린다

두께는 박스 크기에 더해진다(동작 방식 (3)).
호버 때 0 → 3px 로 바꾸면 아래 요소가 3px 밀린다.
처음부터 같은 두께를 주고 색만 `transparent` 에서 바꾸거나, `box-sizing` 을 고려한다.

### 5. 부모에 준 두께가 자식에도 있을 거라 생각한다

상속되지 않으므로 자식은 자기 기본값을 쓴다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 기본값이 `medium` 이다 | CSS 명세 |
| 상속되지 않는다 | CSS 명세 |
| 애니메이션할 수 있다 | CSS 명세 (원본 `True`) |
| 스타일이 `none` 이면 두께가 0 으로 계산된다 | CSS 명세 (원본 팁) |
| `thin` 은 1px, `medium` 은 3px, `thick` 은 5px | 원본은 「보통」이라 적었다 — 브라우저 관례인지 명세 고정값인지 (확인 필요) |
| `thin` ≤ `medium` ≤ `thick` 순서 | 이름이 뜻하는 순서 — 명세가 순서를 정한다는 것은 (확인 필요) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 아래쪽 선 굵기만 바꾸기(이미 스타일이 있을 때) | `border-bottom-width` | `border-bottom` 전체 재선언(스타일·색까지 덮음) |
| 아래쪽 선을 새로 만들기 | `border-bottom: 2px solid …` 단축 속성 | `border-bottom-width` 하나만 |
| 정확한 픽셀 두께가 필요 | 길이 값 `2px` | `thin` 등 키워드 |
| 호버 때 밑줄 강조, 레이아웃 고정 필요 | 두께 고정 + 색 변경 | 두께 0 → n 애니메이션 |
| 네 변 두께를 한꺼번에 | `border-width` | 네 개의 개별 속성 반복 |

## 핵심 문장

1. **`border-bottom-width` 는 아래쪽 테두리의 두께만 정한다** — 길이 값이나 `thin` · `medium` · `thick` 키워드를 쓰고, 기본값은 `medium` 이다.
2. **스타일이 `none` 이면 두께는 0 으로 계산된다** — 그래서 두께만 적으면 선이 생기지 않는다.
3. **두께는 박스 크기에 더해진다** — 두께를 바꾸면 주변 배치도 바뀐다.
4. **상속되지 않고, 애니메이션할 수 있다.**
5. **단축 속성 `border-bottom` 은 빠뜨린 두께를 `medium` 으로 되돌린다** — 개별 속성은 단축 속성 뒤에 적는다.

## 관련 자료

- `border-width` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `border-bottom` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [border-bottom-style](../37-border-bottom-style/2-summary.md)
- 원본: study-site 항목 데이터 `data/css/box-model.json` 의 `border-bottom-width`

## 용어 풀이

- **테두리(border)** — padding 과 margin 사이에 놓이는 선.
- **`border-bottom-width`** — 아래쪽 테두리의 두께를 정하는 속성.
- **`border-bottom-style`** — 아래쪽 테두리의 선 모양(`solid`, `dashed`, `none` 등)을 정하는 속성.
- **`border-bottom-color`** — 아래쪽 테두리의 색을 정하는 속성.
- **키워드 값** — 숫자 대신 이름으로 적는 값(`thin` 등).
- **길이 값(`<length>`)** — 단위가 붙은 수(`5px`, `1em`).
- **계산값(computed value)** — 브라우저가 규칙을 적용해 정리한 값.
- **상속** — 부모의 값이 자식에게 자동으로 내려가는 것.
- **단축 속성** — 여러 개별 속성을 한 번에 정하는 속성.
- **box-sizing** — `width` · `height` 가 어느 영역의 크기인지 정하는 속성.

## 더 들어가면

- 테두리 두께에는 퍼센트 값을 쓸 수 없다 (확인 필요).
- `border-bottom-style: hidden` 도 `none` 처럼 두께가 0 으로 계산된다 (확인 필요).
- 논리 속성 `border-block-end-width` 는 쓰기 방향에 따라 「블록 끝」 변의 두께를 정한다 — 가로쓰기에서는 아래쪽과 같다 (확인 필요).
- 아주 얇은 값(예: `0.5px`)은 브라우저가 기기 픽셀에 맞춰 반올림해 그릴 수 있다 (확인 필요).
- 레이아웃을 흔들지 않는 밑줄이 필요하면 `box-shadow: inset 0 -3px 0 …` 같은 그림자로 대신하기도 한다 (확인 필요).

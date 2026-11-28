# css/box-model/62 — outline-width — 정리 (힌트)

> 출처 — study-site 항목 `css/outline-width`(항목 데이터 `data/css/box-model.json`) · 정답 코드 study-practice `css/box-model/reference/outline-width.html`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

## 한눈에 — 쉽게 말하면

**`outline-width` 는 「형광펜 선의 굵기」다.**
형광펜으로 글 둘레에 테두리를 칠한다고 하자.
선을 얼마나 굵게 그을지 정하는 것이 굵기다.
그런데 펜 뚜껑을 닫아 두면(선 모양이 「없음」) 굵기를 아무리 정해도 종이에는 아무것도 남지 않는다.
`outline-width` 도 똑같은 구조다.
외곽선의 두께만 정하고, 선의 모양(`outline-style`)과 색(`outline-color`)은 다른 속성이 맡는다.

| 비유 | 실체 |
|---|---|
| 형광펜 선의 굵기 | `outline-width` 값 |
| 펜 뚜껑을 열고 그을지, 어떤 무늬로 그을지 | `outline-style` |
| 형광펜 색 | `outline-color` |
| 뚜껑이 닫힘 | `outline-style: none` → 두께가 0 으로 계산된다 |

```text
  outline-style: solid            outline-style: none
  outline-width: 4px              outline-width: 4px
 ┏━━━━━━━━━━━━━━━━━┓
 ┃   글자 상자      ┃               글자 상자
 ┗━━━━━━━━━━━━━━━━━┛
   두께 4px 선이 둘레에             두께가 0 으로 계산 → 선 없음
```

## 이 주제가 답하려는 질문

1. 외곽선의 두께는 어떤 값으로 정하나 — 길이값과 키워드는 어떻게 다른가?
2. 두께를 정했는데 선이 안 보이는 것은 언제인가?
3. 따로 정하지 않으면 두께는 얼마이고, 부모의 값을 물려받나?
4. 두께를 부드럽게 바꾸는 애니메이션을 걸 수 있나?

## 동작 방식

### (1) 두께를 정하는 두 가지 방법 — 길이값과 키워드

**언제 쓰나** — 정확한 두께가 필요하면 길이값을, 「얇게 · 보통 · 굵게」 정도면 키워드를 쓴다.

```text
입력                          무엇이 일어나나                       결과
outline-width: 4px     →     적힌 길이를 그대로 두께로 쓴다      →  4px 두께
outline-width: 0.1em   →     글자 크기에 비례한 길이로 바꾼다    →  글자가 클수록 굵다
outline-width: thin    →     브라우저가 정한 「얇은」 두께        →  보통 1px
outline-width: medium  →     브라우저가 정한 「중간」 두께        →  보통 3px
outline-width: thick   →     브라우저가 정한 「두꺼운」 두께      →  보통 5px
```

- 길이값은 적은 숫자와 단위가 그대로 두께가 된다.
- `em` 같은 상대 단위는 글자 크기를 기준으로 실제 길이가 정해진다.
- 키워드 세 개는 실제 px 값이 원본에서도 「보통」으로만 적혀 있다 — 정확한 값은 브라우저가 정한다.

> **길이값(`<length>`)** — 숫자와 단위로 적은 크기 값이다.\
> 예: `1px`, `0.1em`.

> **키워드** — 미리 이름이 정해진 값이다.\
> 예: `thin`, `medium`, `thick`.

### (2) 선 모양이 없으면 두께는 0 이 된다

**언제 쓰나** — 「두께를 줬는데 외곽선이 안 보인다」를 풀 때 이 규칙을 떠올린다.

```text
입력                                 무엇이 일어나나                         결과
outline-width: thick;          →    style 이 none 인지 본다               →  계산된 두께 0
outline-style: none;                (none 이면 두께를 0 으로 계산한다)        선이 그려지지 않는다

outline-width: 4px;            →    style 이 solid → 두께를 그대로 쓴다   →  계산된 두께 4px
outline-style: solid;                                                         실선이 그려진다
```

- 브라우저는 `outline-width` 에 적힌 값을 곧바로 쓰지 않고 「계산된 값」을 만든다.
- 그때 `outline-style` 이 `none` 이면 적힌 두께와 상관없이 0 으로 계산한다.
- 그래서 외곽선을 보이게 하려면 `outline-style` 에 `none` 이 아닌 값(예: `solid`)을 함께 준다.

> **계산된 값** — 적힌 값을 규칙에 따라 다듬어 실제로 쓰는 최종 값이다.\
> 예: `outline-style: none` 일 때 `outline-width: thick` 의 계산된 값은 0.

### (3) 기본값과 상속

**언제 쓰나** — 아무 값도 적지 않은 요소의 두께가 얼마인지 알아야 할 때.

```text
입력                                       무엇이 일어나나                    결과
부모 { outline-width: 8px }          →    outline-width 는 상속 안 됨   →  자식의 두께는 기본값
자식 { outline-style: solid }              자식은 자기 기본값을 쓴다         medium (보통 3px)
```

- `outline-width` 의 기본값은 `medium` 이다.
- 이 속성은 상속되지 않는다 — 부모가 8px 이어도 자식은 따로 적지 않으면 `medium` 이다.

> **상속** — 부모 요소의 속성 값을 자식이 따로 적지 않아도 물려받는 것이다.\
> 예: `color` 는 상속되지만 `outline-width` 는 상속되지 않는다.

### (4) 두께는 애니메이션이 된다

**언제 쓰나** — 마우스를 올리거나 포커스를 받을 때 외곽선이 서서히 굵어지게 하고 싶을 때.

```text
입력                                       무엇이 일어나나                        결과
.btn { outline: 1px solid; 
       transition: outline-width .3s }  →  두 값 사이를 시간에 따라 이어 준다 →  1px → 4px 로
.btn:hover { outline-width: 4px }                                                 서서히 굵어진다
```

- 원본 재료에서 이 속성은 「애니메이션 가능」이다.
- 그래서 `transition` 으로 두께가 바뀌는 과정을 부드럽게 보여 줄 수 있다.

> **애니메이션 가능** — 두 값 사이의 중간값을 만들어 시간에 따라 서서히 바뀌게 할 수 있다는 뜻이다.\
> 예: 1px 에서 4px 로 갈 때 2px, 3px 를 거친다.

## 문법 — 형태와 규칙

```css
outline-width: <length> | thin | medium | thick
```

```html demo
<div class="a">thin</div>
<div class="b">4px</div>
<div class="c">style 없음</div>
<style>
  div { padding: 12px; margin: 16px; outline-color: #3b82f6; }
  .a { outline-style: solid; outline-width: thin; }
  .b { outline-style: solid; outline-width: 4px; }
  .c { outline-width: thick; }  /* outline-style 을 주지 않음 */
</style>
```

> **보이는 것** — 위 상자는 얇은 파란 외곽선, 가운데 상자는 4px 파란 외곽선, 아래 상자는 외곽선이 보이지 않을 것이다(`outline-style` 기본값이 `none` 이라는 전제) (코드에서 읽은 것 — 렌더 실측 아님).

| 값 | 뜻 | 원본이 적은 대략값 |
|---|---|---|
| `<length>` | 고정 너비 값 | 적은 그대로 (예: `1px`, `0.1em`) |
| `thin` | 얇은 외곽선 | 보통 1px |
| `medium` | 중간 외곽선 (기본값) | 보통 3px |
| `thick` | 두꺼운 외곽선 | 보통 5px |

- 값은 하나만 적는다 — 길이값이거나 키워드 셋 중 하나다.
- 기본값은 `medium` 이다.
- 상속되지 않는다.
- 애니메이션이 된다.
- 선 모양(`outline-style`)과 색(`outline-color`)은 따로 정한다.

## 어디서 틀리나

### 1. 두께만 주고 선 모양을 안 줬다

원본 팁: `outline-style` 이 `none` 이면 `outline-width` 는 0 으로 계산된다.
`outline-width: 4px` 만 적으면 선 모양이 `none` 인 채로 남아 외곽선이 보이지 않을 수 있다.
두께를 정할 때는 `outline-style` 에 `solid` 같은 값을 반드시 함께 준다.
개발자 도구에서 계산된 `outline-width` 가 0 으로 보이면 이 경우를 먼저 의심한다.

### 2. 키워드를 정확한 px 로 믿었다

`thin` · `medium` · `thick` 은 원본에서도 「보통 1px · 3px · 5px」로만 적혀 있다.
픽셀 단위로 맞춰야 하는 디자인이라면 키워드 대신 길이값을 쓴다.

### 3. 부모에 준 두께가 자식에게도 갈 줄 알았다

`outline-width` 는 상속되지 않는다.
자식에게도 같은 두께를 주려면 자식에게 직접 적는다.

### 4. `em` 두께가 글자 크기에 따라 변한다는 것을 잊었다

`0.1em` 은 글자 크기에 비례한다.
글자 크기가 다른 요소마다 외곽선 두께가 달라진다.
모든 요소에서 같은 두께가 필요하면 `px` 같은 고정 길이를 쓴다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `thin` ≈ 1px, `medium` ≈ 3px, `thick` ≈ 5px | 브라우저(구현)가 정한다 — 원본도 「보통」으로만 적었다 |
| `outline-style` 이 `none` 이면 `outline-width` 는 0 으로 계산된다 | CSS 명세의 계산값 규칙으로 알려져 있다 (확인 필요) |
| 기본값 `medium`, 상속 안 됨 | CSS 명세의 속성 정의 |
| 애니메이션 가능 | CSS 명세의 속성 정의 (길이로 보간) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 외곽선 두께를 픽셀 단위로 정확히 맞춤 | `outline-width: 2px` 같은 길이값 | `thin` · `thick` 키워드 |
| 대략 「얇게 · 굵게」면 충분 | `thin` · `medium` · `thick` | 굳이 정밀한 길이값 |
| 글자 크기에 맞춰 두께도 커지게 | `em` 길이값 | 고정 `px` |
| 외곽선을 보이게 하기 | `outline-width` + `outline-style: solid` 등 | `outline-width` 만 단독으로 |
| 마우스 올림 · 포커스 때 두께를 서서히 바꾸기 | `transition: outline-width …` | 갑자기 바뀌는 값 전환만 |

## 핵심 문장

1. **`outline-width` 는 외곽선의 두께만 정한다** — 모양은 `outline-style`, 색은 `outline-color` 가 맡는다.
2. **값은 길이값 또는 `thin` · `medium` · `thick` 키워드다** — 키워드의 실제 px 는 브라우저가 정한다.
3. **`outline-style` 이 `none` 이면 두께는 0 으로 계산된다** — 그래서 선 모양을 함께 줘야 보인다.
4. **기본값은 `medium`, 상속되지 않고, 애니메이션이 된다.**

## 관련 자료

- `outline` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `outline-style` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `outline-color` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/css/box-model.json` 의 `outline-width`

## 용어 풀이

- **외곽선(outline)** — 요소 둘레에 그려지는 선이다.
- **길이값(`<length>`)** — 숫자와 단위로 적은 크기 값이다(`1px`, `0.1em`).
- **키워드** — 미리 이름이 정해진 값이다(`thin`, `medium`, `thick`).
- **`em`** — 글자 크기를 기준으로 하는 상대 길이 단위다.
- **기본값** — 아무것도 적지 않았을 때 쓰이는 값이다.
- **상속** — 부모의 속성 값을 자식이 저절로 물려받는 것이다.
- **계산된 값** — 적힌 값을 규칙에 따라 다듬어 실제로 쓰는 최종 값이다.
- **애니메이션 가능** — 두 값 사이를 중간값으로 이어 서서히 바꿀 수 있다는 뜻이다.
- **`transition`** — 속성 값이 바뀔 때 그 변화를 시간에 걸쳐 보여 주는 CSS 속성이다.

## 더 들어가면

- `outline` 은 `border` 와 달리 레이아웃에서 자리를 차지하지 않는다고 알려져 있다 — 두께를 바꿔도 주변 요소가 밀리지 않는다 (확인 필요).
- `outline` 단축 속성(`outline: 4px solid #3b82f6`)으로 두께 · 모양 · 색을 한 번에 적을 수 있다 (확인 필요).
- `outline-style` 의 기본값은 `none` 이다 — 그래서 두께만 적으면 보이지 않는다 (확인 필요).
- `outline-width` 에는 퍼센트 값을 쓸 수 없는 것으로 알려져 있다 (확인 필요).
- 외곽선과 요소 사이의 간격은 `outline-offset` 으로 조절한다 (확인 필요).
- 키보드 포커스 표시에 외곽선이 쓰이므로, 외곽선을 없앨 때는 다른 포커스 표시를 마련하는 것이 접근성에 좋다 (확인 필요).

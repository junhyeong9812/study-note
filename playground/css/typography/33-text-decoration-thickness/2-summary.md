# css/typography/33 — text-decoration-thickness — 정리 (힌트)

> 출처 — study-site 항목 `css/text-decoration-thickness`(항목 데이터 `data/css/typography.json`) · 정답 코드 study-practice `css/typography/reference/text-decoration-thickness.html`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

## 한눈에 — 쉽게 말하면

**`text-decoration-thickness` 는 「형광펜 대신 쓰는 펜의 굵기」다.**
글자 아래에 줄을 긋기로 했으면(밑줄을 켰으면), 어떤 굵기의 펜으로 그을지는 따로 고른다.
줄을 긋지 않기로 했다면 펜 굵기를 아무리 골라도 종이에는 아무것도 남지 않는다.
CSS 의 장식 선도 똑같은 구조다.
`text-decoration: underline` 이 「줄을 긋는다」를 정하고, `text-decoration-thickness` 가 「그 줄의 굵기」를 정한다.

> **텍스트 장식 선** — 글자에 붙여 그리는 선. 밑줄 · 윗줄 · 취소선이 있다.\
> 예: `text-decoration: underline` 은 글자 아래에 밑줄을 긋는다.

| 비유 | 실체 |
|---|---|
| 줄을 긋기로 한 결정 | `text-decoration: underline` (선의 종류) |
| 펜 굵기 | `text-decoration-thickness` 값 |
| 「알아서 적당한 펜」 | `auto` |
| 「공책 회사가 권하는 펜」 | `from-font` (글꼴이 지정한 두께) |
| 글씨 크기에 맞춰 펜을 바꾸기 | `em` · `%` 값 |

```text
  Thin  얇은 밑줄        ← thickness: 1px
  ────────────

  Medium 중간 밑줄       ← thickness: 3px
  ━━━━━━━━━━━━

  Thick 두꺼운 밑줄      ← thickness: 5px
  ████████████
```

## 이 주제가 답하려는 질문

1. 밑줄 같은 장식 선의 굵기는 무엇으로 정하고, 어떤 값을 쓸 수 있나?
2. 굵기를 고정할 때와 글자 크기에 맞춰 늘고 줄게 할 때는 어떻게 다르게 쓰나?
3. 굵기를 바꾸는 것을 애니메이션(호버 효과)으로 만들 수 있나?
4. 값을 안 주면 무엇이 쓰이고, 부모의 값은 자식에게 넘어가나?

## 동작 방식

### (1) 선이 먼저, 두께는 그다음

**언제 쓰나** — 밑줄 · 취소선 같은 장식 선을 이미 켜 놓고, 그 선이 너무 가늘거나 굵을 때 쓴다.

```text
입력 코드                                 무엇이 일어나나                    결과
.a { text-decoration: underline;     →   ① 선의 종류: 밑줄을 그린다      →  글자 아래 3px 밑줄
     text-decoration-thickness: 3px; }   ② 그 밑줄의 두께를 3px 로 한다

.b { text-decoration-thickness: 3px; } →  ① 그릴 선이 없다                →  선이 보이지 않음
                                          ② 두께 값은 적용할 곳이 없다
```

- 이 속성의 설명은 「텍스트 장식 선의 두께를 설정」이다 — 두께는 선이 있어야 의미가 있다.
- 원본 예제의 세 클래스는 모두 `text-decoration: underline` 과 두께를 **짝으로** 쓴다.
- `.b` 처럼 선 없이 두께만 주면 그릴 대상이 없으니 화면에는 아무 장식도 나타나지 않는다 (코드에서 읽은 것 — 렌더 실측 아님).

```html demo
<p style="text-decoration: underline; text-decoration-thickness: 3px; font-size: 18px;">밑줄 3px</p>
<p style="text-decoration-thickness: 3px; font-size: 18px;">두께만 3px</p>
```

> **보이는 것** — 첫 줄에는 굵은 밑줄이 있고, 둘째 줄에는 밑줄이 없다 (코드에서 읽은 것 — 렌더 실측 아님).

### (2) 네 가지 값

**언제 쓰나** — 두께를 브라우저에 맡길지, 글꼴에 맡길지, 직접 정할지 고를 때.

```text
값               누가 두께를 정하나            예
auto (기본값)  → 브라우저가 적절히 고른다    →  text-decoration-thickness: auto
from-font      → 글꼴에 지정된 두께를 쓴다   →  text-decoration-thickness: from-font
<length>       → 내가 정한 고정 길이          →  2px, 0.1em
<percentage>   → font-size 기준 백분율        →  10%
```

- `auto` 는 기본값이라 아무것도 안 쓰면 이 값이다 — 두께는 브라우저 판단에 맡겨진다.
- `from-font` 는 글꼴 파일이 「이 글꼴의 밑줄은 이 정도 굵기」라고 정해 둔 값을 가져다 쓴다.
- `<length>` 는 `px` 같은 절대 단위도, `em` 같은 상대 단위도 된다.
- `<percentage>` 는 그 요소의 `font-size` 를 100% 로 보고 계산한다.

> **from-font** — 글꼴이 스스로 정해 둔 장식 선 두께를 쓰라는 키워드.\
> 예: 같은 `from-font` 라도 글꼴이 바뀌면 두께가 달라질 수 있다.

### (3) 고정 두께 대 비례 두께

**언제 쓰나** — 같은 스타일을 크기가 다른 글자(제목 · 본문 · 주석)에 함께 쓸 때 어느 쪽을 고를지 정한다.

```text
입력 코드                           font-size 18px 일 때   font-size 36px 일 때
thickness: 2px                 →   2px                →   2px      (그대로)
thickness: 0.1em               →   1.8px              →   3.6px    (글자 따라 두 배)
thickness: 10%                 →   1.8px              →   3.6px    (글자 따라 두 배)
```

- `px` 는 글자 크기와 상관없이 늘 같은 두께다.
- `em` 은 그 요소의 `font-size` 의 배수라서 글자가 커지면 같이 굵어진다 — 0.1em × 18px = 1.8px.
- `%` 도 `font-size` 기준이라 10% × 18px = 1.8px, 36px 이면 3.6px 이 된다.
- 원본 팁 그대로 — em 이나 % 를 쓰면 `font-size` 에 비례해 자동 조절된다.

> **em** — 그 요소의 글자 크기를 1 로 보는 길이 단위.\
> 예: `font-size: 20px` 인 요소에서 `0.1em` 은 2px.

### (4) 두께를 애니메이션하기

**언제 쓰나** — 링크에 마우스를 올리면 밑줄이 굵어지는 호버 효과를 만들 때.

```text
입력 코드                                          무엇이 일어나나                         결과
a { text-decoration: underline;               →   평소: 1px                             →  가는 밑줄
    text-decoration-thickness: 1px;               호버: 4px 로 바뀐다
    transition: text-decoration-thickness .3s; }  transition 이 0.3초 동안 중간값을 채운다  →  밑줄이 서서히 굵어짐
a:hover { text-decoration-thickness: 4px; }
```

- 이 속성은 「애니메이션 가능」으로 표시된 속성이다.
- 그래서 `transition` 에 이 속성을 걸면 두 길이 사이를 중간값으로 이어 준다.
- 마우스를 떼면 같은 시간에 걸쳐 1px 로 돌아온다 (코드에서 읽은 것 — 렌더 실측 아님).

> **transition** — 속성 값이 바뀔 때 정한 시간 동안 중간값을 이어 그려 주는 CSS 기능.\
> 예: `transition: color .3s` 는 색을 0.3초에 걸쳐 바꾼다.

```html demo
<style>
  .link { font-size: 20px; text-decoration: underline; text-decoration-thickness: 1px;
          transition: text-decoration-thickness .3s; }
  .link:hover { text-decoration-thickness: 4px; }
</style>
<a class="link" href="#">마우스를 올려 보세요</a>
```

> **보이는 것** — 평소에는 가는 밑줄이고, 마우스를 올리면 0.3초 동안 밑줄이 굵어진다 (코드에서 읽은 것 — 렌더 실측 아님).

## 문법 — 형태와 규칙

```css
/* 선을 켜고 두께를 정한다 */
.note  { text-decoration: underline; text-decoration-thickness: auto; }      /* 기본값 */
.font  { text-decoration: underline; text-decoration-thickness: from-font; } /* 글꼴 값 */
.fixed { text-decoration: underline; text-decoration-thickness: 2px; }       /* 고정 */
.scale { text-decoration: underline; text-decoration-thickness: 0.1em; }     /* 비례 */
.pct   { text-decoration: underline; text-decoration-thickness: 10%; }       /* font-size 기준 */
```

| 항목 | 내용 |
|---|---|
| 문법 | `text-decoration-thickness: auto \| from-font \| <length> \| <percentage>` |
| 기본값 | `auto` |
| 상속 | 안 됨 (`False`) |
| 애니메이션 | 가능 (`True`) |
| 키워드 | 장식선두께 · 밑줄두께 · 데코레이션두께 |

| 값 | 뜻 | 쓸 때 |
|---|---|---|
| `auto` | 브라우저가 적절한 두께 결정 | 특별히 정할 것이 없을 때 |
| `from-font` | 글꼴에 지정된 두께 사용 | 글꼴 디자이너의 의도를 따르고 싶을 때 |
| `<length>` | 고정 두께 (예: `2px`, `0.1em`) | 정확한 굵기가 필요할 때 · em 이면 비례 |
| `<percentage>` | `font-size` 기준 백분율 | 글자 크기에 맞춰 늘고 줄게 할 때 |

- 값은 하나만 쓴다.
- 장식 선 자체는 `text-decoration`(종류)으로 따로 켠다.
- 상속되지 않으므로, 자식 요소에서 이 속성의 값을 따로 정하지 않으면 그 자식의 값은 기본값 `auto` 다.

> **상속** — 부모에 준 속성 값이 자식 요소의 값으로 자동으로 넘어가는 것.\
> 예: `color` 는 상속되어 부모 글자색이 자식에게도 적용된다.

## 어디서 틀리나

### 1. 선 없이 두께만 준다
`text-decoration-thickness: 3px` 만 쓰고 밑줄을 켜지 않으면 아무 선도 보이지 않는다.
두께는 「그릴 선」이 있어야 쓰인다 — `text-decoration: underline` 과 짝으로 쓴다.

### 2. 크기가 다른 글자에 같은 px 두께를 쓴다
`2px` 는 큰 제목에서는 가늘어 보이고 작은 주석에서는 너무 굵어 보일 수 있다.
원본 팁 그대로 — em 이나 % 를 쓰면 `font-size` 에 비례해 자동 조절된다.

### 3. % 의 기준을 부모 너비로 착각한다
이 속성의 `%` 는 너비가 아니라 그 요소의 `font-size` 기준이다.
`font-size: 20px` 에서 `10%` 는 2px 이다.

### 4. auto 의 두께를 어디서나 같다고 믿는다
`auto` 는 「브라우저가 적절한 두께를 결정」한다는 뜻이다.
정확한 값이 필요하면 `<length>` 로 직접 정한다.

### 5. 호버 효과를 transition 없이 기대한다
원본 팁 — 이 속성은 호버 효과에서 두께 변경을 애니메이션할 수 있다.
다만 `transition` 을 걸지 않으면 두께는 순간적으로 바뀐다.

### 6. 부모에 준 두께가 자식의 값이 된다고 생각한다
이 속성은 상속되지 않는다.
자식 요소에 밑줄을 따로 켰다면, 그 자식의 두께는 자식에게 직접 준 값(없으면 `auto`)을 따른다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 기본값은 `auto` 이고 상속되지 않는다 | CSS 명세(속성 정의) |
| `%` 는 `font-size` 기준이다 · `em` 은 글자 크기에 비례한다 | CSS 명세(값 정의) |
| `auto` 일 때 실제 몇 px 로 그려지나 | 브라우저 구현 — 브라우저마다 다를 수 있다 (확인 필요) |
| `from-font` 의 실제 두께 | 글꼴 파일 — 글꼴이 값을 지정해 두지 않았을 때의 처리는 브라우저에 달렸다 (확인 필요) |
| 1.8px 같은 소수 두께가 화면에서 어떻게 보이나 | 브라우저 · 화면 해상도 — 반올림 방식은 구현마다 다를 수 있다 (확인 필요) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 링크 밑줄을 디자인에 맞게 굵게 | `text-decoration-thickness: 2px` 등 고정 길이 | 밑줄 대신 `border-bottom` 흉내 |
| 제목 · 본문 모두에 같은 비율의 밑줄 | `0.1em` 또는 `10%` | 크기마다 다른 px 를 따로 적기 |
| 글꼴 디자인을 존중하고 싶다 | `from-font` | 임의의 px |
| 호버 시 밑줄이 굵어지는 효과 | 두께 + `transition` | 클래스 교체만으로 순간 변경(부드러움이 필요할 때) |
| 밑줄 자체가 없는 텍스트 | (먼저 `text-decoration` 으로 선을 켠다) | 두께만 지정 |

## 핵심 문장

1. **`text-decoration-thickness` 는 장식 선의 굵기만 정한다** — 선 자체는 `text-decoration` 으로 켜야 한다.
2. **값은 넷이다** — `auto`(브라우저) · `from-font`(글꼴) · `<length>`(직접) · `<percentage>`(`font-size` 기준).
3. **em 과 % 는 글자 크기를 따라가고 px 는 그대로다** — 크기가 섞인 문서에는 비례 값이 편하다.
4. **애니메이션이 가능하다** — `transition` 과 함께 호버 효과로 두께를 부드럽게 바꿀 수 있다.
5. **기본값은 `auto` 이고 상속되지 않는다.**

## 관련 자료

- `text-decoration` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `text-underline-offset` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/css/typography.json` 의 `text-decoration-thickness`

## 용어 풀이

- **텍스트 장식 선** — 글자에 붙여 그리는 밑줄 · 윗줄 · 취소선.
- **`text-decoration`** — 어떤 장식 선을 그릴지 정하는 속성(여기서는 `underline`).
- **두께(thickness)** — 장식 선의 굵기.
- **`auto`** — 브라우저가 두께를 고르게 하는 기본값.
- **`from-font`** — 글꼴이 지정한 두께를 쓰라는 키워드.
- **`<length>`** — `px` · `em` 같은 길이 값.
- **`<percentage>`** — `%` 값. 이 속성에서는 `font-size` 기준.
- **em** — 그 요소의 글자 크기를 1 로 보는 상대 단위.
- **상속** — 부모의 속성 값이 자식에게 자동으로 넘어가는 것.
- **transition** — 값이 바뀔 때 중간값을 이어 부드럽게 바꾸는 기능.
- **호버** — 마우스 포인터를 요소 위에 올린 상태(`:hover`).

## 더 들어가면

- 상속은 안 되지만, 부모에 그린 장식 선은 자식 글자 위로도 이어 그려진다 — 이때 선의 두께는 부모의 값을 따른다(「장식 전파」) (확인 필요).
- 최신 명세에서 `text-decoration` 단축 속성은 두께도 포함한다고 알려져 있다 — 그러면 두께를 먼저 쓰고 `text-decoration: underline` 을 뒤에 쓰면 두께가 `auto` 로 되돌아갈 수 있다 (확인 필요).
- `auto` 나 `from-font` 같은 키워드와 길이 사이의 전환은 부드럽게 이어지지 않고 한 번에 바뀔 수 있다 (확인 필요).
- 밑줄의 위치는 `text-underline-offset` 으로, 색은 `text-decoration-color` 로, 모양은 `text-decoration-style` 로 따로 정한다 (확인 필요).
- 아주 큰 두께는 아래쪽 글자(g, y 의 꼬리)와 겹칠 수 있고, 브라우저는 이런 부분을 건너뛰어 그리기도 한다(`text-decoration-skip-ink`) (확인 필요).

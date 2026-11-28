# css/typography/32 — text-decoration-style — 정리 (힌트)

> 출처 — study-site 항목 `css/text-decoration-style`(항목 데이터 `data/css/typography.json`) · 정답 코드 study-practice `css/typography/reference/text-decoration-style.html`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

## 한눈에 — 쉽게 말하면

**`text-decoration-style` 은 「밑줄 긋는 펜의 종류」다.**
공책에 밑줄을 그을 때 줄을 그을지 말지는 먼저 정한다.
그다음에 자를 대고 곧게 그을지, 두 줄로 그을지, 점을 찍을지, 짧게 끊어 그을지, 구불구불 그을지를 고른다.
CSS 의 장식선도 똑같은 구조다.
「줄을 긋는다」는 결정은 장식선 종류(`underline` 등)가 맡고, 「어떤 모양으로」는 `text-decoration-style` 이 맡는다.

> **장식선(text decoration)** — 글자에 덧그리는 선. 밑줄 · 윗줄 · 가운데 줄이 있다.\
> 예: 링크 아래의 밑줄, 취소된 가격 위의 가운데 줄.

| 비유 | 실체 |
|---|---|
| 밑줄을 그을지 말지 | 장식선 종류 — `underline` 같은 값 |
| 펜의 종류(곧은 선 · 두 줄 · 점 · 끊긴 선 · 물결) | `text-decoration-style` 의 값 |
| 아무 펜도 고르지 않으면 쓰는 기본 펜 | 기본값 `solid` |

```text
  "밑줄을 긋는다"          +   "어떤 펜으로?"          =   화면의 선
  (underline)                 (text-decoration-style)
                              solid   ────────
                              double  ════════
                              dotted  ········
                              dashed  - - - - -
                              wavy    ∿∿∿∿∿∿∿∿
```

## 이 주제가 답하려는 질문

1. 장식선의 모양은 어떤 값으로 고르고, 값마다 어떤 선이 되나?
2. 모양만 정하고 선 종류를 정하지 않으면 무슨 일이 생기나?
3. 모양을 `text-decoration` 단축 속성으로 정할 때와 따로 정할 때는 어떻게 맞물리나?
4. 이 속성은 상속되나, 애니메이션되나?

## 동작 방식

### (1) 선이 있어야 모양이 보인다

**언제 쓰나** — 밑줄 · 윗줄 · 가운데 줄을 기본 실선이 아닌 모양으로 바꾸고 싶을 때.

```text
입력                                         일어나는 일                          결과
p { text-decoration-style: wavy; }      →   모양은 wavy 로 정해짐              →  선 없음
                                             그릴 선 종류는 정해지지 않음
p { text-decoration: underline wavy; }  →   선 종류 = underline                →  물결 밑줄
                                             모양    = wavy
```

- 원본의 설명대로 이 속성은 「장식 선의 스타일」, 곧 선의 **모양**만 정한다.
- 그릴 선이 정해지지 않았으면 모양을 정해도 그려질 것이 없다.
- 원본 예제가 모든 클래스에서 `underline` 과 모양 값을 함께 쓰는 까닭이 이것이다.

### (2) 다섯 가지 모양

**언제 쓰나** — 선의 뜻을 모양으로 구별하고 싶을 때.

```text
입력 값      그려지는 선
solid    →  실선 한 줄 (기본값)
double   →  나란한 두 줄
dotted   →  점이 이어진 선
dashed   →  짧은 선분이 이어진 선
wavy     →  물결처럼 오르내리는 선
```

- 값을 쓰지 않으면 기본값 `solid` 가 쓰인다.
- `dotted` 는 점, `dashed` 는 짧은 선분이다 — 둘을 헷갈리기 쉽다.
- `wavy` 는 원본 팁대로 맞춤법 오류 표시에 자주 쓰인다.
- 점의 간격 · 물결의 높이 같은 세부 모양은 이 속성으로 정하지 않는다(「구현 세부사항 대 언어 보장」 참고).

### (3) 단축 속성 `text-decoration` 안에서 정하기

**언제 쓰나** — 선 종류와 모양을 한 줄로 함께 정할 때.

```text
입력                                       일어나는 일                       결과
text-decoration: underline double;    →   선 종류 = underline             →  이중 밑줄
                                           모양    = double
text-decoration: underline;           →   선 종류 = underline             →  실선 밑줄
                                           모양    = 적지 않음 → solid 로 되돌림
```

- 원본 팁대로 모양은 단축 속성 `text-decoration` 에서도 정할 수 있다.
- 단축 속성은 적지 않은 하위 값을 기본값으로 되돌린다.
- 그래서 단축 속성에 모양을 빼고 쓰면 앞서 따로 정한 모양이 `solid` 로 덮인다.

> **단축 속성(shorthand property)** — 여러 하위 속성을 한 줄에 함께 정하는 속성.\
> 예: `text-decoration` 은 선 종류 · 모양 등을 한꺼번에 정한다.

### (4) 상속되지 않고, 애니메이션되지 않는다

**언제 쓰나** — 부모와 자식에 따로 장식선을 줄 때, 상태 변화에 전환 효과를 걸 때.

```text
부모: text-decoration-style: double;   (선 없음)
  └ 자식: text-decoration: underline;   →  자식의 모양 = solid (부모 값 물려받지 않음)

a       { text-decoration: underline solid; transition: all .3s; }
a:hover { text-decoration: underline wavy; }   →  사이 모양 없이 바로 바뀜
```

- 원본 데이터에 따르면 상속은 `False` 다 — 자식은 부모의 모양 값을 물려받지 않는다.
- 자식이 스스로 선을 정하고 모양을 정하지 않으면 기본값 `solid` 가 된다.
- 애니메이션 가능도 `False` 다 — 실선과 물결선 「사이」의 모양은 없으므로 상태가 바뀌면 단번에 바뀐다.

> **상속(inheritance)** — 자식 요소가 부모 요소의 속성 값을 그대로 이어받는 것.\
> 예: `color` 는 상속되어 부모의 글자색이 자식에게 이어진다.

## 문법 — 형태와 규칙

```html demo
<p style="text-decoration: underline solid;">solid 밑줄</p>
<p style="text-decoration: underline double;">double 밑줄</p>
<p style="text-decoration: underline dotted;">dotted 밑줄</p>
<p style="text-decoration: underline dashed;">dashed 밑줄</p>
<p style="text-decoration: underline wavy;">wavy 밑줄</p>
<p style="text-decoration-line: line-through; text-decoration-style: wavy;">따로 쓴 wavy 가운데 줄</p>
```

> **보이는 것** — 다섯 단락에 각각 실선 · 이중선 · 점선 · 파선 · 물결선 밑줄이, 마지막 단락에 물결 모양 가운데 줄이 그어진다 (코드에서 읽은 것 — 렌더 실측 아님)

- 꼴: `text-decoration-style: solid | double | dotted | dashed | wavy`
- 값은 다섯 키워드 중 하나만 쓴다.
- 기본값은 `solid` 다.
- 선 종류(`underline` · `overline` · `line-through`)가 함께 정해져야 보인다.
- 단축 속성 `text-decoration` 에 선 종류와 함께 적을 수 있다.

| 값 | 뜻 | 쓰임새 예 |
|---|---|---|
| `solid` | 실선 (기본값) | 평범한 링크 밑줄 |
| `double` | 이중선 | 강하게 짚는 강조 |
| `dotted` | 점선 | 약어 · 용어 풀이가 있음을 알리는 밑줄 |
| `dashed` | 파선 | 보조 표시 · 임시 표시 |
| `wavy` | 물결선 | 맞춤법 오류 표시 |

## 어디서 틀리나

### 1. 모양만 쓰고 선 종류를 빠뜨린다

`text-decoration-style: wavy;` 만 쓰면 아무 선도 보이지 않는다.
모양은 이미 있는 선에만 입혀지기 때문이다.
`underline` 같은 선 종류를 단축 속성이나 `text-decoration-line` 으로 함께 정한다.

### 2. 단축 속성이 앞서 정한 모양을 덮는다

`text-decoration-style: dotted;` 뒤에 `text-decoration: underline;` 을 쓰면 모양이 `solid` 로 돌아간다.
단축 속성은 적지 않은 하위 값을 기본값으로 되돌리기 때문이다.
모양을 따로 정하려면 단축 속성보다 뒤에 쓰거나, 단축 속성 안에 모양까지 적는다.

### 3. `wavy` 를 맞춤법 오류가 아닌 곳에 남발한다

원본 팁대로 `wavy` 는 맞춤법 오류 표시에 자주 쓰인다.
사용자는 물결 밑줄을 「틀린 글자」로 읽기 쉬우므로, 평범한 강조에 쓰면 뜻이 헷갈린다.

### 4. `dotted` 와 `dashed` 를 바꿔 쓴다

`dotted` 는 점, `dashed` 는 짧은 선분이다.
이름의 뜻(dot = 점, dash = 짧은 줄표)으로 외운다.

### 5. 모양 바꾸기에 전환 효과를 기대한다

이 속성은 애니메이션 가능이 `False` 다.
`transition` 을 걸어도 모양은 서서히 변하지 않고 단번에 바뀐다.

### 6. 부모의 모양이 자식에게 이어진다고 여긴다

상속이 `False` 이므로 부모에 정한 모양 값은 자식의 값이 되지 않는다.
자식이 스스로 선을 그으면 자식의 모양은 자식이 정한 값, 없으면 `solid` 다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 값은 `solid` · `double` · `dotted` · `dashed` · `wavy`, 기본값은 `solid` | CSS 명세 (원본 데이터와 일치) |
| 단축 속성은 적지 않은 하위 값을 기본값으로 되돌린다 | CSS 명세의 단축 속성 규칙 |
| 점의 간격 · 선분 길이 · 물결의 높이와 주기 | 브라우저 구현 — 명세가 세부 모양을 정하지 않는다 (확인 필요) |
| `wavy` 가 맞춤법 오류 표시에 자주 쓰인다 | 관례 — 언어 보장이 아니다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 맞춤법 · 입력 오류 표시 | `underline wavy` | 평범한 실선 밑줄(링크와 헷갈림) |
| 용어 풀이가 달린 낱말 표시 | `underline dotted` | `wavy`(오류로 읽힘) |
| 링크 밑줄 | 기본값 `solid` | 굳이 모양 바꾸기 |
| 마우스를 올리면 모양이 바뀌는 효과 | 모양을 바로 바꾸기 | 모양에 `transition` 기대하기 |
| 선 종류와 모양을 함께 정할 때 | `text-decoration: underline double;` | 모양만 따로 쓰고 선을 빠뜨리기 |

## 핵심 문장

1. **`text-decoration-style` 은 선의 모양만 정한다** — 선 자체는 선 종류가 정해야 생긴다.
2. **값은 다섯 개, 기본값은 `solid`** — `double` 두 줄 · `dotted` 점 · `dashed` 짧은 선분 · `wavy` 물결.
3. **단축 속성 `text-decoration` 으로도 정한다** — 빼고 쓰면 모양은 `solid` 로 되돌아간다.
4. **상속도 애니메이션도 되지 않는다.**
5. **`wavy` 는 맞춤법 오류 표시의 관례다.**

## 관련 자료

- `text-decoration` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `text-decoration-line` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `text-decoration-color` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/css/typography.json` 의 `text-decoration-style`

## 용어 풀이

- **장식선** — 글자에 덧그리는 밑줄 · 윗줄 · 가운데 줄.
- **선 종류** — `underline` · `overline` · `line-through` 처럼 어디에 선을 그을지 정하는 값.
- **모양(스타일)** — 선을 실선 · 이중선 · 점선 · 파선 · 물결선 중 무엇으로 그릴지.
- **단축 속성** — 여러 하위 속성을 한 줄에 함께 정하는 속성.
- **기본값(초기값)** — 아무 값도 정하지 않았을 때 쓰이는 값.
- **상속** — 자식 요소가 부모 요소의 값을 이어받는 것.
- **애니메이션 가능** — 두 값 사이를 서서히 바꿀 수 있는지 여부.

## 더 들어가면

- 상속은 되지 않지만, 부모에 그은 장식선은 그 안의 글자 위로 그대로 이어져 그려진다 — 자식이 부모의 선을 지우지는 못한다 (확인 필요).
- 하나의 요소에 `underline overline` 처럼 선을 여럿 그으면, 모양 값 하나가 그 선 모두에 적용된다 (확인 필요).
- 선의 두께는 `text-decoration-thickness`, 색은 `text-decoration-color` 로 따로 정한다 (확인 필요).
- 밑줄과 글자 사이 거리는 `text-underline-offset` 으로 조정한다 (확인 필요).
- 브라우저가 맞춤법 검사로 그리는 빨간 물결선은 페이지의 CSS 가 아니라 브라우저가 따로 그린다 (확인 필요).

# css/typography/45 — initial-letter — 정리 (힌트)

> 출처 — study-site 항목 `css/initial-letter`(항목 데이터 `data/css/typography.json`) · 정답 코드 study-practice `css/typography/reference/initial-letter.html`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

## 한눈에 — 쉽게 말하면

**`initial-letter` 는 「옛 동화책의 첫 장에 크게 그려 넣은 첫 글자」다.**
그림 글자는 본문 몇 줄 높이만큼 크고, 본문 글줄은 그 글자를 피해 오른쪽으로 비켜 흐른다.
CSS 의 드롭캡도 똑같은 구조다.
`initial-letter` 는 첫 글자에게 「본문 몇 줄 크기로 그려지고, 몇 줄만큼 아래로 가라앉아라」를 정한다.

> **드롭캡** — 단락의 첫 글자를 여러 줄 높이로 크게 키워 본문 안으로 내려앉힌 꾸밈.\
> 예: 잡지 기사 첫 단락의 큰 「L」 옆으로 본문 세 줄이 비켜 흐르는 모양.

| 비유 | 실체 |
|---|---|
| 그림으로 그린 큰 첫 글자 | `::first-letter` 로 고른 첫 글자 |
| 「본문 3줄 높이로 그려라」 | `initial-letter: 3` 의 크기(줄 수) |
| 글자가 본문 안으로 내려앉은 깊이 | 싱크(가라앉을 줄 수) |
| 그림을 피해 흐르는 본문 | 첫 글자 오른쪽으로 비켜 흐르는 글줄 |

```text
┌──┐ orem ipsum dolor sit amet,     ← 1줄
│L │ consectetur adipiscing elit.   ← 2줄
└──┘ Sed do eiusmod tempor incid-   ← 3줄
idunt ut labore et dolore magna     ← 4줄부터 왼쪽 끝까지
```

## 이 주제가 답하려는 질문

1. 첫 글자 하나만 몇 줄 높이로 키우려면 어디에 무엇을 적나?
2. 숫자 하나(`3`)와 숫자 둘(`3 2`)은 무엇이 다른가?
3. 첫 글자의 크기는 무엇이 정하나 — `font-size` 인가, 본문의 줄인가?
4. 이 속성이 통하지 않는 곳(상속 · 애니메이션 · 미지원 브라우저)은 어디인가?

## 동작 방식

### (1) `::first-letter` 에 숫자 하나 — 크기 정하기

**언제 쓰나** 단락 첫 글자를 본문 몇 줄 높이의 드롭캡으로 만들 때 쓴다.

```text
.dropcap::first-letter { initial-letter: 3; }
        │
        ▼
① ::first-letter 가 단락의 첫 글자 「L」만 고른다
② initial-letter: 3 → L 의 크기를 「본문 3줄 높이」로 맞춘다
③ 본문 첫 3줄은 L 오른쪽으로 비켜 흐른다
        │
        ▼
결과: 3줄 높이의 L + 그 옆 3줄, 4줄부터는 왼쪽 끝부터
```

① `initial-letter` 는 의사 요소 `::first-letter` 에 적용하는 속성이다.
② `<number>` 는 첫 글자가 차지할 줄 수이고, 이 줄 수가 곧 글자 크기를 정한다.
③ 정답 코드의 주석도 「첫 글자가 3줄 높이로 확장됨」이라고 적는다.

> **의사 요소** — HTML 에 따로 태그가 없는 문서의 한 부분을 CSS 가 요소처럼 골라 꾸미게 해 주는 선택자.\
> 예: `p::first-letter` 는 단락의 첫 글자만 고른다.

### (2) 숫자 둘 — 크기와 싱크를 따로

**언제 쓰나** 큰 글자를 본문 안으로 덜 가라앉히고 위로 솟게 하고 싶을 때 쓴다.

```text
initial-letter: 3 2;
        │
        ▼
① 크기 = 3줄 높이
② 싱크 = 2줄만 본문 안으로 가라앉음
③ 남는 1줄 높이만큼은 첫 줄 위로 솟는다
        │
        ▼
결과: 위로 삐져나온 큰 글자 + 그 옆으로 본문 2줄
```

① 첫 숫자 `<number>` 는 크기(줄 수)다.
② 둘째 숫자 `<integer>` 는 싱크, 곧 글자가 가라앉을 줄 수다.
③ 크기가 싱크보다 크면 그 차이만큼 글자가 첫 줄 위로 올라간다고 읽을 수 있다(원본에 근거 없음 — 추론).

> **싱크** — 큰 첫 글자가 본문 줄 안으로 내려앉는 깊이를 줄 수로 센 값.\
> 예: `initial-letter: 3 2` 의 `2`.

### (3) 크기의 기준은 본문의 줄

**언제 쓰나** 드롭캡 크기를 바꾸고 싶을 때 무엇을 건드려야 하는지 알 때 쓴다.

```text
.dropcap { font-size: 16px; line-height: 1.6; }
        │
        ▼
① 본문 한 줄의 높이 = 글자 크기 × line-height
② 「3줄 높이」 = 그 줄 높이 3개
③ line-height 를 키우면 한 줄이 높아지고, 3줄도 높아진다
        │
        ▼
결과: 드롭캡 크기는 font-size 가 아니라 줄 수와 줄 높이로 정해진다
```

① 정답 코드의 `line-height` 주석은 「드롭캡 줄 수와 함께 동작」이라고 적는다.
② `initial-letter` 의 값은 픽셀이 아니라 줄 수다.
③ 그래서 첫 글자에 `font-size` 를 따로 주지 않아도 크기가 맞춰진다.

```html demo
<p class="dropcap">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
<style>
  .dropcap { font-size: 16px; line-height: 1.6; max-width: 320px; }
  .dropcap::first-letter { initial-letter: 3; font-weight: bold; }
</style>
```

> **보이는 것** — 첫 글자 L 이 본문 3줄 높이로 커지고 본문 첫 3줄이 그 오른쪽으로 비켜 흐른다 (코드에서 읽은 것 — 렌더 실측 아님).

## 문법 — 형태와 규칙

```css
p::first-letter {
  initial-letter: 3;        /* 크기 3줄 */
}
p.raised::first-letter {
  initial-letter: 3 2;      /* 크기 3줄, 싱크 2줄 */
}
p.plain::first-letter {
  initial-letter: normal;   /* 드롭캡 없음 */
}
```

| 값 | 뜻 |
|---|---|
| `normal` | 일반 표시, 드롭캡 없음 (기본값) |
| `<number>` | 첫 글자가 차지할 줄 수 — 크기를 정한다 |
| `<number> <integer>` | 크기(줄 수)와 싱크(가라앉을 줄 수) |

- 문법: `initial-letter: normal | <number> [<integer>]`.
- 기본값은 `normal` 이다.
- 상속되지 않는다.
- 애니메이션할 수 없다.
- 적용 대상은 `::first-letter` 의사 요소다.
- 굵기 · 색 · 여백 같은 꾸밈은 같은 `::first-letter` 규칙에 함께 적는다(정답 코드의 `font-weight` · `color` · `margin-right`).

## 어디서 틀리나

### 1. 단락 자체에 적는다
`initial-letter` 는 `::first-letter` 에 적용하는 속성이다.
상속도 되지 않으므로, `p` 에 적어 두면 첫 글자 의사 요소가 그 값을 물려받지 않는다.
드롭캡은 생기지 않는다.

### 2. 크기를 `font-size` 로 맞추려 한다
크기는 줄 수가 정한다.
드롭캡을 키우거나 줄이려면 숫자(줄 수)나 본문 `line-height` 를 바꾼다.

### 3. 부드럽게 커지는 효과를 기대한다
애니메이션할 수 없는 속성이라 `transition` 을 걸어도 `normal` 과 `3` 사이 중간 단계가 없다.
값이 바뀌는 순간 한 번에 바뀐다.

### 4. 모든 브라우저에서 된다고 믿는다
원본 팁은 「브라우저 지원 확인 필요」라고 적는다.
CSS 는 이해하지 못하는 선언을 버리고 나머지를 적용하므로, 지원하지 않는 곳에서는 `initial-letter` 만 빠진다.
같은 규칙의 굵기 · 색 · 여백은 그대로 남아 「굵고 색만 다른 보통 크기 첫 글자」가 된다.

### 5. 잡지 · 신문 꼴이 아닌 곳에 쓴다
원본 팁대로 쓰임새는 잡지 · 신문 스타일의 드롭캡이다.
짧은 문장이나 목록 항목에 걸면 본문이 3줄도 안 되어 모양이 어색해진다(원본에 근거 없음 — 추론).

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `initial-letter` 의 값 뜻(크기 · 싱크) | CSS 명세 |
| 기본값 `normal`, 상속 안 됨, 애니메이션 불가 | CSS 명세(원본 데이터) |
| 이해하지 못한 선언은 버리고 나머지를 적용 | CSS 명세의 오류 처리 규칙 |
| 이 속성을 실제로 그리는지 | 브라우저 엔진마다 다름 (확인 필요) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 기사 첫 단락에 큰 첫 글자 | `::first-letter { initial-letter: 3; }` | 첫 글자를 `<span>` 으로 감싸 손으로 `font-size` 맞추기 |
| 큰 글자를 위로 솟게 | `initial-letter: 3 2;` | 음수 여백으로 끌어올리기 |
| 드롭캡을 끄기 | `initial-letter: normal;` | 규칙을 남긴 채 색만 지우기 |
| 크기가 부드럽게 커지는 효과 | (이 속성으로는 불가) | `initial-letter` 에 `transition` |

## 핵심 문장

1. **`initial-letter` 는 `::first-letter` 에 적용해 첫 글자를 드롭캡으로 만든다.**
2. **값은 줄 수다** — 첫 숫자는 크기, 둘째 숫자는 싱크(가라앉을 줄 수)다.
3. **크기는 본문의 줄 높이를 따른다** — `font-size` 가 아니라 줄 수와 `line-height` 가 정한다.
4. **상속되지 않고 애니메이션되지 않는다.**
5. **브라우저 지원은 확인이 필요하고, 안 되면 이 선언만 빠진다.**

## 관련 자료

- `font-size` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `line-height` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/css/typography.json` 의 `initial-letter`
## 용어 풀이

- **드롭캡** — 첫 글자를 여러 줄 높이로 키워 본문 안으로 내려앉힌 꾸밈.
- **의사 요소** — 태그 없이 문서의 한 부분을 요소처럼 고르는 선택자(`::first-letter` 등).
- **`::first-letter`** — 블록의 첫 글자를 고르는 의사 요소.
- **싱크** — 큰 첫 글자가 본문 안으로 가라앉는 깊이를 줄 수로 센 값.
- **`line-height`** — 한 줄의 높이를 정하는 속성.
- **상속** — 부모에 준 값을 자식이 그대로 물려받는 것.

## 더 들어가면

- 둘째 숫자를 생략하면 싱크는 크기와 같은 줄 수로 잡힌다고 명세에 적혀 있다 (확인 필요).
- 명세 초안에는 둘째 자리에 `drop` · `raise` 같은 키워드도 있다 (확인 필요).
- 일부 브라우저는 접두사 붙은 `-webkit-initial-letter` 로만 지원한 시기가 있다 (확인 필요).
- 지원 여부에 따라 갈라 쓰려면 `@supports (initial-letter: 3)` 로 감싸고, 그 밖에서는 `float: left` 와 큰 `font-size` 로 흉내 내는 옛 방식을 쓰기도 한다 (확인 필요).
- `::first-letter` 말고 블록의 첫 인라인 자식에도 적용된다는 서술이 명세에 있다 (확인 필요).

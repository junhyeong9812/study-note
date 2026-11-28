# css/box-model/17 — padding-inline — 정리 (힌트)

> 출처 — study-site 항목 `css/padding-inline`(항목 데이터 `data/css/box-model.json`) · 정답 코드 study-practice `css/box-model/reference/padding-inline.html`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

## 한눈에 — 쉽게 말하면

**`padding-inline` 은 「글이 흘러가는 방향의 앞뒤 여백」이다.**
공책에 글을 쓸 때 줄의 시작 쪽과 끝 쪽에 비워 두는 여백을 떠올리면 된다.
가로로 쓰는 공책이면 그 여백은 왼쪽과 오른쪽이다.
세로로 쓰는 원고지라면 같은 「줄의 시작 · 끝」 여백이 위와 아래가 된다.
`padding-inline` 도 똑같은 구조다.
방향을 「왼쪽 · 오른쪽」으로 정하지 않고 「글이 흐르는 방향의 시작 · 끝」으로 정한다.

| 비유 | 실체 |
|---|---|
| 공책 한 줄 | 인라인 축(글자가 이어지는 방향) |
| 줄 시작 쪽 여백 | `padding-inline-start` |
| 줄 끝 쪽 여백 | `padding-inline-end` |
| 가로 공책 / 세로 원고지 | `writing-mode` 값 |

```text
가로 쓰기(horizontal-tb)

         ┌──────────────────────────┐
  start  │ ←40→  padding-inline ←40→│  end
 (왼쪽)  └──────────────────────────┘ (오른쪽)
           글자가 흐르는 방향 ──────▶
```

## 이 주제가 답하려는 질문

1. 인라인 방향 양쪽의 안쪽 여백을 한 줄로 어떻게 주나?
2. 값을 1개 줄 때와 2개 줄 때는 무엇이 다른가?
3. `writing-mode` 가 바뀌면 이 여백은 실제로 어느 쪽에 붙나?
4. 어떤 값을 쓸 수 있고, 퍼센트는 무엇을 기준으로 계산하나?

## 동작 방식

### (1) 값 하나 — 인라인 축 양쪽에 같은 여백

**언제 쓰나** — 버튼 · 배지처럼 글자 양옆 여백을 똑같이 줄 때 쓴다.

```text
입력:  .box { padding-inline: 40px; }
         │
         ▼
풀이:  padding-inline-start: 40px
       padding-inline-end:   40px
         │
         ▼
가로 쓰기에서:  padding-left 40px + padding-right 40px
```

- 값이 하나면 시작 쪽과 끝 쪽에 같은 값이 들어간다.
- `padding-inline` 은 두 개별 속성을 한꺼번에 정하는 단축 속성이다.
- 가로 쓰기(`horizontal-tb`)에서는 결과가 왼쪽 · 오른쪽 패딩과 같다.

> **단축 속성** — 여러 개별 속성을 한 줄로 함께 정하는 속성.\
> 예: `padding-inline` 하나가 `padding-inline-start` 와 `padding-inline-end` 를 정한다.

### (2) 값 둘 — 시작과 끝을 따로

**언제 쓰나** — 아이콘이 붙은 쪽만 여백을 넓히는 식으로 양쪽을 다르게 줄 때 쓴다.

```text
입력:  .tag { padding-inline: 10px 30px; }
         │
         ▼
풀이:  첫째 값 10px → padding-inline-start
       둘째 값 30px → padding-inline-end
         │
         ▼
가로 쓰기(왼→오른)에서:  왼쪽 10px, 오른쪽 30px
```

- 값 순서는 늘 「start, end」다.
- 「왼쪽, 오른쪽」 순서가 아니라 「글이 시작하는 쪽, 끝나는 쪽」 순서다.
- 가로 쓰기에서 글이 왼쪽에서 시작하므로 첫째 값이 왼쪽에 붙는다.

### (3) `writing-mode` 가 매핑을 바꾼다

**언제 쓰나** — 세로 쓰기 레이아웃처럼 글의 흐름이 바뀌는 화면에서 여백이 글을 따라가게 할 때 쓴다.

```text
입력:  .v { writing-mode: vertical-rl; padding-inline: 20px; }
         │
         ▼
인라인 축이 세로가 된다 (글자가 위→아래로 흐른다)
         │
         ▼
결과:  위 20px, 아래 20px  (왼쪽 · 오른쪽에는 붙지 않는다)
```

- `writing-mode` 는 글이 흐르는 축을 정한다.
- 세로 쓰기에서는 인라인 축이 세로이므로 `padding-inline` 이 위 · 아래 여백이 된다.
- 코드는 그대로인데 붙는 쪽이 바뀐다 — 이것이 「논리적」 속성이라는 뜻이다.

> **논리적 속성** — 물리 방향(위 · 아래 · 왼 · 오른) 대신 글의 흐름(인라인 · 블록, 시작 · 끝)으로 방향을 정하는 속성.\
> 예: `padding-inline` 은 논리적, `padding-left` 는 물리적이다.

### (4) 블록 축의 짝 `padding-block`

**언제 쓰나** — 인라인 축과 블록 축 여백을 둘 다 논리적으로 줄 때 짝으로 쓴다.

```text
.box { padding-inline: 40px; padding-block: 16px; }

           ↑ 16px (block-start)
     ┌──────────────────────┐
40px │      내용 영역        │ 40px
     └──────────────────────┘
           ↓ 16px (block-end)
```

- `padding-block` 은 블록 축(줄이 쌓이는 방향) 양쪽 여백이다.
- 가로 쓰기에서 `padding-block` 은 위 · 아래, `padding-inline` 은 왼 · 오른이다.
- 둘을 함께 쓰면 네 면을 모두 논리적으로 정한다.

### (5) 여백을 눈으로 보이게 하는 `display: inline-block`

**언제 쓰나** — 예제처럼 패딩의 크기를 박스 크기로 바로 확인하고 싶을 때 쓴다.

- `div` 는 기본으로 블록 요소라 줄 전체 폭을 차지한다.
- 그러면 오른쪽 끝 여백이 화면 끝까지 늘어난 배경에 묻혀 패딩이 잘 드러나지 않는다.
- `display: inline-block` 이면 박스가 내용 폭 + 패딩만큼만 차지한다.
- 그래서 원본 예제는 패딩 효과를 보이려고 `inline-block` 을 쓴다.

```html demo
<div style="padding-inline: 40px; padding-block: 16px; background: #3b82f6; color: white; border-radius: 4px; display: inline-block;">padding-inline</div>
```

> **보이는 것** — 파란 박스 안에서 글자 양옆에 40px, 위아래에 16px 여백이 생기고 박스는 글자 폭에 맞게 줄어든다 (코드에서 읽은 것 — 렌더 실측 아님)

## 문법 — 형태와 규칙

```css
/* 값 1개: 시작 · 끝 모두 같은 값 */
.a { padding-inline: 40px; }

/* 값 2개: start, end 순서 */
.b { padding-inline: 10px 30px; }

/* 퍼센트: 포함 블록 인라인 크기 기준 */
.c { padding-inline: 5%; }

/* 블록 축 짝과 함께 */
.d { padding-inline: 40px; padding-block: 16px; }

/* 세로 쓰기: 위 · 아래에 붙는다 */
.e { writing-mode: vertical-rl; padding-inline: 20px; }
```

| 값 | 뜻 | 제약 |
|---|---|---|
| `<length>` | 고정 단위 값(`px` · `em` · `rem` 등) | 음수 불가 |
| `<percentage>` | 포함 블록 인라인 크기의 백분율 | 음수 불가 |

- 기본값은 `0` 이다.
- 상속되지 않는다 — 부모에 준 `padding-inline` 이 자식의 패딩이 되지 않는다.
- 애니메이션 가능하다 — `transition` 으로 값 변화를 부드럽게 보일 수 있다.
- 값은 1~2개다 — 1개는 양쪽 같음, 2개는 start / end 따로.

> **포함 블록** — 요소의 크기 · 위치를 계산할 때 기준이 되는 바깥 상자(보통 부모의 내용 영역).\
> 예: 폭 400px 부모 안의 자식에 `padding-inline: 5%` 면 양쪽 각 20px 이다.

## 어디서 틀리나

### 1. `writing-mode` 에 따라 매핑 방향이 달라진다

`padding-inline` 을 「좌우 패딩」으로 외우면 세로 쓰기에서 틀린다.
세로 쓰기에서는 위 · 아래 여백이다.
「좌우」는 가로 쓰기일 때만 맞는 말이다.

### 2. 두 값의 순서는 「왼, 오른」이 아니라 「start, end」다

가로 쓰기에서는 우연히 결과가 같다.
하지만 쓰기 방향이 바뀌면 첫째 값이 붙는 쪽도 바뀐다.

### 3. 값은 최대 2개다

`padding` 처럼 3~4개를 쓰면 안 된다.
`padding-inline: 10px 20px 30px;` 은 잘못된 선언이라 무시된다.

### 4. 음수는 쓸 수 없다

`<length>` · `<percentage>` 둘 다 음수 불가다.
음수를 쓰면 그 선언은 무효가 된다.
안쪽으로 당기고 싶다면 패딩이 아니라 여백(`margin`)의 일이다.

### 5. 퍼센트 기준은 자기 크기가 아니다

퍼센트는 요소 자신의 폭이 아니라 포함 블록의 인라인 크기를 기준으로 한다.
부모가 넓어지면 자식의 패딩도 커진다.

### 6. 블록 요소에서는 여백이 잘 안 보일 수 있다

`div` 처럼 줄 전체를 차지하는 박스에서는 끝 쪽 여백이 남는 공간에 섞여 구분되지 않는다.
여백을 눈으로 확인하려면 원본 예제처럼 `display: inline-block` 으로 박스를 내용 폭에 맞춘다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `padding-inline` 은 start · end 두 개별 속성의 단축이다 | CSS 명세(논리적 속성) |
| `writing-mode` 에 따라 붙는 물리 방향이 달라진다 | CSS 명세 |
| 기본값 `0` · 상속 안 됨 · 애니메이션 가능 | CSS 명세(속성 정의) |
| 브라우저별 지원 범위 · 지원 시작 버전 | 원본에 없음 (확인 필요) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 글자 양옆 여백을 같은 값으로 | `padding-inline: 값` | `padding-left` + `padding-right` 두 줄 |
| 여러 쓰기 방향을 지원하는 화면 | `padding-inline` · `padding-block` | 물리 방향 속성(`padding-left` 등) |
| 시작 쪽 · 끝 쪽을 다르게 | `padding-inline: 시작 끝` | 값 3~4개 |
| 언제나 화면의 왼쪽에만 고정 여백 | `padding-left` | `padding-inline-start` (쓰기 방향 따라 바뀜) |
| 안쪽으로 당기기(음수) | `margin` 쪽 기법 | 음수 `padding-inline` |

## 핵심 문장

1. **`padding-inline` 은 인라인 축의 시작 · 끝 패딩을 한 줄로 정하는 논리적 단축 속성이다.**
2. **값 1개는 양쪽 같음, 값 2개는 start · end 순서다.**
3. **붙는 물리 방향은 `writing-mode` 가 정한다** — 가로 쓰기에서는 좌우, 세로 쓰기에서는 위아래다.
4. **음수는 안 되고, 퍼센트는 포함 블록의 인라인 크기 기준이다.**
5. **짝은 `padding-block` 이다** — 둘이 함께 네 면을 덮는다.

## 관련 자료

- `padding-inline-start` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `padding-inline-end` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [padding-block](../20-padding-block/2-summary.md)
- `padding` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/css/box-model.json` 의 `padding-inline`

## 용어 풀이

- **인라인 축** — 한 줄 안에서 글자가 이어지는 방향. 가로 쓰기에서는 가로.
- **블록 축** — 줄이 쌓여 내려가는 방향. 가로 쓰기에서는 세로.
- **start / end** — 축 위에서 글이 시작하는 쪽과 끝나는 쪽.
- **논리적 속성** — 글의 흐름을 기준으로 방향을 정하는 속성.
- **물리적 속성** — 위 · 아래 · 왼 · 오른 같은 화면 방향으로 정하는 속성.
- **단축 속성** — 여러 개별 속성을 한 줄로 정하는 속성.
- **`writing-mode`** — 글이 흐르는 축을 정하는 속성(`horizontal-tb` · `vertical-rl` 등).
- **포함 블록** — 크기 · 위치 계산의 기준이 되는 바깥 상자.
- **`inline-block`** — 줄 안에 놓이면서 블록처럼 폭 · 패딩을 갖는 표시 방식.

## 더 들어가면

- 같은 가로 쓰기라도 `direction: rtl`(오른쪽에서 왼쪽으로 쓰는 언어)이면 start 가 오른쪽이 된다 (확인 필요).
- CSS 에서 패딩 퍼센트는 `padding-block` 을 포함해 네 면 모두 포함 블록의 인라인 크기를 기준으로 한다고 알려져 있다 (확인 필요).
- 순수 인라인 요소(`span` 등)에서는 인라인 축 패딩은 옆 글자를 밀어내지만 블록 축 패딩은 줄 높이에 영향을 주지 않는다 (확인 필요).
- `padding-inline-start` · `padding-inline-end` 를 개별로 쓰면 한쪽만 바꿀 수 있다.

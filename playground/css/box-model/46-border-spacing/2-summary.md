# css/box-model/46 — border-spacing — 정리 (힌트)

> 출처 — study-site 항목 `css/border-spacing`(항목 데이터 `data/css/box-model.json`) · 정답 코드 study-practice `css/box-model/reference/border-spacing.html`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

## 한눈에 — 쉽게 말하면

**`border-spacing` 은 「달걀판의 칸 사이 벽 두께」다.**
달걀판은 칸마다 달걀이 따로 들어 있고, 칸과 칸 사이에 벽이 있다.
판의 맨 가장자리에도 벽이 둘러 있어서 바깥 줄의 달걀도 판 끝에 바로 닿지 않는다.
테이블도 똑같은 구조다.
셀은 저마다 자기 테두리를 두르고, 셀과 셀 사이, 그리고 셀과 테이블 바깥 가장자리 사이에 `border-spacing` 만큼의 틈이 생긴다.

| 비유 | 실체 |
|---|---|
| 달걀판 | `<table>` |
| 달걀 한 칸 | 셀(`<th>` · `<td>`) |
| 칸 사이 벽 두께 | `border-spacing` 값 |
| 판 가장자리의 벽 | 테이블 바깥 가장자리에도 생기는 간격 |
| 칸 벽을 없애고 달걀을 맞붙인 판 | `border-collapse: collapse` (간격이 무시된다) |

```text
 ┌──────────────────────────┐  ← 테이블 가장자리
 │ sp  ┌────┐ sp ┌────┐ sp  │
 │     │ A  │    │ B  │     │
 │     └────┘    └────┘     │
 │ sp                       │   sp = border-spacing
 │     ┌────┐    ┌────┐     │
 │     │ 1  │    │ 2  │     │
 │     └────┘    └────┘     │
 │ sp                       │
 └──────────────────────────┘
```

## 이 주제가 답하려는 질문

1. 테이블 셀과 셀 사이의 간격은 무엇으로 정하나?
2. 값을 하나 줄 때와 둘 줄 때는 어떻게 다른가?
3. 이 간격은 셀 사이에만 생기나, 바깥 가장자리에도 생기나?
4. 어떤 조건에서 이 속성이 아예 무시되나?

## 동작 방식

### (1) 셀 사이와 바깥 가장자리에 간격 넣기

**언제 쓰나** — 셀마다 테두리를 따로 그리고, 그 테두리끼리 떨어뜨려 놓고 싶을 때 쓴다.

```text
입력 코드                         무엇이 일어나나                       결과
.table {                         셀 테두리를 분리 모드로 둔다          셀마다 자기 테두리
  border-collapse: separate; ─▶  가로 방향: 셀 사이 + 양 끝 가장자리 ─▶ 셀 사이 8px
  border-spacing: 8px;           세로 방향: 행 사이 + 위아래 가장자리   표 가장자리와 셀 사이도 8px
}
```

- `border-collapse: separate` 는 셀 테두리를 서로 합치지 않고 셀마다 따로 그리게 한다.
- `border-spacing: 8px` 는 그렇게 분리된 셀들 사이에 8px 틈을 만든다.
- 틈은 셀과 셀 사이뿐 아니라 맨 바깥 셀과 테이블 가장자리 사이에도 들어간다.
- 그래서 열이 2개면 가로 방향 틈은 3군데(왼쪽 끝 · 가운데 · 오른쪽 끝), 행이 3개면 세로 방향 틈은 4군데다.

> **border-collapse** — 테이블 셀의 테두리를 합칠지(`collapse`) 따로 둘지(`separate`) 정하는 속성.\
> 예: `border-collapse: collapse;` 면 이웃 셀의 테두리가 한 줄로 합쳐진다.

> **셀** — 테이블의 칸 하나. 머리 셀은 `<th>`, 데이터 셀은 `<td>` 로 쓴다.\
> 예: `<td>1</td>` 는 「1」이 든 데이터 셀이다.

```html demo
<table style="border-collapse: separate; border-spacing: 8px; background: #f3f4f6;">
  <tr><td style="border: 2px solid #3b82f6; padding: 8px;">1</td><td style="border: 2px solid #3b82f6; padding: 8px;">2</td></tr>
  <tr><td style="border: 2px solid #3b82f6; padding: 8px;">3</td><td style="border: 2px solid #3b82f6; padding: 8px;">4</td></tr>
</table>
```

> **보이는 것** — 파란 테두리 상자 4개가 서로 떨어져 있고, 상자 사이와 표 가장자리 쪽에 회색 배경이 띠처럼 드러난다 (코드에서 읽은 것 — 렌더 실측 아님)

### (2) 값 두 개로 가로와 세로를 따로 정하기

**언제 쓰나** — 열 사이 간격과 행 사이 간격을 다르게 하고 싶을 때 쓴다.

```text
입력 코드                       무엇이 일어나나                   결과
border-spacing: 4px 12px; ─▶   첫째 값 → 가로(수평) 간격    ─▶   열 사이 좁게 4px
                               둘째 값 → 세로(수직) 간격         행 사이 넓게 12px
```

- 값이 하나면 가로와 세로에 같은 값이 쓰인다.
- 값이 둘이면 첫째가 가로(열 사이), 둘째가 세로(행 사이)다.
- 문법이 `<length>{1,2}` 라서 값은 하나 또는 둘만 쓸 수 있다.

### (3) collapse 일 때는 무시된다

**언제 쓰나** — 간격이 「왜 안 생기지?」 싶을 때 가장 먼저 확인할 자리다.

```text
입력 코드                         무엇이 일어나나                    결과
.table {                         테두리가 이웃 셀과 합쳐진다          셀 사이 간격 없음
  border-collapse: collapse; ─▶  합쳐진 테두리 사이엔 틈이 없다  ─▶  border-spacing 값은
  border-spacing: 20px;          → border-spacing 이 쓰일 자리 없음  아무 효과가 없다
}
```

- `collapse` 에서는 이웃 셀이 테두리 한 줄을 함께 쓰므로 둘 사이를 벌릴 틈 자체가 없다.
- 그래서 `border-spacing` 은 에러 없이 조용히 무시된다.
- `border-collapse` 의 기본값은 `separate` 이므로, 따로 `collapse` 를 주지 않았다면 `border-spacing` 은 그대로 동작한다.

## 문법 — 형태와 규칙

```css
/* 값 하나: 가로·세로 모두 8px */
.t1 { border-collapse: separate; border-spacing: 8px; }

/* 값 둘: 가로 4px, 세로 12px */
.t2 { border-collapse: separate; border-spacing: 4px 12px; }

/* collapse 라서 아래 border-spacing 은 무시된다 */
.t3 { border-collapse: collapse; border-spacing: 20px; }
```

| 항목 | 내용 |
|---|---|
| 문법 | `border-spacing: <length>{1,2}` |
| `<length>` 1개 | 가로 · 세로 간격이 같다 |
| `<length>` 2개 | 첫째 = 가로(수평), 둘째 = 세로(수직) |
| 기본값 | `0` |
| 상속 | 된다 |
| 애니메이션 | 안 된다 (원본 데이터 기준) |
| 전제 조건 | `border-collapse: separate` 일 때만 적용 |

- 값은 길이(`px` · `em` 등)로 쓴다.
- 값을 셋 이상 쓰면 문법 `{1,2}` 를 벗어나 그 선언은 무효가 된다.
- 테이블(`<table>`)에 준다 — 간격은 테이블 안의 모든 셀(`th` · `td`)에 함께 적용된다.

> **상속** — 부모에 준 값을 자식 요소가 따로 지정하지 않아도 물려받는 성질.\
> 예: 상속되는 속성을 바깥 요소에 주면 그 안의 요소도 같은 계산값을 갖는다.

## 어디서 틀리나

### 1. `collapse` 상태에서 간격을 기대한다

`border-collapse: collapse` 를 준 테이블에 `border-spacing` 을 아무리 크게 줘도 효과가 없다.
경고도 나오지 않으므로, 간격이 안 보이면 먼저 `border-collapse` 값을 확인한다.

### 2. 간격이 셀 사이에만 생긴다고 착각한다

간격은 테이블 바깥 가장자리와 맨 바깥 셀 사이에도 들어간다.
그래서 표 전체 크기를 계산할 때 「셀 수 − 1」이 아니라 「셀 수 + 1」 군데의 간격을 더해야 한다.
`border-spacing` 하나로는 「셀 사이는 벌리고 가장자리는 붙이기」를 할 수 없다.

### 3. 값 두 개의 순서를 뒤집는다

`border-spacing: 4px 12px` 에서 첫째는 가로, 둘째는 세로다.
`margin` · `padding` 의 두 값(위아래, 좌우)과 순서가 반대라서 헷갈리기 쉽다.

### 4. `padding` 과 섞어 쓴다

`padding` 은 셀 **안쪽** 여백(테두리와 글자 사이)이고, `border-spacing` 은 셀 **바깥** 틈(셀 테두리와 이웃 셀 테두리 사이)이다.
셀 배경은 `padding` 영역까지 칠해지고, `border-spacing` 틈에는 셀 배경이 아니라 테이블 쪽 배경이 보인다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `collapse` 에서 `border-spacing` 이 무시된다 | CSS 명세(테이블 테두리 모델) |
| 간격이 바깥 가장자리에도 생긴다 | CSS 명세 |
| 기본값 `0` | CSS 명세의 초기값 — 브라우저 기본 스타일시트가 `table` 에 다른 값을 줄 수 있다 (확인 필요) |
| 애니메이션 불가 | 원본 데이터의 표기 — 명세의 애니메이션 유형은 확인 필요 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 셀을 카드처럼 떨어뜨려 보이고 싶다 | `separate` + `border-spacing` | `collapse` |
| 칸막이 선이 한 줄인 깔끔한 표 | `border-collapse: collapse` | `border-spacing` (무시된다) |
| 글자와 셀 테두리 사이를 넓히고 싶다 | 셀의 `padding` | `border-spacing` |
| 열 사이와 행 사이를 다르게 | `border-spacing` 값 2개 | 값 3개 이상 |

## 핵심 문장

1. **`border-spacing` 은 분리된 셀 테두리 사이의 틈이다** — `border-collapse: separate` 일 때만 쓰인다.
2. **틈은 바깥 가장자리에도 생긴다** — n 칸이면 그 방향의 틈은 n + 1 군데다.
3. **값 하나는 가로·세로 같게, 값 둘은 가로 먼저 세로 나중** 이다.
4. **`padding` 은 셀 안쪽, `border-spacing` 은 셀 바깥** 이다.

## 관련 자료

- `border-collapse` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/css/box-model.json` 의 `border-spacing`
## 용어 풀이

- **`border-spacing`** — 분리 모드 테이블에서 셀 사이(와 바깥 가장자리)의 간격.
- **`border-collapse`** — 셀 테두리를 합칠지(`collapse`) 분리할지(`separate`) 정하는 속성.
- **`separate`** — 셀마다 테두리를 따로 그리는 모드. `border-collapse` 의 기본값.
- **`collapse`** — 이웃 셀의 테두리를 한 줄로 합치는 모드.
- **셀** — 테이블의 칸. `<th>`(머리) · `<td>`(데이터).
- **`<length>`** — `px` · `em` 처럼 단위가 붙은 길이 값.
- **상속** — 부모의 값을 자식이 물려받는 성질.
- **`padding`** — 요소의 테두리 안쪽 여백.

## 더 들어가면

- 음수 길이는 `border-spacing` 에 쓸 수 없다고 알려져 있다 (확인 필요).
- 여러 브라우저의 기본 스타일시트가 `table` 에 `border-spacing: 2px` 정도를 준다는 말이 있다 — 그래서 아무것도 안 줬는데 셀 사이에 틈이 보일 수 있다 (확인 필요).
- 표 셀(`td`)은 `margin` 이 적용되지 않으므로 셀 사이 간격은 `border-spacing` 이 사실상 유일한 수단이다 (확인 필요).
- 상속되는 속성이라 바깥 테이블에 준 값이 안쪽에 중첩된 테이블에도 물려 내려갈 수 있다 (확인 필요).
- flex · grid 의 `gap` 은 아이템 사이에만 생기고 바깥 가장자리에는 생기지 않는다는 점에서 `border-spacing` 과 다르다 (확인 필요).

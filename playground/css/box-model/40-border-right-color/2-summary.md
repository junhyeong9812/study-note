# css/box-model/40 — border-right-color — 정리 (힌트)

> 출처 — study-site 항목 `css/border-right-color`(항목 데이터 `data/css/box-model.json`) · 정답 코드 study-practice `css/box-model/reference/border-right-color.html`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

## 한눈에 — 쉽게 말하면

**`border-right-color` 는 「액자 오른쪽 나무 틀에만 칠하는 페인트」다.**
액자 틀은 위 · 오른쪽 · 아래 · 왼쪽 네 조각이고, 이 페인트는 오른쪽 조각 하나에만 칠해진다.
페인트를 따로 고르지 않으면 틀은 그림 속 글씨와 같은 색으로 칠해진다.
그리고 나무 틀 자체(두께 · 모양)가 없으면 페인트를 골라도 칠할 곳이 없다.
CSS 테두리도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 액자 오른쪽 나무 틀 | 요소의 오른쪽 테두리 |
| 오른쪽 틀에 칠하는 페인트 | `border-right-color` 값 |
| 페인트를 안 고르면 글씨 색으로 칠함 | 기본값 `currentcolor` |
| 나무 틀의 두께 · 모양 | `border-right-width` · `border-right-style` |

```text
        위 테두리
   ┌─────────────────┐
   │                 ┃  ← 오른쪽 테두리
   │   내용(글자)     ┃     이 한 조각의 색만
   │                 ┃     border-right-color 가 정한다
   └─────────────────┘
        아래 테두리
```

## 이 주제가 답하려는 질문

1. 오른쪽 테두리 하나의 색만 따로 바꾸려면 무엇을 쓰나?
2. 색을 지정하지 않은 테두리는 무슨 색이 되나?
3. 단축 속성 `border-right` 와 함께 쓸 때 어느 쪽 색이 이기나?
4. 색을 지정했는데 테두리가 안 보이는 것은 왜인가?

## 동작 방식

### (1) 오른쪽 테두리 한 조각의 색만 정한다

**언제 쓍나** — 네 변 중 오른쪽만 다른 색으로 강조하고 싶을 때 쓴다.
다른 세 변의 색은 건드리지 않는다.

```text
입력:  .box { border: 4px solid; border-right-color: #ef4444; }

무엇이 일어나나:
  border 단축 → 네 변 모두 4px · solid · 색은 currentcolor
  border-right-color → 오른쪽 변의 색만 #ef4444 로 덮어씀

결과:
  위 · 아래 · 왼쪽 = 글자색      오른쪽 = 빨간색
```

- `border` 단축 속성이 네 변 모두에 두께 · 모양을 주고, 색은 생략했으니 기본값으로 둔다.
- 그다음 줄의 `border-right-color` 가 오른쪽 변의 색 하나만 바꾼다.
- 나머지 세 변은 여전히 기본값 색이다.

### (2) 기본값 `currentcolor` — 글자색을 따라간다

**언제 쓰나** — 테두리 색을 글자색과 맞추고 싶을 때는 아무것도 쓰지 않아도 된다.

```text
입력:  .box { color: navy; border-right: 4px solid; }

무엇이 일어나나:
  border-right-color 지정 없음 → 기본값 currentcolor
  currentcolor = 이 요소의 color 값 = navy

결과:
  오른쪽 테두리 = navy
  나중에 color 가 바뀌면 테두리 색도 같이 바뀜
```

- 색을 정하지 않으면 기본값 `currentcolor` 가 쓰인다.
- `currentcolor` 는 「그 요소의 현재 텍스트 색상」이다.
- 값이 고정된 색이 아니라 `color` 를 가리키므로, `color` 가 바뀌면 테두리 색도 따라 바뀐다.

> **currentcolor** — 그 요소의 `color`(텍스트 색상) 값을 가리키는 CSS 키워드.\
> 예: `color: green` 인 요소에서 `border-right-color: currentcolor` 는 초록 테두리가 된다.

### (3) 단축 속성과의 순서 — 뒤에 쓴 것이 이긴다

**언제 쓰나** — `border-right` 단축과 `border-right-color` 를 같은 규칙에 함께 쓸 때 순서를 정해야 한다.

```text
입력 A:  border-right: 4px solid;
         border-right-color: #ef4444;

  1줄: 두께 4px · solid · 색은 생략 → 색을 기본값(currentcolor)으로 둠
  2줄: 색만 #ef4444 로 덮어씀
  결과: 빨간 오른쪽 테두리

입력 B:  border-right-color: #ef4444;
         border-right: 4px solid;

  1줄: 색을 #ef4444 로 둠
  2줄: 단축 속성이 생략된 색까지 기본값으로 되돌림
  결과: 글자색(currentcolor) 오른쪽 테두리
```

- 단축 속성은 적지 않은 하위 값을 「안 건드림」이 아니라 「기본값으로 되돌림」으로 처리한다.
- 그래서 단축을 먼저 쓰고 색을 나중에 써야 색이 살아남는다.
- 원본 예제가 `border-right: 4px solid;` 다음 줄에 `border-right-color` 를 쓴 것이 이 순서다.

> **단축 속성** — 여러 하위 속성을 한 줄로 한꺼번에 정하는 속성.\
> 예: `border-right: 4px solid red` 는 오른쪽 테두리의 두께 · 모양 · 색을 한 번에 정한다.

### (4) 색만으로는 테두리가 생기지 않는다

**언제 쓰나** — 테두리가 안 보일 때 원인을 찾을 때 떠올린다.

```text
입력:  .box { border-right-color: #ef4444; }

무엇이 일어나나:
  색은 정해짐
  모양(border-right-style)은 지정 없음 → 기본값 none
  모양이 none 이면 그릴 테두리가 없음

결과:
  오른쪽 테두리가 보이지 않음
```

- `border-right-color` 는 이미 있는 테두리의 색만 정한다.
- 테두리를 그리려면 모양(`solid` 등)이 있어야 한다.
- 원본 예제가 `border-right: 4px solid` 로 두께와 모양을 먼저 준 까닭이다.

### (5) 상속되지 않고, 애니메이션된다

- 상속: 아니다.
  부모에 준 `border-right-color` 가 자식 테두리로 넘어가지 않는다.
- 애니메이션 가능: 그렇다.
  색 값이므로 `transition` 으로 한 색에서 다른 색으로 부드럽게 바뀔 수 있다.

## 문법 — 형태와 규칙

```html demo
<div class="box">border-right-color</div>
<style>
  .box {
    border-right: 4px solid;        /* 두께 · 모양. 색은 생략 */
    border-right-color: #ef4444;    /* 오른쪽 색만 빨간색 */
    padding: 16px;
    background: #f8fafc;
  }
</style>
```

> **보이는 것** — 옅은 회색 박스의 오른쪽에만 4px 빨간 세로줄이 있고, 다른 세 변에는 테두리가 없다 (코드에서 읽은 것 — 렌더 실측 아님)

```css
border-right-color: <color>;
```

| 값 | 뜻 |
|---|---|
| `<color>` | CSS 색상 값(`#ef4444` · `rgb(...)` · `red` 등) |
| `currentcolor` | 요소의 현재 텍스트 색상. 기본값 |

| 성질 | 값 |
|---|---|
| 기본값 | `currentcolor` |
| 상속 | 안 됨 |
| 애니메이션 | 가능 |

- 값은 색 하나만 받는다.
- 오른쪽 변 하나에만 적용된다.
- 같은 규칙 안에서 `border-right` · `border-color` · `border` 단축보다 뒤에 써야 덮이지 않는다.

> **하위 속성(롱핸드)** — 단축 속성이 묶고 있는 개별 속성.\
> 예: `border-right-color` 는 `border-right` 의 하위 속성이다.

## 어디서 틀리나

### 1. 기본값은 `currentcolor` 다

원본 팁 그대로다.
색을 정하지 않으면 테두리는 검정이 아니라 글자색이 된다.
글자색이 검정이라 검정 테두리로 보일 뿐이다.

### 2. 단축 속성을 뒤에 쓰면 색이 지워진다

`border-right-color` 다음에 `border-right: 4px solid` 를 쓰면, 단축 속성이 색을 기본값으로 되돌린다.
「색은 안 적었으니 그대로겠지」가 틀린 생각이다.

### 3. 모양 없이 색만 주면 아무것도 안 보인다

`border-right-style` 의 기본값이 `none` 이라, 색만 주면 그릴 테두리가 없다.

### 4. 부모 색을 자식이 물려받지 않는다

상속되지 않는 속성이다.
자식 테두리를 같은 색으로 하려면 자식에게도 지정한다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 기본값 `currentcolor` · 상속 안 됨 · 애니메이션 가능 | CSS 명세(원본 재료에 기재) |
| 단축 속성이 생략된 하위 값을 기본값으로 되돌림 | CSS 명세의 단축 속성 규칙 |
| `#ef4444` 가 화면에 보이는 정확한 빛깔 | 브라우저 · 화면 색 관리에 달림 (확인 필요) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 오른쪽 변 색만 바꾸기 | `border-right-color` | `border-color`(네 변 모두 바뀜) |
| 오른쪽 테두리를 처음부터 한 줄로 | `border-right: 4px solid #ef4444` | 색만 쓰는 `border-right-color` 단독 |
| 테두리를 글자색과 맞추기 | 아무것도 안 씀(기본값) 또는 `currentcolor` | 글자색을 복사한 고정 색 |
| 마우스 올릴 때 오른쪽 색만 바꾸기 | `border-right-color` + `transition` | 테두리 전체 단축을 다시 쓰기 |

## 핵심 문장

1. **`border-right-color` 는 오른쪽 테두리 한 변의 색만 정한다.**
2. **기본값은 `currentcolor` 라, 지정하지 않으면 글자색을 따라간다.**
3. **단축 속성은 생략한 색을 기본값으로 되돌리므로, 색 지정은 단축 뒤에 쓴다.**
4. **색은 테두리를 만들지 않는다 — 모양(`solid` 등)이 있어야 보인다.**
5. **상속되지 않고, 색끼리 애니메이션된다.**

## 관련 자료

- `border-color` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `border-right` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [border-right-style](../36-border-right-style/2-summary.md)
- 원본: study-site 항목 데이터 `data/css/box-model.json` 의 `border-right-color`

## 용어 풀이

- **테두리(border)** — 박스 모델에서 안쪽 여백(padding)과 바깥 여백(margin) 사이의 선.
- **`currentcolor`** — 그 요소의 `color` 값을 가리키는 키워드.
- **단축 속성** — 여러 하위 속성을 한 줄로 정하는 속성.
- **하위 속성(롱핸드)** — 단축 속성이 묶는 개별 속성.
- **상속** — 부모의 속성 값이 자식에게 저절로 넘어가는 것.
- **`transition`** — 속성 값이 바뀔 때 그 사이를 시간에 걸쳐 이어 주는 CSS 기능.
- **`border-right-style`** — 오른쪽 테두리의 모양(`solid` · `dashed` · `none` 등)을 정하는 속성.

## 더 들어가면

- 논리 속성 `border-inline-end-color` 는 글쓰기 방향에 따라 「줄의 끝 쪽」 테두리 색을 정한다 — 왼쪽에서 오른쪽으로 쓰는 문서에서는 오른쪽에 해당한다 (확인 필요).
- `transparent` 도 `<color>` 의 하나라 테두리 자리를 차지하되 보이지 않게 할 수 있다 (확인 필요).
- 테두리 색이 다른 두 변이 만나는 모서리는 대각선으로 나뉘어 그려진다 (확인 필요).

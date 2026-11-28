# css/box-model/41 — border-bottom-color — 정리 (힌트)

> 출처 — study-site 항목 `css/border-bottom-color`(항목 데이터 `data/css/box-model.json`) · 정답 코드 study-practice `css/box-model/reference/border-bottom-color.html`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

## 한눈에 — 쉽게 말하면

**`border-bottom-color` 는 「공책 밑줄에 쓰는 펜 색」이다.**
밑줄을 긋겠다고(두께와 선 모양) 정한 뒤, 그 밑줄만 다른 펜으로 칠한다.
펜을 따로 고르지 않으면 글씨를 쓰던 펜, 곧 지금 글자 색으로 긋는다.
CSS 박스의 아래쪽 테두리도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 공책의 한 줄 | 요소(박스) |
| 밑줄 | 아래쪽 테두리(`border-bottom`) |
| 밑줄 펜 색 | `border-bottom-color` 값 |
| 펜을 안 골랐을 때 쓰는 글씨 펜 | 기본값 `currentcolor`(요소의 글자 색) |

```text
┌───────────────────────┐
│  글자 (color)          │
│                       │   ← 위 · 왼 · 오른쪽 테두리: 영향 없음
└━━━━━━━━━━━━━━━━━━━━━━━┘   ← 아래쪽 테두리: border-bottom-color 로 칠함
```

## 이 주제가 답하려는 질문

1. 아래쪽 테두리의 색만 따로 바꾸려면 무엇을 쓰나?
2. 색을 지정하지 않으면 아래쪽 테두리는 무슨 색이 되나?
3. 단축 속성 `border-bottom` 과 함께 쓸 때 어떤 차례로 써야 하나?
4. 이 색은 부모에게서 물려받나, 그리고 부드럽게 바뀔 수 있나?

## 동작 방식

### (1) 아래쪽 테두리 하나만 칠한다

**언제 쓰나** — 네 변 가운데 아래쪽 선의 색만 다르게 하고 싶을 때 쓴다.

```text
입력:  .box { border: 2px solid; border-bottom-color: red; }
        │
        ├─ border       → 네 변 모두 2px 실선, 색은 미지정(currentcolor)
        └─ border-bottom-color → 아래쪽 변의 색만 red 로 덮음
        ▼
결과:  위 · 왼 · 오른쪽 = 글자 색 / 아래쪽 = red
```

- `border` 가 네 변에 두께 · 스타일을 주고, 색은 따로 적지 않았으니 글자 색이 된다.
- `border-bottom-color` 는 아래쪽 변의 색 하나만 바꾼다.
- 다른 세 변의 색은 그대로 남는다.

### (2) 색을 비워 두면 `currentcolor`

**언제 쓰나** — 테두리 색을 글자 색과 맞춰 두고, 글자 색만 바꿔서 둘을 함께 바꾸고 싶을 때 기대는 동작이다.

```text
입력:  .box { color: blue; border-bottom: 3px solid; }
        │
        ├─ border-bottom-color 를 어디에도 적지 않음
        ├─ 초깃값 currentcolor 가 쓰임
        └─ currentcolor = 이 요소의 color = blue
        ▼
결과:  아래쪽 테두리 = blue
```

- `border-bottom-color` 의 기본값은 `currentcolor` 다.
- `currentcolor` 는 「이 요소의 현재 텍스트 색」을 가리키는 키워드다.
- 그래서 `color` 가 blue 면 아래쪽 테두리도 blue 가 된다.

> **currentcolor** — 그 요소의 `color` 속성 값을 그대로 가리키는 CSS 색 키워드.\
> 예: `color: green` 인 요소에서 `border-bottom-color: currentcolor` 는 green 이다.

### (3) 단축 속성 뒤에 써야 남는다

**언제 쓰나** — 원본 예제처럼 `border-bottom` 으로 두께 · 스타일을 한 번에 주고 색만 따로 지정할 때 쓴다.

```text
입력 A:  border-bottom: 4px solid;          입력 B:  border-bottom-color: #ef4444;
         border-bottom-color: #ef4444;               border-bottom: 4px solid;
           │                                           │
           ├─ 단축이 색을 currentcolor 로 맞춤          ├─ 색을 #ef4444 로 맞춤
           └─ 뒤 줄이 색을 #ef4444 로 덮음              └─ 뒤 단축이 색을 currentcolor 로 되돌림
           ▼                                           ▼
결과 A:  빨간 아래 테두리                       결과 B:  글자 색 아래 테두리
```

- 단축 속성 `border-bottom` 은 두께 · 스타일 · 색을 한꺼번에 정한다.
- 단축 속성에서 색을 빼면, 색은 「안 건드림」이 아니라 초깃값 `currentcolor` 로 다시 맞춰진다.
- 같은 규칙 안에서는 뒤에 쓴 선언이 이기므로, 개별 속성 `border-bottom-color` 는 단축 속성 **뒤에** 써야 한다.
- 원본 정답 코드의 주석도 「색상은 미지정이라 currentcolor 또는 아래에서 덮어씀」이라고 적는다.

```html demo
<div style="color:#1e3a8a; border-bottom:4px solid; border-bottom-color:#ef4444; padding:16px; background:#f8fafc;">A: 단축 다음에 색</div>
<div style="color:#1e3a8a; border-bottom-color:#ef4444; border-bottom:4px solid; padding:16px; background:#f8fafc; margin-top:8px;">B: 색 다음에 단축</div>
```

> **보이는 것** — A 는 아래쪽에 빨간 4px 선이, B 는 글자와 같은 남색 4px 선이 그어진다 (코드에서 읽은 것 — 렌더 실측 아님)

### (4) 상속되지 않지만 `currentcolor` 로 이어진다

**언제 쓰나** — 부모의 `color` 를 바꿨을 때 자식 테두리가 왜 함께 바뀌는지 이해할 때 필요하다.

```text
부모: color: purple
  └ 자식: color 는 상속 → purple
          border-bottom-color 는 상속 안 됨 → 자기 초깃값 currentcolor
          currentcolor → 자식의 color → purple
결과: 자식 아래 테두리 = purple
```

- `border-bottom-color` 자체는 상속되지 않는다(상속: False).
- 대신 자식의 기본값 `currentcolor` 가 자식의 `color` 를 보고, `color` 는 상속되는 속성이다.
- 그래서 결과만 보면 부모 글자 색이 자식 테두리까지 번져 보인다.

### (5) 색은 부드럽게 바뀔 수 있다

**언제 쓰나** — 마우스를 올리면 밑줄 색이 서서히 바뀌는 효과를 만들 때 쓴다.

```text
.link { border-bottom: 2px solid gray; transition: border-bottom-color .3s; }
.link:hover { border-bottom-color: red; }
   │
   └─ hover 되면 gray → red 사이 색이 0.3초 동안 이어서 그려짐
```

- 원본 데이터에서 이 속성은 「애니메이션 가능: True」다.
- 색 값 사이를 중간 색으로 보간할 수 있으므로 `transition` · `@keyframes` 의 대상이 된다.

## 문법 — 형태와 규칙

```css
/* 아래쪽 테두리가 있어야 색이 보인다 */
.underline {
  border-bottom: 4px solid;          /* 두께 + 스타일, 색 생략 → currentcolor */
  border-bottom-color: #ef4444;      /* 반드시 단축 속성 뒤에 */
}

/* 글자 색을 따르게 하려면 명시적으로 써도 된다 */
.follow {
  color: teal;
  border-bottom: 2px dashed;
  border-bottom-color: currentcolor; /* = teal */
}
```

| 값 | 뜻 |
|---|---|
| `<color>` | CSS 색상 값 — 이름(`red`), 16진(`#ef4444`), `rgb()`, `hsl()` 등 |
| `currentcolor` | 요소의 현재 텍스트 색상(`color` 값). 기본값이다 |

| 항목 | 값 |
|---|---|
| 문법 | `border-bottom-color: <color>` |
| 기본값 | `currentcolor` |
| 상속 | 안 됨 |
| 애니메이션 | 가능 |

- 값은 색 하나만 받는다.
- 아래쪽 변에만 작용하고 위 · 왼 · 오른쪽 변은 건드리지 않는다.
- 색만 있고 테두리 스타일이 없으면(기본 스타일 `none`) 선 자체가 그려지지 않는다.

## 어디서 틀리나

### 1. 기본값을 「검정」이나 「투명」으로 안다

원본 팁: 기본값은 `currentcolor` 다.
색을 지정하지 않은 테두리는 검정이 아니라 그 요소의 글자 색이 된다.
글자 색이 흰색인 요소에 색 없이 테두리를 주면 흰 선이 된다.

### 2. 단축 속성을 뒤에 써서 색이 사라진다

`border-bottom-color` 를 쓴 뒤 `border-bottom: 4px solid;` 를 쓰면, 단축 속성이 색을 `currentcolor` 로 되돌린다.
「왜 빨강이 안 나오지?」의 가장 흔한 원인이다.
개별 속성은 단축 속성 뒤에 둔다.

### 3. 색만 주고 선이 없다

`border-bottom-color` 는 색만 정한다.
`border-bottom-style`(또는 단축 속성의 `solid` 같은 스타일)이 없으면 그릴 선이 없어서 아무것도 보이지 않는다.

### 4. 「상속 안 됨」인데 부모를 따라 바뀐다고 놀란다

속성 자체는 상속되지 않지만, 기본값 `currentcolor` 가 상속된 `color` 를 가리키므로 결과적으로 부모 색을 따라간다.
따라가지 않게 하려면 자식에 색을 직접 적는다.

### 5. `border-color` 로 덮어쓴다

나중에 `border-color: blue;` 를 쓰면 네 변 모두 blue 가 되어 아래쪽 색도 덮인다.
단축 속성 · 개별 속성은 모두 「뒤에 쓴 것이 이긴다」로 읽는다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 기본값이 `currentcolor` 다 | CSS 명세(속성 정의의 초깃값) |
| 단축 속성에서 빠진 값은 초깃값으로 맞춰진다 | CSS 명세(단축 속성 규칙) |
| 상속되지 않고, 색으로 보간되어 애니메이션된다 | CSS 명세(속성 정의) |
| 브라우저별 지원 범위 · 렌더링 모습 | 원본에 근거 없음 — (확인 필요) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 아래쪽 선만 다른 색 | `border-bottom-color` | `border-color` 로 네 변 모두 바꾸기 |
| 테두리를 글자 색과 묶어 두기 | 색 생략(기본 `currentcolor`) | 글자 색과 같은 값을 따로 하드코딩 |
| 두께 · 스타일 · 색을 한 번에 | `border-bottom: 4px solid red` | 개별 속성 세 줄 |
| hover 때 밑줄 색 서서히 바꾸기 | `transition: border-bottom-color` | 테두리를 지웠다 새로 그리기 |

## 핵심 문장

1. **`border-bottom-color` 는 아래쪽 테두리 한 변의 색만 정한다** — 다른 세 변은 그대로다.
2. **기본값은 `currentcolor`** — 색을 안 적으면 요소의 글자 색이 된다.
3. **단축 속성 `border-bottom` 은 빠진 색을 초깃값으로 되돌린다** — 개별 색 지정은 단축 속성 뒤에 쓴다.
4. **상속은 안 되지만 `currentcolor` 를 거쳐 부모 글자 색을 따라갈 수 있다.**
5. **색만으로는 선이 생기지 않고, 색은 애니메이션된다.**

## 관련 자료

- `border-color` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `border-bottom` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [border-bottom-style](../37-border-bottom-style/2-summary.md)
- 원본: study-site 항목 데이터 `data/css/box-model.json` 의 `border-bottom-color`

## 용어 풀이

> **테두리(border)** — 박스의 padding 바깥을 둘러싸는 선. 네 변을 따로 정할 수 있다.\
> 예: `border-bottom` 은 아래 변 하나.

> **단축 속성** — 여러 개별 속성을 한 줄로 정하는 속성.\
> 예: `border-bottom: 4px solid red` 는 두께 · 스타일 · 색 세 속성.

> **개별 속성(롱핸드)** — 단축 속성이 묶는 하나하나의 속성.\
> 예: `border-bottom-color`.

> **currentcolor** — 요소의 `color` 값을 가리키는 색 키워드.\
> 예: `color: blue` 이면 `currentcolor` 는 blue.

> **초깃값(기본값)** — 아무 데서도 값을 정하지 않았을 때 쓰이는 값.\
> 예: `border-bottom-color` 의 초깃값은 `currentcolor`.

> **상속** — 자식이 값을 적지 않으면 부모의 값을 물려받는 성질.\
> 예: `color` 는 상속되고 `border-bottom-color` 는 상속되지 않는다.

> **보간** — 두 값 사이의 중간 값을 이어서 계산하는 것.\
> 예: gray 에서 red 로 가는 중간 색들.

## 더 들어가면

- 쓰기 방향에 따라 변을 고르는 논리 속성 `border-block-end-color` 가 있다. 가로쓰기에서는 아래쪽 변에 해당한다 (확인 필요).
- 반투명 색(`rgb(239 68 68 / 50%)` 등)을 주면 테두리 아래로 배경이 비쳐 보일 수 있으며, 이는 `background-clip` 설정에 따라 달라진다 (확인 필요).
- 예전 명세 표기는 `currentColor` 처럼 대소문자를 섞어 썼지만 CSS 키워드는 대소문자를 구분하지 않는다 (확인 필요).
- 표(`table`)에서 `border-collapse: collapse` 일 때 이웃 칸의 테두리 색이 충돌하면 별도 규칙으로 하나가 고른다 (확인 필요).

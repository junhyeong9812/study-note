# css/filter-effects/18 — shape-margin — 정리 (힌트)

> 출처 — study-site 항목 `css/shape-margin`(항목 데이터 `data/css/filter-effects.json`) · 정답 코드 study-practice `css/filter-effects/reference/shape-margin.html`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

## 한눈에 — 쉽게 말하면

**`shape-margin` 은 「둥근 바위 둘레에 두른 갈대 띠」다.**
강물이 둥근 바위를 돌아 흐를 때, 바위 둘레에 갈대 띠가 있으면 물은 바위 표면이 아니라 갈대 띠 바깥까지만 다가온다.
갈대 띠가 아무리 넓어도 바위를 둘러싼 울타리 밖으로는 뻗지 못한다.
CSS 에서 글이 도형을 감싸는 방식도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 강물 | 도형 옆으로 흐르는 텍스트(줄 상자) |
| 둥근 바위 | `shape-outside` 로 정한 도형(예: `circle(50%)`) |
| 갈대 띠 | `shape-margin` 으로 넓힌 여유 |
| 바위를 둘러싼 울타리 | float 요소의 margin box |
| 바위의 겉모습 | `clip-path` 로 잘라 낸 시각 모양 |

```text
      울타리(margin box)
   ┌───────────────────┐
   │   . . 갈대 띠 . .  │   ← shape-margin
   │  .   ( 바위 )   .  │   ← shape-outside
   │   . . . . . . . .  │
   └───────────────────┘
          ~~~~ 강물(텍스트)은 갈대 띠 바깥, 울타리 안쪽 경계를 따라 흐른다
```

## 이 주제가 답하려는 질문

1. `shape-outside` 로 만든 도형과 텍스트 사이에 여유를 주려면 무엇을 쓰나?
2. `shape-margin` 은 어떤 조건에서만 효과가 있나?
3. `shape-margin` 을 크게 잡으면 어디까지 넓어지나?
4. 글이 흐르는 모양과 눈에 보이는 모양은 왜 따로 맞춰야 하나?

## 동작 방식

### (1) `shape-outside` 가 글이 흐를 경계를 만든다

**언제 쓰나** — 네모난 float 박스 대신 원 · 다각형 같은 모양을 따라 글을 감싸고 싶을 때 쓴다.
`shape-margin` 은 이 경계 위에서만 일하므로 먼저 이 단계가 있어야 한다.

> **float** — 요소를 줄 흐름에서 빼내 왼쪽이나 오른쪽에 붙이고, 뒤따르는 글이 그 옆을 돌아 흐르게 하는 배치.\
> 예: `float: left` 인 그림 옆으로 문단 글이 오른쪽에 흐른다.

> **`shape-outside`** — float 요소 둘레에서 글이 흐를 경계 모양을 정하는 속성.\
> 예: `shape-outside: circle(50%)` 면 글이 원을 따라 휜다.

```text
.shape { float: left; shape-outside: circle(50%); }
        │
        ▼
float 이므로 뒤의 글이 옆으로 흐른다
        │
        ▼
흐름 경계가 네모 박스가 아니라 원이 된다
        │
        ▼
글줄의 왼쪽 끝이 원의 곡선을 따라 들쭉날쭉해진다
```

- `float: left` 가 요소를 왼쪽에 띄우고 글이 오른쪽으로 흐르게 한다.
- `shape-outside` 는 float 요소에만 적용된다(원본 주석: 「shape-outside는 float 필수」).
- 경계가 원이 되면 줄마다 글이 시작하는 위치가 원의 가장자리에 맞춰 달라진다.

### (2) `shape-margin` 이 그 경계를 바깥으로 넓힌다

**언제 쓰나** — 글이 도형에 너무 바짝 붙어 답답해 보일 때 여유 공간을 준다.

```text
shape-outside: circle(50%);  +  shape-margin: 16px;
        │
        ▼
원 경계를 모든 방향으로 16px 바깥쪽에 다시 그린다
        │
        ▼
글은 넓어진 경계 바깥에서 줄을 시작한다
        │
        ▼
원 곡선과 글 사이에 고른 틈이 생긴다
```

- `shape-margin` 은 도형의 모양을 그대로 따라 일정한 두께로 바깥에 띠를 두른다.
- 띠가 생긴 만큼 글은 도형에서 떨어져 흐른다.
- 기본값 `0` 이면 띠가 없어 글이 도형 경계에 바로 붙는다.

### (3) margin box 가 넓힐 수 있는 한계를 정한다

**언제 쓰나** — `shape-margin` 을 크게 줬는데 기대만큼 틈이 생기지 않을 때 이 규칙을 떠올린다.

> **margin box** — 요소의 내용 · padding · border · margin 을 모두 합친 바깥 사각형.\
> 예: 너비 80px 에 `margin-right: 8px` 면 margin box 의 가로는 88px 이다.

```text
너비 80px 원 + shape-margin 16px  →  넓어진 원의 오른쪽 끝은 96px 지점
margin box 오른쪽 끝(80 + margin-right 8)  →  88px 지점
        │
        ▼
넓어진 경계가 margin box 를 넘는 부분은 잘린다
        │
        ▼
원 한가운데 높이에서는 글이 88px 에서 시작한다
```

- 원본 팁은 「margin-box보다 클 수 없음」이라고 말한다.
- 따라서 넓어진 경계 중 margin box 밖으로 나간 부분은 글 흐름에 쓰이지 않는다.
- 예제에서 원 가장자리는 80px 지점이고 margin box 끝은 88px 지점이라, 원 가운데 높이의 틈은 16px 가 아니라 약 8px 가 된다(코드에서 읽은 것 — 렌더 실측 아님).
- 위아래로도 margin 이 없으므로 넓어진 원의 위 · 아래 끝 역시 박스 높이에서 잘린다.

### (4) 흐름 모양과 보이는 모양은 따로다

**언제 쓰나** — 도형 자체도 눈에 원으로 보이게 하고 싶을 때 쓴다.

> **`clip-path`** — 요소를 그릴 때 정한 모양 밖을 잘라 내 보이지 않게 하는 속성.\
> 예: `clip-path: circle(50%)` 면 네모 박스가 원으로 보인다.

```text
shape-outside: circle(50%)   → 글의 흐름만 바꾼다 (박스는 여전히 네모로 그려진다)
clip-path:     circle(50%)   → 그리기만 바꾼다   (글 흐름에는 관여하지 않는다)
        │
        ▼
둘을 같이 써야 「원이 보이고, 글도 원을 따라 흐른다」
```

- 원본 주석대로 `shape-outside` 는 시각 출력에 영향이 없다.
- 그래서 배경색이 있는 박스는 `clip-path` 없이 네모로 보인다.
- `shape-margin` 도 흐름에만 관여하므로 띠는 눈에 보이지 않는다.

## 문법 — 형태와 규칙

```html demo
<div style="max-width:300px">
  <div style="float:left; width:80px; height:80px;
              shape-outside:circle(50%); shape-margin:16px;
              clip-path:circle(50%); background:#8b5cf6;
              margin-right:8px;"></div>
  <p>글이 보라색 원을 따라 휘어 흐르고, 원과 글 사이에 여유가 생긴다. 줄이 바뀔 때마다 시작 위치가 원의 곡선에 맞춰 달라진다.</p>
</div>
```

> **보이는 것** — 왼쪽에 보라색 원이 있고, 글줄의 왼쪽 끝이 원의 곡선을 따라 휘며 원과 글 사이에 틈이 있다. (코드에서 읽은 것 — 렌더 실측 아님)

```css
shape-margin: <length-percentage>;
```

| 값 | 뜻 |
|---|---|
| `0` | 여백 없음 (기본값) — 글이 도형 경계에 붙는다 |
| `<length>` | `px` · `em` 같은 길이 단위로 띠 두께를 정한다 |
| `<percentage>` | 백분율로 띠 두께를 정한다 |

- 기본값은 `0` 이다.
- 상속되지 않는다 — 부모에 줘도 자식 float 에는 전해지지 않는다.
- 애니메이션 가능하다 — `transition` 으로 띠 두께를 부드럽게 바꿀 수 있다.
- `shape-outside` 와 `float` 가 함께 있어야 효과가 난다.
- 넓어진 경계는 margin box 를 넘지 못한다.

## 어디서 틀리나

### 1. `shape-margin` 만 주고 `shape-outside` 를 빠뜨린다

띠를 두를 도형이 없으므로 아무 변화가 없다.
`shape-margin` 은 `shape-outside` 가 정한 도형의 「바깥 여백」이다.

### 2. `float` 를 빼먹는다

`shape-outside` 는 float 요소에만 적용되므로, `float` 가 없으면 도형도 띠도 글 흐름에 관여하지 않는다.
요소는 보통 블록처럼 한 줄을 차지하고 글은 그 아래로 내려간다.

### 3. 틈이 기대보다 좁다 — margin box 한계

원본 팁처럼 `shape-margin` 은 margin box 보다 클 수 없다.
예제처럼 `margin-right: 8px` 에 `shape-margin: 16px` 를 주면, 원 가운데 높이에서는 margin box 끝(88px 지점)이 먼저 막아 틈이 약 8px 로 줄어든다(코드에서 읽은 것 — 렌더 실측 아님).
`shape-margin` 만큼 틈을 확보하려면 margin 도 그만큼 넉넉히 줘야 한다.

### 4. 도형이 네모로 보인다

`shape-outside` 와 `shape-margin` 은 글의 흐름만 바꾼다.
배경이 있는 박스를 원으로 보이게 하려면 `clip-path` 를 따로 줘야 한다.

### 5. 보통의 `margin` 으로 대신하려 한다

`margin` 은 박스를 사각형으로 넓힐 뿐이라 원의 곡선을 따라 고른 틈을 만들지 못한다.
도형 모양을 따라 틈을 주는 것은 `shape-margin` 이다.
다만 3 번 때문에 `margin` 은 `shape-margin` 이 뻗을 공간을 마련하는 역할을 한다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 기본값 `0` · 상속 안 됨 · 애니메이션 가능 | CSS 명세의 속성 정의 (원본 데이터 근거) |
| `shape-outside` 는 float 요소에만 적용된다 | CSS Shapes 명세 (원본 주석 근거, 확인 필요) |
| 넓어진 경계가 margin box 를 넘지 못한다 | CSS Shapes 명세의 float 영역 규칙 (원본 팁 근거, 확인 필요) |
| `shape-outside` 는 그리기에 영향이 없다 | CSS Shapes 명세 (원본 주석 근거) |
| 브라우저별 지원 범위 | 원본에 없음 — 확인 필요 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 원형 그림 둘레로 글을 감싸며 여유를 줄 때 | `shape-outside` + `shape-margin` | `shape-margin` 단독 |
| 네모 박스와 글 사이 간격만 필요할 때 | `margin` | `shape-margin` (도형이 없으면 의미 없음) |
| 도형도 눈에 원으로 보여야 할 때 | `clip-path` 를 함께 | `shape-outside` 에만 기대기 |
| 틈을 정확히 16px 로 확보하고 싶을 때 | margin 도 그만큼 넉넉히 | margin 을 작게 둔 채 `shape-margin` 만 키우기 |
| float 이 아닌 요소 옆에 글을 흘릴 때 | 다른 배치 방법 | `shape-outside` · `shape-margin` |

## 핵심 문장

1. **`shape-margin` 은 `shape-outside` 도형의 모양을 따라 바깥에 두르는 여유 띠다.**
2. **float 요소 + `shape-outside` 가 있어야만 효과가 난다.**
3. **넓어진 경계는 margin box 에서 잘린다** — 틈을 확보하려면 margin 도 넉넉해야 한다.
4. **흐름 모양과 보이는 모양은 따로다** — 보이게 하려면 `clip-path` 를 함께 쓴다.
5. **상속되지 않고 애니메이션할 수 있다.**

## 관련 자료

- `shape-outside` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [shape-image-threshold](../19-shape-image-threshold/2-summary.md)
- 원본: study-site 항목 데이터 `data/css/filter-effects.json` 의 `shape-margin`

## 용어 풀이

- **`shape-margin`** — `shape-outside` 로 정한 도형 바깥에 여유를 두는 속성.
- **`shape-outside`** — float 요소 둘레에서 글이 흐를 경계 모양을 정하는 속성.
- **float** — 요소를 한쪽에 띄워 뒤따르는 글이 그 옆을 돌아 흐르게 하는 배치.
- **margin box** — 내용 · padding · border · margin 을 모두 합친 요소의 바깥 사각형.
- **`clip-path`** — 정한 모양 밖을 잘라 내 그리지 않는 속성.
- **`circle(50%)`** — 박스 크기를 기준으로 반지름을 잡은 원 모양 값.
- **상속** — 부모에 준 값이 자식에게 자동으로 전해지는 것.
- **애니메이션 가능** — `transition` · `animation` 으로 값 사이를 부드럽게 이어 바꿀 수 있다는 뜻.

## 더 들어가면

- `<percentage>` 값은 컨테이닝 블록의 인라인 방향 크기를 기준으로 계산된다고 알려져 있다 (확인 필요).
- `shape-outside` 에는 `circle()` 외에 `ellipse()` · `inset()` · `polygon()` · 이미지도 줄 수 있고, `shape-margin` 은 어느 모양에든 띠를 두른다 (확인 필요).
- 이미지를 도형으로 쓸 때는 `shape-image-threshold` 로 어느 투명도부터 도형으로 볼지 정한다 (확인 필요).
- `shape-outside: margin-box` 처럼 상자 키워드를 쓰면 도형 자체가 margin box 와 같아져 `shape-margin` 이 뻗을 자리가 없다 (확인 필요).

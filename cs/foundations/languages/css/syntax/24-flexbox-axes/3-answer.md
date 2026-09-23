# css/syntax/24 — Flexbox: 주축·교차축과 정렬(`justify-*`/`align-*`) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 좌표·치수는 Google Chrome 151.0.7922.173 headless 에서 실제로 렌더해 `getBoundingClientRect()` 로 잰 값**이다.\
> 좌표는 별말이 없으면 **컨테이너의 바깥 왼쪽 위 모서리를 원점**으로 한 값이고, 단위는 px 다.\
> 규칙은 [CSS Flexible Box Layout Level 1](https://drafts.csswg.org/css-flexbox-1/) 과 [CSS Box Alignment Level 3](https://drafts.csswg.org/css-align-3/) 으로 접지했다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 상자 셋은 어디에 놓이는가

**실행 결과** (Chrome 151 headless — 컨테이너 804×140, 테두리 2px, 패딩 8px)

```text
align-items: center 있음   1: L10 T50 W41 H40   2: L382 T50 W41 H40   3: L753 T50 W41 H40
align-items 줄을 지움      1: L10 T10 W41 H120  2: L382 T10 W41 H120  3: L753 T10 W41 H120
```

**가로로 어떻게 놓이는가**

- **왼쪽 끝 · 가운데 · 오른쪽 끝**에 하나씩 놓인다.
- `space-between` 은 **양 끝에 붙이고 남는 공간을 아이템 사이에만** 나눈다.\
  아이템 1 의 왼쪽(L10)이 내용 영역 왼쪽 경계, 아이템 3 의 오른쪽(753+41=794)이 내용 영역 오른쪽 경계다.

**세로로는 어디에 놓이는가**

- **컨테이너 세로 가운데**다. 내용 영역 높이 120px, 아이템 높이 40px 이므로 위아래에 40px 씩 남는다(T50 = 내용 영역 위 경계 10 + 40).

**`align-items: center` 줄을 지우면 상자의 높이는**

- **40px → 120px 로 늘어난다.**

```text
align-items: center                  align-items 없음 (normal -> stretch)
+---------------------------+        +---------------------------+
|                           |        | +---+   +---+   +---+     |
| +---+   +---+   +---+     |        | |   |   |   |   |   |     |
| +---+   +---+   +---+     |        | |   |   |   |   |   |     |
|                           |        | +---+   +---+   +---+     |
+---------------------------+        +---------------------------+
 아이템은 제 높이(40)만 차지          교차축을 꽉 채운다(120)
```

- 초기값 `normal` 이 flex 아이템에서 **`stretch` 처럼 동작**하기 때문이다.
- 그래서 "카드 높이를 서로 맞추려고" 아무것도 안 쓰는 것이 이미 정답인 경우가 많다.

**`height: 120px` 를 지우면**

- **아무 일도 하지 않는다.** 컨테이너 높이가 내용에 딱 맞아 **교차축에 남는 공간이 0** 이 된다.
- "세로 가운데가 안 된다"의 가장 흔한 원인이 이것이다 — `align-items` 가 아니라 **남는 공간**이 없는 것이다.

> **자유 공간(free space)** — 컨테이너에서 아이템들이 쓰고 남은 공간.\
> 예: 높이 120px 컨테이너에 40px 아이템 하나면 교차축 자유 공간은 80px 다. 정렬 속성은 이 공간을 어떻게 나눌지만 정한다.

### 2. `flex-direction` 만 바꿨을 때

**실행 결과** (Chrome 151 headless — 컨테이너 150×150, 테두리 2px)

```text
.row (flex-direction: row)      1: L88 T2    2: L120 T2     (둘 다 W32 H32)
.col (flex-direction: column)   1: L2  T88   2: L2   T120
.col 을 column-reverse 로        1: L2  T34   2: L2   T2
```

**`.row` 안의 아이템들은 어느 모서리에**

- **오른쪽 위.** 아이템 2 의 오른쪽 모서리(120+32=152)가 내용 영역 오른쪽 경계와 일치하고, 둘 다 T2(내용 영역 위 경계)다.

**`.col` 안의 아이템들은 어느 모서리에**

- **왼쪽 아래.** 둘 다 L2(내용 영역 왼쪽 경계)이고, 아이템 2 의 아래 모서리(120+32=152)가 내용 영역 아래 경계와 일치한다.

**정반대 모서리인 이유**

```text
             row                        column
  주축        가로 →                     세로 ↓
  교차축      세로 ↓                     가로 →

  justify-content: flex-end   주축의 끝      = 오른쪽      = 아래
  align-items:    flex-start  교차축의 시작   = 위         = 왼쪽
                                        ------------  ------------
                                          오른쪽 위      왼쪽 아래
```

- 두 선언은 **한 글자도 안 바뀌었다.** 바뀐 것은 그 선언이 가리키는 **축**뿐이다.
- `justify-*` 와 `align-*` 이 **동시에 역할을 맞바꾸기** 때문에 결과가 대각선 반대편으로 간다.

**`column-reverse` 로 바꾸면**

- 아이템이 **왼쪽 위**로 올라가고, **세로 순서도 `2`, `1` 로 뒤집힌다**(실측: 아이템 2 가 T2, 아이템 1 이 T34).
- `*-reverse` 는 main-start 와 main-end 를 맞바꾼다 — `flex-end` 가 이제 **위**를 가리키고, 아이템이 쌓이는 방향도 아래에서 위로 바뀐다.

### 3. `flex-start` 인데 왼쪽이 아니다

**실행 결과** (Chrome 151 headless — 컨테이너 804 폭, 패딩 8px, 테두리 2px, `gap: 8px`)

```text
justify-content: flex-start   1: L762   2: L722   3: L683   (각 W32)
justify-content: flex-end     1: L90    2: L50    3: L10
```

**화면에 보이는 순서**

- 왼쪽부터 **`3  2  1`** 이다.

**`1` 은 어느 쪽 끝에**

- **오른쪽 끝.** 아이템 1 의 오른쪽 모서리(762+32=794)가 내용 영역 오른쪽 경계와 일치한다.

```text
row-reverse 의 좌표계

  main-end                                            main-start
     |                                                     |
     v                                                     v
  +------------------------------------------------------------+
  |                                            [3] [2] [1]      |
  +------------------------------------------------------------+
                                 justify-content: flex-start
                                 = main-start 쪽으로 = 오른쪽
```

**`flex-end` 로 바꾸면**

- 세 상자가 **왼쪽 끝**으로 모인다(실측: 3 이 L10, 2 가 L50, 1 이 L90).
- 화면상의 순서는 여전히 `3 2 1` 이다 — 바뀐 것은 묶음의 위치뿐이다.

**스크린 리더와 Tab 순서**

- **뒤집히지 않는다.** `flex-direction` 은 **시각 배치만** 바꾸고 DOM 순서는 그대로다.
- 그래서 시각 순서와 읽는 순서가 어긋나고, 키보드 사용자는 오른쪽 끝 → 가운데 → 왼쪽 끝으로 초점이 튀는 것을 보게 된다.
- 같은 문제가 `order` 에서 더 심하게 나온다 — 정본은 [목록의 **26번 주제**](../26-flex-wrap-gap-order/).

### 4. 주축과 교차축은 대칭인가

**아이템 하나만 교차축에서 다르게**

- **`align-self`** 를 그 아이템에 준다.
- 실측: `align-items: flex-start` 인 120px 높이 컨테이너에서 `align-self: flex-end` 를 준 아이템만 T98(아래 경계에 붙음), 나머지는 T10.

**아이템 하나만 주축에서 다르게**

- **`margin: auto`** 를 쓴다. `margin-left: auto` 는 그 아이템 왼쪽의 남는 공간을 전부 먹어 아이템을 오른쪽 끝으로 민다.
- 실측: 200px 컨테이너에서 둘째 아이템의 left 가 1 → 186 으로 밀렸다.

**`justify-self` 를 flex 아이템에 주면**

- **아무 일도 일어나지 않는다.** 에러도 경고도 없고 계산값은 남지만 배치가 안 바뀐다.
- 실측: `justify-self: end` 를 준 아이템의 left 가 전혀 변하지 않았다(같은 판에서 `align-self: center` 는 정상 동작).

**비대칭이 생기는 이유**

```text
주축의 자유 공간                        교차축의 자유 공간
+------------------------------+       +------------------------------+
| 아이템 전체가 나눠 갖는 하나  |       | 아이템마다 자기 줄 안에 따로  |
| [1][2][3] <---- 남는 공간 --->|       | [1] ↕   [2] ↕   [3] ↕        |
+------------------------------+       +------------------------------+
 "2번만 끝으로" 라고 하면                각자 독립이므로 개별 예외가
 1·3 의 위치가 정의되지 않는다           모순 없이 성립한다
```

- 주축의 남는 공간은 **아이템들이 공유하는 자원**이라, 한 아이템만 따로 배치하면 나머지의 배치가 결정되지 않는다.
- 교차축은 아이템마다 **자기 줄 안에서 독립적으로** 결정되므로 개별 예외가 성립한다.
- Grid 에는 `justify-self` 가 있다 — 셀이 미리 나뉘어 있어 **아이템마다 자유 공간이 따로** 있기 때문이다([목록의 **28번**](../28-grid-placement/)).

### 5. 어느 축에 어느 값을 쓸 수 있는가

**실행 결과** (Chrome 151 headless, `getComputedStyle`)

```text
align-items: space-between   -> 계산값 normal     (선언이 버려졌다)
justify-content: stretch     -> 계산값 stretch    (버려지지 않았다)
   그러나 아이템 위치: L1(W17), L18(W17)  = flex-start 와 같고 늘어나지도 않았다
align-items: baseline        -> 계산값 baseline   (정상 값)
```

**`space-between` 을 `align-items` 에 주면**

- **선언 하나가 통째로 버려진다.** `align-items` 의 문법에 없는 값이기 때문이다.
- 계산값은 초기값 `normal` 로 남는다 — 규칙의 나머지 선언은 살아 있다(오류 복구 규칙, [목록의 **07번 주제**](../07-syntax-and-error-recovery/)).
- 이유: `space-*` 는 **아이템 사이 간격**을 다루는 값이라 "묶음"을 움직이는 속성(`justify-content`·`align-content`)에만 있다. `align-items` 는 아이템 하나하나를 다룬다.

**`stretch` 를 `justify-content` 에 주면**

- **버려지지 않는다.** 문법상 유효한 값이라 계산값은 `stretch` 로 남는다.
- **그런데 아무 효과가 없다** — 실측에서 아이템 폭이 그대로였고 위치도 `flex-start` 와 같았다.
- 이유: flex 아이템의 **주축 크기는 `flex-grow`/`flex-shrink` 가 정한다**([목록의 **25번 주제**](../25-flex-shorthand-and-sizing/)). 주축을 늘리는 일이 이미 다른 메커니즘의 몫이라 `justify-content: stretch` 가 할 일이 없다.
- **"버려진다"와 "효과가 없다"는 다르다** — 앞은 구문 문제, 뒤는 의미 문제다.

**초기값**

- `justify-content` — **`normal`**
- `align-items` — **`normal`**
- 실측으로 확인했다. **`flex-start`·`stretch` 가 아니다.**

**flex 컨테이너에서 초기값이 실제로 하는 일**

- `justify-content: normal` → **`flex-start` 처럼** 동작(아이템을 main-start 에 붙인다).
- `align-items: normal` → **`stretch` 처럼** 동작(교차축 치수를 안 정한 아이템을 꽉 늘린다).
- `normal` 이라는 한 이름이 **레이아웃 종류마다 다르게 해석**되는 구조다 — 그래서 초기값을 `stretch` 로 외우면 grid·block 에서 어긋난다.

### 6. 정렬이 안 먹는 세 가지 경우

**`.flex` 의 `justify-content` 는 `.child` 를 움직이는가**

- **움직이지 않는다.** flex 아이템은 **직계 자식만**이다.
- `.wrap` 이 아이템이고 `.child` 는 `.wrap` 안의 평범한 블록 상자다.
- 처방: `.wrap` 을 없애거나, `.wrap` 에도 `display: flex` 를 주거나, `.wrap` 에 `display: contents` 를 준다(그 부작용은 [목록의 **16번 주제**](../16-display-inner-outer/)).

**`flex-wrap` 없이 `align-content` 를 주면**

- **아무 일도 일어나지 않는다.** 선언은 유효해서 버려지지 않고 계산값도 남는다.
- ★ **경계는 「줄이 둘 이상이냐」가 아니라 `flex-wrap` 값이다.** 명세가 `flex-wrap: nowrap` 인 컨테이너를 **single-line flex container** 라 부르고 「그때 `align-content` 는 효과가 없다」고 적는다(css-flexbox-1 §6·§8.4).\
  `wrap` 이면 **줄이 하나뿐이어도 「줄」이 있으므로** 그 줄이 교차축에서 움직인다 — 실측: 200×200 컨테이너·항목 하나에서 `wrap` 은 y = 90, `nowrap` 은 y = 0 이었다(계산값은 두 판 다 `center`).
- 정본은 [목록의 **26번 주제**](../26-flex-wrap-gap-order/).

**`margin-left: auto` 가 있으면 `justify-content: center` 는**

- **아무 일도 하지 않는 것처럼 보인다.**

```text
남는 공간을 먹는 순서

  ① margin: auto  가 있는 만큼 전부 먹는다
         ↓
  ② 그러고도 남으면 justify-content 가 나눈다

  auto 마진이 하나라도 있으면 ② 단계에 남는 공간이 0 이다
```

**셋의 공통점**

- **전부 조용하다.** 에러도, 콘솔 경고도, 잘못된 값 표시도 없다.
- 개발자 도구에서 선언은 **줄이 그어지지 않은 채 멀쩡히 보인다** — 캐스케이드에서 진 것이 아니라 **이긴 뒤에 할 일이 없었던 것**이기 때문이다.
- 그래서 "선언이 적용됐는가"가 아니라 "**이 선언이 다룰 자유 공간·대상이 있는가**"를 물어야 진단이 된다.

### 7. `row` 는 정말 "가로"인가

**실행 결과** (Chrome 151 headless — 200px 폭 컨테이너)

```text
direction: rtl + row + flex-start        1: L186   2: L172    (오른쪽부터 채워진다)
writing-mode: vertical-rl + row          1: T1     2: T16     (세로로 쌓인다)
```

**왼쪽부터인가 오른쪽부터인가**

- **오른쪽부터** 채워진다. `direction: rtl` 에서는 인라인 축의 시작이 오른쪽이고, `row` 의 main-start 가 그것을 따른다.
- 선언 `justify-content: flex-start` 는 그대로다 — **바뀐 것은 main-start 의 물리적 위치**다.

**`writing-mode: vertical-rl` 을 주면**

- `flex-direction: row` 의 주축이 **세로**가 된다(실측: 아이템이 T1, T16 으로 세로로 쌓였다).
- 세로쓰기에서는 인라인 축이 세로이기 때문이다.

**`row`/`column` 을 다시 정의하면**

- `row` = **인라인 축**(글자가 흐르는 방향)을 주축으로.
- `column` = **블록 축**(문단이 쌓이는 방향)을 주축으로.
- 한국어 가로쓰기에서만 그것이 각각 가로·세로와 일치한다.

**값 이름이 `flex-start` 인 이유**

- **물리 방향이 아니기 때문**이다. `left`·`top` 은 화면의 고정된 방향을 가리키지만, flex 정렬은 **축의 시작·끝**을 가리킨다.
- 그 위치는 `flex-direction`·`direction`·`writing-mode` 세 가지에 따라 움직인다.
- 논리 축 어휘 전반의 정본은 [목록의 **32번 주제**](../32-logical-properties-and-writing-mode/).

### 8. 다른 주제와 잇기

**행과 열을 동시에 맞춰야 하면**

- **Grid**(목록의 [**27**](../27-grid-track-sizing/)~[**29**](../29-grid-template-areas/)번)를 쓴다. 그리고 Grid 에서는 **`justify-self` 를 쓸 수 있다.**
- 셀이 미리 나뉘어 있어 아이템마다 자유 공간이 따로 있기 때문이다 — 4번의 비대칭이 Grid 에서는 성립하지 않는다.

**`flex-direction` 을 전환에 태우면 왜 비싼가**

- 레이아웃 속성이라 값이 바뀔 때마다 **레이아웃 → 페인트 → 합성**이 전부 다시 돈다.
- 게다가 `flex-direction` 은 **보간 가능한 값이 아니다**(키워드끼리는 중간값이 없다) — 전환이 아예 걸리지 않는다. 무엇이 보간되는지는 목록의 [52번 주제](../52-transition/2-summary.md).
- 어느 속성이 어느 단계를 다시 돌리는지는 [목록의 **56번 주제**](../56-rendering-pipeline-and-will-change/)가 정본이다.

**`gap` 대신 아이템 `margin` 으로 간격을 주면**

- `margin` 은 **양 끝에도 여백을 만든다** — `gap` 은 아이템 **사이에만** 넣는다.
- `margin` 은 아이템 크기의 일부로 계산되어 **`justify-content` 가 나눌 자유 공간을 미리 줄인다.**\
  그래서 `space-between` 과 섞으면 의도한 간격이 안 나온다.
- `gap` 이 flex 에서 늦게(Baseline widely 2023-10-26) 쓸 수 있게 된 탓에 옛 코드가 `margin` 방식을 쓴다. 정본은 [목록의 **26번 주제**](../26-flex-wrap-gap-order/).

**아이템의 크기가 정해지는 규칙**

- [목록의 **25번 주제**](../25-flex-shorthand-and-sizing/)(`flex` 단축 — `grow`/`shrink`/`basis` 와 크기 해결).
- 이 문서는 **크기가 정해진 뒤의 배치**만 다룬다. `flex: 1` 이 무엇으로 펼쳐지는지, `min-width: auto` 때문에 안 줄어드는 사고는 거기다.

## 용어 풀이

- **flex 컨테이너** — `display: flex`/`inline-flex` 를 준 요소. **직계 자식만** 아이템이 된다.
- **주축(main axis)** — 아이템이 줄지어 놓이는 축. `flex-direction` 이 정한다.
- **교차축(cross axis)** — 주축에 직각인 축. 정하는 속성이 없다.
- **main-start / main-end** — 주축의 시작·끝. `*-reverse`·`direction`·`writing-mode` 가 위치를 옮긴다.
- **자유 공간(free space)** — 아이템들이 쓰고 남은 공간. 정렬 속성은 이것을 나누는 규칙이다.
- **`justify-content`** — 주축에서 아이템 **묶음**을 배치한다.
- **`align-items` / `align-self`** — 교차축에서 아이템 **하나하나** / **하나만** 배치한다.
- **`align-content`** — 교차축에서 **여러 줄**을 배치한다. 줄바꿈이 켜졌을 때만 의미가 있다.
- **`normal`** — 여러 정렬 속성의 초기값. 레이아웃 종류마다 다르게 해석된다(flex 에서 `flex-start`·`stretch` 처럼).
- **인라인 축 / 블록 축** — 글자가 흐르는 축 / 문단이 쌓이는 축. `row`/`column` 의 실제 정의.
- **`margin: auto`** — 남는 공간을 먹어 아이템을 미는 수단. flex 에서 주축의 개별 예외를 만드는 유일한 방법.
- **보간(interpolation)** — 시작값과 끝값 사이의 중간값을 만드는 것. 키워드 값에는 중간값이 없다(52번).

## 실행 검증

**이 표는 2026-09-23 재검증에서 실제로 던진 것만 적는다.** 이 문서를 처음 쓴 판이 몇 번 돌렸는지는 **기록이 없어 모른다.**

| 무엇을 | 어떻게 | 결과 |
|---|---|---|
| demo 4개 | 완성된 `2-summary.md` 에서 `extract-demo-blocks.py --render --shot` 로 다시 뽑아 **창 폭 804 로 3판** | 좌표·치수 **전부 일치** · 3판이 한 글자도 안 달랐다 |
| ★ 창 폭 의존 | 같은 도구를 기본 창(폭 780)으로도 돌려 대조 | **x 값이 전부 24px 씩 어긋난다.** 804 에서만 문서의 값이 나온다 — 이 파일 머리의 「804×140」이 그 조건이다 |
| (1) `space-between` + `align-items: center` | 창 804 | `L10 T50` · `L382 T50` · `L753 T50` · 셋 다 `W41 H40`, 컨테이너 `804×140` |
| (2) `row` 대 `column` | 창 804 | row `L88 T2`·`L120 T2` / col `L2 T88`·`L2 T120` (컨테이너 왼쪽 위 기준, 둘 다 `W32 H32`) |
| (3) `row-reverse` + `flex-start` | 창 804 | `1: L762  2: L722  3: L683` — 아이템 1 의 오른쪽이 794 |
| (4) `align-self: flex-end` | 창 804 | `1: L10 T10` · `2(.odd): L50 T98` · `3: L90 T10` |
| ★ `justify-self: end` | demo (6) 과 같은 판에 `.odd { justify-self: end }` 를 얹고 좌표와 계산값을 같이 읽었다 · 1판 | **`left` 는 50 그대로**인데 **계산값은 `end`** — 세 창이 전부 정상인데 배치만 안 바뀐다 |
| ★ `align-content` 의 경계 | 200×200 컨테이너에 높이 20 짜리 항목 하나, `align-content: center` 를 `wrap`/`nowrap` 두 판 · 1판 | `wrap` → **y = 90** · `nowrap` → **y = 0** · **계산값은 두 판 다 `center`** |
| `align-items: space-between` | 계산값 + `cssRules[i].style.cssText` · 1판 | 계산값 `normal` · **`cssText` 에서 선언이 통째로 사라졌다**(버려졌다) |
| `justify-content: stretch` | 계산값 + 아이템 rect · 1판 | 계산값 `stretch` · 아이템은 `left 0` 으로 `flex-start` 와 같고 **안 늘어났다**(버려지지 않았다) |
| 초기값 | 아무 정렬도 안 준 `display: flex` 의 계산값 · 1판 | `align-items: normal` · `justify-content: normal` · `align-content: normal` |
| 기준 소스 | drafts.csswg.org 의 css-flexbox-1 §6·§8.4 와 css-align-3 §5.1.3·§6.1·§6.2 원문 대조 | **「single-line flex container (i.e. one with `flex-wrap: nowrap`) … align-content has no effect」** · **「stretch behaves as flex-start」** · `justify-self` 의 Applies to 에 flex item 이 **없다** |
| Baseline | api.webstatus.dev 조회 2026-09-23 | `flexbox` widely 2015-09-30 / 2018-03-30 · `flexbox-gap` widely 2021-04-26 / 2023-10-26 — 머리말과 일치 |

**다시 던지지 못한 것** — 본문 (7)·(8)절과 이 파일 4·7번의 **200px 컨테이너 실험 세 건**(`margin-left: auto` 의 `1 → 186` · `direction: rtl` 의 `L186`·`L172` · `writing-mode: vertical-rl` 의 `T1`·`T16`).\
**그 실험의 마크업이 문서에 없다** — demo 블록이 아니라 문서 밖에서 돌린 것이라 추출기가 볼 수 없고, 아이템 치수를 복원할 수 없어 절댓값을 재현하지 못했다.\
같은 성질의 최소 판을 새로 만들어 **방향만** 확인했다 — `margin-left: auto` 는 둘째 아이템을 안쪽 오른쪽 경계까지 밀고(내 판: `9 → 193`), `rtl` 은 오른쪽부터 채우며(`193`·`185`), `vertical-rl` 은 `row` 인데 세로로 쌓인다(`T1`·`T9`). **절댓값이 다른 것은 아이템 폭이 다르기 때문이고, 문서가 틀린 것이 아니다.**

**구현 의존 항목** — ① 본문의 **모든 절대 좌표**는 창 폭 804 에서만 재현된다 ② `W41`·`W32` 같은 치수는 `system-ui` 가 이 머신에서 무엇으로 풀리느냐에 달렸다. **둘 다 Chrome 151 의 이 환경에서 관찰한 것**이다.

**엔진은 Chrome 151.0.7922.173 하나다.** Firefox 155 는 이 환경에서 headless 산출이 조용히 실패하고 WebKit 은 이 머신에 없다 — **「두 엔진에서 확인했다」고 적지 않았다.**

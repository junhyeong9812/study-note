# css/syntax/24 — Flexbox: 주축·교차축과 정렬(`justify-*`/`align-*`) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [CSS Flexible Box Layout Level 1](https://drafts.csswg.org/css-flexbox-1/) (축과 방향·`justify-content`·`align-items`) · [CSS Box Alignment Level 3](https://drafts.csswg.org/css-align-3/) (정렬 키워드의 정본). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 `demo` 블록 **4개 전부**를 **Google Chrome 151.0.7922.173** headless 에 실제로 띄워 `getBoundingClientRect()` 로 좌표를 재고 스크린샷으로 눈으로 확인했다.\
> 본문에 나오는 좌표·픽셀 값은 전부 그 실측값이다. **WebKit(Safari)은 이 머신에 없다** — Safari 관련 서술은 하지 않았다.
> **버전** — Flexbox 는 Baseline **widely**(newly 2015-09-30 → widely 2018-03-30). flex `gap` 은 **widely**(newly 2021-04-26 → widely 2023-10-26)로 더 늦다(목록 README 의 지원 표).
> **여기서 다루지 않는 것** — 「언제 왜 들어왔나」는 [`history/web/03-HTML-CSS-진화.md`](../../../../../../history/web/03-HTML-CSS-진화.md) 의 몫이다. 아이템 크기 해결(`flex` 단축)은 목록의 **25번**, 줄바꿈·`gap`·`order` 는 **26번**이 정본이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 화면은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**flex 컨테이너 = 컨베이어 벨트. 주축은 벨트가 흐르는 방향, 교차축은 벨트의 폭 방향이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 컨베이어 벨트 | flex 컨테이너 (`display: flex` 를 준 요소) |
| 벨트 위의 상자들 | flex 아이템 (컨테이너의 직계 자식) |
| 벨트가 흐르는 방향 | **주축(main axis)** — `flex-direction` 이 정한다 |
| 벨트의 폭 방향 | **교차축(cross axis)** — 주축에 직각으로 자동으로 정해진다 |
| 상자를 흐름 방향으로 미는 일 | `justify-content` |
| 상자를 폭 방향으로 맞추는 일 | `align-items` |

- 벨트 방향을 90도 돌리면 **"밀다"와 "맞추다"의 의미도 같이 돈다.**\
  `justify-content: flex-end` 는 벨트가 가로일 땐 오른쪽, 세로일 땐 아래다.
- **속성 이름에는 가로·세로가 없다.** `justify` 는 "주축에서", `align` 은 "교차축에서"라는 뜻이다.\
  그래서 `flex-direction` 한 줄만 바꿔도 나머지 CSS 를 한 글자도 안 건드리고 배치가 통째로 돈다.
- 이 둘을 `가로 정렬 = justify` / `세로 정렬 = align` 으로 외우면 **`column` 을 만나는 순간 전부 뒤집힌다.**

```text
flex-direction: row                  flex-direction: column
+---------------------------+        +---------------------------+
|  주축 ───────────────>    |        |  교차축 ──────────>        |
|                           |        |     │                     |
|  교차축                   |        |     │ 주축                 |
|     │                     |        |     │                     |
|     v                     |        |     v                     |
+---------------------------+        +---------------------------+
 justify-content = 가로            justify-content = 세로
 align-items     = 세로            align-items     = 가로
```

실무에서 이게 터지는 자리는 **모바일에서만 `flex-direction: column` 으로 바꾸는 미디어 쿼리**다.\
가로일 때 맞춰 놓은 `justify-content: center` 가 세로에서는 전혀 다른 뜻이 되어, "모바일에서만 정렬이 깨진다"가 된다.

> **flex 컨테이너(flex container)** — `display: flex` 또는 `inline-flex` 를 준 요소. 그 **직계 자식들**만 flex 아이템이 된다.\
> 예: 손자 요소는 flex 아이템이 아니다 — `justify-content` 가 손자에게는 영향을 주지 않는다.

> **주축(main axis)** — 아이템이 줄지어 놓이는 방향. `flex-direction` 이 정한다.\
> 예: `row` 면 글이 흐르는 방향(한국어·영어에서는 왼쪽 → 오른쪽), `column` 이면 위 → 아래.

> **교차축(cross axis)** — 주축에 직각인 방향. 따로 정하는 속성이 없고 주축이 정해지면 자동으로 따라온다.\
> 예: 주축이 가로면 교차축은 세로다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `justify-content` 와 `align-items` 중 **무엇이 가로이고 무엇이 세로인가** — 그리고 왜 그 질문 자체가 틀렸는가.
2. `flex-direction` 을 바꿨을 때 **나머지 선언의 의미가 어떻게 따라 도는가.**
3. 주축과 교차축에 **똑같이 주어지지 않은 기능**은 무엇이고, 왜 그런가.

## 동작 방식

### (1) 축이 정해지는 순서 — 주축이 먼저, 교차축은 따라온다

**언제 쓰나** — `display: flex` 를 준 순간. 아이템을 하나도 안 넣어도 축은 이미 정해진다.

```text
① display: flex          이 요소를 flex 컨테이너로 만든다
        ↓
② flex-direction         주축의 방향과 시작점을 정한다
        row              주축 = 인라인 축(글이 흐르는 방향)    시작 = 왼쪽*
        row-reverse      주축 = 인라인 축                     시작 = 오른쪽*
        column           주축 = 블록 축(문단이 쌓이는 방향)     시작 = 위
        column-reverse   주축 = 블록 축                       시작 = 아래
        ↓
③ 교차축                 주축에 직각으로 자동 결정 (정하는 속성이 없다)
        ↓
④ 네 지점               main-start / main-end / cross-start / cross-end
        ↓
⑤ 정렬 속성들이 ④의 이름으로 동작한다
        justify-*  ->  main-start ~ main-end 사이
        align-*    ->  cross-start ~ cross-end 사이

* 「왼쪽/오른쪽」은 한국어·영어처럼 글이 왼쪽에서 오른쪽으로 흐를 때의 이야기다. (8) 참고.
```

그림 해설 (한 단계씩):

- **교차축을 정하는 속성은 없다.** 주축이 정해지면 직각으로 따라온다.
- 그래서 축을 바꾸는 방법은 `flex-direction`(과 글쓰기 방향) 하나뿐이다.
- ⑤가 이 주제의 핵심이다 — **정렬 속성은 물리 방향이 아니라 네 지점의 이름으로 정의돼 있다.**

비용 — 없다. `flex-direction` 을 바꾸는 것은 레이아웃 재계산을 부르지만 축 결정 자체는 공짜다.

### (2) 네 지점 — 모든 정렬 값의 좌표계

**언제 쓰나** — `flex-start`·`flex-end` 가 화면 어디를 가리키는지 판단할 때.

```text
flex-direction: row                     flex-direction: column
+--------------------------------+      +--------------------------------+
| cross-start                    |      | cross-start        cross-end   |
|   +------+  +------+           |      |   +------+                     |
|   |      |  |      |           |      |   |      |  <- main-start      |
|   +------+  +------+           |      |   +------+                     |
| ^                            ^ |      |   +------+                     |
| main-start          main-end   |      |   |      |                     |
| cross-end                      |      |   +------+  <- main-end        |
+--------------------------------+      +--------------------------------+
  justify-* 는 좌우로 움직인다             justify-* 는 위아래로 움직인다
  align-*   는 위아래로 움직인다           align-*   는 좌우로 움직인다
```

그림 해설 (한 단계씩):

- `flex-start` 는 **왼쪽이 아니라 main-start(또는 cross-start)** 다.
- 그래서 `justify-content: flex-start` 는 `row` 에서 왼쪽, `column` 에서 위, `row-reverse` 에서 **오른쪽**이다.
- 값 이름에 `flex-` 가 붙은 이유가 이것이다 — 물리 방향(`left`·`top`)이 아님을 이름으로 표시한 것이다.

### (3) `justify-*` 는 주축, `align-*` 는 교차축

**언제 쓰나** — 아이템을 어디에 붙이고 남는 공간을 어떻게 나눌지 정할 때.

```html demo
<div class="row"><div>1</div><div>2</div><div>3</div></div>
<style>
  .row { display: flex; height: 120px;
         justify-content: space-between;   /* 주축(가로)에서 나눈다 */
         align-items: center;              /* 교차축(세로)에서 맞춘다 */
         border: 2px solid #94a3b8; padding: 8px; }
  .row > div { background: #bfdbfe; padding: 8px 16px; font: 16px system-ui; }
</style>
```

> **보이는 것** — 상자 셋이 **가로로는 왼쪽 끝·가운데·오른쪽 끝에 벌어져** 놓이고, **세로로는 컨테이너 한가운데**에 온다. 컨테이너 높이는 120px 인데 상자는 내용 높이(40px)만 차지하고 위아래에 40px 씩 여백이 남는다.\
> **바꿔 볼 것** — `align-items: center` 줄을 **지우면**(초기값 `normal` = `stretch` 처럼) 상자 셋이 세로 120px 를 꽉 채운다 · `space-between` → `space-evenly`(양 끝에도 같은 간격) · `center`(가운데로 모임)

*(Chrome 151 headless 실측: 내용 영역 높이 120px · 아이템 높이 40px · 아이템 top 이 셋 다 내용 영역 위에서 40px — 위아래 여백이 같다. `align-items` 줄을 지운 판에서는 아이템 높이가 120px 로 늘어났다.)*

| 속성 | 어느 축 | 무엇을 움직이나 |
|---|---|---|
| `justify-content` | **주축** | 아이템 **전체 묶음**과 그 사이 간격 |
| `align-items` | **교차축** | 아이템 **하나하나**를 교차축에서 |
| `align-self` | **교차축** | 아이템 **하나만** 예외로 |
| `align-content` | **교차축** | 여러 **줄**을 (줄바꿈이 켜졌을 때만 — 26번) |

- `justify-content` 는 **묶음**을 움직이고 `align-items` 는 **개별 아이템**을 움직인다.\
  이름이 `content`(내용 전체) 대 `items`(각 아이템)로 갈리는 것이 그 차이를 그대로 적은 것이다.

### (4) 같은 선언, `flex-direction` 만 바꾸면 90도 돈다

**언제 쓰나** — 반응형에서 `row` ↔ `column` 을 바꿀 때. **이 주제에서 가장 자주 사고가 나는 자리다.**

```html demo
<div class="pair">
  <div class="f row"><i>1</i><i>2</i></div>
  <div class="f col"><i>1</i><i>2</i></div>
</div>
<style>
  .pair { display: flex; gap: 16px; }
  .f { display: flex; width: 150px; height: 150px; border: 2px solid #94a3b8;
       justify-content: flex-end;      /* 주축의 끝 */
       align-items: flex-start; }      /* 교차축의 시작 */
  .row { flex-direction: row; }
  .col { flex-direction: column; }
  .f i { background: #bfdbfe; padding: 6px 12px; font: 14px system-ui; font-style: normal; }
</style>
```

> **보이는 것** — 왼쪽 상자(`row`)는 아이템 둘이 **오른쪽 위 모서리**에 붙고, 오른쪽 상자(`column`)는 **왼쪽 아래 모서리**에 붙는다. `justify-content: flex-end` 와 `align-items: flex-start` 는 두 상자에 **똑같이** 걸려 있고 다른 것은 `flex-direction` 한 줄뿐이다.\
> **바꿔 볼 것** — `.col` 의 `column` → `column-reverse` → 아이템이 **왼쪽 위**로 올라가고 세로 순서도 `2`, `1` 로 뒤집힌다(main-start 가 아래로 옮겨갔기 때문) · `justify-content: flex-end` → `center` → 두 상자에서 각각 가로 가운데 / 세로 가운데가 된다

*(Chrome 151 headless 실측 — 컨테이너(150×150, 테두리 2px) 왼쪽 위 모서리를 원점으로 잰 값: `row` 는 두 아이템이 `top=2`(안쪽 위 경계)이고 둘째 아이템의 오른쪽 모서리가 `152`(안쪽 오른쪽 경계)에 닿는다. `col` 은 두 아이템이 `left=2`(안쪽 왼쪽 경계)이고 둘째 아이템의 아래 모서리가 `152`(안쪽 아래 경계)에 닿는다.)*

그림 해설 (한 단계씩):

```text
     row                              column
  +---------------+                +---------------+
  |         [1][2]|  <- 오른쪽 위   |[1]            |
  |               |                |[2]            |
  |               |                |               |
  |               |                |               |
  +---------------+                +---------------+
                                   |[1]            |  <- 실제로는 왼쪽 아래
                                   |[2]            |
```

- 같은 두 선언이 **정반대 모서리**를 가리킨다.
- 그래서 `column` 으로 바꾸는 미디어 쿼리를 쓸 때는 **`justify-content` 와 `align-items` 도 같이 손봐야 하는지** 매번 확인해야 한다.
- "가로 정렬은 justify" 라고 외운 사람은 여기서 반드시 틀린다.

비용 — `flex-direction` 변경은 레이아웃 전체 재계산이다. 애니메이션 대상으로는 쓰지 않는다(목록의 **56번 주제**).

### (5) `row-reverse` — 시작점이 반대쪽으로 옮겨간다

**언제 쓰나** — 마크업 순서는 그대로 두고 시각 순서만 뒤집고 싶을 때.

```html demo
<div class="f"><i>1</i><i>2</i><i>3</i></div>
<style>
  .f { display: flex; flex-direction: row-reverse;
       justify-content: flex-start;    /* 주축의 '시작' */
       border: 2px solid #94a3b8; padding: 8px; gap: 8px; }
  .f i { background: #bfdbfe; padding: 6px 12px; font: 14px system-ui; font-style: normal; }
</style>
```

> **보이는 것** — `1` 이 **오른쪽 끝**에 붙고 그 왼쪽으로 `2`, `3` 이 이어진다. 화면에는 왼쪽부터 `3 2 1` 로 보인다. `justify-content: flex-start` 인데 왼쪽이 아니다 — `row-reverse` 가 main-start 를 오른쪽으로 옮겼기 때문이다.\
> **바꿔 볼 것** — `flex-start` → `flex-end` → 세 상자가 **왼쪽 끝**으로 모인다 · `row-reverse` → `row` → 왼쪽부터 `1 2 3`

*(Chrome 151 headless 실측 — 컨테이너 왼쪽 위를 원점으로: 아이템 `1` 의 오른쪽 모서리가 794 로 내용 영역 오른쪽 끝과 일치하고, `2`(left 722)·`3`(left 683)이 그 왼쪽으로 이어진다. `flex-end` 로 바꾼 판에서는 `3`(left 10)·`2`(50)·`1`(90) 로 왼쪽 끝에 모였다.)*

그림 해설 (한 단계씩):

- `*-reverse` 는 아이템을 뒤집는 게 아니라 **main-start 와 main-end 를 맞바꾼다.**
- 그래서 `flex-start`·`flex-end` 가 가리키는 화면 위치가 통째로 바뀐다.
- **마크업 순서는 그대로다** — 스크린 리더와 키보드 Tab 순서는 여전히 `1 → 2 → 3` 이다.\
  시각 순서와 읽는 순서가 어긋나는 문제는 목록의 **26번 주제**(`order`)가 정본이다.

### (6) 교차축에만 있는 개별 예외 — `align-self`

**언제 쓰나** — 아이템 하나만 다른 정렬을 주고 싶을 때.

```html demo
<div class="f"><i>1</i><i class="odd">2</i><i>3</i></div>
<style>
  .f { display: flex; align-items: flex-start; height: 120px;
       gap: 8px; border: 2px solid #94a3b8; padding: 8px; }
  .f i { background: #bfdbfe; padding: 6px 12px; font: 14px system-ui; font-style: normal; }
  .odd { align-self: flex-end; }       /* 교차축에서만 개별 예외 */
</style>
```

> **보이는 것** — `1` 과 `3` 은 컨테이너 **위쪽**에 붙고 `2` 만 **아래쪽**에 붙는다. 셋의 가로 위치는 그대로다.\
> **바꿔 볼 것** — `align-self: flex-end` → `center`(가운데) · `stretch`(세로로 꽉 참) · `.odd` 에 `justify-self: flex-end` 를 추가 → **아무 일도 일어나지 않는다**(flex 에는 `justify-self` 가 없다)

*(Chrome 151 headless 실측 — 컨테이너 왼쪽 위를 원점으로: `1`·`3` 의 top 이 10(내용 영역 위 경계), `2` 의 top 이 98 이고 그 아래 모서리가 130 으로 내용 영역 아래 경계와 일치. 별도 판에서 `justify-self: end` 를 준 아이템의 left 는 전혀 변하지 않았다 — 무시된다.)*

```text
주축과 교차축은 대칭이 아니다

  교차축                              주축
  +--------------------------+       +--------------------------+
  | align-items  (전체)      |       | justify-content (전체)   |
  | align-self   (개별) ✓    |       | justify-self    (없음) ✗ |
  +--------------------------+       +--------------------------+
     아이템 하나만 예외 가능             개별 예외 수단이 없다
                                       -> margin: auto 로 대신한다 (7)
```

그림 해설 (한 단계씩):

- **교차축에는 개별 예외(`align-self`)가 있고 주축에는 없다.**
- 이유는 주축의 자유 공간이 **아이템들끼리 나눠 갖는 자원**이기 때문이다 — 한 아이템만 "끝으로"라고 하면 나머지 배치가 정의되지 않는다.\
  교차축은 아이템마다 자기 줄 안에서 독립적으로 결정되므로 개별 예외가 성립한다.
- Grid 에는 `justify-self` 가 있다(셀이 미리 나뉘어 있어 자유 공간이 아이템마다 따로 있다). 목록의 **28번 주제**.

### (7) 주축의 개별 예외는 `margin: auto` 로 만든다

**언제 쓰나** — "이 버튼 하나만 오른쪽 끝으로" 같은 배치.

```text
  .f  { display: flex; justify-content: flex-start }
  .f .push { margin-left: auto }

  +--------------------------------------------+
  |[1]                                      [2]|
  +--------------------------------------------+
        ^ margin-left:auto 가 남는 공간을 전부 먹는다
```

- 남는 공간은 **`margin: auto` 가 먼저 먹고, 남으면 `justify-content` 가 나눈다.**\
  그래서 `auto` 마진이 하나라도 있으면 `justify-content` 는 **아무 일도 하지 않는 것처럼 보인다.**
- `margin: auto` 는 교차축에서도 통한다 — 세로 가운데 정렬의 옛 관용구가 이것이다.

*(Chrome 151 headless 실측: 200px 컨테이너에서 `margin-left: auto` 를 받은 둘째 아이템의 left 가 1 → 186 으로 밀렸다.)*

### (8) 물리 방향이 아니다 — 글쓰기 방향이 축을 다시 돌린다

**언제 쓰나** — 아랍어·히브리어(RTL)나 세로쓰기 문서를 다룰 때.

```text
direction: ltr + row              direction: rtl + row
+------------------------+        +------------------------+
|[1][2]                  |        |                  [2][1]|
+------------------------+        +------------------------+
 main-start = 왼쪽                 main-start = 오른쪽

 justify-content: flex-start 는 두 경우 모두 "main-start 로"다.
 바뀐 것은 선언이 아니라 main-start 의 위치다.
```

*(Chrome 151 headless 실측: `direction: rtl` 인 200px 컨테이너에서 `justify-content: flex-start` 일 때 아이템 `1` 의 left 가 186, `2` 가 172 — 오른쪽 끝부터 채워진다.)*

- `writing-mode: vertical-rl` 을 주면 `row` 의 주축이 **세로**가 된다.\
  *(같은 실측: `vertical-rl` 컨테이너에서 `row` 인데 아이템이 세로로 쌓였다 — top 1, 16.)*
- 즉 `row` 는 "가로"가 아니라 **"인라인 축"** 이고, `column` 은 "세로"가 아니라 **"블록 축"** 이다.
- 이것이 `left`/`right` 대신 `start`/`end` 어휘를 쓰는 이유다. 논리 축의 정본은 목록의 **32번 주제**.

비용 — 없다. 다만 **다국어 사이트에서 `flex-start` 를 "왼쪽"으로 읽고 짠 레이아웃은 RTL 에서 통째로 뒤집힌다.**

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 묻는 것 하나만 남겼다.

### 최소 형태

```css
.container {
  display: flex;             /* 이 줄만으로 이미 축이 생긴다 (row 가 기본) */
  flex-direction: row;       /* 주축 — 생략하면 row */
  justify-content: center;   /* 주축 정렬 — 생략하면 normal(= flex-start 처럼) */
  align-items: center;       /* 교차축 정렬 — 생략하면 normal(= stretch 처럼) */
}
```

- **초기값은 `stretch`·`flex-start` 가 아니라 둘 다 `normal` 이다.**\
  *(Chrome 151 headless 에서 `getComputedStyle` 로 확인: `align-items` → `normal`, `justify-content` → `normal`.)*\
  flex 컨테이너에서 `normal` 은 각각 `stretch`·`flex-start` **처럼 동작**한다.
- `display: flex` 는 컨테이너를 블록 상자로, `display: inline-flex` 는 인라인 상자로 만든다.\
  안쪽 배치(= 아이템을 flex 로 놓는 것)는 둘이 같다. `display` 값의 두 부분 이야기는 [목록의 **16번 주제**](../16-display-inner-outer/).

### 값 — 어느 축에 무엇을 쓸 수 있나

| 값 | `justify-content` (주축) | `align-items` (교차축) |
|---|---|---|
| `flex-start` / `flex-end` | ✓ | ✓ |
| `center` | ✓ | ✓ |
| `space-between` / `space-around` / `space-evenly` | ✓ | ✗ — **선언이 통째로 버려진다** |
| `stretch` | 문법은 유효, **flex 에서는 효과 없음** | ✓ (아이템이 교차축 치수를 안 정했을 때) |
| `baseline` | ✗ — 선언이 버려진다 | ✓ (글자 기준선을 맞춘다) |
| `normal` (초기값) | ✓ | ✓ |

*(Chrome 151 headless 실측: `align-items: space-between` 을 쓴 컨테이너의 계산값은 `normal` — 선언이 버려졌다. `justify-content: stretch` 의 계산값은 `stretch` 로 남지만 아이템은 늘어나지 않고 `flex-start` 처럼 왼쪽에 붙었다.)*

- **`space-*` 는 주축(과 여러 줄) 전용**이다 — 아이템 **사이**를 벌리는 값이라 "묶음"을 다루는 `justify-content`·`align-content` 에만 있다.\
  교차축의 `align-items` 에 쓰면 **값이 유효하지 않아 선언 하나가 버려진다**([목록의 **07번 주제**](../07-syntax-and-error-recovery/), 오류 복구).
- **`baseline` 은 교차축 전용**이다 — 아이템 하나하나의 기준선을 다루는 값이라 `align-*` 에만 있다.
- `stretch` 는 `justify-content` 에도 문법적으로 쓸 수 있지만, **flex 아이템의 주축 크기는 `flex-grow` 가 정하므로** 아무 효과가 없다(목록의 **25번 주제**).
- 이 비대칭이 (6)의 `justify-self` 부재와 같은 뿌리다.

### 대응표 — 헷갈릴 때 보는 자리

| 하고 싶은 것 | `row` 일 때 | `column` 일 때 |
|---|---|---|
| 가로 가운데 | `justify-content: center` | `align-items: center` |
| 세로 가운데 | `align-items: center` | `justify-content: center` |
| 양 끝으로 벌리기(가로) | `justify-content: space-between` | (주축이 아니라 불가 — 26번의 `align-content`) |
| 하나만 반대쪽 끝으로(가로) | `margin-left: auto` | `align-self: flex-end` |

- **완전 중앙**은 방향과 무관하게 `justify-content: center; align-items: center;` 둘 다 주면 된다.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 다섯 다 **에러 없이 조용히 어긋난다.**

### 1. `justify` = 가로, `align` = 세로로 외운다

```text
외운 대로면                              실제 (column 일 때)
+------------------------------+        +------------------------------+
| justify-content: center      |        | justify-content: center       |
|   -> 가로 가운데를 기대       |        |   -> 세로 가운데가 된다        |
+------------------------------+        +------------------------------+
```

`row` 에서만 맞는 규칙이다. 미디어 쿼리로 `column` 이 되는 순간 **모바일에서만 정렬이 이상하다**가 된다.\
올바른 기억: **`justify` = 주축, `align` = 교차축.**

### 2. `flex-start` 를 "왼쪽"으로 읽는다

`row-reverse` 에서는 오른쪽, `column` 에서는 위, RTL 에서는 오른쪽이다.\
값 이름에 `left` 가 없는 이유가 그것이다 — **물리 방향이 아니라 축의 시작점**이다.

### 3. 손자 요소에 정렬이 안 먹는다

```html
<div class="flex">
  <div class="wrap">          <!-- 이것이 flex 아이템 -->
    <div class="child">       <!-- 이것은 아니다 -->
```

`justify-content` 는 **직계 자식만** 움직인다.\
"정렬이 안 먹는다"의 절반은 중간에 래퍼가 하나 더 있는 경우다.

### 4. `justify-self` 를 쓴다

flex 컨테이너의 아이템에서는 **무시된다**(에러도 경고도 없다).\
주축의 개별 예외는 `margin: auto` 로 만든다. Grid 와 헷갈리기 쉬운 자리다.

### 5. `align-content` 가 안 먹는다

`flex-wrap: wrap` 으로 **줄이 둘 이상 생겼을 때만** 의미가 있다.\
한 줄짜리 flex 에서는 아무 일도 하지 않는다. 정본은 목록의 **26번 주제**.

### 6. `height` 를 안 줬는데 세로 가운데가 안 된다

`align-items: center` 는 **교차축에 남는 공간**을 전제한다.\
컨테이너 높이가 내용에 딱 맞으면 남는 공간이 0 이라 가운데가 곧 위다 — 위 demo 에서 `height: 120px` 를 준 이유다.

## 언제 쓰고 언제 안 쓰나

| 상황 | Flexbox | 다른 것 |
|---|---|---|
| 한 줄(또는 한 열)로 늘어놓고 남는 공간 나누기 | **쓴다** | |
| 내비게이션 바·버튼 묶음·카드 헤더 | **쓴다** | |
| 행과 열을 **동시에** 맞춰야 한다 | 어렵다 | Grid (목록 27~29번) |
| 아이템마다 주축 위치를 따로 지정해야 한다 | `justify-self` 가 없다 | Grid |
| 여러 카드의 **내부 줄**을 카드끼리 맞춰야 한다 | 못 한다 | `subgrid` (목록 30번) |
| 텍스트를 이미지 주위로 흘려야 한다 | 못 한다 | `float` (목록 20번) |

판단 규칙 두 줄.

- **한 축이면 flex, 두 축이면 grid.** 축을 하나만 신경 쓰면 되는 배치가 flex 의 자리다.
- **`flex-direction` 을 바꾸는 미디어 쿼리를 쓸 거면 정렬 두 줄도 함께 검토한다.** 자동으로 따라 돌지 않는 것이 아니라, **따라 도는 것이 문제**일 때가 있다.

## 핵심 문장

- `justify-*` 는 **주축**, `align-*` 는 **교차축**이다. 가로·세로가 아니다.
- 주축은 `flex-direction` 이 정하고 **교차축은 정하는 속성이 없다** — 직각으로 따라온다.
- `flex-start` 는 왼쪽이 아니라 **main-start** 다. `*-reverse` 와 RTL·세로쓰기가 그 위치를 옮긴다.
- 주축과 교차축은 **대칭이 아니다** — 교차축에는 `align-self` 가 있고 주축에는 `justify-self` 가 없다. 주축의 개별 예외는 `margin: auto` 로 만든다.
- `space-*` 는 주축(묶음) 전용, `stretch`·`baseline` 은 교차축(개별) 전용이다.
- `justify-content`·`align-items` 의 초기값은 둘 다 `normal` 이고, flex 에서 각각 `flex-start`·`stretch` 처럼 동작한다.

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 24번) · 「버전·지원 기준」의 Baseline 표
- 목록의 **25번 주제**(`flex` 단축 — `grow`/`shrink`/`basis`) — **아이템의 크기가 정해지는 규칙**은 거기. 이 문서는 크기가 정해진 뒤의 배치만 다룬다
- 목록의 **26번 주제**(줄바꿈·`gap`·`order`) — `flex-wrap`·`align-content`·`order` 의 정본
- [목록의 **16번 주제**](../16-display-inner-outer/)(`display` 의 내부/외부 값) — `flex` 와 `inline-flex` 가 갈리는 자리
- 목록의 **27~29번 주제**(Grid) — 두 축을 동시에 다뤄야 할 때. `justify-self` 는 거기 있다
- 목록의 **32번 주제**(논리 속성과 글쓰기 방향) — `row` 가 왜 "가로"가 아닌지의 정본
- [`history/web/03-HTML-CSS-진화.md`](../../../../../../history/web/03-HTML-CSS-진화.md) — **1차원 레이아웃이 언제 왜 들어왔나는 거기.** 여기는 오늘의 규칙만
- [`reference/render-rules.md`](../../../../../../reference/render-rules.md) — 이 문서의 `demo` 블록 규칙

## 용어 풀이

- **flex 컨테이너(flex container)** — `display: flex`/`inline-flex` 를 준 요소. 직계 자식만 아이템이 된다.
- **flex 아이템(flex item)** — flex 컨테이너의 직계 자식 상자.
- **주축(main axis)** — 아이템이 줄지어 놓이는 방향. `flex-direction` 이 정한다.
- **교차축(cross axis)** — 주축에 직각인 방향. 자동으로 정해진다.
- **main-start / main-end** — 주축의 시작·끝 지점. `*-reverse` 와 글쓰기 방향이 위치를 바꾼다.
- **cross-start / cross-end** — 교차축의 시작·끝 지점.
- **`justify-content`** — 주축에서 아이템 **묶음**과 그 사이 간격을 정한다.
- **`align-items`** — 교차축에서 아이템 **하나하나**를 맞춘다.
- **`align-self`** — 교차축에서 아이템 **하나만** 예외 처리한다. 주축에는 대응물이 없다.
- **`align-content`** — 교차축에서 **여러 줄**을 다룬다. 줄바꿈이 켜졌을 때만 의미가 있다(26번).
- **인라인 축(inline axis)** — 글자가 흐르는 방향의 축. 한국어 가로쓰기에서는 가로.
- **블록 축(block axis)** — 문단이 쌓이는 방향의 축. 한국어 가로쓰기에서는 세로.
- **자유 공간(free space)** — 컨테이너에서 아이템들이 쓰고 남은 공간. `margin: auto` 가 먼저 먹고 `justify-content` 가 나눈다.

---

## [Claude 추가] 더 알면 좋은 것

- `place-items`·`place-content` 는 `align-*` 와 `justify-*` 를 한 줄로 쓰는 단축이다.\
  **순서가 `align` 먼저, `justify` 나중**이라 헷갈리기 쉽다 — `place-items: center` 하나로 두 축 가운데가 된다.
- `gap`(= `row-gap`/`column-gap`)은 flex 에서 늦게 들어와서(Baseline widely 2023-10-26) 오래된 코드는 아직 아이템 `margin` 으로 간격을 준다.\
  `margin` 방식은 양 끝에도 여백이 생기고 `justify-content` 와 간섭한다는 점이 다르다(26번).
- `flex-direction` 은 **레이아웃 속성**이라 애니메이션에 쓰면 매 프레임 레이아웃이 다시 돈다.\
  움직임이 필요하면 `transform` 쪽으로 옮긴다 — 어떤 속성이 어느 단계를 다시 돌리는지는 목록의 **56번 주제**.
- `align-items: baseline` 은 글자 크기가 다른 아이템을 나란히 놓을 때 **글자 밑줄을 맞춰** 준다.\
  상자 위아래를 맞추는 `flex-start`·`center` 와 결과가 눈에 띄게 다르고, 라벨과 값을 나란히 놓는 UI 에서 쓸모가 크다.

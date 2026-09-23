# css/syntax/20 — 부동(float)과 해제(clear) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [CSS Logical Properties Level 1](https://drafts.csswg.org/css-logical-1/) (`float: inline-start`/`inline-end` 논리 값) · [CSS Display Module Level 3](https://drafts.csswg.org/css-display-3/) (부동이 상자를 블록으로 바꾸는 규정). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 `demo` 블록 **4개 전부**와 본문의 모든 치수를 **Google Chrome 151.0.7922.173** headless 에 실제로 띄워 쟀다.\
> ★ **이 주제에서 「밀렸다」는 `getBoundingClientRect()` 로는 안 보인다.** 상자는 안 움직이고 **줄만** 움직이기 때문이다. 그래서 **`Range.getClientRects()` 로 행 상자를 직접 쟀다** — 자리마다 어느 쪽 값인지 밝혔다.\
> **WebKit(Safari)은 이 머신에 없고 Firefox 는 이 환경에서 headless 스크린샷이 산출되지 않는다** — 크로스 브라우저 주장은 하지 않았다.
> **여기서 다루지 않는 것** — ★ **높이 붕괴를 막는 법(BFC)은 [17번](../17-block-formatting-context/2-summary.md)이 정본이다.** 여기는 **왜 붕괴가 일어나는가** — float 가 높이 계산에 참여하지 않는다는 것까지이고, 고치는 법은 거기로 넘긴다. 마진 상쇄는 [18번](../18-margin-collapsing/2-summary.md), 행 상자 자체는 [19번](../19-inline-formatting-context/2-summary.md), 흐름에서 **완전히** 빠지는 `absolute` 는 [21번](../21-position-and-containing-block/2-summary.md), 1차원 배치의 오늘날 답은 [24번](../24-flexbox-axes/2-summary.md)이다. `shape-outside`(감싸는 모양을 사각형 말고 다른 도형으로 바꾸는 속성)는 **이름만 적고 다루지 않는다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 수치는 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**float 는 「흐름에서 빠지되 글줄은 미는」 반쯤 빠진 상자다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 강물 | 보통 흐름(글줄) |
| 강 한가운데 박힌 **바위** | **float 된 상자** |
| 바위를 **피해 갈라져 흐르는 물** | 바위 옆으로 밀려난 **행 상자** |
| 바위가 **강바닥에는 그대로 있는 것** | 블록 상자는 float 밑으로 그대로 깔린다 |
| 「이 지점부터는 바위 아래에서 시작하라」는 표지판 | `clear` |
| 강을 **다리로 건너가는 배** — 물이 안 갈라진다 | [`position: absolute`](../21-position-and-containing-block/2-summary.md) |

```text
   float                                     absolute
  +----------------------------+            +----------------------------+
  |[ float ] 글줄글줄글줄글줄  |            |[ abs  ]줄줄줄줄줄줄줄줄줄줄|
  |[  상자 ] 글줄글줄글줄글줄  |            |[      ]줄줄줄줄줄줄줄줄줄줄|
  |글줄글줄글줄글줄글줄글줄글줄|            |글줄글줄글줄글줄글줄글줄글줄|
  +----------------------------+            +----------------------------+
     줄이 비켜 간다 (자리를 만든다)            줄이 안 비킨다 (그냥 덮는다)
```

*(Chrome 151 headless 실측 — 같은 폭 300 컨테이너. float 쪽 행 상자는 **x=101 에서 시작해 폭 197** 로 세 줄, absolute 쪽은 **x=1 에서 폭 287** 로 두 줄이었다.)*

실무에서 이게 터지는 자리는 **"float 만 들어 있는 부모의 높이가 0 이 된다"** 는 증상이다.\
그건 float 의 **정의**이지 버그가 아니다 — 막는 법은 [17번](../17-block-formatting-context/2-summary.md)이 정본이다.

> **부동(float)** — 상자를 줄에서 떼어 컨테이너의 한쪽 끝으로 밀어 붙이고, **남은 줄이 그 옆을 흐르게** 하는 것.\
> 예: 신문 기사에서 사진이 왼쪽에 붙고 글이 그 오른쪽을 감싸 도는 배치.

> **해제(clear)** — 「내 위쪽에 있는 float 아래로 내려가서 시작하라」는 지시.\
> 예: 사진 밑에 캡션 줄을 확실히 깔고 싶을 때 쓴다.

> **보통 흐름(normal flow)** — 블록은 위에서 아래로, 인라인은 줄을 따라 가로로 놓이는 기본 배치.\
> 예: 아무 `position`·`float` 도 안 준 문서가 흐르는 방식.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. float 는 흐름에서 **무엇으로부터 빠지고 무엇에는 남아 있는가.**
2. `clear` 는 **정확히 무엇을 하는가** — 그것은 마진인가 아닌가.
3. flex·grid 가 있는 오늘 float 에 **남은 용도는 무엇인가.**

## 동작 방식

### (1) 「빠진다」와 「민다」가 동시에 일어난다

**언제 쓰나** — float 가 무엇을 하는지 한 문장으로 잡을 때. **이 절이 이 주제의 전부다.**

```text
  <div class=col>
    <div class=f>float 120×80</div>
    <div>첫 블록</div>  <div>둘째</div> … 다섯 블록
  </div>

  블록 상자들이 보는 세상            행 상자들이 보는 세상
  +----------------------------+     +----------------------------+
  | [블록 1  폭 300 x=1      ] |     | [float][줄 x=121 폭 89   ] |
  | [블록 2  폭 300 x=1      ] |     | [float][줄 x=121 폭 89   ] |
  | [블록 3  폭 300 x=1      ] |     | [float][줄 x=121 폭 89   ] |
  | [블록 4  폭 300 x=1      ] |     | [float][줄 x=121 폭 89   ] |
  | [블록 5  폭 300 x=1      ] |     | [       줄 x=1   폭 102  ] |
  +----------------------------+     +----------------------------+
      float 가 없는 것처럼 배치           float 옆을 비켜 간다
```

*(Chrome 151 headless 실측 — 폭 300 컨테이너, float 120×80. 다섯 형제 블록 전부 `rect.x=1 · rect.width=300` 으로 **한 픽셀도 안 움직였다.** 같은 요소의 행 상자를 `Range.getClientRects()` 로 재니 float 높이 안에 걸린 **1\~4번째는 x=121 에서 폭 89**, float 아래로 내려간 **5번째만 x=1 에서 폭 102** 였다.)*

```html demo
<div class="col">
  <div class="f">float</div>
  <p>첫째 문단이다. 이 줄은 float 를 비켜 간다.</p>
  <p class="b">둘째 문단이다. 배경을 보면 상자 자체는 안 밀린 것이 드러난다.</p>
  <p>셋째 문단. float 아래로 내려오면 다시 왼쪽 끝부터 흐른다. 계속 이어서 길게 쓴다.</p>
</div>
<style>
  .col { display: flow-root; width: 280px; border: 1px solid #333; font: 13px/20px system-ui; }
  .f { float: left; width: 110px; height: 60px; background: #93c5fd; }
  .col p { margin: 0; }
  .b { background: #fde68a; }
</style>
```

> **보이는 것** — 파란 float 가 왼쪽 위에 있고 글줄은 그 오른쪽에서 시작한다. ★ **노란 배경(둘째 문단)은 파란 상자와 겹치는 구간에서 파란색에 덮이고, 파란 상자가 끝나는 높이부터 왼쪽 끝까지 다시 나타난다** — 노랑이 float 오른쪽에서 끊기지 않고 **float 밑을 지나 이어진다**는 뜻이고, 그것이 상자 자체는 안 밀렸다는 증거다. 밀린 것은 **글자뿐**이다. 셋째 문단은 float 보다 아래라 왼쪽 끝부터 흐른다.\
> **바꿔 볼 것** — `.f` 의 `height` 를 `20px` 로 줄이면 **첫 줄만 밀린다** · `.b` 에 `display: flow-root` 를 주면 **노란 배경이 float 를 피해 오른쪽으로 물러난다**([17번](../17-block-formatting-context/2-summary.md))

- ★ **「빠진다」의 대상은 블록 배치다.** 형제 블록들은 float 가 없는 것처럼 자리를 잡는다.
- ★ **「민다」의 대상은 행 상자다.** 그 블록들 안의 **줄만** 비켜 간다.
- 그래서 **배경색을 주면 겹쳐 보인다** — 배경은 상자의 것이고 상자는 안 밀렸기 때문이다.
- 이것이 [17번](../17-block-formatting-context/2-summary.md)의 「보통 상자는 안 밀린다 — 글줄만 밀린다」와 같은 사실이다. 여기서는 **float 쪽에서** 본 것이다.

비용 — 공짜지만 **레이아웃이 두 겹으로 읽힌다.** `rect` 하나만 보고 디버깅하면 영원히 원인을 못 찾는다.

### (2) float 는 상자를 블록으로 바꾸고 폭을 줄인다

**언제 쓰나** — `<span>` 에 float 를 걸었을 때. 그리고 폭을 안 줬을 때.

```text
  float 를 걸면 상자가 두 번 바뀐다

  <span>  ──(① 블록화)──> 바깥 display 가 block 이 된다
                              ↓
          ──(② 축소 맞춤)──> 폭이 「내용만큼, 단 컨테이너를 못 넘게」로 정해진다
```

*(Chrome 151 headless 실측 — 폭 300 컨테이너. 짧은 글 `<span>` 에 `float:left` → 계산값 `display`가 **`block`**, `rect.width` **25.77**. 아주 긴 글 → **300 에서 멈췄다**(컨테이너 폭). 블록 요소를 float → **168** — 폭 300 을 다 쓰지 않고 **내용만큼**으로 줄었다.)*

> **축소 맞춤(shrink-to-fit)** — 「내용이 원하는 만큼, 단 쓸 수 있는 폭을 넘지 않게」 폭을 정하는 방식.\
> 예: float 한 블록이 `width: auto` 인데도 부모 폭을 다 안 쓰고 글자 폭만큼만 차지하는 것.

- ★ **float 를 걸면 `display: inline` 이 `block` 이 된다.** 그래서 `<span>` 에도 `width`·`height` 가 먹기 시작한다([19번](../19-inline-formatting-context/2-summary.md)에서 안 먹던 그 `<span>` 이다).
- **폭을 안 주면 축소 맞춤**이라 블록이어도 한 줄을 다 안 쓴다. 「float 를 줬더니 갑자기 좁아졌다」의 원인이다.
- **세로 마진이 상쇄되지 않는다**([18번](../18-margin-collapsing/2-summary.md)) — 실측에서 `margin: 30px 0` 인 float 둘이 나란히 y=31 에 놓이고 컨테이너 높이가 **102**(30+40+30+테두리 2)였다.

```html demo
<p>앞 <span class="plain">보통 span</span> 뒤</p>
<p>앞 <span class="fl">float 한 span</span> 뒤</p>
<style>
  p { display: flow-root; width: 260px; font: 13px/20px system-ui;
      border: 1px solid #333; margin: 0 0 10px; }
  span { background: #93c5fd; width: 200px; height: 44px; }
  span.fl { float: left; background: #fca5a5; }
</style>
```

> **보이는 것** — 위 문단의 파란 `<span>` 은 **글자 폭 그대로**이고 높이도 한 줄이다(`width`·`height` 가 안 먹었다). 아래 문단의 분홍 `<span>` 은 **200×44 짜리 네모**가 되어 왼쪽에 붙고, 「앞」·「뒤」 글자가 그 오른쪽으로 밀려 있다.\
> **바꿔 볼 것** — `.fl` 의 `float: left` → `float: right` (네모가 오른쪽에 붙고 글자가 왼쪽에 남는다) · `.fl` 의 `width`·`height` 를 지우면 **글자 폭만큼으로 줄어든다**(축소 맞춤)

### (3) 여러 개를 띄우면 줄 서고, 자리가 모자라면 내려간다

**언제 쓰나** — 카드 목록을 float 로 깔 때(옛 그리드 관용구).

```text
  폭 300 컨테이너에 120px float 셋

  +--------------------------------+
  | [float 1 ][float 2 ]           |   1,2 는 같은 줄 (120+120 = 240 ≤ 300)
  | [float 3 ]                     |   3 은 자리가 모자라 다음 줄
  +--------------------------------+
```

*(Chrome 151 headless 실측 — 폭 300 에 120px float 셋: 1번 (1,1) · 2번 (121,1) · 3번 **(1,41)** 으로 내려갔다. 컨테이너 높이 82. `float: right` 를 하나 더 붙이면 둘째 줄 **오른쪽 끝 (181,41)** 에 붙는다.)*

```html demo
<div class="col"><i>1</i><i>2</i><i>3</i><i class="r">right</i></div>
<style>
  .col { display: flow-root; width: 300px; border: 1px solid #333; font: 12px/40px system-ui; }
  .col i { float: left; width: 120px; height: 40px; background: #93c5fd;
           font-style: normal; text-align: center; }
  .col i.r { float: right; background: #fca5a5; }
</style>
```

> **보이는 것** — 첫 줄에 파란 상자 `1`·`2` 가 왼쪽부터 붙어 서고, **셋째부터는 자리가 모자라 둘째 줄로 내려간다.** 둘째 줄에는 파란 `3` 이 **왼쪽 끝**에, 분홍 `right` 가 **오른쪽 끝**에 붙는다 — 가운데는 빈다.\
> **바꿔 볼 것** — `.col` 의 `width` 를 `500px` 로 키우면 **넷이 한 줄에 들어간다** · `.col i.r` 의 `float: right` → `float: left` (분홍도 왼쪽 줄서기에 합류한다)

- **`float: right` 는 반대쪽에 붙는다.** 실측에서 폭 120 짜리가 x=181(= 301 − 120)에 놓였다.
- **논리 값도 있다** — `inline-start`/`inline-end`. 실측에서 계산값이 그대로 유지되고 `inline-end` 가 오른쪽(x=181)에 붙었다. 글쓰기 방향이 바뀌면 좌우가 따라 뒤집힌다([목록의 **32번 주제**](../32-logical-properties-and-writing-mode/)).
- ★ **이 배치가 옛 그리드였다.** 높이가 제각각이면 **다음 줄이 엉뚱한 곳에 걸리는** 문제가 있었고, 그래서 [flex](../24-flexbox-axes/2-summary.md)·grid 가 나왔다.

### (4) `clear` 는 마진이 아니라 「빈틈」을 만든다

**언제 쓰나** — float 아래에서 시작하고 싶은 블록이 있을 때.

```text
  float L (높이 70) · float R (높이 40) 이 있는 컨테이너

  clear 없음      clear: right     clear: left / both
  +----------+    +----------+     +----------+
  |[L][ R  ] |    |[L][ R  ] |     |[L][ R  ] |
  |[대상 y=1]|    |[L]       |     |[L]       |
  |[L]       |    |[대상y=41]|     |[L]       |
  +----------+    +----------+     |[대상y=71]|
                                   +----------+
```

*(Chrome 151 headless 실측 — 대상 블록의 컨테이너 안 y 좌표. `clear` 없음 **1** · `left` **71** · `right` **41** · `both` **71**. L 의 밑변이 71, R 의 밑변이 41 이다.)*

★ **`clear` 가 만드는 것은 마진이 아니다.** 「빈틈(clearance)」이라는 별도의 값이다.

```text
  clear: left + margin-top: 10px   → 실측 y = 71   (마진 10 이 아니라 float 아래로)
  clear: left + margin-top: 120px  → 실측 y = 121  (float 아래 71 보다 마진이 더 크다)

  둘 다 getComputedStyle().marginTop 은 선언한 값 그대로다 (10px / 120px)
```

- **둘 중 더 아래쪽으로 간다.** float 아래로 내려가야 할 만큼과 마진만큼 중 **큰 쪽**이 이긴다.
- ★ **마진 값은 안 바뀐다** — 실측에서 `marginTop` 계산값이 `10px` 그대로였는데 상자는 71 에 있었다. **계산값만 보면 「마진이 안 먹었다」로 오진한다.**
- 빈틈이 끼면 그 자리의 **마진 상쇄가 깨진다**([18번](../18-margin-collapsing/2-summary.md)).

```html demo
<div class="col">
  <div class="f">float 60</div>
  <p>이 문단은 clear 가 없어 float 옆으로 흐른다.</p>
  <p class="c">이 문단은 clear: left 라 float 아래에서 시작한다.</p>
</div>
<style>
  .col { display: flow-root; width: 260px; border: 1px solid #333; font: 13px/20px system-ui; }
  .f { float: left; width: 100px; height: 60px; background: #93c5fd; }
  .col p { margin: 0; background: #fde68a; }
  .col p.c { clear: left; background: #fca5a5; }
</style>
```

> **보이는 것** — 노란 문단은 파란 float 오른쪽에서 시작하고 **노란 배경은 float 밑으로 깔린다.** 분홍 문단은 **파란 상자보다 아래에서** 시작해 컨테이너 왼쪽 끝부터 폭 전체를 쓴다 — 파란 상자와 겹치는 부분이 없다.\
> **바꿔 볼 것** — `.col p.c` 의 `clear: left` → `clear: right` (**아무 일도 안 일어난다** — 오른쪽 float 가 없다) · 거기에 `margin-top: 100px` 추가 (float 아래 위치보다 마진이 더 크면 **마진이 이긴다**)

### (5) 높이 붕괴 — 왜 일어나는가

**언제 쓰나** — float 만 들어 있는 부모의 높이가 0 이 될 때. ★ **여기서는 「왜」까지만 본다. 고치는 법은 [17번](../17-block-formatting-context/2-summary.md)이 정본이다.**

```text
  보통 부모                              부모가 BFC 루트일 때
  +====================+ 테두리만 남음   +--------------------+
  |[float 60]          |  높이 4         |  [float 60]        |  높이 64
  +====================+                 |                    |
        ↓ float 가 밖으로 삐져나온다      +--------------------+
   [다음 형제]가 float 밑을 뚫고 지나감      float 를 끌어안는다
```

- **float 는 부모의 높이 계산에 참여하지 않는다.** 그것이 float 의 정의다 — 흐름에서 빠졌기 때문이다.
- 그래서 「높이가 0 이다」는 **버그가 아니라 규칙대로 된 것**이다.
- **막는 법(= BFC 를 여는 것)과 그 부작용 대조는 [17번](../17-block-formatting-context/2-summary.md)이 정본이다.** 실측 수치(보통 부모 `rect.height` **4**, `flow-root` **64**)도 거기 있다.

### (6) flex·grid 항목에서는 float 가 아무것도 안 한다

**언제 쓰나** — 옛 CSS 를 flex 로 옮기다가 `float` 선언이 남았을 때.

*(Chrome 151 headless 실측 — `display: flex` 컨테이너의 첫 항목에 `float: left` 를 준 것과 안 준 것을 나란히 쟀다.)*

```text
                     계산값 float   rect.x   rect.width   형제의 x
  float 선언 없음        none        1.0        8.52         9.5
  float: left           left        1.0        8.52         9.5
                         ↑           ↑———— 한 픽셀도 안 다르다 ————↑
```

- ★ **계산값은 `left` 인데 배치는 하나도 안 바뀌었다.** 진단 3창의 셋째 창이 「담겼다」고 말해도 **수행은 안 된** 자리다.
- [17번](../17-block-formatting-context/2-summary.md)의 표가 「flex 항목은 `float` 선언 자체가 무시된다」고 적은 것이 이것이다. 여기서는 **float 쪽에서** 같은 사실을 확인했다.

## 문법 — 형태와 어디서 헷갈리나

### 최소 형태

```css
.img  { float: left; width: 120px; }   /* 왼쪽에 붙이고 글이 오른쪽을 감싼다 */
.below{ clear: both; }                 /* 위쪽 float 전부 아래에서 시작 */
```

값은 `float` 이 `left`·`right`·`none`·`inline-start`·`inline-end`, `clear` 가 `left`·`right`·`both`·`none`·`inline-start`·`inline-end` 다.

### 헷갈리는 자리 ① — `clear` 는 자기 자신에게 건다

```text
  ✗ float 에 clear 를 걸어 「다음 것이 내려오게」 하려 한다
  ✓ 내려가야 할 그 요소에 clear 를 건다

  <div class="f">float</div>
  <div class="next" style="clear: left">내가 내려간다</div>
```

### 헷갈리는 자리 ② — 「무엇이 안 밀리나」

```text
  밀리는 것        행 상자(글줄) · 인라인 상자 · 인라인 배경
  안 밀리는 것     블록 상자 자체 · 그 배경 · 그 테두리
  그래서           배경을 주면 겹쳐 보인다 (rect 로는 못 잡는다)
```

### 금지에 가까운 형태

```css
.grid-item { float: left; width: 33.33%; }  /* 옛 그리드 — 오늘은 flex/grid */
.parent::after { content:""; display:block; clear:both; }  /* 옛 clearfix — 17번이 정본 */
.flex-item { float: left; }                 /* 아무 일도 안 일어난다 (6) */
```

## 구현 세부사항 대 언어 보장

- **「float 는 높이 계산에 참여하지 않는다」·「행 상자만 비켜 간다」는 명세다.** CSS2 의 부동 규정이 근거이고 이 브라우저 실측이 그것과 맞았다.
- **`float` 가 상자를 블록화한다는 것도 명세**(CSS Display Level 3 의 blockification)다. 실측에서 `<span>` 의 계산값 `display` 가 `block` 이었다.
- ★ **`float` 의 계산값이 flex 항목에서도 `left` 로 남는 것은 이 브라우저에서 관찰한 것**이다. 명세가 말하는 것은 「부동을 만들지 않는다」이지 「계산값이 `none` 이 된다」가 아니다 — **관찰은 관찰로 적는다.**
- ★ **축소 맞춤이 정확히 몇 px 이 되느냐는 폰트가 정한다.** 실측 25.77·168 은 이 머신의 글꼴에서 나온 값이다.
- **스크롤바 폭·글자 폭이 섞인 수치는 전부 구현 세부**다. 외울 것은 수치가 아니라 **「내용만큼, 단 컨테이너를 못 넘게」라는 규칙**이다.

## 어디서 틀리나

### 1. 「float 가 형제 블록을 밀어낸다」고 안다

**안 민다.** (1) 실측에서 다섯 형제가 전부 `x=1 · width=300` 이었다.\
밀린 것은 **그 블록들 안의 줄**뿐이다. 배경색을 주면 겹침이 바로 보인다.

### 2. 높이가 0 이 된 것을 버그로 본다

**규칙대로 된 것**이다((5)). 고치는 법은 [17번](../17-block-formatting-context/2-summary.md) — `display: flow-root` 한 줄이다.

### 3. `clear` 를 float 쪽에 건다

`clear` 는 **자기가 내려가는** 선언이다. 내려가야 할 요소에 건다.

### 4. `clear` 가 마진이라고 생각한다

빈틈(clearance)은 **별도의 값**이라 `marginTop` 계산값이 안 바뀐다((4) 실측: 계산값 `10px` 인데 y=71).\
「마진을 10 줬는데 60 이 벌어졌다」를 마진 상쇄로 오진하기 쉽다.

### 5. float 에 폭을 안 주고 「블록이니 한 줄을 다 쓰겠지」 한다

**축소 맞춤이라 안 쓴다**((2) 실측: 블록 요소를 float 했더니 300 이 아니라 168).

### 6. flex 로 옮기고 `float` 선언을 남겨 둔다

**아무 일도 안 하지만 계산값에는 남아** 다음 사람이 「이게 뭘 하나」를 한참 본다((6)).

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 고르는 것 | 왜 |
|---|---|---|
| **글이 이미지를 감싸 돌게 한다** | `float` | ★ **오늘 float 만 할 수 있는 유일한 일**이다 |
| 첫 글자를 크게 빼서 글이 감싸게 한다 | `float` + [`::first-letter`](../13-pseudo-elements-and-generated-content/2-summary.md) | 같은 이유 |
| 카드·칼럼을 나란히 놓는다 | [flex](../24-flexbox-axes/2-summary.md) / grid | float 는 높이가 다르면 줄이 엉킨다 |
| 사이드바 레이아웃 | grid | 옛 float 레이아웃의 자리 |
| float 아래에서 시작하게 한다 | `clear` | 이건 여전히 float 의 짝이다 |
| float 를 감싸 높이를 살린다 | `display: flow-root` | [17번](../17-block-formatting-context/2-summary.md)이 정본 |
| 흐름에서 **완전히** 빼고 좌표로 놓는다 | `position: absolute` | 줄도 안 민다([21번](../21-position-and-containing-block/2-summary.md)) |

판단 규칙 두 줄.

- **「글이 감싸 돌아야 하나?」가 유일한 판정 질문이다.** 그렇다 → float, 아니다 → flex/grid.
- **float 가 남아 있는 옛 코드는 대개 레이아웃 용도다.** 그건 옮기고, 감싸기만 남긴다.

## 핵심 문장

- float 는 **흐름에서 빠지되 글줄은 민다.** 빠지는 것은 **블록 배치**, 미는 것은 **행 상자**다.
- ★ **형제 블록은 한 픽셀도 안 움직인다**(실측 `x=1 · width=300` 다섯 개). 그래서 **배경이 float 밑으로 깔려 겹쳐 보인다.**
- float 는 상자를 **블록화**하고 폭을 **축소 맞춤**으로 정한다 — `<span>` 도 블록이 되고, 블록도 좁아진다.
- **높이 붕괴는 float 의 정의에서 나온다**(높이 계산에 참여하지 않는다). **막는 법은 [17번](../17-block-formatting-context/2-summary.md)이 정본.**
- ★ **`clear` 는 마진이 아니라 빈틈**이다 — `marginTop` 계산값은 안 바뀌는데 상자는 내려간다.
- **flex·grid 항목에서 `float` 는 아무것도 안 한다** — 계산값은 `left` 로 남는데 배치는 한 픽셀도 안 바뀌었다(실측).
- 오늘 float 에 남은 일은 **글이 감싸 도는 것 하나**다.

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 20번)
- [17번 주제](../17-block-formatting-context/2-summary.md)(BFC) — ★ **높이 붕괴를 막는 법과 수단별 부작용 대조가 정본**이다. 여기는 **왜 붕괴가 일어나는가**까지다
- [19번 주제](../19-inline-formatting-context/2-summary.md)(인라인 서식 문맥) — **float 가 미는 그 「행 상자」가 무엇인지**는 거기. 여기는 **무엇이 미나**다
- [21번 주제](../21-position-and-containing-block/2-summary.md)(`position` 과 포함 블록) — **흐름에서 완전히 빠지는 쪽.** float 와의 대비가 이 주제의 좌표계다
- [18번 주제](../18-margin-collapsing/2-summary.md)(마진 상쇄) — float 는 **상쇄에 참여하지 않는다**. 그 규칙의 정본
- [24번 주제](../24-flexbox-axes/2-summary.md)(Flexbox) — **레이아웃 용도의 float 를 대체한 것.** 축·정렬은 거기가 정본
- [`history/web/03-HTML-CSS-진화.md`](../../../../../../history/web/03-HTML-CSS-진화.md) — 테이블·float 레이아웃 시대와 그 탈출. **왜 그 시절에 float 로 레이아웃을 했나**는 거기, 여기는 **오늘의 규칙**이다
- [목록의 **32번 주제**](../32-logical-properties-and-writing-mode/)(논리 속성과 글쓰기 방향) — `float: inline-start` 가 방향에 따라 뒤집히는 규칙
- [`reference/render-rules.md`](../../../../../../reference/render-rules.md) — 이 문서의 `demo` 블록 규칙

## 용어 풀이

- **부동(float)** — 상자를 컨테이너 한쪽 끝에 붙이고 **행 상자가 그 옆을 흐르게** 하는 것.
- **해제(clear)** — 자기 위쪽 float 아래에서 시작하라는 지시. **자기 자신에게 거는 선언**이다.
- **빈틈(clearance)** — `clear` 가 만드는 별도의 세로 간격. **마진이 아니다** — 계산값 `marginTop` 은 안 바뀐다.
- **보통 흐름(normal flow)** — 블록은 위아래로, 인라인은 줄을 따라 놓이는 기본 배치.
- **흐름에서 빠진다(out of flow)** — 형제들의 자리 계산에 참여하지 않는 상태. float 와 `absolute`/`fixed` 가 여기 속한다.
- **축소 맞춤(shrink-to-fit)** — 「내용만큼, 단 쓸 수 있는 폭을 넘지 않게」 폭을 정하는 방식. float 의 기본 폭 계산이다.
- **블록화(blockification)** — 어떤 선언 때문에 상자의 바깥 `display` 가 `block` 으로 강제되는 것. `float` 와 `absolute` 가 그렇게 만든다.
- **높이 붕괴(height collapse)** — 안에 float 만 있는 상자의 높이가 0 이 되는 현상. 막는 법은 [17번](../17-block-formatting-context/2-summary.md).
- **`shape-outside`** — float 를 감싸는 모양을 사각형 말고 원·다각형 등으로 바꾸는 속성. **이 주제 밖이라 이름만 적는다.**

---

## 더 들어가면

- **float 는 「인라인 서식 문맥에만 영향을 주는 유일한 흐름 밖 상자」다.** `absolute`·`fixed` 는 줄도 안 민다([21번](../21-position-and-containing-block/2-summary.md)). 이 차이가 **「흐름에서 얼마나 떨어져 나갔나」의 눈금**이다.
- **float 는 마크업 순서보다 뒤로는 못 올라간다.** 자기 앞 형제들이 만든 줄 위로는 못 올라가므로, 「오른쪽 사진을 문단보다 먼저 쓰라」는 옛 관용구가 여기서 나왔다.
- **float 는 float 를 피한다.** (3)에서 셋째가 내려간 것이 그 규칙이고, 그래서 float 끼리는 겹치지 않는다. 반면 `absolute` 끼리는 겹친다.
- **`clear` 에도 논리 값이 있다**(`inline-start`/`inline-end`). `float` 와 짝을 맞춰 쓰면 글쓰기 방향이 바뀌어도 그대로 동작한다([목록의 **32번 주제**](../32-logical-properties-and-writing-mode/)).

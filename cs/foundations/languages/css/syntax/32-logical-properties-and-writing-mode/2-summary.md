# css/syntax/32 — 논리 속성과 글쓰기 방향(`writing-mode`·`direction`·`inline-size`) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [CSS Logical Properties and Values Level 1](https://drafts.csswg.org/css-logical-1/) (논리 속성과 물리 속성의 대응·캐스케이드 규칙) · [CSS Writing Modes Level 4](https://drafts.csswg.org/css-writing-modes-4/) (`writing-mode`·`direction`·인라인/블록 축의 정의). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 좌표·치수는 **Google Chrome 151.0.7922.173** headless 에 실제로 띄워 `getBoundingClientRect()` 로 잰 값이고, **논리 속성이 어느 물리 속성으로 풀렸는지는 `getComputedStyle` 로 따로 읽었다.**\
> **WebKit(Safari)은 이 머신에 없고 Firefox 는 이 환경에서 headless 스크린샷이 산출되지 않는다** — 엔진 차이는 주장하지 않는다.
> **버전** — 논리 속성은 Baseline **widely**(newly 2021-09-20 → widely 2024-03-20) · `writing-mode` 는 **widely**(2017-03-27 → 2019-09-27) · `text-align` 은 **widely**(2015-07-29 → 2018-01-29). 전부 `api.webstatus.dev` 조회값이다. ★ **이미 기본으로 쓸 수 있는 표면이다.**
> **여기서 다루지 않는 것** — 유니코드·문자 인코딩은 [`foundations/data-representation/`](../../../../data-representation/)이 정본이다. flex 의 축·정렬은 [24번](../24-flexbox-axes/), 박스 모델은 [15번](../15-box-model-and-box-sizing/)이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 수치는 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**「가로/세로」가 아니라 「글이 흐르는 쪽 / 줄이 쌓이는 쪽」이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 공책에 글씨를 쓸 때 **펜이 나아가는 방향** | **인라인 축(inline axis)** — `writing-mode` 와 `direction` 이 정한다 |
| 한 줄을 다 쓰고 **다음 줄로 옮겨 가는 방향** | **블록 축(block axis)** |
| 펜이 처음 놓이는 자리 | **inline-start** |
| 첫 줄이 놓이는 자리 | **block-start** |
| 공책을 90도 돌려 세로로 쓰는 것 | `writing-mode: vertical-rl` |
| 오른쪽에서 왼쪽으로 쓰는 언어 | `direction: rtl` |
| 「왼쪽 여백」이 아니라 「펜이 시작하는 쪽 여백」 | `margin-inline-start` |

- **물리 속성**(`width`·`margin-left`·`top`)은 **화면의 방향**을 가리킨다. 공책을 돌려도 안 따라 돈다.
- **논리 속성**(`inline-size`·`margin-inline-start`·`inset-block-end`)은 **글의 방향**을 가리킨다. 공책을 돌리면 **같이 돈다.**
- ★ **`writing-mode` 한 줄을 바꾸면 나머지 CSS 를 한 글자도 안 건드리고 레이아웃이 통째로 90도 돈다** — 논리 속성으로만 썼을 때의 이야기다.
- ★ [24·25·26번](../24-flexbox-axes/)이 쓴 **「주축」이 바로 이 축**이다. `flex-direction: row` 는 「가로」가 아니라 **「인라인 축」** 이다.

```text
horizontal-tb (한국어 가로쓰기 · 기본)        vertical-rl (세로쓰기)
+----------------------------------+        +----------------------------------+
| inline-start ───펜──> inline-end  |        |            block-start ← ... ────+
|                                  |        |   │                              |
| block-start                      |        |   │ 인라인 축 (펜이 내려간다)       |
|   │ 블록 축 (줄이 내려간다)         |        |   ▼                              |
|   ▼                              |        |            inline-end             |
+----------------------------------+        +----------------------------------+
 인라인 축 = 가로 · 블록 축 = 세로              인라인 축 = 세로 · 블록 축 = 가로(오른쪽→왼쪽)
```

실무에서 이게 터지는 자리는 **다국어 사이트의 RTL 전환**이다.\
`margin-left: 16px` 로 짜 놓은 아이콘 여백이 아랍어 페이지에서 **반대쪽에 남아** 글자와 붙는다.\
`margin-inline-start: 16px` 였다면 **한 글자도 안 고치고** 따라 돌았을 것이다 — (2)가 그 실측이다.

> **인라인 축(inline axis)** — 글자가 이어지는 방향의 축. 한국어 가로쓰기에서는 가로, 세로쓰기에서는 세로다.\
> 예: `inline-size` 는 가로쓰기에서 `width`, 세로쓰기에서 `height` 로 풀린다.

> **블록 축(block axis)** — 줄(문단)이 쌓이는 방향의 축. 인라인 축에 직각이다.\
> 예: `block-size` 는 가로쓰기에서 `height`, 세로쓰기에서 `width` 로 풀린다.

> **`writing-mode`** — 인라인 축과 블록 축을 **둘 다** 정한다. `horizontal-tb`(기본) · `vertical-rl` · `vertical-lr` 등.\
> 예: `vertical-rl` 은 「글은 세로로 내려가고 줄은 오른쪽에서 왼쪽으로 쌓인다」.

> **`direction`** — **인라인 축 안에서의 시작 쪽**만 정한다. `ltr`(기본) · `rtl`.\
> 예: 가로쓰기 + `rtl` 이면 인라인 축은 여전히 가로인데 시작이 오른쪽이 된다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **똑같은 선언**이 `writing-mode`·`direction` 에 따라 화면의 **어느 방향**으로 가는가.
2. 물리 속성과 논리 속성을 **같이 쓰면** 무슨 일이 일어나는가.
3. flex 의 **주축**은 `writing-mode` 에서 어떻게 도는가.

## 동작 방식

### (1) 축이 정해지는 순서 — `writing-mode` 가 먼저, `direction` 이 그 위에서

**언제 쓰나** — `inline-start` 가 화면 어디인지 판단할 때.

```text
① writing-mode        인라인 축과 블록 축을 **둘 다** 정한다
     horizontal-tb    인라인 = 가로      블록 = 세로(위→아래)
     vertical-rl      인라인 = 세로      블록 = 가로(오른쪽→왼쪽)
     vertical-lr      인라인 = 세로      블록 = 가로(왼쪽→오른쪽)
        ↓
② direction           **인라인 축 안에서만** 시작 쪽을 정한다
     ltr              인라인 축의 앞쪽부터
     rtl              인라인 축의 뒤쪽부터
        ↓
③ 네 지점            inline-start / inline-end / block-start / block-end
        ↓
④ 논리 속성이 ③의 이름으로 동작한다
     inline-size · block-size
     margin-inline-start · padding-block-end · border-inline · inset-block-end …
        ↓
⑤ 엔진이 각 요소에서 ③을 물리 방향으로 풀어 레이아웃한다
```

그림 해설 (한 단계씩):

- **둘은 다른 축을 만진다.** `writing-mode` 는 축 두 개를 통째로 정하고, `direction` 은 **인라인 축 안에서만** 앞뒤를 바꾼다.
- 그래서 `vertical-rl` + `rtl` 은 **세로 인라인 축을 아래→위로** 돌린다. 둘을 곱해야 답이 나온다((3)).
- ⑤가 핵심이다 — **논리 속성은 상속되는 값이 아니라 요소마다 그 자리에서 풀린다.** 부모가 세로쓰기여도 자식이 `horizontal-tb` 면 자식은 가로 기준이다.

비용 — 없다. 푸는 일은 계산값 단계에서 끝난다.

### (2) ★ 똑같은 선언, 다섯 판 — 무엇이 어디로 갔나

**언제 쓰나** — 논리 속성이 실제로 무엇으로 풀리는지 볼 때. **이 주제의 본체다.**

부모(300×200)에 자식 하나를 넣고 **자식의 선언을 한 글자도 안 바꾼 채** 부모의 `writing-mode`/`direction` 만 바꿔 쟀다.

```css
/* 다섯 판 모두 똑같이 걸린 선언 */
inline-size: 100px;  block-size: 40px;
margin-inline-start: 20px;  margin-block-start: 10px;
border-inline-start: 6px solid;  padding-inline-end: 8px;
```

```text
판                             상자 (x,y)   w × h    물리로 풀린 값
① horizontal-tb + ltr          (20,10)     114×40    width=100  height=40
                                                      margin-left=20  margin-top=10
                                                      border-left=6   padding-right=8
② writing-mode: vertical-rl    (250,20)     40×114   width=40   height=100
                                                      margin-top=20   margin-right=10
                                                      border-top=6    padding-bottom=8
③ writing-mode: vertical-lr    (10,20)      40×114   width=40   height=100
                                                      margin-left=10  margin-top=20
                                                      border-top=6    padding-bottom=8
④ direction: rtl               (166,10)    114×40    width=100  height=40
                                                      margin-top=10   margin-right=20
                                                      border-right=6  padding-left=8
⑤ vertical-rl + direction: rtl (250,66)     40×114   width=40   height=100
                                                      margin-right=10 margin-bottom=20
                                                      border-bottom=6 padding-top=8
```

*(Chrome 151 headless 실측 — 부모에 `display: flow-root` 를 줘서 [18번](../18-margin-collapsing/)의 마진 상쇄가 좌표를 흐리지 않게 했다. 물리 값은 `getComputedStyle` 로 읽은 것이고, 상자 좌표는 `getBoundingClientRect()` 로 잰 것이다.)*

```text
한 선언이 어떻게 도는지 하나만 따라가 보면 — margin-inline-start: 20px

  ① horizontal-tb + ltr    ->  margin-left   (펜이 왼쪽에서 시작)
  ② vertical-rl            ->  margin-top    (펜이 위에서 시작)
  ③ vertical-lr            ->  margin-top    (펜이 위에서 시작)
  ④ direction: rtl         ->  margin-right  (펜이 오른쪽에서 시작)
  ⑤ vertical-rl + rtl      ->  margin-bottom (펜이 아래에서 시작)

  네 물리 방향을 **전부** 한 번씩 돌았다.
```

```html demo
<div class="p"><b>A</b></div>
<div class="p v"><b>A</b></div>
<style>
  .p { display: flow-root; width: 300px; height: 120px; background: #eee;
       margin-bottom: 8px; font: 16px monospace; }
  .p > b { display: block; font-weight: 400; background: #bfdbfe;
           inline-size: 100px; block-size: 40px;        /* 폭·높이가 아니다 */
           margin-inline-start: 20px;                   /* 왼쪽 여백이 아니다 */
           border-inline-start: 6px solid #c00; }
  .v { writing-mode: vertical-rl; }                     /* 이 한 줄만 다르다 */
</style>
```

> **보이는 것** — 위 상자에서는 파란 블록이 **가로로 긴 직사각형**이고 **왼쪽에 빨간 줄**이 붙어 있다. 아래 상자에서는 같은 블록이 **세로로 긴 직사각형**이 되고 **빨간 줄이 위쪽**으로 옮겨 가며, 블록 자체가 **부모의 오른쪽 끝**에 붙는다. 자식의 선언은 한 글자도 다르지 않다.\
> **바꿔 볼 것** — `.v` 의 `vertical-rl` → `vertical-lr` → 블록이 **부모의 왼쪽 끝**으로 간다(줄이 쌓이는 방향이 반대) · `.v` 를 `direction: rtl` 로 → **가로인 채로 오른쪽으로 옮겨 가고**(20px 여백을 오른쪽에 남긴다) **빨간 줄이 오른쪽**으로 간다

*(Chrome 151 headless 실측 — 이 블록 그대로(위 표와 달리 `padding-inline-end` 가 없다): 위 판은 상자 (20,0)·106×40 이고 계산값이 `width=100px height=40px margin-left=20px border-left=6px`, 아래 판은 상자 (260,20)·40×106 이고 계산값이 `width=40px height=100px margin-top=20px border-top=6px` 다. **`margin-left` → `margin-top`, `border-left` → `border-top` 으로 옮겨 간 것**이 이 demo 가 보여 주려는 하나다.\
★ 「바꿔 볼 것」 둘도 돌려 봤다 — `vertical-lr` 은 상자 **(0,20)**·40×106 에 `border-top=6px`(왼쪽 끝), `direction: rtl` 은 상자 **(174,0)**·106×40 에 **오른끝 280**(20px 여백을 오른쪽에 남긴다)·`border-right=6px` 다.)*

그림 해설 (한 단계씩):

- **선언은 하나도 안 바꿨다.** 바뀐 것은 부모의 `writing-mode`/`direction` 한 줄뿐이다.
- `inline-size: 100px` 가 ①에서는 `width`, ②에서는 `height` 로 풀렸다 — **`inline-size` 는 「폭」이 아니다.**
- `border-inline-start` 가 ①에서 `border-left`, ②·③에서 `border-top`, ④에서 `border-right`, ⑤에서 `border-bottom` 이 됐다.
- ★ **`getComputedStyle` 은 논리 속성을 물리 속성으로 풀어서 돌려준다.** 그래서 「내 논리 선언이 어디로 갔나」를 **물어볼 수 있다** — 이 주제의 진단 방법이다.

비용 — 없다. 물리 속성과 성능 차이가 없다.

### (3) `direction` 과 `writing-mode` 는 다른 축이다

**언제 쓰나** — 둘을 같이 쓸 때. 「둘 다 방향을 바꾸는 속성」으로 뭉뚱그리면 틀린다.

```text
writing-mode 가 바꾸는 것            direction 이 바꾸는 것
+---------------------------+       +---------------------------+
| 인라인 축이 가로냐 세로냐   |       | 인라인 축의 **시작이 어느 쪽**|
| 블록 축이 가로냐 세로냐     |       | (축 자체는 안 바꾼다)        |
+---------------------------+       +---------------------------+
        축을 고른다                        축 위에서 앞뒤를 고른다
```

```text
네 조합을 실제로 재면 (같은 선언, 상자 (x,y))

                     ltr                    rtl
horizontal-tb   ① (20,10)  가로 상자     ④ (166,10)  가로 상자
                   왼쪽에서 시작              오른쪽에서 시작
vertical-rl     ② (250,20) 세로 상자     ⑤ (250,66)  세로 상자
                   위에서 시작                아래에서 시작
```

*(Chrome 151 headless 실측 — (2)의 표에서 뽑았다. ②와 ⑤는 **x 가 250 으로 같고 y 만 다르다** — `direction` 이 블록 축(가로 위치)은 안 건드리고 인라인 축(세로 위치)만 뒤집었다는 증거다.)*

- ★ **②와 ⑤의 x 가 같다는 것이 「다른 축」의 증거**다. `direction` 은 블록 축에 손대지 않는다.
- 그래서 **아랍어 가로쓰기**는 `direction: rtl` 이고, **일본어 세로쓰기**는 `writing-mode: vertical-rl` 이며, 둘은 **독립적으로 조합된다.**
- `direction` 은 HTML 의 `dir` 속성으로도 정해진다. **실무에서는 CSS 가 아니라 `<html dir="rtl">` 로 주는 것이 표준**이다(스크린 리더·폼 컨트롤까지 따라오기 때문).

### (4) ★ 물리 속성과 논리 속성을 같이 쓰면

**언제 쓰나** — 기존 코드에 논리 속성을 섞어 넣을 때. **여기서 사고가 난다.**

같은 요소에 둘을 같이 걸고 다섯 판을 쟀다.

```text
판                                                          상자 x   계산값
① ltr: margin-inline-start:20 → margin-left:80 (물리가 뒤)     80     margin-left=80
② ltr: margin-left:80 → margin-inline-start:20 (논리가 뒤)     20     margin-left=20
③ rtl: margin-inline-start:20 → margin-left:80                220     margin-left=80
                                                                     margin-right=20
④ ltr: margin-inline-start:20 + margin-top:25                  20     margin-left=20
                                                                     margin-top=25
⑤ ltr: b{margin-left:80} + .hi{margin-inline-start:20}         20     margin-left=20
        (명시도 0,0,1 대 0,1,0)
```

*(Chrome 151 headless 실측 — 부모 300px, 상자 60px. ③의 x=220 은 300 − 60 − 20(오른쪽 마진)과 맞는다.)*

```text
두 경우로 갈린다

  같은 물리 방향으로 풀린다            다른 물리 방향으로 풀린다
  (①②⑤ — ltr 에서 inline-start = left)  (③④)
  +------------------------------+     +------------------------------+
  | **캐스케이드로 싸운다**         |     | **둘 다 산다**                 |
  | 나중 선언 / 높은 명시도가 이긴다  |     | 서로 다른 칸을 채운다           |
  +------------------------------+     +------------------------------+
     ①은 물리가 뒤라 80                     ③은 left=80, right=20 둘 다
     ②는 논리가 뒤라 20                     ④는 left=20, top=25 둘 다
     ⑤는 명시도 높은 논리가 20
```

- ★ **「논리와 물리는 캐스케이드로 안 싸운다」는 말은 틀렸다.** 같은 물리 속성으로 풀리면 **정확히 캐스케이드로 싸운다** — 순서와 명시도가 그대로 적용된다([01번](../01-cascade-and-priority/)·[02번](../02-specificity/)).
- **둘 다 사는 것은 서로 다른 물리 칸을 채울 때**뿐이다(③④).
- ③이 특히 위험하다 — `ltr` 에서는 한쪽이 지지만 **`rtl` 로 바뀌는 순간 둘 다 살아나** 양쪽에 여백이 생긴다. **언어를 바꿨더니 여백이 두 배**가 되는 사고가 이것이다.
- 실무 규칙 — **한 속성 그룹에서는 물리든 논리든 한쪽으로 통일한다.** 섞으면 언어마다 결과가 달라진다.

비용 — 없다. 다만 **점진적 전환 중인 코드베이스가 가장 위험하다.**

### (5) flex 의 주축이 `writing-mode` 에서 어떻게 도나

**언제 쓰나** — [24\~26번](../24-flexbox-axes/)의 축 이야기를 논리 축으로 다시 읽을 때.

`flex-direction: row` 를 그대로 둔 채 컨테이너의 `writing-mode` 만 바꿔 쟀다(컨테이너 200×200, 항목 40×30 둘).

```text
판                     항목 좌표                결론
horizontal-tb (기본)   1:(0,0)   2:(40,0)      **가로로 늘어섬**
writing-mode: vertical-rl  1:(160,0) 2:(160,30)  **세로로 쌓임** (오른쪽 끝에서)
writing-mode: vertical-lr  1:(0,0)   2:(0,30)    **세로로 쌓임** (왼쪽 끝에서)
direction: rtl         1:(160,0) 2:(120,0)      가로인 채로 **오른쪽부터**
```

*(Chrome 151 headless 실측 — `flex-direction: row; justify-content: flex-start; align-items: flex-start` 는 네 판 모두 똑같이 걸렸다.)*

```text
row 는 "가로"가 아니다

  flex-direction: row      ──>  주축 = **인라인 축**
  flex-direction: column   ──>  주축 = **블록 축**

  horizontal-tb 에서만 그것이 각각 가로·세로와 일치한다.
```

```html demo
<div class="pair">
  <div class="f"><i>1</i><i>2</i></div>
  <div class="f v"><i>1</i><i>2</i></div>
</div>
<style>
  .pair { display: flex; gap: 16px; font: 14px monospace; }
  .f { display: flex; flex-direction: row;      /* 두 상자 모두 row 다 */
       width: 120px; height: 120px; background: #eee; outline: 2px solid #c00; }
  .f i { display: block; font-style: normal; width: 40px; height: 30px;
         background: #bfdbfe; outline: 1px solid #333; }
  .v { writing-mode: vertical-rl; }             /* 이 한 줄만 다르다 */
</style>
```

> **보이는 것** — 왼쪽 상자에서는 칸 둘이 **가로로 나란히** 놓이고, 오른쪽 상자에서는 같은 `row` 인데 **세로로 쌓이며 상자의 오른쪽 끝**에 붙는다. `flex-direction` 은 두 상자 모두 `row` 다.\
> **바꿔 볼 것** — `.v` 의 `vertical-rl` → `vertical-lr` → 칸들이 **왼쪽 끝**으로 옮겨 간다 · `.v` 를 `direction: rtl` 로 → 다시 가로인데 **오른쪽부터** 채워진다

*(Chrome 151 headless 실측 — 이 블록 그대로(컨테이너 120×120): 왼쪽 상자 1:(0,0) 2:(40,0) — **가로**. 오른쪽 상자 1:(80,0) 2:(80,30) — **세로**이고 x=80 은 120 − 40 으로 오른쪽 끝이다. 위 표의 200×200 판과 같은 이야기를 컨테이너 크기만 바꿔 확인했다.\
★ 「바꿔 볼 것」 둘도 같은 120×120 상자로 돌려 봤다 — `vertical-lr` 은 1:(0,0) 2:(0,30)(**왼쪽 끝에서 세로로**), `direction: rtl` 은 1:(80,0) 2:(40,0)(**가로인 채로 오른쪽부터**).)*

- ★ **[24번](../24-flexbox-axes/)의 「주축」은 처음부터 논리 축이었다.** 이름이 `row`/`column` 이라 물리로 읽히지만 정의는 인라인/블록이다.
- 그래서 `justify-content: flex-start` 는 `vertical-rl` 에서 **「위」** 다. `flex-start` 가 왼쪽이 아니라는 [24번](../24-flexbox-axes/)의 이야기가 여기서 끝까지 이어진다.
- `vertical-rl` 판에서 항목이 **x=160** 인 것은 교차축(블록 축)이 오른쪽에서 시작하기 때문이다 — 200 − 40 = 160.

비용 — `writing-mode` 는 레이아웃 속성이다. 전환에 태우지 않는다([목록의 **56번 주제**](../56-rendering-pipeline-and-will-change/)).

### (6) `inset-*` — `position` 의 논리판

**언제 쓰나** — 절대 위치 요소를 다국어에서 쓸 때.

```text
inset-block-end: 10px;  inset-inline-start: 15px;   (부모 200×120)

판                    상자 (x,y)   계산값
horizontal-tb        (15, 90)     left=15px  top=90px  right=145px bottom=10px
vertical-rl          (10, 15)     left=10px  top=15px  right=150px bottom=85px
```

*(Chrome 151 headless 실측 — 같은 두 선언을 부모의 `writing-mode` 만 바꿔 걸었다.)*

```text
대응표

  물리          논리
  left         inset-inline-start   (ltr 가로쓰기에서)
  right        inset-inline-end
  top          inset-block-start
  bottom       inset-block-end
  top/bottom   inset-block   (단축)
  left/right   inset-inline  (단축)
  네 개 전부    inset         (단축 — 물리 네 방향이지만 이름이 짧다)
```

- `inset-block-end: 10px` 가 가로쓰기에서 **아래에서 10px**(y=90 = 120 − 20 − 10), 세로쓰기에서 **왼쪽에서 10px** 가 됐다.
- ★ **`inset` 단축은 논리가 아니다** — `top right bottom left` 순서의 물리 단축이다. 이름만 새것이라 헷갈린다.

### (7) `text-align: start` / `end`

**언제 쓰나** — 글 정렬을 다국어에서 쓸 때.

```text
컨테이너 200px, 글자 왼쪽 x

ltr + text-align: start    ->    0      (왼쪽 정렬)
ltr + text-align: end      ->  176      (오른쪽 정렬)
rtl + text-align: start    ->  160      (오른쪽 정렬 — start 가 오른쪽이다)
rtl + text-align: left     ->    0      (왼쪽 고정 — 물리라 안 돈다)
```

*(Chrome 151 headless 실측 — 글자 영역은 `Range.selectNodeContents()` 의 사각형으로 쟀다. 계산값은 각각 `start`·`end`·`start`·`left` 로 **선언한 그대로 남는다** — 계산값만으로는 어느 쪽으로 정렬됐는지 알 수 없다.)*

- **`start`/`end` 가 논리 값**이고 `left`/`right` 가 물리 값이다. `text-align` 은 **속성 이름은 그대로 두고 값 쪽에 논리판이 있는** 드문 경우다.
- `rtl + start` 가 160 인 것은 글자 폭(40)만큼을 뺀 오른쪽 끝이다.
- ★ **계산값은 `start` 그대로다.** 「어디로 정렬됐나」는 **좌표를 재야** 안다 — (2)의 `margin` 과 다른 점이다.

## 문법 — 형태와 어디서 헷갈리나

CSS 는 문법 표면이 단순하므로 이 절은 **어디서 헷갈리나**로 읽는다.

### 최소 형태

```css
.box {
  inline-size: 100px;          /* width  의 논리판 */
  block-size: 40px;            /* height 의 논리판 */
  margin-inline: 16px;         /* 인라인 축 양쪽 (단축) */
  padding-block-start: 8px;    /* 블록 축 시작 쪽 */
  border-inline-start: 2px solid;
  inset-block-end: 10px;       /* position 과 함께 */
}
```

### 대응표 — 가로쓰기 `ltr` 기준

| 물리 | 논리 | 세로쓰기(`vertical-rl`)에서는 |
|---|---|---|
| `width` | `inline-size` | `height` 가 된다 |
| `height` | `block-size` | `width` 가 된다 |
| `margin-left` | `margin-inline-start` | `margin-top` |
| `margin-right` | `margin-inline-end` | `margin-bottom` |
| `margin-top` | `margin-block-start` | `margin-right` |
| `margin-bottom` | `margin-block-end` | `margin-left` |
| `left` | `inset-inline-start` | `top` |
| `bottom` | `inset-block-end` | `left` |
| `text-align: left` | `text-align: start` | 값 쪽에 논리판이 있다 |

*(세로쓰기 열은 (2)·(6)의 실측에서 읽은 것이다. `margin-block-start` → `margin-right` 는 ②의 `margin-inline-start → margin-top` 과 짝을 이룬다.)*

- 단축도 다 있다 — `margin-inline`(양쪽) · `margin-block`(위아래) · `inset-inline` · `border-block` 등.
- ★ **`inset` 만 예외다** — 이름이 새것인데 **물리 단축**(`top right bottom left`)이다.

### 금지에 가까운 형태

```css
/* ① 물리와 논리를 같은 방향에 섞어 쓴다 — 언어마다 결과가 달라진다 */
.a { margin-left: 80px; margin-inline-start: 20px; }     /* (4) */

/* ② inset 을 논리 단축으로 안다 */
.b { position: absolute; inset: 10px; }                   /* 물리 네 방향이다 */

/* ③ 물리·논리를 섞은 단축이 있다고 가정한다 */
.c { margin-inline-top: 4px; }                            /* 그런 속성은 없다 */

/* ④ writing-mode 를 전환에 태운다 — 선언은 받아들여지는데 값은 즉시 끝까지 간다 */
.d { transition: writing-mode 1s linear, width 1s linear; }
```

*(Chrome 151 + CDP 실측 — `transitionProperty` 는 `"writing-mode, width"` 로 **선언을 받아들인다.** 그런데 두 값을 동시에 바꾸고 재 보면 **0.1초 시점에 `writing-mode` 는 이미 `vertical-rl`** 이고 `width` 만 210px 로 보간 중이다(0.5s 250px · 0.8s 279.984px). 키워드 값에는 중간값이 없기 때문이다 — 「전환이 걸린 것처럼 보이는데 안 걸린」 전형이다. 정본은 [52번](../52-transition/).)*

*(Chrome 151 headless 실측 — 진단 3창의 첫째 창(`cssRules`)으로 읽은 결과.\
`#L1 { }` ← `margin-inline-top: 4px`(**그런 속성이 없어** 버려짐) · `#L2 { margin-inline-start: 20px; }` ← 정상 ·\
`#L3 { }` ← `inline-size: auto-ish`(모르는 값) · `#L4 { writing-mode: sideways-rl; }` ← **담긴다**(이 Chrome 이 아는 값이다) ·\
`#L5 { inset-inline: 5px; }` · `#L6 { inset: 10px; }` ← 둘 다 유효하고, **이름만 봐서는 어느 쪽이 논리인지 구분되지 않는다**(`inset-inline` 이 논리, `inset` 이 물리).)*

*(같은 실측 — 논리 마진·패딩 여덟 개에 1\~8px 를 각각 주고 `vertical-rl` 에서 어느 물리 칸으로 갔는지 읽었다.\
`inline-start=1 · inline-end=2 · block-start=3 · block-end=4` 를 줬더니 계산값이 **`margin` 왼/위/오른/아래 = 4 / 1 / 3 / 2** 였다 —\
즉 `inline-start→top` · `inline-end→bottom` · `block-start→right` · `block-end→left`. 패딩도 5/6/7/8 이 같은 규칙으로 8 / 5 / 7 / 6 이 됐다.)*

## 구현 세부사항 대 언어 보장

| 항목 | 누가 보장하나 |
|---|---|
| 인라인 축·블록 축의 정의와 `writing-mode`/`direction` 이 각각 무엇을 정하는가 | **명세** — css-writing-modes-4 |
| 논리 속성이 물리 속성으로 **매핑되는 규칙** | **명세** — css-logical-1 §2 |
| 논리와 물리가 **같은 물리 속성으로 풀릴 때 캐스케이드로 겨루는 것** | **명세** — css-logical-1 §3(두 벌이 같은 「선언 블록」을 공유한다) |
| `inset` 이 **물리 단축**인 것 | **명세** — css-logical-1 |
| `getComputedStyle` 이 논리 속성을 **물리로 풀어** 돌려주는 것 | **명세** — 계산값 정의. 다만 `text-align: start` 처럼 **값 쪽 논리는 안 풀린다**((7)) |
| 위 표의 **구체 좌표**(250, 166, 90 …) | **이 머신의 Chrome 151 실측** |
| `sideways-rl` 이 이 Chrome 에서 담기는 것 | **구현** — 명세에 있지만 엔진마다 다를 수 있다. **담긴 것과 먹는 것은 또 다르다**([31번](../31-intrinsic-sizing-and-aspect-ratio/) §(9)와 같은 함정) |

## 어디서 틀리나

이 주제의 값어치는 대부분 여기 있다. 전부 **에러 없이 조용히 어긋난다.**

### 1. `inline-size` 를 「폭」으로 외운다

세로쓰기에서 **높이**가 된다((2)의 ②). 이름을 「폭」으로 외우면 `writing-mode` 를 만나는 순간 전부 뒤집힌다.\
올바른 기억 — **`inline-size` = 펜이 나아가는 쪽의 크기.**

### 2. `direction: rtl` 이 세로쓰기도 만든다고 생각한다

`direction` 은 **인라인 축 안에서만** 앞뒤를 바꾼다((3)). 축 자체는 `writing-mode` 가 정한다.\
실측 근거 — ②와 ⑤에서 **x 가 250 으로 같았다.**

### 3. 「논리와 물리는 안 싸운다」로 안다

**같은 물리 속성으로 풀리면 캐스케이드로 싸운다**((4)). 순서와 명시도가 그대로 적용된다.\
특히 위험한 것은 ③ — **`ltr` 에서는 한쪽이 지다가 `rtl` 에서 둘 다 살아나 여백이 양쪽에 생긴다.**

### 4. `inset: 10px` 를 논리 단축으로 안다

**물리 네 방향 단축**이다. 이름만 새것이다. 논리 단축은 `inset-inline` / `inset-block` 이다.

### 5. `text-align: start` 가 먹었는지 계산값으로 확인하려 한다

계산값은 **`start` 그대로**다((7)). 어느 쪽으로 정렬됐는지는 **좌표를 재야** 안다.

### 6. `flex-direction: row` 를 「가로」로 읽는다

`vertical-rl` 에서 **세로로 쌓인다**((5)). [24번](../24-flexbox-axes/)의 `flex-start` 가 왼쪽이 아니라는 이야기와 같은 뿌리다.

### 7. CSS 의 `direction` 으로 RTL 을 구현한다

동작은 하지만 **HTML 의 `dir` 속성이 표준**이다. 폼 컨트롤·스크린 리더·`::selection` 같은 것이 `dir` 을 본다.\
CSS 의 `direction` 은 **레이아웃만** 돌린다.

### 8. 물리 속성을 쓰고 RTL 용 스타일시트를 따로 만든다

논리 속성이 Baseline **widely**(2024-03-20)인 지금 **불필요한 중복**이다.\
옛날에 쓰던 `[dir="rtl"] .x { margin-right: … }` 패턴은 **한 줄로 대체된다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 왜 |
|---|---|---|
| 새로 쓰는 모든 여백·크기·테두리 | **논리 속성** | Baseline widely 다. 기본값으로 삼는다 |
| 다국어(RTL)·세로쓰기 지원 | **논리 속성** | 스타일시트를 한 벌만 유지한다 |
| 진짜로 **화면의 왼쪽**이어야 하는 것 | 물리 속성 | 스크롤바 위치·화면 고정 장식 같은 것 |
| 이미 물리로 통일된 컴포넌트 | 물리 유지 | 섞는 것이 가장 나쁘다((4)) |
| 세로쓰기 본문(일본어·중국어 전통 조판) | `writing-mode: vertical-rl` | 인라인 축 자체를 돌린다 |
| 아랍어·히브리어 | `<html dir="rtl">` | CSS 가 아니라 마크업이 표준 |
| 방향을 애니메이션 | **안 쓴다** | 레이아웃 속성이다 |

판단 규칙 두 줄.

- **「왼쪽」이라고 쓰기 전에 「화면의 왼쪽인가, 글이 시작하는 쪽인가」를 물어라.** 후자면 논리 속성이다.
- **한 컴포넌트 안에서는 물리든 논리든 한 벌로 통일한다.** 섞인 코드가 가장 위험하다.

## 핵심 문장

- 축은 **인라인(펜이 나아가는 쪽) · 블록(줄이 쌓이는 쪽)** 둘이다. 「가로·세로」가 아니다.
- **`writing-mode` 가 두 축을 고르고, `direction` 은 인라인 축 안에서 앞뒤만 바꾼다.** 둘은 다른 축이다.
- **똑같은 논리 선언 하나가 `writing-mode`/`direction` 조합에 따라 네 물리 방향을 전부 돈다**((2)).
- **`getComputedStyle` 은 논리 속성을 물리로 풀어 돌려준다** — 그래서 「내 선언이 어디로 갔나」를 물어볼 수 있다. 단 `text-align: start` 같은 **값 쪽 논리는 안 풀린다.**
- ★ **논리와 물리가 같은 물리 속성으로 풀리면 캐스케이드로 싸운다.** 다른 방향으로 풀리면 둘 다 산다.
- ★ **`flex-direction: row` 는 「가로」가 아니라 「인라인 축」** 이다 — [24\~26번](../24-flexbox-axes/)의 주축이 여기서 돈다.
- **논리 속성은 이미 Baseline widely** 다(2021-09-20 → 2024-03-20). **이제 기본으로 쓴다.**

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 32번) · 「버전·지원 기준」의 Baseline 표
- [`foundations/data-representation/`](../../../../data-representation/) — **유니코드·문자 인코딩은 거기 정본이다.** 여기는 **물리 축과 논리 축이 갈리는 CSS 규칙**만
- [24번](../24-flexbox-axes/) — **주축·교차축의 정본.** 그쪽이 「축이 돈다」고만 적은 자리의 **왜**가 여기 (5)다
- [25번](../25-flex-shorthand-and-sizing/) · [26번](../26-flex-wrap-gap-order/) — `flex-basis` 가 재는 축, `row-gap`/`column-gap` 이름이 물리인 것
- [15번](../15-box-model-and-box-sizing/) — **`width` 가 어느 칸을 재는가는 거기.** 여기는 **그 `width` 가 어느 축인가**
- [18번](../18-margin-collapsing/) — (2)의 실측에서 부모를 `flow-root` 로 만든 이유
- [01번](../01-cascade-and-priority/) · [02번](../02-specificity/) — (4)에서 논리와 물리가 겨루는 규칙의 정본
- [07번](../07-syntax-and-error-recovery/) — `margin-inline-top` 처럼 **없는 속성이 조용히 버려지는** 규칙
- [31번](../31-intrinsic-sizing-and-aspect-ratio/) — 「담기는 것과 먹는 것이 다르다」는 같은 함정의 다른 사례
- [목록의 **56번 주제**](../56-rendering-pipeline-and-will-change/)(렌더링 파이프라인) — `writing-mode` 가 레이아웃 속성이라 전환에 못 태우는 이유
- [`reference/render-rules.md`](../../../../../../reference/render-rules.md) — 이 문서의 `demo` 블록 규칙

## 용어 풀이

- **인라인 축(inline axis)** — 글자가 이어지는 방향의 축. 가로쓰기에서는 가로, 세로쓰기에서는 세로.
- **블록 축(block axis)** — 줄이 쌓이는 방향의 축. 인라인 축에 직각이다.
- **inline-start / inline-end** — 인라인 축의 시작·끝. `direction` 이 앞뒤를 뒤집는다.
- **block-start / block-end** — 블록 축의 시작·끝. `writing-mode` 가 정한다.
- **`writing-mode`** — 두 축을 **둘 다** 정한다. `horizontal-tb` / `vertical-rl` / `vertical-lr` 등.
- **`direction`** — 인라인 축 안에서의 시작 쪽. `ltr` / `rtl`. **축 자체는 안 바꾼다.**
- **논리 속성(logical property)** — `inline-size`·`margin-inline-start` 처럼 **글의 방향**을 기준으로 하는 속성.
- **물리 속성(physical property)** — `width`·`margin-left` 처럼 **화면의 방향**을 기준으로 하는 속성.
- **`inset`** — 이름은 새것인데 **물리 네 방향 단축**(`top right bottom left`)이다. 논리 단축은 `inset-inline`/`inset-block`.
- **RTL(right-to-left)** — 아랍어·히브리어처럼 오른쪽에서 왼쪽으로 쓰는 문자 체계. 실무에서는 `<html dir="rtl">` 로 켠다.
- **Baseline widely** — 주요 엔진에 들어간 지 충분히 오래돼 **조건 없이 써도 되는** 상태. 논리 속성은 2024-03-20 부터다.

---

## 더 들어가면

- **`sideways-rl` / `sideways-lr`** 라는 `writing-mode` 값도 있다 — 글자를 **회전만** 시키는 것(세로 조판이 아니라 눕히기). *(실측: 이 Chrome 의 `cssRules` 에 `writing-mode: sideways-rl` 이 담긴다.)* **담겼다는 것이 먹는다는 뜻은 아니므로**([31번](../31-intrinsic-sizing-and-aspect-ratio/) §(9)) 쓰기 전에 좌표로 확인한다.
- **`text-orientation`** 은 세로쓰기에서 **글자 하나하나를 눕힐지 세울지**를 정한다(`mixed`·`upright`·`sideways`). `writing-mode` 가 축을 돌리고 이것이 글자를 돌린다 — 둘을 같이 봐야 세로 조판이 완성된다.
- **`:dir()` 의사 클래스**(Baseline **widely**, 2023-12-07 → 2026-06-07)로 `dir` 값에 따라 스타일을 갈라 쓸 수 있다. 다만 **논리 속성으로 되는 일에는 쓰지 않는 것**이 요점이다 — 갈라 쓸수록 스타일시트가 두 벌이 된다.
- ★ **`row-gap`/`column-gap` 은 이름이 물리인데 동작은 논리다**([26번](../26-flex-wrap-gap-order/)). `row-gap` 은 「가로줄 사이」가 아니라 **「블록 축 방향 간격」** 이다. 이름만 옛것이 남은 자리라 세로쓰기에서 헷갈린다.
- **논리 속성이 `transition`/`animation` 에서 물리와 겹칠 때** 어느 쪽이 보간되는지는 (4)의 캐스케이드 규칙을 그대로 따른다 — **같은 물리 속성 하나**로 풀린 뒤 보간되기 때문이다.

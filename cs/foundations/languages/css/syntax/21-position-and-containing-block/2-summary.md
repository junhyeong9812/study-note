# css/syntax/21 — `position` 다섯 값과 포함 블록 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [CSS Positioned Layout Module Level 3](https://drafts.csswg.org/css-position-3/) (다섯 값·포함 블록·`inset` 의 정본) · [CSS Transforms Level 2](https://drafts.csswg.org/css-transforms-2/) (변형된 조상이 포함 블록이 되는 규정). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 `demo` 블록 **4개 전부**와 **포함 블록을 바꾼다고 알려진 선언 12가지**를 **Google Chrome 151.0.7922.173** headless 에 실제로 띄워 `getBoundingClientRect()` 로 좌표를 쟀고, 잘림 여부는 **스크린샷 픽셀을 읽어** 판정했다.\
> **WebKit(Safari)은 이 머신에 없고 Firefox 는 이 환경에서 headless 스크린샷이 산출되지 않는다** — 크로스 브라우저 주장은 하지 않았다.
> **여기서 다루지 않는 것** — **누가 위에 그려지나(쌓임 맥락·`z-index`)는 [22번](../22-stacking-context-and-z-index/2-summary.md)이 정본**이고, 여기는 **어디에 놓이나**까지다. 둘은 만드는 조건이 **비슷해 보이지만 다르다**((5)에서 실측으로 가른다). 스크롤 컨테이너와 `overflow` 값들은 [23번](../23-overflow-and-scroll-containers/2-summary.md), 상자의 네 겹 치수는 [15번](../15-box-model-and-box-sizing/2-summary.md), `%` 가 어느 단계에서 풀리는지는 [04번](../04-value-processing-stages/2-summary.md), 흐름에서 **반쯤** 빠지는 float 는 [20번](../20-float-and-clear/2-summary.md), BFC 는 [17번](../17-block-formatting-context/2-summary.md)이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 좌표는 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**`position` 은 「이 상자를 **무엇에 대고** 재서 놓을까」를 고르는 스위치다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 벽에 그림을 걸 때 **기준으로 삼는 벽** | **포함 블록**(containing block) |
| 「벽 왼쪽에서 20cm」라는 지시 | `left: 20px` |
| 원래 자리에 못은 그대로 두고 **그림만 옆으로 옮긴 것** | `relative` — 자리는 남고 그려지는 위치만 이동 |
| 못을 뽑아 **다른 벽**에 다시 건 것 | `absolute` — 가장 가까운 위치 지정 조상이 새 벽 |
| **유리창**에 붙여 밖을 볼 때마다 같은 자리 | `fixed` — 뷰포트가 벽 |
| 창틀 안에서 **미끄러지다 모서리에 걸리는 것** | `sticky` — 스크롤 컨테이너 안에서만 산다 |

```text
   같은 top: 0; left: 0 인데 어디로 가나

   static     relative     absolute        fixed         sticky
   (무시)     제자리에서    가장 가까운     뷰포트        스크롤 컨테이너
              0,0 이동      위치 지정      왼쪽 위        위끝에 걸릴 때까지
              (= 안 움직임)  조상의 패딩                  보통 흐름
                            상자 왼쪽 위
```

실무에서 이게 터지는 자리는 **"`position: fixed` 인데 화면에 안 붙어 있다"** 는 증상이다.\
조상 어딘가에 `transform`·`filter`·`will-change` 가 있으면 **그 조상이 벽이 된다**((4)에서 실측한다).

> **포함 블록(containing block)** — 그 상자의 `top`/`left`/`%` 를 **재는 기준이 되는 사각형**.\
> 예: `absolute` 상자의 `left: 50%` 는 「포함 블록 폭의 50%」다. 그 폭이 무엇이냐를 정하는 것이 이 주제다.

> **위치 지정 조상(positioned ancestor)** — `position` 이 `static` 이 아닌 조상.\
> 예: `position: relative` 만 줘 놓고 `top`/`left` 를 안 주는 「앵커」 관용구가 이것을 만들려는 것이다.

> **뷰포트(viewport)** — 문서가 보이는 창 자체. 스크롤해도 안 움직인다.\
> 예: 브라우저 창의 내용 영역. `fixed` 의 기본 벽이다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 다섯 값 각각에서 **포함 블록이 무엇이 되는가.**
2. `absolute` 의 `%` 는 **어느 상자**를 기준으로 풀리는가 — 보통 상자와 같은가.
3. **`fixed` 의 벽을 바꿔 버리는 선언**은 무엇이고, 그것은 쌓임 맥락을 만드는 선언과 같은가.

## 동작 방식

### (1) 다섯 값 — 자리를 남기나, 좌표를 쓰나

**언제 쓰나** — 무엇을 고를지 정할 때. **이 표가 이 주제의 좌표계다.**

*(Chrome 151 headless 실측 — 24px 짜리 형제 셋 중 가운데에 각 값을 주고 `top: 20px; left: 30px` 을 걸었다. 컨테이너 안 좌표.)*

| `position` | 원래 자리를 남기나 | `top`/`left` 를 쓰나 | 포함 블록 | 실측(가운데·다음 형제) |
|---|---|---|---|---|
| `static`(기본) | — | **안 쓴다** | — | (2,30) · (2,58) — **선언이 통째로 무시됨** |
| `relative` | **남긴다** | 쓴다(제자리 기준) | 자기 자신의 원래 자리 | **(32,50)** · (2,58) — 다음 형제 **그대로** |
| `absolute` | **안 남긴다** | 쓴다 | 가장 가까운 **위치 지정 조상의 패딩 상자** | (20,−88) · **(2,30)** — 형제가 자리를 채움 |
| `fixed` | **안 남긴다** | 쓴다 | **뷰포트**(조건부로 조상 — (4)) | 스크롤해도 안 움직임 |
| `sticky` | **남긴다** | 쓴다(걸릴 때만) | 가장 가까운 **스크롤 컨테이너의 스크롤포트** | 자리 24px 유지 · 걸리면 고정 |

```text
   relative                           absolute
  +----------------------+           +----------------------+
  | [형제 1        ]     |           | [형제 1        ]     |
  |       [대상] ← 옮겨짐|           | [형제 3        ]  ← 형제가 올라온다
  | (빈 자리 그대로 남음)|           |                      |
  | [형제 3        ]     |           |      [대상] ← 흐름 밖 |
  +----------------------+           +----------------------+
    줄 수 3칸 (높이 88)                 줄 수 2칸 (높이 60)
```

*(Chrome 151 headless 실측 — 컨테이너 높이가 `relative` 는 **88**, `absolute` 는 **60** 이었다. 자리를 남기느냐가 높이에 그대로 드러난다.)*

```html demo
<div class="row"><i>1</i><i class="rel">2 relative</i><i>3</i></div>
<div class="row"><i>1</i><i class="abs">2 absolute</i><i>3</i></div>
<style>
  .row { position: relative; width: 260px; border: 2px solid #333;
         font: 12px/24px system-ui; margin-bottom: 10px; }
  .row i { display: block; width: 150px; height: 24px; background: #fde68a;
           font-style: normal; }
  .row i.rel { position: relative; top: 12px; left: 60px; background: #93c5fd; }
  .row i.abs { position: absolute; top: 12px; left: 60px; background: #fca5a5; }
</style>
```

> **보이는 것** — 위 상자에는 노란 띠 `1`·`3` 사이에 **빈 노란 자리**가 그대로 남아 있고 파란 `2` 가 그 자리에서 오른쪽 아래로 비켜나 `3` 위에 겹쳐 있다. 아래 상자는 **빈 자리가 없어** 노란 `1`·`3` 이 붙어 있고 분홍 `2` 가 그 위를 덮는다. **아래 상자가 위 상자보다 눈에 띄게 낮다.**\
> **바꿔 볼 것** — `.row i.abs` 의 `position: absolute` → `fixed` (상자를 벗어나 **화면 왼쪽 위**로 간다) · `.row i.rel` 의 `top`·`left` 를 지우면 원래 자리로 돌아온다

- ★ **`static` 에서는 `top`/`left` 가 통째로 무시된다** — 에러도 경고도 없다. 실측에서 좌표가 보통 형제와 **한 픽셀도 다르지 않았다.**
- **`relative` 는 자리를 비우지 않는다.** 그려지는 위치만 옮긴다 — 그래서 겹침이 생긴다.
- **`absolute`/`fixed` 는 자리를 없앤다.** 다음 형제가 올라온다.

비용 — `absolute`/`fixed` 는 **흐름에서 빠져** 부모 높이에 기여하지 않는다. [float 가 줄은 미는 것](../20-float-and-clear/2-summary.md)과 달리 **줄도 안 민다** — 글 위에 그냥 덮인다.

### (2) `absolute` 의 포함 블록은 「패딩 상자」다

**언제 쓰나** — `top: 0; left: 0` 을 줬는데 테두리 바깥/안쪽으로 어긋날 때. **가장 헷갈리는 자리다.**

```text
  조상: margin 20 · border 10 · padding 30 · 내용 300×160

  (20,20) ┌──────────────── 테두리 상자 ────────────────┐
          │ border 10                                   │
  (30,30) │  ┌────────── 패딩 상자 (360×220) ─────────┐ │  ← absolute 의 벽
          │  │ padding 30                             │ │
  (60,60) │  │   ┌──── 콘텐츠 상자 (300×160) ────┐    │ │  ← static 의 % 기준
          │  │   │                                │    │ │
          │  │   └────────────────────────────────┘    │ │
          │  └────────────────────────────────────────┘ │
          └─────────────────────────────────────────────┘
```

*(Chrome 151 headless 실측 — 위 조상에 `position: relative` 를 주고 세 자식을 넣었다.)*

| 자식 | 선언 | 실측 좌표·크기 | 기준이 된 상자 |
|---|---|---|---|
| A | `absolute; top:0; left:0` | **x=30 · y=30** | **패딩 상자**(테두리 안쪽) |
| B | `absolute; top:50%; left:50%` | **x=210 · y=140** | 패딩 상자 360×220 의 절반 |
| C | `width: 50%`(보통 블록) | **w=150** | **콘텐츠 상자** 300 의 절반 |

- ★ **같은 `50%` 가 `absolute` 에서는 180, 보통 블록에서는 150 이다.** 기준 상자가 다르기 때문이다.
- **테두리 상자가 아니다** — `top: 0` 이 20 이 아니라 **30** 이었다(테두리 10 안쪽).
- **콘텐츠 상자도 아니다** — 60 이 아니다. **정확히 패딩 상자**다.

```html demo
<div class="anc">
  <b class="a">abs 0,0</b>
  <b class="h"></b>
  <i class="s">static 100%</i>
</div>
<style>
  .anc { position: relative; width: 200px; height: 90px; padding: 30px;
         border: 10px solid #333; background: #e5e7eb; font: 11px/16px system-ui; }
  .anc b { position: absolute; background: #fca5a5; font-weight: normal; }
  .anc b.a { top: 0; left: 0; }
  .anc b.h { top: 0; left: 100%; width: 6px; height: 70px; background: #1d4ed8; }
  .anc i.s { display: block; width: 100%; height: 16px; background: #a7f3d0;
             font-style: normal; }
</style>
```

> **보이는 것** — 굵은 검은 테두리 **바로 안쪽 왼쪽 위 모서리**에 분홍 `abs 0,0` 이 딱 붙어 있다 — 테두리 바깥도, 회색 여백만큼 안쪽도 아니다. 파란 세로 막대(`left: 100%`)는 저 멀리 **오른쪽 테두리의 안쪽 가장자리에 걸쳐** 서 있다(테두리 위를 일부 덮는다). 연두 막대(`width: 100%`)는 회색 여백만큼 안에서 시작해 **파란 막대에 한참 못 미치고 끝난다** — 두 `100%` 의 기준 상자가 다르기 때문이다.\
> **바꿔 볼 것** — `.anc` 의 `padding` 을 `0` 으로 하면 **연두 막대가 파란 막대까지 닿는다**(두 기준이 같아진다) · `.anc` 의 `position: relative` 를 지우면 분홍·파랑이 **화면 왼쪽 위·오른쪽 끝으로 날아간다**

### (3) 포함 블록을 찾아 올라가는 사슬

**언제 쓰나** — 「내 `absolute` 가 왜 저기에 붙었지?」를 추적할 때.

```text
  absolute 의 벽 찾기 — 부모부터 한 칸씩 올라간다

   부모          position 이 static 이 아닌가?  ─ 예 ─> 그 상자의 패딩 상자가 벽
     ↓ 아니오
   조부모        position 이 static 이 아닌가?  ─ 예 ─> 그 상자의 패딩 상자가 벽
     ↓ 아니오
    …
     ↓ 아무도 없으면
   초기 포함 블록 (뷰포트 크기 · 문서 맨 위 원점)
```

```text
  fixed 의 벽 찾기 — 기본은 한 칸도 안 올라간다

   조상 중에 transform · filter · backdrop-filter ·
   will-change(그 속성들) · perspective · contain: paint 가 있나?
        │
        ├─ 없다 ─> 뷰포트가 벽 (스크롤해도 안 움직인다)
        │
        └─ 있다 ─> 그 조상의 패딩 상자가 벽 (같이 스크롤된다)   ★ (4)
```

*(Chrome 151 headless 실측 — 위치 지정 조상이 하나도 없을 때 `absolute; top:20; left:30` 인 상자가 **문서 좌표 (30, 20)** 에 놓였다. 초기 포함 블록의 원점은 **문서 맨 위 왼쪽**이고 크기는 뷰포트 크기(이 실행에서 780×493)였다.)*

> **초기 포함 블록(initial containing block)** — 위로 아무도 없을 때 쓰이는 벽. **크기는 뷰포트**지만 **원점은 문서 맨 위**라 스크롤하면 같이 올라간다.\
> 예: `<body>` 에 아무 `position` 도 안 주고 자식에 `absolute` 를 걸면 여기에 붙는다.

### (4) `transform` 이 걸린 조상 하나가 `fixed` 의 벽을 바꾼다

**언제 쓰나** — 모달·툴팁이 화면에 안 붙어 있을 때. ★ **가장 많이 당하는 자리다.**

*(Chrome 151 headless 실측 — 같은 마크업에서 래퍼의 선언만 바꿨다. 자식은 `position: fixed; top:0; left:0`. 래퍼는 테두리 2px.)*

| 래퍼의 선언 | 래퍼 좌표 | 자식의 실측 좌표 | 벽이 된 것 |
|---|---|---|---|
| (없음) | (40, 40) | **(0, 0)** | **뷰포트** |
| `transform: translateX(0)` | (40, 204) | (42, 206) | **래퍼의 패딩 상자** |
| `filter: blur(0px)` | (40, 368) | (42, 370) | 래퍼 |
| `will-change: transform` | (40, 532) | (42, 534) | 래퍼 |
| `perspective: 500px` | (40, 696) | (42, 698) | 래퍼 |
| `contain: paint` | (40, 860) | (42, 862) | 래퍼 |
| `backdrop-filter: blur(2px)` | (40, 1024) | (42, 1026) | 래퍼 |
| `contain: layout` | (40, 1188) | (42, 1190) | 래퍼 |
| **`opacity: 0.5`** | (40, 1352) | **(0, 0)** | **뷰포트 — 안 바뀐다** |
| **`isolation: isolate`** | (40, 1516) | **(0, 0)** | **뷰포트 — 안 바뀐다** |
| **`overflow: hidden`** | (40, 1680) | **(0, 0)** | **뷰포트 — 안 바뀐다** |
| **`position: relative`** | (40, 1844) | **(0, 0)** | **뷰포트 — 안 바뀐다** |

- ★★ **`translateX(0)` 도 `blur(0px)` 도 「아무것도 안 하는」 값인데 벽이 바뀐다.** 값이 항등이어도 **선언이 있으면** 바뀐다.
- ★ **`will-change: transform` 만으로도 바뀐다.** 성능 힌트를 줬을 뿐인데 레이아웃 기준이 바뀌는 것이다.
- ★ **`opacity`·`isolation`·`overflow: hidden`·`position: relative` 는 `fixed` 의 벽을 안 바꾼다.** 이것이 (5)의 갈림길이다.
- `absolute` 도 같은 영향을 받는다 — 같은 실험에서 `transform` 래퍼(40, 2008) 안의 `absolute; top:0; left:0` 이 **(42, 2010)** 에 붙었다.

```html demo
<div class="w">보통 래퍼<b class="fx">fixed</b></div>
<div class="w" style="transform: translateX(0)">transform 래퍼<b class="fx">fixed</b></div>
<style>
  .w { width: 220px; height: 70px; margin: 30px; border: 2px solid #333;
       background: #e5e7eb; font: 12px/20px system-ui; }
  .fx { position: fixed; top: 0; left: 0; width: 70px; height: 20px;
        background: #fca5a5; font-weight: normal; }
</style>
```

> **보이는 것** — 분홍 `fixed` 상자가 **두 개** 있다. 하나는 **화면 맨 왼쪽 위 구석**에 붙어 있고(보통 래퍼의 것), 다른 하나는 **두 번째 회색 래퍼의 왼쪽 위 안쪽**에 들어가 있다. 같은 `top: 0; left: 0` 인데 **자리가 완전히 다르다.**\
> **바꿔 볼 것** — `transform: translateX(0)` → `opacity: 0.5` (**둘 다 화면 구석으로 간다** — `opacity` 는 벽을 안 바꾼다) · `translateX(0)` → `filter: blur(0px)` (**똑같이 래퍼 안에 갇힌다**)

- 증상 진단법 — **`fixed` 가 스크롤을 따라 움직이면** 조상에 위 선언 중 하나가 있는 것이다.
- 고치는 법은 그 선언을 없애거나, `fixed` 요소를 **그 조상 밖으로**(대개 `<body>` 바로 밑으로) 옮기는 것이다.

### (5) 포함 블록을 바꾸는 것과 쌓임 맥락을 만드는 것은 다르다

**언제 쓰나** — 두 목록을 한 덩어리로 외웠을 때. ★ **이 갈림길을 모르면 오진한다.**

*(Chrome 151 headless 실측 — 같은 선언에 대해 ① `fixed` 자식의 좌표(포함 블록)와 ② 겹치는 지점의 스크린샷 픽셀(쌓임 맥락)을 각각 쟀다. 쌓임 맥락 쪽 실측의 정본은 [22번](../22-stacking-context-and-z-index/2-summary.md)이다.)*

| 선언 | 포함 블록을 바꾸나 | 쌓임 맥락을 만드나 |
|---|---|---|
| `transform: translateZ(0)` | **✓** | **✓** |
| `filter: blur(0px)` | **✓** | **✓** |
| `will-change: transform` | **✓** | **✓** |
| `contain: paint` | **✓** | **✓** |
| `contain: layout` | **✓** | **✓** |
| **`opacity: 0.99`** | **✗** | **✓** |
| **`isolation: isolate`** | **✗** | **✓** |
| **`position: relative` + `z-index: 1`** | **✗**(`fixed` 기준으로는) | **✓** |
| **`position: relative`**(z-index 없음) | **✗**(`fixed` 기준으로는) | **✗** |

```text
   두 목록이 겹치지만 같지 않다

        포함 블록을 바꾸는 것            쌓임 맥락을 만드는 것
       ┌──────────────────────┐        ┌──────────────────────┐
       │                      │        │                      │
       │   (fixed 만 해당)    │  ∩     │   opacity < 1        │
       │   transform / filter │ ─────  │   isolation: isolate │
       │   will-change        │ 겹침   │   position + z-index │
       │   perspective        │        │   mix-blend-mode     │
       │   contain: paint     │        │   flex/grid 항목+z   │
       └──────────────────────┘        └──────────────────────┘
```

- **겹치는 쪽**(`transform`·`filter`·`will-change`·`contain: paint`)은 **둘 다** 한다.
- **`opacity`·`isolation` 은 쌓임 맥락만** 만든다 — 실측에서 `opacity: 0.5` 래퍼 안의 `fixed` 가 **(0,0)** 에 그대로 있었다.
- **`position: relative`** 는 **`absolute` 의 벽은 되지만 `fixed` 의 벽은 안 된다.**
- ★ 그래서 **「`z-index` 가 안 먹는다」와 「`fixed` 가 안 붙는다」를 같은 원인으로 오진하면 안 된다.** 겹치는 구간에서는 원인이 같지만, `opacity` 자리에서는 갈린다.

### (6) `sticky` 는 스크롤 컨테이너 안에서만 산다

**언제 쓰나** — `position: sticky` 를 줬는데 안 붙을 때.

```text
  sticky 의 조건 두 가지

  ① 조상 사슬에 스크롤 컨테이너가 있어야 한다
       (없으면 뷰포트 스크롤이 그 역할을 한다)
  ② top / bottom / left / right 중 하나는 있어야 한다
       (없으면 「걸릴 지점」이 없어 보통 흐름과 똑같다)
```

*(Chrome 151 headless 실측 — 240×120 상자 안에 `sticky; top: 0` 헤더와 400px 짜리 내용을 넣고 `scrollTop = 200` 을 시도했다.)*

| 스크롤러의 `overflow` | 실제 `scrollTop` | 헤더가 붙나 |
|---|---|---|
| `auto` | 200 | **붙는다** |
| `scroll` | 200 | **붙는다** |
| `hidden` | **200** | **붙는다** — 스크롤 컨테이너이기 때문 |
| `clip` | **0** | 스크롤 자체가 안 된다 |
| `visible` | 0 | 스크롤 자체가 안 된다 |

★★ **그런데 조상 중간에 `overflow` 가 끼면 `sticky` 가 죽는다.**

*(Chrome 151 headless 실측 — `overflow: auto` 스크롤러와 `sticky` 헤더 **사이에** 래퍼를 하나 넣고 래퍼의 `overflow` 만 바꿨다. `scrollTop = 200` 후 헤더의 위치.)*

| 중간 래퍼의 `overflow` | 헤더 top(스크롤러 기준) | 결과 |
|---|---|---|
| `visible` | **2.0** | 붙는다 |
| `clip` | **2.0** | **붙는다** — `clip` 은 스크롤 컨테이너가 아니다 |
| `hidden` | **−198.0** | **안 붙는다** — 같이 밀려 올라간다 |
| `auto` | **−198.0** | 안 붙는다 |

- **`sticky` 는 「가장 가까운 스크롤 컨테이너」에 걸린다.** 중간 래퍼가 스크롤 컨테이너가 되어 버리면 **그 래퍼는 스크롤되지 않으므로** 걸릴 일이 없다.
- ★ **`hidden` 은 죽이고 `clip` 은 안 죽인다.** 둘의 차이는 **스크롤 컨테이너를 만드느냐**이고, 정본은 [23번](../23-overflow-and-scroll-containers/2-summary.md)이다.
- 그래서 「**`overflow: hidden` 을 `clip` 으로 바꾸면 `sticky` 가 살아난다**」는 실전 처방이 나온다(실측으로 확인).

```html demo
<div class="sc"><b>sticky 머리</b><p>가나다라마바사 아자차카타파하 가나다라마바사 아자차카타파하
가나다라마바사 아자차카타파하 가나다라마바사 아자차카타파하 가나다라마바사 아자차카타파하
가나다라마바사 아자차카타파하 가나다라마바사 아자차카타파하 가나다라마바사 아자차카타파하</p></div>
<style>
  .sc { overflow: auto; width: 230px; height: 110px; border: 2px solid #333;
        font: 13px/20px system-ui; }
  .sc b { position: sticky; top: 0; display: block; background: #fca5a5;
          font-weight: normal; }
  .sc p { margin: 0; }
</style>
```

> **보이는 것** — 상자 안을 아래로 스크롤하면 분홍 「sticky 머리」 띠가 **상자 위쪽에 붙어 그대로 남고** 글만 그 아래로 흘러간다. 상자 **밖으로는 절대 나가지 않는다.**\
> **바꿔 볼 것** — `.sc` 의 `overflow: auto` → `clip` (스크롤 자체가 안 되므로 **아무 일도 안 일어난다**) · `.sc b` 의 `top: 0` 을 지우면 **걸리지 않고 그냥 같이 올라간다**

### (7) `inset` 단축과 「자리를 다 채우는」 관용구

**언제 쓰나** — 네 방향을 한 줄로 쓸 때.

```text
  inset: <top> <right> <bottom> <left>      margin 과 같은 순서

  inset: 0                 → top/right/bottom/left 전부 0
  inset: 10px auto auto 40px → top:10 right:auto bottom:auto left:40
  inset: 0 auto auto 0     → 왼쪽 위 구석에 붙인다
```

*(Chrome 151 headless 실측 — `position: relative; inset: 10px auto auto 40px` 인 형제가 원래 자리 (2,30) 에서 **(42,40)** 으로 옮겨졌다. 곧 오른쪽 40 · 아래 10.)*

- ★ **`relative` 에서 네 방향을 다 주면 서로 싸운다.** 가로는 `left` 가, 세로는 `top` 이 이긴다(좌횡서 기준).
- **`absolute` 에서 `inset: 0`** 은 「**포함 블록을 꽉 채워라**」가 된다 — 폭·높이를 안 줘도 네 변이 다 고정되므로 크기가 정해진다. 오버레이의 표준 관용구다.
- 논리 짝으로 `inset-block`·`inset-inline` 도 있다([목록의 **32번 주제**](../32-logical-properties-and-writing-mode/)).

## 문법 — 형태와 어디서 헷갈리나

### 최소 형태

```css
.anchor { position: relative; }              /* 좌표는 안 준다 — 벽만 만든다 */
.badge  { position: absolute; top: 0; right: 0; }
.overlay{ position: fixed; inset: 0; }       /* 화면을 꽉 채운다 */
.header { position: sticky; top: 0; }        /* 스크롤 컨테이너 안에서 걸린다 */
```

### 헷갈리는 자리 ① — 「가장 가까운 조상」이 누구인가

```text
  <div>                       position 없음   → 벽이 아니다
    <div style="opacity:.5">  opacity        → fixed 의 벽이 아니다 · absolute 의 벽도 아니다
      <div style="transform:…">transform     → 둘 다의 벽이다   ★
        <span class="target" style="position:absolute">
```

- **`absolute` 의 벽**은 「`position` 이 `static` 이 아닌 조상」**과** 「`transform` 류가 걸린 조상」 **둘 다** 후보다.
- **`fixed` 의 벽**은 **`transform` 류만** 후보다. `position: relative` 로는 안 바뀐다.

### 헷갈리는 자리 ② — `sticky` 와 `fixed`

```text
                 자리를 남기나   어디에 걸리나        밖으로 나갈 수 있나
  fixed              ✗          뷰포트(또는 변형 조상)    나간다
  sticky             ✓          가장 가까운 스크롤 컨테이너 부모 상자 밖으로 못 나간다
```

- `sticky` 는 **부모의 범위를 벗어나지 않는다.** 부모가 화면 밖으로 나가면 같이 나간다.

### 금지에 가까운 형태

```css
.a { position: static; top: 20px; }     /* top 이 통째로 무시된다 — 에러 없음 */
.b { position: sticky; }                /* top/bottom 이 없어 아무 일도 안 일어난다 */
.c { position: fixed; }                 /* 조상의 transform 하나로 벽이 바뀐다 */
.d { overflow: hidden; }                /* 자손 sticky 를 죽인다 — clip 이면 안 죽는다 */
```

## 구현 세부사항 대 언어 보장

- **다섯 값의 의미와 「`absolute` 의 포함 블록은 패딩 상자」는 명세다.** CSS Positioned Layout Level 3 가 근거이고 실측이 그것과 맞았다.
- **「변형된 조상이 `fixed` 의 포함 블록이 된다」도 명세다**(CSS Transforms Level 2). 다만 **어떤 선언이 그 목록에 드는지는 계속 늘어 왔다** — `will-change`·`contain: paint`·`backdrop-filter` 는 나중에 들어온 것이라 **오래된 글과 목록이 다르다.** 이 문서의 표는 **이 브라우저에서 실제로 재 본 것**이다.
- ★ **`opacity` 가 포함 블록을 안 바꾸는 것**은 실측이자 명세의 결론이지만, 이 문서는 **실측한 값만** 적었다.
- **초기 포함 블록의 크기 780×493 은 이 실행의 창 크기**다. CSS 의 보장이 아니다.
- **스크롤바 15px 같은 수치는 플랫폼의 것**이다([23번](../23-overflow-and-scroll-containers/2-summary.md)).

## 어디서 틀리나

### 1. `absolute` 의 기준을 「테두리 상자」나 「콘텐츠 상자」로 안다

**패딩 상자**다((2) 실측: `top:0` 이 20 도 60 도 아닌 **30**).\
그래서 조상에 패딩을 주면 `absolute` 자식이 **같이 움직인다.**

### 2. 같은 `50%` 가 같은 값일 거라 생각한다

`absolute` 는 **패딩 상자**, 보통 블록은 **콘텐츠 상자** 기준이다 — 실측 **180 대 150**.

### 3. `position: static` 에 `top` 을 주고 왜 안 되는지 찾는다

**통째로 무시된다.** 에러도 경고도 없다 — CSS 가 에러가 없는 언어인 자리다.\
「앵커」를 만들려면 `position: relative` 를 줘야 한다.

### 4. `fixed` 가 안 붙는 원인을 `z-index` 에서 찾는다

조상의 `transform`·`filter`·`will-change` 가 **벽을 바꾼 것**이다((4)).\
`opacity` 는 **벽을 안 바꾼다** — 그러니 두 목록을 한 덩어리로 외우면 오진한다((5)).

### 5. `will-change` 를 성능 옵션으로만 본다

**레이아웃 기준을 바꾼다.** 실측에서 `will-change: transform` 하나로 `fixed` 자식이 래퍼 안에 갇혔다.

### 6. `sticky` 가 안 붙는데 자기 선언만 본다

**조상 사슬**을 봐야 한다. 중간의 `overflow: hidden`/`auto` 하나가 죽인다((6) 실측 −198).\
`clip` 으로 바꾸면 살아난다.

### 7. `sticky` 에 `top` 을 안 준다

**걸릴 지점이 없어 보통 흐름과 똑같이 움직인다.** 아무 에러도 없다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 고르는 것 | 왜 |
|---|---|---|
| 배지·툴팁을 어떤 상자 모서리에 붙인다 | 그 상자에 `relative` + 자식에 `absolute` | 벽을 만들고 그 안에서 잰다 |
| 화면 전체 오버레이 | `fixed; inset: 0` | 뷰포트가 벽 |
| 스크롤해도 따라오는 헤더 | `sticky; top: 0` | 자리를 남기므로 내용이 안 튄다 |
| 살짝 밀어서 겹치게 한다 | `relative` + `top`/`left` | 자리를 유지하므로 주변이 안 흔들린다 |
| 흐름은 유지하고 **줄만** 비키게 한다 | [`float`](../20-float-and-clear/2-summary.md) | `absolute` 는 줄을 안 민다 |
| 여러 칸을 나란히 놓는다 | [flex](../24-flexbox-axes/2-summary.md)/grid | `absolute` 로 레이아웃을 짜지 않는다 |
| `fixed` 가 조상에 갇히는 것을 막는다 | 그 요소를 `<body>` 밑으로 옮긴다 | 조상의 `transform` 은 못 지울 때가 많다 |

판단 규칙 두 줄.

- **「무엇에 대고 재나」를 먼저 정한다.** 그것이 포함 블록이고, `position` 은 그것을 고르는 스위치일 뿐이다.
- **`absolute`/`fixed` 는 레이아웃 도구가 아니다.** 덮어씌우는 것에만 쓴다.

## 핵심 문장

- `position` 은 **포함 블록을 고르는 스위치**다. 값마다 벽이 다르다.
- `relative` 는 **자리를 남기고 그려지는 위치만** 옮긴다. `absolute`/`fixed` 는 **자리를 없앤다.**
- ★ **`absolute` 의 벽은 가장 가까운 위치 지정 조상의 패딩 상자**다 — 실측 `top:0` → **30**(테두리 10 안쪽, 패딩 30 바깥쪽).
- ★ **같은 `50%` 가 `absolute` 에서 180, 보통 블록에서 150** 이다(기준 상자가 다르다).
- ★★ **`transform: translateX(0)`·`filter: blur(0px)`·`will-change: transform` 하나로 `fixed` 의 벽이 그 조상이 된다** — 항등값이어도 바뀐다. **`opacity` 는 안 바꾼다.**
- ★ **포함 블록을 바꾸는 목록과 쌓임 맥락을 만드는 목록은 겹치지만 같지 않다**([22번](../22-stacking-context-and-z-index/2-summary.md)).
- ★ **`sticky` 는 가장 가까운 스크롤 컨테이너에 걸린다** — 중간 조상의 `overflow: hidden` 이 죽이고, **`clip` 은 안 죽인다**([23번](../23-overflow-and-scroll-containers/2-summary.md)).

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 21번)
- [22번 주제](../22-stacking-context-and-z-index/2-summary.md)(쌓임 맥락과 `z-index`) — ★ **누가 위에 그려지나는 거기가 정본.** 여기는 **어디에 놓이나**까지다. (5)의 대조표가 두 주제를 잇는 자리다
- [23번 주제](../23-overflow-and-scroll-containers/2-summary.md)(오버플로·스크롤 컨테이너) — **`sticky` 가 기대는 「스크롤 컨테이너」의 정본.** `hidden` 과 `clip` 이 갈리는 이유도 거기
- [20번 주제](../20-float-and-clear/2-summary.md)(부동과 해제) — **흐름에서 반쯤 빠지는 쪽.** float 는 줄을 밀고 `absolute` 는 안 민다
- [15번 주제](../15-box-model-and-box-sizing/2-summary.md)(박스 모델) — **패딩 상자·콘텐츠 상자가 무엇인지**는 거기. 여기는 **그중 어느 것이 벽이 되나**다
- [04번 주제](../04-value-processing-stages/2-summary.md)(값 처리 단계) — `%` 가 **사용값 단계에서** 포함 블록을 만나 풀린다는 규칙의 정본
- [17번 주제](../17-block-formatting-context/2-summary.md)(BFC) — `position: absolute` 가 BFC 를 연다는 사실은 거기 표에 있다
- [목록의 **32번 주제**](../32-logical-properties-and-writing-mode/)(논리 속성) — `inset-block`/`inset-inline`
- [목록의 **47번 주제**](../47-filter-and-backdrop-filter/)(`filter`) — 필터가 포함 블록과 쌓임 맥락을 만드는 부작용
- [`reference/render-rules.md`](../../../../../../reference/render-rules.md) — 이 문서의 `demo` 블록 규칙

## 용어 풀이

- **포함 블록(containing block)** — `top`/`left`/`%` 를 재는 기준 사각형. 이 주제의 본체다.
- **위치 지정 조상(positioned ancestor)** — `position` 이 `static` 이 아닌 조상. `absolute` 의 벽 후보다.
- **초기 포함 블록(initial containing block)** — 위로 아무도 없을 때의 벽. **크기는 뷰포트, 원점은 문서 맨 위.**
- **뷰포트(viewport)** — 문서가 보이는 창. `fixed` 의 기본 벽.
- **스크롤포트(scrollport)** — 스크롤 컨테이너에서 실제로 보이는 칸. `sticky` 가 걸리는 기준이다([23번](../23-overflow-and-scroll-containers/2-summary.md)).
- **`static`** — 기본값. `top`/`left`/`z-index` 를 **통째로 무시한다.**
- **`relative`** — 자리를 남기고 그려지는 위치만 옮긴다. `absolute` 자식의 벽을 만든다.
- **`absolute`** — 흐름에서 빠지고 가장 가까운 위치 지정 조상의 **패딩 상자**를 벽으로 쓴다.
- **`fixed`** — 흐름에서 빠지고 **뷰포트**를 벽으로 쓴다. 단 `transform` 류 조상이 있으면 그 조상이 벽이 된다.
- **`sticky`** — 자리를 남긴 채 스크롤 컨테이너 안에서 걸린다. `top`/`bottom` 등이 없으면 아무 일도 안 한다.
- **`inset`** — `top`/`right`/`bottom`/`left` 의 단축. `margin` 과 순서가 같다.

---

## 더 들어가면

- **「흐름에서 얼마나 떨어져 나갔나」의 눈금** — [19번](../19-inline-formatting-context/2-summary.md)(줄 안에 머문다) → [20번](../20-float-and-clear/2-summary.md)(빠지되 줄은 민다) → **21번**(줄도 안 민다) → [22번](../22-stacking-context-and-z-index/2-summary.md)(그린 순서가 뒤집힌다) → [23번](../23-overflow-and-scroll-containers/2-summary.md)(넘친 것을 어떻게 하나). 이 다섯이 한 사슬이다.
- **`absolute` 는 부모의 `overflow` 에 잘린다 — 단 그 부모가 벽일 때만.** 실측에서 `overflow: hidden` 인 상자(자신이 `relative`)의 `absolute` 자식은 **잘렸고**(스크린샷 픽셀이 바깥에서 흰색), 같은 상자의 `fixed` 자식은 **안 잘리고 화면에 그대로 그려졌다**(픽셀 `(252,165,165)`).
- **`position: absolute` 는 BFC 를 연다**([17번](../17-block-formatting-context/2-summary.md) 실측). 다만 흐름에서 빠져 있어 마진 상쇄 이야기가 애초에 성립하지 않는 경우가 많다.
- **앵커 위치 지정(`anchor-name`·`position-anchor`)** 은 「어느 요소에 붙일지」를 **조상 관계 없이** 정하는 새 기능이다. 이 문서는 실행으로 확인한 것만 적으므로 이름만 적어 둔다(**안 돌려 봄**).

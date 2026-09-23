# css/syntax/17 — 서식 문맥(BFC) — 생성 조건과 그 안에 갇히는 것 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [CSS Display Module Level 3](https://drafts.csswg.org/css-display-3/) (서식 문맥과 `flow-root` 의 정본) · [CSS Overflow Module Level 3](https://drafts.csswg.org/css-overflow-3/) (`overflow` 값과 스크롤 컨테이너). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 `demo` 블록 **4개 전부**와 **BFC 를 만든다고 알려진 선언 13가지**를 **Google Chrome 151.0.7922.173** headless 에 실제로 띄워 `getBoundingClientRect()` 로 재고 스크린샷으로 눈으로 확인했다.\
> ★ **이 주제에서는 `rect` 와 화면이 서로 다른 것을 말한다.** 어느 쪽이 근거인지 자리마다 밝혔다.\
> **WebKit(Safari)은 이 머신에 없고 Firefox 는 이 환경에서 headless 스크린샷이 산출되지 않는다** — 크로스 브라우저 주장은 하지 않았다.
> **여기서 다루지 않는 것** — ★ **`float` 자체의 동작**(무엇을 밀어내고 어떻게 줄을 감싸며 `clear` 가 무엇을 하는가)은 [목록의 **20번 주제**](../20-float-and-clear/)가 정본이다. **여기는 「BFC 가 float 를 감싼다·피한다」는 효과까지다.** 마진 상쇄의 세 경우와 막는 법 전수는 [18번](../18-margin-collapsing/2-summary.md), `overflow` 와 스크롤 컨테이너 설계는 [목록의 **23번 주제**](../23-overflow-and-scroll-containers/), `position` 과 포함 블록은 [목록의 **21번 주제**](../21-position-and-containing-block/), `display` 값의 구조는 [16번](../16-display-inner-outer/2-summary.md)이다. **flex/grid 의 배치 규칙은** [24번](../24-flexbox-axes/2-summary.md)과 목록의 [27](../27-grid-track-sizing/)\~[29](../29-grid-template-areas/)번이고 여기서는 「그 항목이 BFC 를 연다」는 결론만 받아 온다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 동작은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**BFC 는 「안에서 일어난 일이 밖으로 안 새는 상자」다 — 방음실이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 벽이 뚫려 소리가 오가는 사무실 | 보통 블록 상자 (안쪽 `flow`) |
| 방음실 — 안의 소리가 안 새고 밖 소리도 안 들어온다 | **BFC 를 연 상자** (안쪽 `flow-root` 등) |
| 안에서 튼 음악이 복도로 새는 것 | **마진이 부모 밖으로 새는 것** |
| 방 안에 쌓인 짐을 벽이 못 버티는 것 | **`float` 때문에 부모 높이가 무너지는 것** |
| 옆방 소음이 내 책상까지 들어오는 것 | **바깥의 `float` 가 내 상자 안으로 파고드는 것** |

- **BFC 는 선언이 아니다.** `display: bfc` 같은 속성은 없다. **여러 선언의 부수 효과**로 열린다.
- 그중 **`display: flow-root` 만이 「BFC 를 여는 것」 자체를 뜻하는 값**이다. 나머지는 전부 다른 일을 하면서 덤으로 연다.
- 세 증상(마진 샘 · 높이 붕괴 · float 침범)은 **전부 같은 원인**이다 — 그 상자가 방음실이 아니라는 것.

```text
   보통 블록 (flow)                     BFC 를 연 상자 (flow-root)
  +--------------------+               +--------------------+
  |                    | 마진이 샌다    |                    |
  |   [자식]           | ---->         |   [자식]           |  마진이 갇힌다
  |                    |               |                    |
  |  [float]           |               |  [float]           |
  +--------------------+               |                    |
       |                               +--------------------+
       v float 가 삐져나온다                 float 를 끌어안는다
```

실무에서 이게 터지는 자리는 **「clearfix」라는 이름으로 전해 내려오는 주문**이다.\
`::after { content: ""; display: block; clear: both }` 도, `overflow: hidden` 도, 오늘은 **`display: flow-root` 한 줄**이면 된다.

> **서식 문맥(formatting context)** — 상자들이 서로 어떻게 배치되는지를 정하는 **독립된 구역**.\
> 예: 방 하나마다 가구 배치 규칙이 따로 도는 것과 같다. 옆방 가구가 내 방 배치에 끼어들지 않는다.

> **블록 서식 문맥(BFC, block formatting context)** — 블록 상자들이 위에서 아래로 쌓이는 규칙이 도는 구역.\
> 예: 문서 전체(루트 요소)가 이미 하나의 BFC 이고, 그 안에 중첩해서 새 BFC 를 열 수 있다.

> **BFC 루트(BFC root)** — 새 BFC 를 연 그 상자. 「방음실의 벽」에 해당한다.\
> 예: `display: flow-root` 를 준 `<div>` 가 BFC 루트다. 그 `<div>` **자신은 바깥 BFC 의 구성원**이고, **안쪽만 새 구역**이다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **어떤 선언이 BFC 를 만드는가** — 그리고 그 목록이 왜 이렇게 잡다한가.
2. BFC 가 **정확히 무엇 셋을 차단하는가.**
3. 같은 일을 하는 수단이 여럿인데 **왜 `display: flow-root` 가 답인가** — 나머지의 부작용은 무엇인가.

## 동작 방식

### (1) BFC 를 만드는 선언 — 실측으로 가려낸 목록

**언제 쓰나** — 「이 상자는 BFC 인가?」를 판정할 때. 이 목록이 이 주제의 좌표계다.

판별 방법 — 부모에 배경만 주고 자식에 `margin-top: 40px` 을 줬다.\
**마진이 새면 부모 높이가 자식 높이(20)뿐**이고, **갇히면 60**(마진 40 + 자식 20)이 된다.\
`float` 판정은 따로 — 부모 안에 `float` 만 넣고 **부모 높이가 살아 있으면 감싼 것**이다.

*(Chrome 151 headless 실측. 「부모 높이」는 마진 실험, 「float 감쌈」은 float 실험의 결과다.)*

| 선언 | 부모 높이 | float 감쌈 | BFC 인가 | 덤으로 따라오는 것 |
|---|---|---|---|---|
| (아무것도 안 함 — 보통 블록) | **20** (샘) | — | ✗ | — |
| `display: flow-root` | **60** | ✓ | **✓** | **없다** |
| `overflow: hidden` | **60** | ✓ | ✓ | **넘치는 내용이 잘린다** |
| `overflow: auto` | **60** | ✓ | ✓ | 필요하면 스크롤바가 생긴다 |
| `overflow: scroll` | **75** | ✓ | ✓ | **스크롤바가 늘 자리를 먹는다**(실측 +15px) |
| `overflow: clip` | **20** (샘) | **✗** | **✗ 아니다** | 잘리기만 한다 |
| `float: left` | **60** | ✓ | ✓ | 자신이 흐름에서 빠진다 |
| `position: absolute` | **60** | ✓ | ✓ | 자신이 흐름에서 빠진다 |
| `display: inline-block` | **60** | ✓ | ✓ | 줄 안에 놓이고 아래 빈틈이 생긴다 |
| `display: table-cell` | **60** | ✓ | ✓ | 표 규칙이 딸려 온다 |
| `display: grid` | **60** | ✓ | ✓ | 자식 배치가 통째로 바뀐다 |
| `contain: layout` | **60** | ✓ | ✓ | 컨테인먼트 비용 |
| `display: flex` | 60 | ✓ | ✓ | 자식이 flex 항목이 되어 `float` 선언 자체가 무시된다 |

그림 해설 (한 단계씩):

- **목록이 잡다한 이유**는 BFC 가 **이 선언들의 목적이 아니라 부작용**이기 때문이다.\
  `overflow: hidden` 의 목적은 자르는 것이고, BFC 는 자르려면 안쪽이 독립돼야 해서 딸려 온 것이다.
- ★ **`overflow: clip` 은 BFC 가 아니다.** 「`overflow` 가 `visible` 이 아니면 BFC」라는 흔한 요약이 **여기서 깨진다.**\
  `clip` 은 스크롤 컨테이너를 만들지 않으므로 안쪽을 독립시킬 이유가 없다((5)에서 실측으로 다시 본다).
- **`display: flow-root` 만 부작용 칸이 비어 있다.** 이것이 이 주제의 결론이다.
- ★ **`flex`·`grid` 는 「감쌌다」의 뜻이 다르다.** 그 자식은 flex/grid 항목이 되어 **`float` 선언 자체가 무시**되므로, 애초에 삐져나갈 float 가 없다. 높이가 살아난 것은 같지만 기제가 다르다.
- `display: flex`·`grid` 컨테이너의 **항목**도 각각 BFC 를 연다 — 그래서 [18번](../18-margin-collapsing/2-summary.md)에서 flex 항목에는 마진 상쇄가 없다. flex 배치 규칙 자체는 [24번](../24-flexbox-axes/2-summary.md)이 정본이다.

비용 — `flow-root` 는 레이아웃 방식을 안 바꾸므로 사실상 공짜다. `overflow` 계열은 **스크롤 컨테이너를 만드는 비용**이 따로 있다([목록의 **23번 주제**](../23-overflow-and-scroll-containers/)).

### (2) 효과 ① 마진이 밖으로 안 샌다

**언제 쓰나** — 「부모에 배경만 줬는데 자식 마진이 부모를 밀고 나갈 때.」

```text
  보통 블록                              display: flow-root
  ===== 기준선 =====                     ===== 기준선 =====
        ↑ 40 (부모 밖)                   +------------------+  부모 상자 시작
  +------------------+  부모 상자 시작   |  ↑ 40 (부모 안)  |
  |   [자식 30]      |                  |   [자식 30]      |
  +------------------+  부모 높이 30     +------------------+  부모 높이 70
```

*(Chrome 151 headless 실측 — 기준선(빨간 막대) 바로 아래에 부모를 놓고 쟀다. 보통 블록: 기준선 bottom=6, 부모 top=**46** — **40px 이 부모 밖에 있다.** 부모 높이 30. `flow-root`: 부모 top=**82**(기준선 bottom=76 바로 뒤, **간격 0**), 부모 높이 **70**, 자식 top=122 — 40px 이 부모 안에 있다.)*

- 마진이 「새는」 것이 아니라 **자식의 위 마진과 부모의 위 마진이 하나로 합쳐지는** 것이다. 그 규칙의 정본은 [18번](../18-margin-collapsing/2-summary.md).
- BFC 를 열면 **부모의 위 경계와 자식의 위 마진이 서로 만나지 못해** 합쳐질 수 없다.
- demo 와 나머지 두 막는 법(`padding` 한 칸·`border` 한 칸)은 [18번](../18-margin-collapsing/2-summary.md)이 정본이다 — 여기서는 **BFC 가 그중 하나**라는 것까지다.

### (3) 효과 ② `float` 를 감싼다 — 높이 붕괴 해결

**언제 쓰나** — 안에 `float` 만 들어 있는 상자의 높이가 0 이 될 때. **이 주제에서 가장 오래된 사고다.**

```html demo
<div class="p" style="display: flow-root"><div class="f">float</div></div>
<div class="next">다음 형제</div>
<div class="p"><div class="f">float</div></div>
<div class="next">다음 형제</div>
<style>
  .p { width: 260px; border: 2px solid #64748b; background: #fef9c3; }
  .f { float: left; width: 90px; height: 60px; background: #93c5fd; font: 12px system-ui; }
  .next { width: 260px; height: 24px; background: #fecaca; font: 12px system-ui; margin-bottom: 30px; }
</style>
```

> **보이는 것** — 위쪽(`flow-root`)에서는 **노란 부모 상자가 파란 float 를 감싸** float 오른쪽으로 노란 배경이 보이고, 분홍 「다음 형제」는 그 아래에 온다. 아래쪽(보통 블록)에서는 **노란 상자가 납작한 회색 선 한 줄로 찌그러지고**, 파란 float 가 그 선 아래로 통째로 삐져나오며, **분홍 「다음 형제」가 float 오른쪽을 뚫고 지나간다.**\
> **바꿔 볼 것** — 아래 `.p` 에 `display: flow-root` 를 추가 → 위쪽과 똑같아진다 · `flow-root` 대신 `overflow: hidden` → 높이는 똑같이 살아난다((5)를 보라)

*(Chrome 151 headless 실측 — `flow-root` 부모: `rect` top=0 bottom=**64**(float 60 + 테두리 4), 다음 형제 top=**64** 로 부모 바로 아래. 보통 부모: `rect.height` **4** — 위아래 테두리뿐이고 안쪽 높이가 0 이다. 부모 bottom=122 이고 다음 형제 top 도 **122** 인데, **float(높이 60)는 y=120\~180 까지 내려와 그 형제 위를 뚫고 지나간다.**)*

- **float 는 부모의 높이 계산에 참여하지 않는다.** 그것이 float 의 정의다(정본은 [목록의 **20번 주제**](../20-float-and-clear/)).
- **BFC 루트만은 예외로 자기 안의 float 까지 포함해 높이를 잡는다.** 그것이 여기서 다루는 「감싼다」이다.
- 옛날 「clearfix」 주문이 하던 일을 **`display: flow-root` 한 줄이 대신한다.**

### (4) 효과 ③ 바깥 `float` 옆으로 안 흐른다

**언제 쓰나** — float 옆에 놓인 상자가 float 밑으로 파고들어 배경이 겹칠 때.

```html demo
<div class="col">
  <div class="f">float</div>
  <div class="t">보통 상자다. 첫 줄만 float 에 밀리고 float 가 끝나는 높이부터는 상자 폭 전체를 쓴다.</div>
</div>
<div class="col">
  <div class="f">float</div>
  <div class="t" style="display: flow-root">BFC 상자다. 상자 자체가 float 를 피해 좁아졌으므로 모든 줄이 같은 폭으로 흐른다.</div>
</div>
<style>
  .col { display: flow-root; width: 300px; border: 2px solid #64748b; margin-bottom: 12px; }
  .f { float: left; width: 100px; height: 34px; background: #93c5fd; font: 12px system-ui; }
  .t { background: #fecaca; font: 13px/1.5 system-ui; }
</style>
```

> **보이는 것** — 위 상자의 분홍 배경은 **첫 두 줄은 float 오른쪽에만 있다가, float 가 끝나는 셋째 줄부터 왼쪽 끝까지 넓어진다**(분홍이 파란 float 아래로 이어진다). 아래 상자의 분홍 배경은 **세 줄 내내 float 오른쪽에서 시작해** float 아래쪽은 흰 채로 남는다.\
> **바꿔 볼 것** — 아래 `.t` 의 `display: flow-root` 를 지우면 위 상자와 똑같아진다 · `.f` 의 `height` 를 `80px` 로 키워 두 상자의 분홍 배경이 어떻게 달라지는지 보라

*(Chrome 151 headless 실측 — 보통 상자: `rect.x`=2, `rect.width`=**300** — **컨테이너 폭 전체**다. 상자가 float 밑까지 깔려 있고 밀려난 것은 **글줄뿐**이다. BFC 상자: `rect.x`=**102**, `rect.width`=**200** — float 폭 100 만큼 **상자 자체가 좁아지고 오른쪽으로 밀렸다.** 둘의 높이는 58.5 로 같다.)*

- ★ **「밀렸다」의 뜻이 둘에서 다르다.**\
  보통 상자는 **상자는 그대로 깔리고 글줄만** 밀린다. BFC 상자는 **상자 자체**가 밀린다.
- 이것이 「사이드바(float) 옆에 본문을 놓을 때 본문에 BFC 를 열면 깔끔해지는」 옛 관용구의 근거다.
- **float 가 왜 글줄을 미는지, `clear` 가 무엇을 하는지는** [목록의 **20번 주제**](../20-float-and-clear/)가 정본이다.

### (5) `display: flow-root` 대 `overflow: hidden` — 부작용 대조

**언제 쓰나** — 「`overflow: hidden` 으로 되던데 왜 `flow-root` 를 쓰나?」에 답할 때. **이 주제의 결론 자리다.**

```html demo
<div class="p" style="display: flow-root"><div class="big">flow-root — 안 잘린다</div></div>
<div class="p" style="overflow: hidden"><div class="big">overflow:hidden — 잘린다</div></div>
<style>
  .p { width: 160px; height: 40px; border: 2px solid #64748b; margin-bottom: 40px; }
  .big { width: 240px; height: 34px; background: #fca5a5; font: 12px system-ui; }
</style>
```

> **보이는 것** — 두 부모 상자는 폭이 같다(160px). 위쪽에서는 **붉은 자식이 부모 테두리를 오른쪽으로 뚫고 나와 끝까지 보이고** 글자도 온전하다. 아래쪽에서는 **붉은 자식이 부모 테두리에서 딱 잘려** 오른쪽 부분이 사라진다.\
> **바꿔 볼 것** — 아래 `overflow: hidden` → `auto` → 잘리는 대신 **가로 스크롤바가 생긴다**(실측: 부모의 `clientWidth` 가 160 → 145 로 15px 줄었다) · `.big` 의 `width` 를 `140px` 로 줄이면 **두 자식이 140 으로 똑같아진다**(넘치지 않으므로)

*(Chrome 151 headless 실측 — ★ **여기서 `rect` 는 아무 차이도 안 알려 준다.** 두 자식 모두 `rect` 가 **240×34 로 동일**하다. 잘린 것은 **레이아웃이 아니라 페인트**이기 때문이다. 이 자리의 근거는 **스크린샷**이다.)*

```text
  flow-root                            overflow: hidden
  +------------------+                 +------------------+
  |  [ 자식 240 ------|---->            |  [ 자식 240 ]    |  ← 여기서 싹둑
  +------------------+                 +------------------+
   레이아웃도 240, 화면도 240            레이아웃은 240, 화면은 156
```

- ★ **`getBoundingClientRect()` 가 거짓말하는 자리다.** 「잘렸나」는 rect 로 못 잰다.
- `overflow` 계열의 부작용을 정리하면:
  - `hidden` — **잘린다.** 드롭다운·툴팁·포커스 링이 사라지는 사고의 원인.
  - `auto` — 넘치면 **스크롤바가 생긴다.**
  - `scroll` — **늘 스크롤바가 자리를 먹는다.** 실측에서 부모 높이가 60 대신 **75** 였다(가로 스크롤바 15px).
  - 셋 다 **스크롤 컨테이너**가 되어 `position: sticky`·스크롤 앵커링 같은 것에도 영향을 준다([목록의 **23번 주제**](../23-overflow-and-scroll-containers/)).
- `display: flow-root` 는 **잘리지도, 스크롤바가 생기지도, 스크롤 컨테이너가 되지도 않는다.**\
  ★ **「부작용 없이 BFC 만 만드는 유일한 수단」이라는 것이 이 주제의 결론이다.**

### (6) `overflow: clip` 은 BFC 가 아니다 — 흔한 요약이 깨지는 자리

**언제 쓰나** — 「`overflow` 를 `visible` 말고 아무거나 주면 된다」고 외운 뒤.

```html demo
<div class="p" style="overflow: hidden"><div class="f">float</div></div>
<div class="p" style="overflow: clip"><div class="f">float</div></div>
<style>
  .p { width: 240px; background: #fef9c3; border: 2px solid #64748b; margin-bottom: 70px; }
  .f { float: left; width: 90px; height: 54px; background: #93c5fd; font: 12px system-ui; }
</style>
```

> **보이는 것** — 위쪽(`hidden`)은 **노란 부모 상자가 파란 float 를 감싸** 제 높이를 갖는다. 아래쪽(`clip`)은 **노란 상자가 납작한 선 한 줄로 찌그러지고, 파란 float 도 화면에서 사라진다** — 감싸지도 않았고(높이 0), `clip` 이라 잘려 나갔기 때문이다.\
> **바꿔 볼 것** — 아래 `overflow: clip` → `overflow: hidden` → 위와 똑같아진다 · `clip` 을 **그대로 두고** `display: flow-root` 를 함께 주면 높이가 **58 로 살아난다**(그때는 `flow-root` 가 BFC 를 연다 — 실측)

*(Chrome 151 headless 실측 — `overflow: hidden` 부모 `rect.height` **58**(float 54 + 테두리 4). `overflow: clip` 부모 `rect.height` **4** — **테두리뿐이다.** 마진 실험에서도 `clip` 부모는 높이가 20 으로 **자식 마진이 밖으로 샜다.**)*

- **`clip` 은 스크롤 컨테이너를 만들지 않는다** — 스크롤 자체가 불가능한 값이다. 그래서 안쪽을 독립시킬 이유가 없어 **BFC 도 만들지 않는다.**
- 외울 것은 「`overflow` 가 `visible` 이 아니면 BFC」가 아니라 **「스크롤 컨테이너가 되는 `overflow` 값이면 BFC」** 다.
- `overflow` 값들의 정본은 [목록의 **23번 주제**](../23-overflow-and-scroll-containers/)다.

## 문법 — 형태와 어디서 헷갈리나

### 최소 형태

```css
.wrap { display: flow-root; }   /* 이것이 「BFC 를 열어라」라는 뜻의 유일한 값 */
```

- `display: bfc` 같은 값은 **없다.** BFC 는 **속성이 아니라 상태**다.
- `flow-root` 는 **바깥 값이 `block`** 이므로(`block flow-root`), 상자가 한 줄을 통째로 쓰는 성질은 `block` 과 같다([16번](../16-display-inner-outer/2-summary.md)).

### 헷갈리는 자리 — 「누가 BFC 안에 있나」

```text
  <div class="outer">            <- 바깥 BFC 의 구성원
    <div class="root">           <- 자신은 바깥 BFC 의 구성원 · 안쪽에 새 BFC 를 연다
      <div class="inner"></div>  <- 새 BFC 의 구성원
    </div>
  </div>
```

- **BFC 루트 자신은 새 BFC 의 구성원이 아니다.** 그래서 **`.root` 자신의 마진은 여전히 바깥과 상쇄된다.**
- 「`flow-root` 를 줬는데 위쪽 형제와의 간격이 그대로다」는 고장이 아니다 — **막히는 것은 자식의 마진**이지 자기 마진이 아니다.

### 금지에 가까운 형태

```css
.a { overflow: clip; }                 /* BFC 가 아니다 — (6) */
.b::after { content: ""; display: block; clear: both; }   /* 옛 clearfix — 오늘은 불필요 */
.c { overflow: hidden; }               /* 되긴 하지만 잘린다 — (5) */
```

- 옛 clearfix 는 **의사 요소 하나를 더 만들고 `clear` 를 거는** 우회로다. `flow-root` 가 있는 오늘은 쓸 이유가 없다.

## 구현 세부사항 대 언어 보장

- **「어떤 선언이 BFC 를 만드나」는 명세가 정한다.** CSS Display Level 3 의 서식 문맥 규정이 근거다.
- **「스크롤바가 몇 px 을 먹나」는 구현이다.** 실측에서 `overflow: scroll` 부모가 60 대신 75 였는데, **15px 은 이 플랫폼의 스크롤바 폭**이지 CSS 의 보장이 아니다. 다른 OS·설정에서는 0 일 수도 있다.
- **`overflow: clip` 이 BFC 가 아니라는 것은 명세 쪽 사실**이고 이 브라우저의 실측이 그것과 맞았다. 다만 **이 문서는 실측한 값만 적었다.**
- ★ **「잘렸다」는 `getBoundingClientRect()` 로 관찰할 수 없다.** (5)에서 두 경우의 rect 가 완전히 같았다.\
  **레이아웃 API 로 못 보는 것이 있다**는 사실 자체가 이 주제의 교훈이다 — **「안 보인다」는 「없다」가 아니다.**

## 어디서 틀리나

### 1. 「`overflow` 를 `visible` 말고 아무거나」로 외운다

**`clip` 에서 깨진다**((6) 실측). 바른 기억: **스크롤 컨테이너가 되는 값**이어야 한다.

### 2. `overflow: hidden` 으로 clearfix 를 한다

높이는 살아나지만 **드롭다운·툴팁·포커스 링이 잘린다.** 잘림은 rect 로 안 보이므로 **한참 뒤에 발견된다.**\
`display: flow-root` 로 바꾸면 그 부작용이 없다.

### 3. `flow-root` 를 줬는데 자기 마진이 안 막힌다

BFC 루트는 **자기 안쪽만** 새 구역으로 만든다. **자기 자신의 마진은 바깥 BFC 소속**이라 그대로 상쇄된다.

### 4. float 가 「안 밀렸다」고 생각한다

(4) 실측대로 **보통 상자는 밀리지 않는다 — 글줄만 밀린다.** 배경이 float 밑에 깔려 있는데 float 가 위에 그려져 **눈으로는 밀린 것처럼 보인다.**\
rect 를 재야 갈린다.

### 5. BFC 를 「성능 최적화」로 생각한다

BFC 는 **배치 규칙**이지 격리 최적화가 아니다. 렌더 비용을 줄이는 컨테인먼트(`contain`·`content-visibility`)는 [목록의 **56번 주제**](../56-rendering-pipeline-and-will-change/)다.\
다만 `contain: layout` 은 **덤으로 BFC 를 연다**((1) 실측).

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 고르는 것 | 왜 |
|---|---|---|
| 자식 마진이 새는 것만 막고 싶다 | `display: flow-root` | 부작용 없음 |
| float 를 감싸 높이를 살리고 싶다 | `display: flow-root` | 옛 clearfix 를 대체 |
| float 옆 본문이 밑으로 파고드는 것을 막고 싶다 | `display: flow-root` | 상자 자체가 float 를 피한다 |
| 넘치는 것을 **정말로 자르고** 싶다 | `overflow: hidden`(또는 `clip`) | 자르는 것이 목적일 때만 |
| 안을 스크롤하고 싶다 | `overflow: auto` | 스크롤이 목적일 때만(23번) |
| 배치 규칙 자체를 바꾸고 싶다 | `display: flex`/`grid` | BFC 는 덤이다 |

판단 규칙 두 줄.

- **BFC 가 목적이면 `display: flow-root`.** 나머지는 전부 다른 목적의 부수 효과다.
- **부수 효과로 BFC 를 얻고 있다면 그 부수 효과가 진짜 원하는 것인지 확인한다.** 아니면 나중에 잘리거나 스크롤바가 생긴다.

## 핵심 문장

- BFC 는 **「안에서 일어난 일이 밖으로 안 새는 상자」** 다. 선언이 아니라 **상태**다.
- 효과는 셋 — ① **자식 마진이 밖으로 안 샌다** ② **안의 `float` 를 감싸 높이가 살아난다** ③ **바깥 `float` 옆으로 파고들지 않는다.**
- `display: flow-root` 는 **부작용 없이 BFC 만 여는 유일한 수단**이다. `overflow: hidden` 은 잘리고, `scroll` 은 스크롤바가 자리를 먹는다(실측 +15px).
- ★ **`overflow: clip` 은 BFC 가 아니다** — 「`visible` 이 아니면 BFC」라는 요약이 여기서 깨진다.
- **BFC 루트 자신은 새 구역의 구성원이 아니다** — 자기 마진은 여전히 바깥과 상쇄된다.
- ★ **「잘렸나」는 `getBoundingClientRect()` 로 잴 수 없다.** (5)에서 두 경우의 rect 가 완전히 같았다 — 근거는 스크린샷이다.

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 17번)
- [16번 주제](../16-display-inner-outer/2-summary.md)(`display` 의 내부/외부 값) — **`flow` 와 `flow-root` 가 `display` 의 안쪽 값으로 갈린다**는 것은 거기. 여기는 **그 차이가 무엇을 만드는가**다
- [18번 주제](../18-margin-collapsing/2-summary.md)(마진 상쇄) — **마진이 합쳐지는 규칙 자체와 막는 법 전수**는 거기. 여기는 **BFC 가 그중 하나**라는 것까지다
- [15번 주제](../15-box-model-and-box-sizing/2-summary.md)(박스 모델) — 상자의 치수가 정해지는 규칙
- [목록의 **20번 주제**](../20-float-and-clear/)(부동과 해제) — ★ **`float` 자체가 무엇을 하는지, `clear` 가 무엇을 하는지는 거기가 정본**이다. 여기는 **BFC 가 float 를 감싸고 피한다**는 효과까지다
- [목록의 **23번 주제**](../23-overflow-and-scroll-containers/)(오버플로·스크롤 컨테이너) — `overflow` 값들의 정본. 여기서는 **BFC 를 만드느냐**만 본다
- [목록의 **21번 주제**](../21-position-and-containing-block/)(`position` 과 포함 블록) — `absolute` 가 BFC 를 여는 것은 여기 표에 있지만 **기준을 어디로 잡는가**는 거기
- [24번 주제](../24-flexbox-axes/2-summary.md)(Flexbox) — **flex 항목이 BFC 를 연다**는 결론만 여기서 쓰고, 축·정렬은 거기가 정본이다
- [목록의 **56번 주제**](../56-rendering-pipeline-and-will-change/)(렌더링 파이프라인·`contain`) — `contain: layout` 의 본래 목적과 비용
- [`reference/render-rules.md`](../../../../../../reference/render-rules.md) — 이 문서의 `demo` 블록 규칙

## 용어 풀이

- **서식 문맥(formatting context)** — 상자들의 배치 규칙이 도는 독립된 구역.
- **블록 서식 문맥(BFC)** — 블록 상자가 위에서 아래로 쌓이는 규칙이 도는 구역. 루트 요소가 이미 하나의 BFC 다.
- **BFC 루트** — 새 BFC 를 연 상자. **자신은 바깥 BFC 의 구성원**이고 안쪽만 새 구역이다.
- **`display: flow-root`** — 「BFC 를 열어라」를 직접 뜻하는 유일한 값. 부작용이 없다.
- **높이 붕괴(height collapse)** — 안에 `float` 만 있는 상자의 높이가 0 이 되는 현상. float 가 높이 계산에 참여하지 않기 때문이다.
- **clearfix** — 의사 요소와 `clear` 로 높이 붕괴를 우회하던 옛 관용구. 오늘은 `flow-root` 로 대체된다.
- **스크롤 컨테이너(scroll container)** — 안쪽을 스크롤할 수 있는 상자. `overflow` 가 `auto`·`scroll`·`hidden` 일 때 만들어진다. `clip` 은 만들지 않는다.
- **`overflow: clip`** — 넘치는 것을 자르되 **스크롤은 불가능한** 값. **BFC 를 만들지 않는다.**
- **컨테인먼트(containment)** — `contain` 으로 렌더 작업을 상자 안에 가두는 최적화. `layout` 값은 덤으로 BFC 를 연다.

---

## 더 들어가면

- **서식 문맥은 BFC 만 있는 것이 아니다.** 인라인 서식 문맥(IFC)·flex 서식 문맥·grid 서식 문맥·표 서식 문맥이 각각 있다.\
  「`display` 의 안쪽 값이 서식 문맥의 종류를 고른다」고 읽으면 [16번](../16-display-inner-outer/2-summary.md)과 딱 이어진다. IFC 는 [목록의 **19번 주제**](../19-inline-formatting-context/)다.
- **`display: flow-root` 라는 이름의 뜻** — 「이 상자를 **흐름의 뿌리(root)** 로 삼아라」이다.\
  문서 전체의 루트 요소가 하는 일을 이 상자 안에서 다시 하라는 것이라, 이름 자체가 동작의 설명이다.
- **`position: absolute` 가 BFC 를 여는 것**은 (1)에서 실측했지만, 그 상자는 **흐름에서 빠져** 있어 마진 상쇄 이야기가 애초에 성립하지 않는 경우가 많다.\
  「BFC 를 열려고 `absolute` 를 쓴다」는 선택은 거의 없다 — 목적이 전혀 다르기 때문이다([목록의 **21번 주제**](../21-position-and-containing-block/)).
- **BFC 와 쌓임 맥락(stacking context)은 다른 것이다.** `opacity`·`transform` 은 쌓임 맥락을 만들지만 BFC 와는 무관하다.\
  둘을 섞으면 「`z-index` 가 안 먹는다」와 「마진이 샌다」를 같은 원인으로 오진하게 된다. 쌓임 맥락은 [목록의 **22번 주제**](../22-stacking-context-and-z-index/)다.

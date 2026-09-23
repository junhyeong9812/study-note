# css/syntax/22 — 쌓임 맥락과 `z-index` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [CSS Positioned Layout Module Level 3](https://drafts.csswg.org/css-position-3/) 의 「Painting Order」·「Stacking Contexts」 절 (쌓임 맥락과 `z-index` 의 정본) · [CSS Compositing and Blending Level 1](https://drafts.csswg.org/css-compositing-1/) (`isolation`·`mix-blend-mode`). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 `demo` 블록 **4개 전부**와 **쌓임 맥락을 만든다고 알려진 선언 15가지**를 **Google Chrome 151.0.7922.173** headless 에 실제로 띄워 판정했다.\
> ★★ **이 주제는 `getBoundingClientRect()` 로 아무것도 알 수 없다.** 「누가 위에 있나」는 좌표가 아니라 **페인트**다. 그래서 **겹치는 지점의 스크린샷 픽셀 RGB 를 읽어** 판정했다 — 이 문서의 모든 ✓/✗ 는 그 픽셀 값이다.\
> **WebKit(Safari)은 이 머신에 없고 Firefox 는 이 환경에서 headless 스크린샷이 산출되지 않는다** — 크로스 브라우저 주장은 하지 않았다.
> **여기서 다루지 않는 것** — **어디에 놓이나(포함 블록)는 [21번](../21-position-and-containing-block/2-summary.md)이 정본**이고, 여기는 **누가 위에 그려지나**다. 두 주제의 「만드는 선언」 목록이 **겹치지만 같지 않다** — 그 대조표는 [21번](../21-position-and-containing-block/2-summary.md)에 있다. BFC 는 [17번](../17-block-formatting-context/2-summary.md)(**쌓임 맥락과 다른 것이다**), float 의 동작은 [20번](../20-float-and-clear/2-summary.md), 행 상자는 [19번](../19-inline-formatting-context/2-summary.md)이다. `mix-blend-mode`·`isolation` 의 **혼합 규칙 자체**는 [목록의 **48번 주제**](../48-blend-modes-and-isolation/), `filter` 는 **47번 주제**이고 여기서는 **쌓임 맥락을 만드느냐**만 본다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 판정은 픽셀로 접지했다.

## 한눈에 — 쉽게 말하면

**쌓임 맥락은 「같은 리그 안에서만 순위를 매긴다」는 규칙이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 리그 (1부 / 2부) | **쌓임 맥락**(stacking context) |
| 리그 안의 순위 | `z-index` |
| **2부 리그 1위가 1부 리그 꼴찌를 못 이기는 것** | 부모의 `z-index` 가 낮으면 자식의 `z-index: 9999` 도 소용없다 |
| 팀을 2부 리그로 **강등시키는 규정** | `opacity`·`transform`·`filter` 같은 선언 |
| 전체 대회 | 루트 쌓임 맥락(`<html>`) |

```text
   같은 마크업, 부모의 선언만 다르다

   부모에 z-index 없음                 부모에 opacity: 0.99
  +---------------------------+       +---------------------------+
  |   자식 z:9999  ──> 위     |       |   자식 z:9999  ──> 아래   |
  |   형제 z:2                |       |   형제 z:2     ──> 위     |
  +---------------------------+       +---------------------------+
   겹침 픽셀 = (255,0,0) 빨강          겹침 픽셀 = (0,0,255) 파랑
```

*(Chrome 151 headless 실측 — 같은 지점의 스크린샷 RGB. **`opacity: 0.99` 하나가 자식을 가둔다.**)*

실무에서 이게 터지는 자리는 **"`z-index: 9999` 를 줬는데도 안 올라온다"** 는 증상이다.\
원인은 거의 언제나 **조상 어딘가에 쌓임 맥락이 생겨** 그 안에 갇힌 것이다.

> **쌓임 맥락(stacking context)** — 그 안의 요소들끼리만 `z-index` 로 순서를 겨루는 독립된 구역.\
> 예: 리그가 다르면 순위를 직접 비교할 수 없다. **구역 전체가 한 덩어리로 부모 구역에 끼어든다.**

> **`z-index`** — 같은 쌓임 맥락 안에서의 앞뒤 순서. 기본값은 `auto` 이고, **`position` 이 `static` 이면 통째로 무시된다**(flex/grid 항목은 예외).\
> 예: `z-index: 2` 가 `z-index: 1` 위에 그려진다. **다른 맥락의 9999 와는 비교되지 않는다.**

> **페인트 순서(painting order)** — 같은 맥락 안에서 무엇을 먼저 그리는지의 정해진 차례. 나중에 그린 것이 위에 보인다.\
> 예: 배경 → 음수 z → 블록 → float → 인라인 → z:auto/0 → 양수 z 순서다((3)).

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `z-index: 9999` 가 **왜 안 먹는가** — 무엇이 그것을 가두는가.
2. **무엇이 쌓임 맥락을 만드는가** — 그리고 그 목록이 왜 잡다한가.
3. `z-index` 를 아무도 안 줬을 때 **누가 위에 그려지는가.**

## 동작 방식

### (1) `z-index` 는 쌓임 맥락 안에서만 비교된다

**언제 쓰나** — 「9999 를 줬는데 안 올라온다」를 만났을 때. **이 절이 이 주제의 전부다.**

```text
  마크업은 똑같다

  <div class="부모A"> <div class="자식" z-index:9999>빨강</div> </div>
  <div class="부모B" z-index:2> <div>파랑</div> </div>

  ① 부모A 에 아무것도 없을 때            ② 부모A 에 z-index:1 을 줬을 때
     루트 리그에 셋이 함께 있다              부모A 가 리그를 하나 연다
        자식 9999 > 부모B 2                  루트 리그: 부모A(1) vs 부모B(2)
        ──> 빨강이 위                        ──> 부모B 가 이긴다 ──> 파랑이 위
                                             자식의 9999 는 부모A 리그 안에서만 유효
```

*(Chrome 151 headless 실측 — 겹치는 지점의 스크린샷 RGB. ① **(255,0,0) 빨강** · ② **(0,0,255) 파랑**. 두 경우의 `getBoundingClientRect()` 는 **완전히 같다** — 좌표로는 아무것도 알 수 없는 자리다.)*

```html demo
<div class="stage"><div class="p"><b class="c"></b></div><div class="q"><b class="d"></b></div></div>
<div class="stage"><div class="p" style="z-index:1"><b class="c"></b></div><div class="q"><b class="d"></b></div></div>
<style>
  .stage { position: relative; z-index: 0; display: flow-root;
           width: 260px; height: 90px; background: #e5e7eb; margin-bottom: 10px; }
  .p, .q { position: relative; }
  .q { z-index: 2; }
  .stage b { position: absolute; width: 130px; height: 60px; }
  .c { left: 10px; top: 15px; background: #ef4444; z-index: 9999; }
  .d { left: 90px; top: 25px; background: #2563eb; }
</style>
```

> **보이는 것** — 회색 판 두 개에 빨강·파랑 네모가 똑같이 겹쳐 있다. **위 판에서는 빨강이 파랑 위**에 있고, **아래 판에서는 파랑이 빨강 위**에 있다 — 겹치는 부분의 색이 서로 반대다. 두 판의 차이는 빨강의 **부모**에 `z-index: 1` 이 붙었는지뿐이고, 빨강의 `z-index: 9999` 는 둘 다 그대로다.\
> **바꿔 볼 것** — 아래 판 부모의 `z-index: 1` → `z-index: 3` (**빨강이 다시 위로 온다** — 부모끼리의 싸움에서 이기므로) · `z-index: 1` → `opacity: 0.99` (**똑같이 파랑이 이긴다** — (2))

- ★ **자식의 `z-index` 는 자기 맥락의 담장을 못 넘는다.** 밖에서 보면 **부모 덩어리 하나**로만 보인다.
- 그래서 고치는 법은 자식의 숫자를 키우는 것이 **아니라**, **부모끼리의 순서를 고치거나 담장을 없애는 것**이다.
- 「`z-index` 인플레이션」(9999 → 99999)이 안 통하는 이유가 이것이다.

비용 — 없다. 다만 **담장이 어디 생겼는지 찾는 비용**이 크다. 그래서 (2)의 목록이 필요하다.

### (2) 무엇이 쌓임 맥락을 만드나 — 픽셀로 가려낸 목록

**언제 쓰나** — 「담장을 누가 세웠나」를 추적할 때. **이 목록이 이 주제의 좌표계다.**

판정 방법 — 래퍼 안에 `z-index: 9999` 인 빨강을, 밖에 `z-index: 2` 인 파랑을 두고 **겹치는 지점의 RGB 를 읽었다.**\
**빨강(255,0,0)이면 담장이 없는 것**(9999 가 밖까지 통했다), **파랑(0,0,255)이면 담장이 생긴 것**이다.

*(Chrome 151 headless 실측 — 스크린샷 픽셀.)*

| 래퍼의 선언 | 겹침 픽셀 | 쌓임 맥락 |
|---|---|---|
| (아무것도 없음) | **(255,0,0)** | ✗ |
| `position: relative` (z-index 없음) | (255,0,0) | ✗ |
| `position: relative; z-index: 1` | (0,0,255) | **✓** |
| `position: sticky` (z-index 없음) | (0,0,255) | **✓ — 예외** |
| **`opacity: 0.99`** | **(0,0,255)** | **✓** |
| `opacity: 0.999` | (0,0,255) | **✓** |
| **`opacity: 1`** | **(255,0,0)** | **✗** |
| `transform: translateZ(0)` | (0,0,255) | ✓ |
| `filter: blur(0px)` | (0,0,255) | ✓ |
| `backdrop-filter: blur(0px)` | (0,0,255) | ✓ |
| `isolation: isolate` | (0,0,255) | ✓ |
| **`mix-blend-mode: normal`** | **(255,0,0)** | **✗** |
| `mix-blend-mode: multiply` | (0,0,255) | ✓ |
| `will-change: opacity` | (0,0,255) | ✓ |
| `contain: paint` | (0,0,255) | ✓ |
| `contain: layout` | (0,0,255) | ✓ |
| flex/grid 항목 + `z-index: 0` | (0,0,255) | ✓ |
| flex/grid 항목 + `z-index: auto` | (255,0,0) | ✗ |
| 보통 블록(`static`) + `z-index: 0` | (255,0,0) | ✗ |

```html demo
<div class="stage"><div class="p"><b class="c"></b></div><div class="q"><b class="d"></b></div></div>
<div class="stage"><div class="p" style="opacity:0.99"><b class="c"></b></div><div class="q"><b class="d"></b></div></div>
<style>
  .stage { position: relative; z-index: 0; display: flow-root;
           width: 260px; height: 90px; background: #e5e7eb; margin-bottom: 10px; }
  .p, .q { position: relative; }
  .q { z-index: 2; }
  .stage b { position: absolute; width: 130px; height: 60px; }
  .c { left: 10px; top: 15px; background: #ef4444; z-index: 9999; }
  .d { left: 90px; top: 25px; background: #2563eb; }
</style>
```

> **보이는 것** — 두 판이 똑같아 보이는데 **겹친 부분의 색만 반대**다. 위 판은 빨강이 파랑을 덮고, 아래 판은 파랑이 빨강을 덮는다. 아래 판의 빨강은 `opacity: 0.99` 때문에 **아주 조금 흐린데 눈으로는 거의 구분되지 않는다** — 그런데도 순서가 뒤집혔다.\
> **바꿔 볼 것** — `opacity: 0.99` → `opacity: 1` (**위 판과 똑같아진다** — 담장이 사라진다) · `opacity: 0.99` → `isolation: isolate` (**아래 판과 똑같다** — 투명도 변화 없이 담장만 선다)

그림 해설 (한 단계씩):

- ★★ **`opacity: 0.99` 하나가 자식을 가둔다.** 화면상 1% 흐려질 뿐이라 **눈으로는 못 잡는다.** 가장 당황스러운 자리다.
- ★ **`opacity: 1` 은 안 만든다.** 경계는 「1 미만이냐」이고, `0.999` 도 만든다(실측).
- ★ **`mix-blend-mode: normal` 은 안 만든다.** 「`mix-blend-mode` 가 있으면 만든다」로 외우면 여기서 깨진다 — **`normal` 이 아닌 값**이어야 한다.
- **`position: sticky` 는 `z-index` 가 `auto` 여도 만든다.** `relative` 와 달라지는 예외다.
- **`position: static` 에 `z-index` 를 줘도 아무 일도 안 일어난다** — 단 **flex/grid 항목은 예외**로, `position` 없이도 `z-index` 가 먹고 맥락을 만든다.
- **목록이 잡다한 이유**는 [17번](../17-block-formatting-context/2-summary.md)의 BFC 와 같다 — **쌓임 맥락이 이 선언들의 목적이 아니라 부작용**이기 때문이다. `opacity` 의 목적은 흐리게 하는 것이고, **흐리게 하려면 안쪽을 먼저 한 장으로 합성해야** 해서 담장이 딸려 온 것이다.
- ★ **이 목록은 [21번](../21-position-and-containing-block/2-summary.md)의 「포함 블록을 바꾸는 선언」과 겹치지만 같지 않다.** `opacity` 와 `isolation` 이 갈리는 자리다.

### (3) 페인트 순서 일곱 층

**언제 쓰나** — `z-index` 를 아무도 안 줬는데 겹침 순서가 이상할 때.

```text
  한 쌓임 맥락 안에서 그리는 차례 (아래부터 위로)

  ⑦ z-index 양수인 위치 지정 자손          ← 가장 위
  ─────────────────────────────────────
  ⑥ z-index 가 auto / 0 인 위치 지정 자손
  ─────────────────────────────────────
  ⑤ 인라인 내용 (글자·인라인 상자의 배경)
  ─────────────────────────────────────
  ④ float 된 상자
  ─────────────────────────────────────
  ③ 보통 흐름의 블록 상자 배경·테두리
  ─────────────────────────────────────
  ② z-index 음수인 위치 지정 자손
  ─────────────────────────────────────
  ① 이 맥락을 연 상자 자신의 배경·테두리   ← 가장 아래
```

*(Chrome 151 headless 실측 — 이웃한 두 층을 겹쳐 놓고 **겹치는 지점의 RGB** 를 여섯 번 읽었다. 각 줄의 「이긴 색」이 위층이다.)*

| 대결 | 아래층 색 | 위층 색 | 겹침 픽셀 | 이긴 것 |
|---|---|---|---|---|
| ① 맥락 배경 대 ② 음수 z | 회 (128,128,128) | 보라 (128,0,128) | **(128,0,128)** | ② 음수 z |
| ② 음수 z 대 ③ 블록 | 보라 | 초록 (0,128,0) | **(0,128,0)** | ③ 블록 |
| ③ 블록 대 ④ float | 초록 | 주황 (255,128,0) | **(255,128,0)** | ④ float |
| ④ float 대 ⑤ 인라인 | 주황 | 하늘 (0,255,255) | **(0,255,255)** | ⑤ 인라인 |
| ⑤ 인라인 대 ⑥ z:auto | 하늘 | 자홍 (255,0,255) | **(255,0,255)** | ⑥ z:auto |
| ⑥ z:auto 대 ⑦ z:1 | 자홍 | 빨강 (255,0,0) | **(255,0,0)** | ⑦ z:1 |

- ★ **`z-index: -1` 은 맥락 배경 위, 블록 배경 아래**다. 「배경 뒤로 보내기」 관용구가 그래서 동작한다.
- ★ **float 는 블록 배경 위, 글자 아래**다. 이것이 [20번](../20-float-and-clear/2-summary.md)에서 「배경이 float 밑으로 깔려 겹쳐 보인다」의 정확한 이유다 — 실측에서 그 겹침 픽셀이 **float 색**이었다.
- ★ **인라인 내용이 float 보다 위**다. 그래서 float 위로 글자가 지나가는 일이 생긴다([17번](../17-block-formatting-context/2-summary.md)의 높이 붕괴 실측이 그 모양이다).
- **위치 지정 요소는 `z-index` 를 안 줘도 ⑥층**이라 보통 블록·float·글자보다 위다. 「`position: relative` 만 줬는데 위로 올라왔다」의 이유다.

★ **②층이 「배경 뒤로」가 아니라 「블록 배경 뒤로」인 것**을 따로 본다.

```html demo
<div class="wrap"><div class="card">노란 카드</div><b class="deco"></b></div>
<style>
  .wrap { position: relative; z-index: 0; width: 220px; height: 90px;
          padding: 20px; background: #e5e7eb; font: 13px/24px system-ui; }
  .wrap .card { width: 120px; height: 50px; background: #fef08a; }
  .wrap .deco { position: absolute; left: 60px; top: 45px;
                width: 160px; height: 50px; background: #7c3aed; z-index: -1; }
</style>
```

> **보이는 것** — 보라 막대가 **노란 카드와 겹치는 부분에서만 사라지고**, 카드 밖(회색 바탕 위)에서는 **그대로 보인다.** 같은 하나의 보라 상자인데 **회색 배경은 못 가리고 노란 배경은 못 뚫는다.**\
> **바꿔 볼 것** — `.deco` 의 `z-index: -1` 을 지우면 **보라가 카드 위로 올라온다**(②층 → ⑥층) · `.wrap` 의 `z-index: 0` 을 지우면 보라가 **회색 배경 밑으로까지 내려가 아예 안 보인다**(담장이 없어져 더 위 조상의 배경과 겨루게 된다)

*(Chrome 151 headless 실측 — 겹치는 지점 (100,58) 의 픽셀이 **(254,240,138) 노랑**, 보라만 있는 지점 (210,70) 이 **(124,58,237) 보라**였다. ②층은 ①층 위, ③층 아래라는 것이 한 그림에서 다 보인다.)*

```html demo
<div class="stage">
  <i class="f">float</i>
  <b class="blk"></b>
  <u class="pz">position</u>
</div>
<style>
  .stage { position: relative; z-index: 0; display: flow-root; width: 300px;
           height: 90px; background: #cbd5e1; font: 12px/40px system-ui; }
  .stage .f   { float: left; width: 150px; height: 40px; background: #f97316;
                margin: 25px 0 0 10px; font-style: normal; }
  .stage .blk { display: block; width: 150px; height: 40px; background: #16a34a;
                margin: 25px 0 0 60px; }
  .stage .pz  { position: relative; display: block; width: 150px; height: 40px;
                background: #a855f7; margin: -40px 0 0 110px; text-decoration: none; }
</style>
```

> **보이는 것** — 세 막대가 계단처럼 겹쳐 있다. 왼쪽 **주황(float)이 가운데 초록(블록)을 덮고**, 오른쪽 **보라(`position: relative`)가 그 초록을 덮는다.** 아무도 `z-index` 를 안 줬는데 순서가 정해져 있다 — 마크업 순서(주황 → 초록 → 보라)만으로는 주황이 맨 아래여야 하는데 **초록보다 위**에 있다.\
> **바꿔 볼 것** — `.blk` 에 `position: relative` 를 추가 (**초록이 주황 위로 올라온다** — ③층에서 ⑥층으로 승격) · `.pz` 에 `z-index: -1` 추가 (**보라가 초록 밑으로 내려간다**)

### (4) 고치는 법 — 숫자를 키우지 말고 담장을 보라

**언제 쓰나** — 「9999 인데 안 올라온다」를 실제로 고칠 때.

```text
  진단 순서

  ① 겹치는 지점의 픽셀을 읽는다 ──> 정말 밑에 있는 게 맞나
        ↓ 맞다
  ② 그 요소의 조상을 하나씩 올라가며 (2)의 목록에 걸리는 선언을 찾는다
        ↓ 찾았다
  ③ 셋 중 하나를 고른다
       (a) 그 선언을 없앤다            opacity: 0.99 → 1
       (b) 담장 자체의 z-index 를 올린다  부모끼리 겨루게 만든다
       (c) 요소를 담장 밖으로 옮긴다    <body> 바로 밑 (대개 모달·툴팁)
```

- ★ **(c) 가 가장 확실하다.** 오늘날 모달 라이브러리가 전부 `<body>` 에 붙이는 이유다.
- **`isolation: isolate` 는 일부러 담장을 세우는 도구**다 — 위젯 안의 `z-index` 싸움이 밖으로 새지 않게 한다. **투명도를 안 건드리고 담장만 세운다**(실측 확인).
- **`z-index` 를 프로젝트 규칙으로 관리한다** — `--z-modal: 1000` 같은 변수를 두고 **숫자를 직접 쓰지 않는다.**

## 문법 — 형태와 어디서 헷갈리나

### 최소 형태

```css
.overlay { position: fixed; z-index: 10; }   /* position 이 있어야 z-index 가 먹는다 */
.widget  { isolation: isolate; }             /* 일부러 담장을 세운다 */
```

### 헷갈리는 자리 ① — `z-index` 가 먹는 조건

```text
  position: static  + z-index: 5   ──> 무시된다 (에러 없음)
  position: relative + z-index: 5  ──> 먹는다
  flex/grid 항목    + z-index: 5   ──> 먹는다 (position 없이도)   ★
  flex/grid 항목    + z-index: auto ──> 맥락을 안 만든다
```

### 헷갈리는 자리 ② — 세 가지 「구역」

```text
  BFC (17번)          안에서 일어난 일이 밖으로 안 새는 상자 — 마진·float·높이
  쌓임 맥락 (여기)     안의 z-index 가 밖과 안 겨루는 구역 — 페인트 순서
  포함 블록 (21번)     top/left/% 를 재는 기준 사각형 — 위치

  셋은 서로 다른 것이고 만드는 조건도 다르다.
  예: overflow:hidden 은 BFC 를 만들지만 쌓임 맥락은 안 만든다.
      opacity:0.99 는 쌓임 맥락을 만들지만 BFC 도 포함 블록도 안 만든다.
```

### 금지에 가까운 형태

```css
.a { z-index: 9999; }                 /* 담장 안이면 소용없다 */
.b { position: static; z-index: 5; }  /* 통째로 무시 */
.c { opacity: 0.99; }                 /* 「거의 안 보이는」 값인데 담장을 세운다 */
.d { mix-blend-mode: normal; }        /* 이건 담장을 안 세운다 — 목록 암기의 함정 */
```

## 구현 세부사항 대 언어 보장

- **「`z-index` 는 쌓임 맥락 안에서만 비교된다」와 일곱 층의 차례는 명세다.** CSS Positioned Layout Level 3 의 페인트 순서 규정이 근거이고, 실측 여섯 판이 그것과 맞았다.
- ★ **「무엇이 쌓임 맥락을 만드나」의 목록은 계속 늘어 왔다.** `will-change`·`contain`·`backdrop-filter`·`isolation` 은 나중에 들어온 것이라 **오래된 글의 목록과 다르다.** 이 문서의 표는 **이 브라우저에서 실제로 픽셀을 읽어 만든 것**이다.
- ★ **판정을 픽셀로 한 것은 방법이지 보장이 아니다.** 「빨강이 보인다」는 관찰이고, 「그러므로 쌓임 맥락이 없다」는 그 관찰에서의 추론이다. 다만 **다른 방법이 없다** — `getBoundingClientRect()` 는 두 경우에 완전히 같은 값을 준다(실측).
- **색 값은 이 문서가 고른 것**이다. `#ef4444` 를 쓰면 픽셀이 (239,68,68) 로 나오므로, 실험에서는 **순색(`#ff0000`·`#0000ff`)을 써서 판정을 단순하게** 했다.
- ★ **실측 중에 한 번 틀린 판정을 냈다.** 여러 무대를 한 문서에 넣고 잰 첫 판에서 flex 항목 결과가 뒤집혀 나왔는데, 원인은 **같은 문서 안의 다른 무대에 있던 `position: fixed` 요소가 페이지 높이를 바꿔 스크린샷 좌표가 밀린 것**이었다. **무대를 하나씩 떼어 다시 재니** 정상이었다. **픽셀 판정은 좌표가 맞아야 성립한다** — 좌표를 JS 로 뽑아 그대로 쓰는 것까지가 한 실험이다.

## 어디서 틀리나

### 1. `z-index` 숫자를 키운다

**담장 안이면 소용없다**((1) 실측). 9999 든 99999 든 **밖에서는 부모 덩어리 하나**로만 보인다.\
고칠 곳은 **조상**이다.

### 2. `opacity` 를 「보기만 바꾸는 것」으로 안다

**`0.99` 하나로 담장이 선다**((2) 실측 픽셀 (0,0,255)). 화면상 1% 흐려질 뿐이라 **눈으로는 못 잡는다.**\
애니메이션 중간 프레임의 `opacity` 가 이 사고를 일으키기도 한다.

### 3. 목록을 「속성 이름」으로 외운다

**`mix-blend-mode: normal` 은 안 만들고**, **`opacity: 1` 도 안 만든다**((2) 실측).\
외울 것은 속성 이름이 아니라 「**그 선언이 안쪽을 한 장으로 합성해야 하는가**」다.

### 4. BFC·쌓임 맥락·포함 블록을 한 덩어리로 안다

셋은 **다른 구역**이고 조건도 다르다.\
`overflow: hidden` 은 BFC 는 만들되 쌓임 맥락은 안 만들고([17번](../17-block-formatting-context/2-summary.md)), `opacity: 0.99` 는 그 반대다.

### 5. `position: static` 에 `z-index` 를 준다

**통째로 무시된다.** 에러도 경고도 없다.\
단 **flex/grid 항목은 예외**다 — `position` 없이 `z-index` 만으로 먹고 맥락까지 만든다((2) 실측).

### 6. 순서 문제를 좌표로 디버깅한다

★ **`getBoundingClientRect()` 는 두 경우에 완전히 같은 값을 준다.** 좌표로는 절대 안 갈린다.\
**픽셀을 읽거나**, 개발자 도구의 3D 뷰/Layers 패널을 쓴다.

### 7. 「`z-index: -1` 로 뒤로 보냈는데 안 보인다」

**②층은 맥락 배경 위, 블록 배경 아래**다((3)). 부모에 배경이 있으면 **부모 배경에 가린다.**\
부모가 쌓임 맥락이 아니면 더 위 조상의 배경 밑으로까지 내려간다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 고르는 것 | 왜 |
|---|---|---|
| 모달을 무조건 맨 위에 | **`<body>` 바로 밑으로 옮기고** `z-index` | 조상의 담장을 원천 차단 |
| 위젯 안의 순서 싸움을 밖으로 안 새게 | `isolation: isolate` | 투명도를 안 건드리고 담장만 |
| 배경 장식을 내용 뒤로 | `position: absolute; z-index: -1` | 부모가 쌓임 맥락이어야 한다 |
| 겹침 순서를 프로젝트에서 관리 | `--z-*` 변수 | 숫자 인플레이션을 막는다 |
| 드롭다운이 잘리는 것을 막는다 | `overflow` 를 손본다 | 그건 **잘림**이지 순서가 아니다([23번](../23-overflow-and-scroll-containers/2-summary.md)) |
| 성능을 위해 합성 레이어를 띄운다 | `will-change` | **담장이 딸려 온다**는 것을 알고 쓴다 |

판단 규칙 두 줄.

- **「위로 안 온다」를 보면 숫자가 아니라 조상을 본다.** 숫자를 키우는 순간 진단이 멈춘다.
- **담장을 세우는 선언을 쓸 때는 세운다는 것을 알고 쓴다.** `opacity`·`transform`·`will-change` 가 특히 그렇다.

## 핵심 문장

- **`z-index` 는 같은 쌓임 맥락 안에서만 비교된다.** 자식의 9999 는 담장을 못 넘는다 — 밖에서는 **부모 덩어리 하나**다.
- ★★ **`opacity: 0.99` 하나가 자식을 가둔다**(실측 픽셀 (0,0,255)). **`opacity: 1` 은 안 가둔다.**
- ★ **`mix-blend-mode: normal` 은 담장을 안 세운다** — 속성 이름으로 외우면 깨지는 자리다.
- **페인트 순서는 일곱 층**이다 — 배경 → 음수 z → 블록 → float → 인라인 → z:auto/0 → 양수 z. **여섯 판 전부 픽셀로 확인했다.**
- **위치 지정 요소는 `z-index` 없이도 블록·float·글자보다 위**(⑥층)다.
- ★ **이 주제는 `getBoundingClientRect()` 로 아무것도 알 수 없다.** 겹치는 지점의 **픽셀**을 읽는다.
- **쌓임 맥락 · BFC · 포함 블록은 서로 다른 구역**이고 만드는 조건도 다르다.

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 22번)
- [21번 주제](../21-position-and-containing-block/2-summary.md)(`position` 과 포함 블록) — ★ **어디에 놓이나는 거기가 정본**이고 여기는 **누가 위에 그려지나**다. **두 목록의 대조표가 거기 있다**(`opacity` 가 갈리는 자리)
- [17번 주제](../17-block-formatting-context/2-summary.md)(BFC) — **다른 구역이다.** `overflow: hidden` 은 BFC 는 만들되 쌓임 맥락은 안 만든다
- [20번 주제](../20-float-and-clear/2-summary.md)(부동과 해제) — **float 가 블록 배경 위에 그려지는 이유**가 이 문서의 ④층이다
- [19번 주제](../19-inline-formatting-context/2-summary.md)(인라인 서식 문맥) — ⑤층 「인라인 내용」이 무엇인지
- [23번 주제](../23-overflow-and-scroll-containers/2-summary.md)(오버플로) — **「잘린다」는 순서 문제가 아니다.** 드롭다운이 사라지면 거기부터 본다
- [목록의 **47번 주제**](../47-filter-and-backdrop-filter/)(`filter`·`backdrop-filter`) — 필터가 담장을 세우는 부작용의 정본
- [목록의 **48번 주제**](../48-blend-modes-and-isolation/)(혼합 모드와 `isolation`) — **혼합 규칙 자체**는 거기. 여기서는 **담장을 세우느냐**만 봤다
- [목록의 **56번 주제**](../56-rendering-pipeline-and-will-change/)(렌더링 파이프라인·`contain`) — `contain: paint`·`will-change` 의 본래 목적과 비용
- [`reference/render-rules.md`](../../../../../../reference/render-rules.md) — 이 문서의 `demo` 블록 규칙

## 용어 풀이

- **쌓임 맥락(stacking context)** — 그 안의 요소들끼리만 `z-index` 로 겨루는 독립 구역. **구역 전체가 한 덩어리로** 부모 구역에 끼어든다.
- **루트 쌓임 맥락(root stacking context)** — `<html>` 이 만드는 최상위 맥락. 언제나 하나 있다.
- **`z-index`** — 같은 맥락 안의 앞뒤 순서. `position: static` 에서는 무시된다(flex/grid 항목은 예외).
- **페인트 순서(painting order)** — 한 맥락 안에서 무엇을 먼저 그리는지의 차례. 일곱 층((3)).
- **`isolation: isolate`** — **일부러 담장을 세우는** 선언. 투명도·색을 안 건드린다.
- **`mix-blend-mode`** — 아래와 색을 섞는 방식. **`normal` 이 아닌 값**일 때만 담장을 세운다.
- **`will-change`** — 「이 속성이 곧 바뀐다」는 힌트. **담장과 포함 블록이 딸려 온다.**
- **`contain: paint`** — 그리기를 상자 안에 가두는 최적화. 담장도 세운다.
- **합성(compositing)** — 여러 층을 한 장으로 합치는 단계. 담장이 생기는 이유가 여기에 있다.
- **겹침 픽셀 판정** — 두 상자가 겹치는 지점의 RGB 를 읽어 누가 위인지 정하는 방법. **이 주제의 유일한 측정 수단**이다.

---

## 더 들어가면

- **「흐름에서 얼마나 떨어져 나갔나」의 눈금** — [19번](../19-inline-formatting-context/2-summary.md)(줄 안) → [20번](../20-float-and-clear/2-summary.md)(줄은 민다) → [21번](../21-position-and-containing-block/2-summary.md)(줄도 안 민다) → **22번**(그린 순서가 뒤집힌다) → [23번](../23-overflow-and-scroll-containers/2-summary.md)(넘친 것을 어떻게 하나).
- **일곱 층은 재귀한다.** ②·⑥·⑦층에 들어가는 자손이 스스로 쌓임 맥락이면, 그 안에서 같은 일곱 층이 다시 돈다.
- **`z-index` 에는 `auto` 와 `0` 이 다르다.** 둘 다 ⑥층에 놓이지만 **`0` 은 맥락을 만들고 `auto` 는 안 만든다.** 「`z-index: 0` 을 줬을 뿐인데 자식이 갇혔다」가 여기서 나온다.
- **개발자 도구의 Layers 패널**을 쓰면 합성 레이어를 눈으로 볼 수 있다. 이 문서는 **헤드리스에서 픽셀로만** 접지했으므로 그 화면은 **안 돌려 봤다.**

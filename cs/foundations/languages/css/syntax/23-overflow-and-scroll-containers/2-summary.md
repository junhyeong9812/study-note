# css/syntax/23 — 오버플로·스크롤 컨테이너·스크롤바 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [CSS Overflow Module Level 3](https://drafts.csswg.org/css-overflow-3/) (`overflow` 값·스크롤 컨테이너·`overflow-clip-margin` 의 정본) · [CSS Overflow Module Level 4](https://drafts.csswg.org/css-overflow-4/) (`scrollbar-gutter`). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 `demo` 블록 **4개 전부**와 **`overflow` 값 조합 14가지**를 **Google Chrome 151.0.7922.173** headless 에 실제로 띄워 `getComputedStyle`·`clientWidth`/`offsetWidth`·`scrollTop` 대입으로 쟀고, 잘림 여부는 **스크린샷 픽셀**로 판정했다.\
> ★ **이 주제의 핵심 측정은 「`scrollTop` 에 값을 넣어 보는 것」이다.** 값이 남아 있으면 스크롤 컨테이너, 0 으로 되돌아가면 아니다. **화면만 봐서는 `hidden` 과 `clip` 이 완전히 똑같다.**\
> **WebKit(Safari)은 이 머신에 없고 Firefox 는 이 환경에서 headless 스크린샷이 산출되지 않는다** — 크로스 브라우저 주장은 하지 않았다.
> **버전** — `overflow: clip` 은 Baseline **widely**, `scrollbar-gutter` 도 Baseline 에 들어 있다(목록 README 의 지원 표). 실행으로 확인한 것은 **이 Chrome 에서의 동작**이다.
> **여기서 다루지 않는 것** — ★ **`overflow` 가 BFC 를 만드는지와 그 부작용 대조는 [17번](../17-block-formatting-context/2-summary.md)이 정본**이고(거기서 **`clip` 만 BFC 가 아님**을 실측했다), 여기는 **스크롤 컨테이너 쪽**이다. `position: sticky` 의 규칙 자체는 [21번](../21-position-and-containing-block/2-summary.md), 누가 위에 그려지나는 [22번](../22-stacking-context-and-z-index/2-summary.md), 상자의 네 겹 치수는 [15번](../15-box-model-and-box-sizing/2-summary.md)이다. **스크롤 스냅**(`scroll-snap-type`·`scroll-snap-align`)과 `overscroll-behavior` 는 이 편에서 **다루지 않는다** — 이름만 적고 넘긴다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 동작은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**`overflow` 는 「상자보다 큰 내용을 어떻게 할까」에 대한 다섯 가지 대답이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 상자보다 큰 짐 | 넘치는 내용 |
| **짐이 삐져나온 채로 둔다** | `visible`(기본) |
| **삐져나온 부분을 잘라 버리되 상자는 굴릴 수 있다** | `hidden` — **스크롤 컨테이너다** |
| **잘라 버리고 상자를 못 굴리게 아예 고정한다** | `clip` — 스크롤 컨테이너가 **아니다** |
| 손잡이를 달아 굴려 볼 수 있게 한다 | `auto`(필요할 때만 손잡이) · `scroll`(늘 손잡이) |
| 손잡이가 붙을 자리를 미리 비워 두는 것 | `scrollbar-gutter: stable` |

```text
   같은 상자, 같은 내용 — 화면은 hidden 과 clip 이 똑같다

   visible          hidden           clip            auto
  +------+         +------+         +------+       +------+-+
  |[내용 |-->      |[내용 |         |[내용 |       |[내용 |▓|
  |      |         |      |         |      |       |      |▓|
  +------+         +------+         +------+       +------+-+
   삐져나옴          잘림             잘림           잘림 + 스크롤바

   scrollTop = 200 을 넣어 보면
       0               200              0             200
                        ↑ 굴러간다!      ↑ 꿈쩍도 안 한다
```

*(Chrome 151 headless 실측 — `scrollTop = 200` 대입 후 실제 값. **`hidden` 은 200, `clip` 은 0.**)*

실무에서 이게 터지는 자리는 **"`overflow: hidden` 을 줬더니 포커스가 갈 때 내용이 혼자 움직인다"** 는 증상이다.\
`hidden` 은 **스크롤 컨테이너**라 브라우저가 필요하면 굴려 버린다((4)에서 실측한다).

> **스크롤 컨테이너(scroll container)** — 안쪽을 스크롤할 수 있는 상자. 스크롤바가 보이느냐와는 **별개**다.\
> 예: `overflow: hidden` 은 스크롤바가 없지만 스크롤 컨테이너다 — 스크립트로도 브라우저도 굴릴 수 있다.

> **스크롤포트(scrollport)** — 스크롤 컨테이너에서 실제로 내용이 보이는 칸. 패딩 상자에서 스크롤바를 뺀 칸이다.\
> 예: `clientWidth`·`clientHeight` 가 재는 칸. [`sticky`](../21-position-and-containing-block/2-summary.md)가 걸리는 기준이기도 하다.

> **잘림(clipping)** — 넘친 부분이 그려지지 않는 것. **레이아웃이 아니라 페인트**다.\
> 예: 잘린 요소의 `getBoundingClientRect()` 는 잘리기 전과 **똑같다**([17번](../17-block-formatting-context/2-summary.md)).

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `hidden` 과 `clip` 은 **화면이 같은데 무엇이 다른가.**
2. 한 축만 `hidden` 으로 주면 **다른 축에 무슨 일이 일어나는가.**
3. 스크롤바가 **레이아웃을 몇 px 먹는가** — 그리고 그것을 어떻게 안 흔들리게 하나.

## 동작 방식

### (1) 다섯 값 — 스크롤 컨테이너를 만드나

**언제 쓰나** — 값을 고를 때. **이 표가 이 주제의 좌표계다.**

판정 방법 — **`scrollTop = 200` 을 대입하고 되읽는다.** 값이 남으면 스크롤 컨테이너다.

*(Chrome 151 headless 실측 — 200×80 상자(테두리 2), 내용 320×200.)*

| `overflow` | 잘리나 | `scrollTop` 대입 200 → | 스크롤 컨테이너 | `clientWidth` × `clientHeight` | BFC([17번](../17-block-formatting-context/2-summary.md)) |
|---|---|---|---|---|---|
| `visible`(기본) | ✗ | **0** | ✗ | 200 × 80 | ✗ |
| `hidden` | **✓** | **200** | **✓** | 200 × 80 | ✓ |
| `clip` | **✓** | **0** | **✗** | 200 × 80 | **✗** |
| `auto` | ✓ | 200 | ✓ | **185 × 65** | ✓ |
| `scroll` | ✓ | 200 | ✓ | **185 × 65** | ✓ |

```text
   「잘린다」와 「스크롤 컨테이너다」는 다른 축이다

                  스크롤 컨테이너 ✗        스크롤 컨테이너 ✓
                +----------------------+----------------------+
   안 잘린다    |      visible         |        (없음)        |
                +----------------------+----------------------+
   잘린다       |        clip          |  hidden · auto · scroll |
                +----------------------+----------------------+
```

- ★ **`hidden` 과 `clip` 은 화면이 완전히 같다.** 갈리는 것은 **굴릴 수 있느냐**뿐이다.
- **`auto`·`scroll` 만 `clientWidth` 가 줄었다** — 스크롤바가 **레이아웃 공간을 먹었기** 때문이다(실측 200 → **185**, 15px).
- **`hidden` 은 스크롤 컨테이너인데 스크롤바가 없다** — `clientWidth` 가 200 그대로였다.
- **BFC 열은 [17번](../17-block-formatting-context/2-summary.md)의 결론**이다. **`clip` 만 BFC 가 아니고**, 그 이유가 바로 이 표의 「스크롤 컨테이너 ✗」다.

비용 — 스크롤 컨테이너를 만들면 **스크롤 앵커링·`sticky` 가로채기·포커스 스크롤**이 전부 딸려 온다((4)).

### (2) `hidden` 대 `clip` — 화면으로는 못 가린다

**언제 쓰나** — 「잘리기만 하면 되는데」 하고 `hidden` 을 쓸 때. ★ **이 주제의 결론 자리다.**

```html demo
<div class="b" id="h"><div class="big">overflow: hidden</div></div>
<div class="b" id="c" style="overflow: clip"><div class="big">overflow: clip</div></div>
<style>
  .b { overflow: hidden; width: 170px; height: 54px; border: 2px solid #333;
       margin-bottom: 10px; font: 13px/18px system-ui; }
  .big { width: 300px; height: 150px; background: linear-gradient(135deg,#fca5a5,#93c5fd); }
</style>
```

> **보이는 것** — 두 상자가 **완전히 똑같이** 보인다. 둘 다 그라디언트가 상자 테두리에서 딱 잘려 있고, 오른쪽·아래로 넘친 부분은 안 보인다. **화면에서는 아무 차이도 없다.**\
> **바꿔 볼 것** — 두 상자를 마우스 휠로 굴려 보라 — **둘 다 안 굴러간다**(휠은 스크롤바 없는 컨테이너에서 페이지로 넘어간다). 차이는 **스크립트로만** 드러난다: `document.getElementById('h').scrollTop = 200` 은 **200 이 되고**, `'c'` 는 **0 그대로**다.

*(Chrome 151 headless 실측 — 두 상자의 `clientWidth`·`offsetWidth`·`scrollWidth`·`scrollHeight` 가 **전부 동일**(200×80 · 204×84 · 320 · 200)했다. 갈린 것은 **`scrollTop` 대입 결과뿐**이다(200 대 0).)*

```text
   두 값을 가르는 유일한 축

                      hidden                      clip
   화면               잘린다                      잘린다        ← 같다
   clientWidth        200                         200          ← 같다
   scrollWidth        320                         320          ← 같다
   scrollTop = 200    200  ✓                      0   ✗        ← 여기서만 갈린다
   BFC (17번)         연다                        안 연다
   자손 sticky        죽인다                      안 죽인다
   포커스 스크롤      일어난다                    안 일어난다
```

- ★ **`clip` 은 「자르기만 한다」는 뜻의 값**이다. 스크롤 능력이 아예 없다.
- 그래서 **자르는 것만 원하면 `clip` 이 정답**이고, `hidden` 은 **원치 않는 부작용 셋**을 덤으로 준다.
- `clip` 은 **`overflow-clip-margin` 으로 여유를 줄 수 있다**(「살짝만 넘치게」). `hidden` 에는 없다.

```html demo
<div class="b" style="overflow: hidden"><div class="big"></div></div>
<div class="b" style="overflow: clip; overflow-clip-margin: 20px"><div class="big"></div></div>
<style>
  .b { width: 150px; height: 50px; border: 2px solid #333; margin: 20px; }
  .big { width: 300px; height: 150px; background: #7c3aed; }
</style>
```

> **보이는 것** — 위 상자에서는 보라가 **검은 테두리에서 정확히 끊긴다.** 아래 상자에서는 보라가 **테두리 밖으로 20px 더 나온 뒤** 끊긴다 — 테두리 오른쪽·아래로 보라 띠가 한 겹 더 보이고, 그 바깥은 흰색이다. **`hidden` 으로는 이 여유를 만들 수 없다.**\
> **바꿔 볼 것** — 아래의 `overflow-clip-margin: 20px` → `0px` (**위 상자와 똑같아진다**) · `overflow: clip` → `hidden` (`overflow-clip-margin` 이 **통째로 무시돼** 역시 위 상자처럼 된다)

*(Chrome 151 headless 실측 — 스크린샷 픽셀. `hidden` 상자는 테두리 바깥 10px 지점이 **(255,255,255) 흰색**, `clip` + 여유 20px 상자는 같은 지점이 **(124,58,237) 보라**이고 25px 지점부터 흰색이었다.)*

### (3) 한 축만 주면 다른 축이 `auto` 가 된다

**언제 쓰나** — 「가로만 숨기고 세로는 그냥 두자」 할 때. ★ **명세가 그렇게 정한 자리다.**

*(Chrome 151 headless 실측 — 선언한 값과 `getComputedStyle` 이 돌려준 값.)*

| 선언 | 계산값 `overflow-x` | 계산값 `overflow-y` | 스크롤 컨테이너 | `clientWidth` × `clientHeight` |
|---|---|---|---|---|
| `x: hidden` · `y: visible` | `hidden` | **`auto`** | ✓ | **185** × 80 |
| `x: visible` · `y: hidden` | **`auto`** | `hidden` | ✓ | 200 × **65** |
| `x: scroll` · `y: visible` | `scroll` | **`auto`** | ✓ | **185 × 65** |
| `x: clip` · `y: visible` | `clip` | `visible` | **✗** | 200 × 80 |
| `x: visible` · `y: clip` | `visible` | `clip` | **✗** | 200 × 80 |
| `x: hidden` · `y: clip` | `hidden` | **`hidden`** | ✓ | 200 × 80 |

```text
   "한 축을 잘랐으면 다른 축도 잘라야 한다"는 규칙

   overflow-x: hidden 인데 overflow-y: visible 이면?
        세로로 삐져나온 내용이 가로로 잘린 자리를 넘나든다 → 그릴 수가 없다
                          ↓
   그래서 엔진이 visible 쪽을 auto 로 바꿔 버린다 (계산값이 바뀐다!)

   단 clip 과 visible 은 짝이 맞는다 — 둘 다 스크롤 컨테이너가 아니므로
   x: clip  · y: visible  →  그대로   ✓
   x: hidden · y: clip    →  clip 이 hidden 으로 바뀐다   ★
```

- ★ **선언하지 않은 축의 계산값이 바뀐다.** `visible` 이라고 썼는데 `getComputedStyle` 이 **`auto`** 를 돌려준다 — 진단 3창의 셋째 창이 **선언과 다른 값**을 말하는 드문 자리다.
- **그 결과 스크롤바가 생긴다** — `x: hidden; y: visible` 만 줬는데 `clientWidth` 가 **185** 로 15px 줄었다.
- ★ **`clip` 과 `visible` 은 예외로 짝이 맞는다**(둘 다 스크롤 컨테이너가 아니므로 섞여도 그릴 수 있다). **`clip` 을 `hidden` 과 섞으면 `clip` 쪽이 `hidden` 으로 바뀐다.**

```html demo
<div class="b" id="a"><div class="big"></div></div>
<div class="b" id="b" style="overflow-x: clip; overflow-y: visible"><div class="big"></div></div>
<style>
  .b { overflow-x: hidden; overflow-y: visible; width: 170px; height: 50px;
       border: 2px solid #333; margin-bottom: 30px; }
  .big { width: 300px; height: 120px;
         background: linear-gradient(135deg,#fca5a5,#93c5fd); }
</style>
```

> **보이는 것** — 위 상자는 내용이 **상자 안에서 잘려** 있고 **오른쪽에 세로 스크롤바가 생겨** 있다(`overflow-y` 를 `visible` 이라고 썼는데도). 아래 상자는 **스크롤바가 없고**, 잘린 것은 가로뿐이라 **내용이 상자 아래로 길게 삐져나와** 그 아래 여백을 덮는다.\
> **바꿔 볼 것** — 위 상자의 `overflow-x: hidden` → `clip` (**아래 상자와 똑같아진다**) · 아래 상자의 `overflow-y: visible` → `hidden` (**`clip` 이 `hidden` 으로 바뀌어 위 상자처럼 된다**)

### (4) 스크롤 컨테이너가 되면 딸려 오는 것 셋

**언제 쓰나** — `hidden` 을 쓴 뒤 이상한 일이 일어날 때.

```text
   overflow: hidden 을 준 순간 딸려 오는 것

   ① 브라우저가 마음대로 굴린다        깊숙한 자식이 포커스를 받으면 스크롤된다
   ② 자손의 sticky 를 가로챈다         바깥 스크롤러 대신 이 상자에 걸리려 한다
   ③ BFC 가 열린다                     마진이 안 새고 float 를 감싼다 (17번)

   clip 은 셋 다 안 일어난다
```

*(Chrome 151 headless 실측 ① — 200 높이 패딩 뒤에 버튼을 두고 `button.focus()` 를 불렀다.)*

| 상자의 `overflow` | `focus()` 후 `scrollTop` |
|---|---|
| `hidden` | **145** — 내용이 혼자 움직였다 |
| `clip` | **0** — 그대로다 |

*(Chrome 151 headless 실측 ② — 바깥 `overflow: auto` 스크롤러와 `sticky` 헤더 사이에 래퍼를 끼우고 `scrollTop = 200`.)*

| 중간 래퍼의 `overflow` | 헤더 top(스크롤러 기준) | `sticky` |
|---|---|---|
| `visible` | 2.0 | 붙는다 |
| **`clip`** | **2.0** | **붙는다** |
| **`hidden`** | **−198.0** | **죽는다** |
| `auto` | −198.0 | 죽는다 |

- ★★ **①이 실무에서 가장 고약하다.** 화면이 혼자 스크롤되어 레이아웃이 어긋나는데, **CSS 어디를 봐도 원인이 안 보인다.** 원인은 조상의 `overflow: hidden` 이다.
- ★ **②는 [21번](../21-position-and-containing-block/2-summary.md)의 `sticky` 와 같은 사실**이다. 거기는 `sticky` 쪽에서, 여기는 `overflow` 쪽에서 본 것이다.
- **셋 다 `clip` 으로 바꾸면 사라진다.** 「잘리기만 하면 되는데 왜 이런 일이」의 답이 **값을 잘못 골랐다**는 것이다.
- ③ 의 정본은 [17번](../17-block-formatting-context/2-summary.md)이다. 거기서 **`clip` 이 BFC 를 안 여는 것**을 실측했고, 그 이유가 **스크롤 컨테이너가 아니기 때문**이라는 것이 이 절의 표로 확인된다.

### (5) 스크롤바가 먹는 폭과 `scrollbar-gutter`

**언제 쓰나** — 내용이 늘어날 때 레이아웃이 15px 씩 튀는 것을 막을 때.

```text
   clientWidth 와 offsetWidth 가 재는 칸이 다르다

   +---------------------------------------+  offsetWidth  204  (테두리 포함)
   | +-----------------------------------+ |
   | |                             |▓▓▓| | |  clientWidth  185  (스크롤바 제외)
   | |          스크롤포트          |스 | | |
   | |                             |크 | | |
   | +-----------------------------------+ |
   +---------------------------------------+
     ↑ 테두리 2                    ↑ 15px
```

*(Chrome 151 headless 실측 — 200×80 상자(테두리 2). `offsetWidth` 는 네 경우 모두 **204** 로 같았다.)*

| `overflow` | `clientWidth` | 스크롤바가 먹은 폭 |
|---|---|---|
| `visible` · `hidden` · `clip` | **200** | 0 |
| `auto`(내용이 넘칠 때) · `scroll` | **185** | **15** |

★ **기본값 `auto` 의 문제는 「내용에 따라 폭이 바뀐다」는 것이다.**

*(Chrome 151 headless 실측 — 같은 `overflow: auto` 상자에 짧은 내용과 긴 내용을 각각 넣었다.)*

| `scrollbar-gutter` | 내용이 짧을 때 자식 폭 | 내용이 길 때 자식 폭 | 흔들림 |
|---|---|---|---|
| `auto`(기본) | **200** | **185** | **15px 튄다** |
| `stable` | **185** | **185** | **없다** |
| `stable both-edges` | 170 | 170 | 없다(양쪽에 15씩) |

```html demo
<div class="b"><div class="s">짧다 — 스크롤바 없음</div></div>
<div class="b"><div class="l">길다 — 스크롤바 생김</div></div>
<div class="b g"><div class="s">짧다 + gutter</div></div>
<style>
  .b { overflow: auto; width: 200px; height: 60px; border: 2px solid #333;
       margin-bottom: 8px; font: 13px/20px system-ui; }
  .b > div { background: #a7f3d0; }
  .s { height: 30px; }
  .b > .l { height: 200px; background: #fca5a5; }
  .g { scrollbar-gutter: stable; }
</style>
```

> **보이는 것** — 첫 상자의 연두 띠는 **상자 안쪽 끝까지** 꽉 차고 스크롤바가 없다. 둘째 상자는 **오른쪽에 스크롤바가 생겨** 분홍 내용이 그만큼 좁아진다. 셋째 상자는 내용이 짧아 스크롤바가 없는데도 **연두 띠가 둘째 상자와 똑같이 좁다** — 오른쪽에 **빈 자리가 미리 비워져** 있다.\
> **바꿔 볼 것** — `.g` 의 `stable` → `stable both-edges` (**양쪽이 다 좁아진다**) · `.s` 의 `height` 를 `200px` 로 키우면 첫 상자에서 **연두 띠가 갑자기 좁아진다**(레이아웃이 튄다)

- ★ **`offsetWidth` 는 안 바뀐다**(네 경우 모두 204). 바뀌는 것은 **`clientWidth`** 다 — 이 둘의 차이를 [15번](../15-box-model-and-box-sizing/2-summary.md)이 정의했고 여기서 **스크롤바가 그 차이에 끼어든다.**
- **15px 은 이 플랫폼의 값**이다. 다른 OS·설정에서는 0 일 수도 있다(겹침 스크롤바).
- **`stable` 은 스크롤바가 없어도 자리를 비운다** — 대신 **늘 15px 을 잃는다.** 공짜는 아니다.

## 문법 — 형태와 어디서 헷갈리나

### 최소 형태

```css
.crop  { overflow: clip; }                 /* 자르기만 한다 — 부작용 없음 */
.panel { overflow: auto; scrollbar-gutter: stable; }  /* 스크롤 + 레이아웃 안 튐 */
.row   { overflow-x: auto; overflow-y: clip; }        /* 가로만 스크롤 */
```

단축 `overflow: <x> <y>` 도 쓸 수 있다(`overflow: hidden auto`).

### 헷갈리는 자리 ① — 「잘린다」와 「스크롤된다」는 다른 축

```text
   잘리나?          visible 만 ✗, 나머지 넷 전부 ✓
   스크롤 컨테이너?  clip · visible 만 ✗, hidden · auto · scroll 이 ✓
   스크롤바가 보이나? auto(넘칠 때) · scroll 만 ✓

   세 질문의 답이 서로 다르다. hidden 은 「잘리고 · 스크롤 컨테이너이고 · 스크롤바는 없다」.
```

### 헷갈리는 자리 ② — 계산값이 선언과 다르다

```text
   overflow-x: hidden; overflow-y: visible
        ↓ getComputedStyle 로 읽으면
   overflow-x: hidden; overflow-y: auto      ← 내가 안 쓴 값이 나온다
```

**진단 3창의 셋째 창이 선언과 다른 값을 말하는 자리**다. 「내가 `visible` 이라고 썼는데」가 안 통한다.

### 헷갈리는 자리 ③ — `hidden` 이 가로채는 것

```text
   <div style="overflow:auto">          ← 여기에 걸려야 하는데
     <div style="overflow:hidden">      ← 여기가 가로챈다
       <div style="position:sticky">    ← 그래서 안 붙는다
```

### 금지에 가까운 형태

```css
.a { overflow: hidden; }            /* 자르기만 원했다면 clip 이 맞다 */
.b { overflow-y: visible; overflow-x: hidden; }  /* y 가 조용히 auto 가 된다 */
.c { overflow: auto; }              /* 내용에 따라 폭이 15px 튄다 — gutter 를 보라 */
.d { overflow: hidden; }            /* 자손 sticky 가 죽는다 */
```

## 구현 세부사항 대 언어 보장

- **다섯 값의 의미와 「한 축이 `visible` 이 아니면 다른 축의 `visible` 이 `auto` 가 된다」는 명세다.** CSS Overflow Level 3 가 근거이고, 실측 계산값이 그것과 맞았다.
- **`clip` 이 스크롤 컨테이너를 안 만든다는 것도 명세**이고, [17번](../17-block-formatting-context/2-summary.md)의 「그래서 BFC 도 아니다」와 한 사실이다.
- ★ **스크롤바 폭 15px 은 이 플랫폼의 값**이다. CSS 의 보장이 아니다 — macOS 의 겹침 스크롤바에서는 **0** 이 되고, 그러면 `scrollbar-gutter` 도 아무 자리를 안 비운다.
- ★ **`focus()` 가 스크롤을 일으키는 것은 브라우저 동작**이지 CSS 규정이 아니다. 실측값 **145** 는 이 실험의 배치에서 나온 수이고, 스크롤 양을 정하는 규칙은 브라우저가 정한다.
- ★ **「화면이 같다」는 주장의 근거는 스크린샷이 아니라 치수 전수 비교**다. `clientWidth`·`offsetWidth`·`scrollWidth`·`scrollHeight` 가 전부 같았다. **「안 보인다」는 「없다」가 아니므로**, 화면만 보고 「같다」고 적지 않았다.

## 어디서 틀리나

### 1. 자르려고 `hidden` 을 쓴다

**부작용 셋이 딸려 온다**((4)) — 포커스 스크롤·`sticky` 가로채기·BFC.\
**자르는 것만 원하면 `clip`** 이다.

### 2. `hidden` 을 「스크롤 못 하는 값」으로 안다

★ **스크롤 컨테이너다.** `scrollTop = 200` 이 **그대로 먹는다**((1) 실측).\
스크롤바가 없을 뿐이다 — **「스크롤바가 없다」와 「스크롤이 안 된다」는 다른 말**이다.

### 3. 한 축만 `hidden` 으로 주고 다른 축은 그대로일 거라 생각한다

**다른 축이 `auto` 가 된다**((3) 실측 계산값). **스크롤바까지 생긴다**(`clientWidth` 200 → 185).\
가로만 자르고 싶으면 **`overflow-x: clip`** 을 쓴다 — 그때는 세로가 `visible` 로 남는다.

### 4. `sticky` 가 안 붙는 원인을 `sticky` 쪽에서 찾는다

**조상의 `overflow: hidden`** 이다((4) 실측 −198). `clip` 으로 바꾸면 살아난다.

### 5. 스크롤바 때문에 레이아웃이 튀는 것을 반응형 문제로 본다

`overflow: auto` 는 **내용 길이에 따라 `clientWidth` 가 15px 바뀐다**((5) 실측 200 ↔ 185).\
`scrollbar-gutter: stable` 로 고정한다.

### 6. 「잘렸나」를 `getBoundingClientRect()` 로 확인한다

★ **잘림은 레이아웃이 아니라 페인트**다. [17번](../17-block-formatting-context/2-summary.md)에서 잘린 상자와 안 잘린 상자의 `rect` 가 **완전히 같았다.**\
**스크린샷 픽셀**로 봐야 한다.

### 7. 드롭다운이 사라지는 것을 `z-index` 문제로 본다

**`overflow` 문제일 가능성이 높다.** 갈라 보는 법 — **일부만 잘려 있으면 `overflow`**, **통째로 다른 것 밑에 깔려 있으면 [`z-index`](../22-stacking-context-and-z-index/2-summary.md)** 다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 고르는 것 | 왜 |
|---|---|---|
| **자르기만 한다** | `overflow: clip` | 부작용 셋이 없다 |
| 살짝 넘치는 것은 허용하고 자른다 | `clip` + `overflow-clip-margin` | `hidden` 에는 없는 기능 |
| 안을 스크롤한다 | `auto` | 필요할 때만 스크롤바 |
| 스크롤바 자리를 늘 확보한다 | `auto` + `scrollbar-gutter: stable` | 레이아웃이 안 튄다 |
| 스크롤바를 늘 보여 준다 | `scroll` | 스크롤 가능함을 알린다 |
| BFC 만 원한다 | `display: flow-root` | `overflow` 를 쓰지 않는다([17번](../17-block-formatting-context/2-summary.md)) |
| 자손 `sticky` 를 살린다 | `hidden` 대신 `clip` | `clip` 은 스크롤 컨테이너가 아니다 |
| 가로만 자른다 | `overflow-x: clip` | `hidden` 이면 세로가 `auto` 가 된다 |

판단 규칙 두 줄.

- **「굴릴 일이 있나?」를 먼저 묻는다.** 없으면 `clip`, 있으면 `auto`. **`hidden` 은 둘 다 아닌 어중간한 값**이다.
- **`overflow` 를 다른 목적(BFC·잘림)으로 쓰지 않는다.** 그 목적에는 전용 값이 따로 있다.

## 핵심 문장

- `overflow` 는 **「잘리나」·「스크롤 컨테이너인가」·「스크롤바가 보이나」 세 질문에 각각 다르게 답한다.**
- ★★ **`hidden` 과 `clip` 은 화면·치수가 전부 같고 `scrollTop` 대입에서만 갈린다**(200 대 0). **`hidden` 은 스크롤 컨테이너다.**
- `hidden` 에는 부작용 셋이 딸려 온다 — **포커스 스크롤**(실측 `scrollTop` 145) · **자손 `sticky` 가로채기**(실측 −198) · **BFC**([17번](../17-block-formatting-context/2-summary.md)).
- ★ **한 축만 `hidden`/`scroll` 을 주면 다른 축의 계산값이 `auto` 로 바뀐다** — 안 쓴 값이 `getComputedStyle` 에 나온다. **`clip` 과 `visible` 만 짝이 맞는다.**
- **스크롤바는 `clientWidth` 를 먹고 `offsetWidth` 는 안 먹는다**(실측 185 대 204). **15px 은 플랫폼의 값**이다.
- **`overflow: auto` 는 내용 길이에 따라 15px 튄다.** `scrollbar-gutter: stable` 로 고정한다.
- ★ **「잘렸나」는 `getBoundingClientRect()` 로 잴 수 없다** — 픽셀로 본다.

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 23번)
- [17번 주제](../17-block-formatting-context/2-summary.md)(BFC) — ★ **`overflow` 가 BFC 를 만드는지와 수단별 부작용 대조가 정본.** 거기서 **`clip` 만 BFC 가 아님**을 실측했고, 여기는 **그 이유(스크롤 컨테이너가 아님)** 쪽이다
- [21번 주제](../21-position-and-containing-block/2-summary.md)(`position` 과 포함 블록) — **`sticky` 의 규칙 자체는 거기.** 여기는 **`overflow` 가 그것을 가로채는 쪽**이다
- [22번 주제](../22-stacking-context-and-z-index/2-summary.md)(쌓임 맥락) — **「사라졌다」가 잘림인지 가림인지** 가르는 짝. `overflow` 는 **쌓임 맥락을 안 만든다**(실측)
- [15번 주제](../15-box-model-and-box-sizing/2-summary.md)(박스 모델) — **`clientWidth` 와 `offsetWidth` 가 재는 칸**의 정본. 여기는 **스크롤바가 그 차이에 끼어드는 자리**다
- [목록의 **26번 주제**](../26-flex-wrap-gap-order/)(flex 줄바꿈·`gap`) — `min-width: auto` 때문에 안 줄어드는 항목이 `overflow` 를 유발하는 자리
- [목록의 **59번 주제**](../59-view-transitions/)(스크롤 연동 애니메이션) — **스크롤 스냅·`overscroll-behavior`·스크롤 타임라인**은 이 편에서 다루지 않는다
- [`reference/render-rules.md`](../../../../../../reference/render-rules.md) — 이 문서의 `demo` 블록 규칙

## 용어 풀이

- **스크롤 컨테이너(scroll container)** — 안쪽을 스크롤할 수 있는 상자. **스크롤바가 보이느냐와는 별개**다.
- **스크롤포트(scrollport)** — 스크롤 컨테이너에서 내용이 보이는 칸. `clientWidth`/`clientHeight` 가 재는 칸.
- **잘림(clipping)** — 넘친 부분이 그려지지 않는 것. **레이아웃이 아니라 페인트**라 `rect` 로는 안 보인다.
- **`visible`** — 기본값. 안 자르고 안 스크롤한다. 넘친 것이 그대로 보인다.
- **`hidden`** — 자르고 **스크롤 컨테이너를 만든다.** 스크롤바는 없다.
- **`clip`** — 자르기만 한다. **스크롤 컨테이너가 아니다.** BFC 도 안 만든다.
- **`auto`** — 넘칠 때만 스크롤바가 생긴다. 그때 `clientWidth` 가 줄어든다.
- **`scroll`** — 넘치든 말든 스크롤바 자리를 늘 먹는다.
- **`overflow-clip-margin`** — `clip` 에서 「이만큼은 넘쳐도 된다」는 여유. `hidden` 에는 없다.
- **`scrollbar-gutter`** — 스크롤바 자리를 미리 비워 두는 속성. `stable` 은 한쪽, `stable both-edges` 는 양쪽.
- **포커스 스크롤(focus scrolling)** — 포커스 받은 요소를 보이게 하려고 브라우저가 스크롤 컨테이너를 굴리는 것. **`hidden` 에서도 일어난다.**

---

## 더 들어가면

- **「흐름에서 얼마나 떨어져 나갔나」의 눈금** — [19번](../19-inline-formatting-context/2-summary.md)(줄 안) → [20번](../20-float-and-clear/2-summary.md)(줄은 민다) → [21번](../21-position-and-containing-block/2-summary.md)(줄도 안 민다) → [22번](../22-stacking-context-and-z-index/2-summary.md)(그린 순서가 뒤집힌다) → **23번**(넘친 것을 어떻게 하나). 이 다섯이 한 사슬이다.
- **루트 요소의 `overflow` 는 뷰포트로 전파된다.** `<html>`(또는 `<body>`)에 준 값이 **문서 전체의 스크롤**을 정한다 — 그래서 모달을 열 때 `body { overflow: hidden }` 을 쓴다. 이 문서는 **상자 단위만 실측**했고 전파 규칙은 **안 돌려 봤다.**
- **스크롤 앵커링(scroll anchoring)** — 위쪽에 내용이 추가돼도 보고 있던 자리가 안 튀게 브라우저가 스크롤 위치를 보정하는 기능. **스크롤 컨테이너마다 따로 동작**하므로 `hidden` 상자에도 걸린다. `overflow-anchor: none` 으로 끈다(**안 돌려 봄**).
- **`scrollbar-width: thin`/`none`** 으로 스크롤바 자체를 가늘게·없앨 수 있다. `none` 은 **스크롤 능력은 남기고 손잡이만 지운다** — `hidden` 과는 또 다른 조합이다(**안 돌려 봄**).
- **스크롤 스냅**(`scroll-snap-type`·`scroll-snap-align`)과 **`overscroll-behavior`** 는 스크롤 컨테이너 위에 얹히는 층이다. [목록의 **59번 주제**](../59-view-transitions/) 쪽으로 넘긴다.

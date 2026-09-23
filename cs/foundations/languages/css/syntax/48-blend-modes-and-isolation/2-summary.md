# css/syntax/48 — 혼합 모드와 `isolation` — `mix-blend-mode`·`background-blend-mode` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Compositing and Blending Level 1](https://drafts.fxtf.org/compositing-1/) (`mix-blend-mode`·`background-blend-mode`·`isolation` 과 **혼합 공식**의 정본). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 `demo` 블록 **3개 전부**와 본문의 모든 수치를 **Google Chrome 151.0.7922.173** headless 에서 실제로 렌더해 확인했다.\
> ★ **이 주제는 `getComputedStyle` 로 아무것도 증명하지 못한다.** `mix-blend-mode: multiply` 가 계산값으로 돌아와도 **실제로 섞였는지**는 다른 이야기다(격리되면 안 섞인다).\
> 그래서 **스크린샷 PNG 를 파이썬 표준 라이브러리(`zlib`)로 디코드해 좌표별 `(r,g,b)` 를 읽고, 그 값을 명세의 공식과 대조하는 것**이 주 근거다.
> **버전** — CSS 에 언어 버전이 없으므로 Baseline 으로 읽는다. webstatus.dev 조회(2026-09-23): `mix-blend-mode`·`background-blend-mode`·`isolation` 셋 다 **widely**(2020-01-15 → 2022-07-15).
> **여기서 다루지 않는 것** — **쌓임 맥락 자체**는 [목록의 **22번 주제**](../22-stacking-context-and-z-index/)가 정본이다. 여기는 「쌓임 맥락을 만드는 것이 곧 격리다」까지만 쓴다.\
> `filter` 가 쌓임 맥락과 backdrop root 를 만드는 것은 [47번](../47-filter-and-backdrop-filter/2-summary.md), 배경 레이어가 쌓이는 규칙은 [목록의 **44번 주제**](../44-backgrounds-and-object-fit/), 색 표기는 **42번 주제**, 그라디언트는 **45번 주제**, `transform` 은 **54번 주제**다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 수치는 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**투명 필름 두 장을 겹쳐 빛에 비춰 보는 것이다. 「어떻게 겹칠지」를 고르는 손잡이가 혼합 모드다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 아래에 깔린 필름 | **backdrop** — 이미 그려져 있는 뒤쪽 전부 |
| 위에 얹는 필름 | **source** — 지금 그리는 요소(또는 배경 레이어) |
| 겹치는 방식을 고르는 손잡이 | **`mix-blend-mode`·`background-blend-mode`** |
| 필름 여러 장을 먼저 한 장으로 붙여 버리는 것 | **격리** — 그 묶음 바깥과는 더 이상 안 섞인다 |

- 손잡이가 두 개인 이유는 **섞을 대상이 두 종류**이기 때문이다.
  - `mix-blend-mode` — **요소**와 **그 뒤에 깔린 것**
  - `background-blend-mode` — **한 요소 안의 배경 레이어들끼리**
- 「먼저 한 장으로 붙여 버리는 것」이 `isolation: isolate` 다. 붙인 다음에는 **그 안에서만** 섞인다.

```text
  같은 색, 같은 모드, 다른 손잡이 — 결과가 통째로 다르다

  요소의 배경 레이어: 위 #cc6633 / 아래 #3399cc     페이지 배경: #ffcc00

  background-blend-mode: multiply        mix-blend-mode: multiply
   위·아래 배경끼리 섞는다                  요소(합친 배경)와 페이지가 섞인다
   -> (41, 61, 41)                        -> (204, 82, 0)
```

실무에서 이게 터지는 자리는 「**분명히 `multiply` 를 걸었는데 안 섞인다**」이다.\
원인은 대개 **조상 어딘가에 쌓임 맥락이 있어서** 섞을 대상이 잘린 것이다.

> **backdrop(배경판)** — 지금 그리는 것의 **뒤에 이미 그려져 있는 모든 것**을 합친 결과.\
> 예: 파란 판 위에 초록 띠가 놓여 있고 그 위에 무언가를 그린다면, 그 자리의 backdrop 은 초록이거나 파랑이다(좌표마다 다르다).

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 네 질문을 둔다.

1. **`mix-blend-mode` 는 정확히 무엇과 섞이는가** — 부모인가, 바로 뒤 형제인가, 뒤쪽 전부인가.
2. `background-blend-mode` 와 **어떻게 갈리는가** — 한 요소에 둘 다 걸면 어떻게 되는가.
3. 결과 색을 **공식으로 예측할 수 있는가** — 픽셀이 공식과 맞는가.
4. **`isolation: isolate` 가 정확히 무엇을 하는가** — 그리고 그것만이 격리를 만드는가.

## 동작 방식

### (1) `mix-blend-mode` 는 **같은 쌓임 맥락 안의 뒤쪽 전부**와 섞인다

**언제 쓰나** — 요소를 뒤에 깔린 것과 어울리게 만들 때.

```text
  무대: 왼쪽 절반 #3399cc, 오른쪽 절반 #66cc33
  그 위에 #cc6633 인 띠 하나 (mix-blend-mode: multiply)

   ┌──────────┬──────────┐
   │ #3399cc  │ #66cc33  │   <- backdrop 은 좌표마다 다르다
   ├──────────┴──────────┤
   │  #cc6633 띠(multiply) │
   └─────────────────────┘

   띠의 왼쪽 픽셀 = (41, 61, 41)   <- #3399cc 와 섞인 값
   띠의 오른쪽 픽셀 = (82, 82, 11)  <- #66cc33 와 섞인 값
```

```html demo
<div class="bd"><span class="src">multiply</span></div>
<style>
  .bd  { width: 240px; height: 80px; margin: 16px; background: #3399cc; }
  .src { display: block; width: 120px; height: 80px; background: #cc6633;
         mix-blend-mode: multiply; font: 12px/80px system-ui; text-align: center; }
</style>
```

> **보이는 것** — 하늘색 판(`#3399cc`) 왼쪽 절반에 주황 사각형(`#cc6633`)이 얹혀 있는데, 겹친 자리는 주황도 하늘색도 아닌 **짙은 올리브색**이 된다. 판의 오른쪽 절반은 하늘색 그대로다.\
> **실측** — *(Chrome 151 headless: 겹친 자리 `(41,61,41)`. 명세의 multiply 공식 `Cb×Cs÷255` 를 `(51,153,204)`·`(204,102,51)` 에 적용한 값 `(41,61,41)` 과 **정확히 일치**. 안 겹친 자리는 `(51,153,204)`.)*\
> **바꿔 볼 것** — `multiply` → `screen`(밝아져 `(214,194,214)` 가 된다) · `multiply` → `difference`(`(153,51,153)` 자주색) · `.bd` 에 `isolation: isolate` 추가(아무것도 안 바뀐다 — 섞을 대상이 `.bd` 자신의 배경이라서)

그림 해설 (한 단계씩):

- 섞이는 대상은 **부모 하나가 아니라 그 좌표의 backdrop 전부**다. 좌표마다 달라진다.
- 그 범위는 **같은 쌓임 맥락 안**이다. 쌓임 맥락 경계를 넘어가지 못한다 — 이것이 (5) 의 격리다.

비용 — 혼합은 **합성 단계**의 일이라 레이아웃을 다시 돌리지는 않지만, 뒤쪽을 읽어야 하므로 별도 레이어가 생긴다.

### (2) 혼합 공식 — 픽셀이 명세와 맞는가

**언제 쓰나** — 「왜 이 색이 나왔나」를 설명해야 할 때. 그리고 **눈이 아니라 수치로 검증할 때.**

backdrop `#3399cc` = `(51,153,204)`, source `#cc6633` = `(204,102,51)` 로 12 모드를 전부 쟀다.

```text
  모드          픽셀            공식 값         일치
  normal       (204,102, 51)   (204,102, 51)   ○
  multiply     ( 41, 61, 41)   ( 41, 61, 41)   ○
  screen       (214,194,214)   (214,194,214)   ○
  overlay      ( 82,133,173)   ( 82,133,173)   ○
  darken       ( 51,102, 51)   ( 51,102, 51)   ○
  lighten      (204,153,204)   (204,153,204)   ○
  difference   (153, 51,153)   (153, 51,153)   ○
  exclusion    (173,133,173)   (173,133,173)   ○
  hard-light   (173,122, 82)   (173,122, 82)   ○
  soft-light   ( 89,141,180)   ( 89,141,180)   ○
  color-dodge  (255,255,255)   (255,255,255)   ○
  color-burn   (  0,  0,  0)   (  0,  0,  0)   ○
```

★ **12 모드 36 채널이 전부 정확히 일치했다.** 혼합은 채널별 산술이고 그 산술은 명세에 적혀 있다.

```text
  대표 공식 세 개 (채널 하나씩, 0~255 스케일)

  multiply(Cb, Cs)  =  Cb x Cs / 255
  screen(Cb, Cs)    =  255 - (255-Cb) x (255-Cs) / 255
  overlay(Cb, Cs)   =  hard-light(Cs, Cb)
                       hard-light(b,s) = multiply(b, 2s)        (s <= 127.5)
                                       = screen(b, 2s-255)      (s >  127.5)
```

```text
  multiply 를 손으로 따라가 보기 (R 채널)

  Cb = 51 (하늘색의 R),  Cs = 204 (주황의 R)
  51 x 204 = 10,404
  10,404 / 255 = 40.8  ->  41       <- 픽셀도 41 이었다

  G: 153 x 102 / 255 = 61.2 -> 61   <- 픽셀 61
  B: 204 x  51 / 255 = 40.8 -> 41   <- 픽셀 41
```

★ **주의 — 이 실험의 두 색은 서로 보색이라(`Cs = 255 - Cb`) `color-dodge` 가 전부 255, `color-burn` 이 전부 0 이 됐다.** 공식과는 맞지만 **그 두 모드의 성격을 보여 주는 값은 아니다.** 다른 색으로 다시 재야 한다.

*(Chrome 151 headless 실측 — 60×60 상자 12개를 한 문서에 나란히 두고 각 중심 픽셀을 읽어, 명세 §blending 의 정의를 그대로 옮긴 파이썬 함수와 대조했다.)*

### (3) `background-blend-mode` — **한 요소 안의 배경 레이어들끼리**

**언제 쓰나** — 이미지와 색, 또는 이미지 둘을 한 요소 안에서 섞을 때.

```text
  한 요소의 배경 스택 (위에서 아래로)

   background-image  layer 0   #cc6633      <- source
        ↓ background-blend-mode 로 섞는다
   background-image  layer 1   (없음)
        ↓
   background-color            #3399cc      <- 스택의 맨 아래(backdrop)
        ================================
   요소 바깥                    페이지 배경   <- 여기와는 안 섞인다
```

```html demo
<div class="page">
  <div class="bbm">background-blend-mode</div>
  <div class="mbm">mix-blend-mode</div>
</div>
<style>
  .page { background: #ffcc00; padding: 12px; width: 200px; }
  .page div { height: 56px; margin: 10px 0; font: 12px/56px system-ui; text-align: center;
              background-image: linear-gradient(#cc6633, #cc6633); background-color: #3399cc; }
  .bbm { background-blend-mode: multiply; }
  .mbm { mix-blend-mode: multiply; }
</style>
```

> **보이는 것** — 노란 판 위에 같은 배경(주황 이미지 + 하늘색 색상)을 가진 상자 둘이 있다. 위 상자는 **짙은 올리브색**, 아래 상자는 **붉은 주황색**이다. 배경 선언이 완전히 같은데 손잡이가 달라 결과가 다르다.\
> **실측** — *(Chrome 151 headless: 위 `(41,61,41)` = multiply(`#3399cc`, `#cc6633`) · 아래 `(204,82,0)` = multiply(`#ffcc00`, `#cc6633`). 둘 다 공식과 정확히 일치. 페이지 배경 `(255,204,0)`.)*\
> **바꿔 볼 것** — `.page div` 의 `background-color: #3399cc` → `transparent`(위 상자가 주황 `(204,102,51)` 이 된다 — 섞을 아래 레이어가 없어진다) · `.mbm` 에 `isolation: isolate` 추가(**안 바뀐다** — 자기 자신에 걸면 소용없다) · `.page` 에 `isolation: isolate` 추가(★ **이것도 안 바뀐다** — `.page` 의 노란 배경은 `.page` 자신의 쌓임 맥락 **안**이라 여전히 섞인다)

그림 해설:

- `background-blend-mode` 의 backdrop 은 **자기 배경 스택의 아래쪽**이다. **요소 바깥은 절대 안 본다.**
- `mix-blend-mode` 는 **자기 배경 스택을 다 합친 뒤** 그 결과를 **바깥 backdrop** 과 섞는다.
- 그래서 같은 요소에 둘 다 걸면 **두 단계가 차례로** 일어난다.

```text
  레이어가 하나뿐이면 background-blend-mode 는 아무 일도 안 한다

  background-image: linear-gradient(#cc6633,#cc6633)
  background-color: transparent
  background-blend-mode: multiply       -> 픽셀 (204,102,51) = 원본 그대로
```

*(Chrome 151 headless 실측 — 네 판을 한 문서에 두고 잰 값이다.)*

### (4) 둘을 한 표로 갈라 두기

```text
                       mix-blend-mode              background-blend-mode
  섞는 것              요소 전체 ↔ 뒤에 깔린 것      한 요소의 배경 레이어들끼리
  요소 바깥을 보나      본다                        안 본다
  쌓임 맥락을 만드나    만든다 (normal 이 아니면)     만들지 않는다
  값 개수             하나                        레이어마다 하나 (쉼표로 나열)
  격리로 끊을 수 있나   된다 (조상에 isolation)       애초에 바깥과 안 섞이므로 무관
```

### (5) ★★ `isolation: isolate` — **섞임을 그 조상에서 끊는다**

**언제 쓰나** — `mix-blend-mode` 를 쓴 요소가 **너무 멀리까지 섞일 때.**

```text
  전 (격리 없음)                          후 (그룹에 isolation: isolate)

  페이지 배경 #ffcc00                      페이지 배경 #ffcc00
       └ 그룹 (배경 없음)                       └ 그룹 [격리]  ← 여기서 끊긴다
            └ 자식 #6699ff multiply                └ 자식 #6699ff multiply

  자식이 페이지 배경까지 내려가 섞인다         자식이 볼 backdrop 이 「그룹 안」뿐이다
  픽셀 = (102, 122, 0)                     그룹 안에 아무것도 없으니 그냥 자기 색
                                           픽셀 = (102, 153, 255)
```

```html demo
<div class="page">
  <div class="g"><span class="src">섞인다</span></div>
  <div class="g iso"><span class="src">격리</span></div>
</div>
<style>
  .page { background: #ffcc00; padding: 12px; width: 180px; }
  .g    { height: 50px; margin: 10px 0; }
  .iso  { isolation: isolate; }
  .src  { display: block; height: 50px; background: #6699ff; mix-blend-mode: multiply;
          font: 12px/50px system-ui; text-align: center; }
</style>
```

> **보이는 것** — 노란 판 위에 같은 파란 띠 둘이 있다. 위 띠는 노랑과 섞여 **탁한 올리브색**이고, 아래 띠는 **원래의 밝은 파랑** 그대로다. 두 띠의 선언 차이는 부모의 `isolation: isolate` 한 줄뿐이다.\
> **실측** — *(Chrome 151 headless: 위 `(102,122,0)` = multiply(`#ffcc00`, `#6699ff`) 공식 값과 일치 · 아래 `(102,153,255)` = `#6699ff` 원색 그대로.)*\
> **바꿔 볼 것** — `.iso` 의 `isolation: isolate` → `opacity: .999`(똑같이 격리된다) · → `transform: translateZ(0)`(역시 격리된다) · `.src` 의 `multiply` → `normal`(위 띠도 원색이 된다)

그림 해설 (한 단계씩):

- `isolation: isolate` 는 그 요소에 **쌓임 맥락을 만든다.**
- 혼합은 **쌓임 맥락 경계를 못 넘는다.** 그래서 자손의 `mix-blend-mode` 가 볼 backdrop 이 그 안으로 좁혀진다.
- ★ **자기 자신에게 걸면 소용없다.** 끊고 싶은 **조상**에 걸어야 한다.

비용 — 없다. 다만 쌓임 맥락이 생기므로 그 안의 `z-index` 가 바깥과 못 겨룬다([목록의 **22번 주제**](../22-stacking-context-and-z-index/)).

### (6) ★ **쌓임 맥락을 만드는 것은 전부 격리가 된다**

**언제 쓰나** — 「`isolation` 을 안 썼는데 왜 안 섞이지」에 부딪혔을 때.

같은 실험을 여덟 판으로 돌렸다. 전부 `#6699ff` + `multiply` 인 자식이고, 부모에 붙인 것만 다르다.

```text
  부모에 붙인 것              겹침 픽셀        판정
  (아무것도 없음)             (102,122,  0)   섞인다
  isolation: isolate         (102,153,255)   격리
  opacity: .999              (102,153,255)   격리
  filter: brightness(1)      (102,153,255)   격리
  transform: translateZ(0)   (102,153,255)   격리
  will-change: opacity       (102,153,255)   격리
  position:relative + z-index:0  (102,153,255)  격리
  mix-blend-mode: normal     (102,122,  0)   섞인다   ★ 이것만 격리가 아니다
```

- **쌓임 맥락을 만드는 선언은 값이 무해해 보여도 전부 격리를 만든다.** `opacity: .999`·`brightness(1)`·`translateZ(0)` 이 전부 그렇다.
- **`mix-blend-mode: normal` 만 예외**다 — 초깃값이라 쌓임 맥락을 안 만든다.
- 반대로 이것이 사고의 원인이 된다: **페이드인용 `opacity` 애니메이션 하나가 혼합을 통째로 껐다.**

```text
  47번과 이어지는 자리

  filter -> 쌓임 맥락  -> 격리        (이 절)
  filter -> backdrop root            (47번 (9))
  isolation -> 쌓임 맥락 -> 격리       (이 절)
  isolation -> backdrop root 아님     (47번 (9) — 실측)

  곧 「격리」와 「backdrop root」는 겹치지만 같은 축이 아니다.
```

*(Chrome 151 headless 실측 — 여덟 판을 한 문서에 두고 같은 좌표의 픽셀을 읽었다. `backdrop-filter` 쪽 판정은 [47번](../47-filter-and-backdrop-filter/2-summary.md)의 실측이다.)*

### (7) 분리 가능 모드와 그렇지 않은 모드

**언제 쓰나** — 왜 어떤 모드는 채널 계산으로 설명되고 어떤 것은 아닌지 알 때.

```text
  분리 가능(separable) — 채널마다 따로 계산한다
   normal multiply screen overlay darken lighten
   color-dodge color-burn hard-light soft-light difference exclusion
   -> 위 (2) 의 12개가 전부 여기다. 그래서 공식 대조가 된다

  분리 불가(non-separable) — RGB 를 한 덩어리로 보고 색상/채도/명도를 옮긴다
   hue  saturation  color  luminosity
   -> 채널별 곱으로는 설명이 안 된다. 이 문서는 이 넷을 재지 않았다
```

- 실무에서 쓰는 것은 거의 전부 분리 가능 쪽이다.
- 분리 불가 넷은 「원본의 밝기는 두고 색만 바꾸기」 같은 용도에 쓴다.

## 문법 — 형태와 어디서 헷갈리나

### 최소 형태

```css
/* 요소와 뒤쪽을 섞는다 — 값 하나 */
.a { mix-blend-mode: multiply; }

/* 한 요소의 배경 레이어들끼리 섞는다 — 레이어마다 하나, 쉼표 */
.b { background-image: url(a.png), url(b.png);
     background-blend-mode: multiply, screen; }

/* 섞임을 여기서 끊는다 — 조상에 건다 */
.c { isolation: isolate; }

/* 기본값 */
.d { mix-blend-mode: normal; isolation: auto; }
```

### 헷갈리는 자리 — 「어디에 걸어야 하나」

| 하고 싶은 것 | 어디에 거나 |
|---|---|
| 이 요소를 뒤와 섞기 | **그 요소**에 `mix-blend-mode` |
| 이 요소의 배경끼리 섞기 | **그 요소**에 `background-blend-mode` |
| 섞임을 여기까지만 | **끊고 싶은 조상**에 `isolation: isolate` |
| 자식 하나만 안 섞이게 | 그 자식의 `mix-blend-mode` 를 `normal` 로 |

★ **`isolation` 을 자기 자신에게 거는 것이 가장 흔한 실수다.** 자기 `mix-blend-mode` 는 그것으로 안 꺼진다.

### 금지에 가까운 형태 — 조용히 버려지는 것들

```css
.x {
  mix-blend-mode: multiplyy;      /* 오타 — 버려진다 */
  background-blend-mode: 50%;     /* 타입 틀림 — 버려진다 */
  isolation: isolated;            /* 값 이름 틀림 — 버려진다 */
}
```

★ 「진단 3창」으로 물으면 **셋 다 `cssRules` 에서 사라지고** 계산값은 초깃값(`normal`·`normal`·`auto`)이다.
콘솔에도 화면에도 신호가 없다.

★ **그리고 이 주제에는 「3창을 전부 통과하는데 화면이 다른」 제4의 상태가 있다** — **격리**다.

```text
  창 1  cssRules  → mix-blend-mode: multiply 가 그대로 담겨 있다
  창 2  querySelectorAll → 잡혔다
  창 3  getComputedStyle → "multiply"
  그런데 화면 픽셀은 원색 그대로다

  이유: 조상 어딘가에 쌓임 맥락이 있어 섞을 backdrop 이 없다.
  ★ 계산값으로는 절대 안 잡힌다. 픽셀을 읽어야 한다.
```

## 구현 세부사항 대 언어 보장

| 항목 | 누가 보장하나 |
|---|---|
| 12개 분리 가능 모드의 **공식** | **명세**(compositing-1 §blending — 채널별 정의) |
| 혼합이 **쌓임 맥락 경계를 못 넘는** 것 | **명세**(compositing-1 §isolation — 그룹이 격리된다) |
| `isolation: isolate` 가 **쌓임 맥락을 만드는** 것 | **명세**(compositing-1 §isolation) |
| `mix-blend-mode` 가 `normal` 이 아니면 **쌓임 맥락을 만드는** 것 | **명세**(compositing-1 §mix-blend-mode) |
| `background-blend-mode` 가 **요소 바깥을 안 보는** 것 | **명세**(compositing-1 §background-blend-mode — 배경 레이어와 배경색만) |
| 쌓임 맥락을 만드는 **다른 선언들도 격리가 되는** 것 | **명세**에서 따라오지만, 이 문서의 여덟 판 목록은 **실측**이다 |
| **정확한 반올림** | ★ **보장 아님.** 한 실험에서 `multiply` 의 B 채널이 공식 10.2 → 픽셀 11 로 **1 차이**가 났다(다른 34 채널은 정확히 일치). 반올림 방식은 구현 세부다 |
| **혼합이 일어나는 색 공간** | ★ 이 문서는 **sRGB 값으로 공식이 맞았다**는 것만 확인했다. `color-interpolation` 이 다른 값일 때는 재지 않았다 |
| 각 픽셀의 **정확한 값** | ★ `--disable-gpu` **소프트웨어 렌더링** 결과다. GPU 합성에서는 반올림이 다를 수 있다 |

★ **엔진은 Chrome 하나다.** Firefox 155.0.1 은 이 환경에서 headless 스크린샷이 산출되지 않고 WebKit 은 이 머신에 없다. 크로스 브라우저는 **Baseline 데이터로만** 접지했다.

## 어디서 틀리나

### 1. `isolation` 을 자기 자신에게 건다

```css
.bad { mix-blend-mode: multiply; isolation: isolate; }   /* 아무것도 안 바뀐다 */
.ok  { isolation: isolate; }                             /* 조상에 건다 */
```

- `isolation` 은 **자손의 혼합**을 끊는다. 자기 혼합은 못 끈다.

★ **그리고 「조상에 걸면 된다」도 절반만 맞다** — **그 조상이 자기 배경을 갖고 있으면 소용없다.**

```text
  page(배경 #ffcc00) [격리]
       └ 자식 mix-blend-mode: multiply

  page 자신의 노란 배경은 page 의 쌓임 맥락 「안」에서 그려진다
  -> 자식은 여전히 그 노랑과 섞인다.  실측 픽셀 (204,82,0) — 격리 전과 동일
```

- 끊으려면 **배경을 가진 조상과 혼합 요소 사이**에 배경 없는 껍데기를 두고 **거기에** `isolation` 을 건다.
- (5) 의 demo 가 정확히 그 형태다 — 노란 `.page` 와 파란 띠 사이의 `.g` 에 걸었다.

### 2. 「안 섞인다」의 원인을 혼합 쪽에서 찾는다

- 계산값은 `multiply` 로 멀쩡하다. 원인은 **조상의 쌓임 맥락**이다.
- 실측에서 `opacity: .999` 한 줄로 혼합이 통째로 꺼졌다.
- 찾는 법은 조상을 거슬러 올라가며 `opacity`·`transform`·`filter`·`will-change`·`z-index` 를 훑는 것이다.

### 3. 두 손잡이를 헷갈린다

```text
  「이미지 위에 색 오버레이」를 하고 싶다
   -> 한 요소 안이면 background-blend-mode
   -> 별개의 요소면 mix-blend-mode
  둘을 바꿔 쓰면 아무 일도 안 일어나거나 엉뚱한 것과 섞인다
```

- 실측: 같은 배경 선언에 손잡이만 바꿔 `(41,61,41)` 과 `(204,82,0)` 이 나왔다.

### 4. 배경 레이어가 하나인데 `background-blend-mode` 를 건다

- 섞을 대상이 없으므로 **아무 일도 안 일어난다.** `background-color` 를 주거나 레이어를 하나 더 얹어야 한다.

### 5. 「눈으로 보니 맞다」로 끝낸다

- `multiply` 결과가 「어두워 보이는」 것은 대부분의 색에서 맞지만, **`color-dodge`·`color-burn` 은 색 조합에 따라 255/0 으로 포화된다.**
- 이 문서의 실험에서도 두 색이 보색이라 dodge 가 전부 흰색, burn 이 전부 검정이 됐다. **공식과는 맞지만 모드의 성격을 보여 주는 값이 아니다.**
- 결과를 공식과 대조하는 습관이 필요하다.

### 6. 흰 배경 위에서 `multiply` 를 테스트한다

```text
  multiply(255, Cs) = 255 x Cs / 255 = Cs      <- 아무 일도 안 일어난 것처럼 보인다
  screen(0, Cs)     = Cs                       <- 검정 배경에서 screen 도 마찬가지
```

- **흰 배경에서 `multiply`, 검정 배경에서 `screen` 은 항등원**이다. 테스트가 무력해진다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 사진 위에 브랜드 색 입히기 | `background-blend-mode: multiply`·`luminosity` | 한 요소 안에서 끝난다 |
| 글자를 배경에 녹이기 | `mix-blend-mode: difference`·`exclusion` | 배경 밝기와 무관하게 읽힌다 |
| 두 도형이 겹친 자리 강조 | `mix-blend-mode: multiply` | 겹침이 자동으로 짙어진다 |
| 혼합이 너무 멀리 간다 | 조상에 `isolation: isolate` | 부작용이 가장 적다(쌓임 맥락만 생긴다) |
| 단순히 반투명 | **`opacity` 나 알파 색**([목록의 **42번 주제**](../42-color-notation-and-spaces/)) | 혼합은 더 비싸고 부작용이 있다 |
| 뒤에 깔린 것을 흐리기 | **`backdrop-filter`**([47번](../47-filter-and-backdrop-filter/2-summary.md)) | 혼합으로는 못 한다 |

**안 쓰는 쪽** — **본문 글자**에 `mix-blend-mode` 를 걸면 배경에 따라 대비가 무너진다. 명도 대비는 **혼합 결과 색**으로 따져야 한다.

## 핵심 문장

- `mix-blend-mode` 는 **같은 쌓임 맥락 안의 뒤쪽 전부**와 섞이고, backdrop 은 **좌표마다 다르다.**
- `background-blend-mode` 는 **한 요소의 배경 레이어들끼리**만 섞는다. 바깥을 안 본다.
- 분리 가능 12모드는 **채널별 산술**이고, 실측에서 **36 채널이 전부 공식과 일치**했다.
- `isolation: isolate` 는 **자손의 혼합을 그 자리에서 끊는다.** 자기 자신에게는 소용없다.
- **쌓임 맥락을 만드는 선언은 전부 격리가 된다** — `opacity: .999` 하나가 혼합을 끈다.

## 관련 자료

- [목록의 **22번 주제**](../22-stacking-context-and-z-index/)(쌓임 맥락과 `z-index`) — **그쪽이 쌓임 맥락의 정본이다. 여기는 「쌓임 맥락 = 격리」라는 등식까지만.**
- [47번 — `filter` 와 `backdrop-filter`](../47-filter-and-backdrop-filter/2-summary.md) — **그쪽은 자기 픽셀을 바꾸는 것과 backdrop root, 여기는 무엇과 섞이나와 격리.** `filter` 가 만든 쌓임 맥락이 여기서 격리로 쓰인다.
- [46번 — 테두리·그림자](../46-borders-radius-outline-shadow/2-summary.md) — 그림자도 혼합 대상이 된다(`mix-blend-mode` 는 요소 전체에 걸린다).
- [49번 — `clip-path` 와 `mask`](../49-clip-path-and-mask/2-summary.md) — **그쪽은 「보일 자리를 정하는 것」, 여기는 「보이는 색을 정하는 것」.**
- 배경 레이어가 쌓이는 규칙은 [목록의 **44번 주제**](../44-backgrounds-and-object-fit/), 색 표기·알파는 **42번 주제**, 그라디언트는 **45번 주제**, `transform` 은 **54번 주제**다.
- [Compositing and Blending Level 1](https://drafts.fxtf.org/compositing-1/)

## 용어 풀이

- **backdrop(배경판)** — 지금 그리는 것의 뒤에 이미 그려진 모든 것을 합친 결과. 좌표마다 다르다.
- **source(원본)** — 지금 그리는 요소 또는 배경 레이어.
- **혼합 모드(blend mode)** — backdrop 과 source 를 어떤 산술로 합칠지 고르는 값.
- **분리 가능(separable) 모드** — R·G·B 를 따로 계산하는 모드. `multiply`·`screen`·`overlay` 등 12개.
- **분리 불가(non-separable) 모드** — RGB 를 한 덩어리로 보는 모드. `hue`·`saturation`·`color`·`luminosity` 넷. 이 문서는 재지 않았다.
- **격리(isolation)** — 한 묶음을 먼저 한 장으로 합쳐, 그 바깥과 더 이상 안 섞이게 하는 것.\
  예: 부모에 `isolation: isolate` 를 걸면 자식의 `multiply` 가 페이지 배경까지 내려가지 못한다.
- **`isolation: isolate`** — 그 요소에 쌓임 맥락을 만들어 격리를 켜는 선언. 자기 `mix-blend-mode` 에는 효과가 없다.
- **쌓임 맥락(stacking context)** — 그 안의 `z-index` 가 바깥과 겨루지 못하는 독립 층. 혼합의 경계이기도 하다. 정본은 [목록의 **22번 주제**](../22-stacking-context-and-z-index/).
- **항등원(identity)** — 어떤 연산에 넣어도 상대를 안 바꾸는 값.\
  예: `multiply` 에서 흰색, `screen` 에서 검정. 그 배경 위에서는 모드를 걸어도 결과가 안 바뀐다.
- **진단 3창** — `cssRules` → `querySelectorAll` → `getComputedStyle`. 이 주제에는 **셋 다 통과하는데 화면이 다른 제4의 상태**(격리)가 있다. 정본은 [07번](../07-syntax-and-error-recovery/2-summary.md).

## 더 들어가면

- **합성 연산자(`Porter-Duff`)** — `mix-blend-mode` 가 「색을 어떻게 섞나」라면, 합성 연산자는 「알파를 어떻게 다루나」다. CSS 에는 `mask-composite`([49번](../49-clip-path-and-mask/2-summary.md))에만 표면이 열려 있다.
- **분리 불가 모드 넷** — `hue`·`saturation`·`color`·`luminosity`. 「원본의 밝기는 두고 색만 바꾸기」에 쓴다. 이 문서는 재지 않았다.
- **혼합과 성능** — 혼합은 뒤쪽을 읽어야 하므로 별도 레이어와 읽기 비용이 생긴다. 큰 면적에 애니메이션과 함께 쓰면 비싸다. 이 문서는 성능을 측정하지 않았다.
- **`color-interpolation`** — 혼합·보간이 어느 색 공간에서 일어나는지를 정하는 축. 이 문서는 기본값에서만 쟀다.

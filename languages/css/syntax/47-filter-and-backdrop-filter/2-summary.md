# css/syntax/47 — `filter` 와 `backdrop-filter` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Filter Effects Module Level 1](https://drafts.fxtf.org/filter-effects-1/) (`filter` 함수들의 정본) · [Filter Effects Module Level 2](https://drafts.fxtf.org/filter-effects-2/) (`backdrop-filter`·backdrop root). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 `demo` 블록 **4개 전부**와 본문의 모든 수치를 **Google Chrome 151.0.7922.173** headless 에서 실제로 렌더해 확인했다.\
> ★ **이 주제는 `getComputedStyle` 로 거의 아무것도 증명하지 못한다.** `filter: blur(4px)` 가 계산값으로 그대로 돌아와도 **실제로 흐려졌는지**는 다른 이야기다.\
> 그래서 **스크린샷 PNG 를 파이썬 표준 라이브러리(`zlib`)로 디코드해 좌표별 `(r,g,b)` 를 읽는 것**이 주 근거다. 흐림은 **경계가 번진 띠의 폭(px)** 으로 잰다.
> **버전** — CSS 에 언어 버전이 없으므로 Baseline 으로 읽는다. webstatus.dev 조회(2026-09-23): `filter` **widely**(2016-09-07 → 2019-03-07) · `backdrop-filter` **newly**(2024-09-16, 아직 widely 아님).
> **여기서 다루지 않는 것** — **쌓임 맥락 자체**는 [목록의 **22번 주제**](../22-stacking-context-and-z-index/)가 정본이다. 여기는 「`filter` 가 그것을 만든다」까지만 쓴다.\
> `box-shadow` 는 [46번](../46-borders-radius-outline-shadow/2-summary.md), **혼합 모드와 `isolation`** 은 [48번](../48-blend-modes-and-isolation/2-summary.md), 자르기·마스킹은 [49번](../49-clip-path-and-mask/2-summary.md)이 정본이다. `transform` 은 [목록의 **54번 주제**](../54-transform-2d-and-origin/), 색 표기는 **42번 주제**다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 수치는 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**`filter` 는 다 그려 놓은 그림을 스캔해서 사진 보정을 거는 것이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 다 그려진 그림 한 장 | **요소와 그 자손 전부를 하나로 합성한 이미지** |
| 보정 필터를 순서대로 통과시키는 레일 | **`filter` 의 함수 목록 — 왼쪽부터 차례로 적용** |
| 보정을 걸려면 일단 한 장으로 **평평하게 눌러야** 한다 | **그래서 쌓임 맥락이 생기고, 자손이 그 판을 못 벗어난다** |
| 그림 **뒤에 있는 벽**을 보정하는 것 | **`backdrop-filter` — 자기가 아니라 뒤에 깔린 것을 건드린다** |

- 사진 보정은 **순서가 있다.** 밝히고 뒤집는 것과 뒤집고 밝히는 것은 다른 사진이 된다.
- 그리고 **한 장으로 눌러야 보정이 걸리므로**, 그 안에 있던 「위로 튀어나오려던 것」·「화면에 붙어 있으려던 것」이 전부 그 판 안에 갇힌다. 이 부작용이 이 주제의 급소다.

```text
  filter 가 하는 일 — 세 단계

   [요소 + 자손을 평소대로 그린다]
              ↓
   [그 결과를 한 장의 이미지로 합친다]   ← 여기서 쌓임 맥락이 생긴다
              ↓
   [함수를 왼쪽부터 차례로 통과시킨다]
              ↓
   [그 결과를 화면에 합성한다]
```

실무에서 이게 터지는 자리는 **`filter: brightness(1)`** 이다.\
**화면상 아무것도 안 바뀌는데** 그 안의 `position: fixed` 가 조용히 고장 난다.

> **합성(compositing)** — 여러 겹으로 그려진 것을 최종 화면 한 장으로 합치는 단계.\
> 예: 반투명 팝업과 그 뒤 본문을 섞어 한 장의 그림으로 만드는 일.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 네 질문을 둔다.

1. **함수를 여러 개 쓰면 순서가 결과를 바꾸는가** — 바꾼다면 어떤 쌍이 바뀌고 어떤 쌍이 안 바뀌는가.
2. `filter` 를 걸면 **아무것도 안 바뀐 것처럼 보여도** 무엇이 망가지는가.
3. `box-shadow` 와 `drop-shadow` 는 **무엇을 따라가는가.**
4. `backdrop-filter` 는 **무엇을 읽어서** 흐리고, 언제 **아무 일도 안 하는가.**

## 동작 방식

### (1) 함수 목록은 왼쪽부터 차례로 — **순서가 결과다**

**언제 쓰나** — 함수를 두 개 이상 쓸 때마다.

```text
  filter: brightness(2) invert(1)        filter: invert(1) brightness(2)

  원본 (204, 51,102)                      원본 (204, 51,102)
      ↓ brightness(2) — 각 채널 x2            ↓ invert(1) — 255 - c
    (255,102,204) (255 에서 잘린다)          ( 51,204,153)
      ↓ invert(1)                            ↓ brightness(2)
    (  0,153, 51)                          (102,255,255) (255 에서 잘린다)
```

```html demo
<div class="ab">brightness → invert</div>
<div class="ba">invert → brightness</div>
<style>
  div { width: 200px; height: 46px; margin: 16px; background: #cc3366;
        font: 12px/46px system-ui; color: #fff; text-align: center; }
  .ab { filter: brightness(2) invert(1); }
  .ba { filter: invert(1) brightness(2); }
</style>
```

> **보이는 것** — 같은 분홍 `#cc3366` 에 같은 두 함수를 걸었는데 위 상자는 **짙은 초록**, 아래 상자는 **밝은 하늘색**이 된다. 순서만 다르다.\
> **실측** — *(Chrome 151 headless: 위 `(0,153,51)` · 아래 `(102,255,255)`. 원본은 `(204,51,102)`.)*\
> **바꿔 볼 것** — `brightness(2)` → `brightness(1)`(두 상자가 같아진다) · 두 줄을 `grayscale(1) invert(1)` 과 `invert(1) grayscale(1)` 로(놀랍게도 **같아진다** — 아래 (2))

그림 해설:

- 함수는 **파이프라인**이다. 앞 함수의 출력이 뒤 함수의 입력이 된다.
- 순서가 결과를 바꾸는 근본 원인은 **클리핑**(255 에서 잘리는 것)과 **비선형 함수**다.

비용 — 함수 하나마다 한 패스가 더 돈다. 목록이 길수록 비싸다(이 문서는 성능을 측정하지 않았다).

### (2) 그런데 **모든 쌍이 갈리는 것은 아니다** — 실측으로 확인해야 한다

**언제 쓰나** — 「순서가 중요하다」를 외우고 나서 반례를 만날 때.

`#cc3366` 에 여섯 쌍을 걸고 픽셀을 대조했다.

```text
  쌍                                         앞 순서        뒤 순서        판정
  grayscale(1) invert(1)   ↔ 뒤집기          (168,168,168) (168,168,168)  같다  ★
  blur(3px) grayscale(1)   ↔ 뒤집기          ( 87, 87, 87) ( 87, 87, 87)  같다
  grayscale(1) hue-rotate(90deg) ↔ 뒤집기    ( 87, 87, 87) ( 89, 89, 89)  다르다(2 차이)
  brightness(2) invert(1)  ↔ 뒤집기          (  0,153, 51) (102,255,255)  다르다
  sepia(1) invert(1)       ↔ 뒤집기          (116,132,159) (206,183,143)  다르다
  contrast(2) brightness(.5) ↔ 뒤집기        (128,  0, 38) ( 77,  0,  0)  다르다
```

★ **`grayscale` 과 `invert` 는 순서를 바꿔도 한 채널도 안 달라졌다.** 예상과 달랐다.

```text
  왜 같은가 (관찰에 대한 설명 — 명세의 정의에서 따라온다)

  grayscale(1) 은 L = 0.2126R + 0.7152G + 0.0722B  (세 계수의 합이 1)
  invert(1)    은 각 채널을 255 - c 로 바꾼다

  뒤집은 값의 휘도 = 0.2126(255-R) + 0.7152(255-G) + 0.0722(255-B)
                   = 255 x (계수 합) - L
                   = 255 - L          <- 곧 「휘도의 뒤집기」와 같다
```

- 곧 순서 규칙은 「무조건 다르다」가 아니라 「**다를 수 있다**」이다. 「같은지」는 **던져 봐야** 안다.
- `grayscale(1) hue-rotate(90deg)` 쌍은 **2 밖에 안 갈린다** — 눈으로는 절대 못 잡는다. 픽셀로만 보인다.

*(Chrome 151 headless 실측 — 위 표는 60×60 `#cc3366` 상자 12개를 한 문서에 나란히 두고 각 중심 픽셀을 읽은 값이다. `grayscale(1)` 단독은 `(87,87,87)` 로, 위 휘도 식의 값 87.2 와 일치했다.)*

### (3) 함수 하나하나가 무엇을 하나 — 같은 색으로 전부 재기

**언제 쓰나** — 어떤 함수를 고를지 정할 때. **한 색으로 전부 재면 비교가 공짜로 따라온다.**

```text
  원본 #cc3366 = (204, 51, 102) · 흰 배경 위

  함수                  결과            한 줄 설명
  none                 (204, 51,102)   기준
  blur(0px)            (204, 51,102)   값이 0 이어도 「필터가 걸린 상태」다 (아래 (4) 주의)
  brightness(1.5)      (255, 76,153)   채널 x1.5, 255 에서 잘린다
  brightness(0.5)      (102, 26, 51)   채널 x0.5
  contrast(2)          (255,  0, 77)   128 을 기준으로 벌린다
  contrast(0.5)        (166, 89,115)   128 쪽으로 모은다
  grayscale(1)         ( 87, 87, 87)   휘도 하나로 눌러 버린다
  grayscale(0.5)       (146, 69, 95)   원본과 회색의 중간
  invert(1)            ( 51,204,153)   255 - c
  sepia(1)             (139,123, 96)   갈색 톤 행렬
  saturate(3)          (255,  0,131)   채도를 3배
  saturate(0)          ( 87, 87, 87)   grayscale(1) 과 같은 값이 나왔다
  hue-rotate(90deg)    (102, 95,  0)   색상환을 90도 돌린다
  hue-rotate(180deg)   (  0,124, 73)   180도
  opacity(0.5)         (230,153,179)   흰 배경과 반반 섞인 값
```

- `drop-shadow(x y blur color)` 는 값이 색이 아니라 **그림자**라 이 표에 없다 — (6) 에서 따로 잰다.
- `opacity()` 는 **배경에 따라 결과가 달라진다.** 위 값은 **흰 배경 위**에서 잰 것이다.

*(Chrome 151 headless 실측 — 40×40 상자 15개를 한 문서에 나란히 두고 각 중심 픽셀을 읽었다.)*

### (4) 흐림은 「번진 띠의 폭」으로 잰다

**언제 쓰나** — 「흐려졌다」를 눈이 아니라 숫자로 말해야 할 때.

```text
  검정|흰색 이 딱 붙은 경계를 만들고, 값이 0 도 255 도 아닌 구간의 폭을 잰다

  blur 없음      ...0 0 0 0|255 255 255...      전이 띠 폭 = 0 (한 픽셀에서 0→255)
  blur(4px)      ...0 2 .. 53 93 139 183 218 .. 255...   전이 띠 폭 = 16
  blur(12px)     ................................         전이 띠 폭 = 47
```

```html demo
<div class="sharp"></div>
<div class="blur"></div>
<style>
  div { width: 260px; height: 50px; margin: 16px;
        background: linear-gradient(to right, #000 0 130px, #fff 130px 260px); }
  .blur { filter: blur(6px); }
</style>
```

> **보이는 것** — 두 띠 모두 왼쪽 절반이 검정, 오른쪽 절반이 흰색이다. 위 띠는 경계가 **칼날처럼 딱 갈리고**, 아래 띠는 경계가 **뿌옇게 번지며** 띠의 바깥 테두리까지 흐려진다.\
> **실측** — *(Chrome 151 headless: 경계에서 값이 5\~250 사이인 구간의 폭이 위 띠는 **0px**(한 픽셀에서 0→255), 아래 띠는 **22px**(x 135\~156).)*\
> **바꿔 볼 것** — `blur(6px)` → `blur(1px)`(띠가 눈에 띄게 좁아진다) · `blur(6px)` → `blur(6px) contrast(4)`(번진 자리가 다시 또렷해진다)

- 측정한 띠 폭은 `blur(4px)` 에서 16px, `blur(12px)` 에서 47px, `blur(6px)` 에서 22px 이었다 — **선언한 길이의 대략 4배**다.
- 명세는 이 인자를 「가우시안 함수의 **표준편차**」로 정의한다. ±2σ 구간이 4σ 이므로 관찰과 어긋나지 않는다. 다만 **정확한 배수는 보장이 아니다**(아래 「구현 세부사항」).
- ★ **`blur(0px)` 은 「필터 없음」이 아니다.** 픽셀은 원본과 같지만 **쌓임 맥락과 포함 블록은 그대로 만들어진다**(다음 두 절).

### (5) ★ `filter` 는 **쌓임 맥락**을 만든다 — 22번과 잇는 자리

**언제 쓰나** — `z-index: 9999` 를 줬는데 안 먹을 때. 원인 목록에 `filter` 가 들어 있다.

```text
  전 (filter 없음)                     후 (filter: brightness(1))

  부모                                  부모 [새 쌓임 맥락]
   └ 자식 z-index: 9999 ─┐               └ 자식 z-index: 9999 ─┐
                         │                                     │ 부모 판 안에 갇힘
  형제 z-index: 1 ───────┘              형제 z-index: 1 ────────┘
        ↑ 자식이 위로 나온다                    ↑ 형제가 위로 온다
  겹침 픽셀 = 자식색 (220,38,38)        겹침 픽셀 = 형제색 (37,99,235)
```

```text
  쌓임 맥락을 만드는 선언 — 픽셀로 확인한 것들 (같은 실험, 같은 좌표)

  아무것도 없음          (220,38,38) 자식이 이김
  filter: brightness(1) (37,99,235) 갇힘
  opacity: .999         (37,99,235) 갇힘
  isolation: isolate    (37,99,235) 갇힘
```

- **`filter` 값이 무엇이든 `none` 이 아니면** 쌓임 맥락이 생긴다. `brightness(1)`·`blur(0)` 처럼 **화면이 안 바뀌는 값도 마찬가지**다.
- 쌓임 맥락 자체의 정본은 [목록의 **22번 주제**](../22-stacking-context-and-z-index/)다. 여기서는 「`filter` 가 그것을 만든다」까지만 쓴다.
- 이 성질은 [48번](../48-blend-modes-and-isolation/2-summary.md)의 **격리**와 같은 뿌리다 — 쌓임 맥락을 만드는 것은 전부 혼합을 끊는다.

*(Chrome 151 headless 실측 — 네 판을 한 문서에 두고 `z-index:9999` 자식과 `z-index:1` 형제가 겹치는 좌표의 픽셀을 읽었다.)*

### (6) ★★ `filter` 는 `fixed`·`absolute` 자손의 **포함 블록을 가로챈다**

**언제 쓰나** — 화면에 붙어 있어야 할 모달·툴팁이 **스크롤을 따라 움직일 때.** 이 주제의 급소다.

```text
  전 (filter 없음)                          후 (filter: brightness(1))

  host (400,90) 에 있음                      host (400,90) 에 있음
   └ position: fixed; left:0; top:0          └ position: fixed; left:0; top:0
        ↓                                          ↓
     뷰포트 기준 (0,0)                         host 기준 (400,90)
     offsetParent = null                      offsetParent = host
     스크롤 300 해도 (0,0)                     스크롤 300 하면 (400,-210)
                                              ★ fixed 인데 스크롤을 따라간다
```

```text
  absolute 도 마찬가지다

  구조: outer(position:relative) > mid > absolute 자식(left:0; top:0)

  mid 에 filter 없음        자식 = (30,70)   offsetParent = outer
  mid 에 brightness(1)      자식 = (70,540)  offsetParent = mid   ← mid 의 모서리로 옮겨갔다
```

그림 해설 (한 단계씩):

- `filter` 가 `none` 이 아니면 그 요소가 **`fixed`·`absolute` 자손의 포함 블록**이 된다.
- 그래서 `position: fixed` 가 **더 이상 뷰포트에 붙지 않는다.** 스크롤하면 같이 움직인다.
- **화면에 아무 변화가 없어도 그렇다.** `brightness(1)` 은 픽셀을 한 개도 안 바꾸는데 이 부작용은 그대로다.
- 같은 부작용을 내는 다른 속성으로 `transform`([목록의 **54번 주제**](../54-transform-2d-and-origin/))·`backdrop-filter`·`will-change` 가 있다.

*(Chrome 151 headless 실측 — 위 두 표는 각각 세 판·두 판을 한 문서에 두고 `getBoundingClientRect()`·`offsetParent` 를 읽고, `window.scrollTo(0,300)` 뒤 다시 읽은 값이다. `filter: none` 을 명시한 판은 부작용이 없었다.)*

비용 — 이 부작용은 **끌 수 없다.** `filter` 를 쓰는 순간 딸려 온다. 모달을 그 안에 두지 않는 것이 해법이다.

### (7) `drop-shadow` 는 **알파 모양**을 따라간다 — `box-shadow` 와 갈리는 지점

**언제 쓰나** — 투명한 PNG·SVG 아이콘에 그림자를 붙일 때.

```text
  8x8 투명 PNG (왼쪽 아래만 불투명한 삼각형)

   . . . . . . . .      . = 투명 (알파 0)
   # . . . . . . .      # = 불투명 #111827
   # # . . . . . .
   # # # . . . . .
   # # # # . . . .
   # # # # # . . .
   # # # # # # . .
   # # # # # # # .
```

```text
  전 (box-shadow: 14px 14px 0 red)        후 (filter: drop-shadow(14px 14px 0 red))

  그림자가 「상자」를 따라간다               그림자가 「알파 모양」을 따라간다
   ┌────────────┐                          ╲
   │▒▒▒▒▒▒▒▒▒▒▒▒│ ← 투명한 구석에도           ╲▒
   │▒▒▒▒▒▒▒▒▒▒▒▒│   빨강이 깔린다             ╲▒▒
   └────────────┘                          ╲▒▒▒

  투명부 뒤 그림자 자리 픽셀 = (220,38,38)   같은 자리 = (255,255,255)
  불투명부 뒤              = (220,38,38)   같은 자리 = (220,38,38)
```

```html demo
<img class="box" alt="" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAYAAADED76LAAAALUlEQVR42mMQlFD/z4APgBTgVQRTgFMRsgKsitAVYCjCpgBFES4FcEX4FIAwAN9XLx3NViC3AAAAAElFTkSuQmCC">
<img class="drop" alt="" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAYAAADED76LAAAALUlEQVR42mMQlFD/z4APgBTgVQRTgFMRsgKsitAVYCjCpgBFES4FcEX4FIAwAN9XLx3NViC3AAAAAElFTkSuQmCC">
<style>
  img { display: block; width: 72px; height: 72px; margin: 24px 40px;
        image-rendering: pixelated; }
  .box  { box-shadow: 14px 14px 0 #dc2626; }
  .drop { filter: drop-shadow(14px 14px 0 #dc2626); }
</style>
```

> **보이는 것** — 같은 투명 PNG(왼쪽 아래만 채워진 계단 삼각형) 둘이다. 위 것은 **네모난 빨간 그림자**가 이미지 전체 뒤에 깔려 투명한 오른쪽 위에도 빨강이 보이고, 아래 것은 **계단 삼각형 모양의 빨간 그림자**만 보인다.\
> **실측** — *(Chrome 151 headless: 투명한 오른쪽 위에 대응하는 그림자 자리가 위 `(220,38,38)` 빨강 · 아래 `(255,255,255)` 흰색. 불투명한 왼쪽 아래의 그림자 자리는 둘 다 `(220,38,38)`.)*\
> **바꿔 볼 것** — `drop-shadow(14px 14px 0 …)` → `drop-shadow(0 0 8px …)`(모양을 따라가는 후광이 된다) · `.box` 에 `border-radius: 50%` 추가(`box-shadow` 도 그만큼은 둥글어진다)

- `drop-shadow` 는 **알파 채널로 모양을 뜬 뒤** 그 모양을 그림자로 쓴다.
- `box-shadow` 는 **`border-box` 모양**(`border-radius` 반영)을 쓴다. 내용의 투명도는 안 본다.
- 대신 `drop-shadow` 에는 **`spread` 인자가 없다.** `box-shadow` 의 다섯 값 중 네 개(`x y blur color`)만 받는다.
- 그리고 `drop-shadow` 는 `filter` 이므로 **(5)·(6) 의 부작용이 전부 따라온다.**

### (8) `backdrop-filter` — **자기가 아니라 뒤에 깔린 것**을 흐린다

**언제 쓰나** — 반투명 유리판(프로스티드 글래스) UI.

```text
  filter 와 backdrop-filter 가 건드리는 대상

        filter                        backdrop-filter
   ┌──────────────┐               ┌──────────────┐
   │ 뒤에 깔린 것  │ 그대로         │ 뒤에 깔린 것  │ ← 이쪽이 흐려진다
   ├──────────────┤               ├──────────────┤
   │ 이 요소      │ ← 흐려진다      │ 이 요소      │ 그대로(자기 배경은 선명)
   └──────────────┘               └──────────────┘
```

```html demo
<div class="stage"><div class="glass">backdrop-filter</div></div>
<style>
  .stage { width: 280px; height: 140px; margin: 16px; position: relative;
           background: repeating-linear-gradient(45deg, #1d4ed8 0 14px, #fde047 14px 28px); }
  .glass { position: absolute; left: 40px; top: 40px; width: 200px; height: 60px;
           backdrop-filter: blur(8px); background: rgba(255,255,255,.15);
           font: 12px/60px system-ui; color: #fff; text-align: center; }
</style>
```

> **보이는 것** — 파랑·노랑 45도 줄무늬 위에 가로로 긴 판이 얹혀 있다. 판 **바깥**의 줄무늬는 또렷하고, 판 **안쪽**의 줄무늬만 뭉개져 색이 섞인 뿌연 띠로 보인다. 판의 경계에서 또렷/뿌연 것이 딱 갈린다.\
> **실측** — *(Chrome 151 headless: 같은 `y` 행의 빨강 채널 범위가 판 바깥 `29\~253`(폭 224), 판 안 `129\~255`(폭 126). `backdrop-filter` 한 줄만 뺀 대조판에서는 판 안이 `62\~254`(폭 192)였다 — 흰 오버레이가 아니라 흐림이 폭을 줄였다.)*\
> **바꿔 볼 것** — `blur(8px)` → `blur(2px)`(줄무늬가 다시 보인다) · `blur(8px)` → `grayscale(1)`(뒤가 흑백이 된다) · `.glass` 의 `background` → `transparent`(흐림만 남는다)

- `backdrop-filter` 는 **자기 뒤에 이미 그려진 것**을 읽어 필터를 걸고, 그 위에 자기 배경을 얹는다.
- 그 「뒤」의 범위를 **backdrop root** 라고 한다 — 다음 절이 그 경계다.

### (9) ★ `backdrop-filter` 가 **아무 일도 안 하는 경우** — backdrop root

**언제 쓰나** — 「분명히 썼는데 안 흐려진다」에 부딪혔을 때.

```text
  페이지 배경(줄무늬) ─ 이것을 흐리고 싶다
       └ wrap ────────── 여기에 무엇이 붙어 있느냐가 갈림길
            └ glass  backdrop-filter: blur(6px)

  wrap 에 붙은 것            유리판 안 줄무늬의 밝기 범위      판정
  (없음)                     17 ~ 244                        흐려졌다
  isolation: isolate         17 ~ 244                        흐려졌다  ★
  opacity: .999              0 ~ 255                         그대로다
  filter: blur(0)            0 ~ 255                         그대로다
```

그림 해설:

- **조상에 `opacity`(<1)나 `filter` 가 있으면 거기서 새 backdrop root 가 생긴다.** 유리판이 읽을 「뒤」가 그 그룹 안으로 좁혀져, 그룹 안에 아무것도 없으면 **흐릴 것이 없어진다.**
- ★ **`isolation: isolate` 는 backdrop root 를 만들지 않았다.** 쌓임 맥락은 만드는데 이 축은 다르다 — **격리(48번)와 backdrop root 는 같은 축이 아니다.**
- 실무 증상은 늘 같다: 「페이드인 애니메이션(`opacity`)을 넣었더니 유리 효과가 사라졌다」.

*(Chrome 151 headless 실측 — 네 판을 한 문서에 두고, 유리판 안쪽 한 행의 빨강 채널 최소·최대를 읽었다. `0 ~ 255` 는 줄무늬가 원본 그대로라는 뜻이다.)*

## 문법 — 형태와 어디서 헷갈리나

### 최소 형태

```css
/* 함수 하나 */
.a { filter: blur(4px); }

/* 여러 개 — 공백으로 잇는다. 쉼표가 아니다. 왼쪽부터 적용 */
.b { filter: grayscale(1) brightness(1.2) drop-shadow(0 2px 4px rgb(0 0 0 / .4)); }

/* 끄기 */
.c { filter: none; }

/* SVG 필터 참조 */
.d { filter: url(#myFilter); }

/* 뒤에 깔린 것 */
.e { backdrop-filter: blur(12px) saturate(1.4); }
```

### 헷갈리는 자리 — 인자의 단위

| 함수 | 인자 | 비고 |
|---|---|---|
| `blur()` | **길이만**(`4px`) | `%` 도 숫자도 안 된다 |
| `brightness()`·`contrast()`·`grayscale()`·`invert()`·`opacity()`·`saturate()`·`sepia()` | 숫자 또는 `%` | `0.5` 와 `50%` 가 같다 |
| `hue-rotate()` | 각도(`90deg`·`.25turn`) | 숫자만 쓰면 안 된다 |
| `drop-shadow()` | `x y [blur] [color]` | ★ **`spread` 가 없다** · `inset` 도 없다 |

- `grayscale`·`invert`·`sepia` 는 **1(=100%) 을 넘겨도 1 로 잘린다.**
- `brightness`·`contrast`·`saturate` 는 **1 을 넘길 수 있다.**

### 금지에 가까운 형태 — 조용히 버려지는 것들

```css
.x {
  filter: blurr(4px);        /* 함수 이름 오타 — 통째로 버려진다 */
  filter: blur(4);           /* 단위 없음 — 버려진다 */
  filter: blur(4px), invert(1);   /* 쉼표 — 버려진다. 공백으로 잇는다 */
}
```

★ 「진단 3창」으로 물으면 이렇게 나온다.

```text
  창 1  cssRules  → 그 선언이 규칙 텍스트에 아예 없다
  창 2  querySelectorAll → 정상 (선택자는 잡힌다)
  창 3  getComputedStyle().filter → "none"

  화면·콘솔에는 아무 신호가 없다. 목록 중 하나만 틀려도 「목록 전체」가 죽는다.
```

*(Chrome 151 headless 실측 — `filter: blurr(4px)` 를 포함한 규칙을 던지니 `cssRules` 에서 그 선언만 사라지고 계산값은 `none` 이었다.)*

## 구현 세부사항 대 언어 보장

| 항목 | 누가 보장하나 |
|---|---|
| 함수가 **목록 순서대로** 적용되는 것 | **명세**(filter-effects-1 §7 — 앞 함수의 출력이 뒤 함수의 입력) |
| `filter: none` 이 아니면 **쌓임 맥락**이 생기는 것 | **명세**(filter-effects-1 §5 — grouping property) |
| `filter` 가 `fixed`·`absolute` 자손의 **포함 블록**이 되는 것 | **명세**(filter-effects-1 §5 — containing block for fixed/absolutely positioned descendants) |
| `drop-shadow` 가 **알파 채널**로 모양을 뜨는 것 | **명세**(filter-effects-1 §7 — 입력의 알파 채널로 그림자를 만든다) |
| `drop-shadow` 에 `spread` 가 **없는** 것 | **명세**(같은 절의 문법 정의) |
| 조상의 `opacity`·`filter` 가 **backdrop root** 를 만드는 것 | **명세**(filter-effects-2 §backdrop root) |
| `isolation: isolate` 가 backdrop root 를 **안 만드는** 것 | ★ **Chrome 151 에서 관찰한 것.** 명세의 backdrop root 목록을 정독해 대조하지는 않았다 — 관찰로만 적는다 |
| 흐림 띠 폭이 선언 길이의 **약 4배**인 것 | ★ **관찰이다.** 명세는 인자를 「표준편차」로 정의할 뿐 화면상의 띠 폭을 못 박지 않는다. **정확한 배수를 보장으로 쓰지 마라** |
| 각 필터 함수의 **정확한 결과 RGB** | ★ **보장 아님.** 행렬 계수는 명세에 있지만, 이 문서의 값은 `--disable-gpu` **소프트웨어 렌더링** 결과다. GPU 합성에서는 반올림이 다를 수 있다 |
| `grayscale` 과 `invert` 의 **순서가 무관한** 것 | ★ **관찰이다.** 두 함수의 명세 정의에서 따라오는 성질로 보이지만, 명세가 「교환 가능」이라고 적은 것은 아니다 |

★ **엔진은 Chrome 하나다.** Firefox 155.0.1 은 이 환경에서 headless 스크린샷이 산출되지 않고 WebKit 은 이 머신에 없다. 크로스 브라우저 차이는 **Baseline 데이터로만** 접지했다 — `backdrop-filter` 는 **newly**(2024-09-16)라 오래된 브라우저에는 없다.

## 어디서 틀리나

### 1. 「값이 0 이면 필터가 없는 것」이라고 생각한다

```text
  filter: blur(0)      픽셀은 원본과 같다
                       ★ 쌓임 맥락은 생긴다
                       ★ fixed 자손의 포함 블록도 가로챈다
  filter: none         아무 일도 안 일어난다
```

- 애니메이션 시작값으로 `blur(0)` 을 두면 **끝날 때까지 부작용이 유지된다.**
- 끄려면 `none` 을 써야 한다.

### 2. 모달·드롭다운을 `filter` 가 걸린 조상 안에 둔다

- `position: fixed` 가 **뷰포트가 아니라 그 조상 기준**이 된다. 스크롤하면 따라 움직인다.
- 실측: 스크롤 300 뒤 `(400,-210)` — 화면 밖으로 나갔다.
- 고치는 법은 모달을 `<body>` 직계로 옮기는 것이다(포털).

### 3. 쉼표로 함수를 잇는다

- `filter: blur(4px), invert(1)` 은 **선언 통째로 버려진다.** 공백으로 잇는다.
- `box-shadow` 는 쉼표, `filter` 는 공백 — 헷갈리기 딱 좋다.

### 4. `backdrop-filter` 가 안 먹는데 원인을 유리판에서 찾는다

- 원인은 대개 **조상**이다. 어딘가에 `opacity` 나 `filter` 가 있으면 backdrop root 가 잘린다.
- 실측에서 `opacity: .999` 하나로 줄무늬가 **하나도 안 흐려졌다.**

### 5. 순서를 「무조건 중요하다」로 외운다

- `grayscale` 과 `invert` 는 순서를 바꿔도 **한 채널도 안 달라졌다.**
- 「중요할 수 있다」가 맞다. **같은지 다른지는 던져 봐야 안다.**

### 6. 「흐려 보인다」를 눈으로 판정한다

- `grayscale(1) hue-rotate(90deg)` 쌍은 결과가 `(87,87,87)` 과 `(89,89,89)` 로 **2 밖에 안 갈린다.**
- 눈으로는 같아 보이지만 다르다. **픽셀을 읽어야** 판정이 선다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 투명 PNG·SVG 아이콘의 그림자 | `filter: drop-shadow()` | 알파 모양을 따라간다 |
| 네모난 카드의 그림자 | `box-shadow` ([46번](../46-borders-radius-outline-shadow/2-summary.md)) | 부작용이 없다 |
| 비활성 상태 표시 | `filter: grayscale(1)` | 한 줄로 전체를 흑백으로 |
| 로딩 중 배경 가리기 | `filter: blur()` | 다만 그 안의 `fixed` 를 확인할 것 |
| 유리판 UI | `backdrop-filter` | Baseline **newly** — 대체 경로를 둘 것 |
| 색 하나만 바꾸기 | **`color-mix()`·상대 색 구문**([목록의 **43번 주제**](../43-color-mix-and-relative-color/)) | 필터는 다 그린 뒤에 거는 것이라 비싸고 부작용이 있다 |
| 요소를 임의 모양으로 자르기 | **`clip-path`** ([49번](../49-clip-path-and-mask/2-summary.md)) | 필터로는 못 한다 |

**안 쓰는 쪽** — **`fixed` 자손이 있는 조상**에는 `filter` 를 쓰지 않는다. 모달·툴팁·`sticky` 헤더가 전부 이 함정에 빠진다.

## 핵심 문장

- `filter` 는 **다 그려진 한 장**에 거는 보정이고, 함수는 **왼쪽부터 차례로** 통과한다.
- **순서가 갈릴 수 있다** — 갈리는지 아닌지는 픽셀로 확인해야 한다. `grayscale`↔`invert` 는 안 갈렸다.
- `filter` 가 `none` 이 아니면 **쌓임 맥락이 생기고 `fixed`·`absolute` 자손의 포함 블록을 가로챈다.** `brightness(1)` 도 마찬가지다.
- `drop-shadow` 는 **알파 모양**, `box-shadow` 는 **상자 모양**을 따라간다.
- `backdrop-filter` 는 **뒤에 깔린 것**을 흐리고, 조상의 `opacity`·`filter` 가 그 「뒤」를 끊어 버린다.

## 관련 자료

- [목록의 **22번 주제**](../22-stacking-context-and-z-index/)(쌓임 맥락과 `z-index`) — **그쪽이 쌓임 맥락의 정본이다. 여기는 「`filter` 가 그것을 만든다」까지만.**
- [46번 — 테두리·`border-radius`·`outline`·`box-shadow`](../46-borders-radius-outline-shadow/2-summary.md) — **그쪽은 상자 모양을 따라가는 그림자까지, 여기는 알파 모양을 따라가는 그림자부터.**
- [48번 — 혼합 모드와 `isolation`](../48-blend-modes-and-isolation/2-summary.md) — **그쪽은 「무엇과 섞이나」와 그것을 끊는 법, 여기는 「자기 픽셀을 어떻게 바꾸나」.** `filter` 가 만든 쌓임 맥락이 거기서는 **격리**로 쓰인다.
- [49번 — `clip-path` 와 `mask`](../49-clip-path-and-mask/2-summary.md) — **그쪽은 모양으로 잘라내는 것, 여기는 색을 바꾸는 것.**
- [15번 — 박스 모델](../15-box-model-and-box-sizing/2-summary.md)·[17번 — 블록 서식 맥락](../17-block-formatting-context/2-summary.md) — 포함 블록·독립 서식 맥락의 배경 지식.
- `transform` 은 [목록의 **54번 주제**](../54-transform-2d-and-origin/)(같은 부작용을 낸다), 색 표기는 **42번 주제**, `color-mix()` 는 **43번 주제**다.
- [Filter Effects Level 1](https://drafts.fxtf.org/filter-effects-1/) · [Filter Effects Level 2](https://drafts.fxtf.org/filter-effects-2/)

## 용어 풀이

- **`filter`** — 요소와 자손을 한 장으로 합친 뒤 그 이미지에 거는 보정. 목록 왼쪽부터 차례로 적용된다.
- **필터 함수 목록** — 공백으로 잇는다. 쉼표로 이으면 선언 전체가 버려진다.
- **쌓임 맥락(stacking context)** — 그 안의 `z-index` 가 바깥과 겨루지 못하게 되는 독립 층. 정본은 [목록의 **22번 주제**](../22-stacking-context-and-z-index/).
- **포함 블록(containing block)** — `position: absolute`/`fixed` 인 요소가 `top`/`left` 를 재는 기준 상자.\
  예: `fixed` 의 포함 블록은 보통 뷰포트인데, 조상에 `filter` 가 있으면 그 조상으로 바뀐다.
- **`drop-shadow()`** — 입력의 **알파 채널**로 모양을 떠서 그리는 그림자. `spread` 인자가 없다.
- **`backdrop-filter`** — 요소 **뒤에 이미 그려진 것**에 거는 필터. Baseline **newly**(2024-09-16).
- **backdrop root** — `backdrop-filter` 가 읽을 수 있는 「뒤」의 범위. 조상에 `opacity`(<1)·`filter` 가 있으면 거기서 잘린다.
- **표준편차(standard deviation)** — 가우시안 흐림이 얼마나 넓게 퍼지는지를 정하는 값. `blur(4px)` 의 `4px` 가 이것이다.\
  예: 이 문서의 실측에서 `blur(4px)` 의 번진 띠는 16px 이었다(대략 4배).
- **진단 3창** — `cssRules` → `querySelectorAll` → `getComputedStyle`. 정본은 [07번](../07-syntax-and-error-recovery/2-summary.md).

## 더 들어가면

- **SVG 필터(`filter: url(#id)`)** — 단축 함수로 안 되는 것(변위·난류·합성)을 직접 조립하는 축. 색 연산 공간(`color-interpolation-filters`)이 기본으로 linearRGB 라 단축 함수와 결과가 다르다. 이 문서는 확인하지 않았다.
- **합성 레이어와 비용** — `filter` 는 대개 별도 레이어를 만든다. 애니메이션에서 `blur` 값을 매 프레임 바꾸면 비싸다. 이 문서는 성능을 측정하지 않았다.
- **`filter` 와 접근성** — `contrast()`·`grayscale()` 로 대비를 낮추면 읽기 어려워진다. 명도 대비는 필터 **적용 후** 값으로 따져야 한다.
- **`backdrop-filter` 의 대체 경로** — `@supports (backdrop-filter: blur(1px))` 로 갈라 반투명 배경만 주는 방식. `@supports` 는 [목록의 **41번 주제**](../41-supports-feature-queries/)다.

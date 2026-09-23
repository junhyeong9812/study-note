# css/syntax/47 — `filter` 와 `backdrop-filter` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 색은 Google Chrome 151.0.7922.173 headless 로 렌더한 스크린샷 PNG 를 파이썬 표준 라이브러리(`zlib`)로 디코드해 그 좌표의 `(r,g,b)` 를 읽은 값**이고,
> **모든 좌표는 `getBoundingClientRect()`·`offsetParent` 를 읽은 값**이다.\
> **손으로 계산해 유도한 수치는 없다.** 규칙은 [Filter Effects 1](https://drafts.fxtf.org/filter-effects-1/)·[Filter Effects 2](https://drafts.fxtf.org/filter-effects-2/) 로 접지했다.\
> ★ 렌더는 `--disable-gpu` **소프트웨어 렌더링**이다. 정확한 픽셀 값을 「보장」으로 읽지 마라.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 순서만 바꿨다

**실행 결과** (Chrome 151 headless — 원본 `#cc3366` = `(204,51,102)`)

```text
filter: brightness(2) invert(1)     (  0, 153,  51)
filter: invert(1) brightness(2)     (102, 255, 255)
```

**`.ab`**

- **`(0,153,51)`** — 짙은 초록.

**`.ba`**

- **`(102,255,255)`** — 밝은 하늘색.

**갈리는 원인**

- **클리핑**이다. `brightness(2)` 를 먼저 걸면 `(255,102,204)` 로 **255 에서 잘린 뒤** 뒤집히지만, 뒤집기를 먼저 하면 `(51,204,153)` 에서 시작해 **다른 자리가 잘린다.**
- 파이프라인이므로 **앞 함수가 버린 정보는 뒤 함수가 되살릴 수 없다.**

**`brightness(1)` 로 바꾸면**

- 곱이 1 이라 아무 일도 안 하므로 두 판이 **같아진다**(뒤집기만 남는다).
- 그런데 `brightness(1)` 도 **필터가 걸린 상태**라서 쌓임 맥락·포함 블록 부작용은 그대로다(9번).

### 2. 순서가 안 갈리는 쌍도 있는가

**실행 결과** (Chrome 151 headless)

```text
쌍                                    앞 순서         뒤 순서         판정
grayscale(1) invert(1)                (168,168,168)  (168,168,168)  같다
grayscale(1) 단독                      ( 87, 87, 87)  —              —
grayscale(1) hue-rotate(90deg)        ( 87, 87, 87)  ( 89, 89, 89)  다르다 (2 차이)
blur(3px) grayscale(1)                ( 87, 87, 87)  ( 87, 87, 87)  같다
sepia(1) invert(1)                    (116,132,159)  (206,183,143)  다르다
contrast(2) brightness(0.5)           (128,  0, 38)  ( 77,  0,  0)  다르다
```

**두 픽셀**

- ★ **같다.** 둘 다 `(168,168,168)` 이다. **예상과 달랐던 자리다.**

**왜 그런가**

- `grayscale(1)` 은 휘도 `L = 0.2126R + 0.7152G + 0.0722B` 를 구한다. **세 계수의 합이 1** 이다.
- 그래서 뒤집은 값의 휘도는 `0.2126(255-R) + 0.7152(255-G) + 0.0722(255-B) = 255 - L` 이 되어 **「휘도를 뒤집은 것」과 같아진다.**
- 곧 순서 규칙은 「무조건 다르다」가 아니라 「**다를 수 있다**」다.

**`grayscale(1)` 단독**

- **`(87,87,87)`** 이다. 위 식으로 계산하면 87.2 이고 픽셀과 일치했다.

**`grayscale` ↔ `hue-rotate`**

- **다르다.** `(87,87,87)` 과 `(89,89,89)` — **2 밖에 안 갈린다.**
- 눈으로는 절대 못 잡는다. **픽셀을 읽어야만** 보인다.

### 3. 흐림을 숫자로 재라

**실행 결과** (Chrome 151 headless — 값이 5\~250 사이인 구간의 폭)

```text
선언            전이 띠            폭
없음            (한 픽셀에서 0→255)  0
blur(4px)      x 162 ~ 177        16
blur(6px)      x 135 ~ 156        22
blur(12px)     x 146 ~ 192        47
```

**띠 폭 (필터 없음)**

- **0px** 이다. `x=169` 가 0, `x=170` 이 255 — 한 픽셀에서 끊긴다.

**`blur(4px)`**

- **16px** 이다.

**`blur(12px)`**

- **47px** 이다.

**보장인가 관찰인가**

- ★ **관찰이다.** 명세는 인자를 「가우시안 함수의 **표준편차**」로 정의할 뿐 화면상의 띠 폭을 못 박지 않는다.
- 측정된 배수(16/4 = 4.0, 47/12 ≈ 3.9, 22/6 ≈ 3.7)는 ±2σ 구간과 어긋나지 않지만, **「4배」를 보장으로 쓰면 안 된다.** 게다가 이 값은 `--disable-gpu` 소프트웨어 렌더링 결과다.

### 4. 화면이 안 바뀌는데 무엇이 망가지나

**실행 결과** (Chrome 151 headless — `host` 셋을 한 문서에 두고 잼)

```text
host 의 선언            host 좌표     fixed 자식 좌표   offsetParent   scrollTo(0,300) 뒤
filter 없음             (120, 90)    (  0,   0)      null           (  0,    0)
filter: brightness(1)  (400, 90)    (400,  90)      host           (400, -210)   ★
filter: none           (680, 90)    (  0,   0)      null           (  0,    0)
```

**`.fx` 의 좌표**

- **`(400, 90)`** — `host` 의 왼쪽 위 모서리다. `(0,0)` 이 아니다.

**`offsetParent`**

- **`host`** 다. `filter` 가 없으면 `null`(뷰포트 기준)이다.

**스크롤 뒤**

- **`(400, -210)`** 이다. 300 만큼 위로 올라갔다 — **`fixed` 인데 스크롤을 따라간다.**

**`filter: none` 으로 바꾸면**

- 부작용이 **완전히 사라진다.** 좌표 `(0,0)`, `offsetParent` `null`, 스크롤해도 그대로.
- 핵심은 **`brightness(1)` 이 픽셀을 한 개도 안 바꾸는데** 이 부작용은 있었다는 것이다. 화면으로는 잡을 수 없다.

`absolute` 도 같다.

```text
구조: outer(position:relative) > mid > absolute 자식(left:0; top:0)
mid 에 filter 없음       자식 (30, 70)    offsetParent = outer
mid 에 brightness(1)     자식 (70, 540)   offsetParent = mid
```

### 5. `z-index: 9999` 가 안 먹는다

**실행 결과** (Chrome 151 headless — 겹치는 좌표의 픽셀)

```text
.wrap 의 선언             겹침 픽셀        읽는 법
(없음)                    (220, 38, 38)   자식(빨강)이 이김
filter: brightness(1)     ( 37, 99,235)   형제(파랑)가 위 — 자식이 갇혔다
opacity: .999             ( 37, 99,235)   갇혔다
isolation: isolate        ( 37, 99,235)   갇혔다
```

**겹치는 좌표의 픽셀**

- **파랑 `(37,99,235)`** 이다. `z-index: 9999` 가 졌다.

**`filter` 를 빼면**

- **빨강 `(220,38,38)`** 이 된다. 자식이 형제 위로 올라온다.

**같은 결과를 내는 선언들**

- `opacity` 가 1 미만 · `transform` 이 `none` 이 아님 · `isolation: isolate` · `will-change` 에 그 속성들 · `position` + `z-index` 가 `auto` 아님 · `mix-blend-mode` 가 `normal` 아님 · `contain: paint` 등.
- [48번](../48-blend-modes-and-isolation/2-summary.md)에서 픽셀로 확인한 목록: `isolation`·`opacity`·`filter`·`transform`·`will-change`·`position`+`z-index:0` 여섯이 **전부 격리**를 만들었다.

**정본 주제**

- [목록의 **22번 주제**](../22-stacking-context-and-z-index/)(쌓임 맥락과 `z-index`)다. 이 문서는 「`filter` 가 그것을 만든다」까지만 다룬다.

### 6. 그림자 둘 — 무엇을 따라가나

**실행 결과** (Chrome 151 headless — 왼쪽 아래만 불투명한 8×8 삼각형 PNG 를 72×72 로 확대)

```text
                        투명한 구석의 그림자 자리   불투명부의 그림자 자리
box-shadow              (220, 38, 38) 빨강        (220, 38, 38) 빨강
filter: drop-shadow     (255,255,255) 흰색        (220, 38, 38) 빨강
```

**`.a` 의 투명부 그림자 자리**

- **빨강 `(220,38,38)`** 이다. `box-shadow` 는 **`border-box` 모양**을 그림자로 쓴다 — 내용의 투명도를 안 본다.

**`.b` 에서는**

- **흰색 `(255,255,255)`** — 그림자가 없다. `drop-shadow` 는 **알파 채널로 모양을 떠서** 그 모양만 그림자로 쓴다.

**`spread` 를 쓸 수 있는가**

- **없다.** `drop-shadow()` 는 `x y [blur] [color]` 네 자리만 받는다. `inset` 도 없다.

**따라오는 부작용**

- `drop-shadow` 는 `filter` 이므로 **쌓임 맥락이 생기고 `fixed`·`absolute` 자손의 포함 블록을 가로챈다**(4·5번).
- `box-shadow` 에는 그런 부작용이 전혀 없다.

### 7. `backdrop-filter` 가 안 먹는다

**실행 결과** (Chrome 151 headless — 줄무늬 배경 위 유리판 안쪽 한 행의 빨강 채널 범위)

```text
wrap 에 붙은 것          유리판 안 범위   판정
(없음)                  17 ~ 244       흐려졌다
isolation: isolate      17 ~ 244       흐려졌다   ★
opacity: .999            0 ~ 255       그대로다
filter: blur(0)          0 ~ 255       그대로다
(유리판 밖은 네 판 모두 0 ~ 255)
```

**무엇을 읽는가**

- **자기 뒤에 이미 그려진 것**이다. 자기 배경이 아니다. 필터를 건 결과 위에 자기 배경을 얹는다.
- 실측에서 유리판 **안쪽 행만** 대비 범위가 줄고 바깥 행은 그대로였다.

**조상에 `opacity: .999`**

- **아무 일도 안 한다.** 거기서 새 **backdrop root** 가 생겨, 유리판이 읽을 「뒤」가 그 그룹 안으로 좁혀진다. 그룹 안에 배경이 없으니 흐릴 것이 없다.

**조상에 `isolation: isolate`**

- ★ **그대로 흐려졌다.** `isolation` 은 쌓임 맥락은 만들지만 **backdrop root 는 안 만든다.**
- **격리(48번)와 backdrop root 는 같은 축이 아니다.**

**근거의 종류**

- `opacity`·`filter` 가 backdrop root 를 만든다는 것은 **명세 근거**(filter-effects-2 §backdrop root)이자 실측이다.
- `isolation` 이 **안 만든다**는 것은 ★ **이 브라우저에서의 관찰**이다 — 명세의 backdrop root 목록을 전수 대조하지는 않았다.

### 8. 함수 목록의 문법

**실행 결과** (Chrome 151 headless — 「진단 3창」의 창 1·3)

```text
입력                                  cssRules 에 남은 것            계산값
filter: blur(4)                      .a { }                        none
filter: hue-rotate(90)               .b { }                        none
filter: blur(4px), invert(1)         .c { }                        none
filter: blur(4px) blurr(2px)         .d { }                        none   ★ 앞의 유효한 함수까지 같이 죽었다
filter: blur(4px) invert(1)          .e { filter: blur(4px) invert(1); }  blur(4px) invert(1)
filter: hue-rotate(0.25turn)         .f { filter: hue-rotate(0.25turn); } hue-rotate(90deg)
```

**무엇으로 잇는가**

- **공백**이다. 쉼표로 이으면 선언 전체가 버려진다(`box-shadow` 와 반대라 헷갈린다).

**오타 하나면**

- ★ **목록 전체가 죽는다.** `blur(4px) blurr(2px)` 에서 유효한 `blur(4px)` 까지 같이 사라졌다.
- 선언 값은 **통째로 파싱되므로** 부분 생존이 없다.

**단위를 빼면**

- `blur(4)` 는 **무효**다. `blur()` 는 길이만 받는다.

**`hue-rotate(90)`**

- **무효**다. 각도 단위가 필요하다. `hue-rotate(0.25turn)` 은 유효하고 계산값이 `hue-rotate(90deg)` 로 정규화된다.

### 9. `blur(0)` 과 `none` 의 차이

**픽셀**

- **같다.** 실측에서 `blur(0px)` 의 결과는 `(204,51,102)` 로 원본과 한 채널도 안 달랐다.

**쌓임 맥락**

- **다르다.** `filter` 가 `none` 이 아니면 값이 무엇이든 쌓임 맥락이 생긴다. 실측: `brightness(1)` 판에서 `z-index:9999` 자식이 갇혔다.

**포함 블록**

- **다르다.** `filter: brightness(1)` 판의 `fixed` 자식은 `(400,90)` 에 붙고 스크롤을 따라갔다. `filter: none` 판은 `(0,0)` 에 붙고 안 따라갔다.

**애니메이션 시작값으로 쓰면**

- **애니메이션 내내(그리고 그 전에도) 부작용이 유지된다.** 안에 `position: fixed` 가 있으면 조용히 깨진다.
- 끌 때는 반드시 `none` 으로 되돌린다. 다만 `none` 은 보간되지 않으므로 전환 설계를 따로 해야 한다([52번](../52-transition/2-summary.md)).

### 10. 다른 주제로 잇기

**48번에서 무엇으로 쓰이나**

- **격리(isolation)** 다. 쌓임 맥락을 만드는 것은 전부 `mix-blend-mode` 의 혼합을 그 자리에서 끊는다.
- 그래서 `isolation: isolate` 가 못 하는 자리에 `filter: brightness(1)` 을 써도 같은 격리가 된다(다만 backdrop root 까지 만들어 버린다 — 7번).

**같은 포함 블록 부작용을 내는 속성**

- **`transform`** 이고 [목록의 **54번 주제**](../54-transform-2d-and-origin/)다. `backdrop-filter`·`will-change`·`contain` 도 같은 목록에 있다.
- `position` 과 포함 블록의 정본은 [목록의 **21번 주제**](../21-position-and-containing-block/)다.

**색 하나만 바꾸고 싶을 때**

- **`color-mix()` 와 상대 색 구문**이고 [목록의 **43번 주제**](../43-color-mix-and-relative-color/)다. 색 표기 자체는 **42번 주제**다.
- `filter` 는 다 그린 뒤에 거는 것이라 비싸고 부작용이 딸려 온다.

**임의 모양으로 잘라내려면**

- **`clip-path`** 이고 [49번](../49-clip-path-and-mask/2-summary.md) 주제다. 알파로 깎으려면 같은 주제의 `mask` 다.

## 용어 풀이

- **`filter`** — 요소와 자손을 한 장으로 합친 뒤 그 이미지에 거는 보정. 목록 왼쪽부터 차례로 적용된다.
- **파이프라인(filter function list)** — 앞 함수의 출력이 뒤 함수의 입력이 되는 구조.\
  예: `brightness(2) invert(1)` 은 밝힌 뒤 뒤집는다 — 밝히면서 255 에서 잘린 정보는 되돌아오지 않는다.
- **클리핑(clipping)** — 계산 결과가 0\~255 밖으로 나가면 경계값으로 잘리는 것. 필터 순서가 갈리는 주요 원인이다.
- **휘도(luminance)** — `0.2126R + 0.7152G + 0.0722B`. `grayscale()` 이 쓰는 값이고 세 계수의 합이 1 이다.
- **표준편차(standard deviation)** — `blur(<length>)` 의 인자가 뜻하는 값. 화면상 번지는 띠 폭은 이 문서 실측에서 대략 그 4배였다(보장 아님).
- **쌓임 맥락(stacking context)** — 그 안의 `z-index` 가 바깥과 겨루지 못하는 독립 층. 정본은 [목록의 **22번 주제**](../22-stacking-context-and-z-index/).
- **포함 블록(containing block)** — `absolute`/`fixed` 요소가 `top`/`left` 를 재는 기준 상자.\
  예: `fixed` 의 포함 블록은 보통 뷰포트인데, 조상에 `filter` 가 있으면 그 조상이 된다.
- **`drop-shadow()`** — 입력의 알파 채널로 모양을 떠서 그리는 그림자. `spread`·`inset` 이 없다.
- **`backdrop-filter`** — 요소 뒤에 이미 그려진 것에 거는 필터. Baseline **newly**(2024-09-16).
- **backdrop root** — `backdrop-filter` 가 읽을 수 있는 「뒤」의 범위. 조상의 `opacity`(<1)·`filter` 가 여기를 끊는다.
- **진단 3창** — `cssRules` → `querySelectorAll` → `getComputedStyle`. 정본은 [07번](../07-syntax-and-error-recovery/2-summary.md).

## 실행 검증

| 무엇을 | 어떻게 | 결과 |
|---|---|---|
| 필터 순서 | `#cc3366` 에 여섯 쌍을 걸고 중심 픽셀 대조 | 네 쌍 다름 · **`grayscale`↔`invert` 는 동일** |
| 각 함수의 결과색 | 같은 색 15판을 한 문서에서 렌더 | 표 (3) 의 값 전부 |
| `grayscale` 과 휘도 식 | 픽셀 `(87,87,87)` 대 식의 값 87.2 | 일치 |
| 흐림 띠 폭 | 검정↔흰색 경계에서 `5 < v < 250` 구간 측정 | 없음 0 · 4px → 16 · 6px → 22 · 12px → 47 |
| `filter` 와 쌓임 맥락 | `z-index:9999` 자식과 형제의 겹침 픽셀 | 없음 빨강 · `brightness(1)`·`opacity`·`isolation` 전부 파랑 |
| `filter` 와 `fixed` 포함 블록 | `rect`·`offsetParent` + `scrollTo(0,300)` | `(400,90)` → `(400,-210)` · `offsetParent = host` |
| `filter` 와 `absolute` 포함 블록 | 같은 방식 | 자식이 `(30,70)` → `(70,540)` 로 이동 |
| `drop-shadow` 대 `box-shadow` | 투명 삼각형 PNG(data URI) 두 판의 그림자 자리 픽셀 | 투명부 `(220,38,38)` 대 `(255,255,255)` |
| `backdrop-filter` | 줄무늬 위 유리판 안팎 행의 채널 범위 | 안 126 대 밖 224 (대조판 192) |
| backdrop root | 조상에 `isolation`/`opacity`/`filter` 를 각각 붙여 네 판 | `opacity`·`filter` 만 흐림을 껐다 |
| 무효 문법 | 「진단 3창」으로 일곱 줄 | `blur(4)`·`hue-rotate(90)`·쉼표·오타 전부 `cssRules` 에서 사라짐 |
| demo 4개 | 각 블록을 `<!doctype>`·`<body>` 래퍼에 넣어 렌더 + 픽셀 대조 | 「보이는 것」·「바꿔 볼 것」 단언 전부 화면과 일치 |

**구현 의존 항목** — ①흐림 띠 폭이 선언 길이의 **약 4배**인 것 ②각 필터 함수의 **정확한 결과 RGB** ③`isolation: isolate` 가 backdrop root 를 **안 만드는** 것. 셋 다 Chrome 151 에서 관찰한 것이고, ①②는 `--disable-gpu` **소프트웨어 렌더링** 결과라 GPU 합성과 미세하게 다를 수 있다.\
**엔진은 Chrome 하나다.** Firefox 155.0.1 은 이 환경에서 headless 스크린샷이 산출되지 않고 WebKit 은 이 머신에 없다 — **「두 엔진에서 확인했다」고 적지 않았다.** 크로스 브라우저는 Baseline 데이터로만 접지했다(webstatus.dev 조회 2026-09-23: `filter` widely 2016-09-07/2019-03-07 · `backdrop-filter` **newly** 2024-09-16).

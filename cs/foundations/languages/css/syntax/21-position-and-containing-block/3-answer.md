# css/syntax/21 — `position` 다섯 값과 포함 블록 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 좌표는 Google Chrome 151.0.7922.173 headless 에서 실제로 렌더해 `getBoundingClientRect()` 로 잰 값**이다. 단위는 px 다.\
> ★ **「잘렸나」는 좌표로 안 나오므로 스크린샷 픽셀을 읽어 판정했다** — 그 자리에는 RGB 값을 적었다.\
> **손으로 계산해 유도한 수치는 없다.** 규칙은 [CSS Positioned Layout Level 3](https://drafts.csswg.org/css-position-3/) 과 [CSS Transforms Level 2](https://drafts.csswg.org/css-transforms-2/) 로 접지했다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 다섯 값이 자리를 남기는가

**실행 결과** (Chrome 151 headless — 폭 300 컨테이너, 24px 짜리 형제 셋, 가운데에 `top:20px; left:30px`)

```text
position    형제1      대상        형제3      컨테이너 높이
static      (2,2)     (2,30)      (2,58)          88      ← 선언이 무시됨
relative    (2,2)    (32,50)      (2,58)          88      ← 자리는 그대로
absolute    (2,2)   (20,-88)      (2,30)          60      ← 자리가 사라짐
inset 단축  (2,2)    (42,40)      (2,58)          88
```

**`.x` 가 그려지는 자리**

- `static` — **(2,30).** 보통 형제와 한 픽셀도 안 다르다.
- `relative` — **(32,50).** 원래 자리 (2,30) 에서 `left:30`·`top:20` 만큼 이동.
- `absolute` — **(20,−88).** 컨테이너를 기준으로 음수다. 위치 지정 조상이 없어 **초기 포함 블록**(문서 원점)에 붙었기 때문이다(문서 좌표로는 (30,20)).

**형제 `3` 의 y**

- `static` **58** · `relative` **58** · `absolute` **30**.
- ★ `absolute` 에서만 **형제가 위로 올라왔다** — 대상이 흐름에서 빠져 자리가 없어졌기 때문이다.

**컨테이너 높이**

- `static`·`relative` **88**(24×3 + 테두리 4+ 마진), `absolute` **60**(24×2 + 4).
- **자리를 남기느냐가 높이에 그대로 드러난다.**

**`static` 에서 `top` 이 내는 에러**

- ★ **아무 에러도 안 낸다.** 값은 유효하고 캐스케이드도 통과하는데 **레이아웃이 안 쓴다.**
- 화면·콘솔 어디에도 표시가 없다. CSS 가 에러가 없는 언어인 자리다.

### 2. `absolute` 는 어느 상자를 기준으로 재는가

**실행 결과** (Chrome 151 headless — `.anc` 는 margin 20 · border 10 · padding 30 · 콘텐츠 300×160)

```text
.anc 테두리 상자   x=20  y=20   380×240
.anc 패딩 상자     x=30  y=30   360×220
.anc 콘텐츠 상자   x=60  y=60   300×160

자식                            실측
absolute; top:0; left:0        x=30  y=30
absolute; top:50%; left:50%    x=210 y=140
보통 블록; width:50%           w=150
```

**`.kid` 의 `rect.x`·`rect.y`**

- **둘 다 30 이다.**

**어느 상자의 원점인가**

- **패딩 상자**다. 테두리 상자(20)도 콘텐츠 상자(60)도 아니다.
- 외울 문장 — **「테두리 안쪽, 패딩 바깥쪽」.**

**`left: 50%` 면**

- **x=210 이다.** 패딩 상자 왼쪽 30 + 폭 360 의 절반 180 = 210.

**보통 블록의 `width: 50%`**

- **150 이다.** 콘텐츠 상자 폭 300 의 절반.
- ★ **같은 `50%` 가 180 과 150 으로 갈린다.** 이것이 이 주제에서 가장 자주 틀리는 자리다.

> **패딩 상자(padding box)** — 콘텐츠 + 패딩, 테두리 안쪽까지의 칸. `clientWidth` 가 재는 칸이기도 하다([15번](../15-box-model-and-box-sizing/2-summary.md)).\
> 예: `border: 10px; padding: 30px` 인 상자의 패딩 상자는 테두리 바깥선에서 10px 안쪽부터 시작한다.

### 3. 위로 아무도 없으면

**실행 결과** (Chrome 151 headless)

```text
위치 지정 조상 없음 · absolute; top:20; left:30
   문서 좌표 (30, 20)
document.documentElement rect  780 × 374
window.innerWidth/Height        780 × 493
```

**어디에 붙는가 · 이름**

- **초기 포함 블록(initial containing block)** 이다.

**크기**

- **뷰포트와 같다.** 이 실행에서는 780×493 이었다(`documentElement` 의 `rect` 374 는 문서 내용 높이라 다르다 — **둘을 혼동하면 안 된다**).

**원점과 스크롤**

- 원점은 **문서 맨 위 왼쪽**이다. 그래서 **스크롤하면 같이 올라간다** — 화면에 붙어 있지 않다.

**`fixed` 였다면**

- 원점이 **뷰포트**가 되어 **스크롤해도 안 움직인다.**
- ★ 「크기는 같고 원점만 다르다」가 `absolute`(조상 없음)와 `fixed` 의 차이다.

### 4. `fixed` 가 화면에 안 붙는다

**실행 결과** (Chrome 151 headless — 래퍼는 `margin: 40px; border: 2px`, 자식은 `fixed; top:0; left:0`)

```text
래퍼의 선언                    래퍼 x,y        자식 x,y      벽
(없음)                        (40,  40)       (0,   0)    뷰포트
transform: translateX(0)      (40, 204)      (42, 206)    래퍼
filter: blur(0px)             (40, 368)      (42, 370)    래퍼
will-change: transform        (40, 532)      (42, 534)    래퍼
perspective: 500px            (40, 696)      (42, 698)    래퍼
contain: paint                (40, 860)      (42, 862)    래퍼
backdrop-filter: blur(2px)    (40,1024)      (42,1026)    래퍼
contain: layout               (40,1188)      (42,1190)    래퍼
opacity: 0.5                  (40,1352)       (0,   0)    뷰포트 ← 안 바뀐다
isolation: isolate            (40,1516)       (0,   0)    뷰포트 ← 안 바뀐다
overflow: hidden              (40,1680)       (0,   0)    뷰포트 ← 안 바뀐다
position: relative            (40,1844)       (0,   0)    뷰포트 ← 안 바뀐다
(transform 래퍼 + absolute)   (40,2008)      (42,2010)    래퍼
```

**화면 왼쪽 위에 붙는가**

- **안 붙는다.** 래퍼의 패딩 상자 원점인 **(42, 206)** 에 붙었다(래퍼 (40,204) + 테두리 2).

**항등값인데 왜 영향을 주는가**

- **값이 아니라 선언의 존재**가 판정 기준이기 때문이다. `translateX(0)` 도 변형이 걸린 상자로 취급된다.
- 브라우저가 그 상자를 **독립된 합성 단위**로 다루므로, 그 안의 `fixed` 가 밖의 뷰포트를 기준으로 삼을 수 없다.

**같은 효과를 내는 선언 다섯 개 이상**

- `transform` · `filter` · `backdrop-filter` · `will-change`(그 속성들) · `perspective` · `contain: paint` · `contain: layout` — **실측으로 확인한 일곱**이다.
- **안 바꾸는 것** — `opacity` · `isolation: isolate` · `overflow: hidden`(셋 다 실측 **(0,0)**).

**`opacity: 0.5` 는 포함되는가**

- ★ **안 된다.** 실측에서 자식이 **(0,0)** 에 그대로 있었다.
- 이것이 5번의 갈림길이다.

### 5. 두 목록은 같은가

**실행 결과** — 포함 블록은 `fixed` 자식의 좌표로, 쌓임 맥락은 **겹치는 지점의 스크린샷 픽셀**로 판정했다(쌓임 맥락 쪽 정본은 [22번](../22-stacking-context-and-z-index/2-summary.md)).

```text
선언                          fixed 자식     겹침 픽셀        포함블록 / 쌓임맥락
transform: translateZ(0)      래퍼 안        (0,0,255) 파랑      ✓   /   ✓
filter: blur(0px)             래퍼 안        (0,0,255) 파랑      ✓   /   ✓
will-change                   래퍼 안        (0,0,255) 파랑      ✓   /   ✓
contain: paint                래퍼 안        (0,0,255) 파랑      ✓   /   ✓
opacity: 0.99                 (0,0) 뷰포트   (0,0,255) 파랑      ✗   /   ✓
isolation: isolate            (해당 없음)    (0,0,255) 파랑      ✗   /   ✓
position:relative + z-index:1 (0,0) 뷰포트   (0,0,255) 파랑      ✗   /   ✓
position:relative (z 없음)    (0,0) 뷰포트   (255,0,0) 빨강      ✗   /   ✗
```

*(픽셀 읽는 법 — 겹치는 지점에서 파랑이면 「위에 있어야 할 자식이 갇혔다」 = 쌓임 맥락이 생긴 것, 빨강이면 「자식의 `z-index: 9999` 가 밖까지 통했다」 = 안 생긴 것.)*

**같은 목록인가**

- **아니다. 겹치지만 같지 않다.**

**`opacity: 0.99`**

- **쌓임 맥락은 만들고, 포함 블록은 안 바꾼다.**

**`position: relative; z-index: 1`**

- **쌓임 맥락은 만들고**, `absolute` 의 벽은 되지만 **`fixed` 의 벽은 안 된다.**

**같은 원인으로 진단해도 되는가**

- ★ **안 된다.** `transform` 자리에서는 원인이 같지만 **`opacity` 자리에서 갈린다.**
- 실무 증상으로 말하면 — **`opacity: 0.99` 를 준 부모 때문에 `z-index` 가 안 먹는 일은 있어도, 그것 때문에 `fixed` 가 안 붙는 일은 없다.**

### 6. `sticky` 가 안 붙는다

**실행 결과** (Chrome 151 headless — 바깥 스크롤러는 `overflow: auto`, `scrollTop = 200` 후 머리의 top)

```text
가운데 래퍼의 overflow   머리 top (스크롤러 기준)   결과
visible                        2.0                 붙는다
clip                           2.0                 붙는다
hidden                      -198.0                 안 붙는다
auto                        -198.0                 안 붙는다
```

**`visible` 일 때**

- **붙는다.** 머리가 스크롤러 위끝(테두리 2 안쪽)인 **2.0** 에 고정됐다.

**`hidden` 일 때**

- **안 붙는다.** **−198.0** — 내용과 함께 통째로 밀려 올라갔다.

**`clip` 일 때**

- ★ **붙는다. `hidden` 과 결과가 다르다.** 머리가 **2.0** 에 그대로 있었다.

**왜 갈리는가**

- **`sticky` 는 「가장 가까운 스크롤 컨테이너」에 걸리는데, `hidden`·`auto` 는 스크롤 컨테이너를 만들고 `clip` 은 안 만들기 때문이다.**
- 중간 래퍼가 스크롤 컨테이너가 되면 `sticky` 는 **그 래퍼**에 걸리려 하는데, 그 래퍼 자신은 스크롤되지 않으므로 걸릴 일이 영영 안 온다.
- 그래서 실전 처방이 「**`overflow: hidden` 을 `clip` 으로 바꿔 보라**」다. 정본은 [23번](../23-overflow-and-scroll-containers/2-summary.md).

### 7. `overflow: hidden` 은 스크롤 컨테이너인가

**실행 결과** (Chrome 151 headless — 240×120 상자, 내용 424 높이, `scrollTop = 200` 을 시도)

```text
overflow   실제 scrollTop   clientWidth   offsetWidth   스크롤바
auto            200             225           244        생긴다 (15px)
scroll          200             225           244        늘 있다 (15px)
hidden          200             240           244        없다
clip              0             240           244        없다
visible           0             240           244        없다
```

**`hidden` 에서 `scrollTop`**

- **200 이다.** 대입이 먹었다 — **스크롤 컨테이너가 맞다.**

**`clip` 이면**

- **0 이다.** 대입이 무시된다 — 스크롤 컨테이너가 아니다.

**`sticky` 와 어떻게 이어지나**

- 6번의 결과가 그대로 나온다 — **`hidden` 은 스크롤 컨테이너라 `sticky` 를 가로채고, `clip` 은 아니라 안 가로챈다.**
- 두 실험이 **같은 하나의 사실**을 다른 각도에서 잰 것이다.

**스크롤바는 보이는가**

- **안 보인다.** `clientWidth` 가 240 으로 `visible` 과 같았다(`auto` 는 225 로 15px 줄었다).
- ★ **「스크롤바가 없다」와 「스크롤이 안 된다」는 다른 말**이다. `hidden` 은 앞엣것이고 `clip` 이 뒤엣것이다.

### 8. `inset` 단축

**실행 결과** (Chrome 151 headless)

```text
position: relative; inset: 10px auto auto 40px
   원래 자리 (2,30)  →  실측 (42,40)
```

**`.a` 가 옮겨지는 방향과 크기**

- **오른쪽으로 40, 아래로 10.** `left: 40px; top: 10px` 과 같다.

**네 값의 순서**

- **`margin` 과 같다** — `top right bottom left`(시계 방향).

**`.b` 의 크기가 정해지는가**

- **정해진다.** `inset: 0` 이면 네 변이 전부 포함 블록의 변에 고정되므로 **폭·높이가 그 차이로 결정된다.**
- 오버레이의 표준 관용구가 `position: fixed; inset: 0` 인 이유다.

**`left` 와 `right` 를 둘 다 주면**

- `relative` 에서는 **한쪽이 무시된다** — 좌횡서(`ltr`)에서는 **`left` 가 이긴다.**
- `absolute` 에서는 무시가 아니라 **둘 다 쓰여 폭이 정해진다**(`width: auto` 일 때).

### 9. 잘림과 포함 블록

**실행 결과** (Chrome 151 headless — `.box` 는 `overflow: hidden`, 높이 60. 자식은 상자 아래로 삐져나오게 배치)

```text
자식        레이아웃상 상자 밖으로   상자 밖 지점의 스크린샷 픽셀
static             나간다              (255,255,255) 흰색 — 잘렸다
absolute           나간다              (255,255,255) 흰색 — 잘렸다
fixed              나간다              (252,165,165) 분홍 — 안 잘렸다
```

**`absolute` 자식은 잘리는가**

- **잘린다.** `.box` 자신이 `position: relative` 라 **그 자식의 벽이 `.box`** 이기 때문이다.
- (만약 `.box` 가 `static` 이고 더 위의 조상이 벽이라면 **안 잘린다.**)

**`fixed` 자식은**

- **안 잘린다.** 벽이 **뷰포트**라 `.box` 의 클리핑 사슬에 들어 있지 않다.

**포함 블록으로 설명하면**

- **잘림은 「포함 블록 사슬이 그 스크롤/클립 상자를 지나가느냐」를 따라간다.**
- `absolute` 의 사슬은 `.box` 를 지나가고, `fixed` 의 사슬은 `.box` 를 건너뛴다.

**`getBoundingClientRect()` 로 판정할 수 있는가**

- ★ **없다.** 세 자식 모두 레이아웃상으로는 상자 밖으로 나가 있었다 — **`rect` 만 보면 셋이 똑같다.**
- **잘림은 레이아웃이 아니라 페인트**다. 그래서 **스크린샷 픽셀**로 쟀다([17번](../17-block-formatting-context/2-summary.md)이 같은 교훈을 적어 두었다).

### 10. 다른 주제로 잇기

**`absolute` 와 `float` 의 차이**

- **`float` 는 행 상자를 민다. `absolute` 는 안 민다.**
- 실측 — 같은 크기 상자로 같은 컨테이너에서, float 쪽 행 상자는 **x=101 · 폭 197.1**(세 줄), absolute 쪽은 **x=1 · 폭 287.3**(두 줄)이었다([20번](../20-float-and-clear/2-summary.md)).
- 그래서 `absolute` 는 글자 위에 그냥 덮인다.

**`%` 가 풀리는 단계**

- **사용값(used value)** 단계다. 레이아웃이 돌아 포함 블록이 정해져야 `%` 를 풀 수 있다.
- 정본은 [04번 주제](../04-value-processing-stages/2-summary.md)다.

**`absolute` 는 BFC 를 여는가**

- **연다.** [17번 주제](../17-block-formatting-context/2-summary.md)의 실측 표에 있다(부모 높이 60 · float 감쌈 ✓).
- 다만 흐름에서 빠져 있어 **「마진이 샌다」는 상황 자체가 잘 안 생긴다.**

**「누가 위에 그려지나」의 정본**

- [22번 주제](../22-stacking-context-and-z-index/2-summary.md)(쌓임 맥락과 `z-index`)다.
- 이 문서는 **어디에 놓이나**까지이고, 그 다음이 거기다.

## 용어 풀이

- **포함 블록(containing block)** — `top`/`left`/`%` 를 재는 기준 사각형.
- **위치 지정 조상(positioned ancestor)** — `position` 이 `static` 이 아닌 조상. `absolute` 의 벽 후보.
- **초기 포함 블록(initial containing block)** — 위로 아무도 없을 때의 벽. **크기는 뷰포트, 원점은 문서 맨 위.**
- **패딩 상자(padding box)** — 테두리 안쪽까지의 칸. **`absolute` 가 기준으로 삼는 상자.**
- **뷰포트(viewport)** — 문서가 보이는 창. `fixed` 의 기본 벽.
- **스크롤포트(scrollport)** — 스크롤 컨테이너에서 실제로 보이는 칸. `sticky` 가 걸리는 기준.
- **`static`** — 기본값. `top`/`left`/`z-index` 를 **통째로 무시한다.**
- **`relative`** — 자리를 남기고 그려지는 위치만 옮긴다.
- **`absolute`** — 흐름에서 빠지고 가장 가까운 위치 지정 조상의 **패딩 상자**를 벽으로 쓴다.
- **`fixed`** — 뷰포트를 벽으로 쓴다. 단 `transform` 류 조상이 있으면 그 조상이 벽이 된다.
- **`sticky`** — 자리를 남긴 채 스크롤 컨테이너 안에서 걸린다.
- **`inset`** — `top`/`right`/`bottom`/`left` 단축. 순서는 `margin` 과 같다.
- **잘림(clipping)** — 넘친 부분이 그려지지 않는 것. **레이아웃이 아니라 페인트**라 `rect` 로는 안 보인다.

## 실행 검증

| 무엇을 | 어떻게 | 결과 |
|---|---|---|
| 다섯 값의 자리·높이 | Chrome 151 headless · 형제 셋의 좌표와 컨테이너 높이 | `relative` 88 / `absolute` **60** · `static` 은 선언이 무시됨 |
| `absolute` 의 기준 상자 | margin20·border10·padding30 조상에 `top:0;left:0` | **(30,30)** = 패딩 상자 |
| 두 `50%` | 같은 조상에서 `absolute left:50%` 대 보통 블록 `width:50%` | **210(=+180) 대 150** |
| 초기 포함 블록 | 위치 지정 조상 없이 `absolute; top:20;left:30` | 문서 좌표 **(30,20)** · 뷰포트 780×493 |
| `fixed` 의 벽을 바꾸는 선언 | 래퍼 선언 8가지 × `fixed` 자식의 좌표 | transform·filter·will-change·perspective·contain:paint·backdrop-filter **바꿈** / **opacity 는 안 바꿈** |
| 포함 블록 대 쌓임 맥락 | 같은 선언에 좌표 + 겹침 픽셀 두 실험 | **겹치지만 같지 않음**(`opacity` 에서 갈림) |
| `sticky` 죽이기 | 중간 래퍼의 `overflow` 4값 × `scrollTop=200` | `hidden`·`auto` **−198** / `visible`·`clip` **2.0** |
| 스크롤 컨테이너 판정 | `scrollTop=200` 대입 후 실제 값 | `hidden` **200**(되는데 스크롤바 없음) / `clip` **0** |
| `inset` 단축 | `inset: 10px auto auto 40px` 인 `relative` | (2,30) → **(42,40)** |
| 잘림 | 같은 `overflow:hidden` 상자 안의 static/absolute/fixed | rect 는 셋 다 「밖으로 나감」 · **픽셀은 흰/흰/분홍** |
| demo 4개 | 완성 문서에서 `extract-demo-blocks.py --render` 로 재추출·재실행 + 스크린샷 픽셀 | 「보이는 것」 4건 모두 일치 |

**구현 의존 항목** — **초기 포함 블록 780×493 은 이 실행의 창 크기**다. **스크롤바 15px 은 이 플랫폼의 값**이다([23번](../23-overflow-and-scroll-containers/2-summary.md)).\
★ **「`fixed` 의 벽을 바꾸는 선언 목록」은 계속 늘어 왔다** — `will-change`·`contain: paint`·`backdrop-filter` 는 나중에 들어온 것이라 오래된 글과 다르다. 이 표는 **이 브라우저에서 실제로 재 본 것**이고, 브라우저가 바뀌면 다시 찍어야 한다.\
**엔진은 Chrome 하나다.** Firefox 155.0.1 은 이 환경에서 headless 스크린샷이 산출되지 않고 WebKit 은 이 머신에 없다 — **「두 엔진에서 확인했다」고 적지 않았다.**

# css/syntax/46 — 테두리·`border-radius`·`outline`·`box-shadow` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [CSS Backgrounds and Borders Level 3](https://drafts.csswg.org/css-backgrounds-3/) (`border-*`·`border-radius`·`box-shadow` 의 정본) · [CSS Basic User Interface Level 4](https://drafts.csswg.org/css-ui-4/#outline) (`outline`·`outline-offset`). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 `demo` 블록 **3개 전부**와 본문의 모든 수치를 **Google Chrome 151.0.7922.173** headless 에서 실제로 렌더해 확인했다.\
> 치수는 `getBoundingClientRect()`·`getComputedStyle()` 로, **모양은 스크린샷 PNG 를 파이썬 표준 라이브러리로 디코드해 좌표별 `(r,g,b)` 를 읽어서** 잰다.\
> ★ **이 주제는 계산값으로 거의 아무것도 증명하지 못한다** — `border-radius: 150px` 은 계산값이 `150px` 인데 **화면에 그려진 반지름은 100px** 이다(아래 (4)). 그래서 픽셀이 주 근거다.
> **버전** — CSS 에 언어 버전이 없으므로 Baseline 으로 읽는다. webstatus.dev 조회(2026-09-23): `border-radius`·`box-shadow` **widely**(2015-07-29 → 2018-01-29) · `outline`(CSS UI 4 §outline) **widely**(2023-03-27 → 2025-09-27).
> **여기서 다루지 않는 것** — 이 네 가지가 어느 상자 위에 그려지는지, 곧 **네 겹 상자 자체**는 [15번](../15-box-model-and-box-sizing/2-summary.md)이 정본이다. 여기는 「그 네 겹 중 `border` 겹에 무엇을 그리고, 상자 **밖에** 무엇을 더 그리는가」부터다.\
> 색 표기(`oklch`·알파)는 [목록의 **42번 주제**](../42-color-notation-and-spaces/), 그라디언트는 **45번 주제**, 배경 속성은 **44번 주제**, **임의의 모양으로 자르는 것**은 [49번](../49-clip-path-and-mask/2-summary.md)이 정본이다. `filter: drop-shadow` 와 `box-shadow` 의 차이는 [47번](../47-filter-and-backdrop-filter/2-summary.md)에 있다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 수치는 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**액자 가게에 갔다고 하자. 붙일 수 있는 장식이 네 가지다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 나무 액자틀 — 두께만큼 액자가 커진다 | **`border`** — 상자 치수에 **더해진다** |
| 액자틀의 둥근 모서리 — 그림도 같이 잘린다 | **`border-radius`** — 상자 모양 자체를 깎는다 |
| 액자 바깥에 띄워 붙인 형광 띠 — 벽 치수는 그대로 | **`outline`** — 레이아웃 공간을 **0** 차지한다 |
| 액자 뒤에 깔린 그림자 — 역시 벽 치수는 그대로 | **`box-shadow`** — 공간을 **0** 차지한다 |

- 액자틀은 **두께를 말해도 「무슨 나무」를 안 정하면 아예 안 붙는다.** 이것이 `border-style` 의 기본값 `none` 이다.
- 형광 띠와 그림자는 **벽에 걸었을 때 옆 액자를 밀어내지 않는다.** 겹쳐서 가릴 뿐이다.

```text
  같은 90px 짜리 상자에 8px 을 붙였을 때, 이웃이 어디로 밀리나

  border 8px                      outline 8px
  +--------+                      +--------+
  |########|<- 이웃 x = 122       :########:<- 이웃 x = 106
  +--------+                      +--------+
   자기 폭 106                      자기 폭 90
   → 8px 이 치수에 들어갔다           → 8px 이 치수 밖이다. 이웃 위로 겹친다
```

*(Chrome 151 headless 실측 — 같은 90px 상자의 오른쪽 이웃 `x`: `border` 쪽 122, `outline` 쪽 106.)*

실무에서 이게 터지는 자리는 **포커스 링**이다.\
`:focus` 에 `border` 를 주면 포커스가 옮겨갈 때마다 **레이아웃이 8px 씩 들썩이고**, `outline` 을 주면 안 들썩인다.

> **레이아웃 공간(layout space)** — 그 요소가 형제들을 밀어내는 데 쓰는 자리.\
> 예: `border` 를 키우면 옆 상자가 오른쪽으로 밀리지만, `outline` 을 키우면 옆 상자가 가만히 있는다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 네 질문을 둔다.

1. `border-width: 8px` 를 썼는데 **아무것도 안 보인다.** 무엇이 빠졌고, 그때 상자 치수는 어떻게 되는가.
2. `border-radius` 로 선언한 숫자가 **실제로 그려지는 반지름과 다를 때**가 있다. 언제, 얼마로 바뀌는가.
3. `outline` 과 `box-shadow` 는 **왜 레이아웃을 안 건드리는가**, 그리고 그 대가는 무엇인가.
4. 그림자를 여러 개 쓰면 **누가 위에 오는가**, 그리고 `spread` 는 무엇을 하는가.

## 동작 방식

### (1) `border` 는 삼단이다 — `width`·`style`·`color`

**언제 쓰나** — 테두리를 하나라도 그릴 때마다. 세 축 중 하나라도 빠지면 결과가 갈린다.

```text
  border 라는 이름의 속성은 사실 세 개다

  border-width  8px        얼마나 두껍나
  border-style  solid      어떤 선인가      <- 기본값 none
  border-color  #dc2626    무슨 색인가      <- 기본값 currentColor
       │
       └─ 셋 중 style 이 none 이면
          width 가 얼마든 사용값이 0 이 된다
```

```text
  선언                                   계산된 border-width   상자 rect
  border-width:8px; border-color:red     0px                  232 x 32
  같은 것 + border-style:solid           8px                  248 x 48
```

그림 해설 (한 단계씩):

- `border-style` 의 **초깃값은 `none`** 이다. 두께와 색만 쓰면 **그릴 선이 없다.**
- 그리고 그때 **계산된 `border-width` 자체가 `0px` 로 내려간다.** 「안 보이는 8px 가 자리를 차지하는」 상태가 아니다.
- 그래서 나중에 `border-style: solid` 한 줄을 넣는 순간 **상자가 16px 커지며 레이아웃이 밀린다.**

```html demo
<div class="no">border-width 만</div>
<div class="yes">width + style</div>
<style>
  div { width: 220px; padding: 6px; margin: 8px; background: #e0e7ff; font: 14px system-ui; }
  .no  { border-width: 8px; border-color: #dc2626; }          /* style 없음 */
  .yes { border-width: 8px; border-color: #dc2626; border-style: solid; }
</style>
```

> **보이는 것** — 위 상자에는 **테두리가 하나도 안 보이고**, 아래 상자에만 빨간 8px 테두리가 보인다.\
> 두 상자의 선언은 `border-style` 한 줄만 다른데, 위 상자는 **크기까지 작다**(아래 상자가 사방 8px 씩 크다).\
> **실측** — *(Chrome 151 headless: 위 상자 `borderTopWidth` 계산값 `0px`·`rect` 232×32 / 아래 상자 `8px`·`rect` 248×48.)*\
> **바꿔 볼 것** — `.no` 에 `border-style: dashed` 추가(점선으로 나타나며 상자가 커진다) · `.yes` 의 `solid` → `hidden`(다시 위 상자와 같아진다)

비용 — 없다. 다만 **`border` 단축을 쓰면 세 축이 한 번에 들어가서** 이 함정이 안 보인다. 함정은 `border-width` 를 따로 쓸 때만 생긴다.

### (2) `border-style: hidden` 은 `none` 과 다른 이름의 같은 결과처럼 보인다

**언제 쓰나** — 표(`table`)에서 테두리 충돌을 해소할 때. 그 밖에서는 `none` 과 구분이 안 된다.

```text
  border-style     계산된 border-width   rect
  none             0px                  100 x 40
  hidden           0px                  100 x 40      <- 여기서는 결과가 같다
  solid            10px                 120 x 60
```

- 둘 다 **선을 안 그리고 폭을 0 으로 만든다.** 일반 상자에서는 구분할 방법이 없다.
- 갈리는 곳은 `border-collapse: collapse` 인 표 하나뿐이다 — 거기서 `hidden` 은 **이웃 칸의 테두리까지 이긴다.** 표 모델은 이 주제 밖이다.

*(Chrome 151 headless 실측 — 위 표는 같은 문서에서 네 상자를 나란히 두고 잰 값이다.)*

### (3) `border-radius` 는 「그리는 모양」이 아니라 「상자 모양」을 깎는다

**언제 쓰나** — 모서리를 둥글리고 싶을 때. 그런데 이것이 **배경까지 자른다**는 점이 요점이다.

```text
  전 (border-radius 없음)              후 (border-radius: 60px)

  (0,0)                               (0,0)
   +----------------+                   ,-'''----------`.
   |################|                 ,'################`.
   |################|                 |##################|
   |################|                 `.################,'
   +----------------+                   `.___________,-'

   모서리 픽셀 = 상자 배경색           모서리 픽셀 = 페이지 배경색
```

그림 해설:

- **모서리 바깥은 「상자가 투명해진」 것이 아니라 「상자가 없는」 것**이다. 그 자리에는 **뒤에 있던 것**이 그대로 나온다.
- 곧 `border-radius` 는 이미 **모양을 자르는 도구**다. [49번](../49-clip-path-and-mask/2-summary.md)의 `clip-path` 는 이것을 임의의 도형으로 일반화한 것이다.

*(Chrome 151 headless 실측 — 흰 페이지 위 `#cc0000` 200×200 상자에 `border-radius: 60px` 를 주고 모서리 픽셀 `(0,0)` 을 읽으니 `(255,255,255)` — 상자색 `(204,0,0)` 이 아니라 **페이지 배경색**이었다.)*

비용 — 모서리에 **안티앨리어싱 픽셀**이 생긴다. 곡선 경계에서 상자색과 배경색이 섞인 중간값이 나오므로, 픽셀 하나로 판정할 때는 그 사실을 알고 읽어야 한다.

### (4) 반지름 합이 변보다 크면 **전부 같은 비율로 줄어든다**

**언제 쓰나** — `border-radius: 50%` 나 큰 값을 줬을 때. **선언값과 실제 반지름이 갈리는 유일한 자리**다.

```text
  200 x 200 상자에 border-radius: 150px

  위 변에서:  TL 150 + TR 150 = 300  >  200
                            ↓
       f = 변 길이 / 반지름 합 = 200 / 300 = 0.666…
                            ↓
       네 모서리 전부 150 x 0.666… = 100 으로 축소

  getComputedStyle().borderRadius = "150px"   <- 선언값 그대로
  실제로 그려진 반지름            =  100       <- 픽셀이 말해 준다
```

그림 해설 (한 단계씩):

- 축소 비율 `f` 는 **네 변 전부를 보고 가장 작은 것**을 고른다. 한 변만 넘쳐도 **모든 모서리**가 같이 줄어든다.
- **계산값 API 는 이 축소를 반영하지 않는다.** `getComputedStyle` 만 보면 150px 로 보인다.
- 그래서 「진단 3창」의 세 번째 창(`getComputedStyle`)조차 여기서는 **거짓 안심**을 준다. 픽셀을 읽어야 한다.

**픽셀로 잰 근거** — 200×200 상자 셋에 각각 `150px` / `120px` / `100px` 을 주고 렌더해 같은 좌표들을 비교했다.

```text
  선언     45도 대각선에서 첫 불투명 픽셀 d   100px 판과 다른 픽셀 수(40,000 중)
  150px    30                               2      (최대 채널 차 8)
  120px    30                               279    (최대 채널 차 56 — 전부 곡선 경계)
  100px    30                               기준
```

- 세 판 모두 `d = 30` 이다. 반지름 `r` 인 원의 대각선 진입점은 `r - r/√2` 이고 `r = 100` 이면 29.3 이다.
- 차이 픽셀은 전부 **곡선 경계 한 줄**이고 안쪽·바깥쪽은 한 픽셀도 다르지 않았다 — 안티앨리어싱 반올림이다.
- 곧 **150 도 120 도 화면에서는 100 이다.**

비용 — 없다. 다만 **`border-radius` 로 「정확히 이 반지름」을 보장받을 수 없다**는 것을 알아야 한다.

### (5) `/` 는 두 반지름을 가른다 — 앞이 가로, 뒤가 세로

**언제 쓰나** — 모서리를 원이 아니라 **타원**으로 깎을 때.

```text
  border-radius: 60px / 20px       가로 반지름 60, 세로 반지름 20

        x=0   ...        x=59
   y=0   .  .  .  .  .  .  #####      위 변은 x=59 까지 비어 있다
   y=10  .  .  #############
   y=20  ##################          왼 변은 y=20 부터 차 있다
```

```text
  선언            위 변(y=0) 첫 불투명 x    왼 변(x=0) 첫 불투명 y
  60px            59                      60        <- 원
  60px / 20px     59                      20        <- 가로로 눕힌 타원
  20px / 60px     20                      60        <- 세로로 세운 타원
```

- **`/` 앞은 가로 반지름, 뒤는 세로 반지름**이다. 값이 하나면 둘이 같다(=원).
- 각 자리에 네 값(`TL TR BR BL`)까지 쓸 수 있어 최대 여덟 숫자가 된다.

*(Chrome 151 headless 실측 — 200×200 `#cc0000` 상자 셋을 나란히 두고 첫 불투명 픽셀 좌표를 읽은 값이다.)*

### (6) `outline` — 자리를 안 차지하고, 모서리를 따라 돈다

**언제 쓰나** — 포커스 링처럼 **레이아웃을 흔들면 안 되는 표시**를 그릴 때.

```html demo
<p class="row"><b class="brd">border</b><b>이웃</b></p>
<p class="row"><b class="out">outline</b><b>이웃</b></p>
<style>
  .row { margin: 24px 16px; font: 0/0 a; }
  b { display: inline-block; width: 90px; height: 34px; background: #e0e7ff;
      font: 12px/34px system-ui; text-align: center; vertical-align: top; }
  .brd { border: 8px solid #dc2626; }
  .out { outline: 8px solid #16a34a; }
</style>
```

> **보이는 것** — 위 줄은 빨간 8px 테두리가 상자를 키워 「이웃」이 오른쪽으로 밀려 있다.\
> 아래 줄은 초록 8px 테가 상자 **바깥에** 그려지는데 「이웃」이 밀리지 않아, 테가 이웃 상자 밑으로 들어간다.\
> **실측** — *(Chrome 151 headless: 위 줄 상자 폭 106·이웃 `x` 122 / 아래 줄 상자 폭 **90**·이웃 `x` **106**. 초록 테는 상자 위쪽 바깥 `y=90` 에서 `(22,163,74)` 로 읽혔다 — 상자 밖에 그려졌다.)*\
> **바꿔 볼 것** — `outline: 8px` → `outline: 8px solid #16a34a; outline-offset: 12px`(테가 더 바깥으로 물러난다) · `.out` 의 `outline` → `border`(두 줄이 같아진다)

```text
  outline 이 자리를 안 차지한다는 것의 그림

           이웃이 여기부터 (x=106)
                 │
   [ 상자 90px ] │
  ##[##########]##        ## = outline 8px  → 이웃 밑에 깔린다
  ↑            ↑
  x=-8       x=90(상자 끝)

  rect.width 는 90 이고, 이웃의 x 도 106 이다 — outline 은 어느 쪽에도 안 들어갔다
```

**`outline` 은 `border-radius` 를 따라 돈다** — 이건 던져서 확인해야 하는 항목이다.

```text
  border-radius: 50px 인 100x100 원에 outline: 6px

  상자 모서리 (0,0) 픽셀      -> (255,255,255)  = 페이지 배경. 테가 각지지 않았다
  왼쪽 한가운데 바깥 (-4, 50) -> (22,163,74)    = 초록 테
  대각선으로 d=10 지점        -> 초록 테        = 고리 모양으로 돈다

  같은 것을 border-radius: 0 으로 하면
  모서리 바깥 (-3,-3)         -> (22,163,74)    = 각진 테
```

- 곧 Chrome 151 에서 `outline` 은 **둥근 상자에는 둥근 고리로** 그려진다. 예전 브라우저는 각진 사각형으로 그렸다.
- Baseline 조회에서 `outline`(CSS UI 4 §outline) 항목은 **Chrome 94(2021-09-21)·Firefox 88(2021-04-19)·Safari 16.4(2023-03-27)** 로 갈린다. **이 항목이 정확히 무엇을 세는지는 API 가 말해 주지 않으므로** 「둥근 `outline` 이 그때 들어왔다」고 단정하지 않는다 — 확인한 것은 **Chrome 151 에서 지금 둥글게 돈다**는 실측뿐이다.

### (7) `outline-offset` — 테를 안팎으로 옮긴다

**언제 쓰나** — 테가 상자에 딱 붙어 답답할 때, 또는 안쪽에 그리고 싶을 때.

```text
  outline: 6px solid green; outline-offset: 12px

   ┌────────────── 초록 테 (6px)
   │  ┌─────────── 빈 자리 (offset 12px)
   │  │  ┌──────── 상자 (border box)
   x=185  x=192   x=200

   실측:  (185,·) = (22,163,74) 초록
          (192,·) = (255,255,255) 흰 빈 자리
```

- 양수면 바깥으로, 음수면 안쪽으로 파고든다.
- **offset 도 레이아웃 공간을 안 차지한다.** 바깥으로 아무리 밀어도 이웃은 안 밀린다.

### (8) `box-shadow` — 다섯 값, 그리고 `inset`

**언제 쓰나** — 떠 있는 느낌, 테두리 대체, 포커스 링의 대안.

```text
  box-shadow: <offset-x> <offset-y> <blur> <spread> <color>
              그림자를    아래로     흐리기  사방으로   무슨 색
              오른쪽으로             반경    부풀리기

  box-shadow: inset 0 0 0 15px #f59e0b
              └ 이 낱말 하나로 「상자 안쪽」에 그린다
```

```text
  spread 만 준 두 그림자 (offset·blur = 0)

  0 0 0 15px            inset 0 0 0 15px
  ┌───────────────┐      ┌───────────────┐
  │▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒│      │███████████████│
  │▒▒┌─────────┐▒▒│      │██┌─────────┐██│
  │▒▒│ 상자    │▒▒│      │██│ 상자    │██│   ▒ = 상자 바깥 15px
  │▒▒└─────────┘▒▒│      │██└─────────┘██│   █ = 상자 안쪽 15px
  └───────────────┘      └───────────────┘
```

- `spread` 는 **그림자 모양을 사방으로 `N` px 부풀린다.** 흐리지 않고 통째로 키운다.
- 그래서 `0 0 0 Npx` 는 **`border` 처럼 보이지만 자리를 안 차지하는 선**이 된다. 포커스 링의 실무 관용구다.
- `inset` 은 같은 계산을 **안쪽 방향**으로 한다.

*(Chrome 151 headless 실측 — `0 0 0 15px #f59e0b` 인 상자(왼쪽 끝 x=450): `x=445` 는 `(245,158,11)` 주황, `x=434` 는 `(255,255,255)` 흰색. `inset` 판(왼쪽 끝 x=650): `x=658` 주황, `x=680` 은 상자색, `x=645` 는 흰색 — 바깥에 아무것도 없다.)*

### (9) 그림자도 자리를 안 차지한다 — `outline` 과 같은 성질

```text
  같은 90px 상자에 box-shadow: 0 0 0 10px

  자기 rect.width = 80   이웃 x = 80
                          ↑
             10px 그림자가 어디에도 안 들어갔다
```

- 실측에서 `outline` 과 **한 픽셀도 다르지 않았다.** 둘 다 「그리기만 하고 재지 않는」 것이다.
- 대가도 같다 — **이웃이 위로 덮는다.** 나중에 그려지는 형제의 배경이 그림자를 가린다.

*(Chrome 151 headless 실측 — 같은 문서에서 `border:10px` 행의 이웃 `x` 는 100, `outline:10px` 행과 `box-shadow:0 0 0 10px` 행의 이웃 `x` 는 **둘 다 80**이었다. 그리고 그림자·테가 이웃과 겹치는 `x=85` 지점의 픽셀은 **이웃의 배경색**이었다.)*

### (10) 그림자가 여럿이면 **먼저 쓴 것이 위**

**언제 쓰나** — 이중 링·다층 그림자를 만들 때. 순서를 뒤집으면 결과가 통째로 달라진다.

```html demo
<div class="a">빨강 먼저</div>
<div class="b">파랑 먼저</div>
<style>
  div { width: 120px; height: 50px; margin: 40px; background: #111827;
        font: 12px/50px system-ui; color: #fff; text-align: center; }
  .a { box-shadow: 0 0 0 30px #ef4444, 0 0 0 15px #3b82f6; }
  .b { box-shadow: 0 0 0 15px #3b82f6, 0 0 0 30px #ef4444; }
</style>
```

> **보이는 것** — 위 상자는 **빨간 띠 하나**만 30px 두께로 보인다(파란 띠가 완전히 가려진다).\
> 아래 상자는 **안쪽 15px 파랑 + 바깥 15px 빨강**, 두 겹 띠로 보인다. 선언한 값은 두 줄이 똑같고 순서만 다르다.\
> **실측** — *(Chrome 151 headless: 상자 왼쪽 8px 바깥 지점이 위 상자 `(239,68,68)` 빨강 · 아래 상자 `(59,130,246)` 파랑. 20px 바깥 지점은 둘 다 `(239,68,68)` 빨강.)*\
> **바꿔 볼 것** — `.b` 의 `15px` → `28px`(파란 띠가 두꺼워져 빨강이 2px 만 남는다) · `0 0 0 30px` → `0 0 10px 30px`(가장자리가 흐려진다)

```text
  목록의 앞쪽이 위 — 페인트 순서가 「뒤에서 앞으로」가 아니라 「앞이 위」다

  box-shadow: A, B, C
              ↑        A 가 맨 위
                 ↑     B 가 그 아래
                    ↑  C 가 맨 아래

  그래서 큰 그림자를 앞에 쓰면 뒤엣것이 통째로 안 보인다
```

비용 — 없다. 다만 **직관과 반대**라서 자주 틀린다. `z-index` 처럼 「큰 게 위」가 아니라 「**먼저 쓴 게 위**」다.

## 문법 — 형태와 어디서 헷갈리나

### 최소 형태

```css
/* border — 삼단. 단축은 순서 자유 */
.a { border: 8px solid #dc2626; }
.b { border-width: 8px; border-style: solid; border-color: #dc2626; }
.c { border-bottom: 2px dashed currentColor; }     /* 한 변만 */

/* border-radius — 최대 8숫자. / 앞이 가로, 뒤가 세로 */
.d { border-radius: 12px; }                        /* 네 모서리 원 */
.e { border-radius: 12px 0 12px 0; }               /* TL TR BR BL */
.f { border-radius: 60px / 20px; }                 /* 가로 60, 세로 20 */
.g { border-radius: 50%; }                         /* 변 길이의 50% — 타원/원 */

/* outline — border 와 같은 삼단 + offset */
.h { outline: 2px solid #2563eb; outline-offset: 3px; }

/* box-shadow — [inset] x y blur spread color, 쉼표로 여러 개 */
.i { box-shadow: 0 2px 6px rgb(0 0 0 / .2); }
.j { box-shadow: 0 0 0 3px #93c5fd, 0 0 0 5px #2563eb; }
.k { box-shadow: inset 0 1px 0 #fff; }
```

### 헷갈리는 자리 — 「몇 개까지 쓸 수 있나」

| 쓴 값 개수 | `box-shadow` 가 읽는 방식 |
|---|---|
| 2개 (`10px 10px`) | `offset-x offset-y`. 색은 `currentColor` |
| 3개 (`10px 10px 4px`) | + `blur` |
| 4개 (`10px 10px 4px 6px`) | + `spread` |
| 1개 (`10px`) | **무효 — 통째로 버려진다** |

- **길이 값은 반드시 둘 이상**이어야 한다. `offset-x` 만 쓴 선언은 파싱 단계에서 사라진다.
- 색은 아무 자리에나 쓸 수 있지만, **`inset` 은 값 묶음의 맨 앞이나 맨 뒤**여야 한다.

### 금지에 가까운 형태 — 조용히 버려지는 것들

```css
.x {
  border-radius: 50;          /* 단위 없음 — 버려진다 */
  box-shadow: 10px #f00;      /* 길이가 하나 — 버려진다 */
  outline: 10px groove blue;  /* 유효 */
  border: 10px dashed red;    /* 유효 */
}
```

★ **CSS 는 에러가 없는 언어다.** 위 규칙을 Chrome 151 에 던지고 「진단 3창」으로 물었다.

```text
  창 1  cssRules  → .x { outline: blue groove 10px; border: 10px dashed red; }
                    ★ border-radius 와 box-shadow 는 아예 담기지도 않았다
  창 2  querySelectorAll('.x').length → 1     선택자는 잡혔다
  창 3  getComputedStyle → border-radius: 0px · box-shadow: none

  즉 「규칙은 살고 선언 두 줄만 죽었다」. 콘솔에도 화면에도 아무 신호가 없다.
```

*(Chrome 151 headless 실측 — 위 세 줄은 실제 출력이다. 같은 문서의 `.y { border-radius: 50%; box-shadow: 10px 10px #f00 }` 는 `cssRules` 에 둘 다 남았다.)*

## 구현 세부사항 대 언어 보장

| 항목 | 누가 보장하나 |
|---|---|
| `border-style` 의 초깃값이 `none` 이고 그때 `border-width` 사용값이 `0` | **명세**(css-backgrounds-3 §4.2 — `border-style: none` 이면 계산된 `border-width` 가 0) |
| `outline` 이 레이아웃 공간을 차지하지 않는 것 | **명세**(css-ui-4 §outline — "outlines do not take up space") |
| `box-shadow` 가 레이아웃 공간을 차지하지 않는 것 | **명세**(css-backgrounds-3 §7 — 그림자는 오버플로를 만들지도, 스크롤 영역에 들어가지도 않는다) |
| 여러 그림자 중 **먼저 쓴 것이 위** | **명세**(css-backgrounds-3 §7 — 목록 앞쪽이 앞에 그려진다) |
| 반지름 합이 변보다 클 때 **비례 축소** | **명세**(css-backgrounds-3 §5.5 — `f` 를 구해 모든 반지름에 곱한다) |
| `getComputedStyle().borderRadius` 가 **축소 전 값**을 돌려주는 것 | ★ **Chrome 151 에서 관찰한 것.** 계산값 단계와 사용값 단계가 갈리는 자리이고, 명세가 시리얼라이즈 결과를 못 박은 것은 아니다 |
| `outline` 이 `border-radius` 를 따라 **둥글게** 도는 것 | ★ **Chrome 151 에서 관찰한 것.** css-ui-4 는 모서리 모양을 UA 재량으로 남겨 둔 표현을 쓴다 — 엔진마다 다를 수 있다 |
| 곡선 경계의 **정확한 픽셀 값** | ★ **보장 아님.** 이 문서의 픽셀은 `--disable-gpu` 소프트웨어 렌더링 결과다. GPU 합성에서는 안티앨리어싱이 미세하게 다를 수 있다 — **경계의 중간색 하나로 판정하지 말고 띠의 폭·불투명 지점으로 읽어라** |

★ **엔진은 Chrome 하나다.** Firefox 155.0.1 은 이 환경에서 headless 스크린샷이 산출되지 않고 WebKit 은 이 머신에 없다. 크로스 브라우저 차이는 **Baseline 데이터로만** 접지했다.

## 어디서 틀리나

### 1. `border-width` 만 쓰고 안 보인다고 한다

```text
  .btn { border-width: 2px; border-color: #2563eb; }   /* 아무 일도 안 일어난다 */
```

- `border-style` 이 없다. 게다가 **폭까지 0** 이라 나중에 `solid` 를 넣으면 레이아웃이 밀린다.
- 단축 `border: 2px solid #2563eb` 를 쓰면 이 함정을 안 밟는다.

### 2. `border-radius` 가 자식까지 자를 거라고 생각한다

```text
  부모에 border-radius: 60px, 자식은 네모난 배경

  overflow 기본              overflow: hidden
  모서리 픽셀 = 자식의 빨강     모서리 픽셀 = 페이지 배경
  (220,38,38)                (255,255,255)
```

- **`border-radius` 는 자기 배경·테두리만 자른다.** 자손은 그대로 삐져나온다.
- 자손까지 자르려면 `overflow: hidden`(또는 [49번](../49-clip-path-and-mask/2-summary.md)의 `clip-path`)이 필요하다.

*(Chrome 151 headless 실측 — 위 두 픽셀은 같은 문서의 두 상자에서 읽은 값이다.)*

### 3. 「큰 그림자를 먼저 쓰면 위에 온다」를 모른다

- `box-shadow: 0 0 0 30px red, 0 0 0 15px blue` 는 **파란 띠가 아예 안 보인다.**
- 이중 링을 만들려면 **작은 것을 먼저** 쓴다.

### 4. `outline` 이 이웃을 밀어낼 거라고 믿고 여백을 안 준다

- 밀어내지 않으므로 **이웃 위로 겹치고, 나중에 그려지는 이웃이 테를 덮는다.**
- 실측에서 이웃과 겹친 자리의 픽셀은 테 색이 아니라 **이웃의 배경색**이었다.
- 고치는 법은 `outline` 폭만큼 `margin` 을 주거나, 겹쳐도 되는 자리에만 쓰는 것이다.

### 5. `border-radius: 50%` 를 「정확히 절반」으로 믿는다

- 비례 축소 규칙 때문에 **선언값과 실제 반지름이 갈린다.** `50%` 는 마침 축소가 안 걸리는 경계값이라 괜찮지만, `60%` 를 쓰면 조용히 `50%` 처럼 그려진다.
- 계산값 API 는 이 축소를 **안 보여 준다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 포커스 표시 | `outline` (또는 `box-shadow: 0 0 0 Npx`) | 레이아웃이 안 흔들린다 |
| 칸을 구분하는 선 | `border` | 자리를 차지해야 내용이 안 붙는다 |
| 떠 있는 느낌(카드·드롭다운) | `box-shadow` (`blur` 있음) | 자리를 안 차지하고 겹쳐 보인다 |
| 「테두리 같은데 밀리면 안 되는 선」 | `box-shadow: 0 0 0 Npx` | `spread` 가 `border` 두께 역할을 한다 |
| 아이콘·투명 PNG 의 그림자 | **`filter: drop-shadow`** ([47번](../47-filter-and-backdrop-filter/2-summary.md)) | `box-shadow` 는 네모난 상자를 따라간다 |
| 임의의 모양으로 자르기 | **`clip-path`** ([49번](../49-clip-path-and-mask/2-summary.md)) | `border-radius` 는 모서리 넷뿐이다 |

**안 쓰는 쪽** — `outline` 을 `outline: none` 으로 지우고 대체를 안 두면 **키보드 사용자가 자기가 어디 있는지 모르게 된다.** 지울 거면 반드시 다른 표시로 바꾼다.

## 핵심 문장

- `border` 는 **삼단**이고 `style` 이 없으면 폭까지 0 이 된다 — 안 보이는 게 아니라 **없는** 것이다.
- `border-radius` 는 그림이 아니라 **상자 모양**이다. 모서리 밖은 뒤에 있던 것이 나온다.
- 반지름 합이 변보다 크면 **네 모서리가 같은 비율로 줄고**, 계산값 API 는 그 사실을 말해 주지 않는다.
- `outline` 과 `box-shadow` 는 **그리기만 하고 재지 않는다** — 레이아웃 공간 0, 대신 이웃이 덮는다.
- 그림자가 여럿이면 **먼저 쓴 것이 위**다.

## 관련 자료

- [15번 — 박스 모델과 `box-sizing`](../15-box-model-and-box-sizing/2-summary.md) — **그쪽은 네 겹 상자의 치수가 정해지는 규칙까지, 여기는 그 `border` 겹에 무엇을 그리고 상자 밖에 무엇을 더 그리는지부터.**
- [47번 — `filter` 와 `backdrop-filter`](../47-filter-and-backdrop-filter/2-summary.md) — **그쪽은 `drop-shadow` 가 알파 모양을 따라가는 것까지, 여기는 `box-shadow` 가 상자 모양을 따라가는 것까지.**
- [49번 — `clip-path` 와 `mask`](../49-clip-path-and-mask/2-summary.md) — **그쪽은 임의의 도형으로 자르는 것, 여기는 모서리 넷을 깎는 것까지.**
- [04번 — 값 처리 단계](../04-value-processing-stages/2-summary.md) — **계산값과 사용값이 갈리는 이유의 정본.** 반지름 비례 축소는 사용값 단계에서 일어난다.
- 색 표기(`oklch`·알파)는 [목록의 **42번 주제**](../42-color-notation-and-spaces/), 그라디언트는 **45번 주제**, 배경 속성은 **44번 주제**, 쌓임 맥락은 **22번 주제**가 정본이다.
- [CSS Backgrounds and Borders Level 3](https://drafts.csswg.org/css-backgrounds-3/) · [CSS Basic User Interface Level 4 §outline](https://drafts.csswg.org/css-ui-4/#outline)

## 용어 풀이

- **`border-style`** — 테두리를 어떤 선으로 그릴지. 초깃값 `none`, 값은 `solid`·`dashed`·`dotted`·`double`·`groove`·`ridge`·`inset`·`outset`·`hidden`·`none`.
- **`hidden`(테두리)** — 선을 안 그리고 폭이 0 이 되는 것은 `none` 과 같다. `border-collapse: collapse` 인 표에서만 「이웃 테두리까지 이긴다」로 갈린다.
- **비례 축소(scale factor `f`)** — 한 변의 두 반지름 합이 변 길이보다 클 때, 네 변 전부에서 구한 비율 중 **가장 작은 것**을 모든 반지름에 곱하는 것.
- **`outline`** — 상자 **위에 덧그려지는 선**. 레이아웃 공간을 0 차지하고, Chrome 151 에서는 `border-radius` 를 따라 둥글게 돈다.
- **`outline-offset`** — 테를 상자에서 얼마나 떨어뜨릴지. 음수면 안쪽으로 파고든다. 이것도 공간을 안 차지한다.
- **`spread`(그림자 확산)** — 그림자 모양을 사방으로 N px 부풀리는 것. 흐리는 `blur` 와 다르다.
- **`inset`(그림자)** — 그림자를 상자 **안쪽**에 그린다. 바깥에는 아무것도 안 남는다.
- **안티앨리어싱(anti-aliasing)** — 곡선·사선을 픽셀 격자에 맞출 때 경계에 중간색을 넣어 계단을 덜 보이게 하는 것.\
  예: 둥근 모서리 경계에서 `(204,0,0)` 도 `(255,255,255)` 도 아닌 `(226,111,111)` 같은 값이 읽히는 것.
- **진단 3창** — `cssRules`(규칙이 담겼나) → `querySelectorAll`(잡혔나) → `getComputedStyle`(이겼나). CSS 는 에러가 없으므로 이 셋을 안 가르면 증상이 전부 같다. 정본은 [07번](../07-syntax-and-error-recovery/2-summary.md).

## 더 들어가면

- **`border-image`** — 테두리 자리에 이미지를 깔아 늘리는 축. `border-style` 이 `none` 이면 이것도 안 그려진다(폭이 0 이므로).
- **`box-shadow` 와 성능** — `blur` 가 큰 그림자를 많이 쌓으면 합성 비용이 커진다. 같은 모양을 반복할 때는 그림자 대신 미리 그린 이미지를 쓰는 쪽이 쌀 수 있다. 이 문서는 성능을 측정하지 않았다.
- **`outline-style: auto`** — UA 가 자기 포커스 링 모양을 그리도록 맡기는 값. 플랫폼마다 그림이 다르다.
- **`corner-shape`** — 모서리를 원 말고 다른 곡선으로 깎으려는 최신 제안. 이 배치에서는 다루지 않았다.

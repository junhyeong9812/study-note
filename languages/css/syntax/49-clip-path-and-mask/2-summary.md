# css/syntax/49 — `clip-path` 와 `mask` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [CSS Masking Module Level 1](https://drafts.csswg.org/css-masking-1/) (`clip-path`·`mask-*`·`<geometry-box>` 의 정본) · [CSS Shapes Level 1](https://drafts.csswg.org/css-shapes-1/#basic-shape-functions) (`inset`·`circle`·`ellipse`·`polygon`·`path` 도형 함수). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 `demo` 블록 **4개 전부**와 본문의 모든 수치를 **Google Chrome 151.0.7922.173** headless 에서 실제로 렌더해 확인했다.\
> ★ **이 주제는 `getComputedStyle` 로 거의 아무것도 증명하지 못한다.** `mask-image: url(#nope)` 는 계산값이 멀쩡한데 **요소가 통째로 사라진다**(아래 「진단 3창」).\
> 그래서 **스크린샷 PNG 를 파이썬 표준 라이브러리(`zlib`)로 디코드해 좌표별 `(r,g,b)` 를 읽는 것**이 주 근거다 — **잘린 자리가 페이지 배경색으로 돌아오는지**로 판정한다. 이벤트는 `document.elementFromPoint()` 로 확인했다.
> **버전** — CSS 에 언어 버전이 없으므로 Baseline 으로 읽는다. webstatus.dev 조회(2026-09-23): `clip-path` **widely**(2021-01-21 → 2023-07-21) · `masks`(Masks) **widely**(2023-12-07 → 2026-06-07, Chrome 120·Firefox 53·Safari 15.4).
> **여기서 다루지 않는 것** — **모서리 넷을 깎는 것**(`border-radius`)은 [46번](../46-borders-radius-outline-shadow/2-summary.md)이 정본이다. 여기는 그것을 **임의의 도형으로 일반화한 것**부터다.\
> 그라디언트 자체는 [목록의 **45번 주제**](../45-gradients-and-interpolation/), 배경 레이어 규칙(`mask-size`·`mask-repeat` 이 그대로 따르는 것)은 **44번 주제**, 쌓임 맥락은 **22번 주제**, `filter` 는 [47번](../47-filter-and-backdrop-filter/2-summary.md), 혼합·격리는 [48번](../48-blend-modes-and-isolation/2-summary.md)이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 수치는 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**둘 다 「어디를 보이게 할지」를 정하는 도구인데, 가위와 스텐실로 갈린다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 종이를 **모양대로 오려내는 가위** | **`clip-path`** — 도형 안쪽만 남기고 바깥은 **없앤다**(전부 아니면 전무) |
| 구멍 뚫린 **스텐실을 대고 스프레이** | **`mask`** — 마스크의 **밝기나 투명도만큼** 비친다(0\~100% 연속) |
| 액자 유리를 잘라 놓고 **액자째 그대로 두는 것** | **`overflow: hidden`** — 자기 자신은 안 자르고 **삐져나온 자손만** 자른다 |
| 오려낸 자리는 **손도 안 닿는다** | 잘린 밖은 **이벤트도 안 받는다** — `elementFromPoint` 가 그 아래 요소를 돌려준다 |

- **`clip-path` 는 이분법이다.** 도형 안이면 100%, 밖이면 0%.
- **`mask` 는 연속이다.** 그래서 **페이드 아웃**은 `mask` 로만 된다.
- 둘 다 **레이아웃 치수는 안 바꾼다.** 잘려도 `rect` 는 그대로다.

```text
  같은 상자, 세 가지 자르기

  overflow: hidden        clip-path: circle()       mask-image: gradient
  ┌────────────┐          ╭──────╮                  ┌────────────┐
  │ 자기 배경   │          │ 도형  │                  │▓▓▓▒▒▒░░░   │
  │ 자기 그림자 │ 남는다   │ 안만  │ 남는다            │ 점점 사라진다│
  │ 자손만 잘림 │          ╰──────╯                  └────────────┘
  └────────────┘           자기 그림자도 잘린다        경계가 연속이다
```

실무에서 이게 터지는 자리는 **긴 목록의 페이드 아웃**이다.\
`overflow: hidden` 으로는 경계가 칼처럼 잘리고, `mask-image: linear-gradient(#000, transparent)` 면 부드럽게 사라진다.

> **알파(alpha)** — 그 픽셀이 얼마나 불투명한지. 0 이면 완전 투명, 255 면 완전 불투명.\
> 예: 투명 PNG 의 빈 구석은 색이 있어도 알파가 0 이라 안 보인다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 네 질문을 둔다.

1. `clip-path` 가 `overflow: hidden` 과 **정확히 무엇이 다른가** — 모양 말고도 다른 것이 있는가.
2. `clip-path` 가 **쌓임 맥락과 포함 블록을 건드리는가** — 던져서 확인해야 하는 항목이다.
3. **알파 마스크와 휘도 마스크**는 같은 이미지에서 어떻게 갈리는가.
4. `-webkit-mask-` 접두사가 **아직 필요한가** — 그리고 지금 그것을 쓰면 무슨 일이 일어나는가.

## 동작 방식

### (1) `clip-path` 의 도형 함수 — 잘린 밖은 배경색으로 돌아온다

**언제 쓰나** — 상자를 사각형 아닌 모양으로 보이게 할 때.

```text
  노란 페이지(#ffcc00) 위 파란 상자(#1d4ed8) 120x120

  함수                              도형 안 픽셀    도형 밖 픽셀
  inset(20px)                      (29,78,216)   (255,204,0)  <- 페이지 배경
  circle(45px at 60px 60px)        (29,78,216)   (255,204,0)
  ellipse(50px 25px at 60px 60px)  (29,78,216)   (255,204,0)
  polygon(50% 0, 100% 100%, 0 100%) (29,78,216)   (255,204,0)
  path('M 0 0 L 120 0 L 120 60 Z') (29,78,216)   (255,204,0)
```

```html demo
<div class="page">
  <span class="s1"></span><span class="s2"></span><span class="s3"></span>
</div>
<style>
  .page { background: #ffcc00; padding: 14px; width: 330px; font: 0/0 a; }
  .page span { display: inline-block; width: 100px; height: 100px; margin-right: 5px;
               background: #1d4ed8; vertical-align: top; }
  .s1 { clip-path: circle(45px at 50px 50px); }
  .s2 { clip-path: polygon(50% 0, 100% 100%, 0 100%); }
  .s3 { clip-path: inset(10px 30px round 18px); }
</style>
```

> **보이는 것** — 노란 판 위에 파란 사각형 셋이 있어야 할 자리에 **원 하나·위를 향한 삼각형 하나·세로로 좁고 모서리가 둥근 직사각형 하나**가 보인다. 잘려 나간 자리는 파랑이 아니라 **노란 판 색**이다.\
> **실측** — *(Chrome 151 headless: 원 안 `(29,78,216)` / 원 밖 모서리 `(255,204,0)` · 삼각형 안 `(29,78,216)` / 왼쪽 위 `(255,204,0)` · `inset` 안 `(29,78,216)` / 좌우 잘린 자리 `(255,204,0)`. 세 상자 모두 `rect` 는 100×100 그대로다. `elementFromPoint` 를 원 밖 좌표에 던지면 `.s1` 이 아니라 `.page` 가 나온다.)*\
> **바꿔 볼 것** — `circle(45px at 50px 50px)` → `circle(45px)`(중심이 기본값 `center` 가 되어 그대로다) · `polygon(...)` → `polygon(50% 0, 100% 50%, 50% 100%, 0 50%)`(마름모) · `inset(10px 30px round 18px)` 의 `round 18px` 삭제(모서리가 각져진다)

그림 해설 (한 단계씩):

- 잘린 밖은 「투명해진」 것이 아니라 **그 요소가 그려지지 않은** 것이다. 뒤에 있던 것이 그대로 보인다.
- **레이아웃은 안 바뀐다.** `rect` 는 잘리기 전 치수 그대로다 — 옆 상자는 안 당겨진다.
- **잘린 밖은 이벤트도 안 받는다.** `elementFromPoint` 가 그 아래 요소를 돌려준다.

비용 — 없다. 다만 **잘린 자리가 차지하던 공간은 그대로 남는다.**

### (2) 도형 함수 다섯 — 무엇을 쓰나

```text
  inset(<상하좌우> [round <반지름>])    사각형을 안쪽으로 밀어 깎는다. border-radius 문법 재사용
  circle(<반지름> [at <중심>])          원
  ellipse(<가로반지름> <세로반지름> [at <중심>])  타원
  polygon([<채움규칙>,] x y, x y, ...)  꼭짓점 목록. 쉼표로 잇는다
  path([<채움규칙>,] "<SVG 경로>")       SVG path 문법 — 곡선까지 된다
```

```text
  polygon 으로 삼각형 그리기 — 좌표는 요소의 왼쪽 위가 (0,0)

   (50%, 0)
      /\
     /  \
    /    \
   ──────── (100%, 100%)
  (0, 100%)

  polygon(50% 0, 100% 100%, 0 100%)
```

- `circle(45px)` 처럼 중심을 생략하면 `at center` 다.
- `%` 는 참조 상자의 폭·높이 기준이고, 반지름의 `%` 는 대각선 기준이라 **가로·세로가 다르면 직관과 어긋난다.**
- `path()` 는 좌표가 **px 고정**이라 반응형에 약하다. `polygon()` 은 `%` 를 쓸 수 있다.

### (3) `<geometry-box>` — 어느 상자를 기준으로 자르나

**언제 쓰나** — 패딩·테두리가 있는 상자에서 「어디까지」를 정할 때.

```text
  상자: border 10px + padding 20px + content 80px

  선언                       테두리 자리     패딩 자리      내용 자리
  clip-path: inset(0)       (148,163,184)  (29,78,216)   (29,78,216)   <- 기본 border-box
  inset(0) padding-box      (255,204,0)    (29,78,216)   (29,78,216)   <- 테두리가 잘렸다
  inset(0) content-box      (255,204,0)    (255,204,0)   (29,78,216)   <- 패딩까지 잘렸다
```

```text
  네 상자가 이렇게 겹쳐 있다 (15번 주제의 그림과 같은 좌표계)

   margin-box   ┌──────────────────────────┐
   border-box   │ ┌──────────────────────┐ │
   padding-box  │ │ ┌──────────────────┐ │ │
   content-box  │ │ │ [   내용    ]    │ │ │
                │ │ └──────────────────┘ │ │
                │ └──────────────────────┘ │
                └──────────────────────────┘

   clip-path 의 기본은 border-box · mask 쪽 기본은 border-box(mask-clip)
```

- `fill-box`·`stroke-box`·`view-box` 는 SVG 용이다.
- 계산값이 재미있다 — `clip-path: circle(40px) border-box` 는 **`circle(40px)` 으로 직렬화된다**(기본값이라 생략). `padding-box`·`content-box`·`margin-box` 는 그대로 남는다.

*(Chrome 151 headless 실측 — 위 두 표는 같은 문서의 상자 넷에서 읽은 값이다.)*

### (4) ★ `overflow: hidden` 과 무엇이 다른가 — **자기 자신을 자르나**

**언제 쓰나** — 둘 중 무엇을 쓸지 고를 때. 모양 말고 **더 중요한 차이**가 있다.

```html demo
<div class="page">
  <div class="a"><i></i></div>
  <div class="b"><i></i></div>
</div>
<style>
  .page { background: #ffcc00; padding: 30px 40px; width: 250px; }
  .page > div { width: 110px; height: 60px; margin: 30px 0; background: #1d4ed8;
                box-shadow: 0 0 0 12px #dc2626; position: relative; }
  .a { overflow: hidden; }
  .b { clip-path: inset(0); }
  i  { position: absolute; left: -26px; top: -26px; width: 44px; height: 44px; background: #059669; }
</style>
```

> **보이는 것** — 파란 상자 둘 다 왼쪽 위로 삐져나온 초록 사각형이 **잘려 안 보인다.** 그런데 위 상자는 **빨간 테(자기 `box-shadow`)가 그대로 있고**, 아래 상자는 **빨간 테까지 통째로 사라져** 파란 사각형만 남는다.\
> **실측** — *(Chrome 151 headless: 삐져나온 자식 자리가 위 `(220,38,38)`(그 아래 빨간 그림자가 보인다)·아래 `(255,204,0)`(페이지 배경). 자기 그림자 자리가 위 `(220,38,38)`·아래 `(255,204,0)`. 본체는 둘 다 `(29,78,216)`.)*\
> **바꿔 볼 것** — `.b` 의 `inset(0)` → `inset(-20px)`(자르는 상자가 20px 바깥으로 커져 **빨간 테와 삐져나온 초록 자식이 둘 다 돌아온다**) · `.a` 에 `border-radius: 20px` 추가(자손은 **둥글게** 잘리는데 빨간 테는 그대로 남는다) · `.b` 의 `inset(0)` → `circle(50%)`(임의 모양으로 자를 수 있는 쪽은 이쪽뿐이다)

```text
  전 (overflow: hidden)                   후 (clip-path: inset(0))

  ┌─ 자기 box-shadow 남는다 ─┐              (그림자 없음)
  │ ┌──────────────────┐   │              ┌──────────────────┐
  │ │ 자손은 잘린다      │   │              │ 자손도 잘린다      │
  │ └──────────────────┘   │              └──────────────────┘
  └────────────────────────┘

  삐져나온 자식 자리 (220,38,38)             같은 자리 (255,204,0) 페이지 배경
  자기 그림자 자리   (220,38,38)             같은 자리 (255,204,0)
```

정리하면 이렇다.

```text
                       overflow: hidden        clip-path
  자손을 자르나          자른다                  자른다
  자기 배경·테두리를      안 자른다               자른다
  자기 box-shadow 를     안 자른다               자른다
  모양                  사각형 + border-radius   임의 도형
  스크롤 컨테이너를 만드나 만든다                  안 만든다
  잘린 밖의 이벤트        (스크롤로 접근 가능)      안 받는다
```

- 곧 `overflow` 는 **담는 그릇**의 규칙이고 `clip-path` 는 **그려진 결과를 오려내는** 규칙이다.
- `overflow: hidden` 은 BFC 도 만든다([17번](../17-block-formatting-context/2-summary.md)) — `clip-path` 는 안 만든다.

### (5) ★ `clip-path` 가 쌓임 맥락·포함 블록을 건드리나 — **던져서 확인**

**언제 쓰나** — 추측하면 안 되는 자리다. [47번](../47-filter-and-backdrop-filter/2-summary.md)의 `filter` 와 결과가 **갈린다.**

```text
  실험 1 — 쌓임 맥락

  wrap 에 clip-path 없음      z-index:9999 자식이 이김   겹침 픽셀 (220,38,38)
  wrap 에 clip-path: inset(0) 형제가 위로 옴            겹침 픽셀 ( 37,99,235)
  -> 쌓임 맥락을 만든다 ○

  실험 2 — fixed 자손의 포함 블록

  wrap 에 clip-path 없음      fixed 자식 (0,0)  offsetParent = null
  wrap 에 clip-path: inset(0) fixed 자식 (0,0)  offsetParent = null
  -> 포함 블록은 가로채지 않는다 ×
```

```text
  47번과 나란히 놓으면

                      쌓임 맥락   fixed 포함 블록   backdrop root
  filter               O           O                O
  clip-path            O           X                (안 쟀다)
  isolation: isolate   O           X(해당 없음)      X
```

- ★ **`clip-path` 는 쌓임 맥락은 만들지만 포함 블록은 안 가로챈다.** `filter` 와 다르다 — **추측했으면 틀렸을 자리다.**
- 쌓임 맥락을 만든다는 것은 [48번](../48-blend-modes-and-isolation/2-summary.md)의 **격리**도 만든다는 뜻이다.

*(Chrome 151 headless 실측 — 두 실험 모두 두 판을 한 문서에 두고 픽셀과 `offsetParent` 를 읽은 값이다.)*

### (6) `mask` 의 축 — 배경 속성과 같은 모양

**언제 쓰나** — 마스크를 쓸 때마다. 축 이름이 `background-*` 와 짝을 이룬다.

```text
  mask-image      무엇을 마스크로 쓰나        (background-image 와 같은 값 문법)
  mask-mode       그 이미지의 무엇을 읽나      alpha | luminance | match-source
  mask-size       크기                      (background-size 와 같다)
  mask-repeat     반복                      (background-repeat 와 같다)
  mask-position   위치                      (background-position 과 같다)
  mask-origin     기준 상자
  mask-clip       어디까지 보이나
  mask-composite  여러 겹을 어떻게 합치나      add | subtract | intersect | exclude
  mask            위 전부의 단축
```

- **레이어가 여럿**이면 쉼표로 나열한다(배경과 같다 — [목록의 **44번 주제**](../44-backgrounds-and-object-fit/)).
- `mask-composite` 는 **레이어들끼리** 알파를 합치는 규칙이다. [48번](../48-blend-modes-and-isolation/2-summary.md)의 혼합이 「색」이라면 이쪽은 「알파」다.

### (7) ★ 알파 마스크와 휘도 마스크 — **같은 이미지, 정반대 결과**

**언제 쓰나** — 마스크가 안 먹거나, 반대로 먹을 때.

실험용 PNG 를 하나 만들었다 — **알파는 전부 255(완전 불투명)이고 색만 검정→흰색으로 변하는** 16×4 이미지다.

```text
  그 PNG 를 마스크로 썼을 때

  mask-mode       왼쪽 끝         가운데         오른쪽 끝
  alpha           (29,78,216)   (29,78,216)   (29,78,216)   <- 알파가 전부 255 이라 전부 보인다
  luminance       (255,255,255) (129,156,233) (29,78,216)   <- 검정 쪽이 사라진다
  match-source    (29,78,216)   (29,78,216)   (29,78,216)   <- 이미지면 alpha 와 같다
```

```html demo
<div class="alpha">mask-mode: alpha</div>
<div class="lum">mask-mode: luminance</div>
<style>
  div { width: 260px; height: 46px; margin: 16px; background: #1d4ed8;
        font: 12px/46px system-ui; color: #fff; text-align: center;
        mask-image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAECAYAAACHtL/sAAAAS0lEQVR42tXMgRRAIQxA0SmkkMIUUphCCilMYQopTGEKKaTwOh/jX4ArIkJrjd47qsoYAzNjzslaC3cnIth7k5lUFecc7r185P/BA4ion2HV9n29AAAAAElFTkSuQmCC);
        mask-size: 100% 100%; mask-repeat: no-repeat; }
  .alpha { mask-mode: alpha; }
  .lum   { mask-mode: luminance; }
</style>
```

> **보이는 것** — 같은 마스크 이미지를 쓴 파란 띠 둘이다. 위 띠는 **통째로 파랗고**, 아래 띠는 **왼쪽이 하얗게 사라졌다가 오른쪽으로 갈수록 진해진다.** 선언 차이는 `mask-mode` 한 줄뿐이다.\
> **실측** — *(Chrome 151 headless — 글자를 피해 띠의 `x` = 20·90·160·230·270 을 읽었다: 위 띠는 다섯 지점 모두 `(29,78,216)`. 아래 띠는 왼쪽부터 `(255,255,255)` → `(194,207,244)` → `(129,156,233)` → `(64,106,222)` → `(29,78,216)`.)*\
> **바꿔 볼 것** — `.lum` 의 `mask-mode` → `match-source`(위 띠와 같아진다 — 이미지는 기본이 알파다) · `mask-size: 100% 100%` → `mask-size: 40px 100%`(아래 띠가 **왼쪽 40px 만 남고 나머지는 사라진다**) · 그 상태에서 `mask-repeat: no-repeat` 까지 지우면(40px 짜리 마스크가 **타일처럼 되풀이**돼 띠 전체에 줄무늬가 생긴다)

그림 해설:

- **`alpha`** — 이미지의 **알파 채널**을 읽는다. 알파가 255 면 전부 보인다.
- **`luminance`** — 이미지의 **밝기**를 읽는다. 검정이면 숨고 흰색이면 보인다.
- **`match-source`(기본값)** — 이미지면 **알파**, SVG `<mask>` 요소를 참조하면 **휘도**다.
- 그래서 **같은 파일이 두 가지로 읽힌다.** 「마스크가 반대로 걸렸다」의 원인이 대개 이것이다.

### (8) ★ 그라디언트 마스크 — `linear-gradient(#000, #fff)` 는 **아무 일도 안 한다**

**언제 쓰나** — 목록 끝을 부드럽게 사라지게 할 때. 실무에서 가장 많이 쓰는 마스크다.

```text
  마스크로 쓴 그라디언트                      결과 (왼쪽 → 오른쪽)
  linear-gradient(to right,#000,#fff)       전부 그대로  ★ 함정
  같은 것 + mask-mode: luminance             왼쪽이 사라진다
  linear-gradient(to right,#000,transparent) 오른쪽으로 사라진다   <- 이것이 정석
  linear-gradient(to right,transparent,#000) 왼쪽으로 사라진다
```

```html demo
<div class="none">마스크 없음</div>
<div class="fade">오른쪽으로 사라진다</div>
<style>
  div { width: 260px; height: 46px; margin: 16px; background: #1d4ed8;
        font: 12px/46px system-ui; color: #fff; text-align: center; }
  .fade { mask-image: linear-gradient(to right, #000 40%, transparent); }
</style>
```

> **보이는 것** — 위 띠는 오른쪽 끝까지 고르게 파랗다. 아래 띠는 왼쪽 40% 까지는 같은 파랑인데 그 뒤로 **오른쪽 끝까지 점점 옅어지며 배경에 녹아 사라진다.**\
> **실측** — *(Chrome 151 headless — 같은 `x` = 20·90·160·230·270: 위 띠 다섯 지점 모두 `(29,78,216)`. 아래 띠는 `(29,78,216)` → `(29,78,216)` → `(102,135,228)` → `(189,204,244)` → `(247,249,254)`.)*\
> **바꿔 볼 것** — `to right` → `to bottom`(아래로 사라진다) · `#000 40%` → `#000 80%`(사라지는 구간이 짧아진다) · `transparent` → `#fff`(★ **아무 일도 안 일어난다** — 흰색도 알파는 1 이다)

```text
  왜 #000 -> #fff 가 아무 일도 안 하나

  mask-mode 의 기본값 match-source
        ↓
  마스크가 이미지(그라디언트 포함)이면 -> 알파를 읽는다
        ↓
  #000 도 #fff 도 알파는 1  ->  마스크가 전 영역 1  ->  전부 보인다

  고치는 법 두 가지
   (가) 색 대신 알파를 쓴다:  linear-gradient(#000, transparent)
   (나) 모드를 바꾼다:        mask-mode: luminance
```

- **포토샵·SVG 의 습관(검정=숨김, 흰색=보임)이 CSS 기본값과 어긋난다.** 이것이 이 주제 최대의 함정이다.

### (9) `mask-composite` — 여러 겹을 합치는 규칙

**언제 쓰나** — 두 방향 페이드처럼 마스크 두 겹이 필요할 때.

```text
  mask-image: linear-gradient(to right,#000 0 50%,transparent),
              linear-gradient(to left, #000 0 50%,transparent);
  mask-composite: intersect;

  왼쪽에서 오는 마스크   ████████░░░░░░░░
  오른쪽에서 오는 마스크  ░░░░░░░░████████
  intersect (곱)        ░░░▒▒██████▒▒░░░   <- 가운데만 남고 양끝이 사라진다
```

- 실측 픽셀: 양 끝 `(243,245,253)`·`(245,247,253)`(거의 배경), 가운데 `(41,88,218)`(거의 원색).
- 값은 `add`(기본)·`subtract`·`intersect`·`exclude` 넷이다.

*(Chrome 151 headless 실측 — 한 문서에서 다섯 판을 렌더해 다섯 좌표씩 읽었다.)*

### (10) ★ `-webkit-mask-` 접두사는 아직 필요한가 — **던진 결과**

**언제 쓰나** — 예전 코드를 만났을 때. 그리고 **「호환을 위해 둘 다 쓰자」는 생각이 들 때.**

```text
  던진 것                                        cssRules 에 남은 것
  .c { -webkit-mask-image: linear-gradient(...) } .c { mask-image: linear-gradient(...); }
                                                  ★ 접두사가 사라지고 무접두사로 바뀌었다
  .d { mask-image: linear-gradient(...);          .d { mask-image: none; }
       -webkit-mask-image: none }                 ★ 뒤에 쓴 접두사판이 앞의 무접두사판을 덮었다
```

- 곧 Chrome 151 에서 `-webkit-mask-*` 는 **무접두사 속성의 별칭**이다. 같은 속성이라 **나중에 쓴 쪽이 이긴다.**
- **그래서 「둘 다 쓰기」가 위험하다.** 순서를 잘못 쓰면 무접두사판이 조용히 덮인다.
- Baseline 조회(2026-09-23): `masks` 가 **widely**(2023-12-07 → 2026-06-07), Chrome 120(2023-12)·Firefox 53(2017-04)·Safari 15.4(2022-03). **무접두사로 충분하다.**
- 다만 이 판정은 **Chrome 151 의 관찰 + Baseline 데이터**이고, 아주 오래된 Safari 를 지원해야 한다면 접두사판이 필요할 수 있다.

## 문법 — 형태와 어디서 헷갈리나

### 최소 형태

```css
/* clip-path — 도형 [기준 상자] */
.a { clip-path: inset(10px 20px round 8px); }
.b { clip-path: circle(40px at 30% 50%); }
.c { clip-path: polygon(50% 0, 100% 100%, 0 100%); }
.d { clip-path: path('M 0 0 L 120 0 L 120 60 Z'); }
.e { clip-path: inset(0) content-box; }
.f { clip-path: url(#svgClipPath); }

/* mask — 이미지가 축의 중심 */
.g { mask-image: linear-gradient(#000, transparent); }
.h { mask-image: url(icon.svg); mask-size: contain; mask-repeat: no-repeat;
     mask-position: center; }
.i { mask-image: url(a.png); mask-mode: luminance; }
.j { mask-image: url(a.png), url(b.png); mask-composite: intersect; }
```

### 헷갈리는 자리 — 단축 `mask` 가 되돌리는 것

```text
  .a { mask-mode: luminance; mask: linear-gradient(#000,#fff) }
       -> cssRules: .a { mask: linear-gradient(...); }
          계산값 mask-mode = match-source     ★ 단축이 앞의 mask-mode 를 지웠다

  .b { mask: linear-gradient(#000,#fff); mask-mode: luminance }
       -> cssRules: .b { mask: linear-gradient(...) luminance; }
          계산값 mask-mode = luminance        ○
```

- **단축 `mask` 는 `mask-mode` 를 포함한 모든 하위 축을 초깃값으로 되돌린다.** 순서를 지켜야 한다.
- `background` 단축이 `background-color` 를 지우는 것과 같은 성격이다.

### 금지에 가까운 형태 — 조용히 버려지는 것들

```css
.x {
  clip-path: polygon(50%, 100% 100%);   /* 좌표가 한 쌍이 아니다 — 버려진다 */
  mask-mode: alpha-zz;                  /* 값 이름 틀림 — 버려진다 */
  mask-image: url(#nope);               /* ★ 살아남는다. 그런데… */
}
```

★ 「진단 3창」으로 물었다.

```text
  창 1  cssRules  → .x { mask-image: url("#nope"); }   나머지 둘은 사라졌다
  창 2  querySelectorAll → 잡혔다
  창 3  clip-path = none · mask-mode = match-source · mask-image = url("#nope")

  ★ 그런데 화면에서 그 요소는 통째로 사라졌다 — 픽셀이 페이지 배경색 (255,204,0) 이다.
    깨진 data URI 를 마스크로 줘도 같았다.
```

- 이것이 이 주제의 **제4의 상태**다: **세 창을 전부 통과하는데 요소가 안 보인다.**
- 참조가 안 풀리는 마스크는 「마스크 없음」이 아니라 「**전부 가리는 마스크**」처럼 동작했다.

## 구현 세부사항 대 언어 보장

| 항목 | 누가 보장하나 |
|---|---|
| `clip-path` 가 **자기 배경·테두리·그림자까지** 자르는 것 | **명세**(css-masking-1 §clip-path — 요소를 클리핑 경로로 자른다) |
| 잘린 밖이 **이벤트를 안 받는** 것 | **명세**(css-masking-1 — 클리핑은 히트 테스트에도 적용된다) + 실측 |
| `clip-path` 가 **쌓임 맥락**을 만드는 것 | **명세**(css-masking-1 §clip-path — `none` 이 아니면 쌓임 맥락) + 실측 |
| `clip-path` 가 **포함 블록은 안 가로채는** 것 | ★ **실측이다.** 포함 블록 생성 목록(css-position-3)에 `clip-path` 가 없다는 것까지 대조하지는 않았다 |
| `<geometry-box>` 기본값이 **`border-box`** 인 것 | **명세**(css-masking-1) + 계산값이 그 값을 생략해 직렬화하는 것으로 확인 |
| `mask-mode: match-source` 가 **이미지면 알파**인 것 | **명세**(css-masking-1 §mask-mode) |
| 단축 `mask` 가 `mask-mode` 를 되돌리는 것 | **명세**(단축 속성 일반 규칙) + 실측 |
| `-webkit-mask-*` 가 **별칭**이라 순서로 덮이는 것 | ★ **Chrome 151 에서 관찰한 것.** 접두사 동작은 명세가 아니라 구현 사항이다 |
| 참조가 안 풀리는 마스크에서 **요소가 사라지는** 것 | ★ **Chrome 151 에서 관찰한 것.** 「마스크 없음으로 취급」하는 구현도 있을 수 있다 — 그러므로 **깨진 참조를 남기지 마라** |
| 각 픽셀의 **정확한 값**과 경계의 안티앨리어싱 | ★ **보장 아님.** `--disable-gpu` **소프트웨어 렌더링** 결과다 |

★ **엔진은 Chrome 하나다.** Firefox 155.0.1 은 이 환경에서 headless 스크린샷이 산출되지 않고 WebKit 은 이 머신에 없다. 크로스 브라우저는 **Baseline 데이터로만** 접지했다.

## 어디서 틀리나

### 1. `linear-gradient(#000, #fff)` 로 페이드를 만들려 한다

- **아무 일도 안 일어난다.** 흰색도 알파는 1 이다. 실측에서 다섯 지점이 전부 원색이었다.
- `transparent` 를 쓰거나 `mask-mode: luminance` 를 켠다.

### 2. 접두사와 무접두사를 둘 다 쓰면서 순서를 안 본다

```css
.bad { mask-image: linear-gradient(#000, transparent);
       -webkit-mask-image: none; }        /* 무접두사판이 덮인다 */
```

- Chrome 151 에서 둘은 **같은 속성**이다. 나중 것이 이긴다.
- 지금은 **무접두사만 쓰면 된다**(Baseline widely).

### 3. 단축 `mask` 를 `mask-mode` 앞에 쓴다

- 단축이 `mask-mode` 를 `match-source` 로 되돌린다. 순서를 뒤집어야 한다.

### 4. `clip-path` 와 `overflow: hidden` 을 같은 것으로 본다

- `clip-path` 는 **자기 그림자·테두리까지** 자른다. 카드에 그림자를 주고 `clip-path` 로 모양을 내면 **그림자가 사라진다.**
- 그림자를 남기려면 바깥에 한 겹 더 두고 그쪽에 그림자를 준다.

### 5. `clip-path` 가 `fixed` 를 고장 낼 거라고 짐작한다

- **안 고장 낸다.** 실측: `offsetParent` 가 `null` 이고 좌표도 `(0,0)` 그대로였다.
- `filter` 와 결과가 다르다 — **짐작하지 말고 던져야 하는 자리다.**

### 6. 잘린 자리가 공간을 안 차지할 거라고 생각한다

- `rect` 는 잘리기 전 치수 그대로다. 옆 요소는 안 당겨진다.
- **보이는 것과 차지하는 것이 다르다.**

### 7. `mask-image: url(#nope)` 같은 깨진 참조를 남긴다

- 계산값은 멀쩡한데 **요소가 통째로 안 보인다.** 개발자 도구로는 못 잡는다.
- 마스크를 지울 때는 `mask-image: none` 으로 지운다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 아바타를 원형으로 | `border-radius: 50%`([46번](../46-borders-radius-outline-shadow/2-summary.md)) | 가장 싸고 부작용이 없다 |
| 리본·말풍선 꼬리 같은 도형 | `clip-path: polygon()` | 임의 도형이 된다 |
| 목록 끝 페이드 아웃 | `mask-image: linear-gradient(#000, transparent)` | 연속 경계는 마스크로만 된다 |
| 아이콘 색을 CSS 로 바꾸기 | `mask-image: url(icon.svg)` + `background-color` | 한 파일로 여러 색을 낸다 |
| 자손만 가두기 | `overflow: hidden` ([17번](../17-block-formatting-context/2-summary.md), [목록의 **23번 주제**](../23-overflow-and-scroll-containers/)) | 자기 그림자를 남긴다 |
| 스크롤이 필요하다 | `overflow: auto` | `clip-path` 는 스크롤 컨테이너를 안 만든다 |
| 뒤에 깔린 것 흐리기 | `backdrop-filter`([47번](../47-filter-and-backdrop-filter/2-summary.md)) | 자르기로는 못 한다 |

**안 쓰는 쪽** — **클릭해야 하는 요소**를 `clip-path` 로 크게 잘라내면 잘린 밖이 이벤트를 안 받는다. 버튼 모양을 낼 때는 히트 영역을 함께 확인한다.

## 핵심 문장

- `clip-path` 는 **전부 아니면 전무**, `mask` 는 **0\~100% 연속**이다. 페이드는 마스크로만 된다.
- `clip-path` 는 **자기 배경·테두리·그림자까지** 자르고, `overflow: hidden` 은 **자손만** 자른다.
- `clip-path` 는 **쌓임 맥락을 만들지만 포함 블록은 안 가로챈다** — `filter` 와 갈리는 자리다.
- 마스크의 기본은 **알파**다. `linear-gradient(#000, #fff)` 는 **아무 일도 안 한다.**
- Chrome 151 에서 `-webkit-mask-*` 는 **별칭**이다. 둘 다 쓰면 나중 것이 이긴다 — 무접두사만 쓴다.

## 관련 자료

- [46번 — 테두리·`border-radius`·`outline`·`box-shadow`](../46-borders-radius-outline-shadow/2-summary.md) — **그쪽은 모서리 넷을 깎는 것까지, 여기는 그것을 임의 도형으로 일반화한 것부터.** `border-radius` 가 이미 「배경을 자르는 것」이고 `inset(… round …)` 가 그 문법을 그대로 재사용한다.
- [47번 — `filter` 와 `backdrop-filter`](../47-filter-and-backdrop-filter/2-summary.md) — **그쪽은 색을 바꾸는 것, 여기는 보일 자리를 정하는 것.** 포함 블록 부작용이 **갈리는 자리**이기도 하다.
- [48번 — 혼합 모드와 `isolation`](../48-blend-modes-and-isolation/2-summary.md) — **그쪽은 색을 합치는 규칙, 여기(`mask-composite`)는 알파를 합치는 규칙.**
- [15번 — 박스 모델](../15-box-model-and-box-sizing/2-summary.md) — `<geometry-box>` 가 가리키는 네 상자의 정본.
- [17번 — 블록 서식 맥락](../17-block-formatting-context/2-summary.md) — `overflow: hidden` 이 BFC 를 만드는 것. `clip-path` 는 안 만든다.
- 그라디언트는 [목록의 **45번 주제**](../45-gradients-and-interpolation/), 배경 속성(`*-size`·`*-repeat`·`*-position`)은 **44번 주제**, 쌓임 맥락은 **22번 주제**, 오버플로·스크롤 컨테이너는 **23번 주제**다.
- [CSS Masking Level 1](https://drafts.csswg.org/css-masking-1/) · [CSS Shapes Level 1 §basic shapes](https://drafts.csswg.org/css-shapes-1/#basic-shape-functions)

## 용어 풀이

- **`clip-path`** — 요소를 도형 안쪽만 남기고 잘라내는 선언. 이분법(안 100% / 밖 0%)이고 레이아웃 치수는 안 바꾼다.
- **도형 함수(basic shape)** — `inset()`·`circle()`·`ellipse()`·`polygon()`·`path()`. `path()` 만 곡선이 되고 좌표가 px 고정이다.
- **`<geometry-box>`** — 도형의 기준이 되는 상자. `border-box`(기본)·`padding-box`·`content-box`·`margin-box` 와 SVG 용 셋.
- **알파(alpha)** — 픽셀의 불투명도. 0 이면 완전 투명.\
  예: `transparent` 는 알파 0 이고 `#fff` 는 알파 1 이다 — 둘 다 색은 다르지만 마스크에서는 이 값이 갈린다.
- **휘도(luminance)** — 픽셀의 밝기. `mask-mode: luminance` 가 읽는 값이고 검정이 0, 흰색이 최대다.
- **`mask-mode`** — 마스크 이미지의 알파를 읽을지 휘도를 읽을지. 기본 `match-source` 는 **이미지면 알파**, SVG `<mask>` 참조면 휘도다.
- **`mask-composite`** — 마스크 레이어 여럿을 합치는 규칙. `add`(기본)·`subtract`·`intersect`·`exclude`.
- **히트 테스트(hit testing)** — 어느 좌표를 눌렀을 때 어느 요소가 잡히는지 정하는 계산.\
  예: `document.elementFromPoint(x, y)` 가 돌려주는 요소. `clip-path` 로 잘린 밖에서는 그 아래 요소가 나온다.
- **제4의 상태** — 「진단 3창」을 전부 통과하는데 화면이 다른 상태. 이 주제에서는 **깨진 마스크 참조**가 그렇다.
- **진단 3창** — `cssRules` → `querySelectorAll` → `getComputedStyle`. 정본은 [07번](../07-syntax-and-error-recovery/2-summary.md).

## 더 들어가면

- **SVG `<clipPath>`·`<mask>` 참조** — `clip-path: url(#id)` 로 SVG 에 정의한 경로를 쓰는 축. `<mask>` 를 참조하면 `match-source` 가 **휘도**가 된다. 이 문서는 참조가 풀리는 경우를 재지 않았다.
- **`clipPathUnits`·`maskUnits`** — SVG 쪽에서 좌표를 사용자 단위로 쓸지 비율로 쓸지 정하는 속성. 반응형 클리핑에 쓴다.
- **`clip-path` 애니메이션** — 같은 함수·같은 꼭짓점 수끼리만 보간된다. `polygon` 끼리 꼭짓점 수가 다르면 전환이 안 된다([52번](../52-transition/2-summary.md)).
- **`clip` 속성(옛것)** — `rect()` 만 되고 `position: absolute` 에만 걸리던 폐기 대상. 오늘은 `clip-path` 를 쓴다.
- **성능** — 마스크는 별도 레이어와 알파 합성을 부른다. 큰 면적에 애니메이션과 함께 쓰면 비싸다. 이 문서는 성능을 측정하지 않았다.

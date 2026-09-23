# css/syntax/56 — 렌더링 파이프라인과 `will-change`: 무엇이 합성만으로 도는가 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [CSS Containment Level 2](https://drafts.csswg.org/css-contain-2/) (`contain`·`content-visibility`) · [CSS Will Change Level 1](https://drafts.csswg.org/css-will-change-1/) (`will-change` 의 정의와 **남용 경고**). 열어서 확인한 것만 적었다.\
> **파이프라인 단계의 이름과 순서는 명세가 아니라 구현의 것**이다 — 이 문서는 **측정한 것**과 **문서가 주장하는 것**을 갈라 적는다.
> **실행 검증** — 이 문서의 `demo` 블록 **2개 전부**와 본문 실험 **5벌**을 **Google Chrome 151.0.7922.173** headless 에 CDP 로 붙여 돌렸다.\
> ★★ **측정 도구를 먼저 밝힌다**((2)) — **CDP `Performance.getMetrics`** 의 `RecalcStyleCount`·`LayoutCount`·`LayoutDuration` 과 **CDP `Tracing` 도메인**(`devtools.timeline`)의 이벤트 수(`UpdateLayoutTree`·`Layout`·`PrePaint`·`Paint`·`Commit`·`RasterTask`)를 썼다. 속성별 표는 **2초 × 3판**을 돌려 흔들림을 같이 적었다.\
> ★ **못 잰 것이 있다** — **합성 레이어의 수와 메모리는 이 환경에서 못 쟀다**((8)). 지어내지 않고 못 쟀다고 적는다.
> **버전** — CSS 에 언어 버전은 없다. `will-change` 는 Baseline **widely**(newly 2020-01-15 → widely 2022-07-15), `contain` 은 **widely**(newly 2022-03-14 → widely 2024-09-14), `content-visibility` 는 **newly**(2025-09-15, 아직 widely 아님) — `api.webstatus.dev` 조회 결과.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**브라우저는 화면 한 장을 만들 때 공장 라인을 탄다. 문제는 「무엇을 바꾸면 라인의 어느 공정부터 다시 도느냐」다.**

[53번](../53-keyframes-and-animation/2-summary.md)과 [54번](../54-transform-2d-and-origin/2-summary.md)이 **무엇이 움직이나**를 다뤘다면,\
이 주제는 **그게 어느 공정을 다시 돌리나**다. 같은 움직임이 눈에는 똑같아 보여도 비용이 수십 배 다르다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 설계도를 다시 읽는다 | **스타일 재계산**(어느 선언이 이겼나 다시 판정) |
| 부품의 치수와 자리를 다시 잰다 | **레이아웃**(어느 상자가 어디에 얼마만 하게) |
| 부품에 색을 다시 칠한다 | **페인트**(픽셀 목록을 만든다) |
| 칠해 둔 조각들을 **옮겨서 붙인다** | **합성**(이미 그린 것을 화면에 배치) |
| 「이 부품 곧 움직일 겁니다」 미리 알림 | `will-change` |
| 「이 방 안의 일은 밖으로 안 샙니다」 선언 | `contain` |

```text
  스타일 재계산 ──> 레이아웃 ──> 페인트 ──> 합성 ──> 화면
       ↑              ↑           ↑          ↑
   color 가         width 가    color 가   transform 이
   여기부터         여기부터    여기부터   여기만
```

- **앞 공정을 건드릴수록 비싸다.** 레이아웃부터 도는 속성은 그 뒤 공정을 전부 끌고 간다.
- **`transform`·`opacity` 는 주 스레드 카운터가 아예 0 이었다** — 스타일 재계산조차 안 돈다((3)).
- ★ 「**합성만 한다**」는 문서의 주장이고, **내가 잰 것은 주 스레드 카운터가 안 올라간다는 것**이다. 둘은 다른 말이다((2)).

실무에서 터지는 자리는 「**움직이긴 하는데 끊긴다**」이다.\
`left` 로 만든 이동과 `transform` 으로 만든 이동은 **눈으로는 구분이 안 되는데** 지표가 완전히 다르다((4)).

> **스타일 재계산(style recalculation)** — 어느 선언이 이겼는지를 다시 판정해 계산값을 만드는 일.\
> 예: 클래스 하나를 토글하면 그 요소와 자손의 계산값을 다시 구해야 한다.

> **합성(compositing)** — 이미 그려 둔 조각들을 화면에 배치해 한 장으로 합치는 일.\
> 예: 이미 칠해 둔 카드 이미지를 40px 오른쪽에 붙이는 것 — 다시 칠하지 않는다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **어떤 속성이 어느 공정부터 다시 돌리는가** — 그리고 **그것을 무엇으로 재는가.**
2. `will-change` 는 실제로 **무엇을 바꾸는가** — 그리고 **무엇을 대가로 치르는가.**
3. `contain` 은 비용을 **얼마나** 줄이는가 — 어느 값이 실제로 효과가 있었는가.

## 동작 방식

### (1) 네 공정

**언제 쓰나** — 「이 속성을 애니메이션해도 되나」를 판단할 때.

```text
  ① 스타일 재계산    선택자를 다시 매칭하고 캐스케이드를 다시 풀어 계산값을 만든다
        ↓
  ② 레이아웃         각 상자의 크기와 자리를 정한다. 한 상자가 커지면 뒤가 전부 밀린다
        ↓
  ③ 페인트           "여기에 이 색, 저기에 이 글자" 그리기 명령 목록을 만든다
        ↓
  ④ 합성             그려 둔 조각들을 옮기고 겹쳐 화면 한 장으로 만든다
```

- 위쪽 공정이 다시 돌면 **그 아래는 전부 따라 돈다.** 레이아웃이 돌면 페인트도 돈다.
- 그래서 판단 규칙은 「**이 속성이 어느 공정에 처음 닿는가**」다.
- ★ **이 네 이름은 명세 용어가 아니다.** 구현이 쓰는 이름이고, 이 문서는 **Chrome 151 의 카운터 이름으로** 접지한다.

### (2) ★★ 어떻게 재나 — 픽셀로는 안 나온다

**언제 쓰나** — 「`transform` 이 싸다」를 **증명**해야 할 때. **이 주제의 난점이 여기다.**

스크린샷으로는 아무것도 안 나온다. 두 움직임이 **똑같이 보이기 때문**이다.\
그래서 CDP 의 계측 두 가지를 썼다.

```text
  ① Performance.getMetrics        누적 카운터를 읽는다
       RecalcStyleCount   스타일 재계산 횟수
       LayoutCount        레이아웃 횟수
       LayoutDuration     레이아웃에 쓴 시간(초)
     -> 애니메이션 전후로 두 번 읽어 '증가분'을 본다

  ② Tracing 도메인 (devtools.timeline)   이벤트를 세어 본다
       UpdateLayoutTree · Layout · PrePaint · Paint · Commit · RasterTask
     -> ①에 없는 '페인트' 층이 여기서 보인다
```

★ **이 도구들이 답하지 못하는 것도 밝혀 둔다.**

- **`Performance.getMetrics` 에는 페인트 카운터가 없다.** 그래서 페인트는 `Tracing` 으로 따로 셌다.
- **합성 레이어의 수와 메모리는 어느 쪽으로도 못 쟀다**((8)).
- 그러므로 이 문서가 말할 수 있는 것은 「**주 스레드의 스타일·레이아웃·페인트 카운터가 올라갔나**」까지다.\
  **「합성만 한다」는 그보다 강한 주장이고, 그것은 명세·문서의 서술이다.**

*(측정 조건 — 2초 동안 `2s linear infinite alternate` 애니메이션을 돌리고 전후 증가분을 읽었다. 60fps 면 120 프레임이다. **각 속성을 3판씩** 돌렸고 판마다 `Page.navigate` 로 새로 띄웠다. 신호 대 잡음: 정지 대조군이 **전 항목 0** 이므로, 120 이라는 값은 **잡음이 아니다.**)*

### (3) ★ 속성별 실측 표 — 이 주제의 결론

**언제 쓰나** — 애니메이션할 속성을 고를 때.

*(Chrome 151 headless 실측 — 2초 × 3판. 값이 판마다 다르면 `/` 로 나눠 적었다.)*

| 애니메이션한 속성 | Style | Layout | PrePaint | Paint | Commit | Raster |
|---|---|---|---|---|---|---|
| `width` | 121/120/120 | 121/120/120 | 121/120/120 | 242/240/240 | 121/120/120 | 176/174/175 |
| `height` | 121 | 121 | 121/120/121 | 242/240/242 | 121/120/121 | 121/120/121 |
| `left` | 120/120/121 | 120/120/121 | 120 | 240 | 120 | 175/175/174 |
| `margin-left` | 120/120/121 | 120/120/121 | 120/121/121 | 240/242/242 | 120/121/121 | 175/176/176 |
| `font-size` | 120/121/120 | 120/121/120 | 120/121/120 | 240/242/240 | 120/121/120 | 120/121/120 |
| `color` | 121/121/120 | **0** | 121/121/120 | 242/242/240 | 121/121/120 | 121/121/120 |
| `box-shadow` | 120/120/121 | **0** | 120/121/120 | 240/242/240 | 120/121/120 | 120/121/120 |
| `border-radius` | 121/120/120 | **0** | 121/120/120 | 242/240/240 | 121/120/120 | 121/120/120 |
| `filter` | 121/121/120 | **0** | 120/121/120 | **0** | 120/121/120 | **0** |
| `visibility` | 120/120/121 | **0** | 120 | **0** | 120 | **0** |
| `background-color` | **0** | **0** | **0** | **0** | **0** | 121/121/120 |
| **`transform`** | **0** | **0** | **0** | **0** | **0** | **0** |
| **`opacity`** | **0** | **0** | **0** | **0** | **0** | **0** |
| (정지 대조군) | 0 | 0 | 0 | 0 | 0 | 0 |

그림 해설 (한 단계씩):

- **120 = 2초 × 60fps.** 매 프레임 그 공정이 돌았다는 뜻이다.
- ★★ **`transform` 과 `opacity` 는 여섯 칸이 전부 0 이다.** 정지 대조군과 **한 칸도 다르지 않다.**\
  주 스레드가 아무 일도 안 했다 — 그런데 화면은 움직인다((4)의 실측 좌표가 그것을 보인다).
- **레이아웃이 도는 무리**: `width`·`height`·`left`·`margin-left`·`font-size`.
- **레이아웃은 안 돌고 페인트는 도는 무리**: `color`·`box-shadow`·`border-radius`.
- ★ **`filter` 와 `visibility` 는 스타일만 돌고 페인트·래스터가 0 이다.**\
  `visibility` 는 **discrete** 라 값이 한 번만 뒤집히는데 **스타일 재계산은 매 프레임 돌았다** — 「값이 안 바뀌어도 앞 공정은 돈다」는 증거다.
- ★★ **`background-color` 가 놀랍다.** 스타일·레이아웃·페인트가 **전부 0** 인데 `RasterTask` 만 120 이다.\
  Chrome 151 이 배경색 애니메이션도 주 스레드 밖으로 넘긴다는 뜻이다. **널리 알려진 「색은 페인트부터」와 어긋난다.**

```text
  이 실측이 그리는 지도

  주 스레드가 아예 안 돈다        transform · opacity
  래스터만 돈다                   background-color          ★ 예상 밖
  스타일만 돈다                   filter · visibility       ★ 예상 밖
  스타일 + 페인트                 color · box-shadow · border-radius
  스타일 + 레이아웃 + 페인트      width · height · left · margin-left · font-size
```

비용 — 측정 자체의 비용은 없다. 다만 **이 표는 Chrome 151 의 것**이고, 어떤 속성이 합성 경로로 갈 수 있는지는 **구현이 계속 늘려 왔다**(「어디서 틀리나 6」).

### (4) 같은 움직임, 다른 비용

**언제 쓰나** — 「이 애니메이션이 왜 끊기지」를 고칠 때.

```html demo
<div class="lane"><i class="lft"></i><i class="tfm"></i></div>
<style>
  .lane { position: relative; width: 340px; height: 68px; border: 2px solid #94a3b8; }
  .lane i { position: absolute; left: 4px; width: 40px; height: 24px; background: #1d4ed8; }
  .lft { top: 4px; }
  .tfm { top: 36px; }
  @keyframes byleft { to { left: 292px } }
  @keyframes bytfm  { to { translate: 288px } }
  .lane:hover .lft { animation: byleft 2s linear infinite alternate; }
  .lane:hover .tfm { animation: bytfm  2s linear infinite alternate; }
</style>
```

> **보이는 것** — 상자 안에 마우스를 올리면 파란 막대 둘이 **나란히, 똑같은 속도로** 왼쪽 끝에서 오른쪽 끝까지 2초에 걸쳐 가고, 다시 2초에 걸쳐 돌아온다. 마우스를 떼면 둘 다 제자리로 돌아간다. **눈으로는 둘을 구분할 수 없다** — 위는 `left`, 아래는 `translate` 인데 화면상 위치가 매 순간 같다.\
> **바꿔 볼 것** — `byleft` 의 `left: 292px` → `left: 200px`(위 막대만 짧게 간다 — 둘이 같은 거리를 가고 있었음을 확인할 수 있다) · `alternate` 를 빼기(끝에서 되감아 처음으로 튄다) · `.lane:hover` → 버튼 `:focus` 같은 다른 방아쇠로

*(Chrome 151 headless 실측 — 마우스를 올린 뒤 시각별 두 막대의 화면 x 좌표:)*

```text
  시각      .lft (left)    .tfm (translate)
  0.10s     22.8           22.8
  0.50s     80.4           80.4
  1.00s     152.4          152.4
  1.50s     222.0          222.0
  2.00s     291.6          291.6      <- 매 시각 같다
```

*(제출 직전 재실행 — 절댓값은 움직이고 「둘이 같다」는 안 움직였다:)*

```text
  시각      첫 판 (.lft / .tfm)     재확인 판 (.lft / .tfm)
  0.50s     80.4 / 80.4             78.0 / 78.0
  1.00s     152.4 / 152.4           150.0 / 150.0
  2.00s     291.6 / 291.6           294.0 / 294.0
```

- **절댓값이 판마다 2\~3px 움직인다** — 마우스 입력에서 재생이 시작되기까지의 지연이 판마다 다르기 때문이다.
- **두 막대가 서로 같다는 것은 두 판 모두 소수 첫째 자리까지 그대로**다. **근거로 쓸 칸은 그쪽이다.**

*(같은 두 애니메이션을 **하나씩만** 돌리고 2초 동안의 지표를 읽었다:)*

```text
  .lft 만 (left 애니메이션)        RecalcStyleCount=122   LayoutCount=122
  .tfm 만 (translate 애니메이션)   RecalcStyleCount=0     LayoutCount=0
```

그림 해설 (한 단계씩):

- **좌표가 매 시각 같다.** 화면으로는 완전히 같은 움직임이다.
- **지표는 122 대 0.** 위 막대는 2초 동안 레이아웃을 122번 돌렸고 아래 막대는 **한 번도 안 돌렸다.**
- ★ **이것이 「눈으로는 못 잡는다」의 정확한 사례다.** 그래서 이 주제는 계측으로만 접지된다.

### (5) `will-change` — 무엇을 하고 무엇을 안 하나

**언제 쓰나** — 「애니메이션이 끊겨서 `will-change` 를 붙여 볼까」 할 때.

`will-change` 는 **「이 속성이 곧 바뀔 겁니다」라는 힌트**다. 브라우저가 미리 준비할 수 있게 해 준다.

*(Chrome 151 실측 — 2초 × 2판:)*

```text
  경우                                          Style      Layout     TaskDuration(s)
  transform 애니메이션, will-change 없음         0/0        0/0        0.002/0.003
  transform 애니메이션, will-change: transform   0/0        0/0        0.003/0.003
  left 애니메이션, will-change 없음              120/120    120/120    0.054/0.053
  left 애니메이션, will-change: left             120/120    120/120    0.052/0.053
  left 애니메이션, will-change: transform        120/120    120/120    0.052/0.049
```

그림 해설 (한 단계씩):

- ★ **다섯 줄에서 `will-change` 가 지표를 바꾼 자리가 없다.**
- **이미 합성 경로인 애니메이션에는 더 해 줄 것이 없다**(위 두 줄).
- **레이아웃 속성을 싸게 만들지도 못한다**(아래 세 줄). `will-change: left` 를 줘도 레이아웃은 그대로 120번 돈다.
- ★ 그러므로 **「끊기니까 `will-change` 를 붙인다」는 처방이 아니다.** 처방은 **속성을 바꾸는 것**이다((3)의 지도).

★ **대가는 분명하다 — 부작용이 딸려 온다.**

```text
  will-change: transform  또는 opacity 하나로

   ① 쌓임 맥락이 생긴다                  정본 22번 (실측 픽셀 있음)
   ② fixed·absolute 자손의 포함 블록을   정본 21번 (실측 좌표 있음)
      가로챈다
   ③ will-change: opacity 는             정본 55번 (이번 배치에서 실측)
      preserve-3d 를 깨뜨린다
```

- ①②는 [22번](../22-stacking-context-and-z-index/2-summary.md)·[21번](../21-position-and-containing-block/2-summary.md)이 정본이다. **21번은 `will-change: transform` 하나로 `fixed` 자식이 래퍼 안에 갇히는 것을 좌표로 재 놨다.**
- ③은 [55번](../55-3d-transforms/2-summary.md)에서 이번에 쟀다 — **`will-change: opacity` 는 3D 를 평탄화시키고 `will-change: transform` 은 안 시킨다.**\
  규칙은 한 문장이다: 「**그 속성이 부작용을 갖는 속성이면, 힌트만 줘도 그 부작용이 미리 적용된다.**」
- 명세가 직접 경고한다 — `will-change` 를 **많은 요소에 미리 뿌리지 말고, 바뀌기 직전에 켜고 끝나면 끄라**고 한다.

### (6) `contain` — 벽을 세운다

**언제 쓰나** — 큰 문서에서 한 구석의 변화가 **문서 전체의 레이아웃을 돌릴** 때.

`contain` 은 「**이 요소 안의 일은 밖으로 안 샙니다**」를 브라우저에 약속하는 것이다.

```text
  contain 의 값

  layout   안쪽 레이아웃이 바깥에 영향을 주지 않는다
  paint    안쪽이 상자 밖으로 안 그려진다 (자른다)
  size     바깥이 크기를 정할 때 안쪽을 안 본다  ★ 안쪽 내용이 없는 셈 친다
  style    카운터 등 스타일 효과를 가둔다
  content  = layout + paint + style
  strict   = layout + paint + style + size
```

*(Chrome 151 실측 — **뒤에 3000줄이 있는 문서**에서 상자 높이를 2초 동안 애니메이션. 2초 × 3판:)*

```text
  wrap 에 준 선언       Style           Layout          LayoutDuration(초)
  (없음)                120/120/120     120/120/120     0.195/0.190/0.202
  contain: layout       120/120/120     120/120/120     0.182/0.205/0.193   ← 차이 없음
  contain: size         120/120/120     120/120/120     0.148/0.147/0.143   ← 약 25% 감소
  contain: strict       120/120/121     120/120/121     0.022/0.025/0.025   ← 약 8배 감소 ★
  (같은 움직임을 transform 으로)  0/0/0    0/0/0          0.000/0.000/0.000  ← 아예 안 돈다
```

그림 해설 (한 단계씩):

- ★ **`contain: layout` 혼자서는 이 실험에서 아무 차이도 안 냈다.** 세 판의 폭(0.182\~0.205)이 대조군(0.190\~0.202)과 겹친다 — **잡음 안이다.**\
  이유는 **크기 변화가 밖으로 새기 때문**이다. 상자가 높아지면 뒤가 밀리고, 그건 `layout` 만으로는 못 막는다.
- **`size` 가 붙어야 벽이 선다.** `contain: strict` 에서 0.19초 → 0.024초로 **약 8배** 줄었다.
- ★★ **그런데 `transform` 은 0.000초다.** 「가두는 것」보다 「애초에 레이아웃을 안 돌리는 것」이 훨씬 세다.\
  **`contain` 은 레이아웃을 싸게 만드는 도구이지, `transform` 의 대체재가 아니다.**

**`size` 의 대가는 눈에 보인다.**

```html demo
<div class="card">담긴 글이 상자 높이를 정한다. 두 상자의 내용은 같다.</div>
<div class="card strict">담긴 글이 상자 높이를 정한다. 두 상자의 내용은 같다.</div>
<style>
  .card { width: 220px; border: 2px solid #94a3b8; margin: 8px; padding: 6px;
          font: 14px/20px system-ui; background: #eff6ff; }
  .strict { contain: strict; }
</style>
```

> **보이는 것** — 두 상자의 내용은 똑같은데 **아래 상자만 납작하게 찌그러지고 글자가 사라진다.** 위 상자는 두 줄짜리 글에 맞춰 높이가 잡히는데, 아래는 **안쪽 내용이 없는 셈** 쳐서 테두리와 안쪽 여백만 남은 껍데기가 되고, 넘친 글자는 `paint` 가둠에 잘려 안 보인다.\
> **바꿔 볼 것** — `contain: strict` → `contain: content`(**위 상자와 똑같아진다** — `size` 가 빠지면 내용이 높이를 정한다) · `contain: strict` 에 `height: 60px` 을 더하기(높이를 직접 주면 글자가 다시 보인다) · `contain: strict` → `contain: layout`(아무것도 안 바뀐다)

*(Chrome 151 headless 실측 — 두 상자의 `getBoundingClientRect()`:)*

```text
  .card           236.0 x 56.0      <- 글 두 줄(20px x 2) + 안쪽 여백 12 + 테두리 4
  .card.strict    236.0 x 16.0      <- 안쪽 내용이 0 인 셈: 여백 12 + 테두리 4
```

- **`size` 가둠은 「안쪽을 안 본다」는 약속**이라, 높이를 직접 주지 않으면 **0 으로 본다.**
- 그래서 `contain: strict` 는 **높이를 아는 카드**에만 쓴다. 모르면 `content`(= `strict` − `size`)를 쓴다.

### (7) `content-visibility` — 화면 밖은 아예 건너뛴다

**언제 쓰나** — 아주 긴 목록에서 초기 렌더를 줄일 때.

`content-visibility: auto` 는 **화면 밖에 있는 동안 그 요소의 안쪽 렌더링 작업을 건너뛴다**(가둠이 자동으로 걸린다).\
`contain-intrinsic-size` 로 **건너뛰는 동안 쓸 크기**를 알려 줘야 스크롤바가 튀지 않는다.

```css
.row {
  content-visibility: auto;
  contain-intrinsic-size: auto 16px;   /* 건너뛰는 동안 이 높이로 친다 */
}
```

- Baseline **newly**(2025-09-15)다 — 아직 widely 가 아니므로 대체 경로를 생각한다.
- ★ **이 문서에서는 효과를 제대로 못 쟀다.** 1500줄 문서로 초기 로드 지표를 비교했는데 `LayoutDuration` 이 0.010 → 0.004 로 줄긴 했지만 **신호가 잡음보다 크다고 말할 만큼 반복하지 않았다.** 그래서 **수치를 결론으로 싣지 않는다.**
- 55번의 평탄화 실험에서는 **`content-visibility: auto` 가 `preserve-3d` 를 깨뜨리지 않았다**([55번](../55-3d-transforms/2-summary.md)).

### (8) ★ 못 잰 것 — 레이어의 수와 메모리

**언제 쓰나** — 「`will-change` 를 남용하면 메모리가 는다」를 **근거와 함께** 말해야 할 때.

```text
  시도한 것                                    결과
  CDP LayerTree 도메인 (enable 후 이벤트 수집)  layerTreeDidChange 가 빈 목록
  --disable-gpu 를 뺀 Chrome 으로 재시도        마찬가지로 빈 목록
  Performance.getMetrics 의 JSHeapUsedSize     GC 때문에 흔들려 근거가 못 된다
                                               (레이어는 JS 힙에 없다)
  LayoutObjects 카운터                          누적 카운터라 페이지별 비교가 안 된다
```

- ★★ **그러므로 이 문서는 「레이어가 몇 장 생겼다」·「메모리가 얼마 늘었다」를 적지 않는다.**\
  **「`will-change` 남용은 메모리를 쓴다」는 명세와 문서의 주장**이고, 내가 잰 것이 아니다.
- 명세(css-will-change-1)는 남용을 직접 경고한다 — 「많은 요소에 미리 선언하지 말라」·「바뀌기 직전에 켜라」.
- **픽셀로 합성 여부를 판정하려 들지 않았다.** `--disable-gpu` 의 픽셀은 보장이 아니다.
- 잰 것과 못 잰 것의 경계를 다시 적으면 이렇다.

```text
  쟀다        주 스레드의 스타일·레이아웃·페인트·커밋·래스터 카운터
              레이아웃에 쓴 시간(LayoutDuration)
              will-change 가 이 카운터들을 안 바꾼다는 것
  못 쟀다     합성 레이어의 수 · 레이어 메모리 · GPU 시간
              content-visibility 의 효과 크기
```

## 형태 — 어디서 헷갈리나

### `will-change`

```css
/* 값은 '속성 이름' 이다 — 값이 아니라 */
.card { will-change: transform; }
.card { will-change: opacity, transform; }
.card { will-change: auto; }          /* 초기값 = 힌트 없음 */

/* 특수 값 */
.x { will-change: scroll-position; }
.x { will-change: contents; }         /* "안쪽이 자주 바뀐다" */
```

### `contain` 과 `content-visibility`

```css
.panel { contain: layout; }
.panel { contain: content; }          /* layout + paint + style */
.panel { contain: strict; }           /* + size — 높이를 직접 줘야 한다 */

.row { content-visibility: auto; contain-intrinsic-size: auto 16px; }
```

### 헷갈리는 자리 넷

```css
/* ① will-change 를 스타일시트에 박아 두고 안 끈다 — 명세가 경고하는 자리 */
.card { will-change: transform; }     /* 수백 개면 대가만 치른다 */

/* ② will-change 로 레이아웃 속성을 싸게 만들려 한다 — 안 된다 (실측) */
.x { will-change: left; }

/* ③ contain: strict 를 높이 모르는 상자에 쓴다 — 납작해진다 (실측: 56px -> 16px) */
.card { contain: strict; }

/* ④ contain: layout 만 주고 크기 변화가 갇히길 기대한다 — 이 실험에서 차이 없었다 */
.wrap { contain: layout; }
```

## 어디서 틀리나

### 1. 「부드럽게 안 움직인다」를 `will-change` 로 고치려 한다

**안 고쳐진다**((5) 실측: 다섯 경우 전부 지표가 같았다).\
처방은 **속성을 바꾸는 것**이다 — `left`/`top`/`width` 를 `transform` 으로, 페이드를 `opacity` 로.

### 2. `will-change` 를 스타일시트에 박아 둔다

명세가 직접 경고하는 자리다. 부작용(쌓임 맥락·포함 블록·평탄화)은 **즉시** 생기는데 이득은 없을 수 있다.\
쓸 거면 **바뀌기 직전에 JS 로 켜고 끝나면 끈다.**

### 3. `will-change: opacity` 가 3D 를 깨뜨리는 것을 모른다

[55번](../55-3d-transforms/2-summary.md)의 실측이다. **`will-change: transform` 은 안 깨뜨리는데 `opacity` 는 깨뜨린다.**\
카드 뒤집기에 페이드를 준비시키려다 뒤집기가 통째로 망가진다.

### 4. `contain: strict` 를 높이 모르는 상자에 쓴다

**납작해진다**((6) demo 실측: 56px → 16px). `size` 가둠이 「안쪽이 없는 셈」 치기 때문이다.\
높이를 모르면 `contain: content` 를 쓴다.

### 5. `contain: layout` 이 크기 변화까지 막아 줄 것이라 짐작한다

**이 실험에서는 차이가 없었다**((6)). 크기가 바뀌면 바깥이 따라 움직여야 하므로 `size` 가 필요하다.

### 6. 「`background-color` 는 페인트부터」라고 외워 둔다

**Chrome 151 에서는 스타일·레이아웃·페인트가 전부 0 이고 래스터만 돌았다**((3)).\
★ **어떤 속성이 합성 경로로 갈 수 있는지는 구현이 계속 늘려 왔다.** 표를 외우지 말고 **재는 법을 외운다.**

### 7. 스크린샷으로 비용을 판정하려 한다

**안 나온다**((4): 두 막대의 좌표가 매 시각 같았다).\
`--disable-gpu` 의 픽셀은 보장도 아니다 — **합성 여부를 픽셀로 판정하지 않는다.**

### 8. 「합성만 한다」와 「주 스레드 카운터가 0 이다」를 같은 말로 쓴다

**다른 말이다.** 이 문서가 잰 것은 뒤쪽이고, 앞쪽은 문서·명세의 주장이다((2)·(8)).

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 |
|---|---|
| `will-change` 가 **힌트**이고 브라우저가 무시해도 되는 것 | **명세**(css-will-change-1) |
| `will-change` 를 **남용하지 말라**는 것 | **명세**(직접 경고) |
| `will-change` 가 **쌓임 맥락·포함 블록**을 만드는 것 | **명세** — 실측은 [22번](../22-stacking-context-and-z-index/2-summary.md)·[21번](../21-position-and-containing-block/2-summary.md) |
| `contain` 각 값의 **의미**(layout·paint·size·style) | **명세**(css-contain-2) |
| `contain: strict` 가 내용 크기를 0 으로 보는 것 | **명세**(size containment) |
| **속성별 카운터 표**((3)) | ★★ **이 브라우저에서 잰 것**이다. 명세에는 이런 표가 없다 — 파이프라인 단계 자체가 구현의 것이다 |
| **`background-color` 가 주 스레드를 안 쓰는 것** | ★★ **관찰**. 널리 알려진 서술과 어긋난다. **다음 버전에서 다시 찍을 1순위** |
| **`filter`·`visibility` 가 스타일만 돌리는 것** | ★ **관찰** |
| **`will-change` 가 지표를 안 바꾸는 것** | ★ **관찰**. 「힌트를 무시해도 된다」는 명세와 모순되지 않는다 |
| **`contain` 의 시간 감소폭**(약 8배) | ★ **이 실험 설계의 값**이다. 문서 크기·구조가 달라지면 배수가 달라진다 |
| 「**`transform` 은 합성만 한다**」 | ★ **문서·명세의 주장.** 내가 잰 것은 「주 스레드 카운터가 0」까지다 |
| 레이어 수·레이어 메모리 | ★★ **못 쟀다**((8)) |

★ **흔들리는 칸 / 안 흔들리는 칸**

```text
  안 흔들린다   0 이냐 120 이냐 (세 판 전부 같았다) · 정지 대조군이 전 항목 0 인 것
                contain: strict 가 한 자릿수로 떨어지는 것
  흔들린다      120 과 121 사이 (프레임 경계) · LayoutDuration 의 소수 셋째 자리
                contain: layout 의 값 (대조군과 구간이 겹친다 = 차이 없음)
```

## 언제 쓰고 언제 안 쓰나

| 상황 | 무엇을 쓰나 |
|---|---|
| 요소를 움직인다 | **`transform`** — `left`/`top`/`margin` 이 아니라 |
| 크기를 바꾼다 | **`transform: scale()`** — `width`/`height` 가 아니라(내용도 같이 늘어나는 것을 감수) |
| 나타나고 사라진다 | **`opacity`** — `visibility`·`display` 보다 싸다 |
| 색을 바꾼다 | `background-color` 는 이 브라우저에서 쌌다. **다만 관찰이다** |
| 큰 문서의 한 구석만 자주 바뀐다 | `contain: content`(높이를 모르면) · `contain: strict`(높이를 알면) |
| 아주 긴 목록 | `content-visibility: auto` + `contain-intrinsic-size` (Baseline **newly**) |
| 무거운 애니메이션이 끊긴다 | **속성을 바꾼다.** `will-change` 는 처방이 아니다(실측) |
| `will-change` 를 정말 쓸 때 | **바뀌기 직전에 켜고 끝나면 끈다.** 스타일시트에 박아 두지 않는다 |

판단 규칙 두 줄.

- **「이 속성이 어느 공정에 처음 닿는가」로 고른다.** 지도는 (3)의 표다.
- **재지 않은 성능 주장을 하지 않는다.** 이 주제에서 가장 쉽게 나는 사고가 그것이다.

## 핵심 문장

- 파이프라인은 **스타일 → 레이아웃 → 페인트 → 합성**이고, **위쪽 공정이 돌면 아래는 전부 따라 돈다.**
- **`transform` 과 `opacity` 는 주 스레드 카운터 여섯 칸이 전부 0 이었다** — 정지 대조군과 한 칸도 다르지 않다(실측).
- **`left` 와 `transform` 으로 만든 같은 이동은 좌표가 매 시각 같은데 `LayoutCount` 가 122 대 0** 이었다 — **눈으로는 못 잡는다.**
- ★ **`background-color` 는 이 브라우저에서 주 스레드를 안 썼다**(래스터만 120) — 널리 알려진 서술과 어긋난다.
- **`will-change` 는 다섯 경우 전부에서 지표를 안 바꿨다** — 끊김의 처방이 아니다. 처방은 **속성을 바꾸는 것**이다.
- **`will-change` 의 대가는 확실하다** — 쌓임 맥락·포함 블록·(`opacity` 면) 3D 평탄화가 **즉시** 딸려 온다.
- **`contain: layout` 만으로는 이 실험에서 차이가 없었고, `size` 가 붙은 `strict` 에서 약 8배 줄었다.**\
  그런데 **같은 움직임을 `transform` 으로 하면 0 초**다 — 가두는 것보다 안 돌리는 것이 세다.
- ★★ **레이어 수와 메모리는 못 쟀다.** 「남용하면 메모리가 는다」는 명세의 주장이지 내 측정이 아니다.

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 56번) · 「버전·지원 기준」의 Baseline 표
- [`../../../../../../history/web/04-브라우저-엔진.md`](../../../../../../history/web/04-브라우저-엔진.md) — ★ **엔진의 계보와 구조는 거기가 정본이다.** 여기는 **「어느 속성이 어느 단계를 다시 돌리나」라는 실무 판정**만.
- [53번 주제 — `@keyframes` 와 `animation`](../53-keyframes-and-animation/2-summary.md) — **그쪽은 「무엇이 언제 움직이나」, 여기는 「그게 어느 공정을 다시 돌리나」.**
- [54번 주제 — `transform` 2D](../54-transform-2d-and-origin/2-summary.md) — ★ **「`transform` 이 레이아웃을 안 바꾼다」는 좌표 실측이 거기 있다.** 여기는 **그 결과 비용이 어떻게 갈리나**.
- [52번 주제 — `transition`](../52-transition/2-summary.md) — 「비싼 속성을 전환한다」 항목이 이 문서를 정본으로 가리킨다.
- [21번 주제 — `position` 과 포함 블록](../21-position-and-containing-block/2-summary.md) — ★ **`will-change: transform` 이 `fixed` 의 포함 블록을 가로채는 것의 정본.** 좌표 실측이 거기 있다.
- [22번 주제 — 쌓임 맥락과 `z-index`](../22-stacking-context-and-z-index/2-summary.md) — ★ **`will-change`·`contain: paint` 가 쌓임 맥락을 만드는 것의 정본.**
- [55번 주제 — 3D 변환](../55-3d-transforms/2-summary.md) — ★ **`will-change: opacity` 가 `preserve-3d` 를 깨뜨리는 실측이 거기 있다.** `contain: paint` 는 안 깨뜨렸다.
- [47번 주제 — `filter`·`backdrop-filter`](../47-filter-and-backdrop-filter/2-summary.md) — 필터가 「안쪽을 한 장으로 누르는」 일의 정본
- [목록의 **60번 주제**](../60-prefers-reduced-motion/)(`prefers-reduced-motion`) — 모션 접근성. 이 문서의 demo 에는 넣지 않았다.
- [`reference/render-rules.md`](../../../../../../reference/render-rules.md) — 이 문서의 `demo` 블록 규칙

## 용어 풀이

- **스타일 재계산(style recalculation)** — 선택자를 다시 매칭하고 캐스케이드를 풀어 계산값을 만드는 공정. Chrome 의 카운터 이름은 `RecalcStyleCount`.
- **레이아웃(layout)** — 상자의 크기와 자리를 정하는 공정. 카운터는 `LayoutCount`, 시간은 `LayoutDuration`.
- **페인트(paint)** — 그리기 명령 목록을 만드는 공정. Tracing 이벤트 `Paint`·`PrePaint`.
- **래스터(raster)** — 그리기 명령을 실제 픽셀로 굽는 일. Tracing 이벤트 `RasterTask`.
- **합성(compositing)** — 구운 조각들을 옮기고 겹쳐 화면 한 장으로 만드는 일.
- **합성 레이어(composited layer)** — 따로 구워 두고 옮기기만 하는 조각. **이 문서에서는 수와 메모리를 못 쟀다.**
- **`will-change`** — 「이 속성이 곧 바뀐다」는 **힌트**. 브라우저가 무시해도 된다. 부작용은 즉시 생긴다.
- **가둠(containment)** — 「이 요소 안의 일은 밖에 영향을 주지 않는다」는 약속. `layout`·`paint`·`size`·`style` 네 축.
- **`contain: strict`** — `layout + paint + style + size`. **내용 크기를 0 으로 본다** — 높이를 직접 줘야 한다.
- **`content-visibility: auto`** — 화면 밖인 동안 안쪽 렌더링을 건너뛴다. Baseline **newly**.
- **`contain-intrinsic-size`** — 건너뛰는 동안 쓸 가상 크기. 없으면 스크롤바가 튄다.
- **`Performance.getMetrics`** — CDP 의 누적 카운터. 전후 차이를 본다.
- **`Tracing` 도메인** — CDP 의 이벤트 수집. `Performance.getMetrics` 에 없는 **페인트 층**이 여기서 보인다.

---

## 더 들어가면

- **이 표를 외우지 말고 재는 법을 외운다.** 어떤 속성이 합성 경로로 갈 수 있는지는 구현이 계속 늘려 왔고, 이 문서의 `background-color` 결과가 그 증거다.
- Chrome DevTools 의 Performance 패널이 같은 정보를 그림으로 보여 준다 — 이 문서는 **headless 에서 같은 데이터를 CDP 로 직접 읽은 것**이다.
- `PerformanceObserver` 의 `long-animation-frame` 엔트리로 **긴 프레임이 무엇 때문이었나**를 페이지 안에서 볼 수 있다. 이 문서에서는 **쓰지 않았다.**
- 레이아웃이 도는 속성이라도 **바뀌는 요소가 하나뿐이고 문서가 작으면** 체감이 없다. (3)의 표는 **횟수**이지 **비용의 크기**가 아니다 — 비용 크기는 (6)의 `LayoutDuration` 쪽에서 보인다(3000줄 문서에서 0.19초).
- `contain: paint` 는 [55번](../55-3d-transforms/2-summary.md)의 실측에서 **`overflow: hidden` 과 달리 3D 를 안 깨뜨렸다.** 「자르기」라는 같은 일을 하는데 부작용이 다르다 — **목적이 다른 선언이기 때문**이다.
- `will-change` 를 JS 로 켜고 끄는 패턴은 이렇다. 켜고 **한 프레임 뒤에** 애니메이션을 시작해야 준비할 틈이 생긴다.

```js
el.style.willChange = 'transform';
requestAnimationFrame(() => { /* 여기서 애니메이션 시작 */ });
el.addEventListener('transitionend', () => { el.style.willChange = 'auto'; });
```

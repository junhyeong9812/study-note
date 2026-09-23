# css/syntax/32 — 논리 속성과 글쓰기 방향(`writing-mode`·`direction`·`inline-size`) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 좌표·치수는 Google Chrome 151.0.7922.173 headless 에서 실제로 렌더해 `getBoundingClientRect()` 로 잰 값**이고,
> **논리 속성이 어느 물리 속성으로 풀렸는지는 `getComputedStyle` 로 따로 읽었다.** 단위는 px 다.\
> 좌표는 별말이 없으면 **부모의 바깥 왼쪽 위 모서리를 원점**으로 한 값이다.\
> 규칙은 [CSS Logical Properties and Values Level 1](https://drafts.csswg.org/css-logical-1/) 과 [CSS Writing Modes Level 4](https://drafts.csswg.org/css-writing-modes-4/) 로, 지원 상태는 `api.webstatus.dev` 의 Baseline 데이터로 접지했다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 두 축의 정의

**인라인 축 / 블록 축**

- **인라인 축** — **글자가 이어지는 방향**의 축. 펜이 나아가는 쪽.
- **블록 축** — **줄(문단)이 쌓이는 방향**의 축. 인라인 축에 직각이다.
- 한국어 가로쓰기에서만 그것이 각각 가로·세로와 **우연히 일치**한다.

**각각 무엇을 정하나**

- `writing-mode` — **두 축을 둘 다** 정한다(`horizontal-tb` / `vertical-rl` / `vertical-lr` …).
- `direction` — **인라인 축 안에서의 시작 쪽**만 정한다(`ltr` / `rtl`).

**축 자체를 바꾸는 것**

- **`writing-mode`** 다. `direction` 은 이미 정해진 축 위에서 앞뒤만 뒤집는다(3번이 그 실측).

**`horizontal-tb` 에서 풀리는 값**

- `inline-size` → **`width`** · `block-size` → **`height`**.
- *(실측: 그 판의 `getComputedStyle` 이 `width=100px height=40px` 를 돌려줬다. `vertical-rl` 판에서는 `width=40px height=100px` 로 **뒤바뀐다**.)*

### 2. ★ 똑같은 선언, 다섯 판

**실행 결과** (Chrome 151 headless — 부모 300×200 에 `display: flow-root`, 자식의 선언은 다섯 판 모두 동일)

```text
판                             상자 (x,y)   w × h     물리로 풀린 값
① horizontal-tb + ltr          (20,10)     114×40    width=100 height=40
                                                      margin-left=20  margin-top=10
                                                      border-left=6   padding-right=8
② writing-mode: vertical-rl    (250,20)     40×114   width=40  height=100
                                                      margin-top=20   margin-right=10
                                                      border-top=6    padding-bottom=8
③ writing-mode: vertical-lr    (10,20)      40×114   width=40  height=100
                                                      margin-left=10  margin-top=20
                                                      border-top=6    padding-bottom=8
④ direction: rtl               (166,10)    114×40    width=100 height=40
                                                      margin-top=10   margin-right=20
                                                      border-right=6  padding-left=8
⑤ vertical-rl + direction: rtl (250,66)     40×114   width=40  height=100
                                                      margin-right=10 margin-bottom=20
                                                      border-bottom=6 padding-top=8
```

**`margin-inline-start` 가 되는 물리 마진**

- ① **`margin-left`** · ② **`margin-top`** · ④ **`margin-right`** · ⑤ **`margin-bottom`**.

**네 답을 모으면**

- ★ **선언 하나가 `writing-mode`/`direction` 조합에 따라 네 물리 방향을 전부 한 번씩 돈다.**
- 그래서 **「왼쪽 여백」이 아니라 「펜이 시작하는 쪽 여백」** 으로 읽어야 한다.
- `border-inline-start` 도 같이 돈다 — `border-left` → `border-top` → `border-right` → `border-bottom`.

**`getComputedStyle` 로 확인되는가**

- **된다.** ★ **논리 속성은 계산값 단계에서 물리 속성으로 풀려서** 돌아온다.
- 그래서 「내 논리 선언이 어디로 갔나」를 **물어볼 수 있다** — 이 주제의 진단 방법이다.
- 단 **`text-align: start` 같은 값 쪽 논리는 안 풀린다**(7번). 속성 이름의 논리와 값의 논리가 다르게 취급된다.

### 3. `direction` 과 `writing-mode` 는 같은 축인가

**x 가 같고 y 만 다르다는 것**

- ★ **`direction` 이 블록 축을 안 건드렸다**는 뜻이다.
- ②와 ⑤는 둘 다 `vertical-rl` 이라 **블록 축이 가로(오른쪽→왼쪽)** 이고, 그 축에서의 위치가 x=250 으로 같다.
- 달라진 것은 **인라인 축(세로)에서의 시작 쪽**뿐이다 — `ltr` 이면 위(y=20), `rtl` 이면 아래(y=66).
- 즉 **둘은 서로 다른 축을 만진다.** 「둘 다 방향을 바꾸는 속성」으로 뭉뚱그리면 이 실험을 설명할 수 없다.

**아랍어와 일본어 세로쓰기**

- 아랍어·히브리어 — **`direction: rtl`**(가로쓰기인 채로 시작이 오른쪽).
- 일본어·중국어 전통 조판 — **`writing-mode: vertical-rl`**(축 자체가 돈다).

**동시에 쓸 수 있는가**

- **있다.** ⑤가 그 조합이고 결과가 ②·④ 어느 쪽과도 다르다.

**RTL 은 CSS 인가 마크업인가**

- **마크업(`<html dir="rtl">`)이 표준**이다.
- CSS 의 `direction` 은 **레이아웃만** 돌린다. `dir` 속성은 폼 컨트롤·스크린 리더·텍스트 선택 같은 것까지 따라온다.

### 4. ★ 물리와 논리를 같이 쓰면

**실행 결과** (Chrome 151 headless — 부모 300px, 상자 60px)

```text
판                                                          상자 x   계산값
① ltr: margin-inline-start:20 → margin-left:80 (물리가 뒤)     80     margin-left=80
② ltr: margin-left:80 → margin-inline-start:20 (논리가 뒤)     20     margin-left=20
③ rtl: margin-inline-start:20 → margin-left:80                220     margin-left=80
                                                                     margin-right=20
④ ltr: margin-inline-start:20 + margin-top:25                  20     margin-left=20
                                                                     margin-top=25
⑤ ltr: b{margin-left:80} + .hi{margin-inline-start:20}         20     margin-left=20
```

**`.a`(물리가 뒤)의 `margin-left`**

- **80px.** 나중 선언이 이겼다.

**`.b`(논리가 뒤)**

- **20px.** 역시 나중 선언이 이겼다.
- ①과 ②의 차이가 **선언 순서 하나뿐**이라는 것이 이 실험의 핵심이다.

**`.c`(rtl) 안에서는**

- **둘 다 산다.** `margin-left=80`, `margin-right=20`.
- `rtl` 이라 `margin-inline-start` 가 **`margin-right` 로 풀려** 서로 다른 칸을 채웠기 때문이다.
- 상자 x=220 = 300 − 60 − 20(오른쪽 마진)과 맞는다.

**`.d`**

- **둘 다 산다.** `margin-left=20`, `margin-top=25`. 애초에 다른 축이다.

**「논리와 물리는 캐스케이드로 안 싸운다」는 맞는가**

- ★ **틀렸다.** **같은 물리 속성으로 풀리면 정확히 캐스케이드로 싸운다** — 순서와 명시도가 그대로 적용된다([01번](../01-cascade-and-priority/)·[02번](../02-specificity/)).
- **둘 다 사는 것은 서로 다른 물리 칸을 채울 때뿐**이다(③④).

**명시도가 다르면**

- **높은 쪽이 이긴다.** ⑤에서 타입 선택자(`b`, 명시도 0,0,1)의 물리 선언이 앞에 있어도, 클래스 선택자(`.hi`, 0,1,0)의 논리 선언이 이겨 20px 가 됐다.

**언어를 바꿨을 때 터지는 경우**

- ★ **③이다.** `ltr` 에서는 논리 쪽이 져서 조용하다가, **`rtl` 로 바꾸는 순간 둘 다 살아나** 양쪽에 여백이 생긴다.
- 「언어를 바꿨더니 여백이 두 배가 됐다」는 사고가 이것이다.
- 실무 규칙 — **한 속성 그룹에서는 물리든 논리든 한쪽으로 통일한다.**

### 5. ★ flex 의 주축이 도는가

**실행 결과** (Chrome 151 headless — 컨테이너 200×200, 항목 40×30 둘. `flex-direction: row` 는 네 판 모두 동일)

```text
판                        항목 좌표                결론
horizontal-tb (기본)      1:(0,0)   2:(40,0)      가로로 늘어섬
writing-mode: vertical-rl 1:(160,0) 2:(160,30)    세로로 쌓임 (오른쪽 끝에서)
writing-mode: vertical-lr 1:(0,0)   2:(0,30)      세로로 쌓임 (왼쪽 끝에서)
direction: rtl            1:(160,0) 2:(120,0)     가로인 채로 오른쪽부터
```

**`.f` 안의 항목**

- **가로로 늘어선다**(x 가 0, 40).

**`.f.v`(`vertical-rl`) 안에서는**

- **세로로 쌓인다**(y 가 0, 30). `flex-direction` 은 `row` 그대로다.

**`vertical-lr` 이면**

- **역시 세로로 쌓이는데 x 가 0** 이다 — 줄이 왼쪽에서 시작한다.

**`direction: rtl` 이면**

- **가로인 채로 오른쪽부터** 채워진다(x 가 160, 120). 축은 안 돌고 시작 쪽만 바뀌었다.

**`row` 를 다시 정의하면**

- **`flex-direction: row` = 주축이 인라인 축.**
- **`flex-direction: column` = 주축이 블록 축.**
- [24번](../24-flexbox-axes/)의 「주축」은 처음부터 논리 축이었다. 이름이 `row`/`column` 이라 물리로 읽히는 것뿐이다.
- 그래서 `justify-content: flex-start` 가 `vertical-rl` 에서는 **「위」** 다.

**x 가 160 인 이유**

- 교차축(블록 축)이 **오른쪽에서 시작**하기 때문이다. 200 − 40 = 160 이 항목의 왼쪽 좌표다.

### 6. `inset-*`

**실행 결과** (Chrome 151 headless — 부모 200×120, `inset-block-end: 10px; inset-inline-start: 15px`)

```text
판                 상자 (x,y)   계산값
horizontal-tb     (15, 90)     left=15px  top=90px  right=145px bottom=10px
vertical-rl       (10, 15)     left=10px  top=15px  right=150px bottom=85px
```

**`horizontal-tb` 에서**

- **(15, 90).** `inset-inline-start` → `left=15px`, `inset-block-end` → `bottom=10px`(그래서 `top=90` = 120 − 20 − 10).

**`vertical-rl` 에서**

- **(10, 15).** `inset-block-end` → **`left=10px`**, `inset-inline-start` → **`top=15px`**.
- 두 선언이 **완전히 다른 물리 방향**으로 갔다.

**`inset: 10px` 는**

- ★ **물리 단축**이다. `top right bottom left` 순서의 네 방향 단축이고, **이름만 새것이라 논리로 오해하기 쉽다.**

**논리 단축의 이름**

- **`inset-inline`**(인라인 축 양쪽) · **`inset-block`**(블록 축 양쪽).
- *(실측: `inset-inline: 5px` 와 `inset: 10px` 둘 다 `cssRules` 에 정상으로 담긴다 — **이름만 봐서는 구분되지 않는다.**)*

### 7. `text-align: start` / `end`

**실행 결과** (Chrome 151 headless — 컨테이너 200px, 글자 영역은 `Range.selectNodeContents()` 의 사각형으로 쟀다)

```text
판                        글자 왼쪽 x   계산값 text-align
ltr + text-align: start        0        start
ltr + text-align: end        176        end
rtl + text-align: start      160        start
rtl + text-align: left         0        left
```

**네 경우의 정렬**

- `ltr + start` — **왼쪽**(x=0).
- `ltr + end` — **오른쪽**(x=176).
- `rtl + start` — **오른쪽**(x=160).
- `rtl + left` — **왼쪽**(x=0).

**`.c` 와 `.d` 가 갈리는 이유**

- **`start` 는 논리 값이고 `left` 는 물리 값**이기 때문이다.
- `rtl` 에서 인라인 축의 시작은 오른쪽이므로 `start` 는 오른쪽이 되고, `left` 는 화면의 왼쪽에 고정된다.

**`getComputedStyle(c).textAlign`**

- **`start` 그대로다.** ★ **그것으로는 어느 쪽인지 알 수 없다.**

**2번과 무엇이 다른가**

- 2번의 `margin-inline-start` 는 **계산값 단계에서 `margin-right` 로 풀려** 돌아왔다.
- `text-align: start` 는 **속성 이름이 물리·논리 구분이 없고 값 쪽에만 논리판이 있어**, 값이 그대로 남는다.
- 그래서 **`text-align` 은 좌표를 재야만 진단된다.** 같은 「논리」인데 진단 방법이 다르다.

### 8. 대응표

**실행 결과** (Chrome 151 headless — 논리 마진 넷에 1\~4px, 논리 패딩 넷에 5\~8px 를 주고 물리 칸을 읽었다)

```text
준 값   inline-start=1  inline-end=2  block-start=3  block-end=4
        (패딩은 5 / 6 / 7 / 8)

판            margin  L / T / R / B        padding L / T / R / B
horizontal-tb         1 / 3 / 2 / 4                5 / 7 / 6 / 8
vertical-rl           4 / 1 / 3 / 2                8 / 5 / 7 / 6
```

**`vertical-rl` 에서 네 마진**

- `margin-inline-start` → **`margin-top`**(1이 위로 갔다)
- `margin-inline-end` → **`margin-bottom`**(2가 아래로)
- `margin-block-start` → **`margin-right`**(3이 오른쪽으로)
- `margin-block-end` → **`margin-left`**(4가 왼쪽으로)

**`width`/`height` 의 논리판**

- **`inline-size`** / **`block-size`**.

**`left` 의 논리판**

- **`inset-inline-start`**(가로쓰기 `ltr` 기준). `vertical-rl` 에서는 `inset-block-end` 가 `left` 가 된다(6번).

**두 단축**

- **`margin-inline`** — 인라인 축 양쪽(`ltr` 가로쓰기에서 `margin-left`/`margin-right`).
- **`margin-block`** — 블록 축 양쪽(`margin-top`/`margin-bottom`).

### 9. 유효하지 않은 것

**실행 결과** (Chrome 151 headless — `cssRules` 로 읽은 규칙 본문)

```text
#L1 { }                               <- margin-inline-top: 4px   버려졌다
#L2 { margin-inline-start: 20px; }    <- 정상 (대조군)
#L3 { }                               <- inline-size: auto-ish    버려졌다
#L4 { writing-mode: sideways-rl; }    <- 담긴다
#L5 { inset-inline: 5px; }            <- 담긴다 (논리 단축)
#L6 { inset: 10px; }                  <- 담긴다 (물리 단축)
```

**담기는 것**

- **`writing-mode: sideways-rl`** 과 **`inset-inline: 5px`**. 앞의 둘은 버려진다.

**`.a` 가 버려지는 이유**

- ★ **「그런 속성이 없다」** 이다. `margin-inline-top` 은 **인라인 축과 물리 방향을 섞은 이름**이라 애초에 존재하지 않는다.
- 「미지원」이 아니다 — 미래 브라우저에서도 안 생긴다. 논리 이름은 `inline-start`/`inline-end`/`block-start`/`block-end` 넷뿐이다.

**`.c` 가 담겼다는 것이 동작한다는 뜻인가**

- ★ **아니다.** 「담겼다」와 「먹었다」는 다른 검사다([31번](../31-intrinsic-sizing-and-aspect-ratio/) 9번이 그 정본 사례 — `aspect-ratio: 0 / 1` 이 담기고도 아무 일을 안 했다).
- `sideways-rl` 을 쓰려면 **좌표를 재서** 실제로 도는지 확인한다.

**`writing-mode` 를 `transition` 에 태우면**

**실행 결과** (Chrome 151 + CDP — `transition: writing-mode 1s linear, width 1s linear` 를 건 상자에서 두 값을 **동시에** 바꾸고 시각마다 계산값을 읽었다)

```text
transitionProperty = "writing-mode, width"     <- 선언은 받아들여진다
시작       wm=horizontal-tb   w=200px
0.1s 시점  wm=vertical-rl     w=210px          <- wm 은 이미 끝나 있다
0.5s 시점  wm=vertical-rl     w=250px
0.8s 시점  wm=vertical-rl     w=279.984px      <- width 는 아직 보간 중
```

- ★ **선언은 받아들여지고 `transitionProperty` 에도 들어가는데, `writing-mode` 값은 0.1초 시점에 이미 끝까지 가 있었다.**
- 같이 건 `width` 는 같은 시각에 210px 로 **보간 중**이었다 — **한 줄 안에서 한쪽만 전환된 것**이다.
- 키워드 값에는 중간값이 없기 때문이다. 「전환이 걸린 것처럼 보이는데 안 걸린」 전형이다.
- 어느 속성이 어느 단계를 다시 돌리는지는 [목록의 **56번 주제**](../56-rendering-pipeline-and-will-change/), 무엇이 보간되는지는 [52번](../52-transition/)이 정본이다.

### 10. 다른 주제와 잇기

**유니코드·문자 인코딩**

- [`foundations/data-representation/`](../../../../data-representation/). 이 문서는 **물리 축과 논리 축이 갈리는 CSS 규칙**만 다룬다.

**[24번](../24-flexbox-axes/)의 「축이 돈다」의 왜**

- 이 문서의 **(5) flex 의 주축이 `writing-mode` 에서 어떻게 도나** 다. 24번은 실측 한 줄만 남기고 정본을 여기로 넘겼다.

**논리와 물리가 겨루는 규칙**

- [01번](../01-cascade-and-priority/)(캐스케이드)과 [02번](../02-specificity/)(명시도). 4번이 그 규칙을 그대로 받는다.

**`row-gap` 의 기준**

- ★ **이름은 물리인데 동작은 논리다.** `row-gap` 은 「가로줄 사이」가 아니라 **「블록 축 방향 간격」** 이다([26번](../26-flex-wrap-gap-order/)).
- 이름만 옛것이 남은 자리라 세로쓰기에서 헷갈린다.

**Baseline 과 결론**

- 논리 속성 — **widely**(newly 2021-09-20 → widely 2024-03-20). `writing-mode` — **widely**(2017-03-27 → 2019-09-27).
- 결론 — ★ **조건 없이 쓴다.** 새로 쓰는 여백·크기·테두리는 논리 속성을 기본값으로 삼고, RTL 용 스타일시트를 따로 만들던 관행(`[dir="rtl"] .x { … }`)은 **한 줄로 대체된다.**

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 같은 논리 선언 여섯 개, `writing-mode`/`direction` 다섯 조합 | 부모만 바꾸고 자식 선언은 고정 | 2 | 2번 표 |
| `direction` 이 블록 축을 안 건드리는가 | ②와 ⑤의 x 비교 | 1 | 3번 |
| 논리 마진·패딩 여덟 개의 물리 대응 | 1\~8px 를 각각 주고 계산값 읽기 | 1 | 8번 표 |
| 물리·논리 충돌 다섯 판 | 순서·방향·명시도를 바꿔 | 1 | 4번 표 |
| flex 주축이 도는가 | `flex-direction: row` 고정, 네 판 | 1 | 5번 표 |
| `inset-*` 두 판 | `horizontal-tb` / `vertical-rl` | 1 | 6번 표 |
| `text-align: start`/`end` 네 판 | 글자 영역을 `Range` 로 측정 | 1 | 7번 표 |
| 유효하지 않은 속성·값 | `cssRules` 로 여섯 규칙 | 1 | 9번 표 |
| Baseline | `api.webstatus.dev` feature API 조회 | 1 | `logical-properties` widely 2021-09-20 → 2024-03-20 · `writing-mode` widely 2017-03-27 → 2019-09-27 · `text-align` widely 2015-07-29 → 2018-01-29 |
| `demo` 블록 2개 | 완성된 문서에서 `extract-demo-blocks.py --render` 로 재추출해 재실행 | 1 | 수치 일치 |

**측정을 위해 한 일** — 2번의 부모에 `display: flow-root` 를 줬다. 안 주면 자식의 `margin-block-start` 가 [18번](../18-margin-collapsing/)의 상쇄로 부모 밖으로 새어 나가 좌표가 흐려진다(실제로 첫 판이 그랬다).
**구현에 의존하는 항목** — 모든 구체 좌표 · `sideways-rl` 이 이 Chrome 에서 담기는 것.
**「담겼다」를 「먹었다」로 적지 않았다** — 9번의 `sideways-rl` 은 담긴 것까지만 확인했고 **동작은 재지 않았다.**
**엔진은 Chrome 하나다** — Firefox 는 이 환경에서 headless 스크린샷이 산출되지 않아 엔진 차이를 주장하지 않았다.

## 이 주제가 답하려는 질문

1. 똑같은 선언이 어느 방향으로 가는가 — **`writing-mode`/`direction` 조합에 따라 네 물리 방향을 전부 돈다**(2번).
2. 물리와 논리를 같이 쓰면 — **같은 물리 속성으로 풀리면 캐스케이드로 싸우고, 다른 방향이면 둘 다 산다**(4번).
3. flex 의 주축은 어떻게 도는가 — **`row` 는 인라인 축이라 `vertical-rl` 에서 세로가 된다**(5번).

## 구현 세부사항 대 언어 보장

- **명세가 보장하는 것** — 인라인/블록 축의 정의 · `writing-mode` 가 두 축을 정하고 `direction` 은 인라인 축 안에서만 앞뒤를 바꾸는 것 · 논리→물리 매핑 규칙 · 논리와 물리가 같은 물리 속성으로 풀릴 때 캐스케이드로 겨루는 것 · `inset` 이 물리 단축인 것 · `margin-inline-top` 같은 이름이 **존재하지 않는 것**.
- **이 Chrome 의 관찰인 것** — 모든 구체 좌표 · `sideways-rl` 이 `cssRules` 에 담기는 것 · 버려진 선언이 빈 상자로 보이는 표현 형식.
- **관찰을 보장으로 적지 않았다** — `sideways-rl` 은 **담긴 것까지만** 적었다. 동작 여부는 재지 않았으므로 「쓸 수 있다」고 쓰지 않았다.

## 용어 풀이

- **인라인 축(inline axis)** — 글자가 이어지는 방향의 축. 펜이 나아가는 쪽.
- **블록 축(block axis)** — 줄이 쌓이는 방향의 축. 인라인 축에 직각이다.
- **inline-start / inline-end** — 인라인 축의 시작·끝. `direction` 이 앞뒤를 뒤집는다.
- **block-start / block-end** — 블록 축의 시작·끝. `writing-mode` 가 정한다.
- **`writing-mode`** — 두 축을 **둘 다** 정한다. `horizontal-tb`(기본) / `vertical-rl` / `vertical-lr` / `sideways-*`.
- **`direction`** — 인라인 축 안에서의 시작 쪽. `ltr`(기본) / `rtl`. **축 자체는 안 바꾼다.**
- **논리 속성(logical property)** — `inline-size`·`margin-inline-start` 처럼 **글의 방향** 기준. 계산값 단계에서 물리로 풀린다.
- **물리 속성(physical property)** — `width`·`margin-left` 처럼 **화면의 방향** 기준.
- **`inset`** — 이름은 새것인데 **물리 네 방향 단축**이다. 논리 단축은 `inset-inline`/`inset-block`.
- **`text-align: start`/`end`** — **값 쪽에만 논리판이 있는** 드문 경우. 계산값이 안 풀려서 좌표로만 진단된다.
- **RTL(right-to-left)** — 오른쪽에서 왼쪽으로 쓰는 문자 체계. 실무에서는 `<html dir="rtl">` 로 켠다.
- **Baseline widely** — 주요 엔진에 들어간 지 충분히 오래돼 조건 없이 써도 되는 상태. 논리 속성은 2024-03-20 부터다.

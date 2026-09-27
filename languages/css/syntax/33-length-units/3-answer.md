# css/syntax/33 — 길이 단위: `px`·`em`·`rem`·`%`·`ch`·`ex` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 수치는 Google Chrome 151.0.7922.173 headless 에서 실제로 렌더해 `getComputedStyle`·`getBoundingClientRect()`·`elementFromPoint` 로 잰 값**이다. 단위는 px 다.\
> **손으로 계산해 유도한 수치는 없다.** 규칙은 [CSS Values and Units Level 4](https://drafts.csswg.org/css-values-4/) 로 접지했다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 같은 `2em` 이 두 숫자가 된다

**실행 결과** (Chrome 151 headless)

```text
  #p { font-size: 20px }
  #c { font-size: 2em; width: 2em; padding-left: 2em;
       border-left: 0.5em solid; margin-left: 2em }

  html  font-size          = 16px
  #p    font-size          = 20px
  #c    font-size (2em)    = 40px     <- 부모 20px x 2
  #c    width (2em)        = 80px     <- ★ 자기 40px x 2
  #c    padding-left (2em) = 80px
  #c    border-left (0.5em)= 20px
  #c    margin-left (2em)  = 80px
```

**왜 그런가**

- **`font-size` 의 `em` 만 부모를 본다.** 자기 `font-size` 를 정하는 중이므로 자기 값을 쓸 수 없다.
- 그것이 `40px` 으로 확정된 **뒤에** 나머지 `em` 이 풀린다. 그래서 전부 `40 × n` 이다.
- 한 문장으로: **「`font-size` 는 자기가 정해지기 전이라 부모를 보고, 나머지는 정해진 뒤라 자기를 본다.」**
- 부작용 — `font-size: 2em` 을 쓴 규칙에서 `padding: 2em` 은 **부모 글꼴의 4배**가 된다.

### 2. `em` 사슬을 네 겹 내려간다

**실행 결과**

```text
  body { font-size: 32px }   (html { font-size: 2rem } 로 루트가 32px 이었다)
  .chain { font-size: 1.25em }

    1겹 = 40px
    2겹 = 50px
    3겹 = 62.5px
    4겹 = 78.125px
```

**왜 그런가**

- `em` 은 **한 칸 위만** 본다. 그런데 그 한 칸 위도 `em` 이라 사슬이 이어지며 곱해진다.
- `1.25rem` 으로 바꾸면 **네 겹이 전부 같은 값**이 된다 — 루트 하나만 보므로 사슬이 끊긴다.\
  같은 성질을 [04번](../04-value-processing-stages/2-summary.md)이 `1.5em` 중첩 목록 demo 로 이미 쟀다(16 → 24 → 36 → 54px).
- 외울 것은 숫자가 아니라 「**`em` 은 사슬을 만들고 `rem` 은 끊는다**」는 성질이다.

### 3. `%` 의 기준을 속성별로 가른다

**실행 결과** (포함 블록: width 400px / height 200px / font-size 20px)

```text
  선언                계산값     기준
  ------------------  ---------  --------------------------
  width: 50%          200px      부모 content '폭'
  height: 50%         100px      부모 content '높이'
  padding-top: 10%    40px       ★ 부모 content '폭'
  margin-left: 10%    40px       부모 content '폭'
  font-size: 150%     30px       ★ '부모'의 font-size
  line-height: 150%   30px       ★ '자기'의 font-size
```

**왜 그런가**

- **자기 자신을 기준으로 삼는 것은 `line-height` 다.** 나머지 다섯은 전부 부모(포함 블록)를 본다.
- 근거 실측 — `font-size: 10px` 인 요소에 `line-height: 150%` 를 주니 **15px** 이 나왔다. 부모 글꼴 20px 을 봤다면 30px 이었을 것이다.
- `font-size: 150%` 는 **부모 글꼴**의 150% 다. 같은 `150%` 인데 바로 옆 줄과 기준이 다르다 — 이 표에서 가장 잘 틀리는 짝이다.
- `line-height: 150%` 는 **픽셀이 되어 상속된다.** 실측: 위 15px 이 `font-size: 40px` 짜리 자식에게도 **15px 그대로** 내려갔다.\
  무단위 `1.5` 와 갈리는 자리가 여기이고, 그 정본은 [04번](../04-value-processing-stages/2-summary.md)이다.

### 4. 세로 여백의 `%` 는 무엇을 보는가

**왜 그런가**

```text
  만약 padding-top: 10% 가 '부모 높이' 를 봤다면

    부모 높이 auto  <──────────┐
         │                     │
         v                     │
    자식 padding-top 10%       │  자식 높이가 부모 높이를 만드는데
         │                     │  부모 높이가 자식 padding 을 만든다
         └─────────────────────┘  => 답이 정해지지 않는다 (순환)
```

- 그래서 명세가 **가로(인라인 축) 하나로 못을 박았다.** 폭은 세로 방향 계산과 독립이라 순환이 안 생긴다.
- 실측 확인 — 부모 폭 400 / 높이 200 에서 `padding-top: 10%` 와 `padding-left: 10%` 가 **둘 다 40px** 이었다. 높이를 봤다면 20px 이었을 것이다.
- **옛 관용구** — `padding-top: 100%` 로 정사각형 자리를 만드는 것. 폭 기준이라 폭과 같은 높이가 나온다.
- **오늘의 대체** — `aspect-ratio`([목록의 **31번 주제**](../31-intrinsic-sizing-and-aspect-ratio/)). 관용구가 아니라 속성으로 뜻이 드러난다.
- 같은 규칙을 [15번](../15-box-model-and-box-sizing/2-summary.md)이 「부모 높이를 바꿔도 `padding-top: 10%` 가 40 으로 고정」으로 이미 쟀다. 여기는 **왜 폭이냐**까지다.

### 5. `height: 50%` 가 아무 일도 안 한다

**실행 결과**

```text
  부모 height: auto   -> 자식 computed height = 24px,  실높이 24
  부모 height: 200px  -> 자식 computed height = 100px, 실높이 100
```

**왜 그런가**

- `height: 50%` 를 풀려면 **부모의 확정된 높이**가 있어야 한다. `auto` 면 그 숫자가 없다.
- 그때 `height` 는 **`auto` 로 떨어진다** — 24px 은 내용(한 글줄)이 만든 높이다.
- 고치는 법 세 가지 — ① 부모에 높이를 준다 ② flex/grid 로 늘린다(`align-items: stretch`) ③ 뷰포트 단위를 쓴다([34번](../34-viewport-and-container-units/2-summary.md)).

### 6. `transform` 과 `border-radius` 의 `%`

**실행 결과**

```text
  .t { width:100px; height:40px; transform: translate(50%, 50%) }
     computed transform = matrix(1, 0, 0, 1, 50, 20)
     => x 로 50px, y 로 20px 움직였다

  .r { width:200px; height:100px; border-radius: 10% }
     computed border-top-left-radius = 10%   (px 로 안 바뀐다)

     좌상단 모서리 히트테스트 (elementFromPoint)
       (1, 1)   -> HTML     상자 밖 — 깎였다
       (3, 3)   -> 상자     안
       (21, 1)  -> 상자     가로 20px 을 넘기니 들어왔다
       (1, 11)  -> 상자     세로 10px 을 넘기니 들어왔다
     => 깎인 타원 = 가로 20 x 세로 10
```

**왜 그런가**

- **둘 다 부모를 안 본다 — 자기 자신을 본다.** `translate` 의 `%` 는 **자기 border 상자** 기준이다(100의 50% = 50, 40의 50% = 20).
- 그래서 `transform: translate(-50%, -50%)` 로 가운데 정렬하는 관용구가 성립한다 — 자기 크기를 몰라도 절반만큼 물러난다.
- **`border-radius` 는 한 선언 안에서 기준이 둘이다** — 가로 반지름은 자기 폭, 세로 반지름은 자기 높이. 실측 타원 20×10 이 그 근거다(200의 10%, 100의 10%).
- `border-radius` 의 `%` 는 **계산값 단계에서 `%` 인 채로 남는다**(실측 `10%`). 상자 크기가 바뀌면 따라 바뀌어야 하기 때문이다.

### 7. `ch` 와 `ex` 는 무엇에 달려 있나

**실행 결과** (font-size 20px 고정, 글꼴만 교체)

```text
  글꼴                 10ch         10ex
  -------------------  -----------  -----------
  DejaVu Sans Mono     120.40625    110
  Liberation Serif     100          91.796875
  DejaVu Sans          127.234375   110
  JetBrains Mono       119.984375   110
  Liberation Sans      111.21875    105.65625

  "0" 한 글자를 span 으로 재니
    DejaVu Sans Mono = 12.046875   (x10 = 120.40625 — 위 표와 일치)
    Liberation Serif = 10          (x10 = 100      — 위 표와 일치)
```

**왜 그런가**

- **다르다.** `ch` 는 **그 글꼴의 `0`(영) 글리프 전진폭**이라 글꼴이 바뀌면 값이 바뀐다.
- `0` 한 글자를 따로 잰 값에 정확히 10을 곱한 값이 나온 것이 **`ch` 의 정의를 실측으로 확인한 것**이다.
- **`ex` 는 x-height**(소문자 x 높이)다. 같은 20px 에서 91.8 \~ 110px 까지 벌어졌다.
- **폴백도 따라간다** — 없는 글꼴만 지정한 칸과 `monospace` 를 덧붙인 칸이 같은 `10ch` 에서 **177.59375 대 160** 으로 갈렸다(그 실험은 루트 글꼴이 32px 인 문서였다).\
  즉 `ch` 는 **선언한 글꼴이 아니라 실제로 쓰인 글꼴**을 잰다.

### 8. `px` 은 화면의 점 하나인가

**실행 결과** (같은 문서를 `--window-size=400,200` 으로 두 번)

```text
  배율 설정                       devicePixelRatio   1in    100px 상자   나온 PNG
  ------------------------------  -----------------  -----  -----------  ---------
  (기본)                          1                  96px   100px        400 x 200
  --force-device-scale-factor=2   2                  96px   100px        800 x 400
```

**왜 그런가**

- **계산값은 하나도 안 바뀐다.** `1in` 도 `96px`, `100px` 상자도 `100px` 이었다.
- 바뀐 것은 **그 CSS 픽셀을 장치 점 몇 개로 칠하느냐**뿐이다 — 그래서 PNG 만 가로세로 2배가 됐다.
- `px` 은 **기준 픽셀**이라는 추상 단위다. 장치 점으로 내려가는 것은 [04번](../04-value-processing-stages/2-summary.md)의 **④ 실제값** 단계다.
- **`1in ≡ 96px`** 은 명세(css-values-4)가 정한 고정 환산이다. 실제 종이 1인치와는 관계가 없다.\
  나머지 물리 단위도 전부 여기 묶인다 — 실측: `1pc` 16 · `1pt` 1.328125 · `1cm` 37.78125 · `1mm` 3.765625 · `1Q` 0.9375.

### 9. 루트에서 쓴 `rem`

**실행 결과**

```text
  html { font-size: 2rem }
     -> html 의 계산된 font-size = 32px

  뒤이어
     #a { width: 1rem }      -> 32px
     #b { font-size: 200% }  -> 64px   (% 는 부모 = html 의 32px 을 본다)
```

**왜 그런가**

- **루트 자신에 쓴 `rem` 은 루트의 초기 글꼴(16px)을 본다.** 자기 참조를 피하려고 명세가 못 박은 규칙이다.
- 그래서 `2rem` 이 `16 × 2 = 32px` 이 됐다. 「루트의 계산값 2배」였다면 값이 정해지지 않았을 것이다.
- **루트가 확정된 뒤부터는** 모든 `rem` 이 그 계산값 32px 을 본다 — `#a` 가 32px 인 것이 근거다.
- `html { font-size: 62.5% }` 로 「1rem = 10px」을 만드는 관용구는 **`%`** 를 쓴다 — 부모(브라우저 기본 16px)의 62.5% 다.

### 10. 다른 주제로 잇기

- **어느 단계에서 픽셀이 되는가** — [04번](../04-value-processing-stages/2-summary.md)(값 처리 단계)이 정본이다. `em`·`rem`·`ch`·`lh` 는 **계산값 단계**에서 px 이 된다.
- **`%` 만 남는 이유** — `%` 를 풀려면 **레이아웃을 돌려 포함 블록의 치수**를 알아야 한다. 계산값 단계에는 아직 상자가 없다.\
  실측 근거는 04번에 있다 — `width: 50%` 인 요소를 렌더된 채로 읽으면 `200px`, `display: none` 으로 읽으면 `50%` 가 나온다.
- **뷰포트·컨테이너 기준 단위** — [34번](../34-viewport-and-container-units/2-summary.md).
- **단위를 섞어 고르는 문법** — [35번](../35-calc-clamp-min-max/2-summary.md)(`calc()`·`clamp()`·`min()`/`max()`).
- **`%` 가 잰 폭이 어느 칸인가** — [15번](../15-box-model-and-box-sizing/2-summary.md)(박스 모델과 `box-sizing`).

## 용어 풀이

- **`<length>`** — 길이 값 타입. `px`·`em`·`rem`·`ch`·`ex`·`in` 등이 속하고 **`%` 는 속하지 않는다**(별도 타입 `<percentage>`).
- **기준점(reference)** — 상대 단위가 배수·비율을 계산할 때 대고 재는 길이. 예: `width: 2em` 의 기준점은 자기 `font-size` 다.
- **포함 블록(containing block)** — `%` 가 기준으로 삼는 조상 상자. 정적 요소면 부모의 content 상자다. 정본은 [목록의 **21번 주제**](../21-position-and-containing-block/).
- **`em`** — 그 요소의 `font-size` 의 배수. `font-size` 속성 자신에 쓸 때만 **부모의** `font-size` 를 본다.
- **`rem`** — 루트(`html`)의 `font-size` 의 배수. 루트 자신에 쓰면 초기값 16px 기준이다.
- **`ch`** — 그 요소에 실제로 적용된 글꼴의 `0` 글리프 전진폭. 예: 실측에서 20px 등폭의 `1ch` 가 `12.046875px` 이었다.
- **`ex`** — 그 글꼴의 x-height. 예: 같은 20px 에서 글꼴에 따라 `10ex` 가 91.8 \~ 110px 로 갈렸다.
- **`lh` / `rlh`** — 자기 / 루트의 `line-height` 의 배수. 예: `line-height: 1.5` 인 20px 요소의 `2lh` 가 60px 이었다.
- **CSS 픽셀(기준 픽셀)** — CSS 가 쓰는 추상 길이 단위. 장치 점과 1:1 이 아니다.
- **`devicePixelRatio`** — CSS 픽셀 하나를 장치 점 몇 개로 그리는가. 예: 2로 두자 스크린샷만 2배가 됐다.
- **1/64px 격자** — Chrome 이 길이를 저장하는 내부 해상도. `1pt` 이 `1.328125px` 로 떨어진 이유다. **Chrome 151 의 구현 세부다.**

## 실행 검증

| 무엇을 | 어떻게 | 결과 |
|---|---|---|
| `em` 의 기준이 속성마다 갈리는 것 | Chrome 151 headless · `--dump-dom` + `getComputedStyle` | `font-size` 40 / `width`·`padding`·`margin` 80 / `border` 20 |
| `em` 사슬 4겹 | 같은 클래스를 네 겹 중첩해 계산값 수집 | 40 / 50 / 62.5 / 78.125 |
| `rem` 의 루트 자기참조 | `html { font-size: 2rem }` 의 계산값 | 32px (= 초기값 16 × 2) |
| `%` 기준 표 15칸 | 포함 블록 400×200 / 글꼴 20px 에서 속성별 계산값·실측 | 본문 (6) 표 |
| `line-height: 150%` 의 기준 | 글꼴 10px 요소에 선언 후 계산값 + 자식 상속값 | 15px, 자식(40px 글꼴)도 15px |
| `text-indent: 25%` 의 기준 | 첫 글자를 span 으로 감싸 x 좌표 측정 | 100px (부모 폭 400 의 25%) |
| `gap: 10%` 의 기준 | flex 아이템 두 개의 rect 간격 | 40px (폭 400 의 10%) |
| `border-radius: 10%` 의 두 축 | `elementFromPoint` 로 모서리 히트테스트 | 가로 20 / 세로 10 |
| `height: 50%` + 부모 auto | 부모 높이를 auto / 200px 로 바꿔 측정 | 24px(auto 로 떨어짐) / 100px |
| `ch`·`ex` 의 글꼴 의존 | font-size 20px 고정, 글꼴 5종 교체 | 본문 (7) 표 |
| `ch` 의 정의 | `0` 한 글자 span 폭 × 10 과 `10ch` 대조 | 일치(120.40625 · 100) |
| 절대 단위 환산 | 폭 1단위 상자 7종의 rect | `1in` 96 · `1cm` 37.78125 · `1pt` 1.328125 등 |
| `px` 이 장치 점이 아닌 것 | `--force-device-scale-factor=2` 로 같은 문서 재렌더 | 계산값 동일, PNG 만 400×200 → 800×400 |
| `lh`/`rlh` | `line-height: 1.5` 인 20px 요소의 `2lh` / `2rlh` | 60 / 92 |
| demo 3개 | `extract-demo-blocks.py --render` 로 문서에서 재추출해 재실행 | 「보이는 것」 3건 모두 일치 |

**구현 의존 항목** — `10ch = 120.40625px` 같은 **구체 숫자는 글꼴이 정한다**. 글꼴이 바뀌면 이 칸을 다시 찍어야 한다.\
`1pt = 1.328125px` 처럼 1/64 격자에 떨어진 값은 **Chrome 151 의 구현 세부**다.\
**엔진은 Chrome 하나다.** Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고 WebKit 은 이 머신에 없다 — **「두 엔진에서 확인했다」고 적지 않았다.**

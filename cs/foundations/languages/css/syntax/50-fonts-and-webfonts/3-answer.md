# css/syntax/50 — 글꼴과 웹폰트: `font` 단축·`@font-face`·`font-display`·가변 폰트 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 px 수치와 시각별 값은 Google Chrome 151.0.7922.173 headless(Linux)에서 실제로 측정한 것**이다.\
> ⚠️ **글꼴은 환경이다.** 숫자는 이 머신의 설치 글꼴에 달려 있다 — 재현되는 것은 숫자가 아니라 「**같으냐 다르냐**」다.\
> 규칙은 [CSS Fonts 4](https://drafts.csswg.org/css-fonts-4/) · [CSS Fonts 5](https://drafts.csswg.org/css-fonts-5/) · [CSS Font Loading 3](https://drafts.csswg.org/css-font-loading/) 로 접지했다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 이 셋 중 실제로 어느 글꼴이 쓰였는가

**실행 결과** (Chrome 151 headless — 40px `Handgloves` 의 `getBoundingClientRect().width`)

```text
  .a  font-family: Georgia              -> 220.40625   (= UA 기본 글꼴)
  .b  font-family: Georgia, serif       -> 227.96875   (= serif 단독과 같다)
  .c  font-family: Georgia, monospace   -> 200         (= monospace 단독과 같다)

  대조군
      font-family: serif                -> 227.96875
      font-family: monospace            -> 200
      font-family: Zzzznope             -> 220.40625   (= .a 와 같다)
      (font-family 를 안 쓴 요소)        -> 220.40625
```

**셋은 각각 무엇으로 그려지는가**

- `.a` — Georgia 를 못 찾고 **목록이 끝나서 UA 기본 글꼴**로 떨어졌다. 이 환경에서는 `Noto Sans CJK KR`.
- `.b` — `serif` 로 내려갔다.
- `.c` — `monospace` 로 내려갔다.

**`.a` 와 `.b` 는 같은 글꼴인가**

- **아니다.** 220.40625 대 227.96875 로 폭이 다르다.
- 「목록이 다 실패하면 `serif` 가 된다」가 아니다 — **UA 의 기본 글꼴 설정**으로 간다.\
  그래서 목록의 **마지막은 반드시 generic family 로 닫아야** 내가 고른 값이 된다.

**`getComputedStyle` 은 무엇을 돌려주는가**

```text
  .a -> "Georgia"
  .b -> "Georgia, serif"
  .c -> "Georgia, monospace"
```

- **내가 쓴 목록 그대로**다. 존재하지 않는 `Zzzznope` 도 `"Zzzznope"` 로 돌아온다.

**그 값으로 판정할 수 있는가**

- **못 한다.** `font-family` 의 계산값은 명세가 **지정값과 같게** 규정한다.\
  「선언한 목록」이지 「쓰인 글꼴」이 아니다. 판정 방법은 7번.

> **UA 기본 글꼴** — 브라우저 설정의 「표준 글꼴」. 목록이 전부 실패했을 때 쓰인다.\
> 예: 이 환경에서는 `Noto Sans CJK KR` 였고, 그것은 `sans-serif` 와 우연히 같았지 `serif` 와는 달랐다.

### 2. 이 한 줄 뒤에 무엇이 남는가

**실행 결과** (Chrome 151 headless — `class="a b"` 요소의 계산값)

```text
                      .a 만          .a + .b
  font-style          italic     ->  normal
  font-weight         700        ->  400
  font-variant-caps   small-caps ->  normal
  line-height         60px       ->  normal
  font-stretch        75%        ->  100%
  font-size           30px       ->  16px
  font-family         serif      ->  sans-serif
```

**명시도 때문인가**

- **아니다.** `font` 는 **자기가 덮는 롱핸드 칸에 값을 직접 써 넣는** 단축이고,
  안 적은 칸에는 **초기값**을 써 넣는다. 「경쟁에서 이겼다」가 아니라 「그 칸을 채웠다」다.
- 이것은 모든 단축의 공통 규칙이다(`background: red` 가 `background-image` 를 `none` 으로 되돌리는 것과 같다).

**값을 받지도 못하는데 되돌리기만 하는 속성**

```text
  font-feature-settings     "liga" 0      ->  normal
  font-variation-settings   "wght" 700    ->  normal
  font-optical-sizing       none          ->  auto
  font-variant-numeric      tabular-nums  ->  normal
  font-language-override    "TRK"         ->  normal
  font-size-adjust          0.5           ->  none
  font-kerning              none          ->  auto
```

- 이 일곱은 `font:` 문법에 **적을 자리가 없다.** 그런데도 초기값으로 돌아간다.
- **가변 폰트를 쓰는 코드에서 이게 아프다** — `font-variation-settings` 로 축을 조정해 뒀는데
  아래에서 `font:` 한 줄을 쓰면 통째로 날아간다.

**롱핸드 두 줄로 바꾸면**

- `font-size` 와 `font-family` 만 바뀌고 **나머지는 `.a` 의 값이 그대로 남는다.**
- 즉 「한 속성만 바꾸고 싶으면 롱핸드」가 규칙이다.

### 3. 이 다섯 줄 중 살아남는 것은 몇 개인가

**실행 결과** (Chrome 151 headless — `cssRules[...].style.cssText`)

```text
  #a  font: 16px serif;            ->  "font: 16px serif;"
  #b  font: bold italic 16px serif;->  "font: italic bold 16px serif;"     <- 살았다(순서 정규화)
  #c  font: italic 16px;           ->  ""                                  <- 버려졌다
  #d  font: 16px/1.4 serif bold;   ->  ""                                  <- 버려졌다
  #e  font: sans-serif 16px;       ->  ""                                  <- 버려졌다
```

- **둘이 살고 셋이 버려졌다.**
- `#b` 는 앞의 네 칸(`style`·`variant`·`weight`·`stretch`)이 **순서 자유**라서 유효하다.\
  다만 직렬화는 명세 순서(`italic bold`)로 정규화된다.
- `#c` 는 `font-family` 가 없다. `#d` 는 family 뒤에 다른 값이 왔다. `#e` 는 family 가 size 앞에 왔다.

**버려진 줄은 앞의 값을 되돌리는가**

- **안 되돌린다.** 통째로 **없는 줄**이 되므로 2번의 리셋조차 일어나지 않는다.

**어느 쪽이 문법 오류인가**

- **「아무것도 안 바뀐다」가 문법 오류**다(선언이 버려졌다).
- 「다 날아갔다」는 **정상 동작**이다(단축이 칸을 채웠다).
- 진단 순서가 달라진다 — 앞엣것은 `cssText` 를 보고, 뒤엣것은 `font:` 를 쓴 규칙을 찾는다.\
  「담겼나 / 잡혔나 / 이겼나」의 **첫 창**이 여기서 결정적이다([07번](../07-syntax-and-error-recovery/2-summary.md)).

### 4. 이 한 요소는 몇 개의 글꼴로 그려지는가

**실행 결과** (Chrome 151 headless — `font: 40px BoxOnly, serif`, BoxOnly 는 `A`\~`Z` 만 있다)

```text
  <span class="up">ABC</span>   ->  120px        = 40px x 3   (BoxOnly 의 전각 네모)
  <span class="lo">abc</span>   ->  69.328125px               (serif)

  참고: "ABCDEFGHIJ" 에 unicode-range: U+0041-0043 을 건 판
        ->  260px = (3 x 40) + (7 x 20)          앞 셋만 웹폰트, 나머지는 monospace
```

**같은 글꼴로 그려지는가**

- **아니다.** 한 요소, 한 선언인데 **두 글꼴이 섞여 있다.**

**요소 단위인가 글자 단위인가**

- **글자 단위**다. 명세의 글꼴 매칭 알고리즘이 문자마다 목록을 다시 훑는다.

**한글 페이지에서 `font-family: Inter` 만 쓰면**

- 라틴은 Inter, **한글은 전부 그 뒤의 대체 사슬**(목록이 없으면 UA 기본 글꼴)로 내려간다.

**버그인가**

- **아니다.** 명세대로다. 고치는 법은 한글 글꼴을 목록에 **명시적으로 넣는 것**이다.\
  실무의 `font-family: Inter, "Pretendard", sans-serif` 같은 목록이 정확히 이것을 노린 것이다.

### 5. 폰트가 4초 뒤에 도착하면 다섯 값은 각각 무엇을 보여 주는가

**실행 결과 ①** (Chrome 151 + CDP — 응답을 4초 늦추는 로컬 HTTP 서버, 폭: 폴백 200px → 웹폰트 400px)

```text
          t=0     1.7s    3.3s    3.8s    4.6s    7.0s
  auto     200     200     200     200     400     400
  block    200     200     200     200     400     400
  swap     200     200     200     200     400     400
  fallback 200     200     200     200     200     200    <- 교체 기간 3초를 넘겨 포기
  optional 200     200     200     200     200     200
```

**실행 결과 ②** (같은 문서, 스크린샷의 어두운 픽셀 수로 「보이나」를 판정)

```text
  시각      auto      block     swap      fallback  optional
  0.2s     안 보임    안 보임     보임       보임       보임
  0.8s     안 보임    안 보임     보임       보임       보임
  1.9s     안 보임    안 보임     보임       보임       보임
  2.0s      보임      안 보임     보임       보임       보임
  2.9s      보임      안 보임     보임       보임       보임
  3.2s      보임       보임      보임       보임       보임
```

**0.8초에 보이는 것**

- `swap`·`fallback`·`optional`. **`auto` 와 `block` 은 안 보인다**(FOIT).

**4.6초에 웹폰트로 그려져 있는 것**

- `auto`·`block`·`swap`. `fallback` 은 교체 기간 3초를 넘겨 **폴백으로 굳었고**, `optional` 도 폴백이다.

**1.5초 만에 오면 `optional` 은 바뀌는가**

**실행 결과 ③** (지연 1.5초)

```text
          t=0     0.9s    1.7s    2.6s    4.6s    7.0s
  auto     200     200     400     400     400     400
  block    200     200     400     400     400     400
  swap     200     200     400     400     400     400
  fallback 200     200     400     400     400     400
  optional 200     200     200     200     200     200    <- 1.5초에 와도 안 바꿨다
```

- **안 바뀐다.** `optional` 의 교체 기간은 사실상 0이다.

**레이아웃이 안 흔들리는 것과 그 대가**

- `optional`. 대가는 **웹폰트를 거의 항상 포기하는 것**이다.\
  캐시에 이미 있으면 다음 방문부터 쓰인다는 것이 이 값의 전제다.

> **차단/교체/실패 기간** — 폰트를 기다리는 시간의 세 토막.\
> 예: `fallback` 은 0.1초 안 그리고(차단), 3초 동안 오면 바꾸고(교체), 그 뒤엔 와도 안 바꾼다(실패).

### 6. `font-weight: 450` 은 어떻게 그려지는가

**실행 결과 (가)** — 같은 가변 폰트 파일을 `@font-face` + `data:` URI 로 불러온 경우

```text
  font-weight        400       437       450       500
  40px "Weight" 폭   129.77    130.59    130.84    132.00

  font-variation-settings: "wght" 450  ->  130.84   (font-weight: 450 과 같다)
  font-variation-settings: "wght" 800  ->  136.61
```

**실행 결과 (나)** — **같은 파일**이 OS 에 설치돼 있어 `font-family: Ubuntu` 로 쓴 경우

```text
  font-weight        100       300       400       450       500       700
  40px "Weight" 폭   125.61    128.38    129.77    129.77    132.00    134.92
                                         ^^^^^^^^^^^^^^^^  450 이 400 과 똑같다

  font-variation-settings: "wght" 450  ->  129.77   (아무 효과 없음)
  font-variation-settings: "wght" 900  ->  129.77   (아무 효과 없음)
  font-stretch: 75%                    ->  104.09   (wdth 축은 먹었다)
```

**(가)는 400 과 500 사이인가**

- **그렇다.** 129.77 < 130.84 < 132.00. 437 도 그 사이에 따로 있다 — **연속값**이다.

**(나)도 그런가**

- **아니다.** 450 이 400 으로 **스냅**됐다.

**`font-variation-settings` 는 먹는가**

- (가)에서는 먹고, **(나)에서는 전혀 안 먹었다**(`"wght" 900` 도 폭이 그대로).
- 다만 (나)에서도 `font-stretch`(= `wdth` 축)는 먹었다 — **축마다 다르다.**

**이 차이를 만드는 것**

- **OS 쪽**이다. 이 머신의 fontconfig 는 가변 폰트 하나를
  `Thin`·`Light`·`Regular`·`Medium`… 같은 **이름 붙은 인스턴스 여러 줄**로 노출한다.\
  Chrome 은 시스템 글꼴을 그 목록에서 고르므로 연속 축이 끊긴다.
- 그래서 **「가변 폰트는 굵기가 연속이다」는 웹폰트로 불러올 때의 이야기**다.\
  *(이 판정은 이 환경의 관찰이다 — 다른 OS·다른 fontconfig 설정에서는 다를 수 있다.)*

### 7. 왜 `getComputedStyle` 로는 판정이 안 되는가

**`font-family` 의 계산값**

- 명세가 「**지정값과 같다**」로 규정한다. 목록을 그대로 물려주는 것이 상속에도 필요하기 때문이다.
- 즉 계산값은 **요청서**이고, 응답(어느 파일이 쓰였나)은 CSSOM 에 **어디에도 노출되지 않는다.**

**`--dump-dom` 자동화가 같은 함정에 빠지는 이유**

- `--dump-dom` 으로 뽑는 것도 결국 `getComputedStyle` 이다. **선언 목록이 그대로 나온다.**
- 그래서 「스크립트가 `Georgia` 를 확인했다」는 문장이 **아무것도 확인하지 않은 문장**이 된다.

**대신 쓸 수 있는 방법 — 센티넬 대조**

```text
  A:  font-family: <후보>, <센티넬>       B:  font-family: <센티넬>
            |                                       |
            +---------- 폭 비교 --------------------+
                   같다 -> 안 쓰였다 / 다르다 -> 쓰였다
```

**실행 결과** (40px `Handgloves`, 센티넬 `monospace` = 200px · `"DejaVu Sans"` = 235.4375px)

```text
  "DejaVu Serif"      239.375     쓰였다
  "Times New Roman"   191.078125  쓰였다 (이 OS 가 Liberation Serif 로 바꿔치기)
  Arial / Helvetica   211.25      쓰였다 (같은 이유)
  나눔고딕             215.640625  쓰였다
  Ubuntu              210.375     쓰였다
  Georgia             200         안 쓰였다
  Verdana             200         안 쓰였다
  "Comic Sans MS"     200         안 쓰였다
  "Nanum Gothic"      200         안 쓰였다   <- 파일은 있는데 그 이름이 아니다
  Zzzznope            200         안 쓰였다
```

**왜 센티넬이 둘 이상인가**

- 후보의 글자 폭이 **우연히 센티넬과 같을 수** 있다. 그러면 「안 쓰였다」로 오판한다.
- 성격이 다른 센티넬 둘(`monospace` 와 비례 글꼴 하나)에서 **둘 다 같으면** 안 쓰인 것이다.
- 위 표는 두 센티넬에서 판정이 전부 일치했다.

★ 이 방법이 답하는 것은 「**그 목록 항목이 어떤 글꼴을 만들어 냈나**」이지
**「그 이름의 파일이 쓰였나」가 아니다.** `Times New Roman` 이 「쓰였다」로 나온 것이 그 예다.

### 8. `document.fonts.check("16px Georgia")` 는 무엇에 답하는가

**실행 결과** (Chrome 151 headless)

```text
  document.fonts.check("40px Georgia")                 -> true    (Georgia 는 없다)
  document.fonts.check("40px Zzzznope")                -> true    (그런 글꼴은 없다)
  document.fonts.check("40px serif")                   -> true
  document.fonts.check("40px Georgia", "\u{10FFFD}")   -> true    (미정의 코드포인트)
  document.fonts.check("40px BoxTest")                 -> false   (@font-face 있음, 아직 unloaded)
  document.fonts.check("40px BoxTest")  (쓰인 뒤)       -> true
```

**Georgia 가 없는 머신에서**

- **`true`**. 「없는데 true」가 아니라, 이 함수가 **다른 것을 묻고 있다.**

**세상에 없는 이름을 넣으면**

- 역시 **`true`**. 걸리는 `@font-face` 가 하나도 없으면 시스템 대체로 어떻게든 그려지기 때문이다.

**`false` 가 나오는 경우**

- **그 지정에 걸리는 `@font-face` 가 있는데 아직 `loaded` 가 아닐 때**뿐이다.

**이 함수로 「설치돼 있나」를 물을 수 있는가**

- **없다.** 이 함수는 **웹폰트 로드 상태**를 묻는 함수다.\
  「설치돼 있나」는 7번의 폭 대조로만 답할 수 있다.

### 9. `@font-face` 만 써 두면 무슨 일이 일어나는가

**실행 결과**

```text
  어떤 요소도 BoxTest 를 안 쓰는 문서
    document.fonts.check("40px BoxTest")  ->  false
    face 의 status                        ->  unloaded

  어떤 요소가 BoxTest 를 쓰는 문서
    face 의 status                        ->  loaded
    document.fonts.size                   ->  1
```

**파일은 내려받히는가**

- **안 받는다.** 그 이름이 실제로 쓰여야 받는다. 게으른 로딩이 기본이다.

**`status`**

- `unloaded` → (쓰이면) `loading` → `loaded`. 실패하면 `error`.

**`@font-face` 는 적용하는가**

- **아니다. 이름을 등록할 뿐**이다. 적용하는 것은 `font-family` 다.
- 그래서 `@font-face` 를 열 개 써 놓아도 안 쓰면 네트워크가 한 번도 안 돈다 —\
  `unicode-range` 로 쪼개는 전략이 성립하는 이유가 이것이다.

### 10. `format()` 에 오타가 나면 어디까지 사라지는가

**실행 결과** (40px `ABCDE`, 폴백 `monospace` = 100px, 웹폰트 = 200px)

```text
  src: url(<ttf>) format("woff2")                     ->  200   쓰였다
  src: url(<ttf>) format("zzz-nope")                  ->  100   안 쓰였다
        그리고 document.fonts 에 그 face 가 없다
  src: url(<ttf>) format("truetype") tech(zzz-nope)   ->  100   안 쓰였다 (face 없음)
  src: url(<ttf>) format("zzz-nope"),
       url(<ttf>) format("truetype")                  ->  200   둘째 항목이 쓰였다
  src: url(깨진 데이터) format("truetype"),
       url(<ttf>)      format("truetype")             ->  200   둘째 항목이 쓰였다
```

**항목만 사라지나 규칙 전체가 사라지나**

- **항목이 걸러진다.** 남은 항목이 있으면 그것을 쓴다.
- **남는 항목이 하나도 없으면 `@font-face` 가 통째로 없던 것이 된다** —\
  `document.fonts` 에 face 자체가 안 나타났다.

**콘솔에 무엇이 찍히나**

- **아무것도 안 찍힌다.** CSS 는 에러를 던지지 않는다([07번](../07-syntax-and-error-recovery/2-summary.md)).

**ttf 에 `format("woff2")` 를 붙이면**

- **그래도 쓰였다.** `format()` 은 **「내가 지원하지 않는 형식이면 받지 말라」는 힌트**이지 내용 검증이 아니다.\
  woff2 는 지원 형식이므로 받아서 실제 내용으로 판단했다.
- 반대로 **모르는 낱말**은 지원 여부를 판정할 수 없으므로 그 항목을 버린다.

**진단하는 창구**

- **두 번째 창**(`document.fonts`)이다.\
  `cssRules` 에는 `@font-face` 규칙이 그대로 보일 수 있고, `getComputedStyle` 은 늘 선언 목록을 돌려준다 —\
  **face 가 등록됐나**를 묻는 창은 `document.fonts` 뿐이다.

### 11. 왜 `font-variation-settings` 보다 `font-weight` 를 쓰라고 하는가

**`font` 단축과의 관계**

- 2번의 표 — **`font:` 한 줄이 `font-variation-settings` 를 `normal` 로 되돌린다.**\
  `font-weight` 도 되돌아가지만, 그쪽은 `font:` 안에 **다시 적을 수 있다.** 축 설정은 적을 자리가 없다.

**상속될 때**

- `font-variation-settings` 는 **값 전체가 한 덩어리**다. 자식이 축 하나만 바꾸려고 다시 쓰면
  부모가 설정해 둔 **다른 축들이 통째로 사라진다.**
- `font-weight`·`font-stretch` 는 속성이 따로라 그런 일이 없다.

**그 글꼴에 축이 없으면**

- `font-weight: 700` — 굵은 face 를 찾고, 없으면 **합성으로 두껍게 흉내** 낸다(`font-synthesis` 로 끌 수 있다).
- `font-variation-settings: "wght" 700` — **아무 일도 안 일어난다.** 축이 없으면 그냥 무시된다.

**`font-feature-settings` 도 같은 이유인가**

- **그렇다.** `font-feature-settings` 역시 한 덩어리로 상속되고 `font:` 에 되돌아가며,
  `font-variant-ligatures`·`font-variant-numeric` 같은 상위 속성이 같은 일을 한다.
- 실측에서 `font: 16px serif` 한 줄이 `font-feature-settings: "liga" 0` 과
  `font-variant-numeric: tabular-nums` 를 **둘 다** 초기값으로 되돌렸다.

### 12. 다른 주제와 잇기

**글꼴 속성이 상속되는 대표라는 사실**

- `font-family`·`font-size`·`font-weight`·`line-height` 는 전부 상속되는 속성이다([03번](../03-inheritance-and-global-keywords/2-summary.md)).
- 그래서 **글꼴 목록은 `:root`(또는 `body`)에 한 번만 쓴다.** 컴포넌트마다 반복하면 그 자체가 사고 원인이다.
- 자식이 물려받는 것은 **부모의 계산값**이고, `font-family` 의 계산값은 **목록 그대로**다 —\
  그래서 자식에서도 같은 대체 사슬이 그대로 다시 돈다.

**`em` 은 어느 단계에서 다시 계산되나**

- `font-size` 가 바뀌면 그 요소의 `em` 기준이 바뀌고, 그 값들은 **계산값 단계**에서 절대화된다([04번](../04-value-processing-stages/2-summary.md)).
- **`font-size` 가 그 사슬의 뿌리**다 — `font: 16px serif` 한 줄이 그 아래 `em` 으로 쓴 여백·폭을 전부 다시 정한다.
- `font-size` 자신에 쓴 `em` 은 **부모 기준**이라 중첩에서 곱해진다는 것도 04번이 정본이다.

**잘못된 순서가 버려지는 것은 어떤 일반 규칙인가**

- **선언 단위 오류 복구**다([07번](../07-syntax-and-error-recovery/2-summary.md)).\
  값이 문법에 안 맞으면 **그 선언만** 버리고 나머지 규칙은 그대로 산다.
- 그래서 `font:` 오타는 **규칙 전체를 죽이지 않고 그 한 줄만 없앤다** — 그래서 더 안 들킨다.

**`line-height` 가 되돌아가면 행 상자에 무엇이 달라지나**

- 줄 높이가 `normal` 이 되어 **글꼴이 스스로 권하는 값**을 쓰게 된다.\
  글꼴이 바뀌면 줄 높이도 따라 바뀌므로, 레이아웃이 글꼴에 끌려다닌다.
- 행 상자가 그 값을 어떻게 쓰는지는 [목록의 **19번 주제**](../19-inline-formatting-context/)가 정본이다.

**다음 주제에서 무엇을 정할 수 있나**

- **어느 글꼴로 그리는지가 정해져야 어디서 줄이 바뀌는지가 정해진다.**\
  같은 문장도 글꼴이 다르면 글자 폭이 달라 줄 수가 달라진다 — 이 문서의 폭 표가 그 증거다.
- 그 다음 칸이 [51번](../51-text-wrapping-and-decoration/2-summary.md)이다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `devicePixelRatio = 1`.\
**엔진은 이것 하나다**(Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고, WebKit 은 없다).

**설치 글꼴** — `fc-list : family | sort -u` 기준 **312개 패밀리**. 실험에 쓴 이름의 존재 여부는 2-summary 의 「환경 확인」 표가 정본이다.

**하네스 ①(정적 계산값·폭)** — 문서 조각과 프로브 스크립트를 합쳐 한 문서로 만들고, `document.fonts.ready` 뒤에 결과를 `<pre>` 에 써 넣은 뒤 `--dump-dom` 에서 잘라 읽는다.

```bash
{ echo '<!doctype html><meta charset="utf-8">'; cat body.html
  echo '<script>'
  echo 'const __o=[];function P(k,v){__o.push(k+" = "+v)}'
  echo 'function CS(s,p){return getComputedStyle(document.querySelector(s)).getPropertyValue(p)}'
  echo 'function W(s){return document.querySelector(s).getBoundingClientRect().width}'
  cat probes.js
  echo ';document.fonts.ready.then(()=>{const p=document.createElement("pre");'
  echo 'p.textContent="<<<BEGIN>>>\n"+__o.join("\n")+"\n<<<END>>>";document.body.appendChild(p)});'
  echo '</script>'; } > /tmp/doc.html
google-chrome --headless --disable-gpu --no-sandbox --dump-dom /tmp/doc.html 2>/dev/null \
  | sed -n '/&lt;&lt;&lt;BEGIN&gt;&gt;&gt;/,/&lt;&lt;&lt;END&gt;&gt;&gt;/p' | sed '1d;$d'
```

**하네스 ②(`font-display` 시간 측정)** — `data:` URI 는 즉시 도착해 못 재므로 **응답을 N 밀리초 늦추는 로컬 HTTP 서버**(파이썬 `ThreadingTCPServer`, `Cache-Control: no-store`)를 세우고, `--remote-debugging-port` 로 CDP 에 붙어 실제 시각마다 `getBoundingClientRect` 를 샘플링하고 `Page.captureScreenshot` 을 찍었다.\
★ `--virtual-time-budget` 을 쓰면 **가상 시간이 먼저 다 흘러서 폰트가 영영 안 온 것처럼 나온다** — 이 측정에서는 쓰면 안 된다(처음에 그렇게 해서 다섯 값이 전부 「안 바뀜」으로 나왔다).

★ **제출 직전 재실행에서 도구의 사각지대를 하나 찾았다.** `reference/tools/extract-demo-blocks.py --render` 로
완성된 문서에서 demo 를 다시 뽑아 띄웠더니 **글자 단위 대체 demo 의 `.up` 폭이 120px 이 아니라 82px** 로 나왔다.\
원인은 문서가 틀린 것이 아니라 **그 도구가 `document.fonts.ready` 를 안 기다리고 파싱 직후에 재기 때문**이다
(82px 은 웹폰트가 붙기 전 `serif` 로 그린 폭이다). 같은 블록을 `document.fonts.ready` 뒤에 재니 **120px** 이었고,
스크린샷에도 검은 네모 세 개가 찍혔다. **웹폰트가 걸린 demo 는 그 도구로 값을 대조할 수 없다** — 스크린샷이나 `fonts.ready` 프로브를 따로 써야 한다.

**웹폰트 재료** — 외부 URL 을 쓰지 않기 위해 **740바이트짜리 TTF 를 직접 만들어** `data:` URI 로 넣었다.\
글리프는 `A`\~`Z` 하나뿐이고(전각 검은 네모, advance 1em), 그래서 **「폭이 글자 수 × font-size」인지**로 적용 여부를 셀 수 있다.\
가변 폰트 실험만 이 머신의 `Ubuntu[wdth,wght].ttf` 를 **임시 파일에서** base64 로 실어 썼다(문서에는 넣지 않았다).

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 8종 `font-family` 조합의 40px 폭 + 계산값 | 1 | 동작 방식 (2) · A1 · A7 |
| UA 기본 글꼴·`serif`·`sans-serif`·별칭 4종의 폭 | 1 | 환경 확인 · A1 |
| 13개 이름의 센티넬 2종 대조 | 1 | 동작 방식 (2) · A7 |
| `document.fonts.check()` 6가지 | 2 | 동작 방식 (2) · A8 |
| 글자 단위 대체(한글·라틴 / 대문자·소문자) | 2 | 동작 방식 (1) · A4 |
| `font` 단축 전후 13속성 × 7규칙 | 1 | 동작 방식 (3) · A2 |
| `font` 단축 문법 9가지의 `cssText` | 1 | 동작 방식 (4) · A3 |
| `src` 의 `local()`·`format()`·`tech()`·체인·`unicode-range` 5종 | 1 | 동작 방식 (6)(7) · A10 |
| 알 수 없는 `format()`/`tech()` 4종 | 1 | 동작 방식 (6) · A10 |
| `font-display` 5값 × 지연 1.5초 / 4초 × 11시점 폭 | 2 | 동작 방식 (8) · A5 |
| `font-display` 5값 스크린샷 7시점(픽셀 판정) | 7 | 동작 방식 (8) · A5 |
| `auto` 경계 재확인(1.9초·2.0초) | 4 | 동작 방식 (8) — 두 번 반복해 같음 |
| 가변 폰트 웹폰트판 7조합 / 시스템판 13조합 | 각 1 | 동작 방식 (9) · A6 |
| demo 3개(단축 리셋 · 글자 단위 대체 · 센티넬 대조) | 각 1 | 2-summary 의 demo |
| demo 의 「바꿔 볼 것」 단언 3개 | 각 1 | 2-summary 의 demo |

**구현에 달린 항목** — 버전·머신이 바뀌면 다시 찍을 자리다.

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| 모든 px 폭 수치 | 표 참조 | **설치 글꼴에 달렸다.** 다른 머신에서는 전부 달라진다 |
| UA 기본 글꼴 = `Noto Sans CJK KR` | 220.40625px | 브라우저 글꼴 설정 |
| `Times New Roman` → Liberation Serif | 191.078125px | 이 리눅스의 fontconfig 별칭 규칙 |
| `"Nanum Gothic"` 이 안 먹는 것 | 200px(센티넬과 같음) | 글꼴이 등록한 패밀리 이름 |
| `auto` 의 차단 기간 ≈ 2.0초 | 스크린샷 판정 | **명세가 UA 재량으로 둔 값** |
| `block` 의 차단 기간 = 3.0초 | 〃 | 명세 권고값과 일치하지만 관찰이다 |
| 시스템 가변 폰트에서 450 → 400 스냅 | 129.77px | fontconfig 가 이름 붙은 인스턴스로 노출 |
| `format("woff2")` 를 ttf 에 붙여도 쓰인 것 | 200px | Chrome 의 형식 힌트 처리 |

**못 잰 것** — `font-display` 를 **`data:` URI 로는 잴 수 없다.** 즉시 도착해서 차단·교체 기간이 전부 0으로 지나간다. 그래서 로컬 HTTP 서버로 **지연을 만들어야만** 쟀다. 이 방법이 없었다면 「미실행」으로 적었을 자리다.

**안 돌려 본 것** — ① 캐시에 이미 있는 두 번째 방문에서 `optional` 이 웹폰트를 쓰는지 ② `size-adjust`·`ascent-override` 로 폴백 치수를 맞추는 것 ③ `font-synthesis` 를 껐을 때의 합성 여부. 셋 다 이 문서에서 결론으로 쓰지 않았다.

## 용어 풀이

- **글리프(glyph)** — 글꼴 파일에 그려진 글자 그림 하나.
- **대체(fallback)** — 앞 후보로 못 그릴 때 다음으로 내려가는 것. **글자 단위**로 일어난다.
- **generic family** — `serif`·`sans-serif`·`monospace`·`cursive`·`fantasy`·`system-ui`. 따옴표를 붙이면 일반 이름이 된다.
- **UA 기본 글꼴** — 목록이 전부 실패했을 때 쓰이는 브라우저 설정 글꼴.
- **치수 호환 대체** — 이름 대신 글자 폭이 같은 글꼴로 바꿔치는 OS 설정.
- **센티넬 대조** — 후보와 함께 쓴 센티넬의 폭이 같은지로 판정하는 방법. 센티넬은 둘 이상.
- **`@font-face`** — 이름을 등록하는 at-rule. 적용이 아니다.
- **기술자(descriptor)** — `@font-face` 안에서만 쓰는 항목. 같은 이름의 속성과 다른 물건이다.
- **`format()` / `tech()`** — 받기 전에 거르는 **힌트**. 모르는 낱말이면 그 항목이 사라진다.
- **`local()`** — 설치된 글꼴을 소스로 쓰는 것. 내려받지 않는다.
- **`unicode-range`** — 그 face 가 담당할 문자 범위. 범위 밖 글자는 이 face 를 안 본다.
- **FOIT** — 기다리는 동안 글자를 안 그리는 것(차단 기간의 증상).
- **FOUT** — 폴백으로 먼저 그리고 나중에 바꾸는 것(교체 기간의 증상).
- **차단/교체/실패 기간** — `font-display` 가 나누는 세 구간.
- **가변 폰트** — 한 파일이 축을 따라 연속으로 모양을 바꾸는 글꼴.
- **축(axis)** — `wght`·`wdth`·`slnt`·`opsz` 같은 네 글자 태그.
- **이름 붙은 인스턴스** — 가변 폰트가 미리 이름을 붙여 둔 축 좌표.
- **합성(synthesis)** — 굵은/기울인 face 가 없을 때 브라우저가 흉내 내는 것.
- **CLS** — 페이지가 뜨는 동안 요소가 밀린 양을 합산한 지표. 글꼴 교체가 큰 원인이다.

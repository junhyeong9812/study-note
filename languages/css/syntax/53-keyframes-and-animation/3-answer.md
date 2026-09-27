# css/syntax/53 — `@keyframes` 와 `animation`: 단축·반복·채우기 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 수치는 Google Chrome 151.0.7922.173 headless 에서 실제로 측정한 것**이다.\
> 진행률이 중요한 실험은 `animation-play-state: paused` + 음수 `animation-delay` 또는 `getAnimations().currentTime` 세팅으로 **시각을 고정해** 읽었고,\
> `demo` 블록은 CDP 로 실제 마우스를 올린 뒤 벽시계 시각마다 `getComputedStyle` 을 읽었다(±20ms).\
> 규칙은 [CSS Animations Level 1](https://drafts.csswg.org/css-animations-1/) 과 [CSS Cascading and Inheritance Level 5](https://drafts.csswg.org/css-cascade-5/) 로 접지했다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 전환과 무엇이 갈리는가

**무엇이 있어야 시작되나**

- **전환** — **계산값이 바뀌어야** 한다. 그리고 바뀌기 **전** 상태에 `transition` 이 이미 있어야 한다([52번](../52-transition/2-summary.md)).
- **애니메이션** — 아무것도 안 바뀌어도 된다. **규칙이 요소에 붙는 순간** 재생이 시작된다.

**전환으로 못 하는 것 넷**

```text
  ① 들를 지점이 가운데 있는 움직임     0% -> 50% -> 100%
  ② 반복 (특히 infinite)
  ③ 왕복 (direction: alternate)
  ④ 재생 제어 (animation-play-state: paused)
```

**끝난 뒤 어디에 있나**

- **전환** — 바뀐 값이 그대로 남는다. 그 값이 「진짜 계산값」이기 때문이다.
- **애니메이션** — **기본은 원래 값으로 돌아간다**(`animation-fill-mode: none`). 악보의 값은 재생 중에만 얹히는 것이다.

**`!important` 의 답이 반대인 이유**

```text
  캐스케이드 사다리 (위가 셈)
    1. 전환 선언            <- 전환은 여기: !important 로도 못 덮는다
    2~4. !important 무리     <- 작성자 !important 가 여기
    5. 애니메이션 선언       <- 애니메이션은 여기: !important 가 이긴다
    6. 작성자 normal
```

- 전환 값은 **엔진이 만들어 내는 한순간의 값**이라 시트가 덮으면 도중에 튄다. 그래서 맨 위다.
- 애니메이션 값은 **작성자가 악보로 선언한 것**이라 작성자의 다른 선언과 같은 층위에서 다툰다 — `!important` 아래다.

### 2. 양 끝을 안 적으면 어디서 출발하는가

**출력** (Chrome 151 — `currentTime` 을 세팅해 읽은 시각별 `width`)

```text
            half (50% 만 적음)     only100 (to 만 적음)
  t=   0ms  120px                  120px
  t=1000ms  260px                  190px
  t=2000ms  400px                  260px
  t=3000ms  260px                  330px
  t=3999ms  120.125px              399.922px
```

**왜 그런가**

- 안 적은 `0%`/`100%` 를 브라우저가 **그 요소의 원래 계산값**으로 만들어 넣는다.\
  여기서는 `.q { width: 120px }` 이므로 양 끝이 120px 이다.
- 그래서 `half` 는 **120 → 400 → 120** 으로 갔다 돌아온다. 「왜 제자리로 오지」의 정체가 이것이다.
- `only100` 은 `0%` 만 만들어지므로 **120 → 400** 으로 곧게 간다.\
  1초(25%) 시점은 `120 + (400-120) × 0.25 = 190px` — 실측과 같다.
- 명세 문구: *"If a 0% or from keyframe is not specified, then the user agent constructs a 0% keyframe using the computed values of the properties being animated."*

> **암묵 키프레임(implicit keyframe)** — 안 적은 양 끝을 요소의 계산값으로 채워 넣은 키프레임.\
> 예: `width: 120px` 인 요소에 `50% { width: 400px }` 만 주면 0% 와 100% 가 둘 다 120px 이 된다.

### 3. 이 단축 세 줄은 각각 무엇이 되는가

**출력** (Chrome 151 — 단축을 주고 롱핸드 계산값을 되읽었다)

```text
  s1: name=w  dur=2s  delay=1s  tf=linear  dir=normal  fill=none  iter=1  play=paused
  s2: name=w  dur=1s  delay=2s  tf=linear  dir=normal  fill=none  iter=1  play=paused
  s3: name=w  dur=3s  delay=0s  tf=linear  dir=normal  fill=none  iter=1  play=paused
```

**이름을 맨 뒤에 써도 되는 이유**

- 단축은 **각 칸을 「무엇으로 파싱되느냐」로 알아본다.** `2s` 는 시간, `linear` 는 타이밍 함수, `paused` 는 재생 상태로만 읽히므로 **순서를 몰라도 된다.**
- 시간만은 **둘 다 시간으로 읽히므로** 구분할 길이 순서밖에 없다.\
  명세 문구: *"The first value … that can be parsed as a time is assigned to the animation-duration, and the second value … is assigned to animation-delay."*

**셋의 `fill-mode`**

- 전부 **`none`** 이다. 안 적은 칸은 초기값으로 되돌아가기 때문이다.

**`animation: pulse infinite;`**

- **아무 일도 일어나지 않는다.** `animation-duration` 의 초기값이 `0s` 라 한 회차가 0초에 끝난다.
- 선언은 유효하고 계산값도 남는다. 에러도 경고도 없다 — [52번](../52-transition/2-summary.md)의 「`transition-duration` 을 빼먹는다」와 **똑같은 함정**이다.

### 4. 네 막대는 언제 어디에 있는가

**출력** (Chrome 151 headless — `.lane` 에 마우스를 올린 뒤 시각별 `width`)

| 시각 | 구간 | `none` | `forwards` | `backwards` | `both` |
|---|---|---|---|---|---|
| 0.10s | 지연 중 | 100px | 100px | **50px** | **50px** |
| 0.50s | 지연 중 | 100px | 100px | **50px** | **50px** |
| 1.00s | 시작 | 100px | 100px | 50px | 50px |
| 2.00s | 절반 | 149.98px | 149.98px | 149.98px | 149.98px |
| 3.05s | 끝난 뒤 | **100px** | **250px** | **100px** | **250px** |
| 3.60s | 끝난 뒤 | **100px** | **250px** | **100px** | **250px** |

**0.5초 시점(지연 중)**

- `none`·`forwards` = **100px**(요소의 원래 값) · `backwards`·`both` = **50px**(`from` 키프레임).

**3.5초 시점(끝난 뒤)**

- `none`·`backwards` = **100px**(원래 값으로 되돌아감) · `forwards`·`both` = **250px**(`to` 키프레임).

**2초 시점(움직이는 중)**

- **넷이 완전히 같다**(149.98px). `fill-mode` 는 **양 끝만** 손대고 재생 중에는 아무것도 안 한다.

```text
        delay 1s              duration 2s            끝난 뒤
  none        100 ─────────────  50 → 250  ────────  100
  backwards    50 ─────────────  50 → 250  ────────  100
  forwards    100 ─────────────  50 → 250  ────────  250
  both         50 ─────────────  50 → 250  ────────  250
                ↑ 여기만 갈린다              ↑ 여기만 갈린다
```

**지연을 `0s` 로 하면**

- **`backwards` 와 `none` 을 구분할 수 없다.** 「시작 전」이라는 구간 자체가 사라지기 때문이다.\
  (같은 이유로 `both` 와 `forwards` 도 구분이 안 된다.)
- 그래서 `fill-mode` 를 실험할 때는 **지연을 반드시 준다.**

### 5. `alternate` 를 두 번 돌리면 어디서 멈추는가

**출력** (Chrome 151 headless — `.lane` 에 마우스를 올린 뒤 시각별 `width`)

```text
  시각        .n (normal x2)   .a (alternate x2)
  0.05s       51.98px          51.98px
  0.50s       159.98px         159.98px
  1.00s       279.98px         279.98px
  1.50s       159.98px         160.00px
  2.30s       280px            40px          ★
```

**2.3초 시점**

- `.n` = **280px**(`to`) · `.a` = **40px**(`from`). 둘 다 `forwards` 인데 반대다.

**1.5초 시점에 둘이 하고 있는 것**

```text
  회차 1 (0~1s)        회차 2 (1~2s)
  .n   40 ──> 280   |  40 ──> 280        1.5s: 올라가는 중 (되감기 뒤)
  .a   40 ──> 280   |  280 ──> 40        1.5s: 내려오는 중
                       ↑ 값이 같아도 방향이 반대다
```

- **한 시점의 값만 보면 구분이 안 된다.** 이 주제에서 「한 판의 스크린샷으로 판정하지 마라」의 사례다.

**`forwards` 인데 시작값에서 끝나는 이유**

- `forwards` 가 고정하는 것은 「**마지막 키프레임**」이 아니라 「**마지막으로 재생된 회차의 끝 지점**」이다.
- `alternate` 는 짝수 회차를 거꾸로 돌리므로, **짝수 번 반복하면 마지막 회차의 끝이 `from`** 이다.

**반복을 `3` 으로 바꾸면**

- 회차 3 이 다시 정방향이므로 **280px(`to`)에서 끝난다.**
- 판정 규칙: **`alternate` + 홀수 = `to`, `alternate` + 짝수 = `from`.**

*(진행률 고정 실측으로도 같았다 — `alternate` × 2 는 `currentTime` 2000ms 이후 계속 40px, `reverse` × 1 은 0ms 에 280px 에서 출발했다.)*

### 6. 이 애니메이션은 왜 절반까지 느린가

**출력** (Chrome 151 — 4초 `linear`, 둘 다 `0 → 100@50% → 200`)

```text
  진행 시각   전부 linear   구간별 지정
  t=   0ms    0px           0px
  t= 500ms    25px          9.34px      <- 작다
  t=1000ms    50px          31.53px     <- 작다
  t=1500ms    75px          62.17px     <- 작다
  t=2000ms    100px         100px       <- 50% 에서 만난다
  t=2500ms    125px         125px       <- 같다
  t=3000ms    150px         150px
  t=3500ms    175px         175px       <- 같다
```

**0.5초 시점**

- **작다**(9.34px 대 25px). `from` 에 쓴 `ease-in` 이 0%→50% 구간을 지배해 초반이 거의 안 움직인다.

**2.5초 시점**

- **같다**(125px). `50%` 키프레임에 `linear` 를 써 뒀으므로 후반은 등속이다.

**어느 구간에 적용되나**

- 그 키프레임에서 **다음 키프레임까지 가는 구간**이다. 「이 마디에서 나가는 길」의 리듬이다.

**`to` 에 써 두면**

- **아무 일도 안 난다.** `to` 다음에 갈 키프레임이 없기 때문이다. 에러도 경고도 없다.

### 7. 누가 이기는가

**출력** (Chrome 151 — 둘 다 악보 `0 → 400px` 의 50% 에서 멈춤)

```text
  #q { width: 10px; }                ->  200px    (애니메이션이 이긴다)
  #p { width: 10px !important; }     ->   10px    (!important 가 이긴다)
```

**전환이었다면**

- **정반대다.** 전환 선언은 사다리 맨 위라 작성자 `!important` 로도 못 덮는다([52번](../52-transition/2-summary.md)).

**사다리 순서**

```text
  1. 전환 선언
  2. user-agent !important
  3. 사용자 !important
  4. 작성자 !important
  5. 애니메이션 선언
  6. 작성자 normal
```

**`@keyframes` 안의 `!important`**

- **지는 게 아니라 사라진다.** 명세 문구: *"Properties qualified with !important are invalid and ignored."*

**출력** (Chrome 151 — `@keyframes imp { from { width: 0px !important; height: 14px } to { width: 400px !important; height: 14px } }`)

```text
  ① cssRules 덤프 : CSSKeyframesRule name=imp [ 0%{height: 14px;}  100%{height: 14px;} ]
                                                 ↑ width 가 아예 없다
  ③ width 계산값  : 10px          (기본값 그대로 — 애니메이션이 폭을 안 건드린다)
  대조군(!important 없음) : 200px
```

- 진단 3창 중 **첫 창에서 이미 없다.** 「담겼는데 졌다」가 아니라 「담기지도 않았다」이다.

### 8. 같은 이름을 두 번 쓰면

**출력** (Chrome 151 — 50% 지점, 기본값 `width: 10px`·`height: 14px`)

```text
  ① cssRules 덤프
     CSSKeyframesRule name=dup [ 0%{width: 0px;}   100%{width: 400px;}  ]
     CSSKeyframesRule name=dup [ 0%{height: 10px;} 100%{height: 60px;}  ]
     -> @keyframes 는 두 개가 담겨 있다

  ③ width  = 10px      <- 앞 악보는 아예 안 쓰였다
     height = 35px      <- 뒤 악보만 쓰였다 (10 -> 60 의 50%)
```

**폭과 높이**

- **폭 10px · 높이 35px.**

**`cssRules` 에 몇 개**

- **두 개 다 담겨 있다.** 이름도 둘 다 `dup` 이다.

**합쳐지나**

- **안 합쳐진다.** 명세 문구: 같은 이름이 여럿이면 *"the last one in document order wins, and all preceding ones are ignored."*
- ★ 그래서 **첫 창만 보면 못 잡는다.** 「담겼으니 되겠지」가 함정이다.

**애니메이션 둘이 같은 속성을 건드리면**

**출력** (Chrome 151 — `animation: k1 …, k2 …`, `k1` 은 0→100px, `k2` 는 200→400px, 둘 다 50%)

```text
  k1 의 50% = 50px · k2 의 50% = 300px
  getComputedStyle(width) = 300px      <- 목록에서 뒤에 쓴 k2 가 이긴다
```

- 명세 문구: *"the animation which occurs last in the value of animation-name will override the other animations at that point."*

### 9. 선언은 멀쩡한데 아무 일도 안 난다

**출력** (Chrome 151 — 진단 3창을 전부 열었다)

```text
  ① cssRules 의 @keyframes 이름 : ["real"]
  ② animation-name 계산값        : "typoo"
     animation-duration          : "4s"
  ③ width 계산값                 : 60px        <- 원래 값 그대로

  ★ el.getAnimations().length    : 0           <- 정상인 쪽은 1
```

**세 창의 답**

- **① 담겨 있다**(`real` 은 제대로 들어갔다) · **② `typoo` 를 그대로 돌려준다**(선언 자체는 유효하다) · **③ 60px**(원래 값).

**어디서 잡히나**

- ★★ **진단 3창 어디에서도 안 잡힌다.** 규칙도 담겼고 계산값도 정상적으로 나온다.\
  틀린 것은 값이 아니라 **「그 이름의 악보가 존재하지 않는다」는 사실**인데, `getComputedStyle` 은 그것을 모른다.

**네 번째 창**

- **`Element.getAnimations()`** 다. 애니메이션이 실제로 만들어졌으면 길이가 1 이상이고, 이름이 틀리면 **0** 이다.
- 같은 이유로 `animationstart` 이벤트도 오지 않는다.

> **제4의 진단 창** — 애니메이션 주제에서 「선언했는데 안 돈다」를 가르는 관찰 지점.\
> 예: `getAnimations().length === 0` 이면 그 요소에는 살아 있는 애니메이션이 하나도 없다.

### 10. 진행률을 고정해 재는 법

**몇 % 지점인가**

- **25%** 다. 4초짜리를 `-1s` 지연으로 시작하면 재생이 1초 지난 상태에서 출발한다.

**출력** (Chrome 151 — `@keyframes grow { from { width: 0px } to { width: 400px } }`, 전부 `paused`)

```text
  animation-delay    width 계산값    rect 폭
       0s             0px             0
      -1s             100px           100
      -2s             200px           200
      -3s             300px           300
```

**왜 그렇게 되나**

- 음수 지연은 「**이미 그만큼 진행된 상태에서 시작한다**」는 뜻이다. `paused` 와 합치면 그 자리에서 얼어붙는다.
- 기다릴 필요가 없으므로 **구간 실험(지연 중·끝난 뒤)에 정확하다.**

**`currentTime = 4000` 인데 원래 값으로 돌아온 이유**

**출력** (Chrome 151)

```text
  currentTime=0    -> width = 0px
  currentTime=1000 -> width = 100px
  currentTime=2000 -> width = 200px
  currentTime=3000 -> width = 300px
  currentTime=4000 -> width = 0px      ★
```

- 4000ms 는 **활성 구간의 바깥**이다(구간은 `[0, 4000)`).\
  `animation-fill-mode` 가 `none` 이라 끝난 뒤에는 악보가 얹히지 않고 **요소의 원래 값**(여기선 `width: 0`)이 나온다.
- `forwards` 를 주면 400px 로 남는다 — 4번 문항과 같은 규칙이다.

**`--virtual-time-budget` 으로 재면**

- **「아무 일도 안 일어남」이 찍힌다.** 가상 시간이 먼저 다 흘러 버려 시작·중간이 통째로 없어진다.\
  시간 축이 실시간이어야 하는 실험은 **CDP 로만** 잰다.

*(벽시계 대조 — 실제로 돌린 4초 `linear` 는 1.00s 에 105px, 2.00s 에 205px, 3.00s 에 304.98px 이었다. 고정 판정(100/200/300)과 **일정하게 약 5px** 차이인데, 이는 문서를 띄운 뒤 재생이 시작되기까지의 약 50ms 지연이다. 진행률 자체는 어긋나지 않았다.)*

### 11. 멈출 방법

**출력** (Chrome 151 — `#x { animation: w 2s linear infinite alternate paused } #x:hover { animation-play-state: running }`)

```text
  마우스 올리기 전   play-state=paused   width=40px
  올린 뒤 0.50s      play-state=running  width=105px
          1.00s      play-state=running  width=170px
          1.60s      play-state=running  width=248px
  뗀 직후            play-state=paused   width=250.16px
  그 0.6s 뒤         width=250.16px      <- 그 자리에 그대로 있다
```

**올리기 전 폭**

- **40px**(악보의 0% 이자 요소의 기본 폭). `paused` 라 0% 지점에 멈춰 있다.

**떼면 어떻게 되나**

- **그 자리에 선다.** 250.16px 에서 멈췄고 0.6초 뒤에도 같았다. **되감지 않는다.**

**`paused` 와 「애니메이션을 지우는 것」의 차이**

```text
  animation-play-state: paused        규칙은 살아 있다 -> 그 자리에 얼어붙는다
  animation: none (또는 규칙 제거)     규칙이 사라진다  -> 원래 값으로 튄다
```

- 이 문서의 첫 demo 에서 마우스를 떼면 공이 처음 자리로 돌아가는 것이 **뒤쪽**의 경우다.

**모션 접근성의 정본**

- [목록의 **60번 주제**](../60-prefers-reduced-motion/)(`prefers-reduced-motion`)다. 이 문서의 demo 에는 일부러 넣지 않았다 — 한 블록이 두 가지를 보여 주게 되기 때문이다.

### 12. 다른 주제와 잇기

**커스텀 속성이 계단 하나로만 움직인다**

- **`@property` 등록이 빠졌다.** 등록하지 않은 `--` 속성은 값이 **글자 뭉치**라 중간값을 만들 수 없고, **이산 보간**으로 50% 지점에서 한 번 뒤집힌다.
- 정본은 [37번 주제](../37-at-property/2-summary.md)다 — 거기에 등록 전후를 50% 에서 멈춰 읽은 실측이 있다.

**`left` 대 `transform`**

- **다시 도는 파이프라인 단계가 다르다.**

```text
  left 를 애니메이션        transform 을 애니메이션
  +---------------------+   +---------------------+
  | 매 프레임 스타일 재계산 |   | 주 스레드 카운터가   |
  | + 레이아웃 + 페인트    |   | 전부 0              |
  +---------------------+   +---------------------+
```

- 정본은 [56번 주제](../56-rendering-pipeline-and-will-change/2-summary.md)다 — 속성별 실측 표가 거기에 있다.

**`transform` 의 부작용 둘**

- ① **쌓임 맥락을 만든다** — 정본은 [22번](../22-stacking-context-and-z-index/2-summary.md).
- ② **`fixed`·`absolute` 자손의 포함 블록을 가로챈다** — 정본은 [21번](../21-position-and-containing-block/2-summary.md).
- (자세한 대조는 [54번](../54-transform-2d-and-origin/2-summary.md)에서 다시 잇는다.)

**스크롤에 맞춘 움직임**

- `animation-timeline: scroll()` / `view()` — [목록의 **58번 주제**](../58-scroll-driven-animations/)다. 시간 대신 스크롤 진행을 타임라인으로 쓴다.

## 실행 검증

| 무엇을 | 어떻게 | 결과가 있는 곳 |
|---|---|---|
| `demo` 블록 3개 | Chrome 151 headless + CDP `Input.dispatchMouseEvent` 로 실제 `:hover`, 시각별 `getComputedStyle` | 서머리 (2)·(4)·(5) |
| `fill-mode` 네 값 | `getAnimations().currentTime` 고정 + demo 의 벽시계 샘플링 **두 방법** | 서머리 (4) / 문항 4 |
| `direction` × `iteration-count` | `currentTime` 고정(5벌) + demo 벽시계 | 서머리 (5) / 문항 5 |
| 암묵 키프레임 | `currentTime` 고정, 5시각 | 서머리 (2) / 문항 2 |
| 단축 여덟 칸 | 단축 3벌 → 롱핸드 계산값 되읽기 | 서머리 (3) / 문항 3 |
| 키프레임 안의 타이밍 함수 | `currentTime` 고정, 8시각 대조 | 서머리 (6) / 문항 6 |
| `!important` — 선언 쪽 / 키프레임 안 | `cssRules` 덤프 + 계산값, 대조군 포함 | 서머리 (7) / 문항 7 |
| 같은 이름 `@keyframes` 두 번 | `cssRules` 덤프 + 계산값 | 서머리 (8) / 문항 8 |
| 애니메이션 둘이 같은 속성 | 50% 고정 후 계산값 | 서머리 (8) / 문항 8 |
| 전환과 애니메이션이 겹칠 때 | 도는 전환 위에 애니메이션을 얹었다 뗐다 하며 4시점 샘플 | 서머리 (7) |
| 악보 이름 오타 | 진단 3창 + `getAnimations().length` | 서머리 「어디서 틀리나 1」 / 문항 9 |
| `paused` + 음수 지연 | 4벌 + **벽시계 재생과 대조** | 서머리 (9) / 문항 10 |
| `:hover` 로 `running` | 실제 마우스 입력, 뗀 뒤 0.6초까지 추적 | 서머리 (9) / 문항 11 |

**구현 의존 항목** — 다시 찍어야 하는 것

- **전환과 애니메이션이 겹칠 때 어느 값이 나오나** — 명세 사다리와 어긋나는 자리다. 브라우저가 올라가면 다시 찍는다.
- **`cssRules` 의 직렬화 형식**(`from` → `0%`) — 형식 관찰이다.
- **소수점 이하 값**(`149.984px` 등) — 프레임 경계에 따라 흔들린다. 결론은 여기에 세우지 않았다.

**못 잰 것**

- `animation-composition` 세 값 — **돌려 보지 않았다.** 이 문서에는 규칙 서술만 있다.
- **크로스 브라우저** — 엔진이 Chrome 하나뿐이라 Firefox·Safari 차이는 **재지 않았다.** Baseline 데이터로만 접지했다.

## 용어 풀이

- **`@keyframes`** — 이름 붙은 악보. 요소에 저절로 붙지 않는다.
- **암묵 키프레임** — 안 적은 `0%`/`100%` 를 요소의 계산값으로 채운 것.
- **`animation-fill-mode`** — 연주 전(`backwards`)·연주 후(`forwards`)·둘 다(`both`)·아무것도(`none`, 초기값).
- **`animation-direction`** — 회차별 진행 방향. `alternate` 는 짝수 회차를 거꾸로 돌린다.
- **`animation-iteration-count`** — 반복 횟수. 초기값 `1`, `infinite` 가능, 소수도 된다.
- **`animation-play-state`** — `running`/`paused`. `paused` 는 그 자리에 얼어붙고 되감지 않는다.
- **음수 `animation-delay`** — 「이미 그만큼 진행된 상태에서 시작」. `paused` 와 합치면 진행률을 고정한다.
- **`Element.getAnimations()`** — 살아 있는 애니메이션·전환 객체 목록. 이름 오타를 잡는 **제4의 진단 창**.
- **`currentTime`** — 애니메이션 객체의 현재 시각(ms). 쓰기도 된다.
- **`CSSKeyframesRule`** — `@keyframes` 의 CSSOM 객체. 같은 이름이 여럿이면 **전부 담기지만 마지막만 쓰인다.**
- **캐스케이드 사다리** — 전환 > `!important` 무리 > 애니메이션 > 작성자 normal.
- **이산 보간(discrete interpolation)** — 중간값을 못 만드는 타입의 기본 동작. 50% 에서 한 번 뒤집힌다.

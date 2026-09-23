# css/syntax/53 — `@keyframes` 와 `animation`: 단축·반복·채우기 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [CSS Animations Level 1](https://drafts.csswg.org/css-animations-1/) (`@keyframes`·단축 순서·`fill-mode`·이름 충돌) · [CSS Cascading and Inheritance Level 5](https://drafts.csswg.org/css-cascade-5/) (캐스케이드 사다리에서 애니메이션 선언의 자리). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 `demo` 블록 **3개 전부**와 본문 실험 **13벌**을 **Google Chrome 151.0.7922.173** headless 에 CDP 로 붙여 돌렸다.\
> 진행률을 고정할 때는 **`animation-play-state: paused` + 음수 `animation-delay`** 와 **`Element.getAnimations()` 의 `currentTime` 세팅**을 썼고, 두 방법이 벽시계 실측과 일치하는지 따로 대조했다((9) 참조). `demo` 블록은 `Input.dispatchMouseEvent` 로 실제 마우스를 올린 뒤 시각마다 `getComputedStyle` 을 읽었다(샘플 시각 ±20ms).\
> **엔진은 Chrome 하나다** — 이 머신에서 Firefox headless 는 스크린샷이 산출되지 않고 WebKit 은 없다. 크로스 브라우저는 Baseline 으로만 접지했다.
> **버전** — CSS 에 언어 버전은 없다. Animations (CSS) 는 Baseline **widely**(newly 2015-09-30 → widely 2018-03-30), `animation-composition` 은 **widely**(newly 2023-07-04 → widely 2026-01-04) — `api.webstatus.dev` 조회 결과.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**전환이 「A 에서 B 로 걸어가라」라면, 애니메이션은 「악보를 주고 연주시키는 것」이다.**

[52번](../52-transition/2-summary.md)의 전환은 **값이 바뀌는 것을 브라우저가 알아채야** 시작된다.\
애니메이션은 다르다 — **악보(`@keyframes`)를 미리 써 두고, 요소에 「이 악보를 연주해라」라고 붙인다.**\
아무것도 바뀌지 않아도 스스로 돈다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 악보 | `@keyframes 이름 { … }` |
| 악보에 찍힌 마디 | `0%` · `50%` · `100%`(또는 `from`·`to`) |
| 「이 악보를 연주해라」 | `animation-name: 이름` |
| 한 번 연주하는 데 걸리는 시간 | `animation-duration` |
| 몇 번 반복할지 | `animation-iteration-count` |
| 앞으로 / 뒤로 / 번갈아 | `animation-direction` |
| **연주 전과 연주 후에 무대를 어떻게 둘지** | `animation-fill-mode` |
| 연주를 잠깐 멈춤 | `animation-play-state` |
| 시작 전 뜸들이기 | `animation-delay` |
| 마디 사이를 어떻게 이을지 | `animation-timing-function` |

- **악보가 없으면 아무 일도 안 난다.** 이름을 잘못 쓰면 **에러도 경고도 없이** 조용하다(「어디서 틀리나 1」).
- **연주가 끝나면 무대는 원래대로 돌아간다.** 이것이 `fill-mode` 를 모르면 가장 많이 터지는 자리다.
- **악보의 값은 스타일시트의 선언이 아니다.** 캐스케이드에서 자리가 따로 있다((7)).

```text
전환 (52번)                          애니메이션 (이 주제)

  값이 바뀐다                          내가 시작시킨다 (규칙이 붙는 순간)
      |                                   |
      v                                   v
  A ────────> B                    0% ──> 30% ──> 70% ──> 100%
  두 점 사이만                      들를 곳을 내가 정한다
      |                                   |
      v                                   v
  한 번 가면 끝                      반복·왕복·무한 가능
```

실무에서 터지는 자리는 「**로딩 스피너가 다 돌고 나서 원위치로 튄다**」 와\
「**끝난 뒤 그 자리에 있어야 하는데 처음으로 되돌아간다**」 둘이다.\
둘 다 `animation-fill-mode` 한 낱말이다((4)).

> **키프레임(keyframe)** — 악보에 찍은 마디. 「이 시점에 이 값이어야 한다」를 정한 한 점.\
> 예: `50% { width: 200px }` 은 「절반 지났을 때 폭은 200px」이라는 뜻이다. 그 사이는 브라우저가 채운다.

> **보간(interpolation)** — 두 키프레임 사이의 중간값을 만드는 것.\
> 예: `0%` 에 `50px`, `100%` 에 `250px` 이면 25% 지점은 `100px` 이다(등속일 때).

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **애니메이션이 끝난 뒤 요소는 어디에 있는가** — 마지막 키프레임인가, 원래 값인가, 그것을 무엇이 정하는가.
2. `animation: slide 2s 1s` 에서 **어느 쪽이 지속이고 어느 쪽이 지연인가**, 그리고 여덟 칸을 안 적으면 무엇이 되는가.
3. 같은 속성을 **애니메이션과 스타일시트가 동시에 건드리면** 누가 이기는가 — `!important` 는 어느 쪽인가.

## 동작 방식

### (1) 전환과 무엇이 다른가 — 이 주제의 출발점

**언제 쓰나** — 「이걸 전환으로 해야 하나 애니메이션으로 해야 하나」를 고를 때.

전환의 정본은 [52번](../52-transition/2-summary.md)이다. 여기서는 **갈리는 자리만** 본다.

```text
                 transition (52번)          animation (여기)

  방아쇠          계산값이 바뀔 때            규칙이 붙는 순간 (스스로)
  중간 지점       없다 (A -> B 두 점)         마음대로 (0% 30% 70% 100%)
  반복            못 한다                     iteration-count (infinite 가능)
  왕복            방아쇠가 되돌아가야 한다     direction: alternate 한 줄
  끝난 뒤         바뀐 값이 그대로 남는다      기본은 원래 값으로 되돌아간다 ★
  시작 전         해당 없음                   delay 동안 원래 값 ★
  멈추기          못 한다                     animation-play-state: paused
  캐스케이드      사다리 맨 위                작성자 !important 보다 아래 ★
```

★ 표를 붙인 세 줄이 이 주제의 값어치다. 전환을 알고 온 사람이 정확히 거기서 넘어진다.

비용 — 악보를 한 번 써 두면 여러 요소가 같이 쓴다. 대신 **「지금 어디쯤인가」를 CSS 만 봐서는 알 수 없다** — 진행률은 `getAnimations()` 로만 읽힌다((9)).

### (2) `@keyframes` 는 악보다 — 안 적은 마디는 무엇으로 채우나

**언제 쓰나** — 키프레임을 하나만 쓰거나 `50%` 만 쓰고 「왜 이상하지」 할 때.

```text
@keyframes half { 50% { width: 400px } }      <- 0% 와 100% 를 안 적었다
             |
             v
브라우저가 양 끝을 만들어 준다
             |
             v
  0%   { width: <그 요소의 원래 계산값> }      <- 여기선 120px
  50%  { width: 400px }
  100% { width: <그 요소의 원래 계산값> }      <- 120px
```

*(Chrome 151 실측 — `.q { width: 120px }` 에 위 악보를 4초 `linear` 로 걸고 `currentTime` 을 직접 세팅해 읽었다.)*

```text
  진행 시각      half (50% 만 적음)     only100 (to 만 적음)
  t=   0ms       120px                  120px
  t=1000ms       260px                  190px
  t=2000ms       400px                  260px
  t=3000ms       260px                  330px
  t=3999ms       120.125px              399.922px
```

그림 해설 (한 단계씩):

- `half` 는 **120px 에서 출발해 400px 을 찍고 다시 120px 로 돌아온다.** 양 끝을 요소의 원래 값으로 채운 것이다.
- `only100` 은 `to` 만 적었으므로 **0% 만** 만들어진다 — 120px 에서 400px 까지 곧게 간다.
- 명세 문구: *"If a 0% or from keyframe is not specified, then the user agent constructs a 0% keyframe using the computed values of the properties being animated."*

> **암묵 키프레임(implicit keyframe)** — 안 적은 `0%`/`100%` 를 브라우저가 요소의 원래 계산값으로 만들어 넣는 것.\
> 예: 원래 `width: 120px` 인 요소에 `50% { width: 400px }` 만 주면 120 → 400 → 120 으로 간다.

- `from` 과 `to` 는 각각 `0%`·`100%` 의 별명이다. **`cssRules` 에 담길 때 `0%`/`100%` 로 정규화된다**((8)의 덤프 참조).

```html demo
<div class="track"><i class="ball"></i></div>
<style>
  .track { width: 320px; height: 76px; border: 2px solid #94a3b8; }
  .ball  { display: block; width: 36px; height: 36px; margin: 34px 0 0 4px;
           border-radius: 50%; background: #1d4ed8; }
  @keyframes hop {
    0%   { translate: 0 0 }
    50%  { translate: 140px -30px }
    100% { translate: 276px 0 }
  }
  .track:hover .ball { animation: hop 2s linear 1 both; }
</style>
```

> **보이는 것** — 상자 안에 마우스를 올리면 파란 공이 왼쪽 아래에서 출발해 **가운데서 가장 높이 떠올랐다가** 오른쪽 아래로 내려앉는다. 2초가 걸리고 **한 번만** 간다. 도착한 자리에 그대로 멈춰 있고, 마우스를 떼면 처음 자리로 돌아간다(규칙 자체가 사라지기 때문이다).\
> **바꿔 볼 것** — `50%` 의 `-30px` → `-60px`(더 높이 뜬다) · `linear` → `ease-in-out`(가운데가 빨라진다) · `1` → `2`(두 번 튄다 — 두 번째는 처음 자리로 순간이동한 뒤 다시 간다)

*(Chrome 151 headless 실측 — `.track` 위로 마우스를 올린 뒤 시각별 `translate` 계산값:)*

```text
  t=0.06s   7.00px  -1.50px       <- 막 출발
  t=0.50s   70.00px -15.00px      <- 25% 지점: 가로 70, 세로 -15
  t=1.00s   139.99px -29.99px     <- 50% 지점: 꼭대기
  t=1.50s   207.99px -15.00px
  t=2.31s   276px                 <- 도착 (세로 성분이 0 이라 한 값만 남는다)
```

- **세로는 위로 갔다가 내려온다.** 전환으로는 못 만드는 모양이다 — 들를 곳이 가운데에 있기 때문이다.

### (3) `animation` 단축 — 여덟 칸과 시간 둘의 해석

**언제 쓰나** — 단축 한 줄을 읽거나 쓸 때. 여기가 오해의 절반이다.

```text
animation: <name> <duration> <timing-function> <delay>
           <iteration-count> <direction> <fill-mode> <play-state>

  ★ 순서는 대체로 자유다. 단 시간 값 둘은 순서가 뜻을 정한다.
      첫 번째 시간  ->  duration
      두 번째 시간  ->  delay
      시간이 하나뿐 ->  duration (delay 는 0s)
```

*(Chrome 151 실측 — 단축을 주고 롱핸드 계산값을 되읽었다.)*

```text
  animation: w 2s 1s linear paused;
     -> name=w  duration=2s  delay=1s  timing=linear  play=paused
        direction=normal  fill=none  iteration=1

  animation: 1s 2s linear w paused;        <- 이름을 맨 뒤에 써도 된다
     -> name=w  duration=1s  delay=2s

  animation: w 3s linear paused;           <- 시간이 하나
     -> duration=3s  delay=0s
```

명세 문구: *"The first value in each single-animation that can be parsed as a time is assigned to the animation-duration, and the second value … is assigned to animation-delay."*

- **안 적은 칸은 초기값으로 되돌아간다.** `duration` 의 초기값은 `0s`, `iteration-count` 는 `1`, `fill-mode` 는 `none`, `play-state` 는 `running` 이다.
- ★ 그래서 [52번](../52-transition/2-summary.md)의 함정이 그대로 반복된다 — **단축 뒤에 롱핸드를 쓰면 명시도 싸움이 된다.**\
  이 문서의 fill-mode demo 를 **롱핸드 대신 단축 네 줄로 쓴 이유**가 그것이다((4)).

비용 — 단축은 짧지만 **여덟 칸 전부를 건드린다.** 읽는 사람이 「안 적은 칸은 뭐지」를 늘 되짚어야 한다.

### (4) ★ `animation-fill-mode` — 연주 전과 연주 후의 무대

**언제 쓰나** — 「끝났는데 원위치로 튄다」·「시작 전에 잠깐 원래 모습이 보인다」를 고칠 때. **이 주제에서 가장 자주 쓰인다.**

```text
        delay 1s              duration 2s            끝난 뒤
  |<------------------>|<--------------------->|<------------ …
  t=0                  t=1s                    t=3s

  none        원래 값            보간              원래 값
  backwards   0% 키프레임 값      보간              원래 값
  forwards    원래 값            보간              100% 키프레임 값
  both        0% 키프레임 값      보간              100% 키프레임 값
```

```html demo
<div class="lane"><i class="none"></i><i class="fwd"></i><i class="bwd"></i><i class="both"></i></div>
<style>
  .lane { width: 300px; padding: 6px; border: 2px solid #94a3b8; }
  .lane i { display: block; width: 100px; height: 18px; margin: 5px 0; background: #1d4ed8; }
  @keyframes w { from { width: 50px } to { width: 250px } }
  .lane:hover .none { animation: w 2s linear 1s 1 normal none; }
  .lane:hover .fwd  { animation: w 2s linear 1s 1 normal forwards; }
  .lane:hover .bwd  { animation: w 2s linear 1s 1 normal backwards; }
  .lane:hover .both { animation: w 2s linear 1s 1 normal both; }
</style>
```

> **보이는 것** — 막대 넷은 기본 폭이 100px 로 똑같다. 상자에 마우스를 올리면 **1초 동안 아무것도 안 움직이는데, 그 1초 동안 3·4번 막대만 50px 로 줄어 있다**(`backwards`·`both`). 1초가 지나면 넷이 **같이** 50px 에서 250px 로 2초에 걸쳐 늘어난다. 다 늘어난 뒤에는 **2·4번만 250px 로 남고**(`forwards`·`both`) 1·3번은 100px 로 튕겨 돌아온다.\
> **바꿔 볼 것** — 넷 다 `none` 으로 → 지연 구간과 끝난 뒤가 전부 100px 로 같아진다 · `1s`(지연) → `0s` → 「시작 전」 차이가 안 보이게 되어 `backwards` 와 `none` 을 구분할 수 없다

*(Chrome 151 headless 실측 — 마우스를 올린 뒤 시각별 `width`. 기본 100px · `from` 50px · `to` 250px · 지연 1s · 지속 2s:)*

| 시각 | 구간 | `none` | `forwards` | `backwards` | `both` |
|---|---|---|---|---|---|
| 0.10s | 지연 중 | 100px | 100px | **50px** | **50px** |
| 0.50s | 지연 중 | 100px | 100px | **50px** | **50px** |
| 1.00s | 시작 | 100px | 100px | 50px | 50px |
| 2.00s | 절반 | 149.98px | 149.98px | 149.98px | 149.98px |
| 3.05s | 끝난 뒤 | **100px** | **250px** | **100px** | **250px** |
| 3.60s | 끝난 뒤 | **100px** | **250px** | **100px** | **250px** |

그림 해설 (한 단계씩):

- **`backwards` 는 「시작 전」만, `forwards` 는 「끝난 뒤」만** 손댄다. 둘 다 하려면 `both` 다.
- **움직이는 동안은 넷이 완전히 같다.** 갈리는 곳은 양쪽 끝뿐이다.
- 지연이 `0s` 면 `backwards` 와 `none` 의 차이가 **관찰 불가능**해진다 — 그래서 이 실험은 지연을 반드시 준다.

*(같은 실험을 `paused` + `getAnimations().currentTime` 으로 진행률을 고정해 한 번 더 확인했다. 지연 구간·끝난 뒤 값이 위 표와 같았다. 방법 대조는 (9).)*

비용 — 없다. 다만 **`forwards` 는 끝난 뒤에도 그 선언이 계속 요소를 덮고 있다** — 나중에 JS 나 다른 규칙으로 그 속성을 바꾸려 하면 애니메이션 값이 이긴다((7)).

### (5) `direction` 과 `iteration-count` 가 만나면 어디서 끝나나

**언제 쓰나** — `alternate` 로 왕복시켜 놓고 「왜 처음 자리에서 끝나지」 할 때.

```text
@keyframes w { from { width: 40px } to { width: 280px } }

  normal    x2    40 -> 280 ┊ 40 -> 280        끝: 280 (to)
  alternate x2    40 -> 280 ┊ 280 -> 40        끝:  40 (from) ★
  alternate x3    40 -> 280 ┊ 280 -> 40 ┊ 40 -> 280   끝: 280
  reverse   x1    280 -> 40                    끝:  40
```

```html demo
<div class="lane"><i class="n"></i><i class="a"></i></div>
<style>
  .lane { width: 300px; padding: 6px; border: 2px solid #94a3b8; }
  .lane i { display: block; width: 40px; height: 22px; margin: 5px 0; background: #b91c1c; }
  @keyframes w { from { width: 40px } to { width: 280px } }
  .lane:hover .n { animation: w 1s linear 0s 2 normal    forwards; }
  .lane:hover .a { animation: w 1s linear 0s 2 alternate forwards; }
</style>
```

> **보이는 것** — 마우스를 올리면 막대 둘이 **똑같이** 1초에 걸쳐 40px 에서 280px 로 늘어난다. 1초 시점에 위 막대(`normal`)는 **40px 로 툭 되감기고** 다시 늘어나는데, 아래 막대(`alternate`)는 되감기 없이 **거꾸로 줄어든다**. 2초 뒤 위 막대는 280px 로, 아래 막대는 **40px 로** 멈춘다 — 둘 다 `forwards` 인데 끝나는 자리가 반대다.\
> **바꿔 볼 것** — `2` → `3`(둘 다 280px 에서 끝난다) · `alternate` → `alternate-reverse`(첫 회부터 거꾸로 간다) · `forwards` 를 빼면(둘 다 40px 로 돌아간다)

*(Chrome 151 headless 실측 — 마우스를 올린 뒤 시각별 `width`:)*

```text
  시각        normal x2      alternate x2
  0.05s       51.98px        51.98px
  0.50s       159.98px       159.98px
  1.00s       279.98px       279.98px
  1.50s       159.98px       160.00px      <- 여기서는 값이 같다. 가는 방향이 반대다
  2.30s       280px          40px     ★    <- 끝나는 자리가 반대
```

그림 해설 (한 단계씩):

- **1.5초 시점의 값이 같아서 눈으로는 구분이 안 된다.** `normal` 은 되감고 올라가는 중이고 `alternate` 는 내려오는 중이다 — **한 시점만 보면 같은 값이 나오는 대표 사례**다.
- 끝나는 자리를 정하는 것은 `direction` 과 `iteration-count` 의 **홀짝**이다.\
  `alternate` 는 **짝수 번 반복하면 시작값에서 끝난다.**
- `forwards` 는 「마지막 키프레임」이 아니라 「**마지막으로 재생된 회차의 끝 지점**」에 고정한다. 그래서 `alternate` × 2 는 `from` 값에 고정된다.

*(진행률 고정 실측으로도 같은 결과였다 — `alternate` × 2 는 `currentTime` 2000ms 이후 계속 40px 이었고, `reverse` × 1 은 0ms 에 280px 에서 출발했다.)*

★ **제출 직전 재실행에서 한 칸이 움직였다 — 그 사실 자체가 결론이라 지우지 않고 나란히 남긴다.**

```text
  시각      첫 판 (.n / .a)        재확인 판 (.n / .a)
  0.50s     159.98 / 159.98        163.98 / 163.98
  1.00s     279.98 / 279.98        43.98 / 276        ★ 여기만 크게 다르다
  2.30s     280 / 40               280 / 40           <- 결론은 안 흔들렸다
```

- **1.00초는 회차 1 이 끝나고 회차 2 가 시작되는 바로 그 경계**다. 마우스 입력에서 재생이 시작되기까지의 수십 ms 지연이 판마다 달라, 어느 판은 경계 **직전**을, 어느 판은 **직후**를 찍는다.
- `.n` 의 43.98 은 **회차 2 가 40px 에서 다시 출발한 직후**이고, `.a` 의 276 은 **회차 2 가 280px 에서 거꾸로 내려가기 시작한 직후**다 — 둘 다 (5)의 설명과 어긋나지 않는다.
- **근거로 쓸 칸은 2.30초(끝나는 자리)뿐이다.** 두 판에서 `280 / 40` 으로 한 자리도 안 움직였다.

### (6) 키프레임 안에 타이밍 함수를 두면 — 구간마다 다른 곡선

**언제 쓰나** — 한 애니메이션 안에서 구간마다 리듬을 다르게 하고 싶을 때.

`animation-timing-function` 은 **키프레임 블록 안에도** 쓸 수 있다.\
그때는 **그 키프레임에서 다음 키프레임까지** 가는 구간에 적용된다.

```css
@keyframes perkf {
  from { width: 0px;   animation-timing-function: ease-in }   /* 0% -> 50% 구간 */
  50%  { width: 100px; animation-timing-function: linear }    /* 50% -> 100% 구간 */
  to   { width: 200px }
}
```

*(Chrome 151 실측 — 4초 `linear`, 둘 다 `0 → 100@50% → 200`. 왼쪽은 키프레임에 타이밍 함수 없음:)*

```text
  진행 시각   전부 linear     구간별 지정
  t=   0ms    0px             0px
  t= 500ms    25px            9.34px      <- ease-in 구간: 거의 안 움직인다
  t=1000ms    50px            31.53px
  t=1500ms    75px            62.17px
  t=2000ms    100px           100px       <- 50% 지점에서 만난다
  t=2500ms    125px           125px       <- 여기부터는 둘 다 linear
  t=3500ms    175px           175px
```

- **키프레임의 타이밍 함수는 그 마디에서 「나가는」 구간에만 적용된다.** 마지막 키프레임(`to`)에 써 봐야 갈 곳이 없다.
- `animation` 단축이나 롱핸드로 준 타이밍 함수는 **구간별 지정이 없는 구간의 기본값**이 된다.

### (7) ★ 애니메이션 값은 캐스케이드 어디에 오나

**언제 쓰나** — 「애니메이션 중에 내 `!important` 가 먹나 안 먹나」를 볼 때. [52번](../52-transition/2-summary.md)과 **정반대 답이 나오는 자리**다.

명세(css-cascade-5)의 사다리는 이렇다.

```text
  1. 전환(transition) 선언          <- 52번이 여기
  2. user-agent !important
  3. 사용자 !important
  4. 작성자 !important              <- 애니메이션은 여기에 진다 ★
  5. 애니메이션(animation) 선언     <- 이 주제가 여기
  6. 작성자 normal
  7. 사용자 normal
  8. user-agent normal
```

*(Chrome 151 실측 — 같은 악보(`0 → 400px`)를 50% 에서 멈춘 두 요소:)*

```text
  #q { width: 10px; }                  -> 200px   (애니메이션이 이긴다)
  #p { width: 10px !important; }       ->  10px   (작성자 !important 가 이긴다)
```

- 그래서 **애니메이션을 `!important` 로 덮을 수 있다.** 전환은 못 덮는다([52번](../52-transition/2-summary.md)) — **둘이 반대다.**

★ **`@keyframes` 안의 `!important` 는 이야기가 다르다 — 아예 안 담긴다.**

명세 문구: *"Properties qualified with !important are invalid and ignored."*

*(Chrome 151 실측 — `@keyframes imp { from { width: 0px !important; height: 14px } to { width: 400px !important; height: 14px } }` 를 50% 에서 멈추고 `cssRules` 를 덤프했다:)*

```text
  ① cssRules 에 담긴 것: 0%{height: 14px;}  100%{height: 14px;}
                          ↑ width 선언이 통째로 사라졌다
  ③ getComputedStyle(width) = 10px          <- 기본값 그대로

  대조군 (!important 없음)  = 200px
```

- 「**졌다**」가 아니라 「**담기지도 않았다**」이다. 진단 3창 중 **첫 창에서 이미 없다**([선택자 묶음의 「인자가 비워진 것」](../11-is-where-not/2-summary.md)과 같은 성격).
- 「애니메이션에 `!important` 를 붙여 더 세게 만들자」는 발상은 **정확히 반대 효과**를 낸다 — 그 줄이 사라진다.

★ **전환과 애니메이션이 같은 속성에 동시에 걸리면** — 명세와 실측이 갈렸다.

*(Chrome 151 실측 — `transition: width 20s linear` 를 도는 중(10px → 2010px)에 애니메이션을 얹었다:)*

```text
  전환만 1.0s          width = 110px    CSSTransition(running, 1000)
  애니메이션 얹음       width = 200px    CSSTransition(running,1300) + CSSAnimation(paused,…)
  1s 더 지남           width = 200px    CSSTransition(running,2300)   <- 전환은 계속 돌고 있다
  애니메이션 뗌         width = 269.98px                              <- 전환 자리로 튄다
```

- **전환은 죽지 않고 계속 돌았는데 화면에 나온 값은 애니메이션 쪽**이었다.
- 명세 사다리는 전환이 **위**라고 적는다. **이 자리는 명세 서술과 실측이 어긋난다** — 여기서는 **실측을 관찰로만 적고**, 「보장」으로 적지 않는다(「구현 세부사항 대 언어 보장」 절 참조).

### (8) 이름이 겹치거나 애니메이션이 여럿이면

**언제 쓰나** — 큰 프로젝트에서 `@keyframes fade` 가 두 파일에 있을 때.

```text
@keyframes dup { from { width: 0px }   to { width: 400px } }
@keyframes dup { from { height: 10px } to { height: 60px } }      <- 같은 이름
         |
         v
  cssRules 에는 둘 다 담긴다 (CSSKeyframesRule 두 개, name 둘 다 "dup")
         |
         v
  쓰이는 것은 나중 것 하나뿐 — 합쳐지지 않는다
```

*(Chrome 151 실측 — 위 악보를 50% 에서 멈췄다. 기본값은 `width: 10px`·`height: 14px`:)*

```text
  ① cssRules 덤프
     1.1 CSSKeyframesRule name=dup [0%{width: 0px;} 100%{width: 400px;} ]
     1.2 CSSKeyframesRule name=dup [0%{height: 10px;} 100%{height: 60px;} ]

  ③ getComputedStyle  width = 10px      <- 앞 악보는 아예 안 쓰였다
                      height = 35px     <- 뒤 악보만 쓰였다 (10 -> 60 의 50%)
```

- 명세 문구: 같은 이름이 여럿이면 *"the last one in document order wins, and all preceding ones are ignored."*
- ★ **「합쳐진다」가 아니다.** 앞 악보의 `width` 는 **아무 데도 안 남는다.** `cssRules` 만 보면 둘 다 살아 있는 것처럼 보이므로 **첫 창만 보면 못 잡는다.**
- `from`/`to` 가 덤프에서 `0%`/`100%` 로 나오는 것도 여기서 보인다.

**한 요소에 애니메이션이 여럿이고 같은 속성을 건드리면** — `animation-name` 목록에서 **뒤에 있는 것**이 이긴다.

*(Chrome 151 실측 — `animation: k1 …, k2 …` 둘 다 50% 에서 멈춤. `k1` 은 0→100px, `k2` 는 200→400px:)*

```text
  k1 의 50% = 50px · k2 의 50% = 300px
  getComputedStyle(width) = 300px        <- 뒤에 쓴 k2 가 이긴다
```

명세 문구: *"the animation which occurs last in the value of animation-name will override the other animations at that point."*

### (9) 멈추는 법과 진행률을 고정하는 법

**언제 쓰나** — 무한 애니메이션을 문서에 넣을 때, 그리고 **애니메이션을 시험할 때.**

```text
animation-play-state: paused    그 자리에 멈춘다 (되감지 않는다)
                      running   기본값

animation-delay: -1s            "이미 1초 진행된 상태"에서 시작한다
```

이 둘을 합치면 **진행률을 한 방에 고정**할 수 있다.

```css
/* 4초짜리 악보의 25% 지점에서 멈춘 상태 */
.probe { animation: grow 4s linear -1s paused; }
```

*(Chrome 151 실측 — `@keyframes grow { from { width: 0px } to { width: 400px } }`:)*

```text
  animation-delay    계산된 width     rect 폭
       0s             0px              0
      -1s             100px            100
      -2s             200px            200
      -3s             300px            300
```

`Element.getAnimations()` 를 쓰면 **진행률을 JS 로 직접 세팅**할 수도 있다.

```text
  var a = el.getAnimations()[0];
  a.currentTime = 2000;   ->  width = 200px
  a.currentTime = 4000;   ->  width = 0px    ★ fill-mode 가 none 이라 원래 값으로 떨어진다
```

★ **두 방법이 실제 재생과 어긋나지 않는지 벽시계로 대조했다.**

```text
  실제로 돌린 4s linear(0 -> 400px)      진행률 고정 판정
    t=1.00s  width = 105px                100px
    t=2.00s  width = 205px                200px
    t=3.00s  width = 304.98px             300px
```

- 차이는 **일정하게 약 5px** — 문서를 띄운 뒤 애니메이션이 시작되기까지의 지연(약 50ms)이다. 진행률 자체는 어긋나지 않았다.
- 그래서 **기다리지 않아도 되는 자리에는 고정 쪽이 정확하다.** 「끝난 뒤」·「지연 구간」처럼 **구간이 중요한 실험**은 이쪽으로 재는 게 맞다.

**문서에 넣을 때 멈출 방법**은 `paused` 를 기본으로 두고 `:hover` 에서 `running` 으로 바꾸는 것이다.

*(Chrome 151 실측 — `#x { animation: w 2s linear infinite alternate paused } #x:hover { animation-play-state: running }`:)*

```text
  마우스 올리기 전     play-state=paused   width=40px
  올린 뒤 0.50s        play-state=running  width=105px
          1.00s        play-state=running  width=170px
          1.60s        play-state=running  width=248px
  마우스를 뗀 직후     play-state=paused   width=250.16px
  그 0.6s 뒤           width=250.16px      <- 그 자리에 멈춰 있다
```

- **`paused` 는 되감지 않는다.** 뗀 자리에 그대로 선다.
- 모션 접근성(`prefers-reduced-motion`)은 **이 문서에서 다루지 않는다** — 정본은 [목록의 **60번 주제**](../60-prefers-reduced-motion/)다.

## 형태 — 어디서 헷갈리나

CSS 는 문법 표면이 단순하므로 이 절은 「선언 형태」가 아니라 「**어디서 헷갈리나**」로 읽는다.

### 악보와 연주 지시는 별개의 두 덩어리다

```css
/* ① 악보 — 요소와 무관하다. 문서 어디에 있어도 된다 */
@keyframes pulse {
  from { opacity: 1 }
  50%  { opacity: .3 }
  to   { opacity: 1 }
}

/* ② 연주 지시 — 요소에 붙인다 */
.dot { animation: pulse 1.2s ease-in-out infinite; }
```

- **`@keyframes` 는 선택자가 아니다.** 어떤 요소에도 저절로 붙지 않는다.
- 이름은 전역이다 — **같은 이름을 두 번 쓰면 뒤엣것만 산다**((8)).

### 롱핸드 여덟 개

```css
animation-name:            pulse;
animation-duration:        1.2s;     /* 초기값 0s — 빼면 아무 일도 안 난다 */
animation-timing-function: ease;     /* 초기값 ease */
animation-delay:           0s;
animation-iteration-count: infinite; /* 초기값 1 */
animation-direction:       alternate;/* 초기값 normal */
animation-fill-mode:       both;     /* 초기값 none */
animation-play-state:      running;  /* 초기값 running */
```

### 헷갈리는 자리 셋

```css
/* ① 쉼표 목록은 앞에서부터 되풀이된다 */
animation-name: a, b, c;
animation-duration: 1s, 2s;          /* c 는 1s 를 다시 쓴다 */

/* ② 단축은 안 적은 칸을 초기값으로 되돌린다 */
.x { animation: pulse 1s; }          /* fill-mode 가 none 으로 리셋된다 */
.x { animation-fill-mode: forwards; }/* 명시도가 같고 뒤에 있어 이 경우는 이긴다 */

/* ③ 키프레임 안의 !important 는 그 선언째 버려진다 */
@keyframes bad { to { width: 400px !important } }   /* 이 줄이 사라진다 */
```

## 어디서 틀리나

이 주제의 값어치가 여기 몰려 있다. **전부 에러도 경고도 없다.**

### 1. 악보 이름을 잘못 썼다 — 진단 3창으로는 안 잡힌다

```css
@keyframes real { from { width: 60px } to { width: 300px } }
#b { animation: typoo 4s linear; }     /* 오타 */
```

*(Chrome 151 실측 — 진단 3창을 전부 열어 봤다:)*

```text
  ① cssRules 의 @keyframes 이름 : ["real"]          <- 악보는 잘 담겼다
  ② animation-name 계산값       : "typoo"            <- 선언도 잘 먹었다
     animation-duration          : "4s"               <- 시간도 멀쩡하다
  ③ getComputedStyle(width)      : 60px               <- 그런데 아무 일도 안 난다

  ★ 제4의 창: el.getAnimations().length = 0           <- 여기서만 잡힌다
     (정상인 쪽은 1)
```

- ★★ **진단 3창이 전부 정상인데 아무 일도 안 일어난다.** 규칙도 담겼고 선택자도 잡혔고 계산값도 나온다.\
  **틀린 것은 값이 아니라 「그 이름의 악보가 존재하지 않는다」는 사실**인데, 계산값은 그것을 모른다.
- **`Element.getAnimations()` 를 네 번째 창으로 써라.** 애니메이션 주제에서는 이 창이 없으면 「선언했는데 안 돈다」를 못 가른다.

### 2. 끝난 뒤 원위치로 튄다

기본값이 `animation-fill-mode: none` 이기 때문이다((4)).\
「끝난 자리에 남기려면」 `forwards`, 「시작 전에도 키프레임 값을 쓰려면」 `backwards`, 둘 다면 `both`.

### 3. `alternate` 를 짝수 번 반복하고 끝자리를 기대한다

`forwards` 를 붙였는데도 **처음 값에서 끝난다**((5) 실측: 40px).\
`forwards` 가 고정하는 것은 「마지막 키프레임」이 아니라 「**마지막 회차의 끝 지점**」이다.

### 4. `duration` 을 빼먹는다

```css
animation: pulse infinite;     /* duration 초기값 0s -> 아무 일도 안 난다 */
```

[52번](../52-transition/2-summary.md)의 같은 함정이다. 선언은 유효하고 계산값도 남는다.

### 5. `@keyframes` 안에 `!important` 를 붙인다

그 **선언이 통째로 버려진다**((7) 실측: `cssRules` 에서 사라졌다).\
「더 세게 하려다 아예 없앤」 셈이므로 증상이 「안 먹는다」와 같아 보인다.

### 6. 같은 이름의 악보를 두 파일에서 쓴다

**합쳐지지 않고 나중 것만 산다**((8)).\
앞 악보가 건드리던 속성은 **아무 데도 안 남는다** — 「어떤 속성만 안 움직인다」는 증상으로 나온다.

### 7. 단축 뒤에 롱핸드를 쓴다

[52번](../52-transition/2-summary.md)에서 실제로 걸렸던 함정이다.\
단축이 여덟 칸 전부를 선언하므로, **명시도가 더 높은 단축이 뒤에 오면** 뒤이어 쓴 롱핸드가 조용히 무시된다.\
★ **화면으로는 「비슷하게 움직인다」로 보여 눈으로는 못 잡는다.** 값을 읽어야 잡힌다.

### 8. 끝없이 도는 애니메이션에 멈출 방법을 안 둔다

`infinite` 는 배터리와 모션 민감 사용자 양쪽에 비용이다.\
`animation-play-state: paused` 를 기본으로 두고 사용자 조작으로 `running` 을 주거나,\
모션 설정을 존중한다(정본은 [목록의 **60번 주제**](../60-prefers-reduced-motion/)).

### 9. 「애니메이션이 비싸다」를 속성과 무관하게 말한다

**어느 속성을 애니메이션하느냐가 비용을 정한다.**\
`transform`·`opacity` 는 주 스레드 카운터가 **0** 이고 `width`·`left` 는 매 프레임 레이아웃이 돈다.\
정본은 [56번](../56-rendering-pipeline-and-will-change/2-summary.md)이다 — 거기에 실측 표가 있다.

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 |
|---|---|
| 단축의 첫 시간이 `duration`, 두 번째가 `delay` | **명세**(css-animations-1 — 단축 정의) |
| `!important` 가 붙은 키프레임 선언은 무효 | **명세**(*"Properties qualified with !important are invalid and ignored."*) |
| 같은 이름 `@keyframes` 는 **마지막 것만** 쓰인다 | **명세**(*"the last one in document order wins"*) |
| 안 적은 `0%`/`100%` 를 **요소의 계산값**으로 채운다 | **명세**(암묵 키프레임) |
| 같은 속성에 애니메이션이 여럿이면 **`animation-name` 목록의 뒤**가 이긴다 | **명세** |
| 애니메이션 선언이 **작성자 `!important` 아래**에 있다 | **명세**(css-cascade-5 사다리) |
| 전환과 애니메이션이 겹칠 때 **애니메이션 값이 화면에 나왔다** | ★ **이 브라우저의 관찰**. 명세 사다리는 전환이 위라고 적는다 — **어긋나는 자리다** |
| `cssRules` 에서 `from`/`to` 가 `0%`/`100%` 로 나오는 것 | ★ **직렬화 형식** — 관찰이다. 명세가 형식을 못 박는 자리는 확인하지 않았다 |
| `getAnimations()` 가 없는 이름에 **빈 배열**을 주는 것 | ★ **관찰**. Web Animations 의 정의까지는 확인하지 않았다 |
| 샘플 시각의 소수점 값(`149.984px` 등) | ★ **한 판의 값**. 프레임 경계에 따라 흔들린다 — **재현되는 것은 구간이지 소수점이 아니다** |

★ **흔들리는 칸 / 안 흔들리는 칸**

```text
  안 흔들린다   지연 구간의 값 · 끝난 뒤의 값 · 끝나는 자리(from 이냐 to 냐)
                cssRules 에 담기느냐 · getAnimations().length
  흔들린다      소수점 이하 (149.984 대 150) · 샘플 시각 자체 (±20ms)
```

근거를 세울 때는 **왼쪽 칸만** 쓴다.

## 언제 쓰고 언제 안 쓰나

| 상황 | `@keyframes` + `animation` | 다른 것 |
|---|---|---|
| 상태 A ↔ 상태 B 왕복(`:hover`·클래스 토글) | 과하다 | `transition` ([52번](../52-transition/2-summary.md)) |
| 들를 지점이 가운데에 있다(0% → 50% → 100%) | **쓴다** | 전환으로는 못 한다 |
| 반복·무한 재생(스피너·맥박) | **쓴다** | |
| 왕복(늘었다 줄었다) | **쓴다**(`alternate`) | |
| 방아쇠 없이 페이지가 뜨자마자 움직여야 한다 | **쓴다** | 전환은 값 변화가 있어야 한다 |
| 나타나거나 사라지는 순간 | 되지만 번거롭다 | `@starting-style` ([목록의 **57번 주제**](../57-starting-style-and-entry-exit-transitions/)) |
| 스크롤 진행에 맞춘 움직임 | 시간축은 못 쓴다 | `animation-timeline` ([목록의 **58번 주제**](../58-scroll-driven-animations/)) |
| 페이지 전체가 바뀌는 연출 | 못 한다 | 뷰 전환 ([목록의 **59번 주제**](../59-view-transitions/)) |

판단 규칙 두 줄.

- **들를 곳이 있거나 반복해야 하면 애니메이션, 그 외에는 전환.**
- **움직일 속성은 `transform`·`opacity` 로 표현할 수 있는지 먼저 본다**([56번](../56-rendering-pipeline-and-will-change/2-summary.md)).

## 핵심 문장

- 애니메이션은 **악보(`@keyframes`)를 써 두고 요소에 붙이는 것**이다 — 값이 바뀌지 않아도 스스로 돈다.
- **끝난 뒤 기본은 원래 값으로 되돌아간다.** 그것을 정하는 것이 `animation-fill-mode` 네 값이고, **`backwards` 는 시작 전만, `forwards` 는 끝난 뒤만** 손댄다.
- **`alternate` 를 짝수 번 반복하면 `forwards` 여도 시작값에서 끝난다** — `forwards` 가 고정하는 것은 마지막 **회차**의 끝이다.
- 단축의 시간 둘 중 **앞이 `duration`, 뒤가 `delay`** 다. 하나뿐이면 `duration`.
- **안 적은 `0%`/`100%` 는 요소의 원래 계산값으로 채워진다.**
- **같은 이름 `@keyframes` 는 합쳐지지 않는다** — 나중 것만 살고 앞 것은 흔적도 안 남는다(`cssRules` 에는 둘 다 보인다).
- **`@keyframes` 안의 `!important` 는 그 선언을 통째로 없앤다.**
- 애니메이션 선언은 **작성자 `!important` 보다 아래**다 — 전환([52번](../52-transition/2-summary.md))과 반대다.
- **악보 이름 오타는 진단 3창에 안 걸린다** — `getAnimations().length` 가 네 번째 창이다.

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 53번) · 「버전·지원 기준」의 Baseline 표
- [52번 주제 — `transition`](../52-transition/2-summary.md) — ★ **전환의 정본이다.** 보간 가능 조건·타이밍 함수·되돌리기 규칙은 전부 거기. **여기는 「전환으로는 못 하는 것」부터 시작한다** — 들를 지점·반복·왕복·재생 제어.
- [54번 주제 — `transform` 2D](../54-transform-2d-and-origin/2-summary.md) — 애니메이션에 태우기 가장 싼 속성. **그쪽은 「무엇이 어디로 가나」, 여기는 「시간을 따라 어떻게 가나」.**
- [56번 주제 — 렌더링 파이프라인](../56-rendering-pipeline-and-will-change/2-summary.md) — ★ **「어느 속성이 비싼가」의 정본.** 여기서는 「비싸다」는 말만 하고 수치는 거기에 있다.
- [37번 주제 — `@property`](../37-at-property/2-summary.md) — ★ **커스텀 속성을 애니메이션하려면 등록이 필요하다는 것의 정본.** 등록 안 한 `--x` 는 이산 보간으로 **계단 하나**가 된다.
- [01번 주제 — 캐스케이드](../01-cascade-and-priority/2-summary.md) — 사다리 전체와 단축이 하위 속성을 되돌리는 규칙의 정본. 여기는 **애니메이션 선언이 그 사다리 어디에 앉나**만 본다.
- [목록의 **57번 주제**](../57-starting-style-and-entry-exit-transitions/)(`@starting-style`) — 나타나는 요소를 전환에 태우는 법
- [목록의 **58번 주제**](../58-scroll-driven-animations/)(스크롤 연동 애니메이션) — 시간 대신 스크롤을 타임라인으로 쓰기
- [목록의 **60번 주제**](../60-prefers-reduced-motion/)(`prefers-reduced-motion`) — ★ **모션 접근성의 정본.** 이 문서의 demo 에는 일부러 넣지 않았다.
- [`reference/render-rules.md`](../../../../../../reference/render-rules.md) — 이 문서의 `demo` 블록 규칙

## 용어 풀이

- **`@keyframes`** — 이름 붙은 악보. 시점별 값을 적어 둔 규칙 덩어리. 선택자가 아니다.
- **키프레임(keyframe)** — 악보의 한 마디. `0%`·`50%`·`100%` 또는 `from`·`to`.
- **암묵 키프레임(implicit keyframe)** — 안 적은 `0%`/`100%` 를 브라우저가 요소의 계산값으로 만들어 넣는 것.
- **`animation-name`** — 어느 악보를 연주할지. 없는 이름이면 조용히 아무 일도 안 난다.
- **`animation-duration`** — 한 회차에 걸리는 시간. **초기값 `0s`** — 빼먹으면 아무 일도 안 난다.
- **`animation-delay`** — 시작 전 기다리는 시간. 단축에서 **두 번째** 시간 값. 음수면 「이미 그만큼 진행된 상태」로 시작한다.
- **`animation-iteration-count`** — 반복 횟수. 초기값 `1`. `infinite` 가능. 소수(`2.5`)도 된다.
- **`animation-direction`** — `normal`·`reverse`·`alternate`·`alternate-reverse`. 회차마다 진행 방향을 정한다.
- **`animation-fill-mode`** — 연주 전(`backwards`)·연주 후(`forwards`)·둘 다(`both`)·아무것도 안 함(`none`, 초기값).
- **`animation-play-state`** — `running`(초기값)·`paused`. `paused` 는 **되감지 않고 그 자리에 선다.**
- **`animation-timing-function`** — 마디 사이를 잇는 리듬. **키프레임 블록 안에 두면 그 구간에만** 적용된다.
- **`CSSKeyframesRule`** — `@keyframes` 가 `cssRules` 에 담길 때의 객체. `name` 과 자식 키프레임 목록을 갖는다.
- **`Element.getAnimations()`** — 그 요소에서 실제로 살아 있는 애니메이션·전환 객체 목록. **「선언했는데 안 돈다」를 가르는 네 번째 진단 창.**
- **`currentTime`** — 애니메이션 객체의 현재 시각(ms). 읽기도 쓰기도 된다 — 진행률을 직접 세팅할 수 있다.
- **캐스케이드 사다리** — 어느 선언이 이기는지를 정하는 순서. 전환이 맨 위, 그 아래가 `!important` 무리, 그 아래가 애니메이션.

---

## 더 들어가면

- **`animation-composition`**(Baseline widely, newly 2023-07-04 → widely 2026-01-04)은 애니메이션 값을 **밑값에 더할지 덮을지**를 정한다 — `replace`(기본)·`add`·`accumulate`. `transform` 처럼 누적이 뜻을 갖는 속성에서 쓸모가 있다. 이 문서에서는 **돌려 보지 않았다.**
- `animationstart`·`animationiteration`·`animationend` 이벤트가 있다.\
  ★ **악보 이름이 틀리면 `animationstart` 도 안 온다** — (「어디서 틀리나 1」의 `getAnimations().length = 0` 과 같은 사실이다). JS 로 끝을 기다린다면 타임아웃 대비가 필요하다.
- `animation-iteration-count` 에 소수를 쓸 수 있다(`2.5`). 마지막 회차는 중간에서 끊긴다.
- `animation-range`·`animation-timeline` 은 시간 대신 **스크롤·요소 가시 구간**을 타임라인으로 쓴다([목록의 **58번 주제**](../58-scroll-driven-animations/)).
- 커스텀 속성(`--x`)을 애니메이션하려면 [`@property`](../37-at-property/2-summary.md) 등록이 필요하다.\
  등록 안 한 것은 **이산 보간**이라 50% 지점에서 한 번 뒤집히는 계단이 된다.
- 이 문서의 모든 진행률 고정 실측은 **`paused` + 음수 지연** 또는 **`currentTime` 세팅**으로 얻었다.\
  ★ 이 방법은 **`--virtual-time-budget` 과 다르다** — 가상 시간을 쓰면 「아무 일도 안 일어남」이 찍힌다. 시간 축이 실시간이어야 하는 실험은 CDP 로만 잰다.

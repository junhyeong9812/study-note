# css/syntax/27 — Grid 트랙 정의: `fr`·`minmax()`·`repeat()`·`auto-fill`/`auto-fit` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [CSS Grid Layout Level 1](https://drafts.csswg.org/css-grid-1/) (트랙 크기 결정 알고리즘·`fr`·`minmax()`·`repeat()`) · [CSS Box Sizing Level 3](https://drafts.csswg.org/css-sizing-3/) (`min-content`/`max-content`/`fit-content()`). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 `demo` 블록 **4개 전부**와 본문의 트랙 값 표를 **Google Chrome 151.0.7922.173** headless 에 실제로 띄워 `getComputedStyle(el).gridTemplateColumns` 로 **엔진이 푼 트랙 값**을 읽고, 항목 자리는 `getBoundingClientRect()` 로 따로 쟀다.\
> 본문의 px 값은 전부 그 실측값이다. **엔진은 Chrome 하나다** — Firefox 155.0.1 은 이 환경에서 headless 스크린샷이 산출되지 않고 WebKit 은 이 머신에 없다. 「두 엔진에서 확인했다」고 적지 않았다.
> **버전** — Grid 는 Baseline **widely**(newly 2017-10-17 → widely 2020-04-17). `subgrid` 만 늦다(widely 2026-03-15 — 목록의 [**30번 주제**](../30-subgrid/)).
> **여기서 다루지 않는 것** — 트랙에 **무엇을 놓는가**는 [**28번**](../28-grid-placement/), **이름으로** 놓는 것은 [**29번**](../29-grid-template-areas/)이다. `min-content`/`max-content` 자체의 정의는 [목록의 **31번 주제**](../31-intrinsic-sizing-and-aspect-ratio/)가 정본이고 여기서는 **트랙 값으로 쓰일 때**까지만 쓴다. 정렬(`justify-*`/`align-*`)의 정본은 [**24번**](../24-flexbox-axes/)이고, 여기서는 **Grid 에서 의미가 갈리는 것만** 쓴다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 수치는 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**트랙 정의 = 방에 칸막이를 미리 세우는 일. `fr` 은 「고정 가구를 들여놓고 남은 바닥」을 나눠 갖는 몫이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 방 | grid 컨테이너 (`display: grid` 를 준 요소) |
| 미리 세운 칸막이 사이의 공간 | **트랙(track)** — 행 하나 또는 열 하나 |
| 칸막이 자체 | **격자 라인(grid line)** — 트랙 사이의 경계 |
| 「이 자리는 120cm」 | 고정 트랙 (`120px`) |
| 「고정 가구 빼고 남은 바닥을 반씩」 | **`fr` 트랙** |
| 「최소 이만큼, 최대 저만큼」 | `minmax()` |
| 「같은 칸막이를 들어가는 만큼 반복」 | `repeat(auto-fill, …)` |

- 방의 폭이 600cm 이고 고정 가구가 200cm 를 먹으면, **`fr` 이 나누는 것은 600 이 아니라 400** 이다.\
  이 한 문장이 이 주제의 전부이고, 여기서 틀리면 나머지가 전부 어긋난다.
- 칸막이를 **몇 개** 세울지는 내가 정할 수도 있고(`repeat(3, …)`), **들어가는 만큼** 세우라고 시킬 수도 있다(`repeat(auto-fill, …)`).
- 뒤엣것은 **방의 폭이 바뀌면 칸 수가 바뀐다.** 미디어 쿼리 없는 반응형이 여기서 나온다.

```text
grid-template-columns: 200px 1fr 1fr   (컨테이너 500px)

|<------------------------ 500px ------------------------>|
+-------------------+------------------+------------------+
|      200px        |       1fr        |       1fr        |
|   (고정 가구)      |<--- 남은 300px 을 1:1 로 나눈다 --->|
+-------------------+------------------+------------------+
        ^ 이것을 먼저 떼고                150px      150px
```

*(Chrome 151 headless 실측: `getComputedStyle(el).gridTemplateColumns` → `200px 150px 150px`.)*

> **트랙(track)** — 격자의 행 하나 또는 열 하나. 라인 두 개 사이의 띠다.\
> 예: `grid-template-columns: 100px 100px` 은 열 트랙 **둘**과 세로 라인 **셋**을 만든다.

> **격자 라인(grid line)** — 트랙과 트랙 사이의 경계선. 화면에 안 보이지만 번호가 붙어 있다.\
> 예: 열 트랙이 둘이면 세로 라인은 1·2·3 세 개다. 라인 번호로 배치하는 것은 [**28번**](../28-grid-placement/)이다.

> **`fr`(fraction)** — 「남는 공간의 몫」을 뜻하는 grid 전용 단위.\
> 예: `1fr 2fr` 은 남은 공간을 1:2 로 나눈다. **전체를 1:2 로 나누는 것이 아니다.**

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `1fr` 은 **무엇의** 1 인가 — 컨테이너 전체인가, 남은 공간인가.
2. `1fr` 을 줬는데 **항목이 안 줄어드는** 것은 왜인가, 무엇으로 고치나.
3. `auto-fill` 과 `auto-fit` 은 **언제 같고 언제 갈리나** — 그 차이를 무엇으로 확인하나.

## 동작 방식

### (0) 도구부터 — `getComputedStyle` 이 「푼 트랙」을 돌려준다

**언제 쓰나** — Grid 에서 무엇을 확인하든 맨 먼저. **칸 수를 눈으로 세면 틀린다.**

```text
내가 쓴 것                                     엔진이 돌려주는 것
grid-template-columns:                         getComputedStyle(el)
  repeat(auto-fill, minmax(120px, 1fr))          .gridTemplateColumns
            │                                            │
            └──────── 레이아웃 ─────────────────────────> "132px 132px 132px 132px 132px"
                                                          ^ 트랙 수도 트랙 폭도 한 줄에 나온다
```

- **선언이 아니라 결과가 나온다.** `repeat()`·`auto-fill`·`fr`·`minmax()` 가 전부 px 로 풀려서 온다.
- 그래서 **「칸이 몇 개인가」를 세는 유일하게 안전한 방법**이 이것이다 — 스크린샷을 눈으로 세면 틀린다.
- 항목이 **어디 놓였나**는 이 값으로 알 수 없다. 그것은 `getBoundingClientRect()` 로 따로 잰다.\
  **트랙 정의와 항목 배치를 섞지 않는다** — 다른 두 질문이다.

> **계산값(resolved value)** — `getComputedStyle` 이 돌려주는 값. 속성에 따라 계산값이거나 사용값이다.\
> 예: `grid-template-columns` 는 **사용값**이 와서 `1fr` 이 `150px` 로 풀려 있다. 어느 단계 값이 오는지의 정본은 [목록의 **04번 주제**](../04-value-processing-stages/)다.

### (1) 진단 3창 — 무효한 트랙 정의는 소리 없이 버려진다

**언제 쓰나** — 「트랙을 줬는데 안 먹는다」가 나왔을 때. CSS 는 에러가 없는 언어다.

```text
① document.styleSheets[0].cssRules       규칙에 선언이 담겼나?
        ↓  담겼다                          └─ 안 담겼으면 = 파싱 단계에서 버려짐
② el.querySelectorAll / 선택자 매치        내 요소에 걸렸나?
        ↓  걸렸다                          └─ 안 걸렸으면 = 선택자 문제
③ getComputedStyle(el).gridTemplateColumns 이겼나? 무엇으로 풀렸나?
           └─ 앞 선언 값이 그대로면 = 내 선언이 무효라 버려진 것
```

**대조군을 먼저 깔면 ③ 하나로 ①까지 판정된다.** 같은 규칙에 `100px` 을 먼저 쓰고 그 아래 검사할 값을 쓴다 —
계산값이 `100px` 이면 뒤엣것이 버려진 것이다.

```css
#t { grid-template-columns: 100px;                       /* 대조군 */
     grid-template-columns: repeat(auto-fill, 1fr); }    /* 검사 대상 */
```

*(Chrome 151 headless 실측 — 위 규칙의 `cssRules[i].style.gridTemplateColumns` 가 `"100px"` 이고 계산값도 `100px`. 뒤 선언이 **CSSOM 에 아예 안 들어갔다** — 파싱 단계에서 버려졌다는 뜻이다.)*

| 쓴 것 | 규칙에 담겼나 | 계산값 | 판정 |
|---|---|---|---|
| `repeat(auto-fill, 1fr)` | ✗ | `100px` | **무효** — 자동 반복에 `fr` 을 못 쓴다 |
| `repeat(auto-fill, auto)` | ✗ | `100px` | **무효** — 자동 반복에 `auto` 를 못 쓴다 |
| `repeat(auto-fill, 150px) repeat(auto-fit, 100px)` | ✗ | `100px` | **무효** — 자동 반복은 목록에 **하나만** |
| `repeat(auto-fill, minmax(150px, auto))` | ✓ | `150px 150px 150px 150px` | **유효** — 최솟값이 고정이면 된다 |
| `repeat(auto-fill, minmax(min-content, 1fr))` | ✗ | `100px` | **무효** — 최솟값이 내재적이면 안 된다 |
| `repeat(2, 100px 50px)` | ✓ | `100px 50px 100px 50px` | **유효** — 목록을 통째로 반복한다 |

- 경계는 「**자동 반복의 칸 크기가 컨테이너 폭과 무관하게 먼저 정해지는가**」다.\
  `fr` 도 `auto` 도 `min-content` 도 「폭을 알아야 정해지는 값」이라, 그걸로는 **몇 개 들어가는지 셀 수가 없다.**
- `minmax(150px, auto)` 는 **최솟값 150px 으로 개수를 세고** 나서 늘린다 — 그래서 된다.
- 오류 복구의 정본은 [목록의 **07번 주제**](../07-syntax-and-error-recovery/)다.

비용 — 없다. 다만 **버려진 줄은 화면에도 콘솔에도 흔적이 없다.** ③을 안 읽으면 영원히 모른다.

### (2) `fr` — 남은 공간의 몫이지 전체의 몫이 아니다

**언제 쓰나** — 고정 폭 트랙과 유동 트랙을 섞을 때. **이 주제에서 가장 자주 틀리는 자리다.**

```html demo
<div class="g"><i>A</i><i>B</i><i>C</i></div>
<style>
  .g { display: grid; width: 500px;
       grid-template-columns: 200px 1fr 1fr;   /* fr 은 200px 을 뺀 나머지를 나눈다 */
       border: 2px solid #94a3b8; }
  .g i { background: #bfdbfe; font: 14px system-ui; font-style: normal;
         outline: 1px solid #2563eb; }
</style>
```

> **보이는 것** — 파란 칸 셋이 가로로 붙어 있고 **첫 칸이 200px, 나머지 둘이 각각 150px** 다. 첫 칸이 나머지보다 눈에 띄게 넓다. 셋을 합치면 테두리 안쪽 500px 를 꽉 채운다.\
> **바꿔 볼 것** — `200px` → `100px` 하면 나머지 둘이 각각 **200px** 로 커진다(남은 공간이 400px 이 되므로) · `1fr 1fr` → `2fr 1fr` 하면 **200px · 100px** 로 2:1 이 된다 · `200px` → `50%` 로 바꿔 보고 계산값이 어떻게 나오는지 읽어 보라

*(Chrome 151 headless 실측 — `gridTemplateColumns` 계산값: `200px 1fr 1fr` → `200px 150px 150px` · `100px 1fr 1fr` → `100px 200px 200px` · `200px 2fr 1fr` → `200px 200px 100px`. 항목 자리는 `getBoundingClientRect()` 로 따로 쟀다: x=2 / 202 / 352.)*

```text
틀린 머릿속 그림                        실제
500px 을 1:1:1 로?                     200px 을 먼저 떼고 남은 300px 을 1:1 로
+--------+--------+--------+           +-------------+-------+-------+
| 166.7  | 166.7  | 166.7  |           |    200px    | 150px | 150px |
+--------+--------+--------+           +-------------+-------+-------+
     x  그렇지 않다                          ^ 고정   ^ 남은 공간의 몫
```

그림 해설 (한 단계씩):

- 엔진은 먼저 **고정·내재적 트랙을 전부 확정**하고, 그 합을 컨테이너 폭에서 뺀다.
- 남은 값을 **자유 공간**(free space)이라 부르고, `fr` 의 합으로 나눈 것이 `1fr` 한 개의 크기다.
- `gap` 도 자유 공간에서 먼저 빠진다 — 아래 (5)를 보라.

**`fr` 의 합이 1보다 작으면 남은 공간을 다 안 쓴다.**

```text
grid-template-columns: 0.5fr 0.5fr   (600px)   -> 300px 300px   (합 1.0 이라 꽉 찬다)
grid-template-columns: 0.25fr        (600px)   -> 남은 공간의 1/4 만 쓴다
```

*(Chrome 151 headless 실측: 600px 컨테이너에서 `0.5fr 0.5fr` → `300px 300px`.)*

비용 — 트랙 크기 결정은 컨테이너 폭이 정해진 뒤에 한 번 돈다. **`fr` 은 폭이 정해져야 풀리므로** 내용에 따라 컨테이너가 늘어나는 상황(`width: max-content` 등)에서는 뜻이 달라진다.

### (3) `1fr` 의 숨은 최솟값이 `auto` 다 — 항목이 안 줄어드는 함정

**언제 쓰나** — 「칸을 반씩 나눴는데 한쪽이 삐져나간다」·「가로 스크롤이 생긴다」가 나왔을 때.

```text
1fr 은 사실 이것의 줄임말이다

    1fr  ==  minmax(auto, 1fr)
              ^^^^
              이 최솟값이 항목의 min-content 아래로는 절대 안 내려간다
```

```html demo
<div class="g bad"><i>Supercalifragilisticexpialidocious</i><i>B</i></div>
<div class="g fix"><i>Supercalifragilisticexpialidocious</i><i>B</i></div>
<style>
  .g { display: grid; width: 300px; margin-bottom: 8px; border: 2px solid #94a3b8; }
  .bad { grid-template-columns: 1fr 1fr; }                       /* 최솟값이 auto */
  .fix { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); } /* 최솟값을 0 으로 */
  .g i { background: #bfdbfe; font: 14px system-ui; font-style: normal;
         outline: 1px solid #2563eb; }
</style>
```

> **보이는 것** — 위아래 두 줄 다 폭이 300px 인데 **칸이 나뉘는 자리가 다르다.** 위(`1fr 1fr`)는 긴 단어가 들어간 첫 칸이 넓어져 경계가 오른쪽으로 밀려 있고, 아래(`minmax(0, 1fr)`)는 **정확히 절반**에서 갈린다. 아래 줄에서는 긴 단어가 자기 칸을 넘어 옆 칸 위로 삐져나온다.\
> **바꿔 볼 것** — `.bad` 에 `overflow: hidden` 을 더하면 `minmax(0, 1fr)` 없이도 **150px · 150px** 이 된다(자동 최솟값이 0 이 되므로) · `.fix` 의 항목에 `overflow: hidden; text-overflow: ellipsis; white-space: nowrap` 을 주면 삐져나온 글자가 `…` 로 잘린다

*(Chrome 151 headless 실측 — `gridTemplateColumns` 계산값: `1fr 1fr` → **`215.031px 84.9688px`** · `minmax(0, 1fr) minmax(0, 1fr)` → **`150px 150px`**. `.bad` 에 `overflow: hidden` 을 더한 판은 `150px 150px` 이었다.)*

```text
  1fr 1fr (300px)                         minmax(0,1fr) x2 (300px)
+------------------------+-------+      +------------+------------+
| Supercalifragilistic…  |   B   |      | Supercali… |     B      |
+------------------------+-------+      +------------+------------+
        215.031px         84.969px           150px        150px
  긴 단어가 트랙을 밀어냈다                반반. 글자가 칸 밖으로 넘친다
```

**컨테이너가 더 좁으면 넘쳐 나간다.** 같은 내용을 200px 컨테이너에 넣은 판:

```text
1fr 1fr           -> 251.312px 10.5156px   (합 261.8 > 200)  scrollWidth 262 : 가로 스크롤
minmax(0,1fr) x2  -> 100px 100px           (합 200 = 200)    트랙은 안 넘친다
```

*(Chrome 151 headless 실측 — 200px 컨테이너에서 컨테이너 `scrollWidth` 가 262 대 251, `clientWidth` 는 둘 다 200.)*

그림 해설 (한 단계씩):

- `1fr` 의 최솟값 `auto` 는 grid 항목에서 **자동 최소 크기**로 풀리고, 그 값이 대개 `min-content`(못 쪼개는 가장 긴 조각)다.
- 그래서 **트랙이 항목보다 작아질 수가 없다** — 내용이 트랙을 밀어낸다.
- 고치는 법 둘: **`minmax(0, 1fr)`** 로 최솟값을 0 으로 내리거나, **항목에 `overflow` 를 `visible` 이 아닌 값으로** 준다.\
  뒤엣것이 듣는 이유는 자동 최소 크기 규칙 자체가 「`overflow` 가 `visible` 일 때만」이기 때문이다.
- ★ 이것은 flex 의 `min-width: auto` 함정과 **같은 모양의 함정**이다. 그쪽 정본은 [목록의 **25번 주제**](../25-flex-shorthand-and-sizing/)다.

비용 — `minmax(0, 1fr)` 은 **넘치는 글자를 안 보이게 해 주지 않는다.** 트랙만 반반으로 만든다. 글자 자르기는 `overflow`·`text-overflow` 의 몫이다.

### (4) `minmax()`·`repeat()` — 트랙 값을 만드는 두 도구

**언제 쓰나** — 「최소 이만큼은 확보하되 남으면 늘려라」·「같은 칸을 N개」를 쓸 때.

```text
minmax(<최소>, <최대>)
         │       └── 남으면 여기까지 늘어난다
         └── 여기 아래로는 안 줄어든다

  minmax(100px, 200px)  ->  100 ~ 200 사이에서 결정
  minmax(150px, 1fr)    ->  최소 150, 남으면 fr 로 늘어남   <- 반응형의 기본형
  minmax(0, 1fr)        ->  최소 0     (3)의 처방
  minmax(auto, 1fr)     ->  == 1fr

repeat(<횟수 또는 자동>, <트랙 목록>)
  repeat(3, 1fr)        ->  1fr 1fr 1fr
  repeat(2, 100px 50px) ->  100px 50px 100px 50px     <- 목록을 통째로 반복
  repeat(auto-fill, …)  ->  들어가는 만큼             <- (6)
```

*(Chrome 151 headless 실측 — 600px 컨테이너: `minmax(100px,200px) 1fr` → `200px 400px` · `repeat(3, 1fr)` → `200px 200px 200px` · `repeat(2, 100px 50px)` → `100px 50px 100px 50px`.)*

- `minmax()` 의 **최대가 최소보다 작으면 최대가 무시된다**(최소가 이긴다).
- `repeat()` 의 첫 인자는 **정수**이거나 `auto-fill`/`auto-fit` 이다. 음수·0·소수는 안 된다.
- `repeat()` 안에는 **라인 이름도 같이 넣을 수 있다** — [**29번**](../29-grid-template-areas/)에서 쓴다.

### (5) 내재적 크기 키워드가 트랙 값으로 올 때

**언제 쓰나** — 「내용만큼만」 차지하는 열(아이콘 열·라벨 열)을 만들 때.

```html demo
<div class="g"><i>짧다</i><i>아주 아주 아주 긴 제목이다</i><i>C</i></div>
<style>
  .g { display: grid; width: 500px; gap: 4px; border: 2px solid #94a3b8;
       grid-template-columns: min-content max-content 1fr; }
  .g i { background: #bfdbfe; font: 14px system-ui; font-style: normal;
         outline: 1px solid #2563eb; }
</style>
```

> **보이는 것** — 첫 칸이 **글자 한 자 폭**으로 아주 좁아지면서 「짧다」가 **두 줄로 세로로 쌓이고**, 둘째 칸은 「아주 아주 아주 긴 제목이다」가 **한 줄에 다 들어가는 폭**으로 잡히며, 셋째 칸이 **남은 폭 전부**를 먹는다. 그래서 컨테이너 높이가 한 줄(20px)이 아니라 **두 줄 높이**(40px)가 된다.\
> **바꿔 볼 것** — `min-content` → `max-content` 하면 첫 칸이 **25.766px** 이 되면서 「짧다」가 한 줄에 펴진다 · `min-content` → `fit-content(20px)` 하면 첫 칸이 정확히 **20px** 이 된다 · 셋째의 `1fr` → `min-content` 로 바꿔 보고 컨테이너 오른쪽에 빈 자리가 생기는지 보라

*(Chrome 151 headless 실측 — `gridTemplateColumns` 계산값 `12.8906px 157.359px 321.75px`, 컨테이너 내용 폭 500px, 행 높이 40px, 한 줄 높이 20px. `min-content` 트랙 12.89px 은 한글 한 글자 폭이고, 같은 글자의 `max-content` 는 25.766px 이었다. 「바꿔 볼 것」의 두 값도 같은 방법으로 쟀다 — `max-content` → `25.7656px …`, `fit-content(20px)` → `20px …`.)*

```text
min-content          max-content            1fr
+----+  +------------------------+  +----------------------------+
|짧  |  |아주 아주 아주 긴 제목이다 |  |C                           |
|다  |  +------------------------+  +----------------------------+
+----+        157.359px                     321.75px
12.89px
 ^ 못 쪼개는 가장 좁은 폭        ^ 줄바꿈 없이 필요한 폭   ^ 남은 전부
```

- `fit-content(<길이>)` 는 **`min(max-content, max(min-content, <길이>))`** 처럼 동작한다 —\
  내용이 작으면 내용만큼, 크면 지정한 길이에서 멈춘다.\
  *(실측: `fit-content(100px) 1fr` → `100px 500px`.)*
- 이 셋의 **정의 자체**는 [목록의 **31번 주제**](../31-intrinsic-sizing-and-aspect-ratio/)가 정본이다. 여기서는 **트랙 값으로 쓰일 때의 성질**까지만 쓴다.
- ★ **`auto` 트랙은 `min-content`·`max-content` 와 다르다** — `auto` 는 **늘어날 수 있고**(남은 공간이 있고 `justify-content` 가 `normal`/`stretch` 면), 앞의 둘은 안 늘어난다.

### (6) `auto-fill` 과 `auto-fit` — 빈 트랙이 남느냐 접히느냐

**언제 쓰나** — 미디어 쿼리 없이 「폭에 맞춰 칸 수가 알아서 바뀌는」 격자를 만들 때.

```html demo
<div class="g fill"><i>1</i><i>2</i></div>
<div class="g fit"><i>1</i><i>2</i></div>
<style>
  .g { display: grid; width: 700px; gap: 10px; margin-bottom: 8px;
       border: 2px solid #94a3b8; }
  .fill { grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); }
  .fit  { grid-template-columns: repeat(auto-fit,  minmax(120px, 1fr)); }
  .g i { background: #bfdbfe; font: 14px system-ui; font-style: normal;
         outline: 1px solid #2563eb; }
</style>
```

> **보이는 것** — 항목은 양쪽 다 둘뿐인데 **칸 폭이 전혀 다르다.** 위(`auto-fill`)는 항목 둘이 각각 **132px** 로 왼쪽에 붙고 오른쪽에 **빈 자리 세 칸 분**이 그대로 남는다. 아래(`auto-fit`)는 같은 두 항목이 각각 **345px** 로 부풀어 줄 전체를 꽉 채운다.\
> **바꿔 볼 것** — `.g` 의 `width: 700px` → `320px` 하면 **둘이 똑같아진다**(`155px 155px` 두 칸) — 빈 트랙이 안 생기니 접을 것도 없기 때문이다 · 항목을 다섯으로 늘리면 700px 에서도 둘이 같아진다

*(Chrome 151 headless 실측 — `gridTemplateColumns` 계산값: `auto-fill` → `132px 132px 132px 132px 132px` · `auto-fit` → **`345px 345px 0px 0px 0px`**. 접힌 트랙이 사라지는 게 아니라 **`0px` 로 계산값에 그대로 남는다.**)*

```text
auto-fill (700px, 항목 2개)                auto-fit (700px, 항목 2개)
+-----+-----+-----+-----+-----+          +--------------+--------------+
| [1] | [2] |     |     |     |          |     [1]      |     [2]      |
+-----+-----+-----+-----+-----+          +--------------+--------------+
 132   132   132   132   132               345            345   (+0 0 0)
 빈 트랙이 자리를 차지한다                  빈 트랙이 0 으로 접히고 fr 이 다시 나뉜다
```

그림 해설 (한 단계씩):

- **둘 다 트랙 수는 똑같이 5개를 만든다.** 다르게 세는 게 아니다.
- `auto-fit` 은 그 다음에 **항목이 없는 트랙을 `0px` 로 접고**, 접힌 트랙의 `gap` 까지 회수해 `fr` 을 다시 나눈다.
- 그래서 **항목이 트랙을 다 채우면 둘은 완전히 같다.** 차이는 「항목이 모자랄 때」만 드러난다.
- ★ 화면으로는 「칸이 3개인가 5개인가」를 세다가 틀린다. **`gridTemplateColumns` 를 읽어야** `0px` 세 개가 보인다.

**칸 수는 컨테이너 폭이 정한다.** 같은 선언을 폭만 바꿔 잰 것:

| 컨테이너 폭 | `auto-fill` 계산값 | `auto-fit` 계산값 |
|---|---|---|
| 320px | `155px 155px` | `155px 155px` |
| 500px | `160px 160px 160px` | `245px 245px 0px` |
| 700px | `132px 132px 132px 132px 132px` | `345px 345px 0px 0px 0px` |

*(Chrome 151 headless 실측 — 선언은 세 폭 모두 `repeat(auto-fill|auto-fit, minmax(120px, 1fr))` · `gap: 10px` · 항목 2개. 320px 에서 둘이 같은 이유는 트랙이 둘뿐이고 항목도 둘이라 **빈 트랙이 없기** 때문이다.)*

- 칸 수 세는 법: **`n × 120 + (n-1) × 10 ≤ 컨테이너 폭`** 을 만족하는 가장 큰 `n`.\
  320px 이면 `n=2`(250 ≤ 320), `n=3` 은 380 > 320 이라 탈락 → 2칸. 실측이 그대로 2칸이었다.
- **컨테이너 폭이 확정되지 않으면 반복 횟수는 1이다.**\
  *(실측: 같은 선언에 `width: max-content` 를 주면 계산값이 `150px` 한 칸.)*

비용 — `auto-fill` 은 빈 트랙에도 `gap` 이 붙어 **오른쪽에 큰 여백이 남아 보인다.** 카드가 적을 때 허전한 것이 그 때문이고, `auto-fit` 은 대신 **카드 하나가 화면 전체로 부풀어** 우스워질 수 있다. 둘 다 정답이 아니라 **다른 실패 모양**이다.

### (7) 정의 안 한 트랙 — 암묵 트랙과 `grid-auto-rows`

**언제 쓰나** — 항목 수가 정해지지 않은 목록을 격자에 부을 때.

```text
grid-template-columns: 100px 100px      <- 명시 격자: 2열
grid-template-rows:    50px             <- 명시 격자: 1행
항목 4개를 넣으면?

     열1     열2
행1 [ 1 ]  [ 2 ]     <- 명시 행 (50px)
행2 [ 3 ]  [ 4 ]     <- 암묵 행. 크기는 grid-auto-rows 가 정한다 (없으면 auto)
```

| 선언 | `gridTemplateRows` 계산값 | 읽는 법 |
|---|---|---|
| `grid-template-rows: 50px` | `50px 20px` | 둘째 행은 암묵 · `auto` 로 20px |
| `+ grid-auto-rows: 80px` | `50px 80px` | 암묵 행에만 80px 이 걸렸다 |
| `+ grid-auto-rows: 80px 30px` | `50px 80px 30px` | 암묵 행이 **80·30 을 번갈아** 쓴다 |
| `grid-auto-rows: minmax(60px, auto)` (명시 행 없음) | `60px 60px` | 전부 암묵 · 최소 60px |

*(Chrome 151 headless 실측 — `grid-template-columns: 100px 100px` 인 컨테이너에 항목 4\~6개.)*

- ★ **`getComputedStyle` 은 암묵 트랙까지 같이 돌려준다.** 선언에는 `50px` 하나뿐인데 계산값에 `50px 20px` 이 오는 것이 그 증거다.\
  「내가 만든 트랙」과 「엔진이 만든 트랙」이 **한 줄에 섞여 온다**는 뜻이므로, 개수를 셀 때 이 점을 알고 세야 한다.
- `grid-auto-columns` 는 열 쪽의 짝이다. 기본 흐름(`row`)에서는 열이 안 늘어나므로 잘 안 쓰이지만,\
  **정의 안 한 열 자리에 항목을 명시 배치하면** 열도 자란다 — [**28번**](../28-grid-placement/)의 자리다.
- 암묵 트랙에는 **라인 이름이 없다.** 그래서 `-1` 같은 음수 라인 번호가 암묵 트랙을 못 가리킨다([**28번**](../28-grid-placement/)).

> **명시 격자(explicit grid)** — `grid-template-columns`/`-rows`/`-areas` 로 내가 직접 정의한 트랙들.\
> 예: `grid-template-columns: 100px 100px` 이면 명시 열은 둘이다.

> **암묵 격자(implicit grid)** — 명시 격자 밖에 항목이 놓여서 엔진이 자동으로 만든 트랙들.\
> 예: 2열 격자에 항목 5개를 넣으면 3행째는 암묵 행이다. 크기는 `grid-auto-rows` 가 정한다.

### (8) `gap` 은 트랙이 아니다 — 자유 공간에서 먼저 빠진다

**언제 쓰나** — `fr` 계산이 예상과 몇 px 씩 어긋날 때.

```text
grid-template-columns: 1fr 1fr;  gap: 20px;   (컨테이너 600px)

|<---------------------- 600px ---------------------->|
+--------------------+  20px  +--------------------+
|       290px        |<-gap-->|       290px        |
+--------------------+        +--------------------+
      ^ (600 - 20) / 2 = 290
```

*(Chrome 151 headless 실측: `1fr 1fr` + `gap: 20px` 인 600px 컨테이너의 계산값이 `290px 290px`.)*

- `gap` 은 **트랙이 아니다** — 계산값 `gridTemplateColumns` 에 안 나온다. 트랙 수를 셀 때 헷갈리지 말 것.
- 순서는 **`gap` 을 먼저 떼고 → 고정 트랙을 떼고 → 남은 것을 `fr` 이 나눈다**.
- ★ **`gap` 의 정본은 flex 쪽([목록의 26번 주제](../26-flex-wrap-gap-order/))에 있다.** 여기서는 **트랙 계산에 끼어드는 자리**까지만 쓴다.\
  Grid 의 `gap` 은 flex 보다 훨씬 먼저 쓸 수 있었고(Grid 와 함께 들어왔다), **접힌 `auto-fit` 트랙의 `gap` 은 회수된다**는 것이 Grid 고유의 자리다.

## 문법 — 형태와 어디서 헷갈리나

CSS 는 문법 표면이 단순하다. 외울 것은 형태가 아니라 **어느 값이 어디에 못 오는가**다.

### 최소 형태

```css
.g {
  display: grid;                                  /* 이 줄만으로 이미 1열 격자다 */
  grid-template-columns: 200px 1fr minmax(100px, 2fr);
  grid-template-rows: repeat(3, 60px);
  grid-auto-rows: 80px;                           /* 암묵 행의 크기 */
  gap: 12px;                                      /* = row-gap 12px; column-gap 12px */
}
```

- `display: grid` 만 주고 트랙을 안 정하면 **1열 격자**가 된다(모든 항목이 세로로 쌓인다).
- `grid-template-columns` 의 초기값은 `none` 이다 — 「열 트랙이 없다」는 뜻이지 「1열 트랙」이 아니다.\
  그 1열은 **암묵 열**이고, 그래서 계산값에는 `none` 이 아니라 px 이 온다.\
  *(실측 — 항목이 **없는** 400px 컨테이너: 계산값 `none` / 항목이 **하나라도 있으면**: 계산값 `400px`. (7)의 「계산값에 암묵 트랙이 섞여 온다」가 여기서도 그대로다.)*
- `display: inline-grid` 는 바깥만 인라인이고 안쪽 배치는 같다 — [**16번**](../16-display-inner-outer/).

### 금지 사례 — 버려지는 트랙 정의

```css
.a { grid-template-columns: repeat(auto-fill, 1fr); }                  /* 자동 반복 + fr */
.b { grid-template-columns: repeat(auto-fill, auto); }                 /* 자동 반복 + auto */
.c { grid-template-columns: repeat(auto-fill, minmax(min-content, 1fr)); } /* 최솟값이 내재적 */
.d { grid-template-columns: repeat(auto-fill, 150px) repeat(auto-fit, 100px); } /* 자동 반복 둘 */
.e { grid-template-columns: repeat(0, 100px); }                        /* 횟수가 0 */
```

- 전부 **에러도 경고도 없이 그 선언 하나만 버려진다.** 앞서 이긴 값이 그대로 남는다.
- 그래서 (1)의 **대조군 + 계산값 판독**이 유일한 확인 수단이다.
- 반대로 이것들은 **유효**하다 — `minmax(150px, auto)` · `minmax(0, 1fr)` · `repeat(2, 100px 50px)` · `fit-content(100px)`.

### 헷갈리는 짝

| 헷갈리는 것 | 실제 |
|---|---|
| `1fr` 과 `minmax(0, 1fr)` | 앞엣것은 **최솟값이 `auto`**, 뒤엣것은 0. 내용이 크면 결과가 다르다 |
| `auto` 트랙과 `min-content` 트랙 | `auto` 는 **늘어날 수 있고** `min-content` 는 안 늘어난다 |
| `auto-fill` 과 `auto-fit` | 트랙 수는 같다. **빈 트랙을 0 으로 접느냐**만 다르다 |
| `repeat(3, 1fr 2fr)` | 3칸이 아니라 **6칸**이다(목록을 반복한다) |
| `gap` 과 트랙 | `gap` 은 트랙이 아니다. 계산값 목록에 안 나온다 |

## 구현 세부사항 대 언어 보장

- **「`fr` 이 남은 공간을 나눈다」는 명세가 보장한다.** CSS Grid Level 1 의 트랙 크기 결정 알고리즘이 근거이고, 「자유 공간을 `fr` 의 합으로 나눈다」가 그 안에 있다.
- **「계산값이 px 로 풀려서 온다」는 CSSOM 의 규정**이다. `grid-template-columns` 의 resolved value 가 사용값으로 정의돼 있다.
- **「계산값에 암묵 트랙까지 섞여 온다」·「`auto-fit` 의 접힌 트랙이 `0px` 로 남는다」는 Chrome 151 에서 관찰한 직렬화 형태**다. 명세가 문자열 모양까지 정하지는 않으므로 **버전이 오르면 다시 찍어야 하는 칸**이다.
- **구체적인 px 값은 전부 폰트와 창 크기에 딸린 것**이다. `min-content` 가 12.89px 인 것은 「한글 한 글자」라는 성질이 재현되는 것이지 **숫자가 재현되는 것이 아니다.**
- Grid 자체는 Baseline **widely**(2020-04-17)라 「지금 그냥 써도 되는 것」에 든다.

## 어디서 틀리나

이 주제의 값어치는 여기 몰려 있다. 여섯 다 **에러 없이 조용히 어긋난다.**

### 1. `1fr` 을 「전체의 1/n」로 읽는다

```text
grid-template-columns: 200px 1fr 1fr   (500px)

기대: 166.7 / 166.7 / 166.7      실제: 200 / 150 / 150
```

고정 트랙·`gap` 을 먼저 떼고 남은 것을 나눈다. **`fr` 은 비율이 아니라 몫이다.**

### 2. `1fr` 을 줬는데 항목이 안 줄어든다

`1fr` = `minmax(auto, 1fr)` 이라 **내용의 최소 폭 아래로 안 내려간다.**\
처방은 `minmax(0, 1fr)` 또는 항목에 `overflow: hidden`. 25번의 `min-width: auto` 와 같은 모양이다.

### 3. `auto-fill` 과 `auto-fit` 을 눈으로 구분하려 한다

**항목이 트랙을 다 채우면 둘은 화면상 완전히 같다.** 320px 실측에서 둘 다 `155px 155px` 이었다.\
차이를 보려면 **항목을 트랙 수보다 적게** 두고 `gridTemplateColumns` 를 읽어야 한다.

### 4. `repeat(auto-fill, 1fr)` 로 「화면에 맞춰 나눠지겠지」 한다

**버려진다.** 자동 반복은 「몇 개 들어가나」를 먼저 세야 하는데 `fr` 로는 셀 수가 없다.\
의도한 것은 대개 `repeat(auto-fill, minmax(120px, 1fr))` 이다.

### 5. 칸 수를 스크린샷으로 센다

`auto-fit` 에서 접힌 트랙은 **폭이 0 이라 화면에 안 보이는데 계산값에는 있다.**\
`grid-column: 3` 같은 명시 배치가 「왜 여기 놓이지」가 되는 원인이 이것이다.

### 6. 암묵 트랙이 생긴 줄 모른다

`grid-template-rows` 를 하나만 줬는데 계산값이 `50px 20px` 이면 **둘째 행은 내가 만든 게 아니다.**\
`grid-auto-rows` 를 안 주면 그 행은 `auto` 라 내용 높이가 되고, 그래서 **행 높이가 들쭉날쭉해진다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 이유 |
|---|---|---|
| 사이드바 고정 + 본문 가변 | `200px 1fr` | `fr` 이 남은 것을 먹는다 |
| 카드 격자, 화면 폭에 맞춰 칸 수 변경 | `repeat(auto-fill, minmax(220px, 1fr))` | 미디어 쿼리가 필요 없다 |
| 위와 같은데 **카드가 적을 때 꽉 채우고 싶다** | `auto-fit` | 빈 트랙을 접는다 |
| 위와 같은데 **카드가 적어도 칸 폭을 유지**하고 싶다 | `auto-fill` | 빈 트랙이 자리를 지킨다 |
| 내용에 딱 맞는 라벨 열 | `max-content` 또는 `auto` | 늘어나도 되면 `auto` |
| 항목이 줄어들어야 하는 유동 열 | `minmax(0, 1fr)` | 자동 최소 크기를 끈다 |
| 한 축만 신경 쓰면 되는 배치 | Grid 말고 **Flexbox** | [**24번**](../24-flexbox-axes/) |

판단 규칙 두 줄.

- **고정과 유동이 섞이면 `fr`, 내용에 맞추면 내재적 키워드, 둘 다면 `minmax()`.**
- **반응형 격자의 기본형은 `repeat(auto-fill, minmax(<최소 카드 폭>, 1fr))` 하나**이고, 나머지는 그 변주다.

## 핵심 문장

- `fr` 은 **남은 공간**(자유 공간)의 몫이다. 고정 트랙과 `gap` 을 먼저 뗀 뒤에 나눈다.
- `1fr` 은 `minmax(auto, 1fr)` 이다 — **숨은 최솟값이 항목을 안 줄어들게 만든다.** 처방은 `minmax(0, 1fr)`.
- `auto-fill` 과 `auto-fit` 은 **트랙 수가 같다.** `auto-fit` 만 빈 트랙을 `0px` 로 접는다.
- 자동 반복의 트랙 크기는 **고정이어야 한다** — `fr`·`auto`·`min-content` 를 넣으면 선언이 조용히 버려진다.
- `getComputedStyle(el).gridTemplateColumns` 는 **푼 결과**를 돌려준다. 칸 수도 칸 폭도 여기서 읽는다.
- 그 계산값에는 **암묵 트랙과 접힌 `0px` 트랙까지 섞여** 있다. 눈으로 센 수와 다를 수 있다.

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 27번) · 「버전·지원 기준」의 Baseline 표
- [목록의 **28번 주제**](../28-grid-placement/)(Grid 배치) — **이 트랙 위에 무엇을 어떻게 놓는가는 거기.** 여기는 트랙을 만드는 데까지
- [목록의 **29번 주제**](../29-grid-template-areas/)(Grid 영역) — 라인 이름·영역 이름은 거기
- [목록의 **30번 주제**](../30-subgrid/)(`subgrid`) — 여기서 만든 트랙을 **자식이 잇는 것**은 거기
- [목록의 **24번 주제**](../24-flexbox-axes/)(Flexbox 축과 정렬) — ★ **`justify-*`/`align-*` 의 정본은 거기.** 여기는 트랙 크기만 다루고 정렬은 안 다룬다
- [목록의 **25번 주제**](../25-flex-shorthand-and-sizing/)(`flex` 단축) — `min-width: auto` 함정의 정본. (3)의 `minmax(0, 1fr)` 과 **같은 모양의 함정**이다
- [목록의 **26번 주제**](../26-flex-wrap-gap-order/)(flex 줄바꿈·`gap`·`order`) — ★ **`gap` 의 정본은 거기.** 여기는 `gap` 이 `fr` 계산에 끼어드는 자리까지만
- [목록의 **31번 주제**](../31-intrinsic-sizing-and-aspect-ratio/)(내재적 크기) — ★ **`min-content`/`max-content`/`fit-content` 자체의 정의는 거기.** 여기는 트랙 값으로 쓰일 때까지만
- [목록의 **16번 주제**](../16-display-inner-outer/)(`display` 의 내부/외부 값) — `grid` 와 `inline-grid` 가 갈리는 자리
- [목록의 **15번 주제**](../15-box-model-and-box-sizing/)(박스 모델) — 트랙 폭이 가리키는 것이 내용 영역인가 테두리까지인가
- [목록의 **07번 주제**](../07-syntax-and-error-recovery/)(구문과 오류 복구) — 무효한 선언 하나가 버려지는 규칙
- [`history/web/03-HTML-CSS-진화.md`](../../../../../../history/web/03-HTML-CSS-진화.md) — **2차원 레이아웃이 언제 왜 들어왔나는 거기.** 여기는 오늘의 규칙만
- [`reference/render-rules.md`](../../../../../../reference/render-rules.md) — 이 문서의 `demo` 블록 규칙

## 용어 풀이

- **트랙(track)** — 격자의 행 하나 또는 열 하나. 라인 둘 사이의 띠다.
- **격자 라인(grid line)** — 트랙 사이의 경계. 번호가 붙어 있고 이름도 붙일 수 있다(29번).
- **`fr`(fraction)** — 남은 공간의 몫을 뜻하는 grid 전용 단위. 비율이 아니다.
- **자유 공간(free space)** — 컨테이너 폭에서 고정·내재적 트랙과 `gap` 을 뺀 나머지. `fr` 이 이것을 나눈다.
- **`minmax(a, b)`** — 최소 `a`, 최대 `b` 인 트랙. `b` 가 `a` 보다 작으면 `a` 가 이긴다.
- **`repeat(n, …)`** — 트랙 목록을 `n` 번 반복한다. `n` 자리에 `auto-fill`/`auto-fit` 이 올 수 있다.
- **`auto-fill`** — 들어가는 만큼 트랙을 만든다. 항목이 없어도 트랙이 남는다.
- **`auto-fit`** — 같은 수의 트랙을 만든 뒤 **빈 트랙을 `0px` 로 접는다.**
- **명시 격자(explicit grid)** — 내가 `grid-template-*` 로 정의한 트랙들.
- **암묵 격자(implicit grid)** — 항목이 명시 격자 밖에 놓여 엔진이 자동으로 만든 트랙들. 크기는 `grid-auto-rows`/`-columns` 가 정한다.
- **자동 최소 크기(automatic minimum size)** — `auto` 최솟값이 실제로 풀리는 값. 대개 `min-content` 이고, `overflow` 가 `visible` 이 아니면 0 이 된다.
- **`min-content`** — 줄바꿈을 최대한 해서 얻는 가장 좁은 폭. 정본은 31번.
- **`max-content`** — 줄바꿈 없이 필요한 폭. 정본은 31번.
- **`fit-content(x)`** — 내용만큼이되 `x` 에서 멈추는 크기.
- **계산값(resolved value)** — `getComputedStyle` 이 돌려주는 값. `grid-template-columns` 에서는 **px 로 푼 사용값**이 온다.

---

## 더 들어가면

- **`fr` 은 `minmax()` 의 최대 자리에만 올 수 있다.** `minmax(1fr, 2fr)` 은 무효이고 `minmax(100px, 1fr)` 은 유효하다.\
  최소 자리는 「폭을 몰라도 정해지는 값」이어야 하기 때문이다 — (1)의 자동 반복 제약과 같은 뿌리다.
- **`grid-template-columns` 와 `grid-template-rows` 는 성질이 다르다.** 열은 컨테이너 폭이 대개 확정돼 있어 `fr` 이 잘 풀리지만,\
  행은 높이가 `auto` 인 경우가 많아 **`1fr` 행이 내용 높이로 접히는** 일이 흔하다. 행에 `fr` 을 쓰려면 컨테이너 높이를 먼저 정해야 한다.
- **`grid` 단축과 `grid-template` 단축**이 따로 있다. `grid-template` 은 행·열·영역 셋을 한 줄에 쓰고,\
  `grid` 는 거기에 암묵 트랙 설정(`grid-auto-*`)까지 **초기화**한다 — 그래서 `grid` 단축을 쓰면 앞에 쓴 `grid-auto-rows` 가 지워진다.
- **`justify-content`/`align-content` 는 Grid 에서 「트랙 묶음 전체」를 움직인다.** 트랙 합이 컨테이너보다 작을 때만 의미가 있고,\
  `fr` 트랙이 하나라도 있으면 자유 공간이 0 이라 **아무 일도 하지 않는다.** 정렬 어휘의 정본은 [**24번**](../24-flexbox-axes/)이다.
- 행 방향의 「들어가는 만큼」인 **Masonry**(`grid-template-rows: masonry`)는 Baseline **limited** 이고 문법이 아직 논쟁 중이라 이 목록에서 뺐다(목록 README 의 「뺀 것과 이유」).

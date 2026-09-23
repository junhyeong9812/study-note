# css/syntax/29 — Grid 영역: `grid-template-areas`·이름 붙은 라인 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [CSS Grid Layout Level 1](https://drafts.csswg.org/css-grid-1/) (`grid-template-areas` 문법과 유효성·이름 붙은 라인·암묵 이름 규칙·`grid-area` 단축). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 `demo` 블록 **4개 전부**와 본문의 판정을 **Google Chrome 151.0.7922.173** headless 에 실제로 띄워 확인했다.\
> **무효한 영역 정의가 버려지는 것은 「진단 3창」으로** 쟀다 — `cssRules[i].style.gridTemplateAreas`(담겼나) → 항목 매치(잡혔나) → `getComputedStyle(el).gridTemplateAreas`(이겼나). 항목 좌표는 `getBoundingClientRect()` 로 따로 쟀다.\
> **엔진은 Chrome 하나다** — Firefox 155.0.1 은 이 환경에서 headless 스크린샷이 산출되지 않고 WebKit 은 이 머신에 없다. 「두 엔진에서 확인했다」고 적지 않았다.
> **버전** — Grid 는 Baseline **widely**(newly 2017-10-17 → widely 2020-04-17). `grid-template-areas` 는 Grid 와 같이 들어왔다.
> **여기서 다루지 않는 것** — **트랙을 만드는 것**은 [**27번**](../27-grid-track-sizing/), **번호로 놓는 것**은 [**28번**](../28-grid-placement/)이 정본이다(이 문서는 둘의 실측을 그대로 이어 쓴다). 정렬(`justify-*`/`align-*`)의 정본은 [**24번**](../24-flexbox-axes/)이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 판정은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**`grid-template-areas` = 주차장 바닥에 칸 번호 대신 「장애인」·「경차」라고 글자를 써 놓는 것.**

[27번](../27-grid-track-sizing/)에서 칸막이를 세웠고 [28번](../28-grid-placement/)에서 번호로 자리를 잡았다. 여기서는 **번호 대신 이름**을 쓴다.

| 비유 | 실체 |
|---|---|
| 바닥에 쓴 글자 | **영역 이름(grid area name)** |
| 글자를 칸마다 적은 도면 | `grid-template-areas` 의 문자열들 |
| 아무 글자도 안 쓴 칸 | **`.`**(마침표) — 비워 두는 칸 |
| 「경차 자리에 대세요」 | `grid-area: compact` |
| 선 자체에 이름표를 붙이는 것 | **이름 붙은 라인**(`[main-start]`) |
| 이름표 둘이 짝이면 자동으로 구역이 생긴다 | `-start`/`-end` 접미사 규칙 |

- **도면을 CSS 안에 ASCII 아트로 그린다.** 레이아웃이 코드에 **그림으로** 보이는 것이 이 기능의 값이다.
- **도면이 직사각형이 아니면 통째로 버려진다.** 에러는 안 난다 — 그래서 이 주제의 값은 **버려진 것을 잡아내는 법**에 있다.
- 영역 이름과 라인 이름은 **한 좌표계**를 공유한다. 서로 자동으로 만들어 주고, 같은 이름이 둘 있으면 **먼저 나온 라인이 이긴다.**

```text
grid-template-areas: "hd hd"          1열       2열
                     "sb mn"        +--------+--------+
                     ".  ft";       |   hd   |   hd   |   1행
                                    +--------+--------+
  같은 글자가 붙어 있으면 한 영역     |   sb   |   mn   |   2행
  .  은 비워 두는 칸                 +--------+--------+
                                    |  (빈칸) |   ft   |   3행
                                    +--------+--------+
```

> **영역(grid area)** — 라인 넷으로 둘러싸인 직사각형 구역. 칸 하나일 수도, 여러 칸일 수도 있다.\
> 예: 위 도면의 `hd` 는 1행 1\~2열을 덮는 영역이다.

> **이름 붙은 라인(named grid line)** — 트랙 정의에서 대괄호로 이름을 준 격자 라인.\
> 예: `grid-template-columns: [main-start] 100px [main-end]` 는 라인 1·2에 이름을 붙인다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 도면(`grid-template-areas`)이 **무효**가 되는 조건은 무엇이고, 무효일 때 **무엇을 보면** 알 수 있나.
2. 영역 이름과 라인 이름은 **서로 무엇을 만들어 주나** — `-start`/`-end` 규칙.
3. 같은 이름이 둘 있을 때 **무엇이 이기나.**

## 동작 방식

### (1) 도면 문법 — 문자열 하나가 한 행이다

**언제 쓰나** — 레이아웃 뼈대(헤더·사이드바·본문·푸터)를 짤 때. 이 기능의 본래 자리다.

```text
grid-template-areas: "hd hd"      <- 문자열 하나 = 격자의 한 행
                     "sb mn"
                     ".  ft";
                      │   │
                      │   └── 두 번째 열의 칸
                      └── 첫 번째 열의 칸

  규칙 넷
  ① 문자열 개수 = 행 개수
  ② 한 문자열 안의 토큰 개수 = 열 개수 — 모든 행이 같아야 한다
  ③ 같은 이름이 붙어 있으면 한 영역이 된다 (반드시 직사각형)
  ④ . (또는 ...) 은 이름이 없는 칸 = 비워 둔다
```

```html demo
<div class="g"><i class="hd">hd</i><i class="sb">sb</i><i class="mn">mn</i><i class="ft">ft</i></div>
<style>
  .g { display: grid; width: 360px; gap: 4px; border: 2px solid #94a3b8;
       grid-template-columns: 100px 1fr;
       grid-template-rows: 32px 64px 32px;
       grid-template-areas: "hd hd"
                            "sb mn"
                            ".  ft"; }   /* . 은 비워 두는 칸 */
  .hd { grid-area: hd; } .sb { grid-area: sb; }
  .mn { grid-area: mn; } .ft { grid-area: ft; }
  .g i { background: #bfdbfe; font: 13px system-ui; font-style: normal;
         outline: 1px solid #2563eb; }
</style>
```

> **보이는 것** — 세 줄짜리 격자다. **맨 윗줄은 `hd` 하나가 좌우 전체**를 덮고, **가운데 줄은 좁은 `sb` 와 넓은 `mn`** 이 나란히 놓이며, **맨 아랫줄은 왼쪽이 비고 `ft` 만 오른쪽**에 놓인다. 왼쪽 아래에 **파란 상자가 없는 빈자리**가 그대로 보이는 것이 `.` 의 효과다.\
> **바꿔 볼 것** — `".  ft"` → `"ft ft"` 하면 아랫줄이 **좌우 전체**로 늘어난다 · `grid-template-columns` 의 `100px 1fr` → `1fr 100px` 하면 **좁은 칸이 오른쪽으로** 옮겨가고 도면은 한 글자도 안 고쳐도 된다 · `.hd` 의 `grid-area: hd` 를 지우면 그 항목이 자동 배치로 **격자의 첫 칸**(1행 1열 · x=2 y=2 w=100)에 들어간다 — 「`.` 자리」가 아니라 **커서가 처음 만나는 빈 칸**이다([28번](../28-grid-placement/))

*(Chrome 151 headless 실측 — 트랙 계산값 `cols: 100px 256px` · `rows: 32px 64px 32px`, 영역 계산값 `"hd hd" "sb mn" ". ft"`. 항목 좌표: `hd` x=2 y=2 w=360 h=32 · `sb` x=2 y=38 w=100 h=64 · `mn` x=106 y=38 w=256 h=64 · `ft` **x=106** y=106 w=256 h=32 — `ft` 의 x 가 106 인 것이 왼쪽 칸이 비었다는 증거다.)*

- **정렬이 보기 좋게 되라고 공백을 여러 개 넣어도 된다.** 토큰 사이 공백 수는 상관없다.
- ★ **도면은 트랙 크기를 안 정한다.** 크기는 여전히 `grid-template-columns`/`-rows` 의 몫이다([**27번**](../27-grid-track-sizing/)).\
  그래서 **도면을 그대로 두고 트랙 크기만 바꿔** 반응형을 만드는 것이 이 기능의 대표 용법이다.

### (2) 무효한 도면 — 조용히 통째로 버려진다

**언제 쓰나** — 「도면을 썼는데 아무 데도 안 붙는다」가 나왔을 때.

무효가 되는 조건은 셋이다.

```text
① 영역이 직사각형이 아니다            ② 행마다 열 개수가 다르다      ③ 같은 이름이 떨어져 있다
   "a a b"                              "a a"                        "a b a"
   "a c c"                              "b b b"                       └─┬─┘
    └─ a 가 ㄴ 자 모양                     2개 ≠ 3개                     떨어져 있다
```

```html demo
<div class="g ok"><i class="a">a</i><i class="b">b</i><i class="c">c</i></div>
<div class="g bad"><i class="a">a</i><i class="b">b</i><i class="c">c</i></div>
<style>
  .g { display: grid; width: 300px; margin-bottom: 8px; border: 2px solid #94a3b8;
       grid-template-columns: repeat(3, 100px); grid-template-rows: 30px 30px; }
  .ok  { grid-template-areas: "a a b" "c c b"; }   /* a·b·c 전부 직사각형 */
  .bad { grid-template-areas: "a a b" "a c c"; }   /* a 가 L 자 -> 통째로 버려진다 */
  .a { grid-area: a; } .b { grid-area: b; } .c { grid-area: c; }
  .g i { background: #bfdbfe; font: 13px system-ui; font-style: normal;
         outline: 1px solid #2563eb; }
</style>
```

> **보이는 것** — 위 격자는 도면대로 **`a` 가 윗줄 왼쪽 두 칸, `b` 가 오른쪽 세로 두 칸, `c` 가 아랫줄 왼쪽 두 칸**으로 깔끔하게 채워진다. 아래 격자는 **테두리만 남고 안이 텅 빈다.** 세 항목이 격자 **바깥 오른쪽 아래**로 밀려나 한 자리에 겹쳐 쌓이고, 맨 위에 칠해진 `c` 글자 하나만 조그맣게 보인다.\
> **바꿔 볼 것** — `.bad` 의 `"a a b" "a c c"` → `"a a b" "a a c"` 로 고치면(`a` 가 직사각형이 된다) 위 격자처럼 정상으로 그려진다 · `"a a b" "a c c"` → `"a a b" "c c c"` 로 고쳐도 된다

*(Chrome 151 headless 실측 — **진단 3창**: ① 규칙의 `style.gridTemplateAreas` 가 `.ok` 는 `"a a b" "c c b"` 인데 `.bad` 는 **빈 문자열** — 파싱 단계에서 버려졌다. ② 선택자는 양쪽 다 잡았다. ③ 계산값이 `.ok` 는 도면 그대로, `.bad` 는 **`none`**. 좌표: `.ok` 는 `a`(x=2 y=2 w=200) `b`(x=202 y=2 h=60) `c`(x=2 y=32 w=200) · `.bad` 는 **셋 다 x=302 y=62 w=8.05 h=19** 로 한 자리에 겹쳤고, 트랙 계산값이 `100px 100px 100px 0px 8.04688px` 로 **암묵 열 둘이 자랐다.**)*

그림 해설 (한 단계씩):

```text
.bad 에서 일어난 일

① grid-template-areas 가 무효 -> 선언 하나가 통째로 버려진다 (계산값 none)
        ↓
② .a { grid-area: a } 의 a 는 이제 "영역 이름"이 아니다 -> "라인 이름 a" 로 읽힌다
        ↓
③ a 라는 이름의 라인도 없다 -> 명세 규칙: 암묵 라인이 전부 그 이름을 가진 셈 친다
        ↓
④ 세 항목이 전부 명시 격자 바깥(암묵 격자)으로 밀려나 같은 자리에 겹친다
```

- ★ 증상이 「안 그려진다」가 아니라 **「엉뚱한 데 겹쳐 있다」** 라는 것이 중요하다. 화면 밖으로 사라지지 않는다.
- **화면만 보면 ①인지 ②인지 알 수 없다.** 선택자 오타여도, 이름 오타여도 증상이 비슷하다 —\
  그래서 [27번](../27-grid-track-sizing/)에서 쓴 **진단 3창**을 여기서도 그대로 쓴다.
- 오류 복구의 정본은 [목록의 **07번 주제**](../07-syntax-and-error-recovery/)다.

비용 — 없다. 다만 **긴 도면일수록 열 개수를 세다 틀린다.** 행이 다섯을 넘으면 계산값을 한 번 읽어 보는 편이 빠르다.

### (3) `.` 은 빈 칸 — 그리고 `...` 도 같은 뜻이다

**언제 쓰나** — 도면에서 칸 하나를 비워 둘 때, 또는 도면의 세로줄을 맞추고 싶을 때.

```text
"hd hd ."        마침표 하나
"a  ... b"       마침표 여럿 — 같은 뜻이다 (칸 하나를 비운다)

계산값은 언제나 마침표 하나로 접힌다:
  선언  "a . b" "a ... b"   ->   계산값  "a . b" "a . b"
```

*(Chrome 151 headless 실측 — `grid-template-areas: "a . b" "a ... b"` 의 계산값이 `"a . b" "a . b"` 였다. 항목 `a` 와 `b` 는 각각 x=2·x=202 에서 **두 행을 덮었다**(h=80) — 즉 `...` 이 칸 하나로 읽혀 두 행의 열 개수가 맞았다.)*

- **`.` 이 연속으로 여럿이면 각각 다른 빈 칸**이다(`". . b"` 는 빈 칸 둘). **`...` 은 하나**다.\
  헷갈리면 `.` 하나씩만 쓰는 편이 안전하다.
- 빈 칸에는 **자동 배치 항목이 들어갈 수 있다.** 「영원히 비어 있는 칸」이 아니다.\
  *(실측 — 도면 `"a . b" "a . b"` 에 `grid-area` 를 안 준 항목을 하나 더 넣었더니 **가운데 빈 칸**(x=102 y=2 w=100 h=40)에 들어갔다.)*

```text
.  은 「막아 둔 칸」이 아니다

  도면        자동 배치 항목이 하나 있으면
  a . b   ->  a [자동] b      <- . 자리에 들어간다
  a . b       a        b
```

### (4) 이름 붙은 라인 — 선에 이름표를 단다

**언제 쓰나** — 도면을 그릴 만큼 규칙적이지 않지만 번호는 쓰기 싫을 때.

```text
grid-template-columns: [full-start] 50px [main-start] 100px 100px [main-end] 50px [full-end];
                        라인1        트랙  라인2        트랙  트랙  라인4        트랙  라인5

  grid-column: main-start / main-end     이름으로 자리를 잡는다
  grid-column: main                      -start/-end 짝이 있으면 이렇게 줄일 수 있다
```

```text
이름과 번호는 같은 라인을 가리킨다 — 다른 좌표계가 아니다

  [full-start]  50px  [main-start] 100px  100px  [main-end] 50px  [full-end]
       │                   │                          │              │
  번호 1                   2              3           4              5
  음수 -5                 -4             -3          -2             -1

  grid-column: main-start / main-end   ==   grid-column: 2 / 4
```

- 라인 하나에 **이름을 여럿** 붙일 수 있다 — `[main-start sidebar-end]`.
- ★ **계산값에 라인 이름이 그대로 실려 온다.**\
  *(실측 — 계산값 `[full-start] 50px [main-start] 100px 100px [main-end] 50px`. [27번](../27-grid-track-sizing/)에서 본 「계산값은 px 로 푼 결과」에 **이름까지 얹혀 온다.**)*
- 번호 대신 이름을 쓰면 **트랙을 하나 끼워 넣어도 나머지가 안 밀린다.** 이것이 번호보다 나은 점이다.

### (5) `-start`/`-end` 접미사 — 이름 둘이 자동으로 영역이 된다

**언제 쓰나** — 도면 없이 영역을 만들고 싶을 때. **이 주제에서 가장 안 알려진 규칙이다.**

```html demo
<div class="g"><i class="m">main</i></div>
<style>
  .g { display: grid; width: 400px; border: 2px solid #94a3b8;
       grid-template-columns: 50px [main-start] 100px 100px [main-end] 50px;
       grid-template-rows:    30px [main-start] 40px [main-end] 30px; }
  .m { grid-area: main; }   /* -start/-end 짝이 main 이라는 영역을 만든다 */
  .g i { background: #bfdbfe; font: 13px system-ui; font-style: normal;
         outline: 1px solid #2563eb; }
</style>
```

> **보이는 것** — `grid-template-areas` 를 **한 줄도 안 썼는데** 파란 상자 하나가 격자 **한가운데**에 정확히 놓인다. 위·왼쪽에 각각 얇은 띠(30px·50px)가, 아래·오른쪽에도 같은 띠가 남아 상자가 가운데에 떠 있는 것처럼 보인다.\
> **바꿔 볼 것** — `.m` 의 `grid-area: main` → `grid-column: main` 으로 바꾸면 **가로 자리는 그대로이고 세로만 자동 배치**로 간다 · 행 쪽의 `[main-start]`·`[main-end]` 를 지우면 상자가 **세로로 엉뚱한 줄**(암묵 행)로 내려간다

*(Chrome 151 headless 실측 — 영역 계산값은 **`none`**(도면을 안 썼다). 트랙 계산값에 이름이 실려 온다: `cols: 50px [main-start] 100px 100px [main-end] 50px` · `rows: 30px [main-start] 40px [main-end] 30px`. 항목 좌표 x=52 y=32 w=200 h=40 — 정확히 `main` 영역이다. 항목의 `gridColumnStart`/`End` 계산값은 둘 다 `main` 이었다.)*\
*(「바꿔 볼 것」도 같은 방법으로 쟀다 — `grid-column: main` 으로 바꾼 판: x=52 y=2 w=200 h=30(가로는 그대로, 세로는 자동 배치로 1행). 행 쪽 이름을 지운 판: x=52 **y=102** 로 내려가고 행 계산값이 `30px 40px 30px 0px 19px` 가 됐다 — **암묵 행이 둘 자랐다.**)*

```text
양방향 규칙 — 둘은 서로를 만들어 준다

  grid-template-areas 에 영역 hd 를 쓰면
        ↓  자동으로
  라인 이름 hd-start · hd-end 가 생긴다     -> grid-column: hd-start / hd-end 가 된다

  [hd-start] … [hd-end] 라인 이름을 쓰면
        ↓  자동으로
  영역 hd 가 생긴 셈이 된다                 -> grid-area: hd 가 된다
```

*(Chrome 151 headless 실측 — 도면 `"hd hd x" "y y y"` 만 쓴 격자에서 `grid-column: hd-start / hd-end` 인 항목이 x=2 w=200 으로 `hd` 영역과 정확히 겹쳤다. 반대로 위 demo 가 라인 이름만으로 `grid-area: main` 을 성립시켰다.)*

- **한쪽만 있으면 성립하지 않는다.** `[main-start]` 만 있고 `[main-end]` 가 없으면 영역이 안 생긴다.\
  *(실측 — `cols: 50px [main-start] 100px 100px 50px` 에 `grid-column: main` 을 주면 항목이 x=52 **w=250** 으로 **오른쪽 끝까지 삼킨다.** 트랙 계산값에 `0px` 짜리 암묵 열이 하나 붙었다 — `main-end` 를 못 찾아 암묵 라인까지 밀고 간 것이다.)*

```text
main-end 가 없을 때

  cols: 50px [main-start] 100px 100px 50px            (+ 암묵 0px)
  라인:  1     2           3     4     5     6
              └──────── grid-column: main ───────────┘
                        start 는 찾았고 end 를 못 찾아 암묵 라인까지 간다
```

- 축마다 따로다 — 열 쪽만 `-start`/`-end` 를 주면 **열 자리만** 정해지고 행은 자동 배치가 정한다.

### (6) 이름이 겹치면 — 먼저 나온 라인이 이긴다

**언제 쓰나** — 도면과 라인 이름을 **같이** 쓸 때. 던져서 확인해야 하는 자리다.

```html demo
<div class="g"><i class="h">hd</i></div>
<style>
  .g { display: grid; width: 300px; border: 2px solid #94a3b8;
       grid-template-columns: [hd-start] 100px [hd-end] 100px 100px;
       grid-template-rows: 30px 30px;
       grid-template-areas: "x  hd hd"
                            "x  y  y"; }   /* 영역 hd 는 2~3열인데… */
  .h { grid-area: hd; }
  .g i { background: #bfdbfe; font: 13px system-ui; font-style: normal;
         outline: 1px solid #2563eb; }
</style>
```

> **보이는 것** — 도면은 `hd` 를 **윗줄 오른쪽 두 칸**으로 그려 놓았는데, 파란 상자는 **윗줄 왼쪽 첫 칸**에 놓인다. 도면이 아니라 `[hd-start]`·`[hd-end]` 라인 이름이 이긴 것이다. 도면 자체는 버려지지 않았다.\
> **바꿔 볼 것** — `grid-template-columns` 의 `[hd-start] 100px [hd-end]` 를 지우면 상자가 **도면대로 오른쪽 두 칸**으로 옮겨간다 · 라인 이름을 `100px [hd-start] 100px 100px [hd-end]` 로 옮기면 도면과 같은 자리가 된다

*(Chrome 151 headless 실측 — 영역 계산값은 `"x hd hd" "x y y"` 로 **살아 있고**(버려지지 않았다) 트랙 계산값도 `[hd-start] 100px [hd-end] 100px 100px` 로 살아 있다. 그런데 항목 좌표는 x=2 y=2 w=100 — **1열**이다.)*

**「어느 쪽이 이기나」가 아니라 「어느 라인이 먼저 나오나」가 규칙이다.**

```text
경우 A (위 demo)                          경우 B (라인 이름을 뒤로 옮김)
cols: [hd-start] 100 [hd-end] 100 100     cols: 100 [hd-start] 100 [hd-end] 100
areas: "x hd hd"                          areas: "hd hd x"
  라인 이름 hd-start = 라인 1               도면이 만든 hd-start = 라인 1
  도면이 만든 hd-start = 라인 2             라인 이름 hd-start   = 라인 2
        ↓                                        ↓
  먼저 나온 라인 1 이 이긴다 -> 1열           먼저 나온 라인 1 이 이긴다 -> 1~3열
```

*(Chrome 151 headless 실측 — 경우 B(`cols: 100px [hd-start] 100px [hd-end] 100px` + 도면 `"hd hd x"`)에서 항목이 **x=2 w=200**, 즉 **도면이 만든 라인 1**을 썼다. 경우 A 는 위 demo 대로 라인 이름이 이겼다. **둘 다 「먼저 나온 라인」이 이겼다** — 「선언 종류의 우열」이 아니다.)*

- 그래서 **같은 이름을 둘 다 쓰지 않는 것**이 유일한 처방이다. 규칙을 외우는 것보다 안 겹치게 짓는 편이 싸다.
- 명세의 표현으로는 「그 이름을 가진 **첫 번째** 라인부터」이고, 도면이 만든 암묵 이름도 그 목록에 함께 줄을 선다.

## 문법 — 형태와 어디서 헷갈리나

### 최소 형태

```css
.container {
  display: grid;
  grid-template-columns: 100px 1fr;          /* 크기는 여전히 여기 (27번) */
  grid-template-rows: auto 1fr auto;
  grid-template-areas: "hd hd"
                       "sb mn"
                       "ft ft";
}
.header  { grid-area: hd; }                  /* 영역 이름 하나 */
.sidebar { grid-column: main-start / main-end; }  /* 라인 이름 둘 */
.main    { grid-column: main; }              /* -start/-end 짝의 줄임 */
```

★ **`grid-area` 는 값 개수에 따라 뜻이 달라진다.**

```text
grid-area: hd                   영역 이름 하나            (또는 라인 이름 하나로 읽힌다)
grid-area: 2 / 1                row-start / column-start  (끝은 자동)
grid-area: 2 / 1 / 3 / 3        row-start / column-start / row-end / column-end
grid-area: 2 / hd-start / 3 / hd-end     번호와 이름을 섞어도 된다
```

*(Chrome 151 headless 실측 — 마지막 형태를 도면 `"hd hd x" "y y y"` 격자에 쓴 항목이 **2행 1\~2열**(x=2 y=32 w=200 h=30)에 놓였다. 번호와 도면이 만든 이름이 한 선언 안에서 같이 동작한다.)*

- 네 값 순서(`row-start / column-start / row-end / column-end`)의 정본 서술은 [**28번**](../28-grid-placement/)에 있다.

### 금지 사례 — 버려지는 도면

```css
.a { grid-template-areas: "a a b" "a c c"; }   /* a 가 L 자 */
.b { grid-template-areas: "a a" "b b b"; }     /* 행마다 열 개수가 다르다 */
.c { grid-template-areas: "a b a"; }           /* 같은 이름이 떨어져 있다 */
.d { grid-template-areas: "a-start b"; }       /* 이름에 -start/-end 를 직접 쓰면 안 된다 */
```

*(Chrome 151 headless 실측 — 앞의 셋은 `cssRules[i].style.gridTemplateAreas` 가 **빈 문자열**이고 계산값이 `none` 이었다. 넷째는 실행하지 않았다 — 명세가 금지하는 형태이고 이 문서에서 쓸 일이 없어 **안 돌려 봤다**고 적는다.)*

- 넷 다 **선언 하나가 통째로** 버려진다. 「잘못된 줄만」 버려지는 것이 아니다.
- 버려지면 `grid-area: <이름>` 이 **라인 이름 찾기로 떨어지면서** 항목이 암묵 격자로 밀려난다 — (2)의 ②\~④.

### 헷갈리는 짝

| 헷갈리는 것 | 실제 |
|---|---|
| 도면이 트랙 크기를 정한다 | **안 정한다.** 크기는 `grid-template-columns`/`-rows`(27번) |
| `.` 이 「이 칸을 못 쓰게 한다」 | **아니다.** 자동 배치 항목이 들어갈 수 있다 |
| `...` 이 빈 칸 셋 | **하나**다. `. . .` 이 셋이다 |
| `grid-area: hd` 가 항상 영역 | 영역이 없으면 **라인 이름**으로 읽힌다(그래서 조용히 어긋난다) |
| 도면이 라인 이름을 이긴다 | **아니다.** **먼저 나온 라인**이 이긴다 |
| `[main-start]` 만 있으면 영역 `main` | **아니다.** `-end` 짝이 있어야 한다 |

## 구현 세부사항 대 언어 보장

- **도면의 유효성 규칙**(직사각형·열 개수 일치·같은 이름 인접)은 **명세가 정한다.** CSS Grid Level 1 의 `grid-template-areas` 문법이 근거다.
- **`-start`/`-end` 가 영역을 만들고 영역이 `-start`/`-end` 를 만드는 양방향 규칙**도 명세다.
- **「그 이름을 가진 첫 번째 라인」 규칙**도 명세다. 위 (6)의 실측 둘은 그 규칙을 **확인한 것**이지 우연히 그렇게 된 것이 아니다.
- **계산값의 직렬화 형태**는 구현 관찰이다 — `...` 이 `.` 하나로 접혀 오는 것, 무효한 도면이 `cssRules` 에서 **빈 문자열**로 보이는 것, 라인 이름이 `[이름]` 으로 실려 오는 것은 Chrome 151 에서 본 것이다. **버전이 오르면 다시 찍는 칸**이다.
- **무효할 때 항목이 정확히 어느 암묵 칸에 떨어지는가**(실측 x=302 y=62)는 「암묵 격자로 밀려난다」는 성질이 재현되는 것이고 **좌표 자체는 이 판의 값**이다.
- Grid 와 `grid-template-areas` 는 Baseline **widely**(2020-04-17)다.

## 어디서 틀리나

이 주제의 값어치는 여기 몰려 있다. 다섯 다 **에러 없이 조용히 어긋난다.**

### 1. 도면이 무효인 줄 모른다

`a` 가 ㄴ 자면 **선언 전체가** 버려진다. 화면에는 「항목들이 오른쪽 아래에 겹쳐 있다」로 보인다.\
`getComputedStyle(el).gridTemplateAreas` 가 `none` 이면 그것이다.

### 2. 열 개수를 세다 틀린다

행이 다섯을 넘으면 사람이 센 것과 실제가 갈린다. **공백을 맞춰 적어도 토큰 수는 따로 센다.**\
도면을 고친 뒤에는 계산값을 한 번 읽는다.

### 3. `grid-area: hd` 가 라인 이름으로 떨어진 줄 모른다

영역이 없으면 `hd` 는 **라인 이름 찾기**가 되고, 그것도 없으면 **암묵 격자**로 간다.\
이름 오타 하나와 도면 무효가 **똑같은 증상**을 낸다 — 진단 3창으로 가른다.

### 4. 도면과 라인 이름에 같은 이름을 쓴다

**먼저 나온 라인이 이긴다.** 도면이 이길 거라고 생각하면 자리가 통째로 어긋난다.\
처방은 규칙 외우기가 아니라 **이름을 겹치지 않게 짓는 것**이다.

### 5. `.` 을 「막아 둔 칸」으로 읽는다

`.` 은 **이름이 없는 칸**일 뿐이다. `grid-area` 를 안 준 항목이 자동 배치로 그 자리에 들어간다.\
진짜로 비워 두려면 그 자리에 들어갈 항목이 없어야 한다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 이유 |
|---|---|---|
| 페이지 뼈대(헤더·사이드바·본문·푸터) | **`grid-template-areas`** | 레이아웃이 코드에 그림으로 보인다 |
| 중단점마다 배치가 통째로 바뀐다 | 도면만 바꾼다 | 항목 쪽 CSS 를 한 글자도 안 건드린다 |
| 항목 수가 정해지지 않은 목록 | 도면 말고 **자동 배치**([28번](../28-grid-placement/)) | 도면은 칸 수가 고정이다 |
| 불규칙하지만 이름은 쓰고 싶다 | **이름 붙은 라인** | 트랙을 끼워 넣어도 안 밀린다 |
| 트랙 하나를 자주 끼웠다 뺐다 한다 | 번호 대신 이름 | 번호는 전부 밀린다 |
| 카드 내부 줄을 카드끼리 맞춘다 | **`subgrid`**([30번](../30-subgrid/)) | 도면으로는 안 된다 |

판단 규칙 두 줄.

- **칸 수가 고정이면 도면, 아니면 자동 배치.** 도면은 「몇 칸인지 아는 레이아웃」의 도구다.
- **이름은 한 좌표계에서 하나만 쓴다.** 도면 이름과 라인 이름을 섞으면 (6)의 자리에 걸린다.

## 핵심 문장

- 도면은 **문자열 하나가 한 행**이고, 같은 이름이 붙어 있으면 한 영역이다. **반드시 직사각형**이어야 한다.
- 무효한 도면은 **통째로, 조용히** 버려진다. 확인은 `cssRules`(빈 문자열) → 계산값(`none`) 두 자리다.
- 버려진 뒤 `grid-area: hd` 는 **라인 이름 찾기로 떨어져** 항목을 암묵 격자로 밀어낸다 — 「겹쳐 있다」가 그 증상이다.
- **`-start`/`-end` 짝은 영역을 만들고, 영역은 `-start`/`-end` 라인을 만든다.** 양방향이다.
- 이름이 겹치면 **먼저 나온 라인이 이긴다.** 도면이 이기는 것도, 라인 이름이 이기는 것도 아니다.
- 도면은 **자리만** 정한다. 크기는 [27번](../27-grid-track-sizing/), 번호 배치는 [28번](../28-grid-placement/)의 몫이다.

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 29번) · 「버전·지원 기준」의 Baseline 표
- [목록의 **27번 주제**](../27-grid-track-sizing/)(Grid 트랙 정의) — ★ **트랙 크기는 거기.** 도면은 크기를 안 정한다
- [목록의 **28번 주제**](../28-grid-placement/)(Grid 배치) — ★ **라인 번호·`span`·자동 배치·`grid-area` 네 값 순서는 거기.** 여기는 이름 쪽만
- [목록의 **30번 주제**](../30-subgrid/)(`subgrid`) — 자식이 부모의 **라인 이름까지** 잇는 것
- [목록의 **24번 주제**](../24-flexbox-axes/)(Flexbox 축과 정렬) — 정렬 어휘의 정본
- [목록의 **07번 주제**](../07-syntax-and-error-recovery/)(구문과 오류 복구) — 무효한 선언 하나가 통째로 버려지는 규칙
- [목록의 **16번 주제**](../16-display-inner-outer/)(`display` 의 내부/외부 값) — `grid` 와 `inline-grid`
- [`reference/render-rules.md`](../../../../../../reference/render-rules.md) — 이 문서의 `demo` 블록 규칙

## 용어 풀이

- **영역(grid area)** — 라인 넷으로 둘러싸인 직사각형 구역.
- **영역 이름(grid area name)** — 도면에 적는 식별자. 같은 이름이 인접해 있으면 한 영역이 된다.
- **도면(`grid-template-areas`)** — 문자열 목록으로 그린 격자 지도. 문자열 하나가 한 행이다.
- **`.`(null cell token)** — 이름이 없는 칸. `...` 도 같은 뜻으로 **칸 하나**다.
- **이름 붙은 라인(named grid line)** — `[이름]` 으로 이름을 준 격자 라인. 하나에 여럿 붙일 수 있다.
- **`-start`/`-end` 접미사 규칙** — 짝이 맞는 두 라인 이름이 같은 이름의 영역을 만들고, 영역이 같은 이름의 두 라인을 만든다.
- **암묵 라인 이름** — 도면이 자동으로 만들어 주는 `<이름>-start`/`<이름>-end`.
- **진단 3창** — `cssRules`(담겼나) → 매치(잡혔나) → `getComputedStyle`(이겼나). CSS 에 에러가 없어 증상이 같기 때문에 필요하다.
- **명시 격자 / 암묵 격자** — 내가 정의한 트랙 / 엔진이 만든 트랙. 이름을 못 찾은 항목이 뒤쪽으로 밀려난다(28번).

---

## 더 들어가면

- **`grid-template` 단축**은 행·열·도면 셋을 한 줄에 쓴다 — `grid-template: "hd hd" 32px "sb mn" 1fr / 100px 1fr;`\
  도면 문자열 **뒤에 그 행의 크기**를, `/` 뒤에 열 크기를 쓰는 형태다. 읽기는 좋지만 한 줄이 길어져 실무에서는 셋을 따로 쓰는 편이 많다.
- **`grid` 단축은 `grid-template` 에 더해 `grid-auto-*` 까지 초기화한다.** 앞에 쓴 `grid-auto-rows` 가 지워지므로 섞어 쓰지 않는다.
- **중단점마다 도면만 바꾸는 것**이 이 기능의 대표 용법이다. 미디어 쿼리 안에서 `grid-template-areas` 와 `grid-template-columns` 두 줄만 바꾸면\
  항목 쪽 CSS(`grid-area: hd` 등)는 한 글자도 안 고쳐도 된다.\
  ★ 다만 **「도면이니까 접근성이 안전하다」는 말은 아니다.** 도면으로도 마크업 순서와 다른 시각 순서를 얼마든지 만들 수 있다.\
  `dense`([28번](../28-grid-placement/))와 갈리는 점은 **엉킴이 자동으로 생기느냐 내가 적어 넣느냐**뿐이다 — 도면은 눈으로 검토할 수 있고 `dense` 는 항목 수에 따라 바뀐다.
- **도면의 이름은 `<custom-ident>`** 라 `span`·`auto` 같은 예약어는 못 쓴다. 한글도 문법적으로는 쓸 수 있지만 이 문서에서는 **안 돌려 봤다.**
- **`grid-area` 하나에 이름을 쓰면 네 축에 전부 그 이름이 들어간다** — `grid-area: hd` 는 `grid-row-start/column-start/row-end/column-end` 를 모두 `hd` 로 만든다.\
  그래서 영역이 없을 때 **네 축이 동시에** 라인 이름 찾기로 떨어지고, 항목이 행·열 **양쪽 모두** 암묵 격자로 밀려난다((2)의 실측이 그것이다).

# web-api/11 — 스크롤 제어: `scrollTo`/`scrollBy`/`scrollIntoView`·스크롤 컨테이너 찾기·위치 복원 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 `--dump-dom` 으로 실제로 받은 것**이다. 명령은 블록마다 배너로 실려 있다.\
> ★ **배너의 `--window-size=1000,800` 이 이 문서의 전제다.** 스크롤 상한이 뷰포트 높이에 달려 있어 창이 다르면 수치가 달라진다.\
> 규칙은 [CSSOM View Module](https://drafts.csswg.org/cssom-view/) 과 [HTML Living Standard](https://html.spec.whatwg.org/multipage/nav-history-apis.html#scroll-restoration-mode) 로 접지했다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> ★ **못 잰 것이 하나 있다** — `behavior: 'smooth'` 의 **도착**이다(A9).

**★ 이 주제에는 흔들리는 칸이 거의 없다** — 좌표를 재지만 시간을 안 재기 때문이다.

| 안 흔들리는 칸 | 흔들리는 칸 · 못 잰 칸 |
|---|---|
| 모든 스크롤 오프셋 · 클램프 상한 · `scrollingElement` 가 누구인가 · `scrollIntoView` 옵션별 결과 · `overflow` 값별 판정 | **창 크기를 바꾸면 상한과 좌표 전부** |
| 세 판을 돌려 **한 글자도 같았다** | 스크롤바가 먹는 **15px**(플랫폼 설정) |
| — | **못 잰 것** — `behavior: 'smooth'` 의 도착 시각과 중간 값(A9) |
| — | Chrome 판 번호 |

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 문서를 굴리는 것은 누구인가 — 모드가 뒤집는다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-11-doc.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,11p'
문서를 굴리는 것은 누구인가 — 표준 모드
  document.compatMode      = CSS1Compat
  document.scrollingElement = documentElement

무엇을 했나                       scrollY     documentElement.scrollTop body.scrollTop
초기                              0           0                         0
window.scrollTo(0, 300)           300         300                       0
documentElement.scrollTop = 100   100         100                       0
body.scrollTop = 700              100         100                       0

★ 표준 모드에서 body.scrollTop 에 쓰는 것은 아무 일도 안 한다 — 예외도 없다.
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-11-quirks.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
doctype 을 지우면 — 호환 모드
  document.compatMode       = BackCompat
  document.scrollingElement = body
  window.scrollTo(0, 300) 뒤   scrollY=300  documentElement.scrollTop=0  body.scrollTop=300
  documentElement.scrollTop=100 뒤  scrollY=300  (아무 일도 안 일어난다)
  body.scrollTop=700 뒤             scrollY=700  (이쪽이 문서를 굴린다)
(exit 0)
```

**왜 그런가**

- **표준 모드(`CSS1Compat`)에서는 `documentElement`** 가 문서를 굴린다. `scrollTo(0, 300)` 뒤 **`documentElement.scrollTop` 이 300, `body.scrollTop` 은 0** 이다.
- ★ **`body.scrollTop = 700` 은 아무 일도 안 한다.** 예외도 경고도 없고 되읽으면 0 이다. **「안 굴러갔다」는 되읽어야만 안다.**
- **호환 모드(`BackCompat`)에서는 정확히 반대**다 — `body` 가 굴리고 `documentElement` 쪽이 무시된다.
- **`document.scrollingElement` 가 그 답을 직접 준다** — 표준 모드에서 `documentElement`, 호환 모드에서 `body`. **모드를 따지지 말고 이것을 쓴다.**
- ★ **두 모드에서 똑같이 동작하는 것은 `window.scrollY`**(와 `window.scrollTo`)다. 모드에 안 휘둘리는 창구다.
- **옛 관용구 `document.body.scrollTop || document.documentElement.scrollTop`** 은 바로 이 갈림 때문에 생겼다 — **어느 쪽이 0 인지 모르니 둘을 `||` 로 이어 둔 것**이다. `scrollingElement` 가 그 관용구를 대체한다.

### 2. 같은 일을 시키는 네 표면 — 축 순서가 뒤집혀 보인다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-11-api.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,12p'
같은 일을 시키는 네 가지 표면 — 대상은 #sc 하나
무엇을 불렀나                           sc.scrollTop    sc.scrollLeft
(초기)                                  0               0
sc.scrollTop = 120                      120             0
sc.scrollTo(30, 60)  ← x, y 순서       60              30
sc.scrollTo({top: 200})                 200             30
sc.scrollBy(10, 25)                     225             40
sc.scrollBy({top: -25})                 200             40
sc.scrollTo({top:300, left:0})          300             0

★ 두 인자 꼴은 (x, y) 이고 객체 꼴은 {left, top} 이다 — 순서가 뒤집혀 보인다.
★ 객체 꼴에서 빠뜨린 축은 그대로 둔다(scrollTo 여도 그 축은 안 움직인다).
(exit 0)
```

**왜 그런가**

- **`scrollTop = 120`** — 세로만 120. 가로는 그대로.
- **`scrollTo(30, 60)`** — **가로 30 · 세로 60.** 두 인자 꼴은 **`(x, y)`** 다. 표에서 `scrollTop` 이 60, `scrollLeft` 가 30 이 된 줄이 그것이다.
- **`scrollTo({top: 200})`** — 세로만 200 으로 가고 **`scrollLeft` 는 30 그대로**다. ★ **이름이 `scrollTo` 여도 빠뜨린 축은 안 움직인다** — 객체 꼴에서 지정하지 않은 축은 **현재 값을 유지**하도록 명세가 정한다.
- **`scrollBy(10, 25)`** — 현재 값에 **가로 10 · 세로 25** 를 더한다.
- **`scrollBy({top: -25})`** — 음수를 주면 되감긴다.
- ★ **두 꼴을 섞어 쓰면 여기서 틀린다.** 두 인자 꼴에는 「그대로」가 없고 **둘 다 지정**된다.

### 3. 범위 밖 값을 넣으면 — 넷 다 조용하다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-11-api.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '14,26p'
범위 밖 값을 넣으면 — 잘린다, 예외가 아니다
무엇을 넣었나                           sc.scrollTop    판정
-50                                     0               0 으로 잘림
999999                                  615             상한 615 으로 잘림
  상한 = scrollHeight(800) - clientHeight(185) = 615
'abc' (문자열)                          0               0 으로 읽힌다
100.4 (소수)                            100             되읽으면 정수다
100.7 (소수)                            101             되읽으면 정수다
  scrollTop 의 타입은 number 인데 이 판에서는 장치 픽셀로 맞춰져 돌아온다(dpr = 1).

스크롤 컨테이너가 아닌 요소에 쓰면 — 조용히 0 이다
  #in.scrollTop = 100 을 쓰고 되읽으면 0   (overflow=visible · scrollHeight 800 · clientHeight 800)
  예외도 경고도 없다. 「안 굴러갔다」는 되읽어야만 안다.
(exit 0)
```

**왜 그런가**

- **음수는 0 으로, 너무 큰 값은 상한으로 잘린다.** **예외가 나는 줄은 하나도 없다** — 명세가 「범위 안으로 clamp 하라」고 정한다.
- **상한은 `scrollHeight − clientHeight`** 다. 이 상자는 세로가 200 인데 **가로 스크롤바가 15 를 먹어 `clientHeight` 가 185** 라 상한이 615 다.
- **문자열은 `0`** 이다 — 숫자로 바꿀 수 없는 값이 0 으로 떨어진다. **오타가 「맨 위로 가기」가 된다.**
- **소수는 되읽을 때 정수**다. 이 판은 `devicePixelRatio` 가 1 이라 장치 픽셀에 맞춰진 것이고, **다른 배율에서는 소수가 남을 수 있다**(여기서 확인하지 않았다).
- ★ **스크롤 컨테이너가 아닌 요소에 쓰면 조용히 0** 이다(`overflow` 가 `visible` 이고 넘치지도 않는다). **진단은 되읽기 한 줄뿐**이다 — 「대입하고 되읽어 값이 남나」가 [CSS 23번 주제](../../languages/css/syntax/23-overflow-and-scroll-containers/2-summary.md)가 세운 판정법이고, 이 주제의 창 ③ 이다.

### 4. `scrollIntoView` 가 무엇을 움직이나 — 한 번에 여럿이다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-11-into.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,6p'
창 ④ — 무엇이 움직였는지 조상 전체를 훑는다
무엇을 불렀나                       scrollY   outer.scrollTop  inner.scrollTop  t.rect.top
(초기)                              0         0                0                1154
t.scrollIntoView()                  542       12               600              0
  ★ 한 번 불렀는데 셋이 같이 움직였다 — 스크롤 컨테이너를 만날 때마다 굴린다.
  ★ mid 는 스크롤 컨테이너가 아니라 안 움직였다: mid.scrollTop = 0
(exit 0)
```

**왜 그런가**

- **한 번 불렀는데 셋이 움직였다** — `scrollY`·`outer.scrollTop`·`inner.scrollTop`. 명세가 **「목표에서 위로 올라가며 스크롤 컨테이너를 전부 굴리라」고** 정한다.
- **`mid` 는 안 움직였다** — `overflow: visible` 이라 스크롤 컨테이너가 아니다. **건너뛴다.**
- ★ **한 요소만 보고 판정하면 절반만 본다.** 「`inner.scrollTop` 이 0 이네」로는 **안 굴러간 것**인지 **바깥이 대신 굴러간 것**인지 구분이 안 된다 — A6 이 그 차이를 보여 준다. **그래서 이 주제의 창 ④ 가 「조상 전수 스캔」이다.**
- **실무의 사고가 여기서 난다** — 모달 안의 요소에 부르면 **뒤의 페이지까지 굴러간다.**

### 5. 옵션이 정하는 것 — 불리언은 옛 이름이다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-11-into.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '8,17p'
옵션이 정하는 것
무엇을 불렀나                       scrollY   outer.scrollTop  inner.scrollTop  t.rect.top
scrollIntoView(true)                542       12               600              0
scrollIntoView(false)               91        0                380              683
scrollIntoView({"block":"start"})   542       12               600              0
scrollIntoView({"block":"center"})  323       0                490              341
scrollIntoView({"block":"end"})     91        0                380              683
scrollIntoView({"block":"nearest"}) 91        0                380              683
  ★ 인자 없음 = true = {block: "start"} · false = {block: "end"} 다.
  ★ nearest 는 「이미 보이면 안 움직인다」 — 여기서는 아래에 있었으므로 end 와 같은 자리로 갔다.
(exit 0)
```

**왜 그런가**

- **같은 결과끼리 묶으면 세 덩어리**다.
  - **`(인자 없음)` = `true` = `{block: 'start'}`** — 목표를 **맨 위**에 붙인다(`rect.top` 이 0).
  - **`false` = `{block: 'end'}` = `{block: 'nearest'}`**(이 상황에서) — 목표를 **맨 아래**에 붙인다.
  - **`{block: 'center'}`** — 가운데.
- **불리언 인자는 옵션 객체의 옛 이름**이다. 오늘은 객체 꼴을 쓰는 것이 낫다 — `inline` 축과 `behavior` 를 같이 줄 수 있다.
- ★ **`nearest` 와 `end` 가 같은 결과를 준 것은 목표가 아래에 있었기 때문**이다. `nearest` 는 **「이미 보이면 안 움직이고, 안 보이면 최소한으로 움직인다」이므로** **목표가 이미 보이는 상태**에서 던져야 갈린다 — 그 자리가 (11)의 demo 다(거기서 `start` 로 맞춘 뒤 `nearest` 를 누르면 **한 글자도 안 움직였다**).
- **`inline` 축도 같은 네 값**을 받는다. **이 문서는 세로 축만 던졌다.**

### 6. 어떤 `overflow` 가 굴러가나 — `hidden` 은 굴러간다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-11-into.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '19,27p'
스크롤 컨테이너로 쳐 주는 overflow 는 무엇인가 — #inner 의 값만 바꿨다
#inner 의 overflow                  scrollY   outer.scrollTop  inner.scrollTop  굴렀나
overflow: visible                   542       612              0                안 굴렀다
overflow: hidden                    542       12               600              굴렀다
overflow: clip                      580       574              0                안 굴렀다
overflow: auto                      542       12               600              굴렀다
overflow: scroll                    542       12               600              굴렀다
  ★ hidden 도 스크롤 컨테이너다 — 스크롤바가 없을 뿐이다. clip 은 아니다.
  ★ inner 가 안 굴러가면 그만큼을 바깥이 대신 굴린다(outer.scrollTop 이 커진다).
(exit 0)
```

**왜 그런가**

- **`auto`·`scroll`·`hidden` 은 굴러가고 `visible`·`clip` 은 안 굴러간다.**
- ★ **화면이 같은데 갈리는 짝은 `hidden` 과 `clip`** 이다. 둘 다 내용을 자르지만 **`hidden` 만 스크롤 컨테이너**다 — 스크롤바가 없을 뿐 굴릴 수 있다(정본: [CSS 23번 주제](../../languages/css/syntax/23-overflow-and-scroll-containers/2-summary.md)). `scrollIntoView` 가 그 판정을 **그대로 따른다.**
- ★ **`inner` 가 안 굴러가면 그 몫이 바깥으로 간다** — `outer.scrollTop` 이 크게 뛴다. **총 이동량은 비슷한데 누가 움직였는지가 다르다.**
- **`clip` 줄만 `scrollY` 가 다르다** — 바깥이 더 멀리 굴러야 했기 때문이다.

### 7. 스크롤 컨테이너를 스크립트로 찾기 — 루트에서 예외가 난다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-11-into.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '29,32p'
그래서 스크롤 컨테이너를 스크립트로 찾으려면
  #inner(auto ← 스크롤러)  <  #mid(visible)  <  #outer(auto ← 스크롤러)  <  BODY(visible)  <  HTML(visible)
  ★ 사슬 끝의 HTML 은 overflowY 가 visible 인데 문서는 굴러간다(scrollY 를 120 로 만들 수 있다).
    위 규칙만으로는 루트를 놓친다 — 마지막 한 칸은 document.scrollingElement 로 따로 잡아야 한다.
(exit 0)
```

**왜 그런가**

- **조건이 둘인 이유** — `overflow` 만 보면 **넘치지 않는 상자**까지 스크롤러로 세게 된다(굴려도 0 이다). **넘침만 보면** `visible` 인 상자까지 세게 된다(굴러가지 않는다). **둘의 곱**이라야 「지금 실제로 굴릴 수 있는 상자」다.
- ★ **그 규칙으로 사슬을 훑으면 루트를 놓친다.** 출력의 마지막이 **`HTML(visible)`** 이다 — **계산값이 `visible` 인데 문서는 굴러간다**(같은 줄에서 `scrollY` 를 120 으로 만들었다).
- **뷰포트 스크롤은 `overflow` 로 만들어진 것이 아니기 때문**이다. 루트 요소의 `overflow` 는 **뷰포트로 전파**되어 뷰포트가 굴러가는 것이고, 요소 자신은 스크롤 컨테이너 판정을 안 받는다.
- **그래서 사슬의 마지막 칸을 `document.scrollingElement` 로 메운다.**

### 8. `behavior: 'smooth'` — CSS 한 줄이 스크립트를 비동기로 만든다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-11-smooth.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,9p'
behavior 가 무엇을 바꾸나 — 부른 직후 같은 tick 에서 되읽는다
  scrollTo({top: 500, behavior: 'auto'})   직후 sc.scrollTop = 500
  scrollTo({top: 500})  (기본값)          직후 sc.scrollTop = 500
  scrollTo({top: 500, behavior: 'smooth'}) 직후 sc.scrollTop = 0   ★ 안 움직였다

CSS 로 scroll-behavior: smooth 를 준 상자는 scrollTop 대입도 비동기가 되나
  css.scrollTop = 500 직후 되읽으면 0   (getComputedStyle = smooth)
  css.scrollTo({top: 500}) 직후 되읽으면 0   ← 기본값이 CSS 를 따라간다
  css.scrollTo({top: 500, behavior: 'instant'}) 직후 500   ← CSS 를 눌러 덮는다
(exit 0)
```

**왜 그런가**

- **`auto`(기본)는 동기**다 — 부른 직후 되읽으면 **이미 500** 이다.
- **`smooth` 는 비동기**다 — 부른 직후 되읽으면 **0** 이다. **한 tick 안에서는 아무 일도 안 일어난다.**
- ★ **CSS 의 `scroll-behavior: smooth` 가 `scrollTop` 대입까지 비동기로 만든다.** `css.scrollTop = 500` 을 쓰고 되읽어도 0 이다 — **스크립트 쪽에는 아무 표시가 없는데 CSS 한 줄이 그 코드의 동기성을 바꾼다.** 명세가 그렇게 정했다(옵션의 `behavior` 기본값이 CSS 의 `scroll-behavior` 를 따른다).
- **`behavior: 'instant'` 는 그 CSS 를 눌러 덮는다** — 스크립트에서 강제로 동기로 되돌리는 유일한 길이다.
- **도착을 기다리려면** `scrollend` 이벤트가 필요하다. **이 문서는 그 이벤트를 관측하지 못했다**(A9).

### 9. 도착은 관측됐는가 — 못 잰 것이다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-11-smooth.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '11,14p'
smooth 가 어디까지 갔나 — 부른 직후 0  ·  동기 루프 200ms 뒤 0  ·  setTimeout 0 뒤 0  ·  setTimeout 0 을 한 겹 더 0
  ★ 동기 루프로는 못 따라간다(스크립트가 도는 동안 애니메이션이 진행하지 않는다).
  ★ --dump-dom 은 load + setTimeout(…, 0) 두 겹까지만 기다린다 — 세 겹을 걸면 출력이 통째로 사라진다.
  ★ 그래서 「도착한 순간」은 이 도구로 못 잰다. 관측한 것은 「부른 직후에는 안 움직인다」까지다.
(exit 0)
```

**왜 그런가**

- **네 지점이 전부 0** 이다 — 부른 직후도, 동기 루프 200ms 뒤도, `setTimeout` 두 겹 뒤도.
- ★ **동기 루프로 기다리면 안 되는 이유** — 스크롤 애니메이션과 스크립트가 **같은 스레드**에 있다. 루프가 도는 동안에는 **애니메이션이 진행할 틈이 없다.** 「기다렸는데 안 움직였다」는 **기다린 방법이 틀린 것**이다.
- **`--dump-dom` 이 기다리는 끝은 `load` 뒤의 `setTimeout(…, 0)` 두 겹까지**다. 세 겹을 걸면 **출력이 통째로 사라진다**(직접 확인했다).
- ★ **그래서 이것은 「안 돌려 본 것」이 아니라 「못 잰 것」이다.** 던지기는 여러 형태로 던졌고 **도구가 그 시점을 못 본다.** 「smooth 가 몇 ms 걸린다」를 이 문서는 **주장하지 않는다.** 재려면 CDP 로 프레임을 몰아야 한다.
- **그래도 실무 결론은 관측한 것만으로 선다** — **`smooth` 뒤에 좌표를 읽으면 옛 값이다.**

### 10. 위치 복원 — 스위치이지 복원 기능이 아니다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-11-doc.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '13,18p'
위치 복원 — history.scrollRestoration
  기본값 = auto
  'manual' 로 바꾼 뒤 = manual
  'zzz' 를 대입하면 = 예외 없음 · 되읽으면 manual (열거값이라 조용히 무시된다)
  'auto' 로 되돌린 뒤 = auto
  ★ 실제 복원이 일어나는 것은 뒤로 가기·새로 고침 때다 — 이 문서는 그 순간을 관측하지 못했다(못 잰 것).
(exit 0)
```

**왜 그런가**

- **기본값은 `'auto'`** 이고 **`'manual'` 로 바꿀 수 있다.**
- ★ **잘못된 값은 조용히 무시된다.** `'zzz'` 를 대입해도 **예외가 없고** 되읽으면 옛 값(`manual`)이다 — **열거된 값만 받는 속성**이라서다. [06번 주제](../06-attribute-vs-property/2-summary.md)의 「조용히 버려짐」과 같은 모양이다.
- **이 속성이 하는 일** — **브라우저의 자동 복원을 켜고 끄는 스위치**다. **복원해 주는 기능이 아니다.** `'manual'` 로 두면 브라우저가 손을 떼고 **내가 직접 복원해야 한다.**
- ★ **튀는 진짜 원인은 경합**이다 — 브라우저가 복원한 뒤에 **이미지·폰트·비동기 데이터가 로드되어 문서 높이가 늘면** 그 위치가 엉뚱해진다. 처방은 **`manual` 로 끄고, 내용이 자리 잡은 뒤에 직접 복원**하는 것이다.
- **이 문서는 그 순간을 관측하지 못했다** — 뒤로 가기·새로 고침이 필요한데 `--dump-dom` 은 한 번 여는 것뿐이다. **「이 값이 무엇인가」까지만** 관측했고, 경합은 **재현하지 못했다.**

### 11. 다른 주제와 잇기

**출력** — 이 답의 근거는 앞의 블록들과 선행 주제들이다. 새 출력은 없다.

**왜 그런가**

- **[09번 주제](../09-element-geometry/2-summary.md)와의 경계선** — **그쪽은 `scrollTop`·`scrollHeight`·`clientHeight` 를 읽어 「어디에 있나」를 아는 쪽이고, 여기는 그 값을 써서 「옮기는」 쪽**이다. 상한이 `scrollHeight − clientHeight` 라는 것은 **읽기 쪽 지식**이고, 그 상한에서 **잘린다**는 것은 **쓰기 쪽 규칙**이다.
- **스크롤 핸들러 안에서 좌표를 읽으면 [목록의 10번 주제](../10-layout-thrashing/)가 시작된다** — 그 주제의 실측에서 **`window.scrollY` 도 레이아웃 방아쇠**였다. 스크롤 이벤트는 자주 오므로 **가장 흔한 스래싱 자리**다.
- ★ **이 주제의 쓰기 가운데 예외를 던지는 것은 하나도 없었다.** 범위 밖·숫자 아님·컨테이너 아님·모드 반대·열거값 오타 — **다섯 가지 실패가 전부 조용하다.** 그 뜻은 **「쓰고 나서 되읽는 것까지가 한 번의 호출」이라는** 것이다. [08번 주제](../08-getcomputedstyle/2-summary.md)의 읽기 전용 위반이 **예외를 던졌던 것과 대조적**이다.
- **「보이나」를 스크롤 위치로 판정하지 않는 법은 [목록의 35번 주제](../35-intersection-observer/)**(IntersectionObserver)다. 좌표를 읽지 않으므로 방아쇠도 안 당긴다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · **`--window-size=1000,800`**(뷰포트 1000×713). **엔진은 이것 하나다.** **크로스 브라우저 이식성은 이 문서의 주장 범위 밖**이다.

★ **창 크기를 배너에 박은 이유** — 스크롤 상한이 **`scrollHeight − clientHeight`** 이고 `clientHeight` 는 뷰포트에 달렸다. 배너대로 던져야 같은 글자가 나온다.\
★ **시간은 재지 않았다.** 이 주제의 읽기·쓰기가 얼마나 비싼지는 [10번 주제](../10-layout-thrashing/2-summary.md)의 몫이다.\
★ **못 잰 것** — `behavior: 'smooth'` 의 **도착 시각과 중간 값**(A9). 그리고 **`scrollend`·`scroll` 이벤트**와 **뒤로 가기 복원의 순간**도 관측하지 못했다.

**하네스** — 01\~10 과 같은 것을 쓴다. 블록은 `capture.sh` 가 전부 파일로 받았고 사람이 옮겨 적지 않았다.

```bash
# 블록 하나를 다시 던지는 법
google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 \
  --dump-dom wa09b-11-into.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
```

```js
// 이 주제의 창 ④ — 한 번 부르고 조상 '전부' 의 오프셋을 찍는다
const 찍기 = () => [scrollY, outer.scrollTop, inner.scrollTop, mid.scrollTop];
// 창 ③ (CSS 23번의 판정법) — 대입하고 되읽는다
el.scrollTop = 200;  el.scrollTop === 0 ? '컨테이너가 아니다' : '컨테이너다';
// 한글 칸 정렬은 JS 안에서 2폭 padw 로 한다. padEnd 는 UTF-16 단위라 어긋난다.
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
```

★ **`--virtual-time-budget` 은 쓰지 않았다**(이 갈래의 정본 규칙).\
★ **`--dump-dom` 은 `load` 뒤의 `setTimeout(…, 0)` 을 두 겹까지만 기다린다**(직접 확인). 그 한계가 A9 의 결론이 됐다.\
★ **출력은 `<pre>` 가 아니라 `<script type="text/plain">` 에 담아 마커로 잘랐다.**

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 표준 모드 — `scrollingElement` 와 세 창구 | 3 | 동작 방식 (1) · A1 |
| **호환 모드**(doctype 없는 사본) — 같은 네 줄 | 3 | 동작 방식 (1) · A1 |
| 네 표면 × 7단계 추적 | 3 | 동작 방식 (2) · A2 |
| 범위 밖·문자열·소수·비컨테이너 5종 | 3 | 동작 방식 (3) · A3 |
| 창 쪽 표면 4종 + `scrollingElement` 동일성 | 3 | 동작 방식 (4) |
| 창 ④ — `scrollIntoView` 한 번에 조상 4곳 | 3 | 동작 방식 (5) · A4 |
| 옵션 7가지 | 3 | 동작 방식 (6) · A5 |
| `overflow` 5값 × 조상 3곳 | 3 | 동작 방식 (7) · A6 |
| 조상 사슬 스캔 + 루트 예외 | 3 | 동작 방식 (8) · A7 |
| `behavior` 3종 + CSS `scroll-behavior` 3종 | 3 | 동작 방식 (9) · A8 |
| smooth 진행 4지점 | 3 | 동작 방식 (9) · A9 |
| `scrollRestoration` 4단계 | 3 | 동작 방식 (10) · A10 |
| `demo` 블록을 래퍼에 띄워 네 버튼 + `clip` 사본 확인 | 1 | 동작 방식 (11)의 demo |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| **모든 상한과 좌표** | 위 표 | **창 크기**에 달렸다. 배너의 `--window-size` 가 전제다 |
| 스크롤바가 먹는 폭 | **15px** | 플랫폼·설정에 달렸다. 겹침 스크롤바면 0 이다 |
| 소수를 넣으면 정수로 돌아오는 것 | `100.4` → `100` | **장치 픽셀 비**(이 판은 1)에 달렸다 |
| **`scrollIntoView` 가 고르는 정확한 양** | 위 출력 | ★ **명세는 「보이게 하라」까지만 정한다.** `nearest` 가 특히 구현 쪽이다 |
| `smooth` 의 지속 시간·곡선 | **못 쟀다** | 명세가 시간을 정하지 않는다 |
| `overflow` 값별 판정 | 위 출력 | **명세**(CSS Overflow)가 정한 절차다. 값이 아니라 절차를 외운다 |
| 모드별 `scrollingElement` | 위 출력 | **명세**가 정한 절차다 |

**안 돌려 본 것** — ① Firefox·Safari 에서의 재현(엔진이 없다). ② **`scrollend`·`scroll` 이벤트** — 프레임을 못 몰아 **관측하지 못했다.** ③ **뒤로 가기·새로 고침에서의 실제 복원**과 **이미지 로딩과의 경합** — **재현하지 못했다.** ④ **가로 축**(`scrollLeft`·`inline` 옵션) — 세로만 던졌다. ⑤ **쓰기 방향이 오른쪽에서 왼쪽인 문서**에서 `scrollLeft` 가 음수가 되는 판 — **확인하지 않았다.** ⑥ **`scroll-snap`·`overscroll-behavior`** 가 스크립트 스크롤에 미치는 영향 — **던지지 않았다.** ⑦ **`scrollIntoViewIfNeeded()`**(비표준) — 표면만 적었다. ⑧ **`devicePixelRatio` 가 1 이 아닌 환경**에서 소수 오프셋이 남는지 — **확인하지 않았다.** ⑨ **중첩 스크롤러에서 `smooth` 를 줬을 때 조상들이 동시에 움직이는지** — smooth 자체를 못 따라가 **확인하지 못했다.**

## 용어 풀이

- **스크롤 컨테이너(scroll container)** — 내용이 넘칠 때 굴릴 수 있는 상자. `overflow` 가 `auto`·`scroll`·`hidden` 일 때 생긴다(`clip` 은 아니다).
- **스크롤포트(scrollport)** — 그 상자에서 실제로 보이는 칸. `clientHeight` 가 재는 칸.
- **`scrollingElement`** — 문서를 굴리는 요소. 표준 모드는 `<html>`, 호환 모드는 `<body>`.
- **호환 모드(quirks mode)** — `<!doctype html>` 이 없을 때의 옛 동작 모드. `document.compatMode` 가 `BackCompat`.
- **클램프(clamp)** — 범위 밖 값을 범위 안으로 잘라 넣는 것.
- **`ScrollToOptions`** — `{left, top, behavior}` 꼴의 인자 객체.
- **`block`/`inline`** — `scrollIntoView` 의 두 축. 글 흐름 기준이라 가로쓰기에서는 `block` 이 세로다.
- **`scrollRestoration`** — 뒤로 가기에서 브라우저가 위치를 복원할지 정하는 **스위치**.
- **조용한 실패(silent failure)** — 예외도 경고도 없이 아무 일도 안 일어나는 것. 이 주제의 쓰기에 다섯 가지가 있다.
- **못 잰 것** — 도구가 그 순간을 볼 수 없어 확인하지 못한 것. 「안 돌려 본 것」과 다르다.

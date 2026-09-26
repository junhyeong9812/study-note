# web-api/09 — 요소 기하: `getBoundingClientRect`·`offset*`/`client*`/`scroll*` 과 좌표계 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 `--dump-dom` 으로 실제로 받은 것**이다. 명령은 블록마다 배너로 실려 있다.\
> ★ **배너의 `--window-size=1000,800` 이 이 문서의 전제다.** 창이 다르면 절대 좌표가 전부 달라진다 — 기본 창은 780×493 이다.\
> 규칙은 [CSSOM View Module](https://drafts.csswg.org/cssom-view/) 로 접지했다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> ★ **「CSS 가 상자를 어떻게 정하나」는 이 문서가 아니다** — [CSS 15번 주제](../../languages/css/syntax/15-box-model-and-box-sizing/2-summary.md)가 정본이다.

**★ 이 주제에는 흔들리는 칸이 거의 없다** — 시간이 아니라 좌표를 재기 때문이다.

| 안 흔들리는 칸 | 흔들리는 칸 |
|---|---|
| 모든 좌표·치수 · `offsetParent` 가 누구인가 · 정수/소수 여부 · `getClientRects().length` · 객체 동일성 | **창 크기를 바꾸면 절대 좌표 전부** — 그래서 배너에 `--window-size` 를 박았다 |
| 세 판을 돌려 **한 글자도 같았다** | 스크롤바가 먹는 **15px**(플랫폼 설정) · 인라인 조각의 폭(글꼴 치수) |
| — | Chrome 판 번호 |

측정 조건 — **시간을 재지 않는다.** 이 주제의 읽기가 얼마나 비싼지는 [10번 주제](../10-layout-thrashing/2-summary.md)가 잰다.

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 스크롤을 세 번 움직이면 — `rect` 만 움직이고 `offsetTop` 은 가만있다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-09-three.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,6p'
한 요소에 세 묶음을 동시에 대고 스크롤을 세 번 움직였다
무엇을 했나           rect.top    rect.left   offsetTop   offsetLeft  t.scrollTop sc.scrollTop
초기                  765.00      155.00      250         120         0           0
sc.scrollTop = 100    665.00      155.00      250         120         0           100
window 를 200 로      465.00      155.00      250         120         0           100
t.scrollTop = 50      465.00      155.00      250         120         50          100
(exit 0)
```

**왜 그런가**

- **`offsetTop` 은 네 줄 내내 `250`** 이고 `offsetLeft` 도 `120` 그대로다. **스크롤은 배치를 안 바꾸기 때문**이다. 바뀐 것은 「어디에 놓였나」가 아니라 「어디서 보고 있나」다.
- **조상 스크롤러를 100 굴리면 `rect.top` 이 100 줄고**(765 → 665), **창을 200 굴리면 또 200 준다**(665 → 465). **`rect` 는 조상 스크롤러와 창을 둘 다 반영**한다.
- **마지막 단계(`t.scrollTop = 50`)에서는 아무 칸도 안 바뀐다.** 자기 **안쪽 내용**을 민 것이라 **자기 상자는 그 자리에 있다.** `scrollTop` 은 다른 둘과 **묻는 것 자체가 다르다.**
- **`rect.top + scrollY` 는 `offsetTop` 이 아니다.**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-09-three.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '8,15p'
그래서 세 묶음의 기준점이 다르다
무엇을 재나               기준점        스크롤에 따라 변하나
getBoundingClientRect()   뷰포트        변한다 — 조상 스크롤러·창 둘 다
offsetTop / offsetLeft    offsetParent  안 변한다 — 배치가 바뀌어야 변한다
el.scrollTop              자기 내용     자기가 굴려질 때만 변한다

offsetParent = #inner   ·   window.scrollY = 200   ·   t.scrollTop 의 상한 = 255 (scrollHeight 300 - clientHeight 45)
rect.top + scrollY = 665.00   ← 창 스크롤만 되돌린 값이지 offsetTop 이 아니다 (offsetTop = 250)
(exit 0)
```

  665 는 **창 스크롤 200 만 되돌린 값**이고, `offsetTop` 은 250 이다. **가운데 낀 조상 스크롤러 100 과 `offsetParent` 위쪽의 거리는 그 셈에 안 들어 있다.**
- 덤으로 **`t.scrollTop` 의 상한이 255** 인 것도 보인다 — `scrollHeight`(300) − `clientHeight`(45). **`clientHeight` 가 60 이 아닌 것**은 가로 스크롤바가 15px 을 먹었기 때문이다(정본: [CSS 23번 주제](../../languages/css/syntax/23-overflow-and-scroll-containers/2-summary.md)).

### 2. 중간 요소의 `position` 만 바꾸면 — 기준이 통째로 바뀐다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-09-parent.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,7p'
offsetParent 가 무엇이 되나 — 중간 요소 #b 의 position 만 바꿨다
무엇을 바꿨나                 c.offsetParent      c.offsetTop   c.offsetLeft
#b 를 position: static        BODY                95            15
#b 를 position: relative      #b                  5             5
#b 를 position: absolute      #b                  5             5
#b 를 position: fixed         #b                  5             5
#b 를 position: sticky        #b                  5             5
(exit 0)
```

**왜 그런가**

- **다섯 중 갈리는 것은 두 가지뿐**이다 — `static` 이냐 아니냐. `relative`·`absolute`·`fixed`·`sticky` 는 **넷 다 똑같이** `offsetParent` 가 된다.
- **`static` 이면 건너뛴다.** `#b` 를 지나 위로 올라가 **`BODY`** 에 닿았다. `offsetTop` 이 `95` 인 것은 `#a` 의 마진 60 + 패딩 10 + `#b` 의 마진 20 + 패딩 5 를 body 에서부터 잰 값이다.
- **`static` 이 아니면 그 자리에서 멈춘다.** 그래서 `offsetTop` 이 `5`(= `#b` 의 패딩)로 떨어진다.
- ★ **값이 바뀐 게 아니라 기준이 바뀐 것**이다. 같은 요소가 같은 자리에 있는데 **`95` 와 `5`** 로 갈린다.
- **그래서 `offsetTop` 을 쓰기 전에 할 일은 하나다 — `offsetParent` 가 누구인지 같이 읽는 것.** 그러지 않으면 **CSS 한 줄에 JS 가 조용히 틀린다.**

### 3. `offsetParent` 가 `null` 이 되는 자리 — 「기준이 없는데 값은 있다」

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-09-parent.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '9,18p'
자기 자신과 조상의 사정으로 null 이 되는 자리
무엇을 했나                   c.offsetParent      c.offsetTop   c.offsetWidth
#c 자신을 position: fixed     null                95            80
조상 #a 를 display: none      null                0             0
트리에 안 붙인 요소           null                0             0
document.body                 null                0             1000
document.documentElement      null                0             1000

★ offsetTop 은 「문서 위에서부터」가 아니라 「offsetParent 위에서부터」다 —
  위 표의 첫 줄과 둘째 줄이 같은 요소의 같은 위치인데 95 와 5 로 갈린다.
(exit 0)
```

**왜 그런가**

- **자기 자신이 `fixed`** 면 `offsetParent` 가 `null` 인데 **`offsetTop` 은 95 로 값이 나온다.** 이때의 기준은 **초기 포함 블록**이다 — 「기준이 없다」가 아니라 「기준이 요소가 아니다」다.
- **조상이 `display: none`** 이면 `null` 이고 **치수도 0** 이다. 상자 자체가 안 만들어진다.
- **트리에 안 붙인 요소**도 같다([08번 주제](../08-getcomputedstyle/2-summary.md)의 「트리 밖은 침묵한다」와 같은 자리).
- ★ **`body` 와 `documentElement` 가 `null`** 이라는 사실이 **`while (e.offsetParent) { … }` 반복문을 성립시킨다** — 문서 좌표를 구하려고 `offsetTop` 을 누적해 올라갈 때 **body 에서 자연히 멈춘다.** A9 의 누적 셈이 이것 위에 서 있다.

### 4. 세 계열이 각각 어느 칸을 재나 — 이름이 아니라 칸을 외운다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-09-box.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,9p'
세 묶음이 각각 어느 칸을 재나 — 같은 .box 에 테두리 5 · 패딩 10 · 내용 200x60
무엇을                  offsetW    clientW    scrollW    offsetH    rect.width   rect.height
#plain                  230        220        220        90         230.00       90.00
#sc                     230        205        420        90         230.00       90.00
#tr                     230        220        220        90         460.00       180.00
#rot                    230        220        220        90         226.27       226.27
#frac                   111        107        107        51         111.19       50.98
#gone                   0          0          0          0          0.00         0.00
트리 밖                 0          0          0          0          0.00         0.00
(exit 0)
```

**왜 그런가**

- `.box` 는 **내용 200×60 · 패딩 10 · 테두리 5** 다.
  - **`offsetWidth` = 230** — 테두리 상자(200 + 패딩 20 + 테두리 10).
  - **`clientWidth` = 220** — 패딩 상자(200 + 20). **테두리는 빠진다.**
  - **`scrollWidth` = 220** — 넘치는 내용이 없으면 `clientWidth` 와 같다.
  - **`rect.width` = 230.00** — `offsetWidth` 와 **같은 칸**이다.
- **`#sc` 만 `clientWidth` 가 205** 다 — **세로 스크롤바가 15px** 을 먹었다. `scrollWidth` 는 **420**(넘치는 내용 400 + 패딩 20)으로 뛴다.
- **마진은 어느 값에도 안 들어 있다**(정본: [CSS 15번 주제](../../languages/css/syntax/15-box-model-and-box-sizing/2-summary.md)).
- **`#gone`(`display: none`)과 트리 밖은 전부 0** 이다 — A8 이 그 이야기다.

### 5. 같은 상자를 잰 두 수의 눈금 — 한쪽만 정수다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-09-box.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '11,18p'
정수인가 소수인가 — #frac 은 width 100.6 · padding 3.3 · border 2.2
  offsetWidth = 111   (Number.isInteger = true)
  rect.width  = 111.1875   (같은 상자를 잰 값이다)
  offsetTop   = 401   rect.top = 400.59375

transform 은 어느 쪽에 섞이나
  #tr  scale(2)      offsetWidth = 230   rect.width = 460.00
  #rot rotate(45deg) offsetWidth = 230   rect.width = 226.27   rect.left = 9.86 (축 정렬 외접 상자다)
(exit 0)
```

**왜 그런가**

- **`offsetWidth` 는 `111`, `rect.width` 는 `111.1875`** 다. **명세가 그렇게 정했다** — CSSOM View 가 `offset*` 계열을 **`long`**(정수)으로 정의하고 `DOMRect` 를 **`double`** 로 정의한다. 구현의 변덕이 아니다.
- **`offsetTop` 은 `401`, `rect.top` 은 `400.59375`** 다. **반올림된 쪽이 더 크다.** 다른 자리에서는 반대로 작아질 수 있다.
- ★ **두 계열을 섞어 빼면 1px 이 조용히 생기거나 사라진다.** 간격·정렬처럼 뺄셈이 들어가는 계산은 **`rect` 로만** 한다.
- **`111.1875` 는 1/16 단위**다. Blink 가 레이아웃을 1/64px 단위의 정수로 셈하기 때문인데, **그 자릿수는 구현의 사정이지 명세의 보장이 아니다.**

### 6. `transform` 을 주면 — `rect` 에만 섞인다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-09-box.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '20,27p'
상자 하나가 아닌 것 — 줄을 넘긴 인라인
  getClientRects().length = 3   getBoundingClientRect().height = 60.00   (첫 조각 높이 = 20.00)
  .box 하나는 getClientRects().length = 1

돌려받는 객체
  타입 = [object DOMRect]   두 번 부르면 === ? false
  JSON.stringify = {"x":8,"y":8,"width":230,"height":90,"top":8,"right":238,"bottom":98,"left":8}
  마진을 바꾼 뒤 붙들고 있던 옛 객체의 left = 8.00   새로 부른 것의 left = 100.00  ← 스냅숏이다
(exit 0)
```

**왜 그런가**

- **`scale(2)` 인데 `offsetWidth` 는 230 그대로**이고 **`rect.width` 는 460.00** 이다. **`transform` 은 레이아웃을 바꾸지 않고 그리는 단계에서만 작용**하기 때문이다(정본: [CSS 54번 주제](../../languages/css/syntax/54-transform-2d-and-origin/2-summary.md)). `offset*` 은 **레이아웃이 정한 상자**를 읽으므로 변환 전 값이다.
- **`rotate(45deg)` 의 `rect.width` 는 226.27** 이다. 이것은 **기울어진 상자의 변 길이가 아니라 축 정렬 외접 상자**의 폭이다 — 돌아간 테두리 상자를 **가로·세로에 나란한 사각형 하나로 감싼 값**이라 폭과 높이가 둘 다 226.27 로 같아졌다. `offsetWidth` 는 여전히 230 이다.
- 같은 블록의 마지막 줄들이 A7 의 근거이기도 하다.

### 7. 상자가 하나가 아닌 것 — 조각이 여럿이고, 돌려받은 것은 스냅숏이다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-09-box.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '20,27p'
상자 하나가 아닌 것 — 줄을 넘긴 인라인
  getClientRects().length = 3   getBoundingClientRect().height = 60.00   (첫 조각 높이 = 20.00)
  .box 하나는 getClientRects().length = 1

돌려받는 객체
  타입 = [object DOMRect]   두 번 부르면 === ? false
  JSON.stringify = {"x":8,"y":8,"width":230,"height":90,"top":8,"right":238,"bottom":98,"left":8}
  마진을 바꾼 뒤 붙들고 있던 옛 객체의 left = 8.00   새로 부른 것의 left = 100.00  ← 스냅숏이다
(exit 0)
```

**왜 그런가**

- **줄을 넘긴 인라인 요소는 `getClientRects().length` 가 3** 이다 — 세 줄이면 조각 셋이다. **보통 블록 상자는 1** 이다.
- **`getBoundingClientRect()` 는 그 조각들을 전부 감싸는 사각형 하나**를 준다(높이 60 = 20 × 3). **조각 하나의 높이는 20** 이다.
- **돌려받은 `DOMRect` 는 스냅숏**이다. 마진을 100px 로 바꿔도 **붙들고 있던 옛 객체는 `8.00` 그대로**이고 **새로 부른 것만 `100.00`** 이다.
- ★ **[08번 주제](../08-getcomputedstyle/2-summary.md)의 계산값 객체와 정반대**다. 그쪽은 **객체가 매번 새것인데 값은 라이브**였고, 여기는 **객체도 새것이고 값도 그때의 사진**이다. 두 API 를 같은 감각으로 쓰면 틀린다.
- `getBoundingClientRect()` 를 두 번 불러 `===` 로 견주면 **`false`** 다 — 매번 새 객체다.

### 8. `display: none` 과 트리 밖 — 기하에서는 둘이 같다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-09-box.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,9p'
세 묶음이 각각 어느 칸을 재나 — 같은 .box 에 테두리 5 · 패딩 10 · 내용 200x60
무엇을                  offsetW    clientW    scrollW    offsetH    rect.width   rect.height
#plain                  230        220        220        90         230.00       90.00
#sc                     230        205        420        90         230.00       90.00
#tr                     230        220        220        90         460.00       180.00
#rot                    230        220        220        90         226.27       226.27
#frac                   111        107        107        51         111.19       50.98
#gone                   0          0          0          0          0.00         0.00
트리 밖                 0          0          0          0          0.00         0.00
(exit 0)
```

**왜 그런가**

- **`#gone` 과 트리 밖이 둘 다 전부 0** 이다 — `offsetWidth`·`clientWidth`·`scrollWidth`·`offsetHeight`·`rect.width`·`rect.height` 가 모두 0 이고, `rect` 의 `top`/`left` 도 0 이다.
- ★ **[08번 주제](../08-getcomputedstyle/2-summary.md)에서는 둘이 갈렸다.** 거기서 `display: none` 은 **계산값을 대답했고**(`width` 가 `"200px"` 로 선언 그대로 남았다) 트리 밖만 **빈 문자열로 침묵**했다.
- **한 문장으로** — **계산값은 「무엇이 선언됐나」라서 상자가 없어도 대답할 수 있고, 기하는 「어떤 상자가 놓였나」라서 상자가 없으면 대답할 것이 없다.**
- 그래서 **「이 요소 지금 얼마나 크지?」를 계산값으로 물으면 숨긴 요소도 200px 이라고 답한다.** 기하로 물어야 0 이 나온다.

### 9. 읽은 좌표를 도로 넣어 보면 — 스크롤이 0 이면 틀린 좌표도 맞아 보인다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-09-point.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,8p'
창 ④ — 좌표를 읽지 말고 그 좌표로 되물어 본다
스크롤 상태     scrollY   rect.top    offset 누적   rect 중심으로 물으면  offset 좌표로 물으면
스크롤 전       0         320.00      320           #t                    #t
scrollY = 250   250       70.00       320           #t                    #tail

두 좌표가 스크롤 전에는 같은 요소를 가리키고, 250 을 굴리자 갈린다.
elementFromPoint 가 받는 것은 뷰포트 좌표이기 때문이다 — offset 누적값은 문서 좌표다.
되돌리려면 빼 준다: elementFromPoint(누적x - scrollX, 누적y - scrollY) = #t
(exit 0)
```

**왜 그런가**

- **스크롤 전에는 두 좌표가 똑같이 `#t`** 를 가리킨다. `rect.top`(320.00)과 offset 누적값(320)이 **우연히 같은 수**이기 때문이다. **여기서 멈추면 틀린 코드가 통과한다.**
- **250 을 굴리자 갈린다** — `rect` 중심은 여전히 `#t` 인데 **offset 누적 좌표는 `#tail`** 을 가리킨다. `elementFromPoint` 가 받는 것은 **뷰포트 좌표**이고 offset 누적값은 **문서 좌표**라서, 굴린 만큼 어긋났다.
- **빼 주면 다시 맞는다** — `elementFromPoint(누적x − scrollX, 누적y − scrollY)` 가 `#t` 다.
- **뷰포트 밖을 물으면 `null`** 이다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-09-point.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '10,13p'
뷰포트 밖을 물으면 — 스크롤해서 화면에서 사라진 자리
  scrollY = 0 일 때 t 의 rect.top = 320.00 → 뷰포트 높이 713 안인가: true
  scrollY = 1200 일 때 rect.top = -880.00 (음수다) · elementFromPoint(그 점) = null
  그런데 offset 누적값은 320 으로 한 글자도 안 변했다.
(exit 0)
```

  같은 순간에 **offset 누적값은 320 그대로**다. **「화면에서 사라졌나」를 `offsetTop` 으로는 영영 못 묻는다.**
- ★ **이 창이 앞의 세 창과 다른 점** — 앞의 셋은 전부 **값을 읽는다.** 읽기만 하면 **두 수가 같은지 다른지**밖에 모른다. 이 창은 **좌표를 쓴다** — 틀린 원점의 수를 넣으면 **엉뚱한 요소가 나와서** 무엇을 가리키는 수인지가 드러난다.

### 10. 왜 창 ④ 가 `elementFromPoint` 인가

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-09-tree.html 2>/dev/null | sed -n '4,5p'
<style>#t { margin-left: 40px; width: 120px; height: 30px }</style>
</head><body><div id="t">좌표를 잰 상자</div>
(exit 0)
```

**왜 그런가**

- **창 ① 은 이 주제에서 아무것도 못 본다.** 좌표를 읽어도 **트리에 자국이 안 남고**, 트리에는 `margin-left: 40px` 이라는 **선언의 글자**만 있다. **「그래서 몇 px 에 놓였나」는 창 ① 로 영영 못 묻는다.**
- **[08번 주제](../08-getcomputedstyle/2-summary.md)의 창 ④ 가 바로 이 주제**였다 — 거기서는 `getBoundingClientRect()` 를 **판정 도구로 빌려 썼고**(계산값이 `"200px"` 인데 상자는 230/200/460 이라는 것), 여기서는 그 도구 자체가 주인공이다. **그래서 그것을 검사할 창이 또 필요해졌다.**
- **이 주제에서 부적용인 창은 시간 측정**이다. 08 이 창 ⑤ 로 빌려 썼던 `performance.now()` 9판 중앙값을 여기서는 **안 쓴다** — 재지 않는 것이지 못 재는 것이 아니고, 그 값은 [10번 주제](../10-layout-thrashing/2-summary.md)가 잰다.
- **「읽기만 하는 창」의 한계** — **읽은 수가 어느 원점의 것인지는 수만 봐서는 모른다.** 원점이 겹치는 상태(스크롤 0)에서는 셋이 같은 수를 주기 때문이다.

### 11. 좌표를 옮기려면 — 한 줄 식과 그 식이 깨지는 자리

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-09-three.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '8,15p'
그래서 세 묶음의 기준점이 다르다
무엇을 재나               기준점        스크롤에 따라 변하나
getBoundingClientRect()   뷰포트        변한다 — 조상 스크롤러·창 둘 다
offsetTop / offsetLeft    offsetParent  안 변한다 — 배치가 바뀌어야 변한다
el.scrollTop              자기 내용     자기가 굴려질 때만 변한다

offsetParent = #inner   ·   window.scrollY = 200   ·   t.scrollTop 의 상한 = 255 (scrollHeight 300 - clientHeight 45)
rect.top + scrollY = 665.00   ← 창 스크롤만 되돌린 값이지 offsetTop 이 아니다 (offsetTop = 250)
(exit 0)
```

**왜 그런가**

- **뷰포트 → 문서** 는 `rect.top + window.scrollY` 다. 되돌리려면 빼면 된다.
- ★ **그 식은 「창 말고 다른 스크롤러가 없을 때」만 성립한다.** 위 출력의 마지막 줄이 반례다 — 조상 스크롤러를 100 굴린 상태에서 `rect.top + scrollY` 는 **665** 이고 `offsetTop` 은 **250** 이다. **중간 스크롤러의 오프셋은 그 식에 안 들어 있다.** 조상이 여럿이면 `offsetParent` 사슬을 타고 `offsetTop` 을 누적하는 쪽(A9 의 둘째 줄)이 **문서 좌표**다.
- **「화면에 보이나」를 이 주제의 값으로 판정하면 부족하다** — `offsetWidth > 0` 은 `display: none` 만 잡는다. **뷰포트 밖·`opacity: 0`·조상에 가려진 것**은 못 잡는다. 정본은 [목록의 **35번 주제**](../35-intersection-observer/)(IntersectionObserver)이고, 「보이나」 한 번 판정은 `el.checkVisibility()` 다.
- **[10번 주제](../10-layout-thrashing/2-summary.md)와의 이음매** — 이 문서의 **모든 읽기가 강제 동기 레이아웃의 방아쇠**다. 실제로 그 주제의 실측표에서 `offsetTop`·`getBoundingClientRect()`·`offsetParent`·`scrollTop` 이 전부 **한 번 읽는 데 100µs 대**로 나왔고, `elementFromPoint` 는 **그보다 세 배 비쌌다.** 여기서 배운 읽기를 **루프 안에서 쓰는 순간** 그 주제가 시작된다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · **`--window-size=1000,800`**(뷰포트 1000×713). **엔진은 이것 하나다.** **크로스 브라우저 이식성은 이 문서의 주장 범위 밖**이다.

★ **창 크기를 배너에 박은 이유** — 이 주제는 절대 좌표를 싣는다. 기본 창(780×493)에서 돌리면 **가로 방향 수치가 전부 달라진다.** 배너대로 던져야 같은 글자가 나온다.\
★ **시간은 재지 않았다.** 「이 읽기가 비싸다」는 [10번 주제](../10-layout-thrashing/2-summary.md)의 실측을 인용한 것이고 여기서 다시 재지 않았다.

**하네스** — 01\~08 과 같은 것을 쓴다. 블록은 `capture.sh` 가 전부 파일로 받았고 사람이 옮겨 적지 않았다.

```bash
# 블록 하나를 다시 던지는 법
google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 \
  --dump-dom wa09b-09-three.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
```

```js
// 이 주제의 창 ④ — 읽은 좌표를 도로 넣어 본다
const r = el.getBoundingClientRect();
document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
// 문서 좌표는 offsetParent 사슬을 타고 누적한다 (body 에서 자연히 멈춘다)
let y = 0, e = el; while (e.offsetParent) { y += e.offsetTop; e = e.offsetParent; }
// 한글 칸 정렬은 JS 안에서 2폭 padw 로 한다. padEnd 는 UTF-16 단위라 어긋난다.
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
```

★ **`--virtual-time-budget` 은 쓰지 않았다**(이 갈래의 정본 규칙).\
★ **`--dump-dom` 은 `load` + `setTimeout(…, 0)` 까지만 기다린다.** 이 주제의 실험은 전부 **파싱 직후 동기**로 끝나므로 그 한계에 안 걸린다.\
★ **출력은 `<pre>` 가 아니라 `<script type="text/plain">` 에 담아 마커로 잘랐다.**

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 세 묶음 × 스크롤 4단계 | 3 | 동작 방식 (2)(3) · A1 · A11 |
| `offsetParent` — 중간 요소 `position` 5종 | 3 | 동작 방식 (4) · A2 |
| `offsetParent` 가 `null` 이 되는 5가지 | 3 | 동작 방식 (5) · A3 |
| 세 계열 × 7요소(스크롤러·변환·소수·숨김·트리 밖) | 3 | 동작 방식 (7) · A4 · A8 |
| 소수 폭·소수 위치의 두 눈금 | 3 | 동작 방식 (8) · A5 |
| `scale`·`rotate` · 인라인 조각 · 객체 스냅숏 | 3 | 동작 방식 (9) · A6 · A7 |
| 창 ④ — `elementFromPoint` 두 좌표 × 두 상태 | 3 | 동작 방식 (6) · A9 |
| 창 ④ — 뷰포트 밖 점 | 3 | 동작 방식 (6) · A9 |
| 창 ① — 좌표를 읽은 문서의 트리 | 2 | 동작 방식 (1) · A10 |
| `demo` 블록을 래퍼에 띄워 초기 상태 + 버튼 확인 | 1 | 동작 방식 (10)의 demo |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| **모든 절대 좌표** | 위 표 | **창 크기**에 달렸다. 배너의 `--window-size` 가 전제다 |
| 스크롤바가 먹는 폭 | **15px** | 플랫폼·설정에 달렸다. 겹침 스크롤바면 0 이다 |
| 소수의 자릿수 | `111.1875`(1/16) | Blink 의 레이아웃 단위. **명세는 소수라는 것까지만 정한다** |
| 인라인 조각의 폭·개수 | `getClientRects().length` = 3 | **글꼴 치수와 줄바꿈**에 달렸다. 결론은 「조각이 여럿이다」뿐 |
| `rotate(45deg)` 의 `226.27` | 위 출력 | 상자 치수에서 나온 값. 결론은 「외접 상자다」뿐 |
| `offsetParent` 판정 결과 | 위 출력 | **명세가 정한 절차**다. 값이 아니라 절차를 외운다 |

**안 돌려 본 것** — ① Firefox·Safari 에서의 재현(엔진이 없다). ② **`el.getBoxQuads()`** — 회전한 요소의 진짜 네 꼭짓점을 주는 Chromium 한정 API. **표면만 적었고 던지지 않았다.** ③ **`visualViewport`** — 이 판에서는 레이아웃 뷰포트와 시각 뷰포트가 같아 **갈라 볼 수 없었다**(못 잰 것). ④ **`el.checkVisibility()`** — A11 에서 정본으로 가리켰지만 **여기서 던지지 않았다**([08번 주제](../08-getcomputedstyle/2-summary.md)도 같다). ⑤ **`DOMRect` 의 `x`/`y` 가 `left`/`top` 과 갈리는 경우**(음수 폭) — 요소에서는 안 생겨 **만들어 보지 않았다.** ⑥ **디바이스 픽셀 비가 1 이 아닌 환경**에서의 반올림 — `devicePixelRatio` 가 1 인 판에서만 쟀다. ⑦ **쓰기 쪽**(`scrollTop` 에 대입하는 것)의 경계 — [11번 주제](../11-scroll-control/2-summary.md)의 몫이다.

## 용어 풀이

- **뷰포트(viewport)** — 지금 문서를 내다보는 창. `rect` 의 원점.
- **`offsetParent`** — `offsetTop`/`offsetLeft` 의 기준이 되는 조상. `position` 이 `static` 이 아닌 가장 가까운 조상, 없으면 `body`.
- **초기 포함 블록(initial containing block)** — 문서의 맨 바깥 기준 상자. `fixed` 요소의 좌표 기준.
- **테두리 상자(border box)** — 내용 + 패딩 + 테두리. `offsetWidth` 와 `rect.width` 가 재는 칸.
- **패딩 상자(padding box)** — 내용 + 패딩. `clientWidth` 가 재는 칸(스크롤바 제외).
- **`DOMRect`** — `getBoundingClientRect()` 의 반환값. **스냅숏**이고 매번 새 객체다.
- **축 정렬 외접 상자(axis-aligned bounding box)** — 기울어진 도형을 가로·세로에 나란한 사각형으로 감싼 것.
- **히트 테스트(hit testing)** — 어떤 점 위에 어느 요소가 있는지 찾는 일. `elementFromPoint` 가 한다.
- **강제 동기 레이아웃(forced synchronous layout)** — 읽기가 그 자리에서 레이아웃을 다시 계산하게 만드는 것([10번 주제](../10-layout-thrashing/2-summary.md)).
- **레이아웃 단위** — 엔진이 좌표를 셈하는 내부 눈금. Blink 는 1/64px 정수를 쓰고, 그래서 소수가 1/16 단위로 보인다.

# css/syntax/23 — 오버플로·스크롤 컨테이너·스크롤바 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 치수는 Google Chrome 151.0.7922.173 headless 에서 실제로 렌더해** `getComputedStyle`·`clientWidth`/`offsetWidth`/`scrollWidth`·`scrollTop` 대입으로 잰 값이다. 단위는 px 다.\
> ★ **잘림 여부는 좌표로 안 나오므로 스크린샷 픽셀 RGB 로 판정했다.**\
> **손으로 계산해 유도한 수치는 없다.** 규칙은 [CSS Overflow Level 3](https://drafts.csswg.org/css-overflow-3/)·[Level 4](https://drafts.csswg.org/css-overflow-4/) 로 접지했다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 다섯 값의 세 가지 성질

**실행 결과** (Chrome 151 headless — 200×80 상자(테두리 2), 내용 320×200)

```text
overflow   잘리나   scrollTop=200 → 실제   스크롤 컨테이너   clientWidth × clientHeight   offsetWidth
visible      ✗              0                  ✗                 200 × 80                 204
hidden       ✓            200                  ✓                 200 × 80                 204
clip         ✓              0                  ✗                 200 × 80                 204
auto         ✓            200                  ✓                 185 × 65                 204
scroll       ✓            200                  ✓                 185 × 65                 204
```

**잘리는가**

- **`visible` 만 안 잘린다.** 나머지 넷은 전부 잘린다.

**스크롤 컨테이너인가**

- **`hidden`·`auto`·`scroll` 이 ✓**, **`visible`·`clip` 이 ✗** 다.
- 판정은 `scrollTop = 200` 을 넣고 되읽는 것으로 했다.

**`clientWidth`**

- `visible`·`hidden`·`clip` — **200**(스크롤바가 자리를 안 먹는다).
- `auto`·`scroll` — **185**(15px 을 스크롤바가 먹었다).

**세 질문의 답이 모두 같은 값**

- **`auto` 와 `scroll`** 이다(잘림 ✓ · 컨테이너 ✓ · 스크롤바 ✓). 다만 `auto` 는 **넘칠 때만** 스크롤바가 생기고 `scroll` 은 **늘** 생긴다.
- ★ **`hidden` 은 셋의 답이 각각 다르다** — 잘리고, 컨테이너이고, 스크롤바는 없다. 이 어중간함이 이 주제의 모든 사고의 원인이다.

### 2. `hidden` 과 `clip` 을 가르는 한 줄

**실행 결과** (Chrome 151 headless)

```text
                  hidden    clip
scrollTop = 200     200       0
clientWidth         200      200
clientHeight         80       80
offsetWidth         204      204
scrollWidth         320      320
scrollHeight        200      200
```

**`hidden` 이면 출력**

- **200.** 대입이 먹었다.

**`clip` 이면**

- **0.** 대입이 무시된다.

**네 치수는 다른가**

- ★ **하나도 안 다르다.** `clientWidth`·`offsetWidth`·`scrollWidth`·`scrollHeight` 가 **전부 동일**했다.

**화면으로 구분할 수 있는가**

- ★★ **없다.** 스크린샷이 완전히 같다.
- **CSS 는 에러가 없는 언어**라 값을 잘못 골라도 아무 신호가 없는데, 이 자리는 **화면조차 신호를 안 준다.** 갈리는 유일한 창이 **`scrollTop` 대입**이다.

### 3. 한 축만 주면

**실행 결과** (Chrome 151 headless — 선언 대 계산값)

```text
선언                              계산 overflow-x   계산 overflow-y   clientWidth × clientHeight
x: hidden · y: visible               hidden            auto             185 × 80
x: visible · y: hidden               auto              hidden           200 × 65
x: scroll · y: visible               scroll            auto             185 × 65
x: clip   · y: visible               clip              visible          200 × 80
x: visible · y: clip                 visible           clip             200 × 80
x: hidden · y: clip                  hidden            hidden           200 × 80
```

**`.a` 의 `overflowY`**

- **`auto` 다.** 내가 `visible` 이라고 썼는데 다른 값이 나온다.
- 그 결과 **스크롤바까지 생겨** `clientWidth` 가 200 → **185** 로 줄었다.

**`.b` 의 `overflowY`**

- **`visible` 그대로다.** `clip` 과 `visible` 은 **짝이 맞는다.**

**`.c` 의 `overflowY`**

- **`hidden` 이다.** 내가 쓴 `clip` 이 **`hidden` 으로 바뀌었다.**

**왜 이 규칙이 있나**

- **한 축에서 잘라 놓고 다른 축으로는 삐져나오게 하면 그릴 수가 없기 때문**이다. 잘린 경계를 넘나드는 내용이 생긴다.
- 그래서 엔진이 `visible` 쪽을 **스크롤 가능한 값(`auto`)으로 승격**시킨다.
- **`clip` 과 `visible` 이 예외인 이유**는 둘 다 **스크롤 컨테이너가 아니라서** 섞여도 모순이 안 생기기 때문이다.

### 4. `hidden` 이 딸려 오게 하는 것

**실행 결과 ①** (Chrome 151 headless — 200px 패딩 뒤 버튼에 `focus()`)

```text
overflow   focus() 후 scrollTop
hidden            145
clip                0
```

**실행 결과 ②** (Chrome 151 headless — 바깥 `overflow: auto` 와 `sticky` 사이에 래퍼를 끼우고 `scrollTop = 200`)

```text
중간 래퍼의 overflow   머리 top(스크롤러 기준)
visible                       2.0     붙는다
clip                          2.0     붙는다
hidden                     -198.0     죽는다
auto                       -198.0     죽는다
```

**포커스를 받으면**

- **상자가 혼자 스크롤된다**(실측 `scrollTop` **145**). 화면이 어긋나는데 **CSS 어디를 봐도 원인이 안 보인다.**
- `clip` 은 **0 그대로**다.

**자손의 `sticky`**

- **죽는다**(실측 **−198.0** — 머리가 내용과 함께 밀려 올라갔다).
- `hidden` 상자가 **가장 가까운 스크롤 컨테이너**가 되어 `sticky` 를 가로채는데, 정작 그 상자는 스크롤되지 않기 때문이다.

**BFC 는 열리는가**

- **열린다.** 정본은 [17번 주제](../17-block-formatting-context/2-summary.md)이고, 거기서 **`clip` 만 BFC 가 아님**을 실측했다.

**`clip` 으로 바꾸면**

- ★ **셋 다 사라진다.** `clip` 은 스크롤 컨테이너가 아니므로 ①②가 없고, 그래서 ③(BFC)도 없다.
- **하나의 원인이 세 증상을 만들었던 것**이다 — 스크롤 컨테이너가 되느냐.

### 5. 스크롤바가 먹는 자리

**실행 결과** (Chrome 151 headless — `overflow: auto`, 200×60 상자(테두리 2))

```text
scrollbar-gutter   내용이 짧을 때   내용이 길 때   자식 폭
auto (기본)          client 200      client 185     200 → 185  (15px 튄다)
stable               client 185      client 185     185 → 185  (안 튄다)
stable both-edges    client 170      client 170     170 → 170  (양쪽 15씩)

offsetWidth 는 네 경우 전부 204 로 동일
```

**안 넘칠 때**

- `clientWidth` **200** · `offsetWidth` **204**(테두리 2+2).

**넘칠 때**

- `clientWidth` **185** · `offsetWidth` **204**.
- ★ **`offsetWidth` 는 안 바뀐다.** 스크롤바는 **패딩 상자 안쪽**을 먹는다([15번](../15-box-model-and-box-sizing/2-summary.md)의 두 칸 정의가 여기서 갈린다).

**레이아웃에서 어떻게 드러나나**

- **자식 폭이 200 에서 185 로 갑자기 줄어든다**(실측). 목록에 항목이 하나 더 쌓이는 순간 **글줄이 통째로 다시 흐른다.**

**`scrollbar-gutter: stable` 이면**

- **두 경우 다 185 다.** 흔들림이 없어진다.
- 대가는 **늘 15px 을 잃는 것**이다. `both-edges` 면 **170**(양쪽 15씩).

### 6. `clip` 에만 있는 것

**실행 결과** (Chrome 151 headless — 150×50 상자(테두리 2), 내용 300×150, 스크린샷 픽셀)

```text
선언                                      테두리 밖 10px   테두리 밖 25px
overflow: hidden                          (255,255,255)    (255,255,255)
overflow: clip; overflow-clip-margin:20px (124, 58,237)    (255,255,255)
```

**`overflow-clip-margin` 이 하는 일**

- **자르는 경계를 바깥으로 밀어 준다.** 「자르되 이만큼은 넘쳐도 된다」는 여유다.
- 실측에서 테두리 밖 **10px 지점이 보라**(안 잘림), **25px 지점은 흰색**(잘림)이었다 — 여유 20px 이 정확히 적용됐다.

**`hidden` 에 주면**

- **아무 일도 안 일어난다.** `overflow-clip-margin` 은 **`clip` 일 때만** 뜻이 있다 — 에러도 경고도 없다.

**실무 상황**

- **그림자·포커스 링이 살짝 삐져나오는 카드.** 안쪽 내용은 잘라야 하는데 그림자까지 잘리면 어색하다.

**`clip` 을 쓰면 잃는 것**

- **스크롤 능력**이다. 나중에 「여기 스크롤되게 해 주세요」가 오면 값을 바꿔야 한다.
- **BFC 도 안 열린다** — 그게 필요하면 `display: flow-root` 를 따로 준다([17번](../17-block-formatting-context/2-summary.md)).

### 7. 「사라졌다」를 가르기

**원인 후보 둘**

- **① 잘렸다** — 조상의 `overflow` 가 `visible` 이 아니다(이 주제).
- **② 가려졌다** — 다른 요소가 위에 그려졌다([22번](../22-stacking-context-and-z-index/2-summary.md)).

**화면으로 가르는 법**

- **일부만 네모지게 잘려 있으면 `overflow`** — 잘린 선이 **조상 상자의 경계와 일치**한다.
- **통째로 안 보이거나 다른 요소 모양대로 가려져 있으면 `z-index`** 다.

**`getBoundingClientRect()` 로 판정할 수 있는가**

- ★ **없다.** [17번](../17-block-formatting-context/2-summary.md) 실측에서 잘린 자식과 안 잘린 자식의 `rect` 가 **둘 다 240×34 로 완전히 같았다.**
- **잘림은 레이아웃이 아니라 페인트**이기 때문이다.

**그러면 무엇으로 재나**

- **스크린샷 픽셀**이다. [22번](../22-stacking-context-and-z-index/2-summary.md)의 겹침 판정과 같은 도구이고, 이 주제에서도 6번의 `overflow-clip-margin` 을 그렇게 쟀다.

### 8. `sticky` 를 살리는 처방

**왜 안 붙나**

- 가운데 `overflow: hidden` 래퍼가 **스크롤 컨테이너**가 되어 `sticky` 를 **가로챘다.**
- `sticky` 는 **가장 가까운 스크롤 컨테이너**에 걸리는데, 그 래퍼 자신은 스크롤되지 않으므로 **걸릴 순간이 영영 안 온다.**
- 실측 — 머리가 스크롤러 기준 **−198.0**, 곧 내용과 함께 통째로 밀려 올라갔다.

**한 글자만 고치는 법**

- **`hidden` → `clip`.**

**동작하는 이유**

- **`clip` 은 스크롤 컨테이너가 아니다.** 그래서 `sticky` 가 그 래퍼를 건너뛰고 **바깥 `overflow: auto` 스크롤러**에 걸린다.
- 실측 — `clip` 일 때 머리가 **2.0**(스크롤러 위끝 + 테두리 2)에 고정됐다.

**`sticky` 의 정본**

- [21번 주제](../21-position-and-containing-block/2-summary.md)(`position` 과 포함 블록)다.

### 9. 목적에 맞는 값 고르기

**자르기만 하면 된다**

- **`overflow: clip`.** 부작용 셋이 없다.

**BFC 만 필요하다**

- **`display: flow-root`.** `overflow` 를 쓰면 **잘림·스크롤 컨테이너가 덤으로** 따라온다.
- 정본은 [17번](../17-block-formatting-context/2-summary.md)이고, 거기 결론이 「**BFC 가 목적이면 `flow-root`**」다.

**스크롤은 되되 레이아웃은 안 튀게**

- **`overflow: auto` + `scrollbar-gutter: stable`.**

**`hidden` 이 어중간한 이유**

- **셋의 답이 다 다르다** — 자르고(✓), 스크롤 컨테이너이고(✓), 스크롤바는 없다(✗).
- 그래서 **자르려는 사람에게는 부작용이 붙고, 스크롤하려는 사람에게는 손잡이가 없다.** 어느 쪽도 정확히 원하는 값이 아니다.
- **자르기는 `clip`, 스크롤은 `auto`** 로 갈라 쓰면 `hidden` 을 쓸 일이 거의 없다.

### 10. 다른 주제로 잇기

**쌓임 맥락을 만드는가**

- ★ **안 만든다**(실측 — `overflow: hidden` 래퍼의 겹침 픽셀이 **(255,0,0) 빨강**이었다. 담장이 생겼다면 파랑이어야 한다).
- 정본은 [22번 주제](../22-stacking-context-and-z-index/2-summary.md)다.
- **BFC 는 만들되 쌓임 맥락은 안 만드는** 대표 선언이라, 셋을 한 덩어리로 외우면 여기서 깨진다.

**`clientWidth` 와 `offsetWidth`**

- [15번 주제](../15-box-model-and-box-sizing/2-summary.md)(박스 모델)다. `clientWidth` 는 **패딩 상자**, `offsetWidth` 는 **테두리 상자**를 잰다.
- 이 주제는 거기에 「**스크롤바가 패딩 상자 안쪽을 먹는다**」를 하나 더 얹는다.

**`clip` 이 BFC 를 안 여는 이유**

- **스크롤 컨테이너를 안 만들기 때문**이다. 안쪽을 스크롤하려면 안쪽이 독립된 구역이어야 하는데, 스크롤할 일이 없으면 독립시킬 이유도 없다.
- [17번](../17-block-formatting-context/2-summary.md)이 「`overflow` 가 `visible` 이 아니면 BFC」라는 흔한 요약이 깨지는 자리로 적어 둔 것이 이것이고, 이 주제의 (1) 표가 **그 이유**를 보여 준다.

**스크롤 스냅과 `overscroll-behavior`**

- **이 편에서 다루지 않는다.** [목록의 **59번 주제**](../59-view-transitions/)(스크롤 연동 애니메이션) 쪽이다. 여기서는 **이름만** 적었다.

## 용어 풀이

- **스크롤 컨테이너(scroll container)** — 안쪽을 스크롤할 수 있는 상자. **스크롤바가 보이느냐와는 별개**다.
- **스크롤포트(scrollport)** — 스크롤 컨테이너에서 내용이 보이는 칸. `clientWidth`/`clientHeight` 가 재는 칸.
- **잘림(clipping)** — 넘친 부분이 안 그려지는 것. **레이아웃이 아니라 페인트**라 `rect` 로는 안 보인다.
- **`visible`** — 기본값. 안 자르고 안 스크롤한다.
- **`hidden`** — 자르고 **스크롤 컨테이너를 만든다.** 스크롤바는 없다. **어중간한 값.**
- **`clip`** — 자르기만 한다. 스크롤 컨테이너도 BFC 도 아니다.
- **`auto`** — 넘칠 때만 스크롤바. 그때 `clientWidth` 가 줄어든다.
- **`scroll`** — 넘치든 말든 스크롤바 자리를 늘 먹는다.
- **`overflow-clip-margin`** — `clip` 에서 「이만큼은 넘쳐도 된다」는 여유. **`hidden` 에는 없다.**
- **`scrollbar-gutter`** — 스크롤바 자리를 미리 비워 두는 속성. 레이아웃 흔들림을 막는다.
- **포커스 스크롤(focus scrolling)** — 포커스 받은 요소를 보이게 하려고 브라우저가 스크롤 컨테이너를 굴리는 것. **`hidden` 에서도 일어난다.**

## 실행 검증

| 무엇을 | 어떻게 | 결과 |
|---|---|---|
| 다섯 값의 세 성질 | Chrome 151 headless · `scrollTop=200` 대입 + `clientWidth` | `hidden` **200** / `clip` **0** · `auto`·`scroll` 만 client 185 |
| `hidden` 대 `clip` 전수 비교 | `client`·`offset`·`scrollWidth`·`scrollHeight` 네 값 | **전부 동일** — `scrollTop` 대입에서만 갈림 |
| 한 축 규칙 | 6조합의 `getComputedStyle().overflowX/Y` | `visible` → **`auto`** 승격 · `clip`+`hidden` → **`hidden`** · `clip`+`visible` 은 그대로 |
| 승격의 부작용 | 같은 조합의 `clientWidth` | `x:hidden;y:visible` 이 200 → **185** (스크롤바가 생김) |
| 포커스 스크롤 | 200px 패딩 뒤 버튼에 `focus()` | `hidden` **145** / `clip` **0** |
| `sticky` 가로채기 | 중간 래퍼 `overflow` 4값 × `scrollTop=200` | `hidden`·`auto` **−198** / `visible`·`clip` **2.0** |
| 스크롤바 폭 | `clientWidth` 대 `offsetWidth` | **185 대 204** — 15px, `offsetWidth` 는 불변 |
| `scrollbar-gutter` | 짧은 내용 / 긴 내용 × `auto`·`stable`·`both-edges` | `auto` **200↔185 튐** · `stable` **185 고정** · `both-edges` **170** |
| `overflow-clip-margin` | 스크린샷 픽셀(테두리 밖 10px·25px) | `clip`+20px 는 **10px 보라 / 25px 흰색** · `hidden` 은 둘 다 흰색 |
| 쌓임 맥락 여부 | 겹침 픽셀([22번](../22-stacking-context-and-z-index/2-summary.md) 방식) | `overflow: hidden` **(255,0,0)** — 담장을 안 만든다 |
| demo 4개 | 완성 문서에서 `extract-demo-blocks.py --render` 재추출 + 스크린샷 픽셀 | 「보이는 것」 4건 모두 일치 |

**구현 의존 항목** — ★ **스크롤바 폭 15px 은 이 플랫폼의 값**이다. 겹침 스크롤바를 쓰는 환경에서는 **0** 이 되고, 그러면 `scrollbar-gutter: stable` 도 아무 자리를 안 비운다. **이 문서의 185·170 은 전부 그 15 에서 나온 값**이다.\
★ **포커스 스크롤의 양(145)은 브라우저가 정한다.** 「스크롤이 일어난다」는 재현되지만 **얼마나 굴리느냐는 이 판의 결과**다.\
**엔진은 Chrome 하나다.** Firefox 155.0.1 은 이 환경에서 headless 스크린샷이 산출되지 않고 WebKit 은 이 머신에 없다 — **「두 엔진에서 확인했다」고 적지 않았다.**

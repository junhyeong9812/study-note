# web-api/16 — 전파 3단계: 캡처·타깃·버블과 `target` 대 `currentTarget` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 받은 것**이다 — 클릭·포커스·마우스 이동은 **CDP 로 넣은 진짜 입력**이다. 명령은 블록마다 배너로 실려 있다.\
> 규칙은 [WHATWG DOM Standard — Events](https://dom.spec.whatwg.org/#events) 의 「dispatch」·「invoke」·「inner invoke」 절과 [HTML Standard](https://html.spec.whatwg.org/multipage/dom.html#the-document-object) 의 `Document` get the parent 문장으로 접지했다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**

**★ 이 편에는 흔들리는 칸이 없었다** — 세는 것이 호출 순서와 횟수뿐이고 시간을 안 잰다.

| 안 흔들리는 칸 | 흔들리는 칸 · 못 잰 칸 |
|---|---|
| 호출 순서표 14줄 · `eventPhase` · `target`/`currentTarget` · 비버블 격자 · 타깃 단계 순서 | **못 잰 것** — 디스패치에 걸리는 시간 |
| 합성과 진짜의 견줌 · 디스패치 도중 변경 | **부적용** — `--dump-dom` 트리(전파는 자국을 안 남긴다) |
| 캡처를 여러 판 돌려 **한 글자도 같았다** | Chrome 판 번호 |

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 열네 줄 — 내려가며 capture, 타깃에서 둘, 올라가며 bubble

**출력**

```text
$ python3 wa16b-cdp.py page wa16b-16-order.html | sed -n '1,16p'
가. 진짜 클릭 한 번 — 리스너가 불린 순서
#   currentTarget   등록     eventPhase          target    this===currentTarget
1   window          capture  1 CAPTURING_PHASE   #안쪽     true
2   document        capture  1 CAPTURING_PHASE   #안쪽     true
3   html            capture  1 CAPTURING_PHASE   #안쪽     true
4   body            capture  1 CAPTURING_PHASE   #안쪽     true
5   #바깥           capture  1 CAPTURING_PHASE   #안쪽     true
6   #가운데         capture  1 CAPTURING_PHASE   #안쪽     true
7   #안쪽           capture  2 AT_TARGET         #안쪽     true
8   #안쪽           bubble   2 AT_TARGET         #안쪽     true
9   #가운데         bubble   3 BUBBLING_PHASE    #안쪽     true
10  #바깥           bubble   3 BUBBLING_PHASE    #안쪽     true
11  body            bubble   3 BUBBLING_PHASE    #안쪽     true
12  html            bubble   3 BUBBLING_PHASE    #안쪽     true
13  document        bubble   3 BUBBLING_PHASE    #안쪽     true
14  window          bubble   3 BUBBLING_PHASE    #안쪽     true
(exit 0)
```

**왜 그런가**

- **열네 줄**이다(일곱 자리 × 두 단계).
- **1\~6** — `window`·`document`·`html`·`body`·`#바깥`·`#가운데` 의 **capture** 리스너, `eventPhase` **1**.
- **7\~8** — `#안쪽` 의 capture 와 bubble, **둘 다 `eventPhase` 2**. 타깃 자리에서는 「캡처 단계」도 「버블 단계」도 아니다.
- **9\~14** — `#가운데` 에서 `window` 까지 **bubble** 리스너, `eventPhase` **3**. 1\~6 을 정확히 뒤집은 순서다.
- **`target` 은 열네 줄 모두 `#안쪽`** 이다. 바뀌는 것은 `currentTarget` 과 `eventPhase` 둘뿐이다.
- **`this === e.currentTarget` 은 열네 줄 모두 `true`** — 보통 함수로 단 리스너의 `this` 는 **리스너를 단 자리**다.

### 2. B → D → A → C — 타깃에서도 capture 무리가 먼저다

**출력**

```text
$ python3 wa16b-cdp.py page wa16b-16-order.html | sed -n '26,28p'
나. 타깃 한 자리에 A(bubble) B(capture) C(bubble) D(capture) 순서로 등록하고 누르면
  new MouseEvent : 부모 p(capture, phase 1) → B(capture, phase 2) → D(capture, phase 2) → A(bubble, phase 2) → C(bubble, phase 2) → 부모 p(bubble, phase 3)
  진짜 클릭      : 부모 p(capture, phase 1) → B(capture, phase 2) → D(capture, phase 2) → A(bubble, phase 2) → C(bubble, phase 2) → 부모 p(bubble, phase 3)
(exit 0)
```

**왜 그런가**

- **부모(capture) → B → D → A → C → 부모(bubble)** 다. 합성과 진짜가 같다.
- **A·B·C·D 넷 다 `eventPhase` 2** 다.
- ★ **「타깃에서는 등록 순서」라는 설명과 맞지 않는다** — 등록 순서라면 A → B → C → D 였을 것이다.
- 명세의 dispatch 는 경로를 두 번 훑고(A9), 타깃 자리는 **1차에서 capture 만, 2차에서 나머지만** 부른다. 각 무리 안에서는 등록 순서다.

### 3. `target` 은 남고 `currentTarget` 은 `null`, `eventPhase` 는 0

**출력**

```text
$ python3 wa16b-cdp.py page wa16b-16-order.html | sed -n '23,24p'
디스패치가 끝난 뒤 붙들어 둔 이벤트 객체를 다시 읽으면
  e.target = #안쪽 · e.currentTarget = null · e.eventPhase = 0
(exit 0)
```

**왜 그런가**

- **`#안쪽` · `null` · `0`** 이다.
- 명세의 dispatch 마지막 단계가 **`eventPhase` 를 `NONE` 으로, `currentTarget` 을 `null` 로** 되돌린다. `target` 은 그대로 둔다.
- ★ **`await` 뒤의 `e.currentTarget` 은 `null`** 이다 — 리스너 첫 줄에서 `const 자리 = e.currentTarget` 으로 받아 둔다.

### 4. 갈리는 줄은 `bubbles: false` 인 다섯 줄이고, `load` 는 `window` 까지 안 간다

**출력**

```text
$ python3 wa16b-cdp.py page wa16b-16-nobubble.html
자식에서 난 이벤트를 부모·document·window 가 받았나 (받은 횟수)
이벤트      e.bubbles  자식 자신 부모 capture  부모 bubble  document capture  window capture
click       true       1         1             1            1                 1
focus       false      1         1             0            1                 1
blur        false      1         1             0            1                 1
focusin     true       1         1             1            1                 1
focusout    true       1         1             1            1                 1
mouseenter  false      1         1             0            1                 1
mouseover   true       1         1             1            1                 1
load        false      1         1             0            1                 0
scroll      false      1         1             0            1                 1

부모의 capture 칸과 bubble 칸이 갈린 줄 = 5 / 9
(exit 0)
```

**왜 그런가**

- **갈리는 줄은 `focus`·`blur`·`mouseenter`·`load`·`scroll` 다섯**이다(「5 / 9」). 공통점은 **`e.bubbles` 가 `false`** 라는 것 하나다 — 부모의 **capture 칸은 1, bubble 칸은 0** 이다.
- **올라오는 길이 없어도 내려가는 길은 지난다** — 그래서 부모의 capture 와 `document` 의 capture 가 받는다.
- 부모에서 `focus` 를 받는 두 방법 — **① `addEventListener('focus', f, true)`** · **② `focusin` 을 bubble 로.**
- ★ **`window capture` 칸은 아홉 줄이 모두 같지 않다** — **`load` 줄만 0** 이다. `document` 까지는 가고 `window` 로는 안 간다(A10).
- **자식 자신의 칸은 아홉 줄 모두 1** — 버블하지 않는 이벤트도 **타깃 자신의 bubble 리스너는 부른다**(A9).

### 5. 생성자 기본값은 `bubbles: false` — `new MouseEvent('click')` 도

**출력**

```text
$ python3 wa16b-cdp.py page wa16b-16-more.html | sed -n '1,5p'
가. 생성자로 만든 이벤트의 bubbles 기본값 — 부모의 bubble 리스너가 받나
만든 꼴                                     bubbles  부모 bubble 리스너
new CustomEvent(t)                          false    못 받음
new MouseEvent('click')                     false    못 받음
new MouseEvent('click', { bubbles: true })  true     받음
(exit 0)
```

**왜 그런가**

- **`new CustomEvent` 와 `new MouseEvent('click')` 은 부모가 못 받는다** — 둘 다 `bubbles` 가 `false` 다. `{ bubbles: true }` 를 준 것만 받는다.
- **사람의 진짜 클릭은 받는다** — 문항 1의 9\~14 줄이 그것이다.
- ★ **테스트 사고** — 합성 이벤트로 「부모는 안 받는다」를 확인한 테스트가 **실제 클릭에서는 부모가 받는다.** 반대로 부모 리스너를 시험하려면 `bubbles: true` 를 **명시**해야 한다.

### 6. 떼어 둔 나무에서는 경로가 거기서 끝나고, `e.target` 은 요소다

**출력**

```text
$ python3 wa16b-cdp.py page wa16b-16-more.html | sed -n '7,9p'
나. 문서에 안 붙은 나무에서 던지면 — 경로
  composedPath() = span → section
  (견줌) 문서 안의 #굵게 에서 던지면 composedPath() = #굵게 → #문단 → #부모 → body → html → document → window
(exit 0)
```

```text
$ python3 wa16b-cdp.py page wa16b-16-more.html | sed -n '11,13p'
다. 진짜 클릭 — 글자를 눌렀을 때 document 리스너가 본 target
  #문단 의 맨 앞 글자 위 → e.target = #문단 · e.currentTarget = document
  #굵게 의 한가운데     → e.target = #굵게 · e.currentTarget = document
(exit 0)
```

**왜 그런가**

- **떼어 둔 나무의 경로는 `span → section`** 뿐이다. 문서 안에서 던지면 **`body → html → document → window`** 가 더 붙는다.
- 경로는 디스패치가 시작될 때 **부모를 따라 올라가며** 만든다 — 붙어 있지 않으면 올라갈 곳이 없다.
- **「그냥 글자」 위 → `#문단`, 「굵은 글자」 위 → `#굵게`**. **텍스트 노드가 `target` 인 경우는 없었다** — 글자를 담은 가장 깊은 **요소**가 된다(이 판의 관찰).

### 7. 아직 안 지난 자리의 리스너는 불리고, 경로는 옛 조상 그대로다

**출력**

```text
$ python3 wa16b-cdp.py page wa16b-16-live.html
진짜 클릭 — 디스패치 도중에 바꾸면
가. capture@#바깥 이 #가운데 에 bubble 리스너를 더함 → bubble@#가운데 → 더한것@#가운데 → bubble@#바깥
나. capture@#안쪽 이 자기를 #다른곳 으로 옮김 · 지금 부모 = #다른곳 → bubble@#가운데 → bubble@#바깥
(exit 0)
```

**왜 그런가**

- ★ **가 — 불린다**(`더한것@#가운데`). 명세의 invoke 는 **자리에 도착할 때마다** 그 자리의 목록을 복사한다. `#가운데` 는 아직 복사 전이었다.
- **15번 주제의 결과와 함께 성립한다** — 그쪽은 **이미 복사가 끝난 같은 자리**에 더한 것이라 이번 판에 안 들어왔다. **「어느 자리의 목록을 언제 복사하나」가 둘을 가른다.**
- ★ **나 — 옛 조상**(`#가운데` → `#바깥`)을 지난다. 새 부모 `#다른곳` 은 안 불렸다. **경로는 디스패치 시작 때 한 번 만든다.**

### 8. 순서표는 같고 `isTrusted` 만 다르다 — 그래도 합성은 진짜가 아니다

**출력**

```text
$ python3 wa16b-cdp.py page wa16b-16-order.html | sed -n '18,21p'
같은 순서표를 세 가지로 던져 견준다
  줄 수 — 진짜 14 · new MouseEvent 14 · el.click() 14
  isTrusted — 진짜 true · new MouseEvent false · el.click() false
  세 판의 순서표가 갈린 줄 = 0 / 14
(exit 0)
```

**왜 그런가**

- **순서표가 갈린 줄 0 / 14** — 셋이 같은 경로를 같은 순서로 지났다.
- **반드시 다른 값은 `isTrusted`** — 진짜만 `true` 다.
- 「합성으로 테스트해도 된다」가 틀리는 자리 — **① 생성자의 `bubbles` 기본값이 `false`** 라 경로 자체가 짧아진다(A5). **② 그림자 경계에서 생성자의 `composed` 기본값이 `false`** 라 경계를 못 넘는다([12번 주제](../12-shadow-dom/3-answer.md)). 그 밖에 [14번 주제](../14-dialog-popover-scripting/3-answer.md)의 가벼운 닫기처럼 **합성으로는 아예 반응하지 않는** 동작도 있다.

### 9. 두 번 — 거꾸로 한 번(capturing), 바로 한 번(bubbling)

- **1차는 경로를 거꾸로**(`window` → 타깃) 훑으며 `"capturing"` 으로 부르고, **2차는 바로**(타깃 → `window`) 훑으며 `"bubbling"` 으로 부른다.
- inner invoke 가 거르는 두 줄 — **`"capturing"` 인데 리스너의 capture 가 `false` 면 건너뛰고, `"bubbling"` 인데 capture 가 `true` 면 건너뛴다.**
- 문항 2 — 타깃 자리는 1차에서 **B·D**(capture)만, 2차에서 **A·C** 만 불린다. 그래서 B → D → A → C 다.
- 버블하지 않는데 타깃 자신의 bubble 리스너가 불리는 이유 — **2차에서 `bubbles` 가 `false` 면 건너뛰는 것은 「타깃이 아닌 자리」뿐**이다. 타깃 자리는 `AT_TARGET` 으로 불린다.

### 10. `load` 면 `null` — 경로가 `document` 에서 끊긴다

- HTML 표준 — **`Document` 의 get the parent 는 이벤트 타입이 `"load"` 이거나 브라우징 맥락이 없으면 `null`, 아니면 문서의 전역 객체(`window`)** 를 돌려준다.
- 그 문장이 문항 4의 **`load` 줄 `window capture` = 0** 을 만든다.
- 막으려는 사고 — **그림의 `load` 가 `window` 의 `load` 리스너(페이지 로드용)를 부르는 것.** 페이지에 그림이 열 장이면 페이지 로드 처리가 열한 번 돈다.

### 11. 이 편의 질문은 「몇 번」이 아니라 「어느 순서로」이기 때문이다

- **창 ①이 부적용인 이유** — 전파는 트리에 자국을 안 남긴다. 누가 불렸는지는 트리에 없다.
- **15번 주제의 창 ④ 가 모자란 이유** — 횟수는 같아도 **순서·단계·자리**가 다를 수 있다. 문항 2는 네 리스너가 **다 한 번씩** 불리지만 순서가 답이다.
- **창 ③ 은 「같은 클릭을 세 가지로 던지기」로 바뀌었다** — **제5의 상태**(같은 질문을 다른 창으로 물었다)다.
- **`focus`·`mouseenter` 를 진짜 입력으로 일으킨 이유** — 그 둘은 **사람이 포커스를 옮기고 마우스를 움직여야** 나는 이벤트다. 합성으로 만들면 「`bubbles` 를 내가 준 대로」 나오므로 **브라우저가 정한 값**을 물은 것이 아니게 된다.

### 12. 다른 주제와 잇기

- **12번 주제와 함께 성립하는 이유** — 이 편의 「`target` 은 내내 같다」는 **경계가 없는 경로**의 이야기다. 그림자 경계가 있으면 명세의 invoke 가 **자리마다 `target` 을 그 자리에서 볼 수 있는 가장 가까운 것으로** 다시 정한다(재타기팅). 경계 안쪽만 보면 여전히 한 값이다.
- **17번 주제의 `stopPropagation`** 은 **경로의 다음 자리로 가는 것**을 끊는다. 명세의 invoke 가 그 자리의 리스너를 부르기 전에 「stop propagation 플래그가 서 있으면 돌아간다」를 본다.
- **18번 주제의 위임**은 **버블 단계**(3)에 기댄다. 문항 4의 격자는 **`bubbles: false` 인 다섯 가지는 조상의 bubble 리스너로 못 받는다**고 경고한다 — 위임은 capture 로 달거나 버블하는 짝을 써야 한다.
- **리스너의 `this`** 는 JS 07 의 네 규칙 중 **「호스트가 정하는 칸」** 이다 — DOM 이 `currentTarget` 을 `this` 로 넘겨 부른다(명세의 inner invoke 가 「callback this value」로 `currentTarget` 을 준다).

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800`. **엔진은 이것 하나다.** 크로스 브라우저 이식성은 이 문서의 주장 범위 밖이다.

★ **시간은 재지 않았다.**\
★ **진짜 입력은 CDP 로 넣었다** — `Input.dispatchMouseEvent`. 좌표는 매번 요소의 `getBoundingClientRect` 에서 계산했다. 하네스 전문은 [2-summary.md](2-summary.md)의 (1)에 있다.\
★ **포트는 `0`** 으로 띄우고 프로필의 `DevToolsActivePort` 를 읽는다 — 다른 작업의 브라우저와 겹치지 않는다. **자기 프로필로 띄운 프로세스만** 끝낸다.

```sh
# wa16b-16-rerun.sh
# 이 편의 블록을 다시 던지는 법 — 스크래치패드의 src 에서
# 진짜 입력(CDP) 페이지 — 하네스가 자기 프로필로 Chrome 을 띄우고 끝나면 치운다
python3 wa16b-cdp.py page wa16b-16-order.html
python3 wa16b-cdp.py page wa16b-16-nobubble.html
python3 wa16b-cdp.py page wa16b-16-more.html
python3 wa16b-cdp.py page wa16b-16-live.html
python3 wa16b-cdp.py page wa16b-16-same.html
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 호출 순서표 14줄 · 세 입력 견줌 · 디스패치 뒤 · 타깃 단계 순서 | 캡처 4판 | 동작 방식 (1)\~(3)·(6) · A1\~A3 · A8 |
| 비버블 격자 9줄(진짜 클릭·포커스·마우스 이동 + 로드·스크롤) | 캡처 4판 | 동작 방식 (4)·(5) · A4 · A10 |
| 생성자 `bubbles` · 떼어 둔 나무 · 글자 위 클릭 | 캡처 4판 | 동작 방식 (7) · A5 · A6 |
| 디스패치 도중 변경 둘 | 캡처 4판 | 동작 방식 (8) · A7 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| 글자를 눌렀을 때의 `e.target` | 요소 | 히트 테스트는 이 문서가 명세로 확인하지 않았다 |
| 합성과 진짜의 순서표가 같다 | 0 / 14 | **이 판의 관찰**이다 |
| 타깃에서 capture 무리가 먼저 | B → D → A → C | 명세 본문과 맞다. 옛 설명과 다르므로 판이 오르면 다시 찍는다 |

**안 돌려 본 것** — ① Firefox·Safari 에서의 재현(엔진이 없다). ② **포인터 이벤트**(`pointerdown` 등) — 목록의 **23번 주제** 몫이다. ③ **그림자 경계의 경로** — [12번 주제](../12-shadow-dom/3-answer.md)가 이미 쟀다. ④ **디스패치 시간** — 재지 않았다. ⑤ **「타깃에서는 등록 순서」가 언제 바뀌었나** — 확인하지 않았다.

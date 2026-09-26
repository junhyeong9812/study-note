# web-api/18 — 이벤트 위임: 조상 하나로 자손 전체 받기·`closest()` 로 되찾기 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 받은 것**이다 — 클릭·포커스·마우스 이동은 **CDP 로 넣은 진짜 입력**이다. 명령은 블록마다 배너로 실려 있다.\
> 규칙은 [WHATWG DOM Standard](https://dom.spec.whatwg.org/) 의 `closest()`·`contains()`·`composedPath()`·dispatch 절로 접지했다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**

**★ 이 편에는 흔들리는 칸이 없었다.**

| 안 흔들리는 칸 | 흔들리는 칸 · 못 잰 칸 |
|---|---|
| 되찾기 표 · 포커스 · 그림자 · `composedPath()` 길이 · `mouseover` 순서 | **못 잰 것** — 위임의 메모리·시간 이득 |
| 캡처를 여러 판 돌려 **한 글자도 같았다** | Chrome 판 번호 |

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 직접 등록은 나중 항목을 놓치고, 위임은 받는다

**출력**

```text
$ python3 wa16b-cdp.py page wa16b-18-deleg.html | sed -n '1,8p'
진짜 클릭 — 직접 등록한 리스너와 목록 하나에 단 위임 리스너
누른 곳                                   직접  위임: e.target    closest('li')   + 목록.contains 가드
#항목1 의 × (span)                        1     span.표           #항목1          #항목1
#항목3 의 × (나중에 더함)                 0     span.표           #항목3          #항목3
#항목2 의 × (단추가 stopPropagation)      1     (위임 리스너 안 불림)
#목록 의 안쪽 여백                        0     #목록             #바깥항목       null
#항목5 의 × (span 이 pointer-events:none) 1     button.지움       #항목5          #항목5
#항목4 의 × (li 가 pointer-events:none)   0     #목록             #바깥항목       null
(exit 0)
```

**왜 그런가**

- **`#항목1`** — 직접 **1**, `e.target` **`span.표`**, 찾음 **`#항목1`**.
- **`#항목3`(나중에 더함)** — 직접 **0**, `e.target` **`span.표`**, 찾음 **`#항목3`**.
- `e.target` 은 **`li` 도 `button` 도 아닌 × 글자 `span`** 이다 — 가장 깊은 요소다.
- 위임이 받는 이유 — **경로는 디스패치할 때 부모를 따라 만든다.** `#항목3` 이 언제 생겼든 그 부모 사슬에 `#목록` 이 있으면 버블이 지난다. 직접 등록은 **등록할 때 있던 단추**에만 붙었다.

### 2. `#목록` 을 넘어 바깥 목록의 항목까지 올라간다

**출력**

```text
$ python3 wa16b-cdp.py page wa16b-18-deleg.html | sed -n '2p;6p'
누른 곳                                   직접  위임: e.target    closest('li')   + 목록.contains 가드
#목록 의 안쪽 여백                        0     #목록             #바깥항목       null
(exit 0)
```

**왜 그런가**

- `e.target` **`#목록`** · 찾음 **`#바깥항목`** · 가드 **`null`**.
- `closest()` 는 **`#목록` 자신 → 그 부모 `#바깥항목`** 까지 올라가 거기서 `li` 를 찾았다.
- **정의대로다** — `closest()` 는 「자기와 조상 가운데 선택자에 맞는 첫 요소」다. 위임 조상에서 멈추라는 인자가 없다.

### 3. 글자만 투명하면 단추로, 항목째 투명하면 목록으로 떨어진다

**출력**

```text
$ python3 wa16b-cdp.py page wa16b-18-deleg.html | sed -n '2p;7,8p'
누른 곳                                   직접  위임: e.target    closest('li')   + 목록.contains 가드
#항목5 의 × (span 이 pointer-events:none) 1     button.지움       #항목5          #항목5
#항목4 의 × (li 가 pointer-events:none)   0     #목록             #바깥항목       null
(exit 0)
```

**왜 그런가**

- **`#항목5`(글자만)** — `e.target` **`button.지움`** · `closest('li')` **`#항목5`** · 가드 **`#항목5`** · 직접 **1**.
- **`#항목4`(항목째)** — `e.target` **`#목록`** · `closest('li')` **`#바깥항목`** · 가드 **`null`** · 직접 **0**.
- 갈리는 이유 — `pointer-events` 는 **상속**된다. 글자에만 주면 **바로 아래의 단추**가 받고, 항목에 주면 **항목 안 전부**가 투명해져 **목록**이 받는다.
- 함정 — **이벤트가 사라지지 않고 아래 요소로 간다.** 거기서 `closest()` 가 문항 2처럼 **바깥 항목**을 잡는다.

### 4. `closest()` 는 경계를 못 넘고, `open` 만 `composedPath()` 로 되찾는다

**출력**

```text
$ python3 wa16b-cdp.py page wa16b-18-shadow.html | sed -n '1,8p'
그림자 안의 × 를 눌렀을 때 — #목록 에 단 위임 리스너가 본 것
어디를 어떻게               e.target  closest('.지움')  composedPath()[0]  composedPath 에서 찾기  경로 길이
열린 · 진짜 클릭            #열린     null              span.표            button.지움             9
열린 · 합성 composed:false  (위임 리스너 안 불림)
열린 · 합성 composed:true   #열린     null              span.표            button.지움             9
닫힌 · 진짜 클릭            #닫힌     null              #닫힌              null                    6
닫힌 · 합성 composed:false  (위임 리스너 안 불림)
닫힌 · 합성 composed:true   #닫힌     null              #닫힌              null                    6
(exit 0)
```

```text
$ python3 wa16b-cdp.py page wa16b-18-shadow.html | sed -n '10,14p'
그림자 안의 span.표 에서 위로 closest 를 부르면 (open)
  closest('.지움')    = button.지움
  closest('#열린')    = null
  closest('#목록')    = null
  closest(':host')    = null
(exit 0)
```

**왜 그런가**

- **진짜 클릭** — `e.target` 은 **호스트**(`#열린`·`#닫힌`), `closest('.지움')` 은 **둘 다 `null`**.
- **`open`** — `composedPath()[0]` **`span.표`**, 경로에서 찾기 **`button.지움`**, 길이 **9**.
- **`closed`** — `[0]` 이 **호스트**, 찾기 **`null`**, 길이 **6** — 안쪽 세 칸(`span`·`button`·`#shadow-root`)이 빠졌다.
- **합성 `composed:false`** — 위임 리스너가 **아예 안 불렸다.** **`composed:true`** — 진짜와 같은 줄이다.
- **안에서 위로** — `closest('.지움')` 은 **`button.지움`**, `closest('#열린')`·`closest('#목록')` 은 **`null`** — 그림자 루트에서 멈춘다.
- ★ **`closed` 에서 바깥의 위임 리스너가 되찾을 방법은 없다** — 컴포넌트가 **`composed: true` 이벤트에 `detail` 을 담아** 알려 주는 것뿐이다([목록의 **21번 주제**](../21-custom-events/)).

### 5. bubble 로 단 `focus` 만 안 불린다

**출력**

```text
$ python3 wa16b-cdp.py page wa16b-18-deleg.html | sed -n '10,13p'
진짜 클릭으로 #칸6 에 포커스 — 목록에 단 리스너가 찾은 항목
  focus           (안 불림)
  focus(capture)  #항목6
  focusin         #항목6
(exit 0)
```

**왜 그런가**

- **`focus`(bubble)** — **안 불림.** **`focus`(capture)** — `#항목6`. **`focusin`** — `#항목6`.
- [16번 주제](../16-event-propagation-phases/3-answer.md)의 비버블 격자 — `focus` 는 `bubbles: false` 라 **부모의 bubble 칸이 0, capture 칸이 1** 이었다. `focusin` 은 버블한다.

### 6. `mouseenter` 는 목록 자신만, `mouseover` 는 같은 항목에서 여러 번

**출력**

```text
$ python3 wa16b-cdp.py page wa16b-18-hover.html
진짜 마우스 이동: 저쪽 → 항목1 글자 → 단추1 → 항목1 글자 → 항목2 글자 → 단추2
  목록의 mouseenter 가 본 target  : #목록
  목록의 mouseover 에서 closest('li'): #항목1 · #항목1 · #항목1 · #항목2 · #항목2
  relatedTarget 으로 거른 mouseover : #항목1 · #항목2

목록이 받은 mouseover 한 줄씩
  e.target        relatedTarget   closest('li')   가드 통과
  #항목1          #저쪽           #항목1          O
  #단추1          #항목1          #항목1          X
  #항목1          #단추1          #항목1          X
  #항목2          #항목1          #항목2          O
  #단추2          #항목2          #항목2          X
(exit 0)
```

**왜 그런가**

- **`로그1`** — `#목록` 하나. 항목의 `mouseenter` 는 버블하지 않아 안 온다. 목록 **자신에게 난** 진입만 봤다.
- **`로그2`** — `#항목1 · #항목1 · #항목1 · #항목2 · #항목2`. `mouseover` 는 **요소가 바뀔 때마다** 나고 버블한다 — 같은 항목 안에서 글자와 단추를 오갈 때도 난다.
- **`로그3`** — `#항목1 · #항목2`. 가드가 보는 **`relatedTarget` 은 「방금 떠난 요소」** 다 — 그것이 이미 그 항목 안이면(`#항목1`·`#단추1`·`#항목2`) 같은 항목 안의 이동이라 버렸다.

### 7. 버블해서 조상을 지나야 한다

- 조건 — **이벤트가 버블해서 위임 조상을 지나야** 한다(그리고 그림자 경계가 있으면 `composed` 여야 한다).
- 깨지는 자리 넷 — **① 버블하지 않는 이벤트**(`focus`·`blur`·`mouseenter`·`load`·`scroll`) · **② `stopPropagation()` 한 자손** · **③ 그림자 경계**(`e.target` 이 호스트로 바뀌고 `closest()` 가 못 넘는다 · `closed` 는 경로도 잘린다) · **④ `pointer-events: none` 이 클릭을 엉뚱한 요소로 보내는 것.**
- 처방 — ① capture 로 달거나 버블하는 짝(`focusin`·`mouseover`) · ② 자손은 `preventDefault()` 만 · ③ `open` 이면 `composedPath()`, `closed` 면 컴포넌트의 `composed` 이벤트 · ④ `closest()` 결과에 `contains` 가드.

### 8. 직접 리스너는 불리고 위임 리스너는 안 불린다

**출력**

```text
$ python3 wa16b-cdp.py page wa16b-18-deleg.html | sed -n '2p;5p'
누른 곳                                   직접  위임: e.target    closest('li')   + 목록.contains 가드
#항목2 의 × (단추가 stopPropagation)      1     (위임 리스너 안 불림)
(exit 0)
```

**왜 그런가**

- **직접 1 · 위임 안 불림.** 단추 자신의 리스너는 불렸고, 버블이 `#목록` 에 못 갔다.
- 17번 주제의 격자에서 **「조상 리스너가 불렸나」 칸**이 「아니오」가 된 것이다 — 위임 리스너가 그 조상이다.
- 기본 동작을 막으려던 것이면 **`preventDefault()` 만** 불렀어야 했다 — 그 칸은 전파를 안 건드린다.

### 9. `closest()` 는 멈출 자리를 모른다

- 명세 — **자기부터 시작해 요소 조상을 차례로** 보며 선택자에 맞는 첫 요소를 돌려준다. **멈출 자리를 주는 인자가 없다.**
- 가드가 없으면 — 바깥 목록의 항목을 **지우거나 고치는** 사고가 **예외 없이** 난다(문항 2·3).
- **`matches()`** 는 자기만, **`closest()`** 는 자기와 조상, **`querySelector()`** 는 자손을 본다.

### 10. 항목이 적고 안 바뀌면 이득이 없다

- 이득이 없는 경우 — **항목 하나이고 안 바뀌는** 자리, **버블하지 않는 이벤트를 주로 받는** 자리(capture 로 바꿔야 하니 읽기가 어려워진다), **그림자 컴포넌트가 대부분인** 자리.
- 컴포넌트 쪽이 할 일 — **바깥이 알아야 하는 것을 `composed: true` 이벤트로 던지고 `detail` 에 담는다.** `closed` 면 그것이 유일한 길이다.
- 재지 않은 것 — **위임이 리스너 수를 줄여 얻는 메모리·시간 이득.** 이 편은 「받나」와 「되찾나」만 쟀다.

### 11. 다른 주제와 잇기

- **칸 수가 다른 이유는 페이지가 달라서**다 — 12번 주제의 (3)은 **단추가 그림자 루트 바로 아래**라 경로가 `단추 · #shadow-root · 호스트 · body · html · document · Window`(open **7칸** → closed **5칸** · 빠진 것 **2칸**)였고, 이 편은 단추 안에 `span` 이 한 겹 더 있고 호스트 위에 `#목록` 이 있어 `span.표 · button.지움 · #shadow-root · #열린 · #목록 · body · html · document · Window`(**9칸** → **6칸** · 빠진 것 **3칸**)다. **성질은 같다** — `closed` 면 **그림자 안쪽 칸(`#shadow-root` 포함)이 빠진다.** 이 편은 그것을 **진짜 클릭**으로 확인했다.
- `closest()` 의 인자 문법 — CSS 갈래 [08번 주제](../../languages/css/syntax/08-basic-selectors-and-combinators/2-summary.md).
- 위임 리스너를 떼는 법 — [15번 주제](../15-listener-registration/3-answer.md)(동일성 조건 · `signal`).

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800`. **엔진은 이것 하나다.** 크로스 브라우저 이식성은 이 문서의 주장 범위 밖이다.

★ **하네스** — [16번 주제](../16-event-propagation-phases/2-summary.md)의 (1)에 전문이 있다. 그림자 안의 × 는 **`js:` 선택자**로 그림자 안 요소의 `getBoundingClientRect` 를 읽어 좌표를 정했다(`closed` 도 `attachShadow` 가 돌려준 참조로 읽었다).\
★ **안쪽 여백**은 `#목록` 의 왼쪽 위 모서리에서 `(4, 4)` 떨어진 점이다(`padding: 16px`).

```sh
# wa16b-18-rerun.sh
# 이 편의 블록을 다시 던지는 법 — 스크래치패드의 src 에서
# 진짜 입력(CDP) 페이지 — 하네스가 자기 프로필로 Chrome 을 띄우고 끝나면 치운다
python3 wa16b-cdp.py page wa16b-18-deleg.html
python3 wa16b-cdp.py page wa16b-18-shadow.html
python3 wa16b-cdp.py page wa16b-18-hover.html
python3 wa16b-cdp.py page wa16b-18-more.html
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 되찾기 표 6줄 · 포커스 3줄 | 캡처 4판 | 동작 방식 (1)\~(5) · A1\~A3 · A5 · A8 |
| 그림자 6줄 · 안에서 위로 4줄 | 캡처 4판 | 동작 방식 (6) · A4 |
| `mouseenter`·`mouseover` 위임 | 캡처 4판 | 동작 방식 (7) · A6 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| `pointer-events: none` 이 보낸 곳 | 단추 / 목록 | CSS 명세의 몫을 이 판의 관찰로만 적었다 |
| `closest(':host')` | `null` | 이 판의 관찰 |
| `mouseover` 가 같은 항목 안에서 또 나는 것 | 세 번 | 이 판의 관찰 |

**안 돌려 본 것** — ① Firefox·Safari(엔진이 없다). ② **위임의 이득**(메모리·시간). ③ **슬롯에 배정된 자식의 위임** — [12번 주제](../12-shadow-dom/3-answer.md)가 합성으로 쟀고 여기서 다시 던지지 않았다. ④ **포인터 이벤트 위임** — [목록의 **23번 주제**](../23-pointer-events/) 몫이다.

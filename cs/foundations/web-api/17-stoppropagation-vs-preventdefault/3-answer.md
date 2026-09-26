# web-api/17 — `stopPropagation` 대 `preventDefault`: 전파를 멈추는 것과 기본 동작을 막는 것 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 받은 것**이다 — 링크 이동·체크 토글·폼 제출은 **CDP 로 넣은 진짜 클릭과 진짜 키**로 일으켰다. 명령은 블록마다 배너로 실려 있다.\
> 규칙은 [WHATWG DOM Standard — Events](https://dom.spec.whatwg.org/#events) 와 [HTML Standard — `input`](https://html.spec.whatwg.org/multipage/input.html) 의 activation 절로 접지했다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**

**★ 이 편에는 흔들리는 칸이 없었다.**

| 안 흔들리는 칸 | 흔들리는 칸 · 못 잰 칸 |
|---|---|
| 2×2 격자 24칸 · 합성 세 가지의 견줌 · `checked` 두 번 읽기 | **부적용** — 시간 |
| 리스너 셋의 호출 · `defaultPrevented` · 반환값 · 키보드 활성화 | **못 잰 것** — 다른 문서로 떠나는 이동 · 실제 폼 전송 |
| 캡처를 여러 판 돌려 **한 글자도 같았다** | Chrome 판 번호 |

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 셋 다 같은 모양 — 멈춤은 조상 칸만, 막음은 기본 칸만

**출력**

```text
$ python3 wa16b-cdp.py page wa16b-17-grid.html | sed -n '1,14p'
진짜 클릭 — 대상 요소의 click 리스너가 하는 일 × 두 가지 관찰
대상       리스너가 부른 것  조상 리스너가 불렸나  기본 동작이 일어났나
링크       없음              예                    예
링크       stopPropagation   아니오                예
링크       preventDefault    예                    아니오
링크       둘 다             아니오                아니오
체크박스   없음              예                    예
체크박스   stopPropagation   아니오                예
체크박스   preventDefault    예                    아니오
체크박스   둘 다             아니오                아니오
제출 단추  없음              예                    예
제출 단추  stopPropagation   아니오                예
제출 단추  preventDefault    예                    아니오
제출 단추  둘 다             아니오                아니오
(exit 0)
```

```text
$ python3 wa16b-cdp.py page wa16b-17-grid.html | sed -n '16,19p'
같은 격자를 다른 던지기로 — 진짜와 갈린 칸
  new MouseEvent  갈린 칸 = 0 / 24
  el.click()      갈린 칸 = 0 / 24
  new Event       갈린 칸 = 6 / 24  (링크/없음/기본, 링크/stopPropagation/기본, 체크박스/없음/기본, 체크박스/stopPropagation/기본, 제출 단추/없음/기본, 제출 단추/stopPropagation/기본)
(exit 0)
```

**왜 그런가**

- **대상 셋이 한 줄도 안 다르다** — 없음(예·예) · `stopPropagation`(아니오·예) · `preventDefault`(예·아니오) · 둘 다(아니오·아니오).
- **`new MouseEvent('click')` 0 / 24 · `el.click()` 0 / 24** — 합성인데도 링크가 이동하고 체크가 바뀌고 제출 이벤트가 났다.
- **`new Event('click')` 6 / 24** — 갈린 여섯 칸이 전부 **「기본」 칸**이다. `new Event` 는 **기본 동작을 아예 안 낸다**(A7).

### 2. 리스너 안에서는 네 줄 모두 `true` — 막으면 끝난 뒤에 되돌아간다

**출력**

```text
$ python3 wa16b-cdp.py page wa16b-17-grid.html | sed -n '21,26p'
체크박스 — 리스너 안에서 읽은 checked 와 디스패치가 끝난 뒤의 checked (진짜 클릭, 처음 값 false)
리스너가 부른 것  리스너 안  끝난 뒤  cancelable  defaultPrevented
없음              true       true     true        false
stopPropagation   true       true     true        false
preventDefault    true       false    true        true
둘 다             true       false    true        true
(exit 0)
```

**왜 그런가**

- **리스너 안의 `읽음` 은 막든 안 막든 `true`** 다. 처음 값은 `false` 였다.
- **끝난 뒤 — 안 막으면 `true`, 막으면 `false`.**
- **`cancelable` 은 넷 다 `true`**, **`defaultPrevented` 는 막은 두 줄만 `true`**.
- ★ **「리스너 안의 `checked` 로 판단」하는 코드는 이미 뒤집힌 새 값을 본다**(A8).

### 3. `stopPropagation` 은 자리를 떠나는 것만, `stopImmediatePropagation` 은 남은 것도

**출력**

```text
$ python3 wa16b-cdp.py page wa16b-17-imm.html | sed -n '1,6p'
가·나. 단추에 리스너 셋(첫째·둘째·셋째) + 조상 — 진짜 클릭, 둘째가 부른 것에 따라
  없음                                 → 첫째 · 둘째 · 셋째 · 조상
  stopPropagation                      → 첫째 · 둘째 · 셋째
  stopImmediatePropagation             → 첫째 · 둘째
  cancelBubble = true                  → 첫째 · 둘째 · 셋째
  조상 capture 에서 stopPropagation    → 조상(capture)
(exit 0)
```

**왜 그런가**

- **없음** — 첫째 · 둘째 · 셋째 · 조상.
- **`stopPropagation`** — 첫째 · 둘째 · **셋째** — 같은 자리의 남은 리스너는 **불린다.** 조상만 안 불린다.
- **`stopImmediatePropagation`** — 첫째 · 둘째 — **셋째도 안 불린다.** inner invoke 가 리스너 하나를 부른 뒤 immediate 플래그를 보고 멈춘다.
- **`cancelBubble = true` 는 `stopPropagation` 과 같다** — 같은 플래그의 옛 이름이다.
- **조상의 capture 에서 멈추면 대상의 리스너는 0 개** 불린다 — 내려가는 길에서 끊었다.

### 4. 조상이 막으면 안 바뀌고, 조상이 멈추면 바뀐다

**출력**

```text
$ python3 wa16b-cdp.py page wa16b-17-imm.html | sed -n '8,9p'
다. 조상의 bubble 리스너가 preventDefault — 진짜 클릭 뒤 체크박스 checked = false · change 이벤트 = 0번
   조상의 capture 리스너가 stopPropagation — 진짜 클릭 뒤 체크박스 checked = true · 체크박스 자신의 click 리스너 = 0번 · change 이벤트 = 1번
(exit 0)
```

**왜 그런가**

- **① 조상의 bubble 리스너가 막으면 — `checked = false` · `change` 0번.** 기본 동작은 **경로를 다 돈 뒤에** 돌고, 그때 취소 표시가 서 있었다.
- **② 조상의 capture 리스너가 멈추면 — `checked = true` · `change` 1번 · 체크박스 자신의 click 리스너 0번.** 전파를 끊어도 **기본 동작은 온다.**
- ★ **기본 동작이 도는 시점은 「디스패치가 다 끝난 뒤」** 다. 그래서 **경로 위 누구든** 막을 수 있고, **전파를 끊는 것은 기본 동작과 무관**하다.

### 5. `cancelable: false` 면 아무 일도 없고, `return false` 는 표면에 따라 갈린다

**출력**

```text
$ python3 wa16b-cdp.py page wa16b-17-imm.html | sed -n '11,16p'
라. cancelable 이 false 인 이벤트에서 preventDefault
  cancelable:false → defaultPrevented = false · dispatchEvent 의 반환값 = true
  cancelable:true  → defaultPrevented = true · dispatchEvent 의 반환값 = false
  returnValue = false 를 대입하면 → defaultPrevented = true
  addEventListener 리스너가 false 를 돌려주면 → dispatchEvent 의 반환값 = true
  onclick 속성 핸들러가 false 를 돌려주면 → defaultPrevented = true
(exit 0)
```

**왜 그런가**

- **`cancelable: false` → `읽음 = false` · 반환값 `true`.** `preventDefault()` 가 아무 일도 안 했다. 예외도 경고도 없다.
- **`cancelable: true` → `읽음 = true` · 반환값 `false`.** 반환값은 「취소 안 됐나」다.
- **`returnValue = false` → `읽음 = true`** — `preventDefault()` 의 옛 표면이다.
- ★ **`addEventListener` 리스너의 `return false` → 반환값 `true`** — **아무것도 안 했다.**
- ★ **`onclick = () => false` → `defaultPrevented = true`** — **속성 핸들러에서는 취소가 된다.** 표면이 다르면 규칙이 다르다.

### 6. 키보드도 click 을 만들고, 같은 `preventDefault` 로 막힌다

**출력**

```text
$ python3 wa16b-cdp.py page wa16b-17-key.html
#상자 click · isTrusted=true · detail=0 · 막기=false
  → 체크박스에서 Space 뒤: 링크 이동 = false · 체크박스 checked = true
#링크 click · isTrusted=true · detail=0 · 막기=false
  → 링크에서 Enter 뒤: 링크 이동 = true · 체크박스 checked = false
#상자 click · isTrusted=true · detail=0 · 막기=true
  → 체크박스에서 Space 뒤: 링크 이동 = false · 체크박스 checked = false
#링크 click · isTrusted=true · detail=0 · 막기=true
  → 링크에서 Enter 뒤: 링크 이동 = false · 체크박스 checked = false
(exit 0)
```

**왜 그런가**

- **진짜 Space(체크박스)·진짜 Enter(링크)가 click 리스너를 부른다** — `isTrusted=true` · **`detail=0`**.
- **`막음` 이 `true` 면 체크도 안 되고 이동도 안 한다.**
- ★ **부작용 — 키보드 사용자의 활성화도 같이 막힌다.** 「마우스만 막는다」는 `click` 으로는 안 된다.

### 7. `MouseEvent` 이고 `click` 이면 — `isTrusted` 는 안 본다

- DOM 표준의 dispatch — **「이벤트가 `MouseEvent` 객체이고 `type` 이 `"click"` 이면」** isActivationEvent 가 참이 되고, 타깃에 activation behavior 가 있으면 activation target 으로 잡는다.
- **`isTrusted` 는 그 조건에 없다.**
- 그래서 **`new Event('click')` 만 기본 동작을 안 낸다** — 이름은 `click` 인데 **`MouseEvent` 가 아니다.** `el.click()` 은 `MouseEvent` 를 만들어 던진다.
- ★ **가벼운 닫기와 같은 규칙으로 외우면 틀린다** — [14번 주제](../14-dialog-popover-scripting/3-answer.md)의 가벼운 닫기는 **합성으로 한 칸도 안 움직였고**, 이 편의 클릭 활성화는 **합성으로도 다 움직였다.** 「합성이면 기본 동작이 없다」도 「합성이면 다 된다」도 틀리다 — **동작마다 명세가 조건을 따로 정한다.**

### 8. 먼저 뒤집고, 취소되면 나중에 되돌린다

- **legacy-pre-activation behavior** — dispatch 가 **경로를 훑기 전에** 돈다. 체크박스는 여기서 **checkedness 를 뒤집는다.**
- **legacy-canceled-activation behavior** — 경로를 다 훑은 뒤 **취소 표시가 서 있으면** 돈다. 체크박스는 여기서 **pre-activation 전의 값으로 되돌린다.**
- 문항 2 — 리스너는 **뒤집힌 뒤**에 불리므로 넷 다 `true` 를 읽는다. 막은 두 줄은 **끝난 뒤에** 되돌아가 `false` 다.
- **링크에는 「먼저 바꾸기」가 없다** — 링크의 이동은 activation behavior(맨 끝)에서만 일어난다. 확인은 문항 1의 격자다 — `preventDefault` 한 줄에서 **`location.hash` 가 끝까지 안 바뀌었다.** ★ 다만 **「리스너 안에서 `location.hash` 를 읽는」 판은 던지지 않았다** — 리스너 안의 값은 명세 절차로만 적는다.

### 9. 두 표시를 읽는 절차가 다르다

- **stop propagation 플래그는 invoke 만 읽는다** — 「이 자리를 부르기 전에 플래그가 서 있으면 돌아간다」. 기본 동작 절차는 이 플래그를 안 본다.
- **취소 표시(canceled flag)는 dispatch 의 끝(activation)과 `defaultPrevented`·반환값만 읽는다.** 경로를 훑는 절차는 이 표시를 안 본다.
- **「둘 다」가 필요한 때** — 기본 동작도 막고 **조상에게도 알리면 안 될 때**뿐이다. 습관처럼 둘 다 부르면 **조상의 위임 리스너·분석 코드·「바깥 클릭 닫기」가 예외 없이 안 불린다.**

### 10. `cancelable` 과 `defaultPrevented`

- **막을 수 있나 = `e.cancelable`**(이벤트의 성질), **막혔나 = `e.defaultPrevented`**(결과).
- **`passive` 리스너 안** — 합성 이벤트에서는 **`cancelable` 이 `true` 인데 `defaultPrevented` 는 `false`** 로 남는다([15번 주제](../15-listener-registration/3-answer.md)). 진짜 휠·터치에서는 **`cancelable` 자체가 `false`** 로 온다([19번 주제](../19-passive-and-scroll/3-answer.md)).
- set the canceled flag 의 두 조건 — **이벤트의 `cancelable` 이 `true`** 이고 **「passive 리스너 안」 표시가 없을 때.**

### 11. 다른 주제와 잇기

- **16번 주제의 경로에서 `stopPropagation` 은 「다음 자리로 가기」를 끊는다.** capture 단계에서 부르면 **타깃까지 못 간다** — 문항 3의 마지막 줄(대상의 리스너 0개)이 그것이다.
- **위임이 깨지는 모양** — 자식이 `stopPropagation` 하면 격자의 「조상 리스너가 불렸나」 칸이 「아니오」가 된다. **위임 리스너가 곧 그 조상**이다([18번 주제](../18-event-delegation/3-answer.md)의 A1).
- **기본 동작 자체의 정본** — 링크는 HTML 갈래 [16번 주제](../../languages/html/syntax/16-links/2-summary.md), 폼 제출은 HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **21번**, 체크박스는 같은 목록의 **24번**이다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800`. **엔진은 이것 하나다.** 크로스 브라우저 이식성은 이 문서의 주장 범위 밖이다.

★ **링크는 같은 문서 안의 조각(`#도착`)으로만 이동시켰다** — 판정은 `decodeURIComponent(location.hash)` 로 했다(한글 조각은 `location.hash` 에 **퍼센트 인코딩**으로 담긴다 — 처음에 그대로 견줬다가 「이동 안 함」으로 잘못 나온 것을 고쳤다).\
★ **폼 제출은 `submit` 이벤트가 났나로만** 쟀다. 실제 전송은 `submit` 리스너가 막았다.\
★ **하네스** — [16번 주제](../16-event-propagation-phases/2-summary.md)의 (1)에 전문이 있다. 좌표는 매번 `getBoundingClientRect` 에서 계산했다.

```sh
# wa16b-17-rerun.sh
# 이 편의 블록을 다시 던지는 법 — 스크래치패드의 src 에서
# 진짜 입력(CDP) 페이지 — 하네스가 자기 프로필로 Chrome 을 띄우고 끝나면 치운다
python3 wa16b-cdp.py page wa16b-17-grid.html
python3 wa16b-cdp.py page wa16b-17-imm.html
python3 wa16b-cdp.py page wa16b-17-key.html
python3 wa16b-cdp.py page wa16b-17-more.html
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 2×2 격자 · 합성 세 가지 견줌 · 체크박스 두 번 읽기 | 캡처 4판 | 동작 방식 (1)·(2)·(4) · A1 · A2 |
| 리스너 셋 · 조상이 막음/멈춤 · `cancelable`·반환값·`return false` | 캡처 4판 | 동작 방식 (3)·(5)·(6) · A3\~A5 |
| 키보드 활성화(진짜 Space·Enter) | 캡처 4판 | 동작 방식 (7) · A6 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| 키보드로 만든 click 의 `detail` | 0 | 이 판의 관찰 |
| `onclick` 의 `return false` 가 취소가 되는 것 | `defaultPrevented = true` | 이벤트 핸들러 절을 열어 확인하지 않았다 |

**안 돌려 본 것** — ① Firefox·Safari(엔진이 없다). ② **다른 문서로 떠나는 링크 이동** — 로그가 사라져 셀 수 없다. ③ **실제 네트워크 전송.** ④ `mousedown` 의 `preventDefault` · `label` 의 두 번째 click · `requestSubmit()` — 이 편의 대상 밖이다. ⑤ **리스너 안에서 `location.hash` 읽기** — 던지지 않았다.

# web-api/20 — 리스너 수명: `once`·`signal` 로 해제하기와 누수 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 받은 것**이다 — GC 격자는 Chrome 을 `--js-flags=--expose-gc` 로 띄워 페이지의 `gc()` 를 불렀다. 명령은 블록마다 배너로 실려 있다.\
> 규칙은 [WHATWG DOM Standard](https://dom.spec.whatwg.org/) 의 add an event listener · signal abort · run the abort steps · `AbortSignal.timeout()`/`any()` 로 접지했다. 회수 보장의 정본은 [JS 갈래 23번 주제](../../languages/js/syntax/23-map-set-and-weak-collections/3-answer.md)다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> ★★ **바이트는 재지 않았다.**

| 안 흔들리는 칸 | 흔들리는 칸 · 못 잰 칸 |
|---|---|
| `signal` 쪽 호출 횟수 · `reason` · `aborted` | ★ **흔들려도 되는 칸** — 「gc() 뒤 몇 번째 틱」 블록 |
| GC 격자의 「불린 판 / 10판」 — **안 흔들렸지만 `10/10` 칸은 이 판의 관찰**이다 | ★ **못 잰 것** — 누수의 바이트 · 속도 영향 |
| 캡처를 세 판 돌려 **한 글자도 같았다** | Chrome 판 번호 |

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `window` 에서 노드까지 길이 남는 칸만 안 회수된다

**출력**

```text
$ python3 wa20b-cdp.py page --gc wa20b-20-gc.html | sed -n '1,10p'
떼어 낸 노드에 FinalizationRegistry 를 걸고 gc() — 콜백이 불린 판 / 10판
무엇을 보나 · 칸                                              불린 판
노드 · 리스너 없음                                            10/10
노드 · 노드 자신에 단 리스너 · 클로저가 n                     10/10
노드 · window 에 단 리스너 · 클로저가 n                       0/10
노드 · window · once · 한 번 던진 뒤                          10/10
노드 · window · once · 안 던짐                                0/10
노드 · window · signal · abort() 뒤                           10/10
노드 · window · removeEventListener 뒤                        10/10
노드 · window · capture:true 로 달고 옵션 없이 remove         0/10
(exit 0)
```

**왜 그런가**

- **① 10/10 · ② 10/10 · ③ 0/10 · ④ 10/10 · ⑤ 0/10 · ⑥ 10/10 · ⑦ 10/10 · ⑧ 0/10.**
- ★ **②와 ③은 클로저가 같은데 답이 반대**다. ②는 `n` 과 리스너가 **서로만** 가리키는 고리라 바깥에서 닿는 길이 없다. ③은 **`window` 의 리스너 목록 → 클로저 → `n`** 으로 길이 이어진다.
- **④와 ⑤를 가르는 것은 「이벤트가 왔나」** 다. `once` 는 **부를 때** 지워지므로([15번 주제](../15-listener-registration/3-answer.md)), 안 오면 남는다.
- ★ **⑧은 [15번 주제](../15-listener-registration/3-answer.md)의 「안 지워지는 칸」이 누수로 바뀐 자리**다 — `capture` 가 동일성 키라 `remove` 가 아무것도 못 찾았다.

### 2. 자식 하나를 쥐면 부모째 남는다

**출력** — 문항 1 과 같은 실행의 뒷부분이다.

```text
$ python3 wa20b-cdp.py page --gc wa20b-20-gc.html | sed -n '1,2p;11,18p'
떼어 낸 노드에 FinalizationRegistry 를 걸고 gc() — 콜백이 불린 판 / 10판
무엇을 보나 · 칸                                              불린 판
노드 · window · 이미 abort 된 signal 로 등록                  10/10
노드 · window 리스너가 n 대신 id 문자열만 기억                10/10
노드 · 리스너 함수를 전역 배열이 붙듦 · 노드 자신에 단 것     0/10
노드 · 리스너 없음 · 노드를 전역 배열이 붙듦                  0/10
부모 · 리스너 없음                                            10/10
부모 · window 리스너의 클로저가 자식 하나를 가리킴            0/10

모든 판에서 불린 칸 = 8 / 14 · 한 판도 안 불린 칸 = 6 / 14
(exit 0)
```

**왜 그런가**

- **⑨ 10/10** — 이미 abort 된 신호로는 **등록 자체가 안 된다.** 붙들 것이 없다.
- **⑩ 10/10** — 클로저가 **노드가 아니라 문자열**을 쥔다. 필요할 때 `getElementById` 로 다시 찾으면 노드를 살리지 않는다.
- **⑪ 0/10 · ⑫ 0/10** — 대조군. 전역에서 `f` 를 거쳐, 또는 곧바로 `n` 에 닿는다.
- ★★ **⑬ 부모 0/10** — 떼어 낸 자식은 `parentNode` 로 부모를 가리키고, 부모는 자기 자식들을 가리킨다. **리스너 하나가 떼어 낸 서브트리 전체**를 붙든다(리스너가 없는 부모는 10/10).

### 3. `abort()` 한 번에 다섯이 빠지고, abort 된 신호로는 조용히 안 달린다

**출력**

```text
$ python3 wa20b-cdp.py page wa20b-20-signal.html | sed -n '1,7p'
가. AbortSignal 하나 · 리스너 다섯 (대상 넷 · 형 둘)
  abort 전 — 네 대상에 가 · 겉에 나 를 던지면 호출 = 5
  abort() 한 번 뒤 — 같은 것을 던지면 호출 = 0

나. 이미 abort 된 signal 로 등록하면
  addEventListener 의 결과 = 예외 없음 · undefined
  던진 뒤 호출 = 0
(exit 0)
```

**왜 그런가**

- **① 5 · ② 0.** 대상 넷 · 형 둘에 흩어진 다섯이 **한 신호**에 묶여 있었다.
- ★ **③ 예외 없음 · 반환 `undefined` · `z` 는 0.** DOM 의 add an event listener 가 첫머리에서 「**signal 이 abort 됐으면 그냥 돌아간다**」.
- ★ 그래서 **abort 한 컨트롤러를 재사용하면 리스너가 안 붙은 것을 모른다** — 문항 8.

### 4. 0 — 리스너는 `abort` 이벤트보다 먼저 떨어진다

**출력**

```text
$ python3 wa20b-cdp.py page wa20b-20-signal.html | sed -n '9,10p'
다. abort 이벤트 리스너 안에서 같은 형을 던지면
  abort 이벤트 리스너 안에서 던진 라 의 호출 = 0
(exit 0)
```

**왜 그런가**

- DOM 의 **run the abort steps** 는 ① abort 알고리즘을 전부 돌리고 ② 목록을 비운 뒤 ③ **그다음에 `abort` 이벤트를 쏜다.** `addEventListener` 가 단 「리스너 지우기」는 ①에 있다.

```text
$ python3 wa20b-cdp.py page wa20b-20-signal.html | sed -n '12,15p'
라. abort 의 이유
  abort() 인자 없음 → reason = AbortError 「signal is aborted without reason」
  abort("그만")     → reason = "그만"
  AbortSignal.abort().aborted = true
(exit 0)
```

- (곁들임) 인자 없는 `abort()` 의 reason 은 **`AbortError`**, 인자를 주면 **그 값 그대로**다.

### 5. `any` 는 한 방향으로 따라가고, `timeout(0)` 도 같은 잡에서는 아직이다

**출력**

```text
$ python3 wa20b-cdp.py page wa20b-20-signal.html | sed -n '17,24p'
마. AbortSignal.any — 둘 중 하나를 abort
  abort 전 호출 = 1
  갑.abort() 뒤 호출 = 0 · 합.aborted = true · 을.signal.aborted = false
  합.reason === 갑.signal.reason → true

바. AbortSignal.timeout(0) — abort 이벤트를 기다린 뒤
  등록 직후(같은 잡) aborted = false
  abort 이벤트 뒤 aborted = true · reason = TimeoutError · 던진 바 의 호출 = 0
(exit 0)
```

**왜 그런가**

- **`갑.abort()` 뒤 0회 · `합.aborted = true` · `을.signal.aborted = false` · reason 은 같은 객체(`true`).** DOM 이 의존 신호에 **원본의 abort reason 을 그대로** 넣는다.
- ★ **`timeout(0)` 이 같은 잡에서 `false`** 인 것은 명세가 「ms 뒤 **타이머 태스크 소스에 태스크를 큐에 넣어** abort」로 정하기 때문이다. `abort` 이벤트 뒤에는 `TimeoutError` 이고 리스너는 빠졌다.
- 이 둘의 **네트워크 쪽 쓰임**은 [목록의 **27번 주제**](../27-abort-and-timeout/)가 정본이다.

### 6. 뿌리에서 닿는 길이 있나

```text
   ② n.addEventListener(형, f)              ③ window.addEventListener(형, f)

      n ──(리스너 목록)──▶ f                   window ──(리스너 목록)──▶ f
      ▲                    │                       ▲                        │
      └───── 클로저 ───────┘                  (뿌리)                        ▼
                                                                            n
      뿌리에서 이 고리로 오는 길 없음            뿌리 ▶ window ▶ f ▶ n
      → 회수 10/10                               → 회수 0/10
```

- **회수는 「참조가 있나」가 아니라 「뿌리에서 닿나」** 로 정해진다. ②는 참조가 두 개나 있지만 **둘 다 고리 안**이다.

### 7. `once` 는 「불린 뒤」에만 풀린다

- **조건 — 그 이벤트가 한 번 와야 한다.** 부를 때 명부에서 지워지기 때문이다.
- **흔한 실패** — `transitionend`·`animationend` 를 `once` 로 기다리는데 전환이 **아예 안 일어나는** 경우(값이 같거나 요소가 숨겨짐). 이 편은 이 경우를 **던지지 않았다** — 대신 「안 던진 `once`」 칸(⑤ 0/10)이 같은 모양이다.
- 그래서 **「`once` 를 썼으니 새지 않는다」는 「반드시 불린다」가 전제**다. 전제가 없으면 `signal` 을 함께 단다.

### 8. 두 실패 다 에러가 없다

- **`capture` 안 맞춘 `remove`** — 호출 쪽에서는 **「지웠는데 또 불린다」**(15편의 4 / 14칸), 메모리 쪽에서는 **0/10**(문항 1의 ⑧). 에러도 경고도 없다.
- **abort 한 컨트롤러 재사용** — 등록이 **예외 없이 무시**된다(문항 3의 ③). 화면에 반응이 없을 뿐 **콘솔도 조용하다**. 마운트마다 **새 컨트롤러**를 만든다.

### 9. 보장은 `0/10` 쪽뿐이다

- ★ **명세가 보장하는 것** — **강하게 닿는 것은 회수되지 않는다**(`0/10` 칸). ECMA-262 는 「어떤 객체가 회수된다」는 **보장을 하지 않는다**고 못 박는다([JS 23번 주제](../../languages/js/syntax/23-map-set-and-weak-collections/3-answer.md)). 그래서 **`10/10` 은 이 판의 V8 이 `gc()` 한 번에 거뒀다는 관찰**이다.
- **「몇 번째 틱」은 명세가 묶지 않는 칸**이라 흔들려도 되는 블록으로 **따로 뗐다** — 섞으면 한 칸이 흔들릴 때 블록 전체가 불일치가 된다.

```text
$ python3 wa20b-cdp.py page --gc wa20b-20-gc.html | sed -n '20,34p'
콜백이 불린 판에서 — gc() 뒤 몇 번째 틱이었나 (- = 20틱 안에 안 불림)
노드 · 리스너 없음                                        1 1 1 1 1 1 1 1 1 1
노드 · 노드 자신에 단 리스너 · 클로저가 n                 1 1 1 1 1 1 1 1 1 1
노드 · window 에 단 리스너 · 클로저가 n                   - - - - - - - - - -
노드 · window · once · 한 번 던진 뒤                      1 1 1 1 1 1 1 1 1 1
노드 · window · once · 안 던짐                            - - - - - - - - - -
노드 · window · signal · abort() 뒤                       1 1 1 1 1 1 1 1 1 1
노드 · window · removeEventListener 뒤                    1 1 1 1 1 1 1 1 1 1
노드 · window · capture:true 로 달고 옵션 없이 remove     - - - - - - - - - -
노드 · window · 이미 abort 된 signal 로 등록              1 1 1 1 1 1 1 1 1 1
노드 · window 리스너가 n 대신 id 문자열만 기억            1 1 1 1 1 1 1 1 1 1
노드 · 리스너 함수를 전역 배열이 붙듦 · 노드 자신에 단 것 - - - - - - - - - -
노드 · 리스너 없음 · 노드를 전역 배열이 붙듦              - - - - - - - - - -
부모 · 리스너 없음                                        1 1 1 1 1 1 1 1 1 1
부모 · window 리스너의 클로저가 자식 하나를 가리킴        - - - - - - - - - -
(exit 0)
```

- **못 잰 것** — ① **바이트**(힙 스냅샷을 안 열었다) ② **무엇이 붙들었나의 경로**(칸을 바꿔 간접으로만 갈랐다). 그 밖에 평소(`gc()` 없이)의 회수 시점도 모른다.

### 10. 다른 주제와 잇기

- **13번 주제의 관용구** — 연결될 때 `this.끈 = new AbortController()` 를 **새로** 만들어 거기 묶어 달고, 분리될 때 `this.끈.abort()`. ★ **컨트롤러는 연결될 때마다 새로** — 같은 요소가 다시 붙으면 연결 콜백이 또 오는데([13번 주제](../13-custom-element-lifecycle/3-answer.md)), abort 된 신호를 재사용하면 **아무것도 안 달린다**(문항 3).
- **18번 주제의 위임** — 리스너를 **오래 사는 조상 하나에** 두지만 **클로저가 개별 노드를 쥐지 않고** `e.target` 으로 그때그때 찾는다. 문항 2의 ⑩(문자열만 기억)과 같은 이유로 **떼어 낸 항목을 살리지 않는다.**
- **JS 23번 주제** — 같은 창(`FinalizationRegistry` + `gc()`)을 **node** 에서 열었다(그쪽은 「브라우저의 GC 는 안 돌렸다」고 적었다). 이 편은 **Chrome 페이지 안에서** `--js-flags=--expose-gc` 로 열었다 — CDP 가 프로미스를 끝까지 기다려 주므로 `setTimeout` 뒤의 결과도 받을 수 있었다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800`. **엔진은 이것 하나다.** 크로스 브라우저 이식성은 이 문서의 주장 범위 밖이다.

★ **GC 격자는 `--js-flags=--expose-gc`** 로 띄운 판에서만 돌렸다(하네스의 `--gc`). 판마다 노드를 새로 만들고, **잡을 한 번 넘긴 뒤** `gc()` 를 부르고, 콜백이 안 불렸으면 **틱마다 `gc()` 를 다시** 부르며 20틱까지 기다린다.\
★ 칸끼리 섞이지 않게 **판마다 이벤트 형 이름을 새로** 지었다. 누수 칸의 리스너는 `window` 에 **남은 채로** 다음 칸이 돈다 — 그 리스너들은 다음 칸의 노드를 가리키지 않는다.\
★ **하네스** — [요약](2-summary.md)의 (1)에 전문이 있다.

```sh
# wa20b-20-rerun.sh
# 이 편의 블록을 다시 던지는 법 — 스크래치패드의 src 에서
# 하네스가 자기 프로필로 Chrome 을 띄우고 끝나면 치운다
python3 wa20b-cdp.py page --gc wa20b-20-gc.html     # --gc = --js-flags=--expose-gc
python3 wa20b-cdp.py page wa20b-20-signal.html
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| GC 격자 14칸 × 10판 | 캡처 3판(판마다 140번 회수를 물었다) | 동작 방식 (2)\~(4) · A1 · A2 · A9 |
| `signal`·`abort` 순서·`reason`·`any`·`timeout` | 캡처 3판 | 동작 방식 (5)\~(7) · A3\~A5 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| 안 붙잡힌 노드의 회수 | `gc()` 한 번에 10/10 | 명세가 회수를 보장하지 않는다 |
| 콜백이 불린 틱 | 첫 틱 | 명세가 시점을 묶지 않는다 |
| `gc()` 의 존재 | `--expose-gc` 에서만 | V8 의 디버깅 표면이다 |

**안 돌려 본 것** — ① Firefox·Safari(엔진이 없다). ② **바이트·시간**(힙 스냅샷·성능 추적). ③ `handleEvent` 객체 · `onclick` 속성 핸들러의 수명. ④ 전환이 안 일어나는 `transitionend` 에 단 `once`(문항 7은 「안 던진 `once`」 칸으로 대신했다).

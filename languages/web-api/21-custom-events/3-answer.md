# web-api/21 — 커스텀 이벤트: `CustomEvent`·`dispatchEvent`·`detail`·`bubbles`/`composed` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 받은 것**이다 — 합성 이벤트가 대부분이고, 문항 6의 ①만 **CDP 로 넣은 진짜 클릭**이다. 명령은 블록마다 배너로 실려 있다.\
> 규칙은 [WHATWG DOM Standard](https://dom.spec.whatwg.org/) 의 `CustomEvent` · `dispatchEvent()` · dispatch · inner invoke · retarget · `composedPath()` 로 접지했다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**

| 안 흔들리는 칸 | 흔들리는 칸 |
|---|---|
| 닿은 자리 격자 · 호출 순서 · 반환값 · `detail` 의 동일성 · 예외 **이름** | 예외 **문구** · Chrome 판 번호 |
| 캡처를 세 판 돌려 **한 글자도 같았다** | — |

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 문서까지는 둘 다 켠 한 줄 · `closed` 는 경로 길이만 바꾼다

**출력**

```text
$ python3 wa20b-cdp.py page wa20b-21-grid.html
그림자 안 #안쪽 에서 dispatchEvent(new CustomEvent('알림', { bubbles, composed }))
칸 = 그 자리에서 본 e.target · e.composedPath().length   (- = 안 불림)
mode · bubbles · composed   #안쪽         호스트              문서
open · true · true          #안쪽 · 7     #열린호스트 · 7     #열린호스트 · 7
open · true · false         #안쪽 · 2     -                   -
open · false · true         #안쪽 · 7     #열린호스트 · 7     -
open · false · false        #안쪽 · 2     -                   -
closed · true · true        #안쪽 · 7     #닫힌호스트 · 5     #닫힌호스트 · 5
closed · true · false       #안쪽 · 2     -                   -
closed · false · true       #안쪽 · 7     #닫힌호스트 · 5     -
closed · false · false      #안쪽 · 2     -                   -

open — 호스트가 받은 칸 = 2 / 4 · 문서가 받은 칸 = 1 / 4
closed — 호스트가 받은 칸 = 2 / 4 · 문서가 받은 칸 = 1 / 4
open 과 closed 가 갈린 칸 = 3 / 12
(exit 0)
```

**왜 그런가**

- **문서까지 닿는 줄은 `bubbles: true · composed: true` 뿐**(두 모드 다 1 / 4). 호스트는 **`composed: true` 인 두 줄**에서 받는다(2 / 4).
- **바깥 자리의 `target` 은 호스트**다 — 재타기팅.
- ★ **`open`/`closed` 가 갈린 칸은 3 / 12 이고 셋 다 경로 길이(7 → 5)** 다. **닿는 곳은 같다.** `closed` 는 **보이는 것**을 줄인다.

### 2. 리스너가 먼저, 마이크로태스크는 맨 끝

**출력**

```text
$ python3 wa20b-cdp.py page wa20b-21-sync.html | sed -n '1,10p'
가. dispatchEvent 앞뒤 줄과 리스너 줄의 순서
  1. dispatchEvent 앞
  2. 리스너 1
  3. 리스너 2 — 안에서 나 를 던짐
  4.   나 의 리스너
  5. 리스너 2 — 나 를 던진 뒤
  6. 리스너 3
  7. 리스너 5
  8. dispatchEvent 뒤
  9. 리스너 4 가 건 마이크로태스크
(exit 0)
```

**왜 그런가**

- `dispatchEvent` 는 **리스너를 전부 부른 뒤** 돌아온다 — 「뒤」가 8번째다.
- 리스너 2 안의 디스패치는 **그 자리에서** 끝까지 돈 뒤 리스너 2 로 돌아온다(3 → 4 → 5).
- ★ **마이크로태스크(9번째)가 「뒤」보다도 늦다** — 스크립트가 던진 디스패치 동안은 **스크립트 스택이 안 비어** 체크포인트가 안 돈다.

### 3. `catch` 는 아무것도 못 잡는다

**출력**

```text
$ python3 wa20b-cdp.py page wa20b-21-sync.html | sed -n '12,15p'
나. 리스너가 던진 예외 — dispatchEvent 를 try 로 감싸면
  리스너 순서 = 리스너 1 — 던지기 직전 → 리스너 2
  호출한 쪽 catch 가 잡은 것 = 없음 · dispatchEvent 의 반환값 = true
  window 의 error 이벤트가 받은 message = ["Uncaught Error: 리스너가 터진다"]
(exit 0)
```

**왜 그런가**

- **리스너 2 는 불린다 · `catch` 는 「없음」 · 반환은 `true`.**
- **`오류` 에는 `"Uncaught Error: 리스너가 터진다"`.** DOM 의 **inner invoke** 가 리스너가 던지면 **report exception** 한다 — 호출자에게 다시 던지지 않는다. 그 보고가 `window` 의 `error` 이벤트와 콘솔로 간다.
- 메시지의 **`Uncaught Error: ` 머리**는 Chrome 의 문구다.

### 4. 같은 상자 · 기본값은 전부 거짓

**출력**

```text
$ python3 wa20b-cdp.py page wa20b-21-sync.html | sed -n '17,25p'
다. dispatchEvent 의 반환값과 cancelable
  cancelable:true · 리스너가 preventDefault → 반환값 = false · defaultPrevented = true
  cancelable:false · 리스너가 preventDefault → 반환값 = true · defaultPrevented = false

라. detail 은 무엇이 건너가나
  리스너가 받은 detail === 보낸 객체 → true
  디스패치 뒤 보낸 쪽이 읽은 값 = {"수":2,"목록":["가","나"]}
  detail 을 안 주면 = null · detail 에 대입하면 = TypeError 「Cannot set property detail of #<CustomEvent> which has only a getter」
  isTrusted = false · bubbles 기본 = false · composed 기본 = false · cancelable 기본 = false
(exit 0)
```

**왜 그런가**

- **`===` 가 `true`**, 디스패치 뒤 `보낸것` 은 **`{"수":2,"목록":["가","나"]}`** — 리스너가 고친 것이 그대로 보인다. DOM 은 `detail` 이 **「초기화된 값을 돌려준다」** 고만 한다 — 복사하라는 말이 없다.
- **기본 `detail` 은 `null` · 대입은 `TypeError`**(읽기 전용 접근자 · 엄격 모드).
- **`isTrusted`·`bubbles`·`composed`·`cancelable` 이 전부 `false`.**
- (곁들임) 반환값 — `cancelable: true` 에서 막으면 `false`, `cancelable: false` 면 막아도 `true`([17번 주제](../17-stoppropagation-vs-preventdefault/3-answer.md)와 같다).

### 5. 디스패치 중이면 `InvalidStateError`

**출력**

```text
$ python3 wa20b-cdp.py page wa20b-21-sync.html | sed -n '27,30p'
마. 같은 이벤트 객체를 다시 던지면
  리스너 안에서 같은 객체를 dispatchEvent = InvalidStateError 「Failed to execute 'dispatchEvent' on 'EventTarget': The event is already being dispatched.」
  디스패치가 끝난 뒤 같은 객체를 한 번 더 = 예외 없음 · true
  Event 가 아닌 객체(CustomEvent.prototype 만 물려받음) 를 던지면 = TypeError 「Failed to execute 'dispatchEvent' on 'EventTarget': parameter 1 is not of type 'Event'.」
(exit 0)
```

**왜 그런가**

- **① `InvalidStateError`** — `dispatchEvent()` 의 첫 단계가 「dispatch flag 가 서 있거나 initialized flag 가 없으면 던진다」.
- **② 예외 없음 · `true`** — 끝난 뒤에는 플래그가 내려가 있다.
- **③ `TypeError`** — 인자가 `Event` 가 아니면 **IDL 변환**에서 먼저 막힌다.

### 6. 진짜 클릭은 리스너 사이에 마이크로태스크가 낀다

**출력**

```text
$ python3 wa20b-cdp.py page wa20b-21-sync.html | sed -n '32,33p'
바. 진짜 클릭 — 진짜 클릭 시작 → 리스너 1 → 리스너 1 이 건 마이크로태스크 → 리스너 2
바. el.click() — el.click() 시작 → 리스너 1 → 리스너 2 → el.click() 다음 줄 → 리스너 1 이 건 마이크로태스크
(exit 0)
```

**왜 그런가**

- **① 리스너 1 → 마이크로태스크 → 리스너 2.** 브라우저가 리스너를 하나씩 부를 때마다 **스크립트 스택이 비어** 체크포인트가 돈다.
- **② 리스너 1 → 리스너 2 → 다음 줄 → 마이크로태스크.** `el.click()` 을 부른 스크립트가 **아직 안 끝났다.**
- ★ 순서는 이 판의 관찰이고, **그 이유를 정한 명세 절은 이 문서가 열지 않았다** — 목록의 **40번 주제** 몫이다.

### 7. 호스트에서 다시 「타깃 단계」가 된다

- `composed: true` 라 경로가 **호스트 너머까지** 만들어진다. 그런데 `bubbles: false` 라 **타깃 단계의 리스너만** 불린다.
- **호스트에서는 이벤트의 `target` 이 호스트로 재타기팅되어** 그 자리가 **타깃 단계**다 — 그래서 불린다([12번 주제](../12-shadow-dom/3-answer.md)의 (15)).
- **문서는 버블 단계로만 받을 수 있는 자리**라 못 받는다.

### 8. 보이는 것을 줄일 뿐, 가는 길은 그대로다

- 바깥 리스너의 `composedPath()` 에서 **그림자 안의 두 칸(`#안쪽` · `#shadow-root`)** 이 빠진다. DOM 의 `composedPath()` 절차가 **closed 트리의 뿌리(root-of-closed-tree)** 를 기준으로 안쪽을 숨긴다.
- **「`closed` 면 바깥으로 안 나간다」는 거짓**이다 — 격자에서 닿는 곳이 `open` 과 **같았다.**

### 9. 다른 주제와 잇기

- **18번 주제의 합성 이벤트** — `composed: false` 로 던진 줄이다(격자의 `bubbles · false` 줄). 경로가 **그림자 루트에서 끝나** 문서의 위임 리스너가 못 받는다.
- **13번 주제와 같은 모양** — 둘 다 **호출자에게 예외가 안 오고** 콘솔(과 `error` 이벤트)로 샌다. 명세가 두 자리 모두 **report exception** 을 쓴다.
- **16번 주제의 기본값** — `new CustomEvent('x', { detail })` 만 쓰면 `bubbles: false` 라 **부모도 못 받는다.** 어디서 틀리나 1번.

### 10. 문구는 Chrome, 이름은 명세

- **예외 이름**(`InvalidStateError`·`TypeError`)은 **명세**가 정한다. **문구**(`The event is already being dispatched.` · `Uncaught Error: …`)는 **Chrome 의 것**이다.
- **진짜 클릭의 마이크로태스크 자리**는 **「이 판의 관찰」** 로 적었다 — 순서는 쟀지만 그 순서를 정한 명세 절(스크립트 실행 뒤 정리 단계의 체크포인트)을 **열어 확인하지 않았기 때문**이다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800`. **엔진은 이것 하나다.** 크로스 브라우저 이식성은 이 문서의 주장 범위 밖이다.

★ **격자와 순서 로그는 전부 합성 이벤트**이고, 문항 6의 ①만 CDP 의 `Input.dispatchMouseEvent` 로 넣은 **진짜 클릭**이다.\
★ 예외 칸의 `오류` 는 **`dispatchEvent` 를 부른 그 함수 안에서 곧바로 읽었는데 이미 채워져 있었다** — `error` 이벤트가 같은 잡 안에서 왔다. 그 뒤의 한 틱(`setTimeout(0)`)은 다음 단계와 떼려고 넣은 것이다.\
★ **하네스** — [20번 주제](../20-listener-lifetime/2-summary.md)의 (1)에 전문이 있다.

```sh
# wa20b-21-rerun.sh
# 이 편의 블록을 다시 던지는 법 — 스크래치패드의 src 에서
python3 wa20b-cdp.py page wa20b-21-grid.html
python3 wa20b-cdp.py page wa20b-21-sync.html      # 바. 만 진짜 클릭(CDP)
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 닿은 자리 격자 8줄 | 캡처 3판 | 동작 방식 (1) · A1 · A7 · A8 |
| 순서 · 예외 · 반환값 · `detail` · 재디스패치 · 진짜 클릭 | 캡처 3판 | 동작 방식 (2)\~(5) · A2\~A6 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| 예외 문구 | `Uncaught Error: …` 등 | Chrome 의 문구다 |
| 진짜 클릭에서 마이크로태스크의 자리 | 리스너 사이 | 이 문서는 관찰로만 적었다 |

**안 돌려 본 것** — ① Firefox·Safari(엔진이 없다). ② `Event` 를 상속한 클래스. ③ 얼린 `detail`(`Object.freeze`)을 리스너가 고치려 할 때. ④ 슬롯 자식에서 던진 `CustomEvent`(12편이 `Event` 로 봤다).

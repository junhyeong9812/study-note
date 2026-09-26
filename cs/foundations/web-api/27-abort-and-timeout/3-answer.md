# web-api/27 — `AbortController` 로 취소와 타임아웃: `AbortSignal.timeout()`/`any()` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 받은 것**이다 — 서버는 로컬 서버 A 이고, 「처리」는 **페이지가 `/go` 를 줄 때** 끝난다. 명령은 블록마다 배너로 실려 있다.\
> 규칙은 [WHATWG Fetch](https://fetch.spec.whatwg.org/) 의 fetch() 메서드 단계 · To abort a fetch() call 과 [WHATWG DOM](https://dom.spec.whatwg.org/) 의 `abort()`·`AbortSignal.timeout()`·`any()` 로 접지했다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**

| 안 흔들리는 칸 | 흔들리는 칸 · 못 잰 칸 |
|---|---|
| 취소 격자 · 서버 로그 · 본문 쪽 넷 · 오류 이름과 문구 | ★★ **흔들린다** — 「부르자마자 취소」에서 서버에 도착한 판 수(캡처 여섯 판 5~6 / 100)와 번호 |
| 캡처를 세 판 돌려 **한 글자도 같았다** | **못 잰 것** — 실제 네트워크 · HTTP/2 의 스트림 리셋 · 업로드 중 취소 |

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 서버에서 끝까지 처리된 칸 6 / 7

**출력**

```text
$ python3 wa24b-net.py page wa24b-27-grid.html
칸                                            페이지가 받은 것                                        서버 도착 처리 끝 연결 닫힘을 앎 응답 쓰기
이미 abort 된 signal 로 fetch                 catch · AbortError 「signal is aborted without reason」 아니오    아니오  아니오         —
서버 도착 뒤·처리 중 abort()                  catch · AbortError 「signal is aborted without reason」 예        예      예             BrokenPipeError
처리 중 abort('그만') — 이유를 줌            catch · string 「그만」                                 예        예      예             BrokenPipeError
처리 중 AbortSignal.timeout(1000)             catch · TimeoutError 「signal timed out」               예        예      예             BrokenPipeError
any([사용자, timeout(60초)]) — 사용자가 abort catch · AbortError 「signal is aborted without reason」 예        예      예             BrokenPipeError
any([사용자, timeout(1000)]) — 아무도 안 누름 catch · TimeoutError 「signal timed out」               예        예      예             BrokenPipeError
abort 없음(대조)                              then · status=200                                       예        예      아니오         오류 없음
서버에서 끝까지 처리된 칸 = 6 / 7
--- 서버 로그 ---
A GET /work  도착 — 처리 시작
A   상대가 연결을 닫은 것을 알았다
A   처리 끝 (주문을 기록했다)
A   응답 쓰기 실패 (BrokenPipeError)
A GET /work  도착 — 처리 시작
A   상대가 연결을 닫은 것을 알았다
A   처리 끝 (주문을 기록했다)
A   응답 쓰기 실패 (BrokenPipeError)
A GET /work  도착 — 처리 시작
A   상대가 연결을 닫은 것을 알았다
A   처리 끝 (주문을 기록했다)
A   응답 쓰기 실패 (BrokenPipeError)
A GET /work  도착 — 처리 시작
A   상대가 연결을 닫은 것을 알았다
A   처리 끝 (주문을 기록했다)
A   응답 쓰기 실패 (BrokenPipeError)
A GET /work  도착 — 처리 시작
A   상대가 연결을 닫은 것을 알았다
A   처리 끝 (주문을 기록했다)
A   응답 쓰기 실패 (BrokenPipeError)
A GET /work  도착 — 처리 시작
A   처리 끝 (주문을 기록했다)
A   응답을 썼다 (오류 없음)
(exit 0)
```

**왜 그런가**

- ★★★ **취소한 다섯 칸 전부 「도착 예 · 처리 끝 예」** — 서버 로그가 칸마다 「상대가 연결을 닫은 것을 알았다 → 처리 끝 (주문을 기록했다) → 응답 쓰기 실패 (BrokenPipeError)」를 적었다. 서버는 끊김을 **알고도** 처리를 마쳤다.
- **이미 abort 된 signal 한 칸만 「도착 아니오」** — 요청이 나가지 않았다(서버 로그에 그 줄이 없다).
- **대조 칸** — `then · status=200` · 응답 쓰기 「오류 없음」.

### 2. 본문 쪽 두 오류는 `signal.reason` 과 다르다

**출력**

```text
$ python3 wa24b-net.py page wa24b-27-body.html
가. 첫 read() → "줄1\n" · 그다음 abort()
   둘째 read() → AbortError 「BodyStreamBuffer was aborted」 · === signal.reason → false
   서버 — 도착=true · 보내려 한 청크=2/5 · 연결 닫힘을 앎=true · 쓰기=BrokenPipeError
나. 서버가 끝까지 썼다(쓰기=오류 없음) · 아직 안 읽었다 · 그다음 abort()
   text() → AbortError 「The user aborted a request.」 · === signal.reason → false
다. 처리 중 abort() → fetch 의 거부 = AbortError 「signal is aborted without reason」 · === signal.reason → true
라. text() 로 다 읽은 뒤 abort() → 이미 받은 글 = "{\"status\": 200}" · bodyUsed=true
--- 서버 로그 ---
A GET /chunks?n=5  도착
A   상대가 연결을 닫은 것을 알았다
A   쓰기 실패 (BrokenPipeError) — 청크 2/5 째에서
A GET /chunks?n=1  도착
A   청크 1개와 끝 표시까지 썼다
A GET /work  도착 — 처리 시작
A   상대가 연결을 닫은 것을 알았다
A   처리 끝 (주문을 기록했다)
A   응답 쓰기 실패 (BrokenPipeError)
A GET /status?code=200  → 200 응답을 끝까지 보냈다
(exit 0)
```

**왜 그런가**

- **가. 읽는 중** — 다음 `read()` 가 **`AbortError 「BodyStreamBuffer was aborted」`**, `=== signal.reason → false`. 서버는 청크 2 를 쓰다 `BrokenPipeError`.
- ★★ **나. 다 왔는데 안 읽음** — `text()` 가 **`AbortError 「The user aborted a request.」`**, `false`. 서버는 끝까지 오류 없이 썼다.
- **다. `fetch` 의 거부** — `AbortError 「signal is aborted without reason」`, **`true`** — 프라미스 쪽은 같은 객체다.
- **라. 다 읽은 뒤** — 아무 일 없음. 받은 글이 그대로다.
- ★ 명세는 프라미스도 본문도 **같은 error** 로 끝내라고 적는다 — 이 판의 본문 쪽은 **새 `AbortError`** 였다.

### 3. 거부는 100 / 100, 도착은 0 이 아니다 — 판마다 다르다

**출력**

```text
$ python3 wa24b-net.py quiet wa24b-27-race.html
AbortError 로 거부된 판 = 100 / 100
서버에 도착한 판 = 6 / 100
도착한 번호 = [0,1,2,3,4,5]
(exit 0)
```

**왜 그런가**

- **페이지는 100번 다 `AbortError`** 를 받았다. **서버에 도착한 판은 캡처 여섯 판에서 5 · 6 · 6 · 6 · 6 · 6**(번호는 앞쪽부터), 시험판(20번씩)은 0 · 1 · 1 — **다시 돌리면 다르다.**
- 결론은 수가 아니라 **「0 이 아니다」** — 부르자마자 취소해도 요청은 서버에 닿을 수 있다.

### 4. 거르지 못한다 — `e` 가 문자열 `"그만"` 이다

- 문항 1 의 「다」 칸에서 페이지가 받은 것은 **`string 「그만」`** — `abort("그만")` 의 reason **그 자체**다. 문자열에는 `name` 이 없으니 조건이 거짓이 되어 **「취소」를 오류로 잘못 다룬다.**
- Fetch 의 abort 단계가 **signal 의 abort reason 으로** 거부하기 때문이다. reason 을 줄 때는 `new DOMException("그만", "AbortError")` 처럼 주거나 **`signal.aborted`** 로 판정한다.

### 5. 페이지 쪽 프라미스와 스트림만 끝낸다

- 「To abort a fetch() call」 — **① 프라미스를 error 로 거부 ② 요청 본문이 readable 이면 취소 ③ 응답 본문이 readable 이면 error 로 error.** 그리고 fetch 의 abort 단계가 **controller 를 abort** 한다.
- **서버에게 되돌리라고 하는 단계는 없다.** 이 판에서 그것은 **연결을 닫는 것**으로만 보였고(서버의 「상대가 연결을 닫은 것을 알았다」), 서버는 처리를 마쳤다(문항 1).

### 6. 두 번 처리 — 멱등 키로 막는다

- `timeout(1000)` 칸에서도 서버는 **「처리 끝」** 이었다(문항 1). 다시 보내면 **주문이 둘**이 될 수 있다.
- 막는 것은 **서버 쪽** — 요청마다 멱등 키를 싣고 서버가 같은 키를 한 번만 처리한다([`../../../ops-patterns/06-idempotency-store/`](../../../ops-patterns/06-idempotency-store/)).

### 7. 이미 abort 된 signal — 보내기 전에 끝났기 때문이다

- **확실한 것은 문항 1 의 첫 칸(이미 abort 된 signal)뿐**이다. Fetch 의 fetch() 메서드가 **「signal 이 이미 abort 됐으면 abort the fetch() call 하고 돌아간다」** — 요청을 만들기 전에 끝난다.
- 문항 3 처럼 **부른 뒤에** 끊으면 요청이 이미 나갔을 수 있다 — 결과가 판마다 달랐다.

### 8. 다른 주제와 잇기

- **20번 주제와 문항 1 첫 칸** — 둘 다 **「이미 abort 된 signal 이면 일을 시작하지 않는다」** 는 규칙이다. DOM 의 add an event listener 는 **등록하지 않고 돌아가고**(호출 0회), Fetch 의 fetch() 는 **요청을 내보내지 않고 거부한다**(서버 도착 아니오).
- **[JS 41번 주제](../../languages/js/syntax/41-cancellation-and-timeouts/2-summary.md)의 (4)** — node 안의 서버로 「이미 abort 된 신호는 요청 0 · 처리 중 abort 는 서버가 받았고 연결만 끊긴다」를 쟀다. 이 편의 문항 1 은 같은 사실을 **브라우저 페이지**에서 다시 보고, **서버가 처리를 끝까지 한 것과 응답 쓰기의 `BrokenPipeError`** 를 더했다.
- **Go 34번 주제의 `context`** — 서버 쪽 처리에 **「클라이언트가 떠났다」를 전하는 통로**다. 이 편의 서버는 끊김을 **알았지만**(연결 닫힘) 처리에 전하지 않아서 끝까지 갔다. 그 편은 `net/http` 쪽을 안 던졌으므로 **대비로만** 적는다.
- **도구가 못 보는 것** — ① **실제 네트워크에서 가는 중에 끊기는 것**(루프백은 거의 즉시 닿는다) ② **HTTP/2·HTTP/3 의 취소**(이 판은 HTTP/1.1 — 연결 닫기로만 보였다).

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · 서버 `http.server`(HTTP/1.1). **엔진은 Chrome 하나다.**

★ **동기화** — 「처리 중」은 **서버가 도착을 알린 뒤**(`/state?wait=arrived`)다. 페이지는 취소를 받은 뒤 **서버가 연결 닫힘을 알아챌 때까지**(`/state?wait=closed`) 기다렸다가 `/go` 로 처리를 끝낸다. 서버는 `/go` 를 기다리는 동안 소켓을 들여다봐 **닫힘을 한 번 적는다.**\
★ **응답 쓰기** — 닫힌 연결에 쓴 첫 바이트는 커널이 받아 준다. 그래서 **오류가 날 때까지 한 바이트씩 더 쓴다** — 시험판에서 한 번만 쓰면 「오류 없음」이 나올 수 있었다.\
★ **재대조 정규화** — 문항 3 의 두 줄(`서버에 도착한 판 = N / 100` · `도착한 번호 = […]`)만.\
★ **하네스** — [24번 주제](../24-document-lifecycle-events/2-summary.md)의 (1)에 전문이 있다.

```sh
# wa24b-27-rerun.sh
# 이 편의 블록을 다시 던지는 법 — 스크래치패드의 src 에서
python3 wa24b-net.py page wa24b-27-grid.html
python3 wa24b-net.py page wa24b-27-body.html
python3 wa24b-net.py quiet wa24b-27-race.html
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 취소 격자 7칸 + 서버 로그 | 캡처 3판 | 동작 방식 (1)·(2) · A1 · A4 · A6 · A7 |
| 본문 쪽 넷 | 캡처 3판 | 동작 방식 (3) · A2 |
| 부르자마자 취소 100번 | 캡처 6판(+ 시험판 20번 × 3) | 동작 방식 (4) · A3 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| 본문 쪽 오류 `=== signal.reason` | `false` | 명세 문장과 다르다 |
| 본문 쪽 오류 문구 | `BodyStreamBuffer was aborted` · `The user aborted a request.` | Chrome 의 글자 |
| 부르자마자 취소의 도착 수 | 판마다 다름 | 정해져 있지 않다 |
| 취소가 서버에 보이는 모양 | 연결 닫힘 | 프로토콜 판에 달렸다 |

**안 돌려 본 것** — ① Firefox·Safari(엔진이 없다). ② 업로드 중 취소 · `keepalive`. ③ HTTP/2.

# web-api/26 — 응답 본문과 스트리밍: `json()`/`text()`/`blob()` 은 한 번만·`body` 와 `ReadableStream` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 받은 것**이다 — 청크 서버는 로컬 서버 A 이고 **페이지가 `/go` 를 줄 때마다** 하나씩 보낸다. 명령은 블록마다 배너로 실려 있다.\
> 규칙은 [WHATWG Fetch](https://fetch.spec.whatwg.org/) 의 Body 믹스인(unusable · consume body · clone a body)과 [WHATWG Streams](https://streams.spec.whatwg.org/) 의 `tee()`·`releaseLock()` 으로 접지했다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**

| 안 흔들리는 칸 | 흔들리는 칸 · 못 잰 칸 |
|---|---|
| 예외 전문 · 청크 대조 · `text()` 정착 · 쪼개진 한글 | **고쳤다** — 청크 대조의 첫 줄·끝 줄(청크를 전부 `/go` 뒤로 미뤘다) |
| 캡처를 세 판 돌려 **한 글자도 같았다** | **못 잰 것** — `clone()` 의 메모리 · 속도 · 큰 청크의 쪼개짐 |

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 문구 셋 — `already read` · `is locked` · `already used`

**출력**

```text
$ python3 wa24b-net.py page wa24b-26-once.html
가. 읽기 전 bodyUsed=false
   첫 json() → {"status":200}
   읽은 뒤 bodyUsed=true
   둘째 json() → TypeError 「Failed to execute 'json' on 'Response': body stream already read」
   그 뒤 text() → TypeError 「Failed to execute 'text' on 'Response': body stream already read」
   그 뒤 clone() → TypeError 「Failed to execute 'clone' on 'Response': Response body is already used」
나. clone 뒤 원본 json() → {"status":200}
   clone 뒤 복사본 text() → "{\"status\": 200}"
다. getReader() 뒤 body.locked=true · bodyUsed=false
   reader 를 쥔 채 text() → TypeError 「Failed to execute 'text' on 'Response': body stream is locked」
   releaseLock() 뒤 text() → "{\"status\": 200}"
라. blob() → size=15 · type="application/json"
   그 뒤 arrayBuffer() → TypeError 「Failed to execute 'arrayBuffer' on 'Response': body stream already read」
--- 서버 로그 ---
A GET /status?code=200  → 200 응답을 끝까지 보냈다
A GET /status?code=200  → 200 응답을 끝까지 보냈다
A GET /status?code=200  → 200 응답을 끝까지 보냈다
A GET /status?code=200  → 200 응답을 끝까지 보냈다
(exit 0)
```

**왜 그런가**

- **한 번 읽은 뒤** — `json()`·`text()`·`arrayBuffer()` 는 **`TypeError 「… body stream already read」`**, `clone()` 은 **`TypeError 「… Response body is already used」`**.
- **reader 를 쥔 동안** — `text()` 는 **`TypeError 「… body stream is locked」`**. 그때 `bodyUsed` 는 아직 `false` 다.
- **읽기 전에 `clone()`** 하면 두 쪽 다 읽힌다. **`releaseLock()` 뒤**에는 `text()` 가 전부 읽는다.
- Fetch 명세 — **disturbed 또는 locked 면 unusable → 소비는 `TypeError` 로 거부, `clone()` 은 `TypeError` 를 던진다.** 문구는 Chrome 의 것이다.

### 2. 정착 때 0 / 5 · 받을 때마다 「아직 다 안 보냈다」

**출력**

```text
$ python3 wa24b-net.py page wa24b-26-stream.html
fetch 가 정착(status=200) — 이때 서버가 보낸 청크 = 0 / 5
read() 1번째 → 5바이트 "줄1\n" · 이때 서버가 보낸 청크 = 1 / 5 · 끝까지 다 썼나 = false
read() 2번째 → 5바이트 "줄2\n" · 이때 서버가 보낸 청크 = 2 / 5 · 끝까지 다 썼나 = false
read() 3번째 → 5바이트 "줄3\n" · 이때 서버가 보낸 청크 = 3 / 5 · 끝까지 다 썼나 = false
read() 4번째 → 5바이트 "줄4\n" · 이때 서버가 보낸 청크 = 4 / 5 · 끝까지 다 썼나 = false
read() 5번째 → 5바이트 "줄5\n" · 이때 서버가 보낸 청크 = 5 / 5 · 끝까지 다 썼나 = false
read() 6번째 → done=true
--- 서버 로그 ---
A GET /chunks?n=5  도착
A   청크 5개와 끝 표시까지 썼다
(exit 0)
```

**왜 그런가**

- **`fetch` 는 헤더에서 정착** — 그때 서버가 보낸 청크는 **0 / 5**.
- **`read()` 다섯 번 모두 「끝까지 다 썼나 = false」** — 청크 k 를 받은 그때 서버는 k 개만 보냈다. 여섯 번째가 `done=true`.
- 서버는 `/go` 없이 다음 청크를 못 보낸다 — 브라우저가 본문을 모아서 줬다면 첫 `read()` 에서 멈췄을 것이다.

### 3. 다섯 번 다 `false` — 끝 표시 뒤에야 다섯 줄

**출력**

```text
$ python3 wa24b-net.py page wa24b-26-whole.html
서버가 청크 1 / 5 를 보낸 뒤 — text() 정착 = false
서버가 청크 2 / 5 를 보낸 뒤 — text() 정착 = false
서버가 청크 3 / 5 를 보낸 뒤 — text() 정착 = false
서버가 청크 4 / 5 를 보낸 뒤 — text() 정착 = false
서버가 청크 5 / 5 를 보낸 뒤 — text() 정착 = false
서버가 끝 표시까지 보낸 뒤 — text() 가 돌려준 것 = "줄1\n줄2\n줄3\n줄4\n줄5\n"
--- 서버 로그 ---
A GET /chunks?n=5  도착
A   청크 5개와 끝 표시까지 썼다
(exit 0)
```

**왜 그런가**

- **`text()` 는 끝 표시가 온 뒤에야 한 번** 정착한다. 그 전에는 서버가 몇 개를 보냈든 아무것도 없다.
- 진행률·조기 처리는 reader 로 한다(문항 2).

### 4. 따로 풀면 `�` · 이어 풀면 「가」「나」

**출력**

```text
$ python3 wa24b-net.py page wa24b-26-decode.html
가. 바이트 조각 길이 = [2,2,3]
   조각마다 new TextDecoder().decode() → ["�","��","��\n"]
나. 한 TextDecoder 에 {stream:true} → ["","가","나\n"]
다. 을.pipeThrough(new TextDecoderStream()) → ["가","나\n"]
--- 서버 로그 ---
A GET /chunks?split=1  도착
A   청크 3개와 끝 표시까지 썼다
(exit 0)
```

**왜 그런가**

- **조각마다 새 `TextDecoder`** — 잘린 바이트가 대체 문자 `�` 가 된다. 오류는 없다.
- **한 `TextDecoder` 에 `{ stream: true }`** — `["","가","나\n"]`. 첫 조각에서는 내지 않고 기다렸다.
- **`TextDecoderStream`** — `["가","나\n"]`. 같은 일을 스트림으로, 빈 조각 없이.

### 5. 고인다 — 「두 갈래가 모두 안 읽힐 때만 배압」

- Fetch 의 **clone a body 는 본문 스트림을 `tee` 한다.** Streams 의 `tee()` 는 **「두 소비자가 다른 속도로」** 읽게 하고, 배압은 **「두 갈래가 모두 안 읽힐 때에만」** 원본에 간다 — 한쪽을 읽는 동안 원본은 흐르고 **안 읽힌 쪽 큐에 쌓인다.**
- **본 것** — 동작 방식 (4)에서 을이 갑이 다 읽을 때까지 안 읽혔는데 **조각이 전부 남아 있었다.** **안 잰 것** — 그 메모리 크기.

### 6. reader 를 쥔 채 — `bodyUsed=false` · `locked=true`

- `getReader()` 만 한 상태다. **`text()` 는 `TypeError 「body stream is locked」`**(문항 1의 「다」줄).

### 7. 헤더까지 — 본문은 0 바이트

- 정착한 순간 서버는 **청크를 하나도 안 보냈다**(0 / 5). 서버는 **페이지가 `/go` 를 줘야** 첫 청크를 쓰므로, 정착 때 본문이 와 있을 수가 **없다** — 시간이 아니라 순서로 묶어서 흔들리지 않는다.

### 8. 다른 주제와 잇기

- **25번 주제의 한 번 쓴 `Request`** — 같은 **Body 믹스인의 unusable 규칙**이다. 요청 본문도 응답 본문도 한 번 흐르면 끝이고, 두 번 쓰려면 **쓰기 전에 `clone()`** 한다.
- **도구가 못 보는 것** — ① **`clone()` 뒤 안 읽은 갈래가 먹는 메모리**(행동만 봤다) ② **「스트리밍이 빠르다」**(순서만 봤다 — 재지 않았다). 그 밖에 중간 장비의 청크 모으기 · 큰 청크의 쪼개짐.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · 청크 서버 `http.server`(HTTP/1.1 · `Transfer-Encoding: chunked`). **엔진은 Chrome 하나다.**

★ **청크 서버** — 헤더는 곧바로, **청크와 끝 표시는 `/go` 를 하나 받을 때마다 하나씩** 쓴다. 「보낸 청크 수」는 **쓰기 전에** 올린다 — 페이지가 받았을 때 이미 올라가 있도록. 시험판은 첫 청크를 헤더와 함께 곧바로 보냈다(정착 때의 수가 0 과 1 사이에서 갈릴 수 있었다).\
★ **하네스** — [24번 주제](../24-document-lifecycle-events/2-summary.md)의 (1)에 전문이 있다.

```sh
# wa24b-26-rerun.sh
# 이 편의 블록을 다시 던지는 법 — 스크래치패드의 src 에서
python3 wa24b-net.py page wa24b-26-once.html
python3 wa24b-net.py page wa24b-26-stream.html
python3 wa24b-net.py page wa24b-26-whole.html
python3 wa24b-net.py page wa24b-26-decode.html
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 두 번 읽기 · 잠금 · `clone` | 캡처 3판 | 동작 방식 (1) · A1 · A6 |
| 청크 대조 | 캡처 3판 | 동작 방식 (2) · A2 · A7 |
| `text()` 정착 | 캡처 3판 | 동작 방식 (3) · A3 |
| 쪼개진 한글 | 캡처 3판 | 동작 방식 (4)·(5) · A4 · A5 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| 예외 문구 셋 | `already read` · `is locked` · `already used` | 명세는 `TypeError` 만 정한다 |
| 한 `read()` 가 주는 크기 | 서버 청크 하나 | 묶어 주는 단위는 구현이다 |
| `TextDecoderStream` 의 빈 조각 | 안 냄 | 이 판의 관찰 |

**안 돌려 본 것** — ① Firefox·Safari(엔진이 없다). ② BYOB reader · 요청 본문 스트림. ③ 압축(`Content-Encoding`)된 청크.

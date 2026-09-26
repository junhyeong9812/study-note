# web-api/25 — `fetch` 와 `Request`/`Response`: 옵션·헤더·상태 코드가 예외가 아니라는 것 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 받은 것**이다 — 서버 두 대(A·B)는 같은 기계의 로컬 서버이고 **바깥 인터넷으로는 요청하지 않았다.** 명령은 블록마다 배너로 실려 있다.\
> 규칙은 [WHATWG Fetch](https://fetch.spec.whatwg.org/) 의 ok status · fetch() 메서드 단계 · CORS check · forbidden request-header / response-header name · clone 으로 접지했다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**

| 안 흔들리는 칸 | 흔들리는 칸 · 못 잰 칸 |
|---|---|
| 격자 · 콘솔 · 서버 로그 · 값 · 헤더 · `urllib` | **고쳤다** — 서버 로그의 마지막 줄이 빠지던 것(처리 중 요청이 0 이 될 때까지 기다린다) |
| 캡처를 세 판 돌려 **한 글자도 같았다** | **못 잰 것** — 실제 네트워크 끊김 · HTTP/2 |

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `catch` 로 간 칸 2 / 6 — 연결 실패와 CORS, 같은 글자

**출력**

```text
$ python3 wa24b-net.py console wa24b-25-grid.html | sed -n '1,8p'
요청              then  catch  res.ok  res.status  catch 의 오류
A 200             불림  —     true    200         —
A 404             불림  —     false   404         —
A 500             불림  —     false   500         —
없는 포트         —    불림   —      —          TypeError 「Failed to fetch」
B POST 허용 없음  —    불림   —      —          TypeError 「Failed to fetch」
B POST 허용 있음  불림  —     true    200         —
catch 로 간 칸 = 2 / 6
(exit 0)
```

**왜 그런가**

- **404·500 은 `then`** — `ok=false` 이고 `status` 가 그대로 실린다. 응답이 왔기 때문이다.
- **`catch` 는 없는 포트와 허용 없는 다른 출처 POST** — 둘 다 **`TypeError 「Failed to fetch」`** 로 **한 글자도 같다.** 스크립트는 둘을 못 가른다.

### 2. 콘솔은 다섯 줄 `error` · 서버 B 는 주문을 처리했다

**출력**

```text
$ python3 wa24b-net.py console wa24b-25-grid.html | sed -n '/^--- 콘솔/,$p'
--- 콘솔 ---
network · error · Failed to load resource: the server responded with a status of 404 (Not Found)
network · error · Failed to load resource: the server responded with a status of 500 (Internal Server Error)
network · error · Failed to load resource: net::ERR_CONNECTION_REFUSED
javascript · error · Access to fetch at 'http://<B>/order' from origin 'http://<A>' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
network · error · Failed to load resource: net::ERR_FAILED
--- 서버 로그 ---
A GET /status?code=200  → 200 응답을 끝까지 보냈다
A GET /status?code=404  → 404 응답을 끝까지 보냈다
A GET /status?code=500  → 500 응답을 끝까지 보냈다
B POST /order  Origin=http://127.0.0.1:<A> · 본문 「주문 1건」 → 주문을 처리했다 · 200 을 보냈다 · 허용 헤더 없음
B POST /order?acao=1  Origin=http://127.0.0.1:<A> · 본문 「주문 2건」 → 주문을 처리했다 · 200 을 보냈다 · 허용 헤더 있음
(exit 0)
```

**왜 그런가**

- ★★★ **서버 B 는 「주문 1건」을 받아 처리하고 200 을 보냈다** — 허용 헤더가 없어서 **브라우저가 읽기를 막았을 뿐**이다. Fetch 는 CORS 검사를 **응답에 대해** 한다.
- **CORS 의 이유는 콘솔에만 있다**(`… blocked by CORS policy: No 'Access-Control-Allow-Origin' header …`) — 스크립트는 못 읽는다.
- ★ **404·500 도 콘솔에서는 `error` 수준**이다 — 그래도 스크립트에서는 예외가 아니다.

### 3. 없는 포트 쪽만 `unhandledrejection`

**출력**

```text
$ python3 wa24b-net.py page wa24b-25-unhandled.html
가. fetch 둘을 걸었다 — catch 는 안 달았다
나. 404 쪽 then → 불림 · res.ok=false
다. 없는 포트 쪽 then → (안 불림)
라. unhandledrejection → reason = TypeError 「Failed to fetch」
--- 서버 로그 ---
A GET /status?code=404  → 404 응답을 끝까지 보냈다
(exit 0)
```

**왜 그런가**

- **404 쪽은 `then` 이 불렸다**(`ok=false`) — 거부가 아니므로 보고될 것이 없다.
- **없는 포트 쪽은 거부됐는데 받는 쪽이 없어** `unhandledrejection` 하나(`TypeError 「Failed to fetch」`). `then` 만 단 코드에서 **404 는 조용히 사라진다.**

### 4. 값으로 만든 응답도 `ok=false` · 한 번 쓴 요청은 `TypeError`

**출력**

```text
$ python3 wa24b-net.py page wa24b-25-value.html
가. new Response(…, {status:404}) → ok=false · status=404 · statusText="" · type=default · url=""
   json() → {"n":1}
나. Response.json({n:2}) → status=200 · Content-Type=application/json
다. status 99 → RangeError 「Failed to construct 'Response': The status provided (99) is outside the range [200, 599].」
   status 204 에 본문 → TypeError 「Failed to construct 'Response': Response with null body status cannot have body」
라. new Request(…) → method=POST · bodyUsed=false
   fetch(요청) → status=201 · 그 뒤 요청.bodyUsed=true
   fetch(요청) 한 번 더 → TypeError 「Failed to execute 'fetch' on 'Window': Cannot construct a Request with a Request object that has already been used.」
   fetch(복사) — 미리 clone 한 것 → status=201
마. new Request(url, {method:'PUT'}) → method=PUT
--- 서버 로그 ---
A POST /status?code=201  → 201 응답을 끝까지 보냈다
A POST /status?code=201  → 201 응답을 끝까지 보냈다
(exit 0)
```

**왜 그런가**

- `new Response` 는 네트워크를 안 거쳐 `type=default` · `url=""`. `Response.json` 은 `application/json` 과 200 을 채운다.
- **상태 99 → `RangeError`**(`[200, 599]`), **204 + 본문 → `TypeError`**(null body status).
- ★★ **본문 있는 `Request` 를 한 번 보내면 `bodyUsed=true`, 두 번째는 `TypeError`.** 미리 `clone()` 한 것은 나갔다 — Fetch 의 `clone()` 은 「unusable 이면 `TypeError`」라 **보내기 전에** 떠야 한다.

### 5. 빈 `Headers` 는 다 담고, `Request` 는 지우고, 서버에는 `x-PrObE` 만

**출력**

```text
$ python3 wa24b-net.py page wa24b-25-headers.html
가. Headers — get('x-probe') = "a, b" · 이름 목록 = ["x-probe"]
나. new Headers 에 담긴 이름 = ["connection","content-length","cookie","host","origin","referer","sec-probe","x-probe"]
다. new Request(…, {headers}) 의 headers 에 남은 이름 = ["x-probe"]
라. fetch(…, {headers}) — 예외 없이 status=200
마. 응답 — get('x-visible') = "v1" · get('set-cookie') = null · 쿠키 통 = ["jar=1","srv=1"]
--- 서버 로그 ---
A GET /headers?show=X-Probe,Host,Cookie,Origin,Referer,Content-Length,Connection,Sec-Probe  받은 헤더 이름(보낸 그대로) = Host · Connection · sec-ch-ua-platform · User-Agent · x-PrObE · sec-ch-ua · sec-ch-ua-mobile · Accept · Sec-Fetch-Site · Sec-Fetch-Mode · Sec-Fetch-Dest · Referer · Accept-Encoding · Accept-Language · Cookie
    X-Probe = 1
    Host = 127.0.0.1:<A>
    Cookie = jar=1
    Origin = (안 왔다)
    Referer = http://127.0.0.1:<A>/wa24b-25-headers.html
    Content-Length = (안 왔다)
    Connection = keep-alive
    Sec-Probe = (안 왔다)
(exit 0)
```

**왜 그런가**

- **빈 `new Headers()`** 는 여덟 이름을 다 담는다. **`new Request(…, { headers })`** 가 되는 순간 `x-probe` 하나만 남는다 — 지우는 자리는 요청을 만들 때다.
- **서버** — `x-PrObE = 1`(이름 글자꼴까지 그대로, HTTP/1.1) · `Host` 는 진짜 주소 · **`Cookie` 는 쿠키 통의 `jar=1`** · `Referer` 는 진짜 페이지 · `Origin`·`Content-Length`·`Sec-Probe` 는 없음. **예외는 하나도 없었다.**
- **`X-Visible` 은 읽히고 `Set-Cookie` 는 `null`** — 그런데 쿠키 통에는 `srv=1` 이 들어갔다. 브라우저는 처리했고 스크립트만 못 본다.

### 6. `urllib` 는 404·500 에 `HTTPError`

**출력**

```text
$ python3 wa24b-net.py urllib
urlopen /status?code=200 → 돌아옴 · status 200
urlopen /status?code=404 → 예외 HTTPError 「404 Not Found」
urlopen /status?code=500 → 예외 HTTPError 「500 Internal Server Error」
--- 서버 로그 ---
A GET /status?code=200  → 200 응답을 끝까지 보냈다
A GET /status?code=404  → 404 응답을 끝까지 보냈다
A GET /status?code=500  → 500 응답을 끝까지 보냈다
(exit 0)
```

**왜 그런가**

- **200 은 돌아오고 404·500 은 `HTTPError`** — 파이썬 표준 라이브러리는 HTTP 오류를 예외로 올린다. JS `fetch` 는 안 올린다.
- **서버 로그는 `fetch` 때와 같다** — 서버가 한 일은 같고 **클라이언트의 설계**가 다르다.

### 7. 「ok status 는 200\~299」 · 「network error 면 `TypeError` 로 거부」

- Fetch 명세 — **「An ok status is a status in the range 200 to 299, inclusive.」** 그리고 fetch() 메서드 단계의 **「If response is a network error, then reject p with a TypeError」**.
- 404 응답은 network error 가 아니라 **응답**이다 → 프라미스는 이행되고 `ok` 만 거짓이다.

### 8. 막힌 것은 읽기, 안 막힌 것은 전송과 처리

- **막힌 것** — 페이지가 응답을 읽는 것(`TypeError`). **안 막힌 것** — 요청이 서버에 닿는 것, 서버가 **처리하는** 것(문항 2 의 서버 로그).
- 그래서 **주문·송금처럼 되돌릴 수 없는 엔드포인트**는 「CORS 가 막아 주겠지」로 지킬 수 없다 — 서버가 `Origin`·토큰으로 스스로 막아야 한다(목록의 **28번 주제**).

### 9. `Request` 를 만들 때 — 서버 로그로만 알아챈다

- **`new Request(…, { headers })` 가 금지 헤더를 지운다**(문항 5의 「다」줄). `fetch(url, { headers })` 도 안에서 같은 `Request` 를 만든다.
- **예외가 없으므로** 알아채는 창은 **서버가 받은 헤더**뿐이다 — 이 편의 창 ④.

### 10. 다른 주제와 잇기

- **JS 37번 주제와 문항 3** — 37편이 **「거부를 아무도 안 받으면 태스크 하나 뒤 `unhandledrejection`」** 을 Chrome 에서 쟀다. 문항 3은 그 틀 위에서 **`fetch` 의 무엇이 거부인가**를 가른다 — **404 는 거부가 아니라서 그 틀에 아예 안 들어간다.**
- **도구가 못 보는 것** — ① **실제 네트워크 끊김**(루프백만 썼다 — 「없는 포트」 하나로 흉내 냈다) ② **HTTP/2 에서의 헤더 이름 글자꼴**(이 판은 HTTP/1.1).

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · Python 3 표준 라이브러리 `http.server`(서버 A·B) · `urllib.request`(대비). **엔진은 Chrome 하나다.**

★ **서버 로그** — 엔드포인트 요청만 적는다. 로그를 찍기 전에 **처리 중인 요청이 0 이 될 때까지** 기다린다 — 시험판에서 `urllib` 가 헤더만 받고 돌아와 **마지막 로그 줄이 빠진 판**이 있었다.\
★ **하네스** — [24번 주제](../24-document-lifecycle-events/2-summary.md)의 (1)에 전문이 있다.

```sh
# wa24b-25-rerun.sh
# 이 편의 블록을 다시 던지는 법 — 스크래치패드의 src 에서
python3 wa24b-net.py console wa24b-25-grid.html
python3 wa24b-net.py page wa24b-25-unhandled.html
python3 wa24b-net.py page wa24b-25-value.html
python3 wa24b-net.py page wa24b-25-headers.html
python3 wa24b-net.py urllib
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 여섯 요청 격자 + 콘솔 + 서버 로그 | 캡처 3판 | 동작 방식 (1)·(2) · A1 · A2 · A7 · A8 |
| 미처리 거부 | 캡처 3판 | 동작 방식 (3) · A3 |
| 값 · 헤더 | 캡처 3판 | 동작 방식 (4)·(5) · A4 · A5 · A9 |
| `urllib` 대비 | 캡처 3판 | 동작 방식 (6) · A6 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| 오류 문구 | `Failed to fetch` | 명세는 `TypeError` 만 정한다 |
| 헤더 이름 글자꼴 | 보낸 그대로(HTTP/1.1) | 프로토콜 판에 달렸다 |
| 콘솔의 404 수준 | `error` | 개발자 도구의 성질 |

**안 돌려 본 것** — ① Firefox·Safari(엔진이 없다). ② `mode: "no-cors"` · 리다이렉트 · 캐시. ③ 프리플라이트가 붙는 요청(28번 주제).

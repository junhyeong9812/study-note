# web-api/28 — CORS: 단순 요청과 프리플라이트, 막는 것과 못 막는 것 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 받은 것**이다 — 서버 두 대(A·B)는 같은 기계의 로컬 서버이고 **바깥 인터넷으로는 요청하지 않았다.** 명령은 블록마다 배너로 실려 있다.\
> 규칙은 [WHATWG Fetch](https://fetch.spec.whatwg.org/) 의 CORS-safelisted method · CORS-safelisted request-header · main fetch 의 프리플라이트 조건 · HTTP fetch · CORS-preflight fetch · CORS-preflight cache · opaque filtered response · Request 생성자로 접지했다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**

| 안 흔들리는 칸 | 흔들리는 칸 · 못 잰 칸 |
|---|---|
| 격자 32칸 · 격자 밖 · 거부 · 노출 헤더 · `no-cors` · 리다이렉트 · Go | **시간에 기댄 칸** — `Max-Age` 없음의 「1번」(기본 5초 안) |
| 캡처를 세 판 돌려 **한 글자도 같았다** | **못 잰 것** — 프리플라이트의 지연 · HTTP/2 스트림 업로드 · `Max-Age` 상한 |

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. OPTIONS 가 먼저 온 칸 26 / 32 — 안 붙는 여섯 칸

**출력**

```text
$ python3 wa28b-net.py quiet wa28b-28-grid.html
메서드  Content-Type                       헤더  B 가 받은 순서            페이지
GET     text/plain                         없음  GET                       status 200
GET     text/plain                         X-A   OPTIONS → GET            status 200
GET     application/x-www-form-urlencoded  없음  GET                       status 200
GET     application/x-www-form-urlencoded  X-A   OPTIONS → GET            status 200
GET     multipart/form-data                없음  GET                       status 200
GET     multipart/form-data                X-A   OPTIONS → GET            status 200
GET     application/json                   없음  OPTIONS → GET            status 200
GET     application/json                   X-A   OPTIONS → GET            status 200
POST    text/plain                         없음  POST                      status 200
POST    text/plain                         X-A   OPTIONS → POST           status 200
POST    application/x-www-form-urlencoded  없음  POST                      status 200
POST    application/x-www-form-urlencoded  X-A   OPTIONS → POST           status 200
POST    multipart/form-data                없음  POST                      status 200
POST    multipart/form-data                X-A   OPTIONS → POST           status 200
POST    application/json                   없음  OPTIONS → POST           status 200
POST    application/json                   X-A   OPTIONS → POST           status 200
PUT     text/plain                         없음  OPTIONS → PUT            status 200
PUT     text/plain                         X-A   OPTIONS → PUT            status 200
PUT     application/x-www-form-urlencoded  없음  OPTIONS → PUT            status 200
PUT     application/x-www-form-urlencoded  X-A   OPTIONS → PUT            status 200
PUT     multipart/form-data                없음  OPTIONS → PUT            status 200
PUT     multipart/form-data                X-A   OPTIONS → PUT            status 200
PUT     application/json                   없음  OPTIONS → PUT            status 200
PUT     application/json                   X-A   OPTIONS → PUT            status 200
DELETE  text/plain                         없음  OPTIONS → DELETE         status 200
DELETE  text/plain                         X-A   OPTIONS → DELETE         status 200
DELETE  application/x-www-form-urlencoded  없음  OPTIONS → DELETE         status 200
DELETE  application/x-www-form-urlencoded  X-A   OPTIONS → DELETE         status 200
DELETE  multipart/form-data                없음  OPTIONS → DELETE         status 200
DELETE  multipart/form-data                X-A   OPTIONS → DELETE         status 200
DELETE  application/json                   없음  OPTIONS → DELETE         status 200
DELETE  application/json                   X-A   OPTIONS → DELETE         status 200
OPTIONS 가 먼저 온 칸 = 26 / 32
(exit 0)
```

**왜 그런가**

- **안 붙는 여섯 칸 = `GET`·`POST` × `text/plain`·`application/x-www-form-urlencoded`·`multipart/form-data` × 헤더 없음.** 세 문(메서드 · `Content-Type` 값 · 헤더 이름)이 **모두 안전 목록**일 때만 단순 요청이다.
- ★ **`GET` + `application/json`** 도 붙는다 — 본문이 없어도 **헤더 값**으로. **`multipart/form-data`** 는 boundary 없이도 안전 목록이다(명세는 MIME 본질만 본다).
- ★★ **페이지의 `status` 는 32칸 모두 200** — 페이지만으로는 못 가른다. **서버에게 물어야** 보인다.

### 2. 값의 모양 · 안전 헤더 · 스트림 본문

**출력**

```text
$ python3 wa28b-net.py console wa28b-28-edge.html
Content-Type: text/plain;charset=UTF-8
    B 가 받은 순서 = POST · 페이지 = status 200
Content-Type: TEXT/PLAIN
    B 가 받은 순서 = POST · 페이지 = status 200
Content-Type: text/plain + 매개변수로 129바이트
    B 가 받은 순서 = OPTIONS → POST · 페이지 = status 200
Accept: application/json
    B 가 받은 순서 = POST · 페이지 = status 200
Accept-Language: ko
    B 가 받은 순서 = POST · 페이지 = status 200
본문 ReadableStream · duplex 없음
    B 가 받은 순서 = (없음) · 페이지 = TypeError 「Failed to execute 'fetch' on 'Window': The `duplex` member must be specified for a request with a streaming body」
본문 ReadableStream · duplex: 'half'
    B 가 받은 순서 = OPTIONS · 페이지 = TypeError 「Failed to fetch」
본문 ReadableStream · mode: 'no-cors'
    B 가 받은 순서 = (없음) · 페이지 = TypeError 「Failed to execute 'fetch' on 'Window': If request is made from ReadableStream, mode should be"same-origin" or "cors"」
--- 콘솔 ---
network · error · Failed to load resource: net::ERR_ALPN_NEGOTIATION_FAILED
--- 서버 로그 ---
B POST /cors?id=e0  Origin=http://127.0.0.1:<A> · Content-Type=text/plain;charset=UTF-8 · X-A=(없음) · 본문 1바이트 → 처리했다
B POST /cors?id=e1  Origin=http://127.0.0.1:<A> · Content-Type=TEXT/PLAIN · X-A=(없음) · 본문 1바이트 → 처리했다
B OPTIONS /cors?id=e2  Origin=http://127.0.0.1:<A> · Access-Control-Request-Method=POST · Access-Control-Request-Headers=content-type
B POST /cors?id=e2  Origin=http://127.0.0.1:<A> · Content-Type=text/plain; p=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa · X-A=(없음) · 본문 1바이트 → 처리했다
B POST /cors?id=e3  Origin=http://127.0.0.1:<A> · Content-Type=text/plain;charset=UTF-8 · X-A=(없음) · 본문 1바이트 → 처리했다
B POST /cors?id=e4  Origin=http://127.0.0.1:<A> · Content-Type=text/plain;charset=UTF-8 · X-A=(없음) · 본문 1바이트 → 처리했다
B OPTIONS /cors?id=e6  Origin=http://127.0.0.1:<A> · Access-Control-Request-Method=POST · Access-Control-Request-Headers=(없음)
(exit 0)
```

**왜 그런가**

- **`;charset=UTF-8`·대문자는 안전**(본질이 `text/plain`), **129바이트는 붙는다**(128바이트를 넘으면 안전 목록 밖). **`Accept`·`Accept-Language` 는 안전 목록 헤더**다.
- ★★ **스트림 + `duplex: 'half'` 는 OPTIONS 가 먼저 왔는데 `Access-Control-Request-Headers=(없음)`** — 붙은 이유가 **본문의 종류**다(명세: `ReadableStream` 이면 use-CORS-preflight flag). 본 요청은 서버에 안 왔고 페이지는 `TypeError 「Failed to fetch」`, 콘솔은 `ERR_ALPN_NEGOTIATION_FAILED` — 이 판의 Chrome 은 HTTP/1.1 로 스트림 본문을 안 보낸다(구현).
- **`duplex` 없음·`no-cors` 는 보내기 전 `TypeError`** — 서버에 아무것도 없다.

### 3. 거부되면 서버 로그에 OPTIONS 한 줄뿐

**출력**

```text
$ python3 wa28b-net.py console wa28b-28-answers.html
가. OPTIONS 답이 넉넉함 → then · status 200
나. OPTIONS 답에 Access-Control-Allow-Origin 없음 → catch · TypeError 「Failed to fetch」
다. OPTIONS 답의 Allow-Methods 가 GET 뿐 → catch · TypeError 「Failed to fetch」
--- 콘솔 ---
javascript · error · Access to fetch at 'http://127.0.0.1:<B>/cors?id=d2&pf=noacao' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: No 'Access-Control-Allow-Origin' header is present on the requested resource.
network · error · Failed to load resource: net::ERR_FAILED
javascript · error · Access to fetch at 'http://127.0.0.1:<B>/cors?id=d3&pf=nomethod' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: Method PUT is not allowed by Access-Control-Allow-Methods in preflight response.
network · error · Failed to load resource: net::ERR_FAILED
--- 서버 로그 ---
B OPTIONS /cors?id=d1&pf=ok  Origin=http://127.0.0.1:<A> · Access-Control-Request-Method=PUT · Access-Control-Request-Headers=(없음)
B PUT /cors?id=d1&pf=ok  Origin=http://127.0.0.1:<A> · Content-Type=text/plain;charset=UTF-8 · X-A=(없음) · 본문 6바이트 → 처리했다
B OPTIONS /cors?id=d2&pf=noacao  Origin=http://127.0.0.1:<A> · Access-Control-Request-Method=PUT · Access-Control-Request-Headers=(없음)
B OPTIONS /cors?id=d3&pf=nomethod  Origin=http://127.0.0.1:<A> · Access-Control-Request-Method=PUT · Access-Control-Request-Headers=(없음)
(exit 0)
```

**왜 그런가**

- ★★★ **나·다는 `PUT` 이 서버에 닿지 않았다** — OPTIONS 한 줄뿐이다. 25편 문항 2의 단순 `POST` 는 **「주문을 처리했다 · 허용 헤더 없음」** 이었다 — 거기는 **처리된 뒤 읽기만** 막혔고, 여기는 **보내지도 않았다.**
- ★★ **페이지 쪽 글자는 25편과 같다**(`TypeError 「Failed to fetch」`) — 스크립트는 두 경우를 못 가른다. **콘솔만 가른다** — 「Response to preflight request doesn't pass …」 · 「Method PUT is not allowed by Access-Control-Allow-Methods …」.

### 4. `600` 은 1번 · `0` 은 2번 · 헤더 없음도 1번

**출력**

```text
$ for k in 1 2 3; do python3 wa28b-net.py quiet wa28b-28-maxage.html; done
Max-Age: 600 — PUT 두 번 → B 가 받은 순서 = OPTIONS → PUT → PUT · OPTIONS 1번
Max-Age: 0 — PUT 두 번 → B 가 받은 순서 = OPTIONS → PUT → OPTIONS → PUT · OPTIONS 2번
Max-Age 헤더 없음 — PUT 두 번 → B 가 받은 순서 = OPTIONS → PUT → PUT · OPTIONS 1번
Max-Age: 600 — PUT 두 번 → B 가 받은 순서 = OPTIONS → PUT → PUT · OPTIONS 1번
Max-Age: 0 — PUT 두 번 → B 가 받은 순서 = OPTIONS → PUT → OPTIONS → PUT · OPTIONS 2번
Max-Age 헤더 없음 — PUT 두 번 → B 가 받은 순서 = OPTIONS → PUT → PUT · OPTIONS 1번
Max-Age: 600 — PUT 두 번 → B 가 받은 순서 = OPTIONS → PUT → PUT · OPTIONS 1번
Max-Age: 0 — PUT 두 번 → B 가 받은 순서 = OPTIONS → PUT → OPTIONS → PUT · OPTIONS 2번
Max-Age 헤더 없음 — PUT 두 번 → B 가 받은 순서 = OPTIONS → PUT → PUT · OPTIONS 1번
(exit 0)
```

**왜 그런가**

- **세 판(하네스를 매번 새로 띄움) 모두 같다.** `600` 은 두 번째 PUT 을 캐시가 답했고, `0` 은 매번 물었다.
- ★★ **헤더가 없으면 기본 5초**(명세) — 두 PUT 이 5초 안이라 1번이었다. 「안 적으면 캐시 안 한다」가 아니다.
- ★ 캐시가 답한 OPTIONS 는 **서버에 흔적이 없다** — 「안 왔다」를 「캐시가 답했다」로 읽는 근거는 **같은 주소의 첫 PUT 에는 왔다**는 것이다.

### 5. 노출 안 된 헤더는 `null`

**출력**

```text
$ python3 wa28b-net.py page wa28b-28-expose.html
가. Access-Control-Expose-Headers 없음
    x-secret=null · content-language="ko" · content-type="application/json" · content-length="13"
    순회한 이름 = ["content-language","content-length","content-type"]
나. Access-Control-Expose-Headers: X-Secret
    x-secret="s1" · content-language="ko" · content-type="application/json" · content-length="13"
    순회한 이름 = ["content-language","content-length","content-type","x-secret"]
다. Access-Control-Expose-Headers: *
    x-secret="s1" · content-language="ko" · content-type="application/json" · content-length="13"
    순회한 이름 = ["access-control-allow-origin","access-control-expose-headers","content-language","content-length","content-type","date","server","x-secret"]
--- 서버 로그 ---
B GET /cors?id=x1  Origin=http://127.0.0.1:<A> · Content-Type=(없음) · X-A=(없음) · 본문 0바이트 → 처리했다
B GET /cors?id=x2&expose=X-Secret  Origin=http://127.0.0.1:<A> · Content-Type=(없음) · X-A=(없음) · 본문 0바이트 → 처리했다
B GET /cors?id=x3&expose=*  Origin=http://127.0.0.1:<A> · Content-Type=(없음) · X-A=(없음) · 본문 0바이트 → 처리했다
(exit 0)
```

**왜 그런가**

- **노출 헤더 없음 → `x-secret=null`**, 순회 이름은 **안전 목록 응답 헤더 셋**(`content-language`·`content-length`·`content-type`)뿐. 헤더는 **도착했는데** 스크립트에게 안 보인다.
- **`X-Secret` 을 적으면 그것이 더**, **`*` 면 전부**(`date`·`server` 까지) — 자격 증명이 없는 요청이라 `*` 가 통했다.

### 6. `then` · opaque · status 0 — 서버는 받았다

**출력**

```text
$ python3 wa28b-net.py page wa28b-28-nocors.html
가. then · type=opaque · status=0 · ok=false · 헤더 이름 = [] · text() = ""
나. PUT → TypeError 「Failed to execute 'fetch' on 'Window': 'PUT' is unsupported in no-cors mode.」
--- 서버 로그 ---
B POST /cors?id=n1&acao=none  Origin=http://127.0.0.1:<A> · Content-Type=text/plain;charset=UTF-8 · X-A=(없음) · 본문 11바이트 → 처리했다
(exit 0)
```

**왜 그런가**

- ★★ **허용 헤더가 없는데 `catch` 가 아니라 `then`** — 그런데 **`type=opaque · status=0 · 헤더 [] · 본문 ""`**. 페이지는 **성공했는지조차 모른다.**
- ★★ **서버 B 는 「주문 3건」을 처리했다.** **`X-A` 는 안 실렸다**(예외 없이 버려짐). **`PUT` 은 보내기 전 `TypeError`**.

### 7. HTTP fetch 가 프리플라이트의 network error 를 그대로 돌려주고 끝난다

- Fetch 의 HTTP fetch 는 프리플라이트가 필요하면 **CORS-preflight fetch 를 먼저** 돌리고, **「preflightResponse 가 network error 면 그것을 돌려준다」** — 본 요청을 만드는 단계까지 가지 않는다. CORS-preflight fetch 는 **CORS check 가 성공하고 status 가 ok status** 일 때만, 그리고 **메서드·헤더가 허용 목록에 있을 때만** 성공한다.
- **단순 요청은 프리플라이트가 없다** — 그래서 **보내고, 응답을 받은 뒤** CORS check 를 한다(25편). 막히는 것은 그 뒤의 읽기다.

### 8. 새 주소마다 다시 묻는다 · `Origin: null` · 프리플라이트는 따라가지 않는다

**출력**

```text
$ python3 wa28b-net.py console wa28b-28-redirect.html
가. 본 요청이 307 → 같은 B 의 다른 주소 → then · status 200 · redirected=true · url 의 경로 = /cors?id=r1-2
나. 본 요청이 307 → 페이지의 출처 A → then · status 200 · redirected=true · url 의 경로 = /cors?id=r2-2
다. 프리플라이트가 307 → catch · TypeError 「Failed to fetch」
--- 콘솔 ---
javascript · error · Access to fetch at 'http://127.0.0.1:<B>/cors?id=r3&pf=redirect' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: Redirect is not allowed for a preflight request.
network · error · Failed to load resource: net::ERR_FAILED
--- 서버 로그 ---
B OPTIONS /cors?id=r1&redir=B  Origin=http://127.0.0.1:<A> · Access-Control-Request-Method=PUT · Access-Control-Request-Headers=x-a
B PUT /cors?id=r1&redir=B  Origin=http://127.0.0.1:<A> · Content-Type=text/plain;charset=UTF-8 · X-A=1 · 본문 1바이트 → 처리하지 않고 307 을 보냈다
B OPTIONS /cors?id=r1-2  Origin=http://127.0.0.1:<A> · Access-Control-Request-Method=PUT · Access-Control-Request-Headers=x-a
B PUT /cors?id=r1-2  Origin=http://127.0.0.1:<A> · Content-Type=text/plain;charset=UTF-8 · X-A=1 · 본문 1바이트 → 처리했다
B OPTIONS /cors?id=r2&redir=A  Origin=http://127.0.0.1:<A> · Access-Control-Request-Method=PUT · Access-Control-Request-Headers=x-a
B PUT /cors?id=r2&redir=A  Origin=http://127.0.0.1:<A> · Content-Type=text/plain;charset=UTF-8 · X-A=1 · 본문 1바이트 → 처리하지 않고 307 을 보냈다
A OPTIONS /cors?id=r2-2  Origin=null · Access-Control-Request-Method=PUT · Access-Control-Request-Headers=x-a
A PUT /cors?id=r2-2  Origin=null · Content-Type=text/plain;charset=UTF-8 · X-A=1 · 본문 1바이트 → 처리했다
B OPTIONS /cors?id=r3&pf=redirect  Origin=http://127.0.0.1:<A> · Access-Control-Request-Method=PUT · Access-Control-Request-Headers=x-a
(exit 0)
```

- **본 요청의 307 은 따라가고, 새 주소에 OPTIONS 가 또 온다**(가). **다른 출처를 거쳐 A 로 돌아오면 A 가 받은 `Origin` 은 `null`**(나 — 명세의 redirect-taint).
- **프리플라이트가 307 이면 실패**(다) — 콘솔 「Redirect is not allowed for a preflight request.」, 서버에는 OPTIONS 한 줄.

### 9. Go 는 그냥 읽는다 — CORS 는 페이지를 위한 규칙이다

**출력**

```text
$ python3 wa28b-net.py go wa28b-28-client.go
status 200 · Access-Control-Allow-Origin="" · 본문 {"cors":"ok"}
(go run exit 0)
--- 서버 로그 ---
B POST /cors?acao=none&id=go  Origin=(없음) · Content-Type=text/plain · X-A=(없음) · 본문 11바이트 → 처리했다
(exit 0)
```

- **`status 200` · 본문을 읽었다** — 허용 헤더가 없다는 것이 Go 에게는 아무 뜻도 없다. `Origin` 도 안 붙는다.
- ★★ CORS 는 **브라우저가 「다른 출처의 페이지」에게 응답을 보여 줄지**를 정하는 규칙이다. **서버를 지키는 장치가 아니다** — 서버는 `Origin`·토큰으로 스스로 막아야 한다([`../../security/`](../../security/) 가 정본 자리지만 CORS·CSRF 절은 아직 없다).

### 10. 다른 주제와 잇기

- **[30번 주제](../30-request-body-and-content-type/3-answer.md)** — `JSON.stringify` 만 넘긴 본문은 **`text/plain;charset=UTF-8`** 이었다. 다른 출처로 `POST` 하면 문항 1의 **「`POST` · `text/plain` · 헤더 없음」 칸 — 프리플라이트가 안 붙는 칸**이다. 「JSON API 는 프리플라이트가 지켜 준다」가 여기서 깨진다.
- **도구가 못 보는 것** — ① **프리플라이트가 드는 시간**(줄 수만 봤다) ② **HTTP/2 서버에서의 스트림 업로드**(이 서버는 HTTP/1.1) · `Max-Age` 상한.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · Python 3 표준 라이브러리 `http.server`(서버 A·B, IPv4·IPv6) · Go 1.27.1(대비). **엔진은 Chrome 하나다.**

★ **하네스** — [24번 주제](../24-document-lifecycle-events/2-summary.md)의 (1)을 `import` 하고 서버만 새로 세웠다 — 전문은 [2-summary.md](2-summary.md)의 (1).\
★ **격자는 페이지가 서버에게 묻는다**(`/seen`) — 페이지는 프리플라이트를 못 보기 때문이다.

```sh
# wa28b-28-rerun.sh
# 이 편의 블록을 다시 던지는 법 — 스크래치패드의 src 에서
python3 wa28b-net.py quiet wa28b-28-grid.html
python3 wa28b-net.py console wa28b-28-edge.html
python3 wa28b-net.py console wa28b-28-answers.html
for k in 1 2 3; do python3 wa28b-net.py quiet wa28b-28-maxage.html; done
python3 wa28b-net.py page wa28b-28-expose.html
python3 wa28b-net.py page wa28b-28-nocors.html
python3 wa28b-net.py console wa28b-28-redirect.html
python3 wa28b-net.py go wa28b-28-client.go
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 프리플라이트 격자 32칸 | 캡처 3판 | 동작 방식 (2) · A1 |
| 격자 밖 여덟 칸 | 캡처 3판 | 동작 방식 (3) · A2 |
| 프리플라이트 답 셋 + 콘솔 + 서버 로그 | 캡처 3판 | 동작 방식 (4) · A3 · A7 |
| `Max-Age` | 캡처 3판 × 블록 안 3판 | 동작 방식 (5) · A4 |
| 노출 헤더 · `no-cors` · 리다이렉트 | 캡처 3판 | 동작 방식 (6)\~(8) · A5 · A6 · A8 |
| Go 대비 | 캡처 3판 | 동작 방식 (9) · A9 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| HTTP/1.1 로의 스트림 본문 | 안 보냄(`ERR_ALPN_NEGOTIATION_FAILED`) | 명세 문장이 아니라 Chrome 의 선택 |
| 콘솔의 CORS 문구 | 거부 이유마다 다른 문장 | 개발자 도구의 글자 |
| `Max-Age` 없음의 캐시 | 5초 안의 두 번째는 캐시 | 명세 기본값이지만 **시간에 기댄 칸** |

**안 돌려 본 것** — ① Firefox·Safari(엔진이 없다). ② `HEAD` · `Allow-Methods: *`. ③ HTTP/2 서버.

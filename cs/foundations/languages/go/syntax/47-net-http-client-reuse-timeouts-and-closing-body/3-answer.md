# go/syntax/47 — `net/http` 클라이언트: `Client` 재사용·타임아웃·`Body` 닫기 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다(4번은 `go1.25.12` 판을 나란히). 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★ **근거로 읽을 칸** — 「1초 안에 돌아왔나」 참/거짓 · 에러 문구 · 새 연결 수 · `Reused` · 상태 코드 · 서버가 받은 요청 수.
> **가린 칸** — 서버 포트(`<포트>`). **칸으로 안 만든 것** — 경과 시간.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `http.Get` 은 둘 다 `false`·`<nil>` · `Client.Timeout`·`context` 는 둘 다 `true`(헤더면 `Get`, 본문이면 `ReadAll` 에서) · `ResponseHeaderTimeout` 은 `/slowhead` 만 `true` — 서버 `8 / 8`·취소 5 · **`5 / 8`**

**출력**

```text
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && ./prog > rows.txt; rc=$?; awk -F"\t" "/^\// && NF!=6 {bad=1} END {exit bad}" rows.txt || echo "칸 수 어긋남"; cat rows.txt; echo "prog exit=$rc" =====
vet exit=0
/slowhead	http.Get	1초 안에 돌아왔나=false	ReadAll err=<nil>	Is(DeadlineExceeded)=false	net.Error.Timeout()=false
/slowhead	Client{Timeout: 200ms}	1초 안에 돌아왔나=true	Get err=Get "http://127.0.0.1:<포트>/slowhead": context deadline exceeded (Client.Timeout exceeded while awaiting headers)	Is(DeadlineExceeded)=true	net.Error.Timeout()=true
/slowhead	context.WithTimeout(200ms)	1초 안에 돌아왔나=true	Get err=Get "http://127.0.0.1:<포트>/slowhead": context deadline exceeded	Is(DeadlineExceeded)=true	net.Error.Timeout()=true
/slowhead	Transport{ResponseHeaderTimeout: 200ms}	1초 안에 돌아왔나=true	Get err=Get "http://127.0.0.1:<포트>/slowhead": net/http: timeout awaiting response headers	Is(DeadlineExceeded)=true	net.Error.Timeout()=true
/slowbody	http.Get	1초 안에 돌아왔나=false	ReadAll err=<nil>	Is(DeadlineExceeded)=false	net.Error.Timeout()=false
/slowbody	Client{Timeout: 200ms}	1초 안에 돌아왔나=true	ReadAll err=context deadline exceeded (Client.Timeout or context cancellation while reading body)	Is(DeadlineExceeded)=true	net.Error.Timeout()=true
/slowbody	context.WithTimeout(200ms)	1초 안에 돌아왔나=true	ReadAll err=context deadline exceeded	Is(DeadlineExceeded)=true	net.Error.Timeout()=true
/slowbody	Transport{ResponseHeaderTimeout: 200ms}	1초 안에 돌아왔나=false	ReadAll err=<nil>	Is(DeadlineExceeded)=false	net.Error.Timeout()=false
서버 — 핸들러가 끝까지 돈 요청 8 / 8 · 그중 끝날 때 r.Context() 가 취소돼 있던 요청 5
1초 안에 돌아온 칸 5 / 8
prog exit=0
(exit 0)
```

**왜 그런가**

- ★★★ 문서 「**A Timeout of zero means no timeout**」 — `http.Get` 은 `DefaultClient`(제로값)라 1.5 초를 다 기다렸다.
- ★★★ `Client.Timeout` 은 「includes … reading the response body」 — **`Get` 이 돌아온 뒤에도** `ReadAll` 을 끊었다. `context` 도 요청이 끝날 때까지 살아 있어 같은 구간을 지킨다.
- ★★ 타임아웃 난 다섯 칸은 `Is(DeadlineExceeded)` 와 `net.Error.Timeout()` 이 **전부 `true`**.

### 2. `ResponseHeaderTimeout` 은 **응답 헤더가 올 때까지만** 잰다 — `/slowbody` 는 헤더가 바로 와서 그 시계가 끝났다 · `Client.Timeout` 은 **본문을 다 읽을 때까지** 잰다

- ★★★ 같은 「200 ms」가 **다른 구간**을 잰다 — 설정이 틀린 것이 아니라 **기준이 다르다**(제5의 상태).
- ★★ 그래서 `Transport` 의 세부 타임아웃만으로는 **느린 본문**을 못 막는다 — 전체 상한은 `Client.Timeout` 이나 `context` 다.

### 3. 문구는 **설정마다 다르고 판을 탈 수 있다** — `errors.Is(err, context.DeadlineExceeded)` 나 `errors.As` 로 꺼낸 `net.Error` 의 `Timeout()` 으로 가른다 · 34번의 `Err()` 가 **`*url.Error` 에 감겨** 올라온 것이다

- ★★★ 1번 — 문구 셋(`Client.Timeout exceeded …` · `context deadline exceeded` · `timeout awaiting response headers`)이 **두 판별에서 전부 `true`**.
- ★★ [34번 주제](../34-context-cancellation-deadlines-and-values/) (2)절 — 시간 초과의 `Err()` 는 `context deadline exceeded` 이고 `errors.Is(…, DeadlineExceeded)` 가 참이다. HTTP 클라이언트는 그 에러를 **`Get "…":` 접두어로 감싸** 돌려준다([24번 주제](../24-error-wrapping-and-errors-is-as-join/)의 사슬 — 그래서 `Is` 가 닿는다).

### 4. `go1.27.1` — 읽고닫음·읽기만·매번 `Client{}` 는 **1**(`Reused` 9) · 둘 다 안 함·매번 `Transport` 는 **10**(0) · 닫기만은 **100 B 가 1 · 1 MiB 가 10** — `go1.25.12` 는 **「닫기만 · 100 B」 한 줄만** `10` 으로 다르다(`1 / 12`)

**출력**

```text
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o p127 . && "$GO125" build -trimpath -o p125 . || exit 1; ./p127 > a.txt && ./p125 > b.txt || exit 1; echo "── go1.27.1 판 마지막 줄: $(tail -1 a.txt)"; echo "── go1.25.12 판 마지막 줄: $(tail -1 b.txt)"; printf "본문 크기\t다루는 법\t새 연결(1.27.1)\tReused(1.27.1)\t새 연결(1.25.12)\n"; paste a.txt b.txt | sed "1d;\$d" | awk -F"\t" "NF!=8 || \$1!=\$5 || \$2!=\$6 {bad=1} {printf \"%s\t%s\t%s\t%s\t%s\n\", \$1, \$2, \$3, \$4, \$7; m++; if (\$3!=\$7) n++} END {if (bad) print \"칸 수 어긋남\"; printf \"1.27.1 과 1.25.12 의 새 연결 수가 갈린 칸 %d / %d\n\", n, m}" =====
vet exit=0
── go1.27.1 판 마지막 줄: 새 연결 10개인 칸 5 / 12
── go1.25.12 판 마지막 줄: 새 연결 10개인 칸 6 / 12
본문 크기	다루는 법	새 연결(1.27.1)	Reused(1.27.1)	새 연결(1.25.12)
100	끝까지 읽고 닫음	1	9	1
100	닫기만	1	9	10
100	끝까지 읽기만	1	9	1
100	둘 다 안 함	10	0	10
100	요청마다 &http.Client{}	1	9	1
100	요청마다 새 Transport	10	0	10
1048576	끝까지 읽고 닫음	1	9	1
1048576	닫기만	10	0	10
1048576	끝까지 읽기만	1	9	1
1048576	둘 다 안 함	10	0	10
1048576	요청마다 &http.Client{}	1	9	1
1048576	요청마다 새 Transport	10	0	10
1.27.1 과 1.25.12 의 새 연결 수가 갈린 칸 1 / 12
(exit 0)
```

- ★★★ 1.27.1 은 닫힌 본문을 **256 KiB 까지 대신 읽어** 연결을 살린다(`maxPostCloseReadBytes`). 1 MiB 는 한도를 넘어 버려졌고, 1.25.12 에는 그 동작이 **없다**(`transport.go` 에 그 이름 0 줄).
- ★★ 서버 창의 새 연결 수와 클라이언트 창의 `Reused` 가 **12줄 전부** 맞물렸다(1 ↔ 9 · 10 ↔ 0).

### 5. 연결은 **`EOF` 를 읽는 순간** 풀로 돌아간다 — `Close` 가 계기가 아니다 · 그래도 **`Close` 는 빼지 않는다** — 문서는 「read to EOF **and** closed」를 적고, 닫을 책임이 호출한 쪽에 있다고 적는다

- ★★★ 4번 — 「끝까지 읽기만」 줄이 **두 판·두 크기 모두 1**.
- ★★ 읽다가 에러가 나면 `EOF` 에 못 닿는다 — 그때 닫지 않으면 「둘 다 안 함」(10)과 같아진다. `defer res.Body.Close()` 는 **그 모든 길을 덮는 한 줄**이다.

### 6. 연결 풀은 **`Transport` 에 산다** — `&http.Client{}` 는 `Transport` 가 `nil` 이라 **`DefaultTransport` 를 같이 쓴다**(1) · 새 `Transport` 는 **새 풀**(10) · 문서의 「Clients should be reused」의 이유가 「**The Client.Transport typically has internal state (cached TCP connections)**」다

- ★★★ 재사용해야 하는 것은 **`Transport`** 다. 타임아웃이 다른 `Client` 여럿이 **`Transport` 하나를 나눠 써도** 된다.

### 7. `200`·`404`·`500` 은 전부 **`err=<nil>`** · 닫힌 서버만 **`connection refused`**

**출력**

```text
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && ./prog =====
vet exit=0
http://127.0.0.1:<포트>/200        err=<nil> · StatusCode=200 · Status="200 OK" · 본문="ok"
http://127.0.0.1:<포트>/404        err=<nil> · StatusCode=404 · Status="404 Not Found" · 본문="404 page not found\n"
http://127.0.0.1:<포트>/500        err=<nil> · StatusCode=500 · Status="500 Internal Server Error" · 본문="oops\n"
http://127.0.0.1:<포트>/200        err=Get "http://127.0.0.1:<포트>/200": dial tcp 127.0.0.1:<포트>: connect: connection refused
(exit 0)
```

- ★★★ 문서 「**A non-2xx status code doesn't cause an error**」 — 에러는 「failure to speak HTTP」일 때다.

### 8. **같은 선을 긋는다** — `fetch` 도 404·500 이 `then`(`res.ok` 만 거짓)이고 `catch` 는 **네트워크 오류**일 때뿐이었다(`catch` 로 간 칸 2 / 6)

- ★★ [web-api 25번](../../../../web-api/25-fetch-request-response/) — 「`fetch` 는 응답이 오면 이행한다」. Go 의 `err` 와 JS 의 `catch` 가 **둘 다 「응답을 못 받았나」만** 말한다. 상태 코드는 **따로** 본다.

### 9. 기본 — `res==nil=false` · `Get "/r/10": stopped after 10 redirects` · `10` · `CheckRedirect` 3 — `false` · `Get "/r/3": 세 번째에서 멈춤` · `3` · `ErrUseLastResponse` — `err=<nil>` · `302` · `Location=/r/1` · `1`

**출력**

```text
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && ./prog =====
vet exit=0
[기본 Client] res==nil=false · err=Get "/r/10": stopped after 10 redirects · 서버가 받은 요청 10
[CheckRedirect 3] res==nil=false · err=Get "/r/3": 세 번째에서 멈춤 · 서버가 받은 요청 3
[ErrUseLastResponse] err=<nil> · StatusCode=302 · Location=/r/1 · 서버가 받은 요청 1
(exit 0)
```

- ★★★ 문서 — 기본 정책은 「stop after 10 consecutive requests」, 그리고 「A non-nil Response with a non-nil error **only occurs when CheckRedirect fails**」(본문은 이미 닫혀 있다).

### 10. 서버는 **끝까지 처리했다**(`8 / 8`) — 취소를 안 봤을 뿐 `r.Context()` 는 **5개가 취소돼 있었다** · web-api 27번과 **같은 결론** · 멈추려면 핸들러가 **`r.Context().Done()`/`Err()`** 를 봐야 한다

- ★★★ 클라이언트의 타임아웃은 **클라이언트 쪽 기다림**을 끝낼 뿐이다. [web-api 27번](../../../../web-api/27-abort-and-timeout/) — 「취소는 요청을 없던 일로 만들지 않는다」(서버에서 끝까지 처리된 칸 6 / 7).
- ★★ 서버는 연결이 끊기면 `r.Context()` 를 **취소해 준다**(취소 5 — 타임아웃 난 칸도 5 다. 칸마다 짝을 맞춰 보지는 않았다) — 그것을 [34번 주제](../34-context-cancellation-deadlines-and-values/)의 취소 나무처럼 **아래 호출로 넘기는 것**은 핸들러의 몫이다. ★ 이 문서는 그렇게 고친 핸들러를 **안 던졌다.**

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 로 **★고칠 것 0** |
| ★★★ 새 연결 격자 (`t47body`) | 10 요청 × 법 6 × 크기 2 · 서버 `ConnState` + `GotConn.Reused` · **두 툴체인** · `paste` 후 탭 8칸 검사 | 캡처마다 | **`5 / 12` · `6 / 12` · 갈린 칸 `1 / 12`** |
| ★★★ 타임아웃 격자 (`t47timeout`) | 서버 2 × 법 4 · 「1초 안에」 참/거짓 · 서버 완료·취소 수 | 캡처마다 | **`5 / 8`** · 서버 `8 / 8`·취소 5 |
| ★★ 상태·리다이렉트 (`t47status`·`t47redirect`) | 포트 가림 · 서버가 받은 요청 수 | 캡처마다 | 비-2xx `err=<nil>` · 10 |

**구현·환경에 달린 항목**

| 항목 | 무엇에 달렸나 |
|---|---|
| 타임아웃 0 = 없음 · 비-2xx 는 에러 아님 · 리다이렉트 10 · 응답+에러 | **표준 라이브러리 문서의 계약** |
| 닫힌 본문 자동 비우기(256 KiB) | **판에 달린 구현** — 1.27.1 에 있고 1.25.12 에 없다 |
| `EOF` 에서 연결 반환 | **관찰**(두 판) |
| 비우기가 비동기 | **1.27.1 문서의 「asynchronously」** — 그래서 요청 사이 20 ms 를 쉬었다 |
| 포트 | **실행마다** — 소스에서 가렸다 |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다(기본 규칙만). `GO125` 가 가리키는 `go1.25.12` 툴체인이 있어야 4번이 돈다. 외부 네트워크는 필요 없다.

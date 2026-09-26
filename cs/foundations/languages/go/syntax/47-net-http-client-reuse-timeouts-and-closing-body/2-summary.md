# go/syntax/47 — `net/http` 클라이언트: `Client` 재사용·타임아웃·`Body` 닫기 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [`net/http`](https://pkg.go.dev/net/http) 패키지 문서(`go doc net/http.Client` · `Client.Do` · `Response`) · `net/http/transport.go` 소스(이 툴체인의 것). **이 툴체인에서 직접 떴다.**\
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.
> ★ **네트워크는 `localhost` 만** 썼다 — 서버는 `httptest.NewServer`(`127.0.0.1` 의 빈 포트)이고 외부로 나가는 요청은 없다.
> ★★ 판 격자에는 모듈 캐시에 있던 **`go1.25.12`** 를 같이 썼다(머리말 `tools` — 명령에는 `"$GO125"` 로 찍힌다).\
> **버전** — ★★★ **`Body` 를 닫기만 해도 작은 본문을 비워 연결을 돌려주는 동작은 1.25.12 에 없고 1.27.1 에 있다**((3)절 — 문서 문장도 판마다 다르다). 그 사이 어느 판에서 들어왔는지는 **확인하지 않았다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체는 넷째 창이다** — 「**서버가 본 새 연결 수** — 같은 서버에 요청 10번 × 본문을 다루는 법 6(끝까지 읽고 닫음 · 닫기만 · 끝까지 읽기만 · 둘 다 안 함 · 요청마다 `&http.Client{}` · 요청마다 새 `Transport`) × 본문 크기 2(100 B · 1 MiB)를 **서버의 `ConnState` 훅으로** 센 것」.
마지막 줄 「**1.27.1 과 1.25.12 의 새 연결 수가 갈린 칸 1 / 12**」와 두 판의 「**새 연결 10개인 칸 5 / 12 · 6 / 12**」((3)절). ★★★ **「끝까지 읽기만」 한 칸은 닫지 않아도 1 연결이다 — 연결을 돌려주는 것은 `Close` 가 아니라 `EOF` 였다.**
★★ 짝이 되는 창은 「**타임아웃 격자**」 — 느린 서버 2 × 기다리는 법 4 → **「1초 안에 돌아왔나」 참/거짓**, 「**1초 안에 돌아온 칸 5 / 8**」((2)절). ★★★ **`http.Get` 은 두 서버 다 `false`** — 기본 `Client` 에 타임아웃이 없다.

★★★ **이 주제의 경계** — **재시도·백오프 정책**(언제 다시 걸고 얼마나 기다리나)은 [`ops-patterns/01-retry-backoff`](../../../../../ops-patterns/01-retry-backoff/)가 정본이다 — 여기서는 **`Client` 필드와 자원 반납**으로 좁힌다. ★ 타임아웃 값을 **계층마다 어떻게 나누나**(타임아웃 예산)는 [server-design 06 §2 타임아웃](../../../../../systems/server-design/06-resilience.md)에 있다.
`context` 의 취소가 **호출 나무를 따라 내려가는 것**과 `DeadlineExceeded` 는 [34번 주제](../34-context-cancellation-deadlines-and-values/) (1)·(2)절이 정본이다 — 여기서는 그것이 **HTTP 요청에 걸렸을 때의 에러 모양**만 본다. 서버 쪽 `Handler` 는 [46번 주제](../46-net-http-server-servemux-patterns-handler-and-middleware/)다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 이 주제에서 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | ★ 거의 없다 — 이 주제는 **표준 라이브러리 계약**이 본체다 |
| **표준 라이브러리 계약** | `go doc` 이 적은 것 | ★★★ 「**A Timeout of zero means no timeout**」 · `DefaultClient` 는 제로값 `Client` · **「Clients should be reused」** · 「**A non-2xx status code doesn't cause an error**」 · `Body` 는 **닫을 책임이 호출한 쪽** · 리다이렉트는 **10번에서 멈춘다**(「stop after 10 consecutive requests」) · 한도에 걸리면 **응답과 에러가 같이** 온다 |
| **구현** | 이 판 소스·출력 | ★★ **닫힌 본문을 256 KiB 까지 비우는 `maxPostCloseReadBytes`**(1.27.1 에 있고 1.25.12 에 없다) · 에러 문구 전부 |

★★★ **선을 긋는다** — 「`Body` 를 닫아라」는 **계약**이다. 「닫기만 해도 재사용된다」는 **이 판 구현의 성질**이고 **본문 크기에 달렸다**(1 MiB 는 안 됐다). ★★★ **「커넥션을 재사용하면 빠르다」는 이 문서에 없다** — 연결 **수**만 셌다.

## 이 판

```text
===== 명령: go version; "$GO125" version; node --version =====
go version go1.27.1 linux/amd64
go version go1.25.12 linux/amd64
v18.19.1
(exit 0)
```

```text
===== 명령: go doc net/http.Client | sed -n "21,22p;36,42p;53,58p"; go doc net/http.Get | sed -n "22p" =====
	// If CheckRedirect is nil, the Client uses its default policy,
	// which is to stop after 10 consecutive requests.
	// Timeout specifies a time limit for requests made by this
	// Client. The timeout includes connection time, any
	// redirects, and reading the response body. The timer remains
	// running after Get, Head, Post, or Do return and will
	// interrupt reading of the Response.Body.
	//
	// A Timeout of zero means no timeout.
    A Client is an HTTP client. Its zero value (DefaultClient) is a usable
    client that uses DefaultTransport.

    The Client.Transport typically has internal state (cached TCP connections),
    so Clients should be reused instead of created as needed. Clients are safe
    for concurrent use by multiple goroutines.
    Get is a wrapper around DefaultClient.Get.
(exit 0)
```

```text
===== 명령: go doc net/http.Client.Do | sed -n "7,24p" =====
    An error is returned if caused by client policy (such as CheckRedirect),
    or failure to speak HTTP (such as a network connectivity problem). A non-2xx
    status code doesn't cause an error.

    If the returned error is nil, the Response will contain a non-nil Body
    which the user is expected to close. If the Body is not both read to EOF and
    closed, the Client's underlying RoundTripper (typically Transport) may not
    be able to re-use a persistent TCP connection to the server for a subsequent
    "keep-alive" request. Note, however, that Transport will automatically try
    to read a Response Body to EOF asynchronously up to a conservative limit
    when a Body is closed.

    The request Body, if non-nil, will be closed by the underlying Transport,
    even on errors. The Body may be closed asynchronously after Do returns.

    On error, any Response can be ignored. A non-nil Response with a non-nil
    error only occurs when CheckRedirect fails, and even then the returned
    Response.Body is already closed.
(exit 0)
```

```text
===== 명령: echo "── go1.27.1 ──"; go doc net/http.Response | sed -n "27,35p"; echo "── go1.25.12 ──"; "$GO125" doc net/http.Response | sed -n "27,32p" =====
── go1.27.1 ──
	// The http Client and Transport guarantee that Body is always
	// non-nil, even on responses without a body or responses with
	// a zero-length body. It is the caller's responsibility to
	// close Body. The default HTTP client's Transport may not
	// reuse HTTP/1.x "keep-alive" TCP connections if the Body is
	// not read to completion and closed; however, manually reading
	// the body to completion should not be needed in most cases,
	// as closing the body will also cause the body to be read to
	// completion asynchronously, up to a conservative limit.
── go1.25.12 ──
	// The http Client and Transport guarantee that Body is always
	// non-nil, even on responses without a body or responses with
	// a zero-length body. It is the caller's responsibility to
	// close Body. The default HTTP client's Transport may not
	// reuse HTTP/1.x "keep-alive" TCP connections if the Body is
	// not read to completion and closed.
(exit 0)
```

```text
===== 명령: echo "1.27.1 transport.go 의 maxPostCloseReadBytes 줄 수: $(grep -c maxPostCloseReadBytes "$(go env GOROOT)/src/net/http/transport.go")"; echo "1.25.12 transport.go 의 maxPostCloseReadBytes 줄 수: $(grep -c maxPostCloseReadBytes "$("$GO125" env GOROOT)/src/net/http/transport.go")"; sed -n "2417,2420p;2605,2609p" "$(go env GOROOT)/src/net/http/transport.go" =====
1.27.1 transport.go 의 maxPostCloseReadBytes 줄 수: 4
1.25.12 transport.go 의 maxPostCloseReadBytes 줄 수: 0
// maxPostCloseReadBytes is the max number of bytes that a client is willing to
// read when draining the response body of any unread bytes after it has been
// closed. This number is chosen for consistency with maxPostHandlerReadBytes.
const maxPostCloseReadBytes = 256 << 10
			tryDrain := !bodyEOF && resp.ContentLength <= maxPostCloseReadBytes
			if tryDrain {
				eofc <- struct{}{}
				bodyEOF = maybeDrainBody(body.body)
			}
(exit 0)
```

- ★★★ **두 판의 문서가 다르다** — 1.25.12 는 「may not reuse … if the Body is not read to completion and closed」**에서 끝나고**, 1.27.1 은 「**closing the body will also cause the body to be read to completion asynchronously, up to a conservative limit**」를 **덧붙였다.** 그 「limit」이 소스의 `maxPostCloseReadBytes = 256 << 10` 이고, **1.25.12 의 `transport.go` 에는 그 이름이 0 줄**이다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다 — 출력 전에 가렸다** | ★★ **서버 포트** | 소스가 `127.0.0.1:<포트>` 로 **바꿔서** 찍는다 |
| **흔들린다 — 칸으로 안 만들었다** | ★★★ **경과 시간** | 「**1초 안에 돌아왔나**」 참/거짓으로만 찍었다(서버는 1.5 초 쉬고, 타임아웃은 200 ms) |
| 안 흔들린다 | ★★★ **새 연결 수 · `Reused` 수 · `5 / 12`·`6 / 12`·`1 / 12` · `5 / 8`** | 재대조 두 판에서 같았다 — ★ **요청 사이에 20 ms 쉰 판**이다(아래) |
| 안 흔들린다 | 에러 문구 · 상태 코드 · 서버가 받은 요청 수 | |

★★ **요청 사이 20 ms 쉼은 흔들림을 없애려고 넣었다** — 1.27.1 의 「닫기만 · 100 B」 칸은 **비우기가 비동기**라(문서의 「asynchronously」) 쉬지 않은 첫 판들에서 **1 과 2 가 번갈아** 나왔다. 다음 요청이 **연결이 풀에 돌아오기 전에** 나가면 새 연결을 판다.
★ 정규화 규칙은 **기본 넷**만 썼다.

## 한눈에 — 쉽게 말하면

**`http.Client` 는 「택시 회사」, `Transport` 는 「차고」, 연결은 「택시」다.** 손님(요청)을 태워 보내고, 택시가 **차고로 돌아와야** 다음 손님이 **같은 택시**를 탄다.
택시가 돌아오는 조건은 **「손님이 짐을 다 내렸다(본문을 `EOF` 까지 읽었다)」** 다. 짐을 **다 안 내리고 문만 닫으면(`Close`)** — 짐이 작으면 기사가 **대신 내려 주고** 돌아오지만(1.27.1), 짐이 크거나 옛 회사(1.25.12)면 **택시를 폐차**하고 다음 손님에게 **새 택시**를 판다.
그리고 **기본 택시 회사(`DefaultClient`)는 「목적지에 못 가면 돌아와라」는 시간 제한이 없다** — 손님이 아무리 기다려도 안 끝난다.

| 비유 | 실체 |
|---|---|
| 택시 회사 | ★★ **`http.Client`** — 타임아웃·리다이렉트·쿠키 정책 |
| 차고 | ★★★ **`http.Transport`** — **연결 풀**이 여기 산다. `&http.Client{}` 는 **기본 차고(`DefaultTransport`)를 같이 쓴다**((3)절) |
| 짐을 다 내림 | ★★★ **본문을 `EOF` 까지 읽음** — 닫지 않아도 연결이 돌아온다 |
| 문만 닫음 | ★★ **`Close` 만** — 작은 짐은 기사가 대신 내림(1.27.1 · ≤ 256 KiB) |
| 시간 제한 없는 회사 | ★★★ **`http.Get`·`http.DefaultClient`** — `Timeout` 이 0 |
| 「이 주소 아닙니다」 쪽지 | ★★★ **404·500** — **택시는 무사히 돌아왔다**(`err == nil`)((4)절) |

```text
   ★★★ 연결이 풀로 돌아가는 조건 — 이 문서가 센 것

   Do(req) ─▶ [ 연결 ] ─▶ 응답 헤더 ─▶ res.Body
                                      │
             ┌──── 끝까지 읽음(EOF) ───┴──────────────▶ 풀로 돌아감   (닫기 안 해도 1 연결)
             ├──── Close 만 ── 본문 ≤ 256 KiB ──(1.27.1)─▶ 대신 비우고 돌아감
             │                 본문 > 256 KiB ─────────▶ 연결을 닫음 (새 연결 10)
             └──── 둘 다 안 함 ────────────────────────▶ 연결이 붙들림 (새 연결 10)
```

> **`http.Transport`** — 실제로 TCP 연결을 열고, **다 쓴 연결을 풀에 넣어 두었다가** 같은 호스트의 다음 요청에 다시 쓰는 부분.

> **keep-alive(연결 유지)** — HTTP/1.1 에서 응답 하나가 끝난 뒤에도 **TCP 연결을 닫지 않고** 다음 요청에 쓰는 것.

## 이 주제가 답하려는 질문

1. **타임아웃을 안 걸면 무엇이 일어나나** — 네 가지 걸기가 **어느 단계**를 막나.
2. **무엇을 해야 연결이 재사용되나** — 읽기·닫기·`Client` 만들기의 조합.
3. **무엇이 에러이고 무엇이 에러가 아닌가** — 상태 코드·연결 거부·리다이렉트.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **서버가 본 새 연결 수 — 10 요청 × 다루는 법 6 × 크기 2 × 판 2** | 연결이 **돌아왔나** | ★ 본체 창 · 서버 `ConnState` 가 `StateNew` 를 센다 · 스크립트가 **탭 8칸**을 검사하고 판 사이 갈린 칸을 센다 |
| ★★ **클라이언트 쪽 `httptrace.GotConn` 의 `Reused`** | 같은 질문을 **클라이언트 창**으로 | (3)절 — 서버 창과 **한 칸도 안 어긋났다**(1 연결 ↔ `Reused` 9) |
| ★★★ **타임아웃 격자 — 느린 서버 2 × 기다리는 법 4 → 참/거짓·에러** | 어느 설정이 **어느 단계**를 막나 | (2)절 |
| ★★ **에러 대 상태 코드** | 무엇이 `err` 인가 | (4)·(5)절 |
| ★★ **제5의 상태 — 「기준만 다른 것」** | ★★★ **`ResponseHeaderTimeout: 200ms` 가 `/slowbody` 에서는 `false`(1.5 초 기다림)** — 설정은 틀리지 않았다. 이름 그대로 **「응답 헤더」까지만** 잰다. 헤더를 바로 보내고 본문을 늦게 보내는 서버에는 **그 시계가 이미 멈춘 뒤**다. **같은 「200ms 타임아웃」이 다른 구간을 잰다** | (2)절 |
| **부적용 — 속도** | ★★★ **「연결 재사용이 빠르다」·「`Client` 를 새로 만들면 느리다」는 주장하지 않는다** — 시간은 한 번도 안 쟀다. 연결 **수**만 셌다 | 규칙 4 |
| **못 잰 것 — 누수 고루틴·파일 디스크립터 수** | 「둘 다 안 함」이 붙든 연결의 **고루틴·fd 수**는 판마다 흔들릴 수 있어 **싣지 않았다** | — |
| **못 잰 것 — HTTP/2** | `httptest.NewServer` 는 HTTP/1.1 이다. HTTP/2 의 한 연결 다중화에서 「새 연결 수」의 뜻은 다르다 — **안 돌렸다** | — |

### (1) ★ `Client` 의 기본값 — 문서가 먼저 말한다

`t47cdoc` 의 두 문장이 이 주제의 절반이다 — **「A Timeout of zero means no timeout」**, 그리고 **`DefaultClient` 는 제로값 `Client`** 다. `http.Get` 은 「**a wrapper around DefaultClient.Get**」이므로 **시간 제한이 없다.**
★★ 「Clients should be reused instead of created as needed」의 이유도 같은 곳에 있다 — **「The Client.Transport typically has internal state (cached TCP connections)」**. 재사용해야 하는 것은 **`Client` 라기보다 `Transport`** 다((3)절의 `&http.Client{}` 칸).

### (2) ★★★ 타임아웃 격자 — 느린 서버 2 × 기다리는 법 4

**언제 쓰나** — 외부 API 를 부르는 코드에 **시간 제한을 처음 걸 때.**

```text
===== 소스: t47timeout.go =====
package main

import (
	"context"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync/atomic"
	"time"
)

const wait = 1500 * time.Millisecond

func main() {
	var done, canceled atomic.Int64
	finish := func(r *http.Request) {
		done.Add(1)
		if r.Context().Err() != nil {
			canceled.Add(1)
		}
	}
	mux := http.NewServeMux()
	mux.HandleFunc("/slowhead", func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(wait) // 응답 헤더를 보내기 전에 쉰다
		io.WriteString(w, "late")
		finish(r)
	})
	mux.HandleFunc("/slowbody", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(200)
		w.(http.Flusher).Flush() // 헤더는 바로 보낸다
		time.Sleep(wait)
		io.WriteString(w, "late")
		finish(r)
	})
	srv := httptest.NewServer(mux)
	mask := func(err error) string {
		if err == nil {
			return "<nil>"
		}
		return strings.ReplaceAll(err.Error(), srv.URL, "http://127.0.0.1:<포트>")
	}

	var cancels []context.CancelFunc
	defer func() {
		for _, c := range cancels {
			c()
		}
	}()
	type way struct {
		name string
		get  func(url string) (*http.Response, error)
	}
	ways := []way{
		{"http.Get", func(u string) (*http.Response, error) { return http.Get(u) }},
		{"Client{Timeout: 200ms}", func(u string) (*http.Response, error) {
			return (&http.Client{Timeout: 200 * time.Millisecond}).Get(u)
		}},
		{"context.WithTimeout(200ms)", func(u string) (*http.Response, error) {
			ctx, cancel := context.WithTimeout(context.Background(), 200*time.Millisecond)
			cancels = append(cancels, cancel) // 본문을 다 읽은 뒤에 부른다
			req, _ := http.NewRequestWithContext(ctx, "GET", u, nil)
			return http.DefaultClient.Do(req)
		}},
		{"Transport{ResponseHeaderTimeout: 200ms}", func(u string) (*http.Response, error) {
			c := &http.Client{Transport: &http.Transport{ResponseHeaderTimeout: 200 * time.Millisecond}}
			return c.Get(u)
		}},
	}
	n, m := 0, 0
	for _, path := range []string{"/slowhead", "/slowbody"} {
		for _, w := range ways {
			start := time.Now()
			res, err := w.get(srv.URL + path)
			stage := "Get"
			if err == nil {
				_, err = io.ReadAll(res.Body)
				res.Body.Close()
				stage = "ReadAll"
			}
			fast := time.Since(start) < time.Second
			var ne net.Error
			isNet := errors.As(err, &ne) && ne.Timeout()
			m++
			if fast {
				n++
			}
			fmt.Printf("%s\t%s\t1초 안에 돌아왔나=%v\t%s err=%s\tIs(DeadlineExceeded)=%v\tnet.Error.Timeout()=%v\n",
				path, w.name, fast, stage, mask(err), errors.Is(err, context.DeadlineExceeded), isNet)
		}
	}
	srv.Close() // 남은 핸들러가 끝날 때까지 기다린다
	fmt.Printf("서버 — 핸들러가 끝까지 돈 요청 %d / %d · 그중 끝날 때 r.Context() 가 취소돼 있던 요청 %d\n", done.Load(), m, canceled.Load())
	fmt.Printf("1초 안에 돌아온 칸 %d / %d\n", n, m)
}
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

그림 해설 (한 단계씩):

- ★★★ **`http.Get` 은 두 서버 다 `1초 안에 돌아왔나=false` · `err=<nil>`** — 서버가 1.5 초 뒤에 답할 때까지 **그냥 기다렸다.** 서버가 영영 안 답하면 **영영 기다린다** — 기본 `Client` 에 타임아웃이 없다.
- ★★★ **`Client{Timeout: 200ms}` 는 두 서버 다 `true`** — 헤더 대기 중이면 `Get` 이 **`context deadline exceeded (Client.Timeout exceeded while awaiting headers)`**, 본문 읽는 중이면 **`ReadAll` 이** `(Client.Timeout or context cancellation while reading body)`. 문서 「**The timeout includes … reading the response body**」 — **`Get` 이 돌아온 뒤에도 시계가 돈다.**
- ★★★ **`context.WithTimeout(200ms)` 도 두 서버 다 `true`** — 에러는 **`context deadline exceeded`** 만. [34번 주제](../34-context-cancellation-deadlines-and-values/) (2)절의 `Err` 문구 그대로이고, `errors.Is(err, context.DeadlineExceeded)` 가 **`true`**([24번 주제](../24-error-wrapping-and-errors-is-as-join/)의 사슬 — `*url.Error` 가 감쌌다).
  ★ 이 `ctx` 는 요청 **하나**의 수명이다 — 34번의 취소 나무에서 **잎 하나**를 요청에 붙인 것과 같다.
- ★★★ **`Transport{ResponseHeaderTimeout: 200ms}` 는 `/slowhead` 만 `true`** — `net/http: timeout awaiting response headers`. **`/slowbody` 는 `false`**(헤더가 바로 와서 이 시계는 할 일이 끝났다) — 제5의 상태((0)절).
- ★★ **`Is(DeadlineExceeded)` 와 `net.Error.Timeout()` 이 타임아웃 난 다섯 칸에서 전부 `true`** — 문구가 셋으로 갈려도 **판별은 한 가지로** 된다. 문구로 가르지 말고 **`errors.Is` 나 `Timeout()`** 으로 가른다.
- ★★★ **서버 줄 — `핸들러가 끝까지 돈 요청 8 / 8 · 그중 끝날 때 r.Context() 가 취소돼 있던 요청 5`** — 클라이언트가 200 ms 에 떠난 **다섯 요청도 서버는 1.5 초를 다 돌았다.** 서버의 `r.Context()` 는 취소됐지만 핸들러가 **그것을 안 봤다.**
  ★★ [web-api 27번](../../../../web-api/27-abort-and-timeout/)의 「**취소는 요청을 없던 일로 만들지 않는다** — 서버에서 끝까지 처리된 칸 6 / 7」과 **같은 결론**이다(브라우저 `AbortController` 대 Go `context`).

```text
   ★★★ 네 설정이 지키는 구간

   연결 ─▶ 요청 보냄 ─▶ [ 응답 헤더 기다림 ] ─▶ [ 본문 읽기 ] ─▶ 끝
   Client.Timeout          ├──────────────────────────────────────┤   Get 뒤에도 계속
   context.WithTimeout     ├──────────────────────────────────────┤   ctx 가 살아 있는 동안
   ResponseHeaderTimeout              ├────────┤                       헤더까지만
   (기본 http.Get)          없음
```

비용 — 시간은 참/거짓으로만 쟀다.

### (3) ★★★ `Body` 를 다루는 법 6 × 크기 2 — 서버가 본 새 연결

**언제 쓰나** — `resp, err := client.Do(req)` 다음 줄을 쓸 때.

```text
===== 소스: t47body.go =====
package main

import (
	"fmt"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"net/http/httptrace"
	"strconv"
	"strings"
	"sync/atomic"
	"time"
)

func main() {
	var newConns atomic.Int64
	srv := httptest.NewUnstartedServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		n, _ := strconv.Atoi(r.URL.Query().Get("n"))
		io.WriteString(w, strings.Repeat("x", n))
	}))
	srv.Config.ConnState = func(c net.Conn, s http.ConnState) {
		if s == http.StateNew {
			newConns.Add(1)
		}
	}
	srv.Start()
	defer srv.Close()

	type mode struct {
		name        string
		read, close bool
		perRequest  func() *http.Client // nil 이면 모드마다 Client 하나
	}
	modes := []mode{
		{"끝까지 읽고 닫음", true, true, nil},
		{"닫기만", false, true, nil},
		{"끝까지 읽기만", true, false, nil},
		{"둘 다 안 함", false, false, nil},
		{"요청마다 &http.Client{}", true, true, func() *http.Client { return &http.Client{} }},
		{"요청마다 새 Transport", true, true, func() *http.Client { return &http.Client{Transport: &http.Transport{}} }},
	}
	const reqs = 10
	all, cells := 0, 0
	fmt.Println("본문 크기\t다루는 법\t서버가 본 새 연결\tGotConn Reused=true")
	for _, size := range []int{100, 1 << 20} {
		for _, md := range modes {
			newConns.Store(0)
			http.DefaultTransport.(*http.Transport).CloseIdleConnections()
			shared := &http.Client{Transport: &http.Transport{}}
			reused := 0
			for range reqs {
				c := shared
				if md.perRequest != nil {
					c = md.perRequest()
				}
				trace := &httptrace.ClientTrace{GotConn: func(i httptrace.GotConnInfo) {
					if i.Reused {
						reused++
					}
				}}
				req, _ := http.NewRequest("GET", srv.URL+"/?n="+strconv.Itoa(size), nil)
				req = req.WithContext(httptrace.WithClientTrace(req.Context(), trace))
				res, err := c.Do(req)
				if err != nil {
					fmt.Println(md.name, "err", err)
					continue
				}
				if md.read {
					io.Copy(io.Discard, res.Body)
				}
				if md.close {
					res.Body.Close()
				}
				time.Sleep(20 * time.Millisecond) // 요청 사이에 쉰다
			}
			n := newConns.Load()
			cells++
			if n == reqs {
				all++
			}
			fmt.Printf("%d\t%s\t%d\t%d\n", size, md.name, n, reused)
		}
	}
	fmt.Printf("새 연결 %d개인 칸 %d / %d\n", reqs, all, cells)
}
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

그림 해설 (한 단계씩):

- ★★★ **「끝까지 읽고 닫음」은 두 크기·두 판 모두 `1`** — 10 요청이 **한 연결**을 돌려 썼다(`Reused` 9 = 첫 요청만 새 연결).
- ★★★ **「끝까지 읽기만」(닫지 않음)도 전부 `1`** — ★★ **브리핑의 전제 「Body 를 안 닫아 커넥션이 재사용되지 않는다」가 이 칸에서 뒤집혔다.** 연결이 풀로 돌아가는 계기는 **`EOF` 를 읽은 순간**이다. 그렇다고 `Close` 를 빼도 된다는 뜻은 **아니다** — 문서는 닫을 책임을 적고, 도중에 에러가 나면 `EOF` 까지 못 간다.
- ★★★ **「닫기만」이 판과 크기로 갈렸다** — **1.27.1 · 100 B 는 `1`**, **1.27.1 · 1 MiB 와 1.25.12 둘 다 `10`**. 1.27.1 은 닫힌 본문을 **`maxPostCloseReadBytes`(256 KiB)까지 대신 읽어** 연결을 살린다(머리말 `t47impl`). 1 MiB 는 그 한도를 넘어 **연결을 버렸다.** 이 한 칸이 `갈린 칸 1 / 12` 다.
- ★★★ **「둘 다 안 함」은 전부 `10`** — 연결이 본문에 **붙들린 채** 남아 다음 요청은 새 연결을 판다. ★ 붙들린 연결은 **이 프로그램이 끝날 때까지** 안 풀렸다(몇 개의 고루틴·fd 가 남았는지는 **안 셌다**).
- ★★★ **「요청마다 `&http.Client{}`」는 `1`** — ★★ **두 번째로 뒤집힌 전제** — `Client` 를 매번 새로 만들어도 **`Transport` 가 `nil` 이면 `DefaultTransport` 를 같이 쓴다**(문서 「Its zero value (DefaultClient) is a usable client that uses DefaultTransport」). 연결 풀은 `Client` 가 아니라 **`Transport` 에 산다.**
- ★★★ **「요청마다 새 `Transport`」는 `10`** — 풀이 요청마다 새로 생기니 **돌려받을 곳이 없다.**
- ★★ **서버 창(`ConnState`)과 클라이언트 창(`GotConn.Reused`)이 12칸 전부 맞았다** — 1 ↔ 9, 10 ↔ 0. **같은 질문을 두 창으로 물어** 서로를 확인했다.

```text
   ★★★ 이 격자의 결론 — 새 연결 수(10 요청)

                         읽고닫음  닫기만   읽기만  둘다안함  매번Client{}  매번Transport
   1.27.1  · 100 B          1        1        1       10          1            10
   1.27.1  · 1 MiB          1       10        1       10          1            10
   1.25.12 · 100 B          1       10        1       10          1            10
   1.25.12 · 1 MiB          1       10        1       10          1            10
                                     └ 판·크기로 갈린 유일한 열
```

비용 — 연결 **수**만 셌다. **빠르다는 주장은 없다.**

### (4) ★★★ 4xx·5xx 는 에러가 아니다

```text
===== 소스: t47status.go =====
package main

import (
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"regexp"
)

func main() {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/404":
			http.NotFound(w, r)
		case "/500":
			http.Error(w, "oops", http.StatusInternalServerError)
		default:
			io.WriteString(w, "ok")
		}
	}))
	base := srv.URL
	port := regexp.MustCompile(`127\.0\.0\.1:\d+`)
	mask := func(s string) string { return port.ReplaceAllString(s, "127.0.0.1:<포트>") }
	get := func(u string) {
		res, err := http.Get(u)
		if err != nil {
			fmt.Printf("%-32s err=%s\n", mask(u), mask(err.Error()))
			return
		}
		b, _ := io.ReadAll(res.Body)
		res.Body.Close()
		fmt.Printf("%-32s err=%v · StatusCode=%d · Status=%q · 본문=%q\n", mask(u), err, res.StatusCode, res.Status, b)
	}
	get(base + "/200")
	get(base + "/404")
	get(base + "/500")
	srv.Close()
	get(base + "/200")
}
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && ./prog =====
vet exit=0
http://127.0.0.1:<포트>/200        err=<nil> · StatusCode=200 · Status="200 OK" · 본문="ok"
http://127.0.0.1:<포트>/404        err=<nil> · StatusCode=404 · Status="404 Not Found" · 본문="404 page not found\n"
http://127.0.0.1:<포트>/500        err=<nil> · StatusCode=500 · Status="500 Internal Server Error" · 본문="oops\n"
http://127.0.0.1:<포트>/200        err=Get "http://127.0.0.1:<포트>/200": dial tcp 127.0.0.1:<포트>: connect: connection refused
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`404`·`500` 도 `err=<nil>`** — `StatusCode` 와 본문이 **정상적으로** 왔다. 문서 「**A non-2xx status code doesn't cause an error**」.
- ★★★ **에러는 서버를 닫은 뒤의 `connection refused` 하나뿐** — 「HTTP 로 말을 주고받지 못한 것」만 `err` 다.
- ★★ **`if err != nil` 만 보는 코드는 404 를 성공으로 처리한다** — `res.StatusCode` 를 **따로** 봐야 한다. [web-api 25번](../../../../web-api/25-fetch-request-response/)의 **`fetch` 도 404·500 이 `then`**(`catch` 로 간 칸 2 / 6)이었다 — **Go 와 브라우저가 같은 선을 긋는다.**

비용 — 없다.

### (5) ★★ 리다이렉트 — 10번에서 멈추고, 응답도 같이 준다

```text
===== 소스: t47redirect.go =====
package main

import (
	"errors"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strconv"
	"strings"
	"sync/atomic"
)

func main() {
	var hits atomic.Int64
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		hits.Add(1)
		n, _ := strconv.Atoi(strings.TrimPrefix(r.URL.Path, "/r/"))
		http.Redirect(w, r, "/r/"+strconv.Itoa(n+1), http.StatusFound)
	}))
	defer srv.Close()
	mask := func(s string) string { return strings.ReplaceAll(s, srv.URL, "http://127.0.0.1:<포트>") }

	res, err := http.Get(srv.URL + "/r/0")
	fmt.Printf("[기본 Client] res==nil=%v · err=%s · 서버가 받은 요청 %d\n", res == nil, mask(err.Error()), hits.Load())

	hits.Store(0)
	c := &http.Client{CheckRedirect: func(req *http.Request, via []*http.Request) error {
		if len(via) >= 3 {
			return errors.New("세 번째에서 멈춤")
		}
		return nil
	}}
	res, err = c.Get(srv.URL + "/r/0")
	fmt.Printf("[CheckRedirect 3] res==nil=%v · err=%s · 서버가 받은 요청 %d\n", res == nil, mask(err.Error()), hits.Load())
	if res != nil {
		res.Body.Close()
	}

	hits.Store(0)
	c = &http.Client{CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
	res, err = c.Get(srv.URL + "/r/0")
	fmt.Printf("[ErrUseLastResponse] err=%v · StatusCode=%d · Location=%s · 서버가 받은 요청 %d\n", err, res.StatusCode, res.Header.Get("Location"), hits.Load())
	res.Body.Close()
}
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && ./prog =====
vet exit=0
[기본 Client] res==nil=false · err=Get "/r/10": stopped after 10 redirects · 서버가 받은 요청 10
[CheckRedirect 3] res==nil=false · err=Get "/r/3": 세 번째에서 멈춤 · 서버가 받은 요청 3
[ErrUseLastResponse] err=<nil> · StatusCode=302 · Location=/r/1 · 서버가 받은 요청 1
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **기본 `Client` — `Get "/r/10": stopped after 10 redirects` · 서버가 받은 요청 `10`** — 끝없이 리다이렉트하는 서버에 **열 번째 응답에서** 멈췄다. 문서 「stop after 10 consecutive requests」(머리말 `t47cdoc`).
- ★★★ **`res==nil=false`** — **에러와 응답이 같이 왔다.** 문서 「**A non-nil Response with a non-nil error only occurs when CheckRedirect fails**, and even then the returned Response.Body is already closed」. `if err != nil { return }` 뒤에 `defer res.Body.Close()` 를 두는 흔한 꼴은 **이 경우에도 문제없다**(이미 닫혀 있다).
- ★★ **`CheckRedirect` 로 한도를 바꾼다** — 세 번째에서 멈추니 서버가 받은 요청 `3`. **`http.ErrUseLastResponse`** 를 돌려주면 **따라가지 않고** `302` 응답 그대로(`err=<nil>`).

비용 — 없다.

## 문법 — 형태와 규칙

### 형태

```go
// t47status.go
package main

import (
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"regexp"
)

func main() {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/404":
			http.NotFound(w, r)
		case "/500":
			http.Error(w, "oops", http.StatusInternalServerError)
		default:
			io.WriteString(w, "ok")
		}
	}))
	base := srv.URL
	port := regexp.MustCompile(`127\.0\.0\.1:\d+`)
	mask := func(s string) string { return port.ReplaceAllString(s, "127.0.0.1:<포트>") }
	get := func(u string) {
		res, err := http.Get(u)
		if err != nil {
			fmt.Printf("%-32s err=%s\n", mask(u), mask(err.Error()))
			return
		}
		b, _ := io.ReadAll(res.Body)
		res.Body.Close()
		fmt.Printf("%-32s err=%v · StatusCode=%d · Status=%q · 본문=%q\n", mask(u), err, res.StatusCode, res.Status, b)
	}
	get(base + "/200")
	get(base + "/404")
	get(base + "/500")
	srv.Close()
	get(base + "/200")
}
```

규칙 불릿.

- ★★★ **기본 `Client`(`http.Get`)는 타임아웃이 없다** — `Client{Timeout: …}` 나 요청마다 `context.WithTimeout`.
- ★★★ **`Client.Timeout` 은 본문 읽기까지 · `ResponseHeaderTimeout` 은 헤더까지** — 타임아웃 판별은 `errors.Is(err, context.DeadlineExceeded)` 나 `net.Error` 의 `Timeout()`.
- ★★★ **`defer res.Body.Close()` + 본문을 쓰는 만큼 읽는다** — 안 읽고 닫기만 하면 **작은 본문만**(이 판) 연결이 돌아온다.
- ★★★ **`Client` 보다 `Transport` 를 재사용한다** — 요청마다 새 `Transport` 면 연결이 매번 새로.
- ★★★ **`err == nil` 이어도 `StatusCode` 를 본다.**
- ★★ **리다이렉트 한도 초과는 응답과 에러가 같이 온다** — `CheckRedirect` 로 바꾼다.

### 금지 사례 — 누가 잡나

| 쓴 꼴 | 누가 잡나 | 어디서 |
|---|---|---|
| 외부 호출에 `http.Get` | ★★★ **아무도 안 잡는다** — 서버가 안 답하면 영영 기다린다 | (2)절 |
| `ResponseHeaderTimeout` 만 걸고 안심 | ★★ **아무도 안 잡는다** — 본문이 느리면 못 막는다 | (2)절 |
| 응답을 안 읽고 안 닫음 | ★★★ **아무도 안 잡는다** — 요청마다 새 연결(`10`) | (3)절 |
| 요청마다 `&http.Client{Transport: &http.Transport{}}` | ★★ **아무도 안 잡는다** — `10` | (3)절 |
| `if err != nil` 만 보고 성공 처리 | ★★★ **아무도 안 잡는다** — 404 가 성공으로 | (4)절 |
| 클라이언트 타임아웃으로 서버 일을 멈추려 함 | ★★ **서버는 끝까지 돈다**(`8 / 8`) — 핸들러가 `r.Context()` 를 봐야 한다 | (2)절 |

## 어디서 틀리나

### 1. ★★★ 「`http.Get` 에도 적당한 기본 타임아웃이 있다」

- (2)절 — **두 서버 다 `false`**. 문서 「A Timeout of zero means no timeout」.

### 2. ★★★ 「`ResponseHeaderTimeout` 이면 느린 응답을 막는다」

- (2)절 — **헤더만** 막는다. 본문이 느린 서버에는 **1.5 초를 다 기다렸다.**

### 3. ★★★ 「`Body` 를 안 닫으면 연결이 재사용되지 않는다」

- (3)절 — **반만 맞다.** **끝까지 읽기만 해도 `1`**. 안 읽고 **닫기만** 한 것이 판·크기로 갈렸고, **둘 다 안 하면 `10`**.

### 4. ★★★ 「`Client` 를 요청마다 만들면 연결이 매번 새로 생긴다」

- (3)절 — **`&http.Client{}` 는 `1`** — `DefaultTransport` 를 같이 쓴다. 매번 새로 생기는 것은 **`Transport` 를 새로 만들 때**다.

### 5. ★★★ 「404 는 에러로 온다」

- (4)절 — **`err=<nil>`**. 브라우저 `fetch` 도 같다.

### 6. ★★ 「클라이언트가 타임아웃으로 떠나면 서버도 멈춘다」

- (2)절 — **`8 / 8` 이 끝까지 돌았다.** 서버의 `r.Context()` 가 취소된 것은 5개지만 핸들러가 안 봤다.

### 7. ★ 「리다이렉트 한도에 걸리면 응답은 `nil` 이다」

- (5)절 — **`res==nil=false`** — 응답과 에러가 같이 온다(본문은 닫혀 있다).

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| ★★★ `Timeout` 0 = 없음 · `DefaultClient` 는 제로값 | **표준 라이브러리 계약** | `t47cdoc` · (2)절 |
| `Client.Timeout` 이 본문 읽기까지 | **표준 라이브러리 계약** | `t47cdoc` · (2)절 |
| 비-2xx 는 에러가 아님 | **표준 라이브러리 계약** | `t47ddoc` · (4)절 |
| 리다이렉트 실패 시 응답+에러 | **표준 라이브러리 계약** | `t47ddoc` · (5)절 |
| ★★ 닫힌 본문을 256 KiB 까지 비움 | **구현**(1.27.1 `transport.go`) — 1.27.1 문서는 「conservative limit」이라고만 적는다 | `t47bdoc`·`t47impl` · (3)절 |
| `EOF` 에서 연결이 돌아감 | **관찰**(두 판 모두) — 문서는 「read to EOF **and** closed」를 요구한다 | (3)절 |
| 리다이렉트 10번에서 멈춤 | **표준 라이브러리 계약** | `t47cdoc` · (5)절 |
| 에러 문구 셋 | **구현** — 판별은 `errors.Is`·`Timeout()` | (2)절 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 외부 API 호출 | ★★★ **패키지 수준에 `Client{Timeout: …}` 하나** — 요청마다 새로 안 만든다 | (2)·(3)절 |
| 요청마다 다른 마감(상위 `ctx` 가 있다) | **`http.NewRequestWithContext(ctx, …)`** | (2)절 · 34번 |
| 응답을 받은 뒤 | ★★★ **`defer res.Body.Close()` + 필요한 만큼 읽기 · `StatusCode` 확인** | (3)·(4)절 |
| 긴 본문을 버릴 때 | 끝까지 읽어 버리기(`io.Copy(io.Discard, …)`) — ★ 1.27.1 의 자동 비우기는 **256 KiB 까지** | (3)절 |
| 재시도 | [`ops-patterns/01-retry-backoff`](../../../../../ops-patterns/01-retry-backoff/) | 정본 |
| 계층별 타임아웃 값 | [server-design 06 §2](../../../../../systems/server-design/06-resilience.md) | 정본 |

## 핵심 문장

- ★★★ **기본 `Client` 에는 타임아웃이 없다** — `http.Get` 은 느린 서버 둘 다 끝까지 기다렸다. 걸면 `1초 안에 돌아온 칸 5 / 8`.
- ★★★ **`Client.Timeout`·`context` 는 본문까지, `ResponseHeaderTimeout` 은 헤더까지** — 판별은 `errors.Is(err, context.DeadlineExceeded)`.
- ★★★ **연결은 `EOF` 에서 풀로 돌아간다** — 끝까지 읽기만 해도 1, 둘 다 안 하면 10. **닫기만은 판과 크기에 달렸다**(1.27.1 · 100 B 만 1 — `1 / 12`).
- ★★★ **연결 풀은 `Transport` 에 산다** — `&http.Client{}` 를 매번 만들어도 1, `Transport` 를 매번 만들면 10.
- ★★★ **404·500 은 `err == nil`** — 에러는 HTTP 로 말을 못 나눴을 때(연결 거부)뿐.
- ★★ **클라이언트가 떠나도 서버는 끝까지 돈다**(`8 / 8`) — 리다이렉트 한도에서는 응답과 에러가 같이 온다.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 47번)
- [46번 주제](../46-net-http-server-servemux-patterns-handler-and-middleware/)(서버 · `Handler`) — ★ 목록상 선행
- [34번 주제](../34-context-cancellation-deadlines-and-values/) — ★★ **요청 타임아웃의 뒤쪽 — 취소 전파·`DeadlineExceeded` 의 정본** · [24번 주제](../24-error-wrapping-and-errors-is-as-join/)(`errors.Is`) · [43번 주제](../43-io-reader-writer-and-composition/)(`Body` 는 `io.ReadCloser`) · [44번 주제](../44-os-bufio-and-io-copy/)(`Close` 를 안 하면 사라지는 것)
- [`ops-patterns/01-retry-backoff`](../../../../../ops-patterns/01-retry-backoff/) — ★★ **재시도·백오프 정책의 정본** · [server-design 06 §2 타임아웃](../../../../../systems/server-design/06-resilience.md)(타임아웃 예산) · [server-design 02 §5 연결 관리](../../../../../systems/server-design/02-request-path.md)(Keep-Alive)
- [web-api 25번](../../../../web-api/25-fetch-request-response/)(`fetch` 도 404 가 `then`) · [web-api 27번](../../../../web-api/27-abort-and-timeout/)(취소해도 서버는 처리)

## 용어 풀이

- **`http.Client`** — 요청 정책(타임아웃·리다이렉트·쿠키)을 가진 값. 제로값이 `DefaultClient`.
- **`http.Transport`** — 연결을 열고 **풀에 보관**하는 부분. `Client.Transport` 가 `nil` 이면 `DefaultTransport`.
- **`Client.Timeout`** — 연결·리다이렉트·본문 읽기를 **다 합친** 시간 제한. 0 이면 없음.
- **`ResponseHeaderTimeout`** — 요청을 다 보낸 뒤 **응답 헤더가 올 때까지**의 제한.
- **`ConnState`** — 서버 연결의 상태가 바뀔 때(`StateNew` 등) 부르는 훅.
- **`httptrace.GotConn`** — 클라이언트가 연결을 얻을 때 부르는 훅. `Reused` 가 재사용 여부.
- **`CheckRedirect`** — 리다이렉트를 따라갈지 정하는 함수. `ErrUseLastResponse` 를 돌려주면 따라가지 않는다.
- **`maxPostCloseReadBytes`** — 1.27.1 `transport.go` 의 상수(256 KiB) — 닫힌 본문을 이만큼까지 대신 읽는다.

---

## 더 들어가면

- ★ **`Transport` 의 `MaxIdleConnsPerHost`** — 동시에 여러 요청을 보낼 때 풀에 남는 연결 수를 정한다. 이 문서는 **순차 요청만** 보내 **안 던졌다.**
- ★ **`1.25.12` 와 `1.27.1` 사이 어느 판에서 자동 비우기가 들어왔나** — 그 사이 툴체인이 없어 **확인하지 않았다.**
- ★ **HTTP/2** — 한 연결 다중화라 「새 연결 수」 격자의 뜻이 다르다. **안 돌렸다.**

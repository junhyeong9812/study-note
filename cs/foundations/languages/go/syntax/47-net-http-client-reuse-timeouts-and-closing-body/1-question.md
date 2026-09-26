# go/syntax/47 — `net/http` 클라이언트: `Client` 재사용·타임아웃·`Body` 닫기 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ **모든 문제에서 「이 동작은 표준 라이브러리 문서의 계약인가, 이 판 구현의 성질인가」를 먼저 적어라.**
> 모든 Go 실험은 `module ex` 이고 `go build -trimpath` 로 빌드해 돌렸다(`go1.27.1` · 4번만 `go1.25.12` 와 나란히). 서버는 `httptest.NewServer`(`127.0.0.1`)뿐이다 — 포트는 `<포트>` 로 가렸다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 느린 서버 둘과 기다리는 법 넷 (예측)

```go
// t47timeout.go
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
```

- 여덟 줄 각각의 「1초 안에 돌아왔나」와 에러(어느 단계에서 났나), `Is(DeadlineExceeded)` 는? 서버 줄과 마지막 줄의 수는?

### 2. 헤더는 빨리, 본문은 늦게 (왜)

- 1번에서 `ResponseHeaderTimeout: 200ms` 와 `Client{Timeout: 200ms}` 가 `/slowbody` 에서 다르게 끝나는 이유를, 두 설정이 **재는 구간**으로 설명하라.

### 3. 타임아웃을 무엇으로 알아보나 (경계)

- 1번의 에러 문구는 세 가지로 갈린다. 코드에서 「타임아웃이었나」를 가를 때 문구를 비교하면 안 되는 이유와, 대신 쓸 두 방법은? [34번 주제](../34-context-cancellation-deadlines-and-values/) (2)절의 `Err` 와 어떻게 이어지나?

### 4. 본문을 다루는 법 여섯과 크기 둘 (예측)

```go
// t47body.go
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
```

<!-- go.mod 의 go 줄은 1.25 — 같은 소스를 go1.27.1 과 go1.25.12 로 각각 빌드해 돌리고 줄마다 나란히 놓는다. -->

- `go1.27.1` 로 돌리면 열두 줄 각각의 「서버가 본 새 연결」과 `Reused` 는? `go1.25.12` 로 돌리면 **어느 줄이** 달라지나?

### 5. 닫지 않았는데 한 연결 (왜)

- 4번의 「끝까지 읽기만」 줄이 닫지 않았는데도 한 연결로 끝난 이유는? 그렇다면 `Close` 를 빼도 되나 — 문서는 무엇을 요구하나?

### 6. 무엇을 재사용하나 (경계)

- 4번의 「요청마다 `&http.Client{}`」와 「요청마다 새 `Transport`」가 다르게 나온 이유는? 「`Client` 를 재사용하라」는 문서 문장이 실제로 가리키는 것은 무엇인가?

### 7. 200 · 404 · 500 · 닫힌 서버 (예측)

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

- 네 줄 각각의 `err` 와 `StatusCode` 는?

### 8. 브라우저의 `fetch` 와 (연결)

- [web-api 25번](../../../../web-api/25-fetch-request-response/)에서 `fetch` 는 404·500 을 어떻게 다뤘나? 7번의 Go 와 같은 선을 긋나, 다른가?

### 9. 끝없는 리다이렉트 (예측)

```go
// t47redirect.go
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
```

- 세 줄 각각의 `res==nil`·`err`·서버가 받은 요청 수는?

### 10. 떠난 클라이언트, 남은 서버 (연결)

- 1번의 서버 줄로 보면 클라이언트가 200 ms 에 떠난 요청을 서버는 어떻게 처리했나? [web-api 27번](../../../../web-api/27-abort-and-timeout/)의 브라우저 취소와 같은 결론인가? 서버 쪽에서 멈추게 하려면 핸들러가 무엇을 봐야 하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

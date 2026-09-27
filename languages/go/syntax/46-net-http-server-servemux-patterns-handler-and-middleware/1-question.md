# go/syntax/46 — `net/http` 서버: `ServeMux` 패턴(1.22)·`Handler`·미들웨어 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ **모든 문제에서 「이 동작은 명세인가, 표준 라이브러리 문서의 계약인가, 이 판 소스의 구현인가」를 먼저 적어라.**
> 모든 Go 실험은 `module ex` 이고 `go build -trimpath` 로 빌드해 돌렸다(`go1.27.1`). 서버는 `httptest.NewServer`(`127.0.0.1`)뿐이다 — 포트는 출력에서 `<포트>` 로 가렸다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 패턴 일곱 개와 요청 열네 개 (예측)

```go
// t46route.go
package main

import (
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
)

func h(name string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintf(w, "%s id=%q path=%q", name, r.PathValue("id"), r.PathValue("path"))
	}
}

func main() {
	mux := http.NewServeMux()
	for _, p := range []string{
		"GET /items/{id}",
		"POST /items",
		"/items/{$}",
		"/files/{path...}",
		"/lit/{id}",
		"/static/",
		"example.com/",
	} {
		mux.Handle(p, h("["+p+"]"))
	}
	srv := httptest.NewServer(mux)
	defer srv.Close()
	cl := &http.Client{CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}

	for _, q := range [][3]string{
		{"GET", "", "/items/7"},
		{"HEAD", "", "/items/7"},
		{"DELETE", "", "/items/7"},
		{"GET", "", "/items/7/"},
		{"POST", "", "/items"},
		{"GET", "", "/items"},
		{"GET", "", "/items/"},
		{"GET", "", "/files/a/b/c"},
		{"GET", "", "/lit/7"},
		{"GET", "", "/lit/{id}"},
		{"GET", "", "/static/x.css"},
		{"GET", "", "/static"},
		{"GET", "example.com", "/items/7"},
		{"GET", "", "/nope"},
	} {
		req, _ := http.NewRequest(q[0], srv.URL+q[2], nil)
		if q[1] != "" {
			req.Host = q[1]
		}
		res, err := cl.Do(req)
		if err != nil {
			fmt.Printf("%s %s%s\terr\n", q[0], q[1], q[2])
			continue
		}
		b, _ := io.ReadAll(res.Body)
		res.Body.Close()
		cell := fmt.Sprintf("%d", res.StatusCode)
		if a := res.Header.Get("Allow"); a != "" {
			cell += " Allow: " + a
		}
		if l := res.Header.Get("Location"); l != "" {
			cell += " → " + l
		}
		if res.StatusCode == 200 {
			cell += " " + string(b)
		}
		fmt.Printf("%s %s%s\t%s\n", q[0], q[1], q[2], strings.TrimSpace(cell))
	}
}
```

<!-- go.mod 의 go 줄을 1.22 로 두고 빌드해 실행한다. 리다이렉트는 따라가지 않는다. -->

- `go.mod` 가 `go 1.22` 일 때 열네 줄 각각의 상태 코드(와 `Allow`·리다이렉트 대상), 200 이면 고른 패턴과 `id`·`path` 는?

### 2. 같은 소스를 `go 1.21` 줄로 (예측)

- 1번 소스를 `go.mod` 의 `go` 줄만 `1.21` 로 바꿔 다시 빌드하면 열네 줄은 각각 어떻게 되나? 1.22 와 **갈리는 줄**은 어느 것인가?

### 3. `GET /items` 가 받은 것 (왜)

- 1번에서 `POST /items` 라는 패턴이 있는데 `GET /items` 가 `405` 가 아닌 것을 받는 이유는? `DELETE /items/7` 과는 무엇이 다른가?

### 4. `405` 라는 숫자는 누가 약속했나 (경계)

- `DELETE /items/7` 의 `405 Allow: GET, HEAD` 는 `go doc net/http.ServeMux` 가 약속한 것인가, 이 판 소스의 한 줄인가? 어떻게 확인하나?

### 5. 패턴 여섯 쌍 (예측)

```go
// t46conflict.go
package main

import (
	"fmt"
	"net/http"
)

func try(a, b string) {
	defer func() {
		if e := recover(); e != nil {
			fmt.Printf("[%s] + [%s]\n    panic: %v\n", a, b, e)
		}
	}()
	mux := http.NewServeMux()
	nop := http.HandlerFunc(func(http.ResponseWriter, *http.Request) {})
	mux.Handle(a, nop)
	mux.Handle(b, nop)
	fmt.Printf("[%s] + [%s]\n    등록됨\n", a, b)
}

func main() {
	try("/items/{id}", "/items/{name}")
	try("/items/", "/items/{rest...}")
	try("/b/{x}/c", "/b/c/{y}")
	try("GET /a/{x}", "/a/{x}")
	try("/a/{x}", "/a/new")
	try("/d", "/d")
}
```

- 여섯 쌍 각각 등록되나, panic 인가? panic 이면 문구는?

### 6. `/a/{x}` 와 `/a/new` (왜)

- 5번에서 `/items/{id}` + `/items/{name}` 은 막히고 `/a/{x}` + `/a/new` 는 공존하는 이유를 문서의 「more specific」 정의로 설명하라.

### 7. 사슬 · 감싸개 · `Flush` (예측)

```go
// t46mw.go
package main

import (
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
)

var (
	mu  sync.Mutex
	log []string
)

func logf(format string, a ...any) {
	mu.Lock()
	log = append(log, fmt.Sprintf(format, a...))
	mu.Unlock()
}

func mw(name string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			logf("%s 들어감", name)
			next.ServeHTTP(w, r)
			logf("%s 나옴", name)
		})
	}
}

// rec 는 WriteHeader 로 넘어온 상태 코드를 적는다.
type rec struct {
	http.ResponseWriter
	status int
}

func (r *rec) WriteHeader(code int) { r.status = code; r.ResponseWriter.WriteHeader(code) }

// recU 는 rec 에 Unwrap 을 더한 것이다.
type recU struct{ rec }

func (r *recU) Unwrap() http.ResponseWriter { return r.ResponseWriter }

func status(next http.Handler, unwrap bool) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		var rw http.ResponseWriter
		var get func() int
		if unwrap {
			x := &recU{rec{ResponseWriter: w}}
			rw, get = x, func() int { return x.status }
		} else {
			x := &rec{ResponseWriter: w}
			rw, get = x, func() int { return x.status }
		}
		next.ServeHTTP(rw, r)
		logf("감싼 쪽이 본 상태 코드 = %d", get())
	})
}

func main() {
	final := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		logf("핸들러")
		_, isFlusher := w.(http.Flusher)
		ferr := http.NewResponseController(w).Flush()
		logf("w.(http.Flusher) ok=%v · ResponseController.Flush err=%v", isFlusher, ferr)
		if r.URL.Path == "/nf" {
			w.WriteHeader(http.StatusNotFound)
		}
		io.WriteString(w, "body")
	})
	mux := http.NewServeMux()
	mux.Handle("/chain", mw("A")(mw("B")(mw("C")(final))))
	mux.Handle("/ok", status(final, false))
	mux.Handle("/nf", status(final, false))
	mux.Handle("/ok-unwrap", status(final, true))
	srv := httptest.NewServer(mux)
	defer srv.Close()
	for _, p := range []string{"/chain", "/ok", "/nf", "/ok-unwrap"} {
		mu.Lock()
		log = nil
		mu.Unlock()
		res, err := http.Get(srv.URL + p)
		if err != nil {
			fmt.Println(p, err)
			continue
		}
		io.Copy(io.Discard, res.Body)
		res.Body.Close()
		mu.Lock()
		fmt.Printf("── GET %s → 클라이언트가 받은 상태 %d ──\n    %s\n", p, res.StatusCode, strings.Join(log, "\n    "))
		mu.Unlock()
	}
}
```

- 네 요청 각각에서 클라이언트가 받은 상태와 로그 줄들은?

### 8. 감싸개가 본 `0` (왜)

- 7번 `/ok` 에서 감싸개가 본 상태 코드와 클라이언트가 받은 상태가 다른 이유는? 감싸개를 고치는 방법 두 가지(상태 기록 · `Flush`)는?

### 9. 핸들러 panic (예측)

```go
// t46panic.go
package main

import (
	"bytes"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/http/httptest"
	"regexp"
	"strings"
	"sync"
)

type safeBuf struct {
	mu sync.Mutex
	b  bytes.Buffer
}

func (s *safeBuf) Write(p []byte) (int, error) { s.mu.Lock(); defer s.mu.Unlock(); return s.b.Write(p) }
func (s *safeBuf) String() string              { s.mu.Lock(); defer s.mu.Unlock(); return s.b.String() }

func main() {
	var buf safeBuf
	mux := http.NewServeMux()
	mux.HandleFunc("/boom", func(w http.ResponseWriter, r *http.Request) {
		io.WriteString(w, "part")
		panic("boom")
	})
	mux.HandleFunc("/abort", func(w http.ResponseWriter, r *http.Request) {
		panic(http.ErrAbortHandler)
	})
	mux.HandleFunc("/ok", func(w http.ResponseWriter, r *http.Request) { io.WriteString(w, "ok") })
	srv := httptest.NewUnstartedServer(mux)
	srv.Config.ErrorLog = log.New(&buf, "", 0)
	srv.Start()
	defer srv.Close()
	port := regexp.MustCompile(`127\.0\.0\.1:\d+`)
	mask := func(s string) string { return port.ReplaceAllString(s, "127.0.0.1:<포트>") }

	for _, p := range []string{"/boom", "/abort", "/ok"} {
		before := len(strings.Split(buf.String(), "\n"))
		res, err := http.Get(srv.URL + p)
		if err != nil {
			fmt.Printf("GET %-6s → err=%s\n", p, mask(err.Error()))
		} else {
			b, _ := io.ReadAll(res.Body)
			res.Body.Close()
			fmt.Printf("GET %-6s → %d %q\n", p, res.StatusCode, b)
		}
		lines := strings.Split(buf.String(), "\n")
		stack := false
		for _, l := range lines[before-1:] {
			if strings.HasPrefix(l, "http:") {
				fmt.Printf("    서버 로그 첫 줄: %s\n", mask(l))
			}
			if strings.HasPrefix(l, "goroutine ") {
				stack = true
			}
		}
		fmt.Printf("    서버 로그에 새 줄이 생겼나 %v · 그 안에 goroutine 머리줄이 있나 %v\n", len(lines) > before, stack)
	}
}
```

- 세 요청 각각의 클라이언트 결과와 서버 로그 줄은? `/boom` 이 먼저 쓴 `"part"` 는 클라이언트에 도착하나?

### 10. 인터페이스 하나가 만든 것 (연결)

- [20번 주제](../20-interface-declaration-and-implicit-implementation/) (6)절의 「작은 인터페이스」가 `http.Handler` 에서 무엇을 가능하게 했나? 그리고 7번의 `w.(http.Flusher)` 가 `false` 가 된 것은 같은 성질의 **어떤 대가**인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

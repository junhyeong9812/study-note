# go/syntax/46 — `net/http` 서버: `ServeMux` 패턴(1.22)·`Handler`·미들웨어 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [`net/http`](https://pkg.go.dev/net/http) 패키지 문서(`go doc net/http.Handler` · `net/http.ServeMux`) · `net/http/server.go`·`servemux121.go` 소스(이 툴체인의 것). **이 툴체인에서 직접 떴다.**\
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.
> ★ **네트워크는 `localhost` 만** 썼다 — 서버는 `httptest.NewServer`(`127.0.0.1` 의 빈 포트)이고 외부로 나가는 요청은 없다.\
> **버전** — 메서드·와일드카드 패턴은 **1.22** 부터다. **`go.mod` 의 `go` 줄이 1.21 이하면 옛 의미로 돈다**((2)절 — `httpmuxgo121`). `ResponseController` 는 1.20.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체는 넷째 창이다** — 「**라우팅 격자** — 패턴 7개(`GET /items/{id}` · `POST /items` · `/items/{$}` · `/files/{path...}` · `/lit/{id}` · `/static/` · `example.com/`)를 건 한 `ServeMux` 에 요청 14개를 보내 **클라이언트가 받은 상태 코드와 고른 핸들러**를 적고, 같은 소스를 **`go.mod` 의 `go 1.22` 줄과 `go 1.21` 줄로 두 번 빌드**해 견준 표」.
마지막 줄 「**go 1.22 줄과 go 1.21 줄이 갈린 칸 10 / 14**」((2)절). ★★★ **소스는 한 글자도 같은데 `go` 한 줄이 라우팅을 바꾼다.**
★★ 짝이 되는 창은 「**미들웨어 사슬의 로그**」 — 바깥에서 들어가 **안쪽부터 나오고**, 상태 코드를 적는 감싸개는 **`WriteHeader` 가 안 불리면 `0` 을 본다**((4)절).

★★★ **이 주제의 경계** — 서버 **구조 설계**(계층·로드밸런서·세션·연결 관리·정상 종료)는 [`systems/server-design`](../../../../../systems/server-design/) 이 정본이다 — 특히 [02 요청 경로 §5 앱 계층](../../../../../systems/server-design/02-request-path.md). 여기서는 **`Handler` 인터페이스와 1.22 라우팅 패턴**으로 좁힌다.
★ 그쪽에 **미들웨어를 어느 순서로 쌓나** 같은 절은 **아직 없다**(`grep` 으로 `미들웨어`·`middleware` 0건). 인터페이스를 감싸면 **다른 인터페이스가 가려지는 것**은 [20번 주제](../20-interface-declaration-and-implicit-implementation/) (6)절 · [43번 주제](../43-io-reader-writer-and-composition/)의 조합과 같은 집안이다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 이 주제에서 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | ★ **메서드 하나짜리 인터페이스를 어떤 타입이든 암묵으로 만족한다**(20번) — `HandlerFunc` 가 함수 타입에 `ServeHTTP` 를 단 것 |
| **표준 라이브러리 계약** | `go doc` 이 적은 것 | ★★★ 패턴 문법 `[METHOD ][HOST]/[PATH]` · **`GET` 은 `HEAD` 도 받는다** · **더 구체적인 패턴이 이긴다 · 누구도 더 구체적이지 않으면 충돌 → 등록 시 panic** · 호스트 있는 패턴이 이긴다 · 끝 `/` 없는 요청은 **리다이렉트** · `httpmuxgo121=1` 로 옛 의미 · **핸들러 panic 은 서버가 recover 하고 연결을 끊는다** · `ErrAbortHandler` 는 로그를 안 남긴다 |
| **구현** | 이 판 소스·출력 | ★★ **메서드 불일치는 `405` + `Allow`**(문서에 숫자가 없고 `server.go` 에 있다) · 리다이렉트가 **1.22 는 `307`, 1.21 은 `301`** · 에러 문구 전부 |

★★★ **선을 긋는다** — 「`/items/{id}` 와 `/items/{name}` 을 같이 걸면 panic」은 **문서의 계약**이다. 「메서드가 틀리면 `405`」는 **이 판 소스의 한 줄**이다 — 문서가 약속한 숫자가 아니다((1)절 `t46impl`).

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
```

```text
===== 명령: go doc net/http.Handler | sed -n "3,5p;21,26p" =====
type Handler interface {
	ServeHTTP(ResponseWriter, *Request)
}
    If ServeHTTP panics, the server (the caller of ServeHTTP) assumes that the
    effect of the panic was isolated to the active request. It recovers the
    panic, logs a stack trace to the server error log, and either closes the
    network connection or sends an HTTP/2 RST_STREAM, depending on the HTTP
    protocol. To abort a handler so the client sees an interrupted response but
    the server doesn't log an error, panic with the value ErrAbortHandler.
(exit 0)
```

```text
===== 명령: go doc net/http.ServeMux | sed -n "24p;33,37p;62,72p;104,112p" =====
        [METHOD ][HOST]/[PATH]
    GET matches both GET and HEAD requests. Otherwise, the method must match
    exactly.

    A pattern with no host matches every host. A pattern with a host matches
    URLs on that host only.
    # Precedence

    If two or more patterns match a request, then the most specific pattern
    takes precedence. A pattern P1 is more specific than P2 if P1 matches a
    strict subset of P2’s requests; that is, if P2 matches all the requests
    of P1 and more. If neither is more specific, then the patterns conflict.
    There is one exception to this rule, for backwards compatibility: if two
    patterns would otherwise conflict and one has a host while the other does
    not, then the pattern with the host takes precedence. If a pattern passed to
    ServeMux.Handle or ServeMux.HandleFunc conflicts with another pattern that
    is already registered, those functions panic.
    The pattern syntax and matching behavior of ServeMux changed significantly
    in Go 1.22. To restore the old behavior, set the GODEBUG environment
    variable to "httpmuxgo121=1". This setting is read once, at program startup;
    changes during execution will be ignored.

    The backwards-incompatible changes include:
      - Wildcards are just ordinary literal path segments in 1.21. For example,
        the pattern "/{x}" will match only that path in 1.21, but will match any
        one-segment path in 1.22.
(exit 0)
```

```text
===== 명령: S="$(go env GOROOT)/src/net/http"; grep -n "StatusMethodNotAllowed), \"\", nil, nil\|Error(w, StatusText(StatusMethodNotAllowed)" "$S/server.go"; grep -n "RedirectHandler(u.String(), StatusTemporaryRedirect)" "$S/server.go"; grep -n "RedirectHandler(u.String(), StatusMovedPermanently)" "$S/servemux121.go"; grep -n -A1 "pattern\[0\] != ./." "$S/servemux121.go" =====
2759:				Error(w, StatusText(StatusMethodNotAllowed), StatusMethodNotAllowed)
2723:			return RedirectHandler(u.String(), StatusTemporaryRedirect), u.Path, nil, nil
2739:			return RedirectHandler(u.String(), StatusTemporaryRedirect), n.pattern.String(), nil, nil
2748:			return RedirectHandler(u.String(), StatusTemporaryRedirect), patStr, nil, nil
112:			return RedirectHandler(u.String(), StatusMovedPermanently), u.Path
126:		return RedirectHandler(u.String(), StatusMovedPermanently), u.Path
132:		return RedirectHandler(u.String(), StatusMovedPermanently), pattern
75:	if pattern[0] != '/' {
76-		mux.hosts = true
(exit 0)
```

- ★★ **`405` 와 `Allow` 는 `server.go:2759` 의 한 줄**이다 — `go doc net/http.ServeMux` 에는 `405` 라는 숫자가 **없다**(`grep` 0건). 리다이렉트 코드도 **새 쪽 `StatusTemporaryRedirect`(307)** · **옛 쪽 `StatusMovedPermanently`(301)** 로 소스가 갈린다.
- ★★ **`servemux121.go:75` — 옛 규칙은 `/` 로 시작하지 않는 패턴을 「호스트가 있는 패턴」으로 읽는다.** 그래서 1.21 의미에서는 `GET /items/{id}` 가 **호스트 `GET ` 의 경로**가 된다((2)절).

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다 — 출력 전에 가렸다** | ★★ **서버 포트** | `httptest.NewServer` 가 빈 포트를 고른다 — 소스가 `127.0.0.1:<포트>` 로 **바꿔서** 찍는다 |
| 안 흔들린다 | ★★★ **격자의 상태 코드·핸들러 이름·`PathValue` · `10 / 14`** | 요청과 패턴이 정한다 |
| 안 흔들린다 | panic 문구(`registered at ex/t46conflict.go:16`) · 미들웨어 로그 순서 | `-trimpath` 라 경로가 모듈 기준이다 · 요청을 하나씩 보낸다 |
| **안 싣는다** | 패닉 스택의 고루틴 번호·주소 | 「`goroutine` 머리줄이 있나」 **참/거짓**으로만 찍었다 |

★ 정규화 규칙은 **기본 넷**만 썼다. 포트는 **정규화가 아니라 소스에서** 가렸다.

## 한눈에 — 쉽게 말하면

**`Handler` 는 「창구 직원」 한 명의 약속이다** — 「손님(요청)을 받으면 답장(응답)을 쓴다」 하나뿐이다(`ServeHTTP`).
**`ServeMux` 는 「안내 데스크」** 다. 손님의 **용건(메서드) · 건물(호스트) · 층과 호수(경로)** 를 보고 창구를 골라 준다. 1.22 부터 안내 데스크가 **「3층 아무 호수(`{id}`)」·「GET 손님만」** 같은 안내문을 읽을 줄 알게 됐다.
**미들웨어는 「창구 앞에 선 또 한 명의 직원」** 이다 — 자기도 창구 직원(`Handler`)이라 손님을 받아 **뒤의 직원에게 넘기고**, 돌아오는 답장을 **나가는 길에 다시 본다.**

| 비유 | 실체 |
|---|---|
| 창구 직원의 약속 | ★★★ **`type Handler interface{ ServeHTTP(ResponseWriter, *Request) }`** — 메서드 하나 |
| 안내문 「GET 손님, 3층 아무 호수」 | ★★★ **`GET /items/{id}`** — `r.PathValue("id")` 로 호수를 읽는다 |
| 용건이 다른 손님 | ★★ **`DELETE /items/7` → `405 Allow: GET, HEAD`**(이 판) |
| 안내문 두 장이 같은 손님을 가리킴 | ★★★ **충돌 → 등록할 때 panic**((3)절) |
| 옛 안내 데스크 | ★★★ **`go 1.21` 줄 → `{id}` 가 글자 그대로**((2)절) |
| 앞에 선 직원 | ★★ **`func(http.Handler) http.Handler`**((4)절) |
| 앞 직원이 답장 봉투를 바꿔 끼움 | ★★ **`ResponseWriter` 감싸개** — 원래 봉투의 **다른 기능(`Flusher`)이 가려진다** |

```text
   ★★★ 요청 하나가 지나가는 길 — 이 문서가 찍은 순서

   클라이언트 ── GET /chain ──▶ Server ──▶ mux.ServeHTTP ── 패턴 고르기 ──▶ A ─▶ B ─▶ C ─▶ 핸들러
                                                                         │    │    │     │
   로그:                                                           A 들어감 B 들어감 C 들어감 핸들러
                                                                   A 나옴 ◀ B 나옴 ◀ C 나옴 ◀─┘
```

> **`ServeMux`** — 패턴과 핸들러의 표. 요청마다 **가장 구체적인** 패턴을 골라 그 핸들러를 부른다.

> **`HandlerFunc`** — `func(ResponseWriter, *Request)` 에 `ServeHTTP` 메서드를 단 함수 타입. **함수를 `Handler` 로 바꾸는 어댑터**다.

## 이 주제가 답하려는 질문

1. **1.22 패턴이 무엇을 흡수했나** — 메서드·와일드카드·끝 표시가 없던 시절에 손으로 하던 것.
2. **패턴 둘이 겹치면 무슨 일이 일어나나** — 누가 이기고, 언제 panic 인가.
3. **미들웨어는 왜 `Handler` 를 받아 `Handler` 를 돌려주나** — 그리고 감싸면 무엇이 가려지나.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **라우팅 격자 — 요청 14 × `go` 줄 2 → 상태·핸들러** | 1.22 가 **무엇을 바꿨나** | ★ 본체 창 · 스크립트가 **탭 4칸**을 검사하고 갈린 칸을 센다 |
| ★★★ **등록 panic 문구** | 겹치는 패턴을 **누가 막나** | (3)절 |
| ★★ **미들웨어 로그** | 사슬의 **들어가고 나오는 순서** · 감싸개가 **본 상태 코드** | (4)절 |
| ★★ **서버 에러 로그 + 클라이언트 에러** | 핸들러 panic 을 **양쪽이 어떻게 보나** | (5)절 |
| ★★ **제5의 상태 — 「기준만 다른 것」** | ★★★ **`감싼 쪽이 본 상태 코드 = 0` 인데 클라이언트는 `200`** — 감싸개도 틀리지 않았고 클라이언트도 틀리지 않았다. **감싸개는 「`WriteHeader` 가 불렸나」를 재고, 클라이언트는 「무엇이 나갔나」를 잰다.** 같은 「상태 코드」가 **다른 사건**을 가리킨다 | (4)절 |
| **부적용 — 성능** | ★★★ **「1.22 라우터가 빠르다/느리다」는 주장하지 않는다** — 재지 않았다 | 규칙 4 |
| **못 잰 것 — HTTP/2 의 `RST_STREAM`** | 문서는 panic 때 HTTP/2 면 스트림을 끊는다고 적는다. `httptest.NewServer` 는 **HTTP/1.1** 이라 **그 갈래는 안 돌렸다** | 규칙 3 |

### (1) ★★ 핸들러는 인터페이스 하나다

`t46hdoc` 의 세 줄이 전부다 — **`ServeHTTP(ResponseWriter, *Request)`**. `ServeMux` 도, 미들웨어도, `http.FileServer` 도 **전부 이것을 만족하는 값**이다.
★★ 그래서 **`mux` 자체가 `Handler`** 다 — `httptest.NewServer(mux)` 가 그렇게 받는다((2)절 소스). [20번 주제](../20-interface-declaration-and-implicit-implementation/)의 「소비자 쪽의 작은 인터페이스」가 표준 라이브러리에서 가장 크게 쓰인 자리다.

### (2) ★★★ 라우팅 격자 — 요청 14 × `go 1.22` 줄 대 `go 1.21` 줄

**언제 쓰나** — 핸들러 안에서 `r.Method` 를 검사하고 `strings.TrimPrefix(r.URL.Path, …)` 로 id 를 자르던 코드를 옮길 때.

```text
===== 소스: t46route.go =====
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
===== 명령: for v in 1.22 1.21; do printf "module ex\n\ngo %s\n" $v > go.mod; echo "[go $v] 기본 GODEBUG 의 httpmuxgo121: $(go list -f "{{.DefaultGODEBUG}}" . | tr "," "\n" | grep httpmuxgo121 || echo 없음)"; go build -trimpath -o prog$v . || exit 1; ./prog$v > rows$v.txt || exit 1; done; paste rows1.22.txt rows1.21.txt | awk -F"\t" "NF!=4 || \$1!=\$3 {bad=1} {printf \"%s\t%s\t%s\n\", \$1, \$2, \$4; m++; if (\$2!=\$4) n++} END {if (bad) print \"칸 수 어긋남\"; printf \"go 1.22 줄과 go 1.21 줄이 갈린 칸 %d / %d\n\", n, m}" =====
[go 1.22] 기본 GODEBUG 의 httpmuxgo121: 없음
[go 1.21] 기본 GODEBUG 의 httpmuxgo121: httpmuxgo121=1
GET /items/7	200 [GET /items/{id}] id="7" path=""	404
HEAD /items/7	200	404
DELETE /items/7	405 Allow: GET, HEAD	404
GET /items/7/	404	404
POST /items	200 [POST /items] id="" path=""	404
GET /items	307 → /items/	404
GET /items/	200 [/items/{$}] id="" path=""	404
GET /files/a/b/c	200 [/files/{path...}] id="" path="a/b/c"	404
GET /lit/7	200 [/lit/{id}] id="7" path=""	404
GET /lit/{id}	200 [/lit/{id}] id="{id}" path=""	200 [/lit/{id}] id="" path=""
GET /static/x.css	200 [/static/] id="" path=""	200 [/static/] id="" path=""
GET /static	307 → /static/	301 → /static/
GET example.com/items/7	200 [example.com/] id="" path=""	200 [example.com/] id="" path=""
GET /nope	404	404
go 1.22 줄과 go 1.21 줄이 갈린 칸 10 / 14
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **첫 두 줄 — `go 1.22` 줄의 기본 GODEBUG 에는 `httpmuxgo121` 이 없고, `go 1.21` 줄에는 `httpmuxgo121=1` 이 들어간다.** 컴파일러도 소스도 같다 — **`go.mod` 한 줄**이 기본값을 바꿨다([41번 주제](../41-modules-go-mod-version-selection-and-workspaces/)의 `go` 줄).
- ★★★ **1.22 — `GET /items/7` 은 `[GET /items/{id}] id="7"`**. 핸들러가 `r.PathValue("id")` 로 **이미 잘린 조각**을 받는다. `HEAD /items/7` 도 `200`(「GET matches both GET and HEAD」) — 본문은 비었다.
- ★★★ **1.22 — `DELETE /items/7` 은 `405 Allow: GET, HEAD`** — 경로는 맞는데 메서드가 없다. **핸들러가 `if r.Method != …` 를 쓸 일이 사라졌다.** ★ 이 `405` 는 **`server.go` 의 한 줄**이다(머리말).
- ★★ **`GET /items/7/`(끝 `/`)은 `404`** — `{id}` 는 **한 조각**만 받는다. **`/files/{path...}` 는 `a/b/c` 를 통째로** 받는다(나머지 전부).
- ★★ **`GET /items/` 는 `/items/{$}`** — `{$}` 는 **「여기서 끝」** 이다. `/items/` 가 **하위 전부를 먹는 접두사**가 아니게 한다.
- ★★ **`GET /items` 는 `307 → /items/`** — `/items/` 로 끝나는 **정확한 일치**(`{$}`)가 있어서 리다이렉트됐다. ★ **`POST /items` 가 같은 경로에 있는데도 `405` 가 아니다** — 소스(`matchOrRedirect`)가 **리다이렉트를 먼저** 본다.
- ★★ **`GET /lit/{id}` 라는 글자 그대로의 경로도 `{id}` 에 맞는다** — `id="{id}"`. 와일드카드는 **어떤 한 조각**이든 받는다.
- ★★★ **`Host: example.com` 인 `GET /items/7` 은 `[example.com/]`** — **호스트 있는 패턴이 이긴다**(문서의 「one exception」). 경로가 더 구체적인 `GET /items/{id}` 가 있는데도.
- ★★★ **1.21 열 — 8칸이 `404` 로 바뀌었다.** `GET /items/{id}`·`POST /items` 는 `/` 로 시작하지 않아 **호스트 `GET `·`POST ` 의 패턴**이 됐고(머리말 `servemux121.go:75`), `/items/{$}`·`/files/{path...}`·`/lit/{id}` 는 **글자 그대로의 경로**가 됐다.
  **`GET /lit/{id}`(글자 그대로) 만 `200`** 이고 `id=""` — 문서 「the pattern "/{x}" will match only that path in 1.21」 그대로다.
- ★★ **나머지 둘도 갈렸다** — `GET /lit/{id}` 는 둘 다 `200` 이지만 **`id` 가 `"{id}"` 대 `""`**, `GET /static` 은 둘 다 리다이렉트지만 **`307` 대 `301`**. 8 + 2 = **`10 / 14`**.
- ★★ **안 갈린 넷** — `/static/x.css`(접두사 패턴은 옛날에도 있었다) · `example.com/` · `/items/7/`·`/nope`(둘 다 `404`).

```text
   ★★★ 1.22 패턴이 흡수한 것 — 핸들러 안에서 손으로 하던 일

   1.21 까지 핸들러 안                         1.22 패턴
   if r.Method != "GET" { 405 … }             "GET /items/{id}"   → 405 + Allow 를 mux 가
   id := strings.TrimPrefix(path, "/items/")  r.PathValue("id")
   if strings.Contains(id, "/") { 404 }       {id} 는 한 조각 — /items/7/ 는 404
   if path == "/items/" { 목록 }               "/items/{$}"
   if r.Host == "example.com" { … }           "example.com/"
```

비용 — 이 문서는 재지 않았다.

### (3) ★★★ 겹치는 패턴 — 등록할 때 panic

```text
===== 소스: t46conflict.go =====
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
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && ./prog =====
vet exit=0
[/items/{id}] + [/items/{name}]
    panic: pattern "/items/{name}" (registered at ex/t46conflict.go:17) conflicts with pattern "/items/{id}" (registered at ex/t46conflict.go:16):
/items/{name} matches the same requests as /items/{id}
[/items/] + [/items/{rest...}]
    panic: pattern "/items/{rest...}" (registered at ex/t46conflict.go:17) conflicts with pattern "/items/" (registered at ex/t46conflict.go:16):
/items/{rest...} matches the same requests as /items/
[/b/{x}/c] + [/b/c/{y}]
    panic: pattern "/b/c/{y}" (registered at ex/t46conflict.go:17) conflicts with pattern "/b/{x}/c" (registered at ex/t46conflict.go:16):
/b/c/{y} and /b/{x}/c both match some paths, like "/b/c/c".
But neither is more specific than the other.
/b/c/{y} matches "/b/c/y", but /b/{x}/c doesn't.
/b/{x}/c matches "/b/x/c", but /b/c/{y} doesn't.
[GET /a/{x}] + [/a/{x}]
    등록됨
[/a/{x}] + [/a/new]
    등록됨
[/d] + [/d]
    panic: pattern "/d" (registered at ex/t46conflict.go:17) conflicts with pattern "/d" (registered at ex/t46conflict.go:16):
/d matches the same requests as /d
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`/items/{id}` + `/items/{name}` → panic** — 「**matches the same requests as**」. 와일드카드 **이름은 매칭에 안 쓰인다** — 둘은 같은 패턴이다.
- ★★ **`/items/` + `/items/{rest...}` → panic** — 접두사 패턴과 `{…}` 나머지 와일드카드가 **같은 요청 집합**이다.
- ★★★ **`/b/{x}/c` + `/b/c/{y}` → panic, 그리고 이유를 예로 든다** — 「both match some paths, like "/b/c/c". But neither is more specific than the other.」 이어서 **한쪽만 맞는 경로를 하나씩** 보여 준다. **문서의 「more specific」 정의를 에러가 직접 계산해 준다.**
- ★★ **`GET /a/{x}` + `/a/{x}` 는 등록됨** — 메서드가 있는 쪽이 **더 구체적**(요청 집합이 부분집합)이다. **`/a/{x}` + `/a/new` 도 등록됨** — 글자 조각이 와일드카드보다 구체적이다.
- ★★ **`/d` + `/d` → panic** — 같은 패턴 두 번도 같은 문구다.
- ★★ **panic 이 「등록한 줄」을 둘 다 가리킨다** — `registered at ex/t46conflict.go:16` · `:17`. **실행 전에, 서버가 뜨기 전에** 터지므로 배포 전 기동에서 잡힌다.

비용 — 없다.

### (4) ★★★ 미들웨어 — `func(http.Handler) http.Handler`

```text
===== 소스: t46mw.go =====
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
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && ./prog =====
vet exit=0
── GET /chain → 클라이언트가 받은 상태 200 ──
    A 들어감
    B 들어감
    C 들어감
    핸들러
    w.(http.Flusher) ok=true · ResponseController.Flush err=<nil>
    C 나옴
    B 나옴
    A 나옴
── GET /ok → 클라이언트가 받은 상태 200 ──
    핸들러
    w.(http.Flusher) ok=false · ResponseController.Flush err=feature not supported
    감싼 쪽이 본 상태 코드 = 0
── GET /nf → 클라이언트가 받은 상태 404 ──
    핸들러
    w.(http.Flusher) ok=false · ResponseController.Flush err=feature not supported
    감싼 쪽이 본 상태 코드 = 404
── GET /ok-unwrap → 클라이언트가 받은 상태 200 ──
    핸들러
    w.(http.Flusher) ok=false · ResponseController.Flush err=<nil>
    감싼 쪽이 본 상태 코드 = 0
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`/chain` — `A 들어감 → B 들어감 → C 들어감 → 핸들러 → C 나옴 → B 나옴 → A 나옴`**. `mw("A")(mw("B")(mw("C")(final)))` 은 **바깥부터 들어가 안쪽부터 나온다** — `defer` 의 LIFO([26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/))와 같은 모양이다. **「나옴」 쪽에서 하는 일(시간 기록·로그)은 역순**으로 돈다.
- ★★★ **`/ok` — 핸들러가 `WriteHeader` 를 안 불렀다 → `감싼 쪽이 본 상태 코드 = 0` · 클라이언트는 `200`**. 첫 `Write` 가 **안쪽 `w` 에서 암묵으로** `200` 을 내보냈는데, 그 일은 **감싸개의 `WriteHeader` 를 거치지 않았다.** 감싸개를 `status: 200` 으로 **초기화하지 않으면** 로그에 `0` 이 찍힌다.
- ★★ **`/nf` — `WriteHeader(404)` 를 부르면 `404` 를 본다** — 감싸개가 잡는 것은 **명시적 호출**뿐이다.
- ★★★ **감싸면 `w.(http.Flusher)` 가 `false`** — `rec` 는 `http.ResponseWriter` 를 **임베드**했지만 `Flush` 는 **그 인터페이스에 없는** 메서드라 승격되지 않는다([18번 주제](../18-embedding-and-field-method-promotion/)). `ResponseController.Flush` 도 `feature not supported`.
- ★★★ **`/ok-unwrap` — `Unwrap() http.ResponseWriter` 를 달면 `ResponseController.Flush err=<nil>`** — 타입 단언은 여전히 `false` 지만, **`ResponseController` 는 `Unwrap` 을 따라 내려가** 원래 `Flusher` 를 찾는다(1.20).

```text
   ★★ 감싸개가 가리는 것

   원래 w : ResponseWriter + Flusher + Hijacker …
   rec{ResponseWriter: w}
        └ 겉으로 보이는 메서드 = ResponseWriter 셋(Header·Write·WriteHeader) + 내가 단 것
          w.(http.Flusher)                 → false   (가려짐)
          ResponseController(rec).Flush()  → feature not supported
   recU = rec + Unwrap()
          ResponseController(recU).Flush() → nil     (Unwrap 을 따라 원래 w 로)
```

비용 — 없다.

### (5) ★★ 핸들러 panic — 서버는 살고 연결은 끊긴다

```text
===== 소스: t46panic.go =====
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
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && ./prog =====
vet exit=0
GET /boom  → err=Get "http://127.0.0.1:<포트>/boom": EOF
    서버 로그 첫 줄: http: panic serving 127.0.0.1:<포트>: boom
    서버 로그에 새 줄이 생겼나 true · 그 안에 goroutine 머리줄이 있나 true
GET /abort → err=Get "http://127.0.0.1:<포트>/abort": EOF
    서버 로그에 새 줄이 생겼나 false · 그 안에 goroutine 머리줄이 있나 false
GET /ok    → 200 "ok"
    서버 로그에 새 줄이 생겼나 false · 그 안에 goroutine 머리줄이 있나 false
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`/boom` — 클라이언트는 `Get "…/boom": EOF`** · 서버 로그 첫 줄 **`http: panic serving 127.0.0.1:<포트>: boom`** + 스택(`goroutine` 머리줄 있음). 핸들러가 `"part"` 를 **먼저 썼는데도** 클라이언트는 그것을 **응답으로 못 받았다** — 서버가 **연결을 끊었다**(문서 「either closes the network connection …」).
- ★★ **`/abort` — `panic(http.ErrAbortHandler)` 는 클라이언트 쪽은 같은 `EOF`, 서버 로그는 새 줄 없음** — 문서 「panic with the value ErrAbortHandler」.
- ★★★ **`/ok` — 그 뒤 요청은 `200 "ok"`** — **서버 프로세스는 안 죽었다.** 핸들러를 돌린 고루틴 안에서 서버가 `recover` 했다 — [27번 주제](../27-panic-recover-and-where-to-use-them/)는 **다른 고루틴의 패닉은 못 잡는다**를 보였다. 서버는 **핸들러를 돌리는 바로 그 고루틴**에 `recover` 를 걸어 둔 셈이다(문서 「It recovers the panic」).
- ★★ **그래서 「핸들러에서 panic 해도 안전하다」가 아니다** — 클라이언트는 **상태 코드 없이 끊긴다.** 500 을 주고 싶으면 **미들웨어가 `recover` 해서 `WriteHeader(500)`** 을 불러야 한다 — ★ 이 문서는 그 미들웨어를 **안 던졌다.**

비용 — 없다.

## 문법 — 형태와 규칙

### 형태

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

규칙 불릿.

- ★★★ **패턴은 `[METHOD ][HOST]/[PATH]`** — `{name}` 은 한 조각 · `{name...}` 은 나머지 · `{$}` 는 끝. 값은 **`r.PathValue("name")`**.
- ★★★ **겹치는 패턴은 등록 시 panic** — 한쪽이 **엄격히 더 구체적**이어야 공존한다. 호스트가 있는 쪽은 예외로 이긴다.
- ★★★ **`go.mod` 의 `go` 줄이 1.21 이하면 옛 의미** — 메서드 패턴이 **호스트**로, 와일드카드가 **글자**로 읽힌다.
- ★★ **미들웨어는 `func(http.Handler) http.Handler`** — 바깥부터 들어가 안쪽부터 나온다.
- ★★ **`ResponseWriter` 감싸개는 상태 기본값을 `200` 으로** · `Flusher` 등이 필요하면 **`Unwrap()`** 을 달고 `ResponseController` 를 쓴다.
- ★★ **핸들러 panic 은 연결을 끊는다** — 500 이 필요하면 `recover` 미들웨어.

### 금지 사례 — 누가 잡나

| 쓴 꼴 | 누가 잡나 | 어디서 |
|---|---|---|
| `/items/{id}` 와 `/items/{name}` 을 둘 다 등록 | ★★★ **등록 시 panic**(두 줄의 위치까지) | (3)절 |
| `go 1.21` 모듈에서 `GET /items/{id}` | ★★★ **아무도 안 잡는다** — 조용히 `404` | (2)절 |
| 감싸개 `status` 를 0 으로 두고 로그 | ★★ **아무도 안 잡는다** — `0` 이 찍힌다 | (4)절 |
| 감싼 `w` 에 `w.(http.Flusher)` | ★★ **`ok=false`** — 스트리밍이 조용히 안 된다 | (4)절 |
| 핸들러에서 panic 으로 에러 응답 | ★★ **클라이언트는 `EOF`** — 상태 코드 없음 | (5)절 |

## 어디서 틀리나

### 1. ★★★ 「1.22 패턴은 툴체인만 올리면 켜진다」

- (2)절 — **`go.mod` 의 `go` 줄**이 정한다. `go 1.21` 이면 **`10 / 14`** 칸이 바뀐다.

### 2. ★★★ 「와일드카드 이름이 다르면 다른 패턴이다」

- (3)절 — **`{id}` 와 `{name}` 은 같은 패턴** — 등록 panic.

### 3. ★★ 「경로가 맞고 메서드가 틀리면 늘 `405`」

- (2)절 — **`GET /items` 는 `307`** 로 갔다. 끝 `/` 리다이렉트가 **먼저**다. 그리고 `405` 는 문서가 아니라 **소스의 한 줄**이다.

### 4. ★★ 「경로가 더 구체적인 패턴이 이긴다」

- (2)절 — **호스트 패턴이 이긴다**(`example.com/` 이 `GET /items/{id}` 를 눌렀다).

### 5. ★★★ 「감싸개로 상태 코드를 다 잡을 수 있다」

- (4)절 — **`WriteHeader` 없는 `200` 은 `0`** 으로 보인다. 그리고 **`Flusher` 가 가려진다.**

### 6. ★★ 「핸들러가 panic 하면 서버가 죽는다」 / 「500 이 나간다」

- (5)절 — **둘 다 아니다** — 서버는 살고(`/ok` → `200`) 클라이언트는 **`EOF`**.

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| `Handler` 를 암묵 구현 | **명세** | (1)절 · 20번 |
| ★★★ 패턴 문법·구체성·충돌 panic·호스트 우선 | **표준 라이브러리 계약** | `t46mdoc` · (2)·(3)절 |
| `GET` 이 `HEAD` 도 받음 | **표준 라이브러리 계약** | `t46mdoc` · (2)절 |
| ★★★ `httpmuxgo121` · `go` 줄 1.21 이하면 옛 의미 | **표준 라이브러리 계약** + **`go` 줄이 GODEBUG 기본값을 정하는 규칙** | `t46mdoc` · (2)절 첫 두 줄 |
| ★★ `405` + `Allow` · `307`/`301` | **구현**(`server.go`·`servemux121.go`) | `t46impl` |
| 리다이렉트가 405 보다 먼저 | **구현**(`matchOrRedirect`) | (2)절 `GET /items` |
| panic → recover·로그·연결 끊기 · `ErrAbortHandler` | **표준 라이브러리 계약** | `t46hdoc` · (5)절 |
| `ResponseController` 가 `Unwrap` 을 따른다 | **표준 라이브러리 계약**(1.20) | (4)절 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 메서드·경로 조각으로 나누기 | ★★★ **1.22 패턴 + `PathValue`** — `go.mod` 가 `go 1.22` 이상인지 확인 | (2)절 |
| 「목록」과 「하위 전부」를 가르기 | **`/items/{$}`** 대 **`/items/`** | (2)절 |
| 공통 전·후처리 | **`func(http.Handler) http.Handler` 사슬** — 순서는 바깥부터 | (4)절 |
| 상태 코드 로그 | 감싸개 기본값 `200` + **`Unwrap()`** | (4)절 |
| 핸들러 안의 예기치 못한 panic | **`recover` 미들웨어로 500** — 기본은 `EOF` 로 끊긴다 | (5)절 |
| 서버 계층·정상 종료 설계 | [`systems/server-design`](../../../../../systems/server-design/) | 정본 |

## 핵심 문장

- ★★★ **`Handler` 는 메서드 하나짜리 인터페이스다** — `ServeMux` 도 미들웨어도 그것을 만족하는 값이다.
- ★★★ **1.22 패턴은 메서드·한 조각(`{id}`)·나머지(`{p...}`)·끝(`{$}`)을 mux 가 가르게 했다** — `DELETE` 는 `405 Allow: GET, HEAD`(이 판 소스).
- ★★★ **`go.mod` 의 `go 1.21` 줄이면 같은 소스가 옛 의미로 돈다** — 갈린 칸 `10 / 14`, `{id}` 는 글자 그대로.
- ★★★ **겹치는 패턴은 등록할 때 panic** — `{id}` 와 `{name}` 은 같은 패턴이다.
- ★★ **미들웨어는 바깥부터 들어가 안쪽부터 나온다** — 상태 감싸개는 `WriteHeader` 없는 `200` 을 `0` 으로 보고, `Flusher` 를 가린다(`Unwrap` 으로 되찾는다).
- ★★ **핸들러 panic 은 서버가 recover 하고 연결을 끊는다** — 클라이언트는 `EOF`, 서버는 산다.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 46번)
- [43번 주제](../43-io-reader-writer-and-composition/)(`io.Reader`/`Writer`) — ★ 목록상 선행 · `ResponseWriter` 는 `io.Writer` 이고 `Request.Body` 는 `io.ReadCloser`
- [20번 주제](../20-interface-declaration-and-implicit-implementation/)(작은 인터페이스) · [18번 주제](../18-embedding-and-field-method-promotion/)(임베드와 승격) · [26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/)(LIFO) · [27번 주제](../27-panic-recover-and-where-to-use-them/)(recover) · [41번 주제](../41-modules-go-mod-version-selection-and-workspaces/)(`go` 줄)
- [`systems/server-design`](../../../../../systems/server-design/) — ★★ **서버 구조 설계의 정본** · [02 요청 경로 §5 앱 계층](../../../../../systems/server-design/02-request-path.md)(세션·연결 관리·정상 종료) — 여기는 `net/http` 표면으로 좁힘
- [목록의 **47번 주제**](../47-net-http-client-reuse-timeouts-and-closing-body/)(클라이언트 — 이 서버에 요청을 보내는 쪽)

## 용어 풀이

- **`http.Handler`** — `ServeHTTP(ResponseWriter, *Request)` 하나짜리 인터페이스.
- **`http.HandlerFunc`** — 함수를 `Handler` 로 쓰게 하는 함수 타입.
- **`ServeMux`** — 패턴 → 핸들러 표. 가장 구체적인 패턴을 고른다.
- **패턴** — `[METHOD ][HOST]/[PATH]`. `{name}` · `{name...}` · `{$}`.
- **`r.PathValue(name)`** — 와일드카드에 맞은 조각.
- **더 구체적(more specific)** — 한 패턴이 맞는 요청이 다른 패턴이 맞는 요청의 **진부분집합**.
- **`httpmuxgo121`** — 1.21 라우팅 의미로 되돌리는 GODEBUG 설정. `go` 줄이 1.21 이하면 기본으로 켜진다.
- **미들웨어** — `Handler` 를 받아 `Handler` 를 돌려주는 함수. 앞뒤로 일을 끼운다.
- **`http.ResponseController`** — 감싼 `ResponseWriter` 에서도 `Unwrap` 을 따라 `Flush` 등을 부르는 도우미(1.20).
- **`http.ErrAbortHandler`** — 이 값으로 panic 하면 서버가 로그 없이 연결만 끊는다.

---

## 더 들어가면

- ★ **`recover` 로 500 을 주는 미들웨어** — 모양은 (5)절에서 추론했고 **안 던졌다.**
- ★ **HTTP/2 에서의 panic**(`RST_STREAM`) — `httptest.NewServer` 가 HTTP/1.1 이라 **못 쟀다.**
- ★ **경로 이스케이프(`%2F`)** — 문서가 1.21 과의 차이로 적는 자리다. 한 번 던졌다가 **클라이언트가 경로를 먼저 정리해** 서버가 무엇을 받았는지 가를 수 없어 **격자에서 뺐다.**

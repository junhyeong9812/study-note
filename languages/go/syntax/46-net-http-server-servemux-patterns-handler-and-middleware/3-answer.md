# go/syntax/46 — `net/http` 서버: `ServeMux` 패턴(1.22)·`Handler`·미들웨어 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★ **근거로 읽을 칸** — 상태 코드 · `Allow` · 리다이렉트 대상 · 핸들러 이름 · `PathValue` · `10 / 14` · panic 문구 · 로그 순서.
> **가린 칸** — 서버 포트(`<포트>`).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `GET`·`HEAD /items/7` 은 `200 {id}=7` · `DELETE` 는 `405 Allow: GET, HEAD` · `/items/7/` 는 `404` · `GET /items` 는 `307 → /items/` · `/items/` 는 `{$}` · `/files/a/b/c` 는 `path="a/b/c"` · `/lit/{id}` 는 `id="{id}"` · `Host: example.com` 은 `example.com/` 이 이긴다

**출력**

```text
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

**왜 그런가** (둘째 칸이 `go 1.22` 줄이다)

- ★★★ 문서 — 패턴은 `[METHOD ][HOST]/[PATH]` · **`GET` 은 `HEAD` 도** · **더 구체적인 쪽이 이기고 호스트 있는 쪽이 예외로 이긴다.**
- ★★ `{id}` 는 **한 조각**이라 `/items/7/` 은 `404`, `{path...}` 는 나머지 전부, `{$}` 는 끝.

### 2. **10 / 14 가 갈린다** — 메서드 패턴 둘은 **호스트 `GET `·`POST ` 의 패턴**이 돼 `404`, 와일드카드 패턴은 **글자 그대로** — `/lit/{id}` 만 `200`(`id=""`) · `/static` 은 `301` · 안 갈린 것은 `/static/x.css`·`example.com/`·`/items/7/`·`/nope`

- ★★★ 1번 출력 **셋째 칸**과 마지막 줄. 첫 두 줄 — `go 1.21` 줄이면 **기본 GODEBUG 에 `httpmuxgo121=1`** 이 들어간다.
- ★★★ 1.21 규칙은 **`/` 로 시작하지 않는 패턴을 호스트 패턴**으로 읽는다(`servemux121.go:75`) — `GET /items/{id}` 는 「호스트 `GET ` 의 `/items/{id}`」가 된다. 문서 「the pattern "/{x}" will match only that path in 1.21」.

### 3. 끝 `/` 리다이렉트를 **먼저** 본다 — `/items/` 가 `/items/{$}` 에 **정확히** 맞아서 `307 → /items/` · `DELETE /items/7` 은 그 경로에 **리다이렉트할 곳이 없고** 메서드만 안 맞아 `405`

- ★★ 문서의 「Trailing-slash redirection」 — 끝 `/` 없는 요청을 `/` 를 붙여 **리다이렉트**한다. 이 판 소스(`matchOrRedirect`)는 그 검사를 **메서드 검사보다 앞에** 둔다.
- ★ 그래서 **「경로가 맞고 메서드가 틀리면 늘 `405`」가 아니다.**

### 4. **소스의 한 줄**이다 — `go doc net/http.ServeMux` 에는 `405` 가 없고, `server.go:2759` 가 `Allow` 를 달아 `StatusMethodNotAllowed` 를 쓴다

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

- ★★ 확인법 — 문서를 `grep` 해 숫자가 **없음**을 보고, 이 툴체인의 `$(go env GOROOT)/src/net/http/server.go` 에서 그 줄을 찾는다. 리다이렉트 코드도 새 쪽 `307` · 옛 쪽 `301` 로 **소스가 정한다.**

### 5. `{id}`+`{name}` · `/items/`+`{rest...}` · `/b/{x}/c`+`/b/c/{y}` · `/d`+`/d` 는 **panic** · `GET /a/{x}`+`/a/{x}` 와 `/a/{x}`+`/a/new` 는 **등록됨**

**출력**

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

- ★★★ 문서 「If neither is more specific, then the patterns conflict … those functions **panic**」. 문구가 **두 등록 위치**(`:16`·`:17`)와, 겹치는데 서로 포함하지 않는 경우엔 **예시 경로**까지 준다.

### 6. `/a/new` 가 맞는 요청은 `/a/{x}` 가 맞는 요청의 **진부분집합**이다 — 그래서 `/a/new` 가 「더 구체적」이고 공존한다 · `{id}` 와 `{name}` 은 **요청 집합이 똑같아** 어느 쪽도 더 구체적이지 않다

- ★★★ 문서 「A pattern P1 is more specific than P2 if P1 matches a **strict subset** of P2’s requests」. 와일드카드 **이름은 집합을 안 바꾼다.**
- ★★ `GET /a/{x}` 도 같은 이유로 `/a/{x}` 보다 구체적이다(메서드가 요청을 좁힌다).

### 7. `/chain` 은 `A·B·C 들어감 → 핸들러 → C·B·A 나옴`(`Flusher` 있음) · `/ok` 는 `200` 인데 **감싼 쪽 `0`**(`Flusher` 없음 · `feature not supported`) · `/nf` 는 `404`/`404` · `/ok-unwrap` 은 `200`/`0` 이지만 **`ResponseController.Flush` 가 `<nil>`**

**출력**

```text
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

- ★★★ `mw("A")(mw("B")(mw("C")(final)))` — **바깥이 먼저 불리고 안쪽이 먼저 끝난다.**
- ★★ `rec` 는 `ResponseWriter` 만 임베드했으므로 **겉으로는 그 세 메서드**만 있다 — `Flusher` 단언이 `false`.

### 8. 핸들러가 `WriteHeader` 를 **안 불렀다** — 첫 `Write` 가 **안쪽 `w` 에서** 암묵으로 `200` 을 냈고, 감싸개의 `WriteHeader` 는 **한 번도 안 불렸다** · 고치기 — **`status` 기본값을 `200`** 으로(또는 `Write` 도 가로채기) · **`Unwrap()` 을 달고 `ResponseController` 로** `Flush`

- ★★★ 제5의 상태 — 감싸개는 「`WriteHeader` 호출」을, 클라이언트는 「나간 응답」을 잰다. **같은 「상태 코드」가 다른 사건**이다.
- ★★ `/ok-unwrap` — 단언은 여전히 `false` 지만 `ResponseController` 는 `Unwrap` 을 따라 원래 `w` 의 `Flush` 를 찾았다.

### 9. `/boom` — 클라이언트 `EOF` · 서버 로그 `http: panic serving 127.0.0.1:<포트>: boom` + 스택 · `/abort` — 클라이언트 `EOF` · 로그 없음 · `/ok` — `200 "ok"` · `"part"` 는 **도착하지 않는다**

**출력**

```text
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

- ★★★ 문서 — 서버가 **recover 하고, 스택을 에러 로그에 남기고, 연결을 닫는다.** `ErrAbortHandler` 로 panic 하면 **로그 없이** 끊는다.
- ★★ 서버는 산다(`/ok` 가 `200`). 클라이언트는 **상태 코드 없이** 끊긴다 — 500 을 원하면 `recover` 미들웨어가 필요하다.

### 10. **무엇이든 `Handler` 가 된다** — `ServeMux`·미들웨어·`HandlerFunc` 가 서로를 감싸 한 줄로 이어진다 · 대가는 **감싸면 원래 값의 다른 메서드가 가려지는 것**

- ★★★ 메서드 하나라 **감싸개가 쉽다** — 미들웨어는 `Handler` 를 받아 `Handler` 를 돌려주는 함수일 뿐이다. [20번 주제](../20-interface-declaration-and-implicit-implementation/) (6)절이 **한 메서드 `5/5` · 네 메서드 `1/5`** 로 보인 「작은 인터페이스를 만족하는 타입이 더 많다」가 여기서는 「무엇이든 감쌀 수 있다」가 된다.
- ★★ 그런데 감싸개는 **자기가 선언한 메서드만** 보인다 — `http.ResponseWriter` 를 감싸면 원래 값이 가진 `Flusher`·`Hijacker` 가 **동적 단언에서 사라진다.** [43번 주제](../43-io-reader-writer-and-composition/)·[44번 주제](../44-os-bufio-and-io-copy/)에서 래퍼가 `WriterTo`/`ReaderFrom` 을 가려 `io.Copy` 의 길이 바뀐 것과 **같은 집안**이다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 로 **★고칠 것 0** |
| ★★★ 라우팅 격자 (`t46route`) | 요청 14 × `go.mod` 의 `go 1.22`/`go 1.21` · `paste` 후 탭 4칸 검사 | 캡처마다 | **`10 / 14`** |
| ★★ 충돌 (`t46conflict`) | 여섯 쌍 · `recover` 로 panic 문구 | 캡처마다 | panic 넷 · 등록 둘 |
| ★★ 미들웨어 (`t46mw`) | 요청 넷 · 로그 | 캡처마다 | 들어간 순의 역순으로 나옴 · 감싼 쪽 `0` |
| ★★ panic (`t46panic`) | 서버 `ErrorLog` 를 버퍼로 · 포트 가림 | 캡처마다 | `EOF` · 로그 첫 줄 |

**구현·환경에 달린 항목**

| 항목 | 무엇에 달렸나 |
|---|---|
| 패턴 문법·구체성·충돌 panic·호스트 우선·`HEAD`·`httpmuxgo121` | **표준 라이브러리 문서의 계약** |
| `405`·`307`/`301`·리다이렉트가 먼저 | **이 판 소스의 구현** |
| panic 의 recover·로그·끊기 | **표준 라이브러리 문서의 계약**(HTTP/2 갈래는 못 잼) |
| 포트 | **실행마다** — 소스에서 가렸다 |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다(기본 규칙만). 외부 네트워크는 필요 없다.

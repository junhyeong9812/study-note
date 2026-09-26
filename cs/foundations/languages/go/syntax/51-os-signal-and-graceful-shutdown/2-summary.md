# go/syntax/51 — `os/signal`과 정상 종료 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [`os/signal`](https://pkg.go.dev/os/signal) 패키지 문서(「Default behavior of signals in Go programs」 · `NotifyContext`) · [`net/http.Server.Shutdown`](https://pkg.go.dev/net/http#Server.Shutdown) · `Server.Close`. **이 툴체인에서 직접 떴다.**\
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.
> ★★ 서버는 **`httptest` 가 아니라 실제 자식 프로세스**다 — 구동기(`drive.go`)가 `./server` 를 띄우고, 느린 요청(2초)이 **핸들러에 들어간 것을 서버 로그로 확인한 뒤** 신호를 보낸다. 시간으로 맞추지 않고 **로그 줄로 맞췄다.**\
> **버전** — `Server.Shutdown`·`ErrServerClosed` 는 1.8 · `signal.NotifyContext` 는 1.16(이 툴체인의 `api/go1*.txt` — [49번 주제](../49-testing-table-driven-t-run-cleanup-and-parallel/) 「이 판」의 `tapi`) · 신호가 `context.Cause` 로 보이는 것은 이 판의 `NotifyContext` 문서가 적는다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체는 넷째 창이다** — 「**종료 경로 격자** — 서버 종료 방식 8(`NotifyContext`→`Shutdown(5s)` · `Shutdown(100ms)` · `Close()` · 신호 처리 없음 · `Shutdown` 을 고루틴에서 부르고 `main` 은 `Serve` 반환에서 끝냄 · `stop()` 뒤 두 번째 신호 · `stop()` 없이 두 번째 신호 · `SIGKILL`) × 관찰 4(느린 요청이 받은 것 · 종료 중 새 요청 · 서버 종료 상태 · 서버 로그 순서)」.
마지막 줄 「**진행 중 요청이 끝까지 간 칸 2 / 8**」((1)절). ★★★ **여덟 중 둘만 `200 done` 을 받았다 — 둘 다 `main` 이 `Shutdown` 의 반환을 기다린 칸이다.**
★★ 짝이 되는 창은 「**셸이 본 종료 상태**」 — `143` · `0` · `137`((3)절). Go 프로그램이 돌려준 것과 셸이 **보고한** 것은 층이 다르다.

★★★ **이 주제의 경계** — 우아한 종료 **패턴**(RUNNING→DRAINING→STOPPED · 헬스체크 · 기한 잡기)의 정본은 [`ops-patterns/19-graceful-shutdown`](../../../../../ops-patterns/19-graceful-shutdown/) 이다. 여기는 **Go 에서의 배선** — `signal.NotifyContext` → `srv.Shutdown(ctx)` → `main` 이 기다리기 — 으로 좁힌다.
`context` 취소 전파는 [34번 주제](../34-context-cancellation-deadlines-and-values/) · `Handler`·`ServeMux` 는 [46번 주제](../46-net-http-server-servemux-patterns-handler-and-middleware/) · 클라이언트 쪽 에러 판별(`errors.Is`)은 [47번 주제](../47-net-http-client-reuse-timeouts-and-closing-body/) 가 정본이다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 이 주제에서 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | ★★ **`main` 이 반환하면 프로그램이 끝나고 다른 고루틴을 기다리지 않는다** — (1)절 `E` 칸 사고의 뿌리 |
| **표준 라이브러리 계약** | `go doc` 이 적은 것 | ★★★ **`Shutdown` 은 리스너를 먼저 닫고, 쉬는 연결을 닫고, 활성 연결이 쉴 때까지 기다린다** · ★★★ **`Shutdown` 을 부르면 `Serve`·`ListenAndServe` 가 즉시 `ErrServerClosed`** — 「Make sure the program doesn't exit and waits instead for Shutdown to return」 · `Close` 는 **즉시** 닫는다 · `NotifyContext` 의 `stop` 은 **기본 동작을 되돌린다** · SIGINT·SIGTERM 의 기본 동작은 **종료** |
| **OS·셸** | 커널과 셸이 정한 것 | ★★★ **`SIGKILL` 은 못 잡는다**(커널 — `os/signal` 문서도 그렇게 적는다) · ★★ **`143`·`137` 은 셸의 관례**(128 + 신호 번호)이지 Go 의 종료 코드가 아니다 · 클라이언트가 본 `EOF` 는 **커널이 연결을 닫은 결과** |

★★★ **선을 긋는다** — 「`Shutdown` 은 진행 중 요청을 기다린다」는 **문서의 계약**이다. 「`main` 이 먼저 끝나면 기다림이 끊긴다」는 **명세**(`main` 반환 = 프로그램 종료)와 계약(`Serve` 가 즉시 돌아온다)이 **만나서 생기는 사고**다 — 이 문서는 그 한 쌍을 (1)절 `A` 대 `E` 로 **직접 냈다.** 「클라이언트가 `EOF` 를 받는다」는 **이 머신·이 판의 관찰**이다(서버가 요청을 다 읽은 뒤 죽었기 때문으로 보인다 — `connection reset` 이 나올 조건은 이 문서가 재지 않았다).

## 이 판

```text
===== 명령: go version; "$GO125" version; go env CGO_ENABLED; nproc =====
go version go1.27.1 linux/amd64
go version go1.25.12 linux/amd64
1
24
(exit 0)
```

```text
===== 명령: go doc os/signal | sed -n "10,11p;32,33p"; go doc os/signal.NotifyContext | sed -n "9,14p"; go doc net/http.Server.Shutdown | sed -n "4,13p"; go doc net/http.Server.Close | sed -n "4,6p" =====
The signals SIGKILL and SIGSTOP may not be caught by a program, and therefore
cannot be affected by this package.
By default, a synchronous signal is converted into a run-time panic. A SIGHUP,
SIGINT, or SIGTERM signal causes the program to exit. A SIGQUIT, SIGILL,
    The stop function unregisters the signal behavior, which, like signal.Reset,
    may restore the default behavior for a given signal. For example,
    the default behavior of a Go program receiving os.Interrupt is to exit.
    Calling NotifyContext(parent, os.Interrupt) will change the behavior to
    cancel the returned context. Future interrupts received will not trigger the
    default (exit) behavior until the returned stop function is called.
    Shutdown gracefully shuts down the server without interrupting any active
    connections. Shutdown works by first closing all open listeners, then
    closing all idle connections, and then waiting indefinitely for connections
    to return to idle and then shut down. If the provided context expires before
    the shutdown is complete, Shutdown returns the context's error, otherwise it
    returns any error returned from closing the Server's underlying Listener(s).

    When Shutdown is called, Serve, ServeTLS, ListenAndServe, and
    ListenAndServeTLS immediately return ErrServerClosed. Make sure the program
    doesn't exit and waits instead for Shutdown to return.
    Close immediately closes all active net.Listeners and any connections
    in state StateNew, StateActive, or StateIdle. For a graceful shutdown,
    use Server.Shutdown.
(exit 0)
```

- ★★★ **「SIGKILL and SIGSTOP may not be caught by a program」** — 잡을 수 없는 신호는 패키지 문서가 먼저 말한다.
- ★★★ **「A SIGHUP, SIGINT, or SIGTERM signal causes the program to exit」** — 아무것도 안 하면 **즉시 종료**다((1)절 `D`).
- ★★★ **`stop` — 「unregisters the signal behavior, which … may restore the default behavior」** — `stop()` 을 부른 뒤의 두 번째 신호는 **다시 기본 동작(종료)** 이다((1)절 `F`).
- ★★★ **`Shutdown` — 「first closing all open listeners, then closing all idle connections, and then waiting indefinitely for connections to return to idle」** · 「**immediately return ErrServerClosed. Make sure the program doesn't exit and waits instead for Shutdown to return**」 — 이 두 문장이 (1)절 `A`·`E` 한 쌍이다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다 — 칸으로 안 만들었다** | 서버 주소의 **포트 번호** · 경과 시간 | 포트는 `127.0.0.1:0` 이 고르고 **구동기가 로그에서 지웠다**(첫 줄 `addr …` 은 싣지 않음). 시간은 재지 않았다 — 순서만 |
| 안 흔들린다 | ★★★ **여덟 칸의 결과 · 서버 로그 순서 · `2 / 8`** | 신호를 **로그 줄(`handler: start`)을 본 뒤** 보냈다 — 예행에서 세 판 md5 가 같았다 |
| 안 흔들린다 | ★★ 셸의 `143`·`0`·`137` | |
| **관찰** | ★★ 클라이언트의 `EOF`(대 `connection reset`) | 서버가 요청을 다 읽은 뒤 죽어 **FIN 이 간 것으로 보인다** — 재대조에서 같았지만 **보장은 아니다** |

★ 정규화 규칙은 **기본 넷**만 썼다.

## 한눈에 — 쉽게 말하면

**`SIGTERM` 은 「문 닫을 시간입니다」 방송이다.** Go 프로그램은 **아무 준비가 없으면 방송을 듣자마자 불을 끄고 나간다**(기본 동작 — 손님이 식사 중이어도).
`signal.NotifyContext` 는 **방송을 「매니저 호출」로 바꿔 놓는 것**이다 — 방송이 오면 `ctx` 가 취소될 뿐, 가게는 아직 안 닫힌다.
그다음 매니저가 `srv.Shutdown(ctx)` 로 **「새 손님 사절」 팻말을 걸고 안의 손님이 다 나갈 때까지 기다린다.**

그런데 가게 주인(`main`)이 **팻말이 걸리는 걸 보자마자 퇴근해 버리면**(`Serve` 가 `ErrServerClosed` 로 돌아온 자리에서 `return`) — **건물 전체가 잠긴다.** 매니저가 기다리던 손님도 쫓겨난다.
**주인은 매니저가 「다 나갔습니다」라고 할 때(`Shutdown` 반환)까지 기다려야 한다.**

| 비유 | 실체 |
|---|---|
| 「문 닫을 시간」 방송 | ★★ **`SIGTERM`**(쿠버네티스·systemd 가 보낸다) |
| 준비 없이 불 끄기 | ★★★ **기본 동작 — 즉시 종료**(`D` 칸 · 셸 `143`) |
| 방송을 매니저 호출로 | ★★★ **`signal.NotifyContext`** — `ctx.Done()` 이 닫힌다 |
| 「새 손님 사절」 + 기다림 | ★★★ **`srv.Shutdown(ctx)`** — 리스너 닫기 → 활성 연결 대기 |
| 기다림에 마감 시각 | ★★ **`Shutdown` 에 준 `ctx` 의 기한**(`B` 칸 — 100ms 면 못 기다린다) |
| 주인이 먼저 퇴근 | ★★★ **`Serve` 반환(`ErrServerClosed`)에서 `main` 이 끝남**(`E` 칸) |
| 즉시 셔터 내리기 | ★★ **`srv.Close()`**(`C` 칸) |
| 건물 강제 철거 | ★★★ **`SIGKILL`** — 아무도 못 막는다(`H` 칸 · 셸 `137`) |

```text
   ★★★ 제대로 된 배선 (A 칸) — main 이 Shutdown 의 반환을 기다린다

   main ── ctx, stop := signal.NotifyContext(bg, SIGTERM, os.Interrupt)
     │     go func() { errc <- srv.Serve(ln) }()        ← Serve 는 고루틴에
     │     <-ctx.Done()            ← SIGTERM 이 여기서 풀어 준다
     │     srv.Shutdown(ctx 5s) ─┬─ 리스너 닫기  → 새 요청 connection refused
     │                            ├─ (Serve 는 여기서 곧바로 ErrServerClosed 를 errc 에)
     │                            └─ 활성 연결 대기 → handler: end → 200 done
     │     ◀── Shutdown 반환 (nil)
     │     <-errc                  ← ErrServerClosed 확인
     ▼     return

   ★★★ 사고 (E 칸) — Serve 를 main 에서 부르고, Shutdown 을 고루틴에

   main ── srv.Serve(ln)  ◀── Shutdown 이 불리자마자 ErrServerClosed 로 돌아온다
     ▼     return          ← 프로세스 끝. 고루틴의 Shutdown 도, 핸들러도 같이 죽는다
```

> **신호(signal)** — 커널이 프로세스에 보내는 비동기 알림. `SIGTERM`(15) 은 「정리하고 끝내라」, `SIGINT`(2) 는 Ctrl-C, `SIGKILL`(9) 은 「그냥 죽어라」(잡을 수 없다).

> **`http.ErrServerClosed`** — `Shutdown`·`Close` 뒤 `Serve`·`ListenAndServe` 가 돌려주는 에러. **정상 종료의 신호**이지 실패가 아니다.

## 이 주제가 답하려는 질문

1. **신호를 받아 진행 중 요청을 끝까지 마치는 종료 경로는 어떻게 배선하나** — 무엇이 `ctx` 를 취소하고, 누가 무엇을 기다리나.
2. **그 배선이 조용히 끊기는 자리는** — `ErrServerClosed` 에서 끝나는 `main` · 너무 짧은 기한 · `Close`.
3. **신호 쪽 경계는** — 두 번째 신호 · 잡을 수 없는 신호 · 셸이 보는 종료 상태.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **종료 경로 격자 — 방식 8 × 관찰 4** | 진행 중 요청이 **끝까지 갔나** · 새 요청은 · 프로세스는 어떻게 끝났나 | ★ 본체 창 · 구동기가 자식 프로세스를 띄우고 **탭 6칸**을 찍고, 스크립트가 칸 수를 검사해 `200` 칸을 센다 |
| ★★ **서버 로그 순서** | `Shutdown` 이 **언제 돌아오나** · `Serve` 가 **언제 돌아오나** | 격자의 마지막 칸 |
| ★★ **셸이 본 종료 상태** | `143`·`0`·`137` | (3)절 `t51shell` |
| ★ **문서** | 계약의 문장 | 머리말 `t51doc` |
| ★★ **제5의 상태 — 「기준만 다른 것」** | ★★★ **`E` 칸의 서버 종료는 `exit 0`** 이고 로그도 `Serve returned: http: Server closed` 로 **정상처럼 끝난다** — 틀린 게 없어 보인다. 그런데 **느린 요청은 `EOF`** 다. 「정상 종료했나」를 **서버의 종료 코드로 물으면 예**, **요청의 운명으로 물으면 아니오**다. ★ `B` 칸은 반대로 `exit 1` 로 **실패를 드러낸다** — 기한을 넘긴 걸 알린다 | (1)절 |
| **대신 쓴 창 — 연결 상태 훅** | 47번은 서버의 `ConnState` 로 연결을 셌다. 여기서는 **클라이언트가 받은 본문(`200 done`)과 서버 로그의 `handler: end`** 두 창으로 「끝까지 갔나」를 물었다 — 둘이 **여덟 칸 모두 일치**했다(`200` 인 칸에만 `handler: end` 가 있다) | (1)절 |
| **부적용 — 시간** | ★★ **종료에 몇 ms 걸렸나는 재지 않았다** — 순서만 | 규칙 4 · 기한 잡기는 ops-patterns 19 |

### (1) ★★★ 종료 경로 격자 — 방식 8 × 관찰 4

**언제 쓰나** — 서버 `main` 을 쓸 때, 그리고 「배포하면 가끔 요청이 끊긴다」를 볼 때.

```text
===== 소스: drive.go =====
package main

import (
	"bufio"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os/exec"
	"strings"
	"syscall"
	"time"
)

type result struct {
	status string
	body   string
}

func get(url string) result {
	c := &http.Client{Timeout: 10 * time.Second}
	resp, err := c.Get(url)
	if err != nil {
		return result{status: classify(err)}
	}
	defer resp.Body.Close()
	b, err := io.ReadAll(resp.Body)
	if err != nil {
		return result{status: fmt.Sprint(resp.StatusCode) + " 본문 " + classify(err)}
	}
	return result{status: fmt.Sprint(resp.StatusCode), body: strings.TrimSpace(string(b))}
}

func classify(err error) string {
	switch {
	case errors.Is(err, syscall.ECONNREFUSED):
		return "connection refused"
	case errors.Is(err, syscall.ECONNRESET):
		return "connection reset"
	case errors.Is(err, io.EOF), errors.Is(err, io.ErrUnexpectedEOF):
		return "EOF"
	}
	return "기타: " + err.Error()
}

// run 은 서버를 자식 프로세스로 띄우고, 느린 요청이 핸들러에 들어간 뒤 신호를 보낸다.
func run(name string, sigs []syscall.Signal, probe bool, args ...string) {
	cmd := exec.Command("./server", args...)
	out, _ := cmd.StdoutPipe()
	if err := cmd.Start(); err != nil {
		fmt.Println(name, "start:", err)
		return
	}
	lines := make(chan string, 64)
	go func() {
		sc := bufio.NewScanner(out)
		for sc.Scan() {
			lines <- sc.Text()
		}
		close(lines)
	}()
	var log []string
	wait := func(prefix string) string {
		for l := range lines {
			log = append(log, l)
			if strings.HasPrefix(l, prefix) {
				return l
			}
		}
		return ""
	}
	addr := strings.TrimPrefix(wait("addr "), "addr ")
	res := make(chan result, 1)
	go func() { res <- get("http://" + addr + "/slow") }()
	wait("handler: start")
	newReq := "-"
	for i, s := range sigs {
		cmd.Process.Signal(s)
		if i == 0 && probe {
			wait("shutdown: start")
			newReq = get("http://" + addr + "/slow").status
		}
		if i+1 < len(sigs) {
			time.Sleep(300 * time.Millisecond)
		}
	}
	r := <-res
	for l := range lines {
		log = append(log, l)
	}
	err := cmd.Wait()
	exit := "exit 0"
	var ee *exec.ExitError
	if errors.As(err, &ee) {
		if ws := ee.Sys().(syscall.WaitStatus); ws.Signaled() {
			exit = "신호로 죽음(" + ws.Signal().String() + ")"
		} else {
			exit = fmt.Sprintf("exit %d", ee.ExitCode())
		}
	}
	fmt.Printf("%s\t%s\t%s\t%s\t%s\t%s\n", name, strings.Join(args, " "), strings.TrimSpace(r.status+" "+r.body), newReq, exit, strings.Join(log[1:], " → "))
}

func main() {
	T, K := syscall.SIGTERM, syscall.SIGKILL
	fmt.Println("칸\t서버 인자\t느린 요청이 받은 것\t종료 중 새 요청\t서버 종료\t서버 로그")
	run("A", []syscall.Signal{T}, true, "-mode", "shutdown", "-grace", "5s")
	run("B", []syscall.Signal{T}, true, "-mode", "shutdown", "-grace", "100ms")
	run("C", []syscall.Signal{T}, false, "-mode", "close")
	run("D", []syscall.Signal{T}, false, "-mode", "none")
	run("E", []syscall.Signal{T}, false, "-mode", "shutdown-goroutine")
	run("F", []syscall.Signal{T, T}, false, "-mode", "shutdown-stop")
	run("G", []syscall.Signal{T, T}, false, "-mode", "shutdown")
	run("H", []syscall.Signal{K}, false, "-mode", "shutdown")
}
===== 소스: go.mod =====
module ex

go 1.27
===== 소스: server.go =====
package main

import (
	"context"
	"errors"
	"flag"
	"fmt"
	"net"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
)

func say(s string) { fmt.Println(s) }

func main() {
	mode := flag.String("mode", "shutdown", "shutdown | shutdown-goroutine | shutdown-stop | close | none")
	grace := flag.Duration("grace", 5*time.Second, "Shutdown 기한")
	flag.Parse()

	mux := http.NewServeMux()
	mux.HandleFunc("/slow", func(w http.ResponseWriter, r *http.Request) {
		say("handler: start")
		time.Sleep(2 * time.Second)
		fmt.Fprintln(w, "done")
		say("handler: end")
	})
	srv := &http.Server{Handler: mux}
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		say("listen: " + err.Error())
		os.Exit(1)
	}
	say("addr " + ln.Addr().String())

	if *mode == "none" {
		err := srv.Serve(ln)
		say("Serve returned: " + err.Error())
		return
	}

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGTERM, os.Interrupt)
	defer stop()

	if *mode == "shutdown-goroutine" {
		go func() {
			<-ctx.Done()
			say("signal received: " + context.Cause(ctx).Error())
			srv.Shutdown(context.Background())
		}()
		err := srv.Serve(ln)
		say("Serve returned: " + err.Error())
		return
	}

	errc := make(chan error, 1)
	go func() { errc <- srv.Serve(ln) }()
	<-ctx.Done()
	say("signal received: " + context.Cause(ctx).Error())
	if *mode == "shutdown-stop" {
		stop()
	}

	if *mode == "close" {
		say("Close: " + fmt.Sprint(srv.Close()))
	} else {
		sctx, cancel := context.WithTimeout(context.Background(), *grace)
		defer cancel()
		say("shutdown: start")
		err := srv.Shutdown(sctx)
		say("shutdown: returned " + fmt.Sprint(err))
		if err != nil {
			os.Exit(1)
		}
	}
	err = <-errc
	say("Serve returned: " + err.Error() + " · ErrServerClosed? " + fmt.Sprint(errors.Is(err, http.ErrServerClosed)))
}
===== 명령: go vet ./... ; echo "vet exit=$?"; go build -trimpath -o server ./srv && go build -trimpath -o drv ./drive || exit 1; ./drv > rows.txt; echo "drive exit=$?"; awk -F"\t" "NF!=6 {bad=1} {print} NR>1 {m++; if (\$3 ~ /^200/) n++} END {if (bad) print \"칸 수 어긋남\"; printf \"진행 중 요청이 끝까지 간 칸 %d / %d\n\", n, m}" rows.txt =====
vet exit=0
drive exit=0
칸	서버 인자	느린 요청이 받은 것	종료 중 새 요청	서버 종료	서버 로그
A	-mode shutdown -grace 5s	200 done	connection refused	exit 0	handler: start → signal received: terminated signal received → shutdown: start → handler: end → shutdown: returned <nil> → Serve returned: http: Server closed · ErrServerClosed? true
B	-mode shutdown -grace 100ms	EOF	connection refused	exit 1	handler: start → signal received: terminated signal received → shutdown: start → shutdown: returned context deadline exceeded
C	-mode close	EOF	-	exit 0	handler: start → signal received: terminated signal received → Close: <nil> → Serve returned: http: Server closed · ErrServerClosed? true
D	-mode none	EOF	-	신호로 죽음(terminated)	handler: start
E	-mode shutdown-goroutine	EOF	-	exit 0	handler: start → signal received: terminated signal received → Serve returned: http: Server closed
F	-mode shutdown-stop	EOF	-	신호로 죽음(terminated)	handler: start → signal received: terminated signal received → shutdown: start
G	-mode shutdown	200 done	-	exit 0	handler: start → signal received: terminated signal received → shutdown: start → handler: end → shutdown: returned <nil> → Serve returned: http: Server closed · ErrServerClosed? true
H	-mode shutdown	EOF	-	신호로 죽음(killed)	handler: start
진행 중 요청이 끝까지 간 칸 2 / 8
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`A`(`Shutdown(5s)`, `main` 이 기다림) — `200 done` · 새 요청 `connection refused` · `exit 0`** — 로그 순서 `signal received → shutdown: start → handler: end → shutdown: returned <nil> → Serve returned … ErrServerClosed? true`. 문서 그대로 **리스너를 먼저 닫아** 새 요청은 거절되고, **진행 중 요청은 끝까지** 갔다.
- ★★★ **`E`(`Shutdown` 은 고루틴, `main` 은 `Serve` 반환에서 끝) — `EOF` · `exit 0`** — 로그가 `signal received → Serve returned: http: Server closed` 에서 **끝난다.** `handler: end` 가 없다. 문서 「**immediately** return ErrServerClosed」 — `Serve` 가 곧바로 돌아왔고 `main` 이 `return` 하자 **프로세스가 끝났다**(명세: `main` 이 반환하면 다른 고루틴을 기다리지 않는다). ★★★ **`A` 와 `E` 는 같은 부품을 쓴다 — 다른 것은 「누가 누구를 기다리나」뿐이다.**
- ★★★ **`B`(`Shutdown(100ms)`) — `EOF` · `exit 1` · 로그 `shutdown: returned context deadline exceeded`** — 문서 「If the provided context expires before the shutdown is complete, Shutdown returns the context's error」. ★★ **`Shutdown` 이 핸들러를 죽인 것이 아니다** — 기한이 끝나 **돌아왔을 뿐**이고, 이 서버가 그 에러에 `os.Exit(1)` 해서 프로세스가 끝났다. 새 요청은 여기서도 `connection refused`(리스너는 이미 닫혔다).
- ★★ **`C`(`Close()`) — `EOF`** — 문서 「immediately closes all active net.Listeners and any connections in state StateNew, StateActive, or StateIdle」. `Close: <nil>` 뒤 `Serve` 도 `ErrServerClosed` 로 돌아왔다 — **`ErrServerClosed` 는 `Shutdown` 과 `Close` 를 가리지 않는다.**
- ★★★ **`D`(신호 처리 없음) — `EOF` · `신호로 죽음(terminated)` · 로그는 `handler: start` 하나** — 기본 동작(종료). **`defer` 도 로그도 없이** 사라진다 — ops-patterns 19 의 「예외도 로그도 없이 사라진다」가 이것이다.
- ★★★ **`F`(`stop()` 뒤 두 번째 `SIGTERM`) — `신호로 죽음(terminated)`** 대 **`G`(`stop()` 없이 두 번째 `SIGTERM`) — `200 done` · `exit 0`** — `stop()` 이 **기본 동작을 되돌려** 두 번째 신호가 프로세스를 죽였다. `stop` 을 안 부르면 두 번째 신호도 `ctx` 가 받아 **무시된다**(이미 취소됨). ★ 「두 번째 Ctrl-C 로 강제 종료」를 원하면 `F` 모양이 그것이다 — 원치 않으면 `G` 모양.
- ★★★ **`H`(`SIGKILL`) — `신호로 죽음(killed)` · 로그 `handler: start` 하나** — `NotifyContext` 에 `SIGKILL` 을 넣지도 않았지만 **넣어도 못 잡는다**(문서 「may not be caught」). 쿠버네티스의 유예 시간이 끝나면 오는 것이 이것이다.
- ★★ 「진행 중 요청이 끝까지 간 칸 **2 / 8**」 — `A`·`G`. 둘 다 **`main` 이 `Shutdown` 의 반환을 기다렸고 기한이 충분했다.**
- ★ 새 요청 칸이 `-` 인 것은 **안 물었다**는 뜻이다(`Shutdown` 이 시작된 칸 `A`·`B` 만 물었다). `-` 를 「거절 안 됨」으로 읽지 마라.

비용 — `Shutdown` 은 **가장 긴 진행 중 요청만큼** 종료를 늦춘다. 기한은 **오케스트레이터의 유예 시간보다 짧게** 잡는다(ops-patterns 19).

### (2) ★★ 배선 한 장 — `A` 칸의 `main`

`A` 칸의 서버가 한 일을 순서대로 읽으면 이렇다(격자의 `server.go` 에서 `mode == "shutdown"` 경로).

```text
   ① ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGTERM, os.Interrupt)
      defer stop()
   ② errc := make(chan error, 1)
      go func() { errc <- srv.Serve(ln) }()          ← Serve 를 고루틴으로
   ③ <-ctx.Done()                                     ← 신호가 올 때까지
   ④ sctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
      err := srv.Shutdown(sctx)                       ← ★ main 이 여기서 기다린다
   ⑤ err = <-errc   → errors.Is(err, http.ErrServerClosed) 면 정상
```

- ★★★ **④ 의 `ctx` 를 ①의 `ctx` 로 쓰지 마라** — ①은 **이미 취소됐다**(신호로). 그걸 `Shutdown` 에 주면 **기다림이 0초**가 된다. 새 `context.Background()` 에서 기한을 건다. ★ 이 문서는 그 판을 **따로 돌리지 않았다** — `B` 칸(100ms)이 「기한이 짧으면」의 실측이다.
- ★★ **⑤ 에서 `ErrServerClosed` 를 실패로 다루지 마라** — `Shutdown`·`Close` 뒤에는 **늘** 이것이다(`A`·`C`·`G` 칸 `ErrServerClosed? true`).
- ★ 핸들러가 `r.Context()` 를 보고 있으면 — **`Shutdown` 은 그것을 취소하지 않는다**(문서가 말하지 않는다 · 이 문서는 재지 않았다). 취소 전파는 34번이 정본이다.

### (3) ★★ 셸이 본 종료 상태 — `143` · `0` · `137`

```text
===== 명령: go build -trimpath -o server ./srv || exit 1; for c in "none TERM" "shutdown TERM" "shutdown KILL"; do set -- $c; coproc S { exec ./server -mode $1; }; read -r line <&"${S[0]}"; kill -$2 $S_PID; wait $S_PID; echo "-mode $1 에 SIG$2 → 셸이 본 종료 상태 $?"; done 2>/dev/null =====
-mode none 에 SIGTERM → 셸이 본 종료 상태 143
-mode shutdown 에 SIGTERM → 셸이 본 종료 상태 0
-mode shutdown 에 SIGKILL → 셸이 본 종료 상태 137
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **신호 처리 없는 서버에 `SIGTERM` → `143`** · **`SIGKILL` → `137`** — 셸은 **신호로 죽은 자식**의 상태를 `128 + 신호 번호` 로 보고한다(`SIGTERM` 15 · `SIGKILL` 9). **Go 가 돌려준 종료 코드가 아니다** — Go 프로그램은 코드를 돌려줄 틈도 없이 죽었다. (1)절 구동기는 같은 것을 `신호로 죽음(…)` 으로 적었다(`WaitStatus.Signaled()`).
- ★★ **`NotifyContext` 가 있는 서버에 `SIGTERM` → `0`** — 신호를 **받아 처리하고 정상 반환**했다. 오케스트레이터 로그에서 `143` 대신 `0` 이 보이면 **정리가 돌았다**는 뜻이다.
- ★ `Ctrl-C`(`SIGINT` 2)면 `130` 이 된다 — 이 문서는 `SIGINT` 를 **돌리지 않았다**(같은 규칙에서 나온 숫자다).

## 문법 — 형태와 규칙

### 형태

```text
   ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGTERM, os.Interrupt)
   defer stop()                         ← stop 을 부르면 기본 동작으로 돌아간다

   go func() {
       if err := srv.ListenAndServe(); !errors.Is(err, http.ErrServerClosed) {
           log.Fatal(err)                ← ErrServerClosed 가 아닌 것만 진짜 실패
       }
   }()

   <-ctx.Done()
   stop()                               ← (선택) 두 번째 신호로 강제 종료하게 하려면
   sctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
   defer cancel()
   if err := srv.Shutdown(sctx); err != nil {   ← 기한 초과면 context.DeadlineExceeded
       log.Printf("shutdown: %v", err)
       srv.Close()                               ← 남은 연결을 끊는다
   }
```

- **`Shutdown` 은 `main`(또는 `main` 이 기다리는 곳)에서** 부른다 — `Serve` 가 돌아온 것으로 끝을 삼지 않는다.
- **`NotifyContext` 에 넣는 신호** — 컨테이너는 `SIGTERM`, 터미널은 `os.Interrupt`. `SIGKILL` 은 넣어도 소용없다.
- ★ 위 틀은 **그림**이다 — 이 문서가 돌린 것은 (1)절 `server.go` 이고, 거기서는 `ListenAndServe` 대신 `Serve(ln)` 을 썼다(포트를 `:0` 으로 받으려고). 문서는 둘이 `Shutdown` 에 같게 반응한다고 적는다(`t51doc`).

### 금지 사례 — 누가 잡나

| 쓴 꼴 | 누가 잡나 | 어디서 |
|---|---|---|
| `main` 에서 `ListenAndServe`/`Serve` · `Shutdown` 은 고루틴 | ★★★ **아무도 안 잡는다** — `exit 0` 에 요청은 `EOF` | (1)절 `E` |
| `ErrServerClosed` 를 `log.Fatal` | ★★ **아무도 안 잡는다** — 정상 종료가 실패로 기록된다 | (1)절 `A` 의 `ErrServerClosed? true` |
| 이미 취소된 신호 `ctx` 를 `Shutdown` 에 | ★★ **아무도 안 잡는다** — 기다림이 없어진다(돌려 보지 않았다) | (2)절 |
| 버퍼 없는 채널로 `signal.Notify` | ★★ **`go vet`(`sigchanyzer`)** | [52번 주제](../52-tools-gofmt-vet-build-tags-embed-and-escape-analysis/) (2)절 |

## 어디서 틀리나

### 1. ★★★ 「`Shutdown` 을 불렀으니 진행 중 요청은 마무리된다」

**`main` 이 `Shutdown` 의 반환을 기다릴 때만**이다((1)절 `A` 대 `E`). `Serve` 는 `Shutdown` 이 불리는 **즉시** 돌아온다 — 거기서 `main` 이 끝나면 **`exit 0` 인 채로** 요청이 끊긴다.

### 2. ★★★ 「`Shutdown` 은 기한이 지나면 남은 요청을 끊는다」

**돌아올 뿐**이다(`B` 칸 — `context deadline exceeded`). 끊는 것은 **그 뒤의 `Close()` 나 프로세스 종료**다. 기한 초과를 **에러로 보고**해야 몇 건을 버렸는지 안다(ops-patterns 19 의 「세어서 버린다」).

### 3. ★★ 「`ErrServerClosed` 가 오면 뭔가 잘못됐다」

`Shutdown`·`Close` 뒤에는 **늘** 온다(`A`·`C`·`G`). **정상 종료의 표지**다. 판별은 `errors.Is(err, http.ErrServerClosed)`.

### 4. ★★ 「두 번째 Ctrl-C 를 누르면 강제 종료된다」

**`stop()` 을 불렀을 때만**이다(`F` 대 `G`). `NotifyContext` 가 살아 있으면 두 번째 신호도 이미 취소된 `ctx` 가 **삼킨다.**

### 5. ★★ 「`SIGKILL` 도 `NotifyContext` 에 넣으면 잡힌다」

못 잡는다 — 커널이 곧바로 죽인다(`H` 칸 · 셸 `137` · 문서 「may not be caught」).

### 6. ★ 「종료 코드 `143` 은 Go 가 돌려준 것이다」

**셸의 관례**다((3)절). 신호로 죽은 프로세스는 종료 코드를 **돌려주지 않았다** — 셸이 `128 + 15` 로 **보고**한 것이다.

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| `main` 이 반환하면 다른 고루틴을 안 기다린다 | **명세** | (1)절 `E` |
| `Shutdown` 의 순서(리스너 → 쉬는 연결 → 대기) · `ErrServerClosed` 즉시 | **표준 라이브러리 계약**(1.8) | `t51doc` · (1)절 `A` |
| `NotifyContext` · `stop` 이 기본 동작 복귀 | **표준 라이브러리 계약**(1.16) | `t51doc` · (1)절 `F`·`G` |
| SIGINT·SIGTERM 기본 동작 = 종료 | **표준 라이브러리 계약**(Go 런타임) | `t51doc` · (1)절 `D` |
| `SIGKILL` 을 못 잡는다 | **OS(커널)** — 문서도 적는다 | (1)절 `H` |
| `143`·`137` | ★★ **셸의 관례** | (3)절 |
| 클라이언트가 `EOF` 를 봤다 | ★★ **이 머신·이 판의 관찰** | (1)절 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| HTTP 서버의 `main` | ★★★ **`NotifyContext` → `Shutdown(기한)` 을 `main` 에서 · `Serve` 는 고루틴** | (1)절 `A` |
| 기한 | **오케스트레이터 유예 시간보다 짧게** | 넘으면 `SIGKILL`(`H`) |
| 기한 초과 뒤 | **에러를 보고하고 `Close()`** | (1)절 `B` · 어디서 틀리나 2 |
| 두 번째 신호로 강제 종료를 허용 | `<-ctx.Done()` 뒤 **`stop()`** | (1)절 `F` |
| 강제 종료를 막는다 | `stop` 을 끝까지 미룬다 | (1)절 `G` |
| 즉시 내려야 한다(테스트·치명적 오류) | `Close()` | (1)절 `C` |
| 웹소켓 같은 하이재킹 연결 | ★ `Shutdown` 이 **안 기다린다**(문서) — `RegisterOnShutdown` 으로 따로 알린다 | 이 문서는 돌리지 않았다 |

## 핵심 문장

- ★★★ **`NotifyContext` 는 신호를 `ctx` 취소로 바꾸고, `Shutdown` 은 리스너를 닫고 진행 중 요청을 기다린다** — 끝까지 간 칸 `2 / 8`.
- ★★★ **`Serve`·`ListenAndServe` 는 `Shutdown` 즉시 `ErrServerClosed` 를 돌려준다** — `main` 이 거기서 끝나면 `exit 0` 인 채 요청이 `EOF`(`E` 칸). **`main` 은 `Shutdown` 의 반환을 기다린다.**
- ★★ **`Shutdown` 의 기한이 지나면 돌아올 뿐 끊지 않는다** — 끊는 것은 `Close`·종료다(`B`).
- ★★ **`stop()` 뒤의 두 번째 신호는 기본 동작(종료)** · 안 부르면 삼켜진다(`F`·`G`).
- ★★ **`SIGKILL` 은 못 잡는다** · `143`·`137` 은 셸이 보고한 `128 + 신호`.

## 관련 자료

- [`os/signal`](https://pkg.go.dev/os/signal) · [`net/http.Server`](https://pkg.go.dev/net/http#Server) — 이 툴체인의 `go doc` 으로 떴다.
- [`ops-patterns/19-graceful-shutdown`](../../../../../ops-patterns/19-graceful-shutdown/) — ★ **우아한 종료 패턴의 정본.** 그쪽은 RUNNING→DRAINING→STOPPED · 기한 · 헬스체크까지, 여기는 Go 에서 `NotifyContext`→`Shutdown` 을 **어떻게 잇나**부터.
- [34번 주제](../34-context-cancellation-deadlines-and-values/) — `context` 취소 전파. `NotifyContext` 의 `ctx` 는 그 나무의 뿌리가 된다.
- [46번 주제](../46-net-http-server-servemux-patterns-handler-and-middleware/) — `Handler`·`ServeMux` · 핸들러 panic 은 서버가 recover 한다.
- [47번 주제](../47-net-http-client-reuse-timeouts-and-closing-body/) — 클라이언트 쪽 에러 판별 · `ConnState` 로 연결을 센 창.
- [52번 주제](../52-tools-gofmt-vet-build-tags-embed-and-escape-analysis/) — `vet` 의 `sigchanyzer`(버퍼 없는 신호 채널).

## 용어 풀이

- **`signal.NotifyContext`** — 신호가 오면 취소되는 `ctx` 와 `stop` 함수를 준다(1.16).
- **`stop`** — 신호 가로채기를 풀어 **기본 동작**으로 돌린다. 자원도 푼다.
- **`Server.Shutdown(ctx)`** — 리스너를 닫고, 쉬는 연결을 닫고, 활성 연결이 쉴 때까지 기다린다. `ctx` 가 끝나면 그 에러로 돌아온다.
- **`Server.Close()`** — 리스너와 연결을 **즉시** 닫는다.
- **`ErrServerClosed`** — `Shutdown`·`Close` 뒤 `Serve` 계열이 돌려주는 에러.
- **기본 동작(default behavior)** — 프로그램이 신호를 가로채지 않았을 때 일어나는 일. Go 에서 SIGTERM·SIGINT 는 종료.
- **`128 + N`** — 신호 N 으로 죽은 자식을 셸이 보고하는 종료 상태.
- **`EOF`(클라이언트 쪽)** — 응답을 다 받기 전에 상대가 연결을 닫았다.

## 더 들어가면

- ★ **`Server.RegisterOnShutdown`** — `Shutdown` 때 부를 함수를 건다(하이재킹 연결 알림용). 돌리지 않았다.
- ★ **`BaseContext`** — 모든 요청 `ctx` 의 부모를 정한다. 여기에 신호 `ctx` 를 주면 신호가 **핸들러의 `r.Context()` 까지** 취소한다 — 대신 진행 중 요청이 **취소 신호를 받는다**(마무리와 반대 방향). 돌리지 않았다.
- ★ C 의 시그널 핸들러는 **async-signal-safe 함수만** 부를 수 있다 — Go 는 런타임이 신호를 받아 **채널로** 넘기므로(`signal.Notify` 문서) 사용자 코드가 핸들러 문맥에서 돌지 않는다 — 이 문서는 C 쪽을 돌리지 않았다. C 갈래에는 시그널 주제 폴더가 아직 없다.

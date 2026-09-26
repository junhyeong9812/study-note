# go/syntax/51 — `os/signal`과 정상 종료 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ **모든 문제에서 「이 동작은 명세인가, 표준 라이브러리 문서의 계약인가, OS·셸의 성질인가」를 먼저 적어라.**
> 모든 실험은 `module ex`(`go 1.27`) 이고 `go1.27.1` 에서 `go build -trimpath` 로 빌드했다. 서버는 **실제 자식 프로세스**다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 서버 여덟 번 끄기 (예측)

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
```

<!-- 구동기가 칸마다 ./server 를 띄우고, /slow 요청(2초)이 핸들러에 들어간 것(handler: start 줄)을 본 뒤 신호를 보낸다. A·B 는 shutdown: start 줄을 본 뒤 새 요청을 한 번 더 보낸다. F·G 는 300ms 간격으로 SIGTERM 을 두 번 보낸다. H 는 SIGKILL. -->

- 칸 `A`…`H` 각각에서 느린 요청이 받은 것(`200 done` / `EOF` / …)과 서버가 끝난 모양(`exit N` / 신호로 죽음)은? 「진행 중 요청이 끝까지 간 칸」은 몇 / 8 인가?

### 2. 같은 부품, 다른 결과 (왜)

- 1번의 `A` 와 `E` 는 둘 다 `NotifyContext` 와 `Shutdown` 을 쓴다. 왜 `E` 만 요청이 끊기나? `E` 의 서버 종료가 `exit 0` 인 것은 무엇을 숨기나?

### 3. 종료 중에 온 새 요청 (예측)

- 1번 `A`·`B` 에서 `shutdown: start` 뒤 보낸 새 요청은 무엇을 받나? `Shutdown` 문서의 **어느 단계** 때문인가?

### 4. 기한 100ms (경계)

- 1번 `B` 에서 `Shutdown` 은 무엇을 돌려주나? 그때 **핸들러를 끊은 것은 `Shutdown` 인가**, 다른 무엇인가?

### 5. 두 번째 `SIGTERM` (예측)

- 1번 `F`(`<-ctx.Done()` 뒤 `stop()` 을 부름)와 `G`(부르지 않음)에 `SIGTERM` 을 두 번 보내면 각각 어떻게 끝나나? `NotifyContext` 문서의 어느 문장이 이것을 가르나?

### 6. 셸이 본 숫자 (예측)

<!-- 1번의 server 를 bash 의 coproc 으로 띄우고 첫 줄(addr …)을 읽은 뒤 ① -mode none 에 SIGTERM ② -mode shutdown 에 SIGTERM ③ -mode shutdown 에 SIGKILL 을 보내고, wait 의 $? 를 찍었다. -->

- 세 줄의 종료 상태 숫자는? 그 숫자는 **누가** 만든 것인가?

### 7. `SIGKILL` 을 넣어 두면 (경계)

- `signal.NotifyContext(ctx, syscall.SIGTERM, syscall.SIGKILL)` 이라고 쓰면 1번 `H` 칸의 결과가 바뀌나? 쿠버네티스에서 이것이 왜 **기한 선택**의 문제가 되나?

### 8. `ErrServerClosed` 를 `log.Fatal` 하면 (왜)

- `if err := srv.ListenAndServe(); err != nil { log.Fatal(err) }` 를 고루틴에 두고 `main` 에서 `Shutdown` 을 기다린다. 신호가 오면 무엇이 일어나나? 1번의 로그 칸 어디가 그 근거인가?

### 9. 패턴과 배선 (연결)

- [`ops-patterns/19-graceful-shutdown`](../../../../../ops-patterns/19-graceful-shutdown/)의 RUNNING → DRAINING → STOPPED 세 단계는 1번 `A` 칸의 서버 로그 어느 줄에 대응하나? 그쪽의 「기한 초과면 세어서 보고」는 `B` 칸의 무엇에 대응하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

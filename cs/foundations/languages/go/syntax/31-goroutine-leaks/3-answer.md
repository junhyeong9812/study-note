# go/syntax/31 — ★ 고루틴 누수 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★ **근거로 읽을 칸** — `NumGoroutine` 의 수 · 「돌아왔나 : true / false」 · 누수 프로파일의 수 · **`(leaked)`·`(durable)` 표시** · `파일:줄` · `PASS`/`FAIL` · 종료 코드.
> **근거로 읽지 않을 칸** — `goroutine N` 의 N · `@ 0x…` 주소 · 테스트 시간(머리말의 정규화 칸).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 넷 다 `1 · 11 · false` — 누수 프로파일은 `10 · 10 · 0 · 10` · 에러 0줄

**출력**

```text
===== 소스: t31shapes.go =====
package main

import (
	"fmt"
	"os"
	"runtime"
	"runtime/pprof"
	"time"
)

// ① 받는 쪽이 사라진 송신 — 부른 쪽이 시간 초과로 먼저 떠난다
func sendNoRecv() {
	res := make(chan int)
	go func() {
		time.Sleep(20 * time.Millisecond)
		res <- 42
	}()
	select {
	case <-res:
	case <-time.After(time.Millisecond):
	}
}

// ② 보내는 쪽 없는 수신 — 아무도 안 보내고 안 닫는다
func recvNoSend() {
	ch := make(chan int)
	go func() { <-ch }()
}

// ③ 취소 없는 대기 — 멈추라는 신호를 받을 통로가 없다
func noCancel() {
	go func() {
		t := time.NewTicker(time.Millisecond)
		for range t.C {
		}
	}()
}

// ④ 끝나지 않는 range — 보내는 쪽이 close 를 잊었다
func rangeNoClose() {
	ch := make(chan int)
	go func() {
		for i := range 3 {
			ch <- i
		}
	}()
	go func() {
		for range ch {
		}
	}()
}

func settle(want int) bool {
	for deadline := time.Now().Add(time.Second); time.Now().Before(deadline); {
		if runtime.NumGoroutine() == want {
			return true
		}
		time.Sleep(time.Millisecond)
	}
	return false
}

func main() {
	shapes := map[string]func(){
		"sendNoRecv": sendNoRecv, "recvNoSend": recvNoSend,
		"noCancel": noCancel, "rangeNoClose": rangeNoClose,
	}
	f := shapes[os.Args[1]]
	fmt.Println("시작 NumGoroutine            :", runtime.NumGoroutine())
	for range 10 {
		f()
	}
	time.Sleep(100 * time.Millisecond)
	fmt.Println("10번 부른 뒤 NumGoroutine    :", runtime.NumGoroutine())
	fmt.Println("1초 안에 1 로 돌아왔나       :", settle(1))
	fmt.Println("goroutineleak 프로파일의 수  :", leaked())
}

func leaked() int {
	p := pprof.Lookup("goroutineleak")
	p.WriteTo(new(discard), 0) // 쓰기가 누수 탐지 GC 를 한 번 돌린다
	return p.Count()
}

type discard struct{}

func (discard) Write(b []byte) (int, error) { return len(b), nil }
===== 명령: go build -trimpath -o prog . && for s in sendNoRecv recvNoSend noCancel rangeNoClose; do echo "--- $s"; ./prog $s; done =====
--- sendNoRecv
시작 NumGoroutine            : 1
10번 부른 뒤 NumGoroutine    : 11
1초 안에 1 로 돌아왔나       : false
goroutineleak 프로파일의 수  : 10
--- recvNoSend
시작 NumGoroutine            : 1
10번 부른 뒤 NumGoroutine    : 11
1초 안에 1 로 돌아왔나       : false
goroutineleak 프로파일의 수  : 10
--- noCancel
시작 NumGoroutine            : 1
10번 부른 뒤 NumGoroutine    : 11
1초 안에 1 로 돌아왔나       : false
goroutineleak 프로파일의 수  : 0
--- rangeNoClose
시작 NumGoroutine            : 1
10번 부른 뒤 NumGoroutine    : 11
1초 안에 1 로 돌아왔나       : false
goroutineleak 프로파일의 수  : 10
(exit 0)
```

**왜 그런가**

- ★★★ **네 모양 모두 1 → 11, 1초 뒤에도 안 줄었다** — 10번 부른 만큼 **그대로 남았다.** `exit 0`, **에러·경고·패닉은 0줄.** 누수는 **조용하다.**
- ★★★ **`noCancel`(③ 티커 루프)만 누수 프로파일이 0** — 그 고루틴은 **막혀 있지 않다.** 1ms 마다 타이머가 깨워 준다. 누수 프로파일은 「**닿을 수 없는 동기화 수단에 막힌**」 것만 센다.
  ① ② ④ 는 **로컬 채널**이 함수 반환과 함께 **아무도 모르는 채널**이 됐으니 정확히 **10** 이다.

### 2. `3` 과 `5` · `goroutine` 프로파일에만 · 「확실히 샌 것」 대 「있는 것 전부」

**출력**

```text
===== 소스: t31prof.go =====
package main

import (
	"os"
	"runtime/pprof"
	"time"
)

func sendNoRecv() {
	res := make(chan int)
	go func() { res <- 42 }()
}

func poller() {
	go func() {
		t := time.NewTicker(time.Millisecond)
		for range t.C {
		}
	}()
}

func main() {
	for range 3 {
		sendNoRecv()
	}
	poller()
	time.Sleep(50 * time.Millisecond)
	os.Stdout.WriteString("===== goroutineleak (debug=1)\n")
	pprof.Lookup("goroutineleak").WriteTo(os.Stdout, 1)
	os.Stdout.WriteString("===== goroutine (debug=1)\n")
	pprof.Lookup("goroutine").WriteTo(os.Stdout, 1)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
===== goroutineleak (debug=1)
goroutineleak profile: total 3
3 @ 0x47d84a 0x41421c 0x413e17 0x4dec3e 0x4836a1
#	0x4dec3d	main.sendNoRecv.func1+0x1d	ex/t31prof.go:11

===== goroutine (debug=1)
goroutine profile: total 5
3 @ 0x47d84a 0x41421c 0x413e17 0x4dec3e 0x4836a1
#	0x4dec3d	main.sendNoRecv.func1+0x1d	ex/t31prof.go:11

1 @ 0x440e31 0x47cbbd 0x4ccaf1 0x4cc7c5 0x4c9729 0x4debf0 0x44aa47 0x4836a1
#	0x4ccaf0	runtime/pprof.writeRuntimeProfile+0xb0	runtime/pprof/pprof.go:848
#	0x4cc7c4	runtime/pprof.writeGoroutine+0x44	runtime/pprof/pprof.go:781
#	0x4c9728	runtime/pprof.(*Profile).WriteTo+0x148	runtime/pprof/pprof.go:405
#	0x4debef	main.main+0xef				ex/t31prof.go:31
#	0x44aa46	runtime.main+0x426			runtime/proc.go:302

1 @ 0x47d84a 0x41514e 0x414c92 0x4decaf 0x4836a1
#	0x4decae	main.poller.func1+0x4e	ex/t31prof.go:17
(exit 0)
```

**왜 그런가**

- ★★★ 누수 프로파일은 **3**(① 셋, `ex/t31prof.go:11`), 고루틴 프로파일은 **5**(main · 프로파일러 · ① 셋 · ③ 하나).
- ★★ **`main.poller.func1`(③)은 `goroutine` 프로파일에만** 있다.
- ★★ **누수 프로파일 = 「확실히 샌 것」의 목록**(판정이 붙는다), **고루틴 프로파일 = 「지금 있는 것 전부」**(사람이 골라야 한다). 둘을 **같이** 본다.

### 3. `[chan send (leaked)]` 대 `[chan send]` · 채널에 닿을 수 있나 · 안 치워진다

**출력**

```text
===== 소스: t31prof2.go =====
package main

import (
	"os"
	"runtime/pprof"
	"time"
)

func sendNoRecv() {
	res := make(chan int)
	go func() { res <- 42 }()
}

var kept = make(chan int) // 전역 — 누가 언젠가 받을 수도 있다

func sendKept() {
	go func() { kept <- 42 }()
}

func main() {
	sendNoRecv()
	sendKept()
	time.Sleep(50 * time.Millisecond)
	pprof.Lookup("goroutineleak").WriteTo(os.Stdout, 2)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
goroutine 1 [running]:
runtime/pprof.writeGoroutineStacks({0x5dff90, 0x2777d68d6030})
	runtime/pprof/pprof.go:816 +0x69
runtime/pprof.writeGoroutineLeak({0x5dff90, 0x2777d68d6030}, 0x2)
	runtime/pprof/pprof.go:803 +0xa8
runtime/pprof.(*Profile).WriteTo(0x4e04a7?, {0x5dff90?, 0x2777d68d6030?}, 0x2777d68d81e0?)
	runtime/pprof/pprof.go:405 +0x149
main.main()
	ex/t31prof2.go:24 +0x4e

goroutine 7 [chan send (leaked)]:
main.sendNoRecv.func1()
	ex/t31prof2.go:11 +0x1e
created by main.sendNoRecv in goroutine 1
	ex/t31prof2.go:11 +0x67

goroutine 8 [chan send]:
main.sendKept.func1()
	ex/t31prof2.go:17 +0x25
created by main.sendKept in goroutine 1
	ex/t31prof2.go:17 +0x1a
(exit 0)
```

```text
===== 명령: sed -n "108,110p;784,785p" "$(go env GOROOT)/src/runtime/pprof/pprof.go"; sed -n "1274,1277p" "$(go env GOROOT)/src/runtime/mgc.go"; echo "godebug.md 에서 leak 이 나오는 줄 수: $(grep -ci leak "$(go env GOROOT)/doc/godebug.md")" =====
//	goroutine      - stack traces of all current goroutines
//	goroutineleak  - stack traces of all leaked goroutines
//	allocs         - a sampling of all past memory allocations
// writeGoroutineLeak first invokes a GC cycle that performs goroutine leak detection.
// It then writes the goroutine profile, filtering for leaked goroutines.
// findGoroutineLeaks scans the remaining stackRoots and marks any which are
// blocked over exclusively unreachable concurrency primitives as leaked (deadlocked).
// Returns true if the goroutine leak check was performed (or unnecessary).
// Returns false if the GC cycle has not yet computed all maybe-runnable goroutines.
godebug.md 에서 leak 이 나오는 줄 수: 0
(exit 0)
```

**왜 그런가**

- ★★★ **`sendNoRecv` 쪽은 `[chan send (leaked)]`, `sendKept` 쪽은 그냥 `[chan send]`.** 둘 다 똑같이 보내다 막혔다.
- ★★★ 가르는 것은 **채널의 도달성**이다 — `kept` 는 **전역 변수**라 「언젠가 누가 받을 수도 있다」. `findGoroutineLeaks` 는 「**blocked over exclusively unreachable concurrency primitives**」 만 판정한다.
  그래서 **전역·구조체 필드처럼 살아 있는 곳에 붙은 채널의 누수**는 이 프로파일이 **못 본다.**
- ★★ **안 치워진다** — `(leaked)` 로 **표시만** 한다. (1)번의 `NumGoroutine` 이 11 로 남은 것이 그 증거다.

### 4. `1·true` · `11·false` · `11·true` · `11·true` · `1·true` — `buf1Twice`

**출력**

```text
===== 소스: t31fix.go =====
package main

import (
	"context"
	"fmt"
	"os"
	"runtime"
	"time"
)

// ① 처방 — 결과 채널에 버퍼 1: 받는 쪽이 떠나도 한 번은 보낼 자리가 있다
func buf1() {
	res := make(chan int, 1)
	go func() {
		time.Sleep(20 * time.Millisecond)
		res <- 42
	}()
	select {
	case <-res:
	case <-time.After(time.Millisecond):
	}
}

// ①' 같은 처방인데 고루틴이 두 번 보낸다
func buf1Twice() {
	res := make(chan int, 1)
	go func() {
		time.Sleep(20 * time.Millisecond)
		res <- 1
		res <- 2
	}()
	select {
	case <-res:
	case <-time.After(time.Millisecond):
	}
}

// ②·③ 처방 — context 로 끝낼 통로를 준다
func ctxWait(ctx context.Context) {
	ch := make(chan int)
	go func() {
		select {
		case <-ch:
		case <-ctx.Done():
		}
	}()
}

func ctxTicker(ctx context.Context) {
	go func() {
		t := time.NewTicker(time.Millisecond)
		defer t.Stop()
		for {
			select {
			case <-t.C:
			case <-ctx.Done():
				return
			}
		}
	}()
}

// ④ 처방 — 보내는 쪽이 끝나면 닫는다
func closeRange() {
	ch := make(chan int)
	go func() {
		defer close(ch)
		for i := range 3 {
			ch <- i
		}
	}()
	go func() {
		for range ch {
		}
	}()
}

func settle(want int) bool {
	for deadline := time.Now().Add(time.Second); time.Now().Before(deadline); {
		if runtime.NumGoroutine() == want {
			return true
		}
		time.Sleep(time.Millisecond)
	}
	return false
}

func main() {
	ctx, cancel := context.WithCancel(context.Background())
	fixes := map[string]func(){
		"buf1": buf1, "buf1Twice": buf1Twice,
		"ctxWait":    func() { ctxWait(ctx) },
		"ctxTicker":  func() { ctxTicker(ctx) },
		"closeRange": closeRange,
	}
	for range 10 {
		fixes[os.Args[1]]()
	}
	time.Sleep(100 * time.Millisecond)
	fmt.Printf("[%s] 100ms 뒤 NumGoroutine: %d", os.Args[1], runtime.NumGoroutine())
	cancel()
	fmt.Printf(" · cancel 뒤 1초 안에 1 로 돌아왔나: %v\n", settle(1))
}
===== 명령: go build -trimpath -o prog . && for s in buf1 buf1Twice ctxWait ctxTicker closeRange; do ./prog $s; done =====
[buf1] 100ms 뒤 NumGoroutine: 1 · cancel 뒤 1초 안에 1 로 돌아왔나: true
[buf1Twice] 100ms 뒤 NumGoroutine: 11 · cancel 뒤 1초 안에 1 로 돌아왔나: false
[ctxWait] 100ms 뒤 NumGoroutine: 11 · cancel 뒤 1초 안에 1 로 돌아왔나: true
[ctxTicker] 100ms 뒤 NumGoroutine: 11 · cancel 뒤 1초 안에 1 로 돌아왔나: true
[closeRange] 100ms 뒤 NumGoroutine: 1 · cancel 뒤 1초 안에 1 로 돌아왔나: true
(exit 0)
```

**왜 그런가**

- ★★★ **`buf1`·`closeRange` 는 100ms 뒤 이미 1** — 일꾼이 보낼 자리가 있고, 소비자의 `range` 가 끝났다.
- ★★ **`ctxWait`·`ctxTicker` 는 100ms 뒤 11**(아직 정상적으로 기다리는 중), **`cancel()` 뒤 1초 안에 1** — `<-ctx.Done()` 가지가 **끝낼 통로**다.
- ★★★ **`buf1Twice` 만 안 듣는다 — 11, `false`.** 버퍼 1 은 **정확히 한 번 보낼 때만** 맞다. 둘째 송신이 막혔다.

### 5. `FAIL`(`시작 2 → 끝 4`)·`PASS` · 테스트는 `testing` 의 고루틴에서 돈다 · 사라지는 틈 · 병렬

**출력**

```text
===== 소스: t31leak_test.go =====
package ex

import (
	"runtime"
	"testing"
	"time"
)

// noLeak 은 테스트가 끝날 때 NumGoroutine 이 시작 값으로 돌아왔는지 본다.
func noLeak(t *testing.T) {
	before := runtime.NumGoroutine()
	t.Cleanup(func() {
		for deadline := time.Now().Add(500 * time.Millisecond); time.Now().Before(deadline); {
			if runtime.NumGoroutine() <= before {
				return
			}
			time.Sleep(time.Millisecond)
		}
		t.Errorf("고루틴 수: 시작 %d → 끝 %d", before, runtime.NumGoroutine())
	})
}

func first(results []int, bufSize int) int {
	ch := make(chan int, bufSize)
	for _, r := range results {
		go func() { ch <- r }()
	}
	return <-ch // 첫 결과만 쓴다
}

func TestFirstUnbuffered(t *testing.T) {
	noLeak(t)
	if got := first([]int{1, 2, 3}, 0); got == 0 {
		t.Fatal("결과 없음")
	}
}

func TestFirstBuffered(t *testing.T) {
	noLeak(t)
	if got := first([]int{1, 2, 3}, 3); got == 0 {
		t.Fatal("결과 없음")
	}
}
===== 명령: go test -trimpath -count=1 -v . =====
=== RUN   TestFirstUnbuffered
    t31leak_test.go:19: 고루틴 수: 시작 2 → 끝 4
--- FAIL: TestFirstUnbuffered (0.50s)
=== RUN   TestFirstBuffered
--- PASS: TestFirstBuffered (0.00s)
FAIL
FAIL	ex	0.506s
FAIL
(exit 1)
```

**왜 그런가**

- ★★★ **`TestFirstUnbuffered` 는 `FAIL`, 「고루틴 수: 시작 2 → 끝 4」** — 결과 셋 중 첫 것만 받으니 **둘이 남았다.** `TestFirstBuffered` 는 **`PASS`**(버퍼 3 = 보내는 횟수).
- ★★ 시작이 **2** 인 것은 테스트 함수가 **`testing` 이 띄운 고루틴**에서 돌기 때문이다 — 그래서 「1 로」가 아니라 **「시작 값으로」** 돌아왔나를 본다.
- ★★ **500ms 기다림** — 고루틴이 끝나도 **사라지기까지 틈**이 있다([28번 주제](../28-goroutines-go-statement-cost-and-termination/) (2)절). 안 기다리면 깨끗한 코드도 가끔 실패한다.
- ★ 거짓 결과의 조건 — **병렬 테스트**(`t.Parallel`)면 다른 테스트의 고루틴이 섞인다. 이 문서는 **안 던졌다.**

### 6. 「blocked goroutines remain」 · 둘 · `(durable), synctest bubble 1` · 패닉이 바이너리를 끝내서 · `1h0m0s` 대 `(0.00s)`

**출력**

```text
===== 소스: t31synctest_test.go =====
package ex

import (
	"testing"
	"testing/synctest"
	"time"
)

func firstOf(bufSize int) int {
	ch := make(chan int, bufSize)
	for i := 1; i <= 3; i++ {
		go func() { ch <- i }()
	}
	return <-ch
}

func TestBubbleUnbuffered(t *testing.T) {
	synctest.Test(t, func(t *testing.T) {
		firstOf(0)
	})
}

func TestBubbleBuffered(t *testing.T) {
	synctest.Test(t, func(t *testing.T) {
		firstOf(3)
	})
}

func TestBubbleClock(t *testing.T) {
	synctest.Test(t, func(t *testing.T) {
		start := time.Now()
		select {
		case <-make(chan int):
		case <-time.After(time.Hour):
		}
		t.Log("한 시간짜리 time.After 뒤 가짜 시계가 간 양:", time.Since(start))
	})
}
===== 명령: go test -trimpath -count=1 -v -run TestBubbleUnbuffered . =====
=== RUN   TestBubbleUnbuffered
--- FAIL: TestBubbleUnbuffered (0.00s)
panic: deadlock: main bubble goroutine has exited but blocked goroutines remain [recovered, repanicked]

goroutine 7 [running]:
testing.tRunner.func1.2({0x6c18b8, 0x2fd35b2d8198})
	testing/testing.go:2123 +0x232
testing.tRunner.func1()
	testing/testing.go:2126 +0x329
panic({0x6c18b8?, 0x2fd35b2d8198?})
	runtime/panic.go:859 +0x125
internal/synctest.Run(0x2fd35b37e160)
	runtime/synctest.go:247 +0x2dd
testing/synctest.Test(0x2fd35b3d2248, 0x6d4848)
	testing/synctest/synctest.go:291 +0x99
ex.TestBubbleUnbuffered(0x2fd35b3d2248?)
	ex/t31synctest_test.go:18 +0x1a
testing.tRunner(0x2fd35b3d2248, 0x6d4790)
	testing/testing.go:2193 +0xea
created by testing.(*T).Run in goroutine 1
	testing/testing.go:2258 +0x4d4

goroutine 10 [chan send (durable), synctest bubble 1]:
ex.firstOf.func1()
	ex/t31synctest_test.go:12 +0x1b
created by ex.firstOf in goroutine 9
	ex/t31synctest_test.go:12 +0x48

goroutine 11 [chan send (durable), synctest bubble 1]:
ex.firstOf.func1()
	ex/t31synctest_test.go:12 +0x1b
created by ex.firstOf in goroutine 9
	ex/t31synctest_test.go:12 +0x48
FAIL	ex	0.006s
FAIL
(exit 1)
```

```text
===== 소스: t31synctest_test.go =====
package ex

import (
	"testing"
	"testing/synctest"
	"time"
)

func firstOf(bufSize int) int {
	ch := make(chan int, bufSize)
	for i := 1; i <= 3; i++ {
		go func() { ch <- i }()
	}
	return <-ch
}

func TestBubbleUnbuffered(t *testing.T) {
	synctest.Test(t, func(t *testing.T) {
		firstOf(0)
	})
}

func TestBubbleBuffered(t *testing.T) {
	synctest.Test(t, func(t *testing.T) {
		firstOf(3)
	})
}

func TestBubbleClock(t *testing.T) {
	synctest.Test(t, func(t *testing.T) {
		start := time.Now()
		select {
		case <-make(chan int):
		case <-time.After(time.Hour):
		}
		t.Log("한 시간짜리 time.After 뒤 가짜 시계가 간 양:", time.Since(start))
	})
}
===== 명령: go test -trimpath -count=1 -v -run "TestBubbleBuffered|TestBubbleClock" . =====
=== RUN   TestBubbleBuffered
--- PASS: TestBubbleBuffered (0.00s)
=== RUN   TestBubbleClock
    t31synctest_test.go:36: 한 시간짜리 time.After 뒤 가짜 시계가 간 양: 1h0m0s
--- PASS: TestBubbleClock (0.00s)
PASS
ok  	ex	0.004s
(exit 0)
```

```text
===== 명령: go doc testing/synctest | sed -n "42,44p;63,70p" =====
A goroutine in a bubble is "durably blocked" when it is blocked and can only
be unblocked by another goroutine in the same bubble. A goroutine which can be
unblocked by an event from outside its bubble is not durably blocked.
When every goroutine in a bubble is durably blocked:

  - Wait returns, if it has been called.
  - Otherwise, time advances to the next time that will unblock at least one
    goroutine, if there is such a time and the root goroutine of the bubble has
    not exited.
  - Otherwise, there is a deadlock and Test panics.
(exit 0)
```

**왜 그런가**

- ★★★ **`panic: deadlock: main bubble goroutine has exited but blocked goroutines remain [recovered, repanicked]`** — 버블의 주 함수가 끝났는데 **막힌 고루틴 둘**이 남았다. 상태 줄 **`[chan send (durable), synctest bubble 1]`**.
  문서 — 전부가 durably blocked 이고 시계를 건너뛸 곳도 없으면 「**there is a deadlock and Test panics**」.
- ★★ **패닉이 테스트 바이너리 전체를 끝낸다**(`[recovered, repanicked]` — `testing` 이 받아 다시 던졌다). 한 번에 돌리면 **나머지 테스트가 안 돈다.** 그래서 나눴다.
- ★★★ **가짜 시계는 `1h0m0s` 를 갔고, 테스트는 `(0.00s)`** — 전부 막히면 **시계가 다음 타이머까지 건너뛴다.**

### 7. `1 → 1`, 고루틴 누수가 아니다 · 치워진다(1.23) · `fatal error: removed GODEBUG` — 못 돌린다

```text
===== 소스: t31after.go =====
package main

import (
	"fmt"
	"runtime"
	"time"
)

func main() {
	ready := make(chan int, 1)
	var ms runtime.MemStats
	runtime.GC()
	runtime.ReadMemStats(&ms)
	before := ms.HeapInuse
	g0 := runtime.NumGoroutine()
	for i := range 200000 {
		ready <- i
		select {
		case <-ready:
		case <-time.After(time.Hour): // 매 회차 한 시간짜리 타이머를 만들고 버린다
		}
	}
	g1 := runtime.NumGoroutine()
	runtime.GC()
	runtime.ReadMemStats(&ms)
	grow := int64(ms.HeapInuse) - int64(before)
	fmt.Println("루프 전후 NumGoroutine         :", g0, "→", g1)
	fmt.Println("GC 뒤 HeapInuse 증분이 1MiB 미만인가:", grow < 1<<20)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
루프 전후 NumGoroutine         : 1 → 1
GC 뒤 HeapInuse 증분이 1MiB 미만인가: true
(exit 0)
```

```text
===== 소스: t31after.go =====
package main

import (
	"fmt"
	"runtime"
	"time"
)

func main() {
	ready := make(chan int, 1)
	var ms runtime.MemStats
	runtime.GC()
	runtime.ReadMemStats(&ms)
	before := ms.HeapInuse
	g0 := runtime.NumGoroutine()
	for i := range 200000 {
		ready <- i
		select {
		case <-ready:
		case <-time.After(time.Hour): // 매 회차 한 시간짜리 타이머를 만들고 버린다
		}
	}
	g1 := runtime.NumGoroutine()
	runtime.GC()
	runtime.ReadMemStats(&ms)
	grow := int64(ms.HeapInuse) - int64(before)
	fmt.Println("루프 전후 NumGoroutine         :", g0, "→", g1)
	fmt.Println("GC 뒤 HeapInuse 증분이 1MiB 미만인가:", grow < 1<<20)
}
===== 명령: go build -trimpath -o prog . && GODEBUG=asynctimerchan=1 ./prog =====
fatal error: removed GODEBUG "asynctimerchan" set to old value "1" in environment (https://go.dev/doc/godebug#go-127)

goroutine 1 [running, locked to thread]:
runtime.fatal({0x109f0a5e0150, 0x68})
	runtime/panic.go:1267 +0x74
runtime.main()
	runtime/proc.go:224 +0x2aa
runtime.goexit({})
	runtime/asm_amd64.s:1264 +0x1
(exit 2)
```

```text
===== 소스: go.mod =====
module ex

go 1.22
===== 소스: t31after.go =====
package main

import (
	"fmt"
	"runtime"
	"time"
)

func main() {
	ready := make(chan int, 1)
	var ms runtime.MemStats
	runtime.GC()
	runtime.ReadMemStats(&ms)
	before := ms.HeapInuse
	g0 := runtime.NumGoroutine()
	for i := range 200000 {
		ready <- i
		select {
		case <-ready:
		case <-time.After(time.Hour): // 매 회차 한 시간짜리 타이머를 만들고 버린다
		}
	}
	g1 := runtime.NumGoroutine()
	runtime.GC()
	runtime.ReadMemStats(&ms)
	grow := int64(ms.HeapInuse) - int64(before)
	fmt.Println("루프 전후 NumGoroutine         :", g0, "→", g1)
	fmt.Println("GC 뒤 HeapInuse 증분이 1MiB 미만인가:", grow < 1<<20)
}
===== 명령: echo "asynctimerchan 이 기본 GODEBUG 에 있나: $(go list -f "{{.DefaultGODEBUG}}" . | grep -q asynctimerchan && echo 예 || echo 아니오)" =====
asynctimerchan 이 기본 GODEBUG 에 있나: 아니오
(exit 0)
```

- ★★★ **`NumGoroutine 1 → 1`** — `time.After` 는 **고루틴을 만들지 않는다.** 루프 안의 `time.After` 는 **고루틴 누수가 아니다**(1.23 전에도 **메모리** 문제였다).
- ★★ **`GC 뒤 HeapInuse 증분이 1MiB 미만인가: true`** — 「**As of Go 1.23, the garbage collector can recover unreferenced, unstopped timers.**」
- ★★★ **`GODEBUG=asynctimerchan=1` → `fatal error: removed GODEBUG "asynctimerchan" set to old value "1"`, exit 2.** `go 1.22` 모듈의 기본 GODEBUG 에도 **안 들어간다.**
  그래서 **1.22 쪽 칸은 이 툴체인으로 「못 잰 것」**(제3의 상태)이다.

### 8. 한 번은 넣을 자리가 있어서 · 「정확히 한 번」+「결과를 버려도 됨」 · `context`

- ★★★ 받는 쪽이 떠나도 일꾼이 **버퍼에 넣고 끝날 수 있다.** 막힐 자리가 없어진다.
- ★★★ 조건 — **보내는 횟수가 정확히 1** 이고, **아무도 안 받아도 되는 결과**일 것. (4)번 `buf1Twice` 가 첫 조건을 어긴 반례다.
- ★★ 횟수를 모르면(스트림·재시도) **`context` 취소**로 일꾼이 스스로 멈추게 한다.

### 9. 어디서 · ③ 과 전역 채널 · 침묵 · 없다 — 못 잰 것

```text
===== 소스: t31shapes.go =====
package main

import (
	"fmt"
	"os"
	"runtime"
	"runtime/pprof"
	"time"
)

// ① 받는 쪽이 사라진 송신 — 부른 쪽이 시간 초과로 먼저 떠난다
func sendNoRecv() {
	res := make(chan int)
	go func() {
		time.Sleep(20 * time.Millisecond)
		res <- 42
	}()
	select {
	case <-res:
	case <-time.After(time.Millisecond):
	}
}

// ② 보내는 쪽 없는 수신 — 아무도 안 보내고 안 닫는다
func recvNoSend() {
	ch := make(chan int)
	go func() { <-ch }()
}

// ③ 취소 없는 대기 — 멈추라는 신호를 받을 통로가 없다
func noCancel() {
	go func() {
		t := time.NewTicker(time.Millisecond)
		for range t.C {
		}
	}()
}

// ④ 끝나지 않는 range — 보내는 쪽이 close 를 잊었다
func rangeNoClose() {
	ch := make(chan int)
	go func() {
		for i := range 3 {
			ch <- i
		}
	}()
	go func() {
		for range ch {
		}
	}()
}

func settle(want int) bool {
	for deadline := time.Now().Add(time.Second); time.Now().Before(deadline); {
		if runtime.NumGoroutine() == want {
			return true
		}
		time.Sleep(time.Millisecond)
	}
	return false
}

func main() {
	shapes := map[string]func(){
		"sendNoRecv": sendNoRecv, "recvNoSend": recvNoSend,
		"noCancel": noCancel, "rangeNoClose": rangeNoClose,
	}
	f := shapes[os.Args[1]]
	fmt.Println("시작 NumGoroutine            :", runtime.NumGoroutine())
	for range 10 {
		f()
	}
	time.Sleep(100 * time.Millisecond)
	fmt.Println("10번 부른 뒤 NumGoroutine    :", runtime.NumGoroutine())
	fmt.Println("1초 안에 1 로 돌아왔나       :", settle(1))
	fmt.Println("goroutineleak 프로파일의 수  :", leaked())
}

func leaked() int {
	p := pprof.Lookup("goroutineleak")
	p.WriteTo(new(discard), 0) // 쓰기가 누수 탐지 GC 를 한 번 돌린다
	return p.Count()
}

type discard struct{}

func (discard) Write(b []byte) (int, error) { return len(b), nil }
===== 명령: go vet . && echo "vet exit=$?" =====
vet exit=0
(exit 0)
```

```text
===== 명령: cd "$(mktemp -d)" && printf "module probe\n\ngo 1.27\n" > go.mod && echo "모듈 캐시에 go.uber.org 가 있나: $(ls "$(go env GOMODCACHE)/go.uber.org" >/dev/null 2>&1 && echo 예 || echo 아니오)"; GOPROXY=off go get go.uber.org/goleak; echo "go get exit=$?" =====
모듈 캐시에 go.uber.org 가 있나: 아니오
go: go.uber.org/goleak: module lookup disabled by GOPROXY=off
go get exit=1
(exit 0)
```

- ★★ **`NumGoroutine`** 은 **몇 개**인지만 — **어디서** 멈췄나는 못 말한다. 프로파일이 그 자리를 채운다.
- ★★★ 누수 프로파일은 **③ 티커 루프**(막혀 있지 않다)와 **전역·필드에 붙은 채널에 막힌 것**(닿을 수 있다)을 못 본다.
- ★★★ **`go vet` 은 `vet exit=0`, 한 줄도 없다** — 「누가 이 채널에 보내나」는 **함수 하나를 넘는 질문**이다.
- ★★ **`goleak` 은 이 환경에 없다**(모듈 캐시 「아니오」 · `module lookup disabled by GOPROXY=off`). **「못 잰 것」** 으로 적고, 표준 창 둘(전후 비교·`synctest`)로 같은 질문을 물었다.

### 10. 「막힘은 영원」+「고루틴을 없애는 문법이 없다」 · 구현(이 판 runtime) · 없다

- ★★★ [29번 주제](../29-channels-buffering-direction-close-range-and-nil/)의 **차단 규칙**(받을 쪽이 없으면 영원히 막힌다)과, **고루틴을 밖에서 끝내는 문법이 없다**는 것 — 둘이 합쳐 「아무도 안 치운다」가 된다.
- ★★ **`goroutineleak` 프로파일은 이 판 `runtime`·`pprof` 의 구현**이다. 명세의 보장이 아니다. 판이 바뀌면 다시 확인할 칸이다.
- ★ **명세에는 「누수」라는 낱말이 없다** — 누수는 **프로그램의 성질**이지 언어의 사건이 아니다.

### 11. ③ — 29편 (8)절 `sleeper` · ① · `failure-modes`

- ★★★ **③ 티커 루프**가 가린다 — 29편 (8)절에서 **곁에 `time.Sleep` 하는 고루틴 하나**가 교착 탐지를 막아 **탐지 못 한 칸 1 / 3** 이 됐다. **채널에 막혀 새어 있는 ①②④ 는 못 가린다.**
- ★★ 30편 (4)절의 `NumGoroutine: 2` 는 **① 받는 쪽이 사라진 송신**이다.
- ★ 실패 모드 분류 일반은 [`../../../../../ops-patterns/failure-modes/`](../../../../../ops-patterns/failure-modes/).

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 로 **★고칠 것 0** |
| ★★★ 네 모양 (`t31shapes`) | 모양마다 10번, `settle(1)` + 누수 프로파일 | 4 | 넷 다 `11 · false` · 프로파일 `10 · 10 · 0 · 10` |
| ★★★ 처방 (`t31fix`) | 다섯 처방, `cancel` 뒤 `settle(1)` | 5 | `buf1Twice` 만 `false` |
| ★★ 프로파일 (`t31prof`·`t31prof2`) | `debug=1` 두 종 · `debug=2` 누수 | 2 | `3` · `5` · `(leaked)` 한 줄 |
| ★★★ 테스트 (`t31test`) | `go test -count=1 -v` | 1 | `FAIL 시작 2 → 끝 4` · `PASS` |
| ★★★ `synctest` (`t31synctest`·`t31synctest2`) | 나눠서 두 번 | 2 | `blocked goroutines remain` · `1h0m0s` |
| ★★ `time.After` (`t31after`·`t31async`·`t31defgodebug`) | 20만 회 · `GODEBUG` · `go 1.22` 모듈 | 3 | `1 → 1` · `true` · `fatal error` · 「아니오」 |
| ★ `goleak` 판별 · `vet` | `GOPROXY=off go get` · `go vet` | 2 | 없다 · `vet exit=0` |

**구현·환경에 달린 항목**

| 항목 | 무엇에 달렸나 |
|---|---|
| `goroutineleak` 프로파일의 존재·판정 규칙 | **이 판 runtime·pprof** — 몇 판부터인지는 **확인 못 했다** |
| `synctest` 의 `Sleep` | **1.27** |
| `asynctimerchan` 제거 | **1.27** — 1.22 쪽 칸은 **못 잰 것** |
| 고루틴 id · 주소 · 테스트 시간 | **흔들린다** — 정규화 규칙 `([Gg]oroutine) \d+` + 기본 넷 |
| `goleak` | **이 환경에 없다** |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다.

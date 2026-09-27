# go/syntax/31 — ★ 고루틴 누수 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ **모든 고루틴에 대해 먼저 「이것은 무엇이 오면 끝나나」를 한 줄로 적어라.** 적을 수 없으면 그것이 누수다.
> ★★ **창마다 「무엇을 못 보나」를 같이 적어라** — `NumGoroutine` · 누수 프로파일 · 테스트 · `vet` 은 보는 것이 다르다.
> 소스는 전부 `go build -trimpath -o prog .` 또는 `go test -trimpath -count=1 -v .` 로 돌렸다. 모듈 이름은 `ex` 다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 네 모양 × 세 창 (예측)

```go
// t31shapes.go
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
```

<!-- 셸이 sendNoRecv · recvNoSend · noCancel · rangeNoClose 를 차례로 한 판씩 돌린다. -->

- 네 판 각각의 네 줄(시작 · 10번 부른 뒤 · 1초 안에 돌아왔나 · 누수 프로파일의 수)을 적어라.
- 누수 프로파일의 수가 **다른 셋과 다른** 모양이 하나 있다면 어느 것이고, 왜인가?
- 이 네 판에서 에러·경고·패닉은 몇 줄 나오나?

### 2. 두 프로파일을 나란히 (예측)

```go
// t31prof.go
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
```

- `goroutineleak profile: total ?` 과 `goroutine profile: total ?` 의 두 수는?
- `main.poller.func1` 은 두 프로파일 중 어디에 나오나?
- 두 프로파일은 각각 **무엇을 묻는 데** 쓰나?

### 3. 같은 송신, 다른 판정 (예측)

```go
// t31prof2.go
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
```

- `sendNoRecv` 의 고루틴과 `sendKept` 의 고루틴은 상태 줄(`goroutine N [...]:`)이 각각 어떻게 찍히나?
- 둘을 가르는 것은 무엇인가? 그렇다면 이 프로파일이 **못 보는** 누수는?
- 판정을 받은 고루틴은 치워지나?

### 4. 처방 다섯 (예측)

```go
// t31fix.go
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
```

<!-- 셸이 buf1 · buf1Twice · ctxWait · ctxTicker · closeRange 를 차례로 한 판씩 돌린다. -->

- 다섯 줄 각각의 「100ms 뒤 NumGoroutine」 과 「cancel 뒤 1초 안에 1 로 돌아왔나」 를 적어라.
- 처방이 **안 듣는** 줄은 어느 것이고, 그것이 말해 주는 버퍼 1 의 조건은?

### 5. 테스트 전후 비교 (예측)

```go
// t31leak_test.go
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
```

<!-- go test -trimpath -count=1 -v . -->

- 두 테스트 각각 `PASS` 인가 `FAIL` 인가? 실패 메시지의 두 수는?
- 시작 값은 왜 1 이 아닌가?
- `Cleanup` 이 500ms 를 기다리는 이유는? 이 방법이 거짓 결과를 낼 수 있는 조건 하나는?

### 6. 버블 안의 누수 (예측)

```go
// t31synctest_test.go
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
```

<!-- 둘로 나눠 돌렸다: -run TestBubbleUnbuffered 한 번, -run "TestBubbleBuffered|TestBubbleClock" 한 번. -->

- `TestBubbleUnbuffered` 의 패닉 첫 줄은? 남은 고루틴은 몇 개이고, 상태 줄의 괄호 안에는 무엇이 붙나?
- 왜 세 테스트를 한 번에 돌리지 않고 **나눠** 돌렸나?
- `TestBubbleClock` 이 찍는 「가짜 시계가 간 양」과 테스트가 실제로 걸린 시간은?

### 7. 루프 안의 `time.After` (경계)

- 한 시간짜리 `time.After` 를 20만 번 만들고 버리면 `NumGoroutine` 은 어떻게 되나? 그것은 「고루틴 누수」인가?
- 이 판에서 버려진 타이머의 메모리는 치워지나 — 몇 판부터인가?
- `GODEBUG=asynctimerchan=1` 로 옛 동작을 켜 보면 무엇이 나오나? 그래서 이 툴체인으로 판 격자를 돌릴 수 있나?

### 8. 버퍼 1 의 조건 (왜)

- 결과 채널에 버퍼 1 을 주면 ① 이 고쳐지는 이유는?
- 버퍼 1 이 **맞는** 조건 둘을 적어라.
- 보내는 횟수를 모르면 무엇으로 고치나?

### 9. 창마다 못 보는 것 (경계)

- `NumGoroutine` 이 못 말해 주는 것은?
- 누수 프로파일이 못 보는 모양 **둘**은?
- `go vet` 은 이 네 모양에 대해 무엇을 말하나? 왜인가?
- 외부 도구 `goleak` 은 이 환경에 있나 — 없다면 그 칸은 무엇이라고 적나?

### 10. 명세와 구현 (왜)

- 「막힌 고루틴은 아무도 안 치운다」는 명세의 어느 사실들에서 나오나?
- 「GC 가 닿을 수 없는 채널에 막힌 고루틴을 `leaked` 로 표시한다」는 어느 층인가?
- 명세에 「누수」라는 낱말이 있나?

### 11. 다른 주제와 (연결)

- 네 모양 중 **교착 탐지까지 가리는** 것은 어느 것인가 — 29번 주제의 어느 실측과 이어지나?
- 30번 주제의 타임아웃 블록에서 남은 고루틴은 네 모양 중 어느 것인가?
- 실패 모드의 분류 일반은 어느 문서가 정본인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

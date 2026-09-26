# go/syntax/29 — 채널: 버퍼·방향·`close`·`range`·`nil` 채널 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★ **근거로 읽을 칸** — 셸이 찍은 `exit=` · 「교착 탐지=」 · **칸 수 `N / M`** · 패닉 첫 줄 · 고루틴 상태 줄 · 컴파일 진단.
> **근거로 읽지 않을 칸** — 다른 고루틴이 나오는 트레이스의 `goroutine N` 의 N(흔들린다 — 머리말의 정규화 칸).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `8 / 12` — `s > b` 인 칸이 죽는다 · exit 2 · `fatal error` · `[chan send]`

**출력**

```text
===== 소스: t29grid.go =====
package main

import (
	"fmt"
	"os"
	"strconv"
)

// 인자: 버퍼 크기, 보낼 횟수. 받는 쪽은 아무도 없다.
func main() {
	buf, _ := strconv.Atoi(os.Args[1])
	sends, _ := strconv.Atoi(os.Args[2])
	ch := make(chan int, buf)
	for i := range sends {
		ch <- i
	}
	fmt.Fprintln(os.Stderr, "보낸 수", sends, "len", len(ch), "cap", cap(ch))
}
===== 명령: go build -trimpath -o prog . && n=0; m=0; for b in 0 1 3; do for s in 1 2 3 4; do ./prog $b $s 2>err.txt; rc=$?; m=$((m+1)); d=아니오; if grep -q "all goroutines are asleep" err.txt; then d=예; n=$((n+1)); fi; echo "버퍼 $b · 송신 $s : exit=$rc 교착 탐지=$d"; done; done; echo "교착으로 죽은 칸 $n / $m" =====
버퍼 0 · 송신 1 : exit=2 교착 탐지=예
버퍼 0 · 송신 2 : exit=2 교착 탐지=예
버퍼 0 · 송신 3 : exit=2 교착 탐지=예
버퍼 0 · 송신 4 : exit=2 교착 탐지=예
버퍼 1 · 송신 1 : exit=0 교착 탐지=아니오
버퍼 1 · 송신 2 : exit=2 교착 탐지=예
버퍼 1 · 송신 3 : exit=2 교착 탐지=예
버퍼 1 · 송신 4 : exit=2 교착 탐지=예
버퍼 3 · 송신 1 : exit=0 교착 탐지=아니오
버퍼 3 · 송신 2 : exit=0 교착 탐지=아니오
버퍼 3 · 송신 3 : exit=0 교착 탐지=아니오
버퍼 3 · 송신 4 : exit=2 교착 탐지=예
교착으로 죽은 칸 8 / 12
(exit 0)
```

```text
===== 소스: t29grid.go =====
package main

import (
	"fmt"
	"os"
	"strconv"
)

// 인자: 버퍼 크기, 보낼 횟수. 받는 쪽은 아무도 없다.
func main() {
	buf, _ := strconv.Atoi(os.Args[1])
	sends, _ := strconv.Atoi(os.Args[2])
	ch := make(chan int, buf)
	for i := range sends {
		ch <- i
	}
	fmt.Fprintln(os.Stderr, "보낸 수", sends, "len", len(ch), "cap", cap(ch))
}
===== 명령: go build -trimpath -o prog . && ./prog 0 1 =====
fatal error: all goroutines are asleep - deadlock!

goroutine 1 [chan send]:
main.main()
	ex/t29grid.go:15 +0xa6
(exit 2)
```

**왜 그런가**

- ★★★ **버퍼 0 은 송신 1 부터, 버퍼 1 은 송신 2 부터, 버퍼 3 은 송신 4 에서** 죽는다 — **받는 쪽이 없으면 `s > b` 인 칸.** 12칸 중 **8**.
  명세 「**communication succeeds only when both a sender and receiver are ready**」(버퍼 0) · 「**can proceed if there is room in the buffer**」(버퍼 n).
- ★★★ 죽는 칸은 **exit 2** 의 **`fatal error: all goroutines are asleep - deadlock!`** — `panic` 이 아니라 **`recover` 로 못 잡는다.**
  ★ 이것은 **런타임(구현)** 이 준 것이다. 명세는 「막힌다」고만 한다.
- ★★ 상태 줄은 **`goroutine 1 [chan send]:`** — **채널 송신에 잠든 main.**

### 2. `0 3 · 1 3 · 2 3 · 3 3 · 2 3 · 0 0` · 깃발 `true` — 메모리 모델

**출력**

```text
===== 소스: t29lencap.go =====
package main

import (
	"fmt"
	"sync/atomic"
	"time"
)

func main() {
	b := make(chan int, 3)
	fmt.Println("버퍼 3, 만든 직후   : len", len(b), "cap", cap(b))
	for i := 1; i <= 3; i++ {
		b <- i
		fmt.Println("버퍼 3, 보낸 뒤", i, "  : len", len(b), "cap", cap(b))
	}
	<-b
	fmt.Println("버퍼 3, 하나 받은 뒤: len", len(b), "cap", cap(b))

	u := make(chan int)
	fmt.Println("버퍼 0             : len", len(u), "cap", cap(u))

	var aboutToReceive atomic.Bool
	go func() {
		time.Sleep(30 * time.Millisecond)
		aboutToReceive.Store(true) // 받기 직전에 깃발을 올린다
		<-u
	}()
	u <- 1 // 버퍼 0 에 보낸다
	fmt.Println("버퍼 0 송신이 돌아왔을 때 받는 쪽 깃발:", aboutToReceive.Load())
}
===== 명령: go build -trimpath -o prog . && ./prog =====
버퍼 3, 만든 직후   : len 0 cap 3
버퍼 3, 보낸 뒤 1   : len 1 cap 3
버퍼 3, 보낸 뒤 2   : len 2 cap 3
버퍼 3, 보낸 뒤 3   : len 3 cap 3
버퍼 3, 하나 받은 뒤: len 2 cap 3
버퍼 0             : len 0 cap 0
버퍼 0 송신이 돌아왔을 때 받는 쪽 깃발: true
(exit 0)
```

```text
===== 명령: sed -n "373,374p;405,406p;416,417p" "$(go env GOROOT)/doc/go_mem.html" | sed -e "s/<[^>]*>//g" =====
A send on a channel is synchronized before the completion of the
corresponding receive from that channel.
The closing of a channel is synchronized before a receive that returns a zero value
because the channel is closed.
A receive from an unbuffered channel is synchronized before the completion of
the corresponding send on that channel.
(exit 0)
```

**왜 그런가**

- ★★ 버퍼 3 은 `len` 이 **0 → 1 → 2 → 3**, 하나 받으면 **2**. `cap` 은 끝까지 3. **버퍼 0 은 `len 0 cap 0`** — 값이 **머무는 자리가 없다.**
- ★★★ **깃발은 `true`** — 받는 고루틴은 **깃발을 올린 뒤** 받고, 메모리 모델이
  「**A receive from an unbuffered channel is synchronized before the completion of the corresponding send**」 를 보장한다.
  그래서 송신이 **돌아온 뒤** 읽은 깃발은 **반드시** 선 뒤다. **30ms 는 순서를 만들지 않는다** — 송신이 막혀 있게 할 뿐이다.

### 3. 네 줄(5·10·11·19) · 세 줄은 통과 · `close(in)`

**출력**

```text
===== 소스: t29dir.go =====
package main

func producer(out chan<- int) {
	out <- 1
	<-out
}

func consumer(in <-chan int) {
	<-in
	in <- 1
	close(in)
}

func main() {
	ch := make(chan int, 1)
	producer(ch) // 양방향 채널을 넘긴다
	consumer(ch) // 양방향 채널을 넘긴다
	var r <-chan int = ch
	var back chan int = r
	_ = back
}
===== 명령: go build -trimpath -gcflags=-e -o prog . =====
# ex
./t29dir.go:5:4: invalid operation: cannot receive from send-only channel chan<- int out (variable of type chan<- int)
./t29dir.go:10:2: invalid operation: cannot send to receive-only channel <-chan int in (variable of type <-chan int)
./t29dir.go:11:8: invalid operation: cannot close receive-only channel in (variable of type <-chan int)
./t29dir.go:19:22: cannot use r (variable of type <-chan int) as chan int value in variable declaration
(exit 1)
```

**왜 그런가**

- ★★ **5행**(보내기 전용에서 받기) · **10행**(받기 전용에 보내기) · **11행**(받기 전용 닫기) · **19행**(받기 전용 → 양방향 변수) 넷.
- ★ `producer(ch)`·`consumer(ch)`·`var r <-chan int = ch` 는 **통과** — 양방향 → 한 방향은 **암묵 변환**, 그 반대만 막힌다.
- ★★★ **11행 `close(in)`** 이 「**닫는 것은 보내는 쪽**」 관례를 타입으로 강제한다 — 명세 「**It is an error if ch is a receive-only channel.**」

### 4. `7 true 0 false` · `0 false` · 패닉 둘 · `1 2 range 뒤 줄`

**출력**

```text
===== 소스: t29closed.go =====
package main

import (
	"fmt"
	"os"
)

func main() {
	ch := make(chan int, 2)
	switch os.Args[1] {
	case "rest": // 값이 남은 채로 닫고 받기
		ch <- 7
		close(ch)
		v1, ok1 := <-ch
		v2, ok2 := <-ch
		fmt.Println(v1, ok1, v2, ok2)
	case "empty": // 빈 채로 닫고 받기
		close(ch)
		v, ok := <-ch
		fmt.Println(v, ok)
	case "send": // 닫은 뒤 보내기
		close(ch)
		ch <- 1
		fmt.Println("송신 뒤 줄")
	case "reclose": // 두 번 닫기
		close(ch)
		close(ch)
		fmt.Println("두 번째 close 뒤 줄")
	case "range": // 닫은 채널을 range
		ch <- 1
		ch <- 2
		close(ch)
		for v := range ch {
			fmt.Print(v, " ")
		}
		fmt.Println("range 뒤 줄")
	}
}
===== 명령: go build -trimpath -o prog . && for c in rest empty send reclose range; do ./prog $c >out.txt 2>err.txt; rc=$?; echo "[$c] stdout      : $(cat out.txt)"; echo "[$c] stderr 첫 줄: $(head -n 1 err.txt)"; echo "[$c] exit=$rc"; done =====
[rest] stdout      : 7 true 0 false
[rest] stderr 첫 줄: 
[rest] exit=0
[empty] stdout      : 0 false
[empty] stderr 첫 줄: 
[empty] exit=0
[send] stdout      : 
[send] stderr 첫 줄: panic: send on closed channel
[send] exit=2
[reclose] stdout      : 
[reclose] stderr 첫 줄: panic: close of closed channel
[reclose] exit=2
[range] stdout      : 1 2 range 뒤 줄
[range] stderr 첫 줄: 
[range] exit=0
(exit 0)
```

**왜 그런가**

- ★★★ **`rest` 는 `7 true 0 false`** — 남은 7 은 **받혔고**, 그다음이 영값·`false`. 「**after any previously sent values have been received**」.
- ★★ **`empty` 는 `0 false`** — 닫힌 빈 채널은 **막히지 않고** 바로 영값.
- ★★★ **`send` 는 `panic: send on closed channel`, `reclose` 는 `panic: close of closed channel`** — 둘 다 **exit 2**. **`panic` 이므로 `recover` 가 들을 수 있는** 쪽이다(1번의 `fatal error` 와 다르다).
- ★★ **`range` 는 `1 2` 를 돌고 끝났다** — 「**until the channel is closed**」.

### 5. 첫 줄은 넷이 같다 · 셋은 막히고(`(nil chan)`) 닫기만 터진다 · 어느 칸도 안 찍힌다

**출력**

```text
===== 소스: t29nil.go =====
package main

import (
	"fmt"
	"os"
)

func main() {
	var ch chan int // nil 채널
	fmt.Fprintln(os.Stderr, "ch == nil :", ch == nil, "len", len(ch), "cap", cap(ch))
	switch os.Args[1] {
	case "send":
		ch <- 1
	case "recv":
		<-ch
	case "close":
		close(ch)
	case "range":
		for range ch {
		}
	}
	fmt.Fprintln(os.Stderr, "switch 뒤 줄")
}
===== 명령: go build -trimpath -o prog . && for c in send recv close range; do timeout 2 ./prog $c 2>err.txt; rc=$?; echo "[$c] $(sed -n 1p err.txt)"; echo "[$c] $(sed -n 2p err.txt)"; echo "[$c] $(grep -m 1 "^goroutine 1 " err.txt)"; echo "[$c] exit=$rc"; done =====
[send] ch == nil : true len 0 cap 0
[send] fatal error: all goroutines are asleep - deadlock!
[send] goroutine 1 [chan send (nil chan)]:
[send] exit=2
[recv] ch == nil : true len 0 cap 0
[recv] fatal error: all goroutines are asleep - deadlock!
[recv] goroutine 1 [chan receive (nil chan)]:
[recv] exit=2
[close] ch == nil : true len 0 cap 0
[close] panic: close of nil channel
[close] goroutine 1 [running]:
[close] exit=2
[range] ch == nil : true len 0 cap 0
[range] fatal error: all goroutines are asleep - deadlock!
[range] goroutine 1 [chan receive (nil chan)]:
[range] exit=2
(exit 0)
```

**왜 그런가**

- ★★ **첫 줄 `ch == nil : true len 0 cap 0`** 은 넷이 같다 — `len`·`cap` 은 **안 터진다.**
- ★★★ **`send`·`recv`·`range` 는 교착 탐지로 죽는다** — 상태 줄이 **`[chan send (nil chan)]`** · **`[chan receive (nil chan)]`**. 런타임이 **`(nil chan)` 을 붙여 구별**한다.
  명세 「**A send on a nil channel blocks forever.**」·「**Receiving from a nil channel blocks forever.**」
- ★★★ **`close` 만 `panic: close of nil channel`** — 「**Closing the nil channel also causes a run-time panic.**」
- ★ **`switch 뒤 줄` 은 네 칸 모두 안 찍혔다.**

### 6. 2 · 2 · 124 — `1 / 3` · `timeout` 이 끝냈다 · 타이머를 쥔 고루틴이 가린다

**출력**

```text
===== 소스: t29hide.go =====
package main

import (
	"fmt"
	"os"
	"time"
)

func main() {
	block := make(chan int)
	switch os.Args[1] {
	case "sleeper": // 잠만 자는 고루틴 하나를 곁에 둔다
		go func() {
			for {
				time.Sleep(time.Hour)
			}
		}()
	case "stuck": // 채널에서 막힌 고루틴 하나를 곁에 둔다
		go func() { <-block }()
	}
	fmt.Fprintln(os.Stderr, "main 이 nil 채널에 보낸다")
	var ch chan int
	ch <- 1
}
===== 명령: go build -trimpath -o prog . && n=0; m=0; for c in alone stuck sleeper; do timeout 2 ./prog $c 2>err.txt; rc=$?; m=$((m+1)); d=아니오; if grep -q "all goroutines are asleep" err.txt; then d=예; else n=$((n+1)); fi; echo "[$c] exit=$rc 교착 탐지=$d"; done; echo "탐지 못 한 칸 $n / $m" =====
[alone] exit=2 교착 탐지=예
[stuck] exit=2 교착 탐지=예
[sleeper] exit=124 교착 탐지=아니오
탐지 못 한 칸 1 / 3
(exit 0)
```

```text
===== 소스: t29hide.go =====
package main

import (
	"fmt"
	"os"
	"time"
)

func main() {
	block := make(chan int)
	switch os.Args[1] {
	case "sleeper": // 잠만 자는 고루틴 하나를 곁에 둔다
		go func() {
			for {
				time.Sleep(time.Hour)
			}
		}()
	case "stuck": // 채널에서 막힌 고루틴 하나를 곁에 둔다
		go func() { <-block }()
	}
	fmt.Fprintln(os.Stderr, "main 이 nil 채널에 보낸다")
	var ch chan int
	ch <- 1
}
===== 명령: go build -trimpath -o prog . && ./prog stuck =====
main 이 nil 채널에 보낸다
fatal error: all goroutines are asleep - deadlock!

goroutine 1 [chan send (nil chan)]:
main.main()
	ex/t29hide.go:23 +0x114

goroutine 7 [chan receive]:
main.main.func2()
	ex/t29hide.go:19 +0x19
created by main.main in goroutine 1
	ex/t29hide.go:19 +0xa5
(exit 2)
```

```text
===== 명령: sed -n "6511,6519p" "$(go env GOROOT)/src/runtime/proc.go" =====
	// There are no goroutines running, so we can look at the P's.
	for _, pp := range allp {
		if len(pp.timers.heap) > 0 {
			return
		}
	}

	unlock(&sched.lock) // unlock so that GODEBUG=scheddetail=1 doesn't hang
	fatal("all goroutines are asleep - deadlock!")
(exit 0)
```

**왜 그런가**

- ★★★ **`alone`·`stuck` 은 exit 2(탐지), `sleeper` 는 exit 124** — 프로그램은 **말없이 멈춰 있었고** 2초 뒤 **`timeout` 이** 죽였다. **탐지 못 한 칸 1 / 3.**
- ★★★ 런타임 `checkdead` 는 「**There are no goroutines running, so we can look at the P's**」 뒤 **타이머 힙이 비어 있지 않으면 `return`** 한다 — `time.Sleep(time.Hour)` 가 그 타이머다.
  **이것은 구현이다** — 명세에는 교착 탐지라는 말이 없다.
- ★★ 「새어 있는 고루틴이 탐지를 가린다」는 **반만 맞다.** **채널에 막혀 새어 있는 고루틴(`stuck`)은 못 가린다** — 그것도 잠들어 있고, 트레이스에 **같이 찍힌다**(`[chan receive]`).
  **가리는 것은 타이머를 쥔 고루틴**이다(네트워크 대기는 이 문서가 **안 던졌다**).

### 7. 닫지 않았으니까 · 끝남 ≠ 닫힘 · 조용히 멈춘다(누수)

- ★★★ `range` 는 **채널이 닫힐 때까지** 돈다. 보내는 고루틴이 **끝난 것**은 채널에 **아무 흔적도 안 남긴다** — 닫힘은 `close` 한 줄로만 생긴다.
- ★★ 탐침에서는 main 뿐이라 **교착 탐지가 `[chan receive]` 로 죽여 줬다.** 곁에 **타이머를 쥔 고루틴이 있으면** 탐지가 안 오고((6)번), 그 고루틴은 **영영 남는다** — [31번 주제](../31-goroutine-leaks/)의 넷째 모양이다.
- 고치는 법 — 보내는 고루틴 첫 줄에 **`defer close(out)`**.

```text
===== 소스: t29range.go =====
package main

import (
	"fmt"
	"os"
)

func main() {
	ch := make(chan int)
	go func() {
		for i := 1; i <= 3; i++ {
			ch <- i
		}
		if os.Args[1] == "close" {
			close(ch)
		}
	}()
	for v := range ch {
		fmt.Fprintln(os.Stderr, "받음", v)
	}
	fmt.Fprintln(os.Stderr, "range 뒤 줄")
}
===== 명령: go build -trimpath -o prog . && for m in close noclose; do echo "--- $m"; ./prog $m 2>&1; echo "exit=$?"; done =====
--- close
받음 1
받음 2
받음 3
range 뒤 줄
exit=0
--- noclose
받음 1
받음 2
받음 3
fatal error: all goroutines are asleep - deadlock!

goroutine 1 [chan receive]:
main.main()
	ex/t29range.go:18 +0xf4
exit=2
(exit 0)
```

### 8. 보내는 고루틴 · 프로세스 전체 exit 2 · 별도 취소 신호 · 전부 끝난 뒤 한 곳에서

```text
===== 소스: t29whoclose.go =====
package main

import (
	"fmt"
	"os"
)

func main() {
	ch := make(chan int)
	closed := make(chan struct{})
	done := make(chan struct{})
	go func() { // 보내는 쪽
		ch <- 1
		<-closed
		ch <- 2
		fmt.Fprintln(os.Stderr, "보내는 쪽 끝")
		close(done)
	}()
	fmt.Fprintln(os.Stderr, "받는 쪽이 받음", <-ch)
	close(ch) // 받는 쪽이 닫는다
	close(closed)
	<-done
	fmt.Fprintln(os.Stderr, "main 끝")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
받는 쪽이 받음 1
panic: send on closed channel

goroutine 19 [running]:
main.main.func1()
	ex/t29whoclose.go:15 +0x56
created by main.main in goroutine 1
	ex/t29whoclose.go:12 +0xba
(exit 2)
```

- ★★★ **보내는 고루틴**이 둘째 송신에서 **`panic: send on closed channel`**, 그 패닉은 **main 이 못 잡으니** 프로세스 전체가 **exit 2** 다(`main 끝` 없음).
- ★★ 받는 쪽의 「그만」은 **닫지 말고** 별도의 **`done` 채널이나 `context`** 로([목록의 **34번 주제**](../34-context-cancellation-deadlines-and-values/)). 보내는 쪽은 그것을 보고 **스스로 멈추고 스스로 닫는다.**
- ★ 보내는 쪽이 여럿이면 **`WaitGroup` 으로 전부 끝나길 기다린 뒤 한 곳에서** 닫는다([32번 주제](../32-sync-mutex-rwmutex-waitgroup-once/)).

### 9. 명세 · 구현 · 메모리 모델

```text
===== 명령: sed -n "1744,1748p;5354,5358p;6123,6126p;6804,6806p;7552,7558p" "$(go env GOROOT)/doc/go_spec.html" | sed -e "s/<[^>]*>//g" =====
If the capacity is zero or absent, the channel is unbuffered and communication
succeeds only when both a sender and receiver are ready. Otherwise, the channel
is buffered and communication succeeds without blocking if the buffer
is not full (sends) or not empty (receives).
A nil channel is never ready for communication.
The expression blocks until a value is available.
Receiving from a nil channel blocks forever.
A receive operation on a closed channel can always proceed
immediately, yielding the element type's zero value
after any previously sent values have been received.
A send on an unbuffered channel can proceed if a receiver is ready.
A send on a buffered channel can proceed if there is room in the buffer.
A send on a closed channel proceeds by causing a run-time panic.
A send on a nil channel blocks forever.
For channels, the iteration values produced are the successive values sent on
the channel until the channel is closed. If the channel
is nil, the range expression blocks forever.
records that no more values will be sent on the channel.
It is an error if ch is a receive-only channel.
Sending to or closing a closed channel causes a run-time panic.
Closing the nil channel also causes a run-time panic.
After calling close, and after any previously
sent values have been received, receive operations will return
the zero value for the channel's type without blocking.
(exit 0)
```

- ★★★ **「막힌다」는 명세**(위 원문), **「`fatal error` 로 죽는다」는 구현**(runtime `checkdead`) — 명세에는 교착 탐지가 없다.
- ★★ `checkdead` 는 **돌고 있는 고루틴이 없어도 타이머가 있으면** 「언젠가 깨어날 수 있다」고 보고 멈춘다 — 「There are no goroutines running, so we can look at the P's」.
- ★★ **메모리 모델**(`go_mem.html`)의 「A receive from an unbuffered channel is synchronized before the completion of the corresponding send」.

### 10. `Err(SendError)` 대 패닉·막힘 · 송신자의 드롭 · `05-backpressure`

```text
===== 소스: t29mpsc.rs =====
use std::sync::mpsc;
use std::thread;

fn main() {
    // 1) 받는 쪽을 버린 뒤 보내기
    let (tx, rx) = mpsc::channel::<i32>();
    drop(rx);
    println!("받는 쪽을 버린 뒤 send : {:?}", tx.send(1));

    // 2) 보내는 쪽이 전부 사라지면 받기 루프가 끝난다
    let (tx, rx) = mpsc::channel::<i32>();
    let h = thread::spawn(move || {
        for i in 1..=3 {
            tx.send(i).unwrap();
        }
    }); // tx 가 여기서 드롭된다
    let got: Vec<i32> = rx.iter().collect();
    h.join().unwrap();
    println!("송신자 드롭 뒤 받은 것 : {:?}", got);
    println!("그 뒤 recv            : {:?}", rx.recv());
}
===== 명령: rustc --edition 2024 -o prog t29mpsc.rs && ./prog =====
받는 쪽을 버린 뒤 send : Err(SendError { .. })
송신자 드롭 뒤 받은 것 : [1, 2, 3]
그 뒤 recv            : Err(RecvError)
(exit 0)
```

- ★★★ Rust 는 받는 쪽이 사라지면 **`send` 가 `Err`** 를 돌려준다. Go 에는 「받는 쪽이 사라졌다」는 개념이 없어 **보내는 쪽이 조용히 막힌다**(버퍼가 차면) — 누수의 첫 모양([31번 주제](../31-goroutine-leaks/)).
  Go 의 **패닉**은 **닫힌 채널에 보낼 때**만이다.
- ★★ Rust 는 **보내는 쪽이 전부 드롭되면** `rx.iter()` 가 끝나고 `recv` 가 `Err(RecvError)` — Go 의 `close` + `range` + `ok=false` 자리. **값의 수명이 닫힘**이다.
- ★ 버퍼 크기·넘침 정책의 **설계**는 [`../../../../../ops-patterns/05-backpressure/`](../../../../../ops-patterns/05-backpressure/).
  Rust 쪽 정본은 Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **51번**.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 로 **★고칠 것 0** |
| ★★★ 교착 격자 (`t29grid`) | 버퍼 0·1·3 × 송신 1\~4, 칸마다 exit + stderr 문구 | 12 | **8 / 12** |
| ★★ 닫힌 채널 (`t29closed`) | 다섯 칸, stdout·stderr 따로 | 5 | 패닉 2 · 값 3 |
| ★★ `nil` 채널 (`t29nil`) | 네 칸, `timeout 2` | 4 | 막힘 3 · 패닉 1 |
| ★★★ 탐지 못 하는 교착 (`t29hide`) | 곁의 고루틴 셋, `timeout 2` | 3 | **1 / 3**(`sleeper` exit 124) |
| ★ 방향 채널 (`t29dir`) | `go build -gcflags=-e` | 1 | 4줄 · exit 1 |
| ★ Rust `mpsc` (`t29mpsc`) | `rustc 1.92.0 --edition 2024` | 1 | `Err(SendError { .. })` |

**구현·환경에 달린 항목**

| 항목 | 무엇에 달렸나 |
|---|---|
| 교착 탐지 · 타이머 예외 | **runtime `checkdead`(이 판 소스 `proc.go:6511`)** |
| 고루틴 상태 문구 · `fatal error` 모양 · exit 2 | **runtime** |
| 트레이스의 고루틴 id | **흔들린다** — 정규화 규칙 `([Gg]oroutine) \d+` |
| 채널 연산의 **시간** | ★ **안 쟀다** |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다.

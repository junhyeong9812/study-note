# go/syntax/36 — Go 메모리 모델을 코드에서 읽기 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.
> 메모리 모델 문장은 **이 툴체인의 `$(go env GOROOT)/doc/go_mem.html`** 에서 줄 번호째 떴다.\
> ★ **근거로 읽을 칸** — 격자의 `-race 보고=예/아니오` · `9 / 13` · `0 / 6` · 어셈블리 명령 줄 · 20판 참거짓 · 보고 수 · 문서 문장.
> **근거로 읽지 않을 칸** — 루프가 **몇 ms 만에** 끝났나(안 실었다).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `sleep`·`goexit`·`plainflag`·`recvbuf` 만 보고 · `9 / 13`

**출력**

```text
===== 소스: t36hb.go =====
package main

import (
	"fmt"
	"os"
	"runtime"
	"sync"
	"sync/atomic"
	"time"
)

var data int // 고루틴이 쓰고 main 이 읽는다 — 그 사이에 무엇을 두나

func main() {
	switch os.Args[1] {
	case "sleep":
		go func() { data = 1 }()
		time.Sleep(100 * time.Millisecond)
	case "goexit":
		go func() { data = 1 }()
		for runtime.NumGoroutine() > 1 { // 고루틴이 끝나기를 수로 기다린다
			runtime.Gosched()
		}
	case "plainflag":
		var flag bool
		go func() { data = 1; flag = true }()
		for !flag {
		}
	case "atomicflag":
		var flag atomic.Bool
		go func() { data = 1; flag.Store(true) }()
		for !flag.Load() {
		}
	case "send":
		ch := make(chan int)
		go func() { data = 1; ch <- 0 }()
		<-ch
	case "sendbuf":
		ch := make(chan int, 1)
		go func() { data = 1; ch <- 0 }()
		<-ch
	case "close":
		ch := make(chan int)
		go func() { data = 1; close(ch) }()
		<-ch
	case "recv":
		ch := make(chan int)
		go func() { data = 1; <-ch }() // 고루틴은 받는 쪽
		ch <- 0                        // main 은 보내는 쪽
	case "recvbuf":
		ch := make(chan int, 1)
		go func() { data = 1; <-ch }()
		ch <- 0
		time.Sleep(100 * time.Millisecond)
	case "mutex":
		var mu sync.Mutex
		mu.Lock()
		go func() { data = 1; mu.Unlock() }()
		mu.Lock()
	case "once":
		var once sync.Once
		var wg sync.WaitGroup
		wg.Add(1)
		go func() { once.Do(func() { data = 1 }); wg.Done() }()
		time.Sleep(10 * time.Millisecond)
		once.Do(func() { data = 1 })
		// wg.Wait 전에 읽는다 — Once 만으로 순서가 서나
		_ = data
		wg.Wait()
		fmt.Println("once 끝")
		return
	case "waitgroup":
		var wg sync.WaitGroup
		wg.Go(func() { data = 1 })
		wg.Wait()
	case "gostmt":
		data = 1 // 이번에는 main 이 먼저 쓰고
		done := make(chan struct{})
		go func() { _ = data; close(done) }() // 고루틴이 읽는다
		<-done
		fmt.Println("gostmt 끝")
		return
	}
	fmt.Println(os.Args[1], ": data =", data)
}
===== 명령: go build -race -trimpath -o prog . && n=0; m=0; for c in sleep goexit plainflag atomicflag send sendbuf close recv recvbuf mutex once waitgroup gostmt; do timeout 10 ./prog $c >/dev/null 2>err.txt; rc=$?; m=$((m+1)); rep=아니오; if grep -q "DATA RACE" err.txt; then rep=예; else n=$((n+1)); fi; echo "[$c] exit=$rc · -race 보고=$rep"; done; echo "보고 없이 끝난 칸 $n / $m" =====
[sleep] exit=66 · -race 보고=예
[goexit] exit=66 · -race 보고=예
[plainflag] exit=66 · -race 보고=예
[atomicflag] exit=0 · -race 보고=아니오
[send] exit=0 · -race 보고=아니오
[sendbuf] exit=0 · -race 보고=아니오
[close] exit=0 · -race 보고=아니오
[recv] exit=0 · -race 보고=아니오
[recvbuf] exit=66 · -race 보고=예
[mutex] exit=0 · -race 보고=아니오
[once] exit=0 · -race 보고=아니오
[waitgroup] exit=0 · -race 보고=아니오
[gostmt] exit=0 · -race 보고=아니오
보고 없이 끝난 칸 9 / 13
(exit 0)
```

```text
===== 명령: sed -n "307,308p;336,337p;373,374p;405,406p;416,417p;456p;498,499p;559,560p;601,604p;608,609p" "$(go env GOROOT)/doc/go_mem.html" | sed -e "s/<[^>]*>//g" -e "s/&lt;/</g" =====
The go statement that starts a new goroutine
is synchronized before the start of the goroutine's execution.
The exit of a goroutine is not guaranteed to be synchronized before
any event in the program.
A send on a channel is synchronized before the completion of the
corresponding receive from that channel.
The closing of a channel is synchronized before a receive that returns a zero value
because the channel is closed.
A receive from an unbuffered channel is synchronized before the completion of
the corresponding send on that channel.
The kth receive from a channel with capacity C is synchronized before the completion of the k+Cth send on that channel.
For any sync.Mutex or sync.RWMutex variable l and n < m,
call n of l.Unlock() is synchronized before call m of l.Lock() returns.
The completion of a single call of f() from once.Do(f)
is synchronized before the return of any call of once.Do(f).
If the effect of an atomic operation A is observed by atomic operation B,
then A is synchronized before B.
All the atomic operations executed in a program behave as though executed
in some sequentially consistent order.
The preceding definition has the same semantics as C++’s sequentially consistent atomics
and Java’s volatile variables.
(exit 0)
```

**왜 그런가**

- ★★★ **보고 넷** — `sleep`(잠은 목록에 **없다**) · `goexit`(「**The exit of a goroutine is not guaranteed to be synchronized before any event**」) · `plainflag`(평범한 `bool` 은 동기화 연산이 **아니다** — 원자 연산 문장의 대상이 아니다) · `recvbuf`(2번).
- ★★★ **침묵 아홉** — 각각 문서의 한 문장에 대응한다: `atomicflag`(원자 A 를 B 가 보면) · `send`·`sendbuf`(송신 → 수신 완료) · `close`(닫기 → 영값 수신) · `recv`(버퍼 0 의 수신 → 송신 완료) · `mutex`(n번째 `Unlock` → m번째 `Lock`) · `once`(`f` 완료 → 모든 `Do` 반환) · `waitgroup`(`Done` → `Wait` 반환 — `WaitGroup` 문서) · `gostmt`(`go` 문 → 고루틴 시작).
- ★★ **`9 / 13`** — 스크립트가 셌다.

```text
===== 명령: go doc sync.WaitGroup.Done | sed -n "9,10p" =====
    In the terminology of the Go memory model, a call to Done "synchronizes
    before" the return of any Wait call that it unblocks.
(exit 0)
```

### 2. 「버퍼 0 의 수신 → 송신 완료」는 있고, 버퍼 C 면 「k번째 수신 → k+C번째 송신」뿐

- ★★★ **`recv`(버퍼 0)** — 「**A receive from an unbuffered channel is synchronized before the completion of the corresponding send on that channel.**」 main 의 송신이 **끝났으면** 고루틴의 수신도, 그 앞의 `data = 1` 도 끝나 있다.
- ★★★ **`recvbuf`(버퍼 1)** — 「**The kth receive from a channel with capacity C is synchronized before the completion of the k+Cth send on that channel.**」 C=1 이면 **첫 수신은 둘째 송신**보다 먼저일 뿐, **첫 송신과는 순서가 없다.** 첫 송신은 수신을 안 기다리고 바로 끝난다.
- ★★ 채널을 **받는 쪽이 신호를 주는 방향**(세마포어처럼)으로 쓸 때 버퍼를 주면 그 순서가 **사라진다.**

### 3. 여섯 칸 전부 「예」(exit 0) · `끝나지 않은 칸 0 / 6`

**출력**

```text
===== 소스: t36poll.go =====
package main

import (
	"fmt"
	"os"
	"time"
)

var done bool // 전역

type box struct{ done bool }

//go:noinline
func waitGlobal() {
	for !done {
	}
}

//go:noinline
func waitPtr(p *bool) {
	for !*p {
	}
}

//go:noinline
func waitField(b *box) {
	for !b.done {
	}
}

func main() {
	flag := new(bool)
	b := new(box)
	go func() {
		time.Sleep(10 * time.Millisecond)
		done = true
		*flag = true
		b.done = true
	}()
	switch os.Args[1] {
	case "global":
		waitGlobal()
	case "ptr":
		waitPtr(flag)
	case "field":
		waitField(b)
	}
	fmt.Println(os.Args[1], ": 루프 뒤 줄")
}
===== 명령: go build -trimpath -o opt . && go build -trimpath -gcflags="-N -l" -o noopt . && n=0; m=0; for b in opt noopt; do for f in global ptr field; do timeout 2 ./$b $f >/dev/null; rc=$?; m=$((m+1)); d=예; if [ $rc -ne 0 ]; then d=아니오; n=$((n+1)); fi; echo "[$b · $f] exit=$rc · 2초 안에 루프를 빠져나왔나=$d"; done; done; echo "끝나지 않은 칸 $n / $m" =====
[opt · global] exit=0 · 2초 안에 루프를 빠져나왔나=예
[opt · ptr] exit=0 · 2초 안에 루프를 빠져나왔나=예
[opt · field] exit=0 · 2초 안에 루프를 빠져나왔나=예
[noopt · global] exit=0 · 2초 안에 루프를 빠져나왔나=예
[noopt · ptr] exit=0 · 2초 안에 루프를 빠져나왔나=예
[noopt · field] exit=0 · 2초 안에 루프를 빠져나왔나=예
끝나지 않은 칸 0 / 6
(exit 0)
```

**왜 그런가**

- ★★★ **이 판에서는 여섯 칸 모두 끝났다** — 최적화를 켜도 꺼도, 전역·포인터·필드 어느 모양이든.
- ★★★ **그러나 이것은 관찰이다** — 이유는 4번(이 판의 gc 가 매번 다시 읽는다), 문서의 입장은 6번.

### 4. 매번 읽는다 — `CMPB main.done(SB), $0` 이 루프 안에 있다(둘 다)

**출력**

```text
===== 소스: t36poll.go =====
package main

import (
	"fmt"
	"os"
	"time"
)

var done bool // 전역

type box struct{ done bool }

//go:noinline
func waitGlobal() {
	for !done {
	}
}

//go:noinline
func waitPtr(p *bool) {
	for !*p {
	}
}

//go:noinline
func waitField(b *box) {
	for !b.done {
	}
}

func main() {
	flag := new(bool)
	b := new(box)
	go func() {
		time.Sleep(10 * time.Millisecond)
		done = true
		*flag = true
		b.done = true
	}()
	switch os.Args[1] {
	case "global":
		waitGlobal()
	case "ptr":
		waitPtr(flag)
	case "field":
		waitField(b)
	}
	fmt.Println(os.Args[1], ": 루프 뒤 줄")
}
===== 명령: for g in "" "-N -l"; do echo "--- -gcflags=\"$g -S\""; go build -trimpath -gcflags="$g -S" -o prog . 2>asm.txt || exit 1; awk "/^main.waitGlobal STEXT/{p=1} /^main.waitPtr STEXT/{p=0} p" asm.txt | grep -E "^\s+0x[0-9a-f]{4} [0-9]{5} \(" | grep -v -E "PCDATA|FUNCDATA"; done =====
--- -gcflags=" -S"
	0x0000 00000 (ex/t36poll.go:14)	TEXT	main.waitGlobal(SB), NOSPLIT|NOFRAME|ABIInternal, $0-0
	0x0000 00000 (ex/t36poll.go:15)	CMPB	main.done(SB), $0
	0x0007 00007 (ex/t36poll.go:15)	JEQ	0
	0x0009 00009 (ex/t36poll.go:17)	RET
--- -gcflags="-N -l -S"
	0x0000 00000 (ex/t36poll.go:14)	TEXT	main.waitGlobal(SB), NOSPLIT|NOFRAME|ABIInternal, $0-0
	0x0000 00000 (ex/t36poll.go:15)	JMP	2
	0x0002 00002 (ex/t36poll.go:15)	CMPB	main.done(SB), $0
	0x0009 00009 (ex/t36poll.go:15)	JEQ	13
	0x000b 00011 (ex/t36poll.go:15)	JMP	17
	0x000d 00013 (ex/t36poll.go:15)	JMP	15
	0x000f 00015 (ex/t36poll.go:15)	JMP	2
	0x0011 00017 (ex/t36poll.go:17)	RET
(exit 0)
```

**왜 그런가**

- ★★★ **기본 빌드** — `CMPB main.done(SB), $0` · `JEQ 0` — 0번 명령으로 돌아가 **메모리를 다시 읽는다.**
- ★★ **`-N -l`** — 점프가 늘었을 뿐 `CMPB main.done(SB)` 이 **루프 안에** 있다.
- ★★★ 「컴파일러가 루프에서 읽기를 끌어올린다」는 **이 판의 gc 에는 맞지 않았다.** 그것이 3번의 `0 / 6` 의 **구현 쪽 이유**다.

### 5. 「아니오」 · exit 66, 보고 2 건 · 빈 문자열 출력을 허용한다

**출력**

```text
===== 소스: t36pub.go =====
package main

import "fmt"

var msg string
var ready bool

func publish() {
	msg = "hello"
	ready = true
}

func main() {
	go publish()
	for !ready {
	}
	fmt.Printf("msg = %q\n", msg)
}
===== 명령: go build -trimpath -o prog . && bad=0; for i in $(seq 20); do timeout 2 ./prog >out.txt; grep -q "\"hello\"" out.txt || bad=$((bad+1)); done; echo "20판 중 hello 가 아닌 판(또는 안 끝난 판)이 있었나: $([ $bad -gt 0 ] && echo 예 || echo 아니오)"; go build -race -trimpath -o rprog . && ./rprog 2>err.txt; echo "-race 빌드 exit=$? · DATA RACE 보고 수: $(grep -c "DATA RACE" err.txt)" =====
20판 중 hello 가 아닌 판(또는 안 끝난 판)이 있었나: 아니오
msg = "hello"
-race 빌드 exit=66 · DATA RACE 보고 수: 2
(exit 0)
```

**왜 그런가**

- ★★ **20판 모두 `msg = "hello"`** — 이 판·이 CPU(x86-64)에서는 맞게 보였다.
- ★★★ **`-race` 빌드 — exit 66, 보고 2 건**(`ready`·`msg`). 순서를 세우는 연산이 **없다.**
- ★★★ 문서(6번 블록 첫 줄들) — 깃발을 봤다는 것이 값을 봤다는 뜻이 아니므로 「**this program could print an empty string too**」. 약한 순서 CPU 에서의 모습은 **못 쟀다**(이 머신에 에뮬레이터가 없다):

```text
===== 명령: for t in qemu-aarch64 qemu-arm; do if command -v $t >/dev/null; then echo "$t: 있음"; else echo "$t: 없음"; fi; done; echo "uname -m: $(uname -m)" =====
qemu-aarch64: 없음
qemu-arm: 없음
uname -m: x86_64
(exit 0)
```

### 6. 모순이 아니다 — 문서는 **허용 범위**, 3번은 그 안의 **한 점**

```text
===== 명령: sed -n "740,747p" "$(go env GOROOT)/doc/go_mem.html" | sed -e "s/<[^>]*>//g" =====
observing the write to done
implies observing the write to a, so this program could
print an empty string too.
Worse, there is no guarantee that the write to done will ever
be observed by main, since there are no synchronization
events between the two threads.  The loop in main is not
guaranteed to finish.
(exit 0)
```

- ★★★ 「**there is no guarantee that the write to done will ever be observed by main … The loop in main is not guaranteed to finish.**」 — 문서는 **끝나지 않아도 되는 구현**을 허용한다. 3번은 **이 판의 gc 가 그 허용을 쓰지 않은** 한 점이다.
- ★★★ 가르는 것은 **문서의 문장**과 **`-race` 의 보고**(1번 `plainflag` — 끝나는 판에서도 보고)다. **「잘 돌아가더라」는 둘 중 어느 것도 못 이긴다.**

### 7. 「The exit of a goroutine is not guaranteed to be synchronized before any event in the program.」 · `WaitGroup`·채널

- ★★★ 1번 블록의 규칙 문장 둘째 줄이다. **끝났다는 사실**을 `NumGoroutine` 으로 알아도, 그것은 **동기화 연산이 아니다.**
- ★★ 끝남을 알리려면 **`wg.Done` → `wg.Wait`**(`waitgroup` 칸 — 침묵) 또는 **채널 `close`**.

### 8. gcc 는 읽지 않고 영원히(`jmp .L3`), clang 은 루프째 삭제 · JIT 는 5 / 5 안 멈춤 · 같은 허용, 다른 점

- ★★★ [`../../../c/syntax/32-what-volatile-actually-guarantees/`](../../../c/syntax/32-what-volatile-actually-guarantees/) (1)절 — gcc `-O2` 의 `wait_plain` 은 **한 번 읽고 `jmp .L3`**, clang 은 **`ret`(루프 삭제)**.
- ★★★ [`../../../java/syntax/33-synchronized-and-volatile/`](../../../java/syntax/33-synchronized-and-volatile/) (3)절 — 평범한 `boolean` 플래그가 JIT 에서 **5 / 5 안 멈췄고**, `volatile` 은 5 / 5 멈췄다.
- ★★★ **같은 것** — 셋 다 **동기화 없는 폴링**이고, 각 언어의 메모리 모델이 **안 끝나도 된다**고 허용한다. **다른 것** — 이 판의 Go gc 는 **매번 다시 읽어서** 끝났다. **허용 범위 안의 다른 점**일 뿐이다.

### 9. C++ 의 순차 일관 원자 · 자바의 `volatile` — C `volatile` 은 아니다

- ★★★ 1번 규칙 블록의 마지막 두 줄 — 「**The preceding definition has the same semantics as C++'s sequentially consistent atomics and Java's volatile variables.**」
- ★★★ **C 의 `volatile` 은 순서를 안 막는다** — C 32편 (4)·(5)절과 (9)절의 표(「스레드 사이 순서 ✗ (UB — 데이터 경쟁)」). 이름이 같은 자바 `volatile` 과 **뜻이 다르다.**

### 10. 「report the race and halt execution」 — 이 판의 기본은 보고하고 계속 간다

```text
===== 명령: sed -n "3p;224,229p;788,792p;831p" "$(go env GOROOT)/doc/go_mem.html" | sed -e "s/<[^>]*>//g" =====
	"Subtitle": "Version of June 6, 2022",

Any implementation can, upon detecting a data race,
report the race and halt execution of the program.
Implementations using ThreadSanitizer
(accessed with “go build -race”)
do exactly this.
The Go memory model restricts compiler optimizations as much as it does Go programs.
Some compiler optimizations that would be valid in single-threaded programs are not valid in all Go programs.
In particular, a compiler must not introduce writes that do not exist in the original program,
it must not allow a single read to observe multiple values,
and it must not allow a single write to write multiple values.
Not introducing data races also means not assuming that loops terminate.
(exit 0)
```

- ★★★ 「**Any implementation can, upon detecting a data race, report the race and halt execution of the program. Implementations using ThreadSanitizer (accessed with "go build -race") do exactly this.**」
- ★★ [35번 주제](../35-data-races-and-the-race-detector/) (2)절 — **기본 `GORACE` 에서는 보고하고 끝까지 돌았다**(`Found 2`). **`halt_on_error=1`** 이라야 첫 보고에서 멈췄다. 문서의 「exactly this」와 **기본 동작이 한 칸 다르다.**

### 11. 「you are being too clever. / Don't be clever.」 · 목록의 연산만 쓴다

```text
===== 명령: sed -n "30,32p;36,37p;41p" "$(go env GOROOT)/doc/go_mem.html" | sed -e "s/<[^>]*>//g" =====
To serialize access, protect the data with channel operations or other synchronization primitives
such as those in the sync
and sync/atomic packages.
If you must read the rest of this document to understand the behavior of your program,
you are being too clever.
Don't be clever.
(exit 0)
```

- ★★★ 이 편의 13칸이 그 조언의 실측이다 — **목록에 있는 연산(9칸)은 침묵, 목록 밖의 「영리한」 방법(잠·고루틴 종료·평범한 깃발·버퍼 채널의 반대 방향)은 보고.**

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 로 **★고칠 것 0** |
| ★★★ HB 격자 (`t36hb`) | `-race` 빌드 · 13칸 | 탐색 3번 + 캡처마다 | **`9 / 13`** — 매번 같다 |
| ★★★ 폴링 (`t36poll`·`t36asm`) | 기본 · `-N -l` × 세 모양 · `-S` | 캡처마다 | **`0 / 6`** · 루프 안 `CMPB main.done(SB)` |
| ★★ 공개 (`t36pub`) | 보통 빌드 20판 + `-race` 1판 | 캡처마다 | 「아니오」 · exit 66 · 보고 2 |
| ★★★ 문서 (`t36advice`·`t36bad`·`t36rules`·`t36restr`·`t36wgdoc`) | `go_mem.html` 줄 번호 · `go doc` | 1 | `Version of June 6, 2022` |

**구현·환경에 달린 항목**

| 항목 | 무엇에 달렸나 |
|---|---|
| 폴링 루프가 끝나나 | ★★★ **이 판 gc 의 코드 생성** — 문서는 보장하지 않는다 |
| 20판 `hello` | **x86-64 의 메모리 순서 + 이 판 gc** — 약한 순서 CPU 는 **못 쟀다** |
| `-race` 의 보고/침묵 | **검출기** — 순서가 선 칸의 침묵은 관찰 |
| 동기화 연산의 **시간** | ★ **안 쟀다** |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다.

# go/syntax/32 — `sync`: `Mutex`·`RWMutex`·`WaitGroup`·`Once` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★ **근거로 읽을 칸** — `WARNING: DATA RACE` 의 **줄 번호와 `Read`/`Previous write` 짝** · `exit 66` · `답한 탐침 13 / 18` · 20판 **참거짓** · 교착 상태 줄 · `TryLock` 값 · 컴파일 진단.
> **근거로 읽지 않을 칸** — 주소 · `goroutine N`/`Goroutine N` 의 N · 교착 트레이스 프레임의 인자 값(머리말의 정규화 칸).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `1` · exit 66 · 14행 읽기(main) 대 11행 쓰기(고루틴) · `vet` 침묵

**출력**

```text
===== 소스: t32racecheck.go =====
package main

func main() {}
===== 명령: echo "CGO_ENABLED=$(go env CGO_ENABLED) CC=$(go env CC)"; echo "gcc $(gcc -dumpfullversion)"; go build -race -trimpath -o prog . && echo "go build -race exit=$?"; CGO_ENABLED=0 go build -race -trimpath -o prog2 .; echo "CGO_ENABLED=0 go build -race exit=$?" =====
CGO_ENABLED=1 CC=gcc
gcc 13.3.0
go build -race exit=0
go: -race requires cgo; enable cgo by setting CGO_ENABLED=1
CGO_ENABLED=0 go build -race exit=2
(exit 0)
```

```text
===== 소스: t32race.go =====
package main

import (
	"fmt"
	"time"
)

func main() {
	n := 0
	go func() {
		n++ // 고루틴이 쓴다
	}()
	time.Sleep(50 * time.Millisecond) // 50ms 기다린다
	fmt.Println(n)                    // main 이 읽는다
}
===== 명령: go build -race -trimpath -o prog . && ./prog 2>/dev/null; echo "stdout 만 받은 판 exit=$?" =====
1
stdout 만 받은 판 exit=66
(exit 0)
```

```text
===== 소스: t32race.go =====
package main

import (
	"fmt"
	"time"
)

func main() {
	n := 0
	go func() {
		n++ // 고루틴이 쓴다
	}()
	time.Sleep(50 * time.Millisecond) // 50ms 기다린다
	fmt.Println(n)                    // main 이 읽는다
}
===== 명령: go build -race -trimpath -o prog . && ./prog 2>&1 >/dev/null =====
==================
WARNING: DATA RACE
Read at 0x00c000018178 by main goroutine:
  main.main()
      ex/t32race.go:14 +0xbe

Previous write at 0x00c000018178 by goroutine 8:
  main.main.func1()
      ex/t32race.go:11 +0x44

Goroutine 8 (finished) created at:
  main.main()
      ex/t32race.go:10 +0xa4
==================
Found 1 data race(s)
(exit 66)
```

```text
===== 소스: t32race.go =====
package main

import (
	"fmt"
	"time"
)

func main() {
	n := 0
	go func() {
		n++ // 고루틴이 쓴다
	}()
	time.Sleep(50 * time.Millisecond) // 50ms 기다린다
	fmt.Println(n)                    // main 이 읽는다
}
===== 명령: go vet . && echo "vet exit=$?" =====
vet exit=0
(exit 0)
```

**왜 그런가**

- ★★★ **stdout `1`, exit 66** — 값은 맞아 보인다. 종료 코드가 **검출기가 무언가를 봤다**고 말한다.
- ★★★ **`Read at … by main goroutine: … t32race.go:14`** 와 **`Previous write at … by goroutine N: … t32race.go:11`** — main 의 읽기와 고루틴의 쓰기 사이에 **동기화가 없다.** `time.Sleep` 은 순서를 **만들지 않는다.**
- ★★ 쓴 고루틴은 **`(finished)`** — 이미 끝났어도 잡힌다. 검출기는 「동시에」가 아니라 **「순서가 세워졌나」** 를 본다.
- ★★ **`go vet` 은 `vet exit=0`** — 경쟁은 **실행해야** 보인다.
- ★ 이 창의 전제 — **`CGO_ENABLED=1`·gcc** 가 있어야 열린다. 끄면 **`-race requires cgo`**.

### 2. `13 / 18` · 침묵 p07·p10·p12·p14·p18 — 놓친 것은 p12 · 「contains sync.noCopy」 · 빌드된다

**출력**

```text
===== 소스: t32copy.go =====
package main

import (
	"sync"
	"sync/atomic"
)

type Counter struct {
	mu sync.Mutex
	n  int
}

func sink(any) {}

func (c Counter) Get() int { return c.n } // p01

func byValue(mu sync.Mutex) {} // p02

func wgByValue(wg sync.WaitGroup) {} // p03

func onceByValue(o sync.Once) {} // p04

func rwByValue(rw sync.RWMutex) {} // p05

func deref(p *Counter) Counter { return *p } // p06

func fresh() Counter { return Counter{} } // p07

func main() {
	var a Counter
	b := a // p08
	sink(&b)
	s := []Counter{{}, {}}
	for _, v := range s { // p09
		sink(&v)
	}
	for i := range s { // p10
		sink(&s[i])
	}
	var x any = a // p11
	sink(x)
	ch := make(chan Counter, 1)
	ch <- a // p12
	var ai atomic.Int64
	ai2 := ai // p13
	sink(&ai2)
	c := fresh() // p14
	sink(&c)
	arr := [1]sync.Mutex{}
	arr2 := arr // p15
	sink(&arr2)
	f := func(c Counter) {} // p16
	sink(f)
	m := map[string]*Counter{"k": {}}
	d := *m["k"] // p17
	sink(&d)
	p := &a // p18
	sink(p)
}
===== 명령: go vet . 2>vet.txt; echo "vet exit=$?"; cat vet.txt; n=0; m=0; for p in $(grep -o "// p[0-9][0-9]" t32copy.go | cut -c4-); do L=$(grep -n "// $p\$" t32copy.go | cut -d: -f1); m=$((m+1)); if grep -q "^t32copy.go:$L:" vet.txt; then n=$((n+1)); echo "$p (줄 $L) : 답함"; else echo "$p (줄 $L) : 침묵"; fi; done; echo "답한 탐침 $n / $m" =====
vet exit=1
t32copy.go:15:9: Get passes lock by value: ex.Counter contains sync.Mutex
t32copy.go:17:17: byValue passes lock by value: sync.Mutex
t32copy.go:19:19: wgByValue passes lock by value: sync.WaitGroup contains sync.noCopy
t32copy.go:21:20: onceByValue passes lock by value: sync.Once contains sync.noCopy
t32copy.go:23:19: rwByValue passes lock by value: sync.RWMutex
t32copy.go:25:41: return copies lock value: ex.Counter contains sync.Mutex
t32copy.go:31:7: assignment copies lock value to b: ex.Counter contains sync.Mutex
t32copy.go:34:9: range var v copies lock: ex.Counter contains sync.Mutex
t32copy.go:40:14: variable declaration copies lock value to x: ex.Counter contains sync.Mutex
t32copy.go:45:9: assignment copies lock value to ai2: sync/atomic.Int64 contains sync/atomic.noCopy
t32copy.go:50:10: assignment copies lock value to arr2: sync.Mutex
t32copy.go:52:14: func passes lock by value: ex.Counter contains sync.Mutex
t32copy.go:55:7: assignment copies lock value to d: ex.Counter contains sync.Mutex
p01 (줄 15) : 답함
p02 (줄 17) : 답함
p03 (줄 19) : 답함
p04 (줄 21) : 답함
p05 (줄 23) : 답함
p06 (줄 25) : 답함
p07 (줄 27) : 침묵
p08 (줄 31) : 답함
p09 (줄 34) : 답함
p10 (줄 37) : 침묵
p11 (줄 40) : 답함
p12 (줄 43) : 침묵
p13 (줄 45) : 답함
p14 (줄 47) : 침묵
p15 (줄 50) : 답함
p16 (줄 52) : 답함
p17 (줄 55) : 답함
p18 (줄 57) : 침묵
답한 탐침 13 / 18
(exit 0)
```

**왜 그런가**

- ★★★ **`답한 탐침 13 / 18`**.
- ★★★ **옳은 침묵 넷** — p07 `return Counter{}`(새 값) · p10 `&s[i]`(포인터) · p14 `c := fresh()`(호출 결과) · p18 `&a`(포인터).
  **놓친 것 하나 — p12 `ch <- a`.** 채널 송신은 **값을 복사**하는데 `vet` 이 답하지 않았다.
- ★★ `WaitGroup`·`Once` 는 **「contains sync.noCopy」**, `atomic.Int64` 는 **「contains sync/atomic.noCopy」** — 락이 아니라 **`noCopy` 표식**으로 걸린다. `Mutex`·`RWMutex` 는 타입 이름 자체로 걸린다.
- ★★ **`go build` 는 빌드한다** — `vet exit=1` 은 `vet` 의 종료 코드다. 「복사 금지」는 **컴파일러의 규칙이 아니다.**

### 3. `WaitGroup.Add called from inside new goroutine` · 예 · 예 · 아니오 · 아니다(`<autogenerated>`)

**출력**

```text
===== 소스: t32wgadd.go =====
package main

import (
	"fmt"
	"sync"
)

func main() {
	var wg sync.WaitGroup
	var mu sync.Mutex
	n := 0
	for range 100 {
		go func() {
			wg.Add(1) // 고루틴 안에서 Add
			defer wg.Done()
			mu.Lock()
			n++
			mu.Unlock()
		}()
	}
	wg.Wait()
	mu.Lock()
	fmt.Println(n)
	mu.Unlock()
}
===== 명령: go vet . && echo "vet exit=$?" =====
t32wgadd.go:14:10: WaitGroup.Add called from inside new goroutine
(exit 1)
```

```text
===== 소스: t32wgadd.go =====
package main

import (
	"fmt"
	"sync"
)

func main() {
	var wg sync.WaitGroup
	var mu sync.Mutex
	n := 0
	for range 100 {
		go func() {
			wg.Add(1) // 고루틴 안에서 Add
			defer wg.Done()
			mu.Lock()
			n++
			mu.Unlock()
		}()
	}
	wg.Wait()
	mu.Lock()
	fmt.Println(n)
	mu.Unlock()
}
===== 명령: go build -race -trimpath -o prog . && bad=0; races=0; for i in $(seq 20); do ./prog >out.txt 2>err.txt; [ "$(cat out.txt)" = 100 ] || bad=$((bad+1)); if grep -q "DATA RACE" err.txt; then races=$((races+1)); fi; done; echo "20판 중 100 이 아닌 판이 있었나 : $([ $bad -gt 0 ] && echo 예 || echo 아니오)"; echo "-race 가 한 판이라도 보고했나 : $([ $races -gt 0 ] && echo 예 || echo 아니오)"; echo "-race 가 20판 모두 보고했나   : $([ $races -eq 20 ] && echo 예 || echo 아니오)" =====
20판 중 100 이 아닌 판이 있었나 : 예
-race 가 한 판이라도 보고했나 : 예
-race 가 20판 모두 보고했나   : 아니오
(exit 0)
```

```text
===== 소스: t32wgadd.go =====
package main

import (
	"fmt"
	"sync"
)

func main() {
	var wg sync.WaitGroup
	var mu sync.Mutex
	n := 0
	for range 100 {
		go func() {
			wg.Add(1) // 고루틴 안에서 Add
			defer wg.Done()
			mu.Lock()
			n++
			mu.Unlock()
		}()
	}
	wg.Wait()
	mu.Lock()
	fmt.Println(n)
	mu.Unlock()
}
===== 명령: go build -race -trimpath -o prog . && for i in $(seq 50); do ./prog >/dev/null 2>err.txt; if grep -q "DATA RACE" err.txt; then break; fi; done; sed -n "1,/^Found/p" err.txt =====
==================
WARNING: DATA RACE
Write at 0x00c00011e028 by main goroutine:
  runtime.racewrite()
      <autogenerated>:1 +0x1e

Previous read at 0x00c00011e028 by goroutine 29:
  runtime.raceread()
      <autogenerated>:1 +0x1e

Goroutine 29 (finished) created at:
  main.main()
      ex/t32wgadd.go:13 +0x9d
==================
Found 1 data race(s)
(exit 0)
```

**왜 그런가**

- ★★★ **`vet` 은 늘 잡는다** — 이 판의 `waitgroup` 분석기, **정적**이다.
- ★★★ **「100 이 아닌 판이 있었나 : 예」** — `Wait` 가 `Add` 보다 먼저 카운터 0 을 보고 돌아온 판이 있다.
  **「한 판이라도 보고했나 : 예」·「20판 모두 보고했나 : 아니오」** — **`-race` 는 확률적**이다. 이번 실행에서 순서가 실제로 어긋난 판만 본다.
- ★★ 보고의 프레임은 **`runtime.racewrite()` · `<autogenerated>:1`** — `WaitGroup` 내부에 심은 **검출기 표식**이 걸린 것이다. 사용자 코드 줄은 **`created at: … t32wgadd.go:13`**(어느 `go` 문인가)로만 나온다.
- ★ 드물게는 **`panic: sync: WaitGroup is reused before previous Wait has returned`** 까지 난다 — 날 때까지 찾아서 잡았다:

```text
===== 소스: t32wgadd.go =====
package main

import (
	"fmt"
	"sync"
)

func main() {
	var wg sync.WaitGroup
	var mu sync.Mutex
	n := 0
	for range 100 {
		go func() {
			wg.Add(1) // 고루틴 안에서 Add
			defer wg.Done()
			mu.Lock()
			n++
			mu.Unlock()
		}()
	}
	wg.Wait()
	mu.Lock()
	fmt.Println(n)
	mu.Unlock()
}
===== 명령: go build -race -trimpath -o prog . && found=아니오; for i in $(seq 400); do ./prog >/dev/null 2>err.txt; if grep -q "reused before" err.txt; then found=예; break; fi; done; echo "400판 안에 WaitGroup 재사용 패닉이 났나: $found"; echo "그 판의 패닉 첫 줄: $(grep -m 1 "^panic:" err.txt)" =====
400판 안에 WaitGroup 재사용 패닉이 났나: 예
그 판의 패닉 첫 줄: panic: sync: WaitGroup is reused before previous Wait has returned
(exit 0)
```

- 고치는 법 — **`go` 앞에서 `Add`**, 또는 **`wg.Go`**(1.25).

### 4. `첫 Lock` 뒤 교착 · exit 2 · `[sync.Mutex.Lock]` · 자바는 들어간다

**출력**

```text
===== 소스: t32relock.go =====
package main

import (
	"fmt"
	"os"
	"sync"
)

func main() {
	var mu sync.Mutex
	mu.Lock()
	fmt.Fprintln(os.Stderr, "첫 Lock")
	mu.Lock() // 같은 고루틴이 한 번 더
	fmt.Fprintln(os.Stderr, "둘째 Lock")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
첫 Lock
fatal error: all goroutines are asleep - deadlock!

goroutine 1 [sync.Mutex.Lock]:
internal/sync.runtime_SemacquireMutex(0xd6388a12010?, 0x30?, 0x9?)
	runtime/sema.go:95 +0x25
internal/sync.(*Mutex).lockSlow(0xd6388a08008)
	internal/sync/mutex.go:149 +0x15a
internal/sync.(*Mutex).Lock(...)
	internal/sync/mutex.go:70
sync.(*Mutex).Lock(...)
	sync/mutex.go:46
main.main()
	ex/t32relock.go:13 +0xa5
(exit 2)
```

```text
===== 소스: J32Reentry.java =====
public class J32Reentry {
    private final Object lock = new Object();

    void outer() {
        synchronized (lock) {
            inner(); // 같은 스레드가 같은 모니터를 다시 잡는다
        }
    }

    void inner() {
        synchronized (lock) {
            System.out.println("inner 안: holdsLock=" + Thread.holdsLock(lock));
        }
    }

    public static void main(String[] args) {
        new J32Reentry().outer();
        System.out.println("outer 뒤 줄");
    }
}
===== 명령: javac -version && javac -d . J32Reentry.java && java -cp . J32Reentry =====
javac 21.0.5
inner 안: holdsLock=true
outer 뒤 줄
(exit 0)
```

**왜 그런가**

- ★★★ **`fatal error: all goroutines are asleep - deadlock!`**, **`goroutine 1 [sync.Mutex.Lock]:`**, exit 2 — **자기 자신을 기다린다.** Go `Mutex` 는 **재진입이 없다**(누가 잠갔는지 기억하지 않는다 — 8번).
- ★★★ 자바는 **`inner 안: holdsLock=true` · `outer 뒤 줄`** — 모니터가 **재진입**이다. 정본은 [`../../../java/syntax/33-synchronized-and-volatile/`](../../../java/syntax/33-synchronized-and-volatile/) (6)절.

### 5. `alone` 은 된다 · `writer` 는 교착 · `[sync.RWMutex.RLock]`·`[sync.RWMutex.Lock]` · 쓰는 쪽이 없으면 안 드러난다

**출력**

```text
===== 소스: t32rw.go =====
package main

import (
	"fmt"
	"os"
	"sync"
	"time"
)

func main() {
	var rw sync.RWMutex
	rw.RLock()
	fmt.Fprintln(os.Stderr, "첫 RLock")
	if os.Args[1] == "writer" {
		go func() { // 쓰는 쪽이 끼어들어 Lock 을 기다린다
			rw.Lock()
			rw.Unlock()
		}()
		time.Sleep(50 * time.Millisecond)
	}
	rw.RLock() // 같은 고루틴이 읽기 잠금을 한 번 더
	fmt.Fprintln(os.Stderr, "둘째 RLock")
	rw.RUnlock()
	rw.RUnlock()
}
===== 명령: go build -trimpath -o prog . && for c in alone writer; do timeout 2 ./prog $c 2>err.txt; rc=$?; d=아니오; if grep -q "all goroutines are asleep" err.txt; then d=예; fi; echo "[$c] 둘째 RLock 줄이 찍혔나: $(grep -q "둘째 RLock" err.txt && echo 예 || echo 아니오) · exit=$rc · 교착 탐지=$d"; done =====
[alone] 둘째 RLock 줄이 찍혔나: 예 · exit=0 · 교착 탐지=아니오
[writer] 둘째 RLock 줄이 찍혔나: 아니오 · exit=2 · 교착 탐지=예
(exit 0)
```

```text
===== 소스: t32rw.go =====
package main

import (
	"fmt"
	"os"
	"sync"
	"time"
)

func main() {
	var rw sync.RWMutex
	rw.RLock()
	fmt.Fprintln(os.Stderr, "첫 RLock")
	if os.Args[1] == "writer" {
		go func() { // 쓰는 쪽이 끼어들어 Lock 을 기다린다
			rw.Lock()
			rw.Unlock()
		}()
		time.Sleep(50 * time.Millisecond)
	}
	rw.RLock() // 같은 고루틴이 읽기 잠금을 한 번 더
	fmt.Fprintln(os.Stderr, "둘째 RLock")
	rw.RUnlock()
	rw.RUnlock()
}
===== 명령: go build -trimpath -o prog . && ./prog writer =====
첫 RLock
fatal error: all goroutines are asleep - deadlock!

goroutine 1 [sync.RWMutex.RLock]:
sync.runtime_SemacquireRWMutexR(0x2faf080?, 0x8?, 0x19106e70e90?)
	runtime/sema.go:100 +0x25
sync.(*RWMutex).RLock(...)
	sync/rwmutex.go:74
main.main()
	ex/t32rw.go:21 +0x12c

goroutine 7 [sync.RWMutex.Lock]:
sync.runtime_SemacquireRWMutex(0x0?, 0x0?, 0x0?)
	runtime/sema.go:105 +0x25
sync.(*RWMutex).Lock(0x0?)
	sync/rwmutex.go:155 +0x65
main.main.func1()
	ex/t32rw.go:16 +0x1c
created by main.main in goroutine 1
	ex/t32rw.go:15 +0xff
(exit 2)
```

```text
===== 명령: go doc sync.RWMutex | sed -n "1,20p" =====
package sync // import "sync"

type RWMutex struct {
	// Has unexported fields.
}
    A RWMutex is a reader/writer mutual exclusion lock. The lock can be held
    by an arbitrary number of readers or a single writer. The zero value for a
    RWMutex is an unlocked mutex.

    A RWMutex must not be copied after first use.

    If any goroutine calls RWMutex.Lock while the lock is already held by one or
    more readers, concurrent calls to RWMutex.RLock will block until the writer
    has acquired (and released) the lock, to ensure that the lock eventually
    becomes available to the writer. Note that this prohibits recursive
    read-locking. A RWMutex.RLock cannot be upgraded into a RWMutex.Lock,
    nor can a RWMutex.Lock be downgraded into a RWMutex.RLock.

    In the terminology of the Go memory model, the n'th call to RWMutex.Unlock
    “synchronizes before” the m'th call to Lock for any n < m, just as for
(exit 0)
```

**왜 그런가**

- ★★★ **`alone` — 「둘째 RLock 줄이 찍혔나 : 예」, exit 0.** **`writer` — 「아니오」, exit 2, 교착 탐지.**
- ★★★ main 은 **`[sync.RWMutex.RLock]`**(둘째 읽기 잠금), 쓰는 고루틴은 **`[sync.RWMutex.Lock]`** — 쓰는 쪽은 **읽는 쪽이 풀기를**, 둘째 `RLock` 은 **쓰는 쪽이 끝나기를** 기다린다.
  문서 「**concurrent calls to RWMutex.RLock will block until the writer has acquired (and released) the lock … this prohibits recursive read-locking**」.
- ★★ **쓰는 쪽이 `Lock` 대기에 들어간 바로 그때**만 터진다 — 쓰기가 드문 테스트에서는 `alone` 처럼 **그냥 된다.** 그리고 서버에서는 교착 탐지도 안 온다([29번 주제](../29-channels-buffering-direction-close-range-and-nil/) (8)절).

### 6. `true` 대 `false` · 영원히 막혔을 것

**출력**

```text
===== 소스: t32defer.go =====
package main

import (
	"fmt"
	"os"
	"sync"
)

var mu sync.Mutex

func withDefer() {
	mu.Lock()
	defer mu.Unlock()
	panic("잠근 채 터짐")
}

func withoutDefer() {
	mu.Lock()
	panic("잠근 채 터짐")
	mu.Unlock()
}

func call(f func()) {
	defer func() { recover() }()
	f()
}

func main() {
	if os.Args[1] == "defer" {
		call(withDefer)
	} else {
		call(withoutDefer)
	}
	fmt.Printf("[%s] recover 뒤 TryLock: %v\n", os.Args[1], mu.TryLock())
}
===== 명령: go build -trimpath -o prog . && ./prog defer && ./prog nodefer =====
[defer] recover 뒤 TryLock: true
[nodefer] recover 뒤 TryLock: false
(exit 0)
```

**왜 그런가**

- ★★★ **`defer` 는 `true`**(풀려 있다), **`nodefer` 는 `false`**(잠긴 채) — 패닉이 손으로 쓴 `Unlock` **앞에서** 함수를 떠났다. `defer` 는 **패닉 경로에서도 돈다**([26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/)).
- ★★ `Lock` 을 불렀다면 **영원히 막혔다** — 4번의 교착과 같은 모양(곁에 아무도 없으면 교착 탐지, 있으면 **조용히 멈춤**).

### 7. 1 번 · 100 / 100 · 「no call to Do returns until the one call to f returns」 · 한 번

```text
===== 소스: t32once.go =====
package main

import (
	"fmt"
	"sync"
	"sync/atomic"
)

func main() {
	var once sync.Once
	var calls atomic.Int32
	config := ""
	var saw atomic.Int32
	var wg sync.WaitGroup
	for range 100 {
		wg.Go(func() {
			once.Do(func() {
				calls.Add(1)
				config = "준비됨"
			})
			if config == "준비됨" { // Do 가 돌아온 뒤 읽는다
				saw.Add(1)
			}
		})
	}
	wg.Wait()
	fmt.Println("초기화 함수가 돈 횟수   :", calls.Load())
	fmt.Println("준비된 값을 본 고루틴 수:", saw.Load(), "/ 100")

	load := sync.OnceValue(func() int { calls.Add(1); return 42 })
	fmt.Println("OnceValue 두 번         :", load(), load(), "· 누적 호출", calls.Load())
}
===== 명령: go build -race -trimpath -o prog . && ./prog =====
초기화 함수가 돈 횟수   : 1
준비된 값을 본 고루틴 수: 100 / 100
OnceValue 두 번         : 42 42 · 누적 호출 2
(exit 0)
```

```text
===== 명령: go doc sync.Once.Do | sed -n "19,20p" =====
    Because no call to Do returns until the one call to f returns, if f causes
    Do to be called, it will deadlock.
(exit 0)
```

- ★★★ **초기화 1 번, 100 / 100** — `-race` 빌드에서 보고 0 줄.
- ★★★ 「**no call to Do returns until the one call to f returns**」 — `Do` 가 돌아온 모든 고루틴은 **초기화가 끝난 뒤**에 있다. 순서를 `Once` 가 세우니 `config` 읽기는 경쟁이 아니다.
- ★★ **`OnceValue` 두 번 — `42 42`, 누적 호출 2**(`Do` 의 1 + `OnceValue` 의 1) — 함수는 **한 번**만 돌았다.

### 8. 풀 수 있다 · `fatal error: sync: unlock of unlocked mutex` · 못 받는다

```text
===== 소스: t32owner.go =====
package main

import (
	"fmt"
	"sync"
)

func main() {
	var mu sync.Mutex
	mu.Lock() // main 이 잠근다
	done := make(chan struct{})
	go func() {
		mu.Unlock() // 다른 고루틴이 푼다
		close(done)
	}()
	<-done
	fmt.Println("다른 고루틴이 푼 뒤 TryLock:", mu.TryLock())
}
===== 명령: go build -race -trimpath -o prog . && ./prog =====
다른 고루틴이 푼 뒤 TryLock: true
(exit 0)
```

```text
===== 명령: go doc sync.Mutex.Unlock =====
package sync // import "sync"

func (m *Mutex) Unlock()
    Unlock unlocks m. It is a run-time error if m is not locked on entry to
    Unlock.

    A locked Mutex is not associated with a particular goroutine. It is allowed
    for one goroutine to lock a Mutex and then arrange for another goroutine to
    unlock it.
(exit 0)
```

```text
===== 소스: t32unlock.go =====
package main

import (
	"fmt"
	"os"
	"sync"
)

func main() {
	defer func() {
		fmt.Fprintln(os.Stderr, "recover() =", recover())
	}()
	var mu sync.Mutex
	mu.Unlock() // 잠그지 않은 뮤텍스를 푼다
}
===== 명령: go build -trimpath -o prog . && ./prog =====
fatal error: sync: unlock of unlocked mutex

goroutine 1 [running]:
internal/sync.fatal({0x49ef6b?, 0x0?})
	runtime/panic.go:1205 +0x18
internal/sync.(*Mutex).unlockSlow(0x300aac21e008, 0xffffffff)
	internal/sync/mutex.go:204 +0x35
internal/sync.(*Mutex).Unlock(...)
	internal/sync/mutex.go:198
sync.(*Mutex).Unlock(...)
	sync/mutex.go:65
main.main()
	ex/t32unlock.go:14 +0x4b
(exit 2)
```

- ★★ **다른 고루틴이 푼 뒤 `TryLock: true`** — 「**A locked Mutex is not associated with a particular goroutine**」.
- ★★★ 안 잠근 것을 풀면 **`fatal error: sync: unlock of unlocked mutex`**, exit 2 — **`recover() =` 줄이 안 찍혔다.** `panic` 이 아니라 **`fatal error`** 라 `recover` 가 **못 듣는다**([27번 주제](../27-panic-recover-and-where-to-use-them/)). 문서의 「**It is a run-time error**」가 이 모양이다.

### 9. `E0614` — 데이터가 락 안에 · C++ 는 컴파일 에러, Go 는 `vet` · `defer` — 적어야 돈다

```text
===== 소스: t32mutex.rs =====
use std::sync::Mutex;

fn main() {
    let m = Mutex::new(0);
    *m += 1; // 잠그지 않고 데이터를 만진다
    {
        let mut g = m.lock().unwrap();
        *g += 1;
    } // g 가 여기서 드롭되며 풀린다
    println!("{:?}", m);
}
===== 명령: rustc --edition 2024 -o prog t32mutex.rs =====
error[E0614]: type `std::sync::Mutex<{integer}>` cannot be dereferenced
 --> t32mutex.rs:5:5
  |
5 |     *m += 1; // 잠그지 않고 데이터를 만진다
  |     ^^ can't be dereferenced

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0614`.
(exit 1)
```

```text
===== 소스: t32copy.cpp =====
#include <mutex>

struct Counter {
    std::mutex mu;
    int n = 0;
};

void by_value(std::mutex m) {}

int main() {
    Counter a;
    Counter b = a;    // 구조체째 복사
    by_value(a.mu);   // 값으로 넘기기
}
===== 명령: g++ -std=c++20 -fsyntax-only t32copy.cpp =====
t32copy.cpp: In function ‘int main()’:
t32copy.cpp:12:17: error: use of deleted function ‘Counter::Counter(const Counter&)’
   12 |     Counter b = a;    // 구조체째 복사
      |                 ^
t32copy.cpp:3:8: note: ‘Counter::Counter(const Counter&)’ is implicitly deleted because the default definition would be ill-formed:
    3 | struct Counter {
      |        ^~~~~~~
t32copy.cpp:3:8: error: use of deleted function ‘std::mutex::mutex(const std::mutex&)’
In file included from /usr/include/c++/13/mutex:45,
                 from t32copy.cpp:1:
/usr/include/c++/13/bits/std_mutex.h:107:5: note: declared here
  107 |     mutex(const mutex&) = delete;
      |     ^~~~~
t32copy.cpp:13:13: error: use of deleted function ‘std::mutex::mutex(const std::mutex&)’
   13 |     by_value(a.mu);   // 값으로 넘기기
      |     ~~~~~~~~^~~~~~
/usr/include/c++/13/bits/std_mutex.h:107:5: note: declared here
  107 |     mutex(const mutex&) = delete;
      |     ^~~~~
t32copy.cpp:8:26: note:   initializing argument 1 of ‘void by_value(std::mutex)’
    8 | void by_value(std::mutex m) {}
      |               ~~~~~~~~~~~^
(exit 1)
```

- ★★★ Rust — **`error[E0614]: type std::sync::Mutex<{integer}> cannot be dereferenced`.** `Mutex<T>` 가 **데이터를 감싸서** `lock()` 의 가드를 거치지 않으면 **만질 길이 없다.** Go 는 **뮤텍스와 데이터가 따로**라 잠그지 않고도 컴파일된다 — 그 관계를 검사하는 것은 **`-race` 뿐**이다.
- ★★★ C++ — **`use of deleted function 'std::mutex::mutex(const std::mutex&)'`**, exit 1. **컴파일러가** 복사를 막는다. Go 는 **컴파일러가 통과시키고 `vet` 이 대부분 잡는다**(2번 — 13 / 18).
- ★★ `lock_guard` 의 소멸자 자리를 Go 에서는 **`defer mu.Unlock()`** 이 맡는다 — 다른 점은 **Go 는 적어야 돌고**(잊으면 6번의 `false`), C++ 는 **타입이 돌린다**([`../../../cpp/syntax/15-raii-resources-as-types/`](../../../cpp/syntax/15-raii-resources-as-types/) (3)절).

### 10. 채널 · 뮤텍스 · 닫힌 채널 · 안 해 준다(안 쟀다)

- ★★★ **값·일감을 넘긴다 → 채널**([29번 주제](../29-channels-buffering-direction-close-range-and-nil/)), **한 자리의 상태를 여럿이 고친다 → `Mutex`**.
- ★★ 여럿에게 한 번에 → **채널을 `close`**(닫힌 채널은 모든 받는 쪽을 깨운다).
- ★★★ **안 해 준다** — 이 배치는 **어떤 시간도 재지 않았다.** 「채널은 느리다」·「`RWMutex` 가 빠르다」는 이 문서의 근거가 없다. 고르는 기준은 **문제의 모양**이다.

### 11. 라이브러리 계약(`go doc`), 지키는 것은 `vet` · 「이번 실행에서 못 봤다」까지 · cgo 가 꺼지면

```text
===== 명령: go doc sync.Mutex | sed -n "1,20p" =====
package sync // import "sync"

type Mutex struct {
	// Has unexported fields.
}
    A Mutex is a mutual exclusion lock. The zero value for a Mutex is an
    unlocked mutex.

    A Mutex must not be copied after first use.

    In the terminology of the Go memory model, the n'th call to Mutex.Unlock
    “synchronizes before” the m'th call to Mutex.Lock for any n < m.
    A successful call to Mutex.TryLock is equivalent to a call to Lock. A failed
    call to TryLock does not establish any “synchronizes before” relation at
    all.

[the Go memory model]: https://go.dev/ref/mem

func (m *Mutex) Lock()
func (m *Mutex) TryLock() bool
(exit 0)
```

```text
===== 명령: go tool vet help | grep -E "^    (copylocks|waitgroup) " =====
    copylocks    check for locks erroneously passed by value
    waitgroup    check for misuses of sync.WaitGroup
(exit 0)
```

- ★★★ 「**A Mutex must not be copied after first use.**」 — **명세가 아니라 `sync` 문서의 계약**이다. 지켜 주는 것은 **컴파일러가 아니라 `vet copylocks`**(휴리스틱 — 놓치는 자리가 있다).
- ★★★ `-race` 의 침묵은 「**이번 실행에서 순서 없는 접근을 못 봤다**」 까지다 — 3번의 20판 중 **어떤 판은 침묵했다.** 「경쟁이 없다」의 증명이 아니다.
- ★★ **`CGO_ENABLED=0`(또는 C 컴파일러 없음)** — `go: -race requires cgo`(1번 판별 블록).

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 로 **★고칠 것 0** |
| ★★★ `-race` 판별 (`t32judge`) | `go env` · `gcc -dumpfullversion` · `-race` 빌드 두 번(`CGO_ENABLED=0` 포함) | 1 | **열린다** · 끄면 `-race requires cgo` |
| ★★★ 경쟁 보고 (`t32race`·`t32racerr`) | stdout·stderr 따로 | 2 | `1` · `DATA RACE` · exit 66 |
| ★★★ `copylocks` (`t32copy`) | 탐침 18, 줄 번호로 맞춤 | 1 | **13 / 18** · `ch <- a` 침묵 |
| ★★★ `Add` 함정 (`t32wgvet`·`t32wgrun`·`t32wgrace`) | `vet` + 20판 참거짓 + 보고가 날 때까지(최대 50판) + 패닉이 날 때까지(최대 400판) | 가변 | `vet` 늘 · `-race` 어떤 판만 |
| ★★ 재진입·재귀 읽기 잠금 (`t32relock`·`t32rw`·`t32rwdead`) | 교착 탐지, `timeout 2` | 4 | `[sync.Mutex.Lock]` · `alone` 됨 · `writer` 교착 |
| ★★ `defer`·`Once`·주인·안 잠근 `Unlock` | `TryLock` · `-race` 빌드 | 5 | `true`/`false` · `1`·`100 / 100` · `fatal error` |
| ★ 대비 — 자바·Rust·C++ | `javac 21.0.5` · `rustc 1.92.0` · `g++ 13.3.0` | 3 | 재진입 됨 · `E0614` · `deleted function` |

**구현·환경에 달린 항목**

| 항목 | 무엇에 달렸나 |
|---|---|
| `-race` 창 | **cgo + gcc**(이 머신: 있음) |
| `-race` 가 어느 판을 잡나 | **스케줄링 — 흔들린다**(참거짓으로 접었다) |
| `copylocks`·`waitgroup` 의 판정 범위 | **이 판 `vet`** — `ch <- a` 를 놓친 것이 의도인지는 **확인 못 했다** |
| `internal/sync` 구현 경로 · `fatal error` 문구 | **이 판 runtime** |
| 주소 · 고루틴 id · 교착 트레이스의 짧은 인자 | **흔들린다** — 정규화 규칙 `([Gg]oroutine) \d+` · `\((?:0x\|\{0x)[^()]*\)` + 기본 넷 |
| 락·채널의 **시간** | ★ **안 쟀다** |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다.

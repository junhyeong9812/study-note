# go/syntax/36 — Go 메모리 모델을 코드에서 읽기 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ **모든 문제에서 「두 고루틴 사이에 메모리 모델 문서의 어느 문장이 서 있나」를 먼저 적어라 — 없으면 「없다」고 적어라.**
> ★★ **「이 판에서 그랬다」와 「문서가 약속한다」를 다른 칸에 적어라.**
> 소스는 전부 `go build -trimpath -o prog .`(표시한 것은 `-race`·`-gcflags` 를 붙여) 로 빌드했다. 모듈 이름은 `ex` 다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 사이에 무엇을 두나 — 13칸 (예측)

```go
// t36hb.go
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
```

<!-- -race 빌드. 셸이 13칸을 차례로 돌려 칸마다 exit · -race 보고 예/아니오를 찍고, 마지막 줄에 「보고 없이 끝난 칸 N / 13」. -->

- 칸마다 `-race 보고` 는?
- 마지막 줄의 수는?
- 보고가 나는 칸 각각에 대해, 메모리 모델 문서의 어느 문장이 **없어서**인가?

### 2. 버퍼 0 과 버퍼 1 (왜)

- `recv` 와 `recvbuf` 는 버퍼 크기만 다르다. 한쪽만 레이스인 이유를 문서의 두 문장으로 말해 보라.

### 3. 플래그 폴링 — 여섯 칸 (예측)

```go
// t36poll.go
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
```

<!-- 기본 빌드(opt)와 -gcflags="-N -l" 빌드(noopt) 각각에서 global · ptr · field 를 timeout 2 로 돌리고, 칸마다 exit 와 「2초 안에 루프를 빠져나왔나」를 찍는다. 마지막 줄에 「끝나지 않은 칸 N / 6」. -->

- 여섯 칸의 결과와 마지막 줄의 수는?

### 4. 루프 안에 읽기가 있나 (예측)

<!-- 3번과 같은 소스. go build -gcflags=" -S" 와 -gcflags="-N -l -S" 로 각각 어셈블리를 받아 main.waitGlobal 의 명령 줄만 찍는다. -->

- 기본 빌드에서 `waitGlobal` 의 루프는 `main.done` 을 **매번** 읽나, **한 번** 읽고 도나? `-N -l` 에서는?

### 5. 값을 쓰고 깃발을 세우면 (예측)

```go
// t36pub.go
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
```

<!-- 보통 빌드로 20판 돌려 「"hello" 가 아닌 판(또는 안 끝난 판)이 있었나」를 찍고, 이어서 -race 빌드로 한 번 돌려 exit 와 보고 수를 찍는다. -->

- 20판의 참거짓은? `-race` 빌드의 종료 코드와 보고 수는?
- 문서는 이 모양에 대해 무엇을 **허용**하나?

### 6. 3번의 결과와 문서의 문장 (왜)

- 3번의 마지막 줄과 문서의 「**The loop in main is not guaranteed to finish.**」는 모순인가? 무엇이 그 둘을 가르나?

### 7. 고루틴이 끝났다는 것 (왜)

- 1번의 `goexit` 칸은 고루틴이 **확실히 끝난 뒤** 읽는데도 레이스다. 문서의 어느 문장인가? 끝남을 알리려면 무엇을 쓰나?

### 8. C 와 자바에서 같은 루프 (연결)

- C 32편에서 gcc `-O2`·clang 은 동기화 없는 대기 루프를 어떻게 만들었나? 자바 33편에서 JIT 는? 이 편의 3번과 무엇이 같고 무엇이 다른가?

### 9. 원자 연산은 누구와 같은 뜻인가 (연결)

- 메모리 모델 문서는 Go 의 원자 연산을 어느 두 언어의 무엇과 **같은 뜻**이라고 하나? C 의 `volatile` 은 그 자리에 올 수 있나?

### 10. 문서가 `-race` 를 부르는 문장 (경계)

- 문서는 ThreadSanitizer 구현이 레이스를 만나면 무엇을 「exactly」 한다고 적나? 35편에서 본 **기본 동작**과 한 칸 다른 곳은?

### 11. 문서의 첫 조언 (경계)

- 「If you must read the rest of this document …」 뒤의 두 마디는? 이 편의 13칸과 어떻게 이어지나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

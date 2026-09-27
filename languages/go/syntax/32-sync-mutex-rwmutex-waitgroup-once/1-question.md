# go/syntax/32 — `sync`: `Mutex`·`RWMutex`·`WaitGroup`·`Once` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ **모든 문제에서 「누가 이것을 잡아 주나 — 컴파일러·`vet`·`-race`·교착 탐지·아무도」를 먼저 적어라.**
> ★★ **「이것은 계약인가 도구의 휴리스틱인가」를 매번 물어라** — 「복사 금지」는 문서의 계약, 그것을 잡는 것은 `vet` 이다.
> 소스는 전부 `go build -trimpath -o prog .`(표시한 것은 `-race` 를 붙여) 로 빌드했다. 모듈 이름은 `ex` 다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 동기화 없는 `n++` (예측)

```go
// t32race.go
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
```

<!-- go build -race -trimpath -o prog . 후 stdout 만 받은 판과 stderr 만 받은 판을 따로 찍었다. 같은 파일에 go vet 도 돌렸다. -->

- stdout 에 무엇이 찍히고, 종료 코드는 몇인가?
- stderr 의 보고는 **어느 두 줄**(줄 번호)을 짚나? 각각 누가(어느 고루틴이) 읽고 썼나?
- 이 파일에 `go vet` 을 돌리면?

### 2. 복사 탐침 18개 (예측)

```go
// t32copy.go
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
```

<!-- go vet . 의 출력을 받고, 셸이 // pNN 주석의 줄 번호와 vet 줄의 줄 번호를 맞춰 탐침마다 답함/침묵을 찍는다. 마지막 줄에 답한 탐침 수 / 18. -->

- 18 개 중 몇 개가 답하나?
- 침묵하는 탐침을 전부 적고, 그중 **옳은 침묵**과 **놓친 것**을 갈라라.
- `WaitGroup`·`Once`·`atomic.Int64` 의 `vet` 문구는 `Mutex` 와 무엇이 다른가?
- 이 파일은 `go build` 로 빌드되나?

### 3. `wg.Add` 를 고루틴 안에서 (예측)

```go
// t32wgadd.go
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
```

<!-- go vet . 한 번, 그리고 -race 빌드를 20판 돌려 셸이 참거짓 셋을 찍는다: 100 이 아닌 판이 있었나 · -race 가 한 판이라도 보고했나 · 20판 모두 보고했나. -->

- `go vet` 은 무엇을 말하나?
- 참거짓 셋은 각각 무엇인가?
- `-race` 가 보고할 때, 짚는 프레임은 사용자 코드의 줄인가?

### 4. 같은 고루틴이 두 번 잠그면 (예측)

```go
// t32relock.go
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
```

- stderr 에 무엇이 찍히고 종료 코드는 몇인가? 상태 줄의 괄호 안에는?
- 자바에서 같은 스레드가 같은 `synchronized` 모니터에 다시 들어가면?

### 5. `RWMutex` — 쓰는 쪽이 끼면 (예측)

```go
// t32rw.go
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
```

<!-- 셸이 alone · writer 를 timeout 2 로 돌리고, 칸마다 「둘째 RLock」이 찍혔나 · exit · 교착 탐지를 찍는다. -->

- 두 칸 각각의 결과는?
- `writer` 칸이 교착이면 두 고루틴의 상태 줄은 각각 무엇인가?
- 이 함정이 **테스트에서 잘 안 걸리는** 이유는?

### 6. 잠근 채 패닉하면 (예측)

```go
// t32defer.go
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
```

<!-- ./prog defer && ./prog nodefer -->

- 두 줄의 `TryLock` 값은?
- `nodefer` 쪽에서 `TryLock` 대신 `Lock` 을 불렀다면?

### 7. `Once` 와 100 고루틴 (왜)

- 100 고루틴이 `once.Do` 를 부르면 초기화 함수는 몇 번 도나? 몇 고루틴이 준비된 값을 보나?
- `config` 에 락이 없는데도 경쟁이 아닌 이유를 문서의 한 구절로 말해 보라.
- `OnceValue` 를 두 번 부르면 함수는 몇 번 도나?

### 8. 주인 없는 락 · 안 잠근 락 (경계)

- main 이 잠근 `Mutex` 를 다른 고루틴이 풀 수 있나?
- 잠그지 않은 `Mutex` 를 `Unlock` 하면? 그것은 `defer` 안의 `recover` 가 받을 수 있나?

### 9. 다른 언어와 (연결)

- Rust 에서 `Mutex<i32>` 를 잠그지 않고 `*m += 1` 하면? 그것이 말해 주는 Go 와의 차이는?
- C++ 에서 `std::mutex` 를 품은 구조체를 복사하면? Go 에서는 누가 막나?
- C++ 의 `lock_guard` 자리를 Go 에서는 무엇이 맡나 — 무엇이 다른가?

### 10. 채널이냐 뮤텍스냐 (경계)

- 「값을 넘긴다」와 「한 자리를 번갈아 고친다」 — 각각 무엇을 고르나?
- 여럿에게 「끝났다」를 한 번에 알리려면?
- 「채널이 느리니 뮤텍스」 — 이 문서가 그 판단을 해 주나?

### 11. 계약과 도구 (왜)

- 「`Mutex` 를 복사하지 마라」는 명세·라이브러리 계약·도구 중 어디에 적혀 있고, 누가 지켜 주나?
- `-race` 가 조용했다는 것은 무엇을 말하고 무엇을 말하지 **않나**?
- `-race` 창이 **안 열리는** 조건은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

# go/syntax/35 — 데이터 레이스와 `-race` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ **모든 문제에서 「두 접근 사이에 순서를 세우는 것이 있나」와 「검출기가 그 접근을 볼 수 있나」를 따로 적어라.**
> ★★ **「실행 안 됨 · 못 봄 · 볼 것이 없음」을 가르라.**
> Go 소스는 전부 `go build -race -trimpath -o prog .` 로 빌드했다. 모듈 이름은 `ex` 다. 레이스를 만드는 최소 코드는 [32번 주제](../32-sync-mutex-rwmutex-waitgroup-once/) 1번 문제다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 여덟 칸 (예측)

```go
// t35grid.go
package main

/*
#include <stdlib.h>
static void inc(int *p) { (*p)++; }
*/
import "C"

import (
	"fmt"
	"os"
	"runtime"
	"sync"
	"sync/atomic"
	"time"
	"unsafe"
)

var n int

// 경쟁하는 두 접근 — 고루틴이 쓰고 main 이 읽는다. 둘 사이에 동기화가 없다.
func race() {
	done := make(chan struct{})
	go func() {
		n++
		close(done)
	}()
	fmt.Println("n =", n)
	<-done
}

func main() {
	switch os.Args[1] {
	case "ran":
		race()
	case "notran":
		if len(os.Args) > 2 { // 인자가 둘일 때만 — 이 칸에서는 안 들어간다
			race()
		}
	case "apart":
		go func() { n = 1 }()
		time.Sleep(300 * time.Millisecond) // 쓰기는 이미 끝났다 — 시간상 겹치지 않는다
		fmt.Println("n =", n)
	case "many":
		const alive = 100_000
		var started atomic.Int64
		release := make(chan struct{})
		var wg sync.WaitGroup
		for range alive {
			wg.Go(func() {
				started.Add(1)
				<-release
			})
		}
		for started.Load() < alive {
			runtime.Gosched()
		}
		fmt.Println("동시에 살아 있는 고루틴:", runtime.NumGoroutine())
		race()
		close(release)
		wg.Wait()
	case "mixed":
		var x int64
		done := make(chan struct{})
		go func() {
			atomic.AddInt64(&x, 1) // 쓰는 쪽만 원자
			close(done)
		}()
		fmt.Println("x =", x) // 읽는 쪽은 평범한 읽기
		<-done
	case "goOnC", "cOnC", "cOnGo":
		var goInt C.int
		cp := (*C.int)(C.malloc(C.size_t(unsafe.Sizeof(C.int(0)))))
		*cp = 0
		var wg sync.WaitGroup
		for range 2 {
			wg.Go(func() {
				for range 1000 {
					switch os.Args[1] {
					case "goOnC":
						*cp++ // Go 코드가 C 메모리를
					case "cOnC":
						C.inc(cp) // C 코드가 C 메모리를
					case "cOnGo":
						C.inc(&goInt) // C 코드가 Go 메모리를
					}
				}
			})
		}
		wg.Wait()
		C.free(unsafe.Pointer(cp))
		fmt.Println(os.Args[1], "끝")
	}
}
```

<!-- 셸이 여덟 칸을 차례로 돌려 칸마다 「경쟁 접근이 실행됐나」(설계로 정한 값) · exit · -race 보고 예/아니오를 찍는다. many 칸은 첫 줄도 붙인다. 마지막 줄에 「경쟁이 실행됐는데 보고가 없던 칸 N / M」. -->

- 칸마다 `-race 보고` 는 예인가 아니오인가?
- 마지막 줄의 수는? 분모에서 빠지는 칸은 무엇이고, 왜 빠지나?
- `many` 칸의 첫 줄은?

### 2. 300ms 떨어진 두 접근 (왜)

- `apart` 칸은 쓰기가 **끝난 뒤 300ms** 에 읽는다. 검출기는 이것을 어떻게 판정하고, 그 근거가 되는 보고의 한 줄은?

### 3. 같은 자리 1000 번 · 멈춤 · 종료 코드 (예측)

```go
// t35gorace.go
package main

import (
	"fmt"
	"os"
)

var a, b int

func touch(p *int) {
	done := make(chan struct{})
	go func() {
		*p = 1
		close(done)
	}()
	_ = *p
	<-done
}

func main() {
	for range 1000 {
		touch(&a) // 같은 자리의 경쟁을 1000 번
	}
	fmt.Fprintln(os.Stderr, "--- 첫 자리를 지났다")
	touch(&b) // 다른 자리의 경쟁 한 번
	fmt.Fprintln(os.Stderr, "--- main 의 끝에 닿았다")
}
```

<!-- -race 빌드 뒤 GORACE 를 "" · halt_on_error=1 · exitcode=3 으로 바꿔 세 번 돌리고, 판마다 exit 와 stderr 의 --- · Found · WARNING 줄만 찍는다. -->

- 세 판 각각의 종료 코드와 `Found N data race(s)` 의 N 은?
- `halt_on_error=1` 판에는 어느 마커가 빠지나?

### 4. 고루틴 8128 개 (경계)

- 「`-race` 는 8128 개 넘는 고루틴을 살려 두면 죽는다」 — 이 판에서 맞나? 무엇이 그 답의 근거인가? 그 문구는 이 판의 어디에 남아 있나?

### 5. 같은 레이스를 Rust 로 — 스코프 스레드 (예측)

```rust
// t35scope.rs
use std::thread;

fn main() {
    let mut n = 0;
    thread::scope(|s| {
        s.spawn(|| {
            n += 1;
        });
        println!("n = {}", n);
    });
}
```

- `rustc` 는 무엇을 말하나(에러 코드와 한 줄)?

### 6. 같은 레이스를 Rust 로 — `Rc` 로 우회 (예측)

```rust
// t35rc.rs
use std::cell::Cell;
use std::rc::Rc;
use std::thread;

fn main() {
    let n = Rc::new(Cell::new(0));
    let m = Rc::clone(&n);
    let h = thread::spawn(move || {
        m.set(m.get() + 1);
    });
    println!("n = {}", n.get());
    h.join().unwrap();
}
```

- `rustc` 는 무엇을 말하나? 어느 트레잇이 빠졌다고 하나?

### 7. cgo 칸 셋 (왜)

- `goOnC` 는 **Go 코드**가 쓰는데도 조용했다. `cOnGo` 는 **Go 메모리**인데도 조용했다. 둘을 한 문장으로 묶으면 검출기는 무엇만 보나?

### 8. 「거짓 양성이 없다」 (경계)

- Data Race Detector 글이 그렇게 **보장**하나? 이 배치가 그 방향에 대해 가진 근거는 무엇이고, 그것은 보장인가 관찰인가?

### 9. `vet` 과 `-race` (연결)

- 32편의 최소 레이스에서 `go vet` 은 무엇을 했나? 32편의 `WaitGroup.Add` 20판은 이 편의 어느 성질의 첫 증거인가?

### 10. 비용 (경계)

- 「`-race` 는 메모리 5-10배, 시간 2-20배」 — 이 문서가 잰 값인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

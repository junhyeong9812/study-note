# go/syntax/35 — 데이터 레이스와 `-race` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★ **근거로 읽을 칸** — 격자의 `-race 보고=예/아니오` · `3 / 7` · `100001` · `Found 2` · `GORACE` 판의 종료 코드 · 보고의 줄 번호와 `(finished)` · rustc 진단.
> **근거로 읽지 않을 칸** — 주소 · `goroutine N`/`Goroutine N` 의 N(머리말의 정규화 칸) · cgo 칸에서 잃은 값(안 실었다).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `ran`·`apart`·`many`·`mixed` 는 예 · 나머지 넷은 아니오 · `3 / 7`(분모에서 `notran`) · `100001`

**출력**

```text
===== 소스: t35grid.go =====
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
===== 명령: go build -race -trimpath -o prog . && miss=0; m=0; for c in ran notran apart many mixed goOnC cOnC cOnGo; do ./prog $c >out.txt 2>err.txt; rc=$?; rep=아니오; grep -q "DATA RACE" err.txt && rep=예; case $c in notran) ran=아니오 ;; *) ran=예 ;; esac; if [ $ran = 예 ]; then m=$((m+1)); [ $rep = 아니오 ] && miss=$((miss+1)); fi; extra=; [ $c = many ] && extra=" · $(sed -n 1p out.txt)"; echo "[$c] 경쟁 접근이 실행됐나=$ran · exit=$rc · -race 보고=$rep$extra"; done; echo "경쟁이 실행됐는데 보고가 없던 칸 $miss / $m" =====
[ran] 경쟁 접근이 실행됐나=예 · exit=66 · -race 보고=예
[notran] 경쟁 접근이 실행됐나=아니오 · exit=0 · -race 보고=아니오
[apart] 경쟁 접근이 실행됐나=예 · exit=66 · -race 보고=예
[many] 경쟁 접근이 실행됐나=예 · exit=66 · -race 보고=예 · 동시에 살아 있는 고루틴: 100001
[mixed] 경쟁 접근이 실행됐나=예 · exit=66 · -race 보고=예
[goOnC] 경쟁 접근이 실행됐나=예 · exit=0 · -race 보고=아니오
[cOnC] 경쟁 접근이 실행됐나=예 · exit=0 · -race 보고=아니오
[cOnGo] 경쟁 접근이 실행됐나=예 · exit=0 · -race 보고=아니오
경쟁이 실행됐는데 보고가 없던 칸 3 / 7
(exit 0)
```

**왜 그런가**

- ★★★ **보고 — `ran`·`apart`·`many`·`mixed`, exit 66.** **침묵 — `notran`·`goOnC`·`cOnC`·`cOnGo`, exit 0.**
- ★★★ **`경쟁이 실행됐는데 보고가 없던 칸 3 / 7`** — 셋 다 **cgo 칸**이다.
- ★★★ **`notran` 은 분모 밖** — 그 칸에서는 `race()` 가 **실행되지 않았다.** 경쟁이 **없었으니** 못 본 것이 아니라 **볼 것이 없었다.** 문서 「**it can't find races in code paths that are not executed**」 — 테스트가 그 분기를 안 지나면 영원히 모른다.
- ★★ **`many` — `동시에 살아 있는 고루틴: 100001`** 에서도 보고했다(4번).
- ★★ **`mixed`** — 원자로 쓰고 평범하게 읽으면 레이스다([33번 주제](../33-sync-atomic-and-sync-map/) (2)절).

### 2. 「동시에」가 아니라 「순서가 있나」 · `Goroutine N (finished) created at`

```text
===== 소스: t35grid.go =====
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
===== 명령: go build -race -trimpath -o prog . && ./prog apart 2>&1 >/dev/null =====
==================
WARNING: DATA RACE
Read at 0x00000153a738 by main goroutine:
  main.main()
      ex/t35grid.go:43 +0x1ee

Previous write at 0x00000153a738 by goroutine 8:
  main.main.func1()
      ex/t35grid.go:41 +0x24

Goroutine 8 (finished) created at:
  main.main()
      ex/t35grid.go:41 +0x19b
==================
Found 1 data race(s)
(exit 66)
```

- ★★★ 쓴 고루틴은 **이미 끝났다**(`(finished)`). 그래도 `Read at … by main goroutine` · `Previous write at … by goroutine N` 으로 잡았다.
- ★★★ 두 접근 사이에 **happens-before 가 없으면** 시간이 얼마나 떨어졌든 레이스다. `time.Sleep` 은 순서를 **안 만든다** — 무엇이 만드나는 [36번 주제](../36-reading-the-go-memory-model-in-code/) (2)절의 13칸.

### 3. 66·`2` · 66·(Found 없음) · 3·`2` — `halt_on_error=1` 판에는 두 마커가 다 빠진다

**출력**

```text
===== 소스: t35gorace.go =====
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
===== 명령: go build -race -trimpath -o prog . && for g in "" halt_on_error=1 exitcode=3; do GORACE=$g ./prog 2>err.txt; rc=$?; echo "[GORACE=$g] exit=$rc"; grep -E "^(---|Found|WARNING)" err.txt; done =====
[GORACE=] exit=66
WARNING: DATA RACE
--- 첫 자리를 지났다
WARNING: DATA RACE
--- main 의 끝에 닿았다
Found 2 data race(s)
[GORACE=halt_on_error=1] exit=66
WARNING: DATA RACE
[GORACE=exitcode=3] exit=3
WARNING: DATA RACE
--- 첫 자리를 지났다
WARNING: DATA RACE
--- main 의 끝에 닿았다
Found 2 data race(s)
(exit 0)
```

**왜 그런가**

- ★★★ **기본 — exit 66, `Found 2 data race(s)`** — `touch(&a)` **1000 번**에 보고는 **한 건**, `touch(&b)` 한 건. **보고 수는 레이스 횟수가 아니다.** 프로그램은 끝까지 돌았다.
- ★★★ **`halt_on_error=1` — exit 66, 첫 `WARNING` 뒤 `--- 첫 자리를 지났다` 도 `--- main 의 끝에 닿았다` 도 없다.** 첫 보고에서 멈췄다(`Found` 줄도 없다).
- ★★ **`exitcode=3` — exit 3**, 나머지는 기본과 같다. 66 은 기본값일 뿐이다.

### 4. 아니다 — 1.19 부터 한계 없음 · 100001 에서 보고 · 문구는 `.syso` 안에

```text
===== 명령: echo "GOAMD64=$(go env GOAMD64)"; strings "$(go env GOROOT)/src/runtime/race/internal/amd64v1/race_linux.syso" | grep "simultaneously alive" =====
GOAMD64=v1
race: limit on %u simultaneously alive goroutines is exceeded, dying
(exit 0)
```

- ★★★ 1번 `many` 칸 — **100001 고루틴이 살아 있는 채로 레이스를 보고**했다. 죽지 않았다.
- ★★★ Go 1.19 릴리스 노트(웹) — 「**… thread sanitizer version v3 … it supports an unlimited number of goroutines.**」
- ★★ 그런데 **`race: limit on %u simultaneously alive goroutines is exceeded, dying`** 문구는 이 판의 검출기 바이너리(`amd64v1/race_linux.syso` — `GOAMD64=v1`)에 **남아 있다.** `%u` 자리의 값은 **문자열에 없다** — 8128 이라는 값은 이 판에서 **확인 못 했다.**

### 5. ``E0502 — cannot borrow `n` as immutable because it is also borrowed as mutable``

**출력**

```text
===== 명령: rustc --version =====
rustc 1.92.0 (ded5c06cf 2025-12-08)
(exit 0)
```

```text
===== 소스: t35scope.rs =====
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
===== 명령: rustc --edition 2024 -o prog t35scope.rs =====
error[E0502]: cannot borrow `n` as immutable because it is also borrowed as mutable
 --> t35scope.rs:9:28
  |
5 |       thread::scope(|s| {
  |                      - has type `&'1 Scope<'1, '_>`
6 |           s.spawn(|| {
  |           -       -- mutable borrow occurs here
  |  _________|
  | |
7 | |             n += 1;
  | |             - first borrow occurs due to use of `n` in closure
8 | |         });
  | |__________- argument requires that `n` is borrowed for `'1`
9 |           println!("n = {}", n);
  |                              ^ immutable borrow occurs here
  |
note: requirement that the value outlives `'1` introduced here
 --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/std/src/thread/scoped.rs:196:35
  = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0502`.
(exit 1)
```

**왜 그런가**

- ★★★ 새 스레드의 클로저가 `n` 을 **가변으로 빌려 간 동안** main 이 **읽으려** 했다. 빌림 규칙(**가변 하나 XOR 공유 여럿**)이 **순서 없는 쓰기·읽기의 공존**을 **컴파일에서** 거부한다.
- ★★ Go 는 같은 모양이 **컴파일되고**, 실행해서 `-race` 로 찾는다(32편 1번).

### 6. ``E0277 — `Rc<Cell<i32>>` cannot be sent between threads safely`` · `Send`

**출력**

```text
===== 소스: t35rc.rs =====
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
===== 명령: rustc --edition 2024 -o prog t35rc.rs =====
error[E0277]: `Rc<Cell<i32>>` cannot be sent between threads safely
  --> t35rc.rs:8:27
   |
 8 |       let h = thread::spawn(move || {
   |               ------------- ^------
   |               |             |
   |  _____________|_____________within this `{closure@t35rc.rs:8:27: 8:34}`
   | |             |
   | |             required by a bound introduced by this call
 9 | |         m.set(m.get() + 1);
10 | |     });
   | |_____^ `Rc<Cell<i32>>` cannot be sent between threads safely
   |
   = help: within `{closure@t35rc.rs:8:27: 8:34}`, the trait `Send` is not implemented for `Rc<Cell<i32>>`
note: required because it's used within this closure
  --> t35rc.rs:8:27
   |
 8 |     let h = thread::spawn(move || {
   |                           ^^^^^^^
note: required by a bound in `spawn`
  --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/std/src/thread/mod.rs:725:1

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0277`.
(exit 1)
```

**왜 그런가**

- ★★★ 「**the trait `Send` is not implemented for `Rc<Cell<i32>>`**」 — 스레드 경계를 넘는 값은 **`Send`** 여야 하고, 원자적이지 않은 계수를 가진 `Rc` 는 아니다.
- ★★★ **Go 에는 `Send` 같은 표지가 없다** — 어떤 값이든 고루틴이 잡고 채널로 넘긴다. 그래서 검사는 **실행 중**(`-race`)이고, 1번의 **실행 안 된 경로 · cgo 쪽**이 사각지대가 된다.

### 7. 「**Go 코드가 한 접근 중 Go 메모리에 대한 것**」만 본다

- ★★★ `goOnC` — 접근은 Go 코드인데 **메모리가 `C.malloc` 의 것**이라 안 봤다. `cOnGo` — 메모리는 Go 것인데 **접근이 C 함수**라 안 봤다. `cOnC` 는 둘 다 C 쪽.
- ★★ 셋 다 탐색 실행에서 **증가를 잃었다** — 레이스는 실제로 있었다. 그 수는 흔들려서 안 실었다.
- ★ 이 한 문장은 **이 판의 관찰**이다 — 검출기의 주소 범위 판정 코드는 **안 열었다.**
- 그래서 cgo 경계의 공유 메모리는 **Go 쪽 `Mutex`** 로 지킨다.

### 8. 보장하지 않는다(글에 그 문장이 없다) · 36편의 침묵 9칸 — 관찰

- ★★★ 이번에 웹에서 연 **Data Race Detector 글에는 「false positive」 라는 말도, 「보고는 늘 진짜다」 라는 주장도 없다.** 브리핑의 전제였고, 그래서 **제3의 상태**(못 잰 것)로 둔다.
- ★★ 이 배치의 근거는 [36번 주제](../36-reading-the-go-memory-model-in-code/) (2)절 — **메모리 모델이 순서를 약속한 9칸에서 전부 침묵**했다. **관찰**이다.

### 9. 침묵했다 · 「실행된 인터리빙만 본다」

- ★★★ [32번 주제](../32-sync-mutex-rwmutex-waitgroup-once/) 1번 — **`vet exit=0`, 한 줄도 없다.** 레이스는 **실행해야** 보인다.
- ★★★ 32편 3번 — 같은 바이너리가 **20판 중 어떤 판만** 보고했다. **순서가 실제로 어긋난 판**만 본다는 것 — 이 편 1번 `notran` 은 그 극단(한 번도 안 지나간 경로)이다.

### 10. 아니다 — 문서의 수치다

- ★★★ Data Race Detector 글 — 「**memory usage may increase by 5-10x and execution time by 2-20x**」. **이 배치는 재지 않았다.**

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 로 **★고칠 것 0** |
| ★★★ 격자 (`t35grid`) | `-race` 빌드 · cgo(gcc) · 여덟 칸 | 캡처마다 | **`3 / 7`** — 매번 같다 |
| ★★ 보고 전문 (`t35apart`) | stderr 만 | 캡처마다 | `(finished)` · 41·43행 |
| ★★ `GORACE` (`t35gorace`) | 세 판 | 캡처마다 | 66·66·3 · `Found 2` |
| ★★ 검출기 판별 (`t35syso`·`t35readme`) | `strings` · README | 1 | ThreadSanitizer 기반 · 옛 문구 남음 |
| ★★ Rust 대비 (`t35scope`·`t35rc`) | `rustc 1.92.0` | 캡처마다 | `E0502` · `E0277` |
| 문서(웹) | Data Race Detector · Go 1.19 릴리스 노트 | 1 | 인용한 문장 · 「false positive」 없음 |

**구현·환경에 달린 항목**

| 항목 | 무엇에 달렸나 |
|---|---|
| `-race` 창 | **cgo + gcc**(32편 판별) |
| cgo 칸의 침묵 | **이 판 검출기(ThreadSanitizer 기반)** |
| 같은 자리 한 번 보고 | **이 판 검출기** |
| 고루틴 수 한계 없음 | **v3 검출기**(1.19 부터) — `windows/amd64`·`openbsd/amd64` 는 **못 잰다** |
| 주소 · 고루틴 id | **흔들린다** — 정규화 규칙 `([Gg]oroutine) \d+` + 기본 넷 |
| 검출기 비용 | ★ **안 쟀다** |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다.

# go/syntax/28 — 고루틴: `go` 문·시작 비용·종료 조건 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> 판 경계를 보이는 블록은 **`===== 소스: go.mod =====` 까지** 싣는다.
> ★ **근거로 읽을 칸** — 셸이 찍은 **참거짓** · `NumGoroutine` 의 수 · 판 격자의 **가짓수** · 컴파일 진단 · 종료 코드.
> **근거로 읽지 않을 칸** — 없다. 흔들리는 값(끊긴 줄 수·도착 순서·`StackInuse` 절댓값)은 **블록에 들어가기 전에 참거짓·가짓수로 접었다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 종료 코드 0 · `main 끝` 만 찍힌다 · `defer` 도 안 돈다

**출력**

```text
===== 소스: t28a.go =====
package main

import (
	"fmt"
	"time"
)

func main() {
	go func() {
		defer fmt.Println("[고루틴 defer] 돌았다")
		for i := 1; i <= 1000; i++ {
			fmt.Println("고루틴", i)
			time.Sleep(time.Millisecond)
		}
		fmt.Println("고루틴 끝")
	}()
	time.Sleep(20 * time.Millisecond)
	fmt.Println("main 끝")
}
===== 명령: go build -trimpath -o prog . && ./prog > out.txt; echo "prog exit=$?"; echo "main 끝 이 찍혔나        : $(grep -qx "main 끝" out.txt && echo 예 || echo 아니오)"; echo "고루틴 끝 이 찍혔나      : $(grep -qx "고루틴 끝" out.txt && echo 예 || echo 아니오)"; echo "고루틴 defer 가 돌았나   : $(grep -q "고루틴 defer" out.txt && echo 예 || echo 아니오)"; echo "고루틴 줄이 1000 미만인가: $([ "$(grep -c "^고루틴 [0-9]" out.txt)" -lt 1000 ] && echo 예 || echo 아니오)" =====
prog exit=0
main 끝 이 찍혔나        : 예
고루틴 끝 이 찍혔나      : 아니오
고루틴 defer 가 돌았나   : 아니오
고루틴 줄이 1000 미만인가: 예
(exit 0)
```

**왜 그런가**

- ★★★ **종료 코드 0**, `main 끝` **예**, `고루틴 끝` **아니오**, `[고루틴 defer]` **아니오**, 줄 수 1000 미만 **예**.
- ★★★ 명세 — 「**When that function invocation returns, the program exits. It does not wait for other (non-main) goroutines to complete.**」
  다른 고루틴은 **되감기도 없이** 사라진다 — 그래서 `defer` 가 안 돈다.
- ★ 싣지 않은 값 — **몇 줄에서 끊겼나.** 스케줄링과 시간에 달려 실행마다 다르다. 「**끝까지 안 갔다**」 로 바꿔 물으면 안 흔들린다.

### 2. 1 · 101 · true · 11 · false

**출력**

```text
===== 소스: t28b.go =====
package main

import (
	"fmt"
	"runtime"
	"sync"
	"time"
)

// settle 은 NumGoroutine 이 want 가 될 때까지 최대 1초 기다린다.
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
	fmt.Println("시작                     :", runtime.NumGoroutine())

	release := make(chan struct{})
	var wg sync.WaitGroup
	for range 100 {
		wg.Go(func() { <-release }) // 1.25 의 WaitGroup.Go
	}
	fmt.Println("100개 띄운 직후          :", runtime.NumGoroutine())
	close(release)
	wg.Wait()
	fmt.Println("Wait 뒤 1 로 돌아왔나    :", settle(1))

	stuck := make(chan struct{}) // 아무도 안 닫는다
	for range 10 {
		go func() { <-stuck }()
	}
	fmt.Println("받을 쪽 없는 10개 뒤     :", runtime.NumGoroutine())
	fmt.Println("1초 기다리면 1 로 가나   :", settle(1))
}
===== 명령: go build -trimpath -o prog . && ./prog =====
시작                     : 1
100개 띄운 직후          : 101
Wait 뒤 1 로 돌아왔나    : true
받을 쪽 없는 10개 뒤     : 11
1초 기다리면 1 로 가나   : false
(exit 0)
```

**왜 그런가**

- ★★ **시작 1**(main) · **띄운 직후 101**(막혀 있어도 센다 — 「currently exist」) · **Wait 뒤 1 로 돌아옴** · **받을 쪽 없는 10개 뒤 11** · **1초 기다려도 1 이 아님**.
- ★★ `settle` 을 쓴 이유 — `Done` 을 부른 뒤 고루틴이 **실제로 사라지기까지 틈**이 있다. `Wait` 직후 바로 1 이라는 **보장이 없다.**
- ★★★ 마지막 `false` — **고루틴 누수**. 아무도 안 닫는 채널에서 영원히 막혀 있다. 정본은 [목록의 **31번 주제**](../31-goroutine-leaks/).

### 3. `1)` 아래 · main 고루틴에서 · A 는 1, B 는 2

**출력**

```text
===== 소스: t28c.go =====
package main

import "fmt"

func val(tag string, v int) int {
	fmt.Printf("    [평가] %s = %d\n", tag, v)
	return v
}

func show(tag string, v int, ready <-chan struct{}, done chan<- struct{}) {
	<-ready
	fmt.Printf("    [실행] %s 가 받은 값 = %d\n", tag, v)
	close(done)
}

func main() {
	x := 1
	readyA, doneA := make(chan struct{}), make(chan struct{})
	readyB, doneB := make(chan struct{}), make(chan struct{})

	fmt.Println("1) go show(\"A\", val(\"x\", x), …) 를 적는다")
	go show("A", val("x", x), readyA, doneA)

	fmt.Println("2) go func() { … val(\"x\", x) … }() 를 적는다")
	go func() {
		<-readyB
		fmt.Printf("    [실행] B 가 읽은 값 = %d\n", val("x", x))
		close(doneB)
	}()

	x = 2
	fmt.Println("3) x = 2 로 바꾸고 A, B 를 차례로 풀어 준다")
	close(readyA)
	<-doneA
	close(readyB)
	<-doneB
}
===== 명령: go build -trimpath -o prog . && ./prog =====
1) go show("A", val("x", x), …) 를 적는다
    [평가] x = 1
2) go func() { … val("x", x) … }() 를 적는다
3) x = 2 로 바꾸고 A, B 를 차례로 풀어 준다
    [실행] A 가 받은 값 = 1
    [평가] x = 2
    [실행] B 가 읽은 값 = 2
(exit 0)
```

**왜 그런가**

- ★★★ `[평가] x = 1` 은 **`1)` 바로 아래** — `go` 문을 지나는 순간 **부르는 쪽(main) 고루틴에서** 평가됐다.
  명세 「**evaluated as usual in the calling goroutine**」. A 는 **1**.
- ★★ B 는 리터럴 몸통에서 **풀려난 뒤** 읽어 **2**. ([26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/) (1)절과 같은 모양.)
- ★ 순서가 안 흔들리는 이유 — A 를 풀고 **`<-doneA` 로 끝나길 기다린 뒤** B 를 풀었다. 채널이 순서를 세운다.

### 4. `200 [3 3 3]` 대 `200 [0 1 2]` — 가짓수 각각 1

**출력**

```text
===== 소스: go.mod =====
module ex

go 1.21
===== 소스: t28d.go =====
package main

import (
	"fmt"
	"slices"
)

func main() {
	start := make(chan struct{})
	out := make(chan int, 3)
	for i := 0; i < 3; i++ {
		go func() {
			<-start // 루프가 다 끝난 뒤에 읽게 한다 — 경쟁이 아니라 판의 의미만 남긴다
			out <- i
		}()
	}
	close(start)
	got := []int{<-out, <-out, <-out}
	slices.Sort(got) // 도착 순서는 흔들리므로 정렬한다
	fmt.Println(got)
}
===== 명령: go build -trimpath -o prog . && for n in $(seq 200); do ./prog; done | sort | uniq -c =====
    200 [3 3 3]
(exit 0)
```

```text
===== 소스: go.mod =====
module ex

go 1.22
===== 소스: t28d.go =====
package main

import (
	"fmt"
	"slices"
)

func main() {
	start := make(chan struct{})
	out := make(chan int, 3)
	for i := 0; i < 3; i++ {
		go func() {
			<-start // 루프가 다 끝난 뒤에 읽게 한다 — 경쟁이 아니라 판의 의미만 남긴다
			out <- i
		}()
	}
	close(start)
	got := []int{<-out, <-out, <-out}
	slices.Sort(got) // 도착 순서는 흔들리므로 정렬한다
	fmt.Println(got)
}
===== 명령: go build -trimpath -o prog . && for n in $(seq 200); do ./prog; done | sort | uniq -c =====
    200 [0 1 2]
(exit 0)
```

**왜 그런가**

- ★★★ **`go 1.21` → 1가지 `[3 3 3]`, `go 1.22` → 1가지 `[0 1 2]`.** 소스·툴체인·명령이 같고 **`go.mod` 한 줄**만 다르다.
- ★★ `<-start` 를 빼면 1.21 판은 **데이터 경쟁**이 된다 — 고루틴이 루프가 `i` 를 바꾸는 도중에 읽으니 가짓수가 **흔들린다.** 그것은 [목록의 **35번 주제**](../35-data-races-and-the-race-detector/)(레이스)의 일이다.
  `start` 를 두면 `close(start)` 가 루프 **뒤**라 `i` 는 **3** 이고, 채널이 순서를 세워 경쟁이 아니다.
- ★ 정렬한 이유 — **도착 순서는 흔들린다**(규칙 11). 정렬하면 판의 의미만 남는다.

### 5. 2048 · 구현 · `adaptivestackstart = 1`

```text
===== 명령: sed -n "77,78p" "$(go env GOROOT)/src/runtime/stack.go"; sed -n "1415,1419p" "$(go env GOROOT)/src/runtime/stack.go"; grep -n "debug.adaptivestackstart = 1" "$(go env GOROOT)/src/runtime/runtime1.go" =====
	// The minimum size of stack used by Go code
	stackMin = 2048
// startingStackSize is the amount of stack that new goroutines start with.
// It is a power of 2, and between fixedStack and maxstacksize, inclusive.
// startingStackSize is updated every GC by tracking the average size of
// stacks scanned during the GC.
var startingStackSize uint32 = fixedStack
397:	debug.adaptivestackstart = 1 // set this to 0 to turn larger initial goroutine stacks off
(exit 0)
```

- ★★ **`stackMin = 2048`** — **런타임 소스의 구현 상수**다. 명세에는 스택 크기라는 말이 없다.
- ★★★ 틀리는 이유 — `startingStackSize` 는 「**updated every GC by tracking the average size of stacks scanned during the GC**」이고
  **`debug.adaptivestackstart = 1`** 이 기본이다. **시작 크기가 움직인다** — `stackMin` 은 바닥이다.
- ★★ 격자가 말하는 것 — **고루틴당 `StackInuse` 증분이 2KB 자릿수**(1024 이상 4096 미만, 스위치 0/1 × 1000/10000 네 칸 전부).
  **말하지 않는 것** — ① 절댓값(흔들린다) ② 스위치가 효과 없다는 것(이 프로그램은 GC 로 평균을 키울 조건을 안 만들었다) ③ 「**고루틴은 싸다**」(견줄 대상이 없다 — 그 논증은 [`언어-특성/README.md`](../../언어-특성/README.md) §2) ④ 시간(안 쟀다).

```text
===== 소스: t28e.go =====
package main

import (
	"fmt"
	"runtime"
)

// 막힌 고루틴 n 개를 만들고 StackInuse 증분을 n 으로 나눈다.
// 절댓값은 흔들리므로 「2KB 자릿수인가」만 찍는다.
func main() {
	for _, n := range []int{1000, 10000} {
		var a, b runtime.MemStats
		runtime.GC()
		runtime.ReadMemStats(&a)
		stop := make(chan struct{})
		for range n {
			go func() { <-stop }()
		}
		runtime.ReadMemStats(&b)
		per := (b.StackInuse - a.StackInuse) / uint64(n)
		fmt.Printf("  N=%-5d 고루틴당 StackInuse 증분이 1024 이상 4096 미만인가 : %v\n",
			n, per >= 1024 && per < 4096)
		close(stop)
	}
}
===== 명령: go build -trimpath -o prog . && for g in 0 1; do echo "GODEBUG=adaptivestackstart=$g"; GODEBUG=adaptivestackstart=$g ./prog; done =====
GODEBUG=adaptivestackstart=0
  N=1000  고루틴당 StackInuse 증분이 1024 이상 4096 미만인가 : true
  N=10000 고루틴당 StackInuse 증분이 1024 이상 4096 미만인가 : true
GODEBUG=adaptivestackstart=1
  N=1000  고루틴당 StackInuse 증분이 1024 이상 4096 미만인가 : true
  N=10000 고루틴당 StackInuse 증분이 1024 이상 4096 미만인가 : true
(exit 0)
```

### 6. 다섯 줄 · 반환값은 버려진다

**출력**

```text
===== 소스: t28bad.go =====
package main

func f() int { return 1 }

func main() {
	s := []int{1}
	go len(s)
	go (f())
	go f
	defer f
	defer len(s)
	go f() // 이 줄은 된다 — 반환값은 버려진다
}
===== 명령: go build -trimpath -gcflags=-e -o prog . =====
# ex
./t28bad.go:7:5: go discards result of len(s) (value of type int)
./t28bad.go:8:5: expression in go must not be parenthesized
./t28bad.go:9:5: expression in go must be function call
./t28bad.go:10:8: expression in defer must be function call
./t28bad.go:11:8: defer discards result of len(s) (value of type int)
(exit 1)
```

**왜 그런가**

- ★★ 다섯 줄 — `go len(s)`(결과를 버리는 내장 함수) · `go (f())`(괄호) · `go f`(호출 아님) · `defer f`(호출 아님) · `defer len(s)`(내장 함수 결과).
- ★★★ `go f()` 는 통과 — 명세 「**If the function has any return values, they are discarded when the function completes.**」
  **결과는 채널로** 받는다([목록의 **29번 주제**](../29-channels-buffering-direction-close-range-and-nil/)).

### 7. 「함수 값과 인자는 지금」이 같고, 「언제 도나」가 다르다

- ★★★ 같은 부분 — **「the function value and parameters … are evaluated as usual」.** 두 문 모두 **그 자리에서** 평가해 저장한다.
- ★★ 다른 부분 — `defer` 는 **둘러싼 함수가 끝날 때**(LIFO), `go` 는 **새 고루틴에서 스케줄러가 돌릴 때**(부르는 쪽은 안 기다린다).
- ★★ `main` 반환과 `os.Exit` — **둘 다 다른 것의 `defer` 를 버린다.** `os.Exit` 는 **자기 고루틴의 `defer` 까지**([26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/) (6)절), `main` 반환은 **다른 고루틴들의 `defer`** 를(이 문서 (1)절).

### 8. 명세 · 구현 · 명세(판 의존, `go.mod`)

- ★★★ `main` 반환 규칙 — **명세**(`Program execution`).
- ★★ 고루틴 id · 스케줄링 순서 · 스택 크기 — **구현**(runtime). 그래서 흔들리고, 그래서 싣지 않았다.
- ★★ 루프 변수 1.22 — **명세(언어 판 의존)**. **`go.mod` 의 `go` 줄**이 그 모듈의 언어 판을 고른다(컴파일러 `-lang`).

### 9. `WaitGroup`(1.25 `Go`) · 채널 · 그 고루틴 안 · `NumGoroutine` 수렴

- ★★ 기다리기 — **`sync.WaitGroup`**, 1.25 부터 **`wg.Go(func)`**(`api/go1.25.txt:96`). 문서 「**The function f must not panic.**」
- ★★ 결과값 — `go` 는 **반환값을 버린다.** **채널**로 받는다.
- ★★ 패닉 — **그 고루틴의 첫 줄에 `defer`/`recover`.** 다른 고루틴(main 포함)은 못 잡는다([27번 주제](../27-panic-recover-and-where-to-use-them/) (4)절).
- ★ 누수 — **`NumGoroutine()` 이 기준으로 수렴하나**를 잠깐 기다리며 본다((2)절의 `settle`). 정본은 [목록의 **31번 주제**](../31-goroutine-leaks/).

### 10. 데몬이라 안 기다린다 · `언어-특성` §2 · `process-thread/`

- ★★ 자바 가상 스레드는 **항상 데몬**이라 **`main` 이 끝나면 JVM 이 기다리지 않는다** — Go 고루틴과 **같은 자리**
  ([`../../../java/syntax/56-virtual-threads/`](../../../java/syntax/56-virtual-threads/) (1)절 — 3초짜리 출력이 안 찍혔다).
  **플랫폼 스레드**는 기본이 비데몬이라 JVM 이 기다린다 — **Go 에는 「기다려 주는 고루틴」이 없다.**
- ★★ 단가의 논증 — [`../../언어-특성/README.md`](../../언어-특성/README.md) §2.
- ★ 스레드·경쟁 조건 일반 — [`../../../../process-thread/`](../../../../process-thread/).


---

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 로 **★고칠 것 0** |
| ★★★ `main` 종료 (`t28a`) | 출력을 파일로 받고 셸이 참거짓만 | 1 | `고루틴 끝` 아니오 · `defer` 아니오 · exit 0 |
| ★★ `NumGoroutine` (`t28b`) | `go build && ./prog` | 1 | 1 · 101 · true · 11 · false |
| ★★ `go` 인자 (`t28c`) | 〃 | 1 | A 1 · B 2 |
| ★★★ 루프 변수 격자 (`t28d`) | **`go.mod` 의 `go` 줄만** 1.21/1.22, 각 200판 `sort` + `uniq -c` | 400 | `200 [3 3 3]` · `200 [0 1 2]` |
| ★★ 스택 상수 (`t28stack`) | `sed`·`grep` 으로 `runtime` 소스 | 1 | `stackMin = 2048` · `adaptivestackstart = 1` |
| ★ 메모리 격자 (`t28e`) | `GODEBUG=adaptivestackstart=0/1` × N 1000/10000 | 1 | 네 칸 전부 2KB 자릿수 |
| ★ 컴파일 거부 (`t28bad`) | `go build -gcflags=-e` | 1 | 5줄 · exit 1 |

**구현·환경에 달린 항목**

| 항목 | 무엇에 달렸나 |
|---|---|
| 끊기는 줄 수 · 도착 순서 · `StackInuse` 절댓값 | **구현·스케줄러 — 흔들린다**(블록에 안 실었다) |
| `stackMin`·`adaptivestackstart` | **runtime 소스(이 판)** |
| `NumGoroutine` 이 `Done` 직후 바로 줄지 않는 틈 | **구현** |
| 고루틴 생성의 **시간** | ★ **안 쟀다** — 정본은 [`언어-특성/README.md`](../../언어-특성/README.md) §2 |
| `-race` 로 본 1.21 경쟁판 | ★ **안 던졌다**([목록의 **35번 주제**](../35-data-races-and-the-race-detector/)) |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다.

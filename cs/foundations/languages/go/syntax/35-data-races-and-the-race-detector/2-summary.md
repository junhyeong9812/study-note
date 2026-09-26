# go/syntax/35 — 데이터 레이스와 `-race` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Data Race Detector](https://go.dev/doc/articles/race_detector)(★ **이번에는 웹에서 열어 문장을 확인했다** — 32편은 안 열었다) · [Go 1.19 릴리스 노트](https://go.dev/doc/go1.19)(검출기 v3) ·
> [Go 메모리 모델](https://go.dev/ref/mem) · 이 툴체인의 `$(go env GOROOT)/src/runtime/race/`(README · `.syso` 의 문자열).\
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> ★ **버전** — 검출기가 **ThreadSanitizer v3** 로 바뀌며 「**unlimited number of goroutines**」가 된 것이 **1.19**(릴리스 노트, 웹) — (3)절에서 **10만 고루틴으로 던졌다.**
> ★ **`-race` 가 이 머신에서 열리는가**(cgo·gcc)는 [32번 주제](../32-sync-mutex-rwmutex-waitgroup-once/) (1)절이 판별했다 — **다시 판별하지 않았다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체는 넷째 창이다** — 「**경쟁 접근이 실제로 실행됐는지(설계로 안다)와 `-race` 가 보고했는지를 칸마다 나란히 찍는 격자**」.
32편이 「검출기가 **무엇을 보나**」를 줄 번호째 보였다면, 이 편은 「**무엇을 못 보나**」를 칸 수로 센다 — 마지막 줄 **`경쟁이 실행됐는데 보고가 없던 칸 3 / 7`**((1)절).
★★★ **셋 다 cgo 칸**이다. 그리고 **「실행 안 된 경로」는 원리상 못 본다**(보고 없음 · 경쟁도 없었음 — 격자 밖으로 뺐다).

★★★ **이 주제의 경계** — 경쟁 조건의 **원리**(공유 자원에 동시에 접근 · 상호 배제)는
[`../../../../process-thread/`](../../../../process-thread/) 「10. 경쟁 조건」·「11. 상호 배제와 Lock」이 정본이다. **그쪽은 경쟁이 왜 생기나까지**, 여기는 **Go 의 데이터 레이스 정의와 `-race` 가 무엇을 보장하고 못 보나부터.**
**레이스를 만드는 최소 코드**와 첫 보고(`n++` · stdout `1` · exit 66 · `vet` 침묵)는 [32번 주제](../32-sync-mutex-rwmutex-waitgroup-once/) (1)절이 정본이다 — **다시 싣지 않았다.**
**무엇이 순서를 세우나**(happens-before)는 [36번 주제](../36-reading-the-go-memory-model-in-code/)가 정본이다 — 여기서는 「순서가 없으면 **시간이 떨어져 있어도** 잡는다」까지만.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **메모리 모델 보장** | 메모리 모델 문서가 정한 것 | ★★ **데이터 레이스의 정의**(순서 없는 두 접근, 하나는 쓰기) · 「**Any implementation can, upon detecting a data race, report the race and halt**」 — ★ **검출기를 쓰라는 약속은 없다**, **해도 된다**는 허락이다 |
| **도구 문서** | Data Race Detector 글이 말한 것 | ★★★ 「**only finds races that happen at runtime, so it can't find races in code paths that are not executed**」 · `GORACE` 옵션과 기본값 · 「**memory usage may increase by 5-10x and execution time by 2-20x**」(★ **문서의 수치 — 안 쟀다**) |
| **구현(ThreadSanitizer 기반 검출기)** | runtime/race 가 한 것 | ★★★ **Go 가 만든 메모리 접근만 본다** — cgo 칸 셋의 침묵 · 같은 자리 1000 번에 보고 1 건 · exit 66 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | `3 / 7` · 10만 고루틴에서도 보고 · `.syso` 안에 옛 한계 문구가 **남아 있다** |

★★★ **선을 긋는다** — **「`-race` 가 보고했다 → 레이스가 있다」** 는 이 문서가 **실측으로 반례를 못 찾은 방향**이다(36편 격자의 침묵 9칸).
★★★ 그런데 **「거짓 양성이 없다」는 브리핑이 문서의 주장이라 했지만 — 이번에 연 Data Race Detector 글에는 그 문장이 없다**(제3의 상태 — 아래 (0)절). 그래서 이 문서는 그것을 **보장으로 적지 않는다.**
**「`-race` 가 조용했다 → 레이스가 없다」** 는 **틀린 방향**이다 — (1)절의 셋, 32편의 `WaitGroup.Add` 20판.

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
```

```text
===== 명령: sed -n "1,3p" "$(go env GOROOT)/src/runtime/race/README" =====
runtime/race package contains the data race detector runtime library.
It is based on ThreadSanitizer race detector, that is currently a part of
the LLVM project (https://github.com/llvm/llvm-project/tree/main/compiler-rt).
(exit 0)
```

- ★ 「**It is based on ThreadSanitizer race detector**」 — 이 검출기는 **LLVM 의 ThreadSanitizer 를 Go 런타임에 붙인 것**이다. 그래서 (1)절의 한계는 **구현의 한계**이지 언어 규칙이 아니다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | ★★ **보고의 `goroutine N`·`Goroutine N` 의 N** | 고루틴 id — 정규화 규칙 `([Gg]oroutine) \d+`(32편과 같은 규칙) |
| **흔들린다** | 보고의 `Read at 0x00000153a738` · 프레임의 `+0x1ee` | 기본 정규화 규칙(주소 — 5자리 이상)이 잡는다. ★ **`+0x24` 같은 짧은 오프셋은 같은 바이너리에서 안 흔들렸다** |
| **흔들린다(그래서 안 실었다)** | ★★ **cgo 칸에서 잃은 증가 수**(탐색 실행: 2000 중 1984 · 1997) · 경쟁 칸이 찍은 값 | 스케줄링 — 격자는 **보고 예/아니오와 종료 코드**만 싣는다 |
| 안 흔들린다 | ★★★ **격자의 `-race 보고=예/아니오` · exit 66/0 · `3 / 7`** | 재실행 대조에서 같았다 |
| 안 흔들린다 | ★★★ **`동시에 살아 있는 고루틴: 100001`** · `Found 2 data race(s)` · `GORACE` 판의 종료 코드 · 줄 번호 | |
| 안 흔들린다 | rustc 진단 `E0502`·`E0277` 전문 · `파일:줄:칸` | 컴파일 에러 |

★ 정규화 규칙은 **기본 넷 + 고루틴 id 하나**를 썼다.

## 한눈에 — 쉽게 말하면

**`-race` 는 「CCTV」다.** 설치된 복도(Go 코드가 만진 Go 메모리)에서 **실제로 일어난** 일만 찍힌다.
두 사람이 **순서표 없이** 같은 물건을 만졌으면 — **몇 시간 떨어져서**였어도 — 찍힌다(순서표가 없었다는 게 문제니까).
그런데 **아무도 안 지나간 복도**(실행 안 된 분기)는 찍을 게 없고, **카메라 없는 창고**(C 코드 · C 가 할당한 메모리)는 아예 안 보인다.
**녹화가 조용하다고 도둑이 없었던 게 아니다.**

| 비유 | 실체 |
|---|---|
| 실제로 지나간 사람만 찍힌다 | ★★★ **실행된 접근만** — `notran` 칸은 보고 없음(경쟁도 없었음) |
| 몇 시간 떨어져 만져도 **순서표가 없으면** 찍힌다 | ★★★ **`apart` 칸 — 300ms 떨어져도 보고**, `Goroutine N (finished)` |
| 방문객이 10만 명이어도 | ★★ **`many` 칸 — 100001 고루틴에서도 보고**(1.19 부터 한계 없음) |
| 카메라 없는 창고 | ★★★ **`goOnC`·`cOnC`·`cOnGo` — 보고 없음, exit 0** |
| 같은 자리 도둑질 1000 번 | ★ **보고는 1 건**(같은 자리는 한 번만) |
| 경보가 울리면 문을 닫을지 | ★ **`GORACE=halt_on_error=1`** — 첫 보고에서 끝낸다 |

```text
   ★★★ -race 는 무엇을 못 보나 — 격자 ((1)절의 실측, -race 빌드)

   칸        무엇을 했나                              경쟁이 실행됐나   -race 보고
   ───────   ──────────────────────────────────────   ──────────────   ──────────
   ran       고루틴이 n++, main 이 n 읽기               예               예 (exit 66)
   notran    같은 코드인데 분기가 안 열림                아니오            아니오
   apart     쓰기 끝나고 300ms 뒤에 읽기                예               예  ← 시간이 아니라 순서
   many      10만 고루틴이 살아 있는 채로 ran           예               예  ← 한계 없음
   mixed     원자로 쓰고 평범하게 읽기                  예               예
   goOnC     Go 코드가 C.malloc 메모리를 ++             예               ★ 아니오
   cOnC      C 함수가 C 메모리를 ++                     예               ★ 아니오
   cOnGo     C 함수가 Go 변수를 ++                      예               ★ 아니오

   → 경쟁이 실행됐는데 보고가 없던 칸 3 / 7   (전부 cgo 쪽)
```

> **데이터 레이스(data race)** — 메모리 모델의 정의로, **같은 메모리 위치**에 대한 두 접근이 **happens-before 로 순서가 서지 않고**, 적어도 하나가 **쓰기**인 것. 「동시에」가 아니라 「**순서 없이**」 다.

> **`-race`** — 빌드 플래그. 컴파일러가 메모리 접근마다 검출기 호출을 심고, ThreadSanitizer 기반 런타임이 순서를 추적한다. cgo 가 필요하다([32번 주제](../32-sync-mutex-rwmutex-waitgroup-once/) (1)절).

- ★★★ [32번 주제](../32-sync-mutex-rwmutex-waitgroup-once/) (1)절 — **레이스를 만드는 최소 코드**(동기화 없는 `n++`)의 정본. stdout `1`·exit 66·`Read … by main goroutine` / `Previous write … by goroutine N`·**`vet` 침묵**. ★ 여기의 `ran` 칸이 같은 모양이다.
- ★★★ [32번 주제](../32-sync-mutex-rwmutex-waitgroup-once/) (4)절 — **`WaitGroup.Add` 를 고루틴 안에서 부른 코드를 20판 돌려 어떤 판만 보고**했다. 이것이 「**실행된 인터리빙만 본다**」의 첫 증거다 — 이 편 (1)절의 `notran` 은 그 극단(한 번도 안 실행된 경로)이다.

## 이 주제가 답하려는 질문

1. **데이터 레이스는 무엇이고, 「동시에」와 무엇이 다른가.**
2. **`-race` 는 무엇을 보장하고, 무엇을 원리상 못 보나** — 칸 수로.
3. **같은 레이스를 Rust 는 왜 컴파일에서 막고 Go 는 왜 실행에서 찾나.**

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **「경쟁이 실행됐나 × `-race` 보고」 격자** | **못 보는 칸이 몇인가** | ★ 본체 창 — `3 / 7` 을 스크립트가 센다 |
| ★★ **보고 전문(`apart`)** | 시간이 떨어져도 **순서가 없으면** 잡는다 | 32편의 창을 그대로 |
| ★★ **`.syso` 의 문자열 · README** | 이 판 검출기가 **무엇으로 만들어졌나** · 옛 한계 문구가 남아 있나 | 규칙 26(도구 판별) |
| ★★ **`GORACE` 판 셋** | 보고 수 · 멈춤 · 종료 코드 | 도구 설정 |
| ★★ **rustc 진단** | 같은 레이스를 **컴파일러가** 막는다 | 대비 |
| **못 잰 것 — 「거짓 양성 없음」** | ★★★ **Data Race Detector 글에 그 주장이 없다**(이번에 웹에서 열어 확인). 브리핑의 전제였다. **보장으로 적지 않는다** — 관찰(36편 격자의 침묵 9칸)만 있다 | 제3의 상태 |
| **부적용 — 시간·메모리 비용** | ★★ 문서의 「**5-10x · 2-20x**」는 **문서의 수치**다. 이 문서는 **안 쟀다** | — |
| **부적용 — 「실행 안 된 경로」의 경쟁** | `notran` 은 **경쟁이 일어나지 않았다** — 못 본 것이 아니라 **볼 것이 없었다**(규칙 18-B 제4의 상태). 그래서 분모에서 뺐다 | — |

### (1) ★★★ 검출기가 못 보는 것 — 격자

**언제 쓰나** — 「`go test -race` 가 통과했다」를 **어디까지 믿을지** 정할 때.

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

그림 해설 (한 단계씩):

- ★★★ **마지막 줄 `경쟁이 실행됐는데 보고가 없던 칸 3 / 7`.** 스크립트가 셌다. 「경쟁 접근이 실행됐나」는 **설계로 정한 칸**이다(소스의 `switch` 가 그 칸에서 무엇을 하나).
- ★★★ **`ran` — 보고, exit 66** — 32편의 최소 레이스와 같은 모양이다(여기서는 `close(done)` 전에 읽는다).
- ★★★ **`notran` — 보고 없음, exit 0.** **같은 `race()` 함수**가 소스에 있지만 이 칸에서는 **분기가 안 열렸다.**
  문서 「**The race detector only finds races that happen at runtime, so it can't find races in code paths that are not executed.**」 — 테스트가 **그 분기를 안 지나가면** `-race` 는 영원히 모른다.
  ★ 그래서 이 칸은 분모 밖이다 — **경쟁이 실제로 없었다.** 「못 본 것」과 「볼 것이 없던 것」을 가른다.
- ★★★ **`apart` — 보고.** 쓰기는 **이미 끝났고**, main 은 **300ms 뒤에** 읽었다. 두 접근은 **시간상 겹치지 않는다.** 그래도 잡혔다:

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

  ★★★ **`Goroutine N (finished) created at`** — 쓴 고루틴은 **끝난 뒤**다. 검출기는 **「같은 순간이었나」가 아니라 「두 접근 사이에 happens-before 가 있나」** 를 본다. `time.Sleep` 은 순서를 **안 만든다**([36번 주제](../36-reading-the-go-memory-model-in-code/) (2)절 격자의 `sleep` 칸 — 거기서 **무엇이 순서를 만드나**를 13칸으로 센다).
- ★★★ **`many` — `동시에 살아 있는 고루틴: 100001` 에서도 보고.** (3)절.
- ★★ **`mixed` — 보고.** 쓰는 쪽만 `atomic.AddInt64` 이고 읽는 쪽이 **평범한 읽기**면 레이스다. [33번 주제](../33-sync-atomic-and-sync-map/) (2)절 — **옛 함수형이 이 실수를 허용**하고 새 타입(`atomic.Int64`)은 **막는다.**
- ★★★ **`goOnC` — 보고 없음, exit 0.** **Go 코드**가 `*cp++` 를 두 고루틴에서 하는데, 그 메모리가 **`C.malloc` 이 준 것**이라 검출기가 **안 본다.**
  ★★ 코드는 Go 인데 **메모리가 Go 것이 아니다** — 검출기가 추적하는 범위는 **Go 가 관리하는 메모리**다(이 판에서의 관찰 — 이유가 된 구현 코드는 **안 열었다**).
- ★★★ **`cOnC` — 보고 없음.** C 함수 `inc` 는 **`-race` 가 계측하지 않는다**(C 컴파일러가 만든 코드다).
- ★★★ **`cOnGo` — 보고 없음.** **Go 변수** `goInt` 를 **C 함수**가 두 고루틴에서 `++` 했다. 메모리는 Go 것인데 **접근이 C 쪽**이라 안 보인다.
  ★ 세 칸 모두 탐색 실행에서 **증가를 잃었다**(2000 이 아니었다) — **레이스는 실제로 있었다.** 그 수는 흔들려서 블록에 안 실었다.

```text
   ★★★ 누가 접근했나 × 누구의 메모리인가 — cgo 칸 넷의 정리 ((1)절)

                        Go 메모리(Go 변수)          C 메모리(C.malloc)
   접근이 Go 코드       ran · apart · many · mixed    goOnC
                        → 보고                         → ★ 침묵
   접근이 C 함수        cOnGo                          cOnC
                        → ★ 침묵                       → ★ 침묵

   → 보이는 것은 왼쪽 위 칸 하나 — 「Go 코드가 한 Go 메모리 접근」
```

비용 — **안 쟀다.**

### (2) ★★ 보고 수와 멈춤 — `GORACE`

**언제 쓰나** — 보고가 **몇 건**이 나왔는지를 레이스의 **횟수**로 읽으려 할 때.

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

그림 해설 (한 단계씩):

- ★★★ **기본(`GORACE=`) — `Found 2 data race(s)`, exit 66.** `touch(&a)` 를 **1000 번** 불렀는데 **보고는 자리마다 한 건** — `a` 에 하나, `b` 에 하나.
  ★★ **보고 수는 레이스가 일어난 횟수가 아니다** — **서로 다른 자리(코드 위치)의 수**에 가깝다(이 판의 관찰).
  ★ 프로그램은 **끝까지 돌았다**(`--- main 의 끝에 닿았다`) — 기본은 **보고하고 계속 간다.**
- ★★★ **`halt_on_error=1` — 첫 보고 뒤에 멈췄다**(exit 66, `--- 첫 자리를 지났다` 가 **없다**). 메모리 모델 문서의 「**report the race and halt execution**」이 이 설정이다.
- ★★ **`exitcode=3` — exit 3.** 66 은 **기본값**일 뿐이다(문서 「`exitcode` (default `66`)」).
- ★ 마커를 **표준 오류**로 찍었다 — 검출기 보고도 표준 오류라 **순서가 섞이지 않는다**(규칙 18).

비용 — 없다.

### (3) ★★ 고루틴 수 한계 — 8128 은 옛 이야기였다

브리핑은 「**8128 개를 넘기면 `race: limit on 8128 simultaneously alive goroutines is exceeded` 로 죽는다**」를 던져 보라고 했다. (1)절 `many` 칸이 **100001 개**를 동시에 살려 두고 레이스를 일으켰다 — **죽지 않고 보고했다.**

- ★★★ Go 1.19 릴리스 노트(웹) — 「**The race detector has been upgraded to use thread sanitizer version v3 … it supports an unlimited number of goroutines.**」 — **1.19 부터 한계가 없다.** 브리핑의 전제가 **이 판에서 뒤집혔다.**
- ★★ 그런데 **문구 자체는 이 판의 검출기 바이너리 안에 남아 있다**:

```text
===== 명령: echo "GOAMD64=$(go env GOAMD64)"; strings "$(go env GOROOT)/src/runtime/race/internal/amd64v1/race_linux.syso" | grep "simultaneously alive" =====
GOAMD64=v1
race: limit on %u simultaneously alive goroutines is exceeded, dying
(exit 0)
```

  ★ `%u` 자리의 숫자는 **문자열에 없다** — 8128 이라는 값은 **이 바이너리에서 확인 못 했다**(옛 문서의 수치다). 확인한 것은 「**그 문구가 남아 있다**」와 「**100001 개에서 그 문구가 안 나왔다**」 둘이다.
  ★ 1.19 노트는 「**except `windows/amd64` and `openbsd/amd64`, which remain on v2**」 라고 적는다 — 그 두 판의 한계는 **이 머신에서 못 잰다.**

비용 — **안 쟀다**(10만 고루틴의 메모리는 안 실었다).

### (4) ★★★ 같은 레이스를 Rust 로 — 컴파일러가 막는다

**언제 쓰나** — 「Go 는 왜 이것을 컴파일에서 못 막나」를 물을 때. 32편의 최소 레이스(**한 스레드가 쓰고, 다른 쪽이 읽는다**)를 Rust 로 옮겼다.

```text
===== 명령: rustc --version =====
rustc 1.92.0 (ded5c06cf 2025-12-08)
(exit 0)
```

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

- ★★★ **``error[E0502]: cannot borrow `n` as immutable because it is also borrowed as mutable``** — 새 스레드의 클로저가 `n` 을 **가변으로 빌려 간 동안** main 이 `n` 을 **읽으려 했다.**
  Rust 의 빌림 규칙(**가변 참조 하나 XOR 공유 참조 여럿**)이 「**쓰는 쪽과 읽는 쪽이 순서 없이 공존**」 을 **타입 검사에서** 거부한다.

**값을 공유하는 다른 길** — 참조 계수 포인터로 우회하면:

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

- ★★★ **``error[E0277]: `Rc<Cell<i32>>` cannot be sent between threads safely``** · 「**the trait `Send` is not implemented for `Rc<Cell<i32>>`**」 — 스레드 경계를 넘는 값은 **`Send`** 여야 하고, **원자적이지 않은 계수**를 가진 `Rc` 는 `Send` 가 아니다.
- ★★★ **Go 에는 이 두 장치가 없다** — 고루틴의 클로저는 **아무 변수나 잡고**, 어떤 타입이든 **채널로 넘긴다.** 그래서 **같은 코드가 컴파일되고**, 레이스는 **실행해서 `-race` 로** 찾는다.
  ★ 그 대가가 (1)절이다 — **실행 안 된 경로 · cgo 쪽**은 영원히 못 본다. Rust 의 검사는 **실행하지 않아도** 모든 경로를 본다(단 `unsafe` 안은 컴파일러가 믿고 넘긴다 — 이 문서는 **안 던졌다**).
- Rust 쪽 정본은 Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **50번**(`Send`/`Sync` — 아직 폴더 없음) · 빌림 규칙은 [`../../../rust/syntax/10-borrowing-and-aliasing-rules/`](../../../rust/syntax/10-borrowing-and-aliasing-rules/).

비용 — 없다.

## 문법 — 형태와 규칙

| 쓰는 꼴 | 무엇을 하나 |
|---|---|
| `go test -race ./...` · `go build -race` · `go run -race` | 검출기를 붙여 빌드한다(cgo 필요) |
| `GORACE="halt_on_error=1"` | 첫 보고에서 멈춘다 |
| `GORACE="exitcode=3"` | 보고가 있을 때의 종료 코드(기본 66) |
| `GORACE="log_path=/tmp/race"` | 보고를 파일로(문서 — **이 배치는 안 던졌다**) |

규칙 불릿.

- ★★★ **레이스의 기준은 「동시에」가 아니라 「순서 없이」** — 시간이 떨어져 있어도 happens-before 가 없으면 레이스다.
- ★★★ **`-race` 는 실행된 경로만** — 테스트가 그 분기를 **지나가게** 해야 한다. 여러 번·부하를 주며 돌린다(32편 (4)절).
- ★★★ **cgo 쪽은 안 보인다** — C 가 만든 메모리, C 가 한 접근. 그 경계에는 **락을 Go 쪽에서** 건다.
- ★★ **보고 수 ≠ 레이스 횟수** — 같은 자리는 한 번.
- ★ **CI 에서 `-race` 를 켠다** — 단 비용(문서의 5-10x · 2-20x)은 **이 문서가 안 쟀다.**

### 금지 사례 — 컴파일은 되고 `-race` 도 못 잡는 것

| 쓴 꼴 | 누가 잡나 | 어디서 |
|---|---|---|
| 테스트가 안 지나가는 분기의 레이스 | ★★★ **아무도**(실행이 안 됐다) | (1)절 `notran` |
| 두 고루틴이 `C.malloc` 메모리를 Go 코드로 `++` | ★★★ **아무도** | `goOnC` |
| 두 고루틴이 C 함수로 Go 변수를 `++` | ★★★ **아무도** | `cOnGo` |
| `go vet` 으로 레이스 찾기 | ★★ `vet` 은 **침묵**한다 | [32번 주제](../32-sync-mutex-rwmutex-waitgroup-once/) (1)절 |

## 어디서 틀리나

### 1. ★★★ 「`-race` 가 조용하면 레이스가 없다」

- (1)절 실측 — **3 / 7** 이 조용했다. 32편 — 같은 바이너리가 **어떤 판만** 보고.

### 2. ★★★ 「두 접근이 시간상 떨어져 있으면 레이스가 아니다」

- (1)절 `apart` — **300ms 떨어져도 보고.** `Sleep` 은 순서가 아니다. 순서를 만드는 것은 [36번 주제](../36-reading-the-go-memory-model-in-code/)의 격자.

### 3. ★★★ 「Go 코드로 만졌으니 `-race` 가 본다」

- (1)절 `goOnC` — **Go 코드인데 메모리가 C 것이면 안 본다.**

### 4. ★★ 「`Found 1000 data race(s)` 가 아니니 한 번뿐이었다」

- (2)절 — **1000 번의 같은 자리 레이스가 보고 1 건.**

### 5. ★★ 「고루틴이 8128 개를 넘으면 `-race` 가 죽는다」

- (3)절 — **1.19 부터 한계 없음**(이 판 100001 개). 문구는 바이너리에 남아 있다.

### 6. ★★ 「`-race` 는 거짓 양성이 없다고 문서가 보장한다」

- ★★ **이번에 연 Data Race Detector 글에는 그 문장이 없다.** 관찰로는 [36번 주제](../36-reading-the-go-memory-model-in-code/) (2)절의 **순서가 선 9칸이 전부 침묵**했다 — **관찰**이지 보장이 아니다.

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| ★★ **데이터 레이스의 정의** · 「검출하면 보고하고 멈춰도 된다」 | **메모리 모델** | [36번 주제](../36-reading-the-go-memory-model-in-code/) (1)절 문서 블록 |
| ★★★ **실행된 경로만 본다** | **도구 문서** | (1)절 문서 인용 |
| `GORACE` 옵션과 기본값(exitcode 66 …) | **도구 문서** | (2)절 |
| 1.19 부터 고루틴 수 한계 없음(v3) | **릴리스 노트(웹)** | (3)절 |
| ★★★ **cgo 쪽 메모리·접근을 못 본다** | **구현(ThreadSanitizer 기반)** — 이 판의 관찰 | (1)절 |
| 같은 자리는 한 번만 보고 | **구현** — 이 판의 관찰 | (2)절 |
| 「거짓 양성 없음」 | ★★ **못 잰 것 — 문서에 주장 없음** | (0)절 |
| 시간·메모리 비용 5-10x · 2-20x | **문서의 수치 — 안 쟀다** | (0)절 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 모든 동시성 코드의 테스트 | **`go test -race`** | 32편 · (1)절 |
| 드문 인터리빙의 레이스 | **`-race` 를 여러 번 · 부하를 주며** + 정적 도구(`vet`) | 32편 (4)절 |
| cgo 경계를 넘는 공유 메모리 | **Go 쪽 `Mutex`** — 검출기에 기대지 않는다 | (1)절 cgo 칸 |
| CI 가 첫 레이스에서 멈추길 원한다 | **`GORACE=halt_on_error=1`** | (2)절 |

## 핵심 문장

- ★★★ **데이터 레이스는 「순서 없이」다, 「동시에」가 아니다** — 300ms 떨어진 두 접근도 `-race` 가 잡았다(`Goroutine N (finished)`).
- ★★★ **`-race` 가 못 보는 칸 3 / 7 — 전부 cgo 쪽**(Go 코드가 C 메모리를 · C 가 C 메모리를 · C 가 Go 메모리를). 그리고 **실행 안 된 경로는 볼 것 자체가 없다.**
- ★★ **보고 수는 레이스 횟수가 아니다** — 같은 자리 1000 번에 1 건. `halt_on_error=1` 은 첫 보고에서 멈추고, `exitcode` 는 66 을 바꾼다.
- ★★ **8128 한계는 1.19 에서 사라졌다** — 이 판은 100001 고루틴에서도 보고했다. 문구만 바이너리에 남았다.
- ★★ **「거짓 양성 없음」은 이번에 연 문서에 없다** — 보장으로 적지 않는다.
- ★★★ **Rust 는 같은 레이스를 컴파일에서 막는다**(`E0502` 빌림 · `E0277` `Send`) — Go 는 컴파일하고 **실행해서** 찾는다.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 35번)
- [`../../../../process-thread/`](../../../../process-thread/) — ★★ **정본 경계.** 「10. 경쟁 조건」·「11. 상호 배제와 Lock」 — **경쟁이 왜 생기나까지**는 거기.
- [32번 주제](../32-sync-mutex-rwmutex-waitgroup-once/)(`sync`) — ★★★ 레이스를 만드는 최소 코드 · `-race` 판별 · `WaitGroup.Add` 20판의 정본
- [36번 주제](../36-reading-the-go-memory-model-in-code/)(메모리 모델) — ★★ 무엇이 순서를 만드나 — 13칸 격자
- [33번 주제](../33-sync-atomic-and-sync-map/)(`atomic`) — 원자로 쓰고 평범하게 읽기 · `-race` 가 침묵하는데 불변식이 깨지는 칸
- [`../../../c/syntax/32-what-volatile-actually-guarantees/`](../../../c/syntax/32-what-volatile-actually-guarantees/) (8)절 — ★ C 쪽 TSan 이 `volatile` 을 레이스로 잡는 실측 — 같은 ThreadSanitizer
- [`../../../rust/syntax/10-borrowing-and-aliasing-rules/`](../../../rust/syntax/10-borrowing-and-aliasing-rules/) — `E0502` 의 규칙
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **50번**(`Send`/`Sync`)

## 용어 풀이

- **데이터 레이스** — 같은 위치에 대한 두 접근이 happens-before 로 순서가 서지 않고 하나 이상이 쓰기인 것.
- **happens-before** — 메모리 모델이 정하는 「앞선다」 관계. 채널·락·`Once`·원자 연산이 만든다([36번 주제](../36-reading-the-go-memory-model-in-code/)).
- **ThreadSanitizer(TSan)** — LLVM 의 동적 레이스 검출기. Go 의 `-race` 런타임이 이것에 기반한다.
- **`GORACE`** — 검출기 설정 환경 변수(`halt_on_error`·`exitcode`·`log_path`·`history_size` …).
- **exit 66** — 보고가 있을 때 검출기의 기본 종료 코드.
- **`Send`(Rust)** — 스레드 경계를 넘어 옮겨도 되는 타입의 표지. `Rc` 는 아니다.

---

## 더 들어가면

- ★ **`history_size`** 를 줄이거나 늘렸을 때 `Previous write` 의 스택이 사라지는지는 **안 던졌다.**
- ★ 검출기가 cgo 메모리를 안 보는 **구현 코드**(runtime 의 주소 범위 판정)는 **안 열었다** — 관찰만 적었다.
- ★ `-race` 의 **시간·메모리 비용**은 **안 쟀다.**
- ★ Rust 의 `unsafe` 로 같은 레이스를 **컴파일되게** 만드는 것은 **안 던졌다.**

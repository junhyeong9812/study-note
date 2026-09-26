# go/syntax/32 — `sync`: `Mutex`·`RWMutex`·`WaitGroup`·`Once` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [`sync`](https://pkg.go.dev/sync) 문서 · [Go 메모리 모델](https://go.dev/ref/mem) ·
> [`go vet` 의 `copylocks`·`waitgroup` 분석기](https://pkg.go.dev/cmd/vet) · [Data Race Detector](https://go.dev/doc/articles/race_detector).
> 문서는 **이 툴체인의 `go doc`·`go tool vet help`** 에서 직접 떴다(웹의 race detector 글은 **안 열었다**).\
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> ★ **버전** — `sync.OnceValue` 가 **1.21** · `WaitGroup.Go` 가 **1.25**(`api/go1.25.txt:96` — [28번 주제](../28-goroutines-go-statement-cost-and-termination/) (2)절이 이미 판별했다, 다시 재지 않았다) ·
> `go vet` 의 **`waitgroup` 분석기**가 이 판에 있다((4)절 — 이 판의 `go tool vet help` 에 **있다는 것**만 확인했다).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체는 넷째 창이다** — 「**`-race`(데이터 경쟁 검출기)의 `WARNING: DATA RACE` 보고**」.
「안 터졌다」는 동시성에서 **가장 약한 근거**다 — 동기화 없는 코드도 대개 맞는 값을 낸다((1)절의 `1`).
**검출기가 「이 두 접근 사이에 순서가 없다」를 줄 번호째** 짚어야 비로소 근거가 된다.
★ 이 창은 **cgo(gcc)가 있어야 열린다** — 그래서 **판별 블록부터** 실었다(규칙 26). **이 판·이 머신에서 열린다.**
★★ 그 짝으로 「**`go vet` 의 `copylocks` 탐침 18개 중 몇 개가 답했나**」((3)절 — 규칙 18-A) — **복사하면 안 되는 타입**은 컴파일러가 아니라 `vet` 이 지킨다.

★★★ **이 주제의 경계** — 상호 배제·경쟁 조건의 **원리**(임계 구역·락이 왜 필요한가)는
[`../../../../process-thread/`](../../../../process-thread/)가 정본이다. **그쪽은 락이 무엇을 막는가까지**, 여기는 **Go `sync` 타입의 계약·복사 금지·함정부터.**
데이터 경쟁과 `-race` 의 **전모**(무엇을 보장하고 무엇을 못 보나)는 목록의 **35번 주제**다 — 여기서는 **창으로 한 번** 쓴다.
`sync/atomic`·`sync.Map` 은 목록의 **33번 주제**다 — 경계만.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세·메모리 모델 보장** | 명세·메모리 모델이 약속한 것 | ★ **명세에는 `sync` 가 없다** — 표준 라이브러리다. 메모리 모델이 「**n 번째 `Unlock` 은 m 번째 `Lock` 보다 먼저(n < m)**」와 `Once` 의 순서를 정한다 |
| **표준 라이브러리 계약** | `sync` 문서가 약속한 것 | ★★★ **「must not be copied after first use」** · `RWMutex` 는 **재귀 읽기 잠금 금지** · `Once` 는 **정확히 한 번** · `Mutex` 는 **특정 고루틴에 묶이지 않는다** |
| **구현(runtime·도구)** | runtime·`vet`·`-race` 가 한 것 | ★★★ **`-race` 는 실행 중에 본 접근만** 판단한다 · **`copylocks`·`waitgroup` 은 `vet` 의 휴리스틱** · 안 잠근 것을 풀면 **`fatal error`** · 교착 탐지 · `[sync.Mutex.Lock]` 상태 문구 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 18탐침 중 13 · `-race` 가 `WaitGroup.Add` 함정을 **어떤 판은 잡고 어떤 판은 못 잡는다** |

★★★ **선을 긋는다** — 「`Mutex` 를 복사하지 마라」는 **문서의 계약**이고, 그것을 **잡아 주는 것은 컴파일러가 아니라 `vet`** 이다.
「이 코드에는 경쟁이 없다」는 **`-race` 가 말해 줄 수 없다** — `-race` 는 **이번 실행에서 일어난 접근**만 본다((4)절 — 같은 코드에서 **어떤 판은 보고하고 어떤 판은 안 했다**).

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
```

```text
===== 명령: cd "$(go env GOROOT)/api" && grep -n "OnceValue\[\|TryLock" go1.18.txt go1.21.txt =====
go1.18.txt:183:pkg sync, method (*Mutex) TryLock() bool
go1.18.txt:184:pkg sync, method (*RWMutex) TryLock() bool
go1.21.txt:405:pkg sync, func OnceValue[$0 interface{}](func() $0) func() $0 #56102
(exit 0)
```

- ★ `TryLock` 이 **1.18**, `OnceValue` 가 **1.21** — 이 문서가 쓰는 API 중 판이 걸린 것들이다(`WaitGroup.Go` 의 1.25 는 [28번 주제](../28-goroutines-go-statement-cost-and-termination/) (2)절).

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | ★★ **`-race` 보고·트레이스의 `goroutine N`·`Goroutine N` 의 N** | 고루틴 id — 정규화 규칙 `([Gg]oroutine) \d+` **하나**(대소문자 둘 다 — `-race` 는 `Goroutine 8 (finished)` 로 적는다) |
| **흔들린다** | `-race` 의 `Read at 0x00c00011e028` · 트레이스 인자의 긴 주소 | 기본 정규화 규칙(주소)이 잡는다 |
| **흔들린다** | ★★ **교착 트레이스 프레임의 짧은 인자 값** — `runtime_SemacquireRWMutexR(0x2faf080?, 0x0?, …)` | 재실행 대조에서 **`0x0?` 와 `0x8?` 로** 갈렸다 — 5자리 미만이라 주소 규칙이 못 잡는다. 정규화 규칙 `\((?:0x\|\{0x)[^()]*\)` 를 **이 칸 하나에** 더했다((6)·(7)·(8)절의 트레이스). [27번 주제](../27-panic-recover-and-where-to-use-them/)는 같은 칸을 `GOTRACEBACK=none` 으로 껐지만, 여기서는 **상태 줄(`[sync.RWMutex.RLock]`)이 근거**라 트레이스를 끌 수 없었다 |
| **흔들린다(그래서 안 실었다)** | ★★★ `WaitGroup.Add` 를 고루틴 안에서 부른 판의 **결과값**과 **`-race` 가 보고한 판 수** | 스케줄링 — 20판 돌려 「**100 이 아닌 판이 있었나**」·「**한 판이라도 보고했나**」·「**모두 보고했나**」 참거짓만 실었다 |
| 안 흔들린다 | ★★★ **`WARNING: DATA RACE`·`Read at … by main goroutine`·`Previous write … by goroutine N`·줄 번호·`exit 66`** | 50ms 잠으로 순서를 벌려 **같은 보고**가 나왔다(재실행 대조) |
| 안 흔들린다 | ★★★ **`copylocks` 탐침 18개 중 `답한 탐침 13 / 18`** · `vet` 의 문장 · `파일:줄:칸` | 정적 분석이다 |
| 안 흔들린다 | `100000` · `Once` 의 `1` · `100 / 100` · 교착의 `[sync.Mutex.Lock]`·`[sync.RWMutex.RLock]` · 종료 코드 | |

★ 정규화 규칙은 **기본 넷 + 고루틴 id + 프레임 인자, 둘**을 썼다.

## 한눈에 — 쉽게 말하면

**`Mutex` 는 화장실 열쇠 하나다.** 열쇠를 쥔 사람만 들어가고, 나오면서 **걸어 둔다.**
Go 의 열쇠는 **벽에 따로 걸려 있다** — 화장실(데이터)과 **붙어 있지 않다.** 그래서 **열쇠 없이 문을 열어도 아무도 안 막는다**(컴파일러는 모른다).
열쇠를 **복사해 두 개**로 만들면 — 두 사람이 **각자 자기 열쇠로** 들어간다. `vet` 이라는 관리인이 **복사하는 장면**을 대부분 잡는다.

| 비유 | 실체 |
|---|---|
| 화장실 열쇠 하나 | ★★ **`sync.Mutex`** — `Lock`·`Unlock` |
| 열쇠는 **벽에**, 화장실과 **따로** | ★★★ **Go 는 뮤텍스와 데이터가 따로다** — 잠그지 않고 만져도 컴파일된다. ★ **Rust `Mutex<T>` 는 데이터를 감싼다** — 잠그지 않으면 **만질 방법이 없다**((2)절) |
| 나올 때 **반드시** 건다 | ★★ **`defer mu.Unlock()`** — 패닉으로 나가도 풀린다((2)절, [26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/)) |
| 열쇠를 **복사** | ★★★ **`Mutex`·`WaitGroup`·`Once`·`RWMutex` 를 값으로 넘기기** — `vet copylocks` 가 18탐침 중 13 에 답한다((3)절) |
| 안에 있는 사람이 **또 열쇠를 찾는다** | ★★★ **재진입 없음** — 같은 고루틴이 두 번 `Lock` 하면 **교착**((6)절). 자바 `synchronized` 는 들어간다 |
| 열람실 — **여럿이 읽고, 쓸 땐 혼자** | ★★ **`RWMutex`** — 단, **쓰려는 사람이 줄을 서면** 새 읽는 사람도 막힌다 → **재귀 읽기 잠금이 교착**((7)절) |
| 출석부 — **다 돌아왔나** | ★★ **`WaitGroup`** — `Add` 는 **띄우기 전에**((4)절) |
| 개업식 테이프 커팅 — **딱 한 번** | ★★ **`Once`** — 100 고루틴이 불러도 1 번((5)절) |

```text
   ★★★ 경쟁을 무엇이 보나 — 같은 질문, 세 창 ((1)·(4)절의 실측)

   코드                               go vet          -race                 결과값
   ──────────────────────────────     ────────        ────────────────      ──────────
   n++ 를 동기화 없이 (t32race)        침묵(exit 0)    DATA RACE · exit 66    1 (맞아 보인다)
   Mutex 로 감싼 n++ (t32mutex)        —               침묵 · exit 0          100000
   wg.Add 를 고루틴 안에서 (t32wgadd)   ★ 잡는다        어떤 판만 보고         100 이 아닌 판이 있다
```

```text
   ★★★ RWMutex 의 재귀 읽기 잠금 — 쓰는 쪽이 끼면 ((7)절의 실측)

   main     RLock ─────────────────────────────▶ RLock (둘째) ── 막힘 ─┐
                  │                                                     │ 서로 기다린다
   writer         └─(50ms 뒤)── Lock ── 막힘 (읽는 쪽이 있으니) ◀────────┘
                                 └ 「쓰는 쪽이 기다리는 동안 새 RLock 은 막힌다」 (문서)
   → 둘 다 잠듦 → fatal error … deadlock!  [sync.RWMutex.RLock] · [sync.RWMutex.Lock]
   writer 가 없으면 둘째 RLock 은 그냥 된다 (alone 칸)
```

> **`sync.Mutex`** — 상호 배제 락. 문서 「A Mutex is a mutual exclusion lock. The zero value for a Mutex is an unlocked mutex.」

> **데이터 경쟁(data race)** — 두 고루틴이 같은 변수에 **동기화 없이** 접근하고 그중 하나가 쓰기인 것. `-race` 가 **실행 중에** 찾는다.

> **`go vet`** — 컴파일은 되지만 의심스러운 코드를 찾는 정적 분석기. `copylocks`(락 복사)·`waitgroup`(`Add` 위치) 분석기가 여기 든다 — 이 판의 목록:

```text
===== 명령: go tool vet help | grep -E "^    (copylocks|waitgroup) " =====
    copylocks    check for locks erroneously passed by value
    waitgroup    check for misuses of sync.WaitGroup
(exit 0)
```

- [29번 주제](../29-channels-buffering-direction-close-range-and-nil/)가 목록상 **선행**이다 — 채널이 「**값을 넘겨 소유를 옮기는**」 도구라면, 뮤텍스는 「**한 자리의 값을 여럿이 번갈아 만지는**」 도구다((9)절의 판단표).
- ★★ [26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/)가 **`defer` 의 실행 시점**의 정본이다 — `defer mu.Unlock()` 이 패닉 경로에서도 도는 것은 거기의 규칙이다((2)절).
- ★★ [28번 주제](../28-goroutines-go-statement-cost-and-termination/) (2)절이 **`WaitGroup.Go`(1.25)** 의 `go doc` 과 `api/go1.25.txt:96` 을 이미 실었다 — 여기서는 **다시 판별하지 않았다.**

## 이 주제가 답하려는 질문

1. **`Mutex`·`RWMutex`·`WaitGroup`·`Once` 는 각각 무엇을 약속하고, 어디서 교착·오동작하나.**
2. **복사하면 안 되는 타입은 무엇이고, 누가 그것을 잡아 주나**(컴파일러가 아니다).
3. **채널로 풀 문제와 뮤텍스로 풀 문제를 어떻게 가르나** — 성능 주장 **없이**.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **`-race` 의 `WARNING: DATA RACE`** | **순서 없는 두 접근**을 줄 번호째 | ★ 본체 창 — 이 주제의 넷째 창. **판별 블록으로 열리는 것을 확인** |
| ★★★ **`go vet copylocks` × 탐침 18개** | **복사하면 안 되는 것**을 어디서 잡나 · **몇 개가 답했나** | 규칙 18-A |
| ★★ **`go vet waitgroup`** | `Add` 의 자리 | 이 판의 분석기 |
| ★★ **교착 탐지** | 재진입·재귀 읽기 잠금의 **교착** | [29번 주제](../29-channels-buffering-direction-close-range-and-nil/)의 본체 창 |
| ★ **`TryLock`** | 락이 **풀렸나**를 막히지 않고 묻기 | (2)·(8)절 |
| ★ **20판 참거짓** | 흔들리는 함정(`Add` 위치)의 **성질** | [28번 주제](../28-goroutines-go-statement-cost-and-termination/)의 방식 |
| ★ **다른 갈래 컴파일러** | Rust `Mutex<T>` · C++ `std::mutex` 복사 · 자바 재진입 | 대비 |
| **부적용 — 시간·처리량** | ★★★ **안 쟀다.** 「채널은 느리고 뮤텍스는 빠르다」·「`RWMutex` 가 읽기에 유리하다」를 이 문서는 **적지 않는다** | — |
| **부적용 — `sync/atomic`·`sync.Map`** | 목록의 **33번 주제** | — |

### (1) ★★★ `-race` 가 되나 — 판별부터, 그리고 첫 보고

**언제 쓰나** — 「이 코드는 경쟁이 없나」를 물을 때. **창이 열리는지부터** 확인한다(규칙 26).

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

- ★★★ **`CGO_ENABLED=1` · `gcc 13.3.0` · `go build -race exit=0`** — 이 머신에서 **`-race` 창이 열린다.**
- ★★ 마지막 줄 — **`CGO_ENABLED=0` 으로 끄면 `go: -race requires cgo`, exit 2.** cgo 가 꺼진 환경(정적 빌드 이미지 등)에서는 **이 문서의 본체 창이 통째로 안 열린다.** 그래서 이 블록이 전제다.

동기화 없는 `n++` 하나 —

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

- ★★★ **stdout 은 `1`, 종료 코드는 66.** 값만 보면 **맞다.** 고루틴이 50ms 안에 `n++` 을 끝냈으니까.
  ★★★ **「맞는 값이 나왔다」는 근거가 아니다** — 종료 코드 66 이 **검출기가 무언가를 봤다**는 신호다. stderr 를 보면:

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

그림 해설 (한 단계씩):

- ★★★ **`Read at … by main goroutine: main.main() ex/t32race.go:14`** · **`Previous write at … by goroutine N: main.main.func1() ex/t32race.go:11`** — **같은 주소**를 main 이 **14행에서 읽고**, 고루틴이 **11행에서 썼다.**
- ★★★ 둘 사이에 **순서를 세우는 것(동기화)이 없다** — `time.Sleep(50ms)` 는 **동기화가 아니다.** 실제로는 거의 늘 쓰기가 먼저 끝나지만, **메모리 모델은 그것을 약속하지 않는다.**
- ★★ **`Goroutine N (finished) created at: main.main() ex/t32race.go:10`** — 쓴 고루틴은 **이미 끝났는데도** 잡혔다. 검출기는 **「동시에 일어났나」가 아니라 「순서가 세워졌나」를** 본다.
- ★ `Found 1 data race(s)` · **exit 66** — 프로그램은 정상으로 끝났는데 **종료 코드가 66** 이다. 검출기가 보고를 남기면 종료 코드를 바꾼다(이 문서는 `GORACE` 설정을 **안 건드렸다** — 그 설정은 목록의 **35번 주제**).
- ★ 주소·고루틴 id 는 흔들린다 — 머리말의 정규화 칸. **줄 번호와 `Read`/`Previous write` 의 짝은 안 흔들렸다.**

같은 파일에 `vet` 은 —

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

- ★★★ **`vet exit=0`, 한 줄도 없다.** `vet` 은 **경쟁을 보는 도구가 아니다.** 데이터 경쟁은 **실행해 봐야** 보인다(`-race`).
  경쟁의 전모 — **`-race` 가 못 보는 것**(실행되지 않은 경로) — 는 목록의 **35번 주제**가 정본이다.

비용 — **안 쟀다.** `-race` 빌드가 느리고 메모리를 더 쓴다는 것은 이 문서가 **재지 않았다.**

### (2) ★★ `Mutex` 로 고치기 — 그리고 `defer mu.Unlock()`

**언제 쓰나** — 여러 고루틴이 **같은 변수**를 고칠 때.

```text
===== 소스: t32mutex.go =====
package main

import (
	"fmt"
	"sync"
)

type Counter struct {
	mu sync.Mutex
	n  int
}

func (c *Counter) Inc() {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.n++
}

func main() {
	var c Counter
	var wg sync.WaitGroup
	for range 1000 {
		wg.Go(func() {
			for range 100 {
				c.Inc()
			}
		})
	}
	wg.Wait()
	fmt.Println("1000 고루틴 × 100 회:", c.n)
}
===== 명령: go build -race -trimpath -o prog . && ./prog =====
1000 고루틴 × 100 회: 100000
(exit 0)
```

- ★★★ **`1000 고루틴 × 100 회: 100000`, `-race` 빌드에서 보고 0 줄, exit 0.** `Lock`/`Unlock` 이 순서를 세웠다 — 메모리 모델 「the n'th call to Mutex.Unlock "synchronizes before" the m'th call to Mutex.Lock for any n < m」((3)절 문서 블록).
- ★ **`-race` 가 침묵한 것은 「이번 실행에서 순서 없는 접근을 못 봤다」** 까지다 — 「경쟁이 없다」의 증명은 아니다. 다만 이 코드는 **모든 접근이 락 안**이라 설계로 말할 수 있다.

**`defer mu.Unlock()` 이 왜 기본형인가** — 잠근 채 패닉하면:

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

- ★★★ **`defer` — recover 뒤 `TryLock: true`**(풀려 있다) · **`nodefer` — `false`**(잠긴 채 남았다).
  패닉이 `mu.Unlock()` **앞에서** 함수를 떠났다. [26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/)의 규칙대로 **`defer` 는 패닉 경로에서도 돈다** — 손으로 쓴 `Unlock` 은 안 돈다.
- ★★ `nodefer` 쪽에서 `TryLock` 대신 `Lock` 을 불렀다면 **영원히 막혔을 것**이다((6)절의 교착). `TryLock` 은 **막히지 않고 물어보는 창**으로만 썼다.
- ★ **C++ 는 같은 일을 `lock_guard` 의 소멸자가 한다** — 예외 경로에서 락이 남는 것과 `lock_guard` 로 고치는 것은
  [`../../../cpp/syntax/15-raii-resources-as-types/`](../../../cpp/syntax/15-raii-resources-as-types/) (3)절이 이미 실측했다. **Go 의 `defer` 가 그 자리**다 — 다른 점은 **Go 는 적어야 돌고**(잊으면 끝), C++ 는 **타입이 돌린다.**

**Rust 는 잠그지 않으면 만질 수가 없다** —

```rust
// t32mutex.rs
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
```

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

- ★★★ **`error[E0614]: type std::sync::Mutex<{integer}> cannot be dereferenced`** — Rust 의 `Mutex<T>` 는 **데이터를 안에 품는다.** 데이터로 가는 길은 **`lock()` 이 돌려주는 가드**뿐이다.
- ★★★ **Go 는 뮤텍스와 데이터가 따로다** — `Counter{mu, n}` 의 `n` 은 **잠그지 않고도 컴파일러가 만지게 해 준다.** 「`mu` 가 `n` 을 지킨다」는 **주석(관례)일 뿐**이다(문법 절의 `// mu 가 지킨다`).
  그래서 Go 에서는 **`-race` 가 그 관례를 실행으로 검사하는 유일한 창**이 된다.
- Rust 쪽 정본은 Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **52번**(`Mutex`/`RwLock` — 아직 폴더 없음).

비용 — 없다(재지 않았다).

### (3) ★★★ 복사하면 안 되는 타입 — `copylocks` 탐침 18개

**언제 쓰나** — `sync` 타입을 **구조체 필드**로 둘 때(거의 늘 그렇다). 문서가 먼저 말한다:

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

- ★★★ 「**A Mutex must not be copied after first use.**」 — 복사하면 **잠김 상태까지 같이 복사**된 별개의 락이 둘 생긴다. 한쪽을 잠가도 다른 쪽은 모른다.
- ★ 「**the n'th call to Mutex.Unlock "synchronizes before" the m'th call to Mutex.Lock for any n < m**」 — (2)절의 근거.

**누가 그것을 잡나** — 탐침 18개를 한 파일에 두고 `vet` 에 물었다:

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

그림 해설 (한 단계씩):

- ★★★ **마지막 줄 `답한 탐침 13 / 18`.** 스크립트가 셌다 — `vet` 줄의 **줄 번호**를 탐침 주석(`// pNN`)의 줄과 맞췄다.
- ★★★ **답한 13** — 값 리시버(p01) · 값 매개변수(p02 `Mutex`·p03 `WaitGroup`·p04 `Once`·p05 `RWMutex`) · `*p` 반환(p06) · 대입(p08) · `range` 값(p09) · 인터페이스에 담기(p11) ·
  **`atomic.Int64` 복사(p13 — `sync/atomic.noCopy`)** · 배열째(p15) · 함수 리터럴 매개변수(p16) · 맵의 포인터 역참조(p17).
  ★ `WaitGroup`·`Once`·`atomic.Int64` 는 문구가 **「contains sync.noCopy」** 다 — 락이 아닌데도 **`noCopy` 표식**을 품어 같은 분석기에 걸린다.
- ★★★ **침묵한 5** — 그중 **넷은 옳은 침묵**이다: p07 `return Counter{}`(새로 만든 값) · p10 `&s[i]`(포인터) · p14 `c := fresh()`(**호출 결과**를 받기) · p18 `&a`(포인터).
  ★★★ **p12 `ch <- a`(채널로 보내기)만 진짜 놓친 칸**이다 — 채널 송신은 **값을 복사하는데** `vet` 이 답하지 않았다.
  ★ 그래서 「`vet` 이 조용하면 복사가 없다」가 아니다 — **18 개를 물어 13 개가 답했고, 놓친 1 개가 무엇인지**가 이 절의 결론이다.
- ★★ **컴파일러는 18 개 전부 통과시킨다** — `vet exit=1` 은 **`vet` 의** 종료 코드다. `go build` 는 이 파일을 **그대로 빌드한다**(그래서 이 규칙은 **문서의 계약 + 도구의 휴리스틱**이다).

**C++ 는 컴파일러가 막는다** —

```cpp
// t32copy.cpp
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

- ★★★ **`error: use of deleted function 'std::mutex::mutex(const std::mutex&)'`** · `mutex(const mutex&) = delete;` — C++ 는 **복사 생성자를 지운** 타입이라 **컴파일이 안 된다**(exit 1). 구조체째 복사(12행)도, 값으로 넘기기(13행)도.
- ★★★ **Go 에는 「복사 금지」를 타입에 적는 문법이 없다** — 모든 구조체가 대입으로 복사된다([16번 주제](../16-pointers-value-copy-semantics-new-and-make/)). 그래서 **표식 + `vet`** 이라는 우회로를 쓴다:

```text
===== 명령: sed -n "113,120p" "$(go env GOROOT)/src/sync/cond.go" =====
// noCopy may be added to structs which must not be copied
// after the first use.
//
// See https://golang.org/issues/8005#issuecomment-190753527
// for details.
//
// Note that it must not be embedded, due to the Lock and Unlock methods.
type noCopy struct{}
(exit 0)
```

  ★★ **`type noCopy struct{}`** — 필드가 **없는** 구조체다. 「**noCopy may be added to structs which must not be copied after the first use**」 — 컴파일러에게는 아무 뜻이 없고 **`vet` 만** 알아본다.

비용 — 없다.

### (4) ★★★ `WaitGroup.Add` 를 고루틴 안에서 — `vet` 은 잡고, `-race` 는 어떤 판만

**언제 쓰나** — `wg.Add(1)` 을 **어디에** 두나. 유명한 함정이다.

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

- ★★★ **`WaitGroup.Add called from inside new goroutine`**, exit 1 — 이 판 `vet` 의 **`waitgroup` 분석기**가 **정적으로** 잡았다. 매번 같다.

실제로 돌리면 —

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

그림 해설 (한 단계씩):

- ★★★ **「20판 중 100 이 아닌 판이 있었나 : 예」** — `wg.Wait()` 가 **고루틴들이 `Add` 를 부르기도 전에** 카운터 0 을 보고 돌아왔다. 100 개를 다 못 기다렸다.
- ★★★ **「-race 가 한 판이라도 보고했나 : 예」 · 「20판 모두 보고했나 : 아니오」** — **같은 바이너리가 어떤 판은 잡고 어떤 판은 못 잡았다.**
  `-race` 는 **이번 실행에서 실제로 순서가 어긋난 접근**만 본다. 운이 좋으면(모든 `Add` 가 `Wait` 보다 먼저 돌면) **아무것도 안 보인다.**
  ★ **몇 판이었나는 흔들린다** — 블록에는 참거짓만 실었다.
- ★★ 보고할 때는 이런 모양이다 —

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

  ★★ **`runtime.racewrite()` · `<autogenerated>:1`** — 사용자 코드의 줄이 아니라 **`WaitGroup` 내부에 심어 둔 검출기 표식**이 걸렸다. 「`Wait` 와 `Add` 사이에 순서가 없다」를 그렇게 알린다.
  ★ 「Goroutine N (finished) created at: … ex/t32wgadd.go:13」 — 어느 `go` 문의 고루틴인지는 알려 준다.
- ★★ **같은 코드가 세 번째 얼굴도 가진다** — 판을 더 돌리면 **라이브러리 자신이 패닉**하는 판이 나온다:

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

  ★★ **`panic: sync: WaitGroup is reused before previous Wait has returned`** — `Wait` 가 0 을 보고 돌아오는 **도중에** 다른 고루틴의 `Add` 가 끼어든 것을 `WaitGroup` 이 알아챘다. **드물다**(탐색 실행에서 `-race` 빌드 300판 중 한 자릿수 판 — 그 수는 블록에 안 실었다). 그래서 이 블록은 **「날 때까지 최대 400판」** 으로 찾았다.
  ★ 결과가 **틀리거나 · `-race` 가 보고하거나 · 패닉하거나** — 한 함정이 판마다 다른 모습이다. 그래서 **매번 같은 답을 주는 창**(`vet`)이 필요하다.
- ★★★ **그래서 이 함정에는 `vet` 이 더 좋은 창이다** — 정적이라 **매번** 잡는다. `-race` 는 **확률적**이다.
- 고치는 법 — **`go` 앞에서 `wg.Add(1)`**, 또는 1.25 의 **`wg.Go(f)`**(`Add` + `go` + `defer Done` 을 한 번에 — [28번 주제](../28-goroutines-go-statement-cost-and-termination/) (2)절의 문서 「If the WaitGroup is empty, Go must happen before a WaitGroup.Wait」).

비용 — 없다.

### (5) ★★ `Once` — 100 고루틴이 불러도 한 번

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

- ★★★ **초기화 함수가 돈 횟수 1 · 준비된 값을 본 고루틴 수 100 / 100** — `-race` 빌드에서 보고 0 줄.
  `once.Do` 가 돌아온 **모든** 고루틴은 초기화가 **끝난 뒤의** `config` 를 본다 — 문서:

```text
===== 명령: go doc sync.Once.Do | sed -n "19,20p" =====
    Because no call to Do returns until the one call to f returns, if f causes
    Do to be called, it will deadlock.
(exit 0)
```

  ★★ 「**no call to Do returns until the one call to f returns**」 — 그래서 **초기화 중에 `Do` 를 또 부르면 교착**이다(같은 문장의 뒷부분 — 이 문서는 **안 던졌다**).
  ★ 그래서 `config` 에 락이 없어도 경쟁이 아니다 — 순서를 `Once` 가 세운다.
- ★★ **`OnceValue`(1.21) 두 번 — `42 42`, 누적 호출 2** — `Do` 의 1 번 + `OnceValue` 의 1 번. 두 번 불렀는데 **함수는 한 번**만 돌았다.
- ★ 안 흔들린다 — 100 고루틴의 도착 순서와 무관하게 **1 과 100** 이다.

비용 — 없다.

### (6) ★★★ `Mutex` 는 재진입이 안 된다 — 같은 고루틴이 두 번 잠그면

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

- ★★★ **`첫 Lock` 뒤 `fatal error: all goroutines are asleep - deadlock!`**, 상태 줄 **`goroutine 1 [sync.Mutex.Lock]:`**, exit 2 — **자기 자신을 기다린다.**
  Go 의 `Mutex` 는 **누가 잠갔는지 기억하지 않는다**((8)절) — 그러니 「같은 사람이면 들여보낸다」가 원리상 없다.
- ★★ 트레이스가 **`internal/sync.(*Mutex).lockSlow`** 를 지난다 — 이 판의 `sync.Mutex` 는 `internal/sync` 에 구현이 있다(**구현**이다).

**자바 `synchronized` 는 들어간다** —

```java
// J32Reentry.java
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

- ★★★ **`inner 안: holdsLock=true` · `outer 뒤 줄`** — 같은 스레드가 **같은 모니터에 다시 들어갔다.** 자바 모니터는 **재진입**이다.
  정본은 [`../../../java/syntax/33-synchronized-and-volatile/`](../../../java/syntax/33-synchronized-and-volatile/) (6)절(재진입 계수까지 실측).
- ★★ **Go 에서 같은 모양을 쓰려면** — 잠근 채 부를 내부 함수를 **「잠금이 이미 잡혀 있다고 가정하는」 버전**(`incLocked`)으로 나누는 것이 관례다. 이 문서는 **그 패턴을 블록으로 안 던졌다.**

비용 — 없다.

### (7) ★★★ `RWMutex` 의 재귀 읽기 잠금 — 쓰는 쪽이 끼면 교착

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

- ★★★ 「**If any goroutine calls RWMutex.Lock while the lock is already held by one or more readers, concurrent calls to RWMutex.RLock will block until the writer has acquired (and released) the lock … Note that this prohibits recursive read-locking.**」
  **쓰는 쪽이 굶지 않게** 하려는 규칙이, 같은 고루틴의 **둘째 `RLock`** 을 막는다.

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

- ★★★ **`alone` — 둘째 `RLock` 이 찍혔고 exit 0**(쓰는 쪽이 없으면 재귀 읽기 잠금은 **된다** — 그래서 테스트에서 안 걸린다).
  **`writer` — 안 찍혔고 exit 2, 교착 탐지.** 트레이스 전문:

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

  ★★★ **`[sync.RWMutex.RLock]`(main 의 둘째 RLock) · `[sync.RWMutex.Lock]`(쓰는 고루틴)** — 도식 그대로 **서로 기다린다.**
- ★★ **「평소엔 되다가 쓰기 부하가 올 때만 멈춘다」** 가 이 함정의 무서운 점이다. 그리고 서버에서는 **교착 탐지가 안 온다**([29번 주제](../29-channels-buffering-direction-close-range-and-nil/) (8)절).
- ★ 50ms 잠은 **쓰는 쪽이 먼저 `Lock` 대기에 들어가게** 벌린 간격이다 — 재실행 대조에서 같은 결과였다.
- ★★★ **`RWMutex` 가 `Mutex` 보다 빠르다는 주장은 이 문서에 없다** — **안 쟀다.** 여기서 확인한 것은 **의미의 차이**(여럿이 읽기 · 재귀 금지)뿐이다.

비용 — 없다(재지 않았다).

### (8) ★ 뮤텍스에는 주인이 없다 — 그리고 안 잠근 것을 풀면

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

- ★★ **다른 고루틴이 푼 뒤 `TryLock: true`** — main 이 잠근 것을 **다른 고루틴이 풀었고**, `-race` 빌드에서 보고도 없다.
  문서가 그렇게 말한다:

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

  ★★ 「**A locked Mutex is not associated with a particular goroutine. It is allowed for one goroutine to lock a Mutex and then arrange for another goroutine to unlock it.**」
  ★ 첫 문장 「**It is a run-time error if m is not locked on entry to Unlock**」 — 아래 블록이 그 「run-time error」의 모양이다.
  ★ 쓸 수 있다는 것이지 **권하는 것이 아니다** — 잠근 쪽과 푸는 쪽이 갈리면 추적이 어렵다.

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

- ★★★ **`fatal error: sync: unlock of unlocked mutex`**, exit 2 — 그리고 **`defer` 안의 `recover()` 줄이 안 찍혔다.**
  **`panic` 이 아니라 `fatal error`** 라 [27번 주제](../27-panic-recover-and-where-to-use-them/)의 `recover` 가 **못 듣는다.** 되감기 없이 프로세스가 끝난다.
- ★ 트레이스의 `internal/sync.fatal` — 이 판의 구현 경로다.

비용 — 없다.

### (9) ★★★ 채널로 풀 문제 대 뮤텍스로 풀 문제 — 판단표(성능 주장 없이)

| 문제의 모양 | 고를 것 | 근거(이 배치에서) |
|---|---|---|
| **값·일감을 넘긴다**(생산 → 소비) · 소유가 옮겨 간다 | **채널** | [29번 주제](../29-channels-buffering-direction-close-range-and-nil/) — `close` + `range` 가 「끝」까지 전한다 |
| **여럿에게 「끝났다」를 한 번에** | **채널 `close`** | 29편 (4)절 — 닫힌 채널은 모든 받는 쪽을 깨운다 |
| **한 자리의 상태를 여럿이 고친다**(계수기·캐시·맵) | **`Mutex`** | (2)절 — `100000` |
| 읽기가 대부분인 공유 상태 | **`RWMutex`** — 단 **재귀 읽기 잠금 금지** | (7)절 — **의미**의 차이만 확인, 속도는 안 쟀다 |
| 여러 일이 **다 끝날 때까지** | **`WaitGroup`**(1.25+ `wg.Go`) | (4)절 · [28번 주제](../28-goroutines-go-statement-cost-and-termination/) |
| **한 번만** 초기화 | **`Once`·`OnceValue`** | (5)절 |
| 여러 채널을 기다리며 시간 상한 | **`select`** | [30번 주제](../30-select-default-and-timeouts/) |
| 정수 하나를 더하기만 | **`sync/atomic`** | 목록의 **33번 주제**(경계만) |

★★★ **이 표에 「빠르다·느리다」 칸이 없는 것이 의도다** — 이 배치는 **어떤 시간도 재지 않았다.** 고르는 기준은 **문제의 모양**이다.
★ 채널이 맞는 문제를 뮤텍스로 풀면 「끝」을 알리는 법이 따로 필요하고, 뮤텍스가 맞는 문제를 채널로 풀면 **상태를 쥔 고루틴 하나**를 만들어야 한다 — 이것은 **구조**의 비용이지 **실행 시간** 주장이 아니다.

### (10) ★ `sync/atomic` — 경계만

- (3)절 p13 — **`atomic.Int64` 도 복사하면 `vet` 이 잡는다**(`sync/atomic.noCopy`). 같은 「복사 금지」 계약이다.
- 원자 연산으로 **충분한 경우와 아닌 경우**, `sync.Map` 이 이기는 접근 패턴은 목록의 **33번 주제**가 정본이다 — 여기서는 **블록을 싣지 않았다.**

## 문법 — 형태와 규칙

### 형태

```go
// t32form.go
package main

import (
	"fmt"
	"sync"
)

// Cache 는 뮤텍스와 그것이 지키는 데이터를 한 구조체에 둔다.
type Cache struct {
	mu sync.RWMutex
	m  map[string]int // mu 가 지킨다
}

func (c *Cache) Get(k string) (int, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	v, ok := c.m[k]
	return v, ok
}

func (c *Cache) Set(k string, v int) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.m[k] = v
}

func main() {
	c := &Cache{m: map[string]int{}} // 포인터로 다룬다 — 복사하지 않는다
	var wg sync.WaitGroup
	for i := range 100 {
		wg.Go(func() { c.Set(fmt.Sprint(i%10), i) })
	}
	wg.Wait()
	n := 0
	for i := range 10 {
		if _, ok := c.Get(fmt.Sprint(i)); ok {
			n++
		}
	}
	fmt.Println("키 수:", n)
}
```

```text
===== 명령: go vet . && go build -race -trimpath -o prog . && ./prog =====
키 수: 10
(exit 0)
```

규칙 불릿.

- ★★★ **뮤텍스는 지키는 데이터 옆 필드로** 두고, **「mu 가 무엇을 지키나」를 주석으로** 적는다 — Go 는 그 관계를 **타입이 모른다.**
- ★★★ **`sync` 타입을 품은 구조체는 포인터로 다룬다** — 값 리시버·값 매개변수·대입이 **복사**다. `vet copylocks` 가 대부분 잡는다(18 중 13).
- **`Lock` 바로 다음 줄에 `defer Unlock`** — 패닉 경로까지 덮는다.
- **같은 고루틴에서 두 번 잠그지 않는다** — 재진입이 없다. `RWMutex` 도 **재귀 읽기 잠금 금지.**
- **`wg.Add` 는 `go` 앞에서**, 또는 **`wg.Go`**(1.25).
- **`Once.Do`·`OnceValue`** — 정확히 한 번, 돌아온 모든 호출자가 초기화 뒤를 본다.
- **안 잠근 것을 풀면 `fatal error`** — `recover` 로 못 잡는다.
- **제로값이 곧 쓸 수 있는 값**이다(`var mu sync.Mutex`) — 생성자가 필요 없다.

### 금지 사례 — 컴파일은 되고 도구·실행이 잡는 것

| 쓴 꼴 | 누가 잡나 | 어디서 |
|---|---|---|
| `func (c Counter) Get()` (값 리시버, `Counter` 가 `Mutex` 를 품음) | `vet` — `passes lock by value` | (3)절 p01 |
| `b := a` · `for _, v := range s` | `vet` — `assignment copies lock value` · `range var v copies lock` | p08·p09 |
| `ch <- a` | ★★★ **아무도 안 잡는다**(`vet` 침묵) | p12 |
| 동기화 없는 공유 쓰기 | `-race` — `WARNING: DATA RACE`(exit 66) · `vet` 은 침묵 | (1)절 |
| 고루틴 안의 `wg.Add(1)` | `vet waitgroup` 은 늘 · `-race` 는 어떤 판만 | (4)절 |
| 같은 고루틴에서 `Lock` 두 번 | 교착 탐지(곁에 아무도 없을 때만) | (6)절 |
| 쓰는 쪽이 끼는 재귀 `RLock` | 교착 탐지(〃) — **쓰는 쪽이 없으면 안 드러난다** | (7)절 |
| 안 잠근 `Unlock` | `fatal error: sync: unlock of unlocked mutex` | (8)절 |

## 어디서 틀리나

### 1. ★★★ 「값이 맞게 나왔으니 경쟁이 없다」

- (1)절 실측 — **`1` 이 나왔는데 `-race` 는 exit 66.** `time.Sleep` 은 동기화가 아니다.
- 고치는 법 — 공유 변수는 **락 안에서만.** 테스트는 **`go test -race`** 로.

### 2. ★★★ 「`-race` 가 조용했으니 경쟁이 없다」

- (4)절 실측 — **같은 바이너리가 20판 중 어떤 판만** 보고했다. `-race` 는 **이번 실행에서 본 것**만 말한다.
- 고치는 법 — `-race` 는 **여러 번·부하를 주며** 돌린다. 정적으로 잡히는 것(`vet`)은 정적으로 잡는다.

### 3. ★★★ 「`vet` 이 조용하면 락 복사가 없다」

- (3)절 실측 — **18 중 13.** **`ch <- a`(채널로 보내기)는 복사인데 침묵.**
- 고치는 법 — `sync` 타입을 품은 구조체는 **처음부터 포인터로만** 다룬다(`*Counter` 채널·슬라이스).

### 4. ★★★ 「같은 고루틴이면 다시 잠가도 된다」

- (6)절 실측 — **`[sync.Mutex.Lock]` 교착.** 자바와 다르다.
- 고치는 법 — 잠근 채 부를 함수는 **`…Locked` 버전**으로 나눈다.

### 5. ★★★ 「`RWMutex` 는 읽기끼리 안 막으니 읽기 안에서 또 읽기 잠금해도 된다」

- (7)절 실측 — **`alone` 은 되고 `writer` 는 교착.** 테스트에서 **쓰는 쪽이 없으면 안 걸린다.**
- 고치는 법 — **재귀 읽기 잠금을 하지 않는다**(문서 「prohibits recursive read-locking」).

### 6. ★★ 「`wg.Add(1)` 은 고루틴 첫 줄이 자연스럽다」

- (4)절 — `Wait` 가 먼저 0 을 볼 수 있다. **`vet` 이 늘 잡는다.**
- 고치는 법 — `go` 앞에서 `Add`, 또는 `wg.Go`.

### 7. ★★ 「`Unlock` 은 함수 끝에 쓰면 된다」

- (2)절 실측 — 패닉하면 **`TryLock: false`**(잠긴 채). **`defer`** 로.

### 8. ★★ 「채널이 느리니 뮤텍스를 쓴다」·「`RWMutex` 가 더 빠르다」

- ★★★ **이 배치는 안 쟀다.** 고르는 기준은 (9)절의 **문제의 모양**이다.

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| **`Unlock` 이 뒤의 `Lock` 보다 먼저(순서)** | **메모리 모델 보장** | (3)절 문서 |
| ★★★ **「must not be copied after first use」** | **표준 라이브러리 계약** | (3)절 |
| ★★★ **`RWMutex` 재귀 읽기 잠금 금지 · 쓰는 쪽이 기다리면 새 `RLock` 막힘** | **표준 라이브러리 계약** | (7)절 |
| **`Once` 정확히 한 번 · `OnceValue`(1.21) · `WaitGroup.Go`(1.25)** | **표준 라이브러리 계약** | (5)절 · [28번 주제](../28-goroutines-go-statement-cost-and-termination/) |
| **`Mutex` 는 고루틴에 묶이지 않는다 · 재진입 없음** | **표준 라이브러리 계약** | (6)·(8)절 |
| ★★★ **`copylocks`·`waitgroup` 분석** | ★ **도구(`vet`)의 휴리스틱** | 18 중 13 · `ch <- a` 침묵 |
| ★★★ **`-race` — 실행 중 본 접근만 · exit 66** | ★ **도구(검출기) — 판마다 다를 수 있다** | (1)·(4)절 |
| 안 잠근 `Unlock` 이 `fatal error` · `internal/sync` 구현 경로 | **구현(runtime)** | (8)절 |
| 교착 탐지 · `[sync.Mutex.Lock]` 문구 | **구현(runtime)** | (6)·(7)절 |
| 락의 **시간 비용** · `RWMutex` 대 `Mutex` | ★ **안 쟀다** | — |

## 언제 쓰고 언제 안 쓰나

(9)절의 판단표가 이 절이다. 덧붙여 —

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 공유 상태를 가진 타입 | **구조체에 `mu` 필드 + 포인터 리시버** | (3)절 |
| 잠근 채 내부 함수를 부른다 | **`…Locked` 버전으로 나누기** | (6)절 — 재진입 없음 |
| 테스트 | **`go test -race` + `go vet`** | (1)·(3)·(4)절 — 둘이 보는 것이 다르다 |
| 한 번의 비싼 초기화 | **`sync.OnceValue`** | (5)절 |

## 핵심 문장

- ★★★ **`-race` 가 이 판·이 머신에서 열린다**(`CGO_ENABLED=1`·`gcc 13.3.0`) — 동기화 없는 `n++` 은 **값이 `1` 로 맞았는데 exit 66, `Read … by main goroutine` / `Previous write … by goroutine N`.** `vet` 은 침묵했다.
- ★★★ **복사하면 안 되는 것 — `Mutex`·`RWMutex`·`WaitGroup`·`Once`(+ `atomic.Int64`)** — 컴파일러는 전부 통과시키고 **`vet copylocks` 가 18 탐침 중 13** 에 답했다. **`ch <- a` 는 복사인데 침묵.** C++ 는 **컴파일러가** 막는다.
- ★★★ **`WaitGroup.Add` 를 고루틴 안에서** — **`vet` 은 늘 잡고, `-race` 는 20판 중 어떤 판만** 잡는다. 결과가 100 이 아닌 판이 있다.
- ★★★ **재진입이 없다** — 같은 고루틴의 둘째 `Lock` 은 `[sync.Mutex.Lock]` 교착. **`RWMutex` 의 재귀 `RLock` 은 쓰는 쪽이 낄 때만** 교착한다(`alone` 은 된다).
- ★★ **`defer mu.Unlock()`** — 패닉 뒤 `TryLock: true` 대 `false`. **안 잠근 것을 풀면 `fatal error`** — `recover` 도 못 듣는다.
- ★★ **Go 는 뮤텍스와 데이터가 따로다** — Rust `Mutex<T>` 는 잠그지 않으면 **만질 수 없다**(`E0614`). Go 에서 그 관계를 검사하는 것은 **`-race` 뿐**이다.
- ★★ **채널 대 뮤텍스는 문제의 모양으로 고른다** — 넘기면 채널, 한 자리를 번갈아 고치면 뮤텍스. **이 배치는 속도를 재지 않았다.**

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 32번)
- [`../../../../process-thread/`](../../../../process-thread/) — ★★ **정본 경계.** **그쪽은 경쟁 조건·상호 배제·락의 원리까지**, 여기는 **Go `sync` 타입의 계약·복사 금지·함정부터.**
- [29번 주제](../29-channels-buffering-direction-close-range-and-nil/)(채널) — ★ 목록상 선행 · 채널 대 뮤텍스의 한쪽 · 교착 탐지의 한계
- [26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/)(`defer`) — `defer mu.Unlock()` 의 근거
- [27번 주제](../27-panic-recover-and-where-to-use-them/)(`panic`) — `fatal error` 는 `recover` 가 못 듣는다
- [28번 주제](../28-goroutines-go-statement-cost-and-termination/)(고루틴) — `WaitGroup.Go`(1.25) 판별의 정본
- [31번 주제](../31-goroutine-leaks/)(누수) — 띄운 쪽이 기다리기
- [16번 주제](../16-pointers-value-copy-semantics-new-and-make/)(값 복사) — 구조체 대입이 복사라는 것
- 목록의 **33번 주제**(`sync/atomic`·`sync.Map`) · **35번 주제**(데이터 레이스와 `-race` — ★ 검출기의 전모) · **36번 주제**(메모리 모델)
- [`../../../java/syntax/33-synchronized-and-volatile/`](../../../java/syntax/33-synchronized-and-volatile/) — ★ 자바 모니터는 **재진입** — Go 와 반대
- [`../../../cpp/syntax/15-raii-resources-as-types/`](../../../cpp/syntax/15-raii-resources-as-types/) — ★ `lock_guard` 가 예외 경로에서 락을 푼다((3)절) — Go 의 `defer` 자리
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **52번**(`Mutex`/`RwLock`) — 락이 데이터를 감싸는 타입

## 용어 풀이

- **`sync.Mutex`** — 상호 배제 락. 제로값이 풀린 락.
- **`sync.RWMutex`** — 읽기는 여럿, 쓰기는 혼자. 쓰는 쪽이 기다리면 새 읽기도 막힌다.
- **`sync.WaitGroup`** — 고루틴 여럿이 끝나길 기다리는 계수기. `Add`·`Done`·`Wait`, 1.25 `Go`.
- **`sync.Once`** — 함수를 정확히 한 번만 돌린다. `OnceValue`·`OnceFunc`(1.21)는 그 함수형.
- **재진입(reentrancy)** — 락을 쥔 쪽이 같은 락을 다시 잡을 수 있는 성질. Go `Mutex` 는 **없다.**
- **`noCopy`** — `vet copylocks` 가 알아보는 빈 표식 타입. `WaitGroup`·`Once`·`atomic.*` 가 품는다.
- **`-race`** — 데이터 경쟁 검출기를 붙여 빌드하는 플래그. cgo 가 필요하다. 경쟁을 보면 exit 66.
- **데이터 경쟁** — 동기화 없는 두 접근 중 하나가 쓰기인 것.
- **`TryLock`** — 막히지 않고 잠가 보는 메서드. 이 문서에서는 「풀렸나」를 묻는 창으로만 썼다.

---

## 더 들어가면

- ★ **`sync.Cond`** 는 **안 다뤘다.**
- ★ **`-race` 의 `GORACE` 설정**(`halt_on_error`·`exitcode`)은 **안 바꿨다** — 목록의 **35번 주제**.
- ★ **`Mutex` 의 기아 모드**(오래 기다린 고루틴에게 넘기는 구현)는 **구현**이고 **안 열었다.**
- ★★ 락·채널의 **시간 비용**은 **안 쟀다.**
- ★ `vet` 이 `ch <- a` 를 놓친 것이 **의도된 한계인지 버그인지**는 **확인 못 했다** — 분석기 소스를 안 열었다.

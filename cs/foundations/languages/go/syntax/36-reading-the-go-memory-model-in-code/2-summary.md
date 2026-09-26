# go/syntax/36 — Go 메모리 모델을 코드에서 읽기 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [The Go Memory Model](https://go.dev/ref/mem) — ★★★ **웹이 아니라 이 툴체인이 들고 있는 `$(go env GOROOT)/doc/go_mem.html`**(`Version of June 6, 2022` — (1)절 블록) **에서 줄 번호째 떴다.** 문서를 옮기지 않고 **규칙 문장만** 인용한다.
> `sync.WaitGroup` 문서(`go doc`) · [Go 1.19 릴리스 노트](https://go.dev/doc/go1.19)(메모리 모델 개정 — 웹).\
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> ★ **버전** — 지금의 메모리 모델 문서는 **2022-06-06 판**이고, Go 1.19 릴리스 노트가 「**revised to align Go with the memory model used by C, C++, Java, JavaScript, Rust, and Swift**」 · 「**Go only provides sequentially consistent atomics**」라고 적는다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체는 넷째 창이다** — 「**순서를 만드는 연산을 하나씩 끼워 넣고 `-race` 가 침묵하나를 칸마다 찍는 격자**」.
메모리 모델은 **「무엇이 happens-before 를 만드나」의 목록**이다. 그 목록을 **읽기만** 하면 외울 거리이고, **칸마다 던지면** 「목록에 없는 것(잠·고루틴 종료·버퍼 채널의 반대 방향)은 순서를 안 만든다」가 **보고로** 보인다 — 마지막 줄 **`보고 없이 끝난 칸 9 / 13`**((2)절).
★★★ 그리고 **「잘 돌아가더라」가 왜 근거가 아닌가**를 **거꾸로** 보였다 — 동기화 없는 플래그 폴링이 **이 판에서는 6칸 전부 끝났다**(`끝나지 않은 칸 0 / 6`, (3)절). **문서는 「끝난다는 보장이 없다」고 적는다.** 끝난 것은 **이 컴파일러가 매번 다시 읽기 때문**이지 **언어가 약속해서가 아니다.**

★★★ **이 주제의 경계** — 레이스 **검출기**가 무엇을 보고 무엇을 못 보나는 [35번 주제](../35-data-races-and-the-race-detector/)가 정본이다. 여기서는 그 검출기를 **「순서가 섰나」를 묻는 창**으로만 쓴다.
`sync` 타입의 계약은 [32번 주제](../32-sync-mutex-rwmutex-waitgroup-once/), 원자 타입은 [33번 주제](../33-sync-atomic-and-sync-map/)가 정본이다 — 여기서는 그것들이 **순서를 만든다는 문장**만 본다.
★ 가시성·원자성의 **일반 원리**는 [`../../../../process-thread/`](../../../../process-thread/)가 다룬다(경쟁 조건·상호 배제까지 — 메모리 모델은 그 문서에 없다).

## 이 갈래가 쓰는 세 층 — ★ 이 편에서는 문서가 곧 명세다

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **메모리 모델(명세)** | `go_mem.html` 이 정한 것 | ★★★ **「synchronized before」 규칙 목록**((1)절 블록) · ★★★ 「**The loop in main is not guaranteed to finish**」 · 컴파일러에 대한 제한(쓰기를 지어내지 말 것 …) |
| **구현(gc 컴파일러·runtime·검출기)** | 이 판이 실제로 한 것 | ★★★ **gc 는 플래그 루프에서 매번 메모리를 다시 읽는다**(`CMPB main.done(SB)` 이 루프 안) · 검출기가 순서 없는 접근을 보고 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | `0 / 6` · `9 / 13` · 20판 `hello` |

★★★ **선을 가장 날카롭게 긋는다** — **「이 판에서 끝났다」(관찰)** 와 **「끝난다」(보장)** 는 다른 문장이다.
(3)절의 `0 / 6` 은 **관찰**이고, 그 옆에 문서가 「**보장이 없다**」 고 적은 문장을 **나란히** 싣는다. 둘이 **모순이 아니다** — 문서는 **허용 범위**를, 관찰은 **그중 한 점**을 말한다.
C 는 **같은 모양의 루프를 gcc 가 읽지 않고 영원히 돌게 만들고 clang 이 통째로 지웠다**([C 32편](../../../c/syntax/32-what-volatile-actually-guarantees/) (1)절). 자바는 **JIT 가 플래그를 못 보게 해 5 / 5 안 멈췄다**([자바 33편](../../../java/syntax/33-synchronized-and-volatile/) (3)절). **Go 의 「된다」는 그 둘과 같은 허용 범위 안의 다른 한 점**이다.

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다(그래서 안 실었다)** | 경쟁 칸이 **찍은 값** · 보고 전문의 주소·고루틴 id | 격자는 **보고 예/아니오와 종료 코드**만 싣는다 |
| 안 흔들린다 | ★★★ **HB 격자의 `-race 보고=예/아니오` · `9 / 13`** | 재실행 대조에서 같았다. 경쟁 칸도 **순서가 없다는 사실**은 매번 같다 |
| 안 흔들린다 | ★★★ **폴링 격자의 `0 / 6` · 어셈블리의 명령 줄** | 같은 컴파일러·같은 소스 |
| 안 흔들린다(단 관찰) | ★★ **20판 `hello` 가 아닌 판 : 아니오** | ★ **이 칸은 보장이 아니다** — (4)절. 이 판에서 20판 같았을 뿐이다 |

★ 정규화 규칙은 **기본 넷**만 썼다 — 이 편의 블록에는 보고 전문이 실리지 않는다.

## 한눈에 — 쉽게 말하면

**메모리 모델은 「택배 영수증 규칙」이다.** 내가 상자에 물건을 넣고 **영수증을 건넸으면**(채널로 보냈으면), 영수증을 **받은** 사람은 상자 안의 물건을 **반드시** 본다.
영수증 없이 「**아마 넣었겠지, 시간이 좀 지났으니까**」 하고 상자를 열면 — 대개는 들어 있다. 그런데 **규칙은 그것을 약속하지 않는다.**
**영수증이 되는 것**은 정해져 있다 — 채널 송수신 · 닫기 · 락 풀기/잠그기 · `Once` · `WaitGroup` · 원자 연산 · `go` 문. **기다린 시간은 영수증이 아니다.**

| 비유 | 실체 |
|---|---|
| 영수증을 건네고 받는다 | ★★★ **채널 송신 → 대응하는 수신 완료**((2)절 `send`) |
| 가게 문 닫힘 공지 | ★★ **`close` → 닫혀서 영값을 받는 수신**(`close`) |
| 열쇠를 반납하고 다음 사람이 받는다 | ★★ **`Unlock` → 다음 `Lock` 반환**(`mutex`) |
| 「한참 기다렸으니 됐겠지」 | ★★★ **`time.Sleep` 은 영수증이 아니다**(`sleep` — 보고) |
| 「배달원이 퇴근했으니 됐겠지」 | ★★★ **고루틴이 끝난 것은 영수증이 아니다**(`goexit` — 보고) — 문서 「The exit of a goroutine is not guaranteed to be synchronized before any event」 |
| 사물함(버퍼 1칸)에 넣고 가 버림 | ★★★ **버퍼 채널은 반대 방향 영수증이 없다**(`recvbuf` — 보고) |
| 영수증 없이 문 앞에서 계속 들여다보기 | ★★★ **평범한 플래그 폴링** — 이 판에서는 끝났다(`0 / 6`), **규칙은 안 약속한다** |

```text
   ★★★ happens-before 를 만드는 것 — 13칸 ((2)절의 실측, -race 빌드)
        고루틴:  data = 1 ; [ X ]          main:  [ Y ] ; data 읽기

   X (고루틴 쪽)               Y (main 쪽)                     문서 규칙                    -race
   ─────────────────────────   ─────────────────────────────   ──────────────────────────   ─────
   (없음)                       time.Sleep(100ms)                —                            보고
   (끝남)                       NumGoroutine 이 1 될 때까지        goroutine 종료는 순서 아님     보고
   flag = true                 for !flag {}                     —                            보고
   flag.Store(true) (atomic)   for !flag.Load() {}              원자 A 를 B 가 보면            침묵
   ch <- 0                     <-ch            (버퍼 0)          송신 → 수신 완료               침묵
   ch <- 0                     <-ch            (버퍼 1)          송신 → 수신 완료               침묵
   close(ch)                   <-ch                             close → 영값 수신              침묵
   <-ch            (버퍼 0)     ch <- 0                          수신 → 송신 완료 (버퍼 0)       침묵
   <-ch            (버퍼 1)     ch <- 0 ; Sleep                  k번째 수신 → k+C번째 송신       ★ 보고
   mu.Unlock()                 mu.Lock()                        n번째 Unlock → m번째 Lock      침묵
   once.Do(f)                  once.Do(f)                       f 완료 → 모든 Do 반환          침묵
   wg.Go(f)                    wg.Wait()                        Done → Wait 반환              침묵
   (main 이 먼저 쓰고) go f()     f 안에서 읽기                     go 문 → 고루틴 시작            침묵

   → 보고 없이 끝난 칸 9 / 13
```

> **happens-before** — 「이 사건의 효과가 저 사건에서 **반드시 보인다**」는 관계. 같은 고루틴 안의 순서(sequenced before)와 고루틴 사이의 동기화(synchronized before)로 만들어진다.

> **synchronized before** — 문서가 **고루틴 사이**의 순서를 정하는 말. 「송신은 대응하는 수신 완료보다 synchronized before」처럼 **연산 짝마다** 규칙이 있다.

- ★★★ [35번 주제](../35-data-races-and-the-race-detector/) (1)절의 `apart` 칸 — **300ms 떨어져도 레이스.** 그 칸이 「시간은 순서가 아니다」의 한쪽이고, 이 편 (2)절은 **무엇이 순서인가**의 다른 쪽이다.
- ★★ [29번 주제](../29-channels-buffering-direction-close-range-and-nil/)가 채널의 **차단 규칙**을, [32번 주제](../32-sync-mutex-rwmutex-waitgroup-once/)가 `Mutex`·`Once` 의 **계약**을 이미 인용했다 — 여기서는 그 규칙이 **메모리 순서를 만든다**는 쪽만 본다.

## 이 주제가 답하려는 질문

1. **어떤 연산이 happens-before 를 만들고, 어떤 것은 그럴듯해 보여도 안 만드나.**
2. **「잘 돌아가더라」는 왜 근거가 아닌가** — 이 판에서 도는 것과 문서가 허용하는 것의 차이.
3. **컴파일러는 메모리 모델 때문에 무엇을 못 하나** — 그리고 이 판의 gc 는 실제로 무엇을 했나.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **HB 격자 × `-race` 침묵** | **무엇이 순서를 만드나** — 13칸 | ★ 본체 창 — `9 / 13` 을 스크립트가 센다 |
| ★★★ **`go_mem.html` 원문 줄** | 규칙 문장 · 「끝난다는 보장 없음」 | 이 툴체인 — **웹이 아니다** |
| ★★ **폴링 격자 — 최적화 켬/끔 × 세 모양** | 이 판에서 **끝나나** | 규칙 24(판 격자) |
| ★★ **`-gcflags=-S` 어셈블리** | 루프 안에 **로드가 있나** | [C 32편](../../../c/syntax/32-what-volatile-actually-guarantees/)의 본체 창과 같은 자리 |
| ★ **20판 참거짓** | 공개(publication) 모양이 이 판에서 맞게 보이나 | [28번 주제](../28-goroutines-go-statement-cost-and-termination/)의 방식 |
| **부적용 — 약한 메모리 순서의 하드웨어** | ★★ 이 머신은 **amd64(x86-64)** 다. **ARM 같은 약한 순서 CPU 에서 `msg` 가 비어 보이는가**는 **이 머신에서 못 잰다**(에뮬레이터도 없다 — 아래 판별 블록) | 제3의 상태 |
| **부적용 — 시간** | 동기화 연산의 **비용**은 안 쟀다 | — |

```text
===== 명령: for t in qemu-aarch64 qemu-arm; do if command -v $t >/dev/null; then echo "$t: 있음"; else echo "$t: 없음"; fi; done; echo "uname -m: $(uname -m)" =====
qemu-aarch64: 없음
qemu-arm: 없음
uname -m: x86_64
(exit 0)
```

### (1) ★★★ 문서가 말하는 것 — 규칙 문장과 「조언」

먼저 판과 **검출기에 대한 허락**, **컴파일러에 대한 제한**:

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

- ★★ **`Version of June 6, 2022`** — 이 툴체인이 들고 있는 판.
- ★★★ 「**Any implementation can, upon detecting a data race, report the race and halt execution of the program. Implementations using ThreadSanitizer (accessed with "go build -race") do exactly this.**」 — 문서가 **`-race` 를 이름으로** 부른다. 그래서 이 편은 `-race` 를 **「순서가 섰나」의 창**으로 쓸 수 있다.
  ★ 「do exactly this」는 **halt** 까지 말하지만, [35번 주제](../35-data-races-and-the-race-detector/) (2)절 실측에서 **기본값은 보고하고 계속 갔다**(`halt_on_error=1` 이라야 멈춤). **문서의 문장과 이 판의 기본 동작이 한 칸 다르다.**
- ★★★ 「**a compiler must not introduce writes that do not exist in the original program, it must not allow a single read to observe multiple values, and it must not allow a single write to write multiple values.**」 — 메모리 모델은 **프로그램뿐 아니라 컴파일러도** 묶는다.
  ★★ 마지막 줄 — 「**Not introducing data races also means not assuming that loops terminate.**」 — 컴파일러는 **루프가 끝난다고 가정하고** 뒤의 접근을 앞으로 당기면 안 된다.
  ★★ 그런데 **「루프 안의 읽기를 루프 밖으로 끌어올리지 말라」는 이 세 금지에도 없다** — 레이스가 없는 프로그램에서 그 읽기는 **바뀔 수 없으니까**. (3)절이 그 빈칸 위에 있다.

**규칙 문장** — 무엇이 순서를 만드나:

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

- ★★★ **순서를 만드는 것** — `go` 문 → 고루틴 시작 · 송신 → 수신 완료 · `close` → 영값 수신 · (버퍼 0) 수신 → 송신 완료 · **k번째 수신 → k+C번째 송신** · n번째 `Unlock` → m번째 `Lock` · `once.Do(f)` 의 `f` 완료 → 모든 `Do` 반환 · 원자 A 를 B 가 보면 A → B.
- ★★★ **순서를 안 만드는 것이 목록에 한 줄 있다** — 「**The exit of a goroutine is not guaranteed to be synchronized before any event in the program.**」 고루틴이 **끝났다는 사실**로는 아무것도 못 본다.
- ★★ 마지막 줄 — 「**same semantics as C++'s sequentially consistent atomics and Java's volatile variables**」. 자바의 `volatile` 은 **순서를 만든다** — [C 32편](../../../c/syntax/32-what-volatile-actually-guarantees/) (9)절이 **C 의 `volatile` 은 순서를 안 막는다**고 쟀다. ★ **이름만 같다** — Go 의 원자 연산은 **자바 `volatile` 쪽**이다.
- ★ `WaitGroup` 은 메모리 모델 문서가 아니라 **자기 문서**에 적는다(문서 「Additional Mechanisms」가 그렇게 넘긴다):

```text
===== 명령: go doc sync.WaitGroup.Done | sed -n "9,10p" =====
    In the terminology of the Go memory model, a call to Done "synchronizes
    before" the return of any Wait call that it unblocks.
(exit 0)
```

그리고 문서 첫머리의 **조언**:

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

- ★★★ 「**If you must read the rest of this document to understand the behavior of your program, you are being too clever. Don't be clever.**」 — 이 편의 결론이 이미 여기 있다. **규칙의 가장자리에서 줄타기하지 말고, 목록에 있는 연산을 쓴다.**

### (2) ★★★ happens-before 격자 — 13칸

**언제 쓰나** — 「이 두 고루틴 사이에 **무엇이** 순서를 세우나」를 코드 리뷰에서 물을 때. **모든 칸이 같은 모양**이다 — 고루틴이 `data = 1` 을 쓰고 **X** 를 하고, main 이 **Y** 를 하고 `data` 를 읽는다(`gostmt` 만 방향이 반대).

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

그림 해설 (한 단계씩):

- ★★★ **마지막 줄 `보고 없이 끝난 칸 9 / 13`.** 스크립트가 셌다. **침묵 9칸이 전부 (1)절 규칙 목록에 한 줄씩 대응한다** — 한눈에 절의 표.
- ★★★ **`sleep` — 보고.** 100ms 는 넉넉하다. 쓰기는 **거의 늘** 먼저 끝난다. 그래도 **순서가 아니다.**
- ★★★ **`goexit` — 보고.** main 은 `NumGoroutine` 이 1 이 될 때까지 기다렸다 — 고루틴이 **확실히 끝난 뒤**에 읽었다. 그래도 레이스다. 문서 「**The exit of a goroutine is not guaranteed to be synchronized before any event**」의 실측이다.
- ★★★ **`plainflag` — 보고**(`flag` 자체와 `data` 둘). **`atomicflag` — 침묵.** 모양이 **완전히 같은데** 깃발이 `atomic.Bool` 이냐만 다르다. 원자 `Store` 를 원자 `Load` 가 **보았으니** 그 앞의 `data = 1` 도 보인다.
- ★★ **`send`·`sendbuf`·`close` — 침묵.** 송신(또는 닫기)이 수신 **완료**보다 먼저다. **버퍼가 있어도** 이 방향은 선다.
- ★★★ **`recv`(버퍼 0) — 침묵, `recvbuf`(버퍼 1) — 보고.** 이번에는 **고루틴이 받고 main 이 보낸다.**
  버퍼 0 이면 「**수신 → 송신 완료**」 규칙이 있어 main 의 송신이 끝났을 때 고루틴의 `data = 1` 도 끝나 있다.
  **버퍼 1 이면 송신이 수신을 안 기다리고 바로 끝난다** — 규칙은 「**k번째 수신 → k+C번째 송신**」, 즉 **첫 수신은 둘째 송신**보다 먼저일 뿐이다. 첫 송신과는 **순서가 없다.**
  ★★ **같은 코드에 버퍼 크기 하나를 바꿨을 뿐인데 레이스가 생긴다** — 채널을 **세마포어처럼 거꾸로** 쓸 때의 함정이다.
- ★★ **`mutex`·`once`·`waitgroup` — 침묵.** `once` 칸은 main 이 `wg.Wait()` **전에** 읽었다 — `Once` **하나만으로** 순서가 섰다.
- ★★ **`gostmt` — 침묵.** main 이 **`go` 문 앞에서** 쓴 것은 새 고루틴이 본다(「The go statement … is synchronized before the start of the goroutine's execution」).

비용 — **안 쟀다.**

### (3) ★★★ 「잘 돌아가더라」 — 플래그 폴링이 이 판에서 끝나나

**언제 쓰나** — 「테스트해 보니 잘 끝나던데」를 근거로 쓰고 싶을 때. **문서가 먼저** 말한다(문서 자신의 예 뒤의 문단):

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

- ★★★ 「**Worse, there is no guarantee that the write to done will ever be observed by main, since there are no synchronization events between the two threads. The loop in main is not guaranteed to finish.**」

그러면 **이 판에서는?** — 전역·포인터·구조체 필드 세 모양 × **최적화 켬(기본) / 끔(`-N -l`)**:

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

그림 해설 (한 단계씩):

- ★★★ **`끝나지 않은 칸 0 / 6`** — **여섯 칸 전부 2초 안에 빠져나왔다**(걸린 시간은 안 쟀다).
  ★★★ 「**0 이 결론인 격자일수록 그 0 이 진짜인지 따로 물어야 한다**」(규칙 22) — 그래서 **왜 끝났는지**를 어셈블리로 확인했다:

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

- ★★★ **기본 빌드 — `CMPB main.done(SB), $0` · `JEQ 0`.** 루프가 **메모리의 `main.done` 을 매번 다시 읽는다**(0번 주소로 되돌아가 다시 `CMPB`). 레지스터에 한 번 올려 두고 도는 코드가 **아니다.**
  **`-N -l`** 도 같다 — 점프가 늘었을 뿐 **`CMPB main.done(SB)` 이 루프 안에** 있다.
  ★★★ **브리핑의 전제 하나가 여기서 갈렸다** — 「컴파일러가 루프에서 읽기를 끌어올린다」는 **이 판의 gc 에는 맞지 않았다**(전역·포인터·필드 셋 다 — 탐색에서 `-S` 로 셋 다 확인, 블록에는 전역만 실었다).
- ★★★ **그러면 「Go 에서는 된다」인가 — 아니다.**
  **gcc `-O2` 는 같은 모양을 `jmp .L3`(읽지 않고 영원히)로, clang 은 루프째 지웠다** — [C 32편](../../../c/syntax/32-what-volatile-actually-guarantees/) (1)절. **자바 JIT 는 5 / 5 안 멈췄다** — [자바 33편](../../../java/syntax/33-synchronized-and-volatile/) (3)절.
  **셋 다 각자의 메모리 모델이 허용하는 동작**이다. Go 의 문서도 **같은 허용**을 적는다(「not guaranteed to finish」). **이 판의 gc 가 그 허용을 안 썼을 뿐이다** — 다음 판의 최적화가 쓰면 **소스를 한 글자도 안 바꿨는데** 멈추지 않는다.
- ★★ **그리고 이 루프는 끝나는 판에서도 레이스다** — (2)절의 `plainflag` 칸이 **보고**했다. 「끝났다」와 「옳다」는 **다른 질문**이다.

```text
   ★★★ 문서가 허용하는 것 · 각 구현이 한 것 — 같은 「동기화 없는 폴링」

   메모리 모델(Go·C·Java 모두)   「끝난다는 보장이 없다」  ── 허용 범위
        │
        ├── Go gc 1.27.1 (이 편)    매번 CMPB main.done(SB)  → 6 칸 전부 끝났다
        ├── C gcc -O2 (C 32편)      한 번 읽고 jmp .L3       → 영원히
        ├── C clang (C 32편)        루프째 삭제 (ret)         → 기다리지도 않고 반환
        └── Java JIT (자바 33편)    플래그를 못 봄            → 5 / 5 안 멈춤

   → 「이 판에서 끝났다」는 허용 범위 안의 한 점이다. -race 는 어느 점이든 보고한다.
```

비용 — 없다.

### (4) ★★ 공개(publication) — 값을 쓰고 깃발을 세우면

**언제 쓰나** — 「값을 다 채운 **뒤에** 깃발을 세우니, 깃발을 본 쪽은 값도 본다」고 생각할 때.

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

- ★★ **보통 빌드 20판 — 「`hello` 가 아닌 판이 있었나 : 아니오」.** 이 판·이 CPU 에서는 **늘 맞게 보였다.**
- ★★★ 문서는 이 모양에 대해 「**could print an empty string too**」 라고 적는다((3)절 블록 첫 줄들) — **깃발을 봤다는 것이 값을 봤다는 것을 뜻하지 않는다.**
  x86-64 는 **쓰기 순서를 비교적 지키는** CPU 라 이 머신에서 빈 문자열을 보기는 어렵다 — ★ **약한 순서 CPU 에서의 모습은 못 쟀다**((0)절).
- ★★★ **`-race` 빌드 — exit 66, 보고 2 건**(`ready` 와 `msg`). 20판이 **아무리 맞아도** 검출기는 **순서가 없다**고 말한다.
- 고치는 법 — 깃발을 **`atomic.Bool`** 로((2)절 `atomicflag` 가 침묵), 또는 **채널 하나**로 값과 신호를 같이 보낸다.

비용 — 없다.

## 문법 — 형태와 규칙

순서를 만드는 연산 — (1)절 문서 블록의 요약.

| 앞(고루틴 A) | 뒤(고루틴 B) | 조건 |
|---|---|---|
| `go f()` 문 | `f` 의 시작 | 늘 |
| `ch <- v` | 대응하는 `<-ch` 의 **완료** | 늘(버퍼 무관) |
| `close(ch)` | 닫혀서 영값을 받는 `<-ch` | 늘 |
| `<-ch` | 대응하는 `ch <- v` 의 **완료** | ★ **버퍼 0 일 때만** — 버퍼 C 면 k번째 수신 → k+C번째 송신 |
| n번째 `mu.Unlock()` | m번째 `mu.Lock()` 반환(n < m) | 늘 |
| `once.Do(f)` 의 `f` 완료 | 모든 `once.Do(f)` 반환 | 늘 |
| `wg.Done()` | 그것이 깨운 `wg.Wait()` 반환 | `WaitGroup` 문서 |
| 원자 연산 A | A 의 효과를 **본** 원자 연산 B | 늘 · 전체가 순차 일관 |
| ★ 고루틴 종료 | — | ★★★ **아무것도 안 만든다** |
| ★ `time.Sleep` | — | ★★★ **아무것도 안 만든다** |

규칙 불릿.

- ★★★ **두 고루틴이 같은 변수를 만지고 하나라도 쓰면 — 위 표의 한 줄이 둘 사이에 있어야** 한다.
- ★★★ **「기다렸다」·「끝났다」·「매번 됐다」는 표에 없다.**
- ★★ **채널을 거꾸로(받는 쪽이 신호) 쓸 때는 버퍼 0** — 버퍼를 주면 그 방향의 순서가 사라진다.
- ★★ **깃발은 `atomic.Bool`** — 평범한 `bool` 폴링은 끝나도 레이스다.
- ★ 문서의 조언 — 「**Don't be clever.**」

## 어디서 틀리나

### 1. ★★★ 「테스트에서 잘 끝나니 플래그 폴링은 괜찮다」

- (3)절 — **이 판은 여섯 칸 전부 끝났다**(`끝나지 않은 칸 0 / 6`). 문서는 「**not guaranteed to finish**」. gcc `-O2` 와 자바 JIT 는 **같은 모양에서 실제로 멈추지 않았고**, clang 은 **루프를 지웠다.** 그리고 `-race` 는 **보고한다.**

### 2. ★★★ 「충분히 기다렸으니 보인다」

- (2)절 `sleep` — **100ms 뒤에도 레이스.** [35번 주제](../35-data-races-and-the-race-detector/) `apart` — 300ms.

### 3. ★★★ 「고루틴이 끝났으니 그 쓰기는 보인다」

- (2)절 `goexit` — **보고.** 끝남을 알리려면 **`WaitGroup`·채널**로.

### 4. ★★ 「채널로 신호를 주고받으면 방향도 버퍼도 상관없다」

- (2)절 `recv` 대 `recvbuf` — **버퍼 1 이면 받는 쪽 → 보내는 쪽 순서가 없다.**

### 5. ★★ 「깃발을 봤으면 깃발 앞의 값도 봤다」

- (4)절 — 평범한 `bool` 이면 **문서가 빈 문자열을 허용**한다. 이 머신에서 20판 맞은 것은 **관찰**이다.

### 6. ★★ 「Go 의 원자 연산은 C 의 `volatile` 같은 것」

- (1)절 — 문서는 **C++ 순차 일관 원자 · 자바 `volatile`** 과 같다고 적는다. C `volatile` 은 **순서를 안 막는다**(C 32편).

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| ★★★ **순서를 만드는 연산 목록 · 고루틴 종료는 순서 아님** | **메모리 모델(명세)** | (1)절 |
| ★★★ **동기화 없는 폴링 루프는 끝난다는 보장이 없다** | **메모리 모델(명세)** | (3)절 |
| 컴파일러는 쓰기를 지어내지 못한다 · 한 읽기가 두 값을 보게 못 한다 | **메모리 모델(명세)** | (1)절 |
| `Done` → `Wait` 반환 | **표준 라이브러리 계약** | (1)절 |
| ★★★ **gc 가 폴링 루프에서 매번 다시 읽는다(`CMPB main.done(SB)`)** | **구현(이 판의 gc)** | (3)절 어셈블리 |
| 6칸 전부 끝남 · 20판 `hello` | **이 판의 관찰** | (3)·(4)절 |
| `-race` 가 순서 없는 접근을 보고 · 기본은 계속 감 | **구현(검출기)** | (2)절 · 35편 |
| gcc·clang·JIT 가 같은 모양에서 멈추지 않음 | **다른 언어의 구현**(각 편 실측) | C 32 · 자바 33 |
| 약한 순서 CPU 에서의 모습 | ★ **못 잰 것** | (0)절 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 값을 넘기며 알린다 | **채널 송신** | (2)절 `send` |
| 여럿에게 「끝」 | **`close`** | `close` |
| 여러 일이 끝나길 | **`WaitGroup`** | `waitgroup` |
| 한 번 초기화 | **`Once`** | `once` |
| 멈춤 깃발 · 준비 깃발 | **`atomic.Bool`** | `atomicflag` |
| 공유 상태 | **`Mutex`** | `mutex` |
| 「조금 기다리면 되겠지」 | ★★★ **쓰지 않는다** | `sleep`·`goexit` |

## 핵심 문장

- ★★★ **happens-before 를 만드는 것은 목록이다** — 13칸 중 **목록에 있는 9칸이 침묵, 목록에 없는 4칸(잠·고루틴 종료·평범한 깃발·버퍼 채널의 반대 방향)이 보고**했다.
- ★★★ **고루틴이 끝난 것도, 100ms 를 기다린 것도 순서가 아니다** — 문서 「The exit of a goroutine is not guaranteed to be synchronized before any event」.
- ★★★ **버퍼 0 이면 수신 → 송신 완료, 버퍼 1 이면 그 방향이 없다** — 버퍼 크기 하나로 레이스가 생겼다.
- ★★★ **동기화 없는 플래그 폴링은 이 판에서 6 / 6 끝났다** — gc 가 **루프 안에서 매번 다시 읽기** 때문이다. **문서는 「끝난다는 보장이 없다」** 고 적고, gcc `-O2` 와 자바 JIT 는 같은 모양에서 **실제로 안 끝났다**(clang 은 루프째 지웠다).
- ★★ **「잘 돌아가더라」는 관찰이고 「끝난다」는 보장이다** — 둘을 가르는 것은 **문서의 문장**과 **`-race` 의 보고**다.
- ★★ **Go 의 원자 연산은 자바 `volatile`·C++ 순차 일관 원자와 같은 뜻**(문서) — C 의 `volatile` 은 순서를 안 막는다(C 32편). **「`volatile`」이라는 이름에 기대지 말고 문서의 규칙 목록에 기댄다.**

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 36번)
- [35번 주제](../35-data-races-and-the-race-detector/)(레이스와 `-race`) — ★★ **정본 경계.** 검출기가 **무엇을 못 보나**는 거기, 여기는 **무엇이 순서를 만드나**.
- [32번 주제](../32-sync-mutex-rwmutex-waitgroup-once/)(`sync`) · [33번 주제](../33-sync-atomic-and-sync-map/)(`atomic`) — 각 타입의 계약
- [29번 주제](../29-channels-buffering-direction-close-range-and-nil/)(채널) — 차단 규칙 · 메모리 모델 세 문장을 먼저 인용했다
- [`../../../c/syntax/32-what-volatile-actually-guarantees/`](../../../c/syntax/32-what-volatile-actually-guarantees/) — ★★ gcc `jmp .L3` · clang 루프 삭제 · `volatile` 은 순서를 안 막는다
- [`../../../java/syntax/33-synchronized-and-volatile/`](../../../java/syntax/33-synchronized-and-volatile/) — ★★ 자바 `volatile` 은 happens-before 를 만든다 · JIT 에서 평범한 플래그 5 / 5 안 멈춤
- [`../../../../process-thread/`](../../../../process-thread/) — 경쟁 조건·상호 배제 일반

## 용어 풀이

- **메모리 모델** — 한 고루틴의 쓰기가 다른 고루틴의 읽기에 **언제 보이는가**를 정한 규칙.
- **happens-before** — 효과가 반드시 보이는 「앞섬」 관계.
- **synchronized before** — 고루틴 사이의 앞섬. 동기화 연산 짝마다 정해져 있다.
- **sequenced before** — 한 고루틴 안의 프로그램 순서.
- **DRF-SC** — 데이터 레이스가 없으면(data-race-free) 순차 일관처럼 동작한다는 성질. 문서의 목표다(이 편은 그 절을 **인용하지 않았다**).
- **공개(publication)** — 값을 다 만든 뒤 다른 고루틴에 「이제 봐도 된다」를 알리는 것.
- **`CMPB`** — Go 어셈블리의 바이트 비교 명령. `CMPB main.done(SB), $0` 은 **메모리의 `done` 을 읽어** 0 과 비교한다.

---

## 더 들어가면

- ★ 문서의 「**Implementation Restrictions for Programs Containing Data Races**」 절(레이스가 있는 프로그램에 대해 구현이 지켜야 할 것)은 **첫 두 문단만** 인용했다.
- ★ **`sync.Cond`·`sync.Pool`·`runtime.SetFinalizer`** 의 순서 규칙은 **안 던졌다.**
- ★★ **약한 메모리 순서 CPU**(ARM)에서 (4)절이 빈 문자열을 내는지는 **못 쟀다.**
- ★ gc 가 **앞으로도** 루프 안에서 다시 읽을지는 **알 수 없다** — 이 문서가 보인 것은 **go1.27.1** 의 한 점이다.

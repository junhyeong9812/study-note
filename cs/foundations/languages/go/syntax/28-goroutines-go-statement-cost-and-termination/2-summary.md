# go/syntax/28 — 고루틴: `go` 문·시작 비용·종료 조건 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Go 명세 — Go statements · Program execution](https://go.dev/ref/spec#Go_statements) ·
> [`runtime`](https://pkg.go.dev/runtime) · [`sync.WaitGroup`](https://pkg.go.dev/sync#WaitGroup) 문서.
> 명세·`runtime` 소스·`api/go1NN.txt` 는 **이 툴체인의 `$(go env GOROOT)` 에서 직접 떴다.**\
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> ★★ **버전** — **루프 변수가 회차마다 새로 생기는 것이 1.22**((4)절 — **`go.mod` 판 격자로** 같은 소스를 두 번 던졌다) ·
> `sync.WaitGroup.Go` 가 **1.25**(`api/go1.25.txt:96`) · 정수 `range` 가 **1.22**.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체는 넷째 창이다** — 「**`main` 이 끝난 뒤의 출력 파일을 셸이 검사해, 「끝까지 안 찍혔다」만 참거짓으로 남기는 창**」.
고루틴이 **몇 줄 찍고 끊겼나**는 실행마다 흔들린다. **「끝 줄이 없다」·「`defer` 가 안 돌았다」는 안 흔들린다.**
흔들리는 것을 지우는 대신 **안 흔들리는 질문으로 바꿔** 물었다.
★ 그 짝으로 「**`runtime.NumGoroutine()` 으로 만든 수와 남은 수를 세는 창**」.

★★★ **이 주제는 동시성 묶음(28\~36)의 첫 편이다.** 여기서는 **`go` 문이 무엇을 만들고 언제 사라지나**까지만 본다.
기다리기(`sync`)·채널·누수·레이스는 뒤 번호가 정본이다 — **경계만** 긋는다.

★★★ **「시작 비용」은 재지 않는다.** 목록이 이 주제의 인출 목표에 「시작 비용」을 넣었지만,
**고루틴 단가의 논증은 [`../../언어-특성/README.md`](../../언어-특성/README.md) §2 가 정본**이다.
여기서는 **런타임 소스의 구현 상수를 인용**하고((5)절, **구현 층**으로 표시), **시간은 안 잰다.**
메모리는 판 격자로 **자릿수만** 확인했다 — ★ **「고루틴은 싸다」를 이 문서의 결론으로 쓰지 않는다.**

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | ★★★ `go` 문의 **함수 값·인자가 부르는 쪽 고루틴에서 평가** · **`main` 이 반환하면 다른 고루틴을 기다리지 않는다** · 반환값은 버려진다 |
| **구현(gc·runtime)·표준 라이브러리** | `runtime`·`sync` 가 한 것 | ★★ **스택 초기 크기**·스케줄링·고루틴 id — **전부 구현**이다 · `NumGoroutine`·`WaitGroup` 의 계약 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 실행 출력(재실행 대조까지) · `StackInuse` 의 자릿수 |

★★★ **선을 긋는다** — 「`go f()` 는 `f` 를 새 고루틴에서 돌리고 기다리지 않는다」는 **명세**,
「그 고루틴의 스택이 2KB 에서 시작한다」는 **구현**이다. **후자를 언어 사실로 적지 마라**((5)절 — 이 판은 **2KB 로 고정되지도 않는다**).

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다(그래서 안 실었다)** | ★★★ `main` 이 끝나기 전 고루틴이 **몇 줄 찍었나** | 스케줄링과 시간에 달렸다 — 블록에는 「**1000 미만인가**」 참거짓만 실었다 |
| **흔들린다(그래서 안 실었다)** | ★★ 고루틴 결과의 **도착 순서** | 정렬한 뒤 `uniq -c` 로 **가짓수**를 실었다(규칙 11) |
| **흔들린다(그래서 안 실었다)** | ★★ 고루틴당 `StackInuse` 증분의 **절댓값** | 블록을 만들기 전 탐색 실행에서 **1900\~2400 바이트 대로** 흔들렸다(그 값은 블록에 안 실었다) — 「**1024 이상 4096 미만인가**」 만 실었다(규칙 24) |
| 안 흔들린다 | ★★★ 「`고루틴 끝` 이 찍혔나 : 아니오」 · 「`defer` 가 돌았나 : 아니오」 | **명세**가 정한다 — `main` 이 반환하면 기다리지 않는다 |
| 안 흔들린다 | `NumGoroutine` 의 **101 · 11** | 막혀 있는 고루틴 수 — 만든 대로다 |
| 안 흔들린다 | 판 격자의 **가짓수**(`200 [3 3 3]` · `200 [0 1 2]`) | ★ 경쟁을 **없애고** 판의 의미만 남겼다((4)절) |
| 안 흔들린다 | 컴파일 에러의 `파일:줄:칸`과 문장 · 종료 코드 · 소스 줄 번호 | |

★ **정규화 규칙은 하나도 안 썼다.** 흔들리는 것은 **블록에 들어가기 전에 참거짓·가짓수로 접었다.**

## 한눈에 — 쉽게 말하면

**`go f()` 는 「이 일을 따로 맡겨 두고, 나는 기다리지 않고 간다」는 지시다.**
맡긴 일에 쓸 **재료는 지금 건네준다.** 그리고 **가게 주인(`main`)이 문을 닫으면** 맡긴 일이 어디까지 됐든 **전부 그 자리에서 끝난다.**

| 비유 | 실체 |
|---|---|
| 일을 맡기고 **뒤도 안 돌아보고** 간다 | ★★ **`go f()`** — 부르는 쪽은 `f` 가 끝나길 **기다리지 않는다** |
| 맡길 때 **재료를 지금 손에 쥐여 준다** | ★★★ **`go f(x)`** — 함수 값과 인자는 **부르는 쪽 고루틴에서 지금** 평가([26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/)의 `defer` 와 **같은 규칙**) |
| 주인이 문을 닫으면 **일하던 사람도 그 자리에서 사라진다** | ★★★ **`main` 반환 = 프로그램 종료.** 다른 고루틴을 **기다리지 않고**, 그들의 **`defer` 도 안 돈다** |
| 문 닫기 전에 **다 끝났는지 확인**한다 | ★ **`sync.WaitGroup`** — 동시성 묶음의 정본은 [목록의 **32번 주제**](../32-sync-mutex-rwmutex-waitgroup-once/) |
| 맡긴 일꾼이 **영영 안 오는 손님**을 기다린다 | ★ **고루틴 누수** — `NumGoroutine` 이 **안 줄어든다**. 정본은 [목록의 **31번 주제**](../31-goroutine-leaks/) |
| 일꾼 명단을 세어 본다 | **`runtime.NumGoroutine()`** — 지금 **있는** 고루틴 수 |

```text
   ★★★ main 이 반환하는 순간 — 기다리지 않는다 ((1)절의 실측)

   main 고루틴    ──▶ go func(){…}() ──▶ Sleep(20ms) ──▶ "main 끝" ──▶ return ──▶ 프로세스 종료
                           │                                              │
   새 고루틴               └─▶ 고루틴 1 · 고루틴 2 · … · 고루틴 k ─────────┘ ✂ 여기서 끊긴다
                               (k 는 실행마다 다르다 — 싣지 않는다)
                               "고루틴 끝"           ← 안 찍힌다 (안 흔들린다)
                               [고루틴 defer] 돌았다 ← 안 찍힌다 (안 흔들린다)
```

```text
   ★★★ go 문의 두 칸 — defer 와 같은 규칙 ((3)절 · 26번 (1)절과 나란히)

        go show("A", val("x", x), …)             go func() { … val("x", x) … }()
        ────────────────────────────             ───────────────────────────────
   go 문 val 이 「main 고루틴에서」 지금 돈다      함수 리터럴(값)만 만든다
        [평가] x = 1
   x = 2
   풀어 줌 [실행] A 가 받은 값 = 1                  새 고루틴이 그제야 x 를 읽는다
                                                 [평가] x = 2
                                                 [실행] B 가 읽은 값 = 2
```

```text
   ★★★ 루프 변수 × 고루틴 — go.mod 한 줄 ((4)절의 실측)

   for i := 0; i < 3; i++ { go func(){ <-start; out <- i }() }

   go 1.21  i 는 루프 전체에 하나 ──▶ 세 고루틴이 같은 i 를 본다 ──▶ 200판 전부 [3 3 3]
   go 1.22  i 는 회차마다 새로 ────▶ 셋이 각자 0·1·2 를 본다  ──▶ 200판 전부 [0 1 2]
```

> **고루틴(goroutine)** — 명세 「an independent concurrent thread of control … within the same address space」. `go` 문이 만든다.

> **`go` 문** — `go 호출식`. 명세 「The function value and parameters are evaluated as usual **in the calling goroutine**, but … program execution does not wait for the invoked function to complete.」

> **`runtime.NumGoroutine()`** — 「returns the number of goroutines that **currently exist**」. 막혀 있어도 센다.

- [12번 주제](../12-functions-multiple-returns-named-results-and-variadics/)가 목록상 **선행**이다 — 함수 값·호출식이 무엇인가.
- ★★ [26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/) (1)절 — **`defer` 의 인자가 등록 시점에 평가된다.** `go` 문도 **명세 문장이 같다**(「evaluated as usual」). (3)절이 같은 `val()` 창으로 확인한다.
- ★★ [13번 주제](../13-closures-variable-capture-and-loop-variable-change/) — **루프 변수 의미 변경(1.22)의 정본.** 거기서 `//go:build` 와 `go.mod` 두 레버로 이미 갈랐다.
  **여기는 그 변화가 고루틴에서 어떻게 드러나나**만 본다((4)절).
- 자바와 다른 점 — ★★ **자바 가상 스레드는 항상 데몬**이라 **`main` 이 끝나면 JVM 이 기다려 주지 않는다** —
  [`../../../java/syntax/56-virtual-threads/`](../../../java/syntax/56-virtual-threads/) (1)절이 「3초짜리 가상 스레드의 출력이 안 찍혔다」를 실측했다.
  **Go 의 고루틴과 같은 자리**다. 다만 자바의 **플랫폼 스레드**는 기본이 비데몬(같은 편 실측 `isDaemon=false`)이라 JVM 이 기다린다 — Go 에는 그런 「기다려 주는 고루틴」이 **없다.**

## 이 주제가 답하려는 질문

1. **`go f()` 가 만드는 것은 무엇이고, 무엇이 언제 평가되나.**
2. **`main` 이 끝나면 왜 다 사라지나** — 그리고 그 고루틴들의 `defer` 는?
3. **고루틴이 얼마나 있고 얼마나 남았나를 어떻게 보나** — 시작 비용은 무엇이 정하나(구현).

★ **스레드·프로세스 일반**(OS 스케줄링·컨텍스트 스위칭·경쟁 조건)은
[`../../../../process-thread/`](../../../../process-thread/)가 정본이다 — **그쪽은 스레드가 무엇이고 어떻게 스케줄되나까지**,
여기는 **Go 의 `go` 문이 만드는 것과 그 종료 조건부터.**
★ **고루틴 단가(왜 싼가, M:N 스케줄러)** 는 [`../../언어-특성/README.md`](../../언어-특성/README.md) §2 가 정본이다.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **출력 파일을 셸이 검사해 참거짓만 남기기** | `main` 이 끝나면 **끝까지 안 찍혔다** | ★ 본체 창 — 이 주제의 넷째 창 |
| ★★ **`runtime.NumGoroutine()`** | 만든 수 · 남은 수 · 안 줄어드는 수 | ★ 이 주제의 고유 창 |
| ★★ **`val()` 을 인자에 끼우기** | `go` 문의 인자가 **언제 평가되나** | [26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/)의 본체 창 |
| ★★★ **`go.mod` 판 격자 + `sort` + `uniq -c`** | 루프 변수 1.21 대 1.22 의 **가짓수** | [13번 주제](../13-closures-variable-capture-and-loop-variable-change/) (3)절의 격자 + 규칙 11 |
| ★ **`runtime` 소스 인용** | 스택 초기 크기가 **구현**이라는 것 | 정본 [`언어-특성/README.md`](../../언어-특성/README.md) §2 의 인용을 **이 판 소스로 재확인** |
| ★ **`runtime.MemStats` × `GODEBUG` 격자** | 고루틴당 스택 증분의 **자릿수** | 규칙 24 |
| **부적용 — 시간** | ★★★ **안 쟀다.** 「고루틴 하나 만드는 데 몇 ns」를 이 문서는 적지 않는다 — 논증의 정본이 따로 있다 | — |
| **부적용 — `-race`** | 이 문서의 블록은 **경쟁을 일부러 없앴다**((4)절의 `start` 채널). 레이스 검출기는 [목록의 **35번 주제**](../35-data-races-and-the-race-detector/) | — |

★★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.**
「`main` 이 끝나면 고루틴이 **어디까지 갔나**」는 원리상 **안정된 답이 없다.** 그래서 질문을 **「끝까지 갔나」로 바꿔** 물었다((1)절).
★ 바꾼 창의 한계 — **「몇 줄에서 끊겼나」의 분포**는 이 문서에 없다. 그것은 스케줄러 관찰이지 이 주제의 결론이 아니다.

### (1) ★★★ `main` 이 끝나면 — 끝까지 안 찍힌다

**언제 쓰나** — `go` 로 띄우고 **기다리지 않은** 코드를 볼 때.

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

그림 해설 (한 단계씩):

- ★★★ **`main 끝` 은 찍혔고, `고루틴 끝` 은 안 찍혔다.** 고루틴은 1000줄을 찍을 생각이었는데 **1000 미만에서 끊겼다.**
  ★ **몇 줄에서 끊겼나는 싣지 않았다** — 실행마다 다르다. 블록에 남은 것은 「**끝까지 안 갔다**」 하나다.
- ★★★ **`[고루틴 defer] 돌았다` 도 안 찍혔다** — `main` 이 반환하면 다른 고루틴은 **되감기도 없이** 사라진다.
  ★ [26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/) (6)절의 `os.Exit` 와 같은 결과다 — **`defer` 에 기대던 정리가 안 된다.**
- ★★ **종료 코드는 0** 이다 — 이것은 **실패가 아니다.** 명세가 그렇게 정했다.

```text
===== 명령: sed -n "6980,6990p;8440,8443p" "$(go env GOROOT)/doc/go_spec.html" | sed -e "s/<[^>]*>//g" =====

The function value and parameters are
evaluated as usual
in the calling goroutine, but
unlike with a regular call, program execution does not wait
for the invoked function to complete.
Instead, the function begins executing independently
in a new goroutine.
When the function terminates, its goroutine also terminates.
If the function has any return values, they are discarded when the
function completes.
Program execution begins by initializing the program
and then invoking the function main in package main.
When that function invocation returns, the program exits.
It does not wait for other (non-main) goroutines to complete.
(exit 0)
```

  ★★★ 「**When that function invocation returns, the program exits. It does not wait for other (non-main) goroutines to complete.**」
  ★ 윗 문단은 `go` 문 — 「**evaluated as usual in the calling goroutine**」·「**If the function has any return values, they are discarded**」. (3)·(6)절이 던진다.

비용 — 없다(재지 않았다).

### (2) ★★ 만든 수와 남은 수 — `NumGoroutine`

**언제 쓰나** — 「고루틴이 정리됐나」를 확인할 때. 테스트에서 누수를 잡는 가장 싼 창이다.

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

그림 해설 (한 단계씩):

- ★★ **시작은 1**(main 고루틴), **100개를 띄운 직후 101** — 모두 `<-release` 에 **막혀 있어도 센다.** 「currently exist」다.
- ★★ **`close(release)` 로 풀고 `wg.Wait()` 뒤에는 1 로 돌아왔다**(1초 안).
  ★ `Wait` 가 돌아온 **바로 그 순간**에 1 이라는 보장은 없다 — `Done` 을 부른 뒤 고루틴이 **실제로 사라지기까지** 틈이 있다. 그래서 **기다리며 확인**했다(`settle`).
- ★★★ **받을 쪽 없는 10개 뒤 11, 1초를 기다려도 1 로 안 간다**(`false`) — **고루틴 누수**다.
  `stuck` 채널을 아무도 안 닫으니 **영원히 막혀 있다.** GC 도 이것을 치우지 않는다.
  ★ 누수의 형태·테스트로 잡는 법의 정본은 [목록의 **31번 주제**](../31-goroutine-leaks/)다 — 여기는 「**`NumGoroutine` 이 안 줄어든다**」 까지.
- ★ **`wg.Go(func(){…})`** 는 **1.25** 의 새 메서드다 — `Add(1)` + `go` + `defer Done()` 을 한 번에 한다.

```text
===== 명령: grep -n "WaitGroup) Go" "$(go env GOROOT)/api/go1.25.txt"; go doc sync.WaitGroup.Go =====
96:pkg sync, method (*WaitGroup) Go(func()) #63796
package sync // import "sync"

func (wg *WaitGroup) Go(f func())
    Go calls f in a new goroutine and adds that task to the WaitGroup. When f
    returns, the task is removed from the WaitGroup.

    The function f must not panic.

    If the WaitGroup is empty, Go must happen before a WaitGroup.Wait.
    Typically, this simply means Go is called to start tasks before Wait is
    called. If the WaitGroup is not empty, Go may happen at any time. This means
    a goroutine started by Go may itself call Go. If a WaitGroup is reused to
    wait for several independent sets of tasks, new Go calls must happen after
    all previous Wait calls have returned.

    In the terminology of the Go memory model, the return from f "synchronizes
    before" the return of any Wait call that it unblocks.

[the Go memory model]: https://go.dev/ref/mem
(exit 0)
```

  ★★ 「**The function f must not panic.**」 — [27번 주제](../27-panic-recover-and-where-to-use-them/) (4)절대로 **다른 고루틴의 패닉은 못 잡으니** 그 고루틴 안에서 막아야 한다.
  `WaitGroup` 전체(`Add`·`Wait`·복사 금지)의 정본은 [목록의 **32번 주제**](../32-sync-mutex-rwmutex-waitgroup-once/)다.

```text
===== 명령: go doc runtime.NumGoroutine && go doc runtime.Goexit =====
package runtime // import "runtime"

func NumGoroutine() int
    NumGoroutine returns the number of goroutines that currently exist.

package runtime // import "runtime"

func Goexit()
    Goexit terminates the goroutine that calls it. No other goroutine is
    affected. Goexit runs all deferred calls before terminating the goroutine.
    Because Goexit is not a panic, any recover calls in those deferred functions
    will return nil.

    Calling Goexit from the main goroutine terminates that goroutine without
    func main returning. Since func main has not returned, the program continues
    execution of other goroutines. If all other goroutines exit, the program
    crashes.

    It crashes if called from a thread not created by the Go runtime.
(exit 0)
```

  ★ `runtime.Goexit` — **그 고루틴만** 끝내고 **`defer` 는 돌린다**(「Goexit runs all deferred calls」). `recover` 는 `nil` 을 준다.
  ★ 「**Calling Goexit from the main goroutine terminates that goroutine without func main returning.**」 — (1)절과 반대로 **다른 고루틴이 계속 돈다.** 이 문서는 **안 던졌다.**

비용 — 없다.

### (3) ★★★ `go` 문의 인자도 즉시 평가된다 — `defer` 와 같은 규칙

**언제 쓰나** — `go f(x)` 뒤에 `x` 를 바꿀 때.

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

그림 해설 (한 단계씩):

- ★★★ **`1)` 바로 아래 `[평가] x = 1`** — `go show("A", val("x", x), …)` 를 **지나는 순간, main 고루틴에서** `val` 이 돌았다.
  A 는 나중에 풀려나도 **1** 을 받는다.
- ★★★ **`2)` 아래에는 아무것도 없다** — 리터럴 몸통의 `val` 은 **새 고루틴이 풀려난 뒤에야** 돈다 → `[평가] x = 2`, B 는 **2**.
- ★★ **[26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/) (1)절과 한 글자도 다르지 않은 모양**이다 — 명세 문장이 둘 다 「**evaluated as usual**」이다.
  다른 것은 **실행 시점**뿐이다 — `defer` 는 「함수가 끝날 때」, `go` 는 「스케줄러가 돌릴 때」.
- ★ **경쟁이 없다** — `x = 2` 가 `close(readyB)` **전에** 일어나고 B 는 `<-readyB` **뒤에** 읽으니, 채널이 순서를 세운다.
  A·B 를 **차례로** 풀어 줘서 출력 순서도 고정했다. 이 보장의 정본은 [목록의 **36번 주제**](../36-reading-the-go-memory-model-in-code/)(메모리 모델)다.

비용 — 없다.

### (4) ★★★ 루프 변수 × 고루틴 — `go.mod` 판 격자

**언제 쓰나** — 루프 안에서 `go func(){ … i … }()` 를 쓸 때. **같은 소스를 `go.mod` 의 `go` 줄만 바꿔** 200판씩 던지고 **가짓수**를 셌다.

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

그림 해설 (한 단계씩):

- ★★★ **`go 1.21` — 200판 전부 `[3 3 3]`**, **`go 1.22` — 200판 전부 `[0 1 2]`.** 가짓수가 **각각 1**이다.
- ★★★ **소스·툴체인·빌드 명령이 같고 `go.mod` 한 줄만 다르다** — 차이는 「**모듈이 선언한 언어 판**」이다(컴파일러의 `-lang`).
  1.21 의미에서는 `i` 가 **루프 전체에 하나**라 세 고루틴이 같은 `i` 를 보고, 1.22 의미에서는 **회차마다 새 `i`** 다.
- ★★★ **왜 1.21 도 흔들리지 않나** — 고루틴이 **`<-start` 를 기다렸다가** 읽게 했다. `close(start)` 는 루프가 **끝난 뒤**라 그때 `i` 는 **3** 이고,
  채널이 순서를 세우니 **경쟁이 아니다.** ★ `start` 가 없으면 1.21 판은 **데이터 경쟁**이 되어 가짓수가 흔들린다 — 그건 이 주제가 아니라 [목록의 **35번 주제**](../35-data-races-and-the-race-detector/)(레이스)다.
- ★ **도착 순서는 흔들린다** — 그래서 `slices.Sort` 로 정렬한 뒤 찍었다(규칙 11). 정렬 전 순서는 **싣지 않았다.**
- ★★ 이 변화의 전모 — `//go:build go1.21` 로 **한 빌드 안에서 두 의미**를 나란히 낸 것, `go vet` 이 판을 아는 것 — 은
  [13번 주제](../13-closures-variable-capture-and-loop-variable-change/) (2)·(3)·(8)절이 정본이다.

비용 — 없다.

### (5) ★★ 시작 비용은 무엇이 정하나 — 구현 상수, 그리고 고정되지 않는다

**언제 쓰나** — 「고루틴 하나에 스택 몇 KB」라는 말을 들었을 때. ★ **이 절 전체가 구현 층이다 — 명세에는 스택 크기라는 말이 없다.**

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

그림 해설 (한 단계씩):

- ★★ **`stackMin = 2048`** — 「The minimum size of stack used by Go code」. [`언어-특성/README.md`](../../언어-특성/README.md) §2 가 인용한 그 상수가 **이 판 소스에도 같은 값**으로 있다.
- ★★★ **그런데 「새 고루틴이 2048 로 시작한다」는 이 판에서 고정된 사실이 아니다** — 브리핑의 전제를 이 소스가 뒤집었다.
  `startingStackSize` 의 주석 「**the amount of stack that new goroutines start with … is updated every GC by tracking the average size of stacks scanned during the GC**」,
  그리고 `runtime1.go:397` 의 **`debug.adaptivestackstart = 1`**(기본 켜짐).
  ★ **시작 크기는 GC 마다 평균 스택 크기를 따라 움직인다.** `stackMin` 은 **바닥**이지 **시작값의 정의**가 아니다.
- ★★ 그래서 **「고루틴은 2KB」를 언어 사실로도, 고정된 구현 사실로도 적지 않는다.**

**메모리를 판 격자로 — 자릿수만**

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

- ★★ **`adaptivestackstart` 0/1 × 고루틴 1000/10000, 네 칸 전부 「1024 이상 4096 미만」** — 고루틴당 `StackInuse` 증분이 **2KB 자릿수**다.
  ★ 이 프로그램은 고루틴을 만드는 동안 **GC 로 평균을 키울 일이 없어서** 두 스위치가 같은 자릿수를 냈다 — **스위치가 효과 없다는 증거가 아니다.**
- ★★★ **절댓값은 흔들린다**(탐색 실행에서 1900\~2400 바이트 대 — 블록에는 안 실었다) — 그래서 **범위만** 찍었다(규칙 24).
- ★★★ **이 블록은 「고루틴은 싸다」의 근거가 아니다.** 싼지는 **무엇과 견주나**에 달렸고, 그 견줌(OS 스레드 8MB·10만 개 RSS)은
  [`언어-특성/README.md`](../../언어-특성/README.md) §2 의 몫이다. 여기서 확인한 것은 「**스택 증분이 KB 자릿수이고, 그것은 구현이 정한다**」까지다.
- ★ **시간은 안 쟀다.**

비용 — 이 절이 그 비용을 다룬다. **자릿수만, 구현 층으로.**

### (6) ★ `go` 뒤에 올 수 있는 것 — 컴파일러가 거부하는 것

**언제 쓰나** — `go` 문의 문법 경계를 확인할 때. `defer` 도 같은 규칙이라 함께 던졌다.

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

그림 해설 (한 단계씩):

- ★★ **다섯 줄이 거부된다** — `go len(s)`(결과를 버리는 내장 함수) · `go (f())`(괄호) · `go f`(호출이 아님) · `defer f` · `defer len(s)`.
  명세 「**The expression must be a function or method call; it cannot be parenthesized. Calls of built-in functions are restricted as for expression statements.**」
- ★★★ **마지막 `go f()` 는 통과한다** — `f` 가 `int` 를 돌려주는데도. 명세 「**If the function has any return values, they are discarded**」.
  ★ **고루틴에서 값을 받으려면 채널**이다([목록의 **29번 주제**](../29-channels-buffering-direction-close-range-and-nil/)). `go` 문 자체는 **값을 돌려줄 통로가 없다.**
- ★ `-gcflags=-e` 로 **에러 상한을 풀어** 다섯 줄을 다 받았다.

비용 — 없다.

## 문법 — 형태와 규칙

### 형태

```go
// t28form.go
package main

import (
	"fmt"
	"sync"
)

func work(id int, out chan<- string) { out <- fmt.Sprint("일꾼 ", id) }

func main() {
	out := make(chan string, 3)
	var wg sync.WaitGroup
	for i := range 3 {
		wg.Add(1)
		go func() { // 1.22+ — 회차마다 새 i
			defer wg.Done()
			work(i, out)
		}()
	}
	wg.Wait() // main 이 먼저 끝나지 않게 기다린다
	close(out)
	n := 0
	for range out {
		n++
	}
	fmt.Println("받은 수:", n)
}
```

```text
===== 명령: go build -trimpath -o prog . && ./prog =====
받은 수: 3
(exit 0)
```

규칙 불릿.

- **`go 호출식`** — 함수·메서드 호출이어야 하고 **괄호로 감쌀 수 없다.**
- **함수 값과 인자는 부르는 쪽 고루틴에서 지금 평가**된다([26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/)의 `defer` 와 같다).
- **반환값은 버려진다.** 결과는 **채널**이나 공유 변수(+동기화)로 받는다.
- **`main` 이 반환하면 프로그램이 끝난다** — 다른 고루틴을 기다리지 않고, 그들의 **`defer` 도 안 돈다.**
- **기다리려면 `sync.WaitGroup`**(1.25+ `wg.Go`) 이나 채널.
- **루프 변수는 1.22 부터 회차마다 새로** — `go.mod` 의 `go` 줄이 정한다.
- **다른 고루틴의 패닉은 못 잡는다** — 고루틴 안에서 막는다([27번 주제](../27-panic-recover-and-where-to-use-them/)).
- **고루틴 id·스택 크기·스케줄링 순서는 구현**이다. 기대지 마라.

### 금지 사례 — 컴파일러가 거부하는 것

| 쓴 꼴 | 진단 | 어디서 |
|---|---|---|
| `go len(s)` | `go discards result of len(s) (value of type int)` | (6)절 |
| `go (f())` | `expression in go must not be parenthesized` | 〃 |
| `go f` | `expression in go must be function call` | 〃 |
| `defer f` | `expression in defer must be function call` | 〃 |
| `defer len(s)` | `defer discards result of len(s) (value of type int)` | 〃 |
| `main` 에서 안 기다리고 반환 | ★★★ **아무도 안 막는다** — 종료 코드 0 | (1)절 |
| 아무도 안 닫는 채널에서 받기 | ★★ **아무도 안 막는다** — 누수 | (2)절 |

## 어디서 틀리나

### 1. ★★★ 「`go` 로 띄웠으니 언젠가 끝까지 돈다」

- (1)절 실측 — `main 끝` 뒤에 **`고루틴 끝` 이 없다.** 종료 코드는 0.
- 고치는 법 — **기다린다**(`WaitGroup`·채널). 「`time.Sleep` 으로 넉넉히」는 **기다리기가 아니다** — (1)절이 바로 그 코드다.

### 2. ★★★ 「고루틴 안의 `defer` 가 정리해 준다」

- (1)절 실측 — `main` 이 반환하면 **`[고루틴 defer]` 가 안 돈다.**
- 고치는 법 — 정리가 필요한 고루틴은 **main 이 끝나기 전에 끝나게** 한다(취소 신호 + 기다리기 — [목록의 **34번 주제**](../34-context-cancellation-deadlines-and-values/) `context`).

### 3. ★★ 「`go f(x)` 의 `f` 는 실행될 때의 `x` 를 본다」

- (3)절 실측 — A 는 **1**(`go` 문을 지날 때의 값). 클로저 몸통 안의 `x` 만 나중에 읽힌다.
- 고치는 법 — [26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/)와 같은 기준 — **지금 값이면 인자로, 나중 값이면 클로저로**(단, 나중 값은 **동기화**가 있어야 경쟁이 아니다).

### 4. ★★ 「1.22 부터 루프 변수는 안전하니 판을 신경 안 써도 된다」

- (4)절 실측 — **`go.mod` 가 `go 1.21` 이면 같은 소스가 `[3 3 3]`** 이다. 툴체인이 1.27 이어도.
- 고치는 법 — **`go.mod` 의 `go` 줄을 확인한다.** 옛 모듈을 올릴 때 이 한 줄이 의미를 바꾼다([13번 주제](../13-closures-variable-capture-and-loop-variable-change/)).

### 5. ★★ 「`Wait` 가 돌아오면 `NumGoroutine` 은 바로 1 이다」

- (2)절 — `Done` 을 부른 뒤 고루틴이 **사라지기까지 틈**이 있어 기다리며 확인했다. 바로 1 이라는 **보장은 없다.**
- 고치는 법 — 누수 테스트는 **잠깐 기다리며 수렴을 본다**([목록의 **31번 주제**](../31-goroutine-leaks/)).

### 6. ★★ 「고루틴은 2KB 로 시작한다」

- (5)절 — **구현**이고, 이 판은 **GC 마다 시작 크기를 평균에 맞춘다**(`adaptivestackstart = 1`). `stackMin = 2048` 은 **바닥**이다.
- 고치는 법 — 크기를 말할 때는 **판과 층(구현)** 을 같이 적는다. 싼지 비싼지는 [`언어-특성/README.md`](../../언어-특성/README.md) §2 로.

### 7. ★ 「`go f()` 로 값을 돌려받을 수 있다」

- (6)절 실측 — **컴파일은 되지만 반환값은 버려진다.** 결과는 채널로.

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| ★★★ **`go` 문의 함수 값·인자가 부르는 쪽 고루틴에서 평가** | **명세 보장** | (1)·(3)절 |
| ★★★ **`main` 이 반환하면 기다리지 않는다** | **명세 보장** | 「It does not wait for other (non-main) goroutines」 |
| **반환값이 버려지는 것** | **명세 보장** | (6)절 |
| **`go` 뒤는 호출식 · 괄호 금지 · 내장 함수 제한** | **명세 보장** | (6)절 진단 |
| ★★ **루프 변수 회차마다 새로(1.22)** | **명세 보장(판 의존)** | (4)절 격자 · [13번 주제](../13-closures-variable-capture-and-loop-variable-change/) |
| **`NumGoroutine`·`WaitGroup.Go`(1.25)** | **표준 라이브러리 계약** | `go doc` · `api/go1.25.txt:96` |
| ★★★ **스택 초기 크기 · `stackMin = 2048` · 적응형 시작** | ★ **구현(runtime)** | (5)절 소스 |
| 고루틴당 `StackInuse` 증분의 자릿수 | **이 판의 관찰** | (5)절 격자 |
| 고루틴 id · 스케줄링 순서 · 끊기는 지점 | **구현 — 흔들린다** | 그래서 싣지 않았다 |
| 고루틴의 **시작 시간** | ★ **안 쟀다** | 정본은 [`언어-특성/README.md`](../../언어-특성/README.md) §2 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 기다리지 않아도 되는 일 | ★ **거의 없다** — `main` 이 끝나면 사라진다 | (1)절 |
| 여러 일을 띄우고 다 끝날 때까지 | **`sync.WaitGroup`**(1.25+ `wg.Go`) | (2)절 · [목록의 **32번 주제**](../32-sync-mutex-rwmutex-waitgroup-once/) |
| 결과를 받아야 한다 | **채널** | `go` 는 반환값을 버린다((6)절) · [목록의 **29번 주제**](../29-channels-buffering-direction-close-range-and-nil/) |
| 지금 값으로 넘긴다 | **인자로**(`go f(x)`) | (3)절 |
| 루프에서 띄운다 | **1.22+ 모듈이면 그대로**, 아니면 인자로 | (4)절 |
| 끝낼 수 있어야 한다 | **취소 신호**(`context`) | [목록의 **34번 주제**](../34-context-cancellation-deadlines-and-values/) |
| 누수를 테스트한다 | **`NumGoroutine` 수렴** | (2)절 · [목록의 **31번 주제**](../31-goroutine-leaks/) |
| 고루틴 안의 패닉 | **그 고루틴 안에서 `recover`** | [27번 주제](../27-panic-recover-and-where-to-use-them/) (4)절 |

## 핵심 문장

- ★★★ **`main` 이 반환하면 프로그램이 끝난다** — 고루틴이 **끝까지 안 찍었고**(`고루틴 끝` 없음) **`defer` 도 안 돌았다.** 종료 코드는 **0**.
  ★ **몇 줄에서 끊겼나는 흔들리고, 「끝까지 안 갔다」는 안 흔들린다.**
- ★★★ **`go` 문의 함수 값과 인자는 부르는 쪽 고루틴에서 지금 평가된다** — `defer` 와 **명세 문장이 같다.** A 는 1, 클로저 B 는 2.
- ★★ **`NumGoroutine` 은 막혀 있는 것까지 센다** — 101 → (풀고 기다리면) 1. **받을 쪽 없는 10개는 1초를 기다려도 11** — 누수다.
- ★★★ **루프 변수 × 고루틴은 `go.mod` 한 줄로 갈린다** — `go 1.21` 은 200판 전부 `[3 3 3]`, `go 1.22` 는 200판 전부 `[0 1 2]`(가짓수 각각 1).
  ★ **경쟁을 `start` 채널로 없애야** 판의 의미만 남는다.
- ★★★ **스택 초기 크기는 구현이다** — `stackMin = 2048` 은 바닥이고, 이 판은 **`adaptivestackstart = 1`** 로 **GC 마다 시작 크기를 평균에 맞춘다.**
  메모리 격자는 **2KB 자릿수**까지만 말한다 — ★ **「고루틴은 싸다」는 이 문서의 결론이 아니다.**
- ★★ **`go` 뒤에는 괄호 없는 호출식만** — 반환값은 버려진다. 값은 채널로.
- ★ **`WaitGroup.Go`(1.25)** 의 문서가 「**f must not panic**」 — 다른 고루틴의 패닉은 못 잡으니까.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 28번)
- [`../../../../process-thread/`](../../../../process-thread/) — ★★ **정본 경계.** **그쪽은 스레드·프로세스·스케줄링·경쟁 조건 일반까지**, 여기는 **`go` 문이 만드는 것과 종료 조건부터.**
- [`../../언어-특성/README.md`](../../언어-특성/README.md) §2 — ★★★ **정본 경계.** **고루틴 단가의 논증**(Go FAQ·G/M/P·`stackMin`·10만 개 RSS)은 거기.
  여기는 그 상수를 **이 판 소스로 재확인하고 구현 층으로 표시**했을 뿐이고, **적응형 시작 크기**를 덧붙였다
- [26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/)(`defer`) — ★★ **`go` 문과 같은 평가 규칙** · `os.Exit` 와 `main` 반환이 둘 다 `defer` 를 버린다
- [13번 주제](../13-closures-variable-capture-and-loop-variable-change/)(루프 변수) — ★★ **1.22 의미 변경의 정본**
- [27번 주제](../27-panic-recover-and-where-to-use-them/)(`panic`) — 다른 고루틴의 패닉은 못 잡는다
- [12번 주제](../12-functions-multiple-returns-named-results-and-variadics/)(함수) — 목록상 선행
- [목록의 **29번 주제**](../29-channels-buffering-direction-close-range-and-nil/)(채널) — 고루틴에서 값을 받는 정본
- [목록의 **31번 주제**](../31-goroutine-leaks/)(고루틴 누수) — ★ 누수의 정본. 여기는 `NumGoroutine` 이 안 줄어드는 것까지
- [목록의 **32번 주제**](../32-sync-mutex-rwmutex-waitgroup-once/)(`sync`) — `WaitGroup` 의 정본
- [목록의 **34번 주제**](../34-context-cancellation-deadlines-and-values/)(`context`) — 고루틴을 끝내는 신호
- [목록의 **35번 주제**](../35-data-races-and-the-race-detector/)(레이스) · **36번 주제**(메모리 모델) — 이 문서가 일부러 **없앤** 경쟁의 정본
- [`../../../java/syntax/56-virtual-threads/`](../../../java/syntax/56-virtual-threads/) — ★★ **가상 스레드는 항상 데몬 — `main` 이 끝나면 JVM 이 안 기다린다.** Go 와 같은 자리

## 용어 풀이

- **고루틴** — `go` 문이 만든 독립 실행 흐름. 같은 주소 공간을 쓴다.
- **`go` 문** — `go 호출식`. 부르는 쪽은 기다리지 않는다.
- **main 고루틴** — `main.main` 을 도는 고루틴. 이것이 반환하면 프로그램이 끝난다.
- **`runtime.NumGoroutine()`** — 지금 있는 고루틴 수. 막혀 있어도 센다.
- **`sync.WaitGroup`** — 고루틴 여럿이 끝나길 기다리는 계수기. `Go` 메서드는 1.25.
- **고루틴 누수** — 끝날 길이 없이 막혀 남는 고루틴.
- **`stackMin`** — 런타임 소스의 최소 스택 크기 상수(2048). **구현**이다.
- **`adaptivestackstart`** — GC 마다 새 고루틴의 시작 스택 크기를 평균에 맞추는 런타임 스위치(기본 1).

---

## 더 들어가면

- ★ **`runtime.Goexit` 를 main 에서 부르는 경우**(다른 고루틴이 다 끝나면 크래시)는 **안 던졌다** — `go doc` 만 실었다.
- ★ **`GOMAXPROCS`** 와 스케줄링은 **안 봤다** — [`언어-특성/README.md`](../../언어-특성/README.md) §2 가 1.25 의 cgroup 반영까지 다룬다.
- ★ **`adaptivestackstart` 가 실제로 시작 크기를 키우는 조건**(GC 사이에 깊은 스택)은 **안 던졌다.** (5)절 격자는 그 조건을 안 만들었다.
- ★ **`testing/synctest`**(고루틴을 결정적으로 테스트하는 패키지)는 **안 던졌다** — [목록의 **49번 주제**](../49-testing-table-driven-t-run-cleanup-and-parallel/) 쪽이다.
- ★★ 고루틴 생성의 **시간 비용**은 **안 쟀다.**

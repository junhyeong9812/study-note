# go/syntax/30 — `select`·`default`·타임아웃 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★ **근거로 읽을 칸** — 200판 **가짓수** · 마지막 줄 **`N / M`** · 셸의 참거짓 · 루프 횟수 **1** · **995** · `NumGoroutine` · 교착 상태 줄 · 종료 코드.
> **근거로 읽지 않을 칸** — 없다. 흔들리는 값(판마다 뽑힌 가지·비율·`default` 루프 횟수)은 **블록에 들어가기 전에 가짓수·참거짓으로 접었다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `2 · 1 · 1 · 1` 가지 · `default` 는 안 나온다 · exit 2 `[select]` · `1 / 4`

**출력**

```text
===== 소스: t30grid.go =====
package main

import (
	"fmt"
	"os"
)

// 인자로 「어느 채널에 값이 있나 · default 가 있나」를 고른다. 한 판에 select 한 번.
func main() {
	a := make(chan int, 1)
	b := make(chan int, 1)
	mode := os.Args[1]
	if mode == "both" || mode == "onlyA" || mode == "aDefault" {
		a <- 1
	}
	if mode == "both" {
		b <- 1
	}
	if mode == "aDefault" || mode == "noneDefault" {
		select {
		case <-a:
			fmt.Println("a")
		case <-b:
			fmt.Println("b")
		default:
			fmt.Println("default")
		}
		return
	}
	select {
	case <-a:
		fmt.Println("a")
	case <-b:
		fmt.Println("b")
	}
}
===== 명령: go build -trimpath -o prog . && n=0; m=0; for c in both onlyA aDefault noneDefault; do for i in $(seq 200); do ./prog $c; done > got.txt; k=$(sort -u got.txt | wc -l); m=$((m+1)); if [ "$k" -ge 2 ]; then n=$((n+1)); fi; echo "[$c] 200판 가짓수 $k : $(sort -u got.txt | tr "\n" " ")"; done; timeout 2 ./prog none 2>err.txt; echo "[none] exit=$? $(sed -n 1p err.txt)"; echo "가짓수가 2 이상인 칸 $n / $m" =====
[both] 200판 가짓수 2 : a b 
[onlyA] 200판 가짓수 1 : a 
[aDefault] 200판 가짓수 1 : a 
[noneDefault] 200판 가짓수 1 : default 
[none] exit=2 fatal error: all goroutines are asleep - deadlock!
가짓수가 2 이상인 칸 1 / 4
(exit 0)
```

```text
===== 소스: t30grid.go =====
package main

import (
	"fmt"
	"os"
)

// 인자로 「어느 채널에 값이 있나 · default 가 있나」를 고른다. 한 판에 select 한 번.
func main() {
	a := make(chan int, 1)
	b := make(chan int, 1)
	mode := os.Args[1]
	if mode == "both" || mode == "onlyA" || mode == "aDefault" {
		a <- 1
	}
	if mode == "both" {
		b <- 1
	}
	if mode == "aDefault" || mode == "noneDefault" {
		select {
		case <-a:
			fmt.Println("a")
		case <-b:
			fmt.Println("b")
		default:
			fmt.Println("default")
		}
		return
	}
	select {
	case <-a:
		fmt.Println("a")
	case <-b:
		fmt.Println("b")
	}
}
===== 명령: go build -trimpath -o prog . && ./prog none =====
fatal error: all goroutines are asleep - deadlock!

goroutine 1 [select]:
main.main()
	ex/t30grid.go:30 +0x2c8
(exit 2)
```

**왜 그런가**

- ★★★ **`both` 는 `a b` 두 가지**, `onlyA`·`aDefault` 는 **`a` 만**, `noneDefault` 는 **`default` 만.**
  명세 「**If one or more of the communications can proceed, a single one that can proceed is chosen via a uniform pseudo-random selection. Otherwise, if there is a default case, that case is chosen.**」
- ★★★ **`aDefault` 에서 `default` 는 한 번도 안 나왔다** — `default` 는 「**Otherwise**」, 진행 가능한 것이 **하나도 없을 때만**이다.
- ★★ **`none` 은 exit 2, `fatal error: all goroutines are asleep - deadlock!`**, 상태 줄 **`goroutine 1 [select]:`** — `default` 도 없으니 막혔다.
- ★ 마지막 줄 **`1 / 4`** — 스크립트가 셌다.

### 2. `true` · `1` · 「안 막히고 돈다」까지만

**출력**

```text
===== 소스: t30busy.go =====
package main

import (
	"fmt"
	"time"
)

func main() {
	done := make(chan struct{})
	go func() {
		time.Sleep(20 * time.Millisecond)
		close(done)
	}()
	spins := 0
	for {
		spins++
		select {
		case <-done:
			fmt.Println("default 있는 루프: 1회보다 많이 돌았나:", spins > 1)
			goto blocking
		default:
		}
	}
blocking:
	done2 := make(chan struct{})
	go func() {
		time.Sleep(20 * time.Millisecond)
		close(done2)
	}()
	spins = 0
	for {
		spins++
		select {
		case <-done2:
			fmt.Println("default 없는 루프: 돈 횟수:", spins)
			return
		}
	}
}
===== 명령: go build -trimpath -o prog . && ./prog =====
default 있는 루프: 1회보다 많이 돌았나: true
default 없는 루프: 돈 횟수: 1
(exit 0)
```

**왜 그런가**

- ★★★ **`true`** — 20ms 동안 `select` 는 **한 번도 막히지 않고** `default` 로 빠져 루프를 **계속 돌았다**(바쁜 대기). 몇 번인지는 흔들려서 **참거짓으로만** 찍었다.
- ★★ **`1`** — `default` 가 없으면 `select` 는 **막혀서 기다렸다가 한 번에** 깬다.
- ★★ **CPU 는 안 쟀다.** 이 블록이 말하는 것은 「**막히지 않고 계속 돈다**」 까지다 — 「CPU 를 태운다」는 그 해석이다.

### 3. `받음 42` · `시간 초과` · `NumGoroutine: 2` — 받는 쪽 없는 송신

**출력**

```text
===== 소스: t30timeout.go =====
package main

import (
	"fmt"
	"runtime"
	"time"
)

// call 은 고루틴에게 일을 맡기고 50ms 까지만 기다린다. 결과 채널은 버퍼 0 이다.
func call(d time.Duration) string {
	res := make(chan int)
	go func() {
		time.Sleep(d)
		res <- 42
	}()
	select {
	case v := <-res:
		return fmt.Sprint("받음 ", v)
	case <-time.After(50 * time.Millisecond):
		return "시간 초과"
	}
}

func main() {
	fmt.Println("빠른 일(0ms)    :", call(0))
	fmt.Println("느린 일(200ms)  :", call(200*time.Millisecond))
	time.Sleep(400 * time.Millisecond) // 느린 일이 보낼 차례를 충분히 지나 보낸다
	fmt.Println("400ms 뒤 NumGoroutine:", runtime.NumGoroutine())
}
===== 명령: go build -trimpath -o prog . && ./prog =====
빠른 일(0ms)    : 받음 42
느린 일(200ms)  : 시간 초과
400ms 뒤 NumGoroutine: 2
(exit 0)
```

**왜 그런가**

- ★★ 빠른 일은 50ms 안에 와서 **`받음 42`**, 느린 일(200ms)은 `time.After(50ms)` 가 먼저 열려 **`시간 초과`**.
- ★★★ **`NumGoroutine: 2`** — 느린 일의 고루틴은 200ms 에 **`res <- 42`** 를 하는데, **`call` 은 이미 떠났고 `res` 는 버퍼 0** 이다. **받을 쪽이 영원히 안 오는 송신**에 막혀 있다.
  **타임아웃은 기다림을 끊을 뿐, 맡긴 일을 끊지 않는다** — [31번 주제](../31-goroutine-leaks/)의 누수 첫 모양이다.

### 4. `[1 2 10 20 30]` · 끝난다 · `995` — 5 개를 뺀 나머지 전부

**출력**

```text
===== 소스: t30nilcase.go =====
package main

import (
	"fmt"
	"slices"
)

func filled(vals ...int) chan int {
	ch := make(chan int, len(vals))
	for _, v := range vals {
		ch <- v
	}
	close(ch)
	return ch
}

func main() {
	// 1) 닫힌 채널을 nil 로 바꿔 가지를 끈다
	a, b := filled(1, 2), filled(10, 20, 30)
	var got []int
	for a != nil || b != nil {
		select {
		case v, ok := <-a:
			if !ok {
				a = nil
				continue
			}
			got = append(got, v)
		case v, ok := <-b:
			if !ok {
				b = nil
				continue
			}
			got = append(got, v)
		}
	}
	slices.Sort(got)
	fmt.Println("nil 로 끈 쪽 — 받은 값:", got)

	// 2) 끄지 않으면 — 닫힌 채널 가지가 계속 뽑힌다 (1000회로 자른다)
	a, b = filled(1, 2), filled(10, 20, 30)
	zeros := 0
	for range 1000 {
		select {
		case _, ok := <-a:
			if !ok {
				zeros++
			}
		case _, ok := <-b:
			if !ok {
				zeros++
			}
		}
	}
	fmt.Println("안 끈 쪽 — 1000회 중 ok=false 로 받은 횟수:", zeros)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
nil 로 끈 쪽 — 받은 값: [1 2 10 20 30]
안 끈 쪽 — 1000회 중 ok=false 로 받은 횟수: 995
(exit 0)
```

**왜 그런가**

- ★★★ 닫힌 쪽을 **`nil` 로 바꾸면 그 가지는 다시는 안 뽑힌다** — `nil` 채널은 **절대 진행 못 하고**, `select` 는 **진행 가능한 것 중에서만** 고른다. 둘 다 `nil` 이 되면 루프 조건이 끝낸다.
- ★★★ **995** — 값 **5 개**(1·2·10·20·30)를 받은 뒤 **나머지 995 번이 전부** 닫힌 채널의 영값(`ok=false`)이다. 닫힌 채널은 **늘 받을 수 있으니** 늘 준비된 가지다.
  두 채널이 다 닫힌 뒤에는 **어느 쪽이 뽑혀도** `ok=false` 라, 무작위여도 **합은 딱 995** 다 — 그래서 흔들리지 않는다.

### 5. `4` · 영원히 헛돈다 · `[1 2]` · `vet` 침묵(exit 0)

**출력**

```text
===== 소스: t30break.go =====
package main

import (
	"fmt"
	"os"
)

func main() {
	ch := make(chan int, 3)
	ch <- 1
	ch <- 2
	close(ch)
	var got []int
	if os.Args[1] == "plain" {
		spins := 0
		for {
			select {
			case v, ok := <-ch:
				if !ok {
					spins++
					if spins > 3 { // 안전 장치
						fmt.Println("close 뒤 select 에 다시 들어간 횟수:", spins, "받은 값:", got)
						return
					}
					break
				}
				got = append(got, v)
			}
		}
	}
loop:
	for {
		select {
		case v, ok := <-ch:
			if !ok {
				break loop
			}
			got = append(got, v)
		}
	}
	fmt.Println("라벨 break 뒤 줄 — 받은 값:", got)
}
===== 명령: go build -trimpath -o prog . && ./prog plain && ./prog label =====
close 뒤 select 에 다시 들어간 횟수: 4 받은 값: [1 2]
라벨 break 뒤 줄 — 받은 값: [1 2]
(exit 0)
```

```text
===== 소스: t30break.go =====
package main

import (
	"fmt"
	"os"
)

func main() {
	ch := make(chan int, 3)
	ch <- 1
	ch <- 2
	close(ch)
	var got []int
	if os.Args[1] == "plain" {
		spins := 0
		for {
			select {
			case v, ok := <-ch:
				if !ok {
					spins++
					if spins > 3 { // 안전 장치
						fmt.Println("close 뒤 select 에 다시 들어간 횟수:", spins, "받은 값:", got)
						return
					}
					break
				}
				got = append(got, v)
			}
		}
	}
loop:
	for {
		select {
		case v, ok := <-ch:
			if !ok {
				break loop
			}
			got = append(got, v)
		}
	}
	fmt.Println("라벨 break 뒤 줄 — 받은 값:", got)
}
===== 명령: go vet . && echo "vet exit=$?" =====
vet exit=0
(exit 0)
```

```text
===== 명령: sed -n "7033,7036p;7209,7212p" "$(go env GOROOT)/doc/go_spec.html" | sed -e "s/<[^>]*>//g" =====

For all the cases in the statement, the channel operands of receive operations
and the channel and right-hand-side expressions of send statements are
evaluated exactly once, in source order, upon entering the "select" statement.
A "break" statement terminates execution of the innermost
"for",
"switch", or
"select" statement
(exit 0)
```

**왜 그런가**

- ★★★ **`plain` 은 4** — `break` 는 **가장 안쪽의 `select`** 를 끝낼 뿐이라 `for` 가 계속 돌고, 닫힌 채널이 **늘 준비돼 있으니** 다시 같은 가지로 들어온다. 안전 장치가 없으면 **영원히 헛돈다.**
  명세 「**A "break" statement terminates execution of the innermost "for", "switch", or "select" statement**」.
- ★★ **`label` 은 `라벨 break 뒤 줄 — 받은 값: [1 2]`** — `break loop` 가 라벨이 붙은 `for` 를 끝냈다.
- ★★★ **`go vet` 은 `vet exit=0`, 한 줄도 없다** — 문법상 옳은 코드라 도구가 **의도**를 판단 못 한다.

### 6. 교착 탐지로 exit 2 `[select (no cases)]` · 탐지 안 됨(구현) · 교착이 아니라 의도된 막힘

```text
===== 소스: t30empty.go =====
package main

import (
	"fmt"
	"os"
)

func main() {
	fmt.Fprintln(os.Stderr, "빈 select 에 들어간다")
	select {}
}
===== 명령: go build -trimpath -o prog . && ./prog =====
빈 select 에 들어간다
fatal error: all goroutines are asleep - deadlock!

goroutine 1 [select (no cases)]:
main.main()
	ex/t30empty.go:10 +0x4a
(exit 2)
```

- ★★ 곁에 아무도 없으면 **`fatal error … deadlock!`**, 상태 줄 **`[select (no cases)]`**, exit 2.
- ★★★ 곁에 **타이머를 쥔 고루틴**이 있으면 **탐지가 안 온다** — [29번 주제](../29-channels-buffering-direction-close-range-and-nil/) (8)절 `sleeper` 칸(exit 124). 이것은 **구현**(runtime `checkdead`)의 사정이다. 명세는 「blocks forever」뿐.
- ★ 서버의 `select {}` 는 **다른 고루틴이 일하는 동안 main 을 세워 두는** 의도된 영원한 막힘이다 — 교착은 「**아무도 못 나아가는**」 것이고 여기는 다른 고루틴이 나아간다.

### 7. uniform · 약속 안 한다 · `cheaprandn`, `nil` 가지는 뺀다 · `both` 칸

```text
===== 명령: sed -n "7002,7005p;7046,7050p;7070,7071p" "$(go env GOROOT)/doc/go_spec.html" | sed -e "s/<[^>]*>//g" =====
A "select" statement chooses which of a set of possible
send or
receive
operations will proceed.
If one or more of the communications can proceed,
a single one that can proceed is chosen via a uniform pseudo-random selection.
Otherwise, if there is a default case, that case is chosen.
If there is no default case, the "select" statement blocks until
at least one of the communications can proceed.
Since communication on nil channels can never proceed,
a select with only nil channels and no default case blocks forever.
(exit 0)
```

```text
===== 명령: sed -n "167,176p;191,194p" "$(go env GOROOT)/src/runtime/select.go" =====
	// generate permuted order
	norder := 0
	allSynctest := true
	for i := range scases {
		cas := &scases[i]

		// Omit cases without channels from the poll and lock orders.
		if cas.c == nil {
			cas.elem = nil // allow GC
			continue
		j := cheaprandn(uint32(norder + 1))
		pollorder[norder] = pollorder[j]
		pollorder[j] = uint16(i)
		norder++
(exit 0)
```

- ★★★ 명세의 낱말은 **「uniform pseudo-random」** 하나 — **비율의 숫자는 없다.**
- ★★ 런타임은 **`cheaprandn`** 으로 `pollorder` 를 섞고, 「**Omit cases without channels from the poll and lock orders**」 로 **`nil` 가지를 순서에서 뺀다.**
- ★★ `both` 칸 — `a` 를 **먼저 적었는데** 200판에 **`b` 도 나왔다.** 적은 순서는 우선순위가 아니다.

### 8. 「Otherwise」 · 한 번 시도는 비차단, 루프는 바쁜 대기

- ★★★ `default` 는 **진행 가능한 가지가 하나도 없을 때만** — 명세의 「**Otherwise**」.
- ★★ **한 번만 시도**(「버퍼가 차 있으면 버린다」·「받을 게 있으면 받는다」)는 `default` 의 제자리다. **루프**에 넣으면 막히는 자리가 사라져 **바쁜 대기**가 된다(2번). 루프에는 **막히는 가지**(타이머·`done`)를 둔다.

### 9. `time.After`(맡긴 일은 안 끊긴다) · `nil` 로 · 라벨 `break`/`return` · 안 된다

- ★★★ **`case <-time.After(d)`** — 단 **기다림만 끊긴다.** 맡긴 고루틴은 결과 채널에 **버퍼 1** 을 주거나 **취소 신호**로 따로 끝낸다(3번 · [31번 주제](../31-goroutine-leaks/)).
- ★★ 닫힌 채널 변수를 **`nil` 로**(4번).
- ★★ **라벨 `break`** 또는 **`return`**(5번).
- ★ 우선순위는 **한 겹으로는 안 된다** — 둘 다 준비되면 무작위다(1번).

### 10. 「`nil` 은 영원히 막힌다」+「닫힌 채널은 늘 받는다」 · 받는 쪽 없는 송신 · 닫히는 채널

- ★★ [29번 주제](../29-channels-buffering-direction-close-range-and-nil/) (5)절 「`nil` 채널 송수신은 영원히 막힌다」 → 그 가지는 **절대 진행 못 한다.** (4)절 「닫힌 채널은 막히지 않고 영값」 → 끄지 않으면 **늘 뽑힌다.**
- ★★ 3번의 고루틴은 [31번 주제](../31-goroutine-leaks/)의 **① 받는 쪽이 사라진 송신**이다.
- ★ `ctx.Done()` 은 **취소되면 닫히는 `<-chan struct{}`** 다 — 닫힌 채널은 **모든 받는 쪽을 동시에** 깨우므로 `select` 의 가지 하나로 「취소」를 받을 수 있다. 정본은 [목록의 **34번 주제**](../34-context-cancellation-deadlines-and-values/).

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 로 **★고칠 것 0** |
| ★★★ 선택 격자 (`t30grid`) | 네 칸 × 200판 `sort -u` + `none` 한 판 | 801 | **`2 · 1 · 1 · 1` 가지 · `1 / 4`** |
| ★★ 바쁜 대기 (`t30busy`) | 20ms, 루프 횟수 참거짓 | 1 | `true` · `1` |
| ★★ 타임아웃 (`t30timeout`) | 50ms 대 0·200ms, 400ms 뒤 `NumGoroutine` | 1 | `받음 42` · `시간 초과` · **2** |
| ★★ 가지 끄기 (`t30nilcase`) | 두 채널 합치기, 1000 회 | 1 | `[1 2 10 20 30]` · **995** |
| ★★★ `break` 함정 (`t30break`·`t30vet`) | 두 판 + `go vet` | 3 | **4** · `[1 2]` · `vet exit=0` |

**구현·환경에 달린 항목**

| 항목 | 무엇에 달렸나 |
|---|---|
| 섞는 방법(`cheaprandn`) · 선택 비율 | **runtime `select.go`** — 비율은 **안 실었다** |
| 교착 탐지 · `[select]`·`[select (no cases)]` · exit 2 | **runtime** |
| 타임아웃 블록의 시간 여유 | **이 머신의 스케줄링** — 여유를 4배 이상 두었다 |
| 바쁜 대기의 CPU | ★ **안 쟀다** |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다.

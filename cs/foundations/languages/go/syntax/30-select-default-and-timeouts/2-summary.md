# go/syntax/30 — `select`·`default`·타임아웃 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Go 명세 — Select statements](https://go.dev/ref/spec#Select_statements) ·
> [`time.After`](https://pkg.go.dev/time#After) · `runtime/select.go` 소스.
> 명세·`runtime` 소스는 **이 툴체인의 `$(go env GOROOT)` 에서 직접 떴다.**\
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> ★ **버전** — `select` 의 선택 규칙은 **이 판(`go1.27`) 명세의 문장으로** 적었다(옛 판과는 **견주지 않았다**). `time.After` 의 타이머가 **GC 로 회수되는 것이 1.23** 이다 — 그 판 경계는 [31번 주제](../31-goroutine-leaks/) (7)절이 다룬다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체는 넷째 창이다** — 「**같은 `select` 를 200판 돌려 `sort -u` 로 「몇 가지가 나왔나」만 세는 창**」.
어느 가지가 뽑혔나는 **판마다 흔들린다.** 그런데 **가짓수는 흔들리지 않는다** — 둘 다 준비됐으면 **2**, 하나만이면 **1**.
그래서 **준비 상태 네 가지**를 격자로 놓고 **「가짓수가 2 이상인 칸 N / M」** 을 스크립트가 마지막 줄로 찍게 했다.
★ **비율은 안 실었다** — 명세는 「**균등 의사 무작위**」라고만 하고, 비율은 **구현과 한 판의 결과**다.

★★ **이 주제의 경계** — 「기다림을 **밖에서 끊는** 신호」인 `context.Context` 의 `Done()` 은 목록의 **34번 주제**다. 여기서는 **`select` 의 가지 하나**로만 쓴다.
`select` 로 기다리다 **떠난 뒤 남는 고루틴**은 [31번 주제](../31-goroutine-leaks/)가 정본이다 — (4)절이 그 입구다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | ★★★ **준비된 것이 여럿이면 「uniform pseudo-random」으로 하나** · **없으면 `default`, `default` 도 없으면 막힘** · **`nil` 채널만 있고 `default` 가 없으면 영원히 막힘** · `break` 는 가장 안쪽의 `for`·`switch`·`select` 를 끝낸다 |
| **구현(gc·runtime)·표준 라이브러리** | `runtime`·`time` 이 한 것 | ★★ **`cheaprandn` 으로 뽑는 순서를 섞는다** · **`nil` 채널 가지는 순서에서 뺀다** · 교착 탐지 · `time.After` 가 **타이머 채널**이라는 것 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 200판 가짓수 · 루프 횟수 · `NumGoroutine` |

★★★ **선을 긋는다** — 「**둘 다 준비됐으면 아무거나 하나**」는 **명세**, 「**어떻게 섞나(`cheaprandn`)**」와 「**몇 대 몇으로 나오나**」는 **구현**이다.
「반반이다」를 언어 사실로 적지 마라 — 명세의 낱말은 **uniform** 하나이고, 그것을 **몇 판으로 확인할지**는 이 문서가 하지 않는다.

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다(그래서 안 실었다)** | ★★★ 둘 다 준비된 `select` 가 **판마다 무엇을 뽑았나** · **몇 대 몇이었나** | 명세가 무작위라 했다 — **`sort -u` 로 가짓수만** 실었다(규칙 11) |
| **흔들린다(그래서 안 실었다)** | ★★ `default` 루프가 **몇 번 돌았나** | 스케줄링과 시간 — 「**1회보다 많이 돌았나**」 참거짓만 실었다 |
| 안 흔들린다 | ★★★ **200판 가짓수**(`2 · 1 · 1 · 1`) · 마지막 줄 **`1 / 4`** | 준비된 가지가 둘이면 둘 다 나오고, 하나면 그것만 나온다 |
| 안 흔들린다 | ★★ `default` **없는** 루프의 횟수 **1** · 닫힌 채널 가지의 `ok=false` **995** 번 | 막히면 한 번에 깨고, 닫힌 채널은 늘 준비돼 있다 |
| 안 흔들린다 | ★ 타임아웃 블록의 `받음 42` · `시간 초과` · `NumGoroutine: 2` | ★ **시간 여유를 4배 이상** 두었다(50ms 대 0ms·200ms, 400ms 대기) — 여유가 좁으면 흔들린다 |
| 안 흔들린다 | 교착의 `goroutine 1 [select]:` · `[select (no cases)]` · 종료 코드 | |

★ **정규화 규칙은 하나도 안 썼다** — 이 편의 트레이스에는 main 고루틴(id 1)만 나온다.

## 한눈에 — 쉽게 말하면

**`select` 는 창구 여러 개 앞에 선 손님이다.** 어느 창구든 **먼저 열리는 곳**으로 간다.
**둘이 동시에 열려 있으면 동전을 던진다** — 어느 쪽인지는 그때그때 다르다.
**`default` 는 「아무 창구도 안 열렸으면 그냥 간다」** 는 쪽지다. 쪽지가 있으면 **절대 줄을 서지 않는다.**
**`time.After` 는 「이 시각이 되면 열리는 창구」** 다 — 타임아웃이 곧 창구 하나다.

| 비유 | 실체 |
|---|---|
| 창구 여러 개 중 **먼저 열린 곳**으로 | ★★ **`select`** — 준비된 가지 하나를 고른다 |
| 둘이 **동시에** 열려 있으면 **동전 던지기** | ★★★ **uniform pseudo-random** — 200판에 **두 가지 다** 나온다((1)절) |
| 「안 열렸으면 그냥 간다」 쪽지 | ★★★ **`default`** — 막히지 않는다. 루프에 넣으면 **바쁜 대기**((2)절) |
| 창구가 **하나도 없는** 줄 | ★ **`select {}`** — 영원히 막힘. 곁에 아무도 없으면 교착 탐지((3)절) |
| 「5시가 되면 열리는 창구」 | ★★ **`time.After(d)`** — 타임아웃 가지((4)절) |
| 문 닫은 창구를 **명단에서 지운다** | ★★ **`nil` 채널로 가지 끄기** — `nil` 가지는 **절대 안 뽑힌다**((5)절) |
| 창구 앞에서 「그만」 하고 **줄에서만** 빠진다 | ★★★ **`for`-`select` 의 `break`** — `select` 만 빠진다. 건물 밖으로 나가려면 **라벨**((6)절) |

```text
   ★★★ select 가 무엇을 고르나 — 준비 상태 네 칸 × 200판 ((1)절의 실측)

   준비 상태              명세                              200판 sort -u
   ─────────────────      ─────────────────────────────     ─────────────
   a ○  b ○               둘 중 하나를 균등 의사 무작위로     a b   (2가지)
   a ○  b ✗               a 만 진행 가능                     a     (1가지)
   a ○  b ✗  + default    진행 가능한 것이 있으면 default 아님  a     (1가지)
   a ✗  b ✗  + default    진행 가능한 것이 없으니 default      default (1가지)
   a ✗  b ✗               default 도 없으니 막힌다           교착 · exit 2
```

```text
   ★★★ for-select 의 break — 어디를 빠져나가나 ((6)절의 실측)

   for {                          loop:
       select {                   for {
       case v, ok := <-ch:            select {
           if !ok {                   case v, ok := <-ch:
               break  ──┐                 if !ok {
           }            │                     break loop ──┐
       }  ◀─────────────┘                 }                │
   }   ← 다시 select 로 (4번 들어가 가드에 걸림)   }          │
                                  }                        │
                                  ◀────────────────────────┘ 루프 밖으로
```

> **`select` 문** — 명세 「A "select" statement chooses which of a set of possible send or receive operations will proceed.」 `switch` 와 비슷하지만 가지마다 **채널 연산**이다.

> **`default` 가지** — 준비된 채널 연산이 **없을 때** 고르는 가지. 있으면 `select` 는 **절대 막히지 않는다.**

> **`time.After(d)`** — `d` 뒤에 현재 시각을 **한 번 보내는 채널**을 돌려준다. 문서 「It is equivalent to NewTimer(d).C.」

- [29번 주제](../29-channels-buffering-direction-close-range-and-nil/)가 목록상 **선행**이다 — **한 채널**이 언제 막히나. `select` 는 그 규칙을 **여러 채널에 동시에** 건다.
  ★ 29편 (5)절의 「**`nil` 채널은 영원히 막힌다**」가 (5)절 관용구의 근거이고, 29편 (4)절의 「**닫힌 채널은 늘 받을 수 있다**」가 (5)절 함정의 근거다.
- ★ [15번 주제](../15-switch-type-switch-fallthrough-labels-and-goto/)가 **라벨·`break`·`goto`** 의 정본이다 — (6)절은 그 규칙이 **`select` 안에서** 어떻게 물리나만 본다.

## 이 주제가 답하려는 질문

1. **준비된 가지가 여럿이면 `select` 는 무엇을 고르나** — 그리고 그것은 누가 정하나(명세 대 구현).
2. **`default` 가 붙으면 의미가 어떻게 바뀌나** — 막힘 대 바쁜 대기.
3. **타임아웃·가지 끄기·루프 빠져나가기를 어떻게 쓰나** — 그리고 각자 어디서 틀리나.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **200판 × `sort -u` 가짓수 격자** | 준비 상태별로 **무엇이 나올 수 있나** | ★ 본체 창 — 이 주제의 넷째 창(규칙 11) |
| ★★ **교착 탐지** | `default` 없는 `select` 가 **막혔다** | [29번 주제](../29-channels-buffering-direction-close-range-and-nil/)의 본체 창 |
| ★★ **루프 횟수 참거짓** | `default` 가 **바쁜 대기**를 만든다 | 이 주제의 고유 창 |
| ★ **`NumGoroutine`** | 타임아웃 뒤 **남은 고루틴** | [28번 주제](../28-goroutines-go-statement-cost-and-termination/)의 창 |
| ★ **`runtime/select.go` 소스 인용** | 무작위가 **어떻게** 구현됐나 | 구현 층 |
| ★ **`go vet` 의 침묵** | `for`-`select` `break` 함정을 **도구가 못 본다** | 규칙 18-A |
| **부적용 — CPU 사용률** | ★★★ **안 쟀다.** 바쁜 대기가 「CPU 를 태운다」는 이 문서에서 **루프 횟수**로만 보였다 | — |
| **부적용 — 선택 비율** | ★★ **안 실었다.** 흔들리는 값이고 명세는 비율을 약속하지 않는다 | — |

★★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.**
「무작위인가」는 **한 판으로는 답이 없다**(한 판은 늘 한 가지만 낸다). 그래서 「**200판에 몇 가지가 나왔나**」로 물었다.
★ 바꾼 창의 한계 — **「균등한가」는 이 창이 답하지 않는다.** 두 가지가 **나온다**까지만 말한다.

### (1) ★★★ 준비된 가지가 여럿이면 — 200판 가짓수 격자

**언제 쓰나** — 두 채널이 **동시에** 준비될 수 있는 `select` 를 쓸 때. 「먼저 적은 가지가 이긴다」고 기대하면 틀린다.

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

그림 해설 (한 단계씩):

- ★★★ **마지막 줄 `가짓수가 2 이상인 칸 1 / 4`** — 스크립트가 셌다.
- ★★★ **`both` — 200판에 `a b` 두 가지.** 소스에서 `a` 가 **먼저 적혀 있어도** `b` 가 뽑힌 판이 있다. **적은 순서는 우선순위가 아니다.**
- ★★ **`onlyA` 는 `a` 만** — 준비된 것이 하나면 그것뿐이다. **`aDefault` 도 `a` 만** — ★★★ **준비된 가지가 있으면 `default` 는 절대 안 뽑힌다.**
- ★★ **`noneDefault` 는 `default` 만** — 아무것도 준비 안 됐을 때에만.
- ★★ **`none` — exit 2, `fatal error … deadlock!`** — `default` 가 없으니 **막혔다**:

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

  ★ 상태 줄이 **`[select]`** 다 — [29번 주제](../29-channels-buffering-direction-close-range-and-nil/)의 `[chan send]` 자리에 `select` 가 온다.

명세는 이렇게만 말한다 —

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

  ★★★ 「**a single one that can proceed is chosen via a uniform pseudo-random selection**」 — **비율의 숫자는 없다.**
  「**Otherwise, if there is a default case, that case is chosen.**」 — `default` 는 **「Otherwise」** 다.

구현은 이렇게 섞는다 —

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

  ★★ **`cheaprandn(uint32(norder + 1))`** 로 **뽑아 볼 순서(`pollorder`)** 를 가지마다 섞는다 — 섞인 순서대로 보다가 **처음 준비된 것**을 고른다. **이것은 구현이다.**
  ★★ 윗부분의 「**Omit cases without channels from the poll and lock orders.**」 — **`nil` 채널 가지는 순서에서 아예 빠진다.** (5)절 관용구가 **런타임에서 공짜**인 이유다.

비용 — 없다(재지 않았다).

### (2) ★★★ `default` — 막히지 않는다, 그래서 바쁜 대기가 된다

**언제 쓰나** — 「받을 것이 있으면 받고 없으면 넘어간다」를 쓸 때. **루프 안에서는 조심.**

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

그림 해설 (한 단계씩):

- ★★★ **`default` 있는 루프: 1회보다 많이 돌았나: true** — 20ms 동안 `select` 가 **한 번도 안 막히고** 계속 `default` 로 빠져 루프를 돌았다.
  ★ **몇 번 돌았나는 싣지 않았다**(흔들린다). 「**여러 번**」이 결론이다 — 그것이 **바쁜 대기(busy-wait)** 다.
- ★★★ **`default` 없는 루프: 돈 횟수: 1** — `select` 가 **막혀서 기다렸다가** 한 번에 깼다.
- ★★ **CPU 를 얼마나 쓰나는 안 쟀다** — 이 문서가 보인 것은 **「막히지 않고 계속 돈다」** 까지다. 「CPU 를 태운다」는 그 결과의 **해석**이다.
- ★ `default` 의 올바른 자리 — **한 번만 시도하는 비차단 송수신**(「버퍼가 차 있으면 버린다」). 루프에 넣을 거면 **다른 막히는 가지**(타이머·`done`)와 같이 둔다.

비용 — 이 절이 비용을 다룬다 — **횟수로만.**

### (3) ★ 빈 `select {}` — 영원히 막힌다

**언제 쓰나** — 「main 을 영원히 붙잡아 둔다」는 코드를 볼 때.

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

- ★★ **`goroutine 1 [select (no cases)]:`** · exit 2 — 가지가 **하나도 없는** `select` 는 **절대 진행할 수 없다.** 곁에 아무도 없으니 교착 탐지가 죽였다.
- ★★ **곁에 타이머를 쥔 고루틴이 있으면 탐지가 안 온다** — [29번 주제](../29-channels-buffering-direction-close-range-and-nil/) (8)절의 `sleeper` 칸(**탐지 못 한 칸 1 / 3**)과 같은 사정이다.
  그래서 서버의 `select {}` 는 **다른 고루틴이 다 하는 동안 main 을 세워 두는 관용구**로 쓰인다 — 교착이 아니라 **의도된 영원한 막힘**이다.
- ★ 명세 「**a select with only nil channels and no default case blocks forever**」의 극단형이다(가지 0 개).

비용 — 없다.

### (4) ★★ `time.After` 타임아웃 — 그리고 떠난 뒤에 남는 것

**언제 쓰나** — 「50ms 안에 답이 없으면 포기」를 쓸 때.

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

그림 해설 (한 단계씩):

- ★★ **빠른 일은 `받음 42`, 느린 일(200ms)은 `시간 초과`** — `time.After(50ms)` 가 **또 하나의 창구**로 열려 먼저 뽑혔다.
- ★★★ **400ms 뒤 `NumGoroutine: 2`** — 느린 일의 고루틴이 **아직 있다.** 200ms 에 `res <- 42` 를 하려는데 **받을 쪽(`call`)은 이미 떠났다.** 버퍼 0 이니 **영원히 막힌다.**
  ★★★ **타임아웃은 기다림을 끊을 뿐, 맡긴 일을 끊지 않는다.** 이것이 [31번 주제](../31-goroutine-leaks/)의 **누수 첫 모양**(받는 쪽이 사라진 송신)이고, 고치는 법(버퍼 1·`context`)도 거기다.
- ★ 타이밍 여유를 **4배 이상**(50ms 대 0ms·200ms, 400ms 대기)으로 두어 이 블록은 흔들리지 않았다 — 재실행 대조에서 한 글자도 같았다.
- ★ `time.After` 를 **루프 안에서 매번** 부르는 것의 메모리 사정(1.23 이전 판에서는 타이머가 발화 전까지 안 치워졌다)은 [31번 주제](../31-goroutine-leaks/) (7)절 — ★ **고루틴 누수가 아니다**(`NumGoroutine` 이 안 는다).

비용 — 없다.

### (5) ★★ `nil` 채널로 가지를 끈다 — 닫힌 채널 가지는 늘 뽑힌다

**언제 쓰나** — 채널 **둘을 합쳐** 받다가 하나가 먼저 닫힐 때.

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

그림 해설 (한 단계씩):

- ★★★ **nil 로 끈 쪽 — `[1 2 10 20 30]`** 를 다 받고 루프가 **끝났다.** 닫힌 쪽을 `a = nil` 로 바꾸면 그 가지는 **다시는 안 뽑힌다** —
  [29번 주제](../29-channels-buffering-direction-close-range-and-nil/) (5)절의 「`nil` 채널은 영원히 막힌다」 + (1)절의 「진행 가능한 것 중에서만 고른다」.
- ★★★ **안 끈 쪽 — 1000회 중 `ok=false` 로 받은 횟수: 995.** 값 5 개를 받은 뒤 **나머지 995 번이 전부 닫힌 채널의 영값**이다.
  닫힌 채널은 **늘 받을 수 있으니**(29편 (4)절 `empty`) **늘 준비된 가지**가 된다 — 끄지 않으면 **다른 가지를 굶기며 헛돈다.**
- ★ 두 가지가 다 닫혀 **둘 다 `nil`** 이 되면 `for a != nil || b != nil` 이 끝난다 — 조건을 안 두고 `select` 로 들어가면 **`nil` 만 있는 `select`** 라 영원히 막힌다(명세 「blocks forever」).

비용 — 없다. 런타임은 `nil` 가지를 **순서에서 뺀다**((1)절 소스).

### (6) ★★★ `for`-`select` 의 `break` — `select` 만 빠져나간다

**언제 쓰나** — 루프 안 `select` 에서 「끝」을 처리할 때. **유명한 함정이다.**

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

그림 해설 (한 단계씩):

- ★★★ **`plain` — `close 뒤 select 에 다시 들어간 횟수: 4`.** `break` 를 만났는데 **루프가 계속 돌았다.** 안전 장치가 4 번째에 끊었다(없었으면 **영원히 헛돈다** — (5)절처럼 닫힌 채널이 늘 준비돼 있으니까).
  ★ 명세의 `break` — 「**terminates execution of the innermost "for", "switch", or "select" statement**」. 가장 안쪽이 **`select`** 다.
- ★★★ **`label` — `라벨 break 뒤 줄 — 받은 값: [1 2]`.** `break loop` 는 **라벨이 붙은 `for`** 를 끝낸다. 정본은 [15번 주제](../15-switch-type-switch-fallthrough-labels-and-goto/).
- ★ 다른 고치는 법 — `return`(함수를 끝낸다) · 루프 조건에 상태를 두기.

명세 원문 — `break` 와, `select` 가 채널 식을 언제 평가하나 —

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

- ★★ 둘째 문단 「**A "break" statement terminates execution of the innermost "for", "switch", or "select" statement**」 — `select` 도 **`break` 가 끝내는 문**에 들어 있다. 그래서 가장 안쪽인 `select` 가 끝난다.
- ★ 첫 문단 — 채널 식과 보낼 값은 **들어설 때 한 번, 적힌 순서대로** 평가된다. 뽑히지 않은 가지의 식도 평가된다(이 문서는 그 부수 효과를 **안 던졌다**).

도구는 이것을 잡나 —

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

- ★★★ **`go vet` 은 침묵한다 — `vet exit=0`.** 문법상 **완벽히 옳은** 코드다(`break` 로 `select` 를 끝내는 것도 쓸모가 있다). **의도**가 틀렸을 뿐이라 도구가 판단할 수 없다.
  ★ 「`vet` 이 안 잡았다」는 **물었는데 조용했다**는 것이다(규칙 18-A) — 탐침 1 개, 답 0 개.

비용 — 없다.

### (7) ★ `context.Context` 의 `Done()` — 경계만

- `ctx.Done()` 은 **`<-chan struct{}`** 이고, **취소되면 닫힌다.** 그래서 `select` 의 가지 하나로 쓴다 — `case <-ctx.Done(): return`.
  닫힌 채널이 **모든 받는 쪽을 동시에 깨우는** 것([29번 주제](../29-channels-buffering-direction-close-range-and-nil/) (4)절)이 「취소를 여럿에게 한 번에 알린다」의 바탕이다.
- ★★ 취소가 **호출 트리를 따라 어떻게 번지나**, 데드라인·값은 목록의 **34번 주제**가 정본이다. 이 문서는 **블록을 싣지 않았다** — [31번 주제](../31-goroutine-leaks/) (3)절이 누수를 고치는 데 한 번 쓴다.

## 문법 — 형태와 규칙

### 형태

```go
// t30form.go
package main

import (
	"fmt"
	"time"
)

func main() {
	jobs := make(chan int)
	go func() {
		defer close(jobs)
		for i := 1; i <= 3; i++ {
			jobs <- i
		}
	}()
	timeout := time.After(time.Second)
	sum := 0
loop:
	for {
		select {
		case j, ok := <-jobs:
			if !ok {
				break loop // 라벨이 없으면 select 만 빠져나간다
			}
			sum += j
		case <-timeout:
			fmt.Println("시간 초과")
			break loop
		}
	}
	fmt.Println("합:", sum)
}
```

```text
===== 명령: go build -trimpath -o prog . && ./prog =====
합: 6
(exit 0)
```

규칙 불릿.

- **가지마다 채널 연산 하나** — `case v := <-ch:` · `case v, ok := <-ch:` · `case ch <- x:` · `default:`.
- **준비된 것이 여럿이면 균등 의사 무작위로 하나.** 적은 순서는 우선순위가 아니다.
- **준비된 것이 없으면 `default`**, `default` 도 없으면 **막힌다.**
- **`default` 가 있으면 절대 안 막힌다** — 루프에 넣으면 바쁜 대기.
- **`nil` 채널 가지는 절대 안 뽑힌다** — 가지를 끄는 데 쓴다. **닫힌 채널 가지는 늘 뽑힐 수 있다.**
- **`select {}`** 는 영원히 막힌다.
- **`break` 는 `select` 를 끝낸다** — 루프를 끝내려면 **라벨** 또는 `return`.
- 채널 식과 보낼 값은 **`select` 에 들어설 때 한 번씩, 적힌 순서대로** 평가된다(명세 「evaluated exactly once, in source order, upon entering the "select" statement」) — 뽑히지 않은 가지의 식도 평가된다.

### 금지 사례 — 컴파일은 되는데 틀리는 것

| 쓴 꼴 | 무엇이 되나 | 어디서 |
|---|---|---|
| `for { select { … break … } }` | ★★★ **`select` 만 빠진다** — 루프는 계속. `go vet` 침묵 | (6)절 |
| `for { select { case …: default: } }` | ★★ **바쁜 대기** — 한 번도 안 막힌다 | (2)절 |
| 닫힌 채널을 가지에 둔 채 루프 | ★★ **그 가지가 계속 뽑힌다**(995 / 1000) | (5)절 |
| 타임아웃으로 떠나면서 결과 채널이 버퍼 0 | ★★★ **맡긴 고루틴이 남는다**(`NumGoroutine: 2`) | (4)절 |
| 「먼저 적은 가지가 먼저」 | ★★ **아니다** — 200판에 `a b` 둘 다 | (1)절 |

## 어디서 틀리나

### 1. ★★★ 「`break` 로 루프를 빠져나왔다」

- (6)절 실측 — **`select` 에 4 번 다시 들어갔다.** `go vet` 은 **침묵**.
- 고치는 법 — **라벨 `break loop`** 또는 `return`.

### 2. ★★★ 「먼저 적은 `case` 가 우선이다」

- (1)절 실측 — `a` 를 먼저 적었는데 200판에 **`a b` 두 가지.**
- 고치는 법 — 우선순위가 필요하면 **`select` 를 두 겹**으로(먼저 높은 쪽만 `default` 와 함께 시도, 없으면 둘 다) — 이 문서는 **그 패턴을 안 던졌다.**

### 3. ★★★ 「타임아웃이 났으니 일도 멈췄다」

- (4)절 실측 — **400ms 뒤에도 고루틴이 남아 있다**(`NumGoroutine: 2`).
- 고치는 법 — 결과 채널에 **버퍼 1**(떠나도 한 번은 보낼 수 있게) 또는 일에 **취소 신호**를 넘긴다 — [31번 주제](../31-goroutine-leaks/) (3)절.

### 4. ★★ 「`default` 를 붙이면 더 빠르다·반응이 좋다」

- (2)절 실측 — **막히지 않고 계속 돈다.** 반응은 좋아 보이지만 **그동안 할 일 없이 돈다.** 시간·CPU 는 **안 쟀다.**
- 고치는 법 — 루프에는 **막히는 가지**(타이머·`done`)를 둔다. `default` 는 **한 번만 시도**할 때.

### 5. ★★ 「닫힌 채널 가지는 저절로 조용해진다」

- (5)절 실측 — **995 / 1000 번이 영값.** 닫힌 채널은 **늘 준비돼 있다.**
- 고치는 법 — `ok=false` 를 받으면 **그 변수를 `nil` 로.**

### 6. ★ 「비율이 반반인지 테스트로 확인하자」

- 명세는 **uniform** 이라는 말만 한다. 비율 검정은 **구현을 시험하는 것**이고, 판마다 흔들린다. 이 문서는 **가짓수까지만** 말한다.

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| ★★★ **준비된 것 여럿 → 균등 의사 무작위 하나** | **명세 보장** | (1)절 원문 · 200판 `a b` |
| ★★★ **준비된 것 없음 → `default`, 없으면 막힘** | **명세 보장** | (1)절 격자 |
| **`nil` 채널만 있고 `default` 없으면 영원히 막힘 · `select {}`** | **명세 보장** | (3)·(5)절 |
| ★★ **`break` 는 가장 안쪽 `for`·`switch`·`select`** | **명세 보장** | (6)절 |
| ★★ **`cheaprandn` 으로 뽑는 순서를 섞는다 · `nil` 가지는 순서에서 뺀다** | ★ **구현(runtime)** | (1)절 `select.go` |
| **선택 비율** | **구현 — 흔들린다** | 싣지 않았다 |
| 교착 탐지 · `[select]`·`[select (no cases)]` 문구 · exit 2 | **구현(runtime)** | (1)·(3)절 |
| `time.After` 가 타이머 채널 · **1.23 부터 GC 가 회수** | **표준 라이브러리 계약** | [31번 주제](../31-goroutine-leaks/) (7)절 |
| 바쁜 대기의 **CPU 비용** | ★ **안 쟀다** | — |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 여러 채널 중 **먼저 오는 것** | **`select`** | (1)절 |
| 기다림에 **상한** | **`case <-time.After(d)`**(또는 `context` 데드라인) | (4)절 — 단 맡긴 일은 따로 끝내라 |
| **한 번만** 막히지 않고 시도 | **`select` + `default`** | (2)절 |
| 루프 안에서 **계속** 기다림 | `default` **없이** 막히는 가지만 | (2)절 |
| 합친 채널 중 하나가 닫혔다 | **그 변수를 `nil` 로** | (5)절 |
| 루프를 끝낸다 | **라벨 `break`** 또는 `return` | (6)절 |
| 밖에서 끊을 수 있어야 | **`case <-ctx.Done():`** | 목록의 **34번 주제** |
| 우선순위가 있다 | `select` 한 겹으로는 **안 된다** | (1)절 — 무작위 |

## 핵심 문장

- ★★★ **준비된 가지가 여럿이면 균등 의사 무작위** — 200판에 **`a b` 두 가지**, 하나만 준비되면 **그것만**. 격자의 **가짓수 2 이상인 칸 1 / 4**.
- ★★★ **`default` 는 「진행 가능한 것이 없을 때만」** 이다 — `a` 가 준비돼 있으면 200판 전부 `a`. **`default` 가 있으면 막히지 않고, 루프에서는 바쁜 대기가 된다**(`default` 없는 루프는 1 회).
- ★★★ **`for`-`select` 의 `break` 는 `select` 만 빠진다** — 4 번 다시 들어갔고 **`go vet` 은 침묵**했다. **라벨**로 고친다.
- ★★ **`nil` 가지는 안 뽑히고, 닫힌 가지는 늘 뽑힌다** — 끄지 않으면 1000 회 중 **995 번이 영값**. 런타임은 `nil` 가지를 **순서에서 뺀다.**
- ★★ **타임아웃은 기다림을 끊을 뿐 일을 끊지 않는다** — 400ms 뒤에도 **`NumGoroutine: 2`**. 그 뒤는 [31번 주제](../31-goroutine-leaks/).
- ★ **무작위 섞기(`cheaprandn`)와 비율은 구현**이다 — 명세의 낱말은 **uniform** 하나다.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 30번)
- [29번 주제](../29-channels-buffering-direction-close-range-and-nil/)(채널) — ★★ 목록상 선행 · 한 채널의 차단 규칙 · `nil` 채널 · 닫힌 채널 · **탐지 못 하는 교착**
- [31번 주제](../31-goroutine-leaks/)(누수) — ★★ 타임아웃으로 떠난 뒤 남는 고루틴 · `time.After` 의 메모리
- [15번 주제](../15-switch-type-switch-fallthrough-labels-and-goto/)(라벨·`break`) — 라벨 규칙의 정본
- [28번 주제](../28-goroutines-go-statement-cost-and-termination/)(고루틴) — `NumGoroutine`
- 목록의 **34번 주제**(`context`) — ★ `Done()` 의 정본. 여기는 가지 하나로만
- [`../../../../process-thread/`](../../../../process-thread/) — 여러 사건을 기다리는 일반(폴링 대 대기)

## 용어 풀이

- **`select`** — 여러 채널 연산 중 준비된 하나를 고르는 문.
- **균등 의사 무작위(uniform pseudo-random)** — 명세가 쓰는 말. 비율의 숫자는 약속하지 않는다.
- **`default` 가지** — 준비된 연산이 없을 때 고르는 가지. 있으면 `select` 가 막히지 않는다.
- **바쁜 대기(busy-wait)** — 막혀서 기다리는 대신 **계속 돌며 확인**하는 것.
- **`time.After(d)`** — `d` 뒤에 한 번 값을 보내는 채널을 돌려주는 함수.
- **가지 끄기** — 채널 변수를 `nil` 로 바꿔 그 `case` 가 다시는 안 뽑히게 하는 관용구.
- **`pollorder`** — 런타임이 가지를 살펴볼 순서. `cheaprandn` 으로 섞는다(구현).

---

## 더 들어가면

- ★ **우선순위 `select`**(두 겹 `select`) 패턴은 **안 던졌다.**
- ★ **`time.NewTimer` + `Reset`/`Stop`** 은 **안 다뤘다** — 1.23 에서 타이머 채널이 **버퍼 0 처럼** 바뀐 사정([31번 주제](../31-goroutine-leaks/) (7)절의 문서 인용)과 얽힌다.
- ★★ `select` 의 **시간 비용**·가지 수에 따른 비용은 **안 쟀다.**
- ★ 명세가 말하는 「**채널 식은 들어설 때 한 번씩 평가**」(부수 효과가 뽑히지 않은 가지에서도 난다)는 **안 던졌다.**

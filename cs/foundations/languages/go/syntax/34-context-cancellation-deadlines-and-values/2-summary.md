# go/syntax/34 — ★ `context`: 취소·데드라인·값 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [`context`](https://pkg.go.dev/context) 문서 · [`go vet` 의 `lostcancel`·`stdversion` 분석기](https://pkg.go.dev/cmd/vet).
> 문서·`api/go1NN.txt`·분석기 소스는 **이 툴체인의 `$(go env GOROOT)` 에서 직접 떴다.** 문서가 가리키는 블로그 글(context-and-structs)은 **안 열었다.**\
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> ★★ **버전** — `context` 패키지가 **1.7** · `WithCancelCause`·`Cause` 가 **1.20** · `AfterFunc`·`WithoutCancel`·`WithDeadlineCause`·`WithTimeoutCause` 가 **1.21**((6)절 판 표 — `api/go1NN.txt` 에서 뗐다).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체는 넷째 창이다** — 「**취소 전파 나무의 노드마다 `Done` 을 받았나를 참거짓으로 찍는 로그**」.
**누가 먼저 받나**(도착 순서)는 실행마다 흔들린다 — 그래서 순서는 「**두 가지 이상 나왔나**」 로만 적고,
「**누가 받았나 / 안 받았나**」 를 근거로 쓴다. 부모를 끊으면 **7 / 7**, 자식 하나를 끊으면 **2 / 7**((1)절).
★★ 그 짝으로 「**`go vet lostcancel` 탐침 11개 중 몇 개가 답했나**」((5)절 — 규칙 18-A)와 「**`stdversion` 이 판마다 말했나**」((6)절 — `go.mod` 판 격자).

★★★ **이 주제의 경계** — 데드라인 전파의 **설계**(타임아웃 대 데드라인 · 진입점 → 작업 → DB → 외부 연결 → 큐 · 취소가 닿지 않는 곳)는
[`../../../../../ops-patterns/deadline-propagation/`](../../../../../ops-patterns/deadline-propagation/)가 정본이다. **그쪽은 「무엇을 어디까지 넘기나」의 설계까지**, 여기는 **`context` 타입의 API·관례·함정부터.**
[31번 주제](../31-goroutine-leaks/) (3)절이 **`context` 로 누수를 고친 것**(`ctxWait`·`ctxTicker` — `cancel()` 뒤 1초 안에 1)을 이미 보였다 — 여기서는 **다시 재지 않고**, 그 취소가 **나무를 따라 번지는 모양**과 **값 전달의 경계**를 본다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | ★ **명세에는 `context` 가 없다** — 표준 라이브러리다. 명세에서 오는 것은 「`Done()` 은 채널이고 **닫힌 채널은 모든 받는 쪽을 깨운다**」([29번 주제](../29-channels-buffering-direction-close-range-and-nil/)) 뿐이다 |
| **표준 라이브러리 계약** | `context` 문서가 약속한 것 | ★★★ 「**When a Context is canceled, all Contexts derived from it are also canceled**」 · 「**Failing to call the CancelFunc leaks the child**」 · ★★★ 「**Do not store Contexts inside a struct type**」·「**first parameter**」 · 키는 **내장 타입이 아니게** |
| **구현·도구** | `vet`·런타임이 한 것 | ★★ **`lostcancel` 은 `vet` 의 휴리스틱**(11 중 5) · **`stdversion` 은 `go 1.21` 미만 모듈에 침묵** · `key is not comparable` 패닉 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 나무의 참거짓 · 도착 순서의 가짓수 |

★★★ **선을 긋는다** — 「부모가 취소되면 자식이 취소된다」는 **문서의 계약**이다.
「**자식이 취소돼도 부모는 그대로**」는 그 계약의 **방향**이다 — 취소는 **아래로만** 흐른다((1)절의 `2 / 7`).
「`cancel` 을 부르지 않으면 샌다」도 계약이고, 그것을 **잡아 주는 것은 컴파일러가 아니라 `vet`** 이다((5)절).

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
```

```text
===== 명령: cd "$(go env GOROOT)/api" && grep -n "pkg context, func" go1.7.txt go1.20.txt go1.21.txt =====
go1.7.txt:6:pkg context, func Background() Context
go1.7.txt:7:pkg context, func TODO() Context
go1.7.txt:8:pkg context, func WithCancel(Context) (Context, CancelFunc)
go1.7.txt:9:pkg context, func WithDeadline(Context, time.Time) (Context, CancelFunc)
go1.7.txt:10:pkg context, func WithTimeout(Context, time.Duration) (Context, CancelFunc)
go1.7.txt:11:pkg context, func WithValue(Context, interface{}, interface{}) Context
go1.20.txt:6:pkg context, func Cause(Context) error #51365
go1.20.txt:7:pkg context, func WithCancelCause(Context) (Context, CancelCauseFunc) #51365
go1.21.txt:7:pkg context, func AfterFunc(Context, func()) func() bool #57928
go1.21.txt:8:pkg context, func WithDeadlineCause(Context, time.Time, error) (Context, CancelFunc) #56661
go1.21.txt:9:pkg context, func WithoutCancel(Context) Context #40221
go1.21.txt:10:pkg context, func WithTimeoutCause(Context, time.Duration, error) (Context, CancelFunc) #56661
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다(그래서 안 실었다)** | ★★★ **`Done` 이 도착한 순서** | 고루틴 스케줄링 — 200판을 돌려 「**두 가지 이상 나왔나 : 예**」 만 실었다(탐색 실행에서 50판 중 49가지) |
| 안 흔들린다 | ★★★ **노드마다 `Done 받았나=true/false` · `Err` · `7 / 7` · `2 / 7`** | 취소가 번지는 **범위**는 나무 모양이 정한다 |
| 안 흔들린다 | ★★★ **`lostcancel` 탐침 `답한 탐침 5 / 11`** · `vet` 문장 · `파일:줄:칸` | 정적 분석 |
| 안 흔들린다 | `vet 이 말한 판 2 / 5` · `Err` 문구 · `Cause` · 종료 코드 | |

★ 정규화 규칙은 **기본 넷**만 썼다.

## 한눈에 — 쉽게 말하면

**`context` 는 「회사의 지시 계통」이다.** 사장(부모)이 「이 일 접어」 하면 **부장·과장·사원 모두**에게 전달된다.
과장(자식)이 자기 팀 일을 접어도 **사장은 모른다** — 지시는 **아래로만** 흐른다.
사원은 지시를 **스스로 확인해야** 한다(`ctx.Done()` 을 보는 코드가 있어야 멈춘다).
그리고 이 계통에 **메모(값)** 를 붙일 수 있는데, **「id」 같은 흔한 이름표**를 쓰면 다른 부서 메모와 **섞인다.**

| 비유 | 실체 |
|---|---|
| 사장의 「접어」가 아래로 전달 | ★★★ **부모 `cancel()` → 파생된 모든 `Context` 의 `Done` 이 닫힌다**((1)절 `7 / 7`) |
| 과장이 접어도 사장은 계속 | ★★★ **자식 `cancel()` 은 부모·형제를 건드리지 않는다**((1)절 `2 / 7`) |
| 누가 먼저 소식을 듣나 | ★ **도착 순서는 흔들린다** — 「다 들었나」만 믿는다 |
| 「시간 다 됐다」와 「그만둬」 | ★★ **`DeadlineExceeded`** 대 **`Canceled`**((2)절) |
| 왜 접었는지 **사유서** | ★★ **`WithCancelCause`·`Cause`(1.20)**((3)절) |
| 지시를 받아 놓고 **서류 정리를 안 함** | ★★★ **`cancel` 을 안 부르면 샌다** — `vet lostcancel`((5)절) |
| 「id」라는 이름표 메모가 다른 부서 것과 섞임 | ★★★ **문자열 키 충돌** — `authstr.User` 가 **`req-42`** 를 돌려준다((4)절) |
| 부서만 아는 **전용 봉투** | ★★ **비공개 타입 키 `type userKey struct{}`** |

```text
   ★★★ 취소 전파 나무 ((1)절의 실측)

                         root (WithCancel)
             ┌──────────────┼──────────────────┐
         a (WithCancel)  b (WithTimeout 1h)  c (WithValue)
             │              │                  │
            a1             b1                 c1        (셋 다 WithCancel)

   root 를 cancel()  →  root a a1 b b1 c c1 : 전부 Done   →  7 / 7 · Err 전부 context canceled
   a 를 cancel()     →  a a1 만 Done · root b b1 c c1 은 Err=<nil>  →  2 / 7

   ★ 취소는 아래로만 흐른다 — 위(root)로도 옆(b·c)으로도 안 간다
   ★ c 는 WithValue 라 cancel 이 없는데도 root 의 취소를 받아 c1 까지 전한다
   ★ 누가 먼저 받았나(도착 순서)는 200판에서 두 가지 이상 — 근거로 쓰지 않는다
```

> **`context.Context`** — 데드라인·취소 신호·요청 범위 값을 **API 경계를 넘어** 나르는 인터페이스. `Done()`·`Err()`·`Deadline()`·`Value()` 넷.

> **파생(derive)** — `WithCancel(parent)` 처럼 부모에서 **자식** `Context` 를 만드는 것. 자식은 부모의 취소를 물려받는다.

- ★★ [30번 주제](../30-select-default-and-timeouts/) (7)절 — `ctx.Done()` 은 **취소되면 닫히는 채널**이라 `select` 의 가지 하나로 쓴다. 그 「한 번에 여럿을 깨운다」가 [29번 주제](../29-channels-buffering-direction-close-range-and-nil/) (4)절의 닫힌 채널이다.
- ★★ [31번 주제](../31-goroutine-leaks/) (3)절 — **`context` 로 누수를 고친 실측**(`ctxWait`·`ctxTicker`)은 거기가 정본이다.

## 이 주제가 답하려는 질문

1. **취소는 호출 나무를 따라 어떻게 번지나** — 누가 받고, 누가 안 받나.
2. **`cancel` 을 부르는 책임은 누구에게 있고, 안 부르면 누가 잡아 주나.**
3. **값 전달은 어디까지 괜찮나** — 키가 부딪히는 자리와 관례(첫 인자 · 구조체에 넣지 않기).

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **나무 노드별 `Done` 참거짓 로그** | 취소가 **어디까지** 번지나 | ★ 본체 창 |
| ★★ **도착 순서의 `sort -u` 가짓수** | 순서가 **흔들린다는 사실** 자체 | 규칙 11 |
| ★★★ **`vet lostcancel` × 탐침 11개** | `cancel` 누락을 **어디까지** 잡나 | 규칙 18-A |
| ★★ **`vet stdversion` × `go.mod` 판 5개** | 새 API 를 **옛 판 모듈**에서 쓰면 누가 말하나 | [24번 주제](../24-error-wrapping-and-errors-is-as-join/)의 `api/` 방식 + 판 격자 |
| ★★ **다중 패키지 모듈** | 문자열 키가 **패키지 사이에서** 부딪히는 것 | (4)절 |
| ★ **`go doc` 원문** | 관례(첫 인자 · 구조체 금지 · 키 타입) | 이 툴체인 |
| **부적용 — `-race`** | ★ 나무 블록은 `-race` 빌드로 돌렸고 보고 0 줄이다 — 그러나 이 주제의 질문(「누가 받나」)은 경쟁이 아니다 | [35번 주제](../35-data-races-and-the-race-detector/) |
| **부적용 — 시간** | 취소 전파가 **몇 µs 걸리나**는 안 쟀다 | — |
| **못 잰 것 — 외부 린터** | ★ `staticcheck`·`golangci-lint` 는 **이 머신에 없다**(아래 판별 블록) — 받지 않았다. **`go vet` 은 침묵**했다((4)절) | 규칙 26 |

```text
===== 명령: for t in staticcheck golangci-lint; do if command -v $t >/dev/null; then echo "$t: 있음"; else echo "$t: 없음"; fi; done; echo "GOPATH/bin: $(ls "$(go env GOPATH)/bin" 2>/dev/null | wc -l) 개" =====
staticcheck: 없음
golangci-lint: 없음
GOPATH/bin: 0 개
(exit 0)
```

### (1) ★★★ 취소 전파 나무 — 누가 `Done` 을 받나

**언제 쓰나** — 「이 `cancel()` 이 **어디까지** 멈추나」를 물을 때.

```go
// t34tree.go
package main

import (
	"context"
	"fmt"
	"os"
	"slices"
	"strings"
	"time"
)

type key struct{}

// 나무:            root (WithCancel)
//          ┌──────────┼──────────────┐
//         a (WithCancel)  b (WithTimeout 1h)  c (WithValue)
//          │           │              │
//         a1          b1             c1      (셋 다 WithCancel)
func main() {
	root, cancelRoot := context.WithCancel(context.Background())
	a, cancelA := context.WithCancel(root)
	b, cancelB := context.WithTimeout(root, time.Hour)
	c := context.WithValue(root, key{}, "v")
	a1, cancelA1 := context.WithCancel(a)
	b1, cancelB1 := context.WithCancel(b)
	c1, cancelC1 := context.WithCancel(c)
	defer func() { cancelA(); cancelB(); cancelA1(); cancelB1(); cancelC1(); cancelRoot() }()

	nodes := map[string]context.Context{"root": root, "a": a, "b": b, "c": c, "a1": a1, "b1": b1, "c1": c1}

	arrived := make(chan string, len(nodes))
	for name, ctx := range nodes {
		go func() {
			<-ctx.Done()
			arrived <- name
		}()
	}

	switch os.Args[1] {
	case "root":
		cancelRoot()
	case "a":
		cancelA()
	}

	var got []string
	timeout := time.After(200 * time.Millisecond)
collect:
	for {
		select {
		case n := <-arrived:
			got = append(got, n)
		case <-timeout:
			break collect
		}
	}
	if len(os.Args) > 2 && os.Args[2] == "order" {
		fmt.Println(strings.Join(got, " ")) // 도착 순서 그대로
		return
	}
	names := slices.Sorted(func(yield func(string) bool) {
		for n := range nodes {
			if !yield(n) {
				return
			}
		}
	})
	for _, n := range names {
		fmt.Printf("%-4s Done 받았나=%-5v Err=%v\n", n, slices.Contains(got, n), nodes[n].Err())
	}
	fmt.Printf("Done 을 받은 노드 %d / %d\n", len(got), len(nodes))
}
```

```text
===== 소스: t34tree.go =====
package main

import (
	"context"
	"fmt"
	"os"
	"slices"
	"strings"
	"time"
)

type key struct{}

// 나무:            root (WithCancel)
//          ┌──────────┼──────────────┐
//         a (WithCancel)  b (WithTimeout 1h)  c (WithValue)
//          │           │              │
//         a1          b1             c1      (셋 다 WithCancel)
func main() {
	root, cancelRoot := context.WithCancel(context.Background())
	a, cancelA := context.WithCancel(root)
	b, cancelB := context.WithTimeout(root, time.Hour)
	c := context.WithValue(root, key{}, "v")
	a1, cancelA1 := context.WithCancel(a)
	b1, cancelB1 := context.WithCancel(b)
	c1, cancelC1 := context.WithCancel(c)
	defer func() { cancelA(); cancelB(); cancelA1(); cancelB1(); cancelC1(); cancelRoot() }()

	nodes := map[string]context.Context{"root": root, "a": a, "b": b, "c": c, "a1": a1, "b1": b1, "c1": c1}

	arrived := make(chan string, len(nodes))
	for name, ctx := range nodes {
		go func() {
			<-ctx.Done()
			arrived <- name
		}()
	}

	switch os.Args[1] {
	case "root":
		cancelRoot()
	case "a":
		cancelA()
	}

	var got []string
	timeout := time.After(200 * time.Millisecond)
collect:
	for {
		select {
		case n := <-arrived:
			got = append(got, n)
		case <-timeout:
			break collect
		}
	}
	if len(os.Args) > 2 && os.Args[2] == "order" {
		fmt.Println(strings.Join(got, " ")) // 도착 순서 그대로
		return
	}
	names := slices.Sorted(func(yield func(string) bool) {
		for n := range nodes {
			if !yield(n) {
				return
			}
		}
	})
	for _, n := range names {
		fmt.Printf("%-4s Done 받았나=%-5v Err=%v\n", n, slices.Contains(got, n), nodes[n].Err())
	}
	fmt.Printf("Done 을 받은 노드 %d / %d\n", len(got), len(nodes))
}
===== 명령: go build -race -trimpath -o prog . && echo "--- root 를 취소" && ./prog root && echo "--- a 를 취소" && ./prog a =====
--- root 를 취소
a    Done 받았나=true  Err=context canceled
a1   Done 받았나=true  Err=context canceled
b    Done 받았나=true  Err=context canceled
b1   Done 받았나=true  Err=context canceled
c    Done 받았나=true  Err=context canceled
c1   Done 받았나=true  Err=context canceled
root Done 받았나=true  Err=context canceled
Done 을 받은 노드 7 / 7
--- a 를 취소
a    Done 받았나=true  Err=context canceled
a1   Done 받았나=true  Err=context canceled
b    Done 받았나=false Err=<nil>
b1   Done 받았나=false Err=<nil>
c    Done 받았나=false Err=<nil>
c1   Done 받았나=false Err=<nil>
root Done 받았나=false Err=<nil>
Done 을 받은 노드 2 / 7
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`root` 를 취소 — `Done 을 받은 노드 7 / 7`, `Err` 가 전부 `context canceled`.** 문서 「**When a Context is canceled, all Contexts derived from it are also canceled.**」 그대로다.
  ★★ **`b` 는 한 시간짜리 `WithTimeout`** 인데도 `DeadlineExceeded` 가 아니라 **`Canceled`** — 시간보다 **부모의 취소가 먼저** 왔다.
  ★★ **`c` 는 `WithValue`** — `cancel` 이 **없는** 노드인데 root 의 취소를 **그대로 보이고, 자식 `c1` 까지 전했다.** 값 노드는 **취소를 막지도 만들지도 않는다.**
- ★★★ **`a` 를 취소 — `2 / 7`.** `a` 와 그 자식 `a1` 만 받았고, **`root`·`b`·`b1`·`c`·`c1` 은 `Err=<nil>`.**
  **취소는 아래로만 흐른다** — 부모에게도, 형제에게도 가지 않는다.
- ★ 각 노드의 고루틴은 **`<-ctx.Done()` 을 스스로 기다린다.** 취소는 「고루틴을 죽이는 것」이 아니라 「**닫힌 채널을 보여 주는 것**」 이다 — 보지 않는 코드는 멈추지 않는다([ops-patterns 의 3-2절](../../../../../ops-patterns/deadline-propagation/) 「취소 신호를 넘기지 않으면 없는 것과 같다」).

**도착 순서는?** — 같은 나무를 200판:

```text
===== 소스: t34tree.go =====
package main

import (
	"context"
	"fmt"
	"os"
	"slices"
	"strings"
	"time"
)

type key struct{}

// 나무:            root (WithCancel)
//          ┌──────────┼──────────────┐
//         a (WithCancel)  b (WithTimeout 1h)  c (WithValue)
//          │           │              │
//         a1          b1             c1      (셋 다 WithCancel)
func main() {
	root, cancelRoot := context.WithCancel(context.Background())
	a, cancelA := context.WithCancel(root)
	b, cancelB := context.WithTimeout(root, time.Hour)
	c := context.WithValue(root, key{}, "v")
	a1, cancelA1 := context.WithCancel(a)
	b1, cancelB1 := context.WithCancel(b)
	c1, cancelC1 := context.WithCancel(c)
	defer func() { cancelA(); cancelB(); cancelA1(); cancelB1(); cancelC1(); cancelRoot() }()

	nodes := map[string]context.Context{"root": root, "a": a, "b": b, "c": c, "a1": a1, "b1": b1, "c1": c1}

	arrived := make(chan string, len(nodes))
	for name, ctx := range nodes {
		go func() {
			<-ctx.Done()
			arrived <- name
		}()
	}

	switch os.Args[1] {
	case "root":
		cancelRoot()
	case "a":
		cancelA()
	}

	var got []string
	timeout := time.After(200 * time.Millisecond)
collect:
	for {
		select {
		case n := <-arrived:
			got = append(got, n)
		case <-timeout:
			break collect
		}
	}
	if len(os.Args) > 2 && os.Args[2] == "order" {
		fmt.Println(strings.Join(got, " ")) // 도착 순서 그대로
		return
	}
	names := slices.Sorted(func(yield func(string) bool) {
		for n := range nodes {
			if !yield(n) {
				return
			}
		}
	})
	for _, n := range names {
		fmt.Printf("%-4s Done 받았나=%-5v Err=%v\n", n, slices.Contains(got, n), nodes[n].Err())
	}
	fmt.Printf("Done 을 받은 노드 %d / %d\n", len(got), len(nodes))
}
===== 명령: go build -race -trimpath -o prog . && for i in $(seq 200); do ./prog root order; done > got.txt; k=$(sort -u got.txt | wc -l); echo "200판 · 도착 순서가 두 가지 이상 나왔나: $([ $k -ge 2 ] && echo 예 || echo 아니오)"; echo "200판 · 모든 판이 일곱 노드를 다 담았나: $(awk "NF!=7{b=1} END{print b?\"아니오\":\"예\"}" got.txt)" =====
200판 · 도착 순서가 두 가지 이상 나왔나: 예
200판 · 모든 판이 일곱 노드를 다 담았나: 예
(exit 0)
```

- ★★★ **「도착 순서가 두 가지 이상 나왔나 : 예」 · 「모든 판이 일곱 노드를 다 담았나 : 예」.** 순서는 흔들리고, **「다 받았다」는 안 흔들린다.**
  ★ 그래서 「부모가 먼저 받고 자식이 나중에 받는다」 같은 **순서 가정 위에 코드를 세우면 안 된다.**

```text
   ★★ cancel() 이 하는 일 — 닫힌 채널을 보여 줄 뿐이다

   cancel()  ──▶  ctx.Done() 채널이 닫힌다  ──▶  ctx.Err() 가 Canceled 가 된다
                                  │
            ┌─────────────────────┴──────────────────────┐
     select { case <-ctx.Done(): return }          for { 일만 한다 }
     → 깨어나 끝난다                                → 아무 일도 없다 (보지 않으니까)
```

비용 — **안 쟀다.**

### (2) ★★ `Err` 두 가지 — 그리고 부모보다 긴 데드라인

```go
// t34err.go
package main

import (
	"context"
	"errors"
	"fmt"
	"time"
)

func main() {
	// ① 시간 초과로 끝난 것과 ② 취소로 끝난 것
	t, cancelT := context.WithTimeout(context.Background(), 10*time.Millisecond)
	defer cancelT()
	fmt.Println("① Done 전 Err:", t.Err())
	<-t.Done()
	fmt.Println("① Err:", t.Err())
	fmt.Println("① errors.Is(Err, DeadlineExceeded):", errors.Is(t.Err(), context.DeadlineExceeded))

	c, cancelC := context.WithCancel(context.Background())
	cancelC()
	fmt.Println("② Err:", c.Err())
	fmt.Println("② errors.Is(Err, Canceled):", errors.Is(c.Err(), context.Canceled))

	// ③ 부모보다 긴 데드라인을 준 자식
	parent, cancelP := context.WithTimeout(context.Background(), 50*time.Millisecond)
	defer cancelP()
	child, cancelCh := context.WithTimeout(parent, time.Hour)
	defer cancelCh()
	pd, _ := parent.Deadline()
	cd, _ := child.Deadline()
	fmt.Println("③ 자식 Deadline == 부모 Deadline:", cd.Equal(pd))
	<-child.Done()
	fmt.Println("③ 자식 Err:", child.Err())

	// ④ 이미 끝난 뒤 cancel 을 불러도
	cancelT()
	fmt.Println("④ 시간 초과 뒤 cancel() 한 Err:", t.Err())
}
```

```text
===== 소스: t34err.go =====
package main

import (
	"context"
	"errors"
	"fmt"
	"time"
)

func main() {
	// ① 시간 초과로 끝난 것과 ② 취소로 끝난 것
	t, cancelT := context.WithTimeout(context.Background(), 10*time.Millisecond)
	defer cancelT()
	fmt.Println("① Done 전 Err:", t.Err())
	<-t.Done()
	fmt.Println("① Err:", t.Err())
	fmt.Println("① errors.Is(Err, DeadlineExceeded):", errors.Is(t.Err(), context.DeadlineExceeded))

	c, cancelC := context.WithCancel(context.Background())
	cancelC()
	fmt.Println("② Err:", c.Err())
	fmt.Println("② errors.Is(Err, Canceled):", errors.Is(c.Err(), context.Canceled))

	// ③ 부모보다 긴 데드라인을 준 자식
	parent, cancelP := context.WithTimeout(context.Background(), 50*time.Millisecond)
	defer cancelP()
	child, cancelCh := context.WithTimeout(parent, time.Hour)
	defer cancelCh()
	pd, _ := parent.Deadline()
	cd, _ := child.Deadline()
	fmt.Println("③ 자식 Deadline == 부모 Deadline:", cd.Equal(pd))
	<-child.Done()
	fmt.Println("③ 자식 Err:", child.Err())

	// ④ 이미 끝난 뒤 cancel 을 불러도
	cancelT()
	fmt.Println("④ 시간 초과 뒤 cancel() 한 Err:", t.Err())
}
===== 명령: go build -trimpath -o prog . && ./prog =====
① Done 전 Err: <nil>
① Err: context deadline exceeded
① errors.Is(Err, DeadlineExceeded): true
② Err: context canceled
② errors.Is(Err, Canceled): true
③ 자식 Deadline == 부모 Deadline: true
③ 자식 Err: context deadline exceeded
④ 시간 초과 뒤 cancel() 한 Err: context deadline exceeded
(exit 0)
```

- ★★★ **① 시간 초과 → `context deadline exceeded`**(`errors.Is(…, DeadlineExceeded)` 가 `true`), **② 취소 → `context canceled`**. `Done` 전에는 **`<nil>`**.
- ★★★ **③ 부모 50ms 아래에 한 시간짜리 자식 — `자식 Deadline == 부모 Deadline: true`, 자식 `Err` 는 `deadline exceeded`.**
  자식은 **부모보다 늦게 끝날 수 없다.** 이 성질이 데드라인 전파 설계의 바탕이다 — 설계 쪽 서술은 [`../../../../../ops-patterns/deadline-propagation/`](../../../../../ops-patterns/deadline-propagation/) 「3. 전파 경로」가 정본이다.
- ★★ **④ 시간 초과 뒤 `cancel()` 을 불러도 `Err` 는 `deadline exceeded` 그대로** — **첫 원인이 남는다.** 그래서 `cancel` 은 끝난 뒤에 불러도 해가 없고, **`defer cancel()`** 이 기본형이 된다.

비용 — 없다.

### (3) ★★ 1.20·1.21 이 더한 것 — `Cause`·`AfterFunc`·`WithoutCancel`

```go
// t34cause.go
package main

import (
	"context"
	"errors"
	"fmt"
	"time"
)

var errQuota = errors.New("quota exhausted")

type key struct{}

func main() {
	// WithCancelCause · Cause (1.20)
	ctx, cancel := context.WithCancelCause(context.Background())
	child, cancelChild := context.WithCancel(ctx)
	defer cancelChild()
	cancel(errQuota)
	fmt.Println("[cause] Err:", ctx.Err(), "· Cause:", context.Cause(ctx))
	fmt.Println("[cause] 자식의 Cause:", context.Cause(child))
	plain, cancelPlain := context.WithCancel(context.Background())
	cancelPlain()
	fmt.Println("[cause] 원인 없이 취소한 것의 Cause:", context.Cause(plain))

	// WithTimeoutCause (1.21)
	tc, cancelTC := context.WithTimeoutCause(context.Background(), time.Millisecond, errQuota)
	defer cancelTC()
	<-tc.Done()
	fmt.Println("[timeoutCause] Err:", tc.Err(), "· Cause:", context.Cause(tc))

	// AfterFunc (1.21)
	ran := make(chan string, 2)
	a, cancelA := context.WithCancel(context.Background())
	stopA := context.AfterFunc(a, func() { ran <- "a" })
	cancelA()
	fmt.Println("[afterFunc] 취소 뒤 f 가 돌았나:", <-ran == "a", "· 그 뒤 stop():", stopA())
	b, cancelB := context.WithCancel(context.Background())
	stopB := context.AfterFunc(b, func() { ran <- "b" })
	fmt.Println("[afterFunc] 취소 전 stop():", stopB())
	cancelB()
	select {
	case n := <-ran:
		fmt.Println("[afterFunc] stop 뒤 취소하니 f 가 돌았다:", n)
	case <-time.After(50 * time.Millisecond):
		fmt.Println("[afterFunc] stop 뒤 취소 — 50ms 동안 f 가 안 돌았다")
	}

	// WithoutCancel (1.21)
	p, cancelP := context.WithTimeout(context.WithValue(context.Background(), key{}, "trace-7"), time.Hour)
	w := context.WithoutCancel(p)
	cancelP()
	_, hasDeadline := w.Deadline()
	fmt.Println("[withoutCancel] 부모 Err:", p.Err(), "· 자식 Err:", w.Err())
	fmt.Println("[withoutCancel] 자식 Done 이 nil 인가:", w.Done() == nil, "· Deadline 있나:", hasDeadline, "· 값:", w.Value(key{}))
}
```

```text
===== 소스: t34cause.go =====
package main

import (
	"context"
	"errors"
	"fmt"
	"time"
)

var errQuota = errors.New("quota exhausted")

type key struct{}

func main() {
	// WithCancelCause · Cause (1.20)
	ctx, cancel := context.WithCancelCause(context.Background())
	child, cancelChild := context.WithCancel(ctx)
	defer cancelChild()
	cancel(errQuota)
	fmt.Println("[cause] Err:", ctx.Err(), "· Cause:", context.Cause(ctx))
	fmt.Println("[cause] 자식의 Cause:", context.Cause(child))
	plain, cancelPlain := context.WithCancel(context.Background())
	cancelPlain()
	fmt.Println("[cause] 원인 없이 취소한 것의 Cause:", context.Cause(plain))

	// WithTimeoutCause (1.21)
	tc, cancelTC := context.WithTimeoutCause(context.Background(), time.Millisecond, errQuota)
	defer cancelTC()
	<-tc.Done()
	fmt.Println("[timeoutCause] Err:", tc.Err(), "· Cause:", context.Cause(tc))

	// AfterFunc (1.21)
	ran := make(chan string, 2)
	a, cancelA := context.WithCancel(context.Background())
	stopA := context.AfterFunc(a, func() { ran <- "a" })
	cancelA()
	fmt.Println("[afterFunc] 취소 뒤 f 가 돌았나:", <-ran == "a", "· 그 뒤 stop():", stopA())
	b, cancelB := context.WithCancel(context.Background())
	stopB := context.AfterFunc(b, func() { ran <- "b" })
	fmt.Println("[afterFunc] 취소 전 stop():", stopB())
	cancelB()
	select {
	case n := <-ran:
		fmt.Println("[afterFunc] stop 뒤 취소하니 f 가 돌았다:", n)
	case <-time.After(50 * time.Millisecond):
		fmt.Println("[afterFunc] stop 뒤 취소 — 50ms 동안 f 가 안 돌았다")
	}

	// WithoutCancel (1.21)
	p, cancelP := context.WithTimeout(context.WithValue(context.Background(), key{}, "trace-7"), time.Hour)
	w := context.WithoutCancel(p)
	cancelP()
	_, hasDeadline := w.Deadline()
	fmt.Println("[withoutCancel] 부모 Err:", p.Err(), "· 자식 Err:", w.Err())
	fmt.Println("[withoutCancel] 자식 Done 이 nil 인가:", w.Done() == nil, "· Deadline 있나:", hasDeadline, "· 값:", w.Value(key{}))
}
===== 명령: go build -trimpath -o prog . && ./prog =====
[cause] Err: context canceled · Cause: quota exhausted
[cause] 자식의 Cause: quota exhausted
[cause] 원인 없이 취소한 것의 Cause: context canceled
[timeoutCause] Err: context deadline exceeded · Cause: quota exhausted
[afterFunc] 취소 뒤 f 가 돌았나: true · 그 뒤 stop(): false
[afterFunc] 취소 전 stop(): true
[afterFunc] stop 뒤 취소 — 50ms 동안 f 가 안 돌았다
[withoutCancel] 부모 Err: context canceled · 자식 Err: <nil>
[withoutCancel] 자식 Done 이 nil 인가: true · Deadline 있나: false · 값: trace-7
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`[cause]` — `Err` 는 여전히 `context canceled`, `Cause` 가 `quota exhausted`.** `Err` 의 두 값 체계를 **안 바꾸고** 사유를 옆에 붙였다. **자식도 같은 `Cause`** 를 본다.
  ★ 원인 없이 취소한 것의 `Cause` 는 **`Err` 와 같다**(`context canceled`) — 문서 「If no cause is specified, Cause(ctx) returns the same value as ctx.Err()」.
- ★★ **`[timeoutCause]`** — 시간 초과에도 사유를 단다. `Err` 는 `deadline exceeded`, `Cause` 는 `quota exhausted`.
- ★★★ **`[afterFunc]` — 취소 뒤 `f` 가 돌았고, 그 뒤 `stop()` 은 `false`**(이미 돌았다). **취소 전 `stop()` 은 `true`** 이고, 그 뒤 취소해도 **50ms 동안 `f` 가 안 돌았다.**
  ★ `stop()` 의 `bool` 이 「**내가 막았나**」를 알려 준다.
- ★★★ **`[withoutCancel]` — 부모는 `canceled`, 자식은 `<nil>` · `Done` 이 `nil` · `Deadline 있나: false` · 값은 `trace-7`.**
  **취소와 데드라인은 끊고 값만** 물려받는다. 요청이 끝난 뒤에도 **남겨야 하는 일**(감사 로그 등 — 설계는 [`../../../../../ops-patterns/deadline-propagation/`](../../../../../ops-patterns/deadline-propagation/) 「5. 취소해도 남겨야 하는 것」)에 쓰는 자리다.
  ★ `Done()` 이 **`nil` 채널**이다 — `select` 에서 그 가지는 **영원히 안 뽑힌다**([29번 주제](../29-channels-buffering-direction-close-range-and-nil/) (5)절).

비용 — 없다.

### (4) ★★★ 값 전달의 경계 — 문자열 키가 부딪힌다

**언제 쓰나** — `ctx` 에 요청 id·사용자 같은 값을 실을 때. 두 패키지가 **각자 `"id"` 라는 문자열 키**를 골랐다:

```text
===== 소스: t34authstr.go =====
package authstr

import "context"

func WithUser(ctx context.Context, id string) context.Context {
	return context.WithValue(ctx, "id", id)
}

func User(ctx context.Context) (string, bool) {
	id, ok := ctx.Value("id").(string)
	return id, ok
}
===== 소스: t34authtyp.go =====
package authtyp

import "context"

type userKey struct{} // 비공개 타입 — 다른 패키지는 이 키를 만들 수 없다

func WithUser(ctx context.Context, id string) context.Context {
	return context.WithValue(ctx, userKey{}, id)
}

func User(ctx context.Context) (string, bool) {
	id, ok := ctx.Value(userKey{}).(string)
	return id, ok
}
===== 소스: t34keymain.go =====
package main

import (
	"context"
	"fmt"

	"ex/authstr"
	"ex/authtyp"
	"ex/tracestr"
	"ex/tracetyp"
)

func main() {
	ctx := context.Background()

	s := authstr.WithUser(ctx, "alice")
	s = tracestr.WithRequest(s, "req-42")
	u, ok := authstr.User(s)
	fmt.Printf("문자열 키 — authstr.User: %q ok=%v\n", u, ok)

	t := authtyp.WithUser(ctx, "alice")
	t = tracetyp.WithRequest(t, "req-42")
	u, ok = authtyp.User(t)
	fmt.Printf("비공개 타입 키 — authtyp.User: %q ok=%v\n", u, ok)
}
===== 소스: t34tracestr.go =====
package tracestr

import "context"

func WithRequest(ctx context.Context, id string) context.Context {
	return context.WithValue(ctx, "id", id)
}
===== 소스: t34tracetyp.go =====
package tracetyp

import "context"

type requestKey struct{}

func WithRequest(ctx context.Context, id string) context.Context {
	return context.WithValue(ctx, requestKey{}, id)
}
===== 명령: go vet ./... && echo "vet exit=$?" && go build -trimpath -o prog . && ./prog =====
vet exit=0
문자열 키 — authstr.User: "req-42" ok=true
비공개 타입 키 — authtyp.User: "alice" ok=true
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`문자열 키 — authstr.User: "req-42" ok=true`** — 인증 패키지는 `"alice"` 를 넣었는데 **추적 패키지의 `"req-42"` 가 나왔다.** 뒤에 넣은 `WithValue` 가 같은 키를 **가렸다.**
  ★★★ **`ok=true`** 다 — 타입도 `string` 으로 같아서 **아무 에러도 없다.** 틀린 사용자로 **조용히** 진행된다.
- ★★★ **`비공개 타입 키 — authtyp.User: "alice" ok=true`** — `type userKey struct{}` 는 **그 패키지 밖에서 만들 수 없는** 키다. 다른 패키지가 같은 키를 **원리상** 못 쓴다.
- ★★ **`vet exit=0`** — `go vet` 은 문자열 키에 **침묵**했다(탐침 1, 답 0 — 규칙 18-A).
- ★ 문서가 이 모든 것을 말한다:

```text
===== 명령: go doc context.WithValue =====
package context // import "context"

func WithValue(parent Context, key, val any) Context
    WithValue returns a derived context that points to the parent Context.
    In the derived context, the value associated with key is val.

    Use context Values only for request-scoped data that transits processes and
    APIs, not for passing optional parameters to functions.

    The provided key must be comparable and should not be of type string or any
    other built-in type to avoid collisions between packages using context.
    Users of WithValue should define their own types for keys. To avoid
    allocating when assigning to an interface{}, context keys often have
    concrete type struct{}. Alternatively, exported context key variables'
    static type should be a pointer or interface.
(exit 0)
```

  ★★★ 「**should not be of type string or any other built-in type to avoid collisions between packages using context. Users of WithValue should define their own types for keys.**」
  ★★★ 「**Use context Values only for request-scoped data that transits processes and APIs, not for passing optional parameters to functions.**」 — **값 전달 남용의 경계**가 이 한 문장이다. 함수의 선택 인자를 `ctx` 에 숨기면 **시그니처에서 사라진다.**

키가 **비교할 수 없는** 타입이면 —

```go
// t34nokey.go
package main

import (
	"context"
	"fmt"
)

func main() {
	defer func() { fmt.Println("recover:", recover()) }()
	_ = context.WithValue(context.Background(), []string{"id"}, 1)
	fmt.Println("WithValue 가 돌아왔다")
}
```

```text
===== 소스: t34nokey.go =====
package main

import (
	"context"
	"fmt"
)

func main() {
	defer func() { fmt.Println("recover:", recover()) }()
	_ = context.WithValue(context.Background(), []string{"id"}, 1)
	fmt.Println("WithValue 가 돌아왔다")
}
===== 명령: go vet . && echo "vet exit=$?" && go build -trimpath -o prog . && ./prog =====
vet exit=0
recover: key is not comparable
(exit 0)
```

- ★★ **`recover: key is not comparable`** — 컴파일은 되고(`vet exit=0`) **`WithValue` 가 실행 중에 패닉**했다. 문서 「The provided key must be comparable」의 모양이다.

비용 — 없다.

### (5) ★★★ `cancel` 을 안 부르면 — `vet lostcancel` 탐침 11개

문서가 먼저 말한다:

```text
===== 명령: go doc context | sed -n "12,21p;33,43p" =====
A Context may be canceled to indicate that work done on its behalf should stop.
A Context with a deadline is canceled after the deadline passes. When a Context
is canceled, all Contexts derived from it are also canceled.

The WithCancel, WithDeadline, and WithTimeout functions take a Context (the
parent) and return a derived Context (the child) and a CancelFunc. Calling the
CancelFunc directly cancels the child and its children, removes the parent's
reference to the child, and stops any associated timers. Failing to call the
CancelFunc leaks the child and its children until the parent is canceled.
The go vet tool checks that CancelFuncs are used on all control-flow paths.
Do not store Contexts inside a struct type; instead, pass a Context
explicitly to each function that needs it. This is discussed further in
https://go.dev/blog/context-and-structs. The Context should be the first
parameter, typically named ctx:

    func DoSomething(ctx context.Context, arg Arg) error {
    	// ... use ctx ...
    }

Do not pass a nil Context, even if a function permits it. Pass context.TODO if
you are unsure about which Context to use.
(exit 0)
```

- ★★★ 「**Failing to call the CancelFunc leaks the child and its children until the parent is canceled. The go vet tool checks that CancelFuncs are used on all control-flow paths.**」
- ★★★ 「**Do not store Contexts inside a struct type; instead, pass a Context explicitly to each function that needs it.**」 · 「**The Context should be the first parameter, typically named ctx**」 — **관례**다. ★ 이 둘을 **검사하는 도구는 이 판 `vet` 에 없다**(`go tool vet help` 목록에 해당 분석기가 없다 — [32번 주제](../32-sync-mutex-rwmutex-waitgroup-once/)의 목록 블록 참고). **문서의 관례를 지키는 것은 사람**이다.

그러면 `vet` 은 `cancel` 누락을 **어디까지** 잡나:

```go
// t34lost.go
package main

import (
	"context"
	"time"
)

type holder struct{ stop context.CancelFunc }

func use(context.Context) {}

func p01() {
	ctx, _ := context.WithCancel(context.Background()) // p01
	use(ctx)
}

func p02(fail bool) error {
	ctx, cancel := context.WithTimeout(context.Background(), time.Second) // p02
	if fail {
		return nil
	}
	defer cancel()
	use(ctx)
	return nil
}

func p03() {
	ctx, cancel := context.WithCancel(context.Background()) // p03
	_ = cancel
	use(ctx)
}

func p04() {
	ctx, cancel := context.WithDeadline(context.Background(), time.Now()) // p04
	use(ctx)
	if false {
		cancel()
	}
}

func p05() {
	ctx, cancel := context.WithCancel(context.Background()) // p05
	defer cancel()
	use(ctx)
}

func p06() context.CancelFunc {
	ctx, cancel := context.WithCancel(context.Background()) // p06
	use(ctx)
	return cancel
}

func p07(h *holder) {
	ctx, cancel := context.WithCancel(context.Background()) // p07
	h.stop = cancel
	use(ctx)
}

func p08() {
	ctx, cancel := context.WithCancel(context.Background()) // p08
	go func() {
		defer cancel()
		use(ctx)
	}()
}

func p09() {
	ctx, _ := context.WithCancelCause(context.Background()) // p09
	use(ctx)
}

func p10() {
	var ctx context.Context
	ctx, _ = context.WithTimeout(context.Background(), time.Second) // p10
	use(ctx)
}

func register(context.CancelFunc) {}

func p11() {
	ctx, cancel := context.WithCancel(context.Background()) // p11
	register(cancel)
	use(ctx)
}

func main() {
	p01()
	_ = p02(false)
	p03()
	p04()
	p05()
	p06()()
	p07(&holder{})
	p08()
	p09()
	p10()
	p11()
}
```

```text
===== 소스: t34lost.go =====
package main

import (
	"context"
	"time"
)

type holder struct{ stop context.CancelFunc }

func use(context.Context) {}

func p01() {
	ctx, _ := context.WithCancel(context.Background()) // p01
	use(ctx)
}

func p02(fail bool) error {
	ctx, cancel := context.WithTimeout(context.Background(), time.Second) // p02
	if fail {
		return nil
	}
	defer cancel()
	use(ctx)
	return nil
}

func p03() {
	ctx, cancel := context.WithCancel(context.Background()) // p03
	_ = cancel
	use(ctx)
}

func p04() {
	ctx, cancel := context.WithDeadline(context.Background(), time.Now()) // p04
	use(ctx)
	if false {
		cancel()
	}
}

func p05() {
	ctx, cancel := context.WithCancel(context.Background()) // p05
	defer cancel()
	use(ctx)
}

func p06() context.CancelFunc {
	ctx, cancel := context.WithCancel(context.Background()) // p06
	use(ctx)
	return cancel
}

func p07(h *holder) {
	ctx, cancel := context.WithCancel(context.Background()) // p07
	h.stop = cancel
	use(ctx)
}

func p08() {
	ctx, cancel := context.WithCancel(context.Background()) // p08
	go func() {
		defer cancel()
		use(ctx)
	}()
}

func p09() {
	ctx, _ := context.WithCancelCause(context.Background()) // p09
	use(ctx)
}

func p10() {
	var ctx context.Context
	ctx, _ = context.WithTimeout(context.Background(), time.Second) // p10
	use(ctx)
}

func register(context.CancelFunc) {}

func p11() {
	ctx, cancel := context.WithCancel(context.Background()) // p11
	register(cancel)
	use(ctx)
}

func main() {
	p01()
	_ = p02(false)
	p03()
	p04()
	p05()
	p06()()
	p07(&holder{})
	p08()
	p09()
	p10()
	p11()
}
===== 명령: go vet . 2>vet.txt; echo "vet exit=$?"; cat vet.txt; n=0; m=0; for p in $(grep -o "// p[0-9][0-9]" t34lost.go | cut -c4-); do L=$(grep -n "// $p\$" t34lost.go | cut -d: -f1); m=$((m+1)); if grep -q "^t34lost.go:$L:" vet.txt; then n=$((n+1)); echo "$p (줄 $L) : 답함"; else echo "$p (줄 $L) : 침묵"; fi; done; echo "답한 탐침 $n / $m" =====
vet exit=1
t34lost.go:13:7: the cancel function returned by context.WithCancel should be called, not discarded, to avoid a context leak
t34lost.go:18:2: the cancel function is not used on all paths (possible context leak)
t34lost.go:20:3: this return statement may be reached without using the cancel var defined on line 18
t34lost.go:34:2: the cancel function is not used on all paths (possible context leak)
t34lost.go:39:1: this return statement may be reached without using the cancel var defined on line 34
t34lost.go:68:7: the cancel function returned by context.WithCancelCause should be called, not discarded, to avoid a context leak
t34lost.go:74:7: the cancel function returned by context.WithTimeout should be called, not discarded, to avoid a context leak
p01 (줄 13) : 답함
p02 (줄 18) : 답함
p03 (줄 28) : 침묵
p04 (줄 34) : 답함
p05 (줄 42) : 침묵
p06 (줄 48) : 침묵
p07 (줄 54) : 침묵
p08 (줄 60) : 침묵
p09 (줄 68) : 답함
p10 (줄 74) : 답함
p11 (줄 81) : 침묵
답한 탐침 5 / 11
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **마지막 줄 `답한 탐침 5 / 11`.** 스크립트가 `vet` 줄의 줄 번호를 `// pNN` 주석과 맞춰 셌다.
- ★★★ **답한 5** — `_` 로 버리기(p01 `WithCancel` · p09 `WithCancelCause` · p10 `=` 대입의 `WithTimeout`) · **어떤 경로에서 안 부름**(p02 이른 `return` · p04 `if false` 안에만).
  ★ p02 는 **두 줄**로 답한다 — 「not used on all paths」(18행)와 「this return statement may be reached」(20행).
- ★★★ **침묵 6** — 그중 **다섯은 옳은 침묵**이다: p05 `defer cancel()` · p06 **돌려준다** · p07 **구조체 필드에 저장** · p08 **다른 고루틴에서 `defer`** · p11 **다른 함수에 넘긴다**.
  ★★★ **p03 `_ = cancel` 만 진짜 놓친 칸**이다 — 한 번 **「쓴」 것으로 쳐서** 넘어갔다. 실제로는 **아무도 안 부른다.**
- ★★ **컴파일러는 11 개 전부 통과시킨다** — `lostcancel` 은 **`vet` 의 휴리스틱**이다.

비용 — 없다.

### (6) ★★ 판 경계 — `api/go1NN.txt` 와 `go.mod` 가 막아 주나

| API | 판 | 근거(머리말 블록) |
|---|---|---|
| `Background`·`TODO`·`WithCancel`·`WithDeadline`·`WithTimeout`·`WithValue` | **1.7** | `go1.7.txt:6-11` |
| **`WithCancelCause`·`Cause`** | **1.20** | `go1.20.txt:6-7` |
| **`AfterFunc`·`WithoutCancel`·`WithDeadlineCause`·`WithTimeoutCause`** | **1.21** | `go1.21.txt:7-10` |

그러면 `go.mod` 가 `go 1.19` 인 모듈에서 1.20·1.21 API 를 쓰면? — 같은 파일을 `go` 줄만 바꿔 다섯 판:

```go
// t34ver.go
package main

import (
	"context"
	"fmt"
	"sync"
)

func main() {
	ctx, cancel := context.WithCancelCause(context.Background()) // 1.20
	stop := context.AfterFunc(ctx, func() {})                    // 1.21
	defer stop()
	cancel(nil)
	var m sync.Map
	m.Store("k", 1)
	m.Clear() // 1.23
	fmt.Println("빌드되어 돌았다")
}
```

```text
===== 소스: t34ver.go =====
package main

import (
	"context"
	"fmt"
	"sync"
)

func main() {
	ctx, cancel := context.WithCancelCause(context.Background()) // 1.20
	stop := context.AfterFunc(ctx, func() {})                    // 1.21
	defer stop()
	cancel(nil)
	var m sync.Map
	m.Store("k", 1)
	m.Clear() // 1.23
	fmt.Println("빌드되어 돌았다")
}
===== 명령: n=0; for v in 1.19 1.20 1.21 1.22 1.23; do printf "module ex\n\ngo $v\n" > go.mod; go build -trimpath -o prog . && b=$(./prog); go vet . 2>vet.txt; rc=$?; if [ $rc -ne 0 ]; then n=$((n+1)); fi; echo "[go $v] 실행: $b · vet exit=$rc $(cat vet.txt)"; done; echo "vet 이 말한 판 $n / 5" =====
[go 1.19] 실행: 빌드되어 돌았다 · vet exit=0 
[go 1.20] 실행: 빌드되어 돌았다 · vet exit=0 
[go 1.21] 실행: 빌드되어 돌았다 · vet exit=1 t34ver.go:16:4: sync.(*Map).Clear requires go1.23 or later (module is go1.21)
[go 1.22] 실행: 빌드되어 돌았다 · vet exit=1 t34ver.go:16:4: sync.(*Map).Clear requires go1.23 or later (module is go1.22)
[go 1.23] 실행: 빌드되어 돌았다 · vet exit=0 
vet 이 말한 판 2 / 5
(exit 0)
```

- ★★★ **다섯 판 전부 빌드되고 돌았다.** 표준 라이브러리는 **툴체인의 것**(1.27.1)이라 **컴파일러는 `go` 줄로 API 를 막지 않는다.**
- ★★★ **`vet 이 말한 판 2 / 5`** — `go 1.21`·`1.22` 에서만 `sync.(*Map).Clear requires go1.23 or later` 를 말했다.
  ★★★ **`go 1.19`·`1.20` 은 침묵** — 그 판에서는 `Clear`(1.23)도 `AfterFunc`(1.21)도 `WithCancelCause`(1.20)도 **다 너무 새것인데** 한 줄도 없다. 분석기 소스가 이유를 적는다:

```text
===== 명령: sed -n "54,60p" "$(go env GOROOT)/src/cmd/vendor/golang.org/x/tools/go/analysis/passes/stdversion/stdversion.go" =====
	// Don't report diagnostics for modules marked before go1.21,
	// since at that time the go directive wasn't clearly
	// specified as a toolchain requirement.
	pkgVersion := pass.Pkg.GoVersion()
	if !versions.AtLeast(pkgVersion, "go1.21") {
		return nil, nil
	}
(exit 0)
```

  ★★ 「**Don't report diagnostics for modules marked before go1.21, since at that time the go directive wasn't clearly specified as a toolchain requirement.**」 — **1.21 미만 모듈에는 일부러 침묵한다.** 그래서 **`context` 의 1.20·1.21 API 는 이 분석기로 판 경계를 지킬 수 없다**(1.21 모듈에서는 이미 쓸 수 있는 API 라 말할 것이 없다).
- ★ 그러니 **판 경계는 `api/` 표로 확인한다** — 도구가 지켜 주는 것은 **1.21 이상 모듈의, 그보다 새 API** 뿐이다.

비용 — 없다.

## 문법 — 형태와 규칙

### 형태

```go
// t34err.go
package main

import (
	"context"
	"errors"
	"fmt"
	"time"
)

func main() {
	// ① 시간 초과로 끝난 것과 ② 취소로 끝난 것
	t, cancelT := context.WithTimeout(context.Background(), 10*time.Millisecond)
	defer cancelT()
	fmt.Println("① Done 전 Err:", t.Err())
	<-t.Done()
	fmt.Println("① Err:", t.Err())
	fmt.Println("① errors.Is(Err, DeadlineExceeded):", errors.Is(t.Err(), context.DeadlineExceeded))

	c, cancelC := context.WithCancel(context.Background())
	cancelC()
	fmt.Println("② Err:", c.Err())
	fmt.Println("② errors.Is(Err, Canceled):", errors.Is(c.Err(), context.Canceled))

	// ③ 부모보다 긴 데드라인을 준 자식
	parent, cancelP := context.WithTimeout(context.Background(), 50*time.Millisecond)
	defer cancelP()
	child, cancelCh := context.WithTimeout(parent, time.Hour)
	defer cancelCh()
	pd, _ := parent.Deadline()
	cd, _ := child.Deadline()
	fmt.Println("③ 자식 Deadline == 부모 Deadline:", cd.Equal(pd))
	<-child.Done()
	fmt.Println("③ 자식 Err:", child.Err())

	// ④ 이미 끝난 뒤 cancel 을 불러도
	cancelT()
	fmt.Println("④ 시간 초과 뒤 cancel() 한 Err:", t.Err())
}
```

규칙 불릿.

- ★★★ **`ctx context.Context` 는 첫 인자, 이름은 `ctx`** — 문서의 관례.
- ★★★ **구조체 필드에 넣지 않는다** — 함수마다 넘긴다(문서). 이 판 `vet` 은 **검사하지 않는다.**
- ★★★ **`WithCancel`·`WithTimeout`·`WithDeadline` 을 만들면 바로 다음 줄에 `defer cancel()`** — 끝난 뒤 불러도 `Err` 는 안 바뀐다((2)절 ④).
- ★★ **취소는 아래로만** — 자식 `cancel()` 로 부모를 멈출 수 없다.
- ★★ **`Err` 는 `Canceled`·`DeadlineExceeded` 둘뿐** — 사유는 **`Cause`**(1.20).
- ★★★ **값 키는 비공개 타입**(`type userKey struct{}`) — 문자열·내장 타입 금지. 값은 **요청 범위 데이터만.**
- ★ `nil` `Context` 를 넘기지 않는다 — 모르면 **`context.TODO()`**(문서).

### 금지 사례 — 컴파일은 되고 도구·실행이 잡거나 아무도 안 잡는 것

| 쓴 꼴 | 누가 잡나 | 어디서 |
|---|---|---|
| `ctx, _ := context.WithCancel(…)` | `vet` — `should be called, not discarded` | (5)절 p01 |
| 이른 `return` 뒤에 `defer cancel()` | `vet` — `not used on all paths` | p02 |
| `_ = cancel` | ★★★ **아무도 안 잡는다** | p03 |
| 두 패키지가 문자열 키 `"id"` | ★★★ **아무도 안 잡는다**(`vet` 침묵, `ok=true`) | (4)절 |
| 비교할 수 없는 키 | 실행 — `panic: key is not comparable` | (4)절 |
| `go 1.20` 모듈에서 1.21 API | ★★ **아무도 안 잡는다**(빌드 통과 · `stdversion` 은 1.21 미만에 침묵) | (6)절 |
| 구조체에 `ctx` 저장 | 이 판 `vet` 에 분석기 없음 — **문서의 관례** | (5)절 |

## 어디서 틀리나

### 1. ★★★ 「자식을 취소하면 부모도 멈춘다」

- (1)절 실측 — **`a` 취소는 `2 / 7`**, root 는 `<nil>`. 위로 올리고 싶으면 **부모의 `cancel` 을 불러야** 한다.

### 2. ★★★ 「`cancel()` 하면 고루틴이 멈춘다」

- 취소는 **`Done` 을 닫을 뿐**이다. **`ctx.Done()` 을 보지 않는 코드는 안 멈춘다**([31번 주제](../31-goroutine-leaks/) (3)절이 `select` 가지로 고친 실측).

### 3. ★★★ 「`vet` 이 조용하면 `cancel` 누락이 없다」

- (5)절 실측 — **11 중 5**, **`_ = cancel` 은 침묵.**

### 4. ★★★ 「문자열 키면 충분하다」

- (4)절 실측 — **`"alice"` 대신 `"req-42"`, `ok=true`.** 비공개 타입 키로.

### 5. ★★ 「부모보다 긴 타임아웃을 주면 자식은 더 오래 산다」

- (2)절 ③ — **`자식 Deadline == 부모 Deadline: true`.**

### 6. ★★ 「`go 1.20` 모듈이면 1.21 API 는 컴파일 에러가 난다」

- (6)절 — **빌드된다.** `stdversion` 도 1.21 미만에서는 침묵한다.

### 7. ★ 「먼저 취소된 부모가 먼저 `Done` 을 받는다」

- (1)절 — 도착 순서는 **200판에서 두 가지 이상.** 순서에 기대지 않는다.

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| `Done()` 이 닫히면 모든 받는 쪽이 깨어난다 | **명세**(닫힌 채널) | [29번 주제](../29-channels-buffering-direction-close-range-and-nil/) |
| ★★★ **부모 취소 → 파생된 모두 취소 · 자식 취소는 부모에 안 감** | **표준 라이브러리 계약** | (1)절 |
| `Err` 는 `Canceled`/`DeadlineExceeded` · 첫 원인이 남는다 | **표준 라이브러리 계약** | (2)절 |
| 자식 데드라인은 부모를 넘지 못한다 | **표준 라이브러리 계약**(관찰로 확인) | (2)절 ③ |
| `Cause`·`AfterFunc`·`WithoutCancel` 의 동작 | **표준 라이브러리 계약** | (3)절 |
| ★★★ **첫 인자 · 구조체 금지 · 키 타입** | **문서의 관례**(도구 없음) | (4)·(5)절 |
| ★★ **`lostcancel` 11 중 5 · `stdversion` 의 1.21 미만 침묵** | **도구(`vet`)의 휴리스틱·정책** | (5)·(6)절 |
| `key is not comparable` 패닉 | **표준 라이브러리 구현** | (4)절 |
| `Done` 도착 순서 | ★ **흔들린다 — 약속 없음** | (1)절 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 요청 하나의 작업 전체 | **`r.Context()` 를 받아 첫 인자로 계속 넘긴다** | 문서 · 설계는 ops-patterns 정본 |
| 한 단계에 시간 상한 | **`WithTimeout` + `defer cancel()`** | (2)절 |
| 왜 취소됐는지 로그에 남기기 | **`WithCancelCause` + `Cause`** | (3)절 |
| 취소되면 정리 함수 하나 | **`AfterFunc`**(`stop()` 의 `bool` 확인) | (3)절 |
| 요청이 끝나도 남겨야 할 일 | **`WithoutCancel`** — 값은 유지 | (3)절 |
| 요청 id·인증 주체 | **`WithValue` + 비공개 타입 키** | (4)절 |
| 선택 인자·설정 | ★★ **`ctx` 에 넣지 않는다** — 함수 인자로 | (4)절 문서 |

## 핵심 문장

- ★★★ **부모를 취소하면 7 / 7, 자식 하나를 취소하면 2 / 7** — 취소는 **아래로만** 흐르고, `WithValue` 노드도 그대로 전한다.
- ★★★ **도착 순서는 흔들린다**(200판에서 두 가지 이상) — 근거는 「**다 받았나**」 다.
- ★★ **시간 초과는 `DeadlineExceeded`, 취소는 `Canceled`** — 끝난 뒤 `cancel()` 해도 첫 원인이 남는다. **자식 데드라인은 부모를 못 넘는다.**
- ★★ **1.20 `Cause`, 1.21 `AfterFunc`·`WithoutCancel`** — `WithoutCancel` 은 취소·데드라인을 끊고 **값만** 남긴다.
- ★★★ **`vet lostcancel` 은 11 중 5** — **`_ = cancel` 을 놓친다.** 구조체 금지·첫 인자는 **도구가 없는 관례**다.
- ★★★ **문자열 키 `"id"` 가 두 패키지에서 부딪혀 `"req-42"`, `ok=true`** — 비공개 타입 키로 막는다. `vet` 은 침묵했다.
- ★★ **`go 1.19`/`1.20` 모듈에서도 1.21 API 가 빌드된다** — `stdversion` 은 **1.21 미만 모듈에 일부러 침묵**한다(`2 / 5`).

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 34번)
- [`../../../../../ops-patterns/deadline-propagation/`](../../../../../ops-patterns/deadline-propagation/) — ★★ **정본 경계.** 타임아웃 대 데드라인 · 전파 경로(진입점 → 작업 → DB → 외부 → 큐) · 취소가 닿지 않는 곳 · 감사 로그는 **거기**, 여기는 **`context` 의 API·관례·함정부터.**
- [31번 주제](../31-goroutine-leaks/)(누수) — ★ 목록상 선행 · `context` 로 누수를 고친 실측
- [30번 주제](../30-select-default-and-timeouts/)(`select`) — `case <-ctx.Done()` 의 자리
- [29번 주제](../29-channels-buffering-direction-close-range-and-nil/)(채널) — 닫힌 채널 · `nil` 채널
- [24번 주제](../24-error-wrapping-and-errors-is-as-join/)(`errors.Is`) — `DeadlineExceeded` 판별
- [33번 주제](../33-sync-atomic-and-sync-map/) — `sync.Map.Clear`(1.23)
- 목록의 **51번 주제**(`os/signal` 과 정상 종료) — 신호로 `context` 를 취소하는 배선

## 용어 풀이

- **`Context`** — 데드라인·취소·값을 나르는 인터페이스.
- **`CancelFunc`** — 파생된 `Context` 를 취소하는 함수. 부르지 않으면 자식이 부모가 취소될 때까지 남는다.
- **`Done()`** — 취소되면 닫히는 채널. `WithoutCancel`·`Background` 는 `nil`.
- **`Err()`** — `nil` · `Canceled` · `DeadlineExceeded` 셋 중 하나.
- **`Cause`** — 취소 사유(1.20). 사유가 없으면 `Err` 와 같다.
- **`AfterFunc`** — 취소되면 `f` 를 자기 고루틴에서 돌린다. `stop()` 이 `true` 면 막은 것이다(1.21).
- **`WithoutCancel`** — 취소·데드라인은 끊고 값만 물려받는 자식(1.21).
- **`lostcancel`** — `cancel` 이 모든 경로에서 쓰이나 보는 `vet` 분석기.
- **`stdversion`** — `go.mod` 의 판보다 새 표준 API 를 쓰면 알리는 `vet` 분석기. **1.21 미만 모듈은 안 본다.**

---

## 더 들어가면

- ★ **`net/http` 가 연결이 끊기면 `Request.Context()` 를 취소하는 것**은 [ops-patterns 정본](../../../../../ops-patterns/deadline-propagation/) 「2. 고아 작업」 이 인용한다 — 여기서는 **안 던졌다.**
- ★ 문서가 가리키는 블로그 글(context-and-structs)은 **안 열었다.**
- ★ 취소 전파가 **자식 수에 따라 어떻게 비용이 드나**(구현 — 자식 맵)는 **안 열었다.**
- ★ `staticcheck` 등 **외부 린터**가 문자열 키를 잡는지는 **이 머신에서 확인 못 했다.**

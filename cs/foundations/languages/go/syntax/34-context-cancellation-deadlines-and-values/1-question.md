# go/syntax/34 — ★ `context`: 취소·데드라인·값 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ **모든 문제에서 「이 취소는 나무의 어느 방향으로 흐르나 — 아래·위·옆」을 먼저 그려라.**
> ★★ **「이것은 문서의 계약인가, 관례인가, 도구의 휴리스틱인가」를 매번 물어라.**
> 소스는 전부 `go build -trimpath -o prog .`(표시한 것은 `-race` 를 붙여) 로 빌드했다. 모듈 이름은 `ex` 다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 나무의 어디를 끊느냐 (예측)

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

<!-- -race 빌드. ./prog root 와 ./prog a 를 차례로 돌린다. 노드마다 「Done 받았나」·Err 를 이름순으로 찍고 마지막 줄에 받은 노드 수를 센다. -->

- `root` 를 취소한 판에서 일곱 노드의 `Done 받았나`·`Err` 는? `b` 의 `Err` 는 무엇인가?
- `a` 를 취소한 판에서는? 마지막 줄의 수는?
- `c`(`WithValue`)는 취소를 어떻게 다루나?

### 2. 도착 순서 (왜)

- 같은 나무에서 **누가 먼저 `Done` 을 받았나**를 근거로 쓰지 않는 이유는? 그 대신 무엇을 근거로 쓰나?

### 3. `Err` 두 가지와 부모보다 긴 데드라인 (예측)

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

- ①·② 의 `Err` 와 `errors.Is` 는?
- ③ 자식의 데드라인은 부모와 같나? 자식의 `Err` 는?
- ④ 시간 초과 뒤 `cancel()` 을 부르면 `Err` 가 바뀌나?

### 4. 1.20·1.21 이 더한 것 (예측)

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

- `[cause]` 세 줄은? 원인 없이 취소한 것의 `Cause` 는?
- `[afterFunc]` 의 두 `stop()` 값과 마지막 줄은?
- `[withoutCancel]` 의 자식 `Err`·`Done`·`Deadline`·값은?

### 5. 두 패키지의 같은 문자열 키 (예측)

```go
// t34authstr.go
package authstr

import "context"

func WithUser(ctx context.Context, id string) context.Context {
	return context.WithValue(ctx, "id", id)
}

func User(ctx context.Context) (string, bool) {
	id, ok := ctx.Value("id").(string)
	return id, ok
}
```

```go
// t34tracestr.go
package tracestr

import "context"

func WithRequest(ctx context.Context, id string) context.Context {
	return context.WithValue(ctx, "id", id)
}
```

```go
// t34authtyp.go
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
```

```go
// t34tracetyp.go
package tracetyp

import "context"

type requestKey struct{}

func WithRequest(ctx context.Context, id string) context.Context {
	return context.WithValue(ctx, requestKey{}, id)
}
```

```go
// t34keymain.go
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
```

<!-- go vet ./... 후 빌드해 돌린다. -->

- `go vet` 은 무엇을 말하나?
- 두 줄의 출력은? 첫 줄의 `ok` 는?

### 6. `cancel` 누락 탐침 11개 (예측)

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

<!-- go vet . 의 출력을 받고, 셸이 // pNN 주석의 줄 번호와 vet 줄의 줄 번호를 맞춰 탐침마다 답함/침묵을 찍는다. 마지막 줄에 답한 탐침 수 / 11. -->

- 몇 개가 답하나?
- 침묵하는 탐침 중 **옳은 침묵**과 **놓친 것**을 갈라라.
- p02 는 몇 줄로 답하나?

### 7. `go.mod` 판 다섯 (예측)

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

<!-- 같은 파일에서 go.mod 의 go 줄만 1.19 · 1.20 · 1.21 · 1.22 · 1.23 으로 바꿔 빌드·실행·go vet 한다. 마지막 줄에 vet 이 말한 판 수. -->

- 다섯 판 중 빌드가 실패하는 판이 있나?
- `vet` 이 말하는 판은 어느 것이고, 무엇을 말하나? `go 1.19`·`1.20` 에서 `vet` 이 침묵하는 이유는?

### 8. 비교할 수 없는 키 (경계)

- `context.WithValue(ctx, []string{"id"}, 1)` 은 컴파일되나? 실행하면?

### 9. 관례 둘 (왜)

- 문서가 `Context` 를 **구조체에 넣지 말고 첫 인자로** 받으라고 하는 것은 계약인가 관례인가? 이 판의 `vet` 이 그것을 검사하나?
- 「값은 요청 범위 데이터만」 — 선택 인자를 `ctx` 에 넣으면 무엇을 잃나?

### 10. `defer cancel()` (경계)

- 이미 끝난 `Context` 의 `cancel` 을 불러도 되는 이유를 3번의 한 줄로 말해 보라. `cancel` 을 **안** 부르면 문서는 무엇이 샌다고 하나?

### 11. 설계 문서와 (연결)

- `ops-patterns/deadline-propagation` 과 이 편은 어디서 갈리나? 3번 ③ 의 성질은 그쪽의 어느 설계를 받치나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

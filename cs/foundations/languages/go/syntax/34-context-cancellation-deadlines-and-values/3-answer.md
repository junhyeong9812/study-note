# go/syntax/34 — ★ `context`: 취소·데드라인·값 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★ **근거로 읽을 칸** — 노드별 `Done 받았나`·`Err` · `7 / 7`·`2 / 7` · 200판 참거짓 · `답한 탐침 5 / 11` · `vet 이 말한 판 2 / 5` · `Err`/`Cause` 문구.
> **근거로 읽지 않을 칸** — `Done` 의 **도착 순서**(그래서 블록에 안 실었다).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `root` → `7 / 7`(`b` 도 `canceled`) · `a` → `2 / 7` · `c` 는 그대로 전한다

**출력**

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

**왜 그런가**

- ★★★ **`root` 취소 — 전부 `true`, `Err` 전부 `context canceled`.** 문서 「**When a Context is canceled, all Contexts derived from it are also canceled.**」
  ★★ `b` 는 한 시간짜리 `WithTimeout` 인데 **`Canceled`** — 부모의 취소가 먼저 왔다.
- ★★★ **`a` 취소 — `a`·`a1` 만 `true`, 나머지 `Err=<nil>`, `2 / 7`.** **취소는 아래로만** — 부모(`root`)에도 형제(`b`·`c`)에도 안 간다.
- ★★ **`c`(`WithValue`)** — `cancel` 이 없는 노드인데 root 의 취소를 **그대로 보이고 `c1` 까지 전했다.** 값 노드는 취소를 **막지도 만들지도 않는다.**

### 2. 순서는 흔들린다 — 「다 받았나」가 근거다

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

- ★★★ **「도착 순서가 두 가지 이상 나왔나 : 예」 · 「모든 판이 일곱 노드를 다 담았나 : 예」.** 누가 먼저냐는 고루틴 스케줄링이다. 문서도 순서를 약속하지 않는다.
- ★★ 그래서 근거는 **노드마다의 참거짓**(1번)이다 — 그것은 나무 모양이 정한다.

### 3. `deadline exceeded`·`canceled`(둘 다 `Is` 참) · 같다, `deadline exceeded` · 안 바뀐다

**출력**

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

**왜 그런가**

- ★★★ **① `context deadline exceeded` / ② `context canceled`**, 각각 `errors.Is` 가 `true`. `Done` 전에는 `<nil>`.
- ★★★ **③ `자식 Deadline == 부모 Deadline: true`** — 한 시간을 줬어도 부모의 50ms 를 **못 넘는다.** 자식의 `Err` 도 **`deadline exceeded`**.
- ★★ **④ 첫 원인이 남는다** — 끝난 뒤 `cancel()` 은 `Err` 를 안 바꾼다. 그래서 **`defer cancel()`** 을 늘 붙여도 해가 없다.

### 4. `canceled`+`quota exhausted` · `false`/`true` · 자식은 `<nil>`·`nil`·없음·`trace-7`

**출력**

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

**왜 그런가**

- ★★★ **`Err` 는 `context canceled` 그대로, `Cause` 가 `quota exhausted`** — 자식도 같은 `Cause`. 원인 없이 취소한 것의 `Cause` 는 **`Err` 와 같다**(`context canceled`).
- ★★ **`[timeoutCause]`** — `Err` 는 `deadline exceeded`, `Cause` 는 `quota exhausted`.
- ★★★ **`AfterFunc`** — 취소 뒤 `f` 가 돌았고 그 뒤 `stop()` 은 **`false`**(이미 돌았다). **취소 전 `stop()` 은 `true`**, 그 뒤 취소해도 **`f` 가 안 돌았다.**
- ★★★ **`WithoutCancel`** — 부모 `canceled` · **자식 `<nil>` · `Done` 이 `nil` · `Deadline` 없음 · 값 `trace-7`.** 취소·데드라인은 끊고 **값만** 물려받았다.

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

- ★ 판 — `WithCancelCause`·`Cause` **1.20**, `AfterFunc`·`WithoutCancel`·`…Cause` **1.21**.

### 5. `vet exit=0`(침묵) · `"req-42" ok=true` · `"alice" ok=true`

**출력**

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

**왜 그런가**

- ★★★ **`authstr.User` 가 `"req-42"`** — 두 패키지가 **같은 문자열 `"id"`** 를 키로 썼다. 뒤에 넣은 `tracestr.WithRequest` 가 **가렸다.** 타입도 `string` 이라 **`ok=true`** — 에러 없이 **틀린 사용자로** 진행된다.
- ★★★ **비공개 타입 키(`type userKey struct{}`)** 는 다른 패키지가 **만들 수 없다** — `"alice"` 가 제대로 나왔다.
- ★★ 문서 — 「**should not be of type string or any other built-in type to avoid collisions between packages using context. Users of WithValue should define their own types for keys.**」
- ★★ **`vet` 은 침묵** — 이 판 `vet` 에는 이것을 보는 분석기가 없다.

### 6. `5 / 11` · 옳은 침묵 p05·p06·p07·p08·p11, 놓친 것 p03 · 두 줄

**출력**

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

**왜 그런가**

- ★★★ **답한 5** — p01·p09·p10(`_` 로 버리기 — `WithCancel`·`WithCancelCause`·`=` 대입의 `WithTimeout`) · p02(이른 `return`) · p04(`if false` 안에만).
- ★★★ **옳은 침묵 다섯** — p05 `defer cancel()` · p06 돌려준다 · p07 필드에 저장 · p08 다른 고루틴의 `defer` · p11 다른 함수에 넘긴다.
  **놓친 것 — p03 `_ = cancel`.** 한 번 「쓴」 것으로 쳐서 넘어갔다. 실제로는 **아무도 안 부른다.**
- ★★ **p02 는 두 줄** — 「not used on all paths」(18행)와 「this return statement may be reached」(20행).
- ★ **컴파일러는 11 개 전부 통과시킨다** — `lostcancel` 은 **`vet` 의 휴리스틱**이다.

### 7. 없다(다섯 판 전부 빌드·실행) · `go 1.21`·`1.22` 에서 `Clear requires go1.23` · 1.21 미만 모듈은 일부러 안 본다

**출력**

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

**왜 그런가**

- ★★★ **컴파일러는 `go` 줄로 표준 API 를 막지 않는다** — 표준 라이브러리는 **툴체인(1.27.1)의 것**이다.
- ★★★ **`vet 이 말한 판 2 / 5`** — `go 1.21`·`1.22` 에서 **`sync.(*Map).Clear requires go1.23 or later`**.
- ★★★ **`go 1.19`·`1.20` 의 침묵** — 분석기 소스 「**Don't report diagnostics for modules marked before go1.21**」. 그래서 **`context` 의 1.20·1.21 API 는 이 도구로 판 경계를 지킬 수 없다** — `api/` 표로 확인한다.

### 8. 컴파일된다 · `panic: key is not comparable`

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

- ★★ **`vet exit=0`, 빌드 통과, 실행 중 `WithValue` 가 패닉** — `recover` 가 `key is not comparable` 을 받았다. 문서 「**The provided key must be comparable**」의 모양이다.

### 9. 관례 — 이 판 `vet` 은 검사 안 한다 · 시그니처에서 사라진다

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

- ★★★ 「**Do not store Contexts inside a struct type; instead, pass a Context explicitly to each function that needs it … The Context should be the first parameter, typically named ctx**」 — **문서의 관례**다. 컴파일러도 이 판 `vet` 도 **검사하지 않는다** — 지키는 것은 사람이다.
- ★★ 「**Use context Values only for request-scoped data that transits processes and APIs, not for passing optional parameters to functions.**」 — 선택 인자를 `ctx` 에 넣으면 **함수 시그니처에서 사라지고**, 컴파일러가 **타입도 존재도** 확인해 주지 않는다(5번의 `ok=true` 가 그 대가).

### 10. 「④ 시간 초과 뒤 `cancel()` 한 `Err`: `context deadline exceeded`」 · 자식과 그 자식들이 부모가 취소될 때까지

- ★★★ 3번 ④ — **끝난 뒤의 `cancel()` 은 `Err` 를 안 바꾼다.** 그래서 **만든 바로 다음 줄에 `defer cancel()`** 이 기본형이다.
- ★★★ 문서(9번 블록 첫 문단) — 「**Failing to call the CancelFunc leaks the child and its children until the parent is canceled.**」

### 11. 그쪽은 「무엇을 어디까지 넘기나」의 설계 · 이 편은 API·관례 · ③ 은 데드라인 예산

- ★★★ [`../../../../../ops-patterns/deadline-propagation/`](../../../../../ops-patterns/deadline-propagation/) — 타임아웃 대 데드라인 · 전파 경로 · 취소가 닿지 않는 곳 · 감사 로그의 **설계**가 정본이다. 이 편은 **`context` 타입이 그 설계를 어떻게 싣나**(API·관례·함정)부터다.
- ★★ 3번 ③(**자식 데드라인은 부모를 못 넘는다**)은 그쪽 「3. 전파 경로」가 말하는 「**어느 계층도 자기 아래에 자기가 받은 것보다 큰 값을 넘길 수 없다**」 를 `context` 가 **자동으로** 지키는 모양이다. 4번의 `WithoutCancel` 은 그쪽 「5. 취소해도 남겨야 하는 것」의 자리다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 로 **★고칠 것 0** |
| ★★★ 나무 (`t34tree`·`t34order`) | `-race` 빌드 · 두 칸 + 200판 | 캡처마다 | **`7 / 7` · `2 / 7`** · 순서는 두 가지 이상 |
| ★★ `Err`·`Cause`·`AfterFunc`·`WithoutCancel` | 실행 | 캡처마다 | 위 블록 |
| ★★★ 키 충돌 (`t34key`·`t34nokey`) | 다중 패키지 모듈 · `vet` | 캡처마다 | `"req-42" ok=true` · `vet` 침묵 · `not comparable` |
| ★★★ `lostcancel` (`t34lost`) | 탐침 11, 줄 번호로 맞춤 | 캡처마다 | **`5 / 11`** · p03 놓침 |
| ★★ 판 경계 (`t34ver`·`t34stdver`·`t34api`) | `go.mod` 다섯 판 × 빌드·실행·`vet` | 캡처마다 | 전부 빌드 · **`2 / 5`** |

**구현·환경에 달린 항목**

| 항목 | 무엇에 달렸나 |
|---|---|
| `Done` 도착 순서 | **스케줄링 — 흔들린다**(가짓수로 접었다) |
| `lostcancel` 의 판정 범위 | **이 판 `vet`** — `_ = cancel` 을 놓치는 것이 의도인지는 **확인 못 했다** |
| `stdversion` 의 1.21 미만 침묵 | **이 판 분석기의 정책**(소스 인용) |
| 문자열 키 경고 | **이 판 `vet` 에는 없다** · 외부 린터는 **이 머신에 없다** |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다.

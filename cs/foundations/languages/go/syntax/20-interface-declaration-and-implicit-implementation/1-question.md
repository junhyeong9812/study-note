# go/syntax/20 — 인터페이스 선언과 암묵 구현 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> ★★★ **모든 문제에서 「인터페이스 값의 두 칸이 지금 무엇인가」를 먼저 적어라.**
> 타입 칸과 값 칸을 갈라 적으면 이 주제의 함정이 전부 풀린다.
> ★★ **「도구가 이것을 알려 주나」를 매번 물어라** — 이 주제의 답이 자주 「아니오」다.
> ★ **답마다 「그 값을 누가 보장하나」를 같이 적어라** — 규칙은 명세이고 **바이트 수는 구현**이다.
> ★ 자바·Rust 를 안다면 **「구현을 적는 자리」** 라는 직관을 먼저 의심하라.
> 소스는 전부 `go build -trimpath -o prog . && ./prog` 로 던졌다. 모듈 이름은 `ex` 다.
> 컴파일 에러를 전부 보려고 몇 블록은 `-gcflags=-e` 를 붙였다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 누가 이 인터페이스를 만족하는가 (예측)

```go
// t20a.go
package main

import (
	"bytes"
	"fmt"
	"os"
	"strings"
)

// 표준 라이브러리는 이 인터페이스를 모른다. 그래도 만족한다.
type Sizer interface {
	Len() int
}

// 내가 만든 타입도 io.Writer 라고 한 마디도 안 적는다
type Upper struct{ out *strings.Builder }

func (u Upper) Write(p []byte) (int, error) {
	u.out.WriteString(strings.ToUpper(string(p)))
	return len(p), nil
}

func report(s Sizer) string { return fmt.Sprintf("%T len=%d", s, s.Len()) }

func main() {
	fmt.Println("── 표준 타입들이 내 인터페이스를 만족한다 ──")
	fmt.Println(" ", report(bytes.NewBufferString("abc")))
	fmt.Println(" ", report(strings.NewReader("abcd")))
	var sb strings.Builder
	sb.WriteString("abcde")
	fmt.Println(" ", report(&sb))

	fmt.Println("── 내 타입이 io.Writer 를 만족한다 — implements 를 안 적었다 ──")
	var b strings.Builder
	fmt.Fprintf(Upper{out: &b}, "hello %s", "go")
	fmt.Println("  Fprintf 가 쓴 것 :", b.String())

	fmt.Println("── os.Stdout 도 같은 인터페이스다 ──")
	fmt.Fprintln(os.Stdout, "  Fprintln(os.Stdout, …)")

	fmt.Println("── 인터페이스는 쓰는 쪽에 둔다 : report 는 Sizer 만 알고 구현을 모른다 ──")
	fmt.Printf("  report 의 타입 : %T\n", report)
}
```

- 여덟 줄은 각각 무엇으로 찍히는가?
- `Sizer` 는 내가 방금 만든 타입이다. 표준 라이브러리가 어떻게 그것을 만족하는가?
- `Upper` 는 `io.Writer` 라고 어디에 적었는가?
- 마지막 줄이 말하는 「인터페이스를 쓰는 쪽에 둔다」가 패키지 의존에 무엇을 바꾸는가?

### 2. ★★★ 네 줄의 단언 (예측)

```go
// t20b.go
package main

import "fmt"

type Handler interface {
	Handle(n int) error
	Name() string
}

type Good struct{}

func (g *Good) Handle(n int) error { return nil }
func (g *Good) Name() string       { return "good" }

type Typo struct{}

func (t *Typo) Handle(n int) error { return nil }
func (t *Typo) Nmae() string       { return "typo" } // 오타

type ValueRecv struct{}

func (v ValueRecv) Handle(n int) error { return nil }
func (v ValueRecv) Name() string       { return "value" }

type WrongSig struct{}

func (w *WrongSig) Handle(n int64) error { return nil } // int 가 아니라 int64
func (w *WrongSig) Name() string         { return "wrong" }

// ★ 이 줄들이 이 자리의 관용구다 — 「이 타입이 이 인터페이스를 만족한다」를 컴파일러에게 시킨다
var (
	_ Handler = (*Good)(nil)
	_ Handler = (*Typo)(nil)
	_ Handler = ValueRecv{}
	_ Handler = (*WrongSig)(nil)
)

func main() { fmt.Println("여기까지 오면 단언이 전부 통과한 것이다") }
```

- 컴파일러는 몇 줄을 거부하는가 — 각각의 메시지 **전문**은?
- 거부되지 **않은** 단언은 어느 것인가, 왜인가?
- `have`/`want` 두 줄은 무엇을 말해 주는가?
- `var _ Handler = (*Good)(nil)` 이라는 꼴이 무엇을 하는 것인가 — 값을 하나 만드는가?

### 3. ★★★ `nil` 포인터를 돌려주는 함수 (예측)

```go
// t20d.go
package main

import (
	"fmt"
	"reflect"
)

type MyErr struct{ Msg string }

func (e *MyErr) Error() string { return "MyErr:" + e.Msg }

// ★ 함정 — 구체 포인터 타입으로 선언해 두고 그대로 돌려준다
func trap() error {
	var p *MyErr // nil 이다
	return p     // error 인터페이스에 담기면서 (타입=*MyErr, 값=nil) 이 된다
}

// 고친 판 — error 로 선언하거나, nil 을 직접 돌려준다
func fixed() error {
	var p *MyErr
	if p == nil {
		return nil
	}
	return p
}

func describe(name string, err error) {
	fmt.Printf("  %-8s err == nil : %-5v  %%T=%-10T  %%v=%v\n", name, err == nil, err, err)
}

func main() {
	fmt.Println("── 인터페이스 값은 두 칸이다 : (타입, 값) ──")
	var pure error // 두 칸이 다 비었다
	describe("pure", pure)
	describe("trap()", trap())
	describe("fixed()", fixed())

	fmt.Println("── 두 칸을 따로 본다 ──")
	e := trap()
	rv := reflect.ValueOf(e)
	fmt.Printf("  reflect.TypeOf(e)  = %v\n", reflect.TypeOf(e))
	fmt.Printf("  rv.Kind()          = %v\n", rv.Kind())
	fmt.Printf("  rv.IsNil()         = %v   ← 값 칸은 nil 이다\n", rv.IsNil())
	fmt.Printf("  e == nil           = %v   ← 인터페이스 자체는 nil 이 아니다\n", e == nil)
	fmt.Printf("  reflect.ValueOf(error(nil)).IsValid() = %v   ← 진짜 nil 인터페이스\n",
		reflect.ValueOf(error(nil)).IsValid())

	fmt.Println("── 그래서 이런 코드가 조용히 틀린다 ──")
	if err := trap(); err != nil {
		fmt.Println("  err != nil 이 참이 되었다 →", err)
	}
	if err := fixed(); err != nil {
		fmt.Println("  여기는 안 온다")
	} else {
		fmt.Println("  fixed() 는 제대로 nil 이다")
	}

	fmt.Println("── 담긴 값이 nil 이어도 메서드는 불린다 (리시버가 nil 일 뿐이다) ──")
	fmt.Printf("  trap().Error() = %q\n", func() (s string) {
		defer func() {
			if r := recover(); r != nil {
				s = fmt.Sprintf("panic: %v", r)
			}
		}()
		return trap().Error()
	}())
}
```

- 세 `describe` 줄은 각각 무엇으로 찍히는가?
- `trap()` 이 그렇게 되는 이유를 **두 칸**으로 설명하라.
- `rv.IsNil()` 과 `e == nil` 이 다른 답을 주는 이유는 무엇인가?
- 마지막 줄의 `trap().Error()` 는 무엇을 찍는가 — 그리고 그것이 「`nil` 인터페이스 호출」과 어떻게 다른가?

### 4. 인터페이스 값은 몇 바이트인가 (예측)

```go
// t20e.go
package main

import (
	"fmt"
	"unsafe"
)

type Speaker interface{ Speak() string }
type Empty interface{}

type Big struct{ Buf [1024]byte }

func (b Big) Speak() string { return "big" }

func main() {
	fmt.Println("── 인터페이스 값은 두 칸이다 : 크기가 포인터 둘이다 (구현·플랫폼) ──")
	var s Speaker
	var e Empty
	var a any
	var p *Big
	fmt.Println("  unsafe.Sizeof(Speaker) =", unsafe.Sizeof(s))
	fmt.Println("  unsafe.Sizeof(Empty)   =", unsafe.Sizeof(e))
	fmt.Println("  unsafe.Sizeof(any)     =", unsafe.Sizeof(a))
	fmt.Println("  unsafe.Sizeof(*Big)    =", unsafe.Sizeof(p), " ← 포인터 한 칸")
	fmt.Println("  unsafe.Sizeof(Big{})   =", unsafe.Sizeof(Big{}), " ← 값 그 자체")

	fmt.Println("── 1024바이트짜리를 인터페이스에 담아도 인터페이스 값은 16이다 ──")
	s = Big{}
	fmt.Println("  담은 뒤 unsafe.Sizeof(s) =", unsafe.Sizeof(s), " · %T =", fmt.Sprintf("%T", s))
	fmt.Println("  ★ 담을 때 값이 어디에 놓이는지는 명세에 없는 낱말이다 — 구현이 정한다")

	fmt.Println("── 두 칸이 비어야 nil 이다 ──")
	var n1 Speaker
	fmt.Println("  var n1 Speaker      -> n1 == nil :", n1 == nil)
	var n2 Speaker = (*Big)(nil)
	fmt.Printf("  Speaker = (*Big)(nil) -> n2 == nil : %v  (%%T=%T)\n", n2 == nil, n2)
}
```

- 아홉 줄은 각각 무엇으로 찍히는가?
- 그 수가 그 값인 이유는 무엇인가 — 그리고 **누가 보장하는가**?
- 1024바이트짜리를 담았는데 인터페이스 값이 그 크기인 것은 무엇을 뜻하는가?
- 마지막 두 줄은 3번과 어떤 관계인가?

### 5. 단언 두 꼴 (예측)

```go
// t20f.go
package main

import (
	"fmt"
	"io"
	"os"
	"strings"
)

type Closer interface{ Close() error }

func main() {
	var r io.Reader = strings.NewReader("abc")

	fmt.Println("── comma-ok 형 : 물어보기 ──")
	if sr, ok := r.(*strings.Reader); ok {
		fmt.Println("  *strings.Reader 다  Len =", sr.Len())
	}
	if _, ok := r.(Closer); !ok {
		fmt.Println("  Closer 는 아니다 — ok 가 false 다")
	}
	if s, ok := any(42).(string); !ok {
		fmt.Printf("  any(42).(string) -> ok=false, 제로값 %q\n", s)
	}

	fmt.Println("── 인터페이스에서 인터페이스로도 단언한다 ──")
	var rc io.Reader = io.NopCloser(strings.NewReader("abc"))
	_, ok := rc.(io.Closer)
	fmt.Println("  NopCloser 는 io.Closer 인가 :", ok)

	fmt.Println("── 빈 인터페이스 any 는 아무거나 담는다 ──")
	for _, v := range []any{1, "ㄱ", 2.5, []int{1}, nil, struct{}{}} {
		fmt.Printf("  %-10s %T\n", fmt.Sprint(v), v)
	}

	fmt.Fprintln(os.Stderr, "-- 이제 단항 단언을 틀리게 던진다 --")
	_ = r.(*os.File)
	fmt.Fprintln(os.Stderr, "-- 여기는 안 온다 --")
}
```

- 빌드는 성공하는가? 앞의 열두 줄은 각각 무엇으로 찍히는가?
- `any(42).(string)` 의 `s` 는 무엇인가 — 왜 패닉하지 않는가?
- `nil` 을 `any` 에 담았을 때 `%T` 는 무엇인가?
- 마지막에 무엇이 나오는가 — **전문과 종료 코드**는?

### 6. 메서드를 셋 더 요구하면 (예측)

```go
// t20g.go
package main

import (
	"bytes"
	"fmt"
	"io"
	"os"
	"reflect"
	"strings"
)

// 한 메서드 인터페이스 — 직접 만든 것
type Reader1 interface {
	Read(p []byte) (n int, err error)
}

// 네 메서드 인터페이스 — 같은 일을 하는데 요구가 많다
type Reader4 interface {
	Read(p []byte) (n int, err error)
	Close() error
	Seek(offset int64, whence int) (int64, error)
	WriteTo(w io.Writer) (int64, error)
}

// 내가 만든 최소 구현 — Read 하나뿐이다
type Ones struct{ left int }

func (o *Ones) Read(p []byte) (int, error) {
	if o.left <= 0 {
		return 0, io.EOF
	}
	n := min(len(p), o.left)
	for i := range n {
		p[i] = '1'
	}
	o.left -= n
	return n, nil
}

func main() {
	fmt.Println("── 후보 타입들이 두 인터페이스를 각각 얼마나 만족하나 ──")
	cands := []reflect.Type{
		reflect.TypeOf((*strings.Reader)(nil)),
		reflect.TypeOf((*bytes.Buffer)(nil)),
		reflect.TypeOf((*bytes.Reader)(nil)),
		reflect.TypeOf((*os.File)(nil)),
		reflect.TypeOf((*Ones)(nil)),
	}
	r1 := reflect.TypeOf((*Reader1)(nil)).Elem()
	r4 := reflect.TypeOf((*Reader4)(nil)).Elem()
	n1, n4 := 0, 0
	for _, t := range cands {
		a, b := t.Implements(r1), t.Implements(r4)
		if a {
			n1++
		}
		if b {
			n4++
		}
		fmt.Printf("  %-18v Reader1=%-6v Reader4=%v\n", t, a, b)
	}
	fmt.Printf("  합계 : 한 메서드 %d/%d · 네 메서드 %d/%d\n", n1, len(cands), n4, len(cands))

	fmt.Println("── 작은 인터페이스는 조합된다 ──")
	src := io.MultiReader(strings.NewReader("ab"), &Ones{left: 3}, bytes.NewReader([]byte("cd")))
	var tee bytes.Buffer
	lim := io.LimitReader(io.TeeReader(src, &tee), 6)
	got, err := io.ReadAll(lim)
	fmt.Printf("  MultiReader→TeeReader→LimitReader : %q err=%v\n", got, err)
	fmt.Printf("  곁가지(tee)로 흘러간 것            : %q\n", tee.String())

	fmt.Println("── io.Reader 의 선언은 한 줄이다 ──")
	fmt.Println("  type Reader interface { Read(p []byte) (n int, err error) }")
}
```

- 다섯 후보의 두 판정은 각각 무엇인가 — 합계 두 수는?
- `*os.File` 만 다른 이유는 무엇인가?
- 세 겹 배관이 낸 두 문자열은 각각 무엇인가?
- 이 실험이 「작은 인터페이스가 좋다」를 **어떻게** 보이는가?

### 7. 오타가 난 타입을 아무도 안 본다 (경계)

```go
// t20c.go
package main

import "fmt"

type Handler interface {
	Handle(n int) error
	Name() string
}

type Good struct{}

func (g *Good) Handle(n int) error { return nil }
func (g *Good) Name() string       { return "good" }

type Typo struct{}

func (t *Typo) Handle(n int) error { return nil }
func (t *Typo) Nmae() string       { return "typo" } // 오타 — 아무도 모른다

var _ Handler = (*Good)(nil) // 단언을 적은 쪽만 검사된다

func main() {
	var h Handler = &Good{}
	fmt.Println("Good 은 만족한다 :", h.Name())
	fmt.Println("Typo 는 만족하지 않는다 — 그런데 빌드도 vet 도 한 마디 안 한다")
}
```

- 이 프로그램은 빌드되는가 — `go vet ./...` 은 무엇을 말하는가?
- `Typo` 는 `Handler` 를 만족하는가 — 누가 그것을 알려 주는가?
- 같은 디렉토리에서 `go doc -all .` 을 던지면 만족 관계가 나오는가?
- 이 상황을 막으려면 소스에 무엇을 한 줄 더 적어야 하는가?

### 8. 도구가 못 보는 것 (왜)

- 「이 인터페이스를 무엇이 구현하나」를 답해 주는 표준 도구가 있는가?
- 그 목록이 **원리상** 만들어지지 않는 이유는 무엇인가?
- `grep` 으로 구현체를 찾을 수 있는가 — 자바라면?
- 그 부재를 코드에서 메우는 방법 두 가지를 적어라.

### 9. 인터페이스를 어디에 두고 얼마나 크게 (경계)

- 인터페이스를 선언하는 자리는 구현하는 쪽인가 쓰는 쪽인가 — 왜 고를 수 있는가?
- 인터페이스를 **미리** 만들어 둘 필요가 있는가?
- 메서드를 늘리면 무엇이 줄어드는가 — 6번의 두 수로 답하라.
- `error` 를 돌려주는 함수에서 지켜야 할 한 줄 규칙은?
- 두 종류의 `nil` 을 가르는 도구는 무엇인가?

### 10. 다른 언어와 나란히 (연결)

- Rust 에서 「이 타입이 이 트레이트를 구현한다」를 적는 곳은 어디인가 — Go 는?
- 그래서 틀림이 드러나는 **자리**가 어떻게 다른가?
- 자바의 인터페이스는 기본 구현을 줄 수 있는가 — 코틀린은? Go 는?
- 자바 IDE 가 「구현체 목록」을 보여 줄 수 있는 이유는 무엇인가 — Go 에서는?
- 인터페이스를 쓰는 쪽에 두는 것이 Rust·자바에서 왜 어려운가?

### 11. 다른 주제와 잇기 (연결)

- 메서드 집합 규칙의 정본은 몇 번 주제인가?
- 타입 스위치의 정본은 몇 번 주제인가?
- `nil` 인터페이스 함정의 정본은 몇 번 주제인가?
- `io.Reader`/`Writer` 조합의 정본은 몇 번 주제인가?
- 인터페이스 필드가 든 구조체의 `==` 가 런타임에 터지는 실측은 몇 번 주제에 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

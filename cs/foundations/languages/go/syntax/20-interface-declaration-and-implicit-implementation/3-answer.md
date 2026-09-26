# go/syntax/20 — 인터페이스 선언과 암묵 구현 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> 블록은 전부 `===== 소스: … =====` 로 소스를 먼저 싣는다 — **그대로 다시 던질 수 있게** 하기 위해서다.
> ★ **근거로 읽을 칸** — `== nil` 의 참거짓, `%T`·`%v` 가 찍는 것, `reflect` 의 `IsNil`/`IsValid`/`Implements`,
> 컴파일 에러 문장과 `파일:줄:칸`, 패닉 메시지 본문, 종료 코드, `go vet` 의 **출력 줄 수**.
> **근거로 읽지 않을 칸** — `unsafe.Sizeof` 의 **수**(플랫폼), 패닉 첫 줄의 `pc=0x…`,
> 스택의 `goroutine N` 과 `+0x…`, `go doc` 의 **차례와 꼴**(도구).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 표준 라이브러리가 내 인터페이스를 모르면서 만족한다

**출력**

```text
===== 소스: t20a.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
── 표준 타입들이 내 인터페이스를 만족한다 ──
  *bytes.Buffer len=3
  *strings.Reader len=4
  *strings.Builder len=5
── 내 타입이 io.Writer 를 만족한다 — implements 를 안 적었다 ──
  Fprintf 가 쓴 것 : HELLO GO
── os.Stdout 도 같은 인터페이스다 ──
  Fprintln(os.Stdout, …)
── 인터페이스는 쓰는 쪽에 둔다 : report 는 Sizer 만 알고 구현을 모른다 ──
  report 의 타입 : func(main.Sizer) string
(exit 0)
```

**왜 그런가**

- `*bytes.Buffer`(3) · `*strings.Reader`(4) · `*strings.Builder`(5) 가 전부 `Sizer` 로 받아졌다.
- ★★★ **그 세 타입은 `Sizer` 라는 이름을 모른다.** `Len() int` 이 있을 뿐이다. 명세:

  > An interface type defines a **type set**. A variable of interface type can store a value of any type
  > that is in the type set of the interface. **Such a type is said to implement the interface.**

  > **More than one type may implement an interface.** … regardless of what other methods
  > S1 and S2 may have or share.

- `Upper` 는 **어디에도 `io.Writer` 라고 안 적었다.** `Write([]byte) (int, error)` 하나뿐인데
  `fmt.Fprintf` 가 받아 `HELLO GO` 를 만들었다.
- ★★ **패키지 의존 방향이 달라진다** — `report(s Sizer)` 는 `Sizer` 만 알고 구현을 모르고,
  **구현하는 쪽은 `Sizer` 를 import 할 필요가 없다.**
  자바·Rust 는 `implements`·`impl … for` 를 적어야 하므로 **구현하는 쪽이 인터페이스를 알아야** 한다.
  ★ 그래서 Go 에서는 **인터페이스를 쓰는 쪽 패키지에 선언**하는 것이 관용이 된다.
- 층 — 전부 **명세 보장**이다.

### 2. ★★★ 넷 중 둘이 막힌다 — 실패 모양이 서로 다르다

**출력**

```text
===== 소스: t20b.go =====
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
===== 명령: go build -trimpath -gcflags=-e -o prog . =====
# ex
./t20b.go:33:14: cannot use (*Typo)(nil) (value of type *Typo) as Handler value in variable declaration: *Typo does not implement Handler (missing method Name)
./t20b.go:35:14: cannot use (*WrongSig)(nil) (value of type *WrongSig) as Handler value in variable declaration: *WrongSig does not implement Handler (wrong type for method Handle)
		have Handle(int64) error
		want Handle(int) error
(exit 1)
```

**왜 그런가**

- **두 줄이 거부된다.**

| 타입 | 무엇이 틀렸나 | 메시지 |
|---|---|---|
| `*Typo` | 이름 오타(`Nmae`) | `*Typo does not implement Handler (missing method Name)` |
| `*WrongSig` | 시그니처(`int64`) | `*WrongSig does not implement Handler (wrong type for method Handle)` + `have Handle(int64) error` / `want Handle(int) error` |

- 거부되지 **않은** 것은 `(*Good)(nil)` 과 `ValueRecv{}` 다.
  `ValueRecv` 는 **값 리시버**라 `ValueRecv{}` 로도 만족한다
  ([19번 주제](../19-method-sets-value-vs-pointer-receiver/)의 격자 왼쪽 세로줄).
  ★ 그래서 **단언을 값으로 적을지 포인터로 적을지**가 무엇을 검사하는지를 정한다 —
  `(*T)(nil)` 은 `*T` 의 집합을, `T{}` 는 `T` 의 집합을 묻는다.
- ★★ **`have`/`want` 두 줄이 이 관용구의 값어치**다. 「구현이 없다」가 아니라
  **무엇을 어떻게 고쳐야 하는지**를 그대로 말해 준다.
- **`var _ Handler = (*Good)(nil)` 이 하는 일** — 값을 만들지 않는다.
  `(*Good)(nil)` 은 **`nil` 을 `*Good` 으로 형변환만** 한 것이고, `_` 에 대입하므로 **아무것도 남지 않는다.**
  남는 것은 **컴파일러가 한 검사** 하나뿐이다. 통과하면 흔적이 없고, 안 통과하면 그 줄에서 멈춘다.
- 층 — 만족 규칙은 **명세 보장**, 에러 **문구**는 툴체인 판의 것이다.

### 3. ★★★ 두 칸 중 타입 칸만 차 있으면 `nil` 이 아니다

**출력**

```text
===== 소스: t20d.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
── 인터페이스 값은 두 칸이다 : (타입, 값) ──
  pure     err == nil : true   %T=<nil>       %v=<nil>
  trap()   err == nil : false  %T=*main.MyErr  %v=<nil>
  fixed()  err == nil : true   %T=<nil>       %v=<nil>
── 두 칸을 따로 본다 ──
  reflect.TypeOf(e)  = *main.MyErr
  rv.Kind()          = ptr
  rv.IsNil()         = true   ← 값 칸은 nil 이다
  e == nil           = false   ← 인터페이스 자체는 nil 이 아니다
  reflect.ValueOf(error(nil)).IsValid() = false   ← 진짜 nil 인터페이스
── 그래서 이런 코드가 조용히 틀린다 ──
  err != nil 이 참이 되었다 → <nil>
  fixed() 는 제대로 nil 이다
── 담긴 값이 nil 이어도 메서드는 불린다 (리시버가 nil 일 뿐이다) ──
  trap().Error() = "panic: runtime error: invalid memory address or nil pointer dereference"
(exit 0)
```

**왜 그런가**

| | `err == nil` | `%T` | `%v` |
|---|---|---|---|
| `var pure error` | **`true`** | `<nil>` | `<nil>` |
| `trap()` | ★ **`false`** | **`*main.MyErr`** | `<nil>` |
| `fixed()` | **`true`** | `<nil>` | `<nil>` |

- ★★★ **두 칸으로 설명하면 이렇다.**

```text
   var pure error            trap()                     fixed()
   [타입: nil][값: nil]      [타입: *MyErr][값: nil]     [타입: nil][값: nil]
        == nil : true              == nil : false            == nil : true
```

  `trap()` 의 `return p` 는 `p` 가 `nil` 이어도 **`*MyErr` 이라는 타입표를 함께** 담는다.
  명세의 비교 규칙이 그것을 그대로 말한다.

  > Two interface values are equal if they have **identical dynamic types and equal dynamic values**
  > **or if both have value nil.**

  ★ **「둘 다 `nil`」은 두 칸이 다 비었다는 뜻**이다. 타입 칸이 차면 그 조건이 깨진다.
- **`rv.IsNil()` 은 `true` 인데 `e == nil` 은 `false`** — 둘이 **다른 칸을 보기** 때문이다.
  `IsNil` 은 **값 칸**(동적 값)을, `== nil` 은 **인터페이스 자체**(두 칸)를 본다.
  ★ 그리고 **진짜 `nil` 인터페이스**는 `reflect.ValueOf(error(nil)).IsValid()` 가 **`false`** 다 —
  `reflect` 가 아예 값을 못 만든다. **두 상태가 도구에서도 갈린다.**
- ★★ `%v` 가 **`<nil>`** 로 찍히는 것이 사고를 키운다 —
  로그에는 `<nil>` 이 찍히는데 `err != nil` 은 참이라 「에러가 없는데 에러 처리로 들어간다」가 된다.
  실제로 그 분기가 실행돼 `err != nil 이 참이 되었다 → <nil>` 이 찍혔다.
- 마지막 줄 — **`trap().Error()` 는 패닉한다**
  (`panic: runtime error: invalid memory address or nil pointer dereference`, `recover` 로 받았다).
  ★★ **그런데 호출 자체는 성공했다** — 리시버가 `nil` 일 뿐이고 그 안에서 `e.Msg` 를 읽다 죽었다.
  **「`nil` 인터페이스의 메서드 호출」은 다른 자리**다 — 그쪽은 **호출 자체가** 패닉이다
  ([18번 주제](../18-embedding-and-field-method-promotion/) (5)절).
  ★ 그래서 `nil` 리시버로도 잘 도는 메서드라면 **아무 일도 안 난다** — 더 조용해진다.
- **고치는 법은 `fixed()`** 다 — `error` 로 선언하고 성공이면 **`nil` 을 직접** 돌려준다.
- 층 — 비교 규칙은 **명세 보장**, `%v` 가 `<nil>` 로 찍는 것은 **`fmt` 의 계약**, 패닉 문구는 **런타임**이다.

### 4. 16바이트 — 두 칸짜리라는 뜻이고, 그 수는 구현이다

**출력**

```text
===== 소스: t20e.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
── 인터페이스 값은 두 칸이다 : 크기가 포인터 둘이다 (구현·플랫폼) ──
  unsafe.Sizeof(Speaker) = 16
  unsafe.Sizeof(Empty)   = 16
  unsafe.Sizeof(any)     = 16
  unsafe.Sizeof(*Big)    = 8  ← 포인터 한 칸
  unsafe.Sizeof(Big{})   = 1024  ← 값 그 자체
── 1024바이트짜리를 인터페이스에 담아도 인터페이스 값은 16이다 ──
  담은 뒤 unsafe.Sizeof(s) = 16  · %T = main.Big
  ★ 담을 때 값이 어디에 놓이는지는 명세에 없는 낱말이다 — 구현이 정한다
── 두 칸이 비어야 nil 이다 ──
  var n1 Speaker      -> n1 == nil : true
  Speaker = (*Big)(nil) -> n2 == nil : false  (%T=*main.Big)
(exit 0)
```

**왜 그런가**

- `Speaker`·`Empty`·`any` 가 전부 **16**, `*Big` 이 **8**, `Big{}` 이 **1024** 다.
- **16 = 포인터 둘**이고 그것이 (타입, 값) 두 칸이다.
- ★★★ **그런데 명세에 그 수가 없다.** 명세는 두 칸을 **비교 규칙의 낱말**
  (dynamic type / dynamic value)로만 말한다. **바이트 수는 구현·플랫폼**이다.
  **amd64 가 아니면 달라질 수 있다.**
- **1024바이트짜리를 담아도 인터페이스 값이 16** 이라는 것은,
  **그 1024바이트가 인터페이스 값 안에 없다**는 뜻이다. 어디에 있는지는
  ★ **명세에 없는 낱말**이고 이 문서는 **재지 않았다**(목록의 **52번 주제**).
- 마지막 두 줄이 3번을 한 번 더 말한다 —
  `var n1 Speaker` 는 `n1 == nil` 이 **`true`** 이고,
  `Speaker = (*Big)(nil)` 은 **`false`** 에 `%T` 가 `*main.Big` 이다.
  ★ **같은 `nil` 인데 담는 순간 달라진다.**
- 층 — 두 칸이라는 **사실**은 명세, **수**는 구현·플랫폼이다.

### 5. comma-ok 는 묻고 단항은 단정한다

**출력**

```text
===== 소스: t20f.go =====
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
===== 명령: go build -trimpath -o prog . =====
(exit 0)
```

```text
===== 명령: ./prog 2>&1 =====
── comma-ok 형 : 물어보기 ──
  *strings.Reader 다  Len = 3
  Closer 는 아니다 — ok 가 false 다
  any(42).(string) -> ok=false, 제로값 ""
── 인터페이스에서 인터페이스로도 단언한다 ──
  NopCloser 는 io.Closer 인가 : true
── 빈 인터페이스 any 는 아무거나 담는다 ──
  1          int
  ㄱ          string
  2.5        float64
  [1]        []int
  <nil>      <nil>
  {}         struct {}
-- 이제 단항 단언을 틀리게 던진다 --
panic: interface conversion: io.Reader is *strings.Reader, not *os.File

goroutine 1 [running]:
main.main()
	ex/t20f.go:37 +0x596
(exit 2)
```

**왜 그런가**

- **빌드는 성공**한다(exit 0).
- comma-ok 세 줄 — `*strings.Reader` 로 꺼내 `Len()` 이 3,
  `Closer` 는 `ok=false`, `any(42).(string)` 은 `ok=false` 에 **제로값 `""`** 다. 명세:

  > A type assertion used in an assignment statement … yields an additional untyped boolean value.
  > The value of ok is true if the assertion holds. Otherwise it is **false and the value of v is
  > the zero value for type T. No run-time panic occurs in this case.**

  ★ **패닉하지 않는 이유가 그 마지막 문장**이다. comma-ok 형은 **묻는 꼴**이라 실패가 값으로 돌아온다.
- **인터페이스에서 인터페이스로도** 단언한다 — `io.NopCloser(...)` 가 `io.Closer` 인가 → `true`.

  > If T is an interface type, x.(T) asserts that the **dynamic type of x implements the interface T**.

- **`any` 에 담은 여섯 가지** — `int`·`string`·`float64`·`[]int`·`<nil>`·`struct {}`.
  ★ **`nil` 의 `%T` 가 `<nil>`** 인 것이 3번과 이어진다 — **아무것도 안 담긴 인터페이스**다.
  `any` 는 **1.18부터**의 이름이다("any is an alias for the empty interface … [Go 1.18]").
- ★★ 마지막은 **`panic: interface conversion: io.Reader is *strings.Reader, not *os.File`**,
  **종료 코드 2** 다.
  ★ 메시지가 **어떤 인터페이스였고 무엇이 들어 있었고 무엇을 바랐는지** 셋을 다 말해 준다 —
  진단에 그대로 쓸 수 있다.
- 층 — 단언 규칙은 **명세 보장**, 패닉 문구는 **런타임**이다.

### 6. 5/5 대 1/5 — 「작은 것이 좋다」는 산술이다

**출력**

```text
===== 소스: t20g.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
── 후보 타입들이 두 인터페이스를 각각 얼마나 만족하나 ──
  *strings.Reader    Reader1=true   Reader4=false
  *bytes.Buffer      Reader1=true   Reader4=false
  *bytes.Reader      Reader1=true   Reader4=false
  *os.File           Reader1=true   Reader4=true
  *main.Ones         Reader1=true   Reader4=false
  합계 : 한 메서드 5/5 · 네 메서드 1/5
── 작은 인터페이스는 조합된다 ──
  MultiReader→TeeReader→LimitReader : "ab111c" err=<nil>
  곁가지(tee)로 흘러간 것            : "ab111c"
── io.Reader 의 선언은 한 줄이다 ──
  type Reader interface { Read(p []byte) (n int, err error) }
(exit 0)
```

**왜 그런가**

| 후보 | `Reader1`(메서드 1개) | `Reader4`(메서드 4개) |
|---|---|---|
| `*strings.Reader` | `true` | `false` |
| `*bytes.Buffer` | `true` | `false` |
| `*bytes.Reader` | `true` | `false` |
| `*os.File` | `true` | **`true`** |
| `*main.Ones` | `true` | `false` |
| **합계** | ★ **5/5** | ★ **1/5** |

- ★★★ **메서드를 셋 더 요구했더니 만족하는 타입이 5에서 1로 줄었다.**
  「작은 인터페이스가 좋다」가 **취향이 아니라 산술**이라는 것을 이 두 수가 말한다.
- **`*os.File` 만 다른 이유** — 파일은 `Read`·`Close`·`Seek`·`WriteTo` 를 전부 갖고 있다.
  나머지는 하나씩 빠진다(예컨대 `*strings.Reader` 에는 `Close` 가 없다).
  ★ **넷을 다 가진 타입은 드물다** — 그것이 1/5 의 뜻이다.
- **세 겹 배관** — `io.MultiReader`(세 소스를 잇고) → `io.TeeReader`(곁가지로 흘리고)
  → `io.LimitReader`(6바이트에서 끊는다)가 **`"ab111c"`** 를 냈고, 곁가지에도 **`"ab111c"`** 가 흘렀다.
  `Ones` 는 **`Read` 하나만 쓴** 내 타입인데 그 배관에 그대로 들어간다.
- ★★ **조합이 되는 이유가 「작아서」다.** 세 함수가 전부 **`io.Reader` 를 받아 `io.Reader` 를 낸다** —
  메서드가 넷이었다면 그 배관은 애초에 못 만들어진다.
  ★ 그래서 이 실험은 「작으면 **만족하는 타입이 늘고**, 늘면 **조합이 가능해진다**」를 두 단계로 보인 것이다.
- 층 — `Implements` 의 판정은 **명세 보장**, 배관의 결과는 **`io` 패키지의 계약**이다.

### 7. 오타가 난 타입을 아무도 안 본다

**출력**

```text
===== 소스: t20c.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
Good 은 만족한다 : good
Typo 는 만족하지 않는다 — 그런데 빌드도 vet 도 한 마디 안 한다
(exit 0)
```

```text
===== 명령: go vet ./... =====
(exit 0)
```

```text
===== 명령: go doc -all . =====


TYPES

type Good struct{}

func (g *Good) Handle(n int) error

func (g *Good) Name() string

type Handler interface {
	Handle(n int) error
	Name() string
}

type Typo struct{}

func (t *Typo) Handle(n int) error

func (t *Typo) Nmae() string
(exit 0)
```

**왜 그런가**

- **빌드가 성공(exit 0)** 하고 `go vet ./...` 은 **출력 0줄에 exit 0** 이다.
- `Typo` 는 `Name()` 대신 `Nmae()` 를 갖고 있으니 **`Handler` 를 만족하지 않는다.**
  그런데 **아무도 알려 주지 않는다** — 아무도 `Typo` 를 `Handler` 로 쓰려 하지 않았기 때문이다.
- ★★★ `go doc -all .` 에도 **없다.** `Good`·`Handler`·`Typo` 가 **이름 오름차순으로 나란히** 있고
  메서드가 딸려 나올 뿐, **누가 누구를 만족하는지 한 줄도 없다.**
  ★ `go doc` 은 **선언을 보여 주는 도구**이지 관계를 계산하는 도구가 아니다.
- **막는 법은 한 줄이다** — **`var _ Handler = (*Typo)(nil)`** 을 적는다.
  그러면 2번의 `missing method Name` 이 **그 자리에서** 난다.
- ★★ 그리고 이 블록이 보여 주는 것은 **「단언은 적은 것만 검사한다」** 는 대가다.
  `Good` 에는 적었고 `Typo` 에는 안 적었더니 **한쪽만 지켜졌다.**
- 층 — 「아무도 안 본다」는 **언어 설계의 결과**, `vet`·`doc` 의 범위는 **도구(구현)** 다.

### 8. 도구가 못 보는 것

**출력** — 없음(왜 문항). 근거 블록은 7번과 아래 둘이다.

```text
===== 명령: go doc io.Writer =====
package io // import "io"

type Writer interface {
	Write(p []byte) (n int, err error)
}
    Writer is the interface that wraps the basic Write method.

    Write writes len(p) bytes from p to the underlying data stream. It returns
    the number of bytes written from p (0 <= n <= len(p)) and any error
    encountered that caused the write to stop early. Write must return a non-nil
    error if it returns n < len(p). Write must not modify the slice data,
    even temporarily.

    Implementations must not retain p.

var Discard Writer = discard{}
func MultiWriter(writers ...Writer) Writer
(exit 0)
```

```text
===== 명령: echo "구현 선언 낱말이 소스에 몇 줄 있나 : $(grep -c -E "implements|extends|impl " t20g.go)" =====
구현 선언 낱말이 소스에 몇 줄 있나 : 0
(exit 0)
```

**왜 그런가**

- **「이 인터페이스를 무엇이 구현하나」를 답해 주는 표준 도구가 없다.**
  `go doc io.Writer` 는 선언과 문서와 `Discard`·`MultiWriter` 를 보여 주지만
  **구현체 목록은 한 줄도 없다.**
- ★★★ **원리상 못 만든다** — 암묵 구현이라 그 관계가 **어디에도 저장되지 않는다.**
  누가 `io.Writer` 를 만족하는지 알려면 **세상의 모든 패키지의 모든 타입**을 봐야 한다.
  자바·Rust 는 `implements`·`impl … for` 가 **소스에 적혀 있으므로** 인덱싱하면 된다.
- **`grep` 으로도 못 찾는다** — 소스에 `implements`·`extends` 같은 낱말이 **0줄**이다.
  ★ 자바라면 `grep implements` 로 후보를 좁힐 수 있는데 **Go 에는 찾을 문자열이 없다.**
- ★★ **부재를 메우는 두 방법** —
  ① **`var _ Iface = (*T)(nil)`** 을 구현하는 쪽에 적어 **관계를 소스에 남긴다**(그리고 검사된다).
  ② **인터페이스를 작게 유지해** 만족 여부를 사람이 **눈으로 셀 수 있게** 한다(6번).
  ★ 두 번째가 설계 취향만이 아니라 **도구 부재에 대한 대응**이기도 하다.
- 층 — 「없다」는 **언어 설계의 결과**이고, 「지금 판의 `go doc` 이 안 낸다」는 **도구(구현)** 다.
  ★ 에디터·언어 서버가 인덱싱해서 흉내 내 주기도 하는데, 그것은 **도구의 기능**이지 언어의 것이 아니다 —
  이 문서는 에디터를 근거로 쓰지 않았다.

### 9. 어디에 두고 얼마나 크게

**출력** — 없음(경계 문항).

**왜 그런가**

| 물음 | 답 | 근거 |
|---|---|---|
| 어디에 선언하나 | **쓰는 쪽** | 1번 — 구현하는 쪽이 import 할 것이 없다 |
| 미리 만들어 둬야 하나 | ★ **아니다** | 암묵 구현이라 **나중에 만들어도 기존 타입이 만족한다** |
| 메서드를 늘리면 | **만족하는 타입이 준다** — **5/5 → 1/5** | 6번 |
| `error` 반환의 규칙 | **`error` 로 선언하고 `nil` 을 직접 돌려준다** | 3번 |
| 두 `nil` 을 가르는 도구 | **`reflect`** — `IsNil()` 과 `IsValid()` | 3번 |

- ★★ **「미리 안 만들어도 된다」가 암묵 구현의 가장 큰 실무 이득**이다.
  자바라면 나중에 인터페이스를 뽑을 때 **기존 클래스들을 전부 고쳐 `implements` 를 달아야** 한다.
  Go 는 **인터페이스만 새로 선언하면 끝**이다 — 기존 타입은 한 글자도 안 바뀐다.
- ★ `error` 규칙을 한 줄로 적으면 — **구체 포인터 타입의 변수를 그대로 `return` 하지 마라.**
  3번의 `trap()` 이 그 한 줄을 어긴 코드다.

### 10. 다른 언어와 나란히

**출력** — 없음(연결 문항).

**왜 그런가**

| 물음 | **Go** | **Rust** | **Java** | **Kotlin** |
|---|---|---|---|---|
| 구현을 적는 곳 | ★ **없다** | `impl Trait for T` | `implements I` | `: I` |
| 틀림이 드러나는 자리 | ★ **쓰는 자리** | **`impl` 블록**(선언 자리) | **선언 자리** | 선언 자리 |
| 인터페이스에 몸통 | ★ **없다** | 기본 메서드 있음 | `default` 메서드(8+) | 있음(상태는 못 준다) |
| 구현체 목록을 도구가 | ★ **원리상 못 만든다** | 인덱싱하면 된다 | 인덱싱하면 된다 | 인덱싱하면 된다 |
| 쓰는 쪽에 인터페이스를 | ★ **가능** | 어렵다(고아 규칙) | 어렵다(기존 클래스를 고쳐야) | 어렵다 |

- ★★★ **결정적인 갈림은 두 번째 줄이다.**
  Rust 는 `impl Trait for T` 를 적으므로 **빠진 메서드가 선언 자리에서** 드러난다
  (Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **25번**).
  Go 는 적는 곳이 없으니 **대입하는 자리에 가서야** 드러난다 —
  그래서 `var _ I = (*T)(nil)` 이 **선언 자리를 인공으로 만드는** 일을 한다.
- 자바의 인터페이스는 `default` 메서드로 **몸통을 줄 수 있고**
  ([`../../../java/syntax/11-interfaces-default-methods/`](../../../java/syntax/11-interfaces-default-methods/)),
  코틀린도 그렇다(단 **상태는 못 준다** —
  [`../../../kotlin/syntax/20-interfaces-default-impl-and-super/`](../../../kotlin/syntax/20-interfaces-default-impl-and-super/)).
  **Go 인터페이스에는 몸통이 아예 없다** — 이름과 시그니처뿐이다.
  ★ 그래서 Go 에서 「공통 구현」은 **인터페이스가 아니라 임베딩**이 맡는다(18번 주제).
- **IDE 가 구현체 목록을 보여 줄 수 있는 이유**는 소스에 `implements` 가 **적혀 있기 때문**이다.
  Go 에서는 **그 문자열이 없다**(8번의 grep 0줄). 에디터가 보여 준다면 **타입 검사를 전부 돌려** 흉내 낸 것이다.
- **쓰는 쪽에 인터페이스를 두기 어려운 이유** — Rust 는 **고아 규칙**이 남의 타입에 남의 트레이트를
  구현하지 못하게 막고(Rust 갈래 [목록의 **26번**](../26-defer-evaluation-lifo-named-results-and-loops/)), 자바는 **기존 클래스를 고쳐야** 한다.
  Go 는 둘 다 필요 없다.

### 11. 다른 주제와 잇기

**출력** — 없음(연결 문항).

**왜 그런가**

- **메서드 집합 규칙** — [19번 주제](../19-method-sets-value-vs-pointer-receiver/).
  **이 주제의 직접 선행**이고, 2번의 `(*T)(nil)` 대 `T{}` 가 거기서 나온다.
- **타입 스위치** — [15번 주제](../15-switch-type-switch-fallthrough-labels-and-goto/).
  5번은 **comma-ok 한 꼴**까지만 본다.
- **`nil` 인터페이스 함정** — [목록의 **21번 주제**](../21-nil-interface-vs-interface-holding-nil-pointer/). 3번은 **한 번 던져 보는** 데까지다.
- **`io.Reader`/`Writer` 조합** — 목록의 **43번 주제**. 6번은 **「작을수록 좋다」를 수로 보이는** 데까지다.
- **인터페이스 필드가 든 구조체의 `==` 가 런타임에 터지는 실측** —
  [17번 주제](../17-struct-literals-comparability-field-tags-and-sorting/) (4)절
  (`comparing uncomparable type []int`).
- 덤 — **인터페이스 임베딩**은 [18번 주제](../18-embedding-and-field-method-promotion/) (5)절,
  **타입 단언·`comparable`** 은 [목록의 **22번 주제**](../22-type-assertion-any-and-comparable/),
  **오류 값 설계**는 [목록의 **23번**](../23-error-interface-and-errors-as-values/)·**24번 주제**,
  **제네릭으로 `any` 를 대신하는 자리**는 목록의 **37번 주제**다.

---

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행 1회** | 재실행 결과가 `normalize-shaky.py` 로 **동일** |
| 판 확인 | `go version` | 1 | `go1.27.1 linux/amd64` |
| 암묵 구현 (`t20a`) | `go build && ./prog` | 1 | 표준 타입 셋이 `Sizer` 를 만족 · `Upper` 가 `io.Writer` |
| ★★★ 만족 단언 (`t20b`) | `go build -trimpath -gcflags=-e` | 1 | 에러 **2건** · `missing method` · `wrong type` + `have`/`want` · exit 1 |
| ★★★ 두 종류의 `nil` (`t20d`) | `go build && ./prog` | 1 | `trap()` 의 `err == nil` 이 **`false`** · `%T`=`*main.MyErr` · `%v`=`<nil>` |
| 인터페이스 값의 크기 (`t20e`) | 〃 | 1 | 16 · 16 · 16 · 8 · 1024 · 담은 뒤에도 16 |
| 타입 단언 (`t20f`) | `go build` · `./prog 2>&1` | 2 | comma-ok 셋 · `interface conversion: … not *os.File` · **exit 2** |
| ★★ 작은 인터페이스 (`t20g`) | `go build && ./prog` | 1 | **5/5 대 1/5** · 배관이 `"ab111c"` |
| ★★★ 아무도 안 본다 (`t20c`) | `go build && ./prog` · `go vet ./...` · `go doc -all .` | 3 | 빌드 exit 0 · **vet 출력 0줄 exit 0** · doc 에 만족 목록 **없음** |
| 도구에 물어보기 | `go doc io.Writer` · `grep` 세기 | 2 | 구현체 목록 **없음** · 구현 선언 낱말 **0줄** |
| 형태 (`t20form`) | `go build && ./prog` | 1 | 다섯 줄 |

**구현·환경에 달린 항목**(버전이 오르거나 타깃이 바뀌면 **다시 찍어야 하는** 것)

| 항목 | 무엇에 달렸나 |
|---|---|
| `unsafe.Sizeof` 의 **16과 8** | **플랫폼(amd64).** 명세에 그 수가 없다 |
| **담긴 값이 어디에 놓이나**(힙/스택) | **구현(gc)**. 명세에 그 낱말이 없다(목록의 **52번 주제**) |
| 패닉·컴파일 에러의 **문구 자체** | **툴체인 판(go1.27.1)** |
| 패닉 첫 줄의 `pc=0x…` · 스택의 `goroutine N` · `+0x…` | **빌드 산출물·런타임** |
| `go doc` 의 **차례와 꼴** | **도구(구현)** |
| `go vet` 이 **만족 여부를 안 보는 것** | **도구(구현)**. 판이 오르면 달라질 수 있다 |
| `%v` 가 `nil` 포인터를 **`<nil>`** 로 찍는 것 | **`fmt` 의 계약** |
| `io.MultiReader`·`TeeReader`·`LimitReader` 의 동작 | **`io` 패키지의 계약** |
| 인터페이스 호출·단언의 **실제 비용** | ★ **안 쟀다**(목록의 **50번 주제**) |
| 인터페이스에 담을 때 **할당이 생기나** | ★ **안 쟀다** |
| 타입 요소(`~int \| ~string`)가 든 인터페이스 | ★ **안 던졌다**(목록의 **37번 주제**) |
| 시그니처가 다른 메서드를 겹쳐 임베딩한 에러 | ★ **안 던졌다**(명세 인용만) |
| 인터페이스에서 꺼낸 값이 addressable 이 아닌 에러 | ★ **안 던졌다** |
| 에디터·언어 서버가 구현체를 보여 주는 것 | ★ **근거로 안 썼다** — 도구의 기능이지 언어의 것이 아니다 |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다.

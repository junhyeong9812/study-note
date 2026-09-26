# go/syntax/22 — 타입 단언·`any`·`comparable` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> 블록은 전부 `===== 소스: … =====` 로 소스를 먼저 싣는다 — **그대로 다시 던질 수 있게** 하기 위해서다.
> 판 경계를 보이는 두 블록은 **`===== 소스: go.mod =====` 까지** 싣는다 — 그 한 줄이 결과를 바꾸기 때문이다.
> ★ **근거로 읽을 칸** — 패닉·컴파일 에러의 **문장과 `파일:줄:칸`**, 종료 코드,
> `ok` 의 참거짓, 타입 스위치가 고른 가지, `go vet` 의 진단 문장, `-lang` 게이트 문구.
> **근거로 읽지 않을 칸** — 스택 프레임의 주소(이 주제의 블록에서는 한 건도 안 흔들렸다).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 실패 모양 여섯 가지와 그 전문 — 문구가 두 갈래다

**출력**

```text
===== 소스: t22a.go =====
package main

import (
	"fmt"
	"io"
	"strings"
)

type Shape interface{ Area() float64 }
type Square struct{ S float64 }
type Circle struct{ R float64 }

func (s Square) Area() float64 { return s.S * s.S }
func (c Circle) Area() float64 { return 3 * c.R * c.R }

// 단항 단언을 던지고 패닉 문구만 받아 온다.
func caught(name string, f func()) {
	defer func() {
		if r := recover(); r != nil {
			fmt.Printf("  %-34s panic -> %v\n", name, r)
			return
		}
		fmt.Printf("  %-34s 패닉 없음\n", name)
	}()
	f()
}

func main() {
	fmt.Println("-- comma-ok 형 : 물어본다. 실패해도 패닉이 없다 --")
	var a any = 42
	if s, ok := a.(string); !ok {
		fmt.Printf("  a.(string) -> ok=false, v=%q (제로값)\n", s)
	}
	if n, ok := a.(int); ok {
		fmt.Printf("  a.(int)    -> ok=true,  v=%d\n", n)
	}
	var sh Shape = Square{S: 2}
	if _, ok := sh.(Circle); !ok {
		fmt.Println("  sh.(Circle) -> ok=false")
	}

	fmt.Println("-- 단항 형 : 틀리면 패닉이고, 문구가 무엇이 들어 있었는지까지 말한다 --")
	caught("any(42).(string)", func() { _ = a.(string) })
	caught("Square 를 Circle 로", func() { _ = sh.(Circle) })
	var empty any
	caught("nil any 를 int 로", func() { _ = empty.(int) })
	var nilShape Shape
	caught("nil Shape 를 Square 로", func() { _ = nilShape.(Square) })
	caught("any(42).(fmt.Stringer)", func() { _ = a.(fmt.Stringer) })
	var r io.Reader = strings.NewReader("x")
	caught("io.Reader 를 io.Closer 로", func() { _ = r.(io.Closer) })

	fmt.Println("-- comma-ok 는 같은 자리에서 전부 false 를 준다 --")
	for _, tc := range []struct {
		name string
		ok   bool
	}{
		{"a.(string)", func() bool { _, ok := a.(string); return ok }()},
		{"sh.(Circle)", func() bool { _, ok := sh.(Circle); return ok }()},
		{"empty.(int)", func() bool { _, ok := empty.(int); return ok }()},
		{"a.(fmt.Stringer)", func() bool { _, ok := a.(fmt.Stringer); return ok }()},
		{"r.(io.Closer)", func() bool { _, ok := r.(io.Closer); return ok }()},
	} {
		fmt.Printf("  %-20s ok=%v\n", tc.name, tc.ok)
	}
}
===== 명령: go build -trimpath -o prog . && ./prog =====
-- comma-ok 형 : 물어본다. 실패해도 패닉이 없다 --
  a.(string) -> ok=false, v="" (제로값)
  a.(int)    -> ok=true,  v=42
  sh.(Circle) -> ok=false
-- 단항 형 : 틀리면 패닉이고, 문구가 무엇이 들어 있었는지까지 말한다 --
  any(42).(string)                   panic -> interface conversion: interface {} is int, not string
  Square 를 Circle 로                  panic -> interface conversion: main.Shape is main.Square, not main.Circle
  nil any 를 int 로                    panic -> interface conversion: interface {} is nil, not int
  nil Shape 를 Square 로               panic -> interface conversion: main.Shape is nil, not main.Square
  any(42).(fmt.Stringer)             panic -> interface conversion: int is not fmt.Stringer: missing method String
  io.Reader 를 io.Closer 로            panic -> interface conversion: *strings.Reader is not io.Closer: missing method Close
-- comma-ok 는 같은 자리에서 전부 false 를 준다 --
  a.(string)           ok=false
  sh.(Circle)          ok=false
  empty.(int)          ok=false
  a.(fmt.Stringer)     ok=false
  r.(io.Closer)        ok=false
(exit 0)
```

**왜 그런가**

- **첫 덩어리** — comma-ok 는 **패닉하지 않는다.** 명세가 그렇게 적는다.

```text
===== 명령: sed -n "4216,4228p" "$(go env GOROOT)/doc/go_spec.html" | sed -e "s/<[^>]*>//g" =====
var v, ok = x.(T)
var v, ok interface{} = x.(T) // dynamic types of v and ok are T and bool



yields an additional untyped boolean value. The value of ok is true
if the assertion holds. Otherwise it is false and the value of v is
the zero value for type T.
No run-time panic occurs in this case.



Calls
(exit 0)
```

  `a.(string)` 이 `ok=false` 에 제로값 `""`, `a.(int)` 이 `ok=true` 에 42다.
- ★★★ **둘째 덩어리가 답이다.**

| 왜 틀렸나 | 문구 |
|---|---|
| 담긴 구체 타입이 다르다 | `interface conversion: interface {} is int, not string` |
| 이름 있는 인터페이스에 담겨 있었다 | `interface conversion: main.Shape is main.Square, not main.Circle` |
| 인터페이스가 비어 있었다 | `interface conversion: interface {} is nil, not int` |
| 이름 있는 인터페이스가 비어 있었다 | `interface conversion: main.Shape is nil, not main.Square` |
| 메서드가 모자라다(구체 → 인터페이스) | `interface conversion: int is not fmt.Stringer: missing method String` |
| 메서드가 모자라다(인터페이스 → 인터페이스) | `interface conversion: *strings.Reader is not io.Closer: missing method Close` |

- ★★★ **문구가 두 갈래인 이유는 묻는 것이 다르기 때문**이다. 명세가 그 둘을 나눠 적는다.

```text
===== 명령: sed -n "4170,4190p" "$(go env GOROOT)/doc/go_spec.html" | sed -e "s/<[^>]*>//g" =====



asserts that x is not nil
and that the value stored in x is of type T.
The notation x.(T) is called a type assertion.


More precisely, if T is not an interface type, x.(T) asserts
that the dynamic type of x is identical
to the type T.
In this case, T must implement the (interface) type of x;
otherwise the type assertion is invalid since it is not possible for x
to store a value of type T.
If T is an interface type, x.(T) asserts that the dynamic type
of x implements the interface T.


If the type assertion holds, the value of the expression is the value
stored in x and its type is T. If the type assertion is false,
a run-time panic occurs.
(exit 0)
```

  구체 타입이면 「**동적 타입이 `T` 와 같나**」라 「is B, not C」로 답하고,
  인터페이스면 「**동적 타입이 `T` 를 구현하나**」라 「is not I: missing method M」으로 답한다.
- ★ **셋째 덩어리** — 같은 여섯 자리가 comma-ok 로는 전부 `ok=false` 다. 아무 일도 안 난다.
  ★★ 고르는 것은 「**틀릴 수 있나**」가 아니라 「**틀렸을 때 무엇을 하고 싶나**」다.


**출력**

```text
===== 소스: t22b.go =====
package main

import (
	"fmt"
	"os"
)

type Shape interface{ Area() float64 }
type Square struct{ S float64 }

func (s Square) Area() float64 { return s.S * s.S }

func main() {
	var sh Shape = Square{S: 2}
	fmt.Println("면적 :", sh.Area())
	fmt.Fprintln(os.Stderr, "-- 이제 단항 단언을 틀리게 던진다 --")
	_ = sh.(interface{ Perimeter() float64 })
	fmt.Fprintln(os.Stderr, "-- 여기는 안 온다 --")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
면적 : 4
-- 이제 단항 단언을 틀리게 던진다 --
panic: interface conversion: main.Square is not interface { Perimeter() float64 }: missing method Perimeter

goroutine 1 [running]:
main.main()
	ex/t22b.go:17 +0xf9
(exit 2)
```

**왜 그런가**

- `면적 : 4` 가 찍히고, 단항 단언이 틀려 **패닉에 종료 코드 2** 다.
- ★ 익명 인터페이스에 단언했으므로 문구에 **선언 그대로** 들어간다 —
  `not interface { Perimeter() float64 }`.
- 구분 마커를 **표준 오류로 찍었다** — 표준 출력과 섞으면 파이프로 받을 때 순서가 갈릴 수 있다.

### 2. `Both` 는 `case error` 로 간다

**출력**

```text
===== 소스: t22c.go =====
package main

import (
	"errors"
	"fmt"
	"io"
	"strings"
)

type Shape interface{ Area() float64 }
type Square struct{ S float64 }

func (s Square) Area() float64 { return s.S * s.S }

type Named struct{ N string }

func (n Named) String() string { return "Named(" + n.N + ")" }

// 가지를 전수로 늘어놓고 무엇이 골라지는지 본다.
func classify(x any) string {
	switch v := x.(type) {
	case nil: // 두 칸이 다 빈 것만 여기로 온다
		return fmt.Sprintf("case nil            v=%v (%T)", v, v)
	case int, int64: // 여러 타입을 한 가지에 — v 는 any 로 남는다
		return fmt.Sprintf("case int, int64     v=%v (%T)", v, v)
	case string:
		return fmt.Sprintf("case string         v=%q (%T)", v, v)
	case error: // 인터페이스 가지
		return fmt.Sprintf("case error          v=%v (%T)", v, v)
	case fmt.Stringer: // 인터페이스 가지
		return fmt.Sprintf("case fmt.Stringer   v=%v (%T)", v, v)
	case Shape:
		return fmt.Sprintf("case Shape          면적=%v (%T)", v.Area(), v)
	case io.Reader:
		return fmt.Sprintf("case io.Reader      (%T)", v)
	default:
		return fmt.Sprintf("default             v=%v (%T)", v, v)
	}
}

type Both struct{ N string }

func (b Both) String() string { return "Both:" + b.N }
func (b Both) Error() string  { return "Both-err:" + b.N }

func main() {
	fmt.Println("-- 가지가 순서대로 시험된다 : 먼저 맞는 가지가 이긴다 --")
	for _, x := range []any{
		nil,
		42,
		int64(7),
		"hi",
		errors.New("boom"),
		Named{N: "a"},
		Square{S: 3},
		strings.NewReader("z"),
		3.14,
	} {
		fmt.Printf("  %-22s -> %s\n", fmt.Sprintf("%T", x), classify(x))
	}

	fmt.Println("-- 한 값이 두 인터페이스 가지를 다 만족하면 먼저 적은 가지가 이긴다 --")
	fmt.Println("  Both{} ->", classify(Both{N: "x"}))

	fmt.Println("-- nil 을 담은 인터페이스는 case nil 로 안 간다 (21번 주제) --")
	var e error = (*mySlice)(nil)
	fmt.Println("  (*mySlice)(nil) ->", classify(e))
}

type mySlice []int

func (m *mySlice) Error() string { return "mySlice" }
===== 명령: go build -trimpath -o prog . && ./prog =====
-- 가지가 순서대로 시험된다 : 먼저 맞는 가지가 이긴다 --
  <nil>                  -> case nil            v=<nil> (<nil>)
  int                    -> case int, int64     v=42 (int)
  int64                  -> case int, int64     v=7 (int64)
  string                 -> case string         v="hi" (string)
  *errors.errorString    -> case error          v=boom (*errors.errorString)
  main.Named             -> case fmt.Stringer   v=Named(a) (main.Named)
  main.Square            -> case Shape          면적=9 (main.Square)
  *strings.Reader        -> case io.Reader      (*strings.Reader)
  float64                -> default             v=3.14 (float64)
-- 한 값이 두 인터페이스 가지를 다 만족하면 먼저 적은 가지가 이긴다 --
  Both{} -> case error          v=Both-err:x (main.Both)
-- nil 을 담은 인터페이스는 case nil 로 안 간다 (21번 주제) --
  (*mySlice)(nil) -> case error          v=mySlice (*main.mySlice)
(exit 0)
```

**왜 그런가**

- ★★★ **`Both` 가 `case error` 로 갔다.** `Error()` 와 `String()` 을 둘 다 가져
  `case error` 와 `case fmt.Stringer` 를 **둘 다 만족**하는데 **먼저 적은 가지**가 이긴다.
  ★ `case fmt.Stringer` 를 앞에 적었으면 그쪽이었다 — **가지 순서가 의미를 바꾼다.**
- ★★ **구체 타입 가지끼리는 이 문제가 없다** — 중복 타입이 컴파일 에러라 겹칠 수가 없다
  ([15번 주제](../15-switch-type-switch-fallthrough-labels-and-goto/)).
  **인터페이스 가지만 겹친다.**
- ★★★ **`(*mySlice)(nil)` 은 `case nil` 로 안 간다.** `case error` 로 간다 —
  타입 칸이 차 있기 때문이다([21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/)).
- `case int, int64` 처럼 여러 타입을 적으면 **`v` 의 정적 타입은 `any`** 로 남는다.
  출력의 `%T` 가 `int`·`int64` 인 것은 **동적 타입**이다.
- `float64` 는 아무 가지에도 안 맞아 `default` 로 갔다.

### 3. `any` 와 `interface{}` 는 같은 타입이다

**출력**

```text
===== 소스: t22d.go =====
package main

import (
	"fmt"
	"reflect"
)

// any 가 interface{} 의 "다른 이름"이면 이 둘은 같은 타입이어야 한다.
type A = any         // 별칭 선언
type B = interface{} // 별칭 선언

type T struct{}

func (T) M(x any) {} // 아래 줄과 같은 메서드인가?

func main() {
	fmt.Println("-- reflect 가 부르는 이름 --")
	fmt.Println("  reflect.TypeOf((*any)(nil)).Elem()        =",
		reflect.TypeOf((*any)(nil)).Elem())
	fmt.Println("  reflect.TypeOf((*interface{})(nil)).Elem() =",
		reflect.TypeOf((*interface{})(nil)).Elem())
	fmt.Println("  두 타입이 같은가 :",
		reflect.TypeOf((*any)(nil)).Elem() == reflect.TypeOf((*interface{})(nil)).Elem())

	fmt.Println("-- 서로 대입된다 (변환이 아니라 같은 타입이다) --")
	var x any = 1
	var y interface{} = x
	var z A = y
	var w B = z
	fmt.Printf("  any -> interface{} -> A -> B : %v (%T)\n", w, w)

	fmt.Println("-- 함수 시그니처도 같은 타입으로 읽힌다 --")
	var f func(any)
	var g func(interface{})
	f = func(any) {}
	g = f // 대입이 된다
	fmt.Printf("  func(any) 를 func(interface{}) 에 대입 : %T\n", g)

	fmt.Println("-- 에러·패닉 문구에서는 늘 interface {} 로 나온다 --")
	fmt.Printf("  %%T of any(nil) 아닌 any(1) : %T\n", any(1))
	fmt.Printf("  reflect 의 Kind             : %v\n", reflect.TypeOf((*any)(nil)).Elem().Kind())
	fmt.Printf("  메서드 수                   : %d\n", reflect.TypeOf((*any)(nil)).Elem().NumMethod())
}
===== 명령: go build -trimpath -o prog . && ./prog =====
-- reflect 가 부르는 이름 --
  reflect.TypeOf((*any)(nil)).Elem()        = interface {}
  reflect.TypeOf((*interface{})(nil)).Elem() = interface {}
  두 타입이 같은가 : true
-- 서로 대입된다 (변환이 아니라 같은 타입이다) --
  any -> interface{} -> A -> B : 1 (int)
-- 함수 시그니처도 같은 타입으로 읽힌다 --
  func(any) 를 func(interface{}) 에 대입 : func(interface {})
-- 에러·패닉 문구에서는 늘 interface {} 로 나온다 --
  %T of any(nil) 아닌 any(1) : int
  reflect 의 Kind             : interface
  메서드 수                   : 0
(exit 0)
```

**왜 그런가**

- `reflect` 가 둘 다 **`interface {}`** 라고 답하고 **`==` 가 `true`** 다.
- **서로 대입된다** — `any` → `interface{}` → `A` → `B` 가 전부 통과한다.
  ★ **변환이 아니라 대입**이다. 다른 타입이었다면 변환 문법이 필요했다.
- ★ **`func(any)` 를 `func(interface{})` 에 대입**할 수 있고 `%T` 는 `func(interface {})` 로 찍는다.
  ★★ **도구는 `any` 라는 이름을 안 쓴다** — 패닉 문구도 `interface {}` 로 나온다((1)번).
- 메서드 수가 **0** 이라 모든 타입이 만족한다.


**출력**

```text
===== 소스: t22dx.go =====
package main

type T struct{}

// 같은 이름의 메서드를 any 와 interface{} 로 하나씩 선언한다.
// 두 타입이 다르면 오버로드가 아니라 그냥 중복 선언이고,
// 같은 타입이면 컴파일러가 그렇게 말해 준다.
func (T) M(x any)         {}
func (T) M(x interface{}) {}

func main() {}
===== 명령: go build -trimpath -gcflags=-e -o prog . =====
# ex
./t22dx.go:9:10: method T.M already declared at ./t22dx.go:8:10
(exit 1)
```

**왜 그런가**

- ★★★ **`./t22dx.go:9:10: method T.M already declared at ./t22dx.go:8:10`**, 종료 코드 1.
- ★★ **이것이 「별칭」이라는 말의 증명이다.** Go 에는 오버로드가 없지만,
  두 타입이 **달랐다면** 컴파일러는 「같은 이름의 메서드가 둘」이라는 것과 별개로
  **타입이 다르다는 사실을 알고 있었을 것**이다. 여기서는 **완전히 같은 선언**으로 읽었다.
- ★ 문서를 읽어 옮기는 대신 **컴파일러가 자기 입으로 말하게 한 자리**다.

### 4. 동적 타입이 같고 비교 불가일 때만 터진다

**출력**

```text
===== 소스: t22e.go =====
package main

import (
	"fmt"
	"os"
)

type Box struct{ V any } // 인터페이스 필드가 든 구조체

func caught(name string, f func() bool) {
	defer func() {
		if r := recover(); r != nil {
			fmt.Printf("  %-36s panic -> %v\n", name, r)
		}
	}()
	fmt.Printf("  %-36s = %v\n", name, f())
}

func main() {
	fmt.Println("-- 동적 타입이 다르면 비교가 그냥 false 다 (패닉 없음) --")
	var a any = []int{1}
	var b any = 1
	caught("any([]int) == any(int)", func() bool { return a == b })

	fmt.Println("-- 동적 타입이 같고 그 타입이 비교 불가면 런타임 패닉이다 --")
	var c any = []int{1}
	caught("any([]int) == any([]int)", func() bool { return a == c })
	var m1 any = map[string]int{}
	var m2 any = map[string]int{}
	caught("any(map) == any(map)", func() bool { return m1 == m2 })
	var f1 any = func() {}
	var f2 any = func() {}
	caught("any(func) == any(func)", func() bool { return f1 == f2 })

	fmt.Println("-- nil 과의 비교는 특례라 패닉하지 않는다 --")
	caught("any([]int) == nil", func() bool { return a == nil })
	var nilSlice any = []int(nil)
	caught("any([]int(nil)) == nil", func() bool { return nilSlice == nil })

	fmt.Println("-- 인터페이스 필드가 든 구조체도 같은 규칙을 탄다 (17번 주제) --")
	caught("Box{[]int} == Box{[]int}", func() bool { return Box{V: []int{1}} == Box{V: []int{1}} })
	caught("Box{1} == Box{1}", func() bool { return Box{V: 1} == Box{V: 1} })

	fmt.Println("-- 맵 키로 쓰면 문구가 다르다 --")
	caught("map[any]bool 에 []int 를 키로", func() bool {
		mm := map[any]bool{}
		mm[[]int{1}] = true
		return len(mm) == 1
	})

	fmt.Fprintln(os.Stderr, "-- 이제 받지 않고 그대로 던진다 --")
	var x any = []int{1}
	var y any = []int{2}
	fmt.Fprintln(os.Stderr, x == y)
	fmt.Fprintln(os.Stderr, "-- 여기는 안 온다 --")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
-- 동적 타입이 다르면 비교가 그냥 false 다 (패닉 없음) --
  any([]int) == any(int)               = false
-- 동적 타입이 같고 그 타입이 비교 불가면 런타임 패닉이다 --
  any([]int) == any([]int)             panic -> runtime error: comparing uncomparable type []int
  any(map) == any(map)                 panic -> runtime error: comparing uncomparable type map[string]int
  any(func) == any(func)               panic -> runtime error: comparing uncomparable type func()
-- nil 과의 비교는 특례라 패닉하지 않는다 --
  any([]int) == nil                    = false
  any([]int(nil)) == nil               = false
-- 인터페이스 필드가 든 구조체도 같은 규칙을 탄다 (17번 주제) --
  Box{[]int} == Box{[]int}             panic -> runtime error: comparing uncomparable type []int
  Box{1} == Box{1}                     = true
-- 맵 키로 쓰면 문구가 다르다 --
  map[any]bool 에 []int 를 키로            panic -> runtime error: hash of unhashable type []int
-- 이제 받지 않고 그대로 던진다 --
panic: runtime error: comparing uncomparable type []int

goroutine 1 [running]:
main.main()
	ex/t22e.go:54 +0x5af
(exit 2)
```

**왜 그런가**

- ★★★ **`any([]int) == any(int)` 은 `false` 다** — 동적 타입이 다르면 **비교조차 안 한다.**
  명세가 「**identical dynamic types**」일 때만 패닉이라 적는다.

```text
===== 명령: sed -n "5239,5256p" "$(go env GOROOT)/doc/go_spec.html" | sed -e "s/<[^>]*>//g" =====


A comparison of two interface values with identical dynamic types
causes a run-time panic if that type
is not comparable.  This behavior applies not only to direct interface
value comparisons but also when comparing arrays of interface values
or structs with interface-valued fields.



Slice, map, and function types are not comparable.
However, as a special case, a slice, map, or function value may
be compared to the predeclared identifier nil.
Comparison of pointer, channel, and interface values to nil
is also allowed and follows from the general rules above.
(exit 0)
```

- **동적 타입이 같고 비교 불가**면 터진다 — 슬라이스·맵·함수 셋 다
  `runtime error: comparing uncomparable type …` 이다.
- ★ **`nil` 과의 비교는 특례**라 안 터진다(같은 명세 문단의 둘째 덩어리).
  `any([]int) == nil` 이 `false` 이고 `any([]int(nil)) == nil` 도 **`false`** 다
  — 타입 칸이 차 있기 때문이다([21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/)).
- ★★ **`Box{[]int} == Box{[]int}` 도 터진다** — 명세가
  「structs with interface-valued fields」까지 적어 둔다
  ([17번 주제](../17-struct-literals-comparability-field-tags-and-sorting/) (4)절이 그쪽 정본).
  `Box{1} == Box{1}` 은 `true` 다.
- ★★ **맵 키로 쓰면 문구가 다르다** — **`hash of unhashable type []int`**.
  **같은 성질인데 연산이 달라 다른 문장**이 나온다.
- 마지막 — 받지 않고 던지면 **`panic: runtime error: comparing uncomparable type []int`**, 종료 코드 **2**.

### 5. 일곱 건이 컴파일에서 멈추고, `go.mod` 한 줄이 판 경계를 말한다

**출력**

```text
===== 소스: t22f.go =====
package main

// 타입 파라미터에 comparable 을 걸면 컴파일러가 대입 시점에 막는다.
func eq[T comparable](a, b T) bool { return a == b }

type Pair struct{ A, B int }     // 비교 가능
type WithSlice struct{ S []int } // 필드가 비교 불가
type WithIface struct{ V any }   // 필드가 인터페이스 — 엄밀 비교 불가
type MySlice []int               // 비교 불가
type MyMap map[string]int        // 비교 불가
type MyFunc func()               // 비교 불가

func main() {
	// 통과하는 것들
	_ = eq(1, 2)
	_ = eq("a", "b")
	_ = eq(Pair{1, 2}, Pair{3, 4})
	_ = eq([2]int{1, 2}, [2]int{3, 4})
	_ = eq((*int)(nil), (*int)(nil))
	_ = eq(make(chan int), make(chan int))

	// 막히는 것들 — 여섯 가지를 한 번에 던진다
	_ = eq([]int{1}, []int{2})
	_ = eq(map[string]int{}, map[string]int{})
	_ = eq(func() {}, func() {})
	_ = eq(WithSlice{}, WithSlice{})
	_ = eq(MySlice{1}, MySlice{2})
	_ = eq(MyMap{}, MyMap{})
	_ = eq(MyFunc(nil), MyFunc(nil))
}
===== 명령: go build -trimpath -gcflags=-e -o prog . =====
# ex
./t22f.go:23:8: []int does not satisfy comparable
./t22f.go:24:8: map[string]int does not satisfy comparable
./t22f.go:25:8: func() does not satisfy comparable
./t22f.go:26:8: WithSlice does not satisfy comparable
./t22f.go:27:8: MySlice does not satisfy comparable
./t22f.go:28:8: MyMap does not satisfy comparable
./t22f.go:29:8: MyFunc does not satisfy comparable
(exit 1)
```

**왜 그런가**

- ★★★ **일곱 건 전부 `X does not satisfy comparable`** 이고 **종료 코드 1**,
  **실행 파일은 만들어지지 않았다.**
- 통과한 여섯 줄과 막힌 일곱 줄의 경계는 「**엄밀히 비교 가능한가**」다.

| 통과 | 막힘 |
|---|---|
| `int` · `string` · 구조체(`Pair`) · 배열 · 포인터 · 채널 | 슬라이스 · 맵 · 함수 · **그것을 필드로 가진 구조체**(`WithSlice`) |

  ★ `MySlice`·`MyMap`·`MyFunc` 처럼 **이름을 붙여도 막힌다** — 기반 타입이 정한다.
- ★★★ **(4)번과 같은 실수인데 시점이 다르다.**

| | `any` 로 받는다 | `comparable` 제약 |
|---|---|---|
| 언제 안다 | **런타임** | ★ **컴파일** |
| 무엇이 나오나 | `panic: runtime error: comparing uncomparable type []int` | `[]int does not satisfy comparable` |
| 종료 코드 | **2**(실행 실패) | **1**(빌드 실패) |
| 실행 파일 | 만들어졌다 | ★ **안 만들어졌다** |


**출력**

```text
===== 소스: go.mod =====
module ex

go 1.19
===== 소스: t22g.go =====
package main

import "fmt"

func eq[T comparable](a, b T) bool { return a == b }

func dedup[T comparable](xs []T) int {
	seen := make(map[T]bool, len(xs))
	for _, x := range xs {
		seen[x] = true
	}
	return len(seen)
}

func caught(name string, f func()) {
	defer func() {
		if r := recover(); r != nil {
			fmt.Printf("  %-40s panic -> %v\n", name, r)
		}
	}()
	f()
}

func main() {
	fmt.Println("-- 인터페이스를 타입 인자로 주는 것이 컴파일된다 --")
	fmt.Println("  eq[any](1, 1)          =", eq[any](1, 1))
	fmt.Println("  eq[any](1, 2)          =", eq[any](1, 2))
	fmt.Println("  eq[error](nil, nil)    =", eq[error](nil, nil))
	fmt.Println("  dedup[any]([1,1,2])    =", dedup[any]([]any{1, 1, 2}))

	fmt.Println("-- 그 대신 검사가 런타임으로 미뤄진다 --")
	caught("eq[any]([]int{1}, []int{1})", func() {
		fmt.Println(eq[any]([]int{1}, []int{1}))
	})
	caught("dedup[any]([][]int 원소)", func() {
		fmt.Println(dedup[any]([]any{[]int{1}}))
	})

	fmt.Println("-- WithIface{V: []int} 도 같다 : 정적으로는 통과하고 런타임에 터진다 --")
	type WithIface struct{ V any }
	caught("eq[WithIface]({[]int}, {[]int})", func() {
		fmt.Println(eq[WithIface](WithIface{V: []int{1}}, WithIface{V: []int{1}}))
	})
	fmt.Println("  eq[WithIface]({1}, {1}) =", eq[WithIface](WithIface{V: 1}, WithIface{V: 1}))
}
===== 명령: go build -trimpath -gcflags=-e -o prog . =====
# ex
./t22g.go:26:47: any to satisfy comparable requires go1.20 or later (-lang was set to go1.19; check go.mod)
./t22g.go:27:47: any to satisfy comparable requires go1.20 or later (-lang was set to go1.19; check go.mod)
./t22g.go:28:47: error to satisfy comparable requires go1.20 or later (-lang was set to go1.19; check go.mod)
./t22g.go:29:50: any to satisfy comparable requires go1.20 or later (-lang was set to go1.19; check go.mod)
./t22g.go:33:18: any to satisfy comparable requires go1.20 or later (-lang was set to go1.19; check go.mod)
./t22g.go:36:21: any to satisfy comparable requires go1.20 or later (-lang was set to go1.19; check go.mod)
./t22g.go:42:18: WithIface to satisfy comparable requires go1.20 or later (-lang was set to go1.19; check go.mod)
./t22g.go:44:48: WithIface to satisfy comparable requires go1.20 or later (-lang was set to go1.19; check go.mod)
(exit 1)
```

```text
===== 소스: go.mod =====
module ex

go 1.20
===== 소스: t22g.go =====
package main

import "fmt"

func eq[T comparable](a, b T) bool { return a == b }

func dedup[T comparable](xs []T) int {
	seen := make(map[T]bool, len(xs))
	for _, x := range xs {
		seen[x] = true
	}
	return len(seen)
}

func caught(name string, f func()) {
	defer func() {
		if r := recover(); r != nil {
			fmt.Printf("  %-40s panic -> %v\n", name, r)
		}
	}()
	f()
}

func main() {
	fmt.Println("-- 인터페이스를 타입 인자로 주는 것이 컴파일된다 --")
	fmt.Println("  eq[any](1, 1)          =", eq[any](1, 1))
	fmt.Println("  eq[any](1, 2)          =", eq[any](1, 2))
	fmt.Println("  eq[error](nil, nil)    =", eq[error](nil, nil))
	fmt.Println("  dedup[any]([1,1,2])    =", dedup[any]([]any{1, 1, 2}))

	fmt.Println("-- 그 대신 검사가 런타임으로 미뤄진다 --")
	caught("eq[any]([]int{1}, []int{1})", func() {
		fmt.Println(eq[any]([]int{1}, []int{1}))
	})
	caught("dedup[any]([][]int 원소)", func() {
		fmt.Println(dedup[any]([]any{[]int{1}}))
	})

	fmt.Println("-- WithIface{V: []int} 도 같다 : 정적으로는 통과하고 런타임에 터진다 --")
	type WithIface struct{ V any }
	caught("eq[WithIface]({[]int}, {[]int})", func() {
		fmt.Println(eq[WithIface](WithIface{V: []int{1}}, WithIface{V: []int{1}}))
	})
	fmt.Println("  eq[WithIface]({1}, {1}) =", eq[WithIface](WithIface{V: 1}, WithIface{V: 1}))
}
===== 명령: go build -trimpath -o prog . && ./prog =====
-- 인터페이스를 타입 인자로 주는 것이 컴파일된다 --
  eq[any](1, 1)          = true
  eq[any](1, 2)          = false
  eq[error](nil, nil)    = true
  dedup[any]([1,1,2])    = 2
-- 그 대신 검사가 런타임으로 미뤄진다 --
  eq[any]([]int{1}, []int{1})              panic -> runtime error: comparing uncomparable type []int
  dedup[any]([][]int 원소)                   panic -> runtime error: hash of unhashable type []int
-- WithIface{V: []int} 도 같다 : 정적으로는 통과하고 런타임에 터진다 --
  eq[WithIface]({[]int}, {[]int})          panic -> runtime error: comparing uncomparable type []int
  eq[WithIface]({1}, {1}) = true
(exit 0)
```

**왜 그런가**

- ★★★ **`go 1.19` 에서 여덟 건**이 나온다 —
  **`any to satisfy comparable requires go1.20 or later (-lang was set to go1.19; check go.mod)`**.
  ★ **컴파일러가 판 경계를 문장으로 말해 준다.** 릴리스 노트를 옮겨 적을 필요가 없다.
- **`go 1.20` 에서는 그대로 돌아간다.** 소스는 **한 글자도 안 바뀌었다** —
  `go.mod` 의 `1.19` 를 `1.20` 으로 고친 것뿐이다.
- 명세가 그 예외를 한 문단으로 적고 `[Go 1.20]` 표시를 붙인다.

```text
===== 명령: sed -n "2765,2780p" "$(go env GOROOT)/doc/go_spec.html" | sed -e "s/<[^>]*>//g" =====
Satisfying a type constraint


A type argument T satisfies a type constraint C
if T is an element of the type set defined by C; in other words,
if T implements C.
As an exception, a strictly comparable
type constraint may also be satisfied by a comparable
(not necessarily strictly comparable) type argument
[Go 1.20].
More precisely:



A type T satisfies a constraint C if
(exit 0)
```

```text
===== 명령: sed -n "2737,2762p" "$(go env GOROOT)/doc/go_spec.html" | sed -e "s/<[^>]*>//g" =====
interface type comparable
denotes the set of all non-interface types that are
strictly comparable
[Go 1.18].



Even though interfaces that are not type parameters are comparable,
they are not strictly comparable and therefore they do not implement comparable.
However, they satisfy comparable.



int                          // implements comparable (int is strictly comparable)
[]byte                       // does not implement comparable (slices cannot be compared)
interface{}                  // does not implement comparable (see above)
interface{ ~int | ~string }  // type parameter only: implements comparable (int, string types are strictly comparable)
interface{ comparable }      // type parameter only: implements comparable (comparable implements itself)
interface{ ~int | ~[]byte }  // type parameter only: does not implement comparable (slices are not comparable)
interface{ ~struct{ any } }  // type parameter only: does not implement comparable (field any is not strictly comparable)



The comparable interface and interfaces that (directly or indirectly) embed
comparable may only be used as type constraints. They cannot be the types of
values or variables, or components of other, non-interface types.
(exit 0)
```

  ★★ 낱말이 정확하다 — 인터페이스는 `comparable` 을 「**implement 하지 않지만 satisfy 한다**」.
- ★★★ **그 대신 검사가 런타임으로 미뤄진다.** 1.20 판 출력의 둘째 덩어리가 그것이다 —
  `eq[any]([]int{1}, []int{1})` 이 `comparing uncomparable type []int`,
  `dedup[any]` 가 `hash of unhashable type []int` 다.
  **연산이 달라 문구가 갈린 것**((4)번과 같은 짝)이다.
- ★★★ **`WithIface` 가 가장 얄궂다** — `eq[WithIface]({[]int}, {[]int})` 는 **런타임에 터지고**
  `eq[WithIface]({1}, {1})` 은 **`true`** 다. **같은 타입 인자인데 담긴 값에 따라 갈린다.**
  ★ (5)번에서 `WithSlice` 가 **컴파일에서** 막혔던 것과 대비하라 —
  필드가 `[]int` 면 컴파일에서 막히고 `any` 면 런타임으로 미뤄진다.
- 명세가 그 대가를 적어 둔다 — `may panic at run-time (even though comparable type parameters are always strictly comparable)`.

### 6. 컴파일러가 셋, `go vet` 이 하나

**출력**

```text
===== 소스: t22h.go =====
package main

import (
	"fmt"
	"io"
	"strings"
)

type Speaker interface{ Speak() string }
type Talker interface{ Speak() int } // 같은 이름, 다른 시그니처

type Dog struct{}

func (Dog) Bark() string { return "멍" }

func main() {
	var r io.Reader = strings.NewReader("x")
	var n int
	var s Speaker

	// (가) 인터페이스가 아닌 것에 단언한다
	_ = n.(io.Reader)

	// (나) 대상 타입이 그 인터페이스를 만족할 수 없다
	_ = r.(int)

	// (다) 구조체가 메서드를 안 가졌다
	_ = r.(Dog)

	// (라) 인터페이스에서 인터페이스로 — 겹칠 수 없는 시그니처
	_ = s.(Talker)

	fmt.Println(r, n, s)
}
===== 명령: go build -trimpath -gcflags=-e -o prog . =====
# ex
./t22h.go:22:6: invalid operation: n (variable of type int) is not an interface
./t22h.go:25:6: impossible type assertion: r.(int)
	int does not implement io.Reader (missing method Read)
./t22h.go:28:6: impossible type assertion: r.(Dog)
	Dog does not implement io.Reader (missing method Read)
(exit 1)
```

```text
===== 소스: t22i.go =====
package main

import "fmt"

type Speaker interface{ Speak() string }
type Talker interface{ Speak() int } // Speak 의 시그니처가 다르다

func main() {
	var s Speaker
	// comma-ok 형이라 패닉은 안 나는데, 애초에 참이 될 수 없다.
	if t, ok := s.(Talker); ok {
		fmt.Println(t)
	}
	fmt.Println("여기까지 온다")
}
===== 명령: go vet ./... =====
t22i.go:11:17: impossible type assertion: no type can implement both ex.Speaker and ex.Talker (conflicting types for Speak method)
(exit 1)
```

**왜 그런가**

- ★★★ **컴파일 에러는 세 건**이다. 네 자리를 적었는데 셋만 나왔다.

| 자리 | 누가 | 문장 |
|---|---|---|
| **(가)** 인터페이스가 아닌 것에 단언 | 컴파일러 | `invalid operation: n (variable of type int) is not an interface` |
| **(나)** 대상 타입이 만족 못 함 | 컴파일러 | `impossible type assertion: r.(int)` + `int does not implement io.Reader (missing method Read)` |
| **(다)** 구조체가 메서드를 안 가짐 | 컴파일러 | `impossible type assertion: r.(Dog)` + 같은 꼴 |
| ★★ **(라)** 인터페이스끼리 시그니처 충돌 | ★ **`go vet`** | `impossible type assertion: no type can implement both ex.Speaker and ex.Talker (conflicting types for Speak method)` |

- ★★★ **(라)가 컴파일러에서 안 나온 이유** — 명세가 인터페이스로의 단언을
  「**동적 타입이 `T` 를 구현하나**」로 정의하는데, 그것은 **실행 시점의 질문**이다.
  컴파일러는 정적 타입만 보고 「불가능하다」고 단정하지 않는다.
- ★★ **그 자리를 `go vet` 의 `ifaceassert` 분석기가 메운다.** 종료 코드 1이다.
  ★ [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/) (6)절과 대비하라 —
  **거기서 `go vet` 은 탐침 8개 중 0개에 답했다.** 같은 도구인데 주제에 따라 갈린다.

### 7. 타입을 적는 만큼 검사가 앞당겨진다

- **`any` 로 받은 값의 `==` 를 컴파일에서 못 막는 이유** — `any` 는 **모든 타입의 집합**이라
  그 안에 비교 가능한 것과 불가능한 것이 **둘 다** 들어 있다.
  컴파일러가 아는 것은 「인터페이스」뿐이고 **무엇이 담길지는 실행 시점**에 정해진다.
- **`comparable` 이 막을 수 있는 이유** — 제약이 **타입 인자를 그 자리에서 확정**하기 때문이다.
  `eq([]int{1}, []int{2})` 를 부르는 순간 `T = []int` 로 추론되고,
  컴파일러는 그 타입이 집합 밖이라는 것을 **그 줄에서** 안다.
- ★★★ **1.20의 완화가 바꾼 것** — 인터페이스도 타입 인자로 줄 수 있게 됐다.
  그 순간 `T` 가 다시 「**무엇이 담길지 모르는 것**」이 되어 검사가 런타임으로 돌아간다.
  **편의를 얻고 시점을 잃은 것**이다.
- ★★ **「엄밀히 비교 가능」이라는 낱말이 따로 필요한 이유** —
  인터페이스는 **`==` 가 되기는 한다.** 「비교 가능」만으로는 그것을 집합 밖으로 못 민다.
  「**런타임에 패닉할 수 없는가**」라는 더 센 조건이 있어야 `comparable` 의 뜻이 선다.

### 8. 경계에서는 comma-ok, 제네릭에서는 comparable

- **외부 입력** → **comma-ok.** 틀려도 안 터진다. 단항은 「틀릴 수 없다」가 확실한 자리에만.
- **인터페이스 가지가 둘 겹친다** → **구체적인 쪽을 먼저.**
  `Both` 가 `case error` 로 간 것이 실측이다((2)번).
- **제네릭 안에서 맵 키** → **`comparable` 제약.** 컴파일에서 막힌다((5)번).
  ★ 단 **타입 인자로 인터페이스를 주면** 그 보장이 사라진다((5)번).
- ★★★ **`any` 를 쓰지 말아야 하는 이유 둘** —
  ① `==` 가 **런타임 패닉**이 된다((4)번) ② 맵 키로 쓰면 **`hash of unhashable type`** 이 된다.
  둘 다 **타입 파라미터로 받으면 컴파일에서 걸린다**(목록의 **37번 주제**).

### 9. Rust 는 comma-ok 만, 자바는 둘을 따로

- **Rust 의 `downcast_ref`** 는 **`Option` 을 돌려준다** — **comma-ok 형만 있고 단항이 없다.**
  ★ 「패닉하는 다운캐스트」라는 문법 자체가 없다.
  (Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **24번**.)
- **자바** — `instanceof` 로 **묻고** 캐스트로 **꺼낸다.** 둘이 **따로**라
  묻지 않고 캐스트하면 `ClassCastException` 이다
  ([`../../../java/syntax/22-instanceof-type-patterns/`](../../../java/syntax/22-instanceof-type-patterns/)).
  ★ 자바 16의 패턴 매칭(`if (o instanceof String s)`)이 그 둘을 묶은 것이고,
  **Go 의 comma-ok 가 처음부터 그 모양**이었다.
- ★★ 세 언어가 같은 자리에서 갈린다 — 「**틀렸을 때 터지는 길을 문법이 남겨 두는가**」.
  Go 는 남겨 두고(단항), 자바도 남겨 두고(맨 캐스트), Rust 는 **안 남겨 둔다.**

### 10. 다른 주제와 잇기

- 타입 스위치 **문법**의 정본 — [15번 주제](../15-switch-type-switch-fallthrough-labels-and-goto/) (3)절.
- 구조체 **비교 가능성**의 정본 — [17번 주제](../17-struct-literals-comparability-field-tags-and-sorting/) (4)절.
- **제네릭 일반**의 정본 — 목록의 **37번 주제**. 여기는 `comparable` 하나까지.
- **`case nil`** 이 무엇을 보는지 —
  [15번 주제](../15-switch-type-switch-fallthrough-labels-and-goto/)가 문법의 정본이고
  [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/)가 「그것이 무엇을 못 막나」의 정본이다.
- **`errors.As`** — [24번 주제](../24-error-wrapping-and-errors-is-as-join/). ★ **사슬을 따라 단언을 반복하는 것**이 그 함수다.
- 덤 — **인터페이스 선언·암묵 구현**은 [20번 주제](../20-interface-declaration-and-implicit-implementation/),
  **메서드 집합**은 [19번 주제](../19-method-sets-value-vs-pointer-receiver/),
  **`go vet` 전반**은 목록의 **52번 주제**다.


---

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행 1회** | `normalize-shaky.py` 로 **★고칠 것 0** |
| 판 확인 | `go version` | 1 | `go1.27.1 linux/amd64` |
| ★★ 실패 모양 여섯 (`t22a`) | `go build && ./prog` | 1 | 패닉 문구 **6가지** · comma-ok 는 전부 `false` |
| 단항 전문 (`t22b`) | 〃 | 1 | `interface conversion: main.Square is not interface { Perimeter() float64 }` · **exit 2** |
| ★★ 가지 겹침 (`t22c`) | 〃 | 1 | `Both` → `case error` · `(*mySlice)(nil)` → `case error` |
| `any` 가 별칭 (`t22d`) | 〃 | 1 | `interface {}` · `==` 가 `true` · `func(interface {})` |
| ★★ 중복 선언 (`t22dx`) | `go build -gcflags=-e` | 1 | `method T.M already declared` · **exit 1** |
| ★★★ 런타임 패닉 (`t22e`) | `go build && ./prog` | 1 | `comparing uncomparable type` 4건 · `hash of unhashable type` 1건 · **exit 2** |
| ★★★ 컴파일 에러 (`t22f`) | `go build -gcflags=-e` | 1 | `does not satisfy comparable` **7건** · **exit 1** |
| ★★★ 판 경계 (`t22g`) | **`go.mod` 의 `go` 줄만 바꿔** 두 번 | 2 | 1.19 → `requires go1.20 or later` **8건** · 1.20 → 컴파일되고 런타임에 2건 패닉 |
| ★★ 불가능한 단언 (`t22h`·`t22i`) | `go build -gcflags=-e` · `go vet ./...` | 2 | 컴파일러 **3건** · vet **1건** |
| 명세 인용 | `sed` 로 `go_spec.html` 에서 직접 | 4 | Type assertions · comma-ok · 비교 규칙 · `comparable`/satisfy |
| 형태 (`t22form`) | `go build && ./prog` | 1 | 여섯 줄 |

**구현·환경에 달린 항목**(버전이 오르거나 타깃이 바뀌면 **다시 찍어야 하는** 것)

| 항목 | 무엇에 달렸나 |
|---|---|
| 패닉·컴파일 에러의 **문구 자체** | **툴체인 판(go1.27.1)** |
| `-lang` 게이트가 **안내까지 주는 것**(`check go.mod`) | **도구(구현)** |
| 맵 키 실패가 **다른 문장인 것** | **런타임(구현)** — 명세는 연산별 문장을 안 정한다 |
| `go vet` 의 `ifaceassert` 가 **잡는 범위** | **도구(구현)**. 판이 오르면 달라질 수 있다 |
| `%T` 가 `interface {}` 로 찍는 것 | **`fmt`·`reflect` 의 계약** |
| 단언·타입 스위치의 **비용** | ★ **안 쟀다**(목록의 **50번 주제**) |
| `reflect` 로 런타임 단언하는 것 | ★ **안 던졌다** |
| 제네릭의 **타입 추론·타입 집합·`~T`** | ★ **안 던졌다**(목록의 **37번 주제**) |
| `cmp.Ordered` 등 다른 제약 | ★ **안 던졌다**(목록의 **38번 주제**) |
| `go.mod` 를 1.17 로 낮춘 판(`comparable` 자체가 없던 때) | ★ **안 던졌다** |
| 타입 스위치가 만드는 **기계어** | ★ **안 던졌다**(목록의 **52번 주제**) |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다.

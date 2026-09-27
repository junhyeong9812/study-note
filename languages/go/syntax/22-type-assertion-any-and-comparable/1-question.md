# go/syntax/22 — 타입 단언·`any`·`comparable` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> ★★★ **모든 문제에서 「이것이 컴파일에서 걸리나 런타임에서 걸리나」를 먼저 적어라.**
> 이 주제의 급소가 그 한 줄이다.
> ★★ **패닉 문구는 낱말까지 적어 보라** — `is B, not C` 인지 `is not I: missing method M` 인지가 갈린다.
> ★ **「누가 말해 주나」도 물어라** — 컴파일러인가 `go vet` 인가 런타임인가.
> ★ [15번 주제](../15-switch-type-switch-fallthrough-labels-and-goto/)를 안다면
> **타입 스위치 문법은 아는 것으로 치고** 여기서는 **가지가 겹칠 때**만 묻는다.
> 소스는 전부 `go build -trimpath -o prog . && ./prog` 로 던졌다. 모듈 이름은 `ex` 다.
> 컴파일 에러를 전부 보려고 몇 블록은 `-gcflags=-e` 를 붙였고,
> 판 경계를 보려고 두 블록은 **`go.mod` 의 `go` 줄만 바꿔** 두 번 던졌다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 단언이 실패하는 모양과 그 전문 (예측)

```go
// t22a.go
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
```

- 첫 덩어리 세 줄 — `a.(string)`·`a.(int)`·`sh.(Circle)` 의 `ok` 와 값이 각각 무엇인가?
- 둘째 덩어리 여섯 줄의 **패닉 문구를 낱말까지** 적어라.
- `any(42).(string)` 과 `any(42).(fmt.Stringer)` 의 문구가 **왜 다른 모양**인가?
- 셋째 덩어리 — 같은 여섯 자리를 comma-ok 로 물으면 무엇이 되나?


```go
// t22b.go
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
```

- `면적 :` 줄에 무엇이 찍히나?
- 패닉 문구 전문과 종료 코드는?
- 익명 인터페이스에 단언했다 — 문구에 그 인터페이스가 어떻게 들어가나?

### 2. 가지가 겹치면 무엇이 이기나 (예측)

```go
// t22c.go
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
```

- 아홉 값이 각각 **어느 가지**로 가나?
- `Both` 는 `Error()` 와 `String()` 을 둘 다 갖고 있다 — 어느 가지로 가나?
- `(*mySlice)(nil)` 은 어느 가지로 가나 — `case nil` 인가?
- `case int, int64` 가지에서 `%T` 가 무엇을 찍나?

### 3. `any` 가 새 타입인가 (예측)

```go
// t22d.go
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
```

- `reflect.TypeOf((*any)(nil)).Elem()` 이 무엇을 찍나?
- 두 타입이 `==` 로 같은가?
- `func(any)` 를 `func(interface{})` 에 대입할 수 있나 — `%T` 는 무엇으로 찍나?


```go
// t22dx.go
package main

type T struct{}

// 같은 이름의 메서드를 any 와 interface{} 로 하나씩 선언한다.
// 두 타입이 다르면 오버로드가 아니라 그냥 중복 선언이고,
// 같은 타입이면 컴파일러가 그렇게 말해 준다.
func (T) M(x any)         {}
func (T) M(x interface{}) {}

func main() {}
```

- 컴파일 에러가 나나? 나면 문장과 종료 코드는?
- 이 결과가 **무엇을 증명**하나?

### 4. `any` 끼리 `==` 하면 (예측)

```go
// t22e.go
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
```

- `any([]int) == any(int)` 은 패닉인가 `false` 인가 — 왜인가?
- `any([]int) == any([]int)`·`any(map) == any(map)`·`any(func) == any(func)` 은 각각 무엇인가?
- `any([]int) == nil` 은 무엇인가 — 왜 안 터지나?
- `Box{[]int} == Box{[]int}` 는 무엇인가?
- 맵 키로 쓰면 **문구가 어떻게 달라지나**?
- 마지막 — 받지 않고 던지면 문구와 종료 코드는?

### 5. `comparable` 제약과 판 경계 (예측)

```go
// t22f.go
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
```

- 컴파일이 통과하나 — 아니면 **몇 건**이 나오나?
- 에러 문장은 어떤 형태인가?
- 종료 코드는 몇이고, 실행 파일은 만들어지나?
- 통과하는 여섯 줄과 막히는 일곱 줄을 가르는 기준은 무엇인가?


```go
// t22g.go
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
```

<!-- 같은 소스를 go.mod 의 go 1.19 와 go 1.20 두 판으로 던졌다. -->

- `go 1.19` 판에서 **몇 건**이 나오고 문장은 무엇인가?
- `go 1.20` 판에서는 컴파일되나 — 되면 출력의 첫 덩어리 네 줄은 무엇인가?
- 둘째 덩어리 두 줄은 무엇이 되나 — 두 문구가 왜 다른가?
- `eq[WithIface]({[]int}, {[]int})` 와 `eq[WithIface]({1}, {1})` 이 왜 갈리나?

### 6. 불가능한 단언은 누가 잡나 (예측)

```go
// t22h.go
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
```

- 컴파일 에러가 **몇 건** 나오고 각 문장은 무엇인가?
- 네 자리를 적었는데 몇 건이 나왔나 — **안 잡힌 것**은 무엇이고 왜인가?
- 그 안 잡힌 자리를 `go vet` 은 잡나?

### 7. 왜 두 시점으로 갈리나 (왜)

- `any` 로 받은 값의 `==` 는 왜 컴파일에서 못 막나?
- `comparable` 제약은 어떻게 컴파일에서 막나 — 무엇을 알고 있기에 가능한가?
- 그 둘 사이에 **1.20의 완화**가 무엇을 바꿨나?
- 「엄밀히 비교 가능」이라는 낱말이 왜 따로 필요한가?

### 8. 어느 꼴을 고르나 (경계)

- 외부 입력에서 값을 꺼낸다 — 단항인가 comma-ok 인가?
- 인터페이스 가지가 둘 겹친다 — 어느 것을 먼저 적나?
- 제네릭 함수 안에서 맵 키로 쓴다 — 제약을 무엇으로 거나?
- `any` 를 쓰지 말아야 하는 이유를 **이 주제의 실측 두 개**로 답하라.

### 9. 다른 언어와 나란히 (연결)

- Rust 의 `downcast_ref` 는 두 꼴 중 어느 쪽에 해당하나?
- 자바의 `instanceof` 와 캐스트는 Go 의 무엇에 해당하나 — 실패하면 무엇이 되나?
- Go 의 comma-ok 가 그 둘을 **한 식으로 묶은 것**이라는 말은 무슨 뜻인가?

### 10. 다른 주제와 잇기 (연결)

- 타입 스위치 문법의 정본은 몇 번 주제인가?
- 구조체 비교 가능성의 정본은 몇 번 주제인가?
- 제네릭 일반의 정본은 몇 번 주제인가?
- `case nil` 이 무엇을 보는지의 정본은 몇 번 주제인가?
- `errors.As` 가 단언과 어떻게 이어지는지는 몇 번 주제인가?


## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

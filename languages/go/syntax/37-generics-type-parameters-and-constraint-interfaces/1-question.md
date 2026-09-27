# go/syntax/37 — 제네릭: 타입 파라미터와 제약 인터페이스(1.18) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ **모든 문제에서 「이 잘못을 누가, 언제 알려 주나 — 컴파일러인가, 실행인가, 아무도 아닌가」를 먼저 적어라.**
> ★★ **「이것은 명세의 의미인가, gc 의 구현인가」를 매번 물어라.**
> 소스는 전부 `go build -trimpath -o prog .`(컴파일 에러를 다 보려면 `-gcflags=-e`)로 빌드했다. 모듈 이름은 `ex`, `go.mod` 는 `go 1.27` 이다(판을 바꾼 문항은 따로 적었다).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 같은 최댓값 함수를 세 가지로 받으면 (예측)

```go
// t37maxany.go
package main

// 최댓값 — any 로 받는다.
func MaxAny(xs ...any) any {
	m := xs[0]
	for _, x := range xs[1:] {
		if x.(int) > m.(int) {
			m = x
		}
	}
	return m
}

func main() {
	ints := []int{3, 9, 4}
	i, f := 3, 9.5
	_ = MaxAny(true, false)    // p1
	var got int = MaxAny(i, 9) // p2
	_ = MaxAny(ints...)        // p3
	_ = MaxAny(i, f)           // p4
	_, _ = got, ints
}
```

```go
// t37maxiface.go
package main

// 최댓값 — 인터페이스로 받는다.
type Ord interface{ Less(Ord) bool }

type N int

func (a N) Less(b Ord) bool { return a < b.(N) }

type F float64

func (a F) Less(b Ord) bool { return a < b.(F) }

func MaxI(xs ...Ord) Ord {
	m := xs[0]
	for _, x := range xs[1:] {
		if m.Less(x) {
			m = x
		}
	}
	return m
}

func main() {
	ns := []N{3, 9, 4}
	i, f := 3, 9.5
	_ = MaxI(true, false)        // p1
	var got N = MaxI(N(i), N(9)) // p2
	_ = MaxI(ns...)              // p3
	_ = MaxI(N(i), F(f))         // p4
	_, _ = got, ns
}
```

```go
// t37maxgen.go
package main

import "cmp"

// 최댓값 — 타입 파라미터로 받는다.
func Max[T cmp.Ordered](xs ...T) T {
	m := xs[0]
	for _, x := range xs[1:] {
		if x > m {
			m = x
		}
	}
	return m
}

func main() {
	ints := []int{3, 9, 4}
	i, f := 3, 9.5
	_ = Max(true, false)    // p1
	var got int = Max(i, 9) // p2
	_ = Max(ints...)        // p3
	_ = Max(i, f)           // p4
	_, _ = got, ints
}
```

<!-- 세 파일을 각각 go build -gcflags=-e 로 빌드한다. 스크립트가 // pN 주석의 줄에 에러가 떨어졌으면 「막힘」, 아니면 「통과」로 찍는다. -->

- 세 판 × `p1`\~`p4` 의 막힘/통과를 표로 채워라.
- 인터페이스 판의 `p2` 에서 컴파일러는 무엇이 필요하다고 말하나?
- 인터페이스 판과 제네릭 판이 갈리는 칸은 어디인가? 갈린 칸마다 어느 쪽이 옳은가?

### 2. 같은 격자를 「이어 쓰기」에 (예측)

```go
// t37joinany.go
package main

import "fmt"

type Name string

func (n Name) String() string { return string(n) }

type Code int

func (c Code) String() string { return fmt.Sprintf("#%d", int(c)) }

// 이어 쓰기 — any 로 받는다.
func JoinAny(xs ...any) string {
	s := ""
	for _, x := range xs {
		s += x.(fmt.Stringer).String() + " "
	}
	return s
}

func main() {
	names := []Name{"kim", "lee"}
	_ = JoinAny(1, 2)                     // p1
	var got string = JoinAny(Name("kim")) // p2
	_ = JoinAny(names...)                 // p3
	_ = JoinAny(Name("kim"), Code(7))     // p4
	_, _ = got, names
}
```

```go
// t37joiniface.go
package main

import "fmt"

type Name string

func (n Name) String() string { return string(n) }

type Code int

func (c Code) String() string { return fmt.Sprintf("#%d", int(c)) }

// 이어 쓰기 — 인터페이스로 받는다.
func JoinI(xs ...fmt.Stringer) string {
	s := ""
	for _, x := range xs {
		s += x.String() + " "
	}
	return s
}

func main() {
	names := []Name{"kim", "lee"}
	_ = JoinI(1, 2)                     // p1
	var got string = JoinI(Name("kim")) // p2
	_ = JoinI(names...)                 // p3
	_ = JoinI(Name("kim"), Code(7))     // p4
	_, _ = got, names
}
```

```go
// t37joingen.go
package main

import "fmt"

type Name string

func (n Name) String() string { return string(n) }

type Code int

func (c Code) String() string { return fmt.Sprintf("#%d", int(c)) }

// 이어 쓰기 — 타입 파라미터로 받는다.
func JoinG[T fmt.Stringer](xs ...T) string {
	s := ""
	for _, x := range xs {
		s += x.String() + " "
	}
	return s
}

func main() {
	names := []Name{"kim", "lee"}
	_ = JoinG(1, 2)                     // p1
	var got string = JoinG(Name("kim")) // p2
	_ = JoinG(names...)                 // p3
	_ = JoinG(Name("kim"), Code(7))     // p4
	_, _ = got, names
}
```

- 세 판 × `p1`\~`p4` 의 막힘/통과는?
- 1번과 합쳐 인터페이스 판과 제네릭 판이 갈린 칸은 모두 몇 칸인가?
- 이어 쓰기에서 `p2` 가 안 갈리는 이유는? `p4` 에서는 어느 쪽이 옳은가?

### 3. 컴파일을 통과한 칸을 돌리면 (예측)

```go
// t37anyrun.go
package main

import "fmt"

type Ord interface{ Less(Ord) bool }

type N int

func (a N) Less(b Ord) bool { return a < b.(N) }

type F float64

func (a F) Less(b Ord) bool { return a < b.(F) }

func MaxAny(xs ...any) any {
	m := xs[0]
	for _, x := range xs[1:] {
		if x.(int) > m.(int) {
			m = x
		}
	}
	return m
}

func MaxI(xs ...Ord) Ord {
	m := xs[0]
	for _, x := range xs[1:] {
		if m.Less(x) {
			m = x
		}
	}
	return m
}

func JoinAny(xs ...any) string {
	s := ""
	for _, x := range xs {
		s += x.(fmt.Stringer).String() + " "
	}
	return s
}

// 컴파일을 통과한 호출을 실제로 돌려 본다.
func try(label string, f func() any) {
	defer func() {
		if r := recover(); r != nil {
			fmt.Printf("%-22s → recover: %v\n", label, r)
		}
	}()
	v := f()
	fmt.Printf("%-22s → %v (%T)\n", label, v, v)
}

func main() {
	try("MaxAny(3, 9)", func() any { return MaxAny(3, 9) })
	try("MaxAny(true, false)", func() any { return MaxAny(true, false) })
	try("MaxAny(3, 9.5)", func() any { return MaxAny(3, 9.5) })
	try("MaxI(N(3), F(9.5))", func() any { return MaxI(N(3), F(9.5)) })
	try("JoinAny(1, 2)", func() any { return JoinAny(1, 2) })
}
```

- 다섯 줄은 각각 무엇을 찍나? 패닉이 나는 줄은 **어느 함수의 어느 식**에서 나나?
- `MaxI(N(3), F(9.5))` 를 컴파일러가 통과시킨 것은 잘못인가?

### 4. 제약 에러 (예측)

```go
// t37constraint.go
package main

type MyInt int

type Number interface{ ~int | ~float64 }

func SumInt[T int](xs []T) (s T) {
	for _, x := range xs {
		s += x
	}
	return s
}

func SumTilde[T ~int](xs []T) (s T) {
	for _, x := range xs {
		s += x
	}
	return s
}

func Zero[T any]() T {
	var z T
	return z
}

type Setter interface{ Set(string) }

type Box struct{ v string }

func (b *Box) Set(s string) { b.v = s }

func Fill[T Setter](xs []T) {
	for _, x := range xs {
		x.Set("v")
	}
}

func main() {
	_ = SumInt([]MyInt{1, 2})   // p1
	_ = SumTilde([]MyInt{1, 2}) // p2
	var n Number                // p3
	_ = Zero()                  // p4
	Fill([]Box{{}})             // p5
	_ = n
}
```

- `p1`\~`p5` 중 에러가 나는 줄과 그 진단은?
- `p1` 의 진단은 무엇을 되묻나?

### 5. `*T` 를 담은 제약 (경계)

```go
// t37fix.go
package main

import "fmt"

type MyInt int

func SumTilde[T ~int](xs []T) (s T) {
	for _, x := range xs {
		s += x
	}
	return s
}

type Box struct{ v string }

func (b *Box) Set(s string) { b.v = s }

// PT 는 「*T 이면서 Set 을 가진 것」이다 — 포인터 리시버 메서드를 제약으로 부른다.
func Fill[T any, PT interface {
	*T
	Set(string)
}](n int) []T {
	xs := make([]T, n)
	for i := range xs {
		PT(&xs[i]).Set("v")
	}
	return xs
}

func main() {
	s := SumTilde([]MyInt{1, 2})
	fmt.Printf("SumTilde: %v (%T)\n", s, s)
	fmt.Printf("SumTilde(int): %T\n", SumTilde([]int{1}))
	fmt.Printf("Fill[Box](2): %+v\n", Fill[Box](2))
}
```

- 이 프로그램의 세 줄 출력은? `SumTilde([]MyInt{…})` 의 결과 타입은 무엇인가?
- `Fill` 을 부를 때 `PT` 를 적지 않아도 되는 이유는? 4번의 `p5` 와 무엇이 다른가?

### 6. 메서드가 타입 파라미터를 가지면 (예측)

```go
// t37method.go
package main

import "fmt"

type Bag []string

// 메서드 자신이 타입 파라미터 T 를 선언한다.
func (b Bag) Map[T any](f func(string) T) []T {
	out := make([]T, 0, len(b))
	for _, s := range b {
		out = append(out, f(s))
	}
	return out
}

func main() {
	b := Bag{"go", "rust"}
	fmt.Println(b.Map(func(s string) int { return len(s) }))
	fmt.Println(b.Map(func(s string) string { return s + "!" }))
}
```

<!-- go.mod 의 go 줄만 1.18 · 1.26 · 1.27 로 바꿔 빌드하고, 되면 돌린다. 마지막 줄에 빌드가 막힌 판 수. -->

- 세 판의 빌드 결과는? 되는 판의 출력은?
- 이 판에서 무엇이 결과를 갈랐나 — 컴파일러의 판인가?

### 7. 인터페이스 쪽에서 보면 (경계)

```go
// t37methodif.go
package main

type Bag []string

func (b Bag) Map[T any](f func(string) T) []T {
	out := make([]T, 0, len(b))
	for _, s := range b {
		out = append(out, f(s))
	}
	return out
}

type Mapper interface {
	Map(func(string) int) []int
}

type GenericMapper interface {
	Map[T any](func(string) T) []T // p1
}

var _ Mapper = Bag{} // p2

func main() {}
```

- `p1`·`p2` 의 진단은? 제네릭 메서드는 인터페이스를 만족시킬 수 있나?

### 8. 몇 벌이 되나 (예측)

```go
// t37shape.go
package main

import "fmt"

type MyInt int
type A struct{ n int }
type B struct{ s string }

//go:noinline
func First[T any](xs []T) T { return xs[0] }

//go:noinline
func FirstAny(xs []any) any { return xs[0] }

func main() {
	fmt.Println(First([]int{1}), First([]MyInt{2}), First([]float64{3}), First([]string{"s"}))
	fmt.Println(First([]*A{{1}}), First([]*B{{"b"}}))
	fmt.Println(FirstAny([]any{1}), FirstAny([]any{"s"}))
}
```

<!-- 빌드해 돌린 뒤 go tool nm -sort name 의 결과에서 First 와 그 사전의 심볼만 (종류, 이름) 으로 뽑고, 마지막 줄에 본문(T)과 사전(R)의 수를 센다. -->

- 타입 인자 여섯 가지로 불린 `First` 의 **본문(T)** 은 몇 벌, **사전(R)** 은 몇 개인가? 어느 타입들이 합쳐지나?
- `FirstAny` 는 몇 벌인가?

### 9. 타입 목록을 담은 인터페이스 (왜)

- `interface{ ~int | ~float64 }` 를 변수의 타입으로 쓸 수 없는 이유를 명세의 말로 하라.

### 10. `comparable` 과 판 (연결)

- [22번 주제](../22-type-assertion-any-and-comparable/)에서 `any` 를 `==` 한 것과 `comparable` 제약이 갈린 **시점**은? 그 편의 1.20 판 격자는 무엇을 갈랐나?

### 11. 벌 수는 누가 정하나 (왜)

- 8번의 「합쳐진 벌」은 명세의 보장인가 구현의 선택인가? [Rust 31번](../../../rust/syntax/31-generics-trait-bounds-where-and-monomorphization/)의 단형화와 무엇이 같고 무엇이 다른가?
- 「제네릭이 느리다」는 이 문서에서 무엇으로 답했나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

# go/syntax/37 — 제네릭: 타입 파라미터와 제약 인터페이스(1.18) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★ **근거로 읽을 칸** — 격자의 막힘/통과 · `갈린 칸 5 / 8` · 진단 문구와 `파일:줄:칸` · `recover` 가 받은 값 · `빌드가 막힌 판 2 / 3`.
> **판을 타는 칸** — 8번의 심볼 이름·벌 수(**gc 의 구현**이다).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 인터페이스 판은 `need type assertion` · 갈린 칸은 `p2`·`p3`·`p4` — 셋 다 제네릭이 옳다

**출력**

```text
===== 명령: n=0; for t in max join; do for k in any iface gen; do d=$t$k; f=$(ls $d/*.go); printf "module ex\n\ngo 1.27\n" > $d/go.mod; (cd $d && go build -gcflags=-e -o /dev/null . 2>err.txt); row=; for p in p1 p2 p3 p4; do L=$(grep -n "// $p\$" $f | cut -d: -f1); if grep -q "\.go:$L:" $d/err.txt; then v=막힘; else v=통과; fi; eval "R_${t}_${k}_$p=$v"; row="$row  $p=$v"; done; echo "[$t / $k]$row"; done; for p in p1 p2 p3 p4; do a=$(eval echo \$R_${t}_iface_$p); b=$(eval echo \$R_${t}_gen_$p); if [ "$a" != "$b" ]; then n=$((n+1)); fi; done; done; echo "인터페이스 판과 제네릭 판이 갈린 칸 $n / 8" =====
[max / any]  p1=통과  p2=막힘  p3=막힘  p4=통과
[max / iface]  p1=막힘  p2=막힘  p3=막힘  p4=통과
[max / gen]  p1=막힘  p2=통과  p3=통과  p4=막힘
[join / any]  p1=통과  p2=통과  p3=막힘  p4=통과
[join / iface]  p1=막힘  p2=통과  p3=막힘  p4=통과
[join / gen]  p1=막힘  p2=통과  p3=통과  p4=막힘
인터페이스 판과 제네릭 판이 갈린 칸 5 / 8
(exit 0)
```

```text
===== 소스: t37maxiface.go =====
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
===== 명령: go build -trimpath -gcflags=-e -o prog . =====
# ex
./t37maxiface.go:27:11: cannot use true (constant of type bool) as Ord value in argument to MaxI: bool does not implement Ord (missing method Less)
./t37maxiface.go:27:17: cannot use false (constant of type bool) as Ord value in argument to MaxI: bool does not implement Ord (missing method Less)
./t37maxiface.go:28:14: cannot use MaxI(N(i), N(9)) (value of interface type Ord) as N value in variable declaration: need type assertion
./t37maxiface.go:29:11: cannot use ns (variable of type []N) as []Ord value in argument to MaxI
(exit 1)
```

```text
===== 소스: t37maxgen.go =====
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
===== 명령: go build -trimpath -gcflags=-e -o prog . =====
# ex
./t37maxgen.go:19:9: bool does not satisfy cmp.Ordered (bool missing in ~int | ~int8 | ~int16 | ~int32 | ~int64 | ~uint | ~uint8 | ~uint16 | ~uint32 | ~uint64 | ~uintptr | ~float32 | ~float64 | ~string)
./t37maxgen.go:22:13: in call to Max, type float64 of f does not match inferred type int for T
(exit 1)
```

**왜 그런가**

- ★★★ **`p1`(bool)** — `any` 만 통과, **인터페이스와 제네릭은 둘 다 막는다.** 틀린 타입을 막는 것은 제네릭만의 장점이 아니다.
- ★★★ **`p2`** — 인터페이스 판은 `Ord` 를 돌려주므로 `var got N = …` 에 「**need type assertion**」. 제네릭은 `T` 를 돌려주므로 **`int` 가 그대로 나온다.**
- ★★ **`p3`** — `[]N` 은 `[]Ord` 로 **바뀌지 않는다**(`cannot use ns (variable of type []N) as []Ord value`). 제네릭만 그대로 받는다.
- ★★ **`p4`** — `Max(i, f)` 는 `type float64 of f does not match inferred type int for T` 로 막힌다. **`int` 와 `float64` 의 최댓값은 뜻이 없으니 막는 쪽이 옳다.** 인터페이스 판은 통과시키고 실행에서 터진다(3번).

### 2. 이어 쓰기는 `p3`·`p4` 만 갈린다 — 합쳐 `5 / 8` · `p2` 는 반환이 `string` 이라 · `p4` 는 인터페이스가 옳다

**출력**

```text
===== 명령: n=0; for t in max join; do for k in any iface gen; do d=$t$k; f=$(ls $d/*.go); printf "module ex\n\ngo 1.27\n" > $d/go.mod; (cd $d && go build -gcflags=-e -o /dev/null . 2>err.txt); row=; for p in p1 p2 p3 p4; do L=$(grep -n "// $p\$" $f | cut -d: -f1); if grep -q "\.go:$L:" $d/err.txt; then v=막힘; else v=통과; fi; eval "R_${t}_${k}_$p=$v"; row="$row  $p=$v"; done; echo "[$t / $k]$row"; done; for p in p1 p2 p3 p4; do a=$(eval echo \$R_${t}_iface_$p); b=$(eval echo \$R_${t}_gen_$p); if [ "$a" != "$b" ]; then n=$((n+1)); fi; done; done; echo "인터페이스 판과 제네릭 판이 갈린 칸 $n / 8" =====
[max / any]  p1=통과  p2=막힘  p3=막힘  p4=통과
[max / iface]  p1=막힘  p2=막힘  p3=막힘  p4=통과
[max / gen]  p1=막힘  p2=통과  p3=통과  p4=막힘
[join / any]  p1=통과  p2=통과  p3=막힘  p4=통과
[join / iface]  p1=막힘  p2=통과  p3=막힘  p4=통과
[join / gen]  p1=막힘  p2=통과  p3=통과  p4=막힘
인터페이스 판과 제네릭 판이 갈린 칸 5 / 8
(exit 0)
```

**왜 그런가**

- ★★★ **마지막 줄 `인터페이스 판과 제네릭 판이 갈린 칸 5 / 8`** — 최댓값 3, 이어 쓰기 2.
- ★★ **`p2` 가 안 갈린다** — 반환이 `string` 으로 **고정**이라 잃을 타입이 처음부터 없다.
- ★★★ **`p4` 는 방향이 반대다** — `JoinG(Name("kim"), Code(7))` 는 `T` 가 **한 번에 한 타입**이라 막힌다. 섞어 받는 것이 목적인 함수라면 **인터페이스가 옳다.**
- ★ 판단 규칙 — 「**넣은 타입이 나와야 하나 · 연산자가 필요한가**」면 제네릭, 「**메서드만 부르고 섞어 받나**」면 인터페이스.

### 3. 첫 줄만 `9 (int)`, 나머지 넷은 `interface conversion` 패닉 · 컴파일러는 옳았다 — 약속이 시그니처에 없었다

**출력**

```text
===== 소스: t37anyrun.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
MaxAny(3, 9)           → 9 (int)
MaxAny(true, false)    → recover: interface conversion: interface {} is bool, not int
MaxAny(3, 9.5)         → recover: interface conversion: interface {} is float64, not int
MaxI(N(3), F(9.5))     → recover: interface conversion: main.Ord is main.F, not main.N
JoinAny(1, 2)          → recover: interface conversion: int is not fmt.Stringer: missing method String
(exit 0)
```

**왜 그런가**

- ★★★ `MaxAny(true, false)`·`MaxAny(3, 9.5)` 는 **`MaxAny` 안의 `x.(int)`** 에서, `JoinAny(1, 2)` 는 **`x.(fmt.Stringer)`** 에서, `MaxI(N(3), F(9.5))` 는 **`N.Less` 안의 `b.(N)`** 에서 터졌다.
- ★★★ **컴파일러는 옳았다** — `N` 도 `F` 도 `Ord` 를 **구현한다.** 「`Less` 의 인자는 **같은 타입**」이라는 약속을 `Less(Ord) bool` 은 **적을 방법이 없다.** 제네릭 `Max[T](xs ...T)` 는 그것을 「전부 같은 `T`」로 **시그니처에 적는다.**
- ★ `MaxAny(3, 9)` 의 `(int)` 는 **동적 타입**이다 — 정적 타입은 `any` 라 1번 `p2` 처럼 담으려면 단언이 필요하다.

### 4. `p1`·`p3`·`p4`·`p5` · 「`~` 를 빠뜨렸나」

**출력**

```text
===== 소스: t37constraint.go =====
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
===== 명령: go build -trimpath -gcflags=-e -o prog . =====
# ex
./t37constraint.go:39:12: MyInt does not satisfy int (possibly missing ~ for int in int)
./t37constraint.go:41:8: cannot use type Number outside a type constraint: interface contains type constraints
./t37constraint.go:42:10: in call to Zero, cannot infer T (declared at ./t37constraint.go:21:11)
./t37constraint.go:43:6: in call to Fill, T (type Box) does not satisfy Setter (method Set has pointer receiver)
(exit 1)
```

**왜 그런가**

- ★★★ **`p1` — `MyInt does not satisfy int (possibly missing ~ for int in int)`.** 제약 `int` 의 타입 집합은 **`int` 하나**다. `~int` 라야 기반 타입이 `int` 인 것이 다 들어온다 — **`p2` 는 통과.**
- ★★★ **`p3` — `cannot use type Number outside a type constraint: interface contains type constraints`.** 타입 목록 인터페이스는 **제약으로만** 쓴다.
- ★★ **`p4` — `cannot infer T`.** 인자가 없으면 추론할 재료가 없다.
- ★★★ **`p5` — `method Set has pointer receiver`.** 값 `Box` 의 메서드 집합에는 `*Box` 의 `Set` 이 없다([19번 주제](../19-method-sets-value-vs-pointer-receiver/) (1)절).

### 5. `3 (main.MyInt)` · `int` · `[{v:v} {v:v}]` — `PT` 는 `*Box` 로 추론된다

**출력**

```text
===== 소스: t37fix.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
SumTilde: 3 (main.MyInt)
SumTilde(int): int
Fill[Box](2): [{v:v} {v:v}]
(exit 0)
```

**왜 그런가**

- ★★ **`~int` 는 돌려줄 때도 `MyInt`** 다 — 받은 타입이 그대로 흘러나온다.
- ★★★ `PT interface{ *T; Set(string) }` 의 타입 집합은 「**`*T` 하나이면서 `Set` 을 가진 것**」이다. `T` 를 `Box` 로 주면 `PT` 는 **`*Box` 하나**로 정해져 추론된다.
- ★★ 4번 `p5` 는 **값 `T` 에게** 포인터 메서드를 요구했다. 여기서는 **`PT(&xs[i])` 로 주소를 얻은 쪽**에게 요구한다 — 메서드 집합 규칙은 그대로이고, **받는 자리를 포인터로 옮긴 것**이다.

### 6. `go 1.18`·`1.26` 은 막히고 `go 1.27` 은 `[2 4] [go! rust!]` · 가른 것은 `go.mod` 의 한 줄이다

**출력**

```text
===== 소스: t37method.go =====
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
===== 명령: n=0; for v in 1.18 1.26 1.27; do printf "module ex\n\ngo $v\n" > go.mod; if go build -trimpath -o prog . 2>err.txt; then echo "[go $v] 빌드 exit=0 · 실행: $(./prog | tr "\n" " ")"; else n=$((n+1)); echo "[go $v] 빌드 exit=1 · $(grep -v "^#" err.txt)"; fi; done; echo "빌드가 막힌 판 $n / 3" =====
[go 1.18] 빌드 exit=1 · ./t37method.go:8:18: generic method requires go1.27 or later (-lang was set to go1.18; check go.mod)
[go 1.26] 빌드 exit=1 · ./t37method.go:8:18: generic method requires go1.27 or later (-lang was set to go1.26; check go.mod)
[go 1.27] 빌드 exit=0 · 실행: [2 4] [go! rust!] 
빌드가 막힌 판 2 / 3
(exit 0)
```

```text
===== 명령: sed -n "8764,8784p;8827,8832p;8842,8857p" "$(go env GOROOT)/doc/go_spec.html" | sed -e "s/<[^>]*>//g" | awk NF =====
Go 1.18
The 1.18 release adds polymorphic functions and types ("generics") to the language.
Specifically:
The set of operators and punctuation includes the new token ~.
Function and type declarations may declare type parameters.
Interface types may embed arbitrary types (not just type names of interfaces)
as well as union and ~T type elements.
The set of predeclared types includes the new types
any and comparable.
Go 1.23
A "for" statement with "range" clause accepts an iterator
function as range expression.
Go 1.27
Function type inference applies in all
assignment contexts involving functions.
A method declaration may declare
type parameters.
A key in a struct composite literal may
be any valid field selector for the struct type,
not just a (top-level) field name of the struct.
(exit 0)
```

**왜 그런가**

- ★★★ **`generic method requires go1.27 or later (-lang was set to go1.26; check go.mod)`** — 컴파일러는 세 판 모두 **같은 1.27.1** 이다. 갈라 놓은 것은 **`go` 지시자**다.
- ★★★ 명세 판 부록 `Go 1.27` — 「**A method declaration may declare type parameters.**」 「메서드에는 타입 파라미터를 못 단다」는 **1.26 까지의 사실**이 됐다.
- ★ 한 메서드가 `int` 와 `string` 두 타입으로 불렸고 `T` 는 **인자에서 추론됐다.**

### 7. `interface method must have no type parameters` · `wrong type for method Map` — 못 만족시킨다

**출력**

```text
===== 소스: t37methodif.go =====
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
===== 명령: go build -trimpath -gcflags=-e -o prog . =====
# ex
./t37methodif.go:18:5: interface method must have no type parameters
./t37methodif.go:18:26: undefined: T
./t37methodif.go:21:16: cannot use Bag{} (value of slice type Bag) as Mapper value in variable declaration: Bag does not implement Mapper (wrong type for method Map)
		have Map[T any](func(string) T) []T
		want Map(func(string) int) []int
(exit 1)
```

**왜 그런가**

- ★★★ **인터페이스 메서드는 여전히 타입 파라미터를 못 가진다**(명세 — 「Interface methods cannot declare type parameters」).
- ★★★ **`have Map[T any](func(string) T) []T` · `want Map(func(string) int) []int`** — 제네릭 메서드는 **`T=int` 로 고정한 메서드로 쳐 주지 않는다.** 그래서 1.27 의 제네릭 메서드는 **구체 타입에 직접 부르는 자리**에서만 쓴다.

### 8. 본문 4 벌 · 사전 6 개 — `int`·`MyInt` 와 `*A`·`*B` 가 합쳐진다 · `FirstAny` 는 1 벌

**출력**

```text
===== 소스: t37shape.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog && go tool nm -sort name prog > syms.txt && awk "/ main\.(First|FirstAny|\.dict\.First)(\[|$)/{print \$2, \$3}" syms.txt && echo "First 의 본문(T) $(awk "\$2==\"T\" && \$3 ~ /^main\.First\[/" syms.txt | wc -l) 벌 · 사전(R) $(awk "\$3 ~ /^main\.\.dict\.First\[/" syms.txt | wc -l) 개 · 타입 인자 6 가지" =====
1 2 3 s
&{1} &{b}
1 s
R main..dict.First[*main.A]
R main..dict.First[*main.B]
R main..dict.First[float64]
R main..dict.First[int]
R main..dict.First[main.MyInt]
R main..dict.First[string]
T main.FirstAny
T main.First[go.shape.*uint8]
T main.First[go.shape.float64]
T main.First[go.shape.int]
T main.First[go.shape.string]
First 의 본문(T) 4 벌 · 사전(R) 6 개 · 타입 인자 6 가지
(exit 0)
```

**왜 그런가**

- ★★★ **`First[go.shape.int]`** 한 벌을 `int`·`MyInt` 가, **`First[go.shape.*uint8]`** 한 벌을 `*A`·`*B` 가 나눠 쓴다 — 기계어 **모양(shape)** 이 같으면 한 벌이다.
- ★★★ **사전 `main..dict.First[…]` 는 타입 인자마다 하나(6 개)** — 한 벌의 본문이 「지금 무슨 타입인가」를 이것으로 안다.
- ★ `//go:noinline` 은 **인라인되어 심볼이 사라지는 것**을 막으려고 달았다 — 이 창은 인라인된 벌을 못 센다.

### 9. 「may only be used as type constraints」

- ★★★ 명세 General interfaces — 「**Interfaces that are not basic may only be used as type constraints, or as elements of other interfaces used as constraints. They cannot be the types of values or variables, or components of other, non-interface types.**」
- ★ 타입 목록은 「**어떤 타입이 들어올 수 있나**」의 규칙이지 **값의 모양**(메서드 표)이 아니다 — 값으로 들고 다닐 방법이 없다(4번 `p3`).

### 10. `any` 는 실행 시점, `comparable` 은 컴파일 시점 · 1.20 판 격자는 인터페이스 타입 인자가 `comparable` 을 만족하나를 갈랐다

- ★★★ [22번 주제](../22-type-assertion-any-and-comparable/) (5)·(6)절 — 같은 실수가 `any` 로는 `panic: runtime error: comparing uncomparable type []int`, `comparable` 로는 `does not satisfy comparable`(빌드 실패). 이 편 1번의 `p1` 이 그 성질을 **`==` 밖으로 넓힌 것**이다.
- ★★ 같은 편 (7)절 — **`go 1.19` 에서는 막히고 `go 1.20` 에서는 통과**(명세의 `[Go 1.20]` 예외). 이 편 6번과 **같은 레버**(`go.mod` 의 `go` 줄)다.

### 11. 구현의 선택이다 · 둘 다 「컴파일러가 정한 수」, 다른 것은 합치는 기준 · 답하지 않았다

- ★★★ **명세는 벌 수를 말하지 않는다** — 의미(타입 집합·추론·대입)만 정한다. `go.shape.*` 와 사전은 **gc 의 구현**이다.
- ★★ [Rust 31번](../../../rust/syntax/31-generics-trait-bounds-where-and-monomorphization/) (8)절 — **타입마다 한 벌**(`opt-level=0` 에서 3 벌)이 기본이고 최적화가 켜지면 **몸이 같은 것을 합쳤다**. Go 는 **처음부터 모양으로 합치고 사전을 붙인다.** 같은 것 — **둘 다 언어가 아니라 컴파일러가 정한 수**라는 것.
- ★★★ 「제네릭이 느리다」 — **이 문서는 재지 않았다.** 센 것은 벌 수뿐이다(규칙 5).

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 로 **★고칠 것 0** |
| ★★★ 판단 격자 (`t37grid`) | 여섯 파일 × `-gcflags=-e` · `// pN` 줄 번호로 맞춤 | 캡처마다 | **`5 / 8`** |
| ★★ 통과 칸 실행 (`t37anyrun`) | `recover` 로 받음 | 캡처마다 | 넷 다 `interface conversion` |
| ★★ 제약 에러 (`t37constraint`·`t37fix`) | 빌드 · 실행 | 캡처마다 | 위 블록 |
| ★★★ 제네릭 메서드 (`t37method`·`t37methodif`) | `go.mod` 세 판 · 인터페이스 탐침 | 캡처마다 | **`2 / 3`** 막힘 · 인터페이스 불가 |
| ★★ 벌 수 (`t37shape`) | `go tool nm -sort name` | 캡처마다 | **본문 4 · 사전 6** |

**구현·환경에 달린 항목**

| 항목 | 무엇에 달렸나 |
|---|---|
| 벌 수·`go.shape.*` 이름 | **gc 의 구현** — 판이 오르면 바뀔 수 있다 |
| 에러 문구 | **이 판 컴파일러** — 근거는 막힘/통과와 `파일:줄:칸` |
| 제네릭 메서드 | **명세 1.27** · `go.mod` 의 `go` 줄 |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다.

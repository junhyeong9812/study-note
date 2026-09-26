# go/syntax/37 — 제네릭: 타입 파라미터와 제약 인터페이스(1.18) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Go 명세](https://go.dev/ref/spec)의 Type parameter declarations · Type constraints · General interfaces · Method declarations · 판 부록(Language versions).
> 명세는 웹이 아니라 **이 툴체인의 `$(go env GOROOT)/doc/go_spec.html`**(`Language version go1.27`)에서 직접 떴다. 제네릭 구현 설계 문서(GC shape stenciling)는 **안 열었다** — 그 층은 **심볼 표로만** 봤다((6)절).\
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> ★★ **버전** — 타입 파라미터·`~`·`any`·`comparable` 이 **1.18** · 비교 가능한 인터페이스가 `comparable` 을 만족하는 예외가 **1.20**([22번 주제](../22-type-assertion-any-and-comparable/) (7)절) · ★★★ **메서드가 자기 타입 파라미터를 선언하는 「제네릭 메서드」가 1.27**((4)절 — 명세 판 부록과 `go.mod` 판 격자로 뗐다).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체는 넷째 창이다** — 「**판단 격자** — 같은 기능을 `any` · 인터페이스 · 타입 파라미터 세 판으로 쓰고, 똑같은 탐침 넷을 컴파일러에 던져 **막힘/통과**를 찍는 로그」.
제네릭을 쓸지 말지는 취향이 아니라 **「어떤 잘못이 컴파일에서 막히나 · 타입이 호출부까지 흘러나오나」** 의 차이로 갈린다.
마지막 줄 「**인터페이스 판과 제네릭 판이 갈린 칸 5 / 8**」 — 최댓값에서 **3 / 4**, 이어 쓰기에서 **2 / 4**, 그리고 **갈린 방향이 다르다**((1)절).
★★ 짝이 되는 창은 「**링크된 바이너리의 심볼 표**」 — 타입 인자 6 가지가 **본문 4 벌 + 사전 6 개**가 됐다((6)절).

★★★ **이 주제의 경계** — `comparable` 제약과 「`any` 를 `==` 하면 런타임 패닉 대 `comparable` 은 컴파일 에러」, 그리고 1.20 의 「비교 가능한 인터페이스」 판 격자는
[22번 주제](../22-type-assertion-any-and-comparable/) (5)·(6)·(7)절이 정본이다 — **여기서 다시 재지 않는다.**
포인터 리시버와 메서드 집합은 [19번 주제](../19-method-sets-value-vs-pointer-receiver/) (1)절이 정본이고, 여기서는 그 규칙이 **제약에서 다시 나오는 자리**((3)절)만 본다.
표준 라이브러리의 제네릭 함수(`slices`·`maps`·`cmp`)는 [38번 주제](../38-slices-maps-and-cmp/), 제네릭 반복자(`iter.Seq[V]`)는 [39번 주제](../39-iter-and-custom-iterators/)다 — **37 → 38 → 39 는 한 사슬이다.**

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | 타입 파라미터·제약·타입 집합의 **의미** · 「타입 집합 인터페이스는 **제약으로만** 쓴다」 · ★★★ **「메서드가 타입 파라미터를 선언할 수 있다 [Go 1.27]」** · 「인터페이스 메서드는 타입 파라미터를 선언할 수 없다」 |
| **구현(gc)** | 컴파일러가 실제로 한 것 | ★★★ **GC shape stenciling + 사전(dictionary)** — 몇 벌을 찍나는 **명세에 없다.** `go.shape.int`·`main..dict.First[int]` 같은 심볼 이름이 그 흔적이다 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 격자의 막힘/통과 · 에러 문구 · 벌 수 `4` · 사전 수 `6` |

★★★ **선을 긋는다** — 「`MyInt` 는 `int` 제약을 못 통과하고 `~int` 는 통과한다」는 **명세**다(타입 집합의 정의).
「`int` 와 `MyInt` 가 **한 벌의 기계어**를 나눠 쓴다」는 **gc 의 구현**이다 — 명세는 벌 수를 말하지 않는다((6)절).
★ 「제네릭이 느리다」·「인터페이스가 느리다」는 **이 문서가 재지 않았다** — 벌 수는 셌지만 **시간은 안 쟀다.**

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
```

★ 명세의 판 부록 — 이 문서가 기대는 세 판만 떴다:

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

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ **격자의 막힘/통과 · `갈린 칸 5 / 8`** | 컴파일러의 판정 — 캡처마다 같다 |
| 안 흔들린다 | ★★ **에러 문구 · `파일:줄:칸`** | 정적 판정 |
| **판을 탄다** | ★★ **심볼 이름·벌 수**(`go.shape.*uint8` · `4 벌`) | ★ **구현이다** — 인라인을 막으려고 `//go:noinline` 을 달았다. 판이 오르면 합치는 방식이 바뀔 수 있다 |
| 안 흔들린다 | `recover` 가 받은 `interface conversion` 문구 · 종료 코드 | |

★ 정규화 규칙은 **기본 넷**만 썼다. nm 의 **주소 열은 캡처가 버렸다**(`awk` 로 종류·이름만 남겼다 — 배너에 적혀 있다).

## 한눈에 — 쉽게 말하면

**제네릭은 「치수가 비어 있는 설계도」다.** 「이 틀에 **무엇이든 한 가지**를 넣으면, 나오는 것도 **그 한 가지**다」.
인터페이스는 「**이 구멍에 맞는 모양이면 무엇이든 받는 접수창구**」다 — 받는 순간 **원래 무엇이었는지는 창구 뒤로 사라진다.**
`any` 는 「**아무거나 받는 상자**」 — 꺼낼 때 **라벨을 직접 확인해야**(단언) 하고, 라벨이 틀리면 **그 자리에서 터진다.**

| 비유 | 실체 |
|---|---|
| 치수가 빈 설계도 | ★★★ **타입 파라미터** `[T cmp.Ordered]` — 넣은 타입이 **반환까지 흘러나온다**((1)절 `p2=통과`) |
| 모양만 맞으면 받는 창구 | **인터페이스 인자** — 받는 순간 `Ord` 가 된다. 원래 타입을 되찾으려면 **단언**((1)절 `need type assertion`) |
| 아무거나 받는 상자 | **`any` 인자** — 틀린 것을 넣어도 **컴파일은 통과**, 실행에서 `interface conversion` 패닉((2)절) |
| 「int 계열이면 된다」 는 규격 | ★★ **`~int`** — 기반 타입이 `int` 인 것 전부. 그냥 `int` 는 **정확히 `int` 하나**((3)절) |
| 설계도를 치수별로 **몇 장 복사하나** | ★★ **구현의 선택** — gc 는 「모양(shape)」이 같으면 **한 장**을 나눠 쓰고 **메모(사전)** 를 따로 붙인다((6)절) |

```text
   ★★★ 같은 「최댓값」을 세 판으로 쓰면 — (1)절 격자의 요약

                       p1 틀린 원소    p2 반환을 원래 타입에    p3 가진 []int 를    p4 두 타입 섞기
                       (bool)          바로 담기                 그대로 넘기기
   any    MaxAny(...any)   통과 ✗          막힘 (단언 필요)          막힘                통과 ✗ → 실행에서 터짐
   iface  MaxI(...Ord)     막힘 ✓          막힘 (단언 필요)          막힘                통과 ✗ → 실행에서 터짐
   gen    Max[T](...T)     막힘 ✓          통과 ✓                    통과 ✓              막힘 ✓

   ★ 인터페이스 판과 제네릭 판이 갈린 칸 : 최댓값 3 / 4 — 셋 다 제네릭 쪽이 옳다
   ★ 「이어 쓰기」(String() 만 부른다)는 2 / 4 — 그중 p4 는 인터페이스 쪽이 옳다(섞어 받는 게 목적이라서)
```

> **타입 파라미터(type parameter)** — 함수·타입 선언에 붙는 `[T 제약]` 자리. 부를 때 **타입 인자**로 채워진다.\
> 예: `Max[T cmp.Ordered](xs ...T) T` 를 `Max(3, 9)` 로 부르면 `T` 가 `int` 로 **추론**된다.

> **제약(constraint)** — 타입 파라미터에 걸리는 인터페이스. **메서드**뿐 아니라 **타입 목록**(`~int \| ~float64`)도 담을 수 있다.\
> 예: `cmp.Ordered` 는 `<` 가 되는 타입들의 **목록**이다.

> **타입 집합(type set)** — 인터페이스가 허용하는 **타입들의 모임**. 메서드만 적은 인터페이스는 「그 메서드를 가진 모든 타입」, `~int` 는 「기반 타입이 `int` 인 모든 타입」이다.

- ★★ [20번 주제](../20-interface-declaration-and-implicit-implementation/) — 인터페이스는 **암묵 구현**이다. 제약의 메서드 부분도 똑같이 **모양으로** 맞춘다(TS 제약도 구조적이다 — [TS 20번](../../../ts/syntax/20-generic-constraints-and-defaults/)).
- ★★ [22번 주제](../22-type-assertion-any-and-comparable/) (6)절 — `comparable` 은 **컴파일에서** 막는다. 이 문서 (1)절은 그 성질을 「**`any` 대 제약**」 전체로 넓힌 것이다.

## 이 주제가 답하려는 질문

1. **제네릭이 필요한 자리와 인터페이스로 충분한 자리는 무엇으로 가르나** — 컴파일러가 막아 주는 잘못과, 호출부까지 흘러나오는 타입으로.
2. **제약 인터페이스는 무엇을 적을 수 있고, 어디에 못 쓰나** — `~`·타입 목록·메서드, 그리고 포인터 리시버.
3. **제네릭은 실제로 몇 벌이 되나** — 그리고 그것은 누가 정하나(명세인가 구현인가).

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **판단 격자 — 세 판 × 탐침 넷 × 막힘/통과** | **어느 잘못이 컴파일에서 막히나** · 타입이 흘러나오나 | ★ 본체 창 — 스크립트가 `// pN` 주석의 줄 번호와 에러 줄을 맞춰 센다 |
| ★★ **컴파일러 진단 전문** | 제약이 **왜** 거부했나(`possibly missing ~` · `pointer receiver`) | (3)절 |
| ★★ **`recover` 로 받은 패닉 값** | 컴파일을 **통과한** 칸이 실행에서 무엇이 되나 | (2)절 |
| ★★★ **`go.mod` 판 격자** | 제네릭 메서드가 **어느 판부터** 되나 | [28번 주제](../28-goroutines-go-statement-cost-and-termination/) (4)절 방식 |
| ★★ **`go tool nm` 심볼 표** | 타입 인자마다 **몇 벌**이 생기나 | ★★ **제5의 상태 — 「같은 질문을 다른 창으로」.** 벌 수는 **명세가 답하지 않는 질문**이라 링크된 바이너리에 물었다. [Rust 31번](../../../rust/syntax/31-generics-trait-bounds-where-and-monomorphization/)과 같은 창이다 |
| **부적용 — 시간** | ★★★ **「제네릭이 느리다/빠르다」는 안 쟀다** — 벌 수는 셌지만 속도는 이 주제의 질문이 아니다 | 규칙 5 |

★ 심볼 표 창이 **못 보는 것** — 인라인되어 **심볼이 사라진 벌**은 안 세어진다. 그래서 `//go:noinline` 을 달았다(Rust 31번의 `#[inline(never)]` 와 같은 이유).

### (1) ★★★ 판단 격자 — 같은 기능 세 판에 똑같은 탐침 넷

**언제 쓰나** — 「이거 제네릭으로 짜야 하나, 인터페이스면 되나」를 물을 때.

**최댓값**(값을 비교하고, **그 값을 돌려준다**) 세 판:

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

**이어 쓰기**(각 원소의 `String()` 만 부르고, **문자열을 돌려준다**) 세 판:

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

여섯 파일을 각각 `-gcflags=-e` 로 빌드하고, **에러가 `// pN` 줄에 떨어졌나**를 스크립트가 셌다:

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

그림 해설 (한 단계씩):

- ★★★ **p1(틀린 원소 — `bool`·`int`)** — `any` 판만 **통과**했다. 인터페이스·제네릭은 **둘 다 컴파일에서 막았다.** 여기서는 **둘이 갈리지 않는다** — 「틀린 타입을 막는 것」은 제네릭만의 장점이 아니다.
- ★★★ **p2(반환을 원래 타입 변수에 담기)** — **최댓값에서 갈린다.** 인터페이스 판은 `Ord` 를 돌려주므로 `var got N = MaxI(…)` 가 막힌다. 컴파일러가 이유까지 말한다:

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

  ★★★ 「**need type assertion**」 — 인터페이스로 받으면 **나올 때 원래 타입을 잃는다.** 제네릭은 `T` 를 돌려주므로 `int` 가 그대로 나온다.
  **이어 쓰기에서는 안 갈린다** — 반환이 `string` 이라 **잃을 타입이 처음부터 없다.**
- ★★ **p3(가진 `[]int`·`[]Name` 을 그대로 넘기기)** — `any`·인터페이스 판은 **둘 다 막혔다**(`cannot use ns (variable of type []N) as []Ord value`). **`[]N` 은 `[]Ord` 로 바뀌지 않는다** — 원소마다 모양이 달라서다. 제네릭만 **그대로** 받는다.
- ★★★ **p4(서로 다른 두 타입 섞기)** — **방향이 반대로 갈린다.**
  최댓값에서 `Max(i, f)` 가 막힌 것은 **옳다**(`int` 와 `float64` 의 최댓값은 뜻이 없다):

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

  이어 쓰기에서 `JoinG(Name("kim"), Code(7))` 가 막힌 것은 **손해다** — `T` 는 **한 번에 한 타입**이라 서로 다른 `Stringer` 를 **섞어 받을 수 없다.** 인터페이스 판은 받는다.
- ★★★ **마지막 줄 `갈린 칸 5 / 8`** — 최댓값 **3 / 4**(p2·p3·p4, 셋 다 제네릭이 옳다), 이어 쓰기 **2 / 4**(p3 은 제네릭이 편하고 p4 는 **인터페이스가 옳다**).

```text
   ★★★ 이 격자에서 읽는 판단 규칙

   「넣은 타입이 나와야 하나?」 ── 예 ──▶ 타입 파라미터        (최댓값 p2 — 단언이 사라진다)
            │
            아니오
            │
   「한 번에 여러 타입을 섞어 받나?」 ── 예 ──▶ 인터페이스    (이어 쓰기 p4 — T 는 한 가지뿐)
            │
            아니오
            │
   「연산자(< == +)가 필요한가?」 ── 예 ──▶ 타입 파라미터 + 타입 목록 제약 (cmp.Ordered)
            │
            아니오 ──▶ 인터페이스로 충분하다 — 메서드만 부르고, 반환이 고정 타입이면
```

비용 — **안 쟀다.** 이 격자는 「어느 잘못을 **언제** 알게 되나」만 본다.

### (2) ★★ 컴파일을 통과한 칸은 실행에서 무엇이 되나

(1)절에서 **통과**한 칸 중 옳지 않은 것 — `any` 판의 p1·p4, 인터페이스 판의 p4 — 을 실제로 돌렸다:

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

- ★★★ **넷 다 `interface conversion` 패닉**이다. `any` 판은 **함수 안의 `x.(int)`** 에서, 인터페이스 판은 **`N.Less` 안의 `b.(N)`** 에서 터졌다.
  ★ 인터페이스 판의 p4 는 **컴파일러가 통과시킨 것이 맞다** — `N` 과 `F` 는 둘 다 `Ord` 를 **구현한다.** 틀린 것은 「`Less` 의 인자가 **같은 타입**이어야 한다」는 **숨은 약속**인데, `Less(Ord) bool` 시그니처는 그것을 **말할 방법이 없다.**
  ★★ 제네릭의 `[T cmp.Ordered](xs ...T)` 는 그 약속을 **시그니처에 적는다** — 「전부 **같은** `T`」.
- ★ `MaxAny(3, 9)` 는 옳게 돌지만 결과가 **`any`** 다 — `(int)` 가 보여 주는 것은 **동적 타입**이고, 정적으로는 여전히 단언이 필요하다(p2).
- ★★ 이것이 [22번 주제](../22-type-assertion-any-and-comparable/) (5)·(6)절의 「**런타임 패닉 대 컴파일 에러**」를 `==` 밖으로 넓힌 모양이다.

비용 — 없다.

### (3) ★★ 제약 인터페이스 — `~`·값으로 못 쓰는 인터페이스·추론·포인터 리시버

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

그림 해설 (한 단계씩):

- ★★★ **p1 — `MyInt does not satisfy int (possibly missing ~ for int in int)`.** 제약 `int` 의 타입 집합은 **정확히 `int` 하나**다. `MyInt` 는 기반 타입이 `int` 여도 **다른 타입**이다. 컴파일러가 **`~` 를 빠뜨렸나** 하고 되묻는다.
  ★★ **p2 는 통과** — `~int` 는 「**기반 타입이 `int` 인 모든 타입**」이다.
- ★★★ **p3 — `cannot use type Number outside a type constraint: interface contains type constraints`.** 타입 목록을 담은 인터페이스는 **값의 타입이 될 수 없다.** 명세 — 「Interfaces that are not basic **may only be used as type constraints** … They cannot be the types of values or variables」.
- ★★ **p4 — `in call to Zero, cannot infer T`.** 인자가 없으면 **추론할 재료가 없다** — `Zero[int]()` 처럼 **명시**해야 한다.
- ★★★ **p5 — `T (type Box) does not satisfy Setter (method Set has pointer receiver)`.** [19번 주제](../19-method-sets-value-vs-pointer-receiver/) (1)절의 「**값 `Box` 의 메서드 집합에 `*Box` 의 메서드는 없다**」가 **제약에서 그대로** 나왔다.

고친 판:

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

- ★★ **`SumTilde: 3 (main.MyInt)`** — `~int` 는 받기만 하는 게 아니라 **돌려줄 때도 `MyInt`** 다. `int` 로 부르면 `int`.
- ★★★ **`Fill[Box](2): [{v:v} {v:v}]`** — 관용구 `[T any, PT interface{ *T; Set(string) }]` 이다.
  `PT` 의 타입 집합은 「**`*T` 하나이면서 `Set` 을 가진 것**」 — 그래서 `PT(&xs[i])` 로 **주소를 얻어 포인터 메서드를 부를 수 있다.**
  ★ 부르는 쪽은 `Fill[Box]` 만 적는다 — `PT` 는 `*Box` 로 **추론된다.**

```text
   ★★ 제약이 담을 수 있는 세 가지와, 어디에 쓸 수 있나

   interface { String() string }        메서드만     → 기본 인터페이스 : 값의 타입으로도 · 제약으로도
   interface { ~int | ~float64 }        타입 목록    ┐
   interface { *T; Set(string) }        목록+메서드  ┘→ 일반 인터페이스 : 제약으로만 (p3)

   int      의 타입 집합 = { int }                  → MyInt ✗ (p1)
   ~int     의 타입 집합 = { int, MyInt, … }         → MyInt ✓ (p2) · 돌려줄 때도 MyInt
```

비용 — 없다. 전부 컴파일 시점이다.

### (4) ★★★ 제네릭 메서드 — 1.27 에서 열렸다

「**메서드에는 타입 파라미터를 못 단다**」는 오랫동안 Go 제네릭의 가장 유명한 제약이었다. **이 판의 명세는 다르게 말한다** — 판 부록(머리말 블록) 「**A method declaration may declare type parameters.**」가 `Go 1.27` 아래에 있다.

같은 소스를 `go.mod` 의 `go` 줄만 바꿔 세 판으로:

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

- ★★★ **`go 1.18`·`1.26` 에서 막히고 `go 1.27` 에서 돈다** — `generic method requires go1.27 or later (-lang was set to go1.26; check go.mod)`. 컴파일러는 같은 1.27.1 이다. **갈라 놓은 것은 `go` 한 줄**이다([13번 주제](../13-closures-variable-capture-and-loop-variable-change/)의 루프 변수와 같은 레버).
- ★★ `b.Map(func(s string) int …)` 과 `b.Map(func(s string) string …)` — **한 메서드가 두 타입으로** 불렸고 `T` 는 인자에서 **추론됐다.**

그러면 이제 제약이 없나 — 인터페이스와 만나면:

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

- ★★★ **p1 — `interface method must have no type parameters`.** 인터페이스에는 **여전히 못 적는다**(명세 — 「Interface methods cannot declare type parameters」). `undefined: T` 는 그 뒤따름이다.
- ★★★ **p2 — `Bag does not implement Mapper (wrong type for method Map)` · `have Map[T any](func(string) T) []T` · `want Map(func(string) int) []int`.**
  제네릭 메서드는 **`T` 를 `int` 로 고정한 메서드**로 쳐 주지 않는다 — **인터페이스를 만족시키는 데 쓸 수 없다.**
- ★★ 그러니 1.27 의 제네릭 메서드는 「**구체 타입에 직접 부르는 도우미**」 자리다. **동적 디스패치(인터페이스 경유)** 로는 못 부른다.

비용 — 없다.

### (5) ★ `comparable` 과 1.20 — 인용만

- ★★★ [22번 주제](../22-type-assertion-any-and-comparable/) (6)절 — `eq[T comparable]` 에 슬라이스·맵·함수를 넣으면 **일곱 줄 전부 `does not satisfy comparable`**(컴파일). 같은 실수를 `any` 로 받으면 **런타임 패닉**((5)절).
- ★★ 같은 편 (7)절 — `comparable` 제약에 **`any` 같은 인터페이스**를 넣는 것은 **`go 1.19` 에서 막히고 `go 1.20` 에서 통과**한다(명세의 `[Go 1.20]` 예외). **여기서는 다시 재지 않았다.**

### (6) ★★ 몇 벌이 되나 — 심볼 표로 센다

**언제 쓰나** — 「제네릭을 쓰면 바이너리가 타입마다 불어나나」를 물을 때. **명세는 이 질문에 답하지 않는다** — 그래서 링크된 바이너리에 물었다.

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

그림 해설 (한 단계씩):

- ★★★ **타입 인자 6 가지(`int`·`MyInt`·`float64`·`string`·`*A`·`*B`)가 본문(T) 4 벌이 됐다.**
  **`int` 와 `MyInt` 는 `go.shape.int` 한 벌**을, **`*A` 와 `*B` 는 `go.shape.*uint8` 한 벌**을 나눠 쓴다. 기계어 입장에서 **모양(shape)이 같으면 한 벌**이다.
- ★★★ **사전(R) 은 6 개** — 타입 인자마다 하나씩 `main..dict.First[…]` 가 생겼다. 한 벌의 본문이 **「지금 나는 `*A` 인가 `*B` 인가」** 를 이 사전으로 안다.
- ★★ **`FirstAny` 는 한 벌** — 인터페이스·`any` 는 처음부터 **한 벌 + 실행 중 동적 타입**이다.

```text
   ★★ 같은 질문 「몇 벌?」 — 두 언어, 두 구현

   Rust 31번 (단형화)                       Go 37번 (GC shape stenciling + 사전)
   total::<Sq>      ┐                       First[go.shape.int]      ← int · MyInt
   total::<Circle>  ├ 타입마다 한 벌         First[go.shape.float64]  ← float64
   total::<Rect>    ┘ (opt-level=0)         First[go.shape.string]   ← string
                                            First[go.shape.*uint8]   ← *A · *B  ★ 포인터는 한 벌
   Sq 와 몸이 같은 Tile 은                   + 사전 6 개 (타입 인자마다)
   opt-level=2 부터 합쳐졌다(함수 병합)
   ★ 둘 다 「언어」가 아니라 「컴파일러」가 정한 수다 — 명세는 의미만 말한다
```

- ★★★ [Rust 31번](../../../rust/syntax/31-generics-trait-bounds-where-and-monomorphization/) (8)절은 **타입마다 한 벌**(`opt-level=0` 에서 3 벌)을 셌고, 최적화가 켜지면 **몸이 같은 것을 합쳤다**(3 → 2). Go 는 **최적화 전부터 모양으로 합친다** — 대신 **사전**이 붙는다.
- ★ **판을 탄다** — 심볼 이름 `go.shape.*uint8` 과 벌 수는 **gc 의 현재 선택**이다. 근거로 쓰는 것은 「**모양이 같으면 합칠 수 있다 — 벌 수는 언어가 안 정한다**」 뿐이다.

비용 — ★★★ **안 쟀다.** 사전을 거치는 호출이 단형화보다 느린지는 **이 문서의 질문이 아니다**(규칙 5).

## 문법 — 형태와 규칙

### 형태

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

규칙 불릿.

- ★★ 타입 파라미터 목록 `[T 제약, …]` 은 **함수 이름·타입 이름 뒤**, 1.27 부터는 **메서드 이름 뒤**에도 온다.
- ★★ **부를 때는 대개 추론된다** — 인자가 없으면 `Zero[int]()` 처럼 명시한다.
- ★★★ **`~T` 는 기반 타입이 `T` 인 모든 타입**, 그냥 `T` 는 **`T` 하나.** 공개 라이브러리 제약은 거의 언제나 `~` 를 쓴다(`cmp.Ordered` 가 전부 `~` 다 — [38번 주제](../38-slices-maps-and-cmp/)).
- ★★★ **타입 목록이 든 인터페이스는 제약으로만** — 변수·필드·반환 타입이 될 수 없다.
- ★★ 포인터 리시버 메서드를 제약으로 부르려면 **`[T any, PT interface{ *T; M() }]`**.
- ★★★ **인터페이스 메서드는 타입 파라미터를 못 가진다** · 제네릭 메서드(1.27)는 **인터페이스를 만족시키지 못한다.**

### 금지 사례 — 컴파일러가 거부하는 것

| 쓴 꼴 | 진단 | 어디서 |
|---|---|---|
| `SumInt[T int]` 에 `[]MyInt` | `MyInt does not satisfy int (possibly missing ~ for int in int)` | (3)절 p1 |
| `var n Number`(`Number` = `~int \| ~float64`) | `cannot use type Number outside a type constraint` | (3)절 p3 |
| `Zero()` | `in call to Zero, cannot infer T` | (3)절 p4 |
| 값 `Box` 를 포인터 리시버 제약에 | `method Set has pointer receiver` | (3)절 p5 |
| `go 1.26` 모듈의 제네릭 메서드 | `generic method requires go1.27 or later` | (4)절 |
| 인터페이스 메서드에 `[T any]` | `interface method must have no type parameters` | (4)절 |
| `Max(i, f)`(`int`·`float64`) | `type float64 of f does not match inferred type int for T` | (1)절 |

## 어디서 틀리나

### 1. ★★★ 「타입을 막아 주니까 제네릭을 쓴다」

- (1)절 p1 — **인터페이스도 똑같이 막는다.** 제네릭만의 것은 **p2(타입이 흘러나온다)** 와 **p3(`[]T` 를 그대로 받는다)** 다.

### 2. ★★★ 「제네릭이 인터페이스의 상위 호환이다」

- (1)절 p4 — **이어 쓰기에서 제네릭이 졌다.** `T` 는 **한 번에 한 타입**이라 서로 다른 `Stringer` 를 섞어 못 받는다.

### 3. ★★★ 「`type MyInt int` 는 `int` 제약을 통과한다」

- (3)절 p1 — **안 된다.** `~int` 라야 한다.

### 4. ★★★ 「메서드에는 타입 파라미터를 못 단다」

- (4)절 — **1.27 부터 된다**(`go.mod` 가 `go 1.27` 이상일 때). ★ 다만 **인터페이스로는 못 부른다.** 1.26 이하 모듈에서는 여전히 막힌다.

### 5. ★★ 「인터페이스 판도 컴파일이 통과했으니 안전하다」

- (2)절 — `MaxI(N(3), F(9.5))` 는 통과하고 **실행에서 터졌다.** `Less(Ord) bool` 은 「**같은 타입끼리**」를 말할 수 없다.

### 6. ★★ 「제네릭은 타입마다 코드가 복사된다」

- (6)절 — gc 는 **모양이 같으면 한 벌**(`int`·`MyInt` · `*A`·`*B`) + **사전**. 「타입마다 한 벌」은 Rust 의 `opt-level=0` 관찰이지 **Go 의 것이 아니다** — 그리고 **둘 다 명세의 보장이 아니다.**

### 7. ★ 「제네릭이 느리다」

- **이 문서는 재지 않았다.** 벌 수를 셌을 뿐이다.

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| 타입 파라미터·`~`·타입 집합·추론의 의미 | **명세**(1.18) | 판 부록 · (3)절 |
| ★★★ **타입 목록 인터페이스는 제약으로만** | **명세** | (3)절 p3 |
| ★★★ **제네릭 메서드** | **명세 [Go 1.27]** · `go.mod` 판이 가른다 | (4)절 |
| 인터페이스 메서드는 타입 파라미터 불가 | **명세** | (4)절 p1 |
| 제네릭 메서드가 인터페이스를 못 만족시킴 | **명세의 귀결 · 이 판 컴파일러가 확인** | (4)절 p2 |
| ★★★ **GC shape stenciling + 사전 · `go.shape.*` 이름 · 4 벌** | **구현(gc)** — 명세에 없다 | (6)절 |
| 격자의 막힘/통과 | **명세의 귀결**(대입 가능성·타입 집합) — 문구는 이 판의 것 | (1)절 |
| `interface conversion` 패닉 문구 | **런타임 구현** | (2)절 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 넣은 타입이 그대로 나와야 한다(최댓값·첫 원소·컨테이너) | ★★★ **타입 파라미터** | (1)절 p2 — 단언이 사라진다 |
| `<`·`+`·`==` 가 필요하다 | **타입 파라미터 + `cmp.Ordered`·`comparable`·`~int \| …`** | 인터페이스는 연산자를 못 적는다 |
| 메서드만 부르고 반환이 고정 타입 | ★★ **인터페이스** | (1)절 이어 쓰기 — p2 가 안 갈린다 |
| 서로 다른 타입을 한 번에 섞어 받는다 | ★★★ **인터페이스** | (1)절 p4 |
| 가진 `[]MyType` 을 그대로 넘긴다 | **타입 파라미터** | (1)절 p3 — `[]T` 는 `[]I` 로 안 바뀐다 |
| 구체 타입에 붙는 변환 도우미(`Map[T]`) | **제네릭 메서드(1.27)** — 인터페이스 경유가 필요 없을 때만 | (4)절 |
| 「무엇이든」 받아 로그만 찍는다 | `any` | 컴파일이 막아 줄 것이 없다 |

## 핵심 문장

- ★★★ **판단 격자 `갈린 칸 5 / 8`** — 제네릭만의 것은 **타입이 흘러나오는 것**(p2)과 **`[]T` 를 그대로 받는 것**(p3)이다. 틀린 타입을 막는 것(p1)은 인터페이스도 한다.
- ★★★ **섞어 받기(p4)는 인터페이스가 이긴다** — `T` 는 한 번에 한 타입이다.
- ★★★ **`int` 제약은 `MyInt` 를 거부한다(`possibly missing ~`)** — `~int` 라야 한다. 타입 목록 인터페이스는 **제약으로만** 쓴다.
- ★★ **포인터 리시버 메서드를 제약으로 부르려면 `PT interface{ *T; M() }`** — 19번의 메서드 집합이 제약에서 다시 나온다.
- ★★★ **제네릭 메서드는 1.27 에서 열렸다** — `go 1.26` 모듈에서는 막힌다. **인터페이스 메서드는 여전히 안 되고, 제네릭 메서드는 인터페이스를 못 만족시킨다.**
- ★★ **타입 인자 6 가지 → 본문 4 벌 + 사전 6 개** — `int`·`MyInt`, `*A`·`*B` 가 합쳐졌다. **벌 수는 구현이 정한다.** 시간은 안 쟀다.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 37번)
- [22번 주제](../22-type-assertion-any-and-comparable/)(`any`·`comparable`) — ★ 목록상 선행 · **`comparable` 과 1.20 판 격자의 정본**
- [19번 주제](../19-method-sets-value-vs-pointer-receiver/)(메서드 집합) — (3)절 p5 의 뿌리
- [20번 주제](../20-interface-declaration-and-implicit-implementation/)(암묵 구현) — 제약의 메서드 부분도 모양으로 맞춘다
- [13번 주제](../13-closures-variable-capture-and-loop-variable-change/)·[28번 주제](../28-goroutines-go-statement-cost-and-termination/) — `go.mod` 한 줄이 의미를 가르는 판 격자
- [38번 주제](../38-slices-maps-and-cmp/) — `cmp.Ordered`·`slices` 의 제네릭 함수 · [39번 주제](../39-iter-and-custom-iterators/) — `iter.Seq[V]`
- [Rust 31번](../../../rust/syntax/31-generics-trait-bounds-where-and-monomorphization/) — ★★ **단형화 벌 수의 대비** · [TS 20번](../../../ts/syntax/20-generic-constraints-and-defaults/) — 구조적 제약

## 용어 풀이

- **타입 파라미터** — `[T 제약]`. 부를 때 타입 인자로 채워진다.
- **타입 인자** — 타입 파라미터 자리에 들어가는 실제 타입. 대개 추론된다.
- **제약(constraint)** — 타입 파라미터가 받을 수 있는 타입 집합을 정하는 인터페이스.
- **타입 집합** — 인터페이스가 허용하는 타입들의 모임.
- **`~T`** — 기반 타입이 `T` 인 모든 타입.
- **기본 인터페이스 / 일반 인터페이스** — 메서드만 적은 것 / 타입 목록·`~` 가 든 것. 뒤엣것은 제약으로만 쓴다.
- **추론(inference)** — 인자의 타입으로 타입 인자를 채우는 것.
- **제네릭 메서드** — 자기 타입 파라미터를 선언한 메서드(1.27). 인터페이스를 만족시키지 못한다.
- **GC shape stenciling** — gc 의 구현. 기계어 모양이 같은 타입 인자끼리 본문 한 벌을 나눠 쓴다.
- **사전(dictionary)** — 한 벌의 본문이 「지금의 타입 인자」를 알기 위해 받는 표. 심볼 `main..dict.F[…]`.
- **단형화(monomorphization)** — 타입마다 따로 한 벌을 찍는 전략(Rust 가 쓴다).

---

## 더 들어가면

- ★ 제네릭 구현 설계 문서(GC shape stenciling · 사전 설계)는 **안 열었다.** 이 문서의 층 구분은 **심볼 이름**과 명세의 **침묵**에서 나왔다.
- ★ 사전을 거치는 호출과 인터페이스 호출의 **속도 비교**는 목록의 **50번 주제**(벤치마크)의 자리다 — 여기서는 **안 쟀다.**
- ★ 1.24 의 **제네릭 타입 별칭**(`type A[T any] = …`)과 1.27 의 「모든 대입 문맥에서의 함수 타입 추론」은 판 부록에 있으나 **던지지 않았다.**

# go/syntax/16 — 포인터와 값 복사 의미론, `new` 와 `make` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Go 명세](https://go.dev/ref/spec) 의 Pointer types · Address operators ·
> Selectors · Assignability · Calls · Allocation(`new`) · Making slices, maps and channels(`make`) ·
> Method sets 절.\
> 웹이 아니라 **이 툴체인이 들고 있는 `$(go env GOROOT)/doc/go_spec.html` 을 열어** 인용했다.
> 그 파일의 머리는 「**Language version go1.27 (May 26, 2026)**」이다.
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> **버전** — 이 주제의 규칙은 전부 **1.0부터 지금까지 같다.** 판 경계가 없다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 명세로, 출력은 실행으로 접지했다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것. 어느 컴파일러에서도 같다 | `go_spec.html` 원문 인용 |
| **구현(gc)** | 이 컴파일러·런타임이 그렇게 하는 것. 약속은 아니다 | 패닉 스택의 주소·오프셋 · 값을 스택에 두나 힙에 두나 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 실행 출력(재실행 대조까지) |

★ 이 주제도 **명세 보장 칸이 크다.** 「대입은 복사다」도, 「`make` 는 셋에만 쓴다」도,
「`nil` 포인터를 역참조하면 런타임 패닉이다」도 전부 명세에 적혀 있다.
★★ 구현인 칸은 **「값이 스택에 사나 힙에 사나」** 하나다 — 명세에는 그 낱말이 없다.

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
```

```text
===== 명령: go env GOOS GOARCH GOVERSION =====
linux
amd64
go1.27.1
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | 패닉 첫 줄의 **`pc=0x…` 주소** | 빌드 산출물·ASLR 에 달렸다. 같은 바이너리를 다시 돌리면 같지만 **다시 빌드하면 달라질 수 있다** |
| **흔들린다** | 패닉 스택의 `goroutine N [running]` 번호와 `+0x…` 오프셋 | 런타임·빌드 산출물에 달렸다 |
| **흔들린다** | 포인터 값 자체 | 그래서 이 문서는 **주소를 한 번도 안 찍는다** — `==` 로 **같나 다르나**만 묻는다 |
| 안 흔들린다 | 패닉·치명 오류의 **메시지 본문** 셋 (`invalid memory address or nil pointer dereference` · `assignment to entry in nil map` · `all goroutines are asleep - deadlock!`) | 런타임이 정한 문장이다 |
| 안 흔들린다 | 패닉의 `파일:줄` · 종료 코드 `2` | 같은 소스·같은 판이면 같다 |
| 안 흔들린다 | `%T` 가 찍는 타입 이름 · `len`·`cap` 값 · `== nil` 의 참거짓 | 〃 |
| 안 흔들린다 | 컴파일 에러 문장 본문과 `파일:줄:칸` | 〃 |
| 해당 없음 | 맵 순회 순서 | 이 주제는 맵을 **키 하나**로만 쓴다 — 순서가 성립하지 않는다 |

## 한눈에 — 쉽게 말하면

**Go 에서 대입은 언제나 복사다. 갈리는 것은 「무엇이 복사되느냐」뿐이다.**

값을 통째로 복사하는 타입이 있고, **안에 든 포인터만** 복사되어 실체는 하나로 남는 타입이 있다.
포인터는 그 둘째 무리를 **직접** 만드는 법이다.

| 비유 | 실체 |
|---|---|
| 서류를 통째로 복사한다 | **값 타입** — 수치·배열·구조체. 복사본을 고쳐도 원본은 그대로 |
| 사물함 열쇠만 복사한다 | **포인터** `*T` — 열쇠가 둘이어도 사물함은 하나 |
| 서류 안에 열쇠가 끼어 있다 | **슬라이스·맵·채널** — 겉은 복사되는데 **안의 열쇠가 같은 사물함**을 연다 |
| 빈 사물함 하나를 놓고 열쇠를 준다 | **`new(T)`** — 제로값 하나를 놓고 `*T` 를 돌려준다 |
| 쓸 수 있게 차린 세 가지를 만든다 | **`make`** — 슬라이스·맵·채널 **셋에만**. `T` 를 돌려준다(`*T` 가 아니다) |
| 열쇠가 없는데 문을 연다 | **`nil` 포인터 역참조** — 런타임 패닉 |

```text
   b := a  가 무엇을 복사하나

   ┌──────────────┬────────────────────────────┬──────────────────────┐
   │ 타입         │ 복사되는 것                │ 고치면 원본에 보이나 │
   ├──────────────┼────────────────────────────┼──────────────────────┤
   │ int · bool   │ 값 그 자체                 │ 안 보인다            │
   │ [N]T 배열    │ 원소 N개 전부              │ 안 보인다            │
   │ struct       │ 필드 전부(얕게)            │ 안 보인다 (직접 필드)│
   │ string       │ (ptr, len) — 불변이라 무의미│ 고칠 수 없다        │
   │ *T 포인터    │ 주소 한 칸                 │ ★ 보인다            │
   │ []T 슬라이스 │ 헤더 세 칸(ptr·len·cap)    │ ★ 원소는 보인다     │
   │ map[K]V      │ 맵 참조 한 칸              │ ★ 보인다            │
   │ chan T       │ 채널 참조 한 칸            │ ★ 보인다            │
   │ func()       │ 함수 값(코드+캡처)         │ ★ 캡처한 변수가 보인다│
   └──────────────┴────────────────────────────┴──────────────────────┘
       ↑ 윗줄 넷은 「서류」 · 아랫줄 다섯은 「열쇠가 끼어 있는 서류」
```

> **포인터(pointer)** — 변수의 주소를 담는 값. 타입은 `*T` 이고 제로값은 `nil` 이다.\
> 예: `p := &x` 뒤 `*p = 20` 을 하면 `x` 가 20이 된다 — 같은 칸을 가리키기 때문이다.

> **역참조(dereference)** — `*p` 로 포인터가 가리키는 변수에 닿는 것. 명세의 낱말은 pointer indirection 이다.\
> 예: `p` 가 `nil` 이면 `*p` 는 **런타임 패닉**이다.

> **주소를 가질 수 있음(addressable)** — `&` 를 붙일 수 있는 것. 변수·포인터 역참조·슬라이스 인덱스·
> 주소를 가질 수 있는 구조체의 필드·배열 인덱스.\
> 예: **맵 원소는 아니다** — `&m["k"]` 는 컴파일 에러다.

> **얕은 복사(shallow copy)** — 한 겹만 복사하는 것. 구조체를 복사하면 필드는 복사되지만
> 필드가 든 포인터·슬라이스·맵은 **같은 실체**를 가리킨다.\
> 예: (2)절에서 `cp.Sl[0] = 9` 가 원본에도 보인다.

- C 와 다른 점 — **포인터 산술이 없다.** `p++` 도 `p + 1` 도 컴파일 에러다((7)절).
  그리고 **지역 변수의 주소를 돌려줘도 된다** — 컴파일러가 알아서 힙에 둔다((4)절).
- Java 와 다른 점 — 자바는 객체가 **언제나** 참조다. Go 는 **구조체가 값**이고,
  참조가 필요하면 `*T` 를 **적어야** 한다.
- Rust 와 다른 점 — Rust 는 대입이 **이동**일 수 있다. Go 는 **언제나 복사**다 —
  원본이 쓸 수 없게 되는 일이 없다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **어떤 대입이 복사이고 어떤 것이 공유인가** — 그 경계가 타입의 어디에 적혀 있나.
2. `new` 와 `make` 는 왜 둘인가 — **무엇이 갈라서** 둘이 필요한가.
3. 메서드 리시버를 값으로 할지 포인터로 할지가 **무엇을 바꾸나.**

★ 「포인터라는 개념 자체」와 「메모리 모형」은 이 주제가 아니다 —
[`../../../../variables-and-memory/`](../../../../variables-and-memory/)가 정본이다.
여기는 **Go 의 표면**(`*T`·`&`·`new`·`make`·리시버)만 본다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

| 창 | 무엇을 보여 주나 | 한계 |
|---|---|---|
| 실행 출력 | 복사본을 고쳤을 때 원본이 어떻게 됐나 | **왜 그런지는 안 보인다** |
| ★★★ **포인터 동일성 창** — `&a.F == &b.F` · `p == q` | **두 칸이 같은 것을 가리키나** | 주소 자체는 흔들리므로 **`==` 의 참거짓만** 읽는다 |
| ★★ **컴파일 에러** | 이 언어가 **못 하게 막은 것** — 포인터 산술 · `&m[k]` · `make(struct)` | 못 하게 막은 이유까지는 안 말한다 |
| **런타임 패닉·치명 오류** | `nil` 포인터를 역참조했나 · `nil` 맵에 썼나 · `nil` 채널에 보냈나 | **셋의 메시지가 전부 다르다**는 것이 정보다 |

★ 두 번째 창이 이 주제의 본체다. 「값이 같다」와 「같은 칸이다」는 다른 물음이고,
**출력만 보면 그 둘이 구분되지 않는다.**

### (1) `*T`·`&x`·역참조 — 일곱 줄

**언제 쓰나** — 포인터를 처음 만날 때.

```text
===== 소스: t16a.go =====
package main

import "fmt"

func main() {
	x := 10
	p := &x // ① 주소를 얻는다
	fmt.Printf("x=%d  p 의 타입=%T  *p=%d\n", x, p, *p)

	*p = 20 // ② 역참조로 쓴다
	fmt.Println("*p = 20 한 뒤 x =", x)

	x = 30
	fmt.Println("x = 30 한 뒤 *p =", *p)

	q := p // ③ 포인터를 복사해도 가리키는 곳은 하나다
	*q = 40
	fmt.Println("*q = 40 한 뒤 x =", x, " p == q :", p == q)

	var nilp *int // ④ 포인터의 제로값은 nil
	fmt.Println("var nilp *int — nilp == nil :", nilp == nil)

	// ⑤ 포인터의 포인터
	pp := &p
	**pp = 50
	fmt.Println("**pp = 50 한 뒤 x =", x, " 타입 =", fmt.Sprintf("%T", pp))

	// ⑥ 구조체 포인터는 점 하나로 필드에 닿는다 — (*s).F 를 안 써도 된다
	type S struct{ F int }
	s := &S{F: 1}
	s.F = 2
	fmt.Println("s.F =", s.F, " (*s).F =", (*s).F)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
x=10  p 의 타입=*int  *p=10
*p = 20 한 뒤 x = 20
x = 30 한 뒤 *p = 30
*q = 40 한 뒤 x = 40  p == q : true
var nilp *int — nilp == nil : true
**pp = 50 한 뒤 x = 50  타입 = **int
s.F = 2  (*s).F = 2
(exit 0)
```

그림 해설 (한 단계씩):

- `p := &x` 는 **`x` 의 주소**를 담는다. 타입은 **`*int`** 다. 명세:

  > For an operand x of type T, **the address operation `&x` generates a pointer of type `*T` to x.**
  > The operand must be **addressable**, that is, either a variable, pointer indirection,
  > or slice indexing operation; or a field selector of an addressable struct operand;
  > or an array indexing operation of an addressable array.

- `*p = 20` 으로 쓰면 **`x` 가 20**이 되고, `x = 30` 으로 쓰면 **`*p` 가 30**이 된다.
  **양방향**이다 — 하나의 칸을 두 이름으로 부르는 것이기 때문이다.
- `q := p` 는 **주소 한 칸을 복사**한다. `*q = 40` 이 `x` 에 보이고 `p == q` 가 **`true`** 다.
  ★ 주소 값 자체는 안 찍었다 — 흔들리는 칸이다.
- **포인터의 제로값은 `nil`** 이다. 명세: "The value of an uninitialized pointer is nil."
- `**pp` 로 포인터의 포인터도 된다.
- ★ 마지막 줄 — **구조체 포인터는 점 하나로 필드에 닿는다.** `(*s).F` 를 안 써도 된다.
  명세가 그 축약을 명시한다.

  > As an exception, if the type of x is a defined pointer type and `(*x).f` is a valid selector
  > expression denoting a field (but not a method), **`x.f` is shorthand for `(*x).f`.**

비용 — 포인터 하나는 8바이트(64비트). 역참조는 메모리 접근 한 번 — **이 문서는 재지 않았다.**

### (2) ★★★ 무엇이 복사되나 — 격자 하나로

**언제 쓰나** — 이 주제에서 **가장 중요한 절**이다. Go 버그의 절반이 이 표에서 나온다.

구조체 하나에 여덟 종류의 필드를 담고 **`cp := src` 한 줄**을 한 뒤 전부 고쳐 본다.

```text
===== 소스: t16b.go =====
package main

import "fmt"

type Inner struct{ N int }

type Box struct {
	V   int            // 값
	Arr [2]int         // 배열
	Sl  []int          // 슬라이스
	M   map[string]int // 맵
	Ch  chan int       // 채널
	P   *Inner         // 포인터
	S   string         // 문자열
	F   func() int     // 함수
}

func show(tag string, b Box) {
	fmt.Printf("%-8s V=%d Arr=%v Sl=%v M=%v P.N=%d S=%q\n",
		tag, b.V, b.Arr, b.Sl, b.M, b.P.N, b.S)
}

func main() {
	src := Box{
		V: 1, Arr: [2]int{1, 2}, Sl: []int{1, 2},
		M: map[string]int{"k": 1}, Ch: make(chan int, 1),
		P: &Inner{N: 1}, S: "가",
	}
	cp := src // 대입 한 줄 — 여기서 무엇이 복사되나

	cp.V = 9
	cp.Arr[0] = 9
	cp.Sl[0] = 9
	cp.M["k"] = 9
	cp.P.N = 9
	cp.S = "나"
	cp.Ch <- 7

	show("원본", src)
	show("복사본", cp)
	fmt.Println("원본 채널에서 받은 값 :", <-src.Ch, " — 복사본에 보낸 것이다")

	fmt.Println()
	fmt.Println("두 칸이 같은 것을 가리키나")
	fmt.Println("  &src.V   == &cp.V   :", &src.V == &cp.V)
	fmt.Println("  &src.Arr[0] == &cp.Arr[0] :", &src.Arr[0] == &cp.Arr[0])
	fmt.Println("  &src.Sl[0] == &cp.Sl[0] :", &src.Sl[0] == &cp.Sl[0])
	fmt.Println("  src.P    == cp.P    :", src.P == cp.P)
	fmt.Println("  src.Ch   == cp.Ch   :", src.Ch == cp.Ch)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
원본       V=1 Arr=[1 2] Sl=[9 2] M=map[k:9] P.N=9 S="가"
복사본      V=9 Arr=[9 2] Sl=[9 2] M=map[k:9] P.N=9 S="나"
원본 채널에서 받은 값 : 7  — 복사본에 보낸 것이다

두 칸이 같은 것을 가리키나
  &src.V   == &cp.V   : false
  &src.Arr[0] == &cp.Arr[0] : false
  &src.Sl[0] == &cp.Sl[0] : true
  src.P    == cp.P    : true
  src.Ch   == cp.Ch   : true
(exit 0)
```

그림 해설 (한 단계씩):

- `cp := src` **한 줄**이 일어난 뒤, 복사본을 여섯 군데 고쳤다. 결과가 **둘로 갈린다.**

| 고친 것 | 원본에 보이나 | 왜 |
|---|---|---|
| `cp.V = 9`(`int`) | **안 보인다** | 값이 통째로 복사됐다 |
| `cp.Arr[0] = 9`(`[2]int`) | **안 보인다** | 배열도 값이다 — 원소까지 복사된다 |
| `cp.S = "나"`(`string`) | **안 보인다** | 문자열은 불변이라 「고친다」가 새 값을 넣는 것이다 |
| `cp.Sl[0] = 9`(`[]int`) | ★ **보인다** | 헤더만 복사됐고 **기반 배열은 하나** |
| `cp.M["k"] = 9`(`map`) | ★ **보인다** | 맵 참조가 복사됐다 |
| `cp.P.N = 9`(`*Inner`) | ★ **보인다** | 주소가 복사됐다 |
| `cp.Ch <- 7`(`chan`) | ★ **보인다** | 채널 참조가 복사됐다 — **원본에서 받아진다** |

- ★★★ 아래 다섯 줄이 그 판정을 **출력으로** 못 박는다 —
  `&src.V == &cp.V` 가 **`false`**, `&src.Sl[0] == &cp.Sl[0]` 가 **`true`**,
  `src.P == cp.P` 와 `src.Ch == cp.Ch` 가 **`true`** 다.
  ★ **주소를 안 찍고 `==` 만 물었다.** 알고 싶은 것은 「같나 다르나」뿐이다.
- 명세는 「복사」라는 낱말을 따로 쓰지 않는다 — **대입의 정의**와 **각 타입의 정의**가 이것을 함께 만든다.
  슬라이스는 "a **descriptor** for a contiguous segment of an underlying array" 이고,
  맵은 "a reference to a hash table" 성격의 값이며, 배열은 "The length is **part of the array's type**" 이다.
- ★★ 이것이 **얕은 복사**다. 구조체를 복사해도 **한 겹만** 복사된다.
  깊은 복사가 필요하면 **손으로 써야 한다** — Go 에 `clone` 이 언어 차원에 없다
  (`slices.Clone`·`maps.Clone` 은 **한 겹**만 더 떠 준다).

```text
   cp := src   한 줄 뒤

   src.V   [1]     cp.V   [9]      <- 칸이 둘
   src.Arr [1 2]   cp.Arr [9 2]    <- 칸이 둘
   src.Sl  [ptr]───┬──> [9 2]      <- 칸은 둘인데 가리키는 곳이 하나
   cp.Sl   [ptr]───┘
   src.P   [addr]──┬──> Inner{9}
   cp.P    [addr]──┘
```

비용 — 구조체 대입은 **그 크기만큼의 메모리 복사**다. 안에 슬라이스·맵이 있어도
**그 실체까지 복사되지는 않는다.**

### (3) ★★ `new` 와 `make` — 무엇이 갈라서 둘인가

**언제 쓰나** — 「`new` 를 써야 하나 `make` 를 써야 하나」에서 멈출 때.

```text
===== 소스: t16c.go =====
package main

import "fmt"

type P struct{ X, Y int }

func main() {
	fmt.Println("── new(T) 는 *T 를 준다. 제로값 하나를 놓고 그 주소를 돌려준다 ──")
	a := new(int)
	b := new(P)
	c := new([3]int)
	d := new([]int)
	e := new(map[string]int)
	fmt.Printf("  new(int)             -> %T  *p=%v\n", a, *a)
	fmt.Printf("  new(P)               -> %T  *p=%v\n", b, *b)
	fmt.Printf("  new([3]int)          -> %T  *p=%v\n", c, *c)
	fmt.Printf("  new([]int)           -> %T  *p=%v  *p == nil : %v\n", d, *d, *d == nil)
	fmt.Printf("  new(map[string]int)  -> %T  *p=%v  *p == nil : %v\n", e, *e, *e == nil)

	fmt.Println("── make 는 T 를 준다. 그리고 쓸 수 있게 초기화한다 ──")
	s := make([]int, 2, 5)
	m := make(map[string]int)
	ch := make(chan int, 3)
	fmt.Printf("  make([]int,2,5)      -> %T  %v  len=%d cap=%d  == nil : %v\n", s, s, len(s), cap(s), s == nil)
	fmt.Printf("  make(map[string]int) -> %T  %v  == nil : %v\n", m, m, m == nil)
	fmt.Printf("  make(chan int, 3)    -> %T  cap=%d  == nil : %v\n", ch, cap(ch), ch == nil)

	fmt.Println("── new 로 만든 슬라이스도 append 는 된다(nil 슬라이스라서) ──")
	*d = append(*d, 1, 2)
	fmt.Println("  *d = append(*d, 1, 2) 뒤 :", *d)
	m["쓸 수 있다"] = 1
	fmt.Println("  make 한 맵에는 바로 쓴다 :", m)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
── new(T) 는 *T 를 준다. 제로값 하나를 놓고 그 주소를 돌려준다 ──
  new(int)             -> *int  *p=0
  new(P)               -> *main.P  *p={0 0}
  new([3]int)          -> *[3]int  *p=[0 0 0]
  new([]int)           -> *[]int  *p=[]  *p == nil : true
  new(map[string]int)  -> *map[string]int  *p=map[]  *p == nil : true
── make 는 T 를 준다. 그리고 쓸 수 있게 초기화한다 ──
  make([]int,2,5)      -> []int  [0 0]  len=2 cap=5  == nil : false
  make(map[string]int) -> map[string]int  map[]  == nil : false
  make(chan int, 3)    -> chan int  cap=3  == nil : false
── new 로 만든 슬라이스도 append 는 된다(nil 슬라이스라서) ──
  *d = append(*d, 1, 2) 뒤 : [1 2]
  make 한 맵에는 바로 쓴다 : map[쓸 수 있다:1]
(exit 0)
```

그림 해설 (한 단계씩):

- **`new(T)` 는 언제나 `*T`** 를 준다. 제로값 하나를 놓고 그 주소를 돌려준다. 명세:

  > **The built-in function `new` creates a new, initialized variable and returns a pointer to it.** …
  > If the argument is a type T, then **`new(T)` allocates a variable of type T
  > initialized to its zero value.**

- **`make` 는 `T` 를 준다 — `*T` 가 아니다.** 그리고 **셋에만** 쓴다. 명세:

  > **The built-in function `make` takes a type T, which must be a slice, map or channel type**,
  > or a type parameter, optionally followed by a type-specific list of expressions.
  > **It returns a value of type T (not *T).** The memory is initialized as described in the section
  > on initial values.

- ★★★ **갈리는 이유가 여기 있다.** 슬라이스·맵·채널은 **제로값이 쓸 수 없는 상태**다 —
  `nil` 맵에 쓰면 패닉하고 `nil` 채널은 영원히 막힌다.
  그래서 「제로값을 놓는 것」(`new`)으로는 부족하고 **런타임 자료구조를 차리는 함수**(`make`)가 따로 필요하다.
  나머지 타입은 **제로값이 이미 쓸 만해서** `new` 로 충분하다.
- 그 차이가 출력에 그대로 있다 — **`new([]int)` 의 `*p` 는 `nil` 슬라이스**이고,
  **`new(map[string]int)` 의 `*p` 는 `nil` 맵**이다.
  반면 `make` 로 만든 셋은 전부 **`== nil` 이 `false`** 다.
- ★ 그런데 **`nil` 슬라이스에는 `append` 가 된다** — 마지막 줄이 그것이다.
  `nil` 맵은 안 된다((6)절에서 패닉을 던진다). **슬라이스와 맵이 여기서 갈린다.**
  ([05번 주제](../05-arrays-vs-slices-value-and-header/) (6)절이 `nil` 슬라이스의 정본이다.)

```text
   new(T)                          make(T, …)

   제로값 T 하나를 놓고            슬라이스·맵·채널을 「쓸 수 있게」 차리고
   그 주소를 돌려준다              그 값을 돌려준다
        -> *T                           -> T

   어떤 타입에도 쓴다              셋에만 쓴다
   `nil` 맵을 만들 뿐이다          맵을 실제로 만든다
```

비용 — 둘 다 할당이다. `make([]T, n)` 은 원소 n개만큼 잡는다.

### (4) `new(T)` 와 `&T{}` 는 같은 것을 만든다

**언제 쓰나** — 둘 중 무엇을 쓸지 고를 때.

```text
===== 소스: t16d.go =====
package main

import (
	"fmt"
	"reflect"
)

type P struct{ X, Y int }

func main() {
	a := new(P)
	b := &P{}
	c := &P{X: 0, Y: 0}
	fmt.Printf("new(P)    %T  %v\n", a, *a)
	fmt.Printf("&P{}      %T  %v\n", b, *b)
	fmt.Printf("&P{0,0}   %T  %v\n", c, *c)
	fmt.Println("*a == *b == *c :", *a == *b && *b == *c)
	fmt.Println("a == b (같은 것을 가리키나) :", a == b, " — 다른 곳에 놓였다")
	fmt.Println("타입이 같나 :", reflect.TypeOf(a) == reflect.TypeOf(b))

	// 기본 타입은 &int{} 가 없으니 new 가 유일한 한 줄짜리다
	n := new(int)
	*n = 7
	fmt.Println("new(int) 에 7 을 넣으면 *n =", *n)

	// 지역 변수의 주소를 돌려줘도 된다 — C 와 갈리는 자리다
	fmt.Println("지역 변수의 주소를 돌려받아 읽는다 :", *escape())
}

func escape() *int {
	v := 42 // 스택에 있을 법한 지역 변수
	return &v
}
===== 명령: go build -trimpath -o prog . && ./prog =====
new(P)    *main.P  {0 0}
&P{}      *main.P  {0 0}
&P{0,0}   *main.P  {0 0}
*a == *b == *c : true
a == b (같은 것을 가리키나) : false  — 다른 곳에 놓였다
타입이 같나 : true
new(int) 에 7 을 넣으면 *n = 7
지역 변수의 주소를 돌려받아 읽는다 : 42
(exit 0)
```

그림 해설 (한 단계씩):

- `new(P)`·`&P{}`·`&P{X: 0, Y: 0}` 셋 다 **`*main.P`** 이고 가리키는 값이 **`{0 0}`** 이다.
  `reflect.TypeOf` 로 봐도 같다.
- ★ 그런데 `a == b` 는 **`false`** 다 — **다른 곳에 놓였기** 때문이다. 「같은 타입」과 「같은 칸」은 다르다.
- **`&P{}` 쪽이 관용**이다. 필드를 채워 만들 수 있기 때문이다. `new` 가 남는 자리는
  **기본 타입**(`new(int)`)처럼 `&int{}` 라는 문법이 없는 경우다.
  ★ 명세는 **`new(123)` 처럼 식도 받는다**고 적지만, 실무에서 쓰이는 일은 드물다.
- ★★★ **마지막 줄이 C 와 갈리는 자리다.** `escape()` 는 **지역 변수의 주소를 돌려준다.**
  C 라면 대롱 포인터(dangling pointer)가 되어 UB 인데, **Go 는 42를 그대로 읽어 준다.**
  컴파일러가 탈출 분석으로 **그 변수를 힙에 두기** 때문이다.
  ★ 「스택이냐 힙이냐」는 **명세에 없는 낱말**이다 — 명세는 그저 「그 변수는 살아 있다」고만 보장한다.
  어디에 두느냐는 **구현**이고, 그 판정을 보는 법은 [13번 주제](../13-closures-variable-capture-and-loop-variable-change/) (7)절에 있다.

비용 — 힙 할당 하나. 다만 **컴파일러가 스택에 둘 수도 있다** — 이 문서는 **그것을 재지 않았다.**

### (5) ★★ 값 리시버는 복사본을 고친다

**언제 쓰나** — 메서드를 처음 쓸 때. **조용히 틀리는 자리**다.

```text
===== 소스: t16e.go =====
package main

import "fmt"

type Counter struct{ n int }

func (c Counter) IncVal()  { c.n++ } // 값 리시버 — 복사본을 고친다
func (c *Counter) IncPtr() { c.n++ } // 포인터 리시버 — 원본을 고친다
func (c Counter) Get() int { return c.n }

type Big struct{ Buf [1024]byte }

func (b Big) ByValue() byte { return b.Buf[0] }
func (b *Big) ByPtr() byte  { return b.Buf[0] }

func main() {
	c := Counter{}
	c.IncVal()
	fmt.Println("IncVal() 뒤 :", c.Get(), " — 복사본을 고쳤다")
	c.IncPtr()
	fmt.Println("IncPtr() 뒤 :", c.Get(), " — 원본을 고쳤다")

	// 주소를 가질 수 있으면 c.IncPtr() 은 (&c).IncPtr() 로 자동 변환된다
	p := &c
	p.IncVal()
	p.IncPtr()
	fmt.Println("포인터에서 둘 다 불러도 :", c.Get(), " — 값 리시버 쪽만 못 고친다")

	// 슬라이스 원소는 주소를 가질 수 있다
	cs := []Counter{{}, {}}
	cs[0].IncPtr()
	cs[1].IncVal()
	fmt.Println("슬라이스 원소 :", cs[0].Get(), cs[1].Get())

	var big Big
	big.Buf[0] = 7
	fmt.Println("값 리시버는 1024바이트를 복사한다 :", big.ByValue(), " · 포인터는 안 한다 :", big.ByPtr())
}
===== 명령: go build -trimpath -o prog . && ./prog =====
IncVal() 뒤 : 0  — 복사본을 고쳤다
IncPtr() 뒤 : 1  — 원본을 고쳤다
포인터에서 둘 다 불러도 : 2  — 값 리시버 쪽만 못 고친다
슬라이스 원소 : 1 0
값 리시버는 1024바이트를 복사한다 : 7  · 포인터는 안 한다 : 7
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`c.IncVal()` 뒤에도 `c.n` 이 0**이다. 값 리시버 `c Counter` 가 **복사본**이라
  그 안의 `c.n++` 가 복사본을 고쳤다. **에러도 경고도 없다.**
- `c.IncPtr()` 뒤에는 1이다. 포인터 리시버 `c *Counter` 가 원본을 가리킨다.
- ★ `p := &c` 로 바꿔 불러도 **똑같다.** 「포인터로 불렀으니 고쳐지겠지」가 아니다 —
  갈리는 것은 **부르는 쪽이 아니라 리시버 선언**이다.
  (`p.IncVal()` 은 `(*p).IncVal()` 로 풀려 역시 복사본을 만든다.)
- 슬라이스 원소도 마찬가지다 — `cs[0].IncPtr()` 은 1이 되고 `cs[1].IncVal()` 은 0이다.
  ★ **슬라이스 인덱스는 주소를 가질 수 있어서** `cs[0].IncPtr()` 이 자동으로 `(&cs[0]).IncPtr()` 이 된다.
  **맵 원소였다면 그 자동 변환이 안 된다**((7)절이 그 에러를 던진다).
- 마지막 줄 — 값 리시버는 **1024바이트짜리 구조체도 복사한다.**
  ★ 다만 **그 비용은 안 쟀다** — 벤치마크가 없다. 「복사가 일어난다」는 명세의 결과이고,
  「그래서 느리다」는 **측정이 필요한 주장**이다.
- ★★ 메서드 집합(어떤 타입이 어떤 인터페이스를 만족하나)의 정본은 목록의 **19번 주제**다.
  여기서는 **「고쳐지나 안 고쳐지나」** 한 축만 본다.

비용 — 값 리시버는 리시버 크기만큼 복사한다. 포인터 리시버는 8바이트다.

### (6) `nil` 을 건드리는 두 패닉 — 메시지가 다르다

**언제 쓰나** — 패닉 메시지를 읽고 원인을 좁힐 때.

```text
===== 소스: t16f.go =====
package main

import (
	"fmt"
	"os"
)

type P struct{ X int }

func main() {
	var p *P
	fmt.Fprintln(os.Stderr, "-- p == nil :", p == nil, "--")
	fmt.Fprintln(os.Stderr, "-- 이제 *p 를 읽는다 --")
	fmt.Println(p.X)
	fmt.Fprintln(os.Stderr, "-- 여기는 안 온다 --")
}
===== 명령: go build -trimpath -o prog . =====
(exit 0)
```

```text
===== 명령: ./prog 2>&1 =====
-- p == nil : true --
-- 이제 *p 를 읽는다 --
panic: runtime error: invalid memory address or nil pointer dereference
[signal SIGSEGV: segmentation violation code=0x1 addr=0x0 pc=0x499e91]

goroutine 1 [running]:
main.main()
	ex/t16f.go:14 +0xb1
(exit 2)
```

- `p` 가 `nil` 인데 `p.X` 를 읽었다. 명세가 그것을 직접 적는다.

  > **If x is of pointer type and has the value nil and x.f denotes a struct field,
  > assigning to or evaluating x.f causes a run-time panic.**

  그리고 역참조 자체도 같다 — "If x is nil, an attempt to evaluate `*x` will cause a run-time panic."
- 메시지 본문은 `panic: runtime error: invalid memory address or nil pointer dereference` 이고
  그 아래 `[signal SIGSEGV: segmentation violation …]` 이 붙는다. **종료 코드는 2**다.
- ★ 마커 줄을 **표준 오류로** 찍었다(`fmt.Fprintln(os.Stderr, …)`). 파이프로 받아도 자리가 안 바뀐다.
- ★ 빌드와 실행을 **두 블록으로 갈랐다** — 컴파일은 성공하고 실행만 실패한다는 것을 보이기 위해서다.

`new(map)` 은 다른 패닉을 낸다.

```text
===== 소스: t16g.go =====
package main

import (
	"fmt"
	"os"
)

func main() {
	m := new(map[string]int)
	fmt.Fprintln(os.Stderr, "-- new(map) 은 nil 맵을 놓는다 : *m == nil 이", *m == nil, "--")
	fmt.Fprintln(os.Stderr, "-- 읽기는 된다 : (*m)[\"a\"] =", (*m)["a"], "--")
	fmt.Fprintln(os.Stderr, "-- 이제 쓴다 --")
	(*m)["a"] = 1
	fmt.Fprintln(os.Stderr, "-- 여기는 안 온다 --")
}
===== 명령: go build -trimpath -o prog . =====
(exit 0)
```

```text
===== 명령: ./prog 2>&1 =====
-- new(map) 은 nil 맵을 놓는다 : *m == nil 이 true --
-- 읽기는 된다 : (*m)["a"] = 0 --
-- 이제 쓴다 --
panic: assignment to entry in nil map

goroutine 1 [running]:
main.main()
	ex/t16g.go:13 +0x169
(exit 2)
```

- **읽기는 된다** — `(*m)["a"]` 가 제로값 `0` 을 준다. `nil` 맵도 읽을 수 있다.
- **쓰면 패닉**이다 — `panic: assignment to entry in nil map`.
  ★ 메시지가 **완전히 다르다.** 앞엣것은 「주소가 잘못됐다」이고 이것은 「`nil` 맵에 넣으려 했다」다.
- ★★ **두 메시지를 가르는 것이 실무의 진단**이다 —
  앞엣것은 **포인터가 `nil`**, 뒤엣것은 **맵을 `make` 안 했다**는 뜻이다.
- 그리고 이것이 (3)절의 결론을 다시 말한다 — **`new(map)` 으로는 맵을 못 만든다.**
  `make` 를 써야 한다.

★★ 셋째 꼴이 하나 더 있다 — **`new(chan int)` 로 만든 채널에 보내면** 또 다른 말이 나온다.

```text
===== 소스: t16j.go =====
package main

import (
	"fmt"
	"os"
)

func main() {
	c := new(chan int)
	fmt.Fprintln(os.Stderr, "-- new(chan int) 의 *c == nil :", *c == nil, "--")
	fmt.Fprintln(os.Stderr, "-- 이제 보낸다 --")
	*c <- 1
	fmt.Fprintln(os.Stderr, "-- 여기는 안 온다 --")
}
===== 명령: go build -trimpath -o prog . =====
(exit 0)
```

```text
===== 명령: ./prog 2>&1 =====
-- new(chan int) 의 *c == nil : true --
-- 이제 보낸다 --
fatal error: all goroutines are asleep - deadlock!

goroutine 1 [chan send (nil chan)]:
main.main()
	ex/t16j.go:12 +0xc5
(exit 2)
```

- **`panic:` 이 아니라 `fatal error:`** 다 — `fatal error: all goroutines are asleep - deadlock!`.
  ★ 그리고 goroutine 줄이 이유를 말해 준다 — **`[chan send (nil chan)]`**.
- ★★★ **`fatal error` 는 `recover` 로 못 잡는다.** `panic` 과 다른 부류다.
  「패닉 메시지를 읽고 원인을 좁힌다」에서 **첫 낱말부터 갈린다.**
- 종료 코드는 역시 **2**다.
- 셋을 한 줄로 묶으면 — **`nil` 포인터는 「주소가 잘못됐다」, `nil` 맵은 「넣을 수 없다」,
  `nil` 채널은 「영원히 기다린다」** 다. 셋 다 `new` 로 만들면 걸리는 자리이고,
  **맵과 채널은 `make` 를 써야** 풀린다.

비용 — 없다(셋 다 프로그램이 죽는다).

### (7) ★★ 컴파일러가 못 하게 막은 것 — 포인터 산술이 없다

**언제 쓰나** — C 에서 오면 여기서 막힌다.

```text
===== 소스: t16h.go =====
package main

import "fmt"

type P struct{ X int }

func main() {
	a := [3]int{1, 2, 3}
	p := &a[0]
	p++
	q := p + 1
	fmt.Println(*q)

	m := map[string]P{"k": {1}}
	r := &m["k"]
	fmt.Println(r)

	s := make(P)
	fmt.Println(s)

	t := make([]int)
	fmt.Println(t)

	u := new(int, 3)
	fmt.Println(u)

	var f float64 = 1.5
	g := (*int)(&f)
	fmt.Println(g)
}
===== 명령: go build -trimpath -o prog . =====
# ex
./t16h.go:10:2: invalid operation: p++ (non-numeric type *int)
./t16h.go:11:7: invalid operation: p + 1 (mismatched types *int and untyped int)
./t16h.go:15:8: invalid operation: cannot take address of m["k"] (map index expression of struct type P)
./t16h.go:18:12: invalid argument: cannot make P: type must be slice, map, or channel
./t16h.go:21:7: invalid operation: make([]int) expects 2 or 3 arguments; found 1
./t16h.go:24:7: invalid operation: too many arguments for new(int, 3) (expected 1, found 2)
./t16h.go:28:14: cannot convert &f (value of type *float64) to type *int
(exit 1)
```

그림 해설 (한 단계씩):

- ★★★ **`p++` 도 `p + 1` 도 에러**다 — `invalid operation: p++ (non-numeric type *int)` ·
  `mismatched types *int and untyped int`.
  **Go 에 포인터 산술이 없다.** 배열을 훑으려면 **슬라이스와 인덱스**를 쓴다.
  ★ C 와 갈리는 가장 큰 자리다
  ([`../../../c/syntax/16-array-pointer-decay-and-function-parameters/`](../../../c/syntax/16-array-pointer-decay-and-function-parameters/)).
- **`&m["k"]` 가 에러**다 — `cannot take address of m["k"] (map index expression of struct type P)`.
  ★ 맵 원소는 **주소를 가질 수 없다**(addressable 이 아니다). 맵이 자라며 원소를 옮길 수 있기 때문이다.
  정본은 [09번 주제](../09-maps-declaration-comma-ok-delete-and-iteration-order/)다.
- **`make(P)` 가 에러**다 — `cannot make P: type must be slice, map, or channel`.
  **메시지가 규칙을 그대로 말해 준다.**
- **`make([]int)` 도 에러**다 — 슬라이스는 길이를 줘야 한다(`expects 2 or 3 arguments`).
- **`new(int, 3)` 도 에러**다 — `new` 는 인자가 **하나**다.
- **`(*int)(&f)` 가 에러**다 — `cannot convert &f (value of type *float64) to type *int`.
  **포인터 타입끼리 마음대로 못 바꾼다.** 그런 일을 하려면 `unsafe` 가 필요하다.

비용 — 없다. 전부 컴파일 시점이다.

### (8) 함수에 넘길 때 — 무엇을 바꿀 수 있나

**언제 쓰나** — 「이 함수가 내 값을 고칠 수 있나」를 판단할 때.

```text
===== 소스: t16i.go =====
package main

import "fmt"

type P struct{ X int }

func byValue(p P)   { p.X = 99 }
func byPtr(p *P)    { p.X = 99 }
func reseat(p *P)   { p = &P{X: 7}; _ = p } // 포인터 자체를 갈아 끼운다 — 밖에 안 보인다
func reseat2(p **P) { *p = &P{X: 7} }       // 포인터를 바꾸려면 포인터의 포인터다

func main() {
	a := P{X: 1}
	byValue(a)
	fmt.Println("byValue 뒤 :", a)

	b := P{X: 1}
	byPtr(&b)
	fmt.Println("byPtr 뒤   :", b)

	c := &P{X: 1}
	reseat(c)
	fmt.Println("reseat 뒤  :", *c, " — 포인터 자체는 값으로 넘어갔다")

	d := &P{X: 1}
	reseat2(&d)
	fmt.Println("reseat2 뒤 :", *d)

	// 슬라이스·맵·채널은 「이미 안에 포인터가 있어서」 값으로 넘겨도 내용이 보인다
	sl := []int{1, 2}
	func(s []int) { s[0] = 99 }(sl)
	m := map[string]int{"k": 1}
	func(mm map[string]int) { mm["k"] = 99 }(m)
	fmt.Println("슬라이스·맵은 값으로 넘겨도 내용이 보인다 :", sl, m)

	// 그런데 헤더 자체를 바꾸는 것은 안 보인다(05번 주제)
	func(s []int) { s = append(s, 3) }(sl)
	fmt.Println("append 는 안 보인다 : len =", len(sl))
}
===== 명령: go build -trimpath -o prog . && ./prog =====
byValue 뒤 : {1}
byPtr 뒤   : {99}
reseat 뒤  : {1}  — 포인터 자체는 값으로 넘어갔다
reseat2 뒤 : {7}
슬라이스·맵은 값으로 넘겨도 내용이 보인다 : [99 2] map[k:99]
append 는 안 보인다 : len = 2
(exit 0)
```

그림 해설 (한 단계씩):

- `byValue(a)` 는 **원본을 못 고친다** — 매개변수가 복사본이다.
  명세: "the arguments of the call are passed to the function, which means that they are
  **assigned to their corresponding function parameters**." 즉 **인자 전달도 대입이다.**
- `byPtr(&b)` 는 고친다.
- ★★ `reseat(c)` 는 **포인터 자체를 갈아 끼우는데 밖에 안 보인다** —
  `p = &P{X: 7}` 이 고친 것은 **포인터의 복사본**이다.
  포인터를 바꾸려면 **포인터의 포인터**가 필요하다(`reseat2`).
  ★ 이것이 05번 주제의 「`append` 결과가 안 보이는」 것과 **같은 모양**이다.
- **슬라이스·맵은 값으로 넘겨도 내용이 보인다** — (2)절의 표 그대로다.
- ★ 그런데 **`append` 는 안 보인다** — 마지막 줄이 그것이다.
  「내용은 보이는데 헤더는 안 보인다」가 슬라이스의 정확한 성질이다
  ([05번 주제](../05-arrays-vs-slices-value-and-header/) (3)절이 정본).

비용 — 매개변수 크기만큼 복사. 포인터면 8바이트다.

## 문법 — 형태와 규칙

### 형태

```go
// t16form.go
package main

import "fmt"

type P struct{ X int }

func main() {
	var p *int      // ① 포인터 타입 — 제로값은 nil
	x := 1          //
	p = &x          // ② 주소 연산자
	fmt.Println(*p) // ③ 역참조

	q := new(P)   // ④ new — *P 를 준다
	r := &P{X: 1} // ⑤ 리터럴의 주소 — ④ 와 같은 타입이다
	q.X = 2       // ⑥ 포인터에서 점 하나로 필드에 닿는다
	fmt.Println(q.X, r.X, (*r).X)

	s := make([]int, 1) // ⑦ make — 슬라이스·맵·채널 셋에만
	m := make(map[string]int)
	c := make(chan int, 1)
	fmt.Println(s, m, cap(c))

	var pp **int = &p // ⑧ 포인터의 포인터
	fmt.Println(**pp)
}
```

```text
===== 소스: t16form.go =====
package main

import "fmt"

type P struct{ X int }

func main() {
	var p *int      // ① 포인터 타입 — 제로값은 nil
	x := 1          //
	p = &x          // ② 주소 연산자
	fmt.Println(*p) // ③ 역참조

	q := new(P)   // ④ new — *P 를 준다
	r := &P{X: 1} // ⑤ 리터럴의 주소 — ④ 와 같은 타입이다
	q.X = 2       // ⑥ 포인터에서 점 하나로 필드에 닿는다
	fmt.Println(q.X, r.X, (*r).X)

	s := make([]int, 1) // ⑦ make — 슬라이스·맵·채널 셋에만
	m := make(map[string]int)
	c := make(chan int, 1)
	fmt.Println(s, m, cap(c))

	var pp **int = &p // ⑧ 포인터의 포인터
	fmt.Println(**pp)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
1
2 1 1
[0] map[] 1
1
(exit 0)
```

규칙 불릿.

- **`*T` 는 타입**이고 **`*p` 는 역참조**다. 같은 별표가 자리에 따라 다른 일을 한다.
- **`&x` 는 `x` 가 addressable 일 때만** 된다 — 변수·역참조·슬라이스 인덱스·
  주소 가능한 구조체의 필드·주소 가능한 배열의 인덱스. **맵 원소는 아니다.**
  예외로 **복합 리터럴**(`&P{}`)에는 붙일 수 있다.
- **포인터의 제로값은 `nil`** 이고 `nil` 역참조는 **런타임 패닉**이다.
- **구조체 포인터는 점 하나**로 필드에 닿는다 — `p.F` 가 `(*p).F` 의 축약이다.
- **`new(T)` 는 `*T`**, **`make(T, …)` 는 `T`** 를 돌려준다. `make` 는 **슬라이스·맵·채널** 셋에만.
- **포인터 산술이 없다.** `p++`·`p+1`·`p[i]` 전부 안 된다.
- **포인터 타입끼리 변환이 안 된다**(`unsafe` 없이는).
- 포인터는 **`==` 로 비교**되고 `nil` 과도 비교된다.
- **메서드 리시버가 값이면 복사본**을, 포인터면 원본을 받는다.
  주소를 가질 수 있는 피연산자에서는 `x.M()` 이 `(&x).M()` 으로 **자동 변환**된다.

### 금지 사례 — 컴파일러가 거부하는 것

(7)절의 블록이 정본이다. 일곱 가지를 한 표로 묶으면 이렇다.

| 쓴 것 | 메시지 | 왜 막나 |
|---|---|---|
| `p++` | `invalid operation: p++ (non-numeric type *int)` | 포인터 산술이 없다 |
| `p + 1` | `invalid operation: p + 1 (mismatched types *int and untyped int)` | 〃 |
| `&m["k"]` | `cannot take address of m["k"] (map index expression of struct type P)` | 맵 원소는 addressable 이 아니다 |
| `make(P)` | `invalid argument: cannot make P: type must be slice, map, or channel` | `make` 는 셋에만 |
| `make([]int)` | `invalid operation: make([]int) expects 2 or 3 arguments; found 1` | 슬라이스는 길이가 필요하다 |
| `new(int, 3)` | `invalid operation: too many arguments for new(int, 3) (expected 1, found 2)` | `new` 는 인자 하나 |
| `(*int)(&f)` | `cannot convert &f (value of type *float64) to type *int` | 포인터 타입 변환이 없다 |

★ **거부하지 않는 것**도 함께 봐야 한다 — **값 리시버로 원본을 못 고치는 것**은
에러도 경고도 없다((5)절). 그것이 이 주제의 조용한 자리다.

## 어디서 틀리나

### 1. ★★★ 「구조체를 복사했으니 완전히 갈라졌다」

- (2)절 실측 — `cp.Sl[0] = 9`·`cp.M["k"] = 9`·`cp.P.N = 9` 가 **전부 원본에 보인다.**
- **얕은 복사**다. 한 겹만 복사된다.
- 고치는 법 — 깊은 복사가 필요하면 **손으로 쓴다.** `slices.Clone`·`maps.Clone` 도 **한 겹**만 더 뜬다.

### 2. ★★★ 「값 리시버로도 필드를 고칠 수 있겠지」

- (5)절 실측 — `IncVal()` 뒤에도 **0**이다. 에러도 경고도 없다.
- 포인터로 불러도 마찬가지다 — 갈리는 것은 **리시버 선언**이지 부르는 쪽이 아니다.
- 고치는 법 — **고치는 메서드는 포인터 리시버**로 선언한다.
  한 타입 안에서 리시버 종류를 섞지 않는 것이 관용이다.

### 3. ★★ 「`new(map[string]int)` 로 맵을 만들었다」

- (6)절 실측 — **읽기는 되고 쓰면 패닉**이다. `assignment to entry in nil map`.
- `new` 는 **제로값을 놓을 뿐**이고 맵의 제로값은 `nil` 이다.
- 고치는 법 — **`make`** 를 쓴다. 그리고 두 패닉 메시지를 외워 둔다.

### 4. ★★ 「`nil` 이면 아무것도 못 한다」

- (3)절·(6)절 실측 — **`nil` 슬라이스에는 `append` 가 되고**, **`nil` 맵은 읽기가 된다.**
  못 하는 것은 **`nil` 맵에 쓰기**와 **`nil` 포인터 역참조**다.
- 고치는 법 — 타입마다 `nil` 의 쓸모가 다르다. 슬라이스는 그냥 쓰고 맵은 `make` 한다.

### 5. ★★ 「포인터를 넘겼으니 그 포인터를 바꿀 수 있다」

- (8)절 실측 — `reseat(c)` 뒤 `*c` 가 **`{1}`** 그대로다.
- **포인터도 값**이다. 함수가 받은 것은 주소의 복사본이다.
- 고치는 법 — **`**T` 를 받거나 결과를 돌려받는다.** Go 관용은 뒤쪽이다.

### 6. ★★ 「맵 원소의 주소를 잡아 고치면 되지」

- (7)절 실측 — **컴파일 에러**다. `cannot take address of m["k"]`.
- 맵이 자라면서 원소를 옮길 수 있어 주소가 안정적이지 않기 때문이다.
- 고치는 법 — **꺼내 고쳐 다시 넣거나**, 맵의 값 타입을 **포인터**로 둔다(`map[string]*P`).

### 7. ★ 「C 처럼 포인터를 움직여 배열을 훑자」

- (7)절 실측 — `p++` 도 `p + 1` 도 **컴파일 에러**다.
- 고치는 법 — **슬라이스와 인덱스**를 쓴다. 그것이 Go 에서 그 자리를 맡는다.

### 8. ★ 「지역 변수의 주소를 돌려주면 안 된다」 — C 의 직관이다

- (4)절 실측 — `escape()` 가 돌려준 포인터로 **42를 읽는다.**
- Go 는 그 변수를 **살려 둔다.** 어디에 두느냐(스택/힙)는 컴파일러가 정한다.
- 고치는 법 — 그냥 쓴다. 대신 **할당이 늘 수 있다**는 것만 안다(측정은 별도다).

### 9. ★ 「배열도 슬라이스처럼 공유되겠지」

- (2)절 실측 — `cp.Arr[0] = 9` 가 **원본에 안 보인다.** 배열은 값이다.
- 정본은 [05번 주제](../05-arrays-vs-slices-value-and-header/)다.
- 고치는 법 — 공유하고 싶으면 **슬라이스**를 쓰거나 **배열 포인터**(`*[N]T`)를 넘긴다.

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| **대입과 인자 전달이 복사** | **명세 보장** | "arguments … are **assigned to** their corresponding function parameters" |
| `&x` 가 **addressable 한 것에만** 붙는다 | **명세 보장** | "The operand must be addressable, that is, either a variable, pointer indirection, or slice indexing operation; or …" |
| **맵 원소가 addressable 이 아니다** | **명세 보장** | 위 목록에 맵 인덱스가 **없다** |
| **포인터의 제로값이 `nil`** | **명세 보장** | "The value of an uninitialized pointer is nil" |
| **`nil` 역참조가 런타임 패닉** | **명세 보장** | "If x is nil, an attempt to evaluate *x will cause a run-time panic" |
| **`p.F` 가 `(*p).F` 의 축약** | **명세 보장** | "x.f is shorthand for (*x).f" |
| **`new(T)` 가 `*T`** 를 돌려준다 | **명세 보장** | "creates a new, initialized variable and **returns a pointer to it**" |
| **`make` 가 `T` 를 돌려주고 셋에만** 쓰인다 | **명세 보장** | "must be a slice, map or channel type … It returns a value of type T (**not \*T**)" |
| **포인터 산술이 없다** | **명세 보장** | 연산자 절에 포인터 산술이 **없다** |
| **값 리시버가 복사본을 받는다** | **명세 보장** | 리시버도 매개변수이고 인자 전달은 대입이다 |
| `x.M()` 이 **`(&x).M()` 으로 자동 변환** | **명세 보장** | Calls·Method sets 절 |
| 패닉 **메시지 본문**(`invalid memory address …` · `assignment to entry in nil map`) | **런타임(구현)** | 명세는 「패닉한다」까지만 정한다 |
| `nil` 채널 송신이 **영원히 막히는 것** | **명세 보장** | "A send on a nil channel blocks forever" |
| 그것이 `fatal error: … deadlock!` 로 **드러나는 것** | **런타임(구현)** | 데드락 탐지는 런타임의 기능이다 |
| 패닉 스택의 `goroutine N` · `pc=0x…` · `+0x…` | **구현·빌드 산출물** | 다시 빌드하면 달라질 수 있다 |
| **지역 변수의 주소를 돌려줘도 되는 것** | **명세 보장** | 변수의 수명이 접근 가능성으로 정해진다 |
| **그 변수가 스택에 사나 힙에 사나** | **구현(gc)** | 명세에 그 낱말이 없다([13번 주제](../13-closures-variable-capture-and-loop-variable-change/) (7)절) |
| 값 리시버 복사의 **실제 비용** | **안 쟀다** | 벤치마크가 없다(목록의 **50번 주제**) |
| 포인터 하나가 **8바이트**인 것 | **구현·플랫폼** | 64비트의 값이다 |

★ 이 주제의 결론은 「**무엇이 복사되는지는 전부 명세가 정하고,
어디에 놓이는지만 구현이 정한다**」이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 작은 값(수치·작은 구조체)을 넘김 | **값** | 복사가 싸고 공유 사고가 없다 |
| 함수가 원본을 고쳐야 함 | **포인터** | 값으로는 못 고친다 |
| 큰 구조체를 자주 넘김 | **포인터** — 단 **재고 나서** | 「크니까 느리다」는 측정 대상이다 |
| 메서드가 리시버를 고침 | **포인터 리시버** | 값 리시버는 복사본을 고친다 |
| 한 타입에 메서드가 여럿 | **리시버 종류를 통일** | 섞으면 메서드 집합이 헷갈린다(19번 주제) |
| 슬라이스·맵·채널을 만듦 | **`make`** | `new` 는 `nil` 을 놓을 뿐이다 |
| 구조체 하나를 만들어 포인터로 씀 | **`&T{…}`** | 필드를 채워 만들 수 있다 |
| 기본 타입의 포인터가 필요함 | **`new(int)`** 또는 `v := 0; &v` | `&int{}` 라는 문법이 없다 |
| 「값 없음」을 표현해야 함 | **`*T`** 와 `nil` | JSON 에서 빠진 필드와 `null` 을 가를 때가 그 자리(45번 주제) |
| 맵의 값을 자주 고침 | **`map[K]*V`** | 맵 원소는 주소를 못 잡는다 |
| C 처럼 배열을 훑고 싶음 | **슬라이스 + 인덱스** | 포인터 산술이 없다 |

판단 규칙 두 줄.

- **「이 대입이 무엇을 복사하나」를 타입에서 읽어라.** (2)절의 격자가 그 답 전부다.
- **고치는 메서드는 포인터 리시버로 선언하라.** 그러지 않으면 아무 말 없이 안 고쳐진다.

## 핵심 문장

- Go 에서 **대입과 인자 전달은 언제나 복사**다. 갈리는 것은 **무엇이 복사되느냐**뿐이다.
- ★★★ **구조체 복사는 얕다.** 안에 든 슬라이스·맵·채널·포인터는 **같은 실체**를 가리킨다 —
  `&src.Sl[0] == &cp.Sl[0]` 가 **`true`** 이고 `&src.V == &cp.V` 가 **`false`** 다.
- **`new(T)` 는 `*T` 를 주고 `make` 는 `T` 를 준다.** `make` 는 **슬라이스·맵·채널 셋에만** 쓴다.
- ★★ 그 갈림의 이유는 **셋만 제로값이 쓸 수 없는 상태**라서다 —
  `new(map)` 은 맵을 만들지 않고 `nil` 맵을 놓을 뿐이다.
- **`new(P)` 와 `&P{}` 는 같은 것**을 만든다. `&P{…}` 쪽이 관용이고,
  `new` 가 남는 자리는 `&int{}` 라는 문법이 없는 기본 타입이다.
- ★★★ **값 리시버는 복사본을 고친다** — `IncVal()` 뒤에도 카운터가 **0**이다.
  에러도 경고도 없다. 갈리는 것은 **부르는 쪽이 아니라 리시버 선언**이다.
- ★★ **`nil` 을 건드리는 세 메시지가 전부 다르다** —
  `invalid memory address or nil pointer dereference`(포인터) ·
  `assignment to entry in nil map`(맵) ·
  `fatal error: all goroutines are asleep - deadlock!` + `[chan send (nil chan)]`(채널).
  셋 다 **종료 코드 2**인데 **앞의 둘은 `panic:` 이고 마지막은 `fatal error:`** 다.
- ★★ **Go 에 포인터 산술이 없다.** `p++` 도 `p + 1` 도 컴파일 에러다 — 그 자리는 슬라이스가 맡는다.
- **지역 변수의 주소를 돌려줘도 된다.** C 와 갈리는 자리이고, 그것이 가능한 이유(스택/힙)는 **구현**이다.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 16번)
- [05번 주제](../05-arrays-vs-slices-value-and-header/)(배열과 슬라이스) — **이 주제의 직접 선행.**
  **그쪽은 「배열은 값, 슬라이스는 헤더」까지**, 여기는 **그 규칙을 여덟 타입으로 넓힌 격자**부터
- [02번 주제](../02-variable-declarations-and-zero-values/)(변수 선언·제로값) —
  **그쪽은 제로값 규칙까지**, 여기는 **그 제로값이 쓸 만한가 아닌가가 `new`/`make` 를 가르는 것**부터
- [09번 주제](../09-maps-declaration-comma-ok-delete-and-iteration-order/)(맵) —
  **맵 원소가 주소를 못 잡는 것의 정본**
- [13번 주제](../13-closures-variable-capture-and-loop-variable-change/)(클로저) —
  (4)절의 「지역 변수가 살아남는 것」과 **같은 기계**다. 탈출 분석 실측이 거기 (7)절에 있다
- 목록의 **17번 주제**(구조체) — 비교 가능성·필드 태그·정렬. 이 주제의 `Box` 가 거기서 자세해진다
- 목록의 **19번 주제**(메서드 집합) — **값 리시버와 포인터 리시버의 정본.**
  여기서는 「고쳐지나」 한 축만 본다
- 목록의 **21번 주제**(`nil` 인터페이스) — `nil` 이 또 한 번 함정이 되는 자리
- 목록의 **45번 주제**(`encoding/json`) — 「빠진 필드와 `null`」을 `*T` 로 가르는 관용구
- [`../../../../variables-and-memory/`](../../../../variables-and-memory/) —
  **그쪽은 포인터·메모리 모형 일반까지**, 여기는 **Go 의 표면**(`*T`·`&`·`new`·`make`)부터
- [`../../../c/syntax/16-array-pointer-decay-and-function-parameters/`](../../../c/syntax/16-array-pointer-decay-and-function-parameters/) —
  **그쪽은 배열이 포인터로 감쇠하고 포인터 산술로 훑고**,
  여기는 **감쇠도 산술도 없고 슬라이스가 그 자리를 맡는다**

## 용어 풀이

- **포인터(pointer)** — 변수의 주소를 담는 값. 타입 `*T`, 제로값 `nil`.
- **역참조(dereference)** — `*p`. 명세의 낱말은 pointer indirection 이다.
- **주소 연산자(address operator)** — `&x`. `x` 가 addressable 일 때만 쓸 수 있다.
- **addressable** — 주소를 취할 수 있는 것. 변수·역참조·슬라이스 인덱스·주소 가능한 구조체의 필드 등.
  **맵 원소는 아니다.**
- **얕은 복사(shallow copy)** — 한 겹만 복사하는 것. Go 의 구조체 대입이 이것이다.
- **`new(T)`** — 제로값 변수 하나를 만들고 **`*T`** 를 돌려주는 내장 함수.
- **`make(T, …)`** — 슬라이스·맵·채널을 **쓸 수 있게 차려** **`T`** 를 돌려주는 내장 함수.
- **값 리시버 / 포인터 리시버** — `func (c T) M()` 와 `func (c *T) M()`.
  앞엣것은 복사본을, 뒤엣것은 원본을 받는다.
- **포인터 산술(pointer arithmetic)** — 포인터에 수를 더해 옮기는 것. **Go 에는 없다.**
- **대롱 포인터(dangling pointer)** — 죽은 변수를 가리키는 포인터. **Go 에서는 생기지 않는다.**

---

## 더 들어가면

- 명세는 `new` 가 **타입 말고 식도 받는다**고 적는다 — `new(123)` 이 `*int` 를 주고 그 값은 123이다.
  실무에서 쓰이는 일은 드물어 **이 문서는 안 던졌다.**
- `make(T, n)` 의 맵 판은 「**대략** n개가 들어갈 공간」을 잡는다(`initial space for approximately n elements`).
  「정확히」가 아니라는 점이 구현에 여지를 남긴 자리다.
- 배열 포인터 `*[N]T` 는 특별 대우를 받는다 — `p[i]` 로 인덱싱이 되고 `len(p)` 도 된다.
  `range p` 도 된다([14번 주제](../14-for-four-forms-range-over-int-and-func/) (2)절).
  **포인터 중에서 이것만 그렇다.** 이 문서는 그 인덱싱을 **안 던졌다.**
- `unsafe.Pointer` 를 거치면 포인터 타입 변환도 포인터 산술도 된다.
  05번 주제가 `unsafe.SliceData` 를 쓴 것이 그 문의 가장 얌전한 용례다.
  `unsafe` 심화는 이 목록에서 **뺐다**(README 의 「뺀 것과 이유」).
- 구조체에 **슬라이스 필드가 하나라도 있으면 그 구조체는 `==` 로 비교할 수 없다** —
  비교 가능성은 필드를 따라 전파된다. 정본은 목록의 **17번 주제**다.
- Go 에 **참조 타입**(reference type)이라는 공식 낱말은 없다.
  「슬라이스·맵·채널은 참조 타입이다」는 흔한 설명인데 명세의 낱말이 아니다 —
  명세는 슬라이스를 **descriptor**, 맵을 **unordered group … of element types**,
  채널을 **conduit** 로 부른다. **정확히 말하면 「값인데 안에 포인터가 있다」** 다.

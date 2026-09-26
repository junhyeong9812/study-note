# go/syntax/16 — 포인터와 값 복사 의미론, `new` 와 `make` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> 블록은 전부 `===== 소스: … =====` 로 소스를 먼저 싣는다 — **그대로 다시 던질 수 있게** 하기 위해서다.
> ★ **근거로 읽을 칸** — 값, `==` 의 참거짓, `%T` 가 찍는 타입 이름, `len`·`cap`,
> 패닉·치명 오류의 **메시지 본문**과 `파일:줄`, 컴파일 에러 문장과 `파일:줄:칸`, 종료 코드.
> **근거로 읽지 않을 칸** — **포인터 값 자체**(그래서 이 문서는 주소를 한 번도 안 찍는다),
> 패닉 첫 줄의 `pc=0x…`, 스택의 `goroutine N` 과 `+0x…`.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 10 → 20 → 30 → 40 → 50 — 하나의 칸을 두 이름으로 부른다

**출력**

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

**왜 그런가**

- `p := &x` 뒤 `p` 의 타입은 **`*int`** 다. 명세:

  > For an operand x of type T, **the address operation `&x` generates a pointer of type `*T` to x.**

- `*p = 20` 이 `x` 에 보이고, `x = 30` 이 `*p` 에 보인다. **양방향**이다 —
  둘이 서로를 베낀 것이 아니라 **같은 칸을 두 이름으로 부르는 것**이기 때문이다.
- `q := p` 는 **주소 한 칸을 복사**한다. `*q = 40` 이 `x` 에 보이고 **`p == q` 가 `true`** 다.
  ★ 그 줄이 증명하는 것은 「**둘이 같은 곳을 가리킨다**」이지 「값이 같다」가 아니다.
  주소 값 자체는 안 찍었다 — 흔들리는 칸이다.
- **포인터의 제로값은 `nil`** 이다 — "The value of an uninitialized pointer is nil."
- `**pp` 로 포인터의 포인터도 된다. 타입은 `**int` 다.
- 마지막 줄 — `s.F` 와 `(*s).F` 가 같다. 명세가 그 축약을 예외로 명시한다.

  > As an exception, if the type of x is a defined pointer type and `(*x).f` is a valid selector
  > expression denoting a field (but not a method), **`x.f` is shorthand for `(*x).f`.**

- 층 — 전부 **명세 보장**이다. 다만 포인터가 8바이트인 것은 **플랫폼**이다.

### 2. ★★★ 셋은 갈라지고 넷은 공유된다

**출력**

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

**왜 그런가**

| 고친 것 | 원본에 보이나 | 왜 |
|---|---|---|
| `cp.V = 9`(`int`) | **안 보인다** | 값이 통째로 복사됐다 |
| `cp.Arr[0] = 9`(`[2]int`) | **안 보인다** | **배열도 값**이다 — 원소까지 복사된다 |
| `cp.S = "나"`(`string`) | **안 보인다** | 불변이라 「고친다」가 새 값을 대입하는 것이다 |
| `cp.Sl[0] = 9`(`[]int`) | ★ **보인다** | 헤더만 복사됐고 **기반 배열은 하나** |
| `cp.M["k"] = 9`(`map`) | ★ **보인다** | 맵 참조가 복사됐다 |
| `cp.P.N = 9`(`*Inner`) | ★ **보인다** | 주소가 복사됐다 |
| `cp.Ch <- 7`(`chan`) | ★ **보인다** | 채널 참조가 복사됐다 |

- 채널 줄이 `7` 을 찍는다 — **복사본에 보냈는데 원본에서 받아진다.** 채널이 하나이기 때문이다.
- ★★★ 다섯 개의 `==` 가 그 판정을 **출력으로** 못 박는다.

```text
   &src.V      == &cp.V      : false   <- 칸이 둘
   &src.Arr[0] == &cp.Arr[0] : false   <- 칸이 둘
   &src.Sl[0]  == &cp.Sl[0]  : true    <- ★ 같은 칸
   src.P       == cp.P       : true    <- ★ 같은 주소
   src.Ch      == cp.Ch      : true    <- ★ 같은 채널
```

- ★ **주소를 안 찍고 `==` 만 물었다.** 알고 싶은 것은 「같나 다르나」뿐이고 주소는 흔들리는 칸이다
  (05번 주제가 같은 이유로 `A`·`B` 이름표를 썼다).
- ★★ 이것이 **얕은 복사**다. `cp := src` 는 **한 겹만** 복사한다.
  깊은 복사는 **손으로 써야 한다** — `slices.Clone`·`maps.Clone` 도 한 겹만 더 뜬다.
- 층 — 전부 **명세 보장**이다. 무엇이 복사되는지는 **타입이 정한다.**

### 3. `new` 는 다섯 줄 다 `*T`, `make` 는 세 줄 다 `T`

**출력**

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

**왜 그런가**

| 쓴 것 | 준 타입 | `*p` 또는 값 |
|---|---|---|
| `new(int)` | `*int` | `0` |
| `new(P)` | `*main.P` | `{0 0}` |
| `new([3]int)` | `*[3]int` | `[0 0 0]` |
| `new([]int)` | `*[]int` | `[]` — ★ **`*p == nil` 이 `true`** |
| `new(map[string]int)` | `*map[string]int` | `map[]` — ★ **`*p == nil` 이 `true`** |
| `make([]int,2,5)` | `[]int` | `[0 0]` · `len=2 cap=5` · `== nil` 이 **`false`** |
| `make(map[string]int)` | `map[string]int` | `map[]` · `== nil` 이 **`false`** |
| `make(chan int, 3)` | `chan int` | `cap=3` · `== nil` 이 **`false`** |

- 명세가 반환 타입을 못 박는다.

  > **The built-in function `new` creates a new, initialized variable and returns a pointer to it.**

  > **The built-in function `make` takes a type T, which must be a slice, map or channel type** …
  > **It returns a value of type T (not \*T).**

- ★ **`new([]int)` 는 그대로 쓸 수 있다** — 마지막 줄에서 `*d = append(*d, 1, 2)` 가 `[1 2]` 를 낸다.
  `nil` 슬라이스에 `append` 하는 것은 **합법**이다([05번 주제](../05-arrays-vs-slices-value-and-header/) (6)절).
  **`new(map[string]int)` 는 못 쓴다** — 쓰면 패닉이다(6번).
- ★★★ `make` 가 세 타입에만 있는 이유 — **그 셋만 제로값이 쓸 수 없는 상태**다.
  `nil` 맵에 쓰면 패닉하고 `nil` 채널은 영원히 막힌다.
  「제로값을 놓는 것」(`new`)으로는 모자라 **런타임 자료구조를 차리는 함수**가 따로 필요했다.
- 층 — 전부 **명세 보장**이다.

### 4. ★★ `IncVal()` 뒤에도 0 — 복사본을 고쳤다

**출력**

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

**왜 그런가**

- ★★★ **`c.IncVal()` 뒤에도 `c.n` 이 0**이다. 값 리시버 `c Counter` 는 **복사본**이고,
  `c.n++` 가 그 복사본을 고쳤다. **에러도 경고도 없다** — 이 주제에서 가장 조용한 자리다.
- 리시버도 매개변수이고, 명세가 인자 전달을 **대입**으로 정의하기 때문이다.

  > … the arguments of the call are passed to the function, which means that they are
  > **assigned to their corresponding function parameters**

- `c.IncPtr()` 뒤에는 1이다.
- ★ `p := &c` 로 바꿔 불러도 **결과가 같다** — `p.IncVal()` 은 `(*p).IncVal()` 로 풀려 역시 복사본을 만든다.
  **갈리는 것은 부르는 쪽이 아니라 리시버 선언**이다. 그래서 세 번째 줄이 1이 아니라 **2**다
  (`IncPtr` 만 한 번 더 먹혔다).
- 슬라이스 원소에서 `cs[0].IncPtr()` 이 되는 이유 — **슬라이스 인덱스는 addressable** 이라
  `(&cs[0]).IncPtr()` 로 자동 변환된다. `cs[1].IncVal()` 은 여전히 0이다.
  ★ **맵 원소였다면 그 자동 변환이 안 된다** — `&m["k"]` 가 애초에 컴파일 에러다(7번).
- 마지막 줄 — 값 리시버는 **1024바이트짜리 구조체도 복사한다.**
  ★ **그 비용은 안 쟀다.** 「복사가 일어난다」는 명세의 결과이고 「그래서 느리다」는 **측정이 필요한 주장**이다.
- 층 — 전부 **명세 보장**이다. 메서드 집합의 정본은 [목록의 **19번 주제**](../19-method-sets-value-vs-pointer-receiver/)다.

### 5. `{1}` / `{99}` / `{1}` / `{7}` — 포인터도 값이다

**출력**

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

**왜 그런가**

- `byValue(a)` 는 못 고친다 — 매개변수가 복사본이다.
- `byPtr(&b)` 는 고친다.
- ★★ `reseat(c)` 뒤 `*c` 가 **`{1}`** 이다. 함수 안에서 `p = &P{X: 7}` 을 했는데 밖에 안 보인다 —
  고친 것이 **포인터의 복사본**이기 때문이다. **포인터도 값**이다.
- `reseat2(&d)` 는 **포인터의 포인터**(`**P`)를 받아서 된다.
  ★ 이것이 05번 주제의 「함수 안의 `append` 가 안 보이는」 것과 **같은 모양**이다 —
  고쳐진 것이 「헤더의 복사본」이냐 「포인터의 복사본」이냐만 다르다.
- 슬라이스·맵은 값으로 넘겨도 내용이 보인다 — 2번의 표 그대로다.
- 마지막 줄 — **`append` 는 안 보인다.** `len` 이 2 그대로다.
  「내용은 보이는데 헤더는 안 보인다」가 슬라이스의 정확한 성질이다
  ([05번 주제](../05-arrays-vs-slices-value-and-header/) (3)절이 정본).
- 층 — 전부 **명세 보장**이다.

### 6. 빌드는 둘 다 성공 — 실행이 각각 다른 말로 죽는다

**출력**

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

**왜 그런가**

- 둘 다 **컴파일은 성공**한다(`(exit 0)`). 그래서 블록을 빌드와 실행으로 갈라 실었다.
- 첫째 — `panic: runtime error: invalid memory address or nil pointer dereference` +
  `[signal SIGSEGV: segmentation violation code=0x1 addr=0x0 pc=0x…]`.
  명세가 그것을 직접 적는다.

  > **If x is of pointer type and has the value nil and x.f denotes a struct field,
  > assigning to or evaluating x.f causes a run-time panic.**

- 둘째 — `panic: assignment to entry in nil map`.
  ★ **읽기는 된다** — `(*m)["a"]` 가 제로값 `0` 을 준다. `nil` 맵도 **읽을 수** 있다.
  **쓸 수만 없다.**
- ★★ 두 메시지가 다르다는 것이 **진단**이다 —
  앞엣것은 「**포인터가 `nil`**」, 뒤엣것은 「**맵을 `make` 안 했다**」는 뜻이다.
  같은 「`nil` 때문에 죽었다」인데 고치는 법이 전혀 다르다.
- **종료 코드는 둘 다 2**다.
- ★ 마커 줄을 **표준 오류로** 찍었다(`fmt.Fprintln(os.Stderr, …)`). 파이프로 받아도 자리가 안 바뀐다.
- 층 — 「패닉한다」는 **명세 보장**, **메시지 본문은 런타임(구현)** 이다.

### 7. 일곱 가지 전부 컴파일 에러

**출력**

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

**왜 그런가**

| 쓴 것 | 메시지 | 왜 막나 |
|---|---|---|
| `p++` | `invalid operation: p++ (non-numeric type *int)` | ★ **포인터 산술이 없다** |
| `p + 1` | `invalid operation: p + 1 (mismatched types *int and untyped int)` | 〃 |
| `&m["k"]` | `invalid operation: cannot take address of m["k"] (map index expression of struct type P)` | 맵 원소는 **addressable 이 아니다** |
| `make(P)` | `invalid argument: cannot make P: type must be slice, map, or channel` | ★ **메시지가 규칙을 그대로 말한다** |
| `make([]int)` | `invalid operation: make([]int) expects 2 or 3 arguments; found 1` | 슬라이스는 길이가 필요하다 |
| `new(int, 3)` | `invalid operation: too many arguments for new(int, 3) (expected 1, found 2)` | `new` 는 인자 하나 |
| `(*int)(&f)` | `cannot convert &f (value of type *float64) to type *int` | 포인터 타입 변환이 없다 |

- ★★★ **`p++` 가 막히는 것은 Go 에 포인터 산술이 없기 때문**이다.
  명세의 연산자 절 어디에도 포인터 덧셈이 없다. 그 자리를 **슬라이스와 인덱스**가 맡는다.
- **`&m["k"]` 가 막히는 설계 사정** — 맵이 자라면서 **원소를 다른 자리로 옮길 수 있어서** 주소가 안정적이지 않다.
  그래서 명세의 addressable 목록에 맵 인덱스가 **아예 없다**
  ([09번 주제](../09-maps-declaration-comma-ok-delete-and-iteration-order/)가 정본).
- 종료 코드는 **1**이다.
- 층 — 전부 **명세 보장**이다(에러 **문구**는 구현).

### 8. `*T` 와 `T` — 그리고 셋만 제로값이 못 쓸 상태다

**출력**

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

**왜 그런가**

- **`new(T)` 는 `*T`**, **`make(T, …)` 는 `T`** 를 돌려준다.
- `make` 가 받는 세 타입의 **공통점** — **제로값(`nil`)이 쓸 수 없는 상태**다.
  그래서 「변수를 놓는 것」만으로는 부족하고 **런타임 자료구조를 차리는** 단계가 따로 필요하다.
- 던져 봤다 — `new(chan int)` 로 만든 채널에 보내면
  **`fatal error: all goroutines are asleep - deadlock!`** 이고
  goroutine 줄이 이유를 댄다 — **`[chan send (nil chan)]`**.
- ★★★ **6번의 두 메시지와 낱말 하나가 다르다 — `panic:` 이 아니라 `fatal error:`** 다.
  그 차이가 중요한 이유는 **`fatal error` 는 `recover` 로 못 잡는다**는 것이다(27번 주제).
  「`nil` 때문에 죽었다」가 셋인데 **부류가 둘**이다.
- 세 줄로 묶으면 —
  **`nil` 포인터는 「주소가 잘못됐다」 · `nil` 맵은 「넣을 수 없다」 · `nil` 채널은 「영원히 기다린다」.**
- 다른 타입들이 `new` 로 충분한 이유 — **제로값이 이미 쓸 만하다.**
  `0`·`""`·`false`·`nil` 슬라이스·제로 구조체는 전부 그대로 쓸 수 있다
  ([02번 주제](../02-variable-declarations-and-zero-values/)의 「쓸 만한 제로값」이 이 주제로 이어진다).
- 층 — 「`nil` 채널 송신이 영원히 막힌다」는 **명세 보장**,
  그것이 `fatal error … deadlock!` 로 드러나는 것은 **런타임(구현)** 이다.

### 9. 셋 다 `*main.P` 이고 값이 `{0 0}` — 그런데 `a == b` 는 `false`

**출력**

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

**왜 그런가**

- `new(P)`·`&P{}`·`&P{X: 0, Y: 0}` 셋 다 **`*main.P`** 이고 가리키는 값이 **`{0 0}`** 이다.
  `reflect.TypeOf` 로 봐도 같다.
- ★ **`*a == *b` 는 `true`** (가리키는 값이 같다)인데 **`a == b` 는 `false`** (다른 곳에 놓였다)다.
  **「같은 값」과 「같은 칸」은 다른 물음**이다 — 이 주제 내내 반복되는 구분이다.
- **관용은 `&P{…}`** 다. 필드를 채워 만들 수 있기 때문이다.
  `new` 가 남는 자리는 **`&int{}` 라는 문법이 없는 기본 타입**(`new(int)`)이다.
- ★★★ 마지막 줄 — `escape()` 는 **지역 변수의 주소를 돌려준다.**
  C 라면 **대롱 포인터**가 되어 UB 인데, Go 는 **42를 그대로 읽어 준다.**
  변수의 수명이 **접근 가능성**으로 정해지기 때문이다.
  ★ 「스택이냐 힙이냐」는 **명세에 없는 낱말**이다 — 어디에 두느냐는 **구현**이고,
  그 판정을 보는 법은 [13번 주제](../13-closures-variable-capture-and-loop-variable-change/) (7)절에 있다
  (`moved to heap: x`).
- 층 — 「돌려줘도 된다」는 **명세 보장**, 「어디에 놓이나」는 **구현**이다.

### 10. C 의 포인터와 나란히

**출력** — 없음(연결 문항).

**왜 그런가**

| 물음 | **C** | **Go** | **Java** |
|---|---|---|---|
| 배열을 함수에 넘기면 | **감쇠** — 포인터가 되고 길이를 잃는다 | **복사** — 끝까지 `[N]T` | 배열은 객체 참조 |
| `p++` | 다음 원소로 **간다** | ★ **컴파일 에러** | 해당 없음 |
| 지역 변수의 주소를 돌려주면 | **대롱 포인터** — UB | ★ **된다** — 변수가 살아남는다 | 해당 없음 |
| 포인터 산술의 자리를 맡은 것 | — | **슬라이스 + 인덱스** | 배열 인덱스 |
| 구조체를 넘기면 | **복사**(값) | **복사**(값) | ★ **참조**(객체는 언제나) |
| 참조가 필요하면 | `*T` 를 적는다 | `*T` 를 적는다 | 적을 것이 없다(언제나 참조) |

- C 쪽 실측은 [`../../../c/syntax/16-array-pointer-decay-and-function-parameters/`](../../../c/syntax/16-array-pointer-decay-and-function-parameters/) 에 있다.
- ★ **자바와 갈리는 지점이 결정적이다.** 자바는 「객체면 참조」라 고민할 것이 없는데,
  Go 는 **구조체가 값**이라 「이 함수가 내 값을 고칠 수 있나」를 **매번 타입에서 읽어야** 한다.
  2번의 격자가 그 읽는 법이다.
- ★ Go 는 C 의 **두 위험**(감쇠로 길이를 잃는 것 · 대롱 포인터)을 **둘 다 없앴다** —
  앞엣것은 배열을 값으로 만들어서, 뒤엣것은 수명을 접근 가능성으로 정의해서.
  대신 **복사 비용**이라는 새 비용이 생겼고, 그것은 사람이 판단할 몫이다.

### 11. 다른 주제와 잇기

**출력** — 없음(연결 문항).

**왜 그런가**

- **배열이 값이고 슬라이스가 헤더인 것** — [05번 주제](../05-arrays-vs-slices-value-and-header/).
  **이 주제의 직접 선행**이고, 2번 격자의 두 줄이 거기서 나온다.
- **맵 원소가 주소를 못 잡는 것** — [09번 주제](../09-maps-declaration-comma-ok-delete-and-iteration-order/).
- **메서드 집합(값 리시버 대 포인터 리시버)** — [목록의 **19번 주제**](../19-method-sets-value-vs-pointer-receiver/).
  여기서는 「고쳐지나」 한 축만 봤고, 그쪽은 「**어떤 인터페이스를 만족하나**」를 본다.
- **지역 변수가 힙으로 가는지 보는 법** — [13번 주제](../13-closures-variable-capture-and-loop-variable-change/) (7)절,
  정본은 목록의 **52번 주제**.
- **「빠진 필드와 `null`」을 `*T` 로 가르는 관용구** — 목록의 **45번 주제**(`encoding/json`).
- 덤 — **제로값이 쓸 만한가**는 [02번 주제](../02-variable-declarations-and-zero-values/),
  **구조체의 비교 가능성·정렬**은 [목록의 **17번 주제**](../17-struct-literals-comparability-field-tags-and-sorting/),
  **`recover` 가 `fatal error` 를 못 잡는 것**은 [목록의 **27번 주제**](../27-panic-recover-and-where-to-use-them/)다.

---

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행 1회** | 재실행 결과가 `normalize-shaky.py` 로 **동일** |
| 판 확인 | `go version` · `go env GOOS GOARCH GOVERSION` | 1 | `go1.27.1 linux/amd64` |
| 포인터 기본 (`t16a`) | `go build && ./prog` | 1 | 10→20→30→40→50 · `p == q` 가 `true` |
| ★★★ 무엇이 복사되나 (`t16b`) | 〃 | 1 | 셋은 갈라지고 넷은 공유 · `==` 다섯 줄 |
| `new` 와 `make` (`t16c`) | 〃 | 1 | `new` 는 전부 `*T` · `make` 는 전부 `T` · `nil` 여부 갈림 |
| `new(T)` 와 `&T{}` (`t16d`) | 〃 | 1 | `*a == *b` 는 `true` · `a == b` 는 `false` · 지역 주소 반환 42 |
| ★★ 값 리시버 (`t16e`) | 〃 | 1 | `IncVal()` 뒤 **0** · 포인터로 불러도 같음 |
| `nil` 포인터 (`t16f`) | `go build` · `./prog 2>&1` | 2 | 빌드 0 · `invalid memory address …` · **exit 2** |
| `nil` 맵 (`t16g`) | 〃 | 2 | 읽기는 0 · 쓰기에서 `assignment to entry in nil map` · **exit 2** |
| ★ `nil` 채널 (`t16j`) | 〃 | 2 | **`fatal error: … deadlock!`** · `[chan send (nil chan)]` · **exit 2** |
| 거부되는 일곱 (`t16h`) | `go build` | 1 | 에러 **7건** · exit 1 |
| 함수 인자 (`t16i`) | `go build && ./prog` | 1 | `reseat` 는 안 보이고 `reseat2` 는 보임 · `append` 안 보임 |
| 형태 (`t16form`) | 〃 | 1 | 네 줄 |

**구현·환경에 달린 항목**(버전이 오르거나 타깃이 바뀌면 **다시 찍어야 하는** 것)

| 항목 | 무엇에 달렸나 |
|---|---|
| 패닉 첫 줄의 **`pc=0x…`** · 스택의 `goroutine N` · `+0x…` | **런타임·빌드 산출물.** 다시 빌드하면 달라질 수 있다 |
| 패닉·치명 오류의 **메시지 본문** | **런타임(구현)**. 명세는 「패닉한다」까지만 정한다 |
| **포인터가 8바이트인 것** | **플랫폼(64비트)** — 이 문서는 크기를 안 찍었다 |
| **지역 변수가 스택에 사나 힙에 사나** | **구현(gc)**. 명세에 그 낱말이 없다 |
| 값 리시버 복사의 **실제 비용** | ★ **안 쟀다.** 벤치마크가 없다(목록의 **50번 주제**) |
| 역참조·복사의 **실행 비용** | ★ **안 쟀다** |
| `new(123)` 처럼 **식을 인자로 주는 꼴** | **안 던졌다**(명세가 허용한다고만 확인) |
| **배열 포인터의 인덱싱**(`p[i]`·`len(p)`) | **안 던졌다** |
| 에러 메시지의 **문구 자체** | **툴체인 판(go1.27.1)** |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다.

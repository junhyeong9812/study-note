# go/syntax/16 — 포인터와 값 복사 의미론, `new` 와 `make` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> ★★★ **모든 문제에서 「이 대입이 무엇을 복사하나」를 먼저 적어라.** 답이 거기서 나온다.
> ★ **「값이 같다」와 「같은 칸이다」를 갈라서 답하라.** 이 주제는 그 둘이 자주 어긋난다.
> ★ **답마다 「그 값을 누가 보장하나」를 같이 적어라** — 명세인가, gc 구현인가, 이 판의 관찰인가.
> ★ C 를 안다면 **감쇠·포인터 산술·대롱 포인터** 세 직관을 먼저 의심하라.
> 소스는 전부 `go build -trimpath -o prog . && ./prog` 로 던졌다. 모듈 이름은 `ex` 다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 일곱 줄 (예측)

```go
// t16a.go
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
```

- 일곱 줄은 각각 무엇으로 찍히는가?
- `x = 30` 한 뒤 `*p` 가 그 값인 이유는 무엇인가?
- `p == q` 는 무엇인가 — 그 줄이 무엇을 증명하는가?
- 마지막 줄에서 `s.F` 와 `(*s).F` 가 같은 이유를 명세의 문장으로 답하라.

### 2. ★★★ 대입 한 줄 뒤 여섯 군데를 고쳤다 (예측)

```go
// t16b.go
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
```

- 「원본」 줄과 「복사본」 줄은 각각 무엇으로 찍히는가?
- 여섯 수정 중 **원본에 보이는 것**과 **안 보이는 것**을 갈라라.
- 채널 줄은 무엇을 찍는가 — 왜 그런가?
- 아래 다섯 개의 `==` 비교는 각각 무엇인가?

### 3. `new` 와 `make` 열 줄 (예측)

```go
// t16c.go
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
```

- `new` 다섯 줄은 각각 무슨 타입을 주고 `*p` 는 무엇인가?
- `make` 세 줄은 각각 무슨 타입을 주는가 — `== nil` 은?
- `new([]int)` 와 `new(map[string]int)` 중 **그대로 쓸 수 있는** 것은 어느 쪽인가?
- 왜 `make` 는 세 타입에만 있는가 — 그 셋의 공통점은 무엇인가?

### 4. ★★ 세 번 부른 메서드 (예측)

```go
// t16e.go
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
```

- 다섯 줄은 각각 무엇으로 찍히는가?
- `IncVal()` 뒤에 그 값이 나오는 이유는 무엇인가 — 에러나 경고가 나는가?
- `p := &c` 로 바꿔 불러도 결과가 같은가 — 갈리는 것은 무엇인가?
- 슬라이스 원소에서 `cs[0].IncPtr()` 이 되는 이유는 무엇인가 — 맵 원소였다면?

### 5. 함수 넷이 지나간 뒤 (예측)

```go
// t16i.go
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
```

- 여섯 줄은 각각 무엇으로 찍히는가?
- `reseat(c)` 뒤 `*c` 가 그 값인 이유는 무엇인가?
- `reseat2` 는 무엇을 더 받았기에 되는가?
- 마지막 두 줄에서 「내용은 보이는데 `append` 는 안 보이는」 이유는 무엇인가?

### 6. `nil` 을 건드리는 두 프로그램 (예측)

각각 빌드는 성공하는가? 실행하면 무엇이 나오는가?

```go
// t16f.go
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
```

```go
// t16g.go
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
```

- 두 프로그램의 **패닉 메시지 전문**은 각각 무엇인가?
- 두 메시지가 다르다는 사실에서 무엇을 진단할 수 있는가?
- 둘째 프로그램에서 **읽기**는 되는가?
- **종료 코드**는 각각 무엇인가?

### 7. 컴파일러가 거부하는 일곱 가지 (경계)

```go
// t16h.go
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
```

- 일곱 개의 메시지 전문은 각각 무엇인가?
- `p++` 가 막히는 것은 Go 가 무엇을 안 갖고 있기 때문인가?
- `&m["k"]` 가 막히는 이유는 무엇인가 — 어떤 설계 사정 때문인가?
- `make(P)` 의 메시지는 어떤 규칙을 그대로 말하는가?

### 8. 왜 `new` 와 `make` 둘인가 (왜)

- `new(T)` 와 `make(T)` 의 **반환 타입**이 각각 무엇인가?
- `make` 가 받는 세 타입의 **공통점**은 무엇인가?
- 아래 프로그램은 빌드되는가 — 실행하면 무엇이 나오는가?

```go
// t16j.go
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
```

- 그 메시지는 6번의 두 패닉과 **어떻게 다른가** — 낱말 하나가 다르다.
- 다른 타입들은 왜 `new` 로 충분한가?

### 9. `new(T)` 와 `&T{}` (경계)

```go
// t16d.go
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
```

- 처음 세 줄은 각각 무엇으로 찍히는가?
- `*a == *b` 와 `a == b` 가 다른 이유는 무엇인가?
- 둘 중 실무 관용은 어느 쪽인가 — `new` 가 남는 자리는 어디인가?
- 마지막 줄이 C 와 갈리는 자리다. 무엇이 갈리는가?

### 10. C 의 포인터와 나란히 (연결)

- C 에서 `int a[10]` 을 함수에 넘기면 무슨 일이 일어나는가 — Go 는?
- C 에서 `p++` 는 무엇을 하는가 — Go 는?
- C 에서 지역 변수의 주소를 돌려주면 무엇이 되는가 — Go 는?
- Go 에서 C 의 포인터 산술이 하던 일을 맡은 것은 무엇인가?
- 자바에서 객체를 넘기는 것과 Go 에서 구조체를 넘기는 것은 무엇이 다른가?

### 11. 다른 주제와 잇기 (연결)

- 배열이 값이고 슬라이스가 헤더인 것의 정본은 몇 번 주제인가?
- 맵 원소가 주소를 못 잡는 것의 정본은 몇 번 주제인가?
- 메서드 집합(값 리시버 대 포인터 리시버)의 정본은 몇 번 주제인가?
- 지역 변수가 힙으로 가는지 보는 법의 정본은 몇 번 주제인가?
- 「빠진 필드와 `null`」을 `*T` 로 가르는 관용구의 정본은 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

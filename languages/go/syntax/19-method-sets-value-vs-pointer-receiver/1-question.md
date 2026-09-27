# go/syntax/19 — ★ 메서드 집합: 값 리시버 대 포인터 리시버 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> ★★★ **모든 문제에서 격자를 먼저 그려라** — 세로는 `T`/`*T`, 가로는 값 리시버/포인터 리시버.
> **빈 칸은 하나뿐**이고, 이 주제의 모든 에러가 거기서 나온다.
> ★★★ **「부를 수 있나」와 「집합에 있나」를 갈라서 답하라.** 둘은 다른 물음이다.
> ★ **답마다 「그 값을 누가 보장하나」를 같이 적어라** — 이 주제는 **거의 전부 명세**다.
> ★ 이 주제는 **패닉이 한 번도 안 난다.** 틀리면 실행까지 못 간다 — 근거는 전부 **컴파일 에러**다.
> 소스는 전부 `go build -trimpath -o prog . && ./prog` 로 던졌다. 모듈 이름은 `ex` 다.
> 컴파일 에러를 전부 보려고 몇 블록은 `-gcflags=-e` 를 붙였다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 네 개의 대입 (예측)

```go
// t19a.go
package main

import "fmt"

type Speaker interface{ Speak() string }

// 값 리시버 하나
type V struct{ n int }

func (v V) Speak() string { return "V" }

// 포인터 리시버 하나
type P struct{ n int }

func (p *P) Speak() string { return "P" }

func main() {
	v := V{}
	p := P{}

	// 네 조합
	var i1 Speaker = v  // ① 값 리시버 · 값을 담는다
	var i2 Speaker = &v // ② 값 리시버 · 포인터를 담는다
	var i3 Speaker = &p // ③ 포인터 리시버 · 포인터를 담는다
	var i4 Speaker = p  // ④ 포인터 리시버 · 값을 담는다

	fmt.Println(i1.Speak(), i2.Speak(), i3.Speak(), i4.Speak())
}
```

- 컴파일러는 몇 개를 거부하는가 — 어느 것인가?
- 그 메시지 **전문**은 무엇인가?
- 괄호 안의 말이 이유를 하나 말해 준다. 무엇인가?
- 명세의 어느 두 문장이 이 결과를 만드는가?

### 2. ★★ 집합의 크기를 세면 (예측)

```go
// t19b.go
package main

import (
	"fmt"
	"reflect"
)

type Speaker interface{ Speak() string }

type V struct{ n int }

func (v V) Speak() string { return "V" }

type P struct{ n int }

func (p *P) Speak() string { return "P" }

type Mixed struct{ n int }

func (m Mixed) Val() string  { return "val" }
func (m *Mixed) Ptr() string { return "ptr" }

func methodNames(t reflect.Type) []string {
	out := make([]string, 0, t.NumMethod())
	for i := range t.NumMethod() {
		out = append(out, t.Method(i).Name)
	}
	return out
}

func main() {
	fmt.Println("── 메서드 집합의 크기를 세어 본다 ──")
	for _, t := range []reflect.Type{
		reflect.TypeOf(V{}), reflect.TypeOf(&V{}),
		reflect.TypeOf(P{}), reflect.TypeOf(&P{}),
		reflect.TypeOf(Mixed{}), reflect.TypeOf(&Mixed{}),
	} {
		fmt.Printf("  %-10v NumMethod=%d  %v\n", t, t.NumMethod(), methodNames(t))
	}

	fmt.Println("── 되는 세 조합을 실제로 담아 본다 ──")
	v := V{}
	p := P{}
	var i1 Speaker = v
	var i2 Speaker = &v
	var i3 Speaker = &p
	fmt.Printf("  ① Speaker = v   -> %T  %s\n", i1, i1.Speak())
	fmt.Printf("  ② Speaker = &v  -> %T  %s\n", i2, i2.Speak())
	fmt.Printf("  ③ Speaker = &p  -> %T  %s\n", i3, i3.Speak())

	fmt.Println("── 인터페이스가 만족되는지 런타임에 묻는 법 ──")
	st := reflect.TypeOf((*Speaker)(nil)).Elem()
	for _, t := range []reflect.Type{
		reflect.TypeOf(V{}), reflect.TypeOf(&V{}),
		reflect.TypeOf(P{}), reflect.TypeOf(&P{}),
	} {
		fmt.Printf("  %-10v Implements(Speaker) = %v\n", t, t.Implements(st))
	}
}
```

- 여섯 줄의 `NumMethod` 와 메서드 이름 목록은 각각 무엇인가?
- `main.P` 의 수가 그 값인 것이 왜 이상하게 느껴지는가 — 무엇을 선언했는데?
- `Mixed` 와 `*Mixed` 가 갈리는 이유는 무엇인가?
- 마지막 네 줄의 `Implements` 는 각각 무엇인가 — 1번의 답과 어떤 관계인가?

### 3. ★★★ 다섯 자리에서 같은 메서드를 부른다 (예측)

```go
// t19c.go
package main

import "fmt"

type C struct{ n int }

func (c *C) Inc()    { c.n++ }
func (c C) Get() int { return c.n }

type Speaker interface{ Speak() string }

func (c *C) Speak() string { return "C" }

func make1() C { return C{} }

func main() {
	m := map[string]C{"k": {}}
	m["k"].Inc() // ① 맵 원소 — 주소를 못 얻는다

	make1().Inc() // ② 함수 반환값 — 주소를 못 얻는다

	C{}.Inc() // ③ 복합 리터럴 그 자체 — 주소를 못 얻는다

	var i Speaker = m["k"] // ④ 맵 원소를 인터페이스에 — 메서드 집합이 모자란다
	fmt.Println(i)

	s := []C{{}}
	s[0].Inc() // ⑤ 슬라이스 원소는 된다
	fmt.Println(s[0].Get(), m["k"].Get())
}
```

- 컴파일러는 몇 줄을 거부하는가 — 메시지 전문은?
- 거부되지 **않은** 자리는 어디인가, 왜인가?
- ④의 메시지는 나머지 셋과 다르다. 무엇이 다르고 왜인가?
- 세 거부의 **공통 원인**을 한 낱말로 적어라.

### 4. 주소를 얻을 수 있는 자리들 (예측)

```go
// t19d.go
package main

import "fmt"

type C struct{ n int }

func (c *C) Inc()    { c.n++ }
func (c C) Get() int { return c.n }

func main() {
	fmt.Println("── 되는 자리 : 주소를 얻을 수 있는 피연산자 ──")
	var v C
	v.Inc() // (&v).Inc() 로 풀린다
	fmt.Println("  변수          :", v.Get())

	p := &C{}
	p.Inc() // 이미 포인터다
	p.Get() // (*p).Get() 으로 풀린다 — 반대 방향의 자동 변환
	fmt.Println("  포인터        :", p.Get())

	s := []C{{}}
	s[0].Inc()
	fmt.Println("  슬라이스 원소 :", s[0].Get())

	a := [1]C{}
	a[0].Inc()
	fmt.Println("  배열 원소     :", a[0].Get())

	st := struct{ In C }{}
	st.In.Inc()
	fmt.Println("  구조체 필드   :", st.In.Get())

	fmt.Println("── 맵 원소를 고치는 두 길 ──")
	m1 := map[string]C{"k": {}}
	tmp := m1["k"] // ① 꺼내고 고치고 다시 넣는다
	tmp.Inc()
	m1["k"] = tmp
	fmt.Println("  ① 꺼내 넣기   :", m1["k"].Get())

	m2 := map[string]*C{"k": {}} // ② 값 타입을 포인터로 둔다
	m2["k"].Inc()
	fmt.Println("  ② map[K]*V    :", m2["k"].Get())

	fmt.Println("── 값 메서드는 주소를 안 따지므로 맵 원소에서도 된다 ──")
	fmt.Println("  m1[\"k\"].Get() :", m1["k"].Get())
}
```

- 아홉 줄은 각각 무엇으로 찍히는가?
- `p.Get()` 이 되는 이유는 무엇인가 — 어느 방향의 자동 변환인가?
- 맵 원소를 고치는 두 길은 각각 무엇인가 — 어느 쪽이 관용인가?
- 마지막 줄은 왜 되는가?

### 5. ★★ 메서드를 변수에 담아 두면 (예측)

```go
// t19e.go
package main

import "fmt"

type C struct{ n int }

func (c *C) Inc()    { c.n++ }
func (c C) Get() int { return c.n }

func main() {
	fmt.Println("── 메서드 값 : 리시버가 그 자리에서 평가된다 ──")
	c := C{n: 1}
	getVal := c.Get // 값 리시버 — 지금의 c 를 복사해 묶는다
	incPtr := c.Inc // 포인터 리시버 — &c 를 묶는다

	c.n = 100
	fmt.Println("  c.n 을 100 으로 바꾼 뒤")
	fmt.Println("    getVal() =", getVal(), " ← 묶일 때의 복사본이다")
	fmt.Println("    c.Get()  =", c.Get())
	incPtr()
	fmt.Println("    incPtr() 뒤 c.n =", c.n, " ← 이쪽은 원본을 본다")

	fmt.Println("── 메서드 표현식 : 리시버가 첫 인자가 된다 ──")
	fGet := C.Get
	fInc := (*C).Inc
	fmt.Printf("    C.Get    의 타입 : %T\n", fGet)
	fmt.Printf("    (*C).Inc 의 타입 : %T\n", fInc)
	fmt.Println("    fGet(C{n: 7}) =", fGet(C{n: 7}))
	d := C{}
	fInc(&d)
	fmt.Println("    fInc(&d) 뒤 d.n =", d.n)

	fmt.Println("── 값 리시버 메서드는 *C 에서도 꺼낼 수 있다 ──")
	e := &C{n: 5}
	fmt.Printf("    (*C).Get 의 타입 : %T\n", (*C).Get)
	fmt.Println("    e.Get() =", e.Get())
}
```

- 아홉 줄은 각각 무엇으로 찍히는가?
- `getVal()` 이 그 값인 이유를 명세의 한 문장으로 답하라.
- `C.Get`·`(*C).Inc`·`(*C).Get` 의 타입은 각각 무엇인가?
- `C.Inc` 는 되는가 — 왜인가?

### 6. ★ 뮤텍스를 품은 타입의 두 메서드 (예측)

```go
// t19f.go
package main

import (
	"fmt"
	"sync"
)

// 뮤텍스를 품은 타입에 값 리시버를 달면 잠금이 복사된다
type Safe struct {
	mu sync.Mutex
	n  int
}

func (s Safe) BadInc() { // 값 리시버 — 잠금째 복사된다
	s.mu.Lock()
	defer s.mu.Unlock()
	s.n++
}

func (s *Safe) GoodInc() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.n++
}

func main() {
	var s Safe
	s.BadInc()
	s.GoodInc()
	fmt.Println(s.n)
}
```

- `go build` 는 성공하는가?
- `go vet ./...` 은 무엇을 말하는가 — **전문과 종료 코드**는?
- `BadInc` 가 실제로 무엇을 잠그는가?
- 이 진단이 리시버를 고르는 기준 하나를 준다. 무엇인가?

### 7. 도구는 무엇을 말해 주는가 (경계)

2번 프로그램이 있는 디렉토리에서 `go doc -all .` 을 던졌다.

- 출력에서 **리시버의 꼴**을 읽을 수 있는가?
- 「`V` 가 `Speaker` 를 만족한다」는 출력 어디에 있는가?
- 그 사실을 알려면 사람이 무엇을 해야 하는가?
- 코드에서 그것을 **컴파일러에게 시키는** 관용구가 있다. 무엇인가?

### 8. 「부를 수 있다」와 「집합에 있다」 (왜)

- 두 물음은 각각 무엇을 보는가?
- `var v T; v.PtrM()` 이 되는 근거가 되는 명세의 문장은?
- `var i I = v` 가 안 되는 근거가 되는 명세의 문장은?
- 두 물음이 **같아지는** 경우가 있는가 — 어떤 경우인가?

### 9. 어느 쪽을 고르나 (경계)

- 리시버를 **고치는** 메서드는 어느 쪽인가?
- `sync.Mutex` 를 품은 타입은 어느 쪽인가 — 근거는 무엇으로 확인했는가?
- 한 타입 안에서 값과 포인터를 섞으면 무엇이 생기는가?
- 「리시버가 크니까 포인터」는 무엇이 더 필요한 주장인가?
- 값으로도 인터페이스에 담고 싶으면 어느 쪽이어야 하는가?

### 10. 다른 언어와 나란히 (연결)

- Rust 에서 「이 타입이 이 트레이트를 구현한다」를 적는 곳은 어디인가 — Go 는?
- Rust 의 `&self`/`&mut self`/`self` 와 Go 의 값·포인터 리시버는 무엇이 대응하는가?
- 자바에 값 리시버와 포인터 리시버의 갈림이 있는가 — 왜인가?
- Go 에서 틀렸다는 사실이 **어느 자리에서** 드러나는가 — Rust 는?

### 11. 다른 주제와 잇기 (연결)

- 「값 리시버가 복사본을 고친다」의 정본은 몇 번 주제인가?
- addressable 의 정본은 몇 번 주제인가?
- 임베딩이 메서드 집합을 키우는 것의 정본은 몇 번 주제인가?
- 「복사하면 안 되는 타입」의 정본은 몇 번 주제인가?
- 인터페이스에 담긴 뒤에 생기는 `nil` 함정은 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

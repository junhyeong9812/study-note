# go/syntax/19 — ★ 메서드 집합: 값 리시버 대 포인터 리시버 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> 블록은 전부 `===== 소스: … =====` 로 소스를 먼저 싣는다 — **그대로 다시 던질 수 있게** 하기 위해서다.
> ★ **근거로 읽을 칸** — 컴파일 에러 문장과 `파일:줄:칸`, `NumMethod` 와 메서드 이름,
> `Implements` 의 참거짓, `%T` 가 찍는 타입 이름, `go vet` 의 진단 줄, 종료 코드.
> **근거로 읽지 않을 칸** — `go vet` 이 **무엇까지 잡나**(도구의 검사 목록은 판마다 다르다).
> ★★ 이 주제는 **패닉이 한 번도 안 난다** — 흔들리는 주소·스택이 아예 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 넷 중 하나만 막힌다 — 격자의 빈 칸

**출력**

```text
===== 소스: t19a.go =====
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
===== 명령: go build -trimpath -gcflags=-e -o prog . =====
# ex
./t19a.go:25:19: cannot use p (variable of struct type P) as Speaker value in variable declaration: P does not implement Speaker (method Speak has pointer receiver)
(exit 1)
```

**왜 그런가**

- **거부되는 것은 ④ 하나**다(`./t19a.go:25:19`).

| # | 리시버 | 담은 것 | 결과 |
|---|---|---|---|
| ① | 값 `func (v V)` | `v`(값) | **된다** |
| ② | 값 `func (v V)` | `&v`(포인터) | **된다** |
| ③ | 포인터 `func (p *P)` | `&p`(포인터) | **된다** |
| ④ | 포인터 `func (p *P)` | `p`(값) | ★ **막힌다** |

- 메시지 전문 —

  > `cannot use p (variable of struct type P) as Speaker value in variable declaration:
  > P does not implement Speaker (method Speak has pointer receiver)`

- ★★★ 괄호 안의 **`method Speak has pointer receiver`** 가 이유다.
  「그런 메서드가 없다」가 아니라 「**있는데 값의 집합에는 없다**」는 뜻이다.
  ★ 이 구분이 이 주제의 전부다 — 메서드는 분명히 선언되어 있다.
- 명세의 두 문장이 이 결과를 만든다.

  > **The method set of a defined type T consists of all methods declared with receiver type T.**

  > **The method set of a pointer to a defined type T** (where T is neither a pointer nor an interface)
  > **is the set of all methods declared with receiver \*T or T.**

  앞 문장에 `\*T` 가 **없다.** 그 없음이 격자의 빈 칸이고 이 에러다.
  그리고 만족의 정의가 그 집합을 본다 —
  "A type T implements an interface I if **T … is an element of the type set of I**."
- ★★ 층 — **전부 명세 보장**이다. 「gc 가 그렇게 한다」가 아니다. 판 경계도 없다.

### 2. ★★ `main.P` 의 집합이 비어 있다

**출력**

```text
===== 소스: t19b.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
── 메서드 집합의 크기를 세어 본다 ──
  main.V     NumMethod=1  [Speak]
  *main.V    NumMethod=1  [Speak]
  main.P     NumMethod=0  []
  *main.P    NumMethod=1  [Speak]
  main.Mixed NumMethod=1  [Val]
  *main.Mixed NumMethod=2  [Ptr Val]
── 되는 세 조합을 실제로 담아 본다 ──
  ① Speaker = v   -> main.V  V
  ② Speaker = &v  -> *main.V  V
  ③ Speaker = &p  -> *main.P  P
── 인터페이스가 만족되는지 런타임에 묻는 법 ──
  main.V     Implements(Speaker) = true
  *main.V    Implements(Speaker) = true
  main.P     Implements(Speaker) = false
  *main.P    Implements(Speaker) = true
(exit 0)
```

**왜 그런가**

| 타입 | `NumMethod` | 이름 |
|---|---|---|
| `main.V` | 1 | `[Speak]` |
| `*main.V` | 1 | `[Speak]` |
| **`main.P`** | ★ **0** | `[]` |
| `*main.P` | 1 | `[Speak]` |
| `main.Mixed` | 1 | `[Val]` |
| `*main.Mixed` | 2 | `[Ptr Val]` |

- ★★★ **`main.P` 가 0이다.** `func (p *P) Speak()` 를 **분명히 선언했는데** 집합이 비어 있다.
  「선언한 메서드 수」와 「그 타입의 집합 크기」는 **다른 수**다.
- `V` 는 값 리시버라 `V` 와 `*V` 가 **둘 다 1** 이다 — 격자의 왼쪽 세로줄 그대로다.
- `Mixed` 는 둘을 섞었다 — **값 리시버 `Val` 은 양쪽에, 포인터 리시버 `Ptr` 은 `*Mixed` 에만** 든다.
  ★ 그래서 한 타입 안에서 **리시버를 섞으면 집합이 둘로 갈린다.**
- 마지막 네 줄 — `Implements(Speaker)` 가
  `main.V` **`true`** · `*main.V` **`true`** · `main.P` **`false`** · `*main.P` **`true`** 다.
  ★★ **1번의 컴파일 에러와 정확히 같은 답**이다. 다른 것은 **시점**뿐이다 —
  컴파일러는 빌드에서, `reflect` 는 실행에서 같은 판정을 낸다.
- ★ `reflect` 의 메서드 목록은 **이름 오름차순**(`[Ptr Val]`)이라 정렬이 필요 없다 — 패키지의 계약이다.
- 층 — 집합 규칙은 **명세 보장**, 이름 순서는 **`reflect` 의 계약**이다.

### 3. ★★★ 셋이 막힌다 — 원인은 「주소를 못 얻는다」

**출력**

```text
===== 소스: t19c.go =====
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
===== 명령: go build -trimpath -gcflags=-e -o prog . =====
# ex
./t19c.go:18:9: cannot call pointer method Inc on C
./t19c.go:20:10: cannot call pointer method Inc on C
./t19c.go:22:6: cannot call pointer method Inc on C
./t19c.go:24:18: cannot use m["k"] (map index expression of struct type C) as Speaker value in variable declaration: C does not implement Speaker (method Speak has pointer receiver)
(exit 1)
```

**왜 그런가**

- **네 줄이 거부된다** — 그중 셋이 같은 문장이다.

  > `cannot call pointer method Inc on C` — 맵 원소(`m["k"].Inc()`) · 함수 반환값(`make1().Inc()`) ·
  > 복합 리터럴(`C{}.Inc()`)

- 거부되지 **않은** 자리는 **⑤ 슬라이스 원소**(`s[0].Inc()`)다 — 에러 목록에 그 줄이 **없다.**
  슬라이스 인덱스는 **addressable** 이기 때문이다.
- ★★ **④는 문구가 다르다** —

  > `cannot use m["k"] (map index expression of struct type C) as Speaker value in variable declaration:
  > C does not implement Speaker (method Speak has pointer receiver)`

  **호출이 아니라 대입**이라 1번과 같은 에러가 나오고, 앞에 **`map index expression of struct type C`**
  로 **어디서 온 값인지**까지 밝힌다.
  ★ 즉 **같은 원인이 두 얼굴**로 나온다 — 부르려 하면 `cannot call pointer method`,
  담으려 하면 `does not implement`.
- **공통 원인은 한 낱말로 `addressable`** 이다. 명세:

  > **If x is addressable and &x's method set contains m, x.m() is shorthand for (&x).m().**

  addressable 의 목록은 [16번 주제](../16-pointers-value-copy-semantics-new-and-make/)가 정본이고,
  거기에 **맵 인덱스가 없다.**
- 층 — **전부 명세 보장**이다.

### 4. 자동 변환은 양방향이다

**출력**

```text
===== 소스: t19d.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
── 되는 자리 : 주소를 얻을 수 있는 피연산자 ──
  변수          : 1
  포인터        : 1
  슬라이스 원소 : 1
  배열 원소     : 1
  구조체 필드   : 1
── 맵 원소를 고치는 두 길 ──
  ① 꺼내 넣기   : 1
  ② map[K]*V    : 1
── 값 메서드는 주소를 안 따지므로 맵 원소에서도 된다 ──
  m1["k"].Get() : 1
(exit 0)
```

**왜 그런가**

- **변수·슬라이스 원소·배열 원소·구조체 필드**에서 전부 `Inc()` 가 되어 **1**이 나온다 —
  `(&x).Inc()` 로 풀리기 때문이다.
- ★ **`p.Get()` 은 반대 방향**이다 — `(*p).Get()` 으로 **자동 역참조**된다. 명세:

  > As with selectors, a reference to a non-interface method with a value receiver using a pointer
  > will **automatically dereference that pointer**.

  ★★ 그래서 **포인터를 들고 있으면 양쪽 다 부를 수 있다.** 걱정은 **값을 들고 있을 때**만 생긴다.
- **맵 원소를 고치는 두 길** —
  ① `tmp := m1["k"]; tmp.Inc(); m1["k"] = tmp` — 꺼내 고치고 다시 넣는다.
  ② `map[string]*C` — 값 타입을 포인터로 둔다. **이쪽이 관용**이다(16번 주제의 결론과 같다).
- 마지막 줄 `m1["k"].Get()` 이 되는 이유 — **값 메서드는 주소를 안 따진다.**
  맵 원소로도 메서드 집합(`C` 의 집합)에 있고, 복사본을 받아 읽기만 하면 되기 때문이다.
  ★ **막히는 것은 포인터 메서드뿐**이다.
- 층 — **전부 명세 보장**이다.

### 5. ★★ 메서드 값은 리시버를 그 자리에서 저장한다

**출력**

```text
===== 소스: t19e.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
── 메서드 값 : 리시버가 그 자리에서 평가된다 ──
  c.n 을 100 으로 바꾼 뒤
    getVal() = 1  ← 묶일 때의 복사본이다
    c.Get()  = 100
    incPtr() 뒤 c.n = 101  ← 이쪽은 원본을 본다
── 메서드 표현식 : 리시버가 첫 인자가 된다 ──
    C.Get    의 타입 : func(main.C) int
    (*C).Inc 의 타입 : func(*main.C)
    fGet(C{n: 7}) = 7
    fInc(&d) 뒤 d.n = 1
── 값 리시버 메서드는 *C 에서도 꺼낼 수 있다 ──
    (*C).Get 의 타입 : func(*main.C) int
    e.Get() = 5
(exit 0)
```

**왜 그런가**

- ★★★ `c.n` 을 100으로 바꾼 뒤에도 **`getVal()` 은 1**이고 `c.Get()` 은 **100**이다. 명세:

  > The expression x is **evaluated and saved during the evaluation of the method value**;
  > **the saved copy is then used as the receiver** in any calls, which may be executed later.

  ★ 값 리시버라 **저장된 것이 복사본**이다. 그래서 나중에 불러도 **묶일 때의 값**을 본다.
- **포인터 리시버 쪽은 `&c` 를 묶는다** — `incPtr()` 뒤 `c.n` 이 **101**이다.
  ★ **같은 문법 두 줄이 정반대로 군다.** 갈리는 것은 **리시버 선언**이다.
- 메서드 표현식의 타입 —

| 식 | 타입 |
|---|---|
| `C.Get` | `func(main.C) int` |
| `(*C).Inc` | `func(*main.C)` |
| `(*C).Get` | `func(*main.C) int` |

  ★ **`(*C).Get` 이 있다**는 것이 요점이다 — 값 리시버 메서드는 `*C` 의 집합에도 있으므로
  포인터를 받는 함수로도 뽑힌다.
- **`C.Inc` 는 안 된다.** 명세가 illegal 이라 적는다.

  > The final case, **a value-receiver function for a pointer-receiver method, is illegal**
  > because pointer-receiver methods are not in the method set of the value type.

  ★ 격자의 빈 칸이 **여기서 한 번 더** 나온다. 이 문서는 그 에러를 **안 던졌다**(명세 인용만).
- 층 — **전부 명세 보장**이다.

### 6. 컴파일러는 통과시키고 `go vet` 이 잡는다

**출력**

```text
===== 소스: t19f.go =====
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
===== 명령: go build -trimpath -o prog . =====
(exit 0)
```

```text
===== 명령: go vet ./... =====
t19f.go:14:9: BadInc passes lock by value: ex.Safe contains sync.Mutex
(exit 1)
```

**왜 그런가**

- **`go build` 는 성공**한다(exit 0). 문법도 타입도 맞기 때문이다.
- `go vet ./...` 이 잡는다 —
  **`t19f.go:14:9: BadInc passes lock by value: ex.Safe contains sync.Mutex`**, **종료 코드 1**.
- ★★ **`BadInc` 가 잠그는 것은 복사본의 잠금**이다. 리시버가 값이라 `sync.Mutex` 까지 복사됐고,
  그 복사본을 잠갔다 풀 뿐이다. **원본은 아무도 안 지킨다.**
  16번 주제의 「복사본을 고친다」가 여기서는 **「복사본을 잠근다」** 로 나타난다.
- ★ 기준 하나 — **복사되면 안 되는 것이 들어 있으면 포인터 리시버**다.
  `sync.Mutex`·`sync.WaitGroup`·`strings.Builder`·`atomic.*` 이 그 부류다.
- ★★ 그리고 **`vet` 이 잡아 주는 것은 이 한 자리뿐**이다 —
  1번의 대입 실패는 **컴파일러**가, 16번의 「안 고쳐짐」은 **아무도** 안 잡는다.
- 층 — 「복사된다」는 **명세 보장**, 「`vet` 이 잡는다」는 **도구(구현)** 다.

### 7. `go doc` 은 리시버를 보여 주고 만족은 안 보여 준다

**출력**

```text
===== 명령: go doc -all . =====


TYPES

type Mixed struct {
	// Has unexported fields.
}

func (m *Mixed) Ptr() string

func (m Mixed) Val() string

type P struct {
	// Has unexported fields.
}

func (p *P) Speak() string

type Speaker interface{ Speak() string }

type V struct {
	// Has unexported fields.
}

func (v V) Speak() string
(exit 0)
```

**왜 그런가**

- **리시버의 꼴은 그대로 읽힌다** — `func (p *P) Speak() string` · `func (v V) Speak() string` ·
  `func (m *Mixed) Ptr() string` · `func (m Mixed) Val() string`.
  「이 메서드가 포인터 리시버인가」는 이것으로 판정한다.
- ★★★ **「`V` 가 `Speaker` 를 만족한다」는 출력 어디에도 없다.**
  `Speaker`·`V`·`P`·`Mixed` 가 **이름 오름차순으로 나란히** 있을 뿐이고,
  누가 누구를 만족하는지는 **한 줄도 안 나온다.**
  ★ 이 「없음」 자체가 근거다 — **암묵 구현이라 도구가 그 관계를 안 들고 있다.**
- 그 사실을 알려면 사람이 **메서드 목록을 인터페이스와 맞춰 봐야** 한다 —
  이름·인자·반환을 하나씩. 그리고 **리시버 꼴까지** 봐야 한다.
- ★★ 코드에서 그것을 **컴파일러에게 시키는 관용구**가 있다 —
  **`var _ Iface = (*T)(nil)`**. 정본은
  [20번 주제](../20-interface-declaration-and-implicit-implementation/) (2)절이다.
- 층 — `go doc` 의 차례와 꼴은 **도구(구현)**, 「만족 목록이 없다」는 **언어 설계의 결과**다.

### 8. 두 물음은 무엇을 보는가

**출력** — 없음(왜 문항).

**왜 그런가**

```text
   「부를 수 있나」                        「집합에 있나」

   보는 것 : x 가 addressable 인가         보는 것 : 그 타입의 메서드 집합
   쓰는 곳 : x.M()                         쓰는 곳 : 인터페이스 대입·타입 파라미터
   되는 예 : var v T; v.PtrM()             되는 예 : var i I = &v
   막힘    : cannot call pointer method    막힘    : does not implement (… pointer receiver)
```

- **「부를 수 있나」의 근거** —

  > A method call x.m() is valid if the method set of (the type of) x contains m … .
  > **If x is addressable and &x's method set contains m, x.m() is shorthand for (&x).m().**

  ★ 뒷문장이 **`*T` 의 집합을 빌려 쓰게** 해 준다. 그래서 `v.PtrM()` 이 된다.
- **「집합에 있나」의 근거** —

  > The method set of a defined type T consists of all methods declared with receiver type T.

  ★ 인터페이스 대입에는 **빌려 쓰는 규칙이 없다.** `T` 의 집합만 본다.
- ★★ **둘이 같아지는 경우** — **피연산자가 이미 포인터일 때**다.
  `p := &v` 를 들고 있으면 `p.M()` 도 되고 `var i I = p` 도 된다 — `*T` 의 집합 하나만 보면 된다.
  ★ 그래서 **「포인터로 들고 다니면 고민이 사라진다」** 가 실무의 요령이 된다.
- ★ **왜 인터페이스 대입에는 빌려 쓰기가 없나** — 대입은 **값을 복사해 담는** 일이라
  담긴 뒤에는 **원본이 어디 있는지 알 수 없다.** 주소를 몰래 만들어 담으면
  「내가 담은 값」과 「인터페이스가 들고 있는 것」이 달라진다.
  (이 문단은 명세의 문장이 아니라 **설계 해석**이다 — 명세는 규칙만 적고 이유를 안 적는다.)
- 층 — 두 규칙 다 **명세 보장**, 마지막 해석은 **명세에 없는 설명**이다.

### 9. 어느 쪽을 고르나

**출력** — 없음(경계 문항).

**왜 그런가**

| 물음 | 답 | 근거 |
|---|---|---|
| 리시버를 **고치는** 메서드 | **포인터 리시버** | [16번 주제](../16-pointers-value-copy-semantics-new-and-make/) (5)절 — 값이면 복사본을 고친다 |
| `sync.Mutex` 를 품은 타입 | **포인터 리시버** | 6번 — `go vet` 이 `passes lock by value` 로 잡는다 |
| 값과 포인터를 **섞으면** | 집합이 **둘로 갈린다** | 2번 — `Mixed` 1개, `*Mixed` 2개 |
| 「크니까 포인터」 | **측정이 더 필요하다** | 이 문서는 안 쟀다([목록의 **50번 주제**](../50-benchmarks-testing-b-and-reading-profiles/)) |
| 값으로도 인터페이스에 담고 싶다 | **값 리시버** | 1번 — 값 리시버라야 `T` 의 집합에 든다 |

- ★★ 실무의 규칙 한 줄은 **「하나라도 고치는 메서드가 있으면 전부 포인터 리시버로 통일한다」** 이다.
  그러면 집합이 하나로 모이고, 2번의 갈림도 1번의 에러도 안 생긴다.
- ★ 반대로 **작고 불변인 값**(시각·좌표·ID·`error` 값)은 값 리시버가 낫다 —
  `*T` 를 만들 필요가 없어 **값으로 그냥 담기기** 때문이다.
- ★ **「크니까 느리다」를 근거로 쓰지 마라** — 이 문서는 벤치마크를 한 번도 안 돌렸다.
  「복사가 일어난다」는 명세의 결과이고 「그래서 느리다」는 **측정이 필요한 주장**이다.

### 10. 다른 언어와 나란히

**출력** — 없음(연결 문항).

**왜 그런가**

| 물음 | **Go** | **Rust** | **Java** |
|---|---|---|---|
| 구현을 적는 곳 | ★ **없다** — 메서드만 선언한다 | `impl Trait for T { … }` | `implements I` |
| 리시버의 꼴 | `func (t T)` / `func (t *T)` | `self` / `&self` / `&mut self` | 언제나 참조(`this`) |
| 「고칠 수 있나」 | 포인터 리시버 | `&mut self` | 언제나 고칠 수 있다 |
| 집합이 둘로 갈리나 | ★ **갈린다**(`T` 와 `*T`) | 갈리지 않는다 — `impl` 이 한 덩어리 | 갈리지 않는다 |
| 틀린 것이 드러나는 자리 | ★ **대입·호출하는 자리** | **`impl` 블록 자체**(선언 자리) | **선언 자리** |

- ★★★ **결정적인 갈림은 마지막 줄이다.**
  Rust 는 `impl Trait for T` 를 적으므로 **빠진 메서드가 선언 자리에서** 드러난다
  (Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **25번**).
  Go 는 적는 곳이 없으니 **쓰는 자리에 가서야** 드러난다 —
  그래서 7번의 관용구(`var _ Iface = (*T)(nil)`)가 **선언 자리를 인공으로 만드는** 일을 한다.
- Rust 의 `&mut self` 가 Go 의 포인터 리시버에 대응하는데,
  **Rust 는 집합이 안 갈린다** — `impl` 안에 `self`·`&self`·`&mut self` 가 섞여 있어도
  타입이 트레이트를 구현하는지는 **`impl` 한 덩어리**로 정해진다.
  Go 는 **리시버마다 집합이 갈리므로** 격자가 생긴다.
- 자바에는 이 갈림이 **없다.** 객체가 언제나 참조라 「값 리시버」가 성립하지 않는다 —
  `this` 는 늘 원본을 가리킨다. 자바에서 온 사람은 **격자 자체를 처음 만난다.**

### 11. 다른 주제와 잇기

**출력** — 없음(연결 문항).

**왜 그런가**

- **「값 리시버가 복사본을 고친다」** — [16번 주제](../16-pointers-value-copy-semantics-new-and-make/) (5)절.
  **이 주제의 직접 선행**이다. 거기는 **「고쳐지나」** 한 축만 봤고, 여기는 **「담기나」** 를 본다.
- **addressable** — 같은 [16번 주제](../16-pointers-value-copy-semantics-new-and-make/)가 정본이고,
  맵 원소 쪽은 [09번 주제](../09-maps-declaration-comma-ok-delete-and-iteration-order/)다.
- **임베딩이 메서드 집합을 키우는 것** — [18번 주제](../18-embedding-and-field-method-promotion/) (6)절.
  `ByValue` 1개 대 `ByPtr` 2개가 그 실측이다.
- **「복사하면 안 되는 타입」** — [목록의 **32번 주제**](../32-sync-mutex-rwmutex-waitgroup-once/)(`sync`). 6번이 그 한 자리다.
- **인터페이스에 담긴 뒤의 `nil` 함정** — [목록의 **21번 주제**](../21-nil-interface-vs-interface-holding-nil-pointer/).
  맛보기는 [20번 주제](../20-interface-declaration-and-implicit-implementation/) (3)절에 있다.
- 덤 — **암묵 구현과 만족 단언**은 [20번 주제](../20-interface-declaration-and-implicit-implementation/),
  **타입 파라미터에서 같은 에러가 나는 것**은 [목록의 **37번 주제**](../37-generics-type-parameters-and-constraint-interfaces/),
  **`String()` 의 리시버가 출력에 보이는 자리**는 [목록의 **42번 주제**](../42-fmt-verbs-stringer-and-errorf/)다.

---

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행 1회** | 재실행 결과가 `normalize-shaky.py` 로 **동일** |
| 판 확인 | `go version` | 1 | `go1.27.1 linux/amd64` |
| ★★★ 네 조합 (`t19a`) | `go build -trimpath -gcflags=-e` | 1 | 에러 **1건**(④만) · `method Speak has pointer receiver` · exit 1 |
| ★★ 집합의 크기 (`t19b`) | `go build && ./prog` | 1 | `main.P` 가 **0** · `Implements` 가 `main.P` 만 `false` |
| `go doc` (`t19b`) | `go doc -all .` | 1 | 리시버는 보이고 **만족 목록은 없다** · exit 0 |
| ★★★ 주소를 못 얻는 값 (`t19c`) | `go build -gcflags=-e` | 1 | 에러 **4건** · 슬라이스 원소는 통과 · exit 1 |
| 되는 자리 (`t19d`) | `go build && ./prog` | 1 | 아홉 줄 전부 1 · `map[K]*V` 가 관용 |
| ★★ 메서드 값 (`t19e`) | 〃 | 1 | `getVal()`=1 · `c.Get()`=100 · `c.n`=101 |
| `vet` 의 한 자리 (`t19f`) | `go build` · `go vet ./...` | 2 | 빌드 exit 0 · `passes lock by value` · **vet exit 1** |
| 형태 (`t19form`) | `go build && ./prog` | 1 | 세 줄 |

**구현·환경에 달린 항목**(버전이 오르거나 타깃이 바뀌면 **다시 찍어야 하는** 것)

| 항목 | 무엇에 달렸나 |
|---|---|
| 컴파일 에러의 **문구 자체** | **툴체인 판(go1.27.1)**. 규칙은 명세, 문장은 gc 의 것 |
| `go vet` 이 **무엇까지 잡나** | **도구(구현)**. 검사 목록은 판마다 넓어질 수 있다 |
| `go doc -all .` 의 **차례와 꼴** | **도구(구현)** |
| `reflect` 가 메서드를 **이름 오름차순**으로 주는 것 | **`reflect` 의 계약** |
| 값 리시버 복사의 **실제 비용** | ★ **안 쟀다**([목록의 **50번 주제**](../50-benchmarks-testing-b-and-reading-profiles/)) |
| 인터페이스에 담을 때 **할당이 생기나** | ★ **안 쟀다** · 구현(gc)의 영역이다 |
| `C.Inc`(메서드 표현식)의 에러 | ★ **안 던졌다**(명세가 illegal 이라 적는다) |
| 인터페이스에 메서드를 다는 에러 | ★ **안 던졌다** |
| 다른 패키지 타입에 메서드를 다는 에러 | ★ **안 던졌다**(명세 인용만) |
| 메서드 이름과 필드 이름 충돌 | ★ **안 던졌다** |
| `reflect.Value.CanAddr` 로 addressable 을 묻는 법 | ★ **안 던졌다** |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다.

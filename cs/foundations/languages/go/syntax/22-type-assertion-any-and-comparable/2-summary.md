# go/syntax/22 — 타입 단언·`any`·`comparable` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Go 명세](https://go.dev/ref/spec) 의 Type assertions · Type switches ·
> Comparison operators · General interfaces · Satisfying a type constraint 절.
> 웹이 아니라 **이 툴체인이 들고 있는 `$(go env GOROOT)/doc/go_spec.html` 을 열어** 인용했고,
> 그 파일의 머리는 「**Language version go1.27 (May 26, 2026)**」이다.\
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> **버전** — 단언과 타입 스위치는 **1.0부터 같다.** 판 경계는 둘이다 —
> **`any` 라는 이름이 1.18부터**이고, **`comparable` 도 1.18부터**다.
> ★★★ 그리고 **「인터페이스가 `comparable` 을 만족하는 것」이 1.20부터**인데,
> 그 판 경계를 **컴파일러가 `go.mod` 의 `go` 한 줄을 보고 직접 말해 준다**((7)절).

★ **본체는 셋째 창이다** — 「같은 질문을 컴파일 타임과 런타임에 각각 던져 답이 어디서 오나를 보는 창」.
`any` 를 `==` 하면 **런타임 패닉**이고 `comparable` 을 걸면 **컴파일 에러**다. 그 대비가 이 주제의 급소다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | `go_spec.html` 원문 인용(★ `[Go 1.18]`·`[Go 1.20]` 표시까지 붙어 있다) |
| **구현(gc)** | 이 컴파일러·런타임이 그렇게 하는 것 | 패닉·컴파일 에러의 **문장** · `go vet` 이 무엇을 보나 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 실행 출력(재실행 대조까지) |

★★ **패닉이 나는지 안 나는지는 명세**이고, **그 문장의 낱말은 gc 의 것**이다.
`interface conversion: interface {} is int, not string` 이라는 **형식**은 명세에 없다.

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | 패닉 블록의 스택 프레임 주소 | 실행마다 다르다 — ★ 이 주제의 블록에서는 **한 건도 안 흔들렸다**(2판 대조) |
| 안 흔들린다 | ★★★ 패닉 **메시지 본문** · 종료 코드 `2` | 이 주제의 결론 자체다 |
| 안 흔들린다 | ★★★ 컴파일 에러 **문장과 `파일:줄:칸`** | 같은 소스·같은 판이면 같다 |
| 안 흔들린다 | `ok` 의 참거짓 · 타입 스위치가 고른 가지 | 타입 구조가 정한다 |
| 안 흔들린다 | `go vet` 의 진단 **문장** | 분석기가 정한 문장이다 |
| 안 흔들린다 | `-lang` 게이트 문구(`requires go1.20 or later`) | `go.mod` 의 한 줄이 정한다 |
| 해당 없음 | 맵 순회 순서 | 이 주제는 맵을 순회해 찍지 않는다 |

★ 이 주제의 블록은 **재실행에서 한 글자도 같았다.** 정규화 규칙을 **하나도 안 썼다.**

## 한눈에 — 쉽게 말하면

**타입 단언은 「인터페이스 상자를 열어 안을 꺼내는 일」이고, 꺼내는 법이 두 가지다.**
**묻지 않고 꺼내면**(`x.(T)`) 틀렸을 때 **터지고**,
**물어보고 꺼내면**(`v, ok := x.(T)`) 틀렸을 때 **제로값과 `false`** 를 준다.

| 비유 | 실체 |
|---|---|
| 상자 겉면에 뭐가 들었는지 안 적혀 있다 | **인터페이스** — 정적 타입은 메서드 목록뿐 |
| 묻지 않고 손을 넣는다 | **단항 단언** `x.(T)` — 틀리면 패닉 |
| 「이거 맞아요?」라고 먼저 묻는다 | **comma-ok** `v, ok := x.(T)` — 틀리면 제로값과 `false` |
| 「무엇이 들었든 받는 상자」 | **`any`** — `interface{}` 의 **다른 이름**일 뿐이다(1.18) |
| 물건 여러 개를 종류별로 나눈다 | **타입 스위치** — 먼저 맞는 가지가 이긴다 |
| 「무게를 잴 수 있는 것만」이라고 입구에 써 둔다 | ★★★ **`comparable` 제약** — **컴파일에서** 막는다 |
| 아무거나 받아 놓고 저울에 올린다 | ★★★ **`any` 를 `==`** — **런타임에** 터진다 |

```text
   ★★★ 이 주제의 급소 — 같은 질문, 다른 시점

   ① any 로 받아 놓고 == 한다               ② comparable 제약을 건다

     var a any = []int{1}                     func eq[T comparable](x, y T) bool
     var b any = []int{1}                     eq([]int{1}, []int{2})
     _ = a == b
        │                                        │
        ▼ 컴파일은 통과한다                      ▼ 컴파일에서 멈춘다
     런타임 패닉                              컴파일 에러
       「comparing uncomparable                 「[]int does not satisfy
         type []int」 · 종료 코드 2               comparable」 · 종료 코드 1
     ★ 실행 파일이 만들어졌다                 ★ 실행 파일이 안 만들어졌다

   ★ 막는 것은 같은 실수인데, 하나는 배포된 뒤에 알고 하나는 빌드에서 안다.
```

```text
   단언의 두 꼴과 실패 모양

     x.(T)                                v, ok := x.(T)
       │                                    │
       ├─ 맞으면 값                         ├─ 맞으면 (값, true)
       └─ 틀리면 ★ panic                    └─ 틀리면 (제로값, false)

     틀린 이유에 따라 패닉 문구가 갈린다 — (1)절의 표가 전문이다

       담긴 타입이 다르다   「A is B, not C」 꼴
       인터페이스가 비었다  「A is nil, not C」 꼴
       메서드가 모자란다    「A is not I, missing method M」 꼴
```

> **타입 단언(type assertion)** — `x.(T)`. `x` 는 **인터페이스 타입이어야** 한다.\
> 예: `n.(io.Reader)` 에서 `n` 이 `int` 면 `invalid operation: … is not an interface` 다((8)절).

> **comma-ok 형** — `v, ok := x.(T)`. 명세가 「No run-time panic occurs in this case.」라 적는다((1)절).

> **`any`** — 빈 인터페이스 `interface{}` 의 **별칭**(1.18). 새 타입이 아니라 **같은 타입의 다른 이름**이다((4)절).

> **`comparable`** — 타입 제약으로만 쓰는 미리 선언된 인터페이스(1.18).\
> 「**엄밀히 비교 가능한**(strictly comparable) 타입 전부」의 집합이다((6)절).

> **엄밀히 비교 가능(strictly comparable)** — `==` 가 **런타임에 패닉할 수 없는** 것.\
> 인터페이스는 `==` 가 되지만 **패닉할 수 있어서** 엄밀하지 않다 — 이 한 낱말이 (7)절 전부다.

- [20번 주제](../20-interface-declaration-and-implicit-implementation/) (4)절이 **comma-ok 한 꼴을 던져 보고 넘겼다.**
  거기서 결론난 것은 ① 두 꼴이 있다 ② 단항은 패닉이고 문구가 무엇이 들었는지까지 말한다
  ③ 인터페이스에서 인터페이스로도 단언한다 ④ `any` 는 1.18부터의 별칭이다 — 네 가지다.
  **여기서는 그것을 전제로 두고** 「**실패 모양이 몇 가지인가**」와 「**`comparable` 이 무엇을 언제 막나**」로 간다.
- [15번 주제](../15-switch-type-switch-fallthrough-labels-and-goto/) (3)절이 **타입 스위치 문법의 정본**이다 —
  `v` 가 가지마다 다른 타입인 것, `fallthrough` 금지, 중복 타입 금지, `case nil`.
  **여기서는 그 문법을 전제로 두고** 「**가지가 겹칠 때 무엇이 이기나**」만 본다.
- Rust 와 다른 점 — ★★ Rust 의 `dyn Trait` 는 **다운캐스트가 `downcast_ref` 라는 메서드**이고
  `Option` 을 돌려준다 — **comma-ok 만 있고 단항이 없다.**
  (Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **24번**.)
- 자바와 다른 점 — 자바는 `instanceof` 와 캐스트가 **따로**이고 캐스트가 틀리면 `ClassCastException` 이다
  ([`../../../java/syntax/22-instanceof-type-patterns/`](../../../java/syntax/22-instanceof-type-patterns/)).
  ★ Go 의 comma-ok 는 **그 둘을 한 식으로** 묶은 것이다.

## 이 주제가 답하려는 질문

1. **단언이 실패하는 모양이 몇 가지인가** — 패닉 문구가 그것을 얼마나 말해 주나.
2. **`any` 는 새 타입인가** — 「별칭」이라는 말을 **무엇으로 증명하나**.
3. **같은 실수를 컴파일에서 막을 수 있나** — `any` 의 `==` 와 `comparable` 제약이 어디서 갈리나.

★ 타입 스위치 **문법**의 정본은 [15번 주제](../15-switch-type-switch-fallthrough-labels-and-goto/)다.
★ 제네릭 **일반**의 정본은 [목록의 **37번 주제**](../37-generics-type-parameters-and-constraint-interfaces/)다. 여기는 **`comparable` 한 제약**까지다.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| **`recover` 로 패닉 문구만 받아 모으기** | 실패 모양 **여섯 가지를 한 블록에** — 문구가 갈리는 자리 | ★ 이 주제의 고유 창 |
| **패닉을 안 받고 그대로 던지기** | **전문**(스택·종료 코드 2)까지 | [20번 주제](../20-interface-declaration-and-implicit-implementation/) (4)절에서 쓰던 창 |
| ★★★ **같은 실수를 두 시점에 각각 던지기** | `any` 의 `==` 는 **런타임**, `comparable` 은 **컴파일** | ★ 본체 창 |
| ★★ **`go.mod` 의 `go` 한 줄을 바꿔 다시 던지기** | 판 경계를 **컴파일러가 직접 말하게** 한다 | ★ 이 주제의 고유 창 |
| ★ **메서드를 두 이름으로 선언해 보기** | `any` 와 `interface{}` 가 **같은 타입**이라는 것 — 중복 선언 에러가 증거다 | ★ 이 주제의 고유 창 |
| ★ **`go vet` 을 한 번 더 던지기** | 컴파일러가 놓친 **인터페이스끼리의 불가능한 단언**을 vet 이 잡는다 | [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/)에서 쓰던 창 |
| **부적용 — 벤치마크** | 단언은 타입 비교 한 번이다. **이 문서는 안 쟀다** | — |
| **부적용 — `reflect` 의 두 칸** | 이 주제는 **값 칸이 비었나**를 묻지 않는다. 그쪽은 [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/) | — |

★★★ **셋째 창이 본체다.** 「비교 불가능한 것을 비교하면 터진다」는 **같은 사실**인데,
`any` 로 받으면 **배포된 뒤에** 알고 `comparable` 로 받으면 **빌드에서** 안다.
**타입을 어디까지 적었느냐**가 그 시점을 정한다.

★★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.**
「인터페이스가 `comparable` 을 만족하는 것이 언제부터인가」를 **릴리스 노트를 읽어 옮기지 않고**
**`go.mod` 의 `go` 줄을 1.19 로 낮춰 컴파일러에게 물었다**((7)절).
★ 바꾼 창의 한계 — 이 방법은 **언어 기능**에만 통한다.
표준 라이브러리 API 의 판 경계는 이렇게 안 물어진다([24번 주제](../24-error-wrapping-and-errors-is-as-join/)에서 실제로 안 물어졌다).

### (1) ★★ 단언의 두 꼴 — 실패 모양 여섯 가지

**언제 쓰나** — 인터페이스에 담긴 것을 되꺼낼 때.

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

그림 해설 (한 단계씩):

- ★★ **첫 덩어리 — comma-ok 는 패닉하지 않는다.** 명세가 그렇게 적는다.

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

  ★ `a.(string)` 이 `ok=false` 에 **제로값 `""`** 를 준다.
- ★★★ **둘째 덩어리가 이 절의 본문이다** — 같은 자리에서 단항으로 던지면 **여섯 가지 문구**가 나온다.

| 왜 틀렸나 | 패닉 문구 |
|---|---|
| **담긴 구체 타입이 다르다** | `interface conversion: interface {} is int, not string` |
| **이름 있는 인터페이스에 담겨 있었다** | `interface conversion: main.Shape is main.Square, not main.Circle` |
| **인터페이스가 비어 있었다** | `interface conversion: interface {} is nil, not int` |
| **이름 있는 인터페이스가 비어 있었다** | `interface conversion: main.Shape is nil, not main.Square` |
| **메서드가 모자라다(구체 → 인터페이스)** | `interface conversion: int is not fmt.Stringer: missing method String` |
| **메서드가 모자라다(인터페이스 → 인터페이스)** | `interface conversion: *strings.Reader is not io.Closer: missing method Close` |

  ★★ **문구가 두 갈래로 갈린다** — 구체 타입으로의 단언은 「**A is B, not C**」이고
  인터페이스로의 단언은 「**A is not I: missing method M**」이다.
  **무엇이 모자란지까지** 말해 준다.
  ★ 명세가 그 두 갈래를 그대로 나눠 적는다.

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

- ★ **셋째 덩어리** — 같은 여섯 자리를 comma-ok 로 물으면 **전부 `ok=false`** 이고 아무 일도 안 난다.
  고르는 것은 「**틀릴 수 있나**」가 아니라 「**틀렸을 때 무엇을 하고 싶나**」다.

비용 — 단언은 타입 비교 한 번이다. **이 문서는 재지 않았다.**

### (2) ★ 단항 단언의 전문

**언제 쓰나** — 패닉 로그를 읽을 때.

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

그림 해설 (한 단계씩):

- **종료 코드 2** 이고 `goroutine 1 [running]:` 아래에 `main.main()` 과 `파일:줄` 이 찍힌다.
- ★ **익명 인터페이스에 단언한 것**이라 문구에 그 인터페이스가 **선언 그대로** 들어간다 —
  `not interface { Perimeter() float64 }`.
- ★ 구분 마커를 **표준 오류로 찍었다**(`fmt.Fprintln(os.Stderr, …)`) —
  표준 출력과 섞으면 파이프로 받을 때 순서가 갈릴 수 있기 때문이다.

비용 — 없다.

### (3) ★★ 타입 스위치 — 먼저 맞는 가지가 이긴다

**언제 쓰나** — 담긴 타입이 여러 가지일 때.

★ **문법의 정본은 [15번 주제](../15-switch-type-switch-fallthrough-labels-and-goto/) (3)절**이다.
여기서는 **가지가 겹칠 때 무엇이 이기나**만 본다.

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

그림 해설 (한 단계씩):

- ★★★ **`Both` 가 `case error` 로 갔다.** `Both` 는 `Error()` 와 `String()` 을 **둘 다** 갖고 있어
  `case error` 와 `case fmt.Stringer` 를 **둘 다 만족**하는데, **먼저 적은 가지**가 이긴다.
  ★ **가지 순서가 의미를 바꾸는 자리**다 — 구체 타입 가지들과 달리 인터페이스 가지는 **겹칠 수 있다.**
- ★★ **`Named` 가 `case fmt.Stringer` 로 간 것**과 짝이다 — `Named` 는 `error` 가 아니라 그 가지를 지나쳤다.
- ★ **`case int, int64` 처럼 여러 타입을 적으면 `v` 의 타입이 `any` 로 남는다** —
  출력의 `%T` 가 `int`·`int64` 로 찍힌 것은 **동적 타입**이지 `v` 의 정적 타입이 아니다
  ([15번 주제](../15-switch-type-switch-fallthrough-labels-and-goto/)가 정본).
- ★★★ **마지막 줄이 [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/)와 잇는다** —
  `(*mySlice)(nil)` 은 **`case nil` 로 안 가고 `case error` 로 간다.**
  `case nil` 은 **인터페이스 값 자체**가 비었는지만 본다.

비용 — 가지 수만큼 타입 비교가 는다. **이 문서는 재지 않았다.**

```text
   ★★ 가지는 순서대로 시험된다 — 인터페이스 가지만 겹친다

   switch x.(type) {
     case nil            ← 두 칸이 다 빈 것만
     case int, int64     ┐
     case string         ├ 구체 타입 가지 — 서로 겹칠 수 없다(중복이면 컴파일 에러)
     case error          ┐
     case fmt.Stringer   ├ ★ 인터페이스 가지 — 겹칠 수 있다
     case Shape          │
     case io.Reader      ┘
     default
   }

   Both{}  (Error() 와 String() 을 둘 다 가졌다)
      │  위에서부터 시험한다
      ▼
   case error 에서 멈춘다 ← 먼저 적은 쪽이 이긴다
```

### (4) ★★ `any` 는 `interface{}` 의 다른 이름이다

**언제 쓰나** — 「`any` 로 바꿔도 되나」가 궁금할 때.

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

그림 해설 (한 단계씩):

- **`reflect` 가 둘을 같은 타입으로 답한다** — 이름이 `interface {}` 이고 **`==` 가 `true`** 다.
- **서로 대입된다** — `any` → `interface{}` → `A` → `B` 가 전부 통과한다.
  ★ **변환이 아니라 대입**이다. 다른 타입이면 변환 문법이 필요했을 것이다.
- ★ **함수 타입도 같다** — `func(any)` 를 `func(interface{})` 에 대입할 수 있고,
  `%T` 는 **`func(interface {})`** 로 찍는다. ★ **도구는 `any` 라는 이름을 안 쓴다.**
- ★★★ **더 센 증거 — 같은 이름의 메서드를 둘로 선언해 본다.**

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

  ★★ **`method T.M already declared`** 다. 두 타입이 달랐다면 **오버로드가 없는 Go 에서도**
  「다른 시그니처」로 읽혔을 텐데, **컴파일러가 같은 메서드로 읽었다.**
  **별칭이라는 말을 컴파일러가 직접 말해 준 것**이다.
- 명세도 그렇게 적는다 — `any is an alias for the empty interface … [Go 1.18]`
  ([20번 주제](../20-interface-declaration-and-implicit-implementation/) (4)절의 인용).

비용 — 없다. 이름일 뿐이다.

### (5) ★★★ `any` 를 `==` 하면 런타임 패닉이다

**언제 쓰나** — `any` 나 인터페이스 값을 견줄 때.

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

그림 해설 (한 단계씩):

- ★★★ **동적 타입이 같고 그 타입이 비교 불가일 때만 터진다.**
  `any([]int) == any(int)` 는 **동적 타입이 다르므로 그냥 `false`** 다 — 패닉이 아니다.
- 명세가 그 조건을 그대로 적는다.

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

  ★★ **「arrays of interface values or structs with interface-valued fields」까지** 적혀 있다 —
  출력의 `Box{[]int} == Box{[]int}` 가 그 문장의 실측이다
  ([17번 주제](../17-struct-literals-comparability-field-tags-and-sorting/) (4)절이 그쪽 정본이다).
- ★ **`nil` 과의 비교는 특례라 안 터진다** — 같은 명세 문단의 둘째 덩어리다.
  `any([]int) == nil` 이 **`false`** 이고 패닉이 없다.
- ★★ **맵 키로 쓰면 문구가 다르다** — `hash of unhashable type []int`.
  **같은 성질인데 연산이 달라 다른 문장**이 나온다. 로그에서 둘을 갈라 읽어라.
- 마지막 — 받지 않고 그대로 던지면 **`panic: runtime error: comparing uncomparable type []int`**,
  종료 코드 **2** 다.

비용 — 없다. 터지는 것이 비용이다.

### (6) ★★★ `comparable` 은 컴파일에서 막는다

**언제 쓰나** — 제네릭 함수에 `==` 나 맵 키가 들어갈 때.

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

그림 해설 (한 단계씩):

- ★★★ **일곱 줄이 전부 컴파일에서 멈췄다.** 문장은 한 형태다 —
  **`X does not satisfy comparable`**. 종료 코드 1이고 **프로그램은 만들어지지 않았다.**
- ★★ **(5)절과 같은 실수인데 시점이 다르다.**

| | `any` 로 받는다 | `comparable` 제약을 건다 |
|---|---|---|
| 언제 안다 | ★ **런타임** — 그 줄이 실행될 때 | ★★★ **컴파일** — 빌드가 멈춘다 |
| 무엇이 나오나 | `panic: runtime error: comparing uncomparable type []int` | `[]int does not satisfy comparable` |
| 종료 코드 | **2**(실행 실패) | **1**(빌드 실패) |
| 실행 파일 | 만들어졌다 | ★ **안 만들어졌다** |

- ★ **막히는 것과 통과하는 것의 경계**가 (6)절 소스 위쪽에 있다 —
  `int`·`string`·구조체·배열·포인터·채널은 통과하고, **슬라이스·맵·함수와 그것을 필드로 가진 구조체**가 막힌다.
- ★★ **`MySlice`·`MyMap`·`MyFunc` 처럼 이름을 붙여도 막힌다** — 기반 타입이 정한다.

비용 — 없다. 빌드에서 걸러진다.

### (7) ★★★ 1.20 의 「비교 가능한 인터페이스」 — 판마다 갈린 자리

**언제 쓰나** — `comparable` 제약에 `any` 나 인터페이스를 타입 인자로 주고 싶을 때.

★ **명세가 그 예외를 한 문단으로 적고 `[Go 1.20]` 표시를 달아 둔다.**

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

★★ 「**implement 하지는 않는데 satisfy 는 한다**」가 그 예외의 전부다.
인터페이스는 **비교는 되지만 엄밀히 비교 가능하지는 않다**(런타임에 터질 수 있으므로).
그래서 `comparable` 을 **구현하지는 않지만 만족은 한다.**

**그것을 릴리스 노트가 아니라 컴파일러에게 물었다.** `go.mod` 의 `go` 한 줄만 바꿔 같은 소스를 던진다.

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

그림 해설 (한 단계씩):

- ★★★ **`go 1.19` 에서는 여덟 줄이 전부 막힌다** —
  **`any to satisfy comparable requires go1.20 or later (-lang was set to go1.19; check go.mod)`**.
  ★ **컴파일러가 판 경계를 문장으로 말해 준다.** 릴리스 노트를 읽어 옮길 필요가 없다.
- **`go 1.20` 에서는 그대로 컴파일되고 돌아간다.** 소스는 **한 글자도 안 바뀌었다** —
  `go.mod` 의 `1.19` 를 `1.20` 으로 고친 것뿐이다.
- ★★★ **그런데 그 대신 검사가 런타임으로 미뤄진다** — 1.20 판 출력의 둘째 덩어리다.
  `eq[any]([]int{1}, []int{1})` 이 **`comparing uncomparable type []int`** 로 터지고
  `dedup[any]` 는 **`hash of unhashable type []int`** 로 터진다.
- ★★ **`WithIface` 줄이 가장 얄궂다** — 필드가 `any` 인 구조체는
  **(6)절에서 `does not satisfy comparable` 로 막혔는데**,
  타입 인자로 **직접 주면**(`eq[WithIface]`) 1.20부터 통과하고 **런타임에 터진다.**
  같은 타입이 **어느 자리에 쓰이느냐**로 갈린다.
- ★ 명세가 그 대가까지 적어 둔다 — `may panic at run-time (even though comparable type parameters are always strictly comparable)`.

비용 — 없다. **어디서 터질지**가 바뀔 뿐이다.

```text
   ★★★ 구현(implement) 대 만족(satisfy) — 1.20이 가른 두 낱말

   ┌─ 엄밀히 비교 가능 ────────────────┐
   │  int · string · 구조체 · 배열      │  ← comparable 을 구현한다
   │  포인터 · 채널                     │
   └────────────────────────────────────┘
        ▲                       ▲
        │ 구현한다              │ ★ 1.20부터 「만족」만 한다
        │                       │   (비교는 되는데 패닉할 수 있다)
     타입 파라미터            any · error · 인터페이스 필드를 가진 구조체
                                 │
                                 └─ 그래서 검사가 런타임으로 미뤄진다

   ★ 집합 밖 — 슬라이스 · 맵 · 함수. 둘 중 어느 쪽으로도 못 들어간다.
```

### (8) ★★ 애초에 참이 될 수 없는 단언 — 컴파일러 셋, `go vet` 하나

**언제 쓰나** — 단언이 「절대 안 맞을」 때 누가 말해 주나가 궁금할 때.

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

그림 해설 (한 단계씩):

- **컴파일러가 세 가지를 잡는다.**

| 무엇이 틀렸나 | 누가 | 문장 |
|---|---|---|
| **인터페이스가 아닌 것에 단언** | 컴파일러 | `invalid operation: n (variable of type int) is not an interface` |
| **대상 타입이 그 인터페이스를 만족 못 함** | 컴파일러 | `impossible type assertion: r.(int)` + `int does not implement io.Reader (missing method Read)` |
| **구조체가 메서드를 안 가짐** | 컴파일러 | `impossible type assertion: r.(Dog)` + 같은 꼴 |
| ★★ **인터페이스 → 인터페이스인데 시그니처가 충돌** | ★ **`go vet`** | `impossible type assertion: no type can implement both ex.Speaker and ex.Talker (conflicting types for Speak method)` |

- ★★★ **넷째 줄이 컴파일러에서는 안 나왔다.** 같은 파일 안에 `_ = s.(Talker)` 가 있었는데
  에러가 셋뿐이다 — **인터페이스끼리의 단언은 컴파일러가 통과시킨다.**
  명세가 그것을 허락하기 때문이다(「If T is an interface type, x.(T) asserts that the dynamic type of x implements T」).
- ★★ **그 자리를 `go vet` 의 `ifaceassert` 분석기가 메운다.** 종료 코드 1이다.
  ★ [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/) (6)절과 대비하라 —
  **거기서는 `go vet` 이 탐침 8개 중 0개에 답했고 여기서는 답한다.**
  **같은 도구인데 주제에 따라 갈린다.**

비용 — 없다.

## 문법 — 형태와 규칙

### 형태

```go
// t22form.go
package main

import (
	"fmt"
	"io"
	"strings"
)

type Stringish interface{ String() string }

func main() {
	var x any = strings.NewReader("abc")

	// (1) 단항 단언 — 틀리면 패닉
	r := x.(*strings.Reader)
	fmt.Println("(1)", r.Len())

	// (2) comma-ok 단언 — 틀리면 제로값과 false
	if s, ok := x.(string); ok {
		fmt.Println("(2)", s)
	} else {
		fmt.Printf("(2) ok=false, 제로값 %q\n", s)
	}

	// (3) 인터페이스로의 단언 — 메서드 집합을 묻는다
	if rd, ok := x.(io.Reader); ok {
		b, _ := io.ReadAll(rd)
		fmt.Println("(3)", string(b))
	}

	// (4) 타입 스위치 — 가지마다 v 의 타입이 다르다 (15번 주제가 정본)
	switch v := x.(type) {
	case nil:
		fmt.Println("(4) nil", v)
	case int, string: // 여러 타입이면 v 는 any 로 남는다
		fmt.Printf("(4) int|string %v %T\n", v, v)
	case Stringish:
		fmt.Println("(4) Stringish", v.String())
	default:
		fmt.Printf("(4) default %T\n", v)
	}

	// (5) any 는 interface{} 의 별칭이다 (1.18)
	var a any = 1
	var b interface{} = a
	fmt.Printf("(5) %T %T\n", a, b)

	// (6) comparable 은 타입 제약으로만 쓴다
	fmt.Println("(6)", eq(1, 1), eq("a", "b"))
}

func eq[T comparable](a, b T) bool { return a == b }
```

```text
===== 명령: go build -trimpath -o prog . && ./prog =====
(1) 3
(2) ok=false, 제로값 ""
(3) abc
(4) default *strings.Reader
(5) int int
(6) true false
(exit 0)
```

규칙 불릿.

- **단언의 피연산자는 인터페이스 타입이어야** 한다. 아니면 `is not an interface` 다.
- **단항 `x.(T)` 는 틀리면 패닉**, **`v, ok := x.(T)` 는 제로값과 `false`** 다(명세).
- **`T` 가 인터페이스면 「동적 타입이 `T` 를 구현하나」를 묻는다.** 구체 타입이면 「동적 타입이 `T` 와 같나」다.
- **타입 스위치는 가지를 순서대로 시험하고 먼저 맞는 가지가 이긴다.** 인터페이스 가지는 겹칠 수 있다.
- **`any` 는 `interface{}` 의 별칭**이다(1.18). 새 타입이 아니다.
- **`comparable` 은 타입 제약으로만** 쓴다. 변수 타입으로 못 쓴다(명세).
- **인터페이스의 `==` 는 동적 타입이 같고 그것이 비교 불가면 패닉**이다.
- **`nil` 과의 비교는 특례**라 슬라이스·맵·함수도 된다.
- **인터페이스는 `comparable` 을 구현하지 않지만 만족한다**(1.20부터).

### 금지 사례 — 컴파일러가 거부하는 것

| 무엇 | 문장 | 누가 |
|---|---|---|
| 인터페이스가 아닌 것에 단언 | `invalid operation: … is not an interface` | 컴파일러 |
| 불가능한 단언(구체 타입) | `impossible type assertion: r.(int)` | 컴파일러 |
| 비교 불가 타입을 `comparable` 에 | `[]int does not satisfy comparable` | 컴파일러 |
| 1.19 이하에서 인터페이스를 `comparable` 에 | `any to satisfy comparable requires go1.20 or later` | 컴파일러(`-lang`) |
| 같은 메서드를 `any` 와 `interface{}` 로 | `method T.M already declared` | 컴파일러 |
| 불가능한 단언(인터페이스끼리) | `impossible type assertion: no type can implement both …` | ★ **`go vet`** |
| 타입 스위치의 `fallthrough`·중복 타입 | `cannot fallthrough in type switch` 등 | 컴파일러([15번 주제](../15-switch-type-switch-fallthrough-labels-and-goto/)) |

## 어디서 틀리나

### 1. ★★★ 「`any` 끼리 `==` 하면 그냥 비교되겠지」

- (5)절 실측 — 동적 타입이 같고 비교 불가면 **`panic: runtime error: comparing uncomparable type []int`**,
  종료 코드 2다. **컴파일은 통과한다.**
- 고치는 법 — 제네릭이 되는 자리면 **`comparable` 제약**으로 바꾼다((6)절).
  안 되면 `reflect.DeepEqual` 이나 직접 비교 함수를 쓴다.

### 2. ★★★ 「`comparable` 을 걸었으니 런타임에 안 터지겠지」

- (7)절 실측 — **1.20부터 `eq[any](…)` 가 컴파일된다.**
  그리고 그 안에서 `comparing uncomparable type` 이 터진다.
  ★ 명세가 그 대가를 적어 둔다 — `may panic at run-time`.
- 고치는 법 — **타입 인자로 인터페이스를 주지 않는다.** 주려면 터질 수 있다고 알고 준다.

### 3. ★★ 「타입 스위치는 가지 순서가 상관없겠지」

- (3)절 실측 — `Both` 가 **`case error` 로 갔다.** `case fmt.Stringer` 를 앞에 적었으면 그쪽이었다.
- 고치는 법 — **구체적인 가지를 먼저, 넓은 가지를 나중에** 적는다.
  ★ 구체 타입 가지끼리는 겹칠 수 없어(중복 타입이 에러다) 이 문제가 안 생긴다.

### 4. ★★ 「단항 단언이 짧으니 쓰자」

- (1)·(2)절 실측 — 틀리면 **패닉에 종료 코드 2** 다.
- 고치는 법 — **경계에서는 comma-ok.** 단항은 「틀릴 수 없다」가 확실한 자리에만.

### 5. ★★ 「`nil` 인터페이스에 단언하면 `ok` 가 `true` 이겠지」

- (1)절 실측 — `empty.(int)` 가 **`ok=false`** 이고 단항이면
  **`interface conversion: interface {} is nil, not int`** 다.
- 고치는 법 — `nil` 여부는 `== nil` 이나 `case nil` 로 따로 본다
  ([21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/)).

### 6. ★ 「`any` 는 `interface{}` 보다 넓겠지」

- (4)절 실측 — **같은 타입**이다. 메서드를 둘로 선언하면 `already declared` 다.
- 고치는 법 — 읽기 좋은 쪽을 쓴다. 다만 **도구 출력에는 `interface {}` 로 나온다.**

### 7. ★★ 「`any` 로 받으면 유연하겠지」

- (5)·(7)절 실측 — `any` 로 받는 순간 **비교 가능성·해시 가능성이 런타임 문제**가 된다.
- 고치는 법 — **타입 파라미터**를 쓴다([목록의 **37번 주제**](../37-generics-type-parameters-and-constraint-interfaces/)).
  `any` 는 마지막 수단이다.

### 8. ★ 「불가능한 단언은 컴파일러가 다 잡겠지」

- (8)절 실측 — **컴파일러는 셋, `go vet` 이 하나**다.
  인터페이스끼리의 단언은 컴파일러가 통과시킨다.
- 고치는 법 — CI 에 **`go vet` 을 넣는다.**

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| **단항 단언이 틀리면 패닉인 것** | **명세 보장** | "If the type assertion is false, a run-time panic occurs" |
| **comma-ok 가 제로값과 `false` 를 주는 것** | **명세 보장** | "No run-time panic occurs in this case." |
| **피연산자가 인터페이스여야 하는 것** | **명세 보장** | Type assertions 절 |
| **구체 타입 단언과 인터페이스 단언이 다른 것을 묻는 것** | **명세 보장** | "if T is not an interface type … If T is an interface type …" |
| **타입 스위치가 순서대로 시험하는 것** | **명세 보장** | Type switches 절([15번 주제](../15-switch-type-switch-fallthrough-labels-and-goto/)) |
| **`any` 가 빈 인터페이스의 별칭인 것** | **명세 보장 + 판 경계(1.18)** | "any is an alias for the empty interface … [Go 1.18]" |
| **인터페이스 `==` 가 동적 타입이 비교 불가면 패닉인 것** | **명세 보장** | "causes a run-time panic if that type is not comparable" |
| **구조체의 인터페이스 필드·인터페이스 배열도 같은 것** | **명세 보장** | 같은 문단 |
| **`nil` 과의 비교가 특례인 것** | **명세 보장** | "as a special case, a slice, map, or function value may be compared to … nil" |
| **`comparable` 이 엄밀 비교 가능 타입의 집합인 것** | **명세 보장 + 판 경계(1.18)** | "denotes the set of all non-interface types that are strictly comparable [Go 1.18]" |
| **인터페이스가 `comparable` 을 만족하는 것** | ★★★ **명세 보장 + 판 경계(1.20)** | "may also be satisfied by a comparable … type argument [Go 1.20]" |
| **그 경우 런타임에 패닉할 수 있는 것** | **명세 보장** | "may panic at run-time" |
| **`comparable` 을 변수 타입으로 못 쓰는 것** | **명세 보장** | "may only be used as type constraints" |
| 패닉 **문구 자체**(`interface conversion: …`) | **툴체인 판(go1.27.1)** | 규칙은 명세, 문장은 런타임의 것 |
| 컴파일 에러 **문구 자체** | **툴체인 판(go1.27.1)** | 〃 |
| `-lang` 게이트가 **문장으로 말해 주는 것** | **도구(구현)** | `check go.mod` 라는 안내까지 gc 의 것이다 |
| `go vet` 의 `ifaceassert` 가 **잡는 것** | **도구(구현)** | 분석기 목록에 있다. 판이 오르면 달라질 수 있다 |
| 맵 키 실패가 **다른 문장인 것**(`hash of unhashable`) | **런타임(구현)** | 명세는 연산별 문장을 정하지 않는다 |
| 단언·타입 스위치의 **비용** | ★ **안 쟀다** | 벤치마크가 없다([목록의 **50번 주제**](../50-benchmarks-testing-b-and-reading-profiles/)) |

★ 이 주제의 결론은 「**같은 사실을 명세가 두 시점에 걸쳐 놓았고, 어느 쪽에 걸릴지는 타입을 어디까지 적었느냐가 정한다**」이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 외부에서 온 값을 꺼낸다 | **comma-ok** | 틀려도 안 터진다 |
| 「틀릴 수 없다」가 확실하다 | **단항** | 짧다. 틀리면 종료 코드 2 |
| 여러 타입을 분기한다 | **타입 스위치**([15번 주제](../15-switch-type-switch-fallthrough-labels-and-goto/)) | comma-ok 를 늘어놓는 것보다 읽힌다 |
| 가지가 겹칠 수 있다 | **구체적인 것을 먼저** | 먼저 맞는 가지가 이긴다 |
| 「아무거나」를 받는다 | **타입 파라미터**(37번) · `any` 는 마지막 | `any` 는 검사를 런타임으로 미룬다 |
| 제네릭 함수에서 `==` 를 쓴다 | **`comparable` 제약** | 컴파일에서 막힌다 |
| 맵 키로 쓸 타입 파라미터 | **`comparable` 제약** | 〃 |
| `comparable` 에 인터페이스를 준다 | **주지 않는다** | 1.20부터 되지만 **런타임에 터진다** |
| 인터페이스 값을 견준다 | **`==` 전에 동적 타입을 확인** | 비교 불가면 패닉 |
| `any` 와 `interface{}` 중 | **`any`**(1.18 이상) | 같은 타입이고 짧다 |

판단 규칙 두 줄.

- ★★★ **타입을 적는 만큼 검사가 앞당겨진다.** `any` 로 받으면 런타임, `comparable` 로 받으면 컴파일이다.
- ★★ **단언은 「꺼내는 법」이 아니라 「틀렸을 때 무엇을 할까」를 고르는 일이다.**

## 핵심 문장

- ★★★ **같은 실수가 두 시점에 걸린다** — `any` 를 `==` 하면 **런타임 패닉**
  (`comparing uncomparable type []int`, 종료 코드 2)이고
  `comparable` 제약을 걸면 **컴파일 에러**(`[]int does not satisfy comparable`, 종료 코드 1)다.
  **실행 파일이 만들어지느냐 아니냐**가 그 차이다.
- ★★★ **단언의 실패 모양은 여섯 가지**이고 문구가 두 갈래다 —
  구체 타입은 「**A is B, not C**」, 인터페이스는 「**A is not I: missing method M**」이다.
- ★★ **comma-ok 는 명세가 「패닉하지 않는다」고 못 박는다.** 제로값과 `false` 를 준다.
- ★★ **`any` 는 `interface{}` 의 별칭**이다 — 두 이름으로 같은 메서드를 선언하면
  컴파일러가 `method T.M already declared` 라고 답한다. **별칭이라는 말을 컴파일러가 증명한 것**이다.
- ★★★ **인터페이스는 `comparable` 을 구현하지 않지만 만족한다**(1.20). 명세의 낱말이 정확히 그렇다 —
  「do not implement comparable. However, they satisfy comparable」.
- ★★★ **그 판 경계를 컴파일러에게 물을 수 있다** — `go.mod` 의 `go 1.19` 한 줄이
  `any to satisfy comparable requires go1.20 or later (check go.mod)` 를 낸다.
  **소스는 한 글자도 안 바꿨다.**
- ★★ **1.20의 완화는 공짜가 아니다** — 검사가 런타임으로 옮겨 가고
  같은 프로그램이 `comparing uncomparable type` 으로 터진다. 명세도 `may panic at run-time` 이라 적는다.
- ★★ **타입 스위치는 먼저 맞는 가지가 이긴다.** 인터페이스 가지는 **겹칠 수 있어**
  순서가 의미를 바꾼다(`Both` 가 `case error` 로 갔다).
- ★★ **`nil` 과의 비교는 특례**라 슬라이스·맵·함수도 터지지 않는다.
- ★ **불가능한 단언은 컴파일러가 셋, `go vet` 이 하나**를 잡는다 —
  인터페이스끼리의 단언은 컴파일러가 통과시킨다.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 22번)
- [20번 주제](../20-interface-declaration-and-implicit-implementation/)(인터페이스 선언) (4)절 —
  **그쪽은 두 꼴을 한 번 던져 보는 데까지**, 여기는 **실패 모양 여섯 가지와 `comparable` 부터**
- [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/)(`nil` 인터페이스) —
  **`case nil` 이 무엇을 보나**의 짝. `nil` 인터페이스에 단언하면 무엇이 나오는지가 (1)절에 있다
- [15번 주제](../15-switch-type-switch-fallthrough-labels-and-goto/)(타입 스위치) —
  ★★★ **타입 스위치 문법의 정본.** `v` 의 타입·`fallthrough` 금지·중복 타입·`case nil` 은 전부 거기.
  **여기는 「가지가 겹칠 때 무엇이 이기나」만**
- [17번 주제](../17-struct-literals-comparability-field-tags-and-sorting/)(구조체) —
  **구조체 비교 가능성의 정본.** 여기는 **그것이 `comparable` 제약과 만나는 자리**까지
- [19번 주제](../19-method-sets-value-vs-pointer-receiver/)(메서드 집합) —
  「인터페이스로의 단언」이 무엇을 묻는지의 바탕
- [23번 주제](../23-error-interface-and-errors-as-values/)(`error` 인터페이스) — 단언을 **오류에 쓰는** 자리
- [24번 주제](../24-error-wrapping-and-errors-is-as-join/)(`%w`·`Is`/`As`) — ★ **`errors.As` 는 단언을 사슬을 따라 반복하는 것**이다
- [목록의 **37번 주제**](../37-generics-type-parameters-and-constraint-interfaces/)(제네릭) — ★★ **타입 파라미터·제약 일반의 정본.**
  여기는 **`comparable` 한 제약**까지
- [목록의 **42번 주제**](../42-fmt-verbs-stringer-and-errorf/)(`fmt`) — `%T` 가 무엇을 찍는지
- [목록의 **52번 주제**](../52-tools-gofmt-vet-build-tags-embed-and-escape-analysis/)(도구) — `go vet` 의 분석기 목록
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **24번**
  ([`../../../rust/syntax/24-error-type-design/`](../../../rust/syntax/24-error-type-design/)) —
  ★ **그쪽의 `downcast_ref` 는 `Option` 을 돌려준다** — comma-ok 만 있고 단항이 없다
- [`../../../java/syntax/22-instanceof-type-patterns/`](../../../java/syntax/22-instanceof-type-patterns/) —
  **그쪽은 `instanceof` 와 캐스트가 따로**이고 캐스트 실패가 `ClassCastException` 이다

## 용어 풀이

- **타입 단언(type assertion)** — `x.(T)`. 피연산자는 인터페이스여야 한다.
- **단항 형 / comma-ok 형** — 틀렸을 때 패닉이냐 `(제로값, false)` 냐.
- **타입 스위치** — `switch v := x.(type)`. 문법의 정본은 [15번 주제](../15-switch-type-switch-fallthrough-labels-and-goto/).
- **`any`** — `interface{}` 의 별칭(1.18). 새 타입이 아니다.
- **`comparable`** — 엄밀히 비교 가능한 타입 전부의 집합. **타입 제약으로만** 쓴다(1.18).
- **엄밀히 비교 가능(strictly comparable)** — `==` 가 런타임에 패닉할 수 없는 것.
  인터페이스는 비교는 되지만 엄밀하지 않다.
- **구현(implement) 대 만족(satisfy)** — 타입 집합의 원소인 것이 구현,
  제약을 쓸 수 있는 것이 만족. **1.20부터 둘이 갈린다.**
- **`-lang` 게이트** — `go.mod` 의 `go` 줄이 정하는 언어 판. 컴파일러가 그 줄을 근거로 거부한다.

---

## 더 들어가면

- ★ **제네릭의 나머지**(타입 추론·타입 집합·`~T`·제약 인터페이스)는 **안 다뤘다** —
  정본은 [목록의 **37번 주제**](../37-generics-type-parameters-and-constraint-interfaces/)다. 이 문서는 `comparable` **하나**만 던졌다.
- ★ **`reflect` 로 런타임에 단언하는 것**(`Value.Convert`·`Type.AssignableTo`)은 **안 던졌다.**
- ★ **단언·타입 스위치의 비용**은 **안 쟀다**([목록의 **50번 주제**](../50-benchmarks-testing-b-and-reading-profiles/)).
  「타입 스위치가 `if` 사슬보다 빠르다」 같은 말을 이 문서는 하지 않는다.
- **타입 스위치가 만드는 코드**(`-gcflags=-S` 로 보는 것)는 **안 던졌다** — [목록의 **52번 주제**](../52-tools-gofmt-vet-build-tags-embed-and-escape-analysis/) 쪽이다.
- ★★ **`comparable` 이 아닌 다른 미리 선언된 제약**(`cmp.Ordered` 등)은 **안 던졌다**([목록의 **38번 주제**](../38-slices-maps-and-cmp/)).
- ★ **1.19 이하에서 `any` 를 `comparable` 에 주는 것 말고 다른 판 경계**
  (예: 1.18에서 `comparable` 자체가 없던 것)는 **안 던졌다** — `go.mod` 를 1.17 로 낮추는 판을 안 만들었다.

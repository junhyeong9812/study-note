# go/syntax/19 — ★ 메서드 집합: 값 리시버 대 포인터 리시버 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Go 명세](https://go.dev/ref/spec) 의 Method sets · Method declarations ·
> Calls · Selectors · Method values · Method expressions · Implementing an interface 절.\
> 웹이 아니라 **이 툴체인이 들고 있는 `$(go env GOROOT)/doc/go_spec.html` 을 열어** 인용했다.
> 그 파일의 머리는 「**Language version go1.27 (May 26, 2026)**」이다.
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> **버전** — 이 주제의 규칙은 전부 **1.0부터 지금까지 같다.** 판 경계가 없다.
> ★★★ 그리고 이 주제는 **명세가 규칙을 못 박은 자리**다 — 메서드 집합도 인터페이스 만족도
> **구현 사정이 아니다.** 어느 Go 컴파일러에서도 같은 답이 나온다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 명세로, 출력은 실행으로 접지했다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것. 어느 컴파일러에서도 같다 | `go_spec.html` 원문 인용 |
| **구현(gc)** | 이 컴파일러·런타임이 그렇게 하는 것. 약속은 아니다 | 에러 문구 · `go vet` 의 검사 목록 · `go doc` 의 꼴 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 실행 출력(재실행 대조까지) |

★★★ **이 주제는 명세 보장 칸이 거의 전부다.**
「값 리시버 메서드는 `T` 와 `*T` 둘 다의 집합에 들고, 포인터 리시버 메서드는 `*T` 의 집합에만 든다」는
**두 문장으로 명세에 적혀 있다.** 컴파일러가 그렇게 고른 것이 아니다.
★★ 구현인 칸은 **에러 문구**와 **`go vet` 이 무엇을 검사하나** 둘뿐이다.

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | 컴파일 에러 문장 본문과 `파일:줄:칸` | 같은 소스·같은 판이면 같다 |
| 안 흔들린다 | `reflect` 의 `NumMethod` 와 **메서드 이름 목록** | ★ `reflect` 가 **이름 오름차순**으로 준다 — 정렬이 필요 없다 |
| 안 흔들린다 | `Implements` 의 참거짓 · `%T` 가 찍는 타입 이름 | 타입 구조가 정한다 |
| 안 흔들린다 | `go doc -all .` 의 **차례**(타입 이름 오름차순, 그 안은 메서드 이름 오름차순) | 도구가 정렬해 낸다 |
| 안 흔들린다 | `go vet` 의 진단 줄과 종료 코드 | 같은 소스·같은 판이면 같다 |
| **흔들릴 수 있다** | `go vet` 이 **무엇까지 잡나** | 검사 목록은 **도구의 것**이다. 판이 오르면 넓어질 수 있다 |
| 해당 없음 | 맵 순회 순서 | 이 주제는 맵을 **키 하나**로만 쓴다 |
| 해당 없음 | 포인터 값 · 패닉 스택 | 이 주제는 **패닉을 한 번도 안 낸다** — 전부 컴파일 시점에 갈린다 |

★★ **마지막 줄이 이 주제의 성격이다** — 여기서 틀리면 **실행까지 못 간다.**
그래서 「조용히 틀리는 자리」가 아니라 **「에러 문구를 읽을 줄 아느냐」의 자리**다.
★ 다만 **고쳐지지 않는 쪽**은 조용하다 —
[16번 주제](../16-pointers-value-copy-semantics-new-and-make/) (5)절의 `IncVal()` 이 그것이다.

## 한눈에 — 쉽게 말하면

**리시버를 값으로 쓸지 포인터로 쓸지가 「그 타입이 무엇을 할 수 있는지」의 목록을 정한다.**
그 목록을 **메서드 집합(method set)** 이라 부르고, **인터페이스 만족은 그 목록만 본다.**

| 비유 | 실체 |
|---|---|
| 명함에 적힌 자격 목록 | **메서드 집합** — 그 타입으로 부를 수 있는 메서드들 |
| 「원본이 있어야만 할 수 있는 일」 | **포인터 리시버** `func (t *T)` — `*T` 의 명함에만 적힌다 |
| 「사본으로도 되는 일」 | **값 리시버** `func (t T)` — `T` 와 `*T` **둘 다의 명함**에 적힌다 |
| 자격증을 요구하는 창구 | **인터페이스** — **명함만 본다** |
| 내 눈앞에 원본이 있으면 대신 가져다준다 | **자동 주소 얻기** — `v.Ptr()` 이 `(&v).Ptr()` 로 풀린다 |
| 원본을 못 집는 자리 | **맵 원소·함수 반환값** — 거기서는 대신 못 가져다준다 |

```text
   ★★★ 메서드 집합 격자 — 이 주제의 전부

                          선언한 리시버
                  ┌────────────────┬────────────────┐
                  │  func (t T) M  │ func (t *T) M  │
                  │   (값 리시버)  │ (포인터 리시버)│
   ┌──────────────┼────────────────┼────────────────┤
   │ T 의 집합    │       O        │       X        │ <- 여기 한 칸만 비어 있다
   ├──────────────┼────────────────┼────────────────┤
   │ *T 의 집합   │       O        │       O        │
   └──────────────┴────────────────┴────────────────┘

   비어 있는 칸 하나가 이 주제의 모든 에러를 만든다.
```

★★★ **그리고 두 물음을 갈라야 한다.**

```text
   「부를 수 있나」            와        「집합에 있나」는 다른 물음이다

   var v T
   v.PtrM()        <- 된다            var i I = v     <- 안 된다
   (v 가 주소를 얻을 수 있어서          (T 의 메서드 집합에
    (&v).PtrM() 로 풀린다)              PtrM 이 없다)

   ↑ 이 둘을 같은 것으로 읽으면 「부르는 건 되는데 왜 대입이 안 되지」에서 막힌다.
```

> **메서드 집합(method set)** — 그 타입의 피연산자로 부를 수 있는 메서드의 집합.\
> 예: `func (p *P) Speak()` 만 있으면 `P` 의 집합은 **비어 있고** `*P` 의 집합에 `Speak` 이 있다.

> **리시버(receiver)** — 메서드 선언의 `func` 과 이름 사이에 적는 것.\
> 예: `func (c Counter) Get() int` 의 `c Counter`. **값이면 복사본**을 받는다(16번 주제).

> **자동 주소 얻기** — 주소를 얻을 수 있는 피연산자에서 `x.M()` 이 `(&x).M()` 으로 풀리는 것.\
> 예: `var v T; v.PtrM()` 은 되는데 `m["k"].PtrM()` 은 안 된다.

- Rust 와 다른 점 — Rust 는 `&self`·`&mut self`·`self` 를 적고
  **트레이트 구현을 `impl Trait for T` 로 명시**한다
  (Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **25번**).
  Go 는 **명시가 없고 집합이 자동으로 정해지므로**, 틀렸다는 사실이 **대입하는 자리에서야** 드러난다.
- Java 와 다른 점 — 자바에는 이런 갈림이 **없다.** 객체는 언제나 참조라 「값 리시버」가 성립하지 않는다.
  그래서 자바에서 온 사람은 **집합이 둘로 갈린다는 것 자체를** 처음 만난다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **어떤 타입이 어떤 인터페이스를 만족하는가** — 그 판정이 무엇을 보고 이뤄지나.
2. **「부를 수 있다」와 「집합에 있다」는 왜 다른가** — 어디서 갈라지나.
3. **값 리시버와 포인터 리시버 중 무엇을 고르는가** — 기준이 무엇인가.

★ 「값 리시버가 복사본을 고친다」는 이 주제가 아니다 —
[16번 주제](../16-pointers-value-copy-semantics-new-and-make/) (5)절이 그것을 이미 실측했다
(`IncVal()` 뒤에도 카운터가 **0**이었다).
**여기는 그 다음 물음** — **「그래서 인터페이스를 만족하나」** 부터다.

## 동작 방식

### (0) ★★ 이 주제가 쓰는 네 창 — 패닉은 부적용이다

| 창 | 무엇을 보여 주나 | 한계 |
|---|---|---|
| ★★★ **컴파일 에러** | **집합에 없다는 사실과 그 이유**(`method Speak has pointer receiver`) | **일부러 대입해 봐야** 나온다 |
| ★★ **`reflect` 의 `NumMethod`** | **집합의 크기를 수로** — `P` 가 **0**이다 | 왜 0인지는 안 말한다 |
| **`reflect` 의 `Implements`** | 런타임에 「만족하나」를 참거짓으로 | 컴파일 시점 판정과 **같은 답**이지만 늦다 |
| **`go doc -all .`** | 선언된 **리시버의 꼴**(`func (p *P) Speak()`) | ★ **어떤 타입이 어떤 인터페이스를 만족하는지는 안 말한다**(20번 주제) |
| ★ **부적용인 창 — 런타임 패닉** | **이 주제는 패닉을 한 번도 안 낸다** | 틀리면 실행까지 못 간다 |

★★ **「부적용인 창」 칸을 비워 두지 않는 것**이 중요하다.
「재 봤더니 없었다」가 아니라 **「잴 것이 없다」** — 메서드 집합은 **컴파일 시점에 전부 갈린다.**

### (1) ★★★ 네 조합 — 한 칸만 막힌다

**언제 쓰나** — 이 주제의 **본체**다. 다른 절은 전부 이 한 블록의 주석이다.

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

그림 해설 (한 단계씩):

- 네 대입 중 **④ 하나만** 막혔다.

| # | 리시버 | 담은 것 | 결과 |
|---|---|---|---|
| ① | 값 `func (v V)` | `v`(값) | **된다** |
| ② | 값 `func (v V)` | `&v`(포인터) | **된다** |
| ③ | 포인터 `func (p *P)` | `&p`(포인터) | **된다** |
| ④ | 포인터 `func (p *P)` | `p`(값) | ★ **막힌다** |

- 에러 전문이 곧 규칙이다.

  > `cannot use p (variable of struct type P) as Speaker value in variable declaration:
  > P does not implement Speaker (method Speak has pointer receiver)`

  ★★★ **괄호 안의 `method Speak has pointer receiver` 가 이유를 말해 준다.**
  「구현이 없다」가 아니라 「**포인터 리시버라서 값의 집합에 없다**」는 뜻이다.
- 명세가 그 규칙을 **두 문장**으로 적는다.

  > **The method set of a defined type T consists of all methods declared with receiver type T.**

  > **The method set of a pointer to a defined type T** (where T is neither a pointer nor an interface)
  > **is the set of all methods declared with receiver \*T or T.**

  앞 문장에 `\*T` 가 **없다** — 그것이 격자의 빈 칸이다.
- 만족의 정의도 명세에 있다.

  > A type T implements an interface I if **T is not an interface and is an element of the type set of I**.

  그리고 기본 인터페이스의 타입 집합은 **그 메서드들을 구현하는 타입의 집합**이다.
- ★★ **이것은 구현 사정이 아니다.** 명세가 못 박았으므로 어느 Go 컴파일러에서도 같다.
  「gc 가 그렇게 한다」로 적으면 틀린다.

비용 — 없다. 전부 컴파일 시점이다.

### (2) ★★ 집합의 크기를 세어 본다 — `P` 는 0이다

**언제 쓰나** — 격자를 수로 확인할 때.

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

그림 해설 (한 단계씩):

- ★★★ **`main.P` 의 `NumMethod` 가 0**이다. 메서드를 하나 선언했는데 **값 타입의 집합은 비어 있다.**
  `*main.P` 라야 1이다.
- `V` 는 값 리시버라 **`V` 와 `*V` 가 둘 다 1** 이다 — 격자의 왼쪽 세로줄이다.
- `Mixed` 는 둘을 섞은 타입이다 — **`Mixed` 가 1(`Val`), `*Mixed` 가 2(`Ptr`·`Val`)**.
  ★ 리시버를 섞으면 **집합이 둘로 갈린다.** 그래서 한 타입 안에서 **섞지 않는 것이 관용**이다.
- 되는 세 조합을 실제로 담아 보면 `%T` 가 `main.V`·`*main.V`·`*main.P` 로 나온다 —
  **인터페이스는 담은 것을 그대로 들고 있다.**
- ★★ 마지막 네 줄이 **런타임 쪽 판정**이다 — `reflect.Type.Implements` 가
  `main.P` 에만 **`false`** 를 준다. (1)절의 컴파일 에러와 **같은 답**이다.
  ★ 다만 **늦다** — 컴파일러가 잡아 줄 것을 실행까지 미루는 셈이다.
- ★ `reflect` 의 메서드 목록은 **이름 오름차순**이라 정렬할 필요가 없다(`[Ptr Val]`).

**도구로 리시버를 읽는 법** — `go doc` 은 선언을 그대로 보여 준다.

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

- **`func (p *P) Speak() string`** 처럼 **리시버의 꼴이 그대로** 나온다.
  「이 메서드가 포인터 리시버인가」는 이것으로 읽는다.
- ★★ 그런데 **`Speaker` 를 누가 만족하는지는 한 줄도 안 나온다.**
  `V`·`P`·`Mixed` 가 나란히 있을 뿐이다 — **그 판정은 사람이 해야 한다.**
  ★ 이 「없음」이 [20번 주제](../20-interface-declaration-and-implicit-implementation/)의 재료가 된다.

비용 — `reflect` 호출이다. **이 문서는 재지 않았다.**

### (3) ★★★ 주소를 못 얻는 값에서는 포인터 메서드를 못 부른다

**언제 쓰나** — 「변수에서는 됐는데 맵에서는 안 된다」에서 막힐 때.

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

그림 해설 (한 단계씩):

- **세 자리에서 `cannot call pointer method Inc on C`** 가 나온다 —
  **맵 원소**·**함수 반환값**·**복합 리터럴 그 자체**.
  ★ 셋의 공통점은 **주소를 얻을 수 없다**는 것이다.
- 명세가 그 조건을 적는다.

  > A method call x.m() is valid if the method set of (the type of) x contains m and the argument list
  > can be assigned to the parameter list of m. **If x is addressable and &x's method set contains m,
  > x.m() is shorthand for (&x).m().**

  ★★ **「x is addressable」가 조건**이다. 주소를 못 얻으면 그 축약이 성립하지 않는다.
  addressable 의 정의는 [16번 주제](../16-pointers-value-copy-semantics-new-and-make/)가 정본이다 —
  **맵 원소는 거기에 없다.**
- **④는 문구가 다르다** — 맵 원소를 인터페이스에 담으려 하자
  `map index expression of struct type C` 라고 **어디서 온 값인지 밝히면서**
  `C does not implement Speaker (method Speak has pointer receiver)` 로 끝난다.
  ★ (1)절과 같은 에러의 다른 얼굴이다.
- ★ **⑤ 슬라이스 원소는 통과한다**(에러 목록에 27번 줄이 **없다**).
  슬라이스 인덱스는 **addressable** 이기 때문이다.
  **맵과 슬라이스가 여기서 갈린다** — 맵이 자라며 원소를 옮길 수 있어서다
  ([09번 주제](../09-maps-declaration-comma-ok-delete-and-iteration-order/)).

```text
   주소를 얻을 수 있나

   var v C          -> O   변수
   s[0]  ([]C)      -> O   슬라이스 인덱스
   a[0]  ([1]C)     -> O   주소 가능한 배열의 인덱스
   st.In            -> O   주소 가능한 구조체의 필드
   *p               -> O   포인터 역참조
   ───────────────────────────────────────────
   m["k"]           -> X   맵 원소        <- 자라면서 옮겨질 수 있다
   f()              -> X   함수 반환값    <- 담길 변수가 없다
   C{}              -> X   복합 리터럴    <- &C{} 는 되지만 C{}.M() 은 아니다
```

비용 — 없다. 전부 컴파일 시점이다.

### (4) 되는 자리 — 자동 주소 얻기와 그 반대 방향

**언제 쓰나** — (3)절의 반대편을 확인할 때.

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

그림 해설 (한 단계씩):

- **변수·슬라이스 원소·배열 원소·구조체 필드**에서 전부 `Inc()` 가 된다 —
  `(&x).Inc()` 로 풀리기 때문이다.
- ★ **반대 방향의 자동 변환도 있다** — `p.Get()` 이 `(*p).Get()` 으로 풀린다.
  명세: "a reference to a non-interface method with a value receiver using a pointer will
  **automatically dereference that pointer**."
  ★★ 그래서 **포인터를 들고 있으면 아무 걱정이 없다** — 양쪽 다 부를 수 있다.
  걱정은 **값을 들고 있을 때**만 생긴다.
- **맵 원소를 고치는 두 길** —
  ① **꺼내 고치고 다시 넣는다**(`tmp := m1["k"]; tmp.Inc(); m1["k"] = tmp`)
  ② **값 타입을 포인터로 둔다**(`map[string]*C`) — 이쪽이 관용이다.
- 마지막 줄 — **값 메서드는 맵 원소에서도 된다**(`m1["k"].Get()`).
  주소를 안 따지기 때문이다. **막히는 것은 포인터 메서드뿐**이다.

비용 — ①은 구조체를 두 번 복사한다. **이 문서는 재지 않았다.**

### (5) ★★ 메서드 값은 리시버를 그 자리에서 묶는다

**언제 쓰나** — 메서드를 함수 값으로 넘길 때. **조용히 틀리는 자리다.**

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

그림 해설 (한 단계씩):

- ★★★ **`getVal := c.Get` 이 그 순간의 복사본을 묶는다.**
  `c.n` 을 100으로 바꿔도 **`getVal()` 은 1**이고 `c.Get()` 은 100이다.
  명세가 그것을 직접 적는다.

  > The expression x is **evaluated and saved during the evaluation of the method value**;
  > **the saved copy is then used as the receiver** in any calls, which may be executed later.

- **포인터 리시버 쪽은 다르다** — `incPtr := c.Inc` 가 묶은 것은 **`&c`** 라서
  부르면 원본이 바뀐다(`c.n` 이 101).
  ★ **같은 문법 두 줄이 정반대로 군다** — 갈리는 것은 **리시버 선언**이다(16번 주제의 결론과 같다).
- **메서드 표현식**은 리시버를 **첫 인자**로 바꾼다 —
  `C.Get` 이 **`func(main.C) int`**, `(*C).Inc` 가 **`func(*main.C)`** 다.
- ★ **`(*C).Get` 도 있다** — **`func(*main.C) int`** 다.
  값 리시버 메서드는 `*T` 의 집합에도 있으므로 포인터를 받는 함수로도 뽑힌다.
  ★★ **그 반대는 없다** — `C.Inc` 는 안 된다. 명세가 그렇게 적는다.

  > The final case, **a value-receiver function for a pointer-receiver method, is illegal**
  > because pointer-receiver methods are not in the method set of the value type.

  ★ 격자의 빈 칸이 **여기서 한 번 더** 나온다. 이 문서는 그 에러를 **안 던졌다**(명세 인용만).
- ★ 명세는 **주소를 못 얻는 값의 메서드 값**도 막는다고 적는다 —
  `f := makeT().Mp // invalid`. (3)절과 같은 이유다.

비용 — 메서드 값은 클로저를 만든다. 값 리시버면 **리시버 크기만큼 복사**한다. **재지는 않았다.**

### (6) ★ 어느 쪽을 고르나 — `go vet` 이 한 자리를 잡아 준다

**언제 쓰나** — 새 타입에 첫 메서드를 달 때.

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

그림 해설 (한 단계씩):

- **빌드는 성공한다**(exit 0). `go vet` 만 잡는다 —
  **`BadInc passes lock by value: ex.Safe contains sync.Mutex`**, 종료 코드 1.
- ★★ **값 리시버가 잠금째 복사한 것**이다. `s.mu.Lock()` 이 **복사본의 잠금**을 잠그므로
  **아무것도 지켜 주지 않는다.** 16번 주제의 「복사본을 고친다」가
  여기서는 **「복사본을 잠근다」** 로 나타난다.
- ★ 이것이 **리시버를 고르는 첫째 기준**이다 — **복사되면 안 되는 것이 들어 있으면 포인터**다.
  (`sync.Mutex`·`sync.WaitGroup`·`strings.Builder`·`atomic.*` 이 그 부류다.)
- ★★ 다만 **`go vet` 이 잡아 주는 것은 이 한 자리뿐**이다.
  (1)절의 대입 실패는 컴파일러가, 16번의 「안 고쳐짐」은 **아무도** 잡아 주지 않는다.

**기준을 표로 묶으면 이렇다.**

| 고르는 기준 | 값 리시버 | 포인터 리시버 |
|---|---|---|
| 리시버를 **고쳐야** 하나 | 아니오 | ★ **예** |
| 복사되면 안 되는 것이 들어 있나(`sync.*`) | 아니오 | ★ **예**(`vet` 이 잡는다) |
| 리시버가 큰가 | 작다 | 크다(단 **재고 나서**) |
| 한 타입 안에 **둘을 섞나** | ★ **섞지 않는다** — 집합이 갈린다 | 〃 |
| 값으로도 인터페이스에 담고 싶나 | ★ **예** | 아니오(`*T` 로만 담긴다) |
| 슬라이스·맵 같은 **작은 참조 타입** | 값이 흔하다 | — |

비용 — 값 리시버는 **리시버 크기만큼 복사**한다.
★ **「그래서 느리다」는 이 문서가 재지 않았다** — 16번 주제에서도 같은 자리를 비워 뒀다.

## 문법 — 형태와 규칙

### 형태

```go
// t19form.go
package main

import "fmt"

type T struct{ n int }

// ① 값 리시버 — T 와 *T 두 집합에 다 들어간다
func (t T) Val() int { return t.n }

// ② 포인터 리시버 — *T 의 집합에만 들어간다
func (t *T) Ptr() { t.n++ }

// ③ 리시버 이름은 생략할 수 있다 (안 쓰면)
func (T) NoName() string { return "ok" }

type I interface{ Val() int }
type J interface{ Ptr() }

func main() {
	v := T{n: 1}
	p := &T{n: 1}

	v.Ptr()              // ④ 변수는 주소를 얻을 수 있어 (&v).Ptr() 로 풀린다
	fmt.Println(p.Val()) // ⑤ 포인터에서 값 메서드도 된다 — (*p).Val()

	var i1 I = v  // ⑥ 값 리시버 메서드만 요구 → T 로 된다
	var i2 I = &v // ⑦ *T 로도 된다
	var j J = &v  // ⑧ 포인터 리시버 메서드 요구 → *T 라야 한다
	fmt.Println(i1.Val(), i2.Val(), v.NoName())
	j.Ptr()

	f := T.Val    // ⑨ 메서드 표현식 — func(T) int
	g := (*T).Ptr // ⑩ func(*T)
	fmt.Printf("%T %T %d\n", f, g, v.n)
}
```

```text
===== 소스: t19form.go =====
package main

import "fmt"

type T struct{ n int }

// ① 값 리시버 — T 와 *T 두 집합에 다 들어간다
func (t T) Val() int { return t.n }

// ② 포인터 리시버 — *T 의 집합에만 들어간다
func (t *T) Ptr() { t.n++ }

// ③ 리시버 이름은 생략할 수 있다 (안 쓰면)
func (T) NoName() string { return "ok" }

type I interface{ Val() int }
type J interface{ Ptr() }

func main() {
	v := T{n: 1}
	p := &T{n: 1}

	v.Ptr()              // ④ 변수는 주소를 얻을 수 있어 (&v).Ptr() 로 풀린다
	fmt.Println(p.Val()) // ⑤ 포인터에서 값 메서드도 된다 — (*p).Val()

	var i1 I = v  // ⑥ 값 리시버 메서드만 요구 → T 로 된다
	var i2 I = &v // ⑦ *T 로도 된다
	var j J = &v  // ⑧ 포인터 리시버 메서드 요구 → *T 라야 한다
	fmt.Println(i1.Val(), i2.Val(), v.NoName())
	j.Ptr()

	f := T.Val    // ⑨ 메서드 표현식 — func(T) int
	g := (*T).Ptr // ⑩ func(*T)
	fmt.Printf("%T %T %d\n", f, g, v.n)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
1
2 2 ok
func(main.T) int func(*main.T) 3
(exit 0)
```

규칙 불릿.

- **메서드는 `func (리시버) 이름(…)`** 꼴이다. 리시버 이름은 **생략할 수 있다**(안 쓰면).
- **값 리시버 메서드는 `T` 와 `*T` 둘 다의 집합**에, **포인터 리시버 메서드는 `*T` 의 집합에만** 든다.
- **인터페이스 만족은 메서드 집합만 본다.** 「부를 수 있나」와 다른 물음이다.
- **주소를 얻을 수 있으면 `x.M()` 이 `(&x).M()`** 으로, **포인터면 `p.M()` 이 `(*p).M()`** 으로 풀린다.
- **맵 원소·함수 반환값·복합 리터럴은 주소를 못 얻는다** — 거기서는 포인터 메서드를 못 부른다.
- **메서드 값**(`x.M`)은 리시버를 **그 자리에서 평가해 저장**한다. 값 리시버면 **복사본**이다.
- **메서드 표현식**(`T.M`·`(*T).M`)은 리시버를 **첫 인자**로 바꾼다. `(*T).값메서드` 는 되고 `T.포인터메서드` 는 안 된다.
- **한 타입 안에서 리시버 종류를 섞지 않는 것**이 관용이다.
- 리시버는 **정의된 타입(defined type)** 이어야 한다 — 포인터 타입이나 인터페이스에는 메서드를 못 단다.

### 금지 사례 — 컴파일러가 거부하는 것

(1)·(3)절의 블록이 정본이다. 한 표로 묶으면 이렇다.

| 쓴 것 | 메시지 | 왜 막나 |
|---|---|---|
| `var i Speaker = p`(`p` 는 `P` 값) | `P does not implement Speaker (method Speak has pointer receiver)` | `P` 의 집합에 없다 |
| `m["k"].Inc()` | `cannot call pointer method Inc on C` | 맵 원소는 addressable 이 아니다 |
| `make1().Inc()` | `cannot call pointer method Inc on C` | 함수 반환값도 아니다 |
| `C{}.Inc()` | `cannot call pointer method Inc on C` | 복합 리터럴 그 자체도 아니다 |
| `var i Speaker = m["k"]` | `cannot use m["k"] (map index expression of struct type C) as Speaker value …` | 위 둘이 겹친 자리 |
| `C.Inc`(메서드 표현식) | — | 명세가 illegal 이라 적는다. **이 문서는 안 던졌다** |

★ **거부하지 않는 것**도 함께 봐야 한다 — **값 리시버로 원본을 못 고치는 것**은
에러도 경고도 없고([16번 주제](../16-pointers-value-copy-semantics-new-and-make/) (5)절),
**잠금을 복사하는 것**은 **`go vet` 만** 잡는다((6)절).

## 어디서 틀리나

### 1. ★★★ 「부를 수 있으니 인터페이스에도 담기겠지」

- (1)절 실측 — `p.Speak()` 은 되는데 `var i Speaker = p` 는 막힌다.
  에러가 이유를 말한다 — **`method Speak has pointer receiver`**.
- **두 물음이 다르다** — 호출은 **addressable 인가**를 보고, 만족은 **집합에 있나**를 본다.
- 고치는 법 — **`&p` 를 담는다.** 아니면 리시버를 값으로 바꾼다(단 고칠 수 없게 된다).

### 2. ★★ 「메서드를 선언했으니 그 타입에 메서드가 있겠지」

- (2)절 실측 — **`main.P` 의 `NumMethod` 가 0**이다.
- 고치는 법 — 「선언한 메서드 수」와 「그 타입의 집합 크기」를 **갈라 센다.**
  `reflect` 로 두 줄 찍어 보면 바로 보인다.

### 3. ★★★ 「맵에 든 구조체도 메서드로 고치면 되지」

- (3)절 실측 — `cannot call pointer method Inc on C`. **함수 반환값·리터럴도 같다.**
- 고치는 법 — **꺼내 고쳐 다시 넣거나**, **`map[K]*V`** 로 둔다((4)절).

### 4. ★★ 「메서드를 변수에 담아 뒀다가 나중에 부르면 최신 값을 보겠지」

- (5)절 실측 — 값 리시버 메서드 값 `getVal()` 이 **1**을 냈다. `c.n` 은 100인데.
- **리시버는 묶는 순간 평가된다.** 값이면 **복사본**이 저장된다.
- 고치는 법 — 최신 값을 봐야 하면 **포인터 리시버**이거나 **클로저로 감싼다**(`func() int { return c.Get() }`).

### 5. ★★ 「한 타입에 값 리시버와 포인터 리시버를 섞어도 된다」

- (2)절 실측 — `Mixed` 는 **1**, `*Mixed` 는 **2**다. 집합이 둘로 갈린다.
- 고치는 법 — **한쪽으로 통일**한다. 하나라도 고치는 메서드가 있으면 **전부 포인터**가 관용이다.

### 6. ★ 「잠금을 품은 타입도 값 리시버면 읽기 전용이라 안전하다」

- (6)절 실측 — **`go vet` 이 `passes lock by value` 로 잡는다.** 빌드는 통과한다.
- **복사된 잠금은 아무것도 지켜 주지 않는다.**
- 고치는 법 — `sync.*` 를 품은 타입은 **전부 포인터 리시버**로 둔다.

### 7. ★ 「`go vet` 이 메서드 집합 문제를 잡아 주겠지」

- (6)절 실측 — `vet` 이 잡은 것은 **`copylocks` 한 자리뿐**이다.
  대입 실패는 **컴파일러**가 잡고, 「안 고쳐짐」은 **아무도** 안 잡는다.
- 고치는 법 — 도구에 기대지 말고 **격자를 외운다.** 빈 칸은 하나뿐이다.

### 8. ★ 「포인터를 들고 있는데 값 메서드를 못 부르면 어떡하지」

- (4)절 실측 — `p.Get()` 이 `(*p).Get()` 으로 **자동으로 풀린다.**
- ★ **포인터를 들고 있으면 걱정이 없다.** 걱정은 **값을 들고 있을 때**만 생긴다.

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| **`T` 의 집합 = 리시버가 `T` 인 메서드들** | **명세 보장** | "The method set of a defined type T consists of all methods declared with receiver type T" |
| **`\*T` 의 집합 = 리시버가 `\*T` 또는 `T` 인 메서드들** | **명세 보장** | "is the set of all methods declared with receiver \*T or T" |
| **인터페이스 만족이 메서드 집합으로 정해지는 것** | **명세 보장** | "A type T implements an interface I if T … is an element of the type set of I" |
| **addressable 이면 `x.M()` 이 `(&x).M()` 인 것** | **명세 보장** | "If x is addressable and &x's method set contains m, x.m() is shorthand for (&x).m()" |
| **포인터에서 값 메서드가 자동 역참조되는 것** | **명세 보장** | "will automatically dereference that pointer" |
| **맵 원소가 addressable 이 아닌 것** | **명세 보장** | Address operators 절의 목록에 맵 인덱스가 **없다** |
| **메서드 값이 리시버를 그 자리에서 저장하는 것** | **명세 보장** | "evaluated and saved during the evaluation of the method value" |
| **`T.포인터메서드` 가 illegal 인 것** | **명세 보장** | "a value-receiver function for a pointer-receiver method, is illegal" |
| **이 규칙들에 판 경계가 없는 것** | **명세 보장** | 1.0부터 같다 |
| 컴파일 에러의 **문구 자체** | **툴체인 판(go1.27.1)** | 규칙은 명세, 문장은 gc 의 것 |
| `reflect` 가 메서드를 **이름 오름차순**으로 주는 것 | **패키지 계약** | `reflect` 문서의 약속이다 |
| `go doc` 의 **차례와 꼴** | **도구(구현)** | 판이 바뀌면 달라질 수 있다 |
| `go vet` 이 **`copylocks` 를 잡는 것** | **도구(구현)** | 검사 목록은 도구의 것이다 |
| 값 리시버 복사의 **실제 비용** | **안 쟀다** | 벤치마크가 없다([목록의 **50번 주제**](../50-benchmarks-testing-b-and-reading-profiles/)) |
| 인터페이스에 담을 때의 **할당 여부** | **안 쟀다** | 구현(gc)의 영역이고 이 문서는 안 봤다 |

★★★ 이 주제의 결론은 「**메서드 집합도 인터페이스 만족도 명세가 전부 정한다.
구현이 정하는 것은 에러 문장뿐이다**」이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 메서드가 리시버를 고친다 | **포인터 리시버** | 값이면 복사본을 고친다(16번) |
| `sync.*`·`strings.Builder` 를 품었다 | **포인터 리시버** | 복사하면 잠금이 무력해진다 — `vet` 이 잡는다 |
| 한 타입에 메서드가 여럿 | **한쪽으로 통일** | 섞으면 집합이 둘로 갈린다 |
| 하나라도 고치는 메서드가 있다 | **전부 포인터** | 관용이자 사고를 막는 가장 싼 규칙 |
| 작은 불변 값(시간·좌표·ID) | **값 리시버** | 값으로도 인터페이스에 담긴다 |
| 인터페이스에 **값으로** 담고 싶다 | **값 리시버** | `*T` 를 만들 필요가 없어진다 |
| 맵에 넣고 고쳐야 한다 | **`map[K]*V`** | 맵 원소는 주소를 못 잡는다 |
| 메서드를 함수 값으로 넘긴다 | 리시버 종류를 **다시 확인** | 값이면 그 순간의 복사본이 묶인다 |
| 「크니까 포인터」 | **재고 나서** | 이 문서는 안 쟀다 |

판단 규칙 두 줄.

- **격자의 빈 칸은 하나다** — 「포인터 리시버 메서드는 값의 집합에 없다」. 그것만 외우면 된다.
- **고치는 메서드가 하나라도 있으면 전부 포인터 리시버로 통일하라.** 나머지 고민이 사라진다.

## 핵심 문장

- ★★★ **값 리시버 메서드는 `T` 와 `*T` 둘 다의 집합에, 포인터 리시버 메서드는 `*T` 의 집합에만** 든다.
  **격자의 빈 칸은 하나**이고 그 한 칸이 이 주제의 모든 에러를 만든다.
- ★★★ **「부를 수 있나」와 「집합에 있나」는 다른 물음이다.**
  `v.PtrM()` 은 되는데 `var i I = v` 는 안 된다 — 앞엣것은 **addressable** 을, 뒤엣것은 **집합**을 본다.
- ★★ **에러 문구가 이유를 말한다** — `P does not implement Speaker (method Speak has pointer receiver)`.
  「구현이 없다」가 아니라 「**포인터 리시버라서**」다.
- ★★ **`reflect` 로 세면 `main.P` 의 `NumMethod` 가 0**이다. 메서드를 선언했는데 집합이 비어 있다.
- ★★★ **맵 원소·함수 반환값·복합 리터럴에서는 포인터 메서드를 못 부른다** —
  `cannot call pointer method Inc on C`. **슬라이스 원소는 된다.**
- ★ **포인터를 들고 있으면 양쪽 다 된다**(`p.Get()` 이 `(*p).Get()` 으로 풀린다).
  **걱정은 값을 들고 있을 때만** 생긴다.
- ★★ **메서드 값은 리시버를 그 자리에서 저장한다** — 값 리시버면 **복사본**이라
  나중에 불러도 **옛 값**을 본다(`getVal()` 이 1, `c.Get()` 이 100).
- ★ **`go vet` 이 잡아 주는 것은 `copylocks` 한 자리뿐**이다. 나머지는 컴파일러이거나 **아무도 아니다.**
- ★★★ **이 모두가 명세다.** 메서드 집합도 인터페이스 만족도 **구현 사정이 아니고 판 경계도 없다.**

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 19번)
- [16번 주제](../16-pointers-value-copy-semantics-new-and-make/)(포인터·값 복사) —
  **이 주제의 직접 선행.** **그쪽은 「값 리시버가 복사본을 고친다」까지**(에러도 경고도 없다),
  여기는 **「그래서 인터페이스를 만족하나」** 부터. addressable 의 정본도 그쪽이다
- [18번 주제](../18-embedding-and-field-method-promotion/)(임베딩) —
  **그쪽은 승격이 집합을 키우는 것까지**(`ByValue` 1개 대 `ByPtr` 2개), 여기는 **집합 자체의 규칙**
- [20번 주제](../20-interface-declaration-and-implicit-implementation/)(인터페이스) —
  **이 주제의 직접 후행.** 여기는 **「담기나 안 담기나」** 까지,
  그쪽은 **「무엇이 무엇을 만족하는지 찾는 도구가 없다」** 부터
- [09번 주제](../09-maps-declaration-comma-ok-delete-and-iteration-order/)(맵) —
  맵 원소가 주소를 못 잡는 것의 정본
- [17번 주제](../17-struct-literals-comparability-field-tags-and-sorting/)(구조체) — 메서드를 다는 대상
- [목록의 **21번 주제**](../21-nil-interface-vs-interface-holding-nil-pointer/)(`nil` 인터페이스) — 담긴 뒤에 생기는 함정
- [목록의 **32번 주제**](../32-sync-mutex-rwmutex-waitgroup-once/)(`sync`) — **복사하면 안 되는 타입**의 정본. (6)절이 그 한 자리다
- [목록의 **42번 주제**](../42-fmt-verbs-stringer-and-errorf/)(`fmt`) — `String()` 을 값 리시버로 달지 포인터로 달지가 출력에 보이는 자리
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **25번**
  ([`../../../rust/syntax/25-traits-definition-impl-default-methods-and-associated-types/`](../../../rust/syntax/25-traits-definition-impl-default-methods-and-associated-types/)) —
  **그쪽은 `impl Trait for T` 를 적고 `&self`/`&mut self` 를 고른다**,
  여기는 **적는 것이 없고 리시버 선언이 집합을 정한다**

## 용어 풀이

- **메서드 집합(method set)** — 그 타입의 피연산자로 부를 수 있는 메서드의 집합.
- **값 리시버 / 포인터 리시버** — `func (t T) M()` 과 `func (t *T) M()`.
- **addressable** — `&` 를 붙일 수 있는 것. 변수·역참조·슬라이스 인덱스 등. **맵 원소는 아니다.**
- **자동 주소 얻기** — addressable 인 `x` 에서 `x.M()` 이 `(&x).M()` 으로 풀리는 것.
- **자동 역참조** — 포인터 `p` 에서 `p.M()` 이 `(*p).M()` 으로 풀리는 것.
- **메서드 값(method value)** — `x.M` 처럼 리시버를 묶은 함수 값. 리시버가 **그 자리에서 평가**된다.
- **메서드 표현식(method expression)** — `T.M`·`(*T).M`. 리시버가 **첫 인자**가 된다.
- **정의된 타입(defined type)** — `type X …` 로 만든 타입. 메서드는 여기에만 달 수 있다.
- **`copylocks`** — `go vet` 의 검사 하나. 잠금을 값으로 복사하는 자리를 잡는다.

---

## 더 들어가면

- **인터페이스 타입의 메서드 집합**은 그 인터페이스가 선언한 메서드들이다.
  그리고 **인터페이스에는 메서드를 달 수 없다** — 리시버는 정의된 타입이라야 한다.
  이 문서는 그 에러를 **안 던졌다.**
- 명세는 **리시버의 기반 타입이 그 메서드와 같은 패키지**에 있어야 한다고 적는다 —
  그래서 `int` 나 `time.Time` 에 메서드를 못 단다. Rust 의 orphan rule 과 같은 자리이고
  (Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **26번**),
  Go 의 답은 **새 타입을 정의하는 것**이다. 이 문서는 **안 던졌다.**
- **메서드 이름은 필드 이름과 겹칠 수 없다** — "If the base type is a struct type,
  the non-blank method and field names must be distinct." 이 문서는 **안 던졌다.**
- 인터페이스에 값을 담을 때 **값이 어디에 놓이나**(힙인가 아닌가)는 **구현**이다.
  명세에 그 낱말이 없고, 이 문서는 **재지 않았다**([목록의 **52번 주제**](../52-tools-gofmt-vet-build-tags-embed-and-escape-analysis/)).
- `reflect.Value` 쪽에도 `CanAddr`·`Addr` 이 있어 (3)절의 판정을 런타임에 물을 수 있다.
  이 문서는 **안 던졌다** — 컴파일 에러가 더 이른 답이기 때문이다.
- 제네릭의 타입 파라미터에서는 **메서드 집합 규칙이 한 번 더 걸린다** —
  `[T Speaker]` 에 값 타입을 넘기면 같은 에러가 난다. 정본은 [목록의 **37번 주제**](../37-generics-type-parameters-and-constraint-interfaces/)다.

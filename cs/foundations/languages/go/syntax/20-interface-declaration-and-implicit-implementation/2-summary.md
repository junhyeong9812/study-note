# go/syntax/20 — 인터페이스 선언과 암묵 구현 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Go 명세](https://go.dev/ref/spec) 의 Interface types · Implementing an interface ·
> Type assertions · Selectors · Comparison operators 절.\
> 웹이 아니라 **이 툴체인이 들고 있는 `$(go env GOROOT)/doc/go_spec.html` 을 열어** 인용했다.
> 그 파일의 머리는 「**Language version go1.27 (May 26, 2026)**」이다.
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> **버전** — 암묵 구현·타입 단언 규칙은 **1.0부터 같다.**
> 판 경계는 **`any` 라는 이름이 1.18부터**라는 것 하나다(그전에는 `interface{}` 라고 적었다).
> ★★★ 그리고 이 주제도 **명세가 규칙을 못 박은 자리**다 — 무엇이 무엇을 만족하는지는 **구현 사정이 아니다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 명세로, 출력은 실행으로 접지했다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것. 어느 컴파일러에서도 같다 | `go_spec.html` 원문 인용 |
| **구현(gc)** | 이 컴파일러·런타임이 그렇게 하는 것. 약속은 아니다 | 에러·패닉 문구 · 인터페이스 값의 **바이트 수** · `go doc` 의 꼴 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 실행 출력(재실행 대조까지) |

★★★ **「인터페이스 값이 (타입, 값) 두 칸이다」는 명세 보장**이다 —
비교 규칙이 "identical **dynamic types** and equal **dynamic values**" 라고 두 칸을 직접 부른다.
★★ 그런데 **그 값이 16바이트인 것은 구현·플랫폼**이다. 명세에 그 수가 없다((5)절).

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | 패닉 첫 줄의 `pc=0x…` · 스택의 `goroutine N` 과 `+0x…` | 빌드 산출물·런타임에 달렸다 |
| **흔들릴 수 있다** | `unsafe.Sizeof` 가 내놓는 **16과 8** | **플랫폼(amd64).** 명세의 수가 아니다 |
| **흔들릴 수 있다** | `go doc` 의 **차례와 꼴** | 도구의 것이다 |
| 안 흔들린다 | 컴파일 에러 문장 본문과 `파일:줄:칸` | 같은 소스·같은 판이면 같다 |
| 안 흔들린다 | 패닉 메시지 본문 · 종료 코드 `2` | 런타임이 정한 문장이다 |
| 안 흔들린다 | `err == nil` 의 참거짓 · `%T`·`%v` 가 찍는 것 | 타입 구조가 정한다 |
| 안 흔들린다 | `reflect` 의 `Implements`·`IsNil`·`IsValid` | 〃 |
| 안 흔들린다 | `io.MultiReader`→`TeeReader`→`LimitReader` 가 낸 `"ab111c"` | 결정적인 배관이다 |
| 해당 없음 | 맵 순회 순서 | 이 주제는 맵을 찍지 않는다 |

## 한눈에 — 쉽게 말하면

**Go 의 인터페이스는 「무엇을 할 수 있는지」의 목록이고, 그 목록에 맞으면 아무 말 없이 만족된다.**
`implements` 라고 적는 자리가 **없다.**

그리고 **인터페이스 값은 한 칸이 아니라 두 칸**이다 — **어떤 타입인가**와 **그 값은 무엇인가**.
이 주제의 유명한 함정이 전부 그 둘째 사실에서 나온다.

| 비유 | 실체 |
|---|---|
| 「운전할 줄 아는 사람 구함」 | **인터페이스** — 자격 목록만 적는다 |
| 지원서에 「운전 자격 보유」라고 안 적는다 | **암묵 구현** — 메서드만 있으면 된다 |
| 누가 지원할 수 있는지 미리 못 센다 | ★★★ **만족하는 타입을 찾아 주는 도구가 없다** |
| 지원서를 강제로 내 보게 한다 | **컴파일 타임 단언** `var _ I = (*T)(nil)` |
| 봉투에 「이름표」와 「내용물」이 따로 있다 | **(타입, 값) 두 칸** |
| 이름표는 붙었는데 내용물이 비었다 | ★★★ **`nil` 을 담은 인터페이스** — `== nil` 이 **거짓**이다 |

```text
   ★★★ 인터페이스 값은 두 칸이다

   var e error                        e := trap()           // return (*MyErr)(nil)
   ┌──────────┬──────────┐            ┌──────────┬──────────┐
   │ 타입     │ 값       │            │ 타입     │ 값       │
   │  nil     │  nil     │            │ *MyErr   │  nil     │
   └──────────┴──────────┘            └──────────┴──────────┘
      e == nil  ->  true                 e == nil  ->  false
                                                        ↑ 여기서 사고가 난다
```

> **암묵 구현(implicit implementation)** — 메서드 집합이 맞으면 **적지 않아도** 인터페이스를 만족하는 것.\
> 예: `*bytes.Buffer` 는 내가 만든 `Sizer` 인터페이스를 **모르면서** 만족한다((1)절).

> **동적 타입 / 동적 값(dynamic type / dynamic value)** — 인터페이스 값이 지금 들고 있는 타입과 그 값.\
> 예: `var e error = (*MyErr)(nil)` 이면 동적 타입이 `*MyErr`, 동적 값이 `nil` 이다.

> **컴파일 타임 만족 단언** — `var _ Iface = (*T)(nil)`.\
> 예: `T` 가 `Iface` 를 안 만족하면 **그 줄에서** 컴파일이 멈춘다((2)절).

- Rust 와 다른 점 — ★★★ Rust 는 **`impl Trait for T` 를 적고** Go 는 **안 적는다.**
  그래서 Rust 는 **빠진 메서드가 선언 자리에서** 드러나고, Go 는 **쓰는 자리에서야** 드러난다.
  (Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **25번**.)
  Go 의 `var _ I = (*T)(nil)` 은 그 **선언 자리를 인공으로 만드는** 관용구다.
- Java 와 다른 점 — 자바는 `implements` 를 적는다
  ([`../../../java/syntax/11-interfaces-default-methods/`](../../../java/syntax/11-interfaces-default-methods/)).
  그래서 IDE 가 「구현체 목록」을 보여 줄 수 있다. **Go 에는 그 목록이 원리상 없다.**
- Kotlin 과 다른 점 — 코틀린 인터페이스는 **기본 구현을 줄 수 있다**
  ([`../../../kotlin/syntax/20-interfaces-default-impl-and-super/`](../../../kotlin/syntax/20-interfaces-default-impl-and-super/)).
  **Go 인터페이스에는 몸통이 없다** — 메서드 이름과 시그니처뿐이다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **`implements` 를 안 적으면 무엇이 달라지는가** — 설계에서, 그리고 도구에서.
2. **인터페이스 값은 무엇으로 되어 있는가** — 그래서 `== nil` 이 언제 참인가.
3. **인터페이스는 얼마나 작아야 하는가** — 「작을수록 좋다」를 무엇으로 보이나.

★ 메서드 집합 규칙은 이 주제가 아니다 —
[19번 주제](../19-method-sets-value-vs-pointer-receiver/)가 정본이고,
여기는 **그 집합이 맞았다고 치고 그 다음**을 본다.
★ `nil` 인터페이스 함정의 **정본은 [목록의 21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/)다** — 여기서는 **한 번 던져 보고 넘긴다**((3)절).

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 네 창 — 그리고 「없는 창」이 재료다

| 창 | 무엇을 보여 주나 | 한계 |
|---|---|---|
| ★★★ **없는 창 — 「무엇이 이것을 만족하나」** | **없다.** `go doc` 도 `go vet` 도 그 목록을 안 들고 있다 | ★ **그 없음 자체가 이 주제의 결론**이다 |
| ★★ **컴파일 타임 단언** | 만족 여부를 **선언 자리에서** 묻는다 | **적은 것만** 검사된다 |
| **컴파일 에러** | 무엇이 모자란지 — 세 가지 모양이 있다 | 〃 |
| **실행 출력 + `%T`** | 인터페이스가 **지금 무엇을 들고 있나** | 두 칸 중 타입 칸만 보인다 |
| ★★ **`reflect` 의 `IsNil`/`IsValid`** | **값 칸이 `nil` 인지**를 따로 묻는다 | 이걸 안 쓰면 두 칸을 못 가른다 |
| **`unsafe.Sizeof`** | 값이 **두 칸짜리**라는 것 | **수는 플랫폼의 것**이다 |

★★★ **첫 줄이 이 주제의 성격이다.** 다른 주제는 「도구가 무엇을 보여 주나」를 적는데,
여기서는 **「도구가 무엇을 못 보나」가 본문**이다 — `implements` 를 안 적으니
**그 관계가 어디에도 저장되지 않는다.** (2)·(7)절이 그것을 출력으로 보인다.

### (1) 암묵 구현 — 표준 라이브러리가 내 인터페이스를 만족한다

**언제 쓰나** — 인터페이스를 처음 선언할 때.

```text
===== 소스: t20a.go =====
package main

import (
	"bytes"
	"fmt"
	"os"
	"strings"
)

// 표준 라이브러리는 이 인터페이스를 모른다. 그래도 만족한다.
type Sizer interface {
	Len() int
}

// 내가 만든 타입도 io.Writer 라고 한 마디도 안 적는다
type Upper struct{ out *strings.Builder }

func (u Upper) Write(p []byte) (int, error) {
	u.out.WriteString(strings.ToUpper(string(p)))
	return len(p), nil
}

func report(s Sizer) string { return fmt.Sprintf("%T len=%d", s, s.Len()) }

func main() {
	fmt.Println("── 표준 타입들이 내 인터페이스를 만족한다 ──")
	fmt.Println(" ", report(bytes.NewBufferString("abc")))
	fmt.Println(" ", report(strings.NewReader("abcd")))
	var sb strings.Builder
	sb.WriteString("abcde")
	fmt.Println(" ", report(&sb))

	fmt.Println("── 내 타입이 io.Writer 를 만족한다 — implements 를 안 적었다 ──")
	var b strings.Builder
	fmt.Fprintf(Upper{out: &b}, "hello %s", "go")
	fmt.Println("  Fprintf 가 쓴 것 :", b.String())

	fmt.Println("── os.Stdout 도 같은 인터페이스다 ──")
	fmt.Fprintln(os.Stdout, "  Fprintln(os.Stdout, …)")

	fmt.Println("── 인터페이스는 쓰는 쪽에 둔다 : report 는 Sizer 만 알고 구현을 모른다 ──")
	fmt.Printf("  report 의 타입 : %T\n", report)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
── 표준 타입들이 내 인터페이스를 만족한다 ──
  *bytes.Buffer len=3
  *strings.Reader len=4
  *strings.Builder len=5
── 내 타입이 io.Writer 를 만족한다 — implements 를 안 적었다 ──
  Fprintf 가 쓴 것 : HELLO GO
── os.Stdout 도 같은 인터페이스다 ──
  Fprintln(os.Stdout, …)
── 인터페이스는 쓰는 쪽에 둔다 : report 는 Sizer 만 알고 구현을 모른다 ──
  report 의 타입 : func(main.Sizer) string
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`*bytes.Buffer`·`*strings.Reader`·`*strings.Builder` 가 내가 만든 `Sizer` 를 만족한다.**
  그 세 타입은 `Sizer` 라는 이름을 **모른다.** `Len() int` 이 있을 뿐이다. 명세:

  > An interface type defines a **type set**. A variable of interface type can store a value of any type
  > that is in the type set of the interface. **Such a type is said to implement the interface.**

  > **More than one type may implement an interface.** … then the File interface is implemented by both
  > S1 and S2, **regardless of what other methods S1 and S2 may have or share.**

- **내 타입도 `io.Writer` 를 만족한다** — `Upper` 는 `Write([]byte) (int, error)` 하나뿐이고
  `io.Writer` 라고 **한 마디도 안 적었는데** `fmt.Fprintf` 가 받아 준다.
- ★★ **그래서 인터페이스를 「쓰는 쪽」에 둘 수 있다.**
  `report(s Sizer)` 는 `Sizer` 만 알고 구현을 모른다 —
  **구현하는 쪽이 인터페이스를 import 할 필요가 없다.**
  ★ 자바·Rust 는 **구현하는 쪽이 인터페이스를 알아야** 한다(`implements`·`impl … for`).
  이 한 가지가 패키지 의존 방향을 통째로 바꾼다.

```text
   자바·Rust                          Go

   package api  ──┐                   package api   (인터페이스 없음)
     interface I  │ 구현쪽이                 ↑
   package impl   │ 이걸 import 한다         │ 쓰는 쪽이 필요한 만큼만
     class C implements I               package use
                                          type I interface { … }
```

비용 — 인터페이스를 거치는 호출은 간접 호출이다. **이 문서는 재지 않았다.**

### (2) ★★★ 만족을 묻는 도구가 없다 — 그래서 단언을 적는다

**언제 쓰나** — 「내 타입이 이 인터페이스를 만족하나」를 확인하고 싶을 때.

**먼저 안 적은 판을 던져 본다.**

```text
===== 소스: t20c.go =====
package main

import "fmt"

type Handler interface {
	Handle(n int) error
	Name() string
}

type Good struct{}

func (g *Good) Handle(n int) error { return nil }
func (g *Good) Name() string       { return "good" }

type Typo struct{}

func (t *Typo) Handle(n int) error { return nil }
func (t *Typo) Nmae() string       { return "typo" } // 오타 — 아무도 모른다

var _ Handler = (*Good)(nil) // 단언을 적은 쪽만 검사된다

func main() {
	var h Handler = &Good{}
	fmt.Println("Good 은 만족한다 :", h.Name())
	fmt.Println("Typo 는 만족하지 않는다 — 그런데 빌드도 vet 도 한 마디 안 한다")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
Good 은 만족한다 : good
Typo 는 만족하지 않는다 — 그런데 빌드도 vet 도 한 마디 안 한다
(exit 0)
```

```text
===== 명령: go vet ./... =====
(exit 0)
```

- `Typo` 는 `Name()` 대신 **`Nmae()`** 를 갖고 있다. `Handler` 를 만족하지 않는다.
- 그런데 **빌드가 성공(exit 0)** 하고 **`go vet` 은 출력이 0줄에 exit 0** 이다.
  ★★★ **아무도 말해 주지 않는다.** 아무도 `Typo` 를 `Handler` 로 쓰려 하지 않았기 때문이다.

**도구에 물어봐도 없다.**

```text
===== 명령: go doc -all . =====


TYPES

type Good struct{}

func (g *Good) Handle(n int) error

func (g *Good) Name() string

type Handler interface {
	Handle(n int) error
	Name() string
}

type Typo struct{}

func (t *Typo) Handle(n int) error

func (t *Typo) Nmae() string
(exit 0)
```

- ★★★ **`Handler`·`Good`·`Typo` 가 나란히 있을 뿐, 누가 누구를 만족하는지 한 줄도 없다.**
  `go doc` 은 **선언을 보여 주는 도구**이지 관계를 계산하는 도구가 아니다.
- 표준 라이브러리에 물어도 같다.

```text
===== 명령: go doc io.Writer =====
package io // import "io"

type Writer interface {
	Write(p []byte) (n int, err error)
}
    Writer is the interface that wraps the basic Write method.

    Write writes len(p) bytes from p to the underlying data stream. It returns
    the number of bytes written from p (0 <= n <= len(p)) and any error
    encountered that caused the write to stop early. Write must return a non-nil
    error if it returns n < len(p). Write must not modify the slice data,
    even temporarily.

    Implementations must not retain p.

var Discard Writer = discard{}
func MultiWriter(writers ...Writer) Writer
(exit 0)
```

- `io.Writer` 의 선언과 문서가 나오고 `Discard`·`MultiWriter` 가 딸려 나오는데,
  **「이 인터페이스를 무엇이 구현하나」는 없다.**
  ★ 그 목록은 **원리상 못 만든다** — 세상의 모든 패키지를 봐야 하기 때문이다.
- 소스에 낱말이 있는지도 세어 보자.

```text
===== 명령: echo "구현 선언 낱말이 소스에 몇 줄 있나 : $(grep -c -E "implements|extends|impl " t20g.go)" =====
구현 선언 낱말이 소스에 몇 줄 있나 : 0
(exit 0)
```

- ★ **0줄**이다. `implements`·`extends` 같은 낱말이 **소스 어디에도 없다.**
  자바라면 `grep implements` 로 구현체를 찾을 수 있는데 **Go 에는 찾을 문자열이 없다.**

**그래서 그 자리의 관용구가 이것이다.**

```text
===== 소스: t20b.go =====
package main

import "fmt"

type Handler interface {
	Handle(n int) error
	Name() string
}

type Good struct{}

func (g *Good) Handle(n int) error { return nil }
func (g *Good) Name() string       { return "good" }

type Typo struct{}

func (t *Typo) Handle(n int) error { return nil }
func (t *Typo) Nmae() string       { return "typo" } // 오타

type ValueRecv struct{}

func (v ValueRecv) Handle(n int) error { return nil }
func (v ValueRecv) Name() string       { return "value" }

type WrongSig struct{}

func (w *WrongSig) Handle(n int64) error { return nil } // int 가 아니라 int64
func (w *WrongSig) Name() string         { return "wrong" }

// ★ 이 줄들이 이 자리의 관용구다 — 「이 타입이 이 인터페이스를 만족한다」를 컴파일러에게 시킨다
var (
	_ Handler = (*Good)(nil)
	_ Handler = (*Typo)(nil)
	_ Handler = ValueRecv{}
	_ Handler = (*WrongSig)(nil)
)

func main() { fmt.Println("여기까지 오면 단언이 전부 통과한 것이다") }
===== 명령: go build -trimpath -gcflags=-e -o prog . =====
# ex
./t20b.go:33:14: cannot use (*Typo)(nil) (value of type *Typo) as Handler value in variable declaration: *Typo does not implement Handler (missing method Name)
./t20b.go:35:14: cannot use (*WrongSig)(nil) (value of type *WrongSig) as Handler value in variable declaration: *WrongSig does not implement Handler (wrong type for method Handle)
		have Handle(int64) error
		want Handle(int) error
(exit 1)
```

그림 해설 (한 단계씩):

- ★★★ **`var _ Handler = (*Good)(nil)`** — 값을 만들지 않고(`nil` 포인터를 형변환만 한다)
  **컴파일러에게 「이 타입이 이 인터페이스를 만족하나」를 묻는다.**
  통과하면 아무 일도 안 일어나고, 안 통과하면 **그 줄에서 멈춘다.**
- 던져 보면 **세 가지 실패 모양**이 나온다.

| 무엇이 틀렸나 | 메시지 |
|---|---|
| **메서드 이름 오타** | `*Typo does not implement Handler (missing method Name)` |
| **시그니처가 다름** | `*WrongSig does not implement Handler (wrong type for method Handle)` + `have`/`want` 두 줄 |
| **리시버가 포인터** | `… (method Speak has pointer receiver)` — [19번 주제](../19-method-sets-value-vs-pointer-receiver/) (1)절 |

  ★★ **`have Handle(int64) error` / `want Handle(int) error` 두 줄**이 특히 값지다 —
  **무엇을 어떻게 고쳐야 하는지**를 그대로 말해 준다.
- ★ `ValueRecv` 는 **에러가 없다**(값 리시버라 `ValueRecv{}` 로도 만족한다).
  단언을 **값으로 적을지 포인터로 적을지**가 무엇을 검사하는지를 정한다 —
  `(*T)(nil)` 은 `*T` 의 집합을, `T{}` 는 `T` 의 집합을 묻는다.
- ★★ **단언은 적은 것만 검사한다.** 앞의 `t20c` 가 그 증거다 —
  `Typo` 에 단언을 안 달았더니 아무 말도 없었다.
  **이 관용구는 「도구가 못 보는 것」을 사람이 손으로 메우는 일**이다.

비용 — 없다. `var _ …` 는 컴파일 시점에 사라진다.

### (3) ★★★ `nil` 인터페이스와 `nil` 을 담은 인터페이스

**언제 쓰나** — `err != nil` 이 참인데 `err` 가 `<nil>` 로 찍힐 때. **이 갈래의 유명한 함정이다.**

```text
===== 소스: t20d.go =====
package main

import (
	"fmt"
	"reflect"
)

type MyErr struct{ Msg string }

func (e *MyErr) Error() string { return "MyErr:" + e.Msg }

// ★ 함정 — 구체 포인터 타입으로 선언해 두고 그대로 돌려준다
func trap() error {
	var p *MyErr // nil 이다
	return p     // error 인터페이스에 담기면서 (타입=*MyErr, 값=nil) 이 된다
}

// 고친 판 — error 로 선언하거나, nil 을 직접 돌려준다
func fixed() error {
	var p *MyErr
	if p == nil {
		return nil
	}
	return p
}

func describe(name string, err error) {
	fmt.Printf("  %-8s err == nil : %-5v  %%T=%-10T  %%v=%v\n", name, err == nil, err, err)
}

func main() {
	fmt.Println("── 인터페이스 값은 두 칸이다 : (타입, 값) ──")
	var pure error // 두 칸이 다 비었다
	describe("pure", pure)
	describe("trap()", trap())
	describe("fixed()", fixed())

	fmt.Println("── 두 칸을 따로 본다 ──")
	e := trap()
	rv := reflect.ValueOf(e)
	fmt.Printf("  reflect.TypeOf(e)  = %v\n", reflect.TypeOf(e))
	fmt.Printf("  rv.Kind()          = %v\n", rv.Kind())
	fmt.Printf("  rv.IsNil()         = %v   ← 값 칸은 nil 이다\n", rv.IsNil())
	fmt.Printf("  e == nil           = %v   ← 인터페이스 자체는 nil 이 아니다\n", e == nil)
	fmt.Printf("  reflect.ValueOf(error(nil)).IsValid() = %v   ← 진짜 nil 인터페이스\n",
		reflect.ValueOf(error(nil)).IsValid())

	fmt.Println("── 그래서 이런 코드가 조용히 틀린다 ──")
	if err := trap(); err != nil {
		fmt.Println("  err != nil 이 참이 되었다 →", err)
	}
	if err := fixed(); err != nil {
		fmt.Println("  여기는 안 온다")
	} else {
		fmt.Println("  fixed() 는 제대로 nil 이다")
	}

	fmt.Println("── 담긴 값이 nil 이어도 메서드는 불린다 (리시버가 nil 일 뿐이다) ──")
	fmt.Printf("  trap().Error() = %q\n", func() (s string) {
		defer func() {
			if r := recover(); r != nil {
				s = fmt.Sprintf("panic: %v", r)
			}
		}()
		return trap().Error()
	}())
}
===== 명령: go build -trimpath -o prog . && ./prog =====
── 인터페이스 값은 두 칸이다 : (타입, 값) ──
  pure     err == nil : true   %T=<nil>       %v=<nil>
  trap()   err == nil : false  %T=*main.MyErr  %v=<nil>
  fixed()  err == nil : true   %T=<nil>       %v=<nil>
── 두 칸을 따로 본다 ──
  reflect.TypeOf(e)  = *main.MyErr
  rv.Kind()          = ptr
  rv.IsNil()         = true   ← 값 칸은 nil 이다
  e == nil           = false   ← 인터페이스 자체는 nil 이 아니다
  reflect.ValueOf(error(nil)).IsValid() = false   ← 진짜 nil 인터페이스
── 그래서 이런 코드가 조용히 틀린다 ──
  err != nil 이 참이 되었다 → <nil>
  fixed() 는 제대로 nil 이다
── 담긴 값이 nil 이어도 메서드는 불린다 (리시버가 nil 일 뿐이다) ──
  trap().Error() = "panic: runtime error: invalid memory address or nil pointer dereference"
(exit 0)
```

그림 해설 (한 단계씩):

- 세 줄이 갈린다.

| | `err == nil` | `%T` | `%v` |
|---|---|---|---|
| `var pure error` | **`true`** | `<nil>` | `<nil>` |
| `trap()` | ★ **`false`** | **`*main.MyErr`** | `<nil>` |
| `fixed()` | **`true`** | `<nil>` | `<nil>` |

- ★★★ **`trap()` 은 `nil` 포인터를 돌려주는데 `err == nil` 이 `false`** 다.
  `return p` 가 `p`(동적 값 `nil`)를 **`*MyErr` 이라는 타입표와 함께** 인터페이스에 담기 때문이다.
  명세의 비교 규칙이 그것을 그대로 말한다.

  > Two interface values are equal if they have **identical dynamic types and equal dynamic values**
  > **or if both have value nil.**

  ★ **「둘 다 `nil`」은 두 칸이 다 비었다는 뜻**이다. 타입 칸에 `*MyErr` 이 있으면 그 조건이 깨진다.
- **두 칸을 따로 보는 법** —
  `reflect.TypeOf(e)` 가 **`*main.MyErr`**, `rv.IsNil()` 이 **`true`**(값 칸은 비었다),
  `e == nil` 이 **`false`**(인터페이스 자체는 안 비었다).
  ★ 그리고 **진짜 `nil` 인터페이스**는 `reflect.ValueOf(error(nil)).IsValid()` 가 **`false`** 다 —
  `reflect` 가 아예 **값을 못 만든다.** 두 상태가 도구에서도 갈린다.
- ★★ `%v` 가 **`<nil>`** 로 찍히는 것이 사고를 키운다 —
  **로그에는 `<nil>` 이 찍히는데 `err != nil` 은 참**이라, 「에러가 없는데 에러 처리로 들어간다」가 된다.
- **고치는 법은 반환 타입에 있다** — `fixed()` 처럼 **`error` 로 선언하고 `nil` 을 직접 돌려주거나**,
  애초에 구체 포인터 타입의 변수를 두지 않는다.
- ★ 마지막 줄 — **담긴 값이 `nil` 이어도 메서드는 불린다.**
  `trap().Error()` 가 그 안에서 `e.Msg` 를 읽다 패닉한다
  (`recover` 로 받아 찍었다 — `panic: runtime error: invalid memory address or nil pointer dereference`).
  ★★ **인터페이스 호출 자체는 성공했다.** 리시버가 `nil` 일 뿐이다 —
  `nil` 리시버로도 잘 도는 메서드라면 아무 일도 안 난다.
  이것이 **「`nil` 인터페이스 호출」과 다른 자리**다(그쪽은 호출 자체가 패닉이다 — 18번 주제 (5)절).

```text
   두 가지 nil 을 갈라라

   ① nil 인터페이스            var e error
      [타입: nil][값: nil]      -> e == nil 이 true, e.M() 은 패닉
   ② nil 을 담은 인터페이스     var p *T = nil; var e error = p
      [타입: *T ][값: nil]      -> e == nil 이 false, e.M() 은 불린다(리시버가 nil)
```

비용 — 없다. 두 칸을 채우는 일뿐이다.

### (4) 타입 단언과 comma-ok · 빈 인터페이스

**언제 쓰나** — 인터페이스에 담긴 것을 되꺼낼 때.

```text
===== 소스: t20f.go =====
package main

import (
	"fmt"
	"io"
	"os"
	"strings"
)

type Closer interface{ Close() error }

func main() {
	var r io.Reader = strings.NewReader("abc")

	fmt.Println("── comma-ok 형 : 물어보기 ──")
	if sr, ok := r.(*strings.Reader); ok {
		fmt.Println("  *strings.Reader 다  Len =", sr.Len())
	}
	if _, ok := r.(Closer); !ok {
		fmt.Println("  Closer 는 아니다 — ok 가 false 다")
	}
	if s, ok := any(42).(string); !ok {
		fmt.Printf("  any(42).(string) -> ok=false, 제로값 %q\n", s)
	}

	fmt.Println("── 인터페이스에서 인터페이스로도 단언한다 ──")
	var rc io.Reader = io.NopCloser(strings.NewReader("abc"))
	_, ok := rc.(io.Closer)
	fmt.Println("  NopCloser 는 io.Closer 인가 :", ok)

	fmt.Println("── 빈 인터페이스 any 는 아무거나 담는다 ──")
	for _, v := range []any{1, "ㄱ", 2.5, []int{1}, nil, struct{}{}} {
		fmt.Printf("  %-10s %T\n", fmt.Sprint(v), v)
	}

	fmt.Fprintln(os.Stderr, "-- 이제 단항 단언을 틀리게 던진다 --")
	_ = r.(*os.File)
	fmt.Fprintln(os.Stderr, "-- 여기는 안 온다 --")
}
===== 명령: go build -trimpath -o prog . =====
(exit 0)
```

```text
===== 명령: ./prog 2>&1 =====
── comma-ok 형 : 물어보기 ──
  *strings.Reader 다  Len = 3
  Closer 는 아니다 — ok 가 false 다
  any(42).(string) -> ok=false, 제로값 ""
── 인터페이스에서 인터페이스로도 단언한다 ──
  NopCloser 는 io.Closer 인가 : true
── 빈 인터페이스 any 는 아무거나 담는다 ──
  1          int
  ㄱ          string
  2.5        float64
  [1]        []int
  <nil>      <nil>
  {}         struct {}
-- 이제 단항 단언을 틀리게 던진다 --
panic: interface conversion: io.Reader is *strings.Reader, not *os.File

goroutine 1 [running]:
main.main()
	ex/t20f.go:37 +0x596
(exit 2)
```

그림 해설 (한 단계씩):

- **comma-ok 형은 묻는다** — `sr, ok := r.(*strings.Reader)` 가 `ok=true` 이고 `Len()` 이 3이다.
  `r.(Closer)` 는 `ok=false` 다. 명세:

  > A type assertion used in an assignment statement … **yields an additional untyped boolean value.**
  > The value of ok is true if the assertion holds. Otherwise it is **false and the value of v is
  > the zero value for type T. No run-time panic occurs in this case.**

  ★ `any(42).(string)` 이 `ok=false` 에 **제로값 `""`** 를 주는 것이 그 규칙이다.
- **인터페이스에서 인터페이스로도 단언한다** — `rc.(io.Closer)` 가 `true` 다.
  명세: "If T is an interface type, x.(T) asserts that the **dynamic type of x implements the interface T**."
- **빈 인터페이스 `any`** 에는 아무거나 담긴다 — `int`·`string`·`float64`·`[]int`·`nil`·`struct{}`.
  ★ `nil` 의 `%T` 가 **`<nil>`** 인 것이 (3)절과 이어진다 — **담긴 것이 없는 인터페이스**다.
  `any` 는 **1.18부터**의 이름이다.

  > For convenience, the predeclared type **any is an alias for the empty interface**;
  > it is not a named type. **[Go 1.18]**

- ★★ **단항 단언은 틀리면 패닉**이다 —
  **`panic: interface conversion: io.Reader is *strings.Reader, not *os.File`**, **종료 코드 2**.
  ★ 메시지가 **무엇이 들어 있었는지까지** 말해 준다 — 진단에 그대로 쓸 수 있다.
- ★ 타입 스위치는 [15번 주제](../15-switch-type-switch-fallthrough-labels-and-goto/)가 정본이다.
  여기서는 comma-ok 한 꼴만 본다.

비용 — 단언은 타입 비교 한 번이다. **이 문서는 재지 않았다.**

### (5) ★ 인터페이스 값의 크기 — 두 칸이라는 것을 수로

**언제 쓰나** — 「인터페이스에 담으면 값이 어떻게 되나」가 궁금할 때.

```text
===== 소스: t20e.go =====
package main

import (
	"fmt"
	"unsafe"
)

type Speaker interface{ Speak() string }
type Empty interface{}

type Big struct{ Buf [1024]byte }

func (b Big) Speak() string { return "big" }

func main() {
	fmt.Println("── 인터페이스 값은 두 칸이다 : 크기가 포인터 둘이다 (구현·플랫폼) ──")
	var s Speaker
	var e Empty
	var a any
	var p *Big
	fmt.Println("  unsafe.Sizeof(Speaker) =", unsafe.Sizeof(s))
	fmt.Println("  unsafe.Sizeof(Empty)   =", unsafe.Sizeof(e))
	fmt.Println("  unsafe.Sizeof(any)     =", unsafe.Sizeof(a))
	fmt.Println("  unsafe.Sizeof(*Big)    =", unsafe.Sizeof(p), " ← 포인터 한 칸")
	fmt.Println("  unsafe.Sizeof(Big{})   =", unsafe.Sizeof(Big{}), " ← 값 그 자체")

	fmt.Println("── 1024바이트짜리를 인터페이스에 담아도 인터페이스 값은 16이다 ──")
	s = Big{}
	fmt.Println("  담은 뒤 unsafe.Sizeof(s) =", unsafe.Sizeof(s), " · %T =", fmt.Sprintf("%T", s))
	fmt.Println("  ★ 담을 때 값이 어디에 놓이는지는 명세에 없는 낱말이다 — 구현이 정한다")

	fmt.Println("── 두 칸이 비어야 nil 이다 ──")
	var n1 Speaker
	fmt.Println("  var n1 Speaker      -> n1 == nil :", n1 == nil)
	var n2 Speaker = (*Big)(nil)
	fmt.Printf("  Speaker = (*Big)(nil) -> n2 == nil : %v  (%%T=%T)\n", n2 == nil, n2)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
── 인터페이스 값은 두 칸이다 : 크기가 포인터 둘이다 (구현·플랫폼) ──
  unsafe.Sizeof(Speaker) = 16
  unsafe.Sizeof(Empty)   = 16
  unsafe.Sizeof(any)     = 16
  unsafe.Sizeof(*Big)    = 8  ← 포인터 한 칸
  unsafe.Sizeof(Big{})   = 1024  ← 값 그 자체
── 1024바이트짜리를 인터페이스에 담아도 인터페이스 값은 16이다 ──
  담은 뒤 unsafe.Sizeof(s) = 16  · %T = main.Big
  ★ 담을 때 값이 어디에 놓이는지는 명세에 없는 낱말이다 — 구현이 정한다
── 두 칸이 비어야 nil 이다 ──
  var n1 Speaker      -> n1 == nil : true
  Speaker = (*Big)(nil) -> n2 == nil : false  (%T=*main.Big)
(exit 0)
```

그림 해설 (한 단계씩):

- **`Speaker`·`Empty`·`any` 가 전부 16바이트**다. `*Big` 은 8, `Big{}` 은 1024다.
  ★★ **16 = 포인터 둘**이고, 그것이 (타입, 값) 두 칸이다.
- ★★★ **그런데 16이라는 수는 명세에 없다.** 명세는 「인터페이스 값이 두 칸이다」를
  **비교 규칙의 낱말**(dynamic type / dynamic value)로만 말한다.
  **바이트 수는 구현·플랫폼**이다.
- **1024바이트짜리를 담아도 인터페이스 값은 16**이다 — 그러면 그 1024바이트는 어디 갔나.
  ★ **명세에 그 답이 없다.** 「담을 때 값이 어디에 놓이나」는 **구현**이고
  이 문서는 **재지 않았다**([목록의 **52번 주제**](../52-tools-gofmt-vet-build-tags-embed-and-escape-analysis/)).
- 마지막 두 줄이 (3)절을 한 번 더 말한다 —
  `var n1 Speaker` 는 `nil` 이고 `Speaker = (*Big)(nil)` 은 **`nil` 이 아니다**(`%T` 가 `*main.Big`).

비용 — 담을 때 할당이 생길 수 있다. **이 문서는 재지 않았다.**

### (6) ★★ 작은 인터페이스가 이기는 것을 수로 보인다

**언제 쓰나** — 인터페이스에 메서드를 몇 개 넣을지 고를 때.

```text
===== 소스: t20g.go =====
package main

import (
	"bytes"
	"fmt"
	"io"
	"os"
	"reflect"
	"strings"
)

// 한 메서드 인터페이스 — 직접 만든 것
type Reader1 interface {
	Read(p []byte) (n int, err error)
}

// 네 메서드 인터페이스 — 같은 일을 하는데 요구가 많다
type Reader4 interface {
	Read(p []byte) (n int, err error)
	Close() error
	Seek(offset int64, whence int) (int64, error)
	WriteTo(w io.Writer) (int64, error)
}

// 내가 만든 최소 구현 — Read 하나뿐이다
type Ones struct{ left int }

func (o *Ones) Read(p []byte) (int, error) {
	if o.left <= 0 {
		return 0, io.EOF
	}
	n := min(len(p), o.left)
	for i := range n {
		p[i] = '1'
	}
	o.left -= n
	return n, nil
}

func main() {
	fmt.Println("── 후보 타입들이 두 인터페이스를 각각 얼마나 만족하나 ──")
	cands := []reflect.Type{
		reflect.TypeOf((*strings.Reader)(nil)),
		reflect.TypeOf((*bytes.Buffer)(nil)),
		reflect.TypeOf((*bytes.Reader)(nil)),
		reflect.TypeOf((*os.File)(nil)),
		reflect.TypeOf((*Ones)(nil)),
	}
	r1 := reflect.TypeOf((*Reader1)(nil)).Elem()
	r4 := reflect.TypeOf((*Reader4)(nil)).Elem()
	n1, n4 := 0, 0
	for _, t := range cands {
		a, b := t.Implements(r1), t.Implements(r4)
		if a {
			n1++
		}
		if b {
			n4++
		}
		fmt.Printf("  %-18v Reader1=%-6v Reader4=%v\n", t, a, b)
	}
	fmt.Printf("  합계 : 한 메서드 %d/%d · 네 메서드 %d/%d\n", n1, len(cands), n4, len(cands))

	fmt.Println("── 작은 인터페이스는 조합된다 ──")
	src := io.MultiReader(strings.NewReader("ab"), &Ones{left: 3}, bytes.NewReader([]byte("cd")))
	var tee bytes.Buffer
	lim := io.LimitReader(io.TeeReader(src, &tee), 6)
	got, err := io.ReadAll(lim)
	fmt.Printf("  MultiReader→TeeReader→LimitReader : %q err=%v\n", got, err)
	fmt.Printf("  곁가지(tee)로 흘러간 것            : %q\n", tee.String())

	fmt.Println("── io.Reader 의 선언은 한 줄이다 ──")
	fmt.Println("  type Reader interface { Read(p []byte) (n int, err error) }")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
── 후보 타입들이 두 인터페이스를 각각 얼마나 만족하나 ──
  *strings.Reader    Reader1=true   Reader4=false
  *bytes.Buffer      Reader1=true   Reader4=false
  *bytes.Reader      Reader1=true   Reader4=false
  *os.File           Reader1=true   Reader4=true
  *main.Ones         Reader1=true   Reader4=false
  합계 : 한 메서드 5/5 · 네 메서드 1/5
── 작은 인터페이스는 조합된다 ──
  MultiReader→TeeReader→LimitReader : "ab111c" err=<nil>
  곁가지(tee)로 흘러간 것            : "ab111c"
── io.Reader 의 선언은 한 줄이다 ──
  type Reader interface { Read(p []byte) (n int, err error) }
(exit 0)
```

그림 해설 (한 단계씩):

- 같은 후보 다섯에게 **메서드 하나짜리**와 **메서드 넷짜리**를 각각 물었다.

| 후보 | `Reader1`(1개) | `Reader4`(4개) |
|---|---|---|
| `*strings.Reader` | `true` | `false` |
| `*bytes.Buffer` | `true` | `false` |
| `*bytes.Reader` | `true` | `false` |
| `*os.File` | `true` | **`true`** |
| `*main.Ones` | `true` | `false` |
| **합계** | ★ **5/5** | ★ **1/5** |

- ★★★ **메서드를 셋 더 요구했더니 만족하는 타입이 5에서 1로 줄었다.**
  「작은 인터페이스가 좋다」가 **취향이 아니라 산술**이라는 것을 이 두 수가 말한다.
- ★ 내가 만든 `Ones` 는 **`Read` 하나만 썼는데** `io` 의 배관에 그대로 들어간다 —
  `io.MultiReader` → `io.TeeReader` → `io.LimitReader` 가 **`"ab111c"`** 를 냈고
  곁가지로도 같은 바이트가 흘렀다.
- ★★ **조합이 되는 이유가 「작아서」다.** `io.Reader` 가 `Read` 하나라
  `MultiReader`·`TeeReader`·`LimitReader` 가 전부 **`io.Reader` 를 받아 `io.Reader` 를 낸다.**
  메서드가 넷이었다면 그 배관은 못 만들어진다.
- 마지막 줄 — **`io.Reader` 의 선언은 한 줄**이다.

비용 — 각 단계가 호출 한 겹씩 더한다. **이 문서는 재지 않았다.**

### (7) ★★ 「도구가 못 보는 것」을 한 자리에 모으면

**언제 쓰나** — 이 주제의 결론을 적을 때.

| 묻고 싶은 것 | 답해 주는 도구 | 실측 |
|---|---|---|
| 이 메서드의 리시버가 포인터인가 | **`go doc`** | (2)절 · [19번 주제](../19-method-sets-value-vs-pointer-receiver/) (2)절 |
| 이 타입이 이 인터페이스를 만족하나 | ★ **없다 — 사람이 단언을 적어야 한다** | (2)절 — `go doc` 에 그 줄이 없다 |
| 이 인터페이스를 무엇이 구현하나 | ★ **없다 — 원리상 못 만든다** | (2)절 — `go doc io.Writer` 에 목록이 없다 |
| 구현 선언 낱말을 grep 하면 | ★ **0줄** | (2)절 — 찾을 문자열이 없다 |
| 만족 못 하는 타입이 방치돼 있나 | ★ **없다 — `go vet` 도 침묵**(출력 0줄·exit 0) | (2)절 |
| 인터페이스 값의 두 칸 | **`reflect`**(`TypeOf`·`IsNil`·`IsValid`) | (3)절 |
| 두 칸짜리라는 크기 | **`unsafe.Sizeof`**(구현) | (5)절 |
| 만족 여부를 런타임에 | **`reflect.Type.Implements`** | [19번 주제](../19-method-sets-value-vs-pointer-receiver/) (2)절 |

★★★ **위 다섯 줄의 「없다」가 이 주제의 값어치다.**
암묵 구현은 **그 관계를 어디에도 저장하지 않는다.** 그래서 —
**① `var _ I = (*T)(nil)` 을 적어 선언 자리를 만들고**,
**② 인터페이스를 작게 유지해** 만족 여부를 사람이 눈으로 셀 수 있게 한다.
★ 「작게 유지한다」가 설계 취향이 아니라 **도구 부재에 대한 대응**이기도 한 것이다.

## 문법 — 형태와 규칙

### 형태

```go
// t20form.go
package main

import (
	"fmt"
	"io"
	"strings"
)

// ① 인터페이스 선언 — 메서드 이름과 시그니처만 적는다
type Speaker interface {
	Speak() string
}

// ② 여러 메서드 · 다른 인터페이스 임베딩
type Loud interface {
	Speaker
	io.Closer
	Volume() int
}

// ③ 빈 인터페이스 — any 가 별칭이다 (1.18)
type Anything interface{}

// ④ 구현 선언이 없다. 메서드만 있으면 만족한다
type Dog struct{ Name string }

func (d Dog) Speak() string { return d.Name + ": 멍" }

// ⑤ 컴파일 타임 단언 — 이 줄이 「구현한다」를 적는 유일한 자리다
var _ Speaker = Dog{}

func main() {
	var s Speaker = Dog{Name: "바둑이"}
	fmt.Println(s.Speak())

	if d, ok := s.(Dog); ok { // ⑥ 타입 단언(comma-ok)
		fmt.Println("  안에 든 것 :", d.Name)
	}

	switch v := s.(type) { // ⑦ 타입 스위치 (15번 주제)
	case Dog:
		fmt.Println("  타입 스위치 : Dog", v.Name)
	default:
		fmt.Println("  타입 스위치 : 그 밖")
	}

	var a Anything = 1 // ⑧ any 에는 아무거나
	var b any = strings.NewReader("x")
	fmt.Printf("  %T %T\n", a, b)

	var nilIface Speaker // ⑨ 두 칸이 다 비면 nil
	fmt.Println("  nilIface == nil :", nilIface == nil)
}
```

```text
===== 소스: t20form.go =====
package main

import (
	"fmt"
	"io"
	"strings"
)

// ① 인터페이스 선언 — 메서드 이름과 시그니처만 적는다
type Speaker interface {
	Speak() string
}

// ② 여러 메서드 · 다른 인터페이스 임베딩
type Loud interface {
	Speaker
	io.Closer
	Volume() int
}

// ③ 빈 인터페이스 — any 가 별칭이다 (1.18)
type Anything interface{}

// ④ 구현 선언이 없다. 메서드만 있으면 만족한다
type Dog struct{ Name string }

func (d Dog) Speak() string { return d.Name + ": 멍" }

// ⑤ 컴파일 타임 단언 — 이 줄이 「구현한다」를 적는 유일한 자리다
var _ Speaker = Dog{}

func main() {
	var s Speaker = Dog{Name: "바둑이"}
	fmt.Println(s.Speak())

	if d, ok := s.(Dog); ok { // ⑥ 타입 단언(comma-ok)
		fmt.Println("  안에 든 것 :", d.Name)
	}

	switch v := s.(type) { // ⑦ 타입 스위치 (15번 주제)
	case Dog:
		fmt.Println("  타입 스위치 : Dog", v.Name)
	default:
		fmt.Println("  타입 스위치 : 그 밖")
	}

	var a Anything = 1 // ⑧ any 에는 아무거나
	var b any = strings.NewReader("x")
	fmt.Printf("  %T %T\n", a, b)

	var nilIface Speaker // ⑨ 두 칸이 다 비면 nil
	fmt.Println("  nilIface == nil :", nilIface == nil)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
바둑이: 멍
  안에 든 것 : 바둑이
  타입 스위치 : Dog 바둑이
  int *strings.Reader
  nilIface == nil : true
(exit 0)
```

규칙 불릿.

- **인터페이스는 메서드 이름과 시그니처만** 적는다. **몸통이 없다**(코틀린과 갈리는 자리).
- **다른 인터페이스를 임베딩**할 수 있다. 메서드 집합의 합집합이 된다(18번 주제).
- **`interface{}` 는 아무거나 담고, `any` 가 그 별칭**이다(1.18부터).
- **구현을 적는 문법이 없다.** 메서드 집합이 맞으면 만족한다.
- **만족을 컴파일러에게 묻는 관용구**는 `var _ Iface = (*T)(nil)` 이다.
- **인터페이스 값은 (타입, 값) 두 칸**이고, **두 칸이 다 비어야 `nil`** 이다.
- **타입 단언은 두 꼴** — `x.(T)` 는 틀리면 패닉, `v, ok := x.(T)` 는 제로값과 `false`.
- **인터페이스에서 인터페이스로도** 단언한다.
- **`nil` 인터페이스의 메서드를 부르면 패닉**이다. 담긴 값이 `nil` 인 것과는 다르다.

### 금지 사례 — 컴파일러가 거부하는 것

(2)절의 블록이 정본이다. 한 표로 묶으면 이렇다.

| 무엇이 틀렸나 | 메시지 |
|---|---|
| 메서드 이름 오타 | `*Typo does not implement Handler (missing method Name)` |
| 시그니처 불일치 | `*WrongSig does not implement Handler (wrong type for method Handle)` + `have`/`want` |
| 포인터 리시버 | `… (method Speak has pointer receiver)`([19번 주제](../19-method-sets-value-vs-pointer-receiver/)) |

★ **거부하지 않는 것**이 이 주제의 본문이다 —
**단언을 안 적으면 아무 일도 안 일어난다**(`t20c` 가 exit 0, `vet` 도 0줄).

## 어디서 틀리나

### 1. ★★★ 「`nil` 포인터를 돌려줬으니 `err == nil` 이겠지」

- (3)절 실측 — **`err == nil` 이 `false`** 이고 `%T` 는 `*main.MyErr`, `%v` 는 `<nil>` 이다.
  **로그에는 `<nil>` 이 찍히는데 에러 처리로 들어간다.**
- 고치는 법 — 반환값을 **`error` 로 선언**하고 성공이면 **`nil` 을 직접** 돌려준다.
  구체 포인터 타입의 변수를 그대로 `return` 하지 않는다.

### 2. ★★★ 「내 타입이 이 인터페이스를 만족하는지 도구가 알려 주겠지」

- (2)절 실측 — `go doc` 에 그 줄이 **없고**, `go vet` 은 **출력 0줄에 exit 0** 이며,
  `grep implements` 는 **0줄**이다.
- 고치는 법 — **`var _ Iface = (*T)(nil)` 을 적는다.** 그것이 그 관계를 저장하는 유일한 자리다.

### 3. ★★ 「단항 단언이 comma-ok 보다 짧으니 쓰자」

- (4)절 실측 — 틀리면 **`panic: interface conversion: io.Reader is *strings.Reader, not *os.File`**,
  종료 코드 2다.
- 고치는 법 — **경계에서는 comma-ok** 를 쓴다. 단항은 「틀릴 수 없다」가 확실한 자리에만.

### 4. ★★ 「인터페이스가 클수록 표현력이 좋다」

- (6)절 실측 — 메서드를 셋 더 요구했더니 만족하는 타입이 **5에서 1로** 줄었다.
- 고치는 법 — **필요한 만큼만** 요구한다. `io.Reader` 가 한 줄인 이유가 그것이다.

### 5. ★★ 「인터페이스에 담으면 값이 복사 안 되겠지」

- (5)절 실측 — 인터페이스 값 자체는 **16바이트**이고 `Big{}` 은 1024다.
  **1024가 어디 갔는지는 명세에 없다** — 구현이 정한다.
- 고치는 법 — 「담으면 공짜」라고 생각하지 않는다. 궁금하면 **재야 한다**(이 문서는 안 쟀다).

### 6. ★ 「`nil` 인터페이스의 메서드를 부르면 그냥 아무 일도 안 나겠지」

- (3)절·18번 주제 (5)절 실측 — **호출 자체가 패닉**이다.
- ★ **담긴 값이 `nil` 인 것과 다르다** — 그쪽은 호출이 되고, 메서드가 그 `nil` 을 어떻게 쓰느냐에 달렸다.
- 고치는 법 — 두 상태를 갈라서 생각한다. `reflect` 의 `IsValid`·`IsNil` 이 그 둘을 가른다.

### 7. ★ 「인터페이스는 구현하는 쪽 패키지에 둬야지」

- (1)절 실측 — `report(s Sizer)` 가 구현을 **모른 채** 표준 타입 셋을 받았다.
- 고치는 법 — **쓰는 쪽에 둔다.** 그러면 구현하는 쪽이 아무것도 import 하지 않는다.

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| **메서드 집합이 맞으면 만족하는 것(암묵 구현)** | **명세 보장** | "A type T implements an interface I if T … is an element of the type set of I" |
| **구현 선언 문법이 없는 것** | **명세 보장** | 문법에 그런 생산이 없다 |
| **인터페이스 값이 (동적 타입, 동적 값)인 것** | **명세 보장** | "identical dynamic types and equal dynamic values or if both have value nil" |
| **두 칸이 다 비어야 `nil` 인 것** | **명세 보장** | 〃 |
| **`nil` 인터페이스의 메서드 호출이 패닉인 것** | **명세 보장** | "calling or evaluating the method x.f causes a run-time panic" |
| **comma-ok 가 제로값과 `false` 를 주고 패닉하지 않는 것** | **명세 보장** | "the value of v is the zero value for type T. No run-time panic occurs" |
| **단항 단언이 틀리면 패닉인 것** | **명세 보장** | "If the type assertion is false, a run-time panic occurs" |
| **`any` 가 빈 인터페이스의 별칭인 것** | **명세 보장 + 판 경계(1.18)** | "any is an alias for the empty interface … [Go 1.18]" |
| **인터페이스가 다른 인터페이스를 담을 수 있는 것** | **명세 보장** | Interface types 절의 Embedded interfaces |
| **인터페이스 값이 16바이트인 것** | **구현·플랫폼** | 명세에 그 수가 없다 |
| **담긴 값이 어디에 놓이나**(힙/스택) | **구현(gc)** | 명세에 그 낱말이 없다([목록의 **52번 주제**](../52-tools-gofmt-vet-build-tags-embed-and-escape-analysis/)) |
| 패닉·컴파일 에러의 **문구 자체** | **툴체인 판(go1.27.1)** | 규칙은 명세, 문장은 gc 의 것 |
| `go doc` 의 **차례와 꼴** | **도구(구현)** | 판이 바뀌면 달라질 수 있다 |
| **「만족 목록을 주는 도구가 없다」** | ★ **언어 설계의 결과** | 관계가 어디에도 저장되지 않는다 |
| `go vet` 이 **만족 여부를 안 보는 것** | **도구(구현)** | 검사 목록에 없다. 판이 오르면 달라질 수 있다 |
| 인터페이스 호출의 **실제 비용** | **안 쟀다** | 벤치마크가 없다([목록의 **50번 주제**](../50-benchmarks-testing-b-and-reading-profiles/)) |

★ 이 주제의 결론은 「**무엇이 무엇을 만족하는지는 전부 명세가 정하는데,
그 답을 들고 있는 곳이 어디에도 없다**」이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 인터페이스를 어디에 둘까 | **쓰는 쪽** | 구현하는 쪽이 아무것도 import 안 한다 |
| 메서드를 몇 개 넣을까 | **필요한 만큼만** | 넷이면 만족하는 타입이 1/5 로 준다 |
| 내 타입이 만족하는지 보장하고 싶다 | **`var _ I = (*T)(nil)`** | 도구가 안 알려 준다 |
| 에러를 돌려준다 | **`error` 로 선언하고 `nil` 을 직접** | `nil` 포인터를 담으면 `== nil` 이 거짓이 된다 |
| 담긴 타입을 되꺼낸다 | **comma-ok** | 단항은 틀리면 패닉 |
| 여러 타입을 분기한다 | **타입 스위치**(15번 주제) | comma-ok 를 늘어놓는 것보다 읽힌다 |
| 「아무거나」를 받는다 | **`any`** — 단 마지막 수단 | 타입 정보를 잃는다. 제네릭이 나은 자리가 많다(37번) |
| 인터페이스를 미리 만들어 둘까 | **필요해질 때 만든다** | 암묵 구현이라 **나중에 만들어도 기존 타입이 만족한다** |
| 두 `nil` 을 갈라야 한다 | **`reflect` 의 `IsValid`/`IsNil`** | `== nil` 만으로는 못 가른다 |

판단 규칙 두 줄.

- **인터페이스는 쓰는 쪽에서, 필요해질 때, 가장 작게 만든다.** 암묵 구현이 그 셋을 전부 허락한다.
- **`error` 를 돌려줄 때 구체 포인터 타입의 변수를 그대로 `return` 하지 마라.** 그 한 줄이 (3)절의 함정이다.

## 핵심 문장

- ★★★ **Go 는 `implements` 를 안 적는다.** 메서드 집합이 맞으면 만족한다 —
  표준 라이브러리 타입들이 **내가 방금 만든 인터페이스를 모르면서** 만족한다.
- ★★ **그래서 인터페이스를 쓰는 쪽에 둘 수 있다.** 구현하는 쪽이 아무것도 import 하지 않는다 —
  패키지 의존 방향이 통째로 달라진다.
- ★★★ **무엇이 무엇을 만족하는지 찾아 주는 도구가 없다.**
  `go doc` 에 그 줄이 없고, `go vet` 은 출력 0줄에 exit 0 이며, `grep implements` 는 0줄이다.
  **그 없음 자체가 이 주제의 결론**이다.
- ★★★ **그 자리의 관용구가 `var _ Iface = (*T)(nil)`** 이다.
  실패 모양이 셋이고(`missing method` · `wrong type for method` + `have`/`want` · `pointer receiver`),
  **적은 것만 검사된다.**
- ★★★ **인터페이스 값은 두 칸(타입, 값)이고 두 칸이 다 비어야 `nil` 이다.**
  `nil` 포인터를 담으면 **`err == nil` 이 `false` 인데 `%v` 는 `<nil>`** 이다 — 이 갈래의 유명한 함정이다.
- ★★ **두 칸을 가르는 도구는 `reflect`** 다 — `IsNil()` 이 `true`, `IsValid()` 가 `false` 로 갈린다.
- ★ **타입 단언은 두 꼴**이다. comma-ok 는 **제로값과 `false`**, 단항은
  **`panic: interface conversion: io.Reader is *strings.Reader, not *os.File`** 이다.
- ★★ **작은 인터페이스가 이기는 것은 산술이다** — 메서드를 셋 더 요구하자 만족하는 타입이 **5/5 에서 1/5** 로 줄었다.
- ★ **인터페이스 값은 16바이트**(이 플랫폼)이고, **1024바이트를 담아도 16**이다.
  담긴 값이 어디 놓이는지는 **명세에 없는 낱말**이다.
- ★★★ **이 모두가 명세다** — 만족도, 두 칸도, 패닉 조건도. 판 경계는 **`any` 라는 이름(1.18)** 하나다.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 20번)
- [19번 주제](../19-method-sets-value-vs-pointer-receiver/)(메서드 집합) — **이 주제의 직접 선행.**
  **그쪽은 「무엇이 집합에 드나」까지**, 여기는 **「그 집합이 맞았다고 치고 그 다음」** 부터
- [18번 주제](../18-embedding-and-field-method-promotion/)(임베딩) —
  인터페이스 임베딩과 「바깥이 안쪽의 인터페이스를 만족하는 것」이 거기 (5)절에 있다
- [15번 주제](../15-switch-type-switch-fallthrough-labels-and-goto/)(타입 스위치) —
  **담긴 것을 분기하는 법의 정본.** 여기는 **comma-ok 한 꼴**까지
- [17번 주제](../17-struct-literals-comparability-field-tags-and-sorting/)(구조체) —
  인터페이스 필드가 든 구조체의 `==` 가 런타임에 터지는 자리
- [목록의 **21번 주제**](../21-nil-interface-vs-interface-holding-nil-pointer/)(`nil` 인터페이스) — **(3)절의 정본.** 여기는 **한 번 던져 보는** 데까지
- [목록의 **22번 주제**](../22-type-assertion-any-and-comparable/)(타입 단언·`any`·`comparable`) — **(4)절의 정본**
- [목록의 **23번 주제**](../23-error-interface-and-errors-as-values/)(`error` 인터페이스) — (3)절의 `trap()` 이 왜 흔한 실수인지
- [목록의 **43번 주제**](../43-io-reader-writer-and-composition/)(`io.Reader`/`Writer`) — **(6)절의 정본.**
  여기는 **「작을수록 좋다」를 수로 보이는** 데까지
- [목록의 **37번 주제**](../37-generics-type-parameters-and-constraint-interfaces/)(제네릭) — 「`any` 로 받지 말고 타입 파라미터로」가 갈리는 자리
- [`../../../../oop-basics/`](../../../../oop-basics/) —
  **그쪽은 다형성 일반까지**, 여기는 **암묵 구현이 설계에 무엇을 바꾸나**부터
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **25번**
  ([`../../../rust/syntax/25-traits-definition-impl-default-methods-and-associated-types/`](../../../rust/syntax/25-traits-definition-impl-default-methods-and-associated-types/)) —
  ★★★ **그쪽은 `impl Trait for T` 를 적고 여기는 안 적는다.**
  그래서 그쪽은 **선언 자리에서**, 여기는 **쓰는 자리에서** 틀림이 드러난다
- [`../../../java/syntax/11-interfaces-default-methods/`](../../../java/syntax/11-interfaces-default-methods/) —
  **그쪽은 `implements` 를 적고 기본 구현을 준다**, 여기는 **적지도 않고 몸통도 없다**
- [`../../../kotlin/syntax/20-interfaces-default-impl-and-super/`](../../../kotlin/syntax/20-interfaces-default-impl-and-super/) —
  **그쪽은 인터페이스가 구현을 줄 수 있다**(상태는 못 준다), 여기는 **구현도 못 준다**

## 용어 풀이

- **인터페이스(interface)** — 메서드 이름과 시그니처의 목록. 명세의 낱말로는 **타입 집합**을 정의한다.
- **암묵 구현(implicit implementation)** — 적지 않아도 메서드 집합이 맞으면 만족하는 것.
- **동적 타입 / 동적 값** — 인터페이스 값이 지금 들고 있는 타입과 값. **두 칸**이다.
- **`nil` 인터페이스** — 두 칸이 다 빈 것. `== nil` 이 참이고 메서드 호출은 패닉이다.
- **`nil` 을 담은 인터페이스** — 타입 칸이 차고 값 칸이 빈 것. `== nil` 이 **거짓**이다.
- **타입 단언(type assertion)** — `x.(T)`. 단항형은 패닉, comma-ok 형은 제로값과 `false`.
- **빈 인터페이스 / `any`** — 메서드가 없는 인터페이스. 모든 타입이 만족한다. `any` 는 1.18부터의 별칭.
- **컴파일 타임 만족 단언** — `var _ Iface = (*T)(nil)`. 만족을 컴파일러에게 묻는 관용구.
- **소비자 쪽 인터페이스(consumer-side interface)** — 쓰는 패키지가 선언하는 인터페이스.
  암묵 구현이라 가능한 배치다.

---

## 더 들어가면

- 인터페이스에는 **타입 요소**(`~int | ~string`)도 들어간다 — 제네릭 제약용이다(1.18).
  그런 인터페이스는 **변수 타입으로 못 쓴다.** 이 문서는 **안 던졌다** — 정본은 [목록의 **37번 주제**](../37-generics-type-parameters-and-constraint-interfaces/)다.
- **인터페이스도 비교된다** — 동적 타입이 같고 동적 값이 같으면 같다.
  다만 **동적 타입이 비교 불가면 런타임 패닉**이다.
  실측은 [17번 주제](../17-struct-literals-comparability-field-tags-and-sorting/) (4)절에 있다.
- **메서드 이름이 겹치는 인터페이스를 둘 임베딩**해도 된다 — 명세가
  「**When embedding interfaces, methods with the same names must have identical signatures.**」라 적고,
  `Reader`·`Writer` 가 둘 다 `Close()` 를 가져도 `ReadWriter` 의 메서드가 셋이 되는 예를 싣는다.
  시그니처가 다르면 illegal 이다. 이 문서는 그 에러를 **안 던졌다.**
  ★ 명세는 그 문단(「an interface T may use a … interface type name E as an interface element」)에
  **`[Go 1.14]`** 표시를 달아 둔다 — **이 문서는 그 판 경계가 정확히 무엇을 가르는지 안 던졌다.**
- `errors.Is`/`As` 가 (3)절의 함정을 **못 막는다** — 인터페이스가 이미 안 비었기 때문이다.
  정본은 [목록의 **24번 주제**](../24-error-wrapping-and-errors-is-as-join/)다.
- **인터페이스를 값으로 담을지 포인터로 담을지**는 19번 주제의 격자가 정한다.
  그리고 **담긴 뒤에는 주소를 못 얻는다** — 인터페이스에서 꺼낸 값은 addressable 이 아니다.
  이 문서는 그 에러를 **안 던졌다.**
- Go 에는 **인터페이스를 만족하는 타입을 찾아 주는 표준 도구가 없지만**, 에디터·언어 서버가
  인덱싱해서 흉내 내 준다. 그것은 **도구의 기능**이지 언어의 것이 아니다 —
  이 문서는 에디터를 근거로 쓰지 않았다.

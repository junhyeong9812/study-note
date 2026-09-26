# go/syntax/18 — 임베딩과 필드·메서드 승격 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> ★★★ **모든 문제에서 「이 메서드의 리시버는 어느 타입인가」를 먼저 적어라.** 답이 거기서 갈린다.
> ★★ **「깊이」를 세어라** — 자기 것은 0, 임베딩 한 겹마다 +1 이다.
> ★ **답마다 「그 값을 누가 보장하나」를 같이 적어라** — 명세인가, 패키지 계약인가, 이 판의 관찰인가.
> ★ 자바를 안다면 **`extends`·`super`·가상 디스패치** 세 직관을 먼저 의심하라.
> 소스는 전부 `go build -trimpath -o prog . && ./prog` 로 던졌다. 모듈 이름은 `ex` 다.
> 컴파일 에러를 전부 보려고 몇 블록은 `-gcflags=-e` 를 붙였다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 이 메서드는 누구를 부르는가 (예측)

```go
// t18a.go
package main

import "fmt"

type Animal struct {
	Name string
}

func (a Animal) Speak() string { return "..." }

func (a Animal) Intro() string {
	return fmt.Sprintf("%s 왈 %q  (이 메서드의 리시버 타입 = %T)", a.Name, a.Speak(), a)
}

type Dog struct {
	Animal // 임베딩 — 필드 이름이 없다. 타입 이름이 곧 필드 이름이다
	Age    int
}

func (d Dog) Speak() string { return "멍" }

func main() {
	d := Dog{Animal: Animal{Name: "바둑이"}, Age: 3}

	fmt.Println("── 필드 승격 ──")
	fmt.Println("  d.Name        =", d.Name)
	fmt.Println("  d.Animal.Name =", d.Animal.Name)
	fmt.Println("  같은 칸인가   :", &d.Name == &d.Animal.Name)

	fmt.Println("── 메서드 승격 ──")
	fmt.Println("  d.Speak()        =", d.Speak(), " ← Dog 자신의 것")
	fmt.Println("  d.Animal.Speak() =", d.Animal.Speak(), " ← 승격된 것은 이쪽")

	fmt.Println("── ★ 상속이 아니다 : 승격된 Intro 안의 a.Speak() 는 Dog 를 못 본다 ──")
	fmt.Println("  d.Intro() =", d.Intro())

	fmt.Println("── 이름 있는 필드로 두면 승격이 아예 없다 ──")
	type Cat struct {
		A   Animal // 이름이 붙었다 — 임베딩이 아니다
		Age int
	}
	c := Cat{A: Animal{Name: "나비"}, Age: 2}
	fmt.Println("  c.A.Name =", c.A.Name, " · c.A.Intro() =", c.A.Intro())
}
```

- 여덟 줄은 각각 무엇으로 찍히는가?
- 「같은 칸인가」 줄은 무엇인가 — 그것이 무엇을 증명하는가?
- `d.Intro()` 가 찍는 두 가지(문장과 `%T`)는 각각 무엇인가?
- 자바에서 같은 모양을 `extends` 로 쓰면 무엇이 달라지는가?

### 2. 얕은 쪽과 깊은 쪽 (예측)

```go
// t18b.go
package main

import "fmt"

type Base struct {
	Name string
}

func (Base) Tag() string { return "Base" }

type Mid struct {
	Base        // 깊이 1 에 Base.Name 이 있다
	Name string // 깊이 0 — 얕은 쪽
}

func (Mid) Tag() string { return "Mid" }

type Deep struct {
	Mid // Mid.Name 은 깊이 1, Mid.Base.Name 은 깊이 2
}

func main() {
	m := Mid{Base: Base{Name: "밑"}, Name: "가운데"}

	fmt.Println("── 얕은 쪽이 이긴다 (깊이 0 대 깊이 1) ──")
	fmt.Println("  m.Name       =", m.Name)
	fmt.Println("  m.Base.Name  =", m.Base.Name)
	fmt.Println("  m.Tag()      =", m.Tag())
	fmt.Println("  m.Base.Tag() =", m.Base.Tag())

	d := Deep{Mid: m}
	fmt.Println("── 두 겹 밑에서도 규칙은 같다 (깊이 1 대 깊이 2) ──")
	fmt.Println("  d.Name          =", d.Name)
	fmt.Println("  d.Mid.Name      =", d.Mid.Name)
	fmt.Println("  d.Mid.Base.Name =", d.Mid.Base.Name)
	fmt.Println("  d.Tag()         =", d.Tag())

	fmt.Println("── 승격은 「이름이 하나뿐인 가장 얕은 깊이」에서만 일어난다 ──")
	d.Name = "바뀜"
	fmt.Println("  d.Name 에 쓰면 어디가 바뀌나 :",
		"d.Mid.Name =", d.Mid.Name, "· d.Mid.Base.Name =", d.Mid.Base.Name)
}
```

- 열한 줄은 각각 무엇으로 찍히는가?
- `d.Name` 이 그 값인 이유를 **깊이**로 설명하라.
- 마지막 줄에서 `d.Name = "바뀜"` 이 고친 것은 어디인가 — 안 고쳐진 곳은?
- 가려진 이름은 **사라진 것인가**?

### 3. ★★ 같은 깊이에 둘 (예측)

```go
// t18c.go
package main

import "fmt"

type L struct {
	Name string
}

func (L) Tag() string { return "L" }

type R struct {
	Name string
}

func (R) Tag() string { return "R" }

type Both struct {
	L // 깊이 1
	R // 깊이 1 — 같은 깊이에 Name 과 Tag 가 둘씩 있다
}

func main() {
	b := Both{L: L{Name: "왼"}, R: R{Name: "오"}}

	fmt.Println(b.L.Name, b.R.Name) // ① 이름을 밝히면 된다
	fmt.Println(b.L.Tag(), b.R.Tag())

	fmt.Println(b.Name)  // ② 모호하다
	fmt.Println(b.Tag()) // ③ 모호하다
}
```

- 컴파일러는 몇 줄을 거부하는가 — 메시지 전문은?
- 거부되지 **않은** 줄은 어느 것인가, 왜인가?
- `type Both struct{ L; R }` 라는 **선언 자체**는 통과하는가?
- 선언에서 막히는 경우도 있다. 어떤 모양인가?

### 4. ★ `reflect` 는 무엇을 보여 주는가 (예측)

```go
// t18d.go
package main

import (
	"fmt"
	"reflect"
)

type Base struct {
	Name string
	Code int
}

type Mid struct {
	Base
	Name string
}

type Deep struct {
	Mid
	Extra bool
}

type L struct{ Dup string }
type R struct{ Dup string }

type Both struct {
	L
	R
}

func main() {
	t := reflect.TypeOf(Deep{})
	fmt.Println("── 평평해 보이지만 중첩이다 : 바깥 타입의 필드는 둘뿐 ──")
	fmt.Println("  Deep.NumField() =", t.NumField())
	for i := range t.NumField() {
		f := t.Field(i)
		fmt.Printf("    [%d] %-6s %-8v anonymous=%v\n", i, f.Name, f.Type, f.Anonymous)
	}

	fmt.Println("── FieldByName 은 경로를 Index 로 돌려준다 ──")
	for _, name := range []string{"Extra", "Name", "Code"} {
		f, ok := t.FieldByName(name)
		fmt.Printf("    %-6s ok=%-6v Index=%v  깊이=%d\n", name, ok, f.Index, len(f.Index))
	}

	fmt.Println("── 모호한 이름은 ok=false 로 돌아온다 (컴파일 에러와 같은 판정) ──")
	tb := reflect.TypeOf(Both{})
	f, ok := tb.FieldByName("Dup")
	fmt.Printf("    Both.Dup ok=%v Index=%v\n", ok, f.Index)
	fl, okl := tb.FieldByName("L")
	fmt.Printf("    Both.L   ok=%v Index=%v\n", okl, fl.Index)

	fmt.Println("── Index 로 실제 값을 꺼내 본다 ──")
	d := Deep{Mid: Mid{Base: Base{Name: "밑", Code: 7}, Name: "가운데"}, Extra: true}
	v := reflect.ValueOf(d)
	fn, _ := t.FieldByName("Name")
	fc, _ := t.FieldByName("Code")
	fmt.Printf("    Index=%v -> %q\n", fn.Index, v.FieldByIndex(fn.Index))
	fmt.Printf("    Index=%v -> %v\n", fc.Index, v.FieldByIndex(fc.Index))
	fmt.Printf("    d.Name=%q  d.Mid.Base.Name=%q\n", d.Name, d.Mid.Base.Name)
}
```

- `Deep.NumField()` 는 몇인가 — 어떤 필드가 나오는가?
- `Extra`·`Name`·`Code` 의 `Index` 는 각각 무엇인가?
- `Both.Dup` 의 `ok` 는 무엇인가 — 3번의 컴파일 에러와 무엇이 같고 무엇이 다른가?
- 마지막 두 줄은 각각 무엇으로 찍히는가?

### 5. 인터페이스가 끼어들면 (예측)

```go
// t18e.go
package main

import (
	"fmt"
	"io"
	"os"
	"strings"
)

type Greeter interface{ Greet() string }
type Counter interface{ Count() int }

// ① 인터페이스 임베딩 — 메서드 집합의 합집합이다
type GreetCounter interface {
	Greeter
	Counter
}

type Core struct{ n int }

func (c Core) Greet() string { return "안녕" }
func (c Core) Count() int    { return c.n }

// ② 구조체 임베딩 — 바깥이 안쪽의 인터페이스를 그대로 만족한다
type Wrapper struct {
	Core
	Extra string
}

// ③ 인터페이스를 구조체에 임베딩 — 「일부만 바꿔 끼우기」 관용구
type OnlyGreet struct {
	Greeter // 필드 이름이 Greeter 다. 값은 넣지 않으면 nil
}

func main() {
	var gc GreetCounter = Wrapper{Core: Core{n: 3}, Extra: "ㄱ"}
	fmt.Println("① 바깥 타입이 두 인터페이스를 다 만족한다 :", gc.Greet(), gc.Count())
	fmt.Printf("   인터페이스에 담긴 동적 타입 : %T\n", gc)

	var g Greeter = Wrapper{}
	fmt.Println("② 임베딩한 타입의 인터페이스도 그대로 :", g.Greet())

	og := OnlyGreet{Greeter: Core{}}
	fmt.Println("③ 인터페이스 필드를 채우면 그리로 간다 :", og.Greet())

	fmt.Println("④ io.ReadWriter 도 두 인터페이스의 임베딩이다")
	var rw io.ReadWriter = struct {
		io.Reader
		io.Writer
	}{Reader: strings.NewReader("hi\n"), Writer: os.Stdout}
	n, _ := io.Copy(rw, rw)
	fmt.Println("   io.Copy 가 옮긴 바이트 :", n)

	fmt.Fprintln(os.Stderr, "-- ⑤ 인터페이스 필드를 안 채우면 nil 이다. 이제 부른다 --")
	var empty OnlyGreet
	fmt.Println(empty.Greet())
	fmt.Fprintln(os.Stderr, "-- 여기는 안 온다 --")
}
```

- 빌드는 성공하는가? ①\~④는 각각 무엇으로 찍히는가?
- ①에서 `%T` 가 찍는 것은 `Wrapper` 인가 `Core` 인가 — 왜인가?
- ②의 `Wrapper` 는 `Greet` 을 안 적었다. 어떻게 `Greeter` 인가?
- ⑤에서 무엇이 나오는가 — 전문과 종료 코드는?

### 6. ★★ 같은 데이터, 다섯 모양 (예측)

```go
// t18f.go
package main

import (
	"encoding/json"
	"fmt"
)

type Meta struct {
	ID   int    `json:"id"`
	Kind string `json:"kind"`
}

type FlatDoc struct { // ① 임베딩 — 평평해진다
	Meta
	Title string `json:"title"`
}

type NamedDoc struct { // ② 이름 있는 필드 — 중첩된다
	Meta  Meta   `json:"meta"`
	Title string `json:"title"`
}

type TaggedDoc struct { // ③ 임베딩에 태그를 주면 다시 중첩된다
	Meta  `json:"meta"`
	Title string `json:"title"`
}

type L struct {
	Dup string `json:"dup"`
}

type R struct {
	Dup string `json:"dup"`
}

type Clash struct { // ④ 같은 깊이에서 JSON 이름이 겹치면
	L
	R
	Title string `json:"title"`
}

type Shadow struct { // ⑤ 얕은 쪽이 있으면 그쪽이 이긴다
	Meta
	Kind string `json:"kind"`
}

func main() {
	m := Meta{ID: 1, Kind: "ㄱ"}
	p := func(tag string, v any) {
		b, err := json.Marshal(v)
		fmt.Printf("  %-10s %s   err=%v\n", tag, b, err)
	}
	fmt.Println("── 같은 데이터를 다섯 모양으로 ──")
	p("FlatDoc", FlatDoc{Meta: m, Title: "ㄷ"})
	p("NamedDoc", NamedDoc{Meta: m, Title: "ㄷ"})
	p("TaggedDoc", TaggedDoc{Meta: m, Title: "ㄷ"})
	p("Clash", Clash{L: L{Dup: "왼"}, R: R{Dup: "오"}, Title: "ㄷ"})
	p("Shadow", Shadow{Meta: m, Kind: "얕은쪽"})

	fmt.Println("── 되읽기 ──")
	var f FlatDoc
	err := json.Unmarshal([]byte(`{"id":9,"kind":"ㄴ","title":"ㄹ"}`), &f)
	fmt.Printf("  FlatDoc 되읽기 : %+v err=%v\n", f, err)

	fmt.Println("── ④ 는 에러가 아니다 : 겹친 두 필드가 조용히 빠졌을 뿐이다 ──")
	var c Clash
	err = json.Unmarshal([]byte(`{"dup":"들어갈까","title":"ㄹ"}`), &c)
	fmt.Printf("  Clash 되읽기 : L.Dup=%q R.Dup=%q Title=%q err=%v\n", c.L.Dup, c.R.Dup, c.Title, err)
}
```

- 다섯 `Marshal` 결과는 각각 무엇인가?
- `Clash` 의 결과가 그런 이유는 무엇인가 — `err` 는 무엇인가?
- `Clash` 를 되읽으면 `L.Dup`·`R.Dup` 은 무엇이 되는가?
- 3번의 컴파일 에러와 견주면 **무엇이 다른가** — 그리고 그 규칙은 **누가 정하는가**?

### 7. 값으로 임베딩할까 포인터로 임베딩할까 (경계)

```go
// t18g.go
package main

import (
	"fmt"
	"os"
	"reflect"
)

type Base struct{ Name string }

func (b Base) Val() string  { return "Val:" + b.Name }
func (b *Base) Ptr() string { return "Ptr:" + b.Name }

type ByValue struct{ Base } // 값으로 임베딩
type ByPtr struct{ *Base }  // 포인터로 임베딩

func main() {
	fmt.Println("── 값 임베딩과 포인터 임베딩의 메서드 집합 (19번 주제로 이어진다) ──")
	for _, t := range []reflect.Type{
		reflect.TypeOf(ByValue{}), reflect.TypeOf(&ByValue{}),
		reflect.TypeOf(ByPtr{}), reflect.TypeOf(&ByPtr{}),
	} {
		names := make([]string, 0, t.NumMethod())
		for i := range t.NumMethod() {
			names = append(names, t.Method(i).Name)
		}
		fmt.Printf("  %-12v NumMethod=%d %v\n", t, t.NumMethod(), names)
	}

	bp := ByPtr{Base: &Base{Name: "ㄱ"}}
	fmt.Println("── 포인터 임베딩은 필드도 승격한다 ──")
	fmt.Println("  bp.Name =", bp.Name, " · bp.Val() =", bp.Val(), " · bp.Ptr() =", bp.Ptr())

	fmt.Fprintln(os.Stderr, "-- 임베딩한 포인터를 안 채우면 nil 이다. 이제 승격 필드를 읽는다 --")
	var empty ByPtr
	fmt.Println(empty.Name)
	fmt.Fprintln(os.Stderr, "-- 여기는 안 온다 --")
}
```

- 네 타입의 `NumMethod` 와 메서드 이름은 각각 무엇인가?
- `ByValue` 와 `*ByValue` 가 다른 이유, `ByPtr` 와 `*ByPtr` 가 같은 이유는?
- 마지막에 무엇이 나오는가 — 전문과 종료 코드는?
- 포인터 임베딩의 이득과 대가를 각각 한 줄로 적어라.

### 8. 승격된 이름을 리터럴 키로 (경계)

```go
// t18h.go
package main

import "fmt"

type Object struct{ Name, Color string }

type Point3D struct {
	Object
	X, Y, Z float64
}

type Line struct {
	Object
	P, Q Point3D
}

func main() {
	// ★ 1.27 부터 — 승격된 필드 이름을 리터럴의 키로 쓸 수 있다
	l := Line{Name: "대각", Q: Point3D{X: 1, Y: 1, Z: 1}}
	fmt.Printf("  l.Name=%q  l.Object.Name=%q  l.Q.Z=%v\n", l.Name, l.Object.Name, l.Q.Z)
	fmt.Printf("  l = %+v\n", l)

	// 1.26 이하의 적는 법 — 임베딩한 타입 이름을 키로 쓴다
	old := Line{Object: Object{Name: "대각"}, Q: Point3D{X: 1, Y: 1, Z: 1}}
	fmt.Println("  두 꼴이 같은가 :", l == old)
}
```

같은 소스를 `go.mod` 의 `go` 줄만 `go 1.26` 으로 내려 던지면 어떻게 되는가?

```go
// t18j.go
package main

import "fmt"

type Object struct{ Name, Color string }

type ByPtr struct {
	*Object // 포인터로 임베딩
	N       int
}

type Line struct {
	Object
	P int
}

func main() {
	// ① 포인터 임베딩을 지나는 승격 키는 안 된다
	a := ByPtr{Name: "ㄱ", N: 1}
	fmt.Println(a)

	// ② 임베딩한 타입과 그 안의 승격 필드를 같이 적을 수 없다
	b := Line{Object: Object{Color: "검정"}, Name: "대각"}
	fmt.Println(b)
}
```

- 첫 프로그램은 무엇을 찍는가 — 마지막 줄의 `==` 는?
- `go 1.26` 에서의 메시지 전문은 무엇인가 — 소스는 몇 글자가 바뀌었는가?
- 셋째 프로그램의 메시지 **두 줄 전문**은 무엇인가?
- 7번에서는 `bp.Name` 이 됐다. 셋째 프로그램의 ①과 **무엇이 다른가**?

### 9. 무엇이 승격을 보여 주는가 (왜)

- Go 에는 `javap -c` 같은 「컴파일러가 한 일」 덤프가 없다. 그러면 승격을 무엇으로 보이는가?
- 이름 충돌을 **일부러 만드는** 것이 왜 증명이 되는가?
- `reflect` 의 `Index` 가 말해 주는 것과 말해 주지 **않는** 것은 각각 무엇인가?
- 「승격 메서드의 리시버」는 어떻게 보이는가?

### 10. 다른 언어와 나란히 (연결)

- 자바의 `extends` 와 Go 의 임베딩은 **무엇이 결정적으로 다른가**?
- 자바의 `super.m()` 에 해당하는 것이 Go 에 있는가?
- 코틀린의 `by` 위임은 무엇을 만들어 주는가 — Go 는?
- 코틀린·자바에서 두 인터페이스의 같은 기본 구현이 충돌하면 어떻게 푸는가 — Go 는?
- Rust 에는 임베딩이 있는가?

### 11. 다른 주제와 잇기 (연결)

- 「이름을 적은 필드」의 정본은 몇 번 주제인가?
- 메서드 집합(값 리시버 대 포인터 리시버)의 정본은 몇 번 주제인가?
- `json` 태그 전체 규칙의 정본은 몇 번 주제인가?
- `*T` 가 `nil` 일 때 필드를 읽으면 패닉하는 것의 정본은 몇 번 주제인가?
- 「바깥이 안쪽의 인터페이스를 만족하는 것」이 본론이 되는 주제는 몇 번인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

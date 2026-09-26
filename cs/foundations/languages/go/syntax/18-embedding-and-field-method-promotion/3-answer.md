# go/syntax/18 — 임베딩과 필드·메서드 승격 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> 블록은 전부 `===== 소스: … =====` 로 소스를 먼저 싣는다 — **그대로 다시 던질 수 있게** 하기 위해서다.
> ★ 8번의 두 블록은 **`go.mod` 까지 소스로** 싣는다. 그 한 줄이 결과를 바꾸기 때문이다.
> ★ **근거로 읽을 칸** — 값, `==` 의 참거짓, `%T` 가 찍는 타입 이름, `NumMethod`·`NumField`·`Index`,
> 컴파일 에러 문장과 `파일:줄:칸`, 패닉 메시지 본문, 종료 코드, `json.Marshal` 이 낸 바이트.
> **근거로 읽지 않을 칸** — 패닉 첫 줄의 `pc=0x…`, 스택의 `goroutine N` 과 `+0x…`.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 리시버는 `main.Animal` 이다 — 되부름이 없다

**출력**

```text
===== 소스: t18a.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
── 필드 승격 ──
  d.Name        = 바둑이
  d.Animal.Name = 바둑이
  같은 칸인가   : true
── 메서드 승격 ──
  d.Speak()        = 멍  ← Dog 자신의 것
  d.Animal.Speak() = ...  ← 승격된 것은 이쪽
── ★ 상속이 아니다 : 승격된 Intro 안의 a.Speak() 는 Dog 를 못 본다 ──
  d.Intro() = 바둑이 왈 "..."  (이 메서드의 리시버 타입 = main.Animal)
── 이름 있는 필드로 두면 승격이 아예 없다 ──
  c.A.Name = 나비  · c.A.Intro() = 나비 왈 "..."  (이 메서드의 리시버 타입 = main.Animal)
(exit 0)
```

**왜 그런가**

- **필드 승격** — `d.Name` 과 `d.Animal.Name` 이 `"바둑이"` 로 같고,
  **`&d.Name == &d.Animal.Name` 이 `true`** 다.
  ★ 그 줄이 증명하는 것은 「값이 같다」가 아니라 **「두 이름이 한 칸이다」** 이다.
  명세: "**Promoted fields act like ordinary fields of a struct.**"
- **메서드 승격** — `d.Speak()` 는 `Dog` 자신의 것(`"멍"`)이고,
  승격된 쪽은 `d.Animal.Speak()`(`"..."`)다.
- ★★★ **`d.Intro()` 가 `바둑이 왈 "..."` 이고 리시버 타입이 `main.Animal` 이다.**
  `Intro` 는 `Animal` 의 메서드이므로 그 안의 `a.Speak()` 는 **`Animal.Speak()`** 다.
  `Dog.Speak()` 를 **안 부른다.**
- 자바에서 `extends` 로 같은 모양을 쓰면 `intro()` 안의 `this.speak()` 가
  **가상 디스패치로 `Dog.speak()`** 로 간다 — `"멍"` 이 나온다.
  **Go 에는 그 표가 없다.** 승격은 **선택자의 축약**일 뿐이다.
- 마지막 줄 — **이름 있는 필드(`A Animal`)로 두면 승격이 아예 없다.**
  `c.Name` 은 컴파일도 안 되고 `c.A.Name` 이라야 한다. **이름을 안 적는 것 하나**가 전부를 가른다.
- 층 — 전부 **명세 보장**이다.

### 2. 얕은 쪽이 이기고, 깊은 쪽은 그대로 살아 있다

**출력**

```text
===== 소스: t18b.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
── 얕은 쪽이 이긴다 (깊이 0 대 깊이 1) ──
  m.Name       = 가운데
  m.Base.Name  = 밑
  m.Tag()      = Mid
  m.Base.Tag() = Base
── 두 겹 밑에서도 규칙은 같다 (깊이 1 대 깊이 2) ──
  d.Name          = 가운데
  d.Mid.Name      = 가운데
  d.Mid.Base.Name = 밑
  d.Tag()         = Mid
── 승격은 「이름이 하나뿐인 가장 얕은 깊이」에서만 일어난다 ──
  d.Name 에 쓰면 어디가 바뀌나 : d.Mid.Name = 바뀜 · d.Mid.Base.Name = 밑
(exit 0)
```

**왜 그런가**

- `Mid` 는 자기 `Name`(깊이 0)과 `Base.Name`(깊이 1)을 갖는다.
  **가장 얕은 깊이 하나**가 뽑히므로 `m.Name` 은 `"가운데"`, `m.Tag()` 는 `"Mid"` 다. 명세:

  > **x.f denotes the field or method at the shallowest depth in T where there is such an f.**

  > The depth of a field or method f declared in T is **zero**.
  > The depth of a field or method f declared in an embedded field A in T is the depth of f in A **plus one**.

- `Deep` 에서는 `Mid.Name` 이 깊이 1, `Mid.Base.Name` 이 깊이 2다. 그래서 `d.Name` 도 `"가운데"` 다.
  `d.Tag()` 도 `"Mid"` — `Base.Tag()` 는 더 깊다.
- ★★ **`d.Name = "바뀜"` 이 고친 것은 `d.Mid.Name` 뿐**이고
  **`d.Mid.Base.Name` 은 `"밑"` 그대로**다.
- ★★★ **가려진 이름은 사라진 것이 아니다.** 메모리에 있고, 필드 이름으로 닿고,
  JSON 같은 곳에도 영향을 줄 수 있다. **「가림」은 「이름이 안 닿음」** 이지 「없어짐」이 아니다.
- 층 — 전부 **명세 보장**이다.

### 3. ★★ 두 줄만 막힌다 — 그리고 선언은 통과한다

**출력**

```text
===== 소스: t18c.go =====
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
===== 명령: go build -trimpath -gcflags=-e -o prog . =====
# ex
./t18c.go:28:16: ambiguous selector b.Name
./t18c.go:29:16: ambiguous selector b.Tag
(exit 1)
```

**왜 그런가**

- **거부되는 것은 두 줄**이다 — `ambiguous selector b.Name` 과 `ambiguous selector b.Tag`.
- 거부되지 **않은** 것은 `b.L.Name`·`b.R.Name`·`b.L.Tag()`·`b.R.Tag()` 다.
  **어느 쪽인지 적었으므로 모호하지 않다.** 에러 목록에 그 줄들이 **없다**는 것이 근거다.
- 명세:

  > **If there is not exactly one f with shallowest depth, the selector expression is illegal.**

- ★★★ **`type Both struct{ L; R }` 선언 자체는 통과한다.** 에러가 선언 줄이 아니라
  **쓰는 줄**(28·29)에 붙은 것이 그 증거다.
  ★ 그래서 **임베딩한 라이브러리에 메서드가 하나 늘면 내 타입이 나중에 깨질 수 있다.**
- **선언에서 막히는 경우**는 **필드 이름 자체가 겹칠 때**다. 명세의 예:

  > The following declaration is illegal because **field names must be unique in a struct type**:
  > `struct { T; *T; *P.T }`

  `struct{ L; L }`·`struct{ L; *L }` 가 그 꼴이다 — **임베딩 필드의 이름이 둘 다 `L`** 이기 때문이다.
  이 문서는 그 꼴을 **안 던졌다.**
- 층 — 규칙은 **명세 보장**, 문구는 **툴체인 판**이다.

### 4. ★ 평평해 보이지만 `Index` 가 깊이를 말한다

**출력**

```text
===== 소스: t18d.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
── 평평해 보이지만 중첩이다 : 바깥 타입의 필드는 둘뿐 ──
  Deep.NumField() = 2
    [0] Mid    main.Mid anonymous=true
    [1] Extra  bool     anonymous=false
── FieldByName 은 경로를 Index 로 돌려준다 ──
    Extra  ok=true   Index=[1]  깊이=1
    Name   ok=true   Index=[0 1]  깊이=2
    Code   ok=true   Index=[0 0 1]  깊이=3
── 모호한 이름은 ok=false 로 돌아온다 (컴파일 에러와 같은 판정) ──
    Both.Dup ok=false Index=[]
    Both.L   ok=true Index=[0]
── Index 로 실제 값을 꺼내 본다 ──
    Index=[0 1] -> "가운데"
    Index=[0 0 1] -> 7
    d.Name="가운데"  d.Mid.Base.Name="밑"
(exit 0)
```

**왜 그런가**

- ★★★ **`Deep.NumField()` 가 2** 다 — `[0] Mid main.Mid anonymous=true` 와 `[1] Extra bool anonymous=false`.
  **승격된 `Name`·`Code` 는 `Deep` 의 필드가 아니다.**
  `anonymous=true` 가 **임베딩 필드**라는 표시다.
- `Index` 는 경로다 — `Extra`=`[1]`(깊이 1), `Name`=`[0 1]`(깊이 2), **`Code`=`[0 0 1]`(깊이 3)** .
  ★ 선택자로는 `d.Extra`·`d.Name`·`d.Code` 가 **똑같아 보이는데** 경로 길이가 전부 다르다.
- ★★ **`Both.Dup` 은 `ok=false`, `Index=[]`** 다. 3번의 컴파일 에러와 **같은 판정**이다.
  **다른 것은 시끄러움**이다 — 컴파일러는 에러를 내고 `reflect` 는 **조용히 `false`** 를 준다.
  ★ 그래서 `reflect` 로 필드를 훑는 코드에서는 이 자리가 **조용해진다.**
  `Both.L` 은 `ok=true`, `Index=[0]` 으로 **임베딩 필드 자체는 이름으로 닿는다.**
- 마지막 두 줄 — `FieldByIndex([0 1])` 이 `"가운데"`, `FieldByIndex([0 0 1])` 이 `7` 이고,
  `d.Name="가운데"`·`d.Mid.Base.Name="밑"` 로 **두 칸이 여전히 갈라져 있다**(2번의 결론).
- 층 — 「어느 이름이 뽑히나」는 **명세 보장**, `Index` 라는 표현은 **`reflect` 의 계약**이다.

### 5. 승격이 인터페이스 만족으로 이어진다 — 그리고 안 채우면 죽는다

**출력**

```text
===== 소스: t18e.go =====
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
===== 명령: go build -trimpath -o prog . =====
(exit 0)
```

```text
===== 명령: ./prog 2>&1 =====
① 바깥 타입이 두 인터페이스를 다 만족한다 : 안녕 3
   인터페이스에 담긴 동적 타입 : main.Wrapper
② 임베딩한 타입의 인터페이스도 그대로 : 안녕
③ 인터페이스 필드를 채우면 그리로 간다 : 안녕
④ io.ReadWriter 도 두 인터페이스의 임베딩이다
hi
   io.Copy 가 옮긴 바이트 : 3
-- ⑤ 인터페이스 필드를 안 채우면 nil 이다. 이제 부른다 --
panic: runtime error: invalid memory address or nil pointer dereference
[signal SIGSEGV: segmentation violation code=0x1 addr=0x0 pc=0x4a11c9]

goroutine 1 [running]:
main.main()
	ex/t18e.go:56 +0x409
(exit 2)
```

**왜 그런가**

- **빌드는 성공**한다(exit 0).
- ① `Wrapper` 가 `GreetCounter`(= `Greeter` + `Counter`)를 만족해 `안녕 3` 을 낸다.
  **`%T` 는 `main.Wrapper`** 다 — 인터페이스에 담긴 것은 **바깥 값 전체**이지 안쪽 `Core` 가 아니다.
  (승격은 이름 해석이지 값의 교체가 아니다.)
- ② `Wrapper` 는 `Greet` 을 **안 적었는데** `Greeter` 다. 명세가 승격 메서드를 집합에 넣는다.

  > Given a struct type S and a type name T, **promoted methods are included in the method set of the struct**:
  > If S contains an embedded field T, the method sets of S and \*S both include promoted methods with receiver T.

  ★ **이것이 18번이 19·20번으로 이어지는 다리다.**
- ③ **인터페이스를 구조체에 임베딩**하면 필드 이름이 `Greeter` 가 되고, 넣은 값으로 호출이 간다.
- ④ 익명 구조체에 `io.Reader`·`io.Writer` 를 임베딩해 **그 자리에서 `io.ReadWriter`** 를 만들었다.
  `io.Copy` 가 `hi\n` 을 `os.Stdout` 에 쓰고 **3** 을 돌려준다.
- ★★ ⑤ 인터페이스 필드를 **안 채우면 `nil`** 이다 —
  **`panic: runtime error: invalid memory address or nil pointer dereference`**, **종료 코드 2**.
  명세: "If x is of interface type and has the value nil, **calling or evaluating the method x.f
  causes a run-time panic.**"
- 층 — 승격·패닉 규칙은 **명세 보장**, 패닉 **문구**는 런타임(구현)이다.

### 6. ★★ JSON 은 컴파일러와 다르게 군다 — 조용히 버린다

**출력**

```text
===== 소스: t18f.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
── 같은 데이터를 다섯 모양으로 ──
  FlatDoc    {"id":1,"kind":"ㄱ","title":"ㄷ"}   err=<nil>
  NamedDoc   {"meta":{"id":1,"kind":"ㄱ"},"title":"ㄷ"}   err=<nil>
  TaggedDoc  {"meta":{"id":1,"kind":"ㄱ"},"title":"ㄷ"}   err=<nil>
  Clash      {"title":"ㄷ"}   err=<nil>
  Shadow     {"id":1,"kind":"얕은쪽"}   err=<nil>
── 되읽기 ──
  FlatDoc 되읽기 : {Meta:{ID:9 Kind:ㄴ} Title:ㄹ} err=<nil>
── ④ 는 에러가 아니다 : 겹친 두 필드가 조용히 빠졌을 뿐이다 ──
  Clash 되읽기 : L.Dup="" R.Dup="" Title="ㄹ" err=<nil>
(exit 0)
```

**왜 그런가**

| 타입 | 결과 | 왜 |
|---|---|---|
| `FlatDoc` | `{"id":1,"kind":"ㄱ","title":"ㄷ"}` | 임베딩이라 **평평해진다** |
| `NamedDoc` | `{"meta":{"id":1,"kind":"ㄱ"},"title":"ㄷ"}` | 이름 있는 필드라 **중첩** |
| `TaggedDoc` | `{"meta":{"id":1,"kind":"ㄱ"},"title":"ㄷ"}` | ★ 임베딩에 **태그를 주면 다시 중첩** |
| `Clash` | `{"title":"ㄷ"}` | ★★★ **겹친 `dup` 둘이 다 빠졌다** |
| `Shadow` | `{"id":1,"kind":"얕은쪽"}` | 얕은 쪽이 이긴다 |

- ★★★ **`Clash` 의 `err` 는 `<nil>`** 이다. **에러가 아니다.**
  되읽기도 같다 — `{"dup":"들어갈까","title":"ㄹ"}` 를 넣어도
  **`L.Dup=""` · `R.Dup=""`** 이고 `err` 는 `<nil>` 이다.
- ★★ **3번과 견주면 성질이 갈린다** —
  선택자에서는 **컴파일 에러**로 시끄럽게 막히는데, JSON 에서는 **아무 말 없이 빠진다.**
  값을 주고받는 쪽에서 **조용히 데이터가 사라지는** 자리다.
- ★★★ **그리고 그 규칙은 명세가 아니라 `encoding/json` 의 계약**이다.
  다른 직렬화 라이브러리는 다르게 굴 수 있다 — **층을 갈라 적어야 한다.**
- 층 — 「평평해진다」·「조용히 버린다」 둘 다 **패키지 계약**이다.
  키가 **필드 선언 순서**로 나오는 것도 같은 층이다.

### 7. 값 임베딩은 1개, 포인터 임베딩은 2개

**출력**

```text
===== 소스: t18g.go =====
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
===== 명령: go build -trimpath -o prog . =====
(exit 0)
```

```text
===== 명령: ./prog 2>&1 =====
── 값 임베딩과 포인터 임베딩의 메서드 집합 (19번 주제로 이어진다) ──
  main.ByValue NumMethod=1 [Val]
  *main.ByValue NumMethod=2 [Ptr Val]
  main.ByPtr   NumMethod=2 [Ptr Val]
  *main.ByPtr  NumMethod=2 [Ptr Val]
── 포인터 임베딩은 필드도 승격한다 ──
  bp.Name = ㄱ  · bp.Val() = Val:ㄱ  · bp.Ptr() = Ptr:ㄱ
-- 임베딩한 포인터를 안 채우면 nil 이다. 이제 승격 필드를 읽는다 --
panic: runtime error: invalid memory address or nil pointer dereference
[signal SIGSEGV: segmentation violation code=0x1 addr=0x0 pc=0x4ef230]

goroutine 1 [running]:
main.main()
	ex/t18g.go:36 +0x570
(exit 2)
```

**왜 그런가**

| 타입 | `NumMethod` | 메서드 |
|---|---|---|
| `main.ByValue` | **1** | `[Val]` |
| `*main.ByValue` | **2** | `[Ptr Val]` |
| `main.ByPtr` | **2** | `[Ptr Val]` |
| `*main.ByPtr` | **2** | `[Ptr Val]` |

- 명세의 두 조항이 그대로다.

  > **If S contains an embedded field T**, the method sets of S and \*S both include promoted methods
  > with receiver T. **The method set of \*S also includes promoted methods with receiver \*T.**

  > **If S contains an embedded field \*T**, the method sets of **S and \*S both** include promoted
  > methods with receiver **T or \*T**.

  즉 `ByValue` 는 `*Base` 리시버 메서드를 **`*ByValue` 에서만** 얻고,
  `ByPtr` 는 **값에서도** 얻는다. (정본은 [19번 주제](../19-method-sets-value-vs-pointer-receiver/)다.)
- **포인터 임베딩도 필드를 승격한다** — `bp.Name` 이 `"ㄱ"` 이다.
- 마지막은 **`panic: runtime error: invalid memory address or nil pointer dereference`**,
  **종료 코드 2** 다. `var empty ByPtr` 의 `*Base` 가 `nil` 인데 `empty.Name` 을 읽었다.
  기계는 [16번 주제](../16-pointers-value-copy-semantics-new-and-make/) (6)절과 같다.
- **이득과 대가** —
  이득: **값 타입의 메서드 집합이 넓어진다**(인터페이스 만족이 쉬워진다).
  대가: **제로값이 못 쓸 상태**가 된다 — 반드시 채워야 한다.
- 층 — 메서드 집합 규칙은 **명세 보장**, 패닉 문구는 **런타임**이다.

### 8. `go.mod` 한 줄이 답을 바꾼다

**출력**

```text
===== 소스: go.mod =====
module ex

go 1.27
===== 소스: t18h.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
  l.Name="대각"  l.Object.Name="대각"  l.Q.Z=1
  l = {Object:{Name:대각 Color:} P:{Object:{Name: Color:} X:0 Y:0 Z:0} Q:{Object:{Name: Color:} X:1 Y:1 Z:1}}
  두 꼴이 같은가 : true
(exit 0)
```

```text
===== 소스: go.mod =====
module ex

go 1.26
===== 소스: t18i.go =====
package main

import "fmt"

type Object struct{ Name, Color string }

type Line struct {
	Object
	P int
}

func main() {
	l := Line{Name: "대각", P: 1} // 승격된 필드를 키로
	fmt.Println(l)
}
===== 명령: go build -trimpath -gcflags=-e -o prog . =====
# ex
./t18i.go:13:12: use of promoted field Object.Name in struct literal of type Line requires go1.27 or later (-lang was set to go1.26; check go.mod)
(exit 1)
```

```text
===== 소스: t18j.go =====
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
===== 명령: go build -trimpath -gcflags=-e -o prog . =====
# ex
./t18j.go:19:13: invalid implicit pointer indirection to reach Name
./t18j.go:23:45: cannot specify promoted field Name and enclosing embedded field Object
(exit 1)
```

**왜 그런가**

- 첫 프로그램은 `l.Name="대각"`·`l.Object.Name="대각"`·`l.Q.Z=1` 을 찍고,
  마지막 줄의 **`==` 가 `true`** 다 — 승격 키로 적은 것과 임베딩 타입 이름으로 적은 것이 **같은 값**이다.
- ★★★ **`go.mod` 의 `go` 를 `go 1.26` 으로 내리면** —
  **`use of promoted field Object.Name in struct literal of type Line requires go1.27 or later
  (-lang was set to go1.26; check go.mod)`** 이고 exit 1 이다.
  ★ **소스는 한 글자도 안 바뀌었다.** 갈린 것은 **언어 판 그 자체**이고,
  그래서 그 블록은 **`go.mod` 를 소스로 함께** 싣는다. 명세도 판을 달고 있다.

  > Each key must be a valid field selector **[Go 1.27]** for a (possibly promoted) field of the struct.

- 셋째 프로그램의 두 줄은 —
  **`invalid implicit pointer indirection to reach Name`** 과
  **`cannot specify promoted field Name and enclosing embedded field Object`** 다.

  > **The types of the embedded fields (if any) traversed to reach a selected field must not be pointer types.**

  > **A key must not denote a promoted field inside an embedded struct if that struct is also specified
  > by another key.**

- ★★ **7번의 `bp.Name` 과 무엇이 다른가** — 7번은 **선택자**이고 셋째 프로그램 ①은 **리터럴 키**다.
  **선택자는 포인터를 지나도 되고**(명세가 `p.x // (*(*p).T0).x` 예를 싣는다),
  **리터럴 키는 안 된다.** 리터럴은 **아직 없는 값을 만드는 자리**라 역참조할 대상이 없기 때문이다.
  ★ 「같은 규칙이겠지」로 읽으면 여기서 틀린다.
- 층 — 전부 **명세 보장**이고, 첫 항목에는 **1.27 이라는 판 경계**가 붙는다.

### 9. 승격을 보여 주는 세 가지 — 덤프가 없기 때문이다

**출력** — 없음(왜 문항).

**왜 그런가**

- Go 에는 자바의 `javap -c` 처럼 **컴파일러가 한 일을 교재로 읽을 수 있는 덤프가 없다.**
  `go tool objdump` 는 기계어라 **승격을 읽어 내기에 부적합**하다 — **부적용인 창**이다.
- 그래서 이 주제는 **셋으로 증명한다.**

| 방법 | 무엇을 보이나 | 블록 |
|---|---|---|
| ★★★ **일부러 이름을 충돌시킨다** | 승격이 **이름 해석 규칙**이라는 것 · 깊이가 뜻을 정한다는 것 | 3번 |
| ★★ **승격 메서드 안에서 `%T` 를 찍는다** | 리시버가 **안쪽 타입**이라는 것 = **상속이 아니라는 것** | 1번 |
| ★ **`reflect` 의 `Index` 를 뜬다** | 평평해 보이는 이름의 **실제 경로** | 4번 |

- **이름 충돌이 왜 증명이 되나** — 컴파일러가 침묵하면 아무것도 안 보이는데,
  **모호하게 만들면 컴파일러가 규칙을 말로 뱉는다**(`ambiguous selector b.Name`).
  ★ 「에러도 출력이다」의 전형이고, 이 주제에서는 **유일하게 규칙이 문장으로 나오는 자리**다.
- **`reflect` 의 `Index` 가 말해 주는 것** — 필드의 **경로와 깊이**, 그리고 모호 여부(`ok`).
  **말해 주지 않는 것** — **메서드의 리시버가 어느 타입인지**는 `Index` 로 안 나온다.
  (`reflect.Method` 의 `Func` 첫 인자로 간접적으로 보이지만, 그보다 `%T` 를 찍는 쪽이 곧바르다.)
- 층 — 「덤프가 없다」는 **도구의 사정**이고, 셋이 보여 주는 규칙은 전부 **명세 보장**이다.

### 10. 다른 언어와 나란히

**출력** — 없음(연결 문항).

**왜 그런가**

| 물음 | **Go** | **Java** | **Kotlin** | **Rust** |
|---|---|---|---|---|
| 재사용의 문법 | **임베딩**(이름 없는 필드) | `extends` · `implements` | `:` 상속 · **`by` 위임** | 트레이트 + `impl` |
| 안쪽이 바깥을 되부르나 | ★ **안 부른다** | **부른다**(가상 디스패치) | 부른다 | 트레이트 기본 메서드는 구현체를 되부른다 |
| `super` | ★ **없다** — `d.Animal.Speak()` | `super.m()` | `super<T>.m()` | `Trait::m(self)` |
| 충돌 해소 | **선택자를 길게 적는다** | ①클래스가 이김 ②더 구체적인 인터페이스 ③에러 | `override` + `super<T>` 를 **사람이 적는다** | 완전 정규화(`<T as Trait>::m`) |
| 전달 메서드가 생기나 | ★ **안 생긴다**(선택자 규칙) | 해당 없음 | ★ **컴파일러가 만들어 준다**(`by`) | 해당 없음 |
| 인터페이스 만족을 적나 | ★ **안 적는다** | `implements` | `:` | `impl Trait for T` |

- ★★★ **결정적인 갈림은 「되부름이 있나」** 다. 1번의 실측이 그것이다 —
  `d.Intro()` 안의 `a.Speak()` 가 **`Animal.Speak()`** 로 간다.
  자바라면 `Dog.speak()` 로 간다. **임베딩은 상속이 아니다.**
- 자바의 충돌 규칙은
  [`../../../java/syntax/11-interfaces-default-methods/`](../../../java/syntax/11-interfaces-default-methods/)가 정본이다 —
  「**클래스가 인터페이스를 이긴다**」가 있고, Go 에는 그런 우선순위가 없다.
  Go 는 **깊이 하나**만 본다.
- 코틀린은
  [`../../../kotlin/syntax/20-interfaces-default-impl-and-super/`](../../../kotlin/syntax/20-interfaces-default-impl-and-super/)에서
  「**컴파일러가 안 고른다. `override` + `super<T>` 로 사람이 적는다**」로 끝난다.
  Go 도 컴파일러가 안 고르는데, **적는 방법이 다르다** — 재정의가 아니라 **선택자를 길게** 적는다.
- 코틀린의 `by` 위임([`../../../kotlin/syntax/21-class-delegation-by/`](../../../kotlin/syntax/21-class-delegation-by/))이
  겉보기에 가장 가까운데, 그쪽은 **전달 메서드를 실제로 만들어** 인터페이스를 구현한다.
  Go 는 **아무것도 만들지 않는다** — 선택자가 닿을 뿐이다.
- Rust 에는 임베딩이 **없다.** `Deref` 로 흉내 내지만 트레이트 구현은 여전히
  **`impl Trait for T` 를 적어야** 한다
  (Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **25번**).

### 11. 다른 주제와 잇기

**출력** — 없음(연결 문항).

**왜 그런가**

- **「이름을 적은 필드」** — [17번 주제](../17-struct-literals-comparability-field-tags-and-sorting/).
  **이 주제의 직접 선행**이고, 리터럴·태그가 거기서 정본이다.
- **메서드 집합(값 리시버 대 포인터 리시버)** — [19번 주제](../19-method-sets-value-vs-pointer-receiver/).
  **이 주제의 직접 후행**이고, 7번의 격자가 거기서 본론이 된다.
- **`json` 태그 전체 규칙** — 목록의 **45번 주제**. 6번은 **임베딩이 만드는 네 모양**까지만 본다.
- **`*T` 가 `nil` 일 때 필드를 읽으면 패닉하는 것** —
  [16번 주제](../16-pointers-value-copy-semantics-new-and-make/) (6)절.
- **「바깥이 안쪽의 인터페이스를 만족하는 것」이 본론이 되는 주제** —
  [20번 주제](../20-interface-declaration-and-implicit-implementation/).
- 덤 — **타입 스위치로 되꺼내는 법**은 [15번 주제](../15-switch-type-switch-fallthrough-labels-and-goto/),
  **`sync.Mutex` 임베딩의 대가**는 [목록의 **32번 주제**](../32-sync-mutex-rwmutex-waitgroup-once/),
  **임베딩한 `String()` 이 무한 재귀가 되는 자리**는 목록의 **42번 주제**다.

---

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행 1회** | 재실행 결과가 `normalize-shaky.py` 로 **동일** |
| 판 확인 | `go version` | 1 | `go1.27.1 linux/amd64` |
| ★★★ 승격과 리시버 (`t18a`) | `go build && ./prog` | 1 | `d.Intro()` 가 `"..."` · 리시버 `main.Animal` · 같은 칸 `true` |
| 깊이 규칙 (`t18b`) | 〃 | 1 | `d.Name="가운데"` · `d.Mid.Base.Name="밑"` 유지 |
| ★★ 모호 (`t18c`) | `go build -gcflags=-e` | 1 | `ambiguous selector` **2건** · 선언은 통과 · exit 1 |
| `reflect` 경로 (`t18d`) | `go build && ./prog` | 1 | `NumField=2` · `Code` 의 `Index=[0 0 1]` · `Both.Dup` 은 `ok=false` |
| 인터페이스 임베딩 (`t18e`) | `go build` · `./prog 2>&1` | 2 | `io.Copy` 3바이트 · `nil` 인터페이스 호출 패닉 · **exit 2** |
| ★★ `json` 과 임베딩 (`t18f`) | `go build && ./prog` | 1 | `Clash` 가 `{"title":"ㄷ"}` · `err` 는 `<nil>` |
| 포인터 임베딩 (`t18g`) | `go build` · `./prog 2>&1` | 2 | `ByValue`=1 · `*ByValue`=2 · `ByPtr`=2 · 패닉 **exit 2** |
| 승격 키 (`t18h`) | `go build && ./prog` | 1 | 두 꼴이 `==` 로 `true` |
| ★★★ 판 경계 (`t18i`) | `go.mod` 를 `go 1.26` 으로 + `go build -gcflags=-e` | 1 | `requires go1.27 or later` · exit 1 |
| 승격 키의 제약 (`t18j`) | `go build -gcflags=-e` | 1 | 에러 **2건** · exit 1 |
| 형태 (`t18form`) | `go build && ./prog` | 1 | 네 줄 |

**구현·환경에 달린 항목**(버전이 오르거나 타깃이 바뀌면 **다시 찍어야 하는** 것)

| 항목 | 무엇에 달렸나 |
|---|---|
| `encoding/json` 이 임베딩을 **평평하게** 내고 충돌을 **조용히 버리는 것** | **패키지 계약.** 명세가 아니다 |
| `json.Marshal` 이 낸 **키 순서** | **패키지 계약**(구조체는 필드 선언 순서) |
| 컴파일 에러·패닉의 **문구 자체** | **툴체인 판(go1.27.1)** |
| 패닉 첫 줄의 `pc=0x…` · 스택의 `goroutine N` · `+0x…` | **빌드 산출물·런타임** |
| `reflect` 의 `Index`·`Anonymous` 표현 | **`reflect` 의 계약** |
| **승격 필드를 리터럴 키로 쓰는 것** | ★ **언어 판(1.27).** `go.mod` 의 `go` 줄이 정한다 |
| 승격 호출의 **실행 비용** | ★ **안 쟀다.** 벤치마크가 없다(목록의 **50번 주제**) |
| `struct{ L; L }` 처럼 **선언에서 막히는 꼴** | ★ **안 던졌다**(명세 인용만) |
| 다른 패키지의 타입(`P.T`) 임베딩 | ★ **안 던졌다** |
| 제네릭 타입 임베딩 | ★ **안 던졌다**(목록의 **37번 주제**) |
| 임베딩한 `String()` 의 무한 재귀 | ★ **안 던졌다**(목록의 **42번 주제**) |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다.

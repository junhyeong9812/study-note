# go/syntax/21 — `nil` 인터페이스와 `nil` 포인터를 담은 인터페이스 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> ★★★ **모든 문제에서 「지금 두 칸이 각각 무엇인가」를 먼저 적어라.**
> 타입 칸과 값 칸을 갈라 적으면 이 주제의 함정이 전부 풀린다.
> ★★ **「`%v` 로는 구별이 되나」를 매번 물어라** — 이 주제의 답이 늘 「아니오」다.
> ★ **「이것을 누가 막아 주나」도 같이 물어라** — 컴파일러인가, `go vet` 인가, 아무도 아닌가.
> ★ [20번 주제](../20-interface-declaration-and-implicit-implementation/) (3)절을 먼저 읽었다면
> **「두 칸이 있다」까지는 아는 것으로 치고** 여기서는 **코드 모양**을 묻는다.
> 소스는 전부 `go build -trimpath -o prog . && ./prog` 로 던졌다. 모듈 이름은 `ex` 다.
> 컴파일 에러를 전부 보려고 몇 블록은 `-gcflags=-e` 를 붙였다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 다섯 칸을 한 줄에 나란히 찍으면 (예측)

```go
// t21a.go
package main

import (
	"fmt"
	"reflect"
)

type MyErr struct{ Msg string }

func (e *MyErr) Error() string { return "MyErr:" + e.Msg }

// 인터페이스의 두 칸을 한 줄로 찍는다.
// x == nil 은 두 칸이 모두 비었을 때만 참이고, IsNil() 은 값 칸만 본다.
func slots(label string, x any) {
	rv := reflect.ValueOf(x)
	isNil := "cannot-ask" // 값 칸이 nil 을 가질 수 없는 종류
	switch {
	case !rv.IsValid():
		isNil = "no-value-slot"
	case rv.Kind() == reflect.Pointer || rv.Kind() == reflect.Map ||
		rv.Kind() == reflect.Slice || rv.Kind() == reflect.Func ||
		rv.Kind() == reflect.Chan || rv.Kind() == reflect.Interface:
		isNil = fmt.Sprintf("%v", rv.IsNil())
	}
	fmt.Printf("  %-22s x==nil:%-6v %%T=%-16T IsValid:%-6v IsNil:%s\n",
		label, x == nil, x, rv.IsValid(), isNil)
}

func main() {
	fmt.Println("-- (1) 두 칸이 다 빈 것 --")
	var pureIface error
	slots("var e error", pureIface)
	slots("untyped nil", nil)

	fmt.Println("-- (2) 타입 칸만 찬 것 : x == nil 이 false 인데 IsNil() 은 true 다 --")
	slots("(*MyErr)(nil)", (*MyErr)(nil))
	slots("(*int)(nil)", (*int)(nil))
	slots("map[string]int(nil)", map[string]int(nil))
	slots("[]int(nil)", []int(nil))
	slots("(func())(nil)", (func())(nil))
	slots("(chan int)(nil)", (chan int)(nil))

	fmt.Println("-- (3) 값 칸이 비지 않은 것 --")
	slots("&MyErr{}", &MyErr{Msg: "x"})
	slots("map[string]int{}", map[string]int{})
	slots("[]int{}", []int{})

	fmt.Println("-- (4) IsNil() 을 물을 수 없는 종류 --")
	slots("int(0)", 0)
	slots("string(\"\")", "")
	slots("struct{}{}", struct{}{})

	fmt.Println("-- (5) 인터페이스를 인터페이스에 담으면 두 칸이 그대로 복사된다 --")
	var e1 error                 // 두 칸 다 빔
	var a1 any = e1              // 담아도 여전히 두 칸 다 빔
	var e2 error = (*MyErr)(nil) // 타입 칸이 찬 것
	var a2 any = e2              // 담으면 그 두 칸이 그대로 온다
	fmt.Printf("  var a any = (빈 error)       -> a == nil : %v\n", a1 == nil)
	fmt.Printf("  var a any = (nil 담은 error) -> a == nil : %v  (%%T=%T)\n", a2 == nil, a2)
}
```

- `var e error` 줄과 `(*MyErr)(nil)` 줄의 **다섯 칸**(`x==nil`·`%T`·`IsValid`·`IsNil`)이 각각 무엇인가?
- `map[string]int(nil)`·`[]int(nil)`·`(func())(nil)`·`(chan int)(nil)` 은 위 둘 중 어느 쪽과 같은가?
- `int(0)`·`string("")`·`struct{}{}` 의 `IsNil` 칸에는 무엇이 찍히나 — 왜인가?
- 마지막 두 줄 — **빈 `error` 를 `any` 에 담으면** `a == nil` 이 무엇이고,
  **`nil` 담은 `error` 를 `any` 에 담으면** 무엇인가?

### 2. 성공 경로인데 네 번 다 들어간다 (예측)

```go
// t21b.go
package main

import "fmt"

type ValidationErr struct{ Field string }

func (e *ValidationErr) Error() string { return "invalid field: " + e.Field }

// (가) 미리 선언해 두고 분기에서만 채운다 — 가장 흔한 꼴
func validate(name string) error {
	var e *ValidationErr // 이 한 줄이 타입 칸을 정한다
	if name == "" {
		e = &ValidationErr{Field: "name"}
	}
	return e // name 이 비지 않아도 nil 이 아닌 error 가 나온다
}

// (나) 도우미가 구체 타입을 돌려주고 호출부가 그대로 넘긴다
func check(n int) *ValidationErr {
	if n < 0 {
		return &ValidationErr{Field: "n"}
	}
	return nil // 여기서는 진짜 nil 포인터다
}

func run(n int) error { return check(n) } // 담기면서 타입 칸이 찬다

// (다) 구조체 필드가 구체 타입이다
type Result struct{ Err *ValidationErr }

func (r Result) Fail() error { return r.Err }

// (라) defer 로 명명 반환값을 채운다
func withDefer(fail bool) (err error) {
	var e *ValidationErr
	defer func() { err = e }() // 성공해도 e 의 타입 칸이 실린다
	if fail {
		e = &ValidationErr{Field: "d"}
	}
	return
}

func report(label string, err error) {
	taken := "아니오"
	if err != nil {
		taken = "예"
	}
	fmt.Printf("  %-26s err==nil:%-6v %%T=%-20T %%v=%-22v if err != nil 로 들어가나:%s\n",
		label, err == nil, err, err, taken)
}

func main() {
	fmt.Println("-- 성공 경로인데 전부 함정에 빠진다 --")
	report("(가) validate(\"go\")", validate("go"))
	report("(나) run(1)", run(1))
	report("(다) Result{}.Fail()", Result{}.Fail())
	report("(라) withDefer(false)", withDefer(false))

	fmt.Println("-- 실패 경로는 정상이다 (원래 의도대로) --")
	report("(가) validate(\"\")", validate(""))
	report("(나) run(-1)", run(-1))

	fmt.Println("-- (나) 의 도우미를 구체 타입 그대로 받으면 제대로 nil 이다 --")
	p := check(1)
	fmt.Printf("  check(1) 의 정적 타입은 *ValidationErr -> p == nil : %v\n", p == nil)
	fmt.Printf("  같은 값을 error 에 담으면          -> err == nil : %v\n", error(p) == nil)
}
```

- 첫 덩어리 네 줄의 `err==nil` 칸에 무엇이 찍히나?
- 그 네 줄의 `%v` 칸에는 무엇이 찍히나?
- 마지막 두 줄 — `p := check(1)` 로 받은 `p == nil` 과 `error(p) == nil` 이 각각 무엇인가?
- 네 모양 각각에서 **타입 칸을 채우는 줄**을 한 줄씩 짚어라.

### 3. 막는 규칙 셋 (예측)

```go
// t21c.go
package main

import "fmt"

type ValidationErr struct{ Field string }

func (e *ValidationErr) Error() string { return "invalid field: " + e.Field }

// 규칙 (1) 도우미의 반환 타입도 error 로 적는다 — 구체 타입을 밖으로 내보내지 않는다
func checkA(n int) error {
	if n < 0 {
		return &ValidationErr{Field: "n"}
	}
	return nil
}
func runA(n int) error { return checkA(n) }

// 규칙 (2) 성공 경로에서 nil 을 명시로 돌려준다 — 구체 변수를 쓸 수밖에 없을 때
func validateB(name string) error {
	var e *ValidationErr
	if name == "" {
		e = &ValidationErr{Field: "name"}
	}
	if e == nil { // 두 줄이 함정을 막는다
		return nil
	}
	return e
}

// 규칙 (3) 구체 타입 변수를 아예 만들지 않는다 — 분기에서 바로 돌려준다
func validateC(name string) error {
	if name == "" {
		return &ValidationErr{Field: "name"}
	}
	return nil
}

// 규칙 (2)의 defer 판 — 명명 반환값에 쓸 때
func withDeferFixed(fail bool) (err error) {
	var e *ValidationErr
	defer func() {
		if e != nil { // 조건을 씌운다
			err = e
		}
	}()
	if fail {
		e = &ValidationErr{Field: "d"}
	}
	return
}

func report(label string, err error) {
	fmt.Printf("  %-28s err==nil:%-6v %%T=%-20T %%v=%v\n", label, err == nil, err, err)
}

func main() {
	fmt.Println("-- 성공 경로 : 세 규칙이 전부 제대로 nil 을 낸다 --")
	report("규칙(1) runA(1)", runA(1))
	report("규칙(2) validateB(\"go\")", validateB("go"))
	report("규칙(3) validateC(\"go\")", validateC("go"))
	report("규칙(2) withDeferFixed(false)", withDeferFixed(false))

	fmt.Println("-- 실패 경로 : 네 판 모두 원래대로 동작한다 --")
	report("규칙(1) runA(-1)", runA(-1))
	report("규칙(2) validateB(\"\")", validateB(""))
	report("규칙(3) validateC(\"\")", validateC(""))
	report("규칙(2) withDeferFixed(true)", withDeferFixed(true))
}
```

- 첫 덩어리 네 줄의 `err==nil` 칸에 무엇이 찍히나?
- 둘째 덩어리(실패 경로)는 어떻게 되나 — 규칙이 원래 동작을 깨뜨리나?
- `validateB` 의 `if e == nil { return nil }` 두 줄을 지우면 무엇이 달라지나?
- `withDeferFixed` 의 `if e != nil` 조건을 지우면 무엇이 달라지나?

### 4. 로그에 무엇이 찍히나 (예측)

```go
// t21d.go
package main

import (
	"errors"
	"fmt"
	"os"
)

// Error() 안에서 리시버를 읽는 흔한 판
type MyErr struct{ Msg string }

func (e *MyErr) Error() string { return "MyErr:" + e.Msg }

// nil 리시버를 스스로 막는 판 — 로그가 더 그럴듯해진다
type SafeErr struct{ Msg string }

func (e *SafeErr) Error() string {
	if e == nil {
		return "SafeErr(비어 있음)"
	}
	return "SafeErr:" + e.Msg
}

func main() {
	var bad error = (*MyErr)(nil)
	var safe error = (*SafeErr)(nil)
	var pure error

	fmt.Println("-- 로그에 찍히는 글자와 err != nil 의 답이 어긋난다 --")
	fmt.Printf("  bad  : fmt.Println -> ")
	fmt.Println(bad)
	fmt.Printf("  safe : fmt.Println -> ")
	fmt.Println(safe)
	fmt.Printf("  pure : fmt.Println -> ")
	fmt.Println(pure)

	fmt.Println("-- 그런데 세 값의 err != nil 은 이렇다 --")
	fmt.Printf("  bad  != nil : %v\n", bad != nil)
	fmt.Printf("  safe != nil : %v\n", safe != nil)
	fmt.Printf("  pure != nil : %v\n", pure != nil)

	fmt.Println("-- %v 가 <nil> 을 찍는 것은 fmt 의 계약이다 (Error() 를 안 부른다) --")
	fmt.Printf("  bad  : %%v=%v  %%s=%s  %%T=%T\n", bad, bad, bad)
	fmt.Printf("  safe : %%v=%v  %%s=%s  %%T=%T\n", safe, safe, safe)

	fmt.Println("-- errors.Is(err, nil) 은 == 와 같은 답을 준다 --")
	fmt.Printf("  errors.Is(bad,  nil) = %v   (bad == nil  은 %v)\n", errors.Is(bad, nil), bad == nil)
	fmt.Printf("  errors.Is(pure, nil) = %v   (pure == nil 은 %v)\n", errors.Is(pure, nil), pure == nil)
	fmt.Printf("  errors.Is(nil,  nil) = %v\n", errors.Is(nil, nil))
	fmt.Printf("  errors.As(bad, new(*MyErr)) = %v  <- 타입 칸이 있으니 찾아진다\n",
		errors.As(bad, new(*MyErr)))

	fmt.Fprintln(os.Stderr, "-- 이제 bad.Error() 를 직접 부른다 --")
	_ = bad.Error()
	fmt.Fprintln(os.Stderr, "-- 여기는 안 온다 --")
}
```

- 첫 덩어리 세 줄 — `fmt.Println(bad)`·`fmt.Println(safe)`·`fmt.Println(pure)` 이 각각 무엇을 찍나?
- 둘째 덩어리 — 세 값의 `err != nil` 이 각각 무엇인가?
- `errors.Is(bad, nil)`·`errors.Is(pure, nil)`·`errors.Is(nil, nil)` 은 각각 무엇인가?
- 마지막 — `bad.Error()` 를 직접 부르면 무엇이 일어나고 종료 코드는 몇인가?

### 5. 포인터만 걸리는가 (예측)

```go
// t21e.go
package main

import (
	"fmt"
	"io"
	"os"
)

type Cache interface{ Get(k string) int }

type mapCache struct{ m map[string]int }

func (c *mapCache) Get(k string) int { return c.m[k] }

// 포인터가 아닌 것들도 같은 함정에 빠진다.
func newWriter(enable bool) io.Writer {
	var f *os.File // 포인터
	if enable {
		f = os.Stdout
	}
	return f
}

func newCache(enable bool) Cache {
	var c *mapCache
	if enable {
		c = &mapCache{m: map[string]int{"a": 1}}
	}
	return c
}

func tags(enable bool) any {
	var m map[string]int // 맵
	if enable {
		m = map[string]int{"a": 1}
	}
	return m
}

func rows(enable bool) any {
	var s []int // 슬라이스
	if enable {
		s = []int{1}
	}
	return s
}

func hook(enable bool) any {
	var f func() // 함수
	if enable {
		f = func() {}
	}
	return f
}

func events(enable bool) any {
	var ch chan int // 채널
	if enable {
		ch = make(chan int, 1)
	}
	return ch
}

// 타입 스위치는 무엇을 고르나 — case nil 로 안 간다
func which(x any) string {
	switch x.(type) {
	case nil:
		return "case nil"
	case map[string]int:
		return "case map[string]int"
	case []int:
		return "case []int"
	case func():
		return "case func()"
	case chan int:
		return "case chan int"
	case io.Writer:
		return "case io.Writer"
	case Cache:
		return "case Cache"
	default:
		return "default"
	}
}

func line(label string, x any) {
	fmt.Printf("  %-22s x==nil:%-6v %%T=%-18T 타입스위치:%s\n", label, x == nil, x, which(x))
}

func main() {
	fmt.Println("-- 포인터만 걸리는 것이 아니다 : 맵·슬라이스·함수·채널도 같다 --")
	line("newWriter(false)", newWriter(false))
	line("newCache(false)", newCache(false))
	line("tags(false)", tags(false))
	line("rows(false)", rows(false))
	line("hook(false)", hook(false))
	line("events(false)", events(false))

	fmt.Println("-- 진짜 nil 인터페이스만 case nil 로 간다 --")
	var pure any
	line("var x any", pure)
	line("untyped nil", nil)

	fmt.Println("-- 채워 넣은 판 --")
	line("tags(true)", tags(true))
	line("events(true)", events(true))

	fmt.Println("-- 그런데 쓰임새는 종류마다 다르다 --")
	var m map[string]int
	fmt.Printf("  nil 맵 읽기      : m[\"a\"] = %d (패닉 없음)\n", m["a"])
	var s []int
	fmt.Printf("  nil 슬라이스 append : %v (패닉 없음)\n", append(s, 1))
	fmt.Fprintln(os.Stderr, "-- 이제 nil 함수를 부른다 --")
	var f func()
	f()
	fmt.Fprintln(os.Stderr, "-- 여기는 안 온다 --")
}
```

- 첫 덩어리 여섯 줄의 `x==nil` 칸이 전부 무엇인가?
- 그 여섯 줄이 **타입 스위치에서 어느 가지로** 가나 — `case nil` 로 가는 것이 있나?
- `nil` 맵을 읽고 `nil` 슬라이스에 `append` 하면 무엇이 되나?
- 마지막 — `nil` 함수를 부르면 무엇이 일어나고 종료 코드는 몇인가?

### 6. `go vet` 이 이것을 잡나 (예측)

```go
// t21probe.go
// go vet 에게 같은 함정을 여덟 가지 모양으로 던진다.
package main

import (
	"fmt"
	"io"
	"os"
)

type E struct{ M string }

func (e *E) Error() string { return "E:" + e.M }

// 탐침 1 — 미리 선언하고 그대로 반환
func p1() error {
	var e *E
	return e
}

// 탐침 2 — 도우미가 구체 타입, 호출부가 error 로 넓힌다
func helper() *E { return nil }
func p2() error  { return helper() }

// 탐침 3 — nil 포인터 리터럴을 바로 반환
func p3() error { return (*E)(nil) }

// 탐침 4 — 명명 반환값을 defer 로 채운다
func p4() (err error) {
	var e *E
	defer func() { err = e }()
	return
}

// 탐침 5 — 구조체 필드가 구체 타입
type R struct{ Err *E }

func p5() error { return R{}.Err }

// 탐침 6 — nil *os.File 을 io.Writer 로
func p6() io.Writer {
	var f *os.File
	return f
}

// 탐침 7 — nil 맵을 any 로
func p7() any {
	var m map[string]int
	return m
}

// 탐침 8 — 호출부가 그 결과를 nil 과 비교한다 (함정이 실제로 터지는 자리)
func caller() string {
	if err := p1(); err != nil {
		return "에러 처리로 들어갔다"
	}
	return "정상"
}

func main() {
	fmt.Println(p1() == nil, p2() == nil, p3() == nil, p4() == nil,
		p5() == nil, p6() == nil, p7() == nil, caller())
}
```

<!-- 위 소스는 vet21/probe.go 다. 같은 패키지에 탐침 여덟이 들어 있다. -->

- `go vet ./...` 의 **출력이 몇 줄**이고 종료 코드는 몇인가?
- 그 패키지가 빌드는 되나 — 되면 왜인가?
- `go tool vet help` 의 분석기 목록에서 **이름에 `nil` 이 든 것이 몇 개**이고 그것은 무슨 검사인가?
- 같은 목록에 `errorsas` 가 있다 — **어떤 실수는 잡고 이 실수는 안 잡는** 이유는 무엇인가?

### 7. 이 함정이 명세인가 구현인가 (왜)

- 「인터페이스 값이 두 칸이다」는 어느 층인가 — 명세인가 gc 인가?
- `%v` 가 `<nil>` 을 찍는 것은 어느 층인가?
- `go vet` 이 안 보는 것은 어느 층인가?
- 셋을 가르면 「이 함정은 Go 를 바꾸면 없어지나」에 어떻게 답하게 되나?

### 8. `<nil>` 이 찍혔다는 것이 무슨 뜻인가 (왜)

- `fmt` 는 `nil` 포인터의 `Error()` 를 **부르는가 안 부르는가** — 무엇으로 그것을 아는가?
- 그런데 `SafeErr` 쪽은 왜 `<nil>` 이 아닌 메시지가 찍혔나?
- 「로그에 `<nil>` 이 찍혔다」로부터 **확실히 말할 수 있는 것**은 무엇인가?
- 로그 한 줄에 무엇을 더 찍으면 두 상태가 갈리나?

### 9. 무엇으로도 못 막는 것 (경계)

- `errors.Is(err, nil)` 이 이 함정을 못 막는 이유를 **표준 라이브러리 소스 두 줄**로 답하라.
- 타입 스위치의 `case nil` 이 못 막는 이유는?
- `any` 로 한 번 감싸면 풀리는가?
- **컴파일러가 왜 안 막나** — 무엇이 틀리지 않았기 때문인가?

### 10. 어느 규칙을 고르나 (경계)

- 도우미 함수가 구체 오류 타입을 돌려주고 있다. 고칠 자리는 어디인가?
- 구조체 필드가 `*MyErr` 이다. 규칙 셋 중 무엇이 먹고 무엇이 안 먹나?
- `defer` 로 명명 반환값을 채우고 있다. 무엇을 더 적나?
- 세 규칙 중 **가장 센 것**은 무엇이고 왜인가?

### 11. 다른 언어와 나란히 (연결)

- Rust 에서 「오류가 없음」을 어떤 값으로 나타내는가 — 두 칸이 갈릴 자리가 있나?
- 자바의 `null` 에는 이 함정이 없다. 대신 무엇이 있나?
- Go 에서 이 함정이 「유명한」 이유를 **`error` 라는 인터페이스의 성질**로 설명하라.

### 12. 다른 주제와 잇기 (연결)

- 「인터페이스 값이 두 칸이다」의 정본은 몇 번 주제인가?
- 「담긴 것을 되꺼내는 법」의 정본은 몇 번 주제인가?
- `case nil` 의 정본은 몇 번 주제인가?
- `nil` 채널이 조용히 멈추는 것의 정본은 몇 번 주제인가?
- `errors.Is`/`As` 의 정본은 몇 번 주제이고, 그쪽은 이 함정을 막아 주나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

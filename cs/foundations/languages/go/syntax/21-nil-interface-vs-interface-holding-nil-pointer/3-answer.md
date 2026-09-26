# go/syntax/21 — `nil` 인터페이스와 `nil` 포인터를 담은 인터페이스 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> 블록은 전부 `===== 소스: … =====` 로 소스를 먼저 싣는다 — **그대로 다시 던질 수 있게** 하기 위해서다.
> ★ **근거로 읽을 칸** — `== nil` 의 참거짓, `%T`·`%v` 가 찍는 것, `reflect` 의 `IsValid`/`IsNil`,
> 타입 스위치가 고른 가지, 패닉 메시지 본문과 `파일:줄`, 종료 코드, `go vet` 의 **출력 줄 수**,
> 표준 라이브러리 소스의 줄 번호와 본문.
> **근거로 읽지 않을 칸** — 패닉 블록의 `pc=0x…` 와 스택 프레임의 힙 주소.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `x == nil` 은 `false` 인데 `IsNil()` 은 `true` 인 칸

**출력**

```text
===== 소스: t21a.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
-- (1) 두 칸이 다 빈 것 --
  var e error            x==nil:true   %T=<nil>            IsValid:false  IsNil:no-value-slot
  untyped nil            x==nil:true   %T=<nil>            IsValid:false  IsNil:no-value-slot
-- (2) 타입 칸만 찬 것 : x == nil 이 false 인데 IsNil() 은 true 다 --
  (*MyErr)(nil)          x==nil:false  %T=*main.MyErr      IsValid:true   IsNil:true
  (*int)(nil)            x==nil:false  %T=*int             IsValid:true   IsNil:true
  map[string]int(nil)    x==nil:false  %T=map[string]int   IsValid:true   IsNil:true
  []int(nil)             x==nil:false  %T=[]int            IsValid:true   IsNil:true
  (func())(nil)          x==nil:false  %T=func()           IsValid:true   IsNil:true
  (chan int)(nil)        x==nil:false  %T=chan int         IsValid:true   IsNil:true
-- (3) 값 칸이 비지 않은 것 --
  &MyErr{}               x==nil:false  %T=*main.MyErr      IsValid:true   IsNil:false
  map[string]int{}       x==nil:false  %T=map[string]int   IsValid:true   IsNil:false
  []int{}                x==nil:false  %T=[]int            IsValid:true   IsNil:false
-- (4) IsNil() 을 물을 수 없는 종류 --
  int(0)                 x==nil:false  %T=int              IsValid:true   IsNil:cannot-ask
  string("")             x==nil:false  %T=string           IsValid:true   IsNil:cannot-ask
  struct{}{}             x==nil:false  %T=struct {}        IsValid:true   IsNil:cannot-ask
-- (5) 인터페이스를 인터페이스에 담으면 두 칸이 그대로 복사된다 --
  var a any = (빈 error)       -> a == nil : true
  var a any = (nil 담은 error) -> a == nil : false  (%T=*main.MyErr)
(exit 0)
```

**왜 그런가**

- ★★★ **둘째 덩어리가 답이다.** 여섯 줄 전부 `x==nil:false` 인데 `IsNil:true` 다.
  **값 칸은 비었는데 인터페이스 자체는 안 비었다.** 이 한 줄이 이 주제의 전부다.
- 명세가 그 규칙을 못 박는다.

```text
===== 명령: sed -n "5204,5210p" "$(go env GOROOT)/doc/go_spec.html" | sed -e "s/<[^>]*>//g" =====

	
	Interface types that are not type parameters are comparable.
	Two interface values are equal if they have identical dynamic types
	and equal dynamic values or if both have value nil.
	
(exit 0)
```

  「둘 다 `nil`」은 **두 칸이 다 비었다**는 뜻이다. 타입 칸에 `*MyErr` 이 있으면 그 조건이 깨진다.
- `var e error` 와 `untyped nil` 은 **`IsValid:false`** 다 — `reflect` 가 **값을 아예 못 만든다.**
  그것이 「진짜 `nil` 인터페이스」의 표식이다.
- **맵·슬라이스·함수·채널이 포인터와 한 글자도 같은 줄**을 낸다. 포인터만의 문제가 아니다((5)번).
- ★ `int(0)`·`string("")`·`struct{}{}` 은 **`IsNil()` 을 물을 수 없다** — 그 종류에는
  「비었다」는 상태가 없다. 부르면 패닉이라 `Kind()` 로 먼저 걸러 놓고 물었다.
- ★★★ **마지막 두 줄** — 인터페이스를 인터페이스에 담으면 **두 칸이 그대로 복사된다.**
  빈 `error` 를 `any` 에 넣으면 `true`, `nil` 담은 `error` 를 넣으면 **`false`** 에 `%T` 가 `*main.MyErr` 이다.
  **`any` 로 감싸서 풀리지 않는다.**

### 2. 네 모양이 전부 성공 경로에서 틀린다

**출력**

```text
===== 소스: t21b.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
-- 성공 경로인데 전부 함정에 빠진다 --
  (가) validate("go")         err==nil:false  %T=*main.ValidationErr  %v=<nil> if err != nil 로 들어가나:예
  (나) run(1)                 err==nil:false  %T=*main.ValidationErr  %v=<nil> if err != nil 로 들어가나:예
  (다) Result{}.Fail()        err==nil:false  %T=*main.ValidationErr  %v=<nil> if err != nil 로 들어가나:예
  (라) withDefer(false)       err==nil:false  %T=*main.ValidationErr  %v=<nil> if err != nil 로 들어가나:예
-- 실패 경로는 정상이다 (원래 의도대로) --
  (가) validate("")           err==nil:false  %T=*main.ValidationErr  %v=invalid field: name    if err != nil 로 들어가나:예
  (나) run(-1)                err==nil:false  %T=*main.ValidationErr  %v=invalid field: n       if err != nil 로 들어가나:예
-- (나) 의 도우미를 구체 타입 그대로 받으면 제대로 nil 이다 --
  check(1) 의 정적 타입은 *ValidationErr -> p == nil : true
  같은 값을 error 에 담으면          -> err == nil : false
(exit 0)
```

**왜 그런가**

- ★★★ **첫 덩어리 네 줄이 전부 `err==nil:false` 에 `%v=<nil>`** 이고
  **`if err != nil` 로 들어갔다.** 넷 다 성공 경로다.
- 타입 칸을 채우는 줄은 각각 이것이다.

| 모양 | 타입 칸을 채우는 줄 |
|---|---|
| **(가)** | `var e *ValidationErr` 로 선언하고 `return e` |
| **(나)** | `func check(n int) *ValidationErr` 의 반환 타입 — `run` 의 `return check(n)` 에서 넓혀진다 |
| **(다)** | `type Result struct{ Err *ValidationErr }` 의 필드 타입 |
| **(라)** | `defer func() { err = e }()` — `e` 가 `*ValidationErr` 이다 |

- ★★ **마지막 두 줄이 (나)의 급소다** — 같은 값인데 **받는 변수의 정적 타입**에 따라 답이 갈린다.
  `p := check(1)` 이면 `p == nil` 이 **`true`**, `error(p)` 로 넓히면 **`false`** 다.
  ★ **`check` 함수 안에는 버그가 없다.** 버그는 `return check(n)` 한 줄에 있다.
- 둘째 덩어리(실패 경로)는 **원래대로 동작한다.** 그래서 실패 경로만 테스트하면 이 버그가 안 잡힌다 —
  ★ **성공 경로를 테스트해야** 잡힌다.

### 3. 세 규칙이 전부 `true` 를 낸다

**출력**

```text
===== 소스: t21c.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
-- 성공 경로 : 세 규칙이 전부 제대로 nil 을 낸다 --
  규칙(1) runA(1)                err==nil:true   %T=<nil>                %v=<nil>
  규칙(2) validateB("go")        err==nil:true   %T=<nil>                %v=<nil>
  규칙(3) validateC("go")        err==nil:true   %T=<nil>                %v=<nil>
  규칙(2) withDeferFixed(false)  err==nil:true   %T=<nil>                %v=<nil>
-- 실패 경로 : 네 판 모두 원래대로 동작한다 --
  규칙(1) runA(-1)               err==nil:false  %T=*main.ValidationErr  %v=invalid field: n
  규칙(2) validateB("")          err==nil:false  %T=*main.ValidationErr  %v=invalid field: name
  규칙(3) validateC("")          err==nil:false  %T=*main.ValidationErr  %v=invalid field: name
  규칙(2) withDeferFixed(true)   err==nil:false  %T=*main.ValidationErr  %v=invalid field: d
(exit 0)
```

**왜 그런가**

- ★★★ **첫 덩어리 네 줄이 전부 `err==nil:true` 에 `%T=<nil>`** 이다. 두 칸이 다 비었다.
- 둘째 덩어리 — **실패 경로는 그대로 돈다.** 규칙이 원래 동작을 깨뜨리지 않는다.
- 규칙마다 고치는 자리가 다르다.

| 규칙 | 고치는 자리 | 무엇을 막나 |
|---|---|---|
| **(1) 반환 타입을 `error` 로** | 도우미의 시그니처 | ★ **구체 타입이 밖으로 새는 것** |
| **(2) 성공 경로에서 `nil` 을 명시** | `if e == nil { return nil }` 두 줄 | 그 함수 하나 |
| **(3) 구체 타입 변수를 안 만든다** | 변수 선언 자체를 없앤다 | 그 함수 하나 |

- `validateB` 의 두 줄을 지우면 **(2)번의 (가) 모양으로 되돌아간다** — `err==nil` 이 `false` 가 된다.
- `withDeferFixed` 의 `if e != nil` 을 지우면 **(2)번의 (라) 모양**이 된다.
  `defer` 가 성공 경로에서도 `err = e` 를 실행해 타입 칸이 실린다.
- ★★ **규칙 (1)이 가장 세다.** (2)·(3)은 그 함수를 고치는 것이고 (1)은 **타입이 새는 것**을 막는다.
  (2)번의 (나) 모양이 정확히 그것 때문에 생겼다.

### 4. 로그의 `<nil>` 은 「삼켜진 패닉」일 수 있다

**출력**

```text
===== 소스: t21d.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
-- 로그에 찍히는 글자와 err != nil 의 답이 어긋난다 --
  bad  : fmt.Println -> <nil>
  safe : fmt.Println -> SafeErr(비어 있음)
  pure : fmt.Println -> <nil>
-- 그런데 세 값의 err != nil 은 이렇다 --
  bad  != nil : true
  safe != nil : true
  pure != nil : false
-- %v 가 <nil> 을 찍는 것은 fmt 의 계약이다 (Error() 를 안 부른다) --
  bad  : %v=<nil>  %s=<nil>  %T=*main.MyErr
  safe : %v=SafeErr(비어 있음)  %s=SafeErr(비어 있음)  %T=*main.SafeErr
-- errors.Is(err, nil) 은 == 와 같은 답을 준다 --
  errors.Is(bad,  nil) = false   (bad == nil  은 false)
  errors.Is(pure, nil) = true   (pure == nil 은 true)
  errors.Is(nil,  nil) = true
  errors.As(bad, new(*MyErr)) = true  <- 타입 칸이 있으니 찾아진다
-- 이제 bad.Error() 를 직접 부른다 --
panic: runtime error: invalid memory address or nil pointer dereference
[signal SIGSEGV: segmentation violation code=0x1 addr=0x0 pc=0x49e954]

goroutine 1 [running]:
main.(*MyErr).Error(...)
	ex/t21d.go:12
main.main()
	ex/t21d.go:54 +0x5f4
(exit 2)
```

**왜 그런가**

- ★★★ **세 줄이 전부 `<nil>` 로 찍히지 않는다** — `bad` 는 `<nil>`, `safe` 는 `SafeErr(비어 있음)`,
  `pure` 는 `<nil>` 이다. **그런데 `err != nil` 은 `bad`·`safe` 가 참**이고 `pure` 만 거짓이다.
  **로그와 분기가 어긋난다.**
- ★★★ **`bad` 가 `<nil>` 로 찍힌 이유가 예상과 다르다** — `fmt` 가 메서드를 **안 부른 것이 아니라**
  **부르고 터진 것을 받아 `<nil>` 로 바꿔 찍은 것**이다. 소스가 그렇게 적혀 있다.

```text
===== 명령: grep -n -A 8 "func (p \*pp) catchPanic" "$(go env GOROOT)/src/fmt/print.go" =====
580:func (p *pp) catchPanic(arg any, verb rune, method string) {
581-	if err := recover(); err != nil {
582-		// If it's a nil pointer, just say "<nil>". The likeliest causes are a
583-		// Stringer that fails to guard against nil or a nil pointer for a
584-		// value receiver, and in either case, "<nil>" is a nice result.
585-		if v := reflect.ValueOf(arg); v.Kind() == reflect.Pointer && v.IsNil() {
586-			p.buf.writeString(nilAngleString)
587-			return
588-		}
(exit 0)
```

  `if err := recover(); err != nil` **아래**에 있다는 것이 증거다.
  주석도 그 사정을 적는다 — 「a Stringer that fails to guard against nil」.
- ★★ 그래서 `safe` 는 다르다 — `Error()` 가 `nil` 리시버를 스스로 막아 **정상 반환**하므로
  `fmt` 가 그 문자열을 그대로 찍는다. ★ **사람이 보기에 멀쩡한 오류 로그**가 된다.
- **`errors.Is(err, nil)` 은 `==` 와 같은 답을 준다.** 표준 라이브러리 소스가 말한다.

```text
===== 명령: grep -n -A 8 "^func Is(err, target error) bool" "$(go env GOROOT)/src/errors/wrap.go" =====
45:func Is(err, target error) bool {
46-	if err == nil || target == nil {
47-		return err == target
48-	}
49-
50-	isComparable := reflectlite.TypeOf(target).Comparable()
51-	return is(err, target, isComparable)
52-}
53-
(exit 0)
```

  첫 두 줄 — `target` 이 `nil` 이면 사슬을 타지 않고 **`err == target` 을 그대로** 돌려준다.
  ★ **그러니 이 함정을 `errors.Is` 로 못 막는다.**
- `errors.As(bad, new(*MyErr))` 는 **`true`** 다. 타입 칸이 있으니 찾아지고,
  ★★ **찾아진 값이 `nil` 포인터**라 그것을 쓰면 그때 터진다.
- 마지막 — `bad.Error()` 는 **`panic: runtime error: invalid memory address or nil pointer dereference`**,
  종료 코드 **2** 다. ★ 스택에 **`main.(*MyErr).Error(...)` 프레임**이 찍혔다 —
  **호출 자체는 성공했고** 메서드 안에서 터진 것이다.
  [20번 주제](../20-interface-declaration-and-implicit-implementation/) (3)절의 「`nil` 인터페이스 호출」과는 다른 자리다.

### 5. 맵·슬라이스·함수·채널도 전부 같고, 뒤가 더 나쁘다

**출력**

```text
===== 소스: t21e.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
-- 포인터만 걸리는 것이 아니다 : 맵·슬라이스·함수·채널도 같다 --
  newWriter(false)       x==nil:false  %T=*os.File           타입스위치:case io.Writer
  newCache(false)        x==nil:false  %T=*main.mapCache     타입스위치:case Cache
  tags(false)            x==nil:false  %T=map[string]int     타입스위치:case map[string]int
  rows(false)            x==nil:false  %T=[]int              타입스위치:case []int
  hook(false)            x==nil:false  %T=func()             타입스위치:case func()
  events(false)          x==nil:false  %T=chan int           타입스위치:case chan int
-- 진짜 nil 인터페이스만 case nil 로 간다 --
  var x any              x==nil:true   %T=<nil>              타입스위치:case nil
  untyped nil            x==nil:true   %T=<nil>              타입스위치:case nil
-- 채워 넣은 판 --
  tags(true)             x==nil:false  %T=map[string]int     타입스위치:case map[string]int
  events(true)           x==nil:false  %T=chan int           타입스위치:case chan int
-- 그런데 쓰임새는 종류마다 다르다 --
  nil 맵 읽기      : m["a"] = 0 (패닉 없음)
  nil 슬라이스 append : [1] (패닉 없음)
-- 이제 nil 함수를 부른다 --
panic: runtime error: invalid memory address or nil pointer dereference
[signal SIGSEGV: segmentation violation code=0x1 addr=0x0 pc=0x49bd33]

goroutine 1 [running]:
main.main()
	ex/t21e.go:115 +0x373
(exit 2)
```

**왜 그런가**

- ★★★ **여섯 줄 전부 `x==nil:false`** 이고 **타입 스위치도 `case nil` 로 안 간다.**
  각자의 구체 타입 가지(또는 인터페이스 가지)로 간다.
- `case nil` 로 가는 것은 **`var x any` 와 `untyped nil` 뿐**이다 —
  명세가 `case nil` 을 **인터페이스 값 자체가 `nil` 일 때**로 정의한다
  ([15번 주제](../15-switch-type-switch-fallthrough-labels-and-goto/) (3)절).
- ★★ **`newWriter(false)` 가 `case io.Writer` 로 간 것**에 주의하라 —
  `*os.File` 이 `nil` 이어도 **`io.Writer` 를 만족한다.** 메서드 집합은 타입이 정하지 값이 정하지 않는다
  ([19번 주제](../19-method-sets-value-vs-pointer-receiver/)).
- ★★★ **쓰임새가 종류마다 달라서 뒤가 더 나쁘다.**

| 종류 | `nil` 인 채로 | 그래서 |
|---|---|---|
| **맵** | 읽기 **된다**(제로값 0) · 쓰기는 패닉 | 읽기만 하면 끝까지 안 터진다 |
| **슬라이스** | `append` **된다**(`[1]`) · `len`·`range` 도 된다 | ★ **영원히 안 터진다** |
| **함수** | 부르면 **패닉** | 바로 터진다 |
| **채널** | 송수신이 **영원히 막힌다** | ★★ 안 터지고 **멈춘다**(목록의 **29번 주제**) |
| **포인터** | 필드를 읽으면 패닉 | 메서드가 리시버를 안 쓰면 안 터진다 |

- 마지막 — `nil` 함수 호출은 **`panic: runtime error: invalid memory address or nil pointer dereference`**,
  종료 코드 **2** 다. (4)번의 `nil` 포인터 역참조와 **같은 문구**다.

### 6. `go vet` 은 탐침 8개 중 0개에 답한다

**출력**

```text
===== 소스: t21probe.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
false false false false false false false 에러 처리로 들어갔다
(exit 0)
```

```text
===== 소스: t21probe.go =====
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
===== 명령: go vet ./... =====
(exit 0)
```

**왜 그런가**

- ★★★ **여덟 탐침이 전부** `false` 이고 마지막 칸이 「**에러 처리로 들어갔다**」다.
  같은 패키지에 여덟이 다 들어 있고 **빌드가 통과한다**(종료 코드 0).
- ★★★ **`go vet ./...` 의 출력이 0줄에 종료 코드 0** 이다.
  「안 물어본 것」이 아니라 「**물었는데 조용한 것**」이다 — 그 구분을 위해 탐침 수를 선언했다.
- **빌드가 통과하는 이유는 타입이 맞기 때문**이다. `*E` 를 `error` 로 넓히는 것은 **옳은 코드**다.
  컴파일러가 거부할 근거가 없다.
- 분석기 목록에도 그 검사가 없다.

```text
===== 명령: go tool vet help | sed -n "/^Registered analyzers:/,/^By default/p" =====
Registered analyzers:

    appends      check for missing values after append
    asmdecl      report mismatches between assembly files and Go declarations
    assign       check for useless assignments
    atomic       check for common mistakes using the sync/atomic package
    bools        check for common mistakes involving boolean operators
    buildtag     check //go:build and // +build directives
    cgocall      detect some violations of the cgo pointer passing rules
    composites   check for unkeyed composite literals
    copylocks    check for locks erroneously passed by value
    defers       report common mistakes in defer statements
    directive    check Go toolchain directives such as //go:debug
    errorsas     report passing non-pointer or non-error values to errors.As
    framepointer report assembly that clobbers the frame pointer before saving it
    hostport     check format of addresses passed to net.Dial
    httpresponse check for mistakes using HTTP responses
    ifaceassert  detect impossible interface-to-interface type assertions
    loopclosure  check references to loop variables from within nested functions
    lostcancel   check cancel func returned by context.WithCancel is called
    nilfunc      check for useless comparisons between functions and nil
    printf       check consistency of Printf format strings and arguments
    shift        check for shifts that equal or exceed the width of the integer
    sigchanyzer  check for unbuffered channel of os.Signal
    slog         check for invalid structured logging calls
    stdmethods   check signature of methods of well-known interfaces
    stdversion   report uses of too-new standard library symbols
    stringintconv check for string(int) conversions
    structtag    check that struct field tags conform to reflect.StructTag.Get
    testinggoroutine report calls to (*testing.T).Fatal from goroutines started by a test
    tests        check for common mistaken usages of tests and examples
    timeformat   check for calls of (time.Time).Format or time.Parse with 2006-02-01
    unmarshal    report passing non-pointer or non-interface values to unmarshal
    unreachable  check for unreachable code
    unsafeptr    check for invalid conversions of uintptr to unsafe.Pointer
    unusedresult check for unused results of calls to some functions
    waitgroup    check for misuses of sync.WaitGroup

By default all analyzers are run.
(exit 0)
```

```text
===== 명령: echo "이름에 nil 이 든 분석기 : $(go tool vet help | sed -n "/^Registered analyzers:/,/^By default/p" | grep -c "^    .*nil")" =====
이름에 nil 이 든 분석기 : 1
(exit 0)
```

- ★★ **이름에 `nil` 이 든 분석기는 `nilfunc` 하나**이고, 그것은
  「함수를 `nil` 과 견주는 쓸모없는 비교」를 보는 **다른 검사**다.
- ★★★ 같은 목록에 **`errorsas`** 가 있다 —
  「report passing non-pointer or non-error values to errors.As」.
  **같은 도구가 `errors.As` 의 인자 실수는 잡고 이 실수는 안 잡는다**([24번 주제](../24-error-wrapping-and-errors-is-as-join/)에서 실측).
  ★ 이유는 **검사 가능성**에 있다 — `errors.As` 의 둘째 인자는 **그 자리에서** 옳고 그름이 정해지는데,
  `return p` 는 **`p` 가 실행 시점에 `nil` 인지 아닌지에 달려** 있다.
  전자는 타입만 보면 되고 후자는 값을 따라가야 한다.
- 밖의 도구는 이 머신에 없다.

```text
===== 명령: for t in staticcheck errcheck nilaway golangci-lint; do printf "%s : %s\n" "$t" "$(command -v $t || echo "PATH 에 없음")"; done =====
staticcheck : PATH 에 없음
errcheck : PATH 에 없음
nilaway : PATH 에 없음
golangci-lint : PATH 에 없음
(exit 0)
```

  ★ 네 이름 전부 없다 — 그러니 **이 문서는 그 도구들이 이 함정을 잡는지 모른다.** 모르는 것은 모른다고 적는다.

### 7. 규칙은 명세, 글자는 `fmt`, 침묵은 도구

| 사실 | 층 |
|---|---|
| 인터페이스 값이 두 칸이고 두 칸이 다 비어야 `nil` | ★★★ **명세 보장** |
| 구체 값을 넓히면 타입 칸이 차는 것 | **명세 보장** |
| `case nil` 이 인터페이스 값 자체를 보는 것 | **명세 보장** |
| `%v` 가 `<nil>` 을 찍는 것 | ★ **`fmt` 의 계약**(그것도 패닉을 받아서다) |
| `errors.Is(err, nil)` 이 `==` 와 같은 것 | **표준 라이브러리 계약** |
| `go vet` 이 안 보는 것 | ★ **도구(구현)** |
| 패닉 문구 자체 | **툴체인 판(go1.27.1)** |

- ★★★ **「이 함정은 Go 를 바꾸면 없어지나」에 대한 답은 「아니오」다.**
  두 칸은 **명세가 정한 것**이고, 두 칸이 있는 한 「타입 칸만 찬 상태」가 존재한다.
  **도구가 잡아 주게 만드는 것**은 가능하지만 그것은 도구 층의 일이다.
- ★ 반대로 **`%v` 의 글자와 `vet` 의 침묵은 바뀔 수 있다.**
  판이 오르면 다시 찍어야 하는 칸이다.

### 8. `<nil>` 로부터 확실히 말할 수 있는 것은 거의 없다

- ★★★ **`fmt` 는 `Error()` 를 부른다.** 그리고 **터진 것을 받아** 인자가 `nil` 포인터면
  `<nil>` 로 바꿔 찍는다(`fmt/print.go` 의 `catchPanic` — (4)번의 블록).
- `SafeErr` 쪽은 `Error()` 가 **정상 반환**했으므로 그 문자열이 그대로 찍혔다.
  ★ **`nil` 포인터면 무조건 `<nil>`」이 아니다.**
- ★★★ **「로그에 `<nil>` 이 찍혔다」로부터 확실한 것은 「`%v` 가 그렇게 찍었다」뿐**이다.
  가능한 상태가 최소 셋이다 — ① 진짜 `nil` 인터페이스 ② `nil` 담은 인터페이스인데 `Error()` 가 터졌다
  ③ `Error()` 가 정말 `"<nil>"` 을 돌려줬다.
- ★★ **`%T` 를 같이 찍으면 ①과 ②가 갈린다.**
  `fmt.Printf("err=%v (%T)", err, err)` — `<nil>` 이면 ①, `*main.MyErr` 이면 ②다.

### 9. 아무도 안 막는다

- ★★★ **`errors.Is(err, nil)`** — 소스가 `if err == nil || target == nil { return err == target }` 이다((4)번).
  **`== nil` 과 똑같이 속는다.**
- ★★ **`case nil`** — 인터페이스 값 자체가 `nil` 일 때만 골라진다((5)번).
  값 칸이 비었는지는 **안 본다.**
- ★★ **`any` 로 감싸기** — 두 칸이 그대로 복사된다((1)번의 마지막 두 줄).
- ★★★ **컴파일러** — `*MyErr` 을 `error` 로 넓히는 것은 **타입이 맞는 옳은 코드**다.
  거부할 근거가 없다. **금지 사례 표가 이 주제에만 비어 있는 이유**가 그것이다.
- ★ 그래서 막는 것은 **(3)번의 코드 규칙뿐**이다.

### 10. 반환 타입을 고치는 것이 가장 세다

- **도우미가 구체 타입을 돌려주고 있다** → 규칙 (1). **도우미의 시그니처를 `error` 로** 고친다.
  호출부를 고치면 그 호출부 하나만 고쳐진다.
- **구조체 필드가 `*MyErr` 이다** → 규칙 (3)은 **안 먹는다**(필드는 변수가 아니다).
  규칙 (1)의 필드 판 — **필드 타입을 `error` 로** — 이거나 규칙 (2)를 꺼내는 메서드에 적는다.
- **`defer` 로 명명 반환값을 채운다** → `defer func() { if e != nil { err = e } }()`.
  **조건 한 줄**이 타입 칸이 실리는 것을 막는다.
- ★★★ **가장 센 것은 (1)** 이다 — (2)·(3)은 **그 함수 하나**를 고치고
  (1)은 **그 타입이 패키지 밖으로 새는 것**을 막는다. 함정이 재발할 자리를 없앤다.

### 11. Rust 에는 갈릴 칸이 없고 자바에는 다른 문제가 있다

- **Rust** — 「오류가 없음」은 `Result::Ok` 이거나 `Option::None` 이라는 **값**이다.
  `Box<dyn Error>` 자체는 **`None` 이 될 수 없고**, 「없음」을 나타내려면 `Option` 으로 한 겹 감싸야 한다.
  ★ **두 칸이 갈릴 자리가 원리상 없다** — 「비었음」이 타입에 적혀 있다.
  (Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **21번**·**22번**.)
- **자바** — `null` 은 **참조 하나**라 두 칸이 없다. 「`null` 인데 `!= null` 이 참」이 될 수 없다.
  ★ 대신 자바에는 **`NullPointerException` 이 한참 뒤에 터지는** 다른 문제가 있다
  ([`../../../java/syntax/60-null-handling/`](../../../java/syntax/60-null-handling/)).
  **Go 는 안 터지고 틀리고, 자바는 나중에 터진다.**
- ★★★ **Go 에서 이 함정이 유명한 이유**는 `error` 라는 인터페이스가
  **거의 모든 함수의 반환값**이기 때문이다. 두 칸짜리 값을 **매 함수마다 넓혀서** 돌려주니
  넓히는 자리가 코드베이스 전체에 흩어져 있다.

### 12. 다른 주제와 잇기

- 「인터페이스 값이 두 칸이다」의 정본 —
  [20번 주제](../20-interface-declaration-and-implicit-implementation/) (3)절. **여기는 그 뒤부터**다.
- 「담긴 것을 되꺼내는 법」의 정본 — [22번 주제](../22-type-assertion-any-and-comparable/)(타입 단언·`any`·`comparable`).
- `case nil` 의 정본 — [15번 주제](../15-switch-type-switch-fallthrough-labels-and-goto/) (3)절.
- `nil` 채널이 조용히 멈추는 것의 정본 — 목록의 **29번 주제**.
- `errors.Is`/`As` 의 정본 — [24번 주제](../24-error-wrapping-and-errors-is-as-join/).
  ★ **그쪽은 이 함정을 안 막는다** — 인터페이스가 이미 안 비었기 때문이다((9)번).
- 덤 — **메서드 집합**은 [19번 주제](../19-method-sets-value-vs-pointer-receiver/),
  **`nil` 맵·슬라이스가 무엇을 허락하는지**는
  [09번](../09-maps-declaration-comma-ok-delete-and-iteration-order/)·[05번](../05-arrays-vs-slices-value-and-header/)·[06번 주제](../06-len-cap-and-append-reallocation/),
  **`fmt` 의 동사**는 목록의 **42번 주제**, **`go vet` 전반**은 목록의 **52번 주제**다.

---

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행 1회** | `normalize-shaky.py` 로 **★고칠 것 0** |
| 판 확인 | `go version` | 1 | `go1.27.1 linux/amd64` |
| ★★★ 두 칸 격자 (`t21a`) | `go build && ./prog` | 1 | `x==nil:false` 인데 `IsNil:true` 인 줄 **6개** |
| ★★★ 함정 네 모양 (`t21b`) | 〃 | 1 | 성공 경로 **4/4** 가 `err!=nil` 로 들어감 |
| ★★ 막는 규칙 셋 (`t21c`) | 〃 | 1 | 성공 경로 **4/4** 가 `err==nil:true` |
| ★★ 로그와 분기의 어긋남 (`t21d`) | `go build && ./prog` | 1 | `<nil>` 인데 `!= nil` · 패닉 · **종료 코드 2** |
| ★★ 전수 — 여섯 종류 (`t21e`) | 〃 | 1 | 6/6 이 `case nil` 로 안 감 · `nil` 함수 호출 패닉 |
| ★★★ `go vet` 탐침 (`t21probe`) | `go build && ./prog` · `go vet ./...` | 2 | 빌드 exit 0 · **vet 출력 0줄 exit 0** — 탐침 **8개 중 0개** |
| 분석기 목록 | `go tool vet help \| sed …` · 세기 | 2 | 35개 중 이름에 `nil` 이 든 것 **1개**(`nilfunc`) |
| 밖의 도구 | `command -v` 네 번 | 1 | **넷 다 PATH 에 없음** |
| 명세 인용 | `sed` 로 `go_spec.html` 에서 직접 | 1 | "identical dynamic types and equal dynamic values or if both have value nil" |
| ★★ `fmt` 의 `catchPanic` | `grep` 으로 `fmt/print.go` | 1 | `recover()` **아래**에 `nil` 포인터 특례가 있다 |
| `errors.Is` 의 `nil` 처리 | `grep` 으로 `errors/wrap.go` | 1 | `if err == nil \|\| target == nil { return err == target }` |
| 형태 (`t21form`) | `go build && ./prog` | 1 | 다섯 줄 |

**구현·환경에 달린 항목**(버전이 오르거나 타깃이 바뀌면 **다시 찍어야 하는** 것)

| 항목 | 무엇에 달렸나 |
|---|---|
| 패닉 블록의 `pc=0x…` · 스택 프레임의 힙 주소 | **빌드 산출물·런타임** — 이 문서의 **유일한 흔들리는 칸** |
| 패닉 **문구 자체** | **툴체인 판(go1.27.1)** |
| `%v` 가 `nil` 포인터를 `<nil>` 로 찍는 것 | **`fmt` 의 계약**(`catchPanic`) |
| `errors.Is(err, nil)` 의 동작 | **`errors` 패키지의 계약** |
| `go vet` 이 이 함정을 안 보는 것 | **도구(구현)**. 판이 오르면 달라질 수 있다 |
| 분석기 목록의 **차례와 개수** | **도구(구현)** |
| 밖의 린터가 이 함정을 잡는지 | ★ **모른다** — 이 머신에 없다 |
| 인터페이스 넓힘·`reflect` 호출의 **비용** | ★ **안 쟀다**(목록의 **50번 주제**) |
| `%+v`·`%#v` 가 `nil` 포인터를 어떻게 찍는지 | ★ **안 던졌다**(목록의 **42번 주제**) |
| 제네릭에서 `var zero T` 가 인터페이스일 때 | ★ **안 던졌다**(목록의 **37번 주제**) |
| `nil` 채널의 송수신이 막히는 것 | ★ **안 던졌다** — (5)절은 성질만 적었다(목록의 **29번 주제**) |
| `nil` 맵에 **쓰기**가 패닉인 것 | ★ **안 던졌다** — 읽기만 던졌다([09번 주제](../09-maps-declaration-comma-ok-delete-and-iteration-order/)) |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다.

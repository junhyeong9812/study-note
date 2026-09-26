# go/syntax/27 — `panic`·`recover` 와 쓰는 자리 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> 판 경계를 보이는 블록은 **`===== 소스: go.mod =====` 까지** 싣는다.
> ★ **근거로 읽을 칸** — `[defer]` 줄의 **차례** · guard 가 받은 값 · `panic:` 첫 줄 · 프레임 이름·`파일:줄` · 종료 코드 · `%T`.
> **근거로 읽지 않을 칸** — 다른 고루틴 블록의 **`goroutine N` 의 N** · `panic({0x…})`·`pc=0x…` 주소.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `inner` → `middle` → `outer` → `main`, 본문은 0줄 · 받지 않으면 `defer` 가 먼저

**출력**

```text
===== 소스: t27a.go =====
package main

import (
	"fmt"
	"os"
)

func say(s string) { fmt.Fprintln(os.Stderr, s) }

func inner() {
	defer say("  [defer] inner")
	say("  inner  : 패닉을 던진다")
	panic("깊은 곳에서 터짐")
}

func middle() {
	defer say("  [defer] middle")
	inner()
	say("  middle : 여기는 안 온다")
}

func outer() {
	defer say("  [defer] outer")
	middle()
	say("  outer  : 여기는 안 온다")
}

func main() {
	defer func() {
		say(fmt.Sprintf("  [defer] main — recover() = %v", recover()))
	}()
	say("  main   : outer() 를 부른다")
	outer()
	say("  main   : 여기는 안 온다")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
  main   : outer() 를 부른다
  inner  : 패닉을 던진다
  [defer] inner
  [defer] middle
  [defer] outer
  [defer] main — recover() = 깊은 곳에서 터짐
(exit 0)
```

**왜 그런가**

- ★★★ **호출의 역순** — 패닉이 난 `inner` 부터 거슬러 간다. 「여기는 안 온다」는 **0줄**, 종료 코드 **0**(main 의 `recover` 가 멈췄다).

**출력**

```text
===== 소스: t27b.go =====
package main

import (
	"fmt"
	"os"
)

func say(s string) { fmt.Fprintln(os.Stderr, s) }

func g() {
	defer say("  [defer] g")
	panic("아무도 안 받는 패닉")
}

func f() {
	defer say("  [defer] f")
	g()
}

func main() {
	defer say("  [defer] main")
	f()
}
===== 명령: go build -trimpath -o prog . && ./prog =====
  [defer] g
  [defer] f
  [defer] main
panic: 아무도 안 받는 패닉

goroutine 1 [running]:
main.g()
	ex/t27b.go:12 +0x3e
main.f()
	ex/t27b.go:17 +0x30
main.main()
	ex/t27b.go:22 +0x30
(exit 2)
```

- ★★★ **`[defer]` 셋이 먼저, `panic:` 이 나중** — 명세 「**At that point, the program is terminated and the error condition is reported**」.
- ★★ 종료 코드 **2** — **런타임**이 정한다. 명세는 「terminated」, `go doc builtin.panic` 은 「non-zero exit code」만 말한다.

### 2. 「`defer` 로 불린 함수 안에서 직접」만 듣는다

**출력**

```text
===== 소스: t27c.go =====
package main

import (
	"fmt"
	"os"
)

func say(format string, a ...any) { fmt.Fprintf(os.Stderr, format+"\n", a...) }

// helper 는 recover 를 부르는 도우미다.
func helper() { say("    helper 안의 recover() = %v", recover()) }

type guardObj struct{}

func (guardObj) Recover() { say("    메서드 안의 recover() = %v", recover()) }

// 판 1 — defer 된 함수 리터럴 안에서 직접 부른다
func direct() {
	defer func() { say("    리터럴 안의 recover() = %v", recover()) }()
	panic("P1")
}

// 판 2 — defer 된 함수 리터럴이 helper 를 부른다(한 겹 더)
func wrapped() {
	defer func() { helper() }()
	panic("P2")
}

// 판 3 — helper 자체를 defer 한다
func deferHelper() {
	defer helper()
	panic("P3")
}

// 판 4 — 메서드 값을 defer 한다
func deferMethod() {
	defer guardObj{}.Recover()
	panic("P4")
}

// 판 5 — recover 자체를 defer 한다
func deferRecover() {
	defer recover()
	panic("P5")
}

// 판 6 — defer 가 아닌 자리에서 부른다
func notDeferred() {
	say("    본문의 recover() = %v", recover())
	panic("P6")
}

// guard 는 바깥에서 직접 recover 해 「안쪽이 멈췄나」를 본다.
func guard(name string, f func()) {
	defer func() { say("  %-14s -> 바깥 guard 가 받은 것 = %v", name, recover()) }()
	say("  %s", name)
	f()
}

func main() {
	guard("판1 직접", direct)
	guard("판2 한 겹 더", wrapped)
	guard("판3 defer helper", deferHelper)
	guard("판4 defer 메서드", deferMethod)
	guard("판5 defer recover()", deferRecover)
	guard("판6 defer 아님", notDeferred)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
  판1 직접
    리터럴 안의 recover() = P1
  판1 직접          -> 바깥 guard 가 받은 것 = <nil>
  판2 한 겹 더
    helper 안의 recover() = <nil>
  판2 한 겹 더       -> 바깥 guard 가 받은 것 = P2
  판3 defer helper
    helper 안의 recover() = P3
  판3 defer helper -> 바깥 guard 가 받은 것 = <nil>
  판4 defer 메서드
    메서드 안의 recover() = P4
  판4 defer 메서드   -> 바깥 guard 가 받은 것 = <nil>
  판5 defer recover()
  판5 defer recover() -> 바깥 guard 가 받은 것 = P5
  판6 defer 아님
    본문의 recover() = <nil>
  판6 defer 아님    -> 바깥 guard 가 받은 것 = P6
(exit 0)
```

**왜 그런가**

| 판 | 자리 | 안쪽 `recover()` | guard 가 받은 것 | 멈췄나 |
|---|---|---|---|---|
| 1 | 리터럴 안에서 직접 | `P1` | `<nil>` | ✔ |
| 2 | 리터럴이 `helper` 를 부름 | `<nil>` | **`P2`** | ✘ |
| 3 | `defer helper()` | `P3` | `<nil>` | ✔ |
| 4 | `defer guardObj{}.Recover()` | `P4` | `<nil>` | ✔ |
| 5 | `defer recover()` | (찍을 곳 없음) | **`P5`** | ✘ |
| 6 | 본문에서 | `<nil>` | **`P6`** | ✘ |

- ★★★ 판2 대 판3 — **`helper` 가 「`defer` 로 불린 함수」 자체인가, 그 함수가 「부른」 함수인가**다. 판3 은 전자, 판2 는 후자.
- ★★ 판5 — `recover` 가 **`defer` 된 함수 그 자체**다. 「`defer` 된 함수 **안에서** 부른」 것이 아니다.
  `go doc builtin.recover` 「**inside a deferred function (but not any function called by it)**」.

**출력**

```text
===== 소스: t27c2.go =====
package main

import (
	"fmt"
	"os"
)

func helper() { fmt.Fprintln(os.Stderr, "  helper 안의 recover() =", recover()) }

func main() {
	defer func() { helper() }() // 한 겹 더 감쌌다 — 바깥 guard 가 없다
	panic("한 겹 더 감싼 recover 는 못 듣는다")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
  helper 안의 recover() = <nil>
panic: 한 겹 더 감싼 recover 는 못 듣는다

goroutine 1 [running]:
main.main()
	ex/t27c2.go:12 +0x3e
(exit 2)
```

- ★★★ `helper 안의 recover() = <nil>` 을 찍고 **`panic: 한 겹 더 감싼 recover 는 못 듣는다`, 종료 코드 2**.

### 3. 안 찍힌다 · 2 · `goroutine N` 의 N

**출력**

```text
===== 소스: t27d.go =====
package main

import (
	"fmt"
	"os"
)

func main() {
	defer func() {
		fmt.Fprintln(os.Stderr, "  [defer] main 의 recover() =", recover())
	}()
	done := make(chan struct{})
	go func() {
		fmt.Fprintln(os.Stderr, "  고루틴: 터진다")
		panic("다른 고루틴의 패닉")
	}()
	<-done // 영원히 기다린다 — 그 전에 프로세스가 끝난다
}
===== 명령: go build -trimpath -o prog . && ./prog =====
  고루틴: 터진다
panic: 다른 고루틴의 패닉

goroutine 19 [running]:
main.main.func2()
	ex/t27d.go:15 +0x58
created by main.main in goroutine 1
	ex/t27d.go:13 +0x4a
(exit 2)
```

**왜 그런가**

- ★★★ main 의 `[defer]` 줄은 **없다** — `recover` 는 **같은 고루틴**의 패닉만 보고, 그 고루틴의 맨 위에 닿으면 **프로세스가 끝난다.** 종료 코드 **2**.
- ★★ 흔들리는 칸 — **`goroutine 7 [running]:` 의 7**. 같은 바이너리가 재실행에서 `19` 도 냈다. 런타임이 매기는 id 다.

### 4. 여섯 줄 · 네 가지 · 「런타임 버그인가, 의도한 패닉인가」

**출력**

```text
===== 소스: t27f.go =====
package main

import (
	"errors"
	"fmt"
	"runtime"
)

// try 는 f 의 패닉 값을 받아 타입과 runtime.Error 여부를 찍는다.
func try(name string, f func()) {
	defer func() {
		r := recover()
		_, isRT := r.(runtime.Error)
		fmt.Printf("%-8s %%T=%-28T runtime.Error=%-5v : %v\n", name, r, isRT, r)
	}()
	f()
}

func main() {
	var s []int
	var m map[string]int
	var p *struct{ x int }
	var a any = "x"
	z := 0
	try("index", func() { _ = s[3] })
	try("nilmap", func() { m["a"] = 1 })
	try("nilptr", func() { _ = p.x })
	try("div", func() { _ = 1 / z })
	try("assert", func() { _ = a.(int) })
	try("close2", func() { c := make(chan int); close(c); close(c) })
	try("string", func() { panic("내가 던진 문자열") })
	try("error", func() { panic(errors.New("내가 던진 오류")) })
}
===== 명령: go build -trimpath -o prog . && ./prog =====
index    %T=runtime.boundsError          runtime.Error=true  : runtime error: index out of range [3] with length 0
nilmap   %T=runtime.plainError           runtime.Error=true  : assignment to entry in nil map
nilptr   %T=runtime.errorString          runtime.Error=true  : runtime error: invalid memory address or nil pointer dereference
div      %T=runtime.errorString          runtime.Error=true  : runtime error: integer divide by zero
assert   %T=*runtime.TypeAssertionError  runtime.Error=true  : interface conversion: interface {} is string, not int
close2   %T=runtime.plainError           runtime.Error=true  : close of closed channel
string   %T=string                       runtime.Error=false : 내가 던진 문자열
error    %T=*errors.errorString          runtime.Error=false : 내가 던진 오류
(exit 0)
```

**왜 그런가**

- ★★★ **`runtime.Error=true` 가 여섯 줄**(런타임이 낸 것 전부), 내가 던진 문자열·오류 두 줄은 `false`.
- ★★ 구체 타입은 **넷** — `runtime.boundsError` · `runtime.plainError`(nil 맵·닫힌 채널) · `runtime.errorString`(nil 역참조·0 나누기) · `*runtime.TypeAssertionError`.
- ★ 그래서 `recover` 뒤에 **`r.(runtime.Error)`** 로 「런타임 버그」와 「내가 의도한 패닉」을 가를 수 있다. 구체 타입 이름은 **구현 내부**라 기대지 않는다.

### 5. `0, safeDiv(7, 0): …` 대 `0, <nil>`

**출력**

```text
===== 소스: t27e.go =====
package main

import "fmt"

// safeDiv — 명명 반환값이 있어 defer 가 오류를 돌려줄 수 있다.
func safeDiv(a, b int) (q int, err error) {
	defer func() {
		if r := recover(); r != nil {
			err = fmt.Errorf("safeDiv(%d, %d): %v", a, b, r)
		}
	}()
	return a / b, nil
}

// lostDiv — 이름이 없다. defer 가 고친 err 는 지역 변수일 뿐이다.
func lostDiv(a, b int) (int, error) {
	var err error
	defer func() {
		if r := recover(); r != nil {
			err = fmt.Errorf("lostDiv(%d, %d): %v", a, b, r)
		}
	}()
	return a / b, err
}

func main() {
	q, err := safeDiv(7, 2)
	fmt.Printf("safeDiv(7, 2) = %d, %v\n", q, err)
	q, err = safeDiv(7, 0)
	fmt.Printf("safeDiv(7, 0) = %d, %v\n", q, err)
	q, err = lostDiv(7, 0)
	fmt.Printf("lostDiv(7, 0) = %d, %v   <- 패닉이 조용히 사라졌다\n", q, err)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
safeDiv(7, 2) = 3, <nil>
safeDiv(7, 0) = 0, safeDiv(7, 0): runtime error: integer divide by zero
lostDiv(7, 0) = 0, <nil>   <- 패닉이 조용히 사라졌다
(exit 0)
```

**왜 그런가**

- ★★★ `safeDiv` — `defer` 가 **명명 반환값 `err`** 에 썼다. 패닉 경로에는 `return` 문이 없으니 **결과 칸에 직접** 쓰는 것이 유일한 길이다.
- ★★★ `lostDiv` — **`0, <nil>`**. `defer` 가 고친 것은 **지역 변수**다. **패닉은 멈췄고 오류는 안 나갔다** — 호출자는 「성공, 답 0」으로 읽는다.
  **실패가 조용히 삼켜진다** — 패닉보다 나쁘다.

### 6. `<nil>` · `*runtime.PanicNilError` · `<nil>` — `go.mod` 한 줄이 갈랐다

**출력**

```text
===== 소스: go.mod =====
module ex

go 1.20
===== 소스: t27g.go =====
package main

import (
	"fmt"
	"runtime"
)

func main() {
	defer func() {
		r := recover()
		fmt.Printf("  recover() = %v\n  %%T        = %T\n  r == nil  : %v\n", r, r, r == nil)
		if e, ok := r.(runtime.Error); ok {
			fmt.Println("  runtime.Error :", e.Error())
		}
	}()
	panic(nil)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
  recover() = <nil>
  %T        = <nil>
  r == nil  : true
(exit 0)
```

```text
===== 소스: go.mod =====
module ex

go 1.21
===== 소스: t27g.go =====
package main

import (
	"fmt"
	"runtime"
)

func main() {
	defer func() {
		r := recover()
		fmt.Printf("  recover() = %v\n  %%T        = %T\n  r == nil  : %v\n", r, r, r == nil)
		if e, ok := r.(runtime.Error); ok {
			fmt.Println("  runtime.Error :", e.Error())
		}
	}()
	panic(nil)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
  recover() = runtime error: panic called with nil argument
  %T        = *runtime.PanicNilError
  r == nil  : false
  runtime.Error : runtime error: panic called with nil argument
(exit 0)
```

```text
===== 소스: go.mod =====
module ex

go 1.27
===== 소스: t27g.go =====
package main

import (
	"fmt"
	"runtime"
)

func main() {
	defer func() {
		r := recover()
		fmt.Printf("  recover() = %v\n  %%T        = %T\n  r == nil  : %v\n", r, r, r == nil)
		if e, ok := r.(runtime.Error); ok {
			fmt.Println("  runtime.Error :", e.Error())
		}
	}()
	panic(nil)
}
===== 명령: go build -trimpath -o prog . && GODEBUG=panicnil=1 ./prog =====
  recover() = <nil>
  %T        = <nil>
  r == nil  : true
(exit 0)
```

**왜 그런가**

- ★★★ `go 1.20` → **`<nil>`, `%T=<nil>`**. `go 1.21` → **`*runtime.PanicNilError`**(`runtime error: panic called with nil argument`). `go 1.27` + `GODEBUG=panicnil=1` → 다시 **`<nil>`**.
- ★★★ 가른 것 — **`go.mod` 의 `go` 줄**(과 그것이 정하는 **GODEBUG 기본값**). `godebug.md` 「**says go 1.20, then the program defaults to panicnil=1**」.
- ★★ 깨지는 보장 — 「**if a goroutine is panicking and recover was called directly by a deferred function, the return value of recover is guaranteed not to be nil**」.
  1.20 판에서는 패닉 중인데 `nil` 이다.

### 7. `[recovered, repanicked]`(1.25) · 안 바뀐다 · 가장 최근 것

- ★★ 같은 값 재패닉 — **`panic: 처음 패닉 [recovered, repanicked]`** 한 줄. **1.25 부터**다(릴리스 노트 — 예전엔 `[recovered]` + 두 번째 줄).
  ★ 이 툴체인은 1.27 하나라 **1.24 이전 런타임으로는 못 돌렸다**(제3의 상태).
- ★★ `go 1.24` 로 낮춰도 **그대로**다 —

```text
===== 소스: go.mod =====
module ex

go 1.24
===== 소스: t27h.go =====
package main

import (
	"fmt"
	"os"
)

func main() {
	defer func() {
		r := recover()
		fmt.Fprintln(os.Stderr, "  [defer] 받아서 기록하고 같은 값을 다시 던진다 :", r)
		panic(r)
	}()
	panic("처음 패닉")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
  [defer] 받아서 기록하고 같은 값을 다시 던진다 : 처음 패닉
panic: 처음 패닉 [recovered, repanicked]

goroutine 1 [running]:
main.main.func1()
	ex/t27h.go:12 +0x6d
panic({0x5572e8?, 0x4a3960?})
	runtime/panic.go:859 +0x125
main.main()
	ex/t27h.go:14 +0x3e
(exit 2)
```

  트레이스 모양은 **모듈의 언어 판이 아니라 런타임 판**이 정한다(GODEBUG 스위치도 없다).
- ★★★ 되감는 중의 새 패닉 — `recover` 가 받는 것은 **가장 최근 것**(`defer ① 안에서 또 터짐`)이다. 앞의 패닉은 **값으로는 사라지고** 트레이스의 줄로만 남는다.

```text
===== 소스: t27h2.go =====
package main

import (
	"fmt"
	"os"
)

func main() {
	defer func() {
		r := recover()
		fmt.Fprintln(os.Stderr, "  [defer ②] 받은 것 :", r)
		panic(fmt.Sprintf("문맥을 붙여 새로 던진다(%v)", r))
	}()
	defer func() {
		panic("defer ① 안에서 또 터짐") // 되감는 도중에 새 패닉
	}()
	panic("처음 패닉")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
  [defer ②] 받은 것 : defer ① 안에서 또 터짐
panic: 처음 패닉
	panic: defer ① 안에서 또 터짐 [recovered]
	panic: 문맥을 붙여 새로 던진다(defer ① 안에서 또 터짐)

goroutine 1 [running]:
main.main.func1()
	ex/t27h2.go:12 +0xaa
panic({0x55a0d8?, 0x4a5998?})
	runtime/panic.go:859 +0x125
main.main.func2()
	ex/t27h2.go:15 +0x25
panic({0x55a0d8?, 0x4a5978?})
	runtime/panic.go:859 +0x125
main.main()
	ex/t27h2.go:17 +0x4e
(exit 2)
```

### 8. `fmt` 는 글자로, `json` 은 이 판(v2)에서 안 받는다

**출력**

```text
===== 소스: t27i.go =====
package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
)

type Loud struct{}

func (Loud) String() string { panic("내 String 이 터짐") }

type Bad struct{}

func (Bad) MarshalJSON() ([]byte, error) { return nil, errors.New("내가 돌려준 오류") }

type Boom struct{}

func (Boom) MarshalJSON() ([]byte, error) { panic("내 MarshalJSON 이 터짐") }

func say(format string, a ...any) { fmt.Fprintf(os.Stderr, format+"\n", a...) }

func main() {
	say("-- fmt: String() 의 패닉을 글자로 바꿔 찍는다 --")
	say("  %%v -> %v", Loud{})
	say("  %%s -> %s", Loud{})

	say("-- json: 내가 오류로 돌려준 것은 오류가 된다 --")
	_, err := json.Marshal(Bad{})
	say("  err = %v", err)

	say("-- json: 내 패닉은 오류로 안 바꾸고 다시 던진다 --")
	_, err = json.Marshal(Boom{})
	say("  여기는 안 온다 %v", err)
}
===== 명령: go build -trimpath -o prog . && GOTRACEBACK=none ./prog =====
-- fmt: String() 의 패닉을 글자로 바꿔 찍는다 --
  %v -> %!v(PANIC=String method: 내 String 이 터짐)
  %s -> %!s(PANIC=String method: 내 String 이 터짐)
-- json: 내가 오류로 돌려준 것은 오류가 된다 --
  err = json: error calling MarshalJSON for type *main.Bad: 내가 돌려준 오류
-- json: 내 패닉은 오류로 안 바꾸고 다시 던진다 --
panic: 내 MarshalJSON 이 터짐
(exit 2)
```

**왜 그런가**

- ★★★ `fmt` — **`%!v(PANIC=String method: 내 String 이 터짐)`** 로 바꿔 찍고 **계속 간다.**
  ([21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/) (4)절 — `nil` 리시버면 `<nil>`.)
- ★★★ `json`(이 판) — **`panic: 내 MarshalJSON 이 터짐`**, `[recovered]` 표시가 **없다.** `json` 이 `recover` 를 안 했다.
- ★★★ 소스와 다른 이유 — **go1.27.1 은 `encoding/json` 을 v2 구현으로 빌드한다.**

```text
===== 명령: R="$(go env GOROOT)/src"; sed -n "5p" "$R/encoding/json/encode.go"; sed -n "5p" "$R/encoding/json/v2_encode.go"; grep -n "JSONv2:" "$R/internal/buildcfg/exp.go" =====
//go:build !goexperiment.jsonv2
//go:build goexperiment.jsonv2
87:		JSONv2:                true,
(exit 0)
```

  `encode.go`(recover 가 있는 v1)는 `//go:build !goexperiment.jsonv2` 이고 기본 실험에 **`JSONv2: true`**. **그 파일은 이 판에서 컴파일되지 않는다.**
- ★★ v1 으로 다시 빌드하면(`GOEXPERIMENT=nojsonv2`) —

```text
===== 소스: t27i.go =====
package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
)

type Loud struct{}

func (Loud) String() string { panic("내 String 이 터짐") }

type Bad struct{}

func (Bad) MarshalJSON() ([]byte, error) { return nil, errors.New("내가 돌려준 오류") }

type Boom struct{}

func (Boom) MarshalJSON() ([]byte, error) { panic("내 MarshalJSON 이 터짐") }

func say(format string, a ...any) { fmt.Fprintf(os.Stderr, format+"\n", a...) }

func main() {
	say("-- fmt: String() 의 패닉을 글자로 바꿔 찍는다 --")
	say("  %%v -> %v", Loud{})
	say("  %%s -> %s", Loud{})

	say("-- json: 내가 오류로 돌려준 것은 오류가 된다 --")
	_, err := json.Marshal(Bad{})
	say("  err = %v", err)

	say("-- json: 내 패닉은 오류로 안 바꾸고 다시 던진다 --")
	_, err = json.Marshal(Boom{})
	say("  여기는 안 온다 %v", err)
}
===== 명령: GOEXPERIMENT=nojsonv2 go build -trimpath -o prog . && GOTRACEBACK=none ./prog =====
-- fmt: String() 의 패닉을 글자로 바꿔 찍는다 --
  %v -> %!v(PANIC=String method: 내 String 이 터짐)
  %s -> %!s(PANIC=String method: 내 String 이 터짐)
-- json: 내가 오류로 돌려준 것은 오류가 된다 --
  err = json: error calling MarshalJSON for type main.Bad: 내가 돌려준 오류
-- json: 내 패닉은 오류로 안 바꾸고 다시 던진다 --
panic: 내 MarshalJSON 이 터짐 [recovered, repanicked]
(exit 2)
```

  **`[recovered, repanicked]`**. v1 은 **자기 패닉(`jsonError`)만 오류로 바꾸고 남의 패닉은 `panic(r)`** 으로 다시 던진다.
  ★ 두 판 모두 **남의 패닉을 오류로 바꿔 주지는 않는다.**

### 9. `main` 에 못 온다 · `main.init()`

**출력**

```text
===== 소스: t27j.go =====
package main

import (
	"fmt"
	"regexp"
)

// 패키지 변수 — main 보다 먼저 초기화된다. 틀린 패턴이면 거기서 패닉이다.
var ident = regexp.MustCompile(`^[a-z]+$`)
var broken = regexp.MustCompile(`(`)

func main() {
	fmt.Println("main 에 왔다", ident, broken)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
panic: regexp: Compile(`(`): error parsing regexp: missing closing ): `(`

goroutine 1 [running]:
regexp.MustCompile({0x4bf578, 0x1})
	regexp/regexp.go:312 +0xb4
main.init()
	ex/t27j.go:10 +0x53
(exit 2)
```

- ★★★ **`main 에 왔다` 가 없다.** 트레이스의 **`main.init()`** 프레임 — 패키지 변수 초기화에서 터졌다.
- ★★ **상수 패턴이 틀린 것은 프로그래머의 버그**라 첫 실행에서 바로 드러나는 편이 낫다(`go doc` 「simplifies safe initialization of global variables」).
  **입력 패턴은 실행 중의 실패**라 `regexp.Compile` 의 오류로 다룬다.

### 10. 클로저 하나 대 자리의 규칙 · 쓰는 자리는 같다 · 101 대 2

- ★★ Rust `catch_unwind` 는 **클로저 하나를 감싸 결과를 `Result` 로** 받는 함수다. Go `recover` 는 **「`defer` 로 불린 함수 안에서 직접」이라는 자리의 규칙**이다.
- ★★ 같은 판단 — **예외 처리의 대체가 아니다.** 쓰는 자리는 **경계**(FFI·스레드 풀·테스트 하네스 — Rust 23번 (6)절 / 요청 고루틴·라이브러리 내부 패닉 감추기 — 이 문서 (5)·(8)절).
- ★ 종료 코드 — Rust **101**(Rust 갈래 [23번](../../../rust/syntax/23-panic-vs-result/) (2)절), Go **2**(이 문서 (2)절). 둘 다 **런타임이 정한 값**이다.


---

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` (+ 고루틴 id 규칙 하나)로 **★고칠 것 0** |
| ★★★ 되감기 (`t27a`·`t27b`) | `go build && ./prog` | 1 | 안쪽부터 · 받지 않으면 exit 2 |
| ★★★ `recover` 자리 (`t27c`·`t27c2`) | 〃 | 1 | 판2·5·6 못 멈춤 · guard 없으면 exit 2 |
| ★★ 다른 고루틴 (`t27d`) | 〃 | 1 + 재실행 | exit 2 · **고루틴 id 가 7/19 로 흔들림** |
| ★★ 런타임 패닉 타입 (`t27f`) | 〃 | 1 | `runtime.Error` 6/8 · 구체 타입 4가지 |
| ★★ 명명 반환값 (`t27e`) | 〃 | 1 | `lostDiv` 가 `0, <nil>` |
| ★★★ `panic(nil)` 격자 (`t27g`) | **`go.mod` 의 `go` 줄만** 1.20/1.21/1.27+GODEBUG | 3 | `<nil>` · `*runtime.PanicNilError` · `<nil>` |
| ★ 재패닉 (`t27h`·`t27h_124`·`t27h2`) | 〃 | 3 | `[recovered, repanicked]` · 1.24 판도 같음 · 사슬 3줄 |
| ★★★ 경계 (`t27i`·`t27i_v1`) | `GOTRACEBACK=none` · `GOEXPERIMENT=nojsonv2` 격자 | 2 | v2 는 recover 없음 · v1 은 재패닉 |
| ★ `Must` (`t27j`) | `go build && ./prog` | 1 | `main.init()` 에서 exit 2 |

**구현·환경에 달린 항목**

| 항목 | 무엇에 달렸나 |
|---|---|
| 종료 코드 2 · 트레이스 모양 · `[recovered, repanicked]` | **런타임 판** — 1.25 이전은 이 툴체인으로 못 돌렸다 |
| 고루틴 id | **런타임** — 흔들리는 칸 |
| `boundsError`·`plainError` 같은 구체 타입 이름 | **구현 내부** |
| `encoding/json` 이 v2 로 빌드되는 것 | ★★ **이 툴체인 판의 기본 실험(`JSONv2: true`)** — 판이 바뀌면 다시 찍어라 |
| `json` 오류 문구(`*main.Bad` 대 `main.Bad`) | **구현 판** |
| `panicnil` 기본값 | **`go.mod` 의 `go` 줄 + GODEBUG** |
| `panic`/`recover` 비용 | ★ **안 쟀다** |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고
`normalize-shaky.py --rule 'goroutine \d+ \[running\]=goroutine <gid> [running]'` 로 견준다.

# go/syntax/27 — `panic`·`recover` 와 쓰는 자리 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ **모든 문제에서 「`recover` 가 어느 함수 안에서, 그 함수는 누가 불렀나」를 먼저 적어라.**
> ★★ **「이것은 명세인가 런타임인가」를 매번 물어라** — 순서는 명세, 종료 코드와 트레이스 모양은 런타임이다.
> 마커는 전부 `stderr` 로 찍었다 — 패닉 메시지와 한 흐름이라 순서가 안 흔들린다.
> 소스는 전부 `go build -trimpath -o prog . && ./prog` 로 던졌다. 모듈 이름은 `ex` 다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 세 프레임에 `defer` 를 심고 패닉하면 (예측)

```go
// t27a.go
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
```

- `[defer]` 줄 넷은 **어떤 차례**로 찍히나?
- 「여기는 안 온다」 줄은 몇 개 찍히나?
- 종료 코드는 몇인가?


```go
// t27b.go
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
```

- `recover` 가 없으면 `[defer]` 줄과 `panic:` 줄 중 **무엇이 먼저** 나오나?
- 종료 코드는 몇이고, 그것은 명세가 정한 것인가?

### 2. `recover` 를 부르는 자리 여섯 (예측)

```go
// t27c.go
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
```

- 판1\~판6 각각에서 **안쪽 `recover()` 가 받은 것**과 **바깥 guard 가 받은 것**은?
- 판2 와 판3 은 같은 `helper` 를 쓰는데 결과가 왜 갈리나?
- 판5 `defer recover()` 는 왜 못 멈추나?


```go
// t27c2.go
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
```

- guard 가 없으면 이 프로그램은 무엇을 찍고 종료 코드 몇으로 끝나나?

### 3. 다른 고루틴이 터지면 (예측)

```go
// t27d.go
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
```

- main 의 `[defer]` 줄이 찍히나?
- 종료 코드는 몇인가?
- 이 블록에서 **재실행마다 흔들리는 칸**은 어디인가?

### 4. 런타임 패닉의 값 (예측)

```go
// t27f.go
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
```

- 여덟 줄 중 `runtime.Error=true` 는 몇 줄인가?
- 런타임이 낸 여섯의 **구체 타입**은 몇 가지로 갈리나?
- 이 결과로 `recover` 뒤에 무엇을 가를 수 있나?

### 5. 이름 있는 반환값과 없는 반환값 (예측)

```go
// t27e.go
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
```

- `safeDiv(7, 0)` 과 `lostDiv(7, 0)` 은 각각 무엇을 돌려주나?
- `lostDiv` 가 그 값을 돌려주는 것이 왜 가장 나쁜 조합인가?

### 6. `panic(nil)` 을 세 판으로 (예측)

```go
// t27g.go
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
```

<!-- 같은 소스를 go.mod 의 go 1.20 · go 1.21 · go 1.27 + GODEBUG=panicnil=1 로 던졌다. -->

- 세 판에서 `recover()` 의 값과 `%T` 는 각각 무엇인가?
- 소스·툴체인·명령이 같은데 무엇이 결과를 갈랐나?
- 명세의 어느 보장이 1.20 판에서 깨지나?

### 7. 재패닉과 되감는 중의 새 패닉 (경계)

- 같은 값을 다시 던지면 첫 줄이 어떤 모양인가 — 그 표시는 몇부터인가?
- `go.mod` 를 `go 1.24` 로 낮추면 그 모양이 바뀌나 — 왜인가?
- 되감는 중에 새 패닉이 나면 `recover` 는 **어느 패닉**을 받나?

### 8. 표준 라이브러리는 남의 패닉을 어떻게 하나 (경계)

- `fmt` 는 `String()` 의 패닉을 무엇으로 바꾸나?
- `encoding/json` 은 이 판에서 내 `MarshalJSON` 의 패닉을 어떻게 하나 — `[recovered]` 표시가 나오나?
- 왜 이 판의 `json` 과 `encode.go` 의 소스가 다르게 행동하나?
- v1 구현은 자기 패닉과 남의 패닉을 어떻게 가르나?

### 9. 언제 패닉이 맞나 (왜)

- `regexp.MustCompile` 에 틀린 패턴을 주면 `main` 에 도착하나 — 트레이스의 어느 프레임이 그것을 말하나?
- 상수 패턴에는 패닉이 맞고 입력 패턴에는 틀린 이유는?

### 10. 다른 언어와 나란히 (연결)

- Rust 의 `catch_unwind` 와 Go 의 `recover` 는 「무엇을 감싸나」에서 어떻게 다른가?
- 둘이 **같은 판단**을 내리는 자리는 어디인가?
- 패닉으로 끝난 프로세스의 종료 코드는 Rust 와 Go 에서 각각 몇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

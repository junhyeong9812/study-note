# go/syntax/39 — `iter` 와 사용자 정의 반복자(1.23) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ **모든 문제에서 「지금 누가 누구를 부르고 있나 — 반복자가 `yield` 를, 아니면 소비자가 `next` 를」을 먼저 그려라.**
> ★★ **「이 규칙은 명세의 것인가, `iter` 문서의 것인가, 런타임만의 것인가」를 매번 물어라.**
> 소스는 전부 `go build -trimpath -o prog .` 로 빌드했다. 모듈 이름은 `ex`, `go.mod` 는 `go 1.27` 이다(판을 바꾼 문항은 따로 적었다).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 다섯 가지로 떠나고 두 가지로 치우면 (예측)

```go
// t39clean.go
package main

import (
	"fmt"
	"iter"
	"strings"
)

var log []string

func note(s string) { log = append(log, s) }

// 정리를 defer 로 건다.
func withDefer() iter.Seq[int] {
	return func(yield func(int) bool) {
		defer note("정리")
		for i := range 3 {
			ok := yield(i)
			note(fmt.Sprintf("y%d=%v", i, ok))
			if !ok {
				return
			}
		}
	}
}

// 정리를 yield 가 false 일 때와 끝에서 직접 부른다.
func inline() iter.Seq[int] {
	return func(yield func(int) bool) {
		for i := range 3 {
			ok := yield(i)
			note(fmt.Sprintf("y%d=%v", i, ok))
			if !ok {
				note("정리")
				return
			}
		}
		note("정리")
	}
}

// v == 1 에서 how 대로 루프를 떠난다.
func consume(seq iter.Seq[int], how string) (res string) {
	defer func() {
		if r := recover(); r != nil {
			res = fmt.Sprint("recover ", r)
		}
	}()
outer:
	for range 1 {
		for v := range seq {
			if v != 1 {
				continue
			}
			if how == "break" {
				break
			}
			switch how {
			case "return":
				return "return"
			case "breakOuter":
				break outer
			case "panic":
				panic("body")
			}
		}
	}
	return "loop end"
}

func main() {
	ran, cells := 0, 0
	for _, how := range []string{"none", "break", "return", "breakOuter", "panic"} {
		for _, kind := range []string{"defer", "inline"} {
			log = nil
			seq := withDefer()
			if kind == "inline" {
				seq = inline()
			}
			res := consume(seq, how)
			cells++
			did := strings.Contains(strings.Join(log, " "), "정리")
			if did {
				ran++
			}
			fmt.Printf("[%-10s / %-6s] 결과=%-12s 로그=%v\n", how, kind, res, log)
		}
	}
	fmt.Printf("정리가 돈 칸 %d / %d\n", ran, cells)
}
```

<!-- go vet 뒤 빌드해 돌린다. 떠나는 법 5 × 정리 방식 2 를 한 줄씩 찍고, 마지막 줄에 정리가 돈 칸 수를 센다. -->

- 열 줄의 `결과` 와 `로그` 는? 마지막 줄의 수는?
- `panic` 두 줄에서 `yield(1)` 은 무엇을 돌려받았나?
- 정리를 어떻게 걸어야 다섯 가지 떠나는 법이 전부 덮이나?

### 2. 반복자가 계약을 어기면 (예측)

```go
// t39misuse.go
package main

import (
	"fmt"
	"os"
)

// yield 의 반환값을 보지 않는 반복자
func ignoring(yield func(int) bool) {
	for i := range 3 {
		yield(i)
	}
}

// 몸통의 패닉을 recover 로 삼키는 반복자
func swallowing(yield func(int) bool) {
	defer func() { recover() }()
	yield(0)
}

func main() {
	switch os.Args[1] {
	case "ignore":
		for v := range ignoring {
			fmt.Println("body", v)
			break
		}
	case "swallow":
		for v := range swallowing {
			fmt.Println("body", v)
			panic("body")
		}
	}
	fmt.Println("after loop")
}
```

<!-- go vet 뒤 빌드하고, ignore 와 swallow 를 각각 stdout·stderr 를 따로 받아 돌린다. stderr 는 첫 줄만 찍는다. -->

- `go vet` 은 무엇을 말하나?
- 두 모드의 종료 코드·stdout·stderr 첫 줄은? `after loop` 은 찍히나?

### 3. 누가 말한 규칙인가 (왜)

- 2번의 두 패닉 각각에 대해, 그 규칙을 **명세**가 말하나, **`iter` 문서**가 말하나, **런타임만** 막나?

### 4. `stop` 을 부르느냐 마느냐 (예측)

```go
// t39pull.go
package main

import (
	"fmt"
	"iter"
	"os"
	"runtime"
	"time"
)

var cleaned bool

func naturals() iter.Seq[int] {
	return func(yield func(int) bool) {
		defer func() { cleaned = true }()
		for i := 0; ; i++ {
			if !yield(i) {
				return
			}
		}
	}
}

func settle() {
	time.Sleep(20 * time.Millisecond)
	runtime.GC()
}

func main() {
	g0 := runtime.NumGoroutine()
	next, stop := iter.Pull(naturals())
	a, _ := next()
	b, _ := next()
	settle()
	fmt.Printf("next 두 번: %d %d · 늘어난 고루틴 %d · 정리 돌았나 %v\n", a, b, runtime.NumGoroutine()-g0, cleaned)
	if os.Args[1] == "stop" {
		stop()
	}
	settle()
	fmt.Printf("[%s] 늘어난 고루틴 %d · 정리 돌았나 %v\n", os.Args[1], runtime.NumGoroutine()-g0, cleaned)
	c, ok := next()
	fmt.Printf("[%s] 그 뒤 next: %d %v\n", os.Args[1], c, ok)
}
```

<!-- 빌드해 ./prog nostop 과 ./prog stop 을 차례로 돌린다. 늘어난 고루틴은 시작 시점과의 차이다. -->

- 두 판의 여섯 줄은? `nostop` 에서 20ms 기다리고 GC 를 돌린 뒤에도 남은 것은?
- `stop` 뒤의 `next` 는 무엇을 돌려주나?

### 5. push 와 pull (왜)

- `iter.Pull` 이 push 반복자를 pull 로 바꾸려면 **왜** 무언가를 하나 세워야 하나? 4번의 어느 줄이 그 흔적인가?

### 6. 1.22 와 1.23 (예측)

```go
// t39vrange.go
package main

import "fmt"

func upto(yield func(int) bool) {
	for i := range 2 {
		if !yield(i) {
			return
		}
	}
}

// 언어 기능 — 함수를 range 한다.
func main() {
	for v := range upto {
		fmt.Println(v)
	}
}
```

```go
// t39vmanual.go
package main

import (
	"fmt"
	"iter"
)

// 표준 라이브러리 타입 — iter.Seq 를 쓰되 range 없이 직접 부른다.
func main() {
	var s iter.Seq[int] = func(yield func(int) bool) { yield(7) }
	s(func(v int) bool { fmt.Println(v); return true })
}
```

```go
// t39vcollect.go
package main

import (
	"fmt"
	"slices"
)

// 표준 라이브러리 함수 — slices.Collect 에 반복자를 넘긴다.
func main() {
	fmt.Println(slices.Collect(func(yield func(int) bool) { yield(7) }))
}
```

```go
// t39vpull.go
package main

import (
	"fmt"
	"iter"
)

// 표준 라이브러리 함수 — iter.Pull 로 당긴다.
func main() {
	next, stop := iter.Pull(func(yield func(int) bool) { yield(7) })
	defer stop()
	fmt.Println(next())
}
```

<!-- 네 디렉토리를 go.mod 의 go 줄만 1.22 · 1.23 으로 바꿔 go build 와 go vet 을 돌린다. 마지막 줄에 빌드가 막힌 칸과 vet 이 말한 칸을 센다. -->

- 여덟 칸의 `build exit`·`vet exit` 는? 막힌 칸마다 누가 무엇을 말하나?
- 「1.23 경계」를 지키는 것은 누구와 누구인가?

### 7. `vet` 이 말하는 판 (연결)

- [34번 주제](../34-context-cancellation-deadlines-and-values/) (6)절에서 `stdversion` 이 침묵한 판은? 6번에서 말한 이유는?

### 8. JS 의 `return()` 과 나란히 (연결)

- [JS 19번](../../../js/syntax/19-iterable-protocol-and-for-of/)에서 `for...of` 의 몸통이 `throw` 하면 `return()` 이 불렸나? 같은 자리에서 Go 의 `yield` 는 무엇을 하나? 두 언어에서 **공통으로 도는 정리**는 무엇인가?

### 9. 14번과의 경계 (연결)

- [14번 주제](../14-for-four-forms-range-over-int-and-func/) (5)절이 이미 보인 것은 무엇이고, 이 편 1번은 그 위에 무엇을 더했나?

### 10. 반복자 대신 슬라이스 (경계)

- 반복자를 공개 API 로 내면 **만드는 쪽**이 떠안는 계약 두 가지는? 그 계약이 필요 없는 경우는 언제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

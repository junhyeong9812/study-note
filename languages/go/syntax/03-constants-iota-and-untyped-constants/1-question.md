# go/syntax/03 — 상수·`iota`·타입 없는 상수 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> ★ **이 주제의 예측은 「값」과 「타입」 둘 다다.** 값만 맞히면 절반이다.
> ★ **그리고 「컴파일 타임인가 런타임인가」를 매번 같이 답하라.** 이 주제와 04번을 가르는 축이 그것이다.
> 소스는 전부 `go build -trimpath -o prog . && ./prog` 로 던졌다. 모듈 이름은 `ex` 다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★ 같은 `K` 가 여덟 자리에서 무엇이 되나 (예측)

```go
// t03a.go
package main

import "fmt"

const K = 3       // 타입 없는 정수 상수
const T int32 = 3 // 타입 있는 상수

func takesFloat(f float64) string { return fmt.Sprintf("%T %v", f, f) }
func takesByte(b byte) string     { return fmt.Sprintf("%T %v", b, b) }

func main() {
	var a = K
	var b float64 = K
	var c byte = K
	var d complex128 = K
	fmt.Printf("var a = K        -> %-10T %v\n", a, a)
	fmt.Printf("var b float64= K -> %-10T %v\n", b, b)
	fmt.Printf("var c byte   = K -> %-10T %v\n", c, c)
	fmt.Printf("var d complex128 -> %-10T %v\n", d, d)
	fmt.Println("takesFloat(K) ->", takesFloat(K))
	fmt.Println("takesByte(K)  ->", takesByte(K))
	fmt.Printf("K 자신을 %%T 로 찍으면 -> %T (기본 타입으로 떨어진다)\n", K)

	var i32 int32 = T
	fmt.Printf("var i32 int32 = T -> %T %v\n", i32, i32)
	fmt.Println("K * 2.5 =", K*2.5, "— 타입 없는 상수라 실수 연산이 된다")
}
```

- 아홉 줄의 출력은 각각 무엇인가 — **값과 타입 둘 다** 적어라.
- `%T` 로 `K` 자신을 찍으면 왜 그 타입인가?
- 마지막 줄의 `K * 2.5` 는 무엇이고, 그것이 가능한 이유는?
- 이 중에 **변환(`float64(K)` 같은 것)을 적은 자리**가 하나라도 있는가?

### 2. 이 상수 블록은 컴파일되나 (예측)

```go
// t03c.go
package main

import (
	"fmt"
	"math"
)

const (
	big     = 1 << 200          // int64 최대의 약 1.6e42 배
	huge    = big * big         // 1 << 400
	back    = huge >> 399       // 다시 2 로
	overMax = math.MaxInt64 + 1 // int64 최대를 넘는 상수
	backMax = overMax - 1       // 다시 int64 최대로
	third   = 1.0 / 3.0         // 정확한 유리수로 들고 있다
)

func main() {
	fmt.Println("back        =", back)
	fmt.Println("backMax     =", backMax, "== math.MaxInt64 :", backMax == math.MaxInt64)
	fmt.Printf("float64(third) = %.20f\n", float64(third))
	fmt.Printf("float32(third) = %.20f\n", float32(third))
	fmt.Println("big/huge/overMax 는 선언은 됐지만 변수에 담지 않았다")
}
```

- 컴파일되는가 — 된다면 다섯 줄의 출력은 각각 무엇인가?
- `back` 이 그 값인 것은 무엇을 증명하는가?
- `float64(third)` 와 `float32(third)` 의 20자리가 왜 다른가?
- `big` 을 `fmt.Println(big)` 으로 찍으려 하면 어떻게 되는가?

### 3. 이 세 프로그램의 에러 줄 수는 (예측)

```go
// t03f.go
package main

import "fmt"

const (
	small int8    = 300
	neg   uint8   = -1
	fl    float32 = 1e40
)

func main() {
	var x uint8 = 256
	fmt.Println(small, neg, fl, x)
}
```

```go
// t03g.go
package main

import "fmt"

const zero = 0

func main() {
	fmt.Println(7 / zero)
}
```

```go
// t03e.go
package main

import "fmt"

const c = 10

func main() {
	p := &c
	const s = []int{1, 2}
	const t = fmt.Sprint(1)
	fmt.Println(p, s, t)
}
```

- 각각 **에러가 몇 줄**이고 메시지는 무엇인가?
- 첫 프로그램의 마지막 줄(`var x uint8 = 256`)은 상수 선언이 아닌데 왜 같은 층에서 걸리는가?
- 둘째 프로그램의 `7 / zero` 가 **런타임 패닉이 아닌** 이유는?
- 셋째 프로그램의 세 줄은 각각 **왜** 상수가 될 수 없는가?

### 4. `iota` 블록의 값을 전부 적어라 (예측)

```go
// t03h.go
package main

import "fmt"

type Weekday int

const (
	Sunday Weekday = iota
	Monday
	Tuesday
	_ // 자리를 버린다
	Thursday
)

const (
	_  = iota             // 0 을 버린다
	KB = 1 << (10 * iota) // iota == 1
	MB                    // 식이 비어 있으면 윗줄 식을 그대로 반복한다
	GB
	TB
)

const (
	FlagRead  = 1 << iota // 1
	FlagWrite             // 2
	FlagExec              // 4
)

const (
	a, b = iota, iota * 10 // iota == 0
	c, d                   // iota == 1
	e, f                   // iota == 2
)

const g = iota // 선언이 다르면 iota 는 다시 0

func main() {
	fmt.Println("Sunday..Thursday :", Sunday, Monday, Tuesday, Thursday)
	fmt.Printf("Sunday 의 타입    : %T\n", Sunday)
	fmt.Println("KB MB GB TB      :", KB, MB, GB, TB)
	fmt.Println("Flag             :", FlagRead, FlagWrite, FlagExec)
	fmt.Println("a b c d e f      :", a, b, c, d, e, f)
	fmt.Println("g                :", g)
}
```

- `Sunday`·`Monday`·`Tuesday`·`Thursday` 는 각각 무엇인가?
- `Sunday` 의 `%T` 는 무엇인가?
- `KB`·`MB`·`GB`·`TB` 는 각각 무엇인가?
- `a`·`b`·`c`·`d`·`e`·`f` 는 각각 무엇인가?
- `g` 는 무엇인가 — 왜 그런가?

### 5. 일곱 상수의 값과 타입 (예측)

```go
// t03j.go
package main

import "fmt"

const (
	a             = 2 + 3.0 // 타입 없는 실수 상수
	b             = 15 / 4  // 타입 없는 정수 상수
	c             = 15 / 4.0
	theta float64 = 3 / 2  // float64 인데 3/2 는 정수 나눗셈
	pi    float64 = 3 / 2. // 3/2. 는 실수 나눗셈
	k             = 'w' + 1
	m             = string(k)
)

func main() {
	fmt.Printf("a = %-6v %T\n", a, a)
	fmt.Printf("b = %-6v %T\n", b, b)
	fmt.Printf("c = %-6v %T\n", c, c)
	fmt.Printf("theta = %-6v %T\n", theta, theta)
	fmt.Printf("pi    = %-6v %T\n", pi, pi)
	fmt.Printf("k = %-6v %T\n", k, k)
	fmt.Printf("m = %-6q %T\n", m, m)
}
```

- 일곱 줄의 값과 타입은 각각 무엇인가?
- `theta` 와 `pi` 가 다른 이유를 **한 글자**로 짚어라.
- `k` 의 타입이 그것인 이유는?
- `b = 15 / 4` 가 상수인데도 그 값인 이유는?

### 6. 이 블록은 어디까지 컴파일되나 (예측)

```go
// t03k.go
package main

import "fmt"

const (
	ok511  = 1 << 511
	back   = ok511 >> 510
	bad512 = 1 << 512
)

func main() { fmt.Println(back) }
```

- 컴파일되는가 — 안 된다면 **어느 줄**에서 무슨 메시지인가?
- `ok511` 과 `bad512` 를 가르는 경계는 무엇인가?
- 그 경계는 **명세가 정한 것**인가 **이 컴파일러가 정한 것**인가?
- 명세가 요구하는 최소치는 얼마인가?

### 7. 상수는 왜 초기화 순서에 안 들어가나 (왜)

- 01번 주제의 「변수 → `init` → `main`」 순서에 상수가 없는 이유는 무엇인가?
- 그것을 **실행 출력이 아닌 방법**으로 확인하려면 무슨 도구를 쓰는가?
- 그 도구의 출력에서 **무엇을 근거로 읽고 무엇을 안 읽어야** 하는가?
- 상수의 주소를 잡을 수 없는 것이 이 사실과 어떻게 이어지는가?

### 8. 타입을 적을 것인가 말 것인가 (경계)

- `const K = 3` 과 `const T int32 = 3` 중 **쓸 수 있는 자리가 넓은** 쪽은?
- 좁은 쪽을 `float64` 를 받는 함수에 넘기면 어떤 메시지가 나오는가?
- 그런데도 타입을 적는 것이 맞는 경우는 언제인가?
- 「타입 없는 상수」와 「타입 없는 값」은 같은 말인가?

### 9. 상수 오버플로와 변수 오버플로 (경계)

- `const x int8 = 300` 과 `v := 300; int8(v)` 는 각각 언제 무엇이 일어나는가?
- 「상수를 0으로 나누기」와 「변수를 0으로 나누기」는 각각 언제 무엇이 일어나는가?
- 이 두 쌍이 말하는 **하나의 원칙**은 무엇인가?
- 명세가 「조용히 자르지 않는다」고 약속한 자리는 어디인가?

### 10. 다른 주제와 잇기 (연결)

- `i := 0` 의 `i` 가 `int` 인 것은 이 주제의 어느 규칙인가 — 변수 쪽 정본은 몇 번 주제인가?
- `var f float64 = 1` 은 되고 `var f float64 = n`(`n` 이 `int`)은 안 되는 이유의 정본은 몇 번 주제인가?
- `'w' + 1` 의 타입이 `int32` 인 배경의 정본은 몇 번 주제인가?
- `go tool compile -S` 를 읽는 법의 정본은 몇 번 주제인가?
- `iota` 로 만든 값을 DB 에 저장하면 안 되는 이유는 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

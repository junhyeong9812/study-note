# go/syntax/04 — 수치 타입과 명시 변환·오버플로·정수 나눗셈 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> ★ **답마다 「그 값을 누가 보장하나」를 같이 적어라** — 명세인가, gc 인가, 이 판의 관찰인가.
> 이 주제는 명세가 값까지 정해 둔 칸이 대부분이고, **구현에 맡겨진 칸은 딱 둘**이다. 그 둘을 찾는 것이 문항의 절반이다.
> ★ 다른 언어를 알고 있다면 **그 직관이 여기서 뒤집히는지** 먼저 의심하라(C 의 승격 · Rust 의 디버그 패닉).
> 소스는 전부 `go build -trimpath -o prog . && ./prog` 로 던졌다. 모듈 이름은 `ex` 다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★ 에러가 몇 줄 나오나 (예측)

```go
// t04a.go
package main

import "fmt"

func main() {
	var i int = 1
	var i64 int64 = 2
	var i32 int32 = 3
	var f float64 = 4

	fmt.Println(i + i64)
	fmt.Println(i32 + i64)
	fmt.Println(i + 1)
	fmt.Println(f * i)
	var r rune = 'A'
	var b byte = 1
	fmt.Println(r + b)
}
```

- 컴파일 에러는 **몇 줄**이고 각각 무슨 메시지인가?
- 다섯 개의 `fmt.Println` 중 **통과하는 것**이 있는가 — 있다면 왜인가?
- `r + b`(`rune` + `byte`)가 걸리는 이유는?
- 전부 고치려면 각 줄을 어떻게 쓰는가?

### 2. ★ 여섯 줄의 값과 타입 (예측)

```go
// t04b.go
package main

import (
	"fmt"
	"math"
)

func main() {
	var c uint8 = 200
	fmt.Printf("uint8 200 * 200      = %-6v (%T)  — C 라면 int 로 승격해 40000\n", c*c, c*c)

	var s int8 = 100
	fmt.Printf("int8  100 + 100      = %-6v (%T)\n", s+s, s+s)

	var u8 uint8 = 0
	fmt.Printf("uint8 0 - 1          = %-6v (%T)\n", u8-1, u8-1)

	var i8 int8 = math.MinInt8
	fmt.Printf("int8  MinInt8 - 1    = %-6v (%T)\n", i8-1, i8-1)

	var i64 int64 = math.MaxInt64
	fmt.Printf("int64 MaxInt64 + 1   = %-21v (%T)\n", i64+1, i64+1)

	var big int = math.MaxInt
	fmt.Printf("int   MaxInt + 1     = %-21v (%T)\n", big+1, big+1)

}
```

- 여섯 줄의 값과 `%T` 는 각각 무엇인가?
- 첫 줄(`uint8 200 * 200`)을 **C 로 같은 코드를 쓰면** 무엇이 나오는가 — 왜 다른가?
- 이 프로그램을 **최적화를 끄고**(`-gcflags='all=-N -l'`) 빌드하면 출력이 달라지는가?
- `-race` 를 붙이면?

### 3. 일곱 줄의 변환 결과 (예측)

```go
// t04g.go
package main

import "fmt"

func id(i int) int { return i }

func main() {
	v := 300
	var v16 uint16 = 0x10F0
	var n int = -1
	fmt.Println("uint8(v)                     =", uint8(v))
	fmt.Println("uint8(id(300))               =", uint8(id(300)))
	fmt.Println("int8(v)                      =", int8(v))
	fmt.Printf("uint32(int8(v16))            = 0x%X\n", uint32(int8(v16)))
	fmt.Println("uint8(n)                     =", uint8(n))
	fmt.Println("uint64(n)                    =", uint64(n))
	fmt.Println("int64(uint64(n))             =", int64(uint64(n)))
}
```

- 일곱 줄은 각각 무엇으로 찍히는가?
- 컴파일 경고는 몇 줄인가?
- `uint32(int8(v16))` 이 그 값인 이유를 두 단계로 설명하라.
- 같은 식을 **상수로** 쓰면(`uint8(300)`) 어떻게 되는가?

### 4. 여덟 줄 중 근거로 쓸 수 있는 것은 (예측)

```go
// t04f.go
package main

import (
	"fmt"
	"math"
)

func id(f float64) float64 { return f } // 상수 접기를 막으려고 함수로 뺀다

func main() {
	fmt.Println("int32(id(3.9))        =", int32(id(3.9)))
	fmt.Println("int32(id(-3.9))       =", int32(id(-3.9)))
	fmt.Println("int32(id(1e30))       =", int32(id(1e30)), "  ← 구현 의존")
	fmt.Println("int32(id(-1e30))      =", int32(id(-1e30)), "  ← 구현 의존")
	fmt.Println("int32(id(math.NaN())) =", int32(id(math.NaN())), "  ← 구현 의존")
	fmt.Println("int64(id(1e30))       =", int64(id(1e30)), "  ← 구현 의존")
	fmt.Println("uint8(id(-1.5))       =", uint8(id(-1.5)), "  ← 구현 의존")
	fmt.Println("uint8(id(300.7))      =", uint8(id(300.7)), "  ← 구현 의존")
}
```

- 여덟 줄의 값은 각각 무엇인가?
- 그중 **다른 컴파일러·다른 아키텍처에서 달라질 수 있는** 줄은 어디까지인가?
- `id()` 라는 함수를 굳이 거친 이유는?
- `int32(id(3.9))` 가 3인 것은 내림인가 0쪽 버림인가 — 어떻게 구별해 보이겠는가?

### 5. 표를 채워라 (예측)

```go
// t04c.go
package main

import "fmt"

func div(a, b int) (int, int) { return a / b, a % b }

func main() {
	fmt.Printf("%4s %4s | %6s %6s\n", "x", "y", "x / y", "x % y")
	fmt.Println("-----------+--------------")
	for _, p := range [][2]int{{5, 3}, {-5, 3}, {5, -3}, {-5, -3}, {11, 4}, {-11, 4}} {
		q, r := div(p[0], p[1])
		fmt.Printf("%4d %4d | %6d %6d\n", p[0], p[1], q, r)
	}
	fmt.Println()
	fmt.Println("-11 >> 2 =", -11>>2, "  (나눗셈이 아니라 음의 무한대 쪽 버림)")
	fmt.Println("-11 / 4  =", -11/4, "  (0 쪽 버림)")
}
```

- 여섯 행의 `x / y` 와 `x % y` 는 각각 무엇인가?
- 나머지의 **부호를 정하는 것**은 무엇인가?
- 마지막 두 줄에서 `-11 / 4` 와 `-11 >> 2` 가 다른 이유는?
- `b` 가 0이면 어떻게 되는가 — `b` 가 **상수 0**이면?

### 6. 이 프로그램은 어디까지 가는가 (예측)

```go
// t04k.go
package main

import (
	"fmt"
	"os"
)

func sh(x int32, n int) int32 { return x << n }

func main() {
	fmt.Println("int32(1) << 31 =", sh(1, 31))
	fmt.Println("int32(1) << 32 =", sh(1, 32), " (C 라면 미정의 동작)")
	fmt.Println("int32(1) << 99 =", sh(1, 99))
	fmt.Println("int32(-8) >> 1 =", -8>>1, " (산술 시프트)")
	var u uint8 = 0xF8
	fmt.Println("uint8(0xF8) >> 1 =", u>>1, " (논리 시프트)")
	fmt.Fprintln(os.Stderr, "----- 여기까지 stdout · 아래부터 음수 시프트 -----")
	neg := -1
	fmt.Println(sh(1, neg))
}
```

- 다섯 줄이 찍히는가 — 각각 무엇인가?
- `int32(1) << 32` 가 C 와 다른 점은 무엇인가?
- 마지막 줄에서 무슨 일이 일어나는가 — **메시지 전문**과 **종료 코드**는?
- `sh(1, 99)` 는 왜 에러가 아닌가?

### 7. 왜 `int` 와 `int64` 를 못 섞게 했나 (왜)

- 둘은 이 머신에서 `unsafe.Sizeof` 가 같은가?
- `math.MaxInt` 와 `math.MaxInt64` 는 같은가?
- 그런데도 못 섞는 근거가 되는 명세의 낱말은 무엇인가?
- `rune` 과 `int32` 는 왜 섞이는가 — `%T` 가 그 차이를 어떻게 보여 주는가?

### 8. Go 가 구현에 맡긴 칸은 어디인가 (경계)

아래 다섯 가지를 **「명세 보장」 / 「구현에 달림」** 으로 갈라라.

- ① `uint8` 에서 `0 - 1` 이 255다
- ② `int64` MaxInt64 + 1 이 MinInt64 다
- ③ `unsafe.Sizeof(int)` 가 8이다
- ④ `int32(1e30)` 이 −2147483648 이다
- ⑤ `MinInt64 / -1` 이 MinInt64 다

### 9. 컴파일러가 통과시키고 `go vet` 이 잡는 것 (경계)

```go
// t04j.go
package main

import "fmt"

func main() {
	n := 65
	s := string(rune(n))
	t := string(n)
	fmt.Printf("string(rune(65)) = %q\n", s)
	fmt.Printf("string(65)       = %q\n", t)
}
```

- `go build` 는 통과하는가? `go vet` 은?
- `go vet` 의 메시지 전문은 무엇인가?
- `string(65)` 은 무엇이 되는가 — 무엇으로 고쳐야 하는가?
- `go test` 를 돌리면 이 문제가 언제 드러나는가?

### 10. 다른 언어와 나란히 놓기 (연결)

- C 에서 `unsigned char c = 200; c * c` 는 무엇이고 Go 와 왜 다른가?
- Rust 에서 `250u8 + 10` 은 디버그와 릴리스가 어떻게 갈리며, Go 는 어떤가?
- Rust 에서 `i32::MIN / -1` 은 무엇이고 Go 는 무엇인가?
- C 의 「미정의 동작」에 해당하는 것이 Go 에 있는가?
- 「컴파일러가 오버플로가 없다고 가정해 최적화할 수 있는가」에 두 언어는 각각 뭐라고 답하는가?

### 11. 다른 주제와 잇기 (연결)

- `i + 1` 이 통과하는 이유의 정본은 몇 번 주제인가?
- `string(n)` 대신 무엇을 쓰며, 그 정본은 몇 번 주제인가?
- `rune` 이 왜 `int32` 인지의 정본은 몇 번 주제인가?
- `unsafe.Sizeof` 를 제대로 다루는 주제는 몇 번인가?
- 2의 보수 표현 자체를 다루는 갈래는 어디인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

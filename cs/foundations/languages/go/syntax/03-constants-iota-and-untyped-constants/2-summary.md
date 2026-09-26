# go/syntax/03 — 상수·`iota`·타입 없는 상수 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Go 명세](https://go.dev/ref/spec) 의 Constants · Constant declarations · Iota ·
> Constant expressions · Conversions 절.\
> 웹이 아니라 **이 툴체인이 들고 있는 `$(go env GOROOT)/doc/go_spec.html` 을 열어** 인용했다.
> 그 파일의 머리는 「**Language version go1.27 (May 26, 2026)**」이다.
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 손으로 옮겨 적은 블록은 없다.
> **버전** — 이 절의 규칙은 1.0부터 같다. `min`/`max` 가 상수식에 쓰이는 것은 **1.21**부터다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 명세로, 출력은 실행으로 접지했다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것. 어느 컴파일러에서도 같다 | `go_spec.html` 원문 인용 |
| **구현(gc)** | 이 컴파일러가 그렇게 하는 것. 약속은 아니다 | `go build`·`go tool compile -S` 출력 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 실행 출력(재실행 대조까지) |

★ 이 주제에서 층이 갈리는 대표 자리는 「**임의 정밀도**」다.
명세는 「**최소 256비트**」만 요구하고, gc 는 **512비트**를 준다. 둘은 다른 약속이다.

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
===== 명령: go env GOOS GOARCH GOVERSION =====
linux
amd64
go1.27.1
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| 칸 | 흔들리나 | 확인한 방법 |
|---|---|---|
| 상수의 값·타입(`%T`) | **안 흔들림** | 컴파일 타임에 정해진다 |
| 컴파일 에러 문장 본문 · `파일:줄:칸` | 안 흔들림 | 재실행 대조 동일 |
| 종료 코드 (`0` / `1`) | 안 흔들림 | 재실행 대조 동일 |
| `float32`/`float64` 변환 결과의 20자리 | 안 흔들림 | IEEE 754 가 정한다 |
| **`1 << 512` 가 에러라는 것** | **gc 의 한계**다 | 명세는 256비트만 요구한다 |
| 어셈블리의 `size=` · 레지스터 이름 · 오프셋 | **판·아키텍처가 바뀌면 바뀐다** | linux/amd64 · go1.27.1 |
| 맵 순회 순서 | 이 주제는 맵을 아예 안 쓴다 | — |

## 한눈에 — 쉽게 말하면

**Go 의 타입 없는 상수는 「아직 단위를 안 적은 숫자」다. 적는 순간 단위가 정해진다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 종이에 적어 둔 그냥 숫자 `3` | **타입 없는 상수**(`const K = 3`) |
| 「3 **킬로그램**」이라고 적는 순간 | 대입·전달 지점에서 타입이 붙는다 |
| 같은 `3` 을 kg 으로도 cm 로도 쓸 수 있다 | `var f float64 = K` 도 `var c byte = K` 도 된다 |
| 처음부터 「3 kg」이라고 못 박은 쪽지 | **타입 있는 상수**(`const T int32 = 3`) |
| 그 쪽지는 cm 자리에 못 쓴다 | `int32` 상수는 `float64` 자리에 **컴파일 에러** |
| 머릿속 계산은 자릿수 제한이 없다 | 상수식은 **임의 정밀도**로 계산된다 |
| 계산이 끝나고 **장부에 옮겨 적을 때** 칸을 넘으면 거부 | 대입 지점에서 넘치면 **컴파일 에러** |
| 장부에 옮겨 적지 않은 중간 계산은 장부에 안 남는다 | 상수는 **런타임에 존재하지 않는다** |

- 그래서 Go 에서는 `var f float64 = 1` 이 **되고**, `var f float64 = i`(`i` 가 `int`)는 **안 된다.**
  앞은 「아직 단위 없는 숫자」이고 뒤는 「이미 kg 이 붙은 값」이다.
- ★ 그리고 상수의 오버플로는 **런타임 사고가 아니라 컴파일 에러**다. 04번 주제의 변수 오버플로와 **층이 다르다.**

```text
        const K = 3        (타입 없음 — 아직 단위가 없다)
              |
      +-------+--------+--------------+
      |       |        |              |
  var a = K   |   var c byte = K   takesFloat(K)
   -> int     |     -> uint8          -> float64
              |
        var b float64 = K
           -> float64

  같은 K 하나가 대입 자리마다 다른 타입이 된다.
```

**언어도 똑같은 구조다.** 위 네 갈래는 아래 (2)절 출력 그대로다.

> **타입 없는 상수(untyped constant)** — 타입이 아직 안 정해진 상수. 대입·전달 지점에서 타입이 붙는다.\
> 예: `const K = 3` 은 `byte` 자리에도 `float64` 자리에도 그대로 들어간다.

> **기본 타입(default type)** — 문맥이 타입을 안 정해 줄 때 타입 없는 상수가 떨어지는 타입.\
> 예: `i := 0` 의 `i` 는 `int`, `f := 1.5` 는 `float64`, `r := 'a'` 는 `rune`(= `int32`).

> **`iota`** — 상수 선언 블록 안에서 **몇 번째 줄인가**를 나타내는 미리 선언된 정수 상수. 0부터 센다.\
> 예: `const ( A = iota; B; C )` 면 `A`·`B`·`C` 가 0·1·2 다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 타입 없는 상수는 **어느 지점에서** 타입이 되나 — 그리고 안 정해 주면 **무엇으로** 떨어지나.
2. 「상수는 임의 정밀도」는 **어디까지 참인가** — 명세의 약속과 gc 의 한계는 각각 얼마인가.
3. 상수가 **런타임에 존재하지 않는다**는 것을 어떻게 눈으로 확인하나.

## 동작 방식

### (1) 상수의 자리 — 컴파일 타임에 끝난다

**언제 쓰나** — 값이 프로그램 수명 내내 안 바뀔 때.

`const` 는 변수 선언과 형태가 닮았지만 **층이 다르다.**

선언 형태는 아래 「문법 — 형태와 규칙」 절에 한 파일로 모아 두었다. 여기서는 **자리**만 본다.

- 상수는 **초기화 순서에 들어가지 않는다.** 01번 주제의 「변수 → `init` → `main`」 어디에도 없다.
- 그래서 **주소를 잡을 수 없다**(`&K` 는 에러). 메모리에 자리가 없기 때문이다.
- 그리고 **함수 호출 결과는 상수가 될 수 없다** — 컴파일 타임에 값을 모른다.
- 상수가 될 수 있는 것은 명세가 열거한다 — 리터럴·상수 식별자·상수식·상수를 낳는 변환·
  `min`/`max`·`unsafe.Sizeof`·`len`/`cap`(일부)·`real`/`imag`/`complex`.

비용 — 0이다. (7)절에서 어셈블리로 확인한다.

### (2) ★ 타입 없는 상수 — 대입 지점에서 타입이 된다

**언제 쓰나** — 숫자 상수를 쓰는 거의 모든 자리.

같은 `const K = 3` 하나를 네 군데에 넣는다.

```text
===== 소스: t03a.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
var a = K        -> int        3
var b float64= K -> float64    3
var c byte   = K -> uint8      3
var d complex128 -> complex128 (3+0i)
takesFloat(K) -> float64 3
takesByte(K)  -> uint8 3
K 자신을 %T 로 찍으면 -> int (기본 타입으로 떨어진다)
var i32 int32 = T -> int32 3
K * 2.5 = 7.5 — 타입 없는 상수라 실수 연산이 된다
(exit 0)
```

그림 해설 (한 단계씩):

- `var a = K` — 문맥이 타입을 안 주므로 **기본 타입 `int`** 로 떨어진다.
- `var b float64 = K` — **`float64`** 가 된다. 변환을 한 글자도 안 적었다.
- `var c byte = K` — **`uint8`** 이 된다. 같은 `K` 다.
- `takesFloat(K)`·`takesByte(K)` — **함수 인자 자리도 대입 지점**이다.
- `%T` 로 `K` 자신을 찍으면 `int` 다 — `fmt` 의 `any` 인자가 문맥을 안 주므로 **기본 타입으로 떨어진다.**
- 마지막 줄 — `K * 2.5` 가 **7.5**다. 타입 없는 정수 상수와 실수 상수를 섞으면
  **결과가 실수 상수**가 된다(명세: "the result is of the operand's kind that appears later in this list:
  integer, rune, floating-point, complex").

명세:

> A constant may be given a type explicitly by a constant declaration
> or conversion, or **implicitly when used in a variable declaration or an
> assignment statement or as an operand in an expression.**
> It is an error if the constant value cannot be represented as a value of the respective type.

비용 — 없음. 전부 컴파일 타임이다.

### (3) 타입이 붙는 순간 벽이 생긴다

**언제 쓰나** — `const T int32 = 3` 처럼 상수에 타입을 적을지 정할 때.

```text
===== 소스: t03b.go =====
package main

import "fmt"

const T int32 = 3

func takesFloat(f float64) float64 { return f }

func main() {
	fmt.Println(takesFloat(T))
}
===== 명령: go build -trimpath -o prog . =====
# ex
./t03b.go:10:25: cannot use T (constant 3 of type int32) as float64 value in argument to takesFloat
(exit 1)
```

그림 해설 (한 단계씩):

- `const T int32 = 3` 을 `float64` 를 받는 함수에 넘기면 **컴파일 에러**다.
- 메시지가 「`constant 3 of type int32`」라고 **타입을 이름으로 부른다.** 이미 `int32` 라는 뜻이다.
- (2)절의 `K` 는 같은 자리에 아무 문제 없이 들어갔다. **한 낱말(`int32`) 차이**다.

★ 그래서 **숫자 상수에는 웬만하면 타입을 적지 않는다.** 적는 순간 쓸 수 있는 자리가 줄어든다.

비용 — 없음. 대신 **유연성**을 잃는다.

### (4) ★ 임의 정밀도 — 그리고 그 정밀도의 끝

**언제 쓰나** — 비트 마스크·큰 단위 상수처럼 중간 계산이 커질 때.

`int64` 최대의 수십억 배를 지나가는 상수식을 만든다.

```text
===== 소스: t03c.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
back        = 2
backMax     = 9223372036854775807 == math.MaxInt64 : true
float64(third) = 0.33333333333333331483
float32(third) = 0.33333334326744079590
big/huge/overMax 는 선언은 됐지만 변수에 담지 않았다
(exit 0)
```

그림 해설 (한 단계씩):

- `big = 1 << 200` 과 `huge = big * big`(= `1 << 400`)이 **컴파일된다.**
  `int64` 는 물론 `uint64` 로도 담을 수 없는 수다.
- `back = huge >> 399` 가 **2**로 정확히 돌아온다 — 중간값이 **잘리지 않았다**는 증거다.
- `overMax = math.MaxInt64 + 1` 도 상수로는 문제없고, `backMax` 가 **정확히 `math.MaxInt64`** 로 돌아온다.
- `third = 1.0/3.0` 은 **유리수로 정확히** 들고 있다가, `float64`·`float32` 로 **변환할 때만** 반올림된다.
  그래서 20자리가 서로 다르다.
- 마지막 줄이 중요하다 — `big`·`huge`·`overMax` 를 **변수에 담지 않았다.**

**변수에 담으면 그때 거부된다.**

```text
===== 소스: t03d.go =====
package main

import "fmt"

const big = 1 << 200

func main() {
	fmt.Println(big)
}
===== 명령: go build -trimpath -o prog . =====
# ex
./t03d.go:8:14: cannot use big (untyped int constant 1606938044258990275541962092341162602522202993782792835301376) as int value in argument to fmt.Println (overflows)
(exit 1)
```

- 에러가 **61자리 수를 그대로 찍는다.** 컴파일러가 그 값을 **정확히 들고 있었다**는 증거다.
- 「런타임에 잘린다」가 아니라 「**컴파일이 거부한다**」이다.

명세:

> Numeric constants represent exact values of arbitrary precision and do not overflow.

> Constant expressions are always evaluated exactly; intermediate values and the
> constants themselves may require precision significantly larger than supported
> by any predeclared type in the language.

**그런데 「임의」에는 끝이 있다.**

```text
===== 소스: t03k.go =====
package main

import "fmt"

const (
	ok511  = 1 << 511
	back   = ok511 >> 510
	bad512 = 1 << 512
)

func main() { fmt.Println(back) }
===== 명령: go build -trimpath -o prog . =====
# ex
./t03k.go:8:13: constant shift overflow
(exit 1)
```

- `1 << 511` 은 통과하고 **`1 << 512` 는 `constant shift overflow`** 다.
- 명세는 「임의 정밀도」라고 말하면서 **구현 제한**을 따로 둔다.

  > Implementation restriction: Although numeric constants have arbitrary
  > precision in the language, a compiler may implement them using an
  > internal representation with limited precision. That said, every
  > implementation must: **Represent integer constants with at least 256 bits.**
  > … **Give an error if unable to represent an integer constant precisely.**

- 읽는 법 — **명세가 약속한 것은 256비트**이고, **gc 가 주는 것은 512비트**다.
  그리고 부족하면 **조용히 자르지 않고 에러를 낸다**는 것까지가 약속이다.

비용 — 없음(컴파일 타임). 큰 상수식이 많으면 컴파일이 아주 조금 느려질 뿐이다.

### (5) 타입 없는 상수의 **종류**와 기본 타입

**언제 쓰나** — `15 / 4` 가 왜 3인지 설명해야 할 때.

```text
===== 소스: t03j.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
a = 5      float64
b = 3      int
c = 3.75   float64
theta = 1      float64
pi    = 1.5    float64
k = 120    int32
m = "x"    string
(exit 0)
```

그림 해설 (한 단계씩):

- `a = 2 + 3.0` → **`float64` 5**. 정수와 실수를 섞으면 실수 쪽으로 간다.
- **`b = 15 / 4` → `int` 3.** 둘 다 정수 상수라 **정수 나눗셈**이다. 상수라고 봐주지 않는다.
- `c = 15 / 4.0` → `float64` 3.75.
- ★ **`theta float64 = 3 / 2` 가 1이다.** 타입을 `float64` 로 적었는데도
  **`3 / 2` 는 정수끼리라 먼저 1이 되고**, 그 1이 `float64` 가 된다.
- `pi float64 = 3 / 2.` 는 1.5 — 점 하나가 결과를 바꾼다.
- `k = 'w' + 1` → **`int32` 120**. 룬 상수의 기본 타입은 `rune`(= `int32`)이다.
- `m = string(k)` → `"x"`. 상수 변환이라 결과도 상수다.

명세가 「종류(kind)」를 이렇게 정의한다.

> If the untyped operands of a binary operation (other than a shift) are of
> different kinds, the result is of the operand's kind that appears later in this
> list: integer, rune, floating-point, complex.

그리고 기본 타입은 이렇다.

> The default type of an untyped constant is `bool`, `rune`,
> `int`, `float64`, `complex128`, or `string`
> respectively, depending on whether it is a boolean, rune, integer, floating-point,
> complex, or string constant.

비용 — 없음.

### (6) `iota` — 「몇 번째 줄인가」일 뿐이다

**언제 쓰나** — 열거형·비트 플래그·단위 상수.

```text
===== 소스: t03h.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
Sunday..Thursday : 0 1 2 4
Sunday 의 타입    : main.Weekday
KB MB GB TB      : 1024 1048576 1073741824 1099511627776
Flag             : 1 2 4
a b c d e f      : 0 0 1 10 2 20
g                : 0
(exit 0)
```

그림 해설 (한 단계씩):

- `Sunday Weekday = iota` 다음 세 줄은 **식을 안 적었다.** 그러면 **윗줄의 식이 그대로 반복**된다.
  그래서 0·1·2 가 되고, `_` 가 3을 삼켜 `Thursday` 가 **4**다.
- 타입도 같이 반복된다 — `Sunday` 의 `%T` 가 **`main.Weekday`** 다.
- `KB` 블록 — 첫 줄 `_ = iota` 가 0을 버리고, `1 << (10*iota)` 가 1024·1048576·… 로 간다.
  **반복되는 것은 값이 아니라 식**이라 `iota` 가 줄마다 다시 계산된다.
- `FlagRead/Write/Exec` — 1·2·4. 같은 원리다.
- `a, b = iota, iota*10` — **한 줄 안의 여러 `iota` 는 같은 값**이다. 0·0 → 1·10 → 2·20.
- 마지막 `const g = iota` 는 **다른 선언**이므로 `iota` 가 **다시 0**이다.

명세:

> Within a constant declaration, the predeclared identifier
> `iota` represents successive untyped integer constants.
> Its value is **the index of the respective ConstSpec in that constant declaration**, starting at zero.

> By definition, multiple uses of `iota` in the same ConstSpec all have the same value.

★ **`iota` 는 「자동 증가 카운터」가 아니다.** 「몇 번째 ConstSpec 인가」다 —
`_` 로 버린 줄도, 식을 안 적은 줄도 **한 칸을 차지한다.**

비용 — 없음.

### (7) ★ 네 번째 창 — 어셈블리로 「상수는 런타임에 없다」를 본다

실행 출력·컴파일 진단·`go vet` 셋으로는 「상수가 **언제** 계산되는가」가 안 보인다.
값이 맞게 나오는 것은 런타임 계산이어도 똑같기 때문이다. 그래서 이 주제는 **컴파일러가 낸 코드**를 직접 본다.

```text
===== 소스: t03i.go =====
package sizes

const (
	_  = iota
	KB = 1 << (10 * iota)
	MB
)

// FromConst 는 상수만으로 값을 만든다.
func FromConst() int { return MB*2 + KB }

// FromVar 는 같은 모양의 계산을 변수로 한다.
func FromVar(mb, kb int) int { return mb*2 + kb }
===== 명령: go tool compile -S -trimpath "$PWD" -p sizes t03i.go 2>&1 | grep -vE 'FUNCDATA|PCDATA|^\s+0x[0-9a-f]{4} [0-9a-f]{2} ' | sed '/^go:cuinfo/,$d' =====
sizes.FromConst STEXT nosplit size=6 align=0x0 args=0x0 locals=0x0 funcid=0x0
	0x0000 00000 (t03i.go:10)	TEXT	sizes.FromConst(SB), NOSPLIT|NOFRAME|ABIInternal, $0-0
	0x0000 00000 (t03i.go:10)	MOVL	$2098176, AX
	0x0005 00005 (t03i.go:10)	RET
sizes.FromVar STEXT nosplit size=5 align=0x0 args=0x10 locals=0x0 funcid=0x0
	0x0000 00000 (t03i.go:13)	TEXT	sizes.FromVar(SB), NOSPLIT|NOFRAME|ABIInternal, $0-16
	0x0000 00000 (t03i.go:13)	LEAQ	(BX)(AX*2), AX
	0x0004 00004 (t03i.go:13)	RET
(exit 0)
===== 명령: rm -f t03i.o =====
(exit 0)
```

그림 해설 (한 단계씩):

- `FromConst` 는 `MB*2 + KB` 를 계산한다. 나온 코드는 **두 줄**이다 —
  `MOVL $2098176, AX` 와 `RET`. 곱셈도 덧셈도 **없다.**\
  2098176 = 1048576×2 + 1024. **컴파일러가 다 계산해 상수 하나로 접었다.**
- `FromVar` 는 같은 모양인데 인자가 변수다. `LEAQ (BX)(AX*2), AX` — **주소 계산 명령 하나**로
  `mb*2 + kb` 를 한다. 즉 **런타임에 계산이 있다.**
- 함수 크기도 갈린다 — `size=6` 대 `size=5` 로 비슷해 보이지만,
  **`FromConst` 쪽은 입력이 아예 없다**(`args=0x0`). 상수는 인자가 필요 없다.
- ★ 그래서 (1)절의 「상수는 초기화 순서에 없다」가 눈으로 확인된다 — **초기화할 것이 없다.**

**이 창이 답하는 것** — 「이 값이 컴파일 타임에 정해졌나, 런타임에 계산되나」.
`iota` 블록이 아무리 길어도 **런타임 비용이 0**이라는 것도 여기서 보인다.

★ 이 블록의 배너에 `grep`·`sed` 가 들어 있는 것은, 실린 것이 **그 명령의 전체 출력**임을 밝히기 위해서다.
(FUNCDATA·PCDATA·바이트 덤프·DWARF 꼬리는 상수와 무관해 걸러 냈다.)

비용 — 어셈블리는 **판과 아키텍처에 달렸다.** 레지스터 이름·오프셋·`size=` 는 근거로 읽지 않는다.
읽을 것은 「**곱셈 명령이 있나 없나**」뿐이다.

## 문법 — 형태와 규칙

### 형태

```go
// t03form.go
package main

import "fmt"

const K = 3          // ① 타입 없는 상수
const T int32 = 3    // ② 타입 있는 상수
const A, B = 1, "hi" // ③ 여러 개 — 타입이 달라도 된다

const ( // ④ 블록
	Sunday    = iota // 0
	Monday           // 1 — 식을 안 적으면 윗줄 식 반복
	_                // 2 를 버린다
	Wednesday        // 3
)

const (
	KB = 1 << (10 * (iota + 1)) // ⑤ iota 를 식 안에서 쓴다
	MB
)

func main() {
	fmt.Println(K, T, A, B, Sunday, Monday, Wednesday, KB, MB)
}
```

```text
===== 소스: t03form.go =====
package main

import "fmt"

const K = 3          // ① 타입 없는 상수
const T int32 = 3    // ② 타입 있는 상수
const A, B = 1, "hi" // ③ 여러 개 — 타입이 달라도 된다

const ( // ④ 블록
	Sunday    = iota // 0
	Monday           // 1 — 식을 안 적으면 윗줄 식 반복
	_                // 2 를 버린다
	Wednesday        // 3
)

const (
	KB = 1 << (10 * (iota + 1)) // ⑤ iota 를 식 안에서 쓴다
	MB
)

func main() {
	fmt.Println(K, T, A, B, Sunday, Monday, Wednesday, KB, MB)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
3 3 1 hi 0 1 3 1024 1048576
(exit 0)
```

규칙 불릿.

- 상수는 **함수 안에서도 선언할 수 있다.** `:=` 는 못 쓴다(상수 전용 짧은 꼴이 없다).
- **블록 안에서 식을 생략하면 윗줄의 식(과 타입)이 반복**된다. 값이 아니라 **식**이다.
- `iota` 는 **선언 블록 안에서만**, 그 블록의 **줄 번호**(0부터)다.
- 상수끼리의 나눗셈은 **피연산자가 둘 다 정수면 정수 나눗셈**이다.
- 안 쓴 상수는 **에러가 아니다**(변수와 다르다).

### 금지 사례 — 컴파일러가 거부하는 것

**① 상수가 될 수 없는 것**

```text
===== 소스: t03e.go =====
package main

import "fmt"

const c = 10

func main() {
	p := &c
	const s = []int{1, 2}
	const t = fmt.Sprint(1)
	fmt.Println(p, s, t)
}
===== 명령: go build -trimpath -o prog . =====
# ex
./t03e.go:8:8: invalid operation: cannot take address of c (untyped int constant 10)
./t03e.go:9:12: []int{…} (value of type []int) is not constant
./t03e.go:10:12: fmt.Sprint(1) (value of type string) is not constant
(exit 1)
```

- `&c` — **주소를 잡을 수 없다.** 메모리에 자리가 없다.
- `[]int{1, 2}` — 슬라이스는 상수가 될 수 없다(`is not constant`).
- `fmt.Sprint(1)` — **함수 호출 결과**는 상수가 아니다. 컴파일 타임에 모른다.

**② 타입에 안 담기는 상수**

```text
===== 소스: t03f.go =====
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
===== 명령: go build -trimpath -o prog . =====
# ex
./t03f.go:6:18: cannot use 300 (untyped int constant) as int8 value in constant declaration (overflows)
./t03f.go:7:18: cannot use -1 (untyped int constant) as uint8 value in constant declaration (overflows)
./t03f.go:8:18: cannot use 1e40 (untyped float constant 1e+40) as float32 value in constant declaration (overflows)
./t03f.go:12:16: cannot use 256 (untyped int constant) as uint8 value in variable declaration (overflows)
(exit 1)
```

- 넷 다 **컴파일 에러**다. `int8` 에 300, `uint8` 에 −1, `float32` 에 `1e40`,
  그리고 **변수 선언(`var x uint8 = 256`)도 같은 층**에서 걸린다.
- ★ 이것이 04번 주제와 갈리는 자리다 — **상수는 컴파일 타임, 변수는 런타임**이다.
  명세: "The values of typed constants must always be accurately representable by values of the constant type."

**③ 상수를 0으로 나누기**

```text
===== 소스: t03g.go =====
package main

import "fmt"

const zero = 0

func main() {
	fmt.Println(7 / zero)
}
===== 명령: go build -trimpath -o prog . =====
# ex
./t03g.go:8:18: invalid operation: division by zero
(exit 1)
```

- `invalid operation: division by zero` — **컴파일 에러**다.
- 04번 주제에서 보겠지만 **변수를 0으로 나누면 런타임 패닉**이다. 같은 `/` 가 층이 다르다.
- 명세: "The divisor of a constant division or remainder operation must not be zero."

## 어디서 틀리나

### 1. ★ `3 / 2` 를 `float64` 자리에 쓰고 1.5 를 기대한다

- (5)절 실측 — `const theta float64 = 3 / 2` 는 **1**이다.
- 타입을 적어도 **오른쪽 식이 먼저 계산**되고, 거기서는 둘 다 정수 상수다.
- 고치는 법 — 한쪽에 점을 찍는다(`3 / 2.`). **점 하나가 결과를 바꾼다.**

### 2. 숫자 상수에 타입을 적어 두고 재사용이 막힌다

- (3)절 실측 — `const T int32 = 3` 은 `float64` 자리에 **컴파일 에러**다.
- 특히 라이브러리 공개 상수에서 아프다. 쓰는 쪽이 변환을 적어야 한다.
- 고치는 법 — **타입을 적지 않는다.** 열거형처럼 **타입이 의미인** 경우에만 적는다(`Weekday`).

### 3. `iota` 를 「자동 증가」로 읽는다

- (6)절 실측 — `_` 로 버린 줄도 칸을 차지해 `Thursday` 가 **4**다.
- `a, b = iota, iota*10` 처럼 **한 줄 안의 `iota` 는 전부 같은 값**이다.
- 고치는 법 — 「몇 번째 줄인가」로 읽는다. 줄을 추가·삭제하면 **뒤의 값이 전부 밀린다** —
  그래서 **`iota` 값을 파일·DB 에 그대로 저장하면 안 된다.**

### 4. 「상수는 임의 정밀도니까 무한」이라고 읽는다

- (4)절 실측 — `1 << 512` 는 `constant shift overflow` 다.
- 명세가 약속한 것은 **최소 256비트**이고, 그 이상은 **구현에 달렸다.**
- 다만 부족할 때 **조용히 자르지 않고 에러를 낸다**는 것은 약속이다. 그래서 무음 실패가 아니다.

### 5. 상수 오버플로와 변수 오버플로를 같은 것으로 본다

- `const x int8 = 300` → **컴파일 에러**(금지 사례 ②).
- `var v = 300; int8(v)` → **런타임에 조용히 44**(04번 주제).
- **같은 수, 같은 타입, 완전히 다른 층**이다. 이 둘을 안 가르면 04번이 통째로 안 읽힌다.

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| 타입 없는 상수가 **대입 지점**에서 타입을 받는다 | **명세 보장** | "implicitly when used in a variable declaration or an assignment statement or as an operand in an expression" |
| 기본 타입이 `bool`/`rune`/`int`/`float64`/`complex128`/`string` | **명세 보장** | "The default type of an untyped constant is …" |
| 상수식이 **정확히** 계산된다 | **명세 보장** | "Constant expressions are always evaluated exactly" |
| **최소 256비트** 정수 상수 | **명세 보장(하한)** | "Represent integer constants with at least 256 bits." |
| **`1 << 511` 까지 되고 `1 << 512` 는 에러** | **구현(gc)** | (4)절 실측. 명세는 512를 약속하지 않는다 |
| 정밀도가 부족하면 **에러를 낸다**(조용히 안 자른다) | **명세 보장** | "Give an error if unable to represent an integer constant precisely." |
| 타입 있는 상수는 그 타입으로 **정확히 표현 가능**해야 한다 | **명세 보장** | "The values of typed constants must always be accurately representable …" |
| 상수 0으로 나누기가 **컴파일 에러** | **명세 보장** | "The divisor of a constant division or remainder operation must not be zero." |
| `iota` 가 **ConstSpec 의 인덱스** | **명세 보장** | "Its value is the index of the respective ConstSpec …" |
| 식 생략 시 **윗줄 식 반복** | **명세 보장** | "the implicit repetition of the last non-empty expression list" |
| 상수식이 **런타임 명령을 안 남기는** 것 | **구현(gc)** | (7)절 어셈블리. 명세는 코드 생성을 약속하지 않는다 |
| 어셈블리의 `MOVL $2098176, AX` | **이 판의 관찰** | linux/amd64 · go1.27.1 |
| 실수 상수식에 **반올림이 끼어들 수 있다** | **명세가 허용** | "A compiler may use rounding while computing untyped floating-point or complex constant expressions" |

★ 마지막 줄이 조용한 함정이다 — 명세는 실수 상수식의 **반올림을 허용**하고,
그 때문에 「무한 정밀도로 계산하면 정수인데 정수 문맥에서 거부되는(또는 그 반대)」 일이 **생길 수 있다**고
못 박아 둔다. 이 문서에서는 **그 사례를 만들지 못했다**(gc 는 유리수로 정확히 들고 있었다) —
「안 돌려 봄」이 아니라 **재현 조건을 못 만든 것**이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 숫자 상수 일반 | **타입 없이** `const K = 3` | 쓸 수 있는 자리가 가장 넓다 |
| 열거형 | `type X int` + `const ( A X = iota … )` | 타입이 **의미**이므로 적는 것이 맞다 |
| 비트 플래그 | `1 << iota` | 값이 겹치지 않는다 |
| 단위(KB·MB) | `_ = iota` 로 0을 버리고 `1 << (10*iota)` | 읽기 쉽고 런타임 비용 0 |
| 외부에 저장할 코드값 | **`iota` 를 쓰지 말고 값을 직접 적는다** | 줄을 추가하면 뒤가 전부 밀린다 |
| 실수 나눗셈이 필요하다 | 한쪽에 점을 찍는다(`3 / 2.`) | 둘 다 정수면 정수 나눗셈이다 |
| 값이 런타임에 정해진다 | `var` (상수가 아니다) | 함수 호출은 상수가 될 수 없다 |
| 슬라이스·맵 상수 | **불가능** — `var` 로 두거나 함수로 만든다 | 상수가 될 수 있는 타입이 아니다 |

판단 규칙 두 줄.

- **타입은 의미가 있을 때만 적는다.** 숫자 그 자체면 적지 않는 쪽이 언제나 낫다.
- **`iota` 는 프로그램 안에서만 쓴다.** 밖으로 나가는 값에는 쓰지 않는다.

## 핵심 문장

- 타입 없는 상수는 **대입·전달 지점에서** 타입이 된다 — 같은 `const K = 3` 이 `int`·`float64`·`uint8` 이 된다.
- 문맥이 타입을 안 주면 **기본 타입**으로 떨어진다(`int`·`float64`·`rune`·`complex128`·`string`·`bool`).
- **타입을 적는 순간 벽이 생긴다** — `const T int32 = 3` 은 `float64` 자리에 컴파일 에러다.
- 상수식은 **정확히** 계산된다. `1 << 400` 이 컴파일되고, 변수에 담을 때 **컴파일 에러**로 거부된다.
- 「임의 정밀도」의 약속은 **최소 256비트**이고 gc 가 주는 것은 **512비트**다. 둘은 다른 문장이다.
- `15 / 4` 는 상수여도 **정수 나눗셈**이고, `const theta float64 = 3 / 2` 는 **1**이다.
- `iota` 는 카운터가 아니라 **블록 안의 줄 번호**다. 버린 줄도 한 칸을 먹는다.
- 어셈블리로 보면 상수식은 **명령 한 줄의 즉값**으로 접혀 있다 — **런타임에 상수는 없다.**

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 03번)
- [02번 주제](../02-variable-declarations-and-zero-values/)(변수 선언·제로값) —
  `b := 42` 가 `int` 가 되는 것이 여기 (5)절의 **기본 타입** 규칙이다. 그쪽은 **변수 쪽 표면**을 본다
- [04번 주제](../04-numeric-types-conversions-and-integer-division/)(수치 타입·변환) —
  **상수 오버플로는 컴파일 에러, 변수 오버플로는 조용한 랩어라운드**. 그 대비의 반대쪽이 거기다
- [01번 주제](../01-packages-imports-main-and-init/)(패키지·`init`) —
  **상수는 초기화 순서에 들어가지 않는다.** 그쪽 순서표에 상수가 없는 이유가 여기 (7)절이다
- [`../../../../data-representation/`](../../../../data-representation/) —
  **그쪽은 2의 보수·IEEE 754 라는 표현 자체**까지, **여기는 Go 가 그 위에 얹은 상수 규칙**부터다
- [목록의 **10번 주제**](../10-strings-bytes-runes-and-utf8-iteration/)(문자열·`rune`) — `'w' + 1` 이 `int32` 인 것의 배경
- [목록의 **37번 주제**](../37-generics-type-parameters-and-constraint-interfaces/)(제네릭) — 타입 파라미터 자리에 상수를 쓰면
  **상수가 아니라 그 타입의 값으로 변환**된다(명세). 여기서는 다루지 않았다
- [목록의 **52번 주제**](../52-tools-gofmt-vet-build-tags-embed-and-escape-analysis/)(도구) — `go tool compile -S` 를 읽는 법의 정본.
  여기서는 (7)절의 한 물음에만 썼다

## 용어 풀이

- **상수(constant)** — 컴파일 타임에 값이 정해지는 이름. 주소를 잡을 수 없다.
- **타입 없는 상수(untyped constant)** — 타입이 아직 안 정해진 상수. 대입 지점에서 타입이 붙는다.
- **타입 있는 상수(typed constant)** — 선언에 타입을 적은 상수. 그 타입 밖으로 못 나간다.
- **기본 타입(default type)** — 문맥이 타입을 안 줄 때 떨어지는 타입.
- **종류(kind)** — 타입 없는 상수의 분류: boolean · integer · rune · floating-point · complex · string.
- **`iota`** — 상수 선언 블록 안의 ConstSpec 인덱스. 0부터.
- **ConstSpec** — 상수 선언 블록 안의 한 줄(한 명세). `iota` 가 세는 단위다.
- **식의 암묵 반복** — 블록에서 식을 생략하면 윗줄의 식과 타입이 반복되는 규칙.
- **상수식(constant expression)** — 상수만으로 이루어진 식. 컴파일 타임에 정확히 계산된다.
- **임의 정밀도(arbitrary precision)** — 미리 정해진 비트 폭에 매이지 않는 계산. 실제로는 구현 한계가 있다.
- **구현 제한(implementation restriction)** — 명세가 「컴파일러가 이렇게 해도 된다」고 허용한 조항.
- **상수 접기(constant folding)** — 컴파일러가 상수식을 미리 계산해 하나의 값으로 바꾸는 것.

---

## 더 들어가면

- `unsafe.Sizeof` 의 결과는 **상수**다(명세의 열거에 들어 있다). 그래서 배열 길이로 쓸 수 있다.
- `len`/`cap` 도 **일부 경우**에만 상수다 — 배열이나 배열 포인터에 대고 쓸 때다. 슬라이스는 아니다.
- `min`/`max` 가 상수 인자에 쓰이면 결과도 상수다 — **1.21**부터다.
- 실수 상수는 **IEEE 754 의 무한·NaN·음의 0 을 표현할 수 없다.**
  명세: "there are no constants denoting the IEEE 754 negative zero, infinity, and not-a-number values."
  그래서 `math.Inf(1)` 은 **함수**이지 상수가 아니다.
- `^1` 은 **−2**다. 타입 없는/부호 있는 상수의 보수 마스크는 −1(전부 1)이기 때문이다.
  `^uint8(1)` 은 `0xFE` 로 다르다 — 마스크가 타입에 달렸다.
- (7)절의 `LEAQ (BX)(AX*2), AX` 는 x86 의 주소 계산 명령을 산술에 쓴 것이다.
  곱셈기 없이 `×2 + kb` 를 한 번에 한다 — **최적화의 관찰**이지 언어의 성질이 아니다.

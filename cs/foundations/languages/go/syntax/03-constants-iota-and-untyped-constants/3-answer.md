# go/syntax/03 — 상수·`iota`·타입 없는 상수 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 손으로 옮겨 적은 블록은 없다.\
> 블록은 전부 `===== 소스: … =====` 로 소스를 먼저 싣는다 — **그대로 다시 던질 수 있게** 하기 위해서다.
> ★ **근거로 읽을 칸** — 상수의 값과 `%T`, 컴파일 에러 문장 본문, `파일:줄:칸`, 종료 코드,
> 어셈블리에서 **곱셈 명령이 있나 없나**.
> **근거로 읽지 않을 칸** — 어셈블리의 `size=`·레지스터 이름·오프셋(아키텍처와 판에 달렸다),
> `1 << 512` 가 에러라는 **경계 자체**(gc 의 한계이지 명세의 약속이 아니다).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `int` · `float64` · `uint8` · `complex128` — 같은 `K` 가 자리마다 갈린다

**출력**

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

**왜 그런가**

| 자리 | 타입 | 왜 |
|---|---|---|
| `var a = K` | `int` | 문맥이 타입을 안 준다 → **기본 타입** |
| `var b float64 = K` | `float64` | 변수 선언이 타입을 준다 |
| `var c byte = K` | `uint8` | 〃 (`byte` 는 `uint8` 의 별칭) |
| `var d complex128 = K` | `complex128` | 〃 — `(3+0i)` 로 찍힌다 |
| `takesFloat(K)` | `float64` | **함수 인자도 대입 지점**이다 |
| `takesByte(K)` | `uint8` | 〃 |
| `%T` 로 `K` 자신 | `int` | `fmt` 의 `any` 인자는 타입을 안 준다 → 기본 타입 |
| `var i32 int32 = T` | `int32` | `T` 는 처음부터 `int32` 인 상수 |

- 마지막 줄 `K * 2.5 = 7.5` — 타입 없는 정수 상수와 실수 상수를 섞으면 **실수 상수**가 된다.

  > If the untyped operands of a binary operation (other than a shift) are of
  > different kinds, the result is of the operand's kind that appears later in this
  > list: integer, rune, floating-point, complex.

- ★ **변환을 적은 자리가 하나도 없다.** `float64(K)` 도 `byte(K)` 도 안 썼다.
  변수였다면 전부 명시 변환이 필요하다(04번 주제).

### 2. 컴파일된다 — `1 << 400` 까지 정확히 들고 있다

**출력**

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

**왜 그런가**

- `big = 1 << 200`, `huge = big * big`(= `1 << 400`) 이 **컴파일된다.**
  `uint64` 최대의 약 2×10⁹⁹ 배다.
- **`back = 2`** 가 그 증거다. 중간값이 한 비트라도 잘렸다면 2로 돌아올 수 없다.
- `backMax == math.MaxInt64` 가 **true** — `math.MaxInt64 + 1` 을 만들었다가 다시 뺐는데 정확하다.
- `float64(third)` 는 `0.33333333333333331483`, `float32(third)` 는 `0.33333334326744079590`.
  상수 `1.0/3.0` 은 **정확한 값**으로 들고 있다가 **변환하는 순간** 각 타입의 정밀도로 반올림된다.
  20자리를 찍으면 그 반올림 자국이 보인다.

**`fmt.Println(big)` 으로 찍으려 하면**

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

- **컴파일 에러**다. 그리고 에러가 **61자리 수를 그대로 찍는다** —
  `1606938044258990275541962092341162602522202993782792835301376`.
  컴파일러가 그 값을 **정확히 들고 있었다**는 직접 증거다.
- 「런타임에 잘린다」가 아니다. `int` 로 못 담는 순간 **컴파일이 거부**한다.

> **임의 정밀도(arbitrary precision)** — 미리 정해진 비트 폭에 매이지 않고 계산하는 것.\
> 예: `1 << 400` 을 중간값으로 쓰고 다시 나눠 2를 얻을 수 있다.

### 3. 네 줄 · 한 줄 · 세 줄 — 전부 컴파일 타임이다

**출력**

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

**왜 그런가**

- **네 줄**이다. `int8` 에 300, `uint8` 에 −1, `float32` 에 `1e40`, 그리고 `var x uint8 = 256`.
- 마지막 줄이 **상수 선언이 아닌데 같은 층에서 걸리는** 이유 — `256` 이 **타입 없는 상수**이고,
  변수 선언이 그 상수에 `uint8` 을 주려 하는데 **담기지 않기** 때문이다.
  즉 걸린 것은 변수가 아니라 **상수를 그 타입으로 만드는 일**이다.

  > It is an error if the constant value cannot be represented as a value of the respective type.

- 메시지 낱말도 갈린다 — 상수 선언 쪽은 `in constant declaration`,
  변수 쪽은 `in variable declaration` 이다. **같은 규칙의 두 자리**다.

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

- **한 줄** — `invalid operation: division by zero`.
- 런타임 패닉이 아닌 이유는 `zero` 가 **상수**여서 컴파일러가 값을 알기 때문이다.

  > The divisor of a constant division or remainder operation must not be zero.

- 같은 식을 변수로 쓰면 **런타임 패닉**이다(04번 주제). **같은 `/`, 다른 층.**

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

- **세 줄**이다.
  - `&c` — **주소를 잡을 수 없다.** 상수는 메모리에 자리가 없다.
    메시지가 `cannot take address of c (untyped int constant 10)` 로 **값까지 말해 준다.**
  - `[]int{1, 2}` — 슬라이스는 상수가 될 수 있는 타입이 아니다(`is not constant`).
  - `fmt.Sprint(1)` — **함수 호출 결과**는 컴파일 타임에 모른다.

### 4. `0 1 2 4` · `main.Weekday` · `1024 …` · `0 0 1 10 2 20` · `0`

**출력**

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

**왜 그런가**

- `Sunday Monday Tuesday` = **0 1 2**, `_` 가 3을 먹고 **`Thursday` = 4**.
  식을 안 적은 줄은 **윗줄의 식(`iota`)이 반복**되고, `iota` 는 **줄마다 다시 계산**된다.
- `Sunday` 의 `%T` 는 **`main.Weekday`** — 타입도 윗줄에서 같이 반복된다.
- `KB MB GB TB` = **1024 · 1048576 · 1073741824 · 1099511627776**.
  첫 줄 `_ = iota` 가 0을 버렸으므로 `KB` 의 `iota` 는 1이고, `1 << (10*1)` = 1024.
- `a b c d e f` = **0 0 1 10 2 20**.
  `a, b = iota, iota*10` 에서 **같은 줄의 두 `iota` 는 같은 값**이다.

  > By definition, multiple uses of `iota` in the same ConstSpec all have the same value.

- `g` = **0**. `const g = iota` 는 **다른 선언**이라 `iota` 가 다시 0부터 센다.

```text
  iota 는 카운터가 아니라 「이 블록의 몇 번째 줄인가」다

  const (
      Sunday   = iota   <- 0
      Monday            <- 1   (식 생략 = 윗줄 식 반복)
      Tuesday           <- 2
      _                 <- 3   (버려도 한 칸을 먹는다)
      Thursday          <- 4
  )
```

### 5. `5 float64` · `3 int` · `3.75 float64` · `1 float64` · `1.5 float64` · `120 int32` · `"x" string`

**출력**

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

**왜 그런가**

- `a = 2 + 3.0` → **5 · `float64`**. 종류가 다른 둘을 섞으면 뒤쪽(실수) 종류가 된다.
- `b = 15 / 4` → **3 · `int`**. 둘 다 정수 상수이므로 **정수 나눗셈**이다.
  상수라고 실수로 바꿔 주지 않는다.
- `c = 15 / 4.0` → **3.75 · `float64`**.
- ★ `theta float64 = 3 / 2` → **1**. `pi float64 = 3 / 2.` → **1.5**.
  **가르는 것은 점(`.`) 한 글자다.** 타입을 `float64` 로 적어도
  오른쪽 식이 먼저 계산되고, `3 / 2` 는 거기서 정수 나눗셈이다.
- `k = 'w' + 1` → **120 · `int32`**. 룬 상수의 종류가 rune 이고 기본 타입이 `rune`(= `int32`)이다.
- `m = string(k)` → **`"x"`**. 상수를 상수로 바꾸는 변환이라 결과도 상수다.

### 6. `1 << 512` 에서 막힌다 — 그리고 그 경계는 gc 의 것이다

**출력**

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

**왜 그런가**

- `ok511 = 1 << 511` 은 통과하고 **`bad512 = 1 << 512` 에서 `constant shift overflow`** 가 난다.
  에러는 그 줄 하나뿐이다.
- 경계는 **512비트**다. 즉 gc 의 정수 상수 표현은 511비트 시프트까지 담는다.
- ★ **이것은 명세의 약속이 아니다.** 명세가 요구하는 하한은 **256비트**다.

  > Implementation restriction: Although numeric constants have arbitrary
  > precision in the language, a compiler may implement them using an
  > internal representation with limited precision. That said, every
  > implementation must: Represent integer constants with **at least 256 bits**.
  > … Give an error if unable to represent an integer constant precisely.

- 그래서 `1 << 300` 에 기대는 코드는 **명세상 안전**하고,
  `1 << 400`(2번에서 실제로 썼다)은 **gc 에서는 되지만 명세가 약속한 범위 밖**이다.
- 약속된 것이 하나 더 있다 — **정밀도가 모자라면 에러를 낸다.** 조용히 자르지 않는다.
  그래서 이 실패는 무음 실패가 아니다.

### 7. 상수는 초기화할 것이 없다 — 어셈블리가 그것을 보인다

**출력**

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

**왜 그런가**

- `FromConst` 가 낸 코드는 **두 줄**이다 — `MOVL $2098176, AX` 와 `RET`.
  `MB*2 + KB` 의 곱셈도 덧셈도 **명령이 없다.** 컴파일러가 미리 계산해 **즉값 하나**로 접었다.
  (2098176 = 1048576×2 + 1024)
- `FromVar` 는 같은 모양인데 인자가 변수다. `LEAQ (BX)(AX*2), AX` —
  **런타임에 계산하는 명령이 하나 있다.**
- 그래서 상수는 **초기화 단계에 낄 자리가 없다.** 01번 주제의 「변수 → `init` → `main`」은
  **메모리에 값을 넣는 일**의 순서인데, 상수는 메모리에 들어가지 않는다.
- **주소를 잡을 수 없는 것**(3번의 `&c`)도 같은 사실의 다른 얼굴이다. 자리가 없으니 주소가 없다.

**무엇을 근거로 읽고 무엇을 안 읽나**

- **읽을 것** — 「곱셈·덧셈 명령이 있나 없나」. 이건 판이 바뀌어도 같은 결론이 나올 성질이다.
- **안 읽을 것** — `size=6`·`AX`/`BX` 같은 레지스터 이름·`0x0005` 오프셋.
  **아키텍처와 판**에 달렸다.
- 배너에 `grep`·`sed` 가 적혀 있는 것은, 실린 것이 **그 명령의 전체 출력**임을 밝히기 위해서다.

### 8. 타입을 안 적은 쪽이 넓다 — 적는 것은 타입이 **의미**일 때만

**출력**

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

**왜 그런가**

- `const T int32 = 3` 을 `float64` 를 받는 함수에 넘기면
  **`cannot use T (constant 3 of type int32) as float64 value in argument to takesFloat`** 다.
- 1번에서 본 대로 `const K = 3` 은 같은 자리에 **아무 문제 없이** 들어간다. **한 낱말 차이**다.
- 그런데도 타입을 적는 것이 맞는 경우 — **타입이 의미일 때**다.
  `type Weekday int` 의 `Sunday`(4번)가 그 예다. 「요일은 `float64` 자리에 들어가면 안 된다」가 **의도**다.
- **「타입 없는 상수」와 「타입 없는 값」은 같은 말이 아니다.**
  타입 없음은 **상수에만** 있는 상태다. 변수·함수 반환값은 언제나 타입이 있다.
  그래서 02번 주제에서 본 대로 `var f float64 = n`(`n` 이 `int`)은 에러다.

### 9. 상수는 컴파일 타임, 변수는 런타임 — 그것이 하나의 원칙이다

**출력** (컴파일 타임 쪽 두 블록이 근거다)

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

**왜 그런가**

| 쌍 | 상수 쪽 | 변수 쪽 |
|---|---|---|
| 넘치는 값 | `const x int8 = 300` → **컴파일 에러** | `v := 300; int8(v)` → **런타임에 조용히 44**(04번) |
| 0으로 나누기 | `7 / zero`(상수) → **컴파일 에러** | `a / b`(변수, `b == 0`) → **런타임 패닉**(04번) |

- 원칙은 하나다 — **컴파일러가 값을 아는 자리에서는 거부하고, 모르는 자리에서는 런타임으로 넘긴다.**
- 그리고 넘긴 쪽의 처리가 둘로 갈린다 — **오버플로는 조용히 감싸고, 0나누기는 패닉**한다.
  그 대비가 04번 주제의 본문이다.
- **명세가 「조용히 자르지 않는다」고 약속한 자리**는 상수 쪽이다 —
  "Give an error if unable to represent an integer constant precisely."
  변수 쪽에는 그런 약속이 **없다.** 오히려 "Overflow does not cause a run-time panic" 이라고 적혀 있다.

### 10. 다른 주제와 잇기

**출력** — 없음(연결 문항).

**왜 그런가**

- **`i := 0` 이 `int`** — 이 주제 (5)절의 **기본 타입** 규칙이다.
  변수 쪽 표면의 정본은 [02번 주제](../02-variable-declarations-and-zero-values/).
- **`var f float64 = 1` 은 되고 `var f float64 = n` 은 안 되는 이유** —
  앞은 **타입 없는 상수**라 대입 지점에서 `float64` 가 되고, 뒤는 이미 `int` 타입이 붙은 값이라
  **명시 변환**이 필요하다. 정본은 [04번 주제](../04-numeric-types-conversions-and-integer-division/).
- **`'w' + 1` 이 `int32`** — 룬 상수와 `rune` 별칭의 배경. 정본은 목록의 **10번 주제**.
- **`go tool compile -S` 읽는 법** — 정본은 목록의 **52번 주제**.
  여기서는 「곱셈 명령이 있나 없나」 한 물음에만 썼다.
- **`iota` 값을 DB 에 저장하면 안 되는 이유** — `iota` 는 **줄 번호**라서
  블록 중간에 한 줄을 넣으면 **그 아래 값이 전부 밀린다.**
  저장된 데이터는 안 밀리므로 **코드와 데이터의 뜻이 어긋난다.**
  밖으로 나가는 값은 숫자를 직접 적거나 문자열로 둔다.

---

## 실행 검증

| 실험 | 던진 명령 | 결과 | 문항 |
|---|---|---|---|
| 판 확인 | `go version` · `go env` | `go1.27.1 linux/amd64` | 머리말 |
| 타입 없는 상수 8자리 (`t03a`) | `go build -trimpath && ./prog` | `int`/`float64`/`uint8`/`complex128` 등 | 1 |
| 타입 있는 상수를 `float64` 로 (`t03b`) | `go build` | `cannot use T (constant 3 of type int32) …` | 8 |
| `1 << 200` · `1 << 400` (`t03c`) | `go build && ./prog` | `back = 2` · `backMax == MaxInt64` true | 2 |
| 큰 상수를 변수 자리에 (`t03d`) | `go build` | **61자리 수를 찍는 컴파일 에러** | 2 |
| 상수가 될 수 없는 셋 (`t03e`) | `go build` | 세 줄 — 주소·슬라이스·함수 호출 | 3 |
| 타입에 안 담기는 상수 (`t03f`) | `go build` | **네 줄** — 상수 선언 3 + 변수 선언 1 | 3 · 9 |
| 상수 0으로 나누기 (`t03g`) | `go build` | `invalid operation: division by zero` | 3 · 9 |
| `iota` 네 블록 (`t03h`) | `go build && ./prog` | `0 1 2 4` · `main.Weekday` · `0 0 1 10 2 20` · `g = 0` | 4 |
| 종류와 기본 타입 (`t03j`) | 〃 | `theta = 1` · `pi = 1.5` · `k` 는 `int32` | 5 |
| 정밀도 경계 (`t03k`) | `go build` | `1 << 511` 통과 · **`1 << 512` 에서 `constant shift overflow`** | 6 |
| 어셈블리 (`t03i`) | `go tool compile -S -trimpath "$PWD" -p sizes …` | `FromConst` 는 `MOVL $2098176, AX` 하나 | 7 |
| 안 쓴 상수 (`t03m`) | `go build` | **에러 아님**(안 쓴 **변수**만 에러) | 2-summary |

**구현·환경에 달린 항목**(다시 찍을 자리)

| 항목 | 무엇에 달렸나 |
|---|---|
| **`1 << 512` 가 에러라는 경계** | **gc 의 내부 표현**. 명세의 하한은 256비트다 |
| 어셈블리의 명령·레지스터·`size=`·오프셋 | **아키텍처(amd64)와 판(go1.27.1)** |
| `MOVL $2098176, AX` 라는 **즉값 접기** | **gc 의 최적화**. 명세는 코드 생성을 약속하지 않는다 |
| 실수 상수식의 **반올림** | **명세가 허용**("A compiler may use rounding …"). gc 에서는 **재현 조건을 못 만들었다** — 「안 돌려 봄」이 아니라 **못 만든 것**이다 |
| `float32`/`float64` 변환의 20자리 | **IEEE 754**. 이건 흔들리지 않는다 |
| 32비트 플랫폼에서 `int` 기본 타입의 폭 | **못 돌려 봤다** — 이 머신에 그 타깃이 없다(04번 주제에서 다시 다룬다) |

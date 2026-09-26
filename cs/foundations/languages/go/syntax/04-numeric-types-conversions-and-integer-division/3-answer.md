# go/syntax/04 — 수치 타입과 명시 변환·오버플로·정수 나눗셈 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 손으로 옮겨 적은 블록은 없다.\
> 블록은 전부 `===== 소스: … =====` 로 소스를 먼저 싣는다 — **그대로 다시 던질 수 있게** 하기 위해서다.
> ★ **오버플로가 걸린 프로그램은 세 빌드로 돌렸다** — 기본 · `-gcflags='all=-N -l'` · `-race`.
> **한 글자도 다르지 않았다**(2번).
> ★ **근거로 읽을 칸** — 값, `%T`, 에러·패닉 문장 본문, `파일:줄:칸`, 종료 코드.
> **근거로 읽지 않을 칸** — `unsafe.Sizeof(int)` 가 8인 것(플랫폼),
> **범위 밖 부동소수 변환의 값**(명세가 `implementation-dependent` 라고 못 박았다),
> 어셈블리의 레지스터·오프셋·`size=`, 패닉 스택의 `+0x…`.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 네 줄 — 다섯 개의 연산 중 하나만 통과한다

**출력**

```text
===== 소스: t04a.go =====
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
===== 명령: go build -trimpath -o prog . =====
# ex
./t04a.go:11:14: invalid operation: i + i64 (mismatched types int and int64)
./t04a.go:12:14: invalid operation: i32 + i64 (mismatched types int32 and int64)
./t04a.go:14:14: invalid operation: f * i (mismatched types float64 and int)
./t04a.go:17:14: invalid operation: r + b (mismatched types rune and byte)
(exit 1)
```

**왜 그런가**

- 에러는 **네 줄**이다 — `i + i64` · `i32 + i64` · `f * i` · `r + b`.
- **`fmt.Println(i + 1)` 만 통과**했다. `1` 이 **타입 없는 상수**라 문맥에서 `int` 가 되기 때문이다
  (03번 주제). **상수만이 유일한 예외**다.
- `r + b` 는 `rune`(= `int32`)과 `byte`(= `uint8`)다. 둘 다 정수 별칭이지만 **폭도 부호도 다르다.**
  에러 메시지가 별칭 이름(`rune`·`byte`)을 그대로 쓴다.
- 근거는 명세의 한 문장이다.

  > To avoid portability issues all numeric types are **named types and thus distinct** except
  > `byte` … and `rune` …. **Explicit conversions are required** when different numeric types
  > are mixed in an expression or assignment.

**고치는 법**

```text
  fmt.Println(int64(i) + i64)
  fmt.Println(int64(i32) + i64)
  fmt.Println(f * float64(i))
  fmt.Println(r + rune(b))       // 또는 int32(r) + int32(b)
```

### 2. `64` · `-56` · `255` · `127` · `MinInt64` · `MinInt64` — 그리고 세 빌드가 같다

**출력**

```text
===== 소스: t04b.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
uint8 200 * 200      = 64     (uint8)  — C 라면 int 로 승격해 40000
int8  100 + 100      = -56    (int8)
uint8 0 - 1          = 255    (uint8)
int8  MinInt8 - 1    = 127    (int8)
int64 MaxInt64 + 1   = -9223372036854775808  (int64)
int   MaxInt + 1     = -9223372036854775808  (int)
(exit 0)
```

**왜 그런가**

| 식 | 값 | `%T` |
|---|---|---|
| `uint8` 200 × 200 | **64** | `uint8` |
| `int8` 100 + 100 | **−56** | `int8` |
| `uint8` 0 − 1 | **255** | `uint8` |
| `int8` MinInt8 − 1 | **127** | `int8` |
| `int64` MaxInt64 + 1 | **−9223372036854775808** | `int64` |
| `int` MaxInt + 1 | 같은 값 | `int` |

- **`%T` 가 전부 원래 타입 그대로**인 것이 핵심이다. 연산이 결과 타입을 **키우지 않는다.**

  > Arithmetic operators … yield a result of the same type as the first operand.

**C 로 같은 코드를 쓰면**

- **40000 이 나온다.** C 에는 **정수 승격**이 있어 `unsigned char` 둘이 먼저 `int` 로 올라가고,
  결과도 `int` 라 절단이 일어나지 않는다.
  실측은 [`../../../c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/`](../../../c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/) (3)절에 있다.

```text
  같은 코드, 다른 답

  C                                  Go
  200 (uchar) -> 200 (int)           200 (uint8) 그대로
  200 (uchar) -> 200 (int)           200 (uint8) 그대로
  200*200 = 40000 (int)              40000 mod 256 = 64 (uint8)
```

**최적화를 끄면 / `-race` 를 붙이면**

```text
===== 소스: t04b.go =====
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
===== 명령: go build -trimpath -o p1 . && ./p1 | md5sum =====
cb6d20b62eeca524273d35f1ad447856  -
(exit 0)
===== 명령: go build -trimpath -gcflags='all=-N -l' -o p2 . && ./p2 | md5sum =====
cb6d20b62eeca524273d35f1ad447856  -
(exit 0)
===== 명령: go build -trimpath -race -o p3 . && ./p3 | md5sum =====
cb6d20b62eeca524273d35f1ad447856  -
(exit 0)
===== 명령: ./p1 > a; ./p2 > b; ./p3 > c; diff a b && diff a c && echo '세 판이 한 글자도 같다' =====
세 판이 한 글자도 같다
(exit 0)
===== 명령: rm -f p1 p2 p3 a b c =====
(exit 0)
```

- **세 빌드의 md5 가 같다.** `diff` 까지 돌려 **한 글자도 같다**는 것을 확인했다.
- ★ Rust 와 정반대다. Rust 는 **디버그에서 패닉하고 릴리스에서 감싸며**, 감싸는 쪽이 **구현 재량**이다.
  Go 는 **빌드와 무관하게 감싸고 그것이 명세**다.

  > For signed integers, the operations `+`, `-`, `*`, `/`, and `<<` may legally
  > overflow and the resulting value exists and is **deterministically defined** …
  > **Overflow does not cause a run-time panic.**

### 3. `44 · 44 · 44 · 0xFFFFFFF0 · 255 · 18446744073709551615 · -1` — 경고는 0줄

**출력**

```text
===== 소스: t04g.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
uint8(v)                     = 44
uint8(id(300))               = 44
int8(v)                      = 44
uint32(int8(v16))            = 0xFFFFFFF0
uint8(n)                     = 255
uint64(n)                    = 18446744073709551615
int64(uint64(n))             = -1
(exit 0)
```

**왜 그런가**

- `uint8(v)`·`uint8(id(300))`·`int8(v)` 가 전부 **44**다. 300 = 256 + 44.
- **컴파일 경고는 0줄**이다. 빌드가 그냥 성공한다(`exit 0`).
  명세가 그것을 명시한다 — "The conversion always yields a valid value;
  **there is no indication of overflow.**"
- `uint8(n)`(`n` 이 −1)은 **255**, `uint64(n)` 은 **18446744073709551615**.
  `int64(uint64(n))` 은 다시 **−1** — 비트가 그대로라 왕복이 된다.

**`uint32(int8(v16))` 의 두 단계**

```text
  v16 = 0x10F0 (uint16)

  [1] int8(v16)     하위 8비트만 남긴다: 0xF0 = -16 (int8)
  [2] uint32(-16)   부호 확장: 0xFFFFFFF0
```

> When converting between integer types, if the value is a signed integer, it is
> **sign extended** to implicit infinite precision; otherwise it is zero extended.
> It is then **truncated** to fit in the result type's size.
> For example, if `v := uint16(0x10F0)`, then `uint32(int8(v)) == 0xFFFFFFF0`.

**상수로 쓰면**

```text
===== 소스: t04h.go =====
package main

import "fmt"

func main() {
	fmt.Println(uint8(300))
	fmt.Println(int8(-129))
	fmt.Println(uint(-1))
	fmt.Println(int(3.14))
}
===== 명령: go build -trimpath -o prog . =====
# ex
./t04h.go:6:20: constant 300 overflows uint8
./t04h.go:7:19: constant -129 overflows int8
./t04h.go:8:19: constant -1 overflows uint
./t04h.go:9:18: cannot convert 3.14 (untyped float constant) to type int
(exit 1)
```

- **컴파일 에러 네 줄**이다. 값이 컴파일 타임에 보이면 **거부**한다(03번 주제).
- **같은 수, 같은 타입, 다른 층** — 변수면 조용히 44, 상수면 컴파일 에러다.

### 4. 앞 두 줄만 근거가 된다 — 나머지 여섯은 구현 의존

**출력**

```text
===== 소스: t04f.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
int32(id(3.9))        = 3
int32(id(-3.9))       = -3
int32(id(1e30))       = -2147483648   ← 구현 의존
int32(id(-1e30))      = -2147483648   ← 구현 의존
int32(id(math.NaN())) = -2147483648   ← 구현 의존
int64(id(1e30))       = -9223372036854775808   ← 구현 의존
uint8(id(-1.5))       = 255   ← 구현 의존
uint8(id(300.7))      = 44   ← 구현 의존
(exit 0)
```

**왜 그런가**

| 식 | 값 | 근거로 쓸 수 있나 |
|---|---|---|
| `int32(id(3.9))` | 3 | **쓸 수 있다** — 0쪽 버림은 명세 보장 |
| `int32(id(-3.9))` | −3 | **쓸 수 있다** — 〃 |
| `int32(id(1e30))` | −2147483648 | **못 쓴다** — 구현 의존 |
| `int32(id(-1e30))` | −2147483648 | **못 쓴다** |
| `int32(id(math.NaN()))` | −2147483648 | **못 쓴다** |
| `int64(id(1e30))` | −9223372036854775808 | **못 쓴다** |
| `uint8(id(-1.5))` | 255 | **못 쓴다** |
| `uint8(id(300.7))` | 44 | **못 쓴다** |

> In all non-constant conversions involving floating-point or complex values,
> if the result type cannot represent the value the conversion succeeds but the
> **result value is implementation-dependent.**

- 「**성공한다**」는 보장이고 「**값**」은 보장이 아니다. 여섯 줄 전부 **이 판의 관찰**로만 읽는다.
- **`id()` 를 거친 이유** — 상수 접기를 막기 위해서다. `int32(1e30)` 이라고 바로 쓰면
  **상수 변환**이 되어 컴파일 에러가 난다(3번의 `int(3.14)` 와 같은 층). 런타임 변환을 보려면
  값이 함수를 한 번 지나가야 한다.
- **내림이 아니라 0쪽 버림**인 것은 **음수 줄에서 갈린다** — `int32(-3.9)` 가 **−3**이다.
  내림이었으면 −4 였을 것이다. **양수만 보면 구별이 안 된다.**

### 5. 몫은 0 쪽, 나머지는 왼쪽 부호를 따른다

**출력**

```text
===== 소스: t04c.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
   x    y |  x / y  x % y
-----------+--------------
   5    3 |      1      2
  -5    3 |     -1     -2
   5   -3 |     -1      2
  -5   -3 |      1     -2
  11    4 |      2      3
 -11    4 |     -2     -3

-11 >> 2 = -3   (나눗셈이 아니라 음의 무한대 쪽 버림)
-11 / 4  = -2   (0 쪽 버림)
(exit 0)
```

**왜 그런가**

| x | y | x / y | x % y |
|---|---|---|---|
| 5 | 3 | 1 | 2 |
| −5 | 3 | **−1** | **−2** |
| 5 | −3 | **−1** | **2** |
| −5 | −3 | 1 | **−2** |
| 11 | 4 | 2 | 3 |
| −11 | 4 | **−2** | **−3** |

- **나머지의 부호를 정하는 것은 피제수(왼쪽)** 다. 제수의 부호는 나머지에 영향이 없다.
- 관계식이 명세에 있다 — `x = q*y + r` 이고 `|r| < |y|`, 그리고 몫은 **0 쪽으로 버린다.**
- **마지막 두 줄** — `-11 / 4` 는 **−2**(0 쪽), `-11 >> 2` 는 **−3**(음의 무한대 쪽).

  > `x >> 1` is the same as `x/2` but **truncated towards negative infinity**.

  양수에서는 둘이 같아서 **테스트가 통과하고, 음수 입력에서만 갈린다.**

**`b` 가 0이면**

```text
===== 소스: t04e.go =====
package main

import (
	"fmt"
	"os"
)

func main() {
	a, b := 7, 0
	fmt.Println("7 % 0 도 같은 패닉이다 — 먼저 7 / 0 부터")
	fmt.Fprintln(os.Stderr, "----- 여기까지 stdout -----")
	fmt.Println(a / b)
}
===== 명령: go build -trimpath -o prog . =====
(exit 0)
===== 명령: ./prog 2>&1 =====
7 % 0 도 같은 패닉이다 — 먼저 7 / 0 부터
----- 여기까지 stdout -----
panic: runtime error: integer divide by zero

goroutine 1 [running]:
main.main()
	ex/t04e.go:12 +0x8a
(exit 2)
```

- 변수면 **런타임 패닉** — `panic: runtime error: integer divide by zero`, 종료 코드 **2**.
- **상수 0이면 컴파일 에러**다(03번 주제).

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

> If the divisor is a constant, it must not be zero.
> If the divisor is zero at run time, a run-time panic occurs.

### 6. 다섯 줄 찍고 여섯째에서 죽는다 — 종료 코드 2

**출력**

```text
===== 소스: t04k.go =====
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
===== 명령: go build -trimpath -o prog . =====
(exit 0)
===== 명령: ./prog 2>&1 =====
int32(1) << 31 = -2147483648
int32(1) << 32 = 0  (C 라면 미정의 동작)
int32(1) << 99 = 0
int32(-8) >> 1 = -4  (산술 시프트)
uint8(0xF8) >> 1 = 124  (논리 시프트)
----- 여기까지 stdout · 아래부터 음수 시프트 -----
panic: runtime error: negative shift amount

goroutine 1 [running]:
main.sh(...)
	ex/t04k.go:8
main.main()
	ex/t04k.go:19 +0x29d
(exit 2)
```

**왜 그런가**

- `int32(1) << 31` = **−2147483648**(부호 비트로 밀려 들어갔다).
- **`int32(1) << 32` 와 `<< 99` 가 둘 다 0**이다. C 에서는 **폭 이상의 시프트가 미정의 동작**인데,
  Go 는 값을 정해 뒀다.

  > There is **no upper limit** on the shift count. Shifts behave
  > as if the left operand is shifted n times by 1 for a shift count of n.

- `int32(-8) >> 1` = **−4**(산술 시프트), `uint8(0xF8) >> 1` = **124**(논리 시프트).
  C 에서 부호 있는 오른쪽 시프트는 **구현 정의**인데 Go 는 명세로 정해 둔다.
- 마지막 줄 — **시프트 횟수가 음수라 런타임 패닉**이다.
  `panic: runtime error: negative shift amount`, 종료 코드 **2**.
  스택이 두 칸(`main.sh` → `main.main`)으로 보이는 것은 `sh` 가 인라인됐기 때문이다(`(...)` 표기).

> **산술 시프트(arithmetic shift)** — 부호 비트를 유지하며 오른쪽으로 미는 것.\
> 예: `int32(-8) >> 1` 은 −4 다. 위쪽이 1로 채워진다.

### 7. 폭도 같고 범위도 같다 — 다른 것은 **이름**뿐이다

**출력**

```text
===== 소스: t04i.go =====
package main

import (
	"fmt"
	"math"
	"unsafe"
)

func main() {
	var i int
	var i64 int64
	var i32 int32
	var u uint
	var up uintptr
	var r rune
	var b byte
	fmt.Printf("%-10s %%T=%-8T Sizeof=%d\n", "int", i, unsafe.Sizeof(i))
	fmt.Printf("%-10s %%T=%-8T Sizeof=%d\n", "int64", i64, unsafe.Sizeof(i64))
	fmt.Printf("%-10s %%T=%-8T Sizeof=%d\n", "int32", i32, unsafe.Sizeof(i32))
	fmt.Printf("%-10s %%T=%-8T Sizeof=%d\n", "uint", u, unsafe.Sizeof(u))
	fmt.Printf("%-10s %%T=%-8T Sizeof=%d\n", "uintptr", up, unsafe.Sizeof(up))
	fmt.Printf("%-10s %%T=%-8T Sizeof=%d\n", "rune", r, unsafe.Sizeof(r))
	fmt.Printf("%-10s %%T=%-8T Sizeof=%d\n", "byte", b, unsafe.Sizeof(b))
	fmt.Println()
	fmt.Println("int 과 int64 는 폭이 같다 :", unsafe.Sizeof(i) == unsafe.Sizeof(i64))
	fmt.Println("그런데도 서로 대입이 안 된다 — 04a 의 컴파일 에러가 그 증거다")
	fmt.Println()
	fmt.Println("math.MaxInt   =", math.MaxInt)
	fmt.Println("math.MaxInt64 =", math.MaxInt64)
	fmt.Println("두 값이 같은가 :", math.MaxInt == int(math.MaxInt64))
}
===== 명령: go build -trimpath -o prog . && ./prog =====
int        %T=int      Sizeof=8
int64      %T=int64    Sizeof=8
int32      %T=int32    Sizeof=4
uint       %T=uint     Sizeof=8
uintptr    %T=uintptr  Sizeof=8
rune       %T=int32    Sizeof=4
byte       %T=uint8    Sizeof=1

int 과 int64 는 폭이 같다 : true
그런데도 서로 대입이 안 된다 — 04a 의 컴파일 에러가 그 증거다

math.MaxInt   = 9223372036854775807
math.MaxInt64 = 9223372036854775807
두 값이 같은가 : true
(exit 0)
```

**왜 그런가**

- `unsafe.Sizeof(int)` 와 `unsafe.Sizeof(int64)` 가 **둘 다 8**이고,
  `unsafe.Sizeof(i) == unsafe.Sizeof(i64)` 가 **true** 다.
- `math.MaxInt == int(math.MaxInt64)` 도 **true** — **표현 범위까지 같다.**
- 그런데도 안 섞인다. 근거가 되는 명세의 낱말은 「**named types and thus distinct**」다.
  뒤이은 예문이 아예 이 경우를 든다 —
  "For instance, `int32` and `int` are not the same type even though they may have
  the same size on a particular architecture."
- **`rune` 과 `int32` 는 다르다** — 이쪽은 **별칭(alias)** 이라 **같은 타입**이다.
  증거가 `%T` 에 있다 — `rune` 을 찍으면 **`int32`** 라고 나오고 `byte` 를 찍으면 **`uint8`** 이라고 나온다.
  `%T` 가 답할 다른 이름이 없다는 것이 「같은 타입」의 뜻이다.

```text
  별개 타입                          별칭
  int  (Sizeof 8)                   rune  -> %T 가 int32 라고 답한다
  int64(Sizeof 8)                   byte  -> %T 가 uint8 이라고 답한다
    -> %T 가 서로 다르다              -> 이름이 하나뿐이다
    -> 섞으면 컴파일 에러              -> 그냥 섞인다
```

### 8. ①②⑤ 는 명세 보장, ③④ 는 구현에 달렸다

**출력** (판정의 근거가 되는 두 블록)

```text
===== 소스: t04i.go =====
package main

import (
	"fmt"
	"math"
	"unsafe"
)

func main() {
	var i int
	var i64 int64
	var i32 int32
	var u uint
	var up uintptr
	var r rune
	var b byte
	fmt.Printf("%-10s %%T=%-8T Sizeof=%d\n", "int", i, unsafe.Sizeof(i))
	fmt.Printf("%-10s %%T=%-8T Sizeof=%d\n", "int64", i64, unsafe.Sizeof(i64))
	fmt.Printf("%-10s %%T=%-8T Sizeof=%d\n", "int32", i32, unsafe.Sizeof(i32))
	fmt.Printf("%-10s %%T=%-8T Sizeof=%d\n", "uint", u, unsafe.Sizeof(u))
	fmt.Printf("%-10s %%T=%-8T Sizeof=%d\n", "uintptr", up, unsafe.Sizeof(up))
	fmt.Printf("%-10s %%T=%-8T Sizeof=%d\n", "rune", r, unsafe.Sizeof(r))
	fmt.Printf("%-10s %%T=%-8T Sizeof=%d\n", "byte", b, unsafe.Sizeof(b))
	fmt.Println()
	fmt.Println("int 과 int64 는 폭이 같다 :", unsafe.Sizeof(i) == unsafe.Sizeof(i64))
	fmt.Println("그런데도 서로 대입이 안 된다 — 04a 의 컴파일 에러가 그 증거다")
	fmt.Println()
	fmt.Println("math.MaxInt   =", math.MaxInt)
	fmt.Println("math.MaxInt64 =", math.MaxInt64)
	fmt.Println("두 값이 같은가 :", math.MaxInt == int(math.MaxInt64))
}
===== 명령: go build -trimpath -o prog . && ./prog =====
int        %T=int      Sizeof=8
int64      %T=int64    Sizeof=8
int32      %T=int32    Sizeof=4
uint       %T=uint     Sizeof=8
uintptr    %T=uintptr  Sizeof=8
rune       %T=int32    Sizeof=4
byte       %T=uint8    Sizeof=1

int 과 int64 는 폭이 같다 : true
그런데도 서로 대입이 안 된다 — 04a 의 컴파일 에러가 그 증거다

math.MaxInt   = 9223372036854775807
math.MaxInt64 = 9223372036854775807
두 값이 같은가 : true
(exit 0)
```

```text
===== 소스: t04f.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
int32(id(3.9))        = 3
int32(id(-3.9))       = -3
int32(id(1e30))       = -2147483648   ← 구현 의존
int32(id(-1e30))      = -2147483648   ← 구현 의존
int32(id(math.NaN())) = -2147483648   ← 구현 의존
int64(id(1e30))       = -9223372036854775808   ← 구현 의존
uint8(id(-1.5))       = 255   ← 구현 의존
uint8(id(300.7))      = 44   ← 구현 의존
(exit 0)
```

**왜 그런가**

| | 주장 | 층 | 근거 |
|---|---|---|---|
| ① | `uint8` 에서 `0 - 1` 이 255 | **명세 보장** | "computed modulo 2ⁿ … programs may rely on 'wrap around'" |
| ② | `int64` MaxInt64 + 1 이 MinInt64 | **명세 보장** | "deterministically defined by the signed integer representation … Overflow does not cause a run-time panic." |
| ③ | `unsafe.Sizeof(int)` 가 8 | **구현·플랫폼** | "`uint` either 32 or 64 bits · `int` same size as `uint`" |
| ④ | `int32(1e30)` 이 −2147483648 | **구현** | "the result value is implementation-dependent" |
| ⑤ | `MinInt64 / -1` 이 MinInt64 | **명세 보장** | "The one exception to this rule …" (아래 블록) |

```text
===== 소스: t04d.go =====
package main

import (
	"fmt"
	"math"
)

func div(a, b int64) int64 { return a / b }
func rem(a, b int64) int64 { return a % b }

func main() {
	x := int64(math.MinInt64)
	fmt.Println("math.MinInt64      =", x)
	fmt.Println("MinInt64 / -1      =", div(x, -1), "  (패닉하지 않는다)")
	fmt.Println("MinInt64 % -1      =", rem(x, -1))
	fmt.Println("같은 값인가          :", div(x, -1) == x)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
math.MinInt64      = -9223372036854775808
MinInt64 / -1      = -9223372036854775808   (패닉하지 않는다)
MinInt64 % -1      = 0
같은 값인가          : true
(exit 0)
```

- ⑤가 특히 헷갈린다 — **오버플로인데 값이 정해져 있다.** 명세가 예외로 못 박았다.

  > The one exception to this rule is that if the dividend `x` is
  > the most negative value for the int type of `x`, the quotient
  > `q = x / -1` is equal to `x` (and `r = 0`) due to two's-complement integer overflow

- ★ **구현에 맡겨진 칸은 정확히 둘**이다 — ③(`int` 의 폭)과 ④(범위 밖 부동소수 변환).
  나머지는 명세가 값까지 정한다.

### 9. `go build` 는 통과하고 `go vet` 이 막는다 — `go test` 는 빌드 단계에서 막는다

**출력**

```text
===== 소스: t04j.go =====
package main

import "fmt"

func main() {
	n := 65
	s := string(rune(n))
	t := string(n)
	fmt.Printf("string(rune(65)) = %q\n", s)
	fmt.Printf("string(65)       = %q\n", t)
}
===== 소스: t04j_test.go =====
package main

import "testing"

func TestNothing(t *testing.T) {}
===== 명령: go build -trimpath -o prog . =====
(exit 0)
===== 명령: go vet ./... =====
t04j.go:8:7: conversion from int to string yields a string of one rune, not a string of digits
(exit 1)
===== 명령: ./prog =====
string(rune(65)) = "A"
string(65)       = "A"
(exit 0)
===== 명령: go test ./... =====
# ex
# [ex]
./t04j.go:8:7: conversion from int to string yields a string of one rune, not a string of digits
FAIL	ex [build failed]
FAIL
(exit 1)
```

**왜 그런가**

- `go build` 는 **종료 0** 이다. 프로그램도 잘 돌아 `"A"` 를 두 번 찍는다.
- **`go vet` 이 종료 1** 로 거부한다 —
  `conversion from int to string yields a string of one rune, not a string of digits`.
- `string(65)` 은 **`"65"` 가 아니라 `"A"`** 다. `65` 를 **코드포인트**로 읽어 그 글자를 만든다.
  숫자를 문자열로 만들려면 **`strconv.Itoa(n)`** 이다.
- ★ **`go test` 는 빌드 단계에서 막는다** — 마지막 명령이 `FAIL ex [build failed]` 다.
  `go test` 가 vet 의 일부 검사를 자동으로 돌리기 때문에,
  테스트가 있는 프로젝트에서는 **빌드보다 먼저 드러난다.**
- 이 주제에서 **세 번째 창(`go vet`)이 컴파일러와 갈리는 자리**가 여기다.
  컴파일러는 「문법이 맞나」를, `go vet` 은 「뜻이 맞을 법한가」를 본다.

### 10. C 는 승격, Rust 는 패닉 — Go 는 둘 다 아니다

**출력** (Go 쪽 근거)

```text
===== 소스: t04b.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
uint8 200 * 200      = 64     (uint8)  — C 라면 int 로 승격해 40000
int8  100 + 100      = -56    (int8)
uint8 0 - 1          = 255    (uint8)
int8  MinInt8 - 1    = 127    (int8)
int64 MaxInt64 + 1   = -9223372036854775808  (int64)
int   MaxInt + 1     = -9223372036854775808  (int)
(exit 0)
```

**왜 그런가**

| 물음 | C | Rust | **Go** |
|---|---|---|---|
| `unsigned char/u8` 200×200 | **40000**(`int` 로 승격) | (디버그에서 패닉) | **64**(승격 없음) |
| `250u8 + 10` 의 디버그/릴리스 | — | **패닉(101) / `4`** | **언제나 감싼다**(세 빌드 동일) |
| 감싸는 것이 보장인가 | 부호 없는 쪽만 | **구현 재량**("at the implementation's discretion") | **명세 보장** |
| `MinInt / -1` | UB | **패닉** `divide with overflow` | **`MinInt`**(명세의 예외 조항) |
| 폭 이상 시프트 | **UB** | (별도 규칙) | **0**(명세가 정의) |
| 부호 있는 오버플로 | **UB** | 위와 같음 | **결정적으로 정의됨** |
| 「오버플로 없음」 가정 최적화 | **합법** | — | **금지**(명세 명시) |

- C 쪽 실측은 [`../../../c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/`](../../../c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/),
  Rust 쪽 실측은 [`../../../rust/syntax/03-primitive-types-and-integer-overflow/`](../../../rust/syntax/03-primitive-types-and-integer-overflow/) 에 있다.
- ★ **C 의 「미정의 동작」에 해당하는 것이 Go 에는 없다.**
  오버플로도, 폭 이상 시프트도, 부호 있는 오른쪽 시프트도 전부 **값이 정해져 있다.**
  구현에 맡긴 칸 둘(`int` 폭 · 범위 밖 부동소수 변환)도 **「구현 의존」이지 「무슨 일이 일어나도 좋다」가 아니다.**
- **마지막 행이 실무적으로 가장 크다.** 명세가 이렇게 적는다.

  > A compiler **may not** optimize code under the assumption that overflow does
  > not occur. For instance, it may not assume that `x < x + 1` is always true.

  C 에서는 그 가정이 합법이라 「검사 코드가 통째로 지워지는」 사고가 난다. Go 에서는 금지다.

### 11. 다른 주제와 잇기

**출력** — 없음(연결 문항).

**왜 그런가**

- **`i + 1` 이 통과하는 이유** — `1` 이 **타입 없는 상수**라 대입 지점에서 `int` 가 된다.
  정본은 [03번 주제](../03-constants-iota-and-untyped-constants/).
- **`string(n)` 대신 `strconv.Itoa(n)`** — 정본은 [목록의 **11번 주제**](../11-strings-strconv-bytes-and-unicode-utf8/).
  `string(rune)` 과 `string([]byte)` 의 뜻 차이는 [목록의 **10번 주제**](../10-strings-bytes-runes-and-utf8-iteration/).
- **`rune` 이 `int32` 인 이유** — 유니코드 코드포인트가 21비트라 32비트에 담는다.
  정본은 [목록의 **10번 주제**](../10-strings-bytes-runes-and-utf8-iteration/).
- **`unsafe.Sizeof` 를 제대로 다루는 주제** — [목록의 **17번 주제**](../17-struct-literals-comparability-field-tags-and-sorting/)(구조체 정렬·패딩).
  여기서는 「폭이 같다」를 보이는 데만 썼다.
- **2의 보수 표현 자체** — [`../../../../data-representation/`](../../../../data-representation/).
  그쪽은 **표현**까지, 여기는 **Go 가 그 위에 얹은 변환·오버플로 규칙**부터다.

---

## 실행 검증

| 실험 | 던진 명령 | 결과 | 문항 |
|---|---|---|---|
| 판 확인 | `go version` · `go env` | `go1.27.1 linux/amd64` | 머리말 |
| 타입이 안 섞인다 (`t04a`) | `go build -trimpath` | **네 줄** — `i + 1` 만 통과 | 1 |
| 승격 없음·랩어라운드 (`t04b`) | `go build && ./prog` | `64 -56 255 127 MinInt64 MinInt64` | 2 |
| 같은 것, 세 빌드 (`t04b`) | 기본 · `-gcflags='all=-N -l'` · `-race` + `diff` | **md5 동일 · 한 글자도 같다** | 2 |
| 정수 변환 7식 (`t04g`) | `go build && ./prog` | `44 44 44 0xFFFFFFF0 255 …` · **경고 0줄** | 3 |
| 상수 변환 4식 (`t04h`) | `go build` | **컴파일 에러 네 줄** | 3 |
| 부동→정수 8식 (`t04f`) | `go build && ./prog` | 앞 둘만 보장 · 뒤 여섯은 **구현 의존** | 4 · 8 |
| 나눗셈·나머지 6행 (`t04c`) | 〃 | 0쪽 버림 · 나머지는 왼쪽 부호 · `>>` 는 다름 | 5 |
| 변수 0나누기 (`t04e`) | `go build` · `./prog 2>&1` | `integer divide by zero` · **exit 2** | 5 |
| 상수 0나누기 (`t03g`) | `go build` | **컴파일 에러** | 5 |
| 시프트 (`t04k`) | `go build` · `./prog 2>&1` | `<< 32`·`<< 99` 가 0 · 음수 시프트에서 **패닉** | 6 |
| 폭과 이름 (`t04i`) | `go build && ./prog` | `int`/`int64` 둘 다 8 · `%T` 만 다름 | 7 · 8 |
| `MinInt64 / -1` (`t04d`) | 〃 | **패닉 없이 `MinInt64`** · 나머지 0 | 8 · 10 |
| `string(int)` (`t04j`) | `go build` · `go vet` · `./prog` · `go test` | build 0 / **vet 1** / 실행 `"A"` / **test 빌드 실패** | 9 |
| 어셈블리 (`t04l`) | `go tool compile -S -trimpath "$PWD" -p divs …` | `Add` 는 `ADDQ` 하나 · `Div` 에 `panicdivide` 분기 | 2-summary (9) |

**구현·환경에 달린 항목**(다시 찍을 자리)

| 항목 | 무엇에 달렸나 |
|---|---|
| **`unsafe.Sizeof(int)` 가 8** | **플랫폼**. 명세는 "either 32 or 64 bits" 까지만 |
| **범위 밖 부동소수 → 정수 변환의 여섯 값** | **구현**. 명세가 `implementation-dependent` 라고 명시 |
| 어셈블리의 명령·레지스터·오프셋·`size=` | **아키텍처(amd64)·판(go1.27.1)** |
| 패닉 스택의 `+0x…` 오프셋 | **빌드 산출물**. 같은 바이너리는 재실행해도 같다 |
| 인라인된 함수가 `main.sh(...)` 로 보이는 것 | **gc 의 인라인**. `-gcflags=-l` 로 끄면 달라진다 |
| `go vet` 의 `stringintconv` 검사 이름·문구 | **go vet 의 판**(go1.27.1과 함께 배포) |
| 부동소수 0나누기의 패닉 여부 | **안 던져 봤다.** 명세가 "implementation-specific" 이라고 적은 자리다 |
| FMA 융합이 실제로 일어나는가 | **안 쟀다.** 명세가 허용만 하고, 재려면 수치 비교 실험이 따로 필요하다 |
| 32비트 타깃에서의 `int` 폭 | **못 돌려 봤다** — 이 머신에 그 타깃이 없다. 「안 돌려 봄」이 아니라 환경이 없어 못 잰 것이다 |

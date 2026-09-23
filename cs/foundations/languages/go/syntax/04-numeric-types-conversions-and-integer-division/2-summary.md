# go/syntax/04 — 수치 타입과 명시 변환·오버플로·정수 나눗셈 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Go 명세](https://go.dev/ref/spec) 의 Numeric types · Arithmetic operators ·
> Integer overflow · Conversions(Conversions between numeric types) 절.\
> 웹이 아니라 **이 툴체인이 들고 있는 `$(go env GOROOT)/doc/go_spec.html` 을 열어** 인용했다.
> 그 파일의 머리는 「**Language version go1.27 (May 26, 2026)**」이다.
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 손으로 옮겨 적은 블록은 없다.\
> ★ **오버플로가 걸린 프로그램은 세 가지 빌드로 돌렸다** — 기본 · `-gcflags='all=-N -l'` · `-race`.
> **한 글자도 다르지 않았다**((4)절). Rust 처럼 「디버그/릴리스 두 답」이 Go 에는 없다.
> **버전** — 이 절의 규칙은 1.0부터 같다. `math.MaxInt`·`math.MinInt` 상수는 **1.17**부터다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 명세로, 출력은 실행으로 접지했다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것. 어느 컴파일러에서도 같다 | `go_spec.html` 원문 인용 |
| **구현(gc)** | 이 컴파일러·런타임이 그렇게 하는 것. 약속은 아니다 | `go build`·`go tool compile -S` 출력 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 실행 출력(재실행 대조까지) |

★ 이 주제는 **명세 보장 칸이 가장 큰 주제**다. 랩어라운드도, 나눗셈의 부호도, `MinInt / -1` 의 값도
전부 명세에 적혀 있다. **구현에 맡겨진 칸은 정확히 둘**이다 — `int` 의 폭과,
**범위를 벗어난 부동소수 → 정수 변환**.

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
| 랩어라운드한 값 · 나눗셈·나머지의 부호 | **안 흔들림** | **명세가 정한다** + 세 빌드 동일 |
| 컴파일 에러 문장 본문 · `파일:줄:칸` | 안 흔들림 | 재실행 대조 동일 |
| 패닉 메시지 본문 · 종료 코드 `2` | 안 흔들림 | 재실행 대조 동일 |
| **`unsafe.Sizeof(int)` 가 8인 것** | **플랫폼에 달렸다** | 명세는 "either 32 or 64 bits" 라고만 한다 |
| **범위 밖 `float64` → 정수 변환 값** | **구현에 달렸다** | 명세가 `implementation-dependent` 라고 못 박았다 |
| 패닉 스택의 `+0x…` | **판·빌드가 바뀌면 바뀐다** | 같은 바이너리는 재실행해도 같다 |
| 어셈블리의 레지스터 이름·오프셋·`size=` | **아키텍처·판이 바뀌면 바뀐다** | amd64 · go1.27.1 |
| 맵 순회 순서 | 이 주제는 맵을 아예 안 쓴다 | — |

## 한눈에 — 쉽게 말하면

**Go 의 수치 타입은 「눈금이 다른 계기판들」이고, 눈금 사이를 옮길 때는 반드시 손으로 옮겨 적어야 한다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 눈금이 고정된 계기판 | 수치 타입 (`uint8` 은 0\~255, `int64` 는 약 ±9.2×10¹⁸) |
| 눈금이 같아도 **모델명이 다르면 부품이 안 맞는다** | `int` 와 `int64` 는 폭이 같아도 **서로 대입이 안 된다** |
| 옮겨 적을 때 손으로 적어야 한다 | **명시 변환**(`int64(x)`) — 자동 승격이 없다 |
| 999 다음이 000 | **랩어라운드** — 2의 보수. **Go 에서는 언어의 약속이다** |
| 계기판에 경보기가 없다 | 오버플로에 **패닉이 없다.** 빌드 종류와 무관하다 |
| 장부에 옮겨 적기 전에 검산해 거부 | **상수**는 넘치면 컴파일 에러(03번 주제) |
| 0으로 나누는 것만은 기계가 멈춘다 | `/`·`%` 의 0 나누기는 **런타임 패닉** |

- C 와 다른 점 — **승격(promotion)이 없다.** `uint8` 끼리 곱하면 결과도 `uint8` 이라 **거기서 감긴다.**
- Rust 와 다른 점 — **디버그/릴리스 두 답이 없다.** 감싸는 것이 **구현 재량이 아니라 언어의 약속**이다.
- ★ 그래서 Go 의 오버플로는 **언제나 조용하고 언제나 같은 값**이다. 예측 가능한 대신 **경보가 없다.**

```text
      uint8 c = 200;  c * c  는?

  C  (승격 있음)                     Go (승격 없음)
  +---------------------------+     +---------------------------+
  | c 를 int 로 올린다        |     | uint8 끼리 그대로 곱한다  |
  | 200 * 200 = 40000 (int)   |     | 40000 mod 256 = 64        |
  | 절단이 안 일어난다        |     | uint8 로 64               |
  +---------------------------+     +---------------------------+
    -> 40000                          -> 64
```

**언어도 똑같은 구조다.** 왼쪽은 [`../../../c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/`](../../../c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/)
의 실측이고, 오른쪽은 아래 (3)절의 실측이다.

> **승격(integer promotion)** — 좁은 정수 타입을 연산 전에 `int` 로 올리는 C 의 규칙.\
> 예: C 에서 `unsigned char` 끼리 곱해도 결과가 `int` 라 40000 이 그대로 나온다. **Go 에는 이 규칙이 없다.**

> **랩어라운드(wrap-around)** — 표현 범위를 넘으면 반대쪽 끝에서 다시 세는 것. 2의 보수로 정의된다.\
> 예: `uint8` 에서 `0 - 1` 은 255, `int8` 에서 `100 + 100` 은 −56이다(실측).

> **명시 변환(explicit conversion)** — `T(x)` 꼴로 타입을 바꿔 적는 것. Go 는 수치 타입 사이에서 **의무**다.\
> 예: `var n int = 1; var m int64 = int64(n)`. `int64(n)` 을 빼면 컴파일 에러다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 폭이 같은 `int` 와 `int64` 가 **왜 안 섞이나** — 그리고 그 결정이 계산 결과를 어떻게 바꾸나.
2. 넘쳤을 때 Go 는 **무엇을 하기로 약속했나** — 그리고 그 약속이 없는 칸은 어디인가.
3. `/` 와 `%` 가 **음수와 0에서** 어떻게 구는가 — 상수일 때와 변수일 때가 어떻게 갈리는가.

## 동작 방식

### (1) 수치 타입의 지도 — 그리고 폭이 구현에 달린 셋

**언제 쓰나** — 타입을 고를 때마다.

| 계열 | 타입 | 폭(비트) |
|---|---|---|
| 부호 없음 | `uint8` `uint16` `uint32` `uint64` | 8 16 32 64 |
| 부호 있음 | `int8` `int16` `int32` `int64` | 8 16 32 64 |
| 실수 | `float32` `float64` | 32 64 (IEEE 754) |
| 복소수 | `complex64` `complex128` | 64 128 |
| **구현에 달림** | `uint` `int` `uintptr` | **32 또는 64** |
| 별칭 | `byte` = `uint8` · `rune` = `int32` | — |

명세:

> There is also a set of predeclared integer types with implementation-specific sizes:
> `uint` either 32 or 64 bits · `int` same size as `uint` ·
> `uintptr` an unsigned integer large enough to store the uninterpreted bits of a pointer value

> To avoid portability issues all numeric types are **named types and thus distinct** except
> `byte`, which is an alias for `uint8`, and `rune`, which is an alias for `int32`.
> **Explicit conversions are required** when different numeric types are mixed in an expression
> or assignment. For instance, `int32` and `int` are not the same type even though they may have
> the same size on a particular architecture.

★ 마지막 문장이 이 주제 전체의 근거다 — **폭이 같아도 다른 타입**이고, **변환은 의무**다.

비용 — 없음. 변환은 대부분 명령 하나거나 아예 없다.

### (2) ★ 섞이지 않는다 — 폭이 같아도

**언제 쓰나** — `len()`(=`int`)과 라이브러리가 주는 `int64` 를 같이 쓸 때. 즉 아주 자주.

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

그림 해설 (한 단계씩):

- `i + i64`(`int` + `int64`)가 **에러**다. `int32 + int64` 도, `float64 * int` 도 마찬가지.
- **`rune + byte` 도 에러**다 — 둘 다 정수 별칭이지만 `int32` 와 `uint8` 이라 다르다.
- ★ **에러가 네 줄뿐이다.** 소스에는 다섯 개의 연산이 있는데 `i + 1` 은 **통과**했다.
  `1` 이 **타입 없는 상수**라 `int` 가 됐기 때문이다(03번 주제).
- 고치는 법은 언제나 같다 — `int64(i) + i64`.

```text
   i (int)      i64 (int64)
      |             |
      +-----+-------+
            |
        컴파일 에러: mismatched types int and int64
            |
     int64(i) + i64   <- 손으로 옮겨 적어야 한다
```

비용 — 변환 자체는 거의 공짜다. 대신 **좁히는 변환은 값을 잃는다**((5)절).

### (3) ★ 승격이 없다 — 연산은 피연산자의 타입에서 일어난다

**언제 쓰나** — 좁은 타입(`uint8`·`int8`·`int16`)으로 계산할 때.

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

그림 해설 (한 단계씩):

- **`uint8` 200 × 200 = 64**. 40000 이 아니다. `uint8` 끼리의 곱은 **`uint8` 안에서** 일어난다.\
  ★ **C 는 여기서 40000 을 준다** — 승격이 둘 다 `int` 로 올리기 때문이다.
  같은 코드, 다른 답. [`../../../c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/`](../../../c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/) (3)절과 나란히 읽어라.
- `int8` 100 + 100 = **−56**, `uint8` 0 − 1 = **255**, `int8` MinInt8 − 1 = **127**.
  전부 그 타입의 폭 안에서 2의 보수로 감긴다.
- `int64` MaxInt64 + 1 = **MinInt64**, `int` MaxInt + 1 도 같다.
- **`%T` 가 전부 원래 타입 그대로**다 — 결과 타입이 커지지 않았다는 직접 증거다.

명세:

> Arithmetic operators apply to numeric values and yield **a result of the same
> type as the first operand.**

비용 — 없음. 오히려 승격이 없어 **명령이 덜 나간다.**

### (4) ★ 오버플로는 조용히 감싼다 — 그리고 그것은 **언어의 약속**이다

**언제 쓰나** — 덧셈·뺄셈·곱셈·왼쪽 시프트가 있는 모든 코드.

(3)절의 같은 프로그램을 **세 가지 빌드**로 돌렸다.

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

그림 해설 (한 단계씩):

- 기본 빌드 · `-gcflags='all=-N -l'`(최적화·인라인 끄기) · `-race` — **md5 가 셋 다 같다.**
- `diff` 까지 돌려 **한 글자도 같다**는 것을 확인했다.
- ★ **Rust 와 정확히 반대다.** Rust 는 디버그에서 패닉하고 릴리스에서 감싸며,
  **감싸는 쪽은 구현 재량**이다([`../../../rust/syntax/03-primitive-types-and-integer-overflow/`](../../../rust/syntax/03-primitive-types-and-integer-overflow/)).
  Go 는 **빌드와 무관하게 감싸고, 그것이 명세**다.

명세가 그것을 두 문단으로 약속한다.

> For unsigned integer values, the operations `+`, `-`, `*`, and `<<` are
> computed modulo 2ⁿ, where n is the bit width of the unsigned integer's type.
> Loosely speaking, these unsigned integer operations
> discard high bits upon overflow, and programs may rely on "wrap around".

> For signed integers, the operations `+`, `-`, `*`, `/`, and `<<` **may legally
> overflow** and the resulting value exists and is **deterministically defined**
> by the signed integer representation, the operation, and its operands.
> **Overflow does not cause a run-time panic.**
> A compiler may not optimize code under the assumption that overflow does
> not occur. For instance, it may not assume that `x < x + 1` is always true.

읽는 법 세 줄.

- 부호 없는 쪽은 「**모듈로 2ⁿ**」이고 「**의존해도 된다**」까지 적혀 있다.
- 부호 있는 쪽도 「**결정적으로 정의된다**」이고 「**패닉하지 않는다**」다. C 의 UB 와 **완전히 다르다.**
- 마지막 문장이 덤이다 — **컴파일러가 「오버플로는 안 난다」고 가정해 최적화할 수 없다.**
  C 에서 UB 를 이용한 최적화가 만드는 사고가 Go 에는 없다.

비용 — 검사 코드가 **아예 없다.** 03번 주제의 창을 빌려 어셈블리로 확인할 수 있다((8)절).

### (5) 명시 변환 — 자르고, 부호 확장하고, 말이 없다

**언제 쓰나** — 타입을 억지로 맞출 때. **이 주제에서 가장 조심할 연산이다.**

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

그림 해설 (한 단계씩):

- `uint8(v)`(`v` 가 300)가 **44**다. 경고가 **한 줄도 없다.**
- `int8(v)` 도 44, `uint8(n)`(`n` 이 −1)은 **255**, `uint64(n)` 은 **18446744073709551615**.
- `uint32(int8(v16))` 이 **`0xFFFFFFF0`** 이다 — 명세가 예제로 든 바로 그 식이다.
  `int8` 로 좁힌 뒤 **부호 확장**되어 위쪽이 전부 1이 된다.
- `int64(uint64(n))` 은 다시 **−1** 이다. 비트가 그대로라 왕복이 된다.

명세:

> When converting between integer types, if the value is a signed integer, it is
> **sign extended** to implicit infinite precision; otherwise it is **zero extended**.
> It is then **truncated** to fit in the result type's size.
> For example, if `v := uint16(0x10F0)`, then `uint32(int8(v)) == 0xFFFFFFF0`.
> **The conversion always yields a valid value; there is no indication of overflow.**

★ 마지막 문장이 이 절의 전부다 — **넘침을 알려 주는 수단이 없다.**

**상수는 다르다.**

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

- `uint8(300)`·`int8(-129)`·`uint(-1)`·`int(3.14)` 는 전부 **컴파일 에러**다.
- 값이 **컴파일 타임에 보이면 거부**하고, **런타임에만 보이면 조용히 자른다.**
  03번 주제의 「상수는 컴파일 타임」과 정확히 같은 원칙이다.

비용 — 변환 명령 하나. **값의 손실이 진짜 비용**이다.

### (6) 부동소수 → 정수 — 0쪽으로 버리고, 범위를 넘으면 **구현에 달렸다**

**언제 쓰나** — 비율·평균을 정수로 떨굴 때.

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

그림 해설 (한 단계씩):

- `int32(3.9)` = **3**, `int32(-3.9)` = **−3**. **0 쪽으로 버린다**(내림이 아니다).
- 범위를 넘는 넷(`1e30`·`-1e30`·`NaN`·`uint8(-1.5)`)은 **전부 값이 나오고 에러가 없다.**
  이 판에서는 `-2147483648`·`-9223372036854775808`·`255`·`44` 였다.
- ★ **이 네 값은 근거로 쓰면 안 된다.** 명세가 직접 그렇게 적었다.

> When converting a floating-point number to an integer, the fraction is discarded
> (truncation towards zero).

> In all non-constant conversions involving floating-point or complex values,
> **if the result type cannot represent the value the conversion succeeds but the
> result value is implementation-dependent.**

- 즉 **「성공한다」는 보장이고 「값」은 보장이 아니다.** 다른 아키텍처·다른 컴파일러에서 달라질 수 있다.
- 고치는 법 — 변환 전에 범위를 직접 검사하거나, `math.IsNaN`·`math.Round` 로 뜻을 분명히 한다.

비용 — 없음. **정확성의 비용**이 전부다.

### (7) 정수 나눗셈과 `%` — 부호와 0의 두 층

**언제 쓰나** — 나머지로 분기할 때(홀짝·해시 버킷·페이지 계산).

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

그림 해설 (한 단계씩):

- **몫은 0 쪽으로 버린다**(truncated division). `-5 / 3` = **−1**(−2가 아니다).
- **나머지의 부호는 피제수(왼쪽)를 따른다.** `-5 % 3` = **−2**, `5 % -3` = **2**.
- 마지막 두 줄이 대비다 — `-11 / 4` = **−2**(0 쪽), `-11 >> 2` = **−3**(음의 무한대 쪽).
  **`>> 1` 과 `/ 2` 는 음수에서 다르다.**

명세가 표까지 준다.

> For two integer values `x` and `y`, the integer quotient
> `q = x / y` and remainder `r = x % y` satisfy the following
> relationships: `x = q*y + r` and `|r| < |y|`, with `x / y` **truncated towards zero**.

> … `x >> 1` is the same as `x/2` but **truncated towards negative infinity**.

**0으로 나누면 — 상수와 변수가 갈린다.**

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

- 상수는 **컴파일 에러**다(03번 주제의 블록을 그대로 가져왔다).

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

- 변수는 **런타임 패닉**이다 — `panic: runtime error: integer divide by zero`, 종료 코드 **2**.
- 명세: "If the divisor is a constant, it must not be zero.
  **If the divisor is zero at run time, a run-time panic occurs.**"
- ★ 마커 줄은 **표준 오류로** 찍었다. 파이프로 받아도 자리가 안 바뀐다.

비용 — 나눗셈에는 **검사 분기가 붙는다**((8)절 어셈블리). 덧셈에는 안 붙는다.

### (8) `MinInt64 / -1` · 시프트 — 명세가 예외까지 적어 둔 자리

**언제 쓰나** — 절댓값·부호 뒤집기를 쓸 때.

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

그림 해설 (한 단계씩):

- `MinInt64 / -1` 이 **패닉하지 않고 `MinInt64` 를 그대로 돌려준다.** 나머지는 0.
- ★ **Rust 는 같은 식에서 패닉한다**(`attempt to divide with overflow`) —
  [`../../../rust/syntax/03-primitive-types-and-integer-overflow/`](../../../rust/syntax/03-primitive-types-and-integer-overflow/) (5)절과 대비된다.
- 명세가 이 한 자리를 **예외로 명시**한다.

  > The one exception to this rule is that if the dividend `x` is
  > the most negative value for the int type of `x`, the quotient
  > `q = x / -1` is equal to `x` (and `r = 0`)
  > due to two's-complement integer overflow

**시프트도 C 와 갈린다.**

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

- `int32(1) << 32`·`<< 99` 가 **0**이다. C 에서는 **미정의 동작**인 자리다.
  명세: "There is **no upper limit** on the shift count.
  Shifts behave as if the left operand is shifted n times by 1 …"
- 부호 있는 오른쪽 시프트는 **산술 시프트**(`-8 >> 1` = −4), 부호 없는 쪽은 **논리 시프트**.
  C 에서 구현 정의인 자리가 Go 에서는 **명세에 적혀 있다.**
- **시프트 횟수가 음수면 런타임 패닉**이다 — `panic: runtime error: negative shift amount`, 종료 코드 2.
  명세: "If the shift count is negative at run time, a run-time panic occurs."

비용 — 없음.

### (9) ★ 네 번째 창 — **폭과 이름을 따로 묻는다**

실행 출력·컴파일 진단·`go vet` 셋으로는 「왜 `int` 와 `int64` 가 다른가」가 안 보인다.
값도 같고 폭도 같은데 컴파일만 거부하기 때문이다. 그래서 이 주제는
**한 타입에게 `unsafe.Sizeof`(폭)와 `%T`(이름)를 따로 묻는 창**을 쓴다.

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

그림 해설 (한 단계씩):

- `int` 와 `int64` 는 **`Sizeof` 가 둘 다 8**이다. `unsafe.Sizeof(i) == unsafe.Sizeof(i64)` 가 **true**.
- 그런데 **`%T` 가 `int` 와 `int64` 로 다르다.** (2)절의 컴파일 에러가 이 한 칸에서 나온다.
- `math.MaxInt == int(math.MaxInt64)` 도 **true** — **값의 범위까지 같다.**
  그래도 안 섞인다. **이름이 다르기 때문**이다.
- **`rune` 의 `%T` 가 `int32`, `byte` 의 `%T` 가 `uint8`** 이다 — 이쪽은 진짜 **별칭**이라
  `%T` 가 답할 다른 이름이 없다. **별칭과 별개 타입의 차이**가 이 창에서만 보인다.

**이 창이 답하는 것** — 「같음」이 폭의 같음인가 이름의 같음인가.
Go 의 타입 검사는 **이름**을 본다.

★ 한 가지를 03번 주제의 창(`go tool compile -S`)에서 **빌려 온다** — 「검사가 붙는 연산과 안 붙는 연산」.

```text
===== 소스: t04l.go =====
package divs

// Add 는 더하기 하나만 한다.
func Add(a, b int64) int64 { return a + b }

// Div 는 나눗셈 하나만 한다.
func Div(a, b int64) int64 { return a / b }
===== 명령: go tool compile -S -trimpath "$PWD" -p divs t04l.go 2>&1 | grep -vE 'FUNCDATA|PCDATA|^\s+0x[0-9a-f]{4} [0-9a-f]{2} ' | sed '/^go:cuinfo/,$d' =====
divs.Add STEXT nosplit size=4 align=0x0 args=0x10 locals=0x0 funcid=0x0
	0x0000 00000 (t04l.go:4)	TEXT	divs.Add(SB), NOSPLIT|NOFRAME|ABIInternal, $0-16
	0x0000 00000 (t04l.go:4)	ADDQ	BX, AX
	0x0003 00003 (t04l.go:4)	RET
divs.Div STEXT nosplit size=38 align=0x0 args=0x10 locals=0x8 funcid=0x0
	0x0000 00000 (t04l.go:7)	TEXT	divs.Div(SB), NOSPLIT|ABIInternal, $8-16
	0x0000 00000 (t04l.go:7)	PUSHQ	BP
	0x0001 00001 (t04l.go:7)	MOVQ	SP, BP
	0x0004 00004 (t04l.go:7)	TESTQ	BX, BX
	0x0007 00007 (t04l.go:7)	JEQ	29
	0x0009 00009 (t04l.go:7)	CMPQ	BX, $-1
	0x000d 00013 (t04l.go:7)	JNE	22
	0x000f 00015 (t04l.go:7)	NEGQ	AX
	0x0012 00018 (t04l.go:7)	XORL	DX, DX
	0x0014 00020 (t04l.go:7)	JMP	27
	0x0016 00022 (t04l.go:7)	CQO
	0x0018 00024 (t04l.go:7)	IDIVQ	BX
	0x001b 00027 (t04l.go:7)	POPQ	BP
	0x001c 00028 (t04l.go:7)	RET
	0x001d 00029 (t04l.go:7)	NOP
	0x0020 00032 (t04l.go:7)	CALL	runtime.panicdivide(SB)
	0x0025 00037 (t04l.go:7)	XCHGL	AX, AX
	rel 33+4 t=R_CALL runtime.panicdivide+0
(exit 0)
===== 명령: rm -f t04l.o =====
(exit 0)
```

- `divs.Add` 는 **`ADDQ` 하나**다(`size=4`). **오버플로 검사가 없다** — (4)절의 명세가 코드로 보인다.
- `divs.Div` 는 **`size=38`** 이고 안에 둘이 들어 있다 —
  `TESTQ BX, BX` → `JEQ` → **`CALL runtime.panicdivide`**(0 나누기 검사)와,
  `CMPQ BX, $-1` → `NEGQ AX`((8)절의 `MinInt / -1` 예외를 코드로 처리하는 분기).
- 즉 **Go 가 넣은 검사는 나눗셈에만** 있고, 그 두 예외가 **어셈블리에 그대로 남아 있다.**

비용 — 어셈블리는 **아키텍처와 판**에 달렸다. 읽을 것은 **명령 이름과 분기의 유무**뿐이다.

## 문법 — 형태와 규칙

### 형태

```go
// t04form.go
package main

import "fmt"

func main() {
	var a int = 1
	var b int64 = int64(a) // ① 명시 변환은 의무
	c := a + 1             // ② 타입 없는 상수는 그냥 섞인다
	var v = 300
	d := uint8(v) // ③ 변수 변환 — 조용히 자른다
	e := 7 / 2    // ④ 정수 나눗셈
	f := 7 % -2   // ⑤ 나머지의 부호는 왼쪽을 따른다
	var one int32 = 1
	g := one << 40 // ⑥ 폭을 넘는 시프트는 0 (변수일 때)
	fmt.Println(a, b, c, d, e, f, g)
}
```

```text
===== 소스: t04form.go =====
package main

import "fmt"

func main() {
	var a int = 1
	var b int64 = int64(a) // ① 명시 변환은 의무
	c := a + 1             // ② 타입 없는 상수는 그냥 섞인다
	var v = 300
	d := uint8(v) // ③ 변수 변환 — 조용히 자른다
	e := 7 / 2    // ④ 정수 나눗셈
	f := 7 % -2   // ⑤ 나머지의 부호는 왼쪽을 따른다
	var one int32 = 1
	g := one << 40 // ⑥ 폭을 넘는 시프트는 0 (변수일 때)
	fmt.Println(a, b, c, d, e, f, g)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
1 1 2 44 3 1 0
(exit 0)
```

★ 이 파일에서 **한 줄이 처음 쓴 대로는 컴파일되지 않았다** — `g := int32(1) << 40` 으로 적었더니
`int32(1)` 이 **타입 있는 상수**라 상수 시프트가 되어 거부됐다. 변수로 바꿔야 0이 나온다.

```text
===== 소스: t04m.go =====
package main

import "fmt"

func main() {
	var one int32 = 1
	fmt.Println(one << 40)      // 변수 — 0
	fmt.Println(int32(1) << 40) // 상수 — ?
}
===== 명령: go build -trimpath -o prog . =====
# ex
./t04m.go:8:14: int32(1) << 40 (constant 1099511627776 of type int32) overflows int32
(exit 1)
```

규칙 불릿.

- **수치 타입 사이에는 자동 변환이 없다.** 유일한 예외가 **타입 없는 상수**다(03번 주제).
- `byte`·`rune` 은 **별칭**이라 `uint8`·`int32` 와 **완전히 같은 타입**이다.
- 연산 결과의 타입은 **피연산자의 타입**이다. 커지지 않는다.
- 시프트의 오른쪽은 **아무 정수 타입**이어도 되고 **상한이 없다**. 음수면 런타임 패닉이다.
- `/`·`%` 의 제수가 **상수 0이면 컴파일 에러**, **런타임 0이면 패닉**이다.

### 금지 사례 — 컴파일러가 거부하는 것

**① 타입이 다른 값끼리의 연산** — (2)절의 블록.

**② 상수가 타입에 안 담기는 것** — (5)절의 두 번째 블록.

**③ `go vet` 이 잡고 컴파일러는 안 잡는 것**

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

- **`go build` 는 통과**한다(종료 0). 프로그램도 잘 돈다.
- 그런데 **`go vet` 이 종료 1로 거부**한다 —
  `conversion from int to string yields a string of one rune, not a string of digits`.
- `string(65)` 은 **`"65"` 가 아니라 `"A"`** 다. 숫자를 문자열로 만들려면 `strconv.Itoa` 다.
- ★ 이것이 이 주제에서 **세 번째 창(`go vet`)이 컴파일러와 갈리는 자리**다.
  컴파일러는 「문법이 맞나」를, `go vet` 은 「뜻이 맞을 법한가」를 본다.
  `go test` 는 기본으로 vet 의 일부를 돌리므로 **테스트 단계에서 먼저 걸린다.**

## 어디서 틀리나

### 1. ★ 「릴리스에서는 다르겠지」라고 생각한다

- (4)절 실측 — **세 빌드가 한 글자도 같았다.** Go 에는 디버그/릴리스 구분이 **없다.**
- Rust 에서 온 직관이 여기서 뒤집힌다. Rust 는 **디버그에서 패닉**하지만 Go 는 **언제나 조용하다.**
- 그래서 **Go 의 오버플로는 테스트로 안 잡힌다.** 값을 직접 검사하는 수밖에 없다.

### 2. ★ 좁은 타입으로 계산하고 C 의 직관을 쓴다

- (3)절 실측 — `uint8` 200×200 은 **64**다. C 의 40000 이 아니다.
- 특히 체크섬·누산기에서 아프다. `uint8` 합계가 256을 넘는 순간 **조용히 감긴다.**
- 고치는 법 — **계산 전에 넓힌다**: `int(c) * int(c)`.

### 3. `int` 와 `int64` 사이에 변환을 흩뿌린다

- 에러가 나니 변환을 넣어 고치는데, **좁히는 방향**이면 (5)절대로 조용히 잘린다.
- 고치는 법 — **경계에서 한 번만 변환**하고 안쪽은 한 타입으로 통일한다.
  「넓히는 변환은 안전, 좁히는 변환은 검사 필요」로 나눠 읽는다.

### 4. 음수에서 `%` 의 부호를 잊는다

- (7)절 실측 — `-5 % 3` 은 **−2**다. `1` 이 아니다.
- 「짝수면 0」 같은 판정은 괜찮지만 **버킷 인덱스로 쓰면 음수 인덱스**가 나와 패닉한다.
- 고치는 법 — `((x % n) + n) % n` 또는 부호 없는 타입으로 옮긴다.

### 5. `/ 2` 와 `>> 1` 을 같은 것으로 본다

- (7)절 실측 — `-11 / 4` 는 **−2**, `-11 >> 2` 는 **−3**이다.
- 양수에서는 같아서 테스트가 통과하고, 음수 입력이 들어오는 순간 갈린다.

### 6. `string(n)` 으로 숫자를 문자열로 만든다

- (금지 사례 ③) — **컴파일은 되고 `go vet` 만 잡는다.** `string(65)` 은 `"A"` 다.
- 고치는 법 — `strconv.Itoa(n)`. 목록의 **11번 주제**가 정본이다.

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| 폭이 같아도 **다른 타입**, 변환은 의무 | **명세 보장** | "all numeric types are named types and thus distinct … Explicit conversions are required" |
| 연산 결과가 **피연산자의 타입** (승격 없음) | **명세 보장** | "yield a result of the same type as the first operand" |
| 부호 **없는** 오버플로 = 모듈로 2ⁿ | **명세 보장** | "computed modulo 2ⁿ … programs may rely on 'wrap around'" |
| 부호 **있는** 오버플로도 **결정적** | **명세 보장** | "the resulting value exists and is deterministically defined … Overflow does not cause a run-time panic." |
| 컴파일러가 「오버플로 없음」으로 최적화 **못 한다** | **명세 보장** | "A compiler may not optimize code under the assumption that overflow does not occur." |
| 정수→정수 변환의 **부호 확장 + 절단** | **명세 보장** | "sign extended … then truncated … there is no indication of overflow" |
| 나눗셈이 **0 쪽으로 버림** · `\|r\| < \|y\|` | **명세 보장** | "truncated towards zero" + 명세의 부호 표 |
| `MinInt / -1` 이 **`MinInt`** | **명세 보장** | "The one exception to this rule …" |
| `>>` 가 **음의 무한대 쪽** | **명세 보장** | "`x >> 1` is the same as `x/2` but truncated towards negative infinity" |
| 시프트 횟수에 **상한이 없다** | **명세 보장** | "There is no upper limit on the shift count." |
| 런타임 0나누기·음수 시프트가 **패닉** | **명세 보장** | "a run-time panic occurs" |
| 상수 0나누기·상수 오버플로가 **컴파일 에러** | **명세 보장** | 03번 주제의 인용들 |
| **`int`·`uint`·`uintptr` 의 폭** | **구현·플랫폼** | "either 32 or 64 bits" — 이 머신에서는 8바이트 |
| **범위 밖 부동소수 → 정수 변환의 값** | **구현** — 명세가 명시 | "the result value is implementation-dependent" |
| 세 빌드(`기본`·`-N -l`·`-race`)가 같은 것 | **이 판의 관찰** | (4)절 md5·diff. 다만 **명세가 갈릴 여지를 안 줬다** |
| `divs.Add` 에 검사가 없는 것 | **구현(gc)** | (9)절 어셈블리. 명세는 코드 생성을 약속하지 않는다 |
| `go vet` 의 `stringintconv` 검사 | **도구(go vet)** | 컴파일러는 통과시킨다 |

★ **구현에 맡겨진 칸이 정확히 둘**이라는 것이 이 주제의 결론이다 —
**`int` 의 폭**과 **범위 밖 부동소수 변환**. 나머지는 전부 명세가 값까지 정한다.
C 의 UB·구현 정의가 널린 자리(오버플로·시프트·부호 있는 오른쪽 시프트)가
Go 에서는 **전부 명세로 메워져 있다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 그냥 정수 | **`int`** | 관용이고 `len`·인덱스가 `int` 다 |
| 파일 크기·타임스탬프·외부 프로토콜 | **`int64`** 등 폭을 못 박은 타입 | 플랫폼이 바뀌어도 같아야 한다 |
| 바이트 데이터 | `byte`(= `uint8`) | 의도가 드러난다 |
| 유니코드 코드포인트 | `rune`(= `int32`) | 〃 (목록의 **10번 주제**) |
| 비트 연산·해시·체크섬 | 부호 **없는** 타입 | 랩어라운드에 **의존해도 된다**고 명세가 적었다 |
| 좁은 타입으로 누산 | **계산 전에 넓힌다** | 승격이 없어 거기서 감긴다 |
| 넓히는 변환 | `int64(x)` 그대로 | 값이 안 변한다 |
| 좁히는 변환 | **범위 검사 후** 변환 | 조용히 잘린다 — 알려 주는 수단이 없다 |
| 부동소수 → 정수 | 범위 검사 + `math.Round` 등 | 범위 밖은 **구현 의존** |
| 숫자를 문자열로 | **`strconv.Itoa`** | `string(n)` 은 룬 변환이다 |
| 음수 나머지를 인덱스로 | `((x % n) + n) % n` | `%` 는 왼쪽 부호를 따른다 |

판단 규칙 두 줄.

- **좁히는 변환에는 근거를 남겨라.** Go 는 절대 알려 주지 않는다.
- **「테스트가 통과했다」는 오버플로의 근거가 못 된다.** 패닉이 없는 언어이기 때문이다.

## 핵심 문장

- Go 의 수치 타입은 **폭이 같아도 다른 타입**이다. 명세가 "named types and thus distinct" 라고 적었다.
- **승격이 없다.** `uint8` 200×200 은 **64**다 — C 는 같은 코드에서 40000 을 준다.
- **오버플로는 조용히 감싸고, 그것이 언어의 약속**이다. 세 빌드가 한 글자도 같았다 —
  Rust 처럼 「디버그에서는 패닉」이 없다.
- 그 대가로 **경보가 없다.** 「안 터졌다」가 「안 넘쳤다」가 아니다.
- 좁히는 변환은 **부호 확장 후 절단**이고 **넘침을 알려 주는 수단이 없다**(명세 원문).
- `/` 는 **0 쪽으로** 버리고 `%` 는 **왼쪽의 부호**를 따른다. `>>` 는 **음의 무한대 쪽**이라 `/` 와 다르다.
- **`MinInt / -1` 은 패닉이 아니라 `MinInt`** 다 — 명세가 예외로 적어 둔 유일한 자리다.
- 구현에 맡겨진 칸은 **둘뿐**이다 — `int` 의 폭, 범위 밖 부동소수 → 정수 변환의 값.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 04번)
- [03번 주제](../03-constants-iota-and-untyped-constants/)(상수·타입 없는 상수) —
  **상수는 컴파일 에러, 변수는 런타임**. 그 대비의 반대쪽이 거기다. `i + 1` 이 왜 통과하는지도 거기
- [02번 주제](../02-variable-declarations-and-zero-values/)(변수 선언·제로값) —
  `var c int64 = 42` 는 되고 `var c int64 = i` 는 안 되는 이유의 앞쪽 절반
- [`../../../c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/`](../../../c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/) —
  **그쪽은 승격이 있어 `unsigned char` 끼리 곱해도 40000**, 여기는 **승격이 없어 64**다.
  같은 코드의 두 답을 나란히 읽어라
- [`../../../rust/syntax/03-primitive-types-and-integer-overflow/`](../../../rust/syntax/03-primitive-types-and-integer-overflow/) —
  **그쪽은 디버그에서 패닉·릴리스에서 랩어라운드이고 뒤엣것이 구현 재량**,
  여기는 **빌드와 무관하게 랩어라운드이고 그것이 명세**다
- [`../../../../data-representation/`](../../../../data-representation/) —
  **그쪽은 2의 보수·IEEE 754 라는 표현 자체**까지, **여기는 Go 의 변환·오버플로 규칙**부터다
- 목록의 **10번 주제**(문자열·`byte`·`rune`) — `string(n)` 이 룬 변환인 것의 정본
- 목록의 **11번 주제**(`strconv`) — 숫자↔문자열 변환의 정본
- 목록의 **17번 주제**(구조체 정렬) — `unsafe.Sizeof` 를 제대로 다루는 자리
- 목록의 **52번 주제**(도구) — `go vet`·`go tool compile -S` 의 정본

## 용어 풀이

- **승격(integer promotion)** — 좁은 정수를 연산 전에 `int` 로 올리는 C 의 규칙. **Go 에는 없다.**
- **랩어라운드(wrap-around)** — 범위를 넘으면 반대쪽 끝에서 다시 세는 것. 2의 보수로 정의된다.
- **명시 변환(explicit conversion)** — `T(x)` 꼴. Go 의 수치 타입 사이에서는 의무다.
- **부호 확장(sign extension)** — 좁은 부호 있는 값을 넓힐 때 최상위 비트로 위쪽을 채우는 것.
- **영 확장(zero extension)** — 부호 없는 값을 넓힐 때 위쪽을 0으로 채우는 것.
- **절단(truncation)** — 넓은 값을 좁은 타입에 넣을 때 위쪽 비트를 버리는 것.
- **0 쪽 버림(truncated division)** — 몫의 소수부를 버려 0에 가까워지는 나눗셈. Go 의 `/` 다.
- **산술 시프트(arithmetic shift)** — 부호 비트를 유지하며 오른쪽으로 미는 것. 부호 있는 타입의 `>>`.
- **논리 시프트(logical shift)** — 위쪽을 0으로 채우며 미는 것. 부호 없는 타입의 `>>`.
- **별칭(alias)** — 같은 타입의 다른 이름. `byte` = `uint8`, `rune` = `int32`.
- **`go vet`** — 컴파일은 통과하지만 뜻이 의심스러운 코드를 잡는 도구. `go test` 가 일부를 자동으로 돌린다.
- **미정의 동작(UB)** — C 에서 「무슨 일이 일어나도 규격 위반이 아닌」 상태. **Go 에는 이 개념이 없다.**

---

## 더 들어가면

- 명세의 「A compiler may not optimize code under the assumption that overflow does not occur」는
  **C 와의 가장 큰 차이**다. C 에서는 `x < x + 1` 을 항상 참으로 접어 버리는 최적화가 합법이고,
  그것이 실제 보안 사고를 냈다. Go 에서는 금지다.
- `uintptr` 은 정수라서 **GC 가 추적하지 않는다.** 포인터를 `uintptr` 에 담아 두면 대상이 회수될 수 있다.
  이 주제에서는 폭만 봤다(8바이트).
- `float32` 로 계산한 중간값이 **더 높은 정밀도로 유지될 수 있다**고 명세가 허용한다.
  `float32(x + 0.1)` 처럼 **명시 변환을 적으면** 그 지점에서 32비트로 반올림된다.
- 명세는 **FMA(융합 곱셈-덧셈)** 를 허용하고, 어디서 허용/금지되는지 예제로 적어 둔다.
  `r = x*y + z` 는 융합이 허용되고 `r = float64(x*y) + z` 는 금지다. 이 문서에서는 **재지 않았다.**
- 부동소수의 **0으로 나누기**는 정수와 다르다 — 명세: "The result of a floating-point or complex
  division by zero is not specified beyond the IEEE 754 standard;
  whether a run-time panic occurs is **implementation-specific**." 이 문서에서는 **안 던져 봤다.**
- `go vet` 의 `stringintconv` 는 **`go test` 가 기본으로 돌리는 검사 묶음**에 들어 있다.
  그래서 테스트가 있는 프로젝트에서는 빌드보다 먼저 걸린다.

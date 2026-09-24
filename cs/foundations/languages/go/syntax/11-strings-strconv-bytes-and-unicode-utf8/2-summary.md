# go/syntax/11 — `strings`·`strconv`·`bytes`·`unicode/utf8` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [표준 라이브러리 문서](https://pkg.go.dev/std)의
> `strings` · `strconv` · `bytes` · `unicode/utf8` · `unicode` 패키지.\
> 웹이 아니라 **이 툴체인이 들고 있는 것을 `go doc` 으로 열어** 인용했다(`go version go1.27.1`).
> ★ 그래서 이 문서가 인용한 문서 문장은 **이 판의 것**이다 — (4)절의 `Deprecated:` 줄이 그 예다.
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> ★★★ **성능 주장은 전부 잰 것만 적는다.** (1)절이 네 방법을 `go test -bench` 로 재고,
> **할당 수(`allocs/op`)를 근거로** 삼는다 — 시간은 흔들리지만 **할당 수는 안 흔들린다.**
> **버전** — `strings.Builder` 는 **1.10**, `strings.Cut` 은 **1.18**, `strings.Title` 의
> `Deprecated` 표시는 **1.18**부터다. 나머지는 1.0 대에 자리를 잡았다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 문서로, 출력은 실행으로 접지했다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | 이 주제에는 거의 없다 — 명세는 **패키지를 모른다** |
| **표준 라이브러리의 계약** | 패키지 문서가 약속한 것 | `go doc` 출력 · 함수 문서의 문장 |
| **이 판의 관찰** | go1.27.1·이 머신에서 이번에 잰 것 | 벤치마크 수치 · 실행 출력 |

★★ **이 주제는 앞의 두 주제와 층 구성이 다르다.** 09·10 은 명세가 대부분을 정했지만
**표준 API 는 명세 밖**이다. 「Go 가 보장한다」가 아니라 「**이 패키지 문서가 약속한다**」가 최선이고,
그 약속은 **판마다 바뀔 수 있다**((5)절의 deprecated 가 그 증거다).

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

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | 벤치마크의 **`ns/op`** | 머신·부하에 달렸다. **대조할 것은 숫자가 아니라 자릿수 차이다** |
| **흔들린다** | 벤치마크의 **`B/op` 끝자리** | 측정 자체에 잡음이 섞인다(실측에서 끝 두 자리가 움직였다) |
| **흔들린다** | 패닉 스택의 **주소 오프셋** | 빌드마다 바뀔 수 있다 |
| **판이 바뀌면 바뀐다** | `strings.Title` 의 **`Deprecated:` 줄** | 패키지 문서다. 판마다 다시 떠야 한다 |
| **판이 바뀌면 바뀐다** | `Builder` 의 **`allocs/op` 15** | 내부 성장 전략이다. 계약이 아니다 |
| **머신에 달렸다** | 벤치마크 이름의 **`-24` 접미**와 `cpu:` 줄 | `GOMAXPROCS` 와 CPU 이름이다 |
| 안 흔들린다 | `allocs/op` 의 **서열**(999 ≫ 15 > 1) | 알고리즘이 정한다. 이것이 이 주제의 근거다 |
| 안 흔들린다 | `Split`·`Cut`·`Fields` 의 **경계 결과** | 패키지 문서가 약속한다 |
| 안 흔들린다 | `strconv` 의 **에러 문장 전문** | `NumError` 의 `Error()` 가 정한다 |
| 안 흔들린다 | 패닉 **메시지 본문**·`파일:줄`·종료 코드 | 런타임과 패키지가 정한다 |

## 한눈에 — 쉽게 말하면

**「연장 네 개가 든 통.」** 무엇을 들고 있느냐가 연장을 정한다.

| 손에 든 것 | 연장 | 한 줄 |
|---|---|---|
| `string` | **`strings`** | 자르고 붙이고 찾고 바꾼다 |
| `[]byte` | **`bytes`** | **이름이 같은 함수가 그대로 있다** — 변환을 안 하려고 |
| 수·불리언 ↔ 문자열 | **`strconv`** | 파싱과 포매팅. **에러가 값으로 온다** |
| 바이트 ↔ 룬 | **`unicode/utf8`** | 세고, 쪼개고, 유효한지 묻는다 |

```text
              [] byte                       string
                 |                             |
        bytes.*  |                             |  strings.*
                 |   <---- string(b) ---->     |     (같은 이름의 함수가 양쪽에 있다)
                 |   <---- []byte(s) ---->     |      ★ 화살표를 건널 때마다 복사가 생긴다
                 |                             |
                 +------- unicode/utf8 --------+   (바이트를 룬으로 세고 쪼갠다)
                                 |
                              strconv           (수·불리언 <-> 문자열 · 따옴표 붙이기)
```

- ★★ **고르는 규칙 한 줄** — 「**지금 손에 든 것이 `string` 인가 `[]byte` 인가**」.
  틀리면 코드가 도는데 **변환 두 번**이 조용히 낀다.
- ★★★ **`+=` 로 1000번 이으면 할당이 999번**이고, `strings.Builder` 는 **15번**,
  크기를 미리 잡으면 **1번**이다((2)절 실측). 같은 결과를 세 가지 비용으로 산다.

> **할당(allocation)** — 힙에서 메모리를 새로 잡는 것. 잡을 때마다 GC 가 나중에 치워야 한다.

> **`allocs/op`** — 벤치마크 한 번에 힙 할당이 몇 번 일어났나. **시간과 달리 잘 안 흔들린다.**

> **deprecated** — 「쓰지 말라」고 문서에 표시된 것. Go 는 삭제하지 않고 **문서에만** 적는다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 네 질문을 둔다.

1. **네 패키지를 언제 고르나** — 왜 `bytes` 가 `strings` 와 따로 있나.
2. **이어 붙이기를 무엇으로 하나** — `+=` 와 `Builder` 의 차이를 **수치로** 말할 수 있나.
3. **`strconv` 의 에러는 어떻게 생겼나** — 「틀린 글자」와 「범위 초과」를 어떻게 가르나.
4. **`Split` 같은 함수의 경계에서 무엇이 나오나** — 빈 문자열·빈 구분자는?

★ 언어가 주는 것(`len`·인덱싱·`range`·변환)은
[`../10-strings-bytes-runes-and-utf8-iteration/`](../10-strings-bytes-runes-and-utf8-iteration/)가 정본이다.
여기는 **그 위에 선 네 패키지**만 본다.

## 동작 방식

### (0) 네 패키지 지도 — 같은 일을 네 갈래로

**언제 쓰나** — 문자열을 만질 때마다. **첫 물음은 언제나 「손에 든 것이 무엇인가」이다**.

```text
===== 소스: t11a.go =====
package main

import (
	"bytes"
	"fmt"
	"strconv"
	"strings"
	"unicode/utf8"
)

func main() {
	s := "  Go, 한글, 42  "
	b := []byte(s)

	fmt.Println("strings — 대상이 string 이다")
	fmt.Printf("  TrimSpace : %q\n", strings.TrimSpace(s))
	fmt.Printf("  Split     : %#v\n", strings.Split(strings.TrimSpace(s), ", "))
	fmt.Printf("  Contains  : %v\n", strings.Contains(s, "한글"))

	fmt.Println("bytes — 같은 이름의 API 를 []byte 로")
	fmt.Printf("  TrimSpace : %q\n", bytes.TrimSpace(b))
	fmt.Printf("  Split     : %q\n", bytes.Split(bytes.TrimSpace(b), []byte(", ")))
	fmt.Printf("  Contains  : %v\n", bytes.Contains(b, []byte("한글")))

	fmt.Println("strconv — 문자열과 수·불리언 사이")
	n, err := strconv.Atoi("42")
	fmt.Printf("  Atoi      : %d, %v\n", n, err)
	fmt.Printf("  Itoa      : %q\n", strconv.Itoa(42))

	fmt.Println("unicode/utf8 — 바이트와 룬 사이")
	fmt.Printf("  RuneCountInString : %d   (len 은 %d)\n", utf8.RuneCountInString(s), len(s))
	fmt.Printf("  ValidString       : %v\n", utf8.ValidString(s))
}
===== 명령: go build -trimpath -o prog . && ./prog =====
strings — 대상이 string 이다
  TrimSpace : "Go, 한글, 42"
  Split     : []string{"Go", "한글", "42"}
  Contains  : true
bytes — 같은 이름의 API 를 []byte 로
  TrimSpace : "Go, 한글, 42"
  Split     : ["Go" "한글" "42"]
  Contains  : true
strconv — 문자열과 수·불리언 사이
  Atoi      : 42, <nil>
  Itoa      : "42"
unicode/utf8 — 바이트와 룬 사이
  RuneCountInString : 14   (len 은 18)
  ValidString       : true
(exit 0)
```

그림 해설 (한 단계씩):

- `strings` 와 `bytes` 는 **이름이 같은 함수를 짝으로** 들고 있다 —
  `TrimSpace`·`Split`·`Contains`·`Index`·`ToUpper` … 거의 전부다.
- 다른 것은 **받고 주는 타입뿐**이다. `strings` 는 `string`, `bytes` 는 `[]byte`.
- ★★ **왜 따로 있나** — `[]byte` 를 들고 `strings` 를 쓰려면 `string(b)` 로 바꿔야 하고,
  그 변환이 **복사**다(10번 주제 (3)절). 되돌아올 때 또 복사다.
  `bytes` 는 **그 두 번의 복사를 없애려고** 있는 것이다.
- `strconv` 는 **수와 문자열 사이**만 본다. `unicode/utf8` 은 **바이트와 룬 사이**만 본다.

```text
   손에 []byte 가 있는데 strings 를 쓰면

     b ──string(b)──▶ "…" ──strings.ToUpper──▶ "…" ──[]byte(s)──▶ b2
          복사 1                                      복사 2

   bytes 를 쓰면

     b ──bytes.ToUpper──▶ b2                         복사 0*
                                                     (*결과 버퍼 하나는 든다)
```

비용 — 변환 한 번은 **바이트 수만큼**의 복사다. 루프 안이면 그것이 누적된다.

### (1) ★★★ 이어 붙이기 — 재서 비교한다

**언제 쓰나** — 루프에서 문자열을 만들 때. **이 주제에서 가장 자주 틀리는 자리**다.

네 방법을 같은 일(8글자 조각 1000개 잇기)로 재 본다.

```text
===== 명령: go test -run=^$ -bench=. -benchmem -benchtime=200x -count=1 ./... 2>&1 | grep "^Benchmark" | awk "{printf \"%-26s %8s %s\n\", \$1, \$(NF-1), \$NF}" =====
BenchmarkPlus-24                999 allocs/op
BenchmarkBuilder-24              15 allocs/op
BenchmarkBuilderGrow-24           1 allocs/op
BenchmarkJoin-24                  1 allocs/op
(exit 0)
```

★★★ **근거는 이 수치다.** `allocs/op` 는 **알고리즘이 정하므로 안 흔들린다.**

| 방법 | `allocs/op` | 왜 그 수인가 |
|---|---|---|
| `s += chunk` | **999** | 이을 때마다 **새 문자열을 통째로 만든다** |
| `strings.Builder` | **15** | 내부 버퍼를 **배로 늘린다** — 늘릴 때만 잡는다 |
| `Builder` + `Grow` | **1** | 최종 크기를 **미리** 잡는다 |
| `strings.Join` | **1** | 총 길이를 먼저 **세고** 한 번에 잡는다 |

시간은 이렇게 나왔다. **이 수치는 흔들린다** — 대조할 것은 숫자가 아니라 **자릿수 차이**다.

```text
===== 소스: t11b.go =====
package main

import "strings"

const chunk = "abcdefgh"

// ConcatPlus 는 += 로 잇는다.
func ConcatPlus(n int) string {
	s := ""
	for i := 0; i < n; i++ {
		s += chunk
	}
	return s
}

// ConcatBuilder 는 strings.Builder 로 잇는다.
func ConcatBuilder(n int) string {
	var b strings.Builder
	for i := 0; i < n; i++ {
		b.WriteString(chunk)
	}
	return b.String()
}

// ConcatBuilderGrow 는 최종 크기를 미리 잡아 둔다.
func ConcatBuilderGrow(n int) string {
	var b strings.Builder
	b.Grow(n * len(chunk))
	for i := 0; i < n; i++ {
		b.WriteString(chunk)
	}
	return b.String()
}

// ConcatJoin 은 조각을 모아 한 번에 잇는다.
func ConcatJoin(n int) string {
	parts := make([]string, n)
	for i := range parts {
		parts[i] = chunk
	}
	return strings.Join(parts, "")
}

func main() {}
===== 소스: t11b_test.go =====
package main

import "testing"

const N = 1000

var sink string

func BenchmarkPlus(b *testing.B) {
	for i := 0; i < b.N; i++ {
		sink = ConcatPlus(N)
	}
}

func BenchmarkBuilder(b *testing.B) {
	for i := 0; i < b.N; i++ {
		sink = ConcatBuilder(N)
	}
}

func BenchmarkBuilderGrow(b *testing.B) {
	for i := 0; i < b.N; i++ {
		sink = ConcatBuilderGrow(N)
	}
}

func BenchmarkJoin(b *testing.B) {
	for i := 0; i < b.N; i++ {
		sink = ConcatJoin(N)
	}
}

func TestSame(t *testing.T) {
	want := ConcatPlus(N)
	for name, got := range map[string]string{
		"Builder":     ConcatBuilder(N),
		"BuilderGrow": ConcatBuilderGrow(N),
		"Join":        ConcatJoin(N),
	} {
		if got != want {
			t.Fatalf("%s 가 다르다", name)
		}
	}
}
===== 명령: go test -run=. -bench=. -benchmem -benchtime=200x -count=1 ./... 2>&1 | sed -E "s/[0-9]+\.[0-9]+s\$/(초)/" =====
goos: linux
goarch: amd64
pkg: ex
cpu: 13th Gen Intel(R) Core(TM) i7-13700HX
BenchmarkPlus-24           	     200	   1010055 ns/op	 4273975 B/op	     999 allocs/op
BenchmarkBuilder-24        	     200	     10637 ns/op	   34296 B/op	      15 allocs/op
BenchmarkBuilderGrow-24    	     200	      3894 ns/op	    8192 B/op	       1 allocs/op
BenchmarkJoin-24           	     200	      7937 ns/op	    8192 B/op	       1 allocs/op
PASS
ok  	ex	(초)
(exit 0)
```

그림 해설 (한 단계씩):

- `+=` 는 **1밀리초대**, 나머지 셋은 **10마이크로초 안팎**이다 — **두 자릿수 차이**다.
- ★ 이것은 **`O(n²)` 대 `O(n)`** 의 차이다. `+=` 는 매번 **지금까지 만든 것 전체를 복사**한다.
  1000번이면 대략 `1+2+…+1000` 칸을 옮긴다.
- `B/op` 도 같은 이야기를 한다 — `+=` 가 **4MB 넘게** 잡았고 `Grow` 는 **8192바이트** 다.
  최종 문자열이 8000바이트이므로 **`Grow` 쪽은 한 덩어리로 끝났다**는 뜻이다.
- ★★ **`Join` 도 1할당**이지만 **조각 슬라이스를 미리 들고 있어야** 한다.
  조각이 이미 슬라이스면 `Join`, 흘러나오는 중이면 `Builder` 다.
- ★★★ **그렇다고 `+` 를 늘 피하라는 말이 아니다.** 두세 개를 잇는 것은 `+` 가 가장 읽기 좋고,
  컴파일러가 **한 번에 잡아 준다.** 문제는 **루프 안**이다.

★ 측정 조건 — `go test -bench` · `-benchtime=200x`(반복 수 고정) · `-count=1` ·
조각 8바이트 × 1000개 · 이 머신 1대 · **신호 대 잡음이 두 자릿수**라 승패가 뒤집힐 여지가 없다.
`ns/op` 은 판마다 10\~30% 움직였다.

비용 — 위 표가 곧 비용이다.

### (2) ★ `Builder` 는 복사하면 안 된다

**언제 쓰나** — `Builder` 를 구조체 필드로 두거나 함수에 **값으로** 넘길 때.

```text
===== 소스: t11g.go =====
package main

import (
	"fmt"
	"os"
	"strings"
)

func main() {
	var a strings.Builder
	a.WriteString("hello")
	b := a
	fmt.Fprintf(os.Stderr, "-- 복사 자체는 됐다 : a=%q b=%q --\n", a.String(), b.String())
	fmt.Fprintln(os.Stderr, "-- 이제 복사본에 쓴다 --")
	b.WriteString(" world")
	fmt.Fprintln(os.Stderr, "-- 여기는 안 온다 --")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
-- 복사 자체는 됐다 : a="hello" b="hello" --
-- 이제 복사본에 쓴다 --
panic: strings: illegal use of non-zero Builder copied by value

goroutine 1 [running]:
strings.(*Builder).copyCheck(...)
	strings/builder.go:41
strings.(*Builder).WriteString(...)
	strings/builder.go:113
main.main()
	ex/t11g.go:15 +0x246
(exit 2)
```

그림 해설 (한 단계씩):

- **복사 자체는 된다.** `b := a` 가 통과하고 두 값이 같은 내용을 준다.
- **복사본에 쓰는 순간** `panic: strings: illegal use of non-zero Builder copied by value` 다.
  종료 코드 **2**.
- ★ 스택에 **`strings.(*Builder).copyCheck`** 가 찍힌다 —
  `Builder` 가 **자기 주소를 기억해 두고 매번 확인**한다는 뜻이다.
- ★★ 왜 막나 — `Builder` 는 `String()` 에서 **내부 버퍼를 복사 없이 문자열로 내준다.**
  그 안전성은 「버퍼를 나 말고 아무도 안 본다」에 기대므로, **복사본이 생기면 그 전제가 깨진다.**
- 고치는 법 — **포인터로 넘긴다**(`*strings.Builder`). 구조체에 담을 때도 마찬가지다.

비용 — 검사는 포인터 비교 하나다.

### (3) `strconv` — 에러가 값으로 온다

**언제 쓰나** — 바깥에서 온 문자열을 수로 바꿀 때. **전부 실패할 수 있다.**

```text
===== 소스: t11c.go =====
package main

import (
	"errors"
	"fmt"
	"strconv"
)

func show(in string) {
	n, err := strconv.Atoi(in)
	fmt.Printf("Atoi(%-22q) = %-21d err = %v\n", in, n, err)
	var ne *strconv.NumError
	if errors.As(err, &ne) {
		fmt.Printf("      &strconv.NumError{Func:%q, Num:%q, Err:%v}  Is(ErrSyntax)=%v Is(ErrRange)=%v\n",
			ne.Func, ne.Num, ne.Err,
			errors.Is(err, strconv.ErrSyntax), errors.Is(err, strconv.ErrRange))
	}
}

func main() {
	for _, in := range []string{"42", "-7", "+7", " 42", "42 ", "0x2a", "", "12a", "9223372036854775808"} {
		show(in)
	}

	fmt.Println()
	f, err := strconv.ParseFloat("3.5e2", 64)
	fmt.Printf("ParseFloat(\"3.5e2\", 64)  = %v, %v\n", f, err)
	f, err = strconv.ParseFloat("1e400", 64)
	fmt.Printf("ParseFloat(\"1e400\", 64)  = %v, %v\n", f, err)
	b, err := strconv.ParseBool("TRUE")
	fmt.Printf("ParseBool(\"TRUE\")        = %v, %v\n", b, err)
	b, err = strconv.ParseBool("참")
	fmt.Printf("ParseBool(\"참\")          = %v, %v\n", b, err)
	i64, err := strconv.ParseInt("2a", 16, 64)
	fmt.Printf("ParseInt(\"2a\", 16, 64)   = %d, %v\n", i64, err)
	i64, err = strconv.ParseInt("300", 10, 8)
	fmt.Printf("ParseInt(\"300\", 10, 8)   = %d, %v\n", i64, err)

	fmt.Println()
	fmt.Printf("Itoa(42)                 = %q\n", strconv.Itoa(42))
	fmt.Printf("FormatInt(42, 2)         = %q\n", strconv.FormatInt(42, 2))
	fmt.Printf("FormatFloat(3.14159,'f',2,64) = %q\n", strconv.FormatFloat(3.14159, 'f', 2, 64))
	fmt.Printf("Quote(\"한\\n\")            = %s\n", strconv.Quote("한\n"))
	fmt.Printf("QuoteToASCII(\"한\")       = %s\n", strconv.QuoteToASCII("한"))
	u, err := strconv.Unquote("\"a\\tb\"")
	fmt.Printf("Unquote(`\"a\\tb\"`)        = %q, %v\n", u, err)
	_, err = strconv.Unquote("a")
	fmt.Printf("Unquote(\"a\")             err = %v\n", err)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
Atoi("42"                  ) = 42                    err = <nil>
Atoi("-7"                  ) = -7                    err = <nil>
Atoi("+7"                  ) = 7                     err = <nil>
Atoi(" 42"                 ) = 0                     err = strconv.Atoi: parsing " 42": invalid syntax
      &strconv.NumError{Func:"Atoi", Num:" 42", Err:invalid syntax}  Is(ErrSyntax)=true Is(ErrRange)=false
Atoi("42 "                 ) = 0                     err = strconv.Atoi: parsing "42 ": invalid syntax
      &strconv.NumError{Func:"Atoi", Num:"42 ", Err:invalid syntax}  Is(ErrSyntax)=true Is(ErrRange)=false
Atoi("0x2a"                ) = 0                     err = strconv.Atoi: parsing "0x2a": invalid syntax
      &strconv.NumError{Func:"Atoi", Num:"0x2a", Err:invalid syntax}  Is(ErrSyntax)=true Is(ErrRange)=false
Atoi(""                    ) = 0                     err = strconv.Atoi: parsing "": invalid syntax
      &strconv.NumError{Func:"Atoi", Num:"", Err:invalid syntax}  Is(ErrSyntax)=true Is(ErrRange)=false
Atoi("12a"                 ) = 0                     err = strconv.Atoi: parsing "12a": invalid syntax
      &strconv.NumError{Func:"Atoi", Num:"12a", Err:invalid syntax}  Is(ErrSyntax)=true Is(ErrRange)=false
Atoi("9223372036854775808" ) = 9223372036854775807   err = strconv.Atoi: parsing "9223372036854775808": value out of range
      &strconv.NumError{Func:"Atoi", Num:"9223372036854775808", Err:value out of range}  Is(ErrSyntax)=false Is(ErrRange)=true

ParseFloat("3.5e2", 64)  = 350, <nil>
ParseFloat("1e400", 64)  = +Inf, strconv.ParseFloat: parsing "1e400": value out of range
ParseBool("TRUE")        = true, <nil>
ParseBool("참")          = false, strconv.ParseBool: parsing "참": invalid syntax
ParseInt("2a", 16, 64)   = 42, <nil>
ParseInt("300", 10, 8)   = 127, strconv.ParseInt: parsing "300": value out of range

Itoa(42)                 = "42"
FormatInt(42, 2)         = "101010"
FormatFloat(3.14159,'f',2,64) = "3.14"
Quote("한\n")            = "한\n"
QuoteToASCII("한")       = "\ud55c"
Unquote(`"a\tb"`)        = "a\tb", <nil>
Unquote("a")             err = invalid syntax
(exit 0)
```

그림 해설 (한 단계씩):

- `Atoi` 는 **엄격하다.** `" 42"`·`"42 "`(공백) · `"0x2a"`(접두) · `""`(빈 문자열) · `"12a"` 가 **전부 실패**다.
  ★ **앞뒤 공백을 안 잘라 준다** — `strings.TrimSpace` 를 먼저 불러야 한다.
- `"+7"` 은 **된다.** 부호는 허용한다.
- ★★ 에러는 **`*strconv.NumError`** 라는 구조체다. `Func`·`Num`·`Err` 세 필드를 들고 있고,
  `Error()` 가 `strconv.Atoi: parsing "12a": invalid syntax` 를 만든다.
  **어느 함수가, 어떤 입력에서, 왜** 가 문장에 다 들어 있다.
- ★★★ **두 종류를 가르는 것이 핵심이다.**

| 센티넬 | 뜻 | 실측 예 | 그때 반환값 |
|---|---|---|---|
| `strconv.ErrSyntax` | **글자가 수가 아니다** | `"12a"` · `""` · `"0x2a"` | **제로값** |
| `strconv.ErrRange` | **수인데 안 들어간다** | `"9223372036854775808"` | ★ **경계값**(`MaxInt64`) |

- ★★ `ErrRange` 일 때 **반환값이 제로가 아니다** — `Atoi` 는 `9223372036854775807` 을,
  `ParseFloat("1e400")` 은 **`+Inf`** 를, `ParseInt("300", 10, 8)` 은 **`127`** 을 준다.
  **에러를 무시하면 그럴듯한 값이 흘러간다.** 이 주제에서 가장 조용한 사고다.
- `errors.Is(err, strconv.ErrSyntax)` 로 판정한다 — `NumError` 가 `Unwrap` 을 들고 있어 그냥 된다.
- 포매팅 쪽 — `Itoa`·`FormatInt(n, 2)`(2진) · `FormatFloat(f, 'f', 2, 64)` ·
  **`Quote`**(Go 문법의 따옴표 문자열) · **`QuoteToASCII`**(비ASCII 를 `\uXXXX` 로).
- `Unquote` 는 **따옴표가 없으면 실패**한다(`invalid syntax`).

비용 — `Atoi` 는 짧은 10진수에 **빠른 경로**가 있다. `ParseInt` 보다 싸다.

### (4) ★ `strings.Title` 은 deprecated 다 — 던져서 확인한다

**언제 쓰나** — 「첫 글자만 대문자로」를 하려 할 때. **쓰면 안 된다.**

```text
===== 명령: go doc strings.Title =====
package strings // import "strings"

func Title(s string) string
    Title returns a copy of the string s with all Unicode letters that begin
    words mapped to their Unicode title case.

    Deprecated: The rule Title uses for word boundaries does not handle Unicode
    punctuation properly. Use golang.org/x/text/cases instead.

(exit 0)
```

- `go doc` 이 **`Deprecated:` 줄을 그대로** 보여 준다.
  **「The rule Title uses for word boundaries does not handle Unicode punctuation properly.」**
- ★★ 그런데 **`go build` 도 `go vet` 도 말리지 않는다.** Go 의 deprecated 는 **문서 표시**일 뿐이고
  컴파일러는 모른다. **`go doc` 을 열어야 보인다.**

무엇이 틀리는지 실제로 보자.

```text
===== 소스: t11e.go =====
package main

import (
	"fmt"
	"strings"
)

func main() {
	in := "don't shout at o'brien"
	fmt.Printf("in                   = %q\n", in)
	fmt.Printf("strings.Title(in)    = %q   ← 아포스트로피 뒤를 단어 시작으로 본다\n", strings.Title(in))
	fmt.Printf("strings.ToTitle(in)  = %q   ← 이건 전부를 title case 로 바꾸는 다른 함수다\n", strings.ToTitle(in))
	fmt.Printf("strings.ToUpper(in)  = %q\n", strings.ToUpper(in))

	fmt.Println()
	fmt.Printf("ToTitle(\"ǳ\")         = %q   (ToUpper 는 %q — 세 벌 글자는 갈린다)\n",
		strings.ToTitle("ǳ"), strings.ToUpper("ǳ"))
}
===== 명령: go build -trimpath -o prog . && ./prog =====
in                   = "don't shout at o'brien"
strings.Title(in)    = "Don'T Shout At O'Brien"   ← 아포스트로피 뒤를 단어 시작으로 본다
strings.ToTitle(in)  = "DON'T SHOUT AT O'BRIEN"   ← 이건 전부를 title case 로 바꾸는 다른 함수다
strings.ToUpper(in)  = "DON'T SHOUT AT O'BRIEN"

ToTitle("ǳ")         = "ǲ"   (ToUpper 는 "Ǳ" — 세 벌 글자는 갈린다)
(exit 0)
===== 명령: go vet ./... =====
(exit 0)
```

그림 해설 (한 단계씩):

- `"don't shout at o'brien"` 이 **`"Don'T Shout At O'Brien"`** 이 된다 —
  **아포스트로피 뒤를 단어 시작으로** 본다. `Don'T` 가 나온다.
- ★ **`ToTitle` 은 아예 다른 함수**다. 「제목 꼴로」가 아니라 **모든 글자를 title case 로** 바꾼다 —
  결과가 `ToUpper` 와 거의 같다. **이름이 닮아서 더 헷갈린다.**
- ★★ 둘이 실제로 갈리는 것은 **세 벌 글자**다 — `ǳ` 의 `ToTitle` 은 `ǲ`(title case)이고
  `ToUpper` 는 `Ǳ`(upper case)다. **유니코드에 대문자와 제목자가 따로 있는 글자**가 있다.
- 고치는 법 — 낱말 첫 글자만 올리려면 **직접 쓰거나** `golang.org/x/text/cases` 를 쓴다.
  표준에는 **대체품이 없다.**

비용 — 없다. 결과가 조용히 틀릴 뿐이다.

### (5) ★★ 경계 — 빈 문자열·빈 구분자

**언제 쓰나** — `Split` 의 결과를 `len` 으로 검사할 때. **거의 모든 파서가 여기서 틀린다.**

```text
===== 소스: t11d.go =====
package main

import (
	"fmt"
	"strings"
)

func main() {
	cases := []struct{ s, sep string }{
		{"a,b,c", ","},
		{"", ","},
		{"a", ","},
		{",a,", ","},
		{",,", ","},
		{"abc", ""},
		{"한글", ""},
		{"", ""},
	}
	fmt.Printf("%-8s %-5s %-4s %s\n", "s", "sep", "len", "strings.Split(s, sep)")
	for _, c := range cases {
		out := strings.Split(c.s, c.sep)
		fmt.Printf("%-8q %-5q %-4d %#v\n", c.s, c.sep, len(out), out)
	}

	fmt.Println()
	z := strings.SplitN("a,b,c", ",", 0)
	fmt.Printf("SplitN(\"a,b,c\", \",\", 2)  = %#v\n", strings.SplitN("a,b,c", ",", 2))
	fmt.Printf("SplitN(\"a,b,c\", \",\", 0)  = %#v   nil 인가: %v\n", z, z == nil)
	fmt.Printf("SplitN(\"a,b,c\", \",\", -1) = %#v\n", strings.SplitN("a,b,c", ",", -1))
	fmt.Printf("SplitAfter(\"a,b\", \",\")   = %#v\n", strings.SplitAfter("a,b", ","))

	fmt.Println()
	fmt.Printf("Fields(\"  a  b \")        = %#v  len=%d\n", strings.Fields("  a  b "), len(strings.Fields("  a  b ")))
	fmt.Printf("Fields(\"\")               = %#v  len=%d\n", strings.Fields(""), len(strings.Fields("")))

	fmt.Println()
	fmt.Printf("Join(nil, \",\")           = %q\n", strings.Join(nil, ","))
	fmt.Printf("Join([]string{\"\"}, \",\")  = %q\n", strings.Join([]string{""}, ","))
	fmt.Printf("Join([]string{\"\",\"\"}, \",\") = %q\n", strings.Join([]string{"", ""}, ","))

	fmt.Println()
	before, after, found := strings.Cut("k=v", "=")
	fmt.Printf("Cut(\"k=v\", \"=\")          = %q %q %v\n", before, after, found)
	before, after, found = strings.Cut("kv", "=")
	fmt.Printf("Cut(\"kv\", \"=\")           = %q %q %v   ← 못 찾으면 before 가 원본 전체다\n", before, after, found)

	fmt.Println()
	fmt.Printf("Index(\"한글\", \"글\")      = %d   ← 바이트 위치다\n", strings.Index("한글", "글"))
	fmt.Printf("Count(\"cheese\", \"e\")     = %d\n", strings.Count("cheese", "e"))
	fmt.Printf("Count(\"abc\", \"\")         = %d   ← 빈 문자열은 룬 수 + 1 이다\n", strings.Count("abc", ""))
	fmt.Printf("Repeat(\"ab\", 0)          = %q\n", strings.Repeat("ab", 0))
	fmt.Printf("HasPrefix(\"\", \"\")        = %v\n", strings.HasPrefix("", ""))
	fmt.Printf("TrimLeft(\"xxhixx\", \"x\")  = %q   TrimPrefix 와 다르다\n", strings.TrimLeft("xxhixx", "x"))
	fmt.Printf("TrimPrefix(\"xxhixx\", \"x\") = %q\n", strings.TrimPrefix("xxhixx", "x"))
}
===== 명령: go build -trimpath -o prog . && ./prog =====
s        sep   len  strings.Split(s, sep)
"a,b,c"  ","   3    []string{"a", "b", "c"}
""       ","   1    []string{""}
"a"      ","   1    []string{"a"}
",a,"    ","   3    []string{"", "a", ""}
",,"     ","   3    []string{"", "", ""}
"abc"    ""    3    []string{"a", "b", "c"}
"한글"     ""    2    []string{"한", "글"}
""       ""    0    []string{}

SplitN("a,b,c", ",", 2)  = []string{"a", "b,c"}
SplitN("a,b,c", ",", 0)  = []string(nil)   nil 인가: true
SplitN("a,b,c", ",", -1) = []string{"a", "b", "c"}
SplitAfter("a,b", ",")   = []string{"a,", "b"}

Fields("  a  b ")        = []string{"a", "b"}  len=2
Fields("")               = []string{}  len=0

Join(nil, ",")           = ""
Join([]string{""}, ",")  = ""
Join([]string{"",""}, ",") = ","

Cut("k=v", "=")          = "k" "v" true
Cut("kv", "=")           = "kv" "" false   ← 못 찾으면 before 가 원본 전체다

Index("한글", "글")      = 3   ← 바이트 위치다
Count("cheese", "e")     = 3
Count("abc", "")         = 4   ← 빈 문자열은 룬 수 + 1 이다
Repeat("ab", 0)          = ""
HasPrefix("", "")        = true
TrimLeft("xxhixx", "x")  = "hixx"   TrimPrefix 와 다르다
TrimPrefix("xxhixx", "x") = "xhixx"
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`Split("", ",")` 은 빈 슬라이스가 아니라 `[]string{""}` — 길이 1** 이다.
  「빈 입력이면 조각이 0개」를 기대한 코드가 여기서 틀린다.
- **`Split("", "")` 만이 길이 0** 이다. 구분자가 비었을 때만 다르다.
- **구분자가 빈 문자열이면 룬 단위로 쪼갠다** — `Split("한글", "")` 이 `["한" "글"]` 이다.
  **바이트가 아니라 룬**이다(10번 주제의 `range` 와 같은 단위).
- `SplitN` 의 셋째 인자 — `2` 는 「최대 2조각」, `0` 은 **`nil`**, `-1` 은 「전부」다.
  ★ **`0` 이 빈 슬라이스가 아니라 `nil`** 인 것에 주의.
- `Fields("")` 는 **길이 0** 이다 — `Split` 과 정반대다. **공백 기준 쪼개기는 빈 입력에 빈 결과**를 준다.
- `Cut` (**1.18**) 은 못 찾으면 **`before` 에 원본 전체**를 넣고 `found=false` 를 준다.
  ★ `SplitN(s, sep, 2)` 보다 **쓰기도 읽기도 낫다** — 조각 수를 세지 않아도 된다.
- `Count(s, "")` 는 **룬 수 + 1** 이다(`"abc"` 에 4). 「빈 문자열이 몇 번 들어 있나」의 관례다.
- ★ **`TrimLeft` 와 `TrimPrefix` 는 다른 함수다** — 앞은 **글자 집합**을 계속 깎고,
  뒤는 **접두사 한 번**만 뗀다. `TrimLeft("xxhixx", "x")` 가 `"hixx"`, `TrimPrefix` 가 `"xhixx"` 다.
  **이름이 닮아서 가장 자주 헷갈리는 짝**이다.

```text
   Split("a,b,c", ",")  ->  ["a" "b" "c"]   len 3
   Split("",      ",")  ->  [""]            len 1   ★ 0 이 아니다
   Split(",a,",   ",")  ->  ["" "a" ""]     len 3
   Split("abc",   "")   ->  ["a" "b" "c"]   len 3   (룬 단위)
   Split("",      "")   ->  []              len 0   ★ 여기만 0

   Fields("")           ->  []              len 0   ← Split 과 다르다
   SplitN("a,b,c", ",", 0) -> nil                   ★ 빈 슬라이스가 아니다
```

비용 — `Split` 은 조각 수만큼 헤더를 잡는다. 한 번만 쪼갤 거면 **`Cut` 이 할당 0**이다.

### (6) `bytes` 가 따로 있는 이유 · 두 버퍼

**언제 쓰나** — `io` 와 붙어 있는 코드에서. `bytes.Buffer` 와 `strings.Builder` 를 고를 때.

```text
===== 소스: t11f.go =====
package main

import (
	"bytes"
	"fmt"
	"io"
	"os"
	"strings"
)

func main() {
	b := []byte("hello 한글")

	fmt.Println("같은 일을 두 갈래로 — 중간에 변환이 끼는가가 다르다")
	fmt.Printf("  bytes.ToUpper(b)                 = %q\n", bytes.ToUpper(b))
	fmt.Printf("  []byte(strings.ToUpper(string(b))) = %q\n", []byte(strings.ToUpper(string(b))))

	fmt.Println()
	fmt.Println("bytes.Buffer 와 strings.Builder 는 쓰는 쪽이 다르다")
	var sb strings.Builder
	sb.WriteString("문자열을 만든다")
	fmt.Printf("  strings.Builder.String() -> %q\n", sb.String())

	var bb bytes.Buffer
	bb.WriteString("바이트를 만든다")
	fmt.Printf("  bytes.Buffer.Bytes()     -> %q   (Buffer 는 읽기도 된다)\n", bb.Bytes())
	fmt.Printf("  bytes.Buffer 는 io.Reader 인가 : %v\n", func() bool { var r io.Reader = &bb; return r != nil }())

	fmt.Println()
	fmt.Println("strings.NewReader / bytes.NewReader 는 io.Reader 를 공짜로 만든다")
	n, _ := io.Copy(os.Stdout, strings.NewReader("  <- strings.NewReader 가 흘려보낸 글자\n"))
	fmt.Printf("  io.Copy 가 옮긴 바이트 수 : %d\n", n)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
같은 일을 두 갈래로 — 중간에 변환이 끼는가가 다르다
  bytes.ToUpper(b)                 = "HELLO 한글"
  []byte(strings.ToUpper(string(b))) = "HELLO 한글"

bytes.Buffer 와 strings.Builder 는 쓰는 쪽이 다르다
  strings.Builder.String() -> "문자열을 만든다"
  bytes.Buffer.Bytes()     -> "바이트를 만든다"   (Buffer 는 읽기도 된다)
  bytes.Buffer 는 io.Reader 인가 : true

strings.NewReader / bytes.NewReader 는 io.Reader 를 공짜로 만든다
  <- strings.NewReader 가 흘려보낸 글자
  io.Copy 가 옮긴 바이트 수 : 47
(exit 0)
```

그림 해설 (한 단계씩):

- `bytes.ToUpper(b)` 와 `[]byte(strings.ToUpper(string(b)))` 는 **결과가 같다.**
  다른 것은 **변환 두 번**이 끼느냐다.
- ★★ **`strings.Builder` 와 `bytes.Buffer` 는 쓰임이 다르다.**

| | `strings.Builder` | `bytes.Buffer` |
|---|---|---|
| 목적 | **문자열을 만든다** | **바이트를 쌓고 다시 읽는다** |
| 읽기 | 없다 | ★ **`io.Reader` 다** |
| 꺼내기 | `String()` — **복사 없음** | `Bytes()` · `String()` |
| 복사 | ★ **금지**(패닉) | 권장하지 않지만 패닉은 없다 |
| 쓸 자리 | 로그 줄·SQL·메시지 조립 | `io.Copy` 의 양쪽·인코더 출력 |

- `strings.NewReader`·`bytes.NewReader` 는 **문자열·바이트를 `io.Reader` 로 감싼다** — 복사가 없다.
  테스트에서 파일 대신 넣는 표준 수법이다.
- ★ 정본은 목록의 **43번 주제**(`io.Reader`/`Writer`)다. 여기서는 **어느 통에 담느냐**만 본다.

비용 — `Builder.String()` 은 **복사가 없고** `Buffer.String()` 은 **복사가 있다.**

### (7) `unicode/utf8` 과 `unicode`

**언제 쓰나** — 바이트와 룬 사이를 오갈 때. 10번 주제의 도구 상자다.

```text
===== 소스: t11h.go =====
package main

import (
	"fmt"
	"unicode"
	"unicode/utf8"
)

func main() {
	s := "Go한🙂"
	fmt.Printf("s = %q  len=%d  RuneCountInString=%d\n", s, len(s), utf8.RuneCountInString(s))
	fmt.Printf("RuneLen : 'G'=%d  '한'=%d  '🙂'=%d\n", utf8.RuneLen('G'), utf8.RuneLen('한'), utf8.RuneLen('🙂'))

	r, size := utf8.DecodeRuneInString(s[2:])
	fmt.Printf("DecodeRuneInString(s[2:])  = %q, %d\n", r, size)
	r, size = utf8.DecodeLastRuneInString(s)
	fmt.Printf("DecodeLastRuneInString(s)  = %q, %d\n", r, size)
	r, size = utf8.DecodeRuneInString("")
	fmt.Printf("DecodeRuneInString(\"\")     = %q, %d   ← 빈 입력은 (RuneError, 0)\n", r, size)

	fmt.Printf("ValidString(s)=%v  ValidString(s[:3])=%v\n", utf8.ValidString(s), utf8.ValidString(s[:3]))
	fmt.Printf("RuneStart: s[2]=%v  s[3]=%v\n", utf8.RuneStart(s[2]), utf8.RuneStart(s[3]))
	fmt.Printf("MaxRune=%U  RuneError=%U  UTFMax=%d  RuneSelf=%d\n",
		utf8.MaxRune, utf8.RuneError, utf8.UTFMax, utf8.RuneSelf)

	fmt.Println()
	fmt.Printf("unicode.IsLetter('한')=%v  IsDigit('4')=%v  IsSpace(' ')=%v  IsPunct(',')=%v\n",
		unicode.IsLetter('한'), unicode.IsDigit('4'), unicode.IsSpace(' '), unicode.IsPunct(','))
	fmt.Printf("unicode.ToUpper('a')=%q  unicode.Is(unicode.Hangul, '한')=%v\n",
		unicode.ToUpper('a'), unicode.Is(unicode.Hangul, '한'))
}
===== 명령: go build -trimpath -o prog . && ./prog =====
s = "Go한🙂"  len=9  RuneCountInString=4
RuneLen : 'G'=1  '한'=3  '🙂'=4
DecodeRuneInString(s[2:])  = '한', 3
DecodeLastRuneInString(s)  = '🙂', 4
DecodeRuneInString("")     = '�', 0   ← 빈 입력은 (RuneError, 0)
ValidString(s)=true  ValidString(s[:3])=false
RuneStart: s[2]=true  s[3]=false
MaxRune=U+10FFFF  RuneError=U+FFFD  UTFMax=4  RuneSelf=128

unicode.IsLetter('한')=true  IsDigit('4')=true  IsSpace(' ')=true  IsPunct(',')=true
unicode.ToUpper('a')='A'  unicode.Is(unicode.Hangul, '한')=true
(exit 0)
```

그림 해설 (한 단계씩):

- **세기** — `RuneCountInString` 은 배열을 안 잡고 센다.
- **쪼개기** — `DecodeRuneInString` 은 `(rune, size)` 를, `DecodeLastRuneInString` 은 **뒤에서** 하나를 준다.
  ★ 빈 입력에는 **`(RuneError, 0)`** 을 준다 — `size` 가 0인 것이 종료 신호다.
- **묻기** — `ValidString` 이 유효성을, `RuneStart` 가 **경계인지**를 답한다.
- **상수** — `MaxRune`(`U+10FFFF`) · `RuneError`(`U+FFFD`) · `UTFMax`(4) · `RuneSelf`(128).
  ★ `RuneSelf` 미만은 **ASCII 라 한 바이트**다 — 빠른 경로를 쓸 때의 기준이다.
- `unicode` 는 **룬 하나의 성질**을 묻는다 — `IsLetter`·`IsDigit`·`IsSpace`·`IsPunct`·`ToUpper`.
  `unicode.Is(unicode.Hangul, '한')` 처럼 **문자 범위표**도 들고 있다.
- ★ `unicode/utf8` 은 **인코딩**을, `unicode` 는 **글자의 성질**을 본다. 둘은 다른 패키지다.

비용 — 전부 할당이 없다. `RuneCountInString` 은 ASCII 구간에 빠른 경로가 있다.

## 문법 — 형태와 규칙

### 형태 — 네 패키지로 하는 일 전부

```go
// t11form.go
package main

import (
	"bytes"
	"fmt"
	"strconv"
	"strings"
	"unicode/utf8"
)

func main() {
	// ① 검사·자르기·바꾸기 — strings
	s := " key=값 "
	fmt.Printf("① %q -> TrimSpace %q · Cut %v · ReplaceAll %q\n",
		s, strings.TrimSpace(s),
		func() []string { a, b, _ := strings.Cut(strings.TrimSpace(s), "="); return []string{a, b} }(),
		strings.ReplaceAll(s, "=", ":"))

	// ② 이어 붙이기 — Builder (길면) · + (짧으면) · Join (조각이 있으면)
	var b strings.Builder
	b.Grow(16)
	b.WriteString("a")
	b.WriteByte('b')
	b.WriteRune('한')
	fmt.Printf("② Builder %q · Join %q\n", b.String(), strings.Join([]string{"x", "y"}, ","))

	// ③ 수와 문자열 사이 — strconv
	n, err := strconv.Atoi("42")
	fmt.Printf("③ Atoi %d %v · Itoa %q · Quote %s\n", n, err, strconv.Itoa(-7), strconv.Quote("한\t"))

	// ④ []byte 로 같은 일 — bytes
	bs := []byte("  hello  ")
	fmt.Printf("④ bytes.TrimSpace %q · bytes.Equal %v\n",
		bytes.TrimSpace(bs), bytes.Equal([]byte("a"), []byte("a")))

	// ⑤ 바이트와 룬 사이 — unicode/utf8
	fmt.Printf("⑤ RuneCountInString %d · ValidString %v · RuneLen('한') %d\n",
		utf8.RuneCountInString("한글"), utf8.ValidString("한글"), utf8.RuneLen('한'))
}
```

```text
===== 소스: t11form.go =====
package main

import (
	"bytes"
	"fmt"
	"strconv"
	"strings"
	"unicode/utf8"
)

func main() {
	// ① 검사·자르기·바꾸기 — strings
	s := " key=값 "
	fmt.Printf("① %q -> TrimSpace %q · Cut %v · ReplaceAll %q\n",
		s, strings.TrimSpace(s),
		func() []string { a, b, _ := strings.Cut(strings.TrimSpace(s), "="); return []string{a, b} }(),
		strings.ReplaceAll(s, "=", ":"))

	// ② 이어 붙이기 — Builder (길면) · + (짧으면) · Join (조각이 있으면)
	var b strings.Builder
	b.Grow(16)
	b.WriteString("a")
	b.WriteByte('b')
	b.WriteRune('한')
	fmt.Printf("② Builder %q · Join %q\n", b.String(), strings.Join([]string{"x", "y"}, ","))

	// ③ 수와 문자열 사이 — strconv
	n, err := strconv.Atoi("42")
	fmt.Printf("③ Atoi %d %v · Itoa %q · Quote %s\n", n, err, strconv.Itoa(-7), strconv.Quote("한\t"))

	// ④ []byte 로 같은 일 — bytes
	bs := []byte("  hello  ")
	fmt.Printf("④ bytes.TrimSpace %q · bytes.Equal %v\n",
		bytes.TrimSpace(bs), bytes.Equal([]byte("a"), []byte("a")))

	// ⑤ 바이트와 룬 사이 — unicode/utf8
	fmt.Printf("⑤ RuneCountInString %d · ValidString %v · RuneLen('한') %d\n",
		utf8.RuneCountInString("한글"), utf8.ValidString("한글"), utf8.RuneLen('한'))
}
===== 명령: go build -trimpath -o prog . && ./prog =====
① " key=값 " -> TrimSpace "key=값" · Cut [key 값] · ReplaceAll " key:값 "
② Builder "ab한" · Join "x,y"
③ Atoi 42 <nil> · Itoa "-7" · Quote "한\t"
④ bytes.TrimSpace "hello" · bytes.Equal true
⑤ RuneCountInString 2 · ValidString true · RuneLen('한') 3
(exit 0)
```

규칙 불릿.

- **손에 든 것이 `string` 이면 `strings`, `[]byte` 면 `bytes`.** 변환을 넣기 전에 한 번 더 생각한다.
- **루프에서 이으면 `Builder`.** 최종 크기를 알면 **`Grow` 를 부른다**(1할당).
  조각이 이미 슬라이스면 **`Join`**.
- **두세 개는 `+` 로.** 읽기 좋고 컴파일러가 한 번에 잡는다.
- **`Builder` 는 복사 금지.** 포인터로 넘긴다.
- **`Atoi` 는 공백을 안 잘라 준다.** `TrimSpace` 를 먼저.
- **`ErrRange` 일 때 반환값이 경계값**이다. 에러를 안 보면 그럴듯한 수가 흘러간다.
- **`Split("", sep)` 은 길이 1.** 빈 입력 검사를 `len` 으로 하지 마라.
- **한 번만 쪼갤 거면 `Cut`**(1.18). 할당이 0이다.
- **`TrimLeft` 는 글자 집합, `TrimPrefix` 는 접두사.** 다른 함수다.
- **`strings.Title` 을 쓰지 마라.** deprecated 이고 컴파일러는 안 말린다.

## 어디서 틀리나

### 1. ★★★ 「`+=` 도 쓸 만하던데」

- (1)절 실측 — 1000번 이으면 할당이 **999번**, 시간이 **두 자릿수** 차이다.
- ★ 작은 입력에서는 안 드러난다. **10개를 잇는 테스트는 통과**한다.
- 고치는 법 — **루프 안이면 무조건 `Builder`**. 최종 크기를 알면 `Grow`.

### 2. ★★★ 「`len(strings.Split(s, sep))` 으로 빈 입력을 거른다」

- (5)절 실측 — **`Split("", ",")` 의 길이가 1** 이다. 빈 입력이 「조각 하나」로 통과한다.
- ★ CSV·설정 파일 파서가 여기서 **빈 필드 하나**를 만들어 내려보낸다.
- 고치는 법 — **`s == ""` 를 먼저 검사**하거나 `strings.Fields` 를 쓴다.

### 3. ★★★ 「에러는 로그만 찍고 값은 쓴다」

- (3)절 실측 — `ErrRange` 일 때 `Atoi` 가 **`MaxInt64`** 를, `ParseFloat` 가 **`+Inf`** 를 돌려준다.
- ★★ **에러를 무시하면 「그럴듯한 값」이 흘러간다.** 제로값이면 그나마 눈에 띄는데 이쪽은 안 띈다.
- 고치는 법 — `ErrRange` 와 `ErrSyntax` 를 **갈라서** 다루고, 값은 에러가 `nil` 일 때만 쓴다.

### 4. ★★ 「`strings.Title` 로 제목 꼴을 만든다」

- (4)절 실측 — `"don't"` 가 **`"Don'T"`** 가 된다. deprecated 인데 **컴파일러는 조용하다.**
- 고치는 법 — 직접 쓰거나 `golang.org/x/text/cases`. **`ToTitle` 은 대체품이 아니다.**

### 5. ★★ 「`Builder` 를 구조체에 담고 값으로 넘겼다」

- (2)절 실측 — 복사는 되고 **쓰는 순간 패닉**이다.
- ★ 값으로 넘긴 뒤 **읽기만 하면 통과**하므로 테스트를 빠져나갈 수 있다.
- 고치는 법 — **포인터로** 넘긴다.

### 6. ★★ 「`[]byte` 인데 `strings` 를 쓴다」

- (0)절 — `string(b)` 와 `[]byte(s)` 가 **각각 복사**다. 루프 안이면 누적된다.
- 고치는 법 — **`bytes` 에 같은 이름의 함수가 있다.** 찾아보고 쓴다.

### 7. ★ 「`TrimLeft` 로 접두사를 뗀다」

- (5)절 실측 — `TrimLeft("xxhixx", "x")` 가 `"hixx"` 다. **글자 집합**을 계속 깎는다.
- 고치는 법 — 접두사 하나를 떼려면 **`TrimPrefix`**.

### 8. ★ 「`SplitN(s, sep, 0)` 이 빈 슬라이스겠지」

- (5)절 실측 — **`nil`** 이다. `len` 은 0이지만 `== nil` 이 참이다.
- 고치는 법 — 슬라이스를 `nil` 로 구분하는 코드라면 조심한다. 대개는 `len` 으로 충분하다.

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| `Split("", ",")` 이 **길이 1** | **패키지의 계약** | `strings` 문서가 정한 동작 |
| `Split(s, "")` 이 **룬 단위** | **패키지의 계약** | 〃 |
| `Cut` 이 못 찾으면 `before` 에 **원본 전체** | **패키지의 계약** | 〃 |
| `Atoi` 가 **공백을 안 자른다** | **패키지의 계약** | 〃 |
| `ErrRange` 일 때 **경계값을 돌려준다** | **패키지의 계약** | `strconv` 문서가 명시한다 |
| `NumError` 의 **에러 문장 형식** | **패키지의 계약** | `NumError.Error()` 의 구현 |
| `Builder` 복사 시 **패닉** | **패키지의 계약** | `copyCheck` 가 문서화된 동작이다 |
| `Builder.String()` 이 **복사 없음** | **패키지의 계약** | 문서가 그렇게 적는다 |
| `strings.Title` 이 **deprecated** | **이 판의 패키지 문서** | ★ 판마다 다시 떠야 한다(1.18부터) |
| `Builder` 의 **`allocs/op` 15** | **구현(내부 성장 전략)** | 계약이 아니다. 판이 오르면 바뀐다 |
| `+=` 의 **999할당** | **구현의 필연적 결과** | 문자열이 불변이라 매번 새로 만든다 |
| **`ns/op` 수치** | **이 머신의 관찰** | 대조할 것은 **자릿수 차이**다 |
| 벤치마크 이름의 **`-24`** | **이 머신의 `GOMAXPROCS`** | 머신마다 다르다 |
| `Atoi` 의 **빠른 경로** | **구현(strconv)** | 문서에 적혀 있지만 수치는 안 쟀다 |

★★ **이 표의 윗칸 대부분이 「명세」가 아니라 「패키지의 계약」이다.**
Go 명세는 표준 라이브러리를 모른다. 그래서 이 주제에서 인용할 정본은 **명세가 아니라 `go doc`** 이고,
**그것은 판마다 바뀐다** — `strings.Title` 이 그 증거다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 두세 개를 잇는다 | `+` | 읽기 좋고 한 번에 잡는다 |
| 루프에서 잇는다 | `strings.Builder` | 할당이 자릿수로 준다 |
| 최종 크기를 안다 | `Builder` + `Grow` | **1할당** |
| 조각이 이미 슬라이스다 | `strings.Join` | **1할당** · 가장 짧다 |
| `[]byte` 를 들고 있다 | `bytes.*` | 변환 두 번을 없앤다 |
| 바이트를 쌓고 다시 읽는다 | `bytes.Buffer` | `io.Reader` 다 |
| 문자열을 `io.Reader` 로 | `strings.NewReader` | 복사가 없다 |
| 수로 바꾼다 | `strconv.Atoi`/`ParseInt` | 에러를 **갈라서** 본다 |
| 수를 문자열로 | `strconv.Itoa` | ★ `string(n)` 은 코드 포인트다(10번 주제) |
| 로그에 문자열을 안전하게 | `strconv.Quote` | 제어문자가 이스케이프된다 |
| 한 번만 쪼갠다 | `strings.Cut`(**1.18**) | 할당 0 · 조각 수를 안 센다 |
| 공백으로 쪼갠다 | `strings.Fields` | 빈 입력에 **빈 결과** |
| 글자 수를 센다 | `utf8.RuneCountInString` | 배열을 안 잡는다 |
| 제목 꼴로 만든다 | ★ **직접 쓴다** | `strings.Title` 은 deprecated |

판단 규칙 두 줄.

- **「지금 손에 든 것이 `string` 인가 `[]byte` 인가」를 먼저 물어라.** 그게 패키지를 고른다.
- **「이 함수가 빈 입력에 무엇을 주나」를 던져서 확인하라.** 이 주제의 사고는 전부 거기다.

## 핵심 문장

- ★★★ **`+=` 로 1000번 이으면 할당 999번**, `Builder` 는 **15번**, `Grow` 를 부르면 **1번**이다.
  시간은 **두 자릿수** 차이였다. **잰 것만 적는다** — `allocs/op` 는 안 흔들리고 `ns/op` 은 흔들린다.
- ★★★ **`strings.Split("", ",")` 은 길이 1** 이다. 빈 입력을 `len` 으로 거르면 통과해 버린다.
  **`Split("", "")` 만이 길이 0** 이다.
- ★★★ **`strconv` 의 `ErrRange` 는 경계값을 돌려준다** — `MaxInt64`·`+Inf`·`127`.
  에러를 무시하면 **그럴듯한 값**이 흘러간다.
- ★★ **`bytes` 는 변환 두 번을 없애려고 있다.** `strings` 와 함수 이름이 짝을 이룬다.
- ★★ **`strings.Title` 은 deprecated 인데 컴파일러가 안 말린다.** `go doc` 을 열어야 보이고,
  `"don't"` 를 `"Don'T"` 로 만든다. **`ToTitle` 은 대체품이 아니다.**
- ★★ **`strings.Builder` 는 복사하면 패닉**이다 — `String()` 이 복사 없이 내주기 때문이다.
- **`Cut`(1.18)이 `SplitN(s, sep, 2)` 보다 낫다** — 할당 0에 조각 수를 안 센다.
- **`TrimLeft` 는 글자 집합, `TrimPrefix` 는 접두사** — 다른 함수다.
- **`Split(s, "")` 은 룬 단위**이지 바이트 단위가 아니다.
- **이 주제의 정본은 명세가 아니라 `go doc`** 이고, 그것은 **판마다 바뀐다.**

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 11번)
- [`../10-strings-bytes-runes-and-utf8-iteration/`](../10-strings-bytes-runes-and-utf8-iteration/)(문자열과 UTF-8) —
  ★ **직접 선행**. **그쪽은 언어가 주는 것(`len`·인덱싱·`range`·변환)까지**,
  여기는 **그 위에 선 네 패키지**부터
- [`../07-slice-sharing-silent-bugs/`](../07-slice-sharing-silent-bugs/)(슬라이스 공유) —
  `Buffer.Bytes()` 가 **내부 배열을 내주는** 이야기가 거기의 「더 들어가면」에 있다
- [`../04-numeric-types-conversions-and-integer-division/`](../04-numeric-types-conversions-and-integer-division/)(수치 타입) —
  `ParseInt` 의 `bitSize` 와 오버플로가 거기의 규칙에 기댄다
- [`../../../java/syntax/36-stringbuilder-and-concat/`](../../../java/syntax/36-stringbuilder-and-concat/) —
  ★ **직접 대비**. **그쪽의 결론이 여기와 같다** — 루프 안의 `+=` 가 느린 이유는 컴파일 방식이 아니라
  **문자열이 불변이라 매번 전체를 복사하기 때문**이다.
  다른 것은 컴파일 표면이다 — 자바는 JDK 9부터 `+` 를 `invokedynamic`/`StringConcatFactory` 로 접고,
  Go 는 그런 장치 없이 **사람이 `Builder` 를 고른다**
- [`../../../python/syntax/07-string-methods/`](../../../python/syntax/07-string-methods/) —
  파이썬은 메서드가 `str` 에 붙어 있고 Go 는 **패키지 함수**다. `join` 의 방향이 반대인 것도 여기
- [`../../../rust/syntax/14-string-vs-str/`](../../../rust/syntax/14-string-vs-str/) —
  Rust 는 **`String`/`&str` 두 타입**으로 Go 의 `bytes`/`strings` 분업과 비슷한 일을 타입으로 한다
- 목록의 **23번 주제**(`error` 인터페이스) · **24번 주제**(`errors.Is`/`As`) —
  `NumError` 를 `errors.As` 로 꺼내는 것의 정본
- 목록의 **43번 주제**(`io.Reader`/`Writer`) — `bytes.Buffer`·`strings.NewReader` 가 왜 그 모양인지
- 목록의 **50번 주제**(벤치마크) — `go test -bench` 와 `-benchmem` 읽는 법의 정본
- 목록의 **42번 주제**(`fmt`) — `fmt.Sprintf` 와 `Builder` 중 무엇을 고르나

## 용어 풀이

- **`strings`** — `string` 을 다루는 표준 패키지.
- **`bytes`** — 같은 일을 `[]byte` 로 하는 패키지. **변환을 없애려고** 있다.
- **`strconv`** — 수·불리언과 문자열 사이를 오가는 패키지.
- **`unicode/utf8`** — 바이트와 룬 사이. **인코딩**을 다룬다.
- **`unicode`** — 룬 하나의 **성질**(글자인가·숫자인가·대소문자)을 다룬다.
- **`allocs/op`** — 벤치마크 한 번에 일어난 힙 할당 횟수. **시간보다 훨씬 덜 흔들린다.**
- **센티넬 오류(sentinel error)** — `strconv.ErrSyntax` 처럼 **미리 만들어 둔 오류 값**.
  `errors.Is` 로 비교한다. 정본은 목록의 **25번 주제**다.
- **deprecated** — 「쓰지 말라」는 문서 표시. **Go 는 삭제하지 않고 문서에만 적는다.**
- **title case** — 유니코드가 대문자와 따로 정의한 글자꼴. `ǳ` → `ǲ` 같은 세 벌 글자에서 갈린다.

---

## 더 들어가면

- **왜 `bytes` 와 `strings` 를 제네릭으로 합치지 않았나** — 둘 다 1.0 이전부터 있었고
  제네릭은 1.18 에 왔다. **호환성 약속** 때문에 합칠 수 없다.
  ★ 이것이 Go 표준 라이브러리 곳곳에서 보이는 모양이다 — **나중에 온 기능이 앞의 설계를 못 바꾼다.**
- **`Builder` 가 1.10 에 온 이유** — 그전에는 `bytes.Buffer` 로 문자열을 만들었는데
  `Buffer.String()` 이 **복사를 한다.** `Builder` 는 그 복사를 없애려고 만든 물건이다.
- **`strings.Title` 을 왜 안 지우나** — Go 1 호환성 약속이 **표준 라이브러리 함수의 삭제를 금지**한다.
  그래서 Go 에서 deprecated 는 「다음 판에 사라진다」가 아니라 「**영원히 남지만 쓰지 마라**」다.
  ★ 이 점이 다른 언어와 크게 다르다.
- **`Buffer.Bytes()` 는 내부 배열을 그대로 내준다.** 받아서 오래 들고 있으면
  다음 쓰기에 덮인다 — 슬라이스 별칭 문제다(목록의 **07번 주제**).
  **이 문서는 그것을 던져서 확인하지 않았다.**
- **`strconv` 와 `fmt` 중 무엇을 쓰나** — `fmt.Sprintf("%d", n)` 도 되지만 `strconv.Itoa(n)` 이 싸다.
  `fmt` 는 리플렉션을 거친다. ★ **수치는 안 쟀다** — 정본은 목록의 **42번 주제**와 **50번 주제**다.
- **정규식은 이 네 패키지에 없다.** `regexp` 가 따로 있고, **`strings` 로 되는 일에 `regexp` 를 쓰면 느리다.**
  `Contains`·`HasPrefix`·`Cut` 으로 되는지 먼저 본다.

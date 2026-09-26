# go/syntax/11 — `strings`·`strconv`·`bytes`·`unicode/utf8` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★★★ **성능 답은 「무엇을 몇 번 어떻게 재서 얼마가 나왔나」로 적는다.**
> ★ **근거로 읽을 칸** — `allocs/op` 의 **값과 서열** · `Split`·`Cut`·`Fields` 의 경계 결과 ·
> `strconv` 의 **에러 문장 전문**과 **반환값** · 패닉 메시지 본문 · `go doc` 의 `Deprecated:` 줄 ·
> 종료 코드.
> **근거로 읽지 않을 칸** — **`ns/op`**(머신·부하에 달렸다 — 대조할 것은 **자릿수 차이**다) ·
> `B/op` 의 **끝자리** · 벤치마크 이름의 **`-24`** 와 `cpu:` 줄 · 패닉 스택의 **주소 오프셋** ·
> `Builder` 의 **`allocs/op` 15**(내부 성장 전략이라 판이 오르면 바뀐다).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. **999 · 15 · 1 · 1** — 그리고 시간은 **두 자릿수** 차이다

**출력**

```text
===== 명령: go test -run=^$ -bench=. -benchmem -benchtime=200x -count=1 ./... 2>&1 | grep "^Benchmark" | awk "{printf \"%-26s %8s %s\n\", \$1, \$(NF-1), \$NF}" =====
BenchmarkPlus-24                999 allocs/op
BenchmarkBuilder-24              15 allocs/op
BenchmarkBuilderGrow-24           1 allocs/op
BenchmarkJoin-24                  1 allocs/op
(exit 0)
```

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

**왜 그런가**

| 방법 | `allocs/op` | `B/op` | 왜 |
|---|---|---|---|
| `s += chunk` | **999** | 4MB 대 | 문자열이 불변이라 **이을 때마다 통째로 새로 만든다** |
| `strings.Builder` | **15** | 34KB 대 | 내부 버퍼를 **배로 늘린다** — 늘릴 때만 잡는다 |
| `Builder` + `Grow` | **1** | 8192 | 최종 크기를 **미리** 잡는다 |
| `strings.Join` | **1** | 8192 | 총 길이를 먼저 **세고** 한 번에 잡는다 |

- `+=` 가 **999**인 이유 — 1000번 이으면서 **처음 한 번 말고 매번 새 문자열**을 만든다.
  게다가 매번 **지금까지 만든 것 전체를 복사**하므로 `O(n²)` 이다.
  `B/op` 가 **4MB** 를 넘는 것이 그 증거다(최종 문자열은 8000바이트다).
- `Grow` 와 `Join` 이 **똑같이 1** 인 이유 — 둘 다 **최종 크기를 먼저 알고** 한 번에 잡는다.
  `Join` 은 조각의 길이를 다 더해서 알고, `Grow` 는 사람이 알려 준다.
  `B/op` 가 **둘 다 8192** 인 것이 같은 일을 했다는 증거다.
- **`ns/op`** 은 `+=` 가 **밀리초대**, 나머지가 **마이크로초대** — **두 자릿수** 차이다.
- ★★★ **그 수치를 근거로 써도 되는가 — 값 자체는 안 된다.**
  머신·부하·판에 따라 10\~30% 움직였다. **쓸 수 있는 것은 「자릿수 차이가 난다」는 성질**이고,
  숫자로 못을 박을 수 있는 것은 **`allocs/op`** 다.
- ★ 측정 조건 — `go test -bench` · `-benchtime=200x`(반복 고정) · `-count=1` ·
  8바이트 조각 × 1000개 · 한 머신. **신호가 두 자릿수라 잡음에 뒤집히지 않는다.**

### 2. **1 · 0 · 룬 단위 · `nil` · 0** — 그리고 `Cut` 은 원본을 통째로 준다

**출력**

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

**왜 그런가**

| 식 | 결과 | 길이 |
|---|---|---|
| `Split("a,b,c", ",")` | `["a" "b" "c"]` | 3 |
| `Split("", ",")` | ★ `[""]` | **1** |
| `Split(",a,", ",")` | `["" "a" ""]` | 3 |
| `Split("abc", "")` | `["a" "b" "c"]` | 3 |
| `Split("한글", "")` | `["한" "글"]` | **2** — ★ 룬 단위 |
| `Split("", "")` | `[]` | **0** |
| `Fields("")` | `[]` | **0** |
| `SplitN("a,b,c", ",", 0)` | ★ `nil` | 0 |

- ★★★ **`Split("", ",")` 이 1인 이유** — 구분자가 없는 문자열은 **그 자체가 한 조각**이다.
  `Split` 은 「구분자로 나눈 조각들」을 주므로 **조각이 0개인 경우가 없다**(구분자가 비었을 때만 예외).
- **`Split("", "")` 만 0** 이다 — 빈 구분자는 「룬 단위로 쪼갠다」는 뜻이고, 빈 문자열에는 룬이 0개다.
- `Split("한글", "")` 이 **2** 다 — **룬 단위**이지 바이트 단위가 아니다.
  바이트로 쪼개려면 `[]byte(s)` 를 쓴다.
- **`SplitN(s, sep, 0)` 은 `nil`** 이다. 빈 슬라이스가 아니다. `len` 은 0이지만 `== nil` 이 참이다.
- **`Fields("")` 는 0** 이다 — `Split` 과 정반대다. `Fields` 는 「공백으로 갈린 낱말들」이라
  **낱말이 0개인 경우가 자연스럽다.**
- `Cut("kv", "=")` 은 **`"kv"`, `""`, `false`** 다 — 못 찾으면 **`before` 에 원본 전체**가 들어간다.
  ★ 그래서 `found` 를 안 보면 **원본이 조용히 키로 쓰인다.**

### 3. **공백은 실패하고, 범위 초과는 경계값을 돌려준다**

**출력**

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

**왜 그런가**

- `Atoi(" 42")` 는 **실패**다 — `strconv.Atoi: parsing " 42": invalid syntax`.
  ★ **앞뒤 공백을 안 잘라 준다.** `strings.TrimSpace` 를 먼저 불러야 한다.
  `"42 "`·`"0x2a"`·`""`·`"12a"` 도 전부 같은 이유로 실패다. `"+7"` 은 된다.
- ★★★ `Atoi("9223372036854775808")` 의 반환값이 **`9223372036854775807`** 이다. 0이 아니다.
  `int64` 의 최댓값 — 즉 **경계값**이다.
- 같은 식으로 `ParseFloat("1e400", 64)` 는 **`+Inf`**, `ParseInt("300", 10, 8)` 은 **`127`** 이다.
- 에러 문장 전문의 예 —
  `strconv.Atoi: parsing "9223372036854775808": value out of range`.
  `*strconv.NumError` 의 `Func`·`Num`·`Err` 세 필드가 그대로 문장이 된다.
- ★★★ 두 종류를 가르는 기준과 **반환값의 차이**가 핵심이다.

| 센티넬 | 뜻 | 반환값 | 위험도 |
|---|---|---|---|
| `ErrSyntax` | 글자가 수가 아니다 | **제로값** | 무시해도 0이라 눈에 띈다 |
| `ErrRange` | 수인데 타입에 안 들어간다 | ★ **경계값** | **그럴듯한 값이 흘러간다** |

- `errors.Is(err, strconv.ErrRange)` 로 판정한다 — `NumError` 가 `Unwrap` 을 들고 있다.
- ★★ **에러를 무시하는 코드가 `ErrRange` 에서 가장 조용히 틀린다.**
  `MaxInt64` 나 `+Inf` 가 「그냥 큰 수」로 보이기 때문이다.

### 4. **복사는 되고, 쓰는 순간 패닉이다**

**출력**

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

**왜 그런가**

- `b := a` 는 **통과**한다. 두 값이 같은 내용을 준다(`a="hello" b="hello"`).
- 복사본에 쓰는 순간 **`panic: strings: illegal use of non-zero Builder copied by value`**,
  종료 코드 **2** 다.
- 스택에 **`strings.(*Builder).copyCheck`** 와 **`strings.(*Builder).WriteString`** 이 찍힌다 —
  `Builder` 가 **자기 주소를 저장해 두고 매번 대조**한다는 뜻이다.
- ★★ 막는 **이유** — `Builder.String()` 은 **내부 버퍼를 복사 없이** 문자열로 내준다.
  문자열은 불변이어야 하므로 그 안전성은 「이 버퍼를 나 말고 아무도 안 쓴다」에 기댄다.
  **복사본이 생기면 두 `Builder` 가 같은 버퍼를 쓰게 되어 그 전제가 깨진다.**
- 구조체 필드로 담으려면 — **`*strings.Builder`** 로 담거나,
  구조체 자체를 **항상 포인터로만** 넘긴다.
- ★ 값으로 넘긴 뒤 **읽기만 하면 통과**하므로 테스트를 빠져나갈 수 있다. 07번 주제와 같은 성질이다.

### 5. deprecated 이고, **컴파일러는 한 마디도 안 한다**

**출력**

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

**왜 그런가**

- `go doc` 이 **`Deprecated:` 줄을 그대로** 보여 준다 —
  「The rule Title uses for word boundaries does not handle Unicode punctuation properly.
  Use golang.org/x/text/cases instead.」
- ★★ **`go build` 도 `go vet` 도 종료 코드 0** 이다. Go 의 deprecated 는 **문서 표시**일 뿐이고
  컴파일러는 모른다. **`go doc` 을 열어야 보인다.**
- 무엇이 문제인가 — `"don't shout at o'brien"` 이 **`"Don'T Shout At O'Brien"`** 이 된다.
  **아포스트로피를 단어 경계로** 보기 때문이다. 유니코드 문장부호 전반에서 같은 일이 난다.
- ★★ **`ToTitle` 은 대체품이 아니다.** 「낱말 첫 글자만」이 아니라
  **모든 글자를 title case 로** 바꾼다 — 실측에서 `"DON'T SHOUT AT O'BRIEN"` 이 나왔다.
- 둘이 실제로 갈리는 입력 — **세 벌 글자**다. `ǳ` 의 `ToTitle` 은 **`ǲ`**,
  `ToUpper` 는 **`Ǳ`** 다. 유니코드에 **대문자와 제목자가 따로** 있는 글자가 있다.
- 고치는 법 — **직접 쓰거나** `golang.org/x/text/cases`. **표준에는 대체품이 없다.**

### 6. **변환 두 번을 없애려고** 있다

**출력**

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

**왜 그런가**

- `[]byte` 를 들고 `strings` 를 쓰면 **복사가 두 번**이다 —
  `string(b)` 로 한 번, 결과를 `[]byte(s)` 로 되돌릴 때 또 한 번.
  각각 **바이트 수만큼**의 복사이고, 루프 안이면 누적된다.
- 두 버퍼의 차이.

| | `strings.Builder` | `bytes.Buffer` |
|---|---|---|
| 목적 | **문자열을 만든다** | **바이트를 쌓고 다시 읽는다** |
| 읽기 | 없다 | ★ **`io.Reader` 다**(실측에서 `true`) |
| `String()` | ★ **복사 없음** | **복사 있음** |

- ★ `Builder.String()` 이 복사가 없는 것이 `Builder` 의 존재 이유다.
  `Buffer` 는 **쓰고 나서 또 읽을 수 있어야** 하므로 내부 버퍼를 문자열로 넘겨 줄 수 없다.
- **제네릭으로 안 합친 이유** — 둘 다 **1.0 이전**부터 있었고 제네릭은 **1.18** 에 왔다.
  Go 1 호환성 약속이 **기존 API 의 변경을 금지**하므로 합칠 수 없다.
  ★ 표준 라이브러리 곳곳에 같은 모양이 있다 — **나중에 온 기능이 앞의 설계를 못 바꾼다.**

### 7. 일곱 가지를 이렇게 고른다

**출력** — 없음(경계 문항).

**왜 그런가**

| | 할 일 | 고를 것 | 이유 |
|---|---|---|---|
| ① | 로그 한 줄을 루프에서 | **`strings.Builder`**(+`Grow`) | `+=` 는 할당이 **999**(1번 문항) |
| ② | `key=value` 한 줄 | **`strings.Cut`**(1.18) | 할당 0 · 조각 수를 안 센다 · `found` 로 판정 |
| ③ | `[]byte` 에서 찾기 | **`bytes.Contains`/`Index`** | 변환 두 번을 없앤다 |
| ④ | 나이를 수로 | **`strconv.Atoi`** + `TrimSpace` | 공백을 안 잘라 준다 · `ErrRange` 를 따로 본다 |
| ⑤ | 이름이 20**글자**인가 | **`utf8.RuneCountInString`** | ★ `len` 은 바이트다(10번 주제) |
| ⑥ | 제어문자를 로그에 | **`strconv.Quote`** | 이스케이프해 준다. 로그가 안 깨진다 |
| ⑦ | 문자열을 `io.Reader` 로 | **`strings.NewReader`** | 복사가 없다 |

- ★ ⑤가 이 목록에서 가장 자주 틀리는 자리다 — `len(name) > 20` 은 **한글 사용자만** 걸린다.
- ★ ②를 `SplitN(s, "=", 2)` 로 해도 되지만 **조각 수를 세야 하고 슬라이스를 잡는다.**

### 8. 계약은 ①③④⑥⑦, 구현·관찰은 ②⑤⑧

**출력** — 없음(경계 문항).

**왜 그런가**

| | 주장 | 판정 | 근거 |
|---|---|---|---|
| ① | `Split("", ",")` 이 길이 1 | **패키지의 계약** | `strings` 문서가 정한 동작 |
| ② | `Builder` 의 `allocs/op` 가 15 | **구현(내부 성장 전략)** | 판이 오르면 바뀐다. 계약이 아니다 |
| ③ | `ErrRange` 일 때 경계값 | **패키지의 계약** | `strconv` 문서가 명시한다 |
| ④ | `Builder` 복사 후 쓰면 패닉 | **패키지의 계약** | `copyCheck` 가 문서화된 동작 |
| ⑤ | `BenchmarkPlus` 가 1밀리초대 | **이 머신의 관찰** | 머신·부하에 달렸다 |
| ⑥ | `strings.Title` 이 deprecated | **이 판의 패키지 문서** | 1.18부터. 판마다 다시 떠야 한다 |
| ⑦ | `Cut` 이 못 찾으면 `before` 에 원본 | **패키지의 계약** | 문서가 그렇게 적는다 |
| ⑧ | 벤치마크 이름에 `-24` | **이 머신의 `GOMAXPROCS`** | CPU 수다 |

- ★★★ **이 주제에는 「명세 보장」 칸이 거의 없다.** Go 명세는 표준 라이브러리를 모른다.
  그래서 최선의 정본이 **`go doc`** 이고, **그것은 판마다 바뀐다.**
  09·10 번 주제와 **층 구성 자체가 다른 것**이 이 주제의 성격이다.
- ★ ②와 ⑤를 「Go 가 그렇다」로 외우면 다음 판에서 조용히 틀린다.
  **외울 것은 999 ≫ 15 > 1 이라는 서열**이지 15라는 수가 아니다.

### 9. 자바도 루프 안에서는 느리다 — **이유가 Go 와 같다**

**출력** — 없음(연결 문항).

**왜 그런가**

| 물음 | **Go** | **자바** | **파이썬** | **Rust** |
|---|---|---|---|---|
| 루프 안의 `+=` | ★ **느리다** | ★ **느리다** | 느리다 | `String::push_str` 은 자리에서 자란다 |
| 그 이유 | 문자열이 **불변** | ★ **똑같이 불변** | 똑같이 불변 | `String` 은 가변이라 해당 없음 |
| 한 식 안의 `+` 를 컴파일러가 | 그대로 둔다 | ★ `invokedynamic`/`StringConcatFactory` 로 접는다(JDK 9+) | 그대로 둔다 | 그대로 둔다 |
| 이어 붙이기 도구 | `strings.Builder` | `StringBuilder` | `"".join(parts)` | `String::push_str`·`write!` |
| `join` 이 붙는 자리 | `strings.Join(조각, 구분자)` | `String.join(구분자, 조각)` | ★ `구분자.join(조각)` | `조각.join(구분자)` |
| `string`/`[]byte` 분업 | 패키지 둘(`strings`/`bytes`) | 없음(`String`/`byte[]` 따로) | `str`/`bytes` 타입 둘 | ★ **타입 둘**(`&str`/`&[u8]`) |

- ★★★ **「자바는 컴파일러가 `StringBuilder` 로 바꿔 주니까 괜찮다」는 틀린 전제다.**
  형제 문서가 실측으로 그것을 뒤집어 놓았다
  ([`../../../java/syntax/36-stringbuilder-and-concat/`](../../../java/syntax/36-stringbuilder-and-concat/)) —
  **JDK 9부터 `+` 는 `invokedynamic` + `StringConcatFactory` 로 컴파일되어 바이트코드에 `StringBuilder` 가 없고**,
  그런데도 **루프 안 `+=` 는 여전히 느리다.** 이유는 컴파일 방식이 아니라 **`String` 이 불변**이라
  매번 전체를 복사하기 때문이다 — **Go 의 `+=` 가 999번 할당하는 이유와 같은 이유**다.
  그쪽 실측에서 「n 이 2배일 때 `+=` 시간이 **약 4배**」라는 기울기가 세 JDK 모두 같았다.
- ★ 즉 **갈리는 것은 「왜 느린가」가 아니라 「한 식 안의 `+` 를 어떻게 접는가」이다**.
  자바는 접고 Go 는 안 접는다. 하지만 **루프 안에서는 둘 다 사람이 빌더를 골라야 한다.**
- 파이썬은 `join` 이 **구분자에 붙어 있다**(`",".join(parts)`).
  Go 는 **패키지 함수**라 `strings.Join(parts, ",")` 로 순서가 반대다
  ([`../../../python/syntax/07-string-methods/`](../../../python/syntax/07-string-methods/)).
- Rust 는 Go 의 패키지 분업을 **타입으로** 한다 — `&str` 과 `&[u8]` 이 다른 타입이고
  변환이 **검사를 거친다**([`../../../rust/syntax/14-string-vs-str/`](../../../rust/syntax/14-string-vs-str/)).
- ★★ **Go 가 deprecated 를 안 지우는 이유** — **Go 1 호환성 약속**이
  표준 라이브러리 함수의 삭제를 금지한다. 그래서 Go 의 deprecated 는
  「다음 판에 사라진다」가 아니라 「**영원히 남지만 쓰지 마라**」다.

### 10. 다른 주제와 잇기

**출력** — 없음(연결 문항).

**왜 그런가**

- **`len`·인덱싱·`range`·변환** — [`../10-strings-bytes-runes-and-utf8-iteration/`](../10-strings-bytes-runes-and-utf8-iteration/).
  **그쪽은 언어가 주는 것까지**, 여기는 **그 위에 선 네 패키지**부터다.
- **`errors.Is`/`As` 로 `NumError` 꺼내기** — [목록의 **24번 주제**](../24-error-wrapping-and-errors-is-as-join/)(오류 래핑).
  센티넬 오류 설계는 [목록의 **25번 주제**](../25-sentinel-errors-vs-custom-error-types/)다.
- **`bytes.Buffer` 가 `io.Reader` 인 것** — [목록의 **43번 주제**](../43-io-reader-writer-and-composition/)(`io.Reader`/`Writer`).
- **`go test -bench` 읽는 법** — [목록의 **50번 주제**](../50-benchmarks-testing-b-and-reading-profiles/)(벤치마크·프로파일).
  `-benchmem` 의 `B/op`·`allocs/op` 가 거기 정본이다.
- **`Buffer.Bytes()` 가 내부 배열을 내주는 위험** — [`../07-slice-sharing-silent-bugs/`](../07-slice-sharing-silent-bugs/).
  **이 문서는 그것을 던져서 확인하지 않았다.**

---

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행 1회** | 재실행 결과가 `diff -rq` 로 **동일**(벤치마크 블록 제외) |
| 판 확인 | `go version` · `go env GOOS GOARCH GOVERSION` | 1 | `go1.27.1 linux/amd64` |
| 네 패키지 지도 (`t11a`) | `go build && ./prog` | 1 | 같은 일을 네 갈래로 |
| ★★★ 이어 붙이기 **할당** (`t11b`) | `go test -bench=. -benchmem -benchtime=200x -count=1` 에서 `allocs/op` 만 뽑음 | 1 | **999 · 15 · 1 · 1** |
| ★★ 이어 붙이기 **시간** (`t11b`) | 같은 명령의 전체 출력 | 1 | `+=` 밀리초대 · 나머지 마이크로초대 — **흔들리는 칸** |
| 결과가 같은지 | `go test -run=.` 이 `TestSame` 을 돌린다 | 1 | **네 방법의 결과 문자열이 같다** |
| `strconv` 전수 (`t11c`) | `go build && ./prog` | 1 | 공백 실패 · `ErrRange` 가 경계값 |
| `Split` 경계 전수 (`t11d`) | 〃 | 1 | `Split("", ",")` 길이 **1** · `Split("", "")` 길이 **0** |
| ★ `strings.Title` (`t11e`) | `go build && ./prog` · `go vet ./...` | 각 1 | `"Don'T …"` · **vet exit 0**(안 말린다) |
| `Deprecated` 표시 | `go doc strings.Title` | 1 | `Deprecated:` 줄이 나온다 |
| `bytes` 와 두 버퍼 (`t11f`) | `go build && ./prog` | 1 | `Buffer` 는 `io.Reader` · `io.Copy` 47바이트 |
| ★ `Builder` 복사 (`t11g`) | 〃 | 1 | `illegal use of non-zero Builder copied by value` · **exit 2** |
| `unicode/utf8`·`unicode` (`t11h`) | 〃 | 1 | `DecodeRuneInString("")` 이 `(RuneError, 0)` |
| 형태 모음 (`t11form`) | 〃 | 1 | 네 패키지가 한 프로그램에서 동작 |

**구현·도구에 달린 항목**(판이 오르면 **다시 찍어야 하는** 것)

| 항목 | 왜 |
|---|---|
| **`ns/op`** 수치 전부 | 머신·부하에 달렸다. **대조할 것은 자릿수 차이**다 |
| `B/op` 의 **끝자리** | 측정 자체에 잡음이 섞인다(실측에서 끝 두 자리가 움직였다) |
| `Builder` 의 **`allocs/op` 15** | **내부 성장 전략**이다. 계약이 아니다 |
| 벤치마크 이름의 **`-24`** 와 `cpu:` 줄 | 이 머신의 `GOMAXPROCS`·CPU 이름이다 |
| `strings.Title` 의 **`Deprecated:` 문장** | **이 판의 패키지 문서**다. 판마다 다시 떠야 한다 |
| 패닉 스택의 **주소 오프셋**(`+0x246` 등)과 `strings/builder.go` 의 **줄 번호** | 표준 라이브러리 판에 달렸다 |
| `Atoi` 의 **빠른 경로**가 `ParseInt` 보다 싸다는 것 | ★ **안 쟀다.** 문서 서술만 옮겼다 |
| `fmt.Sprintf` 대 `strconv.Itoa` 의 비용 | ★ **안 쟀다.** 정본은 목록의 [**42**](../42-fmt-verbs-stringer-and-errorf/)·[**50**](../50-benchmarks-testing-b-and-reading-profiles/)번 주제다 |
| `Buffer.Bytes()` 의 별칭 위험 | ★ **안 던져 봤다.** 정본은 07번 주제다 |

★ **다시 찍는 법** — `capture.sh` 를 그대로 돌리고 `diff -rq` 한다.
**흔들리는 칸으로 선언한 블록**(`b11bench`) 하나만 달라야 하고 나머지는 한 글자도 같아야 한다.

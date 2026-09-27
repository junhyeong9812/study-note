# go/syntax/11 — `strings`·`strconv`·`bytes`·`unicode/utf8` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★ **이 주제는 「표준 API 지도」형이라 예측형 비율이 낮다** — 대신
> **경계에서 무엇이 나오나**와 **무엇을 근거로 고르나**를 묻는다.
> ★★★ **성능을 묻는 문항에서는 「빠르다/느리다」로 답하지 마라.**
> **무엇을 몇 번 어떻게 재서 얼마가 나왔나**로 답해야 맞은 것이다.
> 소스는 전부 `go build -trimpath -o prog . && ./prog` 로 던졌다. 모듈 이름은 `ex` 다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 네 가지로 이어 붙이면 (예측)

```go
// t11b.go
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
```

```go
// t11b_test.go
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
```

- 네 함수의 **`allocs/op`** 는 각각 얼마인가?
- `+=` 쪽의 수가 그 값인 **이유**를 한 줄로 적어라.
- `Grow` 를 부른 쪽과 `Join` 쪽이 같은 수인 이유는 무엇인가?
- **`ns/op`** 은 몇 자릿수 차이인가 — 그 수치를 근거로 써도 되는가?

### 2. ★★ `Split` 의 경계 (예측)

```go
// t11d.go
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
```

- `Split("", ",")` 의 **길이**는 얼마인가?
- `Split("", "")` 의 길이는 얼마인가 — 왜 다른가?
- `Split("한글", "")` 은 무엇을 돌려주는가 — 단위는 바이트인가 룬인가?
- `SplitN("a,b,c", ",", 0)` 은 무엇인가?
- `Fields("")` 의 길이는 얼마인가 — `Split` 과 왜 다른가?
- `Cut("kv", "=")` 의 세 반환값은 각각 무엇인가?

### 3. ★★★ `strconv` 가 실패할 때 (예측)

```go
// t11c.go
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
```

- `Atoi(" 42")` 는 되는가?
- `Atoi("9223372036854775808")` 의 **반환값**은 얼마인가 — 0이 아닌 이유는?
- `ParseFloat("1e400", 64)` 의 반환값은 무엇인가?
- 에러 문장 **전문**을 하나 적어라.
- `ErrSyntax` 와 `ErrRange` 를 가르는 기준은 무엇인가 — **반환값이 어떻게 달라지나?**

### 4. ★ `Builder` 를 복사하면 (예측)

```go
// t11g.go
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
```

- 복사 자체는 되는가?
- 출력 **전문**을 적어라 — 스택의 함수 이름과 **종료 코드**까지.
- `Builder` 가 복사를 막는 **이유**는 무엇인가?
- 구조체 필드로 담으려면 어떻게 해야 하는가?

### 5. ★★ `strings.Title` 은 지금 어떤 상태인가 (경계)

```go
// t11e.go
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
```

- `go doc strings.Title` 을 열면 무엇이 보이는가?
- `go build` 와 `go vet` 은 무엇이라고 하는가?
- `"don't shout at o'brien"` 이 무엇이 되는가 — 무엇이 문제인가?
- `ToTitle` 은 대체품인가 — 둘이 실제로 갈리는 입력을 하나 대라.

### 6. `bytes` 는 왜 따로 있나 (왜)

- `[]byte` 를 들고 `strings` 를 쓰면 무엇이 몇 번 일어나는가?
- `strings.Builder` 와 `bytes.Buffer` 는 무엇이 다른가 — 표로 셋만 대라.
- `Builder.String()` 과 `Buffer.String()` 의 차이는 무엇인가?
- 둘을 제네릭으로 합치지 않은 이유는 무엇인가?

### 7. 네 패키지를 고르는 기준 (경계)

아래 일곱 가지 일에 **어느 패키지의 무엇**을 쓸지 고르고 이유를 한 줄씩 적어라.

- ① 로그 한 줄을 루프에서 만든다
- ② 설정 파일의 `key=value` 한 줄을 쪼갠다
- ③ HTTP 바디(`[]byte`)에서 부분 문자열을 찾는다
- ④ 사용자가 입력한 나이를 수로 바꾼다
- ⑤ 사용자 이름이 **20글자**를 넘는지 본다
- ⑥ 제어문자가 섞인 문자열을 로그에 안전하게 찍는다
- ⑦ 문자열을 `io.Reader` 가 필요한 함수에 넘긴다

### 8. 어느 칸이 계약이고 어느 칸이 구현·관찰인가 (경계)

아래 여덟 가지를 **「패키지의 계약」 / 「구현·이 머신의 관찰」** 으로 갈라라.

- ① `Split("", ",")` 이 길이 1이다
- ② `Builder` 의 `allocs/op` 가 15다
- ③ `ErrRange` 일 때 경계값을 돌려준다
- ④ `Builder` 를 복사해 쓰면 패닉이다
- ⑤ `BenchmarkPlus` 가 1밀리초대다
- ⑥ `strings.Title` 이 deprecated 다
- ⑦ `Cut` 이 못 찾으면 `before` 에 원본 전체를 넣는다
- ⑧ 벤치마크 이름 끝에 `-24` 가 붙는다

### 9. 다른 언어와 나란히 놓기 (연결)

- 자바에서 루프 안의 `+` 는 어떻게 컴파일되는가 — Go 와 무엇이 다른가?
- 파이썬의 `join` 은 어느 쪽에 붙어 있는가 — Go 와 방향이 어떻게 다른가?
- Rust 는 Go 의 `strings`/`bytes` 분업을 무엇으로 대신하는가?
- Go 가 deprecated 함수를 **지우지 않는** 이유는 무엇인가?

### 10. 다른 주제와 잇기 (연결)

- `len`·인덱싱·`range`·변환의 정본은 몇 번 주제인가?
- `errors.Is`/`As` 로 `NumError` 를 꺼내는 것의 정본은 몇 번 주제인가?
- `bytes.Buffer` 가 `io.Reader` 인 것의 정본은 몇 번 주제인가?
- `go test -bench` 읽는 법의 정본은 몇 번 주제인가?
- `Buffer.Bytes()` 가 내부 배열을 내주는 위험의 정본은 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

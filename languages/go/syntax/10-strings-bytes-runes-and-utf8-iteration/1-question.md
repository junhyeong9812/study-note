# go/syntax/10 — 문자열·`byte`·`rune`과 UTF-8 순회 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> ★★ **답을 적을 때 「바이트」와 「룬」을 반드시 구분해서 적어라.**
> 섞어 적으면 맞아도 맞은 것이 아니다.
> ★ **「에러가 안 난다」도 답이다** — 이 주제에서 가장 중요한 답이 그것이다.
> 소스는 전부 `go build -trimpath -o prog . && ./prog` 로 던졌다. 모듈 이름은 `ex` 다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 같은 문자열을 세 가지 방법으로 읽으면 (예측)

```go
// t10a.go
package main

import "fmt"

func main() {
	s := "Go한글🙂"
	fmt.Printf("s = %q\n", s)
	fmt.Printf("len(s) = %d   ← 글자 수가 아니라 바이트 수다\n", len(s))

	fmt.Println()
	fmt.Println("인덱싱은 byte(=uint8) 를 준다")
	for i := 0; i < 5; i++ {
		fmt.Printf("  s[%d] = %3d  0x%02x  타입 %T\n", i, s[i], s[i], s[i])
	}

	fmt.Println()
	fmt.Println("range 는 (바이트 위치, rune) 을 준다 — 위치가 1씩 늘지 않는다")
	for i, r := range s {
		fmt.Printf("  i=%2d  r=%q  U+%04X  타입 %T  이 룬은 %d바이트\n",
			i, r, r, r, len(string(r)))
	}
}
```

- `len(s)` 는 얼마인가?
- `s[2]` 는 무엇으로 찍히고 **타입**은 무엇인가?
- `range` 가 주는 **`i` 의 값들**을 순서대로 적어라.
- `r` 의 타입은 무엇으로 찍히는가?

### 2. ★★★ `"한글"[:2]` (예측)

```go
// t10b.go
package main

import (
	"fmt"
	"unicode/utf8"
)

func main() {
	s := "한글"
	fmt.Printf("s = %q   len=%d   ('한' 은 3바이트다)\n", s, len(s))

	cut := s[:2] // 룬 경계가 아닌 자리에서 자른다
	fmt.Println()
	fmt.Println("s[:2] — 경계를 안 맞췄다. 그런데 에러도 패닉도 없다")
	fmt.Printf("  %%q 로               : %q\n", cut)
	fmt.Println("  %s 로 찍으면        : 터미널·폰트에 달린 깨진 네모가 나온다 — 근거로 못 쓴다")
	fmt.Printf("  바이트로            : % x\n", []byte(cut))
	fmt.Printf("  len                 : %d\n", len(cut))
	fmt.Printf("  utf8.ValidString    : %v\n", utf8.ValidString(cut))
	fmt.Printf("  utf8.RuneCountInString : %d\n", utf8.RuneCountInString(cut))

	fmt.Println()
	fmt.Println("range 로 돌면 U+FFFD 가 나온다 — 한 바이트씩 전진한다")
	for i, r := range cut {
		fmt.Printf("  i=%d r=%q U+%04X  utf8.RuneError 인가: %v\n", i, r, r, r == utf8.RuneError)
	}

	fmt.Println()
	fmt.Printf("string([]rune(cut)) = %q   ← 변환하면 U+FFFD 로 굳는다\n", string([]rune(cut)))
	fmt.Printf("경계로 물린 s[:3]   = %q   valid=%v\n", s[:3], utf8.ValidString(s[:3]))
}
```

- 이 프로그램은 어느 단계에서 무엇을 말하는가 — **종료 코드**는?
- `%q` 와 `% x` 로 찍은 결과는 각각 무엇인가 — 이 프로그램이 `%s` 결과를 안 싣는 이유는 무엇인가?
- `utf8.ValidString` 과 `RuneCountInString` 은 각각 무엇을 돌려주는가?
- `range` 는 몇 번 도는가 — 무엇이 나오는가?
- ★ **Rust 에서 같은 코드를 쓰면 무엇이 일어나는가?**

### 3. ★ 그러면 언제 패닉하나 (예측)

```go
// t10c.go
package main

import (
	"fmt"
	"os"
)

func main() {
	s := "한글"
	fmt.Fprintf(os.Stderr, "-- len(s)=%d · s[:2] 는 조용히 통과했다 : %d바이트 --\n", len(s), len(s[:2]))
	n := len(s) + 1
	fmt.Fprintf(os.Stderr, "-- 이제 범위를 넘긴다 : s[:%d] --\n", n)
	_ = s[:n]
	fmt.Fprintln(os.Stderr, "-- 여기는 안 온다 --")
}
```

- 출력 **전문**을 적어라 — 메시지 본문·`파일:줄`·**종료 코드**까지.
- 2번 문항과 이 문항이 갈리는 기준을 **한 줄**로 적어라.

### 4. ★★ 깨진 바이트를 `range` 로 돌면 (예측)

```go
// t10f.go
package main

import (
	"fmt"
	"unicode/utf8"
)

func main() {
	bad := string([]byte{0x41, 0xff, 0xed, 0x95, 0x42})
	fmt.Printf("bad = %q\n", bad)
	fmt.Printf("  len=%d  ValidString=%v\n", len(bad), utf8.ValidString(bad))

	fmt.Println("\nrange 로 돌면")
	for i, r := range bad {
		fmt.Printf("  i=%d r=%q U+%04X  RuneError 인가: %v\n", i, r, r, r == utf8.RuneError)
	}

	fmt.Println("\nDecodeRuneInString 으로 한 칸씩 — size 를 같이 준다")
	for i := 0; i < len(bad); {
		r, size := utf8.DecodeRuneInString(bad[i:])
		fmt.Printf("  i=%d -> r=%q size=%d  RuneError 인가: %v\n", i, r, size, r == utf8.RuneError)
		i += size
	}

	fmt.Printf("\nRuneCountInString = %d\n", utf8.RuneCountInString(bad))
	fmt.Printf("string([]rune(bad)) = %q   len=%d   ← 변환이 U+FFFD 로 굳혀 버린다\n",
		string([]rune(bad)), len(string([]rune(bad))))
}
```

- `range` 는 몇 번 도는가 — 각 반복의 `i` 와 `r` 은?
- `utf8.DecodeRuneInString` 이 돌려주는 `size` 는 깨진 자리에서 얼마인가?
- `RuneCountInString(bad)` 은 얼마인가?
- `string([]rune(bad))` 의 `len` 은 얼마인가 — **왜** 늘어나는가?
- 이 동작은 **명세인가 gc 의 사정인가?**

### 5. ★★ 세는 법이 몇 가지인가 (예측)

```go
// t10d.go
package main

import (
	"fmt"
	"unicode/utf8"
)

func main() {
	s := "hello"
	b := []byte(s)
	b[0] = 'H'
	fmt.Printf("s = %q   []byte 를 고친 뒤 string(b) = %q   ← 원본은 안 바뀐다(복사됐다)\n", s, string(b))

	t := "Go한글"
	r := []rune(t)
	fmt.Printf("\n[]rune(%q) = %v   len=%d\n", t, r, len(r))
	fmt.Print("  각 룬 : ")
	for _, x := range r {
		fmt.Printf("%q ", x)
	}
	fmt.Println()
	fmt.Printf("  string(r) = %q\n", string(r))

	fmt.Println()
	fmt.Printf("세 가지 세는 법이 다 다르다 — %q\n", t)
	fmt.Printf("  len(t)                    = %d  (바이트)\n", len(t))
	fmt.Printf("  len([]rune(t))            = %d  (코드 포인트)\n", len([]rune(t)))
	fmt.Printf("  utf8.RuneCountInString(t) = %d  (코드 포인트 — 변환 없이)\n", utf8.RuneCountInString(t))

	e := "🙂‍↔️"
	fmt.Println()
	fmt.Printf("룬 수도 「사람이 세는 글자」가 아니다 — %q 는\n", e)
	fmt.Printf("  len=%d  룬 수=%d   (사람 눈에는 한 글자다)\n", len(e), utf8.RuneCountInString(e))
	for i, x := range e {
		fmt.Printf("    i=%2d U+%04X\n", i, x)
	}
}
```

- `b[0] = 'H'` 뒤 `s` 는 무엇인가 — 왜인가?
- `"Go한글"` 에 대해 `len`·`len([]rune)`·`RuneCountInString` 은 각각 얼마인가?
- 마지막 문자열은 사람 눈에 몇 글자인가 — `len` 과 룬 수는 각각 얼마인가?
- 그 차이를 만드는 보이지 않는 문자의 이름은 무엇인가?

### 6. ★ `string(65)` (예측)

```go
// t10g.go
package main

import "fmt"

func main() {
	n := 65
	fmt.Printf("string(rune(65)) = %q\n", string(rune(n)))
	fmt.Printf("string(n)        = %q\n", string(n))
}
```

- `go build` 는 통과하는가?
- 두 줄의 출력은 각각 무엇인가?
- `go vet` 의 **메시지 전문**과 **종료 코드**는?
- 명세와 `go vet` 이 **다른 말을 하는** 이유를 층으로 설명하라.

### 7. 문자열을 왜 못 고치나 (왜)

```go
// t10e.go
package main

import "fmt"

func main() {
	s := "hello"
	s[0] = 'H'
	p := &s[0]
	fmt.Println(s, p)
}
```

- 두 줄의 **에러 전문**은 무엇인가?
- 불변이라는 성질이 **가능하게 하는 것** 셋을 대라.
- 그 대가는 무엇인가?
- 고치려면 어떻게 하는가?

### 8. 안전하게 자르는 법 (경계)

```go
// t10i.go
package main

import (
	"fmt"
	"unicode/utf8"
)

// ① 바이트로 그냥 자른다 — 경계를 깰 수 있다.
func cutBytes(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n]
}

// ② 자르되 룬 경계까지 뒤로 물린다.
func cutOnBoundary(s string, n int) string {
	if len(s) <= n {
		return s
	}
	for n > 0 && !utf8.RuneStart(s[n]) {
		n--
	}
	return s[:n]
}

// ③ 룬 개수로 자른다.
func cutRunes(s string, n int) string {
	r := []rune(s)
	if len(r) <= n {
		return s
	}
	return string(r[:n])
}

func main() {
	s := "한글과 English"
	fmt.Printf("원본 %q  len=%d  룬 수=%d\n\n", s, len(s), utf8.RuneCountInString(s))
	fmt.Printf("%-3s %-14s %-6s %-14s %-6s\n", "n", "① 그냥", "valid", "② 경계로", "valid")
	for _, n := range []int{2, 4, 5, 7, 10} {
		a, b := cutBytes(s, n), cutOnBoundary(s, n)
		fmt.Printf("%-3d %-14q %-6v %-14q %-6v\n", n, a, utf8.ValidString(a), b, utf8.ValidString(b))
	}
	fmt.Println()
	for _, n := range []int{1, 3, 5} {
		fmt.Printf("③ cutRunes(s, %d) = %q\n", n, cutRunes(s, n))
	}
}
```

- `n=4` 일 때 ①과 ②는 각각 무엇을 돌려주는가?
- ②의 되돌리기 루프는 **최대 몇 번** 도는가 — 왜 그 수인가?
- ①·②·③ 중 「화면에 몇 글자」를 제한하는 것은 어느 것인가?
- 셋 중 **화면 폭을 정확히 맞추는** 것은 무엇인가?

### 9. 어느 칸이 명세이고 어느 칸이 도구·구현의 사정인가 (경계)

아래 여덟 가지를 **「명세 보장」 / 「도구·구현의 사정」** 으로 갈라라.

- ① `len("한")` 이 3이다
- ② 경계를 어긴 자르기가 패닉하지 않는다
- ③ 범위를 넘긴 자르기가 패닉한다
- ④ 깨진 바이트에서 `U+FFFD` 가 나오고 한 바이트 전진한다
- ⑤ `string(65)` 이 `"A"` 다
- ⑥ `go vet` 이 ⑤를 잡는다
- ⑦ `&s[0]` 이 불법이다
- ⑧ `[]rune(s)` 결과의 `cap` 이 룬 수와 같다

### 10. 네 언어의 「문자열 한 칸」이 무엇인가 (연결)

- Go·Rust·파이썬·자바에서 **문자열의 기본 단위**는 각각 무엇인가?
- 그중 **경계를 어긴 자르기를 런타임이 막는** 언어는 어느 것인가?
- C 는 길이를 어디에 두는가 — Go 와 무엇이 다른가?
- 「이모지 하나」를 각 언어에서 세면 몇으로 나오는가?

### 11. 다른 주제와 잇기 (연결)

- `byte`=`uint8`·`rune`=`int32` 라는 사실의 정본은 몇 번 주제인가?
- UTF-8 인코딩 자체의 정본은 어느 갈래인가?
- `range` 문 전체의 정본은 몇 번 주제인가?
- `strings.Builder`·`strconv` 의 정본은 몇 번 주제인가?
- 「문자열이 맵 키가 된다」는 사실이 기대는 주제는 몇 번인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

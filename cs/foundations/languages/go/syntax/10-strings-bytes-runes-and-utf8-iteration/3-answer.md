# go/syntax/10 — 문자열·`byte`·`rune`과 UTF-8 순회 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★★ **이 파일의 답은 「바이트냐 룬이냐」로 거의 다 갈린다.**
> ★ **근거로 읽을 칸** — `len` · 인덱스별 바이트 값 · `range` 가 준 **바이트 위치** ·
> `utf8.ValidString` 의 참/거짓 · 패닉 메시지 본문 · 컴파일 에러 문장 · `go vet` 의 **종료 코드**.
> **근거로 읽지 않을 칸** — 패닉 스택의 **주소 오프셋** · `%s` 로 찍은 깨진 바이트가
> **화면에 어떻게 보이는가**(터미널·폰트의 문제다 — `%q` 와 `% x` 를 보라) ·
> `[]rune` 결과의 **`cap`**(명세가 "implementation-specific" 이라 적는다).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `len` 은 **12**, `s[2]` 는 **237**, `range` 의 `i` 는 **0·1·2·5·8**

**출력**

```text
===== 소스: t10a.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
s = "Go한글🙂"
len(s) = 12   ← 글자 수가 아니라 바이트 수다

인덱싱은 byte(=uint8) 를 준다
  s[0] =  71  0x47  타입 uint8
  s[1] = 111  0x6f  타입 uint8
  s[2] = 237  0xed  타입 uint8
  s[3] = 149  0x95  타입 uint8
  s[4] = 156  0x9c  타입 uint8

range 는 (바이트 위치, rune) 을 준다 — 위치가 1씩 늘지 않는다
  i= 0  r='G'  U+0047  타입 int32  이 룬은 1바이트
  i= 1  r='o'  U+006F  타입 int32  이 룬은 1바이트
  i= 2  r='한'  U+D55C  타입 int32  이 룬은 3바이트
  i= 5  r='글'  U+AE00  타입 int32  이 룬은 3바이트
  i= 8  r='🙂'  U+1F642  타입 int32  이 룬은 4바이트
(exit 0)
```

**왜 그런가**

- `"Go한글🙂"` 은 `G`(1) + `o`(1) + `한`(3) + `글`(3) + `🙂`(4) = **12바이트**다.
  명세: "**The number of bytes is called the length of the string.**"
- `s[2]` 는 **`237`(`0xed`)** 이고 타입이 **`uint8`** 이다 — `한` 이 아니라 **한 의 첫 바이트**다.
  명세: "**A string's bytes can be accessed by integer indices 0 through len(s)-1.**"
- `range` 의 `i` 는 **0, 1, 2, 5, 8** 이다. **1씩 늘지 않는다** — 다음 코드 포인트의 **첫 바이트 위치**다.

  > **the index value will be the index of the first byte of successive UTF-8-encoded
  > code points in the string**

- `r` 의 타입은 **`int32`** 로 찍힌다. `rune` 은 `int32` 의 **별명**일 뿐이라 `%T` 가 본래 이름을 준다.
- ★★ 그래서 **`s[i]` 로 글자를 꺼낼 수 없다.** 글자가 필요하면 `range` 이거나 `[]rune` 이다.

### 2. **아무 일도 일어나지 않는다** — 종료 코드 0

**출력**

```text
===== 소스: t10b.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
s = "한글"   len=6   ('한' 은 3바이트다)

s[:2] — 경계를 안 맞췄다. 그런데 에러도 패닉도 없다
  %q 로               : "\xed\x95"
  %s 로 찍으면        : 터미널·폰트에 달린 깨진 네모가 나온다 — 근거로 못 쓴다
  바이트로            : ed 95
  len                 : 2
  utf8.ValidString    : false
  utf8.RuneCountInString : 2

range 로 돌면 U+FFFD 가 나온다 — 한 바이트씩 전진한다
  i=0 r='�' U+FFFD  utf8.RuneError 인가: true
  i=1 r='�' U+FFFD  utf8.RuneError 인가: true

string([]rune(cut)) = "��"   ← 변환하면 U+FFFD 로 굳는다
경계로 물린 s[:3]   = "한"   valid=true
(exit 0)
```

**왜 그런가**

- 종료 코드가 **0** 이다. **에러도 패닉도 경고도 없다.** `go vet` 도 이 꼴을 안 본다.
- 세 가지로 찍은 결과.

| 동사 | 결과 | 읽는 법 |
|---|---|---|
| `%q` | `"\xed\x95"` | ★ **진단은 이것으로 한다.** 깨진 바이트가 그대로 보인다 |
| `% x` | `ed 95` | 바이트를 직접 본다 |
| `%s` | ★ **싣지 않았다** | 터미널·폰트에 달린 깨진 네모다. 게다가 **실으면 문서가 유효한 UTF-8 이 아니게 된다** |

- ★ `%s` 를 안 실은 이유가 이 주제의 성질을 그대로 보여 준다 — **깨진 바이트를 그대로 내보내면
  그것을 받아 적은 파일까지 깨진다.** 이 배치에서 실제로 그렇게 됐고, 캡처 파일을 읽는 단계에서 잡혔다.

- `utf8.ValidString(cut)` 이 **`false`**, `RuneCountInString(cut)` 이 **2** 다.
  ★ **「유효한가」와 「몇 개인가」는 다른 질문**이다 — 깨진 바이트도 하나씩 세어진다.
- `range` 는 **두 번** 돌고 둘 다 **`U+FFFD`** 다. 한 바이트씩 전진했다.
- ★★★ **Rust 에서는 같은 코드가 패닉한다.**
  [`../../../rust/syntax/15-slices-ranges-and-utf8-boundaries/`](../../../rust/syntax/15-slices-ranges-and-utf8-boundaries/)의
  핵심 문장이 「`&s[0..1]` 은 **실행 패닉**」이고, 메시지가 **`it is inside '한' (bytes 0..3)`** 처럼
  **처방까지** 준다.
- ★★ 갈린 이유는 **타입이 든 불변식**이다. Rust 의 `&str` 은 「항상 올바른 UTF-8」을 약속하므로
  그것을 깨는 연산을 런타임이 막아야 한다. Go 의 `string` 은 **그냥 바이트 열**이라 약속할 것이 없다.
- **Go 가 얻은 것** — 아무 바이트 열이나 `string` 에 담을 수 있다.
  **잃은 것** — 「`string` 이면 유효하다」는 보증.

### 3. `s[:7]` 은 **패닉**이다 — 검사하는 것은 「범위」뿐이다

**출력**

```text
===== 소스: t10c.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
-- len(s)=6 · s[:2] 는 조용히 통과했다 : 2바이트 --
-- 이제 범위를 넘긴다 : s[:7] --
panic: runtime error: slice bounds out of range [:7] with length 6

goroutine 1 [running]:
main.main()
	ex/t10c.go:13 +0xd8
(exit 2)
```

**왜 그런가**

- `panic: runtime error: slice bounds out of range [:7] with length 6` · **종료 코드 2**.
- 갈리는 기준 한 줄 — ★★★ **Go 는 「인덱스가 0..len 안인가」만 검사하고
  「그 자리가 룬 경계인가」는 검사하지 않는다.**
- 그래서 같은 슬라이스 식이 **한쪽은 패닉, 한쪽은 무반응**이다. 두 가지를 섞으면
  「자르기는 안전하다」는 틀린 결론이 나온다.

### 4. **다섯 번** 돌고, 깨진 자리는 `size=1` 이며, 변환하면 **11바이트**가 된다

**출력**

```text
===== 소스: t10f.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
bad = "A\xff\xed\x95B"
  len=5  ValidString=false

range 로 돌면
  i=0 r='A' U+0041  RuneError 인가: false
  i=1 r='�' U+FFFD  RuneError 인가: true
  i=2 r='�' U+FFFD  RuneError 인가: true
  i=3 r='�' U+FFFD  RuneError 인가: true
  i=4 r='B' U+0042  RuneError 인가: false

DecodeRuneInString 으로 한 칸씩 — size 를 같이 준다
  i=0 -> r='A' size=1  RuneError 인가: false
  i=1 -> r='�' size=1  RuneError 인가: true
  i=2 -> r='�' size=1  RuneError 인가: true
  i=3 -> r='�' size=1  RuneError 인가: true
  i=4 -> r='B' size=1  RuneError 인가: false

RuneCountInString = 5
string([]rune(bad)) = "A���B"   len=11   ← 변환이 U+FFFD 로 굳혀 버린다
(exit 0)
```

**왜 그런가**

- 바이트는 `41 ff ed 95 42` 다. `range` 는 **다섯 번** 돈다 —
  `A` · `U+FFFD` · `U+FFFD` · `U+FFFD` · `B`.
- `0xff` 는 **UTF-8 에 없는 바이트**이고, `ed 95` 는 **3바이트 글자의 앞 두 바이트**라 미완성이다.
  둘 다 「invalid UTF-8 sequence」이므로 같은 처리를 받는다.
- 명세가 정한다.

  > **If the iteration encounters an invalid UTF-8 sequence, the second value will be 0xFFFD,
  > the Unicode replacement character, and the next iteration will advance a single byte in the string.**

- `utf8.DecodeRuneInString` 은 깨진 자리에서 **`size=1`** 을 준다. `range` 가 안에서 하는 일과 같다.
- `RuneCountInString(bad)` 은 **5** 다 — 깨진 바이트를 **하나씩 센다.**
- ★★★ `string([]rune(bad))` 의 `len` 이 **11** 이다. `U+FFFD` 가 **3바이트**짜리라
  깨진 바이트 3개가 각각 3바이트로 부풀었다(`1 + 3 + 3 + 3 + 1 = 11`).
  **원래 바이트는 영영 사라진다** — 바이트를 지켜야 하면 `[]rune` 변환을 하면 안 된다.
- ★ 이 동작은 **명세**다. gc 의 사정이 아니다.

### 5. `s` 는 **안 바뀌고**, 세는 법 셋이 **8 · 4 · 4**, 마지막은 **13 · 4 · 1**

**출력**

```text
===== 소스: t10d.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
s = "hello"   []byte 를 고친 뒤 string(b) = "Hello"   ← 원본은 안 바뀐다(복사됐다)

[]rune("Go한글") = [71 111 54620 44544]   len=4
  각 룬 : 'G' 'o' '한' '글' 
  string(r) = "Go한글"

세 가지 세는 법이 다 다르다 — "Go한글"
  len(t)                    = 8  (바이트)
  len([]rune(t))            = 4  (코드 포인트)
  utf8.RuneCountInString(t) = 4  (코드 포인트 — 변환 없이)

룬 수도 「사람이 세는 글자」가 아니다 — "🙂\u200d↔️" 는
  len=13  룬 수=4   (사람 눈에는 한 글자다)
    i= 0 U+1F642
    i= 4 U+200D
    i= 7 U+2194
    i=10 U+FE0F
(exit 0)
```

**왜 그런가**

- `b := []byte(s)` 는 **새 배열을 잡는다.** 그래서 `b[0]` 을 고쳐도 `s` 는 `"hello"` 그대로다.
  문자열이 **불변**이므로 공유하면 그 불변식이 깨진다 — 복사가 강제된다.
- `"Go한글"` 에서 — `len` **8** · `len([]rune)` **4** · `RuneCountInString` **4**.
  뒤의 둘은 같지만 **`RuneCountInString` 은 배열을 안 잡는다.** 세기만 할 거면 그쪽이다.
- ★★★ 마지막 문자열은 **사람 눈에 한 글자**인데 `len` **13** · 룬 수 **4** 다.

| | 값 | 무엇을 센 것인가 |
|---|---|---|
| `len` | 13 | 바이트 |
| `RuneCountInString` | 4 | 코드 포인트 |
| 사람이 세는 글자 | 1 | **자소 묶음** — Go 표준에 세는 장치가 없다 |

- 그 차이를 만든 보이지 않는 문자는 **ZWJ(zero-width joiner, `U+200D`)** 다.
  출력에 `U+200D` 로 찍힌 줄이 그것이고, 뒤의 `U+FE0F` 는 **변이 선택자**다.
- ★ 그래서 **「글자 수」라는 말은 Go 에서 세 가지를 뜻할 수 있다.** 어느 쪽인지 적지 않으면 틀린다.

### 6. **빌드는 통과하고 `go vet` 이 종료 코드 1로 잡는다**

**출력**

```text
===== 소스: t10g.go =====
package main

import "fmt"

func main() {
	n := 65
	fmt.Printf("string(rune(65)) = %q\n", string(rune(n)))
	fmt.Printf("string(n)        = %q\n", string(n))
}
===== 명령: go build -trimpath -o prog . && ./prog =====
string(rune(65)) = "A"
string(n)        = "A"
(exit 0)
===== 명령: go vet ./... =====
t10g.go:8:40: conversion from int to string yields a string of one rune, not a string of digits
(exit 1)
```

**왜 그런가**

- `go build` 는 **통과**한다. 두 줄 다 **`"A"`** 로 찍힌다 — `string(65)` 는 `"65"` 가 아니다.
- 명세가 그 변환을 적법이라고 적는다.

  > **Finally, for historical reasons, an integer value may be converted to a string type.**

- `go vet` 은 **종료 코드 1** 과 함께 이렇게 말한다 —
  `conversion from int to string yields a string of one rune, not a string of digits`.
- ★★ **층이 다르다.** 명세는 「**적법한가**」를 말하고 vet 은 「**뜻한 바일 것 같은가**」를 말한다.
  명세는 지금도 이 변환을 허용하고, vet 은 **1.15**부터 말린다. 둘은 충돌이 아니다.
- 고치는 법 — 숫자의 **글자 표현**이 필요하면 `strconv.Itoa(n)`,
  **코드 포인트**를 글자로 바꾸려면 `string(rune(n))` 이라고 **뜻을 적는다.**
- ★ 이 주제에서 **`go vet` 이 실제로 잡아 주는 유일한 자리**다. CI 에 넣을 값이 여기에 있다.

### 7. 불변이라서 — 그리고 그 덕에 셋이 가능해진다

**출력**

```text
===== 소스: t10e.go =====
package main

import "fmt"

func main() {
	s := "hello"
	s[0] = 'H'
	p := &s[0]
	fmt.Println(s, p)
}
===== 명령: go build -trimpath -o prog . =====
# ex
./t10e.go:7:2: cannot assign to s[0] (neither addressable nor a map index expression)
./t10e.go:8:8: invalid operation: cannot take address of s[0] (value of type byte)
(exit 1)
```

**왜 그런가**

- 두 줄 다 컴파일 에러다.
  - `cannot assign to s[0] (neither addressable nor a map index expression)`
  - `invalid operation: cannot take address of s[0] (value of type byte)`
- 명세가 둘 다 적어 둔다.

  > **Strings are immutable: once created, it is impossible to change the contents of a string.**
  > … **It is illegal to take the address of such an element; if s[i] is the i'th byte of a string,
  > &s[i] is invalid.**

- 불변이라서 가능해지는 것 셋.
  - ① **맵 키가 된다** — 키가 나중에 바뀌면 해시가 어긋난다(목록의 **09번 주제**).
  - ② **복사가 싸다** — 헤더 두 칸(포인터 + 길이)만 복사하고 바이트는 공유한다.
  - ③ **공유해도 안전하다** — 여러 고루틴이 같은 문자열을 읽어도 레이스가 없다.
- 대가 — **이어 붙일 때마다 새 문자열**이 생긴다. 그래서 `strings.Builder` 가 필요하다(목록의 **11번 주제**).
- 고치려면 `[]byte` 나 `[]rune` 으로 **바꿔 고치고 다시 문자열로** 만든다. 복사가 두 번 든다.

### 8. `n=4` 에서 ①은 **깨진 것**, ②는 **`"한"`** — 되돌리기는 **최대 3번**

**출력**

```text
===== 소스: t10i.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
원본 "한글과 English"  len=17  룬 수=11

n   ① 그냥           valid  ② 경계로          valid 
2   "\xed\x95"     false  ""             true  
4   "한\xea"        false  "한"            true  
5   "한\xea\xb8"    false  "한"            true  
7   "한글\xea"       false  "한글"           true  
10  "한글과 "         true   "한글과 "         true  

③ cutRunes(s, 1) = "한"
③ cutRunes(s, 3) = "한글과"
③ cutRunes(s, 5) = "한글과 E"
(exit 0)
```

**왜 그런가**

- `"한글과 English"` 는 `한`(3) `글`(3) `과`(3) 공백(1) … 이다. `n=4` 는 **`글` 의 한가운데**다.
  - ① `s[:4]` → `"한\xea"` · `valid=false`
  - ② 경계까지 물려 `s[:3]` → `"한"` · `valid=true`
- ★ 되돌리기 루프는 **최대 3번** 돈다. UTF-8 에서 한 글자는 **최대 4바이트**이고
  이어지는 바이트가 **최대 3개**이기 때문이다.
- 「화면에 몇 글자」에 가까운 것은 **③(룬 개수)** 이다. ①·②는 **바이트**를 제한한다.
- ★★ 그런데 **셋 다 화면 폭을 정확히 맞추지 못한다.** 한글·CJK 는 폭이 2이고
  이모지 조합은 룬 여럿이 폭 2를 쓴다. **폭은 또 다른 층**이고 Go 표준에 그 장치가 없다.
  (이 문서 (4)절의 표가 실제로 어긋나 보이는 것이 그 증거다.)

### 9. 명세는 ①②③④⑤⑦, 도구·구현의 사정은 ⑥⑧

**출력** — 없음(경계 문항).

**왜 그런가**

| | 주장 | 판정 | 근거 |
|---|---|---|---|
| ① | `len("한")` 이 3 | **명세 보장** | 문자열은 바이트 열이고 `len` 은 바이트 수다 |
| ② | 경계 위반이 패닉 안 함 | **명세 보장** | 슬라이스 식은 **범위만** 검사한다 |
| ③ | 범위 초과가 패닉 | **명세 보장** | Slice expressions 의 인덱스 규칙 |
| ④ | `U+FFFD` + 1바이트 전진 | **명세 보장** | RangeClause 의 string 절 |
| ⑤ | `string(65)` 이 `"A"` | **명세 보장** | "for historical reasons …" |
| ⑥ | `go vet` 이 ⑤를 잡는다 | **도구의 판단** | 1.15부터. **명세는 여전히 적법이라 한다** |
| ⑦ | `&s[0]` 이 불법 | **명세 보장** | "It is illegal to take the address of such an element" |
| ⑧ | `[]rune(s)` 의 `cap` 이 룬 수와 같다 | **구현(gc)** | 명세: "The capacity … is implementation-specific and may be larger" |

- ★★ ②와 ③이 **같은 문법의 다른 검사**라는 점이 이 표의 핵심이다.
  「자르기가 검사된다」를 뭉뚱그려 외우면 둘 중 하나를 반드시 틀린다.
- ★ ⑥은 **명세와 도구가 다른 말을 하는** 드문 자리다. 충돌이 아니라 **층이 다른 것**이다.

### 10. 네 언어의 기본 단위가 전부 다르다

**출력** — 없음(연결 문항).

**왜 그런가**

| 물음 | **Go** | **Rust** | **파이썬** | **자바** |
|---|---|---|---|---|
| 문자열의 기본 단위 | **바이트**(UTF-8) | **바이트**(UTF-8) | **코드 포인트** | **UTF-16 코드 단위** |
| `len`/`length` 가 세는 것 | 바이트 | 바이트 | 코드 포인트 | 코드 단위 |
| 경계 위반 자르기 | ★ **무반응** | ★ **런타임 패닉** | 해당 없음(인덱스가 코드 포인트) | 해당 없음(코드 단위 인덱스) |
| 인덱싱이 주는 것 | `byte` | ★ **컴파일 에러**(`s[0]` 자체가 안 된다) | 길이 1 `str` | `char`(코드 단위) |
| 「이모지 하나」를 세면 | 4바이트 · 1룬 | 4바이트 · 1 `char` | **1** | **2** |

- **경계 위반을 런타임이 막는 것은 Rust 뿐**이다. `&str` 이 「항상 올바른 UTF-8」이라는
  **불변식을 타입으로 들고** 있기 때문이다.
- **C 는 길이를 어디에 두나** — **아무 데도 안 둔다.** 끝에 `\0` 을 놓고 **셀 때마다 훑는다**
  ([`../../../c/syntax/20-null-terminated-strings-and-string-literals/`](../../../c/syntax/20-null-terminated-strings-and-string-literals/)).
  ★ **Go 는 길이를 헤더에 들고 다닌다** — `len` 이 `O(1)` 이고,
  **`\0` 이 그냥 한 바이트**라 문자열 안에 들어가도 아무 문제가 없다.
  C 에서는 그것이 **문자열을 잘라 먹는** 사고다.
- ★★ 「이모지 하나」에서 자바의 **2**가 가장 자주 사고를 낸다 —
  `length()` 가 코드 단위라 **서로게이트 쌍이 둘로 세어진다**
  ([`../../../java/syntax/35-string/`](../../../java/syntax/35-string/)).
  Go 는 **1룬**으로 옳게 세지만, **ZWJ 로 묶인 이모지에서는 Go 도 틀린다**(5번 문항).

### 11. 다른 주제와 잇기

**출력** — 없음(연결 문항).

**왜 그런가**

- **`byte`=`uint8` · `rune`=`int32`** — [`../04-numeric-types-conversions-and-integer-division/`](../04-numeric-types-conversions-and-integer-division/).
  **그쪽은 별명과 명시 변환 규칙까지**, 여기는 **그 별명이 문자열 위에서 무엇을 뜻하나**부터다.
- **UTF-8 인코딩 자체** — [`../../../../data-representation/`](../../../../data-representation/).
  **그쪽은 비트 배치와 왜 그 바이트인가까지**, 여기는 **Go 문법이 그것을 어떻게 내주나**부터다.
- **`range` 문 전체** — 목록의 **14번 주제**(`for` 의 네 형태). 맵·채널·정수 `range` 가 거기다.
- **`strings.Builder`·`strconv`·`unicode/utf8` 의 API** —
  [`../11-strings-strconv-bytes-and-unicode-utf8/`](../11-strings-strconv-bytes-and-unicode-utf8/).
  **여기는 언어가 주는 것까지**, 그쪽은 **그 위에 선 네 패키지**부터다.
- **「문자열이 맵 키가 된다」** — [`../09-maps-declaration-comma-ok-delete-and-iteration-order/`](../09-maps-declaration-comma-ok-delete-and-iteration-order/).
  키가 **비교 가능해야** 하고, 문자열은 **불변이라 그 조건을 만족**한다.

---

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행 1회** | 재실행 결과가 `diff -rq` 로 **동일** |
| 판 확인 | `go version` · `go env GOOS GOARCH GOVERSION` | 1 | `go1.27.1 linux/amd64` |
| 바이트·룬 격자 (`t10h`) | `go build && ./prog` | 1 | 선두/이어지는 바이트 구분 · `RuneStart` 참/거짓 |
| `len`·인덱싱·`range` (`t10a`) | 〃 | 1 | `len` 12 · `s[2]`=237(`uint8`) · `i`=0,1,2,5,8 |
| ★★★ 경계 위반 자르기 (`t10b`) | 〃 | 1 | **exit 0** · `ValidString=false` · `U+FFFD` 2회 |
| ★ 범위 초과 (`t10c`) | 〃 | 1 | `slice bounds out of range [:7] with length 6` · **exit 2** |
| 깨진 UTF-8 순회 (`t10f`) | 〃 | 1 | 5회 순회 · `size=1` · 변환 뒤 11바이트 |
| 변환 복사 · 세는 법 셋 (`t10d`) | 〃 | 1 | 8 / 4 / 4 · 이모지는 13 / 4 |
| 불변성 (`t10e`) | `go build` | 1 | 컴파일 에러 2줄 · exit 1 |
| ★ `string(int)` (`t10g`) | `go build && ./prog` · `go vet ./...` | 각 1 | 빌드 통과 · **vet exit 1** |
| 안전하게 자르기 (`t10i`) | `go build && ./prog` | 1 | ① 4건 invalid · ② 전부 valid |
| 문자열의 나머지 표면 (`t10j`) | 〃 | 1 | `"Z" < "a"` 참 · 제로값 `""` |
| 형태 모음 (`t10form`) | 〃 | 1 | 위 규칙들이 한 프로그램에서 동작 |

**구현·도구에 달린 항목**(판이 오르면 **다시 찍어야 하는** 것)

| 항목 | 왜 |
|---|---|
| `go vet` 이 `string(int)` 를 **잡는 것** | **도구의 검사 목록**(1.15부터). 명세는 여전히 적법이라 한다 |
| `[]rune(s)` 결과의 **`cap`** | 명세가 "implementation-specific and may be larger" 라고 적는다 |
| 패닉 스택의 **주소 오프셋**(`+0xd8` 등) | 빌드마다 바뀔 수 있다 |
| `%s` 로 찍은 깨진 바이트가 **화면에 어떻게 보이는가** | 터미널·폰트의 문제다. 그래서 `%q`·`% x` 를 같이 실었다 |
| `"한글과 English"` 표의 **칸 정렬이 어긋나 보이는 것** | 한글이 **폭 2**라서다. `%-14q` 는 룬 수로 맞춘다 |
| 「`m[string(b)]` 이 최적화로 변환을 건너뛴다」 | ★ **안 던져 봤다.** 정본은 목록의 **52번 주제**다 |
| 정규화(NFC/NFD) 동작 | ★ **표준에 없다.** `golang.org/x/text` 가 필요하고 이 문서는 쓰지 않았다 |

★ **다시 찍는 법** — `capture.sh` 를 그대로 돌리고 `diff -rq` 한다. 이 주제에는 흔들리는 블록이 없다.

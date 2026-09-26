# go/syntax/10 — 문자열·`byte`·`rune`과 UTF-8 순회 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Go 명세](https://go.dev/ref/spec)의 String types · Index expressions ·
> Slice expressions · For statements(RangeClause) · Conversions to and from a string type 절.\
> 웹이 아니라 **이 툴체인이 들고 있는 ``$(go env GOROOT)/doc/go_spec.html`` 을 열어** 인용했다.
> 그 파일의 머리는 「**Language version go1.27 (May 26, 2026)**」이다.
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> ★★★ **이 주제의 본체는 「바이트·룬 격자」 그림이다.** 문자열이 **바이트 열**이라는 한 사실에서
> `len`·인덱싱·`range`·자르기의 결과가 전부 따라 나온다. 그림을 먼저 보고 문장을 읽어라.
> ★★ **이 주제의 핵심 대비는 「경계를 어긴 자르기」다** — Rust 는 **패닉**인데 **Go 는 아무 일도 없다.**
> (2)절이 그것을 던져서 확인한다.
> **버전** — 여기 나오는 모든 동작은 **1.0**부터 같다.
> `go vet` 이 `string(int)` 를 잡는 것은 **1.15**부터다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 명세로, 출력은 실행으로 접지했다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | `go_spec.html` 원문 인용 |
| **구현(gc)·도구** | gc·`go vet` 이 그렇게 하는 것 | vet 의 종료 코드 · 변환 비용 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 실행 출력 · 컴파일 에러 문장 |

★ 이 주제는 **명세가 유난히 많이 정해 둔** 자리다. `U+FFFD` 가 나오는 것도, 한 바이트씩 전진하는 것도
**명세의 문장**이지 gc 의 사정이 아니다. 그래서 **층을 가르기는 쉽고, 사람이 틀리는 것은 바이트와 룬을 섞는 쪽**이다.

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
| **흔들린다** | 패닉 스택의 **주소 오프셋**(`+0xd8`) | 빌드마다 바뀔 수 있다 |
| **터미널에 따라 달라 보인다** | `%s` 로 찍은 **깨진 바이트**(`�` 로 보이는 칸) | 폰트·터미널의 문제다. **`%q` 와 `% x` 로 같이 찍어** 못을 박았다 |
| **판이 바뀌면 바뀐다** | `[]rune` 변환 결과의 **`cap`** | 명세가 "implementation-specific" 이라고 적는다 |
| **판이 바뀌면 바뀐다** | `go vet` 이 `string(int)` 를 **잡는다**는 것 | 도구의 검사 목록이다(1.15부터) |
| 안 흔들린다 | **`len`**·인덱스별 바이트 값·`range` 가 주는 **바이트 위치** | 명세가 정한다 |
| 안 흔들린다 | 경계 위반이 **패닉하지 않는다**는 것 | 명세가 정한다 — 이 주제의 결론이다 |
| 안 흔들린다 | `U+FFFD` 가 나오고 **한 바이트씩 전진**하는 것 | 명세의 문장이다 |
| 안 흔들린다 | 패닉 **메시지 본문**·`파일:줄`·종료 코드 | 런타임이 정한다 |
| 안 흔들린다 | 컴파일 에러 문장 본문 | 같은 소스·같은 판이면 같다 |

## 한눈에 — 쉽게 말하면

**「자막 필름 한 롤.」**

문자열은 **글자의 배열이 아니라 바이트의 배열**이다. 필름의 칸은 **바이트**이고,
사람이 보는 **글자 하나가 칸을 하나 쓸 수도 넷 쓸 수도** 있다.

| 비유 | 실체 |
|---|---|
| 필름의 칸 하나 | 바이트 — `s[i]` 가 주는 것 |
| 칸을 세는 것 | `len(s)` |
| **글자**를 세는 것 | `utf8.RuneCountInString(s)` |
| 필름을 **글자 단위로** 돌리는 것 | `for i, r := range s` |
| 글자 한가운데서 필름을 **가위로 자르는 것** | `s[:2]` — **막는 사람이 없다** |
| 잘린 반쪽을 비추면 나오는 **깨진 네모** | `U+FFFD` (`utf8.RuneError`) |
| 필름은 **덧쓸 수 없다** | 문자열은 불변 — `s[0] = 'H'` 는 컴파일 에러 |

```text
   s := "A한🙂"

   바이트 :   0     1     2     3     4     5     6     7        len(s) = 8
            +-----+-----+-----+-----+-----+-----+-----+-----+
            | 41  | ed  | 95  | 9c  | f0  | 9f  | 99  | 82  |
            +-----+-----+-----+-----+-----+-----+-----+-----+
   비트    : 0xxx  110x  10xx  10xx  1111  10xx  10xx  10xx
              ^      ^                 ^
   룬 시작 :  A      한                🙂                        룬 수 = 3

   s[1]         -> 0xed          (byte 하나 — 글자가 아니다)
   range 의 i   -> 0, 1, 4       (1씩 늘지 않는다)
   s[:2]        -> "A\xed"       ★ 에러도 패닉도 없다. 그냥 깨진 문자열이다
```

- ★★★ **이 그림이 이 주제의 전부다.** `len`·인덱싱·`range`·자르기가 전부 여기서 읽힌다.
- ★★ **「이어지는 바이트」는 전부 `10xxxxxx`** 로 시작한다. 그래서 **한 바이트만 보고도
  「여기가 글자 시작인가」를 알 수 있다** — `utf8.RuneStart` 가 그 한 줄이다.

> **바이트(byte)** — 8비트. Go 에서 `byte` 는 `uint8` 의 별명이다.

> **룬(rune)** — 유니코드 **코드 포인트** 하나. Go 에서 `rune` 은 `int32` 의 별명이다.\
> 「글자」가 아니다 — 사람이 한 글자로 보는 것이 룬 여럿일 수 있다((3)절).

> **UTF-8** — 코드 포인트를 1\~4바이트로 적는 인코딩. 인코딩 자체의 정본은
> [`../../../../data-representation/`](../../../../data-representation/)다.

> **U+FFFD (replacement character)** — 「여기 뭔가 깨졌다」를 뜻하는 유니코드 문자.
> Go 에서는 `utf8.RuneError` 라는 이름이 붙어 있다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **한글 문자열의 `len` 은 얼마인가** — 인덱싱과 `range` 가 왜 다른 것을 주나.
2. **글자 한가운데서 자르면 무엇이 일어나나** — Rust 는 패닉인데 Go 는?
3. **깨진 UTF-8 을 `range` 로 돌면 무엇이 나오나** — 그것이 명세인가 구현인가.

★ UTF-8 인코딩의 원리(비트 배치·코드 포인트 범위)는
[`../../../../data-representation/`](../../../../data-representation/)가 정본이다.
여기는 **Go 가 그 바이트를 어떤 문법으로 내주나**만 본다.

## 동작 방식

### (0) ★★★ 바이트·룬 격자 — 이 주제의 본체

**언제 쓰나** — 문자열을 만질 때마다. 이 그림을 머릿속에 못 그리면 나머지가 전부 헷갈린다.

```text
===== 소스: t10h.go =====
package main

import (
	"fmt"
	"unicode/utf8"
)

func main() {
	s := "A한🙂"
	starts := map[int]rune{}
	for i, r := range s {
		starts[i] = r
	}
	fmt.Printf("s = %q   len=%d   룬 수=%d\n\n", s, len(s), utf8.RuneCountInString(s))
	for i := 0; i < len(s); i++ {
		if r, ok := starts[i]; ok {
			fmt.Printf("  바이트 %d : 0x%02x  %08b   <- 룬 시작 %q U+%04X (%d바이트)\n",
				i, s[i], s[i], r, r, utf8.RuneLen(r))
		} else {
			fmt.Printf("  바이트 %d : 0x%02x  %08b        이어지는 바이트 (10xxxxxx)\n",
				i, s[i], s[i])
		}
	}
	fmt.Println()
	fmt.Printf("  utf8.RuneStart(s[1]) = %v   utf8.RuneStart(s[2]) = %v\n",
		utf8.RuneStart(s[1]), utf8.RuneStart(s[2]))
}
===== 명령: go build -trimpath -o prog . && ./prog =====
s = "A한🙂"   len=8   룬 수=3

  바이트 0 : 0x41  01000001   <- 룬 시작 'A' U+0041 (1바이트)
  바이트 1 : 0xed  11101101   <- 룬 시작 '한' U+D55C (3바이트)
  바이트 2 : 0x95  10010101        이어지는 바이트 (10xxxxxx)
  바이트 3 : 0x9c  10011100        이어지는 바이트 (10xxxxxx)
  바이트 4 : 0xf0  11110000   <- 룬 시작 '🙂' U+1F642 (4바이트)
  바이트 5 : 0x9f  10011111        이어지는 바이트 (10xxxxxx)
  바이트 6 : 0x99  10011001        이어지는 바이트 (10xxxxxx)
  바이트 7 : 0x82  10000010        이어지는 바이트 (10xxxxxx)

  utf8.RuneStart(s[1]) = true   utf8.RuneStart(s[2]) = false
(exit 0)
```

그림 해설 (한 단계씩):

- `"A한🙂"` 은 **세 글자**인데 **여덟 바이트**다. `A` 가 1, `한` 이 3, `🙂` 가 4다.
- 비트 꼴을 보면 규칙이 보인다 — **선두 바이트**는 `0xxxxxxx`·`110xxxxx`·`1110xxxx`·`11110xxx` 이고
  **이어지는 바이트**는 전부 `10xxxxxx` 다.
- ★★ 그래서 **아무 바이트나 집어도 그것이 글자 시작인지 알 수 있다** — `utf8.RuneStart(s[i])`.
  이것이 (4)절에서 **안전하게 자르는 법**의 근거가 된다.
- 실측 — `utf8.RuneStart(s[1])` 이 `true`(한 의 시작), `utf8.RuneStart(s[2])` 가 `false`(이어지는 바이트)다.

이제 같은 문자열을 세 가지 방법으로 읽어 본다.

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

그림 해설 (한 단계씩):

- **`len(s)` 는 바이트 수**다. `"Go한글🙂"` 이 **12** 다. 명세가 그렇게 적는다.

  > **A string value is a (possibly empty) sequence of bytes. The number of bytes is called
  > the length of the string … A string's bytes can be accessed by integer indices 0 through len(s)-1.**

- **인덱싱은 `byte`(=`uint8`)를 준다.** `s[2]` 가 `237`(`0xed`) 이다 — **한 의 첫 바이트**이지 `한` 이 아니다.
- **`range` 는 `(바이트 위치, rune)` 을 준다.** 위치가 `0, 1, 2, 5, 8` 로 **1씩 늘지 않는다.**
  명세가 그렇게 적는다.

  > **On successive iterations, the index value will be the index of the first byte of
  > successive UTF-8-encoded code points in the string, and the second value, of type rune,
  > will be the value of the corresponding code point.**

- ★ **`rune` 의 타입이 `int32`** 로 찍힌다. `rune` 은 이름일 뿐이다.

비용 — 셋 다 복사가 없다. `range` 는 바이트를 훑으며 디코딩만 한다.

### (1) ★★★ 경계를 안 맞춰 자르면 — Go 는 **아무 일도 하지 않는다**

**언제 쓰나** — 「앞에서 N자만 보여 준다」를 할 때. **이 주제에서 가장 자주 터지는 자리**다.

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

그림 해설 (한 단계씩):

- `"한글"` 은 **6바이트**이고 `한` 이 **3바이트**다. `s[:2]` 는 **글자 한가운데를 자른 것**이다.
- ★★★ 그런데 **에러도 패닉도 경고도 없다.** `go vet` 도 말이 없다.
  잘린 결과는 그냥 **`"\xed\x95"` 라는 두 바이트짜리 문자열**이다.
- 그것이 잘못됐다는 것은 **일부러 물어봐야** 안다 — `utf8.ValidString(cut)` 이 **`false`** 다.
- ★★ **진단 창은 `%q` 와 `% x` 다.** `%q` 가 `"\xed\x95"` 를, `% x` 가 `ed 95` 를 준다.
  `%s` 는 **터미널·폰트에 달린 깨진 네모**만 보여 주므로 근거가 못 된다.
  ★ 그래서 이 문서는 **`%s` 출력을 싣지 않는다** — 실으면 **문서 파일 자체가 유효한 UTF-8 이 아니게 된다**
  (이 배치에서 실제로 그렇게 됐고, 캡처 파일을 읽는 단계에서 잡혔다).
- `range` 로 돌면 **`U+FFFD` 가 두 번** 나온다 — **한 바이트씩 전진**한다.
- `string([]rune(cut))` 으로 변환하면 **`U+FFFD` 로 굳는다** — 원래 바이트가 사라진다.

```text
   "한"  =  ed 95 9c
             ^
   s[:2] =  ed 95          <- 3바이트 글자를 2에서 끊었다

   Rust   &s[0..2]   ->  패닉 · "byte index 2 is not a char boundary"
   Go     s[:2]      ->  아무 일 없음 · 깨진 문자열이 조용히 흘러간다
   ------------------------------------------------------------------
   Go 에서 이것을 보는 유일한 창 : utf8.ValidString(s)
```

★★★ **이것이 이 주제의 핵심 대비다.** Rust 는 **같은 코드가 패닉**한다 —
[`../../../rust/syntax/15-slices-ranges-and-utf8-boundaries/`](../../../rust/syntax/15-slices-ranges-and-utf8-boundaries/)의
핵심 문장이 「`&s[0..1]` 은 **실행 패닉**」이다. Rust 의 `&str` 은
**「항상 올바른 UTF-8」이라는 불변식을 타입이 들고** 있어서, 그것을 깨는 연산을 런타임이 막는다.
Go 의 `string` 은 **그런 불변식이 없다** — 그냥 바이트 열이고, 올바른 UTF-8 인지는 **아무도 보증하지 않는다.**

**그 대신 Go 가 얻은 것**은 「어떤 바이트 열이든 `string` 에 담을 수 있다」는 것이다 —
파일에서 읽은 것, 네트워크에서 온 것, 잘못 인코딩된 것 전부.
**그 대신 잃은 것**은 「`string` 이면 유효하다」는 보증이다.

범위 자체를 넘기면 **그때는 패닉이다.** 성격이 다른 이야기다.

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

- `s[:7]` 은 **`panic: runtime error: slice bounds out of range [:7] with length 6`** 이다.
- ★ 즉 **Go 가 검사하는 것은 「범위 안인가」이지 「글자 경계인가」가 아니다.**
  **두 가지를 가르는 것이 이 주제의 절반**이다.

비용 — 자르기 자체는 공짜다(헤더만 만든다). **비용이 없어서 위험하다.**

### (2) 깨진 UTF-8 을 `range` 로 돌면 — 명세가 정해 둔 자리

**언제 쓰나** — 바깥에서 온 바이트를 문자열로 받았을 때.

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

그림 해설 (한 단계씩):

- 일부러 깨뜨린 다섯 바이트 `41 ff ed 95 42` 를 `string` 에 담았다. **담는 것 자체는 그냥 된다.**
- `range` 로 돌면 `A` → `U+FFFD` → `U+FFFD` → `U+FFFD` → `B` 다.
  깨진 자리마다 **한 바이트씩** 전진했다. 명세가 그렇게 적는다.

  > **If the iteration encounters an invalid UTF-8 sequence, the second value will be 0xFFFD,
  > the Unicode replacement character, and the next iteration will advance a single byte in the string.**

- ★ `utf8.DecodeRuneInString` 은 같은 일을 하면서 **`size` 를 같이 준다** — 깨진 자리는 `size=1` 이다.
  `range` 가 안에서 하는 일을 손으로 하는 것이 이 함수다.
- ★★ **`RuneCountInString` 이 5** 다. 깨진 바이트 하나를 **룬 하나로 센다.**
  「글자 수」로 쓰면 틀린 값이 조용히 나온다.
- ★★★ **`string([]rune(bad))` 이 파괴적이다** — 5바이트가 **11바이트**가 되고 원래 바이트가 **영영 사라진다.**
  `U+FFFD` 가 3바이트짜리라서 그렇다. **바이트를 지켜야 하면 `[]rune` 변환을 하면 안 된다.**

비용 — `range` 는 복사가 없다. `[]rune` 변환은 **새 배열**을 잡는다((3)절).

### (3) 변환은 복사다 — `[]byte(s)`·`[]rune(s)`

**언제 쓰나** — 문자열을 고쳐야 할 때. Go 에서는 **반드시 복사를 거친다.**

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

그림 해설 (한 단계씩):

- `b := []byte(s)` 뒤 `b[0]` 을 고쳐도 **`s` 는 안 바뀐다.** 변환이 **새 배열을 잡았기** 때문이다.
- ★ 명세가 변환의 **의미**만 정하고 **비용**은 정하지 않는다. 다만 문자열이 불변이므로
  **공유하면 불변식이 깨지니 복사가 강제**된다(컴파일러가 안 새는 경우에 최적화하는 것은 별개다).
- `[]rune("Go한글")` 은 **4칸짜리 `int32` 배열**이다. 원래 8바이트가 **16바이트**가 된다.
- ★★ **세는 법이 셋이고 값이 다르다** — `len` 8 · `len([]rune)` 4 · `RuneCountInString` 4.
  뒤의 둘은 같지만 **`RuneCountInString` 은 배열을 안 잡는다.** 세기만 할 거면 그쪽이다.
- ★★★ **룬 수도 「사람이 세는 글자 수」가 아니다.** 실측 — `"🙂‍↔️"` 는 눈에 한 글자인데
  **13바이트·4룬**이다(이모지 + ZWJ + 화살표 + 변이 선택자).
  **자소 묶음(grapheme cluster)을 세는 장치는 Go 표준에 없다.**

```text
   "Go한글"

   len              8    <- 바이트
   len([]rune)      4    <- 코드 포인트   (배열을 새로 잡는다)
   RuneCountInString 4   <- 코드 포인트   (안 잡는다)
   사람이 세는 글자   4    <- 이 경우엔 같다

   "🙂‍↔️"

   len             13
   RuneCount        4
   사람이 세는 글자   1    ★ 셋이 전부 다르다
```

비용 — `[]byte` 변환은 **바이트 수만큼**, `[]rune` 변환은 **룬 수 × 4바이트**.
명세는 `[]rune` 결과의 `cap` 을 "**implementation-specific**" 이라고 적는다.

### (4) 안전하게 자르는 법 세 가지

**언제 쓰나** — 「앞에서 N까지만」을 진짜로 해야 할 때.

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

그림 해설 (한 단계씩):

- ① **그냥 자르면** `n` 이 2·4·5·7 에서 전부 **`valid=false`** 다. 10에서만 우연히 맞았다.
- ② **경계까지 뒤로 물리면** 전부 `valid=true` 다. 한 줄이면 된다 —
  `for n > 0 && !utf8.RuneStart(s[n]) { n-- }`.
- ③ **룬 개수로 자르면** 의미가 다르다 — 「몇 바이트까지」가 아니라 「몇 글자까지」다.
  대신 **`[]rune` 변환 비용**을 낸다.
- ★ 셋 중 무엇을 쓸지는 **무엇을 제한하려는가**로 정한다 —
  저장 공간이면 ②(바이트), 화면이면 ③(룬)에 가깝다. **화면 폭은 셋 다 정확히 못 맞춘다.**

비용 — ②는 최대 3번 되돌아본다(공짜). ③은 문자열 전체를 룬 배열로 복사한다.

### (5) 문자열은 불변이다

**언제 쓰나** — 문자열의 한 글자만 고치려 할 때. **안 된다.**

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

- `s[0] = 'H'` 가 **컴파일 에러**다 — `cannot assign to s[0] (neither addressable nor a map index expression)`.
- `&s[0]` 도 **컴파일 에러**다. 명세가 그렇게 적는다.

  > **Strings are immutable: once created, it is impossible to change the contents of a string.**
  > … **It is illegal to take the address of such an element; if s[i] is the i'th byte of a string,
  > &s[i] is invalid.**

- ★ 그래서 문자열은 **맵 키가 되고, 구조체를 `==` 로 비교할 수 있고, 복사가 싸다**(헤더 두 칸만 복사).
- 고치려면 **`[]byte` 나 `[]rune` 으로 바꿔 고치고 다시 문자열로** 만든다((3)절).
- ★★ 이 제약은 09번 주제의 「맵은 주소를 못 잡는다」와 **같은 집안이 아니다** —
  맵은 **자리가 움직여서**, 문자열은 **바꾸면 안 되는 값이라서**다. 이유가 다르다.

비용 — 불변이라 **복사가 헤더 두 칸**이다. 이어 붙일 때마다 새 문자열이 생기는 것이 대가다([목록의 **11번 주제**](../11-strings-strconv-bytes-and-unicode-utf8/)).

### (6) ★ `string(정수)` 은 함정이다 — `go vet` 이 잡는다

**언제 쓰나** — 숫자를 문자열로 바꾸려 할 때. **`strconv.Itoa` 를 써야 한다.**

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

그림 해설 (한 단계씩):

- `string(65)` 이 `"65"` 가 아니라 **`"A"`** 다. 명세가 「역사적 이유로」 허용한 변환이다.
- **`go build` 는 통과하고 `go vet` 이 잡는다** — 종료 코드 **1** 과 함께
  `conversion from int to string yields a string of one rune, not a string of digits`.
- ★ 이것은 **명세가 허용하는 것을 도구가 말리는** 자리다. 층이 다르다 —
  **명세는 적법**이라 하고 **vet 은 「그 뜻이 아닐 것」이라고** 한다.
- ★★ `go vet` 이 이 검사를 갖게 된 것은 **1.15**부터다. 그전에는 조용히 지나갔다.
- 고치는 법 — 숫자를 글자로 바꾸려면 **`strconv.Itoa`**, 코드 포인트를 글자로 바꾸려면 **`string(rune(n))`**.

비용 — 없다. 값만 조용히 틀린다.

### (7) 문자열의 나머지 표면

```text
===== 소스: t10j.go =====
package main

import "fmt"

func main() {
	a, b := "가", "각"
	fmt.Println("문자열은 == 와 < 로 비교된다 — 바이트 사전순이다")
	fmt.Printf("  %q == %q : %v\n", a, a, a == a)
	fmt.Printf("  %q <  %q : %v\n", a, b, a < b)
	fmt.Printf("  %q <  %q : %v\n", "Z", "a", "Z" < "a")

	fmt.Println("\n+ 로 이으면 새 문자열이 생긴다 — 원본은 불변이다")
	s := "가"
	t := s
	s += "나"
	fmt.Printf("  s = %q   t = %q\n", s, t)

	fmt.Println("\n문자열은 맵 키가 되고 구조체 필드로 == 된다")
	m := map[string]int{"가": 1}
	fmt.Printf("  m[\"가\"] = %d\n", m["가"])

	fmt.Println("\n문자열의 제로값은 빈 문자열이지 nil 이 아니다")
	var z string
	fmt.Printf("  z == \"\" : %v   len(z) = %d\n", z == "", len(z))

	fmt.Println("\nbyte 와 rune 은 이름만 다른 정수다")
	fmt.Printf("  byte('A') = %d   rune('A') = %d   rune('한') = %d\n", byte('A'), rune('A'), rune('한'))
	var r rune = '한'
	var u int32 = r
	fmt.Printf("  rune 은 int32 의 별명이다 : %d\n", u)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
문자열은 == 와 < 로 비교된다 — 바이트 사전순이다
  "가" == "가" : true
  "가" <  "각" : true
  "Z" <  "a" : true

+ 로 이으면 새 문자열이 생긴다 — 원본은 불변이다
  s = "가나"   t = "가"

문자열은 맵 키가 되고 구조체 필드로 == 된다
  m["가"] = 1

문자열의 제로값은 빈 문자열이지 nil 이 아니다
  z == "" : true   len(z) = 0

byte 와 rune 은 이름만 다른 정수다
  byte('A') = 65   rune('A') = 65   rune('한') = 54620
  rune 은 int32 의 별명이다 : 54620
(exit 0)
```

- **`==` 와 `<` 가 된다** — 바이트 사전순이다. `"Z" < "a"` 가 `true` 인 것은 ASCII 순서다.
  ★ **사람이 기대하는 정렬(로케일)이 아니다.**
- **`+` 는 새 문자열을 만든다.** 원본은 그대로다.
- **맵 키가 된다** — 불변이고 비교 가능하기 때문이다([목록의 **09번 주제**](../09-maps-declaration-comma-ok-delete-and-iteration-order/)).
- **제로값은 `""` 이지 `nil` 이 아니다.** 슬라이스·맵과 다르다.
- **`byte` 와 `rune` 은 이름만 다른 정수**다 — `uint8` 과 `int32` 의 별명이다.

비용 — `==` 는 길이를 먼저 보고 바이트를 비교한다.

## 문법 — 형태와 규칙

### 형태 — 문자열로 하는 일 전부

```go
// t10form.go
package main

import (
	"fmt"
	"strings"
	"unicode/utf8"
)

func main() {
	s := "Go한글"

	// ① 세는 법 — 바이트냐 룬이냐
	fmt.Println("① len(s) =", len(s), " RuneCount =", utf8.RuneCountInString(s))

	// ② 인덱싱은 byte · range 는 (바이트위치, rune)
	fmt.Printf("② s[2] = %d(%T)   range 의 첫 한글 위치는 2 다\n", s[2], s[2])

	// ③ 자르기는 바이트 단위다 — 경계를 맞춰야 한다
	fmt.Printf("③ s[:2]=%q(valid=%v)  s[:3]=%q(valid=%v)\n",
		s[:2], utf8.ValidString(s[:2]), s[:3], utf8.ValidString(s[:3]))

	// ④ 변환은 복사다
	b := []byte(s)
	r := []rune(s)
	fmt.Printf("④ []byte len=%d  []rune len=%d  string(r)=%q\n", len(b), len(r), string(r))

	// ⑤ 이어 붙이기 — 짧으면 +, 길면 Builder
	var sb strings.Builder
	for i := 0; i < 3; i++ {
		sb.WriteString("가")
	}
	fmt.Printf("⑤ \"a\"+\"b\"=%q   Builder=%q\n", "a"+"b", sb.String())

	// ⑥ 한 룬을 문자열로 — string(rune) 이지 string(int) 가 아니다
	fmt.Printf("⑥ string(rune(54620))=%q\n", string(rune(54620)))

	// ⑦ 안전하게 앞에서 n바이트 자르기
	n := 4
	for n > 0 && n < len(s) && !utf8.RuneStart(s[n]) {
		n--
	}
	fmt.Printf("⑦ 경계로 물린 s[:4] -> s[:%d] = %q\n", n, s[:n])
}
```

```text
===== 소스: t10form.go =====
package main

import (
	"fmt"
	"strings"
	"unicode/utf8"
)

func main() {
	s := "Go한글"

	// ① 세는 법 — 바이트냐 룬이냐
	fmt.Println("① len(s) =", len(s), " RuneCount =", utf8.RuneCountInString(s))

	// ② 인덱싱은 byte · range 는 (바이트위치, rune)
	fmt.Printf("② s[2] = %d(%T)   range 의 첫 한글 위치는 2 다\n", s[2], s[2])

	// ③ 자르기는 바이트 단위다 — 경계를 맞춰야 한다
	fmt.Printf("③ s[:2]=%q(valid=%v)  s[:3]=%q(valid=%v)\n",
		s[:2], utf8.ValidString(s[:2]), s[:3], utf8.ValidString(s[:3]))

	// ④ 변환은 복사다
	b := []byte(s)
	r := []rune(s)
	fmt.Printf("④ []byte len=%d  []rune len=%d  string(r)=%q\n", len(b), len(r), string(r))

	// ⑤ 이어 붙이기 — 짧으면 +, 길면 Builder
	var sb strings.Builder
	for i := 0; i < 3; i++ {
		sb.WriteString("가")
	}
	fmt.Printf("⑤ \"a\"+\"b\"=%q   Builder=%q\n", "a"+"b", sb.String())

	// ⑥ 한 룬을 문자열로 — string(rune) 이지 string(int) 가 아니다
	fmt.Printf("⑥ string(rune(54620))=%q\n", string(rune(54620)))

	// ⑦ 안전하게 앞에서 n바이트 자르기
	n := 4
	for n > 0 && n < len(s) && !utf8.RuneStart(s[n]) {
		n--
	}
	fmt.Printf("⑦ 경계로 물린 s[:4] -> s[:%d] = %q\n", n, s[:n])
}
===== 명령: go build -trimpath -o prog . && ./prog =====
① len(s) = 8  RuneCount = 4
② s[2] = 237(uint8)   range 의 첫 한글 위치는 2 다
③ s[:2]="Go"(valid=true)  s[:3]="Go\xed"(valid=false)
④ []byte len=8  []rune len=4  string(r)="Go한글"
⑤ "a"+"b"="ab"   Builder="가가가"
⑥ string(rune(54620))="한"
⑦ 경계로 물린 s[:4] -> s[:2] = "Go"
(exit 0)
```

규칙 불릿.

- **`len` 은 바이트, `RuneCountInString` 은 룬.** 「글자 수」를 말할 때는 **어느 쪽인지 적는다.**
- **인덱싱은 `byte`, `range` 는 `rune`.** `s[i]` 가 글자를 주는 언어가 아니다.
- **자르기는 바이트 단위이고 경계를 안 검사한다.** 잘랐으면 **`utf8.ValidString` 으로 물어라.**
- **범위를 넘기면 패닉, 경계를 어기면 무반응.** 둘은 다른 이야기다.
- **변환은 복사다.** `[]byte`·`[]rune` 둘 다 새 배열을 잡는다.
- **문자열은 불변이다.** 고치려면 변환을 거친다.
- **숫자를 문자열로 바꿀 때 `string(n)` 을 쓰지 마라.** `strconv.Itoa` 다.
- **룬 수도 사람이 세는 글자 수가 아니다.** 자소 묶음은 표준에 없다.

## 어디서 틀리나

### 1. ★★★ 「`len` 이 글자 수겠지」

- (0)절 실측 — `"Go한글🙂"` 의 `len` 이 **12** 다. 글자는 5개다.
- 특히 위험한 자리 — **길이 제한 검사**(`if len(name) > 20`). 한글 사용자에게만 걸린다.
- 고치는 법 — **무엇을 제한하려는지** 먼저 정한다. 저장 공간이면 `len`, 글자 수면 `RuneCountInString`.

### 2. ★★★ 「자르면 에러가 나겠지」

- (1)절 실측 — `s[:2]` 가 **아무 말 없이** 깨진 문자열을 준다. `go vet` 도 조용하다.
- ★★ Rust 를 먼저 배운 사람이 특히 틀린다 — 거기서는 **패닉**이다.
- 고치는 법 — 자른 뒤 **`utf8.ValidString`** 으로 묻거나, 애초에 **경계까지 물려서** 자른다((4)절).

### 3. ★★ 「`s[i]` 로 글자를 꺼낸다」

- (0)절 실측 — `s[2]` 가 `237` 이다. `한` 이 아니라 **한 의 첫 바이트**다.
- 고치는 법 — 글자가 필요하면 `range` 를 돌거나 `[]rune` 으로 바꾼다.
  ★ **인덱스로 임의 접근이 필요하면 그때만 `[]rune`** 을 쓴다(비용이 있다).

### 4. ★★ 「룬 수가 글자 수겠지」

- (3)절 실측 — `"🙂‍↔️"` 가 눈에 한 글자인데 **4룬**이다.
- 자바도 같은 함정이 있다 — 거기서는 `length()` 가 **UTF-16 코드 단위**라 이모지가 **2**로 세어진다
  ([`../../../java/syntax/35-string/`](../../../java/syntax/35-string/)).
  **층이 하나 더 있는 것**이다.
- 고치는 법 — 「사람이 세는 글자」가 정말 필요하면 **표준 밖 라이브러리**가 필요하다. 표준에는 없다.

### 5. ★★ 「`string(n)` 으로 숫자를 문자열로」

- (6)절 실측 — `string(65)` 이 `"A"` 다. **`go build` 는 통과**하고 vet 이 잡는다.
- 고치는 법 — `strconv.Itoa(n)`. **vet 을 CI 에 넣어라** — 이것은 vet 이 잡아 주는 드문 자리다.

### 6. ★ 「깨진 바이트도 룬으로 세면 되겠지」

- (2)절 실측 — `RuneCountInString` 이 깨진 바이트를 **하나씩 센다**(5).
- 고치는 법 — 「유효한가」를 먼저 묻는다. `utf8.ValidString` 은 세는 것과 **다른 질문**이다.

### 7. ★ 「`[]rune` 로 바꿨다 돌아오면 원래대로」

- (2)절 실측 — 깨진 문자열은 **안 돌아온다.** 5바이트가 11바이트가 됐다.
- 고치는 법 — 바이트를 지켜야 하면 **`[]byte` 로** 다룬다. `[]rune` 은 **정규화 아닌 손실 변환**이다.

### 8. ★ 「`"Z" < "a"` 가 이상한데」

- (7)절 실측 — `true` 다. 바이트 비교이지 사전 순서가 아니다.
- 고치는 법 — 사람이 기대하는 정렬이 필요하면 **`golang.org/x/text/collate`** 같은 바깥 도구가 필요하다.

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| **`len` 이 바이트 수**인 것 | **명세 보장** | "The number of bytes is called the length of the string" |
| **`s[i]` 가 바이트**인 것 | **명세 보장** | "A string's bytes can be accessed by integer indices" |
| **문자열이 불변**인 것 | **명세 보장** | "Strings are immutable" |
| **`&s[i]` 가 불법**인 것 | **명세 보장** | "It is illegal to take the address of such an element" |
| **`range` 가 코드 포인트를 준다**는 것 | **명세 보장** | RangeClause 의 string 절 |
| **깨진 바이트에서 `U+FFFD` 가 나오고 1바이트 전진**하는 것 | **명세 보장** | 같은 절의 다음 문장 |
| **경계 위반 자르기가 패닉하지 않는** 것 | **명세 보장** | 슬라이스 식은 **범위만** 검사한다 |
| **범위 초과가 패닉**하는 것 | **명세 보장** | Slice expressions 의 인덱스 규칙 |
| **`string(int)` 이 적법**한 것 | **명세 보장** | "for historical reasons, an integer value may be converted to a string type" |
| `go vet` 이 **그것을 잡는** 것 | **도구(go vet)의 판단** | 1.15부터. **명세는 여전히 적법이라 한다** |
| **`[]rune` 변환이 복사**인 것 | **명세 보장의 결과** | 문자열이 불변이므로 공유할 수 없다 |
| **`[]rune` 결과의 `cap`** | **구현(gc)** | 명세가 "implementation-specific" 이라고 적는다 |
| 패닉 스택의 **주소 오프셋** | **구현(gc)** | 빌드마다 바뀔 수 있다 |
| **자소 묶음을 세는 장치가 없는** 것 | **표준 라이브러리의 범위** | 명세의 문제가 아니다 |

★★ 이 주제는 **명세가 유난히 촘촘하다.** `U+FFFD` 도, 1바이트 전진도, 불변성도 전부 명세다.
**그래서 「gc 가 그러더라」로 설명할 자리가 거의 없다** — 틀리는 것은 사람이 바이트와 룬을 섞기 때문이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 저장 공간을 잰다 | `len(s)` | 바이트가 맞다 |
| 글자 수를 잰다 | `utf8.RuneCountInString(s)` | 배열을 안 잡는다 |
| 글자를 하나씩 본다 | `for i, r := range s` | 복사가 없다 |
| 글자를 **번호로** 집는다 | `[]rune(s)` | 임의 접근이 필요할 때만 |
| 바이트를 고친다 | `[]byte(s)` | 문자열은 불변이다 |
| 앞에서 N바이트 자른다 | 자르고 **경계까지 물린다** | 그냥 자르면 깨진다 |
| 앞에서 N글자 자른다 | `[]rune` 으로 바꿔 자른다 | 비용을 내고 뜻을 산다 |
| 바깥에서 온 바이트를 받는다 | `utf8.ValidString` 으로 **묻는다** | Go 는 안 막아 준다 |
| 숫자를 문자열로 | `strconv.Itoa` | `string(n)` 은 코드 포인트다 |
| 코드 포인트를 문자열로 | `string(rune(n))` | 뜻을 명시한다 |
| 많이 이어 붙인다 | `strings.Builder` | [목록의 **11번 주제**](../11-strings-strconv-bytes-and-unicode-utf8/) |
| 사람이 세는 글자가 필요하다 | **표준 밖** | 자소 묶음은 표준에 없다 |

판단 규칙 두 줄.

- **「이 수가 바이트인가 룬인가」를 변수 이름에 적어라.** 섞이는 순간 조용히 틀린다.
- **「이 문자열이 유효한 UTF-8 인가」는 Go 에서 항상 열린 질문이다.** 물어야 답이 나온다.

## 핵심 문장

- ★★★ **문자열은 바이트 열이다.** `len` 도 인덱싱도 자르기도 바이트이고,
  **`range` 만이 룬을 준다.**
- ★★★ **글자 한가운데서 잘라도 Go 는 아무 일도 하지 않는다.** Rust 는 패닉인데 Go 는
  깨진 문자열을 조용히 돌려준다 — **`utf8.ValidString` 이 그것을 보는 유일한 창**이다.
- ★★ **범위 초과는 패닉이고 경계 위반은 무반응**이다. 검사하는 것은 「범위 안인가」뿐이다.
- ★★ **깨진 바이트를 `range` 로 돌면 `U+FFFD` 가 나오고 한 바이트씩 전진한다** — 이것도 **명세**다.
- ★★ **세는 법이 셋이고 값이 다르다** — `len` · `RuneCountInString` · 사람이 세는 글자.
  `"🙂‍↔️"` 에서 **13 · 4 · 1** 이었다.
- **변환은 복사다.** `[]byte`·`[]rune` 둘 다 새 배열을 잡고, `[]rune` 은 **깨진 바이트를 `U+FFFD` 로 굳힌다.**
- **문자열은 불변**이고 **`&s[i]` 는 불법**이다 — 그래서 맵 키가 되고 복사가 싸다.
- **`string(65)` 은 `"A"` 다.** 명세가 허용하고 **`go vet` 이 말린다**(1.15부터).
- **`utf8.RuneStart` 한 줄이면 경계를 찾는다** — 이어지는 바이트가 전부 `10xxxxxx` 이기 때문이다.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 10번)
- [`../04-numeric-types-conversions-and-integer-division/`](../04-numeric-types-conversions-and-integer-division/)(수치 타입과 변환) —
  ★ **직접 선행**. `byte`=`uint8`·`rune`=`int32` 라는 사실과 **명시 변환 규칙**이 거기다
- [`../09-maps-declaration-comma-ok-delete-and-iteration-order/`](../09-maps-declaration-comma-ok-delete-and-iteration-order/)(맵) —
  같은 `range` 문의 **다른 대상**. 명세의 같은 절이 둘을 나란히 규정한다
- [`../11-strings-strconv-bytes-and-unicode-utf8/`](../11-strings-strconv-bytes-and-unicode-utf8/)(표준 API) —
  **여기는 언어가 주는 것까지**, **그쪽은 그 위에 선 네 패키지**부터
- [`../../../../data-representation/`](../../../../data-representation/) —
  ★ **UTF-8 인코딩 자체의 정본**. **그쪽은 코드 포인트·비트 배치·왜 그 바이트인가까지**,
  여기는 **그 바이트를 Go 문법이 어떻게 내주나**부터
- [`../../../rust/syntax/15-slices-ranges-and-utf8-boundaries/`](../../../rust/syntax/15-slices-ranges-and-utf8-boundaries/) —
  ★★ **이 주제의 직접 대비**. **그쪽은 경계 위반이 패닉이고 메시지가 처방까지 준다**
  (`it is inside '한' (bytes 0..3)`), 여기는 **아무 일도 안 일어난다**.
  같은 문제에 **런타임 검사**와 **무검사**로 갈린 것이다
- [`../../../rust/syntax/14-string-vs-str/`](../../../rust/syntax/14-string-vs-str/) —
  Rust 가 `String`/`&str` 로 **소유와 빌림을 타입에 적는** 이야기. Go 에는 그 구분이 없다
- [`../../../python/syntax/06-strings-bytes-unicode/`](../../../python/syntax/06-strings-bytes-unicode/) —
  ★ **파이썬은 `str` 이 코드 포인트 열이라 `len` 이 룬 수**다. Go 와 **기본 단위가 다르다**.
  대신 파이썬은 `str` 과 `bytes` 사이에 **암묵 변환이 없다**
- [`../../../java/syntax/35-string/`](../../../java/syntax/35-string/) —
  ★ 자바는 **UTF-16 코드 단위**라 이모지가 `length()` 에서 **2**로 세어진다. **세 번째 기준**이다
- [`../../../c/syntax/20-null-terminated-strings-and-string-literals/`](../../../c/syntax/20-null-terminated-strings-and-string-literals/) —
  ★ **C 는 널 종단**이라 길이를 **세어야** 알고, `\0` 이 없으면 UB 다.
  **Go 는 길이를 들고 다닌다** — `len` 이 `O(1)` 이고 `\0` 이 그냥 한 바이트다
- [목록의 **14번 주제**](../14-for-four-forms-range-over-int-and-func/)(`for` 의 네 형태) — `range` 문 전체의 정본
- [목록의 **42번 주제**](../42-fmt-verbs-stringer-and-errorf/)(`fmt`) — `%q`·`%x`·`%U` 같은 진단 동사의 정본
- [목록의 **45번 주제**](../45-encoding-json-tags-omitempty-pointers-numbers-and-streaming/)(`encoding/json`) — 바깥에서 온 바이트가 문자열이 되는 실제 경로

## 용어 풀이

- **바이트(byte)** — Go 에서 `uint8` 의 별명. `s[i]` 가 주는 것.
- **룬(rune)** — Go 에서 `int32` 의 별명. 유니코드 **코드 포인트** 하나.
- **코드 포인트(code point)** — 유니코드가 글자에 매긴 번호(`U+D55C` 등).
- **UTF-8** — 코드 포인트를 1\~4바이트로 적는 인코딩. 선두 바이트와 이어지는 바이트가 비트로 구분된다.
- **`U+FFFD`(replacement character)** — 「깨졌다」를 뜻하는 문자. Go 에서는 `utf8.RuneError`.
- **룬 경계(rune boundary)** — 한 코드 포인트의 첫 바이트 자리. `utf8.RuneStart` 로 판정한다.
- **자소 묶음(grapheme cluster)** — 사람이 한 글자로 보는 단위. **룬 여럿일 수 있고 Go 표준에는 없다.**
- **ZWJ(zero-width joiner)** — `U+200D`. 이모지 여럿을 한 글자로 묶는 보이지 않는 문자.

---

## 더 들어가면

- **왜 Go 는 안 막나** — `string` 을 「바이트 열」로 둔 덕에 **파일·네트워크에서 온 아무 바이트나**
  같은 타입으로 다룰 수 있다. Rust 는 `&str` 에 불변식을 걸고 대신 `&[u8]` 과 `String` 을 나눴다.
  ★ **같은 문제를 「타입을 하나로 두고 사람이 조심」과 「타입을 둘로 나누고 컴파일러가 강제」로 갈라 푼 것**이다.
- **`for i := 0; i < len(s); i++` 와 `for i, r := range s` 는 다른 루프다.** 앞의 것은 바이트를 훑고
  뒤의 것은 룬을 훑는다. **바이트 훑기가 필요한 자리도 있다** — ASCII 만 찾을 때가 그렇다(더 빠르다).
- **`string` 과 `[]byte` 사이 변환이 최적화로 사라지는 경우가 있다.**
  `m[string(b)]` 같은 꼴을 컴파일러가 특별 취급한다고 알려져 있는데,
  **이 문서는 그것을 던져서 확인하지 않았다.** 정본은 [목록의 **52번 주제**](../52-tools-gofmt-vet-build-tags-embed-and-escape-analysis/)(도구·탈출 분석)다.
- **정규화(NFC/NFD)는 이 주제 밖이다.** 눈에 같은 두 문자열이 바이트로 다를 수 있고,
  Go 표준에는 정규화가 **없다**(`golang.org/x/text/unicode/norm` 이 필요하다).
  파이썬은 `unicodedata` 가 표준이라 거기가 다르다.
- **화면 폭은 룬 수도 바이트 수도 아니다.** 한글·CJK 는 폭이 2이고 ZWJ 조합은 1이다.
  **표를 정렬해 찍는 자리에서 이것이 실제로 어긋난다** — 이 문서의 (4)절 표가 그 예다.

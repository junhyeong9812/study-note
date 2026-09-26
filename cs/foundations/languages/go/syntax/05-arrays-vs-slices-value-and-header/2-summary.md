# go/syntax/05 — 배열과 슬라이스는 무엇이 다른가 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Go 명세](https://go.dev/ref/spec) 의 Array types · Slice types ·
> Slice expressions · Appending to and copying slices · Length and capacity · Comparison operators 절.\
> 웹이 아니라 **이 툴체인이 들고 있는 `$(go env GOROOT)/doc/go_spec.html` 을 열어** 인용했다.
> 그 파일의 머리는 「**Language version go1.27 (May 26, 2026)**」이다.
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> **버전** — 배열·슬라이스·`append`·`copy`·3-인덱스 슬라이싱은 **1.2부터 지금까지 같다**
> (3-인덱스 슬라이싱 `s[a:b:c]` 가 1.2에 들어왔고 나머지는 1.0부터다).
> `unsafe.SliceData` 는 **1.20**부터, `slices` 패키지는 **1.21**부터다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 명세로, 출력은 실행으로 접지했다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것. 어느 컴파일러에서도 같다 | `go_spec.html` 원문 인용 |
| **구현(gc)** | 이 컴파일러·런타임이 그렇게 하는 것. 약속은 아니다 | `go tool compile -S` 출력 · `cap` 의 구체적 수치 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 실행 출력(재실행 대조까지) |

★ 이 주제도 **명세 보장 칸이 크다.** 「배열은 값이다」도, 「슬라이스는 기반 배열을 공유한다」도,
「`append` 가 모자라면 새 배열을 잡는다」도 전부 명세에 적혀 있다.
★★ 다만 **`cap` 이 얼마로 늘어나는지는 명세에 한 글자도 없다** — 그것은 구현이다(06번 주제).

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

이 갈래에서 **다시 돌리면 달라지는 칸**을 미리 갈라 둔다. 제출 전 재대조를 한 줄에 판정하기 위해서다.

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | 기반 배열의 **주소 자체** | 실행마다 힙이 다른 자리를 준다. 그래서 이 문서는 주소를 안 찍고 「**같나 다르나**」와 `A`·`B` 이름표만 찍는다 |
| **흔들린다** | 패닉 스택의 `goroutine N [running]` 번호와 `+0x…` 오프셋 | 런타임·빌드 산출물에 달렸다 |
| **흔들린다** | 어셈블리의 레지스터 이름·오프셋·`size=` | 아키텍처(amd64)·판(go1.27.1)에 달렸다 |
| 안 흔들린다 | `len`·`cap` 값 | 같은 소스면 같다. 단 **`cap` 의 「증가 규칙」은 구현이다** |
| 안 흔들린다 | 패닉 **메시지 본문**(`index out of range [4] with length 3`)·종료 코드 `2` | 명세와 런타임이 정한 문장이다 |
| 안 흔들린다 | 컴파일 에러 문장 본문과 `파일:줄:칸` | 같은 소스·같은 판이면 같다 |
| 해당 없음 | 맵 순회 순서 | 이 주제는 맵을 거의 안 쓴다. 07번에서 한 번 쓰는데 **키가 하나뿐**이라 순서가 성립하지 않는다 |

## 한눈에 — 쉽게 말하면

**배열은 「짐칸 그 자체」고 슬라이스는 「어느 짐칸의 몇 번부터 몇 개를 본다」고 적힌 쪽지다.**

쪽지를 복사해도 짐칸은 하나뿐이다. 그런데 짐칸이 꽉 차서 **더 큰 짐칸으로 옮기면**,
옮긴 쪽의 쪽지만 새 주소를 가리키고 **옛 쪽지는 옛 짐칸을 계속 가리킨다.**
이 한 문장이 Go 에서 슬라이스 버그가 나는 자리 전부다.

| 비유 | 실체 |
|---|---|
| 짐칸 자체 | **배열** `[6]int` — 길이가 타입의 일부다 |
| 쪽지 한 장 | **슬라이스 헤더** — 「기반 배열 포인터 · `len` · `cap`」 세 칸 |
| 쪽지를 복사한다 | 슬라이스 대입·함수 인자 전달 — **짐칸은 안 복사된다** |
| 짐칸을 통째로 복사한다 | 배열 대입·함수 인자 전달 — **칸마다 값이 복사된다** |
| 「6번부터 3개」 | `arr[1:4]` — `len` 3, `cap` 은 **배열 끝까지** |
| 짐칸이 꽉 차 더 큰 데로 옮김 | `append` 의 **재할당** — 여기서 **공유가 끊긴다** |
| 쪽지에 「4개까지만 본다」고 못 박음 | `s[a:b:c]` — **`cap` 을 자른다**(08번 주제) |

- C 와 다른 점 — Go 에는 **감쇠(decay)가 없다.** 배열을 함수에 넘기면 포인터가 되는 것이 아니라
  **값이 통째로 복사**된다. 길이도 타입에 그대로 남는다.
- Rust 와 다른 점 — Rust 슬라이스 `&[T]` 는 「포인터 + 길이」 **두 칸**인데
  Go 슬라이스는 **세 칸**이다. 늘어난 한 칸이 `cap` 이고, **`append` 가 그 칸 위에서 산다.**
- Python 과 다른 점 — 파이썬 리스트의 `s[1:4]` 는 **새 리스트를 만드는 복사**다.
  Go 의 `s[1:4]` 는 **복사가 아니라 창**이다. 같은 문법이 정반대로 움직인다.

```text
   배열 arr [6]int  (짐칸 자체)          슬라이스 s := arr[1:4]  (쪽지)
   +----+----+----+----+----+----+       +--------------------------+
   | 10 | 20 | 30 | 40 | 50 | 60 |       | ptr -> arr 의 1번 칸     |
   +----+----+----+----+----+----+       | len = 3                  |
     0    1    2    3    4    5          | cap = 5   (1번~5번)      |
          ^~~~~~~~~~~~^                  +--------------------------+
          s[0] s[1] s[2]
                     ^~~~~~~~~~~~^
                     len 밖 · cap 안 — s[:cap(s)] 로 다시 보인다
```

> **슬라이스 헤더(slice header)** — 슬라이스 값의 실체. 기반 배열 포인터 · `len` · `cap` 세 칸이다.\
> 예: 64비트에서 `unsafe.Sizeof` 가 **길이와 무관하게 24바이트**다((1)절 실측).

> **기반 배열(underlying array)** — 슬라이스가 가리키는 실제 저장소. 명세의 낱말이다.\
> 예: `arr[1:4]` 와 `arr[2:5]` 는 **같은 기반 배열**을 본다. 한쪽을 고치면 다른 쪽에 보인다.

> **재할당(reallocation)** — `append` 가 `cap` 이 모자라 **새 배열을 잡고 옮기는** 것.\
> 예: `cap` 이 남으면 제자리에 쓰고, 모자라면 새 배열로 간다. **그 순간 공유가 끊긴다**((4)절).

> **감쇠(decay)** — C 에서 배열 이름이 식에서 첫 원소 포인터로 자동 변환되는 것.
> **Go 에는 이 규칙이 없다.**\
> 예: C 는 함수 안에서 `sizeof(a)` 가 8이 되는데, Go 는 `[4]int` 를 받으면 끝까지 `[4]int` 다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 배열과 슬라이스는 **값으로서 무엇이 다른가** — 그 차이가 대입과 함수 호출에서 무엇을 바꾸나.
2. 슬라이스 하나가 들고 있는 **세 칸**은 각각 무엇을 정하나 — 그리고 어느 칸이 공유를 정하나.
3. `append` 는 **언제 공유를 끊나** — 그 갈림이 어디에 적혀 있나(명세인가 구현인가).

★ 「동적 배열이라는 자료구조가 왜 배로 늘리나」는 이 주제가 아니다 —
[`../../../../../data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/) 가 정본이다.
여기는 **Go 슬라이스 헤더의 표면**만 본다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

| 창 | 무엇을 보여 주나 | 한계 |
|---|---|---|
| `go build` 의 컴파일 에러 | 타입이 안 맞는 것 · 비교할 수 없는 것 | **공유는 못 본다** — 공유는 타입 문제가 아니다 |
| 실행 출력(`%v`) | 값이 어떻게 됐나 | **왜 그렇게 됐는지는 안 보인다** |
| 런타임 패닉 | 범위를 넘었나 | 범위 **안**에서 나는 사고는 안 잡는다 |
| ★★ **헤더 세 칸 창** — `len`·`cap`·**기반 배열 동일성** | **공유가 살아 있나 끊겼나** | 주소 자체는 흔들리므로 「같나 다르나」로만 읽는다 |

★ 네 번째 창이 이 주제의 본체다. 앞의 셋은 **전부 조용히 통과하는데 값만 틀리는** 자리가 있고
(07번 주제가 그것만 다룬다), 그 자리를 가르는 유일한 관찰이 **기반 배열이 같나 다르나**다.
이 문서는 주소를 그대로 찍지 않고 **처음 본 순서대로 `A`·`B`·`C` 이름표**를 붙여 찍는다 —
주소는 실행마다 바뀌지만 **이름표의 패턴은 안 바뀐다.**

### (1) 배열은 값이다 — 크기부터 다르다

**언제 쓰나** — 「이걸 넘기면 복사인가?」가 궁금할 때마다.

```text
===== 소스: t05a.go =====
package main

import (
	"fmt"
	"unsafe"
)

func main() {
	var a3 [3]int
	var a5 [5]int
	var a1000 [1000]int
	s3 := make([]int, 3)
	s1000 := make([]int, 1000)
	var snil []int
	var b8 [8]byte
	sb := make([]byte, 8)

	fmt.Printf("%-16s %-10T len=%-5d cap=%-5d Sizeof=%d\n", "[3]int", a3, len(a3), cap(a3), unsafe.Sizeof(a3))
	fmt.Printf("%-16s %-10T len=%-5d cap=%-5d Sizeof=%d\n", "[5]int", a5, len(a5), cap(a5), unsafe.Sizeof(a5))
	fmt.Printf("%-16s %-10T len=%-5d cap=%-5d Sizeof=%d\n", "[1000]int", a1000, len(a1000), cap(a1000), unsafe.Sizeof(a1000))
	fmt.Printf("%-16s %-10T len=%-5d cap=%-5d Sizeof=%d\n", "[8]byte", b8, len(b8), cap(b8), unsafe.Sizeof(b8))
	fmt.Println()
	fmt.Printf("%-16s %-10T len=%-5d cap=%-5d Sizeof=%d\n", "[]int (len 3)", s3, len(s3), cap(s3), unsafe.Sizeof(s3))
	fmt.Printf("%-16s %-10T len=%-5d cap=%-5d Sizeof=%d\n", "[]int (len 1000)", s1000, len(s1000), cap(s1000), unsafe.Sizeof(s1000))
	fmt.Printf("%-16s %-10T len=%-5d cap=%-5d Sizeof=%d\n", "[]int (nil)", snil, len(snil), cap(snil), unsafe.Sizeof(snil))
	fmt.Printf("%-16s %-10T len=%-5d cap=%-5d Sizeof=%d\n", "[]byte (len 8)", sb, len(sb), cap(sb), unsafe.Sizeof(sb))
	fmt.Println()
	fmt.Println("포인터 하나의 크기 =", unsafe.Sizeof(&a3), " · int 하나 =", unsafe.Sizeof(len(s3)))
}
===== 명령: go build -trimpath -o prog . && ./prog =====
[3]int           [3]int     len=3     cap=3     Sizeof=24
[5]int           [5]int     len=5     cap=5     Sizeof=40
[1000]int        [1000]int  len=1000  cap=1000  Sizeof=8000
[8]byte          [8]uint8   len=8     cap=8     Sizeof=8

[]int (len 3)    []int      len=3     cap=3     Sizeof=24
[]int (len 1000) []int      len=1000  cap=1000  Sizeof=24
[]int (nil)      []int      len=0     cap=0     Sizeof=24
[]byte (len 8)   []uint8    len=8     cap=8     Sizeof=24

포인터 하나의 크기 = 8  · int 하나 = 8
(exit 0)
```

그림 해설 (한 단계씩):

- **배열의 `Sizeof` 는 길이를 따라 커진다** — `[3]int` 24, `[5]int` 40, `[1000]int` **8000**.
  길이가 **타입의 일부**라서 그렇다.
- **슬라이스의 `Sizeof` 는 언제나 24다** — 원소가 3개든 1000개든, 심지어 `nil` 이어도 24다.
  포인터 8 + `int` 8 + `int` 8 = 24. 마지막 줄이 그 셈을 보여 준다.
- `[8]byte` 는 8바이트인데 `[]byte` 는 **24바이트**다. **원소 하나가 1바이트여도 헤더는 그대로다.**
- 그래서 「큰 배열을 넘기면 비싸다」와 「큰 슬라이스를 넘겨도 24바이트다」가 같은 사실의 앞뒤다.

명세가 그 차이를 둘로 나눠 적는다.

> An array is a numbered sequence of elements of a single type …
> The length is **part of the array's type**; it must evaluate to a non-negative constant …

> A slice is a **descriptor** for a contiguous segment of an underlying array …
> The value of an uninitialized slice is `nil`.

★ 「descriptor」가 이 주제의 낱말이다. 슬라이스는 **데이터가 아니라 데이터를 가리키는 서술**이다.

비용 — 배열을 넘기면 **원소 수에 비례해 복사**된다((9)절 어셈블리에서 그 복사가 보인다).
슬라이스를 넘기면 **언제나 24바이트**다.

### (2) 배열 대입은 복사다 — 그리고 `==` 로 비교된다

**언제 쓰나** — 구조체 필드에 고정 길이 데이터를 둘 때(해시값·IP·키).

```text
===== 소스: t05b.go =====
package main

import "fmt"

// bump 는 받은 배열의 첫 칸을 99 로 바꾼다 — 받은 것이 무엇인지가 문제다.
func bump(arr [4]int) { arr[0] = 99 }

func main() {
	a := [4]int{1, 2, 3, 4}
	b := a
	b[0] = 77
	fmt.Println("b := a; b[0] = 77 한 뒤")
	fmt.Println("  a =", a)
	fmt.Println("  b =", b)

	bump(a)
	fmt.Println("bump(a) 한 뒤")
	fmt.Println("  a =", a)

	c := [4]int{1, 2, 3, 4}
	fmt.Println("a == c :", a == c, " — 배열은 == 로 비교된다")

	for i, v := range a {
		a[i] = 0
		if i == 0 {
			fmt.Println("range 안에서 a 를 0 으로 밀었는데 v =", v, "(0 이 아니다)")
		}
	}
	fmt.Println("  루프 뒤 a =", a)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
b := a; b[0] = 77 한 뒤
  a = [1 2 3 4]
  b = [77 2 3 4]
bump(a) 한 뒤
  a = [1 2 3 4]
a == c : true  — 배열은 == 로 비교된다
range 안에서 a 를 0 으로 밀었는데 v = 1 (0 이 아니다)
  루프 뒤 a = [0 0 0 0]
(exit 0)
```

그림 해설 (한 단계씩):

- `b := a` 뒤에 `b[0] = 77` 을 해도 **`a` 는 그대로**다. 칸이 통째로 둘이 됐다.
- `bump(a)` 는 함수 안에서 `arr[0] = 99` 를 하는데 **돌아와 보면 `a` 가 안 바뀌었다.**
  명세가 함수 호출을 「인자를 매개변수에 **대입**한다」로 정의하고, 배열 대입은 복사이기 때문이다.

  > … the arguments of the call are passed to the function, which means that they are
  > **assigned to their corresponding function parameters**

- `a == c` 가 **true** 다. 배열은 원소 타입이 비교 가능하면 **비교 가능**하다.
  나중에 볼 슬라이스와 정확히 반대다((금지 사례) 블록).
- 마지막 두 줄이 덤이다 — `range a` 로 도는 동안 `a[i] = 0` 으로 밀었는데 **`v` 는 옛 값 `1`** 이다.
  `range` 가 배열을 **한 번 복사해 두고** 돌기 때문이다. 정본은 [목록의 **14번 주제**](../14-for-four-forms-range-over-int-and-func/)다.

```text
   b := a   (배열)                    t := s   (슬라이스)

   a: [1 2 3 4]                       s: [ptr|len 4|cap 4] ---+
        |  복사                            t: [ptr|len 4|cap 4] ---+
        v                                                      |   |
   b: [1 2 3 4]   <- 칸이 둘                                    v   v
                                                        [1 2 3 4]  <- 배열은 하나
```

비용 — 큰 배열의 대입은 **그 크기만큼의 메모리 복사**다.

### (3) ★ 슬라이스 대입은 헤더만 복사한다

**언제 쓰나** — 슬라이스를 함수에 넘기는 모든 자리. 즉 Go 코드 거의 전부.

```text
===== 소스: t05c.go =====
package main

import "fmt"

// setFirst 는 받은 슬라이스의 첫 칸을 99 로 바꾼다.
func setFirst(s []int) { s[0] = 99 }

// appendOne 은 받은 슬라이스에 5 를 붙이고 결과를 버린다.
func appendOne(s []int) { s = append(s, 5); _ = s }

func main() {
	s := []int{1, 2, 3, 4}
	t := s
	t[0] = 77
	fmt.Println("t := s; t[0] = 77 한 뒤")
	fmt.Println("  s =", s)
	fmt.Println("  t =", t, " — 헤더만 복사됐다")

	setFirst(s)
	fmt.Println("setFirst(s) 한 뒤")
	fmt.Println("  s =", s, " — 원소 수정은 호출자에게 보인다")

	fmt.Printf("append 전  len=%d cap=%d\n", len(s), cap(s))
	appendOne(s)
	fmt.Printf("appendOne(s) 뒤 len=%d cap=%d  s=%v  — 길이가 안 늘었다\n", len(s), cap(s), s)

	room := make([]int, 4, 8)
	copy(room, []int{1, 2, 3, 4})
	appendOne(room)
	fmt.Printf("cap 이 남는 슬라이스에 같은 짓을 하면 len=%d cap=%d room=%v\n", len(room), cap(room), room)
	fmt.Println("  room[:cap(room)] =", room[:cap(room)], " — 배열에는 5 가 이미 들어갔다")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
t := s; t[0] = 77 한 뒤
  s = [77 2 3 4]
  t = [77 2 3 4]  — 헤더만 복사됐다
setFirst(s) 한 뒤
  s = [99 2 3 4]  — 원소 수정은 호출자에게 보인다
append 전  len=4 cap=4
appendOne(s) 뒤 len=4 cap=4  s=[99 2 3 4]  — 길이가 안 늘었다
cap 이 남는 슬라이스에 같은 짓을 하면 len=4 cap=8 room=[1 2 3 4]
  room[:cap(room)] = [1 2 3 4 5 0 0 0]  — 배열에는 5 가 이미 들어갔다
(exit 0)
```

그림 해설 (한 단계씩):

- `t := s` 뒤 `t[0] = 77` 이 **`s` 에도 보인다.** 헤더 둘이 **같은 배열**을 가리키기 때문이다.
- `setFirst(s)` 도 마찬가지 — **원소 수정은 호출자에게 보인다.**
- 그런데 `appendOne(s)` 는 **아무 일도 안 한 것처럼 보인다.** `len` 이 4 그대로다.
  함수가 받은 것은 **헤더의 복사본**이고, `append` 가 고친 것은 **그 복사본의 `len`** 이라서다.
- ★ 마지막 두 줄이 이 절의 함정이다. `cap` 이 남는 슬라이스(`make([]int, 4, 8)`)에 같은 짓을 하면
  **호출자의 `len` 은 그대로인데 기반 배열에는 `5` 가 이미 들어가 있다.**
  `room[:cap(room)]` 으로 펴 보면 보인다. **「안 보인다」가 「안 일어났다」가 아니다.**
- 그래서 Go 의 관용은 「**`s = append(s, x)`**」다 — 결과를 **반드시 받는다.**

비용 — 헤더 24바이트 복사. 원소는 안 만진다.

### (4) ★★★ `append` 가 재할당하면 공유가 끊긴다

**언제 쓰나** — 이 주제에서 **가장 중요한 절**이다. 슬라이스 버그의 뿌리가 여기다.

```text
===== 소스: t05d.go =====
package main

import (
	"fmt"
	"unsafe"
)

var seen []unsafe.Pointer

// base 는 기반 배열의 주소를 A·B·C 라는 이름표로 바꿔 준다.
// 주소 자체는 실행마다 바뀌지만 「같나 다르나」는 안 바뀐다.
func base(s []int) string {
	p := unsafe.Pointer(unsafe.SliceData(s))
	if p == nil {
		return "-"
	}
	for i, q := range seen {
		if q == p {
			return string(rune('A' + i))
		}
	}
	seen = append(seen, p)
	return string(rune('A' + len(seen) - 1))
}

func show(tag string, s []int) {
	fmt.Printf("%-20s len=%-2d cap=%-2d 기반배열=%s  %v\n", tag, len(s), cap(s), base(s), s)
}

func main() {
	fmt.Println("── cap 이 남을 때 ──")
	room := make([]int, 3, 6)
	copy(room, []int{1, 2, 3})
	show("room", room)
	r2 := append(room, 4)
	show("r2 := append(room,4)", r2)
	r2[0] = 99
	show("r2[0]=99 뒤 room", room)

	fmt.Println()
	fmt.Println("── cap 이 모자랄 때 ──")
	full := make([]int, 3, 3)
	copy(full, []int{1, 2, 3})
	show("full", full)
	f2 := append(full, 4)
	show("f2 := append(full,4)", f2)
	f2[0] = 99
	show("f2[0]=99 뒤 full", full)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
── cap 이 남을 때 ──
room                 len=3  cap=6  기반배열=A  [1 2 3]
r2 := append(room,4) len=4  cap=6  기반배열=A  [1 2 3 4]
r2[0]=99 뒤 room      len=3  cap=6  기반배열=A  [99 2 3]

── cap 이 모자랄 때 ──
full                 len=3  cap=3  기반배열=B  [1 2 3]
f2 := append(full,4) len=4  cap=6  기반배열=C  [1 2 3 4]
f2[0]=99 뒤 full      len=3  cap=3  기반배열=B  [1 2 3]
(exit 0)
```

그림 해설 (한 단계씩):

- **`cap` 이 남을 때** — `room` 은 `len` 3 `cap` 6이다. `append` 결과 `r2` 의 기반 배열이 **그대로 `A`** 다.
  그래서 `r2[0] = 99` 가 **`room` 에도 보인다.**
- **`cap` 이 모자랄 때** — `full` 은 `len` 3 `cap` 3이다. `append` 결과 `f2` 의 기반 배열이 **`C` 로 바뀌었다**
  (`B` 가 옛 배열이다). 그래서 `f2[0] = 99` 를 해도 **`full` 은 `[1 2 3]` 그대로**다.
- ★★ **같은 코드 `append(s, 4)` 가 한쪽은 공유를 유지하고 한쪽은 끊는다.** 갈린 것은 **`cap` 하나**다.
- 명세가 그 갈림을 한 문장으로 적는다.

  > If the capacity of `s` is not large enough to fit the additional values, `append`
  > **allocates a new, sufficiently large underlying array** that fits both the existing
  > slice elements and the additional values. **Otherwise, `append` re-uses the underlying array.**

```text
   cap 이 남을 때                        cap 이 모자랄 때

   room [ptr|3|6] --+                    full [ptr|3|3] --> 배열 B [1 2 3]
   r2   [ptr|4|6] --+                    f2   [ptr|4|6] --> 배열 C [1 2 3 4]   <- 새 배열
                    v
            배열 A [1 2 3 4 _ _]          B 와 C 는 남남이다.
            둘이 같은 칸을 본다            f2 를 고쳐도 full 은 모른다.
```

★ 「**어느 쪽이 나오는지는 `cap` 으로 예측할 수 있다**」가 실무의 전부다 — 06번 주제가 그 예측을 다루고,
07번 주제가 **예측을 안 한 코드가 어떻게 조용히 틀리는지**를 다룬다.

비용 — 재할당은 **원소를 전부 옮긴다.** 얼마나 자주 일어나는지는 `cap` 의 증가 규칙에 달렸고,
**그 규칙은 명세가 아니라 구현**이다(06번 주제에서 실측한다).

### (5) 슬라이스의 슬라이스는 같은 배열을 본다

**언제 쓰나** — 버퍼를 조각내 넘길 때.

```text
===== 소스: t05e.go =====
package main

import "fmt"

func main() {
	arr := [6]int{10, 20, 30, 40, 50, 60}
	s1 := arr[1:4]
	s2 := s1[1:3]
	fmt.Printf("arr            = %v\n", arr)
	fmt.Printf("s1 = arr[1:4]  = %v  len=%d cap=%d\n", s1, len(s1), cap(s1))
	fmt.Printf("s2 = s1[1:3]   = %v  len=%d cap=%d\n", s2, len(s2), cap(s2))

	s2[0] = 999
	fmt.Println()
	fmt.Println("s2[0] = 999 한 뒤")
	fmt.Printf("arr            = %v\n", arr)
	fmt.Printf("s1             = %v\n", s1)
	fmt.Printf("s2             = %v\n", s2)
	fmt.Println()
	fmt.Println("&arr[2] == &s1[1] :", &arr[2] == &s1[1])
	fmt.Println("&arr[2] == &s2[0] :", &arr[2] == &s2[0])
}
===== 명령: go build -trimpath -o prog . && ./prog =====
arr            = [10 20 30 40 50 60]
s1 = arr[1:4]  = [20 30 40]  len=3 cap=5
s2 = s1[1:3]   = [30 40]  len=2 cap=4

s2[0] = 999 한 뒤
arr            = [10 20 999 40 50 60]
s1             = [20 999 40]
s2             = [999 40]

&arr[2] == &s1[1] : true
&arr[2] == &s2[0] : true
(exit 0)
```

그림 해설 (한 단계씩):

- `s1 := arr[1:4]` 는 `len` 3 `cap` **5**다. **`cap` 은 잘라낸 길이가 아니라 배열 끝까지**다.
- `s2 := s1[1:3]` 은 `len` 2 `cap` **4**다. 자를수록 앞쪽만 줄어든다.
- `s2[0] = 999` 하나가 **`arr`·`s1`·`s2` 셋 다**에 보인다. 셋이 같은 칸을 본다.
- 주소 비교 두 줄이 그것을 **직접** 말한다 — `&arr[2] == &s1[1]` 도 `&arr[2] == &s2[0]` 도 **true** 다.
  (주소 값 자체는 안 찍었다. 흔들리는 칸이기 때문이다.)

명세:

> A slice, once initialized, is always associated with an underlying array that holds its elements.
> A slice therefore **shares storage** with its array and with other slices of the same array;
> by contrast, **distinct arrays always represent distinct storage**.

> The capacity is a measure of that extent: it is the sum of the length of the slice and
> **the length of the array beyond the slice**.

비용 — 없다. 슬라이싱은 헤더 하나를 만드는 일이다.

### (6) `nil` 슬라이스와 빈 슬라이스

**언제 쓰나** — 함수가 「아무것도 없음」을 돌려줄 때.

```text
===== 소스: t05f.go =====
package main

import "fmt"

func describe(tag string, s []int) {
	fmt.Printf("%-18s len=%d cap=%d  == nil : %-5t  %v  %q\n",
		tag, len(s), cap(s), s == nil, s, fmt.Sprint(s))
}

func main() {
	var n []int
	e := []int{}
	m := make([]int, 0)
	describe("var n []int", n)
	describe("[]int{}", e)
	describe("make([]int, 0)", m)

	fmt.Println()
	describe("append(n, 1)", append(n, 1))
	describe("append(e, 1)", append(e, 1))
	fmt.Println("n 을 range 로 돌면 반복 횟수 =", func() int {
		c := 0
		for range n {
			c++
		}
		return c
	}())
	fmt.Println("len(n) == 0 :", len(n) == 0, " — nil 인지 빈 것인지는 len 으로 못 가른다")

	var s []int
	s3 := s[:0]
	fmt.Println("var s []int; s[:0] == nil :", s3 == nil)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
var n []int        len=0 cap=0  == nil : true   []  "[]"
[]int{}            len=0 cap=0  == nil : false  []  "[]"
make([]int, 0)     len=0 cap=0  == nil : false  []  "[]"

append(n, 1)       len=1 cap=1  == nil : false  [1]  "[1]"
append(e, 1)       len=1 cap=1  == nil : false  [1]  "[1]"
n 을 range 로 돌면 반복 횟수 = 0
len(n) == 0 : true  — nil 인지 빈 것인지는 len 으로 못 가른다
var s []int; s[:0] == nil : true
(exit 0)
```

그림 해설 (한 단계씩):

- 셋 다 `len` 0 `cap` 0이고 `fmt` 출력이 **똑같이 `[]`** 다. **출력으로는 못 가른다.**
- 가르는 것은 **`== nil` 하나뿐**이다 — `var n []int` 만 `true` 다.
- ★ 그런데 **쓰는 데는 차이가 없다.** `nil` 에 `append` 해도 되고, `range` 로 돌면 0번 돈다.
  `len(n) == 0` 도 참이다. 명세가 「`nil` 슬라이스의 길이는 0」이라고 직접 적는다.
- 마지막 줄이 명세의 한 구석이다 — **`nil` 슬라이스를 슬라이싱하면 결과도 `nil`** 이다.

  > If the sliced operand of a valid slice expression is a **nil slice**, the result is a **nil slice**.

- 제로값 규칙 자체는 [02번 주제](../02-variable-declarations-and-zero-values/)가 정본이다.
  여기서는 「**`nil` 이냐 아니냐가 동작을 거의 안 바꾼다**」는 것만 본다.
  (바꾸는 자리가 하나 있다 — JSON 으로 내보낼 때 `null` 과 `[]` 로 갈린다. [목록의 **45번 주제**](../45-encoding-json-tags-omitempty-pointers-numbers-and-streaming/)다.)

비용 — `nil` 슬라이스는 **할당이 0**이다. 「빈 슬라이스를 돌려주려고 `[]int{}` 를 만들」 이유가 없다.

### (7) `cap` 을 자르는 3-인덱스와 짧은 쪽만 베끼는 `copy` — 맛보기

**언제 쓰나** — 공유를 **일부러 끊고 싶을 때**. 정본은 08번 주제다.

```text
===== 소스: t05g.go =====
package main

import "fmt"

func main() {
	arr := [6]int{10, 20, 30, 40, 50, 60}

	two := arr[1:4]
	three := arr[1:4:4]
	fmt.Printf("arr[1:4]   len=%d cap=%d %v\n", len(two), cap(two), two)
	fmt.Printf("arr[1:4:4] len=%d cap=%d %v   ← cap 이 잘렸다\n", len(three), cap(three), three)

	dst := make([]int, 2)
	n := copy(dst, []int{1, 2, 3, 4, 5})
	fmt.Println()
	fmt.Println("copy(len 2 짜리 dst, len 5 짜리 src) 의 반환값 =", n, " dst =", dst)
	dst2 := make([]int, 5)
	n2 := copy(dst2, []int{1, 2})
	fmt.Println("copy(len 5 짜리 dst, len 2 짜리 src) 의 반환값 =", n2, " dst =", dst2)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
arr[1:4]   len=3 cap=5 [20 30 40]
arr[1:4:4] len=3 cap=3 [20 30 40]   ← cap 이 잘렸다

copy(len 2 짜리 dst, len 5 짜리 src) 의 반환값 = 2  dst = [1 2]
copy(len 5 짜리 dst, len 2 짜리 src) 의 반환값 = 2  dst = [1 2 0 0 0]
(exit 0)
```

그림 해설 (한 단계씩):

- `arr[1:4]` 는 `cap` 5인데 **`arr[1:4:4]` 는 `cap` 3**이다. 세 번째 숫자가 **`cap` 의 끝**을 정한다.
  `cap` 이 `len` 과 같아지면 **다음 `append` 는 반드시 재할당**한다 — (4)절의 오른쪽 그림이 강제된다.
- `copy` 는 **짧은 쪽만큼만** 베끼고 **그 개수를 돌려준다.** `dst` 가 짧으면 2, `src` 가 짧아도 2다.
  명세: "The number of elements copied is **the minimum of `len(src)` and `len(dst)`**."
- ★ `copy` 가 보는 것은 **`len` 이지 `cap` 이 아니다.** `make([]int, 0, 8)` 에 `copy` 하면 **0개**가 베껴진다
  (08번 주제에서 실측한다). 이것이 `copy` 로 가장 자주 틀리는 자리다.

비용 — `copy` 는 베낀 개수만큼. 3-인덱스 슬라이싱은 공짜다(헤더 하나).

### (8) 범위 밖 — `len` 을 넘어도 `cap` 까지는 된다

**언제 쓰나** — 인덱스와 슬라이싱의 경계가 다르다는 것을 처음 만날 때.

```text
===== 소스: t05j.go =====
package main

import (
	"fmt"
	"os"
)

func main() {
	arr := [6]int{10, 20, 30, 40, 50, 60}
	s := arr[1:4]
	fmt.Printf("s = arr[1:4]  len=%d cap=%d  %v\n", len(s), cap(s), s)
	fmt.Println("s[:cap(s)]  =", s[:cap(s)], " — len 을 넘어 cap 까지는 다시 슬라이싱된다")
	fmt.Println("s[:5]       =", s[:5], " — 같은 것을 숫자로 적어도 된다")
	fmt.Fprintln(os.Stderr, "----- 여기까지 stdout · 아래부터 패닉 -----")
	i := 4
	fmt.Println(s[i])
}
===== 명령: go build -trimpath -o prog . =====
(exit 0)
===== 명령: ./prog 2>&1 =====
s = arr[1:4]  len=3 cap=5  [20 30 40]
s[:cap(s)]  = [20 30 40 50 60]  — len 을 넘어 cap 까지는 다시 슬라이싱된다
s[:5]       = [20 30 40 50 60]  — 같은 것을 숫자로 적어도 된다
----- 여기까지 stdout · 아래부터 패닉 -----
panic: runtime error: index out of range [4] with length 3

goroutine 1 [running]:
main.main()
	ex/t05j.go:16 +0x26a
(exit 2)
```

그림 해설 (한 단계씩):

- `s` 는 `len` 3 `cap` 5다. **`s[:cap(s)]` 가 `[20 30 40 50 60]`** 으로 나온다 —
  **`len` 밖의 칸이 슬라이싱으로는 다시 보인다.**
- 그런데 **인덱스 `s[4]` 는 패닉**이다. `index out of range [4] with length 3`.
  ★ **인덱스는 `len` 을 보고 슬라이싱은 `cap` 을 본다.** 명세가 그렇게 갈라 적었다.

  > For arrays or strings, the indices are in range if `0 <= low <= high <= len(a)` …
  > **For slices, the upper index bound is the slice capacity `cap(a)` rather than the length.**

- 마커 줄은 **표준 오류로** 찍었다(`fmt.Fprintln(os.Stderr, …)`). 파이프로 받아도 자리가 안 바뀐다.
- 종료 코드는 **2**다.

`cap` 마저 넘으면 메시지가 달라진다.

```text
===== 소스: t05k.go =====
package main

import (
	"fmt"
	"os"
)

func main() {
	arr := [6]int{10, 20, 30, 40, 50, 60}
	s := arr[1:4]
	fmt.Printf("s len=%d cap=%d\n", len(s), cap(s))
	fmt.Fprintln(os.Stderr, "----- 여기까지 stdout · 아래부터 패닉 -----")
	n := cap(s) + 1
	fmt.Println(s[:n])
}
===== 명령: go build -trimpath -o prog . =====
(exit 0)
===== 명령: ./prog 2>&1 =====
s len=3 cap=5
----- 여기까지 stdout · 아래부터 패닉 -----
panic: runtime error: slice bounds out of range [:6] with capacity 5

goroutine 1 [running]:
main.main()
	ex/t05k.go:14 +0x105
(exit 2)
```

- `slice bounds out of range [:6] with capacity 5` — **`with length` 가 아니라 `with capacity`** 다.
  **메시지의 끝 낱말이 어느 경계를 넘었는지 알려 준다.**
- ★ Rust 도 여기서 두 문장을 쓴다(`the length is 5` 와 `the len is 5` — 컴파일 타임과 런타임이 갈린다).
  **Go 는 `length` 와 `capacity` 로 갈린다.** 갈리는 축이 서로 다르다.

비용 — 인덱스 검사는 런타임 비용이 있다. 이 문서에서는 **재지 않았다.**

### (9) ★ 네 번째 창 — 헤더 세 칸을 따로 묻는다

실행 출력·컴파일 에러·패닉 셋으로는 「지금 이 둘이 같은 배열을 보나」가 안 보인다.
값이 같을 수도 다를 수도 있고, 어느 쪽이어도 **에러가 안 난다.** 그래서 이 갈래는
**`len`·`cap`·기반 배열 동일성 세 칸을 따로 묻는 창**을 쓴다.

(4)절의 프로그램이 그 창이다 — 그 블록의 `===== 소스: t05d.go =====` 안에 `base` 와 `show` 가 전문으로 들어 있다.
만드는 법은 두 단계다.

1. `unsafe.SliceData(s)` 로 **기반 배열 포인터**를 얻는다.
2. 처음 본 포인터를 목록에 쌓고, **몇 번째로 본 것인지**를 `A`·`B`·`C` 로 돌려준다.

- `unsafe.SliceData(s)` 는 **슬라이스의 기반 배열 포인터**를 돌려준다(**1.20**부터).
  1.20 이전에는 `&s[0]` 를 썼는데 **빈 슬라이스에서 패닉**해서 못 쓰는 자리가 있었다.
- ★ **주소를 찍지 않고 이름표를 찍는 것**이 핵심이다. 주소는 흔들리는 칸이고,
  우리가 알고 싶은 것은 「**같나 다르나**」뿐이다.
- `&a[i] == &b[j]` 로 칸 하나를 직접 비교하는 방법도 있다((5)절이 그것을 썼다).
  이쪽은 **빈 슬라이스에서 못 쓴다.**

★ 이 창의 **구현 쪽 짝**을 하나 더 빌려 온다 — 어셈블리로 보면 「복사되는 것」이 눈에 보인다.

```text
===== 소스: t05l.go =====
package passing

// PassArray 는 [4]int 를 값으로 받아 그대로 돌려준다.
func PassArray(a [4]int) [4]int { return a }

// PassSlice 는 []int 를 받아 그대로 돌려준다.
func PassSlice(s []int) []int { return s }
===== 명령: go tool compile -S -trimpath "$PWD" -p passing t05l.go 2>&1 | grep -vE 'FUNCDATA|PCDATA|^\s+0x[0-9a-f]{4} [0-9a-f]{2} ' | sed '/^go:cuinfo/,$d' =====
passing.PassArray STEXT nosplit size=29 align=0x0 args=0x40 locals=0x0 funcid=0x0
	0x0000 00000 (t05l.go:4)	TEXT	passing.PassArray(SB), NOSPLIT|NOFRAME|ABIInternal, $0-64
	0x0000 00000 (t05l.go:4)	LEAQ	passing.~r0+40(SP), AX
	0x0005 00005 (t05l.go:4)	LEAQ	passing.a+8(SP), CX
	0x000a 00010 (t05l.go:4)	MOVUPS	(CX), X14
	0x000e 00014 (t05l.go:4)	MOVUPS	X14, (AX)
	0x0012 00018 (t05l.go:4)	MOVUPS	16(CX), X14
	0x0017 00023 (t05l.go:4)	MOVUPS	X14, 16(AX)
	0x001c 00028 (t05l.go:4)	RET
passing.PassSlice STEXT nosplit size=6 align=0x0 args=0x18 locals=0x0 funcid=0x0
	0x0000 00000 (t05l.go:7)	TEXT	passing.PassSlice(SB), NOSPLIT|NOFRAME|ABIInternal, $0-24
	0x0000 00000 (t05l.go:7)	MOVQ	AX, passing.s+8(FP)
	0x0005 00005 (t05l.go:7)	RET
(exit 0)
===== 명령: rm -f t05l.o =====
(exit 0)
```

- `PassArray` 는 `args=0x40`(**64바이트** — `[4]int` 가 들어가고 나온다)이고
  안에 **`MOVUPS` 가 네 번** 있다. **32바이트를 통째로 옮기는 코드**다.
- `PassSlice` 는 `args=0x18`(**24바이트** — 헤더 하나)이고 **`MOVQ` 한 줄**이다.
- ★ 읽을 것은 **숫자가 아니라 성질**이다 — 한쪽은 **원소를 옮기고** 한쪽은 **안 옮긴다.**
  레지스터 이름·오프셋·`size=` 는 흔들리는 칸이다.

## 문법 — 형태와 규칙

### 형태

```go
// t05form.go
package main

import "fmt"

func main() {
	var arr [3]int               // ① 배열 — 길이가 타입의 일부다
	lit := [...]string{"a", "b"} // ② 길이를 세어 달라고 맡긴다
	var s []int                  // ③ 슬라이스 — 제로값은 nil
	s = make([]int, 2, 5)        // ④ len 2 · cap 5
	s2 := []int{1, 2, 3}         // ⑤ 리터럴은 배열을 만들고 그것을 가리킨다
	win := arr[1:3]              // ⑥ 배열에서 창을 낸다
	cut := s2[0:2:2]             // ⑦ 3-인덱스 — cap 까지 자른다
	fmt.Println(arr, lit, s, s2, win, cut)
	fmt.Println(len(arr), cap(arr), len(s), cap(s), len(win), cap(win), len(cut), cap(cut))
}
```

```text
===== 소스: t05form.go =====
package main

import "fmt"

func main() {
	var arr [3]int               // ① 배열 — 길이가 타입의 일부다
	lit := [...]string{"a", "b"} // ② 길이를 세어 달라고 맡긴다
	var s []int                  // ③ 슬라이스 — 제로값은 nil
	s = make([]int, 2, 5)        // ④ len 2 · cap 5
	s2 := []int{1, 2, 3}         // ⑤ 리터럴은 배열을 만들고 그것을 가리킨다
	win := arr[1:3]              // ⑥ 배열에서 창을 낸다
	cut := s2[0:2:2]             // ⑦ 3-인덱스 — cap 까지 자른다
	fmt.Println(arr, lit, s, s2, win, cut)
	fmt.Println(len(arr), cap(arr), len(s), cap(s), len(win), cap(win), len(cut), cap(cut))
}
===== 명령: go build -trimpath -o prog . && ./prog =====
[0 0 0] [a b] [0 0] [1 2 3] [0 0] [1 2]
3 3 2 5 2 2 2 2
(exit 0)
```

규칙 불릿.

- **배열은 `[N]T`, 슬라이스는 `[]T`** 다. 대괄호 안에 숫자가 있으면 배열이다. **그 숫자가 타입의 일부**다.
- `[...]T{…}` 는 **길이를 세어 달라**는 뜻이다. 결과는 여전히 배열이다.
- 슬라이스의 **제로값은 `nil`** 이다. `make` 나 리터럴이나 슬라이싱으로만 배열이 생긴다.
- `make([]T, len)` 은 `cap` 도 같고, `make([]T, len, cap)` 은 따로 준다.
- 슬라이싱 `a[low:high]` 의 결과 `len` 은 `high-low`, `cap` 은 **`cap(a)-low`** 다.
- `a[low:high:max]` 는 `cap` 을 **`max-low`** 로 못 박는다.
- 배열에서 슬라이싱하려면 **그 배열이 주소를 가질 수 있어야(addressable)** 한다.

### 금지 사례 — 컴파일러가 거부하는 것

```text
===== 소스: t05i.go =====
package main

import "fmt"

func sumArr(a [3]int) int { return a[0] + a[1] + a[2] }

func main() {
	a := [3]int{1, 2, 3}
	b := [3]int{1, 2, 3}
	fmt.Println("배열끼리 == :", a == b)

	m := map[[3]int]string{a: "배열은 맵 키가 된다"}
	fmt.Println(m[b])

	s := []int{1, 2, 3}
	t := []int{1, 2, 3}
	fmt.Println(s == t)

	var bad map[[]int]string
	fmt.Println(bad)

	fmt.Println(sumArr(s))

	var a4 [4]int
	fmt.Println(a == a4)
}
===== 명령: go build -trimpath -o prog . =====
# ex
./t05i.go:17:14: invalid operation: s == t (slice can only be compared to nil)
./t05i.go:19:14: invalid map key type []int
./t05i.go:22:21: cannot use s (variable of type []int) as [3]int value in argument to sumArr
./t05i.go:25:19: invalid operation: a == a4 (mismatched types [3]int and [4]int)
(exit 1)
```

- **`s == t`(슬라이스끼리)가 에러**다 — `slice can only be compared to nil`.
  명세: "**Slice, map, and function types are not comparable.** However, as a special case,
  a slice, map, or function value may be compared to the predeclared identifier `nil`."
- **`map[[]int]string` 이 에러**다 — 비교할 수 없으니 키가 될 수 없다. **배열은 키가 된다**(첫 줄이 그 증거).
- **`[]int` 를 `[3]int` 자리에 못 넣는다** — 둘은 아예 다른 타입이다. **자동 변환이 없다.**
- **`[3]int` 와 `[4]int` 도 다른 타입**이다. `mismatched types [3]int and [4]int`.
  ★ **길이가 타입의 일부**라는 말의 실전 결과가 이것이다. C 에서는 이런 에러가 안 난다.

## 어디서 틀리나

### 1. ★★★ 「슬라이스를 넘겼으니 원본이 바뀌겠지」 — 반만 맞다

- **원소를 고치면 보인다**((3)절 `setFirst`). **`append` 로 길이를 늘리면 안 보인다.**
- 함수 안의 `append` 가 고치는 것은 **매개변수라는 이름의 헤더 복사본**이다.
- 고치는 법 — **결과를 돌려받는다**(`s = f(s)`) 또는 **`*[]int` 를 받는다.**
  Go 표준 라이브러리가 `append` 를 값 반환으로 만든 이유가 이것이다.

### 2. ★★★ 「`append` 는 항상 새 배열을 만든다」 — 아니다

- (4)절 실측 — **`cap` 이 남으면 제자리에 쓴다.** 그때 이웃 슬라이스가 덮인다.
- 반대 오해도 같이 틀린다 — 「`append` 는 항상 제자리에 쓴다」도 아니다.
- 고치는 법 — **`cap` 을 보고 판단**하거나(06번 주제), **`s[:n:n]` 으로 못 박는다**(08번 주제).

### 3. ★★ 「배열을 넘기면 포인터가 간다」 — C 의 직관이다

- (2)절 실측 — `bump(a)` 가 **원본을 못 바꾼다.** Go 에는 감쇠가 없다.
- C 에서는 `void f(int a[10])` 의 `10` 이 버려지고 `sizeof(a)` 가 8이 된다
  ([`../../../c/syntax/16-array-pointer-decay-and-function-parameters/`](../../../c/syntax/16-array-pointer-decay-and-function-parameters/) (1)절).
  Go 는 **끝까지 `[4]int`** 다.
- 그래서 Go 에서 배열을 함수에 넘기는 것은 **복사 비용을 내는 선택**이다.
  관용은 「**슬라이스를 넘긴다**」이고, 배열은 고정 길이 값이 필요할 때만 쓴다.

### 4. ★★ 「`s[1:4]` 는 잘라낸 복사본」 — 파이썬의 직관이다

- (5)절 실측 — `s2[0] = 999` 가 **원본 배열까지** 바꾼다.
- 파이썬은 정반대다 — `s[1:4]` 가 **새 리스트**이고 `o[:] is o` 가 리스트에서 `False` 다
  ([`../../../python/syntax/09-sequence-ops-and-slicing/`](../../../python/syntax/09-sequence-ops-and-slicing/) 5절).
- 고치는 법 — 복사가 필요하면 **`copy` 나 `slices.Clone` 을 명시**한다(08번 주제).

### 5. ★ 「`cap` 은 잘라낸 길이」 — `cap` 은 배열 끝까지다

- (5)절 실측 — `arr[1:4]` 의 `cap` 이 **3이 아니라 5**다.
- 그래서 「3개만 잘랐으니 3개만 건드린다」가 성립하지 않는다.
- 고치는 법 — 「끝까지 본다」를 막으려면 **세 번째 숫자**를 쓴다.

### 6. ★ 「`nil` 슬라이스는 쓸 수 없다」 — 그냥 쓰면 된다

- (6)절 실측 — `append`·`len`·`range` 가 전부 정상이다.
- 틀리는 자리는 **인덱스 접근 하나뿐**이다(`n[0]` 은 패닉).
- 고치는 법 — 「빈 슬라이스를 만들어 두자」는 대부분 **불필요한 할당**이다.

### 7. ★ 「슬라이스도 `==` 로 비교되겠지」

- (금지 사례) — **컴파일 에러**다. `nil` 과만 비교된다.
- 구조체에 슬라이스 필드가 하나라도 있으면 **그 구조체도 비교 불가**가 된다(07번 주제에서 실측한다).
- 고치는 법 — `slices.Equal`(**1.21**) 또는 `reflect.DeepEqual`.

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| 배열의 길이가 **타입의 일부** | **명세 보장** | "The length is part of the array's type" |
| 배열 대입·인자 전달이 **복사** | **명세 보장** | 대입의 정의 + "arguments … are assigned to their corresponding function parameters" |
| 배열이 **비교 가능**(원소가 비교 가능하면) | **명세 보장** | "Array types are comparable if their array element types are comparable." |
| 슬라이스가 **비교 불가**(`nil` 제외) | **명세 보장** | "Slice, map, and function types are not comparable." |
| 슬라이스가 **기반 배열을 공유** | **명세 보장** | "A slice therefore shares storage with its array and with other slices of the same array" |
| `cap` 이 **배열 끝까지** | **명세 보장** | "it is the sum of the length of the slice and the length of the array beyond the slice" |
| 슬라이싱의 상한이 **`cap`**, 인덱스의 상한이 **`len`** | **명세 보장** | "For slices, the upper index bound is the slice capacity `cap(a)` rather than the length." |
| `append` 가 **모자라면 새 배열, 아니면 제자리** | **명세 보장** | "allocates a new … Otherwise, `append` re-uses the underlying array." |
| `copy` 가 **짧은 쪽만큼** | **명세 보장** | "the minimum of `len(src)` and `len(dst)`" |
| `nil` 슬라이스의 `len`·`cap` 이 **0** | **명세 보장** | "The length of a nil slice, map or channel is 0." |
| 슬라이스 헤더가 **정확히 세 칸**이라는 것 | **명세가 직접 말하지 않는다** | 명세의 낱말은 "descriptor" 와 `len`·`cap` 이다. **24바이트라는 수치는 구현·플랫폼** |
| **`Sizeof([]int)` 가 24** | **구현·플랫폼** | 64비트 gc 의 관찰. 32비트에서는 12다(이 머신에 그 타깃이 없어 **못 돌려 봤다**) |
| **`append` 가 `cap` 을 얼마로 늘리나** | **구현** | 명세에 한 글자도 없다. 06번 주제에서 실측한다 |
| 어셈블리의 `MOVUPS` 네 번·`args=0x40` | **구현(gc)·아키텍처** | (9)절. 명세는 코드 생성을 약속하지 않는다 |
| `unsafe.SliceData` 로 주소를 볼 수 있다는 것 | **표준 라이브러리(1.20+)** | `unsafe` 패키지의 계약이다 |

★ 이 주제의 결론은 「**공유는 명세가 보장하고, 언제 끊기는지도 명세가 보장하는데,
얼마나 자주 끊기는지만 구현이다**」이다.
`cap` 의 **증가 규칙**을 「2배씩」이라고 적으면 **구현을 명세로 적는 것**이다 — 06번 주제가 그 반례를 든다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 개수가 변하는 목록 | **슬라이스** | Go 의 기본값. 배열을 직접 쓰는 일은 드물다 |
| 길이가 타입으로 고정돼야 함(해시·IP·키) | **배열** | `[32]byte` 는 **비교 가능**하고 **맵 키**가 된다 |
| 함수에 큰 데이터를 넘김 | **슬라이스** | 헤더 24바이트만 간다 |
| 함수가 원본을 **못 바꾸게** 하고 싶음 | 배열이거나 **복사해서 넘긴다** | 슬라이스를 넘기면 원소는 고쳐진다 |
| 함수가 길이를 바꿔야 함 | **결과를 돌려받는다**(`s = f(s)`) | 헤더 복사본의 `len` 은 호출자에게 안 간다 |
| 「아무것도 없음」을 돌려줌 | **`nil` 슬라이스** | 할당이 0이고 쓰는 데 차이가 없다 |
| 조각을 오래 들고 있어야 함 | **`copy` 로 끊는다** | 작은 조각이 큰 배열을 살려 둔다(08번 주제) |
| 남의 슬라이스를 받아 `append` 함 | **`s[:n:n]` 으로 못 박는다** | 안 그러면 남의 데이터를 덮는다(07번 주제) |
| 고정 크기 버퍼를 스택에 두고 싶음 | 배열 + `buf[:]` | 배열을 만들고 슬라이스로 창을 낸다 |

판단 규칙 두 줄.

- **넘기는 것이 무엇인지 먼저 물어라** — 「짐칸인가 쪽지인가」. Go 에서 그것이 값 의미론의 전부다.
- **`append` 를 쓰는 순간 `cap` 을 같이 생각하라.** 그러지 않으면 공유가 언제 끊기는지 모른다.

## 핵심 문장

- 배열은 **값**이고 슬라이스는 **서술**(descriptor)이다. 명세의 낱말이 그것이다.
- 배열의 `Sizeof` 는 길이를 따라 커지고(`[1000]int` 는 **8000**),
  슬라이스의 `Sizeof` 는 **언제나 24**다 — `nil` 이어도 그렇다.
- 배열 대입은 **칸을 복사**하고 슬라이스 대입은 **헤더를 복사**한다. 배열은 `==` 로 비교되고 슬라이스는 안 된다.
- 함수 안에서 **원소 수정은 보이고 `append` 는 안 보인다** — 고친 것이 헤더 복사본의 `len` 이기 때문이다.
- ★★ **`append` 는 `cap` 이 남으면 제자리에 쓰고 모자라면 새 배열을 잡는다.
  그 순간 공유가 끊긴다.** 이 한 문장이 07·08번 주제의 전부다.
- `cap` 은 잘라낸 길이가 아니라 **배열 끝까지**다. 그래서 `s[:cap(s)]` 로 `len` 밖이 다시 보인다.
- **인덱스는 `len` 을 보고 슬라이싱은 `cap` 을 본다.** 패닉 메시지의 끝 낱말이 그것을 말한다
  (`with length 3` 대 `with capacity 5`).
- **`cap` 이 얼마로 늘어나는지는 명세에 없다.** 그것만이 이 주제에서 구현에 맡겨진 칸이다.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 05번)
- [02번 주제](../02-variable-declarations-and-zero-values/)(변수 선언·제로값) —
  **그쪽은 `nil` 이 제로값이라는 규칙까지**, 여기는 **`nil` 슬라이스가 실제로 어떻게 구는지**부터
- [목록의 **06번 주제**](../06-len-cap-and-append-reallocation/)(`len`/`cap`과 `append`의 재할당) — **`cap` 의 증가와 재할당 판정의 정본**
- [목록의 **07번 주제**](../07-slice-sharing-silent-bugs/)(슬라이스 공유로 조용히 틀리는 자리) — (4)절의 함정이 **버그가 되는 사례들**
- [목록의 **08번 주제**](../08-copy-three-index-slicing-and-memory-retention/)(`copy`·3-인덱스·메모리 유지) — (7)절에서 맛만 본 **공유를 끊는 법의 정본**
- [목록의 **14번 주제**](../14-for-four-forms-range-over-int-and-func/)(`for`·`range`) — `range` 가 배열을 복사하는 것의 정본
- [목록의 **16번 주제**](../16-pointers-value-copy-semantics-new-and-make/)(포인터·`new`와 `make`) — `make` 가 왜 슬라이스·맵·채널 전용인지
- [`../../../../../data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/) —
  **그쪽은 동적 배열이라는 자료구조(증폭 상각·성장 전략)까지**, 여기는 **Go 슬라이스 헤더의 표면**부터
- [`../../../rust/syntax/15-slices-ranges-and-utf8-boundaries/`](../../../rust/syntax/15-slices-ranges-and-utf8-boundaries/) —
  **그쪽 슬라이스는 「포인터 + 길이」 두 칸(`size_of::<&[i32]>()` 가 16)이고 길이를 못 바꾼다**,
  여기는 **세 칸이고 `cap` 위에서 `append` 가 자란다**
- [`../../../c/syntax/16-array-pointer-decay-and-function-parameters/`](../../../c/syntax/16-array-pointer-decay-and-function-parameters/) —
  **그쪽은 함수 문턱에서 배열이 포인터로 감쇠해 길이를 잃고**, 여기는 **배열이 값이라 통째로 복사된다**
- [`../../../python/syntax/09-sequence-ops-and-slicing/`](../../../python/syntax/09-sequence-ops-and-slicing/) —
  **그쪽 `s[1:4]` 는 새 리스트를 만드는 복사**, 여기는 **같은 배열을 보는 창**이다

## 용어 풀이

- **배열(array)** — `[N]T`. 길이가 타입의 일부인 값. 대입하면 통째로 복사된다.
- **슬라이스(slice)** — `[]T`. 기반 배열의 한 구간을 가리키는 서술.
- **슬라이스 헤더(slice header)** — 기반 배열 포인터 · `len` · `cap` 세 칸. 64비트에서 24바이트다(구현).
- **기반 배열(underlying array)** — 슬라이스가 가리키는 실제 저장소.
- **`len`** — 지금 보이는 원소 수. 인덱스의 상한이다.
- **`cap`** — 기반 배열의 **이 슬라이스 시작점부터 끝까지**의 칸 수. 슬라이싱의 상한이다.
- **재할당(reallocation)** — `append` 가 새 배열을 잡고 옮기는 것. 공유가 여기서 끊긴다.
- **3-인덱스 슬라이싱(full slice expression)** — `a[low:high:max]`. `cap` 을 `max-low` 로 못 박는다.
- **`nil` 슬라이스** — 기반 배열이 없는 슬라이스. `len`·`cap` 이 0이고 `append` 는 그냥 된다.
- **감쇠(decay)** — C 의 규칙. 배열 이름이 포인터가 되는 것. **Go 에는 없다.**
- **addressable** — 주소를 취할 수 있는 것. 배열을 슬라이싱하려면 이 조건이 필요하다.

---

## 더 들어가면

- 명세는 `make([]int, 50, 100)` 과 `new([100]int)[0:50]` 이 **같은 슬라이스를 만든다**고 적는다.
  슬라이스가 「배열 + 창」이라는 것을 명세가 직접 보여 주는 자리다.
- **다차원**에서 배열과 슬라이스가 갈린다. 명세: "With arrays of arrays, the inner arrays are,
  by construction, **always the same length**; however with slices of slices …
  the inner lengths **may vary dynamically**. Moreover, the inner slices must be **initialized individually**."
  `[][]int` 는 `make` 를 **줄마다 한 번씩** 불러야 한다.
- 슬라이스 헤더를 타입으로 직접 다루는 길이 있었다(`reflect.SliceHeader`). **1.21부터 deprecated** 이고
  `unsafe.Slice`·`unsafe.SliceData` 로 갈렸다. 이 문서는 뒤엣것만 썼다.
- 배열이 **비교 가능**하다는 성질이 실무에서 쓰이는 자리는 `[32]byte`(SHA-256 결과)를 **맵 키**로 쓰는 것이다.
  `[]byte` 로는 못 한다. `string(b)` 로 바꿔 키를 만드는 관용구가 그래서 있다.
- `unsafe.Sizeof` 가 재는 것은 **헤더의 크기**지 **가리키는 데이터의 크기**가 아니다.
  「슬라이스가 쓰는 메모리」를 재려면 다른 도구가 필요하다 — 이 문서에서는 **재지 않았다**(08번 주제가
  `runtime.MemStats` 로 한 자리만 재 본다).

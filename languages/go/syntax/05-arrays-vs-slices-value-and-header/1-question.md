# go/syntax/05 — 배열과 슬라이스는 무엇이 다른가 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> ★ **답마다 「그 값을 누가 보장하나」를 같이 적어라** — 명세인가, gc 구현인가, 이 판의 관찰인가.
> ★ **`len`·`cap` 을 먼저 적고 나서 값을 적어라.** 이 주제의 출력은 거의 전부 그 두 숫자에서 따라 나온다.
> ★ 다른 언어를 알고 있다면 **그 직관이 여기서 뒤집히는지** 먼저 의심하라
> (C 의 감쇠 · Rust 의 두 칸짜리 슬라이스 · 파이썬의 복사되는 슬라이스).
> 소스는 전부 `go build -trimpath -o prog . && ./prog` 로 던졌다. 모듈 이름은 `ex` 다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 여덟 줄의 `Sizeof` (예측)

```go
// t05a.go
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
```

- 여덟 줄의 `Sizeof` 는 각각 무엇인가?
- 그중 **입력 길이를 바꾸면 달라지는** 줄은 어디인가?
- 마지막 줄의 두 숫자로 앞의 어느 값을 설명할 수 있는가?
- 이 값들 중 **다른 머신에서 달라질 수 있는** 것이 있는가?

### 2. 세 번 찍은 `a` 는 각각 무엇인가 (예측)

```go
// t05b.go
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
```

- `a` 가 세 번 찍힌다. 각각 무엇인가?
- `a == c` 는 컴파일되는가 — 된다면 무엇인가?
- 마지막 루프에서 `v` 는 무엇으로 찍히는가?
- 같은 프로그램을 `[4]int` 대신 `[]int` 로 바꾸면 **어느 줄이 달라지는가**?

### 3. 함수 둘이 지나간 뒤 (예측)

```go
// t05c.go
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
```

- `setFirst(s)` 뒤의 `s` 는 무엇인가?
- `appendOne(s)` 뒤의 `len(s)`·`cap(s)`·`s` 는 무엇인가?
- 마지막 두 줄에서 `room` 과 `room[:cap(room)]` 은 각각 무엇인가 — 왜 다른가?
- `appendOne` 이 호출자에게 아무것도 못 남기는 이유를 **헤더라는 낱말로** 설명하라.

### 4. ★ 같은 `append` 를 두 번 하면 (예측)

```go
// t05d.go
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
```

- 여섯 줄의 `len`·`cap`·기반배열 이름표는 각각 무엇인가?
- `r2[0] = 99` 뒤의 `room` 과 `f2[0] = 99` 뒤의 `full` 은 왜 다르게 나오는가?
- 그 갈림을 **미리 예측하려면 무엇을 보면 되는가**?
- 이 갈림은 명세가 정하는가, 구현이 정하는가?

### 5. `999` 하나가 몇 군데에 보이나 (예측)

```go
// t05e.go
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
```

- `s1`·`s2` 의 `len`·`cap` 은 각각 무엇인가 — `cap` 이 그 값인 이유는?
- `s2[0] = 999` 뒤에 `arr`·`s1`·`s2` 는 각각 무엇으로 찍히는가?
- 마지막 두 줄의 주소 비교는 각각 무엇인가?
- 파이썬에서 같은 모양의 코드를 쓰면 무엇이 달라지는가?

### 6. 이 프로그램은 어디까지 가는가 (예측)

```go
// t05j.go
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
```

- `s[:cap(s)]` 와 `s[:5]` 는 각각 무엇으로 찍히는가?
- 마지막 줄에서 무슨 일이 일어나는가 — **메시지 전문**과 **종료 코드**는?
- `s[4]` 는 되는데 `s[:5]` 는 되는 이유가 무엇인가?
- `s[:cap(s)+1]` 로 바꾸면 메시지의 **끝 낱말**이 어떻게 달라지는가?

### 7. 왜 배열은 `==` 가 되고 슬라이스는 안 되나 (왜)

- 명세는 둘을 어떻게 갈라 적었는가?
- 슬라이스를 `==` 로 비교하려 하면 메시지 전문은 무엇인가?
- `map[[3]int]string` 과 `map[[]int]string` 중 무엇이 되는가 — 왜인가?
- 슬라이스 필드가 하나 있는 구조체는 `==` 로 비교되는가?
- 그래도 슬라이스를 비교해야 한다면 무엇을 쓰는가 — 몇 버전부터인가?

### 8. `nil` 슬라이스로 할 수 있는 것과 없는 것 (경계)

```go
// t05f.go
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
```

- 세 줄의 `len`·`cap`·`== nil` 과 `fmt` 출력은 각각 무엇인가?
- `nil` 슬라이스에 대해 **에러 없이 되는 것**을 셋 이상 말하라.
- `nil` 슬라이스에서 **패닉하는 것**은 무엇인가?
- `var s []int; s[:0] == nil` 은 무엇인가 — 근거가 되는 명세 문장은?

### 9. 어느 칸이 명세이고 어느 칸이 구현인가 (경계)

아래 여섯 가지를 **「명세 보장」 / 「구현·플랫폼」** 으로 갈라라.

- ① `arr[1:4]` 의 `cap` 이 5다
- ② `unsafe.Sizeof([]int{})` 가 24다
- ③ `append` 가 `cap` 이 모자라면 새 배열을 잡는다
- ④ `make([]int,3,3)` 에 하나 붙이면 `cap` 이 6이 된다
- ⑤ 배열을 함수에 넘기면 복사된다
- ⑥ `copy` 가 짧은 쪽만큼만 베낀다

### 10. 다른 언어와 나란히 놓기 (연결)

- C 에서 `int a[10]` 을 함수에 넘기면 함수 안의 `sizeof(a)` 는 무엇이고, Go 는 어떤가?
- Rust 의 `&[i32]` 는 몇 바이트이고 몇 칸인가 — Go 슬라이스는 몇 칸인가? 늘어난 칸은 무엇을 위한 것인가?
- Rust 슬라이스로 길이를 늘릴 수 있는가 — Go 는?
- 파이썬 리스트의 `s[1:4]` 와 Go 의 `s[1:4]` 는 무엇이 정반대인가?
- 셋 중 **범위를 넘겼을 때 조용히 넘어가는** 언어는 어느 것인가?

### 11. 다른 주제와 잇기 (연결)

- `cap` 이 얼마로 늘어나는지의 정본은 몇 번 주제인가?
- 이 주제의 (4)절 함정이 **실제 버그가 되는 사례**를 모은 주제는 몇 번인가?
- 공유를 끊는 법(`copy`·`s[a:b:c]`)의 정본은 몇 번 주제인가?
- `range` 가 배열을 복사하는 것의 정본은 몇 번 주제인가?
- 동적 배열이라는 **자료구조**의 정본은 어느 갈래인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

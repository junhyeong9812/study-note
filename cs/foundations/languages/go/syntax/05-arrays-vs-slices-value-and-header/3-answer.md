# go/syntax/05 — 배열과 슬라이스는 무엇이 다른가 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> 블록은 전부 `===== 소스: … =====` 로 소스를 먼저 싣는다 — **그대로 다시 던질 수 있게** 하기 위해서다.
> ★ **근거로 읽을 칸** — `len`·`cap`·값, 기반 배열이 **같나 다르나**, 에러·패닉 문장 본문,
> `파일:줄:칸`, 종료 코드.
> **근거로 읽지 않을 칸** — 기반 배열의 **주소 자체**(그래서 `A`·`B` 이름표로 찍었다),
> 패닉 스택의 `goroutine N` 번호와 `+0x…`, 어셈블리의 레지스터·오프셋·`size=`,
> `Sizeof` 가 24인 것(**64비트 플랫폼의 값**이다).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 배열은 길이를 따라 커지고, 슬라이스는 **언제나 24**다

**출력**

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

**왜 그런가**

| 값 | `Sizeof` | 왜 |
|---|---|---|
| `[3]int` | **24** | `int` 8바이트 × 3 |
| `[5]int` | **40** | 8 × 5 |
| `[1000]int` | **8000** | 8 × 1000 — **길이가 타입의 일부**라 그대로 커진다 |
| `[8]byte` | **8** | 1 × 8 |
| `[]int`(len 3) | **24** | 헤더 세 칸 |
| `[]int`(len 1000) | **24** | 〃 — **길이와 무관하다** |
| `[]int`(nil) | **24** | 〃 — **`nil` 이어도 세 칸이다** |
| `[]byte`(len 8) | **24** | 〃 — **원소 크기와도 무관하다** |

- **입력 길이를 바꾸면 달라지는 것은 배열 네 줄뿐**이다. 슬라이스 네 줄은 안 움직인다.
- 마지막 줄이 셈을 보여 준다 — 포인터 8 + `int` 8 + `int` 8 = **24**.
  명세가 슬라이스를 「**descriptor**」라고 부르는 것이 이 수치로 보인다.
- ★ **다른 머신에서 달라질 수 있다.** 32비트 타깃이면 포인터와 `int` 가 4바이트라 헤더가 12,
  `[1000]int` 도 4000이 된다. **이 머신에 그 타깃이 없어 못 돌려 봤다** —
  「안 돌려 봄」이 아니라 환경이 없어 못 잰 것이다.
  명세는 `int` 의 폭을 "either 32 or 64 bits" 로만 정한다([04번 주제](../04-numeric-types-conversions-and-integer-division/)).

### 2. 세 번 다 `[1 2 3 4]` … 가 아니다 — 두 번은 그대로고 한 번은 밀려 있다

**출력**

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

**왜 그런가**

- `b := a` 는 **칸을 통째로 복사**한다. `b[0] = 77` 이 `a` 에 안 보인다.
- `bump(a)` 도 마찬가지다 — 매개변수 `arr` 은 **또 하나의 복사본**이다.
  명세가 함수 호출을 「인자를 매개변수에 **대입**한다」로 정의했기 때문이다.

  > … the arguments of the call are passed to the function, which means that they are
  > **assigned to their corresponding function parameters**

- `a == c` 는 **컴파일되고 `true`** 다.

  > **Array types are comparable** if their array element types are comparable.
  > Two array values are equal if their corresponding element values are equal.

- 마지막 루프에서 `v` 는 **`1`** 이다. `range` 가 배열을 **한 번 복사해 두고** 돌기 때문이다.
  `a[i] = 0` 은 원본을 미는데 `v` 는 복사본에서 나온다. 정본은 [목록의 **14번 주제**](../14-for-four-forms-range-over-int-and-func/)다.
- ★ **`[4]int` 를 `[]int` 로 바꾸면 세 줄이 달라진다** — `b[0] = 77` 이 `a` 에 보이고,
  `bump` 가 원본을 바꾸고, `a == c` 는 **컴파일 에러**가 된다. 마지막 루프의 `v` 도 `0` 이 된다
  (슬라이스는 헤더만 복사되니 `range` 가 같은 배열을 읽는다).

### 3. 원소 수정은 보이고 `append` 는 안 보인다 — 그런데 배열에는 들어가 있다

**출력**

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

**왜 그런가**

- `t := s` 는 **헤더만** 복사한다. 두 헤더가 같은 배열을 가리키므로 `t[0] = 77` 이 `s` 에 보인다.
- `setFirst(s)` 도 같다 — **원소 수정은 호출자에게 보인다.**
- `appendOne(s)` 뒤 `len(s)` 는 **4 그대로**, `cap(s)` 도 **4**, `s` 는 `[99 2 3 4]` 다.
  함수 안의 `s = append(s, 5)` 가 고친 것은 **매개변수라는 이름의 헤더 복사본**이고,
  그 복사본은 함수가 끝나면 사라진다.
- ★ 마지막 두 줄이 이 문항의 핵심이다. `room` 은 `make([]int, 4, 8)` 이라 **`cap` 이 남는다.**
  - `room` 은 `[1 2 3 4]`(len 4) — **호출자 쪽에서는 아무 일도 안 일어난 것처럼 보인다.**
  - `room[:cap(room)]` 은 `[1 2 3 4 5 0 0 0]` — **기반 배열에는 `5` 가 이미 들어가 있다.**
  - 즉 **`append` 가 제자리에 썼고**, 호출자의 `len` 이 그것을 안 세고 있을 뿐이다.
    「안 보인다」가 「안 일어났다」가 아니다. 이 틈이 07번 주제의 버그 전부다.
- 그래서 Go 의 관용은 **`s = append(s, x)`** 다 — 결과를 반드시 받는다.

```text
   함수 안                          호출자
   s' [ptr|5|8]  <- append 가 고친 것    s [ptr|4|8]  <- 안 고쳐졌다
        \                                   /
         +----> 배열 [1 2 3 4 5 _ _ _] <---+
                             ^
                             5 는 진짜로 들어갔다
```

### 4. ★ `cap` 이 남으면 배열이 그대로고, 모자라면 새 배열로 간다

**출력**

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

**왜 그런가**

| | `room`(cap 6) | `full`(cap 3) |
|---|---|---|
| `append` 전 기반 배열 | `A` | `B` |
| `append` 후 기반 배열 | **`A`**(그대로) | **`C`**(새 배열) |
| `append` 후 `cap` | 6 | 6 |
| 그 뒤 원본에 보이나 | **보인다**(`[99 2 3]`) | **안 보인다**(`[1 2 3]`) |

- 갈림을 정하는 것은 **`cap` 하나**다. `len(s) + 붙일 개수 <= cap(s)` 면 제자리, 아니면 새 배열.
- 명세가 그 갈림을 직접 적는다.

  > If the capacity of `s` is not large enough to fit the additional values, `append`
  > **allocates a new, sufficiently large underlying array** … **Otherwise, `append` re-uses
  > the underlying array.**

- ★ **갈림 자체는 명세 보장**이다. 다만 **새 배열의 `cap` 이 6이 되는 것은 구현**이다 —
  명세는 "sufficiently large" 라고만 한다. 4가 돼도, 8이 돼도 명세 위반이 아니다.
  06번 주제가 그 수치를 실측한다.
- 미리 예측하는 법 — **`cap(s) - len(s)` 가 붙일 개수보다 크거나 같은지** 보면 된다.
  06번 주제에서 그 예측을 여섯 경우에 대고 맞춰 본다.

### 5. `999` 하나가 **세 군데 전부**에 보인다

**출력**

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

**왜 그런가**

- `s1 := arr[1:4]` → `len` **3**, `cap` **5**. `cap` 은 **잘라낸 길이가 아니라 배열 끝까지**다
  (`arr` 이 6칸인데 1번부터 시작하니 5).
- `s2 := s1[1:3]` → `len` **2**, `cap` **4**. 또 한 칸 앞으로 밀렸다.
- `s2[0] = 999` 하나가 `arr`·`s1`·`s2` **셋 다**에 보인다. 셋이 같은 칸을 본다.

  > A slice … **shares storage** with its array and with other slices of the same array;
  > by contrast, distinct arrays always represent distinct storage.

- 주소 비교 두 줄이 **`true`·`true`** 다 — `&arr[2]`·`&s1[1]`·`&s2[0]` 이 **같은 칸**이다.
  (주소 값 자체는 안 찍었다. 흔들리는 칸이라 근거로 못 쓴다.)
- ★ **파이썬은 정반대다.** `s[1:4]` 가 **새 리스트**라 원본이 안 바뀐다
  ([`../../../python/syntax/09-sequence-ops-and-slicing/`](../../../python/syntax/09-sequence-ops-and-slicing/) 5절 —
  `o[:] is o` 가 리스트에서 `False`). 같은 문법이 정반대로 움직이는 자리다.

### 6. 두 줄 더 찍고 **`s[4]` 에서 패닉**한다 — 종료 코드 2

**출력**

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

**왜 그런가**

- `s[:cap(s)]` 와 `s[:5]` 는 **둘 다 `[20 30 40 50 60]`** 이다. `cap` 이 5니 같은 것을 두 꼴로 적은 것이다.
- 마지막 줄은 **패닉**이다 — 위 블록의 `panic:` 줄이 그것이고, 종료 코드는 **2**다.
- ★ **인덱스는 `len` 을 보고 슬라이싱은 `cap` 을 본다.** 그래서 `s[4]` 는 죽고 `s[:5]` 는 산다.

  > For arrays or strings, the indices are in range if `0 <= low <= high <= len(a)` …
  > **For slices, the upper index bound is the slice capacity `cap(a)` rather than the length.**

- `cap` 마저 넘기면 **끝 낱말이 `with capacity` 로 바뀐다.**

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

- `slice bounds out of range [:6] with capacity 5` — 메시지가 **어느 경계를 넘었는지** 말해 준다.
- 마커 줄은 **표준 오류로** 찍었다. 파이프로 받아도 자리가 안 바뀐다.

### 7. 「비교 가능」이 타입 속성이고, 슬라이스는 거기서 빠졌다

**출력**

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

**왜 그런가**

- 명세가 둘을 두 문단에 갈라 적는다.

  > **Array types are comparable** if their array element types are comparable.

  > **Slice, map, and function types are not comparable.** However, as a special case,
  > a slice, map, or function value may be compared to the predeclared identifier `nil`.

- 메시지 전문은 `invalid operation: s == t (slice can only be compared to nil)` 이다.
- `map[[3]int]string` 은 **된다**(첫 줄이 `배열은 맵 키가 된다` 를 찍는다).
  `map[[]int]string` 은 `invalid map key type []int` 로 **거부**된다 —
  맵 키는 **비교 가능해야** 하기 때문이다.
- **슬라이스 필드가 하나라도 있으면 그 구조체도 비교 불가**다.
  07번 주제에서 `struct containing []string cannot be compared` 를 직접 던져 본다.
- 그래도 비교해야 하면 **`slices.Equal`**(**1.21**부터) 또는 `reflect.DeepEqual` 을 쓴다.
- ★ 덤으로 두 에러가 더 나온다 — `[]int` 를 `[3]int` 자리에 못 넣고,
  `[3]int` 와 `[4]int` 도 `mismatched types` 다. **길이가 타입의 일부**라는 말의 실전 결과다.

### 8. `nil` 로 못 하는 것은 **인덱스 접근 하나뿐**이다

**출력**

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

**왜 그런가**

| | `len` | `cap` | `== nil` | `fmt` 출력 |
|---|---|---|---|---|
| `var n []int` | 0 | 0 | **true** | `[]` |
| `[]int{}` | 0 | 0 | false | `[]` |
| `make([]int, 0)` | 0 | 0 | false | `[]` |

- **출력으로는 못 가른다.** 셋 다 `[]` 이고 `len`·`cap` 도 같다. 가르는 것은 **`== nil` 하나**다.
- `nil` 슬라이스에 대해 **에러 없이 되는 것** — `append` · `len` · `cap` · `range`(0번 돈다) ·
  슬라이싱(`n[:0]`) · `copy` 의 인자로 쓰기 · `fmt` 로 찍기.
- **패닉하는 것은 인덱스 접근**이다(`n[0]`). 범위가 `0` 칸이니 `len` 을 넘는다.
- `var s []int; s[:0] == nil` 은 **`true`** 다. 명세가 그 한 줄을 따로 적는다.

  > If the sliced operand of a valid slice expression is a **nil slice**, the result is a **nil slice**.

- ★ 그래서 「빈 슬라이스를 돌려주려고 `[]int{}` 를 만들」 이유가 거의 없다.
  `nil` 은 **할당이 0**이다. 갈리는 자리는 실질적으로 **JSON 직렬화**(`null` 대 `[]`) 하나뿐이고,
  그 정본은 목록의 **45번 주제**다.

### 9. 구현인 것은 **② 와 ④ 둘뿐**이다

**출력** — 없음(경계 문항).

**왜 그런가**

| | 주장 | 판정 | 근거 |
|---|---|---|---|
| ① | `arr[1:4]` 의 `cap` 이 5 | **명세 보장** | "the sum of the length of the slice and the length of the array beyond the slice" |
| ② | `Sizeof([]int{})` 가 24 | **구현·플랫폼** | 명세는 헤더의 크기를 정하지 않는다. `int` 폭이 "either 32 or 64 bits" 다 |
| ③ | `cap` 이 모자라면 새 배열 | **명세 보장** | "allocates a new, sufficiently large underlying array" |
| ④ | `make([]int,3,3)` + 1 → `cap` 6 | **구현** | 명세는 "sufficiently large" 까지만. 수치는 gc 의 선택이다 |
| ⑤ | 배열을 넘기면 복사 | **명세 보장** | 인자는 매개변수에 **대입**된다 + 배열 대입은 복사다 |
| ⑥ | `copy` 가 짧은 쪽만큼 | **명세 보장** | "the minimum of `len(src)` and `len(dst)`" |

- ★ 정리하면 **「공유의 규칙」은 전부 명세**고 **「크기와 수치」는 구현**이다.
  `cap` 의 증가 규칙을 「2배씩」이라고 적으면 구현을 명세로 적는 것이다 — 06번 주제가 반례를 든다.

### 10. 셋이 서로 다른 세 가지를 고른 셈이다

**출력** — 없음(연결 문항).

**왜 그런가**

| 물음 | **C** | **Rust** | **Go** |
|---|---|---|---|
| 배열을 함수에 넘기면 | **감쇠** — `sizeof(a)` 가 **8** | `&[T]` 로 강제 변환 | **복사** — 끝까지 `[4]int` |
| 슬라이스 값이 몇 칸인가 | (없다) | **두 칸** — ptr + len (`size_of::<&[i32]>()` = **16**) | **세 칸** — ptr + len + cap (**24**) |
| 늘어난 칸은 무엇 | — | — | **`cap`** — `append` 가 그 위에서 자란다 |
| 슬라이스로 길이를 늘릴 수 있나 | — | **못 한다**(`&mut [T]` 는 내용만) | **늘린다**(`append`) |
| `s[1:4]` 가 복사인가 창인가 | — | **창**(`a.as_ptr() == &arr[1]` 이 `true`) | **창** |
| 파이썬은 | — | — | 파이썬만 **복사** |
| 범위를 넘기면 | **UB**(ASan 이 `stack-buffer-overflow`) | **패닉**(exit 101) | **패닉**(exit 2) |
| 조용히 넘어가는 언어 | — | — | **파이썬**(`s[99:]` 가 `[]`) |

- C 쪽 실측은 [`../../../c/syntax/16-array-pointer-decay-and-function-parameters/`](../../../c/syntax/16-array-pointer-decay-and-function-parameters/) (1)절,
  Rust 쪽은 [`../../../rust/syntax/15-slices-ranges-and-utf8-boundaries/`](../../../rust/syntax/15-slices-ranges-and-utf8-boundaries/) (1)절,
  파이썬 쪽은 [`../../../python/syntax/09-sequence-ops-and-slicing/`](../../../python/syntax/09-sequence-ops-and-slicing/) 1절에 있다.
- ★ **Go 슬라이스와 Rust 슬라이스는 이름만 같고 다른 물건**이다. Rust 는 「길이가 고정된 창」이고
  Go 는 「자랄 수 있는 창」이다. 그 차이가 칸 하나(`cap`)에서 나온다.
- ★ **조용히 넘어가는 쪽이 가장 위험하다**는 것이 파이썬 주제의 결론이고,
  **조용히 공유되는 쪽이 가장 위험하다**는 것이 이 Go 묶음의 결론이다 — 위험의 종류가 다르다.

### 11. 다른 주제와 잇기

**출력** — 없음(연결 문항).

**왜 그런가**

- **`cap` 의 증가 규칙** — [목록의 **06번 주제**](../06-len-cap-and-append-reallocation/). 이 주제는 「갈림이 있다」까지만 말하고
  「얼마로 늘어나나」는 거기서 **구현으로 표시하고 실측**한다.
- **(4)절 함정이 버그가 되는 사례** — [목록의 **07번 주제**](../07-slice-sharing-silent-bugs/). 부분 슬라이스에 `append` 하기,
  제자리 필터, 삭제 관용구가 거기 모여 있다.
- **공유를 끊는 법** — [목록의 **08번 주제**](../08-copy-three-index-slicing-and-memory-retention/)(`copy`·`s[a:b:c]`·메모리 유지).
  이 주제의 (7)절은 맛보기다.
- **`range` 가 배열을 복사하는 것** — [목록의 **14번 주제**](../14-for-four-forms-range-over-int-and-func/).
- **동적 배열이라는 자료구조** — [`../../../../../data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/).
  **그쪽은 증폭 상각 분석까지**, 여기는 **Go 슬라이스 헤더의 표면**부터다.
- **`nil` 이 제로값인 규칙** — [02번 주제](../02-variable-declarations-and-zero-values/).
- **`int` 의 폭이 플랫폼에 달린 것** — [04번 주제](../04-numeric-types-conversions-and-integer-division/).
  그것이 헤더가 24바이트인 이유의 절반이다.

---

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행 1회** | 재실행 결과가 `diff -rq` 로 **동일** |
| 판 확인 | `go version` · `go env GOOS GOARCH GOVERSION` | 1 | `go1.27.1 linux/amd64` |
| 값 크기 (`t05a`) | `go build && ./prog` | 1 | 배열 24·40·8000·8 / 슬라이스 **전부 24** |
| 배열은 값 (`t05b`) | 〃 | 1 | `b[0]=77`·`bump` 둘 다 원본 안 바뀜 · `a == c` 가 `true` |
| 헤더만 복사 (`t05c`) | 〃 | 1 | 원소 수정은 보이고 `append` 는 안 보임 · **배열에는 들어감** |
| ★ `append` 의 두 갈래 (`t05d`) | 〃 | 1 | `cap` 남음 → 배열 `A` 유지 / 모자람 → `B`→`C` |
| 슬라이스의 슬라이스 (`t05e`) | 〃 | 1 | `999` 가 셋 다에 · 주소 비교 `true`·`true` |
| `nil` 대 빈 것 (`t05f`) | 〃 | 1 | `len`·`cap`·출력 같음 · `== nil` 만 갈림 |
| 3-인덱스·`copy` 맛보기 (`t05g`) | 〃 | 1 | `cap` 5→3 · `copy` 반환 2·2 |
| 비교 불가 (`t05i`) | `go build` | 1 | **컴파일 에러 네 줄** |
| 인덱스 패닉 (`t05j`) | `go build` · `./prog 2>&1` | 1 | `index out of range [4] with length 3` · **exit 2** |
| 슬라이싱 패닉 (`t05k`) | 〃 | 1 | `slice bounds out of range [:6] with capacity 5` · **exit 2** |
| 어셈블리 (`t05l`) | `go tool compile -S -trimpath "$PWD" -p passing` | 1 | `PassArray` 에 `MOVUPS` 4회 · `PassSlice` 는 `MOVQ` 1줄 |
| 형태 (`t05form`) | `go build && ./prog` | 1 | `len`/`cap` 여덟 값 |

**구현·환경에 달린 항목**(버전이 오르거나 타깃이 바뀌면 **다시 찍어야 하는** 것)

| 항목 | 무엇에 달렸나 |
|---|---|
| **`Sizeof([]int)` 가 24** | **플랫폼(64비트)**. 32비트면 12다 — 이 머신에 그 타깃이 없어 **못 돌려 봤다** |
| **`[1000]int` 가 8000** | 같은 이유. `int` 폭이 "either 32 or 64 bits" 다 |
| **`append` 뒤의 `cap` 이 6인 것** | **gc 의 성장 전략**. 명세는 "sufficiently large" 까지만 말한다 |
| 어셈블리의 명령·레지스터·`args=0x40`·`size=` | **아키텍처(amd64)·판(go1.27.1)** |
| 패닉 스택의 `goroutine 1 [running]` 과 `+0x…` | **런타임·빌드 산출물**. 같은 바이너리는 재실행해도 같다 |
| `unsafe.SliceData` 를 쓸 수 있는 것 | **1.20+**. 그 이전 판에서는 `&s[0]` 를 쓰되 빈 슬라이스에서 패닉한다 |
| 인덱스 검사의 실행 비용 | **안 쟀다.** 재려면 벤치마크가 따로 필요하다(목록의 **50번 주제**) |

★ **다시 찍는 법** — `capture.sh` 를 그대로 돌리고 `diff -rq` 한다.

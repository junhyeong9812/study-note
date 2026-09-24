# go/syntax/06 — `len`/`cap`과 `append`의 재할당 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> ★★ **`cap` 을 묻는 문항에서는 「숫자」보다 「누가 정하나」가 더 중요한 답이다.**
> 수치를 못 맞혀도 「이건 구현이라 못 맞히는 게 맞다」까지 갔으면 맞힌 것이다.
> ★ 반대로 **「재할당이 일어났나」는 반드시 맞혀야 한다** — 그것은 명세가 정한다.
> 소스는 전부 `go build -trimpath -o prog . && ./prog` 로 던졌다. 모듈 이름은 `ex` 다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 열여섯 줄의 두 숫자 (예측)

```go
// t06a.go
package main

import "fmt"

func row(tag string, s []int) {
	fmt.Printf("%-24s len=%-2d cap=%-2d %v\n", tag, len(s), cap(s), s)
}

func main() {
	arr := [6]int{10, 20, 30, 40, 50, 60}
	fmt.Printf("%-24s len=%-2d cap=%-2d %v\n", "arr [6]int", len(arr), cap(arr), arr)
	fmt.Println()

	row("[]int{1,2,3}", []int{1, 2, 3})
	row("make([]int, 3)", make([]int, 3))
	row("make([]int, 3, 10)", make([]int, 3, 10))
	var nilS []int
	row("var s []int", nilS)
	fmt.Println()

	row("arr[:]", arr[:])
	row("arr[2:]", arr[2:])
	row("arr[:2]", arr[:2])
	row("arr[2:4]", arr[2:4])
	row("arr[2:4:5]", arr[2:4:5])
	row("arr[6:]", arr[6:])
	fmt.Println()

	s := arr[2:4]
	row("s := arr[2:4]", s)
	row("s[:cap(s)]", s[:cap(s)])
	row("s[1:]", s[1:])
	fmt.Println("0 <= len <= cap 인가 :", 0 <= len(s) && len(s) <= cap(s))
}
```

- 열여섯 줄의 `len`·`cap` 을 각각 적어라.
- `arr[:2]` 와 `arr[2:]` 의 `cap` 이 갈리는 이유는?
- `arr[6:]` 은 패닉인가?
- 이 열여섯 줄 중 **판이 올라가면 바뀔 수 있는** 줄이 있는가?

### 2. 여덟 번 붙이면 기반 배열이 몇 번 바뀌나 (예측)

```go
// t06c.go
package main

import (
	"fmt"
	"unsafe"
)

var seen []unsafe.Pointer

// base 는 기반 배열의 주소를 A·B·C 라는 이름표로 바꾼다.
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

func main() {
	s := make([]int, 0, 4)
	realloc := 0
	prev := base(s)
	fmt.Printf("%-16s len=%-2d cap=%-2d 기반배열=%s\n", "make(0, 4)", len(s), cap(s), prev)
	for i := 1; i <= 8; i++ {
		s = append(s, i)
		now := base(s)
		mark := ""
		if now != prev {
			mark = "  ← 재할당"
			realloc++
		}
		fmt.Printf("append %-2d 뒤     len=%-2d cap=%-2d 기반배열=%s%s\n", i, len(s), cap(s), now, mark)
		prev = now
	}
	fmt.Println("재할당 횟수 =", realloc)

	fmt.Println()
	t := make([]int, 0, 8)
	r2 := 0
	p2 := base(t)
	for i := 1; i <= 8; i++ {
		t = append(t, i)
		if base(t) != p2 {
			r2++
			p2 = base(t)
		}
	}
	fmt.Printf("cap 을 8 로 미리 잡고 8번 append 하면 재할당 횟수 = %d (len=%d cap=%d)\n", r2, len(t), cap(t))
}
```

- 첫 블록에서 기반 배열 이름표는 어느 `append` 에서 바뀌는가 — 재할당 횟수는?
- 둘째 블록(`cap` 8로 시작)의 재할당 횟수는?
- `cap` 4에서 다섯째를 붙이면 `cap` 이 얼마가 되는가 — **그 값을 자신 있게 말할 수 있는가**?
- 이 프로그램이 `cap` 말고 **따로 관찰하는 것**은 무엇이고 왜 필요한가?

### 3. 2000번 붙이는 동안 `cap` 은 (예측)

```go
// t06b.go
package main

import "fmt"

func main() {
	fmt.Println("※ 아래 cap 값은 gc go1.27.1 의 관찰이지 명세가 아니다.")
	var s []int
	prev := cap(s)
	fmt.Printf("시작           len=%-4d cap=%d\n", len(s), cap(s))
	for i := 0; i < 2000; i++ {
		s = append(s, i)
		if cap(s) != prev {
			fmt.Printf("len %-4d 에서  cap %-4d -> %-4d  (%.3f 배)\n",
				len(s), prev, cap(s), float64(cap(s))/float64(max(prev, 1)))
			prev = cap(s)
		}
	}
	fmt.Printf("끝             len=%-4d cap=%d\n", len(s), cap(s))
}
```

- `cap` 이 **몇 번** 바뀌는가?
- 그 값들은 앞에서부터 어떻게 움직이는가 — **끝까지 같은 비율인가**?
- 첫 줄의 `0 -> ?` 는 1인가 다른 값인가?
- 이 출력을 문서에 실을 때 **반드시 같이 적어야 하는 문장**은 무엇인가?

### 4. 같은 다섯 개인데 `cap` 이 같은가 (예측)

```go
// t06e.go
package main

import "fmt"

func main() {
	fmt.Println("※ cap 값은 gc go1.27.1 의 관찰이다 — 명세는 cap 을 정하지 않는다.")

	one := []int{}
	for i := 0; i < 5; i++ {
		one = append(one, i)
	}
	fmt.Printf("하나씩 다섯 번 append  len=%d cap=%d\n", len(one), cap(one))

	atonce := append([]int{}, 0, 1, 2, 3, 4)
	fmt.Printf("한 번에 다섯 개 append len=%d cap=%d\n", len(atonce), cap(atonce))

	fromSlice := append([]int{}, []int{0, 1, 2, 3, 4}...)
	fmt.Printf("슬라이스를 통째로 append len=%d cap=%d\n", len(fromSlice), cap(fromSlice))

	made := make([]int, 5)
	fmt.Printf("make([]int, 5)         len=%d cap=%d\n", len(made), cap(made))

	fmt.Println()
	fmt.Println("네 슬라이스의 내용이 같은가 :",
		fmt.Sprint(one) == fmt.Sprint(atonce) && fmt.Sprint(one) == fmt.Sprint(fromSlice))
	fmt.Println("cap 이 같은가              :",
		cap(one) == cap(atonce) && cap(one) == cap(fromSlice) && cap(one) == cap(made))
}
```

- 네 줄의 `len`·`cap` 은 각각 무엇인가?
- 내용이 같은가 — `cap` 이 같은가?
- 이 결과가 뒤엎는 문장은 무엇인가?
- 그러면 `cap` 으로 판단해도 되는 것은 무엇 하나인가?

### 5. 예측과 실제가 어긋나는 줄이 있는가 (예측)

```go
// t06g.go
package main

import (
	"fmt"
	"unsafe"
)

// sameArray 는 두 슬라이스가 같은 기반 배열을 보는지 답한다.
func sameArray(a, b []int) bool {
	return unsafe.SliceData(a) == unsafe.SliceData(b)
}

// willFit 은 cap 만 보고 「재할당이 안 일어난다」를 예측한다.
func willFit(s []int, n int) bool { return len(s)+n <= cap(s) }

func try(tag string, s []int, add ...int) {
	pred := willFit(s, len(add))
	out := append(s, add...)
	fmt.Printf("%-26s len=%d cap=%-2d + %d개 → len=%d cap=%-2d  예측(재할당 없음)=%-5t 실제(같은 배열)=%t\n",
		tag, len(s), cap(s), len(add), len(out), cap(out), pred, sameArray(s, out))
}

func main() {
	try("make([]int,3,6) + 1개", make([]int, 3, 6), 9)
	try("make([]int,3,6) + 3개", make([]int, 3, 6), 9, 9, 9)
	try("make([]int,3,6) + 4개", make([]int, 3, 6), 9, 9, 9, 9)
	try("make([]int,3,3) + 1개", make([]int, 3, 3), 9)
	try("[]int{1,2,3}    + 0개", []int{1, 2, 3})
	var nilS []int
	try("nil             + 1개", nilS, 9)
}
```

- 여섯 줄의 `len`·`cap`·「예측」·「실제」를 각각 적어라.
- 예측식은 무엇인가 — 그 식이 맞는 근거는 명세인가 관찰인가?
- 마지막 줄(`nil` 에 한 개)의 결과 `cap` 은 얼마인가 — `var n []int; n = append(n, 1)` 로 한 개를 붙일 때와 같은가?
- `[]int{1,2,3}` 에 **0개**를 붙이면 어떻게 되는가?

### 6. 네 줄 중 몇 줄이 컴파일 에러인가 (예측)

```go
// t06d.go
package main

import "fmt"

func main() {
	s := make([]int, 0, 4)
	append(s, 1)
	fmt.Println(s)

	var arr [3]int
	arr = append(arr, 1)
	fmt.Println(arr)

	t := make([]int, 5, 3)
	fmt.Println(t)

	u := append(s, "문자열")
	fmt.Println(u)
}
```

- 컴파일 에러는 몇 줄이고 각각 무슨 메시지인가?
- 첫 줄이 에러인 이유를 Go 의 문장 규칙으로 설명하라.
- `make([]int, 5, 3)` 이 잡히는 조건은 무엇인가 — 변수였다면?
- 이 중 **05번 주제의 「함수 안 `append` 가 안 보이는」 사고**와 성격이 같은 것이 있는가?

### 7. 왜 `append` 는 결과를 돌려주는 함수인가 (왜)

- `s.push(x)` 꼴로 만들 수 없었던 이유를 **헤더라는 낱말로** 설명하라.
- 명세는 `append` 의 반환을 어떻게 적었는가?
- 결과를 안 받으면 어떻게 되는가 — 컴파일 타임인가 런타임인가?
- 함수 매개변수로 받은 슬라이스에 `append` 한 결과를 호출자에게 주려면 무엇을 해야 하는가?

### 8. `make` 의 인자를 잘못 주면 (경계)

```go
// t06h.go
package main

import (
	"fmt"
	"os"
)

func main() {
	n := 3
	fmt.Println("make([]int, 3) 은 된다 :", make([]int, n))
	fmt.Fprintln(os.Stderr, "----- 여기까지 stdout · 아래부터 패닉 -----")
	bad := -1
	fmt.Println(make([]int, bad))
}
```

- 이 프로그램은 어디까지 찍고 무엇으로 끝나는가 — **메시지 전문**과 **종료 코드**는?
- `bad` 를 `-1` 이라는 **상수**로 바꾸면 무엇이 달라지는가?
- `make([]int, 5, 3)` 은 어느 쪽인가?
- 이 갈림은 03·04번 주제의 무엇과 같은 모양인가?

### 9. 명세가 약속한 것과 안 한 것 (경계)

아래 여섯 가지를 **「명세 보장」 / 「구현(gc)」** 으로 갈라라.

- ① `0 <= len(s) <= cap(s)`
- ② `cap` 이 모자라면 새 배열을 잡는다
- ③ 새 `cap` 이 512 다음에 848이 된다
- ④ `append` 는 결과를 돌려준다
- ⑤ `append(n, 1)` 은 `cap` 4인데 `append(n, add...)` 는 `cap` 1이다
- ⑥ 음수 길이의 `make` 는 런타임 패닉이다

### 10. 다른 언어·다른 갈래와 나란히 놓기 (연결)

- Rust 슬라이스에는 `cap` 이 있는가 — 없다면 길이를 늘리는 일은 누구의 것인가?
- 파이썬 리스트는 길이를 어떻게 늘리는가 — Go 의 `append` 와 무엇이 다른가?
- 「배로 늘리면 왜 상각 O(1)인가」의 정본은 어느 갈래인가?
- 「미리 잡으면 빠르다」를 주장하려면 무엇이 더 필요한가 — 그 정본은 몇 번 주제인가?

### 11. 다른 주제와 잇기 (연결)

- 「이사하면 공유가 끊긴다」의 정본은 몇 번 주제인가?
- 「이사하지 않아서 이웃이 덮인다」가 버그가 되는 사례를 모은 주제는 몇 번인가?
- 이사를 **일부러 강제하는** 법의 정본은 몇 번 주제인가?
- `slices.Grow`·`slices.Clip` 의 정본은 몇 번 주제이고 몇 버전부터인가?
- 가변 인자(`x...`)의 정본은 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

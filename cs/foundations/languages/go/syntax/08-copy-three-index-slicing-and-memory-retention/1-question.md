# go/syntax/08 — `copy`·3-인덱스 슬라이스·재슬라이싱의 메모리 유지 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> ★★ 이 주제에는 **두 가지 다른 질문이 섞여 있다** — 「**공유가 끊겼나**」와 「**메모리를 놓았나**」.
> 답할 때 **둘을 갈라서** 적어라. 한쪽만 되는 도구가 있다.
> ★ 메모리 수치를 묻는 문항은 **절댓값이 아니라 패턴**을 물은 것이다.
> 소스는 전부 `go build -trimpath -o prog . && ./prog` 로 던졌다. 모듈 이름은 `ex` 다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 여섯 줄의 `copy` 반환값 (예측)

```go
// t08a.go
package main

import "fmt"

func main() {
	src := []int{1, 2, 3, 4, 5}

	short := make([]int, 2)
	n1 := copy(short, src)
	fmt.Printf("copy(len2, len5) -> n=%d  dst=%v\n", n1, short)

	long := make([]int, 8)
	n2 := copy(long, src)
	fmt.Printf("copy(len8, len5) -> n=%d  dst=%v\n", n2, long)

	var nilDst []int
	n3 := copy(nilDst, src)
	fmt.Printf("copy(nil,  len5) -> n=%d  dst=%v\n", n3, nilDst)

	n4 := copy(long, nilDst)
	fmt.Printf("copy(len8, nil ) -> n=%d\n", n4)

	fmt.Println()
	full := make([]int, len(src))
	copy(full, src)
	full[0] = 99
	fmt.Println("베낀 뒤 full[0]=99 → src =", src, " full =", full)
	fmt.Println("같은 배열인가 :", &src[0] == &full[0])

	cap8 := make([]int, 0, 8)
	n5 := copy(cap8, src)
	fmt.Printf("\ncopy(make([]int,0,8), len5) -> n=%d   ← cap 이 아니라 len 을 본다\n", n5)
}
```

- 여섯 줄의 `n` 은 각각 무엇인가?
- `nil` 이 인자로 들어간 두 줄은 패닉하는가?
- `&src[0] == &full[0]` 은 무엇인가?
- 마지막 줄이 **0**이라면 그 이유는 무엇인가?

### 2. 같은 배열 안에서 밀면 (예측)

```go
// t08b.go
package main

import "fmt"

func main() {
	a := []int{0, 1, 2, 3, 4, 5}
	n1 := copy(a, a[2:])
	fmt.Printf("copy(a, a[2:]) -> n=%d  a=%v   (왼쪽으로 민다)\n", n1, a)

	b := []int{0, 1, 2, 3, 4, 5}
	n2 := copy(b[2:], b)
	fmt.Printf("copy(b[2:], b) -> n=%d  b=%v   (오른쪽으로 민다)\n", n2, b)

	fmt.Println()
	fmt.Println("오른쪽으로 밀 때 앞 칸이 꼬리에 번지지 않았다 — 겹쳐도 결과가 정해져 있다.")

	s := []byte("abcdef")
	n3 := copy(s, "XY")
	fmt.Printf("copy([]byte, \"XY\") -> n=%d  s=%q\n", n3, s)
}
```

- `copy(a, a[2:])` 뒤 `a` 는 무엇인가 — `n` 은?
- `copy(b[2:], b)` 뒤 `b` 는 무엇인가 — **앞 칸이 꼬리로 번지는가**?
- 그 답의 근거가 되는 명세 문장은 무엇인가?
- `copy([]byte, "XY")` 는 되는가?

### 3. ★ 숫자 하나를 더 적으면 (예측)

```go
// t08c.go
package main

import (
	"fmt"
	"unsafe"
)

func sameArray(a, b []int) bool { return unsafe.SliceData(a) == unsafe.SliceData(b) }

func main() {
	all := []int{1, 2, 3, 4, 5, 6}

	two := all[:3]
	three := all[:3:3]
	fmt.Printf("all[:3]    len=%d cap=%d\n", len(two), cap(two))
	fmt.Printf("all[:3:3]  len=%d cap=%d   ← cap 을 len 까지 잘랐다\n", len(three), cap(three))

	t2 := append(two, 99)
	fmt.Printf("\nappend(all[:3], 99)   → 같은 배열인가 %t   그 뒤 all=%v\n", sameArray(two, t2), all)

	all2 := []int{1, 2, 3, 4, 5, 6}
	th := all2[:3:3]
	t3 := append(th, 99)
	fmt.Printf("append(all[:3:3], 99) → 같은 배열인가 %t  그 뒤 all=%v\n", sameArray(th, t3), all2)
	fmt.Printf("돌려받은 것은 %v (len=%d cap=%d)\n", t3, len(t3), cap(t3))
}
```

- `all[:3]` 과 `all[:3:3]` 의 `cap` 은 각각 무엇인가?
- 두 `append` 뒤 「같은 배열인가」는 각각 무엇이고, 그때 `all` 은 각각 무엇인가?
- 두 번째 `append` 가 **돌려준 슬라이스의 `cap`** 은 무엇인가 — 왜 그 값인가?
- 이 도구는 **메모리도 놓아 주는가**?

### 4. 세 함수의 결과와 원본 (예측)

```go
// t08e.go
package main

import "fmt"

// Prefix 는 t07e 의 그 함수다 — 원본을 짓이긴다.
func Prefix(s []int, n int) []int { return append(s[:n], 0) }

// PrefixCut 은 3-인덱스로 cap 을 잘라 append 가 반드시 새 배열을 잡게 한다.
func PrefixCut(s []int, n int) []int { return append(s[:n:n], 0) }

// PrefixCopy 는 아예 베껴 놓고 시작한다.
func PrefixCopy(s []int, n int) []int {
	out := make([]int, n, n+1)
	copy(out, s[:n])
	return append(out, 0)
}

func main() {
	for _, f := range []struct {
		name string
		fn   func([]int, int) []int
	}{
		{"Prefix     (그대로)", Prefix},
		{"PrefixCut  (s[:n:n])", PrefixCut},
		{"PrefixCopy (copy)", PrefixCopy},
	} {
		data := []int{1, 2, 3, 4, 5}
		got := f.fn(data, 2)
		fmt.Printf("%-22s 결과=%v  그 뒤 원본=%v\n", f.name, got, data)
	}
}
```

- 세 함수의 **반환값**은 각각 무엇인가 — 같은가?
- 세 함수를 부른 뒤 **원본**은 각각 무엇인가?
- 둘째와 셋째는 **언제 복사가 일어나는지**가 어떻게 다른가?
- 「붙일지 안 붙일지 모를 때」는 어느 것을 고르는가?

### 5. ★★ 다섯 줄의 MiB (예측)

```go
// t08f.go
package main

import (
	"fmt"
	"runtime"
)

// heapMiB 는 GC 를 한 번 돌린 뒤 살아 있는 힙을 MiB 로 반올림해 돌려준다.
// 절댓값이 아니라 「64 가 남아 있나 사라졌나」만 읽는다.
func heapMiB() int {
	runtime.GC()
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	return int((m.HeapAlloc + 512*1024) / (1024 * 1024))
}

// head3 는 앞 3바이트를 잘라 돌려준다 — 기반 배열은 그대로다.
func head3(src []byte) []byte { return src[:3] }

// head3Copy 는 앞 3바이트를 새 배열에 베껴 돌려준다.
func head3Copy(src []byte) []byte {
	out := make([]byte, 3)
	copy(out, src[:3])
	return out
}

func main() {
	fmt.Println("① 바탕                        =", heapMiB(), "MiB")

	big := make([]byte, 64<<20)
	big[0] = 'A'
	fmt.Println("② 64MiB 를 잡은 뒤            =", heapMiB(), "MiB")

	kept := head3(big)
	big = nil
	fmt.Printf("③ 조각(len=%d cap=%d)만 들고  = %d MiB  %q\n",
		len(kept), cap(kept), heapMiB(), kept[0])

	kept = nil
	fmt.Println("④ 그 조각마저 버린 뒤         =", heapMiB(), "MiB")

	big2 := make([]byte, 64<<20)
	big2[0] = 'B'
	kept2 := head3Copy(big2)
	big2 = nil
	fmt.Printf("⑤ copy 로 끊은 조각(len=%d cap=%d) = %d MiB  %q\n",
		len(kept2), cap(kept2), heapMiB(), kept2[0])
}
```

- 다섯 줄의 MiB 값은 각각 무엇인가?
- ③에서 찍히는 조각의 `cap` 은 무엇인가 — 그 숫자가 말하는 것은?
- ④가 그 값인 것이 무엇을 증명하는가?
- 이 프로그램이 조각을 **실제로 읽는 이유**는 무엇인가?

### 6. `Clone` 과 `Clip` 은 무엇이 다른가 (예측)

```go
// t08g.go
package main

import (
	"fmt"
	"slices"
	"unsafe"
)

func sameArray(a, b []int) bool { return unsafe.SliceData(a) == unsafe.SliceData(b) }

func main() {
	src := []int{1, 2, 3, 4, 5, 6}
	part := src[1:3]
	fmt.Printf("part := src[1:3]  len=%d cap=%d\n", len(part), cap(part))

	cl := slices.Clone(part)
	fmt.Printf("slices.Clone(part) len=%d cap=%d  같은 배열인가 %t\n", len(cl), cap(cl), sameArray(part, cl))

	cp := slices.Clip(part)
	fmt.Printf("slices.Clip(part)  len=%d cap=%d  같은 배열인가 %t\n", len(cp), cap(cp), sameArray(part, cp))

	man := part[:len(part):len(part)]
	fmt.Printf("part[:2:2]         len=%d cap=%d  같은 배열인가 %t\n", len(man), cap(man), sameArray(part, man))

	cl[0] = 99
	fmt.Println()
	fmt.Println("Clone 한 쪽을 99 로 바꾼 뒤 src =", src)

	var nilS []int
	fmt.Println("slices.Clone(nil) == nil :", slices.Clone(nilS) == nil)
}
```

- 네 줄의 `len`·`cap`·「같은 배열인가」는 각각 무엇인가?
- `Clone` 과 `Clip` 의 `cap` 이 같은데 갈리는 것은 무엇인가?
- `slices.Clone(nil)` 은 무엇인가?
- 둘은 각각 몇 버전부터인가?

### 7. 세 번째 숫자를 잘못 주면 (경계)

```go
// t08d.go
package main

import (
	"fmt"
	"os"
)

func main() {
	all := []int{1, 2, 3, 4, 5, 6}
	fmt.Printf("all[1:3:5]  len=%d cap=%d %v\n", len(all[1:3:5]), cap(all[1:3:5]), all[1:3:5])
	fmt.Printf("all[1:3:3]  len=%d cap=%d %v\n", len(all[1:3:3]), cap(all[1:3:3]), all[1:3:3])
	fmt.Printf("all[3:3:3]  len=%d cap=%d %v\n", len(all[3:3:3]), cap(all[3:3:3]), all[3:3:3])
	fmt.Fprintln(os.Stderr, "----- 여기까지 stdout · 아래부터 패닉 -----")
	hi := 3
	fmt.Println(all[1:hi:2])
}
```

- 앞의 세 줄은 각각 `len`·`cap` 이 무엇인가?
- 마지막 줄에서 무슨 일이 일어나는가 — **메시지 전문**과 **종료 코드**는?
- 범위 조건을 명세 그대로 적어라.
- 문자열에 `s[1:3:5]` 를 쓰면 어떻게 되는가?

### 8. 지운 것 같은데 안 지워진 것 (경계)

```go
// t08h.go
package main

import "fmt"

// row 는 포인터 하나를 담은 작은 구조체다.
type row struct{ id int }

func main() {
	rows := []*row{{1}, {2}, {3}, {4}}
	kept := rows[:2]
	fmt.Printf("kept len=%d cap=%d\n", len(kept), cap(kept))
	fmt.Println("배열을 cap 까지 펴 보면 아직 네 칸이 살아 있다 :", len(kept[:cap(kept)]))
	for i, p := range kept[:cap(kept)] {
		fmt.Printf("  [%d] = %v\n", i, p)
	}

	tail := rows[len(kept):]
	clear(tail)
	fmt.Println("\nclear(rows[2:]) 한 뒤")
	for i, p := range kept[:cap(kept)] {
		fmt.Printf("  [%d] = %v\n", i, p)
	}

	nums := []int{1, 2, 3}
	clear(nums)
	fmt.Println("\nclear 는 슬라이스를 제로값으로 민다 :", nums, " len=", len(nums))
}
```

- `kept := rows[:2]` 뒤 `kept[:cap(kept)]` 에는 몇 칸이 살아 있는가?
- `clear(rows[2:])` 가 하는 일은 무엇인가 — 길이가 바뀌는가?
- 원소가 `int` 였다면 이 작업이 필요한가?
- 07번 주제의 어느 관용구가 남긴 문제를 여기서 치우는가?

### 9. 「복사했다」는 어디까지인가 (경계)

```go
// t08i.go
package main

import "fmt"

func main() {
	src := [][]int{{1, 2}, {3, 4}}
	dst := make([][]int, len(src))
	n := copy(dst, src)
	fmt.Printf("copy(dst, src) -> n=%d\n", n)

	dst[0][0] = 99
	fmt.Println("dst[0][0] = 99 한 뒤")
	fmt.Println("  src =", src, " ← 안쪽이 같이 바뀐다")
	fmt.Println("  dst =", dst)

	dst[1] = []int{7, 7}
	fmt.Println("dst[1] 을 통째로 갈아 끼우면")
	fmt.Println("  src =", src, " ← 이쪽은 안 바뀐다")
	fmt.Println("  dst =", dst)

	fmt.Println()
	fmt.Println("바깥 칸은 베껴졌고 안쪽 헤더가 가리키는 배열은 공유다 :",
		&src[0][0] == &dst[0][0])
}
```

- `copy(dst, src)` 의 `n` 은 무엇인가?
- `dst[0][0] = 99` 뒤 `src` 는 어떻게 되는가 — `dst[1]` 을 통째로 갈아 끼우면?
- `slices.Clone` 을 썼다면 달라지는가?
- `[][]int` 를 진짜로 복사하려면 무엇을 해야 하는가?

### 10. 잘랐다고 믿은 뒤쪽 (경계)

```go
// t08j.go
package main

import "fmt"

func main() {
	buf := []byte("user=admin;pw=hunter2")
	head := buf[:10]
	fmt.Printf("head          = %q  len=%d cap=%d\n", head, len(head), cap(head))
	fmt.Printf("head[:cap()]  = %q   ← 잘랐다고 믿은 뒤쪽이 그대로 있다\n", head[:cap(head)])

	cut := make([]byte, 10)
	copy(cut, buf[:10])
	fmt.Printf("\ncopy 로 뜬 것   = %q  len=%d cap=%d\n", cut, len(cut), cap(cut))
	fmt.Printf("cut[:cap()]   = %q   ← 되살릴 뒤쪽이 없다\n", cut[:cap(cut)])
}
```

- `head` 와 `head[:cap(head)]` 는 각각 무엇으로 찍히는가?
- `copy` 로 뜬 쪽은 왜 다른가 — `cap` 이 무엇이기 때문인가?
- 이것은 (5)번 문항의 메모리 유지와 **같은 사실인가 다른 사실인가**?
- 민감한 데이터를 정말 지우려면 무엇을 쓰는가?

### 11. 다른 주제·다른 언어와 잇기 (연결)

- 「공유를 끊는 것」과 「메모리를 놓는 것」은 각각 어느 도구인가 — 한쪽만 되는 것은?
- 07번 주제의 버그를 막는 한 글자짜리 처방은 무엇인가?
- GC 가 **어떻게** 회수하는지의 정본은 어느 갈래인가?
- Rust 에서 슬라이스를 소유한 값으로 바꾸려면 무엇을 부르는가 — 그것이 Go 의 무엇에 해당하나?
- `slices.Clone`·`Clip`·`Grow` 의 정본은 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

# go/syntax/08 — `copy`·3-인덱스 슬라이스·재슬라이싱의 메모리 유지 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★★ 답을 적을 때 「**공유가 끊겼나**」와 「**메모리를 놓았나**」를 갈라 적어라. 한쪽만 되는 도구가 있다.
> ★ **근거로 읽을 칸** — `copy` 의 반환값, `len`·`cap`, 기반 배열이 **같나 다르나**,
> (5)절의 **0/64/64/0/0 패턴**, 패닉 문장 본문, 종료 코드.
> **근거로 읽지 않을 칸** — `HeapAlloc` 의 정확한 바이트(그래서 **MiB 로 반올림**했다),
> **회수 시점**(구현), `cap` 의 수치(구현 — 06번 주제), 주소 자체, 패닉 스택의 `goroutine N`·`+0x…`.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `2 · 5 · 0 · 0` — 그리고 마지막은 **`cap` 이 아니라 `len` 때문에 0**이다

**출력**

```text
===== 소스: t08a.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
copy(len2, len5) -> n=2  dst=[1 2]
copy(len8, len5) -> n=5  dst=[1 2 3 4 5 0 0 0]
copy(nil,  len5) -> n=0  dst=[]
copy(len8, nil ) -> n=0

베낀 뒤 full[0]=99 → src = [1 2 3 4 5]  full = [99 2 3 4 5]
같은 배열인가 : false

copy(make([]int,0,8), len5) -> n=0   ← cap 이 아니라 len 을 본다
(exit 0)
```

**왜 그런가**

| 호출 | `n` | 왜 |
|---|---|---|
| `copy(len 2, len 5)` | **2** | 짧은 쪽이 `dst` |
| `copy(len 8, len 5)` | **5** | 짧은 쪽이 `src`. 나머지 세 칸은 제로값 그대로 |
| `copy(nil, len 5)` | **0** | `len(dst)` 가 0 |
| `copy(len 8, nil)` | **0** | `len(src)` 가 0 |
| `copy(make([]int,0,8), len 5)` | **0** | ★ **`cap` 8이어도 `len` 이 0이다** |

- 명세: "The number of elements copied is **the minimum of `len(src)` and `len(dst)`**."
- **`nil` 이 들어가도 패닉하지 않는다.** 0을 돌려줄 뿐이다.
- `full` 로 베낀 뒤 `full[0] = 99` 가 `src` 에 **안 보이고** `&src[0] == &full[0]` 이 **false** —
  **공유가 끊겼다.**
- ★★ 마지막 줄이 `copy` 에서 가장 자주 틀리는 자리다.
  `make([]T, 0, n)` 을 목적지로 주면 **한 개도 안 베껴진다.**
  고치는 법은 `make([]T, len(src))` 또는 `append(dst[:0], src...)` 다.

### 2. 왼쪽으로도 오른쪽으로도 **번지지 않는다**

**출력**

```text
===== 소스: t08b.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
copy(a, a[2:]) -> n=4  a=[2 3 4 5 4 5]   (왼쪽으로 민다)
copy(b[2:], b) -> n=4  b=[0 1 0 1 2 3]   (오른쪽으로 민다)

오른쪽으로 밀 때 앞 칸이 꼬리에 번지지 않았다 — 겹쳐도 결과가 정해져 있다.
copy([]byte, "XY") -> n=2  s="XYcdef"
(exit 0)
```

**왜 그런가**

- `copy(a, a[2:])` → `n` **4**, `a` 는 **`[2 3 4 5 4 5]`**.
  앞 네 칸이 두 칸 왼쪽으로 밀렸고 **뒤 두 칸은 옛 값 그대로**다.
- `copy(b[2:], b)` → `n` **4**, `b` 는 **`[0 1 0 1 2 3]`**.
  ★ 앞에서부터 한 칸씩 옮기는 순진한 구현이면 `[0 1 0 0 0 0]` 처럼 **번져야** 한다. 안 번졌다.
- 근거는 명세의 한 문장이다.

  > For both functions, **the result is independent of whether the memory referenced
  > by the arguments overlaps.**

- `copy([]byte, "XY")` 는 **된다** — `n` 2, `s` 는 `"XYcdef"`.

  > As a special case, `copy` also accepts a destination argument assignable to type `[]byte`
  > with a source argument of a **string** type.

- ★ 이 보장이 있어서 07번 주제의 삭제 관용구가 **값은 맞게** 나온다. 틀리는 것은 꼬리였다.

### 3. ★ `cap` 이 6에서 3으로 잘리고, 그 한 글자가 원본을 지킨다

**출력**

```text
===== 소스: t08c.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
all[:3]    len=3 cap=6
all[:3:3]  len=3 cap=3   ← cap 을 len 까지 잘랐다

append(all[:3], 99)   → 같은 배열인가 true   그 뒤 all=[1 2 3 99 5 6]
append(all[:3:3], 99) → 같은 배열인가 false  그 뒤 all=[1 2 3 4 5 6]
돌려받은 것은 [1 2 3 99] (len=4 cap=6)
(exit 0)
```

**왜 그런가**

| 식 | `len` | `cap` |
|---|---|---|
| `all[:3]` | 3 | **6** |
| `all[:3:3]` | 3 | **3** |

- 명세: "Additionally, it controls the resulting slice's capacity by setting it to **`max - low`**."
- `append(all[:3], 99)` → **같은 배열**(`true`). `all` 이 **`[1 2 3 99 5 6]`** 로 덮였다.
- `append(all[:3:3], 99)` → **다른 배열**(`false`). `all` 은 **`[1 2 3 4 5 6]`** 그대로다.
- 두 번째가 돌려준 슬라이스의 `cap` 은 **6**이다. 새 배열이 잡히면서 **여유가 다시 생겼기** 때문이다.
  ★ 즉 `s[:n:n]` 은 **그 한 번의 `append` 를 가르는 장치**지 영구 제한이 아니다.
  그 수치(6)는 **구현**이다(06번 주제).
- ★★ **메모리는 안 놓아 준다.** `s[:n:n]` 은 `cap` 만 자를 뿐
  **포인터는 여전히 큰 배열의 시작을 가리킨다.** (6)번 문항의 `slices.Clip` 이 그 증거다
  (결과가 **같은 배열**이다).

### 4. 셋 다 `[1 2 0]` 을 돌려주고, **원본은 하나만 망가진다**

**출력**

```text
===== 소스: t08e.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
Prefix     (그대로)       결과=[1 2 0]  그 뒤 원본=[1 2 0 4 5]
PrefixCut  (s[:n:n])   결과=[1 2 0]  그 뒤 원본=[1 2 3 4 5]
PrefixCopy (copy)      결과=[1 2 0]  그 뒤 원본=[1 2 3 4 5]
(exit 0)
```

**왜 그런가**

| 함수 | 반환값 | 부른 뒤 원본 |
|---|---|---|
| `Prefix`(그대로) | `[1 2 0]` | **`[1 2 0 4 5]`** — 짓이겨졌다 |
| `PrefixCut`(`s[:n:n]`) | `[1 2 0]` | `[1 2 3 4 5]` |
| `PrefixCopy`(`make`+`copy`) | `[1 2 0]` | `[1 2 3 4 5]` |

- **반환값만 보는 테스트는 셋을 구별하지 못한다.** 07번 주제 (5)절이 그것을 실측으로 보였다.
- 둘째와 셋째의 차이는 **언제 복사하나**다.
  - `s[:n:n]` — **다음 `append` 가 있을 때만** 복사한다. 안 붙이면 복사가 없다.
  - `make`+`copy` — **무조건** 복사한다.
- ★ 「붙일지 안 붙일지 모를 때」는 **`s[:n:n]`** 이다. 값이 싸고, 붙는 순간에만 대가를 낸다.
  **오래 들고 있어야 하면** (5)번 문항 때문에 **`copy`** 쪽이다.
- **어느 쪽이 빠른지는 이 문서에서 재지 않았다.**

### 5. ★★ **0 / 64 / 64 / 0 / 0** — 3바이트가 64MiB 를 붙잡는다

**출력**

```text
===== 소스: t08f.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
① 바탕                        = 0 MiB
② 64MiB 를 잡은 뒤            = 64 MiB
③ 조각(len=3 cap=67108864)만 들고  = 64 MiB  'A'
④ 그 조각마저 버린 뒤         = 0 MiB
⑤ copy 로 끊은 조각(len=3 cap=3) = 0 MiB  'B'
(exit 0)
```

**왜 그런가**

| 단계 | MiB | 왜 |
|---|---|---|
| ① 바탕 | **0** | 반올림하면 0이다 |
| ② 64MiB 를 잡은 뒤 | **64** | 당연하다 |
| ③ **조각만 들고** | **64** | ★ 조각이 기반 배열 전체를 가리킨다 |
| ④ 조각마저 버린 뒤 | **0** | 붙잡고 있던 것이 조각이었음이 증명된다 |
| ⑤ `copy` 로 끊은 조각 | **0** | 새 배열 3바이트만 남았다 |

- ③에서 찍히는 조각의 `cap` 은 **67108864** 다 — 정확히 64MiB.
  **`len` 은 3인데 `cap` 이 전체**라는 것이 「전체를 붙잡고 있다」의 직접 증거다.
  ★ 이것이 **명세적 근거**이고, MiB 수치는 그것을 **눈으로 보여 주는 예시**다.
- ④가 0인 것이 결정적이다 — ③의 64가 **바탕 잡음이 아니라 조각 때문**임을 가른다.
- ⑤는 `copy` 로 3바이트만 떠낸 경우다. `cap` 이 **3**이고 큰 배열은 **회수됐다.**
- ★★ 이 프로그램이 조각을 **실제로 읽는 이유** — 처음에 안 읽는 판으로 짰더니
  **②부터 0 MiB** 가 나왔다. 컴파일러·GC 가 **쓰이지 않는 값을 죽은 것으로 본다.**
  「살아 있다」를 보이려면 **실제로 써야** 한다. 이것도 구현의 성질이고, **실측으로 뒤집힌 전제**다.
- 재는 법의 한계 — `HeapAlloc` 은 **런타임의 회계**라 정확한 바이트가 흔들린다. 그래서 MiB 로 반올림했고,
  **같은 바이너리를 5회 돌려 출력 md5 가 같았다.** 읽을 것은 **패턴**이다.
  **회수 「시점」은 구현**이다 — 명세는 GC 를 말하지 않는다.
- 실무 모양 — 응답 바디를 통째로 읽어 놓고 **한 필드만 슬라이싱해 보관**하면 **응답 전체가 남는다.**

### 6. `cap` 이 둘 다 2인데 **`Clip` 만 같은 배열**이다

**출력**

```text
===== 소스: t08g.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
part := src[1:3]  len=2 cap=5
slices.Clone(part) len=2 cap=2  같은 배열인가 false
slices.Clip(part)  len=2 cap=2  같은 배열인가 true
part[:2:2]         len=2 cap=2  같은 배열인가 true

Clone 한 쪽을 99 로 바꾼 뒤 src = [1 2 3 4 5 6]
slices.Clone(nil) == nil : true
(exit 0)
```

**왜 그런가**

| 식 | `len` | `cap` | 같은 배열인가 |
|---|---|---|---|
| `part := src[1:3]` | 2 | **5** | — |
| `slices.Clone(part)` | 2 | **2** | **false** — 새 배열 |
| `slices.Clip(part)` | 2 | **2** | **true** — 같은 배열 |
| `part[:2:2]`(손으로) | 2 | **2** | **true** — `Clip` 은 이것의 이름이다 |

- ★★ **`cap` 만 보고 「끊겼다」고 판단하면 안 된다.** 둘 다 2인데 한쪽만 끊겼다.
  갈리는 것은 **기반 배열**이다.
- `Clone` 한 쪽을 `99` 로 고쳐도 `src` 는 **`[1 2 3 4 5 6]`** 그대로다.
- `slices.Clone(nil)` 은 **`nil`** 이다 — `nil` 다움을 보존한다.
- 둘 다 **1.21**부터다(`slices` 패키지와 함께 들어왔다). 정본은 목록의 **38번 주제**다.
- 정리하면 — **끊기 = `Clone`**, **선 긋기 = `Clip`**. 이름이 뜻을 말한다.

### 7. `all[1:3:2]` 에서 **`slice bounds out of range [:3:2]`** — 종료 코드 2

**출력**

```text
===== 소스: t08d.go =====
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
===== 명령: go build -trimpath -o prog . =====
(exit 0)
===== 명령: ./prog 2>&1 =====
all[1:3:5]  len=2 cap=4 [2 3]
all[1:3:3]  len=2 cap=2 [2 3]
all[3:3:3]  len=0 cap=0 []
----- 여기까지 stdout · 아래부터 패닉 -----
panic: runtime error: slice bounds out of range [:3:2]

goroutine 1 [running]:
main.main()
	ex/t08d.go:15 +0x2aa
(exit 2)
```

**왜 그런가**

| 식 | `len` | `cap` |
|---|---|---|
| `all[1:3:5]` | 2 | **4**(`5-1`) |
| `all[1:3:3]` | 2 | **2**(`3-1`) |
| `all[3:3:3]` | 0 | **0** — 빈 것이다(패닉이 아니다) |

- 마지막 줄은 `max`(2)가 `high`(3)보다 작아 **패닉**이다.

  > The indices are in range if **`0 <= low <= high <= max <= cap(a)`**, otherwise they are out of range.
  > … If the indices are out of range at run time, a **run-time panic** occurs.

- 메시지는 `panic: runtime error: slice bounds out of range [:3:2]`, 종료 코드 **2**다.
  마커 줄은 표준 오류로 찍었다.
- ★ **문자열에는 3-인덱스를 못 쓴다.** 명세가 "for an array, pointer to array, or slice `a`
  (**but not a string**)" 라고 적었다 — 컴파일 에러가 난다.
  문자열은 어차피 불변이라 `cap` 이라는 개념이 없다.

### 8. 배열에는 **네 칸이 다 살아 있다** — `clear` 가 놓아 준다

**출력**

```text
===== 소스: t08h.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
kept len=2 cap=4
배열을 cap 까지 펴 보면 아직 네 칸이 살아 있다 : 4
  [0] = &{1}
  [1] = &{2}
  [2] = &{3}
  [3] = &{4}

clear(rows[2:]) 한 뒤
  [0] = &{1}
  [1] = &{2}
  [2] = <nil>
  [3] = <nil>

clear 는 슬라이스를 제로값으로 민다 : [0 0 0]  len= 3
(exit 0)
```

**왜 그런가**

- `kept := rows[:2]` 뒤에도 `kept[:cap(kept)]` 에는 **네 칸**이 있고,
  `[2]`·`[3]` 이 여전히 `&{3}`·`&{4}` 를 **가리킨다.** 그 객체들은 회수될 수 없다.
- `clear(rows[2:])` 는 그 두 칸을 **`<nil>`** 로 민다 — **길이는 안 바뀐다.**

  > `clear(s)` `[]T` — sets all elements up to the length of `s` to the zero value of `T`

- 마지막 줄이 그것을 다시 보인다 — `clear([]int{1,2,3})` 뒤 `[0 0 0]` 이고 `len` 은 **3** 그대로다.
- ★ 원소가 `int` 처럼 **포인터를 안 품는 타입**이면 이 작업은 **필요 없다.**
  회수를 막을 것이 없기 때문이다.
- ★ 07번 주제 (3)절의 **삭제 관용구**가 남긴 꼬리를 여기서 치운다 —
  `s = append(s[:i], s[i+1:]...)` 뒤 `clear(s[len(s):len(s)+1])` 같은 꼴이다.
  `clear` 는 **1.21**부터다.

### 9. 바깥 한 겹만 — 안쪽은 공유다

**출력**

```text
===== 소스: t08i.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
copy(dst, src) -> n=2
dst[0][0] = 99 한 뒤
  src = [[99 2] [3 4]]  ← 안쪽이 같이 바뀐다
  dst = [[99 2] [3 4]]
dst[1] 을 통째로 갈아 끼우면
  src = [[99 2] [3 4]]  ← 이쪽은 안 바뀐다
  dst = [[99 2] [7 7]]

바깥 칸은 베껴졌고 안쪽 헤더가 가리키는 배열은 공유다 : true
(exit 0)
```

**왜 그런가**

- `copy(dst, src)` 의 `n` 은 **2** — 바깥 칸 두 개다.
- `dst[0][0] = 99` 가 **`src` 에도 보인다.** 베껴진 것은 **안쪽 슬라이스의 헤더**이기 때문이다.
- `dst[1]` 을 **통째로 갈아 끼우면** `src` 는 **안 바뀐다** — 바깥 칸은 진짜로 갈라져 있다.
- `&src[0][0] == &dst[0][0]` 이 **true**.
- ★ **`slices.Clone` 을 써도 달라지지 않는다.** 그것도 얕다.
  Go 에는 깊은 복사를 해 주는 **표준 장치가 없다.**
- 진짜로 복사하려면 **줄마다** 복사하는 루프를 직접 쓴다.

  ```text
  out := make([][]int, len(src))
  for i := range src {
      out[i] = slices.Clone(src[i])
  }
  ```

### 10. `head` 는 열 글자, `head[:cap(head)]` 는 **전부**다

**출력**

```text
===== 소스: t08j.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
head          = "user=admin"  len=10 cap=21
head[:cap()]  = "user=admin;pw=hunter2"   ← 잘랐다고 믿은 뒤쪽이 그대로 있다

copy 로 뜬 것   = "user=admin"  len=10 cap=10
cut[:cap()]   = "user=admin"   ← 되살릴 뒤쪽이 없다
(exit 0)
```

**왜 그런가**

- `head := buf[:10]` 은 **`"user=admin"`** 이다. `cap` 은 **21** — 원본 전체 길이다.
- `head[:cap(head)]` 는 **`"user=admin;pw=hunter2"`** — **잘랐다고 믿은 뒤쪽이 그대로 읽힌다.**
- `copy` 로 뜬 쪽은 `cap` 이 **10**이라 `cut[:cap(cut)]` 도 **`"user=admin"`** 이다.
  **되살릴 뒤쪽이 없다.**
- ★ (5)번 문항과 **같은 사실의 다른 얼굴**이다. 하나의 원인(슬라이스가 기반 배열을 가리킨다)이
  한쪽에서는 **메모리가 안 준다**로, 한쪽에서는 **데이터가 안 사라진다**로 드러난다.
- 민감한 데이터를 정말 지우려면 — **필요한 만큼만 `copy` 로 떠내고**,
  원본 버퍼는 **`clear` 로 민다.** 슬라이싱은 지우는 것이 아니다.

### 11. 다른 주제·다른 언어와 잇기

**출력** — 없음(연결 문항).

**왜 그런가**

| 문제 | 도구 | 메모리도 놓나 |
|---|---|---|
| 공유를 끊는다 | `s[:n:n]` = `slices.Clip` | **아니다** — `cap` 만 자른다 |
| 공유를 끊는다 | `copy` / `slices.Clone` | **놓는다** |
| 꼬리가 붙잡은 것을 놓는다 | `clear(s[n:])` | 놓는다(포인터 원소일 때) |

- ★ **한쪽만 되는 것이 `s[:n:n]`** 이다. 이것 하나를 갈라 두면 이 주제의 절반이 정리된다.
- **07번 주제의 버그를 막는 한 글자짜리 처방** — `append(s[:n], …)` 를 **`append(s[:n:n], …)`** 로.
  정본은 목록의 **07번 주제**(버그)와 이 주제 (4)절(처방)이다.
- **GC 가 어떻게 회수하는지** — [`../../../../memory-management/`](../../../../memory-management/).
  **그쪽은 스택·힙·표시-쓸기까지**, 여기는 **무엇이 무엇을 붙잡는지**부터다.
- **Rust** 에서 슬라이스를 소유한 값으로 바꾸려면 **`to_vec()`** 을 부른다 —
  [`../../../rust/syntax/15-slices-ranges-and-utf8-boundaries/`](../../../rust/syntax/15-slices-ranges-and-utf8-boundaries/) (8)절이
  「반대 방향은 비어 있다 — `&[T]` 에서 `&Vec<T>` 로 가는 공짜 강제는 없다(`to_vec()` 이라는 **복사**뿐이다)」
  라고 적었다. **그것이 Go 의 `slices.Clone` 에 해당한다.**
  ★ 다만 Rust 에는 **`Clip` 에 해당하는 것이 없다** — 슬라이스에 `cap` 이 없어 그런 문제가 안 생긴다.
- **`slices.Clone`·`Clip`·`Grow`** — 목록의 **38번 주제**. 전부 **1.21**부터다.

---

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행 1회** | 재실행 결과가 `diff -rq` 로 **동일** |
| 판 확인 | `go version` · `go env GOOS GOARCH GOVERSION` | 1 | `go1.27.1 linux/amd64` |
| `copy` 여섯 줄 (`t08a`) | `go build && ./prog` | 1 | `2 · 5 · 0 · 0` · 끊김 확인 · **`cap` 8에 `len` 0이면 0** |
| 겹침 (`t08b`) | 〃 | 1 | 양방향 모두 **번지지 않음** |
| ★ 3-인덱스 (`t08c`) | 〃 | 1 | `cap` 6 → 3 · 한쪽만 원본이 덮임 |
| 3-인덱스 패닉 (`t08d`) | `go build` · `./prog 2>&1` | 1 | `slice bounds out of range [:3:2]` · **exit 2** |
| 세 처방 (`t08e`) | `go build && ./prog` | 1 | 반환값 셋 다 같고 원본은 하나만 망가짐 |
| ★★ 메모리 유지 (`t08f`) | 〃 + `./prog \| md5sum` **5회** | **5** | **0/64/64/0/0** · md5 **5회 동일** |
| `Clone`·`Clip` (`t08g`) | `go build && ./prog` | 1 | `cap` 둘 다 2 · **`Clip` 만 같은 배열** |
| `clear` (`t08h`) | 〃 | 1 | 꼬리 두 칸이 `<nil>` 로 · 길이 불변 |
| 얕은 `copy` (`t08i`) | 〃 | 1 | 안쪽 공유 · 바깥은 갈림 |
| 되살아나는 뒤쪽 (`t08j`) | 〃 | 1 | `cap` 21 vs 10 |
| 형태 (`t08form`) | 〃 | 1 | `3 [2 3] 2 [2 3] 2 [2 3] 2 [2 3]` |

**구현·환경에 달린 항목**(판이 오르거나 GC 가 바뀌면 **다시 찍어야 하는** 것)

| 항목 | 왜 |
|---|---|
| **`HeapAlloc` 의 정확한 바이트** | **런타임의 회계**. 그래서 MiB 로 반올림해 읽었다 |
| **회수 「시점」**(④가 0이 되는 것) | **구현(GC)**. 명세는 GC 를 전혀 말하지 않는다 |
| **조각을 안 읽으면 ②부터 0이 되는 것** | **구현(최적화·GC)**. 실측으로 뒤집힌 전제라 프로그램이 조각을 읽도록 고쳤다 |
| `append` 뒤 `cap` 이 6이 되는 것 | **gc 의 성장 전략**(06번 주제) |
| `slices.Clip`·`Clone`·`clear` 가 있는 것 | **1.21+**. 그 이전 판에서는 `s[:n:n]` 과 손 루프를 쓴다 |
| 기반 배열의 **주소 자체** | 실행마다 다르다 — 동일성만 찍었다 |
| 패닉 스택의 `goroutine 1 [running]` 과 `+0x…` | 런타임·빌드 산출물 |
| 「`copy` 와 `s[:n:n]` 중 어느 쪽이 빠른가」 | **안 쟀다.** 벤치마크가 따로 필요하다(목록의 **50번 주제**) |
| 「`copy` 가 `memmove` 로 내려가는가」 | **확인하지 않았다.** 어셈블리로 볼 수는 있지만 이 문서의 범위 밖이다 |
| 큰 **문자열**의 슬라이싱이 같은 유지를 만드는가 | **안 던져 봤다.** `strings.Clone`(1.18)이 그 처방이다 |

★ **다시 찍는 법** — `capture.sh` 를 그대로 돌리고 `diff -rq` 한다.
(5)절의 MiB 패턴이 달라졌다면 **회수 시점이 바뀐 것**이므로 본문의 「구현」 표시를 먼저 확인한다.

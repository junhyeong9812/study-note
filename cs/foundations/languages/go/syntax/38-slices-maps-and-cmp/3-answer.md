# go/syntax/38 — `slices`·`maps`·`cmp`(1.21) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★ **근거로 읽을 칸** — 격자의 참거짓 · `4 / 12` · `20판 … 1` · 비교 함수 위반의 다섯 줄 · NaN 여덟 줄 · `4 / 5` · 순서 **가짓수**.
> **근거로 읽지 않을 칸** — `maps.Keys` 가 한 판에서 낸 **특정 순서**(그래서 가짓수로 접었다).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `SortFunc` 는 12 까지 유지·13 부터 깨짐, `SortStableFunc` 는 전부 유지 — `4 / 12` · 20판 1 가지(보장 아님)

**출력**

```text
===== 소스: t38stable.go =====
package main

import (
	"cmp"
	"fmt"
	"math/rand/v2"
	"slices"
)

type rec struct{ key, id int } // id 는 처음 자리

// 같은 key 끼리 id 가 오름차순으로 남았나.
func keptOrder(xs []rec) bool {
	for i := 1; i < len(xs); i++ {
		if xs[i-1].key == xs[i].key && xs[i-1].id > xs[i].id {
			return false
		}
	}
	return true
}

func data(n int) []rec {
	r := rand.New(rand.NewPCG(1, 2)) // 시드 고정 — 같은 입력
	xs := make([]rec, n)
	for i := range xs {
		xs[i] = rec{r.IntN(3), i} // key 는 0·1·2 셋뿐이다
	}
	return xs
}

func main() {
	byKey := func(a, b rec) int { return cmp.Compare(a.key, b.key) }
	broken, cells := 0, 0
	for _, n := range []int{8, 12, 13, 20, 100, 1000} {
		a, b := data(n), data(n)
		slices.SortFunc(a, byKey)
		slices.SortStableFunc(b, byKey)
		ka, kb := keptOrder(a), keptOrder(b)
		for _, k := range []bool{ka, kb} {
			cells++
			if !k {
				broken++
			}
		}
		fmt.Printf("n=%-4d SortFunc 정렬됐나=%v 원래 순서 남았나=%v · SortStableFunc 정렬됐나=%v 원래 순서 남았나=%v\n",
			n, slices.IsSortedFunc(a, byKey), ka, slices.IsSortedFunc(b, byKey), kb)
	}
	fmt.Printf("같은 key 의 원래 순서가 깨진 칸 %d / %d\n", broken, cells)
}
===== 명령: go build -trimpath -o prog . && ./prog && echo "20판 출력이 몇 가지인가: $(for i in $(seq 20); do ./prog | md5sum; done | sort -u | wc -l)" =====
n=8    SortFunc 정렬됐나=true 원래 순서 남았나=true · SortStableFunc 정렬됐나=true 원래 순서 남았나=true
n=12   SortFunc 정렬됐나=true 원래 순서 남았나=true · SortStableFunc 정렬됐나=true 원래 순서 남았나=true
n=13   SortFunc 정렬됐나=true 원래 순서 남았나=false · SortStableFunc 정렬됐나=true 원래 순서 남았나=true
n=20   SortFunc 정렬됐나=true 원래 순서 남았나=false · SortStableFunc 정렬됐나=true 원래 순서 남았나=true
n=100  SortFunc 정렬됐나=true 원래 순서 남았나=false · SortStableFunc 정렬됐나=true 원래 순서 남았나=true
n=1000 SortFunc 정렬됐나=true 원래 순서 남았나=false · SortStableFunc 정렬됐나=true 원래 순서 남았나=true
같은 key 의 원래 순서가 깨진 칸 4 / 12
20판 출력이 몇 가지인가: 1
(exit 0)
```

**왜 그런가**

- ★★★ **여섯 줄 전부 `정렬됐나=true`** — key 순으로는 둘 다 맞다. 갈린 것은 **같은 key 사이의 순서**뿐이다.
- ★★★ **`SortFunc` 는 `n=8`·`12` 에서 `true`, `n=13` 부터 `false`** — 깨진 넷이 `4 / 12` 의 전부다. `SortStableFunc` 는 문서대로 여섯 칸 다 지켰다.
- ★★ **`20판 출력이 몇 가지인가: 1`** — 같은 입력이면 같은 결과. **보장이 아니라 구현**이다(2번의 `xorshift(length)`).

### 2. `length <= maxInsertion`(12) 이면 삽입 정렬 — 문서에는 없다

**출력**

```text
===== 명령: sed -n "61,62p;72,73p" "$(go env GOROOT)/src/slices/zsortanyfunc.go"; grep -n "random := xorshift" "$(go env GOROOT)/src/slices/zsortanyfunc.go" =====
func pdqsortCmpFunc[E any](data []E, a, b, limit int, cmp func(a, b E) int) {
	const maxInsertion = 12
		if length <= maxInsertion {
			insertionSortCmpFunc(data, a, b, cmp)
243:		random := xorshift(length)
(exit 0)
```

- ★★★ **12 이하는 삽입 정렬**(안정)로 넘긴다. 13 부터 pdqsort 분할이 들어와 섞인다.
- ★★★ **문서에 12 는 없다** — 문서는 「**not guaranteed to be stable**」 한 줄뿐이다. **작은 입력의 테스트가 「안정하더라」를 확인해 주는 함정**이 이것이다.
- ★ `random := xorshift(length)` — 분할이 한쪽으로 쏠리지 않게 원소를 흩뜨리는 함수(`breakPatternsCmpFunc`)의 난수가 **길이로 시드**된다. 1번의 「1 가지」의 까닭으로 **읽힌다**(추론) — 어느 쪽이든 **구현**이다.

### 3. 같은 값은 구별이 안 되니까 — `0` 과 `-0` 으로 물었다 · `n=40` 에서 섞였다 · 문서는 말이 없다

**출력**

```text
===== 소스: t38zero.go =====
package main

import (
	"fmt"
	"math"
	"math/rand/v2"
	"slices"
)

// 0 과 -0 은 == 로 같다. 정렬 뒤 두 영의 부호 순서를 +/- 로 찍는다.
func signs(xs []float64) string {
	s := ""
	for _, x := range xs {
		if x == 0 {
			if math.Signbit(x) {
				s += "-"
			} else {
				s += "+"
			}
		}
	}
	return s
}

func main() {
	negZero := math.Copysign(0, -1)
	fmt.Println("0 == -0 :", 0.0 == negZero)
	for _, n := range []int{12, 40} {
		r := rand.New(rand.NewPCG(3, 4))
		xs := make([]float64, n)
		for i := range xs {
			switch r.IntN(3) {
			case 0:
				xs[i] = 0
			case 1:
				xs[i] = negZero
			default:
				xs[i] = float64(r.IntN(5) - 2)
			}
		}
		before := signs(xs)
		slices.Sort(xs)
		fmt.Printf("n=%-3d 정렬 전 영의 부호 %s\n      정렬 뒤 영의 부호 %s\n", n, before, signs(xs))
	}
}
===== 명령: go build -trimpath -o prog . && ./prog =====
0 == -0 : true
n=12  정렬 전 영의 부호 ---+-----
      정렬 뒤 영의 부호 ---+-----
n=40  정렬 전 영의 부호 ---+-----+-+++-+-+++++++-+--+--
      정렬 뒤 영의 부호 -+-------+-++++--+-+++++---++-+
(exit 0)
```

```text
===== 명령: for f in slices.Sort slices.SortFunc slices.SortStableFunc cmp.Compare slices.BinarySearch maps.Keys; do go doc $f | sed 1,2d; done =====
func Sort[S ~[]E, E cmp.Ordered](x S)
    Sort sorts a slice of any ordered type in ascending order. When sorting
    floating-point numbers, NaNs are ordered before other values.

func SortFunc[S ~[]E, E any](x S, cmp func(a, b E) int)
    SortFunc sorts the slice x in ascending order as determined by the cmp
    function. This sort is not guaranteed to be stable. cmp(a, b) should return
    a negative number when a < b, a positive number when a > b and zero when a
    == b or a and b are incomparable in the sense of a strict weak ordering.

    SortFunc requires that cmp is a strict weak ordering. See
    https://en.wikipedia.org/wiki/Weak_ordering#Strict_weak_orderings.
    The function should return 0 for incomparable items.

func SortStableFunc[S ~[]E, E any](x S, cmp func(a, b E) int)
    SortStableFunc sorts the slice x while keeping the original order of equal
    elements, using cmp to compare elements in the same way as SortFunc.

func Compare[T Ordered](x, y T) int
    Compare returns

        -1 if x is less than y,
         0 if x equals y,
        +1 if x is greater than y.

    For floating-point types, a NaN is considered less than any non-NaN,
    a NaN is considered equal to a NaN, and -0.0 is equal to 0.0.

func BinarySearch[S ~[]E, E cmp.Ordered](x S, target E) (int, bool)
    BinarySearch searches for target in a sorted slice and returns the earliest
    position where target is found, or the position where target would appear in
    the sort order; it also returns a bool saying whether the target is really
    found in the slice. The slice must be sorted in increasing order.

func Keys[Map ~map[K]V, K comparable, V any](m Map) iter.Seq[K]
    Keys returns an iterator over keys in m. The iteration order is not
    specified and is not guaranteed to be the same from one call to the next.
(exit 0)
```

**왜 그런가**

- ★★ `slices.Sort` 는 **값 자체로** 정렬한다 — 같은 값은 **구별할 방법이 없어** 「순서가 남았나」를 물을 수가 없다. **`==` 로 같은데 구별되는 값**(`0 == -0 : true`, 부호는 `math.Signbit` 로 보인다)으로 **창을 바꿔** 물었다.
- ★★★ **`n=12` 는 그대로, `n=40` 은 섞였다** — `slices.Sort` 도 안정하지 않다.
- ★★ **`Sort` 의 문서는 안정성에 대해 아무 말도 없다**(「NaNs are ordered before other values」까지만). 「not guaranteed to be stable」은 **`SortFunc` 에만** 있다. **말이 없는 것은 보장이 없는 것**이다.

### 4. 다섯 크기 전부 아무것도 안 받는다 · 정렬 안 됨 · 원소 보존

**출력**

```text
===== 소스: t38bad.go =====
package main

import (
	"fmt"
	"math/rand/v2"
	"slices"
)

func main() {
	for _, n := range []int{10, 100, 2000, 10000, 100000} {
		r := rand.New(rand.NewPCG(5, 6)) // 같은 수열
		xs := make([]int, n)
		for i := range xs {
			xs[i] = n - i
		}
		// 물을 때마다 답이 달라지는 비교 함수 — 추이성도 반대칭성도 없다.
		shaky := func(a, b int) int { return r.IntN(3) - 1 }
		func() {
			defer func() {
				if e := recover(); e != nil {
					fmt.Printf("n=%-6d recover: %v\n", n, e)
				}
			}()
			slices.SortFunc(xs, shaky)
			kept := slices.Sorted(slices.Values(xs))
			same := len(kept) == n && kept[0] == 1 && kept[n-1] == n && len(slices.Compact(kept)) == n
			fmt.Printf("n=%-6d 반환함 · 정말 정렬됐나 %-5v · 원소가 그대로인가 %v\n", n, slices.IsSorted(xs), same)
		}()
	}
}
===== 명령: go build -trimpath -o prog . && ./prog =====
n=10     반환함 · 정말 정렬됐나 false · 원소가 그대로인가 true
n=100    반환함 · 정말 정렬됐나 false · 원소가 그대로인가 true
n=2000   반환함 · 정말 정렬됐나 false · 원소가 그대로인가 true
n=10000  반환함 · 정말 정렬됐나 false · 원소가 그대로인가 true
n=100000 반환함 · 정말 정렬됐나 false · 원소가 그대로인가 true
(exit 0)
```

**왜 그런가**

- ★★★ **`recover` 가 받은 것 없음 · `반환함`** — `n=100000` 까지 패닉도 오류도 없다.
- ★★★ **`정말 정렬됐나 false`** — 결과는 틀렸다. **`원소가 그대로인가 true`** — 개수·원소 검사로는 안 잡힌다.
- ★★ 문서는 「**requires that cmp is a strict weak ordering**」까지만 쓰고 **어기면 무엇이 되는지**는 적지 않았다 — 이 다섯 줄은 **이 판의 관찰**이다.

### 5. NaN 은 `<` 로는 모두 거짓, `cmp.Compare` 로는 가장 작다 · `<`·`>` 비교 함수는 입력을 그대로 둔다

**출력**

```text
===== 소스: t38nan.go =====
package main

import (
	"cmp"
	"fmt"
	"math"
	"slices"
)

func main() {
	nan := math.NaN()
	fmt.Println("NaN < -Inf              :", nan < math.Inf(-1))
	fmt.Println("cmp.Compare(NaN, -Inf)  :", cmp.Compare(nan, math.Inf(-1)))
	fmt.Println("cmp.Compare(NaN, NaN)   :", cmp.Compare(nan, nan))

	a := []float64{3, nan, 1, nan, 2}
	slices.Sort(a)
	fmt.Println("slices.Sort             :", a)

	// < 와 > 로만 만든 비교 함수
	naive := func(x, y float64) int {
		if x < y {
			return -1
		}
		if x > y {
			return 1
		}
		return 0
	}
	b := []float64{3, nan, 1, nan, 2, 5, nan, 4}
	slices.SortFunc(b, naive)
	fmt.Println("SortFunc(< 와 >)        :", b)
	fmt.Println("  cmp.Compare 기준 정렬됐나:", slices.IsSortedFunc(b, cmp.Compare[float64]))

	fmt.Println("slices.Contains(a, NaN) :", slices.Contains(a, nan))
	fmt.Println("slices.Index(a, NaN)    :", slices.Index(a, nan))
}
===== 명령: go build -trimpath -o prog . && ./prog =====
NaN < -Inf              : false
cmp.Compare(NaN, -Inf)  : -1
cmp.Compare(NaN, NaN)   : 0
slices.Sort             : [NaN NaN 1 2 3]
SortFunc(< 와 >)        : [3 NaN 1 NaN 2 5 NaN 4]
  cmp.Compare 기준 정렬됐나: false
slices.Contains(a, NaN) : false
slices.Index(a, NaN)    : -1
(exit 0)
```

**왜 그런가**

- ★★★ **`NaN < -Inf : false` · `cmp.Compare(NaN, -Inf) : -1` · `cmp.Compare(NaN, NaN) : 0`** — 문서 「**a NaN is considered less than any non-NaN, a NaN is considered equal to a NaN**」.
- ★★ **`slices.Sort` → `[NaN NaN 1 2 3]`** — 「NaNs are ordered before other values」.
- ★★★ **`SortFunc(< 와 >)` → `[3 NaN 1 NaN 2 5 NaN 4]` — 입력과 한 글자도 같다.** NaN 이 모든 것과 「같다(0)」가 되어 **엄격한 약한 순서가 깨졌다.** 결과는 `cmp.Compare` 기준 `false` 이고 **아무도 말하지 않는다.**
- ★★ **`Contains`·`Index` 는 `==` 로 찾으므로 NaN 을 못 찾는다**(`false`·`-1`) — 정렬(`cmp.Compare`)과 찾기(`==`)의 NaN 규칙이 다르다.

### 6. `(0,false)`·`(2,false)`·`(2,false)`·`(2,true)`·`(5,false)` · `4 / 5`

**출력**

```text
===== 소스: t38bs.go =====
package main

import (
	"fmt"
	"slices"
)

func main() {
	s := []int{5, 1, 4, 2, 3} // 정렬 안 된 입력
	wrong := 0
	for _, t := range []int{1, 2, 3, 4, 5} {
		i, found := slices.BinarySearch(s, t)
		at := slices.Index(s, t)
		if !found || i != at {
			wrong++
		}
		fmt.Printf("BinarySearch(%d) = (%d, %-5v) · 실제 자리 %d\n", t, i, found, at)
	}
	fmt.Printf("실제 자리와 다른 답 %d / 5\n", wrong)
	sorted := slices.Sorted(slices.Values(s))
	i, found := slices.BinarySearch(sorted, 1)
	fmt.Println("정렬 뒤 BinarySearch(1) =", i, found)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
BinarySearch(1) = (0, false) · 실제 자리 1
BinarySearch(2) = (2, false) · 실제 자리 3
BinarySearch(3) = (2, false) · 실제 자리 4
BinarySearch(4) = (2, true ) · 실제 자리 2
BinarySearch(5) = (5, false) · 실제 자리 0
실제 자리와 다른 답 4 / 5
정렬 뒤 BinarySearch(1) = 0 true
(exit 0)
```

**왜 그런가**

- ★★★ **다섯 중 넷이 틀렸다** — `1`·`2`·`3`·`5` 는 슬라이스에 **있는데** `false`. 패닉도 오류도 없다.
- ★ `4` 가 맞은 것은 **가운데를 처음 짚은 자리**에 있었기 때문 — 운이다.
- ★★ 문서 「**The slice must be sorted in increasing order**」 — 정렬 뒤에는 `0 true`.

### 7. `iter.Seq[string]` · `keys` 3 가지(회전) · `sorted` 1 가지

**출력**

```text
===== 소스: t38keys.go =====
package main

import (
	"fmt"
	"maps"
	"os"
	"slices"
)

func main() {
	m := map[string]int{"a": 1, "b": 2, "c": 3}
	switch os.Args[1] {
	case "type":
		fmt.Printf("maps.Keys(m) 의 타입 : %T\n", maps.Keys(m))
		fmt.Printf("slices.Sorted(...)  : %v\n", slices.Sorted(maps.Keys(m)))
	case "keys":
		for k := range maps.Keys(m) {
			fmt.Print(k)
		}
		fmt.Println()
	case "sorted":
		for _, k := range slices.Sorted(maps.Keys(m)) {
			fmt.Print(k)
		}
		fmt.Println()
	}
}
===== 명령: go build -trimpath -o prog . && ./prog type && for m in keys sorted; do for i in $(seq 600); do ./prog $m; done > got.txt; echo "[$m] 600판에서 나온 순서 $(sort -u got.txt | wc -l) 가지: $(sort -u got.txt | tr "\n" " ")"; done =====
maps.Keys(m) 의 타입 : iter.Seq[string]
slices.Sorted(...)  : [a b c]
[keys] 600판에서 나온 순서 3 가지: abc bca cab 
[sorted] 600판에서 나온 순서 1 가지: abc 
(exit 0)
```

**왜 그런가**

- ★★★ **`iter.Seq[string]`** — 슬라이스가 아니라 **반복자**다([39번 주제](../39-iter-and-custom-iterators/)).
- ★★★ **`abc bca cab` 세 가지** — [09번 주제](../09-maps-declaration-comma-ok-delete-and-iteration-order/) (3)절이 `for k := range m` 으로 센 것과 **같은 세 회전**이다. `maps.Keys` 는 맵 순회를 감쌌을 뿐이다. 문서 「**The iteration order is not specified**」.
- ★★ **`slices.Sorted(maps.Keys(m))`** 는 1 가지 — 순서가 필요하면 이 한 줄.

### 8. `Clone`·`Copy`·`DeleteFunc`·`Equal`·`EqualFunc` · `Keys` 는 `go1.23.txt` — 틀렸다

**출력**

```text
===== 명령: cd "$(go env GOROOT)/api" && grep -n "pkg slices, func \(Sort\|SortFunc\|SortStableFunc\|BinarySearch\|Sorted\|Collect\|Values\)\[\|pkg cmp, func\|pkg maps, func" go1.21.txt go1.23.txt =====
go1.21.txt:4:pkg cmp, func Compare[$0 Ordered]($0, $0) int #59488
go1.21.txt:5:pkg cmp, func Less[$0 Ordered]($0, $0) bool #59488
go1.21.txt:349:pkg maps, func Clone[$0 interface{ ~map[$1]$2 }, $1 comparable, $2 interface{}]($0) $0 #57436
go1.21.txt:350:pkg maps, func Copy[$0 interface{ ~map[$2]$3 }, $1 interface{ ~map[$2]$3 }, $2 comparable, $3 interface{}]($0, $1) #57436
go1.21.txt:351:pkg maps, func DeleteFunc[$0 interface{ ~map[$1]$2 }, $1 comparable, $2 interface{}]($0, func($1, $2) bool) #57436
go1.21.txt:352:pkg maps, func Equal[$0 interface{ ~map[$2]$3 }, $1 interface{ ~map[$2]$3 }, $2 comparable, $3 comparable]($0, $1) bool #57436
go1.21.txt:353:pkg maps, func EqualFunc[$0 interface{ ~map[$2]$3 }, $1 interface{ ~map[$2]$4 }, $2 comparable, $3 interface{}, $4 interface{}]($0, $1, func($3, $4) bool) bool #57436
go1.21.txt:374:pkg slices, func BinarySearch[$0 interface{ ~[]$1 }, $1 cmp.Ordered]($0, $1) (int, bool) #60091
go1.21.txt:400:pkg slices, func Sort[$0 interface{ ~[]$1 }, $1 cmp.Ordered]($0) #60091
go1.21.txt:401:pkg slices, func SortFunc[$0 interface{ ~[]$1 }, $1 interface{}]($0, func($1, $1) int) #60091
go1.21.txt:402:pkg slices, func SortStableFunc[$0 interface{ ~[]$1 }, $1 interface{}]($0, func($1, $1) int) #60091
go1.23.txt:51:pkg maps, func All[$0 interface{ ~map[$1]$2 }, $1 comparable, $2 interface{}]($0) iter.Seq2[$1, $2] #61900
go1.23.txt:52:pkg maps, func Collect[$0 comparable, $1 interface{}](iter.Seq2[$0, $1]) map[$0]$1 #61900
go1.23.txt:53:pkg maps, func Insert[$0 interface{ ~map[$1]$2 }, $1 comparable, $2 interface{}]($0, iter.Seq2[$1, $2]) #61900
go1.23.txt:54:pkg maps, func Keys[$0 interface{ ~map[$1]$2 }, $1 comparable, $2 interface{}]($0) iter.Seq[$1] #61900
go1.23.txt:55:pkg maps, func Values[$0 interface{ ~map[$1]$2 }, $1 comparable, $2 interface{}]($0) iter.Seq[$2] #61900
go1.23.txt:93:pkg slices, func Collect[$0 interface{}](iter.Seq[$0]) []$0 #61899
go1.23.txt:97:pkg slices, func Sorted[$0 cmp.Ordered](iter.Seq[$0]) []$0 #61899
go1.23.txt:98:pkg slices, func Values[$0 interface{ ~[]$1 }, $1 interface{}]($0) iter.Seq[$1] #61899
(exit 0)
```

- ★★★ **1.21 의 `maps` 에는 `Keys` 가 없다.** `go1.23.txt:54` 에서 처음 나오고 **돌려주는 것이 `iter.Seq[$1]`** 이다.
- ★ 「1.21 에서는 슬라이스를 돌려줬다」는 **표준 밖 실험 패키지의 기억**이다 — 이 문서는 그 패키지를 **안 열었다.** 표준 라이브러리에 관해서는 **틀린 말**이다.

### 9. Java 는 `n=2000` 부터 던지고, Python·Go 는 끝까지 조용하다 — 갈린 것은 「검사하는 코드가 있느냐」

- ★★★ [Python 31번](../../../python/syntax/31-comparison-protocol-and-sortability/)의 대비 표 — **Java 는 `n=2000` 부터 `IllegalArgumentException`**(병합 단계의 검사 · [Java 28번](../../../java/syntax/28-comparable-comparator/) 실측), **Python 은 `n=100000` 까지 아무 일 없음.** **Go(4번)는 Python 쪽**이다.
- ★★ 같은 입력이 아니라 **자(비교 함수)의 모양도 다르다** — 그래서 「같은 입력에서 갈렸다」가 아니라 「**검사하는 코드의 유무**」가 갈린 것이다.
- ★ Rust 는 `f64` 의 `sort()` 가 **컴파일이 안 된다** — 타입으로 막는다(같은 표).

### 10. key 를 더했다(`cmp.Or`, 1.22) — 동률 자체가 없어지니 안정성에 기댈 일이 없다

- ★★★ [17번 주제](../17-struct-literals-comparability-field-tags-and-sorting/) (8)절 — `cmp.Or(cmp.Compare(x.Age, y.Age), cmp.Compare(x.Name, y.Name))`. 「안정 정렬을 쓴다」는 **입력 순서에 기대는 것**, 「key 를 더한다」는 **아무것에도 안 기대는 것**이다.
- ★★ 1번의 함정(12 까지만 유지)은 **동률이 있을 때만** 생긴다 — key 를 더해 **동률을 없애면** `SortFunc` 로도 답이 하나다.

### 11. 검사하면 O(log n) 이 아니게 된다 · `4 / 5` 의 조용한 거짓 `false`

- ★★ 정렬됐는지 확인하려면 **원소를 전부 봐야** 한다(O(n)) — 이진 탐색을 쓰는 이유가 사라진다. 그래서 **계약(「must be sorted」)으로 떠넘긴다.**
- ★★★ 그 대가 — 6번에서 **있는 원소 넷이 `false`** 로 나왔다. 패닉이 아니라 **그럴듯한 거짓**이다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 로 **★고칠 것 0** |
| ★★★ 안정성 격자 (`t38stable`) | 시드 고정 입력 · 여섯 크기 × 두 함수 · 20판 md5 | 캡처마다 | **`4 / 12`** · 1 가지 |
| ★★ `±0` (`t38zero`) | `math.Signbit` 로 부호 순서 | 캡처마다 | `n=40` 에서 섞임 |
| ★★★ 계약 위반 (`t38bad`) | 시드 고정 난수 비교 함수 · 다섯 크기 | 캡처마다 | 전부 반환 · 정렬 안 됨 |
| ★★ NaN · 이진 탐색 (`t38nan`·`t38bs`) | 실행 | 캡처마다 | 입력 그대로 · `4 / 5` |
| ★★ `maps.Keys` (`t38keys`) | 600판 × 두 방식 · `sort -u` | 캡처마다 | 3 가지 · 1 가지 |

**구현·환경에 달린 항목**

| 항목 | 무엇에 달렸나 |
|---|---|
| `n ≤ 12` 삽입 정렬 · `xorshift(length)` | **`slices` 소스의 현재 구현** |
| 계약 위반에 패닉 없음 | **이 판의 관찰** — 문서는 결과를 적지 않았다 |
| `maps.Keys` 순서 3 가지 | **gc 런타임의 맵 순회 무작위화** |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다.

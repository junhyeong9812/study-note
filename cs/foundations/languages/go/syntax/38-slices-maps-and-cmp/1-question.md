# go/syntax/38 — `slices`·`maps`·`cmp`(1.21) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ **모든 문제에서 「이것은 문서의 계약인가, 지금 구현의 우연인가」를 먼저 적어라.**
> ★★ **「틀렸을 때 누가 알려 주나 — 패닉인가, 거짓 값인가, 아무도 아닌가」를 매번 물어라.**
> 소스는 전부 `go build -trimpath -o prog .` 로 빌드했다. 모듈 이름은 `ex`, `go.mod` 는 `go 1.27` 이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 원소 수를 바꿔 가며 두 정렬 함수로 (예측)

```go
// t38stable.go
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
```

<!-- 빌드해 한 번 돌리고, 같은 바이너리를 20번 더 돌려 출력의 md5 가 몇 가지인지 센다. -->

- 여섯 줄의 `정렬됐나`·`원래 순서 남았나` 는? 마지막 줄의 수는?
- `SortFunc` 가 원래 순서를 지키는 크기와 못 지키는 크기의 경계는 어디인가?
- 20판 출력은 몇 가지인가? 그것은 보장인가?

### 2. 경계가 거기인 이유 (왜)

- 1번의 경계가 그 자리인 이유를 `slices` 소스의 한 줄로 설명하라. 그 수는 문서에 적혀 있나?

### 3. key 가 없는 `slices.Sort` 의 안정성 (경계)

```go
// t38zero.go
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
```

- `slices.Sort` 의 안정성을 「같은 key 여러 원소」로 물을 수 없는 이유는? 이 소스는 무엇으로 물었나?
- 두 크기에서 정렬 뒤 영의 부호 순서는 정렬 전과 같은가? `slices.Sort` 의 문서는 안정성에 대해 무엇이라고 적나?

### 4. 물을 때마다 답이 바뀌는 비교 함수 (예측)

```go
// t38bad.go
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
```

- 다섯 크기 각각에서 `recover` 가 무엇을 받나? `정말 정렬됐나`·`원소가 그대로인가` 는?

### 5. NaN 이 섞이면 (예측)

```go
// t38nan.go
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
```

- 여덟 줄의 출력은? `<` 와 `>` 로만 만든 비교 함수의 결과는 입력과 어떻게 다른가?

### 6. 정렬 안 된 슬라이스를 이진 탐색하면 (예측)

```go
// t38bs.go
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
```

- 다섯 줄의 `(자리, 찾았나)` 는? 마지막에서 두 번째 줄의 수는?

### 7. `maps.Keys` 가 돌려주는 것 (예측)

```go
// t38keys.go
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
```

<!-- ./prog type 을 한 번, keys 와 sorted 를 각각 600번 돌려 sort -u 로 가짓수를 센다. -->

- `%T` 는? `keys` 와 `sorted` 는 각각 몇 가지 순서가 나오나?

### 8. `maps.Keys` 의 판 (경계)

- `go1.21.txt` 의 `maps` 패키지에는 무엇이 있고 `Keys` 는 어느 판 파일에 처음 나오나? 「1.21 에서는 슬라이스를 돌려줬다」는 맞나?

### 9. 세 언어의 호루라기 (연결)

- 4번의 결과를 Java([Java 28번](../../../java/syntax/28-comparable-comparator/))·Python([Python 31번](../../../python/syntax/31-comparison-protocol-and-sortability/))과 나란히 놓아라. 갈린 것은 무엇인가?

### 10. 안정성에 기대지 않는 길 (연결)

- [17번 주제](../17-struct-literals-comparability-field-tags-and-sorting/) (8)절은 동률을 어떻게 없앴나? 그 방법이 1번의 함정을 어떻게 피하나?

### 11. 이진 탐색이 검사하지 않는 이유 (왜)

- `BinarySearch` 가 입력이 정렬됐는지 확인하지 않는 이유는? 그 대가로 6번에서 무엇이 나왔나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

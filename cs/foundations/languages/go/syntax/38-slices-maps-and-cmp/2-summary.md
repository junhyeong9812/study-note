# go/syntax/38 — `slices`·`maps`·`cmp`(1.21) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [`slices`](https://pkg.go.dev/slices) · [`maps`](https://pkg.go.dev/maps) · [`cmp`](https://pkg.go.dev/cmp) 문서.
> 문서·`api/go1NN.txt`·`slices` 소스는 **이 툴체인의 `$(go env GOROOT)` 에서 직접 떴다.** pdqsort 논문은 **안 열었다.**\
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> ★★ **버전** — `slices`·`maps`·`cmp` 패키지가 **1.21** · ★★★ **`maps.Keys`·`maps.Values`·`slices.Sorted`·`slices.Collect` 는 1.23** — 그리고 **`maps.Keys` 는 1.21 표준 라이브러리에 아예 없었다**(처음 들어올 때부터 반복자를 돌려준다 — 머리말 `api` 블록).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체는 넷째 창이다** — 「**정렬 안정성 격자** — 같은 입력을 원소 수 여섯 가지 × `SortFunc`/`SortStableFunc` 로 정렬하고, 같은 key 끼리 **원래 순서가 남았나**를 참거짓으로 찍는 로그」.
마지막 줄 「**같은 key 의 원래 순서가 깨진 칸 4 / 12**」 — 깨진 넷은 **전부 `SortFunc` 의 `n ≥ 13`** 이다((1)절).
★★ 짝이 되는 창은 「**계약을 어긴 비교 함수 × 원소 수**」 — Java 는 `IllegalArgumentException` 을 던졌는데 Go 는 **다섯 크기 전부 조용히 반환했다**((3)절).

★★★ **이 주제의 경계** — **정렬 알고리즘 자체**(버블·선택·삽입·셸의 동작과 비교·교환 횟수)와 **안정 정렬의 정의**는
[`../../../../../algorithm/01-elementary-sort/`](../../../../../algorithm/01-elementary-sort/)가 정본이다(그 문서의 「사전 지식 3줄」이 안정 정렬을 정의하고, 「비교」 표가 넷의 안정 여부를 적는다).
**그쪽은 알고리즘이 무엇을 하나까지**, 여기는 **`slices`·`maps`·`cmp` 가 무엇을 약속하고 무엇을 안 하나부터.**
제네릭 문법 자체는 [37번 주제](../37-generics-type-parameters-and-constraint-interfaces/), 반복자(`iter.Seq`)는 [39번 주제](../39-iter-and-custom-iterators/)가 정본이다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | ★ **명세에는 `slices` 가 없다** — 표준 라이브러리다. 명세에서 오는 것은 「**맵 순회 순서는 정하지 않는다**」([09번 주제](../09-maps-declaration-comma-ok-delete-and-iteration-order/) (3)절)와 「**NaN 은 어떤 비교에서도 거짓**」뿐이다 |
| **표준 라이브러리 계약** | 패키지 문서가 약속한 것 | ★★★ 「`SortFunc` … **This sort is not guaranteed to be stable**」 · 「**`SortFunc` requires that cmp is a strict weak ordering**」 · 「`SortStableFunc` … **keeping the original order of equal elements**」 · `cmp.Compare` 의 **NaN 은 가장 작다** · `BinarySearch` 는 「**The slice must be sorted**」 · `maps.Keys` 의 순서는 **정하지 않는다** |
| **구현(표준 라이브러리 소스)** | 지금 코드가 하는 것 | ★★ **`n ≤ 12` 는 삽입 정렬** · 원소를 흩뜨리는 `breakPatternsCmpFunc` 의 난수가 **길이로 시드된 `xorshift`** — **같은 입력이면 같은 결과**의 까닭으로 읽힌다((1)절) |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 격자의 참거짓 · `4 / 12` · 비교 함수 위반의 침묵 |

★★★ **선을 긋는다** — 「`SortFunc` 는 안정을 **보장하지 않는다**」는 **문서의 계약**이다.
「**12 개까지는 원래 순서가 남더라**」는 **구현의 우연**이다 — 그 위에 코드를 세우면 **원소가 13 개째 되는 날** 깨진다((1)절).
「비교 함수가 계약을 어겨도 **패닉이 안 난다**」는 **문서가 약속한 것도 아니고 금지한 것도 아니다** — 이 판의 관찰이다((3)절).

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
```

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

- ★★★ **`go1.21.txt` 의 `maps` 는 `Clone`·`Copy`·`DeleteFunc`·`Equal`·`EqualFunc` 다섯뿐**이다. `Keys`·`Values`·`All` 은 **`go1.23.txt`** 에서 처음 나오고 **돌려주는 것이 `iter.Seq`** 다.
  ★ 「`maps.Keys` 가 슬라이스를 돌려주던 시절」은 **표준 라이브러리에는 없었다**(그것은 표준 밖 실험 패키지의 것이다 — 이 문서는 그 패키지를 **안 열었다**).

문서 원문 — 이 문서가 기대는 조항:

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

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ **안정성 격자의 참거짓 · `4 / 12` · `20판 출력이 몇 가지인가: 1`** | 입력을 시드로 고정했고, 구현의 난수도 **길이로 시드**된다(`t38src`) — ★ **보장이 아니라 관찰**이다 |
| 안 흔들린다 | ★★ 비교 함수 위반 · NaN · `BinarySearch` 의 모든 줄 | 시드 고정 |
| **흔들린다(그래서 가짓수만 실었다)** | ★★★ **`maps.Keys` 로 돈 순서** | 600판을 `sort -u` 로 접었다 — **「3 가지」라는 가짓수**만 싣는다(규칙 11) |

★ 정규화 규칙은 **기본 넷**만 썼다.

## 한눈에 — 쉽게 말하면

**정렬은 「줄 세우기」다.** 키가 같은 두 사람이 있을 때 `SortStableFunc` 는 「**먼저 와 있던 사람이 앞**」을 지켜 준다.
`SortFunc` 는 **그 약속을 안 한다** — 줄이 짧으면(12 명 이하) 우연히 지켜지고, 길어지면 **섞인다.**
그리고 **줄 세우는 규칙(비교 함수)이 엉터리여도 아무도 호루라기를 안 분다** — 줄은 어쨌든 끝나 있고, **틀린 줄**이다.

| 비유 | 실체 |
|---|---|
| 먼저 온 사람이 앞 — 약속함 | ★★★ **`SortStableFunc`** — `6 / 6` 칸 전부 원래 순서 유지((1)절) |
| 약속 안 함 — 짧을 땐 우연히 지켜짐 | ★★★ **`SortFunc`** — `n ≤ 12` 는 유지, **`n ≥ 13` 은 깨짐**((1)절) |
| 엉터리 규칙에도 호루라기 없음 | ★★★ **추이성을 깬 `cmp` — 다섯 크기 전부 반환, 정렬 안 됨**((3)절) |
| 「키 없음」 표를 맨 앞에 | ★★ **`cmp.Compare` 는 NaN 을 가장 작게** 본다((4)절) |
| 줄이 안 서 있는데 가운데부터 찾기 | ★★ **`BinarySearch` 가 정렬 안 된 입력에 조용히 틀린 답**((5)절) |
| 명단을 **뽑아 주는 기계**(명단 자체가 아님) | ★★ **`maps.Keys` 는 반복자** — 뽑을 때마다 순서가 다르다((6)절) |

```text
   ★★★ 안정성 격자 ((1)절의 실측) — key 는 0·1·2 셋, id 는 처음 자리

   n         8     12     13     20     100    1000
   SortFunc  ✓     ✓      ✗      ✗      ✗      ✗       ← 12 이하는 삽입 정렬(구현) — 우연히 유지
   Stable    ✓     ✓      ✓      ✓      ✓      ✓       ← 문서가 약속한 것

   ✓ = 같은 key 끼리 id 가 오름차순으로 남았다  ✗ = 섞였다
   ★ 여섯 칸 전부 「정렬됐나」는 true — 틀린 것은 순서가 아니라 「같은 key 사이의 순서」다
```

> **안정 정렬(stable sort)** — 비교가 같은 두 원소의 **원래 순서**가 정렬 뒤에도 남는 정렬. 정의는 [algorithm/01](../../../../../algorithm/01-elementary-sort/)이 정본이다.

> **엄격한 약한 순서(strict weak ordering)** — 비교 함수가 지켜야 하는 조건 묶음. 핵심은 **추이성**(a<b, b<c 면 a<c)과 「**비교할 수 없음**」도 추이적이라는 것.\
> 예: `NaN` 을 `<` 로 비교하면 모든 것과 「비교할 수 없음」이 되어 이 조건이 깨진다((4)절).

> **반복자(iterator)** — 값을 **하나씩 내놓는 함수**. `maps.Keys` 가 돌려주는 `iter.Seq[K]` 가 그것이다([39번 주제](../39-iter-and-custom-iterators/)).

- ★★★ [17번 주제](../17-struct-literals-comparability-field-tags-and-sorting/) (8)절 — **20 명짜리 한 입력**에서 `SortFunc` 가 같은 나이의 입력 순서를 섞고 `SortStableFunc` 가 지키는 것, 그리고 **key 를 더해(`cmp.Or`, 1.22) 동률을 없애는 길**을 이미 보였다. **다시 재지 않는다** — 여기서는 그 한 칸을 **원소 수 격자**로 넓혀 **「어디서부터 섞이나」** 를 찾는다((1)절).
- ★★ [09번 주제](../09-maps-declaration-comma-ok-delete-and-iteration-order/) (3)·(8)절 — 맵 순회 순서의 **「3 가지 전부 회전」** 과 정렬해서 찍는 법. (6)절이 그것을 `maps.Keys` 로 다시 본다.

## 이 주제가 답하려는 질문

1. **`slices` 의 정렬 함수 셋은 무엇을 약속하나** — 안정성과, 그 약속이 없을 때 실제로 무엇이 보이나.
2. **비교 함수가 계약을 어기면 누가 알려 주나** — Go 는, Java 는, Python 은.
3. **`cmp`·`BinarySearch`·`maps.Keys` 가 조용히 틀리는 자리는 어디인가.**

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **안정성 격자 — n × 정렬 함수 × 「원래 순서 남았나」** | 문서의 「보장 안 함」이 **언제 실제로 보이나** | ★ 본체 창 |
| ★★ **20판 출력의 md5 가짓수** | 같은 입력이면 같은 결과인가(결정성) | 규칙 11 |
| ★★★ **±0 의 부호 순서** | ★★ **제5의 상태 — 「같은 질문을 다른 창으로」.** `slices.Sort` 는 key 가 없다 — **같은 값은 구별이 안 되니** 안정성을 물을 수가 없다. 그래서 **`==` 로 같은데 구별되는 값(`0` 과 `-0`)** 으로 물었다((2)절) | 이 문서 |
| ★★★ **계약 위반 비교 함수 × n** | 누가 알려 주나 — 패닉·반환·결과 | [Python 31번](../../../python/syntax/31-comparison-protocol-and-sortability/) 방식 |
| ★★ **`slices` 소스 두 줄** | 12 이하가 삽입 정렬인 **구현** | `t38src` |
| ★★ **`maps.Keys` 600판 `sort -u`** | 순서의 **가짓수** | [09번 주제](../09-maps-declaration-comma-ok-delete-and-iteration-order/) (3)절 방식 |
| **부적용 — 시간** | 정렬이 **몇 ms 걸리나**는 안 쟀다 — 이 주제는 **API 선택**이다 | 정본 경계 |
| **부적용 — 비교 횟수** | 비교·교환 **횟수**는 알고리즘의 질문이라 [algorithm/01](../../../../../algorithm/01-elementary-sort/)의 자리다 | 정본 경계 |

### (1) ★★★ 안정성 격자 — `SortFunc` 대 `SortStableFunc`

**언제 쓰나** — 「이미 이름순인 목록을 **부서별로** 다시 정렬했을 때 같은 부서 안의 이름순이 남나」를 물을 때.

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

그림 해설 (한 단계씩):

- ★ [17번 주제](../17-struct-literals-comparability-field-tags-and-sorting/) (8)절은 `n=20` 한 칸을 봤다 — 이 격자의 `n=20` 줄과 **같은 결론**(섞인다 / 지킨다)이다.
- ★★★ **`SortStableFunc` 는 여섯 크기 전부 `원래 순서 남았나=true`** — 문서 「**keeping the original order of equal elements**」 그대로다.
- ★★★ **`SortFunc` 는 `n=8`·`12` 에서 `true`, `n=13` 부터 `false`** — 마지막 줄 **`깨진 칸 4 / 12`** 가 전부 여기다.
  ★★ **여섯 칸 전부 `정렬됐나=true`** — `SortFunc` 는 **틀리지 않았다.** key 순으로는 완벽하고, **같은 key 사이의 순서**만 섞였다. 그래서 **테스트가 key 순만 보면 안 걸린다.**
- ★★★ **왜 12 에서 갈리나** — 구현이 말한다:

```text
===== 명령: sed -n "61,62p;72,73p" "$(go env GOROOT)/src/slices/zsortanyfunc.go"; grep -n "random := xorshift" "$(go env GOROOT)/src/slices/zsortanyfunc.go" =====
func pdqsortCmpFunc[E any](data []E, a, b, limit int, cmp func(a, b E) int) {
	const maxInsertion = 12
		if length <= maxInsertion {
			insertionSortCmpFunc(data, a, b, cmp)
243:		random := xorshift(length)
(exit 0)
```

  **`length <= maxInsertion`(12) 이면 삽입 정렬**이다. 삽입 정렬은 안정하다(정의·증명은 [algorithm/01](../../../../../algorithm/01-elementary-sort/)의 「비교」 표). **13 부터 pdqsort 의 분할**이 들어오며 섞인다.
  ★★★ **이것은 구현이다** — 문서는 12 를 말하지 않는다. **작은 입력으로 짠 테스트가 「안정하더라」를 확인해 주는 함정**이 정확히 여기다.
- ★★ **`20판 출력이 몇 가지인가: 1`** — 같은 입력이면 같은 결과다. 소스의 `random := xorshift(length)` — 분할이 쏠리지 않게 원소를 흩뜨리는 함수의 난수가 **길이로 시드**된다(그것이 까닭이라는 것은 **추론**이다). ★ 이것도 **관찰·구현**이다 — 문서는 결정성을 약속하지 않는다.

비용 — **안 쟀다.**

### (2) ★★ `slices.Sort` 의 안정성은 어떻게 묻나 — `0` 과 `-0`

`slices.Sort` 는 **key 가 없다** — `cmp.Ordered` 값 그 자체로 정렬한다. 같은 값은 **구별이 안 되니** 「순서가 남았나」를 물을 수 없다. 그런데 **`==` 로 같은데 구별되는 값**이 하나 있다:

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

- ★★★ **`0 == -0 : true`** — 정렬 입장에서 둘은 **같은 값**이다(`cmp.Compare` 문서 「**-0.0 is equal to 0.0**」).
- ★★★ **`n=12` 는 부호 순서가 그대로, `n=40` 은 섞였다.** `slices.Sort` 도 **안정 정렬이 아니다** — 그런데 **문서에 그 말이 없다**(머리말 `t38doc` 의 `Sort` 두 줄). `SortFunc` 에만 「not guaranteed to be stable」이 적혀 있다.
  ★ 이 차이가 실제로 보이는 자리는 **부호 있는 영과 NaN 의 비트** 정도뿐이라 문서가 굳이 말하지 않는 것으로 **읽힌다**(해석이다 — 문서가 이유를 적지는 않았다).

비용 — 없다.

### (3) ★★★ 비교 함수가 계약을 어기면 — 누가 알려 주나

문서 — 「**SortFunc requires that cmp is a strict weak ordering.**」 물을 때마다 답이 바뀌는 `cmp` 를 주면:

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

그림 해설 (한 단계씩):

- ★★★ **다섯 크기 전부 `반환함`** — `n=100000` 까지 **패닉도 오류도 없다.** `recover` 가 받은 것이 **하나도 없다.**
- ★★★ **`정말 정렬됐나 false`** — 결과는 **정렬돼 있지 않다.** 「예외가 없다」가 「답이 맞다」가 아니다.
- ★★ **`원소가 그대로인가 true`** — 잃지도 만들지도 않았다. **틀린 것은 순서뿐**이라 **개수 검사로는 절대 안 잡힌다.**

```text
   ★★★ 같은 결함 — 계약을 어긴 비교 함수로 정렬하면, 누가 알려 주나

   Java   (28번)   n=2000 부터 IllegalArgumentException 「Comparison method violates its general contract!」
                   n=1000 까지는 조용한 오답                    ← 병합 단계의 검사
   Python (31번)   n=100000 까지 아무 일 없음 · 정렬 안 됨        ← 검사 코드가 없다
   Go     (이 편)  n=100000 까지 아무 일 없음 · 정렬 안 됨 · 원소 보존
   Rust   (28번)   f64 는 sort() 가 컴파일 안 됨 — 타입으로 막는다

   ★ 갈린 것은 「같은 입력의 결과」가 아니라 「검사하는 코드가 있느냐」다 — 자(비교 함수)의 모양도 셋이 다르다
```

- ★★★ [Python 31번](../../../python/syntax/31-comparison-protocol-and-sortability/)이 세 언어 대비를 이미 세웠다 — Java 는 `n=2000` 부터 던지고([Java 28번](../../../java/syntax/28-comparable-comparator/)의 실측), Python 은 끝까지 조용했다. **Go 는 Python 쪽이다.**
- ★★ **층** — 「Go 는 검사하지 않는다」는 **문서가 약속한 것이 아니다.** 문서는 「requires」라고만 쓰고, **어기면 무엇이 되는지**를 적지 않았다. 이 다섯 줄은 **이 판의 관찰**이다.

비용 — 없다.

### (4) ★★ NaN — `cmp.Compare` 는 가장 작게, `<` 는 모두 거짓

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

- ★★★ **`NaN < -Inf : false` 인데 `cmp.Compare(NaN, -Inf) : -1`** — 문서 「**a NaN is considered less than any non-NaN, a NaN is considered equal to a NaN**」. `cmp.Compare` 는 NaN 에 **자리를 준다** — 맨 앞.
- ★★ **`slices.Sort` → `[NaN NaN 1 2 3]`** — 문서 「**NaNs are ordered before other values**」.
- ★★★ **`<` 와 `>` 로만 만든 비교 함수 → 입력이 한 글자도 안 바뀌었다**(`[3 NaN 1 NaN 2 5 NaN 4]`). NaN 은 모든 것과 「같다(0)」가 되고, 그러면 **「3 과 NaN 이 같고 NaN 과 1 이 같다」 → 「3 과 1 이 같다」** 가 되어야 하는데 아니다 — **엄격한 약한 순서가 깨졌다.** 결과가 `false` 인데 **아무 말도 없다**((3)절과 같은 침묵).
- ★★ **`slices.Contains(a, NaN) : false` · `Index : -1`** — `==` 로 찾는 함수는 NaN 을 **영영 못 찾는다**(NaN ≠ NaN). 정렬 쪽(`cmp.Compare`)과 **찾기 쪽(`==`)의 NaN 규칙이 다르다.**

비용 — 없다.

### (5) ★★ `BinarySearch` — 정렬 안 된 입력에 조용히 틀린 답

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

- ★★★ **`실제 자리와 다른 답 4 / 5`** — `1` 은 1 번 자리에 **있는데** `(0, false)`, `5` 는 0 번 자리에 **있는데** `(5, false)`.
  **패닉도 오류도 없다** — 문서의 「**The slice must be sorted in increasing order**」를 어기면 **거짓 `false`** 가 나온다.
- ★ 맞은 한 칸(`4`)은 **운**이다 — 가운데를 처음 짚었을 때 거기 있었다.
- ★★ **정렬 뒤에는 `0 true`.** 이진 탐색은 **정렬됐다는 가정을 검사하지 않는다** — 검사하면 O(log n) 이 아니게 되기 때문이다.

비용 — 없다.

### (6) ★★ `maps.Keys` 는 반복자다 — 순서는 매번 다르다

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

- ★★★ **`maps.Keys(m) 의 타입 : iter.Seq[string]`** — 슬라이스가 아니라 **반복자**다. `len` 도 인덱스도 없다. 모으려면 `slices.Collect`, **정렬해서 모으려면 `slices.Sorted`**.
- ★★★ **`[keys] 600판에서 나온 순서 3 가지: abc bca cab`** — [09번 주제](../09-maps-declaration-comma-ok-delete-and-iteration-order/) (3)절이 `for k := range m` 으로 센 것과 **같은 세 회전**이다. `maps.Keys` 는 **맵 순회를 감싼 것**일 뿐이라 순서 규칙도 그대로다(문서 「**The iteration order is not specified**」).
- ★★ **`[sorted] … 1 가지: abc`** — `slices.Sorted(maps.Keys(m))` 가 [09번 주제](../09-maps-declaration-comma-ok-delete-and-iteration-order/) (8)절의 「키를 모아 정렬해서 찍는 법」을 **한 줄**로 줄인 것이다.

비용 — 없다.

## 문법 — 형태와 규칙

### 형태

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

규칙 불릿.

- ★★★ **같은 key 사이 순서가 필요하면 `SortStableFunc`** — `SortFunc`·`Sort` 는 안정하지 않다(작은 입력에서 우연히 유지될 뿐).
- ★★★ **비교 함수는 `cmp.Compare` 로 만든다** — `a < b` 로 직접 만들면 NaN 에서 계약이 깨진다. 여러 key 는 `cmp.Or(cmp.Compare(a.x, b.x), cmp.Compare(a.y, b.y))` 꼴 — `cmp.Or` 는 **1.22**, 실측은 [17번 주제](../17-struct-literals-comparability-field-tags-and-sorting/) (8)절이 정본이다. ★ **key 를 더해 동률을 없애면 안정성에 기댈 일 자체가 사라진다.**
- ★★ **`BinarySearch` 앞에는 반드시 정렬** — 어기면 거짓 `false`.
- ★★ **`maps.Keys` 는 반복자** — 순서가 필요하면 `slices.Sorted(maps.Keys(m))`.
- ★ 이름 규칙 — `Sort`(자연 순서) · `SortFunc`(비교 함수) · `SortStableFunc`(안정) · `Sorted`(반복자를 받아 **새 슬라이스**).

### 금지 사례 — 컴파일은 되고 실행이 조용히 틀리는 것

| 쓴 꼴 | 누가 잡나 | 어디서 |
|---|---|---|
| 같은 key 순서에 기대면서 `SortFunc` | ★★★ **아무도 안 잡는다**(12 개까지는 맞는다) | (1)절 |
| 추이성을 깬 `cmp` | ★★★ **아무도 안 잡는다**(패닉 없음 · 원소 보존) | (3)절 |
| `<`·`>` 로 만든 `cmp` 에 NaN | ★★ **아무도 안 잡는다** | (4)절 |
| `slices.Contains(xs, NaN)` | ★ **항상 `false`** | (4)절 |
| 정렬 안 된 슬라이스에 `BinarySearch` | ★★★ **아무도 안 잡는다**(`4 / 5` 틀림) | (5)절 |
| `maps.Keys` 의 순서에 기댐 | ★★ **아무도 안 잡는다**(3 가지) | (6)절 |

## 어디서 틀리나

### 1. ★★★ 「`SortFunc` 로 돌려 봤더니 같은 key 순서가 남더라」

- (1)절 — **12 개까지만** 그렇다. 구현의 삽입 정렬 구간이다. 13 개부터 깨진다.

### 2. ★★★ 「비교 함수가 틀리면 Java 처럼 예외가 난다」

- (3)절 — **다섯 크기 전부 조용히 반환.** 결과는 정렬돼 있지 않다.

### 3. ★★ 「`slices.Sort` 는 문서에 불안정하다는 말이 없으니 안정하다」

- (2)절 — `n=40` 에서 `0` 과 `-0` 이 **섞였다.** 말이 없는 것은 **보장이 없는 것**이다.

### 4. ★★ 「NaN 이 섞여도 `<` 로 만든 비교 함수면 된다」

- (4)절 — 입력이 **그대로** 남았다. `cmp.Compare` 로.

### 5. ★★ 「`BinarySearch` 가 `false` 면 없다」

- (5)절 — 정렬 안 된 입력이면 **있어도 `false`**.

### 6. ★★ 「`maps.Keys` 는 1.21 부터 슬라이스를 돌려줬다」

- 머리말 `api` 블록 — **1.21 표준에는 `Keys` 가 없다.** 1.23 에 **반복자로** 들어왔다.

### 7. ★ 「같은 입력이면 같은 결과가 나오니 순서를 믿어도 된다」

- (1)절의 `1` 가지는 **구현의 결정성**이다 — 문서가 약속하지 않는다. 판이 오르면 **입력이 같아도** 같은 key 사이 순서가 바뀔 수 있다.

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| 맵 순회 순서는 정하지 않는다 | **명세** | [09번 주제](../09-maps-declaration-comma-ok-delete-and-iteration-order/) |
| ★★★ **`SortFunc` 는 안정 보장 없음 · `SortStableFunc` 는 보장** | **표준 라이브러리 계약** | (1)절 |
| ★★ **`cmp` 는 strict weak ordering 이어야 한다** | **표준 라이브러리 계약** — 어기면 무엇이 되는지는 **안 적었다** | (3)절 |
| `cmp.Compare` 의 NaN · `Sort` 의 NaN 앞 | **표준 라이브러리 계약** | (4)절 |
| `BinarySearch` 는 정렬된 입력을 요구 | **표준 라이브러리 계약** | (5)절 |
| `maps.Keys` 는 1.23 · 반복자 · 순서 무보장 | **표준 라이브러리 계약** | (6)절 |
| ★★★ **12 이하는 삽입 정렬 · 길이 시드 `xorshift`** | **구현(`slices` 소스)** | (1)절 `t38src` |
| ★★ **계약 위반에 패닉 없음** | **이 판의 관찰** | (3)절 |
| `maps.Keys` 순서 3 가지 | **gc 런타임의 관찰** | (6)절 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| `int`·`string`·`float64` 슬라이스 | **`slices.Sort`** | NaN 은 맨 앞으로 간다 |
| 구조체를 한 key 로 | **`slices.SortFunc` + `cmp.Compare`** | 같은 key 사이 순서가 **상관없을 때만** |
| 이미 한 기준으로 정렬된 것을 다른 기준으로 다시 | ★★★ **`slices.SortStableFunc`** | (1)절 |
| 정렬된 슬라이스에서 찾기 | **`slices.BinarySearch`** | 정렬 안 됐으면 **`slices.Index`** |
| 맵의 키를 정해진 순서로 | ★★ **`slices.Sorted(maps.Keys(m))`** | (6)절 |
| 알고리즘을 직접 짠다 | ★ **짜지 않는다** — 알고리즘 공부는 [algorithm/01](../../../../../algorithm/01-elementary-sort/) | 정본 경계 |

## 핵심 문장

- ★★★ **`SortFunc` 는 안정하지 않다 — `n ≤ 12` 는 삽입 정렬이라 우연히 유지, `n ≥ 13` 부터 깨진다**(`4 / 12`). 필요하면 `SortStableFunc`.
- ★★ **`slices.Sort` 도 안정하지 않다** — 문서에 말이 없을 뿐, `0` 과 `-0` 이 섞였다.
- ★★★ **추이성을 깬 `cmp` 에 Go 는 아무 말도 안 한다** — `n=100000` 까지 반환·정렬 안 됨·원소 보존. Java 는 던지고 Python 은 조용했다.
- ★★ **`cmp.Compare` 는 NaN 을 가장 작게 본다** — `<` 로 만든 비교 함수는 NaN 에서 입력을 **그대로** 둔다.
- ★★ **`BinarySearch` 는 정렬을 검사하지 않는다** — 정렬 안 된 입력에 `4 / 5` 틀린 답.
- ★★ **`maps.Keys` 는 1.23 의 반복자** — 1.21 표준에는 없었다. 순서는 3 가지로 돈다 · `slices.Sorted` 로 고정한다.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 38번)
- [`../../../../../algorithm/01-elementary-sort/`](../../../../../algorithm/01-elementary-sort/) — ★★ **정본 경계.** 안정 정렬의 정의 · 버블·선택·삽입·셸의 동작과 안정 여부 · 비교/쓰기 횟수는 **거기**, 여기는 **`slices` 의 API 계약부터.**
- [37번 주제](../37-generics-type-parameters-and-constraint-interfaces/)(제네릭) — ★ 목록상 선행 · `cmp.Ordered` 는 `~` 타입 목록 제약이다
- [39번 주제](../39-iter-and-custom-iterators/)(`iter`) — `maps.Keys`·`slices.Sorted` 가 주고받는 `iter.Seq`
- [09번 주제](../09-maps-declaration-comma-ok-delete-and-iteration-order/)(맵) — 순회 순서 3 가지 · 정렬해서 찍기
- [17번 주제](../17-struct-literals-comparability-field-tags-and-sorting/)(구조체 정렬) — `SortFunc` 의 기본형
- [Python 31번](../../../python/syntax/31-comparison-protocol-and-sortability/) · [Java 28번](../../../java/syntax/28-comparable-comparator/) — ★★ **계약 위반 비교자의 세 언어 대비**

## 용어 풀이

- **`slices.Sort`** — `cmp.Ordered` 슬라이스를 오름차순으로. NaN 이 맨 앞. 안정하지 않다.
- **`slices.SortFunc`** — 비교 함수로 정렬. 안정 보장 없음.
- **`slices.SortStableFunc`** — 같은 원소의 원래 순서를 지키는 정렬.
- **`cmp.Compare`** — `-1`·`0`·`+1`. NaN 은 가장 작고 NaN 끼리는 같다.
- **`cmp.Ordered`** — `<` 가 되는 타입들의 `~` 목록 제약.
- **엄격한 약한 순서** — 비교 함수가 지켜야 하는 조건. 추이성이 핵심.
- **`slices.BinarySearch`** — 정렬된 슬라이스에서 `(자리, 찾았나)`. 정렬을 검사하지 않는다.
- **`maps.Keys`** — 맵의 키를 내놓는 `iter.Seq[K]`(1.23). 순서 무보장.
- **`slices.Sorted`** — 반복자를 모아 정렬한 **새 슬라이스**(1.23).
- **pdqsort** — `slices` 가 쓰는 불안정 정렬(구현). 작은 구간은 삽입 정렬로 넘긴다.

---

## 더 들어가면

- ★ pdqsort 논문과 `slices` 소스의 나머지(피벗 선택·흩뜨리기의 나머지)는 **안 열었다** — (1)절에 필요한 세 자리만 떴다.
- ★ `slices.Delete`·`Compact` 가 **뒤쪽 원소를 제로값으로 지우는지**(판 경계가 있다는 기억이 있다)는 **이 문서가 던지지 않았다** — 확인 대상이다.
- ★ `slices.SortedFunc`·`maps.All` 은 이름만 적었다 — **던지지 않았다.**

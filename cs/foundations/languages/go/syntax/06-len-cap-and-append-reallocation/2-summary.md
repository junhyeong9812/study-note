# go/syntax/06 — `len`/`cap`과 `append`의 재할당 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Go 명세](https://go.dev/ref/spec) 의 Length and capacity ·
> Appending to and copying slices · Making slices, maps and channels · Slice expressions 절.\
> 웹이 아니라 **이 툴체인이 들고 있는 `$(go env GOROOT)/doc/go_spec.html` 을 열어** 인용했다.
> 그 파일의 머리는 「**Language version go1.27 (May 26, 2026)**」이다.
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> ★★ **이 주제의 `cap` 수치는 전부 「이 판의 관찰」이다.** 명세는 `append` 가 얼마나 늘리는지
> **한 글자도 정하지 않는다.** 수치를 규칙처럼 외우면 그것이 이 주제에서 가장 크게 틀리는 자리다.
> **버전** — `append`·`cap` 은 1.0부터, 3-인덱스 슬라이싱은 1.2부터,
> `unsafe.SliceData` 는 **1.20**, `slices.Grow` 는 **1.21**부터다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 명세로, 수치는 실행으로 접지했다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | `go_spec.html` 원문 인용 |
| **구현(gc)** | gc 컴파일러·런타임이 그렇게 하는 것 | `cap` 의 **구체적 수치** 전부가 여기 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 실행 출력(재실행 대조까지) |

★ **05번 주제와 층의 비율이 뒤집힌다.** 05는 명세 칸이 컸는데 이 주제는 **구현 칸이 크다** —
「`cap` 이 얼마인가」를 묻는 질문은 거의 전부 구현이다.
명세가 보장하는 것은 **「모자라면 새 배열을 잡는다」는 갈림 하나**뿐이다.

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
| **흔들린다** | 기반 배열의 **주소 자체** | 그래서 `A`·`B` 이름표와 「같나 다르나」로만 찍는다 |
| **흔들린다** | 패닉 스택의 `goroutine N` 번호와 `+0x…` | 런타임·빌드 산출물에 달렸다 |
| **판이 바뀌면 바뀐다** | **`cap` 의 구체적 수치**(4·8·848·1280 …) | **gc 의 성장 전략**이다. 명세가 정하지 않는다 |
| 안 흔들린다 | 같은 바이너리를 다시 돌렸을 때의 `cap` | **컴파일 타임·런타임이 결정적**이다. 실행마다 바뀌지는 않는다 |
| 안 흔들린다 | `len` 값 | 소스가 정한다 |
| 안 흔들린다 | 「재할당이 일어났나 안 일어났나」 | **`cap` 만 보면 예측된다**((4)절에서 여섯 경우를 맞춰 본다) |
| 안 흔들린다 | 컴파일 에러·패닉 문장 본문 · `파일:줄:칸` · 종료 코드 | 같은 소스·같은 판이면 같다 |
| 해당 없음 | 맵 순회 순서 | 이 주제는 맵을 안 쓴다 |

★ **「같은 판에서 결정적」과 「보장된다」는 다르다.** 이 문서의 `cap` 수치는 다시 돌려도 같지만,
**판이 오르면 바뀔 수 있다.** 관찰은 관찰로 적고 보장은 명세로만 적는다.

## 한눈에 — 쉽게 말하면

**`len` 은 「지금 몇 개를 보고 있나」고 `cap` 은 「이사하지 않고 몇 개까지 넣을 수 있나」다.**

`append` 는 그 두 숫자를 보고 **제자리에 쓸지 이사할지**를 정한다.
이사하면 새 짐칸으로 옮기므로 **옛 짐칸을 같이 보던 쪽과 연이 끊긴다.**

| 비유 | 실체 |
|---|---|
| 지금 쓰는 칸 수 | **`len`** — 인덱스의 상한 |
| 이사 없이 더 넣을 수 있는 한도 | **`cap`** — 슬라이싱의 상한 |
| 한도 안이면 그냥 넣는다 | `append` 가 **기반 배열을 재사용** |
| 한도를 넘으면 이사한다 | `append` 의 **재할당** — 새 배열을 잡고 옮긴다 |
| 이사 갈 집을 얼마나 크게 잡나 | **구현이 정한다** — 명세에 없다 |
| 처음부터 큰 집을 얻어 둔다 | `make([]T, 0, n)` — 이사를 없앤다 |

- 05번 주제가 「**이사하면 연이 끊긴다**」까지 말했다. 이 주제는 「**언제 이사하나**」와 「**집을 얼마나 크게 잡나**」다.
- ★ 앞엣것은 **명세**고 뒤엣것은 **구현**이다. 이 두 줄을 섞어 적는 것이 이 주제의 가장 큰 사고다.

```text
   len = 3 · cap = 6 인 슬라이스

   기반 배열  [ 1 | 2 | 3 | _ | _ | _ ]
               ^~~~~~~~~^   ^~~~~~~~~^
                 len 3        여유 3 (cap - len)

   append 3개까지 -> 제자리.  4개째 -> 이사(새 배열).
   판정은 한 줄이다:  len(s) + 붙일 개수 <= cap(s) ?
```

> **`cap`(capacity)** — 기반 배열에서 **이 슬라이스의 시작점부터 배열 끝까지**의 칸 수.\
> 예: `[6]int` 의 `arr[2:4]` 는 `len` 2, `cap` **4**다(2번부터 5번까지).

> **재할당(reallocation)** — `append` 가 새 배열을 잡고 원소를 옮기는 것.\
> 예: `cap` 3짜리에 넷째를 붙이면 새 배열로 간다 — **이때 공유가 끊긴다**(05번 주제 (4)절).

> **성장 전략(growth strategy)** — 재할당 때 새 `cap` 을 얼마로 잡을지 고르는 규칙.
> **명세에 없다 — 구현이 정한다.**\
> 예: 이 판에서는 작은 슬라이스가 배로 늘고 큰 슬라이스는 그보다 완만했다((5)절 실측).

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `len` 과 `cap` 은 **어떤 연산에서 어떻게 움직이나** — 특히 슬라이싱과 `append` 에서.
2. **재할당이 일어날지 미리 알 수 있나** — 무엇을 보면 되나.
3. 새 `cap` 이 얼마가 되는지는 **누가 정하나** — 그리고 그것을 어떻게 적어야 안 틀리나.

★ 「배로 늘리면 왜 상각 O(1)인가」는 이 주제가 아니다 —
[`../../../../../data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/) 가 정본이다.
여기는 **Go 의 `cap` 이 실제로 어떻게 움직이는지 관찰하는 법**만 본다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

| 창 | 무엇을 보여 주나 | 한계 |
|---|---|---|
| `len(s)` | 지금 보이는 개수 | 재할당 여부를 **못 가른다** |
| `cap(s)` | 여유가 얼마인가 | 값이 바뀌었다고 **반드시 재할당은 아니다**(3-인덱스로도 바뀐다) |
| ★ **기반 배열 동일성** | **재할당이 일어났나** | 주소 자체는 흔들린다 — 「같나 다르나」로만 읽는다 |
| `go build` 의 에러 | `append`·`make` 를 잘못 쓴 것 | **공유·재할당은 못 본다** |

★ 실무에서 쓰는 것은 **`cap` 하나**다. `cap(s) - len(s)` 가 붙일 개수보다 작으면 이사한다.
기반 배열 동일성 창은 **그 예측이 맞는지 확인하는 용도**다((4)절에서 여섯 경우를 맞춰 본다).

### (1) `len` 과 `cap` — 만드는 법마다 다른 두 숫자

**언제 쓰나** — 슬라이스를 만들거나 자를 때마다.

```text
===== 소스: t06a.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
arr [6]int               len=6  cap=6  [10 20 30 40 50 60]

[]int{1,2,3}             len=3  cap=3  [1 2 3]
make([]int, 3)           len=3  cap=3  [0 0 0]
make([]int, 3, 10)       len=3  cap=10 [0 0 0]
var s []int              len=0  cap=0  []

arr[:]                   len=6  cap=6  [10 20 30 40 50 60]
arr[2:]                  len=4  cap=4  [30 40 50 60]
arr[:2]                  len=2  cap=6  [10 20]
arr[2:4]                 len=2  cap=4  [30 40]
arr[2:4:5]               len=2  cap=3  [30 40]
arr[6:]                  len=0  cap=0  []

s := arr[2:4]            len=2  cap=4  [30 40]
s[:cap(s)]               len=4  cap=4  [30 40 50 60]
s[1:]                    len=1  cap=3  [40]
0 <= len <= cap 인가 : true
(exit 0)
```

그림 해설 (한 단계씩):

- 배열의 `cap` 은 **언제나 `len` 과 같다.** 명세가 `cap([n]T)` 를 「array length (== n)」로 못 박았다.
- `[]int{1,2,3}` 과 `make([]int, 3)` 은 `cap` 도 3이다. **리터럴은 딱 맞는 배열을 만든다.**
- `make([]int, 3, 10)` 만 `cap` 이 10이다. **여유는 명시해야 생긴다.**
- 슬라이싱 여섯 줄이 이 절의 본체다.
  - `arr[2:]` → `len` 4 `cap` **4**. 앞을 자르면 **`cap` 도 같이 줄어든다.**
  - `arr[:2]` → `len` 2 `cap` **6**. 뒤를 자르면 **`cap` 은 그대로다.**
  - `arr[2:4:5]` → `cap` **3**. 세 번째 숫자가 `cap` 의 끝을 정한다(`5-2`).
  - `arr[6:]` → `len` 0 `cap` 0. **끝에서 자르면 빈 것이 나온다**(패닉이 아니다).
- `s[1:]` 이 `len` 1 `cap` **3**인 것이 중요하다 — **다시 자를 때도 `cap` 은 배열 끝을 향해 남는다.**

명세:

> The capacity of a slice is the number of elements for which there is space allocated
> in the underlying array. At any time the following relationship holds: `0 <= len(s) <= cap(s)`

```text
   arr [6]int   [ 10 | 20 | 30 | 40 | 50 | 60 ]
                   0    1    2    3    4    5

   arr[:2]   len 2  cap 6   ^~~~~^ ................  뒤는 남아 있다
   arr[2:]   len 4  cap 4             ^~~~~~~~~~~~^  앞을 버리면 cap 도 준다
   arr[2:4]  len 2  cap 4             ^~~~~^ .......
   arr[2:4:5] len 2 cap 3             ^~~~~^ ..^     세 번째 숫자가 끝을 정한다
```

비용 — 슬라이싱은 헤더 하나를 만드는 일이다. `len`·`cap` 은 그 헤더에서 읽는다.

### (2) ★ `append` 의 계약 — 명세가 약속한 것과 안 한 것

**언제 쓰나** — `append` 를 쓰는 모든 자리.

명세의 문단은 짧다.

> If the capacity of `s` is not large enough to fit the additional values, `append`
> **allocates a new, sufficiently large underlying array** that fits both the existing
> slice elements and the additional values. **Otherwise, `append` re-uses the underlying array.**

여기서 읽을 것이 셋이다.

- **약속 ①** — 모자라면 **새 배열**을 잡는다. 그러니 **재할당이 일어나면 반드시 공유가 끊긴다.**
- **약속 ②** — 모자라지 않으면 **재사용**한다. 그러니 **여유가 있으면 반드시 이웃이 덮인다.**
  (07번 주제가 이 두 번째 약속만 다룬다.)
- ★★ **약속하지 않은 것** — 새 배열이 **얼마나** 큰지. 명세의 낱말은 "sufficiently large" 뿐이다.
  4가 돼도 100이 돼도 명세 위반이 아니다.

그리고 명세가 한 줄 더 적는다 — 결과를 **돌려준다**는 것.

> The variadic function `append` appends zero or more values `x` to a slice `s` of type `S`
> and **returns the resulting slice**, also of type `S`.

★ 「왜 `s.push(x)` 가 아니라 `s = append(s, x)` 인가」의 답이 여기다.
`append` 는 **헤더를 바꿀 수 없다**(05번 주제 (3)절) — 그래서 **새 헤더를 돌려주는 수밖에 없다.**

비용 — 재사용이면 원소 하나 쓰기. 재할당이면 **전부 복사**다.

### (3) ★★ `cap` 만 보고 재할당을 예측한다

**언제 쓰나** — 남의 슬라이스를 받아 `append` 할 때. 즉 라이브러리 코드 전부.

```text
===== 소스: t06g.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
make([]int,3,6) + 1개       len=3 cap=6  + 1개 → len=4 cap=6   예측(재할당 없음)=true  실제(같은 배열)=true
make([]int,3,6) + 3개       len=3 cap=6  + 3개 → len=6 cap=6   예측(재할당 없음)=true  실제(같은 배열)=true
make([]int,3,6) + 4개       len=3 cap=6  + 4개 → len=7 cap=12  예측(재할당 없음)=false 실제(같은 배열)=false
make([]int,3,3) + 1개       len=3 cap=3  + 1개 → len=4 cap=6   예측(재할당 없음)=false 실제(같은 배열)=false
[]int{1,2,3}    + 0개       len=3 cap=3  + 0개 → len=3 cap=3   예측(재할당 없음)=true  실제(같은 배열)=true
nil             + 1개       len=0 cap=0  + 1개 → len=1 cap=1   예측(재할당 없음)=false 실제(같은 배열)=false
(exit 0)
```

그림 해설 (한 단계씩):

- 예측식은 한 줄이다 — **`len(s) + 붙일 개수 <= cap(s)`**.
- 여섯 경우에서 **예측과 실제(기반 배열이 같나)가 전부 일치**했다.
  - `cap` 6 · `len` 3 에 **3개까지는 제자리**, **4개째부터 이사**.
  - `cap` 3 · `len` 3 에는 **하나만 붙여도 이사**.
  - **0개를 붙이면 언제나 제자리**다(`[]int{1,2,3}` 행). `append(s)` 는 아무것도 안 한다.
  - **`nil` 에 붙이면 언제나 이사**다. `cap` 이 0이니 당연하다.
- ★ 이 예측은 **명세 보장**이다 — 명세가 갈림을 `cap` 으로 정의했기 때문이다.
  반면 **이사 뒤의 `cap` 이 12·6·1 로 제각각인 것은 구현**이다. 두 층이 한 표에 같이 있다.
- 실무 규칙 — **남의 슬라이스에 `append` 하기 전에 `cap` 을 봐라.** 볼 수 없으면 `s[:n:n]` 으로
  이사를 강제한다(08번 주제).

비용 — `cap` 을 읽는 것은 헤더에서 정수 하나를 꺼내는 일이다.

### (4) ★★★ `cap` 이 얼마로 늘어나는가 — **이 판의 관찰**이다

**언제 쓰나** — 「배로 늘어난다」고 적고 싶어질 때. **그 문장이 틀린다.**

```text
===== 소스: t06b.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
※ 아래 cap 값은 gc go1.27.1 의 관찰이지 명세가 아니다.
시작           len=0    cap=0
len 1    에서  cap 0    -> 4     (4.000 배)
len 5    에서  cap 4    -> 8     (2.000 배)
len 9    에서  cap 8    -> 16    (2.000 배)
len 17   에서  cap 16   -> 32    (2.000 배)
len 33   에서  cap 32   -> 64    (2.000 배)
len 65   에서  cap 64   -> 128   (2.000 배)
len 129  에서  cap 128  -> 256   (2.000 배)
len 257  에서  cap 256  -> 512   (2.000 배)
len 513  에서  cap 512  -> 848   (1.656 배)
len 849  에서  cap 848  -> 1280  (1.509 배)
len 1281 에서  cap 1280 -> 1792  (1.400 배)
len 1793 에서  cap 1792 -> 2560  (1.429 배)
끝             len=2000 cap=2560
(exit 0)
```

그림 해설 (한 단계씩):

- `nil` 에서 시작해 2000번 붙이는 동안 `cap` 이 **열두 번** 바뀌었다.
- 앞쪽은 **정확히 배**다 — 4 → 8 → 16 → 32 → 64 → 128 → 256 → 512.
- ★★ **512 에서 배가 깨진다** — 512 → **848**(1.656배), 848 → **1280**(1.509배),
  1280 → **1792**(1.400배), 1792 → **2560**(1.429배).
- 즉 **「배로 늘어난다」는 앞쪽 절반에서만 맞다.** 뒤쪽은 배도 아니고 **일정한 비율도 아니다.**
- ★★★ 이 수치들을 **규칙으로 적으면 안 된다.** 명세에 없고, 판이 오르면 바뀐다.
  적을 수 있는 것은 두 줄뿐이다 — 「**작을 때는 빠르게, 커지면 완만하게 늘어난다**」와
  「**정확한 수치는 이 판(go1.27.1·amd64)의 관찰이다**」.
- 첫 줄이 `0 → 4` 인 것도 관찰이다. `1` 이 아니다.

```text
   cap 의 변화 (이 판의 관찰 — 명세가 아니다)

     0 -> 4 -> 8 -> 16 -> 32 -> 64 -> 128 -> 256 -> 512 -> 848 -> 1280 -> 1792 -> 2560
          \____________ 여기까지 정확히 배 ____________/  \___ 배가 아니다 ___/
                                                          1.656  1.509  1.400  1.429

   읽을 것 : "작을 때 빠르고 커지면 완만하다" 라는 성질
   적지 말 것 : 4·848·1280 같은 수치를 규칙으로
```

비용 — 재할당 열두 번에 복사가 딸려 온다. 상각 분석은
[`../../../../../data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/)가 정본이다.
**이 문서에서는 시간을 재지 않았다.**

### (5) ★★ 같은 길이인데 `cap` 이 다르다 — 경로가 수치를 바꾼다

**언제 쓰나** — (4)절의 수치를 「규칙」으로 믿고 싶어질 때의 반례다.

```text
===== 소스: t06e.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
※ cap 값은 gc go1.27.1 의 관찰이다 — 명세는 cap 을 정하지 않는다.
하나씩 다섯 번 append  len=5 cap=8
한 번에 다섯 개 append len=5 cap=6
슬라이스를 통째로 append len=5 cap=6
make([]int, 5)         len=5 cap=5

네 슬라이스의 내용이 같은가 : true
cap 이 같은가              : false
(exit 0)
```

그림 해설 (한 단계씩):

- 네 슬라이스 **내용이 전부 같다**(`true`). 길이도 다섯으로 같다.
- 그런데 `cap` 이 **8 · 6 · 6 · 5** 로 갈린다.
  - 하나씩 다섯 번 붙이면 4 → 8 을 거쳐 **8**.
  - 한 번에 다섯 개를 붙이면 **6**.
  - 슬라이스를 통째로 붙여도 **6**.
  - `make([]int, 5)` 는 **5**.
- ★★ **「같은 결과에 이르는 길이 다르면 `cap` 도 다르다.」** `cap` 은 값의 성질이 아니라
  **어떻게 만들어졌는지의 흔적**이다.
- ★ 그래서 **`cap` 을 근거로 「이 슬라이스가 어떤 것인가」를 판단하면 안 된다.**
  `cap` 으로 판단해도 되는 것은 딱 하나 — **다음 `append` 가 이사할 것인가**다.
- 한 가지 덧붙일 관찰이 있다. (3)절의 `nil` 행에서는 `append(s, add...)` 로 **한 개**를 붙였는데
  `cap` 이 **1** 이었고, (6)절에서는 `append(n, 1)` 로 한 개를 붙이는데 `cap` 이 **4** 다.
  **같은 「한 개 붙이기」인데 호출 꼴이 다르면 수치가 다르다** — 구현이라는 증거가 하나 더 늘었다.

비용 — 없음. 다만 **불필요한 재할당**이 숨는다((3)절의 예측식으로 잡는다).

### (6) `append` 의 여러 형태

**언제 쓰나** — 문자열을 바이트로 이을 때, 슬라이스를 통째로 이을 때.

```text
===== 소스: t06f.go =====
package main

import "fmt"

func main() {
	var b []byte
	b = append(b, "bar"...)
	fmt.Printf("append(b, \"bar\"...)  = %q  len=%d cap=%d\n", b, len(b), cap(b))

	var t []any
	t = append(t, 42, 3.1415, "foo")
	fmt.Printf("append(t, 42, 3.1415, \"foo\") = %v  len=%d cap=%d\n", t, len(t), cap(t))

	var n []int
	fmt.Printf("nil 에 append 하기 전  n == nil : %t  len=%d cap=%d\n", n == nil, len(n), cap(n))
	n = append(n, 1)
	fmt.Printf("append(n, 1) 뒤        n == nil : %t  len=%d cap=%d\n", n == nil, len(n), cap(n))

	var z []int
	z = append(z)
	fmt.Printf("append(z) 만 하면      z == nil : %t\n", z == nil)

	e := []int{1, 2, 3}
	e = append(e, []int{}...)
	fmt.Printf("빈 슬라이스를 붙이면    len=%d cap=%d\n", len(e), cap(e))
}
===== 명령: go build -trimpath -o prog . && ./prog =====
append(b, "bar"...)  = "bar"  len=3 cap=8
append(t, 42, 3.1415, "foo") = [42 3.1415 foo]  len=3 cap=3
nil 에 append 하기 전  n == nil : true  len=0 cap=0
append(n, 1) 뒤        n == nil : false  len=1 cap=4
append(z) 만 하면      z == nil : true
빈 슬라이스를 붙이면    len=3 cap=3
(exit 0)
```

그림 해설 (한 단계씩):

- **`append(b, "bar"...)`** 가 된다. 명세가 특례로 적어 둔 꼴이다.

  > As a special case, `append` also accepts a slice whose type is assignable to type `[]byte`
  > with a second argument of **string type** followed by `...`. This form appends the bytes of the string.

- `append(t, 42, 3.1415, "foo")` — `[]any` 에는 아무거나 들어간다. 여러 개를 한 번에 붙인다.
- **`nil` 에 붙이면 `nil` 이 아니게 된다.** `append` 가 배열을 잡았기 때문이다.
- ★ **`append(z)` 만 하면 `z` 는 여전히 `nil`** 이다. 붙일 것이 없으면 **배열을 안 잡는다.**
  명세가 "appends **zero or more** values" 라고 적은 그 자리다.
- 빈 슬라이스를 붙여도 `len`·`cap` 이 안 변한다.
- ★ `append(b, "bar"...)` 의 `cap` 이 **8**인 것은 (4)절과 같은 이유로 **구현**이다.
  `[]byte` 는 원소가 1바이트라 메모리 크기 단위가 다르게 걸린다.

비용 — 붙이는 개수만큼. 한 번에 붙이는 쪽이 재할당 횟수가 적다((5)절이 그 흔적이다).

### (7) 컴파일러가 잡는 것 — `append` 와 `make` 를 잘못 쓴 것

**언제 쓰나** — 에러 메시지를 읽고 무엇이 문제인지 바로 알아야 할 때.

```text
===== 소스: t06d.go =====
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
===== 명령: go build -trimpath -o prog . =====
# ex
./t06d.go:7:2: append(s, 1) (value of type []int) is not used
./t06d.go:11:15: invalid append: argument must be a slice; have arr (variable of type [3]int)
./t06d.go:14:19: invalid argument: length and capacity swapped
./t06d.go:17:17: cannot use "문자열" (untyped string constant) as int value in argument to append
(exit 1)
```

그림 해설 (한 단계씩):

- **`append(s, 1)` 의 결과를 안 받으면 컴파일 에러**다 —
  `append(s, 1) (value of type []int) is not used`.
  ★ Go 가 「값을 버리는 표현식」을 문장으로 안 쳐 주기 때문에 **이 실수는 컴파일 타임에 잡힌다.**
  05번 주제에서 본 「함수 안의 `append` 가 안 보이는」 사고와 **다르다** —
  그쪽은 결과를 받긴 받았는데 **호출자에게 안 간 것**이라 컴파일러가 못 잡는다.
- **배열에는 `append` 못 한다** — `invalid append: argument must be a slice`.
- **`make([]int, 5, 3)`** 은 `invalid argument: length and capacity swapped`.
  명세: "If both `n` and `m` are provided and are constant, then **`n` must be no larger than `m`**."
- 원소 타입이 안 맞으면 보통의 타입 에러다.

`make` 의 인자가 **런타임에** 잘못되면 컴파일러가 못 잡는다.

```text
===== 소스: t06h.go =====
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
===== 명령: go build -trimpath -o prog . =====
(exit 0)
===== 명령: ./prog 2>&1 =====
make([]int, 3) 은 된다 : [0 0 0]
----- 여기까지 stdout · 아래부터 패닉 -----
panic: runtime error: makeslice: len out of range

goroutine 1 [running]:
main.main()
	ex/t06h.go:13 +0xd4
(exit 2)
```

- `makeslice: len out of range`, 종료 코드 **2**.
- 명세: "if `n` is negative or larger than the maximum allowed value,
  **a run-time panic occurs**."
- ★ **상수면 컴파일 에러, 변수면 런타임 패닉** — 03·04번 주제에서 본 것과 같은 갈림이다.

비용 — 없음.

### (8) ★ 네 번째 창 — 재할당 **횟수**를 세는 창

`cap` 하나로는 「지금 여유가 얼마인가」만 보인다. 「**지금까지 몇 번 이사했나**」는 안 보인다.
그래서 이 주제는 **기반 배열이 바뀔 때마다 세는 창**을 쓴다.

```text
===== 소스: t06c.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
make(0, 4)       len=0  cap=4  기반배열=A
append 1  뒤     len=1  cap=4  기반배열=A
append 2  뒤     len=2  cap=4  기반배열=A
append 3  뒤     len=3  cap=4  기반배열=A
append 4  뒤     len=4  cap=4  기반배열=A
append 5  뒤     len=5  cap=8  기반배열=B  ← 재할당
append 6  뒤     len=6  cap=8  기반배열=B
append 7  뒤     len=7  cap=8  기반배열=B
append 8  뒤     len=8  cap=8  기반배열=B
재할당 횟수 = 1

cap 을 8 로 미리 잡고 8번 append 하면 재할당 횟수 = 0 (len=8 cap=8)
(exit 0)
```

그림 해설 (한 단계씩):

- `cap` 4로 시작해 8번 붙이면 **기반 배열이 `A` → `B` 로 한 번 바뀐다.** 재할당 **1회**.
- `cap` 8로 시작해 8번 붙이면 **0회**다.
- ★ **`make([]T, 0, n)` 으로 미리 잡는 것의 값이 이 한 줄**이다 — 이사가 사라진다.
  다만 **얼마나 빨라지는지는 이 문서에서 재지 않았다.** 잰 것은 **횟수**뿐이다.
- 이 창이 없으면 「`cap` 이 8이 됐다」만 보이고, 그게 **한 번에 됐는지 두 번에 걸쳐 됐는지** 모른다.

**이 창이 답하는 것** — 「이 코드가 이사를 몇 번 하나」.
성능 이야기를 하려면 **여기서 시작해서 벤치마크로 넘어가야** 한다([목록의 **50번 주제**](../50-benchmarks-testing-b-and-reading-profiles/)).

## 문법 — 형태와 규칙

### 형태

```go
// t06form.go
package main

import "fmt"

func main() {
	s := make([]int, 0, 4) // ① 길이 0 · 용량 4 로 미리 잡는다
	s = append(s, 1, 2, 3) // ② append 는 결과를 반드시 받는다
	s = append(s, s...)    // ③ 슬라이스를 통째로 붙인다
	var b []byte
	b = append(b, "hi"...) // ④ 문자열의 바이트를 붙인다
	fits := len(s)+1 <= cap(s)
	fmt.Println(s, len(s), cap(s), string(b), fits)
}
```

```text
===== 소스: t06form.go =====
package main

import "fmt"

func main() {
	s := make([]int, 0, 4) // ① 길이 0 · 용량 4 로 미리 잡는다
	s = append(s, 1, 2, 3) // ② append 는 결과를 반드시 받는다
	s = append(s, s...)    // ③ 슬라이스를 통째로 붙인다
	var b []byte
	b = append(b, "hi"...) // ④ 문자열의 바이트를 붙인다
	fits := len(s)+1 <= cap(s)
	fmt.Println(s, len(s), cap(s), string(b), fits)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
[1 2 3 1 2 3] 6 8 hi true
(exit 0)
```

규칙 불릿.

- **`append` 는 결과를 돌려준다.** 받지 않으면 컴파일 에러다. 관용은 `s = append(s, x)` 다.
- `append(s, xs...)` 로 슬라이스를 통째로, `append(b, "문자열"...)` 로 문자열의 바이트를 붙인다.
- **`cap` 은 `make` 로만 여유가 생긴다.** 리터럴·`make(T, n)` 은 `cap == len` 이다.
- 슬라이싱은 **앞을 자르면 `cap` 도 줄고 뒤를 자르면 `cap` 은 안 준다.**
- **재할당 예측식** — `len(s) + 붙일 개수 <= cap(s)` 면 제자리.
- `0 <= len(s) <= cap(s)` 는 **명세가 보장하는 항등식**이다.
- **새 `cap` 의 수치는 구현이다.** 코드가 그 수치에 기대면 안 된다.

### 금지 사례 — 컴파일러가 거부하는 것

- **결과를 버린 `append`** — (7)절 첫 줄.
- **배열에 `append`** — (7)절 둘째 줄.
- **`make([]T, len, cap)` 의 두 수가 뒤바뀐 것** — (7)절 셋째 줄(둘 다 상수일 때만 잡힌다).
- **음수 길이의 `make`** — 변수면 **런타임 패닉**이다.

## 어디서 틀리나

### 1. ★★★ 「`append` 는 `cap` 을 두 배로 늘린다」

- (4)절 실측 — **512 에서 깨진다.** 512 → 848 은 1.656배다.
- 게다가 (5)절 실측 — **같은 길이에 `cap` 이 8·6·6·5 로 갈린다.** 「배」로는 설명이 안 된다.
- 고치는 법 — 문서에 적을 때 **「구현이다」를 같이 적는다.**
  수치가 필요하면 **판을 명시하고 「이 판의 관찰」로** 적는다.

### 2. ★★★ 「`cap` 이 커졌으니 새 배열이겠지」

- 아니다. **3-인덱스 슬라이싱으로도 `cap` 은 바뀐다**(줄어드는 쪽으로).
  또 `append` 가 제자리에 써도 `len` 은 커지고 `cap` 은 그대로다.
- 반대도 틀린다 — **`cap` 이 그대로여도 새 배열일 수** 있다(원리상 명세가 막지 않는다).
- 고치는 법 — 재할당 여부를 정말 알아야 하면 **기반 배열 동일성**을 본다((8)절의 창).
  실무에서는 **예측식**((3)절)으로 충분하다.

### 3. ★★ 「`make([]T, n)` 으로 만들고 `append` 하면 된다」

- `make([]int, 5)` 는 `len` 5다. 거기에 `append` 하면 **여섯 번째 칸부터** 들어간다 —
  앞의 다섯 칸은 **제로값 그대로 남는다.**
- 의도가 「5개 들어갈 자리를 잡아 두기」면 **`make([]int, 0, 5)`** 다.
- 고치는 법 — **`len` 자리에 쓸 것인지 `cap` 자리에 쓸 것인지 먼저 정한다.**

### 4. ★★ 「`cap` 을 미리 잡으면 무조건 빠르다」

- (8)절이 보인 것은 **재할당 횟수가 1 → 0** 이라는 사실뿐이다. **시간은 재지 않았다.**
- 미리 잡는 것에도 대가가 있다 — **안 쓸 메모리를 먼저 잡는다.**
- 고치는 법 — 개수를 알 때만 잡는다. 「빠르다」를 주장하려면 **벤치마크가 따로 필요**하다.

### 5. ★ 「`append` 결과를 안 받아도 되는 경우가 있다」

- (7)절 — **컴파일 에러**다. 예외가 없다.
- 다만 **함수 안에서 받아 놓고 호출자에게 안 돌려주는 것**은 컴파일러가 못 잡는다(05번 주제 (3)절).
  이쪽이 진짜 사고다.

### 6. ★ 「`append(s)` 는 아무 일도 안 하니 `s` 그대로겠지」

- (6)절 실측 — `nil` 에 `append(z)` 만 하면 **`z` 는 여전히 `nil`** 이다. 그것은 맞다.
- 그런데 (3)절 실측 — `[]int{1,2,3}` 에 0개를 붙이면 **같은 배열을 그대로 돌려준다.**
  즉 `append(s)` 는 **복사본이 아니다.** 「빈 `append` 로 복사하기」는 안 된다.
- 고치는 법 — 복사는 `slices.Clone` 이나 `copy` 다(08번 주제).

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| `0 <= len(s) <= cap(s)` | **명세 보장** | "At any time the following relationship holds" |
| 배열의 `cap` 이 `len` 과 같은 것 | **명세 보장** | `cap` 표의 `[n]T` 행이 "array length (== n)" |
| `append` 가 **모자라면 새 배열, 아니면 재사용** | **명세 보장** | "allocates a new … Otherwise, `append` re-uses the underlying array." |
| `append` 가 **결과를 돌려주는** 것 | **명세 보장** | "returns the resulting slice" |
| `append(b, "str"...)` 가 되는 것 | **명세 보장** | "As a special case … a second argument of string type" |
| `make(T, n, m)` 에서 **`n <= m`** | **명세 보장** | "`n` must be no larger than `m`" |
| 음수 `make` 가 **런타임 패닉** | **명세 보장** | "a run-time panic occurs" |
| 슬라이싱이 `cap` 을 `cap(a)-low` 로 만드는 것 | **명세 보장** | Slice expressions 절 |
| **재할당 뒤의 `cap` 수치**(4·8·…·848·1280·1792·2560) | **구현(gc)** | 명세의 낱말은 "sufficiently large" 뿐이다 |
| **512 에서 배가 깨지는 것** | **구현(gc)** | (4)절 관찰. 임계값도 비율도 명세에 없다 |
| **경로에 따라 `cap` 이 8·6·6·5 로 갈리는 것** | **구현(gc)** | (5)절 관찰 |
| **`append(n, 1)` 은 4, `append(n, add...)` 는 1** | **구현(gc)** | (3)·(6)절을 나란히 놓으면 보인다 |
| `[]byte` 에 3바이트 붙였더니 `cap` 8 | **구현(gc)** | 메모리 크기 단위에 걸린다 |
| 「미리 잡으면 빠르다」 | **안 쟀다** | 잰 것은 **재할당 횟수**뿐이다 |

★ 이 주제의 결론은 「**갈림은 명세, 수치는 구현**」 한 줄이다.
`cap` 을 **예측에** 쓰는 것은 명세가 떠받쳐 주고, `cap` 의 **수치에 기대는** 것은 아무것도 떠받치지 않는다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 개수를 아는 목록을 만든다 | **`make([]T, 0, n)`** + `append` | 재할당 0회((8)절) |
| 개수만큼 채워 넣는다(인덱스로) | **`make([]T, n)`** | `len` 이 n 이라 `s[i] = …` 가 된다 |
| 개수를 모른다 | **`var s []T`** + `append` | `nil` 은 할당이 0이다 |
| 남의 슬라이스에 붙인다 | **`s[:n:n]`** 으로 이사 강제 | 이웃을 덮지 않는다(07·08번 주제) |
| 붙일 것이 여러 개다 | **`append(s, xs...)` 한 번** | 재할당 횟수가 준다 |
| 문자열을 `[]byte` 에 잇는다 | `append(b, s...)` | 명세의 특례. 변환이 필요 없다 |
| 재할당 여부를 꼭 알아야 한다 | `len(s)+k <= cap(s)` | 예측식은 **명세 보장**이다 |
| 성능을 주장해야 한다 | **벤치마크** | 재할당 횟수는 근거의 절반이다 |
| `cap` 수치를 문서에 적는다 | **「이 판의 관찰」로 적는다** | 명세에 없는 수치다 |

판단 규칙 두 줄.

- **`cap` 은 예측에 쓰고 수치에 기대지 마라.**
- **「배로 늘어난다」고 적지 마라.** 적을 거면 판을 같이 적어라.

## 핵심 문장

- `len` 은 인덱스의 상한, `cap` 은 슬라이싱의 상한이자 **이사 없이 더 넣을 수 있는 한도**다.
- `append` 의 갈림은 한 줄로 예측된다 — **`len(s) + 붙일 개수 <= cap(s)`**.
  여섯 경우에서 예측과 실제가 **전부 일치**했다.
- ★★★ **새 `cap` 이 얼마인지는 명세에 한 글자도 없다.** 이 판의 관찰로는
  512까지 배로 늘다가 **512 → 848**(1.656배)에서 깨지고, 그 뒤로는 비율도 일정하지 않았다.
- ★★ **같은 내용·같은 길이인데 `cap` 이 8·6·6·5 로 갈렸다.**
  `cap` 은 값의 성질이 아니라 **만들어진 경로의 흔적**이다.
- 앞을 자르면 `cap` 도 줄고 **뒤를 자르면 `cap` 은 안 준다.** `arr[:2]` 의 `cap` 이 6이다.
- `append` 는 **결과를 돌려주는 함수**다 — 헤더를 못 바꾸니 그 수밖에 없다. 안 받으면 컴파일 에러다.
- `make([]T, 0, n)` 은 (8)절에서 재할당을 **1회 → 0회**로 줄였다. **시간은 재지 않았다.**
- 상수면 컴파일 에러, 변수면 런타임 패닉 — `make` 에서도 같은 갈림이 되풀이된다.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 06번)
- [목록의 **05번 주제**](../05-arrays-vs-slices-value-and-header/)(배열과 슬라이스) — **그쪽은 「이사하면 공유가 끊긴다」까지**,
  여기는 「**언제 이사하고 얼마나 크게 잡나**」부터
- [목록의 **07번 주제**](../07-slice-sharing-silent-bugs/)(슬라이스 공유로 조용히 틀리는 자리) —
  (2)절의 **두 번째 약속**(재사용한다)이 버그가 되는 사례들
- [목록의 **08번 주제**](../08-copy-three-index-slicing-and-memory-retention/)(`copy`·3-인덱스·메모리 유지) — 이사를 **일부러 강제하는** 법
- [목록의 **38번 주제**](../38-slices-maps-and-cmp/)(`slices`·`maps`·`cmp`) — `slices.Grow`·`slices.Clip` 의 정본
- [목록의 **50번 주제**](../50-benchmarks-testing-b-and-reading-profiles/)(벤치마크) — 「미리 잡으면 빠른가」를 **재는** 자리
- [`../../../../../data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/) —
  **그쪽은 증폭 상각 분석(왜 상수 시간인가)까지**, 여기는 **Go 의 `cap` 을 관찰하는 법**부터
- [`../../../rust/syntax/15-slices-ranges-and-utf8-boundaries/`](../../../rust/syntax/15-slices-ranges-and-utf8-boundaries/) —
  **그쪽 슬라이스에는 `cap` 이 없어 길이를 못 늘린다**(늘리는 것은 `Vec` 의 일),
  여기는 **슬라이스 자체가 `cap` 을 들고 있어 자란다**
- [`../../../python/syntax/09-sequence-ops-and-slicing/`](../../../python/syntax/09-sequence-ops-and-slicing/) —
  **그쪽은 슬라이스 대입으로 길이가 바뀌고**(`a[1:3] = ['X']`), 여기는 **`append` 가 그 일을 한다**

## 용어 풀이

- **`len`** — 슬라이스가 지금 보고 있는 원소 수. 인덱스의 상한.
- **`cap`** — 기반 배열에서 시작점부터 끝까지의 칸 수. 슬라이싱의 상한.
- **재할당(reallocation)** — `append` 가 새 배열을 잡고 옮기는 것.
- **성장 전략(growth strategy)** — 새 `cap` 을 얼마로 잡을지의 규칙. **구현이 정한다.**
- **예측식** — `len(s) + 붙일 개수 <= cap(s)`. 참이면 제자리, 거짓이면 이사.
- **가변 인자(variadic)** — `append(s, x...)` 처럼 개수가 정해지지 않은 인자. 정본은 [목록의 **12번 주제**](../12-functions-multiple-returns-named-results-and-variadics/).
- **상각 분석(amortized analysis)** — 드문 비싼 연산을 전체에 나눠 세는 분석. 정본은 `data-structure/01`.

---

## 더 들어가면

- `slices.Grow(s, n)`(**1.21**)는 「`n` 개를 더 넣을 자리를 확보한 슬라이스」를 돌려준다.
  `make` 로 다시 잡는 코드를 대신한다. 정본은 [목록의 **38번 주제**](../38-slices-maps-and-cmp/)다.
- `cap` 의 수치가 **메모리 크기 단위(size class)에 맞춰 반올림**되는 것이 (4)절 뒤쪽 숫자의 이유로 보인다
  (848·1280·1792 는 배도 1.25배도 아니다). **소스를 읽어 확인하지는 않았다** —
  이 문서는 관찰만 싣는다.
- `append` 가 **겹치는 슬라이스**를 붙여도 결과가 정해져 있다.
  명세: "For both functions, the result is **independent of whether the memory referenced
  by the arguments overlaps**." 08번 주제에서 `copy` 쪽을 실측한다.
- `make` 의 크기 상한은 구현에 달렸다. `makeslice: len out of range` 가 그 상한을 넘었을 때 나온다.
  **이 문서에서는 상한 자체를 재지 않았다.**
- 「`append` 가 여러 개를 한 번에 받으면 딱 맞게 잡는가」는 (5)절에서 **6(5개인데 6)** 이 나와
  「딱 맞게」도 아니었다. 이것도 구현이다.

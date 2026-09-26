# go/syntax/08 — `copy`·3-인덱스 슬라이스·재슬라이싱의 메모리 유지 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Go 명세](https://go.dev/ref/spec) 의 Appending to and copying slices ·
> Full slice expressions · Simple slice expressions · Clear 절.\
> 웹이 아니라 **이 툴체인이 들고 있는 `$(go env GOROOT)/doc/go_spec.html` 을 열어** 인용했다.
> 그 파일의 머리는 「**Language version go1.27 (May 26, 2026)**」이다.
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> ★ **메모리 수치를 싣는 절이 하나 있다**((5)절). 재는 법은 `runtime.GC()` 뒤
> `runtime.ReadMemStats` 의 `HeapAlloc` 을 **MiB 로 반올림**한 것이고,
> **같은 바이너리를 5회 돌려 md5 가 같았다.** 읽을 것은 절댓값이 아니라 「**64가 남아 있나 사라졌나**」다.
> **버전** — `copy`·재슬라이싱은 1.0부터, **3-인덱스 슬라이싱은 1.2**부터,
> `clear`·`slices.Clone`·`slices.Clip` 은 **1.21**부터다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 명세로, 출력은 실행으로 접지했다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | `go_spec.html` 원문 인용 |
| **구현(gc)** | gc 컴파일러·GC 가 그렇게 하는 것 | `cap` 의 수치 · **회수 시점** |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 실행 출력 · `HeapAlloc` 수치 |

★ 이 주제는 **셋이 골고루 있다.** `copy` 와 3-인덱스의 규칙은 명세고,
**「언제 회수되나」는 구현(GC)** 이며, 64MiB 라는 수치는 이 판의 관찰이다.

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
| **흔들린다** | 기반 배열의 **주소 자체** | 그래서 동일성 비교만 찍는다 |
| **흔들린다** | 패닉 스택의 `goroutine N` 번호와 `+0x…` | 런타임·빌드 산출물 |
| **판·구현이 바뀌면 바뀐다** | **`HeapAlloc` 의 정확한 바이트** | GC 의 회계다. 그래서 **MiB 로 반올림**해 찍었다 |
| **판이 바뀌면 바뀐다** | `cap` 의 구체적 수치 | gc 의 성장 전략(06번 주제) |
| 안 흔들린다 | (5)절의 **0 / 64 / 64 / 0 / 0 패턴** | **같은 바이너리 5회 md5 동일**. 읽을 것은 이 패턴이다 |
| 안 흔들린다 | `copy` 의 **반환값**과 결과 배열 | 명세가 정한다 |
| 안 흔들린다 | 3-인덱스가 만드는 `len`·`cap` | 명세가 `max-low` 로 정한다 |
| 안 흔들린다 | 패닉·컴파일 에러 문장 본문 · 종료 코드 | 같은 소스·같은 판이면 같다 |
| 해당 없음 | 맵 순회 순서 | 이 주제는 맵을 안 쓴다 |

## 한눈에 — 쉽게 말하면

**공유를 끊는 방법은 둘뿐이다 — 「여기까지만 내 것」이라고 선을 긋거나(`s[a:b:c]`),
아예 새 종이에 베끼거나(`copy`).**

그리고 반대쪽 함정이 하나 더 있다 —
**작은 조각 하나를 들고 있으면 그 조각이 속한 큰 배열이 통째로 안 없어진다.**

| 비유 | 실체 |
|---|---|
| 「나는 3쪽까지만 쓴다」고 못 박기 | `s[:3:3]` — **`cap` 을 `len` 까지 자른다** |
| 새 종이에 베끼기 | `copy(dst, src)` / `slices.Clone` |
| 짧은 쪽 종이만큼만 베껴진다 | `copy` 는 **`min(len(dst), len(src))`** 만큼 |
| 책 한 권에서 한 줄만 찢어 보관 | `head := big[:3]` — **책 전체가 안 버려진다** |
| 한 줄만 옮겨 적고 책을 버린다 | `copy` 로 끊기 — **책이 회수된다** |
| 쓴 자리를 지우기 | `clear(s[n:])` — 꼬리가 물고 있던 것을 놓는다 |

- 05·06번 주제가 「**왜 공유가 생기나**」, 07번 주제가 「**그래서 어떻게 틀리나**」였다.
  이 주제는 「**그래서 어떻게 막나**」다.
- ★ 그런데 막는 방법이 **비용을 만든다** — `copy` 는 복사 비용, 3-인덱스는 다음 `append` 의 재할당.
  **공짜로 안전한 길은 없다.**

```text
   공유를 끊는 두 길

   ① 선을 긋는다                       ② 베낀다
   all  [1 2 3 4 5 6]                  all  [1 2 3 4 5 6]
   cut = all[:3:3]                     own = make([]int, 3); copy(own, all[:3])
        len 3 · cap 3                       len 3 · cap 3 · 새 배열
        (아직 같은 배열을 본다)              (이미 남남이다)
   append -> 여기서 비로소 새 배열        append -> 당연히 남남

   반대 함정 — 안 끊으면 큰 것이 안 없어진다
   big  [ 64MiB ..................... ]
   head = big[:3]     <- 이 3바이트가 64MiB 를 붙잡고 있다
```

> **3-인덱스 슬라이싱(full slice expression)** — `a[low:high:max]`.
> `len` 은 `high-low`, **`cap` 은 `max-low`** 가 된다.\
> 예: `all[:3:3]` 은 `len` 3 `cap` 3이라 **다음 `append` 가 반드시 새 배열을 잡는다**.

> **메모리 유지(memory retention)** — 작은 슬라이스가 큰 기반 배열의 회수를 막는 것.\
> 예: 64MiB 배열의 3바이트를 들고 있으면 **64MiB 가 안 없어진다**((5)절 실측).

> **얕은 복사(shallow copy)** — 한 겹만 베끼는 것. `copy` 도 `slices.Clone` 도 얕다.\
> 예: `[][]int` 를 `copy` 하면 **바깥 칸만 베껴지고 안쪽은 공유**다((8)절).

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `copy` 는 **정확히 몇 개**를 베끼나 — 무엇을 보고 그 수를 정하나.
2. `s[a:b:c]` 는 **무엇을 바꾸나** — 그것이 왜 공유를 끊는 도구가 되나.
3. 작은 조각이 **왜 큰 배열을 살려 두나** — 그것을 어떻게 재고 어떻게 끊나.

★ GC 가 **어떻게** 회수하는지는 이 주제가 아니다 —
[`../../../../memory-management/`](../../../../memory-management/)가 정본이다.
여기는 **무엇이 무엇을 붙잡는지**만 본다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

| 창 | 무엇을 보여 주나 | 한계 |
|---|---|---|
| `len`·`cap` | 선이 어디 그어졌나 | 공유 여부를 **못 가른다** |
| 기반 배열 동일성 | 끊겼나 안 끊겼나 | **얼마나 붙잡고 있는지**는 안 보인다 |
| `copy` 의 **반환값** | 몇 개가 실제로 베껴졌나 | 「왜 그 수인가」는 안 보인다 |
| ★★ **`runtime.ReadMemStats`** | **얼마가 살아 있나** | GC 의 회계라 **정확한 바이트는 흔들린다** — 패턴만 읽는다 |

★ 네 번째 창이 이 주제에만 있다. 앞의 셋은 「**끊겼나**」를 답하지만
「**안 끊어서 얼마를 붙잡고 있나**」는 못 답한다. 그것을 재려면 힙을 들여다봐야 한다.

### (1) `copy` 는 짧은 쪽만큼 — 그리고 보는 것은 `len` 이다

**언제 쓰나** — 공유를 끊을 때, 버퍼를 채울 때.

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

그림 해설 (한 단계씩):

- `copy(len 2, len 5)` → **2**. `copy(len 8, len 5)` → **5**. **짧은 쪽이 답이다.**
- `nil` 이 어느 쪽에 있어도 **0**이고 **패닉하지 않는다.**
- 베낀 뒤 `full[0] = 99` 가 `src` 에 **안 보인다** — `&src[0] == &full[0]` 이 **false**.
  **공유가 끊겼다.**
- ★★ 마지막 줄이 이 절에서 가장 자주 틀리는 자리다 —
  `copy(make([]int, 0, 8), src)` 가 **0**을 돌려준다.
  **`copy` 는 `cap` 이 아니라 `len` 을 본다.** `cap` 8짜리라도 `len` 이 0이면 한 개도 안 베껴진다.
- 고치는 법 — `make([]T, len(src))` 로 만들거나, `append(dst[:0], src...)` 를 쓴다.

명세:

> The number of elements copied is **the minimum of `len(src)` and `len(dst)`**.

비용 — 베낀 개수만큼. 그 이상도 이하도 아니다.

### (2) 겹쳐도 결과가 정해져 있다

**언제 쓰나** — 같은 배열 안에서 밀 때(삭제 관용구의 속).

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

그림 해설 (한 단계씩):

- `copy(a, a[2:])` 는 **왼쪽으로 민다** — `[2 3 4 5 4 5]`. 앞 네 칸이 밀렸고 뒤 두 칸은 옛 값이다.
- `copy(b[2:], b)` 는 **오른쪽으로 민다** — `[0 1 0 1 2 3]`.
  ★ 순진하게 앞에서부터 한 칸씩 옮기면 `[0 1 0 0 0 0]` 처럼 **번져야** 하는데 안 번졌다.
- 명세가 그것을 약속한다.

  > For both functions, **the result is independent of whether the memory referenced
  > by the arguments overlaps.**

- `copy([]byte, "XY")` 도 된다 — 문자열을 바이트로 베끼는 특례다.

  > As a special case, `copy` also accepts a destination argument assignable to type `[]byte`
  > with a source argument of a **string** type.

- ★ 이 보장 덕에 07번 주제의 삭제 관용구가 **값은 맞게** 나온다. 틀리는 것은 **꼬리**였다((7)절).

비용 — 겹쳐도 한 번의 이동이다.

### (3) ★★ 3-인덱스 슬라이싱 — `cap` 을 잘라 이사를 강제한다

**언제 쓰나** — 남에게 슬라이스를 줄 때, 남의 슬라이스를 받아 붙일 때.

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

그림 해설 (한 단계씩):

- `all[:3]` 은 `cap` **6**, `all[:3:3]` 은 `cap` **3**이다. 세 번째 숫자가 **`cap` 의 끝**을 정한다.

  > Additionally, it controls the resulting slice's capacity by setting it to **`max - low`**.

- 그 차이가 `append` 에서 갈린다.
  - `append(all[:3], 99)` → **같은 배열**(true). 그래서 `all` 이 `[1 2 3 99 5 6]` 으로 **덮였다.**
  - `append(all[:3:3], 99)` → **다른 배열**(false). `all` 은 `[1 2 3 4 5 6]` 그대로다.
- ★ 돌려받은 슬라이스의 `cap` 이 **6**인 것에 주의하라 — 새 배열이 잡히면서 여유가 다시 생겼다.
  **`cap` 을 자른 것은 그 한 번의 `append` 를 가르기 위해서**지 영구히 작게 만들려는 것이 아니다.
- ★★ 한 줄 규칙 — **남에게 넘기는 슬라이스에는 세 번째 숫자를 붙여라.**
  그러면 받는 쪽이 `append` 해도 내 데이터가 안 다친다.

```text
   all[:3]      len 3 · cap 6      [1 2 3|4 5 6]   append -> 4번 칸에 쓴다 (남의 칸)
   all[:3:3]    len 3 · cap 3      [1 2 3]|         append -> 새 배열을 잡는다
                                         ^ 선
```

비용 — 슬라이싱 자체는 공짜다. 대가는 **다음 `append` 가 반드시 복사한다**는 것이다.

범위를 넘기면 패닉한다.

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

- `all[1:3:5]` 는 `cap` **4**(`5-1`), `all[1:3:3]` 은 `cap` **2**, `all[3:3:3]` 은 **빈 것**이다.
- `all[1:3:2]` 는 **패닉** — `slice bounds out of range [:3:2]`.
  명세가 조건을 적었다: "The indices are in range if **`0 <= low <= high <= max <= cap(a)`**."
  여기서는 `high(3) <= max(2)` 가 깨졌다.
- 종료 코드는 **2**다. 마커 줄은 표준 오류로 찍었다.

### (4) ★★ 07번의 버그를 한 글자로 막는다

**언제 쓰나** — 남의 슬라이스를 받는 함수를 쓸 때. 즉 라이브러리 코드 전부.

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

그림 해설 (한 단계씩):

- 세 함수 **결과가 전부 `[1 2 0]`** 으로 같다. 다른 것은 **원본**이다.
  - `Prefix`(07번 주제의 그 함수) → 원본이 **`[1 2 0 4 5]`** 로 짓이겨졌다.
  - `PrefixCut`(`s[:n:n]`) → 원본이 **그대로**다.
  - `PrefixCopy`(`make` + `copy`) → 원본이 **그대로**다.
- ★ 둘의 차이는 **언제 복사하나**다.
  - `s[:n:n]` — **다음 `append` 가 있을 때만** 복사한다. 안 붙이면 복사가 안 일어난다.
  - `copy` — **무조건** 복사한다. 대신 그 뒤로는 아무 걱정이 없다.
- 고르는 법 — **붙일지 안 붙일지 모르면 `s[:n:n]`**, **오래 들고 있을 거면 `copy`**.
  뒤엣것의 이유는 (5)절에 있다.

비용 — `s[:n:n]` 은 **조건부 복사**, `copy` 는 **무조건 복사**.
**어느 쪽이 빠른지는 이 문서에서 재지 않았다.**

### (5) ★★★ 작은 조각이 큰 배열을 살려 둔다

**언제 쓰나** — 큰 버퍼에서 일부만 잘라 오래 보관할 때(파싱·로깅·캐시).

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

그림 해설 (한 단계씩):

- ① 바탕은 **0 MiB**(반올림).
- ② 64MiB 를 잡으니 **64 MiB**.
- ③ **`big` 을 `nil` 로 만들고 3바이트 조각만 들고 있는데 여전히 64 MiB** 다.
  조각의 `cap` 이 **67108864** — **기반 배열 전체를 가리키고 있다**는 것이 그 자리에 찍혀 있다.
- ④ 조각마저 버리니 **0 MiB**. 붙잡고 있던 것이 조각이었음이 증명된다.
- ⑤ 같은 64MiB 를 잡고 **`copy` 로 3바이트를 떠낸** 뒤 원본을 버리면 **0 MiB** 다.
  조각의 `cap` 이 **3**이다.
- ★★ 읽을 것은 **0 / 64 / 64 / 0 / 0 이라는 패턴**이지 절댓값이 아니다.
  같은 바이너리를 **5회 돌려 출력 md5 가 같았다.**
- ★★★ 이 함정의 실무 모양 — `http` 응답 바디를 통째로 읽어 놓고 **그중 한 필드만 슬라이싱해 저장**하면
  **응답 전체가 메모리에 남는다.** 요청이 쌓이면 그대로 누수처럼 보인다.
- 고치는 법 — 오래 들고 있을 조각은 **`copy` 나 `slices.Clone` 으로 떠낸다.**
  ★ **`s[:n:n]` 으로는 안 된다** — 그것은 `cap` 만 자를 뿐 **포인터는 여전히 큰 배열을 가리킨다.**

```text
   big [ ################ 64MiB ################ ]
         ^^^
   head = big[:3]      cap = 67108864   -> 배열 전체가 살아 있다

   cut  [ ### ]        cap = 3          -> copy 로 새 배열. 64MiB 는 회수된다
```

★ **재는 법과 그 한계** — `runtime.GC()` 로 한 번 돌린 뒤 `runtime.ReadMemStats` 의 `HeapAlloc` 을
MiB 로 반올림해 찍었다. **정확한 바이트는 GC 의 회계라 흔들린다.**
또 **회수 「시점」은 구현이다** — 명세는 GC 를 전혀 말하지 않는다.
읽을 수 있는 것은 「**붙잡고 있나 아닌가**」뿐이다.

★★ 한 가지 덧붙일 것 — 이 프로그램은 조각을 **실제로 읽는다**(`kept[0]` 을 찍는다).
처음에 안 읽는 판으로 짰더니 **컴파일러·GC 가 조각을 죽은 것으로 보아 ②부터 0 MiB** 가 나왔다.
**살아 있음을 증명하려면 실제로 써야 한다** — 이것도 구현의 성질이고, 실측으로 뒤집힌 전제다.

비용 — **측정 자체가 `runtime.GC()` 를 부른다.** 운영 코드에 넣을 것이 아니다.

### (6) `slices.Clone` 과 `slices.Clip` — 1.21 이 준 두 이름

**언제 쓰나** — (4)·(5)절의 두 방법에 표준 이름이 필요할 때.

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

그림 해설 (한 단계씩):

- `slices.Clone(part)` → `len` 2 `cap` 2, **다른 배열**(false). (5)절의 `copy` 와 같은 일이다.
- `slices.Clip(part)` → `len` 2 `cap` 2, **같은 배열**(true). (3)절의 `s[:n:n]` 과 같은 일이다.
- `part[:2:2]` 를 손으로 쓴 것도 **같은 배열**(true) — **`Clip` 은 그것의 이름**이다.
- ★★ **`Clone` 과 `Clip` 은 `cap` 이 똑같이 2인데 한쪽만 끊겼다.**
  **`cap` 만 보고 「끊겼다」고 판단하면 안 된다**는 것의 실물 증거다.
- `Clone` 한 쪽을 고쳐도 `src` 가 **안 바뀐다**.
- `slices.Clone(nil)` 은 **`nil`** 이다 — `nil` 다움을 보존한다.

비용 — `Clone` 은 복사, `Clip` 은 공짜(조건부 복사를 뒤로 미룬다).

### (7) 꼬리가 회수를 막는다 — `clear` 로 놓아 준다

**언제 쓰나** — 포인터·큰 구조체의 슬라이스를 줄일 때.

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

그림 해설 (한 단계씩):

- `kept := rows[:2]` 로 줄였는데 **배열에는 네 칸이 그대로 살아 있다** — `kept[:cap(kept)]` 로 보인다.
- `[2]`·`[3]` 이 여전히 `&{3}`·`&{4}` 를 가리킨다. **그 객체들은 회수될 수 없다.**
- `clear(rows[2:])`(**1.21**) 뒤 두 칸이 **`<nil>`** 이 됐다. 이제 놓아 준 것이다.
- `clear` 는 슬라이스를 **`len` 까지 제로값으로 민다.** 길이는 안 바뀐다.

  > `clear(s)` `[]T` — sets all elements up to the length of `s` to the zero value of `T`

- ★ 07번 주제 (3)절의 삭제 관용구가 남긴 꼬리를 **이것으로 지운다.**
- ★ 원소가 `int` 처럼 포인터를 안 품는 타입이면 **회수 문제는 없다.**
  `clear` 가 필요한 것은 **포인터를 품은 타입**일 때다.

비용 — 민 칸 수만큼.

### (8) `copy` 는 얕다

**언제 쓰나** — `[][]T`·구조체 슬라이스를 복사할 때.

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

그림 해설 (한 단계씩):

- `copy(dst, src)` 가 **2**를 돌려준다. 바깥 칸 두 개가 베껴졌다.
- 그런데 `dst[0][0] = 99` 가 **`src` 에도 보인다.** 베껴진 것은 **안쪽 슬라이스의 헤더**다.
- 반면 `dst[1]` 을 **통째로 갈아 끼우면** `src` 는 안 바뀐다 — 바깥 칸은 진짜로 갈라져 있다.
- `&src[0][0] == &dst[0][0]` 이 **true**.
- ★ `slices.Clone` 도 마찬가지로 **얕다.** Go 에는 깊은 복사를 해 주는 표준 장치가 **없다.**
- 고치는 법 — 줄마다 `slices.Clone` 을 돌리는 루프를 **직접** 쓴다.

비용 — 얕은 복사는 바깥 칸만큼. 깊은 복사는 전부.

### (9) ★ 네 번째 창의 짝 — 「잘랐다」고 믿은 뒤쪽이 아직 있다

**언제 쓰나** — 민감한 데이터를 다룰 때. 그리고 「잘랐다」는 말의 뜻을 확인할 때.

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

그림 해설 (한 단계씩):

- `head := buf[:10]` 은 앞 10바이트만 보인다 — **`"user=admin"`**.
- 그런데 `head[:cap(head)]` 는 **`"user=admin;pw=hunter2"`** 다. **잘랐다고 믿은 뒤쪽이 그대로 있다.**
- `copy` 로 뜬 쪽은 `cap` 이 **10**이라 **되살릴 뒤쪽이 없다.**
- ★★ 그래서 Go 에서 「**슬라이싱은 지우는 것이 아니다**」. 보이는 범위를 줄일 뿐이다.
- ★ 이 창은 (5)절의 메모리 유지와 **같은 사실의 다른 얼굴**이다 —
  한쪽은 **메모리가 안 준다**로, 한쪽은 **데이터가 안 사라진다**로 드러난다.
- 진짜로 지우려면 `clear` 로 밀거나 `copy` 로 필요한 만큼만 떠낸다.

비용 — 없음. **인식의 문제**다.

## 문법 — 형태와 규칙

### 형태

```go
// t08form.go
package main

import (
	"fmt"
	"slices"
)

func main() {
	src := []int{1, 2, 3, 4, 5, 6}
	n := copy(make([]int, 3), src) // ① 짧은 쪽만큼만 베낀다
	cut := src[1:3:3]              // ② 3-인덱스 — cap 을 잘라 공유를 끊는다
	cl := slices.Clone(src[1:3])   // ③ 1.21 — 새 배열에 뜬다
	cp := slices.Clip(src[1:3])    // ④ 1.21 — cap 만 len 까지 자른다
	own := make([]int, 2)
	copy(own, src[1:3]) // ⑤ 손으로 같은 일을 한다
	fmt.Println(n, cut, cap(cut), cl, cap(cl), cp, cap(cp), own)
}
```

```text
===== 소스: t08form.go =====
package main

import (
	"fmt"
	"slices"
)

func main() {
	src := []int{1, 2, 3, 4, 5, 6}
	n := copy(make([]int, 3), src) // ① 짧은 쪽만큼만 베낀다
	cut := src[1:3:3]              // ② 3-인덱스 — cap 을 잘라 공유를 끊는다
	cl := slices.Clone(src[1:3])   // ③ 1.21 — 새 배열에 뜬다
	cp := slices.Clip(src[1:3])    // ④ 1.21 — cap 만 len 까지 자른다
	own := make([]int, 2)
	copy(own, src[1:3]) // ⑤ 손으로 같은 일을 한다
	fmt.Println(n, cut, cap(cut), cl, cap(cl), cp, cap(cp), own)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
3 [2 3] 2 [2 3] 2 [2 3] 2 [2 3]
(exit 0)
```

규칙 불릿.

- **`copy(dst, src)` 는 `min(len(dst), len(src))` 만큼** 베끼고 **그 수를 돌려준다.**
  **보는 것은 `len` 이지 `cap` 이 아니다.**
- `copy` 는 **겹쳐도 결과가 정해져 있다.** `copy(dst []byte, src string)` 특례가 있다.
- `a[low:high:max]` 는 **`len = high-low`, `cap = max-low`** 다. `low` 만 생략할 수 있다.
- 범위 조건은 **`0 <= low <= high <= max <= cap(a)`**. 어기면 런타임 패닉이다.
- **`slices.Clip` = `s[:len(s):len(s)]`**(같은 배열), **`slices.Clone` = 새 배열**. 둘 다 **1.21**.
- **`clear(s)` 는 `len` 까지 제로값으로 민다.** 길이는 안 바뀐다. **1.21**.
- **`copy`·`Clone` 은 얕다.** 깊은 복사는 직접 쓴다.

### 금지 사례 — 거부되는 것

- **`max` 가 `high` 보다 작으면** 런타임 패닉((3)절 뒤쪽 블록).
- **문자열에는 3-인덱스를 못 쓴다** — 명세가 "for an array, pointer to array, or slice `a`
  (**but not a string**)" 라고 적었다.
- **`copy` 에 `nil` 리터럴을 바로 못 준다** — `invalid copy: argument must be a slice; have untyped nil`.
  `nil` 슬라이스 **변수**는 된다((1)절이 그 꼴을 쓴다).

## 어디서 틀리나

### 1. ★★★ 「슬라이싱했으니 나머지는 사라졌다」

- (5)절 실측 — 3바이트만 들고 있는데 **64 MiB 가 안 없어진다.**
- (9)절 실측 — `head[:cap(head)]` 로 **잘라낸 뒤쪽이 그대로 읽힌다.**
- 고치는 법 — 오래 들거나 민감한 데이터면 **`copy`·`slices.Clone`** 으로 떠낸다.

### 2. ★★★ 「`s[:n:n]` 을 썼으니 메모리도 안 붙잡는다」

- **아니다.** 3-인덱스는 **`cap` 만 자른다.** 포인터는 여전히 큰 배열의 시작을 가리킨다.
- (6)절이 그 증거다 — `slices.Clip` 의 결과가 **같은 배열**(true)이다.
- 고치는 법 — 두 문제를 **따로** 생각한다.
  **공유를 끊는 것은 `s[:n:n]`**, **메모리를 놓는 것은 `copy`** 다.

### 3. ★★ 「`copy` 가 `cap` 만큼 베낀다」

- (1)절 실측 — `copy(make([]int, 0, 8), src)` 가 **0**이다.
- 고치는 법 — `make([]T, len(src))` 로 만들거나 `append(dst[:0], src...)` 를 쓴다.

### 4. ★★ 「`cap` 이 `len` 과 같으면 끊긴 것이다」

- (6)절 실측 — `Clone` 과 `Clip` 이 **둘 다 `cap` 2**인데 **한쪽만 끊겼다.**
- 고치는 법 — 끊겼는지는 **기반 배열 동일성**으로만 판정한다.

### 5. ★★ 「`copy` 했으니 깊은 복사다」

- (8)절 실측 — `[][]int` 의 안쪽은 **공유**다.
- 고치는 법 — 줄마다 복사하는 루프를 **직접** 쓴다. Go 에 자동 장치는 없다.

### 6. ★ 「원소를 지웠으니 객체도 회수된다」

- (7)절 실측 — `rows[:2]` 로 줄여도 꼬리 두 칸이 **객체를 붙잡고 있다.**
- 고치는 법 — `clear(rows[2:])`(**1.21**). `int` 같은 타입에는 필요 없다.

### 7. ★ 「3-인덱스로 자르면 그 슬라이스는 영원히 작다」

- (3)절 실측 — `append` 로 새 배열이 잡히면서 **`cap` 이 다시 6이 됐다.**
- 3-인덱스는 **그 한 번의 `append` 를 가르는 장치**지 영구 제한이 아니다.

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| `copy` 가 **`min(len(dst), len(src))`** | **명세 보장** | "the minimum of `len(src)` and `len(dst)`" |
| `copy` 가 **개수를 돌려주는** 것 | **명세 보장** | "returns the number of elements copied" |
| `copy` 가 **겹쳐도 결과가 정해진** 것 | **명세 보장** | "the result is independent of whether the memory … overlaps" |
| `copy(dst []byte, src string)` 특례 | **명세 보장** | "As a special case … a source argument of a string type" |
| `a[l:h:m]` 의 `cap` 이 **`m-l`** | **명세 보장** | "controls the resulting slice's capacity by setting it to `max - low`" |
| 범위 조건 `0 <= l <= h <= m <= cap(a)` | **명세 보장** | Full slice expressions |
| 문자열에 3-인덱스 **불가** | **명세 보장** | "but not a string" |
| `clear(s)` 가 **`len` 까지** 제로값 | **명세 보장** | Clear 절의 표 |
| **작은 조각이 큰 배열을 붙잡는 것** | **명세 보장의 결과** | 슬라이스가 기반 배열을 가리킨다는 사실에서 따라 나온다 |
| **언제 회수되나**(④에서 0이 되는 것) | **구현(GC)** | 명세는 GC 를 말하지 않는다 |
| **`HeapAlloc` 의 정확한 값** | **구현(런타임의 회계)** | 그래서 MiB 로 반올림해 읽는다 |
| **조각을 안 읽으면 ②부터 0이 되는 것** | **구현(최적화·GC)** | 실측으로 뒤집힌 전제. 살아 있음을 보이려면 **써야** 한다 |
| `append` 뒤 `cap` 이 6이 되는 것 | **구현(gc)** | 06번 주제 |
| `slices.Clip`·`Clone`·`clear` 가 있는 것 | **표준 라이브러리·내장(1.21+)** | 1.20 이하에는 없다 |

★ 이 주제의 결론은 「**무엇이 무엇을 붙잡는지는 명세가 정하고, 언제 놓는지는 구현이 정한다**」이다.
그래서 (5)절의 수치는 **근거가 아니라 예시**다 — 근거는 `cap` 이 67108864 라는 **명세적 사실**이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 남에게 슬라이스를 넘긴다 | **`s[:n:n]`** (= `slices.Clip`) | 받는 쪽이 붙여도 안 다친다. 복사는 안 일어난다 |
| 남의 슬라이스를 받아 붙인다 | **`append(s[:n:n], …)`** | 07번 주제의 버그가 사라진다 |
| 조각을 **오래 보관**한다 | **`copy` / `slices.Clone`** | 큰 배열을 놓아 준다((5)절) |
| 민감한 데이터의 일부만 남긴다 | **`copy`** | 슬라이싱은 뒤쪽을 지우지 않는다((9)절) |
| 버퍼를 채운다 | `copy(buf[:n], src)` | `len` 을 맞춰 줘야 베껴진다 |
| 같은 배열 안에서 민다 | `copy` 그대로 | 겹쳐도 결과가 보장된다 |
| 포인터 슬라이스를 줄인다 | `clear(s[n:])` 뒤 `s = s[:n]` | 꼬리가 회수를 막는다 |
| `[][]T` 를 복사한다 | **줄마다 `Clone`** | `copy` 는 얕다 |
| 「끊겼나」를 확인한다 | **기반 배열 동일성** | `cap` 으로는 못 가른다 |
| 메모리 유지를 재 본다 | `runtime.GC()` + `ReadMemStats` | **실험용이다.** 운영 코드에 넣지 않는다 |

판단 규칙 두 줄.

- **「공유를 끊는 것」과 「메모리를 놓는 것」은 다른 문제다.** 앞엣것은 `s[:n:n]`, 뒤엣것은 `copy` 다.
- **「보이지 않는다」가 「없다」가 아니다.** `cap` 까지 다시 슬라이싱하면 돌아온다.

## 핵심 문장

- `copy` 는 **짧은 쪽 `len` 만큼** 베끼고 그 수를 돌려준다. **`cap` 은 안 본다** —
  `make([]int, 0, 8)` 에 베끼면 **0개**다.
- `copy` 는 **겹쳐도 결과가 정해져 있다.** 명세가 그렇게 적었다.
- `a[low:high:max]` 는 **`cap` 을 `max-low`** 로 못 박는다. `s[:n:n]` 이 다음 `append` 를 **반드시 이사**시킨다.
- ★★ **`s[:n:n]` 은 공유를 끊지만 메모리는 안 놓는다.** `slices.Clip` 의 결과가 **같은 배열**인 것이 증거다.
- ★★★ **3바이트를 들고 있으면 64MiB 가 안 없어진다.** `cap` 이 **67108864** 라는 것이 그 자리에 찍혀 있다.
  `copy` 로 떠내면 **0 MiB** 가 된다.
- ★ 그 실험은 **조각을 실제로 읽어야** 성립한다 — 안 읽으면 처음부터 0이 나온다(실측으로 뒤집힌 전제).
- **슬라이싱은 지우는 것이 아니다.** `head[:cap(head)]` 로 **잘라낸 뒤쪽이 그대로 읽힌다.**
- `clear(s[n:])`(**1.21**)가 꼬리의 포인터를 놓아 준다. `int` 슬라이스에는 필요 없다.
- **`copy` 도 `Clone` 도 얕다.** `[][]int` 의 안쪽은 공유다.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 08번)
- [목록의 **05번 주제**](../05-arrays-vs-slices-value-and-header/)(배열과 슬라이스) — 헤더 세 칸과 공유의 정본. (3)절의 `cap` 이 거기서 온다
- [목록의 **06번 주제**](../06-len-cap-and-append-reallocation/)(`len`/`cap`과 `append`) — **그쪽은 예측식과 성장 전략까지**,
  여기는 **예측을 무력화하는 법**부터
- [목록의 **07번 주제**](../07-slice-sharing-silent-bugs/)(슬라이스 공유로 조용히 틀리는 자리) —
  **그쪽은 버그의 모양까지**, 여기는 **막는 법**부터
- 목록의 **38번 주제**(`slices`·`maps`·`cmp`) — `slices.Clone`·`Clip`·`Grow` 의 정본(**1.21**)
- 목록의 **43번 주제**(`io.Reader`/`Writer`) — 버퍼를 `copy` 로 채우는 패턴이 거기 쌓인다
- 목록의 **50번 주제**(벤치마크·`-benchmem`) — 「`copy` 가 비싼가」를 **재는** 자리
- [`../../../../memory-management/`](../../../../memory-management/) —
  **그쪽은 GC 가 어떻게 회수하는지(스택·힙·표시-쓸기)까지**,
  여기는 **무엇이 무엇을 붙잡는지**부터
- [`../../../../../data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/) —
  **그쪽은 동적 배열의 성장·상각까지**, 여기는 **Go 에서 공유를 끊는 표면**부터
- [`../../../rust/syntax/15-slices-ranges-and-utf8-boundaries/`](../../../rust/syntax/15-slices-ranges-and-utf8-boundaries/) —
  **그쪽은 `&[T]` 에서 `Vec` 으로 가는 공짜 길이 없어 `to_vec()` 이라는 복사뿐**,
  여기는 **`copy` 와 `s[a:b:c]` 두 길이 있다**
- [`../../../c/syntax/16-array-pointer-decay-and-function-parameters/`](../../../c/syntax/16-array-pointer-decay-and-function-parameters/) —
  **그쪽은 `memcpy` 와 길이를 손으로 들고 다녀야** 하고, 여기는 **`copy` 가 길이를 안다**

## 용어 풀이

- **`copy`** — 내장 함수. 짧은 쪽 `len` 만큼 베끼고 그 수를 돌려준다.
- **3-인덱스 슬라이싱(full slice expression)** — `a[low:high:max]`. `cap` 을 `max-low` 로 정한다.
- **메모리 유지(memory retention)** — 작은 슬라이스가 큰 기반 배열의 회수를 막는 것.
- **얕은 복사(shallow copy)** — 한 겹만 베끼는 것. Go 의 `copy`·`Clone` 이 그렇다.
- **`slices.Clip`** — `s[:len(s):len(s)]` 의 표준 이름. **같은 배열**이다(1.21).
- **`slices.Clone`** — 새 배열에 떠내는 것. **다른 배열**이다(1.21).
- **`clear`** — 내장 함수. 슬라이스를 `len` 까지 제로값으로 민다(1.21).
- **`HeapAlloc`** — `runtime.MemStats` 의 필드. 살아 있는 힙 객체의 바이트 수(런타임의 회계).

---

## 더 들어가면

- `append(dst[:0], src...)` 는 「`dst` 의 배열을 재사용해 `src` 를 담기」다.
  `copy` 와 달리 **모자라면 늘어난다.** 버퍼 재사용 패턴에서 자주 보인다.
- `slices.Grow(s, n)`(**1.21**)는 반대 방향이다 — **미리 늘려** 재할당을 없앤다. 정본은 목록의 **38번 주제**다.
- (5)절의 함정은 `strings`·`bytes` 에서도 난다. 큰 문자열을 슬라이싱해 조각을 보관하면
  **원본 문자열이 안 없어진다.** `strings.Clone`(**1.18**)이 그것을 끊는다.
  이 문서에서는 **문자열 쪽은 안 던져 봤다.**
- `runtime.ReadMemStats` 는 **stop-the-world** 를 한다. 측정 도구지 운영 도구가 아니다.
  제대로 된 메모리 조사는 `pprof` 의 힙 프로파일이다 — 정본은 목록의 **50번 주제**다.
- `clear` 는 맵에도 쓴다(`clear(m)` 은 모든 항목을 지운다). 슬라이스와 **뜻이 다르다** —
  맵은 **비우고**, 슬라이스는 **제로값으로 민다.** 정본은 [목록의 **09번 주제**](../09-maps-declaration-comma-ok-delete-and-iteration-order/)다.
- 「`copy` 가 `memmove` 로 내려가는가」는 **확인하지 않았다.**
  (9)절 같은 어셈블리 창으로 볼 수는 있지만 이 문서의 범위 밖이다.

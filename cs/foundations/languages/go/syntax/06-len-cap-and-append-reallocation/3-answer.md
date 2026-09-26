# go/syntax/06 — `len`/`cap`과 `append`의 재할당 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★★ **이 파일의 `cap` 수치는 전부 「이 판의 관찰」이다.** 명세는 `append` 가 얼마나 늘리는지
> 정하지 않는다. **수치를 외우지 말고 「누가 정하나」를 외워라.**
> ★ **근거로 읽을 칸** — `len`, 「재할당이 일어났나」, 에러·패닉 문장 본문, `파일:줄:칸`, 종료 코드.
> **근거로 읽지 않을 칸** — `cap` 의 **구체적 수치**, 기반 배열의 **주소 자체**,
> 패닉 스택의 `goroutine N` 번호와 `+0x…`.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 앞을 자르면 `cap` 도 줄고, 뒤를 자르면 `cap` 은 안 준다

**출력**

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

**왜 그런가**

| 식 | `len` | `cap` | 왜 |
|---|---|---|---|
| `arr [6]int` | 6 | **6** | 배열의 `cap` 은 언제나 `len` 과 같다 |
| `[]int{1,2,3}` | 3 | **3** | 리터럴은 딱 맞는 배열을 만든다 |
| `make([]int, 3)` | 3 | **3** | `cap` 을 안 주면 `len` 과 같다 |
| `make([]int, 3, 10)` | 3 | **10** | **여유는 명시해야 생긴다** |
| `var s []int` | 0 | **0** | `nil` 슬라이스 |
| `arr[:]` | 6 | 6 | 전부 |
| `arr[2:]` | 4 | **4** | **앞을 자르면 `cap` 도 준다**(`cap(arr)-2`) |
| `arr[:2]` | 2 | **6** | **뒤를 잘라도 `cap` 은 그대로다** |
| `arr[2:4]` | 2 | **4** | `cap` 은 `low` 만 본다 |
| `arr[2:4:5]` | 2 | **3** | 세 번째 숫자가 끝을 정한다(`5-2`) |
| `arr[6:]` | 0 | **0** | **패닉이 아니다** — `low == len` 은 유효한 경계다 |
| `s[:cap(s)]` | 4 | 4 | `len` 밖이 다시 보인다 |
| `s[1:]` | 1 | **3** | 또 한 칸 밀렸다 |

- `cap` 의 공식은 하나다 — **`cap(a) - low`**. 그래서 `high` 는 `cap` 에 영향이 없다.
- `arr[6:]` 이 패닉이 아닌 것이 경계다. 명세가 `0 <= low <= high <= cap(a)` 라고 적었고 `6 <= 6` 이다.
- ★ **판이 올라가도 이 열여섯 줄은 안 바뀐다.** 전부 명세가 정하는 값이다.
  이 주제에서 판에 달린 것은 **`append` 가 만든 `cap`** 뿐이다.

### 2. 한 번 — 그리고 미리 잡으면 **0번**

**출력**

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

**왜 그런가**

- `cap` 4로 시작해 **다섯째 `append` 에서** 기반 배열이 `A` → `B` 로 바뀐다. 재할당 **1회**.
- `cap` 8로 시작하면 여덟 번을 붙여도 **0회**다.
- **다섯째에서 `cap` 이 8이 된다** — 그런데 ★ **이 값은 자신 있게 말하면 안 된다.**
  명세는 "sufficiently large" 까지만 말한다. 5가 돼도 16이 돼도 명세 위반이 아니다.
  말할 수 있는 것은 「**새 배열이 잡힌다**」까지다.
- 이 프로그램이 `cap` 말고 따로 관찰하는 것은 **기반 배열의 동일성**이다.
  `cap` 만 보면 「4에서 8이 됐다」는 알지만 **그게 한 번에 된 것인지 두 번에 걸친 것인지 모른다.**
  이름표가 그 구멍을 메운다.
- ★ `make([]T, 0, n)` 의 값이 이 한 줄이다 — **이사 횟수가 0이 된다.**
  다만 **얼마나 빨라지는지는 이 문서에서 재지 않았다.** 잰 것은 횟수뿐이다.

### 3. **열두 번** 바뀌고, 512 에서 「배」가 깨진다

**출력**

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

**왜 그런가**

- `cap` 이 **열두 번** 바뀐다.
- 앞쪽은 **정확히 배**다 — `0 → 4 → 8 → 16 → 32 → 64 → 128 → 256 → 512`.
- ★★ **512 → 848 에서 배가 깨진다**(1.656배). 이어서 848 → 1280(1.509배),
  1280 → 1792(1.400배), 1792 → 2560(1.429배).
  **끝까지 같은 비율이 아니다** — 1.25배 같은 고정 비율도 아니다.
- 첫 줄은 `0 → 4` 다. **1이 아니다.**
- ★★★ 이 출력을 문서에 실을 때 반드시 같이 적어야 하는 문장은
  「**이 수치는 gc go1.27.1 의 관찰이고 명세는 `cap` 의 증가를 정하지 않는다**」이다.
  프로그램 자체가 그 줄을 먼저 찍게 해 둔 이유다.
- 「배로 늘리면 왜 상각 O(1)인가」는 여기가 아니라
  [`../../../../../data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/)가 정본이다.
  **이 문서는 시간을 재지 않았다.**

### 4. 내용은 같은데 `cap` 은 **8 · 6 · 6 · 5** 로 갈린다

**출력**

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

**왜 그런가**

| 만든 방법 | `len` | `cap` |
|---|---|---|
| 하나씩 다섯 번 `append` | 5 | **8** |
| 한 번에 다섯 개 `append` | 5 | **6** |
| 슬라이스를 통째로 `append` | 5 | **6** |
| `make([]int, 5)` | 5 | **5** |

- **내용은 같다**(`true`). **`cap` 은 다르다**(`false`).
- ★★ 이 결과가 뒤엎는 문장은 「**`append` 는 `cap` 을 두 배로 늘린다**」다.
  하나씩 붙인 쪽만 4 → 8 을 거쳤고, 한 번에 붙인 쪽은 **5개인데 6**이다. 배도 아니고 딱 맞지도 않다.
- ★ 그래서 `cap` 은 **값의 성질이 아니라 만들어진 경로의 흔적**이다.
  두 슬라이스의 `cap` 이 다르다고 해서 내용이 다른 것도, 같다고 해서 같은 것도 아니다.
- **`cap` 으로 판단해도 되는 것은 하나뿐**이다 — 「**다음 `append` 가 이사할 것인가**」.
  그것만 명세가 떠받쳐 준다.

### 5. 여섯 줄 전부 예측과 실제가 맞는다

**출력**

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

**왜 그런가**

| 경우 | `len` | `cap` | 붙일 개수 | 예측(제자리) | 실제(같은 배열) |
|---|---|---|---|---|---|
| `make(3,6)` + 1 | 3 | 6 | 1 | true | **true** |
| `make(3,6)` + 3 | 3 | 6 | 3 | true | **true** |
| `make(3,6)` + 4 | 3 | 6 | 4 | false | **false** |
| `make(3,3)` + 1 | 3 | 3 | 1 | false | **false** |
| `[]int{1,2,3}` + 0 | 3 | 3 | 0 | true | **true** |
| `nil` + 1 | 0 | 0 | 1 | false | **false** |

- 예측식은 **`len(s) + 붙일 개수 <= cap(s)`** 다.
- ★ 그 식이 맞는 근거는 **명세**다 — 명세가 갈림을 `cap` 으로 정의했다.
  (관찰로 확인한 것이지 관찰에서 유도한 것이 아니다.)

  > If the capacity of `s` is not large enough to fit the additional values …
  > Otherwise, `append` **re-uses the underlying array**.

- 마지막 줄의 결과 `cap` 은 **1**이다. 그런데 `var n []int; n = append(n, 1)` 로 붙이면 **4**다((6)절).
  ★ **같은 「한 개 붙이기」인데 호출 꼴이 다르면 수치가 다르다** —
  `append(s, add...)` 와 `append(s, 9)` 가 다른 길로 간다는 뜻이고, 이것도 **구현**이다.
- `[]int{1,2,3}` 에 **0개**를 붙이면 `len`·`cap` 이 그대로고 **같은 배열**을 돌려준다.
  즉 `append(s)` 는 **복사가 아니다.** 「빈 `append` 로 복사하기」는 안 된다.

### 6. 네 줄 전부 에러다

**출력**

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

**왜 그런가**

- **`append(s, 1)` 을 문장으로 쓰면 에러**다 — `append(s, 1) (value of type []int) is not used`.
  Go 는 값을 만들어 놓고 버리는 표현식을 **문장으로 인정하지 않는다.**
  그래서 이 실수는 **컴파일 타임에 잡힌다.**
- **배열에 `append` 못 한다** — `invalid append: argument must be a slice; have arr (variable of type [3]int)`.
- **`make([]int, 5, 3)`** — `invalid argument: length and capacity swapped`.
  ★ **둘 다 상수일 때만 잡힌다.** 명세: "If both `n` and `m` are provided and are constant,
  then `n` must be no larger than `m`." 변수였다면 **런타임 패닉**이다.
- 원소 타입이 안 맞는 것은 보통의 타입 에러다.
- ★ **05번 주제의 「함수 안 `append` 가 안 보이는」 사고와 성격이 같은 것은 이 중에 없다.**
  그쪽은 **결과를 받긴 받았는데 호출자에게 안 간 것**이라 컴파일러가 볼 수 없다.
  여기 넷은 전부 **타입·문장 규칙 위반**이라 잡힌다. **잡히는 실수와 안 잡히는 실수는 다른 부류다.**

### 7. 헤더를 못 바꾸니 새 헤더를 돌려주는 수밖에 없다

**출력** — 없음(왜 문항).

**왜 그런가**

- `append` 가 고쳐야 하는 것은 **슬라이스 헤더의 `len`(때로는 포인터와 `cap` 까지)** 이다.
  그런데 Go 에서 함수는 **인자의 복사본**을 받는다(05번 주제 (3)절).
  그래서 `append` 가 무엇을 하든 **호출자의 헤더는 못 바꾼다.**
- 방법은 둘뿐이었다 — **포인터를 받거나**(`func push(s *[]int, x int)`),
  **새 헤더를 돌려주거나**. Go 는 뒤엣것을 골랐다.
- 명세가 그 선택을 한 줄로 적는다.

  > The variadic function `append` appends zero or more values `x` to a slice `s` …
  > and **returns the resulting slice**, also of type `S`.

- 결과를 안 받으면 **컴파일 타임 에러**다(6번 문항). 런타임까지 안 간다.
- 매개변수로 받은 슬라이스에 붙인 결과를 호출자에게 주려면 — **반환한다**(`func add(s []int) []int`)
  또는 **`*[]int` 를 받는다.** Go 표준 라이브러리는 거의 전부 앞엣것이다.

### 8. `make([]int, 3)` 을 찍고 **`makeslice: len out of range`** 로 죽는다 — 종료 코드 2

**출력**

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

**왜 그런가**

- 정상인 줄은 찍히고, 마커 줄(표준 오류)이 나온 뒤 **패닉**이다 —
  위 블록의 `panic:` 줄이 그것이고, 종료 코드는 **2**다.
- 명세: "For slices and channels, if `n` is negative or larger than the maximum allowed value,
  **a run-time panic occurs**."
- **`bad` 를 상수 `-1` 로 바꾸면 컴파일 에러**가 된다. 명세: "A constant size argument
  **must be non-negative** and representable by a value of type `int`."
- `make([]int, 5, 3)` 은 **둘 다 상수라 컴파일 에러** 쪽이다(6번 문항).
- ★ 이 갈림은 [03번 주제](../03-constants-iota-and-untyped-constants/)·[04번 주제](../04-numeric-types-conversions-and-integer-division/)에서
  본 것과 **같은 모양**이다 — **값이 컴파일 타임에 보이면 거부하고, 런타임에만 보이면 패닉**한다.
  Go 전체를 관통하는 규칙이다.

### 9. 구현은 **③ 과 ⑤ 둘**이다

**출력** — 없음(경계 문항).

**왜 그런가**

| | 주장 | 판정 | 근거 |
|---|---|---|---|
| ① | `0 <= len(s) <= cap(s)` | **명세 보장** | "At any time the following relationship holds" |
| ② | 모자라면 새 배열 | **명세 보장** | "allocates a new, sufficiently large underlying array" |
| ③ | 512 다음이 848 | **구현(gc)** | 명세의 낱말은 "sufficiently large" 뿐이다 |
| ④ | `append` 가 결과를 돌려준다 | **명세 보장** | "returns the resulting slice" |
| ⑤ | 호출 꼴에 따라 `cap` 이 4와 1로 갈린다 | **구현(gc)** | 명세는 두 꼴을 구별하지 않는다 |
| ⑥ | 음수 `make` 가 런타임 패닉 | **명세 보장** | "a run-time panic occurs" |

- ★ 갈라 보면 **「무슨 일이 일어나나」는 전부 명세**고 **「얼마나」는 전부 구현**이다.
  이 주제의 한 줄 요약이 그것이다.

### 10. 다른 언어·다른 갈래와 나란히 놓기

**출력** — 없음(연결 문항).

**왜 그런가**

| 물음 | **Rust** | **파이썬** | **Go** |
|---|---|---|---|
| 슬라이스에 `cap` 이 있나 | **없다** — `&[T]` 는 ptr + len 두 칸 | (리스트가 내부에 들고 있다) | **있다** — 헤더의 셋째 칸 |
| 길이를 늘리는 일은 누구의 것 | **`Vec<T>`** 의 일(`push`) | 리스트의 `append`·슬라이스 대입 | **슬라이스 자신**(`append`) |
| 늘린 결과를 어떻게 받나 | 제자리에서 바뀐다 | 제자리에서 바뀐다 | **돌려받는다**(`s = append(s, x)`) |
| 원본이 공유되나 | 슬라이스는 창이지만 **못 늘린다** | 슬라이스가 **복사**라 문제가 없다 | **공유되고 늘어난다** — 그래서 07번 주제가 있다 |

- Rust 쪽 근거는 [`../../../rust/syntax/15-slices-ranges-and-utf8-boundaries/`](../../../rust/syntax/15-slices-ranges-and-utf8-boundaries/) —
  「`&mut [T]` 로는 길이를 못 바꾼다. `push`·`remove` 는 `Vec` 의 것이다」.
- 파이썬 쪽은 [`../../../python/syntax/09-sequence-ops-and-slicing/`](../../../python/syntax/09-sequence-ops-and-slicing/) 4절 —
  `a[1:3] = ['X']` 가 길이를 5에서 4로 바꾼다.
- ★ **Go 만 「공유되는 창」과 「자라는 것」을 한 타입에 넣었다.** 편한 대신 07번 주제의 버그가 생긴다.
  세 언어가 같은 문제를 **다른 방식으로 피했다**고 읽으면 셋이 한 줄에 놓인다.
- **「배로 늘리면 왜 상각 O(1)인가」** 의 정본은 [`../../../../../data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/) 다.
- **「미리 잡으면 빠르다」** 를 주장하려면 **벤치마크**가 필요하다 — 정본은 목록의 **50번 주제**다.
  이 문서가 잰 것은 **재할당 횟수**까지다.

### 11. 다른 주제와 잇기

**출력** — 없음(연결 문항).

**왜 그런가**

- **「이사하면 공유가 끊긴다」** — [목록의 **05번 주제**](../05-arrays-vs-slices-value-and-header/) (4)절.
- **「이사하지 않아서 이웃이 덮인다」가 버그가 되는 사례** — [목록의 **07번 주제**](../07-slice-sharing-silent-bugs/).
  이 주제 (2)절의 **두 번째 약속**만 파고든 주제다.
- **이사를 일부러 강제하는 법** — [목록의 **08번 주제**](../08-copy-three-index-slicing-and-memory-retention/)(`s[a:b:c]`·`copy`).
- **`slices.Grow`·`slices.Clip`** — 목록의 **38번 주제**. 둘 다 **1.21**부터다.
- **가변 인자 `x...`** — [목록의 **12번 주제**](../12-functions-multiple-returns-named-results-and-variadics/).
- **벤치마크로 수치를 주장하는 법** — 목록의 **50번 주제**.

---

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행 1회** | 재실행 결과가 `diff -rq` 로 **동일** |
| 판 확인 | `go version` · `go env GOOS GOARCH GOVERSION` | 1 | `go1.27.1 linux/amd64` |
| `len`·`cap` 열여섯 줄 (`t06a`) | `go build && ./prog` | 1 | 앞을 자르면 `cap` 감소 · 뒤는 유지 · `arr[6:]` 은 빈 것 |
| 재할당 횟수 (`t06c`) | 〃 | 1 | `cap` 4 → **1회** · `cap` 8 → **0회** |
| ★ 성장 관찰 (`t06b`) | 〃 | 1 | 열두 번 변화 · **512 → 848 에서 배가 깨짐** |
| 경로가 `cap` 을 바꾼다 (`t06e`) | 〃 | 1 | 내용 같고 `cap` 은 **8·6·6·5** |
| 예측 대 실제 (`t06g`) | 〃 | 1 | **여섯 경우 전부 일치** |
| `append` 의 여러 형태 (`t06f`) | 〃 | 1 | `"bar"...` 됨 · `append(z)` 만 하면 여전히 `nil` |
| 컴파일 에러 (`t06d`) | `go build` | 1 | **네 줄** |
| `make` 런타임 패닉 (`t06h`) | `go build` · `./prog 2>&1` | 1 | `makeslice: len out of range` · **exit 2** |
| 형태 (`t06form`) | `go build && ./prog` | 1 | `[1 2 3 1 2 3] 6 8 hi true` |

**구현 의존 항목**(판이 오르면 **다시 찍어야 하는** 것)

| 항목 | 왜 |
|---|---|
| **`cap` 의 모든 수치**(4·8·…·848·1280·1792·2560 · 8·6·6·5 · 12 · 1) | **gc 의 성장 전략**. 명세는 "sufficiently large" 까지만 말한다 |
| **`cap` 이 열두 번 바뀌는 것**(횟수 자체) | 같은 이유. 성장 전략이 바뀌면 횟수도 바뀐다 |
| **512 라는 임계값** | 〃. 임계값이 있다는 사실도 명세에 없다 |
| `append(n, 1)` 과 `append(n, add...)` 가 갈리는 것 | 〃. 명세는 두 꼴을 구별하지 않는다 |
| `[]byte` 에 3바이트 붙였더니 `cap` 8 | 〃 + 원소 크기에 따른 메모리 단위 |
| 기반 배열의 **주소 자체** | 실행마다 다르다. 그래서 `A`·`B` 이름표로만 찍었다 |
| 패닉 스택의 `goroutine 1 [running]` 과 `+0x…` | 런타임·빌드 산출물 |
| **「미리 잡으면 빠르다」** | **안 쟀다.** 잰 것은 재할당 **횟수**까지다(목록의 **50번 주제**) |
| `make` 의 크기 상한 | **안 던져 봤다.** 상한 자체는 구현에 달렸다 |
| 848·1280·1792 가 메모리 크기 단위 반올림인지 | **소스를 읽어 확인하지 않았다.** 관찰만 실었다 |

★ **다시 찍는 법** — `capture.sh` 를 그대로 돌리고 `diff -rq` 한다.
`cap` 수치가 움직였다면 **그 사실 자체가 이 주제의 결론**이므로 본문을 고치기 전에 기록한다.

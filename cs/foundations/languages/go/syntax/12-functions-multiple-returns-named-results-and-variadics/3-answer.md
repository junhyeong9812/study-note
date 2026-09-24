# go/syntax/12 — 함수: 다중 반환·명명 반환값·가변 인자 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★★★ **이 파일의 답은 거의 전부 「함수가 끝나는 두 단계」로 환원된다** —
> ① `return` 이 결과 파라미터에 대입하고 ② `defer` 가 그 칸을 고친다.
> ★ **근거로 읽을 칸** — 출력의 **값과 순서** · `len`/`cap`/`nil` 여부 ·
> 컴파일 에러 **문장 본문**과 `파일:줄:칸` · 패닉 메시지 본문 · 종료 코드 · `go vet` 의 종료 코드.
> **근거로 읽지 않을 칸** — 패닉 스택의 **주소 오프셋**(`+0x90`)과 **`pc=0x…`** ·
> 컴파일 에러의 **정확한 문구**(컴파일러가 다듬을 수 있다).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. **42 · 21 · 101 · "가" "나" · 시작③②①**

**출력**

```text
===== 소스: t12d.go =====
package main

import "fmt"

// named 는 반환값에 이름이 있다 — defer 가 그 변수를 고칠 수 있다.
func named() (n int) {
	defer func() { n *= 2 }()
	n = 21
	return n
}

// unnamed 는 이름이 없다 — defer 가 고칠 대상이 없다.
func unnamed() int {
	n := 21
	defer func() { n *= 2 }()
	return n
}

// returnsLiteral 은 return 이 리터럴이다 — return 이 먼저 n 에 넣고 defer 가 그 뒤에 돈다.
func returnsLiteral() (n int) {
	defer func() { n++ }()
	return 100
}

// naked 는 벌거벗은 return 이다 — 이름만 적고 값을 안 적는다.
func naked() (a, b string) {
	a, b = "가", "나"
	return
}

// order 는 defer 가 LIFO 로 돌면서 같은 반환값을 차례로 고치는 것을 보인다.
func order() (s string) {
	defer func() { s += "①" }()
	defer func() { s += "②" }()
	defer func() { s += "③" }()
	return "시작"
}

func main() {
	fmt.Println("named()          =", named())
	fmt.Println("unnamed()        =", unnamed())
	fmt.Println("returnsLiteral() =", returnsLiteral())
	a, b := naked()
	fmt.Printf("naked()          = %q %q\n", a, b)
	fmt.Println("order()          =", order())
}
===== 명령: go build -trimpath -o prog . && ./prog =====
named()          = 42
unnamed()        = 21
returnsLiteral() = 101
naked()          = "가" "나"
order()          = 시작③②①
(exit 0)
```

**왜 그런가**

| 함수 | 결과 | 왜 |
|---|---|---|
| `named()` | **42** | `return n` 이 결과 파라미터 `n` 에 21을 넣고, `defer` 가 그 `n` 을 2배로 |
| `unnamed()` | **21** | 이름이 없어 `defer` 가 **지역 변수**를 고쳤다. 반환값은 이미 복사돼 나갔다 |
| `returnsLiteral()` | **101** | `return 100` 이 `n` 에 100을 넣고, `defer` 가 `n++` |
| `naked()` | **"가" "나"** | 벌거벗은 `return` — 이름만 있으면 값을 안 적어도 된다 |
| `order()` | **시작③②①** | `defer` 가 **LIFO** 로 돌며 같은 반환값을 차례로 고쳤다 |

- 갈리는 이유 한 낱말 — **이름**이다. 결과 파라미터에 이름이 있어야 `defer` 가 손댈 칸이 생긴다.
- ★★★ `returnsLiteral()` 이 101인 것이 **이 주제의 심장**이다.
  `return 100` 은 「100을 가지고 나간다」가 아니라 「**`n` 에 100을 넣고 나가기 시작한다**」이다.
  명세가 그 순서를 못 박는다.

  > **A "return" statement that specifies results sets the result parameters
  > before any deferred functions are executed.**

- `order()` 는 `defer` 순서도 같은 문장 근처에서 정해진다.

  > **deferred functions are invoked immediately before the surrounding function returns,
  > in the reverse order they were deferred.**

  ③을 마지막에 적었으니 ③이 먼저 붙고, 그다음 ②, 그다음 ① 이다.
- ★ 결과 파라미터는 **함수에 들어올 때 제로값으로 초기화**된다 —
  "**all the result values are initialized to the zero values for their type upon entry to the function.**"
  그래서 벌거벗은 `return` 이 안전하다.

### 2. 이름이 있는 쪽만 **감싸진다**

**출력**

```text
===== 소스: t12e.go =====
package main

import (
	"errors"
	"fmt"
)

var errNotFound = errors.New("없음")

// load 는 defer 로 오류를 감싼다 — 명명 반환값이라야 되는 관용구다.
func load(id string) (v string, err error) {
	defer func() {
		if err != nil {
			err = fmt.Errorf("load(%q): %w", id, err)
		}
	}()
	if id == "" {
		return "", errNotFound
	}
	return "값:" + id, nil
}

// loadBroken 은 같은 뜻으로 썼지만 반환값에 이름이 없다.
func loadBroken(id string) (string, error) {
	var err error
	defer func() {
		if err != nil {
			err = fmt.Errorf("loadBroken(%q): %w", id, err)
		}
	}()
	if id == "" {
		err = errNotFound
		return "", err
	}
	return "값:" + id, nil
}

// recovered 는 패닉을 오류로 바꾼다 — 이것도 명명 반환값이 있어야 된다.
func recovered() (err error) {
	defer func() {
		if r := recover(); r != nil {
			err = fmt.Errorf("패닉을 오류로 바꿨다: %v", r)
		}
	}()
	panic("터짐")
}

func main() {
	v, err := load("7")
	fmt.Printf("load(\"7\")        = %q, %v\n", v, err)
	v, err = load("")
	fmt.Printf("load(\"\")         = %q, %v\n", v, err)
	fmt.Printf("  errors.Is(err, errNotFound) = %v\n", errors.Is(err, errNotFound))

	_, err = loadBroken("")
	fmt.Printf("loadBroken(\"\")   = err = %v   ← 감싸기가 안 먹었다\n", err)

	fmt.Printf("recovered()      = %v\n", recovered())
}
===== 명령: go build -trimpath -o prog . && ./prog =====
load("7")        = "값:7", <nil>
load("")         = "", load(""): 없음
  errors.Is(err, errNotFound) = true
loadBroken("")   = err = 없음   ← 감싸기가 안 먹었다
recovered()      = 패닉을 오류로 바꿨다: 터짐
(exit 0)
```

**왜 그런가**

- `load("7")` → `"값:7", <nil>` · `load("")` → `"", load(""): 없음` ·
  `errors.Is(err, errNotFound)` 가 **true**(`%w` 로 감쌌으니 안쪽까지 본다) ·
  `loadBroken("")` → **`없음`**(감싸이지 않았다) · `recovered()` → `패닉을 오류로 바꿨다: 터짐`.
- ★★★ `loadBroken` 이 **컴파일되고 `go vet` 도 조용하다.** 오류도 제대로 나간다 —
  **맥락만 조용히 사라진다.** 로그를 읽기 전에는 모른다. **조용한 실패**다.
- 갈리는 이유 — `load` 는 `(v string, err error)` 로 **결과 파라미터에 이름**이 있고,
  `loadBroken` 은 `(string, error)` 라 `defer` 가 고친 것이 **지역 변수 `err`** 이다.
- `recovered()` 가 되는 이유 — **패닉으로 나가는 경로에는 `return` 문이 아예 없다.**
  그래서 결과 파라미터에 값을 넣을 기회가 **`defer` 안뿐**이고, 그러려면 **이름이 있어야** 한다.
  ★ `recover` 자체의 정본은 목록의 **27번 주제**다.
- ★ `load` 가 값진 이유는 **반환 경로가 여럿이어도 한 곳에서 잡는다**는 것이다.
  `return` 이 열 군데여도 `defer` 는 하나면 된다.

### 3. **42 · (안내) · ②는 42 · ①은 0**

**출력**

```text
===== 소스: t12f.go =====
package main

import "fmt"

func main() {
	i := 0
	defer fmt.Println("① defer fmt.Println(i)  — 인자는 defer 를 적은 그 순간 평가된다 : i =", i)
	defer func() { fmt.Println("② defer func(){ ... }() — 몸통은 나중에 돈다 : i =", i) }()

	i = 42
	fmt.Println("본문 끝. 지금 i =", i)
	fmt.Println("아래 두 줄은 LIFO 다 — 나중에 적은 ② 가 먼저 돈다")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
본문 끝. 지금 i = 42
아래 두 줄은 LIFO 다 — 나중에 적은 ② 가 먼저 돈다
② defer func(){ ... }() — 몸통은 나중에 돈다 : i = 42
① defer fmt.Println(i)  — 인자는 defer 를 적은 그 순간 평가된다 : i = 0
(exit 0)
```

**왜 그런가**

- 순서는 이렇다 — 본문 두 줄이 먼저, 그다음 **②**(나중에 적은 것), 그다음 **①**.
- ①이 **0**인 이유 — `defer fmt.Println(…, i)` 는 **인자를 지금 평가해 저장**한다.

  > **Each time a "defer" statement executes, the function value and parameters to the call
  > are evaluated as usual and saved anew but the actual function is not invoked.**

- ②가 **42**인 이유 — 클로저는 **변수 `i` 자체를 잡고** 나중에 읽는다.
  값이 아니라 변수를 잡는 것이 클로저의 성질이다(목록의 **13번 주제**).
- 고르는 기준 한 줄 — ★★ **「지금 값을 찍고 싶은가, 나갈 때 값을 찍고 싶은가」**.
- `defer file.Close()` 뒤에 `file` 을 바꾸면 — **처음 잡아 둔 파일이 닫힌다.**
  메서드 값의 리시버도 **인자와 같이 지금 평가**되기 때문이다.
  ★ 이것이 루프 안에서 `defer` 를 쓸 때의 사고와 이어진다(목록의 **26번 주제**).

### 4. `nil` 은 **세 번**이다 — 그리고 `s...` 는 **복사가 아니다**

**출력**

```text
===== 소스: t12g.go =====
package main

import "fmt"

func sum(label string, nums ...int) int {
	total := 0
	for _, n := range nums {
		total += n
	}
	fmt.Printf("  %-24s nums=%-12s len=%d cap=%d nil인가=%-6v 합=%d\n",
		label, fmt.Sprint(nums), len(nums), cap(nums), nums == nil, total)
	return total
}

func mutate(nums ...int) {
	if len(nums) > 0 {
		nums[0] = 99
	}
}

func main() {
	fmt.Println("가변 인자는 함수 안에서 그냥 슬라이스다")
	sum(`sum(l)`)
	sum(`sum(l, 1)`, 1)
	sum(`sum(l, 1, 2, 3)`, 1, 2, 3)

	s := []int{4, 5, 6}
	sum(`sum(l, s...)`, s...)

	var nilSlice []int
	sum(`sum(l, nilSlice...)`, nilSlice...)
	sum(`sum(l, []int{}...)`, []int{}...)

	fmt.Println()
	fmt.Println("★ ... 로 펼쳐 넘긴 슬라이스는 복사되지 않는다 — 같은 배열이다")
	fmt.Println("  넘기기 전 s =", s)
	mutate(s...)
	fmt.Println("  mutate(s...) 뒤 s =", s)
	fmt.Println("  하나씩 넘기면 새 배열이 생긴다")
	t := []int{4, 5, 6}
	mutate(t[0], t[1], t[2])
	fmt.Println("  mutate(t[0], t[1], t[2]) 뒤 t =", t)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
가변 인자는 함수 안에서 그냥 슬라이스다
  sum(l)                   nums=[]           len=0 cap=0 nil인가=true   합=0
  sum(l, 1)                nums=[1]          len=1 cap=1 nil인가=false  합=1
  sum(l, 1, 2, 3)          nums=[1 2 3]      len=3 cap=3 nil인가=false  합=6
  sum(l, s...)             nums=[4 5 6]      len=3 cap=3 nil인가=false  합=15
  sum(l, nilSlice...)      nums=[]           len=0 cap=0 nil인가=true   합=0
  sum(l, []int{}...)       nums=[]           len=0 cap=0 nil인가=false  합=0

★ ... 로 펼쳐 넘긴 슬라이스는 복사되지 않는다 — 같은 배열이다
  넘기기 전 s = [4 5 6]
  mutate(s...) 뒤 s = [99 5 6]
  하나씩 넘기면 새 배열이 생긴다
  mutate(t[0], t[1], t[2]) 뒤 t = [4 5 6]
(exit 0)
```

**왜 그런가**

| 호출 | `len` | `cap` | `nil` 인가 |
|---|---|---|---|
| `sum(l)` | 0 | 0 | ★ **true** |
| `sum(l, 1)` | 1 | 1 | false |
| `sum(l, 1, 2, 3)` | 3 | 3 | false |
| `sum(l, s...)` | 3 | 3 | false |
| `sum(l, nilSlice...)` | 0 | 0 | ★ **true** |
| `sum(l, []int{}...)` | 0 | 0 | ★ **false** |

- 뒤의 둘이 갈리는 이유 — **펼쳐 넘긴 슬라이스가 그대로 파라미터가 된다.**
  `nilSlice` 는 `nil` 이라 `nil` 이 그대로 들어가고, `[]int{}` 는 **길이 0인 진짜 슬라이스**라 `nil` 이 아니다.
  `len` 으로는 둘이 구별되지 않는다 — **`== nil` 로만 갈린다.**
- ★★★ `mutate(s...)` 뒤 `s` 가 **`[99 5 6]`** 이다. **복사가 없기 때문**이다.
  함수 안의 `nums` 와 바깥의 `s` 가 **같은 배열**을 본다.
- 하나씩 넘긴 쪽(`mutate(t[0], t[1], t[2])`)은 **호출부가 새 배열을 만들어** 넘기므로 원본이 그대로다.
- ★★ **코틀린은 정반대다.** 형제 문서 실측에 따르면 코틀린의 spread(`*`)는
  **`java.util.Arrays.copyOf` 로 복사를 만들어** 호출자의 배열이 안 바뀐다
  ([`../../../kotlin/syntax/09-varargs-spread-local-and-infix-functions/`](../../../kotlin/syntax/09-varargs-spread-local-and-infix-functions/)).
  **같은 모양의 문법 기호가 반대 결과**를 낸다 — 옮겨 온 직관이 Go 에서 조용히 틀린다.
- ★ 이것은 07번 주제(슬라이스 공유)의 한 사례다. 막으려면 **`append([]int(nil), s...)`** 로 복사해 넘긴다.

### 5. **1개와 0개** — 그리고 `[]string` 은 **컴파일 에러**다

**출력**

```text
===== 소스: t12h.go =====
package main

import "fmt"

func count(label string, args ...any) {
	fmt.Printf("  %-34s len=%d  nil인가=%-6v  args=%v\n", label, len(args), args == nil, args)
}

func main() {
	fmt.Println("nil 을 「하나」 넘기는 것과 nil 슬라이스를 「펼쳐」 넘기는 것은 다르다")
	count(`count(l, nil)`, nil)
	var s []any
	count(`count(l, s...) — s 는 nil 슬라이스`, s...)
	count(`count(l)`)

	fmt.Println()
	fmt.Println("[]string 은 ...any 로 못 펼친다 — 하나씩 옮겨야 한다")
	words := []string{"가", "나"}
	as := make([]any, len(words))
	for i, w := range words {
		as[i] = w
	}
	count(`count(l, as...)`, as...)
	fmt.Printf("  fmt.Sprintln(as...) = %q\n", fmt.Sprintln(as...))
}
===== 명령: go build -trimpath -o prog . && ./prog =====
nil 을 「하나」 넘기는 것과 nil 슬라이스를 「펼쳐」 넘기는 것은 다르다
  count(l, nil)                      len=1  nil인가=false   args=[<nil>]
  count(l, s...) — s 는 nil 슬라이스      len=0  nil인가=true    args=[]
  count(l)                           len=0  nil인가=true    args=[]

[]string 은 ...any 로 못 펼친다 — 하나씩 옮겨야 한다
  count(l, as...)                    len=2  nil인가=false   args=[가 나]
  fmt.Sprintln(as...) = "가 나\n"
(exit 0)
```

```text
===== 소스: t12i.go =====
package main

import "fmt"

func count(args ...any) int { return len(args) }

func main() {
	words := []string{"가", "나"}
	fmt.Println(count(words...))
	fmt.Println(count(words, "다"...))
}
===== 명령: go build -trimpath -o prog . =====
# ex
./t12i.go:9:20: cannot use words (variable of type []string) as []any value in argument to count
./t12i.go:10:27: too many arguments in call to count
	have ([]string, string...)
	want (...any)
(exit 1)
```

**왜 그런가**

| 호출 | `len` | `args == nil` |
|---|---|---|
| `count(l, nil)` | **1** | false — `args` 는 `[<nil>]` 이다 |
| `count(l, s...)`(s 는 nil 슬라이스) | **0** | **true** |
| `count(l)` | **0** | **true** |

- ★★ `count(nil)` 은 **`nil` 이라는 값 하나**를 넘긴 것이다. 「아무것도 안 넘김」이 아니다.
  `fmt.Println(nil)` 이 `<nil>` 을 찍는 것이 같은 이유다.
- `[]string` 을 `...any` 로 펼치면 —
  `cannot use words (variable of type []string) as []any value in argument to count`.
  두 번째 줄은 `too many arguments in call to count` 와 함께
  **`have ([]string, string...)`** / **`want (...any)`** 를 보여 준다.
- ★ **메모리 배치가 다르다.** `[]string` 의 원소는 **문자열 헤더(포인터+길이) 두 칸**이고,
  `[]any` 의 원소는 **(타입, 값) 두 칸**이다. 같은 바이트를 다르게 읽는 것이 아니라 **내용이 다르다.**
  변환하려면 **원소마다 감싸야** 하고 그것은 `O(n)` 이라 **언어가 몰래 해 주지 않는다.**
- 고치는 법 — `[]any` 를 만들어 **하나씩 옮긴다.** 실측 코드가 그 모양이다.

### 6. 다중 반환은 **통째로만** 넘길 수 있다 — 튜플이 아니다

**출력**

```text
===== 소스: t12b.go =====
package main

import "fmt"

func two() (int, int) { return 1, 2 }

func add(a, b int) int { return a + b }

func main() {
	fmt.Println("다중 반환을 통째로 넘길 수 있다 — 단 그것만 인자로 줄 때다")
	fmt.Println("  add(two())   =", add(two()))
	fmt.Print("  fmt.Println(two()) -> ")
	fmt.Println(two())
}
===== 명령: go build -trimpath -o prog . && ./prog =====
다중 반환을 통째로 넘길 수 있다 — 단 그것만 인자로 줄 때다
  add(two())   = 3
  fmt.Println(two()) -> 1 2
(exit 0)
```

```text
===== 소스: t12c.go =====
package main

import "fmt"

func two() (int, int) { return 1, 2 }

func add(a, b int) int { return a + b }

func main() {
	fmt.Println(add(two(), 3))
	x := two()
	fmt.Println(x)
}
===== 명령: go build -trimpath -o prog . =====
# ex
./t12c.go:10:18: multiple-value two() (value of type (int, int)) in single-value context
./t12c.go:11:7: assignment mismatch: 1 variable but two returns 2 values
(exit 1)
```

**왜 그런가**

- `add(two())` 가 **3**, `fmt.Println(two())` 가 **`1 2`** 다. 명세가 허용한다.

  > **The expression list in the "return" statement may be a single call to a multi-valued function.
  > The effect is as if each value returned from that function were assigned to a temporary variable**

- 섞으면 안 된다.
  - `add(two(), 3)` → **`multiple-value two() (value of type (int, int)) in single-value context`**
  - `x := two()` → **`assignment mismatch: 1 variable but two returns 2 values`**
- ★ **메시지가 다른 이유** — 앞은 **식의 자리** 문제다(단일 값이 와야 하는 곳에 다중 값이 왔다).
  뒤는 **대입의 개수** 문제다(왼쪽 1개, 오른쪽 2개).
- ★★★ **다중 반환은 튜플이 아니다.** 근거 셋.
  - ① **변수에 못 담는다** — `x := two()` 가 에러다.
  - ② **타입이 없다** — `(int, int)` 라는 타입을 선언할 수 없다.
  - ③ **컬렉션에 못 넣는다** — `[]…` 의 원소가 될 수 없다.
  오직 **`return` 문과 호출 자리에서만** 존재하는 **문법적 장치**다.
  파이썬이 튜플이라는 **값**을 돌려주는 것과 근본이 다르다.

### 7. `return` 이 **대입**이기 때문이다

**출력** — 없음(왜 문항).

**왜 그런가**

- 함수가 끝나는 두 단계.
  - ① **`return v` 가 결과 파라미터에 `v` 를 대입한다.**
  - ② **`defer` 들이 역순으로 돈다.** 그 뒤에야 ③ 호출자에게 값이 간다.
- ★★ 그 사이에 `defer` 가 끼는 것이 유용한 자리 둘.
  - **오류 감싸기** — `return` 이 열 군데여도 **한 곳에서** 맥락을 붙인다(2번 문항의 `load`).
  - **패닉을 오류로** — 패닉 경로에는 `return` 이 없으므로 **여기서만** 값을 정할 수 있다.
- 반환값에 이름이 없으면 — `defer` 가 고치는 것은 **지역 변수**다.
  결과 파라미터는 이미 복사돼 나가서 손댈 방법이 없다.
- ★★★ 이 설계의 **위험**은 **`return` 문만 읽어서는 무엇이 나가는지 알 수 없다**는 것이다.
  `return 100` 이 101을 내보낼 수 있다. **함수의 `defer` 를 전부 읽어야** 반환값을 안다.
  긴 함수에서 명명 반환값을 남용하면 그 비용이 커진다.

### 8. **`<nil>`** 이 나가고, `go vet` 은 **종료 코드 0** 이다

**출력**

```text
===== 소스: t12l.go =====
package main

import (
	"errors"
	"fmt"
)

// shadow 는 명명 반환값 err 을 := 로 가려 버린다.
func shadow() (err error) {
	if true {
		err := errors.New("안쪽에서 만든 err")
		_ = err
	}
	return
}

// fixed 는 = 로 대입한다.
func fixed() (err error) {
	if true {
		err = errors.New("바깥 err 에 대입했다")
	}
	return
}

func main() {
	fmt.Printf("shadow() = %v   ← 에러도 경고도 없이 nil 이다\n", shadow())
	fmt.Printf("fixed()  = %v\n", fixed())
}
===== 명령: go build -trimpath -o prog . && ./prog =====
shadow() = <nil>   ← 에러도 경고도 없이 nil 이다
fixed()  = 바깥 err 에 대입했다
(exit 0)
===== 명령: go vet ./... =====
(exit 0)
```

**왜 그런가**

- `shadow()` 가 **`<nil>`**, `fixed()` 가 `바깥 err 에 대입했다` 다.
- `shadow` 안의 `err := errors.New(…)` 는 **새 변수를 만든다.** 바깥의 결과 파라미터 `err` 은
  손도 안 댔으므로 **제로값(`nil`)** 그대로 나간다.
- ★★ **`go vet` 의 종료 코드가 0** 이다. 기본 vet 에는 섀도잉 검사가 **없다**
  (`shadow` 분석기는 따로 켜야 한다).
- 명세가 컴파일러에게 허락한 것은 **의무가 아니라 재량**이다.

  > **Implementation restriction: A compiler *may* disallow an empty expression list in a "return"
  > statement if a different entity … with the same name as a result parameter is in scope
  > at the place of the return.**

  ★ 「**may**」이고, 게다가 **벌거벗은 `return` 에 한정**된 이야기다.
  이 프로그램은 벌거벗은 `return` 을 쓰는데도 gc 는 **거부하지 않았다.**
- 규칙 — ★ **명명 반환값의 이름을 `:=` 의 왼쪽에 두지 않는다.**
  꼭 필요하면 안쪽 변수의 이름을 다르게 짓는다.

### 9. 명세는 ①②③④⑤⑥, 구현·도구의 사정은 ⑦⑧

**출력** — 없음(경계 문항).

**왜 그런가**

| | 주장 | 판정 | 근거 |
|---|---|---|---|
| ① | `return` 이 먼저 대입 | **명세 보장** | "sets the result parameters before any deferred functions are executed" |
| ② | `defer` 인자가 선언 시점 평가 | **명세 보장** | "parameters to the call are evaluated as usual and saved anew" |
| ③ | `defer` 가 역순 | **명세 보장** | "in the reverse order they were deferred" |
| ④ | `f(s...)` 가 복사가 아니다 | **명세 보장** | 펼친 슬라이스가 그대로 파라미터가 된다 |
| ⑤ | 인자 0개면 `nil` | **명세 보장** | 빈 인자 목록에 대한 Calls 절 |
| ⑥ | 섀도잉된 벌거벗은 `return` 을 gc 가 **거부하지 않는다** | ★ **명세가 재량을 줬다** | "A compiler **may** disallow …" — 안 막아도 규격 준수다 |
| ⑦ | `go vet` 이 섀도잉을 안 잡는다 | **도구의 기본 설정** | `shadow` 분석기가 기본이 아니다 |
| ⑧ | `nil` 함수 호출이 `SIGSEGV` | **구현(런타임)** | 패닉은 명세인데 **`SIGSEGV`·`pc=`** 는 런타임의 표현이다 |

- ★★★ **⑥이 이 표에서 가장 재미있는 칸이다.** 명세가 「**해도 되고 안 해도 된다**」고 적은 자리이므로
  ①\~⑤와 달리 **「명세 보장」이라고 말하면 틀린다.** 정확히는 「**명세가 허용한 범위 안의 구현 선택**」이다.
  실측에서 gc 는 **거부하지 않았고**, 다른 컴파일러가 거부해도 규격 위반이 아니다.
- ★ ⑧도 층이 둘이다 — **「패닉이 난다」는 명세에 가깝고**
  **「`SIGSEGV`·`addr=0x0`·`pc=0x…`」는 런타임이 만드는 문장**이다. 주소는 빌드마다 바뀐다.

### 10. Go 는 **인자 쪽이 얇고 반환 쪽이 두껍다**

**출력** — 없음(연결 문항).

**왜 그런가**

| 물음 | **Go** | **파이썬** | **코틀린** |
|---|---|---|---|
| 기본 인자 | ★ **없다** | 있다 | 있다 |
| 이름 붙인 인자 | ★ **없다** | 있다 | 있다 |
| 오버로딩 | ★ **없다** | 없다 | 있다 |
| 위치 전용·키워드 전용 | 없다 | ★ `/` 와 `*` 로 있다 | 없다 |
| 가변 인자 | `...T` · 펼치기 `s...` | `*args`·`**kwargs` | `vararg` · 펼치기 `*a` |
| **펼치기가 복사하나** | ★ **안 한다** | 해당 없음(`args` 는 **튜플**) | ★ **한다**(`Arrays.copyOf`) |
| 여러 값 돌려주기 | ★ **다중 반환**(문법) | **튜플**(값) | `Pair`/`Triple`/데이터 클래스(값) |
| 나갈 때 반환값 고치기 | ★ **명명 반환값 + `defer`** | 없다 | 없다 |

- Go 에 **없는** 셋 — **기본 인자·이름 붙인 인자·오버로딩**.
  파이썬은 그 자리에 **아주 두꺼운 인자 규칙**을 뒀고
  ([`../../../python/syntax/19-function-argument-rules/`](../../../python/syntax/19-function-argument-rules/)),
  코틀린은 **기본값 + 이름 붙인 인자**로 오버로딩을 대신한다
  ([`../../../kotlin/syntax/08-function-declaration-default-and-named-args/`](../../../kotlin/syntax/08-function-declaration-default-and-named-args/)).
- Go 가 그 자리를 메우는 관용구 둘 —
  ① **옵션 구조체**(`func New(cfg Config)` — 제로값이 기본값) ·
  ② **함수형 옵션**(`func New(opts ...Option)` 에서 `Option` 이 `func(*T)`).
  ★ ②는 **가변 인자와 함수 값을 합쳐** 이름 붙인 인자를 흉내 내는 것이다.
- ★★ **코틀린의 spread 와 Go 의 `...` 가 반대다** — 코틀린은 **복사**하고 Go 는 **안 한다**.
  기호가 닮아서 더 위험하다.
- ★ 「여러 값 돌려주기」도 근본이 다르다 — 파이썬·코틀린은 **값 하나**(튜플·`Pair`)를 돌려주고,
  Go 는 **값이 아닌 문법 장치**다(6번 문항).

### 11. 다른 주제와 잇기

**출력** — 없음(연결 문항).

**왜 그런가**

- **`defer` 자체** — 목록의 **26번 주제**. **그쪽은 LIFO·루프 안의 `defer`·자원 정리 전체까지**,
  여기는 **반환값과 만나는 자리**만이다.
- **`panic`/`recover`** — 목록의 **27번 주제**. (2)절의 `recovered()` 가 거기 정본이다.
- **클로저가 변수를 잡는 것** — 목록의 **13번 주제**. 3번 문항의 ②가 그 성질이다.
- **`f(s...)` 로 원본이 바뀌는 것** — [`../07-slice-sharing-silent-bugs/`](../07-slice-sharing-silent-bugs/).
  막는 법은 [`../08-copy-three-index-slicing-and-memory-retention/`](../08-copy-three-index-slicing-and-memory-retention/)이다.
- **`(T, error)` 관례** — 목록의 **23번 주제**(`error` 인터페이스)와 **24번 주제**(`%w` 래핑).
- **결과 파라미터가 제로값으로 시작하는 것** —
  [`../02-variable-declarations-and-zero-values/`](../02-variable-declarations-and-zero-values/).
  (7)절의 섀도잉도 그 주제의 `:=` 규칙에서 온다.

---

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행 1회** | 재실행 결과가 `diff -rq` 로 **동일** |
| 판 확인 | `go version` · `go env GOOS GOARCH GOVERSION` | 1 | `go1.27.1 linux/amd64` |
| 다중 반환·`(T, error)` (`t12a`) | `go build && ./prog` | 1 | 실패 시 제로값 · `%w` 가 `errors.Is` 로 보임 |
| 다중 반환 통째로 넘기기 (`t12b`) | 〃 | 1 | `add(two())` = 3 |
| 섞으면 안 되는 것 (`t12c`) | `go build` | 1 | 컴파일 에러 **2줄**(서로 다른 메시지) · exit 1 |
| ★★★ 명명 반환값 + `defer` (`t12d`) | `go build && ./prog` | 1 | **42 · 21 · 101 · 가 나 · 시작③②①** |
| ★★ 오류 감싸기·`recover` (`t12e`) | 〃 | 1 | `load` 는 감싸이고 `loadBroken` 은 **안 감싸진다** |
| ★ `defer` 인자 평가 시점 (`t12f`) | 〃 | 1 | ① **i=0** · ② **i=42** · LIFO 순서 |
| ★★★ 가변 인자 여섯 꼴 (`t12g`) | 〃 | 1 | `nil` **3회** · `mutate(s...)` 뒤 **`[99 5 6]`** |
| `nil` 하나 대 `nil` 슬라이스 (`t12h`) | 〃 | 1 | **1개 대 0개** |
| `[]string` 을 `...any` 로 (`t12i`) | `go build` | 1 | `have ([]string, string...)` / `want (...any)` · exit 1 |
| 함수가 값인 것 (`t12j`) | `go build && ./prog` | 1 | 맵 값·클로저·메서드 값 전부 동작 · 제로값 `nil` |
| ★ `nil` 함수 호출 (`t12k`) | 〃 | 1 | `invalid memory address or nil pointer dereference` · **exit 2** |
| ★ 명명 반환값 섀도잉 (`t12l`) | `go build && ./prog` · `go vet ./...` | 각 1 | `<nil>` 이 나감 · **vet exit 0** |
| 형태 모음 (`t12form`) | `go build && ./prog` | 1 | 여섯 규칙이 한 프로그램에서 동작 |

**구현·도구에 달린 항목**(판이 오르면 **다시 찍어야 하는** 것)

| 항목 | 왜 |
|---|---|
| 패닉 스택의 **주소 오프셋**(`+0x90` 등)과 **`pc=0x49b770`** | 빌드마다 바뀔 수 있다 |
| `[signal SIGSEGV …]` 줄의 **형식** | **런타임의 표현**이다. 「패닉이 난다」는 명세지만 이 문장은 아니다 |
| 컴파일 에러의 **정확한 문구** | 컴파일러가 메시지를 다듬을 수 있다 |
| gc 가 **섀도잉된 벌거벗은 `return` 을 거부하지 않는 것** | ★ **명세가 재량을 준 자리**다. 다른 컴파일러는 거부해도 된다 |
| `go vet` 이 **섀도잉을 안 잡는 것** | `shadow` 분석기가 **기본이 아니다** |
| 「`defer` 가 1.14 에서 훨씬 싸졌다」 | ★ **비용을 재지 않았다.** 정본은 목록의 **26·50번 주제**다 |
| 「`recover` 를 한 겹 더 감싸면 안 듣는다」 | ★ **반례를 던지지 않았다.** 정본은 목록의 **27번 주제**다 |
| 코틀린 spread 가 **복사한다**는 것 | ★ **형제 문서의 실측을 인용한 것**이고 이 문서가 직접 던지지는 않았다 |

★ **다시 찍는 법** — `capture.sh` 를 그대로 돌리고 `diff -rq` 한다. 이 주제에는 흔들리는 블록이 없다.

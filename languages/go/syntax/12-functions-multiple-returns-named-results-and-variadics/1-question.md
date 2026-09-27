# go/syntax/12 — 함수: 다중 반환·명명 반환값·가변 인자 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> ★★★ **이 주제의 문항 절반이 「함수가 끝나는 두 단계」를 묻는다.**
> 답을 적을 때 **① 결과 파라미터에 무엇이 들어갔나 ② `defer` 가 그것을 어떻게 고쳤나**를
> **갈라서** 적어라. 뭉뚱그리면 맞아도 맞은 것이 아니다.
> ★ **출력의 순서까지 적어라** — LIFO 가 걸린 문항이 있다.
> 소스는 전부 `go build -trimpath -o prog . && ./prog` 로 던졌다. 모듈 이름은 `ex` 다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 다섯 함수가 무엇을 돌려주나 (예측)

```go
// t12d.go
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
```

- 다섯 줄의 출력을 **순서대로** 적어라.
- `named()` 와 `unnamed()` 가 갈리는 이유를 **한 낱말**로 말하라.
- `returnsLiteral()` 은 `return 100` 이라고 적혀 있다. 그런데 왜 그 값이 안 나오는가?
- `order()` 의 결과가 그 순서인 이유는 무엇인가?
- 명세의 어느 문장이 이 전부를 정하는가?

### 2. ★★★ 같은 관용구를 두 번 썼는데 (예측)

```go
// t12e.go
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
```

- 네 줄의 출력을 적어라.
- `load("")` 와 `loadBroken("")` 이 갈리는 이유는 무엇인가?
- `loadBroken` 은 컴파일되는가 — `go vet` 은 무엇이라 하는가?
- `recovered()` 가 되는 이유를 「반환 경로」라는 말로 설명하라.

### 3. ★★ 두 `defer` 가 같은 변수를 읽으면 (예측)

```go
// t12f.go
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
```

- 네 줄의 출력을 **순서대로** 적어라.
- ①과 ②가 갈리는 이유는 무엇인가?
- 두 꼴을 고르는 기준을 **한 줄**로 적어라.
- `defer file.Close()` 뒤에 `file` 을 다른 값으로 바꾸면 무엇이 닫히는가?

### 4. ★★★ 여섯 번의 호출에서 `nil` 은 몇 번인가 (예측)

```go
// t12g.go
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
```

- 여섯 줄의 `len`·`cap`·`nil인가` 를 각각 적어라.
- `sum(l, nilSlice...)` 와 `sum(l, []int{}...)` 가 갈리는 이유는 무엇인가?
- `mutate(s...)` 뒤 `s` 는 무엇인가 — **왜** 그런가?
- 하나씩 넘긴 쪽은 왜 안 바뀌는가?
- ★ 코틀린의 spread(`*`)는 여기서 어떻게 다른가?

### 5. ★★ `nil` 하나와 `nil` 슬라이스 (예측)

```go
// t12h.go
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
```

- `count(l, nil)` 과 `count(l, s...)` 의 `len` 은 각각 얼마인가?
- `args == nil` 은 각각 무엇인가?
- 그다음 이 프로그램은 어떻게 되는가?

```go
// t12i.go
package main

import "fmt"

func count(args ...any) int { return len(args) }

func main() {
	words := []string{"가", "나"}
	fmt.Println(count(words...))
	fmt.Println(count(words, "다"...))
}
```

- **에러 전문**을 적어라 — 두 번째 에러의 `have`/`want` 줄까지.
- `[]string` 을 `...any` 로 못 펼치는 이유를 **메모리 배치**로 설명하라.

### 6. ★ 다중 반환을 어디까지 넘길 수 있나 (경계)

```go
// t12b.go
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
```

```go
// t12c.go
package main

import "fmt"

func two() (int, int) { return 1, 2 }

func add(a, b int) int { return a + b }

func main() {
	fmt.Println(add(two(), 3))
	x := two()
	fmt.Println(x)
}
```

- `t12b` 의 두 줄은 각각 무엇으로 찍히는가?
- `t12c` 의 **두 에러 문장**은 각각 무엇인가 — 왜 메시지가 다른가?
- 다중 반환은 **튜플인가?** 근거를 대라.

### 7. 왜 `defer` 가 반환값을 고칠 수 있나 (왜)

- 함수가 끝날 때의 **두 단계**를 순서대로 적어라.
- 그 둘 사이에 `defer` 가 끼는 것이 **왜** 유용한가 — 실제 쓰임 둘을 대라.
- 반환값에 이름이 없으면 무엇을 고치게 되는가?
- 이 설계가 만드는 **위험**은 무엇인가?

### 8. ★ 명명 반환값을 가리면 (경계)

```go
// t12l.go
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
```

- 두 줄의 출력은 각각 무엇인가?
- `go vet` 은 무엇이라 하는가 — **종료 코드**는?
- 명세가 이 위험에 대해 컴파일러에게 무엇을 허락했는가 — 「의무」인가 「재량」인가?
- 규칙을 하나 세워라.

### 9. 어느 칸이 명세이고 어느 칸이 구현·도구의 사정인가 (경계)

아래 여덟 가지를 **「명세 보장」 / 「구현·도구의 사정」** 으로 갈라라.

- ① `return` 이 결과 파라미터에 먼저 대입한다
- ② `defer` 의 인자가 선언 시점에 평가된다
- ③ `defer` 가 역순으로 돈다
- ④ `f(s...)` 가 복사가 아니다
- ⑤ 인자 0개면 가변 인자가 `nil` 이다
- ⑥ 섀도잉된 벌거벗은 `return` 을 gc 가 거부하지 않는다
- ⑦ `go vet` 이 섀도잉을 안 잡는다
- ⑧ `nil` 함수 호출이 `SIGSEGV` 로 죽는다

### 10. 다른 언어와 나란히 놓기 (연결)

- Go 에 **없는** 인자 기능 셋을 대라 — 파이썬·코틀린에는 무엇이 있나?
- 그 자리를 Go 는 무엇으로 메우는가 — 관용구 둘을 대라.
- 코틀린의 spread 와 Go 의 `...` 는 무엇이 반대인가?
- 「여러 값을 돌려준다」를 각 언어는 어떻게 하는가?

### 11. 다른 주제와 잇기 (연결)

- `defer` 자체의 정본은 몇 번 주제인가?
- `panic`/`recover` 의 정본은 몇 번 주제인가?
- 클로저가 변수를 잡는 것의 정본은 몇 번 주제인가?
- `f(s...)` 로 원본이 바뀌는 것의 총론은 몇 번 주제인가?
- `(T, error)` 관례가 왜 그 모양인지의 정본은 몇 번 주제인가?
- 결과 파라미터가 제로값으로 시작하는 것의 정본은 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

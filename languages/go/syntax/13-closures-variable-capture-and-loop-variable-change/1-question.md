# go/syntax/13 — 클로저와 변수 캡처, 루프 변수 의미 변경(1.22) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> ★★★ **답하기 전에 `go.mod` 의 `go` 줄과 파일 첫 줄을 먼저 보라.** 이 주제는
> **같은 소스가 언어 판에 따라 다른 답을 내는** 드문 주제다. 문제마다 그 줄을 같이 실어 두었다.
> ★ **답마다 「그 값을 누가 보장하나」를 같이 적어라** — 1.21까지의 보장인가, 1.22부터의 보장인가,
> gc 구현인가, 이 판의 관찰인가.
> ★ 「값이 같다」와 「같은 변수다」를 갈라서 답하라. 이 주제는 그 둘이 자주 어긋난다.
> 소스는 전부 `go build -trimpath -o prog . && ./prog` 로 던졌다. 모듈 이름은 `ex` 다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `x` 를 세 번 고치면 `f()` 는 (예측)

```go
// t13a.go
package main

import "fmt"

// counter 는 두 클로저가 **같은 변수 n** 을 잡는 것을 보인다.
func counter() (func() int, func()) {
	n := 0
	get := func() int { return n }
	inc := func() { n++ }
	return get, inc
}

func main() {
	x := 10
	f := func() int { return x } // x 라는 **변수**를 잡는다 — 10 이라는 값이 아니다
	fmt.Println("만든 직후 f() =", f())
	x = 20
	fmt.Println("x = 20 한 뒤 f() =", f(), " — 값이 아니라 변수를 잡았다")
	x = 30
	fmt.Println("x = 30 한 뒤 f() =", f())

	get, inc := counter()
	inc()
	inc()
	fmt.Println("두 클로저가 같은 n 을 본다 : get() =", get())

	get2, _ := counter()
	fmt.Println("counter() 를 다시 부르면 새 n 이다 : get2() =", get2())
}
```

- `f()` 가 세 번 찍힌다. 각각 무엇인가?
- `get()` 은 무엇인가 — `inc()` 를 두 번 불렀다.
- `get2()` 는 무엇인가 — 왜 `get()` 과 다른가?
- 상자를 가르는 단위는 「클로저를 만드는 것」인가 「바깥 함수를 부르는 것」인가?

### 2. ★★★ 파일 첫 줄만 다른 두 함수 (예측)

두 파일이 **같은 패키지**에 있고 **한 번에 빌드**된다. 몸통은 한 글자도 같다.

```go
// t13b.go
//go:build go1.21

package main

import "fmt"

// oldRules 는 **이 파일 하나만** 언어 판을 1.21 로 내린 것이다.
// 파일 첫머리의 //go:build go1.21 이 그 일을 한다.
func oldRules() {
	var fs []func()
	for i := 0; i < 3; i++ {
		fs = append(fs, func() { fmt.Print(i, " ") })
	}
	for _, f := range fs {
		f()
	}
	fmt.Println(" <- go1.21 의미 (이 파일)")
}
```

```go
// t13c.go
package main

import "fmt"

// newRules 는 go.mod 의 판(이 모듈은 go 1.27)을 그대로 쓴다.
func newRules() {
	var fs []func()
	for i := 0; i < 3; i++ {
		fs = append(fs, func() { fmt.Print(i, " ") })
	}
	for _, f := range fs {
		f()
	}
	fmt.Println(" <- go1.22 이후 의미 (이 파일)")
}

func main() {
	fmt.Println("한 프로그램 · 한 번의 빌드 · 두 의미")
	oldRules()
	newRules()
}
```

- 이 프로그램은 몇 줄을 찍는가 — 각 줄은 무엇인가?
- 두 함수의 출력이 갈린다면 **무엇이 그것을 갈랐는가**?
- 컴파일러는 몇 개인가? 빌드는 몇 번인가?
- 명세는 이 두 동작을 어떻게 적어 두었는가?

### 3. `go.mod` 한 줄을 바꾸면 (예측)

소스는 아래 하나다. `go.mod` 의 `go` 줄만 `1.21` 과 `1.22` 로 바꿔 두 번 던진다.

```go
// t13d.go
package main

import "fmt"

func main() {
	var fs []func()
	for i := 0; i < 3; i++ {
		fs = append(fs, func() { fmt.Print(i, " ") })
	}
	for _, f := range fs {
		f()
	}
	fmt.Println()
}
```

- 두 번의 출력은 각각 무엇인가?
- `go.mod` 의 `go` 지시어는 **툴체인 버전**인가 **언어 판**인가?
- 이 머신의 툴체인은 하나뿐인데 어떻게 두 답이 나오는가?
- 남의 Go 코드에서 루프와 클로저가 만나는 자리를 읽을 때 **무엇을 먼저 봐야 하는가**?

### 4. ★★ 상자가 몇 개인가 (예측)

`t13e.go` 는 첫 줄에 `//go:build go1.21` 이 있고, `t13f.go` 는 없다. 몸통은 같다.

```go
// t13e.go
//go:build go1.21

package main

import "sync"

// oldBoxes 는 **언어 판 1.21** 로 컴파일되는 파일이다(첫머리의 //go:build go1.21).
// 회차마다 루프 변수의 주소를 모은다.
func oldBoxes() []*int {
	var ps []*int
	for i := 0; i < 3; i++ {
		ps = append(ps, &i)
	}
	return ps
}

// oldGoro 는 고루틴 셋이 **루프가 다 끝난 뒤에** i 를 읽게 한다.
// close(start) 가 happens-before 를 만들어 주므로 경쟁도 무작위도 없다.
func oldGoro() []int {
	var wg sync.WaitGroup
	start := make(chan struct{})
	out := make([]int, 3)
	for i := 0; i < 3; i++ {
		wg.Add(1)
		go func(slot int) {
			defer wg.Done()
			<-start
			out[slot] = i
		}(i)
	}
	close(start)
	wg.Wait()
	return out
}
```

```go
// t13f.go
package main

import (
	"fmt"
	"sync"
)

// newBoxes 는 이 모듈의 판(go 1.27)을 그대로 쓴다. 나머지는 oldBoxes 와 한 글자도 같다.
func newBoxes() []*int {
	var ps []*int
	for i := 0; i < 3; i++ {
		ps = append(ps, &i)
	}
	return ps
}

func newGoro() []int {
	var wg sync.WaitGroup
	start := make(chan struct{})
	out := make([]int, 3)
	for i := 0; i < 3; i++ {
		wg.Add(1)
		go func(slot int) {
			defer wg.Done()
			<-start
			out[slot] = i
		}(i)
	}
	close(start)
	wg.Wait()
	return out
}

// distinct 는 주소를 안 찍고 **서로 다른 상자가 몇 개인지**만 센다.
// 주소 자체는 실행마다 바뀌지만 이 개수는 안 바뀐다.
func distinct(ps []*int) int {
	n := 0
	for i, p := range ps {
		seen := false
		for j := 0; j < i; j++ {
			if ps[j] == p {
				seen = true
			}
		}
		if !seen {
			n++
		}
	}
	return n
}

func vals(ps []*int) []int {
	out := make([]int, len(ps))
	for i, p := range ps {
		out[i] = *p
	}
	return out
}

func main() {
	o, n := oldBoxes(), newBoxes()
	fmt.Println("go1.21 의미 — 서로 다른 상자 개수 :", distinct(o), " 상자 안 값 :", vals(o))
	fmt.Println("go1.22 의미 — 서로 다른 상자 개수 :", distinct(n), " 상자 안 값 :", vals(n))
	fmt.Println()
	fmt.Println("고루틴 셋이 루프가 끝난 뒤 i 를 읽으면")
	fmt.Println("  go1.21 의미 :", oldGoro())
	fmt.Println("  go1.22 의미 :", newGoro())
}
```

- 네 줄이 찍힌다. 각각 무엇인가?
- 「서로 다른 상자 개수」가 둘로 갈린다면 그 수는 각각 몇인가?
- `[3 3 3]` 이 나오는 이유를 **「늦게 읽어서」 말고 다른 낱말로** 설명하라.
- 아래 고루틴 실험은 왜 실행할 때마다 흔들리지 않는가?

### 5. ★★ 다섯 줄 중 어느 줄이 아직 옛 답을 내나 (예측)

```go
// t13g.go
package main

import "fmt"

func main() {
	// ① for 의 init 에서 선언한 변수 — 1.22 부터 회차마다 새것이다
	var a []func() int
	for i := 0; i < 3; i++ {
		a = append(a, func() int { return i })
	}

	// ② range 의 변수 — 이것도 회차마다 새것이다
	var b []func() int
	for _, v := range []int{10, 20, 30} {
		b = append(b, func() int { return v })
	}

	// ③ ★ for 바깥에서 선언한 변수 — 1.22 가 손대지 않는 자리다
	var c []func() int
	j := 0
	for ; j < 3; j++ {
		c = append(c, func() int { return j })
	}

	// ④ ③ 을 옛 관용구로 고친 것
	var d []func() int
	k := 0
	for ; k < 3; k++ {
		k := k
		d = append(d, func() int { return k })
	}

	// ⑤ 루프가 아예 아닌 자리 — 클로저 둘이 한 변수를 본다
	n := 0
	up := func() { n++ }
	read := func() int { return n }
	up()
	up()

	show := func(tag string, fs []func() int) {
		fmt.Print(tag, " ")
		for _, f := range fs {
			fmt.Print(f(), " ")
		}
		fmt.Println()
	}
	show("① for init 선언    :", a)
	show("② range 변수       :", b)
	show("③ for 바깥 선언    :", c)
	show("④ ③ + k := k       :", d)
	fmt.Println("⑤ 루프가 아닌 클로저 공유 : read() =", read())
}
```

- 다섯 줄은 각각 무엇으로 찍히는가?
- 그중 **`0 1 2` 가 아닌 줄**은 어느 것이고 왜인가?
- 그 줄을 고치려면 무엇을 적어야 하는가?
- ⑤는 고쳐야 할 것인가?

### 6. 루프 안의 `defer` 둘 (예측)

```go
// t13h.go
package main

import "fmt"

func main() {
	defer fmt.Println() // 맨 처음 적었으니 맨 나중에 돈다 — 줄바꿈용
	for i := 0; i < 3; i++ {
		defer fmt.Print("A", i, " ")              // 인자는 지금 평가된다
		defer func() { fmt.Print("B", i, " ") }() // 클로저는 나갈 때 i 를 읽는다
	}
	fmt.Println("본문 끝 — 아래는 defer 가 LIFO 로 돈 것이다")
}
```

- 출력은 몇 줄이고 각각 무엇인가?
- `A` 쪽과 `B` 쪽의 숫자가 다르다면 왜인가 — 같다면 왜인가?
- 찍히는 **순서**는 무엇이 정하는가?
- `go.mod` 를 `go 1.21` 로 내리면 **어느 쪽 세 줄**이 달라지는가?

### 7. 1.22는 무엇을 고쳤나 (왜)

- 고쳐진 것은 **클로저의 규칙**인가 **`for` 의 규칙**인가?
- 명세에서 그 문장을 찾는다면 어느 절인가 — 그리고 옛 규칙은 명세에 남아 있는가?
- 「회차마다 새 변수」라는 말만으로는 부족하다 — **새 변수의 초깃값**은 무엇인가?
- 이 변경이 **기존 코드를 조용히 바꿀 수 있는데** Go 는 왜 그래도 됐다고 봤겠는가?

### 8. 도구는 무엇을 보고 무엇을 못 보나 (경계)

- `go vet` 은 아래 코드에 무엇이라 말하는가 — `go.mod` 가 `go 1.21` 일 때와 `go 1.27` 일 때 각각.

```go
// t13j.go
package main

import (
	"fmt"
	"sync"
)

func main() {
	var wg sync.WaitGroup
	for i := 0; i < 3; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			fmt.Println(i)
		}()
	}
	wg.Wait()
}
```

- 두 경우의 **종료 코드**는 각각 무엇인가?
- `vet` 이 침묵하는 것은 「안전하다」는 뜻인가?
- 5번 문제 ③의 코드에 대해 `vet` 은 무엇이라 말하겠는가?

### 9. 잡힌 변수는 어디에 사나 (경계)

```go
// t13i.go
package main

import "fmt"

// escapes 는 지역 변수를 클로저가 잡아 밖으로 내보낸다.
func escapes() func() int {
	x := 0
	return func() int { x++; return x }
}

// stays 는 같은 모양인데 클로저를 그 자리에서 쓰고 버린다.
func stays() int {
	y := 0
	f := func() int { y++; return y }
	return f() + f()
}

func main() {
	g := escapes()
	fmt.Println(g(), g(), stays())
}
```

- `go build -gcflags='-m -l'` 는 `x` 에 대해 무엇이라 말하는가?
- `escapes` 의 클로저와 `stays` 의 클로저는 같은 말을 듣는가?
- 이 출력은 **명세 보장**인가 **구현**인가?
- `-l` 을 왜 붙였는가?

### 10. 파이썬과 나란히 놓기 (연결)

- 파이썬의 `[f for …]` 루프 클로저가 같은 값을 내는 이유는 Go 1.21과 같은가 다른가?
- 파이썬은 이것을 고쳤는가 — 고쳤다면 몇 판부터인가?
- 파이썬에서 상자를 가르는 방법 셋은 무엇인가?
- 자바 람다는 바깥 지역 변수를 **고칠 수 있는가** — Go 는?
- 셋 중 **언어가 상자를 갈라 주는** 것은 어느 것인가?

### 11. 다른 주제와 잇기 (연결)

- `defer` 의 인자 평가 시점과 LIFO 의 정본은 몇 번 주제인가?
- `for` 문법 자체(네 형태·`range`)의 정본은 몇 번 주제인가?
- 캡처가 만드는 **데이터 레이스**의 정본은 몇 번 주제인가?
- `-gcflags=-m` 출력 읽기의 정본은 몇 번 주제인가?
- 이 주제와 같은 「`go.mod` 가 언어 의미를 바꾸는」 사례가 목록에 하나 더 있다 — 몇 번인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

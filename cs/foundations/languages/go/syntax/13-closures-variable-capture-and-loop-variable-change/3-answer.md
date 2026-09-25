# go/syntax/13 — 클로저와 변수 캡처, 루프 변수 의미 변경(1.22) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> 블록은 전부 `===== 소스: … =====` 로 소스를 먼저 싣는다 — **그대로 다시 던질 수 있게** 하기 위해서다.
> ★★ **언어 판이 걸린 블록은 `go.mod` 도 소스로 싣는다.** 이 주제는 그 파일이 곧 입력이다.
> ★ **근거로 읽을 칸** — 클로저의 출력 값, **서로 다른 상자의 개수**, `go vet` 문장 본문과 `파일:줄:칸`,
> 종료 코드.
> **근거로 읽지 않을 칸** — 변수의 **주소 자체**(그래서 개수만 센다), `-gcflags='-m -l'` 출력의
> **줄·칸 번호와 항목 수**(읽을 것은 `moved to heap` 이라는 낱말이다).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 10 → 20 → 30 — 클로저는 값을 안 베꼈다

**출력**

```text
===== 소스: t13a.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
만든 직후 f() = 10
x = 20 한 뒤 f() = 20  — 값이 아니라 변수를 잡았다
x = 30 한 뒤 f() = 30
두 클로저가 같은 n 을 본다 : get() = 2
counter() 를 다시 부르면 새 n 이다 : get2() = 0
(exit 0)
```

**왜 그런가**

- `f` 가 들고 있는 것은 **`x` 라는 변수**다. `x` 를 고치면 `f()` 도 따라 바뀐다.
  명세: "Function literals are closures … Those variables are then **shared** between the
  surrounding function and the function literal, and they **survive as long as they are accessible**."
- `get` 과 `inc` 는 **같은 `n`** 을 본다. `inc()` 를 두 번 불렀으니 `get()` 이 **2**다.
  한 변수를 잡은 클로저가 여럿이면 **서로의 수정이 보인다.**
- `counter()` 를 **다시 부르면 새 프레임이고 새 `n`** 이라 `get2()` 가 **0**이다.
- ★ 그러니 상자를 가르는 단위는 **「바깥 함수의 호출」** 이다. 클로저를 몇 개 만드는지는 상관없다.
- 층 — **1.0부터의 명세 보장**이다. 이 절에는 1.22가 바꾼 것이 하나도 없다.

### 2. ★★★ 세 줄 — `3 3 3` 과 `0 1 2` 가 한 바이너리에서 같이 나온다

**출력**

```text
===== 소스: t13b.go =====
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
===== 소스: t13c.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
한 프로그램 · 한 번의 빌드 · 두 의미
3 3 3  <- go1.21 의미 (이 파일)
0 1 2  <- go1.22 이후 의미 (이 파일)
(exit 0)
```

**왜 그런가**

- 갈린 것은 **`t13b.go` 의 첫 줄 `//go:build go1.21` 하나**다. 몸통은 한 글자도 같다.
- 컴파일러는 **하나**(go1.27.1), 빌드도 **한 번**이다. 그런데 출력이 갈렸다.
- ★★★ 그러니 이 차이는 최적화도 아니고 컴파일러 판도 아니고 **「언어 판」 그 자체**다.
  `//go:build go1.N` 은 원래 빌드 제약인데 **1.21부터 그 파일의 언어 판까지 내린다.**
- 명세가 두 동작을 나란히 적어 놓았다.

  > **Each iteration has its own separate declared variable (or variables) [Go 1.22].**
  > The variable used by the first iteration is declared by the init statement.
  > The variable used by each subsequent iteration is declared implicitly before executing
  > the post statement and **initialized to the value of the previous iteration's variable at that moment**.

  > **Prior to [Go 1.22], iterations share one set of variables instead of having their own
  > separate variables.**

- ★★ 명세가 **같은 예제의 옛 출력까지 싣는다** — `1 3 5` 대 `6 6 6`.
  「명세가 바뀐 자리」를 명세 스스로 기록해 둔 드문 경우다.

### 3. `3 3 3` 과 `0 1 2` — 소스는 한 글자도 안 바꿨다

**출력**

```text
===== 소스: t13d.go =====
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
===== 소스: go.mod =====
module ex

go 1.21
===== 명령: go build -trimpath -o prog . && ./prog =====
3 3 3 
(exit 0)
```

```text
===== 소스: t13d.go =====
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
===== 소스: go.mod =====
module ex

go 1.22
===== 명령: go build -trimpath -o prog . && ./prog =====
0 1 2 
(exit 0)
```

**왜 그런가**

- ★ `go.mod` 의 `go` 지시어는 **최소 툴체인 버전이 아니라 언어 판**이다.
  go1.27.1 이 `go 1.21` 짜리 모듈을 **1.21 규칙으로** 읽는다.
- 그래서 툴체인이 하나뿐인 이 머신에서도 **두 답이 나온다.** 레버가 컴파일러가 아니라 모듈 파일에 있다.
- ★★★ 실무에 남기는 문장 한 줄 — **Go 코드에서 루프와 클로저가 만나는 자리를 읽을 때는
  `go.mod` 를 먼저 연다.** 「새 툴체인으로 빌드했으니 새 규칙」이 아니다.
- 층 — 출력값 자체는 **각 판의 명세 보장**이고,
  「`go.mod` 가 그 스위치」라는 것은 **툴체인 계약**이다(명세 본문이 아니다).
  14번 주제의 에러 문구가 그 계약을 직접 말한다 — `-lang was set to go1.21; check go.mod`.

### 4. ★★ 상자 1개 대 3개 — `[3 3 3]` 의 진짜 이유

**출력**

```text
===== 소스: t13e.go =====
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
===== 소스: t13f.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
go1.21 의미 — 서로 다른 상자 개수 : 1  상자 안 값 : [3 3 3]
go1.22 의미 — 서로 다른 상자 개수 : 3  상자 안 값 : [0 1 2]

고루틴 셋이 루프가 끝난 뒤 i 를 읽으면
  go1.21 의미 : [3 3 3]
  go1.22 의미 : [0 1 2]
(exit 0)
```

**왜 그런가**

- **go1.21 의미에서 서로 다른 상자가 1개**다. `ps[0]`·`ps[1]`·`ps[2]` 가 전부 같은 변수를 가리킨다.
  그래서 값도 `[3 3 3]` — **루프가 끝난 뒤의 그 하나**를 셋이 읽은 것이다.
- **go1.22 의미에서는 3개**다. 값도 `[0 1 2]` 다.
- ★★ 그러니 답은 「**늦게 읽어서**」가 아니라 「**읽을 상자가 하나여서**」다.
  상자가 셋이었다면 아무리 늦게 읽어도 `0 1 2` 가 나왔을 것이다 — 오른쪽 줄이 그 반례다.
- ★ 주소를 안 찍고 **개수만** 셌다. 주소는 실행마다 바뀌는 흔들리는 칸이고,
  우리가 알고 싶은 것은 「**같나 다르나**」뿐이다(05번 주제가 같은 이유로 `A`·`B` 이름표를 썼다).
- 고루틴 실험이 안 흔들리는 이유 — 고루틴 셋이 `<-start` 에서 기다리고,
  **루프가 다 끝난 뒤에** `close(start)` 가 그들을 깨운다.
  `close` 와 수신 사이에 **happens-before** 가 서므로 「루프의 마지막 쓰기」가 「읽기」보다 먼저다.
  **경쟁이 없다** — 일부러 그렇게 짰다. 안 그러면 출력이 실행마다 흔들려 근거가 못 된다.

### 5. ★★ 다섯 줄 중 셋째 줄만 아직 `3 3 3` 이다

**출력**

```text
===== 소스: t13g.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
① for init 선언    : 0 1 2 
② range 변수       : 10 20 30 
③ for 바깥 선언    : 3 3 3 
④ ③ + k := k       : 0 1 2 
⑤ 루프가 아닌 클로저 공유 : read() = 2
(exit 0)
```

**왜 그런가**

| 줄 | 출력 | 왜 |
|---|---|---|
| ① `for i := 0; …` | `0 1 2` | **init 문이 선언한 변수** — 1.22가 회차마다 갈라 준다 |
| ② `for _, v := range …` | `10 20 30` | **`range` 절이 선언한 변수** — 역시 갈라 준다 |
| ③ `j := 0; for ; j < 3; j++` | **`3 3 3`** | ★ `j` 를 **`for` 가 선언하지 않았다.** 1.22가 손대지 않은 자리다 |
| ④ ③ + `k := k` | `0 1 2` | 옛 관용구가 **상자를 손으로 하나 더 놓는다** |
| ⑤ 루프가 아닌 클로저 둘 | `read() = 2` | 공유가 **쓸모**인 자리 — 고칠 것이 아니다 |

- ★★★ 그러니 판단 기준은 **버전이 아니라 문법**이다 —
  「**그 변수를 `for` 가 선언했나**」. `for ; cond; post` 꼴을 보면 멈추고 선언 위치를 본다.
- 명세도 그렇게 적혀 있다 — 고친 대상은 "the variable used by the first iteration is
  **declared by the init statement**" 와 `range` 절의 `:=` 선언 둘뿐이다.
- ⑤는 고칠 것이 아니다. (1)절이 말한 「공유」가 그대로 생성기·누산기의 기계다.
- 층 — ①②는 **1.22부터의 보장**, ③은 **양쪽 판 모두의 보장**, ④는 언제나 됐던 관용구다.

### 6. 여섯 칸 — `A` 는 회차 값, `B` 도 회차 값(1.22부터)

**출력**

```text
===== 소스: t13h.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
본문 끝 — 아래는 defer 가 LIFO 로 돈 것이다
B2 A2 B1 A1 B0 A0 
(exit 0)
```

**왜 그런가**

- `defer fmt.Print("A", i, " ")` 는 **인자를 `defer` 를 적은 그 순간 평가**한다.
  그래서 `A0`·`A1`·`A2` 다. 명세:

  > **Each time a "defer" statement executes, the function value and parameters to the call
  > are evaluated as usual and saved anew but the actual function is not invoked.**

- `defer func() { … i … }()` 는 **몸통이 나갈 때** 돌면서 그때 `i` 를 읽는다.
  1.22 이후에는 회차마다 `i` 가 따로라 **`B0`·`B1`·`B2`** 다.
- 순서는 **LIFO** 다 — 나중에 적은 것이 먼저 돈다. 그래서 `B2 A2 B1 A1 B0 A0` 이다.
  (맨 처음 적은 `defer fmt.Println()` 이 맨 나중에 돌아 줄바꿈을 찍는다.)
- ★★ `go.mod` 를 `go 1.21` 로 내리면 **`B` 쪽 세 줄이 전부 `B3`** 이 된다 — 던져서 확인했다.

```text
===== 소스: go.mod =====
module ex

go 1.21
===== 명령: go build -trimpath -o prog . && ./prog =====
본문 끝 — 아래는 defer 가 LIFO 로 돈 것이다
B3 A2 B3 A1 B3 A0 
(exit 0)
```

  `A` 쪽은 안 변한다. 인자를 **그 순간** 평가하므로 상자가 하나든 셋이든 값이 같다.
- ★ 두 꼴을 고르는 기준 한 줄 — 「**지금 값을 쓰고 싶은가, 나갈 때 값을 쓰고 싶은가**」.
  정본은 [12번 주제](../12-functions-multiple-returns-named-results-and-variadics/) (3)절이다.

### 7. `for` 를 고쳤다 — 클로저는 한 글자도 안 고쳤다

**출력** — 없음(왜 문항). 근거는 명세 인용과 2~6번의 출력이다.

**왜 그런가**

- 고쳐진 것은 **`for` 의 규칙**이다. 클로저 쪽 문장("Function literals are closures … shared …")은
  1.0부터 지금까지 같다. 2번의 두 함수가 **같은 클로저 코드로 다른 답**을 낸 것이 그 증거다.
- 명세에서의 자리 — **For statements** 절의 ForClause 부분과, **range clause** 부분 두 군데다.
  옛 규칙은 **지워지지 않고 남아 있다** — "Prior to [Go 1.22], iterations share one set of variables".
- 「회차마다 새 변수」만으로는 부족하다. **새 변수는 직전 회차 변수의 값으로 초기화**되고,
  그 복사가 **post 문을 실행하기 직전**에 일어난다.
  그래서 루프 몸통에서 `i` 를 고쳐도 다음 회차가 그 값을 이어받는다(명세 예제가 `1 3 5` 를 찍는 이유).
- 기존 코드를 조용히 바꿀 수 있는데도 Go 가 이 변경을 한 이유는,
  **바뀌는 코드의 거의 전부가 이미 버그였기** 때문이다 —
  「루프 변수를 캡처했는데 같은 값이 나온다」는 의도된 코드가 드물다.
  ★ 그래도 **조용히 바뀌는 것은 사실이고**, 그래서 스위치를 `go.mod` 에 두어
  **옛 모듈은 옛 규칙으로 남게** 했다. 3번이 그것을 보인 것이다.
  ★ 「거의 전부가 버그였다」는 **이 문서가 잰 것이 아니라 설계 의도에 대한 서술**이다 —
  이 노트에서 측정하지 않았다.

### 8. `go 1.21` 이면 한 줄 + 종료 코드 1, `go 1.27` 이면 **아무것도 없이 0**

**출력**

```text
===== 소스: t13j.go =====
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
===== 소스: go.mod =====
module ex

go 1.21
===== 명령: go vet ./... =====
t13j.go:14:16: loop variable i captured by func literal
(exit 1)
```

```text
===== 소스: go.mod =====
module ex

go 1.27
===== 명령: go vet ./... =====
(exit 0)
```

**왜 그런가**

- 같은 소스인데 **`go.mod` 만 다르다.** `vet` 이 **언어 판을 보고 판단**한다.
  1.22부터는 그 패턴이 버그가 아니게 됐으므로 보고할 것이 없어진 것이다.
- ★★ 두 번째 블록은 **출력이 한 줄도 없는 블록**이다. 그 「없음」이 이 문항의 답이다 —
  명령과 `(exit 0)` 까지 같이 실어야 **「도구가 침묵했다」와 「내가 안 돌렸다」가 구분**된다.
- ★★★ **`vet` 의 침묵은 안전의 보장이 아니다.** 5번 ③의 꼴을 고루틴으로 바꿔 던져 봤다 —
  `j` 를 `for` 바깥에서 선언한 코드다.

```text
===== 소스: go.mod =====
module ex

go 1.21
===== 명령: go vet ./... =====
t13k.go:15:16: loop variable j captured by func literal
(exit 1)
```

```text
===== 소스: t13k.go =====
package main

import (
	"fmt"
	"sync"
)

func main() {
	var wg sync.WaitGroup
	j := 0
	for ; j < 3; j++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			fmt.Println(j)
		}()
	}
	wg.Wait()
}
===== 소스: go.mod =====
module ex

go 1.27
===== 명령: go vet ./... =====
(exit 0)
```

  **`go 1.27` 에서 `vet` 이 완전히 조용하다.** 그런데 5번 ③이 보였듯 이 코드의 클로저들은
  **같은 `j` 를 본다.** 즉 **진짜 버그인데 도구가 침묵한다.**
  ★ 고루틴 쪽의 **실제 출력은 안 실었다** — `j++` 와 고루틴의 읽기가 동기화 없이 겹쳐
  실행마다 달라질 수 있는 자리라, 근거로 쓸 수 없다.
  근거로 쓸 수 있는 것은 **5번 ③의 결정적인 `3 3 3`** 과 **여기의 `vet` 침묵** 둘이다.
- 층 — `vet` 이 하는 말은 **도구(구현)** 다. 명세가 약속한 것이 아니다.

### 9. `moved to heap: x` — 클로저가 변수를 힙으로 올렸다

**출력**

```text
===== 소스: t13i.go =====
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
===== 명령: go build -trimpath -gcflags='-m -l' -o prog . =====
# ex
ex/t13i.go:7:2: moved to heap: x
ex/t13i.go:8:9: func literal escapes to heap
ex/t13i.go:14:7: func literal does not escape
ex/t13i.go:20:13: ... argument does not escape
ex/t13i.go:20:15: g() escapes to heap
ex/t13i.go:20:20: g() escapes to heap
ex/t13i.go:20:29: stays() escapes to heap
(exit 0)
```

**왜 그런가**

- `moved to heap: x` — `escapes` 의 `x` 는 **함수가 끝난 뒤에도 살아야** 하므로 힙으로 갔다.
  명세의 "survive as long as they are accessible" 를 구현이 이렇게 갚는다.
- `func literal escapes to heap` — 그 클로저 자체도 반환되니 힙이다.
- `func literal does not escape` — `stays` 의 클로저는 **그 자리에서 쓰고 버린다.**
  ★ 코드 모양은 거의 같은데 **쓰이는 방식**이 갈랐다.
- 층 — **구현(gc)** 이다. 명세에는 스택도 힙도 없다. 어디에 두느냐는 컴파일러의 판단이다.
  컴파일러 판이 바뀌면 이 출력의 줄 수와 문구가 달라질 수 있다.
- `-l` 은 **인라인을 끄는** 플래그다. 안 끄면 `inlining call to …` 줄이 잔뜩 섞여
  읽을 줄이 묻힌다. 읽을 것은 줄 번호가 아니라 **`moved to heap` 이라는 낱말**이다.
- 정본은 목록의 **52번 주제**(도구·탈출 분석 읽기)다.

### 10. 파이썬은 아직 상자를 안 가른다 — 고침이 사용자 쪽에 있다

**출력** — 없음(연결 문항).

**왜 그런가**

| 물음 | **Go 1.21까지** | **Go 1.22부터** | **파이썬** | **자바** |
|---|---|---|---|---|
| 클로저가 잡는 것 | **변수** | **변수** | **변수**(셀) | 사실상 **값** |
| 루프가 상자를 가르나 | 안 가른다 | **가른다** | **안 가른다** | 해당 없음 |
| 그래서 루프 클로저는 | 같은 값 | **회차 값** | 같은 값 | 잡을 수 있는 변수 자체가 제한됨 |
| 잡은 변수를 고칠 수 있나 | 된다 | 된다 | `nonlocal` 로 된다 | **안 된다**(effectively final) |
| 고침이 어디 있나 | 사용자(`i := i`) | **언어** | **사용자**(팩토리·기본 인자·`partial`) | 해당 없음 |

- 파이썬 쪽은 [`../../../python/syntax/22-closures-and-late-binding/`](../../../python/syntax/22-closures-and-late-binding/)
  가 정본이다. 그 문서는 **셀(cell) 객체를 `is` 로 비교해** 「서로 다른 셀이 몇 개인가: 1」을 찍는다 —
  이 주제의 **「서로 다른 상자 개수: 1」** 과 정확히 같은 격자다.
- ★★ 파이썬은 **고친 적이 없다.** 그 문서의 결론이 그렇다 —
  「`for` 가 스코프를 안 만드는 것」과 「이름이 쓸 때 풀리는 것」이 **둘 다 명세**라서 구현 세부가 아니다.
  그래서 파이썬의 고침은 언제나 사용자 쪽이다 — 팩토리로 셀을 가르거나(`서로 다른 셀 개수: 3`),
  기본 인자 `f(i=i)` 로 셀 자체를 없애거나, `functools.partial` 로 밖에 담는다.
- ★ **셋 중 언어가 상자를 갈라 준 것은 Go 하나**다. 자바스크립트의 `let` 이 같은 선택을 했다
  (파이썬 문서가 그 대비를 든다).
- 자바 람다는 effectively final 한 지역 변수만 잡으므로 **잡은 변수를 고칠 수 없다.**
  Go 는 고칠 수 있고, 그것이 (1)절의 `counter` 를 가능하게 한다.

### 11. 다른 주제와 잇기

**출력** — 없음(연결 문항).

**왜 그런가**

- **`defer` 의 인자 평가 시점과 LIFO** — [12번 주제](../12-functions-multiple-returns-named-results-and-variadics/) (3)절.
  이 주제는 그 규칙이 **루프 변수와 겹치는 자리**만 본다.
- **`for` 문법 자체(네 형태·`range`·정수 range·함수 range)** — [14번 주제](../14-for-four-forms-range-over-int-and-func/).
  이 주제는 그중 「변수가 몇 개인가」 한 축만 본다.
- **캡처가 만드는 데이터 레이스** — 목록의 **35번 주제**(`-race`).
  고루틴 자체는 **28번 주제**다.
- **루프 안의 `defer` 가 쌓이는 문제** — 목록의 **26번 주제**.
- **`-gcflags=-m` 출력 읽기** — 목록의 **52번 주제**.
- ★ **`go.mod` 가 언어 의미를 바꾸는 사례가 하나 더** 있다 — 목록의 **48번 주제**
  (`time.Timer`/`Ticker` 의 1.23 변경). 이 주제와 같은 성질의 자리다.

---

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행 1회** | 재실행 결과가 `normalize-shaky.py` 로 **동일** |
| 판 확인 | `go version` · `go env GOOS GOARCH GOVERSION` | 1 | `go1.27.1 linux/amd64` |
| 변수 캡처 (`t13a`) | `go build && ./prog` | 1 | `f()` 가 10→20→30 · `get()`=2 · `get2()`=0 |
| ★★★ 한 빌드 두 의미 (`t13b`+`t13c`) | 〃 (`//go:build go1.21` 이 한 파일에만) | 1 | `3 3 3` 과 `0 1 2` 가 **같은 바이너리에서** |
| ★★ `go.mod` 레버 (`t13d`) | `go 1.21` / `go 1.22` 로 각각 | 2 | `3 3 3` / `0 1 2` |
| ★★ 상자 세기 (`t13e`+`t13f`) | `go build && ./prog` | 1 | 상자 **1개** 대 **3개** · 고루틴 `[3 3 3]` 대 `[0 1 2]` |
| `i := i` 가 필요한 자리 (`t13g`) | 〃 | 1 | ③만 `3 3 3` |
| `defer` 와 루프 (`t13h`) | `go 1.27` / `go 1.21` 로 각각 | 2 | `B2 A2 B1 A1 B0 A0` / `B3 A2 B3 A1 B3 A0` |
| 탈출 분석 (`t13i`) | `go build -gcflags='-m -l'` | 1 | `moved to heap: x` · 한쪽만 `escapes to heap` |
| `go vet` — 고루틴 (`t13j`) | `go vet ./...` 을 `go 1.21` / `go 1.27` 로 | 2 | 한 줄 + `exit 1` / **0줄 + `exit 0`** |
| ★ `go vet` — 바깥 선언 (`t13k`) | 〃 | 2 | 한 줄 + `exit 1` / **0줄 + `exit 0`** — 버그인데 침묵 |
| 형태 (`t13form`) | `go build && ./prog` | 1 | `2 7 1 3` + `defer` 줄 |

**구현·환경에 달린 항목**(버전이 오르거나 환경이 바뀌면 **다시 찍어야 하는** 것)

| 항목 | 무엇에 달렸나 |
|---|---|
| `-gcflags='-m -l'` 출력의 **줄 수·문구·줄 번호** | **컴파일러 판(go1.27.1)**. 읽을 것은 `moved to heap` 이라는 낱말이다 |
| `go vet` 이 무엇을 보고하나 | **도구 판.** 1.22부터 loopclosure 보고가 사라졌다 |
| 회차마다 **할당이 실제로 생기는가** | **구현.** 캡처가 없으면 안 만들 수 있다 — **안 쟀다** |
| 고루틴이 **뒤엉켜 찍는 순서** | 이 문서는 그 자리를 **일부러 피했다**(`close`+`WaitGroup`+정렬) |
| `t13k` 의 **실행 출력** | 동기화 없는 읽기라 **근거로 못 쓴다** — 그래서 안 실었다 |
| 「바뀌는 코드의 거의 전부가 이미 버그였다」 | **설계 의도에 대한 서술** — 이 노트에서 **측정하지 않았다** |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다.

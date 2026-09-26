# go/syntax/13 — 클로저와 변수 캡처, 루프 변수 의미 변경(1.22) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Go 명세](https://go.dev/ref/spec) 의 Function literals · For statements with ForClause ·
> For statements with range clause · Declarations and scope 절.\
> 웹이 아니라 **이 툴체인이 들고 있는 `$(go env GOROOT)/doc/go_spec.html` 을 열어** 인용했다.
> 그 파일의 머리는 「**Language version go1.27 (May 26, 2026)**」이다.
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> **버전** — 클로저(함수 리터럴이 바깥 변수를 잡는 것)는 **1.0부터 지금까지 같다**.
> **루프 변수가 회차마다 새로 생기는 것은 1.22부터**다. 그 앞에서는 루프 전체가 변수 하나를 나눠 썼다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 명세로, 출력은 실행으로 접지했다.

## ★★ 이 갈래가 쓰는 층 — 이 주제만 넷이다

다른 주제는 셋(명세 보장 / 구현 / 이 판의 관찰)인데, **이 주제는 명세 자체가 한 번 바뀌었다.**
그래서 「명세 보장」 칸이 **둘로 쪼개진다.**

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **1.21까지의 보장** | 그때의 명세가 약속한 것 — 루프가 변수 **하나**를 나눠 쓴다 | `go_spec.html` 의 "Prior to [Go 1.22] …" 문장 · `go.mod` 를 내려 던진 출력 |
| **1.22부터의 보장** | 지금의 명세가 약속한 것 — 회차마다 **자기 변수** | 같은 파일의 "Each iteration has its own separate declared variable [Go 1.22]" |
| **구현(gc)** | 이 컴파일러·도구가 그렇게 하는 것. 약속은 아니다 | `-gcflags='-m -l'` 의 탈출 분석 · `go vet` 이 무엇을 보고하나 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 실행 출력(재실행 대조까지) |

★★★ **여기가 이 묶음의 드문 자리다.** 「돌려 봤더니 이렇더라」가 아니라
**「같은 소스를 두 판으로 던져 출력이 갈리는 것」** 을 보일 수 있다.
같은 툴체인 하나(go1.27.1)로 그것이 되는 이유는 **판을 고르는 스위치가 툴체인이 아니라 `go.mod` 에 있기** 때문이다.

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
```

```text
===== 명령: go env GOOS GOARCH GOVERSION =====
linux
amd64
go1.27.1
(exit 0)
```

★ 툴체인은 이 하나뿐이다. **옛 툴체인은 이 머신에 없다** — 그래서 이 문서가 쓰는 레버는
「옛 컴파일러」가 아니라 「**같은 컴파일러에게 옛 언어 판으로 읽으라고 시키는 것**」이다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | 클로저가 잡은 변수의 **주소 자체** | 실행마다 힙이 다른 자리를 준다. 그래서 이 문서는 주소를 안 찍고 **「서로 다른 상자가 몇 개인가」** 만 센다 |
| **흔들린다** | 고루틴이 **뒤엉켜 찍는 순서** | 그래서 이 문서의 고루틴 예제는 채널로 순서를 못 박고 **정렬된 슬라이스**로 찍는다 |
| **흔들린다** | `-gcflags='-m -l'` 의 **줄·칸 번호와 항목 수** | 컴파일러 판이 바뀌면 달라진다. 읽을 것은 `moved to heap` 이라는 **낱말**이다 |
| 안 흔들린다 | 클로저의 **출력 값** (`3 3 3` 대 `0 1 2`) | 같은 소스·같은 언어 판이면 같다 |
| 안 흔들린다 | **서로 다른 상자의 개수** (1 대 3) | 주소는 바뀌어도 「같나 다르나」는 안 바뀐다 |
| 안 흔들린다 | 컴파일 에러·`go vet` 문장 본문과 `파일:줄:칸` | 같은 소스·같은 판이면 같다 |
| 안 흔들린다 | 종료 코드 | `go vet` 이 무엇을 찾으면 1, 아니면 0 |
| 해당 없음 | 맵 순회 순서 | 이 주제는 맵을 안 쓴다 |

## 한눈에 — 쉽게 말하면

**클로저는 값을 복사해 가는 것이 아니라 「그 변수가 사는 상자의 열쇠」를 복사해 간다.**

열쇠가 셋이어도 상자가 하나면 셋 다 같은 것을 본다.
1.22 가 고친 것은 **열쇠 쪽이 아니라 상자 쪽**이다 — 루프가 회차마다 상자를 새로 놓게 했다.

| 비유 | 실체 |
|---|---|
| 상자 | **변수** — 이름이 가리키는 저장 자리 |
| 열쇠를 복사해 간다 | **클로저가 변수를 캡처한다** — 값이 아니라 변수를 잡는다 |
| 상자가 하나 | 1.21까지의 `for` — 루프 전체가 변수 하나 |
| 회차마다 새 상자 | **1.22부터의 `for`** — 회차마다 자기 변수 |
| 상자를 손으로 하나 더 놓는다 | 옛 관용구 `i := i` — 지금도 필요한 자리가 남아 있다 |
| 상자가 방 밖으로 나가야 한다 | **탈출(escape)** — 클로저가 살아남으니 변수가 힙으로 간다 |

```text
   1.21 까지                            1.22 부터

   for i := 0; i < 3; i++               for i := 0; i < 3; i++
      +-------+                            +---+  +---+  +---+
      |  i    |  <- 상자 하나              | i |  | i |  | i |   <- 회차마다 하나
      +-------+                            +---+  +---+  +---+
       ^  ^  ^                               ^      ^      ^
       |  |  |                               |      |      |
      f0 f1 f2   셋 다 같은 것을 본다        f0     f1     f2

   루프 뒤 i = 3  →  f0()=f1()=f2()=3      각자 0 · 1 · 2 를 본다
```

> **클로저(closure)** — 바깥 스코프의 변수를 잡은 함수 값. 「함수 + 잡은 변수들」 한 덩어리다.\
> 예: `f := func() int { return x }` 의 `f` 는 **`x` 라는 변수**를 들고 다닌다. 그래서 `x` 를 고치면 `f()` 도 바뀐다.

> **캡처(capture)** — 클로저가 바깥 변수를 붙드는 것. Go 는 **값이 아니라 변수**를 붙든다.\
> 예: 한 변수를 클로저 둘이 잡으면 **둘이 서로의 수정을 본다**((1)절 `counter`).

> **루프 변수(loop variable)** — `for` 의 init 절이나 `range` 절이 `:=` 로 선언한 변수.\
> 예: `for i := 0; …` 의 `i`, `for _, v := range s` 의 `v`. **1.22가 바꾼 것은 정확히 이 둘뿐**이다.

> **탈출(escape)** — 지역 변수가 함수보다 오래 살아야 해서 스택이 아니라 힙에 놓이는 것.\
> 예: 클로저가 잡은 `x` 는 함수가 끝나도 살아야 하므로 `moved to heap: x` 가 된다((7)절).

- 파이썬과 다른 점 — 파이썬도 **변수를 잡는다.** 거기까지는 같다.
  그런데 파이썬의 `for` 는 스코프를 만들지 않아 **상자가 지금도 하나**다.
  Go 는 1.22에서 **상자 쪽을 고쳤고** 파이썬은 고친 적이 없다
  ([`../../../python/syntax/22-closures-and-late-binding/`](../../../python/syntax/22-closures-and-late-binding/)).
- 자바와 다른 점 — 자바 람다는 **effectively final** 한 지역 변수만 잡는다(사실상 값 복사).
  Go 는 그런 제약이 없어서 **잡은 변수를 클로저가 고칠 수 있다.**

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 클로저가 잡는 것은 **값인가 변수인가** — 그 답이 출력에서 어떻게 드러나나.
2. 1.22는 무엇을 바꿨나 — **클로저 쪽인가 루프 쪽인가**, 그리고 그 스위치는 어디에 있나.
3. 옛 관용구 `i := i` 는 이제 필요 없나 — **아직 필요한 자리가 어디인가.**

★ 「`defer` 의 인자가 언제 평가되나」는 이 주제가 아니다 —
[12번 주제](../12-functions-multiple-returns-named-results-and-variadics/)가 정본이다.
여기는 **그 규칙과 루프 변수가 만나는 자리**만 본다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

| 창 | 무엇을 보여 주나 | 한계 |
|---|---|---|
| 실행 출력 | 클로저 셋이 무엇을 찍나 | **왜 그런지는 안 보인다** — `3 3 3` 과 `0 1 2` 의 이유가 안 나온다 |
| ★★★ **언어 판 레버** — `go.mod` 의 `go` 지시어 · 파일의 `//go:build go1.N` | **같은 소스가 두 답을 내는 것** | 툴체인은 하나뿐이다. 이건 「옛 컴파일러」가 아니라 「옛 규칙」이다 |
| ★★ **상자 세기** — `&i` 를 모아 **서로 다른 개수**를 센다 | 값이 같아도 **상자가 몇 개인지** | 주소 자체는 흔들리므로 개수만 읽는다 |
| `go vet` · `-gcflags='-m -l'` | 도구가 이 코드를 어떻게 보나 | **도구는 보장이 아니다.** `vet` 이 침묵해도 옳다는 뜻이 아니다 |

★ 두 번째 창이 이 주제의 본체다. 첫 번째 창만으로는 **「지금 이 판에서는 이렇다」** 까지밖에 못 간다.

### (1) 클로저는 값이 아니라 변수를 잡는다

**언제 쓰나** — 함수 리터럴을 쓰는 모든 자리. 즉 Go 코드 거의 전부.

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

그림 해설 (한 단계씩):

- `f := func() int { return x }` 를 만든 **직후** `f()` 는 `10` 이다. 여기까지는 값을 복사해도 같다.
- 그런데 `x = 20` 을 하면 **`f()` 도 20**이 된다. `x = 30` 이면 30이다.
  **`f` 가 들고 있는 것은 10 이라는 값이 아니라 `x` 라는 변수**다.
- `counter()` 가 돌려준 `get` 과 `inc` 는 **같은 `n`** 을 본다. `inc()` 를 두 번 부르니 `get()` 이 2다.
- 그런데 `counter()` 를 **다시 부르면 새 `n`** 이다 — `get2()` 가 0이다.
  상자를 가르는 것은 **바깥 함수의 호출**이지 클로저를 만드는 일이 아니다.
- 명세가 한 문장으로 적는다.

  > **Function literals are closures: they may refer to variables declared in a surrounding
  > function. Those variables are then shared between the surrounding function and the function
  > literal, and they survive as long as they are accessible.**

★★ 「**shared**」와 「**survive**」 두 낱말이 이 절의 전부다. 공유되고, 살아남는다.

비용 — 잡힌 변수는 **힙으로 간다**((7)절에서 실측한다). 클로저 값 자체는 (코드 포인터, 캡처) 두 칸 정도다.

### (2) ★★★ 한 프로그램 · 한 번의 빌드 · 두 의미

**언제 쓰나** — 이 주제에서 **가장 중요한 절**이다. 「명세가 바뀌었다」를 눈으로 보는 자리다.

파일 첫머리에 `//go:build go1.21` 을 적으면 **그 파일 하나만** 언어 판이 1.21로 내려간다.
그래서 **같은 코드를 같은 패키지 안에 두 벌 두고 한 번에 빌드**할 수 있다.

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

그림 해설 (한 단계씩):

- 두 함수 `oldRules` 와 `newRules` 의 몸통은 **한 글자도 같다.** 갈린 것은 **파일 첫 줄 하나**다.
- 그런데 앞엣것은 `3 3 3`, 뒤엣것은 `0 1 2` 를 찍는다. **컴파일러도 하나, 빌드도 한 번이다.**
- ★ 그러니 이 차이는 **컴파일러의 성질도 최적화도 아니고 「언어 판」 그 자체**다.
- 명세가 그 둘을 나란히 적어 놓았다.

  > **Each iteration has its own separate declared variable (or variables) [Go 1.22].**
  > The variable used by the first iteration is declared by the init statement.
  > The variable used by each subsequent iteration is declared implicitly before executing
  > the post statement and initialized to the value of the previous iteration's variable at that moment.

  > **Prior to [Go 1.22], iterations share one set of variables instead of having their own separate variables.**

- ★★ 명세가 **자기 예제의 옛 출력까지 싣는다** — `1 3 5` 대 `6 6 6`.
  「명세가 바뀐 자리」라는 말을 명세 스스로 하고 있는 셈이다.

```text
   t13b.go                              t13c.go
   //go:build go1.21     <- 이 한 줄     (없다)
   package main                         package main
   ... 몸통이 같다 ...                   ... 몸통이 같다 ...

              go build -trimpath -o prog .   (한 번)
                            |
                            v
                  3 3 3     0 1 2
```

비용 — 없다. 두 판의 코드가 한 바이너리에 같이 들어간다.

### (3) ★★ 같은 레버를 `go.mod` 로 당기면

**언제 쓰나** — 실무에서 만나는 꼴이 이쪽이다. 남의 코드를 읽을 때 **먼저 `go.mod` 를 본다.**

같은 파일 `t13d.go` 를 `go.mod` 만 바꿔 두 번 던진다.

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

그림 해설 (한 단계씩):

- 소스는 **한 글자도 안 바꿨다.** `go.mod` 의 `go 1.21` 을 `go 1.22` 로 고쳤을 뿐이다.
- 출력이 `3 3 3` 에서 `0 1 2` 로 갈린다.
- ★★★ **「언어 의미가 모듈 파일에 적혀 있다」** 는 것이 이 주제가 남기는 가장 실용적인 사실이다.
  Go 코드를 읽을 때 **`for` 와 클로저가 만나면 `go.mod` 를 먼저 열어야 한다.**
- ★ `go.mod` 의 `go` 지시어는 **툴체인 버전이 아니라 언어 판**이다.
  go1.27.1 이 `go 1.21` 짜리 모듈을 **1.21 규칙으로** 컴파일해 준다.

### (4) ★★ 상자가 몇 개인가 — 값 말고 정체를 묻는다

**언제 쓰나** — 「값이 같은 것」과 「같은 변수인 것」을 갈라야 할 때.

`3 3 3` 이라는 출력만으로는 **상자가 하나여서인지 셋인데 다 3이어서인지** 알 수 없다.
그래서 `&i` 를 모아 **서로 다른 것이 몇 개인지** 센다. 주소는 안 찍는다(흔들리는 칸이다).

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

그림 해설 (한 단계씩):

- **go1.21 의미 — 서로 다른 상자가 1개**다. 셋이 전부 같은 변수를 가리킨다. 그래서 값도 `[3 3 3]` 이다.
- **go1.22 의미 — 상자가 3개**다. 값도 `[0 1 2]` 다.
- ★★ **이 한 줄이 「늦게 읽어서」가 아니라 「읽을 곳이 하나여서」임을 증명한다.**
  상자가 셋이었다면 아무리 늦게 읽어도 `0 1 2` 가 나왔을 것이다.
- 아래쪽 고루틴 실험은 **같은 사실을 수명이 긴 쪽에서** 본 것이다.
  고루틴 셋이 `close(start)` 를 기다렸다가 루프가 끝난 **뒤에** `i` 를 읽는다.
  1.21 의미에서는 그 하나뿐인 `i` 가 이미 3이라 `[3 3 3]`, 1.22 의미에서는 각자 자기 것을 읽어 `[0 1 2]` 다.
- ★ **이 고루틴 실험에는 경쟁이 없다.** `close` 와 수신이 happens-before 를 만들어서
  「루프의 마지막 쓰기」가 「고루틴의 읽기」보다 먼저인 것이 보장된다.
  **일부러 그렇게 짰다** — 안 그러면 출력이 실행마다 흔들려 근거가 못 된다.

```text
   1.21 의미                              1.22 의미

   ps[0] ─┐                               ps[0] ─> [i=0]
   ps[1] ─┼─> [ i ]  <- 상자 1개          ps[1] ─> [i=1]
   ps[2] ─┘   (루프 뒤 값 3)              ps[2] ─> [i=2]

   서로 다른 상자 개수 : 1                서로 다른 상자 개수 : 3
```

비용 — 회차마다 상자를 새로 놓으니 **회차마다 할당이 생길 수 있다.**
다만 **캡처가 없으면 컴파일러가 그 상자를 안 만든다** — 이 문서는 그 비용을 **재지 않았다.**

### (5) ★★ 옛 관용구 `i := i` 는 아직 필요한가 — 필요하다

**언제 쓰나** — 1.22 이후 코드를 읽으면서 「이 줄은 이제 지워도 되나」를 판단할 때.

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

그림 해설 (한 단계씩):

- ① **`for` 의 init 에서 선언한 변수** — `0 1 2`. 1.22가 고쳐 준 자리다.
- ② **`range` 의 변수** — `10 20 30`. 이것도 고쳐 준 자리다. 명세가 둘을 따로 적는다.

  > The iteration variables may be declared by the "range" clause using a form of short variable
  > declaration (`:=`). In this case their scope is the block of the "for" statement and
  > **each iteration has its own new variables [Go 1.22]**.

- ③ ★★★ **`for` 바깥에서 선언한 변수는 `3 3 3` 이다.** 1.22가 손대지 않은 자리다.
  `j := 0` 다음에 `for ; j < 3; j++` 이면 **`j` 는 루프의 변수가 아니다.**
  명세가 고친 것은 「**init 문이 선언한**」 변수이기 때문이다.
- ④ 그 자리를 옛 관용구로 고치면 다시 `0 1 2` 가 된다.
- ⑤ 루프가 아예 아닌 자리 — 클로저 둘이 한 변수를 본다. **이건 고쳐진 적이 없고 고칠 것도 아니다.**
  (1)절이 말한 「공유」가 그대로 쓸모인 자리다.
- ★★ 그러니 판단 규칙은 「**1.22 이후니까 `i := i` 를 다 지워도 된다**」가 아니라
  「**그 변수를 `for` 가 선언했나**」다.

비용 — ④의 `k := k` 는 회차마다 복사 하나. 잡히면 할당 하나.

### (6) ★ `defer` 와 클로저가 루프에서 만나면

**언제 쓰나** — 루프 안에서 `defer` 를 쓸 때. 두 규칙이 겹쳐 헷갈리는 자리다.

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

그림 해설 (한 단계씩):

- `defer fmt.Print("A", i, " ")` 는 **인자를 `defer` 를 적은 그 순간 평가**한다 → `A0`·`A1`·`A2`.
- `defer func() { … i … }()` 는 **몸통이 나갈 때** 돈다 → 그때 `i` 를 읽는다.
  1.22 이후에는 회차마다 `i` 가 따로라 **`B0`·`B1`·`B2`** 가 나온다.
- ★ 실행 순서는 **LIFO** 다. 그래서 `B2 A2 B1 A1 B0 A0` 순으로 찍힌다.
- ★★ **1.21 의미였다면 `B` 세 줄이 전부 `B3`** 이었을 것이다 — 같은 `i` 를 셋이 봤을 테니까.
  (여기서는 안 던졌다. 같은 갈림을 (2)~(4)절에서 이미 세 번 던졌다.)
- `defer` 의 두 꼴과 LIFO 자체의 정본은
  [12번 주제](../12-functions-multiple-returns-named-results-and-variadics/) (3)절이다.
  여기서는 **루프 변수와 겹치는 부분만** 본다.

비용 — `defer` 하나당 작은 고정 비용. 루프에서 쌓이면 함수가 끝날 때까지 안 돈다(26번 주제).

### (7) ★ 잡힌 변수는 힙으로 간다 — 구현이 보여 준다

**언제 쓰나** — 「왜 회차마다 새 변수를 만들어도 되나」의 비용 쪽이 궁금할 때.

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

그림 해설 (한 단계씩):

- `moved to heap: x` — `escapes` 안의 `x` 는 **함수가 끝난 뒤에도 살아야** 하므로 힙으로 갔다.
- `func literal escapes to heap` — 그 클로저 자체도 밖으로 나가니 힙이다.
- `func literal does not escape` — `stays` 의 클로저는 **그 자리에서 쓰고 버려** 탈출하지 않는다.
  **같은 모양의 코드인데 쓰이는 방식이 갈랐다.**
- ★★ 이것은 **구현(gc)의 관찰이지 명세 보장이 아니다.** 명세에는 스택도 힙도 없다 —
  「accessible 한 동안 survive 한다」까지만 약속한다. **어디에 두느냐는 컴파일러의 일이다.**
- ★ `-l` 을 붙여 인라인을 껐다. 안 끄면 `inlining call to …` 줄이 섞여 **읽을 줄이 묻힌다.**
  읽을 것은 줄 번호가 아니라 **`moved to heap` 이라는 낱말**이다.
- 탈출 분석 출력 읽기의 정본은 목록의 **52번 주제**다.

비용 — 힙 할당 하나 + GC 가 나중에 걷는 비용. **이 문서는 그 비용을 재지 않았다.**

### (8) ★ 도구는 무엇을 보나 — `go vet` 이 판을 안다

**언제 쓰나** — 「린터가 조용하니 괜찮겠지」를 의심할 때.

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

그림 해설 (한 단계씩):

- **같은 소스**다. `go.mod` 만 다르다.
- `go 1.21` 이면 `loop variable i captured by func literal` 이 나오고 **종료 코드가 1**이다.
- `go 1.27` 이면 **아무것도 안 나오고 종료 코드가 0**이다.
- ★★★ 두 번째 블록은 **출력이 한 줄도 없는 블록**이다. 그 「없음」이 곧 결론이다 —
  명령과 종료 코드까지 같이 실어야 **「도구가 침묵했다」와 「내가 안 돌렸다」가 구분**된다.
- ★★ 읽을 것은 이것이다 — **`vet` 은 언어 판을 보고 판단한다.**
  1.22부터는 그 패턴이 버그가 아니게 됐으므로 보고할 것이 없어진 것이지,
  「`vet` 이 못 잡는다」가 아니다.
- ★ 그리고 **`vet` 의 침묵은 보장이 아니다.** (5)절 ③의 「바깥에서 선언한 변수」는
  `go 1.27` 에서도 `3 3 3` 인데 `vet` 은 거기에도 조용하다.

비용 — 없다. `go test` 가 `vet` 의 일부를 자동으로 돌린다.

## 문법 — 형태와 규칙

### 형태

```go
// t13form.go
package main

import "fmt"

func main() {
	x := 1
	f := func() int { return x }      // ① 함수 리터럴 — 바깥 x 를 잡는다
	g := func(y int) int { return y } // ② 안 잡는다 — 클로저가 아니다
	adder := func() func(int) int {   // ③ 상태를 든 클로저를 만들어 돌려준다
		sum := 0
		return func(n int) int { sum += n; return sum }
	}
	acc := adder()
	func() { x = 2 }()    // ④ 즉시 실행 — 잡은 변수를 고친다
	go func() { _ = x }() // ⑤ go 문의 피연산자도 함수 리터럴이다
	defer func() { fmt.Println("⑥ defer 는 나갈 때 돈다 : x =", x) }()
	fmt.Println(f(), g(7), acc(1), acc(2))
}
```

```text
===== 소스: t13form.go =====
package main

import "fmt"

func main() {
	x := 1
	f := func() int { return x }      // ① 함수 리터럴 — 바깥 x 를 잡는다
	g := func(y int) int { return y } // ② 안 잡는다 — 클로저가 아니다
	adder := func() func(int) int {   // ③ 상태를 든 클로저를 만들어 돌려준다
		sum := 0
		return func(n int) int { sum += n; return sum }
	}
	acc := adder()
	func() { x = 2 }()    // ④ 즉시 실행 — 잡은 변수를 고친다
	go func() { _ = x }() // ⑤ go 문의 피연산자도 함수 리터럴이다
	defer func() { fmt.Println("⑥ defer 는 나갈 때 돈다 : x =", x) }()
	fmt.Println(f(), g(7), acc(1), acc(2))
}
===== 명령: go build -trimpath -o prog . && ./prog =====
2 7 1 3
⑥ defer 는 나갈 때 돈다 : x = 2
(exit 0)
```

규칙 불릿.

- **함수 리터럴은 `func` 키워드 + 시그니처 + 몸통**이고 이름이 없다. 값이므로 변수에 담고 넘기고 돌려준다.
- 바깥 변수를 **한 개라도 참조하면 클로저**다. 안 하면 그냥 익명 함수다.
- 잡는 것은 **변수이지 값이 아니다.** 잡힌 변수는 **바깥 함수와 공유**되고 **접근 가능한 동안 살아남는다.**
- **`for` 의 init 문과 `range` 절이 `:=` 로 선언한 변수는 회차마다 새것이다(1.22+).**
  그 밖의 변수는 아니다.
- `go func() { … }()` 와 `defer func() { … }()` 의 **괄호를 빼먹으면 함수 값만 만들고 안 부른다** —
  `go` 와 `defer` 는 **호출식**을 요구하므로 컴파일 에러가 된다.
- 언어 판을 내리는 두 레버 — **`go.mod` 의 `go` 지시어**(모듈 전체)와 **파일의 `//go:build go1.N`**(그 파일만).

### 금지 사례 — 컴파일러가 거부하는 것

이 주제에서 컴파일이 실패하는 자리는 **루프 변수 쪽이 아니다.**
1.21 이든 1.22 든 **양쪽 다 합법**이고, 그래서 **조용히 답만 갈린다** — 그것이 이 주제가 위험한 이유다.
컴파일러가 거부하는 것은 (2)~(4)절과 다른 축의 것들이다((8)절의 `go vet` 이 유일한 자동 경보였고,
그마저 1.22부터는 침묵한다).

## 어디서 틀리나

### 1. ★★★ 「1.22 부터니까 `i := i` 를 다 지워도 된다」

- (5)절 실측 — **`for` 바깥에서 선언한 변수는 지금도 `3 3 3`** 이다.
- 갈림의 기준은 「버전」이 아니라 「**그 변수를 `for` 가 선언했나**」다.
- 고치는 법 — `for ; cond; post` 꼴을 보면 멈추고 **선언이 어디 있는지** 본다.

### 2. ★★★ 「출력이 `3 3 3` 이니 늦게 읽어서다」 — 절반만 맞다

- (4)절 실측 — **서로 다른 상자가 1개**다. 늦게 읽는 것은 맞지만 **읽을 곳이 하나**인 것이 진짜 원인이다.
- 상자가 셋이었으면 아무리 늦게 읽어도 `0 1 2` 다 — 1.22 가 그것을 보였다.
- 고치는 법 — 「언제 읽나」가 아니라 「**몇 개를 보나**」를 물어라.

### 3. ★★ 「클로저는 값을 복사해 간다」 — 자바의 직관이다

- (1)절 실측 — `x = 20` 이 `f()` 에 **그대로 보인다.**
- 자바 람다는 effectively final 한 지역 변수만 잡아 **사실상 값**이다. Go 는 아니다.
- 고치는 법 — 값을 얼려야 하면 **인자로 넘기거나**(`func(v int){…}(x)`) **복사본을 만든다**(`v := x`).

### 4. ★★ 「`go vet` 이 조용하니 안전하다」

- (8)절 실측 — 같은 소스인데 `go.mod` 에 따라 **보고하기도 하고 안 하기도** 한다.
- 그리고 (5)절 ③처럼 **`vet` 이 원래 안 보는 자리**가 있다.
- 고치는 법 — 린터는 **알려진 패턴의 탐지기**이지 정확성 증명이 아니다.

### 5. ★★ 「`go.mod` 의 `go` 줄은 최소 툴체인 버전이다」

- (3)절 실측 — 그 줄이 **언어 의미를 고른다.** 툴체인은 go1.27.1 하나뿐인데 출력이 갈렸다.
- 오래된 모듈을 새 툴체인으로 빌드하면 **옛 규칙으로 컴파일된다.** 「새 컴파일러니까 새 규칙」이 아니다.
- 고치는 법 — 루프·클로저 버그를 볼 때 **`go.mod` 를 먼저 읽는다.**

### 6. ★ 「`go` 문의 클로저에 인자를 넘기는 것은 이제 촌스럽다」

- `go func(i int) { … }(i)` 는 1.22 이후에도 **틀리지 않는다.** 값을 그 자리에 얼리는 명시적 방법이다.
- 오히려 (5)절 ③ 같은 자리에서는 **그것만이 답**이다.
- 고치는 법 — 지우는 것이 목적이 아니다. **그 자리에서 무엇을 얼리는지**를 보고 판단한다.

### 7. ★ 「클로저가 상태를 드는 것은 사고다」

- (1)절의 `counter` 가 보이듯 **그것이 쓸모**다. 생성기·누산기·미들웨어가 전부 그 위에 선다.
- 위험한 것은 「공유」 자체가 아니라 **의도하지 않은 공유**다.
- 고치는 법 — **상자를 가르는 단위가 「바깥 함수의 호출」** 임을 기억한다((1)절 `get2`).

### 8. ★ 「루프 변수를 매 회차 새로 만드니 느려졌다」

- 이 문서는 **재지 않았다.** 캡처가 없으면 컴파일러가 상자를 안 만들지만 그것도 **안 쟀다.**
- 고치는 법 — 성능 주장을 하려면 벤치마크가 필요하다(목록의 **50번 주제**).

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| 함수 리터럴이 **바깥 변수를 공유**하고 **접근 가능한 동안 산다** | **1.0부터 보장** | "Function literals are closures … shared … survive as long as they are accessible" |
| **회차마다 자기 변수**(`for` init · `range` 변수) | **1.22부터의 보장** | "Each iteration has its own separate declared variable (or variables) [Go 1.22]" |
| **회차들이 변수 하나를 나눠 씀** | **1.21까지의 보장** | "Prior to [Go 1.22], iterations share one set of variables" |
| 새 회차의 변수가 **직전 회차 값으로 초기화**된다 | **1.22부터의 보장** | "…initialized to the value of the previous iteration's variable at that moment" |
| `for` **바깥**에서 선언한 변수는 안 갈라진다 | **양쪽 다 보장** | 명세가 고친 대상은 init 문과 `range` 절이 선언한 변수뿐이다 |
| `go.mod` 의 `go` 지시어가 **언어 판을 고른다** | **툴체인 계약**(명세 본문 아님) | (3)절 실측 · 에러 문구가 직접 말한다(14번 주제의 `-lang was set to …`) |
| `//go:build go1.N` 이 **그 파일만** 내린다 | **툴체인 계약** | (2)절 실측 |
| `moved to heap: x` · `escapes to heap` | **구현(gc)** | 명세에 스택·힙이라는 낱말이 없다 |
| `go vet` 이 `loop variable … captured` 를 보고한다 | **도구(구현)** | 1.22부터 침묵한다. 보장이 아니다 |
| 회차마다 **할당이 실제로 생기는가** | **구현 · 안 쟀다** | 캡처가 없으면 안 만들 수 있다. 이 문서는 측정 안 함 |

★ 이 주제의 결론은 「**클로저의 규칙은 안 바뀌었고 `for` 의 규칙이 바뀌었다**」이다.
그래서 고쳐진 자리와 안 고쳐진 자리가 **`for` 의 문법 경계에서 정확히 갈린다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 루프 안에서 고루틴을 띄움 | **1.22+ 면 그냥 캡처** | 회차마다 자기 변수다 |
| 그런데 `go.mod` 가 1.21 이하 | **인자로 넘긴다**(`go func(i int){…}(i)`) | 그 판에서는 상자가 하나다 |
| `for ; cond; post` 꼴 | **`v := v` 로 얼린다** | 1.22도 여기는 안 고쳤다 |
| 콜백에 지금 값을 얼리고 싶음 | **인자로 넘긴다** | 판과 무관하게 확실하다 |
| 상태를 든 생성기·누산기 | **클로저가 정답** | 공유가 쓸모인 자리다 |
| 상태를 여러 벌 만들어야 함 | **팩토리 함수를 다시 부른다** | 상자를 가르는 단위가 호출이다 |
| 잡은 변수를 여러 고루틴이 쓴다 | **캡처 말고 동기화** | 캡처는 공유다 — 경쟁이 그대로 남는다(35번 주제) |
| 오래된 모듈을 새 툴체인으로 빌드 | **`go.mod` 를 먼저 읽는다** | 툴체인이 새것이어도 규칙은 옛것이다 |

판단 규칙 두 줄.

- **「이 변수를 누가 선언했나」를 먼저 물어라.** `for` 가 선언했으면 1.22가 갈라 주고, 아니면 안 갈라 준다.
- **공유가 사고인지 쓸모인지 가려라.** 같은 기계가 생성기에서는 답이고 루프에서는 함정이었다.

## 핵심 문장

- 클로저가 잡는 것은 **값이 아니라 변수**다. 명세의 낱말이 `shared` 와 `survive` 다.
- 1.22가 고친 것은 **클로저가 아니라 `for`** 다 — 회차마다 변수를 새로 만들게 했다.
- ★★★ **같은 소스가 `go.mod` 한 줄로 `3 3 3` 과 `0 1 2` 로 갈린다.**
  그러니 Go 코드를 읽을 때 **루프 + 클로저를 보면 `go.mod` 를 연다.**
- 출력이 `3 3 3` 인 이유는 「늦게 읽어서」가 아니라 **「읽을 상자가 하나여서」** 다 —
  서로 다른 상자 개수가 **1 대 3**으로 그것을 증명한다.
- **`i := i` 는 아직 필요하다.** `for` 바깥에서 선언한 변수는 1.22가 손대지 않았다.
- **`go vet` 은 언어 판을 보고 말한다.** 1.21 이면 보고하고 1.22 이상이면 침묵한다 — 침묵은 보장이 아니다.
- 잡힌 변수는 **힙으로 간다**(`moved to heap`) — 그러나 그건 **구현이지 명세가 아니다.**
- 파이썬도 변수를 잡는다. 다른 것은 **파이썬의 `for` 가 상자를 안 가른다**는 것이고, 지금도 그렇다.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 13번)
- [12번 주제](../12-functions-multiple-returns-named-results-and-variadics/)(함수·다중 반환·`defer`) —
  **그쪽은 `defer` 의 평가 시점과 LIFO·명명 반환값까지**, 여기는 **그 규칙이 루프 변수와 겹치는 자리**부터
- [14번 주제](../14-for-four-forms-range-over-int-and-func/)(`for` 의 네 형태·`range`) — **`for` 문법 자체의 정본.**
  이 주제는 그중 「변수가 몇 개인가」 한 축만 본다
- [목록의 **26번 주제**](../26-defer-evaluation-lifo-named-results-and-loops/)(`defer` 의 평가 시점·루프 안의 `defer`) — 루프에서 `defer` 가 쌓이는 문제의 정본
- [목록의 **28번 주제**](../28-goroutines-go-statement-cost-and-termination/)(고루틴) · **35번 주제**(데이터 레이스와 `-race`) —
  **그쪽은 경쟁 자체까지**, 여기는 **캡처가 그 경쟁을 만드는 자리**까지
- 목록의 **52번 주제**(도구·탈출 분석 읽기) — `-gcflags=-m` 출력 읽기의 정본
- [`../../../python/syntax/22-closures-and-late-binding/`](../../../python/syntax/22-closures-and-late-binding/) —
  **그쪽은 셀(cell)을 `is` 로 들여다보며 「상자가 하나」를 증명하고**,
  여기는 **언어가 그 상자를 갈라 준 판과 안 갈라 준 판을 나란히** 던진다.
  ★ 파이썬은 이것을 **고친 적이 없다** — 고침이 사용자 쪽(팩토리·기본 인자)에 남아 있다
- [`../../../java/syntax/README.md`](../../../java/syntax/README.md) — 자바 람다의 effectively final 제약(해당 주제가 생기면 여기서 잇는다)

## 용어 풀이

- **클로저(closure)** — 바깥 스코프의 변수를 잡은 함수 값. 명세의 낱말은 "function literals are closures" 다.
- **캡처(capture)** — 클로저가 바깥 변수를 붙드는 것. Go 는 변수 자체를 붙든다.
- **함수 리터럴(function literal)** — 이름 없는 함수 식. `func(…) … { … }`.
- **루프 변수(loop variable)** — `for` 의 init 문이나 `range` 절이 `:=` 로 선언한 변수.
- **언어 판(language version)** — 컴파일러가 어느 판의 규칙으로 읽을지. `go.mod` 의 `go` 지시어가 정한다.
- **빌드 제약(build constraint)** — 파일 첫머리의 `//go:build …`. `go1.N` 을 적으면 그 파일의 언어 판이 된다.
- **탈출 분석(escape analysis)** — 변수를 스택에 둘지 힙에 둘지 컴파일러가 판정하는 것.
- **effectively final** — 자바의 규칙. 한 번 대입한 뒤 안 바뀌는 지역 변수만 람다가 잡을 수 있다. Go 에는 없다.
- **happens-before** — 한 연산이 다른 연산보다 먼저임이 보장되는 관계. `close` 와 수신이 그것을 만든다.

---

## 더 들어가면

- 명세가 실은 **옛 규칙의 출력까지 문서에 남겨 두었다** — 같은 예제가 `1 3 5` 와 `6 6 6` 으로 갈린다.
  명세가 「과거의 자기 자신」을 인용하는 드문 자리다.
- 1.22의 정의는 「회차마다 새 변수」로 끝나지 않는다 — **새 변수는 직전 회차 변수의 값으로 초기화**되고,
  그 복사가 **post 문 직전**에 일어난다. 그래서 루프 안에서 `i++` 을 한 번 더 해도 명세 예제처럼 값이 이어진다.
- 1.22 전환기에 `GOEXPERIMENT=loopvar` 라는 스위치가 있었다(1.21). 지금은 필요 없다 —
  이 툴체인에서는 `go.mod` 와 `//go:build` 두 레버로 충분하다. 그 실험 플래그는 **이 문서에서 안 던졌다.**
- `//go:build go1.N` 은 원래 **빌드 제약**(그 판 이상에서만 이 파일을 넣어라)인데,
  1.21부터 **언어 판을 내리는 부수 효과**까지 갖게 됐다. 한 문법이 두 일을 한다.
- 클로저가 **자기 자신을 재귀 호출**하려면 변수를 먼저 선언해야 한다 —
  `var f func(int) int` 를 적고 `f = func(n int) int { … f(n-1) … }` 로 채운다.
  `f := func(...) { f(...) }` 는 `f` 가 아직 스코프에 없어 컴파일 에러다. **여기서는 안 던졌다.**
- 메서드 값(`x.M`)도 리시버를 **잡아 둔 함수 값**이라 클로저와 같은 집안이다
  ([12번 주제](../12-functions-multiple-returns-named-results-and-variadics/) (6)절).

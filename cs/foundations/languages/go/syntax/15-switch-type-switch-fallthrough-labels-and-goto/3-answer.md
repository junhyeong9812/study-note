# go/syntax/15 — `switch`·타입 스위치·`fallthrough`·라벨·`goto` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> 블록은 전부 `===== 소스: … =====` 로 소스를 먼저 싣는다 — **그대로 다시 던질 수 있게** 하기 위해서다.
> ★ **근거로 읽을 칸** — 실행 출력, 에러 문장 본문과 `파일:줄:칸`, 종료 코드.
> **이 주제에는 근거로 읽지 않을 칸이 없다** — 주소도 시간도 맵도 고루틴도 안 나온다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `one` / `two three` / `three` / `four` / `other` — 그리고 99가 돈다

**출력**

```text
===== 소스: t15a.go =====
package main

import "fmt"

func run(x int) {
	fmt.Printf("x=%d : ", x)
	switch x {
	case 1:
		fmt.Print("one ")
	case 2:
		fmt.Print("two ")
		fallthrough
	case 3:
		fmt.Print("three ")
	case 4:
		fmt.Print("four ")
	default:
		fmt.Print("other ")
	}
	fmt.Println()
}

func main() {
	for i := 1; i <= 5; i++ {
		run(i)
	}
	fmt.Println()
	fmt.Println("fallthrough 는 다음 case 의 조건을 보지 않는다")
	switch 1 {
	case 1:
		fmt.Println("  case 1 몸통")
		fallthrough
	case 99:
		fmt.Println("  case 99 몸통 — 1 != 99 인데 들어왔다")
	}
}
===== 명령: go build -trimpath -o prog . && ./prog =====
x=1 : one 
x=2 : two three 
x=3 : three 
x=4 : four 
x=5 : other 

fallthrough 는 다음 case 의 조건을 보지 않는다
  case 1 몸통
  case 99 몸통 — 1 != 99 인데 들어왔다
(exit 0)
```

**왜 그런가**

- `x=1` 은 **`one` 하나**다. `break` 를 안 썼는데도 `case 2:` 로 안 내려간다.
  명세가 **그쪽을 기본값**으로 골랐다.

  > … Otherwise **control flows to the end of the "switch" statement.**

- `x=2` 는 **`two three`** 다 — `fallthrough` 라고 **적었기** 때문이다.
- `x=3` 은 **`three` 하나**다. 그 가지에는 `fallthrough` 가 없다.
- ★★★ 아래 덩어리 — `switch 1` 에서 `case 1:` 이 `fallthrough` 하자 **`case 99:` 의 몸통이 돌았다.**
  1과 99는 같지 않다. 명세의 문장이 그 이유다.

  > In a case or default clause, the last non-empty statement may be a (possibly labeled)
  > "fallthrough" statement to indicate that **control should flow from the end of this clause
  > to the first statement of the next clause.**

  ★ 「**the first statement of the next clause**」— **몸통**으로 간다고 적혀 있지 조건을 본다고 안 적혀 있다.
- 층 — 전부 **명세 보장**이다.

### 2. `A B C` / 모음 셋 / 나머지 1 / `x+y = 7` / 빈 `case` 를 지나감

**출력**

```text
===== 소스: t15b.go =====
package main

import "fmt"

func grade(n int) string {
	switch { // ① 조건 없는 switch — case 가 bool 식이다
	case n >= 90:
		return "A"
	case n >= 80:
		return "B"
	default:
		return "C"
	}
}

func main() {
	fmt.Println("① 조건 없는 switch :", grade(95), grade(85), grade(10))

	// ② case 에 값 여러 개
	for _, c := range []rune{'a', 'e', 'z'} {
		switch c {
		case 'a', 'e', 'i', 'o', 'u':
			fmt.Printf("② %q 는 모음\n", c)
		default:
			fmt.Printf("② %q 는 모음 아님\n", c)
		}
	}

	// ③ init 문이 붙은 switch — 그 변수는 switch 안에서만 산다
	switch v := 7 % 3; v {
	case 0:
		fmt.Println("③ 나누어떨어진다", v)
	case 1, 2:
		fmt.Println("③ 나머지가 있다 :", v)
	}

	// ④ case 는 상수가 아니어도 된다
	x, y := 3, 4
	switch 7 {
	case x + y:
		fmt.Println("④ case 에 식을 써도 된다 : x+y =", x+y)
	}

	// ⑤ 빈 case 는 「아무것도 안 함」이다 — C 처럼 흘러내리지 않는다
	switch 2 {
	case 2:
	case 3:
		fmt.Println("⑤ 여기는 안 온다")
	}
	fmt.Println("⑤ 빈 case 2 를 지나 여기로 왔다")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
① 조건 없는 switch : A B C
② 'a' 는 모음
② 'e' 는 모음
② 'z' 는 모음 아님
③ 나머지가 있다 : 1
④ case 에 식을 써도 된다 : x+y = 7
⑤ 빈 case 2 를 지나 여기로 왔다
(exit 0)
```

**왜 그런가**

- ① **`switch { }` 는 `switch true { }`** 다. 명세:
  "**A missing switch expression is equivalent to the boolean value true.**"
  그래서 `case n >= 90:` 이 성립한다 — `if`-`else if` 사슬의 다른 꼴이다.
- ② `case 'a', 'e', 'i', 'o', 'u':` 는 「또는」이다.
- ③ init 문의 변수는 **`switch` 안에서만** 산다. `7 % 3` 이 1이라 `case 1, 2:` 가 걸렸다.
- ④ ★ **`case` 가 상수가 아니어도 된다.** 명세:
  "the case expressions, **which need not be constants**, are evaluated left-to-right and top-to-bottom".
  **C 와 갈리는 자리다** — C 의 `case` 는 정수 상수식이어야 하고,
  `const int K = 3;` 조차 gcc 에서 `error: case label does not reduce to an integer constant` 다.
- ⑤ **빈 `case` 는 아무것도 안 한다.** `case 3:` 의 몸통은 **안 돈다** —
  C 라면 흘러내려 「⑤ 여기는 안 온다」가 찍혔을 자리다.
- 층 — 전부 **명세 보장**이다.

### 3. ★★ 일곱 줄 — `myInt` 는 `Stringer` 가지에 걸린다

**출력**

```text
===== 소스: t15c.go =====
package main

import "fmt"

type Stringer interface{ String() string }
type myInt int

func (m myInt) String() string { return fmt.Sprintf("myInt(%d)", int(m)) }

func describe(x any) {
	switch v := x.(type) {
	case nil:
		fmt.Printf("  nil          : v=%v  타입=%T\n", v, v)
	case int:
		fmt.Printf("  int          : v+1=%v 타입=%T\n", v+1, v)
	case string:
		fmt.Printf("  string       : len=%d 타입=%T\n", len(v), v)
	case []int:
		fmt.Printf("  []int        : cap=%d 타입=%T\n", cap(v), v)
	case float64, bool:
		fmt.Printf("  여러 타입     : v=%v 타입=%T\n", v, v)
	case Stringer:
		fmt.Printf("  Stringer     : v.String()=%s 타입=%T\n", v.String(), v)
	default:
		fmt.Printf("  default      : v=%v 타입=%T\n", v, v)
	}
}

func main() {
	fmt.Println("v 의 타입이 가지마다 다르다")
	describe(nil)
	describe(7)
	describe("가나")
	describe(make([]int, 1, 5))
	describe(myInt(3))
	describe(3.5)
	describe([2]int{1, 2})

	var a any = "문자열"
	s, ok := a.(string)
	fmt.Printf("comma-ok 꼴 : s=%q ok=%v\n", s, ok)
	n, ok2 := a.(int)
	fmt.Printf("실패하면     : n=%d ok=%v\n", n, ok2)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
v 의 타입이 가지마다 다르다
  nil          : v=<nil>  타입=<nil>
  int          : v+1=8 타입=int
  string       : len=6 타입=string
  []int        : cap=5 타입=[]int
  Stringer     : v.String()=myInt(3) 타입=main.myInt
  여러 타입     : v=3.5 타입=float64
  default      : v=[1 2] 타입=[2]int
comma-ok 꼴 : s="문자열" ok=true
실패하면     : n=0 ok=false
(exit 0)
```

**왜 그런가**

| 인자 | 걸린 가지 | `%T` | 그 가지에서 `v` 의 **정적** 타입 |
|---|---|---|---|
| `nil` | `case nil:` | `<nil>` | `any`(`x` 의 타입 그대로) |
| `7` | `case int:` | `int` | **`int`** — 그래서 `v+1` 이 컴파일된다 |
| `"가나"` | `case string:` | `string` | **`string`** — `len(v)` 가 6(바이트) |
| `make([]int,1,5)` | `case []int:` | `[]int` | **`[]int`** — `cap(v)` 가 5 |
| `myInt(3)` | **`case Stringer:`** | `main.myInt` | **`Stringer`** — `v.String()` 이 된다 |
| `3.5` | `case float64, bool:` | `float64` | ★ **`any`** — 타입이 둘이라 안 좁혀진다 |
| `[2]int{1,2}` | `default:` | `[2]int` | `any` |

- ★★★ **같은 이름 `v` 가 가지마다 다른 타입**이다. 명세:

  > The TypeSwitchGuard may include a short variable declaration. When that form is used,
  > **the variable is declared at the end of the TypeSwitchCase in the implicit block of each clause.**
  > **In clauses with a case listing exactly one type, the variable has that type;
  > otherwise, the variable has the type of the expression in the TypeSwitchGuard.**

- `myInt(3)` 이 `case Stringer:` 에 걸린 이유 — 위에서 아래로 보다가 **처음 맞는 것**이 이기고,
  `myInt` 는 `int`·`string`·`[]int`·`float64`·`bool` 어느 것도 아니며 `String()` 을 갖는다.
  ★ **가지 순서가 의미를 갖는 자리**다. `case Stringer:` 를 맨 위에 뒀으면 `int` 가 아닌 것들이 다 거기 걸렸을 것이다.
- ★★ `3.5` 가 걸린 가지에서 `v` 의 **정적** 타입은 **`any`** 다.
  그런데 `%T` 는 **`float64`** 를 찍는다 — `%T` 가 보는 것은 **동적 타입**이기 때문이다.
  **정적 타입은 `%T` 로 못 본다.** 7번의 `t15i.go` 에러가 그것을 보여 준다.
- 마지막 두 줄 — comma-ok 단언은 실패해도 **패닉하지 않고** 제로값과 `false` 를 준다.
  정본은 목록의 **22번 주제**다.
- 층 — 전부 **명세 보장**이다.

### 4. ★★★ 컴파일된다 · 실행된다 · 경고 0건 — 그리고 `weight` 가 0을 돌려준다

**출력**

```text
===== 소스: t15d.go =====
package main

import "fmt"

type Event int

const (
	Click Event = iota
	Key
	Scroll
	Drag // ← 나중에 늘린 변형. 아래 switch 는 한 글자도 안 고쳤다.
)

func label(e Event) string {
	switch e {
	case Click:
		return "클릭"
	case Key:
		return "키"
	case Scroll:
		return "스크롤"
	}
	return "(여기로 떨어졌다)"
}

func weight(e Event) int {
	switch e {
	case Click:
		return 1
	case Key:
		return 2
	case Scroll:
		return 3
	}
	return 0
}

func main() {
	for _, e := range []Event{Click, Key, Scroll, Drag} {
		fmt.Printf("%d : label=%-14s weight=%d\n", e, label(e), weight(e))
	}
	fmt.Println("컴파일도 되고 실행도 된다 — 에러도 경고도 없다")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
0 : label=클릭             weight=1
1 : label=키              weight=2
2 : label=스크롤            weight=3
3 : label=(여기로 떨어졌다)     weight=0
컴파일도 되고 실행도 된다 — 에러도 경고도 없다
(exit 0)
```

**왜 그런가**

- **에러도 경고도 없다.** `Drag` 는 `label` 에서 `(여기로 떨어졌다)`, `weight` 에서 **`0`** 을 받는다.
- ★★★ Rust 에서 같은 실험을 하면 **`error[E0004]` 가 네 개** 난다
  (`match` 자리 하나에 하나씩). 그 실측이
  [`../../../rust/syntax/18-match-and-exhaustiveness/`](../../../rust/syntax/18-match-and-exhaustiveness/) (3)절이다 —
  `error: aborting due to 4 previous errors` 로 끝난다.
- ★★ **Go 에는 그 검사 자체가 없다.** 이유는 `iota` 열거가 **타입이 아니라 그냥 정수**여서다.
  컴파일러 입장에서 「가능한 값이 넷」이라는 사실이 없다 — `Event(99)` 도 완벽히 합법이다.
  ([03번 주제](../03-constants-iota-and-untyped-constants/)가 `iota` 의 정본이다.)
- Go 에서 이 자리를 막는 것은 **언어가 아니라 습관**이다 —
  `default:` 에서 **패닉하거나 오류를 내는** 것. 「조용히 0을 돌려주는」 것이 사고의 씨앗이다.
  외부 린터(`exhaustive` 류)도 있지만 **이 문서는 안 돌렸다** — 이 툴체인에 없다.
- ★ Rust 문서의 결론 「`_` 는 짧게 쓰는 법이 아니라 **안전망을 끄는 스위치**다」를 Go 로 옮기면
  「**안전망이 처음부터 없다**」가 된다. 같은 실험에서 깨지는 자리가 Rust 는 `4 → 0`(`_` 를 넣으면),
  Go 는 **처음부터 0**이다.
- 층 — 「검사가 없다」는 **명세 보장**(없음의 보장)이다. 어느 Go 컴파일러도 이걸 막으면 안 된다.

### 5. `0 1 2` / `0` / `00 10 20` / `00 01 02 10` / `00 10 20`

**출력**

```text
===== 소스: t15e.go =====
package main

import "fmt"

func main() {
	fmt.Println("① switch 안의 break 는 switch 만 끝낸다")
	for i := 0; i < 3; i++ {
		switch i {
		case 1:
			break // 루프가 아니라 switch 를 끝낸다
		}
		fmt.Print(i, " ")
	}
	fmt.Println("<- 1 도 찍혔다")

	fmt.Println("② 라벨을 달면 루프를 끝낸다")
loop:
	for i := 0; i < 3; i++ {
		switch i {
		case 1:
			break loop
		}
		fmt.Print(i, " ")
	}
	fmt.Println("<- 1 에서 루프가 끝났다")

	fmt.Println("③ 중첩 루프 — break 는 안쪽만 끝낸다")
	for i := 0; i < 3; i++ {
		for j := 0; j < 3; j++ {
			if j == 1 {
				break
			}
			fmt.Print(i, j, " ")
		}
	}
	fmt.Println()

	fmt.Println("④ 라벨 break 는 바깥까지 끝낸다")
outer:
	for i := 0; i < 3; i++ {
		for j := 0; j < 3; j++ {
			if i == 1 && j == 1 {
				break outer
			}
			fmt.Print(i, j, " ")
		}
	}
	fmt.Println()

	fmt.Println("⑤ 라벨 continue 는 바깥 루프의 다음 회차로 간다")
next:
	for i := 0; i < 3; i++ {
		for j := 0; j < 3; j++ {
			if j == 1 {
				continue next
			}
			fmt.Print(i, j, " ")
		}
		fmt.Print("(여기는 안 온다)")
	}
	fmt.Println()
}
===== 명령: go build -trimpath -o prog . && ./prog =====
① switch 안의 break 는 switch 만 끝낸다
0 1 2 <- 1 도 찍혔다
② 라벨을 달면 루프를 끝낸다
0 <- 1 에서 루프가 끝났다
③ 중첩 루프 — break 는 안쪽만 끝낸다
0 0 1 0 2 0 
④ 라벨 break 는 바깥까지 끝낸다
0 0 0 1 0 2 1 0 
⑤ 라벨 continue 는 바깥 루프의 다음 회차로 간다
0 0 1 0 2 0 
(exit 0)
```

**왜 그런가**

- ① ★★ **`switch` 안의 `break` 는 `switch` 를 끝낸다.** 그래서 `i == 1` 에서 `break` 했는데도
  그 아래 `fmt.Print(i, " ")` 가 돌아 **`1` 이 찍힌다.** C 에서 온 직관이 여기서 뒤집힌다.
- ② `break loop` 는 **루프**를 끝낸다. `0` 만 찍고 나온다.
- ③ 중첩 루프에서 `break` 는 **가장 안쪽 하나**만 끝낸다. 명세:

  > A "break" statement terminates execution of the **innermost** enclosing "for", "switch"
  > or "select" statement within the same function.

  그래서 바깥 루프는 세 번 다 돌아 `00 10 20` 이 나온다.
- ④ `break outer` 는 **바깥까지** 끝낸다 — `i==1 && j==1` 에서 멈춰 `00 01 02 10` 이다.
- ⑤ `continue next` 는 **바깥 루프의 다음 회차**로 간다. 그래서 `(여기는 안 온다)` 가 **안 찍힌다.**
  `continue` 는 `for` 에만 붙는다.
- 층 — 전부 **명세 보장**이다.

### 6. 네 줄 — ②는 루프가 되고 ④는 에러가 아니다

**출력**

```text
===== 소스: t15h.go =====
package main

import "fmt"

func main() {
	// ① 앞으로 뛴다 — 선언을 안 건너뛰면 된다
	i := 0
	if i == 0 {
		goto forward
	}
	fmt.Println("건너뛴다")
forward:
	fmt.Println("① 앞으로 뛰었다")

	// ② 뒤로 뛴다 — 루프가 된다
back:
	i++
	if i < 3 {
		goto back
	}
	fmt.Println("② 뒤로 뛰어 i =", i)

	// ③ 블록 밖으로 나온다
	for j := 0; j < 3; j++ {
		if j == 1 {
			goto out
		}
	}
out:
	fmt.Println("③ 블록 밖으로 나왔다")

	// ④ 선언을 건너뛰어도 그 선언이 **블록 안**에 있으면 된다
	if i == 3 {
		goto tail
	}
	{
		w := 1
		fmt.Println(w)
	}
tail:
	fmt.Println("④ 블록 안의 선언은 건너뛸 수 있다")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
① 앞으로 뛰었다
② 뒤로 뛰어 i = 3
③ 블록 밖으로 나왔다
④ 블록 안의 선언은 건너뛸 수 있다
(exit 0)
```

**왜 그런가**

- ① **앞으로** 뛰어 `건너뛴다` 를 건너뛴다.
- ② **뒤로** 뛰면 루프가 된다 — `i` 가 3이 될 때까지 돈다.
- ③ `for` 블록 **밖으로** 나온다.
- ④ ★ 선언 `w := 1` 을 건너뛰는데 **에러가 아니다.**
  그 선언이 **중괄호 블록 안**에 있어서, `tail:` 자리에서는 `w` 가 **애초에 스코프에 없기** 때문이다.
  명세가 막는 것은 「`goto` 지점에 **없던 변수가 스코프에 들어오는** 것」이다.

  > **Executing the "goto" statement must not cause any variables to come into scope
  > that were not already in scope at the point of the goto.**

- 라벨은 **함수 단위**다. 다른 함수의 라벨로는 못 뛴다.
  그리고 라벨 이름은 **변수와 다른 이름 공간**이라 같은 이름을 써도 충돌하지 않는다.
- 층 — 전부 **명세 보장**이다.

### 7. 여덟 가지 거부 — 그리고 하나만 구현 제약이다

**출력**

```text
===== 소스: t15g.go =====
package main

import "fmt"

func main() {
	switch 1 {
	case 1:
		fmt.Println("one")
		fallthrough
	}

	switch 1 {
	case 1:
	case 1:
	}

	var a any = 1
	switch v := a.(type) {
	case int:
		fmt.Println(v)
		fallthrough
	case string:
		fmt.Println(v)
	}

	switch "가" {
	case 1:
	}

	var b any = 1
	switch b.(type) {
	case int:
	case int:
	}
}
===== 명령: go build -trimpath -o prog . =====
# ex
./t15g.go:9:3: cannot fallthrough final case in switch
./t15g.go:14:7: duplicate case 1 (constant of type int) in expression switch
	./t15g.go:13:7: previous case
./t15g.go:21:3: cannot fallthrough in type switch
./t15g.go:27:7: cannot convert 1 (untyped int constant) to type string
./t15g.go:33:7: duplicate case int in type switch
	./t15g.go:32:7: previous case
(exit 1)
```

```text
===== 소스: t15i.go =====
package main

import "fmt"

func main() {
	var a any = 3.5
	switch v := a.(type) {
	case float64:
		fmt.Println(v + 1) // ① 가지가 하나면 v 는 float64 다
	case int, bool:
		fmt.Println(v + 1) // ② 가지가 둘이면 v 는 any 그대로다
	}
}
===== 명령: go build -trimpath -o prog . =====
# ex
./t15i.go:11:15: invalid operation: v + 1 (mismatched types any and untyped int)
(exit 1)
```

```text
===== 소스: t15j.go =====
package main

import "fmt"

func main() {
	x := 2
	switch x {
		v := 99 // switch 몸통에는 case·default 말고 아무것도 못 온다
	case 1:
		fmt.Println(v)
	}
}
===== 명령: go build -trimpath -o prog . =====
# ex
./t15j.go:8:3: syntax error: unexpected name v, expected case or default or }
./t15j.go:9:2: syntax error: unexpected keyword case, expected :
(exit 1)
```

**왜 그런가**

| 메시지 | 층 | 근거 |
|---|---|---|
| `cannot fallthrough final case in switch` | **명세 보장** | "may appear as the last statement of **all but the last clause**" |
| `duplicate case 1 (constant of type int) in expression switch` | ★ **구현** | "Implementation restriction: **A compiler may disallow** multiple case expressions evaluating to the same constant" |
| `cannot fallthrough in type switch` | **명세 보장** | 명세가 `fallthrough` 를 **expression switch** 에만 정의한다 |
| `cannot convert 1 (untyped int constant) to type string` | **명세 보장** | "If a case expression is untyped, it is first implicitly converted to the type of the switch expression" |
| `duplicate case int in type switch` | **명세 보장** | "The types listed in the cases of a type switch **must all be different**" |
| `invalid operation: v + 1 (mismatched types any and untyped int)` | **명세 보장** | 가지에 타입이 둘 이상이면 `v` 는 원래 타입이다 |
| `syntax error: unexpected name v, expected case or default or }` | **명세 보장**(문법) | `ExprSwitchStmt = "switch" … "{" { ExprCaseClause } "}"` |

- ★ **`t15i.go` 의 두 `v + 1` 중 위쪽만 된다.**
  `case float64:` 는 타입이 **정확히 하나**라 `v` 가 `float64` 로 좁혀지고,
  `case int, bool:` 은 **둘**이라 `v` 가 `any` 그대로다. 3번이 `%T` 로는 못 보여 준 것이 여기서 보인다.
- ★★★ **`t15j.go` 의 에러는 `syntax error`** 다 — 타입 검사 이전, **문법 단계**에서 막힌다.
  C 는 같은 코드를 **받아 놓고 경고만** 한다(`warning: statement will never be executed` +
  `warning: 'v' is used uninitialized`) — 그리고 그 변수가 **쓰레기값**을 갖는다
  (gcc `32764` · clang `32765`, C 쪽 (7)절 실측).
  **Go 에서는 그 사고 자체가 문법적으로 불가능하다.**
- 종료 코드는 셋 다 **1**이다.

### 8. C 에서 `case` 는 라벨이다 — Go 는 그 성질을 버렸다

**출력** — 없음(왜 문항). 근거는 1번의 출력과 C 쪽 실측이다.

**왜 그런가**

- C 에서 `case` 는 **문이 아니라 라벨**이다 — `goto` 의 `out:` 과 같은 종류다.
  그래서 `switch` 는 「고르는 것」이 아니라 「**뛰는 것**」이고, 뛴 뒤에는 아래로 계속 흐른다.
  ★ 그 성질의 가장 강한 증거가 **Duff's device** 다 —
  `do { } while` 의 몸통 **안쪽에 `case` 라벨이 박힌다**(C 쪽 (4)절).
- Go 는 그 성질을 버렸다. 가지는 **`switch` 의 직계 자식**이어야 하고(7번의 `syntax error` 가 그 증거),
  한 가지만 돌고 끝난다.
- **잃은 것** — Duff's device 같은 기교가 불가능해졌고, 여러 가지를 묶어 흘려보내는 패턴이
  **`fallthrough` 를 줄마다 적는 꼴**이 됐다. 다만 「여러 값을 한 가지에 묶기」는 `case 1, 2, 3:` 이 대신한다.
- **`fallthrough` 가 조건을 안 보는 것**도 같은 선택의 결과다 —
  Go 의 `fallthrough` 는 「C 의 흘러내림을 한 줄로 재현하는 장치」이지 새 매칭이 아니다.
  C 에서도 흘러내릴 때 다음 `case` 의 값을 검사하지 않는다.
- **C 에서 흘러내림 실수를 막는 장치**는 `-Wimplicit-fallthrough` 다.
  ★ 그런데 **기본으로 안 켜져 있다** — C 쪽 실측에서
  `gcc -Wall` 은 **0건**, `-Wextra` 를 붙여야 1건, `clang -Wall -Wextra` 도 **0건**이고
  `clang -Wimplicit-fallthrough` 를 직접 켜야 2건이 나왔다.
  ★★ 그러니 **C 는 「위험한 기본값 + 꺼져 있는 경고」** 이고 Go 는 **「안전한 기본값 + 명시적 예외」** 다.

### 9. 된다 — `case` 가 `nil` 뿐이면

**출력**

```text
===== 소스: t15k.go =====
package main

import "fmt"

func main() {
	s := []int{1}
	switch s { // 슬라이스도 switch 식이 된다 — case 가 nil 뿐이면
	case nil:
		fmt.Println("s 는 nil 이다")
	default:
		fmt.Println("s 는 nil 이 아니다")
	}

	var m map[string]int
	switch m {
	case nil:
		fmt.Println("맵도 nil 과는 비교된다")
	}

	var f func()
	switch f {
	case nil:
		fmt.Println("함수 값도 그렇다")
	}
}
===== 명령: go build -trimpath -o prog . && ./prog =====
s 는 nil 이 아니다
맵도 nil 과는 비교된다
함수 값도 그렇다
(exit 0)
```

```text
===== 소스: t15l.go =====
package main

func main() {
	s := []int{1}
	t := []int{1}
	switch s {
	case t:
	}
}
===== 명령: go build -trimpath -o prog . =====
# ex
./t15l.go:7:7: invalid case t in switch on s (slice can only be compared to nil)
(exit 1)
```

**왜 그런가**

- 첫 프로그램은 **컴파일되고 실행된다** — `s 는 nil 이 아니다` / `맵도 nil 과는 비교된다` / `함수 값도 그렇다`.
- 둘째는 에러다 — `invalid case t in switch on s (slice can only be compared to nil)`.
  ★ 메시지가 **`switch` 전체가 아니라 그 `case` 하나**를 가리킨다는 점을 보라.
- 명세는 `switch` 식의 타입에 **"must be comparable"** 을 요구한다.
  그런데 비교 연산자 절에 **`nil` 특례**가 있다 —
  "Slice, map, and function types are not comparable. However, as a special case,
  **a slice, map, or function value may be compared to the predeclared identifier `nil`**."
  그 특례가 `switch` 에도 그대로 적용된다.
- ★ 05번 주제의 문장으로 옮기면 — 「**슬라이스는 `nil` 과만 비교된다**」가 답 전부다
  ([05번 주제](../05-arrays-vs-slices-value-and-header/)의 금지 사례 블록이 그 정본이다).
- ★★ **이 문항은 브리핑의 전제가 실행으로 뒤집힌 자리**다.
  「비교 불가 타입은 `switch` 를 못 한다」가 절반만 맞았다. **던지기 전에는 안 적는다.**
- 층 — **명세 보장**이다.

### 10. C 의 `switch` 와 나란히

**출력** — 없음(연결 문항).

**왜 그런가**

| 물음 | **C** | **Go** |
|---|---|---|
| 기본 동작 | **흘러내린다** | **안 흘러내린다** |
| 흘러내림 경고 | `-Wimplicit-fallthrough` — ★ `-Wall` 에도 `-Wextra` 에도 안 들어 있을 수 있다 | 해당 없음 |
| `case` 의 정체 | **라벨**(`goto` 의 그것과 같은 종류) | **가지**(`switch` 의 직계 자식) |
| `case` 에 쓸 수 있는 식 | **정수 상수식**(gcc 는 `const int` 도 거부) | **상수가 아니어도 된다** |
| 첫 `case` 앞의 선언 | **경고만**(`statement will never be executed` + `is used uninitialized`) · 쓰레기값 | ★ **`syntax error`** |
| `goto` 가 선언을 건너뜀 | VLA 면 **에러**, 보통 선언이면 **통과** | **언제나 에러** |
| `switch` 가 스코프 안으로 뜀 | VLA 면 **에러** | 해당 없음(가지가 블록이다) |
| Duff's device | **된다**(21자 복사 실측) | **문법적으로 불가능** |
| 완전성 검사 | 없다 | **없다** |

- C 쪽 실측은 전부 [`../../../c/syntax/12-control-flow-and-switch/`](../../../c/syntax/12-control-flow-and-switch/) 에 있다.
- ★ **Duff's device 가 Go 에서 불가능한 이유**는 `case` 가 라벨이 아니기 때문이다.
  `do { } while` 몸통 안에 `case` 를 박을 자리가 없다 — 7번의 `syntax error` 가 같은 규칙의 다른 얼굴이다.
- ★★ 두 언어가 **같은 낱말로 다른 물건**을 부른다. `switch`·`case`·`goto` 셋 다 그렇다.

### 11. 다른 주제와 잇기

**출력** — 없음(연결 문항).

**왜 그런가**

- **라벨 `break`/`continue` 가 붙는 `for` 자체** — [14번 주제](../14-for-four-forms-range-over-int-and-func/).
- **인터페이스가 (타입, 값) 쌍** — 목록의 **21번 주제**. 타입 스위치의 `case nil:` 이 거기서 설명된다.
- **타입 단언 두 꼴**(패닉형·comma-ok형) — 목록의 **22번 주제**.
- **`iota` 열거** — [03번 주제](../03-constants-iota-and-untyped-constants/).
  4번의 「완전성 검사가 없는 이유」가 거기서 나온다.
- **가지를 무작위로 고르는 사촌** — 목록의 **30번 주제**(`select`).
  꼴은 `switch` 를 닮았는데 **준비된 가지 중 무작위**로 고른다.
- 덤 — 깊은 중첩의 뒷정리는 Go 에서 `goto` 가 아니라 `defer` 다(목록의 **26번 주제**).

---

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행 1회** | 재실행 결과가 `normalize-shaky.py` 로 **동일** |
| 판 확인 | `go version` · `go env GOOS GOARCH GOVERSION` | 1 | `go1.27.1 linux/amd64` |
| 안 흘러내림 + `fallthrough` (`t15a`) | `go build && ./prog` | 1 | `one` / `two three` / `three` · `case 99:` 몸통이 돎 |
| 다섯 꼴 (`t15b`) | 〃 | 1 | `A B C` · 모음 · 나머지 1 · `x+y = 7` · 빈 `case` |
| ★★ 타입 스위치 (`t15c`) | 〃 | 1 | 일곱 줄 · `myInt` 가 `Stringer` 가지 |
| ★★★ 완전성 없음 (`t15d`) | 〃 | 1 | **컴파일·실행 성공 · 경고 0건** · `Drag` 가 0 |
| `break` 와 라벨 (`t15e`) | 〃 | 1 | `switch` 안 `break` 뒤 `1` 이 찍힘 |
| `goto` 되는 것 (`t15h`) | 〃 | 1 | 앞·뒤·블록 밖·블록 안 선언 건너뛰기 |
| `goto` 금지 (`t15f`) | `go build` | 1 | 에러 **2줄** · exit 1 |
| 거부되는 다섯 (`t15g`) | 〃 | 1 | 에러 **5건** · exit 1 |
| 여러 타입 가지의 `v` (`t15i`) | 〃 | 1 | 한 줄만 에러 · exit 1 |
| ★ `switch` 몸통의 선언 (`t15j`) | 〃 | 1 | **`syntax error` 2줄** · exit 1 |
| ★ 슬라이스 `switch` (`t15k`·`t15l`) | `go build && ./prog` · `go build` | 2 | `nil` 가지는 되고 다른 슬라이스는 에러 |
| 형태 (`t15form`) | `go build && ./prog` | 1 | 다섯 줄 |

**구현·환경에 달린 항목**(버전이 오르거나 환경이 바뀌면 **다시 찍어야 하는** 것)

| 항목 | 무엇에 달렸나 |
|---|---|
| **중복 `case` 를 거부하는 것** | ★ **구현.** 명세는 "A compiler may disallow" 로만 적었다 |
| 에러 메시지의 **문구 자체** | **툴체인 판(go1.27.1)**. 다른 컴파일러면 다를 수 있다 |
| 상수 `switch` 가 **점프 표로 컴파일되나** | **구현. 안 쟀다**(어셈블리를 안 떴다) |
| 타입 스위치의 **런타임 비용** | **구현. 안 쟀다** |
| 외부 완전성 린터(`exhaustive` 류)의 결과 | **안 돌렸다** — 이 툴체인에 없다 |
| `fallthrough` 앞에 **라벨을 붙이는** 꼴 | **안 던졌다**(명세가 허용한다고만 확인) |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다.

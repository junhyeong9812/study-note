# go/syntax/15 — `switch`·타입 스위치·`fallthrough`·라벨·`goto` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> ★ **C 를 안다면 그 직관을 먼저 의심하라.** 이 주제는 기본 동작이 C 와 정반대인 자리가 둘 있다.
> ★ **Rust 를 안다면 그것도 의심하라.** Go 의 `switch` 는 완전성을 검사하지 않는다.
> ★ **답마다 「그 값을 누가 보장하나」를 같이 적어라** — 명세인가, gc 구현인가, 이 판의 관찰인가.
> ★★ 이 주제에는 **흔들리는 칸이 없다.** 답이 「실행마다 다르다」인 문제는 하나도 없다.
> 소스는 전부 `go build -trimpath -o prog . && ./prog` 로 던졌다. 모듈 이름은 `ex` 다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 다섯 줄, 그리고 아래 두 줄 (예측)

```go
// t15a.go
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
```

- 위쪽 다섯 줄(`x=1` \~ `x=5`)은 각각 무엇으로 찍히는가?
- `x=1` 에 `break` 가 없는데 왜 그렇게 끝나는가?
- 아래쪽 덩어리에서 `switch 1` 인데 `case 99:` 의 몸통이 도는가?
- 그 동작을 명세의 어느 문장이 정하는가?

### 2. 다섯 가지 `switch` 꼴 (예측)

```go
// t15b.go
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
```

- ①\~⑤는 각각 무엇으로 찍히는가?
- ①의 `switch { }` 는 무엇과 같은 문인가?
- ④는 왜 컴파일되는가 — C 라면 어떤가?
- ⑤에서 `case 3:` 의 몸통이 도는가?

### 3. ★★ 일곱 번 부른 `describe` (예측)

```go
// t15c.go
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
```

- 일곱 줄은 각각 무엇으로 찍히는가 — 특히 `타입=` 칸을 채워라.
- `myInt(3)` 은 어느 가지에 걸리는가 — 왜인가?
- `3.5` 가 걸린 가지에서 `v` 의 **정적** 타입은 무엇인가 — `%T` 로 그것을 볼 수 있는가?
- 마지막 두 줄(comma-ok 단언)은 각각 무엇인가?

### 4. ★★★ 변형을 하나 늘렸는데 (예측)

`Event` 에 네 번째 값 `Drag` 를 더했다. 아래 `switch` 두 개는 **한 글자도 안 고쳤다.**

```go
// t15d.go
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
```

- 이 프로그램은 컴파일되는가? 실행되는가? 경고가 나는가?
- 네 줄은 각각 무엇으로 찍히는가?
- Rust 에서 같은 실험을 하면 무슨 일이 일어나는가 — **에러 개수**는?
- Go 에서 이 자리를 막는 방법은 무엇인가 — 언어가 해 주는가?

### 5. `break` 가 무엇을 끝내나 (예측)

```go
// t15e.go
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
```

- ①\~⑤는 각각 무엇으로 찍히는가?
- ①에서 `i == 1` 에 `break` 를 했는데 `1` 이 찍히는가 안 찍히는가 — 왜인가?
- ③과 ④의 차이는 무엇인가?
- ⑤에서 `(여기는 안 온다)` 는 찍히는가?

### 6. `goto` 넷 (예측)

```go
// t15h.go
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
```

- ①\~④는 각각 무엇으로 찍히는가?
- ②는 무엇이 되는가?
- ④에서 선언 `w := 1` 을 건너뛰는데 왜 에러가 아닌가?
- 라벨의 유효 범위는 어디까지인가?

### 7. 컴파일러가 거부하는 것 (경계)

아래 셋을 각각 던졌을 때 **메시지 전문**과 **종료 코드**는 무엇인가?

```go
// t15g.go
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
```

```go
// t15i.go
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
```

```go
// t15j.go
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
```

- 각 에러가 **명세 보장**인지 **구현 제약**인지 갈라라.
- `t15i.go` 의 두 `v + 1` 중 하나만 에러인 이유는 무엇인가?
- `t15j.go` 의 에러는 **어느 단계**에서 나는가 — 그 사실이 C 와 무엇을 가르는가?

### 8. 왜 Go 는 기본으로 안 흘러내리나 (왜)

- C 에서 `case` 는 **무엇**인가 — 그래서 흘러내리는가?
- Go 가 반대를 고른 대가는 무엇인가 — 잃은 것이 있는가?
- `fallthrough` 가 「다음 `case` 의 조건을 검사하지 않는」 것은 그 선택과 어떻게 이어지는가?
- C 에서 흘러내림 실수를 막는 장치는 무엇인가 — 기본으로 켜져 있는가?

### 9. 슬라이스로 `switch` 를 할 수 있나 (경계)

```go
// t15k.go
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
```

```go
// t15l.go
package main

func main() {
	s := []int{1}
	t := []int{1}
	switch s {
	case t:
	}
}
```

- 첫 프로그램은 컴파일되는가 — 세 줄은 각각 무엇인가?
- 둘째 프로그램의 메시지 전문은 무엇인가?
- 명세는 `switch` 식의 타입에 무엇을 요구하는가 — 그런데 왜 첫 프로그램이 되는가?
- 이 두 답을 05번 주제의 어느 문장으로 설명할 수 있는가?

### 10. C 의 `switch` 와 나란히 (연결)

- C 에서 `switch` 몸통의 **첫 `case` 앞**에 선언을 두면 무슨 일이 일어나는가 — Go 는?
- C 에서 `goto` 가 선언을 건너뛰면 어떻게 되는가 — 어떤 선언일 때 에러이고 어떤 선언일 때 경고인가?
- C 의 `case` 는 어떤 식이어야 하는가 — Go 는?
- Duff's device 는 Go 에서 쓸 수 있는가 — 왜인가?

### 11. 다른 주제와 잇기 (연결)

- 라벨 `break`/`continue` 가 붙는 `for` 자체의 정본은 몇 번 주제인가?
- 인터페이스가 (타입, 값) 쌍이라는 것의 정본은 몇 번 주제인가?
- 타입 단언 두 꼴의 정본은 몇 번 주제인가?
- `iota` 열거의 정본은 몇 번 주제인가?
- `switch` 를 닮았지만 가지를 무작위로 고르는 사촌은 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

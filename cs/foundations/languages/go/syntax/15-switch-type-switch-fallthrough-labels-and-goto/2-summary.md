# go/syntax/15 — `switch`·타입 스위치·`fallthrough`·라벨·`goto` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Go 명세](https://go.dev/ref/spec) 의 Switch statements(Expression switches ·
> Type switches) · Fallthrough statements · Break statements · Continue statements ·
> Goto statements · Labeled statements 절.\
> 웹이 아니라 **이 툴체인이 들고 있는 `$(go env GOROOT)/doc/go_spec.html` 을 열어** 인용했다.
> 그 파일의 머리는 「**Language version go1.27 (May 26, 2026)**」이다.
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> **버전** — 이 주제의 규칙은 전부 **1.0부터 지금까지 같다.**
> 13·14번과 달리 여기에는 **판 경계가 없다** — 그래서 층이 다시 셋으로 돌아온다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 명세로, 출력은 실행으로 접지했다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것. 어느 컴파일러에서도 같다 | `go_spec.html` 원문 인용 |
| **구현(gc)** | 이 컴파일러가 그렇게 하는 것. 약속은 아니다 | 에러 문구의 **낱말 선택** · 중복 `case` 탐지 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 실행 출력(재실행 대조까지) |

★★ 이 주제는 **「명세 보장」 칸이 거의 전부**다. `fallthrough` 가 기본이 아닌 것도,
타입 스위치에서 `v` 의 타입이 가지마다 다른 것도, `goto` 가 선언을 못 건너뛰는 것도 전부 명세에 적혀 있다.
★ 딱 한 칸이 구현이다 — **중복 `case` 를 거부하는 것**은 명세가 "Implementation restriction:
**A compiler may disallow** multiple case expressions evaluating to the same constant" 라고
「해도 된다」로만 적어 둔 자리다.

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

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | (없다) | 이 주제의 블록에는 주소·시간·고루틴·맵이 하나도 안 나온다 |
| 안 흔들린다 | 실행 출력 전부 | 결정적인 제어 흐름만 다룬다 |
| 안 흔들린다 | 컴파일 에러 문장 본문과 `파일:줄:칸` | 같은 소스·같은 판이면 같다 |
| 안 흔들린다 | 종료 코드 | 컴파일 실패는 1 |
| 해당 없음 | 맵 순회 순서 · 패닉 스택 | 이 주제는 둘 다 안 쓴다 |

★ 「흔들리는 칸이 없다」도 선언이다. 그래서 이 주제는 재대조가 **전부 완전 일치**여야 한다.

## 한눈에 — 쉽게 말하면

**C 의 `switch` 는 「뛰어 들어가는 문」이고 Go 의 `switch` 는 「고르는 문」이다.**

C 에서 `case` 는 라벨이라 한 번 들어가면 `break` 를 만날 때까지 아래로 흘러내린다.
Go 는 **가지 하나만 골라 돌고 거기서 끝낸다.** 아래로 가고 싶으면 `fallthrough` 라고 **적어야** 한다.

| 비유 | 실체 |
|---|---|
| 뛰어 들어가는 문 | **C 의 `switch`** — `case` 가 `goto` 의 라벨과 같은 종류다 |
| 고르는 문 | **Go 의 `switch`** — 가지 하나를 골라 돌고 끝낸다 |
| 「그래도 아래로 가겠다」 | **`fallthrough`** — 적어야 흘러내린다. 게다가 **다음 `case` 의 조건을 안 본다** |
| 조건표 | **조건 없는 `switch`** — `case` 자리에 bool 식을 쓴다. `if`-`else if` 사슬의 다른 꼴 |
| 상자를 열어 무슨 물건인지 본다 | **타입 스위치** — `switch v := x.(type)` |
| 문에 이름표를 붙인다 | **라벨** — `break`·`continue`·`goto` 가 그 이름을 부른다 |

```text
   C 의 switch                          Go 의 switch

   case 1: ──┐ (흘러내린다)             case 1: ──> 돌고 끝
   case 2: <─┘                          case 2: ──> 돌고 끝
             break 로만 막는다                    fallthrough 라고 적어야 내려간다
```

> **`fallthrough`** — 지금 가지의 **마지막 비어 있지 않은 문**으로만 쓸 수 있는 문.
> 제어를 **다음 가지의 첫 문**으로 넘긴다.\
> 예: `case 1:` 에서 `fallthrough` 하면 `case 99:` 의 몸통이 돈다 — **1과 99를 비교하지 않는다.**

> **타입 스위치(type switch)** — `switch v := x.(type)` 꼴. 인터페이스 값의 **동적 타입**으로 가른다.\
> 예: `case int:` 가지 안에서 `v` 는 **`int`** 다. `case string:` 안에서는 `string` 이다 — 가지마다 타입이 다르다.

> **라벨(label)** — 문 앞에 붙이는 이름(`loop:`). `break`·`continue`·`goto` 가 그것을 부른다.\
> 예: 중첩 루프에서 바깥까지 끝내려면 `break loop` 라고 쓴다. 안 쓰면 안쪽 하나만 끝난다.

> **완전성(exhaustiveness)** — 가능한 모든 경우를 다뤘는지 컴파일러가 검사하는 것.
> **Go 는 안 한다.**\
> 예: 상수를 하나 더 늘려도 `switch` 는 안 깨진다 — 조용히 `default` 로 떨어지거나 아무것도 안 한다.

- C 와 다른 점 — **기본 동작이 정반대**다. C 는 흘러내리고 Go 는 안 흘러내린다.
  그리고 **`switch` 몸통에 선언을 둘 수 있느냐**도 갈린다((9)절).
  C 쪽 정본은 [`../../../c/syntax/12-control-flow-and-switch/`](../../../c/syntax/12-control-flow-and-switch/) 다.
- Rust 와 다른 점 — Rust 의 `match` 는 **완전성을 강제**한다. 변형을 늘리면 컴파일이 깨진다.
  Go 는 안 깨진다 — 그 대비가 (5)절이다
  ([`../../../rust/syntax/18-match-and-exhaustiveness/`](../../../rust/syntax/18-match-and-exhaustiveness/)).

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. Go 의 `switch` 는 **무엇을 기본값으로 골랐나** — 그 선택이 코드 모양을 어떻게 바꾸나.
2. 타입 스위치에서 **`v` 는 무슨 타입인가** — 가지마다 다르다면 그 규칙은 무엇인가.
3. `break`·`continue`·`goto` 는 **어디까지 뛸 수 있나** — 못 뛰는 자리는 어디인가.

★ 「인터페이스가 (타입, 값) 쌍이라는 것」은 이 주제가 아니다 — [목록의 **21번 주제**](../21-nil-interface-vs-interface-holding-nil-pointer/)가 정본이다.
여기는 **타입 스위치라는 문법 표면**만 본다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

| 창 | 무엇을 보여 주나 | 한계 |
|---|---|---|
| 실행 출력 | 어느 가지가 돌았나 | **왜 그 가지인지는 안 보인다** |
| ★★ **컴파일 에러** | 이 언어가 **거부하는 것** | 거부하지 않는 것이 옳다는 뜻은 아니다 |
| ★★★ **변형을 늘려 보기** | **완전성을 강제하지 않는 것** — 늘려도 안 깨진다 | 「안 깨졌다」는 「안전하다」가 아니다. 그것이 이 절의 결론이다 |
| `%T` 로 타입 찍기 | 타입 스위치 가지 안의 **동적 타입** | **정적 타입**은 안 보인다 — 그건 컴파일 에러로만 갈린다 |

★ 네 번째 창의 한계가 중요하다. `%T` 는 **동적 타입**을 찍으므로
「가지 안에서 `v` 의 **정적** 타입이 무엇인가」는 **에러로만** 드러난다((4)절 마지막).

### (1) ★★ 기본은 안 흘러내린다 — 그리고 `fallthrough` 는 조건을 안 본다

**언제 쓰나** — `switch` 를 쓰는 모든 자리. C 를 알고 오면 여기서 직관이 뒤집힌다.

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

그림 해설 (한 단계씩):

- `x=1` 은 **`one` 하나만** 찍는다. `case 2:` 로 안 내려간다 — **`break` 를 안 썼는데도** 그렇다.
- `x=2` 는 **`two three`** 다. `fallthrough` 라고 **적었기** 때문이다.
- `x=3` 은 **`three` 하나**다. `case 3:` 에는 `fallthrough` 가 없다.
- ★★★ 아래쪽 덩어리가 `fallthrough` 의 진짜 성질이다 —
  `switch 1` 에서 `case 1:` 이 `fallthrough` 하니 **`case 99:` 의 몸통이 돌았다.**
  1과 99는 같지 않은데 들어갔다. 명세가 그 이유를 적는다.

  > In a case or default clause, the last non-empty statement may be a (possibly labeled)
  > "fallthrough" statement to indicate that **control should flow from the end of this clause
  > to the first statement of the next clause.** Otherwise control flows to the end of the "switch" statement.

- ★ 「**the first statement of the next clause**」 — **몸통으로 간다**고 적혀 있지 조건을 본다고 안 적혀 있다.
  그래서 `fallthrough` 는 「다음 조건도 검사해 달라」가 아니라 「**다음 몸통을 그냥 돌려라**」다.
- `default` 가 마지막에 있어야 하는 것도 아니다 — 명세: "There can be at most one default case
  and **it may appear anywhere** in the "switch" statement."

비용 — 없다. `break` 를 안 적는 것이 기본이라 코드가 짧아진다.

### (2) 다섯 가지 꼴 — 조건 없는 `switch` 와 init 문

**언제 쓰나** — `if`-`else if` 사슬이 길어질 때, 그리고 매칭을 묶고 싶을 때.

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

그림 해설 (한 단계씩):

- ① **조건 없는 `switch`** — `switch { case cond: }` 꼴이다. 명세:
  "**A missing switch expression is equivalent to the boolean value true.**"
  그래서 `case n >= 90:` 이 `true == (n >= 90)` 이 된다. `if`-`else if` 사슬의 다른 꼴이다.
- ② **`case` 에 값 여러 개** — 쉼표로 묶는다. 「또는」이다.
- ③ **init 문** — `switch v := 7 % 3; v {` 처럼 앞에 단순문을 둘 수 있다.
  그 변수는 **`switch` 안에서만** 산다.
- ④ **`case` 는 상수가 아니어도 된다.** 명세: "the case expressions, **which need not be constants**,
  are evaluated left-to-right and top-to-bottom; the first one that equals the switch expression
  triggers execution".
  ★ **C 와 갈리는 자리다** — C 의 `case` 는 정수 상수식이어야 한다.
- ⑤ **빈 `case` 는 아무것도 안 한다.** C 라면 흘러내려 `case 3:` 이 돌았을 자리다.

비용 — 없다. 컴파일러가 상수 가지를 표로 바꿀 수 있지만 **이 문서는 확인하지 않았다**(어셈블리를 안 떴다).

### (3) ★★ 타입 스위치 — `v` 의 타입이 가지마다 다르다

**언제 쓰나** — `any` 를 받았을 때. `fmt` 가 하는 일이 이것이다.

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

그림 해설 (한 단계씩):

- **`case int:` 안에서 `v` 는 `int`** 다 — 그래서 `v+1` 이 컴파일된다.
  **`case string:` 안에서는 `string`** 이라 `len(v)` 가 된다. **`case []int:` 안에서는 `[]int`** 라 `cap(v)` 가 된다.
- ★★★ **같은 이름 `v` 가 가지마다 다른 타입**이다. 명세가 그 규칙을 적는다.

  > The TypeSwitchGuard may include a short variable declaration. When that form is used,
  > **the variable is declared at the end of the TypeSwitchCase in the implicit block of each clause.**
  > **In clauses with a case listing exactly one type, the variable has that type;
  > otherwise, the variable has the type of the expression in the TypeSwitchGuard.**

  ★ 즉 **`v` 는 하나가 아니라 가지마다 하나씩**이다. 「암묵 블록마다 선언된다」가 그 뜻이다.
- ★★ **`case float64, bool:` 처럼 둘 이상이면 `v` 는 `any` 그대로**다.
  `%T` 로는 `float64` 가 찍혀서 **안 보인다** — 동적 타입을 찍기 때문이다.
  정적 타입이 갈리는 것은 **에러로만** 드러난다((6)절에 그 에러를 던져 뒀다).
- **`case nil:`** 이 있다 — 인터페이스 값 자체가 `nil` 일 때 골라진다.
  명세: "Instead of a type, a case may use the predeclared identifier `nil`".
- **`case Stringer:`** 처럼 **인터페이스**도 쓸 수 있다. `myInt` 가 거기 걸렸다.
  ★ **가지 순서가 의미를 갖는 자리**다 — 위에서 아래로 처음 맞는 것이 이긴다.
- 아래 두 줄은 **타입 단언의 comma-ok 꼴**이다. 실패하면 **제로값과 `false`** 를 준다(패닉이 아니다).
  정본은 [목록의 **22번 주제**](../22-type-assertion-any-and-comparable/)다.

```text
   switch v := x.(type) {
   case int:      v 는 int      <- 가지마다 「다른 v」가 선언된다
   case string:   v 는 string
   case A, B:     v 는 x 의 타입 그대로 (any)   <- ★ 여기만 다르다
   }
```

비용 — 런타임 타입 검사다. `switch` 가지 수에 비례한다 — **이 문서는 재지 않았다.**

### (4) ★★★ 완전성을 강제하지 않는다 — 변형을 늘려도 안 깨진다

**언제 쓰나** — 상수 묶음(`iota` 열거)에 `switch` 를 쓸 때. **조용히 틀리는 자리**다.

`Event` 에 네 번째 값 `Drag` 를 더했다. 아래 `switch` 두 개는 **한 글자도 안 고쳤다.**

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

그림 해설 (한 단계씩):

- **컴파일이 된다. 실행도 된다. 경고도 없다.** `Drag` 는 `label` 에서 `(여기로 떨어졌다)`,
  `weight` 에서 **0**을 받는다.
- ★★★ Rust 라면 여기서 **컴파일이 깨진다.**
  [`../../../rust/syntax/18-match-and-exhaustiveness/`](../../../rust/syntax/18-match-and-exhaustiveness/)
  의 실측이 정확히 이 실험이다 — 변형 하나를 늘리자 **`match` 네 자리에서 `error[E0004]` 가 넷** 났다.
  그리고 그 문서의 결론은 「`_` 는 짧게 쓰는 법이 아니라 안전망을 끄는 스위치다」였다 —
  `_` 를 넣으면 깨지는 자리가 **4 → 0** 이 된다.
- ★★ **Go 에는 그 안전망이 처음부터 없다.** `default` 를 넣든 안 넣든 컴파일러는 아무 말도 안 한다.
  이유는 `iota` 열거가 **타입이 아니라 그냥 정수**이기 때문이다 —
  컴파일러 입장에서 「가능한 값」이 `Click`·`Key`·`Scroll`·`Drag` 넷이라는 사실 자체가 없다.
  `Event(99)` 도 완벽히 합법이다.
- ★ 그래서 Go 에서 이 자리를 막는 것은 **언어가 아니라 도구와 습관**이다 —
  `default:` 에서 패닉하거나 오류를 내는 관용구, 그리고 외부 린터(`exhaustive` 류)다.
  **이 문서는 그 린터를 안 돌렸다** — 이 툴체인에 없다.
- ★★ 이것이 이 주제에서 **「에러가 안 나는 것」이 결론인 유일한 절**이다.
  「통과했다」가 근거가 되려면 **무엇이 통과했는지를 출력으로** 보여야 한다 — 그래서 네 줄을 다 찍었다.

비용 — 없다. 대신 **유지보수 비용**을 나중에 낸다.

### (5) ★★ `break` 는 무엇을 끝내나 — 그리고 라벨

**언제 쓰나** — 중첩 루프에서 빠져나올 때, 그리고 `switch` 안에서 `break` 를 쓸 때.

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

그림 해설 (한 단계씩):

- ① ★★ **`switch` 안의 `break` 는 `switch` 를 끝낸다.** 루프가 아니다.
  그래서 `i == 1` 에서 `break` 했는데도 **`1` 이 찍혔다.** C 에서 온 직관이 여기서 뒤집힌다.
- ② 라벨을 달면 루프가 끝난다 — `break loop`.
- ③ 중첩 루프에서 **`break` 는 가장 안쪽 하나만** 끝낸다. 명세:

  > A "break" statement terminates execution of the **innermost** enclosing "for", "switch"
  > or "select" statement within the same function.

- ④ `break outer` 는 **바깥까지** 끝낸다.
- ⑤ `continue next` 는 **바깥 루프의 다음 회차**로 간다 — 그래서 `(여기는 안 온다)` 가 안 찍혔다.
  `continue` 는 `for` 에만 붙는다(명세: "…terminates … the innermost enclosing "for" loop").

```text
   for i {            for i {  <- outer
     switch {           for j {
       break   ────┐      break        ──> 안쪽 for 만 끝
     }             │      break outer  ──> 바깥까지 끝
     (여기로 온다) │      continue outer ──> 바깥의 다음 회차
   }        <──────┘    }
                      }
```

비용 — 없다.

### (6) ★★ 컴파일러가 거부하는 다섯 가지

**언제 쓰나** — 「이건 되나?」를 물을 때. **던져 보면 답이 나온다.**

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

그림 해설 (한 단계씩):

- **`fallthrough` 는 마지막 `case` 에서 에러**다 — `cannot fallthrough final case in switch`.
  명세: "A "fallthrough" statement may appear as the last statement of **all but the last clause**
  of an expression switch."
- **중복 `case` 도 에러**다. ★ 그런데 이것은 **명세 보장이 아니다** —
  "Implementation restriction: **A compiler may disallow** multiple case expressions evaluating
  to the same constant." 「해도 된다」로만 적혀 있다. 이 컴파일러는 한다.
- ★★ **타입 스위치 안에서는 `fallthrough` 가 아예 금지**다 — `cannot fallthrough in type switch`.
  타입 가지를 흘러내리면 `v` 의 타입이 정해지지 않기 때문이다.
- **`case` 의 타입이 안 맞으면 에러**다 — `cannot convert 1 (untyped int constant) to type string`.
  명세: "If a case expression is untyped, it is first implicitly converted to the type of the switch expression."
- **타입 스위치의 중복 타입도 에러**다 — "The types listed in the cases of a type switch
  must all be different."

그리고 여러 타입 가지 안에서 `v` 를 그 타입처럼 쓰면 에러다 — (3)절이 말한 정적 타입 규칙의 증거다.

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

- 같은 `v + 1` 이 **한 가지에서는 되고 다른 가지에서는 안 된다.**
  `case float64:` 안의 `v` 는 `float64`, `case int, bool:` 안의 `v` 는 **`any`** 다.
- ★ `%T` 로는 못 봤던 것이 여기서 보인다 — **정적 타입은 에러로만 드러난다.**

비용 — 없다. 전부 컴파일 시점이다.

### (7) `goto` — 되는 것 넷

**언제 쓰나** — Go 에서는 드물다. 생성된 코드나 깊은 중첩의 탈출 정도다.

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

그림 해설 (한 단계씩):

- ① **앞으로** 뛴다. ② **뒤로** 뛰면 루프가 된다. ③ **블록 밖으로** 나올 수 있다.
- ④ ★ **선언을 건너뛰어도 그 선언이 블록 안에 있으면 된다.**
  건너뛰는 것이 금지되는 것은 **그 선언이 `goto` 지점의 스코프에 들어오는 경우**뿐이다.
- 라벨은 **함수 단위**다. 다른 함수의 라벨로는 못 뛴다.

비용 — 없다.

### (8) ★★ `goto` 가 못 넘는 두 가지 — 던져서 확인한다

**언제 쓰나** — 「왜 여기서 에러가 나지?」를 물을 때.

```text
===== 소스: t15f.go =====
package main

import "fmt"

func main() {
	x := 1
	if x == 1 {
		goto skip
	}
	v := 10
	fmt.Println(v)
skip:
	fmt.Println("도착")

	goto into
	{
	into:
		fmt.Println("블록 안으로")
	}
}
===== 명령: go build -trimpath -o prog . =====
# ex
./t15f.go:8:8: goto skip jumps over declaration of v at ./t15f.go:10:4
./t15f.go:15:7: goto into jumps into block starting at ./t15f.go:16:2
(exit 1)
```

그림 해설 (한 단계씩):

- **선언을 건너뛰면 에러**다 — `goto skip jumps over declaration of v at ./t15f.go:10:4`.
  명세가 그 이유를 직접 적고 **예제까지 싣는다.**

  > **Executing the "goto" statement must not cause any variables to come into scope
  > that were not already in scope at the point of the goto.** For instance, this example:
  > `goto L // BAD` / `v := 3` / `L:` is erroneous because **the jump to label L skips the creation of v**.

- **블록 안으로 뛰어도 에러**다 — `goto into jumps into block starting at ./t15f.go:16:2`.

  > **A "goto" statement outside a block cannot jump to a label inside that block.**

- ★★★ **C 와 갈리는 자리다.** C 도 `goto` 가 **VLA 스코프 안으로** 뛰는 것은 에러로 막는다
  (`error: jump into scope of identifier with variably modified type`).
  그런데 **VLA 가 아닌 보통 선언을 건너뛰는 쪽은 경고로 끝나고 컴파일이 된다** —
  C 쪽 실측에서 `switch` 가 첫 `case` 앞의 `int v = 99;` 를 건너뛰자
  `warning: statement will never be executed` + `warning: 'v' is used uninitialized` 만 나고
  **그 변수가 쓰레기값**을 가졌다(gcc `32764` · clang `32765` — **두 컴파일러가 서로 다른 값**을 찍었다.
  [`../../../c/syntax/12-control-flow-and-switch/`](../../../c/syntax/12-control-flow-and-switch/) (7)절).
  **Go 는 이쪽도 거부한다.**
- ★ 그러니 두 언어의 `goto` 는 이름만 같고 **막는 범위가 다르다.**
  C 는 VLA 라는 **특수한 경우만** 막고, Go 는 **모든 선언 건너뛰기**를 막는다.

비용 — 없다. 컴파일 시점에 막힌다.

### (9) ★ 덤 두 가지 — 던져 보니 브리핑 전제가 뒤집혔다

**언제 쓰나** — 「`switch` 몸통에 뭘 넣을 수 있나」와 「비교 불가 타입은 `switch` 가 안 되나」를 물을 때.

첫째 — **`switch` 몸통에는 `case`·`default` 말고 아무것도 못 온다.**

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

- **문법 에러**다. `unexpected name v, expected case or default or }`.
- ★★★ **C 와 갈리는 두 번째 자리다.** 위 (8)절이 인용한 C 실측이 바로 그 코드인데,
  C 는 **그 선언을 받아 놓고 경고만 한다.** Go 는 **파서가 아예 안 받는다** —
  그래서 「선언이 실행되지 않아 쓰레기값이 된다」는 사고 자체가 성립하지 않는다.
- ★ 에러가 **`syntax error`** 라는 점이 결정적이다. 타입 검사 이전, **문법 단계**에서 막힌다.

둘째 — ★★ **슬라이스·맵·함수도 `switch` 식이 될 수 있다.** 단 `case` 가 `nil` 뿐일 때다.

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

- 「비교 불가 타입은 `switch` 를 못 한다」가 **절반만 맞다.**
  명세가 "The switch expression type must be comparable" 이라고 적는데,
  **`nil` 과의 비교는 특례**라서 이 꼴이 통과한다
  ([05번 주제](../05-arrays-vs-slices-value-and-header/)의 「슬라이스는 `nil` 과만 비교된다」가 여기로 이어진다).
- 다른 슬라이스를 `case` 에 두면 그때 막힌다.

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

- `invalid case t in switch on s (slice can only be compared to nil)` —
  **`switch` 전체가 아니라 그 `case` 하나**를 거부한다는 점이 메시지에 그대로 보인다.
- ★ **이 두 가지는 이 배치의 브리핑 전제가 실행으로 뒤집힌 자리**다.
  「Go 는 슬라이스로 `switch` 를 못 한다」와 「C 처럼 첫 `case` 앞에 선언을 둘 수 있다」가
  둘 다 틀렸다. **던져 보기 전에는 적지 않는다.**

비용 — 없다.

## 문법 — 형태와 규칙

### 형태

```go
// t15form.go
package main

import "fmt"

func main() {
	x := 2
	switch x { // ① 식 switch
	case 1, 2: // ② case 에 값 여러 개
		fmt.Println("1 또는 2")
		fallthrough // ③ 다음 case 몸통으로 넘어간다
	case 3:
		fmt.Println("3 의 몸통")
	default: // ④ 어디에도 없으면
		fmt.Println("그 밖")
	}

	switch y := x * 2; { // ⑤ init 문 + 조건 없는 switch
	case y > 3:
		fmt.Println("y > 3 :", y)
	}

	var a any = "가"
	switch v := a.(type) { // ⑥ 타입 스위치
	case string:
		fmt.Println("string :", len(v))
	default:
		fmt.Println("그 밖 :", v)
	}

L: // ⑦ 라벨
	for i := 0; i < 2; i++ {
		for {
			continue L // ⑧ 라벨 continue
		}
	}
	goto end // ⑨ goto
end:
	fmt.Println("끝")
}
```

```text
===== 소스: t15form.go =====
package main

import "fmt"

func main() {
	x := 2
	switch x { // ① 식 switch
	case 1, 2: // ② case 에 값 여러 개
		fmt.Println("1 또는 2")
		fallthrough // ③ 다음 case 몸통으로 넘어간다
	case 3:
		fmt.Println("3 의 몸통")
	default: // ④ 어디에도 없으면
		fmt.Println("그 밖")
	}

	switch y := x * 2; { // ⑤ init 문 + 조건 없는 switch
	case y > 3:
		fmt.Println("y > 3 :", y)
	}

	var a any = "가"
	switch v := a.(type) { // ⑥ 타입 스위치
	case string:
		fmt.Println("string :", len(v))
	default:
		fmt.Println("그 밖 :", v)
	}

L: // ⑦ 라벨
	for i := 0; i < 2; i++ {
		for {
			continue L // ⑧ 라벨 continue
		}
	}
	goto end // ⑨ goto
end:
	fmt.Println("끝")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
1 또는 2
3 의 몸통
y > 3 : 4
string : 3
끝
(exit 0)
```

규칙 불릿.

- `switch` 에 **괄호가 없다.** `switch (x) {` 는 안 쓴다.
- **식 스위치**는 `switch [init;] [expr] { case …: }` 다. `expr` 을 생략하면 **`true`** 다.
- **`case` 는 상수가 아니어도 되고** 여러 값을 쉼표로 묶을 수 있다.
- **가지 하나만 돌고 끝난다.** `break` 를 안 적어도 그렇다.
- **`fallthrough` 는 가지의 마지막 비어 있지 않은 문**으로만 쓸 수 있고 **마지막 가지에는 못 쓴다.**
  **다음 가지의 조건을 검사하지 않는다.** **타입 스위치에서는 아예 금지**다.
- **`default` 는 아무 자리에나** 올 수 있고 **최대 하나**다.
- **타입 스위치**는 `switch [init;] [v :=] x.(type) { case T: }` 다.
  가지에 타입이 **정확히 하나**면 `v` 는 그 타입, **둘 이상이면** `x` 의 타입 그대로다.
  `case nil:` 을 쓸 수 있고 **최대 하나**다. 나열한 타입은 **전부 달라야** 한다.
- **`break`·`continue` 는 가장 안쪽**에 붙는다. `break` 는 `for`·`switch`·`select` 에,
  `continue` 는 `for` 에만. 더 바깥은 **라벨**로 부른다.
- **`goto` 는 같은 함수 안에서만** 뛴다. **선언을 건너뛸 수 없고 블록 안으로 못 들어간다.**
- 라벨 이름은 **변수와 다른 이름 공간**이다. 같은 이름을 써도 충돌하지 않는다.

### 금지 사례 — 컴파일러가 거부하는 것

(6)절과 (8)절의 블록이 이 주제의 금지 사례 정본이다. 일곱 가지를 한 표로 묶으면 이렇다.

| 쓴 것 | 메시지 | 층 |
|---|---|---|
| 마지막 `case` 의 `fallthrough` | `cannot fallthrough final case in switch` | **명세 보장** |
| 타입 스위치의 `fallthrough` | `cannot fallthrough in type switch` | **명세 보장** |
| 식 스위치의 중복 `case` | `duplicate case 1 (constant of type int) in expression switch` | **구현(명세는 「해도 된다」)** |
| 타입 스위치의 중복 타입 | `duplicate case int in type switch` | **명세 보장** |
| 타입이 안 맞는 `case` | `cannot convert 1 (untyped int constant) to type string` | **명세 보장** |
| 여러 타입 가지에서 `v` 를 그 타입처럼 | `invalid operation: v + 1 (mismatched types any and untyped int)` | **명세 보장** |
| 선언을 건너뛰는 `goto` | `goto skip jumps over declaration of v at …` | **명세 보장** |
| 블록 안으로 뛰는 `goto` | `goto into jumps into block starting at …` | **명세 보장** |
| `switch` 몸통의 선언 | `syntax error: unexpected name v, expected case or default or }` | **명세 보장**(문법) |
| 슬라이스 `case` 에 슬라이스 | `invalid case t in switch on s (slice can only be compared to nil)` | **명세 보장** |

★ **거부하지 않는 것**이 더 중요하다 — **완전성 검사는 없다**((4)절).

## 어디서 틀리나

### 1. ★★★ 「`break` 를 안 썼으니 아래로 흘러내린다」 — C 의 직관이다

- (1)절 실측 — `x=1` 은 **`one` 하나만** 찍는다.
- 반대 실수도 같이 난다 — 「Go 에 `fallthrough` 가 있으니 C 처럼 쓰면 되겠지」.
  **`fallthrough` 는 다음 `case` 의 조건을 안 본다** — `switch 1` 에서 `case 99:` 몸통이 돌았다.
- 고치는 법 — 「흘러내리게 하려면 **적는다**」, 그리고 **적으면 조건 검사 없이 들어간다**를 같이 외운다.

### 2. ★★★ 「`switch` 안에서 `break` 하면 루프가 끝난다」

- (5)절 ① 실측 — **`1` 이 찍힌다.** `break` 가 `switch` 를 끝냈을 뿐이다.
- Go 에서는 `switch` 에 `break` 를 쓸 일이 거의 없는데(안 써도 끝난다), **그래서 더 헷갈린다.**
- 고치는 법 — 루프를 끝내려면 **라벨**을 쓴다(`break loop`).

### 3. ★★★ 「상수를 하나 더 늘렸으니 `switch` 가 알려 주겠지」

- (4)절 실측 — **컴파일도 실행도 되고 경고도 없다.** `weight` 가 **0**을 돌려준다.
- Rust 는 같은 실험에서 **에러 넷**을 냈다. Go 에는 그 안전망이 **없다.**
- 고치는 법 — `default:` 에서 **패닉하거나 오류를 낸다.** 「조용히 0」을 돌려주지 않는다.

### 4. ★★ 「타입 스위치의 `v` 는 하나다」

- (3)절 실측 — **가지마다 다른 타입**이다. 명세가 「암묵 블록마다 선언된다」고 적는다.
- 그리고 **가지에 타입이 둘 이상이면 `v` 는 원래 인터페이스 타입 그대로**다 — (6)절이 그 에러다.
- 고치는 법 — 여러 타입을 묶은 가지 안에서는 **다시 단언**하거나 가지를 쪼갠다.

### 5. ★★ 「타입 스위치의 가지 순서는 상관없다」

- (3)절 실측 — `myInt` 가 **`case Stringer:`** 에 걸렸다. 인터페이스 가지가 아래 있었으면 안 걸렸을 것이다.
- 명세: "the case expressions … are evaluated **left-to-right and top-to-bottom**;
  **the first one that equals** the switch expression triggers execution".
- 고치는 법 — **좁은 타입을 위에, 인터페이스를 아래**에 둔다.

### 6. ★★ 「`goto` 는 위험하니 Go 에서도 아무 데나 뛴다」

- (8)절 실측 — **선언을 건너뛸 수 없고 블록 안으로 못 들어간다.** 컴파일 에러다.
- C 는 같은 코드를 **경고만 하고 통과**시키며 쓰레기값을 만든다(gcc `32764` · clang `32765`).
- 고치는 법 — Go 의 `goto` 는 **훨씬 좁은 물건**이다. 그 제약이 곧 안전이다.

### 7. ★ 「중복 `case` 는 컴파일러가 언제나 잡는다」

- (6)절 실측 — 이 컴파일러는 잡는다. 그런데 명세는 **"A compiler may disallow"** 로만 적었다.
- 상수가 아닌 `case` 두 개가 우연히 같은 값이면 **아무도 안 잡는다** — 위쪽이 이긴다.
- 고치는 법 — 「컴파일러가 잡아 줄 것」에 기대지 않는다.

### 8. ★ 「조건 없는 `switch` 는 특별한 문법이다」

- (2)절 — `switch { }` 는 **`switch true { }`** 다. 명세가 그렇게 적는다.
- 그래서 `case` 자리에 bool 식을 쓰는 것이 자연스럽다.
- 고치는 법 — `if`-`else if` 사슬이 셋을 넘으면 이쪽이 읽기 낫다.

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| 가지 하나만 돌고 **흘러내리지 않는다** | **명세 보장** | "Otherwise control flows to the end of the "switch" statement" |
| `fallthrough` 가 **다음 가지의 첫 문**으로 간다 | **명세 보장** | "control should flow … to the first statement of the next clause" |
| `fallthrough` 는 **마지막 가지에 못 쓴다** | **명세 보장** | "may appear as the last statement of all but the last clause" |
| **타입 스위치에서 `fallthrough` 금지** | **명세 보장** | 명세가 `fallthrough` 를 **expression switch** 에만 정의한다 |
| **`case` 가 상수가 아니어도 된다** | **명세 보장** | "the case expressions, which need not be constants" |
| 가지를 **위에서 아래로, 왼쪽에서 오른쪽으로** 본다 | **명세 보장** | "evaluated left-to-right and top-to-bottom" |
| **`default` 는 아무 자리에나 · 최대 하나** | **명세 보장** | "at most one default case and it may appear anywhere" |
| **식을 생략하면 `true`** | **명세 보장** | "A missing switch expression is equivalent to the boolean value true" |
| 타입 스위치의 **`v` 가 가지마다 선언된다** | **명세 보장** | "declared at the end of the TypeSwitchCase in the implicit block of each clause" |
| 가지에 타입이 **둘 이상이면 `v` 는 원래 타입** | **명세 보장** | "otherwise, the variable has the type of the expression in the TypeSwitchGuard" |
| **타입 스위치의 타입은 전부 달라야** 한다 | **명세 보장** | "The types listed in the cases of a type switch must all be different" |
| `break`·`continue` 가 **가장 안쪽**에 붙는다 | **명세 보장** | "terminates execution of the innermost enclosing …" |
| `goto` 가 **선언을 건너뛸 수 없다** | **명세 보장** | "must not cause any variables to come into scope …" |
| `goto` 가 **블록 안으로 못 들어간다** | **명세 보장** | "A "goto" statement outside a block cannot jump to a label inside that block" |
| **중복 `case` 를 거부하는 것** | **구현** | "Implementation restriction: **A compiler may disallow** …" |
| **완전성 검사가 없는 것** | **명세 보장(없음의 보장)** | 명세 어디에도 그런 검사가 없다. `iota` 열거는 그냥 정수다 |
| **`switch` 몸통에 `case`·`default` 만** 올 수 있다 | **명세 보장**(문법) | `ExprSwitchStmt = "switch" … "{" { ExprCaseClause } "}"` |
| **`nil` 만 `case` 면 슬라이스·맵·함수도 된다** | **명세 보장** | 비교 연산자 절의 `nil` 특례 |
| 에러 메시지의 **문구 자체** | **구현(gc)** | 다른 컴파일러면 다를 수 있다 |
| 상수 `switch` 가 **점프 표로 컴파일되나** | **구현 · 안 쟀다** | 어셈블리를 안 떴다 |

★ 이 주제의 결론은 「**거의 전부가 명세 보장이고, 구현에 맡겨진 것은 「중복 `case` 를 잡아 줄 것인가」
한 칸뿐**」이다. 그리고 **가장 중요한 것은 명세에 「없는」 것**이다 — 완전성 검사.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 한 값을 여러 상수와 견준다 | **식 스위치** | `if`-`else if` 보다 읽기 쉽다 |
| 조건이 값 하나에 안 걸린다 | **조건 없는 `switch`** | `switch true` 와 같다 |
| 분기가 둘뿐이다 | **`if`** | `switch` 는 과하다 |
| `any` 를 받아 타입으로 가른다 | **타입 스위치** | 가지마다 `v` 의 타입이 정해진다 |
| 한 타입만 확인한다 | **comma-ok 단언**(`v, ok := x.(T)`) | 가지 하나짜리 타입 스위치는 과하다 |
| 아래 가지도 같이 돌아야 한다 | **`fallthrough`** — 단 **조건을 안 본다**는 것을 알고 쓴다 | 실무에서 드물다 |
| `iota` 열거를 다 다뤄야 한다 | **`default:` 에서 패닉·오류** | 언어가 안 막아 준다 |
| 중첩 루프를 한 번에 나온다 | **라벨 `break`** | 플래그 변수보다 낫다 |
| 깊은 중첩에서 공통 뒷정리로 간다 | **`defer` 를 먼저 고려** | Go 에서는 `goto` 보다 `defer` 가 관용이다 |
| 상태 기계를 코드로 쓴다 | **라벨 + `goto`** 도 후보 | 표준 라이브러리 스캐너에 실제로 쓰인다 |

판단 규칙 두 줄.

- **「이 `switch` 가 모든 경우를 다뤘는가」는 사람이 지킨다.** 컴파일러는 안 도와준다.
- **`break` 를 적을 때 「무엇을 끝내려는가」를 먼저 말하라.** `switch` 인지 `for` 인지가 갈린다.

## 핵심 문장

- Go 의 `switch` 는 **가지 하나만 돌고 끝난다.** `break` 를 안 적어도 그렇다 — C 와 정반대다.
- ★★ **`fallthrough` 는 다음 가지의 조건을 검사하지 않는다.** 「다음 몸통을 그냥 돌려라」다.
  마지막 가지에는 못 쓰고 **타입 스위치에서는 아예 금지**다.
- **식을 생략한 `switch` 는 `switch true`** 다 — `if`-`else if` 사슬의 다른 꼴이다.
- **`case` 는 상수가 아니어도 된다.** C 와 갈리는 자리다.
- ★★★ 타입 스위치의 **`v` 는 가지마다 따로 선언된다.** 타입이 정확히 하나인 가지에서는 그 타입,
  둘 이상인 가지에서는 **원래 인터페이스 타입 그대로**다.
- ★★★ **Go 는 완전성을 강제하지 않는다.** 상수를 하나 늘려도 컴파일도 실행도 되고 경고도 없다 —
  Rust 가 같은 실험에서 **에러 넷**을 내는 자리다. 막는 것은 **`default:` 의 패닉**뿐이다.
- **`switch` 안의 `break` 는 `switch` 를 끝낸다.** 루프를 끝내려면 라벨이 필요하다.
- **`goto` 는 선언을 건너뛸 수 없고 블록 안으로 못 들어간다.**
  C 는 VLA 라는 특수한 경우만 막고 보통 선언은 경고만 하고 통과시켜 쓰레기값을 만든다 —
  **막는 범위가 다르다.**
- ★ 던져 보니 뒤집힌 전제 둘 — **`switch` 몸통에는 `case` 말고 아무것도 못 오고**(문법 에러),
  **슬라이스·맵·함수도 `case nil:` 하나면 `switch` 가 된다.**

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 15번)
- [14번 주제](../14-for-four-forms-range-over-int-and-func/)(`for` 의 네 형태·`range`) —
  **그쪽은 루프 꼴과 `range` 까지**, 여기는 **`break`/`continue` 가 어디에 붙나**부터
- [03번 주제](../03-constants-iota-and-untyped-constants/)(상수·`iota`) —
  **그쪽은 `iota` 가 값을 어떻게 펴는지까지**, 여기는 **그 상수 묶음에 `switch` 를 쓸 때의 위험**부터
- [목록의 **21번 주제**](../21-nil-interface-vs-interface-holding-nil-pointer/)(`nil` 인터페이스와 `nil` 포인터를 담은 인터페이스) —
  **인터페이스가 (타입, 값) 쌍이라는 것의 정본.** 타입 스위치의 `case nil:` 이 거기서 설명된다
- [목록의 **22번 주제**](../22-type-assertion-any-and-comparable/)(타입 단언·`any`·`comparable`) — **단언 두 꼴의 정본**
- [목록의 **26번 주제**](../26-defer-evaluation-lifo-named-results-and-loops/)(`defer`) — 깊은 중첩의 뒷정리는 Go 에서 `goto` 가 아니라 `defer` 다
- [`../../../c/syntax/12-control-flow-and-switch/`](../../../c/syntax/12-control-flow-and-switch/) —
  **그쪽은 `switch` 가 「점프이지 블록이 아니라는」 것을 Duff's device 로 증명하고**,
  여기는 **그 성질을 언어가 뒤집은 쪽**이다.
  ★ `goto` 도 갈린다 — **C 는 선언 건너뛰기를 경고로 통과시키고 Go 는 거부한다**
- [`../../../rust/syntax/18-match-and-exhaustiveness/`](../../../rust/syntax/18-match-and-exhaustiveness/) —
  **그쪽은 변형을 늘리면 `match` 네 자리가 `error[E0004]` 로 깨지고**,
  여기는 **같은 실험에서 아무 일도 안 일어난다.**
  ★ 그쪽 결론 「`_` 는 안전망을 끄는 스위치다」를 Go 로 옮기면 「**안전망이 처음부터 없다**」가 된다

## 용어 풀이

- **식 스위치(expression switch)** — 값을 견주는 `switch`. `case` 가 식이다.
- **타입 스위치(type switch)** — `switch x.(type)`. 인터페이스 값의 동적 타입으로 가른다.
- **`fallthrough`** — 다음 가지의 **첫 문**으로 제어를 넘기는 문. 조건을 안 본다.
- **가지(case clause)** — `case …:` 부터 다음 `case` 전까지. 명세의 낱말은 clause 다.
- **암묵 블록(implicit block)** — 각 가지가 이루는 블록. 타입 스위치의 `v` 가 여기에 선언된다.
- **라벨(label)** — 문 앞의 이름. 변수와 **다른 이름 공간**이다.
- **완전성(exhaustiveness)** — 모든 경우를 다뤘는지의 검사. **Go 에는 없다.**
- **구현 제약(implementation restriction)** — 명세가 「컴파일러가 거부해도 된다」고 허용한 것.
  중복 `case` 가 그것이다.
- **comma-ok 단언** — `v, ok := x.(T)`. 실패하면 제로값과 `false` 를 준다.

---

## 더 들어가면

- `select` 는 채널 전용의 사촌이다 — 꼴은 `switch` 를 닮았는데 **가지를 고르는 방식이 다르다**
  (준비된 것 중 **무작위**로 고른다). 정본은 [목록의 **30번 주제**](../30-select-default-and-timeouts/)다.
- `fallthrough` 앞에 **라벨을 붙일 수 있다**("a (possibly labeled) fallthrough statement").
  실무에서 볼 일은 거의 없다 — **이 문서는 안 던졌다.**
- 식 스위치의 피연산자는 **비교 가능한 타입**이어야 한다("The switch expression type must be comparable").
  그런데 **`nil` 과의 비교가 특례**라서 슬라이스·맵·함수도 `case nil:` 하나짜리 `switch` 는 된다 —
  (9)절이 그것을 던졌다.
- 타입 스위치의 `switch x.(type)` 은 **변수 없이도** 쓸 수 있다((6)절의 마지막 덩어리가 그 꼴이다).
  그때는 가지 안에서 `x` 를 원래 타입 그대로 쓴다.
- `goto` 가 실제로 쓰이는 자리는 표준 라이브러리에도 있다 — 스캐너·파서의 상태 전이 같은 곳이다.
  다만 **일반 코드에서 쓸 이유는 거의 없다.**
- C 의 `switch` 가 「점프」라는 것의 가장 강한 증거는 **Duff's device** 다 —
  `do { } while` 의 몸통 **안쪽에 `case` 라벨이 박힌다.** Go 에서는 문법적으로 불가능하다
  (가지는 `switch` 의 직계 자식이어야 한다). 실측은 C 쪽 (4)절에 있다.

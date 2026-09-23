# go/syntax/02 — 변수 선언 세 형태와 제로값 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> ★ **이 주제의 예측은 「값」과 「`nil` 여부」 둘 다다.** `[]` 라고만 적으면 절반만 맞힌 것이다.
> ★ 컴파일 에러를 묻는 문항은 **에러인지 아닌지**가 아니라 **몇 줄이 나오는지**까지 답해라.
> 소스는 전부 `go build -trimpath -o prog . && ./prog` 로 던졌다. 모듈 이름은 `ex` 다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★ 열네 칸을 채워라 (예측)

```go
// t02a.go
package main

import "fmt"

type Point struct {
	X, Y int
	Name string
	Tags []string
}

func row(typ string, v, gv any, nilCmp string) {
	fmt.Printf("%-14s | %-14s | %-32s | %s\n",
		typ, fmt.Sprintf("%v", v), fmt.Sprintf("%#v", gv), nilCmp)
}

func main() {
	var (
		i   int
		f   float64
		b   bool
		s   string
		r   rune
		by  byte
		p   *int
		sl  []int
		m   map[string]int
		ch  chan int
		fn  func()
		ifc interface{}
		arr [3]int
		st  Point
	)
	fmt.Printf("%-14s | %-14s | %-32s | %s\n", "type", "%v", "%#v", "== nil")
	fmt.Println("---------------+----------------+" +
		"----------------------------------+--------")
	row("int", i, i, "컴파일 에러")
	row("float64", f, f, "컴파일 에러")
	row("bool", b, b, "컴파일 에러")
	row("string", s, s, "컴파일 에러")
	row("rune(=int32)", r, r, "컴파일 에러")
	row("byte(=uint8)", by, by, "컴파일 에러")
	row("*int", p, p, fmt.Sprint(p == nil))
	row("[]int", sl, sl, fmt.Sprint(sl == nil))
	row("map[string]int", m, m, fmt.Sprint(m == nil))
	row("chan int", ch, ch, fmt.Sprint(ch == nil))
	row("func()", fn, fn, fmt.Sprint(fn == nil))
	row("interface{}", ifc, ifc, fmt.Sprint(ifc == nil))
	row("[3]int", arr, arr, "컴파일 에러")
	row("Point", st, st, "컴파일 에러")
}
```

- 열네 행의 `%v` 칸은 각각 무엇인가?
- 열네 행의 `%#v` 칸은 각각 무엇인가 — `%v` 와 **다른 행**은 어디인가?
- `== nil` 칸에 「컴파일 에러」가 아닌 행은 몇 개인가?
- `Point` 행의 `%#v` 에서 `Tags` 는 무엇으로 찍히는가?

### 2. ★ 네 가지 만드는 법의 여섯 칸 (예측)

```go
// t02b.go
package main

import (
	"encoding/json"
	"fmt"
	"reflect"
	"unsafe"
)

func report(label string, s []int) {
	j, _ := json.Marshal(s)
	fmt.Printf("%-16s len=%d cap=%d  s==nil:%-5t  %%v:%-3v  %%#v:%-13v  "+
		"Sizeof=%d  데이터포인터=%v  json=%s\n",
		label, len(s), cap(s), s == nil, s, fmt.Sprintf("%#v", s),
		unsafe.Sizeof(s), unsafe.SliceData(s) == nil, j)
}

func main() {
	var a []int         // 제로값 — nil 슬라이스
	b := []int{}        // 빈 리터럴
	c := make([]int, 0) // make 로 길이 0
	d := make([]int, 0, 4)

	report("var a []int", a)
	report("[]int{}", b)
	report("make([]int,0)", c)
	report("make([]int,0,4)", d)

	fmt.Println()
	fmt.Println("reflect.DeepEqual(a, b) =", reflect.DeepEqual(a, b))
	fmt.Println("len(a) == len(b)        =", len(a) == len(b))
	fmt.Println("append 은 둘 다 된다:  append(a,1) =", append(a, 1),
		"· append(b,1) =", append(b, 1))
	fmt.Println("range 는 둘 다 0바퀴")
	for range a {
		fmt.Println("이 줄은 안 찍힌다")
	}
}
```

- 네 행의 `len`·`cap` 은 각각 무엇인가?
- 네 행의 `s==nil` 은 각각 무엇인가?
- 네 행의 `json` 칸은 각각 무엇인가?
- `Sizeof` 는 네 행이 같은가 다른가 — 그 값은 왜 그 수인가?
- `reflect.DeepEqual(a, b)` 는 무엇인가?

### 3. 이 프로그램은 어디까지 가는가 (예측)

```go
// t02c.go
package main

import (
	"fmt"
	"os"
)

func main() {
	var m map[string]int
	fmt.Println("m == nil :", m == nil, "· len(m) :", len(m))
	fmt.Println("없는 키 읽기 m[\"x\"] :", m["x"])
	v, ok := m["x"]
	fmt.Println("comma-ok :", v, ok)
	fmt.Println("delete(m, \"x\") 는 그냥 지나간다")
	delete(m, "x")
	fmt.Fprintln(os.Stderr, "----- 여기까지 stdout · 아래부터 쓰기 시도 -----")
	m["x"] = 1
	fmt.Println("이 줄은 안 찍힌다")
}
```

- 몇 줄이 찍히고 각각 무엇인가?
- 어느 줄에서 멈추는가 — 멈춘다면 **메시지 전문**과 **종료 코드**는?
- `delete(m, "x")` 에서는 왜 아무 일도 안 나는가?
- 이 프로그램의 어느 줄이 표준 오류로 나가는가?

### 4. 이 세 프로그램은 각각 몇 줄의 에러를 내는가 (예측)

```go
// t02e.go
package main

import "fmt"

count := 0

func main() { fmt.Println(count) }
```

```go
// t02g.go
package main

import "fmt"

func main() {
	a, b := 1, 2
	a, b = 3, 4
	a, c := 5, 6
	var unused int
	fmt.Println(a, b, c)
}
```

```go
// t02h.go
package main

import "fmt"

func main() {
	a, b := 1, 2
	a, b := 3, 4
	fmt.Println(a, b)
}
```

- 각각의 **에러 줄 수**와 **메시지 전문**은 무엇인가?
- 첫 프로그램의 에러는 다른 둘과 **층이 다르다** — 무엇이 다른가?
- 둘째 프로그램에서 `a, c := 5, 6` 은 왜 에러가 아닌가?
- 첫 프로그램에 `gofmt` 를 돌리면 무엇이 나오는가?

### 5. 여섯 줄의 값 (예측)

```go
// t02i.go
package main

import "fmt"

var v = "패키지 수준"

func main() {
	fmt.Println("1:", v)
	v := "main 의 v"
	fmt.Println("2:", v)
	{
		v := 3
		fmt.Printf("3: %v (%T) — 블록 안에서는 타입까지 바뀐다\n", v, v)
	}
	fmt.Println("4:", v)

	if v := "if 의 v"; len(v) > 0 {
		fmt.Println("5:", v)
	}
	fmt.Println("6:", v)
}
```

- 1\~6번 줄은 각각 무엇으로 찍히는가?
- 3번 줄의 타입은 무엇이고 왜 그렇게 되는가?
- 4번 줄이 3번과 다른 이유를 한 문장으로 말하라.
- 이 여섯 줄에서 **컴파일 에러도 경고도 없다** — 그게 왜 문제인가?

### 6. 여덟 변수의 타입 (예측)

```go
// t02f.go
package main

import "fmt"

var pkgLevelUnused int // 패키지 수준은 안 써도 에러가 아니다

var (
	host      = "localhost"
	port  int = 8080
	debug bool
)

func main() {
	var a int        // ① 타입만 — 제로값
	var b = 42       // ② 값만 — 타입은 값에서 온다
	var c int64 = 42 // ③ 둘 다
	d := 42          // ④ 짧은 선언 (함수 안에서만)
	e := 42.0
	f := 'A'
	g := "hi"
	h := 42 + 0i

	fmt.Printf("a: %-8T %v\n", a, a)
	fmt.Printf("b: %-8T %v\n", b, b)
	fmt.Printf("c: %-8T %v\n", c, c)
	fmt.Printf("d: %-8T %v\n", d, d)
	fmt.Printf("e: %-8T %v\n", e, e)
	fmt.Printf("f: %-8T %v\n", f, f)
	fmt.Printf("g: %-8T %v\n", g, g)
	fmt.Printf("h: %-8T %v\n", h, h)
	fmt.Printf("host=%-10q port=%-6d debug=%v\n", host, port, debug)
}
```

- `a`\~`h` 여덟 개의 타입은 각각 무엇인가?
- `f := 'A'` 의 타입 이름이 `rune` 으로 찍히지 않는 이유는?
- 마지막 줄의 `debug` 는 무엇인가?
- `pkgLevelUnused` 는 왜 에러가 아닌가?

### 7. 제로값은 왜 언어의 약속인가 (왜)

- 「선언만 한 변수에 쓰레기 값이 들어가는 일이 없다」는 **명세 보장**인가 **구현**인가?
- 명세는 그것을 어떤 문장으로 적는가 — 「재귀적」이라는 낱말은 무엇을 뜻하는가?
- 그 약속이 있어서 성립하는 Go 관용구를 둘 들어라.
- 그 약속이 **도움이 안 되는** 타입은 무엇이고 왜인가?

### 8. `nil` 과 비교할 수 있는 것 (경계)

```go
// t02k.go
package main

import "fmt"

type Point struct{ X, Y int }

func main() {
	var i int
	var s string
	var arr [3]int
	var pt Point
	var sl []int
	fmt.Println(i == nil)
	fmt.Println(s == nil)
	fmt.Println(arr == nil)
	fmt.Println(pt == nil)
	fmt.Println(sl == sl)
}
```

- 다섯 줄 중 컴파일되는 것이 있는가 — 없다면 각 줄의 메시지는?
- 마지막 줄(`sl == sl`)의 메시지가 앞 네 줄과 **다른 이유**는?
- `== nil` 을 물을 수 있는 타입을 전부 대라.
- 두 슬라이스가 같은지 보려면 무엇을 쓰는가?

### 9. `nil` 슬라이스와 빈 슬라이스를 갈라야 하는 자리 (경계)

- 둘이 **같게 동작하는** 연산을 넷 이상 들어라.
- 둘이 **다르게 동작하는** 자리를 둘 들어라.
- 함수가 결과 없음을 돌려줄 때, 안쪽 코드용으로는 어느 쪽이 낫고 API 응답으로는 어느 쪽이 나은가?
- `unsafe.Sizeof` 로는 둘을 가를 수 있는가?

### 10. 다른 주제와 잇기 (연결)

- `b := 42` 가 `int` 가 되는 규칙의 정본은 몇 번 주제인가?
- `var c int64 = 42` 는 되는데 `var c int64 = d`(`d` 가 `int`)는 왜 안 되며, 그 정본은 몇 번 주제인가?
- 슬라이스 헤더 세 칸의 정본은 몇 번 주제인가?
- 「값은 `nil` 인데 인터페이스는 `nil` 이 아니다」의 정본은 몇 번 주제인가?
- 패키지 변수가 **언제** 초기화되는지의 정본은 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

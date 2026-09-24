# go/syntax/09 — 맵: 선언·comma-ok·`delete`·순회 순서 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> ★★★ **이 주제에서는 「한 판의 출력」을 묻는 문항이 없다.**
> 맵 순회는 실행마다 달라지므로 묻는 것은 언제나 「**몇 가지가 나오나**」이거나 「**무엇이 보장되나**」다.
> ★ 답을 적을 때 **「명세가 정한 것」과 「gc 가 이번 판에서 그렇게 하는 것」을 갈라서** 적어라.
> 소스는 전부 `go build -trimpath -o prog . && ./prog` 로 던졌다. 모듈 이름은 `ex` 다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 선언 세 꼴 중 하나만 다르다 (예측)

```go
// t09a.go
package main

import "fmt"

func main() {
	var a map[string]int           // ① var — nil 맵
	b := make(map[string]int)      // ② make — 빈 맵
	c := map[string]int{"x": 1}    // ③ 리터럴
	d := make(map[string]int, 100) // ④ 크기 힌트를 준 make

	fmt.Printf("① var     a == nil : %-5v  len=%d\n", a == nil, len(a))
	fmt.Printf("② make    b == nil : %-5v  len=%d\n", b == nil, len(b))
	fmt.Printf("③ 리터럴  c == nil : %-5v  len=%d\n", c == nil, len(c))
	fmt.Printf("④ 힌트    d == nil : %-5v  len=%d\n", d == nil, len(d))

	fmt.Println()
	fmt.Println("nil 맵에서 읽는 것은 전부 된다 — 패닉이 아니라 제로값이다")
	fmt.Printf("  a[\"없는키\"]           = %d\n", a["없는키"])
	v, ok := a["없는키"]
	fmt.Printf("  v, ok := a[\"없는키\"]  = %d %v\n", v, ok)
	fmt.Printf("  len(a)                = %d\n", len(a))
	delete(a, "없는키")
	fmt.Println("  delete(a, \"없는키\")   도 그냥 된다")
	n := 0
	for range a {
		n++
	}
	fmt.Printf("  for range a           는 %d번 돈다\n", n)
}
```

- `a`·`b`·`c`·`d` 중 `== nil` 이 참인 것은 무엇인가?
- nil 맵에 대한 **읽기·`len`·`delete`·`range`** 는 각각 어떻게 되는가?
- `make(map[string]int, 100)` 의 **100** 은 무슨 뜻인가 — 상한인가?
- 그다음 이 프로그램을 던지면 어떻게 되는가?

```go
// t09b.go
package main

import (
	"fmt"
	"os"
)

func main() {
	var m map[string]int
	fmt.Fprintf(os.Stderr, "-- m == nil : %v · 읽기는 됐다 : %d --\n", m == nil, m["k"])
	fmt.Fprintln(os.Stderr, "-- 이제 쓴다 : m[\"k\"] = 1 --")
	m["k"] = 1
	fmt.Fprintln(os.Stderr, "-- 여기는 안 온다 --")
}
```

- 출력 **전문**을 적어라 — 메시지 본문·`goroutine` 줄·`파일:줄`·**종료 코드**까지.
- 마커를 `fmt.Fprintln(os.Stderr, …)` 로 찍은 이유는 무엇인가?

### 2. ★ 두 번의 0 (예측)

```go
// t09c.go
package main

import "fmt"

func main() {
	m := map[string]int{"a": 1, "b": 0}

	fmt.Println("값이 0 인 키와 아예 없는 키는 그냥 읽으면 구분이 안 된다")
	fmt.Printf("  m[\"b\"]    = %d\n", m["b"])
	fmt.Printf("  m[\"없음\"] = %d\n", m["없음"])

	fmt.Println()
	fmt.Println("comma-ok 가 그 둘을 가른다")
	v1, ok1 := m["b"]
	v2, ok2 := m["없음"]
	fmt.Printf("  v, ok := m[\"b\"]    -> %d %v\n", v1, ok1)
	fmt.Printf("  v, ok := m[\"없음\"] -> %d %v\n", v2, ok2)
	_, only := m["b"]
	fmt.Printf("  _, ok := m[\"b\"]    -> %v   (값을 안 받아도 된다)\n", only)

	fmt.Println()
	fmt.Println("delete")
	delete(m, "a")
	fmt.Printf("  delete(m, \"a\")     뒤 len=%d  m[\"a\"]=%d\n", len(m), m["a"])
	delete(m, "없음")
	fmt.Printf("  없는 키를 지워도 아무 일 없다 len=%d\n", len(m))
	_, ok3 := m["a"]
	fmt.Printf("  지운 뒤 comma-ok   -> %v\n", ok3)

	clear(m)
	fmt.Printf("  clear(m) (1.21) 뒤 len=%d  m == nil : %v\n", len(m), m == nil)
}
```

- `m["b"]` 와 `m["없음"]` 은 각각 무엇으로 찍히는가?
- comma-ok 의 두 결과는 각각 무엇인가?
- 없는 키를 `delete` 하면 무엇이 일어나는가?
- `clear(m)` 뒤 `m == nil` 은 무엇인가 — **왜** 그런가?

### 3. ★★★ 600번 돌리면 (예측)

```go
// t09d.go
package main

import (
	"fmt"
	"os"
	"strconv"
)

// 인자로 받은 개수만큼 'a' 부터 키를 넣고, 한 번 순회한 순서를 한 줄로 찍는다.
func main() {
	n, _ := strconv.Atoi(os.Args[1])
	m := map[string]int{}
	for i := 0; i < n; i++ {
		m[string(rune('a'+i))] = i
	}
	for k := range m {
		fmt.Print(k)
	}
	fmt.Println()
}
```

- 이 프로그램을 `./prog 3` 으로 **600번** 돌려 `sort -u` 하면 **몇 줄**이 나오는가?
- 3개짜리 키의 순열은 6가지다. 그 수와 위의 답이 다르다면 **왜** 다른가?
- `./prog 8` 과 `./prog 9` 는 각각 몇 가지인가?
- 그 수치는 **명세가 보장하는 것인가, gc 의 사정인가?**

```go
// t09e.go
package main

import "fmt"

func main() {
	m := map[string]int{"a": 1, "b": 2, "c": 3}
	var first, second string
	for k := range m {
		first += k
	}
	for k := range m {
		second += k
	}
	fmt.Println("한 프로세스 안에서 두 번 돈 순서가 같은가 :", first == second)
}
```

- 이것을 600번 돌려 `sort -u` 하면 **몇 줄**이 나오는가?
- 명세의 어느 문장이 그 답을 정하는가?

### 4. ★★ 돌면서 지우기와 돌면서 넣기 (예측)

```go
// t09f.go
package main

import "fmt"

func main() {
	m := map[int]bool{0: true, 1: true, 2: true, 3: true, 4: true, 5: true, 6: true, 7: true}
	seen := 0
	for k := range m {
		seen++
		for j := range m {
			if j != k {
				delete(m, j) // 아직 안 나온 항목까지 전부 지운다
			}
		}
	}
	fmt.Println("8개짜리 맵을 돌면서 나머지를 전부 지웠더니 본 항목 수 :", seen)
}
```

```go
// t09g.go
package main

import "fmt"

func main() {
	m := map[int]int{0: 0, 1: 1, 2: 2, 3: 3}
	n := 0
	for k := range m {
		if n == 0 {
			m[100] = 100 // 순회 중에 새 항목을 넣는다
		}
		n++
		_ = k
	}
	fmt.Println(n)
}
```

- `t09f` 의 출력은 무엇인가 — 흔들리는가?
- `t09g` 를 600번 돌리면 **몇 가지 값**이 나오는가?
- 두 프로그램의 답이 갈리는 이유를 **명세의 문장 두 개**로 설명하라.
- 「돌면서 넣어야 한다」면 어떻게 고치는가?

### 5. ★★ 맵에 담은 구조체의 필드에 손을 대면 (예측)

```go
// t09h.go
package main

import "fmt"

type P struct{ N int }

func main() {
	m := map[string]int{"a": 1}
	p := &m["a"]
	fmt.Println(p)

	s := map[string]P{"a": {1}}
	s["a"].N = 2
	fmt.Println(s)
}
```

- 이 프로그램은 어느 단계에서 무엇을 말하는가 — **두 줄 전문**과 **종료 코드**를 적어라.
- 슬라이스에서는 같은 코드가 되는가 — 왜 갈리는가?
- 고치는 법을 **셋** 대라.

### 6. ★ `any` 키에 무엇을 넣으면 (예측)

```go
// t09k.go
package main

import (
	"fmt"
	"os"
)

func main() {
	m := map[any]string{}
	m[42] = "정수는 된다"
	m[[2]int{1, 2}] = "배열도 된다"
	fmt.Fprintf(os.Stderr, "-- 여기까지 len=%d --\n", len(m))
	fmt.Fprintln(os.Stderr, "-- 이제 슬라이스를 키로 넣는다 --")
	m[[]int{1, 2}] = "슬라이스는?"
	fmt.Fprintln(os.Stderr, "-- 여기는 안 온다 --")
}
```

- 컴파일은 되는가?
- 출력 **전문**을 적어라 — **종료 코드**까지.
- 명세의 어느 문장이 이것을 예고했는가?
- 이 사고를 컴파일 때 잡으려면 무엇을 바꿔야 하는가?

### 7. 왜 `&m[k]` 를 막았나 (왜)

- 맵의 항목은 **왜** 주소를 내줄 수 없는가?
- 슬라이스의 원소는 **왜** 내줄 수 있는가?
- 그 제약이 만드는 **코드 모양의 차이**를 하나 대라.
- 이 제약이 없었다면 어떤 버그가 가능해지는가?

### 8. 키가 될 수 있는 타입 (경계)

```go
// t09j.go
package main

import "fmt"

type Bad struct {
	Tags []string
}

func main() {
	var a map[[]int]string
	var b map[func()]bool
	var c map[Bad]int
	var d map[map[string]int]bool
	fmt.Println(a, b, c, d)
}
```

- 네 줄 중 몇 줄이 거부되는가 — **메시지 전문**은?
- `Bad` 는 구조체인데 왜 거부되는가?
- 되는 것과 안 되는 것을 가르는 **한 낱말**은 무엇인가?
- 그 낱말의 기준이 **컴파일 때 정해지지 않는** 타입은 무엇인가?

### 9. 어느 칸이 명세이고 어느 칸이 gc 의 사정인가 (경계)

아래 여덟 가지를 **「명세 보장」 / 「gc·라이브러리의 사정」** 으로 갈라라.

- ① 맵 순회 순서가 정해져 있지 않다
- ② 3개짜리 맵에서 순서가 3가지만 나온다
- ③ nil 맵에 쓰면 패닉이다
- ④ 순회 중에 지운 항목은 안 나온다
- ⑤ 순회 중에 넣은 항목은 나올 수도 안 나올 수도 있다
- ⑥ `fmt.Println(m)` 이 키 순서로 찍는다
- ⑦ `cap(m)` 이 컴파일 에러다
- ⑧ `abc` 가 다른 순서보다 다섯 배 넘게 자주 나온다

### 10. 다른 언어와 나란히 놓기 (연결)

- 파이썬 `dict` 의 순회 순서는 무엇이 정하는가 — 언제부터인가?
- 자바에서 「순서 있는 맵」을 쓰려면 무엇을 고르는가?
- 셋 중 **「순서를 약속하지 않겠다」고 명시적으로 선언한** 언어는 어느 것인가?
- Go 가 그 대신 얻은 것은 무엇인가?

### 11. 다른 주제와 잇기 (연결)

- 「맵의 제로값이 nil 이다」의 정본은 몇 번 주제인가?
- 「비교 가능한 타입」의 정본은 몇 번 주제인가?
- 해시 테이블 원리 자체의 정본은 어느 갈래인가?
- `maps.Keys`·`slices.Sorted` 의 정본은 몇 번 주제인가?
- 여러 고루틴이 같은 맵을 만질 때의 정본은 몇 번 주제인가?
- `m[k] = append(m[k], v)` 로 다시 넣어야 하는 이야기의 정본은 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

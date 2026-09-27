# go/syntax/17 — 구조체: 리터럴·비교 가능성·필드 태그·정렬 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> ★★★ **모든 문제에서 「이 타입의 필드가 전부 비교 가능한가」를 먼저 적어라.** 답의 절반이 거기서 나온다.
> ★★ **「컴파일에서 걸리나 실행에서 걸리나」를 갈라서 답하라** — 이 주제는 그 둘이 자주 어긋난다.
> ★ **답마다 「그 값을 누가 보장하나」를 같이 적어라** — 명세인가, gc 구현인가, 이 판의 관찰인가.
> 소스는 전부 `go build -trimpath -o prog . && ./prog` 로 던졌다. 모듈 이름은 `ex` 다.
> 컴파일 에러를 전부 보려고 몇 블록은 `-gcflags=-e` 를 붙였다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 리터럴 일곱 줄 (예측)

```go
// t17a.go
package main

import "fmt"

type Point struct {
	X int
	Y int
}

type Line struct {
	From  Point
	To    Point
	Label string
}

func main() {
	// ① 필드명 있는 리터럴 — 순서를 바꿔도 되고, 빠뜨려도 된다(제로값)
	a := Point{X: 1, Y: 2}
	b := Point{Y: 2, X: 1}
	c := Point{X: 1} // Y 는 제로값
	fmt.Printf("① a=%v b=%v c=%v   a==b : %v\n", a, b, c, a == b)

	// ② 위치 리터럴 — 전부 적어야 하고 순서가 뜻이다
	d := Point{1, 2}
	fmt.Printf("② d=%v   d==a : %v\n", d, d == a)

	// ③ 중첩 — 안쪽 타입 이름을 생략할 수 있다
	l1 := Line{From: Point{X: 1, Y: 2}, To: Point{X: 3, Y: 4}, Label: "ㄱ"}
	l2 := Line{Point{1, 2}, Point{3, 4}, "ㄱ"}
	fmt.Printf("③ l1=%v\n   l2=%v   l1==l2 : %v\n", l1, l2, l1 == l2)

	// ④ 배열·슬라이스·맵의 원소에서는 타입 이름을 아예 생략한다
	ps := []Point{{1, 2}, {X: 3}}
	m := map[string]Point{"ㄱ": {1, 2}}
	fmt.Printf("④ ps=%v m=%v\n", ps, m)

	// ⑤ 제로값 — var 와 T{} 는 같은 것이다
	var z1 Point
	z2 := Point{}
	fmt.Printf("⑤ z1=%v z2=%v   z1==z2 : %v\n", z1, z2, z1 == z2)

	// ⑥ 익명 구조체 — 타입 이름 없이 그 자리에서
	anon := struct {
		Name string
		N    int
	}{Name: "ㄴ", N: 7}
	fmt.Printf("⑥ anon=%v  타입=%T\n", anon, anon)

	// ⑦ 포인터를 바로 얻는다 — &T{…} 는 복합 리터럴에만 허용된 예외다
	p := &Point{X: 9, Y: 9}
	p.X = 8
	fmt.Printf("⑦ p=%v  타입=%T\n", *p, p)
}
```

- 일곱 줄은 각각 무엇으로 찍히는가?
- ①에서 `c` 가 그 값인 이유는 무엇인가?
- ⑥의 `%T` 는 무엇으로 찍히는가?
- ⑦의 `&Point{…}` 가 되는 이유는 무엇인가 — 리터럴은 변수가 아닌데?

### 2. ★★ 같은 리터럴을 두 정의에 (예측)

```go
// t17c.go
package main

import "fmt"

// 어제의 정의
type UserV1 struct {
	ID  int
	Age int
}

// 오늘의 정의 — 필드 둘의 **순서만** 바꿨다. 개수도 타입도 그대로다.
type UserV2 struct {
	Age int
	ID  int
}

func main() {
	fmt.Println("── 위치 리터럴 User{1001, 30} 을 두 정의에 각각 ──")
	p1 := UserV1{1001, 30}
	p2 := UserV2{1001, 30}
	fmt.Printf("  V1: ID=%d Age=%d\n", p1.ID, p1.Age)
	fmt.Printf("  V2: ID=%d Age=%d   ← 1001살이 되었다\n", p2.ID, p2.Age)

	fmt.Println("── 필드명 리터럴은 그대로다 ──")
	n1 := UserV1{ID: 1001, Age: 30}
	n2 := UserV2{ID: 1001, Age: 30}
	fmt.Printf("  V1: ID=%d Age=%d\n", n1.ID, n1.Age)
	fmt.Printf("  V2: ID=%d Age=%d\n", n2.ID, n2.Age)

	fmt.Println("── 컴파일러는 한 마디도 안 했다 : go vet 도 이 자리를 안 본다 ──")
}
```

- 여덟 줄은 각각 무엇으로 찍히는가?
- 두 정의의 차이는 무엇인가 — 필드 개수는? 타입은?
- 이 프로그램은 컴파일되는가? `go vet ./...` 은 무엇을 말하는가?
- 같은 실수를 **컴파일러가 잡아 주는** 판을 하나 만들어 보라 — 무엇을 바꾸면 되는가?

### 3. ★★★ `==` 일곱 개 (예측)

```go
// t17d.go
package main

import "fmt"

type HasArr struct {
	A [2]int
}

type HasSlice struct {
	S []int
}

type HasMap struct {
	M map[string]int
}

type HasFunc struct {
	F func()
}

type Outer struct {
	In HasSlice // 비교 불가는 안쪽에서 바깥으로 번진다
}

func main() {
	fmt.Println(HasArr{} == HasArr{})     // ① 배열 필드 — 된다
	fmt.Println(HasSlice{} == HasSlice{}) // ② 슬라이스 필드
	fmt.Println(HasMap{} == HasMap{})     // ③ 맵 필드
	fmt.Println(HasFunc{} == HasFunc{})   // ④ 함수 필드
	fmt.Println(Outer{} == Outer{})       // ⑤ 한 겹 안쪽이 슬라이스

	var s1, s2 []int
	fmt.Println(s1 == s2) // ⑥ 슬라이스끼리

	var a1, a2 [2][]int
	fmt.Println(a1 == a2) // ⑦ 비교 불가 원소의 배열
}
```

- 컴파일러는 몇 개를 거부하는가 — 각각의 메시지 전문은?
- 거부되지 **않는** 것은 어느 것인가, 왜인가?
- ⑤는 슬라이스 필드가 직접 없는데 왜 막히는가?
- ⑥과 ⑦의 메시지가 서로 다른 이유는 무엇인가?

### 4. ★★ `any` 가 끼어든 두 프로그램 (예측)

```go
// t17e.go
package main

import (
	"fmt"
	"os"
)

type WithArr struct {
	A [3]int
	S string
}

type WithPtr struct {
	P *int
}

type WithAny struct {
	V any // 인터페이스 필드 — 컴파일은 통과한다
}

func main() {
	fmt.Fprintln(os.Stderr, "-- 비교되는 것들 --")
	fmt.Println("배열 필드 :", WithArr{A: [3]int{1, 2, 3}, S: "ㄱ"} == WithArr{A: [3]int{1, 2, 3}, S: "ㄱ"})
	n1, n2 := 1, 1
	fmt.Println("포인터 필드(같은 값, 다른 칸) :", WithPtr{&n1} == WithPtr{&n2})
	fmt.Println("포인터 필드(같은 칸)         :", WithPtr{&n1} == WithPtr{&n1})
	fmt.Println("any 에 int 를 담아 :", WithAny{1} == WithAny{1})
	fmt.Println("any 에 다른 타입을 :", WithAny{1} == WithAny{int64(1)})

	fmt.Fprintln(os.Stderr, "-- 이제 any 에 슬라이스를 담고 비교한다 --")
	x := WithAny{[]int{1}}
	y := WithAny{[]int{1}}
	fmt.Println(x == y)
	fmt.Fprintln(os.Stderr, "-- 여기는 안 온다 --")
}
```

```go
// t17f.go
package main

import (
	"fmt"
	"os"
)

type Key struct {
	Tenant string
	ID     int
}

func main() {
	// ① 비교 가능한 구조체는 맵 키가 된다
	m := map[Key]int{}
	m[Key{"a", 1}] = 10
	m[Key{"a", 2}] = 20
	fmt.Println("① m[Key{a,1}] =", m[Key{"a", 1}], " len =", len(m))

	// ② 없는 키는 제로값 + comma-ok
	v, ok := m[Key{"b", 1}]
	fmt.Println("② 없는 키 :", v, ok)

	// ③ 배열도 키가 된다
	ma := map[[2]int]string{{1, 2}: "ㄱ"}
	fmt.Println("③ ma[[2]int{1,2}] =", ma[[2]int{1, 2}])

	// ④ map[any]int 는 컴파일을 통과한다 — 키의 비교 가능성을 런타임에 본다
	anyKey := map[any]int{}
	anyKey[1] = 1
	anyKey["ㄱ"] = 2
	anyKey[Key{"a", 1}] = 3
	fmt.Println("④ map[any]int 에 셋을 넣었다 : len =", len(anyKey))

	fmt.Fprintln(os.Stderr, "-- 이제 슬라이스를 키로 넣는다 --")
	anyKey[[]int{1}] = 4
	fmt.Fprintln(os.Stderr, "-- 여기는 안 온다 --")
}
```

- 두 프로그램의 빌드는 성공하는가?
- 첫 프로그램의 앞 다섯 줄, 둘째 프로그램의 앞 네 줄은 각각 무엇으로 찍히는가?
- 각각 마지막에 무엇이 나오는가 — **전문**과 **종료 코드**는? 두 문구는 어떻게 다른가?
- 「포인터 필드(같은 값, 다른 칸)」 줄이 그 값인 이유는 무엇인가?

### 5. 맵 키가 못 되는 것 (경계)

```go
// t17g.go
package main

import "fmt"

type BadKey struct {
	Tags []string
}

func main() {
	bad := map[BadKey]int{}
	fmt.Println(bad)

	bySlice := map[[]int]string{}
	fmt.Println(bySlice)

	byFunc := map[func()]int{}
	fmt.Println(byFunc)
}
```

- 이 프로그램의 메시지 **세 줄 전문**은 무엇인가?
- 세 메시지가 이유를 말해 주는가 — 3번의 에러와 견주면 무엇이 빠져 있는가?
- 4번의 둘째 프로그램은 같은 규칙에 걸렸는데 **실행에서** 걸렸다. 무엇이 갈랐는가?
- 맵 키의 요건을 한 문장으로 적으면?

### 6. ★★ 태그는 어디에 보이나 (예측)

```go
// t17h.go
package main

import (
	"encoding/json"
	"fmt"
	"reflect"
)

type User struct {
	ID    int    `json:"id" db:"user_id"`
	Name  string `json:"name,omitempty" validate:"required"`
	Email string `json:"-"`
	Note  string // 태그 없음
}

func main() {
	t := reflect.TypeOf(User{})
	fmt.Println("── reflect 로만 보이는 것 : 필드 태그 ──")
	for i := range t.NumField() {
		f := t.Field(i)
		jsonTag, jsonOK := f.Tag.Lookup("json")
		dbTag, dbOK := f.Tag.Lookup("db")
		fmt.Printf("  %-5s json=%-16q %-5v  db=%-10q %-5v\n", f.Name, jsonTag, jsonOK, dbTag, dbOK)
		fmt.Printf("        원문 = %q\n", string(f.Tag))
	}

	fmt.Println("── Get 은 없는 키에 빈 문자열을 준다 — Lookup 이라야 「없음」이 보인다 ──")
	f0 := t.Field(0)
	fmt.Printf("  Get(\"없는키\")    = %q\n", f0.Tag.Get("없는키"))
	v, ok := f0.Tag.Lookup("없는키")
	fmt.Printf("  Lookup(\"없는키\") = %q, %v\n", v, ok)

	fmt.Println("── 태그는 프로그램 동작을 바꾸지 않는다. 읽는 쪽이 있어야 뜻이 생긴다 ──")
	b, _ := json.Marshal(User{ID: 7, Name: "", Email: "a@b", Note: "ㄴ"})
	fmt.Printf("  json.Marshal : %s\n", b)
	fmt.Printf("  fmt 는 태그를 모른다 : %v\n", User{ID: 7, Email: "a@b", Note: "ㄴ"})
}
```

- 네 필드 줄은 각각 무엇으로 찍히는가?
- `Get("없는키")` 와 `Lookup("없는키")` 는 각각 무엇을 주는가 — 왜 둘이 필요한가?
- `json.Marshal` 이 낸 JSON 은 무엇인가 — 네 필드 중 몇 개가 들어갔는가?
- 마지막 줄에서 `fmt` 가 낸 것은 무엇인가 — 그것이 무엇을 증명하는가?

### 7. 정렬 다섯 판 (예측)

```go
// t17k.go
package main

import (
	"cmp"
	"fmt"
	"slices"
	"sort"
)

type P struct {
	Name string
	Age  int
}

func sample() []P {
	return []P{
		{"a", 30}, {"b", 20}, {"c", 30}, {"d", 20}, {"e", 30},
		{"f", 10}, {"g", 20}, {"h", 30}, {"i", 10}, {"j", 20},
		{"k", 30}, {"l", 10}, {"m", 20}, {"n", 30}, {"o", 10},
		{"p", 20}, {"q", 30}, {"r", 10}, {"s", 20}, {"t", 30},
	}
}

func names(ps []P) string {
	s := ""
	for _, p := range ps {
		s += p.Name
	}
	return s
}

func main() {
	fmt.Println("입력          :", names(sample()))

	a := sample()
	sort.Slice(a, func(i, j int) bool { return a[i].Age < a[j].Age })
	fmt.Println("sort.Slice    :", names(a), " ← 같은 나이끼리의 순서는 보장이 아니다")

	b := sample()
	sort.SliceStable(b, func(i, j int) bool { return b[i].Age < b[j].Age })
	fmt.Println("SliceStable   :", names(b), " ← 입력 순서가 유지된다")

	c := sample()
	slices.SortFunc(c, func(x, y P) int { return cmp.Compare(x.Age, y.Age) })
	fmt.Println("SortFunc      :", names(c), " ← 역시 보장이 아니다")

	d := sample()
	slices.SortStableFunc(d, func(x, y P) int { return cmp.Compare(x.Age, y.Age) })
	fmt.Println("SortStableFunc:", names(d), " ← 입력 순서가 유지된다")

	e := sample()
	slices.SortStableFunc(e, func(x, y P) int {
		return cmp.Or(cmp.Compare(x.Age, y.Age), cmp.Compare(x.Name, y.Name))
	})
	fmt.Println("두 키(cmp.Or) :", names(e), " ← 동률을 이름으로 깬다 : 결정적이다")

	fmt.Println()
	fmt.Println("두 API 의 함수 모양이 다르다")
	fmt.Println("  sort.Slice        : less(i, j int) bool  — 인덱스를 받는다")
	fmt.Println("  slices.SortFunc   : cmp(a, b E) int      — 원소를 받고 음수/0/양수를 준다")
	fmt.Println("  slices.IsSortedFunc(d, …) :", slices.IsSortedFunc(d, func(x, y P) int { return cmp.Compare(x.Age, y.Age) }))
}
```

- 다섯 정렬의 결과 문자열은 각각 무엇인가?
- 그중 **같은 것끼리** 묶어라 — 몇 무리인가?
- 다섯 중 **다시 돌려도 같다고 말할 수 있는** 것은 어느 것인가, 그 근거는 명세인가 문서인가 관찰인가?
- 동률의 순서를 **아무것에도 안 기대고** 고정하려면 무엇을 하는가?

### 8. 태그만 다른 두 타입 (경계)

```go
// t17i.go
package main

import (
	"fmt"
	"reflect"
)

type A struct {
	X int `json:"a"`
}

type B struct {
	X int `json:"b"`
}

type C struct {
	X int // 태그 없음
}

func main() {
	fmt.Println("── 태그가 달라도 「변환」은 된다 (1.8부터) ──")
	a := A{X: 1}
	b := B(a)
	c := C(a)
	fmt.Printf("  A -> B : %+v   A -> C : %+v\n", b, c)

	fmt.Println("── 그래도 타입은 다르다 ──")
	fmt.Printf("  %v %v %v\n", reflect.TypeOf(a), reflect.TypeOf(b), reflect.TypeOf(c))
	fmt.Printf("  A 와 B 의 타입이 같나 : %v\n", reflect.TypeOf(a) == reflect.TypeOf(b))
	fmt.Printf("  B 의 태그 : %q\n", reflect.TypeOf(b).Field(0).Tag)
}
```

```go
// t17j.go
package main

import "fmt"

func main() {
	var p struct {
		X int `json:"a"`
	}
	var q struct {
		X int `json:"b"`
	}
	p.X = 1
	q = p // 태그가 다르면 타입이 다르다 — 대입이 막힌다
	fmt.Println(q)
}
```

- 첫 프로그램은 컴파일되는가 — 무엇을 찍는가?
- 둘째 프로그램의 메시지 전문은 무엇인가?
- **변환은 되고 대입은 안 되는** 이유를 명세의 두 문장으로 답하라.
- 태그를 무시하는 변환은 **어느 버전부터**인가?

### 9. 크기는 몇 바이트인가 (경계)

```go
// t17l.go
package main

import (
	"fmt"
	"sort"
	"unsafe"
)

type Loose struct {
	A bool
	B int64
	C bool
}

type Tight struct {
	A bool
	C bool
	B int64
}

type Empty struct{}

func main() {
	fmt.Println("── 빈 구조체는 0바이트다 ──")
	fmt.Println("  unsafe.Sizeof(struct{}{}) =", unsafe.Sizeof(struct{}{}))
	fmt.Println("  unsafe.Sizeof(Empty{})    =", unsafe.Sizeof(Empty{}))
	fmt.Println("  [1000]struct{} 의 크기    =", unsafe.Sizeof([1000]struct{}{}))

	fmt.Println("── 그래서 집합(set)의 값 타입으로 쓴다 ──")
	set := map[string]struct{}{}
	for _, k := range []string{"ㄱ", "ㄴ", "ㄱ"} {
		set[k] = struct{}{}
	}
	keys := make([]string, 0, len(set))
	for k := range set {
		keys = append(keys, k)
	}
	sort.Strings(keys) // 맵 순회 순서는 보장이 없다 — 정렬해서 찍는다
	_, ok := set["ㄱ"]
	fmt.Printf("  set = %v  len=%d  \"ㄱ\" 있나 : %v\n", keys, len(set), ok)

	fmt.Println("── 신호용 채널에도 쓴다 : chan struct{} ──")
	done := make(chan struct{})
	go func() { close(done) }()
	<-done
	fmt.Println("  <-done 통과 — 값이 아니라 「일어났다」만 보낸다")

	fmt.Println("── 필드 순서가 크기를 바꾼다 (구현·플랫폼) ──")
	fmt.Printf("  Loose{bool,int64,bool} : size=%d align=%d  offsets=%d,%d,%d\n",
		unsafe.Sizeof(Loose{}), unsafe.Alignof(Loose{}),
		unsafe.Offsetof(Loose{}.A), unsafe.Offsetof(Loose{}.B), unsafe.Offsetof(Loose{}.C))
	fmt.Printf("  Tight{bool,bool,int64} : size=%d align=%d  offsets=%d,%d,%d\n",
		unsafe.Sizeof(Tight{}), unsafe.Alignof(Tight{}),
		unsafe.Offsetof(Tight{}.A), unsafe.Offsetof(Tight{}.C), unsafe.Offsetof(Tight{}.B))
	fmt.Println("  두 타입의 필드는 같다 — 순서만 다르다")
}
```

- `struct{}` 와 `[1000]struct{}` 의 크기는 각각 얼마인가?
- `Loose` 와 `Tight` 의 크기·오프셋은 각각 얼마인가 — 두 타입의 필드는 무엇이 다른가?
- 그 수들은 **누가 보장하는가** — 명세인가 구현인가?
- 이 프로그램이 맵을 찍을 때 한 일이 하나 있다. 무엇이고 왜인가?

### 10. 위치 리터럴은 언제 잡히나 (경계)

```go
// t17b.go
package main

import "fmt"

// 처음엔 필드가 둘이었다. 누군가 Z 를 더했다.
type Point struct {
	X int
	Y int
	Z int // ← 나중에 더해진 필드
}

func main() {
	named := Point{X: 1, Y: 2} // 필드명 리터럴 — 그대로 컴파일된다
	fmt.Println(named)

	pos := Point{1, 2} // 위치 리터럴 — 여기서 깨진다
	fmt.Println(pos)
}
```

- 이 프로그램의 메시지 전문은 무엇인가 — 어느 줄이 걸렸는가?
- 2번 프로그램은 왜 안 걸렸는가 — 둘의 차이는 무엇인가?
- `go vet` 은 위치 리터럴을 보는가 — **어떤 조건에서** 보는가?
- 그래서 실무의 규칙 한 줄을 적으면?

### 11. 다른 언어와 나란히 (연결)

- Rust 에서 「이 타입이 같음을 지원한다」를 적는 곳은 어디인가 — Go 는 어디인가?
- Rust 의 `HashMap` 키 요건은 어디에 적히는가 — Go 의 맵 키 요건은?
- 자바에서 두 객체가 같은지 정하는 것은 무엇인가 — Go 의 `==` 와 무엇이 다른가?
- C 의 구조체에 `==` 가 있는가 — Go 는?
- Go 의 필드 태그에 해당하는 것이 자바에는 무엇인가?

### 12. 다른 주제와 잇기 (연결)

- 구조체 대입이 얕은 복사인 것의 정본은 몇 번 주제인가?
- 「배열은 값, 슬라이스는 헤더」의 정본은 몇 번 주제인가?
- 맵 순회 순서가 무작위인 것의 정본은 몇 번 주제인가?
- 태그를 실제로 읽는 쪽(JSON)의 정본은 몇 번 주제인가?
- 「필드 이름을 안 적은 필드」가 무엇을 하는지는 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

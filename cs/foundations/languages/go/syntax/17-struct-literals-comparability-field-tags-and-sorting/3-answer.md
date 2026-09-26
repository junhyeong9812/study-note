# go/syntax/17 — 구조체: 리터럴·비교 가능성·필드 태그·정렬 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> 블록은 전부 `===== 소스: … =====` 로 소스를 먼저 싣는다 — **그대로 다시 던질 수 있게** 하기 위해서다.
> ★ **근거로 읽을 칸** — 값, `==` 의 참거짓, `%T` 가 찍는 타입 이름, `len`,
> 컴파일 에러 문장과 `파일:줄:칸`, 패닉 메시지 본문과 `파일:줄`, 종료 코드, `reflect` 가 돌려준 태그 원문.
> **근거로 읽지 않을 칸** — 패닉 첫 줄의 `pc=0x…`, 스택의 `goroutine N` 과 `+0x…`,
> `unsafe.Sizeof`·`Offsetof` 의 **수**(플랫폼), **불안정 정렬이 내놓은 순서**(보장 아님).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 필드명 꼴은 빠뜨려도 되고 위치 꼴은 전부 적어야 한다

**출력**

```text
===== 소스: t17a.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
① a={1 2} b={1 2} c={1 0}   a==b : true
② d={1 2}   d==a : true
③ l1={{1 2} {3 4} ㄱ}
   l2={{1 2} {3 4} ㄱ}   l1==l2 : true
④ ps=[{1 2} {3 0}] m=map[ㄱ:{1 2}]
⑤ z1={0 0} z2={0 0}   z1==z2 : true
⑥ anon={ㄴ 7}  타입=struct { Name string; N int }
⑦ p={8 9}  타입=*main.Point
(exit 0)
```

**왜 그런가**

- ①에서 `a == b` 가 **`true`** 다 — 필드명 리터럴은 **순서가 뜻이 아니다.**
  `c={1 0}` 은 **빠진 필드가 제로값**이기 때문이다. 명세:

  > **The element list does not need to have an element for each struct field.
  > Omitted fields get the zero value for that field.**

- ②의 `Point{1, 2}` 는 **전부 순서대로** 적은 것이라 `a` 와 같다.

  > **For struct literals without keys, the element list must contain an element for each struct field
  > in the order in which the fields are declared.**

- ③ 중첩에서 **안쪽 타입 이름을 생략**할 수 있고(`Line{Point{1,2}, …}`),
  ④ 배열·슬라이스·맵의 원소에서는 **`{1, 2}` 로만** 적는다.
- ⑤ `var z Point` 와 `Point{}` 가 같다 — 구조체에 「초기화 안 됨」이 없다
  ([02번 주제](../02-variable-declarations-and-zero-values/)).
- ⑥ 익명 구조체의 `%T` 는 **`struct { Name string; N int }`** 다. 이름이 없으니 구조가 곧 이름이다.
- ⑦ `&Point{…}` — 명세가 **복합 리터럴에 한해** 주소 연산을 허용한다
  ("Taking the address of a composite literal generates a pointer to a unique variable").
  변수가 아닌데도 되는 **예외**다.
- 층 — 전부 **명세 보장**이다.

### 2. ★★ 필드 순서만 바꾸면 컴파일러도 `vet` 도 침묵한다

**출력**

```text
===== 소스: t17c.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
── 위치 리터럴 User{1001, 30} 을 두 정의에 각각 ──
  V1: ID=1001 Age=30
  V2: ID=30 Age=1001   ← 1001살이 되었다
── 필드명 리터럴은 그대로다 ──
  V1: ID=1001 Age=30
  V2: ID=1001 Age=30
── 컴파일러는 한 마디도 안 했다 : go vet 도 이 자리를 안 본다 ──
(exit 0)
```

```text
===== 명령: go vet ./... =====
(exit 0)
```

**왜 그런가**

- ★★★ 두 정의는 **필드 개수도 타입도 같고 순서만 다르다.**
  그래서 위치 리터럴 `User{1001, 30}` 이 V2 에서는 **`ID=30 Age=1001`** 이 된다.
  **1001살이 되었는데 컴파일은 성공(exit 0)이고 `go vet` 은 출력 0줄에 exit 0** 이다.
- 필드명 리터럴 쪽은 **두 정의에서 똑같다** — 키가 필드를 고르므로 순서가 상관없다.
- **컴파일러가 잡아 주는 판**을 만들려면 **필드 개수를 바꾸면** 된다 — 10번의 프로그램이 그것이다
  (`too few values in struct literal of type Point`).
  ★ 즉 **개수 변화는 시끄럽고 순서 변화는 조용하다.**
- 층 — 「위치 리터럴이 선언 순서를 따른다」는 **명세 보장**,
  「`go vet` 이 같은 패키지를 안 본다」는 **도구(구현)** 다.

### 3. ★★★ 일곱 중 여섯이 막힌다 — 그 목록이 곧 규칙이다

**출력**

```text
===== 소스: t17d.go =====
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
===== 명령: go build -trimpath -gcflags=-e -o prog . =====
# ex
./t17d.go:27:14: invalid operation: HasSlice{} == HasSlice{} (struct containing []int cannot be compared)
./t17d.go:28:14: invalid operation: HasMap{} == HasMap{} (struct containing map[string]int cannot be compared)
./t17d.go:29:14: invalid operation: HasFunc{} == HasFunc{} (struct containing func() cannot be compared)
./t17d.go:30:14: invalid operation: Outer{} == Outer{} (struct containing HasSlice cannot be compared)
./t17d.go:33:14: invalid operation: s1 == s2 (slice can only be compared to nil)
./t17d.go:36:14: invalid operation: a1 == a2 ([2][]int cannot be compared)
(exit 1)
```

**왜 그런가**

- 거부되지 **않는** 것은 ①뿐이다. `HasArr` 의 필드는 `[2]int` 하나이고 **배열은 비교 가능**하다.
- 명세가 규칙을 그대로 적는다.

  > **Struct types are comparable if all their field types are comparable.**

  > **Array types are comparable if their array element types are comparable.**

  > **Slice, map, and function types are not comparable.** However, as a special case, a slice, map,
  > or function value may be compared to the predeclared identifier `nil`.

- ★★ ⑤ `Outer` 는 슬라이스 필드가 **직접 없는데도** 막힌다 —
  `struct containing HasSlice cannot be compared`.
  **비교 불가는 필드를 따라 안쪽에서 바깥으로 번진다.** 한 칸이 타입 전체의 `==` 를 앗아간다.
- ⑥과 ⑦의 문구가 다른 이유 — ⑥은 **슬라이스 자체**라 `slice can only be compared to nil` 로
  「`nil` 하고만 된다」는 **예외를 알려 주고**, ⑦은 **배열**이라 그 예외가 없어
  `[2][]int cannot be compared` 로 끝난다.
- 층 — 규칙은 **명세 보장**, 문장은 **툴체인 판(go1.27.1)** 의 것이다.

### 4. ★★ 컴파일은 통과하고 실행에서 터진다

**출력**

```text
===== 소스: t17e.go =====
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
===== 명령: go build -trimpath -o prog . =====
(exit 0)
```

```text
===== 명령: ./prog 2>&1 =====
-- 비교되는 것들 --
배열 필드 : true
포인터 필드(같은 값, 다른 칸) : false
포인터 필드(같은 칸)         : true
any 에 int 를 담아 : true
any 에 다른 타입을 : false
-- 이제 any 에 슬라이스를 담고 비교한다 --
panic: runtime error: comparing uncomparable type []int

goroutine 1 [running]:
main.main()
	ex/t17e.go:33 +0x308
(exit 2)
```

```text
===== 소스: t17f.go =====
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
===== 명령: go build -trimpath -o prog . =====
(exit 0)
```

```text
===== 명령: ./prog 2>&1 =====
① m[Key{a,1}] = 10  len = 2
② 없는 키 : 0 false
③ ma[[2]int{1,2}] = ㄱ
④ map[any]int 에 셋을 넣었다 : len = 3
-- 이제 슬라이스를 키로 넣는다 --
panic: runtime error: hash of unhashable type []int

goroutine 1 [running]:
main.main()
	ex/t17f.go:36 +0x5f8
(exit 2)
```

**왜 그런가**

- **두 빌드가 다 성공**한다(exit 0). 명세가 **인터페이스를 비교 가능한 타입**으로 치기 때문이다.
- 첫 프로그램의 앞 다섯 줄 —
  **배열 필드**는 원소끼리 견주어 `true`,
  **포인터 필드(같은 값, 다른 칸)** 는 **`false`**, **같은 칸**이면 `true`,
  `any` 에 **같은 타입·같은 값**이면 `true`, **타입이 다르면**(`int` 대 `int64`) `false`.

  > Two pointer values are equal **if they point to the same variable** or if both have value nil.

  > Two interface values are equal if they have **identical dynamic types** and equal dynamic values.

- 둘째 프로그램은 ①\~④를 찍는다 — 비교 가능한 구조체가 맵 키가 되고, **배열도 키**가 되며,
  **`map[any]int` 는 셋을 받아 `len` 이 3**이다.
- ★★★ **마지막 줄에서 둘 다 패닉한다. 그런데 문구가 다르다.**

| 프로그램 | 전문 | 종료 코드 |
|---|---|---|
| `t17e`(구조체의 `==`) | `panic: runtime error: comparing uncomparable type []int` | **2** |
| `t17f`(맵 키) | `panic: runtime error: hash of unhashable type []int` | **2** |

  **같은 성질에 두 이름**이다 — **어느 연산에서 걸렸는지**가 문구로 드러난다.
  앞엣것은 **견주다** 걸렸고 뒤엣것은 **해싱하다** 걸렸다.
- 명세가 둘을 각각 적는다.

  > **A comparison of two interface values with identical dynamic types causes a run-time panic
  > if that type is not comparable.** … also when comparing arrays of interface values or
  > **structs with interface-valued fields**.

  > **If the key type is an interface type, these comparison operators must be defined for the dynamic
  > key values; failure will cause a run-time panic.**

- ★ 「포인터 필드(같은 값, 다른 칸)」가 `false` 인 것이 이 절의 작은 함정이다 —
  **`==` 는 가리키는 값이 아니라 가리키는 칸을 본다.**
  [16번 주제](../16-pointers-value-copy-semantics-new-and-make/) (2)절의 「같나 다르나」와 같은 물음이다.
- 층 — 「패닉한다」는 **명세 보장**, **문구**는 런타임(구현)이다.

### 5. 컴파일에서 걸리는 쪽 — 이유를 안 말해 준다

**출력**

```text
===== 소스: t17g.go =====
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
===== 명령: go build -trimpath -gcflags=-e -o prog . =====
# ex
./t17g.go:10:13: invalid map key type BadKey
./t17g.go:13:17: invalid map key type []int
./t17g.go:16:20: invalid map key type func()
(exit 1)
```

**왜 그런가**

- 세 줄 전문은 **`invalid map key type BadKey`·`invalid map key type []int`·
  `invalid map key type func()`** 이고 exit 1 이다.
- ★★ **셋 다 한 문장**이고 **이유를 안 말한다.**
  3번의 에러는 `struct containing []int cannot be compared` 처럼 **무엇 때문인지**를 말해 줬는데,
  이쪽은 **「키가 될 수 없다」까지만** 말한다.
  ★ `BadKey` 가 왜 안 되는지는 **3번에서 가져와야** 한다 — 안에 `[]string` 이 있기 때문이다.
- ★★ **무엇이 갈랐나**(4번의 둘째 프로그램과 견주면) — **키 타입이 정적으로 적혔나**다.
  `map[BadKey]int` 는 **컴파일 시점에** 비교 불가가 보이고,
  `map[any]int` 는 **담기는 동적 타입을 실행 전에는 모른다.** 명세가 그 둘을 나란히 적는다.

  > The comparison operators `==` and `!=` **must be fully defined for operands of the key type**;
  > thus the key type must not be a function, map, or slice.
  > **If the key type is an interface type, these comparison operators must be defined for the dynamic
  > key values; failure will cause a run-time panic.**

- **맵 키의 요건을 한 문장으로** — 「**키 타입은 비교 가능해야 하고, 인터페이스면 그 판정이 실행으로 미뤄진다**」.
- 층 — 규칙은 **명세 보장**, 문구는 **툴체인 판**이다.

### 6. ★★★ 태그는 `reflect` 로만 보인다 — 「otherwise ignored」

**출력**

```text
===== 소스: t17h.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
── reflect 로만 보이는 것 : 필드 태그 ──
  ID    json="id"             true   db="user_id"  true 
        원문 = "json:\"id\" db:\"user_id\""
  Name  json="name,omitempty" true   db=""         false
        원문 = "json:\"name,omitempty\" validate:\"required\""
  Email json="-"              true   db=""         false
        원문 = "json:\"-\""
  Note  json=""               false  db=""         false
        원문 = ""
── Get 은 없는 키에 빈 문자열을 준다 — Lookup 이라야 「없음」이 보인다 ──
  Get("없는키")    = ""
  Lookup("없는키") = "", false
── 태그는 프로그램 동작을 바꾸지 않는다. 읽는 쪽이 있어야 뜻이 생긴다 ──
  json.Marshal : {"id":7,"Note":"ㄴ"}
  fmt 는 태그를 모른다 : {7  a@b ㄴ}
(exit 0)
```

**왜 그런가**

- 네 필드가 각각 이렇게 나온다 —
  `ID` 는 `json="id"`·`db="user_id"` 둘 다 `true`,
  `Name` 은 `json="name,omitempty"` 만 `true`,
  `Email` 은 `json="-"`,
  **`Note` 는 태그 자체가 없어 원문이 `""`** 이고 `Lookup` 이 전부 `false` 다.
- **`Get` 과 `Lookup` 이 둘 다 필요한 이유** — `Get("없는키")` 는 **빈 문자열**을 준다.
  `Lookup` 이라야 `"", false` 로 **「없다」가 보인다.**
  「빈 값으로 적힌 태그」와 「없는 태그」는 `Get` 으로 구분되지 않는다.
- **`json.Marshal` 의 결과는 `{"id":7,"Note":"ㄴ"}`** — 네 필드 중 **둘**만 들어갔다.
  `Name` 은 값이 비어 `omitempty` 로, `Email` 은 `json:"-"` 로 빠졌고,
  태그 없는 `Note` 는 **필드 이름 그대로** 들어갔다.
- ★★★ 마지막 줄 — **`fmt` 는 `{7  a@b ㄴ}`** 을 낸다. **태그를 전혀 모른다.**
  그것이 명세의 한 구절을 증명한다.

  > **The tags are made visible through a reflection interface** and take part in type identity for
  > structs **but are otherwise ignored.**

  ★ 그래서 **태그 오타는 조용하다** — 컴파일러도 `vet` 도 `fmt` 도 말이 없고, 읽는 쪽의 결과만 달라진다.
- 층 — 전부 **명세 보장**이다. 다만 `json` 의 `omitempty`·`-` 관례는 **`encoding/json` 의 계약**이다.

### 7. 다섯 판이 두 무리로 갈린다

**출력**

```text
===== 소스: t17k.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
입력          : abcdefghijklmnopqrst
sort.Slice    : frolipmsbjgdkncaqeht  ← 같은 나이끼리의 순서는 보장이 아니다
SliceStable   : filorbdgjmpsacehknqt  ← 입력 순서가 유지된다
SortFunc      : frolipmsbjgdkncaqeht  ← 역시 보장이 아니다
SortStableFunc: filorbdgjmpsacehknqt  ← 입력 순서가 유지된다
두 키(cmp.Or) : filorbdgjmpsacehknqt  ← 동률을 이름으로 깬다 : 결정적이다

두 API 의 함수 모양이 다르다
  sort.Slice        : less(i, j int) bool  — 인덱스를 받는다
  slices.SortFunc   : cmp(a, b E) int      — 원소를 받고 음수/0/양수를 준다
  slices.IsSortedFunc(d, …) : true
(exit 0)
```

**왜 그런가**

- 결과는 이렇게 갈린다.

| 판 | 결과 | 무리 |
|---|---|---|
| `sort.Slice` | `frolipmsbjgdkncaqeht` | **불안정** |
| `slices.SortFunc` | `frolipmsbjgdkncaqeht` | **불안정** |
| `sort.SliceStable` | `filorbdgjmpsacehknqt` | **안정** |
| `slices.SortStableFunc` | `filorbdgjmpsacehknqt` | **안정** |
| `cmp.Or` 두 키 | `filorbdgjmpsacehknqt` | **키가 둘이라 답이 하나** |

  → **두 무리**다. 셋째 무리처럼 보이는 마지막 줄은 **우연히 안정 정렬과 같은 답**이다
  (입력이 나이 무리 안에서 이미 이름 순이었기 때문이다).
- **다시 돌려도 같다고 말할 수 있는 것**은 **안정 정렬 둘과 `cmp.Or` 판**이다.
  근거는 **명세가 아니라 패키지 문서**다 — `sort.SliceStable` 이 "keeping equal elements in
  their original order" 를 약속한다. 불안정 쪽은 `sort.Slice` 문서가
  "**is not guaranteed to be stable**" 이라고 적으므로 **이 판의 관찰**로만 읽는다.
  ★ 같은 판에서 **세 번 돌려 md5 가 같았지만** 그것은 보장이 아니다.
- **아무것에도 안 기대는 법** — `cmp.Or(비교1, 비교2)` 로 **동률을 깨는 둘째 키**를 준다(`cmp.Or` 는 1.22).
  ★ 안정 정렬은 「입력 순서」에 기대고, 키를 더하는 것은 **아무것에도 안 기댄다.**
- 두 API 의 함수 모양이 다르다 — `less(i, j int) bool` 대 `cmp(a, b E) int`.
  `slices`·`cmp` 는 **1.21부터**다.
- 층 — 「정렬된다」는 패키지 계약, **동률의 순서**는 안정 쪽만 계약이고 불안정 쪽은 **관찰**이다.

### 8. 변환은 태그를 무시하고 동일성은 무시하지 않는다

**출력**

```text
===== 소스: t17i.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
── 태그가 달라도 「변환」은 된다 (1.8부터) ──
  A -> B : {X:1}   A -> C : {X:1}
── 그래도 타입은 다르다 ──
  main.A main.B main.C
  A 와 B 의 타입이 같나 : false
  B 의 태그 : "json:\"b\""
(exit 0)
```

```text
===== 소스: t17j.go =====
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
===== 명령: go build -trimpath -gcflags=-e -o prog . =====
# ex
./t17j.go:13:6: cannot use p (variable of type struct{X int "json:\"a\""}) as struct{X int "json:\"b\""} value in assignment
(exit 1)
```

**왜 그런가**

- 첫 프로그램은 컴파일된다. `B(a)`·`C(a)` 둘 다 되고 값은 `{X:1}` 그대로다.
  `reflect.TypeOf(a) == reflect.TypeOf(b)` 는 **`false`**, 변환된 `b` 의 태그는 **받는 타입의 것**(`json:"b"`)이다.
- 둘째 프로그램은 막힌다 —
  **`cannot use p (variable of type struct{X int "json:\"a\""}) as struct{X int "json:\"b\""} value in assignment`**.
  에러가 **타입 이름 안에 태그를 그대로 박아** 보여 준다.
- 명세의 두 문장이 그 갈림이다.

  > Two struct types are identical if they have the same sequence of fields, and if corresponding pairs
  > of fields have the same names, **identical types, and identical tags**, and are either both embedded
  > or both not embedded.

  > **Struct tags are ignored when comparing struct types for identity for the purpose of conversion.**

- **태그를 무시하는 변환은 1.8부터**다. 그 전에는 명세의 예제인 `(*Person)(data)` 가 안 됐다.
- ★ 명명 타입끼리는 어차피 변환을 적으므로 잘 안 걸리고, **익명 구조체에서 걸린다.**
- 층 — 둘 다 **명세 보장**이고, 1.8 이라는 **판 경계**가 붙는다.

### 9. 0바이트 · 24바이트 · 16바이트 — 뒤의 둘은 구현이다

**출력**

```text
===== 소스: t17l.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
── 빈 구조체는 0바이트다 ──
  unsafe.Sizeof(struct{}{}) = 0
  unsafe.Sizeof(Empty{})    = 0
  [1000]struct{} 의 크기    = 0
── 그래서 집합(set)의 값 타입으로 쓴다 ──
  set = [ㄱ ㄴ]  len=2  "ㄱ" 있나 : true
── 신호용 채널에도 쓴다 : chan struct{} ──
  <-done 통과 — 값이 아니라 「일어났다」만 보낸다
── 필드 순서가 크기를 바꾼다 (구현·플랫폼) ──
  Loose{bool,int64,bool} : size=24 align=8  offsets=0,8,16
  Tight{bool,bool,int64} : size=16 align=8  offsets=0,1,8
  두 타입의 필드는 같다 — 순서만 다르다
(exit 0)
```

**왜 그런가**

- **`struct{}` 는 0**이고 **`[1000]struct{}` 도 0**이다. 0을 1000번 더해도 0이다.
- `Loose{bool,int64,bool}` 은 **24바이트**(오프셋 0,8,16),
  `Tight{bool,bool,int64}` 는 **16바이트**(오프셋 0,1,8)다.
  **두 타입의 필드는 같고 순서만 다르다** — `bool` 둘을 붙여 두면 패딩이 한 덩이로 줄어든다.
- ★★★ **그 수를 명세가 보장하지 않는다.** 명세에는 구조체 크기 규정이 없고
  「패딩」은 예제 주석(`_ float32 // padding`)에만 나온다.
  **`unsafe.Sizeof` 가 내놓는 것은 이 컴파일러·이 플랫폼(amd64)의 값**이다.
  원리는 [`../../../../data-representation/`](../../../../data-representation/)가 정본이다.
- 맵을 찍을 때 한 일은 **키를 모아 `sort.Strings` 로 정렬한 것**이다.
  맵 순회 순서는 보장이 없어 **그대로 찍으면 다시 돌릴 때 달라질 수 있다**
  ([09번 주제](../09-maps-declaration-comma-ok-delete-and-iteration-order/)).
- 층 — `struct{}` 의 쓰임은 **관용**, 크기 수치는 **구현·플랫폼**이다.

### 10. 개수 변화는 시끄럽고 순서 변화는 조용하다

**출력**

```text
===== 소스: t17b.go =====
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
===== 명령: go build -trimpath -o prog . =====
# ex
./t17b.go:16:19: too few values in struct literal of type Point
(exit 1)
```

```text
===== 소스: t17vet.go =====
package main

import (
	"fmt"
	"net"
)

type Local struct{ A, B int }

func main() {
	l := Local{1, 2}                                   // 같은 패키지 — vet 이 안 본다
	r := net.TCPAddr{net.IPv4(1, 2, 3, 4), 80, "eth0"} // 다른 패키지 — vet 이 본다
	fmt.Println(l, r.Port)
}
===== 명령: go build -trimpath -o prog . =====
(exit 0)
```

```text
===== 명령: go vet ./... =====
t17vet.go:12:7: net.TCPAddr struct literal uses unkeyed fields
(exit 1)
```

**왜 그런가**

- 메시지는 **`./t17b.go:16:19: too few values in struct literal of type Point`** — **16번째 줄**,
  즉 `pos := Point{1, 2}` 가 걸렸다. 바로 위의 `Point{X: 1, Y: 2}` 는 **아무 일 없다.**
- 2번 프로그램이 안 걸린 이유 — 거기서는 **필드 개수가 그대로**이고 순서만 바뀌었다.
  위치 리터럴의 계약은 「**개수와 순서**」인데, 컴파일러가 셀 수 있는 것은 **개수뿐**이다.
- ★★ **`go vet` 은 남의 패키지 타입의 위치 리터럴만 본다** —
  같은 패키지의 `Local{1, 2}` 는 통과하고 **`net.TCPAddr{…}` 만** `struct literal uses unkeyed fields` 로 잡혔다.
  ★ 그래서 「`vet` 이 잡아 준다」로 적으면 틀린다. **내 패키지 안은 무방비다.**
- 실무 규칙 한 줄 — **필드명 리터럴을 기본값으로 쓴다.**
  위치 리터럴은 `Point{1, 2}` 처럼 **필드가 절대 안 늘 작은 타입**에만 남긴다.
- 층 — 에러 규칙은 **명세 보장**, `vet` 의 범위는 **도구(구현)** 다.

### 11. 다른 언어와 나란히

**출력** — 없음(연결 문항).

**왜 그런가**

| 물음 | **Go** | **Rust** | **Java** | **C** |
|---|---|---|---|---|
| 「같음」을 적는 곳 | ★ **없다** — 언어 규칙 | `impl Eq for T`(또는 `derive`) | `equals` 를 사람이 구현 | 해당 없음 |
| 그 규칙의 내용 | 필드가 전부 비교 가능하면 재귀로 `==` | 사람이 쓴 `eq` 가 답 | 사람이 쓴 메서드가 답 | `==` 없음, `memcmp` 는 패딩까지 본다 |
| 해시 맵 키 요건 | 「비교 가능한 타입」이라는 **언어 규칙** | `K: Eq + Hash` **타입 경계** | `hashCode`/`equals` 계약 | 해당 없음 |
| 어기면 | ★ **어길 수가 없다** | 계약 위반 — **값이 사라진다** | 계약 위반 — 값이 사라진다 | 해당 없음 |
| 메타데이터 | **필드 태그**(문자열, `reflect`) | 속성(`#[serde(rename)]`, 매크로가 읽음) | **애너테이션**(`@JsonProperty`, 리플렉션) | 해당 없음 |

- ★★★ **결정적인 갈림은 「누가 정하나」다.**
  Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **28번**은
  「**컴파일러가 강제하는 것은 `impl` 의 존재뿐이고 계약은 사람이 지킨다**」로 끝난다.
  Go 는 정반대다 — **사람이 쓸 자리가 없고 언어가 전부 정한다.**
  그래서 **어길 수가 없고**, 대신 **고칠 수도 없다**(대소문자 무시 비교 같은 것을 `==` 에 넣지 못한다).
- 자바와의 갈림은
  [`../../../java/syntax/27-equals-hashcode-contract/`](../../../java/syntax/27-equals-hashcode-contract/)가 정본이다 —
  그쪽의 값어치는 **「계약을 어기면 무엇이 사라지나」** 이고, Go 에는 그 이야기가 아예 없다.
- C 와의 갈림 — C 구조체에는 `==` 가 **없다.** `memcmp` 로 견주면 **패딩 바이트까지 보므로**
  같은 값이 다르게 나올 수 있다. Go 는 **필드만** 견준다("corresponding non-blank field values").
- 태그와 애너테이션 — 자바의 애너테이션은 **타입이 있고 컴파일러가 검사**하는데
  Go 의 태그는 **그냥 문자열**이다. 그래서 오타를 아무도 안 잡는다(6번).

### 12. 다른 주제와 잇기

**출력** — 없음(연결 문항).

**왜 그런가**

- **구조체 대입이 얕은 복사인 것** — [16번 주제](../16-pointers-value-copy-semantics-new-and-make/) (2)절.
  **이 주제의 직접 선행**이다.
- **「배열은 값, 슬라이스는 헤더」** — [05번 주제](../05-arrays-vs-slices-value-and-header/).
  그 갈림이 여기서 **`==` 로 한 번 더** 나온다(3번).
- **맵 순회 순서가 무작위인 것** — [09번 주제](../09-maps-declaration-comma-ok-delete-and-iteration-order/).
  9번 프로그램이 정렬해서 찍은 이유다.
- **태그를 실제로 읽는 쪽** — 목록의 **45번 주제**(`encoding/json`).
  여기는 **태그가 무엇이고 어떻게 보이나**까지, 그쪽은 **`omitempty`·포인터·스트리밍**부터다.
- **「필드 이름을 안 적은 필드」** — [18번 주제](../18-embedding-and-field-method-promotion/).
  **이 주제의 직접 후행**이고, 거기서 `struct{ Base }` 가 무엇을 하는지 본다.
- 덤 — **정렬 API 의 정본**은 목록의 **38번 주제**,
  **`comparable` 제약**은 목록의 **22번**·**37번 주제**,
  **크기 재는 일 자체의 비용**은 목록의 **50번 주제**다.

---

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행 1회** | 재실행 결과가 `normalize-shaky.py` 로 **동일** |
| 판 확인 | `go version` · `go env GOOS GOARCH GOVERSION` | 1 | `go1.27.1 linux/amd64` |
| 리터럴 일곱 (`t17a`) | `go build && ./prog` | 1 | `a==b` 가 `true` · `c={1 0}` · 익명 `%T` |
| ★★ 필드 순서 (`t17c`) | 〃 + `go vet ./...` | 2 | `ID=30 Age=1001` · **vet 출력 0줄 exit 0** |
| ★★★ 비교 가능성 (`t17d`) | `go build -gcflags=-e` | 1 | 에러 **6건** · ①만 통과 · exit 1 |
| ★ `any` 필드 (`t17e`) | `go build` · `./prog 2>&1` | 2 | 빌드 0 · `comparing uncomparable type []int` · **exit 2** |
| 맵 키 (`t17f`) | 〃 | 2 | `hash of unhashable type []int` · **exit 2** |
| 맵 키 거부 (`t17g`) | `go build -gcflags=-e` | 1 | `invalid map key type` **3건** · exit 1 |
| ★★★ 필드 태그 (`t17h`) | `go build && ./prog` | 1 | `Lookup` 넷 · `{"id":7,"Note":"ㄴ"}` · `fmt` 는 태그를 모름 |
| 태그와 변환 (`t17i`) | 〃 | 1 | `B(a)`·`C(a)` 통과 · 타입은 다름 |
| 태그와 동일성 (`t17j`) | `go build -gcflags=-e` | 1 | 대입 거부 · 에러에 태그가 박힘 |
| 정렬 다섯 (`t17k`) | `go build && ./prog` | 1 + **md5 3판** | 두 무리 · 3판 md5 동일(그래도 보장 아님) |
| 빈 구조체·패딩 (`t17l`) | 〃 | 1 | `struct{}`=0 · `Loose`=24 · `Tight`=16 |
| 위치 리터럴 (`t17b`) | `go build` | 1 | `too few values in struct literal of type Point` · exit 1 |
| `vet` 의 경계 (`t17vet`) | `go build` · `go vet ./...` | 2 | 같은 패키지 통과 · `net.TCPAddr` 만 잡힘 · exit 1 |
| 형태 (`t17form`) | `go build && ./prog` | 1 | 세 줄 |

**구현·환경에 달린 항목**(버전이 오르거나 타깃이 바뀌면 **다시 찍어야 하는** 것)

| 항목 | 무엇에 달렸나 |
|---|---|
| `unsafe.Sizeof`·`Offsetof` 의 **수**(0·24·16·0,8,16·0,1,8) | **플랫폼·컴파일러.** 명세에 그 수가 없다 |
| **불안정 정렬이 내놓은 순서**(`frolipms…`) | **구현.** `sort` 문서가 "not guaranteed to be stable" 이라고 적는다 |
| 패닉 **메시지 본문** 둘 | **런타임(구현)**. 명세는 「패닉한다」까지만 정한다 |
| 패닉 첫 줄의 `pc=0x…` · 스택의 `goroutine N` · `+0x…` | **빌드 산출물·런타임** |
| 컴파일 에러의 **문구 자체** | **툴체인 판(go1.27.1)** |
| `go vet` 이 **남의 패키지 것만** 보는 것 | **도구(구현)**. 판이 바뀌면 넓어질 수 있다 |
| 구조체 대입·맵 해싱·정렬의 **실제 비용** | ★ **안 쟀다.** 벤치마크가 없다(목록의 **50번 주제**) |
| 필드를 몰아 두면 **빨라지는가** | ★ **안 쟀다.** 크기가 준 것만 봤다 |
| `reflect.DeepEqual` 과 `==` 의 차이 | ★ **안 던졌다**(「더 들어가면」) |
| 빈 식별자 필드(`_ [4]byte`) | ★ **안 던졌다** |
| `go vet` 의 `structtag` 검사 | ★ **안 던졌다** |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다.

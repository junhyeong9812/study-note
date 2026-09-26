# go/syntax/17 — 구조체: 리터럴·비교 가능성·필드 태그·정렬 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Go 명세](https://go.dev/ref/spec) 의 Struct types · Composite literals ·
> Comparison operators · Map types · Type identity · Conversions 절.\
> 웹이 아니라 **이 툴체인이 들고 있는 `$(go env GOROOT)/doc/go_spec.html` 을 열어** 인용했다.
> 그 파일의 머리는 「**Language version go1.27 (May 26, 2026)**」이다.
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> **버전** — 비교 가능성·리터럴·태그 규칙은 **1.0부터 지금까지 같다.**
> 이 주제에서 판 경계가 있는 것은 **태그를 무시하는 변환**(1.8)과 `slices`·`cmp` 패키지(1.21) 둘이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 명세로, 출력은 실행으로 접지했다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것. 어느 컴파일러에서도 같다 | `go_spec.html` 원문 인용 |
| **구현(gc)** | 이 컴파일러·런타임이 그렇게 하는 것. 약속은 아니다 | 구조체 크기·필드 오프셋 · 불안정 정렬이 내놓은 순서 · 패닉 문구 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 실행 출력(재실행 대조까지) |

★★ 이 주제에서 **명세 보장 칸이 가장 큰 자리가 「비교 가능성」이다.**
「슬라이스 필드가 있으면 `==` 가 안 된다」는 컴파일러 사정이 아니라 **명세의 문장**이다.
★★ 반대로 **`unsafe.Sizeof` 가 내놓는 24와 16은 구현·플랫폼**이다 — 명세에는 그 수가 없다.

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
| **흔들린다** | 패닉 첫 줄의 `pc=0x…` 주소 · 스택의 `goroutine N` 과 `+0x…` 오프셋 | 빌드 산출물·런타임에 달렸다 |
| **흔들린다** | 맵 순회 순서 | 그래서 이 문서는 맵을 찍을 때 **정렬해서** 찍는다((9)절) |
| **흔들릴 수 있다** | `unsafe.Sizeof`·`Offsetof` 의 수 | **플랫폼·컴파일러**가 정한다. 명세의 수가 아니다 |
| **흔들릴 수 있다** | `sort.Slice`·`slices.SortFunc` 가 동률을 늘어놓는 순서 | **보장이 아니다.** 판이 바뀌면 달라질 수 있다 |
| 안 흔들린다 | 컴파일 에러 문장 본문과 `파일:줄:칸` | 같은 소스·같은 판이면 같다 |
| 안 흔들린다 | 패닉·치명 오류의 **메시지 본문** · 종료 코드 | 런타임이 정한 문장이다 |
| 안 흔들린다 | `==` 의 참거짓 · `%T` 가 찍는 타입 이름 · `len` | 〃 |
| 안 흔들린다 | `reflect` 가 돌려주는 **태그 원문**과 `Lookup` 의 참거짓 | 태그는 소스에 적힌 문자열 그대로다 |
| 안 흔들린다 | **안정 정렬**(`SliceStable`·`SortStableFunc`)의 결과 | **명세가 아니라 패키지 문서의 보장**이다 |
| 해당 없음 | 포인터 값 | 이 문서는 주소를 한 번도 안 찍는다 — `==` 로 **같나 다르나**만 묻는다((4)절) |

★ 같은 판에서 **세 번 돌려 md5 가 같았다** — 그래도 불안정 정렬의 결과는 「이 판의 관찰」로만 적는다.

## 한눈에 — 쉽게 말하면

**구조체는 「값들을 한 칸에 붙여 놓은 것」이다.** 그래서 세 가지가 따라온다 —
**통째로 복사되고**, **필드가 전부 비교 가능하면 통째로 비교되며**, **필드를 붙여 놓은 순서가 크기를 정한다.**

| 비유 | 실체 |
|---|---|
| 서류 양식에 칸을 채운다 | **필드명 리터럴** `Point{X: 1, Y: 2}` — 칸 이름을 적는다 |
| 칸 이름 없이 순서대로 채운다 | **위치 리터럴** `Point{1, 2}` — 양식이 바뀌면 틀어진다 |
| 두 서류를 겹쳐 보고 같은지 본다 | **`==`** — 모든 칸이 「겹쳐 볼 수 있는 것」이라야 한다 |
| 겹쳐 볼 수 없는 칸이 하나라도 있으면 | **슬라이스·맵·함수 필드** — 서류 전체가 `==` 불가가 된다 |
| 서류를 서랍의 이름표로 쓴다 | **맵 키** — 겹쳐 볼 수 있는 서류만 이름표가 된다 |
| 칸 옆에 연필로 쪽지를 붙인다 | **필드 태그** — 프로그램은 안 읽는다. `reflect` 로 보는 쪽만 읽는다 |
| 칸 사이에 빈 자리가 생긴다 | **패딩** — 필드 순서를 바꾸면 크기가 줄기도 한다 |

```text
   type Row struct { ID int; Tags []string }

   ┌──────────────── Row 한 칸 ────────────────┐
   │ ID : int          │ Tags : []int 헤더 3칸 │
   │ [ 1 ]             │ [ptr][len][cap]───┐   │
   └───────────────────┴───────────────────┼───┘
                                           v
                                  기반 배열 ["a" "b"]

   · 대입하면 위 칸 전체가 복사된다(16번 주제)
   · == 는 막힌다 — Tags 가 「겹쳐 볼 수 없는 칸」이기 때문이다
```

> **비교 가능(comparable)** — `==`·`!=` 를 쓸 수 있는 타입.\
> 예: `int`·`string`·포인터·배열은 되고, **슬라이스·맵·함수는 안 된다.**

> **필드 태그(struct tag)** — 필드 선언 뒤에 붙이는 문자열 리터럴.\
> 예: `` ID int `json:"id"` `` — `encoding/json` 이 `reflect` 로 읽어 키 이름을 정한다.

> **패딩(padding)** — 정렬(alignment) 맞추려고 필드 사이에 넣는 빈 바이트.\
> 예: `bool`·`int64`·`bool` 순서면 24바이트, `bool`·`bool`·`int64` 순서면 16바이트다((9)절).

- Rust 와 다른 점 — Rust 는 같음을
  **[`Eq`](../../../rust/syntax/28-partialeq-eq-partialord-ord-and-hash-contracts/) 라는 트레이트로 타입에 요구**하고,
  `HashMap` 의 키에 `Eq + Hash` 를 **타입 경계로 적는다.**
  Go 는 그런 이름이 없고 **「비교 가능한 타입」이라는 언어 규칙**으로 둔다 — 적을 곳이 없다.
- Java 와 다른 점 — 자바는 `equals`/`hashCode` 를 **사람이 구현**한다
  ([`../../../java/syntax/27-equals-hashcode-contract/`](../../../java/syntax/27-equals-hashcode-contract/)).
  Go 의 `==` 는 **언어가 필드마다 재귀로 정의**한다 — 고칠 수 없고 어길 수도 없다.
- C 와 다른 점 — C 는 구조체에 `==` 가 아예 **없다.** Go 는 조건부로 **있다.**

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **어떤 구조체가 `==` 로 비교되는가** — 그 경계가 어디에 적혀 있고, 어기면 무엇이 나오나.
2. **리터럴 두 꼴 중 무엇을 쓸 것인가** — 위치 리터럴은 언제 어떻게 깨지나.
3. **필드 태그는 무엇을 바꾸는가** — 누가 읽고, 안 읽으면 어떻게 되나.

★ 구조체의 **복사 의미론**은 이 주제가 아니다 —
[16번 주제](../16-pointers-value-copy-semantics-new-and-make/)가 정본이고,
여기는 **「그 칸을 어떻게 만들고 어떻게 견주나」** 만 본다.
★ **패딩·정렬 일반론**도 이 주제가 아니다 —
[`../../../../data-representation/`](../../../../data-representation/)가 정본이고, 여기는 **Go 에서 그것을 재는 법**만 본다.

## 동작 방식

### (0) ★★ 이 주제가 쓰는 다섯 창 — 하나는 부적용이다

| 창 | 무엇을 보여 주나 | 한계 |
|---|---|---|
| 실행 출력 | 리터럴이 무엇을 채웠나 · 정렬 결과 | **왜 그런지는 안 보인다** |
| **컴파일 에러** | 이 언어가 **못 하게 막은 것** — `==`·맵 키·태그가 다른 대입 | 막은 이유까지는 안 말한다 |
| **런타임 패닉** | ★ **컴파일을 통과하고 터지는 자리** — `any` 필드·`any` 키 | 통과한 실행은 아무 말도 안 한다 |
| ★★★ **`reflect`** | **필드 태그**와 필드 메타데이터. **이 주제의 네 번째 창이다** | 태그의 **뜻**은 모른다 — 문자열을 그대로 돌려줄 뿐 |
| **`unsafe.Sizeof`·`Offsetof`** | 크기와 필드 오프셋 | **명세의 수가 아니다** — 플랫폼·컴파일러가 정한다 |
| ★ **부적용인 창 — `go vet`** | 위치 리터럴 사고를 **같은 패키지 안에서는 안 본다** | (2)절이 그 경계를 출력으로 못 박는다 |

★★★ **태그는 네 번째 창이 없으면 아예 안 보인다.** 실행 출력에도 없고 컴파일 에러에도 안 나온다 —
`fmt` 는 태그를 모르고((6)절 마지막 줄), 오타를 내도 **아무도 말해 주지 않는다.**

### (1) 리터럴 두 꼴 — 일곱 줄

**언제 쓰나** — 구조체 값을 만들 때. 여기서 고르는 한 가지가 (2)절의 사고를 정한다.

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

그림 해설 (한 단계씩):

- **필드명 리터럴**은 순서를 바꿔도 되고(`Point{Y: 2, X: 1}`), **빠뜨려도 된다** — 빠진 필드는 제로값이다.
  ①의 `c={1 0}` 이 그것이다. 명세:

  > For struct literals with keys the following rules apply: **Every element must have a key.** …
  > **The element list does not need to have an element for each struct field.
  > Omitted fields get the zero value for that field.**

- **위치 리터럴**은 반대다. 명세:

  > **For struct literals without keys, the element list must contain an element for each struct field
  > in the order in which the fields are declared.**

- ③ 중첩 구조체의 **안쪽 타입 이름은 생략할 수 있다** — `Line{Point{1,2}, Point{3,4}, "ㄱ"}`.
  ④ 배열·슬라이스·맵의 원소에서는 **아예 `{1, 2}` 로만** 적는다.
- ⑤ **`var z Point` 와 `Point{}` 는 같은 것**이다. 구조체에는 「초기화 안 됨」 상태가 없다.
- ⑥ **익명 구조체**는 타입 이름 없이 그 자리에서 만든다. `%T` 가 `struct { Name string; N int }` 로 찍힌다.
- ⑦ **`&Point{…}` 는 복합 리터럴에만 허용된 예외**다 — 리터럴은 변수가 아닌데도 주소를 얻을 수 있다.
  ([16번 주제](../16-pointers-value-copy-semantics-new-and-make/) (4)절이 `new(P)` 와의 비교의 정본이다.)

비용 — 리터럴은 값을 그 자리에 만든다. `&T{}` 는 할당 하나일 수 있다 — **이 문서는 재지 않았다.**

### (2) ★★ 위치 리터럴이 깨지는 두 모양 — 하나는 시끄럽고 하나는 조용하다

**언제 쓰나** — 「필드명을 꼭 적어야 하나」를 판단할 때.

**첫째 모양 — 필드를 더하면 컴파일이 깨진다.**

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

- `Point{1, 2}` 가 **`too few values in struct literal of type Point`** 로 막힌다.
  명세의 「전부 적어야 한다」가 그대로 에러가 된 것이다.
- ★ 이건 **좋은 쪽**이다 — 깨지는 자리를 컴파일러가 전부 짚어 준다.

**둘째 모양 — 필드 순서만 바꾸면 아무 말이 없다.**

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

- ★★★ **개수도 타입도 그대로이고 순서만 바뀌었다.** `User{1001, 30}` 이
  **`ID=30 Age=1001`** 이 됐다. 1001살이 되었는데 **컴파일러가 한 마디도 안 한다.**
- 필드명 리터럴 쪽은 **두 정의에서 똑같다.** 이것이 필드명을 적는 이유 전부다.

**`go vet` 은 이 자리를 보나** — 물어보자.

```text
===== 명령: go vet ./... =====
(exit 0)
```

- **한 줄도 없고 `exit 0`** 이다. `go vet` 은 이 사고를 **안 본다.**
- ★★ 다만 **경계가 있다** — `vet` 의 `composites` 검사는 **다른 패키지의 타입**에만 작동한다. 던져 보면 갈린다.

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

- 같은 패키지의 `Local{1, 2}` 는 통과하고, **`net.TCPAddr{…}` 만** `struct literal uses unkeyed fields` 로 잡혔다.
- ★ 그래서 정확히 이렇게 적어야 한다 — 「`go vet` 이 위치 리터럴을 본다」가 아니라
  **「`go vet` 은 남의 패키지 타입의 위치 리터럴만 본다」** 다. **내 패키지 안은 무방비다.**

비용 — 없다. 전부 컴파일·검사 시점이다.

### (3) ★★★ 비교 가능성 — 컴파일 에러로 갈라진다

**언제 쓰나** — `==` 를 쓰려다 막혔을 때. **이 주제의 본체다.**

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

그림 해설 (한 단계씩):

- ★★★ **①만 에러가 없다.** `HasArr{}` 는 `[2]int` 필드뿐이라 비교된다.
  나머지 여섯이 전부 막혔다 — **이 에러 목록이 곧 규칙이다.**
- 명세가 그 규칙을 직접 적는다.

  > **Struct types are comparable if all their field types are comparable.**
  > Two struct values are equal if their corresponding non-blank field values are equal.
  > The fields are compared in source order, and comparison stops as soon as two field values differ.

  > **Array types are comparable if their array element types are comparable.**

  > **Slice, map, and function types are not comparable.** However, as a special case, a slice, map,
  > or function value may be compared to the predeclared identifier `nil`.

- ★★ **배열은 되고 슬라이스는 안 된다** — 이 둘의 갈림이 여기서도 나온다.
  `[2]int` 는 **길이가 타입의 일부**라 원소끼리 견줄 수 있고, `[]int` 는 그렇지 않다.
  정본은 [05번 주제](../05-arrays-vs-slices-value-and-header/)다.
- ★★ **⑤가 이 절의 핵심이다** — `Outer` 에는 슬라이스가 **직접** 없는데도 막혔다.
  `struct containing HasSlice cannot be compared` — **비교 불가는 안쪽에서 바깥으로 번진다.**
- ⑥ 슬라이스끼리의 `==` 는 아예 다른 문구다 — **`slice can only be compared to nil`**.
  「비교가 없다」가 아니라 **「`nil` 하고만 된다」** 는 뜻이다.
- ⑦ 비교 불가 원소의 **배열**도 막힌다 — `[2][]int cannot be compared`.

```text
   비교 가능성은 필드를 따라 번진다

   Outer{ In HasSlice }
      └── HasSlice{ S []int }
              └── []int        <- 여기 하나가 「비교 불가」
      ↑ 그 한 칸 때문에 바깥 두 타입이 전부 == 를 잃는다
```

비용 — 없다. 전부 컴파일 시점이다.

### (4) ★★ 컴파일은 통과하고 런타임에 터지는 자리

**언제 쓰나** — 구조체에 `any` 필드를 둘 때. **제4의 상태다.**

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

그림 해설 (한 단계씩):

- **배열 필드**는 원소끼리 견준다 — `true`.
- **포인터 필드**는 **「같은 칸인가」** 를 본다 — 값이 둘 다 1인데 **다른 칸이면 `false`**, 같은 칸이면 `true`.
  명세: "Two pointer values are equal **if they point to the same variable** or if both have value nil."
- ★ **`any` 필드가 든 구조체는 컴파일을 통과한다.** 명세가 인터페이스를 **비교 가능**으로 치기 때문이다.
  담긴 것이 `int` 면 `true`, **타입이 다르면(`int` 대 `int64`) `false`** 다 —
  "Two interface values are equal if they have **identical dynamic types** and equal dynamic values."
- ★★★ **그런데 담긴 동적 타입이 비교 불가면 그 자리에서 패닉한다** —
  `panic: runtime error: comparing uncomparable type []int`, **종료 코드 2**. 명세가 이것도 적는다.

  > **A comparison of two interface values with identical dynamic types causes a run-time panic
  > if that type is not comparable.** This behavior applies not only to direct interface value
  > comparisons but also when comparing arrays of interface values or **structs with interface-valued fields**.

- ★★ 그래서 이 주제의 판정은 **두 층**이다 — 「`==` 를 적을 수 있나」는 컴파일 시점,
  「그 `==` 가 터지나」는 **실행 시점**이다. `any` 필드 하나가 그 둘을 갈라 놓는다.
- ★ 마커 줄은 **표준 오류로** 찍었다(`fmt.Fprintln(os.Stderr, …)`). 파이프로 받아도 자리가 안 바뀐다.

비용 — 패닉이면 프로그램이 죽는다.

### (5) ★ 맵 키가 될 수 있나 — 같은 규칙을 한 번 더

**언제 쓰나** — 구조체를 맵 키로 쓰려 할 때.

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

- ① **비교 가능한 구조체는 그대로 맵 키**가 된다. `map[Key]int` 에 `Key{"a", 1}` 로 넣고 읽는다.
- ③ **배열도 키가 된다** — `map[[2]int]string`. 슬라이스는 안 된다((6)의 컴파일 에러).
- ★★ ④ **`map[any]int` 는 컴파일을 통과한다.** 그리고 슬라이스를 키로 넣는 순간
  **`panic: runtime error: hash of unhashable type []int`** 다. 명세:

  > The comparison operators `==` and `!=` **must be fully defined for operands of the key type**;
  > thus the key type must not be a function, map, or slice.
  > **If the key type is an interface type, these comparison operators must be defined for the dynamic
  > key values; failure will cause a run-time panic.**

- ★ (4)절의 패닉과 **문구가 다르다** — 저쪽은 `comparing uncomparable type`, 이쪽은 `hash of unhashable type`.
  **어느 쪽에서 걸렸는지가 문구로 갈린다.**

컴파일 시점에 막히는 쪽은 이렇다.

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

- 셋 다 **한 문장**이다 — `invalid map key type <타입>`. 구조체든 슬라이스든 함수든 같은 말을 한다.
- ★ (3)절의 에러가 「왜 안 되는지」를 말해 주던 것과 달리, 이쪽은 **이유를 안 말한다.**
  이유는 (3)절에서 가져와야 한다 — **`BadKey` 안에 `[]string` 이 있기 때문**이다.

비용 — 맵 키 해싱은 키 크기에 비례한다 — **이 문서는 재지 않았다.**

### (6) ★★★ 필드 태그 — `reflect` 로만 보인다

**언제 쓰나** — `json:"…"` 를 처음 적을 때. **이 주제의 네 번째 창이다.**

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

그림 해설 (한 단계씩):

- **태그는 필드 선언 뒤의 문자열 리터럴**이다. 명세:

  > A field declaration may be followed by an optional **string literal tag**, which becomes an attribute
  > for all the fields in the corresponding field declaration. **An empty tag string is equivalent to
  > an absent tag.** **The tags are made visible through a reflection interface** and **take part in
  > type identity for structs** but are otherwise ignored.

- ★★ 「otherwise ignored」가 요점이다 — **프로그램의 동작을 태그가 바꾸지 않는다.**
  바꾸는 것은 **태그를 읽는 쪽**이다.
- 관례는 `` `키:"값" 키:"값"` `` 꼴이고 **`reflect.StructTag` 가 그 관례를 파싱**해 준다.
  ★ 관례일 뿐이라 **아무 문자열이나 넣어도 컴파일된다** — 명세의 예제부터
  `` "ceci n'est pas un champ de structure" `` 를 싣는다.
- ★★ **`Get` 과 `Lookup` 이 갈린다** — `Get("없는키")` 는 **빈 문자열**을 주고,
  `Lookup("없는키")` 라야 **`"", false`** 로 「없다」가 보인다.
  「빈 값으로 적힌 태그」와 「없는 태그」를 가르려면 `Lookup` 이라야 한다.
- 마지막 두 줄이 이 절의 결론이다 — **`json.Marshal` 은 `{"id":7,"Note":"ㄴ"}`** 을 내고
  **`fmt` 는 `{7  a@b ㄴ}`** 을 낸다. 같은 값인데 **읽는 쪽이 다르면 결과가 다르다.**
  `Name` 은 `omitempty` 라서, `Email` 은 `json:"-"` 라서 빠졌고, 태그 없는 `Note` 는 **필드 이름 그대로** 나왔다.

```text
   태그는 누구에게 보이나

   ID int `json:"id" db:"user_id"`
            │
            ├─> 컴파일러      : 문자열 하나로만 본다. 내용을 검사 안 한다
            ├─> fmt           : 아예 모른다        {7  a@b ㄴ}
            ├─> reflect       : ★ 원문을 그대로    "json:\"id\" db:\"user_id\""
            │      └ StructTag.Get / Lookup 이 관례대로 쪼개 준다
            └─> encoding/json : 쪼갠 것을 읽어 키 이름을 정한다  {"id":7,…}
                   ↑ 여기서만 「뜻」이 생긴다
```

★★★ **그래서 태그 오타는 조용하다.** `json:"nmae"` 라고 적어도 컴파일러도 `vet` 도 말이 없고,
JSON 키 이름만 조용히 달라진다. **이 주제에서 가장 조용한 자리다.**

비용 — 태그 읽기는 `reflect` 다. **이 문서는 그 비용을 재지 않았다.**

### (7) ★ 태그는 타입의 일부다 — 그런데 변환에서는 무시된다

**언제 쓰나** — 「태그만 다른 두 구조체」를 오갈 때.

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

- **태그가 다른 명명 타입끼리 변환은 된다** — `B(a)`·`C(a)` 가 둘 다 컴파일된다. 명세:

  > **Struct tags are ignored when comparing struct types for identity for the purpose of conversion.**

  ★ **이 규칙은 1.8부터**다. 그 전에는 `(*Person)(data)` 같은 변환이 안 됐다.
- 그래도 **타입은 다르다** — `reflect.TypeOf(a) == reflect.TypeOf(b)` 가 **`false`** 다.
  그리고 변환된 값의 태그는 **받는 타입의 것**(`json:"b"`)이다.

**대입은 다르다** — 익명 구조체로 던져 보면 갈린다.

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

- **`cannot use p … as struct{X int "json:\"b\""} value in assignment`** —
  에러 메시지가 **타입 이름 안에 태그를 그대로 박아** 보여 준다.
- 명세의 타입 동일성 규칙이 그 이유다.

  > Two struct types are identical if they have the same sequence of fields, and if corresponding pairs
  > of fields have the same names, **identical types, and identical tags**, and are either both embedded
  > or both not embedded.

- ★★ 그래서 한 문장으로 **「변환은 태그를 무시하고 동일성은 무시하지 않는다」** 가 된다.
  명명 타입에서는 어차피 변환을 적으므로 잘 안 걸리고, **익명 구조체에서 걸린다.**

비용 — 없다. 전부 컴파일 시점이다.

### (8) ★ 정렬 — `sort.Slice` 와 `slices.SortFunc`

**언제 쓰나** — 구조체 슬라이스를 정렬할 때. 두 API 중 무엇을 고를지.

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

그림 해설 (한 단계씩):

- **함수의 모양이 다르다.** `sort.Slice` 는 **인덱스 둘**을 받는 `less(i, j int) bool` 이고,
  `slices.SortFunc` 는 **원소 둘**을 받는 `cmp(a, b E) int` 다(음수/0/양수).
  ★ `slices`·`cmp` 는 **1.21부터**다.
- ★★★ **불안정한 쪽 둘이 같은 순서를 냈다** — `sort.Slice` 와 `slices.SortFunc` 가 둘 다
  `frolipmsbjgdkncaqeht` 다. **그래도 이것은 보장이 아니라 이 판의 관찰**이다.
  `sort` 패키지 문서가 "**is not guaranteed to be stable**" 이라고 적는다.
- **안정한 쪽 둘**(`SliceStable`·`SortStableFunc`)은 `filorbdgjmpsacehknqt` 로 **입력 순서를 지켰다.**
  `f i l o r`(10살) → `b d g j m p s`(20살) → `a c e h k n q t`(30살) — 각 무리 안이 **입력 순서 그대로**다.
- ★★ **동률을 결정적으로 만드는 진짜 길은 「키를 더하는 것」이다** —
  `cmp.Or(cmp.Compare(x.Age,y.Age), cmp.Compare(x.Name,y.Name))`(`cmp.Or` 는 **1.22부터**).
  그러면 **불안정 정렬을 써도 답이 하나**가 된다.
  ★ 「안정 정렬을 쓴다」는 **입력 순서에 기대는 것**이고, 「키를 더한다」는 **기대지 않는 것**이다.
- `slices.IsSortedFunc` 로 결과를 되물어 볼 수 있다 — `true`.

```text
   동률이 있을 때 무엇에 기대나

   불안정 + 키 하나   ->  순서가 보장 없음        (판이 바뀌면 달라질 수 있다)
   안정   + 키 하나   ->  입력 순서에 기댄다      (입력이 바뀌면 달라진다)
   불안정 + 키 둘     ->  ★ 아무것에도 안 기댄다  (답이 하나다)
```

비용 — **이 문서는 두 API 의 속도를 재지 않았다.** 「제네릭이라 빠르다」 같은 말은 여기 적지 않는다.

### (9) ★ 빈 구조체와 필드 순서

**언제 쓰나** — 집합을 만들 때, 그리고 구조체 크기가 궁금할 때.

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

그림 해설 (한 단계씩):

- ★★ **`struct{}` 의 크기가 0**이다. `[1000]struct{}` 도 **0**이다.
- 그래서 **집합**의 값 타입으로 쓴다 — `map[string]struct{}`. `map[string]bool` 보다 값 칸이 없다.
  ★ 맵을 찍을 때 **키를 모아 정렬해서** 찍었다 — 순회 순서는 보장이 없다
  ([09번 주제](../09-maps-declaration-comma-ok-delete-and-iteration-order/)가 정본).
- **신호용 채널** `chan struct{}` 도 같은 쓰임이다 — 「값」이 아니라 「일어났다」만 보낸다.
- ★★ **필드 순서가 크기를 바꾼다** — 같은 필드 셋인데
  `Loose{bool,int64,bool}` 이 **24바이트**(오프셋 0,8,16)이고
  `Tight{bool,bool,int64}` 가 **16바이트**(오프셋 0,1,8)다.
- ★★★ **그 수는 명세에 없다.** 명세는 「패딩」이라는 낱말을 예제 주석(`_ float32 // padding`)에서만 쓴다.
  **`unsafe.Sizeof` 가 내놓는 것은 이 컴파일러·이 플랫폼의 값**이다.
  원리 자체는 [`../../../../data-representation/`](../../../../data-representation/)가 정본이다.

비용 — 필드를 몰아 두면 구조체가 작아질 수 있다. **그것이 빨라진다는 주장은 이 문서가 재지 않았다.**

## 문법 — 형태와 규칙

### 형태

```go
// t17form.go
package main

import (
	"fmt"
	"slices"
)

// ① 구조체 타입 선언 — 필드마다 이름과 타입, 뒤에 태그(선택)
type Row struct {
	ID   int      `json:"id"`   // ② 태그는 문자열 리터럴이다
	Name string   `json:"name"` //
	Tags []string // ③ 슬라이스 필드가 있으면 이 타입은 == 가 안 된다
}

// ④ 한 줄에 같은 타입을 묶어 적을 수 있다
type Point struct{ X, Y int }

func main() {
	a := Row{ID: 1, Name: "ㄱ"} // ⑤ 필드명 리터럴 — 권장
	b := Point{1, 2}           // ⑥ 위치 리터럴 — 전부 적어야 한다
	c := &Point{X: 3}          // ⑦ 복합 리터럴에는 & 를 붙일 수 있다
	var z Point                // ⑧ 제로값 — Point{} 와 같다

	fmt.Println(a.Name, b, c.X, z, b == z)

	// ⑨ 익명 구조체
	d := struct{ N int }{N: 7}
	fmt.Println(d.N)

	// ⑩ 정렬 — 원소를 받는 비교 함수
	ps := []Point{{2, 0}, {1, 0}}
	slices.SortFunc(ps, func(x, y Point) int { return x.X - y.X })
	fmt.Println(ps)
}
```

```text
===== 소스: t17form.go =====
package main

import (
	"fmt"
	"slices"
)

// ① 구조체 타입 선언 — 필드마다 이름과 타입, 뒤에 태그(선택)
type Row struct {
	ID   int      `json:"id"`   // ② 태그는 문자열 리터럴이다
	Name string   `json:"name"` //
	Tags []string // ③ 슬라이스 필드가 있으면 이 타입은 == 가 안 된다
}

// ④ 한 줄에 같은 타입을 묶어 적을 수 있다
type Point struct{ X, Y int }

func main() {
	a := Row{ID: 1, Name: "ㄱ"} // ⑤ 필드명 리터럴 — 권장
	b := Point{1, 2}           // ⑥ 위치 리터럴 — 전부 적어야 한다
	c := &Point{X: 3}          // ⑦ 복합 리터럴에는 & 를 붙일 수 있다
	var z Point                // ⑧ 제로값 — Point{} 와 같다

	fmt.Println(a.Name, b, c.X, z, b == z)

	// ⑨ 익명 구조체
	d := struct{ N int }{N: 7}
	fmt.Println(d.N)

	// ⑩ 정렬 — 원소를 받는 비교 함수
	ps := []Point{{2, 0}, {1, 0}}
	slices.SortFunc(ps, func(x, y Point) int { return x.X - y.X })
	fmt.Println(ps)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
ㄱ {1 2} 3 {0 0} false
7
[{1 0} {2 0}]
(exit 0)
```

규칙 불릿.

- **필드는 「이름 + 타입 + (선택)태그」** 다. 같은 타입이면 `X, Y int` 로 묶어 적는다.
- **리터럴은 두 꼴**이다 — 필드명 꼴은 빠뜨려도 되고, 위치 꼴은 **전부 순서대로** 적어야 한다.
- **`T{}` 와 `var t T` 는 같다.** 구조체에 「초기화 안 됨」이 없다.
- **`&T{…}`** 로 포인터를 바로 얻는다. 복합 리터럴에만 허용된 예외다.
- **`==` 는 모든 필드가 비교 가능할 때만** 된다. 슬라이스·맵·함수 필드가 하나라도 있으면 막힌다.
- **비교 가능한 구조체만 맵 키**가 된다. 같은 규칙의 다른 얼굴이다.
- **태그는 프로그램이 안 읽는다.** `reflect` 로 읽는 쪽만 읽는다. 그리고 **타입 동일성에는 들어간다.**
- **정렬은 `slices.SortFunc`**(1.21) 또는 `sort.Slice`. **안정 정렬이 필요하면 `…Stable…`** 을 쓴다.
- **`struct{}` 는 0바이트**다. 집합·신호에 쓴다.

### 금지 사례 — 컴파일러가 거부하는 것

(3)·(5)·(7)절의 블록이 정본이다. 한 표로 묶으면 이렇다.

| 쓴 것 | 메시지 | 왜 막나 |
|---|---|---|
| `Point{1, 2}` (필드 3개) | `too few values in struct literal of type Point` | 위치 리터럴은 전부 적어야 한다 |
| `HasSlice{} == HasSlice{}` | `invalid operation: … (struct containing []int cannot be compared)` | 슬라이스 필드가 있다 |
| `Outer{} == Outer{}` | `invalid operation: … (struct containing HasSlice cannot be compared)` | 비교 불가가 안쪽에서 번진다 |
| `s1 == s2` (슬라이스) | `invalid operation: … (slice can only be compared to nil)` | 슬라이스는 `nil` 하고만 |
| `a1 == a2` (`[2][]int`) | `invalid operation: … ([2][]int cannot be compared)` | 원소가 비교 불가다 |
| `map[BadKey]int{}` | `invalid map key type BadKey` | 키가 비교 가능해야 한다 |
| 태그가 다른 익명 구조체 대입 | `cannot use p (variable of type struct{X int "json:\"a\""}) as struct{X int "json:\"b\""} value in assignment` | 태그가 타입 동일성에 든다 |

★ **거부하지 않는 것**도 함께 봐야 한다 — **필드 순서만 바꾼 위치 리터럴**은 에러도 경고도 없고((2)절),
**`any` 필드의 `==`** 도 컴파일을 통과한 뒤 실행에서 터진다((4)절).

## 어디서 틀리나

### 1. ★★★ 「필드를 늘려도 리터럴은 컴파일러가 잡아 주겠지」

- (2)절 실측 — **필드를 더하면** 잡아 준다(`too few values …`).
  **순서만 바꾸면 안 잡아 준다** — `ID=30 Age=1001` 이 되고 아무 말이 없다.
- `go vet` 도 같은 패키지에서는 침묵한다(출력 0줄·`exit 0`). **남의 패키지 타입만** 본다.
- 고치는 법 — **필드명 리터럴을 기본값으로 쓴다.** 위치 리터럴은 `Point{1, 2}` 처럼
  **필드가 절대 안 늘 작은 타입**에만 남긴다.

### 2. ★★★ 「구조체니까 `==` 로 비교되겠지」

- (3)절 실측 — 슬라이스·맵·함수 필드가 하나라도 있으면 **컴파일 에러**다.
  **안쪽 타입 때문에도** 막힌다(`struct containing HasSlice`).
- 고치는 법 — 비교가 필요하면 **그 필드를 빼거나** 비교 함수를 손으로 쓴다.
  ★ `reflect.DeepEqual` 은 되지만 **`==` 와 뜻이 다르다**(「더 들어가면」).

### 3. ★★ 「`any` 필드를 넣어도 `==` 가 컴파일됐으니 안전하다」

- (4)절 실측 — 컴파일은 통과하고, 담긴 것이 `[]int` 인 순간
  **`panic: runtime error: comparing uncomparable type []int`** 다.
- 맵 쪽은 문구가 또 다르다 — **`hash of unhashable type []int`**((5)절).
- 고치는 법 — `any` 를 비교·키에 쓰는 자리는 **담기는 타입을 좁힌다.** 통과한 실행은 근거가 아니다.

### 4. ★★ 「태그를 적었으니 동작이 바뀐다」

- (6)절 실측 — `fmt` 는 태그를 **모른다**(`{7  a@b ㄴ}`). `json.Marshal` 만 읽는다.
- 태그 **오타는 아무도 안 잡는다** — 컴파일러도 `vet` 도 말이 없다.
- 고치는 법 — 태그는 **읽는 쪽과 짝**으로 생각한다. 그리고 `Lookup` 으로 실제 파싱을 확인한다.

### 5. ★ 「`Get` 이 빈 문자열이면 태그가 없는 것이다」

- (6)절 실측 — `Get` 은 **없는 키에도 빈 문자열**을 준다. `Lookup` 이라야 `false` 가 나온다.
- 고치는 법 — 「있음/없음」을 가르는 자리에서는 **반드시 `Lookup`** 을 쓴다.

### 6. ★★ 「정렬이 같은 값의 순서도 지켜 주겠지」

- (8)절 실측 — `sort.Slice` 와 `slices.SortFunc` 는 **입력 순서를 안 지켰다**(`frolipms…`).
  같은 판에서 세 번 돌려 같았지만 **그것은 보장이 아니다.**
- 고치는 법 — 안정이 필요하면 `…Stable…` 을, **더 나은 길은 `cmp.Or` 로 키를 더하는 것**이다.

### 7. ★ 「필드 순서는 취향이다」

- (9)절 실측 — 같은 필드 셋이 **24바이트와 16바이트**로 갈렸다.
- 고치는 법 — **큰 필드부터 몰아 두면** 패딩이 준다. 단 **그 수는 플랫폼의 것**이고,
  「그래서 빨라진다」는 **측정이 필요한 주장**이다.

### 8. ★ 「빈 구조체는 아무 쓸모가 없다」

- (9)절 실측 — `struct{}` 는 **0바이트**이고, 그래서 집합과 신호 채널의 표준 재료다.

### 9. ★ 「태그만 다르면 그냥 대입되겠지」

- (7)절 실측 — **변환은 되고 대입은 막힌다.** 에러가 타입 이름 안에 태그를 박아 보여 준다.
- 고치는 법 — 명명 타입 사이에서는 **변환을 적는다**(`B(a)`).

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| **위치 리터럴은 필드를 전부 적어야 한다** | **명세 보장** | "the element list must contain an element for each struct field in the order in which the fields are declared" |
| **필드명 리터럴은 빠뜨려도 된다** | **명세 보장** | "Omitted fields get the zero value for that field" |
| **모든 필드가 비교 가능해야 구조체가 비교 가능** | **명세 보장** | "Struct types are comparable if all their field types are comparable" |
| **배열은 되고 슬라이스·맵·함수는 안 된다** | **명세 보장** | "Slice, map, and function types are not comparable" |
| **인터페이스 필드의 비교가 런타임 패닉이 될 수 있다** | **명세 보장** | "causes a run-time panic if that type is not comparable … structs with interface-valued fields" |
| **맵 키는 비교 가능해야 한다** | **명세 보장** | "the key type must not be a function, map, or slice" |
| **인터페이스 키의 실패가 런타임 패닉인 것** | **명세 보장** | "failure will cause a run-time panic" |
| **태그가 reflect 로만 보이고 그 밖에는 무시되는 것** | **명세 보장** | "made visible through a reflection interface … but are otherwise ignored" |
| **태그가 타입 동일성에 드는 것** | **명세 보장** | "identical types, and identical tags" |
| **변환에서는 태그가 무시되는 것**(1.8부터) | **명세 보장** | "Struct tags are ignored when comparing struct types for identity for the purpose of conversion" |
| **`struct{}` 가 0바이트인 것** | **구현·플랫폼** | 명세에 크기 규정이 없다. `unsafe.Sizeof` 의 관찰이다 |
| **`Loose` 24 · `Tight` 16** | **구현·플랫폼** | 〃. 다른 아키텍처에서 달라질 수 있다 |
| 패닉 **메시지 본문** 둘 | **런타임(구현)** | 명세는 「패닉한다」까지만 정한다 |
| **불안정 정렬이 내놓은 순서** | **구현·이 판의 관찰** | `sort` 문서가 "not guaranteed to be stable" 이라고 적는다 |
| **안정 정렬이 입력 순서를 지키는 것** | **패키지 문서의 보장** | 명세가 아니라 `sort`·`slices` 의 계약이다 |
| `go vet` 이 **남의 패키지 것만** 보는 것 | **도구(구현)** | `composites` 검사의 성질이다. 판이 바뀌면 달라질 수 있다 |
| 컴파일 에러의 **문구 자체** | **툴체인 판(go1.27.1)** | 규칙은 명세, 문장은 gc 의 것 |
| 구조체 대입·맵 해싱의 **실제 비용** | **안 쟀다** | 벤치마크가 없다(목록의 **50번 주제**) |

★ 이 주제의 결론은 「**비교되는지는 전부 명세가 정하고, 몇 바이트인지만 구현이 정한다**」이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 구조체 값을 만든다 | **필드명 리터럴** | 필드가 늘거나 순서가 바뀌어도 안 깨진다 |
| 필드 둘짜리 좌표·쌍 | 위치 리터럴도 좋다 | 필드가 늘 일이 없고 짧다 |
| 남의 패키지 타입을 만든다 | **반드시 필드명** | `go vet` 이 잡아 주기는 하나, 잡히기 전에 깨진다 |
| 값끼리 같은지 봐야 한다 | **비교 가능하게 설계** | 슬라이스 필드 하나가 `==` 를 통째로 앗아간다 |
| 슬라이스 필드가 꼭 필요하다 | 비교 함수를 **손으로** | `==` 는 포기한다. 또는 `slices.Equal` 을 필드별로 |
| 복합 키가 필요하다 | **비교 가능한 구조체 키** | 문자열을 이어 붙여 만든 키보다 안전하고 읽힌다 |
| 집합이 필요하다 | **`map[K]struct{}`** | 값 칸이 0바이트다 |
| 직렬화 이름을 정한다 | **필드 태그** | 필드 이름과 외부 이름을 갈라 둘 수 있다 |
| 태그의 유무를 가른다 | **`Lookup`** | `Get` 은 없는 키에도 빈 문자열을 준다 |
| 정렬한다 | **`slices.SortFunc`**(1.21) | 원소를 직접 받아 읽기 쉽다 |
| 동률의 순서가 중요하다 | **`cmp.Or` 로 키를 더한다** | 안정 정렬보다 기대는 것이 적다 |
| 구조체가 아주 많다 | 필드를 **큰 것부터** | 패딩이 준다. 단 속도 주장은 재고 나서 |

판단 규칙 두 줄.

- **「이 타입이 `==` 로 비교되나」를 필드 목록에서 먼저 읽어라.** 맵 키가 되는지도 같은 답이다.
- **필드명 리터럴을 기본값으로 삼아라.** 컴파일러가 안 잡아 주는 유일한 자리가 거기다.

## 핵심 문장

- ★★★ **구조체의 `==` 는 필드가 전부 비교 가능할 때만** 있다.
  슬라이스·맵·함수 필드 하나가 **안쪽에서 바깥으로 번져** 타입 전체의 `==` 를 앗아간다.
- ★★ **배열은 되고 슬라이스는 안 된다** — 길이가 타입의 일부이기 때문이다.
- ★★★ **`any` 필드는 컴파일을 통과하고 실행에서 터진다** —
  `comparing uncomparable type []int`(비교) · `hash of unhashable type []int`(맵 키).
  **문구가 어느 쪽에서 걸렸는지를 말해 준다.**
- **맵 키의 요건은 비교 가능성 하나**다. 같은 규칙의 다른 얼굴이다.
- ★★★ **위치 리터럴은 두 가지로 깨진다** — 필드를 **더하면 시끄럽게**(`too few values …`),
  순서만 **바꾸면 조용하게**(`ID=30 Age=1001`). 뒤엣것은 `go vet` 도 같은 패키지에서는 못 본다.
- ★★★ **필드 태그는 `reflect` 로만 보인다.** `fmt` 도 컴파일러도 태그를 모른다 —
  「otherwise ignored」가 명세의 낱말이다. 그래서 **오타가 조용하다.**
- ★★ **태그는 타입 동일성에 들고 변환에서는 무시된다**(1.8부터). 대입은 막히고 변환은 된다.
- ★ **`Get` 과 `Lookup` 이 갈린다** — 「없음」을 보려면 `Lookup` 이라야 한다.
- ★★ **정렬의 보장은 「정렬됨」까지**다. 동률의 순서는 `…Stable…` 이거나 **키를 더한 것**이라야 한다.
- ★ **`struct{}` 는 0바이트**이고, **필드 순서가 크기를 바꾼다**(24 대 16) — 그 수는 **구현·플랫폼**이다.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 17번)
- [16번 주제](../16-pointers-value-copy-semantics-new-and-make/)(포인터·값 복사) — **이 주제의 직접 선행.**
  **그쪽은 「구조체 대입이 얕은 복사」까지**, 여기는 **「그 칸을 어떻게 만들고 어떻게 견주나」** 부터
- [05번 주제](../05-arrays-vs-slices-value-and-header/)(배열과 슬라이스) —
  **「배열은 값, 슬라이스는 헤더」가 정본.** 여기는 **그 갈림이 `==` 에서 한 번 더 나오는 것**만
- [09번 주제](../09-maps-declaration-comma-ok-delete-and-iteration-order/)(맵) —
  **맵의 표면과 순회 순서가 정본.** 여기는 **「무엇이 키가 되나」 한 줄**만
- [02번 주제](../02-variable-declarations-and-zero-values/)(제로값) — `T{}` 와 `var t T` 가 같은 것의 정본
- [18번 주제](../18-embedding-and-field-method-promotion/)(임베딩) — **이 주제의 직접 후행.**
  **필드 이름을 안 적은 필드**가 무엇을 하는지
- 목록의 **38번 주제**(`slices`·`maps`·`cmp`) — 정렬 API 의 정본. 여기는 **구조체를 정렬하는 자리**만
- 목록의 **45번 주제**(`encoding/json`) — **태그를 읽는 쪽의 정본.**
  여기는 **태그가 무엇이고 `reflect` 로 어떻게 보이나**까지
- [목록의 **22번 주제**](../22-type-assertion-any-and-comparable/)(타입 단언·`comparable`) — 제네릭의 `comparable` 제약이 이 규칙과 만나는 자리
- [`../../../../data-representation/`](../../../../data-representation/) —
  **그쪽은 정렬(alignment)·패딩 일반까지**, 여기는 **Go 에서 그것을 `unsafe.Sizeof` 로 재는 법**부터
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **28번**
  ([`../../../rust/syntax/28-partialeq-eq-partialord-ord-and-hash-contracts/`](../../../rust/syntax/28-partialeq-eq-partialord-ord-and-hash-contracts/)) —
  **그쪽은 `Eq` 를 타입에 요구하고 사람이 계약을 지킨다**, 여기는 **언어 규칙이라 지킬 것도 어길 것도 없다**
- [`../../../java/syntax/27-equals-hashcode-contract/`](../../../java/syntax/27-equals-hashcode-contract/) —
  **그쪽은 `equals`/`hashCode` 를 사람이 구현**하고, 여기는 **언어가 필드마다 재귀로 정의**한다

## 용어 풀이

- **구조체(struct)** — 이름과 타입을 가진 필드의 나열. 명세의 낱말은 "a sequence of named elements".
- **복합 리터럴(composite literal)** — `T{…}` 꼴로 값을 만드는 식. 구조체·배열·슬라이스·맵에 쓴다.
- **필드명 리터럴 / 위치 리터럴** — `T{X: 1}` 와 `T{1}`. 뒤엣것은 **전부 순서대로** 적어야 한다.
- **비교 가능(comparable)** — `==`·`!=` 를 쓸 수 있는 것. 슬라이스·맵·함수는 아니다.
- **필드 태그(struct tag)** — 필드 뒤의 문자열 리터럴. `reflect` 로만 보이고 **타입 동일성에는 든다.**
- **`reflect.StructTag`** — 태그 문자열을 `키:"값"` 관례로 파싱해 주는 타입. `Get` 과 `Lookup` 이 있다.
- **익명 구조체(anonymous struct)** — 타입 이름 없이 그 자리에서 쓰는 `struct{…}{…}`.
- **안정 정렬(stable sort)** — 같은 키의 원소들이 **입력 순서를 지키는** 정렬.
- **패딩(padding)** — 정렬을 맞추려고 필드 사이에 넣는 빈 바이트. 크기를 늘린다.
- **빈 구조체(`struct{}`)** — 필드가 없는 구조체. 이 구현에서 **0바이트**이고 집합·신호에 쓴다.

---

## 더 들어가면

- **`reflect.DeepEqual` 은 `==` 가 아니다.** 슬라이스·맵도 견주지만
  **`nil` 슬라이스와 빈 슬라이스를 다르다고 답한다.** 「`==` 가 막히니 `DeepEqual` 을 쓰자」는
  **뜻이 바뀌는 교체**다. 이 문서는 그 차이를 **안 던졌다.**
- 명세는 **빈 식별자 필드**(`_ [4]byte`)를 예제로 싣는다 — 비교에서 제외되고("non-blank field values")
  패딩을 손으로 넣는 자리다. 이 문서는 **안 던졌다.**
- 태그가 **하나의 필드 선언 전체에 붙는다**는 점이 잘 안 보인다 —
  `` x, y float64 "tag" `` 면 `x` 와 `y` 가 **같은 태그**를 갖는다. 이 문서는 **안 던졌다.**
- `go vet` 의 `structtag` 검사는 **태그 문법이 관례에서 벗어난 것**을 잡는다.
  (6)절의 오타(`json:"nmae"`)는 **문법이 맞아서** 안 잡힌다 — 이 문서는 그 검사를 **안 던졌다.**
- 구조체의 **필드 순서를 자동으로 재배열하지 않는 것**도 Go 의 성질이다.
  명세는 순서를 비교·정체성의 기준으로 쓰므로 컴파일러가 마음대로 못 바꾼다.
- 제네릭의 **`comparable` 제약**(1.18)은 이 규칙을 타입 파라미터로 옮긴 것이다.
  1.20부터 **비교 가능한 인터페이스도 `comparable` 을 만족**하게 바뀌었다 — 정본은 목록의 **37번 주제**다.

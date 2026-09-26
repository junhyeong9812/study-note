# go/syntax/02 — 변수 선언 세 형태와 제로값 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Go 명세](https://go.dev/ref/spec) 의 Variable declarations · Short variable declarations ·
> The zero value · Comparison operators 절.\
> 웹이 아니라 **이 툴체인이 들고 있는 `$(go env GOROOT)/doc/go_spec.html` 을 열어** 인용했다.
> 그 파일의 머리는 「**Language version go1.27 (May 26, 2026)**」이다.
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 손으로 옮겨 적은 블록은 없다.
> **버전** — 이 절의 규칙은 1.0부터 같다. `any`(= `interface{}`)라는 이름만 **1.18**부터다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 명세로, 출력은 실행으로 접지했다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것. 어느 컴파일러에서도 같다 | `go_spec.html` 원문 인용 |
| **구현(gc)** | 이 컴파일러·런타임이 그렇게 하는 것. 약속은 아니다 | `unsafe.Sizeof`·컴파일 출력 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 실행 출력(재실행 대조까지) |

★ 이 주제는 **명세 보장 칸이 유난히 크다.** 제로값은 Go 에서 가장 짧고 가장 강한 약속이다.

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
===== 명령: go env GOOS GOARCH GOVERSION =====
linux
amd64
go1.27.1
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| 칸 | 흔들리나 | 확인한 방법 |
|---|---|---|
| 제로값 자체 · `%v` · `%#v` 출력 | **안 흔들림** | 명세가 정한다 + 재실행 대조 동일 |
| `== nil` 의 참·거짓 | 안 흔들림 | 〃 |
| 에러 문장 본문 · `파일:줄:칸` | 안 흔들림 | 재실행 대조 동일 |
| 종료 코드 (`0` / `1` / `2`) | 안 흔들림 | 재실행 대조 동일 |
| **`unsafe.Sizeof` 의 값** | **플랫폼·구현에 달렸다** | 여기 값은 전부 linux/amd64 의 것 |
| 패닉 스택의 `+0x…` · `pc=0x…` | **판·빌드가 바뀌면 바뀐다** | 같은 바이너리 3판 md5 동일 |
| 맵 순회 순서 | **매번 바뀐다 — 이 문서는 순회를 아예 안 쓴다** | [목록의 **09번 주제**](../09-maps-declaration-comma-ok-delete-and-iteration-order/) |

## 한눈에 — 쉽게 말하면

**Go 의 변수는 「빈 칸」이 아니라 「기본값이 미리 찍힌 서식」이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 미리 인쇄된 서식 한 장 | 새로 선언한 변수 |
| 숫자 칸에 찍힌 `0` | 수치 타입의 제로값 |
| 체크박스가 비어 있음 | `bool` 의 `false` |
| 이름 칸이 빈 줄 | `string` 의 `""` |
| 「첨부 서류: 없음」 | `nil` (포인터·슬라이스·맵·채널·함수·인터페이스) |
| **「없음」과 「빈 봉투」는 다르다** | `nil` 슬라이스 ≠ 빈 슬라이스 — `len` 은 같고 `== nil` 은 다르다 |
| 첨부가 「없음」인데 내용을 읽으면 0 | `nil` 맵 읽기 → 제로값 |
| 첨부가 「없음」인데 **써 넣으려 하면** 사고 | `nil` 맵 쓰기 → **패닉** |

- 다른 언어에서 흔한 「선언만 했으니 쓰레기 값」이 Go 에는 **없다.** 서식은 언제나 찍혀 나온다.
- 그래서 `var buf bytes.Buffer` 처럼 **초기화 없이 바로 쓸 수 있는** 타입이 생긴다.
- ★ 조심할 칸은 하나다 — **`nil` 은 「없음」이라는 값이지 「아무것도 아님」이 아니다.**
  읽을 수 있는 `nil` 이 있고, 읽으면 죽는 `nil` 이 있다.

```text
  var s []int            s := []int{}
  +-----------------+    +-----------------+
  | ptr  = nil      |    | ptr  = (빈 주소) |
  | len  = 0        |    | len  = 0        |
  | cap  = 0        |    | cap  = 0        |
  +-----------------+    +-----------------+
    len/cap/range/append 는 똑같이 동작한다
                    |
                    v
    갈리는 것은 딱 둘 — `s == nil` 과 JSON 출력
    s == nil : true      s == nil : false
    JSON     : null      JSON     : []
```

**언어도 똑같은 구조다.** 위 두 칸은 아래 (3)절 출력에서 실제로 그렇게 갈렸다.

> **제로값(zero value)** — 초기화식을 안 적었을 때 변수에 들어가는 값. 타입마다 정해져 있다.\
> 예: `var n int` 의 `n` 은 **반드시 0**이다. 쓰레기 값이 들어가는 일이 없다.

> **`nil`** — 포인터·슬라이스·맵·채널·함수·인터페이스의 제로값을 나타내는 미리 선언된 식별자.\
> 예: `var p *int` 이면 `p == nil` 이 참이다. 이것은 **타입이 없는 값**이라 `int` 와는 비교조차 안 된다.

> **섀도잉(shadowing)** — 안쪽 블록에서 같은 이름을 다시 선언해 바깥 이름을 가리는 것.\
> 예: `if v := f(); ...` 안의 `v` 는 바깥 `v` 와 **다른 변수**다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 선언 형태 셋(`var T` · `var = v` · `:=`)은 **무엇이 다르고 어디서만 쓸 수 있나.**
2. 초기화식을 안 적으면 **타입마다 정확히 무엇이 들어가나** — 그리고 그것을 **누가 보장하나.**
3. `nil` 로 보이는 값들 사이의 **차이는 어디서 드러나나** — 안 드러나는 자리는 어디인가.

## 동작 방식

### (1) 선언 세 형태 — 그리고 기본 타입

**언제 쓰나** — 변수를 만들 때마다.

```text
===== 소스: t02f.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
a: int      0
b: int      42
c: int64    42
d: int      42
e: float64  42
f: int32    65
g: string   hi
h: complex128 (42+0i)
host="localhost" port=8080   debug=false
(exit 0)
```

그림 해설 (한 단계씩):

- **① `var a int`** — 타입만 적으면 **제로값**이 들어간다. `0`.
- **② `var b = 42`** — 값만 적으면 **타입이 값에서 온다.** 타입 없는 상수 `42` 의 기본 타입은 `int` 다(03번 주제).
- **③ `var c int64 = 42`** — 둘 다 적으면 그 타입이 된다.
- **④ `d := 42`** — ②의 짧은 꼴. **함수 안에서만** 쓸 수 있다.
- `e := 42.0` 은 `float64`, `f := 'A'` 는 **`int32`**(`rune` 의 별칭), `g := "hi"` 는 `string`,
  `h := 42 + 0i` 는 `complex128` 이다.
- **`var ( … )` 블록**은 선언을 묶는 문법 설탕이다. 패키지 수준에서 많이 쓴다.
- 마지막 줄 — 블록 안의 `debug bool` 은 값을 안 적었으므로 **`false`** 다.

★ **패키지 수준 변수는 안 써도 에러가 아니다.** 위 소스의 `pkgLevelUnused` 가 그 증거다
(함수 안이었으면 컴파일 에러다 — 아래 금지 사례).

비용 — 없음. 전부 컴파일 타임에 자리가 정해진다.

### (2) ★ 제로값 전수 — `%v` · `%#v` · `== nil`

**언제 쓰나** — 「선언만 했는데 이게 뭐지」가 나올 때마다.

열네 가지 타입을 한 번에 찍는다.

```text
===== 소스: t02a.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
type           | %v             | %#v                              | == nil
---------------+----------------+----------------------------------+--------
int            | 0              | 0                                | 컴파일 에러
float64        | 0              | 0                                | 컴파일 에러
bool           | false          | false                            | 컴파일 에러
string         |                | ""                               | 컴파일 에러
rune(=int32)   | 0              | 0                                | 컴파일 에러
byte(=uint8)   | 0              | 0x0                              | 컴파일 에러
*int           | <nil>          | (*int)(nil)                      | true
[]int          | []             | []int(nil)                       | true
map[string]int | map[]          | map[string]int(nil)              | true
chan int       | <nil>          | (chan int)(nil)                  | true
func()         | <nil>          | (func())(nil)                    | true
interface{}    | <nil>          | <nil>                            | true
[3]int         | [0 0 0]        | [3]int{0, 0, 0}                  | 컴파일 에러
Point          | {0 0  []}      | main.Point{X:0, Y:0, Name:"", Tags:[]string(nil)} | 컴파일 에러
(exit 0)
```

그림 해설 (한 단계씩):

- **수치·`bool`·`string`** — `0` · `false` · `""`. `nil` 과 **비교조차 안 된다**(컴파일 에러).
- **`rune`·`byte`** — 별칭이라 `int32`·`uint8` 의 제로값 `0` 이다.
  `%#v` 에서 `byte` 만 `0x0` 으로 찍히는 것은 **`fmt` 의 표기 선택**이지 값의 차이가 아니다.
- **포인터·슬라이스·맵·채널·함수·인터페이스** — 전부 `nil`. `== nil` 이 **true**.
- ★ **`%v` 만 보면 셋이 헷갈린다** — 슬라이스는 `[]`, 맵은 `map[]`, 나머지는 `<nil>`.
  `%#v` 로 찍어야 `[]int(nil)` · `map[string]int(nil)` 처럼 **타입과 nil 여부가 같이** 보인다.
- **인터페이스만 `%#v` 도 `<nil>`** 이다 — 담긴 타입이 아예 없기 때문이다((7)절에서 다시 본다).
- **배열·구조체** — 재귀적으로 제로값이다. `Point` 의 `Tags []string` 이 `nil` 인 것까지 보인다.

명세가 이 표를 한 문단으로 약속한다.

> … and no explicit initialization is provided, the variable or value is
> given a default value. Each element of such a variable or value is
> set to the zero value for its type: `false` for booleans,
> `0` for numeric types, `""` for strings, and `nil` for pointers, functions,
> interfaces, slices, channels, and maps.
> This initialization is done **recursively**, so for instance each element of an
> array of structs will have its fields zeroed if no value is specified.

비용 — 없음. 런타임 초기화가 필요하면 그건 **메모리를 0으로 채우는 것**뿐이다.

### (3) ★ `nil` 슬라이스와 빈 슬라이스 — 갈리는 자리는 둘뿐이다

**언제 쓰나** — 슬라이스를 만들거나, API 로 내보낼 때.

네 가지 만드는 법을 나란히 찍는다.

```text
===== 소스: t02b.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
var a []int      len=0 cap=0  s==nil:true   %v:[]  %#v:[]int(nil)     Sizeof=24  데이터포인터=true  json=null
[]int{}          len=0 cap=0  s==nil:false  %v:[]  %#v:[]int{}        Sizeof=24  데이터포인터=false  json=[]
make([]int,0)    len=0 cap=0  s==nil:false  %v:[]  %#v:[]int{}        Sizeof=24  데이터포인터=false  json=[]
make([]int,0,4)  len=0 cap=4  s==nil:false  %v:[]  %#v:[]int{}        Sizeof=24  데이터포인터=false  json=[]

reflect.DeepEqual(a, b) = false
len(a) == len(b)        = true
append 은 둘 다 된다:  append(a,1) = [1] · append(b,1) = [1]
range 는 둘 다 0바퀴
(exit 0)
```

그림 해설 (한 단계씩):

- **`len`·`cap` 이 같다**(0·0). `range` 도 둘 다 0바퀴고, `append` 도 둘 다 된다.
- **갈리는 것 ①** — `s == nil`. `var a []int` 만 **true** 다.
- **갈리는 것 ②** — **JSON** 이다. `nil` 은 `null`, 빈 슬라이스는 `[]` 로 나간다.\
  ★ 이게 실무에서 가장 자주 무는 자리다 — 클라이언트가 `null` 에 `.length` 를 걸면 터진다.
- `reflect.DeepEqual(a, b)` 도 **false** 다. 「같은 값」으로 보지 않는다.
- `unsafe.Sizeof` 는 넷 다 **24**다 — 슬라이스 헤더는 (포인터, len, cap) 셋이고
  이 플랫폼에서 8×3 이다. 즉 **`nil` 이라고 해서 더 작지 않다.**
- 데이터 포인터가 `nil` 인 것은 **`var a []int` 하나뿐**이다. `[]int{}` 는 길이 0인데도 주소가 있다.

비용 — `[]int{}` 와 `make([]int, 0)` 은 **데이터 주소 하나를 만든다**(실측: 데이터포인터가 `false`).
`var a []int` 는 헤더만 0으로 둔다.

### (4) `nil` 맵 — 읽기는 되고, 쓰기는 죽는다

**언제 쓰나** — 구조체 안의 맵 필드처럼 **`make` 를 깜빡하기 쉬운** 자리.

```text
===== 소스: t02c.go =====
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
===== 명령: go build -trimpath -o prog . =====
(exit 0)
===== 명령: ./prog 2>&1 =====
m == nil : true · len(m) : 0
없는 키 읽기 m["x"] : 0
comma-ok : 0 false
delete(m, "x") 는 그냥 지나간다
----- 여기까지 stdout · 아래부터 쓰기 시도 -----
panic: assignment to entry in nil map

goroutine 1 [running]:
main.main()
	ex/t02c.go:17 +0x2a5
(exit 2)
```

그림 해설 (한 단계씩):

- `m == nil` 이 **true**, `len(m)` 은 **0**. 여기까지는 슬라이스와 같다.
- **없는 키 읽기**는 **제로값**을 준다 — 에러도 패닉도 없다. `comma-ok` 도 `0 false` 로 멀쩡히 답한다.
- **`delete`** 도 그냥 지나간다 — 명세: "If the map `m` is nil or the element `m[k]` does not exist, `delete` is a no-op."
- **쓰기만 패닉**한다 — `panic: assignment to entry in nil map`, 종료 코드 **2**.
- ★ 마커 줄(`----- 여기까지 stdout …`)은 **표준 오류로** 찍었다. 그래서 파이프로 받아도 자리가 안 바뀐다.

```text
  var m map[string]int   (nil 맵)

     m["x"]           -->  0         (읽기: 제로값)
     v, ok := m["x"]  -->  0, false  (comma-ok)
     delete(m, "x")   -->  아무 일 없음
     m["x"] = 1       -->  PANIC     <- 여기 하나만 다르다
```

비용 — 패닉은 프로그램을 끝낸다(종료 코드 2). 고칠 때 비용은 `make(map[string]int)` 한 줄이다.

### (5) `nil` 포인터 — 비교는 되고 역참조는 죽는다

**언제 쓰나** — 포인터를 돌려주는 함수의 결과를 받을 때.

```text
===== 소스: t02d.go =====
package main

import (
	"fmt"
	"os"
)

func main() {
	var p *int
	fmt.Println("p == nil :", p == nil)
	fmt.Fprintln(os.Stderr, "----- 여기까지 stdout · 아래부터 *p -----")
	fmt.Println(*p)
}
===== 명령: go build -trimpath -o prog . =====
(exit 0)
===== 명령: ./prog 2>&1 =====
p == nil : true
----- 여기까지 stdout · 아래부터 *p -----
panic: runtime error: invalid memory address or nil pointer dereference
[signal SIGSEGV: segmentation violation code=0x1 addr=0x0 pc=0x499e84]

goroutine 1 [running]:
main.main()
	ex/t02d.go:12 +0xa4
(exit 2)
===== 명령: for i in 1 2 3; do ./prog 2>&1 | md5sum; done =====
d71e2913794d2133e5c2e25fa8ff66c9  -
d71e2913794d2133e5c2e25fa8ff66c9  -
d71e2913794d2133e5c2e25fa8ff66c9  -
(exit 0)
```

그림 해설 (한 단계씩):

- `p == nil` 은 **true** — 비교는 안전하다.
- `*p` 는 **패닉**이다. 메시지가 두 줄인 것에 주의 —
  `panic: runtime error: invalid memory address or nil pointer dereference` 와
  `[signal SIGSEGV: … addr=0x0 pc=0x…]`.
- ★ **`pc=0x499e84` 는 같은 바이너리를 세 번 돌려도 같았다**(md5 동일).
  실행마다 흔들리는 칸이 아니라 **빌드 산출물에 달린 칸**이다 — 판이 바뀌면 바뀐다.
- `addr=0x0` 이 「`nil` 을 건드렸다」는 뜻이다.

비용 — 없음(검사는 하드웨어 예외로 들어온다). 고치는 비용은 `if p == nil` 한 줄이다.

### (6) 섀도잉 — `:=` 는 조용히 새 변수를 만든다

**언제 쓰나** — `if`·`for` 의 초기화절, 그리고 블록 안에서 같은 이름을 다시 쓸 때.

```text
===== 소스: t02i.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
1: 패키지 수준
2: main 의 v
3: 3 (int) — 블록 안에서는 타입까지 바뀐다
4: main 의 v
5: if 의 v
6: main 의 v
(exit 0)
```

그림 해설 (한 단계씩):

- **2번** — `main` 의 `v :=` 가 **패키지 변수 `v` 를 가린다.** 패키지 변수는 그대로 살아 있다.
- **3번** — 블록 안의 `v := 3` 은 **타입까지 바뀐다**(`string` → `int`). 새 변수이기 때문이다.
- **4번** — 블록을 나오면 바깥 `v` 가 그대로다. 안쪽 대입이 바깥에 **안 남는다.**
- **5\~6번** — `if v := …; …` 의 `v` 는 **`if` 문 전체의 스코프**에만 있다.
- 이 셋이 전부 **「대입」이 아니라 「새 선언」이라는 한 가지 사실**에서 나온다.

비용 — 없음. 대신 **버그가 조용하다** — 가려진 변수에 쓴 값은 아무 데도 안 간다.

### (7) ★ 네 번째 창 — 값에게 **세 가지를 묻는다**

실행 출력·컴파일 진단·`go vet` 셋으로는 「`<nil>` 로 보이는 것들이 **어떻게 다른가**」가 안 보인다.
그래서 이 주제는 창을 하나 더 쓴다 — **한 값에게 `%#v`·`unsafe.Sizeof`·`reflect` 셋을 동시에 묻는 것**이다.

```text
===== 소스: t02j.go =====
package main

import (
	"fmt"
	"reflect"
	"unsafe"
)

type Point struct {
	X, Y int
	Name string
	Tags []string
}

func ask(label string, v any, size uintptr) {
	rv := reflect.ValueOf(v)
	kind := "Invalid"
	isNil := "물을 수 없음"
	if rv.IsValid() {
		kind = rv.Kind().String()
		switch rv.Kind() {
		case reflect.Ptr, reflect.Slice, reflect.Map, reflect.Chan,
			reflect.Func, reflect.Interface:
			isNil = fmt.Sprint(rv.IsNil())
		}
	}
	fmt.Printf("%-16s Sizeof=%-3d Kind=%-9s IsNil=%s\n", label, size, kind, isNil)
}

func main() {
	var i int
	var s string
	var p *int
	var sl []int
	var m map[string]int
	var ch chan int
	var fn func()
	var ifc interface{}
	var st Point

	ask("int", i, unsafe.Sizeof(i))
	ask("string", s, unsafe.Sizeof(s))
	ask("*int", p, unsafe.Sizeof(p))
	ask("[]int", sl, unsafe.Sizeof(sl))
	ask("map[string]int", m, unsafe.Sizeof(m))
	ask("chan int", ch, unsafe.Sizeof(ch))
	ask("func()", fn, unsafe.Sizeof(fn))
	ask("interface{}", ifc, unsafe.Sizeof(ifc))
	ask("Point", st, unsafe.Sizeof(st))

	fmt.Println()
	var err error
	fmt.Println("var err error      · err == nil :", err == nil,
		"· reflect 가 보는 것 :", reflect.ValueOf(err).Kind())
	err = (*myErr)(nil)
	fmt.Println("nil 포인터를 담으면 · err == nil :", err == nil,
		"· reflect 가 보는 것 :", reflect.ValueOf(err).Kind(),
		"· IsNil :", reflect.ValueOf(err).IsNil())
}

type myErr struct{}

func (e *myErr) Error() string { return "myErr" }
===== 명령: go build -trimpath -o prog . && ./prog =====
int              Sizeof=8   Kind=int       IsNil=물을 수 없음
string           Sizeof=16  Kind=string    IsNil=물을 수 없음
*int             Sizeof=8   Kind=ptr       IsNil=true
[]int            Sizeof=24  Kind=slice     IsNil=true
map[string]int   Sizeof=8   Kind=map       IsNil=true
chan int         Sizeof=8   Kind=chan      IsNil=true
func()           Sizeof=8   Kind=func      IsNil=true
interface{}      Sizeof=16  Kind=Invalid   IsNil=물을 수 없음
Point            Sizeof=56  Kind=struct    IsNil=물을 수 없음

var err error      · err == nil : true · reflect 가 보는 것 : invalid
nil 포인터를 담으면 · err == nil : false · reflect 가 보는 것 : ptr · IsNil : true
(exit 0)
```

그림 해설 (한 단계씩):

- **`Sizeof`** — 슬라이스 24(헤더 셋), 문자열 16(포인터+길이), 인터페이스 16(타입+값),
  맵·채널·함수·포인터는 전부 **8**(포인터 하나). 구조체 `Point` 는 56.\
  ★ **이 값들은 명세 보장이 아니라 플랫폼·구현의 것**이다.
- **`Kind`** — 타입의 종류를 답한다. `IsNil` 은 **물을 수 있는 종류에만** 있다.
- ★ **마지막 두 줄이 이 창의 값어치다.**
  - `var err error` 는 `err == nil` 이 **true** 이고 `reflect` 가 보는 종류는 **`invalid`** 다 — 담긴 타입이 **없다.**
  - 거기에 **`nil` 포인터를 담으면** `err == nil` 이 **false** 로 바뀐다.
    `reflect` 는 `ptr` 을 보고 `IsNil` 은 `true` 라고 답한다.
  - 즉 「**값은 `nil` 인데 인터페이스는 `nil` 이 아니다**」가 여기서 관찰된다.
    이 함정의 정본은 [목록의 **21번 주제**](../21-nil-interface-vs-interface-holding-nil-pointer/)이고, 여기서는 **제로값 층에서 보이는 만큼만** 본다.

**이 창이 답하는 것** — 「`%v` 가 `<nil>` 이라고 말할 때, 그게 **어느 층의 `nil`** 인가」.

비용 — `reflect` 는 런타임 비용이 있다. **진단용 창**이지 본 코드에 넣을 물건이 아니다.

## 문법 — 형태와 규칙

### 형태

```go
// t02form.go
package main

import "fmt"

var ( // ⑤ 선언 블록
	host       = "localhost"
	port  int  = 8080
	debug bool // 값 없음 → false
)

var x, y = 1, "hi" // ⑥ 여러 개 — 타입이 달라도 된다

func main() {
	var a int        // ① 타입만 — 제로값
	var b = 42       // ② 값만 — 타입은 값에서
	var c int64 = 42 // ③ 둘 다
	d := 42          // ④ 짧은 선언 — 함수 안에서만
	p, q := 1, 2     // ⑦ 짧은 꼴의 여러 개
	_ = q            // ⑧ 블랭크 — 「쓴 것으로 친다」
	fmt.Println(a, b, c, d, p, host, port, debug, x, y)
}
```

```text
===== 소스: t02form.go =====
package main

import "fmt"

var ( // ⑤ 선언 블록
	host       = "localhost"
	port  int  = 8080
	debug bool // 값 없음 → false
)

var x, y = 1, "hi" // ⑥ 여러 개 — 타입이 달라도 된다

func main() {
	var a int        // ① 타입만 — 제로값
	var b = 42       // ② 값만 — 타입은 값에서
	var c int64 = 42 // ③ 둘 다
	d := 42          // ④ 짧은 선언 — 함수 안에서만
	p, q := 1, 2     // ⑦ 짧은 꼴의 여러 개
	_ = q            // ⑧ 블랭크 — 「쓴 것으로 친다」
	fmt.Println(a, b, c, d, p, host, port, debug, x, y)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
0 42 42 42 1 localhost 8080 false 1 hi
(exit 0)
```

규칙 불릿.

- **`:=` 는 함수 안에서만.** 패키지 수준에서는 `var` 만 쓸 수 있다.
- **`:=` 왼쪽에 새 변수가 하나는 있어야** 한다. 전부 기존 변수면 에러다(그때는 `=` 를 쓴다).
- **함수 안에서 선언하고 안 쓰면 컴파일 에러.** 패키지 수준은 괜찮다.
- 타입과 값을 둘 다 적으면 **값이 그 타입으로 변환 가능해야** 한다(03·04번 주제).
- `_`(블랭크 식별자)에 대입하면 「썼다」로 친다. 값은 버려진다.

### 금지 사례 — 컴파일러가 거부하는 것

**① 패키지 수준의 `:=`**

```text
===== 소스: t02e.go =====
package main

import "fmt"

count := 0

func main() { fmt.Println(count) }
===== 명령: go build -trimpath -o prog . =====
# ex
./t02e.go:5:1: syntax error: non-declaration statement outside function body
(exit 1)
===== 명령: gofmt -l . =====
t02e.go:5:1: expected declaration, found count
(exit 2)
```

- `declared and not used` 가 아니라 **`syntax error`** 다. 파서 단계에서 걸린다.
- 그래서 **이 파일은 `gofmt` 도 못 돌린다**(문법이 안 맞으니 파싱이 안 된다).

**② 안 쓴 지역 변수 / 새 변수 없는 `:=`**

```text
===== 소스: t02g.go =====
package main

import "fmt"

func main() {
	a, b := 1, 2
	a, b = 3, 4
	a, c := 5, 6
	var unused int
	fmt.Println(a, b, c)
}
===== 명령: go build -trimpath -o prog . =====
# ex
./t02g.go:9:6: declared and not used: unused
(exit 1)
```

- 에러는 **`unused` 한 줄뿐**이다. `a, c := 5, 6` 은 **`c` 가 새 변수라 통과**했다 —
  기존 `a` 는 대입만 된다.
- 즉 `:=` 는 「전부 새 변수」가 아니라 「**적어도 하나는 새 변수**」가 조건이다.

```text
===== 소스: t02h.go =====
package main

import "fmt"

func main() {
	a, b := 1, 2
	a, b := 3, 4
	fmt.Println(a, b)
}
===== 명령: go build -trimpath -o prog . =====
# ex
./t02h.go:7:7: no new variables on left side of :=
(exit 1)
```

- 새 변수가 하나도 없으면 **`no new variables on left side of :=`**.

**③ `nil` 과 비교할 수 없는 타입**

```text
===== 소스: t02k.go =====
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
===== 명령: go build -trimpath -o prog . =====
# ex
./t02k.go:13:19: invalid operation: i == nil (mismatched types int and untyped nil)
./t02k.go:14:19: invalid operation: s == nil (mismatched types string and untyped nil)
./t02k.go:15:21: invalid operation: arr == nil (mismatched types [3]int and untyped nil)
./t02k.go:16:20: invalid operation: pt == nil (mismatched types Point and untyped nil)
./t02k.go:17:14: invalid operation: sl == sl (slice can only be compared to nil)
(exit 1)
```

- `int`·`string`·배열·구조체는 **`nil` 과 비교하는 문법 자체가 없다**(`mismatched types … and untyped nil`).
- 마지막 줄이 재미있다 — **슬라이스는 `nil` 하고만 비교된다**(`slice can only be compared to nil`).
  슬라이스끼리 `==` 는 안 된다. 맵·함수도 같다.

## 어디서 틀리나

### 1. ★ `nil` 슬라이스를 그대로 JSON 으로 내보낸다

- (3)절 실측 — `null` 이 나간다. 빈 배열을 기대한 클라이언트가 터진다.
- 증상이 **서버 쪽에는 안 보인다.** 에러도 로그도 없다.
- 고치는 법 — 내보내기 직전에 `if s == nil { s = []T{} }`, 또는 애초에 `make([]T, 0)` 로 만든다.

### 2. ★ 구조체 안의 맵 필드에 바로 쓴다

- `var c Config` 의 `c.Opts` 는 `nil` 맵이다. **읽기는 되니까 테스트가 통과한다.**
- 쓰는 경로가 처음 돌 때 (4)절의 패닉이 난다 — 배포 뒤에 나기 쉽다.
- 고치는 법 — 생성자에서 `make` 하거나, 쓰기 직전에 `if m == nil { m = make(...) }`.

### 3. `:=` 로 바깥 변수를 가린다

- (6)절 3번 줄이 그 모양이다. **에러도 경고도 없다** — `go vet` 기본 검사에도 섀도잉 검사는 없다.
- 특히 `err` 에서 아프다 — 안쪽에서 `err :=` 로 받으면 바깥 `err` 은 `nil` 인 채 남는다.
- 고치는 법 — 바깥에 이미 있으면 `=` 를 쓴다. 이름이 겹치면 이름을 바꾼다.

### 4. 「선언만 했으니 쓰레기 값」이라고 생각한다

- C 에서 온 직관이다. Go 에는 **그런 상태가 없다** — (2)절 명세 인용이 전부를 약속한다.
- 그래서 **초기화 없이 바로 쓰는** 관용구가 성립한다. 넷을 한 번에 돌려 봤다.

```text
===== 소스: t02l.go =====
package main

import (
	"bytes"
	"fmt"
	"sync"
)

func main() {
	// 셋 다 make 도 생성자도 없이 제로값 그대로 쓴다.
	var buf bytes.Buffer
	buf.WriteString("제로값 그대로 ")
	buf.WriteString("쓸 수 있다")

	var mu sync.Mutex
	mu.Lock()
	mu.Unlock()

	var wg sync.WaitGroup
	wg.Add(1)
	go func() { defer wg.Done() }()
	wg.Wait()

	var s []int
	s = append(s, 1, 2, 3)

	fmt.Println("buf :", buf.String())
	fmt.Println("mu  : Lock/Unlock 통과")
	fmt.Println("wg  : Wait 통과")
	fmt.Println("s   :", s, "len =", len(s))

	// 맵만 다르다 — 제로값으로는 쓸 수 없다.
	var m map[string]int
	fmt.Println("m   :", m, "len =", len(m), "— 쓰려면 make 가 필요하다")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
buf : 제로값 그대로 쓸 수 있다
mu  : Lock/Unlock 통과
wg  : Wait 통과
s   : [1 2 3] len = 3
m   : map[] len = 0 — 쓰려면 make 가 필요하다
(exit 0)
```

- 다만 **제로값이 쓸 만한 타입과 아닌 타입**을 가려야 한다 — 마지막 줄대로 **맵만 아니다**.

### 5. `%v` 만 보고 `nil` 여부를 판단한다

- (2)절 — `nil` 슬라이스도 `[]`, 빈 슬라이스도 `[]` 다. 화면으로는 못 가른다.
- 고치는 법 — 진단할 때는 `%#v` 를 쓴다. 코드에서는 `== nil` 로 직접 묻는다.

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| 초기화식이 없으면 **타입의 제로값**이 들어간다 | **명세 보장** | "given a default value … `false` / `0` / `""` / `nil`" |
| 제로값이 **재귀적으로** 채워진다 | **명세 보장** | "This initialization is done recursively" |
| `nil` 맵 **읽기**가 제로값을 준다 | **명세 보장** | "A nil map is equivalent to an empty map except that no elements may be added." · (4)절 실측 |
| `nil` 맵 **쓰기**가 런타임 패닉 | **명세 보장** | "Assigning to an element of a nil map causes a run-time panic." · (4)절 실측 |
| `:=` 가 함수 안에서만 쓰인다 | **명세 보장** | "Short variable declarations may appear only inside functions" |
| `:=` 에 새 변수가 하나는 있어야 한다 | **명세 보장** | "… provided they were originally declared earlier in the same block … and at least one of the non-blank variables is new" |
| 슬라이스·맵·함수는 **`nil` 하고만** 비교된다 | **명세 보장** | "Slice, map, and function types are not comparable. However, as a special case, a slice, map, or function value may be compared to the predeclared identifier nil." |
| 안 쓴 **지역** 변수가 에러 | **구현(gc)** — 명세는 **허용**만 한다 | "Implementation restriction: A compiler **may** make it illegal to declare a variable inside a function body if the variable is never used." |
| **`unsafe.Sizeof` 의 값**(슬라이스 24·문자열 16·인터페이스 16) | **구현·플랫폼** | linux/amd64 의 관찰. 명세는 크기를 약속하지 않는다 |
| `%#v` 에서 `byte` 가 `0x0` 으로 찍히는 것 | **구현(`fmt`)** | 값의 차이가 아니라 표기 선택 |
| 빈 슬라이스의 데이터 포인터가 non-nil 인 것 | **구현(런타임)** | (3)절 관찰. 「길이 0인데 주소가 있다」 |
| 패닉 메시지의 `pc=0x…` | **구현(빌드 산출물)** | 같은 바이너리 3판 동일 |

★ **한 칸만 「may」다.** 안 쓴 지역 변수를 에러로 만드는 것은 명세가 **허용**한 구현 제한이고,
gc 는 그것을 **실제로 한다.** 즉 「Go 는 안 쓴 변수를 금지한다」는 정확히는
「**Go 명세가 금지를 허용하고 gc 가 금지한다**」이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 함수 안에서 값을 바로 준다 | `:=` | 가장 짧고 관용적이다 |
| 제로값으로 시작한다 | `var x T` | `x := T{}` 보다 의도가 분명하다 |
| 타입을 값과 다르게 두고 싶다 | `var x int64 = 42` | `:=` 로는 `int` 가 된다 |
| 패키지 수준 | `var` (·`const`) | `:=` 는 문법이 안 된다 |
| 여러 개를 묶는다 | `var ( … )` 블록 | 읽는 쪽이 한 덩어리로 본다 |
| 맵을 만든다 | **`make`** 또는 리터럴 | 제로값 맵은 **쓰기가 안 된다** |
| API 로 내보낼 슬라이스 | `make([]T, 0)` 또는 내보내기 전 치환 | `nil` 이면 JSON 이 `null` 이 된다 |
| 내부에서만 쓸 슬라이스 | `var s []T` | `append` 가 알아서 잡아 준다 |
| 값이 필요 없다 | `_` | 안 쓴 변수 에러를 피하는 정식 방법 |

판단 규칙 두 줄.

- **제로값이 쓸 만한지 타입마다 따져라.** 슬라이스·`bytes.Buffer`·`sync.Mutex` 는 맞고, **맵은 아니다.**
- **경계를 넘는 슬라이스는 `nil` 로 내보내지 마라.** 안에서는 같아도 밖에서는 다르다.

## 핵심 문장

- Go 에는 「초기화 안 된 변수」가 없다 — 명세가 타입마다 **제로값**을 약속한다.
- `nil` 슬라이스와 빈 슬라이스는 `len`·`cap`·`range`·`append` 가 **전부 같고**,
  갈리는 것은 **`== nil` 과 JSON 출력** 둘뿐이다.
- `nil` 맵은 **읽기·`len`·`delete` 가 되고 쓰기만 패닉**한다. 그래서 테스트가 통과하고 배포 뒤에 터진다.
- `:=` 는 **함수 안에서만**, **새 변수가 하나는** 있어야 한다. 그 조건 때문에 **조용한 섀도잉**이 생긴다.
- 안 쓴 **지역** 변수는 에러, 안 쓴 **패키지** 변수는 괜찮다. 그리고 그 에러는 명세가 **허용**한 구현 제한이다.
- `%v` 로는 `nil` 을 못 가른다. **`%#v`·`unsafe.Sizeof`·`reflect`** 셋을 같이 물어야 층이 보인다.
- 인터페이스의 제로값은 **담긴 타입이 아예 없는 상태**다 — `nil` 포인터를 담는 순간 `== nil` 이 거짓이 된다.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 02번)
- [01번 주제](../01-packages-imports-main-and-init/)(패키지·`init`) —
  **패키지 변수가 언제 초기화되는가**는 거기. 여기는 **무엇으로 초기화되는가**다
- [03번 주제](../03-constants-iota-and-untyped-constants/)(상수·타입 없는 상수) —
  `b := 42` 의 타입이 왜 `int` 인지, 즉 **기본 타입 규칙**의 정본
- [04번 주제](../04-numeric-types-conversions-and-integer-division/)(수치 타입) —
  `var c int64 = 42` 가 되고 `var c int64 = i` 가 안 되는 이유
- [`../../../../variables-and-memory/`](../../../../variables-and-memory/) —
  **그쪽은 변수·스택·힙·포인터라는 개념 자체**까지, **여기는 Go 의 제로값 규칙과 선언 문법**부터다.
  메모리 모형을 여기서 다시 설명하지 않는다
- [목록의 **05번 주제**](../05-arrays-vs-slices-value-and-header/)(배열과 슬라이스) — 슬라이스 헤더 3필드의 정본.
  여기서는 `nil` 여부와 `Sizeof` 24 까지만 봤다
- [목록의 **09번 주제**](../09-maps-declaration-comma-ok-delete-and-iteration-order/)(맵) — `comma-ok`·순회 무작위화의 정본.
  여기서는 **`nil` 맵의 읽기/쓰기 비대칭**까지만 봤다
- [목록의 **16번 주제**](../16-pointers-value-copy-semantics-new-and-make/)(포인터·`new`/`make`) — `new(T)` 와 `var t T` 의 관계
- [목록의 **21번 주제**](../21-nil-interface-vs-interface-holding-nil-pointer/)(`nil` 인터페이스) — (7)절 마지막 두 줄의 정본
- 목록의 **45번 주제**(`encoding/json`) — `null` 과 빈 배열을 가르는 설계의 정본

## 용어 풀이

- **제로값(zero value)** — 초기화식이 없을 때 들어가는 타입별 기본값.
- **`nil`** — 포인터·슬라이스·맵·채널·함수·인터페이스의 제로값을 나타내는 미리 선언된 식별자. 타입이 없다.
- **짧은 변수 선언(`:=`)** — 함수 안에서만 쓰는 선언 꼴. 타입을 값에서 추론한다.
- **선언 블록(`var ( … )`)** — 선언 여럿을 괄호로 묶는 꼴.
- **블랭크 식별자(`_`)** — 값을 버리면서 「썼다」로 치는 이름.
- **섀도잉(shadowing)** — 안쪽 블록에서 같은 이름을 다시 선언해 바깥을 가리는 것.
- **슬라이스 헤더** — (데이터 포인터, `len`, `cap`) 세 칸. 이 플랫폼에서 24바이트.
- **`comma-ok`** — `v, ok := m[k]` 꼴. 키가 있었는지를 두 번째 값으로 받는다.
- **`%#v`** — Go 문법 꼴로 찍는 포맷 동사. 타입과 `nil` 여부가 같이 보인다.
- **`unsafe.Sizeof`** — 값이 차지하는 바이트 수. 컴파일 타임 상수이고 **플랫폼에 달렸다**.
- **`reflect.Kind`** — 타입의 종류(`slice`·`ptr`·`struct` …). 인터페이스가 비었으면 `invalid`.
- **구현 제한(implementation restriction)** — 명세가 「컴파일러가 이렇게 해도 된다」고 허용한 조항.

---

## 더 들어가면

- `var x, y = 1, "hi"` 처럼 **타입이 다른 여러 개**를 한 줄에 선언할 수 있다. 타입을 적으면 다 같은 타입이 된다.
- `make([]int, 0, 4)` 는 `cap` 만 4다((3)절 실측). **미리 잡아 두면 `append` 의 재할당이 준다** —
  얼마나 주는지는 [목록의 **06번 주제**](../06-len-cap-and-append-reallocation/)에서 잰다(여기서는 안 쟀다).
- `Point` 의 `Sizeof` 가 56 인 것은 `int`8 + `int`8 + `string`16 + `[]string`24 다.
  **필드 순서를 바꾸면 달라질 수 있다** — 정렬·패딩은 [목록의 **17번 주제**](../17-struct-literals-comparability-field-tags-and-sorting/).
- 인터페이스가 16바이트인 것은 (타입 포인터, 값 포인터) 두 칸이기 때문이다.
  그래서 (7)절 마지막 줄에서 **타입 칸만 채워진 상태**가 만들어진다.
- `gofmt` 는 `var ( … )` 블록 안의 `=` 를 세로로 맞춰 준다. 손으로 맞출 필요가 없다.
- 패키지 수준의 `:=` 가 `syntax error` 인 것은 **`:=` 가 선언(declaration)이 아니라 문(statement)** 이기 때문이다.
  패키지 블록에는 선언만 올 수 있다.

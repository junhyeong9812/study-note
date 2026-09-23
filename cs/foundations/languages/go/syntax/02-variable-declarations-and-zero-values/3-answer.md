# go/syntax/02 — 변수 선언 세 형태와 제로값 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 손으로 옮겨 적은 블록은 없다.\
> 블록은 전부 `===== 소스: … =====` 로 소스를 먼저 싣는다 — **그대로 다시 던질 수 있게** 하기 위해서다.
> ★ **근거로 읽을 칸** — 제로값 자체, `== nil` 의 참·거짓, 에러 문장 본문, `파일:줄:칸`, 종료 코드.
> **근거로 읽지 않을 칸** — `unsafe.Sizeof` 의 값(플랫폼에 달렸다),
> 패닉의 `pc=0x…`·`+0x…`(빌드 산출물에 달렸다. 같은 바이너리 3판은 md5 동일).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 여섯이 `nil`, 나머지는 `0`·`false`·`""` — 그리고 `%v` 로는 셋이 헷갈린다

**출력**

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

**왜 그런가**

- `== nil` 이 **true** 인 행은 **여섯**이다 — `*int` · `[]int` · `map` · `chan` · `func` · `interface{}`.
  나머지 여덟(수치·`bool`·`string`·`rune`·`byte`·배열·구조체)은 **비교 문법 자체가 없다**(8번).
- **`%v` 와 `%#v` 가 다른 행**이 이 표의 요점이다.
  - `[]int` — `%v` 는 `[]`, `%#v` 는 `[]int(nil)`.
  - `map[string]int` — `%v` 는 `map[]`, `%#v` 는 `map[string]int(nil)`.
  - `*int`·`chan`·`func` — `%v` 는 `<nil>`, `%#v` 는 `(*int)(nil)` 처럼 **타입이 붙는다.**
  - `byte` — `%#v` 가 `0x0` 이다. **값이 다른 게 아니라 `fmt` 의 표기 선택**이다.
  - `interface{}` — `%#v` 도 `<nil>` 이다. **담긴 타입이 아예 없어서** 붙일 타입이 없다.
- `Point` 행의 `Tags` 는 **`[]string(nil)`** 이다. 구조체 안의 슬라이스 필드도 `nil` 이다.

```text
  같은 <nil> 이라도 층이 다르다

  var p *int        ->  타입 *int 의 값이 nil
  var ifc any       ->  담긴 타입이 아예 없음   <- %#v 로만 구별된다
```

**명세**

> … no explicit initialization is provided, the variable or value is
> given a default value. Each element of such a variable or value is
> set to the zero value for its type: `false` for booleans,
> `0` for numeric types, `""` for strings, and `nil` for pointers, functions,
> interfaces, slices, channels, and maps.
> This initialization is done recursively …

### 2. `len`·`cap`·`Sizeof` 는 넷 다 같고, `== nil` 과 JSON 만 갈린다

**출력**

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

**왜 그런가**

| 만드는 법 | `len` | `cap` | `== nil` | `json` |
|---|---|---|---|---|
| `var a []int` | 0 | 0 | **true** | **`null`** |
| `[]int{}` | 0 | 0 | false | `[]` |
| `make([]int, 0)` | 0 | 0 | false | `[]` |
| `make([]int, 0, 4)` | 0 | **4** | false | `[]` |

- **`len`·`range`·`append` 는 넷 다 똑같이 동작한다.** 그래서 안쪽 코드에서는 구별이 안 보인다.
- 갈리는 것은 **`== nil` 과 JSON** 둘이다. `reflect.DeepEqual(a, b)` 도 **false** 다.
- **`Sizeof` 는 넷 다 24** — 슬라이스 값은 (데이터 포인터, `len`, `cap`) 세 칸이고
  이 플랫폼에서 포인터가 8바이트라 8×3 이다.\
  ★ **24는 명세 보장이 아니다.** linux/amd64 의 관찰이다.
- 데이터 포인터가 `nil` 인 것은 `var a []int` 하나뿐 — `[]int{}` 는 길이가 0인데도 **주소가 있다.**

```text
  안에서 보면 같다                밖으로 내보내면 다르다
  +--------------------+          +--------------------+
  | len 0 · cap 0      |          | nil  -> null       |
  | range 0바퀴        |          | 빈것 -> []         |
  | append 둘 다 된다  |          |                    |
  +--------------------+          +--------------------+
    -> 테스트가 안 잡는다            -> 클라이언트가 터진다
```

### 3. 네 줄 찍고 다섯째에서 죽는다 — 종료 코드 2

**출력**

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

**왜 그런가**

- **읽기 세 줄이 전부 통과**한다. `m == nil` 은 true, `len(m)` 은 0,
  없는 키는 **제로값 0**, `comma-ok` 는 `0 false`.
- `delete` 도 아무 일이 없다.

  > If the map `m` is nil or the element `m[k]` does not exist, `delete` is a no-op.

- **쓰기만 패닉**한다.

  > Assigning to an element of a nil map causes a run-time panic.

  메시지는 `panic: assignment to entry in nil map`, 종료 코드 **2**다.
- 표준 오류로 나간 줄은 **마커 줄(`----- 여기까지 stdout …`)과 패닉 전문**이다.
  마커를 일부러 `fmt.Fprintln(os.Stderr, …)` 로 찍었기 때문에
  **파이프로 받아도 위치가 안 바뀐다.**

> **no-op** — 아무 일도 하지 않고 그냥 돌아오는 연산.\
> 예: `nil` 맵에 `delete` 를 불러도 에러가 아니라 그냥 지나간다.

### 4. 한 줄 · 한 줄 · 한 줄 — 그런데 첫째만 층이 다르다

**출력**

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

**왜 그런가**

- `syntax error: non-declaration statement outside function body` — **파서 단계**에서 걸린다.
  `:=` 는 선언이 아니라 **문(statement)** 이고, 패키지 블록에는 선언만 올 수 있다.
- ★ 그래서 **`gofmt` 도 못 돌린다** — 둘째 명령이 `expected declaration, found count` 를 내고
  종료 코드가 **2**다. 파싱이 안 되니 포맷할 수도 없다.
  (01번 주제의 「쓰지 않은 import」와 정반대다 — 그쪽은 `gofmt` 가 통과시켰다.)

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

- 에러는 **`unused` 한 줄뿐**이다.
- `a, b = 3, 4` 는 대입이라 문제없고, **`a, c := 5, 6` 은 `c` 가 새 변수라 통과**한다.

  > … a short variable declaration may redeclare
  > variables provided they were originally declared earlier in the same block …
  > and **at least one of the non-blank variables is new**.

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

- 새 변수가 하나도 없으면 `no new variables on left side of :=`. 이때는 `=` 를 써야 한다.

### 5. `패키지 수준` → `main 의 v` → `3` → `main 의 v` → `if 의 v` → `main 의 v`

**출력**

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

**왜 그런가**

- **2번** — `v := "main 의 v"` 는 **대입이 아니라 새 선언**이다. 패키지 변수를 가릴 뿐 바꾸지 않는다.
- **3번** — 블록 안의 `v := 3` 은 또 다른 새 변수라 **타입까지 `int` 로 바뀐다.**
  같은 변수라면 불가능한 일이다.
- **4번** — 블록을 나오니 바깥 `v` 가 그대로다. 안쪽에서 무엇을 해도 **바깥에 안 남는다.**
- **5\~6번** — `if v := …; …` 의 `v` 는 **`if` 문 전체**가 스코프다. 밖으로 안 새어 나온다.

```text
  패키지 v ──┐
             │ (가려짐)
   main v ───┼──┐
             │  │ (가려짐)
   블록 v(int)──┘
             │
   블록을 나오면 main v 로 되돌아온다
```

**왜 문제인가**

- **컴파일 에러도 경고도 없다.** `go vet` 의 기본 검사에도 섀도잉 검사는 없다.
- 특히 `err` 에서 아프다 — 안쪽에서 `err :=` 로 받으면 바깥 `err` 은 `nil` 인 채 남아
  「**에러가 났는데 에러가 없다**」가 된다.

### 6. `int` · `int` · `int64` · `int` · `float64` · `int32` · `string` · `complex128`

**출력**

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

**왜 그런가**

- `a` 는 타입만 적었으므로 **제로값 0**.
- `b := 42` 와 `d := 42` 는 **타입 없는 정수 상수의 기본 타입**인 `int`.
- `c` 는 `int64` 를 적었으므로 `int64`.
- `e := 42.0` → `float64`, `h := 42 + 0i` → `complex128`. 역시 기본 타입 규칙이다.
- ★ **`f := 'A'` 가 `int32` 로 찍힌다.** `rune` 은 **`int32` 의 별칭**이라
  `%T` 가 답할 이름이 `int32` 뿐이다 — `rune` 이라는 **별개 타입이 아니다**(04번 주제).
- 마지막 줄의 `debug` 는 값을 안 적었으므로 **`false`**.
- `pkgLevelUnused` 는 **패키지 수준**이라 안 써도 된다. 금지되는 것은 **함수 안**뿐이다.

### 7. 명세 보장이다 — 그리고 「재귀적」이 그 약속의 절반이다

**출력** (제로값만으로 바로 쓰는 네 가지)

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

**왜 그런가**

- **명세 보장**이다. 1번의 인용이 전문이고, 핵심 낱말이 둘이다.
  - 「**default value**」 — 쓰레기 값이 아니라 **정해진 값**이다.
  - 「**recursively**」 — 구조체 안의 구조체, 배열의 각 원소까지 **전부** 내려가며 채운다.
    그래서 `Point{}` 의 `Tags` 가 `nil` 인 것이 1번에서 보였다.
- 그 약속 덕에 성립하는 관용구 — 위 출력이 넷을 한 번에 보인다.
  - `var buf bytes.Buffer` 를 **생성자 없이 바로** `WriteString` 한다.
  - `var mu sync.Mutex` 를 바로 `Lock`/`Unlock` 한다.
  - `var wg sync.WaitGroup` 을 바로 `Add`/`Wait` 한다.
  - `var s []int` 에 바로 `append` 한다.
- ★ **도움이 안 되는 타입은 맵이다.** 마지막 줄 — `nil` 맵은 읽기만 되고
  **쓰려면 `make` 가 필요하다**(3번). 「제로값이 쓸 만하다」가 타입마다 다르다는 것이 요점이다.

### 8. 다섯 줄 전부 에러 — 그리고 마지막 줄만 이유가 다르다

**출력**

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

**왜 그런가**

- 앞 네 줄은 **`mismatched types … and untyped nil`** 이다.
  `nil` 은 **타입 없는 값**이라 `int`·`string`·배열·구조체와는 **비교식 자체가 성립하지 않는다.**
- 마지막 줄은 **`slice can only be compared to nil`** — 이유가 다르다.
  슬라이스는 `nil` 과는 비교되지만 **서로는 비교가 안 된다.**

  > Slice, map, and function types are not comparable. However, as a special case,
  > a slice, map, or function value may be compared to the predeclared identifier `nil`.

- **`== nil` 을 물을 수 있는 타입** — 포인터 · 슬라이스 · 맵 · 채널 · 함수 · 인터페이스. **여섯.**
- 두 슬라이스가 같은지 보려면 **`slices.Equal`**(1.21부터, 목록의 **38번 주제**)이나
  `reflect.DeepEqual` 을 쓴다. 후자는 2번에서 봤듯 **`nil` 과 빈 것을 다르게** 본다.

### 9. 같은 것 넷, 다른 것 둘

**출력** (2번과 같은 블록이 근거다)

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

**왜 그런가**

- **같게 동작하는 것** — `len` · `cap` · `range`(0바퀴) · `append` · `unsafe.Sizeof`(24).
  넷을 넘겨 다섯이다.
- **다르게 동작하는 것** — ① `== nil` ② `encoding/json` 의 출력(`null` 대 `[]`).
  덤으로 `reflect.DeepEqual` 과 **데이터 포인터의 `nil` 여부**도 다르다.
- **고르는 기준**
  - 안쪽 코드용 — `var s []T` 가 낫다. `append` 가 알아서 잡아 주고 할당이 없다.
  - API 응답용 — `make([]T, 0)` 이 낫다. `null` 이 나가면 클라이언트가 터진다.
- **`unsafe.Sizeof` 로는 못 가른다** — 넷 다 24다. 크기는 헤더 세 칸의 크기이지 내용이 아니다.

### 10. 다른 주제와 잇기

**출력** — 없음(연결 문항).

**왜 그런가**

- **`b := 42` 가 `int` 가 되는 규칙** — 타입 없는 상수의 **기본 타입(default type)** 규칙이다.
  정본은 [03번 주제](../03-constants-iota-and-untyped-constants/).
  명세: "The default type of an untyped constant is `bool`, `rune`, `int`, `float64`, `complex128`, or `string` …"
- **`var c int64 = 42` 는 되고 `var c int64 = d` 는 안 되는 이유** —
  `42` 는 **타입 없는 상수**라 대입 지점에서 `int64` 가 되지만,
  `d` 는 이미 `int` **타입이 붙은 값**이라 명시 변환이 필요하다.
  정본은 [04번 주제](../04-numeric-types-conversions-and-integer-division/).
- **슬라이스 헤더 세 칸** — 정본은 목록의 **05번 주제**.
  여기서는 `Sizeof` 24 와 `nil` 여부까지만 봤다.
- 「**값은 `nil` 인데 인터페이스는 `nil` 이 아니다**」 — 정본은 목록의 **21번 주제**.
  이 문서의 (7)절 마지막 두 줄이 그 현상을 제로값 층에서 **관찰만** 한 것이다.
- **패키지 변수가 언제 초기화되는가** — 정본은 [01번 주제](../01-packages-imports-main-and-init/).
  「무엇으로」는 여기, 「언제」는 거기다.

---

## 실행 검증

| 실험 | 던진 명령 | 결과 | 문항 |
|---|---|---|---|
| 판 확인 | `go version` · `go env` | `go1.27.1 linux/amd64` | 머리말 |
| 제로값 14종 (`t02a`) | `go build -trimpath && ./prog` | 표 그대로 · `nil` 여섯 | 1 |
| 슬라이스 4종 (`t02b`) | 〃 | `len`/`cap`/`Sizeof` 동일 · `nil`·JSON 만 갈림 | 2 · 9 |
| `nil` 맵 (`t02c`) | `go build` · `./prog 2>&1` | 읽기 4줄 통과 · 쓰기에서 **패닉** · exit 2 | 3 |
| `nil` 포인터 (`t02d`) | 〃 + 3판 md5 | `p == nil` true · `*p` 에서 SIGSEGV · **3판 md5 동일** | 2-summary |
| 패키지 수준 `:=` (`t02e`) | `go build` | `syntax error: non-declaration statement …` | 4 |
| 같은 파일 (`t02e`) | `gofmt -l .` | `expected declaration, found count` · **exit 2** | 4 |
| 안 쓴 지역 변수 (`t02g`) | `go build` | `declared and not used: unused` **한 줄** | 4 |
| 새 변수 없는 `:=` (`t02h`) | `go build` | `no new variables on left side of :=` | 4 |
| 섀도잉 6줄 (`t02i`) | `go build && ./prog` | 2·3·5 가 가리고 4·6 이 되돌아옴 | 5 |
| 선언 네 형태 (`t02f`) | 〃 | `int int int64 int float64 int32 string complex128` | 6 |
| 제로값으로 바로 쓰기 (`t02l`) | 〃 | `Buffer`·`Mutex`·`WaitGroup`·슬라이스 통과, **맵만 불가** | 7 |
| `nil` 비교 (`t02k`) | `go build` | 다섯 줄 에러 · 마지막만 이유가 다름 | 8 |
| 세 가지 질의 (`t02j`) | `go build && ./prog` | `Sizeof`/`Kind`/`IsNil` · 인터페이스는 `invalid` | 2-summary (7) |
| stdout/stderr 순서 (`t00buf`) | `./prog 2>&1` 3판 md5 | **3판 동일** — Go 는 stdout 을 버퍼링하지 않는다 | 머리말 |

**구현·환경에 달린 항목**(다시 찍을 자리)

| 항목 | 무엇에 달렸나 |
|---|---|
| `unsafe.Sizeof` 의 값(슬라이스 24·문자열 16·인터페이스 16·`Point` 56) | **플랫폼·구현**. 명세는 크기를 약속하지 않는다 |
| 빈 슬라이스의 데이터 포인터가 non-nil 인 것 | **런타임 구현**. 「길이 0인데 주소가 있다」 |
| `%#v` 가 `byte` 를 `0x0` 으로 찍는 것 | **`fmt` 의 표기 선택**. 값의 차이가 아니다 |
| 안 쓴 지역 변수가 **에러**인 것 | **gc 의 선택**. 명세는 "A compiler **may** make it illegal …" 로 허용만 한다 |
| 패닉의 `pc=0x499e84` · `+0x…` | **빌드 산출물**. 같은 바이너리 3판 md5 동일, 판이 바뀌면 바뀐다 |
| `Point` 의 56바이트 배치 | **필드 정렬·패딩**(목록의 **17번 주제**). 필드 순서를 바꾸면 달라질 수 있다 |
| 32비트 플랫폼에서의 `Sizeof` | **못 돌려 봤다** — 이 머신에 그 타깃이 없다. 「안 돌려 봄」이 아니라 환경이 없어 못 잰 것이다 |

# go/syntax/09 — 맵: 선언·comma-ok·`delete`·순회 순서 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★★★ **이 주제의 답은 「한 판의 출력」이 아니라 「몇 가지가 나오나」와 「무엇이 보장되나」다.**
> ★ **근거로 읽을 칸** — 600판 `sort -u` 의 **줄 수** · 패닉 메시지 본문 · 컴파일 에러 문장 ·
> `파일:줄` · 종료 코드 · `len` · comma-ok 의 `true`/`false`.
> **근거로 읽지 않을 칸** — **한 판의 순회 순서**(흔들린다) · 순서별 **빈도 수치**(흔들린다) ·
> 패닉 스택의 **주소 오프셋** · 「3가지가 나온다」의 **3이라는 수**(gc 의 사정이다).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `var` 로 만든 것만 nil 이고, 그 nil 맵은 **읽기만** 된다

**출력**

```text
===== 소스: t09a.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
① var     a == nil : true   len=0
② make    b == nil : false  len=0
③ 리터럴  c == nil : false  len=1
④ 힌트    d == nil : false  len=0

nil 맵에서 읽는 것은 전부 된다 — 패닉이 아니라 제로값이다
  a["없는키"]           = 0
  v, ok := a["없는키"]  = 0 false
  len(a)                = 0
  delete(a, "없는키")   도 그냥 된다
  for range a           는 0번 돈다
(exit 0)
```

```text
===== 소스: t09b.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
-- m == nil : true · 읽기는 됐다 : 0 --
-- 이제 쓴다 : m["k"] = 1 --
panic: assignment to entry in nil map

goroutine 1 [running]:
main.main()
	ex/t09b.go:12 +0xe9
(exit 2)
```

**왜 그런가**

- `== nil` 이 참인 것은 **`a`(`var`) 하나**다. `make` 와 리터럴은 **빈 맵**이고 nil 이 아니다.
- nil 맵에 대해 **읽기·comma-ok·`len`·`delete`·`range` 가 전부 통과**한다.
  명세가 그렇게 적는다.

  > **A nil map is equivalent to an empty map except that no elements may be added.**

- `make(map[string]int, 100)` 의 100은 **크기 힌트**다. 상한이 아니다 —
  "**The initial capacity does not bound its size.**" 게다가 **되물을 수도 없다**(`cap` 이 없다).
- 쓰기 한 줄에서 **`panic: assignment to entry in nil map`** 이 나고 **종료 코드는 2** 다.
  명세: "**Assigning to an element of a nil map causes a run-time panic.**"
- ★ 마커를 **표준 오류로 찍은 이유** — 패닉도 표준 오류로 나간다.
  표준 출력으로 찍으면 **파이프로 받을 때 버퍼링 때문에 순서가 뒤집힌다.**
  같은 스트림으로 찍으면 순서가 고정된다.
- ★★★ **이 비대칭이 이 주제의 가장 잦은 사고**다. 읽기만 하는 테스트는 **반드시 통과**한다.

### 2. 둘 다 `0` 으로 찍히고, comma-ok 만이 둘을 가른다

**출력**

```text
===== 소스: t09c.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
값이 0 인 키와 아예 없는 키는 그냥 읽으면 구분이 안 된다
  m["b"]    = 0
  m["없음"] = 0

comma-ok 가 그 둘을 가른다
  v, ok := m["b"]    -> 0 true
  v, ok := m["없음"] -> 0 false
  _, ok := m["b"]    -> true   (값을 안 받아도 된다)

delete
  delete(m, "a")     뒤 len=1  m["a"]=0
  없는 키를 지워도 아무 일 없다 len=1
  지운 뒤 comma-ok   -> false
  clear(m) (1.21) 뒤 len=0  m == nil : false
(exit 0)
```

**왜 그런가**

| 읽는 법 | `m["b"]`(값이 0) | `m["없음"]`(없음) |
|---|---|---|
| `v := m[k]` | `0` | `0` — **구분 불가** |
| `v, ok := m[k]` | `0 true` | `0 false` |

- 한 값 꼴로는 **원리상 구분이 안 된다.** 없는 키는 **값 타입의 제로값**을 주기 때문이다.
- comma-ok 는 명세가 정한 특별한 꼴이다 —
  "**An index expression on a map … of the special form `v, ok = a[x]` … yields an additional
  untyped boolean value.**"
- 없는 키를 `delete` 해도 **아무 일도 없다.** 존재 검사를 먼저 할 필요가 없다.
- ★ **`clear(m)` 뒤에도 `m == nil` 은 false** 다. `clear` 는 **항목만** 비운다.
  맵 자체를 없애려면 `m = nil` 이라고 적어야 하고, 그러면 **그 뒤 쓰기가 패닉**이다.
  (`clear` 는 **1.21**부터다.)

### 3. 3개짜리는 **3줄**, 8개짜리는 **8줄** — 순열 수가 아니다

**출력**

```text
===== 소스: t09d.go =====
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
===== 명령: go build -trimpath -o prog . =====
(exit 0)
===== 명령: for i in $(seq 1 600); do ./prog 3; done | sort -u =====
abc
bca
cab
(exit 0)
===== 명령: for i in $(seq 1 600); do ./prog 3; done | sort -u | wc -l =====
3
(exit 0)
===== 명령: for i in $(seq 1 600); do ./prog 8; done | sort -u | wc -l =====
8
(exit 0)
===== 명령: for i in $(seq 1 600); do ./prog 9; done | sort -u | wc -l | awk "{print (\$1 > 100 ? \"100가지 넘음\" : \$1)}" =====
100가지 넘음
(exit 0)
```

```text
===== 소스: t09e.go =====
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
===== 명령: go build -trimpath -o prog . =====
(exit 0)
===== 명령: for i in $(seq 1 600); do ./prog; done | sort -u =====
한 프로세스 안에서 두 번 돈 순서가 같은가 : false
한 프로세스 안에서 두 번 돈 순서가 같은가 : true
(exit 0)
```

**왜 그런가**

- `./prog 3` 을 600번 돌려 `sort -u` 하면 **3줄**(`abc`·`bca`·`cab`)이다.
  3개의 순열은 6가지인데 **절반만 나왔다** — 나온 셋은 전부 **회전**이다.
- `./prog 8` 은 **8줄**, `./prog 9` 는 **100가지를 훌쩍 넘었다**.
  8과 9 사이에서 계단이 있다.
- ★★★ **이 수치는 명세가 아니라 gc 의 사정이다.** 명세는 가짓수를 **한 마디도** 하지 않는다.

  > **The iteration order over maps is not specified and is not guaranteed to be the same
  > from one iteration to the next.**

  작은 맵이 **한 묶음에 담기고 gc 가 시작 칸만 무작위로 고르기 때문**에 회전만 나오는 것으로 보이고,
  9개부터는 묶음이 여럿이라 섞이는 폭이 넓어진다.
  ★ **이 설명은 관찰에서 세운 것이고, 이 문서는 런타임 소스를 읽어 확인하지 않았다.**
- `t09e` 는 **한 프로세스 안에서 연달아 두 번** 돈 것을 비교한다. 600판에서 **`true` 와 `false` 가 둘 다** 나왔다.
  이것을 정하는 문장이 위 인용의 뒷부분 — "**is not guaranteed to be the same from one iteration to the next**".
- ★★ 그래서 **「세 번 돌려 봤는데 같더라」가 근거가 못 된다.**
  2000판 분포에서 `abc` 한 가지가 **1472판**을 차지했다 — **세 판이 우연히 같은 일이 예사**다.

### 4. 지우기는 **단정**, 넣기는 **열려 있다**

**출력**

```text
===== 소스: t09f.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
8개짜리 맵을 돌면서 나머지를 전부 지웠더니 본 항목 수 : 1
(exit 0)
```

```text
===== 소스: t09g.go =====
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
===== 명령: go build -trimpath -o prog . =====
(exit 0)
===== 명령: for i in $(seq 1 600); do ./prog; done | sort -u =====
4
5
(exit 0)
```

**왜 그런가**

- `t09f` 는 **항상 `1`** 이다. 흔들리지 않는다. 명세가 단정하기 때문이다.

  > **If a map entry that has not yet been reached is removed during iteration,
  > the corresponding iteration value will not be produced.**

- `t09g` 는 600판에서 **`4` 와 `5` 둘 다** 나왔다. 명세가 열어 둔 자리다.

  > **If a map entry is created during iteration, that entry may be produced during the iteration
  > or may be skipped. The choice may vary for each entry created and from one iteration to the next.**

- ★ 그래서 Go 에서는 **「돌면서 지우기」가 안전한 관용구**다.
  자바의 `ConcurrentModificationException` 같은 것이 없다.
- ★★ **「돌면서 넣기」는 결과가 정해지지 않는다.** 고치는 법은 **키를 먼저 모으는 것**이다 —
  `for k := range m` 으로 키를 슬라이스에 담고, **루프가 끝난 뒤** 넣는다.

### 5. **컴파일 단계**에서 두 줄이 나온다 — 맵은 주소를 안 내준다

**출력**

```text
===== 소스: t09h.go =====
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
===== 명령: go build -trimpath -o prog . =====
# ex
./t09h.go:9:8: invalid operation: cannot take address of m["a"] (map index expression of type int)
./t09h.go:13:2: cannot assign to struct field s["a"].N in map
(exit 1)
```

**왜 그런가**

- 두 줄 다 **컴파일 에러**이고 **종료 코드는 1** 이다. 실행까지 가지 못한다.
  - `cannot take address of m["a"] (map index expression of type int)`
  - `cannot assign to struct field s["a"].N in map`
- 슬라이스에서는 **된다** — `&s[0]` 도 `s[0].N = 2` 도 된다.
- ★ 갈리는 이유는 **자리가 움직이는가**다. 맵은 자라면서 항목을 **옮긴다.**
  주소를 내주면 그 주소가 언제든 낡은 것이 되므로, Go 는 **주소를 잡는 일 자체를 문법으로 막았다.**
  슬라이스의 원소는 기반 배열에서 **자리가 고정**이다(재할당 전까지는 — 목록의 **06번 주제**).
- 고치는 법 셋.
  - ① **꺼내 고쳐 다시 넣는다** — `v := m[k]; v.N = 2; m[k] = v`.
  - ② **값을 포인터로** — `map[string]*P` 면 `m[k].N = 2` 가 된다.
  - ③ 순서가 필요하거나 자주 고치면 **맵이 아니라 슬라이스**로 바꾼다.

### 6. 컴파일은 되고 **넣는 순간 런타임 패닉**이다

**출력**

```text
===== 소스: t09k.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
-- 여기까지 len=2 --
-- 이제 슬라이스를 키로 넣는다 --
panic: runtime error: hash of unhashable type []int

goroutine 1 [running]:
main.main()
	ex/t09k.go:14 +0x258
(exit 2)
```

**왜 그런가**

- 컴파일은 **통과한다.** `map[any]string` 자체는 적법하다.
- 정수와 배열은 들어갔고, 슬라이스를 넣는 줄에서
  **`panic: runtime error: hash of unhashable type []int`** 가 나며 **종료 코드 2** 다.
- 명세가 이것을 예고해 둔다.

  > **If the key type is an interface type, these comparison operators must be defined
  > for the dynamic key values; failure will cause a run-time panic.**

- ★★ **키 타입이 `any` 이면 컴파일러의 보호를 잃는다.** 검사가 **런타임으로 미뤄진다.**
- 컴파일 때 잡으려면 **키 타입을 구체 타입으로 못 박는다**(`map[string]…`·`map[Point]…`).
  JSON 에서 온 값을 그대로 키로 쓰는 코드가 실제로 여기서 터진다.

### 7. 항목이 **움직이기 때문**이다

**출력** — 없음(왜 문항).

**왜 그런가**

- 맵은 항목이 늘면 **더 큰 저장소로 옮긴다.** 어느 항목이 어디로 갈지는 **밖에서 알 수 없다.**
  주소를 한 번 내주면 그 주소는 **다음 삽입에 낡은 것**이 될 수 있다.
- 슬라이스는 다르다 — 원소의 자리는 **기반 배열 안에서 고정**이다.
  재할당은 `append` 라는 **눈에 보이는 연산**에서만 일어나고, 그때 헤더가 바뀌는 것이 계약이다.
- 코드 모양의 차이 — **맵 값이 구조체면 「꺼내 고쳐 다시 넣기」가 강제**된다.
  그래서 Go 코드에서 `map[K]*V` 가 자주 보인다.
- 이 제약이 없었다면 — **삽입 하나가 남이 들고 있던 포인터를 조용히 무효화**할 수 있다.
  값은 멀쩡히 읽히는데 **엉뚱한 항목**을 가리키는, 에러 없는 버그다.
  ★ Go 는 그 종류의 사고를 **문법으로 원천 차단**하는 쪽을 골랐다.

### 8. 네 줄 전부 거부된다 — 가르는 낱말은 「**비교 가능**」이다

**출력**

```text
===== 소스: t09j.go =====
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
===== 명령: go build -trimpath -o prog . =====
# ex
./t09j.go:10:12: invalid map key type []int
./t09j.go:11:16: invalid map key type func()
./t09j.go:12:12: invalid map key type Bad
./t09j.go:13:12: invalid map key type map[string]int
(exit 1)
```

**왜 그런가**

- **네 줄 다** `invalid map key type` 이다. 종료 코드 1.
- `Bad` 는 구조체인데도 거부된다 — **필드에 슬라이스가 있기 때문**이다.
  구조체의 비교 가능성은 **모든 필드가 비교 가능할 때만** 성립한다(목록의 **17번 주제**).
- 가르는 낱말은 **비교 가능(comparable)** 이다. 명세가 그렇게 적는다.

  > **The comparison operators `==` and `!=` must be fully defined for operands of the key type;
  > thus the key type must not be a function, map, or slice.**

- ★ 그 기준이 **컴파일 때 정해지지 않는 타입**은 **인터페이스**다.
  `map[any]V` 는 컴파일을 통과하고 **런타임에 터진다**(6번 문항).

### 9. 명세는 ①③④⑤⑦, gc·라이브러리의 사정은 ②⑥⑧

**출력** — 없음(경계 문항).

**왜 그런가**

| | 주장 | 판정 | 근거 |
|---|---|---|---|
| ① | 순회 순서가 정해져 있지 않다 | **명세 보장** | "The iteration order over maps is not specified …" |
| ② | 3개짜리에서 3가지만 나온다 | **gc 의 사정** | 명세는 가짓수를 말하지 않는다. 판이 오르면 바뀔 수 있다 |
| ③ | nil 맵에 쓰면 패닉 | **명세 보장** | "Assigning to an element of a nil map causes a run-time panic." |
| ④ | 지운 항목은 안 나온다 | **명세 보장** | "… will not be produced." |
| ⑤ | 넣은 항목은 나올 수도 안 나올 수도 | **명세 보장(열어 둠)** | "may be produced … or may be skipped" |
| ⑥ | `fmt.Println(m)` 이 키 순서 | **표준 라이브러리의 계약** | 1.12 부터. **`range` 의 보장이 아니다** |
| ⑦ | `cap(m)` 이 컴파일 에러 | **명세 보장** | `cap` 은 맵을 받지 않는다 |
| ⑧ | `abc` 가 다섯 배 넘게 나온다 | **gc 의 사정** | 시작 칸 뽑기의 결과. 실행마다 흔들린다 |

- ★★★ ⑤가 가장 헷갈리는 칸이다 — **「정해지지 않았다」가 명세의 보장**이다.
  「구현이 아직 안 정했다」가 아니라 「**영원히 안 정하겠다**」는 뜻이므로,
  **그 위에 결론을 세우면 안 된다**는 것까지가 보장에 포함된다.
- ★ ⑥은 **명세가 아니라 `fmt` 의 계약**이다. 이것을 「Go 가 맵을 정렬한다」로 읽으면 ①과 충돌한다.
  **찍을 때만** 정렬하는 것이고 `range` 는 여전히 무작위다.

### 10. 파이썬은 **보장**하고, 자바는 **타입으로 고르고**, Go 는 **안 하겠다고 선언**했다

**출력** — 없음(연결 문항).

**왜 그런가**

| 물음 | **파이썬** | **자바** | **Go** |
|---|---|---|---|
| 순회 순서 | **삽입 순서를 언어가 보장** | **구현마다 다르다** | **정하지 않는다** |
| 언제부터 | 3.7 부터 언어 보장(3.6 은 구현 세부) | 처음부터 타입이 갈려 있었다 | 1.0 부터 |
| 순서가 필요하면 | 그냥 `dict` | `LinkedHashMap`·`TreeMap` 을 고른다 | **직접 키를 들고 다닌다** |
| 일부러 섞나 | 아니다 | 아니다 | ★ **그렇다** |
| 그 대신 얻은 것 | 편하다 | 고를 수 있다 | **순서에 기댄 코드가 개발 중에 터진다** |

- ★★ 「순서를 약속하지 않겠다」고 **명시적으로 선언**한 것은 **Go** 다.
  그리고 **선언만 한 것이 아니라 일부러 섞는다** — 사람이 우연히 기대지 못하게 하려는 것이다.
- 파이썬 쪽은 [`../../../python/syntax/12-dict-and-key-requirements/`](../../../python/syntax/12-dict-and-key-requirements/)에 있다.
  자바 쪽은 [`../../../java/syntax/39-collections-framework-map/`](../../../java/syntax/39-collections-framework-map/)다.
- ★ 세 언어가 **같은 자료구조에 다른 계약**을 붙인 것이다 —
  파이썬은 **사용자 편의**를, 자바는 **선택권**을, Go 는 **조용한 실패를 시끄럽게 만드는 것**을 샀다.

### 11. 다른 주제와 잇기

**출력** — 없음(연결 문항).

**왜 그런가**

- **「맵의 제로값이 nil 이다」** — [`../02-variable-declarations-and-zero-values/`](../02-variable-declarations-and-zero-values/).
  **그쪽은 타입별 제로값 표까지**, 여기는 **그 nil 로 무엇이 되고 무엇이 안 되는지**부터다.
- **「비교 가능한 타입」** — 목록의 **17번 주제**(구조체). 키 타입 규칙이 전부 거기에 기댄다.
- **해시 테이블 원리** — [`../../../../../data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/)와
  [`../../../../../data-structure/29-open-addressing/`](../../../../../data-structure/29-open-addressing/).
  **그쪽은 충돌 처리·적재율까지**, 여기는 **Go 가 내주는 표면과 보증**부터다.
- **`maps.Keys`·`slices.Sorted`** — 목록의 **38번 주제**(`slices`·`maps`·`cmp`).
- **여러 고루틴이 같은 맵을 만질 때** — 목록의 **32번 주제**(`sync`)와 **33번 주제**(`sync.Map`).
- **`m[k] = append(m[k], v)`** — [`../07-slice-sharing-silent-bugs/`](../07-slice-sharing-silent-bugs/) (7)절.
  **맵 인덱스 식이 값이라는 사실**은 이 주제 (5)절이 정본이다.

---

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행 1회** | 재실행 결과가 `diff -rq` 로 **동일**(흔들리는 칸 제외) |
| 판 확인 | `go version` · `go env GOOS GOARCH GOVERSION` | 1 | `go1.27.1 linux/amd64` |
| 선언 세 꼴 · nil 맵 읽기 (`t09a`) | `go build && ./prog` | 1 | `var` 만 nil · 읽기 전부 통과 |
| ★ nil 맵 쓰기 (`t09b`) | 〃 | 1 | `panic: assignment to entry in nil map` · **exit 2** |
| comma-ok · `delete` · `clear` (`t09c`) | 〃 | 1 | `0 true` 대 `0 false` · `clear` 뒤 nil 아님 |
| ★★★ 순회 순서 가짓수 (`t09d`) | `./prog 3`·`./prog 8`·`./prog 9` 를 **각 600회** 돌려 `sort -u` | **1800회** | **3 · 8 · 100가지 넘음** |
| 순서 분포 (`t09d`) | `./prog 3` **2000회** + `uniq -c` | **2000회** | 한 가지로 크게 쏠림(1472 대 270 대 258) — **흔들리는 칸** |
| 한 프로세스 안 두 번 순회 (`t09e`) | **600회** + `sort -u` | 600회 | `true` 와 `false` **둘 다** |
| 순회 중 삭제 (`t09f`) | `go build && ./prog` | 1 | 본 항목 **1개** — 흔들리지 않음 |
| ★ 순회 중 추가 (`t09g`) | **600회** + `sort -u` | 600회 | **4 와 5 둘 다** |
| 주소를 못 잡는 것 (`t09h`) | `go build` | 1 | 컴파일 에러 2줄 · exit 1 |
| 키가 되는 타입 (`t09i`) | `go build && ./prog` | 1 | 구조체·배열·인터페이스 키 전부 동작 |
| 키가 안 되는 타입 (`t09j`) | `go build` | 1 | `invalid map key type` **4줄** |
| ★ `any` 키 런타임 패닉 (`t09k`) | `go build && ./prog` | 1 | `hash of unhashable type []int` · **exit 2** |
| `cap` 이 없는 것 (`t09l`) | `go build` | 1 | `invalid argument … for built-in cap` |
| 정렬해 찍기 · `fmt` (`t09m`) | `go build && ./prog` | 1 | 세 방법 모두 `a=1 b=2 c=3` |
| 맵이 포인터 한 칸인 것 (`t09n`) | 〃 | 1 | 넣기는 보이고 재대입은 안 보임 |
| 맵끼리 `==` (`t09o`) | `go build` | 1 | `map can only be compared to nil` |
| 형태 모음 (`t09form`) | `go build && ./prog` | 1 | 위 규칙들이 한 프로그램에서 동작 |

**구현·도구에 달린 항목**(판이 오르면 **다시 찍어야 하는** 것)

| 항목 | 왜 |
|---|---|
| 「3개짜리에서 **3가지**」·「8개짜리에서 **8가지**」 | **gc 의 무작위화 방식**이다. 명세는 가짓수를 말하지 않는다 |
| 9개짜리의 **정확한 가짓수** | 실행마다 흔들린다 — 그래서 **「100가지 넘음」으로만** 실었다 |
| 순서별 **빈도**(1472 대 270 대 258) | 무작위다. 대조할 것은 숫자가 아니라 **쏠린다는 성질**이다 |
| 「작은 맵이 한 묶음이라 회전만 나온다」는 **설명** | **관찰에서 세운 추정이다.** 런타임 소스를 읽어 확인하지 않았다 |
| 패닉 스택의 **주소 오프셋**(`+0xe9` 등) | 빌드마다 바뀔 수 있다 |
| `fmt` 가 정렬해 찍는 것 | **표준 라이브러리의 계약**(1.12부터). 명세가 아니다 |
| 동시 쓰기 시 `fatal error: concurrent map writes` | **안 던져 봤다.** 정본은 목록의 **32번 주제**다 |
| 인터페이스 키의 **비용** | **안 쟀다.** 구체 타입 키보다 비싸다는 것만 적었다 |

★ **다시 찍는 법** — `capture.sh` 를 그대로 돌리고 `diff -rq` 한다.
**흔들리는 칸으로 선언한 블록**(`b09dcount`) 하나만 달라야 하고 나머지는 한 글자도 같아야 한다.

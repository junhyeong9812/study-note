# go/syntax/09 — 맵: 선언·comma-ok·`delete`·순회 순서 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Go 명세](https://go.dev/ref/spec)의 Map types · Index expressions ·
> For statements(RangeClause) · Deletion of map elements 절.\
> 웹이 아니라 **이 툴체인이 들고 있는 ``$(go env GOROOT)/doc/go_spec.html`` 을 열어** 인용했다.
> 그 파일의 머리는 「**Language version go1.27 (May 26, 2026)**」이다.
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> ★★★ **이 주제는 「명세가 무작위를 보장하는」 드문 자리다.** 맵 순회 순서는 구현이 편해서 흔들리는 것이 아니라
> **명세가 「정하지 않는다」고 못 박은 것**이고, 그 위에서 gc 가 **일부러** 섞는다. 그 둘을 (4)절에서 가른다.
> **버전** — 맵의 문법과 보증은 **1.0**부터 같다. `clear`·`maps.Clone`·`maps.Equal` 은 **1.21**,
> `maps.Keys` 가 반복자를 돌려주는 꼴과 `slices.Sorted` 는 **1.23**,
> `fmt` 가 맵을 **키 순서로 정렬해 찍는** 것은 **1.12**부터다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 명세로, 출력은 실행으로 접지했다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | `go_spec.html` 원문 인용 |
| **구현(gc)** | gc 가 그렇게 하는 것 | 순회 순서가 **몇 가지** 나오나 · 그 분포 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 실행 출력 · 컴파일 에러 문장 |

★ 이 주제에서 셋이 가장 헷갈리게 엉킨다. **「순서가 없다」는 명세**이고,
**「몇 가지가 나오나」는 gc 의 사정**이며, **「이번에 abc 가 나왔다」는 한 판의 결과**다.
셋을 섞으면 「세 번 돌려 봤는데 다 같더라」로 끝난다.

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

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | **맵 순회 순서** — 한 판의 출력 | 명세가 정하지 않고 gc 가 일부러 섞는다. **그래서 한 판을 그대로 싣지 않는다** |
| **흔들린다** | 순서별 **빈도**((3)절의 `uniq -c` 수치) | 무작위다. 대조할 것은 숫자가 아니라 **한 가지로 크게 쏠린다**는 성질이다 |
| **흔들린다** | 패닉 스택의 **주소 오프셋**(`+0xe9`) | 같은 바이너리면 같지만 판이 오르면 바뀐다 |
| **판이 바뀌면 바뀐다** | 「3개짜리 맵에서 **3가지**가 나온다」 | gc 의 무작위화 방식이다. **명세는 가짓수를 말하지 않는다** |
| 안 흔들린다 | **몇 가지가 나오나를 전수로 센 값**(600판 `sort -u`) | 같은 판에서는 재현된다 — 그래서 이것을 근거로 쓴다 |
| 안 흔들린다 | 패닉 **메시지 본문**·`파일:줄`·종료 코드 | 명세와 런타임이 정한다 |
| 안 흔들린다 | 컴파일 에러 문장 본문 | 같은 소스·같은 판이면 같다 |
| 안 흔들린다 | `len` · comma-ok 의 `true`/`false` | 명세가 정한다 |
| 안 흔들린다 | `fmt` 가 찍은 맵(`map[a:1 b:2 c:3]`) | **fmt 가 정렬한다**(1.12부터) — `range` 와 다르다 |

## 한눈에 — 쉽게 말하면

**「사물함이 늘어선 복도 하나.」**

맵은 **키를 주면 칸을 찾아 주는 물건**이다. 슬라이스가 「몇 번째」로 찾는다면 맵은 「이름」으로 찾는다.
그런데 사물함에는 **번호 순서가 없다** — 복도를 훑으면 **매번 다른 자리에서 시작한다.**

| 비유 | 실체 |
|---|---|
| 이름표로 찾는 사물함 | `m[key]` |
| 사물함 **동 자체가 아직 안 지어졌다** | `var m map[string]int` — nil 맵 |
| 안 지어진 동에서 **문을 열어 보는 것은 된다**(빈 칸이 나온다) | nil 맵 읽기 → 제로값 |
| 안 지어진 동에 **물건을 넣으려 하면 사고** | nil 맵 쓰기 → 패닉 |
| 「칸이 비었다」와 「그런 이름표가 없다」를 가르는 물음 | comma-ok |
| 복도를 훑을 때마다 **시작 자리가 달라진다** | `range` 무작위화 |
| 칸의 **주소를 적어 갈 수는 없다** | `&m[k]` 는 컴파일 에러 |

- ★ 슬라이스와 달리 맵은 **헤더가 아니라 포인터 하나**다. 그래서 함수에 넘기면 **안의 내용이 공유**되고,
  함수 안에서 **통째로 갈아 끼운 것은 안 보인다**((10)절).
- ★★ 이 주제의 값은 **순회 순서**에 몰려 있다. 그것이 **버그를 만드는 유일한 자리**이기 때문이다.

```text
   m := map[string]int{"a":1, "b":2, "c":3}

   [ a:1 ][ b:2 ][ c:3 ][    ][    ][    ][    ][    ]   <- 칸이 8개인 묶음 하나
      ^                                                    gc 는 시작 칸을 매번 새로 뽑는다

   시작이 0 이면 -> a b c        시작이 5,6,7,0 이어도 -> a b c (빈 칸을 건너뛰어 0 으로 감긴다)
   시작이 1 이면 -> b c a
   시작이 2 이면 -> c a b

   그래서 이 판에서는 3가지만 나오고, abc 가 나머지의 6배쯤 나온다.
   ★ 이 「3가지」는 명세가 아니라 gc 의 사정이다.
```

> **해시 맵(hash map)** — 키를 해시 함수로 숫자로 바꿔 그 숫자로 칸을 고르는 자료구조.\
> 원리는 [`../../../../../data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/)가 정본이다. 여기는 **Go 가 그것을 어떤 표면으로 내주나**만 본다.

> **comma-ok** — `v, ok := m[k]` 꼴. 값과 「있었나」를 한꺼번에 받는 Go 의 관용구.

> **제로값(zero value)** — 선언만 하고 값을 안 넣었을 때 들어 있는 값. `int` 는 0, `string` 은 `""`, 맵·슬라이스·포인터는 `nil`.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **없는 키를 읽으면 왜 제로값이 나오나** — 그리고 「값이 0」과 「키가 없음」을 어떻게 가르나.
2. **순회 순서가 왜 무작위인가** — 명세가 정하지 않은 것과 gc 가 일부러 섞는 것이 어떻게 다른가.
3. **그 순서에 기댄 코드가 어떻게 깨지나** — 테스트가 왜 통과해 버리나.

★ 해시 테이블의 원리(충돌 처리·적재율·개방 주소법)는
[`../../../../../data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/)와
[`../../../../../data-structure/29-open-addressing/`](../../../../../data-structure/29-open-addressing/)가 정본이다.
여기는 **Go 맵의 표면과 보증**만 본다.

## 동작 방식

### (0) 선언 세 꼴 — `var`·`make`·리터럴

**언제 쓰나** — 맵을 만들 때마다. **셋 중 하나만 nil 이 된다.**

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

그림 해설 (한 단계씩):

- **`var m map[string]int` 은 nil 맵**이다. 변수는 만들어졌지만 **맵 자체가 없다.**
- `make` 와 리터럴은 **빈 맵**이다 — `nil` 이 아니고 `len` 이 0이다.
- `make(map[string]int, 100)` 의 100은 **크기 힌트**이지 상한이 아니다.
  명세: "**The initial capacity does not bound its size**".
- ★★ **nil 맵에서 읽는 것은 전부 된다.** 인덱스·comma-ok·`len`·`delete`·`range` 넷 다 그냥 돈다.
  명세: "**A nil map is equivalent to an empty map except that no elements may be added.**"
- 그래서 「초기화를 깜빡했다」가 **읽기만 하는 코드에서는 드러나지 않는다.** 쓰는 순간 터진다((1)절).

```text
   var m map[string]int        m -> nil          읽기 O · 쓰기 X
   m := make(map[string]int)   m -> [       ]    읽기 O · 쓰기 O
   m := map[string]int{}       m -> [       ]    읽기 O · 쓰기 O
```

비용 — `var` 는 할당 0. `make` 와 리터럴은 맵 하나를 잡는다.

### (1) ★★ nil 맵 — 읽기는 되고 쓰기는 패닉

**언제 쓰나** — 구조체 필드로 둔 맵, JSON 에서 언마샬된 맵, 함수가 돌려준 맵을 받을 때.
**초기화를 안 한 맵이 조용히 돌아다니는 자리**가 전부 여기다.

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

그림 해설 (한 단계씩):

- 읽기 두 줄은 **아무 일 없이 지나갔다**(`m == nil : true`, `m["k"]` 가 0).
- `m["k"] = 1` 한 줄에서 **`panic: assignment to entry in nil map`** 이 난다.
- 명세가 이 한 줄로 정한다: "**Assigning to an element of a nil map causes a run-time panic.**"
- 종료 코드는 **2**다. `goroutine 1 [running]:` 아래 `ex/t09b.go:12` 가 **터진 줄**이다.
- ★★ **마커를 표준 오류로 찍었다.** 패닉도 표준 오류이므로, 표준 출력으로 찍으면
  파이프로 받을 때 순서가 뒤집힌다. 이 문서의 모든 패닉 블록이 같은 규칙을 쓴다.
- 고치는 법은 둘이다 — `make` 로 만들거나, **쓰기 전에 `if m == nil { m = map[...]{} }`** 를 둔다.

★★★ **이 비대칭이 이 주제에서 가장 자주 사고를 낸다.** 읽기가 되기 때문에
**테스트가 읽기만 하면 통과**하고, 운영에서 처음 쓰는 순간 죽는다.

비용 — 없다. 패닉은 공짜로 터진다.

### (2) comma-ok — 「0」과 「없음」을 가른다

**언제 쓰나** — 값이 제로값일 수 있는 맵을 읽을 때. **전부**라고 봐도 된다.

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

그림 해설 (한 단계씩):

- `m["b"]` 도 `m["없음"]` 도 **둘 다 0** 이다. 한 값 꼴로는 **원리상 구분이 안 된다.**
- `v, ok := m[k]` 는 **`ok` 를 더 준다.** 명세가 정한 특별한 꼴이다 —
  "**An index expression on a map a … used in an assignment statement or initialization of the special form
  `v, ok = a[x]` … yields an additional untyped boolean value.**"
- ★ 값이 필요 없으면 **`_, ok := m[k]`** 로 존재만 묻는다.
- `delete(m, k)` 는 **없는 키에도 안전**하다. 두 번 지워도 에러가 없다.
- `clear(m)`(**1.21**)은 **전부 지운다.** `m = nil` 과 다르다 — `clear` 뒤에도 **맵은 nil 이 아니다.**

```text
   한 값 꼴   v := m[k]        ->  0        "값이 0" 인지 "없음" 인지 모른다
   comma-ok   v, ok := m[k]    ->  0, true  "있고 값이 0 이다"
                               ->  0, false "없다"
```

비용 — comma-ok 는 **공짜다**(같은 조회 하나다).

### (3) ★★★ 순회 순서 — 명세가 「정하지 않는다」고 못 박은 자리

**언제 쓰나** — `for k := range m` 을 쓸 때마다.

명세 원문이 이 절의 전부다.

> **The iteration order over maps is not specified and is not guaranteed to be the same
> from one iteration to the next.**

★★★ 이것은 「구현이 편한 대로 한다」가 아니라 **「순서를 약속하지 않는다」는 명시적 선언**이다.
그 위에서 **gc 는 일부러 섞는다** — 그래야 사람이 순서에 기대지 못한다.
**둘은 다른 층이고, 다른 방식으로 뒤집힌다.**

키 3개짜리 맵을 **600번 돌려 몇 가지가 나오는지** 세어 보자.

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

그림 해설 (한 단계씩):

- 3개짜리 맵을 **600번** 돌려 나온 순서는 **`abc`·`bca`·`cab` 세 가지**였다.
- ★★ 3개의 순열은 6가지인데 **3가지만 나왔다.** 나온 셋은 전부 **회전**이다 —
  `acb`·`bac`·`cba` 는 600판 중 한 번도 안 나왔다.
- 8개짜리는 **8가지**, 9개짜리는 **100가지를 훌쩍 넘었다**(한 판에서 600회 중 487가지였는데, 이 수치는 흔들린다).
- ★★★ **「3가지뿐이다」를 보장으로 읽으면 안 된다.** 명세는 **가짓수를 한 마디도 말하지 않는다.**
  gc 가 작은 맵을 **한 묶음(group)에 담고 시작 칸만 무작위로 고르기 때문**에 회전만 나오는 것이고,
  9개부터는 묶음이 여럿이라 섞이는 폭이 확 넓어진다. **판이 오르면 이 수치는 바뀔 수 있다.**

분포까지 보면 그 구조가 더 또렷하다.

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
===== 명령: for i in $(seq 1 2000); do ./prog 3; done | sort | uniq -c | sort -rn =====
   1472 abc
    270 cab
    258 bca
(exit 0)
```

- `abc` 가 나머지 둘보다 **다섯 배 넘게** 나왔다. 시작 칸을 8칸 중에서 고르는데
  **채워진 칸이 앞 3개뿐**이라 나머지 5칸이 **전부 `abc` 로 접히기** 때문으로 보인다
  (그렇다면 기대되는 비가 `3 + 5` 대 1 대 1 이다).
- ★ 이 빈도 수치는 **흔들리는 칸**이다. 대조할 것은 숫자가 아니라 **「한쪽으로 쏠린다」는 성질**이다.

한 프로세스 안에서 **두 번 돌면 어떤가.**

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

- **같을 때도 있고 다를 때도 있다** — 600판에서 `true` 와 `false` 가 **둘 다** 나왔다.
- 명세의 뒷문장이 이것이다: "**is not guaranteed to be the same from one iteration to the next**".
  **같은 맵, 같은 프로세스, 연달아 두 번**이라도 보장이 없다.
- ★★★ 이것이 **「세 번 돌려 보니 같더라」가 근거가 못 되는 이유**다. 여러 번 돌려 보는 것보다
  **출력 형식을 결정적으로 바꾸는 쪽**이 싸고 확실하다((8)절).

비용 — 무작위화 자체는 한 번의 난수 뽑기다.

### (4) ★ 순회 중 삭제·추가 — 명세가 각각 다르게 말한다

**언제 쓰나** — 「조건에 맞는 키를 지우면서 돌기」를 할 때. 흔한 모양이다.

명세는 **삭제와 추가를 다르게** 다룬다.

> **If a map entry that has not yet been reached is removed during iteration,
> the corresponding iteration value will not be produced.
> If a map entry is created during iteration, that entry may be produced during the iteration
> or may be skipped. The choice may vary for each entry created and from one iteration to the next.**

삭제 쪽은 **단정**이고, 추가 쪽은 「**나올 수도 안 나올 수도 있다**」이다. 던져 보자.

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

- 8개짜리 맵을 돌면서 **첫 항목 말고 전부 지웠더니 본 항목이 1개**였다.
- 「아직 안 나온 항목을 지우면 나오지 않는다」가 **단정**이므로 이 값은 흔들리지 않는다.
- ★ 그래서 **「돌면서 지우기」는 Go 에서 안전하다.** 자바의 `ConcurrentModificationException` 같은 것이 없다.

추가 쪽은 다르다.

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

- 4개짜리 맵을 돌다가 새 키를 하나 넣었더니, 600판에서 **본 항목 수가 4 와 5 둘 다** 나왔다.
- 명세가 말한 「**may be produced … or may be skipped**」가 **한 프로그램 안에서 실제로 갈린 것**이다.
- ★★ 즉 **「돌면서 넣기」는 결과가 정해지지 않는다.** 넣어야 하면 **키를 먼저 모으고 루프 밖에서** 넣는다.

```text
   지우기 — 아직 안 나온 항목    ->  절대 안 나온다      (명세가 단정)
   지우기 — 이미 나온 항목       ->  이미 나왔다         (당연)
   넣기   — 새 항목             ->  나올 수도 안 나올 수도 (명세가 열어 둠 · 실측으로 둘 다 나옴)
```

비용 — 없음. **정해지지 않은 것이 비용이다.**

### (5) ★ 맵은 주소를 못 잡는다

**언제 쓰나** — `map[string]구조체` 를 쓰고 **필드 하나만 고치려** 할 때.

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

그림 해설 (한 단계씩):

- `&m["a"]` 가 **컴파일 에러**다 — `cannot take address of m["a"] (map index expression of type int)`.
- `s["a"].N = 2` 도 에러다 — `cannot assign to struct field s["a"].N in map`.
- 왜인가 — **맵은 자라면서 항목을 옮긴다.** 주소를 내주면 그 주소가 언제든 낡은 것이 된다.
  그래서 Go 는 **주소를 잡는 일 자체를 문법으로 막는다.**
- ★ 고치는 법 셋. ① 값을 **꺼내 고쳐 다시 넣는다**(`v := m[k]; v.N = 2; m[k] = v`) ·
  ② 값 타입을 **포인터로**(`map[string]*P`) · ③ 맵 대신 슬라이스.
- ★★ 이것은 **슬라이스와 정반대**다. 슬라이스는 `&s[0]` 이 되고 `s[0].N = 2` 도 된다 —
  슬라이스의 원소는 **자리가 안 움직이기** 때문이다(목록의 **05번 주제**).

비용 — 값을 꺼내 다시 넣으면 **구조체 한 벌 복사**가 더 든다.

### (6) 키가 될 수 있는 타입 — 「`==` 가 되는가」 하나다

**언제 쓰나** — 구조체나 인터페이스를 키로 쓰려 할 때.

명세가 한 문장으로 정한다.

> **The comparison operators `==` and `!=` must be fully defined for operands of the key type;
> thus the key type must not be a function, map, or slice.
> If the key type is an interface type, these comparison operators must be defined
> for the dynamic key values; failure will cause a run-time panic.**

되는 것부터 보자.

```text
===== 소스: t09i.go =====
package main

import "fmt"

type Point struct{ X, Y int }

func main() {
	byStruct := map[Point]string{{1, 2}: "구조체 키"}
	byArray := map[[2]int]string{{1, 2}: "배열 키"}
	byIface := map[any]string{}
	byIface[42] = "정수"
	byIface[Point{3, 4}] = "구조체"
	byIface["s"] = "문자열"

	fmt.Println(byStruct[Point{1, 2}])
	fmt.Println(byArray[[2]int{1, 2}])
	fmt.Println(byIface[42], byIface[Point{3, 4}], byIface["s"])
	fmt.Println("키 타입은 == 가 되는 타입이면 된다 — 구조체·배열·인터페이스·포인터·채널 전부")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
구조체 키
배열 키
정수 구조체 문자열
키 타입은 == 가 되는 타입이면 된다 — 구조체·배열·인터페이스·포인터·채널 전부
(exit 0)
```

- **구조체·배열·인터페이스·포인터** 가 전부 키가 된다. 「`==` 가 되면 된다」가 규칙의 전부다.
- 안 되는 것은 컴파일 때 잡힌다.

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

- `[]int`·`func()`·`map[string]int` 는 **`invalid map key type`** 으로 거부된다.
- ★ **슬라이스 필드를 가진 구조체도 거부된다**(`invalid map key type Bad`) —
  구조체의 비교 가능성은 **필드가 전부 비교 가능할 때만** 성립하기 때문이다(목록의 **17번 주제**).

그런데 **인터페이스 키는 컴파일 때 못 잡는다.**

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

- `map[any]string` 에 정수·배열은 들어갔는데 **슬라이스를 넣는 순간 런타임 패닉**이다 —
  `panic: runtime error: hash of unhashable type []int`.
- ★★ 명세가 그렇게 말해 둔 자리다 — "**failure will cause a run-time panic**".
  **키 타입이 `any` 인 맵은 컴파일러의 보호를 잃는다.**

비용 — 인터페이스 키는 **해시할 때 동적 타입을 봐야** 하므로 구체 타입 키보다 비싸다(수치는 안 쟀다).

### (7) `len` 은 되고 `cap` 은 안 된다

**언제 쓰나** — 「맵이 얼마나 잡혀 있나」를 알고 싶을 때. **알 방법이 없다.**

```text
===== 소스: t09l.go =====
package main

import "fmt"

func main() {
	m := make(map[string]int, 100)
	m["a"] = 1
	fmt.Println(len(m), cap(m))
}
===== 명령: go build -trimpath -o prog . =====
# ex
./t09l.go:8:26: invalid argument: m (variable of type map[string]int) for built-in cap
(exit 1)
```

- `cap(m)` 이 **컴파일 에러**다 — `invalid argument: m … for built-in cap`.
- `make(map[string]int, 100)` 으로 100을 줬는데도 **그 100을 되물을 길이 없다.**
- ★ 왜인가 — 맵의 「용량」은 **gc 의 내부 사정**이고 명세가 노출하지 않기로 한 것이다.
  슬라이스는 `cap` 이 **관찰 가능한 계약의 일부**라 정반대다(목록의 **06번 주제**).
- ★★ 그래서 **맵에서는 「재할당이 일어났나」를 밖에서 볼 수 없다.** 슬라이스의 `cap` 추적 같은 진단이 불가능하다.

비용 — 힌트를 주면 초기 재해시가 줄어든다(수치는 안 쟀다).

### (8) ★★ 정렬해서 찍는 법 — 그리고 `fmt` 는 이미 정렬한다

**언제 쓰나** — 맵을 **로그·테스트·문서**에 찍을 때마다.

```text
===== 소스: t09m.go =====
package main

import (
	"fmt"
	"maps"
	"slices"
)

func main() {
	m := map[string]int{"c": 3, "a": 1, "b": 2}

	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	slices.Sort(keys)
	fmt.Print("① 손으로 모아 정렬 : ")
	for _, k := range keys {
		fmt.Printf("%s=%d ", k, m[k])
	}
	fmt.Println()

	fmt.Print("② slices.Sorted(maps.Keys(m)) (1.23) : ")
	for _, k := range slices.Sorted(maps.Keys(m)) {
		fmt.Printf("%s=%d ", k, m[k])
	}
	fmt.Println()

	fmt.Println("③ fmt 는 맵을 키 순서로 정렬해 찍는다 (1.12부터) :", m)
	fmt.Printf("   %%v  : %v\n", m)
	fmt.Printf("   %%+v : %+v\n", m)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
① 손으로 모아 정렬 : a=1 b=2 c=3 
② slices.Sorted(maps.Keys(m)) (1.23) : a=1 b=2 c=3 
③ fmt 는 맵을 키 순서로 정렬해 찍는다 (1.12부터) : map[a:1 b:2 c:3]
   %v  : map[a:1 b:2 c:3]
   %+v : map[a:1 b:2 c:3]
(exit 0)
```

그림 해설 (한 단계씩):

- ① **키를 모아 정렬**하는 것이 기본형이다. `make([]string, 0, len(m))` 으로 미리 잡아 둔다.
- ② **`slices.Sorted(maps.Keys(m))`**(**1.23**)이 그 세 줄을 한 줄로 줄인다.
- ③ ★★★ **`fmt` 는 맵을 키 순서로 정렬해 찍는다**(**1.12**부터). `map[a:1 b:2 c:3]` 이 **재현된다.**
- ★★ 그래서 **「`fmt.Println(m)` 은 실어도 되고 `range` 로 찍은 것은 실으면 안 된다.**
  이 문서가 그 규칙을 지킨 자리가 (0)·(9)절이고, 어긴 것처럼 보이는 자리는 (3)절 하나인데
  **거기서는 흔들림 자체가 주제**라 **몇 가지가 나오는지**만 실었다.
- ★ 주의 — `fmt` 의 정렬은 **출력 형식의 편의**이지 `range` 의 보장이 아니다. **둘은 다른 이야기다.**

비용 — 정렬은 키 개수에 대해 `O(n log n)`. 로그 한 줄에는 싸다.

### (9) 맵은 헤더가 아니라 **포인터 하나**다

**언제 쓰나** — 맵을 함수에 넘길 때. 슬라이스와 **결과가 다르다.**

```text
===== 소스: t09n.go =====
package main

import (
	"fmt"
	"maps"
)

func add(m map[string]int) { m["새"] = 1 }

func reassign(m map[string]int) { m = map[string]int{"딴": 2} }

func main() {
	m := map[string]int{"a": 1}
	add(m)
	fmt.Println("함수 안에서 넣은 것은 보인다   :", m)
	reassign(m)
	fmt.Println("함수 안에서 통째로 바꾼 것은 안 보인다 :", m)

	n := maps.Clone(m) // 1.21
	n["a"] = 99
	fmt.Println("maps.Clone 뒤 원본 :", m, " 사본 :", n)
	fmt.Println("maps.Equal(m, n)   :", maps.Equal(m, n))
	fmt.Println("maps.Equal(m, maps.Clone(m)) :", maps.Equal(m, maps.Clone(m)))

	var nilMap map[string]int
	fmt.Println("nil 맵과 빈 맵은 maps.Equal 로 같다 :", maps.Equal(nilMap, map[string]int{}))
}
===== 명령: go build -trimpath -o prog . && ./prog =====
함수 안에서 넣은 것은 보인다   : map[a:1 새:1]
함수 안에서 통째로 바꾼 것은 안 보인다 : map[a:1 새:1]
maps.Clone 뒤 원본 : map[a:1 새:1]  사본 : map[a:99 새:1]
maps.Equal(m, n)   : false
maps.Equal(m, maps.Clone(m)) : true
nil 맵과 빈 맵은 maps.Equal 로 같다 : true
(exit 0)
```

그림 해설 (한 단계씩):

- 함수 안에서 **넣은 것은 보인다** — 맵 값은 내부 구조체를 가리키는 **포인터**이기 때문이다.
- 함수 안에서 **통째로 갈아 끼운 것은 안 보인다** — 갈아 끼운 것은 **그 포인터의 복사본**이다.
- ★★ 슬라이스와 대비하면 이렇다 — 슬라이스는 **(포인터, len, cap) 세 칸**이라
  **원소 수정은 보이고 `append` 는 안 보인다**(목록의 **05번 주제**).
  맵은 **한 칸**이라 **길이 변화까지 보인다.** 안 보이는 것은 **재대입 하나**다.
- `maps.Clone`(**1.21**)은 **얕은 복사**다 — 값이 슬라이스면 그 슬라이스는 여전히 공유다(목록의 **07번 주제**).
- `maps.Equal` 은 **nil 맵과 빈 맵을 같다고** 본다. `m == nil` 과 `len(m) == 0` 이 **다른 물음**이라는 점에 주의.

비용 — 맵을 넘기는 것은 **포인터 하나**다. 구조체를 넘기는 것보다 싸다.

### (10) 맵끼리는 `==` 가 안 된다

```text
===== 소스: t09o.go =====
package main

import "fmt"

func main() {
	a := map[string]int{"x": 1}
	b := map[string]int{"x": 1}
	fmt.Println(a == b)
}
===== 명령: go build -trimpath -o prog . =====
# ex
./t09o.go:8:14: invalid operation: a == b (map can only be compared to nil)
(exit 1)
```

- `a == b` 가 **컴파일 에러**다 — `map can only be compared to nil`.
- 비교하려면 **`maps.Equal`**(1.21) 또는 `reflect.DeepEqual` 을 쓴다.
- ★ 그래서 **맵 필드를 가진 구조체도 `==` 가 안 된다** — 슬라이스 필드와 같은 이유다(목록의 **17번 주제**).

## 문법 — 형태와 규칙

### 형태 — 맵으로 하는 일 전부

```go
// t09form.go
package main

import (
	"fmt"
	"maps"
	"slices"
)

type Point struct{ X, Y int }

func main() {
	var a map[string]int            // ① nil 맵
	b := make(map[string]int)       // ② 빈 맵
	c := map[string]int{"x": 1}     // ③ 리터럴
	d := make(map[string]int, 8)    // ④ 크기 힌트
	set := map[string]struct{}{}    // ⑤ 집합 관용구
	byPoint := map[Point][]string{} // ⑥ 구조체 키 · 슬라이스 값
	ptr := map[string]*Point{}      // ⑦ 값을 포인터로 — 필드를 고치려면 이것

	b["k"] = 1             // 넣기
	v, ok := b["k"]        // comma-ok
	_, exists := b["없음"]   //
	delete(b, "k")         // 지우기
	set["원소"] = struct{}{} // 집합에 넣기
	_, in := set["원소"]     //
	byPoint[Point{1, 2}] = append(byPoint[Point{1, 2}], "태그")
	ptr["p"] = &Point{3, 4}
	ptr["p"].X = 99 // 포인터 값이면 필드를 고칠 수 있다
	d["z"], d["y"] = 26, 25

	fmt.Println("① a == nil :", a == nil, " len :", len(a), " a[\"없음\"] :", a["없음"])
	fmt.Println("② b :", b, " ③ c :", c)
	fmt.Println("   v, ok :", v, ok, " / 없는 키 :", exists)
	fmt.Println("⑤ set 에 있나 :", in, " 값의 크기는 0바이트다")
	fmt.Println("⑥ byPoint :", byPoint)
	fmt.Println("⑦ ptr[\"p\"] :", *ptr["p"])

	// 찍을 때는 fmt 에 맡기거나 키를 정렬한다
	fmt.Println("fmt 에 맡기면 :", d)
	fmt.Print("키를 정렬하면 : ")
	for _, k := range slices.Sorted(maps.Keys(d)) {
		fmt.Printf("%s=%d ", k, d[k])
	}
	fmt.Println()

	clear(d)
	fmt.Println("clear 뒤 len :", len(d), " nil 인가 :", d == nil)
	fmt.Println("maps.Equal(c, maps.Clone(c)) :", maps.Equal(c, maps.Clone(c)))
}
```

```text
===== 소스: t09form.go =====
package main

import (
	"fmt"
	"maps"
	"slices"
)

type Point struct{ X, Y int }

func main() {
	var a map[string]int            // ① nil 맵
	b := make(map[string]int)       // ② 빈 맵
	c := map[string]int{"x": 1}     // ③ 리터럴
	d := make(map[string]int, 8)    // ④ 크기 힌트
	set := map[string]struct{}{}    // ⑤ 집합 관용구
	byPoint := map[Point][]string{} // ⑥ 구조체 키 · 슬라이스 값
	ptr := map[string]*Point{}      // ⑦ 값을 포인터로 — 필드를 고치려면 이것

	b["k"] = 1             // 넣기
	v, ok := b["k"]        // comma-ok
	_, exists := b["없음"]   //
	delete(b, "k")         // 지우기
	set["원소"] = struct{}{} // 집합에 넣기
	_, in := set["원소"]     //
	byPoint[Point{1, 2}] = append(byPoint[Point{1, 2}], "태그")
	ptr["p"] = &Point{3, 4}
	ptr["p"].X = 99 // 포인터 값이면 필드를 고칠 수 있다
	d["z"], d["y"] = 26, 25

	fmt.Println("① a == nil :", a == nil, " len :", len(a), " a[\"없음\"] :", a["없음"])
	fmt.Println("② b :", b, " ③ c :", c)
	fmt.Println("   v, ok :", v, ok, " / 없는 키 :", exists)
	fmt.Println("⑤ set 에 있나 :", in, " 값의 크기는 0바이트다")
	fmt.Println("⑥ byPoint :", byPoint)
	fmt.Println("⑦ ptr[\"p\"] :", *ptr["p"])

	// 찍을 때는 fmt 에 맡기거나 키를 정렬한다
	fmt.Println("fmt 에 맡기면 :", d)
	fmt.Print("키를 정렬하면 : ")
	for _, k := range slices.Sorted(maps.Keys(d)) {
		fmt.Printf("%s=%d ", k, d[k])
	}
	fmt.Println()

	clear(d)
	fmt.Println("clear 뒤 len :", len(d), " nil 인가 :", d == nil)
	fmt.Println("maps.Equal(c, maps.Clone(c)) :", maps.Equal(c, maps.Clone(c)))
}
===== 명령: go build -trimpath -o prog . && ./prog =====
① a == nil : true  len : 0  a["없음"] : 0
② b : map[]  ③ c : map[x:1]
   v, ok : 1 true  / 없는 키 : false
⑤ set 에 있나 : true  값의 크기는 0바이트다
⑥ byPoint : map[{1 2}:[태그]]
⑦ ptr["p"] : {99 4}
fmt 에 맡기면 : map[y:25 z:26]
키를 정렬하면 : y=25 z=26 
clear 뒤 len : 0  nil 인가 : false
maps.Equal(c, maps.Clone(c)) : true
(exit 0)
```

규칙 불릿.

- **선언은 셋** — `var`(nil) · `make`(빈 맵) · 리터럴(빈 맵 또는 채운 맵).
  **nil 이 되는 것은 `var` 뿐**이다.
- **nil 맵은 읽기 전부 되고 쓰기만 패닉**이다. 그래서 초기화 누락이 **읽는 코드에서는 안 드러난다.**
- **읽을 때는 comma-ok 를 기본형으로** 삼는다. 「값이 제로값」과 「없음」이 갈린다.
- **`delete` 는 없는 키에도 안전**하고, **`clear`(1.21)** 는 전부 지우되 **nil 로 만들지는 않는다.**
- **순회 순서에 기대지 마라.** 찍을 때는 `fmt` 에 맡기거나 **키를 정렬**한다.
- **돌면서 지우는 것은 안전**하고, **돌면서 넣는 것은 정해지지 않았다.**
- **`&m[k]` 도 `m[k].field = v` 도 안 된다.** 값 타입이 구조체면 **꺼내 고쳐 다시 넣거나 포인터로** 담는다.
- **키는 `==` 가 되는 타입만.** `any` 키는 **런타임 패닉**으로 미뤄진다.
- **`cap` 은 없다.** `len` 만 있다.
- **맵끼리 `==` 는 없다.** `maps.Equal` 을 쓴다.

## 어디서 틀리나

### 1. ★★★ 「읽어 보니 잘 되던데」 — nil 맵

- (1)절 실측 — nil 맵에서 **읽기·`len`·`delete`·`range` 가 전부 통과**했다. 쓰기 한 줄에서 죽었다.
- 특히 위험한 모양 — **구조체 필드로 둔 맵**. 생성자를 안 거치면 nil 인 채 돌아다닌다.
- 고치는 법 — 생성자에서 `make` 하거나, **쓰는 함수 첫 줄에 nil 검사**를 둔다.

### 2. ★★★ 「순서가 대체로 같더라」

- (3)절 실측 — 3개짜리 맵 2000판에서 **`abc` 한 가지가 1472판**이었다.
  **세 번 돌려 셋 다 같은 순서가 나오는 일이 예사**라는 뜻이다.
- 게다가 **한 프로세스 안에서 두 번 돌아도** 같을 때가 있다((3)절 뒷부분).
- ★★ 그래서 「여러 번 돌려 봤다」는 약한 근거다. **출력 형식을 결정적으로 바꿔라** — 정렬해 찍는다.
- 고치는 법 — 테스트에서 맵을 비교할 때 **`maps.Equal`** 을, 찍을 때는 **`fmt` 또는 정렬**을 쓴다.

### 3. ★★ 「값이 0 이니까 없는 거네」

- (2)절 실측 — `m["b"]` 와 `m["없음"]` 이 **둘 다 0** 이다.
- 카운터 맵(`map[string]int`)에서 특히 자주 틀린다 — **0회가 「안 센 것」이 아니라 「0이라고 센 것」일 수 있다**.
- 고치는 법 — **comma-ok 를 기본으로** 쓴다. 공짜다.

### 4. ★★ 「구조체를 맵에 담고 필드를 고친다」

- (5)절 실측 — `s["a"].N = 2` 가 **컴파일 에러**다.
- 헷갈리는 이유는 **슬라이스에서는 그게 되기 때문**이다.
- 고치는 법 — `map[K]*V` 로 담거나 **꺼내 고쳐 다시 넣는다.**

### 5. ★★ 「`any` 키는 아무거나 넣어도 되겠지」

- (6)절 실측 — `map[any]string` 에 슬라이스를 넣자 **런타임 패닉**이었다. 컴파일은 통과했다.
- ★ **컴파일러의 보호가 런타임으로 미뤄진 자리**다. JSON 에서 온 값을 키로 쓸 때 실제로 터진다.
- 고치는 법 — 키 타입을 **구체 타입으로** 못 박는다.

### 6. ★ 「돌면서 넣어도 되겠지」

- (4)절 실측 — 600판에서 **4 와 5 가 둘 다** 나왔다. 명세가 열어 둔 자리다.
- 고치는 법 — **키를 먼저 모으고** 루프 밖에서 넣는다. **지우는 것은 그냥 해도 된다.**

### 7. ★ 「`clear(m)` 하면 nil 이 되겠지」

- (2)절 실측 — `clear` 뒤에도 **`m == nil` 은 false** 다. 항목만 비운 것이다.
- 고치는 법 — 진짜 nil 로 만들려면 `m = nil` 이라고 쓴다. 다만 그 뒤로는 **쓰기가 패닉**이다.

### 8. ★ 「`make` 에 준 숫자가 상한이겠지」

- (0)절 — 명세가 "**The initial capacity does not bound its size**" 라고 적는다. 힌트일 뿐이다.
- 게다가 **되물을 수도 없다**((7)절의 `cap` 에러).

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| 순회 순서가 **정해져 있지 않다** | **명세 보장** | "The iteration order over maps is not specified …" |
| **연달아 두 번 돌아도 같다는 보장이 없다** | **명세 보장** | 같은 문장의 뒷부분 |
| nil 맵 **쓰기가 패닉** | **명세 보장** | "Assigning to an element of a nil map causes a run-time panic." |
| nil 맵 **읽기가 된다** | **명세 보장** | "A nil map is equivalent to an empty map except that …" |
| `v, ok := m[k]` 가 **두 값을 준다** | **명세 보장** | Index expressions 의 special form |
| **안 나온 항목을 지우면 안 나온다** | **명세 보장** | "… will not be produced." |
| **넣은 항목이 나올 수도 안 나올 수도** | **명세 보장(열어 둠)** | "may be produced … or may be skipped" |
| 키 타입이 **비교 가능해야 한다** | **명세 보장** | Map types 의 `==`/`!=` 문장 |
| `any` 키에 슬라이스를 넣으면 **런타임 패닉** | **명세 보장** | "failure will cause a run-time panic" |
| `cap` 이 **없다** · `&m[k]` 가 **안 된다** | **명세 보장** | 내장 함수 정의 · 주소 연산자 정의 |
| **3개짜리 맵에서 3가지만 나오는 것** | **구현(gc)** | 작은 맵이 한 묶음이라 **회전만** 나온다 |
| `abc` 가 **6배쯤 나오는 것** | **구현(gc)** | 시작 칸을 빈 칸 포함해 고르고 감긴다 |
| **9개부터 가짓수가 확 넓어지는 것** | **구현(gc)** | 묶음이 여럿이 된다 |
| `fmt` 가 **정렬해 찍는 것** | **표준 라이브러리의 계약** | 1.12 릴리스부터 문서화됨. `range` 와 무관하다 |
| 패닉 스택의 **주소 오프셋** | **구현(gc)** | 빌드마다 바뀔 수 있다 |

★★★ 이 표의 가운데 세 줄이 이 주제의 핵심이다. **「무작위다」는 명세**이고
**「이렇게 무작위다」는 gc**다. 뒤엣것 위에 결론을 세우면 **다음 판에서 조용히 틀린다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 키로 찾는다 | `map[K]V` | 원래 용도 |
| 순서가 필요하다 | **슬라이스 + 정렬** 또는 키 슬라이스를 따로 | 맵에는 순서가 없다 |
| 집합이 필요하다 | `map[K]struct{}` | 값이 0바이트다 |
| 값이 구조체이고 자주 고친다 | `map[K]*V` | `m[k].f = v` 가 안 된다 |
| 없을 수 있는 값을 읽는다 | **comma-ok** | 제로값과 부재가 안 갈린다 |
| 전부 비운다 | `clear(m)`(**1.21**) | nil 로 만들지 않는다 |
| 맵을 찍는다 | `fmt` 에 맡기거나 **키 정렬** | `range` 는 재현이 안 된다 |
| 맵을 비교한다 | `maps.Equal`(**1.21**) | `==` 는 컴파일 에러다 |
| 맵을 베낀다 | `maps.Clone`(**1.21**) | **얕은 복사**임을 알고 쓴다 |
| 돌면서 지운다 | 그냥 지운다 | 명세가 단정한다 |
| 돌면서 넣는다 | **키를 모아 루프 밖에서** | 명세가 열어 뒀다 |
| 여러 고루틴이 만진다 | `sync.Mutex` 또는 `sync.Map` | 맵은 **동시 쓰기에 안전하지 않다**(목록의 **32·33번 주제**) |

판단 규칙 두 줄.

- **「이 맵이 nil 일 수 있나」를 쓰기 전에 물어라.** 읽기만으로는 절대 안 드러난다.
- **「순서가 필요하면 맵이 아니다.」** 필요하면 키를 따로 들고 다닌다.

## 핵심 문장

- ★★★ **맵 순회 순서는 「정하지 않는다」고 명세가 못 박은 것**이고, gc 는 그 위에서 **일부러** 섞는다.
  「무작위다」는 명세, **「몇 가지로 무작위다」는 gc** 다.
- ★★★ **nil 맵은 읽기가 전부 되고 쓰기만 패닉**이다 — `panic: assignment to entry in nil map`.
  그래서 초기화 누락이 **읽는 코드에서는 안 드러난다.**
- ★★ 3개짜리 맵을 **600번 돌렸더니 세 가지**가 나왔고, 2000판 분포에서는 **한 가지가 4분의 3 가까이**를 차지했다.
  **세 번 돌려 보는 것은 근거가 못 된다.**
- ★★ **한 프로세스 안에서 연달아 두 번 돌아도** 같다는 보장이 없다 — 실측에서 `true` 와 `false` 가 둘 다 나왔다.
- **comma-ok 가 「값이 0」과 「없음」을 가르는 유일한 장치**다. 비용은 0이다.
- **돌면서 지우는 것은 안전하고, 돌면서 넣는 것은 정해지지 않았다.** 명세가 두 경우를 다르게 적는다.
- **`&m[k]` 도 `m[k].field = v` 도 안 된다** — 맵이 항목을 옮기기 때문이다. 슬라이스와 정반대다.
- **키는 `==` 가 되는 타입만**이고, `any` 키는 그 검사를 **런타임 패닉으로** 미룬다.
- **`cap` 이 없다.** 맵이 얼마나 잡혀 있는지는 **밖에서 볼 수 없다.**
- **맵은 포인터 한 칸**이다 — 함수 안에서 넣은 것은 보이고 **갈아 끼운 것만** 안 보인다.
- **`fmt` 는 맵을 정렬해 찍는다**(1.12부터). 그것이 `range` 의 보장은 **아니다.**

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 09번)
- [`../02-variable-declarations-and-zero-values/`](../02-variable-declarations-and-zero-values/)(변수 선언과 제로값) —
  ★ **직접 선행**. **그쪽은 「맵의 제로값이 nil 이다」까지**, 여기는 **그 nil 로 무엇이 되고 무엇이 안 되는지**부터
- [`../05-arrays-vs-slices-value-and-header/`](../05-arrays-vs-slices-value-and-header/)(배열과 슬라이스) —
  **그쪽은 헤더 세 칸**, 여기는 **포인터 한 칸**. (9)절의 대비가 거기서 온다
- [`../06-len-cap-and-append-reallocation/`](../06-len-cap-and-append-reallocation/)(`len`/`cap`) —
  **그쪽은 `cap` 이 관찰 가능한 계약**, 여기는 **맵에는 `cap` 이 아예 없다**는 대비
- [`../07-slice-sharing-silent-bugs/`](../07-slice-sharing-silent-bugs/)(슬라이스 공유) —
  (7)절의 `m[k] = append(m[k], v)` 가 거기 있다. 여기는 **맵 인덱스 식이 값이라는 사실**이 정본
- [`../10-strings-bytes-runes-and-utf8-iteration/`](../10-strings-bytes-runes-and-utf8-iteration/)(문자열과 UTF-8) —
  같은 `range` 문의 **다른 대상**. 명세의 같은 절이 둘을 나란히 규정한다
- [`../../../../../data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) ·
  [`../../../../../data-structure/29-open-addressing/`](../../../../../data-structure/29-open-addressing/) —
  ★ **해시 테이블 원리의 정본**. **그쪽은 충돌 처리·적재율·개방 주소법까지**,
  여기는 **Go 가 그것을 어떤 표면과 보증으로 내주나**부터
- [`../../../python/syntax/12-dict-and-key-requirements/`](../../../python/syntax/12-dict-and-key-requirements/) —
  ★ **가장 날카로운 대비**. 파이썬 `dict` 는 **삽입 순서를 언어가 보장**한다(3.7+).
  Go 는 정반대로 **보장하지 않겠다고 선언**했다. 같은 자료구조, 반대 선택이다
- [`../../../java/syntax/39-collections-framework-map/`](../../../java/syntax/39-collections-framework-map/) —
  자바는 **구현마다 다르다**(`HashMap` 은 순서 없음, `LinkedHashMap` 은 삽입 순서, `TreeMap` 은 키 순서).
  **타입으로 고르는 쪽**이다
- 목록의 **17번 주제**(구조체) — 「비교 가능한 타입」의 정본. 키 타입 규칙이 거기에 기댄다
- 목록의 **32번 주제**(`sync`) · **33번 주제**(`sync.Map`) — 여러 고루틴이 만질 때. **맵은 동시 쓰기에 안전하지 않다**
- 목록의 **38번 주제**(`slices`·`maps`·`cmp`) — `maps.Keys`·`maps.Clone`·`slices.Sorted` 의 정본
- 목록의 **42번 주제**(`fmt`) — `fmt` 가 맵을 정렬해 찍는 것의 정본
- 목록의 **49번 주제**(`testing`) — 순서 없는 것을 테스트로 고정하는 법

## 용어 풀이

- **맵(map)** — 키로 값을 찾는 Go 의 내장 자료구조. 해시 테이블이다.
- **nil 맵** — 만들어지지 않은 맵. 읽기는 되고 **쓰기만 패닉**이다.
- **comma-ok** — `v, ok := m[k]`. 값과 존재 여부를 한 번에 받는 꼴.
- **제로값(zero value)** — 값을 안 넣었을 때 들어 있는 값. 맵이 없는 키에 대해 주는 것이 이것이다.
- **순회 무작위화(iteration randomization)** — `range` 의 시작점을 매번 새로 뽑는 것. gc 가 **일부러** 한다.
- **비교 가능(comparable)** — `==` 와 `!=` 가 정의된 타입. 맵 키의 유일한 조건이다.
- **해시 불가(unhashable)** — 해시할 수 없는 값. Go 에서는 「비교 불가」와 같은 말이다.
- **얕은 복사(shallow copy)** — 한 겹만 베끼는 것. `maps.Clone` 이 그렇다.

---

## 더 들어가면

- **왜 일부러 섞나** — 섞지 않으면 사람이 순서에 기대는 코드를 쓰고,
  그 코드가 **판이 오르거나 데이터가 바뀌면 조용히 깨진다.**
  Go 팀은 그 사고를 **매 실행마다 터뜨려서** 개발 단계에서 잡게 했다.
  ★ 이것은 **「예측 가능성을 포기해 예측 가능성을 얻는」** 설계다 — 조용한 실패를 시끄러운 실패로 바꾼 것이다.
  총론은 [`../../../../../ops-patterns/failure-modes/`](../../../../../ops-patterns/failure-modes/)가 정본이다.
- **그래도 예외가 하나 있다** — `fmt` 다. 표준 라이브러리는 **찍을 때만** 정렬해 준다.
  「디버깅 출력이 흔들리면 못 쓴다」는 현실과 「순서를 약속하면 안 된다」는 원칙을
  **찍는 자리에서만 타협**한 것이다.
- **`sync.Map` 의 `Range` 도 순서가 없다.** 게다가 **한 시점의 스냅숏도 아니다.** 정본은 목록의 **33번 주제**다.
- **여러 고루틴이 같은 맵에 쓰면 런타임이 잡아 준다** — `fatal error: concurrent map writes` 가 뜨고
  **이것은 패닉이 아니라 치명적 오류라 `recover` 로 못 잡는다.**
  다만 **이 문서에서는 안 던져 봤다** — 정본은 목록의 **32번 주제**다.
- **맵의 내부 구조는 1.24 에서 바뀌었다**(버킷 기반에서 이른바 Swiss table 로).
  이 문서의 (3)절 수치 — 작은 맵이 **회전만** 나오는 것 — 은 그 구조의 결과로 보이지만,
  **이 문서는 런타임 소스를 읽어 확인하지 않았다.** 관찰로만 적는다.
- **삽입 순서를 지키는 맵이 필요하면** Go 표준에는 없다. 키 슬라이스를 따로 들거나
  `container/list` 와 맵을 엮는다. 「없는 것도 설계다」에 해당하는 자리다.

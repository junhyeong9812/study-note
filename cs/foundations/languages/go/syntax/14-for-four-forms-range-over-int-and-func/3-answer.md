# go/syntax/14 — `for` 의 네 형태 · 정수 range(1.22) · 함수 range(1.23) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> 블록은 전부 `===== 소스: … =====` 로 소스를 먼저 싣는다 — **그대로 다시 던질 수 있게** 하기 위해서다.
> ★★ **언어 판이 걸린 블록은 `go.mod` 도 소스로 싣는다.** 이 주제는 그 파일이 곧 입력이다.
> ★ **근거로 읽을 칸** — 반복 횟수, 값, 에러 문장 본문과 `파일:줄:칸`, 종료 코드, `len`·`cap`.
> **근거로 읽지 않을 칸** — **맵 순회 순서**(그래서 정렬해서 찍거나 개수만 센다).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 네 꼴이 전부 `for` 한 낱말이다 — 마지막 줄은 `break` 가 일찍 걸린다

**출력**

```text
===== 소스: t14a.go =====
package main

import "fmt"

func main() {
	fmt.Print("① 3절  : ")
	for i := 0; i < 3; i++ {
		fmt.Print(i, " ")
	}
	fmt.Println()

	fmt.Print("② 조건만: ")
	n := 0
	for n < 3 {
		fmt.Print(n, " ")
		n++
	}
	fmt.Println()

	fmt.Print("③ 무한  : ")
	k := 0
	for {
		if k == 3 {
			break
		}
		fmt.Print(k, " ")
		k++
	}
	fmt.Println()

	fmt.Print("④ range : ")
	for i, v := range []string{"가", "나", "다"} {
		fmt.Print(i, v, " ")
	}
	fmt.Println()

	// 세 절이 전부 비면 ③ 이다 — 아래 둘은 같은 문이다.
	fmt.Print("③ 의 다른 꼴 : ")
	m := 0
	for ; ; m++ {
		if m == 2 {
			break
		}
		fmt.Print(m, " ")
	}
	fmt.Println()
}
===== 명령: go build -trimpath -o prog . && ./prog =====
① 3절  : 0 1 2 
② 조건만: 0 1 2 
③ 무한  : 0 1 2 
④ range : 0가 1나 2다 
③ 의 다른 꼴 : 0 1 
(exit 0)
```

**왜 그런가**

- ①은 C 의 3절 꼴이다. **괄호가 없다.**
- ②는 다른 언어의 **`while`** 이고 ③은 **무한 루프**다. Go 에 그 키워드는 **없다.**
  명세가 동치를 직접 적는다.

  > **`for cond { S() }` is the same as `for ; cond ; { S() }`**\
  > **`for { S() }` is the same as `for true { S() }`**

- ④가 `range` 절이다.
- 마지막 줄 `for ; ; m++` 은 **조건이 비었으니 무한 루프**다. `m == 2` 에서 `break` 하므로 `0 1` 만 찍힌다.
  ★ 앞의 ③은 `k == 3` 에서 끊어 `0 1 2` 였다 — **끊는 자리만 다르다.**
- 층 — **1.0부터의 명세 보장**이다.

### 2. ★★ 배열만 `1 2 3 4` 다 — 나머지 셋은 수정이 보인다

**출력**

```text
===== 소스: t14b.go =====
package main

import "fmt"

func main() {
	fmt.Println("── ① 배열 range — range 식이 복사된다 ──")
	arr := [4]int{1, 2, 3, 4}
	for i, v := range arr {
		if i == 0 {
			arr[1] = 99 // 원본을 민다
		}
		fmt.Print(v, " ")
	}
	fmt.Println("  루프 뒤 arr =", arr)

	fmt.Println("── ② 슬라이스 range — 헤더만 복사되고 칸은 공유다 ──")
	sl := []int{1, 2, 3, 4}
	for i, v := range sl {
		if i == 0 {
			sl[1] = 99
		}
		fmt.Print(v, " ")
	}
	fmt.Println("  루프 뒤 sl =", sl)

	fmt.Println("── ③ 배열 포인터 range — 복사가 안 생긴다 ──")
	ap := [4]int{1, 2, 3, 4}
	for i, v := range &ap {
		if i == 0 {
			ap[1] = 99
		}
		fmt.Print(v, " ")
	}
	fmt.Println("  루프 뒤 ap =", ap)

	fmt.Println("── ④ 슬라이스의 원소가 구조체면 v 는 복사본이다 ──")
	type item struct{ N int }
	items := []item{{1}, {2}}
	for _, it := range items {
		it.N = 99
	}
	fmt.Println("  v 를 고친 뒤 items =", items)
	for i := range items {
		items[i].N = 99
	}
	fmt.Println("  items[i] 를 고친 뒤 items =", items)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
── ① 배열 range — range 식이 복사된다 ──
1 2 3 4   루프 뒤 arr = [1 99 3 4]
── ② 슬라이스 range — 헤더만 복사되고 칸은 공유다 ──
1 99 3 4   루프 뒤 sl = [1 99 3 4]
── ③ 배열 포인터 range — 복사가 안 생긴다 ──
1 99 3 4   루프 뒤 ap = [1 99 3 4]
── ④ 슬라이스의 원소가 구조체면 v 는 복사본이다 ──
  v 를 고친 뒤 items = [{1} {2}]
  items[i] 를 고친 뒤 items = [{99} {99}]
(exit 0)
```

**왜 그런가**

| 덩어리 | `v` 줄 | 왜 |
|---|---|---|
| ① 배열 | **`1 2 3 4`** | `range` 가 **배열을 통째로 복사**해 두고 돈다. 원본을 밀어도 복사본은 그대로다 |
| ② 슬라이스 | **`1 99 3 4`** | **헤더만 복사**됐고 기반 배열은 하나다 — `v` 는 그 배열에서 읽는다 |
| ③ 배열 포인터 | **`1 99 3 4`** | 포인터를 복사해도 가리키는 배열은 하나다 |
| ④ 구조체 원소 | `[{1} {2}]` → `[{99} {99}]` | `v` 는 **원소의 복사본**이다. `items[i]` 를 직접 고쳐야 남는다 |

- ★★ 넷을 한 낱말로 묶으면 **「짐칸인가 쪽지인가」** 다
  ([05번 주제](../05-arrays-vs-slices-value-and-header/)의 비유).
  `range` 는 언제나 피연산자를 **값으로 한 번** 든다 — 그 값이 짐칸이면 짐칸째 복사되고,
  쪽지면 쪽지만 복사되어 짐칸은 하나로 남는다.
- ③이 큰 배열의 복사를 피하는 관용구다. `for i, v := range &arr`.
- ④를 고치는 법은 **`for i := range items { items[i].N = 99 }`** 다 — 마지막 두 줄이 그것을 보인다.
- 층 — 전부 **1.0부터의 명세 보장**이다. 복사 여부가 타입에서 결정되기 때문이다.

### 3. 3회 · 4회 · 본 키 1개

**출력**

```text
===== 소스: t14c.go =====
package main

import (
	"fmt"
	"sort"
)

func main() {
	fmt.Println("── ① range 는 시작할 때 길이를 정한다 ──")
	s := []int{1, 2, 3}
	n := 0
	for range s {
		s = append(s, 9)
		n++
		if n > 10 { // 안전장치 — 안 늘면 여기 안 걸린다
			break
		}
	}
	fmt.Println("  반복 횟수 =", n, " · 루프 뒤 len(s) =", len(s))

	fmt.Println("── ② 슬라이스를 줄여도 이미 정해진 횟수만큼 돈다 ──")
	t := []int{1, 2, 3, 4}
	m := 0
	for range t {
		t = t[:1]
		m++
	}
	fmt.Println("  반복 횟수 =", m, " · 루프 뒤 len(t) =", len(t))

	fmt.Println("── ③ 맵에서 도중에 지운 키는 안 나온다 ──")
	mp := map[string]int{"a": 1, "b": 2, "c": 3, "d": 4}
	var got []string
	for k := range mp {
		if len(got) == 0 {
			// 첫 회차에 자기 자신 말고 전부 지운다
			for kk := range mp {
				if kk != k {
					delete(mp, kk)
				}
			}
		}
		got = append(got, k)
	}
	sort.Strings(got)
	fmt.Println("  본 키의 개수 =", len(got), " · 남은 키 개수 =", len(mp))
}
===== 명령: go build -trimpath -o prog . && ./prog =====
── ① range 는 시작할 때 길이를 정한다 ──
  반복 횟수 = 3  · 루프 뒤 len(s) = 6
── ② 슬라이스를 줄여도 이미 정해진 횟수만큼 돈다 ──
  반복 횟수 = 4  · 루프 뒤 len(t) = 1
── ③ 맵에서 도중에 지운 키는 안 나온다 ──
  본 키의 개수 = 1  · 남은 키 개수 = 1
(exit 0)
```

**왜 그런가**

- ① 루프 안에서 `append` 를 했는데 **3회로 끝난다.** 루프 뒤 `len` 은 6이다.
  ★ 안전장치 `n > 10` 이 **안 걸렸다** — 만약 `range` 가 커지는 슬라이스를 따라갔다면 걸렸을 것이다.
  「안 걸린 것」이 곧 근거다.
- ② 반대로 **줄여도** 이미 정해진 **4회**를 돈다. 루프 뒤 `len(t)` 는 1이다.
- ★★ 이유는 2번과 같다 — `range sl` 이 든 것은 **그 시점의 헤더**다.
  `sl` 변수가 나중에 다른 헤더를 가리켜도 루프가 든 헤더는 안 바뀐다.
- ③ 첫 회차에 나머지 세 키를 지우니 **본 키가 1개**다. 명세가 보장한다.

  > If a map entry that has not yet been reached is removed during iteration,
  > **the corresponding iteration value will not be produced.**

  ★ 그 짝인 「추가」는 **보장이 아니다** — "may be produced during the iteration or may be skipped".
  그래서 이 문서는 **추가 쪽을 안 던졌다.** 던져도 그 판의 관찰일 뿐이다.
- ③이 순서를 안 찍은 이유 — **맵 순회 순서는 보장이 없다**("not specified").
  본 키를 모아 **정렬한 뒤 개수만** 찍었다. 흔들리는 칸을 근거로 쓰지 않기 위해서다(09번 주제).

### 4. `0 1 2 3 4` · 세 번 · 0회 · 0회 · `uint8`

**출력**

```text
===== 소스: t14d.go =====
package main

import "fmt"

func main() {
	fmt.Print("for i := range 5   : ")
	for i := range 5 {
		fmt.Print(i, " ")
	}
	fmt.Println()

	fmt.Print("for range 3        : ")
	for range 3 {
		fmt.Print("* ")
	}
	fmt.Println()

	fmt.Print("for i := range 0   : ")
	for i := range 0 {
		fmt.Print(i, " ")
	}
	fmt.Println("(한 번도 안 돈다)")

	fmt.Print("for i := range -1  : ")
	for i := range -1 {
		fmt.Print(i, " ")
	}
	fmt.Println("(음수도 0회다)")

	var n uint8 = 3
	fmt.Print("타입이 있는 값     : ")
	for i := range n {
		fmt.Printf("%d(%T) ", i, i)
	}
	fmt.Println(" <- i 의 타입은 range 식의 타입이다")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
for i := range 5   : 0 1 2 3 4 
for range 3        : * * * 
for i := range 0   : (한 번도 안 돈다)
for i := range -1  : (음수도 0회다)
타입이 있는 값     : 0(uint8) 1(uint8) 2(uint8)  <- i 의 타입은 range 식의 타입이다
(exit 0)
```

**왜 그런가**

- `for i := range 5` 가 **0부터 4까지**를 준다. `for range 3` 은 변수 없이 세 번 돈다.
- **`range 0` 도 `range -1` 도 0회**다. 명세:

  > For an integer value n … the iteration values **0 through n-1** are produced in increasing order. …
  > **If n <= 0, the loop does not run any iterations.**

- 마지막 줄의 `i` 는 **`uint8`** 이다. `range` 식이 `uint8` 값이기 때문이다.

  > If n is of integer type, **the iteration values have that same type.**
  > Otherwise, the type of n is determined as if it were assigned to the iteration variable.

  ★ 상수 `5` 를 주면 기본 타입인 `int` 가 된다.
- `go 1.21` 로 던지면 **컴파일 에러**다.

```text
===== 소스: t14e.go =====
package main

import "fmt"

func main() {
	for i := range 5 {
		fmt.Println(i)
	}
}
===== 소스: go.mod =====
module ex

go 1.21
===== 명령: go build -trimpath -o prog . =====
# ex
./t14e.go:6:17: cannot range over 5 (untyped int constant): requires go1.22 or later (-lang was set to go1.21; check go.mod)
(exit 1)
```

  메시지 전문 — `cannot range over 5 (untyped int constant): requires go1.22 or later
  (-lang was set to go1.21; check go.mod)` · 종료 코드 **1**.
- `go 1.22` 로 올리면 그대로 돈다.

```text
===== 소스: go.mod =====
module ex

go 1.22
===== 명령: go build -trimpath -o prog . && ./prog =====
0
1
2
3
4
(exit 0)
```

- 층 — **1.22부터의 보장**이다. 그 사실을 문서가 아니라 **컴파일러가 말해 줬다.**

### 5. ★★★ `break` 하는 순간 `yield` 가 `false` 를 돌려주고 `2` 는 만들어지지 않는다

**출력**

```text
===== 소스: t14f.go =====
package main

import "fmt"

// upto 는 0 부터 n-1 까지를 내놓는 반복자 함수다.
// 시그니처가 func(func(int) bool) 이면 range 가 받아 준다(1.23부터).
func upto(n int) func(func(int) bool) {
	return func(yield func(int) bool) {
		for i := 0; i < n; i++ {
			fmt.Printf("  [생산자] %d 을 yield 한다\n", i)
			if !yield(i) {
				fmt.Println("  [생산자] yield 가 false — 되돌아간다")
				return
			}
			fmt.Println("  [생산자] yield 가 true — 계속한다")
		}
		fmt.Println("  [생산자] 다 내놓았다")
	}
}

func main() {
	fmt.Println("── ① 끝까지 도는 경우 ──")
	for v := range upto(3) {
		fmt.Println("[소비자] 받았다:", v)
	}

	fmt.Println("── ② break 로 끊는 경우 ──")
	for v := range upto(3) {
		fmt.Println("[소비자] 받았다:", v)
		if v == 1 {
			fmt.Println("[소비자] break")
			break
		}
	}

	fmt.Println("── ③ return 으로 끊어도 같다 ──")
	func() {
		for v := range upto(3) {
			fmt.Println("[소비자] 받았다:", v)
			if v == 0 {
				fmt.Println("[소비자] return")
				return
			}
		}
	}()
}
===== 명령: go build -trimpath -o prog . && ./prog =====
── ① 끝까지 도는 경우 ──
  [생산자] 0 을 yield 한다
[소비자] 받았다: 0
  [생산자] yield 가 true — 계속한다
  [생산자] 1 을 yield 한다
[소비자] 받았다: 1
  [생산자] yield 가 true — 계속한다
  [생산자] 2 을 yield 한다
[소비자] 받았다: 2
  [생산자] yield 가 true — 계속한다
  [생산자] 다 내놓았다
── ② break 로 끊는 경우 ──
  [생산자] 0 을 yield 한다
[소비자] 받았다: 0
  [생산자] yield 가 true — 계속한다
  [생산자] 1 을 yield 한다
[소비자] 받았다: 1
[소비자] break
  [생산자] yield 가 false — 되돌아간다
── ③ return 으로 끊어도 같다 ──
  [생산자] 0 을 yield 한다
[소비자] 받았다: 0
[소비자] return
  [생산자] yield 가 false — 되돌아간다
(exit 0)
```

**왜 그런가**

- ① **끝까지 도는 경우** — 생산자가 `yield(i)` 를 부르면 **루프 몸통이 돌고**,
  `yield` 가 **`true`** 를 돌려주고, 생산자가 계속한다. 다 내놓으면 `다 내놓았다` 를 찍고 끝난다.
  출력은 **10줄**이다(생산자 7 + 소비자 3).
- ② ★★★ **`break` 하는 경우** — 소비자가 `1` 을 받고 `break` 하자
  **`[생산자] yield 가 false — 되돌아간다`** 가 찍힌다.
  그리고 **`2` 는 아예 만들어지지 않는다** — `0 을 yield 한다`·`1 을 yield 한다` 까지만 있다.
- ③ `return` 으로 끊어도 **같다.** 몸통을 끝내는 모든 방법이 `yield` 를 `false` 로 만든다.
- 명세가 그 계약을 적는다.

  > For a function f, the iteration proceeds by **calling f with a new, synthesized yield function
  > as its argument**. … After each successive loop iteration, **yield returns true** …
  > **If the loop body terminates (such as by a break statement), yield returns false
  > and must not be called again.**

- ★★ 그러니 `yield` 의 반환값을 무시하는 반복자는 **「must not be called again」을 어긴 것**이다.
  계약을 지킬 의무가 **반복자를 만드는 쪽**에 있다는 점이 중요하다.
  `if !yield(v) { return }` 이 그 한 줄이다.
- ★ 이 출력이 안 흔들리는 이유 — 고루틴이 없다. **같은 고루틴 위의 보통 함수 호출**이 왔다 갔다 할 뿐이다.

### 6. 3줄 · `1 2 3` · 정렬해서 셋 · 1개짜리는 피연산자마다 다르다

**출력**

```text
===== 소스: t14h.go =====
package main

import (
	"fmt"
	"sort"
)

func main() {
	fmt.Println("── 문자열 range 는 바이트가 아니라 룬이다 ──")
	s := "가nb"
	for i, r := range s {
		fmt.Printf("  i=%d r=%q r=%d(%T)\n", i, r, r, r)
	}
	fmt.Println("  len(s) =", len(s), " — 바이트 수다")

	fmt.Println("── 채널 range 는 닫힐 때까지 돈다 ──")
	ch := make(chan int, 3)
	ch <- 1
	ch <- 2
	ch <- 3
	close(ch)
	for v := range ch {
		fmt.Print(v, " ")
	}
	fmt.Println(" <- close 가 없으면 여기서 영원히 막힌다")

	fmt.Println("── 맵 range 는 키와 값 둘이다(순서는 정렬해서 찍는다) ──")
	m := map[string]int{"가": 1, "나": 2, "다": 3}
	var keys []string
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	for _, k := range keys {
		fmt.Printf("  %s=%d", k, m[k])
	}
	fmt.Println()

	fmt.Println("── 변수를 몇 개 받느냐는 골라도 된다 ──")
	sl := []string{"x", "y"}
	for range sl {
		fmt.Print("0개 ")
	}
	for i := range sl {
		fmt.Print("1개:", i, " ")
	}
	for i, v := range sl {
		fmt.Print("2개:", i, v, " ")
	}
	fmt.Println()
}
===== 명령: go build -trimpath -o prog . && ./prog =====
── 문자열 range 는 바이트가 아니라 룬이다 ──
  i=0 r='가' r=44032(int32)
  i=3 r='n' r=110(int32)
  i=4 r='b' r=98(int32)
  len(s) = 5  — 바이트 수다
── 채널 range 는 닫힐 때까지 돈다 ──
1 2 3  <- close 가 없으면 여기서 영원히 막힌다
── 맵 range 는 키와 값 둘이다(순서는 정렬해서 찍는다) ──
  가=1  나=2  다=3
── 변수를 몇 개 받느냐는 골라도 된다 ──
0개 0개 1개:0 1개:1 2개:0x 2개:1y 
(exit 0)
```

**왜 그런가**

- **문자열** — 회차는 **3번**인데 `len(s)` 는 **5**다. 인덱스가 `0 → 3 → 4` 로 뛴다.
  `'가'` 가 UTF-8 로 **3바이트**이기 때문이다. `r` 의 타입은 `int32`(`rune` 의 바닥 타입)다.
  정본은 [10번 주제](../10-strings-bytes-runes-and-utf8-iteration/)다.
- **채널** — `1 2 3` 을 받고 끝난다. **`close` 를 지우면 영원히 막힌다** —
  비었다고 끝나는 것이 아니라 **닫힐 때까지** 받기 때문이다. 정본은 [목록의 **29번 주제**](../29-channels-buffering-direction-close-range-and-nil/)다.
- **맵** — 키를 모아 **정렬한 뒤** 찍었다. 순서가 보장이 아니라서다.
- **변수 개수** — 0·1·2개 중 고른다. 1개만 받았을 때 주는 것이 피연산자마다 다르다.

| 피연산자 | 1개만 받으면 | 2개 받으면 |
|---|---|---|
| 슬라이스·배열·문자열 | **인덱스** | 인덱스, 값 |
| 맵 | **키** | 키, 값 |
| 채널 | **받은 값** | (2개는 없다) |
| 정수 | **반복값** | (2개는 없다) |
| 함수(`Seq`) | **값** | `Seq2` 면 둘 |

- ★ **같은 문법이 피연산자에 따라 다른 것을 준다** — 채널에서 1개가 인덱스가 아니라 값인 것이 함정이다.

### 7. 1.22 와 1.23 — 그리고 둘 다 `go.mod` 를 가리킨다

**출력**

```text
===== 소스: t14g.go =====
package main

import "fmt"

func seq(yield func(int) bool) {
	for i := 0; i < 3; i++ {
		if !yield(i) {
			return
		}
	}
}

func main() {
	for v := range seq {
		fmt.Println(v)
	}
}
===== 소스: go.mod =====
module ex

go 1.22
===== 명령: go build -trimpath -o prog . =====
# ex
./t14g.go:14:17: cannot range over seq (value of type func(yield func(int) bool)): requires go1.23 or later (-lang was set to go1.22; check go.mod)
(exit 1)
```

```text
===== 소스: go.mod =====
module ex

go 1.23
===== 명령: go build -trimpath -o prog . && ./prog =====
0
1
2
(exit 0)
```

**왜 그런가**

- 정수 `range` 는 **1.22**, 함수 `range` 는 **1.23**부터다. 4번과 이 블록의 에러가 그 경계다.
- 두 메시지가 공통으로 가리키는 파일은 **`go.mod`** 다 —
  `-lang was set to go1.21; check go.mod` · `-lang was set to go1.22; check go.mod`.
- ★★ 이 메시지는 **「파서가 이 문법을 모른다」가 아니다.**
  파서는 `range 5` 도 `range seq` 도 완벽히 읽었다 — 타입까지 다 말한다
  (`value of type func(yield func(int) bool)`).
  **막고 있는 것은 언어 판**이고, 그래서 `go.mod` 한 줄로 풀린다.
- ★ 이것이 SQL 갈래에서 「`ERROR 1064`(낱말을 모른다)」와
  「`doesn't yet support`(아는데 경로가 없다)」를 갈랐던 것과 같은 구분이다.
  **뒤쪽은 정보가 훨씬 많다** — 어디를 고치면 되는지까지 알려 준다.
- 층 — **1.22 / 1.23부터의 보장**이고, 에러 문구 자체는 **툴체인(구현)** 의 것이다.

### 8. `range` 는 한 번만 평가하고, 그 값이 무엇이냐가 전부다

**출력** — 없음(왜 문항). 근거는 2번·3번의 출력이다.

**왜 그런가**

- `range` 는 피연산자를 **시작 전에 한 번** 평가한다. 회차마다 다시 읽지 않는다.
  3번 ①의 「안전장치가 안 걸렸다」가 그 증거다.
- 복사되는 것 —

```text
   배열 [N]T        원소 N개가 통째로            -> 루프 중 수정이 v 에 안 보인다
   슬라이스 []T     헤더 세 칸만(ptr·len·cap)    -> 기반 배열은 하나 -> 보인다
   *[N]T            포인터 한 칸                 -> 배열은 하나 -> 보인다
   맵·채널          안에 든 참조                 -> 보인다
```

- 배열 복사를 피하는 문법은 **`range &arr`** 이다. 피연산자가 포인터가 되어 한 칸만 복사된다.
- 원소를 고치려면 **`for i := range s` 뒤 `s[i]`** 를 쓴다.
  `v` 로는 안 되는 이유는 **`v` 가 대입으로 만들어진 복사본**이기 때문이다 —
  슬라이스라도 **원소는 값으로 복사된다.** 2번 ④가 그 실측이다.
- ★ 「슬라이스니까 공유」가 아니라 **「슬라이스의 배열이 공유」** 다. 그 한 칸 차이가 ②와 ④를 가른다.

### 9. `iter.Seq[int]` 는 `func(func(int) bool)` 의 이름이다

**출력**

```text
===== 소스: t14i.go =====
package main

import (
	"fmt"
	"iter"
	"maps"
	"slices"
)

// evens 는 iter.Seq[int] 를 돌려준다 — func(func(int) bool) 의 별칭이다.
func evens(limit int) iter.Seq[int] {
	return func(yield func(int) bool) {
		for i := 0; i < limit; i += 2 {
			if !yield(i) {
				return
			}
		}
	}
}

// pairs 는 iter.Seq2[string, int] 다 — 두 값을 내놓는다.
func pairs() iter.Seq2[string, int] {
	return func(yield func(string, int) bool) {
		for i, s := range []string{"가", "나", "다"} {
			if !yield(s, i) {
				return
			}
		}
	}
}

func main() {
	fmt.Printf("evens 의 타입 : %T\n", evens(6))
	fmt.Print("evens(10) : ")
	for v := range evens(10) {
		fmt.Print(v, " ")
	}
	fmt.Println()

	fmt.Print("pairs()   : ")
	for k, v := range pairs() {
		fmt.Printf("%s=%d ", k, v)
	}
	fmt.Println()

	fmt.Println("slices.Collect :", slices.Collect(evens(10)))

	m := map[string]int{"가": 1, "나": 2, "다": 3}
	ks := slices.Sorted(maps.Keys(m))
	fmt.Println("maps.Keys 는 iter.Seq 다 — 정렬해서 찍는다 :", ks)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
evens 의 타입 : iter.Seq[int]
evens(10) : 0 2 4 6 8 
pairs()   : 가=0 나=1 다=2 
slices.Collect : [0 2 4 6 8]
maps.Keys 는 iter.Seq 다 — 정렬해서 찍는다 : [가 나 다]
(exit 0)
```

**왜 그런가**

- `%T` 가 **`iter.Seq[int]`** 를 찍는다 — 별칭이 아니라 **이름 있는 타입**이라 이름 그대로 나온다.
  바닥 타입은 `func(func(int) bool)` 이고, 그래서 `range` 가 받아 준다.
- `iter.Seq2[K, V]` 는 값을 **둘** 내놓는다 — `yield` 의 시그니처가 `func(K, V) bool` 이다.
- **`maps.Keys(m)` 는 `iter.Seq[K]` 를 돌려준다** — **1.23부터**다.
  (그 전에는 `golang.org/x/exp/maps` 가 슬라이스를 돌려줬다.)
- ★ 그래서 **`slices.Sorted(maps.Keys(m))`** 가 관용구가 됐다 —
  「맵 키를 순서대로 보고 싶다」는 요구가 **한 줄**이 된다.
  09번 주제가 「순서를 쓰려면 정렬하라」고 한 자리의 지금 답이 이것이다.
- `slices.Collect` 는 반복자를 슬라이스로 모은다.
- 층 — **표준 라이브러리(1.23+)** 다. `range` 가 함수를 받는 것은 **명세 보장**이고,
  `iter`·`slices`·`maps` 의 이 함수들은 **라이브러리 계약**이다.

### 10. 다른 주제와 잇기

**출력** — 없음(연결 문항).

**왜 그런가**

- **루프 변수가 회차마다 새것인가** — [13번 주제](../13-closures-variable-capture-and-loop-variable-change/).
  이 주제는 「꼴과 피연산자」를, 그 주제는 「변수가 몇 개인가」를 맡는다.
- **배열과 슬라이스가 값과 헤더로 갈리는 것** — [05번 주제](../05-arrays-vs-slices-value-and-header/).
  2번의 답이 통째로 거기서 나온다.
- **문자열 `range` 가 룬을 주는 것** — [10번 주제](../10-strings-bytes-runes-and-utf8-iteration/).
- **맵 순회 순서 무작위화** — [09번 주제](../09-maps-declaration-comma-ok-delete-and-iteration-order/).
- **라벨 `break`/`continue`** — [15번 주제](../15-switch-type-switch-fallthrough-labels-and-goto/).
- **`iter` 패키지 설계 자체** — 목록의 **39번 주제**. 여기서는 `range` 가 받는다는 것까지만 본다.
- 덤 — **채널 `range` 와 `close`** 는 [목록의 **29번 주제**](../29-channels-buffering-direction-close-range-and-nil/),
  표를 `range` 로 도는 테스트 관용구는 **49번 주제**다.

---

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행 1회** | 재실행 결과가 `normalize-shaky.py` 로 **동일** |
| 판 확인 | `go version` · `go env GOOS GOARCH GOVERSION` | 1 | `go1.27.1 linux/amd64` |
| 네 형태 (`t14a`) | `go build && ./prog` | 1 | 다섯 줄 · 마지막만 `0 1` |
| ★★ `range` 복사 (`t14b`) | 〃 | 1 | 배열만 `1 2 3 4` · 나머지 셋은 `1 99 3 4` |
| 횟수는 미리 정해진다 (`t14c`) | 〃 | 1 | 3회(len 6) · 4회(len 1) · 본 키 1개 |
| 정수 `range` (`t14d`) | 〃 | 1 | `0 1 2 3 4` · 0회 · 0회 · `uint8` |
| ★★ 정수 `range` 판 경계 (`t14e`) | `go 1.21` / `go 1.22` 로 각각 | 2 | `requires go1.22 or later` + `exit 1` / 정상 |
| ★★★ 반복자와 `yield` (`t14f`) | `go build && ./prog` | 1 | `break` 뒤 `yield 가 false` · `2` 는 안 만들어짐 |
| ★★ 함수 `range` 판 경계 (`t14g`) | `go 1.22` / `go 1.23` 로 각각 | 2 | `requires go1.23 or later` + `exit 1` / 정상 |
| 문자열·채널·맵 (`t14h`) | `go build && ./prog` | 1 | 룬 3회(`len` 5) · `1 2 3` · 정렬한 키 셋 |
| `iter.Seq` (`t14i`) | 〃 | 1 | `iter.Seq[int]` · `Collect` · `Sorted(Keys)` |
| 형태 (`t14form`) | 〃 | 1 | 여섯 꼴 전부 컴파일 |

**구현·환경에 달린 항목**(버전이 오르거나 환경이 바뀌면 **다시 찍어야 하는** 것)

| 항목 | 무엇에 달렸나 |
|---|---|
| **맵 순회 순서** | **보장 없음.** 이 문서는 정렬하거나 개수만 세어 그 칸을 아예 안 썼다 |
| 순회 중 **추가한 키가 나오나** | **보장 없음** — "may be produced … or may be skipped". **안 던졌다** |
| 값 변수를 안 받을 때 배열 복사가 **지워지는가** | **구현.** 어셈블리를 안 떠서 **안 쟀다** |
| `for i := range n` 이 3절 루프와 **같은 코드인가** | **구현. 안 쟀다** |
| 반복자 호출이 **인라인되는가** | **구현. 안 쟀다** |
| 에러 메시지의 **문구 자체** | **툴체인 판(go1.27.1)**. 읽을 것은 `requires go1.NN or later` 라는 뼈대다 |
| 타입 파라미터에 대한 `range` 규칙 | **안 던졌다**(37번 주제의 영역) |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다.

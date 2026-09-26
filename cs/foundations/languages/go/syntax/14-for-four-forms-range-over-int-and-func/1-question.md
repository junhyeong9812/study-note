# go/syntax/14 — `for` 의 네 형태 · 정수 range(1.22) · 함수 range(1.23) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> ★ **`range` 문제를 만나면 먼저 「이 피연산자는 값인가 참조인가」를 적어라.** 답이 거기서 나온다.
> ★ **답마다 「그 값을 누가 보장하나」를 같이 적어라** — 1.21까지의 보장인가, 1.22 / 1.23부터인가,
> gc 구현인가, 이 판의 관찰인가.
> ★★ **맵이 나오는 문제에서 순회 순서를 답으로 적지 마라.** 보장이 없는 칸이다.
> 소스는 전부 `go build -trimpath -o prog . && ./prog` 로 던졌다. 모듈 이름은 `ex` 다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 다섯 줄 — 마지막 줄만 왜 짧은가 (예측)

```go
// t14a.go
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
```

- 다섯 줄은 각각 무엇으로 찍히는가?
- ②와 ③은 다른 언어의 무엇에 해당하는가 — Go 에 그 키워드가 있는가?
- 마지막 줄의 `for ; ; m++` 은 몇 번 도는가 — 왜 그렇게 끝나는가?
- 명세는 이 꼴들의 관계를 어떻게 적었는가?

### 2. ★★ 네 덩어리가 각각 무엇을 찍나 (예측)

```go
// t14b.go
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
```

- ①②③의 `v` 줄은 각각 무엇으로 찍히는가?
- 셋 중 **루프 안의 수정이 `v` 에 보이는** 것은 어느 것인가 — 왜인가?
- ④에서 `it.N = 99` 를 세 번 한 결과는 무엇인가 — 고치려면 어떻게 써야 하는가?
- 이 네 덩어리의 답을 **05번 주제의 한 낱말**로 묶어 설명하라.

### 3. 루프가 몇 번 도나 (예측)

```go
// t14c.go
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
```

- ①②③의 반복 횟수와 뒤따르는 수치는 각각 무엇인가?
- ①에 넣어 둔 안전장치(`n > 10` 이면 `break`)는 걸리는가 — 그 사실이 무엇을 증명하는가?
- ③에서 「본 키의 개수」가 그 값인 이유는 무엇인가 — 그것은 보장인가 관찰인가?
- ③이 맵을 쓰면서도 **순서를 안 찍은** 이유는 무엇인가?

### 4. 정수 `range` 다섯 줄 (예측)

```go
// t14d.go
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
```

- 다섯 줄은 각각 무엇으로 찍히는가?
- `range 0` 과 `range -1` 은 각각 몇 번 도는가?
- 마지막 줄의 `i` 는 무슨 타입인가 — 그 규칙은 무엇인가?
- 이 소스를 `go.mod` 의 `go 1.21` 로 던지면 무엇이 나오는가 — **메시지 전문과 종료 코드**는?

### 5. ★★★ 생산자와 소비자가 번갈아 찍는다 (예측)

```go
// t14f.go
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
```

- ①의 출력은 몇 줄이고 어떤 순서인가?
- ②에서 `break` 뒤에 생산자 쪽은 무엇을 찍는가 — 그리고 `2` 는 만들어지는가?
- ③은 ②와 같은가 다른가?
- `yield` 의 반환값을 무시하는 반복자는 무엇을 어긴 것인가 — 명세의 문장으로 답하라.

### 6. 문자열·채널·맵·변수 개수 (예측)

```go
// t14h.go
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
```

- 문자열 덩어리는 몇 줄이고 인덱스는 무엇으로 찍히는가 — `len(s)` 와 회차 수가 왜 다른가?
- 채널 덩어리는 무엇을 찍는가 — `close` 를 지우면 무슨 일이 나는가?
- 맵 덩어리가 정렬을 거쳐 찍는 이유는 무엇인가?
- 마지막 덩어리에서 변수를 1개만 받았을 때, **슬라이스·맵·채널**은 각각 무엇을 주는가?

### 7. 어느 판부터 되나 (경계)

- `for i := range 5` 는 몇 판부터인가 — 그 앞 판에서 던지면 **메시지 전문**은 무엇인가?
- `for v := range fn` 은 몇 판부터인가 — 그 앞 판의 메시지 전문은?
- 두 메시지가 공통으로 가리키는 **파일 이름**은 무엇인가?
- 이 메시지는 「파서가 이 문법을 모른다」는 뜻인가, 다른 뜻인가?

### 8. 왜 배열은 안 보이고 슬라이스는 보이나 (왜)

- `range` 는 피연산자를 **몇 번** 평가하는가?
- 배열과 슬라이스에서 「복사되는 것」이 각각 무엇인가?
- 배열 복사를 피하는 문법은 무엇인가?
- 슬라이스에서 원소를 고치려면 어떻게 써야 하는가 — `v` 로는 왜 안 되는가?

### 9. `iter.Seq` 는 무엇인가 (경계)

```go
// t14i.go
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
```

- `iter.Seq[int]` 는 무슨 타입의 별칭인가 — `%T` 는 무엇을 찍는가?
- `iter.Seq2` 는 무엇이 다른가?
- `maps.Keys(m)` 는 무엇을 돌려주는가 — 몇 판부터인가?
- `slices.Sorted(maps.Keys(m))` 가 관용구가 된 이유는 무엇인가?

### 10. 다른 주제와 잇기 (연결)

- 루프 변수가 회차마다 새것인지의 정본은 몇 번 주제인가?
- 배열과 슬라이스가 값과 헤더로 갈리는 것의 정본은 몇 번 주제인가?
- 문자열 `range` 가 룬을 주는 것의 정본은 몇 번 주제인가?
- 맵 순회 순서 무작위화의 정본은 몇 번 주제인가?
- 라벨 `break`/`continue` 의 정본은 몇 번 주제인가?
- `iter` 패키지 설계 자체의 정본은 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

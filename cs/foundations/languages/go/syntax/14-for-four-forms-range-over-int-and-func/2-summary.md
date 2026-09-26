# go/syntax/14 — `for` 의 네 형태 · 정수 range(1.22) · 함수 range(1.23) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Go 명세](https://go.dev/ref/spec) 의 For statements · For statements with ForClause ·
> For statements with range clause · Break statements · Continue statements 절.\
> 웹이 아니라 **이 툴체인이 들고 있는 `$(go env GOROOT)/doc/go_spec.html` 을 열어** 인용했다.
> 그 파일의 머리는 「**Language version go1.27 (May 26, 2026)**」이다.
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> **버전** — `for` 의 세 꼴(3절·조건만·무한)과 배열·슬라이스·맵·문자열·채널 `range` 는 **1.0부터** 같다.
> **정수 `range`(`for i := range 5`)는 1.22부터**, **함수 `range`(반복자)는 1.23부터**,
> `iter` 패키지와 `slices.Collect`·`maps.Keys` 의 반복자 판도 **1.23부터**다.
> **루프 변수가 회차마다 새로 생기는 것도 1.22부터**다 — 그 축의 정본은 [13번 주제](../13-closures-variable-capture-and-loop-variable-change/)다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 명세로, 출력은 실행으로 접지했다.

## ★★ 이 갈래가 쓰는 층 — 이 주제도 넷이다

Go 에 반복문은 `for` 하나뿐인데, **그 하나에 최근 두 판이 꼴을 둘 더 보탰다.**
그래서 이 주제도 「명세 보장」 칸이 판으로 쪼개진다.

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **1.21까지의 보장** | 그때의 명세가 약속한 것 — `range` 의 피연산자는 **배열·슬라이스·문자열·맵·채널** 다섯뿐 | `go.mod` 를 내려 던졌을 때의 **컴파일 에러 전문** |
| **1.22 / 1.23부터의 보장** | 정수 `range`(1.22)와 함수 `range`(1.23)가 그 목록에 더해졌다 | `go_spec.html` 의 `[Go 1.22]`·`[Go 1.23]` 표기 |
| **구현(gc)** | 이 컴파일러가 그렇게 하는 것 | 반복자 함수가 **어느 순서로 불리는지**의 실행 추적 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 실행 출력(재실행 대조까지) |

★★ **에러 메시지가 그 판 경계를 직접 말해 준다** —
`requires go1.22 or later (-lang was set to go1.21; check go.mod)`.
「언제부터인가」를 문서에서 옮겨 적지 않고 **컴파일러에게 물어서** 받은 답이다.

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
| **흔들린다** | **맵 순회 순서** | 명세가 "not specified … not guaranteed to be the same from one iteration to the next" 라고 못 박는다. 그래서 이 문서의 맵 예제는 **키를 모아 정렬해서** 찍는다 |
| **흔들린다** | 고루틴이 섞인 출력 순서 | 이 주제는 그 자리를 안 쓴다 |
| 안 흔들린다 | 반복 **횟수** | `range` 가 시작할 때 정해진다 |
| 안 흔들린다 | 반복자 함수와 루프 몸통이 **번갈아 찍는 순서** | 같은 고루틴 위에서 도는 보통의 함수 호출이다 |
| 안 흔들린다 | 컴파일 에러 문장 본문과 `파일:줄:칸` | 같은 소스·같은 판이면 같다 |
| 안 흔들린다 | 종료 코드 · `len`·`cap` 값 | 〃 |

## 한눈에 — 쉽게 말하면

**Go 의 반복문은 `for` 하나뿐이고, 그 뒤에 무엇을 적느냐로 네 꼴이 된다.**

`while` 도 `do-while` 도 `foreach` 도 없다. 전부 `for` 한 낱말의 변주다.

| 비유 | 실체 |
|---|---|
| 「세 칸짜리 계기판」 | `for init; cond; post { }` — C 의 그것과 같다 |
| 「조건만 단 계기판」 | `for cond { }` — 다른 언어의 `while` |
| 「계기판을 떼 버림」 | `for { }` — 무한 루프. `break` 로만 끝난다 |
| 「상자를 열어 하나씩 꺼냄」 | `for i, v := range x { }` |
| 「숫자를 세어 달라고 맡김」 | `for i := range 5 { }` — **1.22부터** |
| 「남이 꺼내 주는 것을 받음」 | `for v := range fn { }` — **1.23부터**. `fn` 이 반복자 함수다 |

```text
   for  [init; cond; post]  { … }      <- 셋 다 있으면 3절
   for  [cond]              { … }      <- 가운데만 있으면 while
   for                      { … }      <- 아무것도 없으면 무한
   for  [x, y :=] range E   { … }      <- range 절

                     E 에 올 수 있는 것
        ┌───────────────────────────────────────────┐
        │ 배열 · 배열 포인터 · 슬라이스 · 문자열     │  1.0 부터
        │ 맵 · 채널                                 │
        │ 정수                                      │  1.22 부터
        │ 함수 (반복자)                             │  1.23 부터
        └───────────────────────────────────────────┘
```

> **`range` 절(range clause)** — `for` 뒤에 `range E` 를 적는 꼴. `E` 를 훑으며 값을 내놓는다.\
> 예: `for i, v := range s` 는 인덱스와 값을 준다. 변수를 0·1·2개 중 골라 받는다.

> **반복자 함수(iterator function)** — `func(yield func(V) bool)` 꼴의 함수.
> `range` 가 이것을 받아 준다(1.23+).\
> 예: 값을 내놓고 싶을 때마다 `yield(v)` 를 부른다. `yield` 가 `false` 를 돌려주면 **멈춰야 한다.**

> **`yield`** — `range` 가 만들어 반복자에게 넘겨 주는 함수. 「이 값으로 루프 몸통을 한 번 돌려 달라」는 뜻이다.\
> 예: 몸통이 `break` 하면 `yield` 가 `false` 를 돌려주고, **그 뒤로 다시 부르면 안 된다.**

> **복사가 생기는 자리(range expression copy)** — `range` 는 피연산자를 한 번 평가해 **값으로** 든다.
> 배열이면 배열 전체가 복사된다.\
> 예: `for i, v := range arr` 도중에 `arr` 을 고쳐도 `v` 는 안 바뀐다((2)절).

- C 와 다른 점 — `for (;;)` 이 `for { }` 가 됐고 **괄호가 없다.** 그리고 `while` 이 아예 없다.
- Python 과 다른 점 — `for i in range(5)` 가 `for i := range 5` 로 **꼴은 닮았는데**,
  파이썬의 `range` 는 **객체**이고 Go 의 `range` 는 **키워드**다.
- Rust 와 다른 점 — Rust 는 `Iterator` 트레잇이 있고 Go 는 **함수 하나**가 그 자리를 맡는다.
  타입이 아니라 **시그니처**가 계약이다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `for` 하나로 네 꼴이 되는데, **`range` 절은 어디까지 받아 주나** — 그리고 언제 넓어졌나.
2. `range` 는 **어디에서 복사를 만드나** — 그 복사가 보이는 자리와 안 보이는 자리.
3. 반복자 함수는 **누가 누구를 부르는 구조인가** — 몸통이 `break` 하면 무슨 일이 일어나나.

★ 「루프 변수가 회차마다 새것인가」는 이 주제가 아니다 —
[13번 주제](../13-closures-variable-capture-and-loop-variable-change/)가 정본이다.
여기는 **`for` 의 꼴과 `range` 의 피연산자**를 본다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

| 창 | 무엇을 보여 주나 | 한계 |
|---|---|---|
| 실행 출력 | 몇 번 도나 · 무엇이 나오나 | **복사가 생겼는지는 값으로만 짐작**한다 |
| ★★ **판 레버** — `go.mod` 의 `go` 지시어 | **이 꼴이 몇 판부터인가**를 컴파일러가 직접 말한다 | 툴체인은 하나다. 옛 컴파일러가 아니라 옛 규칙이다 |
| ★★ **생산자·소비자 추적** — 반복자 안팎에서 번갈아 찍는다 | **누가 누구를 부르는지**와 `yield` 의 반환값 | 출력이 길어진다 |
| **원본을 루프 중에 밀어 보기** | `range` 가 무엇을 복사했나 | 「안 보인다」가 「복사됐다」의 유일한 증거는 아니다 — 그래서 배열·슬라이스·배열 포인터 셋을 나란히 던진다 |

### (1) 네 형태 — 전부 `for` 한 낱말이다

**언제 쓰나** — Go 코드를 처음 읽을 때. `while` 을 찾다가 못 찾는 자리다.

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

그림 해설 (한 단계씩):

- ①은 C 의 3절 꼴 그대로다. **괄호가 없다**는 것만 다르다.
- ②는 다른 언어의 `while` 이다. 명세가 그 동치를 직접 적는다.

  > **`for cond { S() }` is the same as `for ; cond ; { S() }`**\
  > **`for { S() }` is the same as `for true { S() }`**

- ③은 무한 루프다. `break`·`return`·`panic` 으로만 끝난다.
- ④가 `range` 절이다. 이 절이 이 주제의 나머지 전부다.
- ★ 마지막 줄은 ③의 다른 꼴이다 — **세 절 중 조건만 비어도 무한**이다. `for ; ; m++` 도 무한 루프다.

비용 — 세 꼴 사이에 차이가 없다. 명세가 **같은 문**이라고 말한다.

### (2) ★★ `range` 가 복사를 만드는 자리 — 배열·슬라이스·배열 포인터

**언제 쓰나** — 루프 안에서 원본을 고칠 때. **조용히 틀리는 자리**다.

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

그림 해설 (한 단계씩):

- ① **배열** — 루프 첫 회차에 `arr[1] = 99` 를 했는데 `v` 는 **`1 2 3 4`** 다.
  루프 뒤 배열은 `[1 99 3 4]` 로 바뀌어 있다. **`range` 가 배열을 통째로 복사해 두고 돈다.**
- ② **슬라이스** — 같은 짓을 했는데 `v` 가 **`1 99 3 4`** 다. 고친 것이 **보인다.**
  ★ 복사가 없었던 것이 아니다 — **헤더가 복사됐고 헤더가 가리키는 배열은 하나**라서 보이는 것이다
  ([05번 주제](../05-arrays-vs-slices-value-and-header/) (3)절이 그 정본이다).
- ③ **배열 포인터**(`range &ap`) — **`1 99 3 4`** 다. 포인터를 복사해도 가리키는 배열은 하나다.
  ★ 큰 배열을 `range` 할 때 복사를 피하는 관용구가 이것이다.
- ④ **원소가 구조체면 `v` 는 복사본**이다. `it.N = 99` 가 아무 데도 안 남는다.
  고치려면 **`items[i]` 를 직접** 건드려야 한다.
- ★★ 정리하면 **`range` 는 언제나 피연산자를 값으로 한 번 든다.**
  그 값이 배열이면 원소까지 복사되고, 슬라이스·맵·채널·포인터면 **안에 든 포인터가 복사**되어 내용이 공유된다.
  **05번 주제의 「짐칸인가 쪽지인가」가 여기서 그대로 답이 된다.**

```text
   for … range arr           for … range sl            for … range &ap

   arr [1 2 3 4]             sl [ptr|4|4] ─┐           ap [1 2 3 4]
     │ 통째로 복사              (복사)      │             ▲
     ▼                        sl' [ptr|4|4]─┴─> [1 2 3 4]  │ 포인터만 복사
   복사본 [1 2 3 4]  <- v 는                  ▲              (&ap)
   여기서 나온다                              └ v 는 여기서 나온다
```

비용 — 배열 `range` 는 **원소 수에 비례한 복사**다. `range &arr` 이면 그 복사가 없다.
★ 다만 `for i := range arr` 처럼 **값 변수를 안 받으면** 컴파일러가 복사를 지울 수 있다 —
이 문서는 **그것을 재지 않았다.**

### (3) ★ `range` 는 시작할 때 횟수를 정한다

**언제 쓰나** — 루프 안에서 `append` 하거나 컬렉션을 줄일 때.

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

그림 해설 (한 단계씩):

- ① 루프 안에서 `append` 를 세 번 했는데 **반복은 3회로 끝난다.** 루프 뒤 `len` 은 6이다.
  ★ 안전장치(`n > 10` 이면 `break`)를 넣어 뒀는데 **안 걸렸다** — 즉 정말로 안 늘어난 것이다.
- ② 반대로 **줄여도** 이미 정해진 4회를 돈다.
- ★★ 이유는 (2)절과 같다 — `range sl` 이 든 것은 **그 시점의 헤더**이고,
  루프 뒤에 `sl` 변수가 가리키는 것이 바뀌어도 루프가 들고 있는 헤더는 안 바뀐다.
  명세가 슬라이스에 대해 "the range expression is evaluated once before beginning the loop" 라는 뜻으로
  길이를 한 번만 본다고 적는다(배열·슬라이스의 `len` 은 시작 시점에 정해진다).
- ③ **맵은 다르다.** 맵에는 「길이를 미리 정한다」가 없고, 대신 명세가 이렇게 적는다.

  > **The iteration order over maps is not specified and is not guaranteed to be the same
  > from one iteration to the next.** If a map entry that has not yet been reached is removed
  > during iteration, **the corresponding iteration value will not be produced.** If a map entry
  > is created during iteration, **that entry may be produced during the iteration or may be skipped.**

  실측 — 첫 회차에 나머지 셋을 지우니 **본 키가 1개**로 끝났다.
  ★ 「지운 것은 안 나온다」는 **보장**이고, 「추가한 것이 나오나」는 **보장이 아니다.**
  그래서 이 문서는 **추가 쪽을 안 던졌다** — 던져 봐야 그 판의 관찰일 뿐이다.
- ★★ 이 블록이 맵을 쓰는데도 **순서가 안 실린다.** 본 키를 모아 **개수만** 찍었다.
  맵 순회 순서는 흔들리는 칸이므로 근거로 쓰지 않는다(09번 주제가 그 정본이다).

비용 — 없다. 횟수를 미리 정하는 것이 오히려 싸다.

### (4) ★★ 정수 `range` — 1.22부터

**언제 쓰나** — 「N번 돌아라」가 하고 싶을 때. Go 에서 가장 늦게 들어온 흔한 꼴이다.

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

그림 해설 (한 단계씩):

- `for i := range 5` 가 **0부터 4까지**를 준다. `for range 3` 은 변수 없이 세 번 돈다.
- **0이면 0회, 음수도 0회**다. 명세가 그렇게 적는다.

  > For an integer value n … the iteration values **0 through n-1** are produced in increasing order.
  > If n is of integer type, the iteration values have that same type. …
  > **If n <= 0, the loop does not run any iterations.**

- ★ **`i` 의 타입은 `range` 식의 타입**이다 — `uint8` 짜리를 주면 `i` 도 `uint8` 이다.
  상수를 주면 그 상수의 기본 타입(`int`)이 된다.
- 이 꼴을 1.21 판으로 던지면 **컴파일 에러**다.

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

  `requires go1.22 or later (-lang was set to go1.21; check go.mod)` —
  ★★ **에러 메시지가 「몇 판부터인지」와 「그 스위치가 어디 있는지」를 둘 다 말해 준다.**
  문서에서 옮겨 적은 버전이 아니라 **컴파일러에게 물어서 받은 답**이다.
- 같은 소스를 `go 1.22` 로 올리면 그대로 돈다.

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

비용 — 없다. `for i := 0; i < n; i++` 과 같은 코드가 난다(이 문서는 **그것을 확인하지 않았다** —
어셈블리를 안 떴다).

### (5) ★★★ 함수 `range` — 1.23부터 · `yield` 가 `false` 면 멈춘다

**언제 쓰나** — 컬렉션이 아닌 것을 `for` 로 훑고 싶을 때. 이 주제에서 **가장 중요한 절**이다.

반복자는 **자료구조가 아니라 함수**다. 시그니처가 `func(yield func(V) bool)` 이면 `range` 가 받아 준다.
그 안에서 값을 내놓고 싶을 때마다 `yield(v)` 를 부르고, **`yield` 가 `false` 를 돌려주면 멈춰야 한다.**

여기서는 반복자 **안쪽**과 루프 **몸통** 양쪽에서 찍어 그 대화를 그대로 본다.

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

그림 해설 (한 단계씩):

- ① **끝까지 도는 경우** — 생산자가 `yield` 를 부르고, 소비자(루프 몸통)가 돌고,
  `yield` 가 **`true`** 를 돌려주고, 생산자가 계속한다. 다 내놓으면 생산자가 그냥 끝난다.
- ② ★★★ **`break` 하는 경우** — 소비자가 `break` 를 하자 **`yield` 가 `false` 를 돌려주고**,
  생산자가 `return` 으로 되돌아간다. `2` 는 **아예 만들어지지도 않았다.**
- ③ `return` 으로 끊어도 같다. 몸통을 끝내는 모든 방법이 `false` 를 만든다.
- 명세가 그 계약을 문장으로 적는다.

  > For a function f, the iteration proceeds by **calling f with a new, synthesized yield function
  > as its argument**. … After each successive loop iteration, **yield returns true** and may be
  > called again to continue the loop. … **If the loop body terminates (such as by a break statement),
  > yield returns false and must not be called again.**

- ★★ 「**must not be called again**」이 계약의 절반이다. 반복자를 쓰는 쪽이 아니라 **만드는 쪽의 의무**다.
  `if !yield(i) { return }` 을 빼먹으면 그 반복자는 계약 위반이다.
- ★ 제어가 **왔다 갔다** 한다는 것이 이 꼴의 핵심이다. 반복자는 「값 목록」을 만들어 주는 것이 아니라,
  **루프 몸통을 콜백으로 받아 자기 흐름 안에서 부른다.** 그래서 `defer` 로 뒷정리를 붙일 수 있다.
- 1.22 판으로 던지면 역시 컴파일 에러다.

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

```text
   for v := range upto(3) { 몸통 }

   range 가 yield 를 만들어 upto 에게 준다
        │
        ▼
   upto: yield(0) ──────> 몸통 실행 ──> true 반환 ──> upto 계속
         yield(1) ──────> 몸통 실행 ──> ★ break!  ──> false 반환
                                                        │
         if !yield(1) { return }  <─────────────────────┘
         (여기서 반복자가 스스로 끝낸다 — 2 는 안 만들어진다)
```

비용 — 회차마다 **함수 호출 하나**가 더 있다. 인라인될 수도 있다 — **이 문서는 재지 않았다.**

### (6) `iter.Seq` 와 표준 라이브러리 — 1.23부터

**언제 쓰나** — 반복자를 돌려주는 함수를 쓸 때. 시그니처를 매번 적지 않아도 된다.

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

그림 해설 (한 단계씩):

- `iter.Seq[int]` 는 **`func(func(int) bool)` 의 이름 있는 별칭**이다. `%T` 가 그것을 보여 준다.
- `iter.Seq2[K, V]` 는 값을 **둘** 내놓는다 — `for k, v := range` 로 받는다.
- `slices.Collect` 가 반복자를 슬라이스로 모은다. `maps.Keys` 는 **1.23부터 `iter.Seq` 를 돌려준다.**
  ★ 그래서 `slices.Sorted(maps.Keys(m))` 가 **맵 키를 정렬해 얻는 관용구**가 됐다 —
  09번 주제가 「순서를 쓰려면 정렬하라」고 한 그 자리의 지금 답이다.
- ★ `iter` 패키지 자체의 정본은 목록의 **39번 주제**다. 여기서는 **`range` 가 그것을 받는다**는 것까지만 본다.

비용 — `Collect` 는 슬라이스 하나를 새로 만든다.

### (7) 나머지 피연산자 — 문자열·채널·맵

**언제 쓰나** — 각각의 정본 주제로 가기 전에 「`range` 가 무엇을 주나」만 확인할 때.

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

그림 해설 (한 단계씩):

- **문자열 `range` 는 룬을 준다.** 인덱스는 **바이트 오프셋**이라 `0 → 3 → 4` 로 건너뛴다.
  `len(s)` 는 5(바이트)인데 회차는 3번이다. 정본은 [10번 주제](../10-strings-bytes-runes-and-utf8-iteration/)다.
- **채널 `range` 는 닫힐 때까지** 받는다. 안 닫으면 영원히 막힌다. 정본은 [목록의 **29번 주제**](../29-channels-buffering-direction-close-range-and-nil/)다.
- **맵 `range` 는 키와 값 둘**을 준다. 여기서는 **키를 모아 정렬해** 찍었다 — 순서가 보장이 아니기 때문이다.
- **변수를 몇 개 받을지 고를 수 있다** — 0개·1개·2개.
  ★ 맵에서 1개만 받으면 **키**이고, 슬라이스·배열·문자열에서 1개만 받으면 **인덱스**다.
  채널에서는 1개가 **받은 값**이다. **같은 문법이 피연산자에 따라 다른 것을 준다.**

비용 — 문자열 `range` 는 UTF-8 디코딩 비용이 붙는다. 인덱스 접근(`s[i]`)은 바이트 하나다.

## 문법 — 형태와 규칙

### 형태

```go
// t14form.go
package main

import "fmt"

func main() {
	for i := 0; i < 2; i++ { // ① 3절 — init; cond; post
		_ = i
	}
	n := 0
	for n < 2 { // ② 조건만
		n++
	}
	for { // ③ 무한 — break 가 있어야 끝난다
		break
	}
	for i, v := range []int{7, 8} { // ④ range — 컬렉션
		_, _ = i, v
	}
	for i := range 2 { // ⑤ range — 정수 (1.22+)
		_ = i
	}
	for v := range func(yield func(int) bool) { yield(1) } { // ⑥ range — 함수 (1.23+)
		_ = v
	}
	fmt.Println("여섯 꼴 전부 컴파일된다")
}
```

```text
===== 소스: t14form.go =====
package main

import "fmt"

func main() {
	for i := 0; i < 2; i++ { // ① 3절 — init; cond; post
		_ = i
	}
	n := 0
	for n < 2 { // ② 조건만
		n++
	}
	for { // ③ 무한 — break 가 있어야 끝난다
		break
	}
	for i, v := range []int{7, 8} { // ④ range — 컬렉션
		_, _ = i, v
	}
	for i := range 2 { // ⑤ range — 정수 (1.22+)
		_ = i
	}
	for v := range func(yield func(int) bool) { yield(1) } { // ⑥ range — 함수 (1.23+)
		_ = v
	}
	fmt.Println("여섯 꼴 전부 컴파일된다")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
여섯 꼴 전부 컴파일된다
(exit 0)
```

규칙 불릿.

- **`for` 가 유일한 반복문**이다. `while`·`do-while`·`foreach` 키워드가 없다.
- **괄호를 쓰지 않는다.** `for (i := 0; …)` 은 컴파일 에러다.
- 세 절 중 **조건만 남기면 `while`**, **셋 다 지우면 무한 루프**다.
- `range` 의 피연산자 — **배열 · 배열 포인터 · 슬라이스 · 문자열 · 맵 · 채널**(1.0)
  + **정수**(1.22) + **함수**(1.23).
- 변수는 **0·1·2개** 중 고른다. 두 값의 뜻은 피연산자마다 다르다
  (슬라이스: 인덱스·값 / 맵: 키·값 / 채널: **값 하나뿐** / 정수: **값 하나뿐**).
- `range` 는 피연산자를 **시작 전에 한 번** 평가한다. 배열이면 그 시점에 복사된다.
- **`break`·`continue` 는 가장 안쪽 `for`(또는 `switch`·`select`)에** 붙는다.
  더 바깥을 끝내려면 **라벨**을 쓴다(15번 주제).
- 반복자 함수의 계약 — `yield` 가 **`false` 를 돌려주면 더 부르면 안 된다.**

### 금지 사례 — 컴파일러가 거부하는 것

판이 낮을 때 나는 두 에러가 이 주제의 **금지 사례 정본**이다 — (4)절과 (5)절에 실었다.
둘 다 같은 꼴이다.

```text
cannot range over 5 (untyped int constant): requires go1.22 or later (-lang was set to go1.21; check go.mod)
cannot range over seq (value of type func(yield func(int) bool)): requires go1.23 or later (-lang was set to go1.22; check go.mod)
```

★ **「이 문법을 모른다」가 아니라 「이 판에서는 안 쓴다」** 고 말한다는 점이 중요하다.
파서는 이미 알고 있고, **언어 판이 막고 있는 것**이다. 그래서 `go.mod` 한 줄로 풀린다.

## 어디서 틀리나

### 1. ★★★ 「`range` 로 도는 동안 원소를 고치면 `v` 에 보인다」 — 피연산자에 달렸다

- (2)절 실측 — **배열은 안 보이고**(`1 2 3 4`) **슬라이스는 보인다**(`1 99 3 4`).
- 같은 문법인데 답이 갈린다. 갈리는 것은 **「짐칸인가 쪽지인가」**([05번 주제](../05-arrays-vs-slices-value-and-header/)).
- 고치는 법 — 배열에서 복사를 피하려면 **`range &arr`**, 원소를 고치려면 **`s[i]` 를 직접** 쓴다.

### 2. ★★★ 「`range` 안에서 `append` 하면 루프가 늘어난다」

- (3)절 실측 — **3회로 끝난다.** 안전장치가 안 걸린 것이 그 증거다.
- 줄여도 마찬가지다 — 이미 정해진 4회를 돈다.
- 고치는 법 — 늘어나는 것을 돌려면 **인덱스 루프**(`for i := 0; i < len(s); i++`)를 쓴다.
  그쪽은 회차마다 `len` 을 다시 본다.

### 3. ★★ 「구조체 슬라이스를 `range` 하며 `v.F` 를 고쳤다」

- (2)절 ④ 실측 — **아무 데도 안 남는다.** `v` 는 원소의 복사본이다.
- 슬라이스라서 공유될 것 같은데, 공유되는 것은 **배열 칸**이고 `v` 는 **그 칸에서 복사된 값**이다.
- 고치는 법 — `for i := range items { items[i].F = … }`.

### 4. ★★ 「`for i := range 5` 는 옛날부터 있었다」

- (4)절 실측 — **1.21에서 컴파일 에러**다. 1.22부터다.
- 함수 `range` 는 한 판 더 늦은 **1.23**이다.
- 고치는 법 — **`go.mod` 의 `go` 줄을 본다.** 에러 메시지가 그 줄을 직접 가리킨다.

### 5. ★★ 「반복자에서 `yield` 의 반환값을 무시해도 된다」

- (5)절 실측 — 소비자가 `break` 하면 `yield` 가 **`false`** 를 돌려준다.
- 무시하고 계속 부르면 **명세 위반**이다("must not be called again").
- 고치는 법 — **`if !yield(v) { return }`** 을 언제나 적는다.

### 6. ★ 「맵에서 도중에 지우면 이상해진다」

- (3)절 ③ 실측 — **안 나온다.** 그것은 명세 보장이다.
- 보장이 아닌 것은 **추가**다 — "may be produced … or may be skipped".
- 고치는 법 — 순회 중 추가는 피한다. 지우기는 안전하다.

### 7. ★ 「채널 `range` 는 값이 없으면 끝난다」

- (7)절 실측 — **닫힐 때까지** 돈다. 비었다고 끝나지 않고 **막힌다.**
- 고치는 법 — 보내는 쪽이 `close` 한다. 정본은 [목록의 **29번 주제**](../29-channels-buffering-direction-close-range-and-nil/)다.

### 8. ★ 「`for` 에 괄호를 안 써서 헷갈린다」

- Go 는 **괄호가 없고 중괄호가 필수**다. `if`·`switch` 도 같다.
- `for (i := 0; i < 3; i++)` 은 컴파일되지 않는다.
- 고치는 법 — `gofmt` 가 강제하므로 고민할 일이 없다.

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| `for cond` 가 `for ; cond ;` 와 **같은 문** | **1.0부터 보장** | "for cond { S() } is the same as for ; cond ; { S() }" |
| `for { }` 가 `for true { }` 와 **같은 문** | **1.0부터 보장** | "for { S() } is the same as for true { S() }" |
| 배열 `range` 가 **피연산자를 복사** | **1.0부터 보장** | 대입의 정의 + `range` 식이 한 번 평가된다 |
| 슬라이스 `range` 가 **기반 배열을 공유** | **1.0부터 보장** | 슬라이스가 descriptor 이기 때문이다([05번 주제](../05-arrays-vs-slices-value-and-header/)) |
| **맵 순회 순서가 보장되지 않음** | **1.0부터 보장(없음의 보장)** | "The iteration order over maps is not specified" |
| **순회 중 지운 키는 안 나온다** | **1.0부터 보장** | "the corresponding iteration value will not be produced" |
| **순회 중 추가한 키가 나오나** | **보장이 아니다** | "may be produced … or may be skipped" |
| 문자열 `range` 가 **룬과 바이트 오프셋** | **1.0부터 보장** | 명세의 string range 문단 |
| 채널 `range` 가 **close 까지** | **1.0부터 보장** | "until the channel is closed" |
| **정수 `range`** | **1.22부터의 보장** | "[Go 1.22]" 표기 + 1.21에서의 컴파일 에러 |
| **함수 `range`** | **1.23부터의 보장** | 1.22에서의 컴파일 에러 |
| `yield` 가 `false` 를 돌려주면 **다시 부르면 안 된다** | **1.23부터의 보장** | "must not be called again" |
| `iter.Seq`·`slices.Collect`·`maps.Keys` 의 반복자 판 | **표준 라이브러리(1.23+)** | `iter` 패키지의 계약 |
| 값 변수를 안 받으면 배열 복사가 **지워지는가** | **구현 · 안 쟀다** | 어셈블리를 안 떴다 |
| `for i := range n` 이 3절 루프와 **같은 코드가 나는가** | **구현 · 안 쟀다** | 〃 |
| 반복자 호출이 **인라인되는가** | **구현 · 안 쟀다** | 〃 |

★ 이 주제의 결론은 「**`for` 의 꼴은 안 바뀌었고 `range` 가 받는 것이 넓어졌다**」이다.
그리고 **그 경계를 컴파일러가 직접 말해 준다** — 버전 표를 외울 필요가 없다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 컬렉션을 훑는다 | **`range`** | 인덱스 실수가 없다 |
| N번 돈다 | **`for i := range n`**(1.22+) | 의도가 그대로 읽힌다 |
| 길이가 루프 중에 변한다 | **인덱스 루프** | `range` 는 횟수를 미리 정한다 |
| 큰 배열을 훑는다 | **`range &arr`** 또는 슬라이스 | 배열 복사를 피한다 |
| 원소를 고친다 | **`for i := range s`** 뒤 `s[i]` | `v` 는 복사본이다 |
| 컬렉션이 아닌 것을 훑는다 | **반복자 함수**(1.23+) | 트리·페이지·스트림을 `for` 로 쓴다 |
| 반복자를 공개 API 로 낸다 | **`iter.Seq`/`Seq2`** | 시그니처에 이름이 붙는다 |
| 맵을 순서대로 본다 | **`slices.Sorted(maps.Keys(m))`** | 순서는 보장이 없다(09번 주제) |
| 채널을 훑는다 | **`for v := range ch`** + 보내는 쪽 `close` | 안 닫으면 막힌다 |
| 무한 루프 | **`for { }`** | `for true { }` 와 같다. `gofmt` 도 이쪽을 남긴다 |

판단 규칙 두 줄.

- **`range` 를 쓰기 전에 「이 피연산자는 값인가 참조인가」를 물어라.** 그 답이 (2)절 전부다.
- **루프 중에 컬렉션을 바꿀 생각이면 `range` 를 쓰지 마라.** 횟수가 이미 정해져 있다.

## 핵심 문장

- Go 의 반복문은 **`for` 하나**다. 세 절 중 무엇을 남기느냐로 세 꼴이 되고, `range` 절이 네 번째다.
- `range` 의 피연산자는 **배열·배열 포인터·슬라이스·문자열·맵·채널**(1.0) + **정수**(1.22) + **함수**(1.23)다.
- ★★ **`range` 는 피연산자를 시작 전에 한 번 값으로 든다.**
  배열이면 원소까지 복사되고 슬라이스면 헤더만 복사된다 — 그래서 같은 코드의 답이 갈린다.
- **`range` 는 시작할 때 횟수를 정한다.** 안에서 `append` 해도 안 늘고 잘라도 안 준다.
- ★★★ **반복자는 자료구조가 아니라 함수**다. `range` 가 `yield` 를 만들어 넘기고,
  몸통이 `break` 하면 **`yield` 가 `false` 를 돌려주며 반복자는 더 부르면 안 된다.**
- ★★ **에러 메시지가 판 경계를 직접 말한다** —
  `requires go1.22 or later (-lang was set to go1.21; check go.mod)`.
- **맵 순회 순서는 보장이 없다.** 지운 키가 안 나오는 것은 보장이고, 추가한 키는 보장이 아니다.
- **문자열 `range` 는 룬을 주고 인덱스는 바이트 오프셋**이다 — 회차 수와 `len` 이 다르다.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 14번)
- [13번 주제](../13-closures-variable-capture-and-loop-variable-change/)(클로저·루프 변수 의미 변경) —
  **그쪽은 「루프 변수가 몇 개인가」까지**, 여기는 **「`for` 가 몇 꼴이고 `range` 가 무엇을 받나」** 부터
- [05번 주제](../05-arrays-vs-slices-value-and-header/)(배열과 슬라이스) —
  **그쪽은 값과 헤더의 차이까지**, 여기는 **그 차이가 `range` 에서 드러나는 자리**부터
- [10번 주제](../10-strings-bytes-runes-and-utf8-iteration/)(문자열·`byte`·`rune`) —
  **문자열 `range` 가 룬을 주는 것의 정본**
- [09번 주제](../09-maps-declaration-comma-ok-delete-and-iteration-order/)(맵) —
  **맵 순회 순서 무작위화의 정본.** 여기서는 「그래서 정렬해서 찍는다」만
- [15번 주제](../15-switch-type-switch-fallthrough-labels-and-goto/)(`switch`·라벨·`goto`) — **라벨 `break`/`continue` 의 정본**
- [목록의 **29번 주제**](../29-channels-buffering-direction-close-range-and-nil/)(채널) — 채널 `range` 와 `close` 의 정본
- 목록의 **39번 주제**(`iter` 와 사용자 정의 반복자) — **`iter.Seq` 설계의 정본.**
  여기서는 `range` 가 그것을 받는다는 것까지만
- 목록의 **49번 주제**(`testing`·표 기반 테스트) — 표를 `range` 로 도는 관용구가 거기 있다
- [`../../../python/syntax/09-sequence-ops-and-slicing/`](../../../python/syntax/09-sequence-ops-and-slicing/) —
  **파이썬의 `for x in seq` 는 이터레이터 프로토콜**이고, Go 의 `range` 는 **키워드가 꼴마다 다른 일을 한다**
- [`../../../c/syntax/12-control-flow-and-switch/`](../../../c/syntax/12-control-flow-and-switch/) —
  **그쪽은 `for (;;)` 과 `while (1)` 을 어셈블리로 견주고**, 여기는 **그 둘이 아예 한 문법인 언어**다

## 용어 풀이

- **`range` 절(range clause)** — `for` 뒤의 `range E`. `E` 를 훑으며 값을 내놓는다.
- **반복자 함수(iterator function)** — `func(yield func(V) bool)` 꼴의 함수. 1.23부터 `range` 가 받는다.
- **`yield`** — `range` 가 만들어 반복자에게 넘기는 함수. 「이 값으로 몸통을 한 번 돌려 달라」는 뜻.
- **`iter.Seq[V]` · `iter.Seq2[K,V]`** — 반복자 함수 타입의 이름(1.23+). 값을 하나/둘 내놓는다.
- **3절 꼴(ForClause)** — `for init; cond; post`. 세 자리 전부 비울 수 있다.
- **무한 루프** — `for { }`. 명세가 `for true { }` 와 같다고 적는다.
- **바이트 오프셋** — 문자열 `range` 가 주는 첫 값. 룬 번호가 아니라 **바이트 위치**다.
- **`slices.Collect`** — 반복자를 슬라이스로 모으는 표준 함수(1.23+).
- **`slices.Sorted(maps.Keys(m))`** — 맵 키를 정렬해 얻는 관용구(1.23+).

---

## 더 들어가면

- 명세는 `for i, _ := range testdata.a` 같은 예제를 실으며 **"testdata.a is never evaluated;
  len(testdata.a) is constant"** 라고 적는다 — 배열 포인터의 `len` 이 **타입에서 나오므로**
  피연산자를 아예 안 읽는 자리가 있다. 이 문서는 **그 자리를 안 던졌다.**
- 정수 `range` 의 타입 규칙에는 구석이 하나 더 있다 — **반복 변수가 이미 있으면**
  그 변수의 타입이 반복값의 타입이 된다("if the iteration variable is preexisting …").
  이 문서는 `:=` 로 선언하는 쪽만 던졌다.
- 반복자를 **둘 이상 겹쳐 쓰는 것**(필터·맵 체이닝)은 함수가 함수를 감싸는 꼴이 된다.
  `iter` 패키지의 `Pull` 은 그 반대편이다 — **밀어 주는 반복자를 당겨 오는 쪽으로** 뒤집는다.
  정본은 목록의 **39번 주제**다.
- `range` 가 **타입 파라미터**를 받는 규칙이 따로 있다(제네릭). "all types in its type set must have
  the same underlying type …" — 37번 주제의 영역이다. **여기서는 안 던졌다.**
- `for` 의 세 절은 **전부 단순문(SimpleStmt)** 이라 `i, j = i+1, j-1` 같은 다중 대입도 들어간다.
  선언은 init 자리에서만 된다.

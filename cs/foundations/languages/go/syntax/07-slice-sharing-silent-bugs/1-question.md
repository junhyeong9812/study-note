# go/syntax/07 — 슬라이스 공유로 조용히 틀리는 자리 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> ★★ **이 주제의 문항은 대부분 「반환값」이 아니라 「그 뒤 원본」을 묻는다.**
> 반환값만 맞히면 절반만 맞힌 것이다. **반드시 원본까지 적어라.**
> ★ **`cap` 을 먼저 적어라** — 이 주제의 모든 갈림이 거기서 나온다.
> 소스는 전부 `go build -trimpath -o prog . && ./prog` 로 던졌다. 모듈 이름은 `ex` 다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★ `append` 한 줄 뒤의 `all` (예측)

```go
// t07a.go
package main

import "fmt"

func main() {
	all := []int{1, 2, 3, 4, 5, 6}
	head := all[:3]
	fmt.Printf("all  = %v\n", all)
	fmt.Printf("head = all[:3] = %v  len=%d cap=%d\n", head, len(head), cap(head))

	head = append(head, 99)

	fmt.Println()
	fmt.Println("head = append(head, 99) 한 뒤")
	fmt.Printf("head = %v\n", head)
	fmt.Printf("all  = %v   ← 4 가 99 로 덮였다\n", all)

	tail := all[3:]
	fmt.Printf("tail = all[3:] = %v\n", tail)
}
```

- `head` 의 `len`·`cap` 은 무엇인가?
- `append(head, 99)` 뒤 `head` 와 **`all`** 은 각각 무엇인가?
- `tail := all[3:]` 은 무엇으로 찍히는가?
- `go vet` 은 무엇이라고 하는가?

### 2. ★ 두 번 부른 결과가 같은가 (예측)

```go
// t07b.go
package main

import "fmt"

// addTag 는 받은 슬라이스 뒤에 0 을 하나 붙여 돌려준다.
func addTag(s []int) []int { return append(s, 0) }

func run(name string, all []int) {
	head := all[:2]
	fmt.Printf("%s\n", name)
	fmt.Printf("  부르기 전 all = %v  len=%d cap=%d   head = all[:2] = %v\n",
		all, len(all), cap(all), head)
	got := addTag(head)
	fmt.Printf("  addTag(head)  = %v\n", got)
	fmt.Printf("  부른 뒤   all = %v\n", all)
}

func main() {
	run("① head 뒤에 여유가 있는 경우 (cap 4)", []int{1, 2, 3, 4})
	fmt.Println()
	run("② head 뒤에 여유가 없는 경우 (cap 2)", []int{1, 2})
	fmt.Println()
	fmt.Println("같은 함수 · 같은 관용구인데 원본이 한쪽만 바뀐다. 갈린 것은 cap 하나다.")
}
```

- 두 경우의 **반환값**은 각각 무엇인가 — 같은가?
- 두 경우의 **부른 뒤 `all`** 은 각각 무엇인가 — 같은가?
- 갈린 원인을 한 낱말로 말하라.
- 이 차이가 **테스트에 어떤 함정**을 만드는가?

### 3. 지운 뒤 기반 배열은 어떤 상태인가 (예측)

```go
// t07c.go
package main

import "fmt"

func main() {
	s := []string{"a", "b", "c", "d"}
	i := 1
	fmt.Printf("지우기 전 s = %v  len=%d cap=%d\n", s, len(s), cap(s))

	out := append(s[:i], s[i+1:]...)

	fmt.Printf("append(s[:1], s[2:]...) = %v  len=%d cap=%d\n", out, len(out), cap(out))
	fmt.Printf("원본 배열을 cap 까지 펴 보면 %v   ← 끝에 \"d\" 가 남아 있다\n", out[:cap(out)])
	fmt.Printf("s 라는 이름으로는 %v  (s 의 len 은 그대로 4 다)\n", s)
	fmt.Println()
	fmt.Println("s 와 out 의 첫 칸이 같은 자리인가 :", &s[0] == &out[0])
}
```

- `out` 은 무엇이고 `len`·`cap` 은 무엇인가?
- `out[:cap(out)]` 은 무엇으로 찍히는가?
- `s` 라는 이름으로 찍으면 무엇이 나오는가 — 왜 `out` 과 다른가?
- 원소가 **포인터**였다면 무엇이 더 나빠지는가?

### 4. 거르고 나면 원본은 (예측)

```go
// t07d.go
package main

import "fmt"

// keepEven 은 짝수만 남긴다 — 널리 쓰이는 「할당 없는 필터」 관용구다.
func keepEven(s []int) []int {
	out := s[:0]
	for _, v := range s {
		if v%2 == 0 {
			out = append(out, v)
		}
	}
	return out
}

func main() {
	src := []int{1, 2, 3, 4, 5, 6}
	fmt.Printf("거르기 전 src = %v\n", src)

	even := keepEven(src)

	fmt.Printf("돌려받은 것    = %v\n", even)
	fmt.Printf("거른 뒤 src    = %v   ← 원본이 짓이겨졌다\n", src)
	fmt.Printf("배열 전체      = %v\n", even[:cap(even)])
	fmt.Println("같은 배열인가  :", &src[0] == &even[0])
}
```

- `keepEven(src)` 의 반환값은 무엇인가?
- **그 뒤 `src`** 는 무엇인가?
- `&src[0] == &even[0]` 은 무엇인가?
- 이 관용구는 틀린 것인가 — 언제 쓰면 되나?

### 5. ★★ 네 도구 중 몇 개가 이 버그를 잡나 (예측)

```go
// t07e.go
package main

import "fmt"

// Prefix 는 앞 n 개만 남기고 뒤에 표식 0 을 하나 붙여 돌려준다.
func Prefix(s []int, n int) []int {
	return append(s[:n], 0)
}

func main() {
	data := []int{1, 2, 3, 4, 5}
	got := Prefix(data, 2)
	fmt.Println("Prefix(data, 2) =", got)
	fmt.Println("그 뒤 data      =", data)
}
```

```go
// t07e_test.go
package main

import "testing"

func TestPrefix(t *testing.T) {
	got := Prefix([]int{1, 2, 3, 4, 5}, 2)
	want := []int{1, 2, 0}
	if len(got) != len(want) {
		t.Fatalf("len(got) = %d, want %d", len(got), len(want))
	}
	for i := range want {
		if got[i] != want[i] {
			t.Fatalf("got[%d] = %d, want %d", i, got[i], want[i])
		}
	}
}
```

- `go build`·`go vet`·`go test`·`go test -race` 의 **종료 코드**는 각각 무엇인가?
- `./prog` 의 두 줄은 각각 무엇인가?
- 테스트가 통과한 이유를 **계약**이라는 낱말로 설명하라.
- `-race` 가 통과하는 이유는 무엇인가?

### 6. 구조체를 복사하면 어디까지 갈리나 (예측)

```go
// t07f.go
package main

import "fmt"

// Doc 은 문자열 하나와 슬라이스 하나를 가진 평범한 구조체다.
type Doc struct {
	Name string
	Tags []string
}

func main() {
	a := Doc{Name: "원본", Tags: []string{"x", "y"}}
	b := a

	b.Name = "복사본"
	b.Tags[0] = "바뀜"

	fmt.Printf("a = %+v\n", a)
	fmt.Printf("b = %+v\n", b)
	fmt.Println("Name 은 갈렸고 Tags 는 같이 바뀌었다 :", a.Name != b.Name, "/", a.Tags[0] == b.Tags[0])

	b.Tags = append(b.Tags, "z")
	fmt.Println()
	fmt.Println("b.Tags 에 append 한 뒤")
	fmt.Printf("a.Tags = %v (len=%d cap=%d)\n", a.Tags, len(a.Tags), cap(a.Tags))
	fmt.Printf("b.Tags = %v (len=%d cap=%d)\n", b.Tags, len(b.Tags), cap(b.Tags))
	fmt.Println("append 는 b.Tags 만 새 배열로 옮겼다 — 공유가 거기서 끊겼다")
}
```

- `b := a` 뒤 `b.Name`·`b.Tags[0]` 을 고치면 `a` 는 각각 어떻게 되는가?
- `b.Tags` 에 `append` 한 뒤 `a.Tags` 와 `b.Tags` 의 `len`·`cap` 은?
- 같은 필드가 **어느 시점부터 공유가 아니게** 되는가?
- 이 구조체를 `==` 로 비교하면 어떻게 되는가 — 메시지 전문은?

### 7. 왜 `go vet` 도 `-race` 도 못 잡나 (왜)

- 이 버그는 명세를 어겼는가?
- `-race` 가 보는 것은 무엇인가 — 이 버그가 왜 그 범위 밖인가?
- `go vet` 에 이런 검사를 넣기 어려운 이유를 하나 대라.
- 그러면 무엇으로 막아야 하는가?

### 8. 맵에서 꺼내 붙이면 (경계)

```go
// t07g.go
package main

import "fmt"

func main() {
	m := map[string][]int{"k": {1, 2, 3}}

	s := m["k"]
	s = append(s, 4)
	fmt.Println("s = append(m[\"k\"], 4) 한 뒤 m[\"k\"] =", m["k"], " s =", s)

	m["k"] = append(m["k"], 4)
	fmt.Println("m[\"k\"] = append(...) 로 다시 넣으면 m[\"k\"] =", m["k"])

	m["k"][0] = 99
	fmt.Println("m[\"k\"][0] = 99 는 그냥 된다        m[\"k\"] =", m["k"])

	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	fmt.Println("맵의 키(정렬하지 않아도 하나뿐이다) :", keys)
}
```

- `s := m["k"]; s = append(s, 4)` 뒤 `m["k"]` 는 무엇인가?
- `m["k"][0] = 99` 는 되는가 — 왜 `append` 와 갈리는가?
- 이 구조는 05번 주제의 무엇과 같은 모양인가?
- 키가 여럿이었다면 이 프로그램의 마지막 줄을 어떻게 고쳐야 하는가?

### 9. 어느 칸이 명세이고 어느 칸이 도구의 사정인가 (경계)

아래 여섯 가지를 **「명세 보장」 / 「구현·도구의 사정」** 으로 갈라라.

- ① `cap` 이 남으면 `append` 가 기반 배열을 재사용한다
- ② `s[:3]` 의 `cap` 이 6이다
- ③ `go vet` 이 이 버그를 한 줄도 안 말한다
- ④ 슬라이스 필드가 있는 구조체를 `==` 로 못 비교한다
- ⑤ `append` 뒤 `cap` 이 2에서 4가 된다
- ⑥ `go test -race` 가 통과한다

### 10. 다른 언어와 나란히 놓기 (연결)

- Rust 에서 같은 모양의 코드를 쓰면 무엇이 일어나는가 — 무엇이 막는가?
- 파이썬에서 `head = all[:3]` 뒤 `head.append(99)` 를 하면 `all` 은 어떻게 되는가?
- 셋 중 **사람이 규칙을 외워야만 하는** 언어는 어느 것인가 — 왜인가?
- Go 가 그 대신 얻은 것은 무엇인가?

### 11. 다른 주제와 잇기 (연결)

- 「`cap` 이 남으면 재사용한다」는 사실의 정본은 몇 번 주제인가?
- 막는 법(`s[:n:n]`·`copy`)의 정본은 몇 번 주제인가?
- 조용한 실패의 총론은 어느 갈래인가?
- `-race` 가 실제로 무엇을 잡는지의 정본은 몇 번 주제인가?
- 「인자가 안 바뀌었나」를 표 기반 테스트로 쓰는 법의 정본은 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

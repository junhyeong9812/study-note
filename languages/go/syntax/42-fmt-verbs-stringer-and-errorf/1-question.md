# go/syntax/42 — `fmt`: 포맷 동사·`Stringer`·`Errorf` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ **모든 문제에서 「이 동작은 명세인가, `fmt` 문서의 계약인가, 이 판의 구현인가」를 먼저 적어라.**
> ★★ 출력에 **주소**가 찍히는 칸은 흔들린다 — 그 칸은 「주소」라고만 답하면 된다.
> 모든 실험은 `module ex` · `go 1.27` 이고 `go build -trimpath` 로 빌드해 돌렸다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 메서드 없는 값에 동사를 바꿔 가며 (예측)

```go
// t42grid.go
package main

import (
	"fmt"
	"os"
	"strings"
)

// calls 는 String()·Error() 가 불린 횟수다.
var calls int

type P struct {
	X    int
	Name string
}

type Outer struct {
	In  P
	Ptr *P
}

// V 는 값 리시버로 String 을 가진다.
type V struct{ N int }

func (v V) String() string { calls++; return fmt.Sprintf("V<%d>", v.N) }

// PR 은 포인터 리시버로 String 을 가진다.
type PR struct{ N int }

func (p *PR) String() string { calls++; return fmt.Sprintf("PR<%d>", p.N) }

// E 는 Error 를 가진다.
type E struct{ Msg string }

func (e E) Error() string { calls++; return "E: " + e.Msg }

// Emb 는 V 를 임베딩한다.
type Emb struct {
	V
	Extra int
}

// Hold 는 같은 타입의 필드를 공개·비공개로 하나씩 가진다.
type Hold struct {
	Pub  V
	priv V
}

func main() {
	vals := []struct {
		id  string
		arg any
	}{
		{"v01 P{1,a}", P{1, "a"}},
		{"v02 &P{1,a}", &P{1, "a"}},
		{"v03 Outer", Outer{P{1, "a"}, &P{2, "b"}}},
		{"v04 (*P)(nil)", (*P)(nil)},
		{"v05 map", map[string]int{"b": 2, "a": 1, "c": 3}},
		{"v06 []int", []int{1, 2}},
		{"v07 E", E{"boom"}},
		{"v08 V{7}", V{7}},
		{"v09 &V{7}", &V{7}},
		{"v10 PR{7}", PR{7}},
		{"v11 &PR{7}", &PR{7}},
		{"v12 Emb", Emb{V{7}, 9}},
		{"v13 Hold", Hold{V{1}, V{2}}},
	}
	verbs := []string{"%v", "%+v", "%#v", "%T", "%s", "%d"}
	hit, all := 0, 0
	matrix := []string{}
	for _, v := range vals {
		line := fmt.Sprintf("%-14s", v.id)
		for _, verb := range verbs {
			before := calls
			out := fmt.Sprintf(verb, v.arg)
			n := calls - before
			all++
			if n > 0 {
				hit++
			}
			row := strings.Join([]string{v.id, verb, out, fmt.Sprint(n)}, "\t")
			if strings.Count(row, "\t") != 3 {
				fmt.Fprintln(os.Stderr, "칸 수 어긋남:", row)
				os.Exit(1)
			}
			fmt.Println(row)
			line += fmt.Sprintf(" %s=%d", verb, n)
		}
		matrix = append(matrix, line)
	}
	fmt.Println("── 칸마다 String()·Error() 가 불린 횟수 ──")
	for _, l := range matrix {
		fmt.Println(l)
	}
	fmt.Printf("String()·Error() 가 불린 칸 %d / %d\n", hit, all)
}
```

<!-- go vet . 을 돌리고, 빌드해 실행한다. 프로그램은 칸마다 「값 · 동사 · 출력 · String()/Error() 가 불린 횟수」를 탭으로 찍고, 끝에 행렬과 합계를 찍는다. -->

- `v01`\~`v06` 의 `%v`·`%+v`·`%#v`·`%T` 는 각각 무엇을 찍나? 특히 `v03 Outer` 의 `Ptr` 필드와 `v05` 맵의 키 순서는?
- `v01` 의 `%s` 와 `%d` 는?
- `go vet` 은 이 프로그램에 대해 무엇이라 말하나?

### 2. `String()`·`Error()` 를 가진 값들 (예측)

- 같은 프로그램의 `v07`\~`v13` 에서 **`String()`/`Error()` 가 불리는 동사**는 어느 것인가? 한 칸도 안 불리는 값이 있나?
- `v12 Emb` 의 `%v` 에 `Extra` 가 보이나? `v13 Hold` 의 `%v` 는?
- 마지막 줄의 수는?

### 3. `PR{7}` 과 `&PR{7}` (왜)

- 둘은 같은 타입 `PR` 의 값인데 왜 한쪽만 `String()` 이 불리나? 에러나 경고가 나오나([19번 주제](../19-method-sets-value-vs-pointer-receiver/))?

### 4. `Hold` 의 두 필드 (왜)

- `Hold{Pub V; priv V}` 에서 `priv` 의 `String()` 이 안 불린 이유는? [40번 주제](../40-package-visibility-naming-and-internal/) (4)절의 `encoding/json` 과 무엇이 같은가?

### 5. `String()` 이 자기 자신을 `%v` 로 (예측)

```go
// t42rec.go
package main

import "fmt"

type T struct{ N int }

// String 이 자기 자신을 %v 로 찍는다.
func (t T) String() string { return fmt.Sprintf("T(%v)", t) }

func main() {
	fmt.Println("시작")
	fmt.Println(T{1})
	fmt.Println("끝")
}
```

<!-- go vet . 을 돌리고(실패해도 계속), 빌드해 stdout 과 stderr 를 따로 받는다. stderr 는 줄 수와 첫 세 줄, 생략 표시, 프레임 이름 앞 열넷만 찍는다. -->

- `go vet` 의 말과 `exit` 는? 실행의 `exit` 와 stdout 은?
- `main` 에 `defer func(){ fmt.Println("recover:", recover()) }()` 를 걸면 `recover:` 줄이 찍히나?

### 6. 재귀를 끊는 두 형태 (예측)

```go
// t42fix.go
package main

import "fmt"

type T struct{ N int }

// 메서드가 없는 새 타입으로 바꿔 찍는다.
func (t T) String() string {
	type raw T
	return fmt.Sprintf("T%v", raw(t))
}

type Q struct{ N int }

// 포인터 리시버 안에서 값(*q)을 찍는다.
func (q *Q) String() string { return fmt.Sprintf("Q%v", *q) }

func main() {
	fmt.Println(T{1})
	fmt.Println(&Q{2})
}
```

- 두 줄의 출력은? `go vet` 은 무엇이라 말하나?
- `Q` 쪽은 `String()` 안에서 `*q` 를 `%v` 로 찍는데 왜 5번처럼 재귀하지 않나?

### 7. 잘못 쓴 동사들 (예측)

```go
// t42bad.go
package main

import (
	"errors"
	"fmt"
)

func main() {
	fmt.Printf("b1 %d\n", "hi")
	fmt.Printf("b2 %v %v\n", 1)
	fmt.Printf("b3 %v\n", 1, 2)
	fmt.Printf("b4 %z\n", 1)
	fmt.Printf("b5 %w\n", errors.New("x"))
	err := fmt.Errorf("b6 감쌈: %w", "문자열")
	fmt.Println(err, errors.Unwrap(err) == nil)
}
```

<!-- go vet . 의 출력을 받아 짚은 줄 수를 세고, 빌드해 실행한다. -->

- `vet` 은 몇 줄을 짚나?
- 실행 출력은? `b3` 과 `b4` 는 각각 어느 줄에 찍히나? 마지막 `true`/`false` 는?

### 8. 1번 격자의 `%s`·`%d` 칸과 `vet` (경계)

- 1번의 `v01 %s` 는 7번의 `b1` 과 **같은 종류의 실수**다. 그런데 1번에서 `vet exit=0` 인 이유는? `vet` 의 `printf` 검사가 **볼 수 있는 것의 경계**는?

### 9. `%w` 를 여러 개 쓰면 (연결)

- [24번 주제](../24-error-wrapping-and-errors-is-as-join/) (6)절에서 `fmt.Errorf("…: %w / %w", ErrA, ErrB)` 의 `%T` 와 `errors.Unwrap` 결과는 무엇이었나? 7번의 `b6` 과 무엇이 다른가?

### 10. `nil` 포인터에 `String()` (연결)

- 1번의 `v04 (*P)(nil)` 은 `%v` 가 `<nil>` 이다. **`String()` 이 있는 타입**의 `nil` 포인터라면 `fmt` 는 무엇을 하나([21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/))?

### 11. `v05` 맵 출력의 근거 (경계)

- 1번의 `v05` 가 `map[a:1 b:2 c:3]` 으로 찍히는 것은 **명세·`fmt` 문서·구현** 중 어디에 적혀 있나? [09번 주제](../09-maps-declaration-comma-ok-delete-and-iteration-order/)는 무엇이라 적었나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

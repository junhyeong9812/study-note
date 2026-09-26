# go/syntax/49 — `testing`: 표 기반 테스트·`t.Run`·`t.Cleanup`·`t.Parallel` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ **모든 문제에서 「이 동작은 명세인가, `testing` 문서의 계약인가, 도구(`go` 명령) 판의 성질인가」를 먼저 적어라.**
> 모든 실험은 `module ex`(`go 1.27`) 이고 `go1.27.1` 에서 돌렸다. 테스트는 `go test -c -o t.test .` 로 만든 바이너리를 `./t.test` 로 돌렸다(따로 적은 곳 빼고).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 네 행짜리 표 (예측)

```go
// t49table_test.go
package ex

import "testing"

func abs(x int) int {
	if x < -1 {
		return -x
	}
	return x
}

func TestAbs(t *testing.T) {
	tests := []struct {
		name string
		in   int
		want int
	}{
		{"pos", 2, 2},
		{"zero", 0, 0},
		{"neg1", -1, 1},
		{"neg2", -2, 2},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := abs(tt.in); got != tt.want {
				t.Errorf("abs(%d) = %d, want %d", tt.in, got, tt.want)
			}
		})
	}
}
```

<!-- go vet . 뒤에 go test -count=1 . 을 돌리고, 따로 ./t.test -test.v 도 돌렸다. -->

- `go test -count=1 .` 은 무엇을 찍고 종료 코드는 몇인가? 틀린 행이 있으면 **어느 이름**으로 보고되고, 그 뒤 행은 도나? `-test.v` 로 돌리면 무엇이 더 보이나?

### 2. 정리 순서 — 아홉 질문과 세 판 (예측)

```go
// t49order_test.go
package ex

import (
	"fmt"
	"os"
	"sync"
	"testing"
)

var (
	mu  sync.Mutex
	log []string
)

func rec(s string) {
	mu.Lock()
	log = append(log, s)
	mu.Unlock()
}

// PAR=1 이면 하위 s2·s3 가 t.Parallel() 을 부른다.
// GROUP=1 이면 하위 셋을 t.Run("group", …) 하나로 한 번 더 감싼다.
var (
	par   = os.Getenv("PAR") == "1"
	group = os.Getenv("GROUP") == "1"
)

func TestParent(t *testing.T) {
	defer rec("P.defer")
	t.Cleanup(func() { rec("P.cleanup1") })
	t.Cleanup(func() { rec("P.cleanup2") })
	subs := func(t *testing.T) {
		for _, name := range []string{"s1", "s2", "s3"} {
			t.Run(name, func(t *testing.T) {
				if name != "s1" && par {
					t.Parallel()
				}
				defer rec(name + ".defer")
				t.Cleanup(func() { rec(name + ".cleanup") })
				rec(name + ".body")
			})
		}
	}
	if group {
		t.Run("group", subs)
	} else {
		subs(t)
	}
	rec("P.return")
}

func pos(s string) int {
	for i, v := range log {
		if v == s {
			return i
		}
	}
	return -1
}

func TestMain(m *testing.M) {
	code := m.Run()
	before := func(a, b string) bool { return pos(a) < pos(b) }
	for _, q := range [][2]string{
		{"P.return", "s2.body"},
		{"P.defer", "s2.body"},
		{"P.defer", "s3.cleanup"},
		{"s1.cleanup", "s2.body"},
		{"s2.defer", "s2.cleanup"},
		{"s2.cleanup", "P.cleanup1"},
		{"s3.cleanup", "P.cleanup2"},
		{"P.cleanup2", "P.cleanup1"},
		{"P.defer", "P.cleanup2"},
	} {
		fmt.Printf("%s 가 %s 보다 먼저\t%v\n", q[0], q[1], before(q[0], q[1]))
	}
	if !par && !group {
		fmt.Println("순서:", log)
	}
	os.Exit(code)
}
```

<!-- 한 바이너리를 세 번 돌렸다 — 판 1: 환경 변수 없음 · 판 2: PAR=1 · 판 3: PAR=1 GROUP=1. 판 1 은 기록 전체(순서: …)도 찍는다. 아홉 줄을 판마다 나란히 놓고, 판 1 과 판 2 · 판 1 과 판 3 이 갈린 칸을 센다. -->

- 판 1 의 `순서:` 줄은? 아홉 질문 각각의 판 1·2·3 값은? 마지막 두 줄의 수는?

### 3. 부모의 `defer` 로 닫은 임시 서버 (왜)

- 2번 판 2 의 모양에서 부모 테스트가 `srv := httptest.NewServer(…)` 뒤 `defer srv.Close()` 를 두고, 병렬 하위들이 `srv.URL` 로 요청한다. **무엇이 일어나고 왜인가?** 두 가지 고치는 법을 2번의 결과로 대라.

### 4. 두 파일, 같은 루프 (예측)

```text
===== 소스: cases_test.go =====
package ex

import (
	"fmt"
	"os"
	"sort"
	"sync"
	"testing"
)

type tcase struct {
	name string
	in   int
}

var cases = []tcase{{"a", 1}, {"b", 2}, {"c", 3}}

var (
	mu   sync.Mutex
	seen = map[string]string{}
)

// see 는 하위 테스트 이름과 그 하위 테스트가 읽은 tc.name 을 적는다.
func see(t *testing.T, got string) {
	mu.Lock()
	seen[t.Name()] = got
	mu.Unlock()
}

func TestMain(m *testing.M) {
	code := m.Run()
	keys := make([]string, 0, len(seen))
	for k := range seen {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	for _, k := range keys {
		fmt.Printf("%s\t%s\n", k, seen[k])
	}
	os.Exit(code)
}
===== 소스: go.mod =====
module ex

go 1.27
===== 소스: new_test.go =====
package ex

import "testing"

func TestNew(t *testing.T) {
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()
			see(t, tc.name)
		})
	}
}
===== 소스: old_test.go =====
//go:build go1.21

package ex

import "testing"

func TestOld(t *testing.T) {
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()
			see(t, tc.name)
		})
	}
}
```

<!-- go vet . · go test -count=1 -run "^$" . (vet 부분 집합만) · 바이너리 실행을 차례로 했다. 하위 이름마다 두 파일의 하위가 본 tc.name 을 나란히 놓는다. -->

- `go vet` 과 `go test(-run ^$)` 의 종료 코드는? 하위 `a`·`b`·`c` 가 두 파일에서 각각 본 값은? 테스트는 통과하나?

### 5. `vet` 은 잡았는데 `go test` 는 통과 (왜)

- 4번에서 `go vet` 과 `go test` 가 다른 답을 낸 **두 가지 이유**는? 이 모듈의 `go.mod` 를 `go 1.21` 로 내리면 두 파일 중 **어느 쪽**의 결과가 바뀌나?

### 6. 다른 고루틴에서 `t.Fatal` (예측)

```go
// t49gor_test.go
package ex

import "testing"

func TestG(t *testing.T) {
	done := make(chan struct{})
	go func() {
		defer close(done)
		t.Fatal("in goroutine")
		t.Log("goroutine: after Fatal")
	}()
	<-done
	t.Log("test: after <-done")
}
```

- `go vet` 은 무엇을 말하나? `./t.test -test.v` 의 출력에 `goroutine: after Fatal` 과 `test: after <-done` 중 **무엇이** 찍히나? 테스트 결과와 종료 코드는?

### 7. 필터 · 건너뛰기 · 섞기 (예측)

```go
// t49run_test.go
package ex

import "testing"

func TestA(t *testing.T) {
	for _, n := range []string{"x1", "x2", "y1"} {
		t.Run(n, func(t *testing.T) { t.Log("ran", t.Name()) })
	}
}

func TestB(t *testing.T) {
	t.Skip("skip reason")
	t.Log("TestB: after Skip")
}

func TestC(t *testing.T) {}

func TestD(t *testing.T) {}
```

<!-- ./t.test 를 -test.run "A/1" · -test.run "B" · -test.shuffle=1 · =2 · =1 로 돌렸다(모두 -test.v). -->

- `-test.run "A/1"` 은 어떤 테스트를 돌리나? `-test.run "B"` 의 출력에서 `TestB: after Skip` 은 찍히나? `-test.shuffle` 은 **무엇을** 섞고, 같은 씨앗을 두 번 주면?

### 8. `t.Cleanup` 과 `defer` 를 가르는 두 축 (경계)

- 헬퍼 함수 `newTempDB(t)` 가 DB 를 열고 닫는 일까지 맡으려면 왜 `defer` 가 아니라 `t.Cleanup` 이어야 하나? 2번 판 1 에서 둘이 같이 있을 때 **어느 쪽이 먼저** 도나?

### 9. `tc := tc` 는 아직 필요한가 (연결)

- [13번 주제](../13-closures-variable-capture-and-loop-variable-change/)의 「1.22 부터 `i := i` 를 다 지워도 되나」와 4번은 어떻게 이어지나? 표 기반 병렬 테스트에서 `tc := tc` 를 지워도 되는 **조건**은?

### 10. 통과한 테스트가 말하지 않는 것 (경계)

- 4번의 go1.21 파일은 `PASS` 였다. 이 테스트가 **틀린 값을 봤는데도** 통과한 이유는? 같은 실수를 테스트가 스스로 잡게 하려면 몸통에 무엇이 있어야 하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

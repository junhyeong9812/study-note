# go/syntax/49 — `testing`: 표 기반 테스트·`t.Run`·`t.Cleanup`·`t.Parallel` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★ **근거로 읽을 칸** — 정리 순서 격자의 참/거짓 · `3 / 9` · `0 / 9` · 두 파일 격자 · `vet` 문구 · 종료 코드 · `--- FAIL:` 이름.
> **흔들리는 칸** — `(0.00s)` · `ok`/`FAIL` 줄의 시간.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `--- FAIL: TestAbs/neg1` 하나 · `go test exit=1` · `neg2` 도 돌았다 — `-test.v` 면 `--- PASS:` 셋이 더 보인다

**출력**

```text
===== 소스: t49table_test.go =====
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
===== 명령: go vet . ; echo "vet exit=$?"; go test -count=1 . ; echo "go test exit=$?" =====
vet exit=0
--- FAIL: TestAbs (0.00s)
    --- FAIL: TestAbs/neg1 (0.00s)
        t49table_test.go:26: abs(-1) = -1, want 1
FAIL
FAIL	ex	0.005s
FAIL
go test exit=1
(exit 0)
```

```text
===== 소스: t49table_test.go =====
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
===== 명령: go test -c -o t.test . || exit 1; ./t.test -test.v; echo "test exit=$?" =====
=== RUN   TestAbs
=== RUN   TestAbs/pos
=== RUN   TestAbs/zero
=== RUN   TestAbs/neg1
    t49table_test.go:26: abs(-1) = -1, want 1
=== RUN   TestAbs/neg2
--- FAIL: TestAbs (0.00s)
    --- PASS: TestAbs/pos (0.00s)
    --- PASS: TestAbs/zero (0.00s)
    --- FAIL: TestAbs/neg1 (0.00s)
    --- PASS: TestAbs/neg2 (0.00s)
FAIL
test exit=1
(exit 0)
```

**왜 그런가**

- ★★ 실패는 **표의 `name`** 으로 보고된다(`TestAbs/neg1`). `abs` 의 조건이 `x < -1` 이라 `-1` 만 틀렸다.
- ★★ `t.Errorf` 는 **표시만** 하고 멈추지 않는다 — 그리고 하위마다 고루틴이 따로라 `t.Fatalf` 였어도 **다음 행은 돈다**(문서 「It runs f in a separate goroutine」).
- ★ `-test.v` 의 `--- PASS: TestAbs/neg2` 가 「뒤 행도 돌았다」의 증거다.

### 2. 판 1 순서 `s1.body s1.defer s1.cleanup s2… s3… P.return P.defer P.cleanup2 P.cleanup1` · 판 2 는 **위 세 칸**(`P.return`·`P.defer` 가 `s2.body` 보다 먼저 · `P.defer` 가 `s3.cleanup` 보다 먼저)이 뒤집힌다 · 판 3 은 판 1 과 같다 — `3 / 9` · `0 / 9`

**출력**

```text
===== 명령: go vet . ; echo "vet exit=$?"; go test -c -o t.test . || exit 1; ./t.test > a.txt; ra=$?; PAR=1 ./t.test > b.txt; rb=$?; PAR=1 GROUP=1 ./t.test > c.txt; rc=$?; echo "exit — 판 1: $ra · 판 2: $rb · 판 3: $rc"; grep "^순서" a.txt; printf "질문\t판 1 Parallel 없음\t판 2 Parallel 있음\t판 3 Parallel 있음 + group\n"; paste <(grep -P "\t" a.txt) <(grep -P "\t" b.txt) <(grep -P "\t" c.txt) | awk -F"\t" "NF!=6 || \$1!=\$3 || \$1!=\$5 {bad=1} {printf \"%s\t%s\t%s\t%s\n\", \$1, \$2, \$4, \$6; m++; if (\$2!=\$4) n++; if (\$2!=\$6) k++} END {if (bad) print \"칸 수 어긋남\"; printf \"판 1 과 판 2 가 갈린 칸 %d / %d\n판 1 과 판 3 이 갈린 칸 %d / %d\n\", n, m, k, m}" =====
vet exit=0
exit — 판 1: 0 · 판 2: 0 · 판 3: 0
순서: [s1.body s1.defer s1.cleanup s2.body s2.defer s2.cleanup s3.body s3.defer s3.cleanup P.return P.defer P.cleanup2 P.cleanup1]
질문	판 1 Parallel 없음	판 2 Parallel 있음	판 3 Parallel 있음 + group
P.return 가 s2.body 보다 먼저	false	true	false
P.defer 가 s2.body 보다 먼저	false	true	false
P.defer 가 s3.cleanup 보다 먼저	false	true	false
s1.cleanup 가 s2.body 보다 먼저	true	true	true
s2.defer 가 s2.cleanup 보다 먼저	true	true	true
s2.cleanup 가 P.cleanup1 보다 먼저	true	true	true
s3.cleanup 가 P.cleanup2 보다 먼저	true	true	true
P.cleanup2 가 P.cleanup1 보다 먼저	true	true	true
P.defer 가 P.cleanup2 보다 먼저	true	true	true
판 1 과 판 2 가 갈린 칸 3 / 9
판 1 과 판 3 이 갈린 칸 0 / 9
(exit 0)
```

**왜 그런가**

- ★★★ 문서 — `Run` 은 「blocks until f returns **or calls t.Parallel**」. 판 2 에서 `s2`·`s3` 의 `Run` 이 곧바로 돌아와 **부모 함수가 반환하고 `defer` 가 돈 뒤에** 병렬 하위가 풀려난다.
- ★★★ `Cleanup` 은 「when the test (or subtest) **and all its subtests** complete」 — 판 2 에서도 `P.cleanup*` 은 하위 `cleanup` 뒤다. 「last added, first called」라 `cleanup2 → cleanup1`.
- ★★ 판 3 — `group` 도 하위라 **하위를 가진 하위는 그 하위가 끝나야 끝난다** → 바깥 `Run` 이 병렬 하위를 기다린다 → `P.defer` 가 다시 맨 뒤로.

### 3. 병렬 하위가 **이미 닫힌 서버**에 요청한다 — 부모의 `defer` 가 병렬 하위보다 먼저 돌기 때문이다(2번 판 2) · 고치는 법 ① `t.Cleanup(srv.Close)` ② 하위들을 `t.Run("group", …)` 으로 감싼 뒤 `defer`

- ★★★ 2번의 판 2 — `P.defer 가 s2.body 보다 먼저 true`. 판 2 의 `P.cleanup*` 은 하위 뒤 · 판 3 은 `0 / 9`.
- ★★ 이 문서는 **`httptest` 서버로 직접 돌려 보지는 않았다** — 2번의 순서 기록에서 따라 나오는 결론이다. 증상은 대개 `connection refused` 이고, 예외도 컴파일 에러도 없다.

### 4. `go vet exit=1`(`loop variable tc captured by func literal` — `old_test.go` 만) · `go test(-run ^$) exit=0` · go1.21 파일은 `c c c`, go1.22+ 파일은 `a b c` · 테스트는 **통과**(`test exit=0`) — 「두 파일이 갈린 칸 2 / 3」

**출력**

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
===== 명령: go vet . ; echo "go vet exit=$?"; go test -count=1 -run "^$" . > /dev/null 2>&1; echo "go test(-run ^$) exit=$?"; go test -c -o t.test . || exit 1; ./t.test > r.txt; echo "test exit=$?"; printf "하위 테스트\tgo1.21 파일(TestOld)\tgo1.22+ 파일(TestNew)\n"; paste <(grep "^TestOld/" r.txt) <(grep "^TestNew/" r.txt) | awk -F"\t" "{split(\$1, a, \"/\"); split(\$3, b, \"/\")} NF!=4 || a[2]!=b[2] {bad=1} {printf \"%s\t%s\t%s\n\", a[2], \$2, \$4; m++; if (\$2!=\$4) n++; if (\$2!=a[2]) o++} END {if (bad) print \"칸 수 어긋남\"; printf \"두 파일이 갈린 칸 %d / %d\ngo1.21 파일에서 자기 케이스가 아닌 것을 본 칸 %d / %d\n\", n, m, o, m}" =====
old_test.go:11:11: loop variable tc captured by func literal
go vet exit=1
go test(-run ^$) exit=0
test exit=0
하위 테스트	go1.21 파일(TestOld)	go1.22+ 파일(TestNew)
a	c	a
b	c	b
c	c	c
두 파일이 갈린 칸 2 / 3
go1.21 파일에서 자기 케이스가 아닌 것을 본 칸 2 / 3
(exit 0)
```

**왜 그런가**

- ★★★ 병렬 하위는 부모가 반환한 뒤 풀려난다(2번). go1.21 의미의 `tc` 는 **루프 하나에 변수 하나**라 그때 이미 마지막 값 `c` 다. 1.22+ 는 회차마다 새 `tc`.
- ★★ 이름(`TestOld/a`)은 **`Run` 을 부르는 순간** 읽혀서 제대로다 — 출력의 이름만 보면 멀쩡하다.

### 5. ① `go test` 는 `vet` 의 **일부**(「high-confidence subset」)만 돌리고 `loopclosure` 는 거기 없다 · ② 테스트 몸통이 **아무것도 검사하지 않는다** · `go 1.21` 로 내리면 **`new_test.go` 쪽**이 바뀐다(`old_test.go` 는 이미 1.21)

**출력**

```text
===== 명령: printf "module ex\n\ngo 1.21\n" > go.mod; go vet . ; echo "go vet exit=$?"; go test -c -o t.test . || exit 1; ./t.test | grep /; echo "test exit=$?" =====
new_test.go:9:11: loop variable tc captured by func literal
old_test.go:11:11: loop variable tc captured by func literal
go vet exit=1
TestNew/a	c
TestNew/b	c
TestNew/c	c
TestOld/a	c
TestOld/b	c
TestOld/c	c
test exit=0
(exit 0)
```

- ★★★ `go.mod` 를 `go 1.21` 로 내리니 `vet` 이 **두 파일 다** 짚고, `TestNew` 도 **`c c c`** 가 됐다 — `//go:build go1.21` 이 없는 파일은 **`go.mod` 의 `go` 줄**을 따른다(13번 (2)·(3)절).
- ★★ `go test` 가 도는 목록은 [52번 주제](../52-tools-gofmt-vet-build-tags-embed-and-escape-analysis/) (2)절의 `go help test` 블록에 있다.

### 6. `vet` — `call to (*testing.T).Fatal from a non-test goroutine`(exit 1) · `test: after <-done` **만** 찍힌다 · `--- FAIL: TestG` · `test exit=1`

**출력**

```text
===== 소스: t49gor_test.go =====
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
===== 명령: go vet . ; echo "go vet exit=$?"; go test -c -o t.test . || exit 1; echo "go test 가 빌드했나: 예 (vet 부분 집합을 통과)"; ./t.test -test.v; echo "test exit=$?" =====
t49gor_test.go:9:3: call to (*testing.T).Fatal from a non-test goroutine
go vet exit=1
go test 가 빌드했나: 예 (vet 부분 집합을 통과)
=== RUN   TestG
    t49gor_test.go:9: in goroutine
    t49gor_test.go:13: test: after <-done
--- FAIL: TestG (0.00s)
FAIL
test exit=1
(exit 0)
```

**왜 그런가**

- ★★★ `t.Fatal` → `FailNow` → **`runtime.Goexit`** — **부른 고루틴만** 끝난다(그 고루틴의 `defer close(done)` 은 돈다). 테스트 함수는 `<-done` 에서 풀려 **다음 줄로 계속** 간다.
- ★★ 실패 **표시**는 됐다 — 그래서 `FAIL`.
- ★★ `go test` 는 빌드했다 — `testinggoroutine` 도 `go test` 의 부분 집합에 없다.

### 7. `-run "A/1"` → `TestA/x1`·`TestA/y1` · `TestB: after Skip` 은 **안** 찍힌다(`--- SKIP`) · `-shuffle` 은 **최상위 테스트 순서**를 섞었고 하위는 그대로 · 같은 씨앗이면 같은 순서

**출력**

```text
===== 소스: t49run_test.go =====
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
===== 명령: go test -c -o t.test . || exit 1; echo "── -test.run A/1"; ./t.test -test.run "A/1" -test.v; echo "── -test.run B"; ./t.test -test.run "B" -test.v; for s in 1 2 1; do echo "── -test.shuffle=$s 의 === RUN 순서"; ./t.test -test.shuffle=$s -test.v | grep -E "^(-test.shuffle|=== RUN)" | sed "s/=== RUN   //" | tr "\n" " "; echo; done =====
── -test.run A/1
=== RUN   TestA
=== RUN   TestA/x1
    t49run_test.go:7: ran TestA/x1
=== RUN   TestA/y1
    t49run_test.go:7: ran TestA/y1
--- PASS: TestA (0.00s)
    --- PASS: TestA/x1 (0.00s)
    --- PASS: TestA/y1 (0.00s)
PASS
── -test.run B
=== RUN   TestB
    t49run_test.go:12: skip reason
--- SKIP: TestB (0.00s)
PASS
── -test.shuffle=1 의 === RUN 순서
-test.shuffle 1 TestA TestA/x1 TestA/x2 TestA/y1 TestB TestD TestC 
── -test.shuffle=2 의 === RUN 순서
-test.shuffle 2 TestB TestC TestD TestA TestA/x1 TestA/x2 TestA/y1 
── -test.shuffle=1 의 === RUN 순서
-test.shuffle 1 TestA TestA/x1 TestA/x2 TestA/y1 TestB TestD TestC 
(exit 0)
```

**왜 그런가**

- ★★★ 문서 — `-run` 은 「unanchored regular expression … slash-separated, with expressions matching each name element in turn」. `A` ⊂ `TestA`, `1` ⊂ `x1`·`y1`.
- ★★ `t.Skip` = 로그 + `SkipNow` → **`runtime.Goexit`**.
- ★ 하위가 안 섞인 것은 **이 블록의 관찰**이다(`go help testflag` 는 「tests and benchmarks」까지만 말한다).

### 8. `defer` 는 **헬퍼가 반환할 때** 돌아서 헬퍼 밖에서는 이미 닫혀 있다 · `t.Cleanup` 은 **테스트(와 하위)가 끝날 때** 돈다 · 둘이 같이 있으면 **`defer` 가 먼저**

- ★★ 2번 판 1 — `P.defer 가 P.cleanup2 보다 먼저 true`. 그리고 판 2 에서는 `defer` 만 병렬 하위보다 앞당겨졌다.
- ★ `defer` 는 **함수**의 수명, `Cleanup` 은 **테스트**의 수명이다. 헬퍼 안의 `defer` 는 [26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/)의 규칙대로 헬퍼가 끝날 때 돈다(이 문서는 헬퍼 판을 따로 돌리지 않았다).

### 9. `go.mod` 의 `go` 줄이 **1.22 이상**이고 그 파일에 **`//go:build go1.21` 같은 낮은 판 줄이 없을** 때 — 4·5번이 그 두 조건을 각각 깨 보인 것이다

- ★★ 13번 (5)절 「옛 관용구 `i := i` 는 아직 필요한가 — 필요하다」는 **루프 밖에서 선언한 변수** 등 1.22 가 안 바꾼 자리를 든다. 표 기반 테스트의 `for _, tc := range cases` 는 **1.22 가 바꾼 자리**다.
- ★ 5번 블록 — `go 1.21` 줄이면 **두 파일 다** `c c c`.

### 10. 몸통이 **기대값과 견주지 않고** 기록만 했다 — 검사를 안 한 테스트는 틀린 값을 봐도 통과한다 · `if got != tc.want { t.Errorf(…) }` 처럼 **그 행의 기대값과 견주는 줄**이 있어야 한다

- ★★ 1번의 `TestAbs` 가 그 모양이다 — 몸통이 `tt.want` 와 견줘서 **틀린 행을 이름으로** 잡았다.
- ★ go1.21 의미에서 모든 하위가 마지막 행을 보면 **마지막 행의 입력·기대값**으로 세 번 검사하게 된다 — 마지막 행이 맞으면 **셋 다 통과**한다. 이 문서는 그 판을 따로 돌리지 않았다(4번은 기록만 했다).

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 로 **★고칠 것 0** |
| ★★★ 정리 순서 격자 (`t49order`) | 질문 9 × 판 3 · `paste` 후 탭 6칸 검사 | 캡처마다 | **`3 / 9` · `0 / 9`** |
| ★★ 두 파일 격자 (`t49loop`·`t49loop121`) | `//go:build go1.21` 파일 대 보통 파일 · `go.mod` 의 `go` 줄 1.27 대 1.21 | 캡처마다 | `2 / 3` · 1.21 줄이면 둘 다 `c c c` |
| ★★ 다른 고루틴 `t.Fatal` (`t49gor`) | `go vet` + `-test.v` | 캡처마다 | 그 고루틴만 멈춤 |
| ★ 필터·건너뛰기·섞기 (`t49run`) | `-test.run`·`-test.shuffle=1,2,1` | 캡처마다 | 씨앗이 같으면 같음 |

**구현·환경에 달린 항목**

| 항목 | 무엇에 달렸나 |
|---|---|
| 루프 변수 의미 | **언어 판**(`go` 줄 · `//go:build go1.NN`) |
| `Run`·`Cleanup`·`FailNow` 의 순서 | **`testing` 문서의 계약** |
| `go test` 가 도는 `vet` 분석기 | **`go` 명령의 판** |
| 하위가 안 섞인 것 · 씨앗 → 순서 | **이 판의 관찰** |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다(기본 규칙만).

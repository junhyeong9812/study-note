# go/syntax/49 — `testing`: 표 기반 테스트·`t.Run`·`t.Cleanup`·`t.Parallel` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [`testing`](https://pkg.go.dev/testing) 패키지 문서(`go doc testing` 의 「Subtests and Sub-benchmarks」 · `T.Run` · `T.Parallel` · `T.Cleanup` · `T.FailNow`) · `go help test`. **이 툴체인에서 직접 떴다.**\
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.
> ★ 테스트는 **`go test -c -o t.test .` 로 바이너리를 만든 뒤 `./t.test` 로** 돌렸다 — `go test .` 의 `ok … 0.004s` 줄(시간)이 안 섞이게. `go test .` 을 그대로 실은 블록은 (1)절 하나다.\
> **버전** — `t.Parallel` 은 1.0 · `t.Run` 은 1.7 · `t.Cleanup` 은 1.14 · `t.Setenv` 1.17 · `t.Context` 1.24(이 툴체인의 `api/go1*.txt` — 아래 「이 판」) · ★★ **`for` 루프 변수가 회차마다 새로 생기는 것은 1.22**(언어 판 — [13번 주제](../13-closures-variable-capture-and-loop-variable-change/)).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체는 넷째 창이다** — 「**정리 순서 판 격자** — 「A 가 B 보다 먼저인가」 질문 9 × 판 3(하위 `t.Parallel()` 없음 · 있음 · 있음 + `t.Run("group", …)` 으로 감쌈)」.
마지막 두 줄 「**판 1 과 판 2 가 갈린 칸 3 / 9**」·「**판 1 과 판 3 이 갈린 칸 0 / 9**」((2)절). ★★★ **`t.Parallel()` 한 줄이 부모의 `defer` 를 병렬 하위보다 먼저 돌게 만들고, `group` 한 겹이 그것을 되돌린다.**
★★ 짝이 되는 창은 「**두 파일, 같은 루프**」 — 한 패키지 안에서 `//go:build go1.21` 파일과 보통 파일이 **같은 표 기반 병렬 테스트**를 돌려 **「두 파일이 갈린 칸 2 / 3」**((3)절).

★★★ **이 주제의 경계** — 루프 변수 의미 변경의 **언어 쪽 정본은 [13번 주제](../13-closures-variable-capture-and-loop-variable-change/)** (2)·(8)절이다(한 빌드 두 의미 · `vet` 이 판을 안다). 여기는 그것이 **표 기반 병렬 테스트에서** 어떻게 보이나로 좁힌다.
`defer` 의 LIFO 는 [26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/) · `runtime.Goexit` 과 `panic` 의 차이는 [27번 주제](../27-panic-recover-and-where-to-use-them/) · 벤치마크는 [50번 주제](../50-benchmarks-testing-b-and-reading-profiles/) · `go vet` 분석기 전체 격자는 [52번 주제](../52-tools-gofmt-vet-build-tags-embed-and-escape-analysis/) (2)절이다.
★ Rust 의 `#[test]`·통합 테스트는 Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **58번**이다(폴더가 아직 없다).

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 이 주제에서 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | ★★ **`for` 의 루프 변수는 회차마다 새 변수**(1.22 — `go` 줄이 언어 판을 정한다) · `defer` 는 **함수가 반환할 때** 돈다 |
| **표준 라이브러리 계약** | `go doc` 이 적은 것 | ★★★ **`Run` 은 「f 가 반환하거나 `t.Parallel` 을 부를 때까지」 막는다** · `Cleanup` 은 **하위까지 다 끝난 뒤, 나중에 등록한 것부터** · `FailNow` 는 **`runtime.Goexit`** 이고 **테스트 고루틴에서만** 불러야 한다 · `-run` 은 **`/` 로 나뉜 단계마다 따로 맞추는 비고정 정규식** |
| **구현·도구** | 이 판에서 찍힌 것 | ★★ **`go test` 는 `vet` 의 일부만 돌린다**(`go help test` 의 목록 — `loopclosure`·`testinggoroutine` 은 거기 없다) · `-shuffle` 의 씨앗 → 순서 · 병렬 하위끼리의 순서 |

★★★ **선을 긋는다** — 「부모의 `Cleanup` 은 병렬 하위가 끝난 뒤에 돈다」는 **문서의 계약**이다. 「부모의 `defer` 는 병렬 하위보다 먼저 돈다」는 계약 두 개(`Run` 이 `t.Parallel` 에서 돌아온다 · `defer` 는 함수 반환 때)에서 **따라 나온 것**이고, 이 문서는 그것을 (2)절 격자로 **직접 쟀다.** 「병렬 하위 `s2`·`s3` 중 누가 먼저 도나」는 **아무도 약속하지 않는다** — 그래서 칸으로 만들지 않았다.

## 이 판

```text
===== 명령: go version; "$GO125" version; go env CGO_ENABLED; nproc =====
go version go1.27.1 linux/amd64
go version go1.25.12 linux/amd64
1
24
(exit 0)
```

```text
===== 명령: A="$(go env GOROOT)/api"; for s in "(*T) Run(" "(*T) Parallel(" "(*T) Cleanup(" "(*T) Setenv(" "(*T) Context(" "(*B) Loop(" "(*B) ReportAllocs(" "func NotifyContext(" "(*Server) Shutdown(" "var ErrServerClosed" "func Goexit(" "pkg embed, type FS"; do printf "%s\t%s\n" "$s" "$(grep -lF "$s" "$A"/go1*.txt | xargs -n1 basename | paste -sd" ")"; done =====
(*T) Run(	go1.7.txt
(*T) Parallel(	go1.txt
(*T) Cleanup(	go1.14.txt
(*T) Setenv(	go1.17.txt
(*T) Context(	go1.24.txt
(*B) Loop(	go1.24.txt
(*B) ReportAllocs(	go1.1.txt
func NotifyContext(	go1.16.txt
(*Server) Shutdown(	go1.8.txt
var ErrServerClosed	go1.8.txt
func Goexit(	go1.txt
pkg embed, type FS	go1.16.txt
(exit 0)
```

- ★ **API 가 처음 실린 판** — 각 줄의 파일 이름이 그 판이다(`go1.txt` = 1.0). 50·51번이 같은 블록을 인용한다.

```text
===== 명령: go doc testing.T.Run | sed -n "3,7p"; go doc testing.T.Parallel | sed -n "3,6p"; go doc testing.T.Cleanup | sed -n "3,6p"; go doc testing.T.FailNow | sed -n "3,11p" =====
func (t *T) Run(name string, f func(t *T)) bool
    Run runs f as a subtest of t called name. It runs f in a separate goroutine
    and blocks until f returns or calls t.Parallel to become a parallel test.
    Run reports whether f succeeded (or at least did not fail before calling
    t.Parallel).
func (t *T) Parallel()
    Parallel signals that this test is to be run in parallel with (and only
    with) other parallel tests, and pauses until all non-parallel tests have
    finished.
func (c *T) Cleanup(f func())
    Cleanup registers a function to be called when the test (or subtest) and
    all its subtests complete. Cleanup functions will be called in last added,
    first called order.
func (c *T) FailNow()
    FailNow marks the function as having failed and stops its execution by
    calling runtime.Goexit (which then runs all deferred calls in the current
    goroutine). Execution will continue at the next test or benchmark. FailNow
    must be called from the goroutine running the test or benchmark function,
    not from other goroutines created during the test. Calling FailNow does not
    stop those other goroutines.
(exit 0)
```

- ★★★ **`Run` — 「blocks until f returns or calls t.Parallel」** — 하위가 `t.Parallel()` 을 부르면 `Run` 은 **그 자리에서 돌아온다.** 부모 함수는 계속 진행해 **끝까지 가 버린다.**
- ★★★ **`Cleanup` — 「when the test (or subtest) and all its subtests complete」** — `defer` 와 달리 **하위까지** 기다린다. 「last added, first called」.
- ★★ **`FailNow` — 「calling runtime.Goexit」 · 「must be called from the goroutine running the test」** — `t.Fatal` 은 `FailNow` 를 부른다. 다른 고루틴에서 부르면 **그 고루틴만** 멈춘다((4)절).

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | ★★ `(0.00s)` · `ok ex 0.004s` · `FAIL ex 0.004s` 의 **시간** | 기본 정규화 규칙(`<time>`)이 잡는다 — 재대조에서 확인 |
| **흔들린다 — 칸으로 안 만들었다** | ★★★ **병렬 하위 `s2`·`s3` 끼리의 순서** | 예행 200판에서 **두 가지**가 나왔다(199 대 1) — 그래서 (2)절은 「A 가 B 보다 먼저인가」 중 **순서가 약속된 짝만** 물었다 |
| 안 흔들린다 | ★★★ **정리 순서 격자 9칸 × 3판 · `3 / 9` · `0 / 9`** | 계약이 정하는 짝만 골랐다 |
| 안 흔들린다 | ★★ 두 파일 격자의 `c c c` 대 `a b c` · `2 / 3` · `vet` 문구 · 종료 코드 | 언어 판이 정한다 |
| 안 흔들린다 | `-test.shuffle=1`·`=2` 의 순서 | ★ **씨앗이 같으면 같다**(같은 블록에서 `1` 을 두 번 돌려 확인) — 씨앗을 안 주는 `-shuffle=on` 은 싣지 않았다 |

★ 정규화 규칙은 **기본 넷**만 썼다.

## 한눈에 — 쉽게 말하면

**표 기반 테스트는 「시험지 한 장에 문제를 줄줄이 적는 것」이다.** 문제(입력)와 모범 답안(기대값)을 **표 한 줄씩** 쓰고, 채점기(`for` + `t.Run`)가 줄마다 **따로 채점**한다 — 한 문제가 틀려도 나머지는 계속 채점하고, 틀린 문제는 **이름으로** 보고된다(`TestAbs/neg1`).

**`t.Parallel()` 은 「그 문제는 나중에 한꺼번에 풀겠다」는 표시다.** 채점기는 그 줄에 표시만 해 두고 **바로 다음 줄로 넘어간다** — 그래서 **시험지(부모 함수)가 먼저 끝나 버린다.**
시험지 끝에 적어 둔 **「다 끝나면 교실 불 끄기」(`defer`)는 그때 이미 실행된다** — 나중에 풀 문제들이 **깜깜한 교실에서** 풀리는 셈이다.
**`t.Cleanup` 은 「모든 문제가 끝나면 불 끄기」를 선생님께 맡겨 두는 것**이라 이 사고가 안 난다.

| 비유 | 실체 |
|---|---|
| 문제·답안 한 줄 | ★★ **표의 한 행** — `{name, in, want}` |
| 줄마다 따로 채점 | ★★ **`t.Run(tt.name, …)`** — 실패는 `--- FAIL: TestAbs/neg1` |
| 「나중에 한꺼번에」 표시 | ★★★ **`t.Parallel()`** — `Run` 이 **그 자리에서 돌아온다** |
| 시험지 끝의 「불 끄기」 | ★★★ **부모의 `defer`** — 병렬 하위보다 **먼저** 돈다((2)절 판 2) |
| 선생님께 맡긴 「불 끄기」 | ★★★ **부모의 `t.Cleanup`** — 하위가 **다 끝난 뒤** 돈다 |
| 문제 묶음 봉투 | ★★ **`t.Run("group", …)`** — 봉투가 닫혀야 다음 줄로 간다((2)절 판 3) |

```text
   ★★★ t.Parallel() 하위가 있을 때 — 누가 언제 도나 (판 2)

   TestParent ────────────────────────────────────────────────────────▶ 시간
     defer P.defer · Cleanup P.cleanup1, P.cleanup2 (등록만)
     t.Run("s1")  ─▶ [s1 본문 → s1.defer → s1.cleanup]   ← Run 이 끝까지 기다린다
     t.Run("s2")  ─▶ [s2 가 t.Parallel() — 멈춤] ─┐       ← Run 이 곧바로 돌아온다
     t.Run("s3")  ─▶ [s3 가 t.Parallel() — 멈춤] ─┤
     P.return                                      │
     P.defer      ← ★ 여기서 돈다 (s2·s3 는 아직) │
                                                   ▼
                              [s2 본문·defer·cleanup] [s3 …]   (둘 사이 순서는 약속 없음)
                                                   ▼
     P.cleanup2 → P.cleanup1   ← ★ 하위가 다 끝난 뒤, 나중 등록부터
```

> **하위 테스트(subtest)** — `t.Run(name, f)` 로 만든 테스트 안의 테스트. 이름은 `부모/하위` 로 이어진다(`TestAbs/neg1`).

> **`t.Cleanup(f)`** — 테스트가 끝나면 부를 함수를 등록한다. **하위까지 전부 끝난 뒤**, 나중에 등록한 것부터 부른다.

## 이 주제가 답하려는 질문

1. **케이스를 표로 접으면 무엇이 좋아지나** — 실패가 어떻게 보고되고, 한 케이스가 틀리면 나머지는 어떻게 되나.
2. **병렬 하위 테스트가 있을 때 정리는 어떤 순서로 도나** — 부모의 `defer`·`Cleanup`, 하위의 `defer`·`Cleanup`.
3. **표 기반 병렬 테스트에서 무엇이 조용히 틀리나** — 루프 변수 캡처(판 경계) · 다른 고루틴의 `t.Fatal` · 필터.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **정리 순서 판 격자 — 질문 9 × 판 3** | 부모 `defer`·`Cleanup` 이 **병렬 하위와 어떤 순서로** 도나 | ★ 본체 창 · `TestMain` 이 기록을 읽어 참/거짓을 찍고, 스크립트가 **탭 6칸**을 검사해 갈린 칸을 센다 |
| ★★ **두 파일 격자** — `//go:build go1.21` 파일 대 보통 파일 | 병렬 하위가 **어느 케이스를 봤나** | (3)절 · 13번의 「한 빌드 두 의미」 레버 |
| ★★ **`go vet` 대 `go test` 의 종료 코드** | 같은 실수를 **누가 잡나** | (3)·(4)절 — `go test` 는 `vet` 의 일부만 돈다 |
| ★ **테스트 출력 형식** — `--- FAIL:` · `=== RUN` · `--- SKIP:` | 실패가 **어떤 이름으로** 보고되나 | (1)·(5)절 |
| ★★ **제5의 상태 — 「기준만 다른 것」** | ★★★ **`-run "A/1"` 은 `TestA/x1`·`TestA/y1` 을 돌린다** — 틀린 게 아니다. 이름 전체에 한 정규식을 대는 게 아니라 **`/` 로 나뉜 단계마다 따로, 앵커 없이** 댄다. `A` 가 `TestA` 에, `1` 이 `x1`·`y1` 에 **들어 있기만 하면** 맞는다((5)절) · ★ (3)절의 go1.21 파일도 같은 모양이다 — **`PASS`·`exit 0`** 인데 세 하위가 **전부 `c` 를 봤다**(검사를 안 한 테스트는 통과한다) | (3)·(5)절 |
| **부적용 — 속도** | ★★ **「`t.Parallel()` 이 테스트를 빠르게 한다」는 재지 않았다** — 이 문서의 하위는 거의 일을 안 한다 | 규칙 4 · 시간은 [50번 주제](../50-benchmarks-testing-b-and-reading-profiles/) |
| **부적용 — 병렬 하위끼리의 순서** | 약속이 없다 — **칸으로 만들지 않았다** | 흔들리는 칸 표 |

### (1) ★★ 표 기반 테스트 — 실패는 이름으로 보고되고 나머지는 계속 돈다

**언제 쓰나** — 같은 함수에 입력만 바꿔 여러 번 물을 때. 가장 흔한 Go 테스트 모양이다.

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

그림 해설 (한 단계씩):

- ★★ **`--- FAIL: TestAbs/neg1 (0.00s)`** — 실패한 케이스가 **표의 `name`** 으로 보고된다. 부모 `TestAbs` 도 `FAIL` 이다(하위가 하나라도 실패하면 부모도 실패).
- ★★ **`t49table_test.go:26:`** — `t.Errorf` 를 부른 **줄**이 붙는다. 표의 어느 **행**인지는 줄 번호가 아니라 **이름**이 말한다 — 그래서 `name` 칸을 둔다.
- ★★ **`t.Errorf` 는 멈추지 않는다** — 실패를 표시만 하고 그 하위를 끝까지 돈다. `t.Fatalf` 였다면 **그 하위만** 멈추고 **다음 행은 여전히 돈다**(하위마다 고루틴이 따로다 — 머리말 `Run` 문서 「in a separate goroutine」).
- ★ `abs` 의 조건이 `x < -1` 이라 `-1` 만 틀린다 — `-2` 는 맞는다. **경계값 행이 있어야** 잡힌다.

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

- ★★ **`-test.v`(= `go test -v`)** 면 **통과한 하위도** `--- PASS:` 로 이름이 찍힌다 — `neg2` 가 `neg1` 뒤에도 **돌았다**는 증거다.
- ★ 로그 줄(`t49table_test.go:26: …`)은 **그 하위의 `=== RUN` 아래**에 나온다. 요약(`--- FAIL`·`--- PASS`)은 부모가 끝날 때 한꺼번에 나온다.

비용 — 없다. 표가 길어지면 **이름이 곧 색인**이다.

### (2) ★★★ 정리 순서 판 격자 — 질문 9 × 판 3

**언제 쓰나** — 병렬 하위 테스트가 **공유 자원**(임시 디렉토리·DB 연결·서버)을 쓸 때. 누가 닫느냐가 사고를 가른다.

```text
===== 소스: t49order_test.go =====
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

그림 해설 (한 단계씩):

- ★★★ **판 1(Parallel 없음) — `순서:` 줄이 곧 직관이다** — `s1 → s2 → s3` 가 각자 `본문 → defer → cleanup` 을 마치고, 부모가 `P.return → P.defer → P.cleanup2 → P.cleanup1`. **`defer` 가 `Cleanup` 보다 먼저, `Cleanup` 은 나중 등록부터.**
- ★★★ **판 2(s2·s3 가 `t.Parallel()`) — 위 세 줄이 뒤집혔다: `P.return`·`P.defer` 가 `s2.body` 보다 먼저 · `P.defer` 가 `s3.cleanup` 보다 먼저** — 머리말 `Run` 문서 「blocks until f returns **or calls t.Parallel**」 그대로다. `Run` 이 돌아오니 부모 함수가 **끝까지 가서 반환**하고, **그때 `defer` 가 돈다** — 병렬 하위는 **그 뒤에야** 풀려난다.
- ★★★ **그런데 `P.cleanup1`·`P.cleanup2` 는 판 2 에서도 `s2.cleanup`·`s3.cleanup` 뒤다** — 문서 「when the test (or subtest) **and all its subtests** complete」. **부모의 `defer` 로 공유 자원을 닫으면 병렬 하위가 닫힌 자원을 쓰고, `t.Cleanup` 으로 닫으면 안 그렇다** — 이 한 쌍이 이 주제의 결론이다.
- ★★ **판 3(판 2 + `t.Run("group", subs)` 로 감쌈) — 판 1 과 갈린 칸 `0 / 9`** — `group` 도 하위 테스트이고, **하위를 가진 하위는 그 하위가 다 끝나야 끝난다**(`go doc testing` 「A parent test will only complete once all of its subtests complete」). 그래서 바깥 `t.Run("group")` 이 **병렬 하위가 끝날 때까지** 안 돌아온다. `defer` 를 꼭 써야 한다면 이 모양이다.
- ★ **판 1·2·3 모두 `s1.cleanup` 이 `s2.body` 보다 먼저** — 병렬이 아닌 `s1` 은 `Run` 이 끝까지 기다리므로 **자기 `Cleanup` 까지 마친 뒤** 돌아온다. 하위의 `Cleanup` 은 **그 하위가 끝날 때** 돈다.
- ★ **`s2.defer` 는 `s2.cleanup` 보다 먼저** — 하위 안에서도 규칙이 같다: 함수 반환(`defer`) → 테스트 종료(`Cleanup`).

비용 — `t.Cleanup` 은 **등록 한 줄**이다. 판 3 의 `group` 은 이름에 한 단계(`TestParent/group/s2`)가 더 붙는다.

### (3) ★★ 두 파일, 같은 루프 — 표 기반 병렬 테스트의 루프 변수

**언제 쓰나** — 옛 코드의 `tc := tc` 를 지워도 되나 판단할 때, 그리고 `go.mod` 의 `go` 줄이 낮은 모듈을 볼 때.

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

그림 해설 (한 단계씩):

- ★★★ **go1.21 파일 — 하위 셋이 전부 `c` 를 봤다 · go1.22+ 파일 — `a b c`** · 「두 파일이 갈린 칸 `2 / 3`」 — 소스는 **한 글자도 같고** 파일 첫 줄 `//go:build go1.21` 만 다르다. 13번 (2)절의 레버를 테스트에 댄 것이다.
- ★★★ **왜 전부 `c` 인가** — 병렬 하위는 `t.Parallel()` 에서 멈췄다가 **부모가 반환한 뒤**((2)절) 풀려난다. 그때 1.21 의미의 `tc` 는 **루프 전체가 공유하는 변수 하나**이고 **이미 마지막 값 `c`** 다. 1.22 부터는 **회차마다 새 `tc`** 라 각자 자기 값을 본다.
- ★★ **`t.Run(tc.name, …)` 의 이름은 제대로 `a b c`** 다 — 이름은 **`Run` 을 부르는 순간** 읽히고, 몸통의 `tc.name` 은 **나중에** 읽힌다. 이름만 보면 멀쩡해 보인다.
- ★★★ **`go vet exit=1`(`loop variable tc captured by func literal`) 인데 `go test(-run ^$) exit=0`·`test exit=0`** — `go vet` 은 잡았는데 **`go test` 는 안 막았고 테스트도 통과했다.** `go test` 가 돌리는 `vet` 은 **일부**다([52번 주제](../52-tools-gofmt-vet-build-tags-embed-and-escape-analysis/) (2)절 — 목록에 `loopclosure` 가 없다). 그리고 이 테스트는 **아무것도 검사하지 않아서** 틀린 값을 보고도 통과한다.
- ★ `vet` 은 **go1.21 파일만** 짚었다 — 13번 (8)절 「`vet` 은 언어 판을 보고 판단한다」와 같다.

비용 — 1.22+ 모듈에서는 **없다**. 옛 `go` 줄이면 `tc := tc` 한 줄이 필요했다.

### (4) ★★ 다른 고루틴에서 `t.Fatal` — 그 고루틴만 멈춘다

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

그림 해설 (한 단계씩):

- ★★★ **`in goroutine` 뒤의 `goroutine: after Fatal` 은 안 찍혔고, `test: after <-done` 은 찍혔다** — `t.Fatal` → `FailNow` → **`runtime.Goexit`**(머리말 문서). `Goexit` 은 **부른 고루틴만** 끝낸다(그 고루틴의 `defer` 는 돈다 — `close(done)` 이 돌아서 테스트가 안 멈췄다). **테스트 함수는 멈추지 않고 끝까지 갔다.**
- ★★ **테스트는 `FAIL`** — 실패 **표시**는 됐다. 문서 「Calling FailNow does not stop those other goroutines」의 반대 방향 — **다른 고루틴에서 불러도 테스트 고루틴을 멈추지 못한다.**
- ★★★ **`go vet exit=1`(`call to (*testing.T).Fatal from a non-test goroutine`) · `go test` 는 빌드했다** — 여기서도 `go test` 의 `vet` 부분 집합에 **`testinggoroutine` 이 없다**((3)절과 같은 구멍).
- ★ 고치는 법 — 고루틴에서는 **`t.Error` + `return`**(멈출 필요가 없으면), 또는 **에러를 채널로 돌려받아** 테스트 고루틴에서 `t.Fatal`.

### (5) ★ `-run` 필터 · `t.Skip` · `-shuffle`

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

그림 해설 (한 단계씩):

- ★★★ **`-test.run "A/1"` — `TestA/x1`·`TestA/y1` 이 돌고 `x2`·`TestB…D` 는 안 돌았다** — 문서 「unanchored regular expression … slash-separated, with expressions matching each name element in turn」. 첫 단계 `A` 는 **`TestA` 에 들어 있어서**, 둘째 단계 `1` 은 **`x1`·`y1` 에 들어 있어서** 맞는다. 정확히 하나만 돌리려면 `-run '^TestA$/^x1$'`.
- ★★ **`-test.run "B"` — `--- SKIP: TestB` · `TestB: after Skip` 은 안 찍혔다** — `t.Skip` 은 이유를 로그로 남기고 **`runtime.Goexit` 으로 그 자리에서** 멈춘다(`SkipNow`). 실패가 아니라 `PASS` 다.
- ★★ **`-test.shuffle=1` 과 `=2` — 최상위 테스트(`TestA…D`) 순서가 바뀌었다 · `TestA/x1 x2 y1` 의 순서는 두 씨앗 모두 그대로** — `go help testflag` 는 「Randomize the execution order of tests and benchmarks」까지만 말한다. **하위가 안 섞인 것은 이 블록의 관찰**이다(하위는 `t.Run` 을 부르는 **코드의 순서**로 돈다). 씨앗을 출력 첫 줄(`-test.shuffle 1`)에 찍으므로(문서 「the seed will be reported for reproducibility」) **같은 씨앗으로 다시 돌릴 수 있다** — 같은 블록의 두 번째 `1` 이 첫 번째와 같다.
- ★ 쓸모 — 테스트 사이에 **숨은 순서 의존**(전역 상태)이 있으면 `-shuffle=on` 이 드러낸다. 이 문서의 테스트는 서로 독립이라 결과는 전부 `PASS` 다.

## 문법 — 형태와 규칙

### 형태

```text
   func TestXxx(t *testing.T) {            ← 파일 이름은 _test.go · 이름은 Test + 대문자
       t.Cleanup(func() { … })              ← 하위까지 다 끝난 뒤 · 나중 등록부터
       tests := []struct{ name string; in, want int }{ … }
       for _, tt := range tests {           ← 1.22+ : tt 는 회차마다 새 변수
           t.Run(tt.name, func(t *testing.T) {
               t.Parallel()                 ← Run 이 여기서 돌아온다
               if got := f(tt.in); got != tt.want {
                   t.Errorf("f(%d) = %d, want %d", tt.in, got, tt.want)   ← 계속 돈다
               }                                                          (t.Fatalf 면 이 하위만 멈춘다)
           })
       }
   }
```

- **하위 안에서는 바깥 `t` 가 아니라 인자 `t`** 를 쓴다 — 바깥 `t` 로 `Fatal` 하면 **부모를 멈추려 드는 것**이다.
- **`t.Run` 의 이름**이 `-run` 필터와 실패 보고의 열쇠다 — 문서 「a unique name: the combination of the name of the top-level test and the sequence of names passed to Run, separated by slashes」.
- `TestMain(m *testing.M)` 을 두면 **테스트 전·후**를 쥔다 — 이 문서는 기록을 찍으려고 썼다((2)·(3)절).

### 금지 사례 — 누가 잡나

| 쓴 꼴 | 누가 잡나 | 어디서 |
|---|---|---|
| 병렬 하위가 쓰는 자원을 **부모 `defer`** 로 닫기 | ★★★ **아무도 안 잡는다** — 컴파일·`vet`·`go test` 다 조용하다 | (2)절 판 2 |
| `go 1.21` 이하 파일에서 병렬 하위가 `tc` 를 캡처 | ★★ **`go vet`(`loopclosure`)** 만 — `go test` 는 통과 | (3)절 |
| 다른 고루틴에서 `t.Fatal` | ★★ **`go vet`(`testinggoroutine`)** 만 — `go test` 는 빌드·실행 | (4)절 |
| `Printf` 서식 실수 | ★★ **`go test` 도 막는다**(`printf` 는 부분 집합에 있다) | 52번 (2)절 |

## 어디서 틀리나

### 1. ★★★ 「부모 함수 끝의 `defer` 는 하위 테스트가 다 끝난 뒤에 돈다」

하위에 `t.Parallel()` 이 있으면 **아니다**((2)절 판 2 — `P.defer` 가 `s2.body` 보다 먼저). `Run` 이 `t.Parallel` 에서 돌아오기 때문이다. **`t.Cleanup` 을 쓰거나 `t.Run("group", …)` 으로 감싼다**(판 3 — `0 / 9`).

### 2. ★★★ 「`t.Cleanup` 은 `defer` 의 다른 이름이다」

순서가 다르다 — **`defer` 가 먼저, `Cleanup` 이 나중**(판 1 `P.defer 가 P.cleanup2 보다 먼저 true`), 그리고 **`Cleanup` 은 하위까지 기다린다.** 헬퍼 함수 안에서 등록해도 **테스트가 끝날 때** 돈다는 점도 `defer` 와 다르다(`defer` 는 헬퍼가 반환할 때 돈다).

### 3. ★★★ 「테스트가 통과했으니 표의 모든 행을 검사했다」

(3)절의 go1.21 파일은 **`PASS`·`exit 0`** 인데 세 하위가 **전부 마지막 행**을 봤다. 행 이름(`a b c`)은 제대로라 **출력만 봐서는 모른다.** 1.22 가 이 사고를 언어에서 없앴고, 옛 판에서는 `vet` 만 알려 준다.

### 4. ★★ 「`go test` 가 `vet` 을 돌리니 `go vet` 은 따로 안 돌려도 된다」

`go test` 가 돌리는 것은 **「high-confidence subset」** 이다(52번 (2)절 `go help test`). (3)·(4)절의 두 실수는 **`go vet` 만** 잡았다. CI 에 **`go vet ./...` 을 따로** 둔다.

### 5. ★★ 「다른 고루틴에서 `t.Fatal` 하면 테스트가 멈춘다」

**그 고루틴만** 멈춘다((4)절 — `test: after <-done` 이 찍혔다). 테스트는 `FAIL` 로 표시되지만 **다음 줄로 계속 간다** — 그 뒤 코드가 **실패를 전제로 안 짜여 있으면** 엉뚱한 곳에서 터진다.

### 6. ★★ 「`-run TestA/x1` 은 그것 하나만 돌린다」

**단계마다 앵커 없는 정규식**이다((5)절 — `A/1` 이 `x1`·`y1` 을 다 돌렸다). `TestA/x10` 이 있으면 `-run TestA/x1` 이 그것도 돌린다. 정확히 하나면 `^…$`.

### 7. ★ 「`-shuffle` 을 켜면 하위 테스트 순서도 섞인다」

(5)절의 두 씨앗에서는 **최상위만** 섞였다 — 하위는 `t.Run` 을 부르는 코드 순서다. 하위끼리의 순서 의존은 `-shuffle` 로 드러난다고 기대하지 마라.

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| 루프 변수가 회차마다 새 변수 | **명세**(1.22 · `go` 줄·`//go:build go1.NN` 이 판을 고른다) | (3)절 · 13번 |
| `defer` 는 함수 반환 때 · LIFO | **명세** | (2)절 · 26번 |
| `Run` 이 `t.Parallel` 에서 돌아온다 | **표준 라이브러리 계약** | 머리말 `t49pdoc` |
| `Cleanup` 은 하위까지 기다린 뒤 · 나중 등록부터 | **표준 라이브러리 계약** | 머리말 · (2)절 |
| `FailNow`·`SkipNow` 가 `runtime.Goexit` | **표준 라이브러리 계약** | 머리말 · (4)·(5)절 |
| `-run` 이 단계별 비고정 정규식 | **도구 계약**(`go doc testing`) | (5)절 |
| `go test` 가 도는 `vet` 분석기 목록 | ★★ **도구(`go` 명령) 판의 성질** — 명세가 아니다 | (3)·(4)절 · 52번 |
| 병렬 하위끼리의 순서 | ★★ **약속 없음** — 관찰도 칸으로 안 만들었다 | 흔들리는 칸 표 |
| `-shuffle` 씨앗 → 순서 · 하위는 안 섞임 | **이 판의 구현** — 씨앗이 같으면 같았다 · 하위가 안 섞인 것도 관찰 | (5)절 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 입력만 다른 케이스 여럿 | **표 + `t.Run(tt.name, …)`** | 실패가 이름으로 보고되고 나머지는 계속 돈다((1)절) |
| 하위가 공유 자원을 쓴다 | ★★★ **`t.Cleanup`** 으로 닫는다 | 병렬 하위가 다 끝난 뒤 돈다((2)절) |
| 꼭 `defer` 로 닫아야 한다 | **`t.Run("group", …)` 으로 감싼 뒤** | 판 3 `0 / 9` |
| 헬퍼가 자원을 만든다 | 헬퍼 안에서 **`t.Cleanup`** 등록 | 호출한 쪽이 닫기를 잊을 수 없다 |
| 하위가 서로 독립이고 느리다 | `t.Parallel()` | ★ 속도 이득은 이 문서가 **재지 않았다** |
| 전역 상태를 건드린다 | ★★ **`t.Parallel()` 을 쓰지 않는다** | 병렬 하위끼리 순서가 약속되지 않는다 |
| CI | **`go vet ./...` + `go test ./...`** 둘 다 | `go test` 의 `vet` 은 일부다 |

## 핵심 문장

- ★★★ **`t.Parallel()` 을 부르면 `t.Run` 이 그 자리에서 돌아온다** — 그래서 부모의 `defer` 가 병렬 하위보다 **먼저** 돈다(`3 / 9`).
- ★★★ **부모의 `t.Cleanup` 은 병렬 하위까지 다 끝난 뒤에 돈다** — 공유 자원은 `Cleanup` 으로 닫는다. `group` 으로 감싸면 `defer` 도 되돌아온다(`0 / 9`).
- ★★★ **go1.21 의미의 표 기반 병렬 테스트는 모든 하위가 마지막 행을 본다** — 그리고 **`PASS`** 다. 두 파일이 갈린 칸 `2 / 3`.
- ★★ **다른 고루틴의 `t.Fatal` 은 그 고루틴만 멈춘다** — 테스트는 `FAIL` 로 표시되고 계속 간다.
- ★★ **`go test` 의 `vet` 은 일부다** — `loopclosure`·`testinggoroutine` 은 `go vet` 만 잡았다.
- ★ **`-run` 은 `/` 단계마다 앵커 없는 정규식** · `-shuffle` 은 (두 씨앗에서) 최상위만 섞었다.

## 관련 자료

- [`testing`](https://pkg.go.dev/testing) · `go help test` · `go help testflag` — 이 툴체인의 `go doc` 으로 떴다.
- [13번 주제](../13-closures-variable-capture-and-loop-variable-change/) — ★ **루프 변수 의미 변경의 언어 쪽 정본.** 그쪽은 클로저가 변수를 잡는 규칙과 판 경계까지, 여기는 표 기반 **병렬 테스트**에서 보이는 모습부터.
- [26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/) — `defer` 의 평가 시점·LIFO. 여기는 그것이 **테스트 수명**과 어긋나는 자리.
- [27번 주제](../27-panic-recover-and-where-to-use-them/) — `panic`·`recover`. `runtime.Goexit` 문서 「Because Goexit is not a panic, any recover calls in those deferred functions will return nil」 — 그래서 `t.Fatal` 은 `recover` 로 못 멈춘다(돌려 보지 않았다 — 문서 조항).
- [35번 주제](../35-data-races-and-the-race-detector/) — 병렬 하위가 공유 상태를 건드리면 `-race`.
- [50번 주제](../50-benchmarks-testing-b-and-reading-profiles/) — 같은 `testing` 패키지의 벤치마크.
- [52번 주제](../52-tools-gofmt-vet-build-tags-embed-and-escape-analysis/) — ★ `go vet` 분석기 격자와 `go test` 의 부분 집합.
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **58번** — `#[test]`·통합 테스트·문서 테스트(폴더가 아직 없다).

## 용어 풀이

- **표 기반 테스트(table-driven test)** — 케이스를 구조체 슬라이스로 적고 `for` 로 도는 모양.
- **하위 테스트(subtest)** — `t.Run` 으로 만든 테스트. 이름이 `부모/하위`.
- **`t.Parallel()`** — 이 테스트를 병렬 무리에 넣는다. 부르는 순간 멈췄다가 **부모가 반환한 뒤**(하위면) 또는 **순차 테스트가 다 끝난 뒤**(최상위면) 풀린다.
- **`t.Cleanup(f)`** — 테스트(와 그 하위 전부)가 끝나면 부를 함수. 나중 등록부터.
- **`runtime.Goexit`** — 현재 고루틴만 끝낸다. `defer` 는 돈다. `t.FailNow`·`t.SkipNow` 가 이것을 쓴다.
- **`TestMain`** — 패키지의 테스트 전체를 감싸는 함수. `m.Run()` 이 테스트를 돌리고 종료 코드를 준다.
- **`-shuffle`** — 테스트·벤치마크의 실행 순서를 섞는다. 씨앗을 찍어 재현할 수 있다.
- **`vet` 부분 집합** — `go test` 가 빌드하면서 도는 `vet` 분석기 몇 개. 여기서 걸리면 테스트를 안 돌린다.

## 더 들어가면

- ★ **`t.Context()`(1.24)** — 문서 「canceled just before Cleanup-registered functions are called」. 이 문서는 **돌려 보지 않았다.**
- ★ **`t.Setenv` 는 병렬 테스트(와 병렬 조상을 가진 테스트)에서 못 쓴다**는 문서 조항이 있다 — 「Because Setenv affects the whole process」. 이 문서는 그 패닉을 **돌려 보지 않았다.**
- ★ 퍼징(`FuzzXxx`·`f.Add`)은 같은 `testing` 패키지지만 이 묶음 밖이다.

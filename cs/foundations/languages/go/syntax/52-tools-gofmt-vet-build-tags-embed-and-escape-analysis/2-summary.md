# go/syntax/52 — 도구: `gofmt`·`go vet`·빌드 태그·`go:embed`·탈출 분석 읽기 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — `go doc cmd/vet` · `go help test` · `go help buildconstraint` · [`embed`](https://pkg.go.dev/embed) 패키지 문서 · `go tool compile -help`(`-m`·`-l`). **이 툴체인에서 직접 떴다.**\
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.
> ★ 탈출 분석의 판 대조에는 모듈 캐시의 **`go1.25.12`** 를 같이 썼다(명령에는 `"$GO125"` 로 찍힌다 — 그 블록의 `go.mod` 는 `go 1.25`).\
> **버전** — `//go:build` 줄은 1.17 부터(문서 「Go versions 1.16 and earlier used a different syntax … "// +build"」) · `go:embed`(`embed.FS`)는 1.16([49번 주제](../49-testing-table-driven-t-run-cleanup-and-parallel/) 「이 판」의 `tapi`) · `for` 루프 변수 의미 변경은 1.22([13번 주제](../13-closures-variable-capture-and-loop-variable-change/)) · ★★ **`vet` 분석기 목록과 탈출 분석 결과는 명세가 아니라 툴체인 판의 성질**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체는 넷째 창이 둘이다** — 이 주제는 도구 다섯을 한 편에 묶었고, **판정이 걸린 격자가 둘**이다.
① 「**`vet` 격자** — 탐침 12(분석기 9 + 대조 3) × (`go vet` · `go test`)」 — 마지막 두 줄 「**go vet 이 짚은 칸 9 / 12**」·「**go test 가 막은 칸 1 / 12**」((2)절).
② 「**탈출 격자** — 탐침 9 × (`-gcflags='-m -l'` 의 말 · `testing.AllocsPerRun` 할당 수 · 인라인 켠 할당 수)」 — 「**-m 이 힙을 말한 칸 5 / 9**」·「**allocs 가 1 이상인 칸 6 / 9**」·「**둘이 어긋난 칸 1 / 9**」·「**인라인을 켜서 달라진 칸 1 / 9**」((5)절). ★★★ **`-m` 의 말과 실제 할당이 두 칸에서 갈린다 — 하나는 여기서, 하나는 [50번 주제](../50-benchmarks-testing-b-and-reading-profiles/) (3)절에서.**
★ 나머지 셋(`gofmt` · 빌드 태그 · `go:embed`)은 **결과가 파일 목록·diff 로 바로 보이는** 도구라 격자 하나씩(빌드 태그 「빌드에 들어간 칸 15 / 36」)과 에러 전문으로 적는다.

★★★ **이 주제의 경계** — 스택·힙·가상 메모리 **일반**은 [`cs/foundations/memory-management/`](../../../../memory-management/)(§3 스택 프레임 · §11 다이나믹 힙)가 정본이다 — ★ 그 폴더는 README 하나이고 **GC 알고리즘 절이나 탈출 분석 절은 없다.** 여기는 **Go 컴파일러의 `-m` 출력을 읽는 법**으로 좁힌다.
클로저 캡처가 힙으로 가는 첫 관찰은 [13번 주제](../13-closures-variable-capture-and-loop-variable-change/) (7)절 · `Printf` 서식 `vet` 의 여섯 줄은 [42번 주제](../42-fmt-verbs-stringer-and-errorf/) (5)절 · `lostcancel` 탐침 11개는 [34번 주제](../34-context-cancellation-deadlines-and-values/) (5)절 · `go.mod` 의 `go` 줄은 [41번 주제](../41-modules-go-mod-version-selection-and-workspaces/) · 테스트에서의 `vet` 구멍은 [49번 주제](../49-testing-table-driven-t-run-cleanup-and-parallel/) (3)·(4)절 이다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 이 주제에서 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | ★★★ **명세에는 스택도 힙도 없다** — 「변수는 참조되는 동안 살아 있다」까지다. **어디에 두느냐는 컴파일러의 일**이다(13번 (7)절) · 루프 변수 의미(1.22) |
| **도구 계약** | `go help`·`go doc` 이 적은 것 | ★★ **빌드 제약** — `//go:build` 식 · `_GOOS`·`_GOARCH` 파일 이름 · `go1.N` 태그는 「through the current version」 · ★★ **`go:embed`** — 디렉토리는 `.`·`_` 로 시작하는 파일을 빼고, `dir/*` 는 **그 층의** 그런 파일을 넣고, `all:` 은 전부 · `..` 금지 · ★★ **`go test` 는 `vet` 의 부분 집합만** |
| **구현·판** | 이 판에서 찍힌 것 | ★★★ **`-m` 의 문구와 결정**(인라인·탈출) · **`vet` 분석기 목록** · `gofmt` 의 출력 모양 |

★★★ **선을 긋는다** — 「`&p` 를 반환하면 `p` 가 힙으로 간다」는 **gc 컴파일러 이 판의 결정**이다. 명세는 「`p` 가 반환 뒤에도 살아 있다」만 약속한다. ★ (5)절에서 **같은 `retPtr` 이 인라인되면 할당이 0** 이 됐다 — 「힙으로 간다」는 **함수의 성질이 아니라 부르는 자리에서의 결정**이다.

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
===== 명령: go doc embed | sed -n "68,69p;74,76p;83,88p"; echo "── go help buildconstraint"; go help buildconstraint | sed -n "42,43p;48,55p;132,133p"; echo "── go doc cmd/vet"; go doc cmd/vet | sed -n "1,4p" =====
Windows systems. Patterns may not contain ‘.’ or ‘..’ or empty path elements,
nor may they begin or end with a slash. To match everything in the current
If a pattern names a directory, all files in the subtree rooted at that
directory are embedded (recursively), except that files with names beginning
with ‘.’ or ‘_’ are excluded. So the variable in the above example is almost
The difference is that ‘image/*’ embeds ‘image/.tempfile’ while ‘image’ does
not. Neither embeds ‘image/dir/.tempfile’.

If a pattern begins with the prefix ‘all:’, then the rule for walking
directories is changed to include those files beginning with ‘.’ or ‘_’. For
example, ‘all:image’ embeds both ‘image/.tempfile’ and ‘image/dir/.tempfile’.
── go help buildconstraint
	- a term for each Go major release, through the current version:
	  "go1.1" from Go version 1.1 onward, "go1.12" from Go 1.12, and so on.
If a file's name, after stripping the extension and a possible _test suffix,
matches any of the following patterns:
	*_GOOS
	*_GOARCH
	*_GOOS_GOARCH
(example: source_windows_amd64.go) where GOOS and GOARCH represent
any known operating system and architecture values respectively, then
the file is considered to have an implicit build constraint requiring
Go versions 1.16 and earlier used a different syntax for build constraints,
with a "// +build" prefix. The gofmt command will add an equivalent //go:build
── go doc cmd/vet
Vet examines Go source code and reports suspicious constructs, such as Printf
calls whose arguments do not align with the format string. Vet uses heuristics
that do not guarantee all reports are genuine problems, but it can find errors
not caught by the compilers.
(exit 0)
```

- ★★ **`embed` — 「Patterns may not contain ‘.’ or ‘..’」 · 「files with names beginning with ‘.’ or ‘_’ are excluded」 · 「‘image/*’ embeds ‘image/.tempfile’ while ‘image’ does not. Neither embeds ‘image/dir/.tempfile’」 · 「‘all:image’ embeds both」** — (4)절 격자가 이 네 문장을 그대로 재현한다.
- ★★ **`buildconstraint` — 「"go1.1" from Go version 1.1 onward … through the current version」** — 그래서 `//go:build go1.99` 파일은 **이 판에서 빠진다**((3)절 `future.go`).
- ★ **`vet` — 「Vet uses heuristics that do not guarantee all reports are genuine problems」** — 반대 방향(못 잡는 것)도 있다((2)절 `printf2`).

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ **`vet` 격자 12 × 2 · `9 / 12` · `1 / 12` · `vet` 문구** | 소스와 도구 판이 정한다 |
| 안 흔들린다 | ★★★ **탈출 격자 9 × 3 · `5 / 9` · `6 / 9` · `1 / 9` · `1 / 9`** | `AllocsPerRun` 은 **평균 할당 수**를 정수로 준다 — 예행·재대조에서 같았다 |
| 안 흔들린다 | ★★ 빌드 태그 격자 9 × 4 · `15 / 36` · `go:embed` 목록 · 에러 문구 · `gofmt` diff | |
| **판을 탄다** | ★★ **`-m` 의 문구** | `go1.25.12` 와 `go1.27.1` 은 **이 소스에서 한 줄도 안 달랐다**(「다른 줄 0」) — **보장이 아니다**(규칙 3 「여러 버전에서 같았다」) |

★ 정규화 규칙은 **기본 넷**만 썼다(이 주제에는 시간 칸이 없다).

## 한눈에 — 쉽게 말하면

**Go 의 도구들은 「같은 규칙을 모두에게」 붙이는 장치다.**
`gofmt` 는 **맞춤법 검사기가 아니라 활자 조판기**다 — 띄어쓰기·들여쓰기를 **토론 없이 한 가지로** 찍어 낸다. 그래서 코드 리뷰에서 「탭이냐 공백이냐」가 안 나온다.
`go vet` 은 **감리사**다 — 컴파일은 되는데 **수상한 모양**(서식과 인자 불일치 · 잠금 복사)을 짚는다. 단 **모든 감리사가 현장에 오는 건 아니다** — `go test` 는 **몇 명만** 데려온다.
빌드 태그·파일 이름은 **「이 도면은 리눅스 현장용」 도장**이고, `go:embed` 는 **도면철에 첨부 파일을 묶어 넣는 것**이다 — 단 **숨김 파일(`.`·`_`)은 기본으로 안 묶는다.**
탈출 분석(`-gcflags=-m`)은 **「이 짐은 작업대(스택)에 두나 창고(힙)에 두나」 결정 기록**이다 — 컴파일러가 **왜 창고로 보냈는지** 한 줄씩 적어 준다.

| 비유 | 실체 |
|---|---|
| 활자 조판기 | ★★ **`gofmt`** — 입력이 뭐든 출력은 하나 · `-s` 는 **군더더기 표현 줄이기** |
| 감리사 | ★★ **`go vet`** — 분석기 여럿(여기서 탐침한 것은 9) |
| 몇 명만 데려오는 현장 | ★★★ **`go test` 의 `vet` 부분 집합** — 12 중 1 만 막았다 |
| 현장 도장 | ★★ **`//go:build linux && !cgo`** · `_linux.go` |
| 첨부 파일 묶기 | ★★ **`//go:embed data`** · 숨김 파일은 `all:` 로만 |
| 작업대 대 창고 결정 기록 | ★★★ **`-m` 의 `moved to heap` · `escapes to heap` · `does not escape`** |
| 창고에 간 짐의 수 | ★★★ **`testing.AllocsPerRun` · 50번의 `allocs/op`** |

```text
   ★★★ 탈출 분석 한 줄을 읽는 법

   (파일 · 줄 · 칸)  (판정)          (무엇)
   esc.go 25행 2열   moved to heap   p        ← 실제 줄은 (5)절 블록에 콜론으로 이어져 찍힌다
                     moved to heap      지역 변수 자체를 힙에 만든다 (주소가 밖으로 나감)
                     escapes to heap    이 값(식)이 힙에 복사된다 (인터페이스·클로저 등)
                     does not escape    스택에 둘 수 있다 — ★ 그래도 할당이 날 수 있다 (5)절
                     (한 줄도 없음)     말할 게 없다 — 값 복사로 끝남
```

> **탈출 분석(escape analysis)** — 컴파일러가 「이 값이 함수가 끝난 뒤에도 쓰이나」를 따져 **스택에 둘지 힙에 둘지** 정하는 것. 힙에 두면 할당과 GC 비용이 든다.

> **빌드 제약(build constraint)** — 파일을 빌드에 넣을지 정하는 조건. 파일 첫머리 `//go:build 식` 또는 파일 이름 꼬리(`_linux`·`_amd64`).

## 이 주제가 답하려는 질문

1. **`gofmt` 가 「포맷 논쟁」을 어떻게 없애나** — 무엇을 정하고 무엇을 안 정하나.
2. **`go vet` 은 무엇을 잡고, `go test` 는 그중 무엇을 막나** — 분석기별로.
3. **`-gcflags=-m` 의 한 줄로 「힙으로 갔나」를 판단해도 되나** — 실제 할당과 언제 갈리나.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **`vet` 격자 — 탐침 12 × (`go vet` · `go test`)** | 수상한 모양을 **누가 잡나** | ★ 본체 창 ① · 탭 3칸 검사 · 두 수를 센다 |
| ★★★ **탈출 격자 — 탐침 9 × (`-m` · allocs · 인라인 allocs)** | `-m` 의 **말**과 **실제 할당** | ★ 본체 창 ② · `grid.sh` 가 `-m` 줄을 함수에 붙이고 탭 6칸 검사 |
| ★★ **빌드 태그 격자 — 파일 9 × 환경 4** | **어느 파일이** 빌드에 들어가나 | (3)절 · `go list -f` |
| ★★ **`go:embed` 목록 · 빌드 에러** | 패턴이 **무엇을** 묶나 | (4)절 |
| ★ **`gofmt -d` · `-s` diff** | 무엇이 **바뀌나** | (1)절 |
| ★★ **제5의 상태 — 「기준만 다른 것」** | ★★★ **`make([]int, n)` 은 `does not escape` 인데 할당 1** · 같은 문구의 `make([]int, m)`(m=4)은 0 — `-m` 은 **「탈출하나」** 를 말하고, 할당은 **「스택에 담을 수 있나」**(크기)까지 본다. 두 창이 **서로 다른 질문**에 답한다 · 반대 방향(`escapes` 인데 0)은 50번 (3)절 `BoxSmall` · ★ `vet` 격자의 `printf2` 도 같은 모양 — **서식 실수가 그대로인데 `vet exit 0`**(동사가 변수라 읽을 수 없다 — 42번) | (2)·(5)절 |
| **부적용 — 속도** | ★★ **「힙이 느리다」는 여기서 재지 않았다** — 50번의 `ns/op` 가 그 창이다 | 규칙 4 |

### (1) ★★ `gofmt` — 입력이 달라도 출력은 하나

**언제 쓰나** — 저장할 때마다(편집기) · CI 에서 `gofmt -l .` 이 빈 줄인가.

```text
===== 소스: t52fmt.go =====
package main
import "fmt"
type point struct{x,y int}
func main( ){
    ps:=[]point{point{1,2},point{x:3,y:4}}
	for _ = range ps { fmt.Println( "tick" ) }
  s:="abcdef"
	fmt.Println(s[2:len(s)],ps)
	fmt.Println("gofmt 은 줄 길이를 보지 않는다 — 이 줄은 백 자를 넘지만 접히지 않는다 · abcdefghijklmnopqrstuvwxyz")
}
===== 명령: gofmt -d t52fmt.go; echo "gofmt -d exit=$?" =====
diff t52fmt.go.orig t52fmt.go
--- t52fmt.go.orig
+++ t52fmt.go
@@ -1,10 +1,15 @@
 package main
+
 import "fmt"
-type point struct{x,y int}
-func main( ){
-    ps:=[]point{point{1,2},point{x:3,y:4}}
-	for _ = range ps { fmt.Println( "tick" ) }
-  s:="abcdef"
-	fmt.Println(s[2:len(s)],ps)
+
+type point struct{ x, y int }
+
+func main() {
+	ps := []point{point{1, 2}, point{x: 3, y: 4}}
+	for _ = range ps {
+		fmt.Println("tick")
+	}
+	s := "abcdef"
+	fmt.Println(s[2:len(s)], ps)
 	fmt.Println("gofmt 은 줄 길이를 보지 않는다 — 이 줄은 백 자를 넘지만 접히지 않는다 · abcdefghijklmnopqrstuvwxyz")
 }
gofmt -d exit=1
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **공백·탭·빈 줄·중괄호 위치가 전부 정해진다** — `func main( ){` 가 `func main() {`, 네 칸 공백 들여쓰기가 **탭**으로, `import` 와 `type` 사이에 **빈 줄**, 한 줄 `for … { … }` 가 **세 줄**로. 선택지가 없으니 **논쟁할 것이 없다.**
- ★★ **마지막 `Println` 줄은 바뀌지 않았다** — 100자를 훌쩍 넘는데 **접지 않는다.** `gofmt` 는 **줄 길이를 정하지 않는다** — 그건 사람 몫으로 남겼다.
- ★★ **`point{1, 2}` · `for _ = range` · `s[2:len(s)]` 는 그대로다** — 모양(공백)만 고쳤지 **표현을 바꾸지 않았다.** 그건 `-s` 의 일이다(아래).
- ★ `gofmt -d exit=1` — **diff 가 있으면 1**. CI 에서 「포맷 안 된 파일이 있나」의 신호로 쓴다.

```text
===== 소스: t52fmt.go =====
package main
import "fmt"
type point struct{x,y int}
func main( ){
    ps:=[]point{point{1,2},point{x:3,y:4}}
	for _ = range ps { fmt.Println( "tick" ) }
  s:="abcdef"
	fmt.Println(s[2:len(s)],ps)
	fmt.Println("gofmt 은 줄 길이를 보지 않는다 — 이 줄은 백 자를 넘지만 접히지 않는다 · abcdefghijklmnopqrstuvwxyz")
}
===== 명령: gofmt t52fmt.go > plain.txt; gofmt -s t52fmt.go > simple.txt; echo "── gofmt 결과와 gofmt -s 결과의 diff"; diff plain.txt simple.txt; echo "diff exit=$?"; echo "── gofmt -l ."; gofmt -l .; echo "gofmt -l exit=$?" =====
── gofmt 결과와 gofmt -s 결과의 diff
8,9c8,9
< 	ps := []point{point{1, 2}, point{x: 3, y: 4}}
< 	for _ = range ps {
---
> 	ps := []point{{1, 2}, {x: 3, y: 4}}
> 	for range ps {
13c13
< 	fmt.Println(s[2:len(s)], ps)
---
> 	fmt.Println(s[2:], ps)
diff exit=1
── gofmt -l .
t52fmt.go
gofmt -l exit=0
(exit 0)
```

- ★★ **`-s`(simplify) 가 더 바꾼 세 줄** — `[]point{point{1, 2}, …}` → `[]point{{1, 2}, …}`(원소 타입 생략) · `for _ = range ps` → `for range ps` · `s[2:len(s)]` → `s[2:]`. **뜻이 같은 짧은 표현**으로 바꾼다.
- ★ **`gofmt -l .` — 고칠 파일 이름만 찍고 `exit=0`** — ★★ **`-l` 은 파일이 있어도 0 이다.** CI 에서는 **출력이 비었나**로 판정한다(`test -z "$(gofmt -l .)"`).

### (2) ★★★ `go vet` 격자 — 탐침 12 × (`go vet` · `go test`)

**언제 쓰나** — CI 에 무엇을 둘지 정할 때, 그리고 「`go test` 가 통과했으니 괜찮다」를 의심할 때.

```text
===== 명령: go help test | sed -n "26,34p" =====
As part of building a test binary, go test runs go vet on the package
and its test source files to identify significant problems. If go vet
finds any problems, go test reports those and does not run the test
binary. Only a high-confidence subset of the default go vet checks are
used. That subset is: atomic, bools, buildtag, directive, errorsas,
ifaceassert, nilfunc, printf, stdversion, stringintconv, and tests.
You can see the documentation for these and other vet tests via
"go doc cmd/vet". To disable the running of go vet, use the -vet=off flag.
To run all checks, use the -vet=all flag.
(exit 0)
```

```text
===== 소스: copylock1.go =====
package copylock1

import "sync"

type C struct {
	mu sync.Mutex
	n  int
}

func (c C) Inc() { c.mu.Lock(); c.n++; c.mu.Unlock() }
===== 소스: copylock2.go =====
package copylock2

import "sync"

type C struct {
	mu sync.Mutex
	n  int
}

func (c *C) Inc() { c.mu.Lock(); c.n++; c.mu.Unlock() }
===== 소스: go.mod =====
module ex

go 1.27
===== 소스: httpresp1.go =====
package httpresp1

import "net/http"

func F(u string) error {
	resp, err := http.Get(u)
	defer resp.Body.Close()
	if err != nil {
		return err
	}
	return nil
}
===== 소스: loop121.go =====
//go:build go1.21

package loop121

import "sync"

func F(xs []int) {
	var wg sync.WaitGroup
	for _, v := range xs {
		wg.Add(1)
		go func() { defer wg.Done(); _ = v }()
	}
	wg.Wait()
}
===== 소스: loop127.go =====
package loop127

import "sync"

func F(xs []int) {
	var wg sync.WaitGroup
	for _, v := range xs {
		wg.Add(1)
		go func() { defer wg.Done(); _ = v }()
	}
	wg.Wait()
}
===== 소스: printf1.go =====
package printf1

import "fmt"

func F() { fmt.Printf("%d\n", "s") }
===== 소스: printf2.go =====
package printf2

import "fmt"

func F(verb string) { fmt.Printf(verb+"\n", "s") }
===== 소스: sigchan.go =====
package sigchan

import (
	"os"
	"os/signal"
)

func Wait() os.Signal {
	c := make(chan os.Signal)
	signal.Notify(c, os.Interrupt)
	return <-c
}
===== 소스: tag1.go =====
package tag1

type T struct {
	A int `json: "a"`
}
===== 소스: tag2.go =====
package tag2

type T struct {
	A int `json:"x"`
	B int `json:"x"`
}
===== 소스: tgor.go =====
package tgor
===== 소스: tgor_test.go =====
package tgor

import "testing"

func TestG(t *testing.T) {
	done := make(chan struct{})
	go func() {
		defer close(done)
		t.Fatal("x")
	}()
	<-done
}
===== 소스: unused1.go =====
package unused1

import "fmt"

func F(n int) { fmt.Sprintf("%d", n) }
===== 명령: printf "탐침\tgo vet exit\tgo test(-run ^$) exit\n"; for p in printf1 printf2 copylock1 copylock2 loop121 loop127 unused1 tag1 tag2 httpresp1 sigchan tgor; do go vet ./$p > /dev/null 2>>vet.txt; a=$?; go test -count=1 -run "^$" ./$p > /dev/null 2>&1; b=$?; printf "%s\t%s\t%s\n" $p $a $b; done > rows.txt; cat rows.txt; awk -F"\t" "NF!=3 {bad=1} {m++; if (\$2!=0) n++; if (\$3!=0) k++} END {if (bad) print \"칸 수 어긋남\"; printf \"go vet 이 짚은 칸 %d / %d\ngo test 가 막은 칸 %d / %d\n\", n, m, k, m}" rows.txt; echo "── go vet 이 낸 줄"; grep -v "^#" vet.txt =====
탐침	go vet exit	go test(-run ^$) exit
printf1	1	1
printf2	0	0
copylock1	1	0
copylock2	0	0
loop121	1	0
loop127	0	0
unused1	1	0
tag1	1	0
tag2	1	0
httpresp1	1	0
sigchan	1	0
tgor	1	0
go vet 이 짚은 칸 9 / 12
go test 가 막은 칸 1 / 12
── go vet 이 낸 줄
printf1/printf1.go:5:24: fmt.Printf format %d has arg "s" of wrong type string
copylock1/copylock1.go:10:9: Inc passes lock by value: ex/copylock1.C contains sync.Mutex
loop121/loop121.go:11:36: loop variable v captured by func literal
unused1/unused1.go:5:17: result of fmt.Sprintf call not used
tag1/tag1.go:4:2: struct field tag `json: "a"` not compatible with reflect.StructTag.Get: bad syntax for struct tag value
tag2/tag2.go:5:2: struct field B repeats json tag "x" also at tag2.go:4
httpresp1/httpresp1.go:7:8: using resp before checking for errors
sigchan/sigchan.go:10:2: misuse of unbuffered os.Signal channel as argument to signal.Notify
tgor/tgor_test.go:9:3: call to (*testing.T).Fatal from a non-test goroutine
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **「go vet 이 짚은 칸 9 / 12」 · 「go test 가 막은 칸 1 / 12」** — `go test` 가 막은 하나는 **`printf1`** 뿐이다. 위 `go help test` 의 부분 집합(「atomic, bools, buildtag, directive, errorsas, ifaceassert, nilfunc, **printf**, stdversion, stringintconv, and tests」)에 있는 것이 그것 하나이기 때문이다.
- ★★★ **`copylock1` — 「Inc passes lock by value: ex/copylock1.C contains sync.Mutex」** — 값 리시버 `func (c C)` 가 **뮤텍스째 복사**한다. 각 호출이 **자기 사본을 잠그니** 잠금이 아무것도 안 막는다. 대조 `copylock2`(포인터 리시버)는 조용하다.
- ★★★ **`loop121` 은 짚고 `loop127` 은 조용하다** — 소스는 같고 `//go:build go1.21` 한 줄만 다르다. **`loopclosure` 는 1.22 이후 파일에서는 할 말이 없다**(버그가 아니게 됐다 — 13번 (8)절). ★ 「1.22 이후 `loopclosure` 가 꺼지나」의 답은 **「분석기는 있고, 판을 보고 침묵한다」** 다.
- ★★ **`unused1` — 「result of fmt.Sprintf call not used」** · **`tag1` — 「bad syntax for struct tag value」**(`json: "a"` 의 공백) · **`tag2` — 「repeats json tag "x"」** · **`sigchan` — 「misuse of unbuffered os.Signal channel」**(51번과 이어진다 — 버퍼 없는 채널이면 신호를 놓칠 수 있다) · **`tgor`**(49번 (4)절).
- ★★★ **`httpresp1` — 「using resp before checking for errors」** — `defer resp.Body.Close()` 가 `err` 검사 **앞**에 있다. `err != nil` 이면 `resp` 가 `nil` 이라 **`defer` 가 panic** 한다. 47번의 「`Body` 를 닫아라」를 **순서까지** 지키라는 분석기다.
- ★★ **`printf2` — 동사를 변수로 넘기면 `vet exit 0`** — 42번 (1)절과 같은 구멍이다. `vet` 은 **상수 서식 문자열만** 읽는다.
- ★ 대조 셋(`printf2`·`copylock2`·`loop127`)이 **침묵한 것도 결론**이다 — 「안 물어본 것」이 아니라 「물었는데 조용한 것」이다(규칙 18-A).

비용 — `go vet ./...` 은 **컴파일보다 약간 더** 든다. CI 에 **따로** 둔다.

### (3) ★★ 빌드 태그 · 파일 이름 규칙 — 어느 파일이 빌드에 들어가나

```text
===== 소스: a.go =====
package tags

func A() string { return "a" }
===== 소스: a_test.go =====
package tags

import "testing"

func TestA(t *testing.T) {}
===== 소스: arch_amd64.go =====
package tags

func Arch() string { return "amd64" }
===== 소스: future.go =====
//go:build go1.99

package tags

func Future() {}
===== 소스: gen.go =====
//go:build ignore

package main

func main() {}
===== 소스: go.mod =====
module ex

go 1.27
===== 소스: nocgo.go =====
//go:build linux && !cgo

package tags

func Cgo() bool { return false }
===== 소스: os_linux.go =====
package tags

func OS() string { return "linux" }
===== 소스: os_windows.go =====
package tags

func OS() string { return "windows" }
===== 소스: withcgo.go =====
//go:build cgo || !linux

package tags

func Cgo() bool { return true }
===== 명령: set -- "linux amd64 0" "linux amd64 1" "windows amd64 0" "linux arm64 0"; for c in "$@"; do set -- $c; GOOS=$1 GOARCH=$2 CGO_ENABLED=$3 go list -f "{{range .GoFiles}}{{.}} G{{\"\\n\"}}{{end}}{{range .TestGoFiles}}{{.}} T{{\"\\n\"}}{{end}}" . > "$1-$2-$3.txt" || exit 1; done; printf "파일\tlinux/amd64 cgo=0\tlinux/amd64 cgo=1\twindows/amd64 cgo=0\tlinux/arm64 cgo=0\n"; for f in $(ls *.go | sort); do printf "%s" $f; for c in linux-amd64-0 linux-amd64-1 windows-amd64-0 linux-arm64-0; do k=$(awk -v f=$f "\$1==f {print \$2}" $c.txt); case $k in G) printf "\t빌드";; T) printf "\t테스트만";; *) printf "\t·";; esac; done; echo; done > grid.txt; cat grid.txt; awk -F"\t" "NF!=5 {bad=1} {for (i=2; i<=5; i++) {m++; if (\$i==\"빌드\") n++}} END {if (bad) print \"칸 수 어긋남\"; printf \"빌드에 들어간 칸 %d / %d\n\", n, m}" grid.txt =====
파일	linux/amd64 cgo=0	linux/amd64 cgo=1	windows/amd64 cgo=0	linux/arm64 cgo=0
a.go	빌드	빌드	빌드	빌드
a_test.go	테스트만	테스트만	테스트만	테스트만
arch_amd64.go	빌드	빌드	빌드	·
future.go	·	·	·	·
gen.go	·	·	·	·
nocgo.go	빌드	·	·	빌드
os_linux.go	빌드	빌드	·	빌드
os_windows.go	·	·	빌드	·
withcgo.go	·	빌드	빌드	·
빌드에 들어간 칸 15 / 36
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`os_linux.go` / `os_windows.go`** — 파일 이름 꼬리만으로 GOOS 가 갈린다(`//go:build` 줄이 없다). `arch_amd64.go` 는 **`linux/arm64` 에서 빠졌다.** 문서 「*_GOOS · *_GOARCH · *_GOOS_GOARCH … an implicit build constraint」.
- ★★★ **`nocgo.go`(`//go:build linux && !cgo`)** 와 **`withcgo.go`(`//go:build cgo || !linux`)** 는 **네 환경 모두에서 정확히 하나만** 들어갔다 — 두 식이 서로의 부정이라 **같은 함수 `Cgo()` 를 두 번 정의하지 않는다.** 이렇게 짝을 맞추지 않으면 어느 환경에서 **중복 정의** 또는 **정의 없음** 이 된다.
- ★★ **`windows/amd64 cgo=0` 에서 `withcgo.go` 가 들어갔다** — `!linux` 가 참이라서다. 이름이 「withcgo」여도 **식이 정한다.**
- ★★ **`gen.go`(`//go:build ignore`)** 는 어디서도 안 들어간다 — 관례적 이름일 뿐 **만족 안 되는 아무 낱말**이면 같다(문서 「Any other unsatisfied word will work as well」). `go run gen.go` 처럼 **따로 돌리는 파일**에 쓴다.
- ★★ **`future.go`(`//go:build go1.99`)** 도 빠졌다 — `go1.N` 태그는 **이 툴체인 판까지만** 참이다.
- ★ **`a_test.go` 는 「테스트만」** — `_test.go` 는 `go build` 에는 안 들어가고 `go test` 에서만(`TestGoFiles`).
- ★ 「빌드에 들어간 칸 **15 / 36**」.

### (4) ★★ `go:embed` — 패턴이 묶는 것 · 숨김 파일 · 에러

```text
===== 소스: embed.go =====
package main

import (
	"embed"
	"fmt"
	"io/fs"
	"strings"
)

//go:embed data
var dir embed.FS

//go:embed all:data
var dirAll embed.FS

//go:embed data/*
var star embed.FS

//go:embed data/a.txt
var one string

func list(f embed.FS) string {
	var names []string
	fs.WalkDir(f, ".", func(p string, d fs.DirEntry, err error) error {
		if !d.IsDir() {
			names = append(names, p)
		}
		return nil
	})
	return strings.Join(names, " ")
}

func main() {
	fmt.Printf("data\t%s\n", list(dir))
	fmt.Printf("all:data\t%s\n", list(dirAll))
	fmt.Printf("data/*\t%s\n", list(star))
	fmt.Printf("string data/a.txt\t%q\n", one)
}
===== 소스: go.mod =====
module ex

go 1.27
===== 명령: echo "── data 아래 파일"; find data -type f | sort; go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && ./prog =====
── data 아래 파일
data/.hidden
data/_under.txt
data/a.txt
data/sub/.h2
data/sub/b.txt
vet exit=0
data	data/a.txt data/sub/b.txt
all:data	data/.hidden data/_under.txt data/a.txt data/sub/.h2 data/sub/b.txt
data/*	data/.hidden data/_under.txt data/a.txt data/sub/b.txt
string data/a.txt	"a\n"
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`data` — `a.txt`·`sub/b.txt` 만** — `.hidden`·`_under.txt`·`sub/.h2` 가 빠졌다. 문서 「files with names beginning with ‘.’ or ‘_’ are excluded」.
- ★★★ **`all:data` — 다섯 개 전부** · **`data/*` — `.hidden`·`_under.txt` 는 들어가고 `sub/.h2` 는 빠졌다** — 문서 「‘image/*’ embeds ‘image/.tempfile’ while ‘image’ does not. **Neither embeds ‘image/dir/.tempfile’**」. `*` 는 **그 층에서 이름이 맞는 것**을 직접 고른 것이라 숨김 규칙이 안 걸리고, 그 아래 디렉토리(`sub`)는 **다시 디렉토리 규칙**으로 걸어 내려간다.
- ★ `string` 변수에 파일 하나 — `"a\n"`(끝의 줄바꿈까지).
- ★★ 이런 숨김 파일이 빠지는 게 사고가 되는 자리 — 정적 사이트의 **`_next/`**·**`.well-known/`** 같은 디렉토리. `all:` 을 붙여야 한다.

```text
===== 소스: go.mod =====
module ex

go 1.27
===== 소스: nope.go =====
package main

import _ "embed"

//go:embed nope.txt
var s string

func main() { println(len(s)) }
===== 소스: up.go =====
package main

import _ "embed"

//go:embed ../x.txt
var s string

func main() { println(len(s)) }
===== 명령: for p in nope up; do go build -trimpath -o /dev/null ./$p; echo "[$p] build exit=$?"; done =====
nope/nope.go:5:12: pattern nope.txt: no matching files found
[nope] build exit=1
up/up.go:5:12: pattern ../x.txt: invalid pattern syntax
[up] build exit=1
(exit 0)
```

- ★★★ **없는 파일 — `pattern nope.txt: no matching files found` · build exit 1** — 조용히 빈 값이 되지 않는다. **빌드가 막는다.**
- ★★★ **상위 디렉토리 — `pattern ../x.txt: invalid pattern syntax`** — 파일(`x.txt`)이 **실제로 있어도** 막힌다. 문서 「Patterns may not contain ‘.’ or ‘..’」. **패키지 디렉토리 밖은 묶을 수 없다.**

### (5) ★★★ 탈출 격자 — `-m` 의 말 · 실제 할당 · 인라인

**언제 쓰나** — 50번 `-benchmem` 에서 `allocs/op` 가 기대보다 클 때, **어디서** 할당이 나는지 찾을 때.

```text
===== 소스: esc.go =====
package main

import (
	"fmt"
	"io"
	"testing"
)

type pt struct{ x, y int }

var (
	sink  any
	psink *pt
	fsink func() int
	n     = 8
	m     = 4
)

func retVal() pt {
	p := pt{1, 2}
	return p
}

func retPtr() *pt {
	p := pt{1, 2}
	return &p
}

func toIface(v int) any {
	return v + 1000
}

func capture() func() int {
	c := 0
	return func() int { c++; return c }
}

func sliceConst() int {
	s := make([]int, 8)
	return len(s)
}

func sliceVar() int {
	s := make([]int, n)
	return len(s)
}

func sliceVarSmall() int {
	s := make([]int, m)
	return len(s)
}

func printIt(v int) {
	fmt.Fprintln(io.Discard, v)
}

func main() {
	probes := []struct {
		fn, name string
		f        func()
	}{
		{"retVal", "지역 값 반환", func() { p := retVal(); _ = p }},
		{"retPtr", "포인터 반환 — 전역에 담음", func() { psink = retPtr() }},
		{"retPtr", "포인터 반환 — 호출한 쪽에서 필드만 읽음", func() { p := retPtr(); _ = p.x }},
		{"toIface", "인터페이스에 담아 반환", func() { sink = toIface(n) }},
		{"capture", "클로저가 지역 변수를 잡아 반환", func() { fsink = capture() }},
		{"sliceConst", "make 크기 상수 8", func() { _ = sliceConst() }},
		{"sliceVar", "make 크기 변수 n=8", func() { _ = sliceVar() }},
		{"sliceVarSmall", "make 크기 변수 m=4", func() { _ = sliceVarSmall() }},
		{"printIt", "fmt.Fprintln 에 int 를 넘김", func() { printIt(n + 1000) }},
	}
	for _, p := range probes {
		fmt.Printf("%s\t%s\t%v\n", p.fn, p.name, testing.AllocsPerRun(100, p.f))
	}
}
===== 소스: go.mod =====
module ex

go 1.25
===== 소스: grid.sh =====
# grid.sh — -m 출력(m.txt)의 줄을 그 줄이 속한 함수에 붙이고, 할당 수(a1.txt · a2.txt)와 나란히 놓는다.
grep -n '^func ' esc.go | sed 's/^\([0-9]*\):func \([A-Za-z]*\).*/\1 \2/' > funcs.txt
awk 'NR==FNR { start[NR]=$1; name[NR]=$2; k=NR; next }
     match($0, /^ex\/esc\.go:[0-9]+/) {
       split(substr($0, RSTART, RLENGTH), a, ":"); ln=a[2]+0; f=""
       for (i=1; i<=k; i++) if (start[i] <= ln) f=name[i]
       msg=$0; sub(/^ex\/esc\.go:[0-9]+:[0-9]+: /, "", msg)
       if (f != "main") heap[f]=heap[f] (heap[f]=="" ? "" : " · ") msg
     }
     END { for (f in heap) print f "\t" heap[f] }' funcs.txt m.txt | sort > msgs.txt
printf '탐침\t-m 이 그 함수에 대해 한 말\tallocs(-l)\tallocs(인라인 켬)\n'
paste a1.txt a2.txt | awk -F'\t' 'NR==FNR { m[$1]=$2; next }
  NF!=6 || $1!=$4 || $2!=$5 { bad=1 }
  { f=$1; msg=(f in m) ? m[f] : "(한 줄도 없음)"
    printf "%s\t%s\t%s\t%s\n", $2, msg, $3, $6; t++
    said = (msg ~ /escapes to heap|moved to heap/) ? 1 : 0
    heap = ($3+0 >= 1) ? 1 : 0
    if (said) s++; if (heap) h++; if (said != heap) x++; if ($3 != $6) y++ }
  END { if (bad) print "칸 수 어긋남"
        printf "-m 이 힙을 말한 칸 %d / %d\n", s, t
        printf "allocs(-l) 가 1 이상인 칸 %d / %d\n", h, t
        printf "둘이 어긋난 칸 %d / %d\n", x, t
        printf "인라인을 켜서 allocs 가 달라진 칸 %d / %d\n", y, t }' msgs.txt -
===== 명령: go build -trimpath -gcflags="-m -l" -o p1 . 2>m.txt && go build -trimpath -o p2 . && ./p1 > a1.txt && ./p2 > a2.txt || exit 1; bash grid.sh; "$GO125" build -trimpath -gcflags="-m -l" -o /dev/null . 2>m125.txt; echo "go1.25.12 의 -m 출력과 다른 줄 $(diff m.txt m125.txt | grep -c "^[<>]")" =====
탐침	-m 이 그 함수에 대해 한 말	allocs(-l)	allocs(인라인 켬)
지역 값 반환	(한 줄도 없음)	0	0
포인터 반환 — 전역에 담음	moved to heap: p	1	1
포인터 반환 — 호출한 쪽에서 필드만 읽음	moved to heap: p	1	0
인터페이스에 담아 반환	v + 1000 escapes to heap	1	1
클로저가 지역 변수를 잡아 반환	moved to heap: c · func literal escapes to heap	2	2
make 크기 상수 8	make([]int, 8) does not escape	0	0
make 크기 변수 n=8	make([]int, n) does not escape	1	1
make 크기 변수 m=4	make([]int, m) does not escape	0	0
fmt.Fprintln 에 int 를 넘김	... argument does not escape · v escapes to heap	1	1
-m 이 힙을 말한 칸 5 / 9
allocs(-l) 가 1 이상인 칸 6 / 9
둘이 어긋난 칸 1 / 9
인라인을 켜서 allocs 가 달라진 칸 1 / 9
go1.25.12 의 -m 출력과 다른 줄 0
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **지역 값 반환(`retVal`) — `-m` 은 한 줄도 없고 할당 0** — 값은 **복사되어** 나간다. 스택에 둔 채 끝난다.
- ★★★ **포인터 반환(`retPtr`) — `moved to heap: p` · 할당 1** — `p` 의 주소가 함수 밖으로 나가므로 **변수 자체를 힙에 만든다.**
- ★★★ **그런데 인라인을 켜면(기본 빌드) 「호출한 쪽에서 필드만 읽음」 칸이 0** — 「인라인을 켜서 달라진 칸 **1 / 9**」. `retPtr` 이 호출한 자리로 **펴지면** 컴파일러가 `p` 가 **그 자리를 못 벗어난다**는 것을 보고 스택에 둔다. 전역에 담은 칸은 여전히 1. ★★ **「이 함수는 힙에 할당한다」가 아니라 「이 호출은 …」** 이다.
- ★★ **인터페이스에 담기(`toIface`) — `v + 1000 escapes to heap` · 1** · **클로저(`capture`) — `moved to heap: c` · `func literal escapes to heap` · 2**(변수 하나 + 클로저 하나) — 13번 (7)절과 같다.
- ★★★ **`make([]int, 8)` — `does not escape` · 0** 대 **`make([]int, n)`(n=8) — `does not escape` 인데 1** 대 **`make([]int, m)`(m=4) — 0** — 「둘이 어긋난 칸 **1 / 9**」가 이것이다. 크기가 **컴파일 때 모르는 값**이면 「탈출 안 함」이어도 **작을 때만** 스택에 담겼다(이 판의 관찰 — 경계 크기는 재지 않았다: 4 원소는 0, 8 원소는 1).
- ★★ **`fmt.Fprintln(io.Discard, v)` — `v escapes to heap` · 1** — `...any` 인자에 담으면서 **박싱**된다. `... argument does not escape` 는 **가변 인자 슬라이스 자체**는 스택이라는 뜻이다. ★ 로그 한 줄마다 할당이 나는 이유다.
- ★★ **「go1.25.12 의 -m 출력과 다른 줄 0」** — 두 판이 **이 소스에서** 같은 결정을 했다. 보장은 아니다.
- ★ `-l` 을 붙인 이유 — 안 붙이면 `inlining call to …` 줄이 섞여 **읽을 줄이 묻힌다**(13번 (7)절). 대신 **인라인이 바꾸는 결정**은 `-l` 판만 보면 놓친다 — 그래서 할당은 두 빌드에서 쟀다.

비용 — `-gcflags=-m` 은 **빌드 한 번**이다. 줄이 많으면 `-m` 을 **패키지 하나에만**(`-gcflags=ex=-m`) 건다.

## 문법 — 형태와 규칙

### 형태

```text
   gofmt -l .                     ← 포맷 안 된 파일 이름 (있어도 exit 0 — 출력이 비었나로 판정)
   gofmt -s -d file.go            ← 단순화까지 diff 로
   go vet ./...                   ← 분석기 전부 (go test 는 부분 집합)
   go vet -copylocks=false ./...  ← 하나 끄기

   //go:build linux && !cgo       ← 파일 첫머리 · 뒤에 빈 줄 · package 앞
   //go:build cgo || !linux       ← 짝을 맞춰 정확히 하나가 참이 되게
   os_linux.go · arch_amd64.go    ← 파일 이름만으로도 제약

   //go:embed data                ← . · _ 로 시작하는 것 제외 (재귀)
   //go:embed all:data            ← 전부
   //go:embed data/*              ← 그 층의 숨김 파일은 포함, 하위의 것은 제외
   var content embed.FS            ← 패키지 수준 변수 · import "embed" 필요

   go build -gcflags='-m -l' .    ← 탈출 결정 (인라인 끔) · -m -m 이면 이유까지
```

- `//go:build` 줄은 **`package` 줄보다 앞**, 그 뒤에 **빈 줄**.
- `//go:embed` 는 **`//` 와 `go:` 사이에 공백 없이** · 바로 아래 변수 하나.

### 금지 사례 — 누가 잡나

| 쓴 꼴 | 누가 잡나 | 어디서 |
|---|---|---|
| `//go:embed ../x.txt` | ★★ **빌드 에러** `invalid pattern syntax` | (4)절 |
| `//go:embed nope.txt`(없음) | ★★ **빌드 에러** `no matching files found` | (4)절 |
| 값 리시버에 `sync.Mutex` | ★★ **`go vet`(`copylocks`)** 만 | (2)절 |
| `resp.Body.Close()` 를 `err` 검사 앞에 | ★★ **`go vet`(`httpresponse`)** 만 | (2)절 |
| 동사를 변수로 넘긴 `Printf` | ★★★ **아무도 안 잡는다** | (2)절 `printf2` · 42번 |
| `//go:build` 짝이 안 맞아 한 환경에서 중복 정의 | ★★ **그 환경의 빌드**에서만 — 다른 환경에서는 안 보인다 | (3)절 |

## 어디서 틀리나

### 1. ★★★ 「`go test` 가 `vet` 을 돌리니 충분하다」

12 중 **1**(`printf1`)만 막았다((2)절). `copylocks`·`httpresponse`·`loopclosure`·`testinggoroutine` 은 **`go vet` 만** 잡았다.

### 2. ★★★ 「`-m` 이 `does not escape` 면 할당이 없다」

`make([]int, n)`(n=8)은 `does not escape` 인데 **할당 1**((5)절). 할당은 `AllocsPerRun`·`allocs/op` 로 확인한다.

### 3. ★★★ 「`retPtr` 은 힙에 할당하는 함수다」

**인라인되면 0** 이었다((5)절). 탈출은 **부르는 자리마다** 다시 결정된다 — `-l` 판의 `-m` 만 보고 단정하지 마라.

### 4. ★★ 「`loopclosure` 는 1.22 이후 없어졌다」

**있다** — 1.22 이후 **파일**에서 할 말이 없을 뿐이다((2)절 `loop121` 대 `loop127`). 같은 모듈에 옛 판 파일이 섞이면 **그 파일만** 짚는다.

### 5. ★★ 「`go:embed data` 면 `data` 아래가 다 들어간다」

**`.`·`_` 로 시작하는 것이 빠진다**((4)절). `data/*` 는 **그 층만** 넣는다. 전부면 `all:`.

### 6. ★★ 「`gofmt` 가 긴 줄도 접어 준다」

**안 접는다**((1)절 마지막 줄). 그리고 **`gofmt -l` 은 파일이 있어도 `exit 0`** 이다.

### 7. ★ 「`//go:build ignore` 는 특별한 키워드다」

**만족 안 되는 아무 낱말**이면 된다 — `ignore` 는 관례다((3)절 · 문서).

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| 스택·힙 | ★★★ **명세에 없다** — 컴파일러의 결정 | (5)절 · 13번 (7)절 |
| `-m` 의 문구 · 인라인이 탈출을 바꿈 · 가변 크기 `make` 의 스택 한도 | ★★★ **gc 컴파일러 판** | (5)절 |
| `vet` 분석기 목록 · `go test` 부분 집합 | ★★ **`go` 명령 판** | (2)절 `t52vetdoc` |
| `loopclosure` 가 판을 본다 | **분석기 구현** + 언어 판(1.22) | (2)절 |
| 빌드 제약 식 · 파일 이름 규칙 · `go1.N` 태그 | **도구 계약**(`go help buildconstraint`) | (3)절 |
| `go:embed` 패턴 규칙 | **도구 계약**(`embed` 문서) | (4)절 |
| `gofmt` 출력 | **도구 구현**(하나로 정해져 있다는 것이 계약) | (1)절 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 저장·커밋 | **`gofmt`**(편집기) · CI 는 `test -z "$(gofmt -l .)"` | (1)절 |
| CI | ★★★ **`go vet ./...` 을 `go test` 와 따로** | (2)절 `1 / 12` |
| OS·아키텍처별 구현 | **파일 이름 꼬리** 먼저 · 조건이 복잡하면 `//go:build` | (3)절 |
| cgo 유무로 갈라야 | **짝이 되는 두 식** — 서로의 부정 | (3)절 |
| 정적 파일 묶기 | `//go:embed` · 숨김 디렉토리가 있으면 **`all:`** | (4)절 |
| 할당 원인 찾기 | ★★ **`-gcflags='-m'`(인라인 켠 채) + `allocs`** | (5)절 · 50번 |
| 「힙이 느리니 고치자」 | ★★ **먼저 50번의 `allocs/op`·`ns/op`** 로 잰다 | 이 문서는 속도를 재지 않았다 |

## 핵심 문장

- ★★ **`gofmt` 는 모양을 하나로 정해 논쟁을 없앤다** — 줄 길이는 안 정한다 · `-s` 는 표현까지 줄인다 · `-l` 은 늘 `exit 0`.
- ★★★ **`go vet` 은 12 중 9 를 짚었고 `go test` 는 1 만 막았다** — `go test` 의 `vet` 은 부분 집합이다.
- ★★ **빌드 태그는 식이 정한다** — 짝 식은 네 환경 모두에서 정확히 하나만 참(`15 / 36`) · `go1.99` 는 빠진다.
- ★★ **`go:embed` 는 `.`·`_` 로 시작하는 것을 뺀다** — `dir/*` 는 그 층만 넣고, `all:` 은 전부 · 없는 파일·`..` 은 빌드 에러.
- ★★★ **`-m` 의 말과 실제 할당은 다른 질문의 답이다** — `does not escape` 인데 할당(`make([]int, n)`) · `escapes` 인데 0(50번 `BoxSmall`) · **인라인이 결정을 바꾼다**(`retPtr` 1 → 0).

## 관련 자료

- `go doc cmd/vet` · `go help test` · `go help buildconstraint` · [`embed`](https://pkg.go.dev/embed) · `go tool compile -help` — 이 툴체인에서 떴다.
- [`cs/foundations/memory-management/`](../../../../memory-management/) — ★ **스택·힙 일반의 정본**(§3 스택 프레임 · §11 다이나믹 힙). 그쪽은 메모리 계층까지, 여기는 **Go 컴파일러가 어디에 두는지 읽는 법**부터. GC 알고리즘 절은 거기에도 없다.
- [13번 주제](../13-closures-variable-capture-and-loop-variable-change/) — 클로저 캡처가 `moved to heap` · `vet` 이 판을 안다.
- [34번 주제](../34-context-cancellation-deadlines-and-values/) — `vet lostcancel` 탐침 11개.
- [41번 주제](../41-modules-go-mod-version-selection-and-workspaces/) — `go.mod` 의 `go` 줄 · 빌드 태그 `go1.N` 과 짝.
- [42번 주제](../42-fmt-verbs-stringer-and-errorf/) — `vet printf` 여섯 줄과 동사를 변수로 넘긴 구멍.
- [47번 주제](../47-net-http-client-reuse-timeouts-and-closing-body/) — `Body` 닫기 · `httpresponse` 가 그 순서를 본다.
- [49번 주제](../49-testing-table-driven-t-run-cleanup-and-parallel/) — `loopclosure`·`testinggoroutine` 이 테스트에서 새는 자리.
- [50번 주제](../50-benchmarks-testing-b-and-reading-profiles/) — `allocs/op` · `escapes` 인데 0 인 반대 칸.
- [51번 주제](../51-os-signal-and-graceful-shutdown/) — `sigchanyzer` 가 지키는 신호 채널.

## 용어 풀이

- **`gofmt`** — Go 표준 포매터. `-d` diff · `-l` 파일 이름 · `-s` 단순화 · `-w` 덮어쓰기.
- **`go vet`** — 컴파일은 되는 수상한 코드를 짚는 분석기 묶음. 발견하면 exit 1.
- **분석기(analyzer)** — `vet` 안의 검사 하나(`printf`·`copylocks` 등). `go tool vet help` 로 목록.
- **`//go:build`** — 파일 단위 빌드 제약 줄(1.17+). `&&`·`||`·`!`·괄호.
- **`go:embed`** — 빌드 때 파일을 변수(`string`·`[]byte`·`embed.FS`)에 묶는 지시문(1.16+).
- **`-gcflags`** — `go build` 가 컴파일러에 넘기는 플래그. `-m` 최적화 결정 출력 · `-l` 인라인 끔.
- **`moved to heap` / `escapes to heap` / `does not escape`** — 변수 자체를 힙에 · 값을 힙에 복사 · 스택에 둘 수 있음.
- **`testing.AllocsPerRun(n, f)`** — `f` 를 n 번 돌린 평균 할당 수. 테스트 밖에서도 쓸 수 있다.

## 더 들어가면

- ★ **`-gcflags='-m -m'`** — 탈출한 **이유의 사슬**까지 찍는다. 돌리지 않았다.
- ★ **`go vet` 에 분석기 더하기** — `golang.org/x/tools/go/analysis` 로 자기 분석기를 만들 수 있다. 이 배치는 외부 모듈을 쓰지 않았다.
- ★ **`//go:embed` 와 `go:generate`** — 생성한 파일을 묶는 조합. 돌리지 않았다.

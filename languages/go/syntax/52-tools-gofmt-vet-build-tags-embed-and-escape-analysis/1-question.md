# go/syntax/52 — 도구: `gofmt`·`go vet`·빌드 태그·`go:embed`·탈출 분석 읽기 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ **모든 문제에서 「이 동작은 명세인가, 도구 문서의 계약인가, 컴파일러·도구 판의 성질인가」를 먼저 적어라.**
> 모든 실험은 `module ex`(`go 1.27` — 탈출 격자만 `go 1.25`) 이고 `go1.27.1` 에서 돌렸다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 흐트러진 소스 한 장 (예측)

```go
// t52fmt.go
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
```

<!-- gofmt -d 를 돌리고, 따로 gofmt 결과와 gofmt -s 결과를 diff 하고, gofmt -l . 을 돌렸다. -->

- `gofmt -d` 가 **바꾸는 것**과 **안 바꾸는 것**은? `-s` 가 더 바꾸는 줄은 어느 셋인가? `gofmt -d` 와 `gofmt -l` 의 종료 코드는?

### 2. 탐침 열둘 (예측)

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
```

<!-- 탐침마다 go vet ./<탐침> 과 go test -count=1 -run "^$" ./<탐침> 의 종료 코드를 찍고, 둘이 0 이 아닌 칸을 센다. go vet 이 낸 줄도 모아 찍는다. -->

- 어느 탐침에서 `go vet` 이 짚나(몇 / 12)? `go test` 는 몇 / 12 를 막나 — 그리고 **어느 것**인가?

### 3. `go test` 가 막은 하나 (왜)

- 2번에서 `go test` 가 막은 칸이 그것 하나뿐인 이유는? `go help test` 의 어느 문장이 그 목록을 정하나?

### 4. 파일 아홉 · 환경 넷 (예측)

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
```

<!-- 환경 넷(linux/amd64 cgo=0 · linux/amd64 cgo=1 · windows/amd64 cgo=0 · linux/arm64 cgo=0)에서 go list 로 GoFiles·TestGoFiles 를 떠, 파일마다 「빌드 / 테스트만 / ·」 으로 찍는다. -->

- 파일마다 어느 환경에서 빌드에 들어가나? `nocgo.go` 와 `withcgo.go` 는 몇 환경에서 **둘 다** 들어가나? `future.go`·`gen.go` 는?

### 5. 숨김 파일 셋 (예측)

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
```

<!-- 모듈 안 data/ 아래 파일 — .hidden · _under.txt · a.txt · sub/.h2 · sub/b.txt. go build 뒤 실행했다. -->

- `data` · `all:data` · `data/*` 세 변수에 각각 어떤 파일이 들어가나? `sub/.h2` 는 어느 변수에 들어가나?

### 6. 없는 파일 · 위쪽 파일 (예측)

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
```

<!-- 모듈 루트에 x.txt 가 실제로 있다. 두 패키지를 go build -o /dev/null ./nope · ./up 으로 빌드했다. -->

- 두 패키지를 빌드하면 각각 무엇이 나오나? `x.txt` 가 **실제로 있는데도** 결과가 같은가?

### 7. 탐침 아홉의 탈출 (예측)

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
```

<!-- -gcflags="-m -l" 로 빌드한 판(p1)과 기본 빌드(p2)를 각각 돌려 탐침마다 AllocsPerRun 을 찍고, grid.sh 가 -m 줄을 함수에 붙여 나란히 놓는다. 마지막 줄은 go1.25.12 로 같은 -m 을 뜬 것과의 차이. -->

- 탐침마다 `-m` 은 무엇이라 말하고 할당은 몇인가? 네 개의 「칸 수」 줄의 값은?

### 8. 「`does not escape` 면 스택」 (경계)

- 7번에서 `-m` 의 말과 할당 수가 어긋난 칸은? [50번 주제](../50-benchmarks-testing-b-and-reading-profiles/)의 `BoxSmall` 은 반대 방향으로 어긋났다. 둘을 합쳐 `-m` 은 **무엇에 답하는 창**인가?

### 9. 인라인이 바꾼 칸 (왜)

- 7번에서 `retPtr` 은 `-l` 판에서 두 칸 다 할당 1 인데, 기본 빌드에서는 한 칸만 0 이 됐다. 왜 **그 칸**만인가? 「이 함수는 힙에 할당한다」는 말이 왜 부정확한가?

### 10. `loopclosure` 는 꺼졌나 (연결)

- 2번의 `loop121` 대 `loop127` 과 [13번 주제](../13-closures-variable-capture-and-loop-variable-change/) (8)절을 이어서 — 1.22 이후 `loopclosure` 분석기는 **없어진 것**인가, **침묵하는 것**인가? 그 차이가 드러나는 코드베이스는 어떤 모양인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

# go/syntax/52 — 도구: `gofmt`·`go vet`·빌드 태그·`go:embed`·탈출 분석 읽기 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`**(탈출 격자의 마지막 줄만 `go1.25.12` 와 대조)에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★ **근거로 읽을 칸** — `gofmt` diff · 종료 코드 · `vet` 격자와 문구 · `9 / 12` · `1 / 12` · 빌드 태그 격자 `15 / 36` · `embed` 목록과 에러 · 탈출 격자의 네 칸 수.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 바꾸는 것 — 공백·탭 들여쓰기·빈 줄·중괄호와 한 줄 `for` 펼치기 · 안 바꾸는 것 — **긴 줄**, 그리고 `point{1, 2}`·`for _ =`·`s[2:len(s)]` 같은 **표현** · `-s` 가 더 바꾸는 셋 — `{1, 2}` · `for range` · `s[2:]` · `gofmt -d exit=1` · `gofmt -l exit=0`

**출력**

```text
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

```text
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

- ★★ `gofmt` 는 **모양**만, `-s` 는 **뜻이 같은 짧은 표현**까지. 줄 길이는 사람 몫이다.
- ★★ `-l` 은 파일이 나와도 0 — CI 는 **출력이 비었나**로 본다.

### 2. `go vet` — `printf1`·`copylock1`·`loop121`·`unused1`·`tag1`·`tag2`·`httpresp1`·`sigchan`·`tgor` 의 **9 / 12**(`printf2`·`copylock2`·`loop127` 은 조용) · `go test` — **`printf1` 하나, 1 / 12**

**출력**

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

**왜 그런가**

- ★★★ `printf2` 는 서식 실수가 **그대로인데** 조용하다 — 동사를 변수로 넘겨 `vet` 이 읽을 수 없다(42번 (1)절).
- ★★ `copylock2`·`loop127` 은 **고친 판**이라 조용한 것 — 대조 칸이다.

### 3. `go test` 는 「**Only a high-confidence subset** of the default go vet checks」만 돌리고, 그 목록에 이 열둘 중 **`printf` 만** 있다

**출력**

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

- ★★ 목록 — 「atomic, bools, buildtag, directive, errorsas, ifaceassert, nilfunc, printf, stdversion, stringintconv, and tests」. `copylocks`·`loopclosure`·`unusedresult`·`structtag`·`httpresponse`·`sigchanyzer`·`testinggoroutine` 은 없다.
- ★ 목록은 **`go` 명령 판의 성질**이다 — 판이 오르면 다시 확인한다.

### 4. `a.go` 넷 다 · `a_test.go` 테스트만 · `arch_amd64.go` arm64 만 빠짐 · `os_linux.go`/`os_windows.go` 는 OS 대로 · `nocgo.go` 와 `withcgo.go` 는 **둘 다 들어간 환경 0** — 늘 하나만 · `future.go`·`gen.go` 는 **어디서도 안 들어간다** — `15 / 36`

**출력**

```text
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

- ★★★ 두 식이 서로의 부정이라 **정확히 하나**만 참이다 — `windows/amd64 cgo=0` 에서는 `!linux` 로 `withcgo.go`.
- ★★ `go1.99` 는 「through the current version」 밖이다 · `ignore` 는 만족 안 되는 낱말일 뿐이다(`t52doc`).

### 5. `data` — `a.txt`·`sub/b.txt` · `all:data` — 다섯 전부 · `data/*` — `.hidden`·`_under.txt`·`a.txt`·`sub/b.txt` · `sub/.h2` 는 **`all:data` 에만**

**출력**

```text
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

- ★★★ 문서 — 디렉토리는 「files with names beginning with ‘.’ or ‘_’ are excluded」 · 「‘image/*’ embeds ‘image/.tempfile’ … **Neither embeds ‘image/dir/.tempfile’**」 · 「‘all:image’ embeds both」(`t52doc`).

### 6. `nope` — `pattern nope.txt: no matching files found`(build exit 1) · `up` — `pattern ../x.txt: invalid pattern syntax`(build exit 1) · `x.txt` 가 있어도 **같다** — 패턴 문법에서 막힌다

**출력**

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

- ★★ 문서 — 「Patterns may not contain ‘.’ or ‘..’」. 파일이 있나를 보기 **전에** 거절된다.

### 7. 지역 값 — 없음·0·0 · 포인터 전역 — `moved to heap: p`·1·1 · 포인터 필드만 — `moved to heap: p`·**1·0** · 인터페이스 — `escapes`·1·1 · 클로저 — `moved to heap: c`·`func literal escapes`·2·2 · `make` 상수 8 — `does not escape`·0·0 · `make` 변수 n=8 — `does not escape`·**1**·1 · `make` 변수 m=4 — `does not escape`·0·0 · `Fprintln` — `v escapes`·1·1 — `5 / 9` · `6 / 9` · `1 / 9` · `1 / 9`

**출력**

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

- ★★ `go1.25.12` 의 `-m` 과 **다른 줄 0** — 이 소스에서는 두 판이 같았다. 보장은 아니다.

### 8. `make([]int, n)`(n=8) — `does not escape` 인데 **할당 1** · `-m` 은 「**이 값이 함수 밖으로 나가나**」에 답하는 창이지 「**할당이 나나**」에 답하는 창이 아니다

- ★★★ 이 판에서 크기를 컴파일 때 모르는 `make` 는 **작으면(4) 스택, 크면(8) 힙**이었다(경계는 재지 않았다) — 탈출과 무관한 **크기** 조건이다.
- ★★ 50번 `BoxSmall` — `escapes to heap` 인데 0 allocs(작은 정수는 런타임이 미리 만든 값을 가리킨다). **두 창을 같이 봐야** 한다 — 할당은 `AllocsPerRun`·`allocs/op`.

### 9. 기본 빌드에서 `retPtr` 이 **호출한 자리로 인라인**되면, 결과를 **그 자리에서 필드만 읽고 버리는** 칸은 `p` 가 그 함수를 못 벗어나 스택에 둔다 · 전역에 담는 칸은 여전히 밖으로 나가 1 · 탈출은 **함수가 아니라 부르는 자리마다** 결정된다

- ★★ 7번 「인라인을 켜서 allocs 가 달라진 칸 1 / 9」가 바로 그 칸이다.
- ★ 그래서 `-l` 판의 `-m` 만 읽으면 **실제 빌드보다 할당이 많아 보인다.**

### 10. **침묵하는 것**이다 — `loop121`(`//go:build go1.21`)은 짚고 `loop127` 은 조용했다 · 드러나는 모양 — **한 모듈에 옛 판 파일이 섞였거나 `go.mod` 의 `go` 줄이 1.22 미만**인 코드베이스

- ★★ 13번 (8)절 — 같은 소스를 `go 1.21` 모듈에서 `vet` 하면 짚고 `go 1.27` 이면 exit 0. [49번 주제](../49-testing-table-driven-t-run-cleanup-and-parallel/) (3)절의 `t49loop121` 은 `go.mod` 를 내리자 **두 파일 다** 짚였다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 로 **★고칠 것 0** |
| ★★★ `vet` 격자 (`t52vet`) | 탐침 12 × (`go vet` · `go test -run ^$`) · 탭 3칸 검사 | 캡처마다 | **`9 / 12` · `1 / 12`** |
| ★★★ 탈출 격자 (`t52esc`) | `-m -l` · `AllocsPerRun` 두 빌드 · `grid.sh` 탭 6칸 검사 · `go1.25.12` 대조 | 캡처마다 | **`5 / 9` · `6 / 9` · `1 / 9` · `1 / 9`** · 다른 줄 0 |
| ★★ 빌드 태그 (`t52tags`) | 환경 4 × `go list` | 캡처마다 | `15 / 36` |
| ★★ `go:embed` (`t52embed`·`t52embbad`) | 세 패턴 · 에러 둘 | 캡처마다 | 문서 네 문장 재현 |
| ★ `gofmt` (`t52fmt`·`t52fmts`) | `-d` · `-s` diff · `-l` | 캡처마다 | |

**구현·환경에 달린 항목**

| 항목 | 무엇에 달렸나 |
|---|---|
| `-m` 의 결정·문구 · 인라인 · 가변 크기 `make` 한도 | **gc 컴파일러 판** |
| `vet` 분석기 · `go test` 부분 집합 | **`go` 명령 판** |
| 빌드 제약 · `embed` 패턴 | **도구 계약** |
| 스택·힙이 있다는 것 자체 | ★ **명세에 없다** |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다(기본 규칙만). `GO125` 가 가리키는 `go1.25.12` 가 있어야 탈출 격자의 마지막 줄이 돈다.

# go/syntax/44 — `os`·`bufio`·`io.Copy` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ **모든 문제에서 「이 동작은 명세인가, 표준 라이브러리 문서의 계약인가, 이 머신(OS·파일 시스템)의 관찰인가」를 먼저 적어라.**
> 모든 Go 실험은 `module ex` · `go 1.27` 이고 `go build -trimpath` 로 빌드해 돌렸다. 시스템 호출은 `strace` 로 셌다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 쓰는 법과 끝내는 법 (예측)

```go
// t44exit.go
package main

import (
	"bufio"
	"log"
	"os"
	"strings"
)

// 인자: <쓰는 법> <끝내는 법>
//   쓰는 법   — flush(다 쓰고 Flush) · noflush(Flush 없음) · defer(defer w.Flush()) · direct(bufio 없이 f.Write)
//   끝내는 법 — return · exit(os.Exit(0)) · fatal(log.Fatal) · panic
func main() {
	how, end := os.Args[1], os.Args[2]
	f, err := os.Create("out.bin")
	if err != nil {
		log.Fatal(err)
	}
	data := strings.Repeat("x", 100)
	if how == "direct" {
		f.WriteString(data)
	} else {
		w := bufio.NewWriter(f)
		if how == "defer" {
			defer w.Flush()
		}
		w.WriteString(data)
		if how == "flush" {
			w.Flush()
		}
	}
	switch end {
	case "exit":
		os.Exit(0)
	case "fatal":
		log.Fatal("끝")
	case "panic":
		panic("끝")
	}
}
```

<!-- 빌드한 뒤, 쓰는 법 direct·flush·noflush·defer × 끝내는 법 return·exit·fatal·panic 열여섯 번을 돌리고 매번 out.bin 의 크기를 stat 으로 잰다(stdout 은 버리고 stderr 는 파일로). 마지막 줄에 100 바이트보다 작은 칸 수. -->

- 열여섯 칸 각각의 파일 크기는? 마지막 줄의 수는?

### 2. `defer` 줄의 칸들 (왜)

- 1번에서 `defer` 줄의 `panic` 칸과 `exit` 칸이 다른 이유를 [26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/) (6)절과 [27번 주제](../27-panic-recover-and-where-to-use-them/)로 설명하라. 각각 **명세**인가 **`os` 패키지의 계약**인가?

### 3. `/dev/full` 과 `Close` (예측)

```go
// t44close.go
package main

import (
	"bufio"
	"fmt"
	"os"
)

func size(name string) int64 {
	st, err := os.Stat(name)
	if err != nil {
		return -1
	}
	return st.Size()
}

func main() {
	fmt.Println("c1 /dev/full 에 f.Write → f.Sync → f.Close")
	f, _ := os.OpenFile("/dev/full", os.O_WRONLY, 0)
	n, err := f.Write([]byte("hello"))
	fmt.Printf("   Write n=%d err=%v\n", n, err)
	fmt.Printf("   Sync  err=%v\n", f.Sync())
	fmt.Printf("   Close err=%v\n", f.Close())

	fmt.Println("c2 /dev/full 에 bufio 로 쓰고 Flush 없이 f.Close")
	f, _ = os.OpenFile("/dev/full", os.O_WRONLY, 0)
	w := bufio.NewWriter(f)
	n, err = w.WriteString("hello")
	fmt.Printf("   WriteString n=%d err=%v · Buffered=%d · Size=%d\n", n, err, w.Buffered(), w.Size())
	fmt.Printf("   Close err=%v\n", f.Close())

	fmt.Println("c3 보통 파일에 bufio 로 쓰고 Flush 없이 f.Close")
	f, _ = os.Create("c3.txt")
	w = bufio.NewWriter(f)
	w.WriteString("hello")
	fmt.Printf("   Close err=%v · 파일 크기=%d\n", f.Close(), size("c3.txt"))

	fmt.Println("c4 f.Close 를 두 번")
	f, _ = os.Create("c4.txt")
	fmt.Printf("   첫 Close err=%v\n", f.Close())
	fmt.Printf("   둘째 Close err=%v\n", f.Close())
	fmt.Printf("   닫힌 뒤 Write err=%v\n", func() error { _, e := f.Write([]byte("x")); return e }())
}
```

- `c1`\~`c4` 의 각 줄에 찍히는 에러는? **`Close` 가 에러를 돌려준 줄**은 어느 것인가?

### 4. 「`defer f.Close()` 가 쓰기 에러를 삼킨다」 (경계)

- 3번의 결과로 보면 이 머신에서 쓰기 에러는 **어디서** 보고됐나? 그렇다면 [26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/) (5)절의 `dropped : <nil>` 은 **무엇이** 에러를 삼킨 것이었나? `Close` 의 에러를 그래도 받아야 하는 이유는?

### 5. `fmt.Println` 과 `bufio` 의 `write` (예측)

```go
// t44sys.go
package main

import (
	"bufio"
	"fmt"
	"os"
)

// 인자: println(fmt.Println 세 번) · bufio(bufio.Writer 에 세 번 + Flush 한 번)
func main() {
	if os.Args[1] == "println" {
		for i := 1; i <= 3; i++ {
			fmt.Println("줄", i)
		}
		return
	}
	w := bufio.NewWriter(os.Stdout)
	for i := 1; i <= 3; i++ {
		fmt.Fprintln(w, "줄", i)
	}
	w.Flush()
}
```

<!-- 빌드한 뒤 두 모드를 strace -f -e trace=write 로 돌려 stdout 을 파일로 받고, fd 1 로 간 write 호출 수와 받은 바이트를 센다. -->

- 두 모드의 `write` 호출 수와 받은 바이트는?

### 6. C 의 `exit` 와 `_exit` (연결)

```c
/* t44stdio.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

/* 인자: exit 또는 _exit. printf 세 줄을 찍고 그 방법으로 끝낸다. */
int main(int argc, char **argv) {
    for (int i = 1; i <= 3; i++)
        printf("줄 %d\n", i);
    if (argc > 1 && strcmp(argv[1], "_exit") == 0)
        _exit(0);
    exit(0);
}
```

- 이 프로그램을 stdout 을 파일로 돌려 `strace` 로 세면 `exit`·`_exit` 두 모드의 `write` 수와 받은 바이트는? 1번의 `noflush × return` 과 견주면 Go 는 어느 쪽인가?

### 7. 아주 긴 줄 (예측)

```go
// t44scan.go
package main

import (
	"bufio"
	"fmt"
	"strings"
)

// scan 은 길이 n 인 줄 하나와 짧은 줄 하나를 Scanner 로 읽는다.
func scan(n int, big bool) {
	in := strings.Repeat("x", n) + "\n" + "다음 줄\n"
	sc := bufio.NewScanner(strings.NewReader(in))
	if big {
		sc.Buffer(make([]byte, 0, 4096), 1<<20)
	}
	lines := 0
	for sc.Scan() {
		lines++
	}
	fmt.Printf("  줄 길이 %6d · Buffer 키움=%-5v → Scan 이 참이었던 횟수 %d · Err=%v\n", n, big, lines, sc.Err())
}

func main() {
	fmt.Println("bufio.MaxScanTokenSize =", bufio.MaxScanTokenSize)
	for _, n := range []int{65535, 65536, 70000} {
		scan(n, false)
	}
	scan(70000, true)
}
```

- 네 줄 각각의 `Scan` 횟수와 `Err` 는? 긴 줄 **뒤의 짧은 줄**은 읽혔나?

### 8. `io.Copy` 가 부른 `Write` (예측)

```go
// t44copy.go
package main

import (
	"bufio"
	"bytes"
	"fmt"
	"io"
	"os"
	"strings"
)

// counter 는 Write 가 몇 번, 몇 바이트씩 불렸는지 적는다.
type counter struct{ sizes []int }

func (c *counter) Write(p []byte) (int, error) {
	c.sizes = append(c.sizes, len(p))
	return len(p), nil
}

// onlyReader 는 io.Reader 만 남기고 나머지 메서드를 감춘다.
type onlyReader struct{ io.Reader }

func main() {
	fmt.Println("── 누가 WriterTo / ReaderFrom 인가 ──")
	for _, v := range []struct {
		name string
		x    any
	}{
		{"*strings.Reader", strings.NewReader("")},
		{"*bytes.Buffer", new(bytes.Buffer)},
		{"*os.File", os.Stdout},
		{"*bufio.Reader", bufio.NewReader(nil)},
		{"*bufio.Writer", bufio.NewWriter(nil)},
		{"onlyReader", onlyReader{strings.NewReader("")}},
		{"*counter", new(counter)},
	} {
		_, wt := v.x.(io.WriterTo)
		_, rf := v.x.(io.ReaderFrom)
		fmt.Printf("  %-16s WriterTo=%-5v ReaderFrom=%v\n", v.name, wt, rf)
	}

	src := strings.Repeat("y", 100*1024)
	fmt.Println("── io.Copy(counter, …) 에서 Write 가 불린 모양 ──")
	var a counter
	io.Copy(&a, strings.NewReader(src))
	fmt.Println("  strings.Reader 그대로      :", a.sizes)
	var b counter
	io.Copy(&b, onlyReader{strings.NewReader(src)})
	fmt.Println("  onlyReader 로 감쌈         :", b.sizes)
	var c counter
	io.CopyBuffer(&c, strings.NewReader(src), make([]byte, 1000))
	fmt.Println("  CopyBuffer(1000 바이트 버퍼):", c.sizes)
	var d counter
	io.CopyBuffer(&d, onlyReader{strings.NewReader(src)}, make([]byte, 40000))
	fmt.Println("  CopyBuffer(40000) + 감쌈   :", d.sizes)
}
```

- 표의 `WriterTo`/`ReaderFrom` 칸은? 아래 네 줄의 `Write` 크기 목록은 각각?

### 9. 파일 → 파일 복사의 시스템 호출 (경계)

```go
// t44fcopy.go
package main

import (
	"fmt"
	"io"
	"os"
	"strings"
)

// onlyWriter 는 io.Writer 만 남기고 나머지 메서드를 감춘다.
type onlyWriter struct{ io.Writer }

// 인자: file(dst 가 *os.File 그대로) · hidden(dst 를 onlyWriter 로 감쌈)
func main() {
	os.WriteFile("src.bin", []byte(strings.Repeat("z", 1<<20)), 0o644)
	src, _ := os.Open("src.bin")
	dst, _ := os.Create("dst.bin")
	var w io.Writer = dst
	if os.Args[1] == "hidden" {
		w = onlyWriter{dst}
	}
	fmt.Fprintln(os.Stderr, "COPY-BEGIN")
	n, err := io.Copy(w, src)
	fmt.Fprintln(os.Stderr, "COPY-END")
	fmt.Println(os.Args[1], "n =", n, "err =", err)
}
```

<!-- 빌드한 뒤 두 모드를 strace -f -e trace=read,write,copy_file_range,sendfile,splice 로 돌려, COPY-BEGIN 과 COPY-END 사이의 호출을 이름과 반환값으로 센다. -->

- 두 모드에서 `COPY-BEGIN`\~`COPY-END` 사이에 나온 시스템 호출은? 이 결과로 「`io.Copy` 는 zero-copy 라서 빠르다」고 적어도 되나?

### 10. 버퍼를 비워 주는 사람 (연결)

- [Python 28번](../../../python/syntax/28-context-managers-and-with/)의 `with open(...)` 은 블록을 나갈 때 무엇을 해 주나? Go 에서 같은 일을 하려면 **무엇을 몇 개** 불러야 하고, 그 에러는 각각 어디서 받나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

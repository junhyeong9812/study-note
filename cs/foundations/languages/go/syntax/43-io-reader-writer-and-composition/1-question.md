# go/syntax/43 — `io.Reader`/`Writer` 와 조합 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ **모든 문제에서 「이 동작은 `io` 문서의 계약인가, 한 구현의 선택인가」를 먼저 적어라.**
> 모든 실험은 `module ex` · `go 1.27` 이고 `go build -trimpath` 로 빌드해 돌렸다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 가짜 Reader 와 읽는 루프 (예측)

```go
// t43grid.go
package main

import (
	"bufio"
	"errors"
	"fmt"
	"io"
	"os"
	"strings"
)

var errBroken = errors.New("선이 끊겼다")

// step 은 Read 한 번이 돌려줄 것이다.
type step struct {
	data string
	err  error
}

// script 는 정해 둔 순서대로 Read 에 답하는 가짜 Reader 다.
type script struct {
	steps []step
	i     int
}

func (s *script) Read(p []byte) (int, error) {
	if s.i >= len(s.steps) {
		return 0, s.steps[len(s.steps)-1].err
	}
	st := s.steps[s.i]
	s.i++
	return copy(p, st.data), st.err
}

func readers() []struct {
	id   string
	have int
	r    io.Reader
} {
	one := []step{}
	for _, c := range "abcdef" {
		one = append(one, step{string(c), nil})
	}
	one = append(one, step{"", io.EOF})
	return []struct {
		id   string
		have int
		r    io.Reader
	}{
		{"r1 데이터와 EOF 를 한 번에", 6, &script{steps: []step{{"abcdef", io.EOF}}}},
		{"r2 (0, nil) 이 끼어 있다", 6, &script{steps: []step{{"", nil}, {"", nil}, {"abc", nil}, {"", nil}, {"def", nil}, {"", io.EOF}}}},
		{"r3 한 바이트씩", 6, &script{steps: one}},
		{"r4 데이터와 다른 에러를 한 번에", 3, &script{steps: []step{{"abc", errBroken}}}},
	}
}

// 루프 넷 + 표준 도우미 둘. 받은 바이트와 마지막에 본 에러를 돌려준다.
func loopErrFirst(r io.Reader) (string, error) {
	var sb strings.Builder
	buf := make([]byte, 8)
	for {
		n, err := r.Read(buf)
		if err != nil {
			if err == io.EOF {
				return sb.String(), nil
			}
			return sb.String(), err
		}
		sb.Write(buf[:n])
	}
}

func loopZeroEnds(r io.Reader) (string, error) {
	var sb strings.Builder
	buf := make([]byte, 8)
	for {
		n, _ := r.Read(buf)
		if n == 0 {
			return sb.String(), nil
		}
		sb.Write(buf[:n])
	}
}

func loopContract(r io.Reader) (string, error) {
	var sb strings.Builder
	buf := make([]byte, 8)
	for {
		n, err := r.Read(buf)
		sb.Write(buf[:n])
		if err == io.EOF {
			return sb.String(), nil
		}
		if err != nil {
			return sb.String(), err
		}
	}
}

func readAll(r io.Reader) (string, error) {
	b, err := io.ReadAll(r)
	return string(b), err
}

func scanBytes(r io.Reader) (string, error) {
	var sb strings.Builder
	sc := bufio.NewScanner(r)
	sc.Split(bufio.ScanBytes)
	for sc.Scan() {
		sb.Write(sc.Bytes())
	}
	return sb.String(), sc.Err()
}

func main() {
	loops := []struct {
		id string
		f  func(io.Reader) (string, error)
	}{
		{"L1 err 먼저 보고 break", loopErrFirst},
		{"L2 n == 0 이면 끝", loopZeroEnds},
		{"L3 n 먼저 쓰고 err 를 본다", loopContract},
		{"L4 io.ReadAll", readAll},
		{"L5 bufio.Scanner(ScanBytes)", scanBytes},
	}
	lost, all, swallowed, errCells := 0, 0, 0, 0
	for _, l := range loops {
		for _, rd := range readers() {
			got, err := l.f(rd.r)
			all++
			mark := ""
			if len(got) < rd.have {
				lost++
				mark = "바이트 모자람"
			}
			if strings.HasPrefix(rd.id, "r4") {
				errCells++
				if err == nil {
					swallowed++
					mark += "에러 없음"
				}
			}
			row := fmt.Sprintf("%s\t%s\t받은 %q (%d/%d)\terr=%v\t%s", l.id, rd.id, got, len(got), rd.have, err, mark)
			if strings.Count(row, "\t") != 4 {
				fmt.Fprintln(os.Stderr, "칸 수 어긋남:", row)
				os.Exit(1)
			}
			fmt.Println(row)
		}
	}
	fmt.Printf("바이트가 모자란 칸 %d / %d · r4 에서 에러가 사라진 칸 %d / %d\n", lost, all, swallowed, errCells)
}
```

<!-- go vet . 을 돌리고, 빌드해 실행한다. 프로그램은 칸마다 「읽는 쪽 · Reader · 받은 바이트 (받은 수/받을 수) · 마지막 err · 표시」를 탭으로 찍고, 끝에 두 수를 센다. -->

- 스무 칸 중 **받은 바이트가 모자란 칸**은 어느 것인가? 각각 몇 바이트를 받았나?
- 마지막 줄의 두 수는?

### 2. `r4` 열 — 에러는 어디로 (예측)

- 같은 프로그램에서 `r4`(데이터와 다른 에러를 한 번에)를 읽은 다섯 칸의 `err=` 는 각각? 바이트를 **다 받고도** 문제가 있는 칸은?

### 3. `io.Reader` 문서의 순서 규칙 (왜)

- `go doc io.Reader` 가 「n > 0 을 먼저 처리하라」고 적는 까닭을, 문서가 허용한 **끝을 알리는 두 방식**으로 설명하라.

### 4. `strings.Reader` 를 거듭 읽으면 (예측)

```go
// t43twin.go
package main

import (
	"fmt"
	"strings"
)

func main() {
	r := strings.NewReader("abcdef")
	buf := make([]byte, 4)
	for i := 1; i <= 4; i++ {
		n, err := r.Read(buf)
		fmt.Printf("read %d → n=%d err=%v %q\n", i, n, err, buf[:n])
	}
}
```

- 네 줄의 `n`·`err` 는? 1번의 `L1` 이 이 Reader 에서는 어떻게 되나?

### 5. Rust 의 `Ok(0)` (연결)

```rust
// t43read.rs
use std::io::Read;

fn main() {
    let mut r: &[u8] = b"abcdef";
    let mut buf = [0u8; 4];
    for i in 1..=4 {
        let res = r.read(&mut buf);
        match res {
            Ok(n) => println!("read {} → Ok({}) {:?}", i, n, std::str::from_utf8(&buf[..n]).unwrap()),
            Err(e) => println!("read {} → Err({})", i, e),
        }
    }
}
```

- 이 프로그램의 네 줄은? Rust 에서는 「0 이면 끝」 루프가 맞는데 Go 에서는 왜 1번의 어느 칸을 깨뜨리나?

### 6. `gzip` 사슬과 `Close` (예측)

```go
// t43chain.go
package main

import (
	"bytes"
	"compress/gzip"
	"fmt"
	"io"
	"strings"
)

// pack 은 문자열을 gzip 으로 눌러 bytes.Buffer 에 담는다. closeIt 이 거짓이면 Close 를 안 부른다.
func pack(s string, closeIt bool) *bytes.Buffer {
	var buf bytes.Buffer
	gz := gzip.NewWriter(&buf)
	n, err := io.Copy(gz, strings.NewReader(s))
	fmt.Printf("  io.Copy → n=%d err=%v · Close 전 buf.Len()=%d\n", n, err, buf.Len())
	if closeIt {
		fmt.Printf("  gz.Close() → %v · Close 후 buf.Len()=%d\n", gz.Close(), buf.Len())
	}
	return &buf
}

// unpack 은 그 반대 방향이다.
func unpack(buf *bytes.Buffer) {
	zr, err := gzip.NewReader(buf)
	if err != nil {
		fmt.Println("  gzip.NewReader →", err)
		return
	}
	got, err := io.ReadAll(zr)
	fmt.Printf("  io.ReadAll → %d 바이트 · err=%v\n", len(got), err)
}

func main() {
	s := strings.Repeat("가나다라 ", 200)
	fmt.Println("원문", len(s), "바이트")
	for _, c := range []bool{true, false} {
		fmt.Printf("[Close=%v]\n", c)
		unpack(pack(s, c))
	}
}
```

- `Close=true` 와 `Close=false` 각각에서 `Close 전 buf.Len()`·되읽은 바이트 수·`err` 는?

### 7. 한 바이트 덜 쓰는 Writer (예측)

```go
// t43short.go
package main

import (
	"bufio"
	"fmt"
	"io"
	"strings"
)

// shorty 는 늘 한 바이트 덜 쓰고 err 는 nil 을 돌려준다.
type shorty struct{ got strings.Builder }

func (s *shorty) Write(p []byte) (int, error) {
	if len(p) == 0 {
		return 0, nil
	}
	s.got.Write(p[:len(p)-1])
	return len(p) - 1, nil
}

func main() {
	var a shorty
	n, err := io.Copy(&a, strings.NewReader("hello"))
	fmt.Printf("io.Copy       n=%d err=%v 받은=%q\n", n, err, a.got.String())

	var b shorty
	w := bufio.NewWriter(&b)
	w.WriteString("hello")
	fmt.Printf("bufio Flush   err=%v 받은=%q\n", w.Flush(), b.got.String())

	var c shorty
	n2, err := fmt.Fprint(&c, "hello")
	fmt.Printf("fmt.Fprint    n=%d err=%v 받은=%q\n", n2, err, c.got.String())

	var d shorty
	n3, err := io.WriteString(&d, "hello")
	fmt.Printf("io.WriteString n=%d err=%v 받은=%q\n", n3, err, d.got.String())
}
```

- 네 줄 각각의 `n`·`err`·받은 글자는?

### 8. 짧은 쓰기는 누구 책임인가 (왜)

- 7번에서 알아챈 쪽과 못 알아챈 쪽이 갈렸다. `go doc io.Writer` 의 어느 문장 때문에 **1차 책임이 Writer 구현**에 있나?

### 9. 작은 인터페이스가 조합되는 이유 (연결)

- [20번 주제](../20-interface-declaration-and-implicit-implementation/) (6)절의 「한 메서드 `5/5` 대 네 메서드 `1/5`」는 무엇을 세었나? 6번의 사슬에서 `io.Copy` 가 **알아야 하는 것**은 무엇뿐인가?

### 10. `(0, nil)` 의 뜻 (경계)

- 문서상 `(0, nil)` 은 무엇을 뜻하고 무엇을 뜻하지 **않나**? 1번의 `r2` 에서 `io.ReadAll`·`bufio.Scanner` 는 어떻게 됐나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

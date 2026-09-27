# go/syntax/43 — `io.Reader`/`Writer` 와 조합 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [`io`](https://pkg.go.dev/io) 패키지 문서(`go doc io.Reader` · `go doc io.Writer`). **이 툴체인에서 직접 떴다.**\
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다. Rust 대비 한 블록은 `rustc 1.92.0` 이다.\
> **버전** — `io.Reader`·`io.Writer` 의 선언과 계약 문장은 이 판(1.27.1)의 `go doc` 에서 떴다. **이 문서가 쓰는 API 중 판을 가르는 것은 없다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체는 넷째 창이다** — 「**`Read` 계약 격자** — 가짜 Reader 넷 × 읽는 쪽 다섯에서 **받은 바이트 수와 마지막 에러**를 찍는 로그」.
마지막 줄 「**바이트가 모자란 칸 3 / 20 · r4 에서 에러가 사라진 칸 1 / 5**」((1)절). ★★★ **틀린 루프 둘이 서로 다른 Reader 에서 깨진다** — 한 Reader 로만 시험하면 **둘 다 통과한다.**
★★ 짝이 되는 창은 「**Writer 쪽 — 짧은 쓰기를 누가 알아채나**」다. `io.Copy`·`bufio` 는 `short write` 를 내는데 **`fmt.Fprint`·`io.WriteString` 은 `err=<nil>`** 이다((4)절).

★★★ **이 주제의 경계** — 「작은 인터페이스가 조합된다」의 **수**(한 메서드 `5/5` 대 네 메서드 `1/5`)와 `MultiReader`→`TeeReader`→`LimitReader` 사슬은 [20번 주제](../20-interface-declaration-and-implicit-implementation/) (6)절이 이미 쟀다 — 여기서는 되풀이하지 않고 **그 배관이 기대는 계약**을 잰다.
`implements` 없이 만족하는 것(암묵 구현)도 20번이 정본이다. **`os.File`·`bufio`·`io.Copy` 의 속**(버퍼링·`Flush`·`ReaderFrom`/`WriterTo`)은 [44번 주제](../44-os-bufio-and-io-copy/)다 — 여기서 `bufio` 는 **읽는 쪽 하나**로만 나온다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 이 주제에서 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | ★ **인터페이스 만족**(메서드 집합) — `script` 가 `Read` 하나로 `io.Reader` 가 된다. 그 밖의 **Read 의 뜻은 명세에 없다** |
| **표준 라이브러리 계약** | `go doc io.Reader`·`io.Writer` 가 적은 것 | ★★★ 「**n > 0 을 먼저 처리하고 err 를 본다**」 · 끝에서 `(n>0, EOF)` 도 `(n>0, nil)` 뒤 `(0, EOF)` 도 **둘 다 허용** · `(0, nil)` 은 **EOF 가 아니다** · Writer 는 **`n < len(p)` 면 에러 필수** |
| **구현** | 이 판의 표준 타입이 실제로 한 것 | `strings.Reader` 는 **`(2, nil)` 뒤에 `(0, EOF)`** 로 끝을 알렸다((2)절) — 허용된 두 방식 중 하나일 뿐이다 |

★★★ **선을 긋는다** — 「`Read` 가 `n>0` 과 `io.EOF` 를 **같이** 돌려줄 수 있다」는 **`io` 문서의 계약**이다. 「`strings.Reader` 는 같이 안 돌려준다」는 **한 구현의 선택**이다 — 뒤엣것에 맞춘 루프는 앞엣것에서 깨진다((1)절 `L1 × r1`).

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
```

```text
===== 명령: go doc io.Reader | sed -n "8,31p" =====
    Read reads up to len(p) bytes into p. It returns the number of bytes read (0
    <= n <= len(p)) and any error encountered. Even if Read returns n < len(p),
    it may use all of p as scratch space during the call. If some data is
    available but not len(p) bytes, Read conventionally returns what is
    available instead of waiting for more.

    When Read encounters an error or end-of-file condition after successfully
    reading n > 0 bytes, it returns the number of bytes read. It may return the
    (non-nil) error from the same call or return the error (and n == 0) from a
    subsequent call. An instance of this general case is that a Reader returning
    a non-zero number of bytes at the end of the input stream may return either
    err == EOF or err == nil. The next Read should return 0, EOF.

    Callers should always process the n > 0 bytes returned before considering
    the error err. Doing so correctly handles I/O errors that happen after
    reading some bytes and also both of the allowed EOF behaviors.

    If len(p) == 0, Read should always return n == 0. It may return a non-nil
    error if some error condition is known, such as EOF.

    Implementations of Read are discouraged from returning a zero byte count
    with a nil error, except when len(p) == 0. Callers should treat a return
    of 0 and nil as indicating that nothing happened; in particular it does not
    indicate EOF.
(exit 0)
```

- ★★★ **「Callers should always process the n > 0 bytes returned before considering the error err」** — 이 주제의 계약 한 문장이다.
- ★★★ 끝에서 허용된 **두 방식** — 「It may return the (non-nil) error **from the same call** or return the error (and n == 0) **from a subsequent call**」.
- ★★ 「**a return of 0 and nil … does not indicate EOF**」 — `(0, nil)` 은 「아무 일도 없었다」다.

```text
===== 명령: go doc io.Writer | sed -n "8,12p" =====
    Write writes len(p) bytes from p to the underlying data stream. It returns
    the number of bytes written from p (0 <= n <= len(p)) and any error
    encountered that caused the write to stop early. Write must return a non-nil
    error if it returns n < len(p). Write must not modify the slice data,
    even temporarily.
(exit 0)
```

- ★★★ **「Write must return a non-nil error if it returns n < len(p)」** — Writer 쪽 계약. (4)절이 이것을 **어긴 Writer** 를 만든다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ **격자의 받은 바이트·에러 · `3 / 20` · `1 / 5`** | 가짜 Reader 가 **정해 둔 순서**로만 답한다 |
| 안 흔들린다 | `gzip` 출력 길이(`10`·`56`) · `unexpected EOF` | 재대조 두 판에서 같았다 — 이 문서는 **왜 같은지**(헤더에 무엇이 들어가는지)를 **열어 보지 않았다** |
| 안 흔들린다 | `short write` · `n=4` | |

★ 정규화 규칙은 **기본 넷**만 썼다 — 이 문서에는 주소·시간이 찍히는 칸이 없다.

## 한눈에 — 쉽게 말하면

**`Read` 는 「택배 한 번 받기」다.** 상자(`p`)를 내밀면 기사가 **몇 개를 넣었는지(`n`)** 와 **쪽지(`err`)** 를 준다.
계약은 **「상자에 든 것부터 꺼내고, 쪽지는 그다음에 읽어라」** 다. 마지막 배송에서 기사는 **물건과 함께 「이게 끝입니다」 쪽지(`io.EOF`)를 줄 수도** 있고, **빈 상자에 쪽지만 따로** 줄 수도 있다.
쪽지부터 읽고 「끝이네」 하고 상자를 버리면 **마지막 물건을 잃는다.** 거꾸로 「빈 상자면 끝」이라 믿으면, 기사가 **잠깐 빈손으로 왔을 때**(`(0, nil)`) 배송을 끊어 버린다.

| 비유 | 실체 |
|---|---|
| 상자에 넣은 개수 | ★★★ **`n`** — 에러가 있어도 **먼저 쓴다** |
| 물건과 「끝」 쪽지를 같이 | ★★★ **`(n>0, io.EOF)`** — `r1`((1)절) |
| 빈 상자에 쪽지만 따로 | **`(n>0, nil)` 뒤 `(0, io.EOF)`** — `strings.Reader`((2)절) |
| 잠깐 빈손으로 옴 | ★★ **`(0, nil)`** — **EOF 가 아니다** · `r2` |
| 쪽지부터 읽고 상자를 버림 | ★★★ **`if err != nil { break }` 를 먼저** — `L1` |
| 빈 상자면 끝이라 믿음 | ★★★ **`if n == 0 { break }`** — `L2` · C `read(2)`·Rust `Ok(0)` 의 습관((2)절) |
| 「다 못 넣었습니다」를 말 안 하는 기사 | ★★ **`n < len(p)` 인데 `err == nil`** 인 Writer — 계약 위반((4)절) |

```text
   ★★★ 계약대로 읽는 루프 (L3) — n 을 먼저, err 를 나중에

   for {
       n, err := r.Read(buf)
       쓰기(buf[:n])            ◀── ① 에러가 있든 없든 받은 것부터
       if err == io.EOF { 끝 }   ◀── ② 정상 종료 — 이미 ① 에서 마지막 조각을 썼다
       if err != nil   { 실패 }  ◀── ③ 다른 에러 — 역시 ① 에서 쓴 뒤다
   }                             ◀── (0, nil) 이면 ① 이 0 바이트를 쓰고 다시 돈다
```

> **`io.Reader`** — `Read(p []byte) (n int, err error)` 하나짜리 인터페이스. 표준 라이브러리의 입력은 거의 전부 이것을 받는다.

> **`io.EOF`** — 「더 읽을 것이 없다」를 뜻하는 **센티넬 에러 값**. 실패가 아니라 **정상 종료 신호**다.

> **짧은 쓰기(short write)** — `Write` 가 `len(p)` 보다 적게 썼다는 것. 계약상 **반드시 에러가 같이 와야** 한다.

## 이 주제가 답하려는 질문

1. **`Read` 의 `n` 과 `err` 를 어떤 순서로 봐야 하나** — 틀린 순서는 **어떤 Reader 에서** 데이터를 잃나.
2. **EOF 를 알리는 방식이 둘인데 표준 타입은 어느 쪽인가** — 그리고 다른 언어의 「0 이면 끝」 습관은 Go 에서 무엇을 깨나.
3. **작은 인터페이스 둘을 이으면 무엇을 얻고, 계약을 어긴 쪽은 누가 알아채나** — 압축 사슬과 짧은 쓰기.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **`Read` 계약 격자 — Reader 4 × 읽는 쪽 5** | 어느 조합이 **바이트를 잃나 · 에러를 잃나** | ★ 본체 창 · 프로그램이 **탭 4개**를 세고 어긋나면 `exit 1` |
| ★★ **한 호출씩 찍은 `(n, err)`** | 표준 타입이 **끝을 어떻게 알리나** | (2)절 · Go 와 Rust 를 나란히 |
| ★★ **`buf.Len()` · `io.ReadAll` 의 에러** | 사슬 끝의 쓰기가 **다 흘러 나갔나** | (3)절 |
| ★★ **계약을 어긴 Writer** | 짧은 쓰기를 **누가 알아채나** | (4)절 |
| ★★ **제5의 상태 — 「기준만 다른 것」** | ★★★ `L2 × r4` 는 **바이트를 다 받았고(3/3) `err=<nil>`** — 겉으로는 완벽한 성공이다. **받은 양은 맞는데, 「끝났다」의 근거가 EOF 가 아니라 「0 바이트」였다** — 그래서 선이 끊긴 것(`선이 끊겼다`)이 **정상 종료로 둔갑했다** | (1)절 |
| **부적용 — 성능** | 이 문서는 읽기 속도를 **안 쟀고 주장하지 않는다** | — |
| **못 잰 것 — Java `InputStream.read` 의 `-1`** | 대비로 들 만하지만 **이 문서는 Java 를 돌리지 않았다** | 규칙 26 — 도구가 없어서가 아니라 범위 밖 |

### (1) ★★★ `Read` 계약 격자 — Reader 넷 × 읽는 쪽 다섯

**언제 쓰나** — `Read` 를 **직접 부르는 루프**를 쓸 때(대개는 `io.ReadAll`·`bufio`·`io.Copy` 가 대신 한다).

```text
===== 소스: t43grid.go =====
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
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && ./prog =====
vet exit=0
L1 err 먼저 보고 break	r1 데이터와 EOF 를 한 번에	받은 "" (0/6)	err=<nil>	바이트 모자람
L1 err 먼저 보고 break	r2 (0, nil) 이 끼어 있다	받은 "abcdef" (6/6)	err=<nil>	
L1 err 먼저 보고 break	r3 한 바이트씩	받은 "abcdef" (6/6)	err=<nil>	
L1 err 먼저 보고 break	r4 데이터와 다른 에러를 한 번에	받은 "" (0/3)	err=선이 끊겼다	바이트 모자람
L2 n == 0 이면 끝	r1 데이터와 EOF 를 한 번에	받은 "abcdef" (6/6)	err=<nil>	
L2 n == 0 이면 끝	r2 (0, nil) 이 끼어 있다	받은 "" (0/6)	err=<nil>	바이트 모자람
L2 n == 0 이면 끝	r3 한 바이트씩	받은 "abcdef" (6/6)	err=<nil>	
L2 n == 0 이면 끝	r4 데이터와 다른 에러를 한 번에	받은 "abc" (3/3)	err=<nil>	에러 없음
L3 n 먼저 쓰고 err 를 본다	r1 데이터와 EOF 를 한 번에	받은 "abcdef" (6/6)	err=<nil>	
L3 n 먼저 쓰고 err 를 본다	r2 (0, nil) 이 끼어 있다	받은 "abcdef" (6/6)	err=<nil>	
L3 n 먼저 쓰고 err 를 본다	r3 한 바이트씩	받은 "abcdef" (6/6)	err=<nil>	
L3 n 먼저 쓰고 err 를 본다	r4 데이터와 다른 에러를 한 번에	받은 "abc" (3/3)	err=선이 끊겼다	
L4 io.ReadAll	r1 데이터와 EOF 를 한 번에	받은 "abcdef" (6/6)	err=<nil>	
L4 io.ReadAll	r2 (0, nil) 이 끼어 있다	받은 "abcdef" (6/6)	err=<nil>	
L4 io.ReadAll	r3 한 바이트씩	받은 "abcdef" (6/6)	err=<nil>	
L4 io.ReadAll	r4 데이터와 다른 에러를 한 번에	받은 "abc" (3/3)	err=선이 끊겼다	
L5 bufio.Scanner(ScanBytes)	r1 데이터와 EOF 를 한 번에	받은 "abcdef" (6/6)	err=<nil>	
L5 bufio.Scanner(ScanBytes)	r2 (0, nil) 이 끼어 있다	받은 "abcdef" (6/6)	err=<nil>	
L5 bufio.Scanner(ScanBytes)	r3 한 바이트씩	받은 "abcdef" (6/6)	err=<nil>	
L5 bufio.Scanner(ScanBytes)	r4 데이터와 다른 에러를 한 번에	받은 "abc" (3/3)	err=선이 끊겼다	
바이트가 모자란 칸 3 / 20 · r4 에서 에러가 사라진 칸 1 / 5
(exit 0)
```

그림 해설 (한 단계씩):

- 가짜 Reader 넷 — `r1` **데이터와 `io.EOF` 를 한 호출에** · `r2` **`(0, nil)` 이 섞여 있다** · `r3` 한 바이트씩 · `r4` **데이터와 다른 에러를 한 호출에**(이것만 받을 것이 3 바이트).
- ★★★ **`L1`(err 먼저 보고 break)은 `r1`·`r4` 에서 전부 잃었다** — `받은 "" (0/6)` · `(0/3)`. 마지막(유일한) 조각이 **에러와 같이 왔는데** 에러를 보고 바로 나갔다.
  ★ **`r2`·`r3` 에서는 멀쩡하다** — `strings.Reader` 처럼 **끝을 따로 알리는** Reader 로만 시험하면 **이 버그는 안 보인다.**
- ★★★ **`L2`(n == 0 이면 끝)는 `r2` 에서 전부 잃었다** — 첫 호출이 `(0, nil)` 이라 **시작하자마자** 끝냈다. `(0, nil)` 은 **EOF 가 아니다**(문서).
  ★★★ **그리고 `L2 × r4` 는 바이트는 다 받고 `err=<nil>`** — 에러를 **안 봐서** 「선이 끊겼다」가 **사라졌다.** `r4 에서 에러가 사라진 칸 1 / 5` 가 이 칸이다.
- ★★★ **`L3`(n 먼저 쓰고 err 를 본다)·`io.ReadAll`·`bufio.Scanner` 는 20 칸 중 한 칸도 안 잃었다** — `r4` 에서는 3 바이트를 받고 **에러도 올렸다.** 표준 도우미는 **계약대로 짜여 있다.**
- ★★★ **마지막 줄 `3 / 20 · 1 / 5`** — 틀린 루프 **둘이 서로 다른 Reader 에서** 깨졌다. **어느 한 Reader 로만 시험하면 둘 중 하나는 통과한다.**

```text
   ★★★ 격자를 칸으로 — ✗ 바이트 모자람 · ⊘ 에러 사라짐 · ○ 정상

                  r1 (n,EOF)   r2 (0,nil) 섞임   r3 한 바이트씩   r4 (n,다른 err)
   L1 err 먼저        ✗              ○                 ○                ✗
   L2 n == 0 끝       ○              ✗                 ○                ⊘
   L3 n 먼저          ○              ○                 ○                ○
   L4 io.ReadAll      ○              ○                 ○                ○
   L5 Scanner         ○              ○                 ○                ○
```

비용 — 없다.

### (2) ★★ EOF 를 알리는 두 방식 — `strings.Reader` 와 Rust

```text
===== 소스: t43twin.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
read 1 → n=4 err=<nil> "abcd"
read 2 → n=2 err=<nil> "ef"
read 3 → n=0 err=EOF ""
read 4 → n=0 err=EOF ""
(exit 0)
```

```text
===== 소스: t43read.rs =====
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
===== 명령: rustc --edition 2021 t43read.rs 2>err.txt; echo "rustc exit=$?"; cat err.txt; ./t43read =====
rustc exit=0
read 1 → Ok(4) "abcd"
read 2 → Ok(2) "ef"
read 3 → Ok(0) ""
read 4 → Ok(0) ""
(exit 0)
```

- ★★ **`strings.Reader` 는 `(2, nil)` 다음에 `(0, EOF)`** — 문서가 허용한 두 방식 중 **「따로 알리기」** 쪽이다. `L1` 이 이 Reader 에서는 **통과하는 이유**다.
  ★ 그리고 **다 읽은 뒤에도 계속 `(0, EOF)`** — `read 4` 도 같다.
- ★★★ **Rust `Read::read` 는 `Ok(0)` 이 끝이다** — `read 3 → Ok(0)`. Rust 의 `Read` 는 에러와 개수를 **`Result` 하나에** 담으므로 **「데이터와 EOF 를 같이」가 표현될 수 없다.** 그래서 Rust 에서는 **`L2`(0 이면 끝)가 맞는 루프**다.
  ★★★ **같은 습관이 Go 에서는 `r2` 를 잃는다** — Go 는 `(0, nil)` 을 **허용**(권장은 안 함)하고 그것을 **EOF 로 읽지 말라**고 적는다. 두 언어가 「0」에 **다른 뜻**을 준다.
- ★ C 의 `read(2)` 도 0 을 파일 끝으로 쓴다 — 이 문서는 **C 를 돌리지 않았다.** C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **48번**(EOF 와 오류 구분)이 그 자리다.

비용 — 없다.

### (3) ★★ 조합 — 한 줄 배관과, 끝을 안 닫은 사슬

[20번 주제](../20-interface-declaration-and-implicit-implementation/) (6)절이 `MultiReader`→`TeeReader`→`LimitReader` 로 **Reader 쪽 사슬**을 쟀다. 여기는 **Writer 가 끼는 사슬** — `strings.Reader` → `io.Copy` → `gzip.Writer` → `bytes.Buffer`, 그리고 되돌리기:

```text
===== 소스: t43chain.go =====
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
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && ./prog =====
vet exit=0
원문 2600 바이트
[Close=true]
  io.Copy → n=2600 err=<nil> · Close 전 buf.Len()=10
  gz.Close() → <nil> · Close 후 buf.Len()=56
  io.ReadAll → 2600 바이트 · err=<nil>
[Close=false]
  io.Copy → n=2600 err=<nil> · Close 전 buf.Len()=10
  io.ReadAll → 0 바이트 · err=unexpected EOF
(exit 0)
```

그림 해설 (한 단계씩):

- ★★ **`io.Copy(gz, strings.NewReader(s))` 한 줄**이 **원문 2600 바이트를 전부 넘겼다**(`n=2600 err=<nil>`). `io.Copy` 는 **`io.Reader` 와 `io.Writer` 만** 안다 — 한쪽이 문자열이고 한쪽이 압축기라는 것을 **모른다.**
- ★★★ **그런데 `Close 전 buf.Len()=10`** — 2600 바이트를 받은 압축기가 **밑의 버퍼에는 10 바이트(헤더)만** 흘렸다. 나머지는 **압축기 안에 머물러 있다.**
- ★★★ **`Close=true` — `Close 후 buf.Len()=56` · 되읽기 `2600 바이트 · err=<nil>`.**
  **`Close=false` — 되읽기 `0 바이트 · err=unexpected EOF`.** **`io.Copy` 는 성공(`err=<nil>`)을 보고했는데 결과물이 깨졌다.**
- ★★★ **「Writer 를 이은 사슬은 `Close`(또는 `Flush`)까지가 쓰기」** 다 — [44번 주제](../44-os-bufio-and-io-copy/)가 `bufio.Writer` 와 파일로 같은 자리를 잰다.

```text
   ★★ 한 줄 배관 — 각 칸은 자기 이웃이 io.Reader/io.Writer 라는 것만 안다

   strings.Reader ──Read──▶ io.Copy ──Write──▶ gzip.Writer ──Write──▶ bytes.Buffer
                                                  │
                                                  └ 안에 머문 것은 Close 가 밀어낸다
                                                    (Close 없으면 buf 에 헤더 10 바이트뿐)
```

비용 — 압축 비용이 있다. **재지 않았다.**

### (4) ★★★ Writer 의 짧은 쓰기 계약 — 누가 알아채나

`shorty` 는 **늘 한 바이트 덜 쓰고 `err` 는 `nil`** 을 돌려준다 — **계약 위반**이다(머리말 `t43wdoc`):

```text
===== 소스: t43short.go =====
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
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && ./prog =====
vet exit=0
io.Copy       n=4 err=short write 받은="hell"
bufio Flush   err=short write 받은="hell"
fmt.Fprint    n=4 err=<nil> 받은="hell"
io.WriteString n=4 err=<nil> 받은="hell"
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`io.Copy` — `n=4 err=short write`** · **`bufio` 의 `Flush` — `err=short write`**. 둘은 `n < len(p)` 인데 `err == nil` 인 것을 보고 **`io.ErrShortWrite` 를 만들어** 올린다.
- ★★★ **`fmt.Fprint` — `n=4 err=<nil>`** · **`io.WriteString` — `n=4 err=<nil>`**. **Writer 가 준 것을 그대로 전달**했다 — `n` 이 4 인 것은 보이지만 **`err` 만 보는 호출자는 성공으로 읽는다.**
- ★★ **받은 것은 넷 다 `"hell"`** — 한 바이트가 사라졌다.
- ★★ 그래서 **짧은 쓰기의 1차 책임은 Writer 구현**이다 — 계약이 「에러 필수」라고 적은 이유다. `io.Copy`·`bufio` 가 잡아 주는 것은 **덤**이고, 모든 호출자가 잡아 주지 않는다.

비용 — 없다.

## 문법 — 형태와 규칙

### 형태

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

규칙 불릿.

- ★★★ **`n, err := r.Read(buf)` 다음 줄은 `buf[:n]` 을 쓰는 것** — 에러를 보기 **전에.**
- ★★★ **`err == io.EOF` 는 정상 종료.** 그 밖의 에러는 실패 — 둘 다 **받은 `n` 을 쓴 뒤에** 판정한다.
- ★★★ **`(0, nil)` 은 「아무 일 없음」** — 끝이 아니다. `n == 0` 을 종료 조건으로 쓰지 않는다.
- ★★ 직접 루프를 쓰기 전에 **`io.ReadAll`·`io.Copy`·`bufio.Scanner`** 를 먼저 본다 — 20 칸 중 한 칸도 안 잃었다.
- ★★★ Writer 를 구현하면 **`n < len(p)` 일 때 반드시 에러**를 돌려준다.
- ★★ Writer 사슬(`gzip`·`bufio`)은 **`Close`/`Flush` 까지** 해야 끝이다.

### 금지 사례 — 누가 잡나

| 쓴 꼴 | 누가 잡나 | 어디서 |
|---|---|---|
| `n, err := r.Read(b); if err != nil { break }` 뒤에 `b[:n]` 사용 | ★★★ **아무도 안 잡는다** — `(n, EOF)` 인 Reader 에서 **마지막 조각 유실** | (1)절 `L1` |
| `if n == 0 { break }` | ★★★ **아무도 안 잡는다** — `(0, nil)` 에서 조기 종료 · **에러 삼킴** | (1)절 `L2` |
| `n < len(p)` 에 `nil` 을 돌려주는 Writer | `io.Copy`·`bufio` 는 `short write` · ★ **`fmt.Fprint`·`io.WriteString` 은 못 잡는다** | (4)절 |
| `gzip.Writer` 를 안 닫음 | ★★ **쓰는 쪽은 아무도 안 잡는다** — 읽는 쪽에서 `unexpected EOF` | (3)절 |

## 어디서 틀리나

### 1. ★★★ 「에러부터 확인하는 게 Go 의 관례다」

- (1)절 `L1` — **`Read` 만은 예외**다. 문서가 「n > 0 을 먼저」라고 적는다. `r1`·`r4` 에서 **전부 잃었다.**

### 2. ★★★ 「0 바이트면 끝이다」

- (1)절 `L2 × r2` — `(0, nil)` 에서 **시작하자마자 끝났다.** Rust 의 `Ok(0)`·C 의 `read` 습관이다((2)절).

### 3. ★★★ 「`strings.Reader` 로 테스트했으니 루프가 맞다」

- (1)·(2)절 — `strings.Reader` 는 **끝을 따로 알려서** `L1` 이 통과한다. **데이터와 EOF 를 같이 주는 Reader** 로도 시험해야 한다.

### 4. ★★ 「`io.Copy` 가 `err=<nil>` 이면 결과물도 온전하다」

- (3)절 — **`gzip.Writer` 를 안 닫으면** `io.Copy` 는 성공인데 되읽기가 `unexpected EOF`.

### 5. ★★ 「`fmt.Fprint` 가 `err=<nil>` 이면 다 썼다」

- (4)절 — **짧은 쓰기를 전달만** 한다. 계약을 어긴 Writer 앞에서는 `n` 을 봐야 한다.

### 6. ★ 「바이트를 다 받았으니 성공이다」

- (1)절 `L2 × r4` — **3/3 을 받고 `err=<nil>`** 인데 실제로는 **선이 끊겼다.** 에러를 버린 루프는 **실패를 성공으로 바꾼다.**

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| `Read` 하나로 `io.Reader` 가 된다 | **명세**(인터페이스 만족) | (1)절 `script` · [20번 주제](../20-interface-declaration-and-implicit-implementation/) |
| ★★★ n > 0 을 먼저 처리 · EOF 두 방식 허용 · `(0, nil)` 은 EOF 아님 | **표준 라이브러리 계약**(`go doc io.Reader`) | `t43doc` |
| ★★★ `n < len(p)` 면 에러 필수 | **표준 라이브러리 계약**(`go doc io.Writer`) | `t43wdoc` |
| `strings.Reader` 는 끝을 따로 알린다 | **구현** — 계약이 허용한 한쪽 | (2)절 |
| `io.Copy`·`bufio` 는 `ErrShortWrite` 를 만든다 · `fmt.Fprint` 는 안 만든다 | **이 판의 구현**(문서 문장은 안 찾았다) | (4)절 |
| Rust `Ok(0)` = EOF | **Rust 표준 라이브러리** | (2)절 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 전부 읽어 메모리에 | **`io.ReadAll`** | 계약을 대신 지킨다((1)절) |
| 한 곳에서 다른 곳으로 흘리기 | **`io.Copy`** | 짧은 쓰기까지 잡는다((4)절) |
| 줄·단어 단위 | **`bufio.Scanner`** | ★ 줄 길이 한도가 있다 — [44번 주제](../44-os-bufio-and-io-copy/) |
| 직접 `Read` 루프 | ★★★ **`L3` 꼴** — `n` 먼저, `EOF` 는 정상 | (1)절 |
| 가공 단계를 끼우기 | Reader/Writer 를 **감싸는 타입**(`gzip`·`Tee`·`Limit`) | (3)절 · 20번 (6)절 |
| Writer 사슬을 끝낼 때 | ★★ **`Close`/`Flush` 의 에러까지 확인** | (3)절 |

## 핵심 문장

- ★★★ **`Read` 는 `n` 먼저, `err` 나중** — 문서가 그렇게 적었다. 에러를 먼저 본 루프는 **`(n, EOF)` 에서 마지막 조각을 잃는다**(`L1`).
- ★★★ **`(0, nil)` 은 EOF 가 아니다** — 「0 이면 끝」 루프는 **조기 종료하고 에러까지 삼킨다**(`L2`). Rust 의 `Ok(0)` 과 뜻이 다르다.
- ★★★ **`바이트가 모자란 칸 3 / 20 · 에러가 사라진 칸 1 / 5`** — 틀린 루프 둘이 **서로 다른 Reader 에서** 깨진다. `ReadAll`·`Scanner` 는 0 칸.
- ★★ **`strings.Reader` 는 끝을 따로 알린다** — 그것만으로 시험하면 `L1` 이 통과한다.
- ★★ **Writer 사슬은 `Close` 까지가 쓰기다** — 안 닫은 `gzip` 은 `io.Copy` 성공 뒤에도 `unexpected EOF`.
- ★★ **짧은 쓰기를 `io.Copy`·`bufio` 는 잡고 `fmt.Fprint`·`io.WriteString` 은 전달만 한다.**

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 43번)
- [20번 주제](../20-interface-declaration-and-implicit-implementation/)(인터페이스·암묵 구현) — ★ 목록상 선행 · **작은 인터페이스의 수(`5/5` 대 `1/5`)와 Reader 사슬의 정본**
- [44번 주제](../44-os-bufio-and-io-copy/)(`os`·`bufio`·`io.Copy`) — ★ 이 편의 다음 · 버퍼링·`Flush`·`Close`·`ReaderFrom`/`WriterTo`
- [23번 주제](../23-error-interface-and-errors-as-values/)(값으로서의 오류 — `io.EOF` 도 센티넬 값이다)
- C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **48번**(`fgets`/`fread` — EOF 와 오류 구분) · [Java 57번](../../../java/syntax/57-files-and-path/)(`Files`·`Path` — 이 문서는 Java 스트림을 돌리지 않았다)

## 용어 풀이

- **`io.Reader` / `io.Writer`** — `Read(p) (n, err)` / `Write(p) (n, err)` 하나짜리 인터페이스.
- **`io.EOF`** — 더 읽을 것이 없다는 센티넬 에러. 정상 종료 신호.
- **짧은 쓰기** — `Write` 가 `len(p)` 보다 적게 쓴 것. 계약상 에러가 같이 와야 한다. `io.ErrShortWrite` 가 그 값이다.
- **`io.ReadAll`** — EOF 까지 전부 읽어 `[]byte` 로. 성공이면 `err == nil`(EOF 가 아니다).
- **`bufio.Scanner`** — 토큰(줄·단어·바이트) 단위로 읽는 도우미. `Err()` 로 EOF 아닌 에러를 돌려준다.
- **감싸는 Reader/Writer** — 다른 Reader/Writer 를 받아 같은 인터페이스를 내는 타입(`gzip.NewWriter`·`io.TeeReader` 등).

---

## 더 들어가면

- ★ **`io.ReaderAt`·`io.Seeker`·`io.Pipe`** — 이 문서는 안 던졌다.
- ★ **끝없이 `(0, nil)` 만 주는 Reader** — `bufio` 에 「진전 없음」 에러(`io.ErrNoProgress`)가 있다는 것은 **이름만** 알고 **던지지 않았다.** `r2` 는 `(0, nil)` 이 **두세 번**만 섞인 Reader 다.
- ★ `gzip` 출력 길이(`56`)는 **이 입력의 한 판 관찰**이다 — 압축률 주장이 아니다.

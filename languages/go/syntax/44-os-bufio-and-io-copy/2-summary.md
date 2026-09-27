# go/syntax/44 — `os`·`bufio`·`io.Copy` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [`bufio`](https://pkg.go.dev/bufio) · [`os`](https://pkg.go.dev/os) · [`io`](https://pkg.go.dev/io) 패키지 문서(`go doc bufio.Writer` · `os.File.Close` · `io.Copy` · `io.CopyBuffer` · `bufio.MaxScanTokenSize`). **이 툴체인에서 직접 떴다.**\
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.
> 시스템 호출은 **`strace 6.8`** 로 셌고, C 대비는 **`gcc 13.3.0`** 이다(머리말 `tools`).\
> **버전** — 이 문서가 쓰는 API 중 판을 가르는 것은 없다. 시스템 호출 이름(`copy_file_range`)은 **이 머신의 커널·파일 시스템의 관찰**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체는 넷째 창이다** — 「**데이터가 사라지는 격자** — 쓰는 법 4(`bufio` 없이 · `Flush` · `Flush` 없음 · `defer w.Flush()`) × 끝내는 법 4(`return` · `os.Exit(0)` · `log.Fatal` · `panic`)로 100 바이트를 쓰고 **파일 크기**를 재는 로그」.
마지막 줄 「**사라진 칸 6 / 16**」((1)절). ★★★ **`defer w.Flush()` 는 `panic` 에서는 살고 `os.Exit`·`log.Fatal` 에서는 죽는다.**
★★ 짝이 되는 창은 「**`strace` 가 센 시스템 호출**」 — `fmt.Println` 세 번은 **`write` 세 번**, `bufio` 는 **한 번**, 파일 → 파일 `io.Copy` 는 **`read`/`write` 가 아니라 `copy_file_range`** 였다((3)·(5)절).

★★★ **이 주제의 경계** — **`defer w.Flush()` 가 `Flush` 의 에러를 버리는 것**(`/dev/full` 로 `dropped : <nil>`)과 **`os.Exit` 가 `defer` 를 안 돌리는 것**은 [26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/) (5)·(6)절이 이미 쟀다 — 여기서는 되풀이하지 않고 **그 둘이 만나면 파일에 몇 바이트가 남나**를 잰다.
`panic` 이 `defer` 를 돌리며 스택을 푸는 것은 [27번 주제](../27-panic-recover-and-where-to-use-them/)가 정본이다. `Read`·`Write` 의 계약과 **`gzip.Writer` 를 안 닫으면 깨지는 것**은 [43번 주제](../43-io-reader-writer-and-composition/)다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 이 주제에서 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | ★ **`defer` 는 함수가 반환할 때와 패닉으로 풀릴 때 돈다** — (1)절의 `defer × panic` 칸이 남는 근거 |
| **표준 라이브러리 계약** | `go doc` 이 적은 것 | ★★★ `bufio.Writer` — 「**should call the Writer.Flush method to guarantee all data has been forwarded**」 · `os.Exit` 는 `defer` 를 안 돌린다(26번) · `File.Close` 는 **두 번째 호출에서 에러** · `io.Copy` 는 **`WriterTo`/`ReaderFrom` 에 위임** · `CopyBuffer` 는 그때 **버퍼를 안 쓴다** · `MaxScanTokenSize = 64 * 1024` |
| **OS·구현** | 이 머신에서 찍힌 것 | ★★ `os.Stdout` 은 **버퍼가 없다**(`Println` 한 번 = `write` 한 번) · `/dev/full` 의 `Close` 는 `nil` · 파일 → 파일 복사가 `copy_file_range` |

★★★ **선을 긋는다** — 「`bufio` 는 `Flush` 해야 나간다」는 **문서의 계약**이다. 「`os.File` 에는 사용자 공간 버퍼가 없다」는 **이 판의 구현을 `strace` 로 본 것**이다. 「복사가 `copy_file_range` 로 간다」는 **커널·파일 시스템의 관찰**이고, **그것이 빠르다는 주장은 이 문서에 없다.**

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
```

```text
===== 명령: for t in strace gcc rustc cargo; do printf "%s → " $t; command -v $t >/dev/null && echo "있다" || echo "없다"; done; strace -V | sed -n 1p; gcc --version | sed -n 1p; rustc --version; cargo --version =====
strace → 있다
gcc → 있다
rustc → 있다
cargo → 있다
strace -- version 6.8
gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
rustc 1.92.0 (ded5c06cf 2025-12-08)
cargo 1.92.0 (344c4567c 2025-10-21)
(exit 0)
```

```text
===== 명령: go doc bufio.Writer | sed -n "6,10p"; go doc os.File.Close | sed -n "4,7p" =====
    Writer implements buffering for an io.Writer object. If an error occurs
    writing to a Writer, no more data will be accepted and all subsequent
    writes, and Writer.Flush, will return the error. After all data has been
    written, the client should call the Writer.Flush method to guarantee all
    data has been forwarded to the underlying io.Writer.
    Close closes the File, rendering it unusable for I/O. On files that support
    File.SetDeadline, any pending I/O operations will be canceled and return
    immediately with an ErrClosed error. Close will return an error if it has
    already been called.
(exit 0)
```

```text
===== 명령: go doc io.Copy | sed -n "12,14p"; go doc io.CopyBuffer | sed -n "9,10p" =====
    If src implements WriterTo, the copy is implemented by calling
    src.WriteTo(dst). Otherwise, if dst implements ReaderFrom, the copy is
    implemented by calling dst.ReadFrom(src).
    If either src implements WriterTo or dst implements ReaderFrom, buf will not
    be used to perform the copy.
(exit 0)
```

```text
===== 명령: go doc bufio.MaxScanTokenSize | sed -n "4,8p" =====
	// MaxScanTokenSize is the maximum size used to buffer a token
	// unless the user provides an explicit buffer with [Scanner.Buffer].
	// The actual maximum token size may be smaller as the buffer
	// may need to include, for instance, a newline.
	MaxScanTokenSize = 64 * 1024
(exit 0)
```

- ★★★ **「The actual maximum token size may be smaller as the buffer may need to include, for instance, a newline」** — (4)절의 `65535` 대 `65536` 이 이 문장이다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ **격자의 파일 크기·`exit` · `6 / 16`** | 버퍼에 남은 것은 **나가거나 안 나가거나** 둘뿐이다 |
| 안 흔들린다 | `write` 호출 수(`3`·`1`·`0`) · 받은 바이트 | 프로그램이 한 쓰기의 수 — 재대조 두 판에서 같았다 |
| **머신에 달린다** | ★★ **`copy_file_range` 2 번 · `read` 33 / `write` 32 번** | 커널·파일 시스템(`ext2/ext3` 로 보고됨)이 정한다 — 다른 머신·파일 시스템에서는 **다른 호출 이름**이 나올 수 있다 |
| 안 흔들린다 | `Close`·`Sync` 에러 문구 · `token too long` · `Write` 크기 목록 | |

★ 정규화 규칙은 **기본 넷**만 썼다. `strace` 가 찍는 PID 는 블록에 안 싣고 **줄 수만** 센다.

## 한눈에 — 쉽게 말하면

**`bufio.Writer` 는 「우체통」이다.** 편지를 넣으면(`WriteString`) **바로 배달되지 않고 통에 쌓인다.** 집배원이 오는 것은 **통이 차거나, 누가 수거 버튼(`Flush`)을 눌렀을 때**뿐이다.
퇴근 전에 버튼을 **안 누르면** 통 안의 편지는 **그대로 버려진다** — Go 에는 퇴근할 때 우체통을 대신 비워 주는 사람이 **없다**(C 의 `exit` 에는 있다 — (3)절).
「퇴근할 때 버튼 누르기」를 **메모(`defer w.Flush()`)** 로 붙여 두면 — **정상 퇴근(`return`)** 과 **소동 속 퇴근(`panic`)** 에서는 메모를 보지만, **건물 폭파(`os.Exit`·`log.Fatal`)** 에서는 **메모를 볼 틈이 없다.**

| 비유 | 실체 |
|---|---|
| 우체통에 쌓임 | ★★★ **`bufio.Writer` 의 버퍼**(이 판 기본 `Size=4096` — (2)절 `c2`) — 100 바이트는 통을 못 채운다 |
| 수거 버튼 | ★★★ **`w.Flush()`** — 안 누르면 `0 바이트`((1)절) |
| 우체통 없이 직접 전달 | **`f.Write`** — 끝내는 법과 무관하게 `100 바이트` |
| 퇴근 메모 | ★★ **`defer w.Flush()`** — `return`·`panic` 에서만 돈다 |
| 건물 폭파 | ★★★ **`os.Exit` · `log.Fatal`** — `defer` 를 안 본다 |
| 퇴근 때 대신 비워 주는 사람 | ★★ **C 의 `exit()`** — stdio 버퍼를 비운다 · `_exit()` 는 안 비운다((3)절) |
| 문 잠그기(`Close`) | ★★★ **`f.Close()` 는 우체통을 비우지 않는다** — `bufio` 를 건너뛰고 파일만 닫는다((2)절) |

```text
   ★★★ 데이터가 머무는 층 — 어디서 끊기면 무엇이 사라지나

   w.WriteString("x"*100)
        │
        ▼
   [ bufio.Writer 버퍼 ]  ◀── ★ Flush 가 없으면 여기서 끝 (프로세스와 함께 사라짐)
        │  Flush
        ▼
   [ *os.File ] ── write(2) ──▶ [ 커널 페이지 캐시 ] ── (나중에) ──▶ 디스크
        │                            ▲
        │  f.Close()                 │ 이 문서가 잰 「파일 크기」는 여기서 본 것이다
        └ 파일을 닫을 뿐 — bufio 는 모른다   (전원이 나가면 사라지는지는 안 쟀다 — Sync 의 몫)
```

> **`bufio.Writer`** — 다른 `io.Writer` 앞에 버퍼를 두는 감싸개. **`Flush` 를 불러야** 밑으로 나간다.

> **`os.Exit`** — 프로세스를 **곧바로** 끝낸다. `defer` 를 안 돌린다(26번). `log.Fatal` 은 출력 뒤 `os.Exit(1)` 이다.

> **시스템 호출(system call)** — 프로그램이 커널에 일을 맡기는 호출. `write(2)`·`read(2)`·`copy_file_range(2)` 등. `strace` 가 센다.

## 이 주제가 답하려는 질문

1. **`bufio` 에 쓴 데이터는 어떤 끝내기에서 사라지나** — `Flush`·`defer`·`os.Exit`·`panic` 의 조합.
2. **`Close` 는 무엇을 알려 주고 무엇을 안 알려 주나** — 쓰기 에러는 어디서 나오나.
3. **버퍼링은 언제 일어나고 누가 하나** — `os.Stdout` · `bufio.Scanner` 의 한도 · `io.Copy` 가 고르는 길.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **사라지는 격자 — 쓰는 법 4 × 끝내는 법 4 → 파일 크기** | 데이터가 **어디서 끊기나** | ★ 본체 창 · 스크립트가 **탭 3개**를 세고 두 수를 찍는다 |
| ★★★ **`strace` 의 `write` 수** | 버퍼링이 **실제로 일어났나** | (3)·(5)절 — 출력 바이트가 같아도 **호출 수**가 가른다 |
| ★★ **`Close`·`Sync`·`Write` 의 에러** | 실패가 **어디서 보고되나** | (2)절 · `/dev/full` |
| ★★ **`Write` 크기 목록** | `io.Copy` 가 **어느 길**로 갔나 | (5)절 |
| ★★ **제5의 상태 — 「기준만 다른 것」** | ★★★ **`Close err=<nil>` 인데 파일 크기 `0`** — `Close` 는 **파일을** 닫는 데 성공했다. 그런데 사용자가 묻고 싶었던 것은 **「내가 쓴 데이터가 나갔나」** 다. **같은 「성공」이 다른 층을 가리킨다** | (2)절 `c3` |
| **부적용 — 속도** | ★★★ **「`bufio` 가 빠르다」·「`io.Copy` 가 zero-copy」 는 이 문서에서 주장하지 않는다** — 호출 **수**와 **이름**만 셌다 | 규칙 4 |
| **못 잰 것 — `Close` 가 쓰기 에러를 돌려주는 경우** | NFS·디스크 할당량처럼 **닫을 때 지연된 쓰기 에러**가 오는 파일 시스템이 이 머신에 없다. `/dev/full` 은 **`Write` 에서 바로** 실패하고 `Close` 는 `nil` 이었다((2)절) | 규칙 3 — 「못 잰 이유 + 쪼갠 조각」 |
| **못 잰 것 — 전원 차단** | 페이지 캐시에서 디스크까지(`Sync`)는 **재지 않았다** | — |

### (1) ★★★ 사라지는 격자 — 쓰는 법 4 × 끝내는 법 4

**언제 쓰나** — `bufio.NewWriter(f)` 로 파일·표준 출력에 쓸 때, 그리고 **프로그램이 어떻게 끝날지** 정할 때.

```text
===== 소스: t44exit.go =====
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
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . || exit 1; lost=0; m=0; : > rows.tsv; for how in direct flush noflush defer; do for end in return exit fatal panic; do rm -f out.bin; ./prog $how $end >/dev/null 2>err.txt; rc=$?; sz=$(stat -c %s out.bin); m=$((m+1)); [ "$sz" -lt 100 ] && lost=$((lost+1)); printf "%s\t%s\texit=%d\t%s 바이트\n" $how $end $rc $sz >> rows.tsv; done; done; awk -F"\t" "NF!=4{bad=1} END{exit bad}" rows.tsv || echo "칸 수 어긋남"; cat rows.tsv; echo "사라진 칸 $lost / $m" =====
vet exit=0
direct	return	exit=0	100 바이트
direct	exit	exit=0	100 바이트
direct	fatal	exit=1	100 바이트
direct	panic	exit=2	100 바이트
flush	return	exit=0	100 바이트
flush	exit	exit=0	100 바이트
flush	fatal	exit=1	100 바이트
flush	panic	exit=2	100 바이트
noflush	return	exit=0	0 바이트
noflush	exit	exit=0	0 바이트
noflush	fatal	exit=1	0 바이트
noflush	panic	exit=2	0 바이트
defer	return	exit=0	100 바이트
defer	exit	exit=0	0 바이트
defer	fatal	exit=1	0 바이트
defer	panic	exit=2	100 바이트
사라진 칸 6 / 16
(exit 0)
```

그림 해설 (한 단계씩):

- ★★ **`direct`(`bufio` 없이 `f.WriteString`)는 네 칸 다 `100 바이트`** — `os.File` 의 쓰기는 **곧바로 `write(2)`** 라 끝내는 법이 무엇이든 이미 나갔다.
- ★★ **`flush`(다 쓰고 `w.Flush()`)도 네 칸 다 `100`** — 끝내기 **전에** 비웠다.
- ★★★ **`noflush` 는 네 칸 다 `0 바이트`** — **`return` 으로 곱게 끝나도 0** 이다. Go 에는 **프로그램이 끝날 때 `bufio` 를 비워 주는 장치가 없다.**
- ★★★ **`defer` 는 갈렸다** — **`return`·`panic` 은 `100`**, **`os.Exit`·`log.Fatal` 은 `0`**.
  `panic` 은 스택을 풀며 **`defer` 를 돌리고**(27번) 그다음에 죽는다(`exit=2`). `os.Exit` 는 **`defer` 를 안 돌린다**(26번 (6)절) — `log.Fatal` 도 속에서 `os.Exit(1)` 이다(`exit=1`).
- ★★★ **마지막 줄 `사라진 칸 6 / 16`** — `noflush` 넷 + `defer × {exit, fatal}` 둘.

```text
   ★★★ 격자를 칸으로 — 파일에 남은 바이트

                         return     os.Exit(0)    log.Fatal    panic
   direct (f.Write)       100          100           100         100
   flush (다 쓰고 Flush)  100          100           100         100
   noflush                  0            0             0           0     ◀── return 이어도 0
   defer w.Flush()        100            0             0         100     ◀── defer 를 도나가 가른다
```

- ★★ **처방** — `main` 에서는 **`func main() { os.Exit(run()) }`** 꼴로 정리를 `run` 의 `defer` 에 두라는 것이 26번 (6)절의 결론이다. 이 격자는 그 이유를 **바이트로** 보인다.
- ★ **`defer w.Flush()` 가 살아남는 칸에서도 `Flush` 의 에러는 버려진다** — 26번 (5)절 `dropped : <nil>`.

비용 — 이 문서는 재지 않았다.

### (2) ★★★ `Close` 가 알려 주는 것 — 쓰기 에러는 어디서 나오나

```text
===== 소스: t44close.go =====
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
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && ./prog =====
vet exit=0
c1 /dev/full 에 f.Write → f.Sync → f.Close
   Write n=0 err=write /dev/full: no space left on device
   Sync  err=sync /dev/full: invalid argument
   Close err=<nil>
c2 /dev/full 에 bufio 로 쓰고 Flush 없이 f.Close
   WriteString n=5 err=<nil> · Buffered=5 · Size=4096
   Close err=<nil>
c3 보통 파일에 bufio 로 쓰고 Flush 없이 f.Close
   Close err=<nil> · 파일 크기=0
c4 f.Close 를 두 번
   첫 Close err=<nil>
   둘째 Close err=close c4.txt: file already closed
   닫힌 뒤 Write err=write c4.txt: file already closed
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`c1` — `/dev/full` 에 `f.Write` 는 그 자리에서 `no space left on device`** · `Sync` 는 `invalid argument` · ★★★ **`Close` 는 `<nil>`**.
  **쓰기 에러는 `Write` 에서 나왔고 `Close` 는 아무것도 안 말했다.** 「`defer f.Close()` 가 쓰기 에러를 삼킨다」를 재 보려 했는데, **이 머신에서는 삼킬 에러가 `Close` 에 오지 않았다.**
- ★★★ **`c2` — `/dev/full` 에 `bufio` 로 쓰고 `Flush` 없이 `Close`** — `WriteString n=5 err=<nil>`(버퍼에만 들어갔다) · `Buffered=5` · **`Close err=<nil>`**. **꽉 찬 장치에 썼는데 어디서도 에러가 안 났다** — 데이터가 **장치에 가 보지도 않았기** 때문이다.
- ★★★ **`c3` — 보통 파일도 같다** — `Close err=<nil> · 파일 크기=0`. **`f.Close()` 는 `bufio` 를 모른다.**
- ★★ **`c4` — 두 번 닫으면 `close c4.txt: file already closed`** · 닫힌 뒤 쓰면 `write c4.txt: file already closed`. 문서의 「Close will return an error if it has already been called」 그대로다. ★ 이 머신에서 **`Close` 가 에러를 낸 것은 이 칸뿐**이다.

```text
   ★★ 「쓰기 실패」가 보고되는 자리 — 이 머신의 관찰

   bufio 로 씀 ─ WriteString ─ 성공(버퍼)        ← 여기서는 절대 안 난다
                 Flush ─────── ★ 여기서 난다(26번 (5)절: write /dev/full: no space left on device)
   os.File 로 씀 ─ Write ───── ★ 여기서 난다(c1)
                 Close ─────── nil (c1·c2·c3) · 두 번째면 file already closed (c4)
```

- ★★★ **그래서 쓰기 경로의 정석은 「`Flush` 의 에러를 받고, `Close` 의 에러도 받는다」** 다 — `Close` 가 이 머신에서 조용했던 것은 **이 파일 시스템의 성질**이고 계약이 아니다. 26번 (5)절 `checked` 가 두 에러를 다 올리는 꼴이다.

비용 — 없다.

### (3) ★★ `os.Stdout` 은 버퍼가 없다 — 그리고 C 의 `exit` 는 비워 준다

```text
===== 소스: t44sys.go =====
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
===== 명령: go build -trimpath -o prog . || exit 1; for m in println bufio; do strace -f -e trace=write -o st.txt ./prog $m > out.txt; rc=$?; echo "[$m] exit=$rc · fd 1 로 간 write 호출 $(grep -c "write(1, " st.txt) 번 · 받은 $(wc -c < out.txt) 바이트"; done =====
[println] exit=0 · fd 1 로 간 write 호출 3 번 · 받은 18 바이트
[bufio] exit=0 · fd 1 로 간 write 호출 1 번 · 받은 18 바이트
(exit 0)
```

```text
===== 소스: t44stdio.c =====
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
===== 명령: gcc -O0 -o cprog t44stdio.c || exit 1; for m in exit _exit; do strace -f -e trace=write -o st.txt ./cprog $m > out.txt; rc=$?; echo "[$m] exit=$rc · fd 1 로 간 write 호출 $(grep -c "write(1, " st.txt) 번 · 받은 $(wc -c < out.txt) 바이트"; done =====
[exit] exit=0 · fd 1 로 간 write 호출 1 번 · 받은 18 바이트
[_exit] exit=0 · fd 1 로 간 write 호출 0 번 · 받은 0 바이트
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **Go `fmt.Println` 세 번 → `write` 세 번** · **`bufio` + `Flush` 한 번 → `write` 한 번**. 받은 바이트는 둘 다 `18`. `os.Stdout` 은 **`*os.File`** 이고 **사용자 공간 버퍼가 없다** — `Println` 은 **그 자리에서** 내보낸다.
  ★ **stdout 을 파일로 돌렸는데도 세 번**이다 — 버퍼링 방식이 **tty 인지 파일인지에 따라 바뀌지 않는다**(tty 는 이 캡처에서 **안 쟀다**).
- ★★★ **C `printf` 세 번 → 파일로 돌리면 `write` 한 번** — stdio 가 **모았다가** 한 번에 냈다. **`exit(0)` 은 `18 바이트`, `_exit(0)` 은 `0 바이트`** — `exit` 는 끝나기 전에 **stdio 버퍼를 비우고**, `_exit` 는 **안 비운다.**
- ★★★ **Go 의 `bufio` 는 C 의 `_exit` 쪽이다** — (1)절 `noflush` 가 `return` 에서도 0 이었다. **「끝날 때 누가 비워 주나」에서 두 언어가 정반대**다.
  ★ 그래서 Go 에서 「출력이 사라졌다」는 대개 **`bufio` 를 직접 만든 자리**다. `fmt.Println` 만 쓰는 프로그램에서는 **(1)절의 `direct` 줄처럼** 끝내는 법과 무관하게 남는다.
- ★ C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **47번**(stdio 버퍼링·출력 순서)이 C 쪽 정본 자리다(폴더 없음).

비용 — 호출 **수**만 셌다. **속도는 재지 않았다.**

### (4) ★★ `bufio.Scanner` 의 줄 한도 — 64 KiB

```text
===== 소스: t44scan.go =====
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
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && ./prog =====
vet exit=0
bufio.MaxScanTokenSize = 65536
  줄 길이  65535 · Buffer 키움=false → Scan 이 참이었던 횟수 2 · Err=<nil>
  줄 길이  65536 · Buffer 키움=false → Scan 이 참이었던 횟수 0 · Err=bufio.Scanner: token too long
  줄 길이  70000 · Buffer 키움=false → Scan 이 참이었던 횟수 0 · Err=bufio.Scanner: token too long
  줄 길이  70000 · Buffer 키움=true  → Scan 이 참이었던 횟수 2 · Err=<nil>
(exit 0)
```

- ★★★ **`65535` 는 통과, `65536` 부터 `bufio.Scanner: token too long`** — `MaxScanTokenSize` 가 65536 인데 **줄바꿈 한 바이트가 버퍼에 같이 들어가야** 해서 한 바이트 모자란다(머리말 문장).
- ★★★ **`Scan 이 참이었던 횟수 0`** — 긴 줄 **뒤의 `다음 줄` 까지 못 읽었다.** 한도에 걸리면 **그 자리에서 멈추고**, `for sc.Scan()` 루프는 **그냥 끝난다** — **`sc.Err()` 를 안 보면 파일이 짧은 줄 알고 넘어간다.**
- ★★ **`sc.Buffer(make([]byte, 0, 4096), 1<<20)`** 로 한도를 1 MiB 로 올리면 두 줄 다 읽었다.
- ★ [43번 주제](../43-io-reader-writer-and-composition/) (1)절에서 `Scanner` 는 `Read` 계약을 **20 칸 다** 지켰다 — 그 도우미에도 **이런 한도가 따로 있다.**

비용 — 한도만큼 메모리. **재지 않았다.**

### (5) ★★ `io.Copy` 가 고르는 길 — `WriterTo`·`ReaderFrom`

```text
===== 소스: t44copy.go =====
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
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && ./prog =====
vet exit=0
── 누가 WriterTo / ReaderFrom 인가 ──
  *strings.Reader  WriterTo=true  ReaderFrom=false
  *bytes.Buffer    WriterTo=true  ReaderFrom=true
  *os.File         WriterTo=true  ReaderFrom=true
  *bufio.Reader    WriterTo=true  ReaderFrom=false
  *bufio.Writer    WriterTo=false ReaderFrom=true
  onlyReader       WriterTo=false ReaderFrom=false
  *counter         WriterTo=false ReaderFrom=false
── io.Copy(counter, …) 에서 Write 가 불린 모양 ──
  strings.Reader 그대로      : [102400]
  onlyReader 로 감쌈         : [32768 32768 32768 4096]
  CopyBuffer(1000 바이트 버퍼): [102400]
  CopyBuffer(40000) + 감쌈   : [40000 40000 22400]
(exit 0)
```

그림 해설 (한 단계씩):

- ★★ **누가 무엇인가** — `*strings.Reader` 는 `WriterTo` · `*bytes.Buffer`·`*os.File` 은 **둘 다** · `*bufio.Writer` 는 `ReaderFrom` · **감싼 `onlyReader` 와 내 `*counter` 는 둘 다 아니다.**
- ★★★ **`strings.Reader` 그대로 → `Write` 한 번 `[102400]`** — `io.Copy` 가 `src.WriteTo(dst)` 에 **맡겼고** `strings.Reader` 가 **통째로** 썼다.
- ★★★ **`onlyReader` 로 감싸면 `[32768 32768 32768 4096]`** — 위임할 곳이 없어 `io.Copy` 가 **자기 버퍼(32 KiB)** 로 돌았다. **같은 102400 바이트**인데 `Write` 모양이 다르다.
- ★★★ **`CopyBuffer(…, 1000 바이트 버퍼)` 도 `[102400]`** — **준 버퍼를 안 썼다.** 문서 「If either src implements WriterTo or dst implements ReaderFrom, **buf will not be used**」. 버퍼 크기로 쓰기 단위를 맞추려 했다면 **조용히 무시된다.**
  감싼 뒤 `CopyBuffer(40000)` 을 주면 비로소 `[40000 40000 22400]`.

```text
===== 소스: t44fcopy.go =====
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
===== 명령: stat -f -c "파일 시스템 %T" .; go build -trimpath -o prog . || exit 1; for m in file hidden; do strace -f -e trace=read,write,copy_file_range,sendfile,splice -o st.txt ./prog $m 2>/dev/null; echo "[$m] COPY-BEGIN 과 COPY-END 사이의 시스템 호출:"; awk "/COPY-BEGIN/{on=1;next} /COPY-END/{on=0} on" st.txt | sed -E "s/^[0-9]+ +//; s/\\(.*\\) += /(…) = /" | sort | uniq -c; done =====
파일 시스템 ext2/ext3
file n = 1048576 err = <nil>
[file] COPY-BEGIN 과 COPY-END 사이의 시스템 호출:
      1 copy_file_range(…) = 0
      1 copy_file_range(…) = 1048576
hidden n = 1048576 err = <nil>
[hidden] COPY-BEGIN 과 COPY-END 사이의 시스템 호출:
      1 read(…) = 0
     32 read(…) = 32768
     32 write(…) = 32768
(exit 0)
```

- ★★★ **파일 → 파일 `io.Copy` — `COPY-BEGIN` 과 `COPY-END` 사이에 `copy_file_range` 두 번뿐** — 한 번에 `= 1048576`(1 MiB 전부), 다음 한 번이 `= 0`(끝). **`read`·`write` 는 0 번**이다(인자는 `(…)` 로 줄여 반환값만 센다).
  **`dst` 를 `onlyWriter` 로 감싸면 `read` 는 `= 32768` 32 번 + `= 0` 한 번, `write` 는 `= 32768` 32 번** — 32 KiB 씩 사용자 공간을 거쳤다.
- ★★★ **이것은 「복사가 어느 시스템 호출로 갔나」의 관찰이지 「빠르다」의 근거가 아니다** — 이 문서는 시간을 **안 쟀다.** `copy_file_range` 가 커널 안에서 무엇을 하는지(데이터를 옮기나, 블록을 공유하나)는 **파일 시스템에 달렸고** 이 문서는 **안 봤다.** 그래서 「zero-copy」라는 말을 **쓰지 않는다.**
- ★★ **감싸기 한 겹이 길을 바꾼다** — 로깅·계수용 래퍼를 끼우면 `WriterTo`/`ReaderFrom` 이 **가려져** 기본 루프로 떨어진다(`onlyReader`·`onlyWriter`).

비용 — 호출 수만 셌다.

## 문법 — 형태와 규칙

### 형태

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

규칙 불릿.

- ★★★ **`bufio.NewWriter` 를 만들었으면 `Flush` 를 부르고 그 에러를 받는다** — `f.Close()` 는 `bufio` 를 비우지 않는다.
- ★★★ **`defer w.Flush()` 는 `os.Exit`·`log.Fatal` 에서 안 돈다** — `main` 은 `os.Exit(run())` 꼴로.
- ★★ **쓰기 파일은 `Close` 의 에러도 받는다** — 이 머신에서 조용했던 것은 파일 시스템의 성질이다.
- ★★ **`os.Stdout`·`os.File` 에는 사용자 공간 버퍼가 없다** — 쓰기마다 `write(2)`.
- ★★ **`bufio.Scanner` 는 줄 한도 64 KiB** — 넘으면 `sc.Err()` 가 `token too long`. 긴 줄이 올 수 있으면 `sc.Buffer` 로 올린다.
- ★★ **`io.Copy`/`CopyBuffer` 는 `WriterTo`/`ReaderFrom` 에 위임한다** — 그때 준 버퍼는 안 쓴다. 래퍼가 그 메서드를 가린다.

### 금지 사례 — 누가 잡나

| 쓴 꼴 | 누가 잡나 | 어디서 |
|---|---|---|
| `bufio` 에 쓰고 `Flush` 없이 끝냄 | ★★★ **아무도 안 잡는다** — `return` 이어도 `0 바이트` | (1)절 |
| `defer w.Flush()` + `os.Exit`/`log.Fatal` | ★★★ **아무도 안 잡는다** | (1)절 |
| `f.Close()` 로 `bufio` 가 비워지길 기대 | ★★★ **`Close err=<nil>` · 크기 0** | (2)절 `c3` |
| `for sc.Scan() {}` 뒤 `sc.Err()` 를 안 봄 | ★★ **아무도 안 잡는다** — 64 KiB 넘는 줄에서 **조용히 끝남** | (4)절 |
| `CopyBuffer` 의 버퍼로 쓰기 단위를 정하려 함 | ★ **조용히 무시** | (5)절 |
| `f.Close()` 를 두 번 | `close …: file already closed` | (2)절 `c4` |

## 어디서 틀리나

### 1. ★★★ 「프로그램이 정상 종료하면 버퍼는 비워진다」

- (1)절 — **`noflush × return` 이 `0 바이트`.** C 의 `exit` 는 비우지만(3)절 Go 는 안 비운다.

### 2. ★★★ 「`defer w.Flush()` 를 걸었으니 안전하다」

- (1)절 — **`os.Exit`·`log.Fatal` 에서 `0`**. 그리고 살아남는 칸에서도 **에러는 버려진다**(26번 (5)절).

### 3. ★★★ 「`f.Close()` 가 에러 없이 끝났으니 다 썼다」

- (2)절 `c2`·`c3` — **`bufio` 에 남은 것은 `Close` 가 모른다.** `/dev/full` 에 썼는데도 `Close err=<nil>`.

### 4. ★★ 「`defer f.Close()` 가 쓰기 에러를 삼키는 게 가장 흔한 유실이다」

- (2)절 — **이 머신에서는 `Close` 에 에러가 오지 않았다.** 실측된 유실은 전부 **`Flush` 를 안 부르거나 그 에러를 버린 자리**였다. `Close` 의 지연 에러는 **못 잰 것**이다(NFS 등).

### 5. ★★ 「`fmt.Println` 도 버퍼링된다(C 의 `printf` 처럼)」

- (3)절 — **세 번 = `write` 세 번.** 파일로 돌려도 같았다.

### 6. ★★ 「`Scanner` 가 멈추면 에러로 알려 준다」

- (4)절 — **루프가 그냥 끝난다.** `sc.Err()` 를 **물어야** `token too long` 이 나온다.

### 7. ★ 「`io.Copy` 는 늘 32 KiB 버퍼로 돈다」

- (5)절 — **`WriterTo`/`ReaderFrom` 이 있으면 위임**한다(`[102400]` · `copy_file_range`). 래퍼가 그것을 가리면 32 KiB 로 떨어진다.

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| `defer` 는 반환·패닉에서 돈다 | **명세** | (1)절 `defer × panic` · [27번 주제](../27-panic-recover-and-where-to-use-them/) |
| ★★★ `bufio.Writer` 는 `Flush` 해야 나간다 | **표준 라이브러리 계약** | `t44wdoc` · (1)절 |
| `os.Exit` 는 `defer` 를 안 돌린다 | **표준 라이브러리 계약** | [26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/) (6)절 · (1)절 |
| `Close` 두 번째는 에러 | **표준 라이브러리 계약** | `t44wdoc` · (2)절 `c4` |
| `/dev/full` 의 `Close` 가 `nil` · `Sync` 가 `EINVAL` | **OS·장치의 관찰** | (2)절 |
| ★★ `os.File` 에 사용자 공간 버퍼 없음 | **구현**(`strace` 관찰) | (3)절 |
| C `exit` 는 stdio 를 비움 · `_exit` 는 안 비움 | **C 표준 라이브러리**(이 머신 `gcc 13` + glibc) | (3)절 |
| ★★ `io.Copy` 위임 · `CopyBuffer` 가 버퍼 무시 | **표준 라이브러리 계약** | `t44cdoc` · (5)절 |
| 파일 → 파일이 `copy_file_range` | **구현 + 커널·파일 시스템의 관찰** | (5)절 |
| 64 KiB 줄 한도 | **표준 라이브러리 계약**(`MaxScanTokenSize`) | `t44sdoc` · (4)절 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 작은 쓰기를 **많이** 한다(줄 단위 로그 등) | **`bufio.Writer` + `Flush` 의 에러 확인** | 호출 수가 준다(3)절 — ★ 속도는 이 문서가 안 쟀다 |
| 한 번에 큰 덩어리 | `os.File` 에 직접 | 버퍼가 끼어도 줄일 호출이 적다고 **추론**한다 — ★ 이 문서는 재지 않았다 |
| `main` 에서 종료 코드 | ★★★ **`os.Exit(run())`** | `run` 의 `defer` 가 `Flush`·`Close` 를 한다((1)절) |
| 줄 단위로 읽기 | `bufio.Scanner` + ★ **`sc.Err()`** · 긴 줄이면 `sc.Buffer` | (4)절 |
| 한 곳에서 다른 곳으로 | **`io.Copy`** — 래퍼를 끼우면 길이 바뀐다는 것을 알고 | (5)절 |
| 전원 차단에도 남아야 한다 | `f.Sync()` — ★ 이 문서는 **효과를 재지 않았다** | 못 잰 것 |

## 핵심 문장

- ★★★ **`bufio` 에 쓴 것은 `Flush` 해야 나간다 — `return` 으로 끝나도 `0 바이트`.** 사라진 칸 `6 / 16`.
- ★★★ **`defer w.Flush()` 는 `return`·`panic` 에서는 돌고 `os.Exit`·`log.Fatal` 에서는 안 돈다.**
- ★★★ **`f.Close()` 는 `bufio` 를 비우지 않는다** — `Close err=<nil>` 인데 크기 0. `/dev/full` 에서도 `Close` 는 `nil` 이었다 — 쓰기 에러는 `Write`/`Flush` 에서 나왔다.
- ★★ **`os.Stdout` 은 버퍼가 없다**(`Println` 세 번 = `write` 세 번). **C 의 `exit` 는 stdio 를 비우고 Go 는 `bufio` 를 안 비운다.**
- ★★ **`Scanner` 는 64 KiB 줄에서 조용히 멈춘다** — `sc.Err()` 를 물어야 `token too long`.
- ★★ **`io.Copy` 는 `WriterTo`/`ReaderFrom` 에 위임한다** — 파일 → 파일은 `copy_file_range`, 래퍼 한 겹이면 32 KiB `read`/`write`. **속도 주장은 없다.**

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 44번)
- [43번 주제](../43-io-reader-writer-and-composition/)(`io.Reader`/`Writer`) — ★ 목록상 선행 · `Read`·`Write` 계약 · `gzip` 을 안 닫으면 `unexpected EOF`
- [26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/) — ★★ **`defer w.Flush()` 의 에러 유실(`/dev/full`)·`os.Exit` 와 `defer` 의 정본** · [27번 주제](../27-panic-recover-and-where-to-use-them/)(패닉이 `defer` 를 돌린다)
- [Python 48번](../../../python/syntax/48-pathlib-and-file-io/)(파일 I/O·인코딩·줄바꿈) · [Python 28번](../../../python/syntax/28-context-managers-and-with/)(`with open` — 닫는 것의 정본) — 이 문서는 파이썬의 버퍼 비우기를 **돌리지 않았다**
- C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **47번**(stdio 버퍼링) · **48번**(입력과 파일)

## 용어 풀이

- **`bufio.Writer`** — 쓰기 앞에 버퍼를 두는 감싸개. 이 판 기본 크기 4096 바이트((2)절 `Size=4096`). `Flush` 로 비운다.
- **`Flush`** — 버퍼의 내용을 밑의 Writer 로 내보낸다. 에러를 돌려준다.
- **`os.Exit` / `log.Fatal`** — 곧바로 종료 / 출력 뒤 `os.Exit(1)`. 둘 다 `defer` 를 안 돌린다.
- **`/dev/full`** — 쓰기마다 `ENOSPC`(공간 없음)를 돌려주는 리눅스 장치.
- **`strace`** — 프로세스의 시스템 호출을 기록하는 리눅스 도구.
- **`exit` / `_exit`(C)** — stdio 를 비우고 끝냄 / 안 비우고 곧바로 끝냄.
- **`bufio.Scanner`** — 줄·단어 단위 읽기. `MaxScanTokenSize`(64 KiB)가 기본 한도.
- **`io.WriterTo` / `io.ReaderFrom`** — 「내가 직접 써 주겠다」 / 「내가 직접 읽어 오겠다」는 메서드. `io.Copy` 가 먼저 찾는다.
- **`copy_file_range(2)`** — 두 파일 디스크립터 사이의 복사를 커널에 맡기는 리눅스 시스템 호출.

---

## 더 들어가면

- ★ **`Close` 의 지연 쓰기 에러**(NFS·할당량) — 이 머신에 그런 파일 시스템이 없어 **못 쟀다.**
- ★ **tty 로 돌렸을 때의 C stdio**(줄 버퍼) — 캡처가 파일로 받으므로 **안 쟀다.**
- ★ **`sendfile`·`splice`**(소켓·파이프로 복사할 때) — `strace` 목록에 넣었지만 파일 → 파일에서는 **안 나왔다.** 다른 조합은 안 던졌다.
- ★ Python 의 `print`·`open` 버퍼와 `os._exit` — **안 던졌다.**

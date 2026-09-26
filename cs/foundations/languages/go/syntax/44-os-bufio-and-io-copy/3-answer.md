# go/syntax/44 — `os`·`bufio`·`io.Copy` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다(6번만 `gcc 13.3.0`). 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★ **근거로 읽을 칸** — 파일 크기와 `exit` · `6 / 16` · 에러 문구 · `write` 호출 수 · `Write` 크기 목록 · `token too long`.
> **머신에 달린 칸** — 9번의 시스템 호출 이름과 수(커널·파일 시스템).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `direct`·`flush` 는 전부 `100` · **`noflush` 는 전부 `0`** · `defer` 는 `return`·`panic` 만 `100` — `사라진 칸 6 / 16`

**출력**

```text
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

**왜 그런가**

- ★★★ `bufio.Writer` 는 **`Flush` 를 불러야** 밑의 파일로 보낸다(`go doc bufio.Writer`). 100 바이트는 버퍼(4096)를 못 채워 **저절로는 안 나간다** — 그래서 **`noflush × return` 도 `0`**.
- ★★ `direct` 는 `os.File` 에 바로 써서 **이미 커널에 가 있다** — 끝내는 법과 무관하다.

### 2. `panic` 은 스택을 풀며 `defer` 를 **돌리고**(명세), `os.Exit` 는 `defer` 를 **안 돌린다**(`os` 패키지의 계약)

- ★★★ 명세의 `defer` 는 「함수가 **반환할 때**」와 「**패닉으로 풀릴 때**」 돈다 — 27번. 그래서 `defer × panic` 은 `Flush` 가 돌아 `100`(그리고 `exit=2`).
- ★★★ `os.Exit` 는 **반환하지 않는다** — 26번 (6)절의 `go doc os.Exit` 「deferred functions are not run」. `log.Fatal` 은 「Print followed by a call to os.Exit(1)」이라 같다. 이것은 **명세가 아니라 `os` 의 계약**이다.

### 3. `c1` — `Write` 가 `no space left on device`, `Sync` 가 `invalid argument`, `Close` 는 `<nil>` · `c2`·`c3` — 전부 `<nil>`(크기 0) · `c4` — **둘째 `Close` 와 그 뒤 `Write` 만** `file already closed`

**출력**

```text
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

- ★★★ **`Close` 가 에러를 돌려준 줄은 `c4` 의 둘째 `Close` 하나뿐**이다. `/dev/full` 에서도 `Close` 는 `nil` 이었다.
- ★★★ `c2`·`c3` — `bufio` 에 남은 것은 **`f.Close()` 가 모른다**(`Buffered=5` 인 채로 닫았다). **꽉 찬 장치에 썼는데 어디서도 에러가 안 났다.**

### 4. 이 머신에서는 **`Write`(직접)·`Flush`(bufio)** 에서 보고됐다 — 26번의 `dropped` 는 **`defer w.Flush()` 가 `Flush` 의 에러를 버린 것** · `Close` 는 파일 시스템에 따라 **지연된 쓰기 에러를 돌려줄 수 있어서**

- ★★★ 3번 `c1` — 에러는 **쓰는 그 자리**에서 왔다. 26번 (5)절 `dropped` 는 `defer f.Close()` 가 아니라 **`defer w.Flush()`** 의 반환값이 버려진 자리다(`checked` 만 `write /dev/full: no space left on device` 를 올렸다).
- ★★ 그래도 `Close` 의 에러를 받는 이유 — `Close` 가 에러를 **돌려줄 수 있다**는 것이 시그니처(`Close() error`)이고, **닫을 때 쓰기 실패를 알리는 파일 시스템**(NFS 등)이 있다고 알려져 있다. ★ **이 문서는 그런 파일 시스템에서 재지 못했다**(못 잰 것).

### 5. `println` — `write` 3 번 · 18 바이트 / `bufio` — `write` 1 번 · 18 바이트

**출력**

```text
===== 명령: go build -trimpath -o prog . || exit 1; for m in println bufio; do strace -f -e trace=write -o st.txt ./prog $m > out.txt; rc=$?; echo "[$m] exit=$rc · fd 1 로 간 write 호출 $(grep -c "write(1, " st.txt) 번 · 받은 $(wc -c < out.txt) 바이트"; done =====
[println] exit=0 · fd 1 로 간 write 호출 3 번 · 받은 18 바이트
[bufio] exit=0 · fd 1 로 간 write 호출 1 번 · 받은 18 바이트
(exit 0)
```

- ★★★ `os.Stdout` 은 `*os.File` — **사용자 공간 버퍼가 없다.** `Println` 한 번이 `write(2)` 한 번이다. stdout 을 **파일로** 돌렸는데도 그렇다.
- ★★ `bufio` 는 세 줄을 모았다가 `Flush` 에서 **한 번에** 냈다. ★ 호출 수만 셌다 — **빠르다는 주장은 아니다.**

### 6. `exit` — `write` 1 번 · 18 바이트 / `_exit` — `write` 0 번 · 0 바이트 · Go 의 `bufio` 는 **`_exit` 쪽**이다

**출력**

```text
===== 명령: gcc -O0 -o cprog t44stdio.c || exit 1; for m in exit _exit; do strace -f -e trace=write -o st.txt ./cprog $m > out.txt; rc=$?; echo "[$m] exit=$rc · fd 1 로 간 write 호출 $(grep -c "write(1, " st.txt) 번 · 받은 $(wc -c < out.txt) 바이트"; done =====
[exit] exit=0 · fd 1 로 간 write 호출 1 번 · 받은 18 바이트
[_exit] exit=0 · fd 1 로 간 write 호출 0 번 · 받은 0 바이트
(exit 0)
```

- ★★★ C 의 stdio 는 파일로 돌리면 **모았다가** 내고, **`exit()` 가 끝나기 전에 비워 준다.** `_exit()` 는 안 비운다.
- ★★★ Go 에는 **끝날 때 `bufio` 를 비워 주는 장치가 없다** — 1번 `noflush × return` 이 `0` 이었다. C 로 치면 **늘 `_exit` 로 끝나는 셈**이다(`bufio` 에 한해서).

### 7. `65535` — 2 번 · `<nil>` / `65536`·`70000` — **0 번** · `bufio.Scanner: token too long` / `Buffer` 키움 — 2 번 · `<nil>` — 긴 줄 뒤의 짧은 줄은 **못 읽었다**

**출력**

```text
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && ./prog =====
vet exit=0
bufio.MaxScanTokenSize = 65536
  줄 길이  65535 · Buffer 키움=false → Scan 이 참이었던 횟수 2 · Err=<nil>
  줄 길이  65536 · Buffer 키움=false → Scan 이 참이었던 횟수 0 · Err=bufio.Scanner: token too long
  줄 길이  70000 · Buffer 키움=false → Scan 이 참이었던 횟수 0 · Err=bufio.Scanner: token too long
  줄 길이  70000 · Buffer 키움=true  → Scan 이 참이었던 횟수 2 · Err=<nil>
(exit 0)
```

- ★★★ 버퍼에 **줄바꿈까지** 들어가야 해서 한도가 `65536 - 1` 이다(`go doc bufio.MaxScanTokenSize` — 「may need to include, for instance, a newline」).
- ★★★ 한도에 걸리면 **그 자리에서 멈추고 루프가 그냥 끝난다** — `sc.Err()` 를 물어야 안다. 뒤의 줄도 **같이 사라진다.**

### 8. `strings.Reader` `WriterTo` · `bytes.Buffer`·`os.File` 둘 다 · `bufio.Reader` `WriterTo` · `bufio.Writer` `ReaderFrom` · 감싼 것·`counter` 는 없음 — `[102400]` · `[32768 32768 32768 4096]` · `[102400]` · `[40000 40000 22400]`

**출력**

```text
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

- ★★★ `io.Copy` 는 **`src` 가 `WriterTo` 면 거기 맡긴다**(`go doc io.Copy`). `strings.Reader` 는 한 번에 썼다.
- ★★★ `CopyBuffer` 에 1000 바이트 버퍼를 줘도 **`[102400]`** — 「buf will not be used」. 감싸서 `WriterTo` 를 가려야 준 버퍼(40000)로 돈다.

### 9. `*os.File` 그대로면 `copy_file_range` 두 번(`= 1048576`·`= 0`) · 감싸면 `read` 33 · `write` 32 — **「빠르다」는 적을 수 없다**

**출력**

```text
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

- ★★★ 파일 → 파일에서 `io.Copy` 는 `*os.File` 의 `ReadFrom`/`WriteTo` 로 가 **`copy_file_range(2)`** 를 불렀다 — `read`/`write` 가 **0 번**이다. 감싸면 32 KiB 씩 `read`/`write`.
- ★★★ 이것은 **어느 시스템 호출로 갔나**의 관찰이다 — 시간은 **안 쟀고**, 커널이 그 호출 안에서 무엇을 하는지(블록 공유인지 복사인지)는 **파일 시스템에 달려 안 봤다.** 「zero-copy」·「빠르다」는 **이 문서의 근거로는 적을 수 없다.** 그리고 **다른 머신에서는 호출 이름부터 다를 수 있다**(머신에 달린 칸).

### 10. `__exit__` 가 **나가는 모든 길에서** 닫는다 — Go 는 **`Flush` 와 `Close` 두 개**를 부르고 에러를 **각각** 받아야 한다

- ★★ [Python 28번](../../../python/syntax/28-context-managers-and-with/) — `__exit__` 는 예외로 나가도 불린다(「몸통이 터져도 역순으로 닫힌다」). 파일 객체를 닫을 때 그 버퍼가 비워지는지는 **이 문서가 파이썬으로 돌리지 않았다.**
- ★★★ Go 는 `bufio.Writer` 와 `*os.File` 이 **다른 객체**다 — `w.Flush()` 의 에러(쓰기 실패가 여기서 온다)와 `f.Close()` 의 에러를 **둘 다** 받는다. `defer` 로 걸면 26번 (5)절 `checked` 꼴(비어 있을 때만 채우기)이 된다. `os.Exit` 로 끝내면 **어느 쪽도 안 돈다**(1번).

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 로 **★고칠 것 0** |
| ★★★ 사라지는 격자 (`t44exit`) | 쓰는 법 4 × 끝내는 법 4 · `stat` 파일 크기 · 탭 3개 검사 | 캡처마다 | **`6 / 16`** |
| ★★ `Close` (`t44close`) | `/dev/full` · 보통 파일 · 두 번 닫기 | 캡처마다 | `Close` 에러는 `c4` 만 |
| ★★ `write` 수 (`t44sys`·`t44stdio`) | `strace -f -e trace=write` | 캡처마다 | `3`·`1` / C `1`·`0` |
| ★★ 줄 한도 (`t44scan`) | 65535 · 65536 · 70000 · `Buffer` | 캡처마다 | `token too long` |
| ★★ `io.Copy` 의 길 (`t44copy`·`t44fcopy`) | `Write` 크기 목록 · `strace` 이름·반환값 | 캡처마다 | 위임 · `copy_file_range` |

**구현·환경에 달린 항목**

| 항목 | 무엇에 달렸나 |
|---|---|
| `Flush` 필요 · `os.Exit` 와 `defer` · `Close` 두 번 · `io.Copy` 위임 · 64 KiB | **표준 라이브러리 문서의 계약** |
| `defer` 가 패닉에서 돈다 | **명세** |
| `os.File` 에 버퍼 없음 | **이 판의 구현**(`strace` 관찰) |
| `/dev/full` 의 `Close`·`Sync` · `copy_file_range` | **이 머신의 커널·장치·파일 시스템**(`ext2/ext3` 로 보고됨) |
| C `exit`/`_exit` | **gcc 13 + 이 머신의 C 라이브러리** |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다(기본 규칙만). `strace` 가 있어야 한다(머리말 `tools`).

# go/syntax/43 — `io.Reader`/`Writer` 와 조합 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다(5번만 `rustc 1.92.0`). 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★ **근거로 읽을 칸** — 받은 바이트와 `err` · `3 / 20` · `1 / 5` · `(n, err)` 한 줄씩 · `buf.Len()` · `short write`. 이 문서에는 **흔들리는 칸이 없다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `L1 × r1`(0/6) · `L1 × r4`(0/3) · `L2 × r2`(0/6) — `3 / 20 · 1 / 5`

**출력**

```text
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

**왜 그런가**

- ★★★ `L1` 은 **에러를 먼저 보고 나가서**, 마지막 조각이 **에러와 같은 호출에** 온 `r1`·`r4` 에서 그 조각을 버렸다.
- ★★★ `L2` 는 **`(0, nil)` 을 끝으로 읽어서** `r2` 의 첫 호출에서 멈췄다.
- ★★ 두 버그는 **서로 다른 Reader 에서만** 드러난다 — `r3`(한 바이트씩)는 다섯 루프가 전부 통과했다.

### 2. `L1` 선이 끊겼다(0 바이트) · **`L2` 는 `<nil>`**(3/3 인데 에러 사라짐) · `L3`·`ReadAll`·`Scanner` 는 3 바이트 + `선이 끊겼다`

- 출력은 1번 블록의 `r4` 줄들이다.
- ★★★ **`L2 × r4` 가 가장 나쁘다** — 바이트 수가 맞고 `err=<nil>` 이라 **완벽한 성공으로 보인다.** 루프가 `err` 를 **아예 안 봐서** 연결 끊김이 정상 종료가 됐다.
- ★★ `L1 × r4` 는 에러는 올렸지만 **받은 3 바이트를 버렸다** — 「어디까지 받았나」를 모른다.

### 3. 끝을 **같은 호출**에서 알려도, **다음 호출**에서 알려도 되기 때문 — 먼저 `n` 을 쓰면 **두 방식 모두**에서 맞다

- ★★★ `go doc io.Reader` — 「It may return the (non-nil) error **from the same call** or return the error (and n == 0) **from a subsequent call**」. 같은 호출이면 `n>0` 과 `EOF` 가 **한 번에** 온다 — 에러를 먼저 보면 그 `n` 을 버린다.
- ★★ 같은 이유로 **EOF 가 아닌 에러**도 데이터와 같이 올 수 있다(`r4`) — 「Doing so correctly handles I/O errors that happen after reading some bytes」.

### 4. `(4,nil)` · `(2,nil)` · `(0,EOF)` · `(0,EOF)` — 끝을 **따로** 알리므로 `L1` 이 **통과한다**

**출력**

```text
===== 명령: go build -trimpath -o prog . && ./prog =====
read 1 → n=4 err=<nil> "abcd"
read 2 → n=2 err=<nil> "ef"
read 3 → n=0 err=EOF ""
read 4 → n=0 err=EOF ""
(exit 0)
```

- ★★ `strings.Reader` 는 허용된 두 방식 중 **「다음 호출에서」** 쪽이다. 그래서 이것으로만 시험하면 `L1` 의 버그가 **안 보인다.**

### 5. `Ok(4)` · `Ok(2)` · `Ok(0)` · `Ok(0)` — Rust 는 `Ok(0)` 이 끝이지만, Go 는 `(0, nil)` 을 **허용하고 EOF 로 읽지 말라**고 해서 `L2 × r2` 가 깨진다

**출력**

```text
===== 명령: rustc --edition 2021 t43read.rs 2>err.txt; echo "rustc exit=$?"; cat err.txt; ./t43read =====
rustc exit=0
read 1 → Ok(4) "abcd"
read 2 → Ok(2) "ef"
read 3 → Ok(0) ""
read 4 → Ok(0) ""
(exit 0)
```

- ★★★ Rust 의 `read` 는 개수와 에러를 **`Result` 하나**에 담는다 — **데이터와 EOF 를 동시에 줄 수 없고**, 끝은 `Ok(0)` 뿐이다. 그래서 「0 이면 끝」이 **그 언어에서는** 맞는 루프다.
- ★★ Go 의 계약은 `(0, nil)` 을 「아무 일도 없었다」로 둔다 — 같은 루프가 `r2` 에서 **시작하자마자** 끝났다.

### 6. `Close=true` — `10` → `56` · `2600 바이트` · `<nil>` / `Close=false` — `10` · **`0 바이트` · `unexpected EOF`**

**출력**

```text
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

- ★★★ `io.Copy` 는 **두 경우 모두 `n=2600 err=<nil>`** — 받은 쪽(`gzip.Writer`)이 **안에 쥐고 있었다.** 밑의 `bytes.Buffer` 에는 헤더 10 바이트뿐이다.
- ★★ **`Close` 가 남은 것을 밀어내고 끝 표시까지 써야** 읽는 쪽이 온전하게 받는다. [44번 주제](../44-os-bufio-and-io-copy/)의 `bufio.Writer`·`Flush` 와 같은 자리다.

### 7. `io.Copy` `n=4 short write` · `Flush` `short write` · **`fmt.Fprint` `n=4 <nil>`** · **`io.WriteString` `n=4 <nil>`** — 받은 것은 넷 다 `"hell"`

**출력**

```text
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && ./prog =====
vet exit=0
io.Copy       n=4 err=short write 받은="hell"
bufio Flush   err=short write 받은="hell"
fmt.Fprint    n=4 err=<nil> 받은="hell"
io.WriteString n=4 err=<nil> 받은="hell"
(exit 0)
```

- ★★★ `io.Copy`·`bufio` 는 **`n < len(p)` 인데 `err == nil`** 인 것을 보고 `io.ErrShortWrite` 를 만든다. `fmt.Fprint`·`io.WriteString` 은 **Writer 의 대답을 그대로** 돌려준다.

### 8. 「Write must return a non-nil error if it returns n < len(p)」 — 계약이 Writer 에게 에러를 **의무로** 지웠다

- ★★★ 호출자가 `n` 을 매번 `len(p)` 와 견주지 않아도 되도록 **Writer 가 에러로 말하라**는 것이 계약이다. 7번의 `shorty` 는 그것을 어겼고, 결과는 **호출자마다 달랐다.**
- ★ `io.Copy`·`bufio` 의 검사는 **덤**이다 — 모든 호출자가 해 주지 않는다(`fmt.Fprint`).

### 9. 같은 후보 다섯이 **한 메서드 인터페이스**는 전부, **네 메서드 인터페이스**는 하나(`*os.File`)만 만족했다 — `io.Copy` 가 아는 것은 **`Read` 와 `Write` 뿐**

- ★★ 20번 (6)절 — 요구가 늘자 만족하는 타입이 **5 에서 1 로** 줄었다. 그래서 작은 인터페이스는 **배관 부품이 된다.**
- ★★★ 6번의 사슬에서 `io.Copy` 는 **문자열·압축기·버퍼를 모른다** — `io.Reader` 하나와 `io.Writer` 하나만 안다. 그 대가로 **`Close` 가 필요하다는 것도 모른다**(6번).

### 10. 「아무 일도 없었다」 — **EOF 가 아니다** · `r2` 에서 `ReadAll`·`Scanner` 는 **6/6**

- ★★★ `go doc io.Reader` — 「Callers should treat a return of 0 and nil as indicating that nothing happened; in particular **it does not indicate EOF**」. 구현 쪽에도 「discouraged」(권장하지 않음)라 적는다 — **금지는 아니다.**
- ★★ 표준 도우미는 그 계약대로 **다시 읽었다** — 1번 블록의 `L4 × r2`·`L5 × r2` 가 `(6/6)`.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 로 **★고칠 것 0** |
| ★★★ `Read` 계약 격자 (`t43grid`) | 가짜 Reader 4 × 읽는 쪽 5 · 탭 4개 검사 | 캡처마다 | **`3 / 20` · `1 / 5`** |
| ★★ EOF 두 방식 (`t43twin`·`t43read`) | 호출마다 `(n, err)` · Rust 대비 | 캡처마다 | `(0, EOF)` · `Ok(0)` |
| ★★ 조합 (`t43chain`) | `gzip` 사슬 × `Close` | 캡처마다 | `unexpected EOF` |
| ★★ 짧은 쓰기 (`t43short`) | 계약을 어긴 Writer × 호출자 넷 | 캡처마다 | 둘은 잡고 둘은 못 잡음 |

**구현·환경에 달린 항목**

| 항목 | 무엇에 달렸나 |
|---|---|
| `Read`·`Write` 계약 | **`io` 문서의 계약**(이 판 `go doc`) |
| `strings.Reader` 가 끝을 알리는 방식 | **구현** — 계약이 허용한 한쪽 |
| `io.Copy`·`bufio` 의 `ErrShortWrite` · `fmt.Fprint` 의 전달 | **이 판의 구현** |
| Rust `Ok(0)` | **rustc 1.92.0 의 표준 라이브러리** |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다(기본 규칙만).

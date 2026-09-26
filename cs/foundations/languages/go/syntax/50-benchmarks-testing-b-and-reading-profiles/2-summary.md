# go/syntax/50 — 벤치마크·`testing.B`·프로파일 읽기 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [`testing`](https://pkg.go.dev/testing) 의 `B.Loop` · `B.ResetTimer` · `B.ReportAllocs` 문서 · `go help testflag`(`-benchmem`·`-count`·`-cpuprofile`). **이 툴체인에서 직접 떴다.**\
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.
> ★★ 판 격자에는 모듈 캐시의 **`go1.25.12`** 를 같이 썼다(명령에는 `"$GO125"` 로 찍힌다). 판 격자용 모듈은 `go 1.25` 줄이다(두 툴체인이 다 빌드하게).\
> **버전** — `B.Loop` 은 **1.24**(`api/go1.24.txt` — [49번 주제](../49-testing-table-driven-t-run-cleanup-and-parallel/) 「이 판」의 `tapi`) · ★★★ **그 구현이 1.25.12 와 1.27.1 사이에 바뀌었다** — 「인라인을 끈다」에서 「`runtime.KeepAlive` 로 감싼다」로((1)절 `t50ldoc`).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체는 넷째 창이다** — 「**기계어에 곱셈이 남았나** — 벤치 7(결과 버림 · 전역 싱크 · 입력을 `i` 로 · `b.Loop` + 상수 입력 · 루프 함수 버림 · 루프 함수 싱크 · `b.Loop` + 전역 입력) × 판 2(`go1.27.1` · `go1.25.12`)를 `go tool objdump` 로 센 것」.
마지막 두 줄 「**곱셈도 호출도 기계어에 안 남은 칸 7 / 14**」·「**두 판이 갈린 벤치 1 / 7**」((1)절). ★★★ **`b.Loop` + 상수 입력(`D4`)은 1.25.12 에서는 살아남고 1.27.1 에서는 접혀 사라진다** — `b.Loop` 이 지키는 것은 「계산」이 아니라 「값」이다.
★★ 짝이 되는 창은 「**`-benchmem` 의 `allocs/op`**」 — 벤치 7 × 판 2 에서 **두 판이 갈린 벤치 0 / 7**, 그리고 `ns/op` 는 **5판의 최소·중앙·최대**로만((3)절).

★★★ **이 주제의 경계** — `testing` 의 테스트 쪽(`t.Run`·`t.Cleanup`)은 [49번 주제](../49-testing-table-driven-t-run-cleanup-and-parallel/) · `-gcflags=-m` 탈출 분석 읽기의 정본은 [52번 주제](../52-tools-gofmt-vet-build-tags-embed-and-escape-analysis/) (5)절 · 슬라이스 재할당(2배 규칙)은 [06번 주제](../06-len-cap-and-append-reallocation/) · 문자열 불변성과 `strings.Builder` 는 [11번 주제](../11-strings-strconv-bytes-and-unicode-utf8/) 이다.
★ 여기는 「**벤치마크가 무엇을 잰 것인지**」와 「**어느 칸을 근거로 쓸 수 있나**」로 좁힌다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 이 주제에서 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | ★★ **없다** — 명세는 인라인·상수 접힘·죽은 코드 제거를 **말하지 않는다.** 결과를 안 쓰는 계산을 지워도 프로그램의 관찰 가능한 동작은 같다 |
| **표준 라이브러리 계약** | `go doc` 이 적은 것 | ★★★ **`b.Loop` 안의 호출 인자·결과는 「kept alive」** · `b.Loop` 은 **첫 호출에서 타이머를 리셋** · `ResetTimer` 는 **시간과 할당 계수**를 0 으로 |
| **구현·도구** | 이 판에서 찍힌 것 | ★★★ **무엇이 인라인되고 무엇이 접히나**(컴파일러) · ★★★ **`b.Loop` 의 구현 방식**(1.25.12 = 인라인 끔 · 1.27.1 = `KeepAlive`) · `ns/op` 값 전부 · `pprof` 의 퍼센트 |

★★★ **선을 긋는다** — 「결과를 버린 벤치는 지워질 수 있다」는 **명세가 막지 않는 최적화**의 결과다. 「`D1` 이 0.2 ns 다」는 **이 판·이 머신의 관찰**이다. 「`b.Loop` 은 결과를 살린다」는 **문서의 계약**이고, 「**그래도 상수 입력이면 계산이 컴파일 때 끝난다**」는 **1.27.1 의 관찰**이다((1)절 — 문서는 「kept alive」까지만 약속한다).

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
===== 명령: echo "── go1.27.1"; go doc testing.B.Loop | sed -n "20,25p"; echo "── go1.25.12"; "$GO125" doc testing.B.Loop | sed -n "20,26p"; echo "── go1.27.1 ResetTimer · ReportAllocs"; go doc testing.B.ResetTimer | sed -n "3,6p"; go doc testing.B.ReportAllocs | sed -n "3,6p" =====
── go1.27.1

    Within the body of a "for b.Loop() { ... }" loop, arguments to and results
    from function calls and assigned variables within the loop are kept alive,
    preventing the compiler from fully optimizing away the loop body. Currently,
    this is implemented as a compiler transformation that wraps such variables
    with a runtime.KeepAlive intrinsic call. This applies only to statements
── go1.25.12

    Within the body of a "for b.Loop() { ... }" loop, arguments to and results
    from function calls within the loop are kept alive, preventing the compiler
    from fully optimizing away the loop body. Currently, this is implemented by
    disabling inlining of functions called in a b.Loop loop. This applies only
    to calls syntactically between the curly braces of the loop, and the loop
    condition must be written exactly as "b.Loop()". Optimizations are performed
── go1.27.1 ResetTimer · ReportAllocs
func (b *B) ResetTimer()
    ResetTimer zeroes the elapsed benchmark time and memory allocation counters
    and deletes user-reported metrics. It does not affect whether the timer is
    running.
func (b *B) ReportAllocs()
    ReportAllocs enables malloc statistics for this benchmark. It is equivalent
    to setting -test.benchmem, but it only affects the benchmark function that
    calls ReportAllocs.
(exit 0)
```

- ★★★ **같은 문단이 두 판에서 다르다** — 1.25.12 「this is implemented by **disabling inlining of functions called in a b.Loop loop**」 · 1.27.1 「implemented as a compiler transformation that wraps such variables with a **runtime.KeepAlive intrinsic** call」. 두 판 모두 약속은 「kept alive, preventing the compiler from **fully** optimizing away the loop body」다.

```text
===== 명령: command -v benchstat; echo "command -v benchstat exit=$?"; echo "── \$HOME/go/bin"; ls "$HOME/go/bin" =====
command -v benchstat exit=1
── $HOME/go/bin
dlv
goplay
gopls
gotests
impl
(exit 0)
```

- ★★★ **`benchstat` 이 없다**(`command -v` 가 exit 1 · `$HOME/go/bin` 에도 없다 · 이 배치는 외부 네트워크를 안 쓴다) — **못 잰 것**이다. ★ 그래서 **창을 바꿨다**(제5의 상태): 같은 질문(「두 벤치가 정말 다른가」)을 **`-count=5` 의 최소·중앙·최대와 「흩어짐이 겹치나」** 로 물었다((3)절). ★ 바꾼 창이 못 보는 것 — **유의 확률**(p 값)이 없다. 「안 겹친다」는 5판의 관찰일 뿐이다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | ★★★ **`ns/op` 의 모든 수** — 최소·중앙·최대 | 기본 정규화 규칙(`<time>ns`)이 잡는다 — 규칙 24 |
| **흔들릴 수 있다 — 여유를 두고 골랐다** | ★★ 「2 ns 미만인 판 k / 5」 · 「흩어짐이 겹친다/안 겹친다」 | 경계에서 먼 값만 물었다(지워진 벤치는 1 ns 아래, 남은 벤치는 3 ns 위) — 재대조에서 같았다 |
| 안 흔들린다 | ★★★ **`IMUL` 수 · `mix`·`sum` 호출 수 · `7 / 14` · `1 / 7`** | 기계어는 빌드가 정한다 |
| 안 흔들린다 | ★★★ **`allocs/op` · `B/op`(3판 중 최소)** · `0 / 7` | 할당 **횟수**는 판을 잘 안 탄다(규칙 24) — ★ `B/op` 는 예행에서 **한 판이 1 B 더 나온 적**이 있어(`10737`) 최소를 싣는다 |
| 안 흔들린다 | `-benchtime=100x` 의 `B/op` | 반복 수를 고정하면 「셋업 할당 ÷ 100」이 정수로 고정된다 |
| 안 흔들린다 | `pprof -top` 의 **상위 두 이름** | ★ 퍼센트·시간은 **칸으로 안 만들었다** |

★ 정규화 규칙은 **기본 넷**만 썼다.

## 한눈에 — 쉽게 말하면

**벤치마크는 「같은 일을 N번 시키고 걸린 시간을 N으로 나누는 것」이다.** 그런데 일꾼(컴파일러)이 영리하다 — **아무도 결과를 안 보는 일은 아예 안 한다.** 그러면 「N번 했다」는 기록만 남고 **한 번에 0.2 ns** 라는, 곱셈 한 번도 못 할 시간이 찍힌다.

결과를 **게시판(전역 변수)에 붙이게** 하면 일꾼이 일을 한다. 그런데 **문제 자체가 매번 같으면(상수 입력)** 일꾼은 **답을 미리 외워 두고** 붙이기만 한다 — 게시판이 있어도 계산은 안 한 것이다.
`b.Loop` 은 1.24 에 생긴 **「이 결과는 누가 본다」는 약속**인데, 1.27.1 에서는 그 약속이 「**값을 버리지 마라**」까지라 **외워 둔 답**도 통과한다.

| 비유 | 실체 |
|---|---|
| 아무도 안 보는 일 | ★★★ **`mix(42)` 의 결과를 버림**(`D1`) — 곱셈이 기계어에 없다 |
| 게시판에 붙이기 | ★★ **전역 싱크 `sink = mix(…)`**(`D2`·`D3`) |
| 답을 미리 외움 | ★★★ **상수 접힘** — `mix(42)` 가 컴파일 때 계산됨(`D2` · 1.27.1 의 `D4`) |
| 「누가 본다」는 약속 | ★★★ **`b.Loop`** — 1.25.12 는 **인라인을 꺼서**, 1.27.1 은 **`KeepAlive`** 로 지킨다 |
| 일한 흔적 | ★★★ **`go tool objdump` 의 `IMUL`** — `mix` 는 곱셈 8번 |
| 일하는 데 든 종이 수 | ★★★ **`allocs/op`** — 시간보다 믿을 수 있는 칸 |

```text
   ★★★ 같은 mix(x) 를 재는 일곱 가지 — 기계어에 곱셈(IMUL)이 남았나

                         go1.27.1            go1.25.12
   D1  mix(42) 버림        0  ✗ 지워짐          0  ✗
   D2  sink = mix(42)      0  ✗ 접힘            0  ✗       ← 싱크가 있어도 상수면 접힌다
   D3  sink = mix(i)       8  ✓                 8  ✓
   D4  b.Loop · mix(42)    0  ✗ 접힘            호출 ✓    ← ★ 두 판이 갈린 칸
   D7  b.Loop · mix(in)    8  ✓ (인라인)        호출 ✓
   D5  sum(100) 버림       0  (빈 루프는 남음)   0
   D6  isink = sum(100)    1  ✓                 1  ✓
```

> **싱크(sink)** — 결과를 받아 두는 패키지 수준 변수. 컴파일러가 「이 값은 쓰인다」고 보게 만든다.

> **상수 접힘(constant folding)** — 입력이 컴파일 때 정해져 있으면 계산을 컴파일러가 미리 해 두는 것.

## 이 주제가 답하려는 질문

1. **벤치마크가 최적화로 지워졌는지 어떻게 아나** — `ns/op` 말고 무엇을 보나.
2. **`-benchmem` 의 어느 칸이 근거가 되나** — `allocs/op`·`B/op` 는 판과 실행을 타나.
3. **`ns/op` 로 「X 가 빠르다」를 말해도 되는 때는** — 몇 판을, 무엇과 함께.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **`objdump` 의 `IMUL`·호출 수 — 벤치 7 × 판 2** | 재려던 계산이 **기계어에 남았나** | ★ 본체 창 · 스크립트가 **탭 6칸**을 검사하고 지워진 칸·갈린 벤치를 센다 |
| ★★ **`-gcflags=-m` 의 `inlining call to`·`skip inlining`** | **왜** 지워졌나(인라인이 먼저다) | (1)절 |
| ★★★ **`allocs/op`·`B/op` — 벤치 7 × 판 2** | 할당 **횟수·바이트** | (3)절 · 결정적 칸 |
| ★★ **`ns/op` 5판의 최소·중앙·최대 · 「겹치나」** | 시간 — **흩어짐과 함께만** | (2)·(3)절 |
| ★ **`pprof -top` 의 이름** | 시간이 **어느 함수에** 갔나 | (5)절 |
| ★★ **제5의 상태 — 「기준만 다른 것」** | ★★★ **`D5`(루프 함수 결과 버림)는 42 ns 쯤 찍히고 `IMUL` 이 0 이다** — `ns/op` 는 **그럴듯한데** 잰 것은 `s += i*i` 가 아니라 **빈 루프 100번**이다(곱셈은 지워지고 카운터만 남았다). 「0.3 ns 면 지워졌다」는 **반만 맞는 판정법**이다 — 지워져도 큰 값이 나올 수 있다. ★ 1.27.1 의 `D4` 도 같은 모양 — **`b.Loop` 약속은 지켜졌는데**(값이 살아 있다) 계산은 없다 | (1)·(2)절 |
| **못 잰 것 → 창을 바꿈 — `benchstat`** | 도구가 없다(`t50which`) — **N판 최소·중앙·최대 + 겹침**으로 물었다. 유의 확률은 **없다** | 머리말 |
| **부적용 — 「1.27.1 이 1.25.12 보다 빠르다」** | ★★ **주장하지 않는다** — 판 사이 `ns/op` 는 같은 판의 흩어짐 안팎을 오가고, 이 문서는 **판 간 시간 비교를 설계하지 않았다** | 규칙 4 |

### (1) ★★★ 지워지는 벤치마크 — 기계어에 곱셈이 남았나

**언제 쓰나** — `ns/op` 가 **1 ns 아래**로 나왔을 때, 그리고 **그럴듯한 값인데 의심스러울 때.**

```text
===== 소스: t50elim_test.go =====
package ex

import "testing"

func mix(x uint64) uint64 {
	x ^= x >> 33
	x *= 0xff51afd7ed558ccd
	x ^= x >> 29
	x *= 0xc4ceb9fe1a85ec53
	x ^= x >> 32
	x *= 0x9e3779b97f4a7c15
	x ^= x >> 31
	x *= 0xbf58476d1ce4e5b9
	x ^= x >> 30
	x *= 0x94d049bb133111eb
	x ^= x >> 27
	x *= 0xd6e8feb86659fd93
	x ^= x >> 31
	x *= 0xa0761d6478bd642f
	x ^= x >> 29
	x *= 0xe7037ed1a0b428db
	return x
}

func sum(n int) int {
	s := 0
	for i := 0; i < n; i++ {
		s += i * i
	}
	return s
}

var (
	sink  uint64
	isink int
	in    uint64 = 42
)

func BenchmarkD1(b *testing.B) {
	for i := 0; i < b.N; i++ {
		mix(42)
	}
}

func BenchmarkD2(b *testing.B) {
	for i := 0; i < b.N; i++ {
		sink = mix(42)
	}
}

func BenchmarkD3(b *testing.B) {
	for i := 0; i < b.N; i++ {
		sink = mix(uint64(i))
	}
}

func BenchmarkD4(b *testing.B) {
	for b.Loop() {
		mix(42)
	}
}

func BenchmarkD5(b *testing.B) {
	for i := 0; i < b.N; i++ {
		sum(100)
	}
}

func BenchmarkD6(b *testing.B) {
	for i := 0; i < b.N; i++ {
		isink = sum(100)
	}
}

func BenchmarkD7(b *testing.B) {
	for b.Loop() {
		mix(in)
	}
}
===== 명령: for tc in go "$GO125"; do v=$("$tc" version | cut -d" " -f3); "$tc" test -c -o $v.test -gcflags=-m . 2>$v.mout || exit 1; grep -c "skip inlining within testing.B.loop" $v.mout | sed "s/^/[$v] -m 의 skip inlining within testing.B.loop 줄 수 /"; for B in D1 D2 D3 D4 D5 D6 D7; do d=$("$tc" tool objdump -s "^ex.Benchmark$B\$" $v.test); printf "%s\t%s\t%s\n" $B $(printf "%s\n" "$d" | grep -c IMUL) $(printf "%s\n" "$d" | grep -cE "CALL ex\.(mix|sum)"); done > $v.rows; done; printf "벤치\t1.27.1 IMUL 수\t1.27.1 mix·sum 호출\t1.25.12 IMUL 수\t1.25.12 mix·sum 호출\n"; paste go1.27.1.rows go1.25.12.rows | awk -F"\t" "NF!=6 || \$1!=\$4 {bad=1} {printf \"%s\t%s\t%s\t%s\t%s\n\", \$1, \$2, \$3, \$5, \$6; m+=2; if (\$2==0 && \$3==0) n++; if (\$5==0 && \$6==0) n++; if ((\$2==0 && \$3==0) != (\$5==0 && \$6==0)) k++} END {if (bad) print \"칸 수 어긋남\"; printf \"곱셈도 호출도 기계어에 안 남은 칸 %d / %d\n두 판이 갈린 벤치 %d / %d\n\", n, m, k, m/2}" =====
[go1.27.1] -m 의 skip inlining within testing.B.loop 줄 수 0
[go1.25.12] -m 의 skip inlining within testing.B.loop 줄 수 2
벤치	1.27.1 IMUL 수	1.27.1 mix·sum 호출	1.25.12 IMUL 수	1.25.12 mix·sum 호출
D1	0	0	0	0
D2	0	0	0	0
D3	8	0	8	0
D4	0	0	0	1
D5	0	0	0	0
D6	1	0	1	0
D7	8	0	0	1
곱셈도 호출도 기계어에 안 남은 칸 7 / 14
두 판이 갈린 벤치 1 / 7
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`D1`(결과 버림) — 두 판 모두 `IMUL 0 · 호출 0`** — `mix` 가 **인라인된 뒤**(아래 `-m` 줄) 결과를 아무도 안 쓰니 **통째로 지워졌다.** 루프는 `b.N` 번 **빈 채로** 돈다.
- ★★★ **`D2`(싱크 + 상수 입력 `42`) — 역시 `IMUL 0`** — 싱크에 쓰긴 하는데 `mix(42)` 가 **컴파일 때 계산돼** 상수를 쓰는 것뿐이다. **싱크는 「지우지 마라」이지 「계산해라」가 아니다.**
- ★★ **`D3`(싱크 + 입력 `uint64(i)`) — `IMUL 8`** — 입력이 매번 달라 접을 수 없다. `mix` 의 곱셈 **8번이 전부** 남았다. **재려던 것을 잰 벤치**다.
- ★★★ **`D4`(`b.Loop` + 상수 입력) — 1.27.1 `IMUL 0 · 호출 0` 대 1.25.12 `IMUL 0 · 호출 1`** — 「두 판이 갈린 벤치 **1 / 7**」의 그 하나다. 1.25.12 는 **`b.Loop` 안의 호출을 인라인하지 않아서**(`-m` 의 `skip inlining within testing.B.loop` 줄 **2**개 = `D4`·`D7`) `mix` 가 **진짜로 불린다.** 1.27.1 은 인라인한 뒤 **결과만 `KeepAlive`** 로 살리므로 **접힌 상수가 살아남는다.** 머리말 `t50ldoc` 의 문단 차이가 기계어로 보인 것이다.
- ★★ **`D7`(`b.Loop` + 전역 입력 `in`) — 1.27.1 `IMUL 8`(인라인 · 호출 0) · 1.25.12 호출 1** — 입력이 컴파일 때 모르는 값이면 **두 판 다 계산한다.** 방식만 다르다.
- ★★★ **`D5`(루프 함수 `sum(100)` 결과 버림) — `IMUL 0` 인데 (2)절에서 40 ns 대** — 곱셈은 지워졌고 **`for i < 100` 카운터 루프는 남았다.** 「지워지면 0.3 ns」가 아니다.
- ★ **`D6`(`sum` 싱크) — `IMUL 1`** — 루프 안의 곱셈 **한 줄**이 기계어 한 곳이다(회차마다 돈다).
- ★★ 「곱셈도 호출도 기계어에 안 남은 칸 **7 / 14**」 — `D1`·`D2`·`D5` 가 두 판 모두 + 1.27.1 의 `D4`.

비용 — `objdump` 는 **빌드 하나에 몇 초**다. 판정은 **결정적**이라 `ns/op` 보다 싸다.

### (2) ★★ `ns/op` — 5판의 최소·중앙·최대로만

```text
===== 소스: t50elim_test.go =====
package ex

import "testing"

func mix(x uint64) uint64 {
	x ^= x >> 33
	x *= 0xff51afd7ed558ccd
	x ^= x >> 29
	x *= 0xc4ceb9fe1a85ec53
	x ^= x >> 32
	x *= 0x9e3779b97f4a7c15
	x ^= x >> 31
	x *= 0xbf58476d1ce4e5b9
	x ^= x >> 30
	x *= 0x94d049bb133111eb
	x ^= x >> 27
	x *= 0xd6e8feb86659fd93
	x ^= x >> 31
	x *= 0xa0761d6478bd642f
	x ^= x >> 29
	x *= 0xe7037ed1a0b428db
	return x
}

func sum(n int) int {
	s := 0
	for i := 0; i < n; i++ {
		s += i * i
	}
	return s
}

var (
	sink  uint64
	isink int
	in    uint64 = 42
)

func BenchmarkD1(b *testing.B) {
	for i := 0; i < b.N; i++ {
		mix(42)
	}
}

func BenchmarkD2(b *testing.B) {
	for i := 0; i < b.N; i++ {
		sink = mix(42)
	}
}

func BenchmarkD3(b *testing.B) {
	for i := 0; i < b.N; i++ {
		sink = mix(uint64(i))
	}
}

func BenchmarkD4(b *testing.B) {
	for b.Loop() {
		mix(42)
	}
}

func BenchmarkD5(b *testing.B) {
	for i := 0; i < b.N; i++ {
		sum(100)
	}
}

func BenchmarkD6(b *testing.B) {
	for i := 0; i < b.N; i++ {
		isink = sum(100)
	}
}

func BenchmarkD7(b *testing.B) {
	for b.Loop() {
		mix(in)
	}
}
===== 명령: for tc in go "$GO125"; do v=$("$tc" version | cut -d" " -f3); "$tc" test -c -o $v.test . || exit 1; ./$v.test -test.run "^$" -test.bench . -test.count 5 -test.benchtime 0.3s > $v.txt || exit 1; echo "── $v (5판)"; awk "/^Benchmark/ {sub(/-[0-9]+\$/, \"\", \$1); print \$1, \$3}" $v.txt | sort -k1,1 -k2,2g | awk "{v[\$1]=v[\$1] \" \" \$2; c[\$1]++; if (\$2 < 2) lt[\$1]++} END {for (b in v) {split(substr(v[b], 2), a, \" \"); printf \"%s\t최소 %s ns · 중앙 %s ns · 최대 %s ns\t2 ns 미만인 판 %d / %d\n\", b, a[1], a[3], a[5], lt[b], c[b]}}" | sort; done =====
── go1.27.1 (5판)
BenchmarkD1	최소 0.2242 ns · 중앙 0.2748 ns · 최대 0.4824 ns	2 ns 미만인 판 5 / 5
BenchmarkD2	최소 0.4987 ns · 중앙 0.6118 ns · 최대 0.8044 ns	2 ns 미만인 판 5 / 5
BenchmarkD3	최소 3.718 ns · 중앙 3.866 ns · 최대 8.049 ns	2 ns 미만인 판 0 / 5
BenchmarkD4	최소 0.9398 ns · 중앙 1.019 ns · 최대 1.722 ns	2 ns 미만인 판 5 / 5
BenchmarkD5	최소 49.31 ns · 중앙 58.08 ns · 최대 89.27 ns	2 ns 미만인 판 0 / 5
BenchmarkD6	최소 57.26 ns · 중앙 65.49 ns · 최대 154.1 ns	2 ns 미만인 판 0 / 5
BenchmarkD7	최소 4.304 ns · 중앙 5.720 ns · 최대 7.062 ns	2 ns 미만인 판 0 / 5
── go1.25.12 (5판)
BenchmarkD1	최소 0.2157 ns · 중앙 0.2954 ns · 최대 0.4501 ns	2 ns 미만인 판 5 / 5
BenchmarkD2	최소 0.5098 ns · 중앙 0.5643 ns · 최대 0.7675 ns	2 ns 미만인 판 5 / 5
BenchmarkD3	최소 4.245 ns · 중앙 4.884 ns · 최대 8.980 ns	2 ns 미만인 판 0 / 5
BenchmarkD4	최소 4.078 ns · 중앙 5.903 ns · 최대 12.09 ns	2 ns 미만인 판 0 / 5
BenchmarkD5	최소 43.24 ns · 중앙 50.40 ns · 최대 51.88 ns	2 ns 미만인 판 0 / 5
BenchmarkD6	최소 59.84 ns · 중앙 98.83 ns · 최대 118.5 ns	2 ns 미만인 판 0 / 5
BenchmarkD7	최소 3.863 ns · 중앙 4.993 ns · 최대 6.886 ns	2 ns 미만인 판 0 / 5
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **「2 ns 미만인 판」이 `5 / 5` 인 벤치 = (1)절에서 곱셈이 사라진 벤치**(`D1`·`D2`, 그리고 **1.27.1 의 `D4` 만**) — `mix` 는 곱셈 8번이 **서로 기다리는** 사슬이라 한 번에 몇 ns 가 든다. 그보다 짧으면 **계산을 안 한 것**이다. ★ 판정 경계를 1 ns 가 아니라 2 ns 로 둔 이유 — 예행에서 1.27.1 의 `D4` 가 **1 ns 를 한 판 넘었다**(`b.Loop` 의 회차 비용). 경계에서 먼 값만 칸으로 삼았다.
- ★★★ **`D4` — 1.27.1 은 1 ns 아래, 1.25.12 는 3 ns 대** — (1)절의 「갈린 벤치」가 시간으로도 보인다. ★ 그러나 **「1.25.12 의 `b.Loop` 이 느리다」가 아니다** — 1.27.1 쪽이 **일을 안 한** 것이다.
- ★★★ **`D5` — 40 ns 대인데 곱셈이 없다** — 제5의 상태((0)절). `ns/op` 만 보면 **정상 벤치로 보인다.**
- ★★ **최대가 튄 판이 있다**(예: 한 판만 두 배) — 그래서 **한 판 절댓값은 근거가 아니다**(규칙 24). 최소·중앙·최대를 **같이** 싣는다.

비용 — 벤치 7 × 5판 × 0.3 s × 판 2 ≈ 21초.

### (3) ★★★ `-benchmem` — `allocs/op` 가 결정적 칸이다

**언제 쓰나** — 「이렇게 고치면 빨라지나」를 판단할 때. **시간보다 할당 수가 먼저다.**

```text
===== 소스: t50alloc_test.go =====
package ex

import (
	"strings"
	"testing"
)

var (
	ssink string
	xsink []int
	asink any
)

func BenchmarkConcat(b *testing.B) {
	for b.Loop() {
		s := ""
		for range 100 {
			s += "ab"
		}
		ssink = s
	}
}

func BenchmarkBuilder(b *testing.B) {
	for b.Loop() {
		var sb strings.Builder
		for range 100 {
			sb.WriteString("ab")
		}
		ssink = sb.String()
	}
}

func BenchmarkBuilderGrow(b *testing.B) {
	for b.Loop() {
		var sb strings.Builder
		sb.Grow(200)
		for range 100 {
			sb.WriteString("ab")
		}
		ssink = sb.String()
	}
}

func BenchmarkAppend(b *testing.B) {
	for b.Loop() {
		var xs []int
		for i := range 100 {
			xs = append(xs, i)
		}
		xsink = xs
	}
}

func BenchmarkAppendCap(b *testing.B) {
	for b.Loop() {
		xs := make([]int, 0, 100)
		for i := range 100 {
			xs = append(xs, i)
		}
		xsink = xs
	}
}

func BenchmarkBoxSmall(b *testing.B) {
	i := 0
	for b.Loop() {
		asink = i % 256
		i++
	}
}

func BenchmarkBoxLarge(b *testing.B) {
	i := 0
	for b.Loop() {
		asink = i + 1000
		i++
	}
}
===== 명령: for tc in go "$GO125"; do v=$("$tc" version | cut -d" " -f3); "$tc" test -c -o $v.test . || exit 1; ./$v.test -test.run "^$" -test.bench . -test.benchmem -test.count 3 -test.benchtime 0.1s > $v.txt || exit 1; awk "/^Benchmark/ {sub(/-[0-9]+\$/, \"\", \$1); n=split(\$0, f, \" \"); b=\$1; al=f[n-1]; by=f[n-3]; if (!(b in A)) {A[b]=al; B[b]=by; o[++k]=b} else {if (A[b]!=al) A[b]=\"흔들림\"; if (by+0 < B[b]+0) B[b]=by}} END {for (i=1; i<=k; i++) printf \"%s\t%s\t%s\n\", o[i], A[o[i]], B[o[i]]}" $v.txt > $v.rows; done; printf "벤치\t1.27.1 allocs/op\t1.27.1 B/op(최소)\t1.25.12 allocs/op\t1.25.12 B/op(최소)\n"; paste go1.27.1.rows go1.25.12.rows | awk -F"\t" "NF!=6 || \$1!=\$4 {bad=1} {printf \"%s\t%s\t%s\t%s\t%s\n\", \$1, \$2, \$3, \$5, \$6; m++; if (\$2!=\$5 || \$3!=\$6) n++} END {if (bad) print \"칸 수 어긋남\"; printf \"두 판이 갈린 벤치 %d / %d\n\", n, m}" =====
벤치	1.27.1 allocs/op	1.27.1 B/op(최소)	1.25.12 allocs/op	1.25.12 B/op(최소)
BenchmarkConcat	99	10736	99	10736
BenchmarkBuilder	6	504	6	504
BenchmarkBuilderGrow	1	208	1	208
BenchmarkAppend	8	2040	8	2040
BenchmarkAppendCap	1	896	1	896
BenchmarkBoxSmall	0	0	0	0
BenchmarkBoxLarge	1	8	1	8
두 판이 갈린 벤치 0 / 7
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **「두 판이 갈린 벤치 0 / 7」** — `allocs/op` 와 `B/op` 가 **1.27.1 과 1.25.12 에서 한 글자도 같다.** 3판 안에서도 `allocs/op` 가 안 흔들렸다(흔들리면 칸에 「흔들림」이 찍힌다).
- ★★★ **`Concat`(`s += "ab"` 100번) — 99 allocs** — 문자열은 불변이라 `+=` 마다 **새 문자열**을 만든다. 100번 이어 붙였는데 99인 것은 **첫 회(`"" + "ab"`)가 할당을 안 한 것으로 보인다** — 이 문서는 그 한 번을 따로 재지 않았다. `B/op` 10736 은 **칸의 값 그대로**다(손으로 유도하지 않는다 — 규칙 3).
- ★★ **`Builder` — 6 allocs** · **`BuilderGrow`(`Grow(200)` 먼저) — 1 alloc · 208 B** — `Builder` 는 내부 `[]byte` 를 `append` 로 늘리니 **재할당 몇 번**, `Grow` 로 미리 잡으면 **한 번**이다. ★ 요청은 200 인데 `B/op` 는 208 — 할당기가 **크기 등급**으로 올린 것으로 보인다(등급표는 재지 않았다).
- ★★ **`Append`(용량 없이 100번) — 8 allocs · 2040 B** 대 **`AppendCap`(`make(…, 0, 100)`) — 1 alloc · 896 B** — 06번의 재할당 규칙이 할당 **횟수**로 보인다.
- ★★★ **`BoxSmall`(`any` 에 `i % 256`) — 0 allocs** 대 **`BoxLarge`(`i + 1000`) — 1 alloc · 8 B** — 인터페이스에 담기는 **값에 따라** 할당이 갈린다. 아래 `-m` 블록을 보라.

```text
===== 소스: t50alloc_test.go =====
package ex

import (
	"strings"
	"testing"
)

var (
	ssink string
	xsink []int
	asink any
)

func BenchmarkConcat(b *testing.B) {
	for b.Loop() {
		s := ""
		for range 100 {
			s += "ab"
		}
		ssink = s
	}
}

func BenchmarkBuilder(b *testing.B) {
	for b.Loop() {
		var sb strings.Builder
		for range 100 {
			sb.WriteString("ab")
		}
		ssink = sb.String()
	}
}

func BenchmarkBuilderGrow(b *testing.B) {
	for b.Loop() {
		var sb strings.Builder
		sb.Grow(200)
		for range 100 {
			sb.WriteString("ab")
		}
		ssink = sb.String()
	}
}

func BenchmarkAppend(b *testing.B) {
	for b.Loop() {
		var xs []int
		for i := range 100 {
			xs = append(xs, i)
		}
		xsink = xs
	}
}

func BenchmarkAppendCap(b *testing.B) {
	for b.Loop() {
		xs := make([]int, 0, 100)
		for i := range 100 {
			xs = append(xs, i)
		}
		xsink = xs
	}
}

func BenchmarkBoxSmall(b *testing.B) {
	i := 0
	for b.Loop() {
		asink = i % 256
		i++
	}
}

func BenchmarkBoxLarge(b *testing.B) {
	i := 0
	for b.Loop() {
		asink = i + 1000
		i++
	}
}
===== 명령: go test -c -o t.test -gcflags=-m . 2>m.txt || exit 1; grep -E "i % 256|i \+ 1000" m.txt =====
./t50alloc_test.go:68:13: i % 256 escapes to heap
./t50alloc_test.go:76:13: i + 1000 escapes to heap
(exit 0)
```

- ★★★ **`-m` 은 둘 다 `escapes to heap`** 인데 **`BoxSmall` 은 0 allocs** — 런타임이 **작은 정수(0\~255)는 미리 만들어 둔 값을 가리키게** 해서 할당을 건너뛴다(이 판의 구현 — 52번 (5)절의 「`-m` 과 `allocs` 가 어긋난 칸」의 반대 방향). ★★ **`-m` 은 「힙에 둘 수도 있다」를 말하지 「할당된다」를 말하지 않는다** — 할당은 `allocs/op` 로 확인한다.

```text
===== 소스: t50alloc_test.go =====
package ex

import (
	"strings"
	"testing"
)

var (
	ssink string
	xsink []int
	asink any
)

func BenchmarkConcat(b *testing.B) {
	for b.Loop() {
		s := ""
		for range 100 {
			s += "ab"
		}
		ssink = s
	}
}

func BenchmarkBuilder(b *testing.B) {
	for b.Loop() {
		var sb strings.Builder
		for range 100 {
			sb.WriteString("ab")
		}
		ssink = sb.String()
	}
}

func BenchmarkBuilderGrow(b *testing.B) {
	for b.Loop() {
		var sb strings.Builder
		sb.Grow(200)
		for range 100 {
			sb.WriteString("ab")
		}
		ssink = sb.String()
	}
}

func BenchmarkAppend(b *testing.B) {
	for b.Loop() {
		var xs []int
		for i := range 100 {
			xs = append(xs, i)
		}
		xsink = xs
	}
}

func BenchmarkAppendCap(b *testing.B) {
	for b.Loop() {
		xs := make([]int, 0, 100)
		for i := range 100 {
			xs = append(xs, i)
		}
		xsink = xs
	}
}

func BenchmarkBoxSmall(b *testing.B) {
	i := 0
	for b.Loop() {
		asink = i % 256
		i++
	}
}

func BenchmarkBoxLarge(b *testing.B) {
	i := 0
	for b.Loop() {
		asink = i + 1000
		i++
	}
}
===== 명령: go test -c -o t.test . || exit 1; ./t.test -test.run "^$" -test.bench . -test.count 5 -test.benchtime 0.2s > r.txt || exit 1; awk "/^Benchmark/ {sub(/-[0-9]+\$/, \"\", \$1); sub(/^Benchmark/, \"\", \$1); print \$1, \$3}" r.txt | sort -k2,2g | awk "{v[\$1]=v[\$1] \" \" \$2} END {split(\"Concat Builder BuilderGrow Append AppendCap BoxSmall BoxLarge\", N, \" \"); for (i=1; i<=7; i++) {b=N[i]; split(substr(v[b], 2), a, \" \"); lo[b]=a[1]; hi[b]=a[5]; printf \"%s\t최소 %s ns · 중앙 %s ns · 최대 %s ns\n\", b, a[1], a[3], a[5]}; split(\"Concat:Builder Builder:BuilderGrow Append:AppendCap BoxSmall:BoxLarge\", P, \" \"); for (j=1; j<=4; j++) {split(P[j], q, \":\"); x=q[1]; y=q[2]; ov=(lo[x]+0 <= hi[y]+0 && lo[y]+0 <= hi[x]+0) ? \"겹친다\" : \"안 겹친다\"; printf \"%s 대 %s — 5판의 흩어짐이 %s\n\", x, y, ov}}" =====
Concat	최소 8418 ns · 중앙 8986 ns · 최대 9346 ns
Builder	최소 674.9 ns · 중앙 680.8 ns · 최대 788.1 ns
BuilderGrow	최소 403.8 ns · 중앙 436.2 ns · 최대 492.4 ns
Append	최소 1519 ns · 중앙 1803 ns · 최대 2355 ns
AppendCap	최소 625.2 ns · 중앙 834.6 ns · 최대 1119 ns
BoxSmall	최소 3.925 ns · 중앙 4.373 ns · 최대 5.273 ns
BoxLarge	최소 24.45 ns · 중앙 26.24 ns · 최대 30.41 ns
Concat 대 Builder — 5판의 흩어짐이 안 겹친다
Builder 대 BuilderGrow — 5판의 흩어짐이 안 겹친다
Append 대 AppendCap — 5판의 흩어짐이 안 겹친다
BoxSmall 대 BoxLarge — 5판의 흩어짐이 안 겹친다
(exit 0)
```

- ★★★ **네 쌍 모두 「5판의 흩어짐이 안 겹친다」** — 그러니 **이 머신·이 판에서** `Builder` 가 `Concat` 보다, `BuilderGrow` 가 `Builder` 보다, `AppendCap` 이 `Append` 보다 **빨랐다**고 말할 수 있다. **몇 배인지는 말하지 않는다** — 배수는 판마다 흔들리는 두 수의 비라 더 흔들린다.
- ★★ 그리고 **순서가 `allocs/op` 와 같다** — 99 > 6 > 1 · 8 > 1 · 1 > 0. **할당 수가 결정적 근거이고 시간은 그 확인**이다.

비용 — `-benchmem` 은 **공짜**다(`ReportAllocs` 와 같다). 벤치 7 × 3판 × 0.1 s × 판 2.

### (4) ★★ 셋업을 빼는 법 — `ResetTimer` 와 `b.Loop`

```text
===== 소스: t50reset_test.go =====
package ex

import "testing"

var bsink byte

func setup() []byte { return make([]byte, 1<<20) }

func BenchmarkNoReset(b *testing.B) {
	big := setup()
	for i := 0; i < b.N; i++ {
		bsink = big[i%len(big)]
	}
}

func BenchmarkReset(b *testing.B) {
	big := setup()
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		bsink = big[i%len(big)]
	}
}

func BenchmarkLoopSetup(b *testing.B) {
	big := setup()
	i := 0
	for b.Loop() {
		bsink = big[i%len(big)]
		i++
	}
}
===== 명령: go test -c -o t.test . || exit 1; ./t.test -test.run "^$" -test.bench . -test.benchmem -test.benchtime 100x > r.txt || exit 1; printf "벤치\t반복\tB/op\tallocs/op\n"; awk "/^Benchmark/ {sub(/-[0-9]+\$/, \"\", \$1); n=split(\$0, f, \" \"); printf \"%s\t%s\t%s\t%s\n\", \$1, \$2, f[n-3], f[n-1]}" r.txt =====
벤치	반복	B/op	allocs/op
BenchmarkNoReset	100	10485	0
BenchmarkReset	100	0	0
BenchmarkLoopSetup	100	0	0
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`NoReset` — `B/op` 10485** — 루프 **밖**의 `setup()`(1 MiB 한 번)이 **100 회차로 나뉘어** 매 회차 몫으로 잡혔다(1048576 ÷ 100 을 내림). `allocs/op` 는 1 ÷ 100 이 내림돼 **0** 으로 보인다 — **할당이 있는데 0 으로 보이는 자리**다.
- ★★ **`Reset` — `B/op` 0** — 문서 「ResetTimer zeroes the elapsed benchmark time and memory allocation counters」(머리말 `t50ldoc`). ★ `ns/op` 는 싣지 않았다(흔들린다).
- ★★ **`LoopSetup` — `B/op` 0** — `b.Loop` 문서 「Loop resets the benchmark timer the first time it is called」. **`b.Loop` 을 쓰면 `ResetTimer` 가 필요 없다.**
- ★ `-benchtime=100x` 로 **반복 수를 고정**해 나눗셈을 정수로 만들었다 — 기본(`1s`)이면 `b.N` 이 매번 달라 `B/op` 가 흔들린다.

### (5) ★ `-cpuprofile` → `go tool pprof -top`

```text
===== 소스: t50prof_test.go =====
package ex

import "testing"

func heavy(x uint64) uint64 {
	for range 300 {
		x = x*6364136223846793005 + 1442695040888963407
	}
	return x
}

func light(x uint64) uint64 {
	for range 100 {
		x ^= x << 13
		x ^= x >> 7
	}
	return x
}

var psink uint64

func BenchmarkProf(b *testing.B) {
	var x uint64 = 1
	for b.Loop() {
		x = heavy(x) + light(x)
	}
	psink = x
}
===== 명령: go test -c -o t.test . || exit 1; ./t.test -test.run "^$" -test.bench . -test.benchtime 1s -test.cpuprofile cpu.out > /dev/null || exit 1; go tool pprof -top -nodecount=5 t.test cpu.out 2>/dev/null > top.txt; echo "pprof -top 의 머리 줄: $(grep -c "flat%" top.txt)"; awk "f && NF && n < 2 {n++; printf \"flat 순위 %d\t%s %s\n\", n, \$6, \$7} /flat%/ {f=1}" top.txt =====
pprof -top 의 머리 줄: 1
flat 순위 1	ex.heavy (inline)
flat 순위 2	ex.light (inline)
(exit 0)
```

그림 해설 (한 단계씩):

- ★★ **flat 1위 `ex.heavy`, 2위 `ex.light`** — `heavy` 는 곱셈 300번, `light` 는 시프트·XOR 200번이다. ★ 퍼센트와 시간은 **칸으로 안 만들었다**(흔들린다) — **이름의 순위**만 근거로 쓴다.
- ★★ **`(inline)`** — 두 함수가 벤치 함수 안으로 인라인됐는데도 `pprof` 는 **원래 함수 이름으로** 샘플을 돌려준다(이 판의 관찰 — 어떻게 되돌리는지는 이 문서가 재지 않았다).
- ★ 프로파일(`cpu.out`)과 바이너리는 **작업 디렉토리에만** 두었다 — 저장소에는 없다.

## 문법 — 형태와 규칙

### 형태

```text
   func BenchmarkXxx(b *testing.B) {
       x := setup()                     ← b.Loop 이면 첫 호출이 타이머를 리셋한다
       for b.Loop() {                   ← 1.24+ · 조건은 정확히 "b.Loop()"
           work(x)                      ← 인자·결과가 살아남는다(문서) — 입력이 상수면 접힐 수 있다(1.27.1)
       }
   }

   func BenchmarkOld(b *testing.B) {
       x := setup()
       b.ResetTimer()                   ← 셋업 시간·할당을 뺀다
       for i := 0; i < b.N; i++ {
           sink = work(x)               ← 결과를 전역에 — 버리면 지워질 수 있다
       }
   }

   go test -run '^$' -bench . -benchmem -count 5      ← -run '^$' 로 테스트는 건너뛴다
```

- **`-benchmem`** 은 `B/op`·`allocs/op` 두 칸을 더한다 — 문서 「ReportAllocs … is equivalent to setting -test.benchmem, but it only affects the benchmark function that calls ReportAllocs」.
- **`-count N`** 은 N판을 찍는다 — 흩어짐을 보려면 **이것 없이는 안 된다.**
- **`-benchtime 100x`** 는 반복 수 고정, **`-benchtime 1s`** 는 시간 목표.

### 금지 사례 — 누가 잡나

| 쓴 꼴 | 누가 잡나 | 어디서 |
|---|---|---|
| 결과를 버린 `b.N` 루프 | ★★★ **아무도 안 잡는다** — 0.2 ns 가 찍힌다 | (1)절 `D1` |
| 싱크에 쓰지만 입력이 상수 | ★★★ **아무도 안 잡는다** — 계산이 접힌다 | (1)절 `D2` |
| `b.Loop` + 상수 입력 | ★★ **1.27.1 에서 접힌다** — 1.25.12 에서는 살았다 | (1)절 `D4` |
| 셋업을 루프 밖에 두고 `ResetTimer` 없음 | ★★ **아무도 안 잡는다** — `B/op` 에 셋업이 섞인다 | (4)절 |
| 한 판의 `ns/op` 로 결론 | ★★★ **아무도 안 잡는다** | (2)절 |

## 어디서 틀리나

### 1. ★★★ 「0.3 ns 가 안 나왔으니 지워지지 않았다」

`D5` 는 40 ns 대인데 **곱셈이 없다**((1)·(2)절). 지워진 것이 **몸통 전부**가 아니라 **일부**일 수 있다. **`objdump`(또는 `-gcflags=-m`)로 기계어를 본다.**

### 2. ★★★ 「결과를 전역 싱크에 쓰면 안전하다」

입력이 상수면 **계산이 컴파일 때 끝난다**(`D2` — `IMUL 0`). 싱크는 **값**을 살리지 **계산**을 살리지 않는다. 입력을 **컴파일 때 모르는 값**(루프 변수·전역)으로 준다.

### 3. ★★★ 「`b.Loop` 을 쓰면 컴파일러가 아무것도 못 지운다」

문서는 「kept alive, preventing … **fully** optimizing away」까지다. 1.27.1 에서 `b.Loop` + `mix(42)` 는 **접혔다**(`D4`). 그리고 그 구현은 **판마다 바뀌었다**(`t50ldoc`). **구현이 바뀌면 같은 벤치가 다른 것을 잰다.**

### 4. ★★★ 「`ns/op` 가 줄었으니 개선됐다」

한 판은 근거가 아니다 — (2)절에서 **최대가 두 배로 튄 판**이 있었다. **N판 + 흩어짐이 안 겹칠 때만** 말하고, **`allocs/op` 로 먼저** 판단한다((3)절).

### 5. ★★ 「`allocs/op` 가 0 이면 할당이 없다」

`NoReset` 은 1 MiB 를 할당했는데 **`allocs/op` 0**((4)절) — 회차 수로 나눠 **내림**된다. `B/op` 를 같이 본다.

### 6. ★★ 「`-m` 이 `escapes to heap` 이면 할당된다」

`BoxSmall` 은 `escapes to heap` 인데 **0 allocs**((3)절). 반대 방향(「does not escape」인데 할당)은 52번 (5)절.

### 7. ★ 「`pprof` 의 퍼센트를 그대로 비교한다」

샘플링이라 **흔들린다.** 이 문서는 **상위 이름의 순위**만 칸으로 삼았다((5)절).

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| 결과를 안 쓰는 계산을 지워도 된다 | **명세가 막지 않음**(관찰 가능한 동작이 같다) | (1)절 |
| 인라인·상수 접힘이 일어나는 자리 | ★★ **컴파일러(gc) 판의 성질** | (1)절 `-m` · `objdump` |
| `b.Loop` 이 인자·결과를 살린다 · 첫 호출에 타이머 리셋 | **표준 라이브러리 계약**(1.24) | `t50ldoc` · (4)절 |
| `b.Loop` 을 **어떻게** 구현하나 | ★★★ **툴체인 판** — 1.25.12 인라인 끔 · 1.27.1 `KeepAlive` | `t50ldoc` · (1)절 `D4` |
| `ResetTimer` 가 시간·할당 계수를 0 으로 | **표준 라이브러리 계약** | (4)절 |
| 작은 정수를 인터페이스에 담아도 할당 없음 | ★★ **런타임 구현** | (3)절 `BoxSmall` |
| `allocs/op` 가 1.25.12 와 1.27.1 에서 같음 | **두 판의 관찰**(보장 아님) | (3)절 `0 / 7` |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 새 벤치 | ★★ **`for b.Loop()`** + 입력을 **컴파일 때 모르는 값**으로 | 셋업 자동 제외 · 결과 살림 — 상수 입력은 접힐 수 있다 |
| 옛 `b.N` 루프 | 결과를 **싱크**에 · 셋업 뒤 **`ResetTimer`** | (1)·(4)절 |
| 「빨라졌나」 판단 | ★★★ **`-benchmem` 의 `allocs/op` 먼저** · 시간은 `-count` N판의 흩어짐 | (3)절 |
| 1 ns 아래 · 또는 의심스러운 값 | ★★ **`go tool objdump -s '^pkg.BenchmarkX$'`** 로 기계어 | (1)절 |
| 어디가 느린가 | `-cpuprofile` → `go tool pprof -top` · **이름 순위만** | (5)절 |
| 두 벤치의 차이가 작다 | **`benchstat`**(설치돼 있으면) — 이 배치는 못 썼다 | 머리말 |

## 핵심 문장

- ★★★ **결과를 버린 벤치는 지워진다 — 그리고 싱크에 써도 입력이 상수면 접힌다.** 곱셈도 호출도 안 남은 칸 `7 / 14`.
- ★★★ **`b.Loop` 은 「값」을 살리지 「계산」을 살리지 않는다** — 1.27.1 은 `b.Loop` + 상수 입력을 접었고 1.25.12 는 살렸다(`1 / 7`). 구현이 판마다 바뀌었다.
- ★★★ **`ns/op` 가 그럴듯해도 지워졌을 수 있다** — `D5` 는 40 ns 대인데 곱셈이 없다. **기계어로 확인한다.**
- ★★★ **`allocs/op` 는 판을 안 탔다**(`0 / 7`) — 시간보다 먼저 보는 칸이다. `ns/op` 는 **N판의 흩어짐이 안 겹칠 때만** 비교한다.
- ★★ **셋업은 `ResetTimer` 나 `b.Loop` 으로 뺀다** — 안 빼면 `B/op` 에 섞이고, `allocs/op` 는 내림돼 0 으로 숨는다.

## 관련 자료

- [`testing.B`](https://pkg.go.dev/testing#B) · `go help testflag` — 이 툴체인의 `go doc` 으로 떴다.
- [49번 주제](../49-testing-table-driven-t-run-cleanup-and-parallel/) — 같은 패키지의 테스트 쪽 · 판별 블록 `tapi`.
- [52번 주제](../52-tools-gofmt-vet-build-tags-embed-and-escape-analysis/) — ★ **`-gcflags=-m` 탈출 분석 읽기의 정본.** 그쪽은 힙으로 가는 여섯 모양, 여기는 그것이 **`allocs/op` 로 어떻게 보이나**.
- [06번 주제](../06-len-cap-and-append-reallocation/) — `append` 재할당 규칙 · 여기는 그 **할당 횟수**.
- [11번 주제](../11-strings-strconv-bytes-and-unicode-utf8/) — `strings.Builder` · 여기는 `+=` 와의 **할당 비교**.
- [`cs/foundations/memory-management/`](../../../../memory-management/) — 힙 할당 일반(§11 다이나믹 힙). 여기는 Go 벤치마크가 **그 횟수를 어떻게 세나**.

## 용어 풀이

- **`testing.B`** — 벤치마크 함수가 받는 값. `b.N`(반복 수) · `b.Loop()` · `b.ResetTimer()` · `b.ReportAllocs()`.
- **`b.Loop()`** — 1.24 의 반복 방식. 첫 호출에 타이머 리셋, 몸통의 호출 인자·결과를 살린다.
- **`-benchmem`** — `B/op`(회차당 바이트) · `allocs/op`(회차당 할당 횟수)를 찍는다.
- **인라인(inlining)** — 함수 호출을 그 몸통으로 바꿔 넣는 최적화. 그 뒤에야 상수 접힘·죽은 코드 제거가 된다.
- **죽은 코드 제거(dead code elimination)** — 결과가 안 쓰이는 계산을 지우는 최적화.
- **`go tool objdump`** — 바이너리를 역어셈블한다. `-s 정규식` 으로 함수 하나만.
- **`IMUL`** — x86-64 의 정수 곱셈 명령. 이 문서는 「곱셈이 남았나」의 표지로 셌다.
- **`pprof -top`** — 프로파일에서 시간을 가장 많이 쓴 함수를 표로. `flat` = 그 함수 자신, `cum` = 부른 것까지.
- **`benchstat`** — 여러 판의 벤치 결과를 통계로 견주는 도구(`golang.org/x/perf`). 이 배치에는 없었다.

## 더 들어가면

- ★ **`b.RunParallel`** — 여러 고루틴으로 같은 벤치를 돌린다. 이 문서는 돌리지 않았다.
- ★ **`-cpu 1,2,4`** — `GOMAXPROCS` 를 바꿔 가며 찍는다. 벤치 이름 끝의 `-24` 가 그 값이다(이 머신 `nproc` 24).
- ★ **`-memprofile`** · `pprof -alloc_space` — 할당이 **어디서** 났나. (3)절의 `allocs/op` 가 「몇 번」이라면 이쪽은 「어디서」다. 돌리지 않았다.

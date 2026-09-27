# go/syntax/50 — 벤치마크·`testing.B`·프로파일 읽기 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`**(판 격자는 `go1.25.12` 와 나란히)에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★ **근거로 읽을 칸** — `IMUL`·호출 수 · `7 / 14` · `1 / 7` · `allocs/op` · `B/op` · `0 / 7` · `-benchtime 100x` 의 `B/op` · `pprof` 상위 이름.
> **흔들리는 칸** — `ns/op` 의 모든 수(최소·중앙·최대).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `D1`·`D2`·`D5` 는 두 판 모두 곱셈·호출이 없고 · `D3` 은 `IMUL 8` · `D6` 은 `IMUL 1` · `D4` 는 1.27.1 이 **0·0**, 1.25.12 가 **호출 1** · `D7` 은 1.27.1 `IMUL 8`, 1.25.12 호출 1 — `7 / 14` · `1 / 7`

**출력**

```text
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

**왜 그런가**

- ★★★ `mix` 가 인라인된 뒤 **결과를 안 쓰면**(`D1`) 지워지고, **입력이 상수면**(`D2`) 컴파일 때 계산된다.
- ★★★ 1.25.12 는 `b.Loop` 몸통의 호출을 **인라인하지 않는다**(`skip inlining` 2줄 = `D4`·`D7`) — 그래서 `mix` 가 불린다. 1.27.1 은 인라인한 뒤 결과를 살리므로 `D4` 는 **접힌 상수**가 산다.

### 2. `D1`·`D2` 는 두 판 모두 `5 / 5`, `D4` 는 **1.27.1 만** `5 / 5` · `D5` 는 **수십 ns** — 잰 것은 `s += i*i` 가 아니라 **빈 카운터 루프 100번**

**출력**

```text
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

- ★★★ 1 ns 아래(여기서는 2 ns 경계)는 곱셈 8번 사슬을 **안 했다**는 뜻이다. 그런데 그 역은 아니다 — `D5` 는 그럴듯한 값인데 1번에서 `IMUL 0` 이었다(제5의 상태).
- ★★ 한 판만 두 배로 튄 칸이 있다 — **한 판 절댓값은 근거가 아니다.**

### 3. 1.25.12 — 「**disabling inlining** of functions called in a b.Loop loop」 · 1.27.1 — 「wraps such variables with a **runtime.KeepAlive** intrinsic call」 · 인라인을 끄면 `mix(42)` 가 **실제로 불리고**, `KeepAlive` 는 **값**만 살려서 컴파일 때 접힌 값이 살아남는다

**출력**

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

- ★★★ 두 판 모두 약속은 「preventing the compiler from **fully** optimizing away the loop body」다 — **「계산을 한다」는 약속이 아니다.** 구현이 바뀌자 같은 소스가 다른 것을 잰다.

### 4. `Concat 99` · `Builder 6` · `BuilderGrow 1` · `Append 8` · `AppendCap 1` · `BoxSmall 0` · `BoxLarge 1` — 두 판이 갈린 벤치 **`0 / 7`** · `i % 256` 은 **0\~255** 라 할당이 없고 `i + 1000` 은 할당된다

**출력**

```text
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

- ★★★ `allocs/op` 는 3판 안에서도, 두 판 사이에서도 안 흔들렸다 — **결정적 칸**이다.
- ★★ `BoxSmall` 이 0 인 것은 **런타임 구현**(작은 정수는 미리 만든 값을 가리킨다)이다 — 명세가 아니다. 이 문서는 256 경계 자체를 따로 재지 않았다.

### 5. `escapes to heap` 은 「**컴파일러가 스택에 둘 수 없다고 봤다**」까지다 — **런타임에 실제로 할당됐는지**는 말하지 않는다 · 할당은 `allocs/op` 가 말한다

**출력**

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

- ★★★ 같은 `escapes to heap` 두 줄이 4번에서 **0 과 1** 로 갈렸다.
- ★★ 반대 방향(「does not escape」인데 할당 1)은 [52번 주제](../52-tools-gofmt-vet-build-tags-embed-and-escape-analysis/) (5)절의 `make([]int, n)` 칸이다.

### 6. **5판의 흩어짐(최소\~최대)이 겹치지 않을 때만** 「이 머신·이 판에서 빨랐다」 · 「몇 배」는 **흔들리는 두 수의 비**라 더 흔들린다 · `benchstat` 이 없으면 **유의 확률**을 잃는다

**출력**

```text
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

- ★★★ 네 쌍 모두 「안 겹친다」 — 그리고 순서가 `allocs/op` 순서와 같다. **할당 수가 근거이고 시간은 확인**이다.
- ★★ `benchstat` 은 이 머신에 없었다(`exit=1`) — 이 문서는 **창을 바꿔**(N판 최소·중앙·최대 + 겹침) 같은 질문을 물었다.

### 7. `NoReset` — `B/op 10485` · `allocs/op 0` · `Reset` — `0 · 0` · `LoopSetup` — `0 · 0` · 1 MiB 할당이 **`allocs/op 0`** 으로 보인다

**출력**

```text
===== 명령: go test -c -o t.test . || exit 1; ./t.test -test.run "^$" -test.bench . -test.benchmem -test.benchtime 100x > r.txt || exit 1; printf "벤치\t반복\tB/op\tallocs/op\n"; awk "/^Benchmark/ {sub(/-[0-9]+\$/, \"\", \$1); n=split(\$0, f, \" \"); printf \"%s\t%s\t%s\t%s\n\", \$1, \$2, f[n-3], f[n-1]}" r.txt =====
벤치	반복	B/op	allocs/op
BenchmarkNoReset	100	10485	0
BenchmarkReset	100	0	0
BenchmarkLoopSetup	100	0	0
(exit 0)
```

- ★★★ 셋업 할당 1번 ÷ 100 회차 = **내림해서 0**, 1048576 B ÷ 100 = 10485. **할당이 있는데 0 으로 숨는다.**
- ★★ `ResetTimer` 는 「zeroes the elapsed benchmark time **and memory allocation counters**」, `b.Loop` 은 「resets the benchmark timer the first time it is called」(3번 블록).

### 8. 1위 `ex.heavy`, 2위 `ex.light` · 근거 — **이름의 순위** · 근거 아님 — 퍼센트·밀리초

**출력**

```text
===== 명령: go test -c -o t.test . || exit 1; ./t.test -test.run "^$" -test.bench . -test.benchtime 1s -test.cpuprofile cpu.out > /dev/null || exit 1; go tool pprof -top -nodecount=5 t.test cpu.out 2>/dev/null > top.txt; echo "pprof -top 의 머리 줄: $(grep -c "flat%" top.txt)"; awk "f && NF && n < 2 {n++; printf \"flat 순위 %d\t%s %s\n\", n, \$6, \$7} /flat%/ {f=1}" top.txt =====
pprof -top 의 머리 줄: 1
flat 순위 1	ex.heavy (inline)
flat 순위 2	ex.light (inline)
(exit 0)
```

- ★★ 샘플링이라 퍼센트는 판마다 흔들린다. `heavy` 가 곱셈 300번, `light` 가 시프트·XOR 200번이라 순위는 흔들리기 어렵다 — 그래도 **순위만** 칸으로 삼았다.
- ★ 두 함수가 인라인됐는데도 `(inline)` 표시와 함께 **원래 이름**으로 나온다.

### 9. 싱크는 「**결과를 버리지 마라**」를 막을 뿐 「**컴파일 때 미리 계산하지 마라**」는 못 막는다 · 입력을 **컴파일 때 모르는 값**(루프 변수 `i`·전역)으로 준다

- ★★★ 1번 — `D2`(싱크 + `42`) `IMUL 0` 대 `D3`(싱크 + `uint64(i)`) `IMUL 8`.
- ★ `D7` 처럼 `b.Loop` + 전역 입력도 두 판 다 계산했다.

### 10. `append` 가 용량을 넘길 때마다 새 배열을 잡는다는 06번 규칙이 **`allocs/op` 8 대 1** 로 보인다 · 순서 — **`allocs/op`(·`B/op`) 가 줄었다 → N판 `ns/op` 흩어짐이 안 겹친다 → (의심스러우면) 기계어로 잰 것을 확인**

- ★★ 4번 `Append 8 · 2040 B` 대 `AppendCap 1 · 896 B` · 6번 「Append 대 AppendCap — 안 겹친다」.
- ★ 기계어 확인은 1번의 방식이다 — **`ns/op` 가 그럴듯해도** 잰 것이 다를 수 있다(2번 `D5`).

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 로 **★고칠 것 0** |
| ★★★ 지워지는 벤치 (`t50elim`) | 벤치 7 × 판 2 · `objdump` 의 `IMUL`·`CALL` · 탭 6칸 검사 | 캡처마다 | **`7 / 14` · `1 / 7`** |
| ★★ `ns/op` (`t50ns`·`t50allocns`) | `-count 5` 최소·중앙·최대 · 겹침 | 캡처마다 | 값은 흔들림 · 판정은 같았다 |
| ★★★ 할당 (`t50alloc`) | `-benchmem -count 3` × 판 2 | 캡처마다 | **`0 / 7`** |
| ★★ 셋업 (`t50reset`) | `-benchtime 100x` | 캡처마다 | `10485` · `0` · `0` |
| ★ 프로파일 (`t50prof`) | `-cpuprofile` → `pprof -top` 이름 둘 | 캡처마다 | `heavy` · `light` |

**구현·환경에 달린 항목**

| 항목 | 무엇에 달렸나 |
|---|---|
| 인라인·상수 접힘·죽은 코드 제거 | **컴파일러 판** |
| `b.Loop` 의 구현 | **툴체인 판**(1.25.12 · 1.27.1 이 다르다) |
| 작은 정수 박싱에 할당 없음 | **런타임 구현** |
| `ns/op` 전부 | **이 머신**(24 스레드) · 부하 |
| `benchstat` 없음 | **이 머신의 설치 상태** |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다(기본 규칙만 — `ns/op` 는 `<time>` 이 가린다). `GO125` 가 가리키는 `go1.25.12` 툴체인이 있어야 판 격자가 돈다.

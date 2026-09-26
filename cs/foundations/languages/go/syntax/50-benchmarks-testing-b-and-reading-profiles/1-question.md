# go/syntax/50 — 벤치마크·`testing.B`·프로파일 읽기 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ **모든 문제에서 「이 동작은 명세인가, `testing` 문서의 계약인가, 컴파일러·툴체인 판의 성질인가」를 먼저 적어라.**
> 모든 실험은 `module ex` 이고 `go test -c` 로 만든 바이너리를 돌렸다(`go1.27.1` · 판 격자는 `go1.25.12` 와 나란히 — 그때 `go.mod` 는 `go 1.25`). ★ **`ns/op` 는 흔들리는 칸이다** — 값을 외우지 말고 **어느 칸이 근거가 되나**를 답하라.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 벤치 일곱과 기계어 (예측)

```go
// t50elim_test.go
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
```

<!-- 두 툴체인으로 각각 go test -c -gcflags=-m 로 빌드하고, go tool objdump -s '^ex.BenchmarkDn$' 로 벤치 함수마다 IMUL 명령 수와 CALL ex.mix / CALL ex.sum 수를 셌다. -m 출력에서 "skip inlining within testing.B.loop" 줄도 셌다. -->

- 판마다 `D1`…`D7` 의 `IMUL` 수와 `mix`·`sum` 호출 수는? 「곱셈도 호출도 안 남은 칸」과 「두 판이 갈린 벤치」는 몇 / 몇인가?

### 2. 1 ns 아래 (예측)

- 1번의 일곱 벤치를 5판씩 돌려 「2 ns 미만인 판 k / 5」를 셌다. 두 판에서 **어느 벤치가 5 / 5** 일까? `D5` 의 `ns/op` 는 1 ns 아래일까, 수십 ns 일까 — 그리고 그 값은 무엇을 잰 것인가?

### 3. `b.Loop` 문서의 한 문단 (왜)

- 1번에서 `D4` 만 두 판이 갈렸다. `go doc testing.B.Loop` 의 「kept alive」 문단이 1.25.12 와 1.27.1 에서 **어떻게 다르게** 구현을 설명하나, 그리고 그 차이가 `D4` 의 기계어를 어떻게 설명하나?

### 4. 할당 일곱 칸 (예측)

```go
// t50alloc_test.go
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
```

<!-- -benchmem -count 3 으로 두 툴체인에서 돌렸다. allocs/op 는 3판이 같으면 그 값, 다르면 「흔들림」. B/op 는 3판 중 최소. -->

- 벤치마다 `allocs/op` 는? 두 판이 갈린 벤치는 몇 / 7 인가? `BoxSmall` 과 `BoxLarge` 는 왜 다른가?

### 5. `-m` 은 둘 다 힙이라는데 (경계)

- `go test -c -gcflags=-m` 은 `asink = i % 256` 과 `asink = i + 1000` 을 **둘 다** `escapes to heap` 이라 했다. 그런데 4번에서 한쪽은 0 allocs 다. `-m` 의 `escapes to heap` 은 **무엇을 말하고 무엇을 말하지 않나**?

### 6. 「Builder 가 몇 배 빠르다」 (경계)

- 4번의 일곱 벤치를 5판씩 돌려 최소·중앙·최대를 찍었다. `Concat` 과 `Builder` 의 차이를 **어떤 조건일 때** 「빠르다」로 말할 수 있고, 「몇 배」는 왜 말하지 않나? `benchstat` 이 없을 때 무엇을 잃나?

### 7. 셋업 1 MiB (예측)

```go
// t50reset_test.go
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
```

<!-- -benchmem -benchtime 100x 로 돌렸다. -->

- 세 벤치의 `B/op` 와 `allocs/op` 는? `NoReset` 은 1 MiB 를 할당했는데 `allocs/op` 가 몇으로 보이나?

### 8. 프로파일 상위 두 줄 (예측)

```go
// t50prof_test.go
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
```

<!-- -cpuprofile cpu.out 으로 1초 돌리고 go tool pprof -top 의 flat 순위 1·2 의 이름만 찍었다. -->

- flat 1위와 2위는 어느 함수인가? 이 표에서 **근거로 쓸 칸과 쓰지 말 칸**은?

### 9. 싱크는 무엇을 살리나 (왜)

- 1번의 `D2` 는 결과를 전역 `sink` 에 썼는데도 곱셈이 없다. 싱크가 막는 것과 못 막는 것은? 옛 `b.N` 루프에서 재려던 것을 재게 하려면 **입력을** 어떻게 줘야 하나?

### 10. 할당을 줄였더니 (연결)

- [06번 주제](../06-len-cap-and-append-reallocation/)의 재할당 규칙과 4번의 `Append`·`AppendCap` 은 어떻게 이어지나? 「고쳤더니 좋아졌다」를 주장하려면 이 문서 기준으로 **어느 칸 → 어느 칸** 순서로 보여야 하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

# go/syntax/39 — `iter` 와 사용자 정의 반복자(1.23) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★ **근거로 읽을 칸** — 정리 로그 · `9 / 10` · 패닉 첫 줄과 `exit=2` · 늘어난 고루틴의 **차이** · `1 / 8`·`4 / 8` · 진단 문구.
> **근거로 읽지 않을 칸** — 패닉 트레이스백의 나머지(그래서 첫 줄만 실었다).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `9 / 10` — `panic` 에서는 `yield(1)` 이 돌아오지 않고, `defer` 로 건 정리만 돈다

**출력**

```text
===== 소스: t39clean.go =====
package main

import (
	"fmt"
	"iter"
	"strings"
)

var log []string

func note(s string) { log = append(log, s) }

// 정리를 defer 로 건다.
func withDefer() iter.Seq[int] {
	return func(yield func(int) bool) {
		defer note("정리")
		for i := range 3 {
			ok := yield(i)
			note(fmt.Sprintf("y%d=%v", i, ok))
			if !ok {
				return
			}
		}
	}
}

// 정리를 yield 가 false 일 때와 끝에서 직접 부른다.
func inline() iter.Seq[int] {
	return func(yield func(int) bool) {
		for i := range 3 {
			ok := yield(i)
			note(fmt.Sprintf("y%d=%v", i, ok))
			if !ok {
				note("정리")
				return
			}
		}
		note("정리")
	}
}

// v == 1 에서 how 대로 루프를 떠난다.
func consume(seq iter.Seq[int], how string) (res string) {
	defer func() {
		if r := recover(); r != nil {
			res = fmt.Sprint("recover ", r)
		}
	}()
outer:
	for range 1 {
		for v := range seq {
			if v != 1 {
				continue
			}
			if how == "break" {
				break
			}
			switch how {
			case "return":
				return "return"
			case "breakOuter":
				break outer
			case "panic":
				panic("body")
			}
		}
	}
	return "loop end"
}

func main() {
	ran, cells := 0, 0
	for _, how := range []string{"none", "break", "return", "breakOuter", "panic"} {
		for _, kind := range []string{"defer", "inline"} {
			log = nil
			seq := withDefer()
			if kind == "inline" {
				seq = inline()
			}
			res := consume(seq, how)
			cells++
			did := strings.Contains(strings.Join(log, " "), "정리")
			if did {
				ran++
			}
			fmt.Printf("[%-10s / %-6s] 결과=%-12s 로그=%v\n", how, kind, res, log)
		}
	}
	fmt.Printf("정리가 돈 칸 %d / %d\n", ran, cells)
}
===== 명령: go vet . && go build -trimpath -o prog . && ./prog =====
[none       / defer ] 결과=loop end     로그=[y0=true y1=true y2=true 정리]
[none       / inline] 결과=loop end     로그=[y0=true y1=true y2=true 정리]
[break      / defer ] 결과=loop end     로그=[y0=true y1=false 정리]
[break      / inline] 결과=loop end     로그=[y0=true y1=false 정리]
[return     / defer ] 결과=return       로그=[y0=true y1=false 정리]
[return     / inline] 결과=return       로그=[y0=true y1=false 정리]
[breakOuter / defer ] 결과=loop end     로그=[y0=true y1=false 정리]
[breakOuter / inline] 결과=loop end     로그=[y0=true y1=false 정리]
[panic      / defer ] 결과=recover body 로그=[y0=true 정리]
[panic      / inline] 결과=recover body 로그=[y0=true]
정리가 돈 칸 9 / 10
(exit 0)
```

**왜 그런가**

- ★★★ **`break`·`return`·`breakOuter` 는 로그가 똑같다 — `y0=true y1=false 정리`.** 몸통이 어떻게 끝나든 `yield` 가 **`false`** 를 돌려주고 반복자가 스스로 정리한다(명세 「If the loop body terminates … yield returns false」).
- ★★★ **`panic` 두 줄에는 `y1=` 이 없다** — `yield(1)` 은 **아무것도 돌려받지 못했다.** 패닉이 `yield` 호출을 뚫고 반복자 함수를 지나 `recover` 까지 갔다.
  그 되감기에서 **`defer` 는 돌고**(`[panic / defer]` 에 `정리`), **`false` 를 보고 부르던 정리는 안 돌았다**(`[panic / inline]` 에 없음).
- ★★★ **정리는 `defer` 로** 건다 — 그래야 다섯 가지가 전부 덮인다.

### 2. `vet exit=0` · 둘 다 `exit=2`, stdout `body 0|`, `after loop` 은 안 찍힌다

**출력**

```text
===== 소스: t39misuse.go =====
package main

import (
	"fmt"
	"os"
)

// yield 의 반환값을 보지 않는 반복자
func ignoring(yield func(int) bool) {
	for i := range 3 {
		yield(i)
	}
}

// 몸통의 패닉을 recover 로 삼키는 반복자
func swallowing(yield func(int) bool) {
	defer func() { recover() }()
	yield(0)
}

func main() {
	switch os.Args[1] {
	case "ignore":
		for v := range ignoring {
			fmt.Println("body", v)
			break
		}
	case "swallow":
		for v := range swallowing {
			fmt.Println("body", v)
			panic("body")
		}
	}
	fmt.Println("after loop")
}
===== 명령: go vet . && echo "vet exit=$?" && go build -trimpath -o prog . && for m in ignore swallow; do ./prog $m >out.txt 2>err.txt; rc=$?; echo "[$m] exit=$rc"; echo "  stdout: $(tr "\n" "|" < out.txt)"; echo "  stderr 첫 줄: $(sed -n 1p err.txt)"; done =====
vet exit=0
[ignore] exit=2
  stdout: body 0|
  stderr 첫 줄: panic: runtime error: range function continued iteration after function for loop body returned false
[swallow] exit=2
  stdout: body 0|
  stderr 첫 줄: panic: runtime error: range function recovered a loop body panic and did not resume panicking
(exit 0)
```

**왜 그런가**

- ★★ **`go vet` 은 침묵** — `yield(i)` 의 반환값을 버린 것을 잡는 분석기가 없다.
- ★★★ **`[ignore]` — `panic: runtime error: range function continued iteration after function for loop body returned false`.** `break` 뒤 `false` 를 받은 반복자가 `yield(1)` 을 **또 부른 그 호출**이 패닉했다.
- ★★★ **`[swallow]` — `panic: runtime error: range function recovered a loop body panic and did not resume panicking`.** 반복자가 몸통의 패닉을 삼키자 **런타임이 다시 패닉**시켰다.
- ★ 둘 다 **`runtime error:`** 로 시작한다 — 런타임이 붙인 검사다.

### 3. 첫째는 명세(must not)·`iter` 문서(panics)·런타임 셋 다 · 둘째는 런타임만

**출력**

```text
===== 명령: sed -n "6824,6836p" "$(go env GOROOT)/doc/go_spec.html" | sed -e "s/<[^>]*>//g" | awk NF =====
For a function f, the iteration proceeds by calling f
with a new, synthesized yield function as its argument.
If yield is called before f returns,
the arguments to yield become the iteration values
for executing the loop body once.
After each successive loop iteration, yield returns true
and may be called again to continue the loop.
As long as the loop body does not terminate, the "range" clause will continue
to generate iteration values this way for each yield call until
f returns.
If the loop body terminates (such as by a break statement),
yield returns false and must not be called again.
(exit 0)
```

```text
===== 명령: go doc iter | sed -n "8,10p;23,26p;150,152p"; go doc iter.Pull | sed -n "13,17p" =====
An iterator is a function that passes successive elements of a sequence to a
callback function, conventionally named yield. The function stops either when
the sequence is finished or when yield returns false, indicating to stop the
Yield returns true if the iterator should continue with the next element in the
sequence, false if it should stop.

Yield panics if called after it returns false.
If clients do not consume the sequence to completion, they must call stop, which
allows the iterator function to finish and return. As shown in the example,
the conventional way to ensure this is to use defer.
    Stop ends the iteration. It must be called when the caller is no longer
    interested in next values and next has not yet signaled that the sequence is
    over (with a false boolean return). It is valid to call stop multiple times
    and when next has already returned false. Typically, callers should “defer
    stop()”.
(exit 0)
```

- ★★★ **「`false` 뒤 다시 부르지 않는다」** — 명세는 「**must not be called again**」까지, `iter` 문서가 「**Yield panics if called after it returns false**」로 **결과를 약속**하고, 런타임이 그대로 막았다.
- ★★★ **「몸통의 패닉을 삼키지 않는다」** — **명세에도 `iter` 문서에도 없다.** 이 판 **런타임의 검사**다. 그래서 「보장」이 아니라 「**이 판의 관찰**」로 적는다.

### 4. `nostop` 은 고루틴 1 이 남고 정리가 안 돈다 · `stop` 뒤 `next` 는 `0 false`

**출력**

```text
===== 소스: t39pull.go =====
package main

import (
	"fmt"
	"iter"
	"os"
	"runtime"
	"time"
)

var cleaned bool

func naturals() iter.Seq[int] {
	return func(yield func(int) bool) {
		defer func() { cleaned = true }()
		for i := 0; ; i++ {
			if !yield(i) {
				return
			}
		}
	}
}

func settle() {
	time.Sleep(20 * time.Millisecond)
	runtime.GC()
}

func main() {
	g0 := runtime.NumGoroutine()
	next, stop := iter.Pull(naturals())
	a, _ := next()
	b, _ := next()
	settle()
	fmt.Printf("next 두 번: %d %d · 늘어난 고루틴 %d · 정리 돌았나 %v\n", a, b, runtime.NumGoroutine()-g0, cleaned)
	if os.Args[1] == "stop" {
		stop()
	}
	settle()
	fmt.Printf("[%s] 늘어난 고루틴 %d · 정리 돌았나 %v\n", os.Args[1], runtime.NumGoroutine()-g0, cleaned)
	c, ok := next()
	fmt.Printf("[%s] 그 뒤 next: %d %v\n", os.Args[1], c, ok)
}
===== 명령: go build -trimpath -o prog . && ./prog nostop && ./prog stop =====
next 두 번: 0 1 · 늘어난 고루틴 1 · 정리 돌았나 false
[nostop] 늘어난 고루틴 1 · 정리 돌았나 false
[nostop] 그 뒤 next: 2 true
next 두 번: 0 1 · 늘어난 고루틴 1 · 정리 돌았나 false
[stop] 늘어난 고루틴 0 · 정리 돌았나 true
[stop] 그 뒤 next: 0 false
(exit 0)
```

**왜 그런가**

- ★★★ **`next` 두 번 뒤 `늘어난 고루틴 1`** — `Pull` 이 반복자를 돌릴 고루틴을 세웠다.
- ★★★ **`[nostop]` 은 기다리고 GC 를 돌려도 `1` · `정리 돌았나 false`** — 반복자는 `yield` 안에서 **영영 멈춰 있다.** `next` 도 계속 된다(`2 true`).
- ★★★ **`[stop]` 은 `0` · `true`** — `stop()` 이 멈춘 `yield` 를 `false` 로 돌려보내 반복자가 `return` 하고 `defer` 가 돌았다. 그 뒤 `next` 는 **`0 false`**(문서 — 「It is valid to call next … after calling stop」).
- ★★ 문서 — 「**must be called when the caller is no longer interested**」 · 「**defer stop()**」.

### 5. push 반복자는 「멈춰 기다리는」 자리가 없다 — 그 자리로 고루틴을 세운다 · `늘어난 고루틴 1`

- ★★★ push 반복자는 **제어가 반복자 안에 있다** — `yield` 가 돌아오기 전까지 반복자 함수는 **자기 스택 위에서 달리는 중**이다. `next()` 한 번에 **값 하나만 받고 반복자를 거기 세워 두려면**, 그 스택을 들고 **기다릴 별도의 실행 흐름**이 필요하다.
- ★★ 4번의 **`늘어난 고루틴 1`** 이 그것이다. `stop` 은 그 흐름을 **끝까지 보내 주는** 신호다([31번 주제](../31-goroutine-leaks/) — 끝내는 신호가 없으면 남는다).
- ★ 런타임이 그 고루틴 사이를 **어떻게 넘기는지**(코루틴 전환)는 **소스를 안 열었다** — 차이 `1` 만 봤다.

### 6. `go 1.22` 의 함수 `range` 만 빌드가 막히고(`1 / 8`), `vet` 은 `go 1.22` 네 칸 전부 말한다(`4 / 8`) · 컴파일러와 `vet`

**출력**

```text
===== 소스: t39vcollect.go =====
package main

import (
	"fmt"
	"slices"
)

// 표준 라이브러리 함수 — slices.Collect 에 반복자를 넘긴다.
func main() {
	fmt.Println(slices.Collect(func(yield func(int) bool) { yield(7) }))
}
===== 소스: t39vmanual.go =====
package main

import (
	"fmt"
	"iter"
)

// 표준 라이브러리 타입 — iter.Seq 를 쓰되 range 없이 직접 부른다.
func main() {
	var s iter.Seq[int] = func(yield func(int) bool) { yield(7) }
	s(func(v int) bool { fmt.Println(v); return true })
}
===== 소스: t39vpull.go =====
package main

import (
	"fmt"
	"iter"
)

// 표준 라이브러리 함수 — iter.Pull 로 당긴다.
func main() {
	next, stop := iter.Pull(func(yield func(int) bool) { yield(7) })
	defer stop()
	fmt.Println(next())
}
===== 소스: t39vrange.go =====
package main

import "fmt"

func upto(yield func(int) bool) {
	for i := range 2 {
		if !yield(i) {
			return
		}
	}
}

// 언어 기능 — 함수를 range 한다.
func main() {
	for v := range upto {
		fmt.Println(v)
	}
}
===== 명령: b=0; v=0; for d in rangefunc manual collect pull; do for ver in 1.22 1.23; do printf "module ex\n\ngo $ver\n" > $d/go.mod; (cd $d && go build -o /dev/null . >b.txt 2>&1); rb=$?; (cd $d && go vet . >v.txt 2>&1); rv=$?; [ $rb -ne 0 ] && b=$((b+1)); [ $rv -ne 0 ] && v=$((v+1)); echo "[$d · go $ver] build exit=$rb · vet exit=$rv"; if [ $rb -ne 0 ]; then echo "  build: $(grep -v "^#" $d/b.txt)"; elif [ $rv -ne 0 ]; then echo "  vet  : $(grep -v "^#" $d/v.txt)"; fi; done; done; echo "빌드가 막힌 칸 $b / 8 · vet 이 말한 칸 $v / 8" =====
[rangefunc · go 1.22] build exit=1 · vet exit=1
  build: ./t39vrange.go:15:17: cannot range over upto (value of type func(yield func(int) bool)): requires go1.23 or later (-lang was set to go1.22; check go.mod)
[rangefunc · go 1.23] build exit=0 · vet exit=0
[manual · go 1.22] build exit=0 · vet exit=1
  vet  : t39vmanual.go:10:13: iter.Seq requires go1.23 or later (module is go1.22)
[manual · go 1.23] build exit=0 · vet exit=0
[collect · go 1.22] build exit=0 · vet exit=1
  vet  : t39vcollect.go:10:21: slices.Collect requires go1.23 or later (module is go1.22)
[collect · go 1.23] build exit=0 · vet exit=0
[pull · go 1.22] build exit=0 · vet exit=1
  vet  : t39vpull.go:10:21: iter.Pull requires go1.23 or later (module is go1.22)
[pull · go 1.23] build exit=0 · vet exit=0
빌드가 막힌 칸 1 / 8 · vet 이 말한 칸 4 / 8
(exit 0)
```

**왜 그런가**

- ★★★ **언어 기능은 컴파일러가 막는다** — `cannot range over upto … requires go1.23 or later (-lang was set to go1.22; check go.mod)`.
- ★★★ **표준 라이브러리는 컴파일러가 안 막는다** — `iter.Seq`·`slices.Collect`·`iter.Pull` 은 `go 1.22` 에서도 **빌드된다**(라이브러리는 툴체인의 것). **`vet` 의 `stdversion`** 이 `… requires go1.23 or later (module is go1.22)` 로 잡는다.
- ★★ 그래서 **`go build` 만 도는 CI 는 라이브러리 쪽 판 위반을 못 본다.**

### 7. `go 1.19`·`1.20` — 1.21 미만 모듈에는 일부러 침묵한다 · 이번 모듈은 `go 1.22`

- ★★★ [34번 주제](../34-context-cancellation-deadlines-and-values/) (6)절 — `vet 이 말한 판 2 / 5`, **`go 1.19`·`1.20` 은 침묵.** 분석기 소스 「**Don't report diagnostics for modules marked before go1.21**」.
- ★★ 6번은 **`go 1.22`** 모듈이라 그 문턱을 넘었다 — 그래서 **네 칸 전부** 말했다.

### 8. 불렸다(`return()` → `finally`) · Go 의 `yield` 는 돌아오지 않는다 · 공통은 `finally`/`defer` 에 건 정리

- ★★★ [JS 19번](../../../js/syntax/19-iterable-protocol-and-for-of/) — **`break`·`return`·몸통의 `throw` 셋이 전부 `return()` 을 부른다**(17 가지 중 8 곳). [JS 20번](../../../js/syntax/20-generators/) (3)절 — 그 `return()` 이 제너레이터의 **`finally`** 를 돌린다.
- ★★★ Go 는 **몸통 `panic` 에서 `yield` 가 아예 돌아오지 않는다**(1번). 소비자가 반복자를 **깨워 닫는** 장치가 없다 — push 이기 때문이다.
- ★★ **공통** — **`finally`(JS)·`defer`(Go)에 건 정리는 돈다.** Go 에서만 **`false` 를 보고 적은 정리**가 패닉에 빠진다.

### 9. 14번은 `break` 에 `false` 가 오는 것과 `go 1.22` 에러 · 이 편은 떠나는 법 5 × 정리 2 와 `panic` 의 빈칸

- ★★ [14번 주제](../14-for-four-forms-range-over-int-and-func/) (5)절 — 생산자·소비자 추적으로 **끝까지 / `break`** 두 경우를 보이고 **`yield` 가 `false`** 를 확인했다. `go 1.22` 에러도 거기서 찍었다.
- ★★★ 이 편은 **떠나는 법을 다섯으로**(`return`·`break outer`·`panic` 추가) 늘리고 **정리를 두 방식으로** 걸어, **`false` 가 오지 않는 자리(`panic`)** 를 찾았다(`9 / 10`). 그리고 **라이브러리 쪽 판 경계는 `vet` 만 본다**(6번)를 더했다.

### 10. `false` 뒤 멈추기 · `defer` 로 정리 — 값이 이미 슬라이스에 있고 몇 개 안 되면 필요 없다

- ★★★ 만드는 쪽의 계약 — **① `yield` 가 `false` 면 곧바로 돌아간다**(어기면 2번의 패닉) · **② 정리는 `defer` 로**(1번의 빈칸). 그리고 몸통의 패닉을 **삼키지 않는다**(2번 `swallow`).
- ★ 값이 **이미 메모리에 다 있고 작다면** 슬라이스를 돌려주는 편이 계약이 없다. 반복자가 값을 버는 자리는 **끝이 없거나(스트림), 크거나, 자원을 잡고 도는 것**이다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 로 **★고칠 것 0** |
| ★★★ 정리 격자 (`t39clean`) | `vet` · 떠나는 법 5 × 정리 2 | 캡처마다 | **`9 / 10`** |
| ★★★ 오용 (`t39misuse`) | stdout·stderr 분리 · stderr 첫 줄 | 캡처마다 | 두 `runtime error` 패닉 · `vet` 침묵 |
| ★★ `Pull` (`t39pull`) | `NumGoroutine` 차이 · 20ms + GC | 캡처마다 | `1` 대 `0` |
| ★★★ 판 경계 (`t39ver`) | 네 탐침 × `go 1.22`/`1.23` × `build`/`vet` | 캡처마다 | **`1 / 8` · `4 / 8`** |

**구현·환경에 달린 항목**

| 항목 | 무엇에 달렸나 |
|---|---|
| 몸통 패닉 삼킴 검사 | **이 판 런타임** — 명세·문서에 없다 |
| `Pull` 이 세우는 고루틴 | **구현** — 문서는 「고루틴」이라 적지 않는다 |
| `stdversion` 의 말하는 범위 | **이 판 `vet` 의 정책**(1.21 이상 모듈) |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다.

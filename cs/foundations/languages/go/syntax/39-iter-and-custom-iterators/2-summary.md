# go/syntax/39 — `iter` 와 사용자 정의 반복자(1.23) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Go 명세](https://go.dev/ref/spec)의 For statements with range clause · [`iter`](https://pkg.go.dev/iter) 문서.
> 명세·문서·`api/go1NN.txt` 는 **이 툴체인의 `$(go env GOROOT)` 에서 직접 떴다.** 문서가 가리키는 블로그 글(Range Over Function Types)은 **안 열었다.**\
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> ★★ **버전** — 함수 `range`(언어)와 `iter` 패키지·`slices.Collect`·`maps.Keys`(표준 라이브러리)가 **둘 다 1.23** — ★★★ **그런데 `go 1.22` 모듈에서 막히는 것은 언어 쪽 하나뿐**이다((5)절 `빌드가 막힌 칸 1 / 8`).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체는 넷째 창이다** — 「**조기 종료 정리 로그** — 반복자를 `for range` 로 돌다 다섯 가지로 떠나고 × 정리를 두 가지로 걸어, **`yield` 가 무엇을 돌려받았나 · 정리가 돌았나**를 한 줄씩 찍는 로그」.
마지막 줄 「**정리가 돈 칸 9 / 10**」 — 빠진 한 칸은 **몸통이 `panic` 할 때 `defer` 없이 적은 정리**다((1)절).
★★ 짝이 되는 창은 셋 — **런타임이 막는 두 가지 오용**((2)절) · **`iter.Pull` 의 `stop` 을 안 부르면 남는 고루틴**((3)절) · **`go.mod` 판 × `build`/`vet` 격자**((5)절).

★★★ **이 주제의 경계** — 함수 `range` 의 **기본 동작**(생산자·소비자가 번갈아 도는 추적, `break` 에 `yield` 가 `false` 를 돌려주는 것, `go 1.22` 의 컴파일 에러, `iter.Seq`·`Seq2`·`maps.Keys` 의 첫 쓰임)은
[14번 주제](../14-for-four-forms-range-over-int-and-func/) (5)·(6)절이 이미 보였다 — **여기서는 다시 재지 않는다.**
여기는 **반복자를 「만드는 쪽」의 책임** — 조기 종료 때 무엇이 도나, 계약을 어기면 누가 막나, pull 로 바꾸면 무엇을 치워야 하나 — 부터다.
`defer`·`panic`·`recover` 의 규칙은 [26번](../26-defer-evaluation-lifo-named-results-and-loops/)·[27번 주제](../27-panic-recover-and-where-to-use-them/)가 정본이다. `maps.Keys`·`slices.Sorted` 의 계약은 [38번 주제](../38-slices-maps-and-cmp/)다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | ★★★ 「`range` 가 **새로 만든 `yield`** 를 넘긴다 · 몸통이 끝나면(`break` 등) **`yield` 가 `false` 를 돌려주고 다시 불러서는 안 된다(must not)**」 — ★ 명세는 「**부르면 무엇이 되나**」를 적지 않는다 |
| **표준 라이브러리 계약** | `iter` 문서가 약속한 것 | ★★★ 「**Yield panics if called after it returns false**」 · `Pull` 은 「다 안 쓰면 **must call stop**」 · 「**defer stop()**」 |
| **구현(gc 런타임)** | 실제로 돈 것 | ★★ 두 오용을 **`runtime error` 패닉**으로 막는다((2)절) · `Pull` 이 **고루틴 하나**를 세운다((3)절) |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 정리 격자 `9 / 10` · 늘어난 고루틴 `1` · `1 / 8` · `4 / 8` |

★★★ **선을 긋는다** — 「`false` 뒤에 다시 부르면 안 된다」는 **명세**다. 「부르면 **패닉**이다」는 **`iter` 문서와 런타임**이다.
「몸통의 패닉을 반복자가 삼키면 **또 다른 패닉**」은 **명세에도 `iter` 문서에도 없다** — 이 판의 런타임이 막은 것이다((2)절).

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
```

```text
===== 명령: cd "$(go env GOROOT)/api" && grep -n "pkg iter," go1.23.txt =====
47:pkg iter, func Pull2[$0 interface{}, $1 interface{}](Seq2[$0, $1]) (func() ($0, $1, bool), func()) #61897
48:pkg iter, func Pull[$0 interface{}](Seq[$0]) (func() ($0, bool), func()) #61897
49:pkg iter, type Seq2[$0 interface{}, $1 interface{}] func(func($0, $1) bool) #61897
50:pkg iter, type Seq[$0 interface{}] func(func($0) bool) #61897
(exit 0)
```

★ 명세의 판 부록(함수 `range` 는 `Go 1.23`):

```text
===== 명령: sed -n "8764,8784p;8827,8832p;8842,8857p" "$(go env GOROOT)/doc/go_spec.html" | sed -e "s/<[^>]*>//g" | awk NF =====
Go 1.18
The 1.18 release adds polymorphic functions and types ("generics") to the language.
Specifically:
The set of operators and punctuation includes the new token ~.
Function and type declarations may declare type parameters.
Interface types may embed arbitrary types (not just type names of interfaces)
as well as union and ~T type elements.
The set of predeclared types includes the new types
any and comparable.
Go 1.23
A "for" statement with "range" clause accepts an iterator
function as range expression.
Go 1.27
Function type inference applies in all
assignment contexts involving functions.
A method declaration may declare
type parameters.
A key in a struct composite literal may
be any valid field selector for the struct type,
not just a (top-level) field name of the struct.
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ **정리 로그 · `9 / 10` · `yield` 반환값** | 한 고루틴 안의 순서 — 스케줄링이 끼지 않는다 |
| 안 흔들린다 | ★★★ **두 패닉의 첫 줄 · 종료 코드 `2`** | ★ 트레이스백 나머지(주소 오프셋)는 **안 실었다** — 첫 줄만 뜬다(배너에 적혀 있다) |
| 안 흔들린다 | ★★ **늘어난 고루틴 `1`/`0` · 정리 돌았나** | `NumGoroutine` 의 **차이**만 찍었다 — `20ms` 기다린 뒤 GC 까지 돌렸다 |
| 안 흔들린다 | `1 / 8` · `4 / 8` · 진단 문구 | 정적 판정 |

★ 정규화 규칙은 **기본 넷**만 썼다.

## 한눈에 — 쉽게 말하면

**`iter.Seq` 는 「회전초밥 레일」이다.** 주방(반복자)이 접시를 **밀어 보낸다**(push) — 손님(루프 몸통)은 접시가 오면 먹고 「**더 줘요(`true`)**」 또는 「**그만(`false`)**」 을 말한다.
「그만」을 들은 주방은 **불을 끄고 정리**한다 — 그런데 손님이 **쓰러지면**(`panic`) 「그만」이라는 말이 안 온다. 그때도 불을 끄려면 **「퇴근할 때 무조건 끈다」(`defer`)** 로 걸어 둬야 한다.
**`iter.Pull`** 은 레일을 **「벨 누르면 한 접시씩」** 으로 바꾸는 장치다 — 대신 **주방 직원 한 명(고루틴)이 대기**하고, 「영업 끝(`stop`)」을 안 알리면 **퇴근을 못 한다.**

| 비유 | 실체 |
|---|---|
| 주방이 밀어 보낸다 | ★★★ **push 반복자** — 반복자가 `yield(v)` 를 **부른다** |
| 「더 줘요 / 그만」 | ★★ **`yield` 의 반환값 `true`/`false`** |
| 「그만」을 듣고 정리 | ★★ **`if !yield(v) { 정리; return }`** — `break`·`return` 에서 돈다((1)절) |
| 손님이 쓰러지면 「그만」이 안 온다 | ★★★ **몸통 `panic` — `yield` 가 아예 돌아오지 않는다** · `defer` 만 돈다((1)절 `9 / 10`) |
| 「그만」을 듣고도 계속 내보냄 | ★★★ **런타임 패닉** `range function continued iteration …`((2)절) |
| 벨 누르면 한 접시 | ★★ **`iter.Pull`** — `next()` 로 **당긴다**(pull) |
| 대기 직원이 퇴근을 못 함 | ★★★ **`stop` 을 안 부르면 고루틴 1 · 정리 안 돎**((3)절) |

```text
   ★★★ push 대 pull — 누가 누구를 부르나

   push (iter.Seq · 함수 range)                       pull (iter.Pull · Rust next · JS·Python 제너레이터)

   반복자 ──yield(v)──▶ 루프 몸통                     소비자 ──next()──▶ 반복자
          ◀──true/false──                                    ◀──(v, ok)──
   ★ 반복자가 부르는 쪽 — 제어 흐름이 반복자 안에 있다     ★ 소비자가 부르는 쪽 — 반복자는 멈춰 기다린다
   ★ 조기 종료 신호 = yield 가 돌려주는 false            ★ 조기 종료 신호 = stop() · return() · close()
   ★ 정리 = 반복자 함수의 defer (자기 스택)               ★ 정리 = 멈춘 자리를 깨워 finally 를 돌린다

   iter.Pull 이 push 를 pull 로 바꾸려면 → 반복자를 「멈춰 기다리게」 할 자리가 필요 → 고루틴 하나 ((3)절)
```

> **push 반복자** — 반복자가 값마다 **콜백(`yield`)을 부르는** 방식. 제어가 반복자 쪽에 있다. `iter.Seq` 가 이것이다.

> **pull 반복자** — 소비자가 `next()` 를 불러 **하나씩 당기는** 방식. Rust `Iterator`·JS·Python 제너레이터가 이것이다.

> **`iter.Pull`** — push 반복자를 `next`·`stop` 두 함수로 바꿔 준다(1.23). 다 안 쓰고 그만둘 때는 **`stop` 을 불러야** 한다.

- ★★ [14번 주제](../14-for-four-forms-range-over-int-and-func/) (5)절 — 생산자·소비자 추적에서 `break` 하면 **`yield` 가 `false`** 였다. 이 편 (1)절은 그 `false` 가 **오지 않는 떠나는 법**을 찾는다.
- ★★ [26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/) · [27번 주제](../27-panic-recover-and-where-to-use-them/) (1)절 — **패닉은 `defer` 를 돌리며 스택을 푼다.** 반복자 함수도 그 스택의 한 칸이다.

## 이 주제가 답하려는 질문

1. **반복자를 조기에 떠나는 방법마다, 반복자의 정리 코드는 도나** — `defer` 로 건 것과 `false` 를 보고 부른 것이 갈리나.
2. **반복자가 계약을 어기면 누가 막나** — 명세·문서·런타임 중 누구의 말인가.
3. **pull 로 바꾸면 무엇이 생기고, 무엇을 치워야 하나.** 그리고 **1.23 경계는 누가 지키나.**

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **정리 로그 — 떠나는 법 5 × 정리 방식 2** | `yield` 가 받은 값 · 정리가 **돌았나** | ★ 본체 창 |
| ★★★ **패닉 첫 줄 · 종료 코드** | 런타임이 **어떤 오용을** 막나 | (2)절 — stdout 과 stderr 를 **따로** 받았다(규칙 18) |
| ★★ **`NumGoroutine` 의 차이** | `Pull` 이 세운 것이 **남나** | [31번 주제](../31-goroutine-leaks/)의 기법 |
| ★★★ **`go.mod` 판 × `build`/`vet`** | 1.23 경계를 **누가** 지키나 | [34번 주제](../34-context-cancellation-deadlines-and-values/) (6)절 방식 |
| ★ **`go vet`** | 반복자가 `yield` 의 반환값을 버리면 잡나 | (2)절 — **`vet exit=0`** 침묵 |
| **부적용 — 시간** | push 대 pull 의 **속도**는 안 쟀다 | 규칙 5 |
| **부적용 — `-race`** | 이 주제의 반복자는 전부 **한 고루틴에서** 부른다. `Pull` 의 `next`·`stop` 도 **한 고루틴에서만** 불렀다(문서 — 「It is an error to call next or stop from multiple goroutines simultaneously」) | [35번 주제](../35-data-races-and-the-race-detector/) |

### (1) ★★★ 조기 종료 정리 로그 — 떠나는 법 × 정리 방식

**언제 쓰나** — 반복자 안에서 **파일을 열거나 잠금을 잡고** 값을 내보낼 때. 소비자가 **어떻게 떠나든** 닫혀야 한다.

```go
// t39clean.go
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
```

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

그림 해설 (한 단계씩):

- ★★ **`none`(끝까지)** — `y0`·`y1`·`y2` 가 전부 `true`, 반복자가 스스로 끝나며 **두 방식 다 정리.**
- ★★★ **`break`·`return`·`breakOuter` — 세 가지가 로그가 똑같다(`y0=true y1=false 정리`).** 몸통이 **어떻게** 끝나든 **`yield` 가 `false` 를 돌려준다** — 명세 「If the loop body terminates (such as by a break statement), yield returns false」.
  ★ **`return` 은 바깥 함수를 떠나는데도** `yield` 가 먼저 `false` 로 **돌아온 뒤** 반복자가 정리하고, 그다음 `consume` 이 `"return"` 을 돌려준다. **`break outer` 도 안쪽 루프 입장에서는 「떠남」** 이다.
- ★★★ **`panic` — `y1` 줄이 없다.** 몸통이 패닉하면 **`yield` 는 돌아오지 않는다** — `false` 도 `true` 도 아니다. 패닉이 **`yield` 호출을 뚫고 반복자 함수를 지나** `consume` 의 `recover` 까지 간다.
  **`defer` 로 건 정리는 돌았고**([27번 주제](../27-panic-recover-and-where-to-use-them/) (1)절 — 되감기가 `defer` 를 돌린다), **`false` 를 보고 부르던 정리는 안 돌았다.**
- ★★★ **마지막 줄 `정리가 돈 칸 9 / 10`** — 빠진 한 칸이 **`panic / inline`** 이다. **반복자의 정리는 `defer` 로 건다** — 그래야 다섯 가지 떠나는 법이 전부 덮인다.

```text
   ★★★ 떠나는 법마다 yield 가 받는 것과 정리 ((1)절의 실측)

   떠나는 법            yield(1) 이 돌려준 것      defer 정리    if !yield { 정리 }
   끝까지 (none)        true                       ✓             ✓ (함수 끝에서)
   break                false                      ✓             ✓
   return               false                      ✓             ✓
   break outer          false                      ✓             ✓
   panic (몸통)         ★ 돌아오지 않는다          ✓             ✗   ← 9 / 10 의 빈칸
```

★★★ **JS 와 나란히** — 같은 질문을 JS 는 **`return()`** 으로 답한다.

| 떠나는 법 | JS `for...of` ([JS 19번](../../../js/syntax/19-iterable-protocol-and-for-of/)·[20번](../../../js/syntax/20-generators/)) | Go 함수 `range` (이 편) |
|---|---|---|
| 끝까지 | `done` 을 직접 봤다 → `return()` **안 부른다** | 반복자가 스스로 끝남 |
| `break`·`return` | **`return()` 을 부른다** → 제너레이터의 `finally` | **`yield` 가 `false`** → 반복자가 스스로 정리 |
| 몸통의 `throw`/`panic` | ★ **역시 `return()` 을 부른다** — `finally` 가 돈다 | ★★★ **`yield` 가 안 돌아온다** — `defer` 만 돈다 |
| 바깥 루프로 | `continue outer` 도 `return()`(19번) | `break outer` 도 `false` |

- ★★ JS 19번은 소비자 17 가지 중 **8 곳에서 `return()`** 이 불렸다. 그쪽은 **소비자가 반복자를 깨워 닫는** 설계(pull)이고, Go 는 **반복자가 신호를 받아 스스로 닫는** 설계(push)다.
- ★★ Python 제너레이터의 `close()` 도 pull 쪽이다 — 멈춘 자리에 `GeneratorExit` 를 던져 `finally` 를 돌린다([Python 17번](../../../python/syntax/17-generators-yield/)).
  ★ **셋 다 「`finally`/`defer` 에 건 정리는 돈다」가 결론**이고, Go 에서만 **`false` 를 보고 적은 정리**가 패닉에 빠진다.

비용 — 없다.

### (2) ★★★ 반복자가 계약을 어기면 — 런타임이 막는다

**명세는 「must not be called again」까지만** 말한다:

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

`iter` 문서는 한 걸음 더 간다:

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

그러면 실제로 — `yield` 의 반환값을 **버리는** 반복자와, 몸통의 패닉을 **삼키는** 반복자:

```go
// t39misuse.go
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
```

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

그림 해설 (한 단계씩):

- ★★ **`vet exit=0`** — `go vet` 은 **`yield(i)` 의 반환값을 버린 것**에 침묵했다. 컴파일러도 통과시킨다.
- ★★★ **`[ignore]` — `panic: runtime error: range function continued iteration after function for loop body returned false`**, `exit=2`.
  몸통이 `break` 한 뒤 반복자가 `yield(1)` 을 **또 불렀고**, **그 호출 자체가 패닉**했다. `after loop` 은 **안 찍혔다.**
  ★★ `runtime error:` 가 붙는다 — **런타임이 붙인 검사**다. `iter` 문서의 「**Yield panics if called after it returns false**」가 이것이다.
- ★★★ **`[swallow]` — `panic: runtime error: range function recovered a loop body panic and did not resume panicking`.**
  몸통의 `panic("body")` 를 반복자의 `recover` 가 **삼키자**, 런타임이 **그것을 또 다른 패닉으로** 바꿨다. 반복자는 **몸통의 패닉을 먹을 권리가 없다.**
  ★★★ **이 두 번째 검사는 명세에도 `iter` 문서에도 없다** — 이 판 런타임의 관찰이다.

```text
   ★★ 반복자 계약 — 누가 말하고 누가 막나

   계약                                       명세         iter 문서        런타임(이 판)
   false 뒤에 yield 를 다시 부르지 않는다       must not     Yield panics     runtime error 패닉  ✓ (2)절
   몸통의 패닉을 삼키지 않는다                  —            —                runtime error 패닉  ✓ (2)절
   yield 의 반환값을 본다                       —            —                (다시 부를 때 잡힘)
   go vet                                      —            —                침묵 (vet exit=0)
```

비용 — 없다.

### (3) ★★ `iter.Pull` — pull 로 바꾸면 고루틴이 선다

**언제 쓰나** — 두 반복자를 **번갈아** 한 칸씩 당겨야 할 때(병합·지퍼). `for range` 로는 둘을 동시에 못 돈다.

```go
// t39pull.go
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
```

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

그림 해설 (한 단계씩):

- ★★★ **`next` 두 번 뒤 `늘어난 고루틴 1`** — `Pull` 이 반복자를 돌릴 **고루틴 하나**를 세웠다. `naturals` 는 `yield` 안에서 **멈춰 기다리고** 있다(그림의 「멈춰 기다리게 할 자리」).
- ★★★ **`[nostop]` — 20ms 기다리고 GC 까지 돌린 뒤에도 `늘어난 고루틴 1` · `정리 돌았나 false`.** 반복자의 `defer` 가 **영영 안 돈다.** 그리고 **`next` 는 계속 된다**(`2 true`) — 끝나지 않았으니까.
- ★★★ **`[stop]` — `늘어난 고루틴 0` · `정리 돌았나 true`.** `stop()` 이 멈춰 있던 `yield` 를 **`false` 로 돌려보내** 반복자가 `return` 하고 `defer` 가 돌았다. 그 뒤 `next` 는 **`0 false`**(문서 — 「It is valid to call next … after calling stop」).
- ★★ 문서 — 「**It must be called when the caller is no longer interested in next values**」 · 「**Typically, callers should "defer stop()"**」. [31번 주제](../31-goroutine-leaks/)의 누수와 **같은 모양**이다 — **끝내는 신호를 안 보내면 남는다.**

비용 — **안 쟀다.** 고루틴을 세우는 값이 `for range` 보다 얼마나 비싼지는 이 주제의 질문이 아니다.

### (4) ★ `Seq`·`Seq2`·이름 규칙 — 인용만

- ★★ `iter.Seq[V]` 는 `func(yield func(V) bool)` 의, `Seq2[K, V]` 는 `func(yield func(K, V) bool)` 의 **이름 붙은 타입**이다(머리말 `api` 블록 `go1.23.txt:49-50`). 첫 쓰임과 `%T` 는 [14번 주제](../14-for-four-forms-range-over-int-and-func/) (6)절이 정본이다.
- ★ 문서의 이름 관례 — 컬렉션의 전체 반복자는 **`All`**, 여럿이면 **`Keys`·`Values`·`Backward`** 처럼 **무엇을 도는지**를 이름에 적는다. **한 번만 돌 수 있는(single-use)** 반복자는 **문서 주석에 그렇게 적어야** 한다(이 문서는 던지지 않았다).

### (5) ★★★ 1.22 대 1.23 — 누가 경계를 지키나

같은 1.23 의 네 가지 — **언어 기능 하나(함수 `range`)와 표준 라이브러리 셋(`iter.Seq` 타입 · `slices.Collect` · `iter.Pull`)** — 을 `go 1.22`·`1.23` 두 판으로 빌드하고 `vet` 했다:

```go
// t39vrange.go
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
```

```go
// t39vmanual.go
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
```

```go
// t39vcollect.go
package main

import (
	"fmt"
	"slices"
)

// 표준 라이브러리 함수 — slices.Collect 에 반복자를 넘긴다.
func main() {
	fmt.Println(slices.Collect(func(yield func(int) bool) { yield(7) }))
}
```

```go
// t39vpull.go
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
```

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

그림 해설 (한 단계씩):

- ★★★ **`빌드가 막힌 칸 1 / 8`** — `go 1.22` 의 **함수 `range` 하나**만 막혔다(`requires go1.23 or later (-lang was set to go1.22; check go.mod)` — [14번 주제](../14-for-four-forms-range-over-int-and-func/) (5)절과 같은 문구).
  ★★★ **`iter.Seq`·`slices.Collect`·`iter.Pull` 은 `go 1.22` 에서도 빌드됐다** — 표준 라이브러리는 **툴체인(1.27.1)의 것**이라 **컴파일러가 `go` 줄로 막지 않는다**([34번 주제](../34-context-cancellation-deadlines-and-values/) (6)절의 `context` 와 같은 결론).
- ★★★ **`vet 이 말한 칸 4 / 8`** — `go 1.22` 의 네 칸 전부. 라이브러리 셋은 **`stdversion`** 이 `iter.Seq requires go1.23 or later (module is go1.22)` 로 잡았다.
  ★★ 34번에서 `stdversion` 은 **1.21 미만 모듈에 침묵**했다 — 이번엔 모듈이 `go 1.22` 라 **말한다.**
- ★★ 그래서 경계를 지키는 것이 **둘로 갈린다** — **언어 기능은 컴파일러가, 표준 라이브러리는 `vet` 이.** `go build` 만 돌리는 CI 는 **라이브러리 쪽 판 위반을 못 본다.**

비용 — 없다.

## 문법 — 형태와 규칙

### 형태

```go
// t39clean.go
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
```

규칙 불릿.

- ★★★ **`if !yield(v) { return }`** — `false` 를 받으면 **곧바로 돌아간다.** 다시 부르면 런타임 패닉((2)절).
- ★★★ **정리는 `defer` 로** — 몸통의 `panic` 에는 `false` 가 안 온다((1)절 `9 / 10`).
- ★★★ **반복자 안에서 `recover` 로 몸통의 패닉을 삼키지 않는다** — 런타임 패닉((2)절).
- ★★ **`iter.Pull` 을 쓰면 바로 다음 줄에 `defer stop()`** — 안 부르면 고루틴이 남고 정리가 안 돈다((3)절).
- ★★ 공개 API 는 **`iter.Seq[V]`/`Seq2[K, V]` 를 돌려준다**(문서의 관례 — `range` 와 표준 어댑터가 받는다).
- ★ 1.23 경계 — `go.mod` 가 `go 1.23` 이상이어야 함수 `range` 가 된다. 라이브러리 판 위반은 **`go vet`** 이 잡는다((5)절).

### 금지 사례 — 누가 잡나

| 쓴 꼴 | 누가 잡나 | 어디서 |
|---|---|---|
| `yield(i)` 의 반환값을 버리고 계속 부름 | ★★★ **런타임** — `continued iteration after … returned false` · `vet` 은 침묵 | (2)절 |
| 반복자에서 몸통의 패닉을 `recover` 로 삼킴 | ★★★ **런타임** — `recovered a loop body panic` | (2)절 |
| 정리를 `if !yield { … }` 에만 둠 | ★★★ **아무도 안 잡는다** — 몸통 `panic` 때 안 돈다 | (1)절 |
| `iter.Pull` 뒤 `stop` 을 안 부름 | ★★★ **아무도 안 잡는다** — 고루틴 1 · 정리 안 돎 | (3)절 |
| `go 1.22` 모듈의 함수 `range` | 컴파일러 — `requires go1.23 or later` | (5)절 |
| `go 1.22` 모듈의 `iter`·`slices.Collect` | ★★ **`go vet` 만** — 빌드는 통과 | (5)절 |

## 어디서 틀리나

### 1. ★★★ 「조기 종료면 언제나 `yield` 가 `false` 를 받는다」

- (1)절 — **몸통 `panic` 에서는 `yield` 가 돌아오지 않는다.** `false` 를 보고 하던 정리가 빠진다.

### 2. ★★★ 「`yield` 의 반환값을 무시해도 몸통이 안 돌면 그만이다」

- (2)절 — **다시 부르는 순간 런타임 패닉**이다. `vet` 은 미리 말해 주지 않는다.

### 3. ★★ 「반복자 안의 `recover` 로 소비자의 패닉을 막아 주면 친절하다」

- (2)절 — **런타임이 금지한다**(`did not resume panicking`).

### 4. ★★★ 「`iter.Pull` 은 그냥 함수 두 개다」

- (3)절 — **고루틴이 하나 선다.** `stop` 을 안 부르면 **남고**, 반복자의 `defer` 도 안 돈다.

### 5. ★★ 「`go 1.22` 모듈에서는 1.23 반복자 API 를 쓰면 빌드가 깨진다」

- (5)절 — **함수 `range` 만** 깨진다. 라이브러리는 **`vet` 이 말할 때까지** 조용하다.

### 6. ★ 「Go 반복자도 JS 처럼 소비자가 닫는다」

- (1)절 대비 표 — Go 는 **push** 다. 소비자는 **`false` 를 돌려줄 뿐** 반복자를 깨우지 않는다. 닫는 것은 **반복자 자신**이다.

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| 함수 `range` · 새로 만든 `yield` · `false` 뒤 must not | **명세 [Go 1.23]** | (2)절 `t39spec` |
| `break`·`return`·`break outer` 에 `yield` 가 `false` | **명세**(「loop body terminates」) | (1)절 |
| 몸통 `panic` 에 `yield` 가 안 돌아오고 `defer` 만 돈다 | **명세의 귀결**(패닉 되감기 — [27번 주제](../27-panic-recover-and-where-to-use-them/)) · 이 판에서 확인 | (1)절 |
| ★★★ **`false` 뒤 호출 → 패닉** | **`iter` 문서 계약 + 런타임** | (2)절 |
| ★★★ **몸통 패닉 삼킴 → 패닉** | **런타임(이 판)** — 명세·문서에 없음 | (2)절 |
| `Pull` 은 `stop` 을 불러야 한다 · `next` 는 stop 뒤에도 안전 | **`iter` 문서 계약** | (3)절 |
| ★★ **`Pull` 이 고루틴 하나를 세운다** | **구현** — 문서는 「고루틴」을 말하지 않는다 | (3)절 |
| ★★ **언어 기능은 컴파일러, 라이브러리는 `vet`** | **도구의 정책**(`-lang` · `stdversion`) | (5)절 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 자기 컬렉션을 `for range` 로 돌게 하고 싶다 | ★★★ **`All() iter.Seq[V]`** 메서드 | 문서의 관례 · 표준 어댑터가 받는다 |
| 반복자 안에 파일·잠금 같은 자원 | ★★★ **`defer` 로 정리** | (1)절 `9 / 10` |
| 두 반복자를 한 칸씩 번갈아 | **`iter.Pull` + `defer stop()`** | (3)절 |
| 반복자를 슬라이스로 | `slices.Collect` · 정렬까지 `slices.Sorted` | [38번 주제](../38-slices-maps-and-cmp/) |
| `go 1.22` 이하 모듈을 지원해야 한다 | ★★ **함수 `range` 를 쓰지 않는다** · CI 에 **`go vet`** | (5)절 |
| 값이 몇 개 안 되고 이미 슬라이스에 있다 | ★ **그냥 슬라이스를 돌려준다** — 반복자는 계약(정리·`false`)을 떠안는 값이 있다 | (1)·(2)절 |

## 핵심 문장

- ★★★ **`break`·`return`·`break outer` 는 `yield` 에 `false` 를 돌려주고, 몸통 `panic` 은 `yield` 를 돌아오지 않게 한다** — 정리가 돈 칸 **`9 / 10`**, 빈칸은 `defer` 없이 적은 정리.
- ★★★ **`false` 뒤에 `yield` 를 또 부르면 `panic: runtime error: range function continued iteration after function for loop body returned false`** — 명세는 must not, `iter` 문서와 런타임이 패닉. `vet` 은 침묵.
- ★★ **반복자가 몸통의 패닉을 삼키면 `range function recovered a loop body panic and did not resume panicking`** — 명세·문서에 없는 런타임 검사.
- ★★★ **`iter.Pull` 은 고루틴 하나를 세운다 — `stop` 을 안 부르면 `1` 이 남고 `defer` 가 안 돈다.** `defer stop()`.
- ★★★ **`go 1.22` 에서 막히는 것은 함수 `range` 하나(`1 / 8`)** — 라이브러리 셋은 빌드되고 **`vet` 이 `4 / 8` 로 말한다.**
- ★★ **Go 반복자는 push** — JS·Python·Rust 의 pull 과 달리 **반복자가 스스로 닫는다.** JS 는 `return()`, Go 는 `false`.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 39번)
- [14번 주제](../14-for-four-forms-range-over-int-and-func/)(`for` 의 네 형태) — ★★ **함수 `range` 의 기본 동작·`go 1.22` 에러의 정본**
- [38번 주제](../38-slices-maps-and-cmp/)(`slices`·`maps`) — ★ 목록상 선행 · `maps.Keys`·`slices.Sorted`·`Collect`
- [37번 주제](../37-generics-type-parameters-and-constraint-interfaces/)(제네릭) — `iter.Seq[V]` 는 제네릭 타입이다
- [26번](../26-defer-evaluation-lifo-named-results-and-loops/)·[27번 주제](../27-panic-recover-and-where-to-use-them/) — `defer`·패닉 되감기 · [31번 주제](../31-goroutine-leaks/) — 끝내는 신호가 없으면 남는다 · [34번 주제](../34-context-cancellation-deadlines-and-values/) (6)절 — `stdversion`
- [JS 19번](../../../js/syntax/19-iterable-protocol-and-for-of/)·[20번](../../../js/syntax/20-generators/) — ★★★ **`return()` 과 `finally` 의 대비** · [Python 17번](../../../python/syntax/17-generators-yield/) — `close()` · [Rust 36번](../../../rust/syntax/36-iterator-adapters-laziness-and-collect/) — pull 반복자(`next`)

## 용어 풀이

- **반복자 함수** — `func(yield func(V) bool)` 꼴. 1.23 부터 `range` 가 받는다.
- **`yield`** — `range` 가 새로 만들어 넘기는 함수. `true` 면 계속, `false` 면 멈춰야 한다.
- **`iter.Seq[V]`·`iter.Seq2[K, V]`** — 반복자 함수 타입의 이름(1.23).
- **push / pull** — 반복자가 콜백을 부르는 방식 / 소비자가 `next` 로 당기는 방식.
- **`iter.Pull`** — push 를 pull 로 바꾼다. `next`·`stop` 을 돌려준다. `stop` 을 불러야 한다.
- **조기 종료** — 반복자가 끝나기 전에 루프를 떠나는 것(`break`·`return`·`goto`·바깥 `break`·`panic`).
- **`stdversion`** — `go.mod` 판보다 새 표준 API 를 알리는 `vet` 분석기(1.21 이상 모듈만).

---

## 더 들어가면

- ★ 문서가 가리키는 블로그 글(Range Over Function Types)은 **안 열었다.**
- ★ `Pull` 이 쓰는 런타임의 코루틴 전환(고루틴 사이를 **번갈아** 넘기는 장치)은 **소스를 안 열었다** — (3)절은 `NumGoroutine` 의 차이만 봤다.
- ★ 반복자 안에서 `yield` 를 **다른 고루틴에서** 부르면 무엇이 되는지는 **던지지 않았다.**
- ★ `goto` 로 루프 밖으로 뛰는 떠나는 법은 격자에 넣지 않았다.

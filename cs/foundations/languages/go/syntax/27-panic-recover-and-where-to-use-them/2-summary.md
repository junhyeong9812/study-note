# go/syntax/27 — `panic`·`recover` 와 쓰는 자리 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Go 명세 — Handling panics](https://go.dev/ref/spec#Handling_panics) ·
> [`builtin.panic`/`recover`](https://pkg.go.dev/builtin) · [GODEBUG](https://go.dev/doc/godebug) ·
> [Go 1.25 릴리스 노트](https://go.dev/doc/go1.25)(재패닉 표시 — **이것만 웹에서 열었다**).
> 명세·`godebug.md`·표준 라이브러리 소스는 **이 툴체인의 `$(go env GOROOT)` 에서 직접 떴다.**\
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> ★★ **버전** — `panic(nil)` 이 **1.21**부터 `*runtime.PanicNilError`((7)절 — **`go.mod` 판 격자로 전후를 갈랐다**) ·
> 재패닉 표시 `[recovered, repanicked]` 가 **1.25**부터(릴리스 노트 — 이 툴체인 하나로는 **판 격자를 못 돌린다**, 제3의 상태).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체는 넷째 창이다** — 「**`recover` 를 부르는 자리를 여섯 가지로 바꿔 가며, 바깥의 직접 `recover` 가 「안쪽이 멈췄나」를 대신 증언하게 하는 창**」.
`recover()` 가 `nil` 을 돌려주는 것만으로는 **「못 들었다」와 「들을 것이 없었다」가 구별되지 않는다.**
**바깥 guard 가 그 패닉을 받았는가**로 가른다((3)절).
★ 그 짝으로 「**세 프레임에 `defer` 를 심어 되감기를 로그 줄로 보는 창**」((1)절).

★★★ **`panic`·`recover`·`defer` 의 순서는 명세가 못 박았다** — 구현 사정이 아니다.
반면 **패닉 메시지의 모양**(`goroutine N [running]:`·`+0x…`·`[recovered, repanicked]`)과 **종료 코드 2** 는 **런타임(구현)** 이다. 그 선을 절마다 긋는다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | ★★★ 되감기 순서 · `recover` 가 듣는 자리 · 「직접 불렸으면 `nil` 이 아님을 보장」 · `panic(nil)` 이 런타임 패닉 |
| **표준 라이브러리·런타임** | `runtime`·`fmt`·`encoding/json`·`regexp` 가 한 것 | `runtime.Error` 타입들 · `fmt` 의 `%!v(PANIC=…)` · `GODEBUG=panicnil` · 트레이스 모양 · 종료 코드 2 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 실행 출력(재실행 대조까지) · ★ **`encoding/json` 이 v2 구현으로 빌드된다는 것**((8)절) |

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | ★★ **다른 고루틴이 터진 블록의 `goroutine N [running]:` 의 N** | 같은 바이너리가 재실행 대조에서 `7` 과 `19` 로 갈렸다 — **런타임이 매기는 고루틴 id** 다. 정규화 규칙 `goroutine \d+ \[running\]` 을 **이 칸 하나에만** 더했다 |
| **흔들린다** | 트레이스의 `panic({0x…?, 0x…?})` · `[signal … pc=0x…]` | 주소다 — 기본 정규화 규칙(주소)이 잡는다 |
| 안 흔들린다 | ★★★ **`[defer]` 로그 줄의 차례**와 **guard 가 받은 값** | 명세가 정한 순서다 — 이 주제의 핵심 근거 |
| 안 흔들린다 | `panic:` 첫 줄 문장 · 프레임 이름 · `파일:줄` · `+0x…`(짧은 오프셋) · 종료 코드 | 같은 바이너리에서 같다(재실행에서 한 글자도 같았다) |
| 안 흔들린다 | `recover()` 값의 **`%T`** | 런타임 타입 이름 — 판이 오르면 달라질 수 있다 |
| 안 흔들린다 | `encoding/json` 블록 | ★ **트레이스를 `GOTRACEBACK=none` 으로 껐다** — 표준 라이브러리 프레임의 **짧은 인자 값**(`{0x48?, 0xe0?}`)이 실행마다 흔들렸다. 안 흔들리게 만드는 쪽을 골랐다 |

★ 정규화 규칙은 **기본 넷 + 고루틴 id 하나**를 썼다.

## 한눈에 — 쉽게 말하면

**패닉은 「이 고루틴은 더 못 간다」는 비상벨이다.** 벨이 울리면 **지금 함수부터 거꾸로** 빠져나가며
각 함수가 적어 둔 **`defer` 쪽지를 처리**한다. 쪽지를 처리하던 **바로 그 사람**이 `recover()` 를 외치면 벨이 멈춘다.
**그 사람이 다른 사람에게 시켜서** 외치게 하면 — 벨은 안 멈춘다.

| 비유 | 실체 |
|---|---|
| 비상벨이 울리면 안쪽 방부터 차례로 불을 끄며 나온다 | ★★★ **되감기** — `inner` → `middle` → `outer` 의 `defer` 가 차례로 돈다 |
| 쪽지를 처리하는 **바로 그 사람**이 「멈춰」라고 외친다 | ★★★ **`defer` 된 함수 안에서 직접 부른 `recover()`** 만 듣는다 |
| 그 사람이 **도우미를 불러** 외치게 한다 | ★★★ **한 겹 더 감싸면 `nil`** — 벨은 계속 울린다((3)절) |
| **옆 건물**의 비상벨은 이 건물에서 못 끈다 | ★★ **다른 고루틴의 패닉은 못 잡는다** — 프로세스가 죽는다(종료 코드 2) |
| 벨을 끄고 **「무슨 일이 있었나」를 보고서에 적어** 낸다 | ★★ **명명 반환값으로 오류를 돌려준다**((5)절) |
| **빈 종이**로 벨을 울린다 | ★ **`panic(nil)`** — 1.20 까지는 「안 울린 것」과 구별이 안 됐다((7)절) |
| 벨을 끄고 기록한 뒤 **다시 울린다** | ★ **재패닉** — `[recovered, repanicked]` ((6)절) |
| **개업 전 점검**에서 벨이 울리면 개업을 안 한다 | ★ **`regexp.MustCompile`** — 초기화 시점의 패닉은 정당하다((9)절) |

```text
   ★★★ 되감기 — 안쪽부터 defer 가 돈다 ((1)절의 실측)

   호출 방향 ▶                                   되감기 방향 ◀
   main ─▶ outer ─▶ middle ─▶ inner                 panic("깊은 곳에서 터짐")
    │        │        │          │                        │
    │        │        │          └ [defer] inner    ◀─────┘  ①
    │        │        └ [defer] middle              ◀──────── ②
    │        └ [defer] outer                        ◀──────── ③
    └ [defer] main — recover() = 깊은 곳에서 터짐    ◀──────── ④ 여기서 멈춘다

   「여기는 안 온다」 줄은 셋 다 안 찍힌다 — 패닉 뒤의 본문은 버려진다.
   ④가 없으면(= (2)절) ③ 다음에 「panic: …」 트레이스를 찍고 종료 코드 2.
```

```text
   ★★★ recover 가 듣는 자리 — 「defer 로 불린 함수」 안에서 「직접」 ((3)절의 실측)

   defer func() { recover() }()          ✔  리터럴이 defer 로 불린 함수, 그 안에서 직접
   defer helper()   // helper 안 recover ✔  helper 자체가 defer 로 불린 함수
   defer obj.Recover()                   ✔  메서드 값도 같다
   defer func() { helper() }()           ✘  한 겹 더 — helper 는 defer 로 불린 함수가 「부른」 함수
   defer recover()                       ✘  recover 자체를 defer — 「defer 된 함수가 부른」 것이 아니다
   본문에서 recover()                     ✘  defer 가 아니다

   ✘ 인 자리의 recover() 는 nil 을 주고, 패닉은 계속 위로 간다.
```

> **패닉(panicking)** — 명세의 낱말. `panic` 호출이나 런타임 오류로 함수가 끝나고, `defer` 를 돌며 호출자 쪽으로 거슬러 가는 **종료 순서**.

> **`recover`** — 패닉 중인 고루틴의 패닉 값을 받아 **되감기를 멈추는** 내장 함수. ★ **`defer` 로 불린 함수 안에서 직접** 불려야만 듣는다.

> **`runtime.Error`** — 런타임이 내는 패닉 값(인덱스 범위·`nil` 역참조 등)이 구현하는 인터페이스. `RuntimeError()` 메서드가 표식이다.

- [26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/)가 **이 주제의 직접 선행**이다 — **한 사슬**이다.
  거기서 결론난 것 — `defer` 의 **LIFO**, `return` 뒤에 **명명 반환값을 고칠 수 있다**, ★ **패닉 중에도 `defer` 가 돈다**((2)절의 `nil` 함수).
  여기는 그 위에서 「**누가 멈추나**」를 본다.
- [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/) (4)절 — ★★★ **`fmt` 는 `nil` 리시버의 `Error()` 를 부르고, 터지면 `recover()` 아래 `catchPanic` 이 `<nil>` 로 바꿔 찍는다.**
  「**로그의 `<nil>` 은 삼켜진 패닉일 수 있다**」 — **표준 라이브러리가 `recover` 를 쓰는 실제 자리**다. 여기서는 그 **`nil` 이 아닌 쪽**을 던진다((8)절).
- Rust 와 다른 점 — ★★ Rust 의 `catch_unwind` 는 **패닉을 값(`Result`)으로 받는 함수**이고 **클로저 하나를 감싼다.**
  Go 의 `recover` 는 **「어디서 불렀나」라는 자리의 규칙**이다. Rust 갈래 [23번](../../../rust/syntax/23-panic-vs-result/) (6)절이
  「잡을 수는 있다. 그러나 **예외 처리가 아니다** — FFI 경계와 스레드 풀·테스트 하네스뿐」이라 적었다 — **쓰는 자리의 판단은 같다.**
  ★ 종료 코드가 다르다 — Rust 는 **101**, Go 는 **2**.
- 자바와 다른 점 — 자바의 `finally` 는 **블록**에 붙고 `catch` 가 **타입**으로 가른다([`../../../java/syntax/25-exceptions/`](../../../java/syntax/25-exceptions/) (4)절).
  Go 에는 **타입으로 가르는 문법이 없다** — `recover()` 는 `any` 를 주고, 가르려면 **단언**한다((4)절).

## 이 주제가 답하려는 질문

1. **패닉은 스택을 어떻게 푸나** — 어느 `defer` 가 어느 차례로 도나.
2. **`recover` 는 어디서만 듣나** — 한 겹 더 감싸면? 다른 고루틴이면?
3. **라이브러리 경계에서 패닉을 오류로 바꿀까** — 표준은 어떻게 하나, 언제 패닉이 맞나.

★ **콜 스택과 되감기 일반**(프레임·스택 포인터·예외 테이블)은
[`systems/call-stack/`](../../../../../systems/call-stack/)이 정본이다 — **그쪽은 스택이 무엇이고 어떻게 쌓이나까지**,
여기는 **Go 의 `defer`/`recover` 가 그 위에서 도는 순서부터.**

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★ **프레임마다 `defer` 를 심어 로그** | 되감기의 **차례** | [26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/)의 `defer` 로그 창 |
| ★★★ **`recover` 자리 여섯 + 바깥 guard 의 증언** | **누가 멈췄나** | ★ 본체 창 — 이 주제의 넷째 창 |
| ★★ **`recover()` 값의 `%T` 와 `runtime.Error` 단언** | 런타임 패닉이 **어떤 값**인가 | [22번 주제](../22-type-assertion-any-and-comparable/)의 단언 창 |
| ★★ **`go.mod` 판 격자 · `GODEBUG`** | `panic(nil)` 의 **1.21 경계** | [13번 주제](../13-closures-variable-capture-and-loop-variable-change/) (3)절의 판 격자 |
| ★★ **`GOEXPERIMENT` 격자** | `encoding/json` 이 **어느 구현으로** 빌드됐나 | ★ 이 주제에서 새로 필요해졌다((8)절) |
| **패닉 트레이스 전문** | 종료 코드 2 · 프레임 | [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/)에서 쓰던 창 |
| **부적용 — 벤치마크** | 안 쟀다. 「`recover` 는 비싸다」·「`defer` 가 있으면 느리다」를 이 문서는 말하지 않는다 | — |
| **부적용 — `go vet`** | **잴 것이 없다.** 이 주제의 실수(한 겹 감싼 `recover`·`defer recover()`)를 보는 분석기가 **기본 목록에 없다** — [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/) (6)절이 목록을 찍었다 | — |

★★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.**
「이 `recover()` 가 **패닉을 멈췄나**」는 `recover()` 의 반환값으로는 못 묻는다 — `nil` 이면 **못 들은 것인지 패닉이 없었던 것인지** 모른다.
그래서 **바깥에 직접 `recover` 하는 guard 를 두고, guard 가 받은 값으로** 물었다((3)절).
★ 바꾼 창의 한계 — guard 가 있으면 **프로세스가 안 죽는다.** 「한 겹 더 감싸면 **정말로 죽는가**」는 guard 없는 블록(`t27c2`)으로 따로 보였다.

### (1) ★★★ 되감기를 `defer` 로그로 — 안쪽부터 돈다

**언제 쓰나** — 패닉이 여러 프레임을 지날 때 **무엇이 정리되나**를 알고 싶을 때.

```text
===== 소스: t27a.go =====
package main

import (
	"fmt"
	"os"
)

func say(s string) { fmt.Fprintln(os.Stderr, s) }

func inner() {
	defer say("  [defer] inner")
	say("  inner  : 패닉을 던진다")
	panic("깊은 곳에서 터짐")
}

func middle() {
	defer say("  [defer] middle")
	inner()
	say("  middle : 여기는 안 온다")
}

func outer() {
	defer say("  [defer] outer")
	middle()
	say("  outer  : 여기는 안 온다")
}

func main() {
	defer func() {
		say(fmt.Sprintf("  [defer] main — recover() = %v", recover()))
	}()
	say("  main   : outer() 를 부른다")
	outer()
	say("  main   : 여기는 안 온다")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
  main   : outer() 를 부른다
  inner  : 패닉을 던진다
  [defer] inner
  [defer] middle
  [defer] outer
  [defer] main — recover() = 깊은 곳에서 터짐
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`[defer] inner` → `middle` → `outer` → `main`** — 호출의 **역순**이다. 패닉이 난 함수부터 거슬러 간다.
- ★★ **「여기는 안 온다」 셋이 전부 안 찍혔다** — 패닉 뒤의 본문은 **실행되지 않는다.** 되감는 동안 도는 것은 **`defer` 뿐**이다.
- ★★★ **main 의 `defer` 에서 `recover()` 가 패닉 값을 받았고, 종료 코드가 0** 이다 — 거기서 멈췄다.
- ★ 명세가 그 순서를 그대로 적는다 — 「**Any functions deferred by F are then executed as usual. Next, any deferred functions run by F's caller are run, and so on up to any deferred by the top-level function**」.

```text
===== 명령: sed -n "7917,7958p" "$(go env GOROOT)/doc/go_spec.html" | sed -e "s/<[^>]*>//g" =====
While executing a function F,
an explicit call to panic or a run-time panic
terminates the execution of F.
Any functions deferred by F
are then executed as usual.
Next, any deferred functions run by F's caller are run,
and so on up to any deferred by the top-level function in the executing goroutine.
At that point, the program is terminated and the error
condition is reported, including the value of the argument to panic.
This termination sequence is called panicking.



panic(42)
panic("unreachable")
panic(Error("cannot parse"))



The recover function allows a program to manage behavior
of a panicking goroutine.
Suppose a function G defers a function D that calls
recover and a panic occurs in a function on the same goroutine in which G
is executing.
When the running of deferred functions reaches D,
the return value of D's call to recover will be the value passed to the call of panic.
If D returns normally, without starting a new
panic, the panicking sequence stops. In that case,
the state of functions called between G and the call to panic
is discarded, and normal execution resumes.
Any functions deferred by G before D are then run and G's
execution terminates by returning to its caller.



The return value of recover is nil when the
goroutine is not panicking or recover was not called directly by a deferred function.
Conversely, if a goroutine is panicking and recover was called directly by a deferred function,
the return value of recover is guaranteed not to be nil.
To ensure this, calling panic with a nil interface value (or an untyped nil)
causes a run-time panic.
(exit 0)
```

  ★★★ 둘째 문단이 이 주제의 급소다 — 「**The return value of recover is nil when the goroutine is not panicking or recover was not called directly by a deferred function.**」
  그리고 그 반대 — 「**if a goroutine is panicking and recover was called directly by a deferred function, the return value of recover is guaranteed not to be nil. To ensure this, calling panic with a nil interface value … causes a run-time panic.**」 — (7)절이 그 판 경계를 던진다.

비용 — 없다(재지 않았다).

### (2) ★★ 아무도 안 받으면 — `defer` 를 다 돌리고 죽는다

**언제 쓰나** — 트레이스를 읽을 때. **`defer` 가 먼저 돌고 메시지가 나중**이다.

```text
===== 소스: t27b.go =====
package main

import (
	"fmt"
	"os"
)

func say(s string) { fmt.Fprintln(os.Stderr, s) }

func g() {
	defer say("  [defer] g")
	panic("아무도 안 받는 패닉")
}

func f() {
	defer say("  [defer] f")
	g()
}

func main() {
	defer say("  [defer] main")
	f()
}
===== 명령: go build -trimpath -o prog . && ./prog =====
  [defer] g
  [defer] f
  [defer] main
panic: 아무도 안 받는 패닉

goroutine 1 [running]:
main.g()
	ex/t27b.go:12 +0x3e
main.f()
	ex/t27b.go:17 +0x30
main.main()
	ex/t27b.go:22 +0x30
(exit 2)
```

그림 해설 (한 단계씩):

- ★★★ **`[defer] g` → `f` → `main` 이 먼저 찍히고, 그다음에 `panic:`** 이다 —
  명세 「**At that point, the program is terminated and the error condition is reported**」의 「At that point」가 **모든 `defer` 를 돈 뒤**라는 뜻이다.
- ★★ **종료 코드 2** — 이것은 **명세가 아니라 런타임**이다(명세는 「terminated」만 말한다). `go doc builtin.panic` 은 「**non-zero exit code**」라고만 적는다.

```text
===== 명령: go doc builtin.panic =====
package builtin // import "builtin"

func panic(v any)
    The panic built-in function stops normal execution of the current goroutine.
    When a function F calls panic, normal execution of F stops immediately.
    Any functions whose execution was deferred by F are run in the usual way,
    and then F returns to its caller. To the caller G, the invocation of F then
    behaves like a call to panic, terminating G's execution and running any
    deferred functions. This continues until all functions in the executing
    goroutine have stopped, in reverse order. At that point, the program is
    terminated with a non-zero exit code. This termination sequence is called
    panicking and can be controlled by the built-in function recover.

    Starting in Go 1.21, calling panic with a nil interface value or an untyped
    nil causes a run-time error (a different panic). The GODEBUG setting
    panicnil=1 disables the run-time error.
(exit 0)
```

- ★ 트레이스의 `goroutine 1 [running]:` 아래 **프레임이 안쪽부터**(`main.g` → `main.f` → `main.main`) 찍힌다 — 각 줄의 `+0x3e` 는 함수 안 오프셋이다.
- ★ **마커를 전부 `stderr` 로** 찍었다 — 패닉 메시지도 `stderr` 라 **한 흐름**이 되어 순서가 흔들리지 않는다(규칙 18).

비용 — 없다.

### (3) ★★★ `recover` 가 듣는 자리 — 여섯 판을 던진다

**언제 쓰나** — `recover` 를 **도우미 함수로 빼고 싶을 때**. 이 주제의 급소다.

```text
===== 소스: t27c.go =====
package main

import (
	"fmt"
	"os"
)

func say(format string, a ...any) { fmt.Fprintf(os.Stderr, format+"\n", a...) }

// helper 는 recover 를 부르는 도우미다.
func helper() { say("    helper 안의 recover() = %v", recover()) }

type guardObj struct{}

func (guardObj) Recover() { say("    메서드 안의 recover() = %v", recover()) }

// 판 1 — defer 된 함수 리터럴 안에서 직접 부른다
func direct() {
	defer func() { say("    리터럴 안의 recover() = %v", recover()) }()
	panic("P1")
}

// 판 2 — defer 된 함수 리터럴이 helper 를 부른다(한 겹 더)
func wrapped() {
	defer func() { helper() }()
	panic("P2")
}

// 판 3 — helper 자체를 defer 한다
func deferHelper() {
	defer helper()
	panic("P3")
}

// 판 4 — 메서드 값을 defer 한다
func deferMethod() {
	defer guardObj{}.Recover()
	panic("P4")
}

// 판 5 — recover 자체를 defer 한다
func deferRecover() {
	defer recover()
	panic("P5")
}

// 판 6 — defer 가 아닌 자리에서 부른다
func notDeferred() {
	say("    본문의 recover() = %v", recover())
	panic("P6")
}

// guard 는 바깥에서 직접 recover 해 「안쪽이 멈췄나」를 본다.
func guard(name string, f func()) {
	defer func() { say("  %-14s -> 바깥 guard 가 받은 것 = %v", name, recover()) }()
	say("  %s", name)
	f()
}

func main() {
	guard("판1 직접", direct)
	guard("판2 한 겹 더", wrapped)
	guard("판3 defer helper", deferHelper)
	guard("판4 defer 메서드", deferMethod)
	guard("판5 defer recover()", deferRecover)
	guard("판6 defer 아님", notDeferred)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
  판1 직접
    리터럴 안의 recover() = P1
  판1 직접          -> 바깥 guard 가 받은 것 = <nil>
  판2 한 겹 더
    helper 안의 recover() = <nil>
  판2 한 겹 더       -> 바깥 guard 가 받은 것 = P2
  판3 defer helper
    helper 안의 recover() = P3
  판3 defer helper -> 바깥 guard 가 받은 것 = <nil>
  판4 defer 메서드
    메서드 안의 recover() = P4
  판4 defer 메서드   -> 바깥 guard 가 받은 것 = <nil>
  판5 defer recover()
  판5 defer recover() -> 바깥 guard 가 받은 것 = P5
  판6 defer 아님
    본문의 recover() = <nil>
  판6 defer 아님    -> 바깥 guard 가 받은 것 = P6
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **판1 — 리터럴 안에서 직접**: `P1` 을 받았고 **guard 는 `<nil>`** — 안쪽이 멈췄다.
- ★★★ **판2 — 한 겹 더**: `helper 안의 recover() = <nil>` 이고 **guard 가 `P2` 를 받았다** — **안쪽은 못 멈췄다.**
  `helper` 는 「`defer` 로 불린 함수(리터럴)가 **부른** 함수」라 명세의 「**called directly by a deferred function**」이 아니다.
- ★★★ **판3 — `defer helper()`**: 같은 `helper` 인데 **`P3` 를 받았다.** 이번에는 **`helper` 자체가 `defer` 로 불린 함수**다.
  ★ **도우미로 빼는 것은 된다 — `defer helper()` 로 걸면.** 안 되는 것은 **리터럴 안에서 부르는 것**이다.
- ★★ **판4 — `defer guardObj{}.Recover()`**: 메서드 값도 판3 과 같다 — 받았다.
- ★★★ **판5 — `defer recover()`**: 한 줄도 안 찍히고 **guard 가 `P5` 를 받았다.** `recover` 가 **`defer` 된 함수 그 자체**라
  「`defer` 된 함수가 **부른**」 것이 아니다. `go doc builtin.recover` 가 「**inside a deferred function (but not any function called by it)**」라 적는다.
- ★ **판6 — 본문에서**: `<nil>` — 패닉 전이라 **패닉 중이 아니다.** guard 가 `P6` 를 받았다.

```text
===== 명령: go doc builtin.recover =====
package builtin // import "builtin"

func recover() any
    The recover built-in function allows a program to manage behavior of
    a panicking goroutine. Executing a call to recover inside a deferred
    function (but not any function called by it) stops the panicking sequence
    by restoring normal execution and retrieves the error value passed to the
    call of panic. If recover is called outside the deferred function it will
    not stop a panicking sequence. In this case, or when the goroutine is not
    panicking, recover returns nil.

    Prior to Go 1.21, recover would also return nil if panic is called with a
    nil argument. See [panic] for details.
(exit 0)
```

**guard 가 없으면 — 정말로 죽는다**

```text
===== 소스: t27c2.go =====
package main

import (
	"fmt"
	"os"
)

func helper() { fmt.Fprintln(os.Stderr, "  helper 안의 recover() =", recover()) }

func main() {
	defer func() { helper() }() // 한 겹 더 감쌌다 — 바깥 guard 가 없다
	panic("한 겹 더 감싼 recover 는 못 듣는다")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
  helper 안의 recover() = <nil>
panic: 한 겹 더 감싼 recover 는 못 듣는다

goroutine 1 [running]:
main.main()
	ex/t27c2.go:12 +0x3e
(exit 2)
```

- ★★★ **`helper 안의 recover() = <nil>` 을 찍고 그대로 `panic:` 과 종료 코드 2** 다. **한 겹 더 감싼 `recover` 는 프로세스를 못 살린다.**

비용 — 없다.

### (4) ★★ 다른 고루틴의 패닉은 못 잡는다 · 런타임 패닉의 타입

**언제 쓰나** — `main` 에 `recover` 를 두면 **모든 패닉이 잡히리라** 생각할 때.

```text
===== 소스: t27d.go =====
package main

import (
	"fmt"
	"os"
)

func main() {
	defer func() {
		fmt.Fprintln(os.Stderr, "  [defer] main 의 recover() =", recover())
	}()
	done := make(chan struct{})
	go func() {
		fmt.Fprintln(os.Stderr, "  고루틴: 터진다")
		panic("다른 고루틴의 패닉")
	}()
	<-done // 영원히 기다린다 — 그 전에 프로세스가 끝난다
}
===== 명령: go build -trimpath -o prog . && ./prog =====
  고루틴: 터진다
panic: 다른 고루틴의 패닉

goroutine 19 [running]:
main.main.func2()
	ex/t27d.go:15 +0x58
created by main.main in goroutine 1
	ex/t27d.go:13 +0x4a
(exit 2)
```

그림 해설 (한 단계씩):

- ★★★ **main 의 `[defer]` 줄이 없다** — main 의 `recover` 는 **돌 기회조차 없었다.** 종료 코드 **2**.
  명세의 「**a panic occurs in a function on the same goroutine**」 — `recover` 는 **같은 고루틴**의 패닉만 본다.
  그리고 되감기가 **그 고루틴의 맨 위**(`main.main.func2`)에 닿으면 프로그램 전체가 끝난다.
- ★★ **`created by main.main in goroutine 1`** — 트레이스가 그 고루틴을 **누가 만들었나**까지 찍는다.
- ★★ **`goroutine N` 의 N 은 흔들린다**(같은 바이너리가 `7` 과 `19` 로 갈렸다) — 머리말의 유일한 비기본 정규화 칸이다.
- ★ 그래서 **고루틴마다 자기 `recover`** 를 둔다. [28번 주제](../28-goroutines-go-statement-cost-and-termination/)의 `sync.WaitGroup.Go` 문서가 「**The function f must not panic.**」이라 적는 것도 같은 사정이다.

**런타임 패닉은 무엇인가 — `recover` 로 받아 `%T`**

```text
===== 소스: t27f.go =====
package main

import (
	"errors"
	"fmt"
	"runtime"
)

// try 는 f 의 패닉 값을 받아 타입과 runtime.Error 여부를 찍는다.
func try(name string, f func()) {
	defer func() {
		r := recover()
		_, isRT := r.(runtime.Error)
		fmt.Printf("%-8s %%T=%-28T runtime.Error=%-5v : %v\n", name, r, isRT, r)
	}()
	f()
}

func main() {
	var s []int
	var m map[string]int
	var p *struct{ x int }
	var a any = "x"
	z := 0
	try("index", func() { _ = s[3] })
	try("nilmap", func() { m["a"] = 1 })
	try("nilptr", func() { _ = p.x })
	try("div", func() { _ = 1 / z })
	try("assert", func() { _ = a.(int) })
	try("close2", func() { c := make(chan int); close(c); close(c) })
	try("string", func() { panic("내가 던진 문자열") })
	try("error", func() { panic(errors.New("내가 던진 오류")) })
}
===== 명령: go build -trimpath -o prog . && ./prog =====
index    %T=runtime.boundsError          runtime.Error=true  : runtime error: index out of range [3] with length 0
nilmap   %T=runtime.plainError           runtime.Error=true  : assignment to entry in nil map
nilptr   %T=runtime.errorString          runtime.Error=true  : runtime error: invalid memory address or nil pointer dereference
div      %T=runtime.errorString          runtime.Error=true  : runtime error: integer divide by zero
assert   %T=*runtime.TypeAssertionError  runtime.Error=true  : interface conversion: interface {} is string, not int
close2   %T=runtime.plainError           runtime.Error=true  : close of closed channel
string   %T=string                       runtime.Error=false : 내가 던진 문자열
error    %T=*errors.errorString          runtime.Error=false : 내가 던진 오류
(exit 0)
```

- ★★★ **런타임이 낸 여섯이 전부 `runtime.Error` 를 구현한다** — 그런데 **구체 타입은 넷으로 갈린다**:
  인덱스는 **`runtime.boundsError`**, `nil` 맵 쓰기와 닫힌 채널 닫기는 **`runtime.plainError`**,
  `nil` 역참조와 0 나누기는 **`runtime.errorString`**, 단언 실패는 **`*runtime.TypeAssertionError`**.
- ★★ **내가 던진 문자열·오류는 `runtime.Error` 가 아니다** — `%T=string` · `*errors.errorString`.
  ★ 그래서 `recover` 뒤 **「런타임 버그인가, 의도한 패닉인가」를 `runtime.Error` 단언으로 가를 수 있다.**
- ★ 구체 타입 이름(`boundsError` 등)은 **공개되지 않은 구현**이다 — 기대는 것은 `runtime.Error` 인터페이스까지.

비용 — 없다.

### (5) ★★ `recover()` 뒤의 반환값 — 명명 반환값으로 오류를 돌려준다

**언제 쓰나** — 패닉을 **오류로 바꿔** 호출자에게 돌려줄 때.

```text
===== 소스: t27e.go =====
package main

import "fmt"

// safeDiv — 명명 반환값이 있어 defer 가 오류를 돌려줄 수 있다.
func safeDiv(a, b int) (q int, err error) {
	defer func() {
		if r := recover(); r != nil {
			err = fmt.Errorf("safeDiv(%d, %d): %v", a, b, r)
		}
	}()
	return a / b, nil
}

// lostDiv — 이름이 없다. defer 가 고친 err 는 지역 변수일 뿐이다.
func lostDiv(a, b int) (int, error) {
	var err error
	defer func() {
		if r := recover(); r != nil {
			err = fmt.Errorf("lostDiv(%d, %d): %v", a, b, r)
		}
	}()
	return a / b, err
}

func main() {
	q, err := safeDiv(7, 2)
	fmt.Printf("safeDiv(7, 2) = %d, %v\n", q, err)
	q, err = safeDiv(7, 0)
	fmt.Printf("safeDiv(7, 0) = %d, %v\n", q, err)
	q, err = lostDiv(7, 0)
	fmt.Printf("lostDiv(7, 0) = %d, %v   <- 패닉이 조용히 사라졌다\n", q, err)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
safeDiv(7, 2) = 3, <nil>
safeDiv(7, 0) = 0, safeDiv(7, 0): runtime error: integer divide by zero
lostDiv(7, 0) = 0, <nil>   <- 패닉이 조용히 사라졌다
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`safeDiv(7, 0)` 은 `0, safeDiv(7, 0): runtime error: integer divide by zero`** — `defer` 안에서 **명명 반환값 `err` 에 썼다.**
  패닉으로 나가는 경로에는 **`return` 문이 없다** — 결과 칸에 직접 쓰는 것이 유일한 길이다.
  `q` 는 **제로값 0** 이다(`return a / b` 가 끝까지 못 갔으니 아무도 안 채웠다).
- ★★★ **`lostDiv(7, 0)` 은 `0, <nil>`** — 이름이 없어 `defer` 가 고친 `err` 는 **지역 변수**일 뿐이다.
  **패닉은 멈췄는데 오류는 안 나갔다** — 가장 나쁜 조합, **조용히 삼켜진 패닉**이다.
- ★ 관용구의 정본은 [12번 주제](../12-functions-multiple-returns-named-results-and-variadics/) (2)절의 `recovered()` — 여기는 **이름이 없을 때 삼켜지는 쪽**을 보탰다.

비용 — 없다.

### (6) ★ 재패닉 — 받아서 기록하고 다시 던진다

**언제 쓰나** — 「로그는 남기되 처리는 위에 맡긴다」를 할 때.

```text
===== 소스: t27h.go =====
package main

import (
	"fmt"
	"os"
)

func main() {
	defer func() {
		r := recover()
		fmt.Fprintln(os.Stderr, "  [defer] 받아서 기록하고 같은 값을 다시 던진다 :", r)
		panic(r)
	}()
	panic("처음 패닉")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
  [defer] 받아서 기록하고 같은 값을 다시 던진다 : 처음 패닉
panic: 처음 패닉 [recovered, repanicked]

goroutine 1 [running]:
main.main.func1()
	ex/t27h.go:12 +0x6d
panic({0x557148?, 0x4a3960?})
	runtime/panic.go:859 +0x125
main.main()
	ex/t27h.go:14 +0x3e
(exit 2)
```

그림 해설 (한 단계씩):

- ★★ **`panic: 처음 패닉 [recovered, repanicked]`** — 같은 값을 다시 던지면 런타임이 **한 줄로 합쳐** 찍는다.
  ★ **1.25 부터의 표시**다 — 릴리스 노트가 「Previously … would print: `panic: PANIC [recovered]` / `panic: PANIC`」라고 **예전 두 줄 모양**을 싣는다.
  **이 툴체인은 1.27 하나라 그 전후를 판 격자로 못 돌렸다** — 제3의 상태(못 잰 것)로 적는다.
  ★ `go.mod` 를 `go 1.24` 로 낮춰 던져 봤다 — **그래도 `[recovered, repanicked]`** 다. 트레이스 모양은 **모듈의 언어 판이 아니라 런타임 판**이 정한다.

```text
===== 소스: go.mod =====
module ex

go 1.24
===== 소스: t27h.go =====
package main

import (
	"fmt"
	"os"
)

func main() {
	defer func() {
		r := recover()
		fmt.Fprintln(os.Stderr, "  [defer] 받아서 기록하고 같은 값을 다시 던진다 :", r)
		panic(r)
	}()
	panic("처음 패닉")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
  [defer] 받아서 기록하고 같은 값을 다시 던진다 : 처음 패닉
panic: 처음 패닉 [recovered, repanicked]

goroutine 1 [running]:
main.main.func1()
	ex/t27h.go:12 +0x6d
panic({0x5572e8?, 0x4a3960?})
	runtime/panic.go:859 +0x125
main.main()
	ex/t27h.go:14 +0x3e
(exit 2)
```

- ★ 트레이스에 **`panic(…)` 프레임이 두 번** 나온다 — 처음 던진 자리와 다시 던진 자리.

**다른 값으로 던지거나, 되감는 도중에 또 터지면**

```text
===== 소스: t27h2.go =====
package main

import (
	"fmt"
	"os"
)

func main() {
	defer func() {
		r := recover()
		fmt.Fprintln(os.Stderr, "  [defer ②] 받은 것 :", r)
		panic(fmt.Sprintf("문맥을 붙여 새로 던진다(%v)", r))
	}()
	defer func() {
		panic("defer ① 안에서 또 터짐") // 되감는 도중에 새 패닉
	}()
	panic("처음 패닉")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
  [defer ②] 받은 것 : defer ① 안에서 또 터짐
panic: 처음 패닉
	panic: defer ① 안에서 또 터짐 [recovered]
	panic: 문맥을 붙여 새로 던진다(defer ① 안에서 또 터짐)

goroutine 1 [running]:
main.main.func1()
	ex/t27h2.go:12 +0xaa
panic({0x55a0d8?, 0x4a5998?})
	runtime/panic.go:859 +0x125
main.main.func2()
	ex/t27h2.go:15 +0x25
panic({0x55a0d8?, 0x4a5978?})
	runtime/panic.go:859 +0x125
main.main()
	ex/t27h2.go:17 +0x4e
(exit 2)
```

- ★★★ **줄이 셋**이다 — `panic: 처음 패닉` · `panic: defer ① 안에서 또 터짐 [recovered]` · `panic: 문맥을 붙여 새로 던진다(…)`.
  런타임이 **패닉 사슬 전체**를 찍는다. 받은 것은 **가장 최근 패닉(①)** 이다 — `[defer ②] 받은 것 : defer ① 안에서 또 터짐`.
- ★★ **되감는 도중의 새 패닉이 앞의 패닉을 덮는다** — `recover` 가 받는 것은 **가장 최근 것 하나**다.
  ★ 첫 패닉(`처음 패닉`)은 **값으로는 사라지고 메시지에만** 남았다.

비용 — 없다.

### (7) ★★★ `panic(nil)` — 1.21 판 경계를 `go.mod` 로 가른다

**언제 쓰나** — `panic(err)` 인데 `err` 가 `nil` 일 수 있을 때. **같은 소스를 `go.mod` 의 `go` 줄만 바꿔** 세 판 던졌다.

```text
===== 소스: go.mod =====
module ex

go 1.20
===== 소스: t27g.go =====
package main

import (
	"fmt"
	"runtime"
)

func main() {
	defer func() {
		r := recover()
		fmt.Printf("  recover() = %v\n  %%T        = %T\n  r == nil  : %v\n", r, r, r == nil)
		if e, ok := r.(runtime.Error); ok {
			fmt.Println("  runtime.Error :", e.Error())
		}
	}()
	panic(nil)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
  recover() = <nil>
  %T        = <nil>
  r == nil  : true
(exit 0)
```

```text
===== 소스: go.mod =====
module ex

go 1.21
===== 소스: t27g.go =====
package main

import (
	"fmt"
	"runtime"
)

func main() {
	defer func() {
		r := recover()
		fmt.Printf("  recover() = %v\n  %%T        = %T\n  r == nil  : %v\n", r, r, r == nil)
		if e, ok := r.(runtime.Error); ok {
			fmt.Println("  runtime.Error :", e.Error())
		}
	}()
	panic(nil)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
  recover() = runtime error: panic called with nil argument
  %T        = *runtime.PanicNilError
  r == nil  : false
  runtime.Error : runtime error: panic called with nil argument
(exit 0)
```

```text
===== 소스: go.mod =====
module ex

go 1.27
===== 소스: t27g.go =====
package main

import (
	"fmt"
	"runtime"
)

func main() {
	defer func() {
		r := recover()
		fmt.Printf("  recover() = %v\n  %%T        = %T\n  r == nil  : %v\n", r, r, r == nil)
		if e, ok := r.(runtime.Error); ok {
			fmt.Println("  runtime.Error :", e.Error())
		}
	}()
	panic(nil)
}
===== 명령: go build -trimpath -o prog . && GODEBUG=panicnil=1 ./prog =====
  recover() = <nil>
  %T        = <nil>
  r == nil  : true
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`go 1.20` — `recover() = <nil>`, `r == nil : true`.** 패닉이 **있었는데** `recover` 가 `nil` 을 준다 —
  **「패닉이 없었다」와 구별이 안 된다.** (1)절 명세의 「**guaranteed not to be nil**」이 깨진다.
- ★★★ **`go 1.21` — `*runtime.PanicNilError`**, 문구 `runtime error: panic called with nil argument`, **`runtime.Error` 를 구현한다.**
  ★ 명세가 「**calling panic with a nil interface value … causes a run-time panic**」으로 **보장을 지키려고 규칙을 바꾼 것**이다.
- ★★ **`go 1.27` + `GODEBUG=panicnil=1`** — 다시 `<nil>`. 판 경계가 **`GODEBUG` 한 칸**이다.
- ★★★ **소스·툴체인·빌드 명령이 같고 `go.mod` 한 줄만 다르다** — 차이는 컴파일러 판이 아니라 「**모듈이 선언한 언어 판**」이다.
  그 기제가 `godebug.md` 에 적혀 있다.

```text
===== 명령: sed -n "75,86p" "$(go env GOROOT)/doc/godebug.md" =====
For example, Go 1.21 introduces the `panicnil` setting,
controlling whether `panic(nil)` is allowed;
it defaults to `panicnil=0`, making `panic(nil)` a run-time error.
Using `panicnil=1` restores the behavior of Go 1.20 and earlier.

When compiling a work module or workspace that declares
an older Go version, the Go toolchain amends its defaults
to match that older Go version as closely as possible.
For example, when a Go 1.21 toolchain compiles a program,
if the work module's `go.mod` or the workspace's `go.work`
says `go` `1.20`, then the program defaults to `panicnil=1`,
matching Go 1.20 instead of Go 1.21.
(exit 0)
```

  ★★ 「**if the work module's go.mod … says go 1.20, then the program defaults to panicnil=1**」 — `go.mod` 의 `go` 줄이 **GODEBUG 기본값**을 정한다.
  ★ [13번 주제](../13-closures-variable-capture-and-loop-variable-change/)의 루프 변수(1.22)는 **컴파일러의 `-lang`** 이 정하고, 여기는 **런타임의 GODEBUG** 가 정한다 — **같은 `go` 줄, 다른 기제**다.

비용 — 없다.

### (8) ★★ 라이브러리 경계 — 표준은 패닉을 어떻게 다루나

**언제 쓰나** — 내 라이브러리가 **남의 코드(콜백·메서드)를 부를 때**. 그쪽이 터지면 어쩔 것인가.

```text
===== 소스: t27i.go =====
package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
)

type Loud struct{}

func (Loud) String() string { panic("내 String 이 터짐") }

type Bad struct{}

func (Bad) MarshalJSON() ([]byte, error) { return nil, errors.New("내가 돌려준 오류") }

type Boom struct{}

func (Boom) MarshalJSON() ([]byte, error) { panic("내 MarshalJSON 이 터짐") }

func say(format string, a ...any) { fmt.Fprintf(os.Stderr, format+"\n", a...) }

func main() {
	say("-- fmt: String() 의 패닉을 글자로 바꿔 찍는다 --")
	say("  %%v -> %v", Loud{})
	say("  %%s -> %s", Loud{})

	say("-- json: 내가 오류로 돌려준 것은 오류가 된다 --")
	_, err := json.Marshal(Bad{})
	say("  err = %v", err)

	say("-- json: 내 패닉은 오류로 안 바꾸고 다시 던진다 --")
	_, err = json.Marshal(Boom{})
	say("  여기는 안 온다 %v", err)
}
===== 명령: go build -trimpath -o prog . && GOTRACEBACK=none ./prog =====
-- fmt: String() 의 패닉을 글자로 바꿔 찍는다 --
  %v -> %!v(PANIC=String method: 내 String 이 터짐)
  %s -> %!s(PANIC=String method: 내 String 이 터짐)
-- json: 내가 오류로 돌려준 것은 오류가 된다 --
  err = json: error calling MarshalJSON for type *main.Bad: 내가 돌려준 오류
-- json: 내 패닉은 오류로 안 바꾸고 다시 던진다 --
panic: 내 MarshalJSON 이 터짐
(exit 2)
```

그림 해설 (한 단계씩):

- ★★★ **`fmt` 는 `String()` 의 패닉을 글자로 바꿔 찍는다** — `%!v(PANIC=String method: 내 String 이 터짐)`.
  [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/) (4)절의 `catchPanic` 이 **`nil` 리시버면 `<nil>`**, **그 밖이면 이 모양**을 만든다.
  ★ **로그 한 줄이 패닉을 삼킨 흔적**이다 — 프로그램은 계속 돈다.
- ★★ **`json` 은 내가 오류로 돌려준 것은 오류로** 돌려준다 — `json: error calling MarshalJSON for type *main.Bad: …`.
- ★★★ **내 `MarshalJSON` 이 패닉하면 — 그대로 죽는다.** `panic: 내 MarshalJSON 이 터짐`, `[recovered]` 표시가 **없다** — **`json` 이 `recover` 를 안 했다.**

★★★ **예상과 달랐다 — 이 판의 `encoding/json` 은 v2 구현으로 빌드된다.**

```text
===== 명령: R="$(go env GOROOT)/src"; sed -n "5p" "$R/encoding/json/encode.go"; sed -n "5p" "$R/encoding/json/v2_encode.go"; grep -n "JSONv2:" "$R/internal/buildcfg/exp.go" =====
//go:build !goexperiment.jsonv2
//go:build goexperiment.jsonv2
87:		JSONv2:                true,
(exit 0)
```

- ★★★ **`encode.go` 는 `//go:build !goexperiment.jsonv2`**, **`v2_encode.go` 는 `goexperiment.jsonv2`** 이고
  go1.27.1 의 **기본 실험 목록에 `JSONv2: true`** 가 있다. **내가 읽던 `recover` 코드(`encode.go`)는 이 판에서 컴파일조차 안 된다.**
- ★★ 그래서 **v1 구현으로 다시 빌드**해 같은 소스를 던졌다 — `GOEXPERIMENT=nojsonv2`.

```text
===== 소스: t27i.go =====
package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
)

type Loud struct{}

func (Loud) String() string { panic("내 String 이 터짐") }

type Bad struct{}

func (Bad) MarshalJSON() ([]byte, error) { return nil, errors.New("내가 돌려준 오류") }

type Boom struct{}

func (Boom) MarshalJSON() ([]byte, error) { panic("내 MarshalJSON 이 터짐") }

func say(format string, a ...any) { fmt.Fprintf(os.Stderr, format+"\n", a...) }

func main() {
	say("-- fmt: String() 의 패닉을 글자로 바꿔 찍는다 --")
	say("  %%v -> %v", Loud{})
	say("  %%s -> %s", Loud{})

	say("-- json: 내가 오류로 돌려준 것은 오류가 된다 --")
	_, err := json.Marshal(Bad{})
	say("  err = %v", err)

	say("-- json: 내 패닉은 오류로 안 바꾸고 다시 던진다 --")
	_, err = json.Marshal(Boom{})
	say("  여기는 안 온다 %v", err)
}
===== 명령: GOEXPERIMENT=nojsonv2 go build -trimpath -o prog . && GOTRACEBACK=none ./prog =====
-- fmt: String() 의 패닉을 글자로 바꿔 찍는다 --
  %v -> %!v(PANIC=String method: 내 String 이 터짐)
  %s -> %!s(PANIC=String method: 내 String 이 터짐)
-- json: 내가 오류로 돌려준 것은 오류가 된다 --
  err = json: error calling MarshalJSON for type main.Bad: 내가 돌려준 오류
-- json: 내 패닉은 오류로 안 바꾸고 다시 던진다 --
panic: 내 MarshalJSON 이 터짐 [recovered, repanicked]
(exit 2)
```

```text
===== 명령: sed -n "327,343p" "$(go env GOROOT)/src/encoding/json/encode.go" =====
// jsonError is an error wrapper type for internal use only.
// Panics with errors are wrapped in jsonError so that the top-level recover
// can distinguish intentional panics from this package.
type jsonError struct{ error }

func (e *encodeState) marshal(v any, opts encOpts) (err error) {
	defer func() {
		if r := recover(); r != nil {
			if je, ok := r.(jsonError); ok {
				err = je.error
			} else {
				panic(r)
			}
		}
	}()
	e.reflectValue(reflect.ValueOf(v), opts)
	return nil
(exit 0)
```

- ★★★ **v1 판은 `[recovered, repanicked]`** — `json` 이 **`recover` 한 뒤 다시 던졌다.**
  소스가 그 이유를 적는다 — 「**Panics with errors are wrapped in jsonError so that the top-level recover can distinguish intentional panics from this package.**」
  ★ **`jsonError` 면(자기 패닉이면) 오류로 바꾸고, 아니면(남의 패닉이면) `panic(r)`** 이다.
- ★★ **그러니 두 판 모두 「남의 패닉을 오류로 바꾸지 않는다」는 결론은 같다.** v1 은 받아서 다시 던지고, v2 는 아예 안 받는다.
  **v1 이 `recover` 를 쓴 것은 「자기 내부 제어 흐름」용**이었지 경계 보호용이 아니었다.
- ★ 덤 — **오류 문구도 판마다 다르다**: v2 `type *main.Bad`, v1 `type main.Bad`. **문구에 기대지 마라**([25번 주제](../25-sentinel-errors-vs-custom-error-types/) (4)절).

```text
   ★★ 표준 라이브러리가 recover 를 쓰는 세 모양 (이 판의 실측)

   fmt        남의 String()/Error() 가 터지면     → 글자로 바꿔 찍고 계속 간다
              nil 리시버면 "<nil>", 아니면 "%!v(PANIC=String method: …)"
   json (v1)  자기 패닉(jsonError)이면           → 오류로 바꿔 돌려준다
              남의 패닉이면                        → panic(r) 다시 던진다   [recovered, repanicked]
   json (v2)  (go1.27.1 기본)                     → recover 하지 않는다      panic: … 그대로
```

비용 — 없다.

### (9) ★ 언제 패닉이 맞나 — `Must` 관용구

**언제 쓰나** — **프로그램이 시작하기도 전에 틀린 것**(상수 정규식·템플릿)을 만났을 때.

```text
===== 소스: t27j.go =====
package main

import (
	"fmt"
	"regexp"
)

// 패키지 변수 — main 보다 먼저 초기화된다. 틀린 패턴이면 거기서 패닉이다.
var ident = regexp.MustCompile(`^[a-z]+$`)
var broken = regexp.MustCompile(`(`)

func main() {
	fmt.Println("main 에 왔다", ident, broken)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
panic: regexp: Compile(`(`): error parsing regexp: missing closing ): `(`

goroutine 1 [running]:
regexp.MustCompile({0x4bf578, 0x1})
	regexp/regexp.go:312 +0xb4
main.init()
	ex/t27j.go:10 +0x53
(exit 2)
```

```text
===== 명령: go doc regexp.MustCompile =====
package regexp // import "regexp"

func MustCompile(str string) *Regexp
    MustCompile is like Compile but panics if the expression cannot be parsed.
    It simplifies safe initialization of global variables holding compiled
    regular expressions.
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`main 에 왔다` 가 안 찍혔다** — 패키지 변수 초기화에서 터졌다. 트레이스에 **`main.init()`** 프레임이 있다.
  첫 줄이 `error parsing regexp: missing closing )` 를 담는다 — 틀린 패턴이 **개발 중 첫 실행에서 바로** 드러난다.
- ★★ 문서가 쓰는 자리를 적는다 — 「**It simplifies safe initialization of global variables holding compiled regular expressions.**」
  패턴이 **소스에 박힌 상수**라면 그것이 틀린 것은 **실행 중의 실패가 아니라 프로그래머의 버그**다 — 그때는 패닉이 맞다.
- ★ **입력으로 들어온 패턴에 `MustCompile` 을 쓰면 안 된다** — 그건 **실행 중의 실패**이고 `regexp.Compile` 의 오류로 다룬다.

비용 — 없다.

## 문법 — 형태와 규칙

### 형태

```go
// t27form.go
package main

import (
	"errors"
	"fmt"
)

// Parse 는 라이브러리 경계다 — 안에서 난 패닉을 오류로 바꿔 내보낸다.
func Parse(s string) (n int, err error) {
	defer func() {
		if r := recover(); r != nil {
			err = fmt.Errorf("Parse(%q): %v", s, r)
		}
	}()
	return parse(s), nil
}

func parse(s string) int {
	if s == "" {
		panic(errors.New("빈 입력"))
	}
	return len(s)
}

func main() {
	fmt.Println(Parse("abc"))
	fmt.Println(Parse(""))
}
```

```text
===== 명령: go build -trimpath -o prog . && ./prog =====
3 <nil>
0 Parse(""): 빈 입력
(exit 0)
```

규칙 불릿.

- **`panic(v)`** — `v` 는 `any`. 현재 함수를 끝내고 **`defer` 를 돌며 호출자 쪽으로** 거슬러 간다.
- **`recover()`** — **`defer` 로 불린 함수 안에서 직접** 부를 때만 패닉 값을 받고 되감기를 멈춘다. 그 밖에서는 `nil`.
- **`defer helper()` 는 되고 `defer func(){ helper() }()` 는 안 된다.** `defer recover()` 도 안 된다.
- **`recover` 는 같은 고루틴의 패닉만** 본다. 다른 고루틴이 터지면 **프로세스가 끝난다**(종료 코드 2 — 런타임).
- **패닉을 오류로 바꾸려면 명명 반환값**에 쓴다.
- **`panic(nil)`** 은 1.21 부터 `*runtime.PanicNilError`. `go.mod` 가 `go 1.20` 이하거나 `GODEBUG=panicnil=1` 이면 예전 동작.
- **런타임 패닉 값은 `runtime.Error`** 를 구현한다 — 의도한 패닉과 가를 때 쓴다.

### 금지 사례 — 아무도 안 막는 것

★★ **컴파일러가 거부하는 것이 없다** — 이 주제의 실수는 전부 **자리의 규칙**이라 타입 검사에 안 걸린다.

| 쓴 꼴 | 누가 | 결과 |
|---|---|---|
| `defer func(){ helper() }()` 에서 `helper` 가 `recover` | ★★★ **아무도** | `recover()` 가 `nil`, 패닉은 계속((3)절) |
| `defer recover()` | ★★★ **아무도** | 못 멈춘다((3)절) |
| 이름 없는 반환값 + `defer` 안 `recover` | ★★ **아무도** | 패닉이 **조용히 삼켜진다**((5)절) |
| `main` 의 `recover` 로 다른 고루틴 보호 | ★★ **아무도** | 프로세스가 죽는다((4)절) |
| 입력 패턴에 `regexp.MustCompile` | **런타임**이 실행 중에 | 패닉 — `Compile` 을 써라 |

## 어디서 틀리나

### 1. ★★★ 「`recover` 를 도우미로 빼서 리터럴 안에서 부르면 된다」

- (3)절 실측 — **판2 `<nil>`**, guard 가 `P2` 를 받았다. guard 가 없으면 **종료 코드 2**(`t27c2`).
- 고치는 법 — **`defer helper()`** 로 도우미 **자체를** 건다(판3). 또는 리터럴 안에서 **직접** `recover()`.

### 2. ★★★ 「`main` 에 `recover` 를 두면 다 잡힌다」

- (4)절 실측 — 다른 고루틴의 패닉에 **main 의 `defer` 가 돌지도 않았다.** 종료 코드 2.
- 고치는 법 — **고루틴마다** 자기 `defer`/`recover`. 그 고루틴의 첫 줄에 둔다.

### 3. ★★ 「`recover` 했으니 호출자가 알겠지」

- (5)절 실측 — `lostDiv` 가 **`0, <nil>`**. 이름 없는 반환값이라 오류를 못 돌려줬다.
- 고치는 법 — **명명 반환값 `(…, err error)`** 에 쓴다.

### 4. ★★ 「`defer recover()` 한 줄이면 된다」

- (3)절 실측 — **판5**, guard 가 `P5` 를 받았다. `recover` 가 「`defer` 된 함수가 부른 것」이 아니다.

### 5. ★★ 「`recover()` 가 `nil` 이면 패닉이 없었다」

- (7)절 실측 — `go 1.20` 판에서 **`panic(nil)` 이 `nil` 로 돌아왔다.** (3)절 판2 도 `nil` 인데 패닉은 있었다.
- 고치는 법 — 1.21 이상 판을 쓰고, **「못 들은 것」을 `nil` 로 판정하지 않는다.**

### 6. ★★ 「표준 라이브러리는 남의 패닉을 오류로 바꿔 준다」

- (8)절 실측 — `fmt` 는 **글자로 바꾸고**, `json` 은 **v1 은 다시 던지고 v2 는 안 받는다.** **오류로 바꿔 주는 판은 없었다.**
- 고치는 법 — 내 콜백이 패닉하면 **내가 막는다.** 그리고 로그의 `%!v(PANIC=…)`·`<nil>` 을 **패닉의 흔적**으로 읽는다.

### 7. ★ 「재패닉하면 메시지가 두 번 나온다」

- (6)절 실측 — 이 판(1.25+)은 **`[recovered, repanicked]` 한 줄**이다. 다른 값이면 **사슬 전체**가 줄마다 나온다.

### 8. ★ 「패닉은 언제나 나쁘다」

- (9)절 실측 — **초기화 시점의 상수**가 틀린 것은 패닉이 맞다(`MustCompile`). 실행 중의 입력 실패는 오류다.

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| ★★★ **되감기가 안쪽 `defer` 부터 도는 것** | **명세 보장** | (1)절 명세 문장 · 실측 |
| ★★★ **`recover` 가 「`defer` 된 함수 안에서 직접」만 듣는 것** | **명세 보장** | 「not called directly by a deferred function」 |
| **같은 고루틴의 패닉만 보는 것** | **명세 보장** | 「on the same goroutine」 |
| ★★ **직접 불렸으면 `nil` 이 아님을 보장 · `panic(nil)` 이 런타임 패닉** | **명세 보장(현행)** | (1)·(7)절 |
| ★★ **`go 1.20` 모듈에서 예전 동작** | **툴체인·런타임(GODEBUG)** | `godebug.md` · (7)절 격자 |
| **종료 코드 2** | ★ **런타임** | 명세는 「terminated」, `go doc` 은 「non-zero」만 |
| 트레이스 모양 · `[recovered, repanicked]`(1.25+) | **런타임** | (6)절 · 릴리스 노트 |
| 고루틴 id | **런타임 — 흔들린다** | (4)절 |
| `runtime.Error` 인터페이스 | **표준 라이브러리 계약** | (4)절 |
| `boundsError`·`plainError` 같은 **구체 타입 이름** | **구현 내부** | 기대지 마라 |
| `fmt` 의 `%!v(PANIC=…)` | **표준 라이브러리 계약** | (8)절 · `fmt` 문서 |
| ★★ **`encoding/json` 이 v2 로 빌드되는 것** | **이 툴체인 판의 기본 실험** | (8)절 `exp.go` |
| `recover`·`defer` 의 **비용** | ★ **안 쟀다** | — |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 예상할 수 있는 실패(입력·파일·네트워크) | **`error` 반환** | [23번 주제](../23-error-interface-and-errors-as-values/) — 패닉이 아니다 |
| 소스에 박힌 상수가 틀렸다 | **`Must…` + 패닉** | (9)절 — 초기화에서 바로 드러난다 |
| 불변식이 깨졌다(있을 수 없는 상태) | **패닉** | 계속 가면 더 나쁜 것을 만든다 |
| 라이브러리 경계에서 **내 내부 패닉**을 감춘다 | **`defer` + `recover` + 명명 반환값** | (5)절 · `json` v1 의 `jsonError` 방식 |
| 남의 콜백을 부른다 | **패닉이 올 수 있음을 알고, 막을지 정한다** | (8)절 — 표준은 대신 막아 주지 않았다 |
| 서버의 요청 하나·작업 하나 | **그 고루틴 첫 줄에 `defer`/`recover`** | (4)절 — main 이 대신 못 잡는다 |
| 받아서 기록만 하고 넘긴다 | **재패닉 `panic(r)`** | (6)절 |

## 핵심 문장

- ★★★ **패닉은 안쪽 `defer` 부터 돌며 거슬러 간다** — `inner` → `middle` → `outer` → `main`. **패닉 뒤 본문은 안 돈다.**
  아무도 안 받으면 **`defer` 를 다 돈 뒤에** `panic:` 을 찍고 **종료 코드 2**(런타임).
- ★★★ **`recover` 는 「`defer` 로 불린 함수 안에서 직접」만 듣는다** — **한 겹 더 감싸면 `nil`** 이고 바깥 guard 가 그 패닉을 받았다.
  **`defer helper()` 는 되고, `defer recover()` 는 안 된다.**
- ★★★ **다른 고루틴의 패닉은 못 잡는다** — main 의 `defer` 가 **돌지도 않고** 종료 코드 2.
- ★★ **런타임 패닉은 전부 `runtime.Error`** 이고 구체 타입은 넷으로 갈린다. **내가 던진 것은 `runtime.Error` 가 아니다.**
- ★★★ **패닉을 오류로 바꾸려면 명명 반환값** — 이름이 없으면 **`0, <nil>`**, 패닉이 **조용히 삼켜진다.**
- ★★★ **`panic(nil)` 은 `go.mod` 한 줄로 갈린다** — `go 1.20` 은 `<nil>`, `go 1.21` 은 `*runtime.PanicNilError`, `GODEBUG=panicnil=1` 은 다시 `<nil>`.
  **같은 `go` 줄이라도 루프 변수는 컴파일러, 이것은 런타임 GODEBUG 가** 정한다.
- ★★ **재패닉은 `[recovered, repanicked]`**(1.25+ — 판 격자는 못 돌렸다). 되감는 중의 새 패닉은 **앞의 것을 덮는다.**
- ★★★ **표준은 남의 패닉을 오류로 바꿔 주지 않았다** — `fmt` 는 **글자로 바꾸고**(`%!v(PANIC=…)`),
  `json` v1 은 **자기 것만 오류로, 남의 것은 다시 던지고**, 이 판의 기본인 **v2 는 아예 안 받는다.**
- ★★ **초기화 시점의 상수 오류는 패닉이 맞다** — `regexp.MustCompile`, `main.init()` 에서 터진다.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 27번)
- [`systems/call-stack/`](../../../../../systems/call-stack/) — ★★ **정본 경계.**
  **그쪽은 콜 스택과 되감기 일반(프레임이 어떻게 쌓이고 풀리나)까지**, 여기는 **Go 의 `defer`/`recover` 순서부터.**
  이 문서는 스택 자체를 다시 쓰지 않는다
- [26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/)(`defer`) — ★★★ **직접 선행 — 한 사슬.**
  **그쪽은 「`defer` 가 언제 평가되고 언제 도나(패닉 중에도)」까지**, 여기는 **「누가 멈추나」부터**
- [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/) (4)절 — ★★★ **`fmt` 의 `catchPanic`**, 로그의 `<nil>` 은 삼켜진 패닉일 수 있다
- [12번 주제](../12-functions-multiple-returns-named-results-and-variadics/) (2)절 — `recovered()` 관용구의 첫 실측
- [13번 주제](../13-closures-variable-capture-and-loop-variable-change/) (3)절 — `go.mod` 판 격자(루프 변수 — 컴파일러 쪽)
- [22번 주제](../22-type-assertion-any-and-comparable/) — `recover()` 가 `any` 를 줘서 단언으로 가르는 바탕 · 단언 실패의 패닉
- [23번 주제](../23-error-interface-and-errors-as-values/) — 「오류는 값」 — 패닉을 쓰지 않는 쪽의 정본
- [25번 주제](../25-sentinel-errors-vs-custom-error-types/) — 오류 문구에 기대지 마라(`json` v1 과 v2 가 다르다)
- [28번 주제](../28-goroutines-go-statement-cost-and-termination/)(고루틴) — 고루틴마다 `recover` 가 필요한 바탕
- Rust 갈래 [23번](../../../rust/syntax/23-panic-vs-result/) — ★★ **`catch_unwind` 는 값으로 받는 함수, 쓰는 자리는 FFI·스레드 풀·테스트뿐.** 종료 코드 101
- [`../../../java/syntax/25-exceptions/`](../../../java/syntax/25-exceptions/) — `finally` 는 블록, `catch` 는 타입
- C++ 갈래 [14번](../../../cpp/syntax/14-destructors-and-deterministic-destruction/) (2)절 — **예외가 지나가도 소멸자가 전부 돈다**(되감기)

## 용어 풀이

- **패닉** — 현재 고루틴의 정상 실행을 멈추고 `defer` 를 돌며 거슬러 가는 종료 순서.
- **되감기(unwinding)** — 그 거슬러 가는 과정. Go 에서는 **`defer` 가 도는 것**이 곧 되감기다.
- **`recover`** — `defer` 로 불린 함수 안에서 **직접** 불렸을 때만 패닉 값을 받고 되감기를 멈춘다.
- **재패닉** — 받은 패닉 값을 다시 `panic` 하는 것. 1.25 부터 `[recovered, repanicked]` 로 표시.
- **`runtime.Error`** — 런타임 패닉 값의 인터페이스.
- **`PanicNilError`** — 1.21 부터 `panic(nil)` 이 만드는 런타임 오류.
- **GODEBUG** — 런타임 동작을 판마다 되돌리는 스위치. `go.mod` 의 `go` 줄이 기본값을 정한다.
- **`Must` 관용구** — 실패하면 패닉하는 생성 함수. 초기화 시점의 상수에 쓴다.

---

## 더 들어가면

- ★ **`runtime.Goexit`** — 패닉이 아닌데 `defer` 를 돌리고 고루틴을 끝낸다. `recover` 는 `nil` 을 준다(`go doc` — [28번 주제](../28-goroutines-go-statement-cost-and-termination/)가 싣는다). 이 문서는 **안 던졌다.**
- ★ **`text/template`** 에도 `recover()` 가 있다(`exec.go` 셋 · `funcs.go` 하나를 `grep` 으로만 봤다) — **안 던졌다.**
- ★ **`debug.SetPanicOnFault`**·시그널 패닉 세부는 **안 던졌다.**
- ★ **트레이스 모양을 바꾸는 `GOTRACEBACK`** — (8)절에서 `none` 을 흔들림 제거용으로만 썼다. 다른 값은 **안 던졌다.**
- ★★ `panic`/`recover` 의 **비용**은 **안 쟀다.**

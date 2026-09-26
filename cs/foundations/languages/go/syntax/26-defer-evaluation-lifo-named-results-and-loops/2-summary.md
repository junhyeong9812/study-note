# go/syntax/26 — `defer`: 평가 시점·LIFO·명명 반환값 수정·루프 안의 `defer` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Go 명세 — Defer statements](https://go.dev/ref/spec#Defer_statements) ·
> [`os.Exit`](https://pkg.go.dev/os#Exit) 문서. 명세는 웹이 아니라
> **이 툴체인이 들고 있는 `$(go env GOROOT)/doc/go_spec.html` 에서 직접 떴다.**\
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> **버전** — `defer` 의 규칙에 **판 경계가 없다**(1.0 부터 같은 문장이다). 이 문서가 쓰는 판 의존 문법은
> 정수 `range`(`for i := range 3`, **1.22**)뿐이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체는 넷째 창이다** — 「**평가되는 순간 자기 이름을 찍는 함수(`val`)를 인자 자리에 끼워, 「언제 평가됐나」를 로그 줄의 위치로 보는 창**」.
`defer f(x)` 와 `defer func(){ f(x) }()` 가 **어느 줄에서 `x` 를 읽었는지**가 출력의 차례로 드러난다.
★ 그 짝으로 「**`/proc/self/fd` 를 세어 `defer` 가 안 돈 것을 자원 수로 보는 창**」.

★★★ **이 문서의 순서 규칙은 전부 명세다** — 인자 평가 시점·LIFO·`return` 뒤 실행·`nil` 함수 값의 패닉 시점.
**gc 가 그렇게 구현했다**가 아니라 **명세가 못 박았다.** 그 선을 절마다 긋는다.

★★ [12번 주제](../12-functions-multiple-returns-named-results-and-variadics/)가 이미 잰 것 —
「명명 반환값 + `defer`」(12의 본체) · `defer` 로 오류 감싸기 · 인자는 선언 시점 · LIFO — 은 **다시 재지 않고 인용한다.**
[13번 주제](../13-closures-variable-capture-and-loop-variable-change/) (6)절의 「루프 변수와 `defer` 클로저」도 그쪽이 정본이다.
**여기는 `defer` 자체의 전모** — 함수 값까지 평가되는 것, 메서드 값의 수신자, **루프에서 쌓이는 자원**, `os.Exit`, **버려지는 오류**다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | ★★★ **이 주제의 거의 전부** — `Defer statements` 절의 네 문장 |
| **표준 라이브러리 계약** | `os`·`bufio` 가 문서로 약속한 것 | `os.Exit` 의 「deferred functions are not run」 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 실행 출력 · `/proc/self/fd` 수(리눅스) |

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | `nil` 함수 값 패닉 블록의 `[signal …]` 줄 **`pc=0x…`** | 실행 주소다 — 기본 정규화 규칙(주소)이 잡는다 |
| 안 흔들린다 | ★★★ 로그 줄의 **차례**(`[평가]`·`[실행]`·`[defer]`) | 명세가 정한 순서다 — 이 주제의 핵심 근거 |
| 안 흔들린다 | fd 블록의 **참거짓**(「늘었나」) | ★ **fd 의 절댓값은 싣지 않았다** — 런타임이 여는 fd 가 판·환경마다 다를 수 있어 「N 이상 늘었나」·「1 이하인가」만 찍었다 |
| 안 흔들린다 | 종료 코드(`0`·`2`·`3`) · `go vet` 문장 | |
| 해당 없음 | 고루틴 id · 시간 | 이 주제는 동시성도 시간도 싣지 않는다 |

## 한눈에 — 쉽게 말하면

**`defer` 는 「나갈 때 할 일」을 적어 두는 쪽지다.** 쪽지에는 **할 일(함수)과 재료(인자)를 지금** 적는다.
**실제로 하는 것은 함수가 끝날 때**이고, 쪽지는 **나중에 적은 것부터** 처리한다.

| 비유 | 실체 |
|---|---|
| 쪽지에 **재료를 지금 적어** 넣는다 | ★★★ `defer f(x)` — **함수 값과 인자는 등록 시점에 평가** |
| 쪽지에 「**그때 가서 서랍을 열어 봐라**」라고 적는다 | ★★★ `defer func(){ f(x) }()` — **클로저가 실행 시점에 `x` 를 읽는다** |
| 쪽지 더미는 **맨 위부터** 처리한다 | ★ **LIFO** — 나중에 적은 것이 먼저 돈다 |
| 퇴근할 때 처리한다 — **방을 나설 때가 아니다** | ★★★ **함수가 끝날 때** 돈다. 블록·루프 한 바퀴의 끝이 아니다 |
| 하루 종일 문을 열 때마다 「퇴근할 때 닫기」 쪽지를 쓴다 | ★★★ **루프 안 `defer`** — 문이 **퇴근 때까지 전부 열려 있다** |
| 비상구로 **건물째 폭파**하고 나간다 | ★ `os.Exit` — **쪽지를 하나도 안 본다** |
| 쪽지 처리 결과 「실패」를 **아무 데도 안 적는다** | ★★ `defer w.Flush()` — **반환값이 버려진다** |

```text
   ★★★ 두 칸 — 같은 x 를 읽는데 「언제」가 다르다 ((1)절의 실측)

        defer show("A", val("x", x))            defer func() { show("B", val("x", x)) }()
        ────────────────────────────            ─────────────────────────────────────────
   등록  val("x", x) 가 지금 돈다                함수 리터럴(값)만 만든다 — 안의 x 는 안 읽는다
        [평가] x = 1   ◀── 이 줄이 여기 찍힌다
          │
   x = 2  (본문이 x 를 바꾼다)
          │
   끝    (LIFO — B 먼저)                         몸통이 이제 돈다
                                                [평가] x = 2   ◀── 이 줄은 여기 찍힌다
                                                [실행] B 가 받은 값 = 2
        [실행] A 가 받은 값 = 1

   ★ 규칙은 하나다 — defer 뒤의 「호출식」에서 함수 값과 인자만 지금 평가된다.
     클로저 안의 x 는 「클로저의 몸통」이지 인자가 아니다.
```

```text
   ★★★ 스코프 끝 대 함수 끝 — 루프 안에서 갈린다 ((4)절 · C++ 14편과 대비)

   C++ (RAII)                               Go (defer)
   for (…) {                                for _, p := range paths {
       std::ifstream f(p);                      f, _ := os.Open(p)
       …                                        defer f.Close()
   }   ◀── 여기서 ~ifstream (회차마다)       }   ◀── 여기서는 아무 일도 없다
                                            …
                                            return  ◀── 여기서 Close 50번이 한꺼번에(LIFO)

   열린 fd:  1 → 0 → 1 → 0 …                 열린 fd:  1 → 2 → … → 50 → (return) → 0
```

> **`defer` 문** — 명세 「A "defer" statement invokes a function whose execution is deferred to the moment
> the surrounding function returns」. **둘러싼 함수**가 끝날 때다.

> **등록 시점 / 실행 시점** — `defer` 문을 **지나는 순간**(등록)과 함수가 **끝나는 순간**(실행).
> 명세 「Each time a "defer" statement executes, the function value and parameters to the call are evaluated … and saved anew」.

> **메서드 값(method value)** — `x.Close` 처럼 수신자를 묶은 함수 값. `defer x.Close()` 는 **이 값을 등록 시점에 만든다.**

- [12번 주제](../12-functions-multiple-returns-named-results-and-variadics/)가 **이 주제의 선행**이다. 거기서 결론난 것 셋 —
  ① `defer` 가 `return` 이 **이미 써 놓은 명명 반환값을 고친다** ② 이름이 없으면 고칠 칸이 없다(`loadBroken`)
  ③ `defer fmt.Println(i)` 는 등록 때의 `i`. ★ **③을 여기서는 「평가가 일어나는 줄」로 한 칸 더 판다**((1)절).
- C++ 과 다른 점 — ★★★ **C++ 의 소멸자는 스코프 끝에서, Go 의 `defer` 는 함수 끝에서** 돈다.
  C++ 갈래의 [14번](../../../cpp/syntax/14-destructors-and-deterministic-destruction/) (1)절이 실측한 순서 — 「지역 3 → 지역 2 → 지역 1」, **쌓인 역순** —
  는 Go 의 LIFO 와 **같은 모양**이지만, **쌓이는 단위가 블록이냐 함수냐**가 다르다.
  ★ 그래서 **루프 안 `defer` 가 쌓이는 것은 C++ RAII 에는 없는 사고**다((4)절).
- Python 과 다른 점 — `with` 는 **블록을 나설 때** 닫는다. 다중 `with A, B, C` 의 해제가 **역순**인 것은 같다
  ([`../../../python/syntax/28-context-managers-and-with/`](../../../python/syntax/28-context-managers-and-with/) 3절).

## 이 주제가 답하려는 질문

1. **`defer` 뒤의 무엇이 언제 평가되나** — 인자·함수 값·수신자·클로저 안의 변수.
2. **언제 도나** — LIFO, `return` 뒤, 패닉 중에는? `os.Exit` 에서는?
3. **루프에서 자원이 왜 쌓이고 어떻게 고치나** — 그리고 `defer` 가 **버리는 오류**는 무엇인가.

★ `defer` 안에서 **`recover`** 로 패닉을 멈추는 것은 [27번 주제](../27-panic-recover-and-where-to-use-them/)가 정본이다 —
**여기는 「패닉 중에도 `defer` 는 돈다」까지**, 거기는 **「어디서 부른 `recover` 만 듣나」부터.**

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| **`defer` 로 찍은 줄의 차례** | LIFO · `return` 뒤 실행 | [12번 주제](../12-functions-multiple-returns-named-results-and-variadics/)에서 쓰던 창 |
| ★★★ **평가될 때 이름을 찍는 `val()` 을 인자에 끼우기** | **평가가 어느 줄에서 일어났나** | ★ 본체 창 — 이 주제의 넷째 창 |
| ★★★ **`/proc/self/fd` 세기** | `defer` 가 **아직 안 돈 것**을 자원 수로 | ★ 이 주제의 고유 창 |
| ★★ **`/dev/full` 에 쓰기** | 버려진 `Flush`·`Close` 오류를 **일부러 만들기** | ★ 이 주제의 고유 창 |
| ★ **`go vet` 탐침 넷** | 이 주제의 실수를 **도구가 몇 개 잡나** | [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/) (6)절의 탐침 창 |
| **부적용 — `go.mod` 판 격자** | **잴 것이 없다.** `defer` 의 문장은 1.0 부터 같다 | — |
| **부적용 — 벤치마크** | 안 쟀다. 「`defer` 는 비싸다」·「이제는 공짜다」 **둘 다 이 문서는 말하지 않는다** | — |

★★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.**
「루프 안 `defer` 가 **쌓이나**」를 `defer` 의 개수로 물을 창이 없다(런타임이 그 수를 공개하지 않는다).
그래서 **`defer` 가 쥐고 있는 자원 — 열린 파일 기술자 — 의 수**로 물었다((4)절).
★ 바꾼 창의 한계 — **자원을 쥐지 않는 `defer`**(로그만 찍는 것)는 이 창에 안 보인다.
또 **리눅스 `/proc`** 에 기댄다 — 다른 OS 에서는 이 블록이 그대로 안 돈다.

### (1) ★★★ 등록 시점 대 실행 시점 — 평가가 일어나는 줄

**언제 쓰나** — `defer` 에 넘기는 값이 **나중에 바뀌는** 변수일 때. **가장 자주 틀리는 자리**다.

```text
===== 소스: t26a.go =====
package main

import "fmt"

// val 은 자기가 「평가된 순간」을 찍고 값을 돌려준다.
func val(tag string, v int) int {
	fmt.Printf("    [평가] %s = %d\n", tag, v)
	return v
}

func show(tag string, v int) { fmt.Printf("    [실행] %s 가 받은 값 = %d\n", tag, v) }

func main() {
	x := 1
	fmt.Println("1) defer show(\"A\", val(\"x\", x)) 를 적는다")
	defer show("A", val("x", x))

	fmt.Println("2) defer func() { show(\"B\", val(\"x\", x)) }() 를 적는다")
	defer func() { show("B", val("x", x)) }()

	x = 2
	fmt.Println("3) x = 2 로 바꿨다. 이제 main 이 끝난다")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
1) defer show("A", val("x", x)) 를 적는다
    [평가] x = 1
2) defer func() { show("B", val("x", x)) }() 를 적는다
3) x = 2 로 바꿨다. 이제 main 이 끝난다
    [평가] x = 2
    [실행] B 가 받은 값 = 2
    [실행] A 가 받은 값 = 1
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`1)` 바로 아래에 `[평가] x = 1` 이 찍혔다** — `defer show("A", val("x", x))` 를 **지나는 순간** `val` 이 돌았다.
  **인자는 등록 시점에 평가된다.**
- ★★★ **`2)` 아래에는 아무것도 없다** — `defer func(){ … }()` 는 **함수 리터럴을 값으로 만들 뿐**이고,
  안의 `val("x", x)` 는 **몸통**이라 지금 안 돈다.
- ★★★ **main 이 끝난 뒤 `[평가] x = 2` 가 찍힌다** — 클로저 몸통이 **실행 시점에 `x` 를 읽었다.** 그래서 B 는 **2**, A 는 **1**.
- ★ **B 가 A 보다 먼저** 돈다 — LIFO. 나중에 등록한 것이 먼저다.
- ★★ **이것이 명세의 문장 그대로다.**

```text
===== 명령: sed -n "7361,7374p" "$(go env GOROOT)/doc/go_spec.html" | sed -e "s/<[^>]*>//g" =====

Each time a "defer" statement
executes, the function value and parameters to the call are
evaluated as usual
and saved anew but the actual function is not invoked.
Instead, deferred functions are invoked immediately before
the surrounding function returns, in the reverse order
they were deferred. That is, if the surrounding function
returns through an explicit return statement,
deferred functions are executed after any result parameters are set
by that return statement but before the function returns to its caller.
If a deferred function value evaluates
to nil, execution panics
when the function is invoked, not when the "defer" statement is executed.
(exit 0)
```

  ★★★ 「**the function value and parameters to the call are evaluated as usual and saved anew but the actual function is not invoked**」 —
  **함수 값과 인자**가 지금 평가된다. **클로저 안의 변수는 둘 다 아니다** — 그래서 나중에 읽힌다.
  ★ 「**after any result parameters are set by that return statement**」 — 명명 반환값을 고칠 수 있는 근거다((5)절).
  ★ 「**If a deferred function value evaluates to nil, execution panics when the function is invoked, not when the "defer" statement is executed.**」 — (2)절이 던진다.

비용 — 인자를 저장해 두는 만큼. **이 문서는 재지 않았다.**

### (2) ★★ 함수 값도 등록 시점이다 — 그리고 `nil` 은 나갈 때 터진다

**언제 쓰나** — `defer` 뒤에 **함수 변수**를 쓸 때.

```text
===== 소스: t26b.go =====
package main

import (
	"fmt"
	"os"
)

func a() { fmt.Fprintln(os.Stderr, "  [defer] a 가 돌았다") }
func b() { fmt.Fprintln(os.Stderr, "  [defer] b 가 돌았다") }

func main() {
	f := a
	defer f() // 함수 값도 지금 평가된다
	f = b
	fmt.Fprintln(os.Stderr, "  f = b 로 바꿨다")

	var g func() // nil 함수 값
	defer g()
	fmt.Fprintln(os.Stderr, "  defer g() 를 지났다 — 아직 안 터졌다")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
  f = b 로 바꿨다
  defer g() 를 지났다 — 아직 안 터졌다
  [defer] a 가 돌았다
panic: runtime error: invalid memory address or nil pointer dereference
[signal SIGSEGV: segmentation violation code=0x1 addr=0x0 pc=0x499ef4]

goroutine 1 [running]:
main.main()
	ex/t26b.go:20 +0xb4
(exit 2)
```

그림 해설 (한 단계씩):

- ★★ **`f = b` 로 바꿨는데 `a 가 돌았다`** 가 찍힌다 — `defer f()` 가 **함수 값 `f` 를 등록 시점에 평가**해 `a` 를 저장했다.
- ★★★ **`defer g()` 를 지났는데 안 터졌다** — `g` 는 `nil` 인데 등록은 된다.
  **main 이 끝날 때, 그 쪽지를 처리하는 순간** 터진다 — 명세의 「**when the function is invoked, not when the "defer" statement is executed**」 그대로다.
- ★★★ **터졌는데도 `a 가 돌았다` 가 찍혔다** — 패닉이 나도 **남은 `defer` 는 돈다**(`g` 가 LIFO 로 먼저, 그다음 `f` 에 저장된 `a`).
  그다음에야 `panic: … nil pointer dereference` 와 **종료 코드 2** 다.
  ★ 패닉 중의 `defer` 와 `recover` 는 [27번 주제](../27-panic-recover-and-where-to-use-them/) (1)절이 되감기 로그로 본다.
- ★ 스택에 **`main.main()` 한 프레임**뿐이다 — `nil` 함수를 부르려다 죽었으니 **부를 함수의 프레임이 없다.**

비용 — 없다.

### (3) ★★ 메서드 값 — 수신자가 등록 시점에 고정된다

**언제 쓰나** — `defer x.Close()` 를 쓰고 **그 뒤에 `x` 를 다시 대입**할 때.

```text
===== 소스: t26c.go =====
package main

import "fmt"

type File struct{ name string }

func (f *File) Close() { fmt.Println("    [defer] Close :", f.name) }

type Tag struct{ name string }

func (t Tag) Print() { fmt.Println("    [defer] Print :", t.name) }

func main() {
	f := &File{"첫째 파일"}
	defer f.Close() // 수신자 f(포인터 값)가 지금 평가된다
	f = &File{"둘째 파일"}

	t := Tag{"처음 이름"}
	defer t.Print() // 값 수신자 — 지금 복사된다
	t.name = "나중 이름"

	p := &File{"처음 이름"}
	defer p.Close() // 포인터는 고정되지만 가리키는 것은 바뀔 수 있다
	p.name = "나중 이름"

	fmt.Println("  main 끝 — 아래는 LIFO")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
  main 끝 — 아래는 LIFO
    [defer] Close : 나중 이름
    [defer] Print : 처음 이름
    [defer] Close : 첫째 파일
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`f = &File{"둘째 파일"}` 로 바꿨는데 `Close : 첫째 파일`** 이다.
  `defer f.Close()` 가 **메서드 값 `f.Close` 를 지금 만들면서 수신자 `f`(포인터 값)를 저장**했다.
- ★★ **값 수신자는 복사까지 된다** — `t.name = "나중 이름"` 으로 바꿔도 `Print : 처음 이름`.
  `Tag` 값 전체가 **등록 시점에 복사**됐다.
- ★★★ **그런데 포인터가 가리키는 것은 바뀐다** — `p.name = "나중 이름"` 은 **`Close : 나중 이름`** 으로 나온다.
  고정된 것은 **포인터 값**이지 **그 너머의 구조체**가 아니다. [16번 주제](../16-pointers-value-copy-semantics-new-and-make/)의 값 복사 규칙이 그대로 적용된다.
- ★ 정리 — **「무엇이 고정되나」는 「무엇이 복사되나」와 같은 질문**이다. 포인터면 주소가, 값이면 내용이 고정된다.

비용 — 없다.

### (4) ★★★ 루프 안의 `defer` — 함수가 끝날 때까지 안 돈다

**언제 쓰나** — 루프에서 파일·락·연결을 열 때. **컴파일도 되고 `go vet` 도 조용한** 자원 사고다.

```text
===== 소스: t26d.go =====
package main

import (
	"fmt"
	"os"
	"path/filepath"
)

// openFDs 는 이 프로세스가 지금 연 fd 수를 센다(리눅스 /proc).
func openFDs() int {
	ents, err := os.ReadDir("/proc/self/fd")
	if err != nil {
		panic(err)
	}
	return len(ents)
}

// bad — 루프 안의 defer. Close 는 함수가 끝날 때 한꺼번에 돈다.
func bad(paths []string) (atEnd int) {
	for _, p := range paths {
		f, err := os.Open(p)
		if err != nil {
			panic(err)
		}
		defer f.Close()
	}
	return openFDs() // 함수 끝 직전 — defer 는 아직 하나도 안 돌았다
}

// fixFunc — 한 회차를 함수로 감싼다. defer 가 회차마다 돈다.
func fixFunc(paths []string) (peak int) {
	for _, p := range paths {
		func() {
			f, err := os.Open(p)
			if err != nil {
				panic(err)
			}
			defer f.Close()
			if n := openFDs(); n > peak {
				peak = n
			}
		}()
	}
	return peak
}

// fixClose — defer 없이 회차 끝에서 직접 닫는다.
func fixClose(paths []string) (peak int) {
	for _, p := range paths {
		f, err := os.Open(p)
		if err != nil {
			panic(err)
		}
		if n := openFDs(); n > peak {
			peak = n
		}
		f.Close()
	}
	return peak
}

const N = 50

func main() {
	dir, err := os.MkdirTemp(".", "fd")
	if err != nil {
		panic(err)
	}
	defer os.RemoveAll(dir)
	var paths []string
	for i := 0; i < N; i++ {
		p := filepath.Join(dir, fmt.Sprint(i))
		if err := os.WriteFile(p, []byte("x"), 0o644); err != nil {
			panic(err)
		}
		paths = append(paths, p)
	}
	fixClose(paths[:1]) // 런타임이 처음 한 번 여는 fd(폴러 등)를 미리 열어 둔다
	base := openFDs()

	fmt.Printf("파일 %d개를 루프로 연다 — 「늘었나」만 본다\n", N)
	atEnd := bad(paths)
	fmt.Printf("  bad      : 함수 끝 직전 증가가 N 이상인가 : %v\n", atEnd-base >= N)
	fmt.Printf("             돌아온 뒤 기준으로 돌아왔나   : %v\n", openFDs() == base)
	peak := fixFunc(paths)
	fmt.Printf("  fixFunc  : 루프 중 최대 증가가 1 이하인가  : %v\n", peak-base <= 1)
	peak = fixClose(paths)
	fmt.Printf("  fixClose : 루프 중 최대 증가가 1 이하인가  : %v\n", peak-base <= 1)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
파일 50개를 루프로 연다 — 「늘었나」만 본다
  bad      : 함수 끝 직전 증가가 N 이상인가 : true
             돌아온 뒤 기준으로 돌아왔나   : true
  fixFunc  : 루프 중 최대 증가가 1 이하인가  : true
  fixClose : 루프 중 최대 증가가 1 이하인가  : true
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`bad` 는 함수 끝 직전 fd 증가가 N(50) 이상**이다 — 루프가 50번 돌며 연 파일이 **하나도 안 닫혔다.**
  `defer f.Close()` 쪽지 50장이 **함수 끝까지** 쌓여 있다.
- ★★ **돌아온 뒤에는 기준으로 돌아왔다** — 함수가 끝나는 순간 50장이 **한꺼번에(LIFO로)** 처리됐다.
  **새지는 않았다.** 다만 **루프가 도는 내내 쥐고 있었다** — 파일이 아주 많으면 `ulimit -n` 에 닿을 수 있다 — 이 문서는 거기까지 **안 던졌다**.
- ★★★ **고치는 법 둘** — 둘 다 **루프 중 최대 증가가 1 이하**다.
  - **`fixFunc`** — 한 회차를 **함수 리터럴로 감싼다.** `defer` 의 「둘러싼 함수」가 **회차 함수**가 되어 회차마다 돈다.
  - **`fixClose`** — `defer` 를 버리고 **회차 끝에서 직접 `Close`**. 단 그 사이에서 `return`·패닉이 나면 안 닫힌다.
- ★★★ **C++ RAII 에는 이 사고가 없다** — [C++ 14번](../../../cpp/syntax/14-destructors-and-deterministic-destruction/)이 실측한 대로
  소멸자는 **스코프(블록) 끝**에서 도니, 루프 본문 `{ }` 의 끝이 곧 회차마다의 해제다.
  [C++ 15번](../../../cpp/syntax/15-raii-resources-as-types/) (1)절이 「자원 셋을 타입으로 묶으면 세 경로가 같은 코드로 덮인다」고 보인 것도 **블록 단위**다.
  ★ Go 의 `fixFunc` 는 **함수로 블록을 흉내 내는 것**이다.
- ★ fd 의 **절댓값은 싣지 않았다** — 런타임이 처음 한 번 여는 fd(폴러 등)가 있어서, 기준을 잡기 전에 **한 번 열고 닫아 두었다**(`fixClose(paths[:1])`).

비용 — 쌓인 `defer` 만큼 메모리. **이 문서는 재지 않았다.**

### (5) ★★ 명명 반환값 — 함정의 꼴과 정당한 쓰임, 그리고 버려지는 오류

**언제 쓰나** — 쓰기 파일을 `defer` 로 닫을 때. **읽기 파일과 달리 `Close`·`Flush` 가 실패를 알려 주는 마지막 자리**다.

```text
===== 소스: t26f.go =====
package main

import (
	"bufio"
	"fmt"
	"os"
)

// /dev/full 은 쓰기마다 ENOSPC 를 돌려주는 리눅스 장치다.
// bufio 가 모아 두었다가 Flush 에서야 실제로 쓰므로 실패도 그때 나온다.

// dropped — defer 가 Flush 의 반환값을 버린다.
func dropped(path string) error {
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()
	w := bufio.NewWriter(f)
	defer w.Flush() // 오류가 여기서 사라진다
	_, err = w.WriteString("중요한 데이터")
	return err
}

// overwrite — 21편 (라)의 꼴. defer 가 명명 반환값을 무조건 덮는다.
func overwrite(path string) (err error) {
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer func() { err = f.Close() }() // Flush 의 오류를 Close 의 nil 로 덮는다
	w := bufio.NewWriter(f)
	if _, err = w.WriteString("중요한 데이터"); err != nil {
		return err
	}
	return w.Flush()
}

// checked — 명명 반환값을 「비어 있을 때만」 채우고, 문맥도 붙인다.
func checked(path string) (err error) {
	defer func() {
		if err != nil {
			err = fmt.Errorf("save %s: %w", path, err)
		}
	}()
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer func() {
		if cerr := f.Close(); cerr != nil && err == nil {
			err = cerr
		}
	}()
	w := bufio.NewWriter(f)
	if _, err = w.WriteString("중요한 데이터"); err != nil {
		return err
	}
	return w.Flush()
}

func main() {
	fmt.Println("dropped   :", dropped("/dev/full"))
	fmt.Println("overwrite :", overwrite("/dev/full"))
	fmt.Println("checked   :", checked("/dev/full"))
}
===== 명령: go build -trimpath -o prog . && ./prog =====
dropped   : <nil>
overwrite : <nil>
checked   : save /dev/full: write /dev/full: no space left on device
(exit 0)
```

그림 해설 (한 단계씩):

- ★ **`/dev/full` 은 쓰기마다 `ENOSPC` 를 돌려주는 리눅스 장치**다. `bufio.Writer` 가 모아 두었다가 **`Flush` 에서야** 실제로 쓰므로 실패도 그때 나온다.
- ★★★ **`dropped` 는 `<nil>`** — `defer w.Flush()` 가 **반환값을 버렸다.** `WriteString` 은 버퍼에만 넣어 성공했으니 **함수는 성공을 보고했고 데이터는 사라졌다.**
  ★ 읽기 파일의 `defer f.Close()` 는 대개 무해하지만 **쓰기 쪽은 이것이 데이터 유실**이다.
- ★★★ **`overwrite` 도 `<nil>`** — [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/) (라)의 꼴(`defer func(){ err = e }()`)이다.
  `return w.Flush()` 가 **ENOSPC 를 `err` 에 써 놓았는데**, 그 뒤에 도는 `defer` 가 **`f.Close()` 의 `nil` 로 덮었다.**
  ★ 명세의 「**after any result parameters are set by that return statement**」가 **여기서는 함정의 근거**다.
- ★★★ **`checked` 만 실패를 올린다** — `save /dev/full: write /dev/full: no space left on device`.
  두 `defer` 가 **정당한 쓰임** 둘을 보인다 —
  ① `if cerr := f.Close(); cerr != nil && err == nil { err = cerr }` — **비어 있을 때만** 채운다(21편의 규칙 (2)).
  ② `if err != nil { err = fmt.Errorf("save %s: %w", path, err) }` — **모든 반환 경로에 문맥**을 붙인다([12번 주제](../12-functions-multiple-returns-named-results-and-variadics/) (2)절의 `load`).
  ★ ②를 **맨 먼저 등록**해 **맨 나중에** 돌게 했다 — Close 오류까지 모인 뒤에 감싸야 하므로. **LIFO 를 설계에 쓴 자리**다.

```text
   ★★ 한 return 뒤에 defer 셋이 차례로 같은 칸을 만진다 (checked, (5)절)

   return w.Flush()      ① 결과 칸 err = ENOSPC 를 써 놓는다     ← return 이 먼저
     │
     ├ defer ③ (Close)   cerr == nil 이고 err != nil 이라 안 건드린다
     │                   (overwrite 판은 여기서 err = nil 로 덮었다)
     └ defer ① (문맥)    err != nil 이니 "save /dev/full: " 을 씌운다  ← 맨 먼저 등록, 맨 나중 실행
   호출자에게 반환
```

비용 — 없다.

### (6) ★ `os.Exit` 는 `defer` 를 안 돌린다

**언제 쓰나** — `main` 에서 종료 코드를 정할 때. `log.Fatal` 도 속에서 `os.Exit(1)` 을 부른다.

```text
===== 소스: t26e.go =====
package main

import (
	"fmt"
	"os"
)

func main() {
	defer fmt.Fprintln(os.Stderr, "  [defer] 이 줄은 찍히나?")
	fmt.Fprintln(os.Stderr, "  os.Exit(3) 을 부른다")
	os.Exit(3)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
  os.Exit(3) 을 부른다
(exit 3)
```

```text
===== 명령: go doc os.Exit && go doc log.Fatal =====
package os // import "os"

func Exit(code int)
    Exit causes the current program to exit with the given status code.
    Conventionally, code zero indicates success, non-zero an error. The program
    terminates immediately; deferred functions are not run.

    For portability, the status code should be in the range [0, 125].

package log // import "log"

func Fatal(v ...any)
    Fatal is equivalent to Print followed by a call to os.Exit(1).
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`[defer] 이 줄은 찍히나?` 가 없다** — 종료 코드는 **3**. 문서가 「**The program terminates immediately; deferred functions are not run.**」라 적는다.
  ★ 이것은 명세가 아니라 **`os` 패키지의 계약**이다 — 명세의 `defer` 문장은 「함수가 **반환할 때**」만 말하고, `os.Exit` 는 반환하지 않는다.
- ★★ **C++ 의 `std::_Exit` 와 같은 자리**다 — [C++ 14번](../../../cpp/syntax/14-destructors-and-deterministic-destruction/) (3)절이
  「`std::_Exit` 로 나가면 소멸자가 하나도 안 돈다 — `[파괴]` 줄이 **0개**」를 실측했다.
  Rust 의 `process::exit` 도 같다(Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **23번** (4)절).
- ★ **그래서 `main` 에 `defer` 를 두고 끝에서 `os.Exit` 를 부르면 그 `defer` 는 죽은 코드다.**
  흔한 처방은 **`func main() { os.Exit(run()) }`** — 정리는 `run` 의 `defer` 가 하고, `run` 이 **반환한 뒤에** 나간다.

비용 — 없다.

### (7) ★ 도구는 무엇을 보나 — 탐침 넷

**언제 쓰나** — 「린터가 잡아 주겠지」를 확인할 때.

```text
===== 소스: t26vet.go =====
package main

import (
	"fmt"
	"os"
	"time"
)

// 탐침 1 — 루프 안의 defer
func p1(paths []string) {
	for _, p := range paths {
		f, _ := os.Open(p)
		defer f.Close()
	}
}

// 탐침 2 — 쓰기 파일의 Close 오류를 버린다
func p2() {
	f, _ := os.Create("x")
	defer f.Close()
	f.WriteString("x")
}

// 탐침 3 — defer 의 인자에서 time.Since 를 부른다(등록 시점에 평가된다)
func p3() {
	start := time.Now()
	defer fmt.Println(time.Since(start))
}

// 탐침 4 — defer 뒤에 os.Exit
func p4() {
	defer fmt.Println("x")
	os.Exit(1)
}

func main() { p1(nil); p2(); p3(); p4() }
===== 명령: go vet ./... =====
t26vet.go:27:20: call to time.Since is not deferred
(exit 1)
```

그림 해설 (한 단계씩):

- ★★★ **탐침 4개 중 1개가 잡혔다** — **탐침 3**(`defer fmt.Println(time.Since(start))`) 하나. 종료 코드 1.
  `time.Since` 가 **등록 시점에 평가**돼 **0에 가까운 시간**을 찍는 사고다 — (1)절의 규칙을 **분석기가 아는 유일한 자리**다.
- ★★★ **루프 안 `defer`(탐침 1)·쓰기 파일 `Close` 오류 버리기(탐침 2)·`defer` 뒤 `os.Exit`(탐침 4)는 조용하다.**
  ★ 이 문서의 가장 큰 사고 셋((4)·(5)·(6)절)이 **전부 도구 밖**이다.
- ★ [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/) (6)절의 **8개 중 0개**, [24번 주제](../24-error-wrapping-and-errors-is-as-join/) (4)절의 **4개 중 3개**와 나란히 두면 —
  **그 자리에서 식 하나만 보고 판정되는 것**만 잡힌다. `time.Since` 가 `defer` 의 **인자 자리에 있다**는 것은 그 자리에서 보이지만,
  「이 루프가 몇 번 도나」·「이 파일이 쓰기용인가」는 안 보인다.

비용 — 없다.

## 문법 — 형태와 규칙

### 형태

```go
// t26form.go
package main

import "fmt"

type R struct{ n string }

func (r *R) Close() { fmt.Println("  Close", r.n) }

func named() (n int) {
	defer func() { n *= 10 }() // 명명 반환값을 고친다
	return 4
}

func main() {
	defer fmt.Println("  맨 처음 적은 defer — 맨 나중에 돈다")
	r := &R{"r"}
	defer r.Close()                                  // 메서드 값 — 수신자는 지금 고정
	defer fmt.Println("  인자는 지금 평가 :", 1+1)       // 인자는 지금
	defer func() { fmt.Println("  몸통은 나중 :", named()) }() // 몸통은 나중
	for i := range 3 {
		defer fmt.Println("  루프 안 defer", i) // 함수 끝까지 쌓인다
	}
	fmt.Println("  main 본문 끝")
}
```

```text
===== 명령: go build -trimpath -o prog . && ./prog =====
  main 본문 끝
  루프 안 defer 2
  루프 안 defer 1
  루프 안 defer 0
  몸통은 나중 : 40
  인자는 지금 평가 : 2
  Close r
  맨 처음 적은 defer — 맨 나중에 돈다
(exit 0)
```

규칙 불릿.

- **`defer` 뒤에는 호출식**이 온다. 괄호로 감쌀 수 없다(`defer (f())` 는 컴파일 에러 — [28번 주제](../28-goroutines-go-statement-cost-and-termination/) (6)절이 `go` 와 같이 던졌다).
- **함수 값·인자·메서드 값의 수신자는 등록 시점**에 평가된다. **클로저 몸통은 실행 시점**이다.
- **실행은 둘러싼 함수가 끝날 때, LIFO.** `return` 이 결과 칸을 채운 **뒤**, 호출자에게 돌아가기 **전**이다.
- **패닉 중에도 돈다.** `os.Exit` 에서는 **안 돈다.**
- **`nil` 함수 값은 등록은 되고 실행 때 패닉**이다.
- **`defer` 한 함수의 반환값은 버려진다** — 오류를 올리려면 **명명 반환값에 조건부로** 쓴다.
- **루프에서는 쌓인다** — 회차마다 돌리려면 **함수로 감싼다.**

### 금지 사례 — 컴파일러가 거부하는 것

| 쓴 꼴 | 진단 | 어디서 |
|---|---|---|
| `defer f` (호출 아님) | `expression in defer must be function call` | [28번 주제](../28-goroutines-go-statement-cost-and-termination/) (6)절 `t28bad.go` |
| `defer len(s)` (결과를 버리는 내장 함수) | `defer discards result of len(s) (value of type int)` | 〃 |
| 루프 안 `defer` · 쓰기 파일 `defer Close()` · `defer` 뒤 `os.Exit` | ★★★ **아무도 안 막는다** | (7)절 — `go vet` 도 조용하다 |

## 어디서 틀리나

### 1. ★★★ 「`defer f(x)` 는 나갈 때의 `x` 를 쓴다」

- (1)절 실측 — `[평가] x = 1` 이 **등록 줄 바로 아래** 찍히고 A 는 **1**을 받는다.
- 고치는 법 — 나갈 때 값이 필요하면 **`defer func(){ f(x) }()`**. 지금 값이 필요하면 그대로.

### 2. ★★★ 「루프에서 `defer f.Close()` 해도 회차마다 닫힌다」

- (4)절 실측 — 함수 끝 직전 fd 가 **N 이상** 늘어 있다. **함수 끝에서 한꺼번에** 닫힌다.
- 고치는 법 — **회차를 함수로 감싸거나**(`fixFunc`) **직접 `Close`**(`fixClose`).

### 3. ★★★ 「쓰기 파일도 `defer f.Close()` 면 충분하다」

- (5)절 실측 — `dropped` 가 **`<nil>`** 을 돌려주고 데이터는 사라졌다.
- 고치는 법 — **명명 반환값 + 조건부 대입**(`checked`). 또는 **`Flush`/`Close` 를 명시적으로 부르고 검사**한 뒤 `defer` 는 이중 닫기 방지용으로만.

### 4. ★★ 「`defer func(){ err = f.Close() }()` 로 Close 오류를 올리면 된다」

- (5)절 실측 — `overwrite` 가 **`<nil>`**. 앞선 **진짜 오류를 덮었다.** [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/) (라)의 꼴이다.
- 고치는 법 — **`err == nil` 일 때만** 채운다.

### 5. ★★ 「`defer x.Close()` 뒤에 `x` 를 바꾸면 새 것이 닫힌다」

- (3)절 실측 — **처음 것**이 닫혔다(`첫째 파일`). 수신자가 등록 시점에 고정된다.
- 고치는 법 — 바꿀 거면 **새 것에 대해 `defer` 를 다시** 건다. 나갈 때의 `x` 를 닫으려면 클로저로.

### 6. ★★ 「`main` 의 `defer` 는 `os.Exit` 전에 돈다」

- (6)절 실측 — **안 돈다**, 종료 코드 3. `log.Fatal` 도 같다.
- 고치는 법 — **`os.Exit(run())`** 꼴.

### 7. ★ 「`nil` 함수를 `defer` 하면 그 줄에서 터진다」

- (2)절 실측 — 그 줄은 **지나가고**, 함수가 끝날 때 터진다. 그 사이 다른 `defer` 도 돈다.

### 8. ★ 「`go vet` 이 `defer` 실수를 잡아 준다」

- (7)절 실측 — **4개 중 1개**(`time.Since`)뿐이다.

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| ★★★ **함수 값·인자가 등록 시점에 평가되는 것** | **명세 보장** | (1)절의 명세 문장 · 실측 |
| ★★★ **LIFO** | **명세 보장** | 「in the reverse order they were deferred」 |
| ★★ **`return` 이 결과 칸을 채운 뒤 `defer` 가 도는 것** | **명세 보장** | 「after any result parameters are set」 |
| **`nil` 함수 값이 실행 때 패닉하는 것** | **명세 보장** | 「when the function is invoked, not when …」 |
| **패닉 중에도 `defer` 가 도는 것** | **명세 보장** | `Defer statements` 첫 문장 · [27번 주제](../27-panic-recover-and-where-to-use-them/) |
| **메서드 값의 수신자가 고정되는 것** | **명세 보장** | 함수 값의 평가 = 메서드 값 만들기 |
| ★★ **`os.Exit` 가 `defer` 를 안 돌리는 것** | **표준 라이브러리 계약** | `go doc os.Exit` |
| **`bufio.Writer` 가 `Flush` 에서야 쓰는 것** | **표준 라이브러리 계약** | (5)절 실측 |
| `/dev/full` 이 `ENOSPC` 를 주는 것 · `/proc/self/fd` | **OS(리눅스)** | 다른 OS 에서는 이 블록이 안 돈다 |
| 런타임이 처음 여는 fd 의 수 | **구현·이 판** | 그래서 절댓값을 안 실었다 |
| `go vet` 이 `time.Since` 만 잡는 것 | **도구·이 판** | (7)절 |
| `defer` 의 **비용** | ★ **안 쟀다** | — |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 읽기 파일·락 해제 | **`defer x.Close()` / `defer mu.Unlock()`** | 모든 반환 경로·패닉을 덮는다 |
| **쓰기** 파일 | **명명 반환값 + 조건부 `Close` 오류** | (5)절 — 안 그러면 유실이 조용하다 |
| 모든 반환 경로에 문맥 | **`defer func(){ if err != nil { err = fmt.Errorf(…%w) } }()`** | [12번 주제](../12-functions-multiple-returns-named-results-and-variadics/) (2)절 |
| 루프에서 자원 | **회차를 함수로 감싸기** | (4)절 |
| 나갈 때의 값이 필요 | **클로저 `defer func(){…}()`** | (1)절 |
| 종료 코드를 정한다 | **`os.Exit(run())`** | (6)절 |
| 소요 시간 로그 | **`defer func(){ log(time.Since(start)) }()`** | (7)절 — 인자로 넣으면 0 이 찍힌다 |

## 핵심 문장

- ★★★ **`defer` 뒤 호출식의 함수 값과 인자는 등록 시점에 평가된다** — `[평가] x = 1` 이 **등록 줄 바로 아래** 찍혔다.
  **클로저 몸통 안의 `x` 는 실행 시점**에 읽힌다(`[평가] x = 2` 가 main 이 끝난 뒤에 찍혔다).
- ★★ **함수 변수도 수신자도 등록 시점에 고정된다** — `f = b` 뒤에도 `a` 가 돌고, `defer f.Close()` 뒤에 `f` 를 바꿔도 **첫째**가 닫힌다.
  **포인터가 가리키는 것은 바뀐다.**
- ★★ **`nil` 함수 값은 등록은 되고 실행 때 패닉** — 그 사이 다른 `defer` 도 돈다.
- ★★★ **`defer` 는 함수 끝에서 돈다 — 스코프 끝이 아니다.** 루프 50회 뒤 fd 가 **N 이상** 늘어 있었다.
  **C++ 소멸자는 블록 끝에서 돌아 이 사고가 없다.** 고치는 법은 **회차를 함수로 감싸기**다.
- ★★★ **쓰기 파일의 `defer Flush()`/`Close()` 는 오류를 버린다** — `/dev/full` 에 쓴 `dropped` 가 **`<nil>`**.
  **무조건 대입하는 `defer` 는 진짜 오류를 덮는다**(`overwrite` 도 `<nil>`). **`err == nil` 일 때만** 채운다.
- ★★ **LIFO 를 설계에 쓴다** — 문맥을 붙이는 `defer` 를 **먼저 등록**하면 **맨 나중에** 돌아 모든 오류를 감싼다.
- ★★ **`os.Exit` 는 `defer` 를 안 돌린다**(종료 코드 3, `[defer]` 줄 0개) — C++ 의 `std::_Exit` 와 같은 자리다.
- ★★ **`go vet` 은 탐침 4개 중 1개**(`time.Since` 를 인자로)만 잡는다. 루프 `defer`·버린 `Close` 오류·`os.Exit` 는 조용하다.
- ★ **이 순서 규칙은 전부 명세다.** `os.Exit` 만 `os` 패키지의 계약이다.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 26번)
- [12번 주제](../12-functions-multiple-returns-named-results-and-variadics/)(함수·명명 반환값) — ★★★ **선행.**
  **그쪽은 「명명 반환값을 `defer` 가 고친다」와 `defer` 의 두 꼴·LIFO 의 첫 실측까지**, 여기는 **`defer` 자체의 전모부터**
- [13번 주제](../13-closures-variable-capture-and-loop-variable-change/)(클로저·루프 변수) — (6)절 **루프 변수 × `defer` 클로저**의 정본
- [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/)(`nil` 인터페이스) — (라) **`defer` 가 명명 반환값을 채우는 함정**
- [16번 주제](../16-pointers-value-copy-semantics-new-and-make/)(포인터·값 복사) — 수신자 고정이 「무엇이 복사되나」와 같은 질문인 바탕
- [25번 주제](../25-sentinel-errors-vs-custom-error-types/)(오류 표면) — `defer` 로 붙이는 문맥이 **공개 표면을 늘리지 않는** 쪽
- [27번 주제](../27-panic-recover-and-where-to-use-them/)(`panic`/`recover`) — ★★ **`defer` 안의 `recover` 는 거기가 정본.** 여기는 「패닉 중에도 돈다」까지
- [28번 주제](../28-goroutines-go-statement-cost-and-termination/)(고루틴) — `go` 문의 인자도 **같은 규칙으로 즉시 평가**된다
- 목록의 **44번 주제**(`os`·`bufio`) — `Flush`·`Close` 누락으로 데이터가 사라지는 자리의 정본
- C++ 갈래 [14번](../../../cpp/syntax/14-destructors-and-deterministic-destruction/) — ★★★ **스코프 끝의 소멸자 · 쌓인 역순 · `std::_Exit`**
- C++ 갈래 [15번](../../../cpp/syntax/15-raii-resources-as-types/) — RAII 가 **블록 단위**로 자원을 덮는 것
- Rust 갈래 [09번](../../../rust/syntax/09-copy-clone-and-drop/) (6)절 — `Drop` 순서. **Rust 도 스코프 끝이다**
- [`../../../python/syntax/28-context-managers-and-with/`](../../../python/syntax/28-context-managers-and-with/) — `with` 는 블록 끝, 해제는 역순
- [`../../../java/syntax/26-try-with-resources/`](../../../java/syntax/26-try-with-resources/) — 자원 닫기를 **블록**에 묶는 쪽

## 용어 풀이

- **`defer`** — 둘러싼 함수가 끝날 때 부를 호출을 등록하는 문. LIFO.
- **등록 시점** — `defer` 문을 지나는 순간. 함수 값·인자·수신자가 이때 평가된다.
- **실행 시점** — 둘러싼 함수가 반환·패닉으로 끝나는 순간.
- **LIFO** — Last In, First Out. 나중에 등록한 것이 먼저 돈다.
- **메서드 값** — 수신자를 묶은 함수 값(`x.Close`).
- **명명 반환값** — 이름이 있는 결과 파라미터. `defer` 가 `return` 뒤에 고칠 수 있다.
- **fd(파일 기술자)** — 프로세스가 연 파일·소켓의 번호. 리눅스에서는 `/proc/self/fd` 에 하나씩 보인다.

---

## 더 들어가면

- ★ **`runtime.Goexit`** 도 `defer` 를 돌린다(`go doc runtime.Goexit` — [28번 주제](../28-goroutines-go-statement-cost-and-termination/)가 문서를 싣는다). 이 문서는 **`defer` 쪽에서는 안 던졌다.**
- ★ **`defer` 가 힙에 가나 스택에 가나**(open-coded defer)는 **구현 세부**다 — 이 문서는 **안 봤고 안 쟀다.**
- ★ 루프 안 `defer` 가 **`ulimit -n` 에 닿는 지점**은 **안 던졌다.**
- ★ **`defer mu.Unlock()` 과 패닉** — 락을 쥔 채 패닉이 나도 풀린다는 것은 (2)절 규칙의 따름정리다. 락 자체는 [목록의 **32번 주제**](../32-sync-mutex-rwmutex-waitgroup-once/).
- ★★ `defer` 의 **비용**은 **안 쟀다.** 「비싸다」도 「공짜다」도 이 문서는 말하지 않는다.

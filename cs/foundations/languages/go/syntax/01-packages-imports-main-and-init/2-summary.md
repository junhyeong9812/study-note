# go/syntax/01 — 패키지 선언·import·`main` 과 `init` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Go 명세](https://go.dev/ref/spec) 의 Package clause · Import declarations ·
> Package initialization · Program initialization · Program execution 절.\
> 웹이 아니라 **이 툴체인이 들고 있는 `$(go env GOROOT)/doc/go_spec.html` 을 열어** 인용했다.
> 그 파일의 머리는 「**Language version go1.27 (May 26, 2026)**」이다.
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 손으로 옮겨 적은 블록은 없다.
> **버전** — 이 절의 규칙은 Go 1 호환성 약속 아래 1.0부터 같다. 이 문서는 버전이 갈리는 자리를 다루지 않는다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 명세로, 출력은 실행으로 접지했다.

## 이 갈래가 쓰는 세 층

Go 는 **명세가 짧고 강하다.** 그래서 이 갈래의 모든 사실은 다음 세 층 중 하나에 넣고,
어느 층인지 **밝히지 않은 문장은 쓰지 않는다.**

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것. 어느 컴파일러에서도 같다 | `go_spec.html` 원문 인용 |
| **구현(gc)** | 이 컴파일러·런타임이 그렇게 하는 것. 약속은 아니다 | `go build`·`go tool compile` 출력 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 실행 출력(재실행 대조까지) |

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
===== 명령: go env GOOS GOARCH GOVERSION =====
linux
amd64
go1.27.1
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

출력을 근거로 읽기 전에 **어느 칸을 읽을지** 먼저 정해 둔다.

| 칸 | 흔들리나 | 확인한 방법 |
|---|---|---|
| `init`·변수 초기화가 찍는 순서 | **안 흔들림** | 이 문서의 결론 자체 — 명세가 정한다 |
| 패키지 이름·에러 문장 본문 | 안 흔들림 | 재실행 대조 전부 동일 |
| `파일:줄:칸` 좌표 | 안 흔들림 | 소스가 같으면 같다 |
| 종료 코드 | 안 흔들림 | 재실행 대조 전부 동일 |
| 패닉 스택의 `+0x…` 오프셋 | **판·빌드가 바뀌면 바뀐다** | 같은 바이너리 3판은 동일(md5 동일) |
| `goroutine N` 의 번호 | 고루틴을 안 띄우면 항상 `1` | 이 주제의 프로그램은 전부 단일 고루틴 |
| `go list -deps` 의 **표준 라이브러리 쪽** 줄 수 | **판이 바뀌면 바뀐다** | 62는 go1.27.1 의 수다 |
| 맵 순회 순서 | **매번 바뀐다 — 이 주제는 아예 안 쓴다** | [목록의 **09번 주제**](../09-maps-declaration-comma-ok-delete-and-iteration-order/) 참조 |

## 한눈에 — 쉽게 말하면

**프로그램이 시작되는 것은 공연장에 불이 켜지는 것과 같다 — 무대 밑부터 켜고, 막은 맨 마지막에 오른다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 공연장 한 채 | 프로그램 하나 (`main` 패키지 + 그것이 끌고 온 전부) |
| 무대 밑의 발전실·조명실 | `import` 한 패키지들 |
| 발전실이 먼저 켜져야 조명실이 켜진다 | **의존한 패키지가 먼저 초기화된다** |
| 방마다 「배선을 잇고」 → 「스위치를 올린다」 | 패키지마다 **변수 초기화** → **`init` 호출** |
| 방 하나에 스위치가 여러 개 | `init` 이 여러 개 — 소스에 적힌 순서대로 |
| 막이 오른다 | `main.main()` 호출 |
| 막이 내리면 조명이 뭐가 켜져 있든 끝 | `main` 이 돌아오면 **다른 고루틴을 기다리지 않고** 프로그램이 끝난다 |

- 무대 밑을 안 켜고 막을 올릴 수는 없다 — 그래서 **내가 쓴 코드가 도는 것은 언제나 마지막**이다.
- 발전실이 조명실을 켜고 조명실이 발전실을 켜는 배선은 **지을 수조차 없다** — 그게 순환 import 금지다.
- **한 방 안의 스위치 순서는 공연장이 정하지 않는다.** 전기공이 어느 도면을 먼저 폈느냐에 달렸다 — 이 한 칸이 이 주제의 가장 미끄러운 자리다.

```text
  ex/alpha          ex/beta            ex (main)
  (의존 없음)       (alpha 에 의존)     (alpha·beta 에 의존)
  ----------        ----------         ----------
  var A 초기화
       ↓
  init #1, #2
       ↓
                    var B 초기화
                         ↓
                    init
                         ↓
                                       var M 초기화
                                            ↓
                                       init #1, #2
                                            ↓
                                       main()   ← 여기서 처음으로 내 코드가 돈다
```

**언어도 똑같은 구조다.** 위 그림은 지어낸 것이 아니라 아래 (2)절 출력의 모양 그대로다.

> **초기화(initialization)** — 프로그램이 `main` 을 부르기 전에, 패키지마다 변수에 값을 넣고 `init` 을 부르는 단계.\
> 예: `var conn = mustConnect()` 은 `main` 의 첫 줄보다 **먼저** 돈다.

> **`init` 함수** — 인자도 반환값도 없는 `func init()`. 패키지당 여러 개를 둘 수 있고, 아무도 직접 부를 수 없다.\
> 예: `func init() { sql.Register("pg", &Driver{}) }` — 드라이버 등록이 대표 용도다.

> **순환 import(import cycle)** — A 가 B 를, B 가 A 를 import 하는 것. Go 는 **컴파일 자체를 거부**한다.\
> 예: `one` 이 `two` 를 쓰고 `two` 가 `one` 을 쓰면 `import cycle not allowed`.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `main` 의 첫 줄이 돌기 전에 **무엇이 몇 번 도는가** — 그 순서를 **무엇이** 정하는가.
2. 그 순서 중에서 **명세가 약속한 칸**과 **빌드 도구가 정한 칸**은 각각 어디인가.
3. `import` 한 줄이 만드는 것은 이름 하나뿐인가 — **부수효과**와 **금지**는 무엇인가.

## 동작 방식

### (1) 파일 한 장의 뼈대 — `package` · `import` · 선언

**언제 쓰나** — `.go` 파일을 새로 만들 때마다.

Go 파일은 **순서가 고정**돼 있다. 패키지 절이 맨 위, 그 다음 import 묶음, 그 다음부터 선언이다.

```go
// t01a.go
package main

import (
	"fmt"

	"ex/alpha"
	"ex/beta"
)

func trace(s string) int { fmt.Println(s); return 3 }

var M = trace("6. main: var M 초기화")

func init() { fmt.Println("7. main: init #1") }
func init() { fmt.Println("8. main: init #2") }

func main() {
	fmt.Println("9. main: main() 시작")
	fmt.Println("   alpha.A =", alpha.A, "· beta.B =", beta.B, "· M =", M)
}
```

- **`package` 절이 첫 줄**이다(주석은 그 위에 올 수 있다). 파일마다 반드시 있다.
- **`import` 는 패키지 절 바로 다음**, 다른 선언보다 먼저 와야 한다.
- 그 아래의 `var`·`func`·`const`·`type` 은 **순서가 자유**다 — 위에서 쓰고 아래에서 선언해도 된다.\
  (위 파일도 `trace` 를 쓰는 `var M` 이 `func trace` **아래**에 있지만, 반대로 써도 컴파일된다.)
- 실행 파일이 되려면 **패키지 이름이 `main` 이고 `func main()` 이 있어야** 한다.

비용 — 없음. 전부 컴파일 타임 배치다.

### (2) ★ 초기화는 아래에서 위로 — 의존 패키지가 먼저다

**언제 쓰나** — `main` 의 첫 줄이 왜 첫 줄이 아닌지 설명해야 할 때.

패키지 셋을 만들어 **실제로 찍어 본다.** `ex/beta` 가 `ex/alpha` 를 import 하고, `ex`(main)는 둘 다 import 한다.

```text
===== 소스: t01a.go =====
package main

import (
	"fmt"

	"ex/alpha"
	"ex/beta"
)

func trace(s string) int { fmt.Println(s); return 3 }

var M = trace("6. main: var M 초기화")

func init() { fmt.Println("7. main: init #1") }
func init() { fmt.Println("8. main: init #2") }

func main() {
	fmt.Println("9. main: main() 시작")
	fmt.Println("   alpha.A =", alpha.A, "· beta.B =", beta.B, "· M =", M)
}
===== 소스: t01a_alpha.go =====
package alpha

import "fmt"

func trace(s string) int { fmt.Println(s); return 1 }

var A = trace("1. alpha: var A 초기화")

func init() { fmt.Println("2. alpha: init #1") }
func init() { fmt.Println("3. alpha: init #2") }
===== 소스: t01a_beta.go =====
package beta

import (
	"fmt"

	"ex/alpha"
)

func trace(s string) int { fmt.Println(s); return 2 }

var B = trace("4. beta: var B 초기화 (alpha.A 는 이미 " +
	fmt.Sprint(alpha.A) + ")")

func init() { fmt.Println("5. beta: init") }
===== 명령: go build -trimpath -o prog . && ./prog =====
1. alpha: var A 초기화
2. alpha: init #1
3. alpha: init #2
4. beta: var B 초기화 (alpha.A 는 이미 1)
5. beta: init
6. main: var M 초기화
7. main: init #1
8. main: init #2
9. main: main() 시작
   alpha.A = 1 · beta.B = 2 · M = 3
(exit 0)
```

그림 해설 (한 단계씩):

- **1\~3** — `ex/alpha` 가 먼저 통째로 끝난다. 변수 `A` 가 먼저, `init` 둘이 그 뒤.
- **4** — `ex/beta` 의 변수 초기화식이 `alpha.A` 를 읽는데 **이미 1이 들어 있다.** 이게 「의존 패키지가 먼저」의 증거다.
- **6\~8** — `main` 패키지가 마지막이다. 여기서도 **변수가 먼저, `init` 이 나중**이다.
- **9** — 내 코드(`main()`)는 아홉 번째다.

명세는 이 순서를 **약속**한다.

> Given the list of all packages, sorted by import path, in each step the first
> uninitialized package in the list for which all imported packages (if any) are
> already initialized is initialized.

> The entire package is initialized by assigning initial values
> to all its package-level variables followed by calling
> all `init` functions in the order they appear
> in the source, possibly in multiple files, as presented to the compiler.

비용 — 초기화는 **단일 고루틴에서 순차로** 돈다(명세: "happens in a single goroutine, sequentially").
그래서 `init` 하나가 느리면 그만큼 기동이 통째로 늦어진다.

### (3) 한 패키지 안 — 변수가 먼저, 그리고 변수끼리는 **선언 순서가 아니라 의존 순서**

**언제 쓰나** — 패키지 변수가 서로를 참조할 때.

선언은 `a` → `b` → `c` 순인데, `a` 가 `b` 를 쓴다.

```text
===== 소스: t01b.go =====
package main

import "fmt"

func trace(name string, v int) int {
	fmt.Printf("  초기화: %s = %d\n", name, v)
	return v
}

var a = trace("a", b+1)
var b = trace("b", 10)
var c = trace("c", 100)

func main() {
	fmt.Println("main:", a, b, c)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
  초기화: b = 10
  초기화: a = 11
  초기화: c = 100
main: 11 10 100
(exit 0)
```

그림 해설 (한 단계씩):

- **`b` 가 먼저다.** `a` 는 `b` 에 의존하므로 아직 「준비」가 안 됐다.
- `b` 가 끝나면 준비된 것이 `a` 와 `c` 둘인데, **선언 순서가 빠른 `a`** 가 이긴다.
- `c` 가 마지막이다 — 선언은 셋째인데 실행도 셋째가 된 건 **우연이다.**

명세의 원문이 이 두 단계를 그대로 적는다.

> Initialization proceeds by repeatedly initializing the next package-level
> variable that is earliest in declaration order and ready for initialization,
> until there are no variables ready for initialization.

> Dependency analysis does not rely on the actual values of the
> variables, only on lexical references to them in the source, analyzed transitively.

읽는 법 두 줄.

- 고르는 기준은 **「준비됨」이 먼저이고 「선언 순서」는 동점일 때의 타이브레이커**다.
- 의존은 **값이 아니라 이름 참조**로 본다 — 함수 몸통 안의 참조까지 **전이적으로** 따라간다.

비용 — 없음(컴파일 타임 분석). 다만 **분석이 못 보는 의존**이 있다 — 아래 「구현 세부사항 대 언어 보장」 절.

### (4) ★ `init` 이 여럿일 때 — 파일 순서가 정하고, **그 파일 순서는 언어가 안 정한다**

**언제 쓰나** — 한 패키지를 파일 여러 개로 쪼갤 때. 즉 거의 항상.

`init` 하나씩을 가진 파일 셋을 같은 패키지에 둔다.

```text
===== 소스: t01c.go =====
package main

import "fmt"

func init() { fmt.Println("init in t01c.go") }

func main() { fmt.Println("main()") }
===== 소스: t01c_1st.go =====
package main

import "fmt"

func init() { fmt.Println("init in t01c_1st.go") }
===== 소스: t01c_2nd.go =====
package main

import "fmt"

func init() { fmt.Println("init in t01c_2nd.go") }
===== 명령: go build -trimpath -o prog . && ./prog =====
init in t01c.go
init in t01c_1st.go
init in t01c_2nd.go
main()
(exit 0)
===== 명령: go run t01c_2nd.go t01c_1st.go t01c.go =====
init in t01c_2nd.go
init in t01c_1st.go
init in t01c.go
main()
(exit 0)
```

그림 해설 (한 단계씩):

- **첫 명령**은 `go build` 다 — 파일을 **파일 이름 사전순**으로 컴파일러에 넘긴다.\
  `t01c.go` → `t01c_1st.go` → `t01c_2nd.go`. (`.` 의 코드값이 `_` 보다 작아 `t01c.go` 가 먼저다.)
- **둘째 명령**은 같은 세 파일을 **거꾸로 적어 `go run` 에 넘긴 것**이다.
  **`init` 순서가 그대로 뒤집혔다.**
- 소스는 한 글자도 안 바뀌었다. 바뀐 것은 **파일을 넘긴 순서**뿐이다.

★ **이것이 이 주제에서 가장 중요한 한 칸이다.** 명세는 파일 순서를 **약속하지 않는다.**

> The declaration order of variables declared in multiple files is determined
> by the order in which the files are presented to the compiler …
> To ensure reproducible initialization behavior, build systems are **encouraged**
> to present multiple files belonging to the same package in lexical file name
> order to a compiler.

「**encouraged**」다 — must 가 아니다. 사전순은 **빌드 도구의 예의**이지 언어의 약속이 아니다.

비용 — 없음. 대신 **위험**이 있다: 파일 이름을 바꾸는 리팩터링이 `init` 순서를 바꾼다.

### (5) 의존이 없는 패키지 둘은 **import 경로 정렬**이 정한다

**언제 쓰나** — 서로 모르는 패키지 둘을 같이 import 할 때.

`ex/alfa` 와 `ex/zulu` 는 서로를 모른다. 둘 사이의 순서는 무엇이 정하는가.

```text
===== 소스: t01h.go =====
package main

import (
	"fmt"

	"ex/alfa"
	"ex/zulu"
)

// import 문에서는 zulu 를 먼저 쓰고 싶어도 gofmt 가 정렬한다.
// 서로 의존이 없으므로 초기화 순서를 정하는 것은 import 경로 정렬이다.

func main() { fmt.Println("main:", alfa.A, zulu.Z) }
===== 소스: t01h_alfa.go =====
package alfa

import "fmt"

func init() { fmt.Println("alfa: init") }

var A = 1
===== 소스: t01h_zulu.go =====
package zulu

import "fmt"

func init() { fmt.Println("zulu: init") }

var Z = 26
===== 명령: go build -trimpath -o prog . && ./prog =====
alfa: init
zulu: init
main: 1 26
(exit 0)
```

그림 해설 (한 단계씩):

- `alfa` 가 먼저 돈다. import 문에 무엇을 위에 썼느냐와 **무관**하다(`gofmt` 가 어차피 정렬한다).
- 근거는 명세의 「**sorted by import path**」한 낱말이다 — (2)절 인용의 첫 줄.
- 그래서 **패키지 사이 순서는 명세 보장**이고, **한 패키지 안 파일 사이 순서는 아니다.** 층이 다르다.

비용 — 없음.

### (6) `import` 의 네 형태 — 그중 하나는 **부수효과가 목적**이다

**언제 쓰나** — 드라이버·코덱 등록처럼 「쓰지는 않는데 켜 두어야 하는」 패키지가 있을 때.

```go
// t01imp.go
package main

import (
	_ "ex/plugin" // 이름 없음 — init 만 돌리고 이름은 안 들여온다
	"fmt"         // 보통 — fmt.Println 으로 쓴다
	f "os"        // 별칭 — f.Getpid 로 쓴다
	. "strings"   // 점 — 이름을 지역처럼 쓴다 (권하지 않는다)
)

func main() {
	fmt.Println(ToUpper("점 import 는 이렇게 쓴다"), f.Getpid() > 0)
}
```

```text
===== 소스: t01imp.go =====
package main

import (
	_ "ex/plugin" // 이름 없음 — init 만 돌리고 이름은 안 들여온다
	"fmt"         // 보통 — fmt.Println 으로 쓴다
	f "os"        // 별칭 — f.Getpid 로 쓴다
	. "strings"   // 점 — 이름을 지역처럼 쓴다 (권하지 않는다)
)

func main() {
	fmt.Println(ToUpper("점 import 는 이렇게 쓴다"), f.Getpid() > 0)
}
===== 소스: t01imp_plugin.go =====
package plugin

func init() {}
===== 명령: go build -trimpath -o prog . && ./prog =====
점 IMPORT 는 이렇게 쓴다 true
(exit 0)
```

`_` 형태를 실제로 돌려 본다. `main` 은 `plugin` 의 이름을 하나도 안 쓴다.

```text
===== 소스: t01e.go =====
package main

import (
	"fmt"

	_ "ex/plugin"
)

func main() { fmt.Println("main()") }
===== 소스: t01e_plugin.go =====
package plugin

import "fmt"

func init() { fmt.Println("plugin: init 이 돌았다 — 아무도 부르지 않았는데") }

func Hello() string { return "안녕" }
===== 명령: go build -trimpath -o prog . && ./prog =====
plugin: init 이 돌았다 — 아무도 부르지 않았는데
main()
(exit 0)
```

그림 해설 (한 단계씩):

- `plugin` 의 `init` 이 **돌았다.** 아무도 부르지 않았고 이름도 안 들여왔다.
- 이름 없는 import 의 값어치가 여기 있다 — 「**이 패키지를 프로그램에 넣어라**」만 말한다.
- 그래서 `_` 를 지우면 **컴파일은 그대로 되고 동작만 조용히 바뀐다.** 이 주제의 대표적 무음 실패다.

비용 — 그 패키지와 그 패키지의 의존 전부가 바이너리에 들어온다.

### (7) ★ 네 번째 창 — `go list` 로 **초기화 순서를 실행 전에 읽는다**

실행 출력·컴파일 진단·`go vet` 셋으로는 「**왜** 이 순서인가」가 안 보인다.
Go 의 초기화 순서는 **빌드 그래프의 위상 정렬**이므로, 그래프를 직접 조회하는 창이 하나 더 있다.

```text
===== 명령: go list -deps . | grep '^ex' =====
ex/alpha
ex/beta
ex
(exit 0)
===== 명령: go list -f '{{.ImportPath}} <- {{.Imports}}' ex ex/alpha ex/beta =====
ex <- [ex/alpha ex/beta fmt]
ex/alpha <- [fmt]
ex/beta <- [ex/alpha fmt]
(exit 0)
===== 명령: go list -deps . | wc -l =====
62
(exit 0)
```

그림 해설 (한 단계씩):

- **첫 명령** — `go list -deps` 는 의존을 **먼저 오는 것부터** 늘어놓는다.
  `ex/alpha` → `ex/beta` → `ex`. (2)절에서 실제로 돈 순서와 **같다.**
- **둘째 명령** — 각 패키지가 **직접 import 한 것**을 보여 준다. 그래프를 손으로 그릴 수 있다.
- **셋째 명령** — 전부 세면 62개다. 내가 쓴 셋 말고 **`fmt` 와 그 아래 59개가 먼저 초기화된다**는 뜻이다.\
  ★ 62는 **go1.27.1 의 수**다 — 판이 바뀌면 바뀐다(「흔들리는 칸」 표).

**이 창이 답하는 것** — 「순서를 바꾸고 싶으면 무엇을 바꿔야 하나」. 답은 언제나 **의존을 바꾸는 것**이지
`init` 을 옮기는 것이 아니다.

비용 — `go list -deps` 는 빌드 캐시를 쓰므로 빌드보다 싸다. 다만 처음 한 번은 분석 비용이 든다.

## 문법 — 형태와 규칙

### 형태

```go
// t01form.go
package main // ① 패키지 절 — 첫 줄

import ( // ② import 묶음 — 다른 선언보다 먼저
	"fmt"
)

var x = 1 // ③ 그 아래는 순서 자유

func init() {} // ④ 인자 없음·반환값 없음·여러 개 가능

func main() { fmt.Println(x) } // ⑤ main 패키지에 하나
```

```text
===== 소스: t01form.go =====
package main // ① 패키지 절 — 첫 줄

import ( // ② import 묶음 — 다른 선언보다 먼저
	"fmt"
)

var x = 1 // ③ 그 아래는 순서 자유

func init() {} // ④ 인자 없음·반환값 없음·여러 개 가능

func main() { fmt.Println(x) } // ⑤ main 패키지에 하나
===== 명령: go build -trimpath -o prog . && ./prog =====
1
(exit 0)
```

규칙 불릿.

- 디렉토리 하나 = 패키지 하나. 같은 디렉토리의 `.go` 파일은 **패키지 이름이 같아야** 한다.
- 패키지 이름은 디렉토리 이름과 **달라도 되지만**, 다르면 읽는 쪽이 매번 확인해야 하므로 맞춘다.
- `import` 경로는 **모듈 경로 + 디렉토리 경로**다(`go.mod` 의 `module ex` + `alpha` → `ex/alpha`).
- `init` 은 **선언만 되고 이름으로 존재하지 않는다** — 부를 수도, 주소를 잡을 수도 없다.
- `main` 은 **인자도 반환값도 없다.** 종료 코드가 필요하면 `os.Exit` 를 쓴다.

### 금지 사례 — 컴파일러가 거부하는 것

**① 쓰지 않은 import 는 에러다** (경고가 아니다).

```text
===== 소스: t01f.go =====
package main

import (
	"fmt"
	"os"
)

func main() { fmt.Println("main()") }
===== 명령: go build -trimpath -o prog . =====
# ex
./t01f.go:5:2: "os" imported and not used
(exit 1)
===== 명령: gofmt -l . =====
(exit 0)
```

- 둘째 명령이 요점이다 — **`gofmt` 는 이걸 안 고친다**(출력 없음·종료 0).
  지워 주는 것은 `gofmt` 가 아니라 `goimports` 이고, 그건 툴체인에 없다.
- 즉 **포맷터를 돌렸다고 안심할 수 없다.** 에러를 내는 것은 컴파일러뿐이다.

**② `init` 은 이름이 아니다.**

```text
===== 소스: t01g.go =====
package main

import "fmt"

func init() { fmt.Println("init") }

func main() {
	init()
	fmt.Println(init)
}
===== 명령: go build -trimpath -o prog . =====
# ex
./t01g.go:8:2: undefined: init
./t01g.go:9:14: undefined: init
(exit 1)
```

- 「`init` 이 없다」가 아니라 「**undefined: init**」이다 — 정의는 됐는데 **이름이 선언되지 않았다.**
- 명세: "In the package block, the `init` identifier can be used only to declare `init` functions,
  yet the identifier itself is not declared."

**③ 순환 import 는 빌드 자체가 거부된다.**

```text
===== 소스: t01d.go =====
package main

import (
	"fmt"

	"ex/one"
)

func main() { fmt.Println(one.Name()) }
===== 소스: t01d_one.go =====
package one

import "ex/two"

func Name() string { return "one -> " + two.Name() }
===== 소스: t01d_two.go =====
package two

import "ex/one"

func Name() string { return "two -> " + one.Name() }
===== 명령: go build -trimpath -o prog . =====
package ex
	imports ex/one from t01d.go
	imports ex/two from t01d_one.go
	imports ex/one from t01d_two.go: import cycle not allowed
(exit 1)
```

- 에러가 **경로를 한 줄씩 따라가며** 보여 준다 — `ex` → `ex/one` → `ex/two` → 다시 `ex/one`.
- `go vet` 도 같은 문장을 낸다. 즉 **타입 검사 전에 걸리는** 층이다.
- 명세: "The importing of packages, by construction, guarantees that there
  can be no cyclic initialization dependencies." — 초기화 순환이 **있을 수 없는 이유**가 이것이다.

## 어디서 틀리나

### 1. ★ `init` 순서를 파일 이름에 기대어 쓴다

- (4)절이 보인 대로 **파일 순서는 언어 보장이 아니다.**
- `t01c_1st.go` 를 `aaa.go` 로 바꾸면 순서가 바뀐다. **리네임은 리팩터링이 아니라 동작 변경**이 된다.
- 고치는 법 — 순서가 필요하면 `init` 을 쓰지 말고 **한 `init` 안에서 명시적으로 부른다**,
  또는 `sync.Once` 로 첫 사용 시점에 미룬다([목록의 **32번 주제**](../32-sync-mutex-rwmutex-waitgroup-once/)).

### 2. ★ `_` import 를 「안 쓰는 줄」로 보고 지운다

- (6)절 실측 — 지우면 `plugin` 의 `init` 이 **안 돈다.** 컴파일은 그대로 성공한다.
- 증상은 「드라이버를 못 찾는다」 같은 **런타임 에러**로 한참 뒤에 나온다.
- 고치는 법 — `_` 옆에 **왜 넣었는지 주석**을 단다. 그것이 유일한 방어다.

### 3. 패키지 변수에서 무거운 일을 한다

- `var db = mustConnect()` 은 **`main` 보다 먼저** 돈다. 실패하면 플래그 파싱도 못 해 보고 죽는다.
- 게다가 (3)절대로 **의존 순서**가 정하므로, 「설정을 읽고 나서 접속」이 코드 모양과 다르게 배치될 수 있다.
- 고치는 법 — 패키지 변수는 **상수 같은 것**만 두고, 부작용이 있는 것은 `main` 안에서 명시적으로 부른다.

### 4. 순환 import 를 「구조 문제」로만 읽는다

- 순환은 **컴파일 에러**라 조용히 지나가지 않는다 — 이 주제에서 유일하게 안전한 실수다.
- 대신 사람들이 **패키지를 억지로 합치는 것**으로 푼다. 보통 옳은 해법은
  **인터페이스를 쓰는 쪽에 두는 것**이다([목록의 **20번 주제**](../20-interface-declaration-and-implicit-implementation/)).

### 5. 「`main` 이 끝나도 고루틴은 남겠지」

- 명세: "When that function invocation returns, the program exits.
  It does not wait for other (non-main) goroutines to complete."
- 이 문서에서는 **돌려 보지 않았다** — 고루틴은 [목록의 **28번 주제**](../28-goroutines-go-statement-cost-and-termination/)의 정본이다. 여기서는 명세 인용까지만 한다.

## 구현 세부사항 대 언어 보장

이 갈래에서 층을 가르는 질문은 「**누가 보장하나**」다.

| 사실 | 층 | 근거 |
|---|---|---|
| import 한 패키지가 먼저 초기화된다 | **명세 보장** | "the imported packages are initialized before initializing the package itself" |
| 의존이 없는 패키지끼리는 **import 경로 사전순** | **명세 보장** | "sorted by import path" · (5)절 실측 |
| 패키지 변수가 그 패키지의 `init` 보다 먼저 | **명세 보장** | "assigning initial values to all its package-level variables **followed by** calling all `init` functions" |
| 변수끼리는 **의존 순서**, 동점이면 선언 순서 | **명세 보장** | "earliest in declaration order and ready for initialization" · (3)절 실측 |
| 초기화가 **단일 고루틴에서 순차로** 돈다 | **명세 보장** | "happens in a single goroutine, sequentially" |
| `init` 을 이름으로 부를 수 없다 | **명세 보장** | "the identifier itself is not declared" · (금지 사례 ②) |
| 순환 import 가 금지된다 | **명세 보장** | "by construction, guarantees that there can be no cyclic initialization dependencies" |
| **여러 파일의 `init` 순서** | **빌드 도구** | "build systems are **encouraged** …" — (4)절에서 `go run` 으로 **뒤집었다** |
| `go build` 가 **파일 이름 사전순**으로 넘긴다 | **구현(go 명령)** | (4)절 첫 명령의 관찰 |
| 숨은 의존이 있을 때의 변수 순서 | **명세가 미정이라고 못 박음** | "the initialization order between those variables is **unspecified**" |
| `go list -deps` 가 62줄인 것 | **이 판의 관찰** | go1.27.1 의 표준 라이브러리 구성 |
| 패닉 스택의 `+0x…` | **구현(빌드 산출물)** | 같은 바이너리 3판 동일, 판이 바뀌면 바뀐다 |

★ **명세가 「unspecified」를 직접 쓴 자리가 하나 있다.** 인터페이스를 거친 참조는 의존 분석이 못 본다.

> … the variable `a` will be initialized after `b` but
> whether `x` is initialized before `b`, between `b` and `a`, or after `a`, and
> thus also the moment at which `sideEffect()` is called … is not specified.

즉 **「돌려 보니 이 순서더라」가 근거가 될 수 없는 자리**가 명세에 명시돼 있다.
이 문서는 그 모양의 코드를 예제로 쓰지 않았다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 상수·정적 표 만들기 | 패키지 변수 | 실패할 수 없고 순서가 안 걸린다 |
| 드라이버·코덱 **등록** | `init` + 쓰는 쪽에서 `_` import | 등록이 목적이라 반환값이 없다 |
| 설정 읽기·DB 접속·파일 열기 | **`main` 안에서 명시적으로** | 실패를 다룰 자리가 있어야 한다 |
| 초기화 순서를 내가 정하고 싶다 | `init` 하나 + 그 안에서 순서대로 호출 | 파일 순서에 기대지 않는다 |
| 첫 사용 시점까지 미루고 싶다 | `sync.Once`([목록의 **32번 주제**](../32-sync-mutex-rwmutex-waitgroup-once/)) | `init` 은 **무조건** 돈다 |
| 패키지 둘이 서로를 부른다 | 인터페이스를 소비자 쪽에([목록의 **20번 주제**](../20-interface-declaration-and-implicit-implementation/)) | 순환은 컴파일이 거부한다 |

판단 규칙 두 줄.

- **`init` 은 「다른 방법이 없을 때」 쓴다.** 부를 수 없는 함수라 테스트에서 끌 수가 없다.
- **순서에 기대야 한다면 이미 설계가 틀렸다.** 순서를 코드로 적어라.

## 핵심 문장

- `main` 의 첫 줄은 프로그램의 첫 줄이 아니다 — 의존 패키지 전부가 **변수 → `init`** 을 끝낸 뒤다.
- 패키지 **사이** 순서는 **명세 보장**(의존 + import 경로 사전순)이고,
  한 패키지 **안 파일 사이** 순서는 **빌드 도구의 예의**다. 층이 다르다.
- 그 차이는 말이 아니라 실측으로 갈렸다 — 같은 세 파일을 `go run` 에 **거꾸로 넘기니 `init` 순서가 뒤집혔다**.
- 패키지 변수는 **선언 순서가 아니라 의존 순서**로 초기화된다. 동점일 때만 선언 순서가 쓰인다.
- `import _` 는 「이름은 필요 없고 `init` 만 돌려라」다. **지우면 조용히 동작이 바뀐다.**
- 쓰지 않은 import 는 **에러**이고 `gofmt` 는 그것을 안 고친다.
- 초기화 순서를 실행 전에 읽는 창은 **`go list -deps`** 다 — 순서는 언제나 **의존 그래프**가 정한다.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 01번)
- [02번 주제](../02-variable-declarations-and-zero-values/)(변수 선언·제로값) —
  **초기화식을 안 적은 패키지 변수가 무엇이 되는가**는 거기
- [03번 주제](../03-constants-iota-and-untyped-constants/)(상수·`iota`) —
  **상수는 초기화 순서에 아예 안 들어간다**(컴파일 타임에 끝난다)는 것이 거기
- [목록의 **28번 주제**](../28-goroutines-go-statement-cost-and-termination/)(고루틴) — 「`main` 이 끝나면 다른 고루틴은 어떻게 되나」의 정본.
  여기서는 명세 인용까지만 했다
- [목록의 **32번 주제**](../32-sync-mutex-rwmutex-waitgroup-once/)(`sync`) — `init` 대신 `sync.Once` 로 미루는 방법의 정본
- 목록의 **40번 주제**(가시성·`internal`) — **그쪽은 대문자 하나가 만드는 공개 계약**,
  **여기는 패키지가 언제 켜지는가**다. 이름 규칙은 여기서 다루지 않는다
- 목록의 **41번 주제**(모듈·`go.mod`) — **그쪽은 import 경로가 어느 버전으로 풀리는가**,
  **여기는 풀린 다음의 초기화 순서**다
- [`../../../../../ops-patterns/19-graceful-shutdown/`](../../../../../ops-patterns/19-graceful-shutdown/) —
  **그쪽은 끝내는 쪽**, 여기는 **시작하는 쪽**이다

## 용어 풀이

- **패키지(package)** — 같은 디렉토리의 `.go` 파일 묶음. 컴파일과 초기화의 단위다.
- **모듈(module)** — `go.mod` 가 있는 트리 하나. import 경로의 접두사가 된다.
- **import 경로** — 모듈 경로 + 디렉토리 경로(`ex/alpha`). 초기화 순서의 정렬 키이기도 하다.
- **`init` 함수** — 인자·반환값 없는 `func init()`. 패키지당 여러 개, 호출 불가.
- **패키지 변수(package-level variable)** — 함수 밖에 선언된 변수. `init` 보다 먼저 초기화된다.
- **의존 순서(dependency order)** — 초기화식이 이름으로 참조하는 관계를 전이적으로 따른 순서.
- **이름 없는 import(`_`)** — 이름을 들여오지 않고 `init` 만 돌리는 import.
- **점 import(`.`)** — 대상 패키지의 이름을 지역 이름처럼 쓰는 import. 읽기가 나빠져 거의 안 쓴다.
- **순환 import** — 서로를 import 하는 관계. 컴파일 에러다.
- **위상 정렬(topological sort)** — 「먼저 와야 하는 것」을 앞에 놓는 정렬. `go list -deps` 의 출력 순서다.
- **`go list`** — 빌드 그래프를 조회하는 명령. 빌드하지 않고 의존 관계만 본다.
- **빌드 캐시(`GOCACHE`)** — 컴파일 산출물을 재사용하는 디렉토리. 이 문서의 실행은 전부 스크래치패드 캐시로 돌렸다.

---

## 더 들어가면

- `init` 은 **패키지당 개수 제한이 없고 한 파일 안에서도 여러 개** 둘 수 있다.
  (2)절의 `alpha` 가 그 예다 — 한 파일에 둘이고, 소스에 적힌 순서대로 돌았다.
- `go list -deps` 의 62줄 중 내가 쓴 것은 셋뿐이다. 나머지 59는 `fmt` 가 끌고 온 것이고,
  **그 59가 전부 내 패키지보다 먼저 초기화된다.** 「기동이 왜 이만큼 걸리나」를 볼 첫 자리가 여기다.
- 파일 이름 사전순은 **`.`(0x2E) < `_`(0x5F) < 숫자 < 대문자 < 소문자** 순의 바이트 비교다.
  (4)절에서 `t01c.go` 가 `t01c_1st.go` 보다 먼저인 이유가 이것이다.
- `import` 묶음 안의 줄 순서는 `gofmt` 가 정렬하므로 **손으로 바꿔도 되돌아온다.**
  (5)절 실측에서 `alfa` 와 `zulu` 의 순서를 import 문으로는 바꿀 수 없었다.
- 순환 import 에러는 **타입 검사 이전 단계**라, 순환이 있으면 다른 에러가 아예 안 보인다.
  순환부터 풀고 다시 빌드해야 한다.

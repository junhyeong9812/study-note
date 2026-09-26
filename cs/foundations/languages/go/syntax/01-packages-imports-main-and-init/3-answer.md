# go/syntax/01 — 패키지 선언·import·`main` 과 `init` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 손으로 옮겨 적은 블록은 없다.\
> 블록은 전부 `===== 소스: … =====` 로 소스를 먼저 싣는다 — **그대로 다시 던질 수 있게** 하기 위해서다.
> 모듈 이름은 `ex`, 빌드는 `go build -trimpath` 라 패닉 스택의 경로가 `ex/파일.go` 로 나온다.
> ★ **근거로 읽을 칸** — `init`·변수 초기화가 찍는 **순서**, 에러 문장 본문, `파일:줄:칸`, 종료 코드.
> **근거로 읽지 않을 칸** — `go list -deps` 의 표준 라이브러리 줄 수(판에 달렸다),
> 패닉 스택의 `+0x…` 오프셋(빌드 산출물에 달렸다).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 아홉 줄이 번호대로 찍힌다 — `alpha` 전부 → `beta` 전부 → `main`

**출력**

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

**왜 그런가**

- **패키지 단위로 뭉쳐서** 돈다. `alpha` 의 변수와 `init` 둘이 **전부 끝난 뒤에야** `beta` 가 시작한다.
- 4번 줄의 `alpha.A` 는 **1**이다. `beta` 의 변수 초기화식이 도는 시점에 `alpha` 는 이미 끝났다.
- 마지막 줄은 `alpha.A = 1 · beta.B = 2 · M = 3` — 각 `trace` 의 반환값이다.
- 내가 쓴 `main()` 은 **아홉 번째**다. 앞의 여덟 줄은 내가 부른 적이 없다.

```text
  패키지 하나가 도는 모양 (셋 다 같다)

    패키지 변수 전부 초기화
            ↓
    init 들을 소스 순서대로 호출
            ↓
    다음 패키지로
```

**명세가 약속하는 것은 어디까지인가**

- **패키지 사이 순서** — 약속이다.

  > Given the list of all packages, sorted by import path, in each step the first
  > uninitialized package in the list for which all imported packages (if any) are
  > already initialized is initialized.

- **변수 → `init`** 순서 — 약속이다.

  > The entire package is initialized by assigning initial values
  > to all its package-level variables followed by calling
  > all `init` functions …

- **`alpha` 안에서 `init #1` 이 `init #2` 보다 먼저** — 둘이 **한 파일 안**이라 소스 순서로 약속된다.
  파일이 둘로 갈리면 이야기가 달라진다(3번).

### 2. `b` → `a` → `c` — 선언 순서가 아니라 의존 순서다

**출력**

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

**왜 그런가**

- 첫 단계에서 「준비된」 변수는 `b` 와 `c` 둘이다. `a` 는 `b` 를 참조하므로 아직 아니다.
- 준비된 것 중 **선언 순서가 빠른 `b`** 가 선택된다.
- `b` 가 끝나면 `a` 도 준비된다. 이제 준비된 것은 `a`(1번째)와 `c`(3번째) — **`a` 가 이긴다.**
- 그래서 `c` 가 마지막이다. 선언 셋째가 실행 셋째인 것은 **우연**이다.

```text
  선언 순서 :  a      b      c
                |      |      |
  준비 여부 :  ✗(b)   ○      ○      → b 선택
               ○      끝     ○      → a 선택 (선언이 더 빠르다)
               끝     끝     ○      → c
```

**`a` 를 `trace("a", c+1)` 로 바꾸면**

```text
===== 소스: t01k.go =====
package main

import "fmt"

func trace(name string, v int) int {
	fmt.Printf("  초기화: %s = %d\n", name, v)
	return v
}

var a = trace("a", c+1)
var b = trace("b", 10)
var c = trace("c", 100)

func main() {
	fmt.Println("main:", a, b, c)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
  초기화: b = 10
  초기화: c = 100
  초기화: a = 101
main: 101 10 100
(exit 0)
```

- 순서가 **`b` → `c` → `a`** 로 바뀐다. `a` 가 `c` 를 기다리기 때문이다.
- 즉 순서를 정하는 것은 **참조 관계**이지 줄 번호가 아니다.

**명세가 쓰는 두 낱말**

> Initialization proceeds by repeatedly initializing the next package-level
> variable that is **earliest in declaration order** and **ready for initialization** …

「**ready for initialization**」이 먼저이고, 「**earliest in declaration order**」는 동점일 때의 타이브레이커다.

### 3. 빌드는 사전순, `go run` 은 적어 준 순서 — 같은 소스인데 뒤집힌다

**출력**

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

**왜 그런가**

- `go build` 는 패키지 디렉토리의 `.go` 파일을 **파일 이름 사전순**으로 컴파일러에 넘긴다.
  `t01c.go` → `t01c_1st.go` → `t01c_2nd.go`.\
  (`.` 은 0x2E, `_` 는 0x5F 라 `t01c.go` 가 `t01c_1st.go` 보다 앞이다.)
- `go run` 에 파일을 직접 나열하면 **그 순서 그대로** 넘어간다. 그래서 `init` 순서가 뒤집혔다.
- **소스는 한 글자도 안 바뀌었다.** 바뀐 것은 컴파일러에 파일을 넘긴 순서뿐이다.

**이 사실이 고치게 하는 말**

- 「`init` 순서는 보장된다」는 **절반만 맞다.** 정확히는 이렇다.
  - **한 파일 안**의 `init` 들 사이 순서 → **명세 보장**(소스에 적힌 순서).
  - **파일 사이** 순서 → **빌드 도구가 파일을 넘긴 순서**. 명세는 약속하지 않는다.

  > To ensure reproducible initialization behavior, build systems are **encouraged**
  > to present multiple files belonging to the same package in lexical file name
  > order to a compiler.

- 「**encouraged**」다 — must 가 아니다. 그래서 **파일 이름 바꾸기가 동작 변경이 될 수 있다.**

### 4. 두 줄 — `init` 은 돌고 이름은 안 들어온다

**출력**

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

**왜 그런가**

- `main` 은 `plugin` 의 이름을 하나도 쓰지 않는다. 그런데 `plugin` 의 `init` 이 **돌았다.**
- `import _` 는 「이름은 안 들여오고 **이 패키지를 프로그램에 넣어라**」만 말한다.
  프로그램에 들어온 패키지는 예외 없이 초기화되므로 `init` 이 돈다.

**`_ "ex/plugin"` 을 지우면**

```text
===== 소스: t01i.go =====
package main

import "fmt"

func main() { fmt.Println("main()") }
===== 소스: t01i_plugin.go =====
package plugin

import "fmt"

func init() { fmt.Println("plugin: init 이 돌았다") }

func Hello() string { return "안녕" }
===== 명령: go build -trimpath -o prog . && ./prog =====
main()
(exit 0)
```

- **컴파일은 그대로 성공하고 `plugin` 줄만 사라진다.** 에러도 경고도 없다.
- 이것이 이 주제의 대표적인 무음 실패다 — 「안 쓰는 줄 같아서 지웠다」가 동작을 바꾼다.

**`_` 를 떼고 `"ex/plugin"` 으로 바꾸면**

```text
===== 소스: t01j.go =====
package main

import (
	"fmt"

	"ex/plugin"
)

func main() { fmt.Println("main()") }
===== 소스: t01j_plugin.go =====
package plugin

import "fmt"

func init() { fmt.Println("plugin: init 이 돌았다") }

func Hello() string { return "안녕" }
===== 명령: go build -trimpath -o prog . =====
# ex
./t01j.go:6:2: "ex/plugin" imported and not used
(exit 1)
```

- 이번엔 **에러**다. 이름을 들여왔는데 안 썼기 때문이다. `_` 는 바로 그 에러를 끄는 표식이다.

**어디에 쓰나**

- 드라이버·코덱 **등록**이 표준 용도다 — `_ "github.com/lib/pq"` 처럼 `init` 에서
  `sql.Register` 를 부르게 해 두고, 호출부는 이름을 쓰지 않는다.

### 5. 둘 다 빌드 실패 — 하나는 「안 썼다」, 하나는 「그런 이름이 없다」

**출력**

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

**왜 그런가**

- 쓰지 않은 import 는 **경고가 아니라 에러**다(`exit 1`). Go 는 이걸 문체 문제로 보지 않는다.
- ★ 둘째 명령이 요점이다 — **`gofmt -l .` 은 아무 말도 안 한다**(출력 없음·종료 0).
  이 파일은 **포맷은 완벽한데 컴파일이 안 되는** 상태다.
  지워 주는 것은 `gofmt` 가 아니라 `goimports` 이고, 그건 이 툴체인에 없다.

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

- 에러는 **두 줄**이다. `init()` 호출 한 번과 `fmt.Println(init)` 의 이름 참조 한 번 —
  **`init` 이라는 이름을 쓴 자리마다** 한 줄씩 난다.
- 낱말이 「`init` is not a function」이 아니라 「**undefined: init**」이다.
  즉 **정의는 됐는데 이름이 존재하지 않는다.** 7번이 그 이야기다.

### 6. 세 줄 — 경로를 따라가다 제자리로 돌아온다

**출력**

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

**왜 그런가**

- 에러가 **import 경로를 한 줄씩 따라가며** 보여 준다.
  `ex` → `ex/one` → `ex/two` → **다시 `ex/one`**. 마지막 줄에서 제자리로 돌아오는 순간이 순환이다.
- 「`package ex`」 줄까지 세면 **네 줄**이고, 경로를 따라가는 줄은 셋이다.
- 종료 코드는 **1**이다. 컴파일이 아예 시작되지 않는다 — 이건 **타입 검사 이전** 층이다.

**이 금지가 보증하는 것**

> The importing of packages, by construction, guarantees that there
> can be no cyclic initialization dependencies.

- 초기화 순서가 **언제나 존재한다**는 보증이다. 순환이 가능하다면
  「A 가 먼저냐 B 가 먼저냐」에 답이 없는 프로그램이 생긴다.
- 그래서 Go 에는 「초기화 순환이면 런타임에 무엇이 나오나」라는 질문 자체가 없다.

### 7. 문법 제한이 아니라 **이름이 선언되지 않는 것**이다

**출력** (5번의 두 번째 블록과 같은 프로그램이다)

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

**왜 그런가**

- 명세의 원문이 정확히 그렇게 적는다.

  > In the package block, the `init` identifier can be used only to declare
  > `init` functions, yet **the identifier itself is not declared**.
  > Thus `init` functions cannot be referred to from anywhere in a program.

- 「부르는 것이 금지」가 아니라 「**그 이름이 없다**」이다. 그래서 에러가 `undefined` 다.
- 결과도 같아 보이지만 층이 다르다 — 주소를 잡는 것도, 함수 값으로 넘기는 것도, 전부 같은 이유로 막힌다.

**인자나 반환값을 붙이면**

```text
===== 소스: t01l.go =====
package main

import "fmt"

func init(n int) { fmt.Println(n) }

func init() error { return nil }

func main() { fmt.Println("main()") }
===== 명령: go build -trimpath -o prog . =====
# ex
./t01l.go:5:6: func init must have no arguments and no return values
./t01l.go:7:6: func init must have no arguments and no return values
(exit 1)
```

- 「**func init must have no arguments and no return values**」. 선언 자체가 거부된다.
- 그래서 `init` 은 **오류를 돌려줄 방법이 없다.** 실패하면 `panic` 하거나 `os.Exit` 뿐이다.

「**테스트에서 `init` 을 끄고 싶다**」

- **끌 수 없다.** 이름이 없으니 가려낼 수도, 대체할 수도 없다.
- 그래서 처방은 언제나 「`init` 에 넣지 않는 것」이다 — 명시 호출이나 `sync.Once`([목록의 **32번 주제**](../32-sync-mutex-rwmutex-waitgroup-once/)).

### 8. 셋은 명세 보장, 하나는 빌드 도구, 하나는 이 판의 관찰

**출력** (판정의 근거가 되는 블록)

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

**왜 그런가**

| | 주장 | 층 | 근거 |
|---|---|---|---|
| ① | import 한 패키지가 먼저 | **명세 보장** | "the imported packages are initialized before initializing the package itself" |
| ② | 변수가 `init` 보다 먼저 | **명세 보장** | "assigning initial values … **followed by** calling all `init` functions" |
| ③ | `a.go` 의 `init` 이 `b.go` 보다 먼저 | **빌드 도구** | "build systems are **encouraged** …" — 3번에서 `go run` 으로 뒤집었다 |
| ④ | 의존 없는 패키지는 import 경로 사전순 | **명세 보장** | "sorted by import path" |
| ⑤ | `go list -deps` 가 62줄 | **이 판의 관찰** | go1.27.1 의 `fmt` 의존 구성. 판이 바뀌면 바뀐다 |

- ③만 빌드 도구인 것이 이 주제의 핵심이다. **④는 보장이고 ③은 아니다** — 헷갈리기 쉬운 짝이다.
- ⑤는 재현되는 성질(「내 패키지보다 표준 라이브러리가 먼저 전부 초기화된다」)과
  한 판의 수(62)를 갈라 읽어야 한다. 결론은 성질 위에만 세운다.

### 9. import 경로의 사전순이 정한다 — import 문의 줄 순서가 아니다

**출력**

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

**왜 그런가**

- `alfa` 가 먼저 돈다. 두 패키지는 서로를 모르므로 의존 관계로는 순서가 안 정해진다.
- 그 자리를 채우는 것이 명세의 「**sorted by import path**」다.

  > Given the list of all packages, **sorted by import path**, in each step the first
  > uninitialized package in the list for which all imported packages … is initialized.

- **import 문에서 `zulu` 를 위에 써도 달라지지 않는다.** 게다가 `gofmt` 가 묶음 안을 정렬해
  손으로 바꿔 놔도 되돌아온다.
- 달라지게 하려면 **import 경로**를 바꿔야 한다(디렉토리 이름·모듈 경로).
  **패키지 이름을 바꾸는 것으로는 안 바뀐다** — 정렬 키는 경로이지 패키지 이름이 아니다.

### 10. `go list -deps` — 순서가 **위상 정렬**로 나온다

**출력**

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

**왜 그런가**

- `go list -deps` 는 의존을 **먼저 와야 하는 것부터** 늘어놓는다(위상 정렬).
  `ex/alpha` → `ex/beta` → `ex` 는 1번 실측의 순서와 **같다.**
- 둘째 명령(`go list -f`)은 각 패키지의 **직접 import** 를 보여 준다. 그래프를 손으로 그릴 수 있다.
- 셋째 명령 — 표준 라이브러리까지 세면 **62개**다. 내가 쓴 셋 말고 **59개가 먼저 초기화된다.**\
  ★ 62는 **이 판의 수**다. 재현되는 것은 「`fmt` 와 그 의존이 전부 내 패키지보다 먼저」라는 성질이다.
- 순서를 바꾸려면 **의존을 바꿔야** 한다. `init` 을 파일 위아래로 옮기는 것은 패키지 사이 순서에
  아무 영향이 없다.

> **위상 정렬(topological sort)** — 「먼저 와야 하는 것」을 앞에 놓는 정렬.\
> 예: `beta` 가 `alpha` 를 쓰면 `alpha` 가 반드시 앞에 온다.

### 11. 다른 주제와 잇기

**출력** — 없음(연결 문항).

**왜 그런가**

- **초기화식을 안 적은 패키지 변수** — 타입의 **제로값**이 된다(`0`·`""`·`false`·`nil`).
  정본은 [02번 주제](../02-variable-declarations-and-zero-values/)다.
  명세: "no explicit initialization is provided, the variable or value is given a default value."
- **상수(`const`)** — 이 순서에 **아예 들어가지 않는다.** 상수는 컴파일 타임에 값이 정해져
  초기화할 것이 없다. 정본은 [03번 주제](../03-constants-iota-and-untyped-constants/)이고,
  거기서 어셈블리로 「런타임에 계산이 남지 않는다」를 보인다.
- **첫 사용 시점에 한 번** — `sync.Once`. 정본은 [목록의 **32번 주제**](../32-sync-mutex-rwmutex-waitgroup-once/).
  `init` 은 **무조건** 돌지만 `Once` 는 **필요할 때만** 돈다.
- **`main` 이 돌아왔을 때의 다른 고루틴** — 기다리지 않고 끝난다.
  명세: "It does not wait for other (non-main) goroutines to complete."
  정본은 [목록의 **28번 주제**](../28-goroutines-go-statement-cost-and-termination/)다 — 이 문서에서는 **돌려 보지 않았고** 명세 인용까지만 했다.
- **순환 import 의 구조적 처방** — 인터페이스를 **쓰는 쪽(소비자)** 에 선언해 의존 방향을 한쪽으로 만든다.
  정본은 [목록의 **20번 주제**](../20-interface-declaration-and-implicit-implementation/).

---

## 실행 검증

| 실험 | 던진 명령 | 결과 | 문항 |
|---|---|---|---|
| 판 확인 | `go version` · `go env GOOS GOARCH GOVERSION` | `go1.27.1 linux/amd64` | 머리말 |
| 패키지 3개 초기화 순서 (`t01a`) | `go build -trimpath && ./prog` | 아홉 줄이 번호대로 | 1 |
| 변수 의존 순서 (`t01b`) | 〃 | `b` → `a` → `c` | 2 |
| 의존 대상을 `c` 로 바꿈 (`t01k`) | 〃 | `b` → `c` → `a` | 2 |
| 한 패키지 3파일 (`t01c`) | `go build` | 사전순 `t01c.go`→`_1st`→`_2nd` | 3 |
| 같은 3파일 (`t01c`) | `go run t01c_2nd.go t01c_1st.go t01c.go` | **순서가 뒤집힘** | 3 · 8 |
| 이름 없는 import (`t01e`) | `go build && ./prog` | `plugin` 의 `init` 이 돔 | 4 |
| import 를 지움 (`t01i`) | 〃 | **조용히 안 돔**(exit 0) | 4 |
| `_` 를 뗌 (`t01j`) | `go build` | `"ex/plugin" imported and not used` | 4 |
| 쓰지 않은 import (`t01f`) | `go build` | `"os" imported and not used` · exit 1 | 5 |
| 같은 파일 (`t01f`) | `gofmt -l .` | **출력 없음 · exit 0** | 5 |
| `init` 호출·참조 (`t01g`) | `go build` | `undefined: init` **두 줄** | 5 · 7 |
| `init` 에 인자·반환값 (`t01l`) | `go build` | `func init must have no arguments and no return values` 두 줄 | 7 |
| 순환 import (`t01d`) | `go build` | `import cycle not allowed` · exit 1 | 6 |
| 의존 없는 두 패키지 (`t01h`) | `go build && ./prog` | `alfa` → `zulu` | 9 |
| 빌드 그래프 (`t01a`) | `go list -deps` · `go list -f` · `wc -l` | 위상 정렬 · 직접 import · 62 | 8 · 10 |
| stdout/stderr 순서 (`t00buf`) | `./prog 2>&1` 3판 md5 | **3판 동일** — Go 는 stdout 을 버퍼링하지 않는다 | 머리말 |

**구현·환경에 달린 항목**(다시 찍을 자리)

| 항목 | 무엇에 달렸나 |
|---|---|
| **여러 파일의 `init` 순서** | **빌드 도구**가 파일을 넘긴 순서. 명세는 `encouraged` 까지만 |
| `go build` 의 사전순 | **go 명령의 구현**. 다른 빌드 도구는 다를 수 있다 |
| `go list -deps` 의 62 | **표준 라이브러리 구성**(go1.27.1). 판이 바뀌면 바뀐다 |
| 숨은(인터페이스 경유) 의존이 있을 때의 변수 순서 | **명세가 `unspecified` 라고 못 박았다.** 이 문서는 그 모양을 예제로 쓰지 않았다 |
| 패닉 스택의 `+0x…` | **빌드 산출물**. 같은 바이너리 3판은 동일(md5 동일) |
| `main` 종료와 고루틴 | **못 돌려 봤다** — 「안 돌려 봄」이 아니라 **이 주제의 범위 밖**이라 안 돌렸다(28번 주제) |

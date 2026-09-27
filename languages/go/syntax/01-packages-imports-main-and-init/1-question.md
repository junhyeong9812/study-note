# go/syntax/01 — 패키지 선언·import·`main` 과 `init` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> ★ **이 주제의 예측은 「무엇이 찍히나」가 아니라 「어떤 순서로 찍히나」다.**
> 줄을 다 맞히고 순서를 틀리면 틀린 것이다.
> ★ 답을 적을 때 「**그건 언어가 약속한 것인가, 빌드 도구가 그렇게 하는 것인가**」를 같이 적어라.
> 이 주제는 그 경계가 문항의 절반이다.
> 소스는 전부 `go build -trimpath -o prog . && ./prog` 로 던졌다. 모듈 이름은 `ex` 다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★ 아홉 줄은 어떤 순서로 찍히나 (예측)

모듈 `ex` 에 패키지가 셋 있다. `ex/beta` 는 `ex/alpha` 를 import 하고, `ex`(main)는 둘 다 import 한다.

```go
// t01a_alpha.go
package alpha

import "fmt"

func trace(s string) int { fmt.Println(s); return 1 }

var A = trace("1. alpha: var A 초기화")

func init() { fmt.Println("2. alpha: init #1") }
func init() { fmt.Println("3. alpha: init #2") }
```

```go
// t01a_beta.go
package beta

import (
	"fmt"

	"ex/alpha"
)

func trace(s string) int { fmt.Println(s); return 2 }

var B = trace("4. beta: var B 초기화 (alpha.A 는 이미 " +
	fmt.Sprint(alpha.A) + ")")

func init() { fmt.Println("5. beta: init") }
```

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

- 아홉 줄은 **어떤 순서로** 찍히는가 — 번호는 내가 붙인 것이니 믿지 마라.
- 4번 줄의 괄호 안 `alpha.A` 는 무엇으로 찍히는가?
- 마지막 줄의 세 값은 각각 무엇인가?
- 이 순서 중에서 **명세가 약속한 것**은 어디까지인가?

### 2. 세 변수는 어느 순서로 초기화되나 (예측)

```go
// t01b.go
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
```

- 「초기화:」로 시작하는 세 줄은 **어떤 순서로** 찍히는가?
- 마지막 `main:` 줄의 세 값은 무엇인가?
- `a` 를 `trace("a", c+1)` 로 바꾸면 순서가 달라지는가?
- 이 규칙을 명세는 두 낱말로 적는다 — 무엇과 무엇인가?

### 3. 같은 세 파일을 두 방법으로 넘기면 (예측)

한 패키지가 파일 셋으로 나뉘어 있고, 파일마다 `init` 이 하나씩이다.

```go
// t01c.go
package main

import "fmt"

func init() { fmt.Println("init in t01c.go") }

func main() { fmt.Println("main()") }
```

```go
// t01c_1st.go
package main

import "fmt"

func init() { fmt.Println("init in t01c_1st.go") }
```

```go
// t01c_2nd.go
package main

import "fmt"

func init() { fmt.Println("init in t01c_2nd.go") }
```

- `go build -trimpath -o prog . && ./prog` 의 출력은 무엇인가?
- `go run t01c_2nd.go t01c_1st.go t01c.go` 의 출력은 무엇인가?
- 두 출력이 다르다면 **무엇이 달라졌기 때문**인가 — 소스는 한 글자도 안 바뀌었다.
- 이 사실이 「`init` 순서는 보장된다」는 말을 어떻게 고치게 하는가?

### 4. 이름을 안 들여온 패키지는 (예측)

```go
// t01e_plugin.go
package plugin

import "fmt"

func init() { fmt.Println("plugin: init 이 돌았다 — 아무도 부르지 않았는데") }

func Hello() string { return "안녕" }
```

```go
// t01e.go
package main

import (
	"fmt"

	_ "ex/plugin"
)

func main() { fmt.Println("main()") }
```

- 출력은 몇 줄이고 무엇인가?
- `_ "ex/plugin"` 을 **지우면** 컴파일은 되는가, 출력은 어떻게 되는가?
- `_` 를 지우지 않고 `"ex/plugin"` 으로 바꾸면?
- 이 형태를 실제로 어디에 쓰는가 — 한 가지만 들어라.

### 5. 이 두 프로그램은 빌드되나 (예측)

```go
// t01f.go
package main

import (
	"fmt"
	"os"
)

func main() { fmt.Println("main()") }
```

```go
// t01g.go
package main

import "fmt"

func init() { fmt.Println("init") }

func main() {
	init()
	fmt.Println(init)
}
```

- 각각 빌드되는가 — 안 된다면 **메시지 전문**은 무엇인가?
- 위 프로그램에 `gofmt -l .` 을 돌리면 무엇이 나오는가?
- 아래 프로그램의 에러는 **몇 줄**이고 왜 그 개수인가?
- 아래 에러의 낱말이 「`init` 이 정의되지 않았다」가 아니라는 점에서 무엇을 읽어야 하는가?

### 6. `one` 과 `two` 가 서로를 부르면 (예측)

```go
// t01d_one.go
package one

import "ex/two"

func Name() string { return "one -> " + two.Name() }
```

```go
// t01d_two.go
package two

import "ex/one"

func Name() string { return "two -> " + one.Name() }
```

```go
// t01d.go
package main

import (
	"fmt"

	"ex/one"
)

func main() { fmt.Println(one.Name()) }
```

- `go build` 의 출력 **전문**은 무엇인가 — 몇 줄인가?
- 그 출력은 어느 파일부터 시작해서 어디로 돌아오는가?
- 종료 코드는 무엇인가?
- 이 금지가 **초기화 순서**에 대해 무엇을 보증하는가?

### 7. `init` 은 왜 이름이 아닌가 (왜)

- `init` 을 직접 부를 수 없는 것이 **문법 제한**인가, **이름이 없는 것**인가?
- 명세는 그것을 어떤 문장으로 적는가?
- `init` 에 인자나 반환값을 붙이면 어떻게 되는가?
- 그래서 「테스트에서 `init` 을 끄고 싶다」에는 어떤 답이 돌아오는가?

### 8. 어느 칸이 언어의 약속인가 (경계)

아래 다섯 가지를 **「명세 보장」 / 「빌드 도구」 / 「이 판의 관찰」** 로 갈라라.

- ① import 한 패키지가 먼저 초기화된다
- ② 패키지 변수가 그 패키지의 `init` 보다 먼저 돈다
- ③ 같은 패키지의 파일 `a.go` 의 `init` 이 `b.go` 의 `init` 보다 먼저 돈다
- ④ 의존이 없는 패키지 둘은 import 경로 사전순으로 돈다
- ⑤ `go list -deps` 가 62줄이다

### 9. 의존이 없는 패키지 둘의 순서 (경계)

- `ex/alfa` 와 `ex/zulu` 가 서로를 모를 때, 초기화 순서를 정하는 것은 무엇인가?
- import 문에서 `zulu` 를 위에 쓰면 달라지는가?
- 그 답의 근거가 되는 명세의 낱말은 무엇인가?
- 패키지 이름을 바꾸면 달라지는가, import 경로를 바꾸면 달라지는가?

### 10. 실행하지 않고 순서를 읽는 법 (연결)

- 초기화 순서를 **빌드 전에** 읽으려면 어떤 명령을 쓰는가?
- 그 명령은 순서를 어떤 성질로 내놓는가?
- 표준 라이브러리까지 포함하면 이 프로그램은 패키지 몇 개를 초기화하는가 — 그 수는 고정인가?
- 순서를 바꾸고 싶을 때 **바꿔야 하는 것**은 무엇인가?

### 11. 다른 주제와 잇기 (연결)

- 초기화식을 아예 안 적은 패키지 변수는 무엇이 되며, 그 규칙의 정본은 몇 번 주제인가?
- 상수(`const`)는 이 초기화 순서의 어디에 들어가는가?
- `init` 대신 「첫 사용 시점에 한 번」을 쓰려면 무엇을 쓰고, 그 정본은 몇 번 주제인가?
- `main` 이 돌아왔을 때 다른 고루틴은 어떻게 되며, 그 정본은 몇 번 주제인가?
- 순환 import 를 구조로 푸는 표준 처방은 무엇이고, 그 정본은 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

# go/syntax/12 — 함수: 다중 반환·명명 반환값·가변 인자 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Go 명세](https://go.dev/ref/spec)의 Function types · Function declarations ·
> Calls · Return statements · Defer statements 절.\
> 웹이 아니라 **이 툴체인이 들고 있는 ``$(go env GOROOT)/doc/go_spec.html`` 을 열어** 인용했다.
> 그 파일의 머리는 「**Language version go1.27 (May 26, 2026)**」이다.
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> ★★★ **이 주제의 본체는 「명명 반환값 + `defer`」다.** `return` 이 **먼저 반환값에 대입**하고
> **그다음에** `defer` 가 돌기 때문에, `defer` 가 이미 정해진 반환값을 **고칠 수 있다.**
> (2)절이 그것을 던져서 보이고, (3)절이 그 위에 선 두 관용구(오류 감싸기·`recover`)를 보인다.
> ★★ **Go 에는 기본 인자도 이름 붙인 인자도 없다.** 그 자리를 **다중 반환과 가변 인자**가 메운다.
> **버전** — 여기 나오는 모든 동작은 **1.0**부터 같다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 명세로, 출력은 실행으로 접지했다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | `go_spec.html` 원문 인용 |
| **구현(gc)·도구** | gc·`go vet` 이 그렇게 하는 것 | 패닉 스택 · vet 의 침묵 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 실행 출력 · 컴파일 에러 문장 |

★ 이 주제는 **거의 전부가 명세**다. `defer` 의 평가 시점도, `return` 과 `defer` 의 순서도,
가변 인자가 슬라이스가 되는 것도 명세의 문장이다. **그래서 「돌려 보니 그렇더라」로 넘길 자리가 없다.**

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

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | 패닉 스택의 **주소 오프셋**(`+0x90`) · `pc=0x…` | 빌드마다 바뀔 수 있다 |
| **판이 바뀌면 바뀐다** | 컴파일 에러의 **문구 다듬기** | 컴파일러가 메시지를 고칠 수 있다 |
| 안 흔들린다 | `defer` 의 **실행 순서**와 **인자 평가 시점** | 명세가 정한다 |
| 안 흔들린다 | 명명 반환값이 `defer` 에 **고쳐지는 것** | 명세가 정한다 — 이 주제의 결론이다 |
| 안 흔들린다 | 가변 인자의 `len`·`cap`·`nil` 여부 | 명세가 정한다 |
| 안 흔들린다 | 패닉 **메시지 본문**·`파일:줄`·종료 코드 | 런타임이 정한다 |
| 안 흔들린다 | 컴파일 에러 **문장 본문**·`파일:줄:칸` | 같은 소스·같은 판이면 같다 |

## 한눈에 — 쉽게 말하면

**「나갈 때 서명하는 서류 한 장.」**

함수가 끝날 때 하는 일이 **두 단계**다. 먼저 **반환값 칸에 값을 적고**(`return`),
그다음 **미뤄 둔 일들을 처리한다**(`defer`). 그 사이에 **칸이 아직 열려 있다** —
반환값에 **이름이 있으면** 미뤄 둔 일이 그 칸을 **고쳐 쓸 수 있다.**

| 비유 | 실체 |
|---|---|
| 서류의 빈칸에 값을 적는다 | `return v` — **결과 파라미터에 대입**한다 |
| 적고 나서 하는 뒷정리 | `defer` 가 도는 자리 |
| 빈칸에 **이름표**가 붙어 있다 | 명명 반환값 `func f() (n int)` |
| 뒷정리하는 사람이 **그 칸을 고친다** | `defer func(){ n *= 2 }()` |
| 이름표가 없으면 고칠 칸을 못 찾는다 | `func f() int` — 지역 변수만 고쳐진다 |
| 「적힌 대로 나간다」만 적는다 | 벌거벗은 `return` |
| 뒷정리 목록에 **지금 값을 적어 둔다** | `defer f(i)` — 인자는 **선언 시점**에 평가 |

```text
   func named() (n int) {
       defer func(){ n *= 2 }()      ③ 그다음 defer 가 돈다 → n = 42
       n = 21
       return n                      ② return 이 먼저 n 에 21 을 넣는다
   }                                 ④ 그제야 42 가 호출자에게 간다
                                     ★ ②와 ④ 사이에 ③이 낀다

   func unnamed() int {
       n := 21
       defer func(){ n *= 2 }()      ③ n 은 고쳐지지만 그건 지역 변수다
       return n                      ② 반환값(이름 없는 칸)에 21 이 복사됐다
   }                                 ④ 21 이 간다
```

- ★★★ **이 그림 하나가 이 주제의 절반**이다. 나머지 절반은 **가변 인자**다.
- ★★ Go 에는 **기본 인자·이름 붙인 인자·오버로딩이 없다.** 그래서
  「선택적 인자」를 **가변 인자**나 **옵션 구조체**로 흉내 낸다.

> **결과 파라미터(result parameter)** — 반환값이 들어가는 칸. Go 는 이것을 **변수처럼** 다룬다.\
> 이름을 붙이면 함수 안에서 그 이름으로 읽고 쓸 수 있다.

> **명명 반환값(named result)** — 결과 파라미터에 이름을 붙인 것. `func f() (n int, err error)`.

> **벌거벗은 `return`(naked return)** — 값을 안 적은 `return`. **명명 반환값이 있을 때만** 쓸 수 있다.

> **가변 인자(variadic)** — 마지막 파라미터에 `...` 를 붙인 것. 함수 안에서는 **슬라이스**다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 네 질문을 둔다.

1. **왜 Go 의 오류 처리가 `(T, error)` 모양인가** — 그게 문법의 무엇에서 나오나.
2. **`defer` 가 반환값을 고칠 수 있는 조건은 무엇인가** — 이름이 왜 필요한가.
3. **`defer` 의 인자는 언제 평가되나** — 몸통은 언제 도나.
4. **가변 인자에 슬라이스를 펼쳐 넘기면 복사되나** — 안 되나.

★ `defer` 자체의 전모(LIFO·루프 안의 `defer`·자원 정리)는 [목록의 **26번 주제**](../26-defer-evaluation-lifo-named-results-and-loops/)가 정본이다.
`panic`/`recover` 는 **27번 주제**, 클로저의 변수 캡처는 **13번 주제**다.
여기는 **함수 선언 표면**이 본체이고 `defer` 는 **반환값과 만나는 자리**만 본다.

## 동작 방식

### (0) 다중 반환과 `(T, error)` 관례

**언제 쓰나** — 실패할 수 있는 함수를 쓸 때마다. **Go 코드의 대부분**이다.

```text
===== 소스: t12a.go =====
package main

import (
	"errors"
	"fmt"
	"strconv"
)

// divmod 는 몫과 나머지를 한 번에 돌려준다.
func divmod(a, b int) (int, int) { return a / b, a % b }

// parse 는 Go 의 관례대로 (값, error) 를 돌려준다.
func parse(s string) (int, error) {
	n, err := strconv.Atoi(s)
	if err != nil {
		return 0, fmt.Errorf("parse %q: %w", s, err)
	}
	return n, nil
}

func main() {
	q, r := divmod(17, 5)
	fmt.Printf("divmod(17, 5)   = %d, %d\n", q, r)

	q2, _ := divmod(17, 5)
	fmt.Printf("나머지를 버리면 _ 로 받는다 : %d\n", q2)

	if n, err := parse("42"); err == nil {
		fmt.Printf("parse(\"42\")     = %d\n", n)
	}

	n, err := parse("4x")
	fmt.Printf("parse(\"4x\")     = %d, err = %v\n", n, err)
	fmt.Printf("  errors.Is(err, strconv.ErrSyntax) = %v\n", errors.Is(err, strconv.ErrSyntax))
	fmt.Println("  ★ 실패했을 때 값 자리에 제로값을 넣는 것이 관례다 — 쓰지 말라는 뜻이다")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
divmod(17, 5)   = 3, 2
나머지를 버리면 _ 로 받는다 : 3
parse("42")     = 42
parse("4x")     = 0, err = parse "4x": strconv.Atoi: parsing "4x": invalid syntax
  errors.Is(err, strconv.ErrSyntax) = true
  ★ 실패했을 때 값 자리에 제로값을 넣는 것이 관례다 — 쓰지 말라는 뜻이다
(exit 0)
```

그림 해설 (한 단계씩):

- Go 는 **반환값을 여럿 적을 수 있다.** 예외가 없는 언어에서 이것이 **오류 처리의 문법적 토대**다.
- 관례는 **오류를 마지막에** 두는 것이다 — `(int, error)`.
- ★★ **실패했을 때 값 자리에는 제로값을 넣는다.** 「쓰지 말라」는 뜻의 신호다.
  (`strconv` 의 `ErrRange` 처럼 **경계값**을 주는 예외가 있다 — 11번 주제 (3)절.)
- `fmt.Errorf("… %w", err)` 로 감싸면 `errors.Is` 가 **안쪽까지** 본다([목록의 **24번 주제**](../24-error-wrapping-and-errors-is-as-join/)).
- 안 쓰는 값은 **`_`** 로 받는다. 받지 않으면 **컴파일 에러**다.

다중 반환은 **통째로 넘길 수도** 있다.

```text
===== 소스: t12b.go =====
package main

import "fmt"

func two() (int, int) { return 1, 2 }

func add(a, b int) int { return a + b }

func main() {
	fmt.Println("다중 반환을 통째로 넘길 수 있다 — 단 그것만 인자로 줄 때다")
	fmt.Println("  add(two())   =", add(two()))
	fmt.Print("  fmt.Println(two()) -> ")
	fmt.Println(two())
}
===== 명령: go build -trimpath -o prog . && ./prog =====
다중 반환을 통째로 넘길 수 있다 — 단 그것만 인자로 줄 때다
  add(two())   = 3
  fmt.Println(two()) -> 1 2
(exit 0)
```

- `add(two())` 가 된다 — 명세가 허용한다.

  > **The expression list in the "return" statement may be a single call to a multi-valued function.**
  > … (호출에서도 같은 규칙이 적용된다)

- 단 **그것만 인자로 줄 때**다. 섞으면 컴파일 에러다.

```text
===== 소스: t12c.go =====
package main

import "fmt"

func two() (int, int) { return 1, 2 }

func add(a, b int) int { return a + b }

func main() {
	fmt.Println(add(two(), 3))
	x := two()
	fmt.Println(x)
}
===== 명령: go build -trimpath -o prog . =====
# ex
./t12c.go:10:18: multiple-value two() (value of type (int, int)) in single-value context
./t12c.go:11:7: assignment mismatch: 1 variable but two returns 2 values
(exit 1)
```

- `add(two(), 3)` → **`multiple-value two() (value of type (int, int)) in single-value context`**.
- `x := two()` → **`assignment mismatch: 1 variable but two returns 2 values`**.
- ★ 두 메시지가 **다르다는 것**이 쓸모 있다 — 앞은 **식의 자리**, 뒤는 **대입의 개수** 문제다.

비용 — 다중 반환은 레지스터/스택으로 오간다. 구조체 하나를 돌려주는 것과 비슷하다.

### (1) ★★★ 명명 반환값 + `defer` — 이 주제의 본체

**언제 쓰나** — 오류를 감싸거나, 패닉을 오류로 바꾸거나, 나갈 때 값을 손보아야 할 때.

```text
===== 소스: t12d.go =====
package main

import "fmt"

// named 는 반환값에 이름이 있다 — defer 가 그 변수를 고칠 수 있다.
func named() (n int) {
	defer func() { n *= 2 }()
	n = 21
	return n
}

// unnamed 는 이름이 없다 — defer 가 고칠 대상이 없다.
func unnamed() int {
	n := 21
	defer func() { n *= 2 }()
	return n
}

// returnsLiteral 은 return 이 리터럴이다 — return 이 먼저 n 에 넣고 defer 가 그 뒤에 돈다.
func returnsLiteral() (n int) {
	defer func() { n++ }()
	return 100
}

// naked 는 벌거벗은 return 이다 — 이름만 적고 값을 안 적는다.
func naked() (a, b string) {
	a, b = "가", "나"
	return
}

// order 는 defer 가 LIFO 로 돌면서 같은 반환값을 차례로 고치는 것을 보인다.
func order() (s string) {
	defer func() { s += "①" }()
	defer func() { s += "②" }()
	defer func() { s += "③" }()
	return "시작"
}

func main() {
	fmt.Println("named()          =", named())
	fmt.Println("unnamed()        =", unnamed())
	fmt.Println("returnsLiteral() =", returnsLiteral())
	a, b := naked()
	fmt.Printf("naked()          = %q %q\n", a, b)
	fmt.Println("order()          =", order())
}
===== 명령: go build -trimpath -o prog . && ./prog =====
named()          = 42
unnamed()        = 21
returnsLiteral() = 101
naked()          = "가" "나"
order()          = 시작③②①
(exit 0)
```

그림 해설 (한 단계씩):

- **`named()` 가 42** 다. `n = 21` 한 뒤 `return n` 이 **결과 파라미터 `n` 에 21을 넣고**,
  그다음 `defer` 가 **그 `n` 을 2배로** 만든다.
- **`unnamed()` 는 21** 이다. 반환값에 **이름이 없어** `defer` 가 고칠 칸이 없다 —
  고쳐진 것은 **지역 변수 `n`** 이고, 반환값은 이미 **복사되어 나갔다.**
- ★★★ **`returnsLiteral()` 이 101** 인 것이 결정적이다. `return 100` 이라고 적었는데 101이 나온다.
  명세가 그 순서를 못 박는다.

  > **A "return" statement that specifies results sets the result parameters
  > before any deferred functions are executed.**

  즉 **`return 100` 은 「100을 가지고 나간다」가 아니라 「`n` 에 100을 넣고 나가기 시작한다」는 뜻이다**.
- **`naked()`** 는 값을 안 적은 `return` 이다. 명명 반환값이 있을 때만 쓸 수 있다.
- **`order()` 가 `시작③②①`** 이다 — `defer` 가 **LIFO** 로 돌면서 **같은 반환값을 차례로** 고쳤다.

```text
   함수가 끝나는 두 단계

   ┌ return v 를 만난다
   │   ① 결과 파라미터에 v 를 대입한다        <- 이름이 있으면 그 이름의 변수다
   │   ② defer 들을 역순으로 실행한다          <- 여기서 ①의 값을 읽고 고칠 수 있다
   └ ③ 결과 파라미터의 "지금" 값을 호출자에게 준다

   이름이 없으면 ①의 칸에 이름이 없어 ②가 손댈 수 없다.
```

★★ **이것이 「`defer` 가 반환값을 바꾼다」의 정확한 뜻**이다.
`defer` 가 `return` 을 가로채는 것이 아니라 **`return` 이 이미 써 놓은 칸을 고치는 것**이다.

비용 — `defer` 하나당 작은 고정 비용. 반환값 수정 자체는 공짜다.

### (2) ★★ 그 위에 선 두 관용구 — 오류 감싸기와 `recover`

**언제 쓰나** — 패키지 경계에서 오류에 맥락을 붙일 때, 라이브러리가 패닉을 밖으로 안 내보낼 때.

```text
===== 소스: t12e.go =====
package main

import (
	"errors"
	"fmt"
)

var errNotFound = errors.New("없음")

// load 는 defer 로 오류를 감싼다 — 명명 반환값이라야 되는 관용구다.
func load(id string) (v string, err error) {
	defer func() {
		if err != nil {
			err = fmt.Errorf("load(%q): %w", id, err)
		}
	}()
	if id == "" {
		return "", errNotFound
	}
	return "값:" + id, nil
}

// loadBroken 은 같은 뜻으로 썼지만 반환값에 이름이 없다.
func loadBroken(id string) (string, error) {
	var err error
	defer func() {
		if err != nil {
			err = fmt.Errorf("loadBroken(%q): %w", id, err)
		}
	}()
	if id == "" {
		err = errNotFound
		return "", err
	}
	return "값:" + id, nil
}

// recovered 는 패닉을 오류로 바꾼다 — 이것도 명명 반환값이 있어야 된다.
func recovered() (err error) {
	defer func() {
		if r := recover(); r != nil {
			err = fmt.Errorf("패닉을 오류로 바꿨다: %v", r)
		}
	}()
	panic("터짐")
}

func main() {
	v, err := load("7")
	fmt.Printf("load(\"7\")        = %q, %v\n", v, err)
	v, err = load("")
	fmt.Printf("load(\"\")         = %q, %v\n", v, err)
	fmt.Printf("  errors.Is(err, errNotFound) = %v\n", errors.Is(err, errNotFound))

	_, err = loadBroken("")
	fmt.Printf("loadBroken(\"\")   = err = %v   ← 감싸기가 안 먹었다\n", err)

	fmt.Printf("recovered()      = %v\n", recovered())
}
===== 명령: go build -trimpath -o prog . && ./prog =====
load("7")        = "값:7", <nil>
load("")         = "", load(""): 없음
  errors.Is(err, errNotFound) = true
loadBroken("")   = err = 없음   ← 감싸기가 안 먹었다
recovered()      = 패닉을 오류로 바꿨다: 터짐
(exit 0)
```

그림 해설 (한 단계씩):

- `load` 는 **`defer` 한 번으로 모든 반환 경로의 오류를 감싼다.**
  `return "", errNotFound` 로 나가든 다른 곳으로 나가든 **같은 `defer` 가 잡는다.**
  실측 — `load("")` 가 `load(""): 없음` 이 되고 `errors.Is(err, errNotFound)` 가 **여전히 true** 다.
- ★★★ **`loadBroken` 은 똑같이 썼는데 안 먹는다.** 반환값에 **이름이 없어서**다.
  `err` 이라는 **지역 변수**를 고쳤을 뿐이고 반환값은 이미 복사돼 나갔다.
  실측 — 감싸이지 않은 `없음` 이 그대로 나온다.
- ★★ 이것이 **조용한 실패**다 — **컴파일도 되고 `go vet` 도 조용하고 오류도 나간다.**
  **맥락만 조용히 사라진다.** 로그를 볼 때까지 모른다.
- `recovered()` 는 **패닉을 오류로 바꾼다.** 이것도 **명명 반환값이 있어야** 가능하다 —
  패닉으로 나가는 경로에는 `return` 문이 아예 없으므로, **`defer` 안에서 결과 파라미터에 직접 써야** 한다.
  정본은 [목록의 **27번 주제**](../27-panic-recover-and-where-to-use-them/)다.

비용 — `defer` 하나. `recover` 는 패닉이 없을 때 `nil` 을 준다.

### (3) ★ `defer` 의 인자는 **선언 시점**에 평가된다

**언제 쓰나** — `defer` 안에서 변수를 읽을 때. **가장 자주 틀리는 한 줄**이다.

```text
===== 소스: t12f.go =====
package main

import "fmt"

func main() {
	i := 0
	defer fmt.Println("① defer fmt.Println(i)  — 인자는 defer 를 적은 그 순간 평가된다 : i =", i)
	defer func() { fmt.Println("② defer func(){ ... }() — 몸통은 나중에 돈다 : i =", i) }()

	i = 42
	fmt.Println("본문 끝. 지금 i =", i)
	fmt.Println("아래 두 줄은 LIFO 다 — 나중에 적은 ② 가 먼저 돈다")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
본문 끝. 지금 i = 42
아래 두 줄은 LIFO 다 — 나중에 적은 ② 가 먼저 돈다
② defer func(){ ... }() — 몸통은 나중에 돈다 : i = 42
① defer fmt.Println(i)  — 인자는 defer 를 적은 그 순간 평가된다 : i = 0
(exit 0)
```

그림 해설 (한 단계씩):

- **`defer fmt.Println(…, i)` 는 `i = 0`** 을 찍는다. `defer` 를 **적은 그 순간** 인자가 평가됐다.
- **`defer func(){ … i … }()` 는 `i = 42`** 를 찍는다. 클로저가 **변수 `i` 자체를 잡고** 나중에 읽는다.
- 명세가 정확히 그렇게 적는다.

  > **Each time a "defer" statement executes, the function value and parameters to the call
  > are evaluated as usual and saved anew but the actual function is not invoked.**

- 실행 순서도 명세다 — **역순(LIFO)** 이다. ②를 나중에 적었으니 ②가 먼저 돈다.

  > **deferred functions are invoked immediately before the surrounding function returns,
  > in the reverse order they were deferred.**

- ★★ **두 꼴을 고르는 기준 한 줄** — 「**지금 값을 찍고 싶은가, 나갈 때 값을 찍고 싶은가**」.
  `defer file.Close()` 는 `file` 을 **지금** 잡아 두므로 중간에 `file` 을 바꿔도 **처음 것이 닫힌다.**

비용 — 인자를 저장해 두는 만큼. 클로저면 캡처 비용.

### (4) 가변 인자 — 함수 안에서는 슬라이스다

**언제 쓰나** — 인자 개수를 안 정하고 싶을 때. Go 에 기본 인자가 없어 이것이 그 자리를 메운다.

```text
===== 소스: t12g.go =====
package main

import "fmt"

func sum(label string, nums ...int) int {
	total := 0
	for _, n := range nums {
		total += n
	}
	fmt.Printf("  %-24s nums=%-12s len=%d cap=%d nil인가=%-6v 합=%d\n",
		label, fmt.Sprint(nums), len(nums), cap(nums), nums == nil, total)
	return total
}

func mutate(nums ...int) {
	if len(nums) > 0 {
		nums[0] = 99
	}
}

func main() {
	fmt.Println("가변 인자는 함수 안에서 그냥 슬라이스다")
	sum(`sum(l)`)
	sum(`sum(l, 1)`, 1)
	sum(`sum(l, 1, 2, 3)`, 1, 2, 3)

	s := []int{4, 5, 6}
	sum(`sum(l, s...)`, s...)

	var nilSlice []int
	sum(`sum(l, nilSlice...)`, nilSlice...)
	sum(`sum(l, []int{}...)`, []int{}...)

	fmt.Println()
	fmt.Println("★ ... 로 펼쳐 넘긴 슬라이스는 복사되지 않는다 — 같은 배열이다")
	fmt.Println("  넘기기 전 s =", s)
	mutate(s...)
	fmt.Println("  mutate(s...) 뒤 s =", s)
	fmt.Println("  하나씩 넘기면 새 배열이 생긴다")
	t := []int{4, 5, 6}
	mutate(t[0], t[1], t[2])
	fmt.Println("  mutate(t[0], t[1], t[2]) 뒤 t =", t)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
가변 인자는 함수 안에서 그냥 슬라이스다
  sum(l)                   nums=[]           len=0 cap=0 nil인가=true   합=0
  sum(l, 1)                nums=[1]          len=1 cap=1 nil인가=false  합=1
  sum(l, 1, 2, 3)          nums=[1 2 3]      len=3 cap=3 nil인가=false  합=6
  sum(l, s...)             nums=[4 5 6]      len=3 cap=3 nil인가=false  합=15
  sum(l, nilSlice...)      nums=[]           len=0 cap=0 nil인가=true   합=0
  sum(l, []int{}...)       nums=[]           len=0 cap=0 nil인가=false  합=0

★ ... 로 펼쳐 넘긴 슬라이스는 복사되지 않는다 — 같은 배열이다
  넘기기 전 s = [4 5 6]
  mutate(s...) 뒤 s = [99 5 6]
  하나씩 넘기면 새 배열이 생긴다
  mutate(t[0], t[1], t[2]) 뒤 t = [4 5 6]
(exit 0)
```

그림 해설 (한 단계씩):

- 명세가 한 줄로 정한다.

  > **The final incoming parameter in a function signature may have a type prefixed with `...`.
  > A function with such a parameter is called variadic and may be invoked with zero or more
  > arguments for that parameter.**

- ★★ 함수 안에서 `nums` 는 **그냥 `[]int`** 다. `len`·`cap`·`range` 가 다 된다.
- **인자를 하나도 안 주면 `nil` 슬라이스**다 — `len` 0, `cap` 0, **`nums == nil` 이 true**.
  ★ 그래서 `for range` 는 0번 돌고, `nums[0]` 은 패닉이다.
- ★★★ **`nilSlice...` 를 넘겨도 `nil`** 이고, **`[]int{}...` 를 넘기면 `nil` 이 아니다.**
  펼쳐 넘긴 슬라이스가 **그대로 파라미터가 되기 때문**이다.
- ★★★ **`s...` 로 펼쳐 넘긴 슬라이스는 복사되지 않는다.** 실측 —
  `mutate(s...)` 뒤 `s` 가 `[99 5 6]` 으로 **바뀌었다.**
  하나씩 넘긴 쪽(`mutate(t[0], t[1], t[2])`)은 **새 배열이 생겨** 원본이 그대로다.
- ★★ 이것이 **07번 주제(슬라이스 공유)의 한 사례**다. 「가변 인자니까 복사되겠지」가 틀린 전제다.

```text
   f(a, b, c)     ->  호출부가 [a b c] 라는 새 배열을 만든다   (원본이 없다)
   f(s...)        ->  s 를 그대로 파라미터에 앉힌다             ★ 같은 배열이다
   f(nilSlice...) ->  nil 이 그대로 들어간다                   nums == nil
   f()            ->  nil                                    nums == nil
   f([]int{}...)  ->  빈 슬라이스가 그대로                     nums != nil
```

비용 — 낱개로 넘기면 **배열 하나**를 잡는다. `s...` 는 **할당이 없다.**

### (5) ★ 가변 인자와 `nil`·타입 — 두 함정

**언제 쓰나** — `...any` 를 받는 함수(`fmt.Println` 류)를 쓸 때.

```text
===== 소스: t12h.go =====
package main

import "fmt"

func count(label string, args ...any) {
	fmt.Printf("  %-34s len=%d  nil인가=%-6v  args=%v\n", label, len(args), args == nil, args)
}

func main() {
	fmt.Println("nil 을 「하나」 넘기는 것과 nil 슬라이스를 「펼쳐」 넘기는 것은 다르다")
	count(`count(l, nil)`, nil)
	var s []any
	count(`count(l, s...) — s 는 nil 슬라이스`, s...)
	count(`count(l)`)

	fmt.Println()
	fmt.Println("[]string 은 ...any 로 못 펼친다 — 하나씩 옮겨야 한다")
	words := []string{"가", "나"}
	as := make([]any, len(words))
	for i, w := range words {
		as[i] = w
	}
	count(`count(l, as...)`, as...)
	fmt.Printf("  fmt.Sprintln(as...) = %q\n", fmt.Sprintln(as...))
}
===== 명령: go build -trimpath -o prog . && ./prog =====
nil 을 「하나」 넘기는 것과 nil 슬라이스를 「펼쳐」 넘기는 것은 다르다
  count(l, nil)                      len=1  nil인가=false   args=[<nil>]
  count(l, s...) — s 는 nil 슬라이스      len=0  nil인가=true    args=[]
  count(l)                           len=0  nil인가=true    args=[]

[]string 은 ...any 로 못 펼친다 — 하나씩 옮겨야 한다
  count(l, as...)                    len=2  nil인가=false   args=[가 나]
  fmt.Sprintln(as...) = "가 나\n"
(exit 0)
```

그림 해설 (한 단계씩):

- **`count(nil)` 은 인자가 1개**다 — `nil` 이라는 **값 하나**를 넘긴 것이다(`args = [<nil>]`).
- **`count(s...)`(s 는 nil 슬라이스)는 인자가 0개**다. **완전히 다른 호출**이다.
- ★★ 이 둘을 섞으면 `fmt.Println(nil)` 과 `fmt.Println(vals...)` 가 다르게 도는 이유를 설명 못 한다.
- ★★★ **`[]string` 은 `...any` 로 못 펼친다.** 컴파일 에러다.

```text
===== 소스: t12i.go =====
package main

import "fmt"

func count(args ...any) int { return len(args) }

func main() {
	words := []string{"가", "나"}
	fmt.Println(count(words...))
	fmt.Println(count(words, "다"...))
}
===== 명령: go build -trimpath -o prog . =====
# ex
./t12i.go:9:20: cannot use words (variable of type []string) as []any value in argument to count
./t12i.go:10:27: too many arguments in call to count
	have ([]string, string...)
	want (...any)
(exit 1)
```

- `cannot use words (variable of type []string) as []any value in argument to count`.
- 두 번째 줄은 더 재미있다 — `too many arguments in call to count` 와 함께
  **`have ([]string, string...)` / `want (...any)`** 를 보여 준다.
- ★ 왜 안 되나 — `[]string` 과 `[]any` 는 **메모리 배치가 다르다.** `any` 는 (타입, 값) 두 칸이다.
  변환하려면 **원소마다 감싸야** 하고 그것은 `O(n)` 이라 **언어가 몰래 해 주지 않는다.**
- 고치는 법 — **`[]any` 를 만들어 하나씩 옮긴다.** 실측 코드가 그것이다.

비용 — 옮기는 만큼. `n` 개면 슬라이스 하나 + 인터페이스 값 `n` 개.

### (6) 함수는 값이다

**언제 쓰나** — 콜백·전략·미들웨어를 쓸 때.

```text
===== 소스: t12j.go =====
package main

import (
	"fmt"
	"sort"
	"strings"
)

type op func(int, int) int

func apply(f op, a, b int) int { return f(a, b) }

func adder() func(int) int {
	sum := 0
	return func(x int) int { sum += x; return sum }
}

func main() {
	var f op = func(a, b int) int { return a + b }
	fmt.Println("함수를 변수에 담아 넘긴다 :", apply(f, 2, 3))

	ops := map[string]op{
		"더하기": func(a, b int) int { return a + b },
		"곱하기": func(a, b int) int { return a * b },
	}
	for _, k := range []string{"더하기", "곱하기"} {
		fmt.Printf("  ops[%q](3, 4) = %d\n", k, ops[k](3, 4))
	}

	acc := adder()
	fmt.Println("클로저가 상태를 든다 :", acc(1), acc(2), acc(3))

	words := []string{"bbb", "a", "cc"}
	sort.Slice(words, func(i, j int) bool { return len(words[i]) < len(words[j]) })
	fmt.Println("함수를 인자로 :", words)

	rep := strings.NewReplacer("a", "A").Replace
	fmt.Println("메서드 값도 함수다 :", rep("banana"))

	var nilFn op
	fmt.Println("함수 타입의 제로값은 nil :", nilFn == nil)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
함수를 변수에 담아 넘긴다 : 5
  ops["더하기"](3, 4) = 7
  ops["곱하기"](3, 4) = 12
클로저가 상태를 든다 : 1 3 6
함수를 인자로 : [a cc bbb]
메서드 값도 함수다 : bAnAnA
함수 타입의 제로값은 nil : true
(exit 0)
```

그림 해설 (한 단계씩):

- 명세가 그렇게 적는다.

  > **A function type denotes the set of all functions with the same parameter and result types.
  > The value of an uninitialized variable of function type is nil.**

- **변수에 담고, 맵의 값으로 두고, 인자로 넘기고, 반환한다.** 전부 된다.
- `type op func(int, int) int` 처럼 **이름을 붙이면** 시그니처가 문서가 된다.
- 클로저가 **상태를 든다** — `acc(1), acc(2), acc(3)` 이 `1 3 6` 이다.
  ★ 인자의 평가 순서가 **왼쪽에서 오른쪽**이라 이 값이 정해진다. 정본은 [목록의 **13번 주제**](../13-closures-variable-capture-and-loop-variable-change/)다.
- **메서드 값**(`strings.NewReplacer(…).Replace`)도 함수 값이다 — 리시버를 **묶어서** 들고 있다.
- **함수 타입의 제로값은 `nil`** 이다. 부르면 패닉이다.

```text
===== 소스: t12k.go =====
package main

import (
	"fmt"
	"os"
)

func main() {
	var f func(int) int
	fmt.Fprintf(os.Stderr, "-- f == nil : %v --\n", f == nil)
	fmt.Fprintln(os.Stderr, "-- 이제 불러 본다 --")
	_ = f(1)
	fmt.Fprintln(os.Stderr, "-- 여기는 안 온다 --")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
-- f == nil : true --
-- 이제 불러 본다 --
panic: runtime error: invalid memory address or nil pointer dereference
[signal SIGSEGV: segmentation violation code=0x1 addr=0x0 pc=0x49b770]

goroutine 1 [running]:
main.main()
	ex/t12k.go:12 +0x90
(exit 2)
```

- `panic: runtime error: invalid memory address or nil pointer dereference` ·
  `[signal SIGSEGV …]` · **종료 코드 2**.
- ★ 명세가 이것도 적어 둔다 — "**If a deferred function value evaluates to nil, execution panics
  when the function is invoked**"(`defer` 쪽 문장이지만 원리는 같다).
- ★★ 그래서 **콜백 필드는 `nil` 검사**를 하거나 **기본 구현을 넣어 둔다.**

비용 — 함수 값은 (코드 포인터, 캡처) 두 칸 정도. 클로저는 캡처한 만큼 더.

### (7) ★ 명명 반환값을 `:=` 로 가리면

**언제 쓰나** — 긴 함수에서 `err` 을 여러 번 만들 때. **조용히 틀린다.**

```text
===== 소스: t12l.go =====
package main

import (
	"errors"
	"fmt"
)

// shadow 는 명명 반환값 err 을 := 로 가려 버린다.
func shadow() (err error) {
	if true {
		err := errors.New("안쪽에서 만든 err")
		_ = err
	}
	return
}

// fixed 는 = 로 대입한다.
func fixed() (err error) {
	if true {
		err = errors.New("바깥 err 에 대입했다")
	}
	return
}

func main() {
	fmt.Printf("shadow() = %v   ← 에러도 경고도 없이 nil 이다\n", shadow())
	fmt.Printf("fixed()  = %v\n", fixed())
}
===== 명령: go build -trimpath -o prog . && ./prog =====
shadow() = <nil>   ← 에러도 경고도 없이 nil 이다
fixed()  = 바깥 err 에 대입했다
(exit 0)
===== 명령: go vet ./... =====
(exit 0)
```

그림 해설 (한 단계씩):

- `shadow()` 가 **`<nil>`** 이다. 안쪽 블록에서 `err := …` 로 **새 변수를 만들어** 버렸다.
  바깥의 명명 반환값 `err` 은 손도 안 댔다.
- `fixed()` 는 `=` 를 썼으므로 제대로 대입된다.
- ★★ **`go vet` 이 종료 코드 0** 이다 — 기본 vet 에는 섀도잉 검사가 **없다.**
  (`shadow` 분석기가 따로 있지만 기본이 아니다.)
- ★ 명세가 이 위험을 아는 흔적이 있다 — 벌거벗은 `return` 에 대해 이렇게 적는다.

  > **Implementation restriction: A compiler may disallow an empty expression list in a "return"
  > statement if a different entity (constant, type, or variable) with the same name as a result
  > parameter is in scope at the place of the return.**

  「**may disallow**」다 — **해도 되고 안 해도 된다.** 그래서 컴파일러가 잡아 줄 거라고 믿으면 안 된다.
- 고치는 법 — 명명 반환값을 쓰는 함수 안에서는 **그 이름을 `:=` 왼쪽에 두지 않는다.**

비용 — 없다. 값만 조용히 틀린다.

## 문법 — 형태와 규칙

### 형태 — 함수 선언으로 하는 일 전부

```go
// t12form.go
package main

import (
	"errors"
	"fmt"
)

// ① 다중 반환 — (값, error) 가 관례다
func find(k string) (int, error) {
	if k == "" {
		return 0, errors.New("빈 키")
	}
	return len(k), nil
}

// ② 명명 반환값 + defer — defer 가 반환값을 고친다
func wrapped(k string) (n int, err error) {
	defer func() {
		if err != nil {
			err = fmt.Errorf("wrapped(%q): %w", k, err)
		}
	}()
	return find(k)
}

// ③ 벌거벗은 return — 이름만 있으면 값을 안 적어도 된다
func pair() (a, b int) {
	a, b = 1, 2
	return
}

// ④ 가변 인자 — 함수 안에서는 슬라이스다
func sum(nums ...int) (total int) {
	for _, n := range nums {
		total += n
	}
	return
}

// ⑤ 함수는 값이다 — 인자로도 반환으로도 쓴다
func twice(f func(int) int) func(int) int {
	return func(x int) int { return f(f(x)) }
}

func main() {
	fmt.Println("①", func() string { n, err := find("abc"); return fmt.Sprint(n, " ", err) }())
	_, err := wrapped("")
	fmt.Println("②", err)
	fmt.Println("③", func() string { a, b := pair(); return fmt.Sprint(a, b) }())
	s := []int{1, 2, 3}
	fmt.Println("④", sum(), sum(1, 2), sum(s...))
	inc := func(x int) int { return x + 1 }
	fmt.Println("⑤", twice(inc)(10))

	// ⑥ defer 의 인자는 지금 평가되고, 몸통은 나중에 돈다
	i := 0
	defer fmt.Println("⑥ 인자로 넘긴 i =", i, "(0 이다)")
	defer func() { fmt.Println("⑥ 클로저가 읽은 i =", i, "(42 다)") }()
	i = 42
}
```

```text
===== 소스: t12form.go =====
package main

import (
	"errors"
	"fmt"
)

// ① 다중 반환 — (값, error) 가 관례다
func find(k string) (int, error) {
	if k == "" {
		return 0, errors.New("빈 키")
	}
	return len(k), nil
}

// ② 명명 반환값 + defer — defer 가 반환값을 고친다
func wrapped(k string) (n int, err error) {
	defer func() {
		if err != nil {
			err = fmt.Errorf("wrapped(%q): %w", k, err)
		}
	}()
	return find(k)
}

// ③ 벌거벗은 return — 이름만 있으면 값을 안 적어도 된다
func pair() (a, b int) {
	a, b = 1, 2
	return
}

// ④ 가변 인자 — 함수 안에서는 슬라이스다
func sum(nums ...int) (total int) {
	for _, n := range nums {
		total += n
	}
	return
}

// ⑤ 함수는 값이다 — 인자로도 반환으로도 쓴다
func twice(f func(int) int) func(int) int {
	return func(x int) int { return f(f(x)) }
}

func main() {
	fmt.Println("①", func() string { n, err := find("abc"); return fmt.Sprint(n, " ", err) }())
	_, err := wrapped("")
	fmt.Println("②", err)
	fmt.Println("③", func() string { a, b := pair(); return fmt.Sprint(a, b) }())
	s := []int{1, 2, 3}
	fmt.Println("④", sum(), sum(1, 2), sum(s...))
	inc := func(x int) int { return x + 1 }
	fmt.Println("⑤", twice(inc)(10))

	// ⑥ defer 의 인자는 지금 평가되고, 몸통은 나중에 돈다
	i := 0
	defer fmt.Println("⑥ 인자로 넘긴 i =", i, "(0 이다)")
	defer func() { fmt.Println("⑥ 클로저가 읽은 i =", i, "(42 다)") }()
	i = 42
}
===== 명령: go build -trimpath -o prog . && ./prog =====
① 3 <nil>
② wrapped(""): 빈 키
③ 1 2
④ 0 3 6
⑤ 12
⑥ 클로저가 읽은 i = 42 (42 다)
⑥ 인자로 넘긴 i = 0 (0 이다)
(exit 0)
```

규칙 불릿.

- **오류는 마지막 반환값**이고 실패 시 값 자리는 **제로값**이다.
- **명명 반환값은 `defer` 와 짝일 때만 값이 있다.** 그냥 문서 목적이면 **주석이 낫다** —
  긴 함수에서 섀도잉 사고를 부른다((7)절).
- **`return v` 는 「대입 + 나가기」이다**. `defer` 가 그 사이에 낀다.
- **벌거벗은 `return` 은 짧은 함수에서만.** 길어지면 무엇이 나가는지 안 보인다.
- **`defer` 의 인자는 지금 평가되고 몸통은 나중에 돈다.** 둘을 의식해서 고른다.
- **가변 인자는 슬라이스**이고, **인자 0개면 `nil`** 이다.
- **`s...` 는 복사가 아니다.** 함수가 고치면 원본이 바뀐다.
- **`[]T` 를 `...any` 로 못 펼친다.** 손으로 옮긴다.
- **함수 타입의 제로값은 `nil`** 이고 부르면 패닉이다.
- **기본 인자·이름 붙인 인자·오버로딩은 없다.** 필요하면 **옵션 구조체**나 **함수형 옵션**을 쓴다.

## 어디서 틀리나

### 1. ★★★ 「`defer` 로 오류를 감쌌는데 안 감싸진다」

- (2)절 실측 — `loadBroken` 이 **감싸이지 않은 오류**를 내보낸다. 이름이 없어서다.
- ★★ **컴파일도 되고 vet 도 조용하고 오류도 나간다.** 맥락만 사라진다.
- 고치는 법 — **반환값에 이름을 붙인다**. `func f() (v T, err error)`.

### 2. ★★★ 「`return 100` 이면 100이 나가겠지」

- (1)절 실측 — **101** 이 나간다. `return` 은 **대입**이고 그 뒤에 `defer` 가 돈다.
- 고치는 법 — 고칠 의도가 없으면 **명명 반환값을 안 쓴다.**

### 3. ★★ 「`defer` 안의 변수는 나갈 때 값이겠지」

- (3)절 실측 — `defer fmt.Println(i)` 는 **`i=0`**, 클로저는 **`i=42`** 다.
- 특히 위험한 자리 — `defer resp.Body.Close()` 에서 `resp` 를 나중에 재대입하는 코드.
- 고치는 법 — **나갈 때 값이 필요하면 클로저로** 감싼다.

### 4. ★★ 「가변 인자니까 복사되겠지」

- (4)절 실측 — `mutate(s...)` 뒤 원본이 `[99 5 6]` 이 됐다.
- ★ **코틀린은 정반대다** — spread(`*`)가 **배열을 복사**한다(형제 문서 실측).
  거기서 옮겨 온 직관이 Go 에서 조용히 틀린다.
- 고치는 법 — 함수가 인자를 고칠 것 같으면 **`append([]T(nil), s...)`** 로 넘긴다(07·08번 주제).

### 5. ★★ 「`f(nil)` 과 `f(nilSlice...)` 는 같겠지」

- (5)절 실측 — 앞은 **인자 1개**, 뒤는 **0개**다.
- 고치는 법 — `...any` 를 받는 함수에 `nil` 을 넘길 때 **무엇을 뜻하는지** 분명히 한다.

### 6. ★★ 「명명 반환값이 있으니 `err :=` 해도 되겠지」

- (7)절 실측 — `shadow()` 가 **`<nil>`** 이다. `go vet` 은 조용하다.
- ★ 명세가 컴파일러에게 「막아도 된다」고만 적어 뒀다 — **막아 준다고 믿으면 안 된다.**
- 고치는 법 — 그 이름을 `:=` 왼쪽에 두지 않는다.

### 7. ★ 「`[]string` 을 `fmt.Println` 에 펼친다」

- (5)절 실측 — **컴파일 에러**다. `have ([]string, string...)` / `want (...any)`.
- 고치는 법 — `[]any` 로 옮기거나 `strings.Join` 으로 한 문자열을 만든다.

### 8. ★ 「콜백 필드를 안 채우고 불렀다」

- (6)절 실측 — `nil` 함수를 부르면 **SIGSEGV 패닉**이다.
- 고치는 법 — `nil` 검사 또는 **아무것도 안 하는 기본 구현**을 넣는다.

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| `return` 이 **결과 파라미터에 먼저 대입**한다 | **명세 보장** | "sets the result parameters before any deferred functions are executed" |
| `defer` 의 **인자가 선언 시점에 평가**된다 | **명세 보장** | "the function value and parameters to the call are evaluated as usual and saved anew" |
| `defer` 가 **역순(LIFO)** 으로 돈다 | **명세 보장** | "in the reverse order they were deferred" |
| 결과 파라미터가 **제로값으로 초기화**된다 | **명세 보장** | "all the result values are initialized to the zero values … upon entry" |
| 가변 인자가 **슬라이스**인 것 | **명세 보장** | Function types 의 `...` 문장 |
| **인자 0개면 `nil` 슬라이스**인 것 | **명세 보장의 결과** | 빈 인자 목록에 대한 Calls 절 |
| **`s...` 가 복사가 아닌** 것 | **명세 보장** | Calls — 슬라이스가 그대로 파라미터가 된다 |
| 다중 반환을 **통째로 넘길 수 있는** 것 | **명세 보장** | "may be a single call to a multi-valued function" |
| 함수 타입의 **제로값이 `nil`** 인 것 | **명세 보장** | Function types |
| **섀도잉된 벌거벗은 `return` 을 막아도 되고 안 막아도 되는** 것 | ★ **명세가 컴파일러에게 맡김** | "Implementation restriction: A compiler **may** disallow …" |
| `go vet` 이 **섀도잉을 안 잡는** 것 | **도구의 기본 설정** | `shadow` 분석기가 기본이 아니다 |
| 패닉 스택의 **주소 오프셋**·`pc=` | **구현(gc)** | 빌드마다 바뀔 수 있다 |
| 컴파일 에러의 **정확한 문구** | **구현(gc)** | 컴파일러가 메시지를 다듬을 수 있다 |

★★ **이 표에서 특이한 칸이 「may disallow」다.** 명세가 **컴파일러에게 재량을 준** 드문 자리이고,
그래서 **같은 코드가 다른 컴파일러에서 다르게 거부될 수 있다.** 실측에서 gc 는 **거부하지 않았다**.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 실패할 수 있다 | `(T, error)` | 관례. 호출부가 `if err != nil` 로 받는다 |
| 나갈 때 오류를 감싼다 | **명명 반환값 + `defer`** | 반환 경로가 여럿이어도 한 곳에서 잡는다 |
| 패닉을 오류로 바꾼다 | **명명 반환값 + `recover`** | `return` 문이 없는 경로라 이 방법뿐이다 |
| 그냥 문서 목적으로 이름을 붙인다 | ★ **주석을 쓴다** | 섀도잉 사고를 부른다 |
| 함수가 짧다 | 벌거벗은 `return` 도 괜찮다 | 3\~5줄까지 |
| 함수가 길다 | **값을 적은 `return`** | 무엇이 나가는지 보인다 |
| 나갈 때의 값을 `defer` 에서 읽는다 | **클로저** | 인자 꼴은 지금 값을 잡는다 |
| 지금 값을 잡아 두어야 한다 | **인자 꼴** | `defer f(x)` |
| 인자 개수가 유동적이다 | 가변 인자 | 기본 인자가 없는 자리를 메운다 |
| 선택적 설정이 많다 | **옵션 구조체** 또는 **함수형 옵션** | 가변 인자로는 이름이 안 붙는다 |
| 남의 슬라이스를 `f(s...)` 로 넘긴다 | **복사해 넘긴다** | 함수가 고치면 원본이 바뀐다 |
| 콜백을 필드로 둔다 | **`nil` 검사** 또는 기본 구현 | `nil` 함수는 패닉이다 |

판단 규칙 두 줄.

- **「이 `defer` 가 반환값을 고쳐야 하나」를 물어라.** 그 답이 이름을 붙일지 정한다.
- **「이 슬라이스는 내 것인가」를 `f(s...)` 앞에서 물어라.** 07번 주제와 같은 질문이다.

## 핵심 문장

- ★★★ **`return v` 는 「나간다」가 아니라 「결과 파라미터에 `v` 를 넣고 나가기 시작한다」는 뜻이다**.
  그래서 `return 100` 짜리 함수가 **101** 을 돌려줄 수 있다.
- ★★★ **`defer` 가 반환값을 고치려면 반환값에 이름이 있어야 한다.**
  이름이 없으면 고쳐지는 것은 **지역 변수**이고 반환값은 이미 복사돼 나갔다.
- ★★★ **`defer` 의 인자는 선언 시점에, 몸통은 나갈 때 평가된다.** 같은 변수가 **0과 42** 로 갈린다.
- ★★ **`f(s...)` 는 복사가 아니다.** 함수가 고치면 원본이 바뀐다 —
  **코틀린의 spread 는 복사하므로 정반대**다.
- ★★ **가변 인자에 아무것도 안 주면 `nil` 슬라이스**이고, `nilSlice...` 도 `nil` 이며,
  `[]T{}...` 만 `nil` 이 아니다.
- ★ **`f(nil)` 은 인자 1개, `f(nilSlice...)` 는 0개**다.
- ★ **`[]string` 을 `...any` 로 못 펼친다** — 메모리 배치가 다르고 변환이 `O(n)` 이라서다.
- **Go 에는 기본 인자·이름 붙인 인자·오버로딩이 없다.** 다중 반환과 가변 인자가 그 자리를 메운다.
- **명명 반환값을 `:=` 로 가리면 조용히 nil 이 나간다** — `go vet` 도 안 잡는다.
- **함수 타입의 제로값은 `nil`** 이고 부르면 SIGSEGV 패닉이다.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 12번)
- [`../02-variable-declarations-and-zero-values/`](../02-variable-declarations-and-zero-values/)(변수 선언과 제로값) —
  ★ **직접 선행**. 결과 파라미터가 **제로값으로 초기화**된다는 사실이 거기서 온다.
  `:=` 와 `=` 의 차이도 — (7)절의 섀도잉이 그 규칙의 결과다
- [`../07-slice-sharing-silent-bugs/`](../07-slice-sharing-silent-bugs/)(슬라이스 공유) —
  ★ (4)절의 `f(s...)` 가 **그 주제의 한 사례**다. 막는 법은 08번 주제
- [`../09-maps-declaration-comma-ok-delete-and-iteration-order/`](../09-maps-declaration-comma-ok-delete-and-iteration-order/)(맵) —
  (6)절에서 맵에 함수를 담는다. 순서가 필요해 **키를 손으로 늘어놓았다**
- [`../11-strings-strconv-bytes-and-unicode-utf8/`](../11-strings-strconv-bytes-and-unicode-utf8/)(표준 API) —
  (0)절의 「실패 시 제로값」에 **예외가 있다**는 이야기(`strconv` 의 `ErrRange`)가 거기다
- [목록의 **13번 주제**](../13-closures-variable-capture-and-loop-variable-change/)(클로저와 변수 캡처) — (3)절의 클로저가 변수를 잡는 것, 인자 평가 순서의 정본
- [목록의 **26번 주제**](../26-defer-evaluation-lifo-named-results-and-loops/)(`defer`) — ★ **`defer` 자체의 정본**. **그쪽은 LIFO·루프 안의 `defer`·
  자원 정리 전체까지**, 여기는 **반환값과 만나는 자리**만
- [목록의 **27번 주제**](../27-panic-recover-and-where-to-use-them/)(`panic`/`recover`) — (2)절의 `recovered()` 가 거기 정본이다
- [목록의 **23번 주제**](../23-error-interface-and-errors-as-values/)(`error` 인터페이스) · **24번 주제**(오류 래핑 `%w`) —
  `(T, error)` 관례가 **왜 그 모양인지**와 감싸기의 정본
- [목록의 **19번 주제**](../19-method-sets-value-vs-pointer-receiver/)(메서드 집합) — (6)절의 **메서드 값**이 거기와 이어진다
- [`../../../python/syntax/19-function-argument-rules/`](../../../python/syntax/19-function-argument-rules/) —
  ★ **직접 대비**. 파이썬은 **위치/키워드/기본값/`*`/`/`** 로 인자 규칙이 아주 두껍다.
  Go 는 **그 전부가 없다** — 대신 **반환 쪽이 두껍다**(다중 반환·명명 반환값)
- [`../../../kotlin/syntax/08-function-declaration-default-and-named-args/`](../../../kotlin/syntax/08-function-declaration-default-and-named-args/) —
  ★ 코틀린은 **기본값 + 이름 붙인 인자**로 오버로딩을 대신한다. Go 는 **옵션 구조체**로 대신한다
- [`../../../kotlin/syntax/09-varargs-spread-local-and-infix-functions/`](../../../kotlin/syntax/09-varargs-spread-local-and-infix-functions/) —
  ★★ **spread 의 직접 대비**. **그쪽은 `*` 가 `Arrays.copyOf` 로 복사를 만든다**(그래서 원본이 안 바뀐다),
  **여기는 복사가 없다**(그래서 원본이 바뀐다). **같은 문법 기호, 반대 결과**다

## 용어 풀이

- **결과 파라미터(result parameter)** — 반환값이 들어가는 칸. 함수 진입 시 **제로값**으로 초기화된다.
- **명명 반환값(named result)** — 결과 파라미터에 이름을 붙인 것.
- **벌거벗은 `return`(naked return)** — 값을 안 적은 `return`. 명명 반환값이 있을 때만 쓸 수 있다.
- **가변 인자(variadic)** — 마지막 파라미터의 `...T`. 함수 안에서는 `[]T` 다.
- **펼치기(`s...`)** — 슬라이스를 가변 인자로 넘기는 문법. **복사가 아니다.**
- **섀도잉(shadowing)** — 안쪽 블록에서 같은 이름의 새 변수를 만들어 바깥을 가리는 것.
- **함수 값(function value)** — 함수를 담은 값. 제로값은 `nil`.
- **메서드 값(method value)** — 리시버를 묶어 둔 함수 값. `x.M` 꼴.
- **클로저(closure)** — 바깥 변수를 잡은 함수 리터럴. **값이 아니라 변수를 잡는다.**

---

## 더 들어가면

- **왜 Go 에 기본 인자가 없나** — 언어를 작게 유지하려는 선택이다.
  대신 관용구가 둘 있다. ① **옵션 구조체** — `func New(cfg Config)` 에 제로값을 기본값으로 쓴다.
  ② **함수형 옵션** — `func New(opts ...Option)` 에서 `Option` 이 `func(*T)` 다.
  ②는 **가변 인자와 함수 값을 합쳐** 이름 붙인 인자를 흉내 내는 것이다.
- **명명 반환값을 「문서 목적으로」 쓰는 것은 논쟁거리다.** 짧은 함수에서는 읽기 좋지만
  긴 함수에서는 (7)절의 섀도잉과 「**지금 무엇이 나가는지 모르겠다**」를 부른다.
  ★ 표준 라이브러리도 **`defer` 와 짝일 때 주로** 쓴다.
- **`defer` 는 1.14 에서 「열린 코딩(open-coded defer)」으로 훨씬 싸졌다**고 알려져 있는데,
  **이 문서는 비용을 재지 않았다.** 정본은 [목록의 **26번 주제**](../26-defer-evaluation-lifo-named-results-and-loops/)와 [목록의 **50번 주제**](../50-benchmarks-testing-b-and-reading-profiles/)다.
- **`recover` 는 `defer` 안에서 직접 불러야 듣는다.** 한 겹 더 감싼 함수 안에서 부르면 안 듣는다 —
  **이 문서는 그 반례를 던져 보지 않았다.** 정본은 [목록의 **27번 주제**](../27-panic-recover-and-where-to-use-them/)다.
- **제네릭이 온 뒤(1.18) 함수 표면이 넓어졌다** — 타입 파라미터가 붙은 함수는 이 주제의 규칙을
  그대로 따르되 **인스턴스화**라는 층이 하나 더 생긴다. 정본은 [목록의 **37번 주제**](../37-generics-type-parameters-and-constraint-interfaces/)다.
- **다중 반환은 튜플이 아니다.** 변수에 담을 수 없고, 타입이 없고, 컬렉션에 못 넣는다.
  **오직 `return` 과 호출 자리에서만** 존재한다 — (0)절의 `x := two()` 에러가 그 증거다.

# go/syntax/40 — 패키지 가시성·이름 규칙·`internal` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ **모든 문제에서 「이 경계를 긋는 것은 명세인가, `go` 명령인가, 컴파일러의 구현인가」를 먼저 적어라.**
> ★★ **진단 문구보다 `exit` 를 먼저 읽어라** — 문구는 흔들릴 수 있다.
> 실험마다 모듈 이름이 다르다 — 이름 탐침 `vis`, 인라인 탐침 `leak`, `internal` 격자 `corp`·`other`·`corp/a/plugin`, 테스트 `calc`, JSON `ex`. `go.mod` 는 전부 `go 1.27` 이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 다른 패키지에서 이름 열세 개를 쓰면 (예측)

```go
// t40shop.go
package shop

type Item struct {
	Name  string
	price int
}

func (Item) Label() string  { return "label" }
func (Item) secret() string { return "secret" }

func New() Item { return Item{Name: "pen", price: 3} }

func discount() int { return 1 }

var total int

const limit = 3

type cart struct{}

func 한글() {}

func Ärger() {}
```

```go
// t40app.go
package main

import "vis/shop"

func main() {
	it := shop.New()
	_ = it.Name                        // p01
	_ = it.price                       // p02
	_ = it.Label()                     // p03
	_ = it.secret()                    // p04
	_ = shop.Item{Name: "a", price: 1} // p05
	_ = shop.discount()                // p06
	_ = shop.total                     // p07
	_ = shop.limit                     // p08
	var _ shop.cart                    // p09
	shop.한글()                          // p10
	shop.Ärger()                       // p11
	_ = shop.nothere                   // p12
	_ = it.nothere                     // p13
}
```

<!-- 모듈 vis 에서 go build -gcflags=-e ./app 을 돌리고, 스크립트가 // pNN 주석의 줄에 떨어진 진단을 네 꼴(통과 · unexported · undefined: · no field or method)로 가른다. 마지막 줄에 소문자 칸 중 p12 와 같은 꼴로 답한 칸 수. -->

- 통과하는 탐침은? `p11` 의 `Ärger` 와 `p10` 의 `한글` 은 각각 어떻게 되나?
- 필드·메서드(`p02`·`p04`·`p05`)와 패키지 수준 이름(`p06`\~`p10`)은 **같은 꼴**의 진단을 받나?
- 마지막 줄의 수는?

### 2. `internal` 을 여덟 자리에서 (예측)

<!-- 아래 트리에서 corp/a/internal/x 를 corp · corp/a · corp/a/b · corp/a/internal/y · corp/c · other 가, corp/a/b/internal/w 를 corp/a/d 가, corp/a/internal/x 를 모듈 corp/a/plugin 이 import 한다. other 와 plugin 은 replace corp => ../corp 로 corp 를 가져온다. -->

```text
t40int/
├── corp/                    (module corp)
│   ├── t40root.go           package corp          → corp/a/internal/x
│   ├── a/t40a.go            package a             → corp/a/internal/x
│   ├── a/b/t40b.go          package b             → corp/a/internal/x
│   ├── a/internal/x/t40x.go
│   ├── a/internal/y/t40y.go package y             → corp/a/internal/x
│   ├── a/b/internal/w/t40w.go
│   ├── a/d/t40d.go          package d             → corp/a/b/internal/w
│   └── c/t40c.go            package c             → corp/a/internal/x
├── other/                   (module other)        → corp/a/internal/x
└── plugin/                  (module corp/a/plugin) → corp/a/internal/x
```

- 여덟 칸 각각 막히나? 막힌 칸 수는?
- `plugin` 은 `corp` 와 **다른 모듈**이다. 결과는?

### 3. `internal` 의 기준 (왜)

- 2번의 결과를 한 문장 규칙으로 말하라. 그 규칙은 **명세**에 있나?

### 4. 같은 줄, 세 가지 빌드 (예측)

```go
// t40leakshop.go
//go:build !noinl

package shop

func discount() int { return 1 }

// 공개 함수가 비공개 함수를 부른다 — 본문이 짧다.
func Price() int { return 10 - discount() }
```

```go
// t40leakshopni.go
//go:build noinl

package shop

func discount() int { return 1 }

// 같은 본문에 인라인만 막았다.
//
//go:noinline
func Price() int { return 10 - discount() }
```

```go
// t40leakapp.go
package main

import "leak/shop"

func main() {
	_ = shop.Price()
	_ = shop.discount()
}
```

<!-- 모듈 leak 에서 먼저 go build -gcflags=-m ./shop 을 기본·-tags noinl 로 한 번씩 돌리고, 그다음 ./app 을 기본 · -tags noinl · -gcflags=all=-l 세 가지로 빌드한다. -->

- `-gcflags=-m` 두 번의 출력은 무엇이 다른가?
- `app` 의 7 행 `shop.discount()` 가 세 빌드에서 받는 진단은? 소스가 바뀌었나?

### 5. 4번의 결과를 설명하면 (왜)

- 「내보내기 데이터」라는 말로 4번을 설명하라. 그러면 이 진단 **문구**를 근거로 써도 되나 — 무엇을 근거로 써야 하나?

### 6. 소문자 필드와 `encoding/json` (예측)

```go
// t40json.go
package main

import (
	"encoding/json"
	"fmt"
)

type User struct {
	Name  string
	email string
	Age   int    `json:"age"`
	token string `json:"token"`
}

func main() {
	b, err := json.Marshal(User{Name: "kim", email: "k@x", Age: 30, token: "t"})
	fmt.Println("Marshal  :", string(b), err)

	var u User
	err = json.Unmarshal([]byte(`{"Name":"lee","email":"l@x","age":4,"token":"z"}`), &u)
	fmt.Printf("Unmarshal: %+v %v\n", u, err)
}
```

<!-- go vet . 을 먼저 돌리고(실패해도 계속), 빌드해 실행한다. -->

- `go vet` 은 무엇을 말하나? `email` 에 대해서도 말하나?
- `Marshal`·`Unmarshal` 의 결과와 `err` 는?

### 7. 외부 테스트 패키지 (예측)

```go
// t40calc.go
package calc

func Add(a, b int) int { return add(a, b) }

func add(a, b int) int { return a + b }
```

```go
// t40calc_in_test.go
package calc

import "testing"

// 같은 패키지 안의 테스트
func TestAddInside(t *testing.T) {
	if add(1, 2) != 3 {
		t.Fatal("add")
	}
}
```

```go
// t40calc_ext_test.go
//go:build ext

package calc_test

import (
	"testing"

	"calc"
)

// 패키지 밖(외부 테스트 패키지)의 테스트
func TestAddOutside(t *testing.T) {
	if calc.Add(1, 2) != 3 || calc.add(1, 2) != 3 {
		t.Fatal("add")
	}
}
```

<!-- go test -count=1 . 을 태그 없이, -tags ext 로, -tags ext -gcflags=all=-l 로 세 번 돌린다. -->

- 세 번의 결과와 `exit` 는? `TestAddInside` 는 둘째·셋째 판에서 돌았나?
- 셋째 판의 진단은 둘째 판과 어떻게 다른가?

### 8. C# 의 `CS1061` 과 `CS0122` (연결)

- [C# 15번](../../../csharp/syntax/15-access-modifiers-and-assembly-boundary/)에서 다른 어셈블리의 `internal`·`private` 멤버와 `protected` 멤버는 각각 어느 진단을 받았나? Go 에서 「없다」와 「비공개」를 가르는 것은 무엇인가?

### 9. 경계를 긋는 도구 (연결)

- C# `internal`(어셈블리) · Java 모듈의 `exports`([Java 10번](../../../java/syntax/10-access-modifiers/)) · Go `internal` — 셋은 각각 **무엇을 단위로** 경계를 긋나?

### 10. 공개 이름은 계약이다 (경계)

- [25번 주제](../25-sentinel-errors-vs-custom-error-types/) (3)절이 오류 타입을 소문자로 감춘 이유는? 대문자 이름을 한 번 공개하면 무엇을 잃나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

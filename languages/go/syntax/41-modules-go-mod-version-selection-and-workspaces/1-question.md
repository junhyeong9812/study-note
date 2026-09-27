# go/syntax/41 — 모듈: `go.mod`·버전 선택·워크스페이스 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ **모든 문제에서 「이 규칙은 명세인가, `go` 명령인가」를 먼저 적어라.**
> ★★ 실험 환경 — 의존 모듈은 **로컬 파일 프록시**에서 온다(`GOPROXY=file://<프록시>` · `GOSUMDB=off` · `GOFLAGS=-mod=mod -modcacherw` · `GOTOOLCHAIN=local`). 블록마다 **모듈 캐시를 새로** 쓴다.
> 프록시에 든 모듈과 각 `go.mod` 의 요구는 아래와 같다 — 문제마다 이것을 본다.

```text
===== 명령: find . -type f | sort; echo; grep -r "^require\|^replace" --include=go.mod . | sort =====
./example.com/a@v1.0.0/go.mod
./example.com/a@v1.0.0/t41a100.go
./example.com/a@v1.1.0/go.mod
./example.com/a@v1.1.0/t41a110.go
./example.com/a@v1.2.0/go.mod
./example.com/a@v1.2.0/t41a120.go
./example.com/b@v1.0.0/go.mod
./example.com/b@v1.0.0/t41b100.go
./example.com/b@v1.1.0/go.mod
./example.com/b@v1.1.0/t41b110.go
./example.com/b@v1.2.0/go.mod
./example.com/b@v1.2.0/t41b120.go
./example.com/c@v1.0.0/go.mod
./example.com/c@v1.0.0/t41c100.go
./example.com/c@v1.1.0/go.mod
./example.com/c@v1.1.0/t41c110.go
./example.com/c@v1.2.0/go.mod
./example.com/c@v1.2.0/t41c120.go
./example.com/c@v1.3.0/go.mod
./example.com/c@v1.3.0/t41c130.go
./example.com/d/v2@v2.0.0/go.mod
./example.com/d/v2@v2.0.0/t41d200.go
./example.com/r@v1.0.0/go.mod
./example.com/r@v1.0.0/t41r100.go

./example.com/a@v1.0.0/go.mod:require example.com/c v1.0.0
./example.com/a@v1.1.0/go.mod:require example.com/c v1.1.0
./example.com/a@v1.2.0/go.mod:require example.com/c v1.2.0
./example.com/b@v1.0.0/go.mod:require example.com/c v1.0.0
./example.com/b@v1.1.0/go.mod:require example.com/c v1.1.0
./example.com/b@v1.2.0/go.mod:require example.com/c v1.2.0
./example.com/r@v1.0.0/go.mod:replace example.com/c v1.1.0 => example.com/c v1.2.0
./example.com/r@v1.0.0/go.mod:require example.com/c v1.1.0
(exit 0)
```

- `a vX`·`b vX` 는 전부 `func Which() string` 을 가지고, **「자기 판 → 자기가 빌드될 때 붙은 `c.V`」** 를 돌려준다(예 `a v1.1.0 → c v…`). `c vX` 의 `V` 는 `"c vX"` 다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `a v1.1.0` 과 `b v1.0.0` 을 요구하면 (예측)

```text
===== 소스: go.mod =====
module ex

go 1.27

require (
	example.com/a v1.1.0
	example.com/b v1.0.0
)
===== 소스: t41main.go =====
package main

import (
	"fmt"

	"example.com/a"
	"example.com/b"
)

func main() {
	fmt.Println(a.Which())
	fmt.Println(b.Which())
}
```

<!-- go list -m all 을 돌리고, go run . 을 돌린 뒤 go.mod 를 찍는다. 두 명령의 stderr 는 정렬해 따로 찍는다. -->

- `go list -m all` 에 찍히는 `example.com/c` 의 판은?
- `go run .` 이 찍는 두 줄 — 특히 `b v1.0.0 → c …` 의 `…` 는?
- 실행 뒤 `go.mod` 에 무엇이 더해지나?

### 2. `a`·`b` 의 판을 바꿔 가며 (예측)

<!-- 1번과 같은 main.go 로, go.mod 의 a·b 판을 v1.0.0·v1.1.0·v1.2.0 에서 각각 골라 아홉 번 go list -m -f '{{.Version}}' example.com/c 를 묻는다. 스크립트가 마지막에 「요구 중 최댓값을 고른 칸」과 「최신을 고른 칸」을 센다. 프록시의 c 는 v1.0.0 v1.1.0 v1.2.0 v1.3.0 이다. -->

- 아홉 칸 각각 고른 `c` 는? 마지막 두 줄의 수는?

### 3. 2번 규칙이 주는 것과 받는 것 (왜)

- 2번의 규칙에서 **잠금 파일 없이 빌드가 재현되는** 까닭은? 그 대가로 사용자가 해야 하는 일은?

### 4. `go get` 으로 올리고 내리면 (예측)

```text
===== 소스: go.mod =====
module ex

go 1.27

require (
	example.com/a v1.1.0
	example.com/b v1.0.0
)

require example.com/c v1.1.0 // indirect
===== 소스: t41main.go =====
package main

import (
	"fmt"

	"example.com/a"
	"example.com/b"
)

func main() {
	fmt.Println(a.Which())
	fmt.Println(b.Which())
}
```

<!-- go get example.com/c@v1.2.0 → go.mod diff → go run . , 이어서 go get example.com/c@v1.0.0 → go.mod diff → go run . -->

- 첫 `go get` 뒤 `go.mod` 의 `diff` 는 몇 줄이고 무엇인가?
- 둘째 `go get` 은 `c` 말고 **무엇을 더** 바꾸나? `go run` 이 찍는 두 줄은?

### 5. `exclude` 를 적으면 (예측)

```text
===== 소스: go.mod =====
module ex

go 1.27

require (
	example.com/a v1.1.0
	example.com/b v1.0.0
)

exclude example.com/c v1.1.0
===== 소스: t41main.go =====
package main

import (
	"fmt"

	"example.com/a"
	"example.com/b"
)

func main() {
	fmt.Println(a.Which())
	fmt.Println(b.Which())
}
```

```text
===== 소스: go.mod =====
module ex

go 1.27

require example.com/a v1.1.0

exclude example.com/c v1.1.0
===== 소스: t41onlya.go =====
package main

import (
	"fmt"

	"example.com/a"
)

func main() { fmt.Println(a.Which()) }
```

<!-- 두 모듈 각각에서 go list -m all → go run . → go.mod 를 찍는다. 첫째는 1번과 같은 main.go, 둘째는 a 만 import 한다. -->

- 첫째(`a`·`b`)에서 `go run` 의 `a v1.1.0 → c …` 는?
- 둘째(`a` 하나)에서 `go list -m all` 에 `c` 가 있나? `go run` 뒤 `go.mod` 에 적히는 `c` 의 판은?

### 6. 의존 모듈이 들고 온 `replace` (예측)

```text
===== 소스: go.mod =====
module example.com/c

go 1.21
===== 소스: t41cfork.go =====
package c

// V 는 이 사본의 이름이다.
const V = "c (로컬 디렉토리 cfork)"
===== 소스: go.mod =====
module ex

go 1.27

require example.com/r v1.0.0
===== 소스: t41onlyr.go =====
package main

import (
	"fmt"

	"example.com/r"
)

func main() { fmt.Println(r.Which()) }
```

<!-- [1] 메인 go.mod 그대로, [2] 메인 go.mod 에 "replace example.com/c v1.1.0 => example.com/c v1.2.0" 을 덧붙여서, [3] 대신 "replace example.com/c => ./cfork" 를 덧붙여서 — 각각 go list -m all 과 go run . 을 돌린다. r v1.0.0 의 go.mod 는 위 목록에 있다. -->

- `[1]`·`[2]`·`[3]` 에서 `r v1.0.0 → …` 의 `…` 는 각각?

### 7. `go.work` (예측)

```text
===== 소스: go.mod =====
module ex

go 1.27

require (
	example.com/a v1.1.0
	example.com/b v1.0.0
)

require example.com/c v1.1.0 // indirect
===== 소스: t41main.go =====
package main

import (
	"fmt"

	"example.com/a"
	"example.com/b"
)

func main() {
	fmt.Println(a.Which())
	fmt.Println(b.Which())
}
===== 소스: go.mod =====
module example.com/c

go 1.21
===== 소스: t41cwork.go =====
package c

// V 는 이 사본의 이름이다.
const V = "c (작업 공간의 로컬 사본)"
```

<!-- 두 go.mod 는 위에서 app/go.mod, c/go.mod 순이다. app 에서 go run . → 상위에서 GOFLAGS= go work init ./app ./c → app 에서 [2] go run .(GOFLAGS=-mod=mod -modcacherw 그대로) [3] GOFLAGS= 로 go list -m all · go run . [4] GOWORK=off go run . → app/go.mod 의 replace 줄 수를 센다. -->

- `[2]` 는 성공하나? `[3]` 의 `go list -m all` 에서 `example.com/c` 는 어떻게 찍히나?
- 마지막에 `app/go.mod` 에 `replace` 가 있나?

### 8. `require example.com/d v2.0.0` (경계)

- 프록시에는 `example.com/d/v2` 만 있다. 메인 `go.mod` 에 `require example.com/d v2.0.0` 을 적으면 **어느 단계에서** 무엇이라 막히나? 고치려면 `go.mod` 와 **소스의 어디**를 바꾸나?

### 9. `go` 줄은 무엇을 요구하나 (경계)

- 1.27.1 툴체인·`GOTOOLCHAIN=local` 에서 `go.mod` 의 `go` 줄을 `1.21`·`1.27`·`1.27.1`·`1.28` 로 바꾸면 어느 것이 막히나? 그 줄은 무엇에 대한 요구인가?

### 10. Cargo 로 같은 모양을 만들면 (연결)

- `a 1.1.0` 이 `c = "1.1.0"`, `b 1.0.0` 이 `c = "1.0.0"` 을 요구하고 레지스트리에 `c` 1.0.0\~1.3.0 이 있다. `cargo run` 이 붙이는 `c` 는? Go 와 다르다면 그 차이가 **잠금 파일의 필요**를 어떻게 바꾸나([Rust 01번](../../../rust/syntax/01-cargo-crates-and-modules/))?

### 11. 요구 그래프와 빌드 목록 (왜)

- 1번 모듈에서 `go mod graph` 에 `example.com/b@v1.0.0 example.com/c@v1.0.0` 줄이 **있다**. 그런데 왜 `c v1.0.0` 은 빌드에 안 쓰이나? 두 출력은 각각 무엇을 말하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

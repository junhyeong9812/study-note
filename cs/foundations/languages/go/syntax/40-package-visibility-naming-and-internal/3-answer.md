# go/syntax/40 — 패키지 가시성·이름 규칙·`internal` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★ **근거로 읽을 칸** — `exit` · 탐침별 꼴 · `5 / 8` · `막힌 칸 4 / 8` · `json` 출력과 `err` · `ok`/`FAIL`.
> **플래그를 타는 칸** — 소문자 이름 진단의 **문구**(4번 — 인라인에 달렸다).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `p01`·`p03`·`p11` 통과(`Ärger` 는 공개, `한글` 은 `undefined:`) · 필드·메서드는 「비공개」, 패키지 수준은 「없다」 — `5 / 8`

**출력**

```text
===== 소스: t40app.go =====
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
===== 소스: go.mod =====
module vis

go 1.27
===== 소스: t40shop.go =====
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
===== 명령: go build -gcflags=-e -o /dev/null ./app 2>err.txt; echo "go build exit=$?"; cat err.txt; same=0; m=0; for i in $(seq -w 1 13); do p=p$i; L=$(grep -n "// $p\$" app/t40app.go | cut -d: -f1); msg=$(grep "t40app.go:$L:" err.txt | cut -d" " -f2-); case "$msg" in "") k="통과";; *unexported*) k="「unexported」 라고 말한다";; "undefined: "*) k="「undefined:」 꼴";; *"no field or method"*) k="「no field or method」 꼴";; *) k="기타";; esac; case $p in p02|p04|p05|p06|p07|p08|p09|p10) m=$((m+1)); case "$k" in *undefined*) same=$((same+1));; esac;; esac; echo "$p : $k"; done; echo "소문자 이름 칸 중 「정말 없는 이름」(p12)과 같은 꼴로 답한 칸 $same / $m" =====
go build exit=1
# vis/app
app/t40app.go:8:9: it.price undefined (cannot refer to unexported field price)
app/t40app.go:10:9: it.secret undefined (cannot refer to unexported method secret)
app/t40app.go:11:27: cannot refer to unexported field price in struct literal of type shop.Item
app/t40app.go:12:11: undefined: shop.discount
app/t40app.go:13:11: undefined: shop.total
app/t40app.go:14:11: undefined: shop.limit
app/t40app.go:15:13: undefined: shop.cart
app/t40app.go:16:7: undefined: shop.한글
app/t40app.go:18:11: undefined: shop.nothere
app/t40app.go:19:9: it.nothere undefined (type shop.Item has no field or method nothere)
p01 : 통과
p02 : 「unexported」 라고 말한다
p03 : 통과
p04 : 「unexported」 라고 말한다
p05 : 「unexported」 라고 말한다
p06 : 「undefined:」 꼴
p07 : 「undefined:」 꼴
p08 : 「undefined:」 꼴
p09 : 「undefined:」 꼴
p10 : 「undefined:」 꼴
p11 : 통과
p12 : 「undefined:」 꼴
p13 : 「no field or method」 꼴
소문자 이름 칸 중 「정말 없는 이름」(p12)과 같은 꼴로 답한 칸 5 / 8
(exit 0)
```

```text
===== 명령: sed -n "2304,2320p" "$(go env GOROOT)/doc/go_spec.html" | sed -e "s/<[^>]*>//g" | awk NF =====
Exported identifiers
An identifier may be exported to permit access to it from another package.
An identifier is exported if both:
	the first character of the identifier's name is a Unicode uppercase
	letter (Unicode character category Lu); and
	the identifier is declared in the package block
	or it is a field name or
	method name.
All other identifiers are not exported.
(exit 0)
```

**왜 그런가**

- ★★★ **`Ä` 는 유니코드 대문자(Lu)** — 명세 「**the first character of the identifier's name is a Unicode uppercase letter (Unicode character category Lu)**」. **한글은 대소문자가 없는 글자**라 `한글` 은 **어떤 방법으로도 공개되지 않는다.**
- ★★★ **필드·메서드는 `cannot refer to unexported field/method`** — 「있는데 못 쓴다」. 대조군 `p13` 은 `has no field or method` 로 **다른 꼴**이다.
- ★★★ **패키지 수준 이름은 `undefined: shop.discount`** — 대조군 `p12`(`undefined: shop.nothere`)와 **같은 꼴**. 소문자 여덟 칸 중 **다섯**이 「없다」로 답했다.

### 2. 막힌 칸 `4 / 8` — `plugin` 은 다른 모듈인데 통과한다

**출력**

```text
===== 소스: t40w.go =====
package w

func W() int { return 2 }
===== 소스: t40b.go =====
package b

import "corp/a/internal/x"

var _ = x.X()
===== 소스: t40d.go =====
package d

import "corp/a/b/internal/w"

var _ = w.W()
===== 소스: t40x.go =====
package x

func X() int { return 1 }
===== 소스: t40y.go =====
package y

import "corp/a/internal/x"

var _ = x.X()
===== 소스: t40a.go =====
package a

import "corp/a/internal/x"

var _ = x.X()
===== 소스: t40c.go =====
package c

import "corp/a/internal/x"

var _ = x.X()
===== 소스: go.mod =====
module corp

go 1.27
===== 소스: t40root.go =====
package corp

import "corp/a/internal/x"

var _ = x.X()
===== 소스: go.mod =====
module other

go 1.27

require corp v0.0.0

replace corp => ../corp
===== 소스: t40other.go =====
package other

import "corp/a/internal/x"

var _ = x.X()
===== 소스: go.mod =====
module corp/a/plugin

go 1.27

require corp v0.0.0

replace corp => ../corp
===== 소스: t40plugin.go =====
package plugin

import "corp/a/internal/x"

var _ = x.X()
===== 명령: find . \( -name "*.go" -o -name go.mod \) | sort; n=0; m=0; for c in "corp ." "corp ./a" "corp ./a/b" "corp ./a/internal/y" "corp ./c" "corp ./a/d" "other ." "plugin ."; do set -- $c; m=$((m+1)); (cd $1 && go build $2) >err.txt 2>&1; rc=$?; if [ $rc -ne 0 ]; then n=$((n+1)); fi; echo "[$1 모듈 · go build $2] exit=$rc $(grep -o "use of internal package .* not allowed" err.txt)"; done; echo "막힌 칸 $n / $m" =====
./corp/a/b/internal/w/t40w.go
./corp/a/b/t40b.go
./corp/a/d/t40d.go
./corp/a/internal/x/t40x.go
./corp/a/internal/y/t40y.go
./corp/a/t40a.go
./corp/c/t40c.go
./corp/go.mod
./corp/t40root.go
./other/go.mod
./other/t40other.go
./plugin/go.mod
./plugin/t40plugin.go
[corp 모듈 · go build .] exit=1 use of internal package corp/a/internal/x not allowed
[corp 모듈 · go build ./a] exit=0 
[corp 모듈 · go build ./a/b] exit=0 
[corp 모듈 · go build ./a/internal/y] exit=0 
[corp 모듈 · go build ./c] exit=1 use of internal package corp/a/internal/x not allowed
[corp 모듈 · go build ./a/d] exit=1 use of internal package corp/a/b/internal/w not allowed
[other 모듈 · go build .] exit=1 use of internal package corp/a/internal/x not allowed
[plugin 모듈 · go build .] exit=0 
막힌 칸 4 / 8
(exit 0)
```

**왜 그런가**

- ★★★ **통과 — `corp/a`·`corp/a/b`·`corp/a/internal/y`·`corp/a/plugin`**, **막힘 — `corp`·`corp/c`·`corp/a/d`(→ `a/b/internal/w`)·`other`.**
- ★★★ **`plugin` 은 모듈이 다른데 통과했다** — 모듈 경로가 **`corp/a/plugin`** 이라 `corp/a` 로 시작한다.
- ★★ `corp`(루트)는 `internal` 의 **바로 위 `corp/a`** 가 아니라 그 위라 막혔다.

### 3. 「`internal` 바로 위의 import 경로를 접두로 가진 패키지만」 — 명세에는 없다, `go` 명령의 규칙이다

**출력**

```text
===== 명령: go help importpath | sed -n "15,18p;37,43p" =====
Internal packages

Code in or below a directory named "internal" is importable only
by code that shares the same import path above the internal directory.
The code in z.go is imported as "example.com/m/foo/internal/baz", but that
import statement can only appear in packages with the import path prefix
"example.com/m/foo". The packages "example.com/m/foo", "example.com/m/foo/bar", and
"example.com/m/foo/quux" can all import "foo/internal/baz", but the package
"example.com/m/crash/bang" cannot.

See https://go.dev/s/go14internal for details.
(exit 0)
```

```text
===== 명령: grep -n -i "internal" "$(go env GOROOT)/doc/go_spec.html" =====
712:internal representation with limited precision.  That said, every
(exit 0)
```

- ★★★ `go help importpath` — 「**importable only by code that shares the same import path above the internal directory**」. 기준은 **디렉토리 트리도 모듈도 아닌 import 경로**다 — 그래서 `plugin` 이 통과했다.
- ★★★ **명세에는 없다** — 명세에 「internal」 이 나오는 자리는 **712 행 하나**, 부동소수 표현 이야기다. 막는 것은 **`go` 명령**이다.

### 4. `-m` — 기본 판에만 `can inline Price` · 기본은 `not exported by package`, 나머지 둘은 `undefined:` · 소스는 그대로

**출력**

```text
===== 소스: t40leakapp.go =====
package main

import "leak/shop"

func main() {
	_ = shop.Price()
	_ = shop.discount()
}
===== 소스: go.mod =====
module leak

go 1.27
===== 소스: t40leakshop.go =====
//go:build !noinl

package shop

func discount() int { return 1 }

// 공개 함수가 비공개 함수를 부른다 — 본문이 짧다.
func Price() int { return 10 - discount() }
===== 소스: t40leakshopni.go =====
//go:build noinl

package shop

func discount() int { return 1 }

// 같은 본문에 인라인만 막았다.
//
//go:noinline
func Price() int { return 10 - discount() }
===== 명령: go build -gcflags=-m ./shop 2>&1 | grep -v "^#"; go build -tags noinl -gcflags=-m ./shop 2>&1 | grep -v "^#"; for c in 기본 noinl 인라인끔; do case $c in 기본) f=;; noinl) f="-tags noinl";; 인라인끔) f="-gcflags=all=-l";; esac; go build $f -o /dev/null ./app 2>err.txt; rc=$?; echo "[$c] go build $f ./app → exit=$rc · $(grep -v "^#" err.txt)"; done =====
shop/t40leakshop.go:5:6: can inline discount
shop/t40leakshop.go:8:6: can inline Price
shop/t40leakshop.go:8:40: inlining call to discount
shop/t40leakshopni.go:5:6: can inline discount
shop/t40leakshopni.go:10:40: inlining call to discount
[기본] go build  ./app → exit=1 · app/t40leakapp.go:7:11: name discount not exported by package shop
[noinl] go build -tags noinl ./app → exit=1 · app/t40leakapp.go:7:11: undefined: shop.discount
[인라인끔] go build -gcflags=all=-l ./app → exit=1 · app/t40leakapp.go:7:11: undefined: shop.discount
(exit 0)
```

**왜 그런가**

- ★★ `-gcflags=-m` — **기본 판은 `can inline Price`**, `noinl` 판은 `Price` 에 그 줄이 없다(`discount` 는 두 판 다 `Price` 안으로 인라인됐다).
- ★★★ **`[기본]` `name discount not exported by package shop`** · **`[noinl]`·`[인라인끔]` `undefined: shop.discount`** — `app` 의 소스는 **한 글자도 안 바뀌었다.**

### 5. 인라인되는 `Price` 의 본문이 내보내기 데이터에 실리며 `discount` 도 따라 실린다 · 문구는 근거가 못 된다 — `exit=1` 을 쓴다

- ★★★ `app` 을 컴파일할 때 컴파일러는 `shop` 의 **소스가 아니라 내보내기 데이터**를 읽는다. `Price` 가 인라인될 수 있으면 **그 본문이 실리고**, 본문이 부르는 `discount` 도 **이름째 실린다** → 「있는데 비공개」. `Price` 가 인라인 안 되면 `discount` 가 **안 실린다** → 「없다」.
  ★ 이것은 **`-m` 출력과 세 결과를 잇는 추론**이다 — 내보내기 데이터 파일을 **직접 열어 보지는 않았다.**
- ★★★ 그러니 **문구는 다른 함수의 최적화 판정에 흔들린다**(규칙 27). 근거는 **`exit=1`(막혔다)** 이고, 문구는 **이 판·이 플래그의 관찰**로만 적는다.

### 6. `vet` 은 `token` 만(`has json tag but is not exported`) — `email` 은 침묵 · `{"Name":"kim","age":30}` · 소문자 필드 안 채워짐 · `err` 는 둘 다 `<nil>`

**출력**

```text
===== 소스: t40json.go =====
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
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && ./prog =====
t40json.go:12:2: struct field token has json tag but is not exported
vet exit=1
Marshal  : {"Name":"kim","age":30} <nil>
Unmarshal: {Name:lee email: Age:4 token:} <nil>
(exit 0)
```

**왜 그런가**

- ★★★ **소문자 필드는 조용히 빠진다** — 내보낼 때도 받을 때도. `encoding/json` 은 **다른 패키지**라 소문자 필드를 **쓸 수 없고**, 그것을 오류로 알리지도 않는다.
- ★★ **`vet` 은 태그 달린 `token` 만** — 「태그를 달았는데 비공개」는 **실수로 보고**, 태그 없는 `email` 은 **일부러 감춘 것일 수 있어** 침묵한다. `vet exit=1` 이어도 **빌드·실행은 된다.**

### 7. `ok`(0) · `FAIL [build failed]`(1) · `FAIL [build failed]`(1) — 안 돌았다 · 셋째는 `undefined: calc.add (but have Add)`

**출력**

```text
===== 소스: go.mod =====
module calc

go 1.27
===== 소스: t40calc.go =====
package calc

func Add(a, b int) int { return add(a, b) }

func add(a, b int) int { return a + b }
===== 소스: t40calc_ext_test.go =====
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
===== 소스: t40calc_in_test.go =====
package calc

import "testing"

// 같은 패키지 안의 테스트
func TestAddInside(t *testing.T) {
	if add(1, 2) != 3 {
		t.Fatal("add")
	}
}
===== 명령: go test -count=1 . ; echo "exit=$?"; go test -count=1 -tags ext . ; echo "exit=$?"; go test -count=1 -tags ext -gcflags=all=-l . ; echo "exit=$?" =====
ok  	calc	0.003s
exit=0
# calc_test [calc.test]
./t40calc_ext_test.go:13:33: name add not exported by package calc
FAIL	calc [build failed]
FAIL
exit=1
# calc_test [calc.test]
./t40calc_ext_test.go:13:33: undefined: calc.add (but have Add)
FAIL	calc [build failed]
FAIL
exit=1
(exit 0)
```

**왜 그런가**

- ★★ **태그 없는 판** — `package calc` 테스트는 `add` 를 부를 수 있다 → `ok`.
- ★★★ **`-tags ext`** — `package calc_test` 는 **다른 패키지**(`go help test` — 「compiled as a separate package」)라 `name add not exported by package calc`. **빌드 실패라 `TestAddInside` 도 안 돌았다.**
- ★★★ **`-gcflags=all=-l`** — 같은 줄이 **`undefined: calc.add (but have Add)`**. 인라인이 꺼져 `add` 가 내보내기 데이터에 안 실렸고(5번), 컴파일러는 **대소문자만 다른 `Add` 가 있다**고 귀띔한다. **한 줄에서 세 번째 문구**다.

### 8. `internal`·`private` 은 `CS1061`(없다), `protected` 는 `CS0122`(막힘) · Go 는 멤버냐 패키지 수준이냐, 그리고 내보내기 데이터

- ★★★ [C# 15번](../../../csharp/syntax/15-access-modifiers-and-assembly-boundary/) (3)절 — 다른 어셈블리에서 **`Intl`·`Priv` 는 `CS1061`**(「그런 정의가 없다」), **`Prot`·`ProtIntl`·`PrivProt` 는 `CS0122`**(「보호 수준 때문에」). C# 은 **접근 제한자의 종류**가 목소리를 가른다.
- ★★★ Go(1번) — **필드·메서드는 「비공개」, 패키지 수준 이름은 「없다」**, 그리고 4번 — **다른 함수가 인라인되면 패키지 수준 이름도 「비공개」**. 가르는 것은 **이름의 자리**와 **내보내기 데이터**다.

### 9. C# 은 어셈블리(빌드 산출물), Java 는 모듈의 `exports`(패키지 목록), Go 는 import 경로 접두

- ★★ **C# `internal`** — **어셈블리** 하나. `InternalsVisibleTo` 로 **상대 어셈블리를 이름으로** 연다([C# 15번](../../../csharp/syntax/15-access-modifiers-and-assembly-boundary/)).
- ★ **Java** — [Java 10번](../../../java/syntax/10-access-modifiers/)이 「`module-info.java` 가 `exports` 하지 않은 패키지는 `public` 이어도 밖에서 못 쓴다」를 **언급만** 했다(실측 없음). 단위는 **모듈이 내보낸 패키지 목록**이다.
- ★★★ **Go `internal`** — **import 경로의 접두**. 모듈도 디렉토리도 아니다(2번 `plugin`).

### 10. 공개하면 호출부가 그 이름에 묶인다 — 바꾸면 컴파일 에러로 깨진다

- ★★★ [25번 주제](../25-sentinel-errors-vs-custom-error-types/) (3)절 — 공개한 센티넬·타입·필드는 **전부 공개 API** 라 **바꾸면 호출부가 컴파일 에러로 깨진다.** 감춘 것만 **마음대로 고칠 수 있다.** 그래서 오류 타입을 소문자로 두고 **판별 함수만 공개**했다.
- ★★ 대문자 한 글자가 곧 **「이제 이것은 약속이다」** 라는 선언이다 — 되돌리려면 **호출부 전부**를 고쳐야 한다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 로 **★고칠 것 0** |
| ★★★ 이름 탐침 (`t40names`) | `-gcflags=-e` · `// pNN` 줄 번호로 맞춤 | 캡처마다 | **`5 / 8`** |
| ★★★ `internal` 격자 (`t40int`) | 세 모듈 · 여덟 자리 · `replace` | 캡처마다 | **`4 / 8`** · `plugin` 통과 |
| ★★★ 문구 흔들림 (`t40leak`) | `-m` · 빌드 태그 · `-l` | 캡처마다 | `not exported` 대 `undefined:` |
| ★★ `json` (`t40json`) | `vet` · 실행 | 캡처마다 | 소문자 필드 빠짐 · `vet` 은 태그만 |
| ★★ 외부 테스트 (`t40test`) | `go test` × 태그 × `-l` | 캡처마다 | `ok` · `FAIL` · `FAIL` |

**구현·환경에 달린 항목**

| 항목 | 무엇에 달렸나 |
|---|---|
| 소문자 이름 진단의 문구 | **gc 의 내보내기 데이터·인라인 판정** |
| `internal` 규칙 | **`go` 명령** — 명세가 아니다 |
| `vet structtag` 의 범위 | **이 판 `vet` 의 휴리스틱** |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다.

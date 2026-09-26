# go/syntax/40 — 패키지 가시성·이름 규칙·`internal` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Go 명세](https://go.dev/ref/spec)의 Exported identifiers · `go help importpath` 의 Internal packages · `go help test` · [`encoding/json`](https://pkg.go.dev/encoding/json) 문서.
> 명세와 `go help` 는 **이 툴체인에서 직접 떴다.** `go help importpath` 가 가리키는 설계 문서(go14internal)와 Effective Go 의 이름 절은 **안 열었다.**\
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> ★★ **버전** — 대문자 규칙은 **1.0 부터** 명세에 있다. `internal` 규칙은 **명세가 아니라 `go` 명령의 규칙**이다(명세에 「internal」 이라는 낱말이 **패키지 뜻으로는 한 번도 안 나온다** — 머리말 블록).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체는 넷째 창이다** — 「**`internal` 격자** — 한 `internal` 패키지를 여덟 자리(같은 모듈의 부모·형제·조카, 다른 모듈 둘)에서 import 해 **막혔나**를 찍는 로그」.
마지막 줄 「**막힌 칸 4 / 8**」 — 그리고 ★★★ **다른 모듈인데 통과한 칸이 하나 있다**((2)절).
★★ 짝이 되는 창은 「**소문자 이름 탐침 13 개가 받은 진단의 꼴**」 — 컴파일러는 소문자 이름을 「**없다**」로도 「**비공개다**」로도 말하고, ★★★ **어느 쪽인지가 다른 함수의 인라인 여부에 달려 있었다**((1)·(3)절).

★★★ **이 주제의 경계** — 패키지가 **언제 초기화되나**(`init` 순서·import 네 형태)는 [01번 주제](../01-packages-imports-main-and-init/)가 정본이다(그 편이 「이름 규칙은 40번」이라고 넘겼다).
모듈 경로가 **어느 버전으로 풀리나**(`go.mod`·`replace`·최소 버전 선택)는 목록의 **41번 주제**다 — 여기서는 `replace` 를 **실험 배선**으로만 쓴다.
오류 값을 **감춰서 설계하는 법**은 [25번 주제](../25-sentinel-errors-vs-custom-error-types/) (3)절 — 그 편이 이미 `undefined: opaque.notFound` 를 찍었다. 여기는 그 「없다」가 **언제 「비공개」로 바뀌나**를 본다.
필드 태그와 `reflect` 는 [17번 주제](../17-struct-literals-comparability-field-tags-and-sorting/) (6)절, `encoding/json` 전반은 목록의 **45번 주제**다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | ★★★ 「**첫 글자가 유니코드 대문자(Lu)** 이고 패키지 블록에 선언됐거나 필드·메서드 이름이면 **내보낸다**. 나머지는 전부 안 내보낸다」 — ★ **`internal` 은 명세에 없다** |
| **도구(`go` 명령)의 규칙** | `go help` 가 적은 것 | ★★★ 「`internal` 아래 코드는 **`internal` 위의 import 경로를 공유하는 코드**만 import 한다」 · `_test` 로 끝나는 패키지는 **따로 컴파일되는 패키지**다 |
| **구현(gc)** | 컴파일러가 실제로 한 것 | ★★★ **소문자 이름에 대한 진단 문구** — `undefined:` 인가 `not exported` 인가가 **내보내기 데이터(export data)에 그 이름이 실렸나**에 달린다((3)절) |
| **표준 라이브러리** | `encoding/json` | 소문자 필드는 **조용히 건너뛴다** · `vet structtag` 은 **태그가 달린** 소문자 필드만 말한다((4)절) |

★★★ **선을 긋는다** — 「소문자 이름은 패키지 밖에서 못 쓴다」는 **명세**다. 「못 쓴다는 것을 **무슨 말로** 알려 주나」는 **컴파일러 구현**이고, 이 판에서 **세 가지 문구**가 나왔다.
「`internal` 은 막는다」는 **`go` 명령**이다 — **컴파일러(`go tool compile`)의 일이 아니다.**

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
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

```text
===== 명령: grep -n -i "internal" "$(go env GOROOT)/doc/go_spec.html" =====
712:internal representation with limited precision.  That said, every
(exit 0)
```

- ★★★ **명세에 `internal` 이 나오는 자리는 712 행 하나** — 「internal representation」(부동소수 표현 이야기)이다. **`internal` 패키지 규칙은 명세에 없다.**

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

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ **`internal` 격자의 `exit` · `막힌 칸 4 / 8`** | `go` 명령의 정적 판정 |
| 안 흔들린다 | ★★★ **이름 탐침 13 개의 꼴 · `5 / 8`** | 같은 빌드 플래그면 같다 |
| **플래그를 탄다** | ★★★ **소문자 이름 진단의 문구**(`undefined:` · `not exported` · `(but have Add)`) | ★ **인라인·빌드 태그가 바꾼다**((3)절) — 그래서 근거는 **`exit` 의 1** 이고 문구는 **관찰**이다(규칙 27) |
| 안 흔들린다 | `go test` 의 `ok`/`FAIL` · `exit` | ★ `ok` 줄의 **경과 시간**은 흔들린다 — 기본 정규화 규칙(시간)이 지운다 |

★ 정규화 규칙은 **기본 넷**만 썼다.

## 한눈에 — 쉽게 말하면

**패키지는 「회사」, 대문자 이름은 「대외 공개 연락처」다.** 소문자 이름은 **사내 내선** — 회사 밖에서는 **걸 수가 없다.**
그런데 밖에서 내선에 걸었을 때 교환원의 대답이 **둘**이다 — 「**그런 번호 없습니다**」(`undefined:`)와 「**그 번호는 사내 전용입니다**」(`not exported`).
어느 쪽으로 대답하는지는 **교환원이 가진 전화번호부에 그 내선이 적혀 있느냐**에 달렸다 — 공개 연락처의 **안내문에 그 내선이 한 번 인용돼 있으면**(인라인되는 공개 함수가 부르면) 적혀 있다.
`internal` 은 「**본부 전용 층**」이다 — **같은 본부 간판(import 경로 접두)** 을 단 사람만 올라간다. ★ **다른 회사라도 간판 이름이 같으면 올라간다**((2)절).

| 비유 | 실체 |
|---|---|
| 대외 공개 연락처 | ★★★ **첫 글자 유니코드 대문자** — `Ärger` 도 공개, **`한글` 은 비공개**((1)절) |
| 「그런 번호 없습니다」 | ★★ **`undefined: shop.discount`** — 패키지 수준 이름 대부분((1)절) |
| 「사내 전용입니다」 | ★★ **`cannot refer to unexported field/method`** — 필드·메서드((1)절) |
| 안내문에 인용된 내선 | ★★★ **인라인되는 공개 함수가 부르는 소문자 함수** → `name discount not exported by package shop`((3)절) |
| 본부 전용 층 | ★★★ **`a/internal/x`** — `a` 로 시작하는 import 경로만((2)절) |
| 다른 회사, 같은 간판 | ★★★ **모듈 `corp/a/plugin`** — 다른 모듈인데 통과((2)절) |
| 외부 감사(外部監査)는 내선을 못 건다 | ★★ **`package calc_test`** — 비공개를 못 본다((5)절) |

```text
   ★★★ internal 격자 ((2)절의 실측) — 목표는 corp/a/internal/x (다섯째 줄만 corp/a/b/internal/w)

   import 하는 쪽 (import 경로)        모듈           「internal 위」 corp/a 로 시작?   결과
   corp                               corp           아니오                          ✗ 막힘
   corp/a                             corp           예 (부모 그 자체)                ✓
   corp/a/b                           corp           예                              ✓
   corp/a/internal/y                  corp           예 (형제 internal)              ✓
   corp/c                             corp           아니오                          ✗ 막힘
   corp/a/d  → corp/a/b/internal/w    corp           corp/a/b 로 시작? 아니오         ✗ 막힘
   other                              other          아니오                          ✗ 막힘
   corp/a/plugin                      ★ 다른 모듈    예                              ✓ ★

   막힌 칸 4 / 8 — 기준은 디렉토리도 모듈도 아니라 「import 경로의 접두」다
```

> **내보낸다(export)** — 다른 패키지가 `pkg.Name` 으로 쓸 수 있게 하는 것. Go 에는 `public` 같은 낱말이 없고 **첫 글자**가 정한다.

> **`internal` 디렉토리** — 경로에 `internal` 이 든 패키지. `go` 명령이 **import 할 수 있는 쪽을 경로로 제한**한다.

> **내보내기 데이터(export data)** — 컴파일러가 패키지를 컴파일하고 남기는 **「이 패키지가 밖에 보여 줄 것」의 요약**. 다른 패키지는 소스가 아니라 이것을 읽는다. **인라인될 수 있는 함수의 본문**도 여기 실린다.

- ★★ [01번 주제](../01-packages-imports-main-and-init/) — import 네 형태와 초기화 순서. 여기는 **import 한 뒤 무엇이 보이나**다.
- ★★ [25번 주제](../25-sentinel-errors-vs-custom-error-types/) (3)절 — `var nf *opaque.notFound` 가 **`undefined: opaque.notFound`**. 「없다」로 답한 첫 실측이다.

## 이 주제가 답하려는 질문

1. **대문자 한 글자는 무엇을 공개하고, 소문자 이름을 밖에서 쓰면 컴파일러는 무엇이라 말하나** — 「없다」인가 「비공개」인가.
2. **`internal` 은 정확히 누구를 막나** — 디렉토리인가, 모듈인가, 경로인가.
3. **공개 규칙이 조용히 값을 버리는 자리는 어디인가** — `encoding/json` 과 외부 테스트.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **`internal` 격자 — import 하는 자리 8 × 막혔나** | 경계가 **어디에** 그어지나 | ★ 본체 창 |
| ★★ **이름 탐침 13 × 진단의 꼴** | 소문자 이름을 **무슨 말로** 거절하나 | 스크립트가 `// pNN` 주석의 줄 번호와 진단 줄을 맞춘다 |
| ★★★ **같은 줄을 빌드 조건 셋으로** | 진단 문구가 **무엇에 달렸나** | (3)절 · `-gcflags=-m` 이 인라인을 보여 준다 |
| ★★ **`json.Marshal`/`Unmarshal` 결과 + `vet`** | 소문자 필드가 **조용히** 빠지나 | (4)절 |
| ★★ **`go test` × 빌드 태그** | `_test` 패키지가 무엇을 못 보나 | (5)절 |
| ★★ **제5의 상태 — 「기준만 다른 것」** | ★★★ `internal` 은 **모듈 경계처럼 보이는데** 실제 기준은 **import 경로 접두**다. 같은 모듈 안에서만 실험하면 **여덟 칸 중 일곱이 「모듈 경계」로 읽혀도 맞는다** — 여덟째 칸(`corp/a/plugin`)만 그 해석을 깬다 | (2)절 |
| **부적용 — 실행** | 이름·`internal` 격자는 **전부 빌드 단계**다. 실행할 것이 없다 | — |
| **못 잰 것 — Effective Go 의 이름 관례** | `MixedCaps`·패키지 이름·게터 이름 같은 **관례**는 이 머신의 도구가 검사하지 않고, 이 문서는 그 절을 **안 열었다** | 규칙 26 |

### (1) ★★★ 소문자 이름을 밖에서 쓰면 — 탐침 13 개

**언제 쓰나** — 「이 이름을 다른 패키지에서 쓸 수 있나, 못 쓰면 어떤 에러가 나나」를 물을 때.

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

그림 해설 (한 단계씩):

- ★★★ **대문자 셋(`p01` `Name` · `p03` `Label` · `p11` `Ärger`)은 통과.** ★★ **`Ärger` 는 첫 글자가 `Ä`** — 유니코드 **대문자(Lu)** 라 **공개**다. 명세 「**Unicode uppercase letter (Unicode character category Lu)**」 그대로다.
- ★★★ **`p10` 의 `한글` 은 `undefined: shop.한글`** — 한글은 **대소문자가 없는 글자**(Lo)라 **절대 공개될 수 없다.** 한국어로 이름을 지으면 **그 패키지 안에서만** 쓸 수 있다.
- ★★★ **필드·메서드(`p02`·`p04`·`p05`)는 「비공개」라고 말한다** — `it.price undefined (cannot refer to unexported field price)` · `cannot refer to unexported method secret` · 구조체 리터럴에서도 `cannot refer to unexported field price in struct literal`.
  ★ 대조군 `p13`(정말 없는 필드)은 **`has no field or method nothere`** — **꼴이 다르다.** 컴파일러는 **그 필드가 있다는 것을 안다.**
- ★★★ **패키지 수준 이름(`p06`\~`p10` — 함수·변수·상수·타입·한글 함수)은 「없다」라고 말한다** — `undefined: shop.discount`. 대조군 `p12`(정말 없는 이름) `undefined: shop.nothere` 와 **한 글자도 다르지 않은 꼴**이다.
- ★★★ **마지막 줄 `5 / 8`** — 소문자 칸 여덟 중 **다섯이 「없는 이름」과 같은 꼴**, 셋이 「비공개」.

```text
   ★★ 컴파일러가 소문자 이름을 거절하는 두 목소리 — 그리고 C# 과 나란히

                         Go (이 편, 이 판)                            C# (15번 · 다른 어셈블리)
   필드·메서드            「비공개」 cannot refer to unexported …       private → CS1061 「없다」
   패키지 수준 이름        「없다」  undefined: pkg.name                internal → CS1061 「없다」
   ★ 단, 인라인되는 공개    「비공개」 name X not exported by package      protected → CS0122 「막힘」
     함수가 부르면 ((3)절)
```

- ★★ [C# 15번](../../../csharp/syntax/15-access-modifiers-and-assembly-boundary/) (3)절 — 다른 어셈블리에서 `internal`·`private` 멤버는 **`CS1061`(정의가 없다)**, `protected` 는 **`CS0122`(보호 수준 때문에 막힘)**. C# 은 **접근 제한자 종류**가 목소리를 가르고, Go 는 **멤버냐 패키지 수준이냐**가 가른다.

비용 — 없다.

### (2) ★★★ `internal` 격자 — 누가 막히나

`go help` 가 규칙을 한 줄로 적는다(머리말 블록) — 「**importable only by code that shares the same import path above the internal directory**」. 여덟 자리에서 던졌다:

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

그림 해설 (한 단계씩):

- ★★★ **`corp/a`·`corp/a/b`·`corp/a/internal/y` 는 통과** — 셋 다 import 경로가 **`corp/a` 로 시작**한다. 부모 자신, 그 아래, **다른 `internal` 안의 형제**까지.
- ★★★ **`corp`(모듈 루트)는 막혔다** — **부모의 부모**는 안 된다. `internal` 의 「위」 는 **바로 위 한 칸(`corp/a`)** 이다.
- ★★ **`corp/c` 막힘** — 같은 모듈이어도 경로가 `corp/a` 로 안 시작한다.
- ★★ **`corp/a/d` → `corp/a/b/internal/w` 막힘** — 깊은 `internal` 의 「위」 는 `corp/a/b` 다. `corp/a` 는 **그 위의 부모**라 못 들어간다.
- ★★ **`other` 모듈 막힘** — `use of internal package corp/a/internal/x not allowed`.
- ★★★ **`corp/a/plugin` 모듈은 통과했다** — **다른 모듈**(`go.mod` 가 따로 있고 `replace` 로 `corp` 를 가져왔다)인데, **모듈 경로가 `corp/a/plugin`** 이라 **import 경로 접두 `corp/a` 를 공유**한다.
  ★★★ **`internal` 의 기준은 모듈 경계가 아니라 import 경로다** — `go help` 의 문장 그대로다. 「다른 모듈에서는 `internal` 을 못 쓴다」는 **대개 맞지만 규칙이 아니다.**
- ★★★ **마지막 줄 `막힌 칸 4 / 8`.**

- ★★ [C# 15번](../../../csharp/syntax/15-access-modifiers-and-assembly-boundary/) — C# `internal` 은 **어셈블리 단위**(빌드 산출물 하나)다. Go `internal` 은 **경로 단위**다. C# 은 `InternalsVisibleTo` 로 **대상을 이름으로** 열고, Go 는 **경로를 그 아래로 옮겨야** 열린다.
- ★ Java — [Java 10번](../../../java/syntax/10-access-modifiers/)이 「`module-info.java` 가 `exports` 하지 않은 패키지는 `public` 이어도 밖에서 못 쓴다」를 **언급만** 했다(모듈을 목록에서 뺐다). Go 의 `internal` 과 **자리가 같다** — 「공개인데 안 보인다」.

비용 — 없다.

### (3) ★★★ 「없다」와 「비공개」를 가르는 것 — 다른 함수의 인라인

(1)절에서 패키지 수준 소문자 이름은 「없다」였다. 그런데 공개 함수가 **그 이름을 부르고, 그 공개 함수가 인라인될 수 있으면**:

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

그림 해설 (한 단계씩):

- ★★ 앞 다섯 줄은 `-gcflags=-m`(인라인 판정)이다. **기본 판에서는 `can inline Price`**, `noinl` 판에서는 **`Price` 에 그 줄이 없다**(`//go:noinline`).
- ★★★ **`[기본]` — `name discount not exported by package shop`** — 「**비공개**」다.
  **`[noinl]`·`[인라인끔]` — `undefined: shop.discount`** — 「**없다**」다. **`app` 의 소스는 한 글자도 안 바뀌었다.**
- ★★★ **왜** — `Price` 가 인라인될 수 있으면 컴파일러는 그 **본문을 내보내기 데이터에 싣는다** — 다른 패키지가 `Price()` 를 **자기 안에 펼쳐 넣을 수** 있게. 그 본문이 `discount` 를 부르므로 **`discount` 도 실린다.** `app` 을 컴파일할 때 컴파일러는 `shop` 의 **소스가 아니라 내보내기 데이터**를 읽는다 — 거기 `discount` 가 **있으면 「비공개」, 없으면 「없다」** 가 된다.
  ★ 이 설명은 **`-gcflags=-m` 과 세 결과를 잇는 추론**이다 — 내보내기 데이터 파일 자체는 **열어 보지 않았다.**
- ★★★ **그래서 이 진단 문구는 근거가 못 된다**(규칙 27) — **`exit=1`**(막혔다)만 근거다. 「Go 는 비공개 이름을 없다고 말한다」도 「비공개라고 말한다」도 **한 판·한 플래그의 관찰**이다.

비용 — 없다.

### (4) ★★ `encoding/json` — 소문자 필드는 조용히 빠진다

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

- ★★★ **`Marshal : {"Name":"kim","age":30}`** — `email`·`token` 이 **없다.** 에러는 **`<nil>`**.
- ★★★ **`Unmarshal: {Name:lee email: Age:4 token:}`** — JSON 에 `"email"`·`"token"` 이 **있는데 안 채워졌다.** 역시 **`<nil>`**.
  `encoding/json` 은 `reflect` 로 필드를 보는데, **패키지 밖(`encoding/json`)에서 소문자 필드는 쓸 수 없다** — (1)절의 규칙이 **실행 시간에 조용히** 나타난 것이다.
- ★★ **`vet` 은 `token` 만 잡았다** — `struct field token has json tag but is not exported`. **태그가 달린** 소문자 필드는 「실수」로 보고, **태그 없는 `email` 은 침묵**했다(일부러 감춘 것일 수 있으니까). `vet exit=1` 인데 **빌드·실행은 된다.**

비용 — 없다.

### (5) ★★ 외부 테스트 패키지 — `package calc_test`

`go help test` — 「`_test` 로 끝나는 패키지를 선언한 테스트 파일은 **별도 패키지로 컴파일**된다」. 그러면 비공개를 못 본다:

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

- ★★ **첫 판(`ext` 태그 없음) — `ok`** — **같은 패키지(`package calc`)의 테스트는 `add` 를 부를 수 있다.**
- ★★★ **`-tags ext` — `name add not exported by package calc`** · `FAIL … [build failed]`. 외부 테스트는 **다른 패키지**라 (1)절의 규칙을 그대로 받는다. **테스트 파일 하나가 깨지면 그 패키지의 테스트 전부가 안 돈다**(`TestAddInside` 도 안 돌았다).
- ★★★ **`-tags ext -gcflags=all=-l` — `undefined: calc.add (but have Add)`** — 같은 줄이 **세 번째 문구**를 냈다. `Add` 가 인라인되지 않으면 `add` 가 내보내기 데이터에 안 실리고((3)절), 컴파일러는 **대소문자만 다른 `Add` 가 있다**고 귀띔한다.
- ★ 그래서 외부 테스트는 **공개 API 만으로 쓴 테스트**가 된다 — 「사용자가 보는 것만 시험한다」는 뜻으로 일부러 쓰는 형태다.

비용 — 없다.

## 문법 — 형태와 규칙

### 형태

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

규칙 불릿.

- ★★★ **첫 글자가 유니코드 대문자(Lu)면 공개** — 패키지 블록의 이름·필드·메서드. **한글·숫자·`_` 로 시작하면 비공개.**
- ★★★ **공개한 이름은 전부 계약**이다 — 이름·시그니처·필드를 바꾸면 **호출부가 컴파일 에러로 깨진다**([25번 주제](../25-sentinel-errors-vs-custom-error-types/) (3)절). 비공개만 마음대로 고칠 수 있다.
- ★★★ **`x/internal/…` 는 `x` 로 시작하는 import 경로만** import 한다 — 모듈 경계가 아니다.
- ★★ `encoding/json`·`reflect` 에 쓰일 필드는 **대문자**로. 키 이름은 태그로(`json:"age"`).
- ★★ **`package p_test`** 는 공개 API 만 본다 · **`package p`** 테스트는 비공개까지 본다.

### 금지 사례 — 누가 잡나

| 쓴 꼴 | 누가 잡나 | 어디서 |
|---|---|---|
| 다른 패키지에서 `shop.discount()` | 컴파일러 — `undefined:` 또는 `not exported`(★ 문구는 인라인에 달림) | (1)·(3)절 |
| 다른 패키지에서 `it.price` | 컴파일러 — `cannot refer to unexported field` | (1)절 |
| `func 한글()` 을 공개하려 함 | 컴파일러(쓰는 쪽) — `undefined:` | (1)절 |
| 경로 밖에서 `…/internal/…` | **`go` 명령** — `use of internal package … not allowed` | (2)절 |
| 소문자 필드를 JSON 으로 | ★★★ **아무도 안 잡는다**(태그가 없으면) · 태그가 있으면 `vet` | (4)절 |
| `_test` 패키지에서 비공개 호출 | 컴파일러 — 테스트 **전체**가 빌드 실패 | (5)절 |

## 어디서 틀리나

### 1. ★★★ 「Go 는 비공개 이름을 쓰면 『비공개』라고 알려 준다」

- (1)절 — **패키지 수준 이름은 대개 `undefined:`**(없는 이름과 같은 꼴, `5 / 8`). (3)절 — 그마저 **다른 함수의 인라인**에 따라 바뀐다.

### 2. ★★★ 「`internal` 은 다른 모듈에서 못 쓴다」

- (2)절 — **`corp/a/plugin` 모듈은 썼다.** 기준은 **import 경로 접두**다.

### 3. ★★ 「`internal` 은 모듈 루트에서는 쓸 수 있다」

- (2)절 — **`corp` 루트는 막혔다.** `a/internal` 의 「위」 는 `corp/a` 다.

### 4. ★★ 「한글로 함수 이름을 지으면 다른 패키지에서 부를 수 있다」

- (1)절 `p10` — **한글에는 대문자가 없다.** 절대 공개되지 않는다.

### 5. ★★★ 「JSON 이 안 채워지면 에러가 난다」

- (4)절 — **`err` 가 `<nil>`** 이다. 소문자 필드는 조용히 빠진다. `vet` 은 **태그가 있을 때만** 말한다.

### 6. ★ 「외부 테스트 파일 하나쯤 깨져도 나머지 테스트는 돈다」

- (5)절 — **`[build failed]`** — 그 패키지의 테스트가 **하나도 안 돈다.**

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| ★★★ **첫 글자 유니코드 대문자(Lu) → 공개** | **명세** | (1)절 · 머리말 `t40spec` |
| 한글 이름은 공개 불가 | **명세의 귀결**(Lo 는 Lu 가 아니다) | (1)절 `p10` |
| ★★★ **`internal` — import 경로 접두 규칙** | **`go` 명령의 규칙** — 명세에 없다 | (2)절 · `t40help` · `t40specint` |
| `_test` 패키지는 별도 패키지 | **`go` 명령의 규칙** | (5)절 |
| ★★★ **`undefined:` 대 `not exported` 대 `(but have Add)`** | **구현(gc)** — 내보내기 데이터에 달림 | (3)·(5)절 |
| 소문자 필드를 `json` 이 건너뜀 | **표준 라이브러리**(`reflect` 가 비공개 필드를 못 씀) | (4)절 |
| `vet structtag` 이 태그 달린 소문자만 | **도구(`vet`)의 휴리스틱** | (4)절 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 모듈 안의 여러 패키지가 나눠 쓰지만 **사용자에게는 감출** 코드 | ★★★ **`internal/`** — 가장 넓은 공유자 바로 아래에 | (2)절 |
| 한 패키지 안에서만 쓰는 것 | **소문자 이름** | (1)절 |
| JSON 으로 오갈 필드 | **대문자 + 태그** | (4)절 |
| 공개 API 만으로 시험 | **`package p_test`** | (5)절 |
| 비공개 도우미까지 시험 | **`package p`** 테스트 | (5)절 |
| 외부에 **정말로** 안 보여야 한다(다른 조직의 모듈) | ★ `internal` 만 믿지 않는다 — **경로 접두를 공유하는 모듈**은 들어온다 | (2)절 `plugin` |

## 핵심 문장

- ★★★ **공개 = 첫 글자 유니코드 대문자(Lu)** — `Ärger` 는 공개, **`한글` 은 영원히 비공개.** 공개한 이름은 전부 계약이다.
- ★★★ **소문자 필드·메서드는 「비공개」(`cannot refer to unexported`), 패키지 수준 이름은 대개 「없다」(`undefined:`)** — `5 / 8`.
- ★★★ **그 문구는 다른 함수의 인라인에 달렸다** — 인라인되는 공개 함수가 부르면 `not exported by package`, `-l`·`noinline` 이면 `undefined:`. **근거는 `exit=1` 이다.**
- ★★★ **`internal` 은 명세가 아니라 `go` 명령의 규칙 — 기준은 import 경로 접두** — `막힌 칸 4 / 8`, **다른 모듈 `corp/a/plugin` 이 통과했다.**
- ★★ **소문자 필드는 `json` 이 조용히 버린다(`err` `<nil>`)** — `vet` 은 태그 달린 것만 잡는다.
- ★★ **`package p_test` 는 비공개를 못 본다 — 한 파일이 깨지면 그 패키지의 테스트 전부가 안 돈다.**

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 40번)
- [01번 주제](../01-packages-imports-main-and-init/)(패키지·import·`init`) — ★ 목록상 선행 · **초기화 순서의 정본** — 이름 규칙은 이쪽으로 넘겼다
- [25번 주제](../25-sentinel-errors-vs-custom-error-types/)(오류 표면 설계) — `undefined: opaque.notFound` · 공개 API 로서의 오류
- [17번 주제](../17-struct-literals-comparability-field-tags-and-sorting/)(필드 태그) — 태그는 `reflect` 로만 보인다
- 목록의 **41번 주제**(모듈·`go.mod`) — `replace`·버전 선택의 정본 · 목록의 **45번 주제**(`encoding/json`) · 목록의 **49번 주제**(`testing`)
- [C# 15번](../../../csharp/syntax/15-access-modifiers-and-assembly-boundary/) — ★★ **`CS1061`(없다) 대 `CS0122`(막힘) · 어셈블리 경계** · [Java 10번](../../../java/syntax/10-access-modifiers/) — package-private · 모듈 `exports`(언급)

## 용어 풀이

- **내보낸(exported) 이름** — 첫 글자가 유니코드 대문자(Lu)인 패키지 수준 이름·필드·메서드.
- **유니코드 Lu / Lo** — 대문자 / 대소문자가 없는 글자(한글·한자 등).
- **`internal` 디렉토리** — 그 바로 위 경로를 접두로 가진 패키지만 import 할 수 있게 `go` 명령이 막는 디렉토리.
- **import 경로** — 모듈 경로 + 모듈 안의 상대 디렉토리.
- **내보내기 데이터(export data)** — 컴파일된 패키지가 다른 패키지에게 보여 주는 요약. 인라인 가능한 본문을 담는다.
- **인라인(inlining)** — 함수 호출을 그 본문으로 바꿔 넣는 최적화. `-gcflags=-m` 이 판정을 보여 준다.
- **외부 테스트 패키지** — `package p_test`. 테스트 대상과 **다른 패키지**로 컴파일된다.
- **`vet structtag`** — 태그 형식과 「태그 달린 비공개 필드」를 보는 분석기.

---

## 더 들어가면

- ★ `go help importpath` 가 가리키는 설계 문서(go14internal)와 Effective Go 의 이름 절(`MixedCaps`·패키지 이름·게터)은 **안 열었다.**
- ★ `vendor/` 의 가시성 규칙은 `go help gopath` 가 「internal 과 같은 규칙」이라 적는다 — **GOPATH 모드 이야기라 던지지 않았다.**
- ★ 내보내기 데이터 파일을 직접 풀어 `discount` 가 실렸는지 보는 것(`go tool` 의 해당 도구)은 **하지 않았다** — (3)절은 행동으로만 갈랐다.

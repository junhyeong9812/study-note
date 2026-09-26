# go/syntax/25 — 센티넬 오류 대 커스텀 오류 타입 — 오류 표면 설계 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [`errors`](https://pkg.go.dev/errors) · [`io`](https://pkg.go.dev/io) · [`io/fs`](https://pkg.go.dev/io/fs) · [`os`](https://pkg.go.dev/os) · [`net`](https://pkg.go.dev/net) 문서.
> 웹이 아니라 **이 툴체인에게 `go doc` 으로 직접 물었다** — 계약의 원문이 캡처 블록 그대로 근거다.\
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> **버전** — 이 주제에 새 판 경계는 없다. 기대는 API 가 전부 앞 주제의 것이다 —
> `%w`·`errors.Is`/`As` 가 **1.13**, `errors.AsType` 이 **1.26**([24번 주제](../24-error-wrapping-and-errors-is-as-join/) (9)절이 `api/go1NN.txt` 로 뗐다).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체는 넷째 창이다** — 「**같은 패키지를 세 설계로 쓰고, 호출부 코드가 무엇으로 분기하게 되나를 나란히 보는 창**」.
그리고 그 짝으로 「**`go doc -all` 로 패키지가 밖에 내보인 표면을 찍는 창**」.
설계는 말로 하면 취향 싸움이 되는데, **호출부 코드 모양과 공개 표면을 글자로 찍으면** 차이가 사실이 된다.

★★ **이 주제는 [21번](../21-nil-interface-vs-interface-holding-nil-pointer/)~[24번 주제](../24-error-wrapping-and-errors-is-as-join/) 오류 묶음의 결론이다.**
21\~24 가 「오류 값이 무엇이고 어떻게 감싸고 어떻게 묻나」였다면, 여기는 「**그래서 내 패키지는 무엇을 공개하나**」다.
앞 편이 이미 잰 것은 다시 재지 않고 인용한다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | ★ **대문자로 시작하는 이름만 패키지 밖에 보인다**는 것 하나 — 설계의 뼈대가 이 한 줄이다 |
| **표준 라이브러리 계약** | `errors`·`io`·`os`·`net` 이 문서로 약속한 것 | `go doc` 캡처 — `io.EOF` 의 「감싸지 마라」, `os.IsNotExist` 의 「새 코드는 `errors.Is`」 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 실행 출력(재실행 대조까지) |

★ **「어느 설계가 좋은가」는 셋 어디에도 없다** — 이 문서가 표로 세우는 판단 기준은 **내 추론**이고, 그렇게 표시한다.

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ 각 분기 식의 **참거짓**(`==`·`Is`·`As`·단언) | 값과 타입 구조가 정한다 — 이 주제의 핵심 근거 |
| 안 흔들린다 | `go doc -all` 이 내보인 **공개 표면**(이름·타입·필드) | 소스의 대소문자가 정한다 |
| 안 흔들린다 | 컴파일 에러의 **`파일:줄:칸`과 문장** · 종료 코드 | 툴체인이 정한 문장이다 |
| 안 흔들린다 | 표준 라이브러리 `go doc` **본문**과 소스 줄 번호 | 이 툴체인 판에 든 파일이다 |
| 해당 없음 | 주소·고루틴·시간 | 이 주제는 패닉도 동시성도 싣지 않는다 |

★ **정규화 규칙은 하나도 안 썼다.** 이 문서의 블록은 재실행에서 전부 한 글자도 같았다.

## 한눈에 — 쉽게 말하면

**오류를 돌려주는 쪽이 정하는 것은 「받는 쪽이 무엇으로 갈라 읽게 하나」다.**
방법이 셋이다 — ① **정해 둔 값 하나**를 알려 주고 「이 값이냐」를 묻게 하거나,
② **타입**을 알려 주고 꺼내 필드를 읽게 하거나, ③ 타입은 감추고 **「이런 성질이 있냐」만** 묻게 한다.

| 비유 | 실체 |
|---|---|
| 「품절」이라는 **정해진 도장** 하나를 찍어 돌려준다 | ★ **센티넬** — `var ErrNotFound = errors.New(…)`. 받는 쪽은 `errors.Is` |
| 도장 대신 **「무엇이 몇 개 모자란지」 적힌 쪽지**를 돌려준다 | ★ **커스텀 타입** — `type NotFoundError struct{…}`. 받는 쪽은 `errors.As` |
| 쪽지 양식은 비밀이고 **「다시 오면 되나요?」에만 답해 준다** | ★ **불투명 + 동작** — 타입을 감추고 `NotFound() bool` 같은 메서드만 약속 |
| 도장의 **이름을 바꾸면** 받는 쪽 서류가 전부 무효가 된다 | ★★★ 센티넬 이름은 **공개 API** — 바꾸면 **컴파일 에러**((3)절) |
| 비밀 양식은 **마음대로 고쳐도** 받는 쪽이 모른다 | ★★ 감춘 타입은 **이름·필드를 바꿔도** 호출부가 안 깨진다((3)절) |
| 도장에 **글씨로 사연을 덧쓰면** 「이 도장이냐」를 글자로 못 맞춘다 | ★★ **오류 문자열 비교** — 문맥이 한 겹 붙으면 끝((4)절) |

```text
   ★★★ 같은 「없음」을 세 설계로 — 호출부가 쓰게 되는 식이 다르다 ((1)절의 실측)

   패키지가 공개한 것           호출부가 쓰는 식                         얻는 것
   ─────────────────────────   ──────────────────────────────────────   ───────────
   var ErrNotFound             errors.Is(err, sentinel.ErrNotFound)     신원(예/아니오)
   (값 하나)                   ✗ err == ErrNotFound — 감싸면 false

   type NotFoundError struct   var nf *typed.NotFoundError              값(Key·Tried)
   (타입 + 필드)               errors.As(err, &nf)
                               ✗ err.(*typed.NotFoundError) — 맨 위만 본다

   func IsNotFound(err) bool   opaque.IsNotFound(err)                   성질(예/아니오)
   (타입은 감춤)               또는 errors.As(err, &interface{ NotFound() bool })
                               ✗ *opaque.notFound — 이름을 적을 수 없다
```

```text
   ★★ 공개한 만큼이 계약이다 — 바꾸면 누가 깨지나 ((3)절의 실측)

                      공개 표면(go doc -all)            다음 판에서 바꾸면
   센티넬판      var ErrNotFound · func Get          이름 변경 → 호출부 컴파일 에러
   타입판        type NotFoundError{Key, Tried}      필드 삭제·이름 변경 → 호출부 컴파일 에러
   불투명판      func Get · func IsNotFound          감춘 타입 이름·필드 전부 변경 → 호출부 무사
```

> **센티넬 오류(sentinel error)** — 패키지 수준 변수로 공개한 **정해진 오류 값**. `io.EOF`·`os.ErrNotExist` 가 대표다.\
> 신원(같은 값인가)으로만 묻는다 — 문맥을 안 싣는다.

> **커스텀 오류 타입** — `Error() string` 을 가진 **공개 타입**. 필드로 문맥을 싣는다. `*fs.PathError` 가 대표다.

> **불투명 오류(opaque error)** — 타입을 공개하지 않은 오류. 호출부는 **메서드(동작)** 나 **도우미 함수**로만 묻는다.
> `net.Error` 의 `Timeout()` 이 대표다.

- [24번 주제](../24-error-wrapping-and-errors-is-as-join/)가 **이 주제의 직접 선행**이다. 거기서 결론난 것 셋 —
  ① `%w` 로 감싸야 `Is`/`As` 가 찾는다 ② `Is` 는 신원, `As` 는 값 ③ ★★ `errors.Is(top, os.ErrNotExist)` 가
  **`syscall.Errno` 의 자기 `Is` 메서드**로 참이 된다. ★ ③이 이 주제에서 「**타입이 센티넬 질문에 답한다**」는 표준의 실례가 된다((4)절).
- Rust 와 다른 점 — ★★ Rust 는 오류를 **`enum` 하나**로 공개하는 쪽이 기본이라 **호출부가 `match` 로 전부 다뤘는지 컴파일러가 센다**.
  Go 에는 그 검사가 원리상 없다 — 센티넬·타입·동작 **어느 것을 골라도** 「빠뜨린 분기」를 아무도 안 알려 준다.
  (Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **24번**.)
- 자바와 다른 점 — 자바는 **예외 클래스 계층**이 곧 오류 표면이고 `catch` 가 타입으로 가른다.
  Go 의 「커스텀 타입판」이 거기 가장 가깝지만 **상속이 없어** 「넓게 잡기」를 계층이 아니라 **동작 인터페이스**로 한다.
  ([23번 주제](../23-error-interface-and-errors-as-values/)가 그 차이를 호출부 줄 수로 셌다 — **Java multi-catch 의 상속 제약이 Go 엔 원리상 없다**.)

## 이 주제가 답하려는 질문

1. **호출자는 무엇으로 분기하게 되나** — 센티넬·커스텀 타입·불투명(동작) 셋이 호출부 코드 모양을 어떻게 바꾸나.
2. **무엇을 공개하면 무엇이 계약이 되나** — 이름을 바꾸면 누가 깨지나.
3. **어느 오류를 분기 대상으로 공개하고, 어느 오류는 로그로 충분한가.**

★ **실패를 어떻게 분류하나**(재시도할 것·사람이 볼 것·버릴 것)라는 일반론은
[`ops-patterns/failure-modes/`](../../../../../ops-patterns/failure-modes/)가 정본이다 —
**그쪽은 실패의 분류까지**, 여기는 **그 분류를 Go 오류 값의 공개 표면으로 옮기는 법부터**.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| **분기 식의 참거짓을 찍기** | `==`·`Is`·`As`·단언이 각 설계에서 되나 | [24번 주제](../24-error-wrapping-and-errors-is-as-join/)에서 쓰던 창 |
| ★★★ **같은 패키지를 세 설계로 쓰고 호출부를 나란히** | 호출부가 **무엇을 적게 되나** | ★ 본체 창 — 이 주제의 넷째 창 |
| ★★ **`go doc -all ./패키지` 로 공개 표면 찍기** | 설계가 **밖에 내보인 것**의 목록 | ★ 이 주제의 고유 창 |
| ★★ **다음 판을 흉내 내 고치고 호출부를 다시 빌드** | 공개한 것이 **계약**이라는 것(컴파일 에러) | ★ 이 주제의 고유 창 |
| ★ **표준 라이브러리를 `go doc` 으로 뜨기** | 세 설계가 **표준 안에 다 있다** | [24번 주제](../24-error-wrapping-and-errors-is-as-join/) (9)절의 `go doc errors` |
| **부적용 — `go.mod` 판 격자** | **잴 것이 없다.** 새 API 도 새 언어 기능도 안 쓴다 | — |
| **부적용 — 벤치마크** | 안 쟀다. 「센티넬이 싸다」·「타입 단언이 비싸다」 같은 말을 이 문서는 하지 않는다 | — |
| **부적용 — `go vet`** | 이 주제의 실수(문자열 비교·옛 도우미)를 잡는 분석기가 **기본 목록에 없다**. [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/) (6)절이 분석기 목록을 이미 찍었다 | — |

★★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.**
「어느 설계가 **계약이 무겁나**」는 실행으로는 못 묻는다 — 출력은 셋 다 「없음」을 잘 알려 준다.
그래서 **컴파일러에게 물었다** — 「다음 판에서 이렇게 바꾸면 호출부가 빌드되나」((3)절).
★ 바꾼 창의 한계 — 컴파일러는 **이름과 타입**만 본다. **오류 문구를 바꿔서 깨지는 호출부**(문자열 비교)는
컴파일이 잘 되고 **실행해야만** 드러난다((4)절). 그래서 두 창을 같이 쓴다.

### (1) ★★★ 같은 「없음」을 세 설계로 — 호출부가 쓰게 되는 식

**언제 쓰나** — 패키지가 「못 찾았다」를 밖에 알려야 할 때. 세 판 모두 `Get` 이 **`%w` 로 문맥을 붙여** 돌려준다.

```go
// t25sentinel.go
// Package sentinel 은 「없음」을 공개 변수 하나로 알린다.
package sentinel

import (
	"errors"
	"fmt"
)

// ErrNotFound 는 키가 없을 때 돌려준다. 이 이름이 곧 공개 API 다.
var ErrNotFound = errors.New("키 없음")

var data = map[string]string{"a": "1"}

// Get 은 키를 찾는다. 못 찾으면 ErrNotFound 에 문맥을 붙여 %w 로 감싼다.
func Get(key string) (string, error) {
	v, ok := data[key]
	if !ok {
		return "", fmt.Errorf("sentinel.Get(%q): %w", key, ErrNotFound)
	}
	return v, nil
}
```

```go
// t25typed.go
// Package typed 는 「없음」을 공개 타입으로 알리고 문맥을 필드에 싣는다.
package typed

import "fmt"

// NotFoundError 는 무엇을 몇 곳에서 찾았는지 싣는다. 이 타입과 필드가 공개 API 다.
type NotFoundError struct {
	Key   string
	Tried int
}

func (e *NotFoundError) Error() string {
	return fmt.Sprintf("키 %q 없음(%d곳 찾음)", e.Key, e.Tried)
}

// Get 은 키를 찾는다. 못 찾으면 *NotFoundError 를 감싸 돌려준다.
func Get(key string) (string, error) {
	if key == "a" {
		return "1", nil
	}
	return "", fmt.Errorf("typed.Get: %w", &NotFoundError{Key: key, Tried: 3})
}
```

```go
// t25opaque.go
// Package opaque 는 오류 타입을 감추고 「동작」만 공개한다.
package opaque

import (
	"errors"
	"fmt"
)

// notFound 는 공개하지 않는다 — 호출자는 이 이름을 적을 수 없다.
type notFound struct{ key string }

func (e *notFound) Error() string  { return "키 " + e.key + " 없음" }
func (e *notFound) NotFound() bool { return true }

// Get 은 키를 찾는다. 못 찾으면 감춘 타입을 감싸 돌려준다.
func Get(key string) (string, error) {
	if key == "a" {
		return "1", nil
	}
	return "", fmt.Errorf("opaque.Get: %w", &notFound{key: key})
}

// IsNotFound 는 「없음」인지 묻는 공개 도우미다. 사슬을 따라간다.
func IsNotFound(err error) bool {
	var b interface{ NotFound() bool }
	return errors.As(err, &b) && b.NotFound()
}
```

```go
// t25main.go
package main

import (
	"errors"
	"fmt"

	"ex/opaque"
	"ex/sentinel"
	"ex/typed"
)

func main() {
	fmt.Println("== 1. 센티넬판 — 호출부는 값의 신원을 묻는다 ==")
	_, err := sentinel.Get("zz")
	fmt.Printf("  err = %v\n", err)
	fmt.Printf("  err == sentinel.ErrNotFound          : %v\n", err == sentinel.ErrNotFound)
	fmt.Printf("  errors.Is(err, sentinel.ErrNotFound) : %v\n", errors.Is(err, sentinel.ErrNotFound))

	fmt.Println("== 2. 커스텀 타입판 — 호출부는 타입을 꺼내 필드를 읽는다 ==")
	_, err = typed.Get("zz")
	fmt.Printf("  err = %v\n", err)
	var nf *typed.NotFoundError
	ok := errors.As(err, &nf)
	fmt.Printf("  errors.As(err, &nf) : %v   nf.Key=%q nf.Tried=%d\n", ok, nf.Key, nf.Tried)
	_, direct := err.(*typed.NotFoundError)
	fmt.Printf("  err.(*typed.NotFoundError) 의 ok : %v   <- 맨 위 층만 본다\n", direct)

	fmt.Println("== 3. 불투명판 — 호출부는 타입을 모르고 동작만 묻는다 ==")
	_, err = opaque.Get("zz")
	fmt.Printf("  err = %v   %%T = %T\n", err, err)
	var b interface{ NotFound() bool }
	fmt.Printf("  errors.As(err, &b) && b.NotFound() : %v\n", errors.As(err, &b) && b.NotFound())
	_, direct = err.(interface{ NotFound() bool })
	fmt.Printf("  err.(interface{ NotFound() bool }) 의 ok : %v   <- 맨 위 층만 본다\n", direct)
	fmt.Printf("  opaque.IsNotFound(err) : %v\n", opaque.IsNotFound(err))
	fmt.Printf("  감춘 층의 %%T : %T   <- 이름은 보이지만 호출부 코드에 적을 수는 없다\n", errors.Unwrap(err))
}
```

```text
===== 명령: go build -trimpath -o prog . && ./prog =====
== 1. 센티넬판 — 호출부는 값의 신원을 묻는다 ==
  err = sentinel.Get("zz"): 키 없음
  err == sentinel.ErrNotFound          : false
  errors.Is(err, sentinel.ErrNotFound) : true
== 2. 커스텀 타입판 — 호출부는 타입을 꺼내 필드를 읽는다 ==
  err = typed.Get: 키 "zz" 없음(3곳 찾음)
  errors.As(err, &nf) : true   nf.Key="zz" nf.Tried=3
  err.(*typed.NotFoundError) 의 ok : false   <- 맨 위 층만 본다
== 3. 불투명판 — 호출부는 타입을 모르고 동작만 묻는다 ==
  err = opaque.Get: 키 zz 없음   %T = *fmt.wrapError
  errors.As(err, &b) && b.NotFound() : true
  err.(interface{ NotFound() bool }) 의 ok : false   <- 맨 위 층만 본다
  opaque.IsNotFound(err) : true
  감춘 층의 %T : *opaque.notFound   <- 이름은 보이지만 호출부 코드에 적을 수는 없다
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **센티넬판** — 호출부가 쓰는 것은 **`errors.Is(err, sentinel.ErrNotFound)`** 이고 `true` 다.
  ★ **`err == sentinel.ErrNotFound` 는 `false`** — 패키지가 문맥을 한 겹 붙였기 때문이다.
  [23번 주제](../23-error-interface-and-errors-as-values/) (2)절의 「한 겹만 감싸도 `==` 가 깨진다」가 **설계 안에서** 다시 나온 것이다.
- ★★★ **커스텀 타입판** — 호출부가 쓰는 것은 **`errors.As(err, &nf)`** 이고 **필드(`Key`·`Tried`)가 나온다.**
  ★ 센티넬판은 「없다」만 알려 줬고 이 판은 **「무엇이, 몇 곳을 찾고도」까지** 알려 준다 — 이것이 타입을 공개하는 값이다.
  ★ **`err.(*typed.NotFoundError)` 는 `false`** — 타입 단언은 맨 위 층(`*fmt.wrapError`)만 본다.
- ★★★ **불투명판** — `%T` 가 **`*fmt.wrapError`** 이고, 한 겹 풀면 **`*opaque.notFound`** 가 보인다.
  ★ **이름은 찍히지만 호출부 코드에 적을 수 없다**((3)절이 던진다).
  그래서 호출부는 **`errors.As(err, &b)` 에 익명 인터페이스**를 주거나 **`opaque.IsNotFound(err)`** 를 부른다 — 둘 다 `true`.
  ★ 여기서도 **인터페이스 단언 `err.(interface{ NotFound() bool })` 은 `false`** 다. 맨 위 층이 그 메서드를 안 갖고 있어서다.
- ★★ **세 판의 공통점이 이 절의 결론이다** — **문맥을 붙이는 순간 「맨 위 층만 보는 식」(`==`·타입 단언)은 전부 틀린다.**
  남는 것은 **`Is`·`As`·그것을 감싼 도우미**뿐이다. 설계가 달라도 **호출부의 규칙은 하나**다.

비용 — 없다(재지 않았다).

### (2) ★★ 공개 표면을 `go doc -all` 로 — 밖에서 보이는 것

**언제 쓰나** — 「내 패키지의 오류가 무엇을 약속하나」를 확인할 때. **호출자가 보는 것은 소스가 아니라 이 목록이다.**

```text
===== 명령: for p in sentinel typed opaque; do echo "--- go doc -all ./$p"; go doc -all ./$p; done =====
--- go doc -all ./sentinel
package sentinel // import "ex/sentinel"

Package sentinel 은 「없음」을 공개 변수 하나로 알린다.

VARIABLES

var ErrNotFound = errors.New("키 없음")
    ErrNotFound 는 키가 없을 때 돌려준다. 이 이름이 곧 공개 API 다.


FUNCTIONS

func Get(key string) (string, error)
    Get 은 키를 찾는다. 못 찾으면 ErrNotFound 에 문맥을 붙여 %w 로 감싼다.

--- go doc -all ./typed
package typed // import "ex/typed"

Package typed 는 「없음」을 공개 타입으로 알리고 문맥을 필드에 싣는다.

FUNCTIONS

func Get(key string) (string, error)
    Get 은 키를 찾는다. 못 찾으면 *NotFoundError 를 감싸 돌려준다.


TYPES

type NotFoundError struct {
	Key   string
	Tried int
}
    NotFoundError 는 무엇을 몇 곳에서 찾았는지 싣는다. 이 타입과 필드가 공개 API 다.

func (e *NotFoundError) Error() string

--- go doc -all ./opaque
package opaque // import "ex/opaque"

Package opaque 는 오류 타입을 감추고 「동작」만 공개한다.

FUNCTIONS

func Get(key string) (string, error)
    Get 은 키를 찾는다. 못 찾으면 감춘 타입을 감싸 돌려준다.

func IsNotFound(err error) bool
    IsNotFound 는 「없음」인지 묻는 공개 도우미다. 사슬을 따라간다.
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **센티넬판의 표면은 `var ErrNotFound` 한 줄**이다 — 그 **이름과 값의 신원**이 계약이다.
  ★ 문구(`"키 없음"`)도 표면에 찍혀 있다 — 사람이 그것을 **문자열로 비교하고 싶어지는 자리**다((4)절).
- ★★★ **타입판의 표면은 `type NotFoundError struct { Key; Tried }` 와 `Error()`** 다 — **필드 이름과 타입까지** 계약이다.
  ★ 필드 하나를 지우면 그것을 읽던 호출부가 깨진다. **타입을 공개한다는 것은 필드를 공개한다는 것**이다.
- ★★★ **불투명판의 표면에는 오류 타입이 아예 없다** — `func Get` 과 `func IsNotFound` 둘뿐이다.
  `notFound` 는 소문자라 **목록에서 빠졌다.** ★ 약속한 것은 「**없음이면 `IsNotFound` 가 참이다**」 하나다.
- ★ **이 목록의 차이가 곧 「고칠 자유」의 차이**다 — 다음 절이 그것을 컴파일러로 확인한다.

### (3) ★★★ 다음 판에서 바꾸면 — 컴파일러가 계약을 집행한다

**언제 쓰나** — 오류 이름이나 타입을 고치고 싶을 때. **공개한 것은 이미 남의 코드에 박혀 있다.**

★ 다음 판을 흉내 냈다 — **센티넬 이름을 `ErrNotFound` → `ErrMissing` 으로**, 불투명판은 **감춘 타입의 이름과 필드를 통째로** 바꿨다.
**호출부는 한 글자도 안 바꿨다.**

```go
// t25rensent.go
// Package sentinel — 다음 판에서 센티넬 이름을 바꿨다.
package sentinel

import (
	"errors"
	"fmt"
)

// ErrMissing 은 예전 이름이 ErrNotFound 였다.
var ErrMissing = errors.New("키 없음")

func Get(key string) (string, error) {
	return "", fmt.Errorf("sentinel.Get(%q): %w", key, ErrMissing)
}
```

```go
// t25renopq.go
// Package opaque — 다음 판에서 감춘 타입의 이름과 필드를 통째로 바꿨다.
package opaque

import (
	"errors"
	"fmt"
)

type missingKey struct {
	key   string
	shard int
}

func (e *missingKey) Error() string  { return fmt.Sprintf("키 %s 없음(샤드 %d)", e.key, e.shard) }
func (e *missingKey) NotFound() bool { return true }

func Get(key string) (string, error) {
	return "", fmt.Errorf("opaque.Get: %w", &missingKey{key: key, shard: 7})
}

func IsNotFound(err error) bool {
	var b interface{ NotFound() bool }
	return errors.As(err, &b) && b.NotFound()
}
```

```go
// t25renmain.go
package main

import (
	"errors"
	"fmt"

	"ex/opaque"
	"ex/sentinel"
)

// 호출부는 이전 판에 맞춰 쓴 그대로다 — 한 글자도 안 바꿨다.
func main() {
	_, err := sentinel.Get("zz")
	fmt.Println(errors.Is(err, sentinel.ErrNotFound))

	_, err = opaque.Get("zz")
	fmt.Println(opaque.IsNotFound(err))
}
```

```text
===== 소스: t25renopq.go =====
// Package opaque — 다음 판에서 감춘 타입의 이름과 필드를 통째로 바꿨다.
package opaque

import (
	"errors"
	"fmt"
)

type missingKey struct {
	key   string
	shard int
}

func (e *missingKey) Error() string  { return fmt.Sprintf("키 %s 없음(샤드 %d)", e.key, e.shard) }
func (e *missingKey) NotFound() bool { return true }

func Get(key string) (string, error) {
	return "", fmt.Errorf("opaque.Get: %w", &missingKey{key: key, shard: 7})
}

func IsNotFound(err error) bool {
	var b interface{ NotFound() bool }
	return errors.As(err, &b) && b.NotFound()
}
===== 소스: t25rensent.go =====
// Package sentinel — 다음 판에서 센티넬 이름을 바꿨다.
package sentinel

import (
	"errors"
	"fmt"
)

// ErrMissing 은 예전 이름이 ErrNotFound 였다.
var ErrMissing = errors.New("키 없음")

func Get(key string) (string, error) {
	return "", fmt.Errorf("sentinel.Get(%q): %w", key, ErrMissing)
}
===== 소스: t25renmain.go =====
package main

import (
	"errors"
	"fmt"

	"ex/opaque"
	"ex/sentinel"
)

// 호출부는 이전 판에 맞춰 쓴 그대로다 — 한 글자도 안 바꿨다.
func main() {
	_, err := sentinel.Get("zz")
	fmt.Println(errors.Is(err, sentinel.ErrNotFound))

	_, err = opaque.Get("zz")
	fmt.Println(opaque.IsNotFound(err))
}
===== 명령: go build -trimpath -gcflags=-e -o prog . =====
# ex
./t25renmain.go:14:38: undefined: sentinel.ErrNotFound
(exit 1)
```

그림 해설 (한 단계씩):

- ★★★ **진단이 한 줄뿐이다** — `undefined: sentinel.ErrNotFound`. **센티넬 이름을 바꾼 대가**가 **호출부의 컴파일 에러**로 나왔다.
  ★ `-gcflags=-e` 로 에러 상한을 풀었는데도 한 줄이다 — **불투명판 쪽에서는 아무것도 안 깨졌다.**
- ★★★ **불투명판은 타입 이름(`notFound` → `missingKey`)과 필드(`shard` 추가)를 다 바꿨는데 조용하다.**
  호출부가 그 타입을 **적은 적이 없으니** 깨질 것이 없다. **약속은 `IsNotFound` 하나였다.**
- ★★ **그렇다면 호출부가 감춘 타입을 적으려 하면?** 던졌다.

```go
// t25hide.go
package main

import (
	"errors"
	"fmt"

	"ex/opaque"
)

// 호출부가 감춘 타입을 직접 꺼내려 한다.
func main() {
	_, err := opaque.Get("zz")
	var nf *opaque.notFound
	fmt.Println(errors.As(err, &nf))
}
```

```text
===== 소스: t25opaque.go =====
// Package opaque 는 오류 타입을 감추고 「동작」만 공개한다.
package opaque

import (
	"errors"
	"fmt"
)

// notFound 는 공개하지 않는다 — 호출자는 이 이름을 적을 수 없다.
type notFound struct{ key string }

func (e *notFound) Error() string  { return "키 " + e.key + " 없음" }
func (e *notFound) NotFound() bool { return true }

// Get 은 키를 찾는다. 못 찾으면 감춘 타입을 감싸 돌려준다.
func Get(key string) (string, error) {
	if key == "a" {
		return "1", nil
	}
	return "", fmt.Errorf("opaque.Get: %w", &notFound{key: key})
}

// IsNotFound 는 「없음」인지 묻는 공개 도우미다. 사슬을 따라간다.
func IsNotFound(err error) bool {
	var b interface{ NotFound() bool }
	return errors.As(err, &b) && b.NotFound()
}
===== 소스: t25hide.go =====
package main

import (
	"errors"
	"fmt"

	"ex/opaque"
)

// 호출부가 감춘 타입을 직접 꺼내려 한다.
func main() {
	_, err := opaque.Get("zz")
	var nf *opaque.notFound
	fmt.Println(errors.As(err, &nf))
}
===== 명령: go build -trimpath -gcflags=-e -o prog . =====
# ex
./t25hide.go:13:17: undefined: opaque.notFound
(exit 1)
```

- ★★★ **`undefined: opaque.notFound`** — 「내보내지 않았다」가 아니라 「**없다**」로 답한다.
  ★ 패키지 밖에서 소문자 이름은 **존재하지 않는 것과 같다**. 명세의 「대문자만 내보낸다」가 오류 설계에서 이렇게 쓰인다.
  (C# 갈래에서 `internal` 멤버가 「보이는데 막힘」이 아니라 「이름째 없음」으로 나온 것과 같은 모양이다.)
- ★ **정리** — **센티넬 이름·공개 타입·그 필드는 전부 공개 API** 다. **바꾸면 호출부가 컴파일 에러로 깨진다.**
  감춘 것만 **마음대로 고칠 수 있다.**

비용 — 없다.

### (4) ★★ 조용히 깨지는 두 자리 — 문자열 비교와 옛 도우미

**언제 쓰나** — 남의 패키지 오류를 가를 때. **컴파일은 되는데 실행에서 틀린다** — (3)절의 창이 못 보는 자리다.

```text
===== 소스: t25b.go =====
package main

import (
	"errors"
	"fmt"
	"io"
	"io/fs"
	"os"
	"strings"
	"syscall"
)

func main() {
	fmt.Println("-- 1. 오류 문자열 비교 — 문맥이 한 겹 붙으면 끝이다 --")
	base := errors.New("키 없음")
	wrapped := fmt.Errorf("load(%q): %w", "a", base)
	fmt.Printf("  base.Error() == \"키 없음\"              : %v\n", base.Error() == "키 없음")
	fmt.Printf("  wrapped.Error() == \"키 없음\"           : %v\n", wrapped.Error() == "키 없음")
	fmt.Printf("  strings.Contains(wrapped.Error(), …)   : %v   <- 붙잡는 척은 된다\n",
		strings.Contains(wrapped.Error(), "키 없음"))
	fmt.Printf("  errors.Is(wrapped, base)               : %v\n", errors.Is(wrapped, base))
	other := errors.New("키 없음") // 문구가 같은 다른 오류
	fmt.Printf("  문구가 같은 다른 오류 — 문자열 같음 : %v · errors.Is : %v\n",
		other.Error() == base.Error(), errors.Is(other, base))

	fmt.Println("-- 2. 옛 도우미 os.IsNotExist 는 %w 사슬을 안 탄다 --")
	_, err := os.Open("없는파일.txt")
	w := fmt.Errorf("설정 읽기: %w", err)
	fmt.Printf("  os.IsNotExist(err)           : %v\n", os.IsNotExist(err))
	fmt.Printf("  os.IsNotExist(w)             : %v   <- 한 겹 감싸면 거짓\n", os.IsNotExist(w))
	fmt.Printf("  errors.Is(w, fs.ErrNotExist) : %v\n", errors.Is(w, fs.ErrNotExist))

	fmt.Println("-- 3. 타입이 센티넬 질문에 답한다 — syscall.Errno 의 Is --")
	var pe *fs.PathError
	errors.As(w, &pe)
	errno, _ := pe.Err.(syscall.Errno)
	fmt.Printf("  pe.Err 의 %%T = %T · 번호 = %d · 문구 = %v\n", pe.Err, uintptr(errno), errno)
	fmt.Printf("  error(errno) == fs.ErrNotExist : %v\n", error(errno) == fs.ErrNotExist)
	fmt.Printf("  errno.Is(fs.ErrNotExist)       : %v\n", errno.Is(fs.ErrNotExist))

	fmt.Println("-- 4. io.EOF 는 감싸면 안 되는 센티넬이다 --")
	_, err = strings.NewReader("").Read(make([]byte, 1))
	fmt.Printf("  Read 가 준 err == io.EOF   : %v\n", err == io.EOF)
	bad := fmt.Errorf("read: %w", io.EOF)
	fmt.Printf("  감싼 EOF == io.EOF         : %v\n", bad == io.EOF)
	fmt.Printf("  errors.Is(감싼 EOF, io.EOF) : %v\n", errors.Is(bad, io.EOF))
}
===== 명령: go build -trimpath -o prog . && ./prog =====
-- 1. 오류 문자열 비교 — 문맥이 한 겹 붙으면 끝이다 --
  base.Error() == "키 없음"              : true
  wrapped.Error() == "키 없음"           : false
  strings.Contains(wrapped.Error(), …)   : true   <- 붙잡는 척은 된다
  errors.Is(wrapped, base)               : true
  문구가 같은 다른 오류 — 문자열 같음 : true · errors.Is : false
-- 2. 옛 도우미 os.IsNotExist 는 %w 사슬을 안 탄다 --
  os.IsNotExist(err)           : true
  os.IsNotExist(w)             : false   <- 한 겹 감싸면 거짓
  errors.Is(w, fs.ErrNotExist) : true
-- 3. 타입이 센티넬 질문에 답한다 — syscall.Errno 의 Is --
  pe.Err 의 %T = syscall.Errno · 번호 = 2 · 문구 = no such file or directory
  error(errno) == fs.ErrNotExist : false
  errno.Is(fs.ErrNotExist)       : true
-- 4. io.EOF 는 감싸면 안 되는 센티넬이다 --
  Read 가 준 err == io.EOF   : true
  감싼 EOF == io.EOF         : false
  errors.Is(감싼 EOF, io.EOF) : true
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **오류 문자열 비교는 문맥이 한 겹 붙으면 끝이다** — `wrapped.Error() == "키 없음"` 이 **`false`**.
  ★ `strings.Contains` 로 바꾸면 **붙잡는 척은 된다**(`true`). 그러나 **문구가 같은 전혀 다른 오류**도 붙잡는다 —
  마지막 줄에서 **문자열은 같은데 `errors.Is` 는 `false`** 다. **문자열은 신원이 아니다.**
- ★★ **문구는 계약이 아니다** — (2)절의 표면에 문구가 찍혀 있었지만, 그것을 바꿔도 **컴파일러는 아무 말도 안 한다.**
  문자열로 비교하던 호출부만 **실행에서 조용히 틀린다.**
- ★★★ **옛 도우미 `os.IsNotExist` 는 `%w` 사슬을 안 탄다** — 감싸지 않은 `err` 에는 `true`, **한 겹 감싼 `w` 에는 `false`**.
  `errors.Is(w, fs.ErrNotExist)` 는 `true` 다. 문서가 스스로 그 한계를 적는다.

```text
===== 명령: go doc os.IsNotExist =====
package os // import "os"

func IsNotExist(err error) bool
    IsNotExist returns a boolean indicating whether its argument is known
    to report that a file or directory does not exist. It is satisfied by
    ErrNotExist as well as some syscall errors.

    This function predates errors.Is. It only supports errors returned by the os
    package. New code should use errors.Is(err, fs.ErrNotExist).
(exit 0)
```

  ★★ 「**This function predates errors.Is.** … **New code should use errors.Is(err, fs.ErrNotExist).**」
  **불투명판의 도우미 함수를 쓰면 이 사고를 스스로 만들 수 있다** — 그래서 (1)절의 `opaque.IsNotFound` 는 속에서 `errors.As` 로 **사슬을 따라간다.**
- ★★★ **타입이 센티넬 질문에 답한다** — `pe.Err` 는 **`syscall.Errno`(번호 2)** 이고 **`== fs.ErrNotExist` 는 `false`** 인데
  **`errno.Is(fs.ErrNotExist)` 는 `true`** 다. [24번 주제](../24-error-wrapping-and-errors-is-as-join/) (2)절이 찾은 그 구조를 소스로 본다.

```text
===== 명령: sed -n "120,132p" "$(go env GOROOT)/src/syscall/syscall_unix.go" =====
func (e Errno) Is(target error) bool {
	switch target {
	case oserror.ErrPermission:
		return e == EACCES || e == EPERM
	case oserror.ErrExist:
		return e == EEXIST || e == ENOTEMPTY
	case oserror.ErrNotExist:
		return e == ENOENT
	case errorspkg.ErrUnsupported:
		return e == ENOSYS || e == ENOTSUP || e == EOPNOTSUPP
	}
	return false
}
(exit 0)
```

  ★★ **`switch target`** — 번호 타입 하나가 **네 센티넬 질문**(`ErrPermission`·`ErrExist`·`ErrNotExist`·`ErrUnsupported`)에 답한다.
  ★ **센티넬과 타입은 양자택일이 아니다** — 표준은 **OS 번호라는 타입**을 두고 그 위에서 **이식 가능한 센티넬**로 묻게 한다.
- ★★★ **`io.EOF` 는 「감싸면 안 되는 센티넬」이다** — `Read` 가 준 것은 `== io.EOF` 가 `true`,
  감싼 것은 `false` 다(`errors.Is` 로는 `true`). 문서가 그 이유를 적는다((5)절).

비용 — 없다.

### (5) ★★★ 세 설계가 표준 라이브러리 안에 다 있다 — `go doc` 으로

**언제 쓰나** — 「내 패키지를 어느 쪽으로 할까」를 정할 때. 표준이 **이미 세 가지를 다 쓰고 있다.**

**① 센티넬 — `io.EOF` · `os.ErrNotExist`**

```text
===== 명령: go doc io.EOF && go doc os.ErrNotExist =====
package io // import "io"

var EOF = errors.New("EOF")
    EOF is the error returned by Read when no more input is available. (Read
    must return EOF itself, not an error wrapping EOF, because callers will test
    for EOF using ==.) Functions should return EOF only to signal a graceful
    end of input. If the EOF occurs unexpectedly in a structured data stream,
    the appropriate error is either ErrUnexpectedEOF or some other error giving
    more detail.

package os // import "os"

var (
	// ErrInvalid indicates an invalid argument.
	// Methods on File will return this error when the receiver is nil.
	ErrInvalid = fs.ErrInvalid // "invalid argument"

	ErrPermission = fs.ErrPermission // "permission denied"
	ErrExist      = fs.ErrExist      // "file already exists"
	ErrNotExist   = fs.ErrNotExist   // "file does not exist"
	ErrClosed     = fs.ErrClosed     // "file already closed"

	ErrNoDeadline       = errNoDeadline()       // "file type does not support deadline"
	ErrDeadlineExceeded = errDeadlineExceeded() // "i/o timeout"
)
    Portable analogs of some common system call errors.

    Errors returned from this package may be tested against these errors with
    errors.Is.
(exit 0)
```

- ★★★ **`io.EOF` 의 문서가 센티넬 설계의 계약을 한 문장으로 적는다** —
  「**Read must return EOF itself, not an error wrapping EOF, because callers will test for EOF using ==.**」
  ★ 이것은 [24번 주제](../24-error-wrapping-and-errors-is-as-join/)의 「감쌀 때는 `%w`」와 **정면으로 반대 방향**이다.
  **`io.EOF` 는 「실패」가 아니라 「정상 종료 신호」라서** 호출부가 루프마다 `==` 로 싸게 묻는 것이 계약이다.
  ★ 그래서 규칙이 둘로 갈린다 — **신호형 센티넬은 감싸지 않고 그대로**, **실패형 센티넬은 문맥을 붙여 `%w` 로**.
- ★★ **`os.ErrNotExist = fs.ErrNotExist`** — `os` 의 센티넬은 **`io/fs` 의 것을 다시 내보낸 별칭**이다.
  「**Errors returned from this package may be tested against these errors with errors.Is.**」 — 묻는 법이 **`errors.Is`** 로 적혀 있다.

**② 커스텀 타입 — `*fs.PathError`**

```text
===== 명령: go doc io/fs.PathError =====
package fs // import "io/fs"

type PathError struct {
	Op   string
	Path string
	Err  error
}
    PathError records an error and the operation and file path that caused it.

func (e *PathError) Error() string
func (e *PathError) Timeout() bool
func (e *PathError) Unwrap() error
(exit 0)
```

- ★★★ **필드 셋(`Op`·`Path`·`Err`)이 공개**이고 `Unwrap()` 이 있다 — 문맥을 싣고 **속 원인을 감싸는** 타입이다.
  ★ 그리고 **`Timeout() bool`** 도 달려 있다 — 같은 타입이 **③의 동작 인터페이스에도 답한다.**

**③ 불투명 + 동작 — `net.Error`**

```text
===== 명령: go doc net.Error =====
package net // import "net"

type Error interface {
	error
	Timeout() bool // Is the error a timeout?

	// Deprecated: Temporary errors are not well-defined.
	// Most "temporary" errors are timeouts, and the few exceptions are surprising.
	// Do not use this method.
	Temporary() bool
}
    An Error represents a network error.
(exit 0)
```

- ★★★ **`net.Error` 는 타입이 아니라 인터페이스**다 — 호출부는 구체 타입을 몰라도 「**타임아웃이냐**」를 묻는다.
- ★★★ **그런데 `Temporary()` 는 `Deprecated` 다** — 「**Temporary errors are not well-defined. … Do not use this method.**」
  ★ **브리핑이 예로 든 `interface{ Temporary() bool }` 를 표준이 스스로 버렸다.** 동작 인터페이스도 **뜻이 흐린 동작을 공개하면 계약이 흐려진다**는 실례다.
  남은 것은 `Timeout()` 하나다.

**한 오류에 세 설계가 다 들어 있다 — 실제로 던져 본다**

```text
===== 소스: t25c.go =====
package main

import (
	"errors"
	"fmt"
	"net"
	"os"
	"time"
)

func main() {
	c1, c2 := net.Pipe() // 메모리 안의 연결 — 네트워크를 안 쓴다
	defer c1.Close()
	defer c2.Close()
	c1.SetReadDeadline(time.Now().Add(-time.Second)) // 이미 지난 기한
	_, err := c1.Read(make([]byte, 1))
	fmt.Printf("err = %v\n%%T  = %T\n", err, err)

	fmt.Println("-- 한 오류에 세 설계가 다 들어 있다 --")
	var oe *net.OpError
	fmt.Printf("  타입   errors.As(err, &oe)                : %v  (Op=%q Net=%q)\n",
		errors.As(err, &oe), oe.Op, oe.Net)
	var ne net.Error
	ok := errors.As(err, &ne)
	fmt.Printf("  동작   errors.As(err, &ne) · ne.Timeout() : %v · %v\n", ok, ne.Timeout())
	var to interface{ Timeout() bool }
	fmt.Printf("  동작   익명 interface{ Timeout() bool }   : %v\n", errors.As(err, &to) && to.Timeout())
	fmt.Printf("  센티넬 errors.Is(err, os.ErrDeadlineExceeded) : %v\n",
		errors.Is(err, os.ErrDeadlineExceeded))
}
===== 명령: go build -trimpath -o prog . && ./prog =====
err = read pipe: i/o timeout
%T  = *net.OpError
-- 한 오류에 세 설계가 다 들어 있다 --
  타입   errors.As(err, &oe)                : true  (Op="read" Net="pipe")
  동작   errors.As(err, &ne) · ne.Timeout() : true · true
  동작   익명 interface{ Timeout() bool }   : true
  센티넬 errors.Is(err, os.ErrDeadlineExceeded) : true
(exit 0)
```

그림 해설 (한 단계씩):

- `net.Pipe` 는 **메모리 안의 연결**이라 네트워크를 안 쓴다. 이미 지난 기한으로 읽으니 **`read pipe: i/o timeout`** 이다.
- ★★★ **같은 오류 하나에 세 질문이 다 참이다** — **타입**(`*net.OpError`, `Op="read"` `Net="pipe"`) ·
  **동작**(`net.Error` 의 `Timeout()`, 익명 `interface{ Timeout() bool }`) · **센티넬**(`os.ErrDeadlineExceeded`).
- ★★ **표준의 답은 「셋 중 하나를 고른다」가 아니라 「질문마다 맞는 문을 연다」다.**
  값이 필요한 호출자에게는 타입을, 성질만 필요한 호출자에게는 동작을, 신원만 필요한 호출자에게는 센티넬을 준다.
  ★ **다만 그만큼 공개 표면이 넓어진다** — 표준은 그 표면을 **호환성 약속**으로 영원히 지킨다. 내 패키지도 그럴 각오인지가 판단 기준이다.

비용 — 없다.

### (6) ★★★ 호출자가 분기해야 하는 오류 / 로그로 충분한 오류 — 판단 기준

**언제 쓰나** — 새 패키지의 오류 표면을 정할 때. ★ **이 절의 표는 실행 결과가 아니라 판단 기준이다**(내 추론 — 위 실측을 근거로 삼았다).

```text
   ★★★ 공개할지를 가르는 질문 순서 (판단 — 내 추론)

   호출자가 이 오류를 보고 다르게 행동하나?
     ├─ 아니오 ─────────────────────────▶ 공개하지 않는다. fmt.Errorf("…: %w", err) 로 문맥만
     └─ 예
          정상 흐름의 신호인가? (스트림 끝)
            ├─ 예 ──────────────────────▶ 센티넬, 감싸지 않는다      (io.EOF)
            └─ 아니오
                 값을 읽어야 하나?
                   ├─ 예 ───────────────▶ 커스텀 타입 + errors.As    (*fs.PathError)
                   └─ 아니오
                        성질 하나로 가르나?
                          ├─ 예 ────────▶ 동작 인터페이스            (net.Error 의 Timeout)
                          └─ 아니오 ────▶ 센티넬 + errors.Is         (fs.ErrNotExist)
```

| 호출자가 그 오류를 보고 | 공개할 것 | 호출부 모양 | 근거 |
|---|---|---|---|
| **아무것도 안 하고 위로 올리거나 로그만 남긴다** | ★★★ **아무것도 공개하지 않는다** — `fmt.Errorf("…: %w", err)` 로 문맥만 | `if err != nil { return … }` | 공개하지 않으면 (3)절의 계약이 안 생긴다 |
| **「이것이냐」로만 가른다**(없음·닫힘·끝) | **센티넬** | `errors.Is(err, pkg.ErrX)` | (1)절 센티넬판 · (5)절 `os.ErrNotExist` |
| **정상 흐름의 신호**다(스트림 끝) | **센티넬 — 감싸지 않는다** | `err == io.EOF` | (5)절 `io.EOF` 의 문서 |
| **값을 읽어 행동을 바꾼다**(얼마 모자라나·어느 경로) | **커스텀 타입** | `errors.As(err, &e)` → `e.Field` | (1)절 타입판 · (5)절 `*fs.PathError` |
| **성질로 가른다**(재시도할까·타임아웃인가) | **동작 인터페이스**(또는 그것을 감싼 도우미) | `errors.As(err, &b) && b.Timeout()` | (5)절 `net.Error` |
| 고칠 자유를 남기고 싶다 | **불투명 + 도우미** — 도우미는 **반드시 사슬을 따라가게** | `pkg.IsX(err)` | (3)절 · (4)절 `os.IsNotExist` 의 교훈 |

판단 규칙 세 줄.

- ★★★ **「호출자가 이 오류를 보고 다르게 행동하나?」가 아니면 공개하지 마라.** 공개한 순간 (3)절의 컴파일 에러가 생긴다.
- ★★ **공개하면 신원(센티넬)·값(타입)·성질(동작) 중 호출자에게 필요한 가장 좁은 것을.** 넓게 주면 넓게 묶인다.
- ★★ **문구는 절대 계약으로 삼지 마라** — 공개 표면에 찍혀 있어도 컴파일러가 안 지켜 준다((4)절).

## 문법 — 형태와 규칙

### 형태

```go
// t25form.go
package main

import (
	"errors"
	"fmt"
)

// ① 센티넬 — 공개 변수. 호출부는 errors.Is 로 묻는다.
var ErrClosed = errors.New("닫혔다")

// ② 커스텀 타입 — 공개 타입과 필드. 호출부는 errors.As 로 꺼낸다.
type LimitError struct{ Max, Got int }

func (e *LimitError) Error() string { return fmt.Sprintf("한도 %d 초과(%d)", e.Max, e.Got) }

// ③ 불투명 + 동작 — 타입은 감추고 메서드만 약속한다.
type retryable struct{ msg string }

func (e *retryable) Error() string   { return e.msg }
func (e *retryable) Retryable() bool { return true }

func main() {
	errs := []error{
		fmt.Errorf("쓰기: %w", ErrClosed),
		fmt.Errorf("넣기: %w", &LimitError{Max: 10, Got: 12}),
		fmt.Errorf("호출: %w", &retryable{"잠깐 뒤 다시"}),
	}
	for _, err := range errs {
		var le *LimitError
		var r interface{ Retryable() bool }
		switch {
		case errors.Is(err, ErrClosed):
			fmt.Println("신원으로 분기 :", err)
		case errors.As(err, &le):
			fmt.Println("값으로 분기   :", err, "| 넘친 양", le.Got-le.Max)
		case errors.As(err, &r) && r.Retryable():
			fmt.Println("동작으로 분기 :", err)
		}
	}
}
```

```text
===== 명령: go build -trimpath -o prog . && ./prog =====
신원으로 분기 : 쓰기: 닫혔다
값으로 분기   : 넣기: 한도 10 초과(12) | 넘친 양 2
동작으로 분기 : 호출: 잠깐 뒤 다시
(exit 0)
```

규칙 불릿.

- **센티넬** — `var ErrX = errors.New("…")` 를 **패키지 수준 공개 변수**로. 묻는 법은 `errors.Is`.
- **커스텀 타입** — `Error() string` 을 단 **공개 타입**. 필드로 문맥을 싣고, 속 원인이 있으면 **`Unwrap() error`** 를 단다([24번 주제](../24-error-wrapping-and-errors-is-as-join/) (2)절).
- **불투명 + 동작** — 타입은 소문자로 감추고 **메서드 이름**을 약속한다. 도우미 함수를 둔다면 속에서 **`errors.As`**.
- **포인터 리시버로 `Error()` 를 달면** `errors.As` 의 대상은 **`*T` 의 포인터**다([24번 주제](../24-error-wrapping-and-errors-is-as-join/) (4)절).
- **센티넬 이름·공개 타입·그 필드는 공개 API** 다. 바꾸면 호출부가 컴파일 에러로 깨진다.

### 금지 사례 — 컴파일러가 거부하는 것 / 아무도 안 막는 것

| 쓴 꼴 | 누가 | 문장 |
|---|---|---|
| 이름을 바꾼 센티넬을 옛 이름으로 부름 | **컴파일러** | `undefined: sentinel.ErrNotFound` ((3)절) |
| 감춘 오류 타입을 패키지 밖에서 적음 | **컴파일러** | `undefined: opaque.notFound` ((3)절) |
| `err.Error() == "…"` 로 가르기 | ★★★ **아무도** — 문맥이 붙으면 조용히 `false` | — |
| `os.IsNotExist` 에 감싼 오류 | ★★ **아무도** — 조용히 `false` | 문서에 「New code should use errors.Is」 |
| 감싼 `io.EOF` 를 `==` 로 묻는 호출부 | ★★ **아무도** — 조용히 `false` | 문서에 「Read must return EOF itself」 |
| 뜻이 흐린 동작(`Temporary()`) 공개 | **표준이 스스로 `Deprecated`** | `go doc net.Error` |

## 어디서 틀리나

### 1. ★★★ 「센티넬로 공개했으니 `==` 로 물으면 되겠지」

- (1)절 실측 — 패키지가 `%w` 로 문맥을 붙이면 **`err == sentinel.ErrNotFound` 가 `false`** 다.
- 고치는 법 — **호출부는 `errors.Is`.** ★ 예외는 `io.EOF` 같은 **신호형 센티넬**뿐이고, 그때는 **돌려주는 쪽이 감싸지 않을 의무**를 진다.

### 2. ★★★ 「오류 문자열로 가르면 간단하다」

- (4)절 실측 — 한 겹 감싸면 `==` 가 `false`, `Contains` 로 바꾸면 **문구가 같은 다른 오류까지** 잡힌다.
- 고치는 법 — **문자열은 로그용이다.** 분기가 필요하면 **돌려주는 패키지에 센티넬이나 타입을 요청**한다.

### 3. ★★★ 「오류 타입을 공개해 두면 나중에 고치기 쉽겠지」

- (3)절 실측 — **공개한 이름을 바꾸면 호출부가 `undefined` 로 깨진다.** 필드도 같다.
- 고치는 법 — 호출자가 **값을 읽어야 할 때만** 타입을 공개한다. 아니면 **불투명 + 도우미**로 고칠 자유를 남긴다.

### 4. ★★ 「`os.IsNotExist` 로 물으면 되겠지」

- (4)절 실측 — **한 겹 감싼 오류에 `false`** 다. 문서가 「이 함수는 `errors.Is` 보다 먼저 나왔다」고 적는다.
- 고치는 법 — **`errors.Is(err, fs.ErrNotExist)`.** ★ 내가 도우미 함수를 만든다면 **속에서 `errors.As`/`Is` 로 사슬을 따라가게** 한다.

### 5. ★★ 「타입 단언 `err.(*MyErr)` 로 꺼내면 되겠지」

- (1)절 실측 — 문맥이 한 겹 붙으면 **`false`**. 인터페이스 단언도 같다.
- 고치는 법 — **`errors.As`**(1.26 이상이면 **`errors.AsType`** — [24번 주제](../24-error-wrapping-and-errors-is-as-join/) (8)절).

### 6. ★★ 「`io.EOF` 에도 문맥을 붙여 `%w` 로 감싸자」

- (4)·(5)절 실측 — 감싼 EOF 는 **`== io.EOF` 가 `false`** 이고, `io` 문서가 「**EOF 그 자체를 돌려줘라**」고 적는다.
- 고치는 법 — **신호형 센티넬은 그대로 돌려준다.** 문맥이 필요하면 그것은 신호가 아니라 **실패**(`io.ErrUnexpectedEOF` 등)다.

### 7. ★ 「성질이 비슷한 것은 `Temporary()` 로 묶자」

- (5)절 실측 — 표준이 `net.Error.Temporary` 를 **`Deprecated`** 로 돌렸다. 「대부분의 임시 오류는 타임아웃이고 나머지는 놀랍다」.
- 고치는 법 — **뜻이 한 문장으로 서는 동작**만 공개한다(`Timeout()` 처럼).

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| ★★★ **대문자 이름만 패키지 밖에 보이는 것** | **명세 보장** | (3)절 — 소문자 타입은 밖에서 `undefined` |
| 이름을 바꾸면 호출부가 **컴파일 에러**인 것 | **명세 보장의 결과** | (3)절 실측 |
| `errors.Is`/`As` 가 사슬을 도는 것 | **표준 라이브러리 계약(1.13)** | [24번 주제](../24-error-wrapping-and-errors-is-as-join/) |
| ★★ **`io.EOF` 를 감싸지 말라는 것** | **표준 라이브러리 계약** | `go doc io.EOF` 의 그 문장 |
| **`os.IsNotExist` 가 사슬을 안 타는 것** | **표준 라이브러리 계약** | `go doc os.IsNotExist` · (4)절 실측 |
| **`syscall.Errno` 가 `Is` 로 센티넬에 답하는 것** | **표준 라이브러리 계약** | (4)절 소스 · [24번 주제](../24-error-wrapping-and-errors-is-as-join/) (2)절 |
| **`net.Error.Temporary` 가 폐기된 것** | **표준 라이브러리 문서** | `go doc net.Error` |
| `*fmt.wrapError`·`*opaque.notFound` 라는 **`%T` 문구** | **구현·이 판** | 기대지 마라 |
| `syscall_unix.go` 의 **줄 번호** | **이 툴체인 판** | 판이 오르면 달라진다 |
| ★★★ 「**어느 설계가 좋은가**」 | **어느 층도 아니다 — 판단** | (6)절 표는 내 추론이다 |
| 세 설계의 **비용** | ★ **안 쟀다** | — |

★ 이 주제의 결론은 「**설계의 뼈대는 명세의 한 줄(대문자 공개)이고, 나머지는 표준이 보여 준 관례와 내 판단이다**」.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 호출자가 그 오류로 **행동을 안 바꾼다** | **공개하지 않고 `%w` 로 문맥만** | 계약이 안 생긴다 |
| 「없음」·「닫힘」처럼 **신원만** 필요 | **센티넬** + 호출부 `errors.Is` | 표면이 한 줄이다 |
| **스트림 끝** 같은 정상 신호 | **센티넬, 감싸지 않음** | `io.EOF` 의 계약 |
| **값**을 읽어야 한다 | **커스텀 타입** + `errors.As` | 필드가 곧 문맥이다 |
| **성질**로 가른다 | **동작 인터페이스** | 구체 타입을 몰라도 된다 |
| 내부를 계속 고칠 것이다 | **불투명 + 사슬을 따라가는 도우미** | (3)절 — 감춘 것은 자유롭다 |
| 남의 오류를 가른다 | **`Is`/`As`, 절대 문자열 아님** | (4)절 |

## 핵심 문장

- ★★★ **세 설계는 호출부가 쓰는 식으로 갈린다** — 센티넬은 **`errors.Is`**(신원), 커스텀 타입은 **`errors.As`**(값), 불투명판은 **동작 인터페이스나 도우미**(성질).
  ★ **문맥을 한 겹 붙이는 순간 `==` 와 타입 단언은 셋 다 틀린다.**
- ★★★ **공개한 만큼이 계약이다** — 센티넬 이름을 바꾸니 호출부가 **`undefined: sentinel.ErrNotFound`** 로 깨졌고,
  감춘 타입은 이름·필드를 다 바꿔도 **호출부가 조용했다.**
- ★★ **감춘 타입은 밖에서 「없다」** — `undefined: opaque.notFound`. 명세의 대문자 규칙이 오류 설계의 뼈대다.
- ★★★ **오류 문자열은 신원이 아니다** — 감싸면 `==` 가 깨지고, `Contains` 는 **문구가 같은 다른 오류**까지 잡는다.
- ★★ **`os.IsNotExist` 는 감싼 오류에 `false`** — 문서가 「New code should use errors.Is」라 적는다.
- ★★★ **`io.EOF` 는 감싸면 안 되는 센티넬이다** — 「callers will test for EOF using ==」. **신호형은 그대로, 실패형은 `%w`.**
- ★★★ **표준은 세 설계를 다 쓰고, 한 오류에 셋을 겹쳐 주기도 한다** — `read pipe: i/o timeout` 하나가
  `*net.OpError`(타입)·`Timeout()`(동작)·`os.ErrDeadlineExceeded`(센티넬) 셋에 다 참이다.
- ★★ **`net.Error.Temporary` 는 `Deprecated`** — 뜻이 흐린 동작을 공개하면 표준도 물린다.
- ★★ **판단 기준 한 줄** — 「호출자가 이 오류를 보고 다르게 행동하나?」가 아니면 **공개하지 않는다.**

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 25번)
- [`ops-patterns/failure-modes/`](../../../../../ops-patterns/failure-modes/) — ★★ **정본 경계.**
  **그쪽은 실패를 어떻게 분류하나(재시도·보상·사람 개입)까지**, 여기는 **그 분류를 Go 오류 값의 공개 표면으로 옮기는 법부터.**
  이 문서는 실패 분류 자체를 다시 쓰지 않는다
- [24번 주제](../24-error-wrapping-and-errors-is-as-join/)(래핑과 `Is`/`As`) — ★★★ **직접 선행.**
  **그쪽은 「어떻게 감싸고 어떻게 묻나」까지**, 여기는 **「무엇을 물을 수 있게 공개하나」부터.**
  `syscall.Errno` 의 `Is` · `errors.AsType` · 판 경계는 그쪽 실측을 인용했다
- [23번 주제](../23-error-interface-and-errors-as-values/)(오류는 값) — 한 겹 감싸면 `==` 가 깨진다 · 호출부 분기 수 격자
- [22번 주제](../22-type-assertion-any-and-comparable/)(타입 단언) — 단언이 맨 위 층만 보는 이유
- [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/)(`nil` 인터페이스) — 커스텀 타입을 돌려줄 때의 함정 · `go vet` 분석기 목록
- [20번 주제](../20-interface-declaration-and-implicit-implementation/)(암묵 구현) — 동작 인터페이스를 **선언 없이** 묻는 바탕
- 목록의 **40번 주제**(패키지 가시성) — 대문자 규칙과 `internal` 의 정본
- 목록의 **43번 주제**(`io.Reader`) — `io.EOF` 를 받는 읽기 루프의 정본
- [26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/)(`defer`) — `defer` 로 오류에 문맥을 붙이는 관용구
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **24번**
  ([`../../../rust/syntax/24-error-type-design/`](../../../rust/syntax/24-error-type-design/)) — ★ **`enum` 으로 공개하면 `match` 가 빠뜨린 분기를 센다.** Go 엔 그 검사가 없다
- [`../../../java/syntax/25-exceptions/`](../../../java/syntax/25-exceptions/) — 예외 **클래스 계층**이 곧 오류 표면인 쪽

## 용어 풀이

- **오류 표면** — 패키지가 오류에 관해 밖에 약속한 것 전부(센티넬 이름·타입·필드·메서드·도우미). `go doc -all` 이 찍는 목록.
- **센티넬 오류** — 공개 변수로 둔 정해진 오류 값. 신원으로 묻는다.
- **신호형 센티넬** — 실패가 아니라 정상 흐름을 알리는 센티넬(`io.EOF`). **감싸지 않는다.**
- **커스텀 오류 타입** — `Error()` 를 단 공개 타입. 필드로 문맥을 싣는다.
- **불투명 오류** — 타입을 감춘 오류. 호출부는 동작(메서드)이나 도우미로만 묻는다.
- **동작 인터페이스** — `interface{ Timeout() bool }` 처럼 **성질 하나**를 묻는 작은 인터페이스.
- **도우미 함수** — `os.IsNotExist`·`opaque.IsNotFound` 처럼 오류를 받아 참거짓을 주는 공개 함수. **사슬을 따라가야** 한다.

---

## 더 들어가면

- ★ **`errors.ErrUnsupported`**(1.21)가 `syscall.Errno.Is` 의 넷째 `case` 로 들어 있다 — 이 문서는 **그 센티넬로 묻는 실험은 안 던졌다.**
- ★ **Rust 의 `#[non_exhaustive]`** 처럼 「나중에 늘릴 수 있는 공개 `enum`」에 해당하는 장치가 Go 에는 없다 — 대신 **불투명판**이 그 자리를 맡는다는 것은 **내 추론**이다.
- ★ **오류 값에 오류 코드(정수)를 싣는 설계**(gRPC `status` 류)는 **안 던졌다** — 표준 라이브러리 밖이다.
- ★ **`errors.Is` 를 쓰는 테스트**(목록의 **49번 주제**)에서 센티넬 대 타입이 어떻게 갈리는지는 **안 던졌다.**
- ★★ 세 설계의 **비용**은 **안 쟀다.** 「센티넬이 가장 싸다」 같은 말을 이 문서는 하지 않는다.

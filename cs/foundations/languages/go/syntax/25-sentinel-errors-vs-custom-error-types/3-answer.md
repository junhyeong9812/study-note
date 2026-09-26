# go/syntax/25 — 센티넬 오류 대 커스텀 오류 타입 — 오류 표면 설계 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★ **근거로 읽을 칸** — 분기 식의 참거짓 · `go doc -all` 의 공개 표면 · 컴파일 에러의 `파일:줄:칸`과 문장 · 종료 코드.
> **근거로 읽지 않을 칸** — 없다. 이 문서의 블록은 재실행에서 전부 한 글자도 같았다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 호출부는 `Is`·`As`·동작으로 가르고, `==`·단언은 셋 다 틀린다

**출력**

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

**왜 그런가**

| 설계 | 호출부가 쓰는 식 | 답 | 틀리는 식 |
|---|---|---|---|
| 센티넬 | `errors.Is(err, sentinel.ErrNotFound)` | `true` | `err == sentinel.ErrNotFound` → **`false`** |
| 커스텀 타입 | `errors.As(err, &nf)` → `nf.Key`·`nf.Tried` | `true` · `"zz"` · `3` | `err.(*typed.NotFoundError)` → **`false`** |
| 불투명 | `errors.As(err, &b) && b.NotFound()` · `opaque.IsNotFound(err)` | `true` · `true` | `err.(interface{ NotFound() bool })` → **`false`** |

- ★★★ **세 판 모두 `Get` 이 `%w` 로 문맥을 붙였다** — 그래서 맨 위 층은 셋 다 **`*fmt.wrapError`** 이고,
  **맨 위만 보는 식(`==`·타입 단언·인터페이스 단언)은 전부 틀린다.**
- ★★ 불투명판의 `%T` 는 **`*fmt.wrapError`**, 한 겹 풀면 **`*opaque.notFound`** — 이름은 찍히지만 **호출부가 적을 수는 없다**(3번).
- ★ 타입판만 **값**(`Key="zz"`, `Tried=3`)을 준다. 센티넬판과 불투명판은 **예/아니오**만 준다.

### 2. 센티넬은 변수 한 줄, 타입은 필드까지, 불투명은 타입이 아예 없다

**출력**

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

**왜 그런가**

- ★★★ 센티넬판 — **`var ErrNotFound = errors.New("키 없음")`** 한 줄과 `func Get`. 그 **이름**이 계약이다.
- ★★★ 타입판 — **`type NotFoundError struct { Key string; Tried int }`** 와 `Error()` 까지. **필드가 전부 표면에 나온다.**
- ★★★ 불투명판 — **`func Get` 과 `func IsNotFound` 둘뿐**이다. `notFound` 는 소문자라 **목록에 없다.**
- ★ 이 목록이 **호출자가 기댈 수 있는 것의 전부**이고, 그만큼이 3번에서 컴파일러가 집행하는 계약이다.

### 3. 진단은 한 줄 — 센티넬 이름만 깨지고, 감춘 타입은 밖에서 「없다」

**출력**

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

**왜 그런가**

- ★★★ **`./t25renmain.go:14:38: undefined: sentinel.ErrNotFound`** — 진단이 **한 줄**이다.
  `-gcflags=-e` 로 상한을 풀었으니 **다른 에러가 숨은 것이 아니다.**
- ★★★ **불투명판은 타입 이름(`notFound` → `missingKey`)과 필드를 다 바꿨는데 조용하다** —
  호출부는 `opaque.IsNotFound` 만 불렀고, 그 **이름과 모양은 안 바뀌었다.**

**출력**

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

- ★★★ **`undefined: opaque.notFound`** — 「내보내지 않았다」가 아니라 「**없다**」다.
  패키지 밖에서 소문자 이름은 **존재하지 않는 것과 같다**(명세의 대문자 규칙).
- ★ 정리 — **공개한 이름·타입·필드는 바꾸면 호출부가 깨지고, 감춘 것은 자유롭다.**

### 4. 문자열·옛 도우미는 조용히 틀리고, `Errno` 는 `Is` 로 답한다

**출력**

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

**왜 그런가**

- ★★★ 1번 — `wrapped.Error() == "키 없음"` 이 **`false`**, `strings.Contains` 는 **`true`**(붙잡는 척),
  마지막 줄은 **문자열 같음 `true` · `errors.Is` `false`** — **문구가 같은 다른 오류**를 문자열은 못 가른다.
- ★★★ 2번 — **`os.IsNotExist(w)` 가 `false`**. 한 겹 감싸면 거짓이다. `errors.Is(w, fs.ErrNotExist)` 는 `true`.
  `go doc os.IsNotExist` 가 「**This function predates errors.Is.**」라고 스스로 적는다.
- ★★★ 3번 — `pe.Err` 는 **`syscall.Errno`**, 번호 **`2`**(`no such file or directory`).
  **`== fs.ErrNotExist` 는 `false`**, **`errno.Is(fs.ErrNotExist)` 는 `true`** —
  `syscall_unix.go` 의 `switch target` 이 `ErrNotExist` 에 `e == ENOENT` 로 답한다.
- ★★ 4번 — 감싼 EOF 는 **`== io.EOF` 가 `false`**, `errors.Is` 는 `true`. 그래서 `io` 는 **감싸지 말라**고 계약한다(6번).

### 5. 한 오류에 세 질문이 다 참이다

**출력**

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

**왜 그런가**

- 문구는 **`read pipe: i/o timeout`**, `%T` 는 **`*net.OpError`** 다.
- ★★★ **세 질문이 전부 참이다** — 타입(`*net.OpError`, `Op="read"` `Net="pipe"`) · 동작(`Timeout()`) · 센티넬(`os.ErrDeadlineExceeded`).
- ★ **`net.Pipe` 는 메모리 안의 연결**이라 네트워크가 필요 없고, **이미 지난 기한**으로 읽으니 즉시 타임아웃이 난다 — 그래서 결정적이다.

### 6. `io.EOF` 는 신호라서 `==` 로 묻는 것이 계약이다

- ★★★ `go doc io.EOF` — 「**Read must return EOF itself, not an error wrapping EOF, because callers will test for EOF using ==.**」
- ★★ 양립하는 법 — **센티넬을 두 종류로 가른다.**
  **신호형**(스트림 끝처럼 정상 흐름) → **감싸지 않고 그대로**, 호출부는 `==`.
  **실패형**(없음·권한) → **문맥을 붙여 `%w`**, 호출부는 `errors.Is`.
  ★ 「끝났는데 예상 밖」이면 그건 신호가 아니라 실패다 — 문서가 **`ErrUnexpectedEOF`** 를 따로 둔다.

### 7. 표준에 셋 다 있다

- ★★ **센티넬** — `io.EOF` · `os.ErrNotExist`. **커스텀 타입** — `*fs.PathError`(`Op`·`Path`·`Err` + `Unwrap`).
  **동작 인터페이스** — `net.Error` 의 `Timeout()`.
- ★ `os.ErrNotExist` 는 **`fs.ErrNotExist` 의 별칭**이다(`go doc os.ErrNotExist` 의 `ErrNotExist = fs.ErrNotExist`).
- ★★★ **`Temporary()` 가 폐기됐다** — 「**Temporary errors are not well-defined. Most "temporary" errors are timeouts, and the few exceptions are surprising.**」
- ★★ **`syscall.Errno` 는 타입인데 센티넬 질문에 답한다** — 번호라는 **타입**을 두고 `Is` 메서드로 **이식 가능한 센티넬**에 대답한다.
  양자택일이 아니라 **겹쳐 쓴 실례**다.

### 8. 행동이 안 바뀌면 공개하지 않는다

- ★★★ 행동을 안 바꾼다 → **아무것도 공개하지 않는다.** `fmt.Errorf("…: %w", err)` 로 문맥만 붙인다 — 계약이 안 생긴다.
- 얼마 모자라는지 읽어야 한다 → **커스텀 타입**(필드) + 호출부 `errors.As`.
- 재시도할지만 → **동작 인터페이스**(`Timeout()` 같은 것) — 구체 타입을 몰라도 된다.
- ★★ 내부를 계속 고친다 → **불투명 + 도우미**. 조심할 것은 **도우미가 사슬을 따라가게**(속에서 `errors.As`/`Is`) — 안 그러면 `os.IsNotExist` 꼴이 된다.
- ★ 이 표 전체는 **판단 기준(내 추론)** 이다. 실측은 그 근거일 뿐이다.

### 9. 컴파일 에러만 명세에서 나온다

- ★★★ 「이름을 바꾸면 컴파일 에러」 — **명세**(대문자만 밖에 보인다 · 없는 이름은 `undefined`)의 결과다.
- 「`io.EOF` 를 감싸지 마라」 — **표준 라이브러리 계약**(`io` 문서).
- 「센티넬보다 타입이 좋다」 — **어느 층도 아니다. 판단**이다.
- ★★ 오류 **문구**를 바꾸는 것은 **아무도 안 막는다** — 문자열로 비교하던 호출부만 실행에서 조용히 틀린다.

### 10. Rust 는 완전성을 세고 Go 는 동작으로 넓게 잡는다

- ★★ Rust 는 오류를 **`enum`** 으로 공개하면 호출부의 `match` 가 **빠뜨린 분기를 컴파일러가 센다.**
  Go 의 `error` 는 **인터페이스**라 「가능한 오류의 전체 목록」이 타입에 없다 — **원리상 셀 수 없다.**
  (Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **24번**.)
- ★ 자바는 **예외 계층**의 상위 타입으로 넓게 잡는다. Go 는 상속이 없어 **동작 인터페이스**(`Timeout()`)로 넓게 묻는다.
  ([23번 주제](../23-error-interface-and-errors-as-values/)가 호출부 분기 수를 스크립트로 셌다.)


---

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 로 **★고칠 것 0** |
| 판 확인 | `go version` | 1 | `go1.27.1 linux/amd64` |
| ★★★ 세 설계 (`t25a`) | 네 파일 모듈을 `go build && ./prog` | 1 | `==`·단언 `false` · `Is`/`As`/도우미 `true` |
| ★★ 공개 표면 (`t25surface`) | `go doc -all ./sentinel` 등 셋 | 1 | 불투명판에 오류 타입 없음 |
| ★★★ 다음 판 (`t25ren`) | `go build -gcflags=-e` | 1 | 진단 **1줄** · exit 1 |
| ★★ 감춘 타입 (`t25hide`) | 〃 | 1 | `undefined: opaque.notFound` · exit 1 |
| ★★ 조용한 자리 (`t25b`) | `go build && ./prog` | 1 | 문자열·`os.IsNotExist` 가 감싸면 `false` |
| ★★ 한 오류 세 질문 (`t25c`) | 〃 | 1 | 셋 다 `true` |
| 표준 계약 | `go doc io.EOF` · `os.ErrNotExist` · `io/fs.PathError` · `net.Error` · `os.IsNotExist` | 1 | 위 인용문 |
| `Errno.Is` 소스 | `sed -n` | 1 | `syscall_unix.go:120` |

**구현·환경에 달린 항목**

| 항목 | 무엇에 달렸나 |
|---|---|
| `*fmt.wrapError`·`*opaque.notFound` 라는 **`%T` 문구** | **구현** — 기대지 마라 |
| `syscall_unix.go` 의 줄 번호 | **이 툴체인 판** |
| 컴파일 에러 문장(`undefined: …`) | **툴체인 판(go1.27.1)** |
| 「어느 설계가 좋은가」 | ★ **판단** — 어느 층의 보장도 아니다 |
| 세 설계의 비용 | ★ **안 쟀다** |
| `errors.ErrUnsupported` 로 묻기 | ★ **안 던졌다** |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다.

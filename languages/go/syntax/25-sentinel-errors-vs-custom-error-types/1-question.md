# go/syntax/25 — 센티넬 오류 대 커스텀 오류 타입 — 오류 표면 설계 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ **모든 문제에서 「호출부가 쓰는 식이 무엇인가」를 먼저 적어라** — `==` · `errors.Is` · `errors.As` · 단언 · 도우미.
> ★★ **「이것이 공개 API 인가」를 매번 물어라** — 이 주제의 답은 대개 「**공개한 만큼이 계약**」이다.
> 소스는 전부 `go build -trimpath` 로 던졌다. 모듈 이름은 `ex` 다. 여러 패키지짜리는 `go.mod` 가 있는 디렉토리째 던졌다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 같은 「없음」을 세 설계로 쓰면 (예측)

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

- 센티넬판에서 `err == sentinel.ErrNotFound` 와 `errors.Is(…)` 는 각각 무엇인가?
- 타입판에서 `errors.As` 와 `err.(*typed.NotFoundError)` 는 각각 무엇인가 — `nf` 의 필드에는 무엇이 들어 있나?
- 불투명판에서 `%T` 는 무엇이고, 한 겹 풀면 무엇이 찍히나?
- 불투명판의 인터페이스 단언과 `errors.As`·`IsNotFound` 는 각각 무엇인가?
- 세 판에 공통으로 **틀리는 식**은 무엇인가?

### 2. `go doc -all` 로 세 패키지의 표면을 찍으면 (예측)

- 센티넬판의 표면에 **무엇이 몇 줄** 나오나?
- 타입판의 표면에는 무엇까지 나오나 — 필드도 나오나?
- 불투명판의 표면에 **오류 타입이 나오나**?

### 3. 다음 판에서 이름을 바꾸면 (예측)

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

- `go build -gcflags=-e` 가 **몇 줄**의 진단을 내나 — 어느 파일 어느 이름인가?
- 불투명판은 타입 이름과 필드를 다 바꿨는데 진단이 나오나 — 왜인가?


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

- 감춘 타입을 호출부에서 적으면 진단 문장은 「내보내지 않았다」인가 다른 것인가?

### 4. 조용히 깨지는 자리 넷 (예측)

```go
// t25b.go
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
```

- 1번 덩어리 — `wrapped.Error() == "키 없음"` · `strings.Contains` · 마지막 줄(문구가 같은 다른 오류)의 답은?
- 2번 덩어리 — `os.IsNotExist(w)` 는 무엇인가?
- 3번 덩어리 — `pe.Err` 의 `%T` 와 번호는 무엇이고, `== fs.ErrNotExist` 와 `errno.Is(…)` 는 각각 무엇인가?
- 4번 덩어리 — 감싼 EOF 의 `==` 와 `errors.Is` 는?

### 5. 한 오류에 세 질문을 던지면 (예측)

```go
// t25c.go
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
```

- `err` 의 문구와 `%T` 는 무엇인가?
- 타입·동작·센티넬 세 질문 중 **몇 개가 참**인가?
- 네트워크 없이도 이 실험이 되는 이유는?

### 6. `io.EOF` 는 왜 감싸면 안 되나 (왜)

- `go doc io.EOF` 가 적은 이유는 무엇인가?
- 그것이 「감쌀 때는 `%w`」라는 [24번 주제](../24-error-wrapping-and-errors-is-as-join/)의 규칙과 어떻게 양립하나 — 센티넬을 두 종류로 가르면?

### 7. 표준 라이브러리 안의 세 설계 (연결)

- 센티넬·커스텀 타입·동작 인터페이스를 표준에서 **하나씩** 대라.
- `os.ErrNotExist` 는 어느 패키지의 센티넬을 다시 내보낸 것인가?
- `net.Error` 의 두 메서드 중 **폐기된 것**은 무엇이고 이유는 무엇인가?
- `syscall.Errno` 는 센티넬과 타입 중 어느 쪽인가 — 왜 둘 다라고 말할 수 있나?

### 8. 무엇을 공개하나 (경계)

- 호출자가 그 오류를 보고 **행동을 안 바꾼다** — 무엇을 공개하나?
- 호출자가 **얼마 모자라는지**를 읽어야 한다 — 무엇을 공개하나?
- 호출자가 **재시도할지**만 알면 된다 — 무엇을 공개하나?
- 내부 구조를 계속 고칠 것이다 — 무엇을 공개하고 무엇을 조심하나?

### 9. 무엇이 명세이고 무엇이 판단인가 (왜)

- 「이름을 바꾸면 호출부가 컴파일 에러」는 어느 층에서 나오나?
- 「`io.EOF` 를 감싸지 마라」는 어느 층인가?
- 「센티넬보다 타입이 좋다」는 어느 층인가?
- 오류 **문구**를 바꾸는 것은 누가 막아 주나?

### 10. 다른 언어와 나란히 (연결)

- Rust 가 오류를 `enum` 으로 공개하면 호출부에 무엇이 생기고, Go 는 왜 그것이 없나?
- 자바의 예외 계층과 견주면 Go 는 「넓게 잡기」를 무엇으로 하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

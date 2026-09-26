# go/syntax/23 — `error` 인터페이스와 값으로서의 오류 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 Go 출력은 **`go version go1.27.1 linux/amd64`**,
> Rust 출력은 **`rustc 1.92.0 (ded5c06cf 2025-12-08)`**,
> 자바 출력은 **`javac 21.0.5`(Temurin, `openjdk 21.0.5 2024-10-15 LTS`)** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★ **근거로 읽을 칸** — 네 줄의 출력, `count.sh` 가 센 수, `==` 의 답, `%T`,
> 컴파일 에러의 **문장과 `파일:줄:칸`**, 종료 코드.
> **근거로 읽지 않을 칸** — **없다.** 이 주제의 블록은 재실행에서 한 글자도 같았다.
> ★★ **이 문서는 시간도 할당도 재지 않았다.** 센 것은 **줄 수와 오류 경로 수**뿐이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 메서드가 하나이고, 무시해도 컴파일된다

**출력**

```text
===== 명령: go doc builtin.error =====
package builtin // import "builtin"

type error interface {
	Error() string
}
    The error built-in interface type is the conventional interface for
    representing an error condition, with the nil value representing no error.
(exit 0)
```

```text
===== 소스: t23a.go =====
package main

import (
	"errors"
	"fmt"
	"io"
	"reflect"
)

// error 는 표준 라이브러리 타입이 아니라 미리 선언된 인터페이스다.
//
//	type error interface { Error() string }
type MyErr struct{ Code int }

func (e MyErr) Error() string { return fmt.Sprintf("code=%d", e.Code) }

func main() {
	et := reflect.TypeOf((*error)(nil)).Elem()
	fmt.Println("-- error 인터페이스를 reflect 로 뜯어본다 --")
	fmt.Println("  이름        :", et.Name())
	fmt.Println("  Kind        :", et.Kind())
	fmt.Println("  메서드 수   :", et.NumMethod())
	m := et.Method(0)
	fmt.Printf("  메서드 하나 : %s %v\n", m.Name, m.Type)

	fmt.Println("-- 그래서 만족하는 방법도 하나뿐이다 --")
	fmt.Println("  MyErr 이 error 를 만족하나 :", reflect.TypeOf(MyErr{}).Implements(et))
	fmt.Println("  int 이 error 를 만족하나   :", reflect.TypeOf(0).Implements(et))

	fmt.Println("-- 오류는 값이다 : 변수에 담고 슬라이스에 넣고 비교한다 --")
	list := []error{
		errors.New("첫째"),
		fmt.Errorf("둘째 %d", 2),
		MyErr{Code: 7},
		io.EOF,
		nil,
	}
	for i, e := range list {
		fmt.Printf("  [%d] %%T=%-24T %%v=%v\n", i, e, e)
	}

	fmt.Println("-- 값이므로 함수가 그냥 돌려준다 (던지는 문법이 없다) --")
	v, err := half(9)
	fmt.Printf("  half(9)  -> v=%d err=%v\n", v, err)
	v, err = half(7)
	fmt.Printf("  half(7)  -> v=%d err=%v\n", v, err)

	fmt.Println("-- 그래서 무시할 수도 있다 : 컴파일러가 안 막는다 --")
	v2, _ := half(7)
	fmt.Println("  _ 로 버린 판 -> v2 =", v2)
	half(7) // 반환값을 아예 안 받아도 된다
	fmt.Println("  반환값을 아예 안 받아도 컴파일된다")
}

func half(n int) (int, error) {
	if n%2 != 0 {
		return 0, MyErr{Code: n}
	}
	return n / 2, nil
}
===== 명령: go build -trimpath -o prog . && ./prog =====
-- error 인터페이스를 reflect 로 뜯어본다 --
  이름        : error
  Kind        : interface
  메서드 수   : 1
  메서드 하나 : Error func() string
-- 그래서 만족하는 방법도 하나뿐이다 --
  MyErr 이 error 를 만족하나 : true
  int 이 error 를 만족하나   : false
-- 오류는 값이다 : 변수에 담고 슬라이스에 넣고 비교한다 --
  [0] %T=*errors.errorString      %v=첫째
  [1] %T=*errors.errorString      %v=둘째 2
  [2] %T=main.MyErr               %v=code=7
  [3] %T=*errors.errorString      %v=EOF
  [4] %T=<nil>                    %v=<nil>
-- 값이므로 함수가 그냥 돌려준다 (던지는 문법이 없다) --
  half(9)  -> v=0 err=code=9
  half(7)  -> v=0 err=code=7
-- 그래서 무시할 수도 있다 : 컴파일러가 안 막는다 --
  _ 로 버린 판 -> v2 = 0
  반환값을 아예 안 받아도 컴파일된다
(exit 0)
```

**왜 그런가**

- ★★★ **`NumMethod` 가 1** 이고 그 하나가 **`Error func() string`** 이다.
  Kind 는 `interface`, 이름은 `error` 다.
- `MyErr{}` 은 만족하고(`true`) `int` 은 아니다(`false`).
  ★ **`Error() string` 만 달면 되는 것**이 [20번 주제](../20-interface-declaration-and-implicit-implementation/)의 암묵 구현이다.
- ★ `go doc` 이 「**with the nil value representing no error**」라 적는다 —
  「**`nil` 이 오류 없음**」이라는 관례가 그 한 줄에 있다.
- `[]error` 다섯의 `%T` 는 `*errors.errorString` **세 개**(`errors.New` 둘과 `io.EOF`),
  `main.MyErr`, `<nil>` 이다.
  ★ **`fmt.Errorf` 도 `%w` 가 없으면 `*errors.errorString`** 이다((2)번).
- ★★★ **마지막 두 줄이 이 절의 결론이다** — `_` 로 버려도, **반환값을 아예 안 받아도**
  컴파일되고 돌아간다. ★ **자바의 검사 예외와 정확히 반대**다((5)번).

### 2. 포인터 비교라 같은 글자라도 다른 값이다

**출력**

```text
===== 소스: t23b.go =====
package main

import (
	"errors"
	"fmt"
	"io"
	"io/fs"
	"os"
)

var ErrClosed = errors.New("스트림이 닫혔다") // 센티넬 — 패키지가 공개하는 값

func read(closed bool) (int, error) {
	if closed {
		return 0, ErrClosed
	}
	return 1, nil
}

func main() {
	fmt.Println("-- 같은 메시지의 errors.New 두 개는 같지 않다 --")
	a := errors.New("같은 글자")
	b := errors.New("같은 글자")
	fmt.Printf("  a == b            : %v\n", a == b)
	fmt.Printf("  a.Error() == b.Error() : %v\n", a.Error() == b.Error())
	fmt.Printf("  errors.Is(a, b)   : %v\n", errors.Is(a, b))
	fmt.Printf("  %%T                : %T\n", a)
	fmt.Println("  이유 — errors.New 는 매번 새 *errorString 을 만들고 비교는 포인터 비교다")

	fmt.Println("-- 같은 값을 두 번 쓰면 당연히 같다 --")
	fmt.Printf("  ErrClosed == ErrClosed : %v\n", ErrClosed == ErrClosed)
	_, err := read(true)
	fmt.Printf("  read(true) 가 돌려준 것 == ErrClosed : %v\n", err == ErrClosed)
	fmt.Printf("  errors.Is(그것, ErrClosed)           : %v\n", errors.Is(err, ErrClosed))

	fmt.Println("-- 표준 라이브러리의 센티넬 --")
	fmt.Printf("  io.EOF            : %%T=%T %%v=%v\n", io.EOF, io.EOF)
	fmt.Printf("  fs.ErrNotExist    : %%T=%T %%v=%v\n", fs.ErrNotExist, fs.ErrNotExist)
	fmt.Printf("  os.ErrNotExist == fs.ErrNotExist : %v  (같은 값을 다시 내보낸 것)\n",
		os.ErrNotExist == fs.ErrNotExist)

	fmt.Println("-- fmt.Errorf 는 %w 를 안 쓰면 그냥 새 errorString 이다 --")
	e1 := fmt.Errorf("포장 %v", ErrClosed)
	e2 := fmt.Errorf("포장 %w", ErrClosed)
	fmt.Printf("  %%v 판 : %%T=%-24T errors.Is(e, ErrClosed)=%v\n", e1, errors.Is(e1, ErrClosed))
	fmt.Printf("  %%w 판 : %%T=%-24T errors.Is(e, ErrClosed)=%v\n", e2, errors.Is(e2, ErrClosed))
	fmt.Println("  두 메시지는 한 글자도 같다 :", e1.Error() == e2.Error())
	fmt.Printf("  메시지 : %q\n", e1.Error())
	fmt.Println("  (그래서 %v 로 감싼 사고는 로그만 봐서는 안 보인다 — 24번 주제)")

	fmt.Println("-- 센티넬을 == 로 견주는 것이 언제 깨지나 --")
	wrapped := fmt.Errorf("계층 하나 더: %w", ErrClosed)
	fmt.Printf("  wrapped == ErrClosed        : %v  <- 감싸는 순간 깨진다\n", wrapped == ErrClosed)
	fmt.Printf("  errors.Is(wrapped, ErrClosed): %v  <- 그래서 Is 를 쓴다 (24번 주제)\n",
		errors.Is(wrapped, ErrClosed))
}
===== 명령: go build -trimpath -o prog . && ./prog =====
-- 같은 메시지의 errors.New 두 개는 같지 않다 --
  a == b            : false
  a.Error() == b.Error() : true
  errors.Is(a, b)   : false
  %T                : *errors.errorString
  이유 — errors.New 는 매번 새 *errorString 을 만들고 비교는 포인터 비교다
-- 같은 값을 두 번 쓰면 당연히 같다 --
  ErrClosed == ErrClosed : true
  read(true) 가 돌려준 것 == ErrClosed : true
  errors.Is(그것, ErrClosed)           : true
-- 표준 라이브러리의 센티넬 --
  io.EOF            : %T=*errors.errorString %v=EOF
  fs.ErrNotExist    : %T=*errors.errorString %v=file does not exist
  os.ErrNotExist == fs.ErrNotExist : true  (같은 값을 다시 내보낸 것)
-- fmt.Errorf 는 %w 를 안 쓰면 그냥 새 errorString 이다 --
  %v 판 : %T=*errors.errorString      errors.Is(e, ErrClosed)=false
  %w 판 : %T=*fmt.wrapError           errors.Is(e, ErrClosed)=true
  두 메시지는 한 글자도 같다 : true
  메시지 : "포장 스트림이 닫혔다"
  (그래서 %v 로 감싼 사고는 로그만 봐서는 안 보인다 — 24번 주제)
-- 센티넬을 == 로 견주는 것이 언제 깨지나 --
  wrapped == ErrClosed        : false  <- 감싸는 순간 깨진다
  errors.Is(wrapped, ErrClosed): true  <- 그래서 Is 를 쓴다 (24번 주제)
(exit 0)
```

**왜 그런가**

- ★★★ **`a == b` 가 `false`** 인데 **`a.Error() == b.Error()` 는 `true`** 다.
  `%T` 가 **`*errors.errorString`** — **포인터**라 새로 만들면 늘 다르다.
  `errors.Is(a, b)` 도 `false` 다(사슬이 없으니 `==` 와 같다).
- ★★ **그것이 센티넬이 성립하는 이유**다 — `io.EOF` 를 **한 번만 만들어 공개**하니
  그 값과 견주는 것이 「같은 오류냐」가 된다.
  `os.ErrNotExist == fs.ErrNotExist` 가 **`true`** 인 것은 `os` 가 `fs` 의 값을 **다시 내보냈기** 때문이다.
- ★★★ **`%v` 판과 `%w` 판의 메시지가 한 글자도 같다**(`true`, `"포장 스트림이 닫혔다"`).
  그런데 `errors.Is` 는 **`false` 대 `true`** 로 갈리고 `%T` 도
  `*errors.errorString` 대 **`*fmt.wrapError`** 로 갈린다.
  ★★ **로그만 봐서는 안 보이는 사고**다 — 정본은 [24번 주제](../24-error-wrapping-and-errors-is-as-join/)다.
- ★★ **마지막 두 줄이 `==` 의 한계**다 — 한 겹만 감싸도 `wrapped == ErrClosed` 가 **`false`** 다.
  `errors.Is` 는 **`true`** 다. 그래서 센티넬을 `==` 로 견주는 코드는 **감싸는 순간 깨진다.**

### 3. 값을 들고 다니고, 비교 규칙은 그 타입이 정한다

**출력**

```text
===== 소스: t23c.go =====
package main

import (
	"errors"
	"fmt"
	"strconv"
)

// 커스텀 오류 타입 — 값을 들고 다닌다
type ParseErr struct {
	Line int
	Raw  string
}

func (e *ParseErr) Error() string {
	return fmt.Sprintf("%d행을 못 읽었다: %q", e.Line, e.Raw)
}

// 값 리시버로 단 판
type RangeErr struct{ N int }

func (e RangeErr) Error() string { return fmt.Sprintf("범위 밖: %d", e.N) }

func parse(line int, raw string) (int, error) {
	n, err := strconv.Atoi(raw)
	if err != nil {
		return 0, &ParseErr{Line: line, Raw: raw}
	}
	if n < 0 {
		return 0, RangeErr{N: n}
	}
	return n, nil
}

func main() {
	fmt.Println("-- 오류가 값을 들고 다니므로 호출자가 그 값을 쓴다 --")
	for i, raw := range []string{"12", "x9", "-3"} {
		n, err := parse(i+1, raw)
		switch {
		case err == nil:
			fmt.Printf("  %-4q -> %d\n", raw, n)
		default:
			var pe *ParseErr
			var re RangeErr
			switch {
			case errors.As(err, &pe):
				fmt.Printf("  %-4q -> ParseErr  행=%d 원문=%q\n", raw, pe.Line, pe.Raw)
			case errors.As(err, &re):
				fmt.Printf("  %-4q -> RangeErr   값=%d\n", raw, re.N)
			}
		}
	}

	fmt.Println("-- 포인터 리시버 대 값 리시버 (19번 주제) --")
	var e1 error = &ParseErr{Line: 1, Raw: "z"} // 포인터로만 담긴다
	var e2 error = RangeErr{N: -1}              // 값으로 담긴다
	var e3 error = &RangeErr{N: -1}             // 포인터로도 담긴다
	fmt.Printf("  &ParseErr{} : %%T=%-16T %%v=%v\n", e1, e1)
	fmt.Printf("  RangeErr{}  : %%T=%-16T %%v=%v\n", e2, e2)
	fmt.Printf("  &RangeErr{} : %%T=%-16T %%v=%v\n", e3, e3)

	fmt.Println("-- 커스텀 타입끼리의 == 는 그 타입의 비교 가능성을 탄다 (22번 주제) --")
	fmt.Printf("  RangeErr{1} == RangeErr{1}   : %v\n", error(RangeErr{1}) == error(RangeErr{1}))
	fmt.Printf("  &ParseErr{} == &ParseErr{}   : %v  <- 포인터가 다르다\n",
		error(&ParseErr{}) == error(&ParseErr{}))
}
===== 명령: go build -trimpath -o prog . && ./prog =====
-- 오류가 값을 들고 다니므로 호출자가 그 값을 쓴다 --
  "12" -> 12
  "x9" -> ParseErr  행=2 원문="x9"
  "-3" -> RangeErr   값=-3
-- 포인터 리시버 대 값 리시버 (19번 주제) --
  &ParseErr{} : %T=*main.ParseErr   %v=1행을 못 읽었다: "z"
  RangeErr{}  : %T=main.RangeErr    %v=범위 밖: -1
  &RangeErr{} : %T=*main.RangeErr   %v=범위 밖: -1
-- 커스텀 타입끼리의 == 는 그 타입의 비교 가능성을 탄다 (22번 주제) --
  RangeErr{1} == RangeErr{1}   : true
  &ParseErr{} == &ParseErr{}   : false  <- 포인터가 다르다
(exit 0)
```

**왜 그런가**

- `"12"` 는 성공, `"x9"` 는 `ParseErr`(행 2 · 원문 `"x9"`), `"-3"` 은 `RangeErr`(값 -3)다.
  ★★ **호출자가 오류에서 값을 읽었다** — 센티넬로는 못 하는 일이다.
- `%T` 는 `*main.ParseErr`·`main.RangeErr`·`*main.RangeErr` 이다.
  ★ `ParseErr` 은 `Error()` 가 **포인터 리시버**라 **값으로는 못 담긴다**((4)번).
  `RangeErr` 은 값 리시버라 **둘 다** 담긴다.
- ★★★ **`RangeErr{1} == RangeErr{1}` 이 `true`, `&ParseErr{} == &ParseErr{}` 이 `false`** 다.
  앞엣것은 **구조체 값 비교**(필드가 같으면 같다)이고 뒤엣것은 **포인터 비교**다.
  ★ **오류 타입을 값으로 만들지 포인터로 만들지가 `==` 의 뜻을 바꾼다.**
  비교 규칙 자체는 [22번 주제](../22-type-assertion-any-and-comparable/) (5)절과
  [17번 주제](../17-struct-literals-comparability-field-tags-and-sorting/)가 정본이다.

### 4. 세 건 — 변수·인자·슬라이스 리터럴

**출력**

```text
===== 소스: t23d.go =====
package main

import "fmt"

// Error() 를 포인터 리시버로 달았다.
type PtrErr struct{ M string }

func (e *PtrErr) Error() string { return "PtrErr:" + e.M }

// Error() 를 값 리시버로 달았다.
type ValErr struct{ M string }

func (e ValErr) Error() string { return "ValErr:" + e.M }

func main() {
	// 되는 것 네 가지
	var a error = &PtrErr{M: "a"}
	var b error = ValErr{M: "b"}
	var c error = &ValErr{M: "c"}
	fmt.Println(a, b, c)

	// 안 되는 것 — 19번 주제의 메서드 집합 규칙이 그대로 적용된다
	var d error = PtrErr{M: "d"}
	fmt.Println(d)

	// 함수 인자로 넘길 때도 같다
	show(PtrErr{M: "e"})

	// 슬라이스 원소로 넣을 때도 같다
	_ = []error{PtrErr{M: "f"}}
}

func show(e error) { fmt.Println(e) }
===== 명령: go build -trimpath -gcflags=-e -o prog . =====
# ex
./t23d.go:23:16: cannot use PtrErr{…} (value of struct type PtrErr) as error value in variable declaration: PtrErr does not implement error (method Error has pointer receiver)
./t23d.go:27:7: cannot use PtrErr{…} (value of struct type PtrErr) as error value in argument to show: PtrErr does not implement error (method Error has pointer receiver)
./t23d.go:30:14: cannot use PtrErr{…} (value of struct type PtrErr) as error value in array or slice literal: PtrErr does not implement error (method Error has pointer receiver)
(exit 1)
```

**왜 그런가**

- ★★★ **에러 세 건**이고 전부 같은 이유다 —
  **`PtrErr does not implement error (method Error has pointer receiver)`**, 종료 코드 1.
- 세 자리는 **변수 선언**(`var d error = PtrErr{…}`) ·
  **함수 인자**(`show(PtrErr{…})`) · **슬라이스 리터럴**(`[]error{PtrErr{…}}`)이다.
  ★★ **인터페이스가 요구되는 모든 자리**에서 같은 이유로 막힌다 — 자리마다 문장 뒷부분만 다르다.
- **되는 네 가지**는 `&PtrErr{}` · `ValErr{}` · `&ValErr{}` 이고, 그 셋이 첫 줄에 찍혔다
  (값 리시버 메서드는 `T` 와 `*T` 둘 다의 집합에 들고, 포인터 리시버 메서드는 `*T` 에만 든다 —
  [19번 주제](../19-method-sets-value-vs-pointer-receiver/)).
- ★★ **그래서 오류 타입의 관례가 갈린다** — 포인터 리시버로 달면 **`&MyErr{}` 로만** 쓰게 된다.

### 5. 세 언어의 호출부 — 네 줄은 같고 문구가 다르다

**출력**

```text
===== 소스: t23go.go =====
package main

import (
	"fmt"
	"os"
	"strconv"
	"strings"
)

// 설정 파일에서 포트 번호 하나를 읽는다.
func loadPort(path string) (int, error) {
	b, err := os.ReadFile(path)
	if err != nil {
		return 0, fmt.Errorf("설정 읽기: %w", err)
	}
	n, err := strconv.Atoi(strings.TrimSpace(string(b)))
	if err != nil {
		return 0, fmt.Errorf("port 파싱: %w", err)
	}
	if n < 1 || n > 65535 {
		return 0, fmt.Errorf("port 범위 밖: %d", n)
	}
	return n, nil
}

func main() {
	must(os.WriteFile("ok.conf", []byte("8080\n"), 0o644))
	must(os.WriteFile("bad.conf", []byte("x9\n"), 0o644))
	must(os.WriteFile("big.conf", []byte("99999\n"), 0o644))

	for _, p := range []string{"ok.conf", "bad.conf", "big.conf", "none.conf"} {
		n, err := loadPort(p)
		if err != nil {
			fmt.Printf("  %-10s 실패 : %v\n", p, err)
			continue
		}
		fmt.Printf("  %-10s 성공 : %d\n", p, n)
	}
}

func must(err error) {
	if err != nil {
		panic(err)
	}
}
===== 명령: go build -trimpath -o prog . && ./prog =====
  ok.conf    성공 : 8080
  bad.conf   실패 : port 파싱: strconv.Atoi: parsing "x9": invalid syntax
  big.conf   실패 : port 범위 밖: 99999
  none.conf  실패 : 설정 읽기: open none.conf: no such file or directory
(exit 0)
```

**왜 그런가**

- 네 줄이 **성공 8080 · `port 파싱: …` · `port 범위 밖: 99999` · `설정 읽기: …`** 다.
- 파일이 없을 때 — **`설정 읽기: open none.conf: no such file or directory`**.
  ★ 앞의 `설정 읽기: ` 는 **`fmt.Errorf` 가 손으로 붙인 것**이고,
  뒤는 `os.ReadFile` 이 준 `*fs.PathError` 의 메시지다.
- ★★ **오류 경로는 세 군데**다 — `if err != nil` 두 번과 범위 검사 한 번.
  ★ 셋 다 **같은 모양**(`return 0, fmt.Errorf(…)`)이라 그 반복이 이 언어의 모양이 된다.


**출력**

```text
===== 소스: t23rs.rs =====
use std::error::Error;
use std::fs;

// 같은 일을 하는 Rust 판 — 문맥을 붙이지 않은 ? 만의 꼴
fn load_port(path: &str) -> Result<u32, Box<dyn Error>> {
    let s = fs::read_to_string(path)?;
    let n: u32 = s.trim().parse()?;
    if !(1..=65535).contains(&n) {
        return Err(format!("port 범위 밖: {n}").into());
    }
    Ok(n)
}

fn main() {
    fs::write("ok.conf", "8080\n").unwrap();
    fs::write("bad.conf", "x9\n").unwrap();
    fs::write("big.conf", "99999\n").unwrap();

    for p in ["ok.conf", "bad.conf", "big.conf", "none.conf"] {
        match load_port(p) {
            Ok(n) => println!("  {p:<10} 성공 : {n}"),
            Err(e) => println!("  {p:<10} 실패 : {e}"),
        }
    }
}
===== 명령: rustc --edition 2021 -C debuginfo=0 t23rs.rs -o prog && ./prog =====
  ok.conf    성공 : 8080
  bad.conf   실패 : invalid digit found in string
  big.conf   실패 : port 범위 밖: 99999
  none.conf  실패 : No such file or directory (os error 2)
(exit 0)
```

```text
===== 소스: t23rs2.rs =====
use std::error::Error;
use std::fs;

// Go 와 같은 문맥 문구까지 붙인 Rust 판 — map_err 이 그 자리를 맡는다
fn load_port(path: &str) -> Result<u32, Box<dyn Error>> {
    let s = fs::read_to_string(path).map_err(|e| format!("설정 읽기: {e}"))?;
    let n: u32 = s.trim().parse().map_err(|e| format!("port 파싱: {e}"))?;
    if !(1..=65535).contains(&n) {
        return Err(format!("port 범위 밖: {n}").into());
    }
    Ok(n)
}

fn main() {
    fs::write("ok.conf", "8080\n").unwrap();
    fs::write("bad.conf", "x9\n").unwrap();
    fs::write("big.conf", "99999\n").unwrap();

    for p in ["ok.conf", "bad.conf", "big.conf", "none.conf"] {
        match load_port(p) {
            Ok(n) => println!("  {p:<10} 성공 : {n}"),
            Err(e) => println!("  {p:<10} 실패 : {e}"),
        }
    }
}
===== 명령: rustc --edition 2021 -C debuginfo=0 t23rs2.rs -o prog && ./prog =====
  ok.conf    성공 : 8080
  bad.conf   실패 : port 파싱: invalid digit found in string
  big.conf   실패 : port 범위 밖: 99999
  none.conf  실패 : 설정 읽기: No such file or directory (os error 2)
(exit 0)
```

**왜 그런가**

- ★★ **성공과 범위 밖 줄은 Go 와 같고, 나머지 둘이 다르다.**
  `?` 만 쓴 판은 **`invalid digit found in string`**·**`No such file or directory (os error 2)`** 로
  「**어느 단계에서 났는지**」가 **메시지에서 사라진다.**
- ★★★ **`?` 는 조기 반환과 `From` 변환을 하지 문맥은 안 붙인다.**
  붙이려면 `map_err` 을 쓴다 — 둘째 블록이 그 판이고, 그러면 **Go 와 같은 문구**가 된다.
  ★ **줄 수는 안 는다**((6)번에서 둘 다 8줄) — `map_err` 이 `?` 앞에 붙는 **한 식**이기 때문이다.
- ★★ **그러니 「문맥은 공짜로 따라온다」는 두 언어 다 틀리다.**
  Go 의 `fmt.Errorf("문맥: %w", err)` 와 Rust 의 `.map_err(…)?` 가 **같은 자리**다.
- Rust 22편이 결론낸 대로 `?` 는 **개념적으로** `match` + `return Err(From::from(e))` 로 펼쳐진다
  (Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **22번**).
  ★ 그 편이 내부 트레이트 경로는 **결론으로 삼지 않겠다**고 적었으므로 여기서도 그 선을 지킨다.


**출력**

```text
===== 소스: Ex23.java =====
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

// 같은 일을 하는 자바 판 — 실패는 던지고 호출부가 잡는다
public class Ex23 {
    static int loadPort(String path) throws IOException {
        String s = Files.readString(Path.of(path));
        int n = Integer.parseInt(s.trim());
        if (n < 1 || n > 65535) {
            throw new IllegalArgumentException("port 범위 밖: " + n);
        }
        return n;
    }

    public static void main(String[] args) throws IOException {
        Files.writeString(Path.of("ok.conf"), "8080\n");
        Files.writeString(Path.of("bad.conf"), "x9\n");
        Files.writeString(Path.of("big.conf"), "99999\n");

        for (String p : new String[] {"ok.conf", "bad.conf", "big.conf", "none.conf"}) {
            try {
                System.out.printf("  %-10s 성공 : %d%n", p, loadPort(p));
            } catch (IOException | IllegalArgumentException e) {
                System.out.printf("  %-10s 실패 : %s: %s%n",
                        p, e.getClass().getSimpleName(), e.getMessage());
            }
        }
    }
}
===== 명령: javac -d . Ex23.java && java Ex23 =====
  ok.conf    성공 : 8080
  bad.conf   실패 : NumberFormatException: For input string: "x9"
  big.conf   실패 : IllegalArgumentException: port 범위 밖: 99999
  none.conf  실패 : NoSuchFileException: none.conf
(exit 0)
```

**왜 그런가**

- 네 줄이 **성공 8080 · `NumberFormatException` · `IllegalArgumentException` · `NoSuchFileException`** 이다.
  ★ **단계 문구가 없다** — 예외가 **스택 트레이스를 들고 다니므로** 그 자리를 메시지에 안 적는다.
- ★★ **`throws IOException` 만 있고 `NumberFormatException` 이 없는 이유** —
  그것은 **검사 예외가 아니다**(`RuntimeException` 의 하위다).
  ★ 검사 예외만 「잡거나 선언하라」가 강제된다
  ([`../../../java/syntax/25-exceptions/`](../../../java/syntax/25-exceptions/)).
- **`catch` 는 한 번** 적혔다. ★★ **세 가지 실패를 한 블록이 받는다** —
  Go 에서 `if err != nil` 을 세 번 적은 자리가 여기서는 **한 자리로 모인다.**
  ★ 그 대신 **어느 실패인지 알려면 예외 종류를 다시 갈라야** 한다
  (여기서는 `e.getClass().getSimpleName()` 을 찍었다).


**출력**

```text
===== 소스: Ex23bad.java =====
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

// 같은 일을 하는 자바 판 — 실패는 던지고 호출부가 잡는다
public class Ex23bad {
    static int loadPort(String path) throws IOException {
        String s = Files.readString(Path.of(path));
        int n = Integer.parseInt(s.trim());
        if (n < 1 || n > 65535) {
            throw new IllegalArgumentException("port 범위 밖: " + n);
        }
        return n;
    }

    public static void main(String[] args) throws IOException {
        Files.writeString(Path.of("ok.conf"), "8080\n");
        Files.writeString(Path.of("bad.conf"), "x9\n");
        Files.writeString(Path.of("big.conf"), "99999\n");

        for (String p : new String[] {"ok.conf", "bad.conf", "big.conf", "none.conf"}) {
            try {
                System.out.printf("  %-10s 성공 : %d%n", p, loadPort(p));
            } catch (IOException | NumberFormatException | IllegalArgumentException e) {
                System.out.printf("  %-10s 실패 : %s: %s%n",
                        p, e.getClass().getSimpleName(), e.getMessage());
            }
        }
    }
}
===== 명령: javac -d . Ex23bad.java =====
Ex23bad.java:24: error: Alternatives in a multi-catch statement cannot be related by subclassing
            } catch (IOException | NumberFormatException | IllegalArgumentException e) {
                                                           ^
  Alternative NumberFormatException is a subclass of alternative IllegalArgumentException
1 error
(exit 1)
```

**왜 그런가**

- ★★★ **컴파일이 안 된다.** `NumberFormatException` 이 `IllegalArgumentException` 의 **하위**라
  둘을 한 `catch` 에 적을 수 없다. 종료 코드 1이다.
- ★ 두 번째 줄이 이유를 그대로 말한다 —
  `Alternative NumberFormatException is a subclass of alternative IllegalArgumentException`.
- ★★★ **Go 에는 이 문제가 원리상 없다.** 오류는 **값**이고 값들 사이에 **상속 관계가 없다.**
  `errors.Is` 로 여럿을 물어도 서로 간섭하지 않는다.
  ★ 이 한 건이 「던지기」와 「돌려주기」의 차이를 **컴파일 에러로** 보여 준다 —
  던지기 쪽은 **예외 계층**이라는 구조를 하나 더 들고 다녀야 한다.

### 6. 함수 본문 Go 14 · Rust 8 · 자바 8

**출력**

```text
===== 명령: sh count.sh =====
edition                  fn-lines fn-err-paths   call-lines
Go                             14            3            8
Rust (bare ?)                   8            3            6
Rust (with context)             8            3            6
Java                            8            2            8

how many times the error plumbing is spelled out in the whole file
Go   err                       12
Go   if err != nil              4
Rust ?                          2
Rust unwrap()                   3
Java throws                     2
Java throw                      1
Java catch                      1
(exit 0)
```

**왜 그런가**

- ★★★ **함수 본문** — Go **14줄**, Rust **8줄**(문맥 판도 8줄), 자바 **8줄**.
- ★★ **오류 경로 수** — Go **3** · Rust **3** · 자바 **2**.
  ★★★ **거의 같다.** 그래서 정확한 말은 「**분기가 많다**」가 아니라 「**같은 분기를 적는 글자가 많다**」다.
  Go 의 `if err != nil { return 0, fmt.Errorf(…) }` **세 줄**이 Rust 에서는 `?` **한 글자**다.
- **호출부** — Go **8줄** · Rust **6줄** · 자바 **8줄**. ★ 차이가 좁혀진다 —
  실패를 다루는 자리가 **한 군데로 모이기 때문**이다.
- ★★★ **둘째 표가 더 말이 된다.**

| | 몇 번 적혔나 |
|---|---|
| **Go** | `err` **12번** · `if err != nil` **4번** |
| **Rust** | `?` **2번** · `unwrap()` 3번 |
| **Java** | `throws` 2번 · `throw` 1번 · `catch` 1번 |

  ★★ **그 12번은 「장황하다」이기도 하고 「실패가 지나가는 자리가 12번 눈에 보인다」이기도 하다.**
  ★★★ **어느 쪽이 낫다는 말을 이 문서는 하지 않는다.** 센 것은 글자 수뿐이고
  **속도도 할당도 재지 않았다.**

### 7. 값이라서 얻은 것 셋, 잃은 것 하나

- ★★★ **얻은 것 셋** —
  ① **담긴다**(`[]error{…}` · 구조체 필드 · 채널로 보내기) —
  ② **견줄 수 있다**(`==`·`errors.Is`) 그래서 **센티넬**이라는 설계가 생긴다 —
  ③ **값을 들고 다닌다**(커스텀 타입의 필드를 호출자가 읽는다).
- ★★★ **잃은 것 하나** — **강제가 없다.** (1)번 실측대로 `_` 로 버려도,
  아예 안 받아도 컴파일된다. ★ 그것을 메우는 것은 **도구**이지 언어가 아니다.
- ★★ **Rust 의 `?`** 는 **줄이는 것**이 `if err != nil` 세 줄이고,
  **안 보이게 하는 것**이 「여기서 실패가 위로 샌다」는 사실이다 —
  한 글자라 눈에 덜 걸린다. ★ Rust 22편이 그 대비를 같은 말로 적어 뒀다.
- ★★ **자바의 검사 예외**는 Go 에서 **아무도 안 하는 일**을 컴파일러에게 시킨다 —
  「이 실패를 처리했나」. ★ 그 대신 (5)번처럼 **예외 계층이라는 구조**가 따라온다.

### 8. 명세는 몇 줄뿐이고 나머지는 관례다

| 사실 | 층 |
|---|---|
| `error` 가 미리 선언된 **메서드 하나짜리 인터페이스** | ★★★ **명세 보장** |
| `Error() string` 만 달면 만족하는 것 | **명세 보장**(암묵 구현) |
| 포인터 리시버면 값이 만족 못 하는 것 | **명세 보장**(메서드 집합) |
| 오류를 안 받아도 컴파일되는 것 | **명세 보장**(반환값 버리기에 제약이 없다) |
| **오류가 마지막 반환값인 것** | ★ **관례** — 명세에 그런 조항이 없다 |
| **`nil` 이 「오류 없음」인 것** | ★ **관례 + `go doc` 의 서술** |
| `errors.New` 가 매번 새 값인 것 | **표준 라이브러리 계약** |
| **`*errors.errorString` 이라는 이름** | ★★ **구현 내부** — 기대지 마라 |

- ★★★ **`*errors.errorString` 에 기대면 안 된다.** 그것은 `errors` 패키지 안의 비공개 타입이고
  문서가 약속한 것이 아니다. ★ 실제로 `%w` 를 쓰면 **`*fmt.wrapError`** 로 바뀐다((2)번).
  **타입 이름이 아니라 `errors.Is`/`As` 로 물어야** 한다([24번 주제](../24-error-wrapping-and-errors-is-as-join/)).

### 9. 분기하면 값, 보고만 하면 문구

- **호출자가 분기만 하면 된다** → **센티넬**. `errors.Is` 로 물을 수 있게 값으로 공개한다.
- **호출자가 값을 써야 한다** → **커스텀 타입**. `errors.As` 로 꺼내 필드를 읽는다.
- **오류 타입을 값으로 만들지 포인터로 만들지** → `==` 의 뜻이 바뀐다((3)번).
  ★ 포인터면 **신원 비교**, 값이면 **필드 비교**다.
  ★★ 그리고 `Error()` 의 리시버가 **어느 쪽으로 담기는지**를 정한다((4)번).
- ★ **이 질문의 정본은 [목록의 25번 주제](../25-sentinel-errors-vs-custom-error-types/)**(센티넬 대 커스텀 오류 타입)다.
  여기는 **두 가지가 있다는 것**까지다.

### 10. 다른 주제와 잇기

- `(T, error)` 관례가 어느 문법에서 나오는지 —
  [12번 주제](../12-functions-multiple-returns-named-results-and-variadics/)(다중 반환).
- 「성공이면 `nil` 을 명시로」 —
  [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/)가 정본. 구체 타입 변수를 그대로 돌려주면 함정이다.
- 포인터 리시버가 무엇을 막는지 —
  [19번 주제](../19-method-sets-value-vs-pointer-receiver/)가 정본. (4)번이 그 직접 응용이다.
- `%w`·`errors.Is`/`As` — [24번 주제](../24-error-wrapping-and-errors-is-as-join/). ★ **이 주제의 직접 후속**이다.
- `panic`/`recover` — [목록의 **27번 주제**](../27-panic-recover-and-where-to-use-them/). ★ **이 문서는 `panic` 을 안 던졌다.**
- 덤 — **암묵 구현**은 [20번 주제](../20-interface-declaration-and-implicit-implementation/),
  **단언으로 오류를 되꺼내는 것**은 [22번 주제](../22-type-assertion-any-and-comparable/),
  **오류 표면 설계**는 [목록의 **25번 주제**](../25-sentinel-errors-vs-custom-error-types/), **`fmt.Errorf` 의 동사**는 목록의 **42번 주제**다.


---

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행 1회** | `normalize-shaky.py` 로 **★고칠 것 0** |
| 판 확인 | `go version` · `rustc --version` · `javac --version` | 3 | `go1.27.1` · `rustc 1.92.0` · `javac 21.0.5` |
| `error` 선언 | `go doc builtin.error` | 1 | 메서드 하나 |
| ★ `error` 뜯기 (`t23a`) | `go build && ./prog` | 1 | `NumMethod`=1 · 무시해도 컴파일됨 |
| ★★★ 두 `errors.New` (`t23b`) | 〃 | 1 | `==` 가 **`false`** · `%v` 판과 `%w` 판의 `Is` 가 갈림 |
| ★★ 커스텀 타입 (`t23c`) | 〃 | 1 | 값 리시버는 값·포인터 둘 다 · `==` 가 타입에 따라 갈림 |
| ★★ 포인터 리시버 (`t23d`) | `go build -gcflags=-e` | 1 | **3건** · `method Error has pointer receiver` · exit 1 |
| ★★★ Go 판 (`t23go`) | `go build && ./prog` | 1 | 네 줄 |
| ★★★ Rust 판 (`t23rs`·`t23rs2`) | `rustc --edition 2021 -C debuginfo=0 … && ./prog` | 2 | 네 줄 · 문맥 판만 단계 문구가 붙음 |
| ★★★ 자바 판 (`Ex23`) | `javac -d . Ex23.java && java Ex23` | 1 | 네 줄 |
| ★★ 멀티 catch 금지 (`Ex23bad`) | `javac -d . Ex23bad.java` | 1 | `cannot be related by subclassing` · exit 1 |
| ★★★ 줄 수 세기 (`count.sh`) | `sh count.sh` — `awk` 로 함수를 떼고 `grep -c` | 1 | Go 14 · Rust 8 · 자바 8 · 오류 경로 3·3·2 |
| 형태 (`t23form`) | `go build && ./prog` | 1 | 여덟 줄 |

**구현·환경에 달린 항목**(버전이 오르거나 타깃이 바뀌면 **다시 찍어야 하는** 것)

| 항목 | 무엇에 달렸나 |
|---|---|
| `*errors.errorString`·`*fmt.wrapError` 라는 **이름** | **표준 라이브러리 내부** — 기대지 마라 |
| 오류 **메시지 글자**(`strconv.Atoi: parsing …`) | **표준 라이브러리 판** |
| 컴파일 에러 **문구 자체** | **툴체인 판(go1.27.1)** |
| Rust 의 오류 문구(`os error 2` 등) | **rustc 1.92.0 · 이 OS** |
| 자바의 예외 이름·메시지 | **JDK 21.0.5** |
| `count.sh` 가 세는 수 | ★ **소스가 바뀌면 바뀐다** — 그래서 세는 법을 블록에 실었다 |
| `errors.New` 가 **힙에 가나** | ★★ **안 쟀다** |
| 세 언어의 **실행 시간·할당** | ★★ **안 쟀다** |
| `panic`/`recover` | ★ **안 던졌다**([목록의 **27번 주제**](../27-panic-recover-and-where-to-use-them/)) |
| 오류 메시지 작성 관례(소문자·마침표) | ★ **안 던졌다** — 스타일 문제다 |
| `errors.Is`/`As`/`Unwrap`/`Join` 전반 | ★ (2)절에서 `Is` 를 한 번 부르고 넘겼다([24번 주제](../24-error-wrapping-and-errors-is-as-join/)) |
| 자바의 `finally`·try-with-resources, Rust 의 `Drop` | ★ **안 던졌다**(Go 의 짝은 [목록의 **26번 주제**](../26-defer-evaluation-lifo-named-results-and-loops/)) |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다.

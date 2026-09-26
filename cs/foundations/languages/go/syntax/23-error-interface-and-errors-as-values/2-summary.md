# go/syntax/23 — `error` 인터페이스와 값으로서의 오류 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Go 명세](https://go.dev/ref/spec) 의 Errors 절 ·
> [`errors`](https://pkg.go.dev/errors) · [`fmt`](https://pkg.go.dev/fmt) 문서.
> 인터페이스 선언은 웹이 아니라 **이 툴체인에게 `go doc builtin.error` 로 직접 물었다.**\
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.
> ★★ **대비를 위해 Rust 와 자바도 같은 프로그램으로 돌렸다** —
> `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `javac 21.0.5`(Temurin, `openjdk 21.0.5 2024-10-15 LTS`).
> 세 판 다 같은 머신에서 같은 파일 네 개를 읽혔다.\
> **버전** — `error` 인터페이스와 `errors.New` 는 **1.0부터 같다.**
> `errors.Is`/`As`/`Unwrap` 은 1.13, `errors.Join` 은 1.20 — 그쪽 정본은 [24번 주제](../24-error-wrapping-and-errors-is-as-join/)다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★ **본체는 넷째 창이다** — 「같은 프로그램을 세 언어로 써서 **호출부 코드 모양**을 나란히 놓고
**줄 수와 오류 경로 수를 기계가 세게 하는 창**」. ★★ **세는 것은 줄 수와 분기 수지 속도가 아니다.**

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | `error` 가 미리 선언된 인터페이스인 것 · 메서드 집합 규칙 |
| **구현(gc)·표준 라이브러리** | `errors`·`fmt`·`io` 가 그렇게 하는 것 | `*errors.errorString` 같은 **구체 타입 이름** · 오류 메시지 글자 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 실행 출력(재실행 대조까지) |

★★ **「오류가 값이다」는 언어 설계지 명세 조항이 아니다** — 명세에는
「`error` 는 미리 선언된 인터페이스 타입」이라는 한 줄뿐이다.
`(T, error)` 라는 **관례**는 표준 라이브러리와 커뮤니티가 세운 것이다.
★ 그래서 이 주제의 결론은 「**강제되지 않는다**」로 끝난다((2)절의 마지막 두 줄).

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ 세 언어 프로그램의 **출력 네 줄** | 같은 입력에 같은 답이다 |
| 안 흔들린다 | ★★★ `count.sh` 가 세는 **줄 수와 오류 경로 수** | 사람이 안 센다 — 스크립트가 센다 |
| 안 흔들린다 | `err == nil` 의 참거짓 · `%T` · `==` 의 답 | 타입 구조가 정한다 |
| 안 흔들린다 | 컴파일 에러 **문장과 `파일:줄:칸`** | 같은 소스·같은 판이면 같다 |
| 안 흔들린다 | `go doc builtin.error` 의 본문 | 이 툴체인 판에 든 글이다 |
| 해당 없음 | 힙 할당·실행 시간 | ★★ **안 쟀다.** 「`errors.New` 가 힙에 간다」 같은 말을 이 문서는 하지 않는다 |
| 해당 없음 | 맵 순회 순서 | 이 주제는 맵을 순회해 찍지 않는다 |

★ 이 주제의 블록은 **재실행에서 한 글자도 같았다.** 정규화 규칙을 **하나도 안 썼다.**

## 한눈에 — 쉽게 말하면

**Go 에서 오류는 「던지는 신호」가 아니라 「돌려주는 값」이다.**
그래서 **문법이 하나도 안 는다** — 함수가 값을 하나 더 돌려줄 뿐이다.
대신 **호출부가 그 값을 매번 받아야** 한다.

| 비유 | 실체 |
|---|---|
| 심부름을 시키고 「됐어? 안 됐어?」를 매번 묻는다 | **`(T, error)` 관례** — 오류가 마지막 반환값 |
| 「안 됐어」라는 쪽지를 받아 든다 | `err` 라는 **보통 변수** — 담고 넘기고 견준다 |
| 쪽지를 안 읽고 버려도 아무도 안 말린다 | ★★★ **컴파일러가 안 막는다** — `_` 로 버리거나 아예 안 받아도 된다 |
| 「이 쪽지 맞아?」 — 정해진 쪽지와 대 본다 | **센티넬 오류**(`io.EOF`)와 `==` |
| 쪽지에 숫자가 적혀 있다 | **커스텀 오류 타입** — 값을 들고 다닌다 |
| 같은 글자가 적힌 쪽지 둘은 다른 쪽지다 | ★★ `errors.New("x") == errors.New("x")` 가 **`false`** |
| 외치고 뛰쳐나가는 것 | **`panic`** — Go 에서는 **오류가 아니다**(목록의 **27번 주제**) |

```text
   ★★★ 「던진다」와 「돌려준다」 — 호출부 모양이 다르다

   자바 (던진다)                        Go (돌려준다)

     int n = loadPort(p);                 n, err := loadPort(p)
     ↑ 여기 실패가 안 보인다              ↑ 실패가 이 줄에 글자로 있다
                                          if err != nil { … }
     try {                                       ↑ 안 적으면 n 이 제로값인 채 지나간다
         …
     } catch (IOException e) { … }
     ↑ 실패 경로가 블록으로 따로 있다     Rust (돌려주는데 문법 지원이 있다)

                                          let n = load_port(p)?;
                                                            ↑ 이 한 글자가 if 세 줄이다
```

```text
   같은 프로그램 — 실패 네 가지가 어디로 가나

     설정 읽기 → 숫자 파싱 → 범위 검사 → 성공

   Go    각 단계마다 if err != nil { return 0, fmt.Errorf("문맥: %w", err) }
         ★ 문맥 문구를 손으로 붙인다

   Rust  각 단계마다 ?          ← From 변환이 자동으로 걸린다
         ★ 문맥은 map_err 로 따로 붙여야 붙는다

   Java  loadPort 는 throws 만 달고 지나간다
         ★ 호출부의 catch 한 곳이 네 가지를 한꺼번에 받는다
```

> **`error`** — 미리 선언된 인터페이스. **메서드가 `Error() string` 하나**뿐이다((1)절).

> **센티넬 오류(sentinel error)** — 패키지가 **값으로 공개**해 호출자가 `==`/`errors.Is` 로 견주는 오류.\
> 예: `io.EOF`·`fs.ErrNotExist`((2)절). 설계 논의의 정본은 목록의 **25번 주제**다.

> **커스텀 오류 타입** — `Error()` 를 단 자기 타입. **값을 들고 다닌다.**\
> 예: `&ParseErr{Line: 2, Raw: "x9"}` 에서 호출자가 `Line` 을 읽는다((3)절).

> **`(T, error)` 관례** — 오류를 **마지막 반환값**으로 두는 것. ★ **명세 조항이 아니라 관례**다.

- Rust 와 다른 점 — ★★★ **둘 다 「오류는 값」인데 문법 지원이 다르다.**
  Rust 는 `?` 한 글자가 **조기 반환과 `From` 변환을 같이** 하고, Go 는 그 세 줄을 **손으로** 적는다.
  ★ 그 대신 Go 는 **문맥 문구를 그 자리에서 붙일 수 있다**((5)절에서 세 판을 나란히 돌렸다).
  (Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **22번**·**23번**.)
- 자바와 다른 점 — ★★ 자바는 **던지고**, 호출부는 **`throws` 로 미루거나 `catch` 로 받는다.**
  ★ **Go 의 `error` 는 무시해도 컴파일되고**, 자바의 검사 예외는 **무시하면 컴파일이 안 된다.**
  ([`../../../java/syntax/25-exceptions/`](../../../java/syntax/25-exceptions/).)
- ★ Rust 23편이 그 차이를 한 줄로 적어 뒀다 — 「Go 의 `error` 는 무시해도 컴파일되고,
  Rust 의 `Result` 는 안 쓰면 경고가 난다」. **이 문서는 그 앞쪽 절반을 실측했다**((2)절의 마지막 두 줄).

## 이 주제가 답하려는 질문

1. **`error` 는 무엇인가** — 인터페이스라면 메서드가 몇 개이고, 그래서 무엇이 오류가 될 수 있나.
2. **「값」이라는 말이 코드에서 무엇을 바꾸나** — 담고 견주고 무시하는 것이 다 되나.
3. **호출부 코드 모양이 얼마나 다른가** — 세 언어로 같은 프로그램을 써서 **줄 수와 분기 수**로 답한다.

★ **오류 표면 설계**(센티넬을 공개할까, 타입을 공개할까)의 정본은 목록의 **25번 주제**다.
★ **래핑과 `Is`/`As`** 의 정본은 [24번 주제](../24-error-wrapping-and-errors-is-as-join/), **`panic`/`recover`** 는 목록의 **27번 주제**다.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| **`go doc` 으로 선언을 직접 묻기** | `error` 의 메서드가 **하나**라는 것 | [20번 주제](../20-interface-declaration-and-implicit-implementation/)에서 쓰던 창 |
| **`reflect` 로 인터페이스를 뜯기** | 메서드 수·시그니처·누가 만족하나 | 〃 |
| **`==` 와 `%T` 를 나란히 찍기** | 같은 메시지의 두 오류가 **다른 값**이라는 것 | 기본 창 |
| ★★★ **같은 프로그램을 세 언어로 쓰고 스크립트가 세게 하기** | 호출부 **줄 수와 오류 경로 수** — 사람이 안 센다 | ★ 본체 창 |
| ★★ **컴파일 에러로 메서드 집합을 되묻기** | `Error()` 를 포인터 리시버로 달면 **값이 못 담긴다** | [19번 주제](../19-method-sets-value-vs-pointer-receiver/)의 창 |
| **부적용 — 할당·시간 측정** | ★★★ **안 쟀다.** 「`errors.New` 가 힙에 간다」 같은 주장을 이 문서는 **하지 않는다** | — |
| **부적용 — 스택 트레이스** | Go 의 `error` 값에는 **스택이 안 들어 있다.** 잴 것이 없다 | — |

★★★ **넷째 창이 본체다.** 「오류가 값이면 호출부가 어떻게 되나」는
산문으로 적으면 취향 논쟁이 되고, **줄 수와 분기 수를 세면 사실**이 된다.
★ **세는 법까지 블록에 싣는다** — `count.sh` 가 `awk` 로 함수 본문을 떼어 `grep -c` 로 센다.
사람이 세지 않으니 틀릴 수 없다.

★★ **「부적용 — 할당·시간 측정」 칸이 이 주제의 약속**이다.
「예외가 느리다」·「`errors.New` 가 힙을 쓴다」는 **자주 적히는 말인데 이 문서는 안 쟀다.**
★ C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **15번**(RAII)이
`goto cleanup` 과 RAII 를 견준 것과 같은 방식으로,
**여기서도 재는 것은 글자 수**다.

### (1) ★ `error` 는 메서드 하나짜리 인터페이스다

**언제 쓰나** — 「무엇이 오류가 될 수 있나」가 궁금할 때.

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

그림 해설 (한 단계씩):

- ★★ **메서드가 하나**(`Error func() string`)뿐이다. 그래서 **만족하는 방법도 하나**다.
  `Error() string` 을 달면 **그 순간 오류**가 된다 — [20번 주제](../20-interface-declaration-and-implicit-implementation/)의 암묵 구현이 그대로 적용된다.
- ★ `go doc` 의 설명이 「**with the nil value representing no error**」라 적는다 —
  「**`nil` 이 오류 없음**」이라는 관례가 그 한 줄에 들어 있다.
  ★★ 그 `nil` 이 두 칸짜리라 [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/)의 함정이 생긴다.
- ★★ **오류가 값이므로 슬라이스에 담긴다** — `[]error{…}` 에 `errors.New`·`fmt.Errorf`·커스텀 타입·
  `io.EOF`·`nil` 이 나란히 들어간다. `%T` 가 넷 다 다르다.
- ★★★ **마지막 두 줄이 이 절의 결론이다** — 오류를 **`_` 로 버려도**,
  **반환값을 아예 안 받아도** 컴파일된다.
  ★ **자바의 검사 예외와 정확히 반대**다. 그쪽은 안 받으면 컴파일이 안 된다((5)절).

비용 — 인터페이스 호출 한 겹. **이 문서는 재지 않았다.**

```text
   ★★ error 는 칸이 하나다 — 그래서 무엇이든 오류가 될 수 있다

   type error interface {
       Error() string          ← 메서드 하나. reflect 로 세면 NumMethod = 1
   }
        ▲            ▲              ▲
        │            │              │
   errors.New   fmt.Errorf     내가 만든 타입
   (*errorString)  (*errorString  (Error() 만 달면 끝)
                    또는 *wrapError)

   ★ 등록도 상속도 없다. 목록도 없다(20번 주제).
```

### (2) ★★ 같은 메시지의 두 오류는 다른 값이다

**언제 쓰나** — 오류를 `==` 로 견줄 때.

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

그림 해설 (한 단계씩):

- ★★★ **`errors.New("같은 글자") == errors.New("같은 글자")` 가 `false`** 다.
  메시지는 같고(`a.Error() == b.Error()` 가 `true`) **값이 다르다.**
  ★ `%T` 가 **`*errors.errorString`** — **포인터**다. 포인터 비교라 새로 만들면 늘 다르다.
  ★★ **그것이 센티넬이 성립하는 이유**다. `io.EOF` 를 **한 번만 만들어 공개**하니
  그 값과 견주는 것이 「같은 오류냐」가 된다.
- **표준 라이브러리의 센티넬** — `io.EOF` 와 `fs.ErrNotExist` 가 둘 다 `*errors.errorString` 이고,
  `os.ErrNotExist == fs.ErrNotExist` 가 **`true`** 다(같은 값을 다시 내보낸 것이다).
- ★★★ **`fmt.Errorf` 는 `%w` 를 안 쓰면 그냥 새 `errorString`** 이다.
  `%v` 판과 `%w` 판의 **메시지가 한 글자도 같은데**(`true`)
  `errors.Is` 의 답이 **`false` 대 `true`** 로 갈린다.
  ★★ **로그만 봐서는 안 보이는 사고**다 — 정본은 [24번 주제](../24-error-wrapping-and-errors-is-as-join/)다.
- ★★ **마지막 두 줄이 `==` 의 한계**다 — 한 겹만 감싸도 `wrapped == ErrClosed` 가 **`false`** 가 된다.
  그래서 `errors.Is` 가 필요하다([24번 주제](../24-error-wrapping-and-errors-is-as-join/)).

비용 — 없다.

### (3) ★★ 커스텀 오류 타입은 값을 들고 다닌다

**언제 쓰나** — 호출자가 **무엇이 얼마나** 틀렸는지를 알아야 할 때.

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

그림 해설 (한 단계씩):

- ★★ **`ParseErr` 은 `Line` 과 `Raw` 를 들고 오고** 호출자가 그 값을 읽는다.
  센티넬로는 못 하는 일이다 — 센티넬은 「이것이냐」만 답한다.
- ★ **포인터 리시버와 값 리시버가 갈린다** —
  `&ParseErr{}` 은 포인터로만, `RangeErr{}` 은 **값으로도 포인터로도** 담긴다.
  [19번 주제](../19-method-sets-value-vs-pointer-receiver/)의 메서드 집합 규칙이 그대로다((4)절이 그 에러를 던진다).
- ★★ **마지막 두 줄이 [22번 주제](../22-type-assertion-any-and-comparable/)와 잇는다** —
  `RangeErr{1} == RangeErr{1}` 은 **`true`**(구조체가 비교 가능하다),
  `&ParseErr{} == &ParseErr{}` 은 **`false`**(포인터가 다르다).
  ★ **오류 타입을 값으로 만들지 포인터로 만들지가 `==` 의 뜻을 바꾼다.**

비용 — 구조체 하나. **이 문서는 재지 않았다.**

```text
   ★★ 센티넬 대 커스텀 타입 — 호출자가 무엇을 하느냐가 고른다

   호출자가 「이것이냐」만 묻는다        호출자가 값을 쓴다
        │                                    │
        ▼                                    ▼
   var ErrEmpty = errors.New(…)        type TooBig struct{ N, Max int }
   ── 패키지 수준 변수 하나 ──          func (e *TooBig) Error() string
        │                                    │
        ▼                                    ▼
   err == ErrEmpty                      if tb, ok := err.(*TooBig); ok {
   errors.Is(err, ErrEmpty)                 tb.N - tb.Max
                                        }
   ★ 감싸면 == 가 깨진다 → errors.Is   ★ 감싸면 단언이 깨진다 → errors.As
        (둘 다 목록의 24번 주제)
```

### (4) ★★ `Error()` 를 포인터 리시버로 달면 값이 못 담긴다

**언제 쓰나** — 「내 타입이 왜 `error` 가 아니라지?」 할 때. ★ **[19번 주제](../19-method-sets-value-vs-pointer-receiver/)의 직접 응용**이다.

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

그림 해설 (한 단계씩):

- ★★★ **에러가 세 건**이고 전부 같은 이유다 —
  **`PtrErr does not implement error (method Error has pointer receiver)`**.
- ★★ **세 자리가 다르다** — 변수 선언 · 함수 인자 · 슬라이스 리터럴.
  **인터페이스가 요구되는 모든 자리**에서 같은 이유로 막힌다.
- ★ **되는 네 가지**는 `&PtrErr{}`·`ValErr{}`·`&ValErr{}` 이다.
  값 리시버 메서드는 `T` 와 `*T` 둘 다의 집합에 들고, 포인터 리시버 메서드는 `*T` 에만 든다
  ([19번 주제](../19-method-sets-value-vs-pointer-receiver/)).
- ★★ **그래서 오류 타입의 관례가 갈린다** —
  `Error()` 를 **포인터 리시버로 달면 `&MyErr{}` 로만** 쓰게 되고
  **값 리시버로 달면 둘 다** 된다. ★ 그 선택이 (3)절의 `==` 결과까지 바꾼다.

비용 — 없다. 빌드에서 걸러진다.

### (5) ★★★ 호출부 코드 모양 — 같은 프로그램을 세 언어로

**언제 쓰나** — 「오류가 값이면 무엇이 달라지나」를 말할 때.

**같은 일을 한다** — 설정 파일을 읽어 포트 번호 하나를 얻는다.
실패 네 가지(파일 없음 · 숫자가 아님 · 범위 밖 · 성공)를 같은 네 입력으로 던진다.

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

그림 해설 (한 단계씩):

- ★★★ **네 줄의 결과가 같다.** 「같은 프로그램」이라는 전제가 출력으로 확인됐다.
- ★★ **다만 문구가 다르다** — 같은 실패에 세 언어가 다른 글자를 낸다.

| 실패 | Go | Rust(`?` 만) | Rust(문맥) | Java |
|---|---|---|---|---|
| 파일 없음 | `설정 읽기: open none.conf: no such file or directory` | `No such file or directory (os error 2)` | `설정 읽기: No such file or directory (os error 2)` | `NoSuchFileException: none.conf` |
| 숫자 아님 | `port 파싱: strconv.Atoi: parsing "x9": invalid syntax` | `invalid digit found in string` | `port 파싱: invalid digit found in string` | `NumberFormatException: For input string: "x9"` |

- ★★★ **Rust 의 `?` 는 문맥을 안 붙인다.** 그래서 두 판을 다 돌렸다 —
  `?` 만 쓴 판은 「어느 단계에서 났는지」가 **메시지에서 사라지고**,
  `map_err` 를 붙인 판은 Go 와 같은 문구가 된다.
  ★ **Go 의 `fmt.Errorf("문맥: %w", err)` 가 그 `map_err` 자리**다.
  ★★ 둘 다 **문맥은 손으로 붙인다** — 공짜로 따라오는 것이 아니다.
- ★★ **자바는 단계 문구가 아예 없다** — 예외가 **스택 트레이스를 들고 다니므로**
  「어디서 났나」를 메시지에 적을 필요가 적다.
  ★ 그 대신 여기서는 `catch` 가 **예외 종류로 갈라야** 해서 `e.getClass().getSimpleName()` 을 찍었다.
- ★★ **자바 쪽에는 Go·Rust 에 없는 실패 모양이 하나 더 있었다.**

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

  ★★★ **`Alternatives in a multi-catch statement cannot be related by subclassing`** —
  `NumberFormatException` 이 `IllegalArgumentException` 의 하위라서 **둘을 한 `catch` 에 못 적는다.**
  ★ **Go 에는 이 문제가 원리상 없다** — 오류는 **값**이고 값들 사이에 상속 관계가 없다.
  ★ 이 한 건이 「던지기」와 「돌려주기」의 차이를 **컴파일 에러로** 보여 준다.

비용 — **이 문서는 세 언어의 실행 시간·할당을 재지 않았다.**

### (6) ★★★ 줄 수와 분기 수를 기계가 센다

**언제 쓰나** — 「Go 가 장황하다」를 말할 때. ★ **재지 않은 주장을 피하려면 세어야 한다.**

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

그림 해설 (한 단계씩):

- ★★★ **함수 본문 — Go 가 14줄, Rust 가 8줄, 자바가 8줄**이다.
  ★ **Rust 는 문맥을 붙여도 8줄 그대로**다 — `map_err` 이 `?` 앞에 붙는 **한 식**이라 줄이 안 는다.
- ★★ **오류 경로 수는 셋 다 비슷하다**(Go 3 · Rust 3 · 자바 2).
  ★★★ 「**분기가 많다**」가 아니라 「**같은 분기를 적는 글자가 많다**」가 정확한 말이다 —
  Go 의 `if err != nil { return 0, fmt.Errorf(…) }` **세 줄**이 Rust 에서는 `?` **한 글자**다.
- ★★ **호출부는 Go 8줄 · Rust 6줄 · 자바 8줄**로 좁혀진다.
  ★ 호출부에서는 차이가 작다 — **실패를 다루는 자리가 한 군데로 모이기 때문**이다.
- ★★★ **둘째 표가 더 말이 된다** — 같은 파일에서 오류 배관이 **몇 번 글자로 적히나**.

| | 몇 번 | 무엇 |
|---|---|---|
| **Go** | `err` 라는 식별자 **12번** · `if err != nil` **4번** | 배관이 **본문 전체에 흩어진다** |
| **Rust** | `?` **2번** · `unwrap()` 3번 | 배관이 **한 글자씩** |
| **Java** | `throws` 2번 · `throw` 1번 · `catch` 1번 | 배관이 **선언부와 한 블록에** |

- ★★★ **이것이 「오류는 값이다」의 대가이자 값어치다.**
  `err` 가 12번 적혔다는 것은 **실패가 지나가는 자리가 12번 눈에 보인다**는 뜻이기도 하다.
  Rust 의 `?` 는 **두 자리로 줄이지만** 그만큼 **안 보인다.**
  ★ **어느 쪽이 낫다는 말을 이 문서는 하지 않는다** — 센 것은 글자 수뿐이다.

비용 — **이 문서는 세 언어의 성능을 재지 않았다.**

## 문법 — 형태와 규칙

### 형태

```go
// t23form.go
package main

import (
	"errors"
	"fmt"
	"os"
)

// (1) 미리 선언된 인터페이스 — 메서드 하나뿐이다
//	type error interface { Error() string }

// (2) 센티넬 오류 — 패키지가 값으로 공개한다
var ErrEmpty = errors.New("비어 있다")

// (3) 커스텀 오류 타입 — 값을 들고 다닌다
type TooBig struct{ N, Max int }

func (e *TooBig) Error() string { return fmt.Sprintf("%d 는 %d 를 넘는다", e.N, e.Max) }

// (4) (T, error) 관례 — 오류는 마지막 반환값이다
func parse(s string, max int) (int, error) {
	if s == "" {
		return 0, ErrEmpty // 센티넬을 그대로 돌려준다
	}
	n := len(s)
	if n > max {
		return 0, &TooBig{N: n, Max: max} // 구체 타입을 그 자리에서 만든다
	}
	return n, nil // (5) 성공이면 nil 을 명시로 (21번 주제)
}

func main() {
	// (6) 호출부는 if err != nil 로 받는다
	for _, s := range []string{"go", "", "golang"} {
		n, err := parse(s, 4)
		if err != nil {
			fmt.Printf("  %-8q 실패 : %v\n", s, err)
			continue
		}
		fmt.Printf("  %-8q 성공 : %d\n", s, n)
	}

	// (7) 센티넬은 == 로, 커스텀 타입은 단언으로 가른다 (24번 주제가 Is/As 로 일반화한다)
	_, err := parse("", 4)
	fmt.Println("  센티넬인가 :", err == ErrEmpty)
	_, err = parse("golang", 4)
	if tb, ok := err.(*TooBig); ok {
		fmt.Println("  넘은 만큼 :", tb.N-tb.Max)
	}

	// (8) 오류를 무시해도 컴파일된다
	n, _ := parse("", 4)
	fmt.Println("  무시한 판 :", n)

	// (9) 오류는 값이라 슬라이스에 담긴다
	errs := []error{ErrEmpty, &TooBig{N: 9, Max: 4}, nil}
	fmt.Println("  담은 개수 :", len(errs))

	// (10) 프로그램을 끝내는 것은 오류 값이 아니라 호출부다
	if err != nil {
		fmt.Fprintln(os.Stderr, "  os.Exit 로 끝낼지는 호출부가 정한다")
	}
}
```

```text
===== 명령: go build -trimpath -o prog . && ./prog =====
  "go"     성공 : 2
  ""       실패 : 비어 있다
  "golang" 실패 : 6 는 4 를 넘는다
  센티넬인가 : true
  넘은 만큼 : 2
  무시한 판 : 0
  담은 개수 : 3
  os.Exit 로 끝낼지는 호출부가 정한다
(exit 0)
```

규칙 불릿.

- **`error` 는 미리 선언된 인터페이스**이고 메서드는 **`Error() string` 하나**다.
- **`Error() string` 을 달면 그 타입이 오류가 된다.** 등록도 상속도 없다.
- **오류는 마지막 반환값**으로 둔다 — **관례**이지 명세 조항이 아니다.
- **성공이면 `nil` 을 명시로 돌려준다**([21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/)).
- **`errors.New` 는 매번 새 값**을 만든다. 같은 메시지라도 `==` 가 `false` 다.
- **센티넬은 패키지 수준 변수로 한 번만** 만든다.
- **커스텀 타입은 값을 들고 다닌다.** 호출자가 그 필드를 읽는다.
- **`Error()` 를 포인터 리시버로 달면 값이 인터페이스를 못 만족한다.**
- **오류를 무시해도 컴파일된다.** `_` 로 버리거나 아예 안 받아도 된다.
- **`panic` 은 오류가 아니다.** 경계를 넘길 때만 쓴다(목록의 **27번 주제**).

### 금지 사례 — 컴파일러가 거부하는 것

| 무엇 | 문장 |
|---|---|
| `Error()` 가 포인터 리시버인데 **값**을 `error` 에 담음 | `PtrErr does not implement error (method Error has pointer receiver)` |
| 같은 것을 **함수 인자**로 | `… as error value in argument to show: …` |
| 같은 것을 **슬라이스 리터럴**에 | `… as error value in array or slice literal: …` |

★ **거부하지 않는 것**이 더 중요하다 — **오류를 안 받아도, `_` 로 버려도 통과한다**((1)절).

## 어디서 틀리나

### 1. ★★★ 「오류를 안 받으면 컴파일러가 막겠지」

- (1)절 실측 — `_` 로 버려도, **반환값을 아예 안 받아도** 컴파일된다.
- 고치는 법 — 도구로 메운다(`errcheck` 류). ★ **이 머신에는 그 도구가 없어 이 문서는 안 던졌다**
  ([21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/) (6)절에서 확인했다).

### 2. ★★★ 「같은 메시지면 같은 오류겠지」

- (2)절 실측 — `errors.New("x") == errors.New("x")` 가 **`false`** 다. `*errors.errorString` **포인터** 비교다.
- 고치는 법 — 센티넬은 **패키지 수준 변수로 한 번만** 만들어 그 값을 공개한다.

### 3. ★★★ 「`fmt.Errorf` 로 감싸면 `==` 가 그대로 되겠지」

- (2)절 실측 — 한 겹만 감싸도 `wrapped == ErrClosed` 가 **`false`** 다.
- 고치는 법 — **`errors.Is`** 를 쓴다([24번 주제](../24-error-wrapping-and-errors-is-as-join/)).

### 4. ★★ 「`%v` 로 감싸나 `%w` 로 감싸나 같겠지」

- (2)절 실측 — **메시지가 한 글자도 같은데** `errors.Is` 가 **`false` 대 `true`** 로 갈린다.
- 고치는 법 — **감쌀 때는 `%w`.** 정본은 [24번 주제](../24-error-wrapping-and-errors-is-as-join/)다.

### 5. ★★ 「`Error()` 는 어느 리시버로 달아도 되겠지」

- (4)절 실측 — 포인터 리시버면 **값이 `error` 를 만족하지 않는다.** 에러 세 자리.
- 고치는 법 — **포인터로만 쓸 생각이면 포인터 리시버**, 값으로도 쓰려면 **값 리시버**.
  그 선택이 `==` 의 뜻까지 바꾼다((3)절).

### 6. ★★ 「Go 는 오류 처리가 장황하다」

- (6)절 실측 — 함수 본문이 **Go 14줄 · Rust 8줄 · 자바 8줄**이고,
  **오류 경로 수는 셋 다 2\~3** 이다.
  ★★ 정확한 말은 「**분기가 많다**」가 아니라 「**같은 분기를 적는 글자가 많다**」다.
- 고치는 법 — 이 말을 할 때 **무엇을 셌는지 같이 적는다.** 속도를 말하려면 **재야 한다**(안 쟀다).

### 7. ★ 「예외가 있으면 실패를 안 놓치겠지」

- (5)절 실측 — 자바 판은 `catch` 를 **한 번** 적고 지나갔고,
  멀티 catch 에서 **상속 관계 때문에 컴파일이 막히는** 자리가 하나 더 있었다.
- 고치는 법 — 이 문서는 **어느 쪽이 낫다고 말하지 않는다.** 두 모양을 나란히 두고 셌을 뿐이다.

### 8. ★ 「`panic` 으로 오류를 올리면 짧겠지」

- 이 문서는 **`panic` 을 안 던졌다.** 정본은 목록의 **27번 주제**다.
- 고치는 법 — **경계를 긋고 넘긴다.** Go 에서 `panic` 은 「호출 규약이 깨졌다」 쪽이고
  「밖에서 온 값이 틀렸다」는 `error` 다.

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| **`error` 가 미리 선언된 인터페이스인 것** | **명세 보장** | Errors 절 · `go doc builtin.error` |
| **메서드가 `Error() string` 하나인 것** | **명세 보장** | 〃 |
| **`Error() string` 만 달면 만족하는 것** | **명세 보장** | 암묵 구현([20번 주제](../20-interface-declaration-and-implicit-implementation/)) |
| **포인터 리시버면 값이 만족 못 하는 것** | **명세 보장** | 메서드 집합([19번 주제](../19-method-sets-value-vs-pointer-receiver/)) |
| **오류를 안 받아도 컴파일되는 것** | **명세 보장** | 반환값을 버리는 것에 제약이 없다 |
| **인터페이스 값의 `==` 규칙** | **명세 보장** | [22번 주제](../22-type-assertion-any-and-comparable/) (5)절 |
| **`(T, error)` 가 마지막인 것** | ★ **관례** | 명세에 그런 조항이 없다 |
| **`nil` 이 「오류 없음」인 것** | ★ **관례 + `go doc` 의 서술** | "with the nil value representing no error" |
| **`errors.New` 가 매번 새 값인 것** | **표준 라이브러리 계약** | 문서가 그렇게 적는다 |
| **`*errors.errorString` 이라는 타입 이름** | ★ **구현(표준 라이브러리 내부)** | 이름에 기대지 마라 |
| **`io.EOF`·`fs.ErrNotExist` 가 센티넬인 것** | **표준 라이브러리 계약** | 문서가 값으로 공개한다 |
| **`os.ErrNotExist == fs.ErrNotExist`** | **표준 라이브러리 계약** | `os` 가 `fs` 의 값을 다시 내보낸다 |
| **`fmt.Errorf` 가 `%w` 없이는 `*errorString` 인 것** | ★ **구현** | `%w` 판은 `*fmt.wrapError` 다(24번) |
| 오류 **메시지 글자**(`strconv.Atoi: parsing …`) | **표준 라이브러리 판** | 판이 오르면 달라질 수 있다 |
| 컴파일 에러 **문구 자체** | **툴체인 판(go1.27.1)** | 규칙은 명세, 문장은 gc 의 것 |
| Rust·자바의 **오류 문구** | **그 판의 것**(rustc 1.92.0 · JDK 21.0.5) | 판이 다르면 달라진다 |
| `errors.New` 가 **힙에 가나** | ★★ **안 쟀다** | 이 문서는 그 주장을 하지 않는다 |
| 세 언어의 **실행 시간·할당** | ★★ **안 쟀다** | 센 것은 **줄 수와 오류 경로 수**뿐이다 |
| `panic`/`recover` 의 비용·동작 | ★ **안 던졌다** | 목록의 **27번 주제** |

★ 이 주제의 결론은 「**`error` 는 메서드 하나짜리 인터페이스이고, 나머지는 전부 관례다**」이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 호출자가 **분기**해야 한다 | **센티넬** 또는 **커스텀 타입** | `errors.Is`/`As` 로 물을 수 있다(24번) |
| 호출자가 **값**을 써야 한다 | **커스텀 타입** | 센티넬은 「이것이냐」만 답한다 |
| 로그로 충분하다 | **`fmt.Errorf`** | 새 타입을 만들 이유가 없다 |
| 감싼다 | **`%w`** | `%v` 로 감싸면 `Is` 가 못 찾는다(24번) |
| 오류 타입을 값으로 할까 포인터로 할까 | **포인터가 기본** | 필드가 늘어도 복사가 없고 `==` 가 포인터 비교라 뜻이 분명하다 |
| `Error()` 의 리시버 | **포인터로 달았으면 포인터로만 쓴다** | 값이 안 담긴다((4)절) |
| 성공을 돌려준다 | **`return nil` 을 명시** | 구체 타입 변수를 그대로 돌려주면 함정이다(21번) |
| 프로그램을 끝낸다 | **호출부가 정한다** | 오류 값 자체는 아무것도 안 끝낸다 |
| 호출 규약이 깨졌다 | **`panic`**(27번) | 밖에서 온 값이 틀린 것은 `error` 다 |
| 오류 표면을 설계한다 | 목록의 **25번 주제** | 무엇을 공개할지가 거기 |

판단 규칙 두 줄.

- ★★★ **오류는 값이므로 「무엇을 돌려줄까」가 API 설계다.** 던지는 언어에는 없는 선택지다.
- ★★ **「Go 가 장황하다」를 말하려면 무엇을 셌는지 같이 적어라.** 줄 수인지 분기 수인지 속도인지.

## 핵심 문장

- ★★★ **`error` 는 메서드 하나짜리 인터페이스**다 — `Error() string`.
  `reflect` 로 세면 `NumMethod` 가 **1** 이고, 그래서 만족하는 방법도 하나뿐이다.
- ★★★ **오류가 값이라는 말은 「담고 견주고 무시할 수 있다」는 뜻**이다.
  슬라이스에 넣을 수 있고, `_` 로 버릴 수 있고, **아예 안 받아도 컴파일된다.**
  ★ **자바의 검사 예외와 정확히 반대**다.
- ★★★ **같은 메시지의 두 `errors.New` 는 같지 않다** — `*errors.errorString` **포인터** 비교다.
  그것이 **센티넬이 성립하는 이유**이자 **한 겹만 감싸도 `==` 가 깨지는 이유**다.
- ★★ **`%v` 로 감싸면 메시지가 한 글자도 같은데 `errors.Is` 가 못 찾는다.** 로그로는 안 보인다.
- ★★ **`Error()` 를 포인터 리시버로 달면 값이 `error` 를 못 만족한다** —
  변수 선언·함수 인자·슬라이스 리터럴 **세 자리**에서 같은 이유로 막힌다.
  [19번 주제](../19-method-sets-value-vs-pointer-receiver/)의 직접 응용이다.
- ★★★ **같은 프로그램을 세 언어로 쓰면 함수 본문이 Go 14줄 · Rust 8줄 · 자바 8줄**이고,
  **오류 경로 수는 셋 다 2\~3** 이다.
  「**분기가 많다**」가 아니라 「**같은 분기를 적는 글자가 많다**」가 정확한 말이다.
- ★★★ **오류 배관이 글자로 적히는 횟수는 Go 가 `err` 12번 · `if err != nil` 4번,
  Rust 가 `?` 2번, 자바가 `throws`/`throw`/`catch` 4번**이다.
  그 12번은 **실패가 지나가는 자리가 12번 보인다**는 뜻이기도 하다.
- ★★ **Rust 의 `?` 도 문맥은 안 붙인다** — `map_err` 을 붙이면 Go 와 같은 문구가 되고 줄 수는 안 는다.
  **문맥은 두 언어 다 손으로 붙인다.**
- ★★ **자바에는 Go·Rust 에 없는 실패 모양이 있다** —
  `Alternatives in a multi-catch statement cannot be related by subclassing`.
  **오류가 값이면 그 사이에 상속 관계가 없어 이 문제가 원리상 안 생긴다.**
- ★★ **「오류는 값이다」는 언어 설계지 명세 조항이 아니다.** 명세에는
  「`error` 는 미리 선언된 인터페이스」 한 줄뿐이고 **`(T, error)` 는 관례**다.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 23번)
- [20번 주제](../20-interface-declaration-and-implicit-implementation/)(인터페이스 선언) —
  **`Error() string` 만 달면 오류가 되는** 이유. 암묵 구현의 정본
- [19번 주제](../19-method-sets-value-vs-pointer-receiver/)(메서드 집합) —
  ★★ **(4)절의 정본.** 포인터 리시버가 무엇을 막는지
- [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/)(`nil` 인터페이스) —
  ★★ **「성공이면 `nil` 을 명시로」의 정본.** 이 주제의 `return nil` 이 왜 중요한지가 거기
- [22번 주제](../22-type-assertion-any-and-comparable/)(타입 단언) —
  커스텀 오류 타입을 되꺼내는 법. `==` 가 언제 패닉하는지
- [12번 주제](../12-functions-multiple-returns-named-results-and-variadics/)(다중 반환) —
  ★ **`(T, error)` 관례가 어느 문법에서 나오는지의 정본**
- [24번 주제](../24-error-wrapping-and-errors-is-as-join/)(`%w`·`Is`/`As`/`Join`) — ★★★ **이 주제의 직접 후속.**
  **여기는 「오류가 값이다」까지**, 그쪽은 **「그 값을 겹쳐 쌓고 되찾는 법」부터**
- 목록의 **25번 주제**(센티넬 대 커스텀 타입) — **오류 표면 설계의 정본.**
  여기는 **두 가지가 있다는 것**까지
- 목록의 **27번 주제**(`panic`/`recover`) — **여기는 `panic` 을 안 던졌다.** 그쪽이 정본
- 목록의 **42번 주제**(`fmt`) — `fmt.Errorf` 의 동사 규칙
- 목록의 **49번 주제**(`testing`) — 오류를 테스트에서 견주는 법
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **22번**
  ([`../../../rust/syntax/22-result-question-mark-and-from/`](../../../rust/syntax/22-result-question-mark-and-from/)) —
  ★★★ **그쪽은 `?` 한 글자가 조기 반환과 `From` 변환을 같이 한다**,
  여기는 **그 세 줄을 손으로 적는다.** (5)·(6)절이 그 대비를 줄 수로 잰다
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **23번**
  ([`../../../rust/syntax/23-panic-vs-result/`](../../../rust/syntax/23-panic-vs-result/)) —
  ★★ **그쪽은 `Result` 를 안 쓰면 경고가 난다**, 여기는 **무시해도 조용하다**
- [`../../../java/syntax/25-exceptions/`](../../../java/syntax/25-exceptions/) —
  ★★ **그쪽은 던지고 `throws` 로 전파한다**, 여기는 **돌려주고 호출부가 받는다**
- [`../../../python/syntax/`](../../../python/syntax/) ·
  [`../../../csharp/syntax/`](../../../csharp/syntax/) — 예외를 쓰는 다른 갈래들

## 용어 풀이

- **`error`** — 미리 선언된 인터페이스. 메서드는 `Error() string` 하나.
- **센티넬 오류** — 패키지가 값으로 공개해 호출자가 견주는 오류(`io.EOF`).
- **커스텀 오류 타입** — `Error()` 를 단 자기 타입. 값을 들고 다닌다.
- **`(T, error)` 관례** — 오류를 마지막 반환값으로 두는 것. 명세 조항이 아니다.
- **`*errors.errorString`** — `errors.New` 가 만드는 **구현 내부 타입**. 이름에 기대지 마라.
- **문맥 붙이기** — `fmt.Errorf("어디서: %w", err)` 처럼 어느 단계에서 났는지를 메시지에 더하는 것.
- **검사 예외(checked exception)** — 자바에서 **잡거나 `throws` 로 선언해야** 컴파일되는 예외.
- **`?` 연산자** — Rust 에서 실패면 변환해 조기 반환하는 한 글자. 개념적으로 `match` + `return`.

---

## 더 들어가면

- ★ **`panic`/`recover` 는 이 문서가 안 던졌다.** 정본은 목록의 **27번 주제**다.
  경계를 긋는 자리(고루틴 경계·라이브러리 공개 API)는 거기서 다룬다.
- ★★ **「예외가 느리다」·「`errors.New` 가 힙에 간다」는 이 문서가 안 쟀다.**
  그런 주장을 하려면 벤치마크가 필요하고, 그것은 목록의 **50번 주제**다.
- ★ **`errors.New` 가 매번 새 포인터를 만드는 것**은 관찰했지만
  **그것이 할당인지**는 안 쟀다(상수 문자열이면 컴파일러가 무엇을 하는지도 안 봤다).
- **오류 메시지 작성 관례**(소문자로 시작·마침표 없음)는 이 문서가 **안 던졌다** — 스타일 문제다.
- ★★ **`errors` 의 나머지**(`Is`·`As`·`Unwrap`·`Join`·`AsType`)는 [24번 주제](../24-error-wrapping-and-errors-is-as-join/)가 정본이다.
  이 문서는 (2)절에서 **`Is` 를 한 번 부르고** 넘겼다.
- ★ **자바의 `finally`·try-with-resources**, **Rust 의 `Drop`** 같은 정리 경로는 **안 던졌다** —
  Go 의 짝은 `defer` 이고 그쪽 정본은 목록의 **26번 주제**다.

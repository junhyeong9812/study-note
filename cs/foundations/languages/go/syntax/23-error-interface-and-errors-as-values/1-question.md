# go/syntax/23 — `error` 인터페이스와 값으로서의 오류 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> ★★★ **모든 문제에서 「이것이 명세인가 관례인가」를 먼저 적어라.**
> 이 주제에서 명세인 것은 몇 줄뿐이고 나머지는 전부 관례다.
> ★★ **세 언어 문제에서는 「무엇을 세는가」를 먼저 정해라** — 줄 수인가 분기 수인가.
> ★ **속도를 답으로 쓰지 마라.** 이 문서는 아무것도 재지 않았다.
> 소스는 Go 가 `go build -trimpath -o prog . && ./prog`,
> Rust 가 `rustc --edition 2021 -C debuginfo=0 … -o prog && ./prog`,
> 자바가 `javac -d . ….java && java …` 로 던졌다. Go 모듈 이름은 `ex` 다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `error` 를 뜯어보면 (예측)

```go
// t23a.go
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
```

- `error` 의 `Name()`·`Kind()`·`NumMethod()` 와 **메서드 하나의 시그니처**가 각각 무엇인가?
- `MyErr{}` 과 `int` 이 `error` 를 만족하나?
- `[]error` 다섯 원소의 `%T` 가 각각 무엇인가?
- 마지막 두 줄 — 오류를 `_` 로 버리거나 **아예 안 받으면** 어떻게 되나?

### 2. 같은 메시지의 두 오류 (예측)

```go
// t23b.go
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
```

- `a == b`·`a.Error() == b.Error()`·`errors.Is(a, b)` 가 각각 무엇인가 — 왜인가?
- `os.ErrNotExist == fs.ErrNotExist` 는 무엇인가?
- `%v` 로 감싼 것과 `%w` 로 감싼 것의 **메시지가 같은가**, `errors.Is` 의 답은 같은가?
- 마지막 두 줄 — 한 겹 감싸면 `wrapped == ErrClosed` 가 무엇이 되나?

### 3. 오류가 값을 들고 다니면 (예측)

```go
// t23c.go
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
```

- 첫 덩어리 세 줄에 무엇이 찍히나?
- `&ParseErr{}`·`RangeErr{}`·`&ParseErr{}` 의 `%T` 가 각각 무엇인가?
- `RangeErr{1} == RangeErr{1}` 과 `&ParseErr{} == &ParseErr{}` 이 각각 무엇인가 — 왜 갈리나?

### 4. `Error()` 를 포인터 리시버로 달면 (예측)

```go
// t23d.go
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
```

- 컴파일 에러가 **몇 건** 나오나?
- 문장은 무엇이고 **어느 세 자리**에서 나오나?
- 되는 네 가지는 무엇인가?

### 5. 같은 프로그램을 Go · Rust · 자바로 (예측)

```go
// t23go.go
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
```

- 네 입력(`ok.conf`·`bad.conf`·`big.conf`·`none.conf`)에 각각 무엇이 찍히나?
- 파일이 없을 때의 메시지를 **문구까지** 적어라.
- `loadPort` 안에서 오류 경로가 **몇 군데**인가?


```rust
// t23rs.rs
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
```

- 네 줄의 출력이 Go 와 **어디가 같고 어디가 다른가**?
- `?` 만 쓴 이 판은 「어느 단계에서 났는지」를 말해 주나?
- 문맥을 붙이려면 무엇을 더 적나 — 그러면 **줄 수가 느나**?


```java
// Ex23.java
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
```

- 네 줄의 출력이 무엇인가?
- `loadPort` 의 시그니처에 `throws IOException` 이 있는데 `NumberFormatException` 은 왜 없나?
- 이 파일에서 `catch` 는 **몇 번** 적혔나?


```java
// Ex23bad.java
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
```

- 컴파일되나? 안 되면 문장과 종료 코드는?
- Go 에는 왜 이 문제가 없나?

### 6. 줄 수와 분기 수를 세면 (예측)

- `loadPort` 함수 본문의 줄 수가 **Go · Rust · 자바** 각각 몇인가?
- 그 함수 안의 **오류 경로 수**는 각각 몇인가?
- 호출부(반복문 안)의 줄 수는 각각 몇인가?
- 파일 전체에서 `err`·`?`·`throws`/`throw`/`catch` 가 각각 **몇 번** 적혔나?

### 7. 「오류는 값이다」가 무엇을 바꾸나 (왜)

- 값이라서 **할 수 있게 된 것** 셋을 코드로 말하라.
- 값이라서 **잃은 것** 하나를 (1)절의 실측으로 말하라.
- Rust 의 `?` 는 무엇을 줄이고 무엇을 안 보이게 하나?
- 자바의 검사 예외는 Go 의 무엇에 해당하는 자리를 **컴파일러에게 시키나**?

### 8. 명세인가 관례인가 (경계)

- 「`error` 는 메서드 하나짜리 인터페이스」는 어느 층인가?
- 「오류는 마지막 반환값」은 어느 층인가?
- 「`nil` 은 오류 없음」은 어느 층인가?
- `*errors.errorString` 이라는 이름에 기대도 되나?

### 9. 무엇을 공개하나 (경계)

- 호출자가 **분기**만 하면 되는 오류는 무엇으로 내보내나?
- 호출자가 **값**을 써야 하는 오류는?
- 오류 타입을 값으로 만들지 포인터로 만들지는 무엇을 바꾸나?
- 이 질문의 정본은 몇 번 주제인가?

### 10. 다른 주제와 잇기 (연결)

- `(T, error)` 관례가 어느 문법에서 나오는지의 정본은 몇 번 주제인가?
- 「성공이면 `nil` 을 명시로」의 정본은 몇 번 주제인가?
- 포인터 리시버가 무엇을 막는지의 정본은 몇 번 주제인가?
- `%w`·`errors.Is`/`As` 의 정본은 몇 번 주제인가?
- `panic`/`recover` 의 정본은 몇 번 주제인가 — 이 문서는 그것을 던졌나?


## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

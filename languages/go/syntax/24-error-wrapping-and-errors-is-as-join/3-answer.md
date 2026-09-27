# go/syntax/24 — 오류 래핑 `%w` 와 `errors.Is`/`As`/`Join` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> 판 경계를 보이는 블록은 **`===== 소스: go.mod =====` 까지** 싣는다.
> ★ **근거로 읽을 칸** — 사슬의 **층수·차례·각 층의 `%T`**, `Is`/`As`/`AsType` 의 참거짓,
> 패닉·`go vet` 의 **메시지 본문**, 종료 코드, `Join` 메시지의 **줄바꿈 개수**,
> `api/go1NN.txt` 의 줄 번호와 본문.
> **근거로 읽지 않을 칸** — `errors.As` 패닉 블록의 **스택 프레임 힙 주소**(이 문서의 유일한 흔들리는 칸).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 메시지는 같고 `Is` 가 갈린다 · 사슬은 다섯 층이다

**출력**

```text
===== 소스: t24a.go =====
package main

import (
	"errors"
	"fmt"
)

var ErrDenied = errors.New("권한 없음")

type QueryErr struct{ SQL string }

func (e *QueryErr) Error() string { return "질의 실패: " + e.SQL }

func main() {
	base := ErrDenied
	withW := fmt.Errorf("사용자 조회: %w", base)
	withV := fmt.Errorf("사용자 조회: %v", base)

	fmt.Println("-- 메시지는 한 글자도 같다 --")
	fmt.Printf("  %%w 판 : %q\n", withW.Error())
	fmt.Printf("  %%v 판 : %q\n", withV.Error())
	fmt.Println("  같은가 :", withW.Error() == withV.Error())

	fmt.Println("-- 그런데 안이 다르다 --")
	fmt.Printf("  %%w 판 %%T : %T\n", withW)
	fmt.Printf("  %%v 판 %%T : %T\n", withV)
	fmt.Printf("  errors.Unwrap(%%w 판) : %v\n", errors.Unwrap(withW))
	fmt.Printf("  errors.Unwrap(%%v 판) : %v\n", errors.Unwrap(withV))

	fmt.Println("-- 그래서 Is 의 답이 갈린다 --")
	fmt.Printf("  errors.Is(%%w 판, ErrDenied) : %v\n", errors.Is(withW, ErrDenied))
	fmt.Printf("  errors.Is(%%v 판, ErrDenied) : %v   <- 못 찾는다\n", errors.Is(withV, ErrDenied))

	fmt.Println("-- As 도 마찬가지다 --")
	q := &QueryErr{SQL: "select 1"}
	qw := fmt.Errorf("배치 3번: %w", q)
	qv := fmt.Errorf("배치 3번: %v", q)
	var target *QueryErr
	fmt.Printf("  errors.As(%%w 판, &target) : %v (SQL=%v)\n", errors.As(qw, &target), sqlOf(target))
	target = nil
	fmt.Printf("  errors.As(%%v 판, &target) : %v (SQL=%v)   <- 못 찾는다\n",
		errors.As(qv, &target), sqlOf(target))

	fmt.Println("-- 로그만 봐서는 구별이 안 된다 --")
	fmt.Println("  %w :", qw)
	fmt.Println("  %v :", qv)
	fmt.Println("  두 줄이 같은가 :", qw.Error() == qv.Error())
}

func sqlOf(q *QueryErr) string {
	if q == nil {
		return "<nil>"
	}
	return q.SQL
}
===== 명령: go build -trimpath -o prog . && ./prog =====
-- 메시지는 한 글자도 같다 --
  %w 판 : "사용자 조회: 권한 없음"
  %v 판 : "사용자 조회: 권한 없음"
  같은가 : true
-- 그런데 안이 다르다 --
  %w 판 %T : *fmt.wrapError
  %v 판 %T : *errors.errorString
  errors.Unwrap(%w 판) : 권한 없음
  errors.Unwrap(%v 판) : <nil>
-- 그래서 Is 의 답이 갈린다 --
  errors.Is(%w 판, ErrDenied) : true
  errors.Is(%v 판, ErrDenied) : false   <- 못 찾는다
-- As 도 마찬가지다 --
  errors.As(%w 판, &target) : true (SQL=select 1)
  errors.As(%v 판, &target) : false (SQL=<nil>)   <- 못 찾는다
-- 로그만 봐서는 구별이 안 된다 --
  %w : 배치 3번: 질의 실패: select 1
  %v : 배치 3번: 질의 실패: select 1
  두 줄이 같은가 : true
(exit 0)
```

**왜 그런가**

- ★★★ **메시지가 한 글자도 같다**(`true`).
- ★★★ **`%T` 가 갈린다** — **`*fmt.wrapError`** 대 **`*errors.errorString`**.
  `errors.Unwrap` 이 **속 오류** 대 **`<nil>`** 이다.
  ★ `%w` 판만 **링크**를 들고 있다.
- **`errors.Is`** 가 **`true` 대 `false`**, **`errors.As`** 도 마찬가지다.
  ★★ `As` 쪽은 더 나쁘다 — **대상 변수가 `nil` 인 채로 남는다**(출력의 `SQL=<nil>`).
  그것을 `ok` 안 보고 쓰면 [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/)의 함정으로 이어진다.
- ★★★ **마지막 덩어리 — 로그 두 줄이 한 글자도 같다.**
  **`%v` 로 감싼 사고는 로그를 아무리 봐도 안 보인다.**
  ★ 보려면 **`%T` 를 같이 찍거나** `errors.Unwrap` 을 불러 봐야 한다.


**출력**

```text
===== 소스: t24b.go =====
package main

import (
	"errors"
	"fmt"
	"os"
)

type ConfigErr struct {
	Key string
	Err error
}

func (e *ConfigErr) Error() string { return "설정 " + e.Key + ": " + e.Err.Error() }
func (e *ConfigErr) Unwrap() error { return e.Err }

func main() {
	// 네 층을 쌓는다 — 맨 아래는 os 가 준 오류다
	_, base := os.Open("없는파일.conf")
	mid := &ConfigErr{Key: "port", Err: base}
	up := fmt.Errorf("기동 준비: %w", mid)
	top := fmt.Errorf("서버 시작: %w", up)

	fmt.Println("-- 사슬을 nil 까지 돈다 --")
	i := 0
	for e := top; e != nil; e = errors.Unwrap(e) {
		fmt.Printf("  [%d] %%T=%-22T %%v=%v\n", i, e, e)
		i++
	}
	fmt.Printf("  사슬 길이 : %d 층 (그 다음이 nil 이다)\n", i)

	fmt.Println("-- 맨 위 한 줄만 찍으면 이렇게 보인다 --")
	fmt.Println("  ", top)

	fmt.Println("-- 사슬의 어느 층이든 Is 로 찾아진다 --")
	fmt.Printf("  errors.Is(top, os.ErrNotExist) : %v\n", errors.Is(top, os.ErrNotExist))
	var pe *os.PathError
	fmt.Printf("  errors.As(top, &*os.PathError) : %v", errors.As(top, &pe))
	if pe != nil {
		fmt.Printf(" (Op=%q Path=%q)", pe.Op, pe.Path)
	}
	fmt.Println()
	var ce *ConfigErr
	fmt.Printf("  errors.As(top, &*ConfigErr)    : %v", errors.As(top, &ce))
	if ce != nil {
		fmt.Printf(" (Key=%q)", ce.Key)
	}
	fmt.Println()

	fmt.Println("-- 중간 층에서 Unwrap 을 안 달면 사슬이 거기서 끊긴다 --")
	cut := &NoUnwrap{Err: mid}
	j := 0
	for e := error(cut); e != nil; e = errors.Unwrap(e) {
		fmt.Printf("  [%d] %%T=%-22T %%v=%v\n", j, e, e)
		j++
	}
	fmt.Printf("  사슬 길이 : %d 층\n", j)
	fmt.Printf("  errors.Is(cut, os.ErrNotExist) : %v   <- 끊긴 위로는 못 간다\n",
		errors.Is(cut, os.ErrNotExist))
}

// Unwrap 을 안 단 래퍼
type NoUnwrap struct{ Err error }

func (e *NoUnwrap) Error() string { return "감싸기만 함: " + e.Err.Error() }
===== 명령: go build -trimpath -o prog . && ./prog =====
-- 사슬을 nil 까지 돈다 --
  [0] %T=*fmt.wrapError         %v=서버 시작: 기동 준비: 설정 port: open 없는파일.conf: no such file or directory
  [1] %T=*fmt.wrapError         %v=기동 준비: 설정 port: open 없는파일.conf: no such file or directory
  [2] %T=*main.ConfigErr        %v=설정 port: open 없는파일.conf: no such file or directory
  [3] %T=*fs.PathError          %v=open 없는파일.conf: no such file or directory
  [4] %T=syscall.Errno          %v=no such file or directory
  사슬 길이 : 5 층 (그 다음이 nil 이다)
-- 맨 위 한 줄만 찍으면 이렇게 보인다 --
   서버 시작: 기동 준비: 설정 port: open 없는파일.conf: no such file or directory
-- 사슬의 어느 층이든 Is 로 찾아진다 --
  errors.Is(top, os.ErrNotExist) : true
  errors.As(top, &*os.PathError) : true (Op="open" Path="없는파일.conf")
  errors.As(top, &*ConfigErr)    : true (Key="port")
-- 중간 층에서 Unwrap 을 안 달면 사슬이 거기서 끊긴다 --
  [0] %T=*main.NoUnwrap         %v=감싸기만 함: 설정 port: open 없는파일.conf: no such file or directory
  사슬 길이 : 1 층
  errors.Is(cut, os.ErrNotExist) : false   <- 끊긴 위로는 못 간다
(exit 0)
```

**왜 그런가**

- ★★★ **사슬이 다섯 층**이고 그 다음이 `nil` 이다.

| 층 | `%T` | 누가 만들었나 |
|---|---|---|
| [0] | `*fmt.wrapError` | 내 `fmt.Errorf("서버 시작: %w", …)` |
| [1] | `*fmt.wrapError` | 내 `fmt.Errorf("기동 준비: %w", …)` |
| [2] | `*main.ConfigErr` | 내가 만든 타입(`Unwrap()` 을 달았다) |
| [3] | `*fs.PathError` | ★ **`os.Open` 이 만든 층** |
| [4] | `syscall.Errno` | ★ **OS 가 준 번호** |

  ★★ **내가 쌓은 것은 셋인데 다섯이 나온다** — `os` 가 이미 두 층을 쌓아 놨기 때문이다.
- ★★ **맨 위 한 줄만 찍으면 네 층의 메시지가 이어 붙어** 나온다.
  각 층이 「내 문구 + 속 오류의 문구」로 만들어져서다.
- ★★★ **`errors.Is(top, os.ErrNotExist)` 가 `true` 인데 사슬 어디에도 그 값이 없다.**
  `syscall.Errno` 가 **자기 `Is` 메서드**를 갖고 있어서다 —
  **표준 라이브러리가 커스텀 `Is` 를 쓰는 실제 자리**다((4)번이 그 구조를 던진다).
- **`errors.As` 는 어느 층이든 꺼낸다** — `*fs.PathError`(Op·Path)도, 내 `*ConfigErr`(Key)도.
- ★★★ **마지막 덩어리 — `Unwrap()` 을 안 달면 사슬이 거기서 끊긴다.**
  `NoUnwrap` 은 **메시지에는 속 오류가 들어 있는데** 사슬 길이가 **1** 이고 `errors.Is` 가 **`false`** 다.
  ★ **메시지가 이어져 있다고 사슬이 이어진 것이 아니다.**

### 2. 값이 필요하면 `As`, 신원만 필요하면 `Is`

**출력**

```text
===== 소스: t24c.go =====
package main

import (
	"errors"
	"fmt"
	"io/fs"
	"os"
)

// 값을 안 들고 다니는 오류 — 센티넬. 물어볼 것은 "이것이냐"뿐이다.
var ErrRetryLater = errors.New("나중에 다시")

// 값을 들고 다니는 오류 — 호출자가 그 값을 쓴다.
type QuotaErr struct {
	Limit int
	Used  int
}

func (e *QuotaErr) Error() string { return fmt.Sprintf("할당량 초과: %d/%d", e.Used, e.Limit) }

func doWork(kind string) error {
	switch kind {
	case "retry":
		return fmt.Errorf("업로드 3단계: %w", ErrRetryLater)
	case "quota":
		return fmt.Errorf("업로드 3단계: %w", &QuotaErr{Limit: 100, Used: 137})
	case "file":
		_, err := os.Open("없는파일.bin")
		return fmt.Errorf("업로드 3단계: %w", err)
	}
	return nil
}

func handle(kind string) string {
	err := doWork(kind)
	if err == nil {
		return "성공"
	}
	// Is — "이 오류냐"만 물으면 된다 (값이 필요 없다)
	if errors.Is(err, ErrRetryLater) {
		return "Is  : 큐에 다시 넣는다"
	}
	if errors.Is(err, fs.ErrNotExist) {
		return "Is  : 파일이 없다고 사용자에게 알린다"
	}
	// As — 오류가 들고 온 값을 써야 하면 As 다
	var q *QuotaErr
	if errors.As(err, &q) {
		return fmt.Sprintf("As  : %d 만큼 줄여 다시 올린다", q.Used-q.Limit)
	}
	return "몰라서 그대로 올린다"
}

func main() {
	fmt.Println("-- 고르는 기준 : 값이 필요하면 As, 신원만 필요하면 Is --")
	for _, k := range []string{"retry", "quota", "file", "ok"} {
		fmt.Printf("  %-6s -> %s\n", k, handle(k))
	}

	fmt.Println("-- 같은 오류에 둘 다 던져 본다 --")
	err := doWork("quota")
	var q *QuotaErr
	fmt.Printf("  errors.Is(err, ErrRetryLater) : %v\n", errors.Is(err, ErrRetryLater))
	fmt.Printf("  errors.As(err, &q)            : %v  -> Limit=%d Used=%d\n",
		errors.As(err, &q), q.Limit, q.Used)

	fmt.Println("-- As 는 인터페이스로도 받는다 --")
	err2 := doWork("file")
	var pe interface{ Timeout() bool }
	fmt.Printf("  errors.As(err2, &interface{Timeout() bool}) : %v\n", errors.As(err2, &pe))
	var pathErr *fs.PathError
	fmt.Printf("  errors.As(err2, &*fs.PathError)             : %v\n", errors.As(err2, &pathErr))

	fmt.Println("-- As 는 찾으면 대상에 대입한다. 못 찾으면 건드리지 않는다 --")
	var q2 = &QuotaErr{Limit: -1, Used: -1}
	fmt.Printf("  찾기 전 : %v\n", q2)
	fmt.Printf("  errors.As(err2, &q2) = %v\n", errors.As(err2, &q2))
	fmt.Printf("  찾은 뒤 : %v  <- 못 찾았으므로 그대로다\n", q2)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
-- 고르는 기준 : 값이 필요하면 As, 신원만 필요하면 Is --
  retry  -> Is  : 큐에 다시 넣는다
  quota  -> As  : 37 만큼 줄여 다시 올린다
  file   -> Is  : 파일이 없다고 사용자에게 알린다
  ok     -> 성공
-- 같은 오류에 둘 다 던져 본다 --
  errors.Is(err, ErrRetryLater) : false
  errors.As(err, &q)            : true  -> Limit=100 Used=137
-- As 는 인터페이스로도 받는다 --
  errors.As(err2, &interface{Timeout() bool}) : true
  errors.As(err2, &*fs.PathError)             : true
-- As 는 찾으면 대상에 대입한다. 못 찾으면 건드리지 않는다 --
  찾기 전 : 할당량 초과: -1/-1
  errors.As(err2, &q2) = false
  찾은 뒤 : 할당량 초과: -1/-1  <- 못 찾았으므로 그대로다
(exit 0)
```

**왜 그런가**

- 네 줄이 **`Is` 로 두 가지 · `As` 로 한 가지 · 성공 하나**다.
  `quota` 만 **값**(`Used - Limit = 37`)이 필요해서 `As` 로 갔다.
- ★ `file` 은 `fs.ErrNotExist` 로 잡혔다 — (1)번과 같은 구조다(`syscall.Errno` 의 `Is`).
- ★★ **`As` 는 인터페이스로도 받는다** — `&interface{ Timeout() bool }` 에 **`true`** 다.
  `*fs.PathError` 가 그 메서드를 갖고 있기 때문이다.
  ★ **구체 타입을 몰라도 「타임아웃이냐」를 물을 수 있다.**
- ★★★ **마지막 덩어리 — `As` 가 못 찾으면 대상을 안 건드린다.**
  미리 넣어 둔 `{-1, -1}` 이 그대로 남았다.
  ★ 그래서 **`ok` 를 안 보고 대상만 보면 틀린다.**

### 3. 대상이 `*T` 면 `**T` 이고, `go vet` 이 탐침 4개 중 3개를 잡는다

**출력**

```text
===== 소스: t24d.go =====
package main

import (
	"errors"
	"fmt"
	"os"
)

type QuotaErr struct{ Limit int }

func (e *QuotaErr) Error() string { return fmt.Sprintf("할당량 %d", e.Limit) }

func main() {
	err := fmt.Errorf("겉: %w", &QuotaErr{Limit: 10})

	fmt.Println("-- 제대로 된 꼴 : 포인터의 포인터 --")
	var q *QuotaErr // 대상 타입 자체가 이미 포인터다
	fmt.Printf("  errors.As(err, &q) = %v  (&q 의 타입은 **QuotaErr)\n", errors.As(err, &q))
	fmt.Printf("  찾은 값 : %v\n", q)

	fmt.Println("-- 값 타입이면 한 겹이면 된다 --")
	var v ValErr
	err2 := fmt.Errorf("겉: %w", ValErr{N: 3})
	fmt.Printf("  errors.As(err2, &v) = %v  (&v 의 타입은 *ValErr)\n", errors.As(err2, &v))
	fmt.Printf("  찾은 값 : %v\n", v)

	fmt.Fprintln(os.Stderr, "-- 이제 포인터가 아닌 것을 넘긴다 --")
	var wrong *QuotaErr
	_ = errors.As(err, wrong) // & 를 빠뜨렸다
	fmt.Fprintln(os.Stderr, "-- 여기는 안 온다 --")
}

type ValErr struct{ N int }

func (e ValErr) Error() string { return fmt.Sprintf("값오류 %d", e.N) }
===== 명령: go build -trimpath -o prog . && ./prog =====
-- 제대로 된 꼴 : 포인터의 포인터 --
  errors.As(err, &q) = true  (&q 의 타입은 **QuotaErr)
  찾은 값 : 할당량 10
-- 값 타입이면 한 겹이면 된다 --
  errors.As(err2, &v) = true  (&v 의 타입은 *ValErr)
  찾은 값 : 값오류 3
-- 이제 포인터가 아닌 것을 넘긴다 --
panic: errors: target must be a non-nil pointer

goroutine 1 [running]:
errors.As({0x571560?, 0x1a9a7799c020?}, {0x5535b8?, 0x0?})
	errors/wrap.go:112 +0x1ff
main.main()
	ex/t24d.go:29 +0x39e
(exit 2)
```

**왜 그런가**

- ★★★ **대상 타입이 `*QuotaErr` 이므로 넘기는 것은 `&q`, 즉 `**QuotaErr`** 이다.
  「포인터의 포인터」라는 말이 그 뜻이다.
- ★ **값 타입이면 한 겹**이다 — `ValErr` 이면 `&v`(`*ValErr`).
  ★★ **「무조건 두 겹」이 아니다** — **오류 타입 자체가 포인터인가**가 정한다.
- ★★★ **`&` 를 빠뜨리면 `panic: errors: target must be a non-nil pointer`**, 종료 코드 **2**.
  스택에 **`errors.As(...)` 프레임**과 **`errors/wrap.go:112`** 가 찍힌다.
  ★ 그 줄의 괄호 안 주소는 **흔들리는 칸**이라 근거로 안 읽는다.


**출력**

```text
===== 소스: t24probe.go =====
// go vet 의 errorsas 분석기에게 같은 실수를 여러 모양으로 던진다.
package main

import (
	"errors"
	"fmt"
)

type QuotaErr struct{ Limit int }

func (e *QuotaErr) Error() string { return fmt.Sprintf("할당량 %d", e.Limit) }

func main() {
	err := fmt.Errorf("겉: %w", &QuotaErr{Limit: 10})

	// 탐침 1 — & 를 빠뜨렸다
	var a *QuotaErr
	_ = errors.As(err, a)

	// 탐침 2 — error 를 구현하지 않는 타입
	var b int
	_ = errors.As(err, &b)

	// 탐침 3 — nil 을 넘겼다
	_ = errors.As(err, nil)

	// 탐침 4 — 제대로 된 꼴 (여기는 조용해야 한다)
	var d *QuotaErr
	_ = errors.As(err, &d)

	fmt.Println(a, b, d)
}
===== 명령: go vet ./... =====
t24probe.go:18:6: second argument to errors.As must be a non-nil pointer to either a type that implements error, or to any interface type
t24probe.go:22:6: second argument to errors.As must be a non-nil pointer to either a type that implements error, or to any interface type
t24probe.go:25:6: second argument to errors.As must be a non-nil pointer to either a type that implements error, or to any interface type
(exit 1)
```

**왜 그런가**

- ★★★ **세 건**이 나오고 종료 코드 **1** 이다. 문장은 셋 다 같다 —
  **`second argument to errors.As must be a non-nil pointer to either a type that implements error, or to any interface type`**.
- **안 잡힌 것은 탐침 4**(`errors.As(err, &d)` — 제대로 된 꼴)다. 조용한 것이 맞다.
- ★★★ **[21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/) (6)절과 정확히 대비된다.**
  거기서는 **탐침 8개 중 0개**였고 여기서는 **4개 중 3개**다.
  ★ 이유는 **검사 가능성**이다 — `errors.As` 의 둘째 인자는
  **그 자리에서 타입만 보면** 옳고 그름이 정해지는데,
  `return p` 가 함정인지는 **`p` 가 실행 시점에 `nil` 인가**에 달려 있다.
  **정적 분석이 답할 수 있는 질문이냐가 갈랐다.**

### 4. 위에서 아래로, 그리고 「같음」은 다시 정의된다

**출력**

```text
===== 소스: t24e.go =====
package main

import (
	"errors"
	"fmt"
)

var ErrTemporary = errors.New("일시적")

// 층마다 Is 가 불릴 때 자기 이름을 찍는다 — Is 가 사슬을 어떻게 도는지 보려고.
type Layer struct {
	Name string
	Err  error
}

func (l *Layer) Error() string { return l.Name + " > " + l.Err.Error() }
func (l *Layer) Unwrap() error { return l.Err }
func (l *Layer) Is(target error) bool {
	fmt.Printf("    Is 가 %-8s 층에게 물었다 (target=%v) -> false\n", l.Name, target)
	return false
}

// HTTP 상태코드를 들고 다니는 오류. 같은 상태코드면 같은 것으로 친다.
type StatusErr struct{ Code int }

func (e *StatusErr) Error() string { return fmt.Sprintf("HTTP %d", e.Code) }
func (e *StatusErr) Is(target error) bool {
	t, ok := target.(*StatusErr)
	return ok && t.Code == e.Code
}

// As 를 직접 구현해 다른 타입으로 넘겨 줄 수도 있다.
type Coded struct{ C int }

func (c *Coded) Error() string { return fmt.Sprintf("코드 %d", c.C) }
func (c *Coded) As(target any) bool {
	if p, ok := target.(**StatusErr); ok {
		*p = &StatusErr{Code: c.C}
		fmt.Println("    Coded.As 가 *StatusErr 을 만들어 넘겼다")
		return true
	}
	return false
}

func main() {
	fmt.Println("-- Is 는 사슬을 위에서 아래로 훑는다 --")
	chain := &Layer{Name: "top", Err: &Layer{Name: "mid", Err: &Layer{Name: "bottom", Err: ErrTemporary}}}
	fmt.Printf("  errors.Is(chain, ErrTemporary) = %v\n", errors.Is(chain, ErrTemporary))
	fmt.Println("  (각 층의 Is 가 false 를 돌려줘도 == 비교가 따로 돌아 맨 아래에서 맞는다)")

	fmt.Println("-- 찾는 대상이 아예 없으면 끝까지 간다 --")
	fmt.Printf("  errors.Is(chain, errors.New(\"다른 것\")) = %v\n",
		errors.Is(chain, errors.New("다른 것")))

	fmt.Println("-- 커스텀 Is 로 '같음'을 새로 정의한다 --")
	e := fmt.Errorf("요청 처리: %w", &StatusErr{Code: 404})
	fmt.Printf("  errors.Is(e, &StatusErr{404}) = %v   <- 다른 포인터인데 참이다\n",
		errors.Is(e, &StatusErr{Code: 404}))
	fmt.Printf("  errors.Is(e, &StatusErr{500}) = %v\n", errors.Is(e, &StatusErr{Code: 500}))
	fmt.Printf("  == 로 견주면            = %v\n",
		errors.Unwrap(e) == error(&StatusErr{Code: 404}))

	fmt.Println("-- 커스텀 As 로 다른 타입을 내줄 수 있다 --")
	e2 := fmt.Errorf("게이트웨이: %w", &Coded{C: 503})
	var se *StatusErr
	fmt.Printf("  errors.As(e2, &se) = %v", errors.As(e2, &se))
	if se != nil {
		fmt.Printf(" -> Code=%d", se.Code)
	}
	fmt.Println()
	fmt.Println("  (사슬에 *StatusErr 이 하나도 없는데 찾아졌다)")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
-- Is 는 사슬을 위에서 아래로 훑는다 --
    Is 가 top      층에게 물었다 (target=일시적) -> false
    Is 가 mid      층에게 물었다 (target=일시적) -> false
    Is 가 bottom   층에게 물었다 (target=일시적) -> false
  errors.Is(chain, ErrTemporary) = true
  (각 층의 Is 가 false 를 돌려줘도 == 비교가 따로 돌아 맨 아래에서 맞는다)
-- 찾는 대상이 아예 없으면 끝까지 간다 --
    Is 가 top      층에게 물었다 (target=다른 것) -> false
    Is 가 mid      층에게 물었다 (target=다른 것) -> false
    Is 가 bottom   층에게 물었다 (target=다른 것) -> false
  errors.Is(chain, errors.New("다른 것")) = false
-- 커스텀 Is 로 '같음'을 새로 정의한다 --
  errors.Is(e, &StatusErr{404}) = true   <- 다른 포인터인데 참이다
  errors.Is(e, &StatusErr{500}) = false
  == 로 견주면            = false
-- 커스텀 As 로 다른 타입을 내줄 수 있다 --
    Coded.As 가 *StatusErr 을 만들어 넘겼다
  errors.As(e2, &se) = true -> Code=503
  (사슬에 *StatusErr 이 하나도 없는데 찾아졌다)
(exit 0)
```

**왜 그런가**

- ★★★ **로그가 `top` → `mid` → `bottom` 순서**로 찍힌다. 위에서 아래로 훑는다.
- ★★ **셋 다 `false` 를 돌려줬는데 결과가 `true`** 다.
  `errors.Is` 는 층마다 **두 가지**를 한다 — ① `== target` 인가 ② `Is` 메서드가 있으면 물어본다.
  **①이 맨 아래(`ErrTemporary`)에서 맞았다.**
- **찾는 것이 없으면 끝까지 간다** — 셋에게 다 묻고 `false` 다.
- ★★★ **커스텀 `Is` 로 「같음」이 새로 정의된다** —
  `errors.Is(e, &StatusErr{404})` 가 **`true`** 인데 같은 자리를 `==` 로 견주면 **`false`** 다.
  **다른 포인터인데 같은 오류로 친다.** `{500}` 은 `false` 다.
- ★★★ **커스텀 `As` 는 더 세다** — `Coded` 가 `*StatusErr` 을 **만들어서** 넘겼다.
  **사슬에 `*StatusErr` 이 하나도 없는데 `errors.As` 가 `true`** 다.
  ★ (1)번의 `syscall.Errno` 가 표준 라이브러리에서 같은 일을 한다.

### 5. `%w` 여러 개와 `Join` 은 사슬이 아니라 트리다

**출력**

```text
===== 소스: t24f.go =====
package main

import (
	"errors"
	"fmt"
)

var (
	ErrA = errors.New("A 실패")
	ErrB = errors.New("B 실패")
	ErrC = errors.New("C 실패")
)

func main() {
	fmt.Println("-- %w 를 여러 개 쓰면 (1.20) --")
	multi := fmt.Errorf("두 가지가 같이 터졌다: %w / %w", ErrA, ErrB)
	fmt.Printf("  %%T      : %T\n", multi)
	fmt.Printf("  메시지  : %v\n", multi)
	fmt.Printf("  Is(ErrA): %v   Is(ErrB): %v   Is(ErrC): %v\n",
		errors.Is(multi, ErrA), errors.Is(multi, ErrB), errors.Is(multi, ErrC))

	fmt.Println("-- 그런데 errors.Unwrap 은 nil 을 준다 --")
	fmt.Printf("  errors.Unwrap(multi) : %v\n", errors.Unwrap(multi))
	fmt.Println("  이유 — errors.Unwrap 은 Unwrap() error 만 보고, 여기 있는 것은 Unwrap() []error 다")

	fmt.Println("-- 그 메서드를 직접 물어본다 --")
	if u, ok := multi.(interface{ Unwrap() []error }); ok {
		list := u.Unwrap()
		fmt.Printf("  Unwrap() []error 의 길이 : %d\n", len(list))
		for i, e := range list {
			fmt.Printf("    [%d] %%T=%-22T %%v=%v\n", i, e, e)
		}
	}
	if _, ok := multi.(interface{ Unwrap() error }); !ok {
		fmt.Println("  Unwrap() error 는 없다")
	}

	fmt.Println("-- 그래서 사슬을 도는 코드가 여기서 멈춘다 --")
	n := 0
	for e := error(multi); e != nil; e = errors.Unwrap(e) {
		fmt.Printf("  [%d] %v\n", n, e)
		n++
	}
	fmt.Printf("  사슬로 본 길이 : %d 층 (그런데 안에 둘이 들어 있다)\n", n)

	fmt.Println("-- errors.Is 는 그 둘을 다 본다 : 사슬이 아니라 트리를 돈다 --")
	deep := fmt.Errorf("겉: %w", fmt.Errorf("속1: %w / 속2: %w", ErrA, fmt.Errorf("더 속: %w", ErrC)))
	fmt.Printf("  Is(deep, ErrA): %v   Is(deep, ErrC): %v   Is(deep, ErrB): %v\n",
		errors.Is(deep, ErrA), errors.Is(deep, ErrC), errors.Is(deep, ErrB))
	fmt.Printf("  errors.Unwrap(deep) : %v\n", errors.Unwrap(deep))
	fmt.Printf("  그 다음 Unwrap      : %v\n", errors.Unwrap(errors.Unwrap(deep)))
}
===== 명령: go build -trimpath -o prog . && ./prog =====
-- %w 를 여러 개 쓰면 (1.20) --
  %T      : *fmt.wrapErrors
  메시지  : 두 가지가 같이 터졌다: A 실패 / B 실패
  Is(ErrA): true   Is(ErrB): true   Is(ErrC): false
-- 그런데 errors.Unwrap 은 nil 을 준다 --
  errors.Unwrap(multi) : <nil>
  이유 — errors.Unwrap 은 Unwrap() error 만 보고, 여기 있는 것은 Unwrap() []error 다
-- 그 메서드를 직접 물어본다 --
  Unwrap() []error 의 길이 : 2
    [0] %T=*errors.errorString    %v=A 실패
    [1] %T=*errors.errorString    %v=B 실패
  Unwrap() error 는 없다
-- 그래서 사슬을 도는 코드가 여기서 멈춘다 --
  [0] 두 가지가 같이 터졌다: A 실패 / B 실패
  사슬로 본 길이 : 1 층 (그런데 안에 둘이 들어 있다)
-- errors.Is 는 그 둘을 다 본다 : 사슬이 아니라 트리를 돈다 --
  Is(deep, ErrA): true   Is(deep, ErrC): true   Is(deep, ErrB): false
  errors.Unwrap(deep) : 속1: A 실패 / 속2: 더 속: C 실패
  그 다음 Unwrap      : <nil>
(exit 0)
```

**왜 그런가**

- **`%T` 가 `*fmt.wrapErrors`**(복수형)이고 `Is` 가 `ErrA`·`ErrB` 를 둘 다 찾는다.
- ★★★ **`errors.Unwrap(multi)` 이 `<nil>`** 이다.
  **`errors.Unwrap` 은 `Unwrap() error` 만 보고** 여기 있는 것은 **`Unwrap() []error`** 다.
  ★ 직접 단언해 물으면 **길이 2** 이고 `Unwrap() error` 는 **없다**.
- ★★★ **그래서 사슬 반복문이 1층에서 멈춘다** — 「사슬로 본 길이 1층인데 안에 둘이 들어 있다」.
  ★ **(1)번의 반복문을 그대로 쓰면 못 본다.**
- ★★ **`errors.Is` 는 그래도 다 찾는다** — `deep` 에서 `ErrA` 도 `ErrC` 도 `true` 다.
  `go doc errors` 가 그 동작을 「**tree … pre-order, depth-first traversal**」이라 적는다((7)번).
- ★★★ **정리 — `Is`/`As` 는 트리를 돌고 `errors.Unwrap` 은 사슬만 돈다.**


**출력**

```text
===== 소스: t24g.go =====
package main

import (
	"errors"
	"fmt"
	"strings"
)

var (
	ErrName  = errors.New("이름이 비었다")
	ErrEmail = errors.New("메일이 형식에 안 맞는다")
	ErrAge   = errors.New("나이가 음수다")
)

func validate(name, email string, age int) error {
	var errs []error
	if name == "" {
		errs = append(errs, ErrName)
	}
	if !strings.Contains(email, "@") {
		errs = append(errs, ErrEmail)
	}
	if age < 0 {
		errs = append(errs, ErrAge)
	}
	return errors.Join(errs...) // 빈 슬라이스면 nil 이다
}

func main() {
	fmt.Println("-- Join 은 여러 오류를 한 값으로 묶는다 --")
	err := validate("", "nope", -1)
	fmt.Printf("  %%T : %T\n", err)
	fmt.Printf("  %%v :\n%v\n", err)
	fmt.Printf("  메시지에 줄바꿈이 몇 개 : %d\n", strings.Count(err.Error(), "\n"))
	fmt.Printf("  %%q : %q\n", err.Error())

	fmt.Println("-- 셋 다 Is 로 찾아진다 --")
	fmt.Printf("  Is(ErrName)=%v Is(ErrEmail)=%v Is(ErrAge)=%v\n",
		errors.Is(err, ErrName), errors.Is(err, ErrEmail), errors.Is(err, ErrAge))

	fmt.Println("-- 하나도 안 틀리면 nil 이다 --")
	fmt.Printf("  validate(\"고\", \"a@b\", 1) == nil : %v\n", validate("고", "a@b", 1) == nil)

	fmt.Println("-- nil 을 섞어 넣으면 그 자리는 빠진다 --")
	j := errors.Join(nil, ErrName, nil, ErrAge, nil)
	fmt.Printf("  errors.Join(nil, A, nil, C, nil) -> %q\n", j.Error())
	fmt.Printf("  Unwrap() []error 의 길이 : %d\n", lenOf(j))
	fmt.Printf("  errors.Join(nil, nil) == nil : %v\n", errors.Join(nil, nil) == nil)
	fmt.Printf("  errors.Join() == nil         : %v\n", errors.Join() == nil)

	fmt.Println("-- Join 이 만드는 것은 사슬이 아니라 트리다 --")
	inner := errors.Join(ErrName, ErrEmail)
	outer := errors.Join(inner, ErrAge)
	fmt.Printf("  errors.Unwrap(outer) : %v\n", errors.Unwrap(outer))
	fmt.Println("  트리를 손으로 걸어 본다 :")
	walk(outer, 0)

	fmt.Println("-- Join 한 값에 %w 를 씌우면 두 꼴이 섞인다 --")
	mixed := fmt.Errorf("검증 실패: %w", inner)
	fmt.Printf("  %%T : %T\n", mixed)
	fmt.Printf("  errors.Unwrap(mixed) : %T\n", errors.Unwrap(mixed))
	fmt.Printf("  Is(mixed, ErrEmail)  : %v\n", errors.Is(mixed, ErrEmail))
	fmt.Printf("  %%v :\n%v\n", mixed)
}

func lenOf(e error) int {
	if u, ok := e.(interface{ Unwrap() []error }); ok {
		return len(u.Unwrap())
	}
	return -1
}

func walk(e error, depth int) {
	pad := strings.Repeat("  ", depth+1)
	switch u := e.(type) {
	case interface{ Unwrap() []error }:
		fmt.Printf("%s+ %T (가지 %d개)\n", pad, e, len(u.Unwrap()))
		for _, c := range u.Unwrap() {
			walk(c, depth+1)
		}
	case interface{ Unwrap() error }:
		fmt.Printf("%s- %T %q\n", pad, e, e.Error())
		walk(u.Unwrap(), depth+1)
	default:
		fmt.Printf("%s- %T %q\n", pad, e, e.Error())
	}
}
===== 명령: go build -trimpath -o prog . && ./prog =====
-- Join 은 여러 오류를 한 값으로 묶는다 --
  %T : *errors.joinError
  %v :
이름이 비었다
메일이 형식에 안 맞는다
나이가 음수다
  메시지에 줄바꿈이 몇 개 : 2
  %q : "이름이 비었다\n메일이 형식에 안 맞는다\n나이가 음수다"
-- 셋 다 Is 로 찾아진다 --
  Is(ErrName)=true Is(ErrEmail)=true Is(ErrAge)=true
-- 하나도 안 틀리면 nil 이다 --
  validate("고", "a@b", 1) == nil : true
-- nil 을 섞어 넣으면 그 자리는 빠진다 --
  errors.Join(nil, A, nil, C, nil) -> "이름이 비었다\n나이가 음수다"
  Unwrap() []error 의 길이 : 2
  errors.Join(nil, nil) == nil : true
  errors.Join() == nil         : true
-- Join 이 만드는 것은 사슬이 아니라 트리다 --
  errors.Unwrap(outer) : <nil>
  트리를 손으로 걸어 본다 :
  + *errors.joinError (가지 2개)
    + *errors.joinError (가지 2개)
      - *errors.errorString "이름이 비었다"
      - *errors.errorString "메일이 형식에 안 맞는다"
    - *errors.errorString "나이가 음수다"
-- Join 한 값에 %w 를 씌우면 두 꼴이 섞인다 --
  %T : *fmt.wrapError
  errors.Unwrap(mixed) : *errors.joinError
  Is(mixed, ErrEmail)  : true
  %v :
검증 실패: 이름이 비었다
메일이 형식에 안 맞는다
(exit 0)
```

**왜 그런가**

- ★★★ **줄바꿈이 2개**다(세 오류). `%q` 로 보면
  `"이름이 비었다\n메일이 형식에 안 맞는다\n나이가 음수다"` 다.
  ★ **`", "` 가 아니라 `"\n"`** 이다 — 로그 한 줄로 찍으면 **줄이 늘어난다.**
- **`nil` 을 섞으면 빠진다** — `Join(nil, A, nil, C, nil)` 의 길이가 **2** 다.
- ★★★ **전부 `nil` 이거나 인자가 없으면 `nil`** 이다.
  그래서 `return errors.Join(errs...)` 한 줄이 「**하나도 안 틀렸으면 `nil`**」이 된다.
  ★ [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/)의 함정을 **`Join` 이 스스로 피해 준다** —
  `*joinError` 를 `nil` 로 돌려주는 것이 아니라 **인터페이스 `nil`** 을 준다.
- ★★★ **`errors.Unwrap(outer)` 이 `<nil>`** 이고 손으로 걸으면
  **가지 2개짜리 마디 안에 가지 2개짜리 마디**가 들어 있다 — **트리**다.
- ★★ **`Join` 한 값에 `%w` 를 씌우면 두 꼴이 섞인다** —
  겉이 `*fmt.wrapError`(사슬), 속이 `*errors.joinError`(트리)다.
  `errors.Unwrap` 이 **한 칸은 가고 거기서 멈춘다.** `Is` 는 끝까지 찾는다.
  ★ 메시지도 **한 줄 + 줄바꿈**으로 섞인다.

### 6. `AsType` 은 트리를 보고, `go.mod` 는 아무 말도 안 한다

**출력**

```text
===== 소스: t24h.go =====
package main

import (
	"errors"
	"fmt"
	"io/fs"
	"os"
)

type QuotaErr struct{ Limit int }

func (e *QuotaErr) Error() string { return fmt.Sprintf("할당량 %d", e.Limit) }

func main() {
	_, ioErr := os.Open("없는파일.bin")
	err := fmt.Errorf("업로드: %w", fmt.Errorf("열기: %w", ioErr))

	fmt.Println("-- errors.As : 대상 변수를 미리 만들어 주소를 넘긴다 --")
	var pe *fs.PathError
	if errors.As(err, &pe) {
		fmt.Printf("  As     : Op=%q Path=%q\n", pe.Op, pe.Path)
	}

	fmt.Println("-- errors.AsType : 타입 인자로 주고 값을 돌려받는다 (1.26) --")
	if pe2, ok := errors.AsType[*fs.PathError](err); ok {
		fmt.Printf("  AsType : Op=%q Path=%q\n", pe2.Op, pe2.Path)
	}

	fmt.Println("-- 못 찾으면 제로값과 false 다 --")
	q, ok := errors.AsType[*QuotaErr](err)
	fmt.Printf("  AsType[*QuotaErr] : ok=%v q=%v\n", ok, q)

	fmt.Println("-- 22번 주제의 comma-ok 단언과 모양이 같다. 다른 점은 사슬을 탄다는 것이다 --")
	_, ok2 := err.(*fs.PathError)
	fmt.Printf("  err.(*fs.PathError) comma-ok : %v  <- 맨 위 층만 본다\n", ok2)
	_, ok3 := errors.AsType[*fs.PathError](err)
	fmt.Printf("  errors.AsType[*fs.PathError] : %v  <- 트리를 다 본다\n", ok3)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
-- errors.As : 대상 변수를 미리 만들어 주소를 넘긴다 --
  As     : Op="open" Path="없는파일.bin"
-- errors.AsType : 타입 인자로 주고 값을 돌려받는다 (1.26) --
  AsType : Op="open" Path="없는파일.bin"
-- 못 찾으면 제로값과 false 다 --
  AsType[*QuotaErr] : ok=false q=<nil>
-- 22번 주제의 comma-ok 단언과 모양이 같다. 다른 점은 사슬을 탄다는 것이다 --
  err.(*fs.PathError) comma-ok : false  <- 맨 위 층만 본다
  errors.AsType[*fs.PathError] : true  <- 트리를 다 본다
(exit 0)
```

**왜 그런가**

- **둘이 같은 값을 찾는다**(`Op="open"`·`Path="없는파일.bin"`).
- **못 찾으면 제로값과 `false`** 다 — 여기서는 `*QuotaErr` 의 제로값이라 `<nil>` 이 찍혔다.
- ★★★ **마지막 두 줄이 답이다** —
  `err.(*fs.PathError)` 는 **`false`**(맨 위 층만 본다),
  `errors.AsType[*fs.PathError](err)` 는 **`true`**(트리를 다 본다).
  ★★ **모양은 [22번 주제](../22-type-assertion-any-and-comparable/)의 comma-ok 와 같고 보는 범위가 다르다.**
  `errors.As`/`AsType` 은 「**사슬(트리)을 따라 반복하는 타입 단언**」이라고 읽으면 맞는다.
- ★ (3)번의 「포인터의 포인터」 실수가 **원리상 생길 수 없다** — 넘길 포인터가 없다.


**출력**

```text
===== 소스: go.mod =====
module ex

go 1.19
===== 소스: t24ver.go =====
package main

import (
	"errors"
	"fmt"
)

var ErrA = errors.New("A")
var ErrB = errors.New("B")

func main() {
	j := errors.Join(ErrA, ErrB)           // errors.Join 은 1.20
	m := fmt.Errorf("%w / %w", ErrA, ErrB) // %w 두 개는 1.20
	w := fmt.Errorf("%w", ErrA)            // %w 하나는 1.13
	fmt.Println(errors.Is(j, ErrA), errors.Is(m, ErrB), errors.Unwrap(w) == ErrA)
}
===== 명령: go vet ./... =====
(exit 0)
```

```text
===== 소스: go.mod =====
module ex

go 1.19
===== 소스: t24ver.go =====
package main

import (
	"errors"
	"fmt"
)

var ErrA = errors.New("A")
var ErrB = errors.New("B")

func main() {
	j := errors.Join(ErrA, ErrB)           // errors.Join 은 1.20
	m := fmt.Errorf("%w / %w", ErrA, ErrB) // %w 두 개는 1.20
	w := fmt.Errorf("%w", ErrA)            // %w 하나는 1.13
	fmt.Println(errors.Is(j, ErrA), errors.Is(m, ErrB), errors.Unwrap(w) == ErrA)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
true true true
(exit 0)
```

```text
===== 소스: go.mod =====
module ex

go 1.20
===== 소스: t24ver.go =====
package main

import (
	"errors"
	"fmt"
)

var ErrA = errors.New("A")
var ErrB = errors.New("B")

func main() {
	j := errors.Join(ErrA, ErrB)           // errors.Join 은 1.20
	m := fmt.Errorf("%w / %w", ErrA, ErrB) // %w 두 개는 1.20
	w := fmt.Errorf("%w", ErrA)            // %w 하나는 1.13
	fmt.Println(errors.Is(j, ErrA), errors.Is(m, ErrB), errors.Unwrap(w) == ErrA)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
true true true
(exit 0)
```

**왜 그런가**

- ★★★ **`go 1.19` 에서 그냥 컴파일되고 돌아간다.** `go vet` 도 **출력 0줄에 종료 코드 0** 이다.
  `go 1.20` 판과 출력이 **한 글자도 같다**(`true true true`).
- ★★★ **[22번 주제](../22-type-assertion-any-and-comparable/) (7)절과 정반대**다.
  거기서는 `go.mod` 의 같은 한 줄이
  **`any to satisfy comparable requires go1.20 or later (check go.mod)`** 를 **여덟 건** 냈다.
- ★★★ **이유는 층이 다르기 때문**이다 —
  `comparable` 은 **언어 기능**이라 컴파일러가 `-lang` 으로 막고,
  `errors.Join` 은 **패키지 함수**라 막을 문법 규칙이 없다.
  **링크된 표준 라이브러리에 그 함수가 있으면 그냥 불린다.**
- ★ **그래서 「몇 부터 되나」는 문서와 `api/*.txt` 로만 안다**((7)번).

### 7. 1.13 · 1.20 · 1.26

**출력**

```text
===== 명령: grep -rn "pkg errors, func" "$(go env GOROOT)"/api/go1*.txt | sed "s|^.*/api/||" | sort -V =====
go1.13.txt:46:pkg errors, func As(error, interface{}) bool
go1.13.txt:47:pkg errors, func Is(error, error) bool
go1.13.txt:48:pkg errors, func Unwrap(error) error
go1.20.txt:237:pkg errors, func Join(...error) error #53435
go1.26.txt:129:pkg errors, func AsType[$0 error](error) ($0, bool) #51945
go1.txt:2469:pkg errors, func New(string) error
(exit 0)
```

```text
===== 명령: go doc errors =====
package errors // import "errors"

Package errors implements functions to manipulate errors.

The New function creates errors whose only content is a text message.

An error e wraps another error if e's type has one of the methods

    Unwrap() error
    Unwrap() []error

If e.Unwrap() returns a non-nil error w or a slice containing w, then we say
that e wraps w. A nil error returned from e.Unwrap() indicates that e does
not wrap any error. It is invalid for an Unwrap method to return an []error
containing a nil error value.

An easy way to create wrapped errors is to call fmt.Errorf and apply the %w verb
to the error argument:

    wrapsErr := fmt.Errorf("... %w ...", ..., err, ...)

Successive unwrapping of an error creates a tree. The Is and As functions
inspect an error's tree by examining first the error itself followed by the tree
of each of its children in turn (pre-order, depth-first traversal).

See https://go.dev/blog/go1.13-errors for a deeper discussion of the philosophy
of wrapping and when to wrap.

Is examines the tree of its first argument looking for an error that matches the
second. It reports whether it finds a match. It should be used in preference to
simple equality checks:

    if errors.Is(err, fs.ErrExist)

is preferable to

    if err == fs.ErrExist

because the former will succeed if err wraps io/fs.ErrExist.

AsType examines the tree of its argument looking for an error whose type matches
its type argument. If it succeeds, it returns the corresponding value of that
type and true. Otherwise, it returns the zero value of that type and false.
The form

    if perr, ok := errors.AsType[*fs.PathError](err); ok {
    	fmt.Println(perr.Path)
    }

is preferable to

    if perr, ok := err.(*fs.PathError); ok {
    	fmt.Println(perr.Path)
    }

because the former will succeed if err wraps an *io/fs.PathError.

var ErrUnsupported = New("unsupported operation")
func As(err error, target any) bool
func AsType[E error](err error) (E, bool)
func Is(err, target error) bool
func Join(errs ...error) error
func New(text string) error
func Unwrap(err error) error
(exit 0)
```

**왜 그런가**

| API | 언제부터 | 어디서 |
|---|---|---|
| `errors.New` | **1.0** | `go1.txt:2469` |
| `errors.Is` · `As` · `Unwrap` | **1.13** | `go1.13.txt:46\~48` |
| `errors.Join` | **1.20** | `go1.20.txt:237` |
| `errors.AsType[E error]` | **1.26** | `go1.26.txt:129` |

- ★★★ **`$(go env GOROOT)/api/go1NN.txt` 가 정본**이다. 릴리스 노트를 기억으로 적지 않아도 된다.
- ★★ **`%w` 는 그 파일에 안 나온다** — **함수가 아니라 포맷 동사**라 API 목록의 대상이 아니다.
  `%w` 가 1.13, `%w` 여러 개가 1.20 이라는 것은 **`fmt` 문서 쪽**이다.
  ★ 이 문서는 **`%w` 두 개가 이 판에서 도는 것**만 실행으로 보였다((5)번).
- ★★★ **그 파일이 못 담는 것** — 「**동작이 바뀐 판**」이다.
  예컨대 `errors.Is` 가 `Unwrap() []error` 를 보게 된 것은 **API 추가가 아니라 동작 변경**이라
  그 파일에 줄이 없다. ★ **창의 한계를 같이 적어 둔다.**
- `go doc errors` 가 계약을 한 자리에 적는다 —
  「An error e **wraps** another error if e's type has one of the methods `Unwrap() error` / `Unwrap() []error`」,
  그리고 ★★★ **「Successive unwrapping of an error creates a tree.」** —
  **「사슬」이 아니라** 「**트리**」라고 적혀 있다.

### 8. 명세는 한 줄, 나머지는 계약

| 사실 | 층 |
|---|---|
| 「`error` 는 메서드 하나짜리 인터페이스」 | ★★★ **명세 보장** |
| 「`Unwrap` 을 달면 사슬에 낀다」 | ★★★ **표준 라이브러리 계약** — 명세에 `Unwrap` 이라는 낱말이 없다 |
| 「`%w` 가 감싼다」 | **표준 라이브러리 계약(1.13)** |
| 「`Is`/`As` 가 트리를 pre-order DFS 로 돈다」 | **표준 라이브러리 계약** |
| `*fmt.wrapError` 라는 **이름** | ★★ **구현 내부** |

- ★★★ **그 차이가 (6)번을 설명한다** — 컴파일러는 **언어 규칙**을 강제하고,
  **패키지의 약속**은 강제할 수단이 없다. `-lang` 게이트가 안 걸리는 것이 **버그가 아니라 구조**다.
- ★★★ **`*fmt.wrapError` 라는 이름에 기대면 안 된다.** `%w` 두 개면 `*fmt.wrapErrors`,
  `Join` 이면 `*errors.joinError` 로 바뀐다. **타입 이름이 아니라 `Is`/`As` 로 물어야** 한다.

### 9. 문맥이 있으면 `%w`, 없으면 그대로

- **문맥을 붙일 것이 있으면** `fmt.Errorf("어디서: %w", err)`,
  **없으면** `return err`. ★ 층을 늘리면 메시지가 길어지므로 **붙일 말이 있을 때만** 감싼다.
- **「타임아웃이냐」** → **`As` + 인터페이스 타입**(`&interface{ Timeout() bool }`).
  구체 타입을 몰라도 된다((2)번).
- **검증에서 셋을 모은다** → **`errors.Join`**. 하나도 안 틀렸으면 **`nil`** 이다((5)번).
- **직접 래퍼 타입** → **`Unwrap() error` 를 단다.** 안 달면 사슬이 끊긴다((1)번).
- ★★ **사슬을 손으로 걷는 코드** → **`Unwrap() []error` 를 빠뜨리기 쉽다.**
  `Join` 과 `%w` 여러 개가 거기서 멈춘다((5)번).

### 10. 구조는 거의 같고 `Join` 만 Go 에 있다

- **Rust 의 `source()` 가 `Unwrap()`**, **`downcast_ref` 가 `errors.As`** 다.
  ★★ **구조가 거의 같다** — Rust 24편도 그렇게 적어 뒀다.
  갈리는 것은 **Rust 가 열거형 오류에 `match` 로 완전성 검사를 얹을 수 있다**는 것이다
  (Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **24번**).
- ★ **Rust std 에 `Join` 의 짝이 없다** — 여러 오류를 한 값으로 묶는 표준 함수가 없다.
- **자바의 `getCause()` 가 `Unwrap()`** 이고,
  ★★ **스택 트레이스가 언어에 내장**돼 있다([`../../../java/syntax/25-exceptions/`](../../../java/syntax/25-exceptions/)).
  **Go 의 오류 값에는 스택이 없다** — 그래서 (1)번처럼 **문맥 문구를 손으로 붙여** 그 자리를 메운다.

### 11. 다른 주제와 잇기

- 「오류가 값이다」의 정본 — [23번 주제](../23-error-interface-and-errors-as-values/).
  ★ 그쪽 (2)절의 「**한 겹만 감싸도 `==` 가 깨진다**」가 이 주제를 부른다.
- 「사슬을 따라 반복하는 타입 단언」 —
  [22번 주제](../22-type-assertion-any-and-comparable/). `AsType` 의 comma-ok 모양도 거기서 온다.
- `go vet` 이 아무것도 안 잡는 대비 —
  [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/) (6)절(**8개 중 0개**).
- 오류 표면 설계의 정본 — [목록의 **25번 주제**](../25-sentinel-errors-vs-custom-error-types/).
- `%w` 를 포함한 `fmt` 동사의 정본 — [목록의 **42번 주제**](../42-fmt-verbs-stringer-and-errorf/).
- 덤 — **암묵 구현**은 [20번 주제](../20-interface-declaration-and-implicit-implementation/)(`Unwrap`·`Is`·`As` 가
  인터페이스 선언 없이 동작하는 바탕), **`panic`/`recover`** 는 [목록의 **27번 주제**](../27-panic-recover-and-where-to-use-them/),
  **`go vet` 전반**은 [목록의 **52번 주제**](../52-tools-gofmt-vet-build-tags-embed-and-escape-analysis/)다.


---

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행 1회** | `normalize-shaky.py` 로 **★고칠 것 0** |
| 판 확인 | `go version` | 1 | `go1.27.1 linux/amd64` |
| ★★★ `%w` 대 `%v` (`t24a`) | `go build && ./prog` | 1 | 메시지 동일 · `Is` 가 `true` 대 `false` |
| ★★★ 사슬 걷기 (`t24b`) | 〃 | 1 | **5층** · `Unwrap` 없는 래퍼는 **1층** |
| ★★ `Is` 대 `As` (`t24c`) | 〃 | 1 | 값이 필요한 자리만 `As` · 못 찾으면 대상 그대로 |
| ★★ `As` 인자 (`t24d`) | 〃 | 1 | `panic: errors: target must be a non-nil pointer` · **exit 2** |
| ★★★ `go vet` 탐침 (`t24probe`) | `go vet ./...` | 1 | **4개 중 3개** · exit 1 |
| ★★ 커스텀 `Is`/`As` (`t24e`) | `go build && ./prog` | 1 | 층 순서 로그 3줄 · 다른 포인터인데 `Is` 가 `true` |
| ★★★ `%w` 여러 개 (`t24f`) | 〃 | 1 | `*fmt.wrapErrors` · `errors.Unwrap` 이 `nil` · 길이 2 |
| ★★★ `Join` (`t24g`) | 〃 | 1 | 줄바꿈 **2개** · `nil` 이면 `nil` · **트리** |
| ★ `AsType` (`t24h`) | 〃 | 1 | 단언은 `false`, `AsType` 은 `true` |
| ★★★ 판 경계 (`t24ver`) | **`go.mod` 의 `go` 줄만 바꿔** `go vet` + 빌드 | 3 | 1.19 에서도 **vet 0줄 · 그냥 컴파일** |
| ★★★ API 판 경계 | `grep` 으로 `api/go1*.txt` | 1 | 1.0 · 1.13 · 1.20 · 1.26 |
| 계약 확인 | `go doc errors` | 1 | 「wraps」·「tree … pre-order, depth-first」 |
| 형태 (`t24form`) | `go build && ./prog` | 1 | 일곱 줄 |

**구현·환경에 달린 항목**(버전이 오르거나 타깃이 바뀌면 **다시 찍어야 하는** 것)

| 항목 | 무엇에 달렸나 |
|---|---|
| `errors.As` 패닉의 **스택 프레임 힙 주소** | **런타임** — 이 문서의 **유일한 흔들리는 칸** |
| `*fmt.wrapError`·`*fmt.wrapErrors`·`*errors.joinError` 라는 **이름** | **표준 라이브러리 내부** — 기대지 마라 |
| `errors/wrap.go` 의 **줄 번호** | **이 툴체인 판** |
| 패닉·`go vet` 의 **문구 자체** | **툴체인 판(go1.27.1)** |
| ★★★ `-lang` 게이트가 이 API 들을 **안 막는 것** | **도구(구현)** — 언어 기능과 갈리는 자리 |
| `api/*.txt` 가 **`%w` 를 안 담는 것** | **그 파일의 성질** — 포맷 동사는 대상이 아니다 |
| `api/*.txt` 가 **동작 변경을 안 담는 것** | 〃 |
| `syscall.Errno` 가 `Is` 를 갖고 있는 것 | **표준 라이브러리 계약** |
| `Is`/`As` 의 **비용** | ★ **안 쟀다**([목록의 **50번 주제**](../50-benchmarks-testing-b-and-reading-profiles/)) |
| `errors.ErrUnsupported`(1.21) | ★ **안 던졌다** |
| 오류에 **스택 트레이스**를 붙이는 외부 패키지 | ★ **안 던졌다** — 이 머신에 없다 |
| `Is`/`As` 가 **순환 참조**를 만나면 | ★ **안 던졌다** |
| `%w` 와 다른 동사를 섞을 때의 인자 순서 | ★ **안 던졌다**([목록의 **42번 주제**](../42-fmt-verbs-stringer-and-errorf/)) |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다.

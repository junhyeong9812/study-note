# go/syntax/24 — 오류 래핑 `%w` 와 `errors.Is`/`As`/`Join` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> ★★★ **모든 문제에서 「사슬인가 트리인가」를 먼저 적어라.** `Join` 과 `%w` 여러 개가 그 갈림이다.
> ★★ **「이것을 누가 보장하나」를 매번 물어라** — 이 주제의 답은 거의 다
> 「**명세가 아니라 `errors` 패키지의 계약**」이다.
> ★ **판 경계를 답할 때는 어디서 뗐는지도 적어라**(`api/go1NN.txt` 인지 문서인지).
> 소스는 전부 `go build -trimpath -o prog . && ./prog` 로 던졌다. 모듈 이름은 `ex` 다.
> 판 경계를 보는 블록은 **`go.mod` 의 `go` 줄만 바꿔** 두 번 던졌다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `%w` 와 `%v` · 그리고 사슬을 `nil` 까지 (예측)

```go
// t24a.go
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
```

- 두 판의 **메시지가 같은가**?
- 두 판의 `%T` 가 각각 무엇인가?
- `errors.Unwrap` 이 각각 무엇을 주나?
- `errors.Is`·`errors.As` 의 답이 각각 무엇인가 — `As` 쪽 대상 변수에는 무엇이 남나?


```go
// t24b.go
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
```

- 사슬이 **몇 층**이고 각 층의 `%T` 가 무엇인가?
- 내가 쌓은 층은 셋인데 왜 그 수가 나오나?
- `errors.Is(top, os.ErrNotExist)` 가 무엇인가 — 사슬에 그 값이 있나?
- 마지막 덩어리 — `Unwrap()` 을 안 단 래퍼의 사슬 길이와 `errors.Is` 의 답은?

### 2. `Is` 와 `As` 를 고르면 (예측)

```go
// t24c.go
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
```

- 네 입력(`retry`·`quota`·`file`·`ok`)에 각각 무엇이 찍히나?
- `errors.As(err2, &interface{ Timeout() bool })` 가 무엇인가 — 왜인가?
- 마지막 덩어리 — `As` 가 못 찾았을 때 대상 변수에 무엇이 남나?

### 3. `As` 의 둘째 인자와 `go vet` (예측)

```go
// t24d.go
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
```

- `&q` 의 타입은 무엇인가 — 왜 두 겹인가?
- 값 타입일 때는 몇 겹인가?
- 마지막 — `&` 를 빠뜨리면 무엇이 일어나고 종료 코드는 몇인가?


```go
// t24probe.go
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
```

- `go vet ./...` 이 **몇 건**을 내고 종료 코드는 몇인가?
- 탐침 넷 중 **안 잡힌 것**은 무엇이고 왜인가?
- [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/)에서 같은 도구가 낸 답과 견주면 무엇이 다른가?

### 4. `Is` 는 무엇에게 어떤 순서로 묻나 (예측)

```go
// t24e.go
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
```

- 첫 덩어리에서 **로그 세 줄**이 어떤 순서로 찍히나?
- 각 층의 `Is` 가 `false` 를 돌려줬는데 최종 결과가 무엇인가 — 왜인가?
- 커스텀 `Is` 를 단 `StatusErr` 은 `errors.Is(e, &StatusErr{404})` 에 무엇을 답하나 — `==` 는?
- 마지막 — 사슬에 `*StatusErr` 이 하나도 없는데 `errors.As` 가 무엇을 답하나?

### 5. `%w` 여러 개와 `errors.Join` (예측)

```go
// t24f.go
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
```

- `%T` 가 무엇인가?
- `errors.Unwrap(multi)` 이 무엇을 주나 — 왜인가?
- `Unwrap() []error` 로 단언하면 길이가 몇인가?
- 사슬 반복문으로 세면 **몇 층**인가?
- `errors.Is` 는 `deep` 안의 `ErrA`·`ErrC` 를 찾나?


```go
// t24g.go
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
```

- 메시지에 **줄바꿈이 몇 개**인가? `%q` 로 보면 어떤 글자인가?
- `errors.Join(nil, A, nil, C, nil)` 의 `Unwrap() []error` 길이는?
- `errors.Join(nil, nil)` 과 `errors.Join()` 은 각각 무엇인가?
- `errors.Unwrap(outer)` 이 무엇인가 — 트리를 걸으면 어떤 모양인가?
- `Join` 한 값에 `%w` 를 씌우면 `%T` 와 `errors.Unwrap` 이 각각 무엇인가?

### 6. `AsType` 과 `go.mod` 를 낮추면 (예측)

```go
// t24h.go
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
```

- 두 함수가 같은 값을 찾나?
- 못 찾으면 `AsType` 이 무엇을 돌려주나?
- 마지막 두 줄 — `err.(*fs.PathError)` 와 `errors.AsType[*fs.PathError](err)` 의 답이 왜 갈리나?


```go
// t24ver.go
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
```

<!-- 같은 소스를 go.mod 의 go 1.19 와 go 1.20 두 판으로 던졌다. -->

- `go 1.19` 에서 컴파일되나? `go vet` 은 **몇 줄**을 내나?
- `go 1.20` 판과 출력이 다른가?
- [22번 주제](../22-type-assertion-any-and-comparable/)에서 같은 방법으로 얻었던 답과 견주면 무엇이 다른가 — 왜 다른가?

### 7. 판 경계를 어디서 떼나 (경계)

- `errors.Is`/`As`/`Unwrap` · `Join` · `AsType` 이 각각 **몇부터**인가?
- 그것을 어느 파일에서 뗐나?
- **`%w` 는 왜 그 파일에 안 나오나**?
- 그 파일이 **못 담는 것** 하나를 말하라.

### 8. 무엇이 명세이고 무엇이 계약인가 (왜)

- 「`Unwrap` 을 달면 사슬에 낀다」는 어느 층인가?
- 「`error` 는 메서드 하나짜리 인터페이스」는 어느 층인가?
- 그 차이가 (6)번의 결과를 어떻게 설명하나?
- `*fmt.wrapError` 라는 이름에 기대도 되나?

### 9. 어느 것을 쓰나 (경계)

- 문맥을 붙여 올릴 때와 그대로 올릴 때를 가르는 기준은?
- 「타임아웃이냐」를 구체 타입을 모르고 묻고 싶다 — 무엇을 쓰나?
- 검증에서 실패 셋을 모아 돌려준다 — 무엇을 쓰고 하나도 안 틀렸으면 무엇이 되나?
- 직접 래퍼 타입을 만든다 — 무엇을 달아야 하나?
- 사슬을 손으로 걷는 코드를 쓴다 — 무엇을 빠뜨리기 쉬운가?

### 10. 다른 언어와 나란히 (연결)

- Rust 의 `source()` 와 `downcast_ref` 는 Go 의 무엇에 해당하나?
- Rust 에 없고 Go 에 있는 것 하나는?
- 자바의 `getCause()` 와 스택 트레이스는 Go 와 어떻게 다른가?

### 11. 다른 주제와 잇기 (연결)

- 「오류가 값이다」의 정본은 몇 번 주제인가 — 그쪽 어느 절이 이 주제를 부르나?
- 「사슬을 따라 반복하는 타입 단언」이라는 말은 몇 번 주제와 잇나?
- `go vet` 이 아무것도 안 잡는 대비 사례는 몇 번 주제인가?
- 오류 표면 설계의 정본은 몇 번 주제인가?
- `%w` 를 포함한 `fmt` 동사의 정본은 몇 번 주제인가?


## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

# go/syntax/24 — 오류 래핑 `%w` 와 `errors.Is`/`As`/`Join` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [`errors`](https://pkg.go.dev/errors) · [`fmt`](https://pkg.go.dev/fmt) 문서.
> 웹이 아니라 **이 툴체인에게 `go doc errors` 로 직접 물었고**,
> 판 경계는 **`$(go env GOROOT)/api/go1*.txt` 를 grep 해서** 떴다.\
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> ★★★ **버전 — 이 주제는 「언어 명세」가 아니라 「표준 라이브러리의 계약」이다.**
> `%w`·`Is`/`As`/`Unwrap` 이 **1.13**, `Unwrap() []error`·`Join`·`%w` 여러 개가 **1.20**,
> `AsType` 이 **1.26** 이다. ★ 그 경계를 **릴리스 노트가 아니라 `api/go1NN.txt` 에서** 뗐다((9)절).
> ★★ 그리고 **컴파일러가 그 경계를 안 지켜 준다** — `go.mod` 를 `go 1.19` 로 낮춰도
> `errors.Join` 이 그냥 컴파일된다((9)절). [22번 주제](../22-type-assertion-any-and-comparable/)의 언어 기능과 정반대다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★ **본체는 둘째 창이다** — 「`errors.Unwrap` 을 `nil` 까지 돌며 각 층의 `%T` 와 메시지를 찍는 창」.
사슬을 글자로 찍으면 `%w` 와 `%v` 의 차이도, `Join` 이 사슬이 아니라는 것도 한 블록에서 드러난다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | ★ **이 주제에는 거의 없다.** `error` 인터페이스 한 줄뿐이다 |
| **표준 라이브러리 계약** | `errors`·`fmt` 가 문서로 약속한 것 | `go doc errors` 의 본문 · 판 경계(`api/go1NN.txt`) |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 실행 출력(재실행 대조까지) |

★★★ **이 주제가 다른 주제와 갈리는 자리가 여기다.**
[21번](../21-nil-interface-vs-interface-holding-nil-pointer/)·[22번 주제](../22-type-assertion-any-and-comparable/)는
**명세가 규칙을 못 박았고** 판 경계도 컴파일러가 지킨다.
여기서는 **명세가 아무 말도 안 하고**(`Unwrap` 이라는 낱말이 명세에 없다)
**규칙 전부가 `errors` 패키지 문서의 약속**이다.
★ 그래서 (9)절의 「컴파일러가 안 지켜 준다」가 **이상한 일이 아니라 당연한 일**이다.

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | `errors.As` 패닉 블록의 **스택 프레임 힙 주소** | 실행마다 다르다 — ★ **이 문서의 유일한 흔들리는 칸**이다 |
| 안 흔들린다 | ★★★ 사슬의 **층수·차례·각 층의 `%T`** | 내가 쌓은 대로다 — 이 주제의 핵심 근거다 |
| 안 흔들린다 | `errors.Is`/`As`/`AsType` 의 참거짓 | 타입·값 구조가 정한다 |
| 안 흔들린다 | 패닉·`go vet` 의 **메시지 본문** · 종료 코드 | 라이브러리·도구가 정한 문장이다 |
| 안 흔들린다 | `errors.Join` 메시지의 **줄바꿈 개수** | 계약이다 |
| 안 흔들린다 | `api/go1NN.txt` 의 **줄 번호와 본문** | 이 툴체인 판에 든 파일이다 |
| 해당 없음 | 맵 순회 순서 | 이 주제는 맵을 순회해 찍지 않는다 |

★ 정규화 규칙은 **주소 하나**만 썼다. 나머지 블록은 재실행에서 한 글자도 같았다.

## 한눈에 — 쉽게 말하면

**`%w` 로 감싸면 겉 오류 안에 속 오류가 「링크」로 남고, `%v` 로 감싸면 글자만 남는다.**
그 링크를 따라가는 것이 `errors.Unwrap` 이고,
그 링크를 **끝까지 따라가며 찾아 주는 것**이 `errors.Is`/`As` 다.

| 비유 | 실체 |
|---|---|
| 포장지에 「안에 든 것」이 실제로 들어 있다 | **`%w`** — `Unwrap()` 이 속을 돌려준다 |
| 포장지에 「안에 든 것」이 **글자로만 적혀** 있다 | ★★★ **`%v`** — 메시지는 같고 `Unwrap()` 이 `nil` 이다 |
| 상자를 계속 열어 맨 안을 본다 | **`errors.Unwrap` 을 `nil` 까지 돌기** |
| 「이 상자들 중에 그 물건 있어?」 | **`errors.Is`** — **신원**을 묻는다 |
| 「그 물건 꺼내 줘」 | **`errors.As`** — **값**을 꺼낸다 |
| 상자 하나에 물건 여럿을 넣는다 | ★★ **`errors.Join`·`%w` 여러 개** — 사슬이 아니라 **트리**가 된다 |
| 상자 안에 상자가 여럿이면 줄이 안 선다 | ★★★ **`errors.Unwrap` 이 `nil` 을 준다** — 사슬 함수로는 못 본다 |

```text
   ★★★ %w 와 %v — 메시지는 같고 안이 다르다

   fmt.Errorf("겉: %w", base)          fmt.Errorf("겉: %v", base)
   ┌──────────────────────┐            ┌──────────────────────┐
   │ *fmt.wrapError       │            │ *errors.errorString  │
   │  msg  "겉: 권한 없음"│            │  msg  "겉: 권한 없음"│
   │  err  ──────────┐    │            │  (링크가 없다)       │
   └─────────────────│────┘            └──────────────────────┘
                     ▼
              base(권한 없음)

     Error()      둘이 한 글자도 같다
     Unwrap()     base           nil
     Is(base)     true           ★ false
```

```text
   ★★★ 래핑 사슬 — Unwrap 을 nil 까지 돈다 ((2)절의 실측)

   [0] *fmt.wrapError    "서버 시작: 기동 준비: 설정 port: open …"
        │ Unwrap()
   [1] *fmt.wrapError    "기동 준비: 설정 port: open …"
        │ Unwrap()
   [2] *main.ConfigErr   "설정 port: open …"        ← 내가 만든 층
        │ Unwrap()
   [3] *fs.PathError     "open 없는파일.conf: …"    ← os 가 만든 층
        │ Unwrap()
   [4] syscall.Errno     "no such file or directory" ← OS 가 준 번호
        │ Unwrap()
       nil                                          ← 여기서 멈춘다

   ★ 층 하나가 Unwrap 을 안 달면 그 위로 못 간다((2)절의 마지막 덩어리).
```

```text
   ★★ Join 이 만드는 것은 트리다 ((7)절의 실측)

   errors.Join(errors.Join(A, B), C)

   *errors.joinError (가지 2개)
     ├─ *errors.joinError (가지 2개)
     │    ├─ A
     │    └─ B
     └─ C

   errors.Unwrap(그것)  ->  nil      ← Unwrap() error 가 없다
   errors.Is(그것, B)   ->  true     ← Is 는 트리를 다 돈다
```

> **래핑(wrapping)** — 겉 오류가 `Unwrap()` 으로 속 오류를 돌려주는 것.\
> `go doc errors` 가 「An error e **wraps** another error if e's type has one of the methods
> `Unwrap() error` / `Unwrap() []error`」라 적는다.

> **`%w`** — `fmt.Errorf` 에서 그 인자를 **감싸라**는 동사(1.13). `%v` 와 **메시지가 같다.**

> **센티넬 대 커스텀 타입** — `Is` 로 물을 것과 `As` 로 꺼낼 것.\
> 설계 논의의 정본은 [목록의 **25번 주제**](../25-sentinel-errors-vs-custom-error-types/)다.

> **트리(tree)** — `go doc errors` 의 낱말. 「Successive unwrapping of an error creates a **tree**.\
> The Is and As functions inspect an error's tree … (pre-order, depth-first traversal).」

- [23번 주제](../23-error-interface-and-errors-as-values/)가 **이 주제의 직접 선행**이다. 거기서 결론난 것 셋 —
  ① `error` 는 메서드 하나짜리 인터페이스다 ② `errors.New` 는 매번 새 값이라 `==` 가 포인터 비교다
  ③ **한 겹만 감싸도 `==` 가 깨진다.** ★ **③이 이 주제가 존재하는 이유**다.
- Rust 와 다른 점 — ★★ **구조가 거의 같다.** Rust 의 `source()` 가 Go 의 `Unwrap()` 이고
  `downcast_ref` 가 `errors.As` 다. 갈리는 것은 **Rust 가 `match` 로 완전성 검사를 얹을 수 있다**는 것.
  (Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **24번**.)
  ★ 그리고 **Go 에는 `Join` 이 있고 Rust std 에는 그 짝이 없다.**
- 자바와 다른 점 — 자바의 `getCause()` 가 `Unwrap()` 이고,
  ★ **스택 트레이스가 언어에 내장**돼 있다([`../../../java/syntax/25-exceptions/`](../../../java/syntax/25-exceptions/)).
  Go 의 오류 값에는 **스택이 안 들어 있다** — 그래서 문맥 문구를 손으로 붙인다([23번 주제](../23-error-interface-and-errors-as-values/) (5)절).

## 이 주제가 답하려는 질문

1. **`%w` 와 `%v` 가 무엇이 다른가** — 메시지가 같은데 무엇이 갈리나.
2. **사슬이 몇 층이고 각 층이 무엇인가** — `Unwrap` 을 돌면 무엇이 나오나.
3. **`Is` 와 `As` 를 언제 고르나** — 그리고 `Join` 이 만드는 것은 사슬인가 트리인가.

★ **오류 표면 설계**(무엇을 공개할까)의 정본은 [목록의 **25번 주제**](../25-sentinel-errors-vs-custom-error-types/)다.
★ **`error` 가 값이라는 것 자체**는 [23번 주제](../23-error-interface-and-errors-as-values/)다.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| **`%T` 를 찍기** | `%w` 판이 `*fmt.wrapError` 라는 것 | [23번 주제](../23-error-interface-and-errors-as-values/)에서 쓰던 창 |
| ★★★ **`Unwrap` 을 `nil` 까지 돌며 `%T` 와 메시지를 찍기** | 사슬의 **층수와 차례** | ★ 본체 창 |
| ★★ **각 층에 `Is` 메서드를 달아 로그를 찍게 하기** | `Is` 가 **어느 순서로 무엇에게 묻나** | ★ 이 주제의 고유 창 |
| ★★ **`Unwrap() []error` 를 직접 단언해 물어보기** | `errors.Unwrap` 이 `nil` 을 주는 이유 | [22번 주제](../22-type-assertion-any-and-comparable/)의 comma-ok |
| ★ **트리를 재귀로 걸어 찍기** | `Join` 이 만드는 것이 **트리**라는 것 | ★ 이 주제의 고유 창 |
| ★★ **`go vet` 을 던지기** | `errors.As` 의 인자 실수를 **도구가 잡는다** | [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/)에서 쓰던 창 |
| ★★★ **부적용 — `go.mod` 의 `-lang` 게이트** | **잴 것이 없다.** 표준 라이브러리 API 라 언어 판 게이트가 **안 걸린다**((9)절) | — |
| **부적용 — 벤치마크** | 안 쟀다. 「`Is` 가 사슬을 도니 느리다」 같은 말을 이 문서는 하지 않는다 | — |

★★★ **「부적용 — `-lang` 게이트」 칸이 이 주제의 성격이다.**
[22번 주제](../22-type-assertion-any-and-comparable/) (7)절에서는 `go.mod` 의 `go 1.19` 한 줄이
**`requires go1.20 or later` 라는 문장을 냈다.**
여기서 같은 것을 하면 **아무 말도 안 나온다** — 언어가 아니라 **패키지**이기 때문이다.

★★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.**
「`errors.Join` 이 언제부터인가」를 **컴파일러에게 물을 수 없어**
**`$(go env GOROOT)/api/go1*.txt` 를 grep 해서** 물었다((9)절).
★ 바꾼 창의 한계 — 그 파일은 **API 가 추가된 판**만 말한다.
**동작이 바뀐 판**(예: `Is` 가 `Unwrap() []error` 를 보게 된 것)은 거기 안 적혀 있다.

### (1) ★★★ `%w` 와 `%v` — 메시지가 같고 `Is` 가 갈린다

**언제 쓰나** — `fmt.Errorf` 로 오류를 감쌀 때.

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

그림 해설 (한 단계씩):

- ★★★ **메시지가 한 글자도 같다**(`true`). `%q` 로 찍어도 같다.
- ★★★ **그런데 `%T` 가 갈린다** — **`*fmt.wrapError`** 대 **`*errors.errorString`**.
  `errors.Unwrap` 이 **속 오류** 대 **`<nil>`** 이다.
- ★★ **그래서 `errors.Is` 의 답이 `true` 대 `false`** 로 갈리고, `errors.As` 도 마찬가지다.
  ★ `As` 쪽은 더 나쁘다 — **대상 변수가 `nil` 인 채로 남는다.**
  그것을 모르고 쓰면 [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/)의 함정으로 이어진다.
- ★★★ **마지막 덩어리가 이 절의 결론이다** — **로그 두 줄이 한 글자도 같다.**
  **`%v` 로 감싼 사고는 로그를 아무리 봐도 안 보인다.**
  ★ 보려면 **`%T` 를 같이 찍거나** `errors.Unwrap` 을 불러 봐야 한다.

비용 — `%w` 는 포인터 한 칸을 더 들고 다닌다. **이 문서는 재지 않았다.**

### (2) ★★★ 래핑 사슬을 글자로 — `Unwrap` 을 `nil` 까지

**언제 쓰나** — 「이 오류가 어디서 왔나」를 볼 때.

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

그림 해설 (한 단계씩):

- ★★★ **사슬이 다섯 층**이고 그 다음이 `nil` 이다.
  내가 쌓은 것은 셋인데(`ConfigErr` 과 `fmt.Errorf` 둘)
  **`os` 가 이미 두 층을 쌓아 놨다** — `*fs.PathError` 와 `syscall.Errno`.
- ★★ **맨 위 한 줄만 찍으면** 네 층의 메시지가 **이어 붙어** 나온다.
  각 층이 「내 문구 + 속 오류의 문구」로 만들어졌기 때문이다.
  ★ **그래서 로그 한 줄이 길어지는 것이고**, 그 대가로 사슬을 안 걸어도 읽을 수 있다.
- ★★★ **`errors.Is(top, os.ErrNotExist)` 가 `true`** 인데
  **사슬 어디에도 `os.ErrNotExist` 가 없다.**
  ★ `syscall.Errno` 가 **자기 `Is` 메서드**를 갖고 있어서다((5)절이 그 구조를 던진다).
  **표준 라이브러리가 커스텀 `Is` 를 쓰는 실제 자리**다.
- ★★ **`errors.As` 는 사슬 어느 층이든 꺼낸다** — `*fs.PathError`(Op·Path)도,
  내가 만든 `*ConfigErr`(Key)도 나온다.
- ★★★ **마지막 덩어리가 계약의 핵심이다** — **`Unwrap()` 을 안 달면 사슬이 거기서 끊긴다.**
  `NoUnwrap` 은 메시지에는 속 오류가 들어 있는데 **사슬 길이가 1** 이고
  `errors.Is` 가 **`false`** 다. ★ **메시지가 이어져 있다고 사슬이 이어진 것이 아니다.**

비용 — 층마다 포인터 한 칸. **이 문서는 재지 않았다.**

### (3) ★★ `Is` 와 `As` 를 고르는 기준

**언제 쓰나** — 호출자가 오류를 보고 무언가를 할 때.

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

그림 해설 (한 단계씩):

- ★★★ **기준 한 줄** 「**값이 필요하면 `As`, 신원만 필요하면 `Is`**」다.
  `ErrRetryLater` 는 「이것이냐」만 알면 되고, `QuotaErr` 는 **`Used - Limit` 이라는 값**이 필요하다.
- ★ **`Is` 는 센티넬에도 쓰고 표준 라이브러리 센티넬에도 쓴다** —
  `fs.ErrNotExist` 로 물으니 `os.Open` 의 오류가 잡혔다((2)절과 같은 구조다).
- ★★ **`As` 는 인터페이스로도 받는다** — `&interface{ Timeout() bool }` 에 넣으니 **`true`** 다.
  ★ `*fs.PathError` 가 그 메서드를 갖고 있기 때문이다.
  **구체 타입을 몰라도 「타임아웃이냐」를 물을 수 있다.**
- ★★ **마지막 덩어리가 계약이다** — **`As` 는 못 찾으면 대상을 안 건드린다.**
  미리 넣어 둔 값이 그대로 남는다. ★ 그래서 **`ok` 를 안 보고 대상만 보면 틀린다.**

비용 — 사슬 길이만큼 비교. **이 문서는 재지 않았다.**

### (4) ★★ `As` 의 둘째 인자는 포인터의 포인터다

**언제 쓰나** — `errors.As` 를 쓸 때. **가장 흔한 실수 자리다.**

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

그림 해설 (한 단계씩):

- ★★★ **대상 타입이 `*QuotaErr` 이면 넘기는 것은 `&q`, 즉 `**QuotaErr`** 이다.
  「포인터의 포인터」라는 말이 그 뜻이다.
- ★ **값 타입이면 한 겹이면 된다** — `ValErr` 이면 `&v`(`*ValErr`)다.
  ★★ **「무조건 두 겹」이 아니다** — **오류 타입 자체가 포인터인가**가 정한다.
- ★★★ **`&` 를 빠뜨리면 패닉**이다 —
  **`panic: errors: target must be a non-nil pointer`**, 종료 코드 2.
  스택에 **`errors.As(...)` 프레임과 `errors/wrap.go:112`** 가 찍힌다.
- ★★ **그런데 이 실수는 `go vet` 이 잡는다.**

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

- ★★★ **탐침 4개 중 3개가 잡혔다** — `&` 누락 · `error` 를 구현 안 하는 타입 · `nil`.
  네 번째(제대로 된 꼴)는 조용하다. **종료 코드 1.**
- ★★★ **[21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/) (6)절과 정확히 대비된다.**
  거기서는 **탐침 8개 중 0개**였고 여기서는 **4개 중 3개**다.
  ★ **같은 도구인데 갈린다.** 이유는 **검사 가능성**이다 —
  `errors.As` 의 둘째 인자는 **그 자리에서 타입만 보면** 옳고 그름이 정해지는데,
  `return p` 가 함정인지 아닌지는 **`p` 가 실행 시점에 `nil` 인가**에 달려 있다.


```text
   ★★ As 의 둘째 인자 — 겹수는 「오류 타입이 포인터인가」가 정한다

   오류 타입이 *QuotaErr 이면        오류 타입이 ValErr(값)이면

     var q *QuotaErr                   var v ValErr
     errors.As(err, &q)                errors.As(err, &v)
                     ▲                                ▲
                  **QuotaErr                       *ValErr
                  (두 겹)                          (한 겹)

   & 를 빠뜨리면 —   런타임 패닉 「errors: target must be a non-nil pointer」
   그 자리를 go vet 이 잡는다(탐침 4개 중 3개).
   1.26부터는 errors.AsType[*QuotaErr](err) 로 그 자리를 아예 없앤다((8)절).
```

비용 — 없다.

### (5) ★★ `Is` 는 무엇에게 어떤 순서로 묻나 · 커스텀 `Is`/`As`

**언제 쓰나** — 「같음」을 내가 정의하고 싶을 때.

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

그림 해설 (한 단계씩):

- ★★★ **첫 덩어리가 사슬을 도는 순서를 보인다** — `top` → `mid` → `bottom` 차례로
  **각 층의 `Is` 메서드가 불린다.** 셋 다 `false` 를 돌려줬는데도 결과는 `true` 다.
  ★ **`errors.Is` 는 층마다 두 가지를 한다** — ① `== target` 인가 ② 그 층에 `Is` 메서드가 있으면 물어본다.
  ①이 맨 아래에서 맞았다.
- ★★ **찾는 것이 없으면 끝까지 간다** — 셋에게 다 묻고 `false` 다.
- ★★★ **커스텀 `Is` 로 「같음」을 새로 정의한다** —
  `&StatusErr{404}` 는 **다른 포인터**인데 `errors.Is` 가 **`true`** 다.
  같은 자리를 `==` 로 견주면 **`false`** 다.
  ★ 「HTTP 상태코드가 같으면 같은 오류」라는 규칙을 **타입이 스스로 정한 것**이다.
- ★★ **커스텀 `As` 는 더 세다** — `Coded` 가 `*StatusErr` 을 **만들어서** 넘겼다.
  **사슬에 `*StatusErr` 이 하나도 없는데 `errors.As` 가 `true`** 다.
  ★ (2)절의 `syscall.Errno` 가 표준 라이브러리에서 같은 일을 한다.

비용 — 층마다 메서드 호출 한 번. **이 문서는 재지 않았다.**

```text
   ★★ errors.Is 가 한 층에서 하는 일은 둘이다

   for 각 층 (pre-order, depth-first) :
       ① 이 층 == target 인가          ← 값이 같은가
       ② 이 층에 Is 메서드가 있으면 물어본다   ← 「같음」을 타입이 다시 정의한다
       그 다음 아래 층으로

   실측(로그) —  top → mid → bottom 순서로 ② 가 불렸고 셋 다 false
                 그런데 맨 아래에서 ① 이 맞아 결과는 true

   errors.As 도 같은 순서다. 다만 ① 이 「타입이 맞나」이고
   ② 가 As 메서드다 — 사슬에 없는 타입도 만들어 내줄 수 있다.
```

### (6) ★★★ `%w` 를 여러 개 쓰면 — 사슬이 끊긴다

**언제 쓰나** — 한 번에 두 가지가 틀렸을 때. **1.20부터다.**

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

그림 해설 (한 단계씩):

- **`%T` 가 `*fmt.wrapErrors`**(복수형이다)이고 **`Is` 가 둘 다 찾는다.**
- ★★★ **그런데 `errors.Unwrap(multi)` 이 `<nil>`** 이다.
  **`errors.Unwrap` 은 `Unwrap() error` 만 보고**, 여기 있는 것은 **`Unwrap() []error`** 다.
  ★ 직접 단언해 물으면 **길이 2** 가 나오고 `Unwrap() error` 는 **없다**고 답한다.
- ★★★ **그래서 사슬을 도는 코드가 여기서 멈춘다** — 「사슬로 본 길이 1층」인데 **안에 둘이 들어 있다.**
  ★ **(2)절의 반복문을 그대로 쓰면 못 본다.** 그것이 이 절의 경고다.
- ★★ **`errors.Is` 는 그 둘을 다 본다** — 더 깊이 중첩해도(`deep`) `ErrA` 와 `ErrC` 를 찾는다.
  `go doc errors` 가 그 동작을 「**tree … pre-order, depth-first traversal**」이라 적는다.
- ★★★ **정리 — `Is`/`As` 는 트리를 돌고 `errors.Unwrap` 은 사슬만 돈다.**
  둘이 보는 것이 다르다.

비용 — 없다.

### (7) ★★★ `errors.Join` — 트리를 만들고 줄바꿈으로 잇는다

**언제 쓰나** — 검증처럼 **여러 실패를 모아** 한 번에 돌려줄 때. **1.20부터다.**

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

그림 해설 (한 단계씩):

- ★★★ **메시지가 줄바꿈으로 이어진다** — 세 오류면 **줄바꿈 2개**다.
  `%q` 로 보면 `"이름이 비었다\n메일이 형식에 안 맞는다\n나이가 음수다"` 다.
  ★ **`", "` 가 아니라 `"\n"` 이다** — 로그 한 줄로 찍으면 **줄이 늘어난다.**
- **셋 다 `errors.Is` 로 찾아진다.**
- ★★ **`nil` 을 섞으면 그 자리는 빠진다** — `Join(nil, A, nil, C, nil)` 의 길이가 **2** 다.
  ★★★ **전부 `nil` 이거나 인자가 없으면 `Join` 이 `nil` 을 돌려준다** —
  그래서 `return errors.Join(errs...)` 한 줄로 「**하나도 안 틀렸으면 `nil`**」이 된다.
  ★ [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/)의 함정을 **`Join` 이 스스로 피해 준다.**
- ★★★ **`Join` 이 만드는 것은 트리다** — `errors.Unwrap(outer)` 이 **`<nil>`** 이고,
  손으로 걸으면 **가지 2개짜리 마디 안에 가지 2개짜리 마디**가 들어 있다.
  ★ (6)절과 같은 구조다 — `Unwrap() []error` 를 가진 마디다.
- ★★ **`Join` 한 값에 `%w` 를 씌우면 두 꼴이 섞인다** —
  겉은 `*fmt.wrapError`(사슬), 그 속이 `*errors.joinError`(트리)다.
  `errors.Unwrap` 이 **한 칸은 가고 거기서 멈춘다.** `Is` 는 끝까지 찾는다.
  ★ 메시지도 **한 줄 + 줄바꿈**으로 섞인다.

비용 — 오류 개수만큼 슬라이스. **이 문서는 재지 않았다.**

### (8) ★ `errors.AsType` — 1.26의 제네릭 판

**언제 쓰나** — `errors.As` 를 쓰는 자리에서. **1.26부터다.**

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

그림 해설 (한 단계씩):

- ★★ **`errors.As` 는 대상 변수를 미리 만들어 주소를 넘기고**,
  **`errors.AsType[T]` 는 타입 인자로 주고 값을 돌려받는다.**
  ★ (4)절의 「포인터의 포인터」 실수가 **원리상 생길 수 없다** — 넘길 포인터가 없다.
- **못 찾으면 제로값과 `false`** 다 — [22번 주제](../22-type-assertion-any-and-comparable/)의 comma-ok 와 같은 모양이다.
- ★★★ **마지막 두 줄이 이 절의 결론이다** — `err.(*fs.PathError)` 는 **`false`**(맨 위 층만 본다)이고
  `errors.AsType[*fs.PathError](err)` 는 **`true`**(트리를 다 본다)다.
  ★ **모양은 같고 보는 범위가 다르다.** `errors.As`/`AsType` 은
  「**사슬을 따라 반복하는 타입 단언**」이라고 읽으면 맞는다.

비용 — `As` 와 같다. **이 문서는 재지 않았다.**

### (9) ★★★ 판 경계 — 컴파일러가 안 지켜 준다

**언제 쓰나** — 「이 함수 몇 부터 쓸 수 있나」를 확인할 때.

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

그림 해설 (한 단계씩):

- ★★★ **`$(go env GOROOT)/api/go1NN.txt` 가 판 경계의 정본**이다. 표로 옮기면 이렇다.

| API | 언제부터 | 어디서 뗐나 |
|---|---|---|
| `errors.New` | **1.0** | `go1.txt:2469` |
| `errors.Is` · `errors.As` · `errors.Unwrap` | **1.13** | `go1.13.txt:46\~48` |
| `errors.Join` | **1.20** | `go1.20.txt:237` |
| `errors.AsType[E error]` | **1.26** | `go1.26.txt:129` |
| `%w` 한 개 | **1.13** | `fmt` 동사라 이 파일에 안 나온다 — `go doc fmt` 쪽 |
| `%w` 여러 개 · `Unwrap() []error` | **1.20** | 〃 (`Join` 과 같은 판) |

  ★ **`%w` 는 `api/*.txt` 에 안 나온다** — 그것은 **함수가 아니라 포맷 동사**라 API 목록의 대상이 아니다.
  **이 창의 한계**다.
- ★★★ **그런데 컴파일러가 그 경계를 안 지켜 준다.**

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

- ★★★ **`go.mod` 를 `go 1.19` 로 낮춰도 `errors.Join` 과 `%w` 두 개가 그냥 컴파일되고 돌아간다.**
  `go vet` 도 **출력 0줄에 종료 코드 0** 이다.
  ★★ [22번 주제](../22-type-assertion-any-and-comparable/) (7)절과 **정반대**다 —
  거기서는 `go.mod` 의 같은 한 줄이 `requires go1.20 or later` 를 냈다.
- ★★★ **이유는 이 주제의 성격 그 자체다** — `comparable` 은 **언어 기능**이라
  컴파일러가 `-lang` 으로 막고, `errors.Join` 은 **패키지 함수**라 막을 문법 규칙이 없다.
  **링크된 표준 라이브러리에 그 함수가 있으면 그냥 불린다.**
- ★ **그래서 「몇 부터 되나」는 문서와 `api/*.txt` 로만 안다.**
  ★★ 이것이 「**24는 표준 라이브러리의 계약이지 언어 명세가 아니다**」의 실측이다.
- `go doc errors` 가 그 계약을 한 자리에 적어 둔다.

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

  ★★ 「**An error e wraps another error if e's type has one of the methods**」로 시작한다 —
  **메서드 이름 두 개가 곧 계약**이다.
  ★★★ 그리고 「**Successive unwrapping of an error creates a tree.**」라고 **트리**라는 낱말을 쓴다.
  「사슬」이라고 적혀 있지 않다.

비용 — 없다.

## 문법 — 형태와 규칙

### 형태

```go
// t24form.go
package main

import (
	"errors"
	"fmt"
)

var ErrGone = errors.New("사라짐") // (1) 센티넬

type SizeErr struct{ N int } // (2) 값을 들고 다니는 오류

func (e *SizeErr) Error() string { return fmt.Sprintf("크기 %d", e.N) }

type Wrapper struct{ Err error } // (3) 직접 만든 래퍼

func (w *Wrapper) Error() string { return "겉: " + w.Err.Error() }
func (w *Wrapper) Unwrap() error { return w.Err } // 이 메서드가 사슬을 잇는다

func main() {
	a := fmt.Errorf("문맥: %w", ErrGone)               // (4) %w 로 감싼다
	b := fmt.Errorf("문맥: %v", ErrGone)               // (5) %v 는 안 잇는다
	c := fmt.Errorf("%w / %w", ErrGone, &SizeErr{3}) // (6) %w 여러 개 (1.20)
	d := errors.Join(ErrGone, &SizeErr{3})           // (7) Join (1.20)
	e := &Wrapper{Err: a}                            // (8) 직접 만든 래퍼

	fmt.Println("(4)", errors.Is(a, ErrGone), errors.Unwrap(a) == ErrGone)
	fmt.Println("(5)", errors.Is(b, ErrGone), errors.Unwrap(b))
	fmt.Println("(6)", errors.Is(c, ErrGone), errors.Unwrap(c))
	fmt.Println("(7)", errors.Is(d, ErrGone), errors.Unwrap(d))
	fmt.Println("(8)", errors.Is(e, ErrGone))

	var s *SizeErr
	fmt.Println("(9)", errors.As(c, &s), s.N) // (9) As 로 값을 꺼낸다

	sz, ok := errors.AsType[*SizeErr](d) // (10) AsType (1.26)
	fmt.Println("(10)", ok, sz.N)
}
```

```text
===== 명령: go build -trimpath -o prog . && ./prog =====
(4) true true
(5) false <nil>
(6) true <nil>
(7) true <nil>
(8) true
(9) true 3
(10) true 3
(exit 0)
```

규칙 불릿.

- **`%w` 는 감싸고 `%v` 는 안 감싼다.** 메시지는 같다.
- **직접 만든 타입은 `Unwrap() error` 를 달아야** 사슬에 낀다.
- **`errors.Unwrap` 은 `Unwrap() error` 만** 본다. `Unwrap() []error` 에는 `nil` 을 준다.
- **`errors.Is`/`As` 는 트리를 돈다**(pre-order, depth-first).
- **`As` 의 둘째 인자는** 「**대상 타입의 포인터**」다. 대상이 `*T` 면 `**T` 가 된다.
- **`As` 는 못 찾으면 대상을 안 건드린다.** `ok` 를 봐야 한다.
- **커스텀 `Is`/`As` 메서드**로 「같음」과 「꺼내기」를 새로 정의할 수 있다.
- **`%w` 를 여러 개 쓰면**(1.20) `Unwrap() []error` 가 된다.
- **`errors.Join`**(1.20)은 `nil` 을 빼고 묶고, **전부 `nil` 이면 `nil`** 을 준다. 메시지는 **줄바꿈**으로 잇는다.
- **`errors.AsType[E]`**(1.26)는 `As` 의 제네릭 판이다. comma-ok 모양으로 돌려받는다.

### 금지 사례 — 런타임과 도구가 거부하는 것

★★ **컴파일러가 거부하는 것이 없다.** 이 주제의 규칙은 전부 **패키지의 계약**이라
컴파일 타임에 검사할 문법 규칙이 아니다.

| 무엇 | 누가 | 문장 |
|---|---|---|
| `errors.As` 에 포인터가 아닌 것 | **런타임** | `panic: errors: target must be a non-nil pointer` |
| 〃 | ★ **`go vet`** | `second argument to errors.As must be a non-nil pointer to either a type that implements error, or to any interface type` |
| `errors.As` 에 `error` 를 구현 안 하는 타입 | ★ **`go vet`** | 같은 문장 |
| `errors.As` 에 `nil` | ★ **`go vet`** | 같은 문장 |
| `%v` 로 감쌌는데 `Is` 로 찾기 | ★★★ **아무도** — 조용히 `false` 다 | — |
| `Unwrap` 을 안 달고 감싸기 | ★★★ **아무도** — 조용히 사슬이 끊긴다 | — |
| 1.19 에서 `errors.Join` 쓰기 | ★★ **아무도** — 그냥 컴파일된다((9)절) | — |

## 어디서 틀리나

### 1. ★★★ 「`%v` 로 감싸도 되겠지」

- (1)절 실측 — **메시지는 한 글자도 같은데** `errors.Is` 가 **`false`** 다.
  로그로는 안 보인다.
- 고치는 법 — **감쌀 때는 `%w`.** ★ 의심되면 `%T` 를 찍어 `*fmt.wrapError` 인지 본다.

### 2. ★★★ 「메시지가 이어져 있으니 사슬도 이어졌겠지」

- (2)절 실측 — `NoUnwrap` 은 메시지에 속 오류가 들어 있는데 **사슬 길이가 1** 이고
  `errors.Is` 가 **`false`** 다.
- 고치는 법 — 직접 만든 래퍼에는 **`Unwrap() error` 를 단다.**

### 3. ★★★ 「`errors.Unwrap` 으로 다 돌면 전부 보이겠지」

- (6)·(7)절 실측 — `%w` 여러 개와 `Join` 은 **`Unwrap() []error`** 라
  `errors.Unwrap` 이 **`nil`** 을 준다. 사슬 반복문이 **1층에서 멈춘다.**
- 고치는 법 — 트리를 걸으려면 **두 인터페이스를 다 단언**한다((7)절의 `walk`).
  아니면 **`Is`/`As` 에 맡긴다** — 그것들은 트리를 돈다.

### 4. ★★ 「`As` 의 인자는 그냥 변수 주소면 되겠지」

- (4)절 실측 — `&` 를 빠뜨리면 **`panic: errors: target must be a non-nil pointer`**, 종료 코드 2.
- 고치는 법 — **대상 타입의 포인터**를 넘긴다(`*T` 면 `**T`).
  ★ **CI 에 `go vet` 을 넣으면 잡힌다**(탐침 4개 중 3개).
  ★ 1.26 이상이면 **`errors.AsType[T]`** 로 그 실수를 없앤다((8)절).

### 5. ★★ 「`As` 가 `false` 여도 대상에 뭔가 들어 있겠지」

- (3)절 실측 — **못 찾으면 대상을 안 건드린다.** 미리 넣은 값이 그대로 남는다.
- 고치는 법 — **`ok` 를 본다.** 대상만 보고 판단하지 않는다.

### 6. ★★ 「센티넬은 `==` 로 견주면 되겠지」

- [23번 주제](../23-error-interface-and-errors-as-values/) (2)절 실측 — 한 겹만 감싸도 `==` 가 **`false`** 가 된다.
- 고치는 법 — **`errors.Is`.** 그것이 이 주제가 존재하는 이유다.

### 7. ★★ 「`Join` 도 사슬이겠지」

- (7)절 실측 — `errors.Unwrap(outer)` 이 **`<nil>`** 이고 구조가 **트리**다.
  ★ `go doc errors` 도 「tree」라고 적는다.
- 고치는 법 — 「사슬」이라는 낱말을 버린다. **`Is`/`As` 는 트리를 돈다.**

### 8. ★★ 「`Join` 메시지가 한 줄이겠지」

- (7)절 실측 — **줄바꿈으로 이어진다.** 세 오류면 줄바꿈 2개다.
- 고치는 법 — 로그에 넣기 전에 **한 줄로 접을지** 정한다.
  ★ `Join` 한 값에 `%w` 를 씌워도 **줄바꿈은 그대로 남는다**((7)절 마지막).

### 9. ★★ 「`go.mod` 를 낮추면 못 쓰는 API 가 걸리겠지」

- (9)절 실측 — `go 1.19` 에서 `errors.Join` 이 **그냥 컴파일되고 `go vet` 도 0줄**이다.
- 고치는 법 — **`api/go1NN.txt` 나 문서로 확인한다.**
  ★ 언어 기능과 달리 표준 라이브러리 API 는 **툴체인이 안 막아 준다.**

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| **`error` 가 메서드 하나짜리 인터페이스인 것** | **명세 보장** | [23번 주제](../23-error-interface-and-errors-as-values/) |
| ★★★ **`Unwrap` 이라는 규약** | **표준 라이브러리 계약** | 명세에 그 낱말이 없다. `go doc errors` 가 정본 |
| **`%w` 가 감싸는 것** | **표준 라이브러리 계약(1.13)** | `fmt` 문서 |
| **`Is`/`As` 가 트리를 pre-order DFS 로 도는 것** | **표준 라이브러리 계약** | `go doc errors` 의 그 문장 |
| **`As` 가 못 찾으면 대상을 안 건드리는 것** | **표준 라이브러리 계약** | (3)절 실측 |
| **커스텀 `Is`/`As` 메서드가 불리는 것** | **표준 라이브러리 계약** | (5)절 실측 |
| **`Join` 이 `nil` 을 빼고 전부 `nil` 이면 `nil` 인 것** | **표준 라이브러리 계약(1.20)** | (7)절 실측 |
| **`Join` 메시지가 줄바꿈으로 이어지는 것** | **표준 라이브러리 계약(1.20)** | 〃 |
| **`Unwrap() []error` 를 `errors.Unwrap` 이 안 보는 것** | **표준 라이브러리 계약** | (6)절 실측 · `go doc` 이 두 메서드를 따로 적는다 |
| **`AsType` 이 있는 것** | **표준 라이브러리 계약(1.26)** | `api/go1.26.txt:129` |
| **`*fmt.wrapError`·`*fmt.wrapErrors`·`*errors.joinError` 라는 이름** | ★★ **구현 내부** | 기대지 마라 |
| **`syscall.Errno` 가 `Is` 를 갖고 있는 것** | **표준 라이브러리 계약** | (2)절 실측 — `os.ErrNotExist` 가 그래서 잡힌다 |
| 패닉·`go vet` 의 **문구 자체** | **툴체인 판(go1.27.1)** | 판이 오르면 달라질 수 있다 |
| `errors/wrap.go` 의 **줄 번호** | **이 툴체인 판** | 〃 |
| ★★★ **`-lang` 게이트가 이 API 들을 안 막는 것** | **도구(구현)** | (9)절 실측. 언어 기능과 갈리는 자리 |
| `api/*.txt` 가 **`%w` 를 안 담는 것** | **도구의 성질** | 포맷 동사는 API 목록의 대상이 아니다 |
| `Is`/`As` 의 **비용** | ★ **안 쟀다** | 벤치마크가 없다(목록의 **50번 주제**) |

★ 이 주제의 결론은 「**규칙이 전부 패키지 문서의 약속이고, 어기는 것을 컴파일러가 안 막는다**」이다.
★★ 다만 **`errors.As` 의 인자 실수 하나**는 `go vet` 이 막아 준다 — 유일한 예외다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 문맥을 붙여 올린다 | **`fmt.Errorf("어디서: %w", err)`** | `%v` 면 사슬이 안 생긴다 |
| 문맥을 안 붙이고 그대로 올린다 | **`return err`** | 층을 늘릴 이유가 없다 |
| 호출자가 **신원**만 알면 된다 | **`errors.Is`** | 값이 필요 없다 |
| 호출자가 **값**을 써야 한다 | **`errors.As`**(1.26+면 **`AsType`**) | 필드를 읽는다 |
| 「타임아웃이냐」처럼 **성질**을 묻는다 | **`As` + 인터페이스 타입** | 구체 타입을 몰라도 된다 |
| 여러 실패를 모아 돌려준다 | **`errors.Join`** | `nil` 처리가 공짜다 |
| 「같음」을 내가 정의한다 | **`Is` 메서드** | 상태코드·오류 코드 같은 것 |
| 다른 타입으로 내준다 | **`As` 메서드** | 내부 타입을 감추면서 꺼내게 한다 |
| 직접 래퍼 타입을 만든다 | **`Unwrap() error` 를 단다** | 안 달면 사슬이 끊긴다 |
| 사슬을 손으로 걷는다 | **`Unwrap() []error` 도 같이 단언** | 안 하면 `Join` 에서 멈춘다 |
| 오류 표면을 설계한다 | [목록의 **25번 주제**](../25-sentinel-errors-vs-custom-error-types/) | 무엇을 공개할지가 거기 |

판단 규칙 두 줄.

- ★★★ **감쌀 때는 `%w`, 물을 때는 `Is`/`As`.** 그 둘이 짝이고 한쪽만 하면 조용히 안 된다.
- ★★ **「사슬」이라고 생각하지 말고 「트리」라고 생각해라.** `Join` 과 `%w` 여러 개가 있다.

## 핵심 문장

- ★★★ **`%w` 와 `%v` 는 메시지가 한 글자도 같고 안이 다르다** —
  `*fmt.wrapError` 대 `*errors.errorString`, `Unwrap()` 이 속 오류 대 `nil`,
  `errors.Is` 가 `true` 대 `false`. ★ **로그를 아무리 봐도 안 보인다.**
- ★★★ **사슬을 `nil` 까지 돌면 층이 글자가 된다** — 실측에서 **다섯 층**이었고
  내가 쌓은 것은 셋인데 **`os` 가 이미 두 층**(`*fs.PathError`·`syscall.Errno`)을 쌓아 놨다.
- ★★★ **메시지가 이어져 있다고 사슬이 이어진 것이 아니다.**
  `Unwrap()` 을 안 단 래퍼는 메시지에는 속 오류가 있는데 **사슬 길이가 1** 이고 `Is` 가 `false` 다.
- ★★ **`Is` 는 신원, `As` 는 값**이다. `As` 는 **인터페이스로도** 받아 「타임아웃이냐」를 물을 수 있고,
  **못 찾으면 대상을 안 건드린다.**
- ★★★ **`As` 의 둘째 인자는** 「**대상 타입의 포인터**」다 — 대상이 `*T` 면 `**T` 다.
  빠뜨리면 **`panic: errors: target must be a non-nil pointer`**, 종료 코드 2.
  ★★ **`go vet` 이 탐침 4개 중 3개를 잡는다** —
  [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/)의 **8개 중 0개**와 정확히 대비된다.
- ★★ **커스텀 `Is` 로 「같음」을 새로 정의할 수 있다** — 다른 포인터인데 `Is` 가 `true` 가 된다.
  **커스텀 `As` 는 사슬에 없는 타입도 만들어 내준다.**
- ★★★ **`%w` 를 여러 개 쓰면 `Unwrap() []error` 가 되고 `errors.Unwrap` 이 `nil` 을 준다.**
  사슬 반복문이 **1층에서 멈춘다.** `Is`/`As` 는 그래도 다 찾는다.
- ★★★ **`errors.Join` 이 만드는 것은 트리다** — `Unwrap()` 이 `nil` 이고
  가지 안에 가지가 들어 있다. `go doc errors` 도 「**tree**」라는 낱말을 쓴다.
- ★★ **`Join` 메시지는 줄바꿈으로 이어진다**(셋이면 줄바꿈 2개)이고,
  **`nil` 을 섞으면 빠지고 전부 `nil` 이면 `nil`** 이다.
- ★★★ **이 주제는 언어 명세가 아니라 표준 라이브러리의 계약이다.**
  `go.mod` 를 `go 1.19` 로 낮춰도 `errors.Join` 이 **그냥 컴파일되고 `go vet` 도 0줄**이다 —
  [22번 주제](../22-type-assertion-any-and-comparable/)의 `comparable` 이 같은 한 줄로 막혔던 것과 **정반대**다.
- ★★ **판 경계는 `$(go env GOROOT)/api/go1NN.txt` 에서 뗀다** —
  `Is`/`As`/`Unwrap` 이 1.13, `Join` 이 1.20, `AsType` 이 1.26.
  ★ **`%w` 는 거기 안 나온다** — 포맷 동사는 API 목록의 대상이 아니다.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 24번)
- [23번 주제](../23-error-interface-and-errors-as-values/)(`error` 인터페이스) — ★★★ **이 주제의 직접 선행.**
  **그쪽은 「오류가 값이다」까지**, 여기는 **「그 값을 겹쳐 쌓고 되찾는 법」부터.**
  ★ **한 겹만 감싸도 `==` 가 깨진다**는 그쪽 (2)절이 이 주제가 존재하는 이유다
- [22번 주제](../22-type-assertion-any-and-comparable/)(타입 단언) —
  ★★ **`errors.As` 는** 「**사슬을 따라 반복하는 타입 단언**」이다.
  `AsType` 의 comma-ok 모양도 거기서 온다. ★ **판 경계를 컴파일러가 지켜 주는 쪽**의 대비도 거기
- [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/)(`nil` 인터페이스) —
  ★★ **`go vet` 이 아무것도 안 잡는 쪽**의 대비. 그리고 `errors.Is`/`As` 가 그 함정을 못 막는 이유
- [20번 주제](../20-interface-declaration-and-implicit-implementation/)(암묵 구현) —
  `Unwrap()`·`Is()`·`As()` 가 **인터페이스 선언 없이** 동작하는 바탕
- [목록의 **25번 주제**](../25-sentinel-errors-vs-custom-error-types/)(센티넬 대 커스텀 타입) — **오류 표면 설계의 정본.**
  여기는 **물어보는 법**까지
- [목록의 **27번 주제**](../27-panic-recover-and-where-to-use-them/)(`panic`/`recover`) — 이 문서는 `panic` 을 **경계로 안 다뤘다**
- 목록의 **42번 주제**(`fmt`) — `%w` 를 포함한 동사 규칙의 정본
- 목록의 **49번 주제**(`testing`) — 테스트에서 오류를 견주는 법
- 목록의 **52번 주제**(도구) — `go vet` 의 분석기 목록
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **24번**
  ([`../../../rust/syntax/24-error-type-design/`](../../../rust/syntax/24-error-type-design/)) —
  ★★ **`source()` 가 `Unwrap()` 이고 `downcast_ref` 가 `errors.As` 다. 구조가 거의 같다.**
  갈리는 것은 **Rust 가 `match` 로 완전성 검사를 얹을 수 있다**는 것과
  **Go 에는 `Join` 이 있다**는 것
- [`../../../java/syntax/25-exceptions/`](../../../java/syntax/25-exceptions/) —
  **`getCause()` 가 `Unwrap()` 이고 스택 트레이스가 언어에 내장**돼 있다.
  Go 의 오류 값에는 스택이 없다

## 용어 풀이

- **래핑** — 겉 오류가 `Unwrap()` 으로 속 오류를 돌려주는 것. **`errors` 패키지의 계약**이다.
- **`%w`** — `fmt.Errorf` 에서 감싸라는 동사(1.13). `%v` 와 메시지가 같다.
- **`errors.Unwrap`** — 한 칸만 간다. **`Unwrap() error` 만** 본다.
- **`errors.Is`** — 트리에서 **그 값과 같은 것**을 찾는다. 층마다 `Is` 메서드도 물어본다.
- **`errors.As`** — 트리에서 **그 타입인 것**을 찾아 대상에 대입한다. 못 찾으면 안 건드린다.
- **`errors.AsType[E]`** — `As` 의 제네릭 판(1.26). comma-ok 모양으로 돌려받는다.
- **`errors.Join`** — 여러 오류를 하나로(1.20). **트리**를 만들고 메시지를 줄바꿈으로 잇는다.
- **`Unwrap() []error`** — 가지가 여럿인 마디의 메서드(1.20). `errors.Unwrap` 은 이것을 안 본다.
- **트리 순회** — `go doc errors` 의 낱말로 **pre-order, depth-first**.

---

## 더 들어가면

- ★ **`errors.ErrUnsupported`**(1.21)는 이 문서가 **안 던졌다** — `go doc errors` 목록에만 나온다.
- ★★ **오류에 스택 트레이스를 붙이는 관례**(`pkg/errors` 류 외부 패키지)는 **안 던졌다.**
  표준 `errors` 에는 그 기능이 없고, 이 머신에는 그 패키지가 없다.
- ★ **`Is`/`As` 가 순환 참조를 만나면** 어떻게 되는지는 **안 던졌다.**
- ★ **`fmt.Errorf` 에 `%w` 와 다른 동사를 섞을 때의 인자 순서**는 **안 던졌다** — 목록의 **42번 주제**다.
- ★★ **`Is`/`As` 의 비용**은 **안 쟀다.** 「사슬이 길면 느리다」 같은 말을 이 문서는 하지 않는다.
- ★★ **`api/go1NN.txt` 가 「동작이 바뀐 판」을 안 담는 것**이 이 창의 한계다 —
  예컨대 `errors.Is` 가 `Unwrap() []error` 를 보게 된 것은 **API 추가가 아니라 동작 변경**이라
  그 파일에 줄이 없다. 이 문서는 그것을 **1.20의 `Join` 과 같은 판으로 추정하지 않고**,
  **`%w` 두 개가 1.20에서 도는 것**만 실행으로 보였다((6)·(9)절).

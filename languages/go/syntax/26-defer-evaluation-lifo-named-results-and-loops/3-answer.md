# go/syntax/26 — `defer`: 평가 시점·LIFO·명명 반환값 수정·루프 안의 `defer` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★ **근거로 읽을 칸** — 로그 줄의 **차례** · fd 블록의 **참거짓** · 종료 코드 · `go vet` 문장.
> **근거로 읽지 않을 칸** — `nil` 함수 패닉의 `[signal …]` 줄 **`pc=0x…`**(실행 주소).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `[평가] x = 1` 은 등록 줄 바로 아래 — A 는 1, B 는 2, B 가 먼저

**출력**

```text
===== 소스: t26a.go =====
package main

import "fmt"

// val 은 자기가 「평가된 순간」을 찍고 값을 돌려준다.
func val(tag string, v int) int {
	fmt.Printf("    [평가] %s = %d\n", tag, v)
	return v
}

func show(tag string, v int) { fmt.Printf("    [실행] %s 가 받은 값 = %d\n", tag, v) }

func main() {
	x := 1
	fmt.Println("1) defer show(\"A\", val(\"x\", x)) 를 적는다")
	defer show("A", val("x", x))

	fmt.Println("2) defer func() { show(\"B\", val(\"x\", x)) }() 를 적는다")
	defer func() { show("B", val("x", x)) }()

	x = 2
	fmt.Println("3) x = 2 로 바꿨다. 이제 main 이 끝난다")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
1) defer show("A", val("x", x)) 를 적는다
    [평가] x = 1
2) defer func() { show("B", val("x", x)) }() 를 적는다
3) x = 2 로 바꿨다. 이제 main 이 끝난다
    [평가] x = 2
    [실행] B 가 받은 값 = 2
    [실행] A 가 받은 값 = 1
(exit 0)
```

**왜 그런가**

- ★★★ `[평가] x = 1` 은 **둘째 줄**, `1)` 바로 아래다 — **인자는 `defer` 문을 지나는 순간 평가된다.**
- ★★★ `2)` 아래에는 **아무것도 없다** — 함수 리터럴은 **값으로 만들어질 뿐** 몸통은 안 돈다.
- ★★ main 이 끝난 뒤 **LIFO** 로 B 가 먼저 — 몸통이 그제야 돌아 **`[평가] x = 2`**, B 는 **2**. 그다음 A 는 저장해 둔 **1**.
- 명세 — 「**the function value and parameters to the call are evaluated as usual and saved anew but the actual function is not invoked**」.

### 2. `a` 가 돈다 · `nil` 은 나갈 때 터진다 · 그래도 `a` 는 돈다

**출력**

```text
===== 소스: t26b.go =====
package main

import (
	"fmt"
	"os"
)

func a() { fmt.Fprintln(os.Stderr, "  [defer] a 가 돌았다") }
func b() { fmt.Fprintln(os.Stderr, "  [defer] b 가 돌았다") }

func main() {
	f := a
	defer f() // 함수 값도 지금 평가된다
	f = b
	fmt.Fprintln(os.Stderr, "  f = b 로 바꿨다")

	var g func() // nil 함수 값
	defer g()
	fmt.Fprintln(os.Stderr, "  defer g() 를 지났다 — 아직 안 터졌다")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
  f = b 로 바꿨다
  defer g() 를 지났다 — 아직 안 터졌다
  [defer] a 가 돌았다
panic: runtime error: invalid memory address or nil pointer dereference
[signal SIGSEGV: segmentation violation code=0x1 addr=0x0 pc=0x499ef4]

goroutine 1 [running]:
main.main()
	ex/t26b.go:20 +0xb4
(exit 2)
```

**왜 그런가**

- ★★ **`a`** 가 돈다 — **함수 값 `f` 도 등록 시점에 평가**됐다. 뒤의 `f = b` 는 저장된 값을 못 바꾼다.
- ★★★ `defer g()` 줄은 **지나간다** — 터지는 것은 **main 이 끝나 그 쪽지를 처리할 때**다.
  명세 「**execution panics when the function is invoked, not when the "defer" statement is executed**」.
- ★★ **그래도 `a 가 돌았다` 가 찍힌다** — 패닉 중에도 남은 `defer` 는 돈다. 그다음 `panic: … nil pointer dereference`, **종료 코드 2**.

### 3. `첫째 파일` · `처음 이름` · `나중 이름`

**출력**

```text
===== 소스: t26c.go =====
package main

import "fmt"

type File struct{ name string }

func (f *File) Close() { fmt.Println("    [defer] Close :", f.name) }

type Tag struct{ name string }

func (t Tag) Print() { fmt.Println("    [defer] Print :", t.name) }

func main() {
	f := &File{"첫째 파일"}
	defer f.Close() // 수신자 f(포인터 값)가 지금 평가된다
	f = &File{"둘째 파일"}

	t := Tag{"처음 이름"}
	defer t.Print() // 값 수신자 — 지금 복사된다
	t.name = "나중 이름"

	p := &File{"처음 이름"}
	defer p.Close() // 포인터는 고정되지만 가리키는 것은 바뀔 수 있다
	p.name = "나중 이름"

	fmt.Println("  main 끝 — 아래는 LIFO")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
  main 끝 — 아래는 LIFO
    [defer] Close : 나중 이름
    [defer] Print : 처음 이름
    [defer] Close : 첫째 파일
(exit 0)
```

**왜 그런가**

- ★★★ `f` — **포인터 값(주소)** 이 등록 시점에 저장됐다. `f` 에 **다른 주소**를 넣어도 저장된 것은 첫째다 → **`첫째 파일`**.
- ★★ `t` — 값 수신자라 **구조체 전체가 복사**됐다 → **`처음 이름`**.
- ★★★ `p` — 저장된 것은 **주소**이고, `p.name = …` 은 **그 주소 너머**를 바꿨다 → **`나중 이름`**.
- ★ 정리 — **「고정」은 「복사」와 같은 질문**이다. 복사된 것만 고정된다.

### 4. `bad` 는 N 이상 쌓였다가 한꺼번에 풀리고, 고친 둘은 1 이하

**출력**

```text
===== 소스: t26d.go =====
package main

import (
	"fmt"
	"os"
	"path/filepath"
)

// openFDs 는 이 프로세스가 지금 연 fd 수를 센다(리눅스 /proc).
func openFDs() int {
	ents, err := os.ReadDir("/proc/self/fd")
	if err != nil {
		panic(err)
	}
	return len(ents)
}

// bad — 루프 안의 defer. Close 는 함수가 끝날 때 한꺼번에 돈다.
func bad(paths []string) (atEnd int) {
	for _, p := range paths {
		f, err := os.Open(p)
		if err != nil {
			panic(err)
		}
		defer f.Close()
	}
	return openFDs() // 함수 끝 직전 — defer 는 아직 하나도 안 돌았다
}

// fixFunc — 한 회차를 함수로 감싼다. defer 가 회차마다 돈다.
func fixFunc(paths []string) (peak int) {
	for _, p := range paths {
		func() {
			f, err := os.Open(p)
			if err != nil {
				panic(err)
			}
			defer f.Close()
			if n := openFDs(); n > peak {
				peak = n
			}
		}()
	}
	return peak
}

// fixClose — defer 없이 회차 끝에서 직접 닫는다.
func fixClose(paths []string) (peak int) {
	for _, p := range paths {
		f, err := os.Open(p)
		if err != nil {
			panic(err)
		}
		if n := openFDs(); n > peak {
			peak = n
		}
		f.Close()
	}
	return peak
}

const N = 50

func main() {
	dir, err := os.MkdirTemp(".", "fd")
	if err != nil {
		panic(err)
	}
	defer os.RemoveAll(dir)
	var paths []string
	for i := 0; i < N; i++ {
		p := filepath.Join(dir, fmt.Sprint(i))
		if err := os.WriteFile(p, []byte("x"), 0o644); err != nil {
			panic(err)
		}
		paths = append(paths, p)
	}
	fixClose(paths[:1]) // 런타임이 처음 한 번 여는 fd(폴러 등)를 미리 열어 둔다
	base := openFDs()

	fmt.Printf("파일 %d개를 루프로 연다 — 「늘었나」만 본다\n", N)
	atEnd := bad(paths)
	fmt.Printf("  bad      : 함수 끝 직전 증가가 N 이상인가 : %v\n", atEnd-base >= N)
	fmt.Printf("             돌아온 뒤 기준으로 돌아왔나   : %v\n", openFDs() == base)
	peak := fixFunc(paths)
	fmt.Printf("  fixFunc  : 루프 중 최대 증가가 1 이하인가  : %v\n", peak-base <= 1)
	peak = fixClose(paths)
	fmt.Printf("  fixClose : 루프 중 최대 증가가 1 이하인가  : %v\n", peak-base <= 1)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
파일 50개를 루프로 연다 — 「늘었나」만 본다
  bad      : 함수 끝 직전 증가가 N 이상인가 : true
             돌아온 뒤 기준으로 돌아왔나   : true
  fixFunc  : 루프 중 최대 증가가 1 이하인가  : true
  fixClose : 루프 중 최대 증가가 1 이하인가  : true
(exit 0)
```

**왜 그런가**

- ★★★ `bad` — **참**. 50번 연 파일이 **함수 끝까지 하나도 안 닫혔다.** `defer` 의 단위는 **함수**다.
- ★★ 돌아온 뒤 **참** — 새지는 않았다. **LIFO 로 한꺼번에** 닫혔다. 문제는 **루프 내내 쥐고 있는 것**이다.
- ★★★ `fixFunc`·`fixClose` — 둘 다 **참**(최대 증가 ≤ 1). 회차 함수의 `defer` 가 회차마다 돌거나, 직접 닫았다.
- ★ 절댓값을 안 찍은 이유 — **런타임이 처음 한 번 여는 fd**(폴러 등)가 있고 판·환경마다 다를 수 있다.
  기준을 잡기 전에 한 번 열고 닫아 두고, **「늘었나」만** 본다 — 그래야 재실행에서 안 흔들린다.

### 5. `<nil>` · `<nil>` · `save /dev/full: write /dev/full: no space left on device`

**출력**

```text
===== 소스: t26f.go =====
package main

import (
	"bufio"
	"fmt"
	"os"
)

// /dev/full 은 쓰기마다 ENOSPC 를 돌려주는 리눅스 장치다.
// bufio 가 모아 두었다가 Flush 에서야 실제로 쓰므로 실패도 그때 나온다.

// dropped — defer 가 Flush 의 반환값을 버린다.
func dropped(path string) error {
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()
	w := bufio.NewWriter(f)
	defer w.Flush() // 오류가 여기서 사라진다
	_, err = w.WriteString("중요한 데이터")
	return err
}

// overwrite — 21편 (라)의 꼴. defer 가 명명 반환값을 무조건 덮는다.
func overwrite(path string) (err error) {
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer func() { err = f.Close() }() // Flush 의 오류를 Close 의 nil 로 덮는다
	w := bufio.NewWriter(f)
	if _, err = w.WriteString("중요한 데이터"); err != nil {
		return err
	}
	return w.Flush()
}

// checked — 명명 반환값을 「비어 있을 때만」 채우고, 문맥도 붙인다.
func checked(path string) (err error) {
	defer func() {
		if err != nil {
			err = fmt.Errorf("save %s: %w", path, err)
		}
	}()
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer func() {
		if cerr := f.Close(); cerr != nil && err == nil {
			err = cerr
		}
	}()
	w := bufio.NewWriter(f)
	if _, err = w.WriteString("중요한 데이터"); err != nil {
		return err
	}
	return w.Flush()
}

func main() {
	fmt.Println("dropped   :", dropped("/dev/full"))
	fmt.Println("overwrite :", overwrite("/dev/full"))
	fmt.Println("checked   :", checked("/dev/full"))
}
===== 명령: go build -trimpath -o prog . && ./prog =====
dropped   : <nil>
overwrite : <nil>
checked   : save /dev/full: write /dev/full: no space left on device
(exit 0)
```

**왜 그런가**

- ★★★ `dropped` — `defer w.Flush()` 가 **ENOSPC 를 버렸다.** `WriteString` 은 버퍼에 넣어 성공했으니 **성공을 보고하고 데이터는 사라졌다.**
- ★★★ `overwrite` — **`return w.Flush()` 가 결과 칸 `err` 에 ENOSPC 를 써 놓았고**, 그 뒤에 도는
  `defer func(){ err = f.Close() }()` 가 **`nil` 로 덮었다.** [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/) (라)의 꼴이다.
- ★★ `checked` — Close 오류는 **`err == nil` 일 때만** 채우고, 문맥 `defer` 는 **먼저 등록**해 **맨 나중에** 돈다.
  그래야 **Close 오류까지 모인 뒤에** 한 번 감싼다 — **LIFO 를 설계에 쓴 자리**다.

### 6. 안 찍힌다 · 종료 코드 3 · `os` 패키지의 계약

**출력**

```text
===== 소스: t26e.go =====
package main

import (
	"fmt"
	"os"
)

func main() {
	defer fmt.Fprintln(os.Stderr, "  [defer] 이 줄은 찍히나?")
	fmt.Fprintln(os.Stderr, "  os.Exit(3) 을 부른다")
	os.Exit(3)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
  os.Exit(3) 을 부른다
(exit 3)
```

**왜 그런가**

- ★★★ `[defer]` 줄이 **없다**, 종료 코드 **3**.
- ★★ **명세가 아니라 `os` 패키지의 계약**이다 — `go doc os.Exit` 「**The program terminates immediately; deferred functions are not run.**」
  명세의 `defer` 는 「함수가 **반환할 때**」를 말하는데 `os.Exit` 는 반환하지 않는다. `log.Fatal` 도 속에서 `os.Exit(1)` 이다.
- ★★ C++ 의 **`std::_Exit`** — [C++ 14번](../../../cpp/syntax/14-destructors-and-deterministic-destruction/) (3)절이 **소멸자가 하나도 안 도는 것**(`[파괴]` 0줄)을 실측했다.

### 7. 「함수 값과 인자」 · 「결과 칸이 채워진 뒤」

```text
===== 명령: sed -n "7361,7374p" "$(go env GOROOT)/doc/go_spec.html" | sed -e "s/<[^>]*>//g" =====

Each time a "defer" statement
executes, the function value and parameters to the call are
evaluated as usual
and saved anew but the actual function is not invoked.
Instead, deferred functions are invoked immediately before
the surrounding function returns, in the reverse order
they were deferred. That is, if the surrounding function
returns through an explicit return statement,
deferred functions are executed after any result parameters are set
by that return statement but before the function returns to its caller.
If a deferred function value evaluates
to nil, execution panics
when the function is invoked, not when the "defer" statement is executed.
(exit 0)
```

- ★★★ 지금 평가되는 것 둘 — **함수 값**(`f`·메서드 값의 수신자)과 **인자**. 클로저 몸통 안의 변수는 **둘 다 아니다.**
- ★★★ 「**deferred functions are executed after any result parameters are set by that return statement but before the function returns to its caller**」.
  - **정당한 쓰임** — `err` 가 이미 채워진 것을 보고 **문맥을 붙인다**(`checked`, [12번 주제](../12-functions-multiple-returns-named-results-and-variadics/) (2)절).
  - **함정** — 같은 칸을 **무조건 덮는다**(`overwrite`).
  ★ 한 문장이 둘을 다 가능하게 한다 — 차이는 **조건을 거느냐**뿐이다.

### 8. C++ 는 블록 끝, Go 는 함수 끝

- ★★★ **C++ 소멸자 — 스코프(블록) 끝. Go `defer` — 둘러싼 함수 끝.**
- ★★ 둘 다 **쌓인 역순**이다(C++ 14번의 「지역 3 → 2 → 1」, Go 의 LIFO). 갈리는 것은 **쌓는 통의 크기**다 —
  루프 본문 `{ }` 은 C++ 에서는 **회차마다 비워지는 통**이고 Go 에서는 **통이 아니다.** 그래서 Go 에서만 쌓인다.
- ★ **Python `with`·Rust `Drop` 은 C++ 쪽**이다 — 블록(스코프) 끝에서 닫는다.
  ([`../../../python/syntax/28-context-managers-and-with/`](../../../python/syntax/28-context-managers-and-with/) · [Rust 09번](../../../rust/syntax/09-copy-clone-and-drop/).)

### 9. 넷 중 하나 — `time.Since` 를 인자로

**출력**

```text
===== 소스: t26vet.go =====
package main

import (
	"fmt"
	"os"
	"time"
)

// 탐침 1 — 루프 안의 defer
func p1(paths []string) {
	for _, p := range paths {
		f, _ := os.Open(p)
		defer f.Close()
	}
}

// 탐침 2 — 쓰기 파일의 Close 오류를 버린다
func p2() {
	f, _ := os.Create("x")
	defer f.Close()
	f.WriteString("x")
}

// 탐침 3 — defer 의 인자에서 time.Since 를 부른다(등록 시점에 평가된다)
func p3() {
	start := time.Now()
	defer fmt.Println(time.Since(start))
}

// 탐침 4 — defer 뒤에 os.Exit
func p4() {
	defer fmt.Println("x")
	os.Exit(1)
}

func main() { p1(nil); p2(); p3(); p4() }
===== 명령: go vet ./... =====
t26vet.go:27:20: call to time.Since is not deferred
(exit 1)
```

- ★★★ **1개** — `call to time.Since is not deferred`(탐침 3). 종료 코드 1.
- ★★ **(1)번의 규칙 그 자체**다 — `time.Since(start)` 가 인자 자리에 있으니 **등록 시점에 평가돼 0 근처**가 찍힌다.
- ★★ 안 잡힌 셋 — 「루프가 도나」·「이 파일이 쓰기용인가」·「`os.Exit` 가 `defer` 를 버리나」는
  **그 식 하나만 봐서는 안 보이는 사실**이다. `time.Since` 는 **식의 모양**만 보면 된다.

### 10. 클로저로 감싸기 · 함수로 감싸기 · `os.Exit(run())`

- ★★ 소요 시간 — **`defer func(){ log.Println(time.Since(start)) }()`**. 인자로 넣으면 등록 시점 값(≈0)이다.
- ★★★ 루프의 파일 — ① **회차를 함수로 감싼다**(`fixFunc`) ② **회차 끝에서 직접 `Close`**(`fixClose` — 사이의 `return`·패닉은 못 덮는다).
- ★★ 종료 코드 + 정리 — **`func main() { os.Exit(run()) }`**. 정리는 `run` 의 `defer` 가 하고, `run` 이 **반환한 뒤** 나간다.


---

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 로 **★고칠 것 0** |
| ★★★ 평가 시점 (`t26a`) | `go build && ./prog` | 1 | `[평가] x = 1` 이 등록 줄 아래 · `x = 2` 가 끝에 |
| ★★ 함수 값·`nil` (`t26b`) | 〃 | 1 | `a` · 나갈 때 패닉 · exit 2 |
| ★★ 수신자 (`t26c`) | 〃 | 1 | 첫째 · 처음 · 나중 |
| ★★★ 루프 fd (`t26d`) | 〃 (리눅스 `/proc/self/fd`) | 1 | `bad` N 이상 · 고친 둘 ≤ 1 |
| ★★★ 버려지는 오류 (`t26f`) | 〃 (`/dev/full`) | 1 | `<nil>` · `<nil>` · ENOSPC |
| ★★ `os.Exit` (`t26e`) | 〃 | 1 | `[defer]` 0줄 · exit 3 |
| ★ `go vet` 탐침 (`t26vet`) | `go vet ./...` | 1 | **4개 중 1개** · exit 1 |
| 명세 | `go_spec.html` 7361\~7374행 | 1 | 위 인용문 |

**구현·환경에 달린 항목**

| 항목 | 무엇에 달렸나 |
|---|---|
| `nil` 함수 패닉의 `pc=0x…` | **실행 주소** — 흔들리는 칸 |
| `/proc/self/fd` · `/dev/full` | **리눅스** — 다른 OS 에서는 이 블록이 안 돈다 |
| 런타임이 처음 여는 fd 의 수 | **구현** — 그래서 절댓값을 안 실었다 |
| `go vet` 이 무엇을 잡나 | **도구 판(go1.27.1)** |
| `defer` 의 **비용**·open-coded 여부 | ★ **안 쟀다 · 안 봤다** |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다.

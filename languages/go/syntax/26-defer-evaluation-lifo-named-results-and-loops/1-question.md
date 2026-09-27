# go/syntax/26 — `defer`: 평가 시점·LIFO·명명 반환값 수정·루프 안의 `defer` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ **모든 문제에서 두 칸을 먼저 그려라 — 「등록 시점에 무엇이 평가됐나」 / 「실행 시점에 무엇이 읽혔나」.**
> ★★ **「이 순서를 누가 보장하나」를 매번 물어라** — 답은 거의 다 「**명세**」이고, 하나만 `os` 패키지다.
> 소스는 전부 `go build -trimpath -o prog . && ./prog` 로 던졌다. 모듈 이름은 `ex` 다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 평가되는 순간 이름을 찍는 함수를 인자에 끼우면 (예측)

```go
// t26a.go
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
```

- `[평가] x = 1` 은 **몇 번째 줄**에 찍히나 — 어느 줄 바로 아래인가?
- `2)` 줄 바로 아래에 `[평가]` 가 찍히나?
- A 와 B 는 각각 **무슨 값**을 받나 — 어느 쪽이 먼저 찍히나?

### 2. 함수 변수와 `nil` 함수를 `defer` 하면 (예측)

```go
// t26b.go
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
```

- `a` 와 `b` 중 어느 것이 도나?
- `defer g()` 줄에서 터지나 — 아니면 언제 터지나?
- 터진 뒤에도 `[defer] a 가 돌았다` 가 찍히나? 종료 코드는?

### 3. 메서드 값의 수신자 (예측)

```go
// t26c.go
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
```

- `Close` 가 찍는 이름 둘과 `Print` 가 찍는 이름은 각각 무엇인가?
- 첫째 `f` 와 셋째 `p` 가 다른 결과를 내는 이유를 「무엇이 복사됐나」로 말하라.

### 4. 루프 안의 `defer` 를 fd 로 세면 (예측)

```go
// t26d.go
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
```

- `bad` 의 「함수 끝 직전 증가가 N 이상인가」는 참인가?
- `bad` 가 돌아온 뒤에는 기준으로 돌아오나 — 샜나?
- `fixFunc`·`fixClose` 의 「최대 증가가 1 이하인가」는?
- 왜 fd 의 **절댓값**이 아니라 참거짓만 찍었나?

### 5. `/dev/full` 에 세 방식으로 쓰면 (예측)

```go
// t26f.go
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
```

- `dropped`·`overwrite`·`checked` 가 각각 무엇을 돌려주나?
- `overwrite` 에서 진짜 오류는 **어디서 생겼다가 어디서 사라졌나**?
- `checked` 의 두 `defer` 중 문맥을 붙이는 것을 **먼저** 등록한 이유는?

### 6. `os.Exit` 와 `defer` (예측)

```go
// t26e.go
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
```

- `[defer]` 줄은 찍히나? 종료 코드는?
- 이것은 명세가 정한 것인가, 무엇이 정한 것인가?
- C++ 에서 같은 자리에 있는 함수는 무엇이고, 그쪽에서 무엇이 안 도나?

### 7. 명세의 한 문장 (왜)

- 명세가 「지금 평가된다」고 적은 것 **두 가지**는 무엇인가?
- `return` 과 `defer` 의 순서를 명세는 어떻게 적나 — 그 문장이 **정당한 쓰임과 함정** 둘 다의 근거가 되는 이유는?

### 8. 스코프 끝과 함수 끝 (연결)

- C++ 의 소멸자와 Go 의 `defer` 는 **어느 단위의 끝**에서 도나?
- 둘 다 「역순」인데 루프 안에서 결과가 갈리는 이유는?
- Python `with` 와 Rust `Drop` 은 어느 쪽에 가까운가?

### 9. 도구가 잡는 것 (경계)

- `go vet` 이 탐침 넷 중 **몇 개**를 잡나 — 잡힌 것은 무엇인가?
- 잡힌 것이 (1)번의 규칙과 어떻게 이어지나?
- 안 잡힌 셋은 왜 그 자리에서 판정할 수 없나?

### 10. 어느 것을 쓰나 (경계)

- 소요 시간 로그를 `defer` 로 남긴다 — 어떤 꼴이어야 0 이 안 찍히나?
- 루프에서 파일을 연다 — 고치는 법 둘은?
- `main` 에서 종료 코드를 정하면서 정리도 하고 싶다 — 어떤 꼴인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

# go/syntax/28 — 고루틴: `go` 문·시작 비용·종료 조건 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ **모든 문제에서 「흔들리는 칸은 무엇이고, 안 흔들리는 질문으로 바꾸면 무엇인가」를 먼저 적어라.**
> ★★ **「이것은 명세인가 구현인가」를 매번 물어라** — 평가 시점·`main` 종료는 명세, 스택 크기·id·순서는 구현이다.
> 소스는 전부 `go build -trimpath -o prog . && ./prog` 로 던졌다. 모듈 이름은 `ex` 다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `main` 이 20ms 뒤에 끝나면 (예측)

```go
// t28a.go
package main

import (
	"fmt"
	"time"
)

func main() {
	go func() {
		defer fmt.Println("[고루틴 defer] 돌았다")
		for i := 1; i <= 1000; i++ {
			fmt.Println("고루틴", i)
			time.Sleep(time.Millisecond)
		}
		fmt.Println("고루틴 끝")
	}()
	time.Sleep(20 * time.Millisecond)
	fmt.Println("main 끝")
}
```

<!-- 출력을 파일로 받고 셸이 참거짓만 찍었다: main 끝 · 고루틴 끝 · 고루틴 defer · 줄 수 < 1000 -->

- 종료 코드는 몇인가?
- `main 끝` 과 `고루틴 끝` 은 각각 찍히나?
- `[고루틴 defer] 돌았다` 는 찍히나?
- 이 블록에서 **싣지 않은 흔들리는 값**은 무엇인가?

### 2. 만든 수와 남은 수 (예측)

```go
// t28b.go
package main

import (
	"fmt"
	"runtime"
	"sync"
	"time"
)

// settle 은 NumGoroutine 이 want 가 될 때까지 최대 1초 기다린다.
func settle(want int) bool {
	for deadline := time.Now().Add(time.Second); time.Now().Before(deadline); {
		if runtime.NumGoroutine() == want {
			return true
		}
		time.Sleep(time.Millisecond)
	}
	return false
}

func main() {
	fmt.Println("시작                     :", runtime.NumGoroutine())

	release := make(chan struct{})
	var wg sync.WaitGroup
	for range 100 {
		wg.Go(func() { <-release }) // 1.25 의 WaitGroup.Go
	}
	fmt.Println("100개 띄운 직후          :", runtime.NumGoroutine())
	close(release)
	wg.Wait()
	fmt.Println("Wait 뒤 1 로 돌아왔나    :", settle(1))

	stuck := make(chan struct{}) // 아무도 안 닫는다
	for range 10 {
		go func() { <-stuck }()
	}
	fmt.Println("받을 쪽 없는 10개 뒤     :", runtime.NumGoroutine())
	fmt.Println("1초 기다리면 1 로 가나   :", settle(1))
}
```

- 다섯 줄에 각각 무엇이 찍히나?
- `Wait` 가 돌아온 직후 `NumGoroutine()` 을 바로 찍지 않고 `settle` 로 기다린 이유는?
- 마지막 줄이 `false` 라면 그것은 무엇을 뜻하나?

### 3. `go` 문의 인자 (예측)

```go
// t28c.go
package main

import "fmt"

func val(tag string, v int) int {
	fmt.Printf("    [평가] %s = %d\n", tag, v)
	return v
}

func show(tag string, v int, ready <-chan struct{}, done chan<- struct{}) {
	<-ready
	fmt.Printf("    [실행] %s 가 받은 값 = %d\n", tag, v)
	close(done)
}

func main() {
	x := 1
	readyA, doneA := make(chan struct{}), make(chan struct{})
	readyB, doneB := make(chan struct{}), make(chan struct{})

	fmt.Println("1) go show(\"A\", val(\"x\", x), …) 를 적는다")
	go show("A", val("x", x), readyA, doneA)

	fmt.Println("2) go func() { … val(\"x\", x) … }() 를 적는다")
	go func() {
		<-readyB
		fmt.Printf("    [실행] B 가 읽은 값 = %d\n", val("x", x))
		close(doneB)
	}()

	x = 2
	fmt.Println("3) x = 2 로 바꾸고 A, B 를 차례로 풀어 준다")
	close(readyA)
	<-doneA
	close(readyB)
	<-doneB
}
```

- `[평가] x = 1` 은 어느 줄 바로 아래 찍히나 — 어느 고루틴에서 평가됐나?
- A 와 B 가 받은 값은?
- A·B 의 출력 순서가 흔들리지 않는 이유는?

### 4. 루프 변수를 두 판으로 200번씩 (예측)

```go
// t28d.go
package main

import (
	"fmt"
	"slices"
)

func main() {
	start := make(chan struct{})
	out := make(chan int, 3)
	for i := 0; i < 3; i++ {
		go func() {
			<-start // 루프가 다 끝난 뒤에 읽게 한다 — 경쟁이 아니라 판의 의미만 남긴다
			out <- i
		}()
	}
	close(start)
	got := []int{<-out, <-out, <-out}
	slices.Sort(got) // 도착 순서는 흔들리므로 정렬한다
	fmt.Println(got)
}
```

<!-- 같은 소스를 go.mod 의 go 1.21 과 go 1.22 두 판으로 던지고, 200판을 정렬해 uniq -c 로 셌다. -->

- `go 1.21` 판과 `go 1.22` 판에서 각각 **몇 가지**가 나오고 그것은 무엇인가?
- `<-start` 를 빼면 1.21 판은 어떻게 되나 — 그것은 어느 주제의 일인가?
- 왜 `slices.Sort` 로 정렬했나?

### 5. 스택 초기 크기 (경계)

- 런타임 소스의 `stackMin` 값은 얼마이고, 그것은 **명세**인가?
- 「새 고루틴은 2KB 로 시작한다」를 이 판에서 고정된 사실로 적으면 왜 틀리나 — 어느 스위치 때문인가?
- 메모리 격자 네 칸이 말하는 것과 **말하지 않는 것**은 각각 무엇인가?

### 6. `go` 뒤에 올 수 있는 것 (예측)

```go
// t28bad.go
package main

func f() int { return 1 }

func main() {
	s := []int{1}
	go len(s)
	go (f())
	go f
	defer f
	defer len(s)
	go f() // 이 줄은 된다 — 반환값은 버려진다
}
```

- 진단이 몇 줄이고 각각 무엇을 거부하나?
- 마지막 `go f()` 는 왜 통과하나 — `f` 의 반환값은 어디로 가나?

### 7. `defer` 와 `go` 문 (연결)

- 두 문의 명세 문장에서 **같은 부분**은 무엇인가?
- 다른 부분 — 「언제 실행되나」는 각각 무엇인가?
- `main` 의 반환과 `os.Exit` 는 `defer` 에 대해 무엇이 같은가?

### 8. 명세와 구현 (왜)

- 「`main` 이 반환하면 다른 고루틴을 기다리지 않는다」는 어느 층인가?
- 「고루틴 id」·「스케줄링 순서」·「스택 크기」는 어느 층인가?
- 루프 변수 1.22 변경은 어느 층이고, 무엇이 그 판을 고르나?

### 9. 어느 것을 쓰나 (경계)

- 여러 일을 띄우고 다 끝날 때까지 기다린다 — 무엇을 쓰고 1.25 에서 무엇이 생겼나?
- 고루틴에서 결과값을 받는다 — 왜 `go` 문으로는 안 되고 무엇을 쓰나?
- 고루틴 안의 패닉을 막는다 — 어디에 `recover` 를 두나?
- 누수를 테스트한다 — 무엇을 어떻게 보나?

### 10. 다른 언어·다른 갈래와 (연결)

- 자바 가상 스레드는 `main` 이 끝날 때 Go 고루틴과 무엇이 같은가 — 플랫폼 스레드와는 무엇이 다른가?
- 「고루틴은 왜 싼가」의 논증은 어느 문서가 정본인가?
- 스레드·경쟁 조건 일반은 어느 폴더가 정본인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

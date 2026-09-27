# go/syntax/29 — 채널: 버퍼·방향·`close`·`range`·`nil` 채널 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ **모든 문제에서 「막힌다 / 터진다 / 값이 나온다」 셋 중 무엇인지를 먼저 적어라.** 막히면 **런타임이 알려 주나**까지.
> ★★ **「이것은 명세인가 구현인가」를 매번 물어라** — 차단 규칙·닫힌 채널은 명세, 교착 탐지·종료 코드 2 는 구현이다.
> 소스는 전부 `go build -trimpath -o prog .` 로 빌드했다. 모듈 이름은 `ex` 다. 탐침의 표시는 **stderr** 에 찍는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 버퍼 × 송신 횟수 격자 (예측)

```go
// t29grid.go
package main

import (
	"fmt"
	"os"
	"strconv"
)

// 인자: 버퍼 크기, 보낼 횟수. 받는 쪽은 아무도 없다.
func main() {
	buf, _ := strconv.Atoi(os.Args[1])
	sends, _ := strconv.Atoi(os.Args[2])
	ch := make(chan int, buf)
	for i := range sends {
		ch <- i
	}
	fmt.Fprintln(os.Stderr, "보낸 수", sends, "len", len(ch), "cap", cap(ch))
}
```

<!-- 셸이 버퍼 0·1·3 × 송신 1·2·3·4 의 12칸을 돌리고, 칸마다 exit 코드와 stderr 에 all goroutines are asleep 이 있나를 찍는다. 마지막 줄에 죽은 칸 수 / 전체 칸 수. -->

- 12칸 중 몇 칸이 죽나? 규칙을 한 줄로 적어라.
- 죽는 칸의 종료 코드는? 그것은 `panic` 인가 `fatal error` 인가 — `recover` 로 잡히나?
- 죽은 칸의 트레이스 둘째 줄(`goroutine 1 […]:`)의 괄호 안에는 무엇이 적히나?

### 2. `len`·`cap` 과 버퍼 0 의 깃발 (예측)

```go
// t29lencap.go
package main

import (
	"fmt"
	"sync/atomic"
	"time"
)

func main() {
	b := make(chan int, 3)
	fmt.Println("버퍼 3, 만든 직후   : len", len(b), "cap", cap(b))
	for i := 1; i <= 3; i++ {
		b <- i
		fmt.Println("버퍼 3, 보낸 뒤", i, "  : len", len(b), "cap", cap(b))
	}
	<-b
	fmt.Println("버퍼 3, 하나 받은 뒤: len", len(b), "cap", cap(b))

	u := make(chan int)
	fmt.Println("버퍼 0             : len", len(u), "cap", cap(u))

	var aboutToReceive atomic.Bool
	go func() {
		time.Sleep(30 * time.Millisecond)
		aboutToReceive.Store(true) // 받기 직전에 깃발을 올린다
		<-u
	}()
	u <- 1 // 버퍼 0 에 보낸다
	fmt.Println("버퍼 0 송신이 돌아왔을 때 받는 쪽 깃발:", aboutToReceive.Load())
}
```

- 여섯 줄의 `len`·`cap` 값을 적어라.
- 마지막 줄의 깃발은 `true` 인가 `false` 인가 — **시간이 아니라 무엇이** 그것을 보장하나?

### 3. 방향 채널 (예측)

```go
// t29dir.go
package main

func producer(out chan<- int) {
	out <- 1
	<-out
}

func consumer(in <-chan int) {
	<-in
	in <- 1
	close(in)
}

func main() {
	ch := make(chan int, 1)
	producer(ch) // 양방향 채널을 넘긴다
	consumer(ch) // 양방향 채널을 넘긴다
	var r <-chan int = ch
	var back chan int = r
	_ = back
}
```

<!-- go build -trimpath -gcflags=-e -o prog . -->

- 몇 줄이 컴파일 에러인가? 줄 번호를 적어라.
- `producer(ch)` · `consumer(ch)` · `var r <-chan int = ch` 는 통과하나?
- 이 가운데 **관례를 타입이 강제하는** 줄은 어느 것인가?

### 4. 닫힌 채널 × 다섯 연산 (예측)

```go
// t29closed.go
package main

import (
	"fmt"
	"os"
)

func main() {
	ch := make(chan int, 2)
	switch os.Args[1] {
	case "rest": // 값이 남은 채로 닫고 받기
		ch <- 7
		close(ch)
		v1, ok1 := <-ch
		v2, ok2 := <-ch
		fmt.Println(v1, ok1, v2, ok2)
	case "empty": // 빈 채로 닫고 받기
		close(ch)
		v, ok := <-ch
		fmt.Println(v, ok)
	case "send": // 닫은 뒤 보내기
		close(ch)
		ch <- 1
		fmt.Println("송신 뒤 줄")
	case "reclose": // 두 번 닫기
		close(ch)
		close(ch)
		fmt.Println("두 번째 close 뒤 줄")
	case "range": // 닫은 채널을 range
		ch <- 1
		ch <- 2
		close(ch)
		for v := range ch {
			fmt.Print(v, " ")
		}
		fmt.Println("range 뒤 줄")
	}
}
```

<!-- 셸이 rest·empty·send·reclose·range 를 차례로 돌리고, 칸마다 stdout · stderr 첫 줄 · exit 를 따로 찍는다. -->

- 다섯 칸의 stdout 과 종료 코드를 적어라.
- 터지는 칸의 첫 줄 문구는? 그것은 `recover` 가 들을 수 있는 것인가?
- `rest` 에서 남은 7 은 받히나, 버려지나?

### 5. `nil` 채널 × 네 연산 (예측)

```go
// t29nil.go
package main

import (
	"fmt"
	"os"
)

func main() {
	var ch chan int // nil 채널
	fmt.Fprintln(os.Stderr, "ch == nil :", ch == nil, "len", len(ch), "cap", cap(ch))
	switch os.Args[1] {
	case "send":
		ch <- 1
	case "recv":
		<-ch
	case "close":
		close(ch)
	case "range":
		for range ch {
		}
	}
	fmt.Fprintln(os.Stderr, "switch 뒤 줄")
}
```

<!-- 셸이 send·recv·close·range 를 timeout 2 로 돌리고, 칸마다 stderr 1·2줄 · goroutine 1 상태 줄 · exit 를 찍는다. -->

- 첫 줄(`ch == nil …`)은 넷이 같은가? `len`·`cap` 은 터지나?
- 네 칸 각각 — 막히나, 터지나? 막히면 상태 줄의 괄호 안에 무엇이 붙나?
- `switch 뒤 줄` 은 어느 칸에서 찍히나?

### 6. 곁에 둔 고루틴 셋 (예측)

```go
// t29hide.go
package main

import (
	"fmt"
	"os"
	"time"
)

func main() {
	block := make(chan int)
	switch os.Args[1] {
	case "sleeper": // 잠만 자는 고루틴 하나를 곁에 둔다
		go func() {
			for {
				time.Sleep(time.Hour)
			}
		}()
	case "stuck": // 채널에서 막힌 고루틴 하나를 곁에 둔다
		go func() { <-block }()
	}
	fmt.Fprintln(os.Stderr, "main 이 nil 채널에 보낸다")
	var ch chan int
	ch <- 1
}
```

<!-- 셸이 alone·stuck·sleeper 를 timeout 2 로 돌리고, 칸마다 exit 와 all goroutines are asleep 가 있나를 찍는다. 마지막 줄에 탐지 못 한 칸 수 / 전체 칸 수. -->

- main 은 셋 다 `nil` 채널에 **영원히** 막힌다. 세 칸의 종료 코드는 각각 몇인가?
- 탐지 못 한 칸은 몇 / 3 인가? 그 칸에서 **누가** 프로세스를 끝냈나?
- 「새어 있는 고루틴이 교착 탐지를 가린다」는 맞는 말인가 — **어떤** 고루틴이 가리나?

### 7. `range` 는 언제 끝나나 (왜)

- 보내는 고루틴이 3 개를 보내고 **끝났는데** `for v := range ch` 가 넷째를 기다리는 이유는?
- 「고루틴이 끝났다」와 「채널을 닫았다」는 무엇이 다른가?
- 이 코드가 탐침이 아니라 **다른 고루틴이 살아 있는 서버** 안에 있다면 무엇이 보이나?

### 8. 누가 닫나 (경계)

- 받는 쪽이 채널을 닫으면 **어느 고루틴이** 패닉하고, 프로세스는 어떻게 되나?
- 받는 쪽이 「그만 보내라」를 알려야 할 때는 무엇을 쓰나?
- 보내는 쪽이 **여럿**이면 누가 언제 닫나?

### 9. 명세와 구현 (왜)

- 「버퍼 0 채널에 받는 쪽 없이 보내면 막힌다」와 「그러면 `fatal error` 로 죽는다」 — 각각 어느 층인가?
- 교착 탐지가 **타이머가 있으면 포기하는** 이유를 런타임 소스의 주석으로 말해 보라.
- 「버퍼 0 송신이 돌아왔으면 받는 쪽은 이미 받았다」는 어느 문서가 보장하나?

### 10. 다른 언어·다른 갈래와 (연결)

- Rust `mpsc` 에서 받는 쪽을 버린 뒤 보내면 무엇이 오나 — Go 의 무엇과 다른가?
- Rust 에는 `close` 가 없다. 무엇이 닫힘을 대신하나?
- 버퍼 크기·넘침 정책을 **설계**하는 것은 어느 문서가 정본인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

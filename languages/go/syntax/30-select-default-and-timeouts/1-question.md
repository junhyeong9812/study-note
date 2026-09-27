# go/syntax/30 — `select`·`default`·타임아웃 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ **무작위가 걸린 문제는 「한 판에 무엇이 나오나」가 아니라 「여러 판에 몇 가지가 나올 수 있나」로 답하라.**
> ★★ **「이것은 명세인가 구현인가」를 매번 물어라** — 「균등 의사 무작위」는 명세, 섞는 방법과 비율은 구현이다.
> 소스는 전부 `go build -trimpath -o prog .` 로 빌드했다. 모듈 이름은 `ex` 다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 준비 상태 넷 × 200판 (예측)

```go
// t30grid.go
package main

import (
	"fmt"
	"os"
)

// 인자로 「어느 채널에 값이 있나 · default 가 있나」를 고른다. 한 판에 select 한 번.
func main() {
	a := make(chan int, 1)
	b := make(chan int, 1)
	mode := os.Args[1]
	if mode == "both" || mode == "onlyA" || mode == "aDefault" {
		a <- 1
	}
	if mode == "both" {
		b <- 1
	}
	if mode == "aDefault" || mode == "noneDefault" {
		select {
		case <-a:
			fmt.Println("a")
		case <-b:
			fmt.Println("b")
		default:
			fmt.Println("default")
		}
		return
	}
	select {
	case <-a:
		fmt.Println("a")
	case <-b:
		fmt.Println("b")
	}
}
```

<!-- 셸이 both·onlyA·aDefault·noneDefault 를 각 200판 돌려 sort -u 로 가짓수와 그 목록을 찍는다. 이어서 none 을 한 판(timeout 2) 돌려 exit 와 stderr 첫 줄을 찍는다. 마지막 줄에 가짓수가 2 이상인 칸 수 / 4. -->

- 네 칸 각각 200판에 **몇 가지**가 나오나? 무엇이 나오나?
- `aDefault` 에서 `default` 는 한 번이라도 나오나?
- `none` 의 종료 코드와 stderr 첫 줄은? 트레이스의 상태 줄 괄호 안에는 무엇이 적히나?
- 마지막 줄은 몇 / 4 인가?

### 2. `default` 있는 루프·없는 루프 (예측)

```go
// t30busy.go
package main

import (
	"fmt"
	"time"
)

func main() {
	done := make(chan struct{})
	go func() {
		time.Sleep(20 * time.Millisecond)
		close(done)
	}()
	spins := 0
	for {
		spins++
		select {
		case <-done:
			fmt.Println("default 있는 루프: 1회보다 많이 돌았나:", spins > 1)
			goto blocking
		default:
		}
	}
blocking:
	done2 := make(chan struct{})
	go func() {
		time.Sleep(20 * time.Millisecond)
		close(done2)
	}()
	spins = 0
	for {
		spins++
		select {
		case <-done2:
			fmt.Println("default 없는 루프: 돈 횟수:", spins)
			return
		}
	}
}
```

- 첫 줄은 `true` 인가 `false` 인가 — 그 루프는 20ms 동안 무엇을 하고 있었나?
- 둘째 줄의 횟수는?
- 이 블록은 CPU 사용량에 대해 무엇을 말하고 무엇을 말하지 **않나**?

### 3. 타임아웃과 남는 고루틴 (예측)

```go
// t30timeout.go
package main

import (
	"fmt"
	"runtime"
	"time"
)

// call 은 고루틴에게 일을 맡기고 50ms 까지만 기다린다. 결과 채널은 버퍼 0 이다.
func call(d time.Duration) string {
	res := make(chan int)
	go func() {
		time.Sleep(d)
		res <- 42
	}()
	select {
	case v := <-res:
		return fmt.Sprint("받음 ", v)
	case <-time.After(50 * time.Millisecond):
		return "시간 초과"
	}
}

func main() {
	fmt.Println("빠른 일(0ms)    :", call(0))
	fmt.Println("느린 일(200ms)  :", call(200*time.Millisecond))
	time.Sleep(400 * time.Millisecond) // 느린 일이 보낼 차례를 충분히 지나 보낸다
	fmt.Println("400ms 뒤 NumGoroutine:", runtime.NumGoroutine())
}
```

- 세 줄을 적어라.
- 마지막 줄의 `NumGoroutine` 이 1 이 아닌 이유는? 그 고루틴은 지금 **무엇에** 막혀 있나?

### 4. `nil` 로 끈 쪽·안 끈 쪽 (예측)

```go
// t30nilcase.go
package main

import (
	"fmt"
	"slices"
)

func filled(vals ...int) chan int {
	ch := make(chan int, len(vals))
	for _, v := range vals {
		ch <- v
	}
	close(ch)
	return ch
}

func main() {
	// 1) 닫힌 채널을 nil 로 바꿔 가지를 끈다
	a, b := filled(1, 2), filled(10, 20, 30)
	var got []int
	for a != nil || b != nil {
		select {
		case v, ok := <-a:
			if !ok {
				a = nil
				continue
			}
			got = append(got, v)
		case v, ok := <-b:
			if !ok {
				b = nil
				continue
			}
			got = append(got, v)
		}
	}
	slices.Sort(got)
	fmt.Println("nil 로 끈 쪽 — 받은 값:", got)

	// 2) 끄지 않으면 — 닫힌 채널 가지가 계속 뽑힌다 (1000회로 자른다)
	a, b = filled(1, 2), filled(10, 20, 30)
	zeros := 0
	for range 1000 {
		select {
		case _, ok := <-a:
			if !ok {
				zeros++
			}
		case _, ok := <-b:
			if !ok {
				zeros++
			}
		}
	}
	fmt.Println("안 끈 쪽 — 1000회 중 ok=false 로 받은 횟수:", zeros)
}
```

- 첫 줄에 무엇이 찍히나? 루프는 끝나나?
- 둘째 줄의 횟수는 몇인가 — 왜 딱 그 수인가?

### 5. `break` 두 가지 (예측)

```go
// t30break.go
package main

import (
	"fmt"
	"os"
)

func main() {
	ch := make(chan int, 3)
	ch <- 1
	ch <- 2
	close(ch)
	var got []int
	if os.Args[1] == "plain" {
		spins := 0
		for {
			select {
			case v, ok := <-ch:
				if !ok {
					spins++
					if spins > 3 { // 안전 장치
						fmt.Println("close 뒤 select 에 다시 들어간 횟수:", spins, "받은 값:", got)
						return
					}
					break
				}
				got = append(got, v)
			}
		}
	}
loop:
	for {
		select {
		case v, ok := <-ch:
			if !ok {
				break loop
			}
			got = append(got, v)
		}
	}
	fmt.Println("라벨 break 뒤 줄 — 받은 값:", got)
}
```

<!-- ./prog plain && ./prog label -->

- `plain` 의 줄에 찍히는 횟수는? 안전 장치가 없었다면?
- `label` 의 줄은?
- 이 파일에 `go vet` 을 돌리면 무엇이 나오나 — 종료 코드는?

### 6. 빈 `select {}` (경계)

- 곁에 아무 고루틴도 없을 때 `select {}` 는 어떻게 끝나나? 상태 줄의 괄호 안에는?
- 곁에 `time.Sleep` 하는 고루틴이 있으면? 그 차이는 어느 층(명세·구현)의 것인가?
- 그렇다면 서버의 `main` 끝에 쓰는 `select {}` 는 교착인가?

### 7. 명세와 구현 (왜)

- 명세가 선택에 대해 쓰는 낱말은 무엇인가? 비율을 약속하나?
- 런타임은 무엇으로 순서를 섞나? `nil` 가지는 그 순서에서 어떻게 되나?
- 「먼저 적은 `case` 가 우선」이 틀린 이유를 격자의 어느 칸으로 보이나?

### 8. `default` 의 자리 (왜)

- 명세에서 `default` 가 뽑히는 조건을 한 낱말로 줄이면?
- `default` 를 **한 번만 시도**에 쓸 때와 **루프**에 쓸 때 무엇이 다른가?

### 9. 어느 것을 쓰나 (경계)

- 기다림에 상한을 두고 싶다 — 무엇을 쓰고, **무엇은 끊기지 않나**?
- 합친 채널 중 하나가 닫혔다 — 무엇을 하나?
- 루프를 끝내고 싶다 — 무엇을 쓰나?
- 우선순위가 있는 두 채널 — `select` 한 겹으로 되나?

### 10. 다른 주제와 (연결)

- (4)번 관용구는 29번 주제의 어느 두 사실에 기대나?
- 3번의 남은 고루틴은 31번 주제의 어느 누수 모양인가?
- `ctx.Done()` 을 `select` 가지로 쓸 수 있는 것은 그것이 무엇이기 때문인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

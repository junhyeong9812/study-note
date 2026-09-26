# go/syntax/33 — `sync/atomic` 과 `sync.Map` 을 고르는 자리 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ **모든 문제에서 「이것은 값 하나인가, 값 사이의 관계인가」를 먼저 적어라.**
> ★★ **「누가 이것을 잡아 주나 — 컴파일러·`-race`·런타임·아무도」를 매번 물어라.**
> 소스는 전부 `go build -trimpath -o prog .`(표시한 것은 `-race` · `GOARCH` 를 붙여) 로 빌드했다. 모듈 이름은 `ex` 다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 네 모양 × 세 방식 (예측)

```go
// t33grid.go
package main

import (
	"fmt"
	"os"
	"sync"
	"sync/atomic"
)

// 네 모양 × 세 방식. 인자: <모양> <방식>
//   모양 — counter · flag · pair · ptr
//   방식 — plain · atomic · mutex

type config struct{ x, y int } // 불변식: y == 2*x

func counter(how string) bool {
	var plain int64
	var at atomic.Int64
	var mu sync.Mutex
	var wg sync.WaitGroup
	for range 8 {
		wg.Go(func() {
			for range 10000 {
				switch how {
				case "plain":
					plain++
				case "atomic":
					at.Add(1)
				case "mutex":
					mu.Lock()
					plain++
					mu.Unlock()
				}
			}
		})
	}
	wg.Wait()
	if how == "atomic" {
		return at.Load() == 80000
	}
	return plain == 80000
}

func flag(how string) bool {
	var plain bool
	var at atomic.Bool
	var mu sync.Mutex
	go func() {
		switch how {
		case "plain":
			plain = true
		case "atomic":
			at.Store(true)
		case "mutex":
			mu.Lock()
			plain = true
			mu.Unlock()
		}
	}()
	for {
		switch how {
		case "plain":
			if plain {
				return true
			}
		case "atomic":
			if at.Load() {
				return true
			}
		case "mutex":
			mu.Lock()
			v := plain
			mu.Unlock()
			if v {
				return true
			}
		}
	}
}

// pair — 두 값 a, b 를 함께 옮긴다. 불변식: a+b == 0
func pair(how string) bool {
	var pa, pb int64
	var aa, ab atomic.Int64
	var mu sync.Mutex
	stop := make(chan struct{})
	go func() {
		for {
			select {
			case <-stop:
				return
			default:
			}
			switch how {
			case "plain":
				pa++
				pb--
			case "atomic":
				aa.Add(1)
				ab.Add(-1)
			case "mutex":
				mu.Lock()
				pa++
				pb--
				mu.Unlock()
			}
		}
	}()
	held := true
	for range 2_000_000 {
		var a, b int64
		switch how {
		case "plain":
			a, b = pa, pb
		case "atomic":
			a, b = aa.Load(), ab.Load()
		case "mutex":
			mu.Lock()
			a, b = pa, pb
			mu.Unlock()
		}
		if a+b != 0 {
			held = false
			break
		}
	}
	close(stop)
	return held
}

// ptr — 설정을 통째로 새로 만들어 포인터만 갈아 끼운다
func ptr(how string) bool {
	var plain *config = &config{1, 2}
	var at atomic.Pointer[config]
	at.Store(plain)
	var mu sync.Mutex
	stop := make(chan struct{})
	go func() {
		for i := 2; ; i++ {
			select {
			case <-stop:
				return
			default:
			}
			c := &config{i, 2 * i}
			switch how {
			case "plain":
				plain = c
			case "atomic":
				at.Store(c)
			case "mutex":
				mu.Lock()
				plain = c
				mu.Unlock()
			}
		}
	}()
	held := true
	for range 200_000 {
		var c *config
		switch how {
		case "plain":
			c = plain
		case "atomic":
			c = at.Load()
		case "mutex":
			mu.Lock()
			c = plain
			mu.Unlock()
		}
		if c.y != 2*c.x {
			held = false
			break
		}
	}
	close(stop)
	return held
}

func main() {
	shape, how := os.Args[1], os.Args[2]
	var held bool
	switch shape {
	case "counter":
		held = counter(how)
	case "flag":
		held = flag(how)
	case "pair":
		held = pair(how)
	case "ptr":
		held = ptr(how)
	}
	fmt.Println(held)
}
```

<!-- go build -race 후, 셸이 모양 × 방식 12칸을 돌려 칸마다 exit · -race 보고 예/아니오 · 불변식(plain 칸은 세지 않는다)을 찍고, 마지막 두 줄에 「atomic 과 Mutex 의 불변식이 갈린 모양 N / 4」·「-race 가 침묵했는데 불변식이 깨진 칸 N / 8」을 센다. -->

- `plain` 네 칸의 `-race` 보고와 종료 코드는?
- `atomic` 과 `Mutex` 가 **다른 답**을 내는 모양이 있나? 있다면 어느 것이고, 그 칸의 `-race` 는?
- 마지막 두 줄의 수는?

### 2. 386 에서 옛 함수와 새 타입 (예측)

```go
// t33align.go
package main

import (
	"fmt"
	"os"
	"sync/atomic"
	"unsafe"
)

type Old struct {
	flag int32
	n    int64 // 옛 함수 atomic.AddInt64 로 쓴다
}

type New struct {
	flag int32
	n    atomic.Int64
}

func main() {
	var o Old
	var w New
	fmt.Println("Old.n 오프셋:", unsafe.Offsetof(o.n), "· New.n 오프셋:", unsafe.Offsetof(w.n))
	if os.Args[1] == "new" {
		w.n.Add(1)
		fmt.Println("New:", w.n.Load())
		return
	}
	atomic.AddInt64(&o.n, 1)
	fmt.Println("Old:", o.n)
}
```

<!-- GOARCH=amd64 와 GOARCH=386 으로 각각 빌드해 이 amd64 리눅스에서 old · new 를 돌리고, 칸마다 exit · 첫 두 줄 · stderr 첫 줄을 찍는다. -->

- 네 칸의 오프셋과 결과는?
- 무엇이 갈리고, 왜 64비트에서만 테스트하면 못 보나?

### 3. 락 없는 맵과 `sync.Map` (예측)

```go
// t33map.go
package main

import (
	"fmt"
	"os"
	"sync"
)

func main() {
	m := map[int]int{}
	var sm sync.Map
	var wg sync.WaitGroup
	for g := range 2 {
		wg.Go(func() {
			for i := range 100_000 {
				if os.Args[1] == "map" {
					m[g*100_000+i] = i
				} else {
					sm.Store(g*100_000+i, i)
				}
			}
		})
	}
	wg.Wait()
	n := len(m)
	if os.Args[1] == "syncmap" {
		sm.Range(func(k, v any) bool { n++; return true })
	}
	fmt.Println("원소 수:", n)
}
```

<!-- 보통 빌드(-race 없음). map 칸은 최대 20판 돌려 fatal error 가 났나를 찍고, 그 판의 exit · stderr 첫 줄을 찍는다. 이어서 syncmap 칸. -->

- `map` 칸은 어떻게 끝나나? 그것은 `recover` 로 잡히나?
- `syncmap` 칸은?

### 4. 꺼낸 값에 1 을 더하면 (예측)

```go
// t33any.go
package main

import (
	"fmt"
	"sync"
)

func main() {
	var m sync.Map
	m.Store("hits", 1)
	v, _ := m.Load("hits")
	fmt.Println(v + 1)
}
```

- `go build` 는 무엇을 말하나?

### 5. 섞인 값과 단언 (예측)

```go
// t33assert.go
package main

import (
	"fmt"
	"sync"
)

func main() {
	var m sync.Map
	m.Store("hits", 1)
	m.Store("name", "gopher") // 값 타입이 섞여도 컴파일러는 모른다

	v, _ := m.Load("hits")
	fmt.Println("hits + 1 =", v.(int)+1)

	n, ok := m.Load("name")
	fmt.Println(`Load("name") 의 ok:`, ok)
	_, isInt := n.(int)
	fmt.Println("n.(int) 의 ok:", isInt)
	fmt.Println(n.(int) + 1)
}
```

- 출력은 어디까지 찍히고, 무엇으로 끝나나?
- comma-ok 단언과 패닉형 단언은 각각 무엇을 했나?

### 6. `sync.Map` 이 맞는 자리 (왜)

- `go doc sync.Map` 이 말하는 **두 패턴**은 무엇인가?
- 문서가 그 앞에서 **먼저 권하는 것**은 무엇이고, 그 이유 중 (1)번 문제와 이어지는 것은?

### 7. 원자 연산이 약속하는 것 (왜)

- 원자 연산 A 의 효과를 B 가 보면 둘 사이에는 무엇이 서나?
- 그 약속이 `a.Add(1); b.Add(-1)` 두 연산 **사이**에 대해 말하는 것은?

### 8. 포인터 교체는 왜 되나 (경계)

- `ptr` 모양은 `x`·`y` 두 값인데도 `atomic` 이 `true` 였다. `pair` 와 무엇이 다른가?
- 이미 `Store` 한 `config` 의 필드를 고치면 어느 모양이 되나?

### 9. 옛 함수형의 두 위험 (경계)

- `var x int64` + `atomic.AddInt64(&x, 1)` 에서, 새 타입 `atomic.Int64` 가 막아 주는 실수 **둘**은?

### 10. 속도 (경계)

- 「`atomic` 이 `Mutex` 보다 빠르다」·「`sync.Map` 이 빠르다」 — 이 문서가 그 판단을 해 주나? 문서의 「may significantly reduce lock contention」은 무엇에 대해 말한 것인가?

### 11. 자바와 (연결)

- 자바 55편의 「"각각 원자적"을 "함께 원자적"으로 읽는다」는 이 편의 어느 칸과 같은 실수인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

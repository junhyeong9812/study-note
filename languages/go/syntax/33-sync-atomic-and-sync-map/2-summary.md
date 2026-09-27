# go/syntax/33 — `sync/atomic` 과 `sync.Map` 을 고르는 자리 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [`sync/atomic`](https://pkg.go.dev/sync/atomic) · [`sync.Map`](https://pkg.go.dev/sync#Map) 문서 · [Go 메모리 모델](https://go.dev/ref/mem) · [Go 1.19 릴리스 노트](https://go.dev/doc/go1.19)(원자 타입·정렬 — **웹에서 열어 확인했다**).
> `go doc`·`api/go1NN.txt` 는 **이 툴체인의 `$(go env GOROOT)` 에서 직접 떴다.**\
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> ★ **버전** — `atomic.AddInt64` 같은 **함수**는 **1.0**(`api/go1.txt`), `atomic.Int64`·`atomic.Pointer[T]` **타입**은 **1.19**, `sync.Map` 은 **1.9**, `Swap`·`CompareAndSwap` **1.20**, `Clear` **1.23**((5)절 판 표).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체는 넷째 창이다** — 「**불변식을 셸이 참거짓으로 판정하고, 그 옆에 `-race` 보고를 나란히 적는 격자**」.
[32번 주제](../32-sync-mutex-rwmutex-waitgroup-once/)는 `-race` 를 **「경쟁이 있나」의 창**으로 썼다. 여기서는 그 창이 **답을 못 주는 자리**가 본론이다 —
★★★ **원자 연산 둘로 두 값을 옮기면 `-race` 는 침묵하는데 불변식은 깨진다**((1)절 — `-race 가 침묵했는데 불변식이 깨진 칸 1 / 8`).
경쟁이 없다는 것과 **맞다**는 것이 다른 질문이라는 것을 한 격자가 보인다.
★★ 그 짝으로 「**`GOARCH=386` 으로 빌드해 이 머신에서 돌린 32비트 창**」((3)절) — 브리핑은 「이 머신은 부적용」이라 했지만 **386 바이너리가 여기서 돈다.** 정렬 문제를 문서 인용이 아니라 **패닉으로** 보았다.

★★★ **이 주제의 경계** — [32번 주제](../32-sync-mutex-rwmutex-waitgroup-once/)가 `Mutex`·`WaitGroup`·`Once` 와 **`-race` 창의 첫 사용**의 정본이다. 여기서는 그 **결론을 받아** 「**락 대신 원자 연산으로 되는가**」만 묻는다.
원자 연산이 **순서를 세운다(synchronizes before)** 는 메모리 모델 쪽 이야기는 [36번 주제](../36-reading-the-go-memory-model-in-code/)가 정본이고, 검출기가 **무엇을 못 보나**는 [35번 주제](../35-data-races-and-the-race-detector/)가 정본이다.
CAS 루프·`LongAdder` 같은 원자 변수의 **일반론**은 자바 쪽 [`../../../java/syntax/55-atomics-and-concurrent-collections/`](../../../java/syntax/55-atomics-and-concurrent-collections/)가 자세하다 — 여기서는 **Go 의 타입과 문서가 약속하는 것**부터.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세·메모리 모델 보장** | 명세·메모리 모델이 약속한 것 | ★ **명세에는 `sync/atomic` 이 없다.** 메모리 모델이 「**원자 연산 A 의 효과를 B 가 보면 A 는 B 보다 먼저(synchronizes before)**」·「**순차 일관(sequentially consistent)**」을 정한다 |
| **표준 라이브러리 계약** | `sync/atomic`·`sync.Map` 문서가 약속한 것 | ★★★ 「**types [Int64] and [Uint64] are automatically aligned**」 · 32비트에서 옛 함수의 정렬은 **부르는 쪽 책임** · ★★★ `sync.Map` 이 맞는 **두 패턴**과 「**Most code should use a plain Go map instead**」 |
| **구현(runtime·도구)** | runtime·`-race` 가 한 것 | `panic: unaligned 64-bit atomic operation`(386) · `fatal error: concurrent map writes` · `-race` 의 보고/침묵 |
| **이 판의 관찰** | go1.27.1·linux/amd64(+386 바이너리) 에서 이번에 본 것 | 격자의 참거짓 · 오프셋 `4`/`8` |

★★★ **선을 긋는다** — 「원자 연산 **하나**는 쪼개지지 않고 순서를 세운다」는 **문서의 약속**이다.
「원자 연산 **둘**을 이어 쓰면 그 사이는 **아무도 안 지킨다**」는 그 약속에서 **나오는 결론**이고, `-race` 는 그 틈을 **원리상 못 본다**(두 접근이 전부 원자라 「순서 없는 접근」이 아니다).

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
```

```text
===== 명령: cd "$(go env GOROOT)/api" && grep -n "pkg sync/atomic, func AddInt64\|pkg sync/atomic, type \(Int64\|Pointer\)\|pkg sync, method (\*Map) \(Load\|Swap\|Clear\)(" go1.txt go1.9.txt go1.19.txt go1.20.txt go1.23.txt =====
go1.txt:5903:pkg sync/atomic, func AddInt64(*int64, int64) int64
go1.9.txt:139:pkg sync, method (*Map) Load(interface{}) (interface{}, bool)
go1.19.txt:286:pkg sync/atomic, type Int64 struct #50860
go1.19.txt:287:pkg sync/atomic, type Pointer[$0 interface{}] struct #50860
go1.20.txt:306:pkg sync, method (*Map) Swap(interface{}, interface{}) (interface{}, bool) #51972
go1.23.txt:100:pkg sync, method (*Map) Clear() #61696
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다(그래서 안 실었다)** | ★★ **경쟁 칸(`plain`)의 결과값** — 계수기가 몇을 잃었나, 쌍이 몇 번 어긋났나 | 스케줄링. 격자는 그 칸에 「**(경쟁 칸 — 안 셌다)**」 라고만 적는다 |
| **흔들린다(그래서 안 실었다)** | `concurrent map writes` 가 **몇 번째 판에서** 났나 | 「20판 안에 났나」 참거짓만 실었다 |
| 안 흔들린다 | ★★★ **격자의 `-race 보고=예/아니오` · 불변식 `true`/`false` · `1 / 4` · `1 / 8`** | 탐색 실행 여섯 번 + 제출 전 재실행에서 같았다 |
| 안 흔들린다 | ★★★ 386 의 **`Old.n 오프셋: 4`** · `panic: unaligned 64-bit atomic operation` · exit 2 | 레이아웃과 런타임 검사 |
| 안 흔들린다 | 컴파일 진단 `파일:줄:칸` · 패닉 문구 · `10` · `8000` · 종료 코드 | |

★ 정규화 규칙은 **기본 넷**만 썼다 — 이 편의 블록에는 고루틴 id·트레이스 인자가 실리지 않는다(패닉 트레이스의 `goroutine 1` 은 main 이라 안 흔들린다).

## 한눈에 — 쉽게 말하면

**원자 연산은 「한 번에 한 칸만 고치는 도장」이다.** 도장 한 번은 절대 반쯤 찍히지 않는다.
그런데 **장부 두 칸을 같이 고쳐야** 하는 일(한쪽에서 빼서 다른 쪽에 더하기)에 도장을 **두 번** 찍으면 —
**두 도장 사이에 누가 장부를 보면** 돈이 사라진 것처럼 보인다. 도장은 각각 멀쩡했으니 **감사관(`-race`)은 아무 말도 안 한다.**

| 비유 | 실체 |
|---|---|
| 한 칸 고치는 도장 | ★★ **`atomic.Int64.Add`·`atomic.Bool.Store`** — 한 연산은 쪼개지지 않는다 |
| 두 칸을 도장 두 번으로 | ★★★ **`a.Add(1); b.Add(-1)`** — 사이에서 `a+b != 0` 이 보인다((1)절 `pair / atomic`) |
| 감사관은 도장이 **제대로 찍혔나**만 본다 | ★★★ **`-race` 는 침묵** — 모든 접근이 원자라 「동기화 없는 접근」이 아니다 |
| 장부를 **통째로 새로 써서** 걸어 둔 것을 **바꿔 건다** | ★★ **`atomic.Pointer[T]`** — 새 값을 다 만든 뒤 포인터만 갈아 끼운다((1)절 `ptr / atomic`) |
| 금고 한 칸을 열려면 **자물쇠 위치가 맞아야** 하는 옛 금고 | ★★ **32비트의 `atomic.AddInt64(&s.n)`** — `n` 이 8바이트 경계에 없으면 패닉((3)절) |
| 칸마다 따로 잠그는 **공용 사물함** | ★ **`sync.Map`** — 단 **라벨이 없다**(`any`) — 무엇이 들었는지는 꺼내 봐야 안다((4)절) |

```text
   ★★★ 원자로 충분한가 — 네 모양 × 세 방식 ((1)절의 실측, -race 빌드)

   모양                          plain(동기화 없음)   atomic                     Mutex
   ───────────────────────────   ──────────────────   ────────────────────────   ─────────────
   계수기  n++ 8×10000           -race 보고           침묵 · 80000 맞음           침묵 · 맞음
   플래그  한 번 세운다           -race 보고           침묵 · 봤다                 침묵 · 봤다
   ★ 쌍   a+1, b-1 (합 0 유지)   -race 보고           ★ 침묵 · 합이 0 이 아닌 걸 봤다   침묵 · 늘 0
   포인터  설정을 통째로 갈기      -race 보고           침묵 · y == 2x 늘 참         침묵 · 참

   → 원자가 Mutex 와 갈린 모양 1 / 4 · -race 가 침묵했는데 불변식이 깨진 칸 1 / 8
```

> **원자 연산(atomic operation)** — 다른 고루틴이 **중간 상태를 볼 수 없는** 한 번의 읽기·쓰기·더하기·바꾸기. Go 에서는 `sync/atomic` 패키지가 준다.

> **불변식(invariant)** — 「언제 보아도 참이어야 하는 관계」. 여기서는 `a+b == 0`, `y == 2*x`, 「계수기가 80000」.

- [32번 주제](../32-sync-mutex-rwmutex-waitgroup-once/)가 목록상 **선행**이다 — 거기서 `n++` 을 `Mutex` 로 고쳤다. 여기서는 **같은 자리를 원자 연산으로 고치면 어디까지 되나**를 묻는다.
- ★★ [32번 주제](../32-sync-mutex-rwmutex-waitgroup-once/) (3)절이 **`atomic.Int64` 도 복사하면 `vet copylocks` 가 잡는다**(p13 — `sync/atomic.noCopy`)를 이미 보였다 — 여기서는 **다시 재지 않았다.**

## 이 주제가 답하려는 질문

1. **원자 연산으로 충분한 것과 아닌 것을 무엇이 가르나** — 「값 하나」냐 「값 사이의 관계」냐.
2. **옛 함수(`atomic.AddInt64`)와 새 타입(`atomic.Int64`)은 무엇이 다른가** — 정렬과 「실수로 평범하게 읽기」.
3. **`sync.Map` 은 언제 이기고, 무엇을 잃나** — 문서가 말하는 두 패턴과 **타입 정보**. 성능 주장 **없이**.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **불변식 참거짓 × `-race` 보고 격자** | **원자로 충분한가** — 네 모양 × 세 방식 | ★ 본체 창 — 마지막 줄 `1 / 8` 을 스크립트가 센다 |
| ★★ **`GOARCH=386` 바이너리** | 32비트에서의 **정렬 패닉** | ★ **제5의 상태** — 「문서만 인용」이 될 뻔한 질문을 **다른 판의 실행**으로 물었다 |
| ★★ **`go doc` 원문** | `sync.Map` 의 두 패턴 · 원자 연산의 메모리 모델 문장 · 32비트 BUG 문단 | 이 툴체인 |
| ★ **컴파일 진단 · 패닉** | `sync.Map` 이 `any` 라는 것의 대가 | (4)절 |
| ★ **`fatal error: concurrent map writes`** | 락 없는 맵은 **런타임이** 잡는다(`-race` 없이도) | (4)절 |
| ★ **`api/go1NN.txt`** | 판 경계 | [24번 주제](../24-error-wrapping-and-errors-is-as-join/)의 방식 |
| **부적용 — 시간·처리량** | ★★★ **안 쟀다.** 「`atomic` 이 `Mutex` 보다 빠르다」·「`sync.Map` 이 빠르다」를 이 문서는 **적지 않는다.** 문서의 「**may significantly reduce lock contention**」은 **문서의 문장**으로만 인용한다 | — |
| **부적용 — 복사 금지** | [32번 주제](../32-sync-mutex-rwmutex-waitgroup-once/) (3)절 p13 | — |

### (1) ★★★ 원자로 충분한가 — 네 모양 × 세 방식

**언제 쓰나** — 「락 대신 `atomic` 으로 바꿔도 되나」를 코드 리뷰에서 물을 때. **같은 문제를 세 방식으로** 풀어 `-race` 빌드에서 돌렸다.

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

```text
===== 소스: t33grid.go =====
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
===== 명령: go build -race -trimpath -o prog . && bad=0; silent=0; split=0; for s in counter flag pair ptr; do ia=; im=; for h in plain atomic mutex; do r=$(./prog $s $h 2>err.txt); rc=$?; rep=아니오; if grep -q "DATA RACE" err.txt; then rep=예; fi; if [ $h = plain ]; then inv="(경쟁 칸 — 안 셌다)"; else inv=$r; silent=$((silent+1)); if [ $rep = 아니오 ] && [ "$r" = false ]; then bad=$((bad+1)); fi; fi; [ $h = atomic ] && ia=$r; [ $h = mutex ] && im=$r; echo "[$s / $h] exit=$rc · -race 보고=$rep · 불변식 지켜졌나=$inv"; done; [ "$ia" != "$im" ] && split=$((split+1)); done; echo "atomic 과 Mutex 의 불변식이 갈린 모양 $split / 4"; echo "-race 가 침묵했는데 불변식이 깨진 칸 $bad / $silent" =====
[counter / plain] exit=66 · -race 보고=예 · 불변식 지켜졌나=(경쟁 칸 — 안 셌다)
[counter / atomic] exit=0 · -race 보고=아니오 · 불변식 지켜졌나=true
[counter / mutex] exit=0 · -race 보고=아니오 · 불변식 지켜졌나=true
[flag / plain] exit=66 · -race 보고=예 · 불변식 지켜졌나=(경쟁 칸 — 안 셌다)
[flag / atomic] exit=0 · -race 보고=아니오 · 불변식 지켜졌나=true
[flag / mutex] exit=0 · -race 보고=아니오 · 불변식 지켜졌나=true
[pair / plain] exit=66 · -race 보고=예 · 불변식 지켜졌나=(경쟁 칸 — 안 셌다)
[pair / atomic] exit=0 · -race 보고=아니오 · 불변식 지켜졌나=false
[pair / mutex] exit=0 · -race 보고=아니오 · 불변식 지켜졌나=true
[ptr / plain] exit=66 · -race 보고=예 · 불변식 지켜졌나=(경쟁 칸 — 안 셌다)
[ptr / atomic] exit=0 · -race 보고=아니오 · 불변식 지켜졌나=true
[ptr / mutex] exit=0 · -race 보고=아니오 · 불변식 지켜졌나=true
atomic 과 Mutex 의 불변식이 갈린 모양 1 / 4
-race 가 침묵했는데 불변식이 깨진 칸 1 / 8
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`plain` 넷은 전부 `-race 보고=예`, exit 66** — 동기화가 없으니 당연하다. 그 칸의 결과값은 **흔들리므로 안 셌다.**
- ★★★ **`counter`·`flag`·`ptr` — `atomic` 과 `Mutex` 가 같다**(`true`, 보고 없음). **값 하나**(계수기 하나 · 깃발 하나 · 포인터 하나)를 다루는 한 원자 연산으로 **충분했다.**
- ★★★ **`pair / atomic` 만 `-race 보고=아니오 · 불변식 지켜졌나=false`.** 쓰는 쪽은 `aa.Add(1)` 과 `ab.Add(-1)` 을 **따로** 한다.
  읽는 쪽이 그 **사이**에 `aa.Load()`·`ab.Load()` 를 하면 합이 `1` 이다. 두 연산은 **각각 원자**지만 **함께 원자가 아니다.**
  ★★★ **그리고 `-race` 는 아무 말도 안 한다** — 모든 접근이 원자 연산이라 검출기가 볼 「동기화 없는 접근」이 없다. **경쟁이 없는 것과 맞는 것은 다르다.**
- ★★★ **`pair / mutex` 는 `true`** — 두 값을 **한 임계 구역**에서 고치고 읽으니 중간 상태가 안 보인다.

```text
   ★★★ pair / atomic — 두 도장 사이에 읽는 쪽이 끼면

   쓰는 고루틴   aa.Add(1) ───────────────────────────── ab.Add(-1)
                  a=1, b=0          ▲                     a=1, b=-1
   읽는 고루틴                  aa.Load()=1 · ab.Load()=0      → a+b = 1  (불변식 깨짐)
                               각 연산은 원자 · 둘 사이는 누구의 것도 아니다
   -race        모든 접근이 원자 연산 → 「순서 없는 평범한 접근」 없음 → 침묵

   pair / mutex  Lock ─ pa++ ─ pb-- ─ Unlock   ·   Lock ─ 읽기 ─ Unlock   → 중간이 안 보인다
```
- ★★ **`ptr / atomic` 은 `true`** — 두 값(`x`, `y`)이 있는데도 된다. **새 `config` 를 다 만든 뒤** 포인터 **하나**만 `Store` 하기 때문이다. 「두 값」을 「**값 하나(포인터)**」로 바꾼 것이 요령이다.
  ★ 단 **이미 걸린 `config` 를 고치면** 안 된다 — 그 순간 `pair` 와 같은 모양이 된다(이 문서는 그 칸을 **안 던졌다**).
- ★★★ **마지막 두 줄 — `atomic 과 Mutex 의 불변식이 갈린 모양 1 / 4` · `-race 가 침묵했는데 불변식이 깨진 칸 1 / 8`.** 스크립트가 셌다.

원자 연산이 무엇을 약속하나 — 문서:

```text
===== 명령: go doc sync/atomic | sed -n "36,41p;97,107p" =====
In the terminology of the Go memory model, if the effect of an atomic
operation A is observed by atomic operation B, then A “synchronizes before” B.
Additionally, all the atomic operations executed in a program behave as though
executed in some sequentially consistent order. This definition provides the
same semantics as C++'s sequentially consistent atomics and Java's volatile
variables.
BUG: On 386, the 64-bit functions use instructions unavailable before the Pentium MMX.

On non-Linux ARM, the 64-bit functions use instructions unavailable before the ARMv6k core.

On ARM, 386, and 32-bit MIPS, it is the caller's responsibility to arrange
for 64-bit alignment of 64-bit words accessed atomically via the primitive
atomic functions (types [Int64] and [Uint64] are automatically aligned).
The first word in an allocated struct, array, or slice; in a global
variable; or in a local variable (because on 32-bit architectures, the
subject of 64-bit atomic operations will escape to the heap) can be
relied upon to be 64-bit aligned.
(exit 0)
```

- ★★★ 첫 문단 — 「**if the effect of an atomic operation A is observed by atomic operation B, then A "synchronizes before" B**」 · 「**sequentially consistent order**」 · 「**same semantics as C++'s sequentially consistent atomics and Java's volatile variables**」.
  그래서 `flag / atomic` 에서 깃발을 본 쪽은 **깃발 앞의 쓰기도 본다** — 이 「순서」 쪽 이야기는 [36번 주제](../36-reading-the-go-memory-model-in-code/)가 정본이다.
- ★★ **「약속하는 것은 연산 하나」다** — 두 연산 사이에 대해서는 문서가 **아무것도 말하지 않는다.** `pair` 의 결과가 그 공백이다.
- 자바도 같다 — [`../../../java/syntax/55-atomics-and-concurrent-collections/`](../../../java/syntax/55-atomics-and-concurrent-collections/) 「어디서 틀리나」 2·4번(「원자 연산 둘을 이어 붙인다」·「"각각 원자적"을 "함께 원자적"으로 읽는다」).

비용 — **안 쟀다.** 「`atomic` 이 `Mutex` 보다 빠르다」는 이 격자의 결론이 **아니다.**

### (2) ★★ 새 타입 대 옛 함수 — 「평범하게 읽을 수 없다」

- ★★ 1.19 의 **`atomic.Int64`·`atomic.Bool`·`atomic.Pointer[T]`** 는 값을 **비공개 필드에 숨긴다** — `at.Load()` 말고는 읽을 길이 없다.
  옛 함수형(`var x int64` + `atomic.AddInt64(&x, 1)`)은 **`x` 를 평범하게 읽는 코드도 컴파일된다.**
- ★★★ 그 「평범한 읽기」가 곧 경쟁이다 — 원자로 쓰고 평범하게 읽은 칸은 [35번 주제](../35-data-races-and-the-race-detector/) (1)절 격자의 **`mixed` 칸**(`-race 보고=예`)이 실측이다.
- ★ Go 1.19 릴리스 노트(웹) — 「**These types hide the underlying values so that all accesses are forced to use the atomic APIs.**」

### (3) ★★★ 정렬 — 32비트에서만, 그런데 이 머신에서 돌려 봤다

**언제 쓰나** — 구조체 필드를 옛 함수 `atomic.AddInt64(&s.n, …)` 로 다룰 때. **문서가 먼저 말한다**(위 블록의 BUG 문단):
「**On ARM, 386, and 32-bit MIPS, it is the caller's responsibility to arrange for 64-bit alignment … (types [Int64] and [Uint64] are automatically aligned).**」

★ 브리핑은 이것을 「32비트에서만 — 이 머신은 부적용, 문서 인용」으로 두었다. **그런데 `GOARCH=386` 으로 빌드한 바이너리가 이 amd64 리눅스에서 돈다** — 그래서 던졌다:

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

```text
===== 소스: t33align.go =====
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
===== 명령: for a in amd64 386; do GOARCH=$a go build -trimpath -o prog-$a . || exit 1; echo "[GOARCH=$a] $(file -b prog-$a | cut -d, -f1)"; for m in old new; do ./prog-$a $m >out.txt 2>err.txt; rc=$?; echo "[GOARCH=$a $m] exit=$rc · $(sed -n 1p out.txt) · $(sed -n 2p out.txt) · stderr 첫 줄: $(sed -n 1p err.txt)"; done; done =====
[GOARCH=amd64] ELF 64-bit LSB executable
[GOARCH=amd64 old] exit=0 · Old.n 오프셋: 8 · New.n 오프셋: 8 · Old: 1 · stderr 첫 줄: 
[GOARCH=amd64 new] exit=0 · Old.n 오프셋: 8 · New.n 오프셋: 8 · New: 1 · stderr 첫 줄: 
[GOARCH=386] ELF 32-bit LSB executable
[GOARCH=386 old] exit=2 · Old.n 오프셋: 4 · New.n 오프셋: 8 ·  · stderr 첫 줄: panic: unaligned 64-bit atomic operation
[GOARCH=386 new] exit=0 · Old.n 오프셋: 4 · New.n 오프셋: 8 · New: 1 · stderr 첫 줄: 
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`[GOARCH=386 old] exit=2 · Old.n 오프셋: 4 · … panic: unaligned 64-bit atomic operation`** — `int32` 뒤의 `int64` 가 **4바이트 자리**에 놓였고, 옛 함수가 **패닉**했다.
- ★★★ **`[GOARCH=386 new] … New.n 오프셋: 8 · New: 1`** — 같은 `int32` 뒤인데 **`atomic.Int64` 는 8 에 놓였다.** 문서의 「automatically aligned」가 이것이다.
- ★★ **amd64 에서는 둘 다 8, 둘 다 된다** — 64비트에서는 `int64` 가 원래 8바이트 경계에 놓인다. 그래서 **64비트 머신에서만 테스트하면 이 버그를 영원히 못 본다.**
- ★ `ELF 32-bit LSB executable` — 실제로 32비트 바이너리였다는 판별 줄이다. 커널이 32비트 실행을 받아 주는 **이 머신의 성질**이다(없는 환경에서는 이 블록이 `exec format error` 로 끝난다 — 확인은 안 했다).
- ★★ **고치는 법** — 새 타입을 쓴다. 옛 함수를 써야 하면 **문서대로 그 필드를 구조체의 첫 자리**에 둔다(「The first word in an allocated struct … can be relied upon to be 64-bit aligned」 — 이 배치는 **그 처방을 블록으로 안 던졌다**).

비용 — 없다.

### (4) ★★ `sync.Map` — 문서가 말하는 두 패턴, 그리고 잃는 것

**언제 쓰나** — 여러 고루틴이 **맵 하나**를 만질 때. 먼저 **락 없는 보통 맵**은 —

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

```text
===== 소스: t33map.go =====
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
===== 명령: go build -trimpath -o prog . && found=아니오; for i in $(seq 20); do ./prog map >out.txt 2>err.txt; rc=$?; if grep -q "concurrent map writes" err.txt; then found=예; break; fi; done; echo "[map] 20판 안에 fatal error 로 끝난 판이 있었나: $found"; echo "[map] 그 판 exit=$rc · stdout: $(cat out.txt) · stderr 첫 줄: $(sed -n 1p err.txt)"; ./prog syncmap; echo "[syncmap] exit=$?" =====
[map] 20판 안에 fatal error 로 끝난 판이 있었나: 예
[map] 그 판 exit=2 · stdout:  · stderr 첫 줄: fatal error: concurrent map writes
원소 수: 200000
[syncmap] exit=0
(exit 0)
```

- ★★★ **`fatal error: concurrent map writes`, exit 2** — `-race` 없이 **보통 빌드에서** 런타임이 잡았다. `panic` 이 아니라 **`fatal error`** 라 `recover` 로 못 잡는다([32번 주제](../32-sync-mutex-rwmutex-waitgroup-once/) (8)절과 같은 종류).
  ★ 이것은 **런타임의 최선 노력 검사**(구현)다 — 20판 안에 **났다**는 것만 실었다. 「늘 잡는다」는 **주장하지 않는다.**
- ★★ `syncmap` 칸은 **`원소 수: 200000`**, exit 0.

그러면 `sync.Map` 을 쓰면 되나 — **문서가 먼저 말린다**:

```text
===== 명령: go doc sync.Map | sed -n "6,32p" =====
    Map is like a Go map[any]any but is safe for concurrent use by multiple
    goroutines without additional locking or coordination. Loads, stores,
    and deletes run in amortized constant time.

    The Map type is specialized. Most code should use a plain Go map instead,
    with separate locking or coordination, for better type safety and to make it
    easier to maintain other invariants along with the map content.

    The Map type is optimized for two common use cases: (1) when the entry for
    a given key is only ever written once but read many times, as in caches
    that only grow, or (2) when multiple goroutines read, write, and overwrite
    entries for disjoint sets of keys. In these two cases, use of a Map may
    significantly reduce lock contention compared to a Go map paired with a
    separate Mutex or RWMutex.

    The zero Map is empty and ready for use. A Map must not be copied after
    first use.

    In the terminology of the Go memory model, Map arranges that a write
    operation “synchronizes before” any read operation that observes the effect
    of the write, where read and write operations are defined as follows.
    Map.Load, Map.LoadAndDelete, Map.LoadOrStore, Map.Swap, Map.CompareAndSwap,
    and Map.CompareAndDelete are read operations; Map.Delete, Map.LoadAndDelete,
    Map.Store, and Map.Swap are write operations; Map.LoadOrStore is a write
    operation when it returns loaded set to false; Map.CompareAndSwap is a write
    operation when it returns swapped set to true; and Map.CompareAndDelete is a
    write operation when it returns deleted set to true.
(exit 0)
```

- ★★★ 「**The Map type is specialized. Most code should use a plain Go map instead, with separate locking or coordination, for better type safety and to make it easier to maintain other invariants along with the map content.**」
  기본값은 **보통 맵 + `Mutex`** 다. **(1)절의 `pair` 와 같은 이유**가 문장에 들어 있다 — 「맵 내용과 **다른 불변식을 함께** 지키기 쉽다」.
- ★★★ **이기는 두 패턴** — 「**(1) when the entry for a given key is only ever written once but read many times, as in caches that only grow, or (2) when multiple goroutines read, write, and overwrite entries for disjoint sets of keys.**」
  그리고 「**may significantly reduce lock contention**」 — ★ **문서의 문장이다. 이 문서는 재지 않았다.**
- ★★ 마지막 문단 — `Store` 같은 쓰기가 그 효과를 **본** `Load` 보다 **먼저(synchronizes before)** — 그래서 `sync.Map` 에 넣은 값을 꺼낸 쪽은 **넣기 전의 쓰기도 본다.**

두 패턴을 그대로 짜서 `-race` 빌드로 —

```go
// t33patterns.go
package main

import (
	"fmt"
	"sync"
)

// 패턴 (1) — 한 번 쓰고 여러 번 읽는 키: LoadOrStore 로 채우는 캐시
// 패턴 (2) — 고루틴마다 겹치지 않는 키 집합
func main() {
	var cache sync.Map
	var built sync.Map // 키마다 값을 만든 횟수
	var wg sync.WaitGroup
	for range 50 {
		wg.Go(func() {
			for k := range 10 {
				if _, ok := cache.Load(k); ok {
					continue
				}
				v, loaded := cache.LoadOrStore(k, k*k)
				if !loaded {
					built.Store(k, v)
				}
			}
		})
	}
	wg.Wait()
	n := 0
	built.Range(func(k, v any) bool { n++; return true })
	fmt.Println("(1) 키 10 개 · 50 고루틴 · LoadOrStore 가 새로 넣은 횟수:", n)

	var own sync.Map
	for g := range 8 {
		wg.Go(func() {
			for i := range 1000 {
				own.Store(g*1000+i, g) // 고루틴 g 만 이 범위의 키를 쓴다
			}
		})
	}
	wg.Wait()
	cnt := 0
	own.Range(func(k, v any) bool { cnt++; return true })
	fmt.Println("(2) 고루틴 8 개 × 겹치지 않는 키 1000 개 · 원소 수:", cnt)
}
```

```text
===== 소스: t33patterns.go =====
package main

import (
	"fmt"
	"sync"
)

// 패턴 (1) — 한 번 쓰고 여러 번 읽는 키: LoadOrStore 로 채우는 캐시
// 패턴 (2) — 고루틴마다 겹치지 않는 키 집합
func main() {
	var cache sync.Map
	var built sync.Map // 키마다 값을 만든 횟수
	var wg sync.WaitGroup
	for range 50 {
		wg.Go(func() {
			for k := range 10 {
				if _, ok := cache.Load(k); ok {
					continue
				}
				v, loaded := cache.LoadOrStore(k, k*k)
				if !loaded {
					built.Store(k, v)
				}
			}
		})
	}
	wg.Wait()
	n := 0
	built.Range(func(k, v any) bool { n++; return true })
	fmt.Println("(1) 키 10 개 · 50 고루틴 · LoadOrStore 가 새로 넣은 횟수:", n)

	var own sync.Map
	for g := range 8 {
		wg.Go(func() {
			for i := range 1000 {
				own.Store(g*1000+i, g) // 고루틴 g 만 이 범위의 키를 쓴다
			}
		})
	}
	wg.Wait()
	cnt := 0
	own.Range(func(k, v any) bool { cnt++; return true })
	fmt.Println("(2) 고루틴 8 개 × 겹치지 않는 키 1000 개 · 원소 수:", cnt)
}
===== 명령: go build -race -trimpath -o prog . && ./prog =====
(1) 키 10 개 · 50 고루틴 · LoadOrStore 가 새로 넣은 횟수: 10
(2) 고루틴 8 개 × 겹치지 않는 키 1000 개 · 원소 수: 8000
(exit 0)
```

- ★★ **(1) `LoadOrStore 가 새로 넣은 횟수: 10`** — 50 고루틴이 같은 키 10 개를 동시에 채워도 **키마다 한 번만** 들어갔다(`loaded=false` 인 쪽이 하나).
- ★★ **(2) `원소 수: 8000`** — 겹치지 않는 키. 두 패턴 모두 **`-race` 보고 0 줄, exit 0.**
- ★ 이 블록은 **정확성**만 보인다 — 「이 두 패턴에서 `sync.Map` 이 `Mutex` 맵보다 **빠르다**」는 **안 쟀다.**

**잃는 것 — 타입.** `sync.Map` 의 키와 값은 **`any`** 다:

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

```text
===== 소스: t33any.go =====
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
===== 명령: go build -trimpath -o prog . =====
# ex
./t33any.go:12:14: invalid operation: v + 1 (mismatched types any and untyped int)
(exit 1)
```

- ★★★ **`invalid operation: v + 1 (mismatched types any and untyped int)`**(12행 14칸) — 꺼낸 값은 `any` 라 **단언 없이는 못 쓴다.** 보통 `map[string]int` 였으면 없었을 에러다.

단언을 붙이면 컴파일은 된다 — 그리고 **틀린 단언은 실행 중에야** 드러난다:

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

```text
===== 소스: t33assert.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog 2>&1 =====
hits + 1 = 2
Load("name") 의 ok: true
n.(int) 의 ok: false
panic: interface conversion: interface {} is string, not int

goroutine 1 [running]:
main.main()
	ex/t33assert.go:20 +0x2a5
(exit 2)
```

- ★★★ **`panic: interface conversion: interface {} is string, not int`**, exit 2 — `Store` 가 **값 타입이 섞여도** 받아 줬고(`m.Store("name", "gopher")`), 틀린 것은 **꺼낼 때** 드러났다.
  ★ comma-ok 단언(`_, isInt := n.(int)`)은 **`false`** 로 조용히 답했다([22번 주제](../22-type-assertion-any-and-comparable/)의 두 형태).
- ★★ 이것이 문서의 「**for better type safety**」가 말하는 값이다 — 보통 맵은 **컴파일러가** 막고, `sync.Map` 은 **실행이** 막는다.
- ★ 단언의 **시간 비용**은 **안 쟀다.**

비용 — **안 쟀다.**

### (5) ★ 판 경계 — `api/go1NN.txt`

(머리말 「이 판」의 블록.)

| API | 판 | 근거 |
|---|---|---|
| `atomic.AddInt64` 등 **함수** | **1.0** | `go1.txt:5903` |
| `sync.Map`(`Load`…) | **1.9** | `go1.9.txt:139` |
| **`atomic.Int64`·`atomic.Pointer[T]`**(·`Bool`·`Int32` …) | **1.19** | `go1.19.txt:286-287` |
| `Map.Swap`·`CompareAndSwap`·`CompareAndDelete` | **1.20** | `go1.20.txt:306` |
| `Map.Clear` | **1.23** | `go1.23.txt:100` |

- ★ `Map.Clear` 을 `go 1.22` 모듈에서 쓰면 **`go vet` 의 `stdversion` 분석기가** 말한다 — 그 판 격자는 [34번 주제](../34-context-cancellation-deadlines-and-values/) (6)절에 있다(컴파일러는 **통과시킨다**).

## 문법 — 형태와 규칙

### 형태

```go
// t33patterns.go
package main

import (
	"fmt"
	"sync"
)

// 패턴 (1) — 한 번 쓰고 여러 번 읽는 키: LoadOrStore 로 채우는 캐시
// 패턴 (2) — 고루틴마다 겹치지 않는 키 집합
func main() {
	var cache sync.Map
	var built sync.Map // 키마다 값을 만든 횟수
	var wg sync.WaitGroup
	for range 50 {
		wg.Go(func() {
			for k := range 10 {
				if _, ok := cache.Load(k); ok {
					continue
				}
				v, loaded := cache.LoadOrStore(k, k*k)
				if !loaded {
					built.Store(k, v)
				}
			}
		})
	}
	wg.Wait()
	n := 0
	built.Range(func(k, v any) bool { n++; return true })
	fmt.Println("(1) 키 10 개 · 50 고루틴 · LoadOrStore 가 새로 넣은 횟수:", n)

	var own sync.Map
	for g := range 8 {
		wg.Go(func() {
			for i := range 1000 {
				own.Store(g*1000+i, g) // 고루틴 g 만 이 범위의 키를 쓴다
			}
		})
	}
	wg.Wait()
	cnt := 0
	own.Range(func(k, v any) bool { cnt++; return true })
	fmt.Println("(2) 고루틴 8 개 × 겹치지 않는 키 1000 개 · 원소 수:", cnt)
}
```

규칙 불릿.

- ★★★ **값 하나**(계수기·깃발·포인터)면 **`atomic.Int64`·`atomic.Bool`·`atomic.Pointer[T]`**.
- ★★★ **값 사이의 관계**(두 필드의 합·짝)를 지켜야 하면 **`Mutex`** — 또는 **새 값을 통째로 만들어 `atomic.Pointer` 로 갈아 끼운다.**
- ★★ **새 코드는 타입(1.19+)** — 옛 함수(`atomic.AddInt64(&x, …)`)는 **평범한 읽기**를 막지 못하고 **32비트 정렬**을 부르는 쪽에 떠넘긴다.
- ★★ **`sync.Map` 은 문서의 두 패턴에서만** — 나머지는 **`map` + `Mutex`**. 꺼낸 값은 **comma-ok 단언**으로.
- ★ 원자 타입도 **복사하지 않는다**([32번 주제](../32-sync-mutex-rwmutex-waitgroup-once/) p13).

### 금지 사례 — 컴파일은 되고 실행·도구가 잡거나 아무도 안 잡는 것

| 쓴 꼴 | 누가 잡나 | 어디서 |
|---|---|---|
| `a.Add(1); b.Add(-1)` 로 두 값을 함께 옮기기 | ★★★ **아무도 안 잡는다**(`-race` 침묵, 불변식만 깨짐) | (1)절 `pair / atomic` |
| 386 에서 `int32` 뒤 `int64` 에 `atomic.AddInt64` | 런타임 — `panic: unaligned 64-bit atomic operation` | (3)절 |
| 락 없는 `map` 에 여러 고루틴이 쓰기 | 런타임 — `fatal error: concurrent map writes`(최선 노력) | (4)절 |
| `sync.Map` 에서 꺼낸 값을 틀린 타입으로 단언 | 런타임 — `panic: interface conversion` | (4)절 |
| 원자로 쓰고 평범하게 읽기(옛 함수형) | `-race` | [35번 주제](../35-data-races-and-the-race-detector/) `mixed` 칸 |

| 쓴 꼴 | 진단 | 어디서 |
|---|---|---|
| `v, _ := m.Load("hits"); v + 1` | `invalid operation: v + 1 (mismatched types any and untyped int)` | (4)절 |

## 어디서 틀리나

### 1. ★★★ 「필드마다 `atomic` 이니 구조체도 안전하다」

- (1)절 실측 — **`pair / atomic` 이 `false`** 인데 **`-race` 는 침묵.**
- 고치는 법 — 관계를 지키려면 **`Mutex`**, 또는 **통째로 새로 만들어 포인터 교체**.

### 2. ★★★ 「`-race` 가 조용하니 맞다」

- (1)절 — `-race` 는 **경쟁**을 본다. **불변식**은 안 본다. 원자 연산만 쓴 코드는 **틀려도 조용하다.**

### 3. ★★ 「64비트에서 테스트했으니 됐다」

- (3)절 실측 — **amd64 는 오프셋 8 이라 되고, 386 은 4 라 패닉.** 옛 함수는 **판(아키텍처)** 을 탄다.
- 고치는 법 — **`atomic.Int64`**(자동 정렬).

### 4. ★★ 「동시에 쓰는 맵이면 `sync.Map`」

- (4)절 문서 — 「**Most code should use a plain Go map instead**」. 두 패턴이 아니면 **`map` + `Mutex`** 가 기본이다.

### 5. ★★ 「`sync.Map` 이 빠르다」·「`atomic` 이 `Mutex` 보다 빠르다」

- ★★★ **이 배치는 안 쟀다.** 문서의 「may significantly reduce lock contention」은 **문서의 문장**이다 — **두 패턴 안에서**, **경합에 대해** 말한 것이다.

### 6. ★ 「`sync.Map` 에서 꺼낸 값은 넣은 타입 그대로다」

- (4)절 — 꺼낸 것은 **`any`** 다. 틀린 단언은 **실행 중 패닉.**

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| **원자 연산 A 를 B 가 보면 A 가 먼저 · 순차 일관** | **메모리 모델 보장** | (1)절 문서 · [36번 주제](../36-reading-the-go-memory-model-in-code/) |
| ★★★ **원자 연산 둘 사이는 아무것도 약속되지 않는다** | **보장에서 나오는 결론** | (1)절 `pair` |
| ★★ **`Int64`·`Uint64` 는 자동 정렬 · 옛 함수의 정렬은 부르는 쪽 책임(32비트)** | **표준 라이브러리 계약** | (3)절 |
| `sync.Map` 의 두 패턴 · 「보통 맵을 써라」 · `Store` 가 `Load` 보다 먼저 | **표준 라이브러리 계약** | (4)절 |
| `panic: unaligned 64-bit atomic operation` | **구현(runtime, 386)** | (3)절 |
| `fatal error: concurrent map writes` | **구현(runtime) — 최선 노력** | (4)절 |
| `-race` 가 원자 연산만의 코드에 침묵 | **도구(검출기)** | (1)절 |
| 386 바이너리가 이 머신에서 돈다 | **이 머신의 성질** | (3)절 |
| 원자·`sync.Map`·단언의 **시간** | ★ **안 쟀다** | — |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 요청 수 세기 · 종료 깃발 | **`atomic.Int64`·`atomic.Bool`** | 값 하나 — (1)절 |
| 자주 읽고 가끔 통째로 바뀌는 설정 | **`atomic.Pointer[Config]`** — 새 값을 다 만든 뒤 `Store` | (1)절 `ptr` |
| 두 필드를 함께 바꾼다 | **`Mutex`** | (1)절 `pair` |
| 한 번 채우고 계속 읽는 캐시 · 고루틴마다 다른 키 | **`sync.Map`** 을 **고려** | (4)절 문서의 두 패턴 |
| 그 밖의 공유 맵 | **`map` + `Mutex`/`RWMutex`** | (4)절 문서 |

## 핵심 문장

- ★★★ **원자로 충분한 것은 값 하나다** — 계수기·깃발·포인터 교체는 `atomic` 과 `Mutex` 가 같은 답(`true`)을 냈고, **두 값을 함께 옮기는 `pair` 만 `false`** 였다(`1 / 4`).
- ★★★ **그 `false` 칸에서 `-race` 는 침묵했다**(`1 / 8`) — 경쟁이 없는 것과 **맞는 것**은 다르다.
- ★★★ **386 에서 `int32` 뒤 `int64` 를 옛 함수로 더하면 `panic: unaligned 64-bit atomic operation`**(오프셋 4) — **`atomic.Int64` 는 8 에 놓여 된다.** amd64 에서는 둘 다 된다.
- ★★ **락 없는 맵은 `fatal error: concurrent map writes`** — `-race` 없이 런타임이 잡았다(최선 노력).
- ★★ **`sync.Map` 은 문서가 「대부분은 보통 맵을 써라」라고 먼저 말한다** — 이기는 것은 **한 번 쓰고 여러 번 읽는 키**와 **고루틴마다 겹치지 않는 키** 두 패턴이다. 속도는 **안 쟀다.**
- ★★ **`sync.Map` 은 `any` 다** — `v + 1` 은 컴파일 에러, 틀린 단언은 실행 중 패닉.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 33번)
- [32번 주제](../32-sync-mutex-rwmutex-waitgroup-once/)(`sync`) — ★★ **정본 경계.** `Mutex`·`-race` 창의 첫 사용·복사 금지는 **거기**, 여기는 **「락 대신 원자로 되나」부터.**
- [35번 주제](../35-data-races-and-the-race-detector/)(레이스와 `-race`) — 검출기가 **못 보는 것**의 정본. 원자로 쓰고 평범하게 읽는 `mixed` 칸
- [36번 주제](../36-reading-the-go-memory-model-in-code/)(메모리 모델) — 원자 연산이 **순서를 세운다**는 것의 정본
- [34번 주제](../34-context-cancellation-deadlines-and-values/)(`context`) — `stdversion` 판 격자
- [22번 주제](../22-type-assertion-any-and-comparable/)(타입 단언) — comma-ok 와 패닉형
- [`../../../java/syntax/55-atomics-and-concurrent-collections/`](../../../java/syntax/55-atomics-and-concurrent-collections/) — ★ 자바 원자 변수 — CAS·「각각 원자」 대 「함께 원자」
- [`../../../c/syntax/32-what-volatile-actually-guarantees/`](../../../c/syntax/32-what-volatile-actually-guarantees/) — C `_Atomic` 의 `lock` 접두 · `volatile` 은 원자가 아니다

## 용어 풀이

- **원자 연산** — 중간 상태가 남에게 안 보이는 한 번의 연산.
- **`atomic.Int64`·`atomic.Bool`·`atomic.Pointer[T]`** — 1.19 의 원자 타입. 값을 숨겨 원자 API 로만 만지게 한다. `Int64`·`Uint64` 는 자동 정렬.
- **`atomic.AddInt64`** — 1.0 부터의 함수형. 평범한 `int64` 의 주소를 받는다. 32비트에서 정렬은 부르는 쪽 책임.
- **정렬(alignment)** — 값이 놓인 주소가 몇의 배수인가. 8바이트 원자 연산은 8의 배수를 요구하는 아키텍처가 있다.
- **불변식** — 언제 보아도 참이어야 하는 관계.
- **`sync.Map`** — 락 없이 여러 고루틴이 쓰는 특수 맵. 키·값이 `any`.
- **`LoadOrStore`** — 있으면 읽고, 없으면 넣는다. 한 번에(원자적으로).
- **순차 일관(sequentially consistent)** — 모든 원자 연산이 **어떤 하나의 순서**로 일어난 것처럼 보인다는 약속.

---

## 더 들어가면

- ★ **`atomic.Value`**(타입이 섞이면 패닉하는 옛 방식)는 **안 다뤘다.**
- ★ **CAS 루프**(`CompareAndSwap` 으로 재시도)는 **안 던졌다** — 자바 55편 (2)절이 재시도 횟수까지 쟀다.
- ★ `sync.Map` 의 **내부 구조**(이 판의 구현)는 **안 열었다.**
- ★★ 모든 **시간·처리량** 비교는 **안 쟀다.**
- ★ 386 을 **못 돌리는 환경**에서의 모습(`exec format error`)은 **확인 안 했다.**

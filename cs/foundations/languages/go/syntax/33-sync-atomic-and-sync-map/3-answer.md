# go/syntax/33 — `sync/atomic` 과 `sync.Map` 을 고르는 자리 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★ **근거로 읽을 칸** — 격자의 `-race 보고=예/아니오`·불변식 `true`/`false`·`1 / 4`·`1 / 8` · 386 의 오프셋과 패닉 · 20판 참거짓 · 컴파일 진단 · 종료 코드.
> **근거로 읽지 않을 칸** — 경쟁 칸이 잃은 값(격자가 **안 셌다**) · `concurrent map writes` 가 **몇 번째 판**에서 났나.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `plain` 은 전부 보고 · `pair` 만 갈린다 — `-race` 는 침묵 · `1 / 4` · `1 / 8`

**출력**

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

**왜 그런가**

- ★★★ **`plain` 넷 — `-race 보고=예`, exit 66.** 동기화가 없다.
- ★★★ **`pair / atomic` 만 `불변식 지켜졌나=false`, `-race 보고=아니오`.** `aa.Add(1)` 과 `ab.Add(-1)` 은 **각각** 원자지만, 읽는 쪽이 **그 사이**를 보면 합이 1 이다. 모든 접근이 원자 연산이라 검출기가 볼 「순서 없는 평범한 접근」이 **없다.**
- ★★ `counter`·`flag`·`ptr` 는 `atomic` 과 `Mutex` 가 **같은 `true`** — **값 하나**를 다룬다.
- ★★★ **`1 / 4` · `1 / 8`** — 스크립트가 셌다. **경쟁이 없는 것과 맞는 것은 다른 질문이다.**

### 2. amd64 는 둘 다 8 · 386 은 `Old.n` 이 4 라 패닉, `New.n` 은 8 이라 된다

**출력**

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

**왜 그런가**

- ★★★ **`[GOARCH=386 old] exit=2 · Old.n 오프셋: 4 · … panic: unaligned 64-bit atomic operation`** — 386 에서는 `int32` 뒤의 `int64` 가 4바이트 자리에 놓였고, 옛 함수가 정렬을 검사해 **패닉**했다.
- ★★★ **`[GOARCH=386 new] … New.n 오프셋: 8 · New: 1`** — 문서 「**types [Int64] and [Uint64] are automatically aligned**」.
- ★★ **amd64 는 둘 다 오프셋 8** — 64비트에서는 `int64` 가 원래 8의 배수에 놓인다. 그래서 **64비트 테스트는 이 버그를 영원히 못 본다.**
- ★ `ELF 32-bit LSB executable` — 이 머신이 386 바이너리를 **실제로 돌렸다**(「32비트라 이 머신은 부적용」이 아니었다).

### 3. `fatal error: concurrent map writes`(exit 2, `recover` 불가) · `syncmap` 은 200000

**출력**

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

**왜 그런가**

- ★★★ **보통 빌드에서도 런타임이** 잡았다. **`fatal error`** 라 `recover` 가 못 듣는다([32번 주제](../32-sync-mutex-rwmutex-waitgroup-once/) (8)절과 같은 종류).
- ★ **최선 노력 검사**(구현)다 — 블록은 「20판 안에 났나 : 예」만 싣는다.
- ★★ `syncmap` — **`원소 수: 200000`**, exit 0.

### 4. `invalid operation: v + 1 (mismatched types any and untyped int)`

**출력**

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

**왜 그런가**

- ★★★ `sync.Map` 의 값은 **`any`** 다. 단언 없이는 **산술을 못 한다.** 보통 `map[string]int` 였으면 없었을 에러다.

### 5. 세 줄 뒤 `panic: interface conversion: interface {} is string, not int` · comma-ok 는 `false`, 패닉형은 패닉

**출력**

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

**왜 그런가**

- ★★★ `Store` 가 **값 타입이 섞여도** 받았다. 틀린 것은 **꺼낼 때**, 그것도 **실행 중에** 드러났다.
- ★★ **comma-ok(`_, isInt := n.(int)`)는 `false`** 로 조용히 답하고, **패닉형(`n.(int)`)은 패닉**했다([22번 주제](../22-type-assertion-any-and-comparable/)).
- ★ `Load("name") 의 ok: true` 는 **키가 있다**는 뜻일 뿐, **타입**에 대해서는 아무 말도 안 한다.

### 6. 한 번 쓰고 여러 번 읽는 키 · 고루틴마다 겹치지 않는 키 — 먼저 권하는 것은 보통 맵 + 락

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

- ★★★ 「**(1) when the entry for a given key is only ever written once but read many times, as in caches that only grow, or (2) when multiple goroutines read, write, and overwrite entries for disjoint sets of keys.**」
- ★★★ 그 앞 — 「**Most code should use a plain Go map instead, with separate locking or coordination, for better type safety and to make it easier to maintain other invariants along with the map content.**」
  「**다른 불변식을 함께 지키기**」가 1번의 `pair` 와 같은 이유다 — 맵 내용과 다른 값의 **관계**는 `sync.Map` 이 지켜 주지 않는다.
- ★ 두 패턴의 실측 — `10`(키마다 한 번) · `8000`, `-race` 보고 0 줄.

### 7. synchronized before · 순차 일관 — 두 연산 사이에 대해서는 아무 말도 없다

- ★★★ 문서(2번 블록의 첫 문단) — 「**if the effect of an atomic operation A is observed by atomic operation B, then A "synchronizes before" B**」 · 「**sequentially consistent order**」.
- ★★★ 약속의 단위는 **연산 하나**다. `a.Add(1)` 과 `b.Add(-1)` 을 **함께 한 번에** 한다는 약속은 **없다** — 1번의 `false` 가 그 공백이다.

### 8. 새 값을 다 만든 뒤 **포인터 하나**만 바꾸기 때문 · 필드를 고치면 `pair` 가 된다

- ★★★ `ptr` 는 `&config{i, 2*i}` 를 **다 만든 뒤** `at.Store(c)` **한 번**이다. 읽는 쪽은 **옛 것 전체** 아니면 **새 것 전체**를 본다 — 「두 값」을 **「값 하나(포인터)」로 바꾼** 것이다.
- ★★ 이미 걸린 `config` 의 `x`·`y` 를 고치면 **두 쓰기 사이**가 보인다 — `pair` 와 같은 모양(이 문서는 **그 칸을 안 던졌다**).

### 9. 평범한 읽기 · 32비트 정렬

- ★★★ **평범한 읽기** — 옛 함수형은 `x` 를 **그냥 읽는 코드**도 컴파일된다. 그것이 레이스다([35번 주제](../35-data-races-and-the-race-detector/) 격자의 `mixed` 칸 — 보고). 새 타입은 값을 숨겨 **`Load` 말고는 길이 없다.**
- ★★★ **정렬** — 2번의 386 패닉. 새 타입은 **자동 정렬**.

### 10. 안 해 준다(안 쟀다) · 두 패턴 안의 「락 경합」에 대한 문서의 문장

- ★★★ **이 배치는 어떤 시간도 재지 않았다.**
- ★★ 「**In these two cases, use of a Map may significantly reduce lock contention compared to a Go map paired with a separate Mutex or RWMutex.**」 — **두 패턴 안에서**, **락 경합**을 말한 **문서의 문장**이다. 일반적인 「빠르다」가 아니다.

### 11. `pair / atomic`

- ★★★ **같은 실수다** — 원자 연산 둘을 이어 붙이고 **함께 원자**라고 읽었다. 정본은 [`../../../java/syntax/55-atomics-and-concurrent-collections/`](../../../java/syntax/55-atomics-and-concurrent-collections/) 「어디서 틀리나」 2·4번.
- ★ Go 에서는 그 틈에 **`-race` 도 침묵한다**(1번 — `1 / 8`).

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 로 **★고칠 것 0** |
| ★★★ 격자 (`t33grid`) | `-race` 빌드, 12칸 | 탐색 6번 + 캡처마다(재대조 포함) | **`1 / 4` · `1 / 8`** — 매번 같다 |
| ★★★ 정렬 (`t33align`) | `GOARCH=amd64`·`386` × old·new | 캡처마다 | 386 old 만 **`unaligned 64-bit atomic operation`** |
| ★★ 맵 (`t33map`) | 최대 20판 | 캡처마다 | **`concurrent map writes`** |
| ★★ `sync.Map` (`t33patterns`·`t33any`·`t33assert`) | `-race` 빌드 · 컴파일 · 실행 | 캡처마다 | `10`·`8000` · `mismatched types` · `interface conversion` |
| 문서 (`t33mapdoc`·`t33atomicdoc`·`t33api`) | `go doc` · `api/go1NN.txt` | 1 | — |

**구현·환경에 달린 항목**

| 항목 | 무엇에 달렸나 |
|---|---|
| 386 바이너리가 이 머신에서 도나 | **커널의 32비트 실행 지원**(이 머신: 된다) |
| `unaligned 64-bit atomic operation` 문구 | **이 판 runtime(386)** |
| `concurrent map writes` 가 잡히나 | **runtime 의 최선 노력 검사** — 20판 참거짓으로 접었다 |
| `-race` 의 침묵 | **검출기** — 원자 연산만의 코드는 원리상 조용하다 |
| 원자·락·`sync.Map` 의 **시간** | ★ **안 쟀다** |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다.

# go/syntax/48 — `time`: `Time`·`Duration`·단조 시계·`Timer`/`Ticker`(1.23 변경) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ **모든 문제에서 「이 동작은 명세인가, 표준 라이브러리 문서의 계약인가, 이 판(툴체인)의 성질인가」를 먼저 적어라.**
> 모든 Go 실험은 `module ex` 이고 `go build -trimpath` 로 빌드해 돌렸다(`go1.27.1` · 1번만 `go1.25.12` 와 나란히 · `GOTOOLCHAIN=local`). 시각·경과 시간은 **참/거짓**으로만 찍었다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 탐침 일곱과 판 넷 (예측)

```go
// t48timer.go
package main

import (
	"fmt"
	"runtime"
	"time"
	"weak"
)

func main() {
	t := time.NewTimer(time.Millisecond)
	fmt.Printf("cap(t.C)\t%d\n", cap(t.C))
	time.Sleep(20 * time.Millisecond)
	fmt.Printf("발화 뒤 받기 전 len(t.C)\t%d\n", len(t.C))
	fmt.Printf("발화 뒤 받기 전 Stop()\t%v\n", t.Stop())
	select {
	case <-t.C:
		fmt.Printf("Stop 뒤 t.C 에서 값이 나오나\t%v\n", true)
	default:
		fmt.Printf("Stop 뒤 t.C 에서 값이 나오나\t%v\n", false)
	}

	t2 := time.NewTimer(time.Millisecond)
	time.Sleep(20 * time.Millisecond)
	t2.Reset(time.Hour)
	select {
	case <-t2.C:
		fmt.Printf("Reset(1h) 직후 t.C 에서 값이 나오나\t%v\n", true)
	case <-time.After(30 * time.Millisecond):
		fmt.Printf("Reset(1h) 직후 t.C 에서 값이 나오나\t%v\n", false)
	}

	w := func() weak.Pointer[time.Ticker] {
		tk := time.NewTicker(time.Millisecond) // Stop 하지 않고 참조를 버린다
		return weak.Make(tk)
	}()
	time.Sleep(10 * time.Millisecond)
	runtime.GC()
	runtime.GC()
	fmt.Printf("참조를 버린 Ticker 가 GC 뒤 사라졌나\t%v\n", w.Value() == nil)

	var ms runtime.MemStats
	runtime.GC()
	runtime.ReadMemStats(&ms)
	before := ms.HeapInuse
	ready := make(chan int, 1)
	for i := range 200000 {
		ready <- i
		select {
		case <-ready:
		case <-time.After(time.Hour):
		}
	}
	runtime.GC()
	runtime.ReadMemStats(&ms)
	fmt.Printf("time.After(1h) 20만 번 뒤 GC 한 HeapInuse 증분 < 1MiB\t%v\n", int64(ms.HeapInuse)-int64(before) < 1<<20)
}
```

<!-- 판 1 = go1.25.12 + go.mod 의 go 1.22 · 판 2 = go1.25.12 + go 1.23 · 판 3 = go1.27.1 + go 1.22 · 판 4 = go1.27.1 + go 1.27. 넷을 빌드해 돌리고 탐침마다 한 줄로 나란히 놓는다. -->

- 판 1 과 판 2 에서 일곱 줄 각각의 값은? 판 3·4 는 어느 판과 같나? 마지막 두 줄의 수는?

### 2. 같은 툴체인, 다른 줄 (왜)

- 1번의 판 1·2 는 툴체인이 같은데 갈린다. `go.mod` 의 `go` 줄이 **무엇을 통해** 타이머 의미를 바꾸나? [41번 주제](../41-modules-go-mod-version-selection-and-workspaces/)의 `go` 줄과 어떻게 이어지나?

### 3. 옛 의미를 켜는 세 경로 (예측)

```go
// t48rej.go
package main

import (
	"fmt"
	"time"
)

func main() {
	fmt.Println("cap(NewTimer(1h).C) =", cap(time.NewTimer(time.Hour).C))
}
```

<!-- go.mod 를 go 1.22 로 두고 빌드한 뒤 ① GODEBUG=asynctimerchan=1 환경 변수로 실행 ② 그냥 실행 ③ go.mod 에 godebug asynctimerchan=1 줄을 더해 빌드 ④ 소스 첫 줄에 //go:debug asynctimerchan=1 을 넣어 빌드. -->

- `go1.27.1` 에서 네 단계 각각의 결과(종료 코드·문구)는?

### 4. 31번이 비워 둔 칸 (경계)

- [31번 주제](../31-goroutine-leaks/) (7)절은 「1.22 에서 `time.After` 가 샌다」를 **주장하지 않았다**. 1번의 마지막 줄은 그 칸에 무엇을 더했나? 그리고 이 문서도 **확인하지 못한** 판은 어디인가?

### 5. `m=` 가 남는 연산 (예측)

```go
// t48mono.go
package main

import (
	"fmt"
	"strings"
	"time"
)

func hasM(t time.Time) bool { return strings.Contains(t.String(), " m=") }

func main() {
	t := time.Now()
	fmt.Println("[1] time.Now()           String 에 m= 가 있나:", hasM(t))
	fmt.Println("[2] t.Round(0)           String 에 m= 가 있나:", hasM(t.Round(0)))
	fmt.Println("[3] t.UTC()              String 에 m= 가 있나:", hasM(t.UTC()))
	fmt.Println("[4] t.Add(time.Second)   String 에 m= 가 있나:", hasM(t.Add(time.Second)))
	fmt.Println("[5] t.AddDate(0, 0, 1)   String 에 m= 가 있나:", hasM(t.AddDate(0, 0, 1)))

	b, _ := t.MarshalText()
	var u time.Time
	u.UnmarshalText(b)
	fmt.Println("[6] MarshalText → UnmarshalText 한 u 에 m= 가 있나:", hasM(u))

	fmt.Println("── 같은 순간을 == 와 Equal 로 ──")
	fmt.Println("    t == t.Round(0)   :", t == t.Round(0), "· t.Equal(t.Round(0)):", t.Equal(t.Round(0)))
	fmt.Println("    t == u            :", t == u, "· t.Equal(u)         :", t.Equal(u))
	fmt.Println("    t == t.UTC()      :", t == t.UTC(), "· t.Equal(t.UTC())   :", t.Equal(t.UTC()))
	fmt.Println("    t.Round(0) == u   :", t.Round(0) == u)

	fmt.Println("── 경과 시간 ──")
	s := time.Now()
	time.Sleep(20 * time.Millisecond)
	e := time.Since(s)
	fmt.Println("    time.Since(s) >= 20ms :", e >= 20*time.Millisecond)
	a, c := time.Now(), time.Now()
	fmt.Println("    c.Sub(a) >= 0         :", c.Sub(a) >= 0)
}
```

- `[1]`\~`[6]` 각각에 `m=` 가 있나? `==` 와 `Equal` 네 줄, 경과 시간 두 줄은?

### 6. 같은 순간, `==` 는 `false` (왜)

- 5번에서 `t == t.UTC()` 는 `false` 인데 `t.Equal(t.UTC())` 는 `true` 인 이유를 문서와 [17번 주제](../17-struct-literals-comparability-field-tags-and-sorting/)의 구조체 `==` 로 설명하라. `Time` 을 맵 키로 쓰면 무엇이 문제인가?

### 7. 벽시계를 돌리면 (경계)

- 「벽시계가 바뀌어도 `Sub` 는 양수」를 이 문서는 **직접 보였나**? 보이지 못했다면 대신 **무엇을 쟀나**? 경과 시간을 재는 올바른 꼴과, 그 보호가 **사라지는** 꼴 둘은?

### 8. 큰 `Duration` (예측)

```go
// t48dur.go
package main

import (
	"fmt"
	"math"
	"time"
)

func main() {
	for _, d := range []time.Duration{0, 1, 1500 * time.Microsecond, 90 * time.Second, 36 * time.Hour, -2 * time.Minute} {
		fmt.Printf("%-16d → %v\n", int64(d), d)
	}
	max := time.Duration(math.MaxInt64)
	fmt.Println("Duration(MaxInt64)        →", max, "· Hours() =", max.Hours())
	fmt.Println("그것을 365일짜리 해로      →", int(max.Hours()/24/365), "년")
	fmt.Println("Duration(MaxInt64) + 1    →", max+1)
	years := 300
	d := time.Duration(years) * 365 * 24 * time.Hour
	fmt.Println("300년을 Duration 으로       →", d)
	fmt.Println("(1500ms).Seconds()        →", (1500 * time.Millisecond).Seconds())
	fmt.Println("(1h29m).Round(time.Hour)  →", (89 * time.Minute).Round(time.Hour))
	fmt.Println("(1h29m).Truncate(time.Hour)→", (89 * time.Minute).Truncate(time.Hour))
	pd, err := time.ParseDuration("1d")
	fmt.Println("ParseDuration(\"1d\")       →", pd, err)
}
```

- 각 줄의 출력은?

### 9. 레이아웃 다섯 (예측)

```go
// t48parse.go
package main

import (
	"fmt"
	"time"
)

func main() {
	const in = "2026-03-04"
	for _, layout := range []string{"2006-01-02", "2006-02-01", "YYYY-MM-DD", "2026-03-04", "2006-01-02 15:04"} {
		t, err := time.Parse(layout, in)
		if err != nil {
			fmt.Printf("%-18q → err=%v\n", layout, err)
			continue
		}
		fmt.Printf("%-18q → %s · 3월 4일인가=%v\n", layout, t.Format(time.DateOnly), t.Month() == 3 && t.Day() == 4)
	}
	t, err := time.Parse("2006-01-02 03:04", "2026-03-04 15:30")
	fmt.Printf("%-18q ← \"2026-03-04 15:30\" → %v · err=%v\n", "2006-01-02 03:04", t, err)
	t, _ = time.Parse(time.DateTime, "2026-03-04 15:30:00")
	fmt.Printf("DateTime 레이아웃  → Location=%v\n", t.Location())
}
```

- 레이아웃 다섯 줄과 아래 두 줄 각각의 결과는? **에러 없이 틀린 값**이 나온 줄은?

### 10. 서머타임 전날의 「하루」 (예측)

```go
// t48tz.go
package main

import (
	"fmt"
	"time"
)

func main() {
	ny, err := time.LoadLocation("America/New_York")
	if err != nil {
		fmt.Println("LoadLocation err:", err)
		return
	}
	t0 := time.Date(2026, 3, 7, 12, 0, 0, 0, ny)
	a := t0.Add(24 * time.Hour)
	b := t0.AddDate(0, 0, 1)
	fmt.Println("t0                 :", t0)
	fmt.Println("t0.Add(24h)        :", a)
	fmt.Println("t0.AddDate(0,0,1)  :", b)
	fmt.Println("AddDate 결과 - t0   :", b.Sub(t0))
	fmt.Println("같은 순간 두 표기    :", t0.UTC(), "·", t0.Equal(t0.UTC()))
}
```

- 다섯 줄의 출력은? [Python 49번](../../../python/syntax/49-datetime-and-zoneinfo/)에서 같은 `tzinfo` 에 `timedelta(hours=24)` 를 더한 것은 Go 의 `Add` 와 `AddDate` 중 어느 쪽과 같나?

### 11. `Stop` 뒤 `<-t.C` 로 비우기 (경계)

- 옛 코드에 `if !t.Stop() { <-t.C }` 가 있다. 1번의 판 1 에서 이 관용구가 **왜 필요했나**? 판 3·4 의 의미에서는 `Stop()` 이 무엇을 돌려주고, 이 줄을 그대로 두면 무엇이 걱정되나(이 문서는 그 걱정을 돌려 봤나)?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |

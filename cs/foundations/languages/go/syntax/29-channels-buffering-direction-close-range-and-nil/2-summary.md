# go/syntax/29 — 채널: 버퍼·방향·`close`·`range`·`nil` 채널 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Go 명세 — Channel types · Send statements · Receive operator · Close](https://go.dev/ref/spec#Channel_types) ·
> [Go 메모리 모델 — Channel communication](https://go.dev/ref/mem#chan) · [`runtime`](https://pkg.go.dev/runtime) 소스(`proc.go` 의 `checkdead`).
> 명세·메모리 모델·`runtime` 소스는 **이 툴체인의 `$(go env GOROOT)` 에서 직접 떴다.**\
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> ★ **버전** — 채널의 차단 규칙·닫힌 채널·`nil` 채널 동작은 **이 판(`go1.27`) 명세의 문장으로** 적었다. 이 문서는 **옛 판과 견주지 않았다**(판 격자 없음) — 판 경계가 있다는 근거도, 없다는 근거도 **이 문서에는 없다.**
> 이 문서에서 판이 걸린 것은 정수 `range`(1.22)·`WaitGroup.Go`(1.25) 같은 **곁다리 문법**뿐이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체는 넷째 창이다** — 「**런타임의 교착 탐지(`all goroutines are asleep - deadlock!`)를 「막혔다」의 증인으로 세우는 창**」.
「막힌다」는 원래 **아무 일도 안 일어나는 것**이라 출력으로 보이지 않는다. 그런데 **모든 고루틴이 막히면** 런타임이
`fatal error` 로 프로세스를 죽이고 **종료 코드 2** 를 낸다. 그래서 **버퍼 × 송신 횟수** 격자를 돌려
**어느 칸이 죽었나**를 셸이 세게 했다 — ★ **이 칸들은 흔들리지 않는다**(런타임이 결정적으로 탐지한다).
★★ 그 창의 한계도 같은 창으로 보였다 — **곁에 잠자는 고루틴 하나만 있어도 탐지가 안 된다**((8)절).

★★★ **이 주제의 경계** — 채널로 **배압을 설계하는 것**(큐 길이를 고르는 것 = 대기 시간을 고르는 것, 넘칠 때 버릴까 막을까)은
[`../../../../../ops-patterns/05-backpressure/`](../../../../../ops-patterns/05-backpressure/)가 정본이다.
**그쪽은 정원과 넘침 정책까지**, 여기는 **Go 채널이 언제 막히고 닫히면 무엇이 되는가(차단 규칙)부터.**
여러 채널을 한꺼번에 기다리는 `select` 는 [30번 주제](../30-select-default-and-timeouts/), 막힌 채로 남는 고루틴은 [31번 주제](../31-goroutine-leaks/)다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세·메모리 모델이 약속한 것 | ★★★ **버퍼 0 은 양쪽이 다 준비돼야** · 버퍼가 차면 송신이 막힘 · **닫힌 채널: 송신·재닫기는 패닉, 수신은 남은 값 뒤 영값** · **`nil` 채널은 영원히 막힘 · 닫으면 패닉** · 받기 전용은 닫을 수 없음 · 버퍼 0 의 수신이 송신 완료보다 먼저(메모리 모델) |
| **구현(gc·runtime)** | `runtime` 이 한 것 | ★★★ **교착 탐지(`all goroutines are asleep`)** 와 그 **예외(타이머가 있으면 안 본다)** · 고루틴 상태 문구(`[chan send (nil chan)]`) · 패닉·`fatal error` 의 모양 · **종료 코드 2** |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 격자 12칸 중 교착 8칸 · 재실행 대조까지 |

★★★ **선을 긋는다** — 「버퍼 0 채널에 받는 쪽 없이 보내면 **막힌다**」는 **명세**, 「그러면 **`fatal error` 로 죽는다**」는 **구현**이다.
명세는 **막힌다**고만 말한다. **죽여 주는 것은 런타임의 친절**이고, 그 친절은 **모든 고루틴이 잠들었을 때만** 온다((8)절).

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | ★★ **다른 고루틴이 등장하는 트레이스의 `goroutine N` 의 N** | 런타임이 매기는 고루틴 id — [27번 주제](../27-panic-recover-and-where-to-use-them/)에서 이미 실행마다 바뀌는 것을 보였다. 정규화 규칙 `([Gg]oroutine) \d+` **하나**를 더했다((7)·(8)절 블록) |
| **흔들린다(그래서 안 실었다)** | 버퍼 0 송신이 **몇 ms 막혔나** | 시간이다 — 대신 「**송신이 돌아왔을 때 받는 쪽 깃발이 섰나**」 참거짓으로 바꿔 물었다((2)절) |
| 안 흔들린다 | ★★★ **교착 격자의 `exit=` · 「교착 탐지=」 · 마지막 줄 `8 / 12`** | 런타임이 **모든 고루틴이 잠든 순간** 결정적으로 탐지한다 |
| 안 흔들린다 | ★★ 닫힌·`nil` 채널 격자의 **stdout · 패닉 첫 줄 · 고루틴 상태 줄 · 종료 코드** | 명세가 동작을, 런타임이 문구를 정한다 — 재실행에서 한 글자도 같았다 |
| 안 흔들린다 | 컴파일 에러의 `파일:줄:칸` 과 문장 · `main` 고루틴의 id **1** | |

★ 정규화 규칙은 **기본 넷 + 고루틴 id 하나**를 썼다.

## 한눈에 — 쉽게 말하면

**채널은 고루틴 사이의 우편함이다.** 우편함에 **칸이 몇 개**(버퍼)냐에 따라 보내는 쪽이 **기다리느냐 마느냐**가 갈린다.
칸이 **0** 이면 편지를 **직접 손에서 손으로** 건네야 한다 — 받는 사람이 올 때까지 서 있다.
**우편함을 닫으면**(`close`) 더 넣을 수는 없고, 안에 남은 편지는 꺼낼 수 있고, 다 꺼낸 뒤에는 **빈 봉투**가 나온다.
**우편함이 아예 없으면**(`nil`) 넣으러 간 사람도 꺼내러 간 사람도 **영원히 서 있다.**

| 비유 | 실체 |
|---|---|
| 칸 없는 우편함 — **손에서 손으로** | ★★★ **버퍼 0**(`make(chan T)`) — 송신은 **받는 쪽이 받을 때까지** 막힌다 |
| 칸이 N 개 — **칸이 찰 때까지는 넣고 간다** | ★★ **버퍼 N** — N 개까지는 안 막히고 **N+1 번째**에서 막힌다 |
| 「넣기 전용」·「꺼내기 전용」 열쇠 | ★ **방향 채널** `chan<- T` · `<-chan T` — 반대로 쓰면 **컴파일 에러** |
| 우편함에 「폐쇄」 딱지 | ★★★ **`close`** — 더 넣으면 **패닉**, 두 번 붙여도 **패닉**, 꺼내기는 **남은 것 → 빈 봉투(`ok=false`)** |
| 폐쇄 딱지는 **보내는 사람이 붙인다** | ★★ **받는 쪽이 닫으면 보내는 쪽이 패닉** 한다((7)절) |
| 우편함이 **없는** 주소 | ★★★ **`nil` 채널** — 넣기·꺼내기 **영원히 막힘**, 닫으면 **패닉** |
| 동네 사람이 **전부** 서서 잠들면 경비원이 깨운다 | ★★★ **교착 탐지** — 모든 고루틴이 막히면 `fatal error`(구현) |
| 한 사람이라도 **알람 맞추고 잠들어** 있으면 경비원이 안 온다 | ★★ **타이머가 걸린 고루틴이 있으면 탐지하지 않는다**((8)절) |

```text
   ★★★ 언제 막히나 — 버퍼 b 인 채널에 받는 쪽 없이 s 번 보낸다 ((1)절의 실측)

            송신 1   송신 2   송신 3   송신 4
   버퍼 0    ✗        ✗        ✗        ✗        ✗ = 교착으로 죽음 (exit 2)
   버퍼 1    ○        ✗        ✗        ✗        ○ = 다 넣고 끝남 (exit 0)
   버퍼 3    ○        ○        ○        ✗

   규칙 한 줄 — 「받는 쪽이 없으면 s > b 인 칸에서 막힌다」  → 12칸 중 8칸
```

```text
   ★★★ 닫힌 채널 대 nil 채널 — 같은 연산, 다른 결과 ((4)·(5)절의 실측)

   연산          닫힌 채널                          nil 채널
   ──────        ───────────────────────────        ───────────────────────────
   보내기        패닉 「send on closed channel」    영원히 막힘 [chan send (nil chan)]
   받기          남은 값 → 영값, ok=false           영원히 막힘 [chan receive (nil chan)]
   닫기          패닉 「close of closed channel」   패닉 「close of nil channel」
   range         남은 값을 돌고 끝난다              영원히 막힘
```

```text
   ★★ 교착 탐지가 오는 조건 ((8)절의 실측)

   main 이 nil 채널에 보낸다 (영원히 막힘)
      │
      ├─ 곁에 아무도 없다                  ─▶ 전원 잠듦   ─▶ fatal error · exit 2
      ├─ 곁에 채널에서 막힌 고루틴 하나      ─▶ 전원 잠듦   ─▶ fatal error · exit 2
      └─ 곁에 time.Sleep 으로 자는 고루틴    ─▶ 타이머가 있다 ─▶ 탐지 안 함 · 2초 뒤 timeout 이 죽임(124)
```

> **채널(channel)** — 명세 「A channel provides a mechanism for concurrently executing functions to communicate by sending and receiving values of a specified element type.」 `make(chan T, n)` 으로 만든다.

> **버퍼(용량)** — `make` 의 둘째 인자. 명세 「If the capacity is zero or absent, the channel is unbuffered and communication succeeds only when both a sender and receiver are ready.」

> **교착(deadlock)** — 서로가 서로를 기다려 **아무도 못 나아가는** 상태. Go 런타임은 **모든 고루틴이 잠들면** 이것을 알아채고 죽인다(구현).

- [28번 주제](../28-goroutines-go-statement-cost-and-termination/)가 목록상 **선행**이다 — `go` 문은 **값을 돌려줄 통로가 없고**(반환값은 버려진다) 그 통로가 채널이다.
  ★ 28편 (2)절이 「**받을 쪽 없는 10개는 1초를 기다려도 11**」 을 이미 셌다 — 그 막힘의 **규칙**이 이 편이다.
- ★★ [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/) (5)절이 「**`nil` 채널은 터지지 않고 멈춘다**」를 `nil` 여섯 종류의 표에 적어 두었다 — 여기서 **네 연산 전부를 던져** 그 칸을 채운다((5)절).

## 이 주제가 답하려는 질문

1. **채널 송수신은 언제 막히나** — 버퍼 0 · 1 · N 에서 각각.
2. **닫힌 채널과 `nil` 채널에서 네 연산(보내기·받기·닫기·`range`)은 각각 무엇이 되나.**
3. **「막혔다」를 어떻게 보나** — 그리고 **런타임이 알려 주지 못하는 막힘**은 언제인가.

★ **배압 설계**(정원·넘침 정책)는 [`../../../../../ops-patterns/05-backpressure/`](../../../../../ops-patterns/05-backpressure/)가 정본이다.
★ **스레드 간 통신 일반**은 [`../../../../process-thread/`](../../../../process-thread/)가 정본이다.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **교착 탐지 × 셸의 참거짓 · 칸 세기** | **어느 칸이 막혔나**(`exit=2` + `all goroutines are asleep`) | ★ 본체 창 — 이 주제의 넷째 창 |
| ★★ **고루틴 상태 문구**(`[chan send (nil chan)]`) | **무엇에 막혔나** | 교착 트레이스의 둘째 줄 |
| ★★ **`len`·`cap`** | 버퍼에 **몇 개 들었나** | 이 주제의 고유 창 |
| ★ **메모리 모델의 순서 + 깃발** | 버퍼 0 송신이 **받는 쪽이 받은 뒤에** 돌아오나 | 시간 대신 순서로 물었다((2)절) |
| ★ **컴파일 에러** | 방향 채널의 금지 | |
| ★ **`runtime` 소스 인용** | 교착 탐지가 **구현**이고 **타이머가 있으면 안 본다** | `proc.go` `checkdead` |
| **부적용 — 시간·처리량** | ★★★ **안 쟀다.** 「채널은 느리다」를 이 문서는 적지 않는다 | — |
| **부적용 — `-race`** | 이 문서의 블록은 **채널이 순서를 세워** 경쟁이 없다. 레이스는 [목록의 **35번 주제**](../35-data-races-and-the-race-detector/) | — |

★★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.**
「버퍼 0 송신이 **얼마나** 막혔나」는 시간이라 흔들린다. 그래서 「**송신이 돌아온 순간 받는 쪽이 이미 받으러 왔나**」로 바꿔 물었다((2)절).
★ 바꾼 창의 한계 — **막힌 시간의 길이**는 이 문서에 없다.

### (1) ★★★ 언제 막히나 — 교착 탐지로 증명하는 격자

**언제 쓰나** — `make(chan T, n)` 의 `n` 을 고를 때. **받는 쪽이 없다**고 치고 몇 번까지 보낼 수 있나를 본다.

```text
===== 소스: t29grid.go =====
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
===== 명령: go build -trimpath -o prog . && n=0; m=0; for b in 0 1 3; do for s in 1 2 3 4; do ./prog $b $s 2>err.txt; rc=$?; m=$((m+1)); d=아니오; if grep -q "all goroutines are asleep" err.txt; then d=예; n=$((n+1)); fi; echo "버퍼 $b · 송신 $s : exit=$rc 교착 탐지=$d"; done; done; echo "교착으로 죽은 칸 $n / $m" =====
버퍼 0 · 송신 1 : exit=2 교착 탐지=예
버퍼 0 · 송신 2 : exit=2 교착 탐지=예
버퍼 0 · 송신 3 : exit=2 교착 탐지=예
버퍼 0 · 송신 4 : exit=2 교착 탐지=예
버퍼 1 · 송신 1 : exit=0 교착 탐지=아니오
버퍼 1 · 송신 2 : exit=2 교착 탐지=예
버퍼 1 · 송신 3 : exit=2 교착 탐지=예
버퍼 1 · 송신 4 : exit=2 교착 탐지=예
버퍼 3 · 송신 1 : exit=0 교착 탐지=아니오
버퍼 3 · 송신 2 : exit=0 교착 탐지=아니오
버퍼 3 · 송신 3 : exit=0 교착 탐지=아니오
버퍼 3 · 송신 4 : exit=2 교착 탐지=예
교착으로 죽은 칸 8 / 12
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **마지막 줄이 `교착으로 죽은 칸 8 / 12`** 다. 스크립트가 셌다 — 사람이 센 것이 아니다.
- ★★★ **버퍼 0 은 송신 1 부터 죽는다.** 받는 쪽이 없으니 **첫 편지부터 건넬 손이 없다.**
  명세 「**communication succeeds only when both a sender and receiver are ready**」.
- ★★ **버퍼 1 은 송신 1 까지, 버퍼 3 은 송신 3 까지 산다** — `s > b` 인 칸만 죽는다.
  명세 「**A send on a buffered channel can proceed if there is room in the buffer.**」
- ★ 산 칸은 `보낸 수 … len … cap …` 을 stderr 에 찍고 **exit 0** 이다(격자에서는 그 줄을 안 실었다 — `2>err.txt` 로 받아 교착 문구만 봤다).

한 칸을 통째로 보면 —

```text
===== 소스: t29grid.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog 0 1 =====
fatal error: all goroutines are asleep - deadlock!

goroutine 1 [chan send]:
main.main()
	ex/t29grid.go:15 +0xa6
(exit 2)
```

- ★★★ **`fatal error: all goroutines are asleep - deadlock!`** · **`goroutine 1 [chan send]:`** · **종료 코드 2**.
  둘째 줄의 **`[chan send]`** 가 「**무엇에 막혔나**」다 — 이 트레이스는 **채널 송신에 잠든 main** 을 가리킨다.
- ★★ **`panic` 이 아니라 `fatal error`** 다 — [27번 주제](../27-panic-recover-and-where-to-use-them/)의 `recover` 로 **못 잡는다.**
  런타임이 프로세스를 끝낸다. ★ **stdout 과 섞지 않으려고** 이 편의 탐침은 표시를 전부 **stderr** 에 찍었다.

비용 — 없다(재지 않았다).

### (2) ★★ `len`·`cap` — 그리고 버퍼 0 은 「손에서 손으로」

**언제 쓰나** — 버퍼에 몇 개 들었나를 볼 때, 버퍼 0 송신이 **무엇을 기다리나**를 알 때.

```text
===== 소스: t29lencap.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog =====
버퍼 3, 만든 직후   : len 0 cap 3
버퍼 3, 보낸 뒤 1   : len 1 cap 3
버퍼 3, 보낸 뒤 2   : len 2 cap 3
버퍼 3, 보낸 뒤 3   : len 3 cap 3
버퍼 3, 하나 받은 뒤: len 2 cap 3
버퍼 0             : len 0 cap 0
버퍼 0 송신이 돌아왔을 때 받는 쪽 깃발: true
(exit 0)
```

그림 해설 (한 단계씩):

- ★★ **버퍼 3 — `len` 이 0 → 1 → 2 → 3, 하나 받으면 2.** `cap` 은 끝까지 **3**.
- ★★ **버퍼 0 — `len 0 cap 0`.** 버퍼 0 채널에는 **들어 있는 상태가 없다** — 값은 **건너가는 순간**에만 존재한다.
- ★★★ **「버퍼 0 송신이 돌아왔을 때 받는 쪽 깃발: true」** — 받는 고루틴은 **30ms 자고 → 깃발을 올리고 → 받는다.**
  송신은 그동안 **막혀 있었고**, 돌아왔을 때 **깃발이 이미 서 있었다.**
  ★ 이것이 **잰 시간이 아니라 순서**라서 안 흔들린다 — 근거는 메모리 모델이다:

```text
===== 명령: sed -n "373,374p;405,406p;416,417p" "$(go env GOROOT)/doc/go_mem.html" | sed -e "s/<[^>]*>//g" =====
A send on a channel is synchronized before the completion of the
corresponding receive from that channel.
The closing of a channel is synchronized before a receive that returns a zero value
because the channel is closed.
A receive from an unbuffered channel is synchronized before the completion of
the corresponding send on that channel.
(exit 0)
```

  ★★★ 「**A receive from an unbuffered channel is synchronized before the completion of the corresponding send on that channel.**」
  깃발은 받기 **전**에 올렸고, 받기는 송신 완료 **전**이다 — 그래서 송신이 돌아온 뒤 읽은 깃발은 **반드시** `true` 다.
  ★ 첫 문장(「A send … is synchronized before the completion of the corresponding receive」)은 **버퍼가 있어도** 성립하는 쪽이다.
  **버퍼 0 에서만** 거꾸로(수신 → 송신 완료)도 성립한다. 메모리 모델의 정본은 [목록의 **36번 주제**](../36-reading-the-go-memory-model-in-code/)다.
- ★ `len` 은 **그 순간의 스냅숏**이다 — 다른 고루틴이 동시에 넣고 빼면 읽자마자 틀린 값이 된다. **분기 조건으로 쓰지 마라**(「`len(ch) < cap(ch)` 이면 보낸다」는 경쟁이다).

비용 — 없다.

### (3) ★ 방향 채널 — 반대로 쓰면 컴파일 에러

**언제 쓰나** — 함수 매개변수로 채널을 넘길 때. **보내기만 할 쪽에는 `chan<-`, 받기만 할 쪽에는 `<-chan`** 을 준다.

```text
===== 소스: t29dir.go =====
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
===== 명령: go build -trimpath -gcflags=-e -o prog . =====
# ex
./t29dir.go:5:4: invalid operation: cannot receive from send-only channel chan<- int out (variable of type chan<- int)
./t29dir.go:10:2: invalid operation: cannot send to receive-only channel <-chan int in (variable of type <-chan int)
./t29dir.go:11:8: invalid operation: cannot close receive-only channel in (variable of type <-chan int)
./t29dir.go:19:22: cannot use r (variable of type <-chan int) as chan int value in variable declaration
(exit 1)
```

그림 해설 (한 단계씩):

- ★★ **네 줄이 거부된다** — 보내기 전용에서 받기(`cannot receive from send-only channel`) ·
  받기 전용에 보내기(`cannot send to receive-only channel`) · ★ **받기 전용을 닫기**(`cannot close receive-only channel`) ·
  받기 전용을 양방향 변수에 담기(`cannot use r … as chan int value`).
- ★★★ **`close(in)` 이 컴파일 에러인 것이 이 문법의 가장 쓸모 있는 자리**다 — 명세 「**It is an error if ch is a receive-only channel.**」
  「**닫는 것은 보내는 쪽**」이라는 관례((7)절)를 **타입이 강제**한다.
- ★ `producer(ch)`·`consumer(ch)`·`var r <-chan int = ch` 는 **통과했다** — **양방향 → 한 방향은 암묵 변환**, 그 반대는 안 된다.
- ★ `-gcflags=-e` 로 에러 상한을 풀어 넷을 다 받았다([28번 주제](../28-goroutines-go-statement-cost-and-termination/) (6)절과 같은 방법).

비용 — 없다. **방향은 컴파일 시점의 것**이다 — 런타임에는 같은 채널이다.

### (4) ★★★ 닫힌 채널 × 다섯 연산

**언제 쓰나** — 「다 보냈다」를 받는 쪽에 알릴 때. `close` 뒤에 **무엇이 되고 무엇이 안 되나.**

```text
===== 소스: t29closed.go =====
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
===== 명령: go build -trimpath -o prog . && for c in rest empty send reclose range; do ./prog $c >out.txt 2>err.txt; rc=$?; echo "[$c] stdout      : $(cat out.txt)"; echo "[$c] stderr 첫 줄: $(head -n 1 err.txt)"; echo "[$c] exit=$rc"; done =====
[rest] stdout      : 7 true 0 false
[rest] stderr 첫 줄: 
[rest] exit=0
[empty] stdout      : 0 false
[empty] stderr 첫 줄: 
[empty] exit=0
[send] stdout      : 
[send] stderr 첫 줄: panic: send on closed channel
[send] exit=2
[reclose] stdout      : 
[reclose] stderr 첫 줄: panic: close of closed channel
[reclose] exit=2
[range] stdout      : 1 2 range 뒤 줄
[range] stderr 첫 줄: 
[range] exit=0
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`rest` — `7 true 0 false`.** 값 **하나를 남긴 채** 닫았다. 첫 수신은 **남은 7 을 `ok=true`** 로, 둘째 수신은 **영값 0 을 `ok=false`** 로 받았다.
  ★ **닫아도 남은 값은 버려지지 않는다** — 명세 「**after any previously sent values have been received**」.
- ★★ **`empty` — `0 false`.** 빈 채로 닫으면 **바로 영값 + `false`**. **막히지 않는다** — 「A receive operation on a closed channel can **always proceed immediately**」.
- ★★★ **`send` — `panic: send on closed channel`, exit 2.** · **`reclose` — `panic: close of closed channel`, exit 2.**
  둘 다 **`fatal error` 가 아니라 `panic`** 이다 — [27번 주제](../27-panic-recover-and-where-to-use-them/)의 `recover` 가 **들을 수 있는** 쪽이다.
- ★★ **`range` — `1 2 range 뒤 줄`.** 남은 값을 **다 돈 뒤 끝났다.** 「**until the channel is closed**」.
- ★ 각 칸은 **stdout 과 stderr 를 따로 받았다**(`>out.txt 2>err.txt`) — 한 칸 안에서 섞지 않았다.

`send` 칸을 통째로 —

```text
===== 소스: t29closed.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog send =====
panic: send on closed channel

goroutine 1 [running]:
main.main()
	ex/t29closed.go:23 +0x225
(exit 2)
```

- ★ **`goroutine 1 [running]:`** — 교착의 `[chan send]` 와 달리 **막힌 것이 아니라 달리다 터진** 것이다.

비용 — 없다.

### (5) ★★★ `nil` 채널 × 네 연산

**언제 쓰나** — `var ch chan int` 처럼 **`make` 를 잊은** 채널, 또는 **일부러 `nil` 을 넣은** 채널([30번 주제](../30-select-default-and-timeouts/)의 가지 끄기)을 볼 때.

```text
===== 소스: t29nil.go =====
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
===== 명령: go build -trimpath -o prog . && for c in send recv close range; do timeout 2 ./prog $c 2>err.txt; rc=$?; echo "[$c] $(sed -n 1p err.txt)"; echo "[$c] $(sed -n 2p err.txt)"; echo "[$c] $(grep -m 1 "^goroutine 1 " err.txt)"; echo "[$c] exit=$rc"; done =====
[send] ch == nil : true len 0 cap 0
[send] fatal error: all goroutines are asleep - deadlock!
[send] goroutine 1 [chan send (nil chan)]:
[send] exit=2
[recv] ch == nil : true len 0 cap 0
[recv] fatal error: all goroutines are asleep - deadlock!
[recv] goroutine 1 [chan receive (nil chan)]:
[recv] exit=2
[close] ch == nil : true len 0 cap 0
[close] panic: close of nil channel
[close] goroutine 1 [running]:
[close] exit=2
[range] ch == nil : true len 0 cap 0
[range] fatal error: all goroutines are asleep - deadlock!
[range] goroutine 1 [chan receive (nil chan)]:
[range] exit=2
(exit 0)
```

그림 해설 (한 단계씩):

- ★★ **첫 줄 — `ch == nil : true len 0 cap 0`.** `nil` 채널도 `len`·`cap` 은 **0 을 답한다**(안 터진다).
- ★★★ **`send`·`recv`·`range` 는 셋 다 교착으로 죽었다** — 상태 문구가 **`[chan send (nil chan)]`** · **`[chan receive (nil chan)]`**.
  ★ **`(nil chan)` 이 붙는다** — (1)절의 `[chan send]` 와 **런타임이 구별해서** 적는다.
  명세 「**A send on a nil channel blocks forever.**」·「**Receiving from a nil channel blocks forever.**」
- ★★★ **`close` 만 `panic: close of nil channel`** — 막히는 것이 아니라 **터진다.** 명세 「**Closing the nil channel also causes a run-time panic.**」
- ★★ **「`switch 뒤 줄`」은 넷 다 안 찍혔다.**
- ★ [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/) (5)절의 표가 「**`nil` 채널: 터지지도 않고 멈춘다**」라고 적은 것이 **보내기·받기·`range` 세 칸**의 실측이다. **닫기 한 칸은 터진다.**

비용 — 없다.

### (6) ★★ `range` 는 `close` 전까지 안 끝난다

**언제 쓰나** — `for v := range ch` 로 받을 때. **누가 언제 닫나**가 루프의 끝을 정한다.

```text
===== 소스: t29range.go =====
package main

import (
	"fmt"
	"os"
)

func main() {
	ch := make(chan int)
	go func() {
		for i := 1; i <= 3; i++ {
			ch <- i
		}
		if os.Args[1] == "close" {
			close(ch)
		}
	}()
	for v := range ch {
		fmt.Fprintln(os.Stderr, "받음", v)
	}
	fmt.Fprintln(os.Stderr, "range 뒤 줄")
}
===== 명령: go build -trimpath -o prog . && for m in close noclose; do echo "--- $m"; ./prog $m 2>&1; echo "exit=$?"; done =====
--- close
받음 1
받음 2
받음 3
range 뒤 줄
exit=0
--- noclose
받음 1
받음 2
받음 3
fatal error: all goroutines are asleep - deadlock!

goroutine 1 [chan receive]:
main.main()
	ex/t29range.go:18 +0xf4
exit=2
(exit 0)
```

그림 해설 (한 단계씩):

- ★★ **`close` — `받음 1 2 3` 뒤 `range 뒤 줄`, exit 0.**
- ★★★ **`noclose` — `받음 1 2 3` 까지는 같고 그다음이 `fatal error … deadlock!`, `goroutine 1 [chan receive]`, exit 2.**
  보내는 고루틴은 **3 개를 보내고 끝났다** — 그런데 닫지 않았으니 `range` 는 **넷째를 기다린다.** 아무도 안 보낸다.
- ★★ **여기서는 교착 탐지가 알려 줬지만, 곁에 다른 고루틴이 살아 있었다면 조용히 멈췄을 것이다**((8)절) — 그것이 [31번 주제](../31-goroutine-leaks/)의 누수 넷째 모양이다.

비용 — 없다.

### (7) ★★ `close` 는 보내는 쪽이 한다 — 받는 쪽이 닫으면

**언제 쓰나** — 「누가 닫을 책임이 있나」를 정할 때.

```text
===== 소스: t29whoclose.go =====
package main

import (
	"fmt"
	"os"
)

func main() {
	ch := make(chan int)
	closed := make(chan struct{})
	done := make(chan struct{})
	go func() { // 보내는 쪽
		ch <- 1
		<-closed
		ch <- 2
		fmt.Fprintln(os.Stderr, "보내는 쪽 끝")
		close(done)
	}()
	fmt.Fprintln(os.Stderr, "받는 쪽이 받음", <-ch)
	close(ch) // 받는 쪽이 닫는다
	close(closed)
	<-done
	fmt.Fprintln(os.Stderr, "main 끝")
}
===== 명령: go build -trimpath -o prog . && ./prog =====
받는 쪽이 받음 1
panic: send on closed channel

goroutine 19 [running]:
main.main.func1()
	ex/t29whoclose.go:15 +0x56
created by main.main in goroutine 1
	ex/t29whoclose.go:12 +0xba
(exit 2)
```

그림 해설 (한 단계씩):

- ★★★ **받는 쪽(main)이 `1` 을 받고 닫았더니, 보내는 고루틴이 둘째 송신에서 `panic: send on closed channel`** — **프로세스 전체가 exit 2.**
  `보내는 쪽 끝` 도 `main 끝` 도 안 찍혔다.
- ★★ **`goroutine N [running]: main.main.func1()` · `created by main.main in goroutine 1`** — 터진 것은 **보내는 고루틴**이다.
  ★ [27번 주제](../27-panic-recover-and-where-to-use-them/) (4)절대로 **다른 고루틴의 패닉은 main 이 못 잡는다.** 닫은 쪽은 멀쩡하고 **보낸 쪽이 죽는다.**
- ★★★ 그래서 관례가 「**보내는 쪽이 닫는다**」다. 보내는 쪽은 **언제 더 안 보낼지 아는 유일한 쪽**이다.
  받는 쪽이 「그만 보내라」를 알려야 하면 **닫지 말고 별도의 취소 신호**(`done` 채널·`context`)를 쓴다 — [31번 주제](../31-goroutine-leaks/)·[목록의 **34번 주제**](../34-context-cancellation-deadlines-and-values/).
- ★ 보내는 쪽이 **여럿**이면 누구도 혼자 닫을 수 없다 — 전부 끝난 뒤 **한 곳에서** 닫는다(`WaitGroup` 뒤 `close` — [32번 주제](../32-sync-mutex-rwmutex-waitgroup-once/)).

비용 — 없다.

### (8) ★★★ 탐지 못 하는 교착 — 곁에 누가 있느냐

**언제 쓰나** — 「교착이면 런타임이 알려 주겠지」라고 생각할 때. **main 은 똑같이 `nil` 채널에 영원히 막히고**, 곁에 둔 고루틴만 바꿨다.

```text
===== 소스: t29hide.go =====
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
===== 명령: go build -trimpath -o prog . && n=0; m=0; for c in alone stuck sleeper; do timeout 2 ./prog $c 2>err.txt; rc=$?; m=$((m+1)); d=아니오; if grep -q "all goroutines are asleep" err.txt; then d=예; else n=$((n+1)); fi; echo "[$c] exit=$rc 교착 탐지=$d"; done; echo "탐지 못 한 칸 $n / $m" =====
[alone] exit=2 교착 탐지=예
[stuck] exit=2 교착 탐지=예
[sleeper] exit=124 교착 탐지=아니오
탐지 못 한 칸 1 / 3
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`탐지 못 한 칸 1 / 3`.** `sleeper` 만 **exit 124** — 2초 뒤 `timeout` 이 죽인 것이다. 프로그램은 **아무 말 없이 멈춰 있었다.**
- ★★★ **`stuck` 은 탐지됐다** — 곁의 고루틴도 **채널에 막혀 잠들어 있으니 전원이 잠든 것**이다. 트레이스에 **두 고루틴이 다 나온다**:

```text
===== 소스: t29hide.go =====
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
===== 명령: go build -trimpath -o prog . && ./prog stuck =====
main 이 nil 채널에 보낸다
fatal error: all goroutines are asleep - deadlock!

goroutine 1 [chan send (nil chan)]:
main.main()
	ex/t29hide.go:23 +0x114

goroutine 7 [chan receive]:
main.main.func2()
	ex/t29hide.go:19 +0x19
created by main.main in goroutine 1
	ex/t29hide.go:19 +0xa5
(exit 2)
```

  ★★ **`goroutine N [chan receive]:` · `created by main.main in goroutine 1`** — 런타임이 **막힌 고루틴 전부**를 보여 준다. (N 은 흔들린다 — 머리말의 정규화 칸.)
- ★★★ **왜 `sleeper` 는 탐지가 안 되나** — 런타임 소스가 답한다:

```text
===== 명령: sed -n "6511,6519p" "$(go env GOROOT)/src/runtime/proc.go" =====
	// There are no goroutines running, so we can look at the P's.
	for _, pp := range allp {
		if len(pp.timers.heap) > 0 {
			return
		}
	}

	unlock(&sched.lock) // unlock so that GODEBUG=scheddetail=1 doesn't hang
	fatal("all goroutines are asleep - deadlock!")
(exit 0)
```

  ★★★ 「**There are no goroutines running, so we can look at the P's.**」 뒤에 **`if len(pp.timers.heap) > 0 { return }`** —
  **타이머가 하나라도 걸려 있으면 「언젠가 누가 깨어날 수 있다」고 보고 탐지를 포기한다.** `time.Sleep(time.Hour)` 가 바로 그 타이머다.
  ★ **이것은 명세가 아니다** — `runtime/proc.go` 의 `checkdead` 라는 **구현**이다. 명세는 「blocks forever」라고만 한다.
- ★★ **실무 코드에는 타이머를 쥔 고루틴이 흔하다** — 티커·타임아웃·재시도 대기. 그런 프로세스에서는 **교착 탐지가 오지 않는다.** (네트워크 대기가 같은 효과를 내는지는 이 문서가 **안 던졌다.**)
  (1)절의 격자가 깨끗하게 죽은 것은 **고루틴이 main 하나뿐인 탐침**이라서다.
- ★★ **브리핑의 전제 하나가 여기서 갈렸다** — 「**누수된 고루틴이 교착 탐지를 가린다**」는 **반만 맞다.**
  **채널에 막혀 새어 있는 고루틴(`stuck`)은 가리지 못한다** — 그것도 잠든 것이니까. **가리는 것은 타이머를 쥔 고루틴(`sleeper`)** 이다.
  [31번 주제](../31-goroutine-leaks/)의 누수 넷째 모양(티커 루프)이 바로 이 「가리는」 쪽이다.

비용 — 없다.

### (9) 명세 원문 — 차단 규칙과 닫기

```text
===== 명령: sed -n "1744,1748p;5354,5358p;6123,6126p;6804,6806p;7552,7558p" "$(go env GOROOT)/doc/go_spec.html" | sed -e "s/<[^>]*>//g" =====
If the capacity is zero or absent, the channel is unbuffered and communication
succeeds only when both a sender and receiver are ready. Otherwise, the channel
is buffered and communication succeeds without blocking if the buffer
is not full (sends) or not empty (receives).
A nil channel is never ready for communication.
The expression blocks until a value is available.
Receiving from a nil channel blocks forever.
A receive operation on a closed channel can always proceed
immediately, yielding the element type's zero value
after any previously sent values have been received.
A send on an unbuffered channel can proceed if a receiver is ready.
A send on a buffered channel can proceed if there is room in the buffer.
A send on a closed channel proceeds by causing a run-time panic.
A send on a nil channel blocks forever.
For channels, the iteration values produced are the successive values sent on
the channel until the channel is closed. If the channel
is nil, the range expression blocks forever.
records that no more values will be sent on the channel.
It is an error if ch is a receive-only channel.
Sending to or closing a closed channel causes a run-time panic.
Closing the nil channel also causes a run-time panic.
After calling close, and after any previously
sent values have been received, receive operations will return
the zero value for the channel's type without blocking.
(exit 0)
```

- ★★★ 이 문서의 모든 「막힌다 / 터진다 / 영값이 나온다」는 **이 다섯 문단에서 나왔다.** 교착 탐지와 종료 코드 2 는 **여기에 없다** — 구현이다.

### (10) ★ Rust `mpsc` 와 — 닫기 대신 「드롭」, 패닉 대신 `Err`

**언제 쓰나** — 「채널을 닫는다」가 언어마다 같은 뜻인지 볼 때.

```text
===== 소스: t29mpsc.rs =====
use std::sync::mpsc;
use std::thread;

fn main() {
    // 1) 받는 쪽을 버린 뒤 보내기
    let (tx, rx) = mpsc::channel::<i32>();
    drop(rx);
    println!("받는 쪽을 버린 뒤 send : {:?}", tx.send(1));

    // 2) 보내는 쪽이 전부 사라지면 받기 루프가 끝난다
    let (tx, rx) = mpsc::channel::<i32>();
    let h = thread::spawn(move || {
        for i in 1..=3 {
            tx.send(i).unwrap();
        }
    }); // tx 가 여기서 드롭된다
    let got: Vec<i32> = rx.iter().collect();
    h.join().unwrap();
    println!("송신자 드롭 뒤 받은 것 : {:?}", got);
    println!("그 뒤 recv            : {:?}", rx.recv());
}
===== 명령: rustc --edition 2024 -o prog t29mpsc.rs && ./prog =====
받는 쪽을 버린 뒤 send : Err(SendError { .. })
송신자 드롭 뒤 받은 것 : [1, 2, 3]
그 뒤 recv            : Err(RecvError)
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **받는 쪽을 버린 뒤 보내면 Rust 는 `Err(SendError { .. })` 를 돌려준다** — Go 는 (4)·(7)절에서 **패닉**했다.
  Go 에는 「받는 쪽이 사라졌다」는 개념이 **아예 없다** — `close` 는 **보내는 쪽의 선언**이고, 받는 쪽이 떠난 것은 채널이 모른다.
  그래서 Go 에서 받는 쪽이 떠나면 보내는 쪽은 **패닉도 에러도 없이 막힌다** — [31번 주제](../31-goroutine-leaks/)의 누수 첫 모양이다.
- ★★ **보내는 쪽이 전부 드롭되면 `rx.iter()` 가 끝난다**(`[1, 2, 3]`), 그 뒤 `recv` 는 `Err(RecvError)` — Go 의 **`close` + `range`**, **`ok=false`** 자리다.
  ★ Rust 는 **`close` 를 부르는 문법이 없다** — 송신자 값의 **수명**이 곧 닫힘이다.
- Rust 쪽 정본은 Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **51번**(`mpsc` 채널 — 아직 폴더 없음)이다.

비용 — 없다.

## 문법 — 형태와 규칙

### 형태

```go
// t29form.go
package main

import "fmt"

// gen 은 보내는 쪽이다 — 다 보내면 자기가 닫는다.
func gen(n int) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out)
		for i := 1; i <= n; i++ {
			out <- i
		}
	}()
	return out
}

// square 는 받기 전용을 받아 보내기 전용에 쓴다.
func square(in <-chan int, out chan<- int) {
	defer close(out)
	for v := range in {
		out <- v * v
	}
}

func main() {
	sq := make(chan int, 2)
	go square(gen(4), sq)
	sum := 0
	for v := range sq {
		sum += v
	}
	fmt.Println("제곱의 합:", sum)
}
```

```text
===== 명령: go build -trimpath -o prog . && ./prog =====
제곱의 합: 30
(exit 0)
```

규칙 불릿.

- **`make(chan T)`** 는 버퍼 0, **`make(chan T, n)`** 은 버퍼 n. **`var ch chan T`** 는 `nil` 채널이다(`make` 를 안 했다).
- **버퍼 0 — 송신은 받는 쪽이 받을 때까지 막힌다.** 버퍼 n — **n 개까지는 안 막히고** 찼을 때 막힌다.
- **`v, ok := <-ch`** — 닫힌 뒤 **남은 값을 다 받으면** `ok=false` 와 영값.
- **`close(ch)`** — 한 번만, **보내는 쪽이.** 닫힌 채널에 보내거나 두 번 닫으면 **패닉.** `nil` 을 닫아도 **패닉.**
- **`for v := range ch`** — **닫힐 때까지** 돈다. 안 닫으면 안 끝난다.
- **`chan<- T` 보내기 전용 · `<-chan T` 받기 전용** — 양방향에서 **암묵 변환**, 받기 전용은 **닫을 수 없다.**
- **`nil` 채널** — 보내기·받기·`range` 는 **영원히 막힘**, 닫기는 **패닉**.
- **`len`·`cap`** — 버퍼 안의 개수와 크기. `len` 은 **스냅숏**이라 분기에 쓰지 않는다.

### 금지 사례 — 컴파일러가 거부하는 것

| 쓴 꼴 | 진단 | 어디서 |
|---|---|---|
| 보내기 전용에서 `<-out` | `cannot receive from send-only channel` | (3)절 |
| 받기 전용에 `in <- 1` | `cannot send to receive-only channel` | 〃 |
| 받기 전용을 `close(in)` | `cannot close receive-only channel` | 〃 |
| 받기 전용을 `chan int` 변수에 | `cannot use r (variable of type <-chan int) as chan int value` | 〃 |
| 닫힌 채널에 보내기 | ★★ **컴파일은 된다** — 실행하면 `panic: send on closed channel` | (4)절 |
| `nil` 채널에 보내기 | ★★★ **컴파일도 되고 경고도 없다** — 실행하면 영원히 막힘 | (5)절 |

## 어디서 틀리나

### 1. ★★★ 「교착이면 런타임이 알려 준다」

- (8)절 실측 — **곁에 `time.Sleep` 하는 고루틴 하나**만 있어도 **탐지 못 한 칸 1 / 3.** 프로그램은 **말없이 멈춘다.**
- 고치는 법 — 교착 탐지는 **탐침에서만 믿는 창**이다. 실제 코드는 **누가 닫나·누가 받나**를 설계로 막고, 멈춤은 **고루틴 덤프**로 본다([31번 주제](../31-goroutine-leaks/)의 프로파일).

### 2. ★★★ 「버퍼를 주면 막히지 않는다」

- (1)절 실측 — **버퍼 3 도 송신 4 에서 죽었다.** 버퍼는 **막히는 시점을 미룰 뿐**이다.
- 고치는 법 — 버퍼 크기는 **받는 쪽이 따라오지 못할 때 얼마나 기다리게 할 것인가**의 선택이다 — 그 설계는 [`05-backpressure`](../../../../../ops-patterns/05-backpressure/)의 몫.

### 3. ★★★ 「받는 쪽이 다 받았으면 닫아 준다」

- (7)절 실측 — 받는 쪽이 닫자 **보내는 고루틴이 패닉**, 프로세스가 **exit 2.**
- 고치는 법 — **보내는 쪽이 닫는다.** 받는 쪽의 「그만」은 **별도 신호**로. 받기 전용 타입(`<-chan`)을 주면 **닫는 코드가 컴파일 안 된다**((3)절).

### 4. ★★ 「닫으면 남은 값이 사라진다」

- (4)절 실측 — **`7 true 0 false`.** 남은 7 은 **받혔다.**

### 5. ★★ 「`nil` 채널은 `nil` 포인터처럼 터진다」

- (5)절 실측 — **보내기·받기·`range` 는 터지지 않고 멈춘다.** **닫기만** 터진다.
- 고치는 법 — 채널 필드는 **생성자에서 `make`** 한다. `nil` 은 **의도해서 쓸 때만**([30번 주제](../30-select-default-and-timeouts/) (5)절).

### 6. ★★ 「보내는 쪽이 다 보내고 끝났으니 `range` 도 끝난다」

- (6)절 실측 — `받음 1 2 3` 뒤 **`[chan receive]` 로 교착.** 보내는 고루틴이 **끝난 것**과 **닫은 것**은 다르다.
- 고치는 법 — 보내는 고루틴의 첫 줄에 **`defer close(out)`**((문법) 절의 `gen`).

### 7. ★ 「`len(ch) < cap(ch)` 이면 안전하게 보낼 수 있다」

- (2)절 — `len` 은 **스냅숏**이다. 확인과 송신 사이에 다른 고루틴이 채울 수 있다. **막히지 않고 보내려면 `select` + `default`**([30번 주제](../30-select-default-and-timeouts/)).

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| ★★★ **버퍼 0 은 양쪽이 준비돼야 · 버퍼 n 은 찰 때까지** | **명세 보장** | (9)절 · (1)절 격자 |
| ★★★ **닫힌 채널: 송신·재닫기 패닉 · 수신은 남은 값 뒤 영값·`ok=false` · `range` 끝** | **명세 보장** | (4)절 |
| ★★★ **`nil` 채널: 송수신·`range` 영원히 막힘 · 닫기 패닉** | **명세 보장** | (5)절 |
| **받기 전용은 닫을 수 없음 · 방향 변환 규칙** | **명세 보장** | (3)절 진단 |
| ★★ **버퍼 0 의 수신이 송신 완료보다 먼저** | **메모리 모델 보장** | (2)절 |
| ★★★ **교착 탐지(`all goroutines are asleep`) · 타이머가 있으면 안 봄** | ★ **구현(runtime)** | (8)절 `checkdead` 소스 |
| 고루틴 상태 문구 `[chan send (nil chan)]` · `fatal error` 모양 · **종료 코드 2** | **구현(runtime)** | (1)·(5)절 |
| 트레이스의 고루틴 id | **구현 — 흔들린다** | 정규화 칸 |
| 채널 연산의 **시간 비용** | ★ **안 쟀다** | — |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 고루틴에서 **결과 하나**를 받는다 | **채널**(부르는 쪽이 반드시 받으면 버퍼 0, 안 받고 떠날 수 있으면 **버퍼 1**) | `go` 는 반환값을 버린다 · 버퍼 1 의 조건은 [31번 주제](../31-goroutine-leaks/) |
| **값의 흐름**(생산 → 소비) | **채널 + 보내는 쪽 `defer close` + `range`** | (6)절 |
| 「다 끝났다」 **알림만** | **`chan struct{}` 를 `close`** | 닫힌 채널은 **모든 받는 쪽을 동시에** 깨운다((4)절 `empty`) |
| 받는 쪽이 「그만」을 알린다 | **별도 취소 신호** — 닫지 마라 | (7)절 · [목록의 **34번 주제**](../34-context-cancellation-deadlines-and-values/) |
| 함수 매개변수 | **방향 채널** | 받기 전용이면 **닫기가 컴파일 에러**((3)절) |
| **공유 상태**를 여럿이 고친다 | ★ **채널보다 뮤텍스가 맞는 경우가 많다** | [32번 주제](../32-sync-mutex-rwmutex-waitgroup-once/)의 판단표 |
| 넘칠 때 버릴까 막을까 | — | [`05-backpressure`](../../../../../ops-patterns/05-backpressure/) |

## 핵심 문장

- ★★★ **받는 쪽이 없으면 `s > b` 인 칸에서 막힌다** — 격자 **12칸 중 8칸이 교착으로 죽었다**(exit 2). 버퍼는 막힘을 **미룰 뿐**이다.
- ★★★ **닫힌 채널 — 보내기·다시 닫기는 패닉, 받기는 남은 값 → 영값·`ok=false`, `range` 는 끝난다.** 남은 값은 버려지지 않는다(`7 true 0 false`).
- ★★★ **`nil` 채널 — 보내기·받기·`range` 는 영원히 막히고(`[chan send (nil chan)]`), 닫기만 패닉**이다.
- ★★★ **교착 탐지는 구현이고, 타이머가 하나라도 걸려 있으면 안 온다** — `sleeper` 한 칸이 **exit 124**(탐지 못 한 칸 1 / 3). **채널에 막혀 새어 있는 고루틴은 탐지를 못 가린다.**
- ★★ **닫는 것은 보내는 쪽이다** — 받는 쪽이 닫으면 **보내는 고루틴이 패닉**하고 프로세스가 끝난다. 받기 전용 타입은 **닫기를 컴파일 에러로** 막는다.
- ★ **버퍼 0 송신이 돌아온 순간 받는 쪽은 이미 받았다** — 메모리 모델 「A receive from an unbuffered channel is synchronized before the completion of the corresponding send」.

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 29번)
- [`../../../../../ops-patterns/05-backpressure/`](../../../../../ops-patterns/05-backpressure/) — ★★ **정본 경계.** **그쪽은 정원·넘침 정책(DROP·BLOCK·FAIL)과 큐 길이 설계까지**, 여기는 **채널이 언제 막히고 닫히면 무엇이 되는가(차단 규칙)부터.**
- [`../../../../process-thread/`](../../../../process-thread/) — 스레드 간 통신·동기화 일반
- [28번 주제](../28-goroutines-go-statement-cost-and-termination/)(고루틴) — ★ 목록상 선행 · `NumGoroutine` 이 안 줄어드는 것까지
- [21번 주제](../21-nil-interface-vs-interface-holding-nil-pointer/)(`nil`) — ★ `nil` 채널이 「멈춘다」 칸
- [27번 주제](../27-panic-recover-and-where-to-use-them/)(`panic`) — 닫힌 채널의 패닉은 `recover` 가 듣고, 교착의 `fatal error` 는 못 듣는다 · 다른 고루틴의 패닉은 못 잡는다
- [30번 주제](../30-select-default-and-timeouts/)(`select`) — 여러 채널을 기다리기 · `nil` 로 가지 끄기
- [31번 주제](../31-goroutine-leaks/)(누수) — ★ 막힌 채 남는 고루틴 · 교착 탐지를 가리는 쪽
- [32번 주제](../32-sync-mutex-rwmutex-waitgroup-once/)(`sync`) — 채널 대 뮤텍스
- [목록의 **34번 주제**](../34-context-cancellation-deadlines-and-values/)(`context`) · **36번 주제**(메모리 모델)
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **51번**(`mpsc` 채널) — 송신자 드롭이 닫힘, 받는 쪽이 떠나면 `Err`

## 용어 풀이

- **채널** — 고루틴 사이에 값을 보내고 받는 통로. `make(chan T, n)`.
- **버퍼(용량)** — 채널이 받는 쪽 없이 쥐고 있을 수 있는 값의 수. 0 이면 손에서 손으로.
- **방향 채널** — `chan<- T`(보내기 전용)·`<-chan T`(받기 전용). 컴파일 시점의 제약.
- **`close`** — 「더 안 보낸다」는 보내는 쪽의 선언. 받는 쪽은 남은 값을 받은 뒤 영값·`ok=false`.
- **`nil` 채널** — `make` 하지 않은 채널. 송수신이 영원히 막힌다.
- **교착(deadlock)** — 서로 기다려 아무도 못 나아가는 상태.
- **교착 탐지** — 모든 고루틴이 잠들면 런타임이 `fatal error: all goroutines are asleep - deadlock!` 으로 끝내는 것. **구현**이고 타이머가 있으면 안 한다.
- **`fatal error`** — 런타임이 프로세스를 끝내는 오류. `panic` 과 달리 `recover` 로 못 잡는다. 종료 코드 2.

---

## 더 들어가면

- ★ **채널 내부 구조**(`hchan`·송신 대기열 `sendq`·수신 대기열 `recvq`)는 **안 열었다** — 구현이고, 이 문서의 결론은 명세로 선다.
- ★ **`select` 로 막히지 않고 보내기·받기**는 [30번 주제](../30-select-default-and-timeouts/)다.
- ★ **닫힌 채널에 보내는 패닉을 `recover` 로 받는 것**은 **안 던졌다** — 할 수는 있지만(`panic` 이니까) 설계가 틀린 신호다.
- ★★ 채널 연산의 **시간 비용**은 **안 쟀다.**

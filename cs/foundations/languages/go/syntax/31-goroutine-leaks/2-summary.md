# go/syntax/31 — ★ 고루틴 누수 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [`runtime/pprof`](https://pkg.go.dev/runtime/pprof)(`goroutineleak` 프로파일) · [`testing/synctest`](https://pkg.go.dev/testing/synctest) ·
> [`context`](https://pkg.go.dev/context) · [`time.After`](https://pkg.go.dev/time#After) · [GODEBUG](https://go.dev/doc/godebug) 문서 · `runtime/mgc.go` 소스.
> 문서·소스·`api/go1NN.txt` 는 **이 툴체인의 `$(go env GOROOT)` 에서 직접 떴다.**\
> **실행 검증** — 이 문서의 출력은 전부 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.
> 소스 펜스도 같은 파일에서 떠 왔다. 손으로 옮겨 적은 블록은 없다.\
> ★★ **버전** — `testing/synctest` 의 `Test`·`Wait` 가 **1.25**(`api/go1.25.txt:107-108`), `Sleep` 이 **1.27**(`api/go1.27.txt:288`) ·
> `time.After` 의 타이머를 **GC 가 회수하는 것이 1.23** · 그것을 되돌리던 **`asynctimerchan` 설정이 1.27 에서 제거**((7)절 — ★ **그래서 이 툴체인으로는 판 격자를 못 돌린다**, 제3의 상태) ·
> ★★★ **`goroutineleak` 프로파일이 이 판의 `runtime/pprof` 에 기본으로 들어 있다**((2)절 — 이 판에 **있다는 것**만 확인했다. **몇 판부터인지는 못 확인했다** — `api/` 에 새 식별자가 없는 이름 문자열이라서다).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체는 넷째 창이다** — 「**`NumGoroutine` 이 1초 안에 시작 값으로 「돌아왔나」를 참거짓으로 남기는 창**」.
「몇 개가 샜나」의 절댓값보다 **「줄었나 / 안 줄었나」가 안 흔들린다** — 누수는 **안 줄어드는 것**이다.
누수 네 모양 × 처방을 이 창 하나로 가른다((1)·(3)절).
★★★ **제5의 상태 — 「누수를 「수」가 아니라 「멈춘 자리」로 물었다」.** 이 판의 **`goroutineleak` 프로파일**이
GC 로 **「닿을 수 없는 채널에 막힌 고루틴」** 을 찾아 **`[chan send (leaked)]`** 라고 **줄 번호째** 짚는다((2)절).
그리고 **`testing/synctest`** 가 「**버블 안의 모든 고루틴이 막혔다**」를 테스트 실패로 바꾼다((5)절).
★★ 바꾼 창들의 한계도 같은 블록이 보였다 — **티커 루프(취소 없는 대기)는 `NumGoroutine` 에만 잡히고 누수 프로파일은 0** 이다.

★★★ **이 주제의 경계** — 실패 모드 **총론**(조용한 실패·연쇄 장애·자원 고갈의 분류)은
[`../../../../../ops-patterns/failure-modes/`](../../../../../ops-patterns/failure-modes/)가 정본이다.
**그쪽은 실패를 분류하고 읽는 순서까지**, 여기는 **Go 고루틴이 막힌 채 남는 네 모양과 그것을 코드·테스트로 잡는 법부터.**
취소 신호 `context` 의 **API 전체**(데드라인·값·전파)는 [목록의 **34번 주제**](../34-context-cancellation-deadlines-and-values/)다 — 여기서는 **처방 하나**로만 쓴다.

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **명세 보장** | Go 명세가 약속한 것 | ★★ **막힌 송수신은 영원히 막힌다**([29번 주제](../29-channels-buffering-direction-close-range-and-nil/)) · **`main` 이 반환하면 다른 고루틴을 기다리지 않는다**([28번 주제](../28-goroutines-go-statement-cost-and-termination/)) — ★ **명세에는 「누수」도 「고루틴 회수」도 없다** |
| **구현(runtime)·표준 라이브러리** | `runtime`·`pprof`·`testing`·`time` 이 한 것 | ★★★ **`NumGoroutine` 이 막힌 것도 센다** · ★★★ **`goroutineleak` 프로파일이 GC 로 닿을 수 없는 채널에 막힌 고루틴을 찾는다** · **`synctest` 버블의 교착 판정** · **1.23 부터 타이머를 GC 가 회수** · `context` 의 취소 |
| **이 판의 관찰** | go1.27.1·linux/amd64 에서 이번에 본 것 | 네 모양의 `NumGoroutine`·프로파일 수 · 테스트 결과(재실행 대조까지) |

★★★ **선을 긋는다** — 「막힌 고루틴은 **아무도 안 치운다**」는 명세에서 **나오는 결론**이다(막힘이 영원하고, 고루틴을 없애는 문법이 없다).
「**그 고루틴을 GC 가 찾아 `leaked` 로 표시한다**」는 **이 판 런타임의 기능**이다 — ★ **표시할 뿐 치우지 않는다**((2)절 — 표시 뒤에도 `NumGoroutine` 이 그대로다).

## 이 판

```text
===== 명령: go version =====
go version go1.27.1 linux/amd64
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | ★★ **프로파일·`synctest` 트레이스의 `goroutine N` 의 N** | 런타임이 매기는 고루틴 id — 정규화 규칙 `([Gg]oroutine) \d+` **하나**를 더했다((2)·(5)절). [27번 주제](../27-panic-recover-and-where-to-use-them/)의 규칙을 넓힌 것이다 |
| **흔들린다** | 프로파일의 `@ 0x47d84a …` 주소 · 트레이스의 인자 주소 | 기본 정규화 규칙(주소)이 잡는다 |
| **흔들린다** | `go test` 의 `(0.50s)`·`0.505s` | 기본 정규화 규칙(시간)이 잡는다 |
| 안 흔들린다 | ★★★ **「1초 안에 1 로 돌아왔나 : true / false」** · `NumGoroutine` **1 · 11** | 막힌 고루틴은 만든 대로 남는다 — 이 주제의 핵심 근거 |
| 안 흔들린다 | ★★★ **`goroutineleak` 프로파일의 수(`10 · 10 · 0 · 10`)** · **`(leaked)` 표시가 붙은 줄** · `파일:줄` | GC 의 도달성 판정이다 — 재실행에서 같았다 |
| 안 흔들린다 | `--- FAIL`·`--- PASS` · `시작 2 → 끝 4` · 종료 코드 | |

★ 정규화 규칙은 **기본 넷 + 고루틴 id 하나**를 썼다.

## 한눈에 — 쉽게 말하면

**고루틴 누수는 「퇴근을 못 하는 직원」이다.** 일을 맡겼는데 **결과를 받으러 올 사람이 사라졌거나**, **일감을 줄 사람이 안 오거나**,
**「그만하라」는 말을 전할 방법이 없거나**, **「오늘 일 끝」 방송을 아무도 안 했다.**
직원은 **자리에 앉은 채 영원히 기다린다.** 회사는 **월급(스택·메모리)을 계속 낸다.** 누가 치워 주지도 않는다.

| 비유 | 실체 |
|---|---|
| 결과를 받으러 올 사람이 **먼저 퇴근** | ★★★ **① 받는 쪽이 사라진 송신** — 타임아웃으로 떠난 뒤 `res <- v` 가 영원히 막힌다 |
| 일감을 줄 사람이 **안 온다** | ★★★ **② 보내는 쪽 없는 수신** — 아무도 안 보내고 안 닫는 채널에서 `<-ch` |
| 「그만하라」를 **전할 방법이 없다** | ★★★ **③ 취소 없는 대기** — 티커 루프에 멈출 신호가 없다 |
| 「오늘 일 끝」 **방송을 안 했다** | ★★★ **④ 끝나지 않는 `range`** — 보내는 쪽이 `close` 를 잊었다 |
| 출근부를 센다 | ★★ **`runtime.NumGoroutine()`** — 막혀 있어도 센다 |
| 경비원이 **「아무도 찾아올 수 없는 방」에 갇힌 직원**을 찾아낸다 | ★★★ **`goroutineleak` 프로파일** — GC 가 **닿을 수 없는 채널에 막힌** 고루틴을 짚는다 |
| 경비원 눈에는 **알람 맞춰 놓고 조는 직원**은 일하는 사람으로 보인다 | ★★ **③ 은 프로파일에 안 잡힌다**(0) — 타이머가 깨워 주니까 |
| 모의 근무일을 **가짜 시계**로 돌려 퇴근 못 한 직원을 찾는다 | ★★ **`testing/synctest`** — 버블 안이 다 막히면 테스트가 실패한다 |

```text
   ★★★ 누수 네 모양 — 각각 무엇에 막혀 있나 ((1)절의 실측, 10번씩 불렀다)

   ① 받는 쪽이 사라진 송신            ② 보내는 쪽 없는 수신
      call ──go──▶ [일꾼] res <- 42       [대기] <-ch
        │ 1ms 시간 초과                     ch 를 아무도 안 보내고 안 닫는다
        └──▶ return  (res 를 받을 쪽 없음)
      NumGoroutine 11 · 안 줄어듦           NumGoroutine 11 · 안 줄어듦
      leak 프로파일 10                      leak 프로파일 10

   ③ 취소 없는 대기                   ④ 끝나지 않는 range
      [폴러] for range ticker.C {}        [생산] 0,1,2 를 보내고 return (close 없음)
        멈추라는 통로가 없다                [소비] for range ch { }  ← 넷째를 기다린다
      NumGoroutine 11 · 안 줄어듦           NumGoroutine 11 · 안 줄어듦
      ★ leak 프로파일 0                    leak 프로파일 10
```

```text
   ★★ 처방 — 무엇이 누구를 풀어 주나 ((3)절의 실측)

   ① → 결과 채널 버퍼 1        일꾼이 보낼 자리가 한 번 있다 → 끝난다      1 로 돌아옴 true
       단, 일꾼이 두 번 보내면  둘째에서 막힌다                              ★ false
   ② → context 로 끝낼 가지    select { case <-ch: case <-ctx.Done(): }     cancel 뒤 true
   ③ → context + Ticker.Stop    case <-ctx.Done(): return                    cancel 뒤 true
   ④ → 보내는 쪽 defer close   소비자의 range 가 끝난다                     1 로 돌아옴 true
```

> **고루틴 누수(goroutine leak)** — 끝날 길 없이 막힌 채 남는 고루틴. **에러도 경고도 없고**, 프로그램은 계속 돈다 — 스택과 그 고루틴이 붙든 메모리만 는다.

> **`goroutineleak` 프로파일** — 이 판 `runtime/pprof` 의 기본 프로파일. 문서 한 줄 「**goroutineleak - stack traces of all leaked goroutines**」.

> **`testing/synctest`** — 고루틴을 **버블**이라는 격리된 칸에서 돌리고 **가짜 시계**를 주는 테스트 패키지(1.25).

- [30번 주제](../30-select-default-and-timeouts/)가 목록상 **선행**이다 — 30편 (4)절이 「**타임아웃 뒤 400ms 에도 `NumGoroutine: 2`**」로 이 문서의 ① 을 이미 보였다.
- ★★ [28번 주제](../28-goroutines-go-statement-cost-and-termination/) (2)절이 「**받을 쪽 없는 10개는 1초를 기다려도 11**」 과 `settle` 함수를 세웠다 — 이 문서는 **그 창을 그대로** 네 모양에 건다.
- ★★ [29번 주제](../29-channels-buffering-direction-close-range-and-nil/) (8)절이 「**채널에 막힌 고루틴은 교착 탐지를 못 가리고, 타이머를 쥔 고루틴이 가린다**」를 보였다 — ③ 이 바로 그 「가리는」 쪽이다.
- ★ [26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/)가 루프 안 `defer` 의 **fd 가 「늘었나」를** `/proc/self/fd` 로 셌다 — 이 문서는 같은 질문(「늘었나」)을 **고루틴 수**로 묻는다.

## 이 주제가 답하려는 질문

1. **고루틴은 어떤 모양으로 새나** — 네 모양을 코드에서 짚을 수 있나.
2. **새는지 어떻게 아나** — 수(`NumGoroutine`) · 멈춘 자리(프로파일) · 테스트(`synctest`), 그리고 **각 창이 못 보는 것**.
3. **어떻게 고치나** — 버퍼 1 은 **언제만** 맞나, 취소는 어떻게 주나.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **`NumGoroutine` 수렴 참거짓** | **줄었나 / 안 줄었나** | ★ 본체 창 — [28번 주제](../28-goroutines-go-statement-cost-and-termination/)의 `settle` |
| ★★★ **`goroutineleak` 프로파일** | **어디서 멈췄나**(`파일:줄`)와 **`(leaked)` 판정** | ★ **제5의 상태** — 수가 아니라 멈춘 자리로 물었다 |
| ★★ **`goroutine` 프로파일** | 지금 있는 고루틴 **전부**의 스택 | `runtime/pprof` |
| ★★ **`go test` 의 전후 비교** | 테스트가 **누수를 실패로** 바꾼다 | `t.Cleanup` + `NumGoroutine` |
| ★★ **`testing/synctest`** | 버블 안이 **전부 막혔다**를 테스트가 안다 | 1.25 |
| ★ **`go vet` 의 침묵** | 누수를 **정적 분석이 못 본다** | 규칙 18-A |
| **못 잰 것 — `goleak`** | ★★ **이 환경에 없다**((4)절 판별 블록). 외부 모듈을 받지 않았다 — 대신 위의 두 표준 창으로 같은 질문을 물었다 | 규칙 26 |
| **못 잰 것 — `time.After` 판 격자** | ★★ **`asynctimerchan` 이 1.27 에서 제거**돼 1.22 의미를 되살릴 수 없다((7)절 — 런타임이 **그 설정을 거부**한다) | 제3의 상태 |
| **부적용 — `-race`** | 누수는 **데이터 경쟁이 아니다** — 이 문서의 블록에는 공유 변수 쓰기가 없다 | [목록의 **35번 주제**](../35-data-races-and-the-race-detector/) |
| **부적용 — 메모리 절댓값** | 샌 고루틴이 **몇 바이트**인지는 안 실었다. 스택 크기는 **구현**([28번 주제](../28-goroutines-go-statement-cost-and-termination/) (5)절) | — |

### (1) ★★★ 누수 네 모양 × `NumGoroutine` × 누수 프로파일

**언제 쓰나** — 「이 고루틴은 **무엇이 오면** 끝나나」를 코드 리뷰에서 물을 때. 네 모양을 **10번씩** 부르고 세 창으로 셌다.

```text
===== 소스: t31shapes.go =====
package main

import (
	"fmt"
	"os"
	"runtime"
	"runtime/pprof"
	"time"
)

// ① 받는 쪽이 사라진 송신 — 부른 쪽이 시간 초과로 먼저 떠난다
func sendNoRecv() {
	res := make(chan int)
	go func() {
		time.Sleep(20 * time.Millisecond)
		res <- 42
	}()
	select {
	case <-res:
	case <-time.After(time.Millisecond):
	}
}

// ② 보내는 쪽 없는 수신 — 아무도 안 보내고 안 닫는다
func recvNoSend() {
	ch := make(chan int)
	go func() { <-ch }()
}

// ③ 취소 없는 대기 — 멈추라는 신호를 받을 통로가 없다
func noCancel() {
	go func() {
		t := time.NewTicker(time.Millisecond)
		for range t.C {
		}
	}()
}

// ④ 끝나지 않는 range — 보내는 쪽이 close 를 잊었다
func rangeNoClose() {
	ch := make(chan int)
	go func() {
		for i := range 3 {
			ch <- i
		}
	}()
	go func() {
		for range ch {
		}
	}()
}

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
	shapes := map[string]func(){
		"sendNoRecv": sendNoRecv, "recvNoSend": recvNoSend,
		"noCancel": noCancel, "rangeNoClose": rangeNoClose,
	}
	f := shapes[os.Args[1]]
	fmt.Println("시작 NumGoroutine            :", runtime.NumGoroutine())
	for range 10 {
		f()
	}
	time.Sleep(100 * time.Millisecond)
	fmt.Println("10번 부른 뒤 NumGoroutine    :", runtime.NumGoroutine())
	fmt.Println("1초 안에 1 로 돌아왔나       :", settle(1))
	fmt.Println("goroutineleak 프로파일의 수  :", leaked())
}

func leaked() int {
	p := pprof.Lookup("goroutineleak")
	p.WriteTo(new(discard), 0) // 쓰기가 누수 탐지 GC 를 한 번 돌린다
	return p.Count()
}

type discard struct{}

func (discard) Write(b []byte) (int, error) { return len(b), nil }
===== 명령: go build -trimpath -o prog . && for s in sendNoRecv recvNoSend noCancel rangeNoClose; do echo "--- $s"; ./prog $s; done =====
--- sendNoRecv
시작 NumGoroutine            : 1
10번 부른 뒤 NumGoroutine    : 11
1초 안에 1 로 돌아왔나       : false
goroutineleak 프로파일의 수  : 10
--- recvNoSend
시작 NumGoroutine            : 1
10번 부른 뒤 NumGoroutine    : 11
1초 안에 1 로 돌아왔나       : false
goroutineleak 프로파일의 수  : 10
--- noCancel
시작 NumGoroutine            : 1
10번 부른 뒤 NumGoroutine    : 11
1초 안에 1 로 돌아왔나       : false
goroutineleak 프로파일의 수  : 0
--- rangeNoClose
시작 NumGoroutine            : 1
10번 부른 뒤 NumGoroutine    : 11
1초 안에 1 로 돌아왔나       : false
goroutineleak 프로파일의 수  : 10
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **네 모양 모두 `1 → 11`, 「1초 안에 1 로 돌아왔나 : false」** — 10번 부른 만큼 **그대로 남았다.** 1초를 기다려도 **하나도 안 줄었다.**
  ★ **에러·패닉·경고는 한 줄도 없다** — `exit 0` 이다. 누수는 **조용하다.**
- ★★★ **① `sendNoRecv`** — `call` 이 **1ms 에 시간 초과로 떠나고**, 일꾼은 20ms 뒤 `res <- 42` 에서 **받을 쪽 없이** 막혔다([30번 주제](../30-select-default-and-timeouts/) (4)절과 같은 모양).
- ★★★ **② `recvNoSend`** — `<-ch` 를 기다리는데 **`ch` 는 함수가 반환하며 아무도 모르는 채널**이 됐다.
- ★★★ **③ `noCancel`** — 티커 루프는 **막혀 있지 않다** — 1ms 마다 깨어 돈다. **멈추라는 통로가 없을 뿐**이다.
- ★★★ **④ `rangeNoClose`** — 생산자는 **3 개를 보내고 끝났고**(그 10 개는 사라졌다), 소비자 10 개가 **넷째를 기다린다**([29번 주제](../29-channels-buffering-direction-close-range-and-nil/) (6)절).
- ★★★ **누수 프로파일은 `10 · 10 · 0 · 10`** — ① ② ④ 는 **정확히 10** 을 짚었고, **③ 은 0** 이다. ③ 의 고루틴은 **타이머가 깨워 주는** 살아 있는 고루틴이라 「leaked」 판정 대상이 아니다.
  ★★ 그래서 ③ 은 **`NumGoroutine` 으로만 보인다** — 창을 하나만 믿으면 놓친다. 이것이 [29번 주제](../29-channels-buffering-direction-close-range-and-nil/) (8)절에서 **교착 탐지를 가리던** 그 모양이기도 하다.

비용 — 없다(재지 않았다). 샌 고루틴의 **메모리**는 안 실었다.

### (2) ★★★ 어디서 멈췄나 — `goroutineleak` 프로파일 (제5의 상태)

**언제 쓰나** — 「`NumGoroutine` 이 계속 는다」까지 알았는데 **어느 줄**인지 모를 때.

먼저 이 판에 **있나** — 문서와 소스로 판별했다:

```text
===== 명령: sed -n "108,110p;784,785p" "$(go env GOROOT)/src/runtime/pprof/pprof.go"; sed -n "1274,1277p" "$(go env GOROOT)/src/runtime/mgc.go"; echo "godebug.md 에서 leak 이 나오는 줄 수: $(grep -ci leak "$(go env GOROOT)/doc/godebug.md")" =====
//	goroutine      - stack traces of all current goroutines
//	goroutineleak  - stack traces of all leaked goroutines
//	allocs         - a sampling of all past memory allocations
// writeGoroutineLeak first invokes a GC cycle that performs goroutine leak detection.
// It then writes the goroutine profile, filtering for leaked goroutines.
// findGoroutineLeaks scans the remaining stackRoots and marks any which are
// blocked over exclusively unreachable concurrency primitives as leaked (deadlocked).
// Returns true if the goroutine leak check was performed (or unnecessary).
// Returns false if the GC cycle has not yet computed all maybe-runnable goroutines.
godebug.md 에서 leak 이 나오는 줄 수: 0
(exit 0)
```

- ★★★ **`goroutineleak  - stack traces of all leaked goroutines`** — 이 판 `runtime/pprof` 의 **기본 프로파일 목록**에 있다.
- ★★ 둘째 문단 — 「**writeGoroutineLeak first invokes a GC cycle that performs goroutine leak detection.**」 **쓰는 순간 GC 를 한 번 돌려** 판정한다.
- ★★★ `mgc.go` 의 `findGoroutineLeaks` — 「**marks any which are blocked over exclusively unreachable concurrency primitives as leaked (deadlocked)**」.
  ★ **GC 의 도달성**으로 판정한다 — 막힌 채널에 **아무도 닿을 수 없으면** 그 고루틴은 영원히 못 깨어난다.
- ★ `GODEBUG` 에는 누수 관련 설정이 **없다**(`godebug.md` 에서 `leak` 이 나오는 줄 **0**) — 브리핑이 「`GODEBUG` 로 멈춘 자리를 찍어라」라 했는데, **이 판에서 그 역할을 하는 것은 `GODEBUG` 가 아니라 이 프로파일**이다.

그리고 **두 프로파일을 나란히** — 누수 셋(①)과 티커 하나(③)를 만들었다:

```text
===== 소스: t31prof.go =====
package main

import (
	"os"
	"runtime/pprof"
	"time"
)

func sendNoRecv() {
	res := make(chan int)
	go func() { res <- 42 }()
}

func poller() {
	go func() {
		t := time.NewTicker(time.Millisecond)
		for range t.C {
		}
	}()
}

func main() {
	for range 3 {
		sendNoRecv()
	}
	poller()
	time.Sleep(50 * time.Millisecond)
	os.Stdout.WriteString("===== goroutineleak (debug=1)\n")
	pprof.Lookup("goroutineleak").WriteTo(os.Stdout, 1)
	os.Stdout.WriteString("===== goroutine (debug=1)\n")
	pprof.Lookup("goroutine").WriteTo(os.Stdout, 1)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
===== goroutineleak (debug=1)
goroutineleak profile: total 3
3 @ 0x47d84a 0x41421c 0x413e17 0x4dec3e 0x4836a1
#	0x4dec3d	main.sendNoRecv.func1+0x1d	ex/t31prof.go:11

===== goroutine (debug=1)
goroutine profile: total 5
3 @ 0x47d84a 0x41421c 0x413e17 0x4dec3e 0x4836a1
#	0x4dec3d	main.sendNoRecv.func1+0x1d	ex/t31prof.go:11

1 @ 0x440e31 0x47cbbd 0x4ccaf1 0x4cc7c5 0x4c9729 0x4debf0 0x44aa47 0x4836a1
#	0x4ccaf0	runtime/pprof.writeRuntimeProfile+0xb0	runtime/pprof/pprof.go:848
#	0x4cc7c4	runtime/pprof.writeGoroutine+0x44	runtime/pprof/pprof.go:781
#	0x4c9728	runtime/pprof.(*Profile).WriteTo+0x148	runtime/pprof/pprof.go:405
#	0x4debef	main.main+0xef				ex/t31prof.go:31
#	0x44aa46	runtime.main+0x426			runtime/proc.go:302

1 @ 0x47d84a 0x41514e 0x414c92 0x4decaf 0x4836a1
#	0x4decae	main.poller.func1+0x4e	ex/t31prof.go:17
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`goroutineleak profile: total 3`** — ① 셋만, **`main.sendNoRecv.func1 … ex/t31prof.go:11`** 로 **줄 번호째** 짚었다.
- ★★ **`goroutine profile: total 5`** — **전부**(main·프로파일러 자신·① 셋·③ 하나). ③ 의 **`main.poller.func1 … t31prof.go:17`** 은 **여기에만** 있다.
- ★★ 그래서 쓰는 법이 갈린다 — **누수 프로파일은 「확실히 샌 것」**(오탐이 없는 쪽), **고루틴 프로파일은 「있는 것 전부」**(사람이 골라야 하는 쪽).
- ★ `@ 0x…` 주소는 흔들린다 — 기본 정규화 칸.

`debug=2` 로 찍으면 **상태 표시**가 보인다 — 전역 채널에 막힌 것과 나란히:

```text
===== 소스: t31prof2.go =====
package main

import (
	"os"
	"runtime/pprof"
	"time"
)

func sendNoRecv() {
	res := make(chan int)
	go func() { res <- 42 }()
}

var kept = make(chan int) // 전역 — 누가 언젠가 받을 수도 있다

func sendKept() {
	go func() { kept <- 42 }()
}

func main() {
	sendNoRecv()
	sendKept()
	time.Sleep(50 * time.Millisecond)
	pprof.Lookup("goroutineleak").WriteTo(os.Stdout, 2)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
goroutine 1 [running]:
runtime/pprof.writeGoroutineStacks({0x5dff90, 0x2777d68d6030})
	runtime/pprof/pprof.go:816 +0x69
runtime/pprof.writeGoroutineLeak({0x5dff90, 0x2777d68d6030}, 0x2)
	runtime/pprof/pprof.go:803 +0xa8
runtime/pprof.(*Profile).WriteTo(0x4e04a7?, {0x5dff90?, 0x2777d68d6030?}, 0x2777d68d81e0?)
	runtime/pprof/pprof.go:405 +0x149
main.main()
	ex/t31prof2.go:24 +0x4e

goroutine 7 [chan send (leaked)]:
main.sendNoRecv.func1()
	ex/t31prof2.go:11 +0x1e
created by main.sendNoRecv in goroutine 1
	ex/t31prof2.go:11 +0x67

goroutine 8 [chan send]:
main.sendKept.func1()
	ex/t31prof2.go:17 +0x25
created by main.sendKept in goroutine 1
	ex/t31prof2.go:17 +0x1a
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`goroutine N [chan send (leaked)]:` — `main.sendNoRecv.func1()`** · 반면 **`goroutine N [chan send]:` — `main.sendKept.func1()`** 에는 **`(leaked)` 가 없다.**
  둘 다 **똑같이 보내다 막혔다.** 차이는 **채널에 닿을 수 있나** 하나다 — `kept` 는 **전역 변수**라 「언젠가 누가 받을 수도 있다」.
  ★★★ **그래서 이 프로파일은 전역·필드에 붙은 채널의 누수를 못 본다** — 바꾼 창의 한계다(규칙 18-B 의 「바꾼 창이 무엇을 못 보는지」).
- ★★ 판정 뒤에도 **고루틴은 치워지지 않는다** — 표시만 한다(`(leaked)` 상태로 남는다). `NumGoroutine` 은 그대로 센다((1)절의 `11`).
- ★ 고루틴 id 는 흔들린다 — 머리말의 정규화 칸.

비용 — **프로파일을 쓸 때 GC 를 한 번 돈다**(위 주석 — 이 문서는 그 시간을 **안 쟀다**).

### (3) ★★★ 고치기 — 버퍼 1 · `context` · `close`

**언제 쓰나** — (1)절의 네 모양을 고칠 때. **같은 창**(`NumGoroutine` 이 1 로 돌아오나)으로 확인했다.

```text
===== 소스: t31fix.go =====
package main

import (
	"context"
	"fmt"
	"os"
	"runtime"
	"time"
)

// ① 처방 — 결과 채널에 버퍼 1: 받는 쪽이 떠나도 한 번은 보낼 자리가 있다
func buf1() {
	res := make(chan int, 1)
	go func() {
		time.Sleep(20 * time.Millisecond)
		res <- 42
	}()
	select {
	case <-res:
	case <-time.After(time.Millisecond):
	}
}

// ①' 같은 처방인데 고루틴이 두 번 보낸다
func buf1Twice() {
	res := make(chan int, 1)
	go func() {
		time.Sleep(20 * time.Millisecond)
		res <- 1
		res <- 2
	}()
	select {
	case <-res:
	case <-time.After(time.Millisecond):
	}
}

// ②·③ 처방 — context 로 끝낼 통로를 준다
func ctxWait(ctx context.Context) {
	ch := make(chan int)
	go func() {
		select {
		case <-ch:
		case <-ctx.Done():
		}
	}()
}

func ctxTicker(ctx context.Context) {
	go func() {
		t := time.NewTicker(time.Millisecond)
		defer t.Stop()
		for {
			select {
			case <-t.C:
			case <-ctx.Done():
				return
			}
		}
	}()
}

// ④ 처방 — 보내는 쪽이 끝나면 닫는다
func closeRange() {
	ch := make(chan int)
	go func() {
		defer close(ch)
		for i := range 3 {
			ch <- i
		}
	}()
	go func() {
		for range ch {
		}
	}()
}

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
	ctx, cancel := context.WithCancel(context.Background())
	fixes := map[string]func(){
		"buf1": buf1, "buf1Twice": buf1Twice,
		"ctxWait":    func() { ctxWait(ctx) },
		"ctxTicker":  func() { ctxTicker(ctx) },
		"closeRange": closeRange,
	}
	for range 10 {
		fixes[os.Args[1]]()
	}
	time.Sleep(100 * time.Millisecond)
	fmt.Printf("[%s] 100ms 뒤 NumGoroutine: %d", os.Args[1], runtime.NumGoroutine())
	cancel()
	fmt.Printf(" · cancel 뒤 1초 안에 1 로 돌아왔나: %v\n", settle(1))
}
===== 명령: go build -trimpath -o prog . && for s in buf1 buf1Twice ctxWait ctxTicker closeRange; do ./prog $s; done =====
[buf1] 100ms 뒤 NumGoroutine: 1 · cancel 뒤 1초 안에 1 로 돌아왔나: true
[buf1Twice] 100ms 뒤 NumGoroutine: 11 · cancel 뒤 1초 안에 1 로 돌아왔나: false
[ctxWait] 100ms 뒤 NumGoroutine: 11 · cancel 뒤 1초 안에 1 로 돌아왔나: true
[ctxTicker] 100ms 뒤 NumGoroutine: 11 · cancel 뒤 1초 안에 1 로 돌아왔나: true
[closeRange] 100ms 뒤 NumGoroutine: 1 · cancel 뒤 1초 안에 1 로 돌아왔나: true
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`buf1` — 100ms 뒤 이미 1.** 결과 채널에 **버퍼 1** 을 주면 받는 쪽이 떠나도 일꾼이 **한 번은 넣고 끝난다.**
- ★★★ **`buf1Twice` — 11, 1초 뒤에도 `false`.** **같은 처방인데 일꾼이 두 번 보내면** 둘째에서 막힌다.
  ★★★ **버퍼 1 은 「보내는 횟수가 정확히 1 이고, 그 결과를 버려도 되는」 경우에만 맞는 처방**이다.
  보내는 횟수가 N 이면 버퍼 N — 그런데 **N 을 모르면**(스트림) 버퍼로는 못 고친다. 취소 신호가 필요하다.
- ★★★ **`ctxWait`·`ctxTicker` — 100ms 뒤에는 11(아직 기다리는 중), `cancel()` 뒤 1초 안에 1.** `select` 에 **`<-ctx.Done()` 가지**를 준 것이 **끝낼 통로**다.
  ★ 티커는 **`defer t.Stop()`** 도 같이 — 고루틴이 끝나도 멈추지 않은 티커가 남지 않게.
- ★★★ **`closeRange` — 100ms 뒤 이미 1.** 생산자가 **`defer close(ch)`** 하니 소비자의 `range` 가 끝났다.
- ★ `context` 의 정본은 [목록의 **34번 주제**](../34-context-cancellation-deadlines-and-values/)다 — 여기서는 「**`Done()` 은 취소되면 닫히는 채널**」 하나만 썼다([30번 주제](../30-select-default-and-timeouts/) (7)절).

비용 — 없다.

### (4) ★★★ 테스트로 잡기 — 시작 전후 `NumGoroutine`

**언제 쓰나** — 누수가 **다시 생기지 않게** 막을 때. 테스트마다 시작 값을 재 두고 끝날 때 **돌아왔나**를 본다.

```text
===== 소스: t31leak_test.go =====
package ex

import (
	"runtime"
	"testing"
	"time"
)

// noLeak 은 테스트가 끝날 때 NumGoroutine 이 시작 값으로 돌아왔는지 본다.
func noLeak(t *testing.T) {
	before := runtime.NumGoroutine()
	t.Cleanup(func() {
		for deadline := time.Now().Add(500 * time.Millisecond); time.Now().Before(deadline); {
			if runtime.NumGoroutine() <= before {
				return
			}
			time.Sleep(time.Millisecond)
		}
		t.Errorf("고루틴 수: 시작 %d → 끝 %d", before, runtime.NumGoroutine())
	})
}

func first(results []int, bufSize int) int {
	ch := make(chan int, bufSize)
	for _, r := range results {
		go func() { ch <- r }()
	}
	return <-ch // 첫 결과만 쓴다
}

func TestFirstUnbuffered(t *testing.T) {
	noLeak(t)
	if got := first([]int{1, 2, 3}, 0); got == 0 {
		t.Fatal("결과 없음")
	}
}

func TestFirstBuffered(t *testing.T) {
	noLeak(t)
	if got := first([]int{1, 2, 3}, 3); got == 0 {
		t.Fatal("결과 없음")
	}
}
===== 명령: go test -trimpath -count=1 -v . =====
=== RUN   TestFirstUnbuffered
    t31leak_test.go:19: 고루틴 수: 시작 2 → 끝 4
--- FAIL: TestFirstUnbuffered (0.50s)
=== RUN   TestFirstBuffered
--- PASS: TestFirstBuffered (0.00s)
FAIL
FAIL	ex	0.506s
FAIL
(exit 1)
```

그림 해설 (한 단계씩):

- ★★★ **`TestFirstUnbuffered` 가 `FAIL` — 「고루틴 수: 시작 2 → 끝 4」.** 결과 셋 중 **첫 것만** 받으니 나머지 **둘이** 버퍼 0 에 막혔다(① 모양).
- ★★★ **`TestFirstBuffered` 는 `PASS`** — 버퍼 3 이라 셋 다 넣고 끝났다(**보내는 횟수 = 버퍼**, (3)절의 조건).
- ★★ **시작 값이 1 이 아니라 2** 다 — 테스트 함수는 main 이 아니라 **`testing` 이 띄운 고루틴**에서 돈다((5)절 트레이스의 `created by testing.(*T).Run in goroutine 1`). 그래서 「1 로 돌아왔나」가 아니라 **「시작 값으로 돌아왔나」** 로 적었다.
- ★★ **500ms 를 기다리며** 본다 — [28번 주제](../28-goroutines-go-statement-cost-and-termination/) (2)절대로 `Done` 뒤 고루틴이 **사라지기까지 틈**이 있다. 기다리지 않으면 **깨끗한 코드도 가끔 실패**한다.
- ★ **한계** — 테스트가 **병렬**(`t.Parallel`)이면 다른 테스트의 고루틴이 섞여 이 비교가 **거짓 실패·거짓 통과**를 낸다. 이 문서는 **병렬을 안 던졌다.**

그 일을 대신해 주는 외부 도구(`go.uber.org/goleak`)는 — **판별부터**(규칙 26):

```text
===== 명령: cd "$(mktemp -d)" && printf "module probe\n\ngo 1.27\n" > go.mod && echo "모듈 캐시에 go.uber.org 가 있나: $(ls "$(go env GOMODCACHE)/go.uber.org" >/dev/null 2>&1 && echo 예 || echo 아니오)"; GOPROXY=off go get go.uber.org/goleak; echo "go get exit=$?" =====
모듈 캐시에 go.uber.org 가 있나: 아니오
go: go.uber.org/goleak: module lookup disabled by GOPROXY=off
go get exit=1
(exit 0)
```

- ★★ **모듈 캐시에 없고, `GOPROXY=off` 로 물으니 「module lookup disabled」** — 이 환경에는 **없다.** 받아 오지 않았다(외부 의존을 이 문서에 끌어들이지 않는다).
- ★★★ 그래서 **「못 잰 것」** 이다 — 그 대신 **표준만으로 같은 질문을** 두 창으로 물었다: 위의 전후 비교와 (5)절의 `synctest`.

비용 — 기다림 **500ms**(실패하는 테스트만 — `(0.50s)`).

### (5) ★★★ `testing/synctest` — 버블 안이 전부 막히면 테스트가 안다

**언제 쓰나** — 시간·고루틴이 얽힌 코드를 **결정적으로** 테스트할 때. **이 판에 있나부터**:

```text
===== 명령: cd "$(go env GOROOT)/api" && grep -n "testing/synctest" go1.25.txt go1.27.txt =====
go1.25.txt:107:pkg testing/synctest, func Test(*testing.T, func(*testing.T)) #67434
go1.25.txt:108:pkg testing/synctest, func Wait() #67434
go1.27.txt:288:pkg testing/synctest, func Sleep(time.Duration) #77169
(exit 0)
```

- ★★★ **`Test`·`Wait` 는 1.25**, **`Sleep` 은 1.27** — 이 판(1.27.1)에 **셋 다 있다.**

누수가 있는 코드를 버블 안에서 돌리면 —

```text
===== 소스: t31synctest_test.go =====
package ex

import (
	"testing"
	"testing/synctest"
	"time"
)

func firstOf(bufSize int) int {
	ch := make(chan int, bufSize)
	for i := 1; i <= 3; i++ {
		go func() { ch <- i }()
	}
	return <-ch
}

func TestBubbleUnbuffered(t *testing.T) {
	synctest.Test(t, func(t *testing.T) {
		firstOf(0)
	})
}

func TestBubbleBuffered(t *testing.T) {
	synctest.Test(t, func(t *testing.T) {
		firstOf(3)
	})
}

func TestBubbleClock(t *testing.T) {
	synctest.Test(t, func(t *testing.T) {
		start := time.Now()
		select {
		case <-make(chan int):
		case <-time.After(time.Hour):
		}
		t.Log("한 시간짜리 time.After 뒤 가짜 시계가 간 양:", time.Since(start))
	})
}
===== 명령: go test -trimpath -count=1 -v -run TestBubbleUnbuffered . =====
=== RUN   TestBubbleUnbuffered
--- FAIL: TestBubbleUnbuffered (0.00s)
panic: deadlock: main bubble goroutine has exited but blocked goroutines remain [recovered, repanicked]

goroutine 7 [running]:
testing.tRunner.func1.2({0x6c18b8, 0x2fd35b2d8198})
	testing/testing.go:2123 +0x232
testing.tRunner.func1()
	testing/testing.go:2126 +0x329
panic({0x6c18b8?, 0x2fd35b2d8198?})
	runtime/panic.go:859 +0x125
internal/synctest.Run(0x2fd35b37e160)
	runtime/synctest.go:247 +0x2dd
testing/synctest.Test(0x2fd35b3d2248, 0x6d4848)
	testing/synctest/synctest.go:291 +0x99
ex.TestBubbleUnbuffered(0x2fd35b3d2248?)
	ex/t31synctest_test.go:18 +0x1a
testing.tRunner(0x2fd35b3d2248, 0x6d4790)
	testing/testing.go:2193 +0xea
created by testing.(*T).Run in goroutine 1
	testing/testing.go:2258 +0x4d4

goroutine 10 [chan send (durable), synctest bubble 1]:
ex.firstOf.func1()
	ex/t31synctest_test.go:12 +0x1b
created by ex.firstOf in goroutine 9
	ex/t31synctest_test.go:12 +0x48

goroutine 11 [chan send (durable), synctest bubble 1]:
ex.firstOf.func1()
	ex/t31synctest_test.go:12 +0x1b
created by ex.firstOf in goroutine 9
	ex/t31synctest_test.go:12 +0x48
FAIL	ex	0.006s
FAIL
(exit 1)
```

그림 해설 (한 단계씩):

- ★★★ **`panic: deadlock: main bubble goroutine has exited but blocked goroutines remain`** — 버블의 주 함수가 **끝났는데 막힌 고루틴이 남았다**는 판정이다. 테스트는 **`FAIL`, exit 1.**
- ★★★ 남은 고루틴 **둘**이 **`[chan send (durable), synctest bubble 1]`** 로, **`ex/t31synctest_test.go:12`** 째 찍혔다 — (2)절의 누수 프로파일처럼 **「멈춘 자리」로 답한다.**
  ★ **`durable`** — 문서의 정의가 이렇다:

```text
===== 명령: go doc testing/synctest | sed -n "42,44p;63,70p" =====
A goroutine in a bubble is "durably blocked" when it is blocked and can only
be unblocked by another goroutine in the same bubble. A goroutine which can be
unblocked by an event from outside its bubble is not durably blocked.
When every goroutine in a bubble is durably blocked:

  - Wait returns, if it has been called.
  - Otherwise, time advances to the next time that will unblock at least one
    goroutine, if there is such a time and the root goroutine of the bubble has
    not exited.
  - Otherwise, there is a deadlock and Test panics.
(exit 0)
```

  ★★ 「**durably blocked … can only be unblocked by another goroutine in the same bubble**」 — 버블 **밖에서는 깨울 수 없는** 막힘이다.
  그리고 전부가 그렇게 막히면 **① `Wait` 가 돌아오거나 ② 시계가 다음 타이머로 건너뛰거나 ③ 「there is a deadlock and Test panics」** — 위 실패가 ③ 이다.
- ★★ **`[recovered, repanicked]`** — `testing` 이 패닉을 받아 **다시 던졌다**([27번 주제](../27-panic-recover-and-where-to-use-them/) (6)절의 표시). 그래서 **이 테스트 바이너리의 나머지 테스트는 안 돈다** — 아래 블록을 **따로** 돌렸다.
- ★ 고루틴 id·인자 주소·시간은 흔들린다 — 머리말의 정규화 칸.

고친 코드와 **가짜 시계** —

```text
===== 소스: t31synctest_test.go =====
package ex

import (
	"testing"
	"testing/synctest"
	"time"
)

func firstOf(bufSize int) int {
	ch := make(chan int, bufSize)
	for i := 1; i <= 3; i++ {
		go func() { ch <- i }()
	}
	return <-ch
}

func TestBubbleUnbuffered(t *testing.T) {
	synctest.Test(t, func(t *testing.T) {
		firstOf(0)
	})
}

func TestBubbleBuffered(t *testing.T) {
	synctest.Test(t, func(t *testing.T) {
		firstOf(3)
	})
}

func TestBubbleClock(t *testing.T) {
	synctest.Test(t, func(t *testing.T) {
		start := time.Now()
		select {
		case <-make(chan int):
		case <-time.After(time.Hour):
		}
		t.Log("한 시간짜리 time.After 뒤 가짜 시계가 간 양:", time.Since(start))
	})
}
===== 명령: go test -trimpath -count=1 -v -run "TestBubbleBuffered|TestBubbleClock" . =====
=== RUN   TestBubbleBuffered
--- PASS: TestBubbleBuffered (0.00s)
=== RUN   TestBubbleClock
    t31synctest_test.go:36: 한 시간짜리 time.After 뒤 가짜 시계가 간 양: 1h0m0s
--- PASS: TestBubbleClock (0.00s)
PASS
ok  	ex	0.004s
(exit 0)
```

- ★★ **`TestBubbleBuffered` — `PASS`.** 버퍼 3 이면 막힌 고루틴이 안 남는다.
- ★★★ **`TestBubbleClock` — 한 시간짜리 `time.After` 뒤 가짜 시계가 간 양: `1h0m0s`**, 테스트 시간은 **`(0.00s)`**.
  버블 안의 모든 고루틴이 막히면 **시계가 다음 타이머까지 건너뛴다**(위 문서의 ②). 한 시간을 **기다리지 않고** 「한 시간 뒤」를 시험한다.
- ★★★ **이것이 (4)절보다 나은 점** — 「**500ms 기다려 보고 수렴하나**」가 아니라 **「전부 막혔나」를 런타임이 결정적으로 안다.** 기다림도, 병렬 테스트의 섞임도 없다(버블이 격리한다).
- ★ **한계** — 버블 **밖**의 고루틴(전역 풀·다른 테스트가 만든 것)은 안 본다. 그리고 **③ 티커 루프**는 가짜 시계가 계속 깨우니 「막혔다」가 안 된다 — 이 문서는 **③ 을 버블에 넣어 보지 않았다.**

비용 — 없다(가짜 시계).

### (6) ★ 도구가 못 보는 것 — `go vet` 은 누수에 침묵한다

```text
===== 소스: t31shapes.go =====
package main

import (
	"fmt"
	"os"
	"runtime"
	"runtime/pprof"
	"time"
)

// ① 받는 쪽이 사라진 송신 — 부른 쪽이 시간 초과로 먼저 떠난다
func sendNoRecv() {
	res := make(chan int)
	go func() {
		time.Sleep(20 * time.Millisecond)
		res <- 42
	}()
	select {
	case <-res:
	case <-time.After(time.Millisecond):
	}
}

// ② 보내는 쪽 없는 수신 — 아무도 안 보내고 안 닫는다
func recvNoSend() {
	ch := make(chan int)
	go func() { <-ch }()
}

// ③ 취소 없는 대기 — 멈추라는 신호를 받을 통로가 없다
func noCancel() {
	go func() {
		t := time.NewTicker(time.Millisecond)
		for range t.C {
		}
	}()
}

// ④ 끝나지 않는 range — 보내는 쪽이 close 를 잊었다
func rangeNoClose() {
	ch := make(chan int)
	go func() {
		for i := range 3 {
			ch <- i
		}
	}()
	go func() {
		for range ch {
		}
	}()
}

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
	shapes := map[string]func(){
		"sendNoRecv": sendNoRecv, "recvNoSend": recvNoSend,
		"noCancel": noCancel, "rangeNoClose": rangeNoClose,
	}
	f := shapes[os.Args[1]]
	fmt.Println("시작 NumGoroutine            :", runtime.NumGoroutine())
	for range 10 {
		f()
	}
	time.Sleep(100 * time.Millisecond)
	fmt.Println("10번 부른 뒤 NumGoroutine    :", runtime.NumGoroutine())
	fmt.Println("1초 안에 1 로 돌아왔나       :", settle(1))
	fmt.Println("goroutineleak 프로파일의 수  :", leaked())
}

func leaked() int {
	p := pprof.Lookup("goroutineleak")
	p.WriteTo(new(discard), 0) // 쓰기가 누수 탐지 GC 를 한 번 돌린다
	return p.Count()
}

type discard struct{}

func (discard) Write(b []byte) (int, error) { return len(b), nil }
===== 명령: go vet . && echo "vet exit=$?" =====
vet exit=0
(exit 0)
```

- ★★★ **(1)절의 네 모양 전부가 든 파일에 `vet exit=0`, 한 줄도 없다.** 누수는 **「무엇이 이 채널에 보내나」라는 전역 질문**이라 한 함수만 보는 분석이 판단할 수 없다.
  ★ 탐침 **4 개**(네 모양), 답 **0 개**(규칙 18-A).

### (7) ★★ `time.After` 를 루프에서 — 고루틴 누수가 아니고, 1.23 부터는 메모리 누수도 아니다

**언제 쓰나** — `for { select { case <-ch: case <-time.After(d): } }` 를 볼 때. 흔히 「누수」로 불리는 코드다.

```text
===== 명령: go doc time.After =====
package time // import "time"

func After(d Duration) <-chan Time
    After waits for the duration to elapse and then sends the current time on
    the returned channel. It is equivalent to NewTimer(d).C.

    Before Go 1.23, this documentation warned that the underlying Timer
    would not be recovered by the garbage collector until the timer fired,
    and that if efficiency was a concern, code should use NewTimer instead and
    call Timer.Stop if the timer is no longer needed. As of Go 1.23, the garbage
    collector can recover unreferenced, unstopped timers. There is no reason to
    prefer NewTimer when After will do.
(exit 0)
```

- ★★★ 「**As of Go 1.23, the garbage collector can recover unreferenced, unstopped timers.**」 — 1.23 전에는 **발화 전까지** 타이머가 안 치워졌다(그것이 원래 경고였다).

```text
===== 소스: t31after.go =====
package main

import (
	"fmt"
	"runtime"
	"time"
)

func main() {
	ready := make(chan int, 1)
	var ms runtime.MemStats
	runtime.GC()
	runtime.ReadMemStats(&ms)
	before := ms.HeapInuse
	g0 := runtime.NumGoroutine()
	for i := range 200000 {
		ready <- i
		select {
		case <-ready:
		case <-time.After(time.Hour): // 매 회차 한 시간짜리 타이머를 만들고 버린다
		}
	}
	g1 := runtime.NumGoroutine()
	runtime.GC()
	runtime.ReadMemStats(&ms)
	grow := int64(ms.HeapInuse) - int64(before)
	fmt.Println("루프 전후 NumGoroutine         :", g0, "→", g1)
	fmt.Println("GC 뒤 HeapInuse 증분이 1MiB 미만인가:", grow < 1<<20)
}
===== 명령: go build -trimpath -o prog . && ./prog =====
루프 전후 NumGoroutine         : 1 → 1
GC 뒤 HeapInuse 증분이 1MiB 미만인가: true
(exit 0)
```

그림 해설 (한 단계씩):

- ★★★ **`루프 전후 NumGoroutine : 1 → 1`** — 한 시간짜리 타이머를 **20만 개** 만들고 버렸는데 **고루틴은 하나도 안 늘었다.** ★★ **브리핑의 전제 하나가 여기서 갈렸다** — `time.After` 는 **고루틴을 만들지 않는다.** 타이머는 런타임의 타이머 힙에 산다. 그러니 이것은 **「고루틴 누수」가 아니었다** — 1.23 전에도 **메모리** 문제였다.
- ★★ **`GC 뒤 HeapInuse 증분이 1MiB 미만인가: true`** — 버려진 20만 타이머를 **GC 가 치웠다.**

**판 격자를 돌릴 수 있나** — 1.22 의미로 되돌리는 스위치가 있었다:

```text
===== 명령: sed -n "353,357p" "$(go env GOROOT)/doc/godebug.md"; grep -n "removed the .asynctimerchan. setting" "$(go env GOROOT)/doc/godebug.md" =====
Go 1.23 changed the channels created by package time to be unbuffered
(synchronous), which makes correct use of the [`Timer.Stop`](/pkg/time/#Timer.Stop)
and [`Timer.Reset`](/pkg/time/#Timer.Reset) method results much easier.
The [`asynctimerchan` setting](/pkg/time/#NewTimer) disables this change.
There are no runtime metrics for this change.
171:Go 1.27 removed the `asynctimerchan` setting, as noted in the [Go 1.23](#go-123) section.
(exit 0)
```

```text
===== 소스: t31after.go =====
package main

import (
	"fmt"
	"runtime"
	"time"
)

func main() {
	ready := make(chan int, 1)
	var ms runtime.MemStats
	runtime.GC()
	runtime.ReadMemStats(&ms)
	before := ms.HeapInuse
	g0 := runtime.NumGoroutine()
	for i := range 200000 {
		ready <- i
		select {
		case <-ready:
		case <-time.After(time.Hour): // 매 회차 한 시간짜리 타이머를 만들고 버린다
		}
	}
	g1 := runtime.NumGoroutine()
	runtime.GC()
	runtime.ReadMemStats(&ms)
	grow := int64(ms.HeapInuse) - int64(before)
	fmt.Println("루프 전후 NumGoroutine         :", g0, "→", g1)
	fmt.Println("GC 뒤 HeapInuse 증분이 1MiB 미만인가:", grow < 1<<20)
}
===== 명령: go build -trimpath -o prog . && GODEBUG=asynctimerchan=1 ./prog =====
fatal error: removed GODEBUG "asynctimerchan" set to old value "1" in environment (https://go.dev/doc/godebug#go-127)

goroutine 1 [running, locked to thread]:
runtime.fatal({0x109f0a5e0150, 0x68})
	runtime/panic.go:1267 +0x74
runtime.main()
	runtime/proc.go:224 +0x2aa
runtime.goexit({})
	runtime/asm_amd64.s:1264 +0x1
(exit 2)
```

```text
===== 소스: go.mod =====
module ex

go 1.22
===== 소스: t31after.go =====
package main

import (
	"fmt"
	"runtime"
	"time"
)

func main() {
	ready := make(chan int, 1)
	var ms runtime.MemStats
	runtime.GC()
	runtime.ReadMemStats(&ms)
	before := ms.HeapInuse
	g0 := runtime.NumGoroutine()
	for i := range 200000 {
		ready <- i
		select {
		case <-ready:
		case <-time.After(time.Hour): // 매 회차 한 시간짜리 타이머를 만들고 버린다
		}
	}
	g1 := runtime.NumGoroutine()
	runtime.GC()
	runtime.ReadMemStats(&ms)
	grow := int64(ms.HeapInuse) - int64(before)
	fmt.Println("루프 전후 NumGoroutine         :", g0, "→", g1)
	fmt.Println("GC 뒤 HeapInuse 증분이 1MiB 미만인가:", grow < 1<<20)
}
===== 명령: echo "asynctimerchan 이 기본 GODEBUG 에 있나: $(go list -f "{{.DefaultGODEBUG}}" . | grep -q asynctimerchan && echo 예 || echo 아니오)" =====
asynctimerchan 이 기본 GODEBUG 에 있나: 아니오
(exit 0)
```

- ★★★ **`Go 1.27 removed the asynctimerchan setting`** — 그리고 켜 보면 런타임이 **`fatal error: removed GODEBUG "asynctimerchan" set to old value "1"`** 로 **시작하자마자** 거부한다(exit 2).
  ★ `go.mod` 를 **`go 1.22`** 로 내려도 **기본 GODEBUG 에 `asynctimerchan` 이 안 들어간다**(「아니오」).
- ★★★ 그래서 **「1.22 에서는 샌다」는 이 툴체인으로 못 잰다 — 제3의 상태**다. 확인한 것은 「**1.27.1 에서는 치워진다**」와 「**되돌릴 스위치가 이 판에 없다**」 둘이다.
  ★ 이 설정이 **문서상** 되돌리던 것은 「**changed the channels created by package time to be unbuffered (synchronous)**」 — **타이머 채널의 동기화 변경**이다.
  **GC 회수까지 같이 되돌렸는지는 이 판 문서에 적혀 있지 않다** — 1.23 릴리스 노트(웹)는 **안 열었다.** 그래서 「1.22 에서 샌다」를 이 문서는 **주장하지 않는다.**

비용 — 절댓값은 안 실었다(**1MiB 미만인가**만).

### (8) ★ 교착 탐지를 가리는 누수 — 29편 인용

- [29번 주제](../29-channels-buffering-direction-close-range-and-nil/) (8)절의 실측 — main 이 영원히 막혀도 **곁에 `time.Sleep` 하는 고루틴이 있으면 교착 탐지가 안 온다**(탐지 못 한 칸 **1 / 3**).
  **채널에 막혀 새어 있는 고루틴은 못 가린다.**
- ★★★ (1)절의 ③(티커 루프)이 **바로 그 「가리는」 고루틴**이다 — 그리고 **누수 프로파일에도 안 잡힌다**(0). 세 창 중 **`NumGoroutine` 만** 본다.
  ★ 그래서 ③ 이 **가장 나쁜 모양**이다 — 스스로 **안 보이면서** 남의 교착까지 **가린다.**

## 문법 — 형태와 규칙

### 형태 — 새지 않는 생산자·소비자

```go
// t31form.go
package main

import (
	"context"
	"fmt"
	"runtime"
	"sync"
	"time"
)

// producer 는 ctx 가 끝나면 멈추고, 멈출 때 자기가 닫는다.
func producer(ctx context.Context) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out)
		for i := 0; ; i++ {
			select {
			case out <- i:
			case <-ctx.Done():
				return
			}
		}
	}()
	return out
}

func main() {
	ctx, cancel := context.WithCancel(context.Background())
	src := producer(ctx)
	var wg sync.WaitGroup
	for range 3 {
		wg.Go(func() {
			for range src { // producer 가 닫으면 끝난다
			}
		})
	}
	time.Sleep(10 * time.Millisecond)
	cancel()
	wg.Wait()
	for deadline := time.Now().Add(time.Second); runtime.NumGoroutine() > 1 && time.Now().Before(deadline); {
		time.Sleep(time.Millisecond)
	}
	fmt.Println("cancel 뒤 NumGoroutine:", runtime.NumGoroutine())
}
```

```text
===== 명령: go build -trimpath -o prog . && ./prog =====
cancel 뒤 NumGoroutine: 1
(exit 0)
```

규칙 불릿.

- ★★★ **고루틴을 띄울 때 「이것은 무엇이 오면 끝나나」를 한 줄로 말할 수 있어야 한다.** 말 못 하면 샌다.
- **보내는 쪽은 `defer close(out)`** — 소비자의 `range` 가 끝난다(④).
- **기다리는 `select` 에는 `<-ctx.Done()` 가지** — 밖에서 끝낼 통로(②·③).
- **결과 하나를 버릴 수 있는 일꾼은 버퍼 1** — 단 **정확히 한 번** 보낼 때만(①).
- **티커는 `defer t.Stop()`**.
- **띄운 쪽이 끝을 기다린다** — `WaitGroup`([32번 주제](../32-sync-mutex-rwmutex-waitgroup-once/)).
- **테스트는 전후 `NumGoroutine` 또는 `synctest`** 로 누수를 실패로 바꾼다.

### 금지 사례 — 컴파일도 `vet` 도 통과하는데 새는 것

| 쓴 꼴 | 무엇이 되나 | 어디서 |
|---|---|---|
| 타임아웃 `select` + 버퍼 0 결과 채널 | ★★★ **① 일꾼이 남는다** — 11, 안 줄어듦 | (1)절 |
| 아무도 안 닫는 로컬 채널에서 `<-ch` | ★★★ **② 남는다** | 〃 |
| `for range ticker.C {}` 에 멈출 가지 없음 | ★★★ **③ 남는다 · 누수 프로파일 0** | 〃 |
| 생산자가 `close` 를 잊음 | ★★★ **④ 소비자가 남는다** | 〃 |
| 버퍼 1 인데 두 번 보냄 | ★★ **처방이 안 듣는다** — 11 | (3)절 |
| 넷 전부 | ★ **`go vet` exit 0** | (6)절 |

## 어디서 틀리나

### 1. ★★★ 「에러가 안 났으니 괜찮다」

- (1)절 실측 — 네 모양 **전부 exit 0**, 한 줄의 경고도 없다. **`NumGoroutine` 만** 안 줄어든다.
- 고치는 법 — **테스트에 전후 비교**((4)절) 또는 **`synctest`**((5)절).

### 2. ★★★ 「버퍼 1 을 주면 누수가 고쳐진다」

- (3)절 실측 — **두 번 보내면 11, `false`.** 버퍼 1 은 **정확히 한 번 · 결과를 버려도 되는** 경우만이다.
- 고치는 법 — 보내는 횟수를 모르면 **취소 신호**(`context`).

### 3. ★★★ 「누수 프로파일이 0 이니 안 샌다」

- (1)절 실측 — **③ 티커 루프는 0** 인데 **11 개가 남았다.** (2)절 — **전역 채널에 막힌 것도 `(leaked)` 가 아니다.**
- 고치는 법 — 누수 프로파일은 **「확실히 샌 것」의 목록**이지 전부가 아니다. **`NumGoroutine` 추세**와 **`goroutine` 프로파일**을 같이 본다.

### 4. ★★ 「샌 고루틴은 GC 가 언젠가 치운다」

- (2)절 — 이 판의 GC 는 **찾아서 `leaked` 로 표시만** 한다. `NumGoroutine` 은 그대로다. **치우지 않는다.**

### 5. ★★ 「`time.After` 를 루프에서 쓰면 고루틴이 샌다」

- (7)절 실측 — **`1 → 1`.** 타이머는 고루틴이 아니다. 1.23 부터는 **메모리도 GC 가 치운다**(1MiB 미만).
- ★ 다만 **1.23 전 판**에서는 메모리 문제였다 — **이 툴체인으로는 재현 못 한다**(스위치 제거).

### 6. ★★ 「테스트에서 끝나자마자 `NumGoroutine` 을 보면 된다」

- (4)절 — 시작이 **2** 이고, 끝난 고루틴이 **사라지기까지 틈**이 있다. **시작 값과, 기다리며** 비교한다. 병렬 테스트면 섞인다.

### 7. ★ 「교착이면 런타임이 알려 주니 누수도 알려 준다」

- (8)절 — **③ 모양은 교착 탐지까지 가린다.** 서버에는 늘 타이머가 있다.

## 구현 세부사항 대 언어 보장

| 사실 | 층 | 근거 |
|---|---|---|
| ★★★ **막힌 송수신은 영원히 막힌다** — 그래서 고루틴이 남는다 | **명세 보장** | [29번 주제](../29-channels-buffering-direction-close-range-and-nil/) |
| **고루틴을 밖에서 없애는 문법이 없다** | **명세**(없다는 것) | — |
| ★★★ **`NumGoroutine` 이 막힌 것도 센다** | **표준 라이브러리 계약** | 「currently exist」 · (1)절 |
| ★★★ **`goroutineleak` 프로파일 — 닿을 수 없는 채널에 막힌 것만 · 표시만 하고 안 치움** | ★ **구현(runtime·pprof) — 이 판** | (2)절 소스 · 실측 |
| ★★ **`synctest` 의 교착 판정 · 가짜 시계 · `durable` 표시** | **표준 라이브러리(1.25+)** | (5)절 |
| ★★ **1.23 부터 버려진 타이머를 GC 가 회수 · `asynctimerchan` 은 1.27 에서 제거** | **표준 라이브러리 계약 · 판 의존** | (7)절 문서·실측 |
| `context` 의 `Done()` 이 취소 시 닫힌다 | **표준 라이브러리 계약** | [목록의 **34번 주제**](../34-context-cancellation-deadlines-and-values/) |
| 샌 고루틴 하나의 **메모리** | **구현 — 안 실었다** | [28번 주제](../28-goroutines-go-statement-cost-and-termination/) (5)절 |
| 고루틴 id | **구현 — 흔들린다** | 정규화 칸 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 결과 **하나**를 기다리다 떠날 수 있다 | **버퍼 1** | (3)절 — 정확히 한 번일 때만 |
| 결과가 **여럿**·스트림 | **`context` 취소** | (3)절 `buf1Twice` |
| 주기 작업(티커) | **`context` + `defer t.Stop()`** | (3)절 — ③ 은 프로파일에도 안 보인다 |
| 생산자 → 소비자 | **생산자가 `defer close`** | (3)절 `closeRange` |
| 누수가 **다시 생기지 않게** | **테스트 전후 `NumGoroutine`** · 시간이 얽히면 **`synctest`** | (4)·(5)절 |
| 운영 중 **어느 줄**인지 | **`goroutineleak` 프로파일** + `goroutine` 프로파일 | (2)절 |
| 외부 도구 `goleak` | **이 환경에는 없다** — 표준 두 창으로 | (4)절 |

## 핵심 문장

- ★★★ **누수 네 모양 — ① 받는 쪽이 사라진 송신 · ② 보내는 쪽 없는 수신 · ③ 취소 없는 대기 · ④ 끝나지 않는 `range`** — 넷 다 **`1 → 11`, 1초 뒤에도 안 줄었다.** 에러는 **한 줄도 없다.**
- ★★★ **누수 프로파일은 `10 · 10 · 0 · 10`** — 닿을 수 없는 채널에 막힌 것만 **`(leaked)`** 로 짚고, **③ 티커 루프와 전역 채널에 막힌 것은 못 본다.** 그리고 **표시만 하고 치우지 않는다.**
- ★★★ **버퍼 1 은 「정확히 한 번 보내고 결과를 버려도 될 때」만** 맞다 — 두 번 보내면 11 그대로. 모르면 **`context`**.
- ★★★ **테스트로 잡는다** — 전후 `NumGoroutine`(시작 **2**, 기다리며 비교)이 `FAIL: 시작 2 → 끝 4` 를 냈고, **`synctest` 는 「blocked goroutines remain」을 결정적으로** 낸다. 가짜 시계는 한 시간을 **`(0.00s)`** 에 건넌다.
- ★★ **`time.After` 는 고루틴을 안 만든다**(`1 → 1`) — 루프 안의 `time.After` 는 고루틴 누수가 **아니었고**, 1.23 부터는 메모리도 GC 가 치운다. **1.22 판 격자는 스위치가 제거돼 못 돌린다.**
- ★★ **③ 이 가장 나쁘다** — `NumGoroutine` 에만 보이고, 누수 프로파일은 0 이고, **교착 탐지까지 가린다**([29번 주제](../29-channels-buffering-direction-close-range-and-nil/) (8)절).

## 관련 자료

- [`../README.md`](../README.md) — Go 문법·API 주제 목록(이 주제는 31번)
- [`../../../../../ops-patterns/failure-modes/`](../../../../../ops-patterns/failure-modes/) — ★★ **정본 경계.** **그쪽은 실패 모드의 분류와 읽는 순서까지**, 여기는 **고루틴이 막힌 채 남는 네 모양과 그것을 잡는 법부터.**
- [30번 주제](../30-select-default-and-timeouts/)(`select`) — ★ 목록상 선행 · 타임아웃 뒤 `NumGoroutine: 2`
- [29번 주제](../29-channels-buffering-direction-close-range-and-nil/)(채널) — 차단 규칙 · **교착 탐지를 가리는 것**
- [28번 주제](../28-goroutines-go-statement-cost-and-termination/)(고루틴) — `NumGoroutine`·`settle` · 스택 크기는 구현
- [26번 주제](../26-defer-evaluation-lifo-named-results-and-loops/)(`defer`) — 자원이 「늘었나」를 세는 같은 질문(fd)
- [27번 주제](../27-panic-recover-and-where-to-use-them/)(`panic`) — `[recovered, repanicked]` 표시 · 고루틴 id 정규화
- [32번 주제](../32-sync-mutex-rwmutex-waitgroup-once/)(`sync`) — 띄운 쪽이 기다리기(`WaitGroup`)
- [목록의 **34번 주제**](../34-context-cancellation-deadlines-and-values/)(`context`) — ★ 취소의 정본 · **35번 주제**(레이스) · **49번 주제**(테스트 쪽)

## 용어 풀이

- **고루틴 누수** — 끝날 길 없이 막힌 채 남는 고루틴.
- **`NumGoroutine`** — 지금 있는 고루틴 수. 막혀 있어도 센다.
- **`goroutineleak` 프로파일** — 이 판 `runtime/pprof` 의 기본 프로파일. GC 가 **닿을 수 없는 동기화 수단에 막힌** 고루틴을 찾아 스택을 준다.
- **`(leaked)`** — 그 판정을 받은 고루틴의 상태 표시(`[chan send (leaked)]`).
- **`testing/synctest`** — 격리된 버블 + 가짜 시계로 고루틴 코드를 결정적으로 테스트하는 패키지(1.25).
- **버블(bubble)** — `synctest.Test` 가 만드는 격리 칸. 안의 고루틴·타이머·채널만 본다.
- **`durable` 막힘** — 버블 밖에서는 깨울 수 없는 막힘. 버블이 멈췄다고 판정하는 근거.
- **`asynctimerchan`** — 1.23 의 타이머 변경을 되돌리던 GODEBUG 설정. 1.27 에서 제거됐다.

---

## 더 들어가면

- ★ **`goroutineleak` 프로파일을 HTTP(`net/http/pprof`)로 받는 것**은 **안 던졌다.**
- ★ **`synctest` 버블에 ③ 티커 루프를 넣으면** 어떻게 되나는 **안 던졌다.**
- ★ **병렬 테스트(`t.Parallel`)에서 전후 비교가 틀리는 것**은 **안 던졌다.**
- ★★ 샌 고루틴의 **메모리·시간 비용**은 **안 쟀다.**
- ★ **`goroutineleak` 프로파일이 몇 판부터 기본인지**는 이 툴체인 하나로 **확인 못 했다** — 이름 문자열이라 `api/` 파일에 안 남는다.

# go/syntax/48 — `time`: `Time`·`Duration`·단조 시계·`Timer`/`Ticker`(1.23 변경) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다(1번은 `go1.25.12` 판을 나란히). 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★ **근거로 읽을 칸** — 판 격자의 값 · `7 / 7` · `0 / 7` · `m=` 유무 · `==`/`Equal` · `Duration` 문자열 · 파싱 결과 · 에러 문구.
> **칸으로 안 만든 것** — 시각 · 경과 시간(참/거짓만).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 판 1 — `1 · 1 · false · true · true · false · false` · 판 2 — `0 · 0 · true · false · false · true · true` · 판 3·4 는 **판 2 와 같다** — `7 / 7` · `0 / 7`

**출력**

```text
===== 명령: set -- "$GO125 1.22" "$GO125 1.23" "go 1.22" "go 1.27"; i=0; for c in "$@"; do i=$((i+1)); tc=${c% *}; v=${c#* }; printf "module ex\n\ngo %s\n" $v > go.mod; "$tc" build -trimpath -o p$i . || exit 1; ./p$i > r$i.txt || exit 1; echo "[판 $i] $("$tc" version | cut -d" " -f3) · go.mod 의 go $v"; done; paste r1.txt r2.txt r3.txt r4.txt | awk -F"\t" "NF!=8 || \$1!=\$3 || \$1!=\$5 || \$1!=\$7 {bad=1} {printf \"%s\t%s\t%s\t%s\t%s\n\", \$1, \$2, \$4, \$6, \$8; m++; if (\$2!=\$4) n++; if (\$6!=\$8) k++} END {if (bad) print \"칸 수 어긋남\"; printf \"판 1·2(go1.25.12 · go 1.22 대 1.23 줄)가 갈린 칸 %d / %d\n판 3·4(go1.27.1 · go 1.22 대 1.27 줄)가 갈린 칸 %d / %d\n\", n, m, k, m}" =====
[판 1] go1.25.12 · go.mod 의 go 1.22
[판 2] go1.25.12 · go.mod 의 go 1.23
[판 3] go1.27.1 · go.mod 의 go 1.22
[판 4] go1.27.1 · go.mod 의 go 1.27
cap(t.C)	1	0	0	0
발화 뒤 받기 전 len(t.C)	1	0	0	0
발화 뒤 받기 전 Stop()	false	true	true	true
Stop 뒤 t.C 에서 값이 나오나	true	false	false	false
Reset(1h) 직후 t.C 에서 값이 나오나	true	false	false	false
참조를 버린 Ticker 가 GC 뒤 사라졌나	false	true	true	true
time.After(1h) 20만 번 뒤 GC 한 HeapInuse 증분 < 1MiB	false	true	true	true
판 1·2(go1.25.12 · go 1.22 대 1.23 줄)가 갈린 칸 7 / 7
판 3·4(go1.27.1 · go 1.22 대 1.27 줄)가 갈린 칸 0 / 7
(exit 0)
```

**왜 그런가**

- ★★★ 문서 — 1.23 전 채널은 「asynchronous (buffered, **capacity 1**)」라 「stale time values could be received even after Timer.Stop or Timer.Reset returned」. 1.23 부터 「synchronous (unbuffered, **capacity 0**)」이고 「the garbage collector can recover unreferenced timers, even if they haven't expired or been stopped」.
- ★★★ 판 3·4 가 같은 것은 **`asynctimerchan` 이 1.27 에서 제거**됐기 때문이다(`t48gdoc`).

### 2. `go` 줄이 **GODEBUG 기본값**을 정한다 — `go 1.22` 줄이면 그 판의 옛 기본값 `asynctimerchan=1` 이 켜진다 · 41번의 `go` 줄이 **언어 판**을 정하듯 **라이브러리 동작의 판**도 정한다

- ★★★ 이 판의 `godebug.md` — 「Go 1.23 changed the channels created by package time … The `asynctimerchan` setting … disables this change」. 모듈의 `go` 줄이 그 판보다 낮으면 **옛 값이 기본**이 된다(46번의 `httpmuxgo121` 과 같은 구조).
- ★★ 그래서 **툴체인을 올려도 `go` 줄이 낮으면 옛 의미**였다 — 1.26 툴체인까지는(1.27 이 스위치를 없앴다).

### 3. ① `fatal error: removed GODEBUG "asynctimerchan" set to old value "1" …` · `exit=2` · ② `cap(NewTimer(1h).C) = 0` · ③ `go.mod:5: removed GODEBUG …` · build `exit=1` · ④ `invalid //go:debug: removed GODEBUG …` · build `exit=1`

**출력**

```text
===== 소스: t48rej.go =====
package main

import (
	"fmt"
	"time"
)

func main() {
	fmt.Println("cap(NewTimer(1h).C) =", cap(time.NewTimer(time.Hour).C))
}
===== 명령: printf "module ex\n\ngo 1.22\n" > go.mod; go build -trimpath -o prog . || exit 1; echo "[GODEBUG 환경 변수] $(GODEBUG=asynctimerchan=1 ./prog 2>&1 | sed -n 1p) · exit=$(GODEBUG=asynctimerchan=1 ./prog >/dev/null 2>&1; echo $?)"; ./prog; printf "module ex\n\ngo 1.22\n\ngodebug asynctimerchan=1\n" > go.mod; go build -trimpath -o /dev/null . 2>err.txt; echo "[go.mod 의 godebug 줄] build exit=$?"; sed "s/^/  (stderr) /" err.txt; printf "module ex\n\ngo 1.22\n" > go.mod; sed -i "1i //go:debug asynctimerchan=1" t48rej.go; go build -trimpath -o /dev/null . 2>err.txt; echo "[//go:debug 줄] build exit=$?"; sed "s/^/  (stderr) /" err.txt =====
[GODEBUG 환경 변수] fatal error: removed GODEBUG "asynctimerchan" set to old value "1" in environment (https://go.dev/doc/godebug#go-127) · exit=2
cap(NewTimer(1h).C) = 0
[go.mod 의 godebug 줄] build exit=1
  (stderr) go: error loading go.mod:
  (stderr) go.mod:5: removed GODEBUG "asynctimerchan" set to old value "1" (https://go.dev/doc/godebug#go-127)
[//go:debug 줄] build exit=1
  (stderr) # ex
  (stderr) ./t48rej.go:1:1: invalid //go:debug: removed GODEBUG "asynctimerchan" set to old value "1" (https://go.dev/doc/godebug#go-127)
(exit 0)
```

- ★★★ 환경 변수는 **실행 시** 런타임이, 나머지 둘은 **빌드 시** `go` 명령이 거부한다. 셋 다 `https://go.dev/doc/godebug#go-127` 을 가리킨다.
- ★★ ② — `go 1.22` 줄인데도 용량 0. **1.27 툴체인에서는 옛 의미를 부를 길이 없다.**

### 4. **1.22 의미에서는 버린 타이머가 안 치워졌다**(`HeapInuse 증분 < 1MiB` 가 `false`) — 그리고 `asynctimerchan` 하나가 **채널과 수거를 같이** 갈랐다 · 확인 못 한 판 — **1.26 툴체인**과 **1.22 이하 툴체인**

- ★★★ 31번은 「이 툴체인(1.27.1)으로는 되돌릴 스위치가 없다」에서 멈췄다. 이 문서는 **스위치가 살아 있던 `go1.25.12`** 로 판 1 을 만들어 그 칸을 쟀다. 문서(`godebug.md`)는 이 설정이 **채널**을 되돌린다고만 적는다 — **수거까지 되돌린 것은 `go1.25.12` 의 관찰**이다.
- ★★ 1.26 은 「This setting will be removed in Go 1.27」로 **추론**했을 뿐 돌리지 않았다.

### 5. `[1]`·`[4]` 만 `m=` 가 있다 · `==` 세 줄은 `false`, `Equal` 은 `true` · `t.Round(0) == u` 는 `true` · 경과 시간 두 줄 `true`

**출력**

```text
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && ./prog =====
vet exit=0
[1] time.Now()           String 에 m= 가 있나: true
[2] t.Round(0)           String 에 m= 가 있나: false
[3] t.UTC()              String 에 m= 가 있나: false
[4] t.Add(time.Second)   String 에 m= 가 있나: true
[5] t.AddDate(0, 0, 1)   String 에 m= 가 있나: false
[6] MarshalText → UnmarshalText 한 u 에 m= 가 있나: false
── 같은 순간을 == 와 Equal 로 ──
    t == t.Round(0)   : false · t.Equal(t.Round(0)): true
    t == u            : false · t.Equal(u)         : true
    t == t.UTC()      : false · t.Equal(t.UTC())   : true
    t.Round(0) == u   : true
── 경과 시간 ──
    time.Since(s) >= 20ms : true
    c.Sub(a) >= 0         : true
(exit 0)
```

- ★★★ 문서 — `Add` 는 단조 값을 **같이 옮기고**, `AddDate`·`Round`·`Truncate`·`In`·`Local`·`UTC` 는 **벗기고**, 직렬화·언마샬은 **안 싣는다.**

### 6. `==` 는 **구조체 필드를 다** 견준다 — `Time` 의 필드에는 **Location 과 단조 값**이 들어 있다 · `Equal` 은 **순간만** 본다 · 맵 키로 쓰면 **같은 순간이 다른 키**가 된다

- ★★★ 17번 — 비교 가능한 구조체의 `==` 는 필드별 비교다. 문서 「the Go == operator compares not just the time instant but also the Location and the monotonic clock reading」.
- ★★ 맵 키·`==` 가 필요하면 **`Round(0)` 과 `UTC()` 로 정규화**한 값을 쓴다 — 5번의 `t.Round(0) == u` 가 `true` 였던 이유와 같다(둘 다 단조 값이 없고 Location 이 같다).

### 7. **못 보였다**(시스템 시계를 바꾸지 않았다 — 못 잰 것) · 대신 **문서의 약속** + **벗기는 연산 여섯의 `m=` 유무** + **`Since`·`Sub` 가 음수가 아닌 것**을 쟀다 · 올바른 꼴 `start := time.Now()` … `time.Since(start)` · 보호가 사라지는 꼴 — **`Round(0)` 한 시작점**, **직렬화·파싱으로 만든 시작점**

- ★★★ 문서 「this code always computes a positive elapsed time … even if the wall clock is changed」, 그리고 「If either t or u contains no monotonic clock reading, these operations **fall back to using the wall clock readings**」.
- ★★ 그래서 경과 시간의 시작점은 **같은 프로세스의 `time.Now()`** 여야 한다 — JSON 으로 받은 시각이나 DB 에서 읽은 시각에서 `Since` 를 재면 **벽시계 차이**다.

### 8. `0s` · `1ns` · `1.5ms` · `1m30s` · `36h0m0s` · `-2m0s` · `MaxInt64` 는 `2562047h47m16.854775807s`(`292 년`) · `+1` 은 **음수** · 300년은 **음수** · `1.5` · `1h0m0s` · `1h0m0s` · `ParseDuration("1d")` 는 `unknown unit "d"`

**출력**

```text
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && ./prog =====
vet exit=0
0                → 0s
1                → 1ns
1500000          → 1.5ms
90000000000      → 1m30s
129600000000000  → 36h0m0s
-120000000000    → -2m0s
Duration(MaxInt64)        → 2562047h47m16.854775807s · Hours() = 2.5620477880152157e+06
그것을 365일짜리 해로      → 292 년
Duration(MaxInt64) + 1    → -2562047h47m16.854775808s
300년을 Duration 으로       → -2496095h34m33.709551616s
(1500ms).Seconds()        → 1.5
(1h29m).Round(time.Hour)  → 1h0m0s
(1h29m).Truncate(time.Hour)→ 1h0m0s
ParseDuration("1d")       → 0s time: unknown unit "d" in duration "1d"
(exit 0)
```

- ★★★ `Duration` 은 `int64` 나노초 — 넘치면 **감싸 돈다**(04번). 에러도 패닉도 없다.
- ★★ `String()` 에 **일 단위가 없다** — `36h0m0s`. `ParseDuration` 도 `d` 를 모른다.

### 9. `"2006-01-02"` 만 3월 4일 · **`"2006-02-01"` 은 에러 없이 4월 3일** · 나머지 셋은 에러 · `03:04` 에 `15:30` 은 `hour out of range` · `DateTime` 은 `UTC`

**출력**

```text
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && ./prog =====
vet exit=0
"2006-01-02"       → 2026-03-04 · 3월 4일인가=true
"2006-02-01"       → 2026-04-03 · 3월 4일인가=false
"YYYY-MM-DD"       → err=parsing time "2026-03-04" as "YYYY-MM-DD": cannot parse "2026-03-04" as "YYYY-MM-DD"
"2026-03-04"       → err=parsing time "2026-03-04" as "2026-03-04": cannot parse "-03-04" as "6-"
"2006-01-02 15:04" → err=parsing time "2026-03-04" as "2006-01-02 15:04": cannot parse "" as "15"
"2006-01-02 03:04" ← "2026-03-04 15:30" → 0001-01-01 00:00:00 +0000 UTC · err=parsing time "2026-03-04 15:30": hour out of range
DateTime 레이아웃  → Location=UTC
(exit 0)
```

- ★★★ 레이아웃은 **기준 시각의 각 부분**(`2006`=해 · `01`=월 · `02`=일 · `15`=24시 · `03`=12시)을 원하는 자리에 쓴 것이다. 자리를 바꾸면 **읽는 뜻이 바뀌고** 값이 맞아떨어지면 에러가 없다.

### 10. `t0` `12:00 EST` · `Add(24h)` **`13:00 EDT`** · `AddDate(0,0,1)` **`12:00 EDT`** · 차이 `23h0m0s` · 같은 순간 `true` — 파이썬의 `+ timedelta(hours=24)` 는 **`AddDate` 쪽**(벽시계)

**출력**

```text
===== 명령: go vet . ; echo "vet exit=$?"; go build -trimpath -o prog . && ./prog =====
vet exit=0
t0                 : 2026-03-07 12:00:00 -0500 EST
t0.Add(24h)        : 2026-03-08 13:00:00 -0400 EDT
t0.AddDate(0,0,1)  : 2026-03-08 12:00:00 -0400 EDT
AddDate 결과 - t0   : 23h0m0s
같은 순간 두 표기    : 2026-03-07 17:00:00 +0000 UTC · true
(exit 0)
```

- ★★★ `Add` 는 **경과**를, `AddDate` 는 **달력**을 옮긴다. 서머타임이 시작된 날이라 달력의 하루가 **23시간**이다.
- ★★ [Python 49번](../../../python/syntax/49-datetime-and-zoneinfo/) — 「같은 `tzinfo` 끼리의 산술·비교는 **벽시계 숫자로** 한다 — 뉴욕 `+ 24h` 가 실제 23·25시간」. 실제 경과를 재려면 **UTC 로 바꿔** 쟀다. Go 는 `Add`·`Sub` 가 처음부터 경과다.

### 11. 판 1 에서는 `Stop()` 이 `false` 여도 **채널에 옛 값이 남아** 있어서, 비우지 않으면 다음 `Reset` 뒤 **그 옛 값을 받았다**(1번의 「Stop 뒤」·「Reset(1h) 직후」 두 줄) · 판 3·4 에서는 발화했어도 **안 받았으면 `Stop()` 이 `true`** 라 그 줄이 **안 돈다** — 걱정은 **이미 받은 뒤** `Stop()` 이 `false` 일 때 `<-t.C` 가 **영영 막히는 것**이다 · ★ **돌려 보지 않았다**

- ★★★ `go doc time.Timer.Stop` — 「Before Go 1.23, the only safe way to use Stop was insert an extra <-t.C if Stop returned false to drain a potential stale value」.
- ★★ 막힘은 **문서와 용량 0 이라는 사실에서 추론**한 것이다 — 이 문서의 블록에는 없다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 로 **★고칠 것 0** |
| ★★★ 타이머 판 격자 (`t48timer`) | 탐침 7 × 판 4(툴체인 2 × `go` 줄 2) · `paste` 후 탭 8칸 검사 | 캡처마다 | **`7 / 7` · `0 / 7`** |
| ★★ 스위치 거부 (`t48rej`) | 환경 변수 · `go.mod` `godebug` · `//go:debug` | 캡처마다 | 셋 다 거부 |
| ★★ 단조 시계 (`t48mono`) | `m=` 유무 · `==`/`Equal` · 경과 참/거짓 | 캡처마다 | 벗기는 연산 넷 · 직렬화 하나 |
| ★★ `Duration`·`Parse`·시간대 | 문자열·에러·`EST`/`EDT` | 캡처마다 | 감싸 돔 · 4월 3일 · 23h |

**구현·환경에 달린 항목**

| 항목 | 무엇에 달렸나 |
|---|---|
| 단조 시계 규칙 · 1.23 타이머 · 레이아웃 | **표준 라이브러리 문서의 계약** |
| `go` 줄이 타이머 의미를 가름 | **툴체인 1.23\~1.26 의 GODEBUG 규칙**(실측은 `go1.25.12`) |
| `asynctimerchan` 제거 | **1.27 툴체인** |
| 수거까지 되돌림 | **`go1.25.12` 의 관찰** |
| `EST`/`EDT` | **이 머신의 tzdata** |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다(기본 규칙만). `GO125` 가 가리키는 `go1.25.12` 툴체인이 있어야 1번이 돈다. 시스템 시계는 건드리지 않는다.

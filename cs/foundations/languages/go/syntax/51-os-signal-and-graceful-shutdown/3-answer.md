# go/syntax/51 — `os/signal`과 정상 종료 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`go version go1.27.1 linux/amd64`** 에서 실제로 돌려
> **파일로 캡처한 것**이다. 소스 펜스도 같은 파일에서 떠 왔다 — 손으로 옮겨 적은 블록은 없다.\
> ★ **근거로 읽을 칸** — 여덟 칸의 결과 · 서버 로그 순서 · `2 / 8` · 셸의 `143`·`0`·`137` · 문서 문장.
> **관찰에 그치는 칸** — 클라이언트의 `EOF`(대 `connection reset`).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `A` `200 done`·`exit 0` · `B` `EOF`·`exit 1` · `C` `EOF`·`exit 0` · `D` `EOF`·신호로 죽음 · `E` `EOF`·`exit 0` · `F` `EOF`·신호로 죽음 · `G` `200 done`·`exit 0` · `H` `EOF`·신호로 죽음(killed) — **`2 / 8`**

**출력**

```text
===== 명령: go vet ./... ; echo "vet exit=$?"; go build -trimpath -o server ./srv && go build -trimpath -o drv ./drive || exit 1; ./drv > rows.txt; echo "drive exit=$?"; awk -F"\t" "NF!=6 {bad=1} {print} NR>1 {m++; if (\$3 ~ /^200/) n++} END {if (bad) print \"칸 수 어긋남\"; printf \"진행 중 요청이 끝까지 간 칸 %d / %d\n\", n, m}" rows.txt =====
vet exit=0
drive exit=0
칸	서버 인자	느린 요청이 받은 것	종료 중 새 요청	서버 종료	서버 로그
A	-mode shutdown -grace 5s	200 done	connection refused	exit 0	handler: start → signal received: terminated signal received → shutdown: start → handler: end → shutdown: returned <nil> → Serve returned: http: Server closed · ErrServerClosed? true
B	-mode shutdown -grace 100ms	EOF	connection refused	exit 1	handler: start → signal received: terminated signal received → shutdown: start → shutdown: returned context deadline exceeded
C	-mode close	EOF	-	exit 0	handler: start → signal received: terminated signal received → Close: <nil> → Serve returned: http: Server closed · ErrServerClosed? true
D	-mode none	EOF	-	신호로 죽음(terminated)	handler: start
E	-mode shutdown-goroutine	EOF	-	exit 0	handler: start → signal received: terminated signal received → Serve returned: http: Server closed
F	-mode shutdown-stop	EOF	-	신호로 죽음(terminated)	handler: start → signal received: terminated signal received → shutdown: start
G	-mode shutdown	200 done	-	exit 0	handler: start → signal received: terminated signal received → shutdown: start → handler: end → shutdown: returned <nil> → Serve returned: http: Server closed · ErrServerClosed? true
H	-mode shutdown	EOF	-	신호로 죽음(killed)	handler: start
진행 중 요청이 끝까지 간 칸 2 / 8
(exit 0)
```

**왜 그런가**

- ★★★ `200` 인 칸은 **`main` 이 `Shutdown` 의 반환을 기다렸고 기한이 충분했던** `A`·`G` 뿐이다. 두 칸에만 로그에 `handler: end` 가 있다 — **클라이언트 창과 서버 창이 일치**한다.
- ★★ `D`·`H` 는 로그가 `handler: start` 하나 — **아무 정리 없이** 사라졌다.

### 2. `E` 는 `Serve` 를 `main` 에서 불러서, `Shutdown` 이 불리는 **즉시** `Serve` 가 `ErrServerClosed` 로 돌아오고 `main` 이 `return` 해 **프로세스가 끝났다** · `exit 0` 은 **요청이 끊긴 것**을 숨긴다

- ★★★ 문서 — 「When Shutdown is called, Serve … **immediately** return ErrServerClosed. **Make sure the program doesn't exit and waits instead for Shutdown to return**.」(`t51doc`)
- ★★★ 명세 — `main` 이 반환하면 프로그램은 **다른 고루틴을 기다리지 않는다.** 고루틴의 `Shutdown` 도 핸들러도 같이 끝났다.
- ★★ 로그 — `E` 는 `signal received → Serve returned: http: Server closed` 로 끝난다. `A` 는 그 사이에 `shutdown: start → handler: end → shutdown: returned <nil>` 이 있다.

### 3. `connection refused` — `Shutdown` 이 「**first closing all open listeners**」 하기 때문이다

- ★★ `A`·`B` 둘 다 새 요청 칸이 `connection refused`(1번). 리스너가 닫혀 **TCP 연결 자체가 거절**됐다 — HTTP 응답(503 등)이 아니다.

### 4. `context deadline exceeded` · 핸들러를 끊은 것은 **`Shutdown` 이 아니라 그 뒤의 `os.Exit(1)`**(프로세스 종료)다

- ★★★ 문서 — 「If the provided context expires before the shutdown is complete, Shutdown **returns** the context's error」. 돌아올 뿐이다.
- ★★ `B` 로그 — `shutdown: returned context deadline exceeded` 뒤 `handler: end` 가 **없다** — 서버가 에러에 `os.Exit(1)` 했고 핸들러는 그때 같이 죽었다.

### 5. `F` — 두 번째 신호에 **신호로 죽음(terminated)** · `G` — **`200 done`·`exit 0`**(두 번째 신호는 삼켜진다) · 문서 「The stop function unregisters the signal behavior, which, like signal.Reset, may restore the default behavior」

- ★★ `G` 에서는 `NotifyContext` 가 아직 등록돼 있어 두 번째 `SIGTERM` 도 **이미 취소된 `ctx`** 로 간다.
- ★ 「Future interrupts received will not trigger the default (exit) behavior until the returned stop function is called」(`t51doc`).

### 6. `143` · `0` · `137` — **셸**이 만든 숫자다(신호로 죽은 자식을 `128 + 신호 번호` 로 보고) · `0` 은 Go 프로그램이 **정상 반환**한 것

**출력**

```text
===== 명령: go build -trimpath -o server ./srv || exit 1; for c in "none TERM" "shutdown TERM" "shutdown KILL"; do set -- $c; coproc S { exec ./server -mode $1; }; read -r line <&"${S[0]}"; kill -$2 $S_PID; wait $S_PID; echo "-mode $1 에 SIG$2 → 셸이 본 종료 상태 $?"; done 2>/dev/null =====
-mode none 에 SIGTERM → 셸이 본 종료 상태 143
-mode shutdown 에 SIGTERM → 셸이 본 종료 상태 0
-mode shutdown 에 SIGKILL → 셸이 본 종료 상태 137
(exit 0)
```

- ★★ `SIGTERM` 15 → 143, `SIGKILL` 9 → 137. 1번 구동기는 같은 사실을 `WaitStatus.Signaled()` 로 읽어 「신호로 죽음」으로 적었다 — 종료 **코드**가 아니라 종료 **상태**다.

### 7. **안 바뀐다** — `SIGKILL` 은 못 잡는다(「may not be caught by a program」) · 쿠버네티스는 `SIGTERM` 뒤 유예 시간이 지나면 `SIGKILL` 을 보내므로 **`Shutdown` 의 기한을 그 유예 시간보다 짧게** 잡아야 정리가 돈다

- ★★ 1번 `H` — 로그 `handler: start` 하나, 신호로 죽음(killed).
- ★ 이 문서는 `NotifyContext` 에 `SIGKILL` 을 **넣은 판을 돌리지 않았다** — 문서와 `H` 칸으로 답한다.

### 8. 신호가 오면 `Shutdown` 이 불리고 `ListenAndServe` 가 **`ErrServerClosed`** 를 돌려준다 → `log.Fatal` 이 **`os.Exit(1)`** 로 프로세스를 끝낸다 — `main` 이 기다리던 `Shutdown` 도 끊긴다 · 근거 — `A`·`C`·`G` 의 로그 `Serve returned: http: Server closed · ErrServerClosed? true`

- ★★★ `ErrServerClosed` 는 **정상 종료에서도 늘 온다.** `errors.Is(err, http.ErrServerClosed)` 면 실패로 다루지 않는다.
- ★ 이 문서는 `log.Fatal` 판을 **돌리지 않았다** — `E` 칸(`Serve` 반환 → 종료)과 같은 모양이라 같은 결과가 나올 것으로 **추론**한다.

### 9. RUNNING = `addr …` 부터 `handler: start` 까지 · DRAINING = `shutdown: start` → (새 요청 `connection refused`) → `handler: end` · STOPPED = `shutdown: returned <nil>` · 「기한 초과면 보고」 = `B` 의 `shutdown: returned context deadline exceeded` + `exit 1`

- ★★ ops-patterns 19 의 「막는 것이 먼저」가 `Shutdown` 의 「first closing all open listeners」다.
- ★ 그쪽의 「몇 개를 버렸나 센다」는 Go `Shutdown` 이 **해 주지 않는다** — 에러만 준다. 세는 것은 서버 코드의 몫이다(46·47번의 `ConnState` 같은 훅으로).

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh <디렉토리>` 가 소스 배너 + 명령 배너 + 출력 + `(exit N)` 을 파일로 받고 `assemble-blocks.py` 가 원고에 꽂는다 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 로 **★고칠 것 0** |
| ★★★ 종료 경로 격자 (`t51grid`) | 자식 프로세스 8번 · 로그 줄 동기 · 탭 6칸 검사 | 캡처마다 + 예행 3판 md5 동일 | **`2 / 8`** |
| ★★ 셸 종료 상태 (`t51shell`) | `coproc` + `kill` + `wait` | 캡처마다 | `143` · `0` · `137` |

**구현·환경에 달린 항목**

| 항목 | 무엇에 달렸나 |
|---|---|
| `Shutdown`·`Close`·`ErrServerClosed` · `NotifyContext`·`stop` | **표준 라이브러리 계약** |
| `main` 반환 = 종료 | **명세** |
| `SIGKILL` 못 잡음 | **커널** |
| `143`·`137` | **셸(bash)** |
| 클라이언트의 `EOF` | **이 머신의 관찰** |

★ **다시 찍는 법** — `capture.sh <디렉토리>` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다(기본 규칙만). 한 판에 5초쯤 걸린다(느린 핸들러 2초 × 칸).

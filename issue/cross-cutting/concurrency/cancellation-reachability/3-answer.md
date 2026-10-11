# issue/concurrency/cancellation-reachability — 정답

태그: `resource-bounding`

## 정답
<!-- 질문 1:1 대응 -->

1. **누수된다.** Shutdown은 메인 루프의 `select!`에서만 관찰되므로, 워커가 아직 핸드셰이크의 bare `await`에 있으면 신호가 닿지 않는다.\
   상대(어댑터 프로세스)가 응답하지 않으면 그 await는 영원히 끝나지 않고, 소유자가 drop되며 보낸 Shutdown도 처리되지 않아 스레드와 자식 프로세스가 회수되지 않는다.\
   취소는 "받는 곳이 있다"가 아니라 "**모든 대기 지점에서** 받을 수 있다"여야 성립한다.
   > **취소 도달성** — 취소 신호가 작업의 현재 대기 지점까지 실제로 전달될 수 있는가. 대기 지점 하나만 막혀도 0이 된다.

2. **협력적 취소.** 작업이 스스로 취소 신호를 확인하고 정리한 뒤 끝나는 방식이다.\
   Rust 표준 스레드처럼 외부 강제 종료 API도, 시간 제한 join도 없는 런타임에서는(다른 런타임은 시간 제한 join·`pthread_cancel` 등을 제공하기도 하지만, 강제 종료는 락·자원을 쥔 채 끊겨 대개 안전하지 않다), 스레드가 끝나는 유일한 길은 스레드 코드가 멈춘 대기 지점에서 빠져나오는 것이다.\
   따라서 책임은 작업 쪽에 있다 — 모든 대기 지점을 취소 가능하게 설계해야 한다.

3. **await별 감싸기 vs future 전체 drop.** Rust async에서 future를 drop하면 그 안의 진행 중 await가 모두 함께 취소된다(단, 내부에서 `spawn`해 독립 태스크로 떼어 낸 작업과 `spawn_blocking` 작업은 drop으로 멈추지 않는다).\
   그래서 `select!{ run(...), cancel.changed() }`로 작업 전체를 취소와 경주시키면 connect·인증·채널 read/write 등을 각각 감쌀 필요가 없다.\
   단, await가 아닌 동기 구간(동기 파일 I/O, 키 로드 같은 블로킹 호출)은 실행기가 선점할 수 없어 그 구간이 끝날 때까지는 취소되지 않는다.\
   또 drop은 임의의 await 지점에서 작업을 끊으므로, 부분 쓰기 같은 중간 상태가 남지 않는지(취소 안전성)는 별도로 따져야 한다.
   > **future drop 취소** — Rust처럼 future가 폴링돼야만 진행하는(lazy) 모델에서는, 소유자가 future를 버리면 그 지점에서 작업이 중단된다. JS Promise처럼 생성 즉시 실행되는 모델에서는 참조를 버려도 작업이 멈추지 않는다.

4. **전 세션이 멈춘다.** 락을 쥔 채 join하면, join 대상 스레드가 네트워크 write·close에서 멈춰 있는 동안 락이 풀리지 않는다.\
   같은 맵을 쓰는 다른 세션의 모든 조작이 그 락에서 대기하므로 한 세션의 정지가 전체로 번진다.\
   순서: 락 안에서는 맵에서 **꺼내기만** 하고, 락을 푼 뒤 cancel → join 한다(테스트: 연결 거부 후 `remove()`가 2초 안에 반환).

5. **입력이 올 때까지 끝나지 않는다.** 블로킹 read는 그 fd에 데이터·EOF가 와야 반환하고, 다른 소켓을 닫는 것은 이 스레드를 깨우지 않는다.\
   scoped thread는 scope 끝에서 모든 자식을 join하므로, stdin에 입력이 안 오면 세션이 끝나도 CLI가 반환하지 않았다(원격 터미널이 닫히지 않고 남음).\
   해결은 "기다리지 않기"였다 — 입력 릴레이 스레드를 join하지 않고, 상대 hang-up(POLLHUP)을 감지해 반환한다(수정 후 종료 뒤 수 ms 안에 반환).
   > **POLLHUP** — poll이 보고하는 hang-up 이벤트(파이프는 반대쪽이 모두 닫힘, 소켓은 보통 양방향이 모두 종료됨). 상대가 쓰기 방향만 닫은 half-close는 Linux에서 `POLLRDHUP`으로 따로 본다.

6. **즉시 EOF 입력은 read를 바로 끝낸다.** 테스트 입력이 메모리 버퍼라 read가 즉시 EOF를 받고 릴레이 스레드가 스스로 끝났으므로, "입력이 영원히 오지 않는 read"라는 실제 상황이 재현되지 않았다.\
   취소 도달성 테스트는 **멈춘 상대**(응답 안 하는 RPC, 연결 거부, 입력 없는 stdin)를 만들고 "취소 후 상한 시간 안에 반환"을 단언해야 한다.

7. **같은 원리.** 호출자가 타임아웃으로 포기해도, 실제 작업을 하는 쪽이 취소를 관찰하지 않으면 작업은 계속 자원을 쥐고 돈다.\
   두 경우 모두 "포기 신호"가 "작업이 멈춰 있는 지점"까지 도달하지 못한 것이다 — 상한(타임아웃·취소)은 작업 쪽 대기 지점에 걸려야 자원을 돌려받는다.

## 문제 구조 (추상화 코드)

### 변형 A — 루프는 취소를 보는데 그 앞 대기는 안 봄
```rust
// ① 문제
async fn host_main(mut cmd_rx: Receiver<Cmd>, rpc: Rpc) {
    rpc.initialize().await;       // 상대가 멈추면 영구 대기 — Shutdown 도달 불가
    rpc.authenticate().await;
    rpc.new_session().await;
    loop { select! { cmd = cmd_rx.recv() => { /* Shutdown 처리 */ } /* ... */ } }
}

// ② 고침
async fn await_or_shutdown<T>(fut: impl Future<Output = T>, rx: &mut Receiver<Cmd>) -> Option<T> {
    tokio::pin!(fut);             // &mut fut 로 반복 폴링하려면 pin 필요
    loop {
        select! {
            v = &mut fut => return Some(v),
            c = rx.recv() => match c { Some(Cmd::Shutdown) | None => return None, _ => {} /* 핸드셰이크 중 다른 명령은 버림 */ },
        }
    }
}
if await_or_shutdown(rpc.initialize(), &mut cmd_rx).await.is_none() { child.kill(); return; }
```
무엇이 깨졌나: 취소 수신 지점이 루프에만 있어, 핸드셰이크 중 멈춘 상대가 스레드와 자식 프로세스를 영구히 붙잡았다.

### 변형 B — 강제 종료 불가 스레드 + 락 안 join
```rust
// ① 문제
fn remove(&self, id: Id) {
    let mut map = self.map.lock();
    let h = map.remove(&id);
    h.join.join();                 // 스레드가 connect/write에서 멈추면 락 쥔 채 영구 블록
}

// ② 고침
// 워커: 작업 future 전체를 취소와 경주
select! {
    res = run(/* ... */) => { if let Err(e) = res { status_tx.send(Failed(e)); } }
    _ = cancel_rx.changed() => { /* run future drop → 안의 모든 await 취소 */ }
}
// 소유자: 꺼내고 락 밖에서 cancel → join
fn remove(&self, id: Id) {
    let h = { self.map.lock().remove(&id) };   // 락 짧게
    if let Some(h) = h { h.cancel.send(()); h.join.join(); }
}
```
무엇이 깨졌나: 스레드를 외부에서 끝낼 수단이 없고, 그 대기가 공유 락을 통해 다른 세션으로 번졌다.

### 변형 C — 깨울 수 없는 블로킹 read를 join
```rust
// ① 문제
thread::scope(|s| {
    s.spawn(|| relay(stdin, sock));   // stdin.read에 파킹 — 다른 fd를 닫아도 안 깨어남
    pump(sock, stdout);               // 세션 종료 후 반환해도 scope가 relay를 join → 미반환
});

// ② 고침
thread::spawn(move || relay(stdin, sock_w));   // join하지 않음 — 스레드 자체는 입력·EOF 전까지 남으며, 단명 CLI라 프로세스 종료로 회수된다는 전제
loop {
    if peer_hung_up(&sock) { return Ok(0); }   // POLLHUP 감지로 반환
    // ... pump
}
// 테스트 입력: 즉시 EOF 버퍼가 아니라 "입력이 오지 않는" 스트림
```
무엇이 깨졌나: 입력이 오지 않는 한 끝나지 않는 스레드를 종료 경로가 기다렸다.

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)

## 방안 비교 — 셸: 앞쪽(foreground) 자식을 기다리는 동안 trap은 미뤄진다

같은 원리("취소 신호가 지금 멈춰 있는 대기 지점까지 닿아야 한다")가 **bash 스크립트의 중단 처리**에서 나타난 사례.\
측정 스크립트는 `trap teardown INT TERM HUP`으로 중단 시 정리(표본 수집기 종료·원격 컨테이너 삭제·로그 회수)를 걸어 두고, 수 분짜리 원격 부하 도구를 **앞쪽에서** 실행했다.\
중단 시험에서 TERM을 보냈는데 정리가 바로 돌지 않았다 — 부하 도구가 끝까지 돈 뒤에야 trap이 실행됐다.\
bash는 앞쪽 명령이 끝나기를 기다리는 동안 받은 신호의 trap을 **그 명령이 끝날 때까지 미룬다**. 대기 지점(앞쪽 자식)이 신호를 관찰하지 않는 셈이다.\
`wait` 내장 명령으로 기다리는 중이면 trap이 걸린 신호에 `wait`가 즉시(128보다 큰 코드로) 반환하고 곧바로 trap이 돈다 — 그래서 자식을 배경으로 돌리고 `wait`로 기다리게 바꿨다. 고친 뒤 TERM은 약 6초 안에 정리까지 끝났다.

```
앞쪽 실행        TERM ─▶ [bash: 자식 종료 대기 중 — trap 보류] ────── 자식 종료 ─▶ trap(정리)
배경 + wait      TERM ─▶ [wait 즉시 반환(>128)] ─▶ trap(정리: 자식 kill · 컨테이너 삭제 · 로그 회수)
```

### 방안 1 — 앞쪽 실행 (문제 코드)
```bash
trap 'teardown; exit 130' INT TERM HUP
sleep "$PRE_S"                                         # 기준선 대기 — 여기서도 trap 보류
remote "docker run --rm --name $CNAME $IMAGE loadgen ..." > "$OUT/tool.log" 2>&1   # 수 분 — 끝날 때까지 trap 보류
TOOL_EXIT=$?
sleep "$TAIL_S"
```

### 방안 2 — 배경 실행 + `wait` (고친 코드)
```bash
TOOL_PID=""
teardown() {
  # ...
  remote "docker rm -f $CNAME" > /dev/null 2>&1        # 원격 작업 자체를 멈춘다
  [[ -n "$TOOL_PID" ]] && kill "$TOOL_PID" 2>/dev/null  # 로컬 쪽 연결 프로세스도 남기지 않는다
  # ...
}
trap 'teardown; exit 130' INT TERM HUP
sleep "$PRE_S" & wait $!                               # 짧은 대기도 같은 방식 — 신호에 바로 깬다
remote "docker run --rm --name $CNAME $IMAGE loadgen ..." > "$OUT/tool.log" 2>&1 &
TOOL_PID=$!
wait "$TOOL_PID"
TOOL_EXIT=$?
sleep "$TAIL_S" & wait $!
trap '' INT TERM HUP                                   # 정상 경로의 정리 중에는 끊지 않는다(정리는 한 번만)
teardown
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 1. 앞쪽 실행 | 자식이 짧게 끝난다, 또는 신호가 프로세스 그룹 전체로 가서 자식도 함께 받는다 | 없음 | 스크립트에만 신호를 보내면 정리가 자식 수명만큼 미뤄진다 — 원격·컨테이너 자식은 로컬 신호를 받지도 않아 끝까지 돈다 | 짧은 명령, 터미널 Ctrl-C처럼 그룹 전체에 신호가 가는 대화형 실행 |
| 2. 배경 + `wait` | trap이 자식(과 원격 작업)을 직접 멈춘다 | PID 관리, `wait` 반환 코드(>128 = 신호)와 자식 종료 코드를 구분해야 함 | `wait`만 깨고 자식을 안 죽이면 고아로 남는다, 배경 자식은 stdin이 끊겨 대화형 입력을 못 받는다 | 수명이 긴 자식, 서비스 매니저·캠페인 러너가 스크립트에만 신호를 보내는 무인 실행 |

**결론**: 스크립트가 신호를 "받는다"(trap이 있다)와 신호가 **지금의 대기 지점에 닿는다**는 다르다 — 오래 걸리는 자식은 배경으로 띄우고 `wait`로 기다려 대기 자체를 신호에 깨어나게 하고, trap은 자식과 원격 작업을 직접 멈춘다.\
짧은 `sleep`도 같은 이유로 `sleep N & wait $!`로 바꾼다 — 중단 시험(신호를 보내고 정리까지 걸린 시간을 재는 것)으로 확인한다.\
검증 기록: 2026-10-11 사건 기록 대조·추상화(Claude 초안) — 표의 "프로세스 그룹"·"배경 자식의 stdin" 항목은 일반 원리(사건에서 관측하지 않음).

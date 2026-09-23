# cs/issue/rust/tokio/select-loop-semantics — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 기준. 복습 전 읽지 말 것.

태그: `resource-bounding`

## 정답
<!-- 질문 1:1 대응 -->

1. **패턴 불일치 = 분기 비활성화.** `Some(msg) = rx.recv()`에서 `None`이 오면 패턴이 맞지 않아 **그 분기만 비활성화**되고(그 `select!` 호출 한 번 동안 — 다음 바퀴에 다시 poll되면 또 즉시 `None`이라 또 꺼진다) 루프는 계속 돈다.\
원격이 닫혀도 루프가 끝나지 않아 스레드가 조용히 남는다.\
두 분기가 모두 비활성화되면 `else` 분기가 없는 `select!`는 panic한다("all branches are disabled and there is no else branch").\
그래서 모든 분기를 `match`로 받아 `Eof | Close | None => break`를 명시한다.
   > **select!** — 여러 future 중 먼저 준비된 것 하나의 분기를 실행하는 매크로. 분기 패턴이 맞지 않으면 그 분기를 끄고 나머지로 계속 기다린다.

2. **닫힌 채널은 영원히 준비 상태.** 송신측이 drop된 `changed()`는 기다리지 않고 **즉시** `Err`를 반환하고, 다음 호출도 또 즉시 `Err`를 반환한다.\
`select!`는 매 바퀴 이 분기를 "준비됨"으로 보고 고르므로, `Err`를 무시하면 루프가 쉬지 않고 돌아 런타임 스레드를 태운다(busy loop).\
전형적 처리는 `Err(_) => break`다 — 다른 분기는 계속 살려야 한다면 플래그와 분기 precondition(`, if !closed`)으로 그 분기만 끈다. 핵심은 `Err`를 무시한 채 같은 분기를 다시 poll하지 않는 것이다.

3. **본문 안의 쪼개기는 쪼개기가 아니다.** `select!`는 선택된 분기의 본문이 끝날 때까지 다른 분기를 poll하지 않는다.\
본문 안에서 8KB씩 루프를 돌며 await해도, 다른 분기 입장에서는 "전 청크를 다 보낼 때까지" 하나의 긴 블록이다.\
고친 방법은 입력을 pending 버퍼에 받아두고(버퍼가 빌 때만 새 입력 수신), **루프 한 바퀴에 한 청크만** 쓰는 always-ready 분기를 따로 두는 것이다 — 그러면 매 바퀴 출력 분기도 선택될 기회를 얻는다(`select!` 기본은 분기 poll 순서 무작위 — `biased;`면 순서 고정이라 always-ready 분기를 앞에 두면 다시 굶길 수 있다). 단 청크 한 번의 await 동안은 여전히 다른 분기가 멈춘다 — 흐름제어로 그 await가 오래 걸리는 문제는 4번.
   > **기아(starvation)** — 한 작업이 실행 기회를 독점해 다른 작업이 진행하지 못하는 상태.

4. **자기 교착의 원.** 쓰기는 상대가 광고한 창이 0이면 WINDOW_ADJUST를 기다린다.\
그 메시지를 배달하는 것은 연결 이벤트 루프뿐인데, 그 루프는 채널 수신 큐(용량 100)가 차면 park한다.\
큐를 비우는 것은 우리 쪽 읽기인데, 쓰기가 `select!` 분기 본문에서 await 중이라 읽기가 poll되지 않는다.\
쓰기 → 창 대기 → 연결 루프 → 수신 큐 → 읽기 → 쓰기 완료 대기로 원이 닫힌다 — 라이브러리 버그가 아니라 **우리 구조**가 만든 교착이다.
   > **흐름제어 창(window)** — 수신측이 "이만큼 더 받을 수 있다"고 광고한 바이트 수. 0이면 송신측은 창이 다시 열릴 때까지 멈춘다.

5. **두 신호의 이유.** reader와 writer를 `join!`으로 묶으면 **둘 다 끝나야** join이 끝난다.\
원격이 사라져 reader가 끝나도, writer는 입력 큐 `recv()`나 영원히 열리지 않을 창 위에 앉아 있어 join이 끝나지 않는다.\
그래서 reader가 채널 종료를 `done` 신호로 알려 writer를 깨운다.\
또 하나의 신호 `Success`는 원격이 명령을 수락한 뒤에만 쓰기를 시작하게 하는 허가다.

6. **대조군이 실패하지 않으면 처치는 아무것도 증명하지 않는다.** 기본 2MB 창에서는 쓰기가 애초에 park하지 않아 옛 구조도 교착하지 않았다 — 그 상태의 "교착 없음"은 실험 실패다.\
창을 64KB로 줄여 **대조군이 결정론적으로 교착하는 것(5/5)**을 먼저 확인한 뒤에야 처치군 0/30이 의미를 가진다.\
독립 재현에서도 64KB 창에서 대조군 8/8 교착·처치군 0/15, 더 작은 창(32KB·8KB·2KB)에서 처치군 0/18이었다.\
회귀 테스트에는 데드라인 가드를 둬 교착이 무한 대기가 아니라 **실패**로 나오게 했고, 옛 구조를 다시 주입하면 그 테스트만 실패함을 확인했다.

7. **런타임 드라이버.** tokio `runtime::Builder`로 런타임을 직접 만들면 IO 드라이버·타이머 드라이버는 기본 꺼져 있어 `enable_io()`/`enable_time()`(또는 `enable_all()`)로 켜야 한다(`#[tokio::main]`·`Runtime::new()`는 모두 켠 상태로 만든다).\
IO 드라이버(reactor)가 없으면 소켓이 읽기·쓰기 가능해졌다는 것을 통지할 주체가 없어 비동기 I/O가 진행될 수 없다 — tokio 1.x는 이 경우 소켓을 런타임에 등록하는 시점에 "IO is disabled" panic을 낸다.\
`new_current_thread().enable_all().build()`로 켜고, 코드 옆에 경고 주석을 남겼다 — 설계 리뷰 단계에서 막은 결함이다.

## 문제 구조 (추상화 코드)

### 변형 A — 종료 조건 누락 (패턴 불일치·닫힌 채널)
① 문제 코드
```rust
loop {
    tokio::select! {
        Some(msg) = chan.wait()      => handle(msg),     // None → 분기 비활성화, 루프는 계속
        Some(buf) = input_rx.recv()  => write(buf).await,
        _ = size_rx.changed()        => resize(),         // sender drop 후 즉시 Err 반복 → busy loop
    }
}
```
② 고친 코드
```rust
loop {
    tokio::select! {
        msg = chan.wait() => match msg {
            Some(Msg::Data(d)) => emit(d),
            Some(Msg::Eof) | Some(Msg::Close) | None => break,
            Some(_) => {}
        },
        inp = input_rx.recv() => match inp { Some(b) => pending = b, None => break },
        ch = size_rx.changed() => match ch { Ok(_) => resize(), Err(_) => break },
    }
}
```
무엇이 깨졌나: 종료 신호(None/Err)를 패턴으로 걸러 버려 루프가 끝나지 않거나 쉬지 않고 돌았다.

### 변형 B — 분기 본문의 긴 쓰기가 출력 분기를 굶김
① 문제 코드
```rust
Some(buf) = input_rx.recv() => {
    for chunk in buf.chunks(WRITE_CHUNK) {        // 본문 안에서 쪼개도
        chan.data(chunk).await?;                  // 전 청크를 다 보낼 때까지 출력 분기 poll 없음
    }
}
```
② 고친 코드
```rust
inp = input_rx.recv(), if pending.is_empty() => match inp {   // backlog 있으면 새 입력 안 받음
    Some(b) => pending = b, None => break,
},
_ = std::future::ready(()), if !pending.is_empty() => {        // always-ready: 턴당 1청크
    let n = pending.len().min(WRITE_CHUNK);
    if chan.data(&pending[..n]).await.is_err() { break; }
    pending.drain(..n);
}
```
```rust
// 입력 큐도 유계 + 가득 차면 거절 (UI 스레드를 막지 않음)
match input_tx.try_send(data) { Err(TrySendError::Full(_)) => Err("input buffer full"), /* ... */ }
```
무엇이 깨졌나: 본문 await 동안 다른 분기가 poll되지 않는다는 `select!` 의미를 놓쳤고, 무계 큐는 메모리 상한이 없었다.\
같은 구조: 반대 방향(stderr 전달)은 유계 채널의 `send().await` 자체를 backpressure로 써서 무손실로 원격까지 늦춘다 — 이 경우 수신자는 반드시 드레인해야 한다.

### 변형 C — 흐름제어 채널의 자기 교착
① 문제 코드
```rust
loop {
    tokio::select! {
        msg = chan.wait()          => { /* 출력 처리 */ }
        Some(b) = stdin_rx.recv()  => chan.data(&b).await?,   // 창 0 → park, 그동안 읽기 멈춤
    }
}
```
② 고친 코드
```rust
let (mut read, write) = chan.split();
let reader = async {
    while let Some(msg) = read.wait().await {          // 단일 await 소스
        match msg { Msg::Success => ok_tx.send(()), /* ... */ }
    }
    done_tx.send(());                                  // 채널 종료 → writer 해제
};
let writer = async {
    if ok_rx.await.is_err() { return; }                // 수락 뒤에만 쓰기 (수락 없이 reader 종료 시 쓰지 않음)
    loop {
        tokio::select! {
            Some(b) = stdin_rx.recv() => write.data(&b).await?,
            _ = &mut done_rx => break,
        }
    }
};
tokio::join!(reader, writer);                          // 매 wake마다 둘 다 poll
```
무엇이 깨졌나: 쓰기 await가 읽기를 멈춰 창을 여는 경로 자체를 막았다.\
같은 구조: 교착을 풀기 전 임시 조치로 stdin 쓰기를 통째로 제거(출력 전용)해 "쓰기 0 → 교착 클래스 부재"로 만들었다 — 동기 flush·select 상태머신 재작성 두 시도가 모두 교착을 재현한 뒤의 정지 결정이었다.\
같은 구조: 출력 전용 경로에서 stdin EOF를 기다리는 명령이 끝나지 않는 문제는 수락 직후 `eof()`를 한 번 보내 해결 — `eof()`는 창을 보지 않는 제어 경로라 교착 클래스를 다시 들이지 않음을 먼저 실증했다.

### 변형 D — current_thread 런타임에 IO 드라이버 미활성
① 문제 코드
```rust
let rt = tokio::runtime::Builder::new_current_thread().build()?;   // reactor 없음
rt.block_on(connect_and_run());                                    // TCP I/O 진행 불가
```
② 고친 코드
```rust
// MUST enable the IO driver or TCP I/O won't run
let rt = tokio::runtime::Builder::new_current_thread().enable_all().build()?;
// 세션 전용 OS 스레드에 런타임을 가두고 block_on으로 바깥 API는 동기 유지
```
무엇이 깨졌나: 런타임 빌더의 기본값에 드라이버가 포함된다고 가정했다(`#[tokio::main]`과 달리 Builder는 드라이버가 기본 꺼짐).

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)

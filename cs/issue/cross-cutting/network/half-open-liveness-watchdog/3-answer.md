# cs/issue/network/half-open-liveness-watchdog — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 대조·추상화. 복습 전 읽지 말 것.

태그: `silent-failure`

## 정답
<!-- 질문 1:1 대응 -->

1. **half-open과 보낼 게 없는 쪽.**\
   TCP가 상대의 소멸을 알게 되는 경로는 대개 "내가 보낸 세그먼트에 ACK가 안 오거나 RST가 오는 것"이다.\
   출력을 받기만 하는 쪽은 보낼 데이터가 없으니 ACK를 기다릴 일도 없어, 상대 호스트가 사라져도 에러가 발생하지 않는다 — 연결은 이쪽 커널에서 계속 "열림"이다.\
   그 위의 SSH도 비활성 감지(`inactivity`)가 0(꺼짐)이라 끊지 않았다. 정말로 아무것도 보내지 않는 소켓이라면(keepalive도 없으면) 이론상 **무기한** 모른다.\
   이 사건의 약 15분은, 받는 쪽도 결국 보낼 것(예: SSH 흐름 제어의 창 조정 메시지·프로토콜 제어 패킷)이 생기고 그 세그먼트가 ACK를 못 받아 운영체제의 재전송 한도(리눅스 기본 `tcp_retries2` 설정에서 대략 15분 남짓)가 소진된 시점으로 설명된다(일반론 — 정확한 시간은 RTO·커널 설정에 따라 다르다).
   > **half-open 연결** — 한쪽 끝은 사라졌는데 다른 끝은 여전히 열려 있다고 믿는 TCP 연결.

2. **하트비트가 있어도 감지 못한 이유.**\
   데몬의 15초 하트비트(시각·실행 상태)는 도착하고 있었지만, 브리지가 그 값을 **버렸다** — 어떤 판정에도 쓰지 않았다.\
   하트비트는 "N초간 아무 것도 안 왔다"를 검사하는 코드가 있어야 비로소 liveness 신호가 된다. 받고 버리는 하트비트는 없는 것과 같다.

3. **바이트 기준 시계의 구멍.**\
   도착 바이트로 시계를 갱신하면, 100ms마다 1바이트를 흘리는 스트림은 시계를 계속 새로 고쳐 **워치독을 무기한 회피**한다 — 그동안 화면은 한 줄도 갱신되지 않는다.\
   liveness가 증명해야 하는 것은 "바이트가 흐른다"가 아니라 "의미 있는 진행이 있다"이므로, 갱신 기준을 `consume()`이 실제로 적용한 **완성 줄 수 > 0**으로 바꿨다.\
   이 결함은 post-fix 감사에서 나왔고, "100ms마다 1바이트" e2e로 이빨을 확인했다.

4. **검사 위치.**\
   데드라인 검사가 수신 타임아웃 에러 분기 안에만 있으면, 바이트가 계속 오는 동안 그 분기에 들어가지 않으므로 검사는 **0번** 실행된다.\
   워치독 검사는 수신 결과(데이터/타임아웃/에러)와 무관하게 **루프의 매 턴** 실행돼야 한다.

5. **임계값과 같은 사건.**\
   너무 짧으면 정상적인 하트비트 지연·일시 정체에도 재연결이 잦아지고(플래핑), 너무 길면 죽은 화면을 오래 보여 준다. 하트비트 주기의 배수(15초 × 3 = 45초)로 잡으면 대략 하트비트 두 번 연속 유실까지는 견딘다(지연 편차가 크면 여유를 더 둔다).\
   화면의 "마지막 프레임 N초 전"과 재연결 판정이 서로 다른 사건(하나는 바이트, 하나는 프레임)으로 갱신되면, 화면은 신선하다고 하는데 재연결은 일어나거나 그 반대가 된다 — 사용자에게 보이는 신호와 시스템 판단이 어긋난다. 그래서 `last_frame_at` 하나를 노출하고 두 판단이 공유하게 했다.

6. **DB 스트리밍의 무음 hang.**\
   서버 측 커서 스트리밍에서 클라이언트가 느리게 소비하면 서버는 쓰기 타임아웃으로 연결을 정리하지만, 그 정리가 클라이언트에 FIN/RST로 전달되지 않거나(중간 장비의 연결 추적 만료 등) 클라이언트 드라이버가 읽기 타임아웃 없이 블록돼 있으면 클라이언트는 이를 감지하지 못하고 **에러 없이 무한 대기**가 된다 — 같은 "받는 쪽이 끊김을 모른다" 구조다(정상적으로 종료 신호가 도달하면 보통은 읽기 에러로 드러난다).\
   교정은 워치독 대신 **작업 단위를 끝이 있는 요청으로 쪼개는** 것이었다: 키셋 페이지네이션(`WHERE key > :last ORDER BY key LIMIT N` 반복) + `--resume`. 요청마다 완료/실패가 명시적으로 돌아오고, 중단돼도 마지막 키부터 재개한다(재설계 후 초당 약 2만 행으로 안정).
   > **키셋 페이지네이션** — OFFSET 대신 "마지막으로 본 키보다 큰 것"으로 다음 페이지를 가져오는 방식. 키에 인덱스가 있으면 페이지가 뒤로 가도 비용이 거의 일정하다.

7. **세 층의 증명 범위.**\
   TCP keepalive는 "상대 커널이 이 연결을 아직 안다"를, SSH 비활성 감지는 "SSH 세션 상대가 응답한다"를 증명할 뿐, **앱이 의미 있는 데이터를 만들고 있는지**는 증명하지 않는다.\
   "연결이 살아 있다 ⊃ 데이터가 흐른다 ⊃ 의미 있는 진행이 있다" — 앱 레벨 워치독만 가장 안쪽을 판정한다.\
   이빨 있는 테스트는 두 시나리오를 구분해야 한다: **완전 침묵(600초 무출력)**과 **무의미한 흐름(100ms마다 1바이트, 개행 없음)**. 바이트 기준 워치독은 앞의 것만 잡고, 프레임 기준 워치독은 둘 다 잡는다.

## 문제 구조 (추상화 코드)

### 변형 A — 하트비트를 받고 버림 (판정 없음)
① 문제 코드
```rust
loop {
    match rx.recv() {
        Ok(Msg::Heartbeat { .. }) => {}                 // 버림
        Ok(Msg::Output(chunk)) => screen.apply(chunk),
        Err(_) => break,                                // TCP 에러가 와야만 종료 → ~15분
    }
}
```
② 고친 코드
```rust
const STALE: Duration = HEARTBEAT * 3;                  // 15s × 3 = 45s
let mut last_frame_at = Instant::now();
loop {
    match rx.recv_timeout(TICK) {
        Ok(Msg::Heartbeat { .. }) => last_frame_at = Instant::now(),   // 하트비트도 완성 프레임
        Ok(Msg::Output(chunk)) => { /* 변형 B */ }
        Err(RecvTimeoutError::Timeout) => {}
        Err(_) => break,
    }
    if last_frame_at.elapsed() > STALE { return Reconnect; }   // 매 턴 검사 (변형 B의 교정 포함)
    snapshot.last_frame_at_ms = to_ms(last_frame_at);          // 화면 나이 = 같은 시계
}
```
무엇이 깨졌나: 출력 전용 연결에서 소멸을 TCP 에러에만 맡겼다.

### 변형 B — 워치독 시계를 바이트로 갱신 + 검사가 에러 분기 안
① 문제 코드
```rust
match rx.recv_timeout(TICK) {
    Ok(chunk) => last_frame_at = Instant::now(),        // 1바이트/100ms 가 영원히 회피
    Err(_) => {
        if last_frame_at.elapsed() > STALE { return Reconnect; }   // 바이트가 계속 오면 0회 실행
    }
}
```
② 고친 코드
```rust
match rx.recv_timeout(TICK) {
    Ok(chunk) => {
        let lines = parser.consume(&chunk);             // 적용한 "완성 줄" 수 반환
        if lines > 0 { last_frame_at = Instant::now(); }
    }
    Err(_) => {}
}
if last_frame_at.elapsed() > STALE { return Reconnect; }  // 루프 매 턴
// 접속 직후: HELLO_DEADLINE(20s) 안에 Hello 없으면 실패, 재접속은 지수 백오프
```
무엇이 깨졌나: "무언가 도착"을 "진행"으로 셌고, 검사를 데이터가 없을 때만 돌렸다.

### 변형 C — 긴 서버 측 스트림이 끊겨도 클라이언트가 무한 대기
① 문제 코드
```python
cursor = conn.cursor(server_side=True)
cursor.execute("SELECT * FROM big_table")             # 수억 행 단일 스트림
for row in cursor:                                     # 소비 느림 → 서버 쓰기 타임아웃 → 무음 정지
    load(row)
```
② 고친 코드
```python
last = resume_point() or MIN_KEY                       # --resume
while True:
    rows = conn.execute(
        "SELECT * FROM big_table WHERE id > :last ORDER BY id LIMIT :n",
        {"last": last, "n": N}).fetchall()             # 끝이 있는 요청 — 성공/실패가 명시적
                                                       # (요청마다 문장/읽기 타임아웃을 함께 걸어야 한 페이지의 hang도 끊긴다)
    if not rows:
        break
    load(rows)                                         # 적재는 멱등(upsert)이어야 한다 — load 후 저장 전 중단되면 재개 시 이 페이지를 다시 적재
    last = rows[-1].id
    save_resume_point(last)
```
무엇이 깨졌나: 끊김을 알릴 수단이 없는 긴 스트림 하나에 전체 진행을 걸었다.

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)

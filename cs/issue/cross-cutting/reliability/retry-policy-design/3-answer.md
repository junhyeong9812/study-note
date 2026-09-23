# cs/issue/reliability/retry-policy-design — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 원문 대조 작성. 복습 전 읽지 말 것.

태그: `resource-bounding`

## 정답
<!-- 질문 1:1 대응 -->

1. **영구 실패는 재시도로 안 바뀐다.** 재시도가 의미 있는 것은 "시간이 지나면 조건이 바뀔 수 있는" 실패(네트워크 끊김·상대 재기동)뿐이다.\
인증 거부·키 로드 실패·agent 없음·원격에 실행 파일 없음(exit 127)은 사람이 설정을 고치기 전까지 몇 번을 다시 해도 결과가 같다.\
이들을 일시 실패로 분류하면 루프가 영원히 돌고, 화면은 "재시도 중"으로만 보여 사용자는 조치할 기회를 못 얻는다.
   > **영구 실패 / 일시 실패(permanent / transient)** — 재시도로 결과가 바뀔 수 없는 실패와, 시간이 지나면 성공할 수 있는 실패.

2. **없는 비밀이 공격처럼 보이는 인증 시도가 된다.** `unwrap_or_default()`는 "비밀번호 없음"을 "빈 비밀번호"로 번역한다 — 둘은 다른 사실이다.\
빈 비밀번호로 15초마다 영원히 인증을 시도하면, 상대 서버의 인증 시도 상한·무차별 대입 차단기가 이것을 공격으로 보고 **사용자 주소를 차단**할 수 있다.\
방어 장치가 정상 사용자를 막는 것이다. 교정: 비밀이 없으면 **에러**로 멈추고(조용한 기본값 금지), 인증 실패는 영구 실패로 분류해 조치 안내를 띄운다.

3. **텍스트 부분일치는 오탐한다.** stderr 4KB 어디에든 `"not found"` 한 줄만 있으면 영구 판정이 뒤집힌다 — 무관한 경고 문구로도 재시도가 끊기거나 반대가 된다.\
영구 판정은 **구조화된 신호**(예: 종료 코드 127)로만 하고, 텍스트는 사람에게 보여 줄 세부로 쓴다.\
구조화 신호가 없으면 영구라고 **단정하지 않고** 일시로 둔다(재시도 상한이 따로 루프를 막는다).

4. **poison message.** 입력 자체가 결정적으로 처리 불가능한 메시지다(한도 초과 줄, 디코드 불가 바이트, 필수 필드 없는 데이터).\
재연결은 같은 커서에서 같은 메시지를 다시 받으므로 같은 실패가 무한 반복된다(라이브락 — 계속 일하지만 진행 0).\
손실을 "갭"으로 보고 전체 스냅샷을 다시 받게 하면 더 나빠진다: 문제 바이트가 **스냅샷 안에** 있으면 매 재접속이 같은 자리에서 실패하고, 상태가 클수록 스냅샷에 들어갈 확률이 높아지는 자기강화 실패가 된다(실측 10초에 재접속 11회).\
교정: 한도 초과 줄은 그 줄만 버리고 다음 개행에서 재동기, 재시도 상한을 넘으면 "건너뛰고 갭 표시"(줄 경계가 온전해 잃은 것이 정확히 하나일 때) 또는 치명 종료(잃은 길이를 모를 때).
   > **라이브락(livelock)** — 교착처럼 멈춘 게 아니라 계속 상태를 바꾸며 움직이지만 아무 진행도 없는 상태.

5. **진행을 증명하는 사건에서만 리셋.** 재접속 "성공"은 연결이 됐다는 뜻일 뿐 문제 입력을 넘어섰다는 뜻이 아니다 — 재접속마다 손실 카운터를 0으로 되돌리면 상한에 영원히 도달하지 못한다.\
카운터는 **실제 진행을 말할 수 있는 유일한 사건**(여기서는 온전한 스냅샷 수신)에서만 리셋해야 상한(3회)이 작동한다.\
같은 논리로 백오프 간격도 "진행이 있었을 때" 리셋해야 한다(성공 후에도 안 리셋되면 긴 간격이 남는다).

6. **두 극단 모두 계약 위반.** 스트림 소비자의 계약이 "예외 → 미확인 → pending 재처리"라면:\
전부 삼키면(로그 후 정상 반환) 리스너가 ACK해 버려, DB 미기동 같은 **일시** 장애가 **영구 유실**로 바뀐다.\
전부 재던지면 필수 필드가 없는 **결정적** 결함 메시지가 무한 재처리된다(poison pill).\
기준: 인프라 오류(연결·미초기화)는 재던져 재처리, 데이터 결함(키·타입·값 오류)은 로그 후 폐기(ACK), 전달 횟수 상한(5회)을 넘은 pending은 폐기.\
주의: 타입 기반 분류는 휴리스틱이라 경계가 샌다(예: 무결성 위반 예외가 값 오류 계열이 아니어서 재시도됨) — 격리 스트림(DLQ)이 다음 단계다.
   > **at-least-once** — 메시지를 최소 한 번은 처리함을 보장(중복 가능). 처리 성공 전에 ACK하면 이 보장이 깨진다.

7. **fixedDelay는 "마지막 실행 완료 후 N"이다.** 실패 항목들은 실패 시각이 제각각인데, 폴링은 직전 폴링이 끝난 시각 기준으로 돌므로 "실패 후 N분"이 보장되지 않고 재시도가 한 시점에 몰린다.\
교정: 실패 항목에 `nextRetryAt = 실패 시각 + 지연(30분, 60분)`을 저장하고, 짧은 주기(1분)로 폴링하며 `now < nextRetryAt`인 항목은 건너뛴다. 최대 횟수(2회)와 멱등 삽입을 함께 둔다.

## 문제 구조 (추상화 코드)

### 변형 A — 영구 실패를 일시로 분류 + 없는 비밀을 기본값으로
① 문제 코드
```rust
let password = req.password.or_else(|| keychain.get(id)).unwrap_or_default();   // 없음 → ""
loop {
    match connect(host, &password).await {
        Ok(link) => return Ok(link),
        Err(e) if e.is_unknown_host_key() => return Err(e),   // 이것만 영구
        Err(_) => sleep(backoff.next()).await,                // 인증 거부·키 없음·exit 127 → 영원히 재시도
    }
}
```
② 고친 코드
```rust
fn secret(req: &Req) -> Result<String> {
    req.password.clone().or_else(|| keychain.get(req.id))
        .ok_or(Error::MissingSecret)                           // 조용한 기본값 금지
}
fn permanent_reason(e: &ConnError) -> Option<Reason> {
    match e {
        ConnError::AuthRejected | ConnError::KeyLoad | ConnError::NoAgent => Some(..),
        ConnError::Exit { code: Some(127), .. } => Some(Reason::RemoteBinaryMissing),   // 구조화 신호만
        ConnError::Exit { code: None, .. } => None,           // 신호 없으면 단정 안 함 → 일시
        _ => None,
    }
}
loop {
    match connect(host, &secret(&req)?).await {
        Ok(link) => { backoff.reset(); return Ok(link) }
        Err(e) => match permanent_reason(&e) {
            Some(r) => return Err(Failed(r)),                  // 중단 + 조치 안내
            None => sleep(backoff.next()).await,
        },
    }
}
// 회귀 테스트: secret() 이 빈 문자열을 돌려주게 되돌리면 "없는 비밀은 빈 비밀번호가 아니다" 테스트가 실패
```
무엇이 깨졌나: "없음"이 빈 값으로 번역되고, 영구 실패가 일시로 분류되어 원격 방어를 발동시키는 루프가 무음으로 돌았다.

### 변형 B — poison 입력 + 재접속마다 리셋되는 카운터 (자기강화 루프)
① 문제 코드
```rust
match reader.next_line() {
    Err(LineTooLong) => reconnect(cursor),          // 같은 커서 → 같은 줄 → 라이브락
    Err(Decode(_))   => { cursor = None; reconnect(None) }   // 전체 스냅샷부터 다시 → 스냅샷 속 바이트에서 재실패
    Ok(line) => apply(line),
}
fn on_reconnected(&mut self) { self.losses = 0; }   // 재접속마다 리셋 → 상한 도달 불가
```
② 고친 코드
```rust
match reader.next_line() {
    Err(LineTooLong) => reader.skip_to_next_newline(),     // 그 줄만 버리고 재동기
    Err(Decode(_)) => {
        self.losses_since_snapshot += 1;
        if self.losses_since_snapshot > 3 {
            mark_gap();                                    // 줄 경계 온전 = 잃은 것 정확히 하나 → 건너뛰고 계속
        }
    }
    Err(Dropped) => return Ended::Fatal,                   // 잃은 길이 미상 → 치명
    Ok(line) => apply(line),
}
fn on_snapshot(&mut self) { self.losses_since_snapshot = 0; }   // 진행을 증명하는 유일한 사건에서만 리셋
// + 커서 역행 거부
```
무엇이 깨졌나: 결정적 실패를 재동기로 풀려 했고, 상한 카운터가 진행이 아닌 재접속에서 리셋됐다.\
남은 창: "스냅샷을 다시 달라"는 명령이 프로토콜에 없어, 디그레이드 모드(갭을 안고 계속 읽기)로 버틴다.

### 변형 C — 스트림 소비자의 ACK 계약: 전부 삼키기 vs 분류
① 문제 코드
```python
async def handle(msg):
    if db.session is None:
        logger.error("db not ready"); return        # 정상 반환 → 리스너가 ACK → 메시지 유실
    try:
        await process(msg)
    except Exception as e:
        logger.error(e)                              # 전부 삼킴 → ACK
```
② 고친 코드
```python
async def handle(msg):
    if db.session is None:
        raise RuntimeError("db not ready")           # 미ACK → pending → 재처리
    try:
        async with db.transaction():                 # 핸들러 단일 트랜잭션 (중간 커밋 제거 → 재처리 중복 방지)
            await process(msg)
        mark_seen(msg.id)                            # 멱등 표식은 DB 커밋 "후"에 (먼저 쓰면 재처리를 막음)
    except (KeyError, TypeError, ValueError, AttributeError) as e:
        logger.error(e)                              # 데이터 결함 → 폐기(ACK)
    except Exception:
        raise                                        # 인프라 오류 → 재처리

# 리스너: pending 재시도를 재시작 때만이 아니라 주기적(60초, 단조 시계)으로
#         전달 횟수 >= 5 인 pending 은 폐기, 복구 실패가 남으면 그 스트림만 정지 가드
```
무엇이 깨졌나: 핸들러가 실패를 성공으로 보고해 재처리 계약이 무력화됐다.\
(남은 한계: 타입 기반 분류는 휴리스틱, 격리 스트림은 후속, 스트림 길이 트리밍으로 장기 소비자 다운 시 유실 위험)

### 변형 D — 백오프 기준 시각: 폴링 완료 vs 실패 시점
① 문제 코드
```java
@Scheduled(fixedDelay = 30 * MINUTES)                // "직전 실행 완료 후 30분" — 실패 시점과 무관
void retryFailed() { failedQueue.forEach(this::sync); }
```
② 고친 코드
```java
record FailedSync(Instant failedAt, int attempts, Instant nextRetryAt, String lastError) {}
Queue<FailedSync> failed = new ConcurrentLinkedQueue<>();   // 단일 인스턴스 전제의 인메모리 큐

@Scheduled(fixedDelay = 1 * MINUTES)                 // 짧게 폴링
void retryFailed() {
    for (var f : failed) {
        if (now().isBefore(f.nextRetryAt())) continue;      // 실패 기준 백오프
        if (f.attempts() >= 2) { failed.remove(f); continue; }
        syncIdempotent(f);                                  // 없는 키만 삽입
    }
}
// 실패 시: nextRetryAt = failedAt + (attempts == 0 ? 30m : 60m)
```
무엇이 깨졌나: 백오프 의미를 폴링 주기에 맡겨 "실패 후 N"이 보장되지 않고 재시도가 몰렸다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

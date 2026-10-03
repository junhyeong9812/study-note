# issue/reliability/retry-policy-design — 정답

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
교정: 실패 항목에 `retryAt = 실패 시각 + 지연(30분, 60분)`을 저장하고, 짧은 주기(1분)로 폴링하며 `now < retryAt`인 항목은 건너뛴다. 최대 횟수(2회)와 멱등 삽입을 함께 둔다.

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
for attempt in 1.. {
    match connect(host, &secret(&req)?).await {
        Ok(link) => { backoff.reset(); return Ok(link) }
        Err(e) => match permanent_reason(&e) {
            Some(r) => return Err(Failed(r)),                  // 중단 + 조치 안내
            None if attempt >= MAX_ATTEMPTS => return Err(GaveUp(e)),   // "일시"로 둔 미분류 실패도 상한에서 멈춘다
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
        } else {
            resync();                                      // 상한 전까지만 재동기 시도
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
                                                     # 한계: 커밋과 표식 사이 장애면 중복 처리 가능 — 표식을 같은 트랜잭션 안에 쓰면 원자적
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
record SyncFailure(Instant failureTime, int attempts, Instant retryAt, String lastError) {}
Queue<SyncFailure> failed = new ConcurrentLinkedQueue<>();   // 단일 인스턴스 전제의 인메모리 큐

@Scheduled(fixedDelay = 1 * MINUTES)                 // 짧게 폴링
void retryFailed() {
    for (var f : failed) {
        if (now().isBefore(f.retryAt())) continue;      // 실패 기준 백오프
        failed.remove(f);                                   // 꺼내서 처리 (성공하면 다시 넣지 않음)
        try { syncIdempotent(f); }                          // 없는 키만 삽입
        catch (Exception e) {
            int n = f.attempts() + 1;
            if (n < 2) failed.add(new SyncFailure(now(), n, now().plus(60m), e.getMessage()));   // 재실패 시점 기준 재스케줄
            else log.error("give up", e);                   // 최대 횟수 초과 — 무음 폐기 금지
        }
    }
}
// 최초 실패 시: retryAt = failureTime + 30m (attempts = 0)
```
무엇이 깨졌나: 백오프 의미를 폴링 주기에 맡겨 "실패 후 N"이 보장되지 않고 재시도가 몰렸다.

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)

## 방안 비교

같은 원리("일시 실패는 재시도로 흡수하되, 재시도는 어디에·얼마나 둘지 정해야 한다")가 **수십 시간짜리 배치의 한 단계**에서 나타난 사례.\
측정 배치(약 67시간)는 조건마다 측정 커밋을 원격 서버에 배포하는 단계로 시작하는데, 이 배포 단계에는 **재시도가 없었다** — 회차 내부의 원격 호출 실패는 기록하고 진행하도록 만들어 두었지만 배포 실패만은 치명(비정상 종료 → 배치 중단)이었다.\
부하 PC~서버 경로의 수십 초 단절(서버에는 접속 시도 기록조차 없음 — 원인 미확정) 한 번에 배치가 두 번 멈췄고, 사람이 발견할 때까지 각각 약 8.5시간·2.5시간 유휴였다.

### 방안 1 — 코드 안 재시도 (그 단계에 상한 있는 재시도)
```bash
deploy() {                                        # 배포 = 완료 표식이 있으면 건너뜀 (재실행해도 안전)
  remote "test -f $DEST/$SHA/.deployed" && return 0
  git archive "$SHA" | remote "mkdir -p $DEST/$SHA && tar -x -C $DEST/$SHA && touch $DEST/$SHA/.deployed"
}
for i in 1 2 3 4 5; do                            # 일시 실패만 상한 있게 재시도
  deploy && break
  (( i == 5 )) && { echo "deploy failed after $i tries" >&2; exit 3; }
  sleep $(( 30 * i ))                             # 단절이 수십 초 → 그보다 긴 간격으로
done
```
(원 기록의 후속 후보 — 이 사례에서는 구현하지 않았다.)

### 방안 2 — 실행기 수준 재시작 + 멱등 재개 (이 사례의 선택)
```ini
[Unit]
StartLimitIntervalSec=6h
StartLimitBurst=5                 # 6시간에 최대 5번 — 영구 고장에서 무한 반복 방지
[Service]
ExecStart=/path/runner.sh --sha <SHA> --id <ID>   # 같은 id로 다시 불리면 끝난 조건을 건너뛰고 이어서
Restart=on-failure
RestartSec=180                    # 단절이 지나갈 시간
```
측정 도중이라 **코드를 바꾸지 않고**(측정 커밋 유지) 실행 유닛 설정만 바꿨다. 적용 이후 측정 종료까지 정지·자동 재시작 0회 — 재시작 경로가 실제로 돈 적은 없다.

### 비교

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 코드 안 재시도 | 실패 지점과 실패 종류(일시)를 코드가 알 수 있음, 그 단계가 멱등 | 코드 변경 → 새 커밋(실행 중 배치에는 적용 불가 — 실행 코드 = 기록 커밋 원칙), 단계마다 재시도 설계 | 영구 실패(인증·주소 오류)까지 재시도하면 시간만 소모, 재시도를 단계마다 흩으면 정책이 제각각 | 실패가 잦고 위치가 알려진 단계(원격 배포·네트워크 호출) |
| 실행기 재시작 + 멱등 재개 | 실행기 전체가 "같은 명령 재호출 = 이어서"를 보장 | 재시작 지연(분 단위) + 재진입 비용(재개 확인), 유닛 설정 | 재개가 멱등이 아니면 재시작이 결과를 덮어씀, 종료 코드를 가리지 않아 영구 실패(인자·커밋 불일치 등)도 상한까지 반복, 상한 소진 뒤엔 다시 사람 대기 | 실패 위치를 모르거나 코드를 바꿀 수 없을 때, 프로세스 자체가 죽는 실패까지 덮어야 할 때 |

**결론**: 둘은 대체재가 아니라 층이 다르다 — 알려진 일시 실패(원격 배포의 네트워크 단절)는 **그 단계에서** 상한 있는 재시도로 흡수하는 것이 가장 싸고 빠르며(분 단위 재시작·재진입이 없다), 실행기 재시작은 예상 못 한 위치·프로세스 사망까지 덮는 **바깥 백스톱**이다.\
이 사례처럼 실행 중이라 코드를 바꿀 수 없을 때는 바깥 백스톱이 유일한 선택이었고, 그것이 복구가 되려면 실행기가 이미 멱등 재개(끝난 조건 건너뛰기·계획 복원·끊긴 회차 보존)를 갖추고 있어야 했다.\
재시작 경로는 영구 실패와 일시 실패를 가리지 않으므로, 이 카드의 원칙(실패 분류) 그대로 — 영구 실패에 쓰는 종료 코드를 따로 두고 재시작 대상에서 빼는 것(예: systemd `RestartPreventExitStatus=`)이 다음 개선점이다(일반 원리, 미적용).\
검증 기록: 2026-10-02 사건 기록 대조·추상화(Claude 초안) — 방안 1과 종료 코드 구분은 일반 원리(사건에서 미적용).

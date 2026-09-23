# cs/issue/cross-cutting/reliability/lifecycle-signal-contract — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 원문 대조 작성. 복습 전 읽지 말 것.

태그: `silent-failure`

## 정답
<!-- 질문 1:1 대응 -->

1. **종료 ≠ 결과.** 진행 표시의 off 신호가 사실상 "답변 이벤트"였는데, 호스트는 답변이 비어 있으면 그 이벤트를 보내지 않았다. 도구만 쓴 턴·취소된 턴·에러 뒤 빈 응답 턴에서는 프론트가 **턴 종료를 관측하지 못해** 타이머가 남는다(계획 리뷰 단계 지적).\
   교정: 완료 채널이 닫히면 결과 유무와 무관하게 **무조건** `Finished`를 보낸다. 프론트의 busy off 조건은 `finished | error | disconnected`.
   > **종결 이벤트(terminal event)** — 한 작업의 생애에서 마지막으로 오는, 더 이상 아무 일도 없음을 알리는 신호.

2. **출력 ≠ 입력 준비.** 대화형 프로그램의 첫 출력은 환영·권한·신뢰 확인 화면일 수 있다 — 그때 주입한 입력은 **확인창에 들어간다**. 재기동 직후 주입은 프로그램이 아직 준비 전이라 유실될 수도 있다.\
   명시적 ready 신호가 없으면 주입은 휴리스틱일 수밖에 없다. 최선: 주입을 큐에 넣고, 출력이 잠잠해진(quiesce) 뒤 flush하고, 주입을 멱등하게 만들고, 수동 주입 버튼을 폴백으로 둔다. 완전 자동은 보장하지 않는다(설계상 수용).

3. **전송 ≠ 성립, 그리고 빠진 종결.** 실행 요청 API가 전송만 하고 원격의 Success를 기다리지 않았는데 Ready를 먼저 보냈다. 서버가 거부(Failure)하면 early return으로 끝나 **종결(Exit) 이벤트가 0개** — 소비자는 "종결이 안 왔다 = 아직 실행 중"으로 오독한다.\
   교정: Ready는 원격 Success 수신 **후**로 옮기고, Failure·전송 실패도 `Error`를 방출한 뒤 반환한다. 계약: 요청 전송 이후 소비자는 항상 **`Exit` XOR `Error` 정확히 1회**를 받는다. 그 이전 단계(연결·인증·거부·취소)는 이 이벤트가 0개이며 신호는 채널 종료 + 연결 상태로 온다는 것도 문서화했다.

4. **빈 값은 즉시 완료, never는 영원한 침묵.** 선언 타입이 특정 리액티브 타입인 핸들러가 null을 반환하면, 어댑터가 "빈 값" 공급자로 **구독해도 아무 신호도 내지 않는 객체**를 등록해 두었다. 프레임워크는 "빈 값 지원"으로 그 경로를 신뢰했으므로 응답이 완료되지 않고 **타임아웃까지 행**했다(같은 상황의 다른 리액티브 타입은 빈 완료).\
   교정: "빈 값"을 null item(→ 빈 publisher로 매핑)으로 바꾸는 한 줄. 테스트: 짧은 타임아웃 안에 즉시 null로 끝나는지 + 빈 publisher ↔ 리액티브 값 왕복 대칭.
   > **onComplete** — 리액티브 스트림에서 "더 이상 값이 없다"는 종결 신호. 이게 없으면 구독자는 계속 기다린다.

5. **EOF는 데이터 방향 종료, Close는 채널 종료.** 채널 프로토콜에서 EOF는 "더 보낼 데이터 없음"일 뿐이고, 종료 코드·종료 시그널 같은 메타데이터는 **EOF 뒤에** 올 수 있다. EOF에서 루프를 끊자 종료 정보 없이 `Exit{None, None}`을 보고했다.\
   교정: EOF는 `stdout_done = true`로만 표시하고 계속 드레인, Close/스트림 끝에서만 종료. 회귀 테스트: 서버가 data → eof → exit-status → close 순서로 보낼 때 회수 확인.

6. **상한이 정상보다 짧으면 정상을 죽인다.** 서브에이전트 "6초 무변화 = 완료" 판정은 긴 테스트 실행 같은 정상 무출력 구간마다 **완료 ↔ 재활성**을 진동시키고 매번 전체 재파싱을 일으켰다(→ 60초로 상향 + 재활성 세대 카운터). 배포 하트비트 180초는 3분 넘는 이미지 빌드를 **자동 취소**했다(→ 600초).\
   2차 사고: 취소가 공유 상태(`currentJob = None`)를 지우는데, 아직 실행 중인 경로가 그 상태를 가드 없이 읽어 TypeError가 났다 — null 체크 추가. 이후 자동 취소는 "실행 중 단계"로 한정하고 승인 대기는 별도 TTL 정책이 소유하도록 분리했다.\
   헬스 대기 상한(30회 × 2초)이 새 컨테이너의 초기화 시간보다 짧아, 실제로는 200을 응답 중인 컨테이너를 실패로 판정·종료한 사례도 있다(기록상 조치는 "대기 상한·start_period 상향 예정", 미적용).

7. **started ≠ healthy, ping ≠ 적재 완료, 패턴 ≠ 지금 준비.** 컨테이너가 "Up"이어도 모델 로딩(1~2분) 중인 서비스는 연결을 거부한다 — 기동 순서만 보장하는 의존 설정으로는 첫 호출이 0.8초 만에 실패했다. 교정: `condition: service_healthy` + 클라이언트 연결/읽기 타임아웃 명시. 모듈 import 시점에 원격 연결을 강제하면 기동 경합이 곧 크래시가 된다(기록된 조치는 수동 재시작).\
   DB 컨테이너의 `ping` 헬스체크는 초기 적재를 수행하는 **임시 서버**에도 응답해, 테이블이 일부만 적재된 시점을 healthy로 판정했다. 완료는 실서버의 "ready for connections" 로그·외부 TCP 접속으로 판정하고 테이블·뷰·함수 **개수로 확인**한다.\
   출력 스트림에서 준비 신호(대체 화면 진입 시퀀스)를 찾을 때, 신호가 **청크 경계에 걸치면** 청크별 매칭은 놓친다 — 경계 교차 매칭이 필요하다. 또 재접속 시 스냅샷 재생(replay) 청크에 든 신호는 과거의 흔적이지 "지금 준비됨"의 증거가 아니다 — live 청크만 증거로 쓴다.

## 문제 구조 (추상화 코드)

### 변형 A — 완료 신호를 결과 이벤트에 얹음
① 문제 코드
```rust
_ = done_rx.recv() => {
    if !answer.is_empty() { events.send(Answer { .. }); }   // 빈 턴 = 종료 통지 없음
}
```
② 고친 코드
```rust
_ = done_rx.recv() => {
    if !answer.is_empty() { events.send(Answer { .. }); }
    events.send(Finished { turn, session });                // 무조건 1회
}
// 프론트: busy = false on (finished | error | disconnected)
```
무엇이 깨졌나: "결과 있음"을 "종료"의 대리 신호로 썼다.

### 변형 B — 전송 직후 Ready · 거부 경로의 종결 누락
① 문제 코드
```rust
channel.exec(cmd).await?;          // 큐잉만
ready_tx.send(());                 // 원격이 받아들였는지 모름
match channel.wait().await {
    Some(Failure) => return,       // 종결 이벤트 없이 반환
    // ...
}
```
② 고친 코드
```rust
if let Err(e) = channel.exec(cmd).await { exec_tx.send(Error(e)); return; }
loop { match channel.wait().await {
    Some(Success) if !started => { started = true; ready_tx.send(()); }
    Some(Failure)             => { exec_tx.send(Error(Rejected)); return; }
    // ... 끝에서 Exit — 모든 경로가 Exit XOR Error 1회
}}
```
무엇이 깨졌나: 성립 신호를 전송에서 추론했고, 한 종료 경로가 종결 이벤트를 빠뜨렸다.

### 변형 C — "빈 값"을 영원히 무신호인 객체로 표현
① 문제 코드
```java
registry.singleOptionalValue(ReactiveT.class, () -> ReactiveT.never());   // 구독해도 신호 없음
```
② 고친 코드
```java
registry.singleOptionalValue(ReactiveT.class, () -> ReactiveT.nullItem()); // 즉시 빈 완료
```
무엇이 깨졌나: "값 없음"이 "끝나지 않음"으로 표현돼 프레임워크가 영원히 기다렸다.

### 변형 D — 조회를 시작도 못 하는 경로에 상태가 없음
① 문제 코드
```ts
if (!coord) return;                      // 좌표 없음 → 아무 상태도 안 바꿈 → "불러오는 중" 영구
// 활성 → 지연 조회 전이 시 보던 본문 캐시를 버림 → 화면이 조용히 빔
```
② 고친 코드
```ts
if (!coord) { setState({ kind: "error", reason: "no-coordinate" }); return; }
if (!inFlight && !arrived) setState({ kind: "retryable" });   // 클릭 가능한 재시도 안내
adoptCachedBodies(activeBodies, lazyCache);                   // 전이 시 받은 본문을 캐시로 승계
```
무엇이 깨졌나: 로딩의 끝(성공·실패)이 표현되지 않는 경로가 있었다.

### 변형 E — 첫 출력을 입력 준비로 추론
① 문제 코드
```ts
pty.onData(once(() => pty.write(seed)));   // 첫 출력 = 환영/확인 화면일 수 있음
```
② 고친 코드
```ts
queue.push(seed);
onQuiesce(pty, () => queue.flushIdempotent());   // 출력이 잠잠해진 뒤, 멱등 주입
// 수동 "주입" 버튼 폴백 — 완전 자동은 보장하지 않음(휴리스틱임을 명시)
```
무엇이 깨졌나: 명시적 ready 신호가 없는데 부수 사건을 준비로 간주했다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

기본 방안(변형 A~E)은 "준비·종결을 명시적 계약으로 모든 경로에서 1회 보낸다"이다. 명시 신호를 만들 수 없는 곳(외부 프로세스·프로토콜·컨테이너)에서 쓰인 다른 방안:

### 방안 1 — 출력 스트림 신호 감지: 경계 교차 매칭 + replay 배제
```ts
function makeReadyDetector(signal) {
  let matched = 0;                                   // 청크를 넘어 부분 일치 상태 유지 (KMP)
  return (chunk, origin /* "live" | "replay" */) => {
    if (origin === "replay") { matched = 0; return false; }   // 과거 재생은 증거 아님
    for (const b of chunk) { matched = step(matched, b); if (matched === signal.length) return true; }
    return false;
  };
}
// + settle 300ms, first-wins 폴백 3000ms (신호가 안 오는 경로가 있음), 발사 직전 차단 게이트
```

### 방안 2 — EOF가 아니라 Close까지 드레인
```rust
loop { match ch.wait().await {
    Some(Data(d)) => out.write(d),
    Some(Eof)     => stdout_done = true,           // 계속 읽는다
    Some(ExitStatus(c)) => code = Some(c),
    Some(Close) | None  => break,
}}
```

### 방안 3 — 시간 기반 추론의 상한을 정상 최장보다 길게
```text
무활동 완료 판정   6초   → 60초 (+ 재활성 세대 카운터)
하트비트 취소      180초 → 600초 (+ 취소 후 공유 상태 null 가드, 자동 취소는 실행 중 단계로 한정)
헬스 대기          30×2초 → 상향·start_period 증가 (기록상 미적용)
```

### 방안 4 — 기동 순서를 readiness에 건다
```yaml
depends_on:
  search: { condition: service_healthy }
  embedding:
    condition: service_healthy     # 모델 로딩(1~2분) 전 호출 = 연결 거부
# 클라이언트: connect 5s / read 3m 타임아웃 명시
# depends_on 은 같은 compose 프로젝트(합쳐진 모델) 안 서비스끼리만 걸린다 → 여기선 한 파일로 묶음
```

### 방안 5 — 헬스체크가 초기화 단계를 준비로 오판하지 않게
```yaml
# 문제: healthcheck: ping  → 초기 적재용 임시 서버도 응답 → 일부만 적재된 시점에 healthy
# 고친: 실서버 준비 로그 / 외부 TCP 접속 성공을 완료 신호로, 적재 결과는 개수로 검증
command: --log-bin-trust-function-creators=1   # 부수: 바이너리 로그 활성 시 DETERMINISTIC 등 선언 없는 함수 생성이 거부돼 import 가 중간 중단되던 것
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 명시 계약 | 신호를 내는 코드를 우리가 소유 | 모든 경로에 종결 방출 | 새 경로 추가 시 종결 누락 재발(테스트로 고정) | 자체 이벤트·스트림·상태 머신 |
| 1. 스트림 패턴 감지 | 외부 프로그램이 안정된 신호를 출력 | 매처·origin 구분 | 신호를 안 내는 모드·도구가 있음(폴백이 상시 경로) | 외부 대화형 프로그램 |
| 2. Close까지 드레인 | 프로토콜이 EOF와 Close를 구분 | 없음 | 서버가 Close를 안 보내면 대기(타임아웃 별도) | SSH 류 채널 |
| 3. 긴 시간 상한 | 정상 최장 공백을 추정 가능 | 이상 감지 지연 | 추정보다 긴 정상 작업이 오면 다시 오판 | 명시 신호가 없는 생존·완료 감시 |
| 4. healthy 에 의존 | 대상에 의미 있는 헬스체크가 있다 | 기동 시간 증가 | 헬스체크가 얕으면 여전히 조기 호출 | 긴 초기화를 가진 의존 서비스 |
| 5. 실서버 기준 준비 판정 | 초기화 단계와 실서비스 단계를 구분할 수 있다 | 판정 로직 | 개수 검증을 빼면 부분 적재가 다시 숨음 | 초기 적재가 있는 DB 컨테이너 |

**결론**: 신호를 내는 쪽을 소유하면 **명시 계약**이 가장 정확한 방법이다(기본).\
소유하지 못하면 추론할 수밖에 없는데, 그때는 추론의 약점을 명시적으로 막는다 — 경계·재생(1), 프로토콜 의미(2), 시간 상한(3), 초기화 단계(4·5).\
시간 기반 추론은 마지막 수단이다: 상한은 정상 최장보다 길게, 취소 뒤 공유 상태 접근은 가드한다.

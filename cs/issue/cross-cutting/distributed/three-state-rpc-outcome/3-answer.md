# cs/issue/distributed/three-state-rpc-outcome — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **응답이 없다는 것은 "처리 안 됨"이 아니라 "결과를 모름"이기 때문이다.**\
   요청이 서버에 도달해 처리된 뒤 응답만 늦거나 유실될 수 있다.\
   그래서 결과는 ① 미실행이 보증됨 ② 결과 모름 ③ 성공(또는 명시적 거절) 3상태다.\
   가장 흔한 사태(②)를 이분법에서 빼면 그것은 반드시 ①이나 ③으로 잘못 접힌다.
   > **ambiguous outcome(모호한 결과)** — 요청이 실행됐는지 호출자가 판단할 수 없는 상태. 타임아웃·연결 단절의 기본 의미.

2. **데이터는 적재됐는데 원장은 영구 실패로 남는다.**\
   FAILED가 종결 상태라서 뒤늦은 SUCCESS 콜백이 "상충"으로 버려진다.\
   이 결함은 원래 무한 대기(응답 없는 요청이 영원히 진행 중으로 남는 문제)를 고치려고 타임아웃을 넣은 수정이 만든 것이다 — 고친 결함의 정반대 방향.\
   교정: 비종결 `OUTCOME_UNKNOWN` 상태를 두어 후속 콜백이 원장을 정정할 수 있게 하고, 화면에서도 "실패"와 구분해 폴링 대상에 포함했다.

3. **`ConnectException`·`UnknownHostException`·`NoRouteToHostException` = 미도달 확실 → FAILED. `SocketTimeoutException` = 모름.**\
   앞의 셋은 TCP 연결이나 이름 해석 단계에서 실패해 요청 바이트가 나가지 않았음이 확실하다 — 단 클라이언트·프록시의 자동 재시도가 없다는 전제에서다(재시도가 있으면 앞선 시도가 이미 전달됐을 수 있다).\
   읽기 타임아웃은 요청이 이미 전달된 뒤다.\
   (이 클라이언트 스택에서는) 연결 타임아웃도 같은 예외 타입으로 올라와 메시지 문자열 외에는 읽기 타임아웃과 구분할 수 없으므로, 안전측인 "모름"으로 보낸다 — 예외 타입 구성은 HTTP 클라이언트 구현마다 다르다.\
   전부를 "모름"으로 묶으면 서버가 꺼져 있을 때(connection refused)까지 수동 종결 대기로 쌓이므로, 확실한 미도달은 분리한다.

4. **요청 바이트가 나갈 수 있는 첫 순간이 dial 성공이기 때문이다.**\
   dial 전 실패만 "미실행"이고, dial 후의 모든 오류(RST·write timeout·부분 write·응답 단절·컨텍스트 타임아웃·응답 서명 불일치)는 UNKNOWN이다.\
   "요청을 다 썼다(WroteRequest)" 신호도 서버 도달 증명이 아니다.\
   오류 문자열은 라이브러리·OS마다 달라 파싱하면 경계가 조용히 어긋난다 — dial 성공 여부를 atomic 플래그로 직접 기록한다.

5. **새 소유자가 방금 올린 라이브 슬롯일 수 있다.**\
   409는 "내가 소유권을 잃었다"는 뜻이므로 그 사이 다른 실행자가 같은 슬롯에 라이브를 올렸을 수 있다.\
   그걸 "미전환이니 정리"로 내리면 라이브가 절단되고, 거짓 "변화 없음(net-0)"이 보고되고 락까지 해제된다.\
   원칙: **정리는 미전환이 보증됐을 때만**.\
   "정리 전 라우트 재조회"는 조회 대상이 등록부라 실상태를 보증하지 못해 선택하지 않은 방법이 됐다.

6. **위조되거나 엉뚱한 응답의 body가 "정리해도 안전"으로 승격되기 때문이다.**\
   state 필드를 상태코드와 무관하게 파싱하면, 502·400 같은 중간 프록시·위조 응답 body에 `ROLLED_BACK`이 들어 있을 때 정리 허가가 된다.\
   그래서 state는 정확히 약속된 상태코드(500)에서만 신뢰하고, 2xx 전체가 아니라 200만 성공으로 본다.\
   평문 전송에서 "요청만 서명"하면 가짜 완료뿐 아니라 가짜 "미실행"도 만들 수 있어 중복 실행이 통과한다 — 응답도 requestId·body digest·상태를 결박해 서명한다.

7. **호출자가 모르는 사이 두 번째 실행이 생긴다.**\
   라이브러리가 표준 멱등 헤더를 보고 "재전송해도 안전"이라 판단해 자동 재시도하면(예: Go `net/http`는 `Idempotency-Key`·`X-Idempotency-Key` 헤더가 있는 요청을 멱등으로 보고, 재사용 연결이 끊긴 경우 재시도할 수 있다), "모름" 상태의 요청이 호출자 모르게 한 번 더 실행될 수 있다.\
   그래서 전용 헤더 이름을 쓰고, 프록시·리다이렉트·keep-alive를 끈 전용 전송 계층으로 요청마다 새 연결을 쓴다.\
   조회 결과 "기록 없음(ABSENT)"도 새 requestId 실행 허가로 쓰지 않는다.

## 문제 구조 (추상화 코드)

### 변형 A — 타임아웃을 종결 실패로 확정 + 늦은 성공 무시
① 문제 코드
```java
try {
    remote.submit(job);                       // read timeout 10s
} catch (ResourceAccessException e) {
    ledger.mark(job, FAILED);                 // 종결
}
// callback
void onCallback(Job job, Status s) {
    if (ledger.get(job).isTerminal()) return; // SUCCESS가 와도 무시
    // ...
}
```
② 고친 코드
```java
} catch (ResourceAccessException e) {
    Throwable c = e.getCause();
    if (c instanceof ConnectException || c instanceof UnknownHostException
            || c instanceof NoRouteToHostException) {
        ledger.mark(job, FAILED);             // 요청 미도달 확실
    } else {
        ledger.mark(job, OUTCOME_UNKNOWN); // 비종결: 후속 콜백이 정정
    }
}
```
깨진 것: "모름"을 종결 실패로 접어 원격의 성공 신호가 버려졌다.

### 변형 B — 실패 응답을 한 종류로 접어 불명 상태에서 파괴적 정리
① 문제 코드
```go
resp, err := switchRoute(req)
if err != nil || resp.Status != 200 {
    downIdleSlot()          // 409·500·전송 실패 모두 "미전환" 취급
}
```
② 고친 코드
```go
switch {
case err != nil:                                  // 전송 후 실패 = 모름
    return Unknown
case resp.Status == 409:                          // 소유권 상실 = 정리 금지
    return Unknown
case resp.Status == 500 && resp.State == "ROLLED_BACK":
    downIdleSlot(); return NetZero                // 미전환 보증일 때만 정리
case resp.Status == 200:
    return Switched
default:                                          // INDETERMINATE·그 외 코드
    return Unknown
}
```
깨진 것: 실패 응답의 보증 수준(미실행/롤백됨/불명)을 구분하지 않아 라이브를 내렸다.

### 변형 C — 전송 경계를 오류 문자열로 판정 + 비인증 응답
① 문제 코드
```go
resp, err := http.DefaultClient.Do(req)   // 기본 Transport: 재사용·자동 재전송 가능
if err != nil { return NotExecuted }      // 전송 후 단절도 "미실행"으로 접힘
state := parse(resp.Body)                 // 응답 인증 없음
```
② 고친 코드
```go
var dialed atomic.Bool                         // 요청마다 새 Transport·새 플래그(공유하면 판정이 섞임)
tr := &http.Transport{ Proxy: nil, DisableKeepAlives: true,
    DialContext: func(ctx context.Context, n, a string) (net.Conn, error) {
        c, err := dialer.DialContext(ctx, n, a)
        if err == nil { dialed.Store(true) }
        return c, err
    }}
// 요청 헤더: X-Request-ID (Idempotency-Key·X-Idempotency-Key 이름은 쓰지 않음)
resp, err := client(tr).Do(req)
if err != nil {
    if !dialed.Load() { return NotExecuted }  // dial 전만 미실행
    return Unknown
}
if !verifyHMAC(resp, requestID, bodyDigest) { return Unknown }
```
깨진 것: 미실행/모름 경계가 연결 수립 시점이 아니라 "오류 여부"로 그어졌고, 인증 없는 응답이 상태 근거가 됐다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

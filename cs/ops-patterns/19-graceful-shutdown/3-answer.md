# ops-patterns/19-graceful-shutdown — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 작성 방식: **2-summary를 닫고 기억만으로** 쓴다 → 실제 코드/원전으로 검증 → 틀린 부분만 수정.
> 기준 소스는 문서가 아니라 코드다 (`/home/jun/project/myway/ops-patterns/19-graceful-shutdown/impl/`).

⚠️ 정답은 Claude 초안(2026-09-14) — 원본 impl 코드·README 기준. 본인 검토 후 이 줄 삭제

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. -->

### A. 문제 (AbruptServer · GracefulServer 의 TODO)

#### 1. TODO 1 — AbruptServer.stop

정답 코드 (impl/AbruptServer.java):

```java
int abandoned;
synchronized (this) {
    phase = Phase.STOPPED;
    abandoned = inFlight.size();
    inFlight.clear();
}
// 기다린 시간 0. 남은 것은 그냥 버렸다.
return ShutdownReport.timedOut(0, 0, abandoned, rejected.get());
```

- "틀린 곳이 없다": **예외도 안 나고 로그도 안 남는다.** 코드를 읽어서는 결함을 지목할 수 없다 — 시키는 대로 멈췄을 뿐이다. 사고는 코드가 아니라 **안 한 일**(기다리지 않은 것)에 있다.
- 클라이언트 쪽: **타임아웃이나 연결 끊김**으로만 보인다. 그래서 원인을 서버가 아니라 **네트워크에서** 찾게 된다 — "배포하면 가끔 오류가 난다"로 몇 달을 보내는 이유다.
- 진짜 문제: **버리는 것이 아니라 보고하지 않는 것**이다. 잃은 것을 안 세면 잃는지도 모른다.
- 세는 이유: 즉시 종료를 **관측 가능**하게 만들기 위해서다. 이 클래스도 `abandoned` 는 센다 — 그래서 우아한 종료와의 차이가 "기다림"뿐임이 드러난다.
- 보고 문장: **`0ms 기다렸는데 10건이 남았다`** (ShutdownReport.toString 의 timedOut 형식).

#### 2. TODO 2 — GracefulServer.accept

정답 코드 (impl/GracefulServer.java):

```java
AbruptServer.requireId(requestId);
if (phase != Phase.RUNNING) {
    // DRAINING 이든 STOPPED 든 새 요청은 안 받는다.
    rejected.incrementAndGet();
    return false;
}
if (!inFlight.add(requestId)) {
    throw new IllegalArgumentException("이미 처리 중이다: " + requestId);
}
accepted.incrementAndGet();
return true;
```

- 받으면 안 끝나는 이유: 배수는 `inFlight == 0` 을 기다리는데, 기다리는 동안 계속 받으면 **0 이 되지 않는다.** 바쁜 서비스에서는 **영원히 안 끝난다** — 기한이 있어도 매번 timedOut 으로 끝난다.
- 세는 것: **rejected**(거절 수). 보고에 실려서 "배수 중에 몇 건이 튕겼나" = **로드밸런서에 제때 알렸는가**를 판단하는 근거가 된다.
- 두 번 받으면 던지는 이유: `inFlight` 는 **처리 중인 것을 세는 집합**이다. 중복을 조용히 무시하면 나중에 `complete` 가 한 번만 와서 집합이 어긋나고, **배수가 0 이 되는 시점이 틀어진다.**

#### 3. TODO 3 — GracefulServer.shutdown

정답 코드:

```java
long startedAt = ticker.nowMillis();
int alreadyCompleted;
synchronized (this) {
    // 먼저 막는다. 이 순서가 계약이다.
    phase = Phase.DRAINING;
    alreadyCompleted = (int) completed.get();
}

while (true) {
    long waited = ticker.nowMillis() - startedAt;
    int remaining;
    synchronized (this) { remaining = inFlight.size(); }

    if (remaining == 0) {
        synchronized (this) { phase = Phase.STOPPED; }
        return ShutdownReport.clean(waited,
                (int) completed.get() - alreadyCompleted, rejected.get());
    }
    if (waited >= timeoutMillis) {          // 이상이다. 초과면 주기만큼 더 기다린다
        int abandoned;
        synchronized (this) {
            phase = Phase.STOPPED;
            abandoned = inFlight.size();
            inFlight.clear();
        }
        // 버리는 것은 같은데 몇 개를 버렸는지 아는 것이 다르다.
        return ShutdownReport.timedOut(waited,
                (int) completed.get() - alreadyCompleted, abandoned, rejected.get());
    }
    ticker.sleep(pollMillis);
}
```

- 한 단계로 하면: **새 요청을 막는 것**과 **하던 일을 끝내는 것**이 섞인다 — 그러면 **둘 중 하나를 반드시 잘못한다**(안 막고 기다리거나, 막으면서 하던 일도 버리거나).
- 막는 것이 먼저인 이유: 안 막고 기다리면 **기다리는 동안 계속 들어와 처리 중인 것이 0 이 되지 않는다.**
- 기한이 없으면: 하나가 안 끝날 때 **영원히 기다린다** → 오케스트레이터가 **SIGKILL** 을 보내고, 그때는 **보고할 기회도 없이** 죽는다.
- `>` 로 쓰면: 기한에 정확히 도달한 순간에 안 끝내고 **확인 주기(pollMillis)만큼 더 기다린다** — 기한이 기한이 아니게 된다.
- 누적 보고의 손실: 종료와 상관없는 숫자가 되어 **기한이 맞는지 판단할 근거가 사라진다**(평소 처리량이 섞인다). 그래서 종료 시작 시점의 **`completed` 누적값을 기억해 두고**(`alreadyCompleted`) 보고할 때 빼준다.
- 즉시 종료와의 같음/다름: 버리는 것은 **같다.** 다른 것은 **몇 개를 버렸는지 아는 것**(`abandoned` 를 세어 timedOut 으로 보고).
- `ticker.sleep` 인 이유: 시간을 주입받았기 때문이다 — 테스트가 **10초를 실제로 안 기다린다.** 그리고 "시계를 주입하기로 한 이상 **일도 시계에 태워야** 한다"(README 생각해볼 것 7).
- 두 종료 조건: **① 남은 것이 0 인가**(→ clean) **② 기다린 시간이 기한 이상인가**(→ timedOut). **0 인지를 먼저 본다** — 기한에 딱 맞춰 다 끝났으면 clean 이어야지 실패로 보고하면 안 된다.

#### 4. TODO 4 — GracefulServer.isHealthy

정답 코드:

```java
return phase == Phase.RUNNING;
```

- 안 알리면: 로드밸런서가 **계속 요청을 보내고 그 요청들이 전부 거절된다.** 서버는 우아하게 종료했는데 **사용자는 오류를 본다.**
- 그림:
  ```text
  안 알리면:                              알리면:
  LB ──요청──> [DRAINING] → 전부 거절       LB: isHealthy()=false 를 보고
  사용자가 오류를 본다                      트래픽을 다른 서버로 뺀다
  ```
- 판정식: **`phase == Phase.RUNNING`** — DRAINING 도 STOPPED 도 건강하지 않다.

### B. 개념

#### 5. 잃은 것을 세는 것

- 지표: **배포 직후 오류율**로만 나타난다. 서버에는 아무 흔적이 없으니 **원인을 엉뚱한 데서 찾게 된다**(네트워크·클라이언트).
- clean / timedOut 을 나누는 이유: **깨끗하게 끝났는지가 이 record 의 요점**이다 — 시간 안에 못 끝낸 일이 있으면 그것을 숨기면 안 된다.
- 숨기면: **배포할 때마다 조용히 요청이 사라지고 아무도 그것을 모른다.**

#### 6. 기한을 얼마로 잡나

- 손실(README 실측, 요청 500ms): 기한 **100ms → 3건** / **400ms → 3건** / **600ms → 0건**.
- 평균으로 잡으면: **절반이 잘린다**(평균보다 오래 걸리는 요청이 절반이니까). 400ms 에서도 3건을 그대로 잃는 것이 그 증거다.
- 기준: **"제일 오래 걸리는 요청"** — 최악 케이스보다 길게 잡아야 0 이 된다.
- 기한 0: **안 기다린다** = 즉시 종료와 같다. 다른 것은 **세어서 보고한다**는 점뿐이다.

#### 7. 한계

- 시작점: 이 상자는 **"신호를 받았다"부터** 시작한다. 실제로는 **그 앞이 더 자주 문제**다.
- 신호를 못 받는 경우 셋: ① **SIGTERM 핸들러를 안 걸었다** ② **컨테이너가 PID 1 이라 기본 핸들러가 없다** ③ **프로세스 매니저가 SIGKILL 을 먼저 보낸다.** 그러면 아무리 잘 만든 `shutdown` 도 안 불리고, **증상이 즉시 종료와 똑같다.**
- 30초 배치: **어떤 기한으로도 못 지킨다** — 기한을 30초로 잡으면 배포가 30초씩 멈추고, 짧게 잡으면 그 배치를 잃는다.
- 한 문장: **우아한 종료는 짧은 요청을 지키는 것이지 긴 작업을 지키는 것이 아니다.**
- 긴 작업: **07번 아웃박스처럼 저장해두고 따로 도는 구조로 옮겨야 한다** — 요청 처리 안에 두지 않는다.

#### 8. 만들면서 배운 것

- 안 잡힌 변종: `complete` 의 **`notifyAll`** 이다. 이 구현의 대기 루프는 `wait` 가 아니라 **주기적으로 확인하는 방식(폴링)**이라 **부를 사람이 없었다** — 즉 **죽은 코드**였고, 없애도 아무 테스트가 안 깨진다.
- 대신 한 일: **그 줄을 지웠다.** 근거는 "안 쓰는 장치를 두면 읽는 사람이 **'누군가 wait 하고 있다'고 잘못 읽는다**" — 테스트를 억지로 만드는 것보다 오해의 씨앗을 없애는 쪽이 낫다.
- 가짜 시계 + 실제 스레드: **시계가 순식간에 감기는 동안 스레드가 못 따라와서 결과가 매번 달랐다**(플레이키 테스트).
- 규칙: **시계를 주입하기로 한 이상 일도 시계에 태워야 한다** — 그래서 `shutdown` 이 `ticker.sleep` 으로 기다리고, 테스트는 시계만 감으면 된다.

#### 9. 연결

- 마지막인 이유: **앞의 열여덟 상자가 만든 것들이 종료 순간에 어떻게 무너지는지**가 이 상자의 내용이기 때문이다 — 다른 모든 패턴의 전제(프로세스가 하던 일을 끝낸다)를 다룬다.
- 무력해지는 이유: **재시도도 아웃박스도 사가도, 프로세스가 하던 일을 버리고 죽으면 소용이 없다.** 그 장치들은 전부 "살아서 다음 단계를 밟는 것"을 전제로 한다.
- 07번의 보완: 긴 작업을 **요청 처리 안이 아니라 DB(아웃박스)에 저장**해두면, 프로세스가 죽어도 상태가 남고 다음 프로세스가 이어서 한다 — 종료 기한 안에 끝낼 필요 자체가 없어진다.
- 결론 한 문장: **실패는 없앨 수 없고, 무엇을 잃을지 고를 수 있을 뿐이다. 그리고 고르지 않으면 제일 나쁜 것을 잃는다 — 대개 조용히.**

## 근거

- 기준 소스: `/home/jun/project/myway/ops-patterns/19-graceful-shutdown/impl/AbruptServer.java`, `impl/GracefulServer.java`
- TODO 없는 조각: `src/main/java/com/ops/shutdown/Phase.java`, `ShutdownReport.java`(clean/timedOut), `Ticker.java`
- 문제 원문: `src/main/java/com/ops/shutdown/` 의 TODO 1~4, `README.md` "특히 생각해볼 것" 1~7
- 테스트: `src/test/java/com/ops/shutdown/ShutdownTest.java`, `FakeTicker.java`, `ScriptedTicker.java`

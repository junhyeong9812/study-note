# reliability/14-graceful-shutdown — 우아한 종료: SIGTERM → 준비 해제 → 드레이닝 → 종료 — 정리 (힌트)

## 해결하는 문제

배포·축소·노드 교체 때마다 프로세스는 꺼진다.\
끄는 방법을 정하지 않으면 그때 처리 중이던 요청이 사라지고, 사용자는 502나 연결 끊김을 본다.

```text
 즉시 종료                                 우아한 종료
 SIGTERM ─> 프로세스 사라짐                 SIGTERM ─> 준비 해제 ─> 전파 대기 ─> 드레이닝 ─> 정리 ─> 종료
 처리 중 요청: 끊김                          처리 중 요청: 끝까지 응답
 그 뒤 요청: 아직 오는데 받을 곳이 없음        그 뒤 요청: 로드밸런서가 다른 인스턴스로 보냄
```

- *우아한 종료(graceful shutdown)*: 새 일을 받지 않고, 하던 일을 기한 안에 끝내고, 자원을 정리한 뒤 끝내는 종료.
- *드레이닝(draining)*: 새 요청은 막고 처리 중인 요청이 빠져나가기를 기다리는 단계.

쉬운 예: 가게 마감이다.
- 간판 불을 끈다(준비 해제).
- 지나가던 손님이 불 꺼진 것을 알아챌 때까지 잠깐 문을 열어 둔다(전파 대기).
- 안의 손님이 식사를 마칠 때까지 기다린다(드레이닝). 마감 시각이 되면 정리한다(기한).

똑같은 구조다.\
실무 예: 쿠버네티스 롤링 배포에서 파드 하나가 내려갈 때, 오토스케일러가 인스턴스를 줄일 때, 큐 컨슈머가 재배포될 때.

기초는 원본 두 곳에 있다.
- [ops-patterns/19-graceful-shutdown](../../ops-patterns/19-graceful-shutdown/2-summary.md) 「동작·원리」: RUNNING → DRAINING → STOPPED 상태 기계, 기한(이상 비교), 버린 건수 보고.
- [systems/server-design/02-request-path.md](../../systems/server-design/02-request-path.md) 「Graceful Shutdown」 절: readiness false → LB 인지 대기 → 드레이닝 → 정리 → 종료의 다섯 단계와 `preStop` 예.

이 노트는 그 위에 네 가지를 더한다.
1. 쿠버네티스에서 실제로 무엇이 **동시에** 일어나나.
2. 신호가 앱에 **도착하지 않는** 경우(PID 1).
3. keep-alive 연결 때문에 드레이닝이 **끝나지 않는** 경우.
4. 이것을 일회용 컨테이너로 재현한 실험.

## 동작·원리

### 1. 쿠버네티스 파드 종료 — 두 갈래가 동시에 간다

```text
 kubectl delete / 롤링 배포
        │
        ├──────────────── (갈래 A: 트래픽 쪽) ───────────────────────────────┐
        │   컨트롤 플레인이 EndpointSlice에서 이 파드를 terminating·ready=false로 표시
        │   → kube-proxy·인그레스·외부 LB가 각자 주기로 이 변경을 받아 반영 (수 초 걸릴 수 있음)
        │
        └──────────────── (갈래 B: 프로세스 쪽) ──────────────────────────────┐
            preStop 훅 실행 (있으면)                                           │
            → 컨테이너 PID 1에 SIGTERM                                        │
            → 앱: 드레이닝                                                    │
            → 유예 시간(terminationGracePeriodSeconds, 기본 30초) 끝 → SIGKILL │
```

- 쿠버네티스 문서 "Pod Lifecycle — Termination of Pods"의 순서다.
  - kubelet이 종료를 시작하는 **것과 같은 때에** 컨트롤 플레인이 EndpointSlice에서 파드를 빼는 일을 평가한다("At the same time as the kubelet is starting graceful shutdown").
  - 종료 중인 엔드포인트는 `ready=false`로 노출된다. 그래서 LB가 일반 트래픽을 보내지 않게 된다.
  - 기본 유예 시간은 30초다. `preStop`이 유예 시간을 다 쓰면 kubelet은 2초를 한 번 더 준다.
  - 유예 시간 안에는 `preStop` 시간도 들어간다.
- 문제는 두 갈래가 **서로를 기다리지 않는다**는 점이다.
  - 갈래 B가 빠르면 앱은 이미 닫혔는데 LB는 아직 이 파드로 보낸다. 사용자는 502를 본다.
  - 그래서 `preStop`에서 잠깐 기다리거나, 앱이 SIGTERM을 받고 바로 닫지 않고 전파 시간만큼 버틴다.
  - *전파 대기*: "나 내려간다"를 알린 뒤 상대가 알아챌 때까지 기다리는 시간. 정확한 값은 LB·kube-proxy의 반영 주기에 달렸다.

### 2. 단계별 책임 — 누가 무엇을 하나

```text
 계층              하는 일                                    빠지면
 ───────────────────────────────────────────────────────────────────────────────
 OS·컨테이너        SIGTERM을 PID 1에 보낸다, 기한 뒤 SIGKILL     ─
 PID 1             신호를 받아 앱에 닿게 한다                     신호가 앱에 안 감 → 유예 끝까지 대기 → SIGKILL(137)
 런타임(JVM)        SIGTERM에 종료 훅(shutdown hook)을 돌린다       훅이 없으면 바로 종료(143)
 서버(앱)           준비 해제 → 전파 대기 → 새 요청 거절 → 드레이닝    처리 중 요청이 끊김
 오케스트레이터·LB   준비 안 된 인스턴스를 트래픽에서 뺀다             닫힌 인스턴스로 계속 보냄 → 502
```

- *SIGTERM / SIGKILL*: "정리하고 끝내라" / "즉시 죽어라"는 신호. SIGKILL은 잡을 수 없다. 기초는 [os/06-signals](../../os/06-signals/2-summary.md).
- *종료 코드 143 / 137*: 128 + 신호 번호. 143 = SIGTERM(15)으로 끝남, 137 = SIGKILL(9)로 끝남.
- *PID 1*: 컨테이너 안의 첫 프로세스. 핸들러를 걸지 않은 신호는 받지 않는다(조상 네임스페이스에서 온 SIGKILL·SIGSTOP 제외 — pid_namespaces(7)).
  - Dockerfile의 셸 형식 `CMD java -jar app.jar`는 `/bin/sh -c "java -jar app.jar"`로 실행된다. 셸이 그대로 PID 1로 남으면 앱은 `docker stop`의 SIGTERM을 받지 못한다. Docker 문서도 셸 형식 ENTRYPOINT에 대해 같은 말을 적는다(Dockerfile reference).
  - 셸이 PID 1로 남는지는 셸에 달렸다. 명령이 하나뿐이면 bash는 그 명령을 exec로 바꿔 앱이 PID 1이 된다. eclipse-temurin:21-jdk(Ubuntu, `/bin/sh` = dash 0.5.12)에서는 `sh -c "sleep 30"`의 PID 1이 `sh`로 남았고, 같은 이미지의 `bash -c "sleep 30"`은 PID 1이 `sleep`이었다(점검 확인, 2026-10-01). 그래서 `/proc/1/cmdline`으로 직접 확인한다.
- *종료 훅(shutdown hook)*: JVM이 SIGTERM 등으로 끝날 때 실행하는 스레드. `Runtime.addShutdownHook`으로 건다.

### 3. 드레이닝의 함정 — 연결은 남아 있다

```text
 리스닝 소켓을 닫음 = "새 연결"만 막음
 ┌─ 클라이언트 ─┐  keep-alive 연결 #1 ──────> [서버: 드레이닝 중]  ← 이 연결로 새 요청이 계속 들어온다
 │              │  keep-alive 연결 #2 ──────>                     
 └──────────────┘  새 연결 시도 ───X (거절)
```

- *keep-alive(지속 연결)*: 요청마다 연결을 새로 맺지 않고 한 TCP 연결을 여러 요청에 재사용하는 것. 기초는 [network/35-http-connection-management](../../network/35-http-connection-management/2-summary.md).
- 리스닝 소켓만 닫으면 이미 열린 연결은 계속 요청을 실어 온다.
  - 아래 실험에서 JDK 21 `HttpServer.stop()`이 드레이닝 중에 기존 연결로 새 요청 38~39건을 더 받았다.
  - API 문서는 `stop()`이 "disallowing any new exchanges from being processed"라고 적는다. 그러나 이 실험(eclipse-temurin:21-jdk, 21.0.12)에서는 기존 keep-alive 연결의 새 요청이 처리됐다. 문서 문장만 믿지 말고 쓰는 서버에서 잰다.
  - 트래픽이 계속 오면 "처리 중 0"이 오지 않는다. 드레이닝은 기한까지 간다.
- 대처는 드레이닝 중 응답에 `Connection: close`(HTTP/1.1)를 붙이거나 HTTP/2 GOAWAY를 보내 클라이언트가 연결을 버리게 하는 것이다.
  - 단, 버린 클라이언트가 갈 **다른 인스턴스**가 있어야 한다. LB에서 빠진 뒤라야 의미가 있다.

### 실험: 종료 방식별로 잃는 요청 수

- 서버: JDK 21 `com.sun.net.httpserver.HttpServer`, `/work`가 800ms 걸린다. 일회용 컨테이너 `sn-rl-w14-srv`.
- 클라이언트: 다른 컨테이너에서 100ms마다 요청 하나를 7초 동안 보낸다(약 70건, 동시에 약 8건이 처리 중). JDK `HttpClient`(HTTP/1.1, 연결 재사용).
- 클라이언트가 요청을 보내기 시작하고 2초 뒤에 호스트에서 `docker stop -t <유예>`를 한다.
- 다섯 가지 경우:
  - `nohook`: 종료 훅 없음.
  - `graceful`: 훅에서 ready=false → 1초 전파 대기(예시) → `server.stop(5)`.
  - `graceful3`: 같은데 드레이닝 기한 3초.
  - `gracefulclose`: `graceful` + 드레이닝 중 응답에 `Connection: close`.
  - `pid1sh`: `graceful`과 같은 앱을 `sh -c "java ...; echo ..."`로 띄움(셸이 PID 1).

종료 훅의 핵심 부분:

```java
Runtime.getRuntime().addShutdownHook(new Thread(() -> {
    ready = false;                         // 1. 준비 해제 (/ready가 503을 준다)
    sleep(1000);                           // 2. LB 전파 대기 (예시 1초)
    draining = true;
    server.stop(Integer.getInteger("drain", 5)); // 3. 리스닝 소켓 닫고 최대 N초 드레이닝
    log("stop 반환: 처리 중 " + inFlight.get() + ", 드레이닝 중 새로 받은 요청 " + acceptedWhileDraining.get());
}));
```

(실험, eclipse-temurin:21-jdk 컨테이너 2개, 각 `--cpus=2`, Docker 브리지 네트워크, 2026-10-01 — 경우마다 2회 실행, 수치는 2회 범위. 아래는 실행 로그의 발췌다)

```text
=== nohook 6 #1
[host] docker stop -t 6 소요 0.4s, 종료 코드 143
[cli] 보낸 요청 70 → {ClosedChannelException()=10, ConnectException(HTTP connect timed out)=46, HTTP 200=14}
=== graceful 6 #1
[host] docker stop -t 6 소요 6.0s, 종료 코드 143
[srv t=11216ms] stop 반환: 처리 중 0, 완료 누적 70, 드레이닝 중 새로 받은 요청 39
[cli] 보낸 요청 70 → {HTTP 200=70}
=== gracefulclose 6 #1
[host] docker stop -t 6 소요 2.6s, 종료 코드 143
[srv t= 8185ms] stop 반환: 처리 중 0, 완료 누적 35, 드레이닝 중 새로 받은 요청 4
[cli] 보낸 요청 69 → {ClosedChannelException()=9, ConnectException(HTTP connect timed out)=25, HTTP 200=35}
=== pid1sh 3 #1
[host] docker stop -t 3 소요 3.4s, 종료 코드 137
[cli] 보낸 요청 69 → {ClosedChannelException()=9, ConnectException(HTTP connect timed out)=17, HTTP 200=43}
=== nohook 6 #2
[host] docker stop -t 6 소요 0.4s, 종료 코드 143
[cli] 보낸 요청 69 → {ClosedChannelException()=10, ConnectException(HTTP connect timed out)=46, HTTP 200=13}
=== graceful 6 #2
[host] docker stop -t 6 소요 6.0s, 종료 코드 143
[srv t=11385ms] stop 반환: 처리 중 0, 완료 누적 69, 드레이닝 중 새로 받은 요청 38
[cli] 보낸 요청 69 → {HTTP 200=69}
```

드레이닝 기한을 3초로 줄인 경우(1회):

```text
[host] docker stop -t 6 소요 4.4s, 종료 코드 143
[srv t= 5899ms] SIGTERM 수신: ready=false, 처리 중 8
[srv t= 6901ms] 전파 대기 끝: 리스닝 소켓 닫고 드레이닝, 처리 중 8
[srv t= 9922ms] stop 반환: 처리 중 7, 완료 누적 53, 드레이닝 중 새로 받은 요청 29
[cli] 보낸 요청 69 → {ClosedChannelException()=9, ConnectException(HTTP connect timed out)=7, HTTP 200=53}
```

| 경우 | stop 소요·종료 코드 | 실패 / 보낸 요청 | 무엇을 보였나 |
|---|---|---|---|
| nohook | 0.4~0.6초, 143 | 55~56 / 69~70 | 훅이 없으면 SIGTERM에 JVM이 바로 끝난다 |
| graceful(기한 5초) | 6.0~6.5초, 143 | 0 / 69~70 | 처리 중이던 요청을 다 끝냈다. 그런데 드레이닝 중 기존 연결로 38~39건을 더 받았다 |
| graceful3(기한 3초) | 4.4~4.5초, 143 | 16 / 69 | 트래픽이 계속 와서 기한에 처리 중 7~8건이 남았다 |
| gracefulclose | 2.5~2.7초, 143 | 34~35 / 69 | 연결을 끊어 주자 드레이닝은 빨리 끝났다. 그러나 클라이언트가 갈 다른 인스턴스가 없다 |
| pid1sh(유예 3초) | 3.4~3.6초, **137** | 25~26 / 69~70 | 셸이 PID 1이라 java에 SIGTERM이 가지 않았다. 유예 끝에 SIGKILL |

- 표의 범위는 집필 때 실행(위 로그)과 점검 때 다시 돌린 2회(같은 코드·같은 제한, 2026-10-01)를 합친 것이다. 시간·실패 수는 실행마다 조금씩 다르다.

- 관찰 1 — `nohook`: 같은 앱인데 훅만 없으니 0.4~0.6초 만에 끝나고 55~56건이 실패했다. 이 실험엔 LB가 없다. 그래서 컨테이너가 사라진 뒤의 요청도 갈 곳 없이 연결 타임아웃(2초)으로 실패했다.
- 관찰 2 — `graceful`: 실패 0. 다만 `stop()` 로그를 보면 드레이닝 중에 **새 요청 38~39건**을 기존 keep-alive 연결로 받았다. 드레이닝은 기한(5초) 가까이 이어졌고, 그사이 클라이언트가 보내기를 멈춰 처리 중이 0이 됐다. 기한을 3초로 줄이면 위 3초 실험처럼 처리 중 요청이 남는다.
  - 점검 재실행의 서버 로그로 보면 SIGTERM 수신에서 `stop()` 반환까지 약 5.6초였다. `docker stop -t 6`의 유예 6초 바로 앞이다. 기한이 조금만 길었으면 SIGKILL(137)로 끝났을 것이다(해석).
- 관찰 3 — `graceful3`: 같은 상황에서 기한을 줄이니 기한 시점에 처리 중 7~8건이 남았고, 그것들이 끊겼다. "처리 중 0을 기다린다"는 트래픽이 빠져야 성립한다.
- 관찰 4 — `pid1sh`: 서버 로그에 `SIGTERM 수신` 줄이 **없다**. 훅이 있어도 신호가 오지 않으면 소용없다. `docker stop`은 유예 3초를 다 기다리고 SIGKILL했다(종료 코드 137).
- 관찰 5 — JDK `HttpClient`는 연결 거절도 `ClosedChannelException`으로 보고했다. 같은 상황을 raw 소켓으로 보면 `Connection refused`다([50번 실험](../50-sidecar-ambassador-and-service-mesh/2-summary.md)에서 확인). 그래서 표의 실패 수는 "끊긴 요청 + 거절된 연결"의 합이다. 둘을 이 실험에서 따로 세지는 않았다.
- 해석: 실험의 실패 대부분은 **LB가 없어서** 생겼다. 우아한 종료는 앱 혼자 완성할 수 없다. 앱의 드레이닝과 LB의 제외가 짝을 이뤄야 한다.

## 쓰이는 자료구조·알고리즘

- **상태 기계** — RUNNING → (준비 해제) → DRAINING → STOPPED. 원본 [ops-patterns/19](../../ops-patterns/19-graceful-shutdown/2-summary.md)의 세 상태에 "준비 해제·전파 대기"가 앞에 붙는다.
- **진행 중 요청 카운터** — 요청 시작에 +1, 끝에 −1 하는 원자 카운터(`AtomicInteger`·`LongAdder`). 드레이닝은 "이 값이 0이 되거나 기한이 될 때까지 기다리기"다.
  - 카운터를 지표로 내보내면 "종료 직전 처리 중 몇 건이었나"를 볼 수 있다([16-metrics-and-golden-signals](../16-metrics-and-golden-signals/2-summary.md)).
- **기한(deadline)** — 드레이닝 기한 ≤ 오케스트레이터 유예 시간 − 전파 대기 − 정리 시간. 기한은 "지금부터 N초"가 아니라 종료 시작 시각 + N으로 정한다.
- **열린 연결 집합** — 서버가 연결 목록을 들고 있어야 드레이닝 중 유휴 연결을 닫고, 응답 뒤 `Connection: close`를 붙일 수 있다.
- **신호 → 플래그 전달** — 신호 핸들러는 플래그만 세우고 실제 일은 일반 스레드가 한다([os/06-signals](../../os/06-signals/2-summary.md) 「적용」 1).

## 적용 — 풀어나가는 법

### 1. 순서를 고정한다

```text
 0) 신호가 앱에 닿는지 확인 (exec 형식 CMD, 또는 tini 같은 init)
 1) SIGTERM 수신 → readiness = false
 2) 전파 대기 (LB·kube-proxy 반영 시간, 예: 5~15초 — 환경에서 잰다)
 3) 새 연결 거절 + 기존 연결엔 Connection: close / GOAWAY
 4) 진행 중 요청이 0 또는 기한까지 대기
 5) 큐 컨슈머 중지·오프셋 커밋, 커넥션 풀·스레드 풀 닫기
 6) 종료 — 기한에 걸려 버린 수를 로그·지표로 남긴다
 조건: (2) + (4) + (5) < 유예 시간(terminationGracePeriodSeconds)
```

### 2. Spring Boot

- Spring Boot 3.4부터 `server.shutdown`의 기본값이 `graceful`이다. 3.3까지는 `immediate`였다(ServerProperties 소스 v3.3.0 `Shutdown.IMMEDIATE` → v3.4.0 `Shutdown.GRACEFUL`).
- 드레이닝 기한은 `spring.lifecycle.timeout-per-shutdown-phase`, 기본 30초다(LifecycleProperties 소스 v3.4.0).
- 문서는 Jetty·Reactor Netty·Tomcat이 드레이닝 중 "네트워크 계층에서" 새 요청을 막는다고 적는다. 지속 연결이 이 동작을 바꿀 수 있다고도 적는다(Spring Boot 문서 "Graceful Shutdown").
- 쿠버네티스 유예 기본값(30초)과 Spring 기한 기본값(30초)이 같다. 전파 대기를 앞에 두면 합이 30초를 넘는다. 유예 시간을 늘리거나 기한을 줄인다.

```yaml
# application.yaml (Spring Boot 3.4+)
server:
  shutdown: graceful          # 3.4+ 기본값. 3.3 이하는 명시해야 한다
spring:
  lifecycle:
    timeout-per-shutdown-phase: 20s
```

```yaml
# Pod 명세 (개념 예)
spec:
  terminationGracePeriodSeconds: 45     # 전파 대기 10 + 드레이닝 20 + 정리·여유 15
  containers:
  - name: app
    lifecycle:
      preStop:
        sleep: { seconds: 10 }          # kubelet이 실행하는 sleep 핸들러
    readinessProbe:
      httpGet: { path: /actuator/health/readiness, port: 8080 }
```

- `preStop.sleep`은 기능 게이트 `PodLifecycleSleepAction`으로 1.29 알파, 1.30 베타(기본 켜짐), 1.34 안정이다(kubernetes/website feature-gates 문서). 그보다 오래된 클러스터면 `exec: ["sh","-c","sleep 10"]`을 쓴다. 이미지에 `sh`가 있어야 한다.

### 3. 순수 Java — 진행 중 카운터와 기한

```java
final class Drainer {
    private final AtomicInteger inFlight = new AtomicInteger();
    private volatile boolean accepting = true;

    boolean tryEnter() {                    // 요청 시작
        if (!accepting) return false;       // 드레이닝 중이면 503 + Connection: close
        inFlight.incrementAndGet();
        if (!accepting) { inFlight.decrementAndGet(); return false; } // 경합 보정
        return true;
    }
    void exit() { inFlight.decrementAndGet(); }

    // deadlineNanos: SIGTERM을 받은 순간 정한 절대 기한
    //   예) sigtermAt + (유예 − 정리 − 여유). 전파 대기에 쓴 시간도 여기서 빠진다
    int drain(long deadlineNanos) throws InterruptedException {
        accepting = false;
        while (inFlight.get() > 0 && System.nanoTime() < deadlineNanos) Thread.sleep(50);
        return inFlight.get();              // 버린 건수 — 로그·지표로 남긴다
    }
}
```

- 위 실험 코드의 `server.stop(5)`는 "전파 대기 뒤부터 5초"라는 상대 기한이다. 그래서 SIGTERM부터 재면 최대 약 6초(1 + 5, 점검 실측 5.6초)가 되어 유예 6초에 바짝 붙었다(관찰 2). 위 `Drainer`는 그 대신 절대 기한을 인자로 받는다.

### 4. 진단 명령

```bash
# 컨테이너의 PID 1이 무엇인가 — sh면 신호가 앱에 안 갈 수 있다
docker exec <c> cat /proc/1/cmdline | tr '\0' ' '; echo
docker inspect -f '{{.Config.Entrypoint}} {{.Config.Cmd}}' <c>
# 종료 코드: 143 = SIGTERM으로 정상 처리, 137 = SIGKILL(유예 초과 또는 OOM)
docker inspect -f '{{.State.ExitCode}} OOMKilled={{.State.OOMKilled}}' <c>
# 종료 중인 파드의 엔드포인트 상태 (ready=false, terminating=true)
kubectl get endpointslices -l kubernetes.io/service-name=<svc> -o yaml | grep -A3 conditions
# 드레이닝 중에도 남아 있는 연결
ss -tan state established '( sport = :8080 )' | wc -l
```

## 장애 시나리오와 대처

### 1. 배포 때마다 502가 몇 초간 튄다 (LB 해제 전 종료)

- 현상: 롤링 배포 구간에만 5xx가 짧게 오른다. 앱 로그에는 오류가 없다.
- 보이는 형태: 인그레스·LB 로그에 `502`·`upstream connect error`·`connection refused`. 시각이 각 파드의 종료 시각과 겹친다.
- 원인: 갈래 A(EndpointSlice → LB 반영)가 끝나기 전에 갈래 B(SIGTERM → 앱 종료)가 끝났다. 쿠버네티스는 두 갈래를 서로 기다리게 하지 않는다.
- 대처: `preStop` sleep이나 앱 안의 전파 대기를 둔다. LB 헬스체크 주기 × 실패 임계보다 길게 잡는다. 유예 시간에 그만큼 더한다.

### 2. `docker stop`·파드 종료가 매번 유예 시간을 꽉 채우고 137로 끝난다

- 현상: 종료에 매번 정확히 10초(Docker 기본) 또는 30초(쿠버네티스 기본)가 걸린다. 종료 훅 로그가 없다.
- 보이는 형태: 종료 코드 137. `OOMKilled=false`. 위 실험 `pid1sh`처럼 서버 로그에 SIGTERM 수신 줄이 없다.
- 원인: 셸 형식 CMD로 `sh`가 PID 1이 되어 SIGTERM을 앱에 넘기지 않았다. 또는 앱이 SIGTERM 핸들러 없이 PID 1이다.
- 대처: exec 형식 `ENTRYPOINT ["java","-jar","app.jar"]`, 셸 스크립트라면 마지막 줄을 `exec java ...`로. 여러 프로세스면 `tini`나 `docker run --init`. 결과는 `/proc/1/cmdline`으로 확인한다.

### 3. 드레이닝이 기한까지 안 끝나고 마지막 요청들이 끊긴다

- 현상: 종료 로그에 "기한 초과, 처리 중 N건"이 매번 찍힌다.
- 보이는 형태: 위 실험 `graceful3`처럼 드레이닝 중에도 새 요청 수가 늘어난다. `ss`로 보면 연결이 그대로다.
- 원인: 리스닝 소켓만 닫았고 keep-alive·HTTP/2 연결은 열려 있다. 그 연결로 새 요청이 계속 들어온다.
- 대처: 드레이닝 중 응답에 `Connection: close`, HTTP/2는 GOAWAY. 유휴 연결은 바로 닫는다. 이것이 의미 있으려면 LB에서 먼저 빠져 있어야 한다(`gracefulclose` 관찰).

### 4. 유예 시간이 드레이닝 기한보다 짧아 보고 없이 죽는다

- 현상: 종료 훅 로그가 중간에 끊긴다. 버린 건수 보고가 없다.
- 보이는 형태: 종료 코드 137. 유예 시간 < 전파 대기 + 드레이닝 기한.
- 원인: 두 기한을 따로 정했다. 예를 들어 Spring 기본 30초 + `preStop` 10초인데 쿠버네티스 유예는 기본 30초다.
- 대처: 유예 시간에서 역산한다. 유예 = 전파 대기 + 드레이닝 기한 + 정리 + 여유.

### 5. 큐 컨슈머·백그라운드 작업이 처리 중이던 메시지를 잃거나 두 번 처리한다

- 현상: 배포 뒤 일부 메시지가 다시 처리되거나 처리 흔적 없이 사라진다.
- 보이는 형태: 같은 메시지 ID로 처리 로그가 두 번. 또는 오프셋은 넘어갔는데 결과가 없다.
- 원인: 종료 훅이 HTTP 서버만 드레이닝하고 컨슈머 폴링 루프와 작업 스레드는 그냥 끊었다. 커밋 시점과 처리 완료 시점이 어긋났다.
- 대처: 종료 순서에 "새 메시지 가져오기 중지 → 처리 중 메시지 완료 → 오프셋 커밋 → 컨슈머 close"를 넣는다. 다시 처리돼도 되게 멱등으로 만든다([13-idempotency](../13-idempotency/2-summary.md), [distributed/18-consumer-failure-handling](../../distributed/18-consumer-failure-handling/2-summary.md)). 기한 안에 못 끝나는 긴 작업은 체크포인트를 둔다([31-batch-job-restart-and-checkpoint](../31-batch-job-restart-and-checkpoint/2-summary.md)).

## 핵심 문장

- 우아한 종료는 준비 해제 → 전파 대기 → 새 요청 거절 → 드레이닝 → 정리 → 종료의 순서다. 앞의 둘을 빼면 앱이 잘 닫혀도 LB가 닫힌 곳으로 보낸다.
- 쿠버네티스는 EndpointSlice 갱신과 SIGTERM을 동시에 시작하고 서로 기다리게 하지 않는다. 그 틈을 `preStop`이나 앱의 전파 대기가 메운다.
- 신호가 앱에 닿지 않으면 종료 훅은 소용없다. 셸이 PID 1이면 SIGTERM이 멈추고, 유예 끝에 SIGKILL(137)이 온다(실험 `pid1sh`).
- 리스닝 소켓을 닫아도 keep-alive 연결로 새 요청이 들어온다. 실험에서 드레이닝 중 38~39건을 더 받았다. 트래픽이 빠지지 않으면 드레이닝은 기한까지 간다.
- 유예 시간 ≥ 전파 대기 + 드레이닝 기한 + 정리. 두 기한을 따로 정하면 짧은 쪽이 이긴다.

## 관련 주제·근거

- 선행
  - [os/06-signals](../../os/06-signals/2-summary.md) — SIGTERM·SIGKILL, 종료 코드 128+N, PID 1과 핸들러
  - network/46-load-balancers-and-proxies — 노트는 원고 [systems/server-design/02-request-path.md](../../systems/server-design/02-request-path.md)(헬스체크·연결 드레이닝)
  - [network/35-http-connection-management](../../network/35-http-connection-management/2-summary.md) — keep-alive, `Connection: close`
- 원본(이어받음)
  - [ops-patterns/19-graceful-shutdown](../../ops-patterns/19-graceful-shutdown/2-summary.md) — 상태 기계·기한·버린 건수 보고
  - [systems/server-design/02-request-path.md](../../systems/server-design/02-request-path.md) 「Graceful Shutdown」 — LB 전파 대기, `preStop` 예
- 후속·연결
  - [49-steady-state-fail-fast-and-supervision](../49-steady-state-fail-fast-and-supervision/2-summary.md) — 재시작·감독
  - [31-batch-job-restart-and-checkpoint](../31-batch-job-restart-and-checkpoint/2-summary.md) — 배포 SIGTERM과 장시간 잡
  - [50-sidecar-ambassador-and-service-mesh](../50-sidecar-ambassador-and-service-mesh/2-summary.md) — 사이드카 종료 순서
  - [23-deployment-strategies](../23-deployment-strategies/2-summary.md) — 롤링·블루그린·카나리
  - [distributed/18-consumer-failure-handling](../../distributed/18-consumer-failure-handling/2-summary.md) — 컨슈머 재처리
- 문서·소스
  - Kubernetes 문서 "Pod Lifecycle — Termination of Pods"(기본 유예 30초, preStop 2초 연장, EndpointSlice 동시 평가, terminating 엔드포인트 ready=false) <https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-termination>
  - Kubernetes 문서 "Container Lifecycle Hooks"(Sleep 핸들러) <https://kubernetes.io/docs/concepts/containers/container-lifecycle-hooks/>
  - Docker 문서 `docker container stop`(SIGTERM 뒤 유예, Linux 기본 10초) <https://docs.docker.com/reference/cli/docker/container/stop/>, Dockerfile reference(셸 형식 ENTRYPOINT는 신호를 전달하지 않음) <https://docs.docker.com/reference/dockerfile/>
  - pid_namespaces(7) — init 프로세스의 신호 처리 <https://man7.org/linux/man-pages/man7/pid_namespaces.7.html>
  - Spring Boot 문서 "Graceful Shutdown" <https://docs.spring.io/spring-boot/reference/web/graceful-shutdown.html>, 소스 `ServerProperties.java`(v3.3.0 IMMEDIATE, v3.4.0 GRACEFUL), `LifecycleProperties.java`(30초)
  - JDK 21 API `HttpServer.stop(int delay)` — 리스닝 소켓을 닫고 교환이 끝나거나 약 delay초가 지날 때까지 막힌다 <https://docs.oracle.com/en/java/javase/21/docs/api/jdk.httpserver/com/sun/net/httpserver/HttpServer.html>
- 실험 목록
  - E14 종료 방식 5가지(nohook·graceful·graceful3·gracefulclose·pid1sh)의 실패 수 — JDK 21 HttpServer/HttpClient, 컨테이너 2개(`--cpus=2`), `docker stop -t 6`(pid1sh는 3), 코드 `Srv.java`·`Cli.java`·`run.sh`

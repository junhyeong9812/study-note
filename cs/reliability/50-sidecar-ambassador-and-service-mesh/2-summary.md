# reliability/50-sidecar-ambassador-and-service-mesh — 사이드카·앰배서더·서비스 메시·서비스 디스커버리 — 정리 (힌트)

## 해결하는 문제

서비스가 50개이고 언어가 Java·Node·Go 세 가지다.\
서비스마다 재시도·타임아웃·mTLS·지표·트레이스·서비스 찾기가 필요하다. 이것을 어디에 두나?

```text
 (1) 서비스마다 라이브러리로 (Microservice Chassis)       (2) 서비스 옆 프록시로 (Sidecar / 서비스 메시)
 ┌──────────────────────┐                               ┌────────────┐   localhost   ┌──────────┐
 │ 앱 코드                │                               │ 앱 코드     │ ────────────> │ 프록시    │ ──> 다른 서비스
 │ + 재시도·mTLS·지표 라이브러리│  언어마다 따로, 업그레이드는      └────────────┘               │ 재시도·mTLS│
 └──────────────────────┘  서비스마다 재배포                  언어 무관, 프록시만 교체       │ ·지표     │
                                                                                         └──────────┘
```

- *횡단 관심사(cross-cutting concern)*: 업무 로직과 상관없이 여러 서비스가 똑같이 해야 하는 일. 로깅, 지표, 보안, 설정, 헬스체크, 디스커버리, 서킷 브레이커 등(microservices.io "Microservice chassis"의 목록).

쉬운 예: 해외 출장이다.
- 직원마다 현지어·환전·교통을 각자 공부한다(라이브러리).
- 아니면 직원 옆에 통역 겸 비서를 붙인다(사이드카). 직원은 비서에게 한국어로 말하고, 비서가 현지와 통한다.
- 회사가 모든 비서에게 같은 지침을 무전으로 내려보낸다(컨트롤 플레인).

똑같은 구조다.\
실무 예: Istio·Linkerd 서비스 메시, Envoy 사이드카, 로그 수집 사이드카(Fluent Bit), 쿠버네티스 Service(서버 측 디스커버리), Eureka(클라이언트 측 디스커버리).

## 동작·원리

### 1. 사이드카·앰배서더·어댑터 — 한 파드 안의 보조 컨테이너

```text
 파드 (네트워크 네임스페이스·볼륨 공유)
 ┌──────────────────────────────────────────────────────────────┐
 │ [앱] ──쓰기──> /var/log (공유 볼륨) <──읽기── [사이드카: 로그 수집] ──> 로그 저장소
 │ [앱] ──127.0.0.1:6379──> [앰배서더: 샤딩 프록시] ──> 캐시 샤드 1..N
 │ [앱] /metrics(자기 형식) <──── [어댑터: 형식 변환] <── 모니터링 시스템
 └──────────────────────────────────────────────────────────────┘
```

- Burns·Oppenheimer, "Design Patterns for Container-based Distributed Systems"(USENIX HotCloud 2016)가 단일 노드 다중 컨테이너 패턴으로 이 셋을 묶었다.
  - *사이드카(sidecar)*: 주 컨테이너를 **확장·보강**한다. 논문 예: 웹 서버 로그를 모으는 logsaver, git에서 콘텐츠를 주기적으로 받아 오는 동기화 컨테이너.
  - *앰배서더(ambassador)*: 주 컨테이너가 **바깥과 통신하는 것을 대리**한다. 논문 예: twemproxy로 memcache 샤드에 나눠 보내기. 앱은 localhost의 서버 하나에 붙는다고만 생각하면 된다.
  - *어댑터(adapter)*: 주 컨테이너의 출력을 **바깥이 기대하는 형식으로 맞춘다**(예: 지표 형식 통일).
  - 논문의 근거: 같은 기계의 컨테이너는 localhost와 볼륨을 공유할 수 있다.
- Azure Architecture Center의 설명:
  - Sidecar: 보조 기능을 별도 프로세스·컨테이너로 주 앱 옆에 둔다. 언어와 무관하게 쓰고, 가까이 있어 통신 지연이 작다.
  - Ambassador: 클라이언트 옆에 둔 "프로세스 밖 프록시". 지연이 더해지므로 클라이언트 라이브러리가 나은지 따져 보라고 적는다. 재시도를 프록시가 하면 **모든 연산이 멱등이 아닐 때 안전하지 않을 수 있다**고 적는다.

### 2. 서비스 메시 — 데이터 플레인과 컨트롤 플레인

```text
            컨트롤 플레인 (예: istiod)
            설정·라우팅 규칙·인증서를 모든 프록시에 내려보냄 (Envoy는 xDS API로 받음)
               │            │            │
 ┌─────────────▼──┐  ┌──────▼─────────┐  ┌▼───────────────┐
 │ [앱A]→[Envoy]  │──│→[Envoy]→[앱B]  │  │ [앱C]←[Envoy]  │   ← 데이터 플레인: 실제 트래픽이 지나가는 프록시들
 └────────────────┘  └────────────────┘  └────────────────┘
      mTLS로 암호화·상호 인증, 재시도·타임아웃, 지표·트레이스 스팬을 프록시가 만든다
```

- *서비스 메시(service mesh)*: 서비스 간 통신을 맡는 프록시 층. 
- *데이터 플레인(data plane)*: 요청이 실제로 지나가는 프록시들(대개 파드마다 Envoy 사이드카).
- *컨트롤 플레인(control plane)*: 그 프록시들에게 설정·인증서를 나눠 주는 관리 서버.
- *mTLS*: 양쪽이 서로 인증서를 내보이는 TLS. 메시는 인증서 발급·교체를 자동으로 한다([network/32-mtls-and-cert-operations](../../network/32-mtls-and-cert-operations/2-summary.md)).
- 위임되는 것: mTLS, 재시도·타임아웃·서킷 브레이커, 지표·트레이스, 트래픽 분할(카나리).
- 위임할 수 **없는** 것: 업무 의미가 있는 판단. 어떤 연산이 멱등인지, 재시도해도 되는지, 폴백 값이 무엇인지는 앱만 안다.
- 기본값이 바깥에서 붙는다는 점이 함정이다.
  - Istio 문서("Traffic Management"): HTTP 요청의 기본 재시도는 실패 시 **두 번 재시도**다. 재시도 간격(25ms 이상)은 Istio가 정한다.
  - Istio VirtualService 레퍼런스: 지정하지 않았을 때의 메시 전체 기본 정책은 `attempts: 2`, `retryOn: "connect-failure,refused-stream,unavailable,cancelled"`다(MeshConfig `defaultHttpRetryPolicy`로 바꿀 수 있다). 즉 기본으로는 연결 실패·거절된 스트림·gRPC UNAVAILABLE·CANCELLED에서 재시도하고, 일반 HTTP 5xx 응답 전체가 대상은 아니다. 누군가 `retryOn: 5xx`를 넣으면 아래 실험의 모양이 된다.
  - Envoy route `retry_policy.num_retries`는 정책을 둘 때 기본 1이다(Envoy API 문서 route_components).
  - 앱에도 재시도가 있으면 둘이 **곱해진다**(아래 실험).

### 3. Microservice Chassis vs 메시

| | Microservice Chassis(라이브러리) | 서비스 메시(사이드카 프록시) |
|---|---|---|
| 예 | Spring Boot + Spring Cloud, Resilience4j, Micrometer | Istio, Linkerd |
| 언어 | 언어마다 따로 | 언어 무관 |
| 업그레이드 | 서비스마다 다시 빌드·배포 | 프록시만 교체(앱 재빌드 없음) |
| 업무 문맥 | 안다(어느 메서드가 멱등인지, 폴백) | 모른다(HTTP 메서드·상태 코드 수준) |
| 비용 | 앱 프로세스 안 — 홉 추가 없음 | 요청마다 프록시 홉 2번(보내는 쪽·받는 쪽), 파드마다 메모리 |
| 장애 모양 | 라이브러리 버그는 그 서비스만 | 컨트롤 플레인 설정 오류 하나가 전 서비스로 |

- microservices.io "Microservice chassis": 횡단 관심사와 빌드 로직을 처리하는 프레임워크를 서비스 개발의 바탕으로 쓰라고 한다. 서비스 템플릿(복사·붙여 넣기)은 바뀔 때 서비스마다 고쳐야 하는 단점이 있다고 적는다.
- 해석: 둘은 배타적이지 않다. mTLS·기본 관측은 메시에, 업무 의미가 있는 재시도·폴백·멱등 키는 앱(라이브러리)에 두는 분담이 흔하다. 같은 일을 **양쪽에 두지 않는 것**이 핵심이다.

### 4. 서비스 디스커버리 — 인스턴스 주소를 어떻게 아나

```text
 클라이언트 측 디스커버리                         서버 측 디스커버리
 [클라이언트] ─① 목록 조회─> [레지스트리]         [클라이언트] ──> [라우터/LB] ─목록 조회─> [레지스트리]
      └─② 직접 골라 호출──> 인스턴스 B                              └──> 인스턴스 B
 예: Eureka + Ribbon                           예: AWS ELB, 쿠버네티스 Service(kube-proxy)

 등록 방식
 자기 등록: 인스턴스가 시작 때 등록, 종료 때 해제, 주기적으로 갱신(하트비트)
 제3자 등록: 등록기(registrar)가 인스턴스를 지켜보며 대신 등록·해제 (예: Registrator, 쿠버네티스)
```

- microservices.io의 정의:
  - 클라이언트 측: 클라이언트가 레지스트리에 물어 인스턴스 위치를 얻고 직접 고른다. 예로 Netflix Eureka(레지스트리)와 Ribbon(HTTP 클라이언트)을 든다.
  - 서버 측: 클라이언트는 잘 알려진 위치의 라우터(로드밸런서)로 보내고, 라우터가 레지스트리를 보고 넘긴다. AWS ELB는 라우터이자 레지스트리 역할을 한다.
  - 자기 등록: 시작 때 등록하고 종료 때 해제한다. 클라이언트는 보통 등록을 **주기적으로 갱신**해야 레지스트리가 살아 있음을 안다.
  - 제3자 등록: 등록기가 등록·해제한다. 예로 Registrator와 쿠버네티스·Marathon을 든다.
- *레지스트리(registry)*: 서비스 이름 → 인스턴스 주소 목록을 들고 있는 저장소. 보통 **키-값 + TTL 하트비트**다. 하트비트가 TTL 동안 안 오면 빼낸다.
  - 갑자기 죽은 인스턴스는 해제를 못 한다. 그래서 **TTL 동안** 목록에 남는다(아래 실험 2).

### 실험 1: 앱 재시도 × 사이드카 재시도 = 곱셈

- 파드 흉내: Envoy 컨테이너가 네트워크 네임스페이스를 열고, 앱 컨테이너가 `--network container:`로 같은 네임스페이스에 붙어 `127.0.0.1:10000`으로 부른다(사이드카이자 앰배서더).
- Envoy 라우트: `retry_policy { retry_on: "5xx", num_retries: 2 }`, `include_request_attempt_count: true`(백엔드가 받는 요청에 `x-envoy-attempt-count` 헤더).
- 백엔드: 항상 503을 주고 받은 요청마다 번호·앱 시도 번호·Envoy 시도 번호를 찍는다(작은 Test Harness).
- 앱: 실패하면 100ms 쉬고 다시 시도, 최대 N번(첫 시도 포함). 요청에 `x-app-attempt` 헤더.

```yaml
route:
  cluster: backend
  retry_policy:
    retry_on: "5xx"
    num_retries: 2              # 첫 시도 + 재시도 2 = 최대 3번
```

(실험, Envoy 1.35.13(envoyproxy/envoy:v1.35-latest, 받은 뒤 삭제) + JDK 21 앱·백엔드, 각 컨테이너 `--cpus=1`, 2026-10-01 — 결정적)

```text
== 앱 재시도 3 → 백엔드 직접
[backend] 받은 요청 #1 (앱 시도 1, envoy 시도 null)
[backend] 받은 요청 #2 (앱 시도 2, envoy 시도 null)
[backend] 받은 요청 #3 (앱 시도 3, envoy 시도 null)
== 앱 재시도 1 → 사이드카(envoy 재시도 2)
[backend] 받은 요청 #4 (앱 시도 1, envoy 시도 1)
[backend] 받은 요청 #5 (앱 시도 1, envoy 시도 2)
[backend] 받은 요청 #6 (앱 시도 1, envoy 시도 3)
== 앱 재시도 3 → 사이드카(envoy 재시도 2)
[app] 시도 1 → HTTP 503
[app] 시도 2 → HTTP 503
[app] 시도 3 → HTTP 503
[app] 포기
[backend] 받은 요청 #7 (앱 시도 1, envoy 시도 1)
[backend] 받은 요청 #8 (앱 시도 1, envoy 시도 2)
[backend] 받은 요청 #9 (앱 시도 1, envoy 시도 3)
[backend] 받은 요청 #10 (앱 시도 2, envoy 시도 1)
[backend] 받은 요청 #11 (앱 시도 2, envoy 시도 2)
[backend] 받은 요청 #12 (앱 시도 2, envoy 시도 3)
[backend] 받은 요청 #13 (앱 시도 3, envoy 시도 1)
[backend] 받은 요청 #14 (앱 시도 3, envoy 시도 2)
[backend] 받은 요청 #15 (앱 시도 3, envoy 시도 3)
```

- 관찰 1 — 앱 3번 × Envoy 3번 = 백엔드 **9번**. 앱은 "3번 시도했다"고 믿지만 백엔드는 9번 맞았다.
- 관찰 2 — 앱에서는 Envoy 재시도가 보이지 않는다(앱 로그는 503 세 줄뿐). 증폭은 백엔드 쪽 지표로만 보인다.
- 해석: 계층이 하나 더 있으면(게이트웨이 → 사이드카 → 앱 → 사이드카 → 백엔드) 곱이 또 늘어난다. 장애 중인 백엔드에 부하를 몇 배로 얹는 재시도 폭풍이다([06-retry-backoff-jitter](../06-retry-backoff-jitter/2-summary.md)의 계층 재시도).

### 실험 1b: 사이드카가 준비되기 전에 앱이 부르면

- 같은 구성에서 Envoy를 4초 늦게 띄우고(`sleep 4; exec envoy …`) 앱을 바로 실행했다. 같은 네임스페이스에서 raw 소켓으로도 찔러 봤다.

(실험, 같은 환경, 2026-10-01)

```text
== 앱 재시도 3 → 사이드카(envoy 재시도 2)
[app] 시도 1 → ClosedChannelException null
[app] 시도 2 → ClosedChannelException null
[app] 시도 3 → ClosedChannelException null
[app] 포기
```

- 앱은 예외의 **맨 안쪽 원인**만 찍는다(`while (t.getCause() != null) t = t.getCause();`). 그래서 위 `ClosedChannelException`은 원인 체인의 끝이다. 닫힌 localhost 포트로 `send()`를 다시 불러 체인 전체를 찍어 봤다(판정 재실험, eclipse-temurin:21-jdk 21.0.12, `--network none`, 2026-10-02):

```text
[chain] 시도 1: java.net.ConnectException(null) ← cause: java.net.ConnectException(null) ← cause: java.nio.channels.ClosedChannelException(null)
```

raw 소켓 확인(같은 구성을 다시 띄워 Envoy 기동 전에 한 번, 4초 뒤에 한 번):

```text
[probe] 127.0.0.1:10000 → java.net.ConnectException: Connection refused
[probe] 127.0.0.1:10000 연결됨
```

- 관찰: 프록시가 아직 안 떠 있으면 localhost 포트가 닫혀 있다. raw 소켓은 `ConnectException: Connection refused`를 냈다. JDK `HttpClient.send()`도 `java.net.ConnectException`을 던졌지만 메시지가 `null`이었고, 원인 체인 맨 끝이 `ClosedChannelException`이었다(점검 재실행에서도 같았다). 로그에서 "Connection refused" 문자열만 찾으면 HttpClient 쪽 실패를 놓칠 수 있다. 앱 재시도 3번(300ms 남짓)으로는 4초를 못 넘겼다.
- 대처(제품 기능):
  - 쿠버네티스 네이티브 사이드카: `initContainers`에 `restartPolicy: Always`를 둔 컨테이너. 1.28에 처음 들어왔고 1.29부터 기본 활성, **1.33에서 안정(stable)**. 사이드카가 시작됨(started) 상태가 된 뒤 다음 컨테이너가 시작된다. `startupProbe`가 있으면 그것이 성공해야 started다. 파드 종료 때는 주 컨테이너가 다 멈춘 뒤 사이드카를 정의의 역순으로 끝낸다(쿠버네티스 문서 "Sidecar Containers").
  - Istio `holdApplicationUntilProxyStarts`: 프록시가 트래픽을 받을 준비가 될 때까지 앱 시작을 늦춘다. 기본값 `false`(Istio MeshConfig 문서).

### 실험 2: 레지스트리 TTL과 죽은 인스턴스

- 레지스트리 = 인스턴스 → 마지막 하트비트 시각. TTL이 지나면 목록에서 뺀다.
- A·B·C가 1초마다 하트비트. t=2초에 B가 죽는다. `kill`은 해제 없이, `graceful`은 해제하고 끝낸다.
- 클라이언트는 100ms마다 목록에서 라운드로빈으로 골라 부른다. 15초(가상 시간) 동안.

```java
List<String> alive(long now) {
    lastBeat.entrySet().removeIf(e -> now - e.getValue() > ttlMs);   // TTL 지난 항목 제거
    ...
}
```

(실험, JDK 21 단일 프로세스 시뮬레이션, 가상 시계, 2026-10-01 — 결정적)

```text
kill     TTL  3000ms: 호출 151, 연결 거부 7, 마지막 거부 t=4000ms
kill     TTL 10000ms: 호출 151, 연결 거부 30, 마지막 거부 t=10900ms
graceful TTL  3000ms: 호출 151, 연결 거부 0, 마지막 거부 t=-1ms
graceful TTL 10000ms: 호출 151, 연결 거부 0, 마지막 거부 t=-1ms
```

- 관찰 1 — `kill`: B의 마지막 하트비트는 t=1초였다. 목록에서 빠지는 시각은 1초 + TTL이다. 그때까지 B로 간 호출이 실패했다(TTL 3초 → t=4초까지 7건, TTL 10초 → t=10.9초까지 30건).
- 관찰 2 — `graceful`: 종료 전에 해제하면 실패 0. 우아한 종료([14](../14-graceful-shutdown/2-summary.md))의 "준비 해제"가 레지스트리에서는 "해제"다.
- 해석: TTL은 "죽음을 알아채는 시간"과 "잠깐 끊긴 인스턴스를 성급히 빼지 않기" 사이의 절충이다. 클라이언트 쪽에서도 연결 실패한 인스턴스를 잠시 빼는 장치(이상치 감지, 재시도 시 다른 인스턴스)를 둔다.

## 쓰이는 자료구조·알고리즘

- **서비스 레지스트리 = 키-값 + TTL 하트비트** — 키는 서비스/인스턴스, 값은 주소·메타데이터·마지막 하트비트. TTL 만료 = 빼기. etcd lease·Consul TTL check가 같은 모양이다([distributed/12-coordination-and-fencing](../../distributed/12-coordination-and-fencing/2-summary.md)의 lease).
- **프록시 체인** — 요청이 지나가는 프록시 목록. 각 홉의 재시도 횟수를 곱하면 최악 증폭이다: 증폭 = Π(1 + 재시도ᵢ).
- **재시도 예산(토큰 버킷)** — 재시도를 요청의 일정 비율로 제한해 곱셈을 끊는다(Envoy `retry_budget`, gRPC `retryThrottling` — [06](../06-retry-backoff-jitter/2-summary.md)).
- **로드밸런싱** — 라운드로빈·최소 연결·가중치. 실험 2는 라운드로빈.
- **구성 배포(xDS)** — 컨트롤 플레인이 리스너·라우트·클러스터·엔드포인트 설정을 프록시에 스트림으로 내려보낸다. 설정 하나가 전 프록시에 퍼지는 경로이기도 하다.

## 적용 — 풀어나가는 법

### 1. 분담표를 먼저 쓴다 — 같은 일을 두 곳에 두지 않는다

```text
 관심사          앱(라이브러리)                 메시(사이드카)            게이트웨이
 mTLS            ─                             ○                         ○ (외부)
 재시도           업무상 멱등인 호출만, 예산 포함    끔 또는 연결 실패만         끔
 타임아웃          전체 데드라인(남은 시간)          per-try, 앱보다 짧게        전체 상한
 서킷 브레이커     업무 폴백이 있는 곳             이상치 감지(인스턴스 빼기)    ─
 지표·트레이스     업무 지표, 스팬 문맥 전파         RED 지표, 홉 스팬           입구 지표
```

- 재시도는 **한 계층만** 하게 한다. 둘 다 해야 하면 곱이 허용 범위인지 계산하고 재시도 예산을 둔다.
- 타임아웃은 바깥 계층이 안쪽보다 길어야 안쪽 재시도가 의미가 있다([07-timeout-taxonomy-by-layer](../07-timeout-taxonomy-by-layer/2-summary.md)).

### 2. Istio에서 메시 재시도를 명시한다

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata: { name: payments }
spec:
  hosts: [payments]
  http:
  - route: [{ destination: { host: payments } }]
    timeout: 2s
    retries:
      attempts: 0            # 앱이 재시도하므로 메시 재시도는 끈다. 0이면 재시도 비활성(최대 요청 수 = 1 + attempts)
```

- 근거: Istio VirtualService 레퍼런스 `HTTPRetry.attempts`("If 0, retries will be disabled. The maximum possible number of requests made will be 1 + attempts"). 2026-10-01 latest 문서 기준이며, 쓰는 Istio 버전의 문서로 다시 확인한다.

### 3. 자기 등록 + 해제 + 하트비트 (Java 개념 예)

```java
final class SelfRegistration implements AutoCloseable {
    private final RegistryClient registry; private final Instance me;
    private final ScheduledExecutorService ses = Executors.newSingleThreadScheduledExecutor();

    SelfRegistration(RegistryClient registry, Instance me, Duration ttl) {
        this.registry = registry; this.me = me;
        registry.register(me, ttl);                                     // 준비가 끝난 뒤 등록
        long period = ttl.toMillis() / 3;                               // TTL 안에 하트비트 3번
        ses.scheduleAtFixedRate(() -> registry.heartbeat(me), period, period, TimeUnit.MILLISECONDS);
    }
    @Override public void close() {                                     // 종료 훅에서 먼저 부른다
        ses.shutdownNow();
        registry.deregister(me);                                        // 해제 → 클라이언트가 바로 뺀다
    }
}
```

### 4. 진단

```bash
# Envoy 관리 인터페이스(사이드카 안, 127.0.0.1:9901)
curl -s 127.0.0.1:9901/stats | grep -E 'upstream_rq_retry|upstream_rq_5xx|upstream_cx_connect_fail'
curl -s 127.0.0.1:9901/clusters | grep -E 'health_flags|cx_active'
curl -s 127.0.0.1:9901/config_dump | head        # 지금 프록시가 받은 설정
# Istio
istioctl proxy-config routes <pod> -o json | grep -A5 retryPolicy
istioctl analyze                                  # 설정 오류 정적 검사
# 쿠버네티스 서버 측 디스커버리: 서비스 뒤의 엔드포인트와 준비 상태
kubectl get endpointslices -l kubernetes.io/service-name=<svc> -o wide
```

- 증폭 확인: 백엔드가 받은 요청 수 ÷ 클라이언트가 보낸 논리 요청 수. 1보다 크게 튀는 구간이 재시도 증폭이다.

## 장애 시나리오와 대처

### 1. 앱 재시도 + 메시 재시도 → 곱셈 증폭

- 현상: 하류 서비스가 잠깐 느려졌는데 그 서비스의 요청량이 몇 배로 뛰고 회복이 늦어진다.
- 보이는 형태: 하류가 받은 요청 수가 상류가 보낸 요청 수의 수 배. Envoy `upstream_rq_retry` 증가. 실험 1처럼 `x-envoy-attempt-count`가 1·2·3으로 반복.
- 원인: 앱(3번) × 사이드카(3번) = 9번. 메시의 재시도 설정(기본값 또는 누가 넣은 `retryOn: 5xx`)을 모른 채 앱에도 재시도를 넣었다. Istio 기본값만으로도 연결 실패에서는 앱 재시도 × 3이 된다.
- 대처: 분담표로 재시도를 한 계층에만. 메시 재시도를 명시적으로 끄거나 앱 재시도를 뺀다. 재시도 예산으로 상한을 둔다. 비멱등 호출은 어느 계층도 맹목적으로 재시도하지 않는다.

### 2. 사이드카 준비 전 앱 시작 → 기동 직후 연결 실패

- 현상: 배포 직후 각 파드의 첫 몇 초 동안 외부 호출이 실패한다. 앱이 기동 시 설정·DB를 못 읽고 죽었다 재시작한다.
- 보이는 형태: localhost 프록시 포트로 `ConnectException`(raw 소켓은 `Connection refused`, JDK `HttpClient`는 메시지 `null` + 원인 `ClosedChannelException`). 실험 1b처럼 프록시가 뜨기 전 시도 전부 실패.
- 원인: 파드 안 컨테이너 시작 순서가 보장되지 않았다(일반 컨테이너끼리).
- 대처: 쿠버네티스 네이티브 사이드카(1.29부터 기본 활성, 1.33 stable — `initContainers` + `restartPolicy: Always` + `startupProbe`), Istio `holdApplicationUntilProxyStarts: true`. 앱도 기동 시 의존성 호출에 짧은 재시도를 둔다.

### 3. 레지스트리에 죽은 인스턴스 잔존 → 간헐적 연결 거부

- 현상: 인스턴스가 하나 죽은 뒤 몇 초~몇십 초 동안 요청의 1/N이 실패한다. 저절로 낫는다.
- 보이는 형태: 특정 주소로만 `Connection refused`·연결 타임아웃. 실패가 TTL 길이만큼 이어진다(실험 2: TTL 10초 → 30건).
- 원인: 갑자기 죽어 해제하지 못했다. 레지스트리는 TTL이 지나야 뺀다. 클라이언트 쪽 캐시가 있으면 더 길다.
- 대처: 우아한 종료에서 먼저 해제(실험 2 `graceful`: 0건). TTL·하트비트 주기를 줄인다(오탐과 절충). 클라이언트·프록시의 이상치 감지와 "재시도는 다른 인스턴스로".

### 4. 메시 설정 오류 하나가 전 서비스 장애

- 현상: 설정 하나를 배포한 직후 여러 서비스가 동시에 503·연결 실패.
- 보이는 형태: 서로 무관한 서비스들의 오류가 같은 시각에 오른다. 프록시 로그에 라우트 없음·인증서 검증 실패. 컨트롤 플레인 배포 이력과 시각이 겹친다.
- 원인: 컨트롤 플레인은 설정을 **모든** 프록시에 내려보낸다. 라우팅·mTLS 정책·기본 재시도의 오류는 폭발 반경이 메시 전체다.
- 대처: 메시 설정도 코드처럼 리뷰·정적 검사(`istioctl analyze`)·단계적 배포(네임스페이스·일부 워크로드부터). 되돌리기 절차를 미리 둔다. 셀 단위로 메시를 나눠 반경을 줄인다([51-cells-stamps-and-blast-radius](../51-cells-stamps-and-blast-radius/2-summary.md)).

### 5. 종료 때 사이드카가 먼저 내려가 진행 중 요청 실패

- 현상: 배포 중 파드가 끝나는 몇 초 동안 그 파드가 보낸 외부 호출이 실패한다.
- 보이는 형태: 앱은 드레이닝 중인데 localhost 프록시 연결이 거부된다.
- 원인: 일반 컨테이너로 둔 사이드카는 주 컨테이너와 같은 때 SIGTERM을 받고 먼저 끝날 수 있다(쿠버네티스 문서: 컨테이너는 임의 순서로 TERM을 받는다).
- 대처: 네이티브 사이드카는 주 컨테이너가 멈춘 뒤 끝난다. 그 전 버전에서는 사이드카 `preStop`으로 늦춘다([14-graceful-shutdown](../14-graceful-shutdown/2-summary.md)).

## 핵심 문장

- 사이드카는 주 컨테이너를 보강하고, 앰배서더는 바깥 통신을 대리하고, 어댑터는 출력 형식을 맞춘다. 셋 다 같은 파드의 localhost·볼륨 공유에 기댄다.
- 서비스 메시는 데이터 플레인(프록시)과 컨트롤 플레인(설정·인증서 배포)으로 나뉜다. mTLS·관측은 잘 위임되지만, 무엇이 멱등이고 재시도해도 되는지는 앱만 안다.
- 재시도는 계층마다 곱해진다. 실험에서 앱 3번 × Envoy 3번 = 백엔드 9번이었고, 앱 로그에는 3번만 보였다.
- 사이드카가 늦게 뜨면 localhost가 닫혀 있다(실험 1b). 쿠버네티스 네이티브 사이드카(1.29 기본 활성, 1.33 stable)나 Istio의 시작 대기로 순서를 보장한다.
- 레지스트리는 TTL로 죽음을 안다. 갑자기 죽은 인스턴스는 TTL 동안 남아 호출을 실패시킨다(실험 2). 종료 전에 먼저 해제한다.

## 관련 주제·근거

- 선행
  - [network/46-load-balancers-and-proxies](../../network/46-load-balancers-and-proxies/2-summary.md)
  - [os/28-containers-namespaces-cgroups](../../os/28-containers-namespaces-cgroups/2-summary.md) — 네트워크 네임스페이스 공유
  - [06-retry-backoff-jitter](../06-retry-backoff-jitter/2-summary.md) — 계층 재시도·재시도 예산
- 연결
  - [14-graceful-shutdown](../14-graceful-shutdown/2-summary.md) — 해제·드레이닝·종료 순서
  - [07-timeout-taxonomy-by-layer](../07-timeout-taxonomy-by-layer/2-summary.md) — 계층별 타임아웃
  - [network/32-mtls-and-cert-operations](../../network/32-mtls-and-cert-operations/2-summary.md) — mTLS
  - [network/27-dns-resolution](../../network/27-dns-resolution/2-summary.md) — DNS 기반 디스커버리
  - [distributed/12-coordination-and-fencing](../../distributed/12-coordination-and-fencing/2-summary.md) — lease·TTL
  - [17-distributed-tracing](../17-distributed-tracing/2-summary.md) — 프록시가 만드는 스팬과 문맥 전파
- 논문·문서
  - Burns, Oppenheimer, "Design Patterns for Container-based Distributed Systems", USENIX HotCloud 2016 — Sidecar·Ambassador·Adapter <https://www.usenix.org/conference/hotcloud16/workshop-program/presentation/burns>
  - Azure Architecture Center "Sidecar pattern", "Ambassador pattern" <https://learn.microsoft.com/en-us/azure/architecture/patterns/sidecar>, <https://learn.microsoft.com/en-us/azure/architecture/patterns/ambassador>
  - microservices.io "Client-side service discovery", "Server-side service discovery", "Self Registration", "3rd Party Registration", "Microservice chassis" <https://microservices.io/patterns/>
  - Kubernetes 문서 "Sidecar Containers"(1.28 도입·1.29 기본 활성·1.33 stable, 시작·종료 순서) <https://kubernetes.io/docs/concepts/workloads/pods/sidecar-containers/>
  - Istio 문서 "Traffic Management"(기본 재시도 두 번, 25ms+ 간격) <https://istio.io/latest/docs/concepts/traffic-management/>, VirtualService 레퍼런스(기본 정책 attempts 2·retryOn 목록, attempts 0 = 비활성) <https://istio.io/latest/docs/reference/config/networking/virtual-service/>, MeshConfig `holdApplicationUntilProxyStarts`(기본 false) <https://istio.io/latest/docs/reference/config/istio.mesh.v1alpha1/>
  - Envoy API `config.route.v3.RetryPolicy`(`num_retries` 기본 1), `VirtualHost.include_request_attempt_count` <https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/route/v3/route_components.proto>
- 실험 목록
  - E50a 앱 재시도 × Envoy 재시도 곱셈 — Envoy 1.35.13 + JDK 21, 컨테이너 3개(네트워크 네임스페이스 공유), 코드 `envoy.yaml`·`Backend.java`·`App.java`·`run.sh`
  - E50b 사이드카 4초 지연 기동 → 앱 연결 실패, raw 소켓 확인 — 같은 환경, `DELAY=4`, `Probe.java`
  - E50c 레지스트리 TTL과 죽은 인스턴스(kill vs graceful, TTL 3초·10초) — JDK 21 가상 시계 시뮬레이션, `Registry.java`

# reliability/42-cold-start-and-scale-from-zero — 콜드 스타트: Init 단계·이미지 pull·런타임 시작과 JIT 워밍업·readiness·예열 — 정리 (힌트)

## 해결하는 문제

새 인스턴스는 바로 제 속도를 내지 못한다.\
서버리스 함수의 첫 호출, 오토스케일로 막 뜬 파드, 배포 직후의 JVM은 준비와 워밍업을 하는 동안 느리다. 그 사이 들어온 요청은 느려지거나 타임아웃된다.\
"0대에서 시작(scale from zero)"하는 구성이면 첫 요청이 그 비용을 통째로 낸다.

쉬운 예: 겨울 아침의 자동차다.
- 시동을 거는 데 시간이 든다(프로세스·런타임 시작).
- 시동이 걸려도 엔진이 데워지기 전에는 힘이 안 난다(JIT 워밍업·캐시가 빈 상태).
- 차고에서 차를 꺼내 오는 시간도 있다(이미지 pull·실행 환경 할당).
- 그래서 출근 시각 전에 미리 시동을 걸어 둔다(예열 — provisioned concurrency, 최소 레플리카).

똑같은 구조다.\
실무 예: AWS Lambda의 `Init Duration`, Kubernetes 새 파드의 이미지 pull·startupProbe, 배포 직후 p99 급등, 스냅숏 복원(Lambda SnapStart)과 고유 상태 복제 문제.

## 동작·원리

### 1. 콜드 스타트의 구간

```text
 요청 도착(인스턴스 없음)
   │
   ├─ ① 실행 환경 확보     서버리스: 실행 환경 할당 / K8s: 스케줄 → 노드 할당
   ├─ ② 코드·이미지 가져오기  ZIP·레이어 다운로드·풀기 / 컨테이너 이미지 pull
   ├─ ③ 런타임 시작        JVM·Node·Python 기동, 클래스 로딩·링크
   ├─ ④ 초기화 코드        핸들러 밖의 정적 초기화: 설정 읽기, 클라이언트·커넥션 생성
   │                        ── 여기까지가 Lambda의 Init 단계 ──
   ├─ ⑤ 첫 요청 처리       첫 경로의 클래스 로딩, 람다·문자열 포맷 부트스트랩, 커넥션 지연 생성
   └─ ⑥ 워밍업            인터프리터 → C1 → C2 컴파일, 캐시 채우기, 커넥션 풀 채우기
                            ── 제 속도(steady state)
```

- *콜드 스타트(cold start)*: 실행 환경을 새로 만들어야 하는 호출. Lambda 문서는 코드를 내려받고 환경을 준비하는 앞 두 단계를 흔히 콜드 스타트라고 부르며, 이 시간도 과금되고 호출 지연에 더해진다고 적는다.
  - 반대말 *웜 스타트(warm start)*: 호출이 끝난 실행 환경은 얼려 두었다가(freeze) 같은 함수의 다음 요청에 다시 쓴다.
- Lambda 문서의 Init 단계는 세 작업이다: 확장 시작(Extension init), 런타임 부트스트랩(Runtime init), 함수의 정적 코드 실행(Function init). SnapStart면 before-checkpoint 훅이 더해진다. 코드 내려받기·환경 준비는 그 앞이다(Compute Blog는 이것까지 묶어 INIT duration을 설명한다).
- Lambda 문서(2026-10-01 열람)의 수치
  - 콜드 스타트는 보통 호출의 1% 미만이고, 길이는 100ms 미만부터 1초 넘게까지 다양하다.
  - Init 단계는 10초로 제한된다. 10초 안에 끝나지 않으면 첫 호출 때 함수 타임아웃 설정으로 Init을 다시 시도한다. provisioned concurrency·SnapStart(그리고 Lambda Managed Instances)에는 이 10초 제한이 적용되지 않는다. 같은 문서는 이 경우 초기화 코드가 최대 15분까지 돌 수 있고, 한도는 130초와 함수 타임아웃(최대 900초) 중 큰 쪽이라고 함께 적는다.
  - 성공한 Init은 보통 `INIT_REPORT` 로그를 남기지 않고, `REPORT` 줄의 `Init Duration`으로 보인다. 타임아웃이면 `INIT_REPORT Init Duration: … Phase: init Status: timeout`.
- SRE 책 22장 "Slow Startup and Cold Caching": 프로세스는 시작 직후 안정 상태보다 느리다. 원인으로 필요한 초기화, 첫 요청 때의 백엔드 연결, 그리고 특히 Java의 JIT 컴파일·핫스팟 최적화·지연 클래스 로딩을 든다.

### 2. 쿠버네티스에서의 구간과 readiness

```text
 파드 생성 → 스케줄 → 이미지 pull(없을 때) → 컨테이너 시작 → startupProbe 통과 → readinessProbe 통과 → 서비스 엔드포인트에 들어감
                         ↑ kubelet은 기본적으로                ↑ 통과 전에는 liveness·readiness가 돌지 않는다
                           이미지를 한 번에 하나씩 받는다
```

- 이미지 pull: `imagePullPolicy: IfNotPresent`면 노드에 없을 때만 받는다. kubelet은 기본적으로 이미지를 **직렬로** 받는다(`serializeImagePulls`). 새 노드에서 큰 이미지 여러 개를 받으면 그만큼 기다린다(Kubernetes 문서 "Images").
- *startupProbe*: 느리게 시작하는 컨테이너를 보호한다. `failureThreshold × periodSeconds`를 최악의 시작 시간보다 길게 둔다. 문서 예: 30 × 10 = 300초. 한 번 통과하면 liveness가 이어받고, 끝내 통과 못 하면 300초 뒤 컨테이너를 죽인다.
- *readinessProbe*: 통과해야 트래픽을 받는다. **워밍업이 끝난 뒤에 Ready**가 되도록 설계하지 않으면, 덜 데워진 파드가 트래픽을 받아 p99가 튄다.
  - HPA 문서도 CPU 급증이 끝날 때까지 통과하지 않는 startupProbe, 또는 그 뒤에야 Ready를 알리는 readinessProbe를 권한다([41-autoscaling](../41-autoscaling/2-summary.md)).

### 3. 실험: JVM 시작·첫 요청·워밍업, 그리고 AppCDS·AOT 캐시

- 앱: JDK 내장 `HttpServer`로 만든 작은 서버. 시작 때 XML 설정 파싱·정규식 컴파일 후 `READY <epoch ms>`를 찍는다.
- `/order`: 주문 200건을 만들어 거르고·묶고·정렬해 JSON 문자열로 돌려준다. **서버 안 처리 시간**만 기록해 요청 순번 구간별 중앙값을 낸다(클라이언트 curl의 시간은 빼고).
- 구동: 같은 컨테이너 안에서 `java … ColdApp &` → curl로 첫 성공까지 폴링 → 순차 요청 2,000건.
- 비교: JDK 21 기본 / `-Xint`(JIT 끔) / `-XX:TieredStopAtLevel=1`(C1만) / AppCDS(`-XX:ArchiveClassesAtExit`로 기록 → `-XX:SharedArchiveFile`) / JDK 25 기본 / JDK 25 AOT 캐시(`-XX:AOTCacheOutput`로 기록 → `-XX:AOTCache`). 기록(훈련) 실행은 요청 500건 후 종료.

```bash
# 컨테이너 안 구동 스크립트 핵심(run.sh)
T0=$(( $(date +%s%N) / 1000000 ))
${JAVA:-java} "$@" -cp app.jar ColdApp > /tmp/app.log 2>&1 &
until curl -s -o /dev/null http://127.0.0.1:8080/order; do sleep 0.005; done
T1=$(( $(date +%s%N) / 1000000 ))
for i in $(seq 2 2000); do curl -s -o /dev/null http://127.0.0.1:8080/order; done
```

```java
// 서버 안 처리 시간만 잰다
s.createContext("/order", ex -> {
    long t0 = System.nanoTime();
    String body = handle(times.size());
    times.add(System.nanoTime() - t0);
    ...
});
```

(실험, JDK 21.0.12 / JDK 25.0.4.1 temurin, Docker `--cpus=2`, 같은 컨테이너 안에서 측정, 2026-10-01 — 기본·AppCDS·AOT 캐시는 2회, `-Xint`·C1은 1회. 한 회씩 싣고 범위는 아래 관찰에)

```text
[JDK21 기본] 프로세스 시작→READY 295ms, 시작→첫 응답 556ms
  요청    1~   1번: 서버 처리 중앙값   73.621ms
  요청    2~  10번: 서버 처리 중앙값    3.719ms
  요청   11~ 100번: 서버 처리 중앙값    1.198ms
  요청  101~1000번: 서버 처리 중앙값    0.612ms
  요청 1001~2000번: 서버 처리 중앙값    0.408ms
[JDK21 -Xint(JIT 끔)] 프로세스 시작→READY 245ms, 시작→첫 응답 538ms
  요청    1~   1번: 서버 처리 중앙값   89.566ms
  요청    2~  10번: 서버 처리 중앙값   13.166ms
  요청   11~ 100번: 서버 처리 중앙값   13.268ms
  요청  101~1000번: 서버 처리 중앙값   13.484ms
  요청 1001~2000번: 서버 처리 중앙값   13.421ms
[JDK21 -XX:TieredStopAtLevel=1(C1만)] 프로세스 시작→READY 224ms, 시작→첫 응답 476ms
  요청    1~   1번: 서버 처리 중앙값   79.698ms
  요청    2~  10번: 서버 처리 중앙값    2.365ms
  요청   11~ 100번: 서버 처리 중앙값    1.234ms
  요청  101~1000번: 서버 처리 중앙값    0.815ms
  요청 1001~2000번: 서버 처리 중앙값    0.687ms
[JDK21 AppCDS] 프로세스 시작→READY 205ms, 시작→첫 응답 449ms
  요청    1~   1번: 서버 처리 중앙값   61.810ms
  요청    2~  10번: 서버 처리 중앙값    2.937ms
  요청   11~ 100번: 서버 처리 중앙값    1.083ms
  요청  101~1000번: 서버 처리 중앙값    0.565ms
  요청 1001~2000번: 서버 처리 중앙값    0.403ms
[JDK25 기본] 프로세스 시작→READY 302ms, 시작→첫 응답 575ms
  요청    1~   1번: 서버 처리 중앙값   93.166ms
  요청    2~  10번: 서버 처리 중앙값    4.391ms
  요청   11~ 100번: 서버 처리 중앙값    0.957ms
  요청  101~1000번: 서버 처리 중앙값    0.523ms
  요청 1001~2000번: 서버 처리 중앙값    0.388ms
[JDK25 AOT 캐시] 프로세스 시작→READY 134ms, 시작→첫 응답 307ms
  요청    1~   1번: 서버 처리 중앙값   65.393ms
  요청    2~  10번: 서버 처리 중앙값    2.213ms
  요청   11~ 100번: 서버 처리 중앙값    0.743ms
  요청  101~1000번: 서버 처리 중앙값    0.514ms
  요청 1001~2000번: 서버 처리 중앙값    0.346ms
```

- 관찰 1 — 첫 요청: 기본 설정(JDK 21·25, 각 2회)에서 첫 요청의 서버 처리는 74~93ms, 1,001번째 이후는 약 0.4ms다. 약 180~240배.
  - 사실 점검 재실행(JDK 21 기본 2회, 같은 조건 — 공유 호스트가 더 바빴다): 첫 요청 70·115ms, 1,001번째 이후 0.51·0.55ms. 배수는 약 130~225배로, 실행마다 폭이 크다. 모양(첫 요청 수십~백여 ms → 수 ms → 1ms 미만)은 같다.
- 관찰 2 — 첫 요청 비용의 대부분은 JIT가 아니다. JIT를 끈 `-Xint`에서도 첫 요청은 90ms(사실 점검 재실행 82ms)이고 두 번째부터 약 13~15ms다. 첫 요청에 붙은 약 75ms는 그 경로를 처음 지날 때 드는 일회성 비용이다(클래스 로딩·링크, 람다·`String.format` 부트스트랩 — 해석).
- 관찰 3 — 워밍업은 JIT다. `-Xint`는 끝까지 약 13ms에 머물렀고, 기본 설정은 2~10번 약 3ms → 11~100번 약 1.1ms → 1,001번 이후 약 0.4ms로 내려갔다. C1만 쓰면 0.69ms에서 멈춘다. 마지막 단계의 이득이 C2다(계층 컴파일 — [language/23](../../language/23-jit-tiered-compilation-and-warmup/2-summary.md)).
- 관찰 4 — 시작 시간 단축
  - JDK 21 AppCDS: READY 205·252ms(기본 242·295ms), 첫 응답 432·449ms(기본 512·556ms), 첫 요청 60~62ms(기본 74~79ms). 개선 폭이 작다.
  - 사실 점검 재실행: AppCDS READY 198·222ms(기본 275·285ms), 첫 응답 381·423ms(기본 488·617ms), 첫 요청 66·70ms(기본 70·115ms). 같은 경향이다.
  - JDK 25 AOT 캐시: READY 124·134ms(기본 302·302ms), 첫 응답 307·318ms(기본 538·575ms), 첫 요청 65ms(기본 87~93ms). 2~10번 구간도 1.4~2.2ms(기본 약 4.3ms).
  - JDK 25 AOT 캐시는 클래스를 미리 읽고·파싱하고·로드·링크해 둔다(JEP 483, JDK 24). JDK 25에서는 메서드 프로파일도 담고(JEP 515), `-XX:AOTCacheOutput` 한 번으로 기록과 생성을 한다(JEP 514). JEP 483은 Spring PetClinic 3.2.0 시작이 4.486초 → 2.604초(42%)라고 적는다.
- 관찰 5 — 이 환경에서는 컨테이너 자체를 만드는 데 더 오래 걸렸다. Docker 29.1.3에서 `docker run --rm … true`가 955~1,009ms, `java -version`까지 해도 976~1,021ms였다(3회). 이미 받은 이미지 기준이며 pull 시간은 들어 있지 않다.

### 4. 예열과 스냅숏

```text
 예열(pre-warming)                              스냅숏 복원(snapshot restore)
 ┌ 미리 초기화된 환경 N개 ┐ ← 요청이 바로 쓴다        버전 발행 때 Init 1번 → 메모리·디스크 스냅숏
 └───────────────────────┘                        새 환경 = 스냅숏에서 재개(Restore 단계)
   대가: 놀아도 비용                                 대가: 스냅숏 안의 "고유해야 할 것"이 복제됨
```

- *provisioned concurrency*(Lambda): 미리 초기화된 실행 환경 수. 요청에 바로 응답하도록 준비돼 있고 추가 요금이 든다(Lambda 문서). 설정 수를 넘는 요청은 일반(on-demand) 동시성으로 넘어가 콜드 스타트를 낸다(Application Auto Scaling 절).
- 몇 개를 예열하나 — Little's Law다.
  - Lambda 문서: 동시성 = 평균 초당 요청 × 평균 요청 시간(초). 예: 100 req/s × 0.5초 = 50.
  - 예열 풀이 이 값보다 작으면 넘치는 몫이 콜드 스타트를 낸다. 컨테이너·VM 웜 풀도 같다. 새 인스턴스가 필요한 비율 × 준비 시간 = 준비 중인 인스턴스 수다([math/10-queueing-and-littles-law](../../math/10-queueing-and-littles-law/2-summary.md), [21-scaling-principles](../21-scaling-principles/2-summary.md)).
- *SnapStart*(Lambda): 버전을 발행할 때 Init을 하고, 초기화된 실행 환경의 메모리·디스크를 Firecracker microVM 스냅숏으로 떠서 암호화해 캐시한다. 이후 콜드 호출은 처음부터 초기화하지 않고 스냅숏에서 재개한다(Lambda 문서).
  - 지원 런타임: Java 11 이상, Python 3.12 이상, .NET 8 이상(문서 열람일 기준).
  - after-restore 훅은 10초 안에 끝나야 한다. 아니면 `SnapStartTimeoutException`.
  - **고유성**: 초기화 코드가 만든 고유한 값(고유 ID, 비밀값, 의사 난수의 엔트로피)이 스냅숏에 담기면 여러 실행 환경에서 같은 값이 된다. 고유한 값은 초기화 **뒤에**(핸들러 안 또는 after-restore 훅에서) 만들라고 문서가 적는다.
  - **커넥션**: 초기화 때 연 네트워크 연결의 상태는 재개 뒤 보장되지 않는다. 확인하고 필요하면 다시 연다.

## 쓰이는 자료구조·알고리즘

- **인스턴스 풀(예열 풀)** — 미리 만든 객체를 빌려 주는 풀 패턴의 인프라판. 크기는 Little's Law(동시성 = 도착률 × 체류 시간)로 정한다.
- **계층 컴파일 + 프로파일** — 인터프리터가 호출 횟수·분기 빈도를 세고, 문턱을 넘으면 C1 → C2로 컴파일한다. 실험의 2~10 / 11~100 / 1,001+ 계단이 그 흔적이다. 기초는 [language/23-jit-tiered-compilation-and-warmup](../../language/23-jit-tiered-compilation-and-warmup/2-summary.md).
- **클래스 데이터 공유(CDS)·AOT 캐시** — 클래스 파일을 미리 읽고 파싱한 결과를 파일로 저장해 다음 실행에서 매핑한다(CDS: JEP 310 AppCDS, JEP 350 동적 아카이브). JEP 483 AOT 캐시는 여기에 클래스를 로드·링크한 상태를, JEP 515는 메서드 프로파일을 더한다(JEP 514는 만드는 절차를 줄인다). AOT 네이티브 이미지와의 비교는 [language/24-aot-native-image-and-startup](../../language/24-aot-native-image-and-startup/2-summary.md).
- **스냅숏(체크포인트/복원)** — 프로세스 메모리·디스크 상태를 통째로 저장하고 재개한다. 복원은 복사이므로 "한 번만 만들어야 할 값"이 깨진다.
- **상태 기계** — 컨테이너의 시작 → startup 통과 → ready → (트래픽) 전이. readiness는 이 기계의 "트래픽 받음" 상태로 가는 문이다.

## 적용 — 풀어나가는 법

### 1. 순서

1. **구간을 잰다.** 서버리스는 `REPORT`의 `Init Duration`, K8s는 파드 이벤트(Scheduled·Pulling·Pulled·Started)와 Ready 시각, 앱은 `READY` 로그와 첫 요청 지연. 어느 구간이 긴지부터 안다.
2. **이미지·패키지를 줄인다.** 의존성 정리, 작은 베이스 이미지, 레이어 재사용. 노드에 미리 받아 두기(pre-pull).
3. **초기화를 정리한다.** 매 요청 필요한 클라이언트는 초기화 때 만들고(웜 스타트에서 재사용), 드물게 쓰는 것은 지연 생성. Lambda 문서의 정적 초기화 권고와 같다.
4. **런타임 시작을 줄인다.** JDK 21 AppCDS, JDK 25 AOT 캐시(`-XX:AOTCacheOutput`/`-XX:AOTCache`), 필요하면 네이티브 이미지. 훈련 실행은 운영과 같은 경로를 지나게 한다.
5. **워밍업 뒤에 Ready.** 대표 요청 몇백 건을 자기 자신에게 보내 경로를 데운 뒤 readiness를 통과시킨다. startupProbe는 최악 시작 시간을 덮게.
6. **예열한다.** 최소 레플리카·provisioned concurrency를 Little's Law로 정한다. 정해진 시각의 피크는 그 전에 올린다.
7. **스냅숏을 쓰면 고유성을 점검한다.** 난수 시드·ID·비밀값·커넥션을 복원 뒤에 다시 만든다.

### 2. 워밍업 후 Ready (Java)

```java
/** 시작 → 자기 자신에게 대표 요청을 보내 경로를 데운 뒤에만 Ready를 연다. */
public class Warmup {
    private static final AtomicBoolean READY = new AtomicBoolean(false);

    static void startAndWarm(HttpServer server, int requests) throws Exception {
        server.createContext("/ready", ex -> {
            int code = READY.get() ? 200 : 503;          // readinessProbe가 보는 곳
            ex.sendResponseHeaders(code, -1); ex.close();
        });
        server.start();
        HttpClient c = HttpClient.newHttpClient();
        URI uri = URI.create("http://127.0.0.1:8080/order");
        for (int i = 0; i < requests; i++) {
            c.send(HttpRequest.newBuilder(uri).build(), HttpResponse.BodyHandlers.discarding());
        }
        READY.set(true);                                  // 이제 트래픽을 받는다
    }
}
// 실험 기준으로 약 100건이면 처리 시간이 1ms 근처까지 내려왔다(완전한 C2 수준은 1,000건 이후).
```

- 워밍업 요청은 부작용이 없는 경로로만 보낸다(주문 생성 같은 쓰기 금지).

### 3. 쿠버네티스 설정 예

```yaml
containers:
- name: api
  image: registry.example.com/api@sha256:...     # 다이제스트 고정 — 노드 캐시 재사용
  imagePullPolicy: IfNotPresent
  env:
  - name: JAVA_TOOL_OPTIONS
    value: "-XX:AOTCache=/app/app.aot"            # JDK 25: 빌드 단계에서 훈련 실행으로 만든 캐시
  startupProbe:
    httpGet: { path: /ready, port: 8080 }
    failureThreshold: 30
    periodSeconds: 2                               # 최악 60초까지 시작 허용(예시)
  readinessProbe:
    httpGet: { path: /ready, port: 8080 }
    periodSeconds: 5
```

- AOT 캐시는 훈련 실행과 이후 실행이 같은 JDK 릴리스·같은 하드웨어 아키텍처·OS여야 하고, 클래스패스가 같아야 한다(뒤에 항목을 덧붙이는 것만 허용, JAR만 — 디렉터리 불가). 어기면 HotSpot은 기본적으로 경고를 내고 캐시를 무시한다(JEP 483). 그래서 이미지 빌드 단계에서 만든다.

### 4. 진단

```text
# Lambda — CloudWatch Logs Insights: 콜드 스타트 비율과 Init 시간
filter @type = "REPORT"
| stats count(@initDuration) / count(*) as coldRatio, avg(@initDuration), max(@initDuration) by bin(5m)
```

```bash
kubectl get events --sort-by=.lastTimestamp | grep -E 'Pulling|Pulled|Started'   # pull·시작 시각
kubectl get pod <pod> -o jsonpath='{.status.conditions}'                         # PodScheduled·Initialized·ContainersReady·Ready 시각
```

- `@initDuration`은 Lambda 문서 "Monitoring for Lambda SnapStart"의 Logs Insights 예시 쿼리가 쓰는 필드다(콜드 스타트 호출의 `REPORT` 줄에만 값이 있다). CloudWatch의 "discovered fields" 목록 문서에는 따로 실려 있지 않다.

## 장애 시나리오와 대처

### 1. Init이 길어 첫 요청이 타임아웃 (⚠ Lambda Init Duration 수 초)

- 현상: 한동안 호출이 없던 API의 첫 요청이 API 게이트웨이에서 타임아웃 난다. 다시 부르면 빠르다.
- 보이는 형태: 그 호출의 `REPORT` 줄에 `Init Duration: 수천 ms`. Init이 10초를 넘으면 `INIT_REPORT … Status: timeout`.
- 원인: 큰 패키지·많은 의존성·무거운 정적 초기화(프레임워크 부팅, 원격 설정 조회)와 JVM 시작이 겹쳤다.
- 대처: 패키지 축소, 초기화 지연·정리, SnapStart(Java·Python·.NET), provisioned concurrency(지연 민감 경로). 호출자의 타임아웃이 콜드 스타트를 견디는지도 본다.

### 2. 스케일 아웃된 새 파드가 데워지기 전에 트래픽을 받아 p99 급등 (⚠)

- 현상: 오토스케일이 동작할 때마다, 그리고 배포 직후 몇 분간 p99가 튄다. 평균은 멀쩡하다.
- 보이는 형태: 새 파드의 지연만 높다(파드별 지연 지표). 첫 요청 수십 ms, 이후 수 ms, 몇백~몇천 건 뒤 1ms 미만(실험의 계단). 이미지 pull 이벤트가 길게 찍힌 노드도 있다.
- 원인: readiness가 "포트가 열렸다"만 보고 통과했다. 워밍업과 캐시 채우기가 트래픽을 받으며 일어났다. 이미지 pull이 확장 반응 시간을 늘렸다.
- 대처: 워밍업 후 Ready, LB 슬로 스타트(새 엔드포인트에 트래픽을 천천히 늘림), AOT 캐시·AppCDS, 이미지 축소·pre-pull. 확장 반응 시간이 길면 여유 용량으로 덮는다(41번).

### 3. 스냅숏 복원 뒤 고유 상태가 복제됨 (⚠ SnapStart)

- 현상: 서로 다른 실행 환경에서 같은 "고유" ID·같은 난수열이 나온다. 또는 복원 직후 첫 DB 호출이 끊긴 커넥션으로 실패한다.
- 보이는 형태: 중복 키 오류, 같은 세션 토큰, 재개 직후 커넥션 리셋 오류.
- 원인: 초기화 코드가 만든 ID·시드·비밀값·커넥션이 스냅숏에 담겨 여러 환경으로 복제됐다. Lambda 문서가 이 경우를 직접 경고한다(고유 ID·비밀값·의사 난수 엔트로피, 네트워크 연결 상태).
- 대처: 고유한 값은 핸들러 안이나 after-restore 훅에서 만든다. 커넥션은 복원 뒤 확인·재연결한다. Java용 SnapStart 스캐닝 도구로 점검한다(문서).

### 4. 예열 풀이 작아 피크에 콜드 스타트가 몰림

- 현상: provisioned concurrency를 켰는데도 피크에 지연이 튄다.
- 보이는 형태: 동시 실행 수가 설정값을 넘는 구간에서만 `Init Duration`이 있는 호출이 생긴다.
- 원인: 예열 수 < 피크 동시성. 피크 동시성 = 피크 초당 요청 × 평균 실행 시간(Lambda 문서의 식)인데, 평균 요청 수로 잡았다.
- 대처: 피크 기준으로 다시 계산하고, 정해진 피크는 일정 기반으로 미리 올린다. 짧은 버스트는 평균 기반 알람이 놓칠 수 있다(Lambda 문서: Application Auto Scaling 알람은 기본 평균 통계).

### 5. 콜드 캐시로 재시작 직후 하류가 눌림

- 현상: 전체 재시작 뒤 DB가 과부하로 느려지고, 그 때문에 앱의 워밍업도 더 늦어진다.
- 보이는 형태: 재시작 직후 캐시 적중률 바닥, DB QPS 급등.
- 원인: 모든 인스턴스가 동시에 콜드 캐시로 시작했다. 캐시가 용량 캐시였다([22-capacity-and-load-testing](../22-capacity-and-load-testing/2-summary.md)).
- 대처: 나눠서 재시작, 트래픽을 천천히 올리기(SRE 22장), 캐시를 별도 프로세스로 빼 재시작에도 남기기.

## 핵심 문장

- 콜드 스타트 = 환경 확보 + 코드·이미지 가져오기 + 런타임 시작 + 초기화 + 첫 요청의 일회성 비용 + 워밍업이다. 어느 구간이 긴지 재고 나서 줄인다.
- 실험에서 첫 요청은 안정 상태보다 약 130~240배(실행마다 다름) 느렸고, 그 대부분은 JIT가 아니라 첫 경로의 일회성 비용이었다(`-Xint`도 첫 요청 82~90ms). 그 뒤 수 ms → 1ms 미만으로 내려가는 계단이 JIT 워밍업이다.
- JDK 25 AOT 캐시는 이 앱의 시작→READY를 약 300ms에서 약 130ms로, 첫 응답을 약 550ms에서 약 310ms로 줄였다. JDK 21 AppCDS의 개선은 작았다.
- readiness는 "포트가 열림"이 아니라 "워밍업이 끝남"이어야 한다. 아니면 확장할 때마다 p99가 튄다.
- 예열 수는 Little's Law(동시성 = 초당 요청 × 실행 시간)로 피크 기준으로 정한다. 스냅숏 복원은 빠르지만 고유 값·커넥션을 복원 뒤에 다시 만들어야 한다.

## 관련 주제·근거

- 선행
  - [41-autoscaling](../41-autoscaling/2-summary.md) — 확장 반응 시간의 한 구간이 콜드 스타트
  - [language/24-aot-native-image-and-startup](../../language/24-aot-native-image-and-startup/2-summary.md)
  - [os/28-containers-namespaces-cgroups](../../os/28-containers-namespaces-cgroups/2-summary.md) — 컨테이너 시작의 실체
  - 연결: [language/23-jit-tiered-compilation-and-warmup](../../language/23-jit-tiered-compilation-and-warmup/2-summary.md)
- 후속·연결
  - [22-capacity-and-load-testing](../22-capacity-and-load-testing/2-summary.md) — 콜드 캐시 시나리오
  - [21-scaling-principles](../21-scaling-principles/2-summary.md) — Little's Law
  - [52-reliability-symptom-index](../52-reliability-symptom-index/2-summary.md)의 "배포 직후만 느림"
- 문서
  - AWS Lambda "Understanding the Lambda execution environment lifecycle" — Init 단계 세 작업·10초 제한과 재시도, provisioned concurrency·SnapStart 예외(최대 15분), INIT_REPORT, Restore 단계(10초·SnapStartTimeoutException), Cold starts and latency(1% 미만, 100ms 미만~1초 넘게), freeze·재사용 <https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html>
  - AWS Lambda "Improving startup performance with Lambda SnapStart"(Firecracker microVM 스냅숏, 지원 런타임, 고유성·네트워크 연결 주의, 요금) <https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html> · "Handling uniqueness with Lambda SnapStart" <https://docs.aws.amazon.com/lambda/latest/dg/snapstart-uniqueness.html>
  - AWS Lambda "Understanding Lambda function scaling"(동시성 = 초당 요청 × 요청 시간) <https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html> · "Configuring provisioned concurrency"(추가 요금, 초과분은 표준 동시성, 평균 통계 알람) <https://docs.aws.amazon.com/lambda/latest/dg/provisioned-concurrency.html>
  - AWS Compute Blog, Bhattacharya·Wen, "Understanding and Remediating Cold Starts: An AWS Lambda Perspective", 2025-08-07(Init 구성 요소, 패키징·이미지 크기, provisioned concurrency, SnapStart, INIT duration 지표) <https://aws.amazon.com/blogs/compute/understanding-and-remediating-cold-starts-an-aws-lambda-perspective/>
  - Kubernetes "Liveness, Readiness, and Startup Probes"(startup probe가 성공할 때까지 liveness·readiness를 실행하지 않음) · "Configure Liveness, Readiness and Startup Probes"(startupProbe `failureThreshold × periodSeconds`, 30 × 10 = 300초 예) · "Images"(IfNotPresent, 기본 직렬 pull, `serializeImagePulls`·`maxParallelImagePulls`) · "Horizontal Pod Autoscaling"(Pod readiness and autoscaling metrics)
  - Google SRE 책 22장 "Slow Startup and Cold Caching" <https://sre.google/sre-book/addressing-cascading-failures/>
  - JEP 310(AppCDS, JDK 10), JEP 350(동적 CDS 아카이브, JDK 13), JEP 483(AOT 클래스 로딩·링크, JDK 24 — PetClinic 4.486 → 2.604초), JEP 514(AOT 명령행 간소화 `-XX:AOTCacheOutput`, JDK 25), JEP 515(AOT 메서드 프로파일, JDK 25) <https://openjdk.org/jeps/483>
- 실험 목록
  - E42-A `ColdApp.java` + `run.sh`/`train.sh`: 시작→READY, 시작→첫 응답, 요청 구간별 서버 처리 중앙값 — JDK 21.0.12 기본·`-Xint`·`TieredStopAtLevel=1`·AppCDS, JDK 25.0.4.1 기본·AOT 캐시. Docker `--cpus=2`, 설정마다 2회(`-Xint`·C1은 1회). 사실 점검 재실행: JDK 21 기본 2회·`-Xint` 1회·AppCDS 2회
  - E42-B 컨테이너 생성~종료 시간: `docker run --rm eclipse-temurin:21-jdk true` vs `java -version`, Docker 29.1.3, 3회

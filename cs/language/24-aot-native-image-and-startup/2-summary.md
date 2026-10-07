# language/24-aot-native-image-and-startup — AOT 네이티브 이미지와 시작 시간: 닫힌 세계 가정, 리플렉션 설정, AOT 캐시 — 정리 (힌트)

## 해결하는 문제

JVM은 시작할 때마다 같은 일을 다시 한다.

```text
  java -jar app.jar 의 매번 반복되는 일 (JIT 이전)
  클래스 파일 찾기 → 읽기·파싱 → 로드 → 링크(검증 포함) → 초기화 → 인터프리터로 실행 → JIT 워밍업
  ─────────────────────────────── 앱마다 대부분 같다 ───────────────────────────────

  미리 해 두는 두 방향
  ① JVM은 그대로, 결과만 캐시: CDS·AppCDS(JDK 10+)·AOT 캐시(JDK 24+)     → 같은 JVM, 시작이 빨라짐
  ② JVM 없이 기계어 실행 파일로: GraalVM Native Image(닫힌 세계 AOT)     → 수 ms 시작, 대신 동적 기능 제약
```

- 위 반복은 캐시가 없을 때의 그림이다. JDK 21도 기본 CDS 아카이브(JDK 핵심 클래스 약 1300개 — `java` 도구 문서)를 쓰므로, 그 클래스들은 매번 파싱하지 않는다. 앱 클래스는 매번 위 과정을 거친다.

- *AOT(ahead-of-time) 컴파일*: 실행 전에(빌드 때) 기계어로 컴파일하는 것. JIT의 반대.
- *네이티브 이미지*: Native Image가 만드는 실행 파일. 앱 클래스, 표준 라이브러리 클래스, 언어 런타임, JDK의 정적 링크 네이티브 코드 중 **실행에 필요한 것만** 담는다(GraalVM 문서).

쉬운 예: 이삿짐.
- JVM 방식: 집 전체를 들고 다니다가, 도착할 때마다 필요한 걸 그 자리에서 찾아 꺼낸다.
- 네이티브 이미지: 떠나기 전에 "쓸 물건 목록"을 만들어 그것만 싼다. 도착하면 바로 쓴다.
- 목록에 없던 물건이 필요해지면? 이삿짐에 없다.

똑같은 구조다.\
네이티브 이미지의 장애는 대부분 **"목록에 없던 물건"** — 리플렉션·프록시·리소스처럼 정적 분석이 못 본 것이다.

실무 예:
- 서버리스·스케일 투 제로에서 첫 요청이 시작 시간에 묶인다([reliability/42](../../reliability/42-cold-start-and-scale-from-zero/2-summary.md)).
- JVM에서는 되던 기능이 네이티브 빌드에서만 `ClassNotFoundException`·`NoSuchMethodException`·`MissingReflectionRegistrationError`로 실패한다.
- 네이티브 빌드가 CI에서 수 분·수 GB 메모리를 써서 러너가 OOM으로 죽는다.

## 동작·원리

### 1. 닫힌 세계 가정 — 진입점에서 닿는 것만

```text
  빌드 때 정적 분석 (진입점 main에서 호출 그래프를 넓이 우선으로)
  Main.main ─▶ OrderController.handle ─▶ OrderService.place ─┬▶ Class.forName("JsonCodec")          상수 → 따라감
                                                             └▶ Class.forName(config.get("gateway")) 이름 모름 → 못 따라감
  LegacyReport.render ─▶ PdfWriter                              (아무도 안 부름 → 빠짐)

  이미지 = {Main.main, OrderController.handle, OrderService.place, JsonCodec}
  실행 중 PgPaymentGateway를 찾으면 → 이미지에 없다
```

- GraalVM "Native Image Basics": 도달 가능한 요소만 최종 이미지에 들어간다. 빌드가 끝나면 클래스 로딩 등으로 새 요소를 추가할 수 없다. 이 제약을 *closed-world assumption*이라 부른다.
  - *도달성 분석(reachability analysis)*: 진입점에서 출발해 호출·필드 접근·할당을 따라가며 "실행 중 쓰일 수 있는" 클래스·메서드를 모으는 정적 분석.
- 효과: 안 쓰는 코드가 통째로 빠진다(위 그림의 `LegacyReport`). 링크 단계 데드 코드 제거와 같은 생각이다([25번](../25-lto-pgo-and-binary-size/2-summary.md)).
- 대가: 동적 기능은 분석기에 **알려 줘야** 한다. Spring Boot 문서: GraalVM은 리플렉션·리소스·직렬화·동적 프록시를 직접 알지 못하므로 알려 줘야 한다. 클래스패스는 빌드 때 고정되고, 지연 클래스 로딩이 없다.

### 2. 알려 주는 방법 — 도달성 메타데이터

- 코드 안에서 **상수 인자**로 (GraalVM "Reachability Metadata")
  - `Class.forName("Foo")`처럼 인자가 상수면 빌드 때 값이 계산되어 이미지 힙에 저장된다. `Foo`가 없으면 그 호출은 `throw ClassNotFoundException("Foo")`로 바뀐다.
  - 상수의 범위: 리터럴, 빌드 때 초기화된 static 필드, effectively final 변수, 상수끼리의 단순 계산 등.
- 파일로: `META-INF/native-image/<groupId>/<artifactId>/reachability-metadata.json`
  - 리플렉션으로 꺼낼 타입은 `{ "type": "완전한.클래스.이름" }`, 프록시는 인터페이스 목록으로 적는다.
- 자동 수집: JVM에서 앱을 돌리며 동적 접근을 기록하는 *tracing agent* — `java -agentlib:native-image-agent=config-output-dir=<dir> ...`. 돌린 경로만 기록되므로 테스트·트래픽이 덜 지나간 경로는 빠진다(해석).
- 메타데이터 없이 리플렉션을 부르면 현재 문서 기준 `MissingReflectionRegistrationError`(`java.lang.Error` 하위, 잡지 말라고 적음)가 난다. 문서는 이 동작을 `--exact-reachability-metadata` 모드로 옮겨 가는 중이라고 적는다. 그 이전 기본 모드의 증상(`ClassNotFoundException`·`NoSuchMethodException` 등)은 판에 따라 다를 수 있다 [?].
- Spring Boot는 빌드 때 *Spring AOT* 처리로 빈 정의를 자바 소스로 만들고, `reflect-config.json`·`resource-config.json`·`proxy-config.json` 등 힌트 파일을 생성한다(Spring Boot 문서). 직접 힌트를 더할 수도 있다([software-design/35](../../software-design/35-annotation-and-metadata-programming/2-summary.md)).

### 3. 빌드 때 초기화와 이미지 힙 — 스냅숏

```text
  빌드(JVM 위에서)                              실행(네이티브)
  class Example {                              이미지 힙을 바이너리에서 복사해 시작
    static final String message =               → message 값은 "빌드한 기계의" 시스템 속성 그대로
        System.getProperty("message"); }          (실행 때 -Dmessage=... 를 줘도 이미 정해짐)
  ─ static 초기화가 빌드 때 실행 → 결과를 이미지 힙에 저장
```

- GraalVM Basics: 빌드 때 초기화된 클래스의 static 초기화는 **빌드하는 JVM에서** 실행되고, 그 static 필드 값이 바이너리에 저장된다. 실행 시 처음 써도 초기화가 다시 일어나지 않는다.
  - *이미지 힙*: 빌드 중 만들어져 앱 코드에서 닿을 수 있는 객체, 쓰이는 클래스의 `Class` 객체, 코드에 박힌 상수 객체를 담은 힙. 시작할 때 바이너리에서 복사한다.
- 이것이 "수 ms 시작"의 한 비결이자, **빌드 때 값이 굳는** 함정이다(장애 4).

### 4. JVM을 유지하는 쪽 — CDS에서 AOT 캐시까지

| | 무엇을 미리 | 판 | 비고 |
|---|---|---|---|
| 기본 CDS | JDK 클래스의 파싱 결과 | JDK 기본 아카이브 | `-Xshare:auto`가 기본(java 문서) |
| AppCDS·동적 아카이브 | 앱 클래스까지 | JEP 310(JDK 10)·JEP 350(JDK 13) | `-XX:ArchiveClassesAtExit`로 훈련 실행 |
| AOT 캐시 | 클래스를 **로드·링크된 상태로** | JEP 483(JDK 24) | 훈련 실행 → 캐시 생성 → 운영 실행 |
| + 메서드 프로파일 | JIT 프로파일 | JEP 515(JDK 25) | 시작 직후부터 JIT가 프로파일을 쓴다 |
| + 컴파일된 코드 | 기계어 | JEP 544(열람 시 Targeted, Release 28) | 운영에서 워크로드가 바뀌면 다시 JIT |

- JEP 483의 수치(원문 그대로)
  - Stream API를 쓰는 짧은 프로그램(약 600개 JDK 클래스): JDK 23에서 0.031초 → JDK 24 AOT 캐시로 0.018초(42%), 캐시 11.4MB.
  - Spring PetClinic 3.2.0(시작 시 약 21,000 클래스): 4.486초 → 2.604초(42%), 캐시 130MB.
- 조건(JEP 483): 훈련과 운영이 같은 JDK 릴리스·하드웨어 아키텍처·OS, 일관된 클래스패스(운영은 뒤에 덧붙이기만 가능), **클래스패스에는 JAR만**(디렉터리 불가). 사용자 정의 클래스 로더가 읽은 클래스는 캐시하지 않는다. 캐시를 못 쓰면 경고만 내고 계속 실행한다.
- 네이티브 이미지와 달리 **열린 세계**를 유지한다. 리플렉션·동적 로딩이 그대로 되고, 최고 성능은 여전히 JIT가 낸다.

### 5. 트레이드오프 — 시작 vs 최고 처리량 vs 빌드 비용

```text
                     JVM + JIT            JVM + AOT 캐시        네이티브 이미지
  시작               느림                  덜 느림               가장 빠름(ms)
  워밍업             필요                  줄어듦(JEP 515)        거의 없음(이미 기계어)
  최고 처리량         실행 중 프로파일로 최적  같음                   PGO 없으면 정적 정보로만 최적
  동적 기능           전부                  전부                  메타데이터로 알려 준 것만
  빌드               빠름                  훈련 실행 한 번 추가     수십 초~수 분, 수 GB 메모리
```

- GraalVM PGO 문서: JIT는 실행 중에 프로파일을 모아 최적화하지만, AOT로 컴파일한 앱의 프로파일 수집은 더 번거롭다. 계측(instrumented) 바이너리를 대표 작업으로 돌려 프로파일을 만들고, 그 프로파일로 다시 빌드한다.
  - 같은 문서: AOT 컴파일러는 프로파일이 없으면 보통 코드의 정적 모습만 보고, 그래서 "JIT 컴파일러와 같은 품질의 기계어를 만들기 어렵다". 이것이 "PGO 없는 네이티브 이미지의 최고 처리량이 JIT보다 낮을 수 있다"는 커리큘럼 서술의 근거다. 차이의 크기는 이 노트에서 재지 못했다(Native Image가 이 호스트에 없다).
  - 같은 문서: Native Image PGO는 GraalVM Community Edition에서는 쓸 수 없다.
- 빌드 비용(GraalVM "Native Image Build Output" 문서의 HelloWorld 예시 출력): `Finished generating 'helloworld' in 25.5s`, `Peak RSS: 2.14GiB`, 실행 파일 6.88MiB. 문서 예시의 빌드 기계는 36 프로세서·30GiB 할당이고 디버그 정보도 생성했다 — 기준값이 아니라 한 예시 출력이다.
  - 같은 문서: 컨테이너·CI(`$CI=true`)에서는 기본으로 시스템 메모리의 85%를 쓰는 dedicated 모드를 쓰되 30GiB를 넘지 않는다.

### 실험 1: JDK 21 CDS 세 가지 — 끔 / 기본 / AppCDS

```java
// JEP 483 예제와 같은 모양 — Stream API로 JDK 클래스 수백 개를 읽게 한다
var words = List.of("hello", "fuzzy", "world");
System.out.println(words.stream().filter(w -> !w.contains("z")).collect(Collectors.joining(", ")));
```

```bash
java -XX:ArchiveClassesAtExit=app.jsa -cp app.jar HelloStream    # 훈련 실행 → 동적 아카이브(135,168바이트)
java -Xshare:off                       -cp app.jar HelloStream    # CDS 끔
java                                   -cp app.jar HelloStream    # 기본(JDK 아카이브)
java -XX:SharedArchiveFile=app.jsa     -cp app.jar HelloStream    # AppCDS
```

환경: i7-13700HX, `eclipse-temurin:21-jdk`(21.0.12), `--cpus=2`, 컨테이너 안에서 `java` 프로세스만 10회씩 잼(첫 실행 버림), 2묶음 + 사실 점검 재실행 2묶음.

```text
            프로세스 시작~종료 (ms, 20회)      로드된 클래스   그중 아카이브에서
  off       179 ~ 265                        735             0
  default    89 ~ 160                        702           698
  appcds     84 ~ 146                        632           630

  사실 점검 재실행(2묶음, 20회): off 211~246 / default 91~141 / appcds 97~126 ms, 클래스 수는 위와 같음
```

- CDS를 끄면 시작이 약 2배 느렸다. JDK 클래스 698개를 아카이브에서 바로 가져오는 효과다.
- AppCDS는 앱 클래스·람다 관련 클래스까지 아카이브에서 가져왔다(632개 중 630개). 이 작은 프로그램에서 기본 대비 이득은 실행마다 흔들려 작다(묶음 1: 84~120 vs 99~141, 묶음 2: 95~146 vs 89~160).
- 로드된 클래스가 702 → 632로 준 것은 아카이브에 저장된 람다 관련 클래스를 실행 중에 새로 만들지 않았기 때문으로 본다(해석).
- 처음에 클래스패스를 디렉터리(`-cp out`)로 줬더니 훈련 실행이 `[error][cds] Error: non-empty directory 'out'` → `Cannot have non-empty directory in paths`로 실패했다. JEP 483의 "클래스패스에는 JAR만" 조건과 같은 제약이 JDK 21 동적 아카이브에도 있었다.

### 실험 2: 닫힌 세계 모형 — 호출 그래프 BFS

이 호스트에는 GraalVM Native Image가 없다. 그래서 도달성 분석을 작은 모형으로 흉내 냈다(Java 21, 위 1절 그림의 그래프).

```java
static Set<String> reachable(String entry, Set<String> metadata) {
    Set<String> seen = new LinkedHashSet<>(metadata);       // 메타데이터로 등록한 것은 뿌리로 추가
    Deque<String> q = new ArrayDeque<>(seen);
    if (seen.add(entry)) q.add(entry);
    while (!q.isEmpty()) {
        String m = q.poll();
        for (Edge e : G.getOrDefault(m, List.of())) {
            if (e.reflective() && !e.constantArg()) continue;  // 분석이 이름을 모른다
            if (seen.add(e.to())) q.add(e.to());
        }
    }
    return seen;
}
```

```text
  메타데이터 없음 → 이미지에 든 것: [Main.main, OrderController.handle, OrderService.place, JsonCodec]
    실행: Class.forName("PgPaymentGateway") → ClassNotFoundException (이미지에 없음)
  메타데이터에 PgPaymentGateway 등록 → [PgPaymentGateway, Main.main, PgHttpClient, OrderController.handle, OrderService.place, JsonCodec]
    실행: Class.forName("PgPaymentGateway") 성공
  빠진 코드(죽은 코드 제거 효과): [LegacyReport.render]

  같은 동작을 일반 JVM에서(이름을 환경 변수에서 읽음): JVM: PgPaymentGateway 인스턴스
```

- 메타데이터로 `PgPaymentGateway`를 뿌리에 넣자, 그것이 부르는 `PgHttpClient`까지 따라 들어왔다.
- 이 모형은 원리만 보인다. 실제 Native Image의 분석은 필드·할당·타입 흐름까지 따라가는 더 정교한 분석이고, 오류 종류는 위 2절처럼 모드에 따라 다르다.

## 쓰이는 자료구조·알고리즘

- **도달성 분석 = 그래프 탐색** — 진입점에서 호출 그래프를 BFS(작업 큐 + 방문 집합)로 훑는다. [algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md) · [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md)
- **스냅숏(힙 이미지)** — 빌드 때 객체 그래프를 직렬화해 바이너리에 넣고, 시작할 때 복사한다. 체크포인트/복원과 같은 생각이며 "한 번만 만들어야 할 값이 복제된다"는 함정도 같다([reliability/42](../../reliability/42-cold-start-and-scale-from-zero/2-summary.md) 스냅숏 절).
- **메모리 매핑 아카이브** — CDS·AOT 캐시 파일을 프로세스 주소 공간에 매핑해 파싱·로드 결과를 바로 쓴다([os/14-mmap-and-page-cache](../../os/14-mmap-and-page-cache/2-summary.md)).
- **해시 기반 일관성 검사** — 캐시가 만들어진 JDK·클래스패스와 지금이 같은지 확인한다. 다르면 캐시를 버린다(JEP 483).

## 적용 — 풀어나가는 법

### 1. 무엇을 고르나

```text
  시작 시간이 사업 지표인가? (서버리스, 스케일 투 제로, CLI)
   ├─ 아니오 → JVM 그대로 + 워밍업 후 Ready ([23번](../23-jit-tiered-compilation-and-warmup/2-summary.md))
   └─ 예 → 리플렉션·동적 프록시·런타임 설정 분기를 많이 쓰나?
            ├─ 예 / 모름 → JVM + AppCDS(JDK 21) 또는 AOT 캐시(JDK 24+/25+)부터
            └─ 아니오(또는 프레임워크가 AOT 힌트를 만들어 줌) → 네이티브 이미지 검토
                 → 빌드 시간·메모리, 최고 처리량, 디버깅·관측 도구 차이를 측정으로 확인
```

### 2. JDK 21에서 바로 쓸 수 있는 것 — AppCDS

```bash
# 1) 클래스패스는 JAR로 (비어 있지 않은 디렉터리가 있으면 아카이브 생성이 실패한다 — 실험 1, `java` 도구 문서 CDS 제한)
java -XX:ArchiveClassesAtExit=app.jsa -jar app.jar --warmup-and-exit   # 훈련 실행(예시 플래그)
# 2) 운영
java -XX:SharedArchiveFile=app.jsa -jar app.jar
# 3) 효과 확인: 아카이브에서 온 클래스 수
java -XX:SharedArchiveFile=app.jsa -Xlog:class+load -jar app.jar | grep -c "shared objects file"
```

- JDK·JAR가 바뀌면 아카이브를 다시 만든다. 이미지 빌드 단계에 넣으면 잊지 않는다.

### 3. 네이티브 이미지로 갈 때

1. 테스트·대표 트래픽을 tracing agent와 함께 JVM에서 돌려 메타데이터를 모은다.
2. Spring Boot면 Spring AOT가 만든 힌트를 쓰고, 부족한 것만 직접 더한다.
3. 실행 시 `-XX:MissingRegistrationReportingMode=Warn`으로 누락 위치를 모아 본다(GraalVM 문서 — 정확한 동작은 그 판 문서 확인).
4. **네이티브 바이너리로** 통합 테스트를 돌린다. JVM 테스트 통과는 네이티브 동작을 보장하지 않는다.
5. 빌드 단계의 시간·`Peak RSS`를 CI 지표로 남긴다.

## 장애 시나리오와 대처

### 1. JVM에선 되는데 네이티브에서만 클래스·메서드를 못 찾는다 (⚠)

- **현상**: 특정 기능(플러그인 선택, JSON 역직렬화, 결제 게이트웨이 교체)만 네이티브 빌드에서 실패한다.
- **보이는 형태**: `ClassNotFoundException`, `NoSuchMethodException`, 또는 `MissingReflectionRegistrationError`(현재 GraalVM 문서의 메타데이터 누락 오류).
- **원인**: 이름이 설정·DB·요청에서 오는 리플렉션은 정적 분석이 못 따라간다. 메타데이터에 없으면 그 클래스가 이미지에 빠졌을 수 있고(실험 2 모형), 다른 경로로 들어가 있어도 등록이 없으면 리플렉션 조회가 실패한다(`MissingReflectionRegistrationError` — GraalVM 메타데이터 문서).
- **대처**: `reachability-metadata.json`에 등록, tracing agent로 수집, 가능한 곳은 상수 인자로 바꾸기(`Class.forName("고정 이름")`), 선택지를 `switch`로 명시. 네이티브 통합 테스트에 그 경로를 넣는다.

### 2. 빌드가 수 분 걸리고 수 GB를 쓴다 → CI 러너 OOM (⚠)

- **현상**: 네이티브 빌드 단계만 느리고, 작은 러너에서 프로세스가 죽는다.
- **보이는 형태**: 빌드 출력 끝의 `Peak RSS`, 러너의 OOMKilled(exit 137).
- **원인**: 전체 프로그램 분석 + AOT 컴파일을 한 번에 한다. 문서 예시의 HelloWorld도 25.5초·2.14GiB였다. 컨테이너·CI에서는 기본으로 메모리의 85%(최대 30GiB)를 잡는다.
- **대처**: 네이티브 빌드는 큰 러너·캐시된 단계로 분리, 빌드 메모리 한도를 명시, PR마다가 아니라 릴리스 파이프라인에서만.

### 3. 최고 처리량이 JIT보다 낮다

- **현상**: 시작은 빨라졌는데 부하 테스트 처리량이 JVM 버전보다 낮다.
- **원인(가설)**: AOT는 실행 중 프로파일 없이 빌드 때 정보로 최적화한다. GraalVM PGO 문서도 프로파일 없는 AOT 컴파일러는 JIT와 같은 품질의 코드를 만들기 어렵다고 적는다. JIT의 프로파일 기반 투기적 최적화(타입 프로파일 인라인, [23번](../23-jit-tiered-compilation-and-warmup/2-summary.md))를 그대로 얻지 못한다(차이의 크기는 미측정).
- **대처**: 측정부터. 필요하면 PGO 빌드(계측 바이너리 → 대표 작업 → 재빌드, GraalVM PGO 문서 — Community Edition에는 없다). 오래 도는 처리량 위주 서비스는 JVM + AOT 캐시가 맞을 수 있다.

### 4. 빌드 때 값이 굳었다

- **현상**: 모든 인스턴스가 같은 "시작 시각"·같은 난수 순서를 갖거나, 실행 때 준 설정이 무시된다.
- **원인**: 빌드 때 초기화된 클래스의 static 값은 빌드한 기계의 값으로 이미지 힙에 저장된다(GraalVM Basics의 `System.getProperty` 예).
- **대처**: 환경·시간·난수·비밀값에 의존하는 초기화는 실행 시점 초기화로 둔다. 스냅숏 복원(SnapStart 등)도 같은 문제를 갖는다([reliability/42](../../reliability/42-cold-start-and-scale-from-zero/2-summary.md)).

### 5. 프로필·조건부 빈이 바뀌지 않는다 (Spring)

- **현상**: 네이티브 이미지에 `--spring.profiles.active=prod`를 줬는데 dev 빈 구성이 그대로다.
- **원인**: Spring Boot 문서: 닫힌 세계에서는 애플리케이션의 빈 정의가 실행 중 바뀔 수 없다. `@Profile`·프로필별 설정에 제한이 있고, 빈 생성 여부를 바꾸는 속성(`@ConditionalOnProperty`, `.enabled` 속성)은 지원되지 않는다.
- **대처**: 환경별로 따로 빌드하거나, 빈 구성 분기를 실행 시 값 분기로 바꾼다.

### 6. AOT 캐시·CDS가 조용히 안 쓰인다

- **현상**: AOT 캐시를 붙였는데 시작 시간이 그대로다.
- **원인**: JDK 버전·클래스패스·모듈 옵션이 훈련 때와 다르다. JEP 483: 캐시를 못 쓰면 경고만 내고 계속 실행한다.
- **대처**: 배포 전 검증에서 `-XX:AOTMode=on`으로 위반 시 실패하게 확인한다(JEP 483 — 운영에서는 조심해서 쓰라고 적고, JDK 27에서 `-XX:AOTMode=required`로 바뀌었다는 갱신 메모가 있다). `-Xlog:class+load`의 아카이브 출처 수를 지표로 남긴다.

## 핵심 문장

- 시작 시간을 줄이는 방향은 둘이다. JVM은 두고 클래스 로드·링크·프로파일 결과를 캐시하거나(CDS·AOT 캐시), JVM 없이 미리 기계어로 만들거나(네이티브 이미지).
- 네이티브 이미지는 진입점에서 닿는 것만 담는 닫힌 세계 가정 위에 있다. 정적 분석이 못 보는 리플렉션·프록시·리소스는 메타데이터로 알려 줘야 한다.
- 빌드 때 초기화된 static 값은 이미지 힙에 굳어 실행 때 다시 계산되지 않는다.
- AOT 캐시는 같은 JDK·아키텍처·OS·클래스패스(JAR만)에서만 쓰이고, 어긋나면 경고만 내고 그냥 느리게 돈다.
- 네이티브 이미지는 시작·메모리를 얻는 대신 빌드 비용, 동적 기능, (PGO 없이는) 최고 처리량을 내준다.

## 관련 주제·근거

- 선행
  - [23-jit-tiered-compilation-and-warmup](../23-jit-tiered-compilation-and-warmup/2-summary.md) — JIT·워밍업
  - [os/29-linking-and-loading](../../os/29-linking-and-loading/2-summary.md) — 링커·로더, 정적·동적 링크
- 후속·연결
  - [25-lto-pgo-and-binary-size](../25-lto-pgo-and-binary-size/2-summary.md) — 링크 단계 최적화·PGO·죽은 코드 제거
  - [reliability/42-cold-start-and-scale-from-zero](../../reliability/42-cold-start-and-scale-from-zero/2-summary.md) — 콜드 스타트 측정(JDK 21 AppCDS·JDK 25 AOT 캐시), 스냅숏 복원
  - [software-design/35-annotation-and-metadata-programming](../../software-design/35-annotation-and-metadata-programming/2-summary.md) — 리플렉션·애너테이션과 AOT 힌트
  - [languages/java/syntax/58-reflection](../../../languages/java/syntax/58-reflection/2-summary.md)
  - [algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md) · [os/14-mmap-and-page-cache](../../os/14-mmap-and-page-cache/2-summary.md)
- 근거
  - GraalVM Native Image 레퍼런스 매뉴얼 — 개요(정적 분석 → 컴파일 = build time) <https://www.graalvm.org/latest/reference-manual/native-image/> · Basics(closed-world assumption, 빌드 때 초기화, 이미지 힙) <https://www.graalvm.org/latest/reference-manual/native-image/basics/> · Reachability Metadata(상수 인자, `reachability-metadata.json`, `MissingReflectionRegistrationError`, `--exact-reachability-metadata`) <https://www.graalvm.org/latest/reference-manual/native-image/metadata/> · Collecting Metadata Automatically(tracing agent) <https://www.graalvm.org/latest/reference-manual/native-image/metadata/AutomaticMetadataCollection/> · Build Output(Peak RSS, dedicated 모드 85%·30GiB) <https://www.graalvm.org/latest/reference-manual/native-image/overview/BuildOutput/> · PGO <https://www.graalvm.org/latest/reference-manual/native-image/optimizations-and-performance/PGO/>
  - Spring Boot "Introducing GraalVM Native Images"(JVM과의 차이, 닫힌 세계 제약, Spring AOT 산출물) <https://docs.spring.io/spring-boot/reference/packaging/native-image/introducing-graalvm-native-images.html>
  - JEP 483(JDK 24) <https://openjdk.org/jeps/483> · JEP 515(JDK 25) <https://openjdk.org/jeps/515> · JEP 514(JDK 25) <https://openjdk.org/jeps/514> · JEP 544(열람 시 Targeted, Release 28) <https://openjdk.org/jeps/544> · JEP 310(JDK 10) <https://openjdk.org/jeps/310> · JEP 350(JDK 13) <https://openjdk.org/jeps/350>
  - `java` 도구 문서(JDK 21) — `-Xshare`, `-XX:ArchiveClassesAtExit`, `-XX:SharedArchiveFile`, 기본 CDS 아카이브(핵심 클래스 약 1300개), "Restrictions on Class Path and Module Path"(비어 있지 않은 디렉터리 금지) <https://docs.oracle.com/en/java/javase/21/docs/specs/man/java.html>
- 실험 목록(i7-13700HX, `eclipse-temurin:21-jdk` 21.0.12, `--cpus=2 --network none`)
  - 실험 1: `HelloStream` — CDS 끔 / 기본 / AppCDS(동적 아카이브), 각 10회 × 2묶음(+ 점검 재실행 2묶음), `-Xlog:class+load` 클래스 수. 디렉터리 클래스패스 실패 메시지
  - 실험 2: `ReachModel.java` 호출 그래프 BFS 모형 + `JvmReflect.java`(같은 리플렉션을 일반 JVM에서). Native Image는 이 호스트에 없어 실행하지 않았다

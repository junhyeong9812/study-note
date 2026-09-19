# Spring Boot 3.x (2022 ~)

> 원본: `~/project/java-history/spring/boot-3.x.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·클래스/애너테이션 이름·JDK 버전·코드블록 7개·설정 키는 원문 그대로다.\
> ASCII 도식 3개(그중 2개는 원문의 mermaid 도식을 옮긴 것), 「한눈에」의 규격 교체 비유와 대응표, 용어 블록의 「예:」, 「용어 풀이」는 원문에 없는 보충이다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> Java 17 베이스라인, `javax`→`jakarta` 대전환, 그리고 **GraalVM 네이티브 이미지 1급 지원**. 4년 반 만의 메이저 업그레이드로 Spring을 클라우드 네이티브 시대에 맞춰 다시 정렬했다.

이 편에서 가장 넓게 번진 변화를 비유로 읽으면 **건물의 콘센트 규격을 통째로 바꾸는 공사**다.\
플러그 모양이 바뀌면 벽만 고쳐서는 끝나지 않고, 집 안의 가전을 하나하나 확인해야 한다.\
**`javax` → `jakarta` 전환도 똑같은 구조다** — 원문이 "이는 3.x 마이그레이션에서 가장 광범위한 변화다"라고 적은 자리다.

본문 흐름에 쓰는 비유는 이 규격 교체 하나뿐이고, 3.x의 나머지 축(네이티브 이미지·관측성·가상 스레드)은 비유 없이 원문 문장으로 읽는다.

| 비유 | 실체 |
|------|------|
| 벽의 콘센트 규격을 바꾸는 공사 | 원문 "모든 Java EE API import가 `jakarta.*`로 변경되었다" |
| 그래서 집 안 가전을 전부 확인해야 한다 | 원문 "JPA, 서블릿, Bean Validation, JMS 등을 쓰는 모든 코드와 서드파티 라이브러리가 Jakarta 호환 버전이어야 한다" |
| 규격이 바뀐 이유는 제조사 쪽 사정이다 | 원문 "Oracle이 Java EE를 Eclipse Foundation에 이관하면서, 상표 문제로 패키지 네임스페이스가 `javax.*` → `jakarta.*`로 강제 변경되었다" |

두 세대를 나란히 놓으면 이렇다.

```text
 Boot 2.x (원문이 대비로 적은 쪽)       Boot 3.x (이 편)
 +-------------------------------+     +--------------------------------+
 | import javax.persistence.*    |     | import jakarta.persistence.*   |
 +-------------------------------+     +--------------------------------+
 | Java 8/11 시대                |     | Java 17 LTS(2021)가 새 기준점  |
 +-------------------------------+     +--------------------------------+
```

그림 해설 — 위 행은 원문 코드 블록이 `// Spring Boot 2.x` / `// Spring Boot 3.x` 주석을 달아 나란히 적은 import 두 줄에서 가져왔다.\
아래 행은 원문 한 문장을 좌우로 나눈 것이다 — "Java 8/11 시대에서 **Java 17 LTS**(2021)가 새 기준점이 되었다." 같은 행끼리가 원문이 직접 짝지은 것이다.

## 릴리스 정보
- **최초 출시**: Spring Boot 3.0 GA — 2022년 11월 24일
- **주요 마이너 버전과 시기**:
  - 3.0 (2022-11) — Spring Framework 6, Java 17, Jakarta EE 9, GraalVM 네이티브, 관측성 신규
  - 3.1 (2023-05) — Docker Compose 지원, Testcontainers 통합, Spring Authorization Server 1.1
  - 3.2 (2023-11) — Java 21 지원, **가상 스레드(Virtual Threads)**, `RestClient`/`JdbcClient`, CRaC, Spring Framework 6.1
  - 3.3 (2024-05) — CDS(Class Data Sharing) 통합, Docker Compose에서 Bitnami 이미지 지원, 보안/관측성 개선
  - 3.4 (2024-11) — 구조화된 로깅(structured logging), `RestClient`/`RestTemplate` 클라이언트 자동 설정 확장, 기본 Buildpacks 빌더 변경(Paketo `builder-jammy-java-tiny`)
  - 3.5 (2025-05) — 3.x 후속 라인 (Testcontainers/Docker Compose SSL 구성, 설정/Actuator/빌드 개선)
- **기반 Spring Framework 버전**: Spring Framework 6.x (3.0은 6.0, 3.2는 6.1)
- **최소 자바 버전**: **Java 17** (가상 스레드 등 일부 기능은 Java 21 필요)

> **LTS(Long-Term Support)** — 오래 지원해 주기로 정해 둔 자바 버전. 회사가 기준으로 삼기 좋은 판이다.\
> 예: 원문이 "**Java 17 LTS**(2021)가 새 기준점이 되었다"라고 적은 그 17이 이것이다.

> **최소 자바 버전과 일부 기능의 요구 버전은 다르다** — 원문은 3.x의 바닥을 Java 17로 적고, 괄호로 "가상 스레드 등 일부 기능은 Java 21 필요"라는 단서를 붙인다.\
> 예: Java 17만 있으면 3.x는 돌지만, 뒤에 나오는 `spring.threads.virtual.enabled` 한 줄은 원문 기준 Java 21이 있어야 하는 자리다.

## 시대적 배경 (왜 3.0인가)

2.0 출시(2018) 이후 4년 반, JVM과 클라우드 환경은 다시 한번 크게 바뀌었다.

- **Java LTS의 세대교체**: Java 8/11 시대에서 **Java 17 LTS**(2021)가 새 기준점이 되었다. record, sealed class, 패턴 매칭, `var` 등 현대 문법을 전제할 수 있게 되었다.
- **Java EE → Jakarta EE 전환**: Oracle이 Java EE를 Eclipse Foundation에 이관하면서, 상표 문제로 패키지 네임스페이스가 `javax.*` → `jakarta.*`로 강제 변경되었다. 생태계 전체가 이 전환을 따라야 했다.
- **서버리스/컨테이너 비용 압박**: 빠른 기동과 낮은 메모리 사용이 비용으로 직결되며, **네이티브 이미지(GraalVM)**와 빠른 스타트업이 핵심 경쟁력이 되었다.
- **관측성 표준화**: 메트릭에 더해 **분산 추적(distributed tracing)**까지 표준 요구사항이 되었다.

Spring Boot 3.0은 Spring Framework 6.0을 기반으로 이 변화들을 한꺼번에 흡수했다. 그만큼 **마이그레이션 비용이 큰** 메이저 버전이다.

> **네임스페이스(namespace)** — 이름이 겹치지 않게 앞에 붙여 두는 구역 이름. 자바에서는 `javax.persistence` 같은 패키지 앞부분이 그것이다.\
> 예: 원문이 든 변경이 `javax.*` → `jakarta.*`이고, 원문은 그 이유를 기술적 개선이 아니라 "상표 문제"로 적는다.

> **서버리스(serverless) / 콜드스타트(cold start)** — 요청이 올 때만 인스턴스를 띄워 쓰는 방식 / 그렇게 새로 뜰 때 처음 한 번 걸리는 기동 시간.\
> 예: 원문이 이 압력을 "빠른 기동과 낮은 메모리 사용이 비용으로 직결되며"라고 적는다 — 뜨는 데 걸리는 시간이 곧 돈이 되는 상황이다.

> **분산 추적(distributed tracing)** — 요청 하나가 여러 서비스를 거쳐 가는 길을 이어 붙여 보는 것.\
> 예: 원문은 이것을 "메트릭에 더해" 표준 요구사항이 된 것으로 적는다 — 숫자를 재는 것(메트릭)과는 다른 축이다.

## 핵심 기능

### Java 17 베이스라인
최소 요구 버전이 Java 17로 올라갔다. record를 DTO/설정 객체로, sealed class를 도메인 모델로 자유롭게 쓸 수 있다.

```java
public record UserDto(Long id, String name, String email) {}

@RestController
class UserController {
    @GetMapping("/users/{id}")
    UserDto get(@PathVariable Long id) {
        return new UserDto(id, "Alice", "alice@example.com");
    }
}
```

> **record** — 값을 담기만 하는 클래스를 한 줄로 선언하는 자바 문법.\
> 예: 위 코드의 `public record UserDto(Long id, String name, String email) {}` 한 줄이 그것이고, 원문은 이것의 쓰임을 "DTO/설정 객체로"라고 적는다.

> **DTO(Data Transfer Object)** — 계층 사이에 값만 실어 나르는 객체.\
> 예: 위 코드에서 컨트롤러가 반환하는 `UserDto`가 그 자리다.

### Jakarta EE 9 (`javax` → `jakarta`)
모든 Java EE API import가 `jakarta.*`로 변경되었다. 이는 3.x 마이그레이션에서 가장 광범위한 변화다.

```java
// Spring Boot 2.x
import javax.persistence.Entity;
import javax.servlet.http.HttpServletRequest;
import javax.validation.constraints.NotNull;

// Spring Boot 3.x
import jakarta.persistence.Entity;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.constraints.NotNull;
```

JPA, 서블릿, Bean Validation, JMS 등을 쓰는 모든 코드와 서드파티 라이브러리가 Jakarta 호환 버전이어야 한다.

위 코드에서 바뀐 것은 각 줄 맨 앞의 `javax`가 `jakarta`가 된 것뿐이고, 그 뒤 `persistence.Entity`·`servlet.http.HttpServletRequest`·`validation.constraints.NotNull`은 세 줄 모두 그대로다.\
범위가 넓은 이유는 고칠 자리의 수다 — 원문이 적은 대로 "JPA, 서블릿, Bean Validation, JMS 등을 쓰는 모든 코드와 서드파티 라이브러리"가 그 대상이다.

> **Jakarta EE** — 자바의 기업용 표준 API 묶음. Java EE가 Eclipse Foundation으로 옮겨 가며 얻은 새 이름이다.\
> 예: 원문이 이 절 제목에 붙인 `Jakarta EE 9`가 3.0이 기준으로 삼은 판이고, 위 코드 아래쪽 세 줄이 그 판의 import 모양이다.

### GraalVM 네이티브 이미지 1급 지원 (AOT)
Spring Framework 6의 **AOT(Ahead-of-Time) 처리 엔진**을 내장해, GraalVM Native Image로 OS 네이티브 실행 파일을 빌드할 수 있다. 기동 시간이 수십 밀리초로 줄고 메모리 사용량과 이미지 크기가 크게 감소한다.

```bash
# 네이티브 실행 파일 빌드
mvn -Pnative native:compile

# 또는 네이티브 컨테이너 이미지(Buildpacks)
mvn -Pnative spring-boot:build-image
```

빌드 시점에 빈 구성과 프록시를 미리 계산해 리플렉션/동적 프록시 사용을 최소화한다. 서버리스·콜드스타트 민감 워크로드에 적합하다.

빌드 도구에서 네이티브 실행 파일까지 이어지는 AOT 파이프라인은 다음과 같다.

```text
 Gradle / Maven  -->  Spring AOT 처리          -->  GraalVM native-image  -->  네이티브 실행 파일
                      (빈 구성·프록시 사전 계산)                                  (빠른 시작 · 적은 메모리)
```

빌드 시점에 동적 동작을 정적으로 변환해, 리플렉션을 줄이고 OS 네이티브 바이너리를 만든다.

그림 해설 — 네 칸의 문구와 세 화살표는 원문 도식의 것 그대로다.\
원문이 이 절에서 줄어든다고 적은 것은 **기동 시간·메모리 사용량·이미지 크기** 셋이고, 어울리는 자리로는 "서버리스·콜드스타트 민감 워크로드"를 든다.\
원문이 적은 순서는 "빌드 시점에 빈 구성과 프록시를 미리 계산해 리플렉션/동적 프록시 사용을 최소화한다"이다 — 미리 계산하는 것이 앞이고, 그 결과로 둘의 사용이 줄어든다.

> **AOT(Ahead-of-Time) / 네이티브 이미지** — 실행 전에 미리 컴파일해 두는 것 / 그렇게 만들어 낸, JVM 없이 바로 도는 OS 실행 파일.\
> 예: 위 명령 `mvn -Pnative native:compile`이 그 실행 파일을 만드는 줄이고, 그 앞 단계에서 원문 말대로 "빈 구성과 프록시를 미리 계산"한다.

> **리플렉션(reflection) / 동적 프록시** — 실행 중에 클래스·메서드를 이름으로 찾아 쓰는 기능 / 실행 중에 대역 객체를 만들어 끼우는 기능. 둘 다 실행해 봐야 알 수 있는 동작이다.\
> 예: 원문은 AOT가 "빌드 시점에 빈 구성과 프록시를 미리 계산해" 이 둘의 사용을 "최소화한다"고 적는다.

### 관측성 통합 (Observability — Micrometer Tracing)
2.x의 Micrometer 메트릭에 더해, **Micrometer Observation API**와 **Micrometer Tracing**(구 Spring Cloud Sleuth의 후신)을 통합했다. 하나의 `Observation`으로 메트릭과 트레이스를 함께 생산하며 OpenTelemetry/Zipkin으로 내보낸다.

```java
@Service
class OrderService {
    private final ObservationRegistry registry;

    void place(Order order) {
        Observation.createNotStarted("order.place", registry)
            .observe(() -> process(order)); // 메트릭 + 트레이스 동시 계측
    }
}
```

하나의 Observation이 메트릭과 분산 추적을 함께 만들어 백엔드로 내보내는 흐름은 다음과 같다.

```text
                                        +--> 메트릭            -->  Prometheus 등 메트릭 백엔드
                                        |    (MeterRegistry)
 요청 --> Micrometer Observation API ---+
                                        +--> 분산 추적         -->  OpenTelemetry / Zipkin
                                             (trace / span)
```

단일 계측 지점(Observation)에서 메트릭과 트레이스를 동시에 생산해, Boot 3의 통합 옵저버빌리티를 구현한다.

그림 해설 — 여섯 칸의 문구와 다섯 화살표는 원문 도식의 것 그대로다.\
갈라지는 자리가 하나라는 점이 요점이다 — 원문 코드 주석이 그 자리에 "메트릭 + 트레이스 동시 계측"이라 적어 두었다.

> **트레이스(trace) / 스팬(span)** — 요청 하나가 지나간 길 전체 / 그 길을 이루는 토막 하나.\
> 예: 원문 도식이 "분산 추적"이라는 칸 아래에 이 두 낱말을 `trace / span`으로 나란히 적어 두었다.

> **`Observation`** — 한 번 계측해서 메트릭과 트레이스를 함께 만들어 내는 계측 지점.\
> 예: 위 코드의 `Observation.createNotStarted("order.place", registry).observe(() -> process(order))`가 그 한 지점이고, 원문 주석이 그 줄을 "메트릭 + 트레이스 동시 계측"이라 부른다.

### 가상 스레드 (Virtual Threads, 3.2 / Java 21)
Java 21의 가상 스레드(Project Loom)를 설정 한 줄로 활성화한다. 블로킹 MVC 코드를 거의 그대로 두고도 높은 동시성을 얻을 수 있다.

```properties
spring.threads.virtual.enabled=true
```

> **가상 스레드(virtual thread)** — OS 스레드를 하나씩 붙들지 않고 JVM이 가볍게 관리하는 스레드.\
> 예: 원문이 이 기능에 붙인 설명이 "블로킹 MVC 코드를 거의 그대로 두고도 높은 동시성을 얻을 수 있다"이다 — 켜는 방법으로 든 것은 위 한 줄뿐이다.

### RestClient / JdbcClient (3.2)
`RestTemplate`을 대체하는 현대적 **동기 HTTP 클라이언트** `RestClient`(플루언트 API, WebClient와 유사한 사용감)와, 간결한 `JdbcClient`가 도입되었다. Boot가 `RestClient.Builder`를 자동 구성한다.

```java
RestClient client = RestClient.create();
User user = client.get()
    .uri("https://api.example.com/users/{id}", 1)
    .retrieve()
    .body(User.class);
```

> **플루언트 API(fluent API)** — 점을 찍어 메서드를 이어 붙이며 한 문장처럼 쓰는 호출 방식.\
> 예: 위 코드의 `client.get().uri(...).retrieve().body(User.class)`가 그 사슬이다.

### 개발/테스트 생산성 (3.1)
- **Docker Compose 지원**: `compose.yaml`이 있으면 `bootRun` 시 의존 컨테이너(DB 등)를 자동 기동/종료한다.
- **Testcontainers 1급 통합**: 테스트에서 컨테이너 기반 의존성을 선언적으로 구성(`@ServiceConnection`).

```yaml
# compose.yaml — bootRun 시 자동 기동
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: secret
    ports: ["5432:5432"]
```

> **Testcontainers** — 테스트를 돌릴 때 진짜 DB·브로커를 컨테이너로 띄워 쓰게 해 주는 도구.\
> 예: 원문이 이 통합의 표시로 드는 애너테이션이 `@ServiceConnection`이고, 붙이는 방식을 "선언적으로 구성"이라 적는다.

## 마이너 버전별 변화
- **3.0 (2022)**: Java 17, Jakarta EE 9, Spring Framework 6, GraalVM 네이티브/AOT, 관측성(Observation/Tracing), `spring.factories` 자동 설정 → `AutoConfiguration.imports` 전환 완료.
- **3.1 (2023)**: Docker Compose 지원, Testcontainers 통합(`@ServiceConnection`), SSL 번들, Spring Authorization Server 1.1.
- **3.2 (2023)**: Java 21·가상 스레드, `RestClient`/`JdbcClient`, CRaC(Coordinated Restore at Checkpoint), Spring Framework 6.1.
- **3.3 (2024)**: CDS로 기동 가속, Docker Compose에서 Bitnami 이미지 지원, 보안/관측성 보강.
- **3.4 (2024)**: 구조화된 로깅(JSON 로그), `RestClient`/`RestTemplate`용 HTTP 클라이언트(Reactor Netty/JDK) 자동 설정, 기본 Buildpacks 빌더를 Paketo `builder-jammy-base`에서 `builder-jammy-java-tiny`로 변경.
- **3.5 (2025)**: Testcontainers·Docker Compose SSL 구성 지원, 설정·Actuator·빌드 도구 다듬기 등 후속 개선.

> **`spring.factories` → `AutoConfiguration.imports`** — 자동 설정 후보 목록을 적어 두던 파일이 바뀐 것. 1.x 편의 자동 설정 흐름도에서 "spring.factories 로드"라고 적힌 그 자리다.\
> 예: 이 편의 원문은 3.0 항목에 "전환 완료"라고만 적는다. 2.7에서 전환이 시작됐다는 것은 2.x 편 원문에서 끌어온 값이다(출처 편: `boot-2.x.md` — "전환을 시작하며 3.0 마이그레이션 길을 닦음").

> **CDS(Class Data Sharing) / CRaC** — 클래스 정보를 미리 만들어 두고 나눠 써 기동을 앞당기는 자바 기능 / 실행 중 상태를 체크포인트로 떠 두었다가 되살리는 기능.\
> 예: 원문은 CDS를 3.3의 "CDS로 기동 가속"으로, CRaC를 3.2 항목으로 이름과 풀이름까지만 적는다.

> **구조화된 로깅(structured logging)** — 로그를 사람이 읽는 문장이 아니라 기계가 읽는 형식으로 남기는 것.\
> 예: 원문이 3.4 항목에서 괄호로 붙인 형식이 "JSON 로그"다.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 세 줄은 원문의 세 불릿 그대로다.)*

- **클라우드 네이티브로의 재정렬**: 네이티브 이미지·가상 스레드·관측성 표준 통합으로, Spring을 서버리스/컨테이너 비용 모델에 맞게 현대화했다.
- **Jakarta 전환의 분수령**: 생태계 전체가 `javax`→`jakarta`로 넘어가는 강제 분기점이 되었고, 3.x로의 이동은 단순 버전 업이 아니라 의존성 전수 점검을 요구했다.
- **현대 Java 전제**: record·sealed·패턴 매칭을 자연스럽게 쓰는 코드 스타일을 표준화했고, Kotlin과의 시너지도 더 깊어졌다.

둘째 불릿의 "의존성 전수 점검"은 「시대적 배경」 마지막 문장의 "마이그레이션 비용이 큰"의 한 부분을 가리킨다 — 원문의 그 문장은 Java 17·Jakarta·네이티브·관측성의 변화들을 "한꺼번에 흡수했다"고 적으므로 총비용 쪽이고, 의존성 전수 점검은 그중 Jakarta 한 축에서 나온 몫이다.\
원문이 이 편에서 비용으로 적은 문장은 「시대적 배경」 마지막의 "그만큼 **마이그레이션 비용이 큰** 메이저 버전이다" 한 줄이다 — 따로 표제를 세우지 않고 이 자리에서 가리킨다.

## 용어 풀이

- **LTS(Long-Term Support)** — 오래 지원해 주기로 정해 둔 자바 버전. 3.x의 기준점은 Java 17 LTS(2021)다.
- **최소 자바 버전(3.x)** — 바닥은 Java 17이고, 가상 스레드 등 일부 기능은 Java 21이 필요하다는 단서가 원문에 붙어 있다.
- **record** — 값을 담기만 하는 클래스를 한 줄로 선언하는 자바 문법. 원문은 쓰임을 DTO/설정 객체로 든다.
- **sealed class** — 상속할 수 있는 쪽을 미리 못 박아 두는 자바 문법. 원문은 쓰임을 도메인 모델로 든다.
- **DTO(Data Transfer Object)** — 계층 사이에 값만 실어 나르는 객체.
- **네임스페이스(namespace)** — 이름이 겹치지 않게 앞에 붙여 두는 구역 이름. `javax.*` → `jakarta.*`가 그 변경이다.
- **Jakarta EE** — 자바의 기업용 표준 API 묶음. Java EE가 Eclipse Foundation으로 옮겨 가며 얻은 새 이름이고, 3.0의 기준은 Jakarta EE 9다.
- **AOT(Ahead-of-Time)** — 실행 전에 미리 컴파일·계산해 두는 것. Spring Framework 6의 AOT 처리 엔진을 Boot 3이 내장했다.
- **네이티브 이미지(GraalVM Native Image)** — JVM 없이 바로 도는 OS 실행 파일. 원문이 이 절에서 든 이득은 기동 시간·메모리 사용량·이미지 크기이고, 어울리는 자리는 서버리스·콜드스타트 민감 워크로드다.
- **리플렉션(reflection) / 동적 프록시** — 실행 중에 클래스·메서드를 이름으로 찾아 쓰는 기능 / 실행 중에 대역 객체를 만들어 끼우는 기능. AOT는 이 사용을 최소화한다.
- **서버리스 / 콜드스타트** — 요청이 올 때만 인스턴스를 띄워 쓰는 방식 / 새로 뜰 때 처음 한 번 걸리는 기동 시간.
- **관측성(Observability)** — 돌아가는 시스템의 안을 밖에서 들여다볼 수 있게 해 두는 것. 3.x는 메트릭에 분산 추적을 더했다.
- **분산 추적(distributed tracing) / trace / span** — 요청 하나가 여러 서비스를 거쳐 간 길을 이어 붙여 보는 것 / 그 길 전체 / 길을 이루는 토막 하나.
- **`Observation` / Micrometer Observation API / Micrometer Tracing** — 한 번 계측해 메트릭과 트레이스를 함께 만드는 계측 지점 / 그 API / 원문이 "구 Spring Cloud Sleuth의 후신"이라 적은 추적 쪽 구현.
- **OpenTelemetry / Zipkin** — 원문 도식에서 분산 추적을 받아 가는 백엔드 둘.
- **가상 스레드(virtual thread, Project Loom)** — OS 스레드를 하나씩 붙들지 않고 JVM이 가볍게 관리하는 스레드. 3.2에서 설정 한 줄로 켠다.
- **`RestClient` / `JdbcClient`** — `RestTemplate`을 대체하는 현대적 동기 HTTP 클라이언트 / 간결한 JDBC 클라이언트. 둘 다 3.2다.
- **플루언트 API(fluent API)** — 점을 찍어 메서드를 이어 붙이며 한 문장처럼 쓰는 호출 방식.
- **Testcontainers / `@ServiceConnection`** — 테스트에서 진짜 의존성을 컨테이너로 띄워 쓰게 해 주는 도구 / 그것을 선언적으로 이어 붙이는 애너테이션.
- **`spring.factories` → `AutoConfiguration.imports`** — 자동 설정 후보 목록 파일의 교체. 이 편 원문은 3.0의 "전환 완료"를 적고, 2.7 시작은 2.x 편 원문에서 끌어온 값이다.
- **CDS(Class Data Sharing) / CRaC(Coordinated Restore at Checkpoint)** — 클래스 정보를 미리 만들어 나눠 써 기동을 앞당기는 기능 / 실행 중 상태를 체크포인트로 떠 두었다 되살리는 기능.
- **구조화된 로깅(structured logging)** — 로그를 기계가 읽는 형식으로 남기는 것. 원문이 든 형식은 JSON 로그다.
- **Buildpacks 빌더(Paketo)** — 컨테이너 이미지를 만들 때 쓰는 빌더. 3.4에서 기본이 `builder-jammy-base`에서 `builder-jammy-java-tiny`로 바뀌었다.

## 참고 출처
- [Spring Boot 3.0 Goes GA (spring.io blog)](https://spring.io/blog/2022/11/24/spring-boot-3-0-goes-ga/)
- [Spring Boot 3 and Spring Framework 6 ... GraalVM (InfoQ)](https://www.infoq.com/news/2022/11/spring-6-spring-boot-3-launch/)
- [Spring Boot 3.0 Release Notes (GitHub wiki)](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-3.0-Release-Notes)
- [Spring Boot 3.2 — Virtual Threads, RestClient, JdbcClient (InfoQ)](https://www.infoq.com/news/2023/12/spring-boot-virtual-threads/)
- [Spring Boot 3.2 and Spring Framework 6.1 — Java 21, Virtual Threads, CRaC (InfoQ)](https://www.infoq.com/articles/spring-boot-3-2-spring-6-1/)
- [Spring Boot 3.x Features: Complete Guide (danvega.dev)](https://www.danvega.dev/blog/spring-boot-3-features)
- [Spring Boot 3.5.0 available now (spring.io blog)](https://spring.io/blog/2025/05/22/spring-boot-3-5-0-available-now/)

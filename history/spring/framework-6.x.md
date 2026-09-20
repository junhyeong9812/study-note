# Spring Framework 6.x (2022 ~)

> 원본: `~/project/java-history/spring/framework-6.x.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·패키지/클래스/어노테이션 이름·RFC 번호·코드블록 6개(모두 Java)·「릴리스 정보」와 「마이너 버전별 변화」의 목록은 원문 그대로다.\
> ASCII 도식 2개(모두 원문 mermaid 그림을 글자로 옮긴 것이다), 「한눈에」의 주소 개편 비유와 대응표, 용어 블록의 「예:」, 「용어 풀이」는 원문에 없는 보충이다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> Java 17 baseline과 **`javax.*` → `jakarta.*` 네임스페이스 대전환**으로 한 세대를 끊은 버전. AOT/GraalVM 네이티브 이미지와 옵저버빌리티(Micrometer)를 1급으로 끌어올렸고, 6.1에서 가상 스레드를 받아들였다.

이 편의 대전환을 하나의 비유로 읽으면 **한 도시의 주소 표기가 통째로 새 체계로 바뀐 일**이다.\
내 서류의 주소만 고쳐 적으면 끝나는 게 아니라, 우편물을 받아 주는 곳과 거래처의 장부까지 같이 바꿔야 편지가 도착한다.\
**`javax.*` → `jakarta.*` 전환도 똑같은 구조다** — 원문 자신이 「시대적 배경」에서 "이는 단순 리네이밍이 아니라 import·서드파티 라이브러리·서블릿 컨테이너까지 모두 갈아엎어야 하는 호환성 단절이다"라고 적는다.

본문 흐름에 쓰는 비유는 이 주소 개편 하나뿐이고, 그것이 덮는 것은 「javax → jakarta 네임스페이스 대전환 (6.0의 핵심)」 절이다.\
AOT·옵저버빌리티·가상 스레드 절은 비유 없이 원문 문장과 그림으로만 읽는다.

| 비유 | 실체 |
|---|---|
| 주소 표기가 통째로 새 체계로 바뀌는 일 | 원문 표현으로 "Servlet, JPA, Bean Validation, JMS, Annotations 등 표준 API import가 통째로 바뀐다" |
| 내 서류의 주소를 고쳐 적는 일 | `import javax.…`을 `import jakarta.…`으로 바꾸는 것 |
| 우편물을 받아 주는 곳과 거래처의 장부까지 바꿔야 하는 것 | 원문 표현으로 "서블릿 컨테이너도 Jakarta 지원 버전 필요(Tomcat 10+, Jetty 11+ 등), 모든 서드파티 라이브러리도 jakarta 호환 버전으로 올려야 한다" |
| 이름이 바뀐 까닭이 길이 막혀서가 아니라 간판 문제였던 것 | 원문 표현으로 "Oracle이 Java EE를 Eclipse 재단에 이관(Jakarta EE)하면서, 상표 문제로 … 강제 변경됐다" |

초보자가 가장 자주 하는 오해부터 짚어 두면 이렇다.

- **`javax` → `jakarta`는 이름만 바꾸는 일이 아니다.**\
  원문이 「시대적 배경」에서 "단순 리네이밍이 아니라"라고 직접 부정하고, 갈아엎을 대상으로 import·서드파티 라이브러리·서블릿 컨테이너 셋을 든다.
- **가상 스레드가 WebFlux를 밀어낸 것이 아니다.**\
  원문은 「영향과 의의」에서 "6.x는 리액티브(WebFlux)와 가상 스레드라는 **두 동시성 모델을 모두 품은** 세대다"라고 적는다.\
  가상 스레드에 원문이 붙인 말은 "리액티브의 복잡함 없이 높은 동시성을 얻는 **대안**"이다.
- **AOT의 이득으로 원문이 든 것은 시작 시간과 메모리다.**\
  원문 표현으로 "결과적으로 시작 시간 수십 ms, 메모리 대폭 절감 — 서버리스·컨테이너 환경에 유리"이고, 그 방법은 "런타임 리플렉션 대신 빌드 타임 메타데이터"다.

## 릴리스 정보
- 최초 출시: 6.0 — 2022년 11월 16일
- 주요 마이너 버전과 시기: 6.0(2022-11) → 6.1(2023-11) → 6.2(2024-11)
- 최소 자바 버전(baseline): **Java 17** (6.x 최초로 Java 17을 강제. 6.1은 JDK 21을 first-class 지원, 6.2는 JDK 17-25 범위 지원)
- Java EE / Jakarta EE 기준: **Jakarta EE 9 baseline, Jakarta EE 10 호환** (6.2는 Jakarta EE 9-10, JDK 17-25 범위)

## 시대적 배경

6.0의 배경은 자바 생태계의 두 가지 큰 단절이다.

1. **Jakarta EE 네임스페이스 전환** — Oracle이 Java EE를 Eclipse 재단에 이관(Jakarta EE)하면서, 상표 문제로 모든 표준 API 패키지가 `javax.*` → `jakarta.*`로 강제 변경됐다(Jakarta EE 9, 2020). 이는 단순 리네이밍이 아니라 import·서드파티 라이브러리·서블릿 컨테이너까지 모두 갈아엎어야 하는 호환성 단절이다. Spring 6.0은 이 전환을 정면으로 수용했다.

2. **Java 17 LTS 확산** — 2021년 Java 17 LTS가 나오며 레코드·sealed 클래스·패턴 매칭 등 현대 문법이 자리 잡았다. Spring 6은 과감히 baseline을 Java 17로 올려 낡은 호환 코드를 제거하고 새 언어 기능을 활용한다.

> **네임스페이스(namespace)** — 이름이 겹치지 않게 이름 앞에 붙여 두는 구역. 자바에서는 패키지 이름이 그 구역이다.\
> 예: 원문이 바뀌었다고 적은 그 구역이 `javax.*`와 `jakarta.*`이고, 바뀐 까닭은 기능이 아니라 "상표 문제"다.

> **호환성 단절(breaking change)** — 옛 코드가 그대로는 더 이상 돌아가지 않게 되는 변화.\
> 예: 원문이 이 말을 붙인 대상이 네임스페이스 전환이고, 갈아엎을 것으로 든 셋이 import·서드파티 라이브러리·서블릿 컨테이너다.

> **LTS(Long-Term Support)** — 오래 지원해 주기로 정해 둔 버전. 원문은 Java 17에 이 말을 붙인다.\
> 예: 원문이 "2021년 Java 17 LTS가 나오며" 자리 잡았다고 든 문법이 레코드·sealed 클래스·패턴 매칭이다.

여기에 클라우드 네이티브 수요(빠른 시작·낮은 메모리)에 맞춰 **AOT 컴파일/GraalVM 네이티브 이미지**를 1급으로 지원하고, 분산 추적·메트릭을 위한 **Micrometer 기반 옵저버빌리티**를 코어에 통합했다.

## 핵심 추가/변경 기능

### javax → jakarta 네임스페이스 대전환 (6.0의 핵심)

*(「한눈에」의 주소 개편에 해당하는 자리다.)*

Servlet, JPA, Bean Validation, JMS, Annotations 등 표준 API import가 통째로 바뀐다(다만 `@PostConstruct`·`@Inject` 같은 `javax.annotation`·`javax.inject` 애노테이션은 기존 바이너리 호환을 위해 6.x가 `javax` 쪽도 계속 인식한다 — 완전 제거는 7.0).

```java
// Spring 5.x (Java EE / javax)
import javax.servlet.http.HttpServletRequest;
import javax.persistence.Entity;
import javax.persistence.Id;
import javax.validation.constraints.NotNull;

// Spring 6.x (Jakarta EE / jakarta)
import jakarta.servlet.http.HttpServletRequest;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.validation.constraints.NotNull;
```

위 두 묶음은 줄 수도, 줄 순서도, 점 뒤의 글자도 같다.\
달라진 것은 맨 앞 한 마디뿐이다 — `javax`가 `jakarta`로 바뀌었다.

```java
@Entity                                  // jakarta.persistence.Entity
public class Account {
    @Id                                  // jakarta.persistence.Id
    private Long id;

    @NotNull                             // jakarta.validation.constraints.NotNull
    private String name;
}
```

어노테이션 이름(`@Entity`·`@Id`·`@NotNull`)은 그대로이고, 원문이 주석으로 적어 둔 그 어노테이션의 출처 패키지가 `jakarta.*`로 바뀌었다.

**대가는 무엇인가**

- 원문이 이 절 첫 문단 끝에 적은 그대로다: "이것이 5.x → 6.x 마이그레이션의 **가장 큰 장벽**이다."
- 원문이 코드 아래에 적은 영향 범위도 그대로다: "서블릿 컨테이너도 Jakarta 지원 버전 필요(Tomcat 10+, Jetty 11+ 등), 모든 서드파티 라이브러리도 jakarta 호환 버전으로 올려야 한다."

다음 그림은 네임스페이스 전환의 before/after를 요약한다.\
import 패키지뿐 아니라 서블릿 컨테이너와 서드파티 의존성까지 함께 올려야 하는 호환성 단절이다.

```text
Before (Spring 5.x / Java EE)                     After (Spring 6.x / Jakarta EE)

javax.servlet.*      --[패키지 전환]-->           jakarta.servlet.*
javax.persistence.*  --[패키지 전환]-->           jakarta.persistence.*
javax.validation.*   --[패키지 전환]-->           jakarta.validation.*
Tomcat 9 / Jetty 9   --[컨테이너 업그레이드]-->   Tomcat 10+ / Jetty 11+
```

- 이 그림은 원문의 첫 번째 mermaid 그림을 글자로 옮긴 것이다 — 화살표 넷으로 원문과 같고, 방향도 원문과 같이 왼쪽에서 오른쪽이다.
- 두 칸 머리의 `Before (Spring 5.x / Java EE)`·`After (Spring 6.x / Jakarta EE)`는 원문이 두 묶음에 붙인 제목 그대로다.
- **같은 행의 왼쪽과 오른쪽은 원문이 화살표로 직접 이어 둔 짝이다** — 네 짝 모두 원문의 화살표 하나에 대응한다.
- 화살표 위 라벨도 원문 라벨 그대로다 — 위 세 줄은 "패키지 전환", 맨 아래 한 줄만 "컨테이너 업그레이드"다.

### Java 17 baseline

레코드, sealed 클래스, 텍스트 블록, 패턴 매칭 등을 프레임워크와 애플리케이션에서 자연스럽게 사용.\
예를 들어 record를 그대로 DTO/설정 바인딩에 활용.

> **레코드(record)** — 담을 값의 이름과 타입만 괄호 안에 적어 선언하는 자바의 데이터 전용 타입.\
> 예: 아래 코드의 `AccountDto`가 그것이고, 원문은 이것을 "그대로 DTO/설정 바인딩에 활용"한다고 적는다.

```java
public record AccountDto(Long id, String name, BigDecimal balance) {}

@GetMapping("/{id}")
public AccountDto get(@PathVariable Long id) { ... }   // record 직렬화
```

### AOT(Ahead-Of-Time) 처리 / GraalVM 네이티브 이미지

빌드 시점에 빈 정의·프록시·리플렉션 메타데이터를 미리 분석·생성(AOT)하여, GraalVM으로 **네이티브 실행 파일**을 만든다.\
결과적으로 시작 시간 수십 ms, 메모리 대폭 절감 — 서버리스·컨테이너 환경에 유리. (Spring Boot 3.0이 이 AOT 엔진을 빌드 플러그인으로 노출한다.)

- 런타임 리플렉션 대신 빌드 타임 메타데이터 → 네이티브 이미지에서 동작 보장
- AOT 처리된 컨텍스트의 **테스트**(TestContext AOT 지원)는 6.0부터 제공되며, 6.1에서 `failOnError` 옵션 등으로 보강됐다

> **AOT(Ahead-Of-Time, 미리 하기) / 런타임 / 빌드 타임** — 프로그램을 돌리기 전 빌드하는 시점에 미리 해 두는 것 / 프로그램이 돌아가는 동안 / 프로그램을 만들어 내는 동안.\
> 예: 원문이 미리 해 둔다고 적은 일이 "빈 정의·프록시·리플렉션 메타데이터를 미리 분석·생성"이고, 그 대비로 든 짝이 "런타임 리플렉션 대신 빌드 타임 메타데이터"다.

> **리플렉션(reflection)** — 프로그램이 돌아가는 중에 클래스·메서드 같은 자기 구조를 들여다보고 다루는 기능.\
> 예: 원문은 AOT의 요점을 "런타임 리플렉션 대신 빌드 타임 메타데이터 → 네이티브 이미지에서 동작 보장"으로 적는다.

아래는 소스/빈 정의가 Spring AOT 처리를 거쳐 GraalVM 네이티브 실행 파일로 만들어지는 파이프라인이다.\
동적 리플렉션·프록시를 컴파일 타임에 분석해 코드와 메타데이터 힌트로 미리 생성하므로, 런타임 리플렉션에 의존하지 않고 네이티브 이미지에서 동작이 보장된다.

```text
소스 코드 + 빈 정의 (@Configuration/@Bean)
        ↓
Spring AOT 처리
        ↓                                 ↓
빈 정의 분석 → 빈 등록 코드 생성    리플렉션/프록시/리소스 메타데이터 힌트 생성
        ↓                                 ↓
        생성된 소스 + reachability 힌트
        ↓
GraalVM native-image (도달성 분석)
        ↓
네이티브 실행 파일 (수십 ms 시작, 저메모리)
```

- 이 그림은 원문의 두 번째 mermaid 그림을 글자로 옮긴 것이다 — 화살표 일곱으로 원문과 같다(`Spring AOT 처리`에서 두 갈래로 나가는 둘, 그 둘이 `생성된 소스 …`로 모이는 둘, 그리고 나머지 셋).
- 칸 안의 글자는 원문 노드 문구 그대로다(둘째 갈래 왼쪽 칸의 `→`도 원문 노드 글자다).
- 가운데 두 칸이 나란히 놓인 것은 원문이 그 둘을 같은 칸에서 갈라 같은 칸으로 모아 두었기 때문이다.
- 바로 위 문단이 이 그림을 읽는 법이다 — "동적 리플렉션·프록시를 컴파일 타임에 분석해 코드와 메타데이터 힌트로 미리 생성"하는 부분이 가운데 두 칸이다.

> **도달성 분석(reachability) / 네이티브 이미지** — 실제로 닿을 수 있는 코드만 골라내는 분석 / 그렇게 만들어 낸, JVM을 따로 설치하지 않고 바로 실행되는 파일.\
> 예: 원문 그림의 끝에서 둘째 칸이 "GraalVM native-image (도달성 분석)"이고, 마지막 칸이 "네이티브 실행 파일 (수십 ms 시작, 저메모리)"이다.

### 옵저버빌리티(Observability) — Micrometer 통합

분산 추적과 메트릭을 위한 `Micrometer Observation API`를 코어에 통합.\
WebFlux/WebMVC 요청, `RestTemplate`/`WebClient`, `@Scheduled` 등에 일관된 관측 지점을 제공한다.

> **옵저버빌리티(observability) / 분산 추적 / 메트릭** — 돌아가는 시스템 안에서 무슨 일이 벌어지는지 밖에서 볼 수 있게 하는 것 / 요청 하나가 여러 서비스를 거쳐 간 경로를 따라가 보는 것 / 수치로 재어 남기는 지표.\
> 예: 원문이 관측 지점을 붙였다고 든 자리가 WebFlux/WebMVC 요청, `RestTemplate`/`WebClient`, `@Scheduled`다.

```java
Observation.createNotStarted("account.lookup", registry)
    .observe(() -> accountService.find(id));
```

### HTTP Interface 클라이언트 (선언적 HTTP)

인터페이스 + 어노테이션만으로 HTTP 클라이언트를 선언(Spring Data Repository와 유사한 방식).\
내부적으로 WebClient(또는 6.1의 RestClient) 기반.

> **선언적(declarative) 방식** — 어떻게 할지를 적는 대신 무엇인지를 적어 두면 나머지는 프레임워크가 채우는 방식.\
> 예: 아래 인터페이스에는 호출 코드가 한 줄도 없고 `@GetExchange("/accounts/{id}")`라는 선언만 있다 — 원문은 구현체를 "`HttpServiceProxyFactory`로" 만든다고 주석에 적는다.

```java
public interface AccountClient {
    @GetExchange("/accounts/{id}")
    Account get(@PathVariable long id);
}
// HttpServiceProxyFactory로 구현체 생성
```

### RestClient — 동기 유창형 HTTP 클라이언트 (6.1)

`RestTemplate`의 인프라를 쓰면서 `WebClient`처럼 유창한(fluent) API를 제공하는 **동기** 클라이언트.\
블로킹 코드에서 WebClient의 리액티브 부담 없이 현대적 API를 쓰게 해준다.

> **유창형(fluent) API** — 호출을 점으로 계속 이어 붙여 한 문장처럼 적게 만든 API.\
> 예: 아래 코드의 `client.get().uri(…).retrieve().body(…)`가 그 이어 붙임이고, 원문은 이것을 "`WebClient`처럼 유창한(fluent) API"라 적는다.

```java
RestClient client = RestClient.create("https://api.example.com");

Account account = client.get()
    .uri("/accounts/{id}", 42)
    .retrieve()
    .body(Account.class);
```

### 가상 스레드(Virtual Threads) 지원 (6.1)

Java 21의 가상 스레드(Project Loom)를 지원.\
요청당 스레드(thread-per-request) 모델을 유지하면서도 블로킹 I/O를 값싸게 처리 — 리액티브의 복잡함 없이 높은 동시성을 얻는 대안.\
(Spring Boot 3.2에서 `spring.threads.virtual.enabled=true`로 Tomcat/Jetty에 적용.)

> **가상 스레드(virtual thread) / 요청당 스레드(thread-per-request)** — 운영체제 스레드보다 값싸게 아주 많이 만들 수 있는 스레드 / 요청 하나마다 스레드 하나를 붙이는 모델.\
> 예: 원문이 이 둘을 묶어 적은 말이 "요청당 스레드 모델을 유지하면서도 블로킹 I/O를 값싸게 처리"다 — 모델을 바꾸는 것이 아니라 그 모델을 싸게 만드는 쪽이다.

### 기타 (6.1 / 6.2)
- 6.1: **RestClient**, **JdbcClient**(유창형 JDBC API), 가상 스레드, `@Scheduled` Micrometer 계측, AOT 테스트 보강(`failOnError` 등 — AOT 컨텍스트 테스트 자체는 6.0 도입), Reactor/Jackson 등 의존성 현대화, JDK 21 지원.
- 6.2: 빈 백그라운드 초기화·컨테이너 시작 성능 개선, `@Fallback` 빈, 널 안정성 개선, Jackson/검증/메시징 업데이트, JDK 17-25 범위 지원. (이후 7.0이 2025-11에 등장하며 다음 세대로 이어진다.)

## 설정 스타일의 변화

설정 모델 자체(Java Config + 어노테이션 + Boot 자동 구성 + 함수형 DSL)는 5.x에서 정립된 것을 계승한다.\
6.x의 변화는 **"무엇을 import 하느냐"와 "어떻게 빌드/실행하느냐"**에 있다.
- 패키지 네임스페이스가 `jakarta.*`로 교체 — 코드 레벨의 가장 큰 차이(`javax.annotation`·`javax.inject` 애노테이션만 호환을 위해 6.x가 함께 인식한다).
- **AOT를 전제로 한 설정** — 동적 리플렉션·런타임 빈 등록보다, 빌드 타임에 정적으로 분석 가능한 구성이 권장된다(네이티브 이미지 친화). Kotlin/Java의 함수형 빈 DSL이 이런 면에서 유리.

## 마이너 버전별 변화
- 6.0 (2022-11): **Java 17 baseline**, **`javax→jakarta` 전환(Jakarta EE 9+)**, AOT/GraalVM 네이티브 지원, Micrometer 옵저버빌리티, HTTP Interface 클라이언트, ProblemDetail(RFC 7807) 지원.
- 6.1 (2023-11): **RestClient**, JdbcClient, **가상 스레드(JDK 21)** 지원, `@Scheduled` 관측, AOT 테스트, JDK 21 정식 지원.
- 6.2 (2024-11): 컨테이너 시작 성능·백그라운드 초기화 개선, `@Fallback` 빈, 널 안정성·검증·Jackson 개선, JDK 17-25 / Jakarta EE 9-10 지원.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 세 불릿은 원문의 것이다.)*

- **`javax→jakarta` 전환**은 Spring 역사상 가장 큰 호환성 단절이었지만, 동시에 레거시 정리의 분기점이 됐다. 5.x → 6.x 마이그레이션은 단순 버전업이 아니라 의존성·컨테이너·import 전반의 현대화를 강제했다.
- **AOT/네이티브 이미지**로 Spring이 서버리스·클라우드 네이티브의 빠른 시작·저메모리 요구에 정면으로 대응했다.
- **가상 스레드** 지원은 "고동시성을 위해 반드시 리액티브여야 한다"는 전제를 깼다 — 명령형 코드를 그대로 두고도 확장성을 얻는 새로운 길을 열었다. 6.x는 리액티브(WebFlux)와 가상 스레드라는 두 동시성 모델을 모두 품은 세대다.

## 용어 풀이

- **네임스페이스(namespace)** — 이름이 겹치지 않게 이름 앞에 붙여 두는 구역. 자바에서는 패키지 이름이 그 구역이고, 6.0이 바꾼 것이 `javax.*` → `jakarta.*`다.
- **호환성 단절(breaking change)** — 옛 코드가 그대로는 더 이상 돌아가지 않게 되는 변화. 원문은 네임스페이스 전환을 "Spring 역사상 가장 큰 호환성 단절"이라 적는다.
- **Jakarta EE** — Oracle이 Java EE를 Eclipse 재단에 이관하며 붙은 이름. 패키지 이름이 바뀐 까닭은 기능이 아니라 상표 문제다.
- **LTS(Long-Term Support)** — 오래 지원해 주기로 정해 둔 버전. 원문이 이 말을 붙인 것이 Java 17이다.
- **레코드(record)** — 담을 값의 이름과 타입만 괄호 안에 적어 선언하는 자바의 데이터 전용 타입. 원문은 이것을 "그대로 DTO/설정 바인딩에 활용"한다고 적는다.
- **AOT(Ahead-Of-Time) / 런타임 / 빌드 타임** — 돌리기 전 빌드 시점에 미리 해 두는 것 / 프로그램이 돌아가는 동안 / 프로그램을 만들어 내는 동안. 원문이 미리 해 둔다고 적은 것은 "빈 정의·프록시·리플렉션 메타데이터"다.
- **리플렉션(reflection)** — 실행 중에 클래스·메서드 같은 자기 구조를 들여다보고 다루는 기능. AOT의 요점이 "런타임 리플렉션 대신 빌드 타임 메타데이터"다.
- **도달성 분석(reachability) / 네이티브 이미지** — 실제로 닿을 수 있는 코드만 골라내는 분석 / 그렇게 만들어 낸, JVM을 따로 설치하지 않고 바로 실행되는 파일. 원문이 든 결과가 "시작 시간 수십 ms, 메모리 대폭 절감"이다.
- **GraalVM** — 원문이 네이티브 실행 파일을 만드는 도구로 든 것. 그 명령이 `native-image`다.
- **옵저버빌리티(observability) / 분산 추적 / 메트릭** — 시스템 안에서 무슨 일이 벌어지는지 밖에서 볼 수 있게 하는 것 / 요청이 여러 서비스를 거쳐 간 경로를 따라가는 것 / 수치로 재어 남기는 지표.
- **Micrometer Observation API** — 원문이 코어에 통합했다고 적은 관측 API. 관측 지점이 붙는 자리가 WebFlux/WebMVC 요청, `RestTemplate`/`WebClient`, `@Scheduled`다.
- **선언적(declarative) 방식** — 어떻게 할지 대신 무엇인지를 적어 두면 나머지를 프레임워크가 채우는 방식. HTTP Interface 클라이언트가 그 예이고, 구현체는 `HttpServiceProxyFactory`가 만든다.
- **유창형(fluent) API** — 호출을 점으로 이어 붙여 한 문장처럼 적게 만든 API. 6.1의 `RestClient`와 `JdbcClient`가 그렇게 생겼다.
- **`RestClient`** — `RestTemplate`의 인프라를 쓰면서 `WebClient`처럼 유창한 API를 제공하는 **동기** 클라이언트(6.1).
- **가상 스레드(virtual thread) / 요청당 스레드(thread-per-request)** — 운영체제 스레드보다 값싸게 아주 많이 만들 수 있는 스레드 / 요청 하나마다 스레드 하나를 붙이는 모델. 원문은 가상 스레드를 "리액티브의 복잡함 없이 높은 동시성을 얻는 대안"이라 적는다.

## 참고 출처
- [Spring Framework 6.0 goes GA (spring.io blog)](https://spring.io/blog/2022/11/16/spring-framework-6-0-goes-ga/)
- [What's New in Spring Framework 6.x (GitHub wiki)](https://github.com/spring-projects/spring-framework/wiki/What's-New-in-Spring-Framework-6.x)
- [Spring Boot 3.2 and Spring Framework 6.1 Add Java 21, Virtual Threads, and CRaC (InfoQ)](https://www.infoq.com/articles/spring-boot-3-2-spring-6-1/)
- [Observability Support :: Spring Framework (docs)](https://docs.spring.io/spring-framework/reference/integration/observability.html)
- [Spring Framework - Wikipedia](https://en.wikipedia.org/wiki/Spring_Framework)

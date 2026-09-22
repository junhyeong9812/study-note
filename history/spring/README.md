# Spring 변천사 — 쉽게 다시 쓴 판

> 원본: `~/project/java-history/spring/README.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·모듈 이름·표 4개·원문이 직접 그린 설정 스타일 블록·문서 링크는 원문 그대로다.\
> ASCII 도식 4개(그중 3개는 원문의 mermaid 도식을 옮긴 것)와 「급하면 이렇게 골라 읽어도 된다」 길찾기는 원문 README에 없는 보충이다.\
> H1만 다른 주제 README(`history/python/README.md` 등)와 형식을 맞춰 바꿨다 — 원문 H1은 「Spring 변천사 — Framework / Boot / Kotlin」이다. 나머지 절 제목은 원문 그대로다.\
> 원문 README에는 「읽는 법」·「큰 줄기」 절이 없다. 그 자리를 대신하는 길찾기는 보충이고, 길찾기가 가리키는 절 제목은 각 편 원문에서 그대로 옮겼다.\
> 목차의 「시기」는 열을 새로 만들지 않고 원문 「문서 목차」 표의 **「최초 출시」 칸**을 그대로 쓴다 — Framework 7편과 Boot 4편이 같은 기준으로 적혀 있어 통일이 가능했다.

> Spring Framework와 Spring Boot의 역사를 대버전별로 정리한 "책". 설정 방식의 변천(XML → 어노테이션 → Java Config → 함수형 DSL)과 Kotlin의 도입사를 함께 다룬다.

## 한눈에 — 13편이 놓인 자리

이 폴더는 **12편 + 이 README = 13편**이다. 두 갈래가 나란히 달린 역사라는 점이 이 책의 골격이다.

```text
 대버전의 순서로 놓은 12편 (괄호 = 원문 「문서 목차」 표의 「최초 출시」 칸)

 Framework  1.x        2.x        3.x        4.x        5.x        6.x        7.x
            (2004-03)  (2006-10)  (2009-12)  (2013-12)  (2017-09)  (2022-11)  (2025-11)
 ─────────────────────────────────────────────────────────────────────────────────────
 Boot                                        1.x        2.x        3.x        4.x
                                             (2014-04)  (2018-03)  (2022-11)  (2025-11)

 Kotlin     kotlin-and-spring.md   — 두 갈래를 가로질러 코틀린 도입사를 따로 다룬 1편
 이 문서    README.md              — 위 12편의 색인
```

그림 읽는 법 — **가로 위치는 연도 눈금이 아니라 대버전의 순서**다. 1.x와 2.x 사이(2004-03 → 2006-10)도, 4.x와 5.x 사이(2013-12 → 2017-09)도 같은 한 칸 폭으로 그려져 있다.\
세로로 같은 칸에 놓인 짝(Framework 4.x ↔ Boot 1.x, 5.x ↔ 2.x, 6.x ↔ 3.x, 7.x ↔ 4.x)은 내가 맞춘 것이 아니라 원문 「Spring Boot (자동 설정 레이어)」 표의 **「기반 Framework」 칸**이 적어 둔 것이다.\
Boot 줄이 앞의 세 칸 비어 있는 것도 그대로 읽으면 된다 — 원문 「전체 타임라인」 표의 Boot 칸이 2004·2006\~07·2009\~12 세 행에서 `—`다.

---

## 이 책의 구성

Spring은 두 축으로 진화했다.
- **Spring Framework** — IoC/DI 컨테이너를 핵심으로 한 본체 (1.x \~ 7.x)
- **Spring Boot** — 자동 설정으로 Spring 사용을 간소화한 상위 레이어 (1.x \~ 4.x)

여기에 사용자가 특별히 요청한 **Kotlin과 Spring의 통합사**를 별도 문서로 정리했다.

> **IoC / DI(제어의 역전 / 의존성 주입)** — 필요한 객체를 내가 직접 만들지 않고 컨테이너가 만들어 넣어 주게 맡기는 방식.\
> 예: 원문이 Spring Framework를 "IoC/DI 컨테이너를 핵심으로 한 본체"라 부르고, Boot를 그 위에 얹힌 "상위 레이어"로 적는다.

> **상위 레이어(layer)** — 아래에 있는 것을 대신하는 것이 아니라 그 위에 덧대는 층.\
> 예: 원문이 Boot를 "자동 설정으로 Spring 사용을 간소화한 상위 레이어"라고 적고, 아래 목차에서 Boot 표에 「기반 Framework」 칸을 따로 둔다.

### Spring 모듈 의존성 그래프

아래는 Spring Framework 핵심 모듈의 의존 방향이다. 화살표는 "왼쪽이 오른쪽에 의존한다"는 뜻으로, 모든 길은 결국 `spring-core`로 수렴한다.

```text
 화살표는 "왼쪽이 오른쪽에 의존한다"

 spring-beans       -->  spring-core
 spring-context     -->  spring-beans
 spring-context     -->  spring-aop
 spring-context     -->  spring-expression
 spring-aop         -->  spring-core
 spring-expression  -->  spring-core
 spring-web         -->  spring-context
 spring-webmvc      -->  spring-web
 spring-webflux     -->  spring-web
 spring-tx          -->  spring-beans
 spring-jdbc        -->  spring-tx
 spring-orm         -->  spring-tx
 spring-orm         -->  spring-jdbc
```

그림 읽는 법 — 원문 도식의 열한 개 모듈과 열세 개 화살표를 하나도 빼지 않고 줄 단위로 옮긴 것이다.\
화살표의 뜻은 원문 문장 그대로 "왼쪽이 오른쪽에 의존한다"이다.\
`spring-webmvc`와 `spring-webflux`가 둘 다 `spring-web`을 가리키고 서로를 가리키지 않는 것, 화살표를 여럿 내보내는 모듈이 `spring-context`(셋)와 `spring-orm`(둘) 둘뿐인 것이 이 목록에서 바로 보인다.

---

## 전체 타임라인

| 시기 | Spring Framework | Spring Boot | 핵심 전환점 |
|------|------------------|-------------|-------------|
| 2004 | **1.0** (3월) | — | IoC/DI 컨테이너, AOP, XML 설정, EJB 대안 |
| 2006\~07 | **2.0**(10월) / 2.5(07.11) | — | XML 네임스페이스, 어노테이션(`@Autowired`/`@Component`) 도입 |
| 2009\~12 | **3.0**(12월) / 3.1 / 3.2 | — | Java 5 baseline, **Java Config**, SpEL, REST, `@Profile` |
| 2013\~16 | **4.0**(13.12) / 4.3 | **1.0**(14.04) | Java 8 지원, `@RestController` / Boot 등장(자동 설정·스타터) |
| 2017\~20 | **5.0**(17.09) / 5.2 / 5.3 | **2.0**(18.03) | **리액티브(WebFlux) + Kotlin 1급 지원** / Boot 2.0 Kotlin 정식 지원, 5.2 코루틴 |
| 2022\~ | **6.0**(22.11) / 6.1 / 6.2 | **3.0**(22.11) / 3.1\~3.5 | **Java 17 + Jakarta EE 9(javax→jakarta)**, GraalVM 네이티브/AOT, 가상 스레드 |
| 2025\~ | **7.0**(25.11.13 GA) | **4.0**(25.11.20 GA) | **현재 최신 세대** — Java 17 baseline(Java 25 수용), Jakarta EE 11, JSpecify 널 안정성, API 버저닝, Boot 코드베이스 모듈화 |

표를 읽는 법 — 위에서 세 행은 Boot 칸이 `—`다. Boot가 아직 없던 시기이고, 넷째 행(2013\~16)에서 처음으로 두 칸이 같이 찬다.\
그 넷째 행의 「핵심 전환점」 칸은 두 갈래를 슬래시로 나눠 적는다 — "Java 8 지원, `@RestController` / Boot 등장(자동 설정·스타터)".

아래 타임라인은 Framework 대버전·Boot 대버전과 자바 baseline의 대응 관계를 한눈에 보여준다.

```text
 Spring Framework / Boot 버전 · 자바 매핑

 2004  Framework 1.0 (Java 1.3)
 2006  Framework 2.0 (Java 1.3+)
 2009  Framework 3.0 (Java 5)
 2013  Framework 4.0 (Java 6/8)
 2014  Boot 1.0 (Framework 4.x)
 2017  Framework 5.0 (Java 8)
 2018  Boot 2.0 (Framework 5.x)
 2022  Framework 6.0 / Boot 3.0 (Java 17)
 2025  Framework 7.0 / Boot 4.0 (Java 17, Java 25 수용)
```

그림 읽는 법 — 제목과 아홉 줄의 문구는 원문 도식의 것 그대로다. 원문은 이것을 mermaid의 `timeline`으로 그렸다.\
**줄 사이의 간격은 연도 차이에 비례하지 않는다** — 2009과 2013 사이(4년)와 2013과 2014 사이(1년)가 같은 한 줄이다.\
괄호 안이 두 종류라는 점도 그대로다 — Boot만 적힌 두 줄(2014·2018)의 괄호에는 기반 Framework 버전이, 나머지 일곱 줄의 괄호에는 자바 버전이 들어 있다.

> **baseline(기준선)** — 그 버전을 돌리는 데 최소한 있어야 하는 자바의 바닥 선.\
> 예: 위 목록에서 `Framework 3.0 (Java 5)`의 괄호가 그것이고, 표의 2009\~12 행도 같은 것을 "Java 5 baseline"이라 적는다.

---

## 문서 목차

### Spring Framework (본체)
| 대버전 | 최초 출시 | 최소 자바 | 핵심 | 문서 |
|--------|-----------|-----------|------|------|
| 1.x | 2004-03 | Java 1.3 | IoC/DI, AOP, XML 설정 | [framework-1.x.md](framework-1.x.md) |
| 2.x | 2006-10 | Java 1.3+ (2.5는 1.4.2+) | XML 네임스페이스, 어노테이션 시작 | [framework-2.x.md](framework-2.x.md) |
| 3.x | 2009-12 | Java 5 | Java Config, SpEL, REST | [framework-3.x.md](framework-3.x.md) |
| 4.x | 2013-12 | Java 6 (Java 8은 지원 기능) | Java 8 지원, `@RestController`, WebSocket | [framework-4.x.md](framework-4.x.md) |
| 5.x | 2017-09 | Java 8 | **리액티브(WebFlux) + Kotlin 1급** | [framework-5.x.md](framework-5.x.md) |
| 6.x | 2022-11 | Java 17 | **Jakarta EE 9+, AOT/네이티브** | [framework-6.x.md](framework-6.x.md) |
| 7.x | 2025-11 | Java 17 (Java 25 권장) | **Jakarta EE 11, JSpecify 널 안정성, 코어 회복성, API 버저닝** | [framework-7.x.md](framework-7.x.md) |

### Spring Boot (자동 설정 레이어)
| 대버전 | 최초 출시 | 기반 Framework | 최소 자바 | 핵심 | 문서 |
|--------|-----------|----------------|-----------|------|------|
| 1.x | 2014-04 | 4.x | Java 6 | 자동 설정, 스타터, 내장 톰캣, Actuator | [boot-1.x.md](boot-1.x.md) |
| 2.x | 2018-03 | 5.x | Java 8 | WebFlux, Micrometer, **Kotlin 공식 지원** | [boot-2.x.md](boot-2.x.md) |
| 3.x | 2022-11 | 6.x | Java 17 | Jakarta, GraalVM 네이티브, 가상 스레드 | [boot-3.x.md](boot-3.x.md) |
| 4.x | 2025-11 | 7.x | Java 17 (Java 25 1급) | 자동설정 모듈화, JSpecify, Jackson 3, API 버저닝 | [boot-4.x.md](boot-4.x.md) |

### Kotlin
- [kotlin-and-spring.md](kotlin-and-spring.md) — 코틀린이 언제·어떻게 Spring에 들어왔는가, 자바와 코틀린의 공존 방식

### 원본 뒤
- [99-그-뒤.md](99-그-뒤.md) — 원본이 멈춘 Spring Boot 4.0.1(2025-12-18) 이후 2026-09-20 까지.\
  재서술이 아니라 웹 출처로 새로 쓴 편이다

두 표를 견주어 읽는 법 — Boot 표에만 「기반 Framework」 칸이 있고, 그 칸이 위 표의 어느 행을 가리키는지가 두 갈래를 잇는 실이다.\
Boot 1.x의 「4.x」를 따라가면 Framework 표의 넷째 행이 나오고, 두 행의 「최초 출시」가 2013-12와 2014-04로 넉 달 차이다.

---

## 설정 스타일의 변천 (한눈에)

```
XML BeanFactory     어노테이션         Java Config        Boot 자동설정              함수형/Kotlin DSL
(2004, 1.x)    →    (2007, 2.5)   →    (2009, 3.0)   →    (2014, Boot)         →    (2017, Framework 5.0)
<bean .../>         @Component         @Configuration     @SpringBootApplication    beans { } / router { }
config.xml          @Autowired         @Bean             (auto-configuration)
```

아래 흐름도는 설정 스타일이 XML에서 함수형/Kotlin DSL까지 어떻게 진화했는지를 좌→우로 보여준다.

```text
 XML 설정      -->  어노테이션    -->  JavaConfig    -->  Boot 자동설정      -->  함수형/Kotlin DSL
 (2004, 1.x)        (2007, 2.5)       (2009, 3.0)       (2014, Boot 1.0)        (2017, Framework 5.0)
```

그림 읽는 법 — 다섯 칸의 문구와 네 화살표는 원문 도식의 것 그대로이고, 원문이 적은 방향(좌→우)도 그대로다.\
바로 위의 원문 블록과 이 도식은 같은 다섯 단계를 적지만, 실제 표기 예를 담은 셋째·넷째 줄은 원문 블록에만 있다.\
이름 표기도 조금 다르다 — 원문 블록은 「XML BeanFactory」·「(2014, Boot)」, 이 도식은 「XML 설정」·「(2014, Boot 1.0)」이다.

자바 진영의 흐름:
1. **XML 시대 (1.x\~2.x)** — 모든 빈을 XML로 선언. 장황하지만 설정과 코드 분리.
2. **어노테이션 시대 (2.5\~)** — `@Component`/`@Autowired`로 컴포넌트 스캔. XML 대폭 축소.
3. **Java Config 시대 (3.0\~)** — `@Configuration`/`@Bean`으로 타입 안전한 설정.
4. **Boot 시대 (2014\~)** — 자동 설정(`auto-configuration`)으로 설정 자체를 최소화.
5. **함수형/Kotlin DSL (2017\~)** — `beans { }`, `router { }`로 코드로서의 설정.

다섯 단계의 이름과 순서는 위 두 블록과 이 목록이 같고, 목록 쪽에는 각 단계가 무엇을 얻었는지가 한 마디씩 붙어 있다.

> **컴포넌트 스캔(component scan)** — 패키지를 훑어 표시가 붙은 클래스를 찾아 빈으로 등록하는 것.\
> 예: 위 목록 2번이 `@Component`/`@Autowired`를 그 수단으로 들고, 그 결과를 "XML 대폭 축소"로 적는다.

> **타입 안전한 설정** — 설정을 문자열이 아니라 자바 코드로 적어, 이름을 잘못 쓰면 컴파일 단계에서 걸리게 하는 것.\
> 예: 위 목록 3번의 `@Configuration`/`@Bean`이 그 방식이고, 1번의 `<bean .../>`·`config.xml`이 그 반대쪽이다.

---

## Kotlin 도입 타임라인 (요약)

| 시기 | 사건 |
|------|------|
| 2011-07 | JetBrains, Kotlin 공개 |
| 2016-02 | Kotlin 1.0 출시 |
| 2016 (경) | start.spring.io(프로젝트 생성기)에 Kotlin 옵션 실험적 추가 |
| 2017-05 | Google, 안드로이드 1급 언어로 Kotlin 채택 |
| **2017-09** | **Spring Framework 5.0 — Kotlin 1급 지원 정식 포함** (널 안정성, 확장 함수, `beans`/`router` DSL) |
| **2018-03** | **Spring Boot 2.0 — Kotlin 정식 지원** (컴파일러 플러그인·스타터, start.spring.io 정식 옵션) |
| **2019-09** | **Spring Framework 5.2 — 코루틴(`suspend`/`Flow`) 정식 지원** |

자세한 내용과 코드 예시(자바 vs 코틀린 비교)는 [kotlin-and-spring.md](kotlin-and-spring.md) 참조.

표를 읽는 법 — 굵게 표시된 세 행이 Spring 본체·Boot의 정식 지원 시점이고, 앞의 네 행에는 코틀린·안드로이드 쪽 사건과 start.spring.io의 실험적 추가가 섞여 있다.\
세 번째 행의 "2016 (경)"만 날짜가 흐린데, 그 순서상 의미는 `kotlin-and-spring.md`의 「주의」 블록이 적는다 — Spring Framework 5.0 발표보다 "앞서(2016년경)" 등장했다는 것이다(왜 근사치인지는 원문이 설명하지 않는다).

## 급하면 이렇게 골라 읽어도 된다

*(이 절은 원문 README에 없는 보충이다. 가리키는 절 제목은 각 편 원문에서 그대로 옮겼다.)*

- IoC/DI가 정확히 무엇인지부터 잡고 싶다 → **framework-1.x의 「IoC / DI 컨테이너 (BeanFactory, ApplicationContext)」**
- XML을 언제부터 줄이기 시작했는지 궁금하다 → **framework-2.x의 「어노테이션 기반 설정의 시작 (2.5)」**
- `@Configuration`/`@Bean`이 왜 생겼는지 알고 싶다 → **framework-3.x의 「Java 기반 설정 (@Configuration / @Bean) — 3.x의 핵심」**
- `@Profile`로 환경을 가르는 방식이 어디서 왔는지 궁금하다 → **framework-3.x의 「환경 추상화 / 프로파일 (@Profile) — 3.1」**
- Boot 자동 설정이 딛고 선 조건부 등록이 뭔지 알고 싶다 → **framework-4.x의 「@Conditional — 조건부 빈 등록」**
- 리액티브가 Framework 쪽에서 어떻게 들어왔는지 궁금하다 → **framework-5.x의 「Spring WebFlux — 리액티브 웹 스택」**
- Kotlin 1급 지원이 Framework에서 무엇이었는지 알고 싶다 → **framework-5.x의 「Kotlin 1급 지원 — Spring 5의 또 다른 핵심」**
- `javax`가 왜 `jakarta`가 됐는지 궁금하다 → **framework-6.x의 「javax → jakarta 네임스페이스 대전환 (6.0의 핵심)」**
- 가상 스레드가 Framework 쪽에 언제 들어왔는지 알고 싶다 → **framework-6.x의 「가상 스레드(Virtual Threads) 지원 (6.1)」**
- 7.0이 무엇을 새로 받아들였는지 훑고 싶다 → **framework-7.x의 「JSpecify 기반 널 안정성 (org.springframework.lang → org.jspecify)」·「코어 내장 회복성 — @Retryable · @ConcurrencyLimit」·「REST API 버저닝 (version 속성)」**
- 자동 설정이 "알아서 되는 마법"이 아니라는 걸 확인하고 싶다 → **[boot-1.x](boot-1.x.md)의 「자동 설정 (Auto-configuration)」**
- 스타터가 라이브러리인지 의존성 묶음인지 헷갈린다 → **[boot-1.x](boot-1.x.md)의 「스타터 POM (Starter Dependencies)」**
- `java -jar`로 웹 서버가 뜨는 게 무슨 뜻인지 알고 싶다 → **[boot-1.x](boot-1.x.md)의 「내장 서블릿 컨테이너 (Embedded Tomcat/Jetty/Undertow)」**
- MVC와 WebFlux 중 무엇을 골라야 하는지 기준을 잡고 싶다 → **[boot-2.x](boot-2.x.md)의 「Spring WebFlux (리액티브 웹 스택)」**
- 메트릭을 Prometheus·Datadog에 어떻게 보내는지 궁금하다 → **[boot-2.x](boot-2.x.md)의 「Actuator 재설계 + Micrometer」**
- 2.x에서 3.x로 올리는 게 왜 그렇게 큰일인지 알고 싶다 → **[boot-3.x](boot-3.x.md)의 「Jakarta EE 9 (`javax` → `jakarta`)」**
- 네이티브 이미지가 무엇을 줄여 주는지 궁금하다 → **[boot-3.x](boot-3.x.md)의 「GraalVM 네이티브 이미지 1급 지원 (AOT)」**
- 블로킹 코드를 그대로 두고 동시성을 올리고 싶다 → **[boot-3.x](boot-3.x.md)의 「가상 스레드 (Virtual Threads, 3.2 / Java 21)」**
- 의존성이 왜 그렇게 무거워졌는지, 4.0이 어떻게 줄이는지 궁금하다 → **[boot-4.x](boot-4.x.md)의 「코드베이스 모듈화 (모놀리식 자동 설정 jar의 분리)」**
- 3.x에서 4.0으로 올리는 순서를 잡고 싶다 → **[boot-4.x](boot-4.x.md)의 「마이그레이션 관점 (3.x → 4.0)」**
- 코틀린 클래스에 `@Service`를 붙였는데 프록시가 안 된다 → **[kotlin-and-spring](kotlin-and-spring.md)의 「코틀린에서 Spring 어노테이션 사용 시 주의점 — final class 문제와 all-open」**
- `suspend`/`Flow`가 Reactor와 어떻게 이어지는지 알고 싶다 → **[kotlin-and-spring](kotlin-and-spring.md)의 「코루틴 지원 (suspend 함수, Spring 5.2+ / WebFlux 코루틴)」**
- 같은 코드를 자바와 코틀린으로 나란히 보고 싶다 → **[kotlin-and-spring](kotlin-and-spring.md)의 「자바 vs 코틀린: 같은 Spring 코드 비교」**
- 두 갈래 전체 지도를 한 번에 잡고 싶다 → **이 문서의 「전체 타임라인」 표 + 「한눈에」 도식**

# software-design/36-extension-points-and-plugins — 확장 지점과 플러그인: SPI·ServiceLoader·자동 설정 — 정리 (힌트)

## 해결하는 문제

결제 수단이 하나 늘 때마다 코어 코드를 고치고 다시 배포해야 한다.

```text
 확장 지점 없음                               확장 지점 있음
 class Checkout {                             코어:  interface PaymentMethod (공개 계약)
   switch (type) {                                   Checkout은 계약만 안다
     case CARD  -> card.pay(...);             외부:  card.jar   ── 구현 + 등록 파일
     case KAKAO -> kakao.pay(...);                   kakao.jar  ── 구현 + 등록 파일
     // 새 수단마다 여기를 고친다                 새 수단 = jar 하나 추가 (코어 재컴파일 없음)
   }
 }
```

- *확장 지점(extension point)*: 코어가 미리 열어 둔 자리. 계약(인터페이스)과 "구현을 찾는 방법"으로 이루어진다.
- *플러그인(plugin)*: 그 자리에 끼우는 구현. 코어와 따로 만들고 따로 배포할 수 있다.
- *SPI(Service Provider Interface)*: 코어가 공개하고 외부가 **구현하는** 인터페이스. 보통의 API(외부가 **호출하는** 인터페이스)와 방향이 반대다.

쉬운 예: 멀티탭은 콘센트 모양(계약)만 정한다. 어떤 가전을 꽂을지는 모른다.\
똑같은 구조다.\
실무 예: JDBC 드라이버(`java.sql.Driver`), Spring Boot 스타터(jar를 넣으면 자동 설정이 켜진다), IDE·빌드 도구 플러그인, 어노테이션 처리기([35-annotation-and-metadata-programming](../35-annotation-and-metadata-programming/2-summary.md)의 `META-INF/services/javax.annotation.processing.Processor`).

이 노트는 "찾는 방법" 네 가지를 다룬다. Java `ServiceLoader`, Spring Boot 자동 설정(조건부 빈), 이벤트 리스너, 그리고 그 바탕인 PoEAA의 Separated Interface·Plugin이다.

## 동작·원리

### 1. 뼈대 — Separated Interface와 Plugin

```text
   ┌──────────── 코어 모듈 ────────────┐         ┌──── 플러그인 모듈 ────┐
   │ Checkout ──uses──> «interface»    │ <─impl──│ CardPayment          │
   │                    PaymentMethod  │         │ META-INF/services/…  │
   └───────────────────────────────────┘         └──────────────────────┘
     컴파일 의존: 플러그인 → 코어 (화살표가 코어를 향한다)
     실행 연결:   설정·등록 파일이 "어떤 구현을 쓸지"를 정한다
```

- *Separated Interface*(Fowler, PoEAA): "Defines an interface in a separate package from its implementation." 인터페이스와 구현을 다른 패키지(모듈)에 둔다.
- *Plugin*(Fowler, PoEAA): "Links classes during configuration rather than compilation." 어떤 구현을 쓸지 컴파일이 아니라 설정 단계에서 연결한다.
- 의존 방향이 플러그인 → 코어다. 코어는 구현을 모른다. 이것이 DIP의 모듈 판이다([22-solid](../22-solid/2-summary.md), 원본 [engineering/solid-principles](../../engineering/solid-principles/2-summary.md)).

### 2. Java `ServiceLoader` — 등록 파일로 찾기

```text
 ServiceLoader.load(PaymentMethod.class)
   │ ① 클래스패스의 모든 jar에서 META-INF/services/pay.PaymentMethod 파일을 찾는다
   │      card.jar  → "card.CardPayment"
   │      kakao.jar → "kakao.KakaoPayment"
   │ ② 파일에 적힌 클래스 이름을 클래스패스 순서대로 모은다
   │ ③ 반복할 때 비로소 생성한다 (지연). stream()은 클래스만 보고 생성하지 않는다
   ▼
 Map<String, PaymentMethod> 레지스트리 (타입 이름 → 구현)
```

- JDK 21 `ServiceLoader` 문서: 제공자는 "lazily, that is, on demand" 로드·생성된다. `stream()`은 "인스턴스화하지 않고 검사·필터"할 수 있다.
- 제공자 조건(같은 문서): 서비스 인터페이스에 대입 가능해야 하고, public 무인자 생성자(provider constructor)나 모듈의 `provider()` 메서드가 있어야 한다. 아니면 `ServiceConfigurationError`.

### 실험 A: jar 추가만으로 기능 추가, 순서, 잘못된 제공자

코어(`app.jar`·`api.jar`)는 그대로 두고 클래스패스에 넣는 jar만 바꾼다.

```java
ServiceLoader<PaymentMethod> loader = ServiceLoader.load(PaymentMethod.class);
System.out.println("발견한 구현 클래스(인스턴스화 전): " +
    loader.stream().map(p -> p.type().getSimpleName()).toList());
Map<String, PaymentMethod> registry = new LinkedHashMap<>();   // 레지스트리: 타입 이름 → 구현
for (PaymentMethod m : loader) registry.putIfAbsent(m.type(), m);
```

(실험, JDK 21.0.12 temurin `--cpus=2`, `scratchpad/sd/35/e36/sl/`, 2026-10-02)

```text
== 1) api만
발견한 구현 클래스(인스턴스화 전): []
레지스트리: []
결제 수단 없음 → 기능 비활성
== 2) + card.jar
발견한 구현 클래스(인스턴스화 전): [CardPayment]
  (CardPayment 생성자 호출)
레지스트리: [CARD]
카드 승인 1000
== 3) + card.jar + kakao.jar (코어 재컴파일 없음)
발견한 구현 클래스(인스턴스화 전): [CardPayment, KakaoPayment]
  (CardPayment 생성자 호출)
  (KakaoPayment 생성자 호출)
레지스트리: [CARD, KAKAO]
카카오 결제 1000
== 4) 클래스패스 순서 반대
발견한 구현 클래스(인스턴스화 전): [KakaoPayment, CardPayment]
  (KakaoPayment 생성자 호출)
  (CardPayment 생성자 호출)
레지스트리: [KAKAO, CARD]
카카오 결제 1000
== 5) 잘못된 구현 jar
Exception in thread "main" java.util.ServiceConfigurationError: pay.PaymentMethod: broken.NotAPayment not a subtype
	at java.base/java.util.ServiceLoader.fail(ServiceLoader.java:593)
```

- 관찰 1 — jar만 바꿨는데 기능이 생겼다(1→2→3). 코어 재컴파일은 없었다.
- 관찰 2 — `stream()`의 `type()`은 생성자를 부르지 않았다. 생성자 출력은 반복할 때 나왔다(지연 생성).
- 관찰 3 — 발견 순서가 클래스패스 순서를 따랐다(3과 4). 같은 타입 이름을 내는 구현이 둘이면 `putIfAbsent` 레지스트리에서는 **먼저 온 쪽이 이긴다**. 순서에 기대는 설계는 깨지기 쉽다.
- 관찰 4 — 플러그인이 하나도 없으면 오류 없이 "기능 비활성"이다(1). 필수 플러그인이면 코어가 직접 검사해 실패시켜야 한다.
- 관찰 5 — 계약을 지키지 않은 제공자는 순회 중 `ServiceConfigurationError`로 실패했다.

### 3. Spring Boot 자동 설정 — 조건부 빈

```text
 기동
  │ ① 사용자 설정(@Configuration·컴포넌트 스캔)의 빈 정의를 먼저 등록한다
  │ ② 클래스패스의 META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports
  │    에 적힌 자동 설정 클래스를 읽는다
  │ ③ 조건을 평가한다 (술어)
  │      @ConditionalOnClass        그 클래스가 클래스패스에 있나
  │      @ConditionalOnProperty     설정 값이 맞나
  │      @ConditionalOnMissingBean  그 타입 빈이 아직 없나   ← 사용자가 정의하면 물러난다
  │ ④ 참인 것만 빈 정의로 등록한다
  ▼
 조건 평가 보고서 (--debug): Positive matches / Negative matches
```

- *자동 설정(auto-configuration)*: 스타터 jar에 들어 있는 `@AutoConfiguration` 클래스. 클래스패스·설정·기존 빈을 보고 기본 빈을 등록한다.
- *조건부 빈*: 조건(술어)이 참일 때만 등록되는 빈.
- Spring Boot 문서 「Creating Your Own Auto-configuration」:
  - 자동 설정은 imports 파일로만 로드해야 하고, 컴포넌트 스캔 대상이 되면 안 된다.
  - `@ConditionalOnBean`·`@ConditionalOnMissingBean`은 자동 설정에서만 쓰기를 권한다. 자동 설정은 사용자 빈 정의가 모두 등록된 **뒤에** 로드되기 때문이다.
  - `@Bean` 메서드에 붙은 조건의 대상 타입은 기본이 **메서드 반환 타입**이다.
  - 같은 문서는 반환 타입에 타입 정보를 최대한 담으라고(인터페이스보다 구현 클래스) 권한다. 조건 평가가 메서드 시그니처의 타입 정보만 쓰기 때문이다.
- 마지막 두 권고가 함께 있다는 점이 실험 B의 함정이다. 반환 타입을 구현 클래스로 하면 `@ConditionalOnMissingBean`은 그 구현 클래스만 찾는다.

### 실험 B: 자동 설정이 물러나는 경우와 충돌하는 경우

스타터 하나에 변형 넷을 두고(`variant` 속성으로 선택), 사용자 설정(`custom` 프로파일)은 `CustomPaymentClient`를 `paymentClient` 이름으로 등록한다.

```java
@AutoConfiguration
public class PaymentAutoConfiguration {
    // A: 반환 타입이 인터페이스
    @Bean @ConditionalOnProperty(name = "variant", havingValue = "A") @ConditionalOnMissingBean
    PaymentClient paymentClient() { return new DefaultPaymentClient(); }
    // B: 반환 타입이 구현 클래스 — 조건은 DefaultPaymentClient 타입만 찾는다
    @Bean @ConditionalOnProperty(name = "variant", havingValue = "B") @ConditionalOnMissingBean
    DefaultPaymentClient defaultPaymentClient() { return new DefaultPaymentClient(); }
    // D: 반환 타입은 구현 클래스, 조건 대상은 인터페이스로 명시
    @Bean @ConditionalOnProperty(name = "variant", havingValue = "D") @ConditionalOnMissingBean(PaymentClient.class)
    DefaultPaymentClient defaultPaymentClientD() { return new DefaultPaymentClient(); }
    // C: 조건 없음 + 사용자 빈과 같은 이름
    @Bean(name = "paymentClient") @ConditionalOnProperty(name = "variant", havingValue = "C")
    PaymentClient paymentClientC() { return new DefaultPaymentClient(); }
}
```

(실험, Spring Boot 3.5.6·Spring Framework 6.2.11, JDK 21.0.12 temurin `--cpus=2`, `scratchpad/sd/35/e36/boot/`, 2026-10-02 — 출력 일부 발췌, 전체는 `run-output.txt`)

```text
== A, 사용자 빈 없음
PaymentClient 빈 개수=1
주입된 구현=Default(자동 설정)
== A, 사용자 빈 있음
PaymentClient 빈 개수=1
주입된 구현=Custom(사용자 정의)
== B, 사용자 빈 있음(타입이 다름)
***************************
APPLICATION FAILED TO START
***************************
Description:
Parameter 1 of method show in app.App required a single bean, but 2 were found:
	- paymentClient: defined by method 'paymentClient' in class path resource [app/App$UserConfig.class]
	- defaultPaymentClient: defined by method 'defaultPaymentClient' in class path resource [starter/PaymentAutoConfiguration.class]
== D, 사용자 빈 있음(조건에 인터페이스 명시)
PaymentClient 빈 개수=1
주입된 구현=Custom(사용자 정의)
== D, 사용자 빈 없음
PaymentClient 빈 개수=1
주입된 구현=Default(자동 설정)
== C, 같은 이름, 기본 설정
***************************
APPLICATION FAILED TO START
***************************
Description:
The bean 'paymentClient', defined in class path resource [starter/PaymentAutoConfiguration.class], could not be registered. A bean with that name has already been defined in class path resource [app/App$UserConfig.class] and overriding is disabled.
== C, 같은 이름, overriding 허용
PaymentClient 빈 개수=1
주입된 구현=Default(자동 설정)
```

`--debug` 조건 평가 보고서(같은 환경):

```text
   PaymentAutoConfiguration#paymentClient:                         ← 변형 A, 사용자 빈 있음
      Did not match:
         - @ConditionalOnMissingBean (types: starter.PaymentClient; SearchStrategy: all) found beans of type 'starter.PaymentClient' paymentClient (OnBeanCondition)

   PaymentAutoConfiguration#defaultPaymentClient matched:          ← 변형 B, 사용자 빈 있음
      - @ConditionalOnProperty (variant=B) matched (OnPropertyCondition)
      - @ConditionalOnMissingBean (types: starter.DefaultPaymentClient; SearchStrategy: all) did not find any beans (OnBeanCondition)
```

- 관찰 1(A) — 사용자가 같은 타입 빈을 두자 자동 설정이 물러났다. 보고서에 이유가 그대로 나온다.
- 관찰 2(B) — 조건 대상이 `DefaultPaymentClient`라서 사용자의 `CustomPaymentClient`를 못 봤다. `PaymentClient` 빈이 둘이 되어 **기동 실패**했다.
- 관찰 3(D) — 조건 대상을 `PaymentClient.class`로 명시하자 B의 문제가 사라졌다. 반환 타입은 구현 클래스 그대로다.
- 관찰 4(C) — 이름이 같으면 Spring Boot 기본(`spring.main.allow-bean-definition-overriding=false`, 속성 문서)에서 기동이 실패했다. 덮어쓰기를 허용하자 **자동 설정 빈이 사용자 빈을 조용히 덮었다**. 자동 설정이 사용자 설정보다 뒤에 등록되기 때문이다.

### 4. 이벤트 리스너 — 발행자가 구독자를 모르는 확장 지점

```text
 OrderService ── publishEvent(OrderPlaced) ──> ApplicationEventMulticaster
                                                 ├─> @EventListener 포인트 적립
                                                 ├─> @EventListener 알림 발송
                                                 └─> (새 기능 = 리스너 빈 하나 추가)
```

- 발행자 코드를 고치지 않고 반응을 늘린다. 레지스트리는 "이벤트 타입 → 리스너 목록"이다.
- Spring Framework 문서: 리스너는 기본적으로 **동기**로 받고, `publishEvent()`는 모든 리스너가 끝날 때까지 막힌다. 발행자에게 트랜잭션 컨텍스트가 있으면 리스너도 그 안에서 돈다. 리스너 하나의 예외·지연이 발행자에게 그대로 돌아온다(이 노트에서 실행하지는 않았다).

### 5. 무엇을 고르나

| 방식 | 찾는 시점·주체 | 선택 기준 | 실패 형태 |
|---|---|---|---|
| `ServiceLoader` | 실행 중, JDK | 등록 파일 + 클래스패스 순서 | 0개면 조용히 비활성, 잘못된 제공자는 `ServiceConfigurationError` |
| Spring Boot 자동 설정 | 기동 중, Boot | 조건(클래스·속성·기존 빈) | 빈 충돌로 기동 실패, 덮어쓰기 허용 시 조용한 교체 |
| 이벤트 리스너 | 기동 중 등록, 발행 때 호출 | 이벤트 타입 | 리스너 예외가 발행자로 전파(동기 기본) |
| DI 직접 조립 | 기동 중, 컴포지션 루트 | 코드 | 컴파일 오류(가장 이르게 드러남) |

## 쓰이는 자료구조·알고리즘

- **레지스트리(이름 → 구현 맵)**: 실험 A의 `LinkedHashMap<String, PaymentMethod>`, Spring의 빈 정의 레지스트리(이름 → 정의). 키 충돌 정책(먼저 온 쪽·나중 온 쪽·실패)이 설계의 핵심이다(실험 A 관찰 3, 실험 B의 C).
- **조건 평가(술어)**: 자동 설정은 조건 술어들의 AND가 참일 때만 등록한다. 평가 순서가 결과를 바꾼다(사용자 정의 → 자동 설정 순).
- **지연 반복자(lazy iterator)**: `ServiceLoader`는 꺼낼 때 로드·생성한다. 필요 없는 제공자의 생성 비용을 피한다.
- **관찰자(Observer) 목록**: 이벤트 타입 → 리스너 리스트. GoF Observer([engineering/design-patterns-gof](../../engineering/design-patterns-gof/2-summary.md)).
- **의존 그래프 방향**: 플러그인 → 코어. 순환이 생기면 독립 배포가 깨진다([39-component-principles](../39-component-principles/2-summary.md)).

## 적용 — 풀어나가는 법

1. **확장이 실제로 반복되는 축인지 먼저 본다.** 결제 수단·저장소 드라이버·포맷처럼 종류가 계속 는다면 확장 지점을 둔다. 한 번뿐이면 직접 조립이 싸다(YAGNI).
2. **계약을 코어(별도 모듈)에 둔다.** 플러그인은 계약 모듈에만 의존한다. 추상 메서드 추가 같은 계약 변경은 그 계약을 구현한 플러그인을 깨므로(실험 C) 버전을 둔다.
3. **찾는 방법을 고른다.** 프레임워크 밖 라이브러리 → `ServiceLoader`. Spring Boot 스타터 → 자동 설정 + imports 파일. 앱 안 반응 추가 → 이벤트.
4. **레지스트리의 충돌 정책을 명시한다.** 같은 키가 두 번 오면 실패시키는 편이 순서 의존보다 안전하다.
   ```java
   for (PaymentMethod m : loader) {
       PaymentMethod prev = registry.putIfAbsent(m.type(), m);
       if (prev != null) throw new IllegalStateException("중복 결제 수단 " + m.type()
           + ": " + prev.getClass() + " vs " + m.getClass());
   }
   ```
5. **자동 설정을 쓰는 쪽**: 기본을 바꾸고 싶으면 같은 **타입**의 빈을 정의한다(이름을 맞추는 방식은 덮어쓰기 설정에 따라 결과가 바뀐다). 결과는 `--debug` 보고서로 확인한다.
6. **자동 설정을 만드는 쪽**: `@ConditionalOnMissingBean`의 대상 타입을 사용자가 정의할 타입(보통 인터페이스)으로 명시한다(실험 B의 D). imports 파일에만 등록하고 스캔 대상 패키지에 두지 않는다.

진단:

```bash
java -jar app.jar --debug                          # 조건 평가 보고서 (Positive/Negative matches)
curl localhost:8080/actuator/conditions            # actuator 의존성 + management.endpoints.web.exposure.include=conditions 필요 (이 노트에서는 실행 안 함)
unzip -l some-starter.jar | grep -E 'META-INF/(services|spring)/'   # jar가 무엇을 등록하나
```

- Actuator 엔드포인트는 Spring Boot 기본값으로 HTTP·JMX에 `health`만 노출된다(Boot 문서 "Exposing Endpoints"). `conditions` 보고서에는 빈 구성 정보가 들어 있으므로 외부에 열지 않는다.

## 장애 시나리오와 대처

### 1. 자동 설정이 의도치 않은 빈을 덮어써 엉뚱한 구현이 주입된다 (⚠ 커리큘럼)

- 현상: 직접 정의한 `paymentClient`를 쓰는 줄 알았는데 기본 구현이 동작한다.
- 보이는 형태: 오류 없음. 결과만 다르다(실험 B의 C + 덮어쓰기 허용: `주입된 구현=Default(자동 설정)`). 로그 레벨에 따라 덮어쓰기 기록이 안 보일 수 있다.
- 원인: 같은 이름 + `spring.main.allow-bean-definition-overriding=true`. 자동 설정이 사용자 정의보다 뒤에 등록되어 이긴다.
- 대처: 덮어쓰기 허용을 끈다(Boot 기본 false). 이름이 아니라 타입으로 대체한다. 자동 설정 제작자는 `@ConditionalOnMissingBean`을 붙인다.

### 2. 같은 타입 빈 충돌로 기동 실패 (⚠ 커리큘럼)

- 현상: 스타터 버전을 올리거나 사용자 빈을 하나 추가한 뒤 기동이 안 된다.
- 보이는 형태: `APPLICATION FAILED TO START` … `required a single bean, but 2 were found`(실험 B의 B).
- 원인: 자동 설정의 조건 대상이 구현 클래스라 사용자의 다른 구현을 보지 못했다.
- 대처: 사용 쪽은 `@Primary`·`@Qualifier`로 급히 막는다(실패 분석기 Action 문구 그대로). 근본은 자동 설정의 `@ConditionalOnMissingBean(인터페이스.class)`(변형 D). `--debug` 보고서로 어떤 조건이 무엇을 찾았는지 본다.

### 3. 클래스패스 순서에 따라 다른 플러그인이 선택된다

- 현상: 로컬에서는 A 구현, 운영 이미지에서는 B 구현이 쓰인다.
- 보이는 형태: 같은 코드인데 결과가 환경마다 다르다. 의존성 트리에 같은 SPI 구현이 둘.
- 원인: `ServiceLoader` 발견 순서가 클래스패스 순서를 따르고(실험 A 3·4), 레지스트리가 "먼저 온 쪽"을 고른다.
- 대처: 중복 키를 실패로 바꾼다(적용 4). 선택 기준을 설정 값으로 명시한다. 빌드에서 중복 구현 의존성을 뺀다.

### 4. 플러그인이 하나도 없는데 조용히 기능이 꺼진다

- 현상: 배포 후 특정 기능만 동작하지 않는다.
- 보이는 형태: 오류 없음. 레지스트리가 비어 있음(실험 A 1: `결제 수단 없음 → 기능 비활성`).
- 원인: 플러그인 jar가 패키징에서 빠졌다. 또는 여러 jar를 하나로 합칠 때(셰이딩) 같은 이름의 `META-INF/services` 파일이 하나만 남았다.
  - Maven Shade 플러그인 문서: `ServicesResourceTransformer`는 `META-INF/services` 항목을 합친다(merges). 이 변환기 없이 합쳤을 때의 결과는 이 노트에서 실험하지 않았다 [?].
- 대처: 필수 확장 지점은 기동 시 "최소 1개" 검사로 실패시킨다. 패키징 후 `unzip -l`로 등록 파일을 확인한다.

### 5. 계약 변경이 모든 플러그인을 깨뜨린다

- 현상: 인터페이스에 메서드 하나를 추가했더니 외부 플러그인을 쓰는 기능이 실패한다.
- 보이는 형태: 이미 컴파일된 플러그인은 로드·생성까지는 되고, 새 메서드를 부르는 순간 실패한다. 다시 컴파일하면 컴파일 오류다.

(실험 C, JDK 21.0.12 temurin `--cpus=2`, `scratchpad/sd/35/e36/evo/`, 계약에 `refund(long)` 추가, 2026-10-02)

```text
== 옛 계약으로 컴파일된 card.jar + 새 계약
  (CardPayment 생성자 호출)
Exception in thread "main" java.lang.AbstractMethodError: Receiver class card.CardPayment does not define or inherit an implementation of the resolved method 'abstract java.lang.String refund(long)' of interface pay.PaymentMethod.
== card 소스를 새 계약으로 다시 컴파일
/w/e36/sl/card/card/CardPayment.java:2: error: CardPayment is not abstract and does not override abstract method refund(long) in PaymentMethod
```

- 원인: SPI는 외부가 구현하는 인터페이스라 메서드 추가도 깨는 변경이다.
- 대처: `default` 메서드로 추가, 새 인터페이스(`PaymentMethodV2`)로 분리, 계약 버전 표시.

## 핵심 문장

- 확장 지점은 계약(인터페이스)과 구현을 찾는 방법이다. 의존은 플러그인 → 코어로 흐르고 코어는 구현을 모른다.
- `ServiceLoader`는 등록 파일을 클래스패스 순서대로 읽어 지연 생성한다. 실험에서 jar 추가만으로 기능이 늘었고, 순서를 바꾸자 발견 순서도 바뀌었다.
- Spring Boot 자동 설정은 사용자 빈 등록 뒤에 조건을 평가한다. `@ConditionalOnMissingBean`의 대상 타입은 기본이 반환 타입이다.
- 실험에서 반환 타입을 구현 클래스로 둔 자동 설정은 사용자 빈을 못 보고 같은 타입 빈 둘로 기동 실패했다. 조건 대상을 인터페이스로 명시하자 물러났다.
- 같은 이름 빈은 Boot 기본에서 기동 실패하고, 덮어쓰기를 허용하면 자동 설정 빈이 사용자 빈을 조용히 덮었다.

## 관련 주제·근거

- 선행
  - [25-dependency-injection-and-composition-root](../25-dependency-injection-and-composition-root/2-summary.md), [22-solid](../22-solid/2-summary.md), [32-inversion-of-control-and-framework-flow](../32-inversion-of-control-and-framework-flow/2-summary.md). SOLID 원본은 [engineering/solid-principles](../../engineering/solid-principles/2-summary.md)
- 연결
  - [35-annotation-and-metadata-programming](../35-annotation-and-metadata-programming/2-summary.md) — 어노테이션 처리기도 `META-INF/services`로 찾는 플러그인이다
  - [37-architecture-styles](../37-architecture-styles/2-summary.md) — 마이크로커널(코어 + 플러그인) 스타일
  - [39-component-principles](../39-component-principles/2-summary.md) — 의존 방향과 안정성(플러그인 → 안정된 계약)
  - [engineering/design-patterns-gof](../../engineering/design-patterns-gof/2-summary.md) — Observer·Strategy
- 문서·소스
  - JDK 21 `java.util.ServiceLoader`(지연 로드, `stream()`, provider constructor, `ServiceConfigurationError`) <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/ServiceLoader.html>
  - Spring Boot 「Creating Your Own Auto-configuration」(imports 파일, 조건은 자동 설정에서만, 반환 타입이 조건 대상, 반환 타입에 타입 정보) <https://docs.spring.io/spring-boot/reference/features/developing-auto-configuration.html>
  - Spring Boot 속성 `spring.main.allow-bean-definition-overriding`(기본 false) <https://docs.spring.io/spring-boot/appendix/application-properties/index.html>
  - Spring Framework 「Additional Capabilities of the ApplicationContext」 — 이벤트 리스너는 기본 동기 <https://docs.spring.io/spring-framework/reference/core/beans/context-introduction.html>
  - Martin Fowler, PoEAA 카탈로그 Plugin <https://martinfowler.com/eaaCatalog/plugin.html> · Separated Interface <https://martinfowler.com/eaaCatalog/separatedInterface.html> — 한 줄 정의와 카탈로그 분류(Base Patterns)만 확인, 책 본문·장 번호는 열람하지 못했다 [?]
- 실험 목록 (JDK 21.0.12 temurin 컨테이너 `--cpus=2`, 2026-10-02)
  - A `scratchpad/sd/35/e36/sl/` — `ServiceLoader`: jar 추가로 기능 추가, 지연 생성, 클래스패스 순서, `not a subtype`
  - B `scratchpad/sd/35/e36/boot/run.sh` — Spring Boot 3.5.6 자동 설정 변형 A·B·C·D, `--debug` 조건 보고서. jar는 Maven Central에서 받음(`spring-boot-starter` 3.5.6과 의존성)
  - C `scratchpad/sd/35/e36/evo/` — 계약에 메서드 추가 시 옛 플러그인 `AbstractMethodError`, 재컴파일 오류

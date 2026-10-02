# software-design/36-extension-points-and-plugins — 정답

## 정답

### 1. 확장 지점이 없을 때

- 코어의 `switch`(또는 if 사슬)에 분기를 추가하고, 코어를 다시 컴파일·배포한다. 같은 분기가 여러 곳에 있으면 모두 고친다.
- API는 외부가 **호출하는** 인터페이스, SPI는 코어가 공개하고 외부가 **구현하는** 인터페이스다. 코어는 SPI 구현을 모른 채 찾아서 부른다.

### 2. Separated Interface·Plugin

```text
 [코어 모듈]  Checkout ──uses──> «interface» PaymentMethod
                                         ▲
                                         │ implements (컴파일 의존: 플러그인 → 코어)
 [플러그인 모듈]                    CardPayment + 등록 파일
```

- Separated Interface: 인터페이스를 구현과 다른 패키지에 둔다(Fowler 카탈로그 정의).
- Plugin: 구현 연결을 컴파일이 아니라 설정 단계에서 한다.
- 컴파일 의존은 플러그인 → 코어(계약)를 향한다. 코어는 플러그인을 모른다.

### 3. jar를 늘려 가며 실행

(실험 A, JDK 21.0.12, 2026-10-02)

```text
== 1) api만
레지스트리: []
결제 수단 없음 → 기능 비활성
== 2) + card.jar
레지스트리: [CARD]
== 3) + card.jar + kakao.jar (코어 재컴파일 없음)
레지스트리: [CARD, KAKAO]
```

- 1은 오류 없이 기능 비활성, 2·3은 jar 추가만으로 수단이 늘었다.
- `stream()`으로 `type()`만 볼 때는 생성자가 불리지 않았다. 생성자 출력은 반복(인스턴스화) 때 나왔다. JDK 문서도 `stream()`은 인스턴스화 없이 검사할 수 있다고 한다.

### 4. 클래스패스 순서

```text
== 4) 클래스패스 순서 반대
발견한 구현 클래스(인스턴스화 전): [KakaoPayment, CardPayment]
레지스트리: [KAKAO, CARD]
```

- 발견 순서가 클래스패스 순서를 따라 바뀌었다.
- `putIfAbsent` 레지스트리에서 같은 키를 내는 구현이 둘이면 먼저 발견된 쪽이 선택된다. 환경마다 클래스패스 순서가 다르면 다른 구현이 쓰인다. 중복 키는 실패로 만드는 편이 안전하다.

### 5. 자동 설정의 등록 시점

- 자동 설정은 사용자 빈 정의가 모두 등록된 **뒤에** 로드된다(Spring Boot 문서 「Creating Your Own Auto-configuration」).
- `@ConditionalOnMissingBean`은 "지금까지 등록된 빈 정의"를 보고 판단한다. 자동 설정에서 쓰면 사용자 빈을 다 본 뒤 평가되는 것이 보장된다. 일반 설정에서는 처리 순서에 따라 아직 등록되지 않은 빈을 못 볼 수 있어서 문서가 자동 설정에서만 쓰기를 권한다.

### 6. 반환 타입이 구현 클래스인 조건부 빈

(실험 B 변형 B, Spring Boot 3.5.6)

```text
APPLICATION FAILED TO START
Parameter 1 of method show in app.App required a single bean, but 2 were found:
	- paymentClient: defined by method 'paymentClient' in class path resource [app/App$UserConfig.class]
	- defaultPaymentClient: defined by method 'defaultPaymentClient' in class path resource [starter/PaymentAutoConfiguration.class]
```

- 조건 대상은 기본이 반환 타입이라 `DefaultPaymentClient`만 찾았고(`--debug`: `types: starter.DefaultPaymentClient ... did not find any beans`), 사용자의 `CustomPaymentClient`를 못 봤다. `PaymentClient` 빈이 둘이 되어 기동 실패.
- 고치기: `@ConditionalOnMissingBean(PaymentClient.class)`로 대상을 명시(변형 D: 사용자 빈 있으면 Custom, 없으면 Default). 사용 쪽 임시 대처는 `@Primary`·`@Qualifier`.

### 7. 같은 이름 빈

(실험 B 변형 C)

- Boot 기본(`spring.main.allow-bean-definition-overriding=false`): `The bean 'paymentClient' ... could not be registered. ... overriding is disabled.` 기동 실패.
- 덮어쓰기 허용: `주입된 구현=Default(자동 설정)`. 자동 설정이 뒤에 등록되어 사용자 빈을 **조용히** 덮었다.

### 8. 이벤트 리스너

- 발행자는 이벤트만 내고 누가 받는지 모른다. 리스너 빈을 추가하면 발행자 코드를 고치지 않고 반응이 늘어난다(이벤트 타입 → 리스너 목록 레지스트리).
- Spring Framework 문서: 리스너는 기본 동기로 받고 `publishEvent()`는 모든 리스너가 끝날 때까지 막힌다. 발행자에게 트랜잭션 컨텍스트가 있으면 리스너도 그 안에서 돈다. 그래서 리스너의 지연은 발행자의 지연이 되고, 리스너 예외는 발행자 쪽으로 돌아온다. 이 노트에서는 실행으로 확인하지 않았다.

### 9. 조용히 꺼진 기능

- 원인 1: 플러그인 jar가 배포물에서 빠졌다. 레지스트리가 비어도 오류가 없다(실험 A 1).
- 원인 2: 여러 jar를 합칠 때 `META-INF/services` 파일이 합쳐지지 않았다(Maven Shade는 `ServicesResourceTransformer`로 합친다 — 문서 확인, 실험은 안 함).
- 확인: `unzip -l app.jar | grep META-INF/services`, 기동 로그에 발견한 구현 목록을 남긴다. 필수 확장 지점은 "최소 1개" 검사로 기동을 실패시킨다.

### 10. SPI에 메서드 추가

(실험 C, JDK 21.0.12)

```text
  (CardPayment 생성자 호출)
Exception in thread "main" java.lang.AbstractMethodError: Receiver class card.CardPayment does not define or inherit an implementation of the resolved method 'abstract java.lang.String refund(long)' of interface pay.PaymentMethod.
```

- 옛 계약으로 컴파일된 플러그인은 로드·생성까지 되고, 새 메서드를 **부르는 순간** `AbstractMethodError`가 난다. 플러그인을 새 계약으로 다시 컴파일하면 `does not override abstract method refund(long)` 컴파일 오류.
- 피하기: `default` 메서드로 추가, 새 인터페이스로 분리, 계약 버전을 둔다.

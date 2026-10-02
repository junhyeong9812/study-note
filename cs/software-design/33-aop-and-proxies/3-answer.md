# software-design/33-aop-and-proxies — 정답

## 정답

### 1. 흩어짐과 엉킴

- *흩어짐(scattering)*: 같은 부가 기능 코드가 N개 메서드에 복사된다. 정책이 바뀌면 N곳을 고친다.
- *엉킴(tangling)*: 한 메서드에 본업과 부가 기능이 섞여 읽기 어렵다. Kiczales 외(ECOOP 1997)는 이런 관심사가 기능 분해를 "가로지른다(cross-cut)"고 불렀다.
- AOP는 부가 기능을 애스펙트 한 곳에 쓰고, 어디에 끼울지는 포인트컷으로 정한다. Spring AOP는 그 결과를 빈마다 프록시 하나와 그 안의 인터셉터 목록으로 실현한다.

### 2. 두 프록시와 선택 규칙

```text
 JDK:   «interface» Greeter ◁── $Proxy19 ─위임─> GreeterImpl     (인터페이스 구현)
 CGLIB: GreeterImpl ◁── GreeterImpl$$SpringCGLIB$$0               (서브클래스, override)
```

- Spring 6.2 `DefaultAopProxyFactory`: `optimize`·`proxyTargetClass=true`이거나 사용자 인터페이스가 없으면 CGLIB(대상 클래스가 없거나 인터페이스·람다·JDK 프록시면 JDK). 그 밖은 JDK.
- `@EnableAspectJAutoProxy`의 `proxyTargetClass` 기본은 false.
- Spring Boot는 기본으로 CGLIB을 쓴다. `spring.aop.proxy-target-class=false`로 JDK 프록시로 바꾼다(Spring Boot 3.5 문서).

### 3. JDK 프록시와 구현 타입 조회

(실험 B, Spring Framework 6.2.11, 2026-10-02)

```text
  class=jdk.proxy1.$Proxy19
  getBean(GreeterImpl.class) -> NoSuchBeanDefinitionException
  getBean("greeter", GreeterImpl.class) -> BeanNotOfRequiredTypeException
```

- 컨테이너에 있는 것은 `Greeter`를 구현한 프록시다. `GreeterImpl` 타입이 아니다.
- 타입으로 찾으면 맞는 빈이 없고, 이름으로 찾으면 타입이 다르다.

### 4. 자기 호출

(실험 C1·C2)

```text
  C1 s.inner() 직접 (프록시 경유):
    [advice] -> inner
    = inner
  C2 s.outer() → this.inner() (자기 호출):
    = outer>inner
```

- `proxy.inner()`는 프록시를 거쳐 어드바이스가 실행됐다.
- `proxy.outer()` 안의 `this.inner()`는 `this`가 진짜 객체라 프록시를 우회했다. 에러 없이 어드바이스만 빠졌다.
- JDK·CGLIB 공통이다. AspectJ 위빙은 바이트코드에 넣으므로 이 문제가 없다(Spring 문서).

### 5. final 메서드와 final 클래스

(실험 C3·D)

```text
  C3 s.finalMethod() (final 메서드):
    -> NullPointerException: Cannot invoke "exp33.Main$Repo.name()" because "this.repo" is null
  BeanCreationException / root: IllegalArgumentException: Cannot subclass final class exp33.Main$FinalService
```

- final 메서드: CGLIB 서브클래스가 override하지 못해 어드바이스가 빠진다. 호출은 진짜 객체로 가지 않고 프록시 인스턴스에서 본문이 돈다. 프록시 인스턴스는 Objenesis로 만들어 생성자가 안 불렸으므로 `repo`가 null이다 → NPE.
- Spring 6.2.11 `CglibAopProxy` 소스는 이 경우를 DEBUG 로그로 경고한다("might lead to NPEs against uninitialized fields in the proxy instance").
- final 클래스: 서브클래스를 못 만들어 빈 생성이 실패하고 애플리케이션이 뜨지 않는다.

### 6. 재시도·트랜잭션 순서

(실험 E)

- (Retry 1, Tx 2): 재시도가 바깥. 시도마다 `tx#1`·`tx#2` — 트랜잭션 **2번**, 첫 시도는 롤백.
- (Retry 2, Tx 1): 트랜잭션이 바깥. `tx#1` **1번** 안에서 시도 1·2가 모두 실행.
- 실제 DB면 두 번째 경우 첫 시도의 쓰기가 남은 채 재시도된다. 또 첫 시도 안에서 부른 다른 `@Transactional` 메서드(참여 트랜잭션)가 예외로 끝나 rollback-only가 표시됐다면, 재시도가 성공해도 커밋에서 `UnexpectedRollbackException`이 날 수 있다(database/24). 재시도 애스펙트가 삼킨 예외는 바깥 트랜잭션 인터셉터가 보지 못해 그 자체로는 롤백을 일으키지 않는다.
- Spring에서는 값이 작을수록 우선순위가 높고 들어갈 때 먼저(바깥) 실행된다. 서로 다른 애스펙트에 순서를 주지 않으면 순서는 정해지지 않는다.

### 7. TS 데코레이터

(실험 F, TypeScript 7.0.2 `--target ES2022`)

```text
  적용: @retry → pay
  적용: @tx → pay
    tx 들어감
    retry 들어감
...
== 호출 outer() → this.inner()
    log 들어감
    audit 들어감
```

- 위에 쓴 `@tx`가 바깥이다. 평가는 위→아래, 적용은 아래→위라 나중에 적용된 `tx`가 `retry`로 감싼 함수를 다시 감싼다.
- `this.inner()`의 `audit`도 실행됐다. 데코레이터가 클래스 정의 시점에 프로토타입의 메서드를 감싼 함수로 **교체**하기 때문이다. Spring AOP는 객체 바깥에 대리 객체를 세우므로 `this` 호출을 못 본다.

### 8. 특정 메서드만 캐시 누락 + NPE

- 의심: 그 메서드가 `final`이다(CGLIB 프록시가 override 못 함). 같은 증상의 다른 원인은 자기 호출(NPE는 없고 누락만)과 private 메서드.
- 확인
  - 소스에서 `final` 여부를 본다.
  - `org.springframework.aop.framework.CglibAopProxy`를 DEBUG로 두고 기동해 "Final method [...] cannot get proxied via CGLIB" 줄을 찾는다.
  - NPE 메시지가 `because "this.xxx" is null`이고 그 필드가 생성자 주입이면 프록시 인스턴스에서 본문이 돈 것이다.
- 대처: final을 뗀다. 또는 메서드를 인터페이스에 올리고 JDK 프록시로 만든다. 회귀를 막으려고 "어드바이스가 실제로 실행됐는가"를 확인하는 테스트를 둔다.

# AuthorizationManagerBeforeMethodInterceptor.invoke

상위: [메서드 보안](../README.md)

AOP 인터셉터 체인에서 이 클래스가 하는 일이다. 본문은 한 줄이고 실제 로직은 같은 클래스 아래쪽의 private `attemptAuthorization`(L248)에 있다.

## 위치

`core` / `org.springframework.security.authorization.method` / `AuthorizationManagerBeforeMethodInterceptor.java` L195-L198 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/core/src/main/java/org/springframework/security/authorization/method/AuthorizationManagerBeforeMethodInterceptor.java#L195-L198))

## 실제 코드

```java
// AuthorizationManagerBeforeMethodInterceptor.java L195-L198
@Override
public @Nullable Object invoke(MethodInvocation mi) throws Throwable {
    return attemptAuthorization(mi);
}
```

이 클래스가 구현하는 계약이 특이하다.

`core` / `org.springframework.security.authorization.method` / `AuthorizationAdvisor.java` L35-L35 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/core/src/main/java/org/springframework/security/authorization/method/AuthorizationAdvisor.java#L35-L35))

```java
// AuthorizationAdvisor.java L35-L35
public interface AuthorizationAdvisor extends Ordered, MethodInterceptor, PointcutAdvisor, AopInfrastructureBean {
```

## 동작 흐름

```text
 invoke(mi)
 |
 +-- L197 attemptAuthorization(mi) 에 그대로 위임한다
```

```text
 한 클래스가 네 가지를 겸한다

 AuthorizationAdvisor extends
     Ordered                 순서를 안다
     MethodInterceptor       가로채서 일한다
     PointcutAdvisor         어디에 붙을지 안다
     AopInfrastructureBean   자신은 프록시 대상이 아니다

 보통 AOP 에서는 Advisor(어디에) 와 Advice(무엇을) 가 나뉘지만
 여기서는 한 객체가 둘 다 한다

 AopInfrastructureBean 의 javadoc 상 의미는
 "포인트컷이 매치해도 자동 프록시 대상이 아니다"라는 표시다
```

```text
 포인트컷이 애노테이션을 가리킨다

 설정이 실제로 부르는 것은 AuthorizationManager 를 받는 오버로드다 (L110-116)
   AuthorizationMethodPointcuts.forAnnotations(PreAuthorize.class)
   setOrder(AuthorizationInterceptorsOrder.PRE_AUTHORIZE.getOrder())

 즉 @PreAuthorize 가 붙은 메서드에만 이 인터셉터가 붙는다

 순서는 팩토리가 기본값을 넣고,
 설정이 @EnableMethodSecurity(offset=...) 만큼 더해 덮어쓴다
 (PrePostMethodSecurityConfiguration L204-211, offset 기본 0)
```

## 결과가 쓰이는 곳

```text
 위임 구조
      --> invoke 는 계약을 만족시키는 껍데기다
      --> attemptAuthorization 의 호출처는 이 invoke 하나뿐이다

 포인트컷
      --> 자동 프록시 생성기가 이 값으로 "이 빈을 감쌀까"를 정한다
      --> @PreAuthorize 가 하나도 없는 빈에는 이 인터셉터가 붙지 않는다
          (다른 어드바이저 때문에 프록시 자체는 만들어질 수 있다)

 order
      --> 여러 보안 인터셉터가 한 메서드에 붙을 때의 순서다
      --> AuthorizationInterceptorsOrder 가 전체 순번표를 들고 있다
```

## 하위 메서드

- [01 AuthorizationManagerBeforeMethodInterceptor.attemptAuthorization](01_AuthorizationManagerBeforeMethodInterceptor.attemptAuthorization/README.md)

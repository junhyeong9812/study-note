# AuthorizationAdvisor

상위: [spi](../README.md)

메서드가 하나도 없다. 네 인터페이스를 묶기만 하는 표식 인터페이스다.

## 위치

`core` / `org.springframework.security.authorization.method` / `AuthorizationAdvisor.java` L35-L37 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/core/src/main/java/org/springframework/security/authorization/method/AuthorizationAdvisor.java#L35-L37))

## 실제 코드

```java
// AuthorizationAdvisor.java L35-L37
public interface AuthorizationAdvisor extends Ordered, MethodInterceptor, PointcutAdvisor, AopInfrastructureBean {

}
```

## 흐름에서 불리는 자리

```text
 빈 생성 시점
   자동 프록시 생성기가 PointcutAdvisor 인 빈을 찾는다
   이 인터페이스가 PointcutAdvisor 를 상속하므로 후보가 된다

 호출 시점
   MethodInterceptor 로서 인터셉터 체인에 들어간다
```

- [AuthorizationManagerBeforeMethodInterceptor.invoke](../../02_AuthorizationManagerBeforeMethodInterceptor.invoke/README.md)

## 구현 계층

```text
 AuthorizationAdvisor
   +-- AuthorizationManagerBeforeMethodInterceptor   @PreAuthorize
   +-- AuthorizationManagerAfterMethodInterceptor    @PostAuthorize
   +-- PreFilterAuthorizationMethodInterceptor       @PreFilter
   +-- PostFilterAuthorizationMethodInterceptor      @PostFilter
   +-- AuthorizeReturnObjectMethodInterceptor        반환값에 프록시를 씌운다
   +-- DeferringMethodInterceptor                   config 모듈의 래퍼
   |     설정이 @Bean 으로 내놓는 것은 실제로 이것이다
   |     자동 프록시 생성기가 보는 어드바이저도 이 래퍼다
   +-- (리액티브 변형들, AuthorizationAdvisorProxyFactory 내부 구현)
   +-- (사용자 구현)
```

## 결과가 쓰이는 곳

```text
 네 계약을 겸하는 구조
      --> PointcutAdvisor    어디에 붙을지
      --> MethodInterceptor  붙어서 무엇을 할지
      --> Ordered            여러 보안 인터셉터 사이의 순서
      --> AopInfrastructureBean  자신은 프록시 대상이 아님

 AopInfrastructureBean 의 역할
      --> javadoc 상 "포인트컷이 매치해도 자동 프록시 대상이 아니다"라는 표시다
      --> 다만 PointcutAdvisor 인 것만으로도 이미 대상에서 빠지므로
          이 표시가 결정적 사유는 아니다

 메서드가 없다는 점
      --> 새 계약을 더하지 않는다. 조합을 이름 붙인 것이다
      --> 그래서 이 타입 하나로 "보안 어드바이저"를 골라낼 수 있다
```

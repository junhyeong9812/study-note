# MethodAuthorizationDeniedHandler

상위: [spi](../README.md)

거부됐을 때 무엇을 돌려줄지 정한다. 웹 인가에는 없는 선택지다.

## 위치

`core` / `org.springframework.security.authorization.method` / `MethodAuthorizationDeniedHandler.java` L32-L63 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/core/src/main/java/org/springframework/security/authorization/method/MethodAuthorizationDeniedHandler.java#L32-L63))

## 실제 코드

```java
// MethodAuthorizationDeniedHandler.java L32-L63 (javadoc 생략)
public interface MethodAuthorizationDeniedHandler {

    @Nullable Object handleDeniedInvocation(MethodInvocation methodInvocation, AuthorizationResult authorizationResult);

    default @Nullable Object handleDeniedInvocationResult(MethodInvocationResult methodInvocationResult,
            AuthorizationResult authorizationResult) {
        return handleDeniedInvocation(methodInvocationResult.getMethodInvocation(), authorizationResult);
    }

}
```

## 흐름에서 불리는 자리

```text
 AuthorizationManagerBeforeMethodInterceptor
   L255 / L263 handle(mi, result)
   L273-276 proceed 중에 거부 예외가 나온 경우
```

- [AuthorizationManagerBeforeMethodInterceptor.attemptAuthorization](../../02_AuthorizationManagerBeforeMethodInterceptor.invoke/01_AuthorizationManagerBeforeMethodInterceptor.attemptAuthorization/README.md)

## 구현 계층

```text
 MethodAuthorizationDeniedHandler
 전용 핸들러 셋
   +-- ThrowingMethodAuthorizationDeniedHandler      예외를 던진다. 기본값
   +-- NullReturningMethodAuthorizationDeniedHandler null 을 돌려준다
   |     단 결과가 AuthorizationDeniedException 자체이면 그것을 다시 던진다
   |     proceed 중 거부 경로가 그 갈래를 탄다
   +-- ReflectiveMethodAuthorizationDeniedHandler    package-private
         @HandleAuthorizationDenied 가 지정한 핸들러 클래스를
         리플렉션으로 만들어 위임한다

 인가 매니저가 겸업하는 여섯
   PreAuthorize / PostAuthorize 의 명령형과 리액티브 매니저,
   그리고 Observation 매니저 둘이 이 인터페이스도 구현한다

   +-- (사용자 구현)
```

## 결과가 쓰이는 곳

```text
 반환값이 그대로 호출자에게 간다
      --> 예외 대신 빈 값이나 마스킹된 값을 돌려줄 수 있다
      --> 메서드에 반환 타입이 있어서 가능한 선택지다
      --> 웹 인가는 응답을 쓰는 것뿐이라 이런 갈래가 없다

 handleDeniedInvocationResult
      --> default 메서드로, 기본은 handleDeniedInvocation 에 위임한다
      --> @PostAuthorize 처럼 결과를 보고 거부하는 경우를 위한 갈래다

 인터셉터가 이 타입인지 확인하는 자리
      --> proceed 중에 거부 예외가 나오면
          매니저가 이 인터페이스를 구현했는지 보고 넘긴다
      --> 중첩된 보안 검사의 거부도 같은 규칙으로 다루기 위해서다
```

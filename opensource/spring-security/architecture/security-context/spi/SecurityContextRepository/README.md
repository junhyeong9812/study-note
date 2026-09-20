# SecurityContextRepository

상위: [spi](../README.md)

요청을 넘어 컨텍스트를 보관하는 계약이다. 읽기(지연), 쓰기, 존재 확인 셋으로 되어 있다.

## 위치

`web` / `org.springframework.security.web.context` / `SecurityContextRepository.java` L80-L104 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/context/SecurityContextRepository.java#L80-L104))

## 실제 코드

```java
// SecurityContextRepository.java L80-L104 (javadoc 생략)
default DeferredSecurityContext loadDeferredContext(HttpServletRequest request) {
    Supplier<SecurityContext> supplier = () -> {
        @SuppressWarnings("NullAway") // fixed when remove deprecated method
        HttpRequestResponseHolder holder = new HttpRequestResponseHolder(request, null);
        return loadContext(holder);
    };
    return new SupplierDeferredSecurityContext(SingletonSupplier.of(supplier),
            SecurityContextHolder.getContextHolderStrategy());
}

void saveContext(SecurityContext context, HttpServletRequest request, HttpServletResponse response);

boolean containsContext(HttpServletRequest request);
```

`loadContext(HttpRequestResponseHolder)` 도 인터페이스에 남아 있지만 deprecated 다.

## 흐름에서 불리는 자리

```text
 읽기  SecurityContextHolderFilter.doFilter  L79 loadDeferredContext
 쓰기  인증에 성공한 필터들이 각자 saveContext 를 부른다
         AbstractAuthenticationProcessingFilter, BasicAuthenticationFilter,
         RememberMeAuthenticationFilter, SwitchUserFilter,
         SecurityContextLogoutHandler (빈 컨텍스트를 저장해 지운다)
```

- [SecurityContextRepository.loadDeferredContext](../../01_SecurityContextHolderFilter.doFilter/01_SecurityContextRepository.loadDeferredContext/README.md)

## 구현 계층

```text
 SecurityContextRepository
   +-- HttpSessionSecurityContextRepository      세션에 담는다
   +-- RequestAttributeSecurityContextRepository 요청 속성에 담는다
   +-- DelegatingSecurityContextRepository       여럿을 묶는다
   +-- NullSecurityContextRepository             아무것도 하지 않는다
   +-- (사용자 구현)

 DSL 이 아무것도 지정하지 않으면 기본은
   DelegatingSecurityContextRepository(
       HttpSessionSecurityContextRepository,
       RequestAttributeSecurityContextRepository)
   SessionManagementConfigurer L379-381 이 만든다. 세션이 앞이다
```

## 결과가 쓰이는 곳

```text
 loadDeferredContext
      --> 읽는 방법만 돌려준다. 이 시점에 저장소를 건드리지 않는다
      --> 인터페이스에 default 구현이 있지만 셋 다 오버라이드한다
          default 로 떨어지는 것은 NullSecurityContextRepository 뿐이다

 saveContext
      --> 이 흐름의 필터는 부르지 않는다. 인증한 쪽이 부른다
      --> 상태 없는 API 서버라면 NullSecurityContextRepository 로
          세션을 아예 쓰지 않게 할 수 있다

 containsContext
      --> 저장소에 컨텍스트가 있는지만 묻는다
      --> 세션 고정 보호처럼 기존 컨텍스트 유무가 중요한 쪽이 쓴다
```

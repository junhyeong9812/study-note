# SecurityContextRepository.loadDeferredContext

상위: [SecurityContextHolderFilter.doFilter](../README.md)

읽지 않고, 읽는 방법만 돌려준다.

## 위치

`web` / `org.springframework.security.web.context` / `SecurityContextRepository.java` L80-L88 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/context/SecurityContextRepository.java#L80-L88))

## 실제 코드

인터페이스에 default 구현이 있다. 단 **기본 설정에서는 이 코드가 돌지 않는다.** 실제로 쓰이는 저장소 셋이 모두 오버라이드하기 때문이다. default 로 떨어지는 것은 `NullSecurityContextRepository` 하나뿐이다.

```java
// SecurityContextRepository.java L80-L88
default DeferredSecurityContext loadDeferredContext(HttpServletRequest request) {
    Supplier<SecurityContext> supplier = () -> {
        @SuppressWarnings("NullAway") // fixed when remove deprecated method
        HttpRequestResponseHolder holder = new HttpRequestResponseHolder(request, null);
        return loadContext(holder);
    };
    return new SupplierDeferredSecurityContext(SingletonSupplier.of(supplier),
            SecurityContextHolder.getContextHolderStrategy());
}
```

이 default 가 감싸는 `loadContext` 는 deprecated 다. 구식 메서드를 지연 로딩 모양으로 바꿔 주는 다리 역할이다.

`web` / `org.springframework.security.web.context` / `SecurityContextRepository.java` L68-L69 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/context/SecurityContextRepository.java#L68-L69))

```java
// SecurityContextRepository.java L68-L69
@Deprecated
SecurityContext loadContext(HttpRequestResponseHolder requestResponseHolder);
```

## 동작 흐름

```text
 default 구현 (NullSecurityContextRepository 만 이 경로)
 |
 | L81 supplier 람다를 만든다
 |        L83 HttpRequestResponseHolder 를 만들고
 |        L84 loadContext(holder) 를 부른다
 |
 +-- L86 SupplierDeferredSecurityContext 로 감싸 돌려준다
        SingletonSupplier 로 한 번 더 감싼다
        SecurityContextHolder.getContextHolderStrategy()
          빈 컨텍스트를 만들 때 쓸 전략

 실제로 쓰이는 구현들은 SingletonSupplier 를 쓰지 않는다
   HttpSessionSecurityContextRepository   L145-148
     () -> readSecurityContextFromSession(request.getSession(false))
   RequestAttributeSecurityContextRepository  L90-93
     () -> getContext(request)
   둘 다 SupplierDeferredSecurityContext 로 바로 감싼다
```

```text
 SupplierDeferredSecurityContext 가 하는 일

 get() 이 처음 불릴 때 init() 이 돈다
   supplier.get() 으로 실제 읽기
   결과가 null 이면 strategy.createEmptyContext() 로 빈 것을 만든다
   그리고 missingContext 를 true 로 남긴다

 두 번째 호출부터는 init() 이 바로 return 한다
   securityContext 필드가 이미 채워져 있으면 그대로 돌려준다
   한 요청 안에서 저장소를 한 번만 읽는 것은 이 캐시 덕분이다
   SingletonSupplier 는 기본 경로에 없다

 isGenerated() 도 같은 init() 을 탄다
   "저장소에 없어서 새로 만든 것인가"를 알려 준다
   이 값을 쓰는 곳은 DelegatingSecurityContextRepository 뿐이다
```

```text
 기본 저장소는 둘을 겹쳐 쓴다

 DelegatingSecurityContextRepository(
     HttpSessionSecurityContextRepository(),
     RequestAttributeSecurityContextRepository())

 SessionManagementConfigurer L379-381 이 이 순서로 만든다
 세션이 앞이고 요청 속성이 뒤다

 세션       요청을 넘어 유지된다
 요청 속성  같은 요청 안에서만 산다
            ERROR 나 ASYNC 로 디스패치가 바뀌어도 컨텍스트를 복원한다
            다음 요청에는 남지 않는다

 읽을 때는 앞에서부터 찾고(앞이 isGenerated 가 아니면 거기서 멈춘다)
 쓸 때는 모든 저장소에 쓴다
```

## 결과가 쓰이는 곳

```text
 돌려준 DeferredSecurityContext
      --> 필터가 setDeferredContext 로 ThreadLocal 에 얹는다
      --> 아무도 getContext() 를 부르지 않으면 저장소를 읽지 않는다

 init() 의 캐시
      --> 한 요청 안에서 저장소를 여러 번 읽지 않게 막는다

 isGenerated
      --> 저장소에 없어서 만들어 낸 빈 컨텍스트인지 구분한다
      --> DelegatingSecurityContextRepository 가 이것으로
          "앞 저장소에 실제로 있었는지"를 판정해 다음으로 넘길지 정한다
```

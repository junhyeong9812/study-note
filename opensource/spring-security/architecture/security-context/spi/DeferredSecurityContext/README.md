# DeferredSecurityContext

상위: [spi](../README.md)

"아직 읽지 않은 컨텍스트"를 나타낸다. `Supplier<SecurityContext>` 를 상속하고 메서드 하나를 더한다.

## 위치

`core` / `org.springframework.security.core.context` / `DeferredSecurityContext.java` L28-L38 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/core/src/main/java/org/springframework/security/core/context/DeferredSecurityContext.java#L28-L38))

## 실제 코드

```java
// DeferredSecurityContext.java L28-L38 (javadoc 생략)
public interface DeferredSecurityContext extends Supplier<SecurityContext> {

    boolean isGenerated();

}
```

## 흐름에서 불리는 자리

```text
 SecurityContextRepository.loadDeferredContext 가 이것을 돌려준다
 필터가 그대로 ThreadLocal 에 얹는다
 누군가 get() 을 부르는 순간 실제 읽기가 일어난다
```

- [SecurityContextRepository.loadDeferredContext](../../01_SecurityContextHolderFilter.doFilter/01_SecurityContextRepository.loadDeferredContext/README.md)

## 구현 계층

```text
 DeferredSecurityContext (extends Supplier<SecurityContext>)
   +-- SupplierDeferredSecurityContext   기본. package-private
   +-- (저장소 구현이 자체 제공하기도 한다)
```

## 결과가 쓰이는 곳

```text
 get()
      --> 처음 부를 때만 저장소를 읽는다
      --> 결과가 null 이면 빈 컨텍스트를 만들어 대신 돌려준다

 isGenerated()
      --> 그 빈 컨텍스트가 "만들어 낸 것"인지 알려 준다
      --> 저장소에 원래 있던 것과 구분해야 하는 쪽이 쓴다
      --> get() 과 같은 init() 을 타므로, 부르면 읽기가 일어난다
```

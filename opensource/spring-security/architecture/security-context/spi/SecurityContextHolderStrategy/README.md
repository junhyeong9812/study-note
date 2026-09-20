# SecurityContextHolderStrategy

상위: [spi](../README.md)

한 요청(스레드) 안에서 컨텍스트를 어디에 들고 있을지 정하는 계약이다.

## 위치

`core` / `org.springframework.security.core.context` / `SecurityContextHolderStrategy.java` L30-L80 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/core/src/main/java/org/springframework/security/core/context/SecurityContextHolderStrategy.java#L30-L80))

## 실제 코드

```java
// SecurityContextHolderStrategy.java L30-L80 (javadoc 생략)
public interface SecurityContextHolderStrategy {

    void clearContext();

    SecurityContext getContext();

    default Supplier<SecurityContext> getDeferredContext() {
        return this::getContext;
    }

    void setContext(SecurityContext context);

    default void setDeferredContext(Supplier<SecurityContext> deferredContext) {
        setContext(deferredContext.get());
    }

    SecurityContext createEmptyContext();

}
```

## 흐름에서 불리는 자리

```text
 SecurityContextHolderFilter.doFilter
   L81 setDeferredContext   체인 앞에서 얹는다
   L85 clearContext         체인이 끝나면 지운다

 SecurityContextHolder 의 컨텍스트 조작 static 메서드들이 이 인터페이스로 위임한다
```

- [ThreadLocalSecurityContextHolderStrategy.getContext](../../02_ThreadLocalSecurityContextHolderStrategy.getContext/README.md)

## 구현 계층

```text
 SecurityContextHolderStrategy
   +-- ThreadLocalSecurityContextHolderStrategy             기본
   +-- InheritableThreadLocalSecurityContextHolderStrategy  자식 스레드에 물려준다
   +-- GlobalSecurityContextHolderStrategy                  JVM 하나에 하나
   +-- ListeningSecurityContextHolderStrategy               변경을 이벤트로 알린다
   +-- (사용자 구현)

 넷 다 core 의 같은 패키지에 있다
 앞의 셋은 package-private 이고 SecurityContextHolder 가 모드로 고른다
   MODE_THREADLOCAL, MODE_INHERITABLETHREADLOCAL, MODE_GLOBAL
   또는 무인자 생성자를 가진 클래스 이름을 직접 준다

 ListeningSecurityContextHolderStrategy 는 public 이고 성격이 다르다
   다른 전략을 감싸는 데코레이터라 무인자 생성자가 없다
   모드로 고를 수 없고 setContextHolderStrategy 로 직접 설치한다
```

## 결과가 쓰이는 곳

```text
 getDeferredContext / setDeferredContext
      --> 인터페이스에 default 구현이 있다
          getDeferredContext 는 this::getContext 를 돌려주고
          setDeferredContext 는 즉시 get() 해서 setContext 한다
      --> 즉 default 만으로는 지연이 되지 않는다
          ThreadLocal 구현은 둘 다 오버라이드해 진짜 지연을 만든다

 createEmptyContext
      --> 비어 있을 때 무엇을 돌려줄지 정한다
      --> getContext 가 null 을 돌려주지 않는 근거다
```

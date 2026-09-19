# TransactionAttributeSource

상위: [Spring 트랜잭션](../../README.md) / [spi](../README.md)

메서드 하나에 적용할 트랜잭션 속성을 찾아 준다. `@Transactional`을 어디서 어떻게 읽을지가 이 구현에 달려 있다.

## 실제 코드

`spring-tx` / `org.springframework.transaction.interceptor` / `TransactionAttributeSource.java` L36-L79 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-tx/src/main/java/org/springframework/transaction/interceptor/TransactionAttributeSource.java#L36-L79))

```java
// TransactionAttributeSource.java L36-L79
public interface TransactionAttributeSource {

    default boolean isCandidateClass(Class<?> targetClass) {
        return true;
    }

    default boolean hasTransactionAttribute(Method method, @Nullable Class<?> targetClass) {
        return (getTransactionAttribute(method, targetClass) != null);
    }

    @Nullable TransactionAttribute getTransactionAttribute(Method method, @Nullable Class<?> targetClass);

}
```

## 흐름에서 불리는 자리

```text
 invokeWithinTransaction L338
   tas.getTransactionAttribute(method, targetClass)
     null 이면 트랜잭션 없이 실행
 프록시 생성 단계에서도 쓰인다
   TransactionAttributeSourcePointcut 이 같은 판정으로 "프록시가 필요한가" 를 정한다
```

- [invokeWithinTransaction](../../01_TransactionAspectSupport.invokeWithinTransaction/README.md)

## 구현 계층

```text
 TransactionAttributeSource
   +-- AbstractFallbackTransactionAttributeSource      탐색 순서 + 캐시
   |     +-- AnnotationTransactionAttributeSource      @Transactional (Spring, JTA, EJB)
   +-- NameMatchTransactionAttributeSource             메서드 이름 패턴 (fallback 탐색 없음)
   +-- MethodMapTransactionAttributeSource
   +-- MatchAlwaysTransactionAttributeSource
   +-- CompositeTransactionAttributeSource

 AbstractFallbackTransactionAttributeSource 의 탐색 순서
   1) 타깃 클래스의 메서드
   2) 타깃 클래스
   3) 선언 클래스(인터페이스)의 메서드
   4) 선언 클래스
   = 구현 클래스의 애노테이션이 인터페이스의 것을 덮어쓴다
```

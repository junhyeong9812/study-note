# ReactiveTransactionManager

상위: [Spring R2DBC](../../README.md) / [spi](../README.md)

명령형 `PlatformTransactionManager`의 리액티브 짝이다. 반환 타입이 전부 `Mono`이고, 트랜잭션 상태를 스레드가 아니라 구독 컨텍스트에서 주고받는다.

## 실제 코드

`spring-tx` / `org.springframework.transaction` / `ReactiveTransactionManager.java` L36-L114 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-tx/src/main/java/org/springframework/transaction/ReactiveTransactionManager.java#L36-L114))

```java
// ReactiveTransactionManager.java L36-L114
public interface ReactiveTransactionManager extends TransactionManager {

    Mono<ReactiveTransaction> getReactiveTransaction(@Nullable TransactionDefinition definition);

    Mono<Void> commit(ReactiveTransaction transaction);

    Mono<Void> rollback(ReactiveTransaction transaction);

}
```

## 흐름에서 불리는 자리

```text
 @Transactional 이 붙은 리액티브 메서드
   TransactionInterceptor 가 반환 타입이 리액티브임을 보고
   ReactiveTransactionSupport 경로로 보낸다
 TransactionalOperator 로 직접 감쌀 수도 있다
   operator.transactional(flux)
```

- [R2dbcTransactionManager.doBegin](../../03_R2dbcTransactionManager.doBegin/README.md)
- [R2dbcTransactionManager.doCommit](../../04_R2dbcTransactionManager.doCommit/README.md)

## 구현 계층

```text
 TransactionManager (표식 인터페이스)
   +-- PlatformTransactionManager     명령형
   +-- ReactiveTransactionManager     리액티브
         +-- AbstractReactiveTransactionManager   전파, 동기화 골격
               +-- R2dbcTransactionManager
               +-- (다른 리액티브 리소스의 매니저들)
```

```text
 명령형과 나란히 보기

 getTransaction(정의)  --> Mono<ReactiveTransaction>
 commit(상태)          --> Mono<Void>
 rollback(상태)        --> Mono<Void>
 상태 보관: ThreadLocal --> 리액터 컨텍스트
```

## 결과가 쓰이는 곳

```text
 반환한 Mono
      --> 구독돼야 트랜잭션이 열리고 커밋된다
      --> 명령형처럼 "메서드가 끝나면 커밋돼 있다"가 성립하지 않는다

 같은 체인 안의 공유
      --> 컨텍스트에 실린 동기화 관리자를 통해 커넥션이 공유된다
      --> 체인을 벗어난 별도 구독은 다른 트랜잭션이다

 명령형과 섞을 수 없다
      --> 같은 메서드에서 두 매니저를 함께 쓰면 트랜잭션이 갈라진다
      --> 리액티브 경로에서 블로킹 JDBC 를 부르면 트랜잭션도 스레드도 어긋난다
```

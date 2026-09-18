# Spring 트랜잭션

`@Transactional`이 붙은 메서드를 호출했을 때, 트랜잭션이 열리고 커밋되거나 롤백되기까지의 흐름을 위에서 아래로 따라간다. 시작은 AOP 인터셉터이고, 실제 커넥션 조작은 트랜잭션 매니저 구현이 한다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 트랜잭션 추상화의 인터페이스 모음이다.

기준 커밋: spring-framework `main` [`c1d4a766929`](https://github.com/spring-projects/spring-framework/tree/c1d4a76692949bdcdebae4b98b104174e4b951cf) (2026-09-10). 모든 줄 번호는 이 커밋 기준이다.

## 어디에서 들어오는가

`@Transactional`은 그 자체로는 아무 일도 하지 않는다. `@EnableTransactionManagement`가 어드바이저를 등록하고, 그 어드바이저가 [AOP 프록시](../aop-proxy/README.md)를 만들며, 프록시 호출이 인터셉터 체인을 돌 때 비로소 트랜잭션이 열린다.

```text
 @EnableTransactionManagement
   --> TransactionManagementConfigurationSelector --> ProxyTransactionManagementConfiguration
         @Bean BeanFactoryTransactionAttributeSourceAdvisor   (어드바이저)
         @Bean AnnotationTransactionAttributeSource           (어디에 붙었나 판정)
         @Bean TransactionInterceptor                         (무엇을 할지)
   --> 빈 생성 중 AbstractAutoProxyCreator 가 이 어드바이저를 골라 프록시 생성
   --> 프록시.메서드() --> ReflectiveMethodInvocation.proceed --> TransactionInterceptor.invoke
```

## 전체 그림

```text
 TransactionInterceptor.invoke(invocation)
 |
 +-- [01] TransactionAspectSupport.invokeWithinTransaction
        |
        | txAttr = 이 메서드의 @Transactional 속성 (없으면 그냥 통과)
        | tm     = 사용할 트랜잭션 매니저
        |
        +-- [01-01] createTransactionIfNecessary
        |      +-- [01-01-01] AbstractPlatformTransactionManager.getTransaction
        |             전파 속성에 따라 새 트랜잭션 / 참여 / 중단 / 예외
        |             새 트랜잭션이면 doBegin --> 커넥션 획득, autoCommit=false
        |             TransactionSynchronizationManager 에 리소스 바인딩
        |
        +-- invocation.proceedWithInvocation()      다음 인터셉터 또는 타깃 메서드
        |
        +-- 정상 반환 --> [01-02] commitTransactionAfterReturning
        |                    +-- [01-02-01] AbstractPlatformTransactionManager.commit
        |                           rollback-only 표시면 실제로는 롤백
        |                           새 트랜잭션이면 doCommit
        |
        +-- 예외 --> [01-03] completeTransactionAfterThrowing
        |               txAttr.rollbackOn(ex) 가 true  --> rollback
        |               false --> commit  (체크 예외 기본 동작)
        |                  +-- [01-03-01] AbstractPlatformTransactionManager.rollback
        |
        +-- finally --> [01-04] cleanupTransactionInfo   ThreadLocal 복원
```

## 단계

1. [TransactionAspectSupport.invokeWithinTransaction](01_TransactionAspectSupport.invokeWithinTransaction/README.md)이 트랜잭션 경계를 만든다. 여는 것, 커밋, 롤백, 정리가 모두 이 메서드의 구조 안에 있다.

## 결과가 쓰이는 곳

```text
 열린 트랜잭션
      --> TransactionSynchronizationManager 에 (DataSource -> ConnectionHolder) 로 바인딩
      --> 같은 스레드의 JdbcTemplate / JPA 가 DataSourceUtils.getConnection 으로
          같은 커넥션을 찾아 쓴다 = 같은 트랜잭션에 참여
      --> 트랜잭션 동기화 콜백(TransactionSynchronization) 등록 지점

 커밋/롤백 결과
      --> 커넥션의 commit/rollback 후 바인딩 해제, 커넥션 반납

 rollback-only 표시
      --> 안쪽 메서드가 예외를 삼켜도 바깥 트랜잭션은 커밋되지 않는다
          (UnexpectedRollbackException 으로 드러남)
```

## 다루지 않는 것

리액티브 트랜잭션(`ReactiveTransactionManager`, `TransactionalOperator`)은 같은 구조를 구독 컨텍스트 위에서 수행한다. 이 지도는 명령형 경로만 다룬다.

## 하위 메서드

- [01 TransactionAspectSupport.invokeWithinTransaction](01_TransactionAspectSupport.invokeWithinTransaction/README.md)
- [spi](spi/README.md) — 트랜잭션 매니저, 정의, 상태, 동기화

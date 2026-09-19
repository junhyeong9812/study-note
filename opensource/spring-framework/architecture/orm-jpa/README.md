# Spring JPA 연동

JPA 스펙의 `EntityManagerFactory`와 `EntityManager`를 스프링 컨테이너 안으로 들여오는 흐름이다. 기동 때 팩토리를 만들고, `@PersistenceContext` 자리에는 실제 `EntityManager`가 아니라 프록시를 꽂고, 트랜잭션 매니저가 그 프록시 뒤의 진짜 인스턴스를 스레드에 묶는다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 벤더 어댑터와 방언 인터페이스 모음이다.

기준 커밋: spring-framework `main` [`c1d4a766929`](https://github.com/spring-projects/spring-framework/tree/c1d4a76692949bdcdebae4b98b104174e4b951cf) (2026-09-10). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 [A] 기동 — EntityManagerFactory 만들기

 LocalContainerEntityManagerFactoryBean (FactoryBean)
 |
 +-- [01] afterPropertiesSet
 |        PersistenceUnitManager 로 persistence unit 정보를 정한다
 |        JpaVendorAdapter 가 벤더별 프로퍼티와 방언을 채운다
 |
 +-- [01-01] createNativeEntityManagerFactory
 |        PersistenceProvider.createContainerEntityManagerFactory(정보, 프로퍼티)
 |        = 여기서 하이버네이트 같은 구현이 실제 팩토리를 만든다
 |
 +-- 만들어진 팩토리를 프록시로 감싸 빈으로 노출한다
        프록시가 EntityManagerFactoryInfo 를 구현해 방언과 데이터 소스를 알려 준다

 [B] 주입 — @PersistenceContext 자리에 무엇이 들어가는가

 +-- [02] PersistenceAnnotationBeanPostProcessor.postProcessProperties
 |        @PersistenceContext / @PersistenceUnit 필드와 메서드를 찾아 주입
 |
 +-- [02-01] SharedEntityManagerCreator.createSharedEntityManager
 |        JDK 동적 프록시를 만든다 (진짜 EntityManager 가 아니다)
 |
 +-- [02-01-01] SharedEntityManagerInvocationHandler.invoke
          호출마다 "지금 트랜잭션에 묶인 EntityManager" 를 찾아 위임한다

 [C] 트랜잭션 — 진짜 EntityManager 를 스레드에 묶기

 TransactionInterceptor --> JpaTransactionManager
 |
 +-- [03] doBegin
 |        EntityManager 를 새로 열고 EntityManagerHolder 로 스레드에 바인딩
 |        JpaDialect.beginTransaction 이 벤더별 격리 수준/읽기 전용을 건다
 |        데이터 소스를 알고 있으면 같은 커넥션을 JDBC 쪽에도 노출한다
 |
 +-- [03-01] EntityManagerFactoryUtils.doGetTransactionalEntityManager
 |        프록시가 위 홀더를 찾을 때 쓰는 조회 지점
 |
 +-- [04] doCommit
          EntityTransaction.commit() --> 이 시점에 flush 가 일어난다

 [D] 예외 변환

 +-- [05] EntityManagerFactoryUtils.convertJpaAccessExceptionIfPossible
          JPA 예외 --> 스프링 DataAccessException 계층
```

## 어디에서 쓰이는가

```text
 [빈 생성] LocalContainerEntityManagerFactoryBean 은 FactoryBean 이다
   getObject() 가 EntityManagerFactory 프록시를 돌려준다
 [빈 생성] PersistenceAnnotationBeanPostProcessor 가 주입 단계에서 개입한다
 [트랜잭션] JpaTransactionManager 는 AbstractPlatformTransactionManager 의 하위다
   전파, 롤백 규칙, 동기화 콜백은 전부 그 골격이 제공한다
 [JDBC] 같은 트랜잭션 안의 JdbcTemplate 이 JPA 가 쓰던 커넥션을 그대로 쓴다
```

빈 생성과 주입의 골격은 [빈 생성](../bean-creation/README.md), 트랜잭션 골격은 [트랜잭션](../transaction/README.md), 커넥션 관리는 [JDBC](../jdbc/README.md) 흐름에 있다.

## 단계

1. [LocalContainerEntityManagerFactoryBean.afterPropertiesSet](01_LocalContainerEntityManagerFactoryBean.afterPropertiesSet/README.md)이 팩토리를 만든다.
2. [PersistenceAnnotationBeanPostProcessor.postProcessProperties](02_PersistenceAnnotationBeanPostProcessor.postProcessProperties/README.md)가 `@PersistenceContext`를 채운다.
3. [JpaTransactionManager.doBegin](03_JpaTransactionManager.doBegin/README.md)이 `EntityManager`를 열어 스레드에 묶는다.
4. [JpaTransactionManager.doCommit](04_JpaTransactionManager.doCommit/README.md)이 커밋하며 flush 를 유발한다.
5. [EntityManagerFactoryUtils.convertJpaAccessExceptionIfPossible](05_EntityManagerFactoryUtils.convertJpaAccessExceptionIfPossible/README.md)이 예외를 번역한다.

## 결과가 쓰이는 곳

```text
 EntityManagerFactory 프록시
      --> @PersistenceUnit 주입 대상
      --> EntityManagerFactoryInfo 로 방언, 데이터 소스, 영속성 유닛 이름을 알려 준다

 EntityManager 프록시 (공유)
      --> 싱글톤 빈의 필드에 꽂아도 안전한 이유가 여기 있다
      --> 호출 시점마다 현재 트랜잭션의 EntityManager 를 찾는다
      --> 트랜잭션이 없으면 호출마다 새로 열고 바로 닫는다 (영속성 컨텍스트가 유지되지 않는다)

 EntityManagerHolder (스레드 바인딩)
      --> 같은 트랜잭션 안의 모든 리포지터리가 같은 영속성 컨텍스트를 공유한다
      --> 1차 캐시와 더티 체킹이 성립하는 근거다

 flush 시점
      --> 커밋 때 EntityTransaction.commit() 이 flush 를 부른다
      --> 그래서 "코드 어디에도 update 가 없는데 UPDATE 가 나가는" 일이 생긴다
```

## 다루지 않는 것

하이버네이트 전용 경로(`HibernateTransactionManager`, `LocalSessionFactoryBean`, `SpringSessionContext`)와 확장 영속성 컨텍스트(`ExtendedEntityManagerCreator`), 뷰 렌더링까지 영속성 컨텍스트를 여는 `OpenEntityManagerInViewFilter`는 같은 뼈대의 갈래라 요약만 했다. JPA 스펙 자체의 동작(엔티티 상태 전이, 쿼리 언어)과 벤더 내부도 범위 밖이다.

## 하위 메서드

- [01 LocalContainerEntityManagerFactoryBean.afterPropertiesSet](01_LocalContainerEntityManagerFactoryBean.afterPropertiesSet/README.md)
- [02 PersistenceAnnotationBeanPostProcessor.postProcessProperties](02_PersistenceAnnotationBeanPostProcessor.postProcessProperties/README.md)
- [03 JpaTransactionManager.doBegin](03_JpaTransactionManager.doBegin/README.md)
- [04 JpaTransactionManager.doCommit](04_JpaTransactionManager.doCommit/README.md)
- [05 EntityManagerFactoryUtils.convertJpaAccessExceptionIfPossible](05_EntityManagerFactoryUtils.convertJpaAccessExceptionIfPossible/README.md)
- [spi](spi/README.md) — 벤더 어댑터, 방언, 영속성 유닛, 팩토리 정보, 예외 변환

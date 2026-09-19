# EntityManagerFactoryInfo

상위: [Spring JPA 연동](../../README.md) / [spi](../README.md)

스프링이 만든 `EntityManagerFactory` 프록시가 스스로를 설명하는 창구다. 트랜잭션 매니저와 공유 프록시가 방언과 데이터 소스를 알아내는 경로가 이것뿐이다.

## 실제 코드

`spring-orm` / `org.springframework.orm.jpa` / `EntityManagerFactoryInfo.java` L39-L58 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-orm/src/main/java/org/springframework/orm/jpa/EntityManagerFactoryInfo.java#L39-L58))

```java
// EntityManagerFactoryInfo.java L39-L58
public interface EntityManagerFactoryInfo {

    @Nullable PersistenceProvider getPersistenceProvider();

    @Nullable PersistenceUnitInfo getPersistenceUnitInfo();

```

`spring-orm` / `org.springframework.orm.jpa` / `EntityManagerFactoryInfo.java` L100-L110 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-orm/src/main/java/org/springframework/orm/jpa/EntityManagerFactoryInfo.java#L100-L110))

```java
// EntityManagerFactoryInfo.java L100-L110
@Nullable JpaDialect getJpaDialect();

ClassLoader getBeanClassLoader();

```

## 흐름에서 불리는 자리

```text
 JpaTransactionManager
   팩토리가 EntityManagerFactoryInfo 면 getJpaDialect() 로 방언을,
   getDataSource() 로 데이터 소스를 자동으로 가져온다
 SharedEntityManagerCreator.createSharedEntityManager   L170
   getBeanClassLoader() 로 프록시를 만들 클래스로더를 정한다
```

- [JpaTransactionManager.doBegin](../../03_JpaTransactionManager.doBegin/README.md)
- [SharedEntityManagerCreator.createSharedEntityManager](../../02_PersistenceAnnotationBeanPostProcessor.postProcessProperties/01_SharedEntityManagerCreator.createSharedEntityManager/README.md)

## 구현 계층

```text
 EntityManagerFactoryInfo
   +-- AbstractEntityManagerFactoryBean 이 만든 EntityManagerFactory 프록시
         = 컨테이너에 등록되는 EntityManagerFactory 가 이 인터페이스도 구현한다

 순수 JPA 로 만든 팩토리(Persistence.createEntityManagerFactory)는
 이 인터페이스를 구현하지 않는다 --> 방언과 데이터 소스를 직접 설정해야 한다
```

## 결과가 쓰이는 곳

```text
 getJpaDialect
      --> 트랜잭션 매니저가 벤더별 트랜잭션 처리에 쓴다
      --> 이것이 없으면 DefaultJpaDialect 수준으로 떨어진다

 getDataSource
      --> 트랜잭션 매니저가 JDBC 커넥션 노출 여부를 정할 때 쓴다

 getNativeEntityManagerFactory
      --> 프록시를 벗겨 벤더 구현(SessionFactory 등)에 닿는 탈출구

 createNativeEntityManager
      --> 스프링 설정(기본 프로퍼티)을 적용한 뒤 벤더 팩토리에 위임한다
```

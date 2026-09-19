# JpaVendorAdapter

상위: [Spring JPA 연동](../../README.md) / [spi](../README.md)

하이버네이트냐 EclipseLink냐에 따라 달라지는 것들을 한 곳에 모은 묶음이다. 프로바이더, 기본 프로퍼티, 방언, 확장 인터페이스를 한꺼번에 공급한다.

## 실제 코드

`spring-orm` / `org.springframework.orm.jpa` / `JpaVendorAdapter.java` L38-L60 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-orm/src/main/java/org/springframework/orm/jpa/JpaVendorAdapter.java#L38-L60))

```java
// JpaVendorAdapter.java L38-L60
public interface JpaVendorAdapter {

    PersistenceProvider getPersistenceProvider();

    default @Nullable String getPersistenceProviderRootPackage() {
        return null;
    }

```

`spring-orm` / `org.springframework.orm.jpa` / `JpaVendorAdapter.java` L100-L102 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-orm/src/main/java/org/springframework/orm/jpa/JpaVendorAdapter.java#L100-L102))

```java
// JpaVendorAdapter.java L100-L102
default @Nullable JpaDialect getJpaDialect() {
    return null;
}
```

## 흐름에서 불리는 자리

```text
 AbstractEntityManagerFactoryBean.afterPropertiesSet   L373-L400
   getPersistenceProvider()      구현체 결정
   getJpaPropertyMap(pui)        벤더 기본 프로퍼티 병합 (사용자 값이 우선)
   getEntityManagerFactoryInterface() / getEntityManagerInterface()
                                 프록시가 구현할 인터페이스
 LocalContainerEntityManagerFactoryBean.afterPropertiesSet  L393
   getPersistenceProviderRootPackage()   유닛 정보에 벤더 패키지를 알려 준다
```

- [LocalContainerEntityManagerFactoryBean.afterPropertiesSet](../../01_LocalContainerEntityManagerFactoryBean.afterPropertiesSet/README.md)

## 구현 계층

```text
 JpaVendorAdapter
   +-- AbstractJpaVendorAdapter            공통 설정(Database, 스키마 생성, showSql)
         +-- HibernateJpaVendorAdapter     하이버네이트
         +-- EclipseLinkJpaVendorAdapter   EclipseLink

 어댑터가 공급하는 것
   PersistenceProvider   실제 구현
   JpaDialect            트랜잭션/커넥션 처리 방식
   기본 프로퍼티          방언 클래스, DDL 모드 등
```

## 결과가 쓰이는 곳

```text
 getJpaPropertyMap
      --> 팩토리 빈의 jpaProperties 와 병합된다. 사용자가 직접 넣은 키가 이긴다
      --> 그래서 어댑터 기본값은 "덮어쓸 수 있는 출발점"이다

 getJpaDialect
      --> JpaTransactionManager 가 EntityManagerFactoryInfo 를 통해 이 방언을 찾는다
      --> 방언이 JDBC 커넥션을 내주면 JPA 와 JdbcTemplate 이 한 트랜잭션을 쓴다

 getEntityManagerInterface
      --> 공유 프록시가 구현할 인터페이스 목록에 들어간다
      --> 벤더 전용 타입으로 캐스팅이 가능한 이유다

 어댑터를 아예 지정하지 않으면
      --> 프로바이더는 유닛 정보의 provider 클래스 이름으로 정해진다
      --> 방언은 없으므로 DefaultJpaDialect 의 최소 동작만 쓴다
```

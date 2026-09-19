# PersistenceUnitManager

상위: [Spring JPA 연동](../../README.md) / [spi](../README.md)

영속성 유닛 정보를 공급한다. `persistence.xml`을 읽든, 패키지를 스캔하든, 결과물은 `PersistenceUnitInfo` 하나다.

## 실제 코드

`spring-orm` / `org.springframework.orm.jpa.persistenceunit` / `PersistenceUnitManager.java` L37-L59 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-orm/src/main/java/org/springframework/orm/jpa/persistenceunit/PersistenceUnitManager.java#L37-L59))

```java
// PersistenceUnitManager.java L37-L59
public interface PersistenceUnitManager {

    PersistenceUnitInfo obtainDefaultPersistenceUnitInfo() throws IllegalStateException;

    PersistenceUnitInfo obtainPersistenceUnitInfo(String persistenceUnitName)
            throws IllegalArgumentException, IllegalStateException;

}
```

## 흐름에서 불리는 자리

```text
 LocalContainerEntityManagerFactoryBean.afterPropertiesSet
   L385 지정된 매니저가 없으면 내장 DefaultPersistenceUnitManager 를 초기화
   L391 determinePersistenceUnitInfo(매니저)
          유닛 이름이 지정됐으면 obtainPersistenceUnitInfo(이름)
          아니면 obtainDefaultPersistenceUnitInfo()
```

- [LocalContainerEntityManagerFactoryBean.afterPropertiesSet](../../01_LocalContainerEntityManagerFactoryBean.afterPropertiesSet/README.md)

## 구현 계층

```text
 PersistenceUnitManager
   +-- DefaultPersistenceUnitManager
         persistence.xml 위치 지정 (기본 classpath*:META-INF/persistence.xml)
         packagesToScan 으로 @Entity 스캔 (persistence.xml 없이 구성)
         defaultDataSource / dataSourceLookup 으로 데이터 소스 연결
         PersistenceUnitPostProcessor 로 유닛 정보를 더 손볼 수 있다
```

```text
 한 번만 꺼낼 수 있다

 obtain... 메서드는 이미 꺼낸 유닛을 다시 요구하면 IllegalStateException 이다
 (javadoc 에 명시) — 팩토리 빈 하나가 유닛 하나를 소비한다는 뜻이다
```

## 결과가 쓰이는 곳

```text
 PersistenceUnitInfo
      --> PersistenceProvider.createContainerEntityManagerFactory 로 그대로 넘어간다
      --> 엔티티 목록, 데이터 소스, 트랜잭션 타입, 벤더 프로퍼티가 여기 담긴다

 packagesToScan
      --> persistence.xml 없이도 매핑을 구성할 수 있게 한다
      --> 스캔 결과가 PersistenceManagedTypes 로 고정되면 AOT 에서도 재사용된다

 유닛 이름
      --> 팩토리가 여럿일 때 어떤 유닛을 쓸지 고르는 기준이다
```

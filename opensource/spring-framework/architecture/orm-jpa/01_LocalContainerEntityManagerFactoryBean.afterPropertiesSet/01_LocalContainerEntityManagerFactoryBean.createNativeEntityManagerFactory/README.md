# LocalContainerEntityManagerFactoryBean.createNativeEntityManagerFactory

상위: [LocalContainerEntityManagerFactoryBean.afterPropertiesSet](../README.md)

스프링이 JPA 구현에게 실제 팩토리 생성을 넘기는 한 줄이 여기 있다. 이 지점부터는 하이버네이트 같은 벤더의 코드다.

## 실제 코드

`spring-orm` / `org.springframework.orm.jpa` / `LocalContainerEntityManagerFactoryBean.java` L423-L447 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-orm/src/main/java/org/springframework/orm/jpa/LocalContainerEntityManagerFactoryBean.java#L423-L447))

```java
// LocalContainerEntityManagerFactoryBean.java L423-L447
protected EntityManagerFactory createNativeEntityManagerFactory() throws PersistenceException {
    Assert.state(this.persistenceUnitInfo != null, "PersistenceUnitInfo not initialized");

    PersistenceProvider provider = getPersistenceProvider();
    if (provider == null) {
        String providerClassName = this.persistenceUnitInfo.getPersistenceProviderClassName();
        if (providerClassName == null) {
            throw new IllegalArgumentException(
                    "No PersistenceProvider specified in EntityManagerFactory configuration, " +
                    "and chosen PersistenceUnitInfo does not specify a provider class name either");
        }
        Class<?> providerClass = ClassUtils.resolveClassName(providerClassName, getBeanClassLoader());
        provider = (PersistenceProvider) BeanUtils.instantiateClass(providerClass);
    }

    if (logger.isDebugEnabled()) {
        logger.debug("Building JPA container EntityManagerFactory for persistence unit '" +
                this.persistenceUnitInfo.getPersistenceUnitName() + "'");
    }
    EntityManagerFactory emf =
            provider.createContainerEntityManagerFactory(this.persistenceUnitInfo, getJpaPropertyMap());
    postProcessEntityManagerFactory(emf, this.persistenceUnitInfo);

    return emf;
}
```

## 동작 흐름

```text
 createNativeEntityManagerFactory()
 |
 | L424 persistenceUnitInfo 가 준비돼 있어야 한다 (없으면 IllegalStateException)
 |
 +-- L426 PersistenceProvider 결정
 |        어댑터가 준 것이 있으면 그것
 |        없으면 L428 유닛 정보의 provider 클래스 이름으로 인스턴스를 만든다
 |        그것도 없으면 L430 IllegalArgumentException
 |
 | L443 provider.createContainerEntityManagerFactory(유닛 정보, 프로퍼티)
 |        컨테이너 모드 부트스트랩. 여기서 매핑 파싱과 스키마 검증이 일어난다
 |        기동 시간의 대부분이 이 한 줄이다
 |
 +-- L444 postProcessEntityManagerFactory(emf, 유닛 정보)   확장 훅 (기본 구현은 비어 있다)
```

```text
 컨테이너 모드와 애플리케이션 모드

 createContainerEntityManagerFactory(PersistenceUnitInfo, 맵)
   스프링이 유닛 정보를 직접 만들어 넘긴다 (persistence.xml 불필요)
   데이터 소스도 스프링 것을 쓴다
   LocalContainerEntityManagerFactoryBean 이 쓰는 경로

 createEntityManagerFactory(유닛 이름, 맵)
   persistence.xml 에 적힌 대로 벤더가 알아서 만든다
   LocalEntityManagerFactoryBean 이 쓰는 경로 (스프링 데이터 소스와 엮기 어렵다)
```

## 결과가 쓰이는 곳

```text
 반환한 네이티브 EntityManagerFactory
      --> 상위 클래스가 프록시로 감싼다
      --> 프록시는 EntityManagerFactoryInfo 를 함께 구현한다
            getJpaDialect(), getDataSource(), getPersistenceUnitInfo()
      --> JpaTransactionManager 가 이 정보로 방언과 데이터 소스를 알아낸다

 createEntityManager() 호출
      --> 프록시가 가로채 네이티브 팩토리에 위임한 뒤, 결과를 애플리케이션 관리
          EntityManager 프록시로 다시 감싼다 (AbstractEntityManagerFactoryBean L528, L555)
      --> 그 프록시가 진행 중인 트랜잭션에 자동으로 참여한다
      --> 벤더 어댑터의 postProcessEntityManager 훅도 이때 걸린다

 기동 실패가 여기서 드러난다
      --> 매핑 오류, 스키마 검증 실패, 드라이버 문제는 이 줄에서 예외로 나온다
      --> 즉 컨테이너 기동이 끝나기 전에 실패한다 (지연 초기화가 아니다)
```

이 팩토리를 트랜잭션에서 쓰는 지점은 [JpaTransactionManager.doBegin](../../03_JpaTransactionManager.doBegin/README.md)에 있다.

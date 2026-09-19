# LocalContainerEntityManagerFactoryBean.afterPropertiesSet

상위: [Spring JPA 연동](../README.md)

`persistence.xml` 없이도 스프링 설정만으로 영속성 유닛을 구성해 JPA 팩토리를 만드는 자리다. 이 빈은 `FactoryBean`이라 컨테이너에 노출되는 것은 이 객체가 아니라 만들어진 `EntityManagerFactory`다.

## 실제 코드

`spring-orm` / `org.springframework.orm.jpa` / `LocalContainerEntityManagerFactoryBean.java` L384-L420 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-orm/src/main/java/org/springframework/orm/jpa/LocalContainerEntityManagerFactoryBean.java#L384-L420))

```java
// LocalContainerEntityManagerFactoryBean.java L384-L420
public void afterPropertiesSet() throws PersistenceException {
    PersistenceUnitManager managerToUse = this.persistenceUnitManager;
    if (managerToUse == null) {
        this.internalPersistenceUnitManager.afterPropertiesSet();
        managerToUse = this.internalPersistenceUnitManager;
    }

    this.persistenceUnitInfo = determinePersistenceUnitInfo(managerToUse);
    JpaVendorAdapter jpaVendorAdapter = getJpaVendorAdapter();
    if (jpaVendorAdapter != null && this.persistenceUnitInfo instanceof SmartPersistenceUnitInfo smartInfo) {
        String rootPackage = jpaVendorAdapter.getPersistenceProviderRootPackage();
        if (rootPackage != null) {
            smartInfo.setPersistenceProviderPackageName(rootPackage);
        }
    }

    String scope = this.persistenceUnitInfo.getScopeAnnotationName();
    if (StringUtils.hasText(scope)) {
        logger.info("Scope annotation name for persistence unit ignored by Spring: " + scope);
    }

    List<String> qualifiers = this.persistenceUnitInfo.getQualifierAnnotationNames();
    if (!CollectionUtils.isEmpty(qualifiers)) {
        BeanFactory beanFactory = getBeanFactory();
        String beanName = getBeanName();
        if (beanFactory instanceof ConfigurableBeanFactory cbf && beanName != null) {
            BeanDefinition bd = cbf.getMergedBeanDefinition(beanName);
            if (bd instanceof AbstractBeanDefinition abd) {
                for (String qualifier : qualifiers) {
                    abd.addQualifier(new AutowireCandidateQualifier(qualifier));
                }
            }
        }
    }

    super.afterPropertiesSet();
}
```

벤더 어댑터가 채워 주는 값은 상위 클래스가 처리한다.

`spring-orm` / `org.springframework.orm.jpa` / `AbstractEntityManagerFactoryBean.java` L373-L429 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-orm/src/main/java/org/springframework/orm/jpa/AbstractEntityManagerFactoryBean.java#L373-L429))

```java
// AbstractEntityManagerFactoryBean.java L373-L429
public void afterPropertiesSet() throws PersistenceException {
    JpaVendorAdapter jpaVendorAdapter = getJpaVendorAdapter();
    if (jpaVendorAdapter != null) {
        if (this.persistenceProvider == null) {
            this.persistenceProvider = jpaVendorAdapter.getPersistenceProvider();
        }
        PersistenceUnitInfo pui = getPersistenceUnitInfo();
        Map<String, ?> vendorPropertyMap = (pui != null ? jpaVendorAdapter.getJpaPropertyMap(pui) :
                jpaVendorAdapter.getJpaPropertyMap());
        if (!CollectionUtils.isEmpty(vendorPropertyMap)) {
            vendorPropertyMap.forEach((key, value) -> {
                if (!this.jpaPropertyMap.containsKey(key)) {
                    this.jpaPropertyMap.put(key, value);
                }
            });
        }
        if (this.entityManagerFactoryInterface == null) {
            this.entityManagerFactoryInterface = jpaVendorAdapter.getEntityManagerFactoryInterface();
            if (!ClassUtils.isVisible(this.entityManagerFactoryInterface, this.beanClassLoader)) {
                this.entityManagerFactoryInterface = EntityManagerFactory.class;
            }
        }
        if (this.entityManagerInterface == null) {
            this.entityManagerInterface = jpaVendorAdapter.getEntityManagerInterface();
            if (!ClassUtils.isVisible(this.entityManagerInterface, this.beanClassLoader)) {
                this.entityManagerInterface = EntityManager.class;
            }
        }
        if (this.entityAgentInterface != null) {
            Class<?> vendorInterface = jpaVendorAdapter.getEntityAgentInterface();
            this.entityAgentInterface = (vendorInterface != null &&
                    ClassUtils.isVisible(vendorInterface, this.beanClassLoader) ? vendorInterface : null);
        }
        if (this.jpaDialect == null) {
            this.jpaDialect = jpaVendorAdapter.getJpaDialect();
        }
    }

    AsyncTaskExecutor bootstrapExecutor = getBootstrapExecutor();
    if (bootstrapExecutor != null) {
        this.nativeEntityManagerFactoryFuture = bootstrapExecutor.submit(this::buildNativeEntityManagerFactory);
    }
    else {
        this.nativeEntityManagerFactory = buildNativeEntityManagerFactory();
    }

    // Wrap the EntityManagerFactory in a factory implementing all its interfaces.
    // This allows interception of createEntityManager methods to return an
    // application-managed EntityManager proxy that automatically joins
    // existing transactions.
    this.entityManagerFactory = createEntityManagerFactoryProxy(this.nativeEntityManagerFactory);

    this.sharedEntityManager = SharedEntityManagerCreator.createSharedEntityManager(this.entityManagerFactory);
    if (this.entityAgentInterface != null) {
        this.sharedEntityAgent = SharedEntityManagerCreator.createSharedEntityAgent(this.entityManagerFactory);
    }
}
```

## 동작 흐름

```text
 afterPropertiesSet()
 |
 +-- L385 persistenceUnitManager 가 지정되지 않았으면
 |        내장 DefaultPersistenceUnitManager 를 초기화해 쓴다
 |        = persistence.xml 을 찾고, 없으면 패키지 스캔으로 엔티티를 모은다
 |
 | L391 determinePersistenceUnitInfo(managerToUse)
 |        영속성 유닛 정보 확정 (이름, 엔티티 목록, 데이터 소스, 트랜잭션 타입)
 |
 +-- L393 JpaVendorAdapter 가 있고 정보가 SmartPersistenceUnitInfo 면
 |        벤더 루트 패키지를 알려 준다 (LTW 스캔 범위 등에 쓰인다)
 |
 +-- L405 유닛에 qualifier 애노테이션 이름이 있으면
 |        이 팩토리 빈의 빈 정의에 AutowireCandidateQualifier 로 붙인다
 |        = 팩토리가 여럿일 때 주입 지점에서 골라 쓸 수 있게 한다
 |
 +-- L419 super.afterPropertiesSet()  (AbstractEntityManagerFactoryBean)
        L377 벤더 어댑터에서 PersistenceProvider 를 받는다
        L382 벤더 프로퍼티를 병합한다 (사용자가 직접 넣은 값이 우선)
        L389 EntityManagerFactory / EntityManager 인터페이스도 벤더 것으로
        이어서 createNativeEntityManagerFactory 를 부르고 결과를 프록시로 감싼다
```

```text
 설정 세 갈래가 만나는 자리

 PersistenceUnitManager   무엇을 매핑할 것인가 (엔티티 목록, 데이터 소스)
 JpaVendorAdapter         누가 구현할 것인가 (하이버네이트/EclipseLink)
 jpaProperties            벤더에게 직접 넘길 값 (hibernate.* 등)
```

1. 실제 팩토리 생성은 [createNativeEntityManagerFactory](01_LocalContainerEntityManagerFactoryBean.createNativeEntityManagerFactory/README.md)에서 일어난다.

## 결과가 쓰이는 곳

```text
 확정된 PersistenceUnitInfo
      --> PersistenceProvider 에 그대로 넘어간다
      --> 벤더는 이 정보만 보고 매핑을 구성한다. persistence.xml 이 없어도 되는 이유다

 병합된 jpaPropertyMap
      --> 사용자가 넣은 값이 벤더 어댑터 기본값을 덮는다 (L384 containsKey 검사)
      --> 그래서 hibernate.hbm2ddl.auto 같은 값을 설정으로 바꿀 수 있다

 qualifier
      --> EntityManagerFactory 가 둘 이상일 때 주입 지점의 한정자와 맞춘다

 이 빈 자체
      --> FactoryBean 이므로 컨테이너에는 EntityManagerFactory 가 등록된다
      --> 팩토리 빈 객체가 필요하면 &emf 로 꺼낸다
```

`FactoryBean`이 컨테이너에서 어떻게 다뤄지는지는 [빈 생성의 FactoryBean](../../bean-creation/spi/FactoryBean/README.md)에 있다.

## 하위 메서드

- [01 LocalContainerEntityManagerFactoryBean.createNativeEntityManagerFactory](01_LocalContainerEntityManagerFactoryBean.createNativeEntityManagerFactory/README.md)

# AbstractBeanFactory.doGetBean

상위: [Spring 빈 생성](../README.md)

모든 `getBean` 호출이 도착하는 곳이다. 이미 만들어진 싱글톤이면 캐시에서 바로 돌려주고, 아니면 스코프에 맞는 생성 경로로 넘긴다. `depends-on` 빈을 먼저 만드는 것도 여기다.

## 실제 코드

`spring-beans` / `org.springframework.beans.factory.support` / `AbstractBeanFactory.java` L249-L413 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/support/AbstractBeanFactory.java#L249-L413))

```java
// AbstractBeanFactory.java L249-L413
protected <T> T doGetBean(
        String name, @Nullable Class<T> requiredType, @Nullable Object @Nullable [] args, boolean typeCheckOnly)
        throws BeansException {

    String beanName = transformedBeanName(name);
    Object beanInstance;

    // Eagerly check singleton cache for manually registered singletons.
    Object sharedInstance = getSingleton(beanName);
    if (sharedInstance != null && args == null) {
        if (logger.isTraceEnabled()) {
            if (isSingletonCurrentlyInCreation(beanName)) {
                logger.trace("Returning eagerly cached instance of singleton bean '" + beanName +
                        "' that is not fully initialized yet - a consequence of a circular reference");
            }
            else {
                logger.trace("Returning cached instance of singleton bean '" + beanName + "'");
            }
        }
        beanInstance = getObjectForBeanInstance(sharedInstance, requiredType, name, beanName, null);
    }

    else {
        // Fail if we're already creating this bean instance:
        // We're assumably within a circular reference.
        if (isPrototypeCurrentlyInCreation(beanName)) {
            throw new BeanCurrentlyInCreationException(beanName);
        }

        // Check if bean definition exists in this factory.
        BeanFactory parentBeanFactory = getParentBeanFactory();
        if (parentBeanFactory != null && !containsBeanDefinition(beanName)) {
            // Not found -> check parent.
            String nameToLookup = originalBeanName(name);
            if (parentBeanFactory instanceof AbstractBeanFactory abf) {
                return abf.doGetBean(nameToLookup, requiredType, args, typeCheckOnly);
            }
            else if (args != null) {
                // Delegation to parent with explicit args.
                return (T) parentBeanFactory.getBean(nameToLookup, args);
            }
            else if (requiredType != null) {
                // No args -> delegate to standard getBean method.
                return parentBeanFactory.getBean(nameToLookup, requiredType);
            }
            else {
                return (T) parentBeanFactory.getBean(nameToLookup);
            }
        }

        if (!typeCheckOnly) {
            markBeanAsCreated(beanName);
        }

        StartupStep beanCreation = this.applicationStartup.start("spring.beans.instantiate")
                .tag("beanName", name);
        try {
            if (requiredType != null) {
                beanCreation.tag("beanType", requiredType::toString);
            }
            RootBeanDefinition mbd = getMergedLocalBeanDefinition(beanName);
            checkMergedBeanDefinition(mbd, beanName, args);

            // Guarantee initialization of beans that the current bean depends on.
            String[] dependsOn = mbd.getDependsOn();
            if (dependsOn != null) {
                for (String dep : dependsOn) {
                    if (isDependent(beanName, dep)) {
                        throw new BeanCreationException(mbd.getResourceDescription(), beanName,
                                "Circular depends-on relationship between '" + beanName + "' and '" + dep + "'");
                    }
                    registerDependentBean(dep, beanName);
                    try {
                        getBean(dep);
                    }
                    catch (NoSuchBeanDefinitionException ex) {
                        throw new BeanCreationException(mbd.getResourceDescription(), beanName,
                                "'" + beanName + "' depends on missing bean '" + dep + "'", ex);
                    }
                    catch (BeanCreationException ex) {
                        if (requiredType != null) {
                            // Wrap exception with current bean metadata but only if specifically
                            // requested (indicated by required type), not for depends-on cascades.
                            throw new BeanCreationException(mbd.getResourceDescription(), beanName,
                                    "Failed to initialize dependency '" + ex.getBeanName() + "' of " +
                                            requiredType.getSimpleName() + " bean '" + beanName + "': " +
                                            ex.getMessage(), ex);
                        }
                        throw ex;
                    }
                }
            }

            // Create bean instance.
            if (mbd.isSingleton()) {
                sharedInstance = getSingleton(beanName, () -> {
                    try {
                        return createBean(beanName, mbd, args);
                    }
                    catch (BeansException ex) {
                        // Explicitly remove instance from singleton cache: It might have been put there
                        // eagerly by the creation process, to allow for circular reference resolution.
                        // Also remove any beans that received a temporary reference to the bean.
                        destroySingleton(beanName);
                        throw ex;
                    }
                });
                beanInstance = getObjectForBeanInstance(sharedInstance, requiredType, name, beanName, mbd);
            }

            else if (mbd.isPrototype()) {
                // It's a prototype -> create a new instance.
                Object prototypeInstance = null;
                try {
                    beforePrototypeCreation(beanName);
                    prototypeInstance = createBean(beanName, mbd, args);
                }
                finally {
                    afterPrototypeCreation(beanName);
                }
                beanInstance = getObjectForBeanInstance(prototypeInstance, requiredType, name, beanName, mbd);
            }

            else {
                String scopeName = mbd.getScope();
                if (!StringUtils.hasLength(scopeName)) {
                    throw new IllegalStateException("No scope name defined for bean '" + beanName + "'");
                }
                Scope scope = this.scopes.get(scopeName);
                if (scope == null) {
                    throw new IllegalStateException("No Scope registered for scope name '" + scopeName + "'");
                }
                try {
                    Object scopedInstance = scope.get(beanName, () -> {
                        beforePrototypeCreation(beanName);
                        try {
                            return createBean(beanName, mbd, args);
                        }
                        finally {
                            afterPrototypeCreation(beanName);
                        }
                    });
                    beanInstance = getObjectForBeanInstance(scopedInstance, requiredType, name, beanName, mbd);
                }
                catch (IllegalStateException ex) {
                    throw new ScopeNotActiveException(beanName, scopeName, ex);
                }
            }
        }
        catch (BeansException ex) {
            beanCreation.tag("exception", ex.getClass().toString());
            beanCreation.tag("message", String.valueOf(ex.getMessage()));
            cleanupAfterBeanCreationFailure(beanName);
            throw ex;
        }
        finally {
            beanCreation.end();
            if (!isCacheBeanMetadata()) {
                clearMergedBeanDefinition(beanName);
            }
        }
    }

    return adaptBeanInstance(name, beanInstance, requiredType);
}
```

## 동작 흐름

```text
 doGetBean(name, requiredType, args, typeCheckOnly)
 |
 | L253 transformedBeanName    "&myFactory" 의 & 제거, 별칭을 정식 이름으로
 |
 +-- L257 sharedInstance = getSingleton(beanName)       캐시 1차 조회 (잠금 없이)
 |     있고 args == null --> L268 getObjectForBeanInstance --> 반환
 |       (생성 중인 빈이면 "완성 전 조기 참조" 로그, 순환 참조 해소 경로)
 |
 +-- 없으면
       L274 이 프로토타입이 지금 생성 중 --> BeanCurrentlyInCreationException  (프로토타입 순환 참조)
       L280 이 팩토리에 정의가 없고 부모 팩토리가 있음 --> 부모에게 위임
       L300 markBeanAsCreated                정의 병합 결과 캐시 시작 신호
       L309 mbd = getMergedLocalBeanDefinition   부모 정의 상속을 반영한 병합 정의
       L310 checkMergedBeanDefinition            추상 정의면 오류
       |
       L313 depends-on 처리
       |      순환 depends-on --> BeanCreationException
       |      registerDependentBean 후 getBean(의존 빈)   먼저 생성
       |
       +-- L343 싱글톤
       |      getSingleton(beanName, () -> createBean(...))
       |      생성 중 예외 --> destroySingleton 으로 흔적 제거 후 다시 던짐
       |
       +-- L359 프로토타입
       |      beforePrototypeCreation --> createBean --> afterPrototypeCreation
       |      (생성 중 표시만 하고 캐시는 하지 않는다)
       |
       +-- L372 그 밖의 스코프
              scopes 에서 Scope 조회, 없으면 IllegalStateException
              scope.get(beanName, () -> createBean(...))
              스코프가 비활성(요청 밖에서 request 빈 요구) --> ScopeNotActiveException
       |
       L398 실패 --> cleanupAfterBeanCreationFailure 후 예외 전파
 |
 +-- L412 adaptBeanInstance   요구 타입과 다르면 TypeConverter 로 변환 시도
```

1. 싱글톤 생성은 [DefaultSingletonBeanRegistry.getSingleton](01_DefaultSingletonBeanRegistry.getSingleton/README.md)이 잠금과 생성 중 표시를 맡는다.
2. 실제 생성은 [AbstractAutowireCapableBeanFactory.createBean](02_AbstractAutowireCapableBeanFactory.createBean/README.md)이 한다.
3. 결과가 [FactoryBean](../spi/FactoryBean/README.md)이면 `getObjectForBeanInstance`가 `getObject()` 결과로 바꿔 돌려준다.

`spring-beans` / `org.springframework.beans.factory.support` / `AbstractBeanFactory.java` L1854-L1884 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/support/AbstractBeanFactory.java#L1854-L1884))

```java
// AbstractBeanFactory.java L1854-L1884
protected Object getObjectForBeanInstance(Object beanInstance, @Nullable Class<?> requiredType,
        String name, String beanName, @Nullable RootBeanDefinition mbd) {

    // Don't let calling code try to dereference the factory if the bean isn't a factory.
    if (BeanFactoryUtils.isFactoryDereference(name)) {
        if (beanInstance instanceof NullBean) {
            return beanInstance;
        }
        if (!(beanInstance instanceof FactoryBean)) {
            throw new BeanIsNotAFactoryException(beanName, beanInstance.getClass());
        }
        if (mbd != null) {
            mbd.isFactoryBean = true;
        }
        return beanInstance;
    }

    // Now we have the bean instance, which may be a normal bean or a FactoryBean.
    // If it's a FactoryBean, we use it to create a bean instance, unless the
    // caller actually wants a reference to the factory.
    if (!(beanInstance instanceof FactoryBean<?> factoryBean)) {
        return beanInstance;
    }

    Object object = null;
    if (mbd != null) {
        mbd.isFactoryBean = true;
    }
    else {
        object = getCachedObjectForFactoryBean(beanName);
    }
```

## 결과가 쓰이는 곳

```text
 반환한 빈
      --> preInstantiateSingletons: 싱글톤 캐시에 남고 컨테이너 기동 완료로 이어짐
      --> resolveDependency: 주입 대상 필드/파라미터 값
      --> 사용자 코드

 markBeanAsCreated 표시
      --> 이후 이 빈의 정의 변경을 금지하는 근거 (이미 만든 빈의 정의를 바꾸면 불일치)
      --> 병합 정의 캐시 유지

 registerDependentBean 으로 기록한 의존 관계
      --> 소멸 시 역순 파괴 (의존하는 쪽을 먼저 파괴)
      --> 순환 참조 검사의 입력

 args 를 준 getBean(name, args)
      --> 캐시를 건너뛰고 항상 새로 만든다 (프로토타입 전용 경로)
```

## 하위 메서드

- [01 DefaultSingletonBeanRegistry.getSingleton](01_DefaultSingletonBeanRegistry.getSingleton/README.md)
- [02 AbstractAutowireCapableBeanFactory.createBean](02_AbstractAutowireCapableBeanFactory.createBean/README.md)

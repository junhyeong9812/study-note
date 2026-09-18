# AbstractAutowireCapableBeanFactory.createBeanInstance

상위: [AbstractAutowireCapableBeanFactory.doCreateBean](../README.md)

객체를 실제로 만든다. 공급자 함수, 팩토리 메서드(`@Bean`), 생성자 주입, 기본 생성자 중 하나를 고른다. 이 단계가 끝나면 필드가 비어 있는 맨 객체가 `BeanWrapper`에 담겨 나온다.

## 실제 코드

`spring-beans` / `org.springframework.beans.factory.support` / `AbstractAutowireCapableBeanFactory.java` L1175-L1230 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/support/AbstractAutowireCapableBeanFactory.java#L1175-L1230))

```java
// AbstractAutowireCapableBeanFactory.java L1175-L1230
protected BeanWrapper createBeanInstance(String beanName, RootBeanDefinition mbd, @Nullable Object @Nullable [] args) {
    // Make sure bean class is actually resolved at this point.
    Class<?> beanClass = resolveBeanClass(mbd, beanName);

    if (beanClass != null && !Modifier.isPublic(beanClass.getModifiers()) && !mbd.isNonPublicAccessAllowed()) {
        throw new BeanCreationException(mbd.getResourceDescription(), beanName,
                "Bean class isn't public, and non-public access not allowed: " + beanClass.getName());
    }

    if (args == null) {
        Supplier<?> instanceSupplier = mbd.getInstanceSupplier();
        if (instanceSupplier != null) {
            return obtainFromSupplier(instanceSupplier, beanName, mbd);
        }
    }

    if (mbd.getFactoryMethodName() != null) {
        return instantiateUsingFactoryMethod(beanName, mbd, args);
    }

    // Shortcut when re-creating the same bean...
    boolean resolved = false;
    boolean autowireNecessary = false;
    if (args == null) {
        synchronized (mbd.constructorArgumentLock) {
            if (mbd.resolvedConstructorOrFactoryMethod != null) {
                resolved = true;
                autowireNecessary = mbd.constructorArgumentsResolved;
            }
        }
    }
    if (resolved) {
        if (autowireNecessary) {
            return autowireConstructor(beanName, mbd, null, null);
        }
        else {
            return instantiateBean(beanName, mbd);
        }
    }

    // Candidate constructors for autowiring?
    Constructor<?>[] ctors = determineConstructorsFromBeanPostProcessors(beanClass, beanName);
    if (ctors != null || mbd.getResolvedAutowireMode() == AUTOWIRE_CONSTRUCTOR ||
            mbd.hasConstructorArgumentValues() || !ObjectUtils.isEmpty(args)) {
        return autowireConstructor(beanName, mbd, ctors, args);
    }

    // Preferred constructors for default construction?
    ctors = mbd.getPreferredConstructors();
    if (ctors != null) {
        return autowireConstructor(beanName, mbd, ctors, null);
    }

    // No special handling: simply use no-arg constructor.
    return instantiateBean(beanName, mbd);
}
```

## 동작 흐름

```text
 createBeanInstance(beanName, mbd, args)
 |
 | L1177 resolveBeanClass
 | L1179 public 이 아닌 클래스 + 비공개 접근 불허 --> BeanCreationException
 |
 +-- L1185 instanceSupplier 있음 (프로그램 방식 등록, AOT 생성 코드)
 |      --> obtainFromSupplier
 |
 +-- L1191 factoryMethodName 있음  (@Bean 메서드, 팩토리 빈 메서드)
 |      --> instantiateUsingFactoryMethod
 |            인스턴스 @Bean : factoryBeanName 으로 설정 클래스 빈을 먼저 getBean
 |            static @Bean   : 클래스의 정적 메서드 직접 호출
 |            메서드 파라미터는 생성자 주입과 같은 방식으로 해석
 |
 +-- L1196 이전에 해석해 둔 생성자/팩토리 메서드가 있음 (같은 정의로 재생성)
 |      autowireNecessary --> autowireConstructor / 아니면 instantiateBean
 |
 +-- L1216 determineConstructorsFromBeanPostProcessors
 |      SmartInstantiationAwareBeanPostProcessor 에게 "쓸 생성자" 질의
 |        AutowiredAnnotationBeanPostProcessor 가 @Autowired 생성자를 고르고,
 |        생성자가 하나뿐이고 파라미터가 있으면 그 생성자를 고른다
 |      후보 있음 | AUTOWIRE_CONSTRUCTOR 모드 | 생성자 인자 정의 | 명시 args
 |        --> autowireConstructor
 |              파라미터마다 resolveDependency 로 주입 대상 탐색
 |
 +-- L1223 preferredConstructors (Kotlin 주 생성자 등) --> autowireConstructor
 |
 +-- L1229 그 밖 --> instantiateBean   기본 생성자
```

생성자 파라미터를 해석할 때도 주입 경로는 같다. 자세한 것은 [populateBean](../02_AbstractAutowireCapableBeanFactory.populateBean/README.md) 아래의 [resolveDependency](../02_AbstractAutowireCapableBeanFactory.populateBean/01_DefaultListableBeanFactory.resolveDependency/README.md)에 있다.

## 결과가 쓰이는 곳

```text
 BeanWrapper (맨 객체 + 타입 변환기)
      --> doCreateBean [2] 정의 후처리의 beanType 입력
      --> populateBean 의 프로퍼티 설정 대상
      --> initializeBean 의 대상 객체

 해석 결과 캐시 (resolvedConstructorOrFactoryMethod, constructorArgumentsResolved)
      --> 프로토타입처럼 같은 정의로 여러 번 만들 때 생성자 탐색을 건너뜀

 생성자 주입으로 들어간 의존 빈
      --> 이 시점에 이미 완성된 빈이어야 한다
          = 생성자 순환 참조는 조기 참조로 풀 수 없어 BeanCurrentlyInCreationException
```

`@Autowired` 필드 주입과 달리 생성자 주입은 인스턴스화 시점에 의존 빈을 요구하므로, 순환 참조가 있으면 여기서 실패한다. 이것이 생성자 주입이 순환 참조를 조기에 드러내는 이유다.

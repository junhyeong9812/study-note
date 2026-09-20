# BeanRegistrationsAotProcessor.processAheadOfTime

상위: [BeanFactoryInitializationAotContributions.applyTo](../README.md)

빈 정의 하나하나를 "그 빈을 등록하는 자바 코드"로 바꿀 준비를 한다. AOT가 대체하는 것의 핵심이 이 처리기다.

## 실제 코드

`spring-beans` / `org.springframework.beans.factory.aot` / `BeanRegistrationsAotProcessor.java` L38-L62 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/aot/BeanRegistrationsAotProcessor.java#L38-L62))

```java
// BeanRegistrationsAotProcessor.java L38-L62
class BeanRegistrationsAotProcessor implements BeanFactoryInitializationAotProcessor {

    @Override
    public @Nullable BeanRegistrationsAotContribution processAheadOfTime(ConfigurableListableBeanFactory beanFactory) {
        BeanDefinitionMethodGeneratorFactory beanDefinitionMethodGeneratorFactory =
                new BeanDefinitionMethodGeneratorFactory(beanFactory);
        List<Registration> registrations = new ArrayList<>();

        for (String beanName : beanFactory.getBeanDefinitionNames()) {
            RegisteredBean registeredBean = RegisteredBean.of(beanFactory, beanName);
            BeanDefinitionMethodGenerator beanDefinitionMethodGenerator =
                    beanDefinitionMethodGeneratorFactory.getBeanDefinitionMethodGenerator(registeredBean);
            if (beanDefinitionMethodGenerator != null) {
                registrations.add(new Registration(registeredBean, beanDefinitionMethodGenerator,
                        beanFactory.getAliases(beanName)));
            }
        }

        if (registrations.isEmpty()) {
            return null;
        }
        return new BeanRegistrationsAotContribution(registrations);
    }

}
```

## 동작 흐름

```text
 processAheadOfTime(beanFactory)
 |
 | L42 BeanDefinitionMethodGeneratorFactory 를 만든다
 |        빈마다 등록 메서드를 만들 수 있는지 판단하는 팩토리다
 |
 +-- L46 빈 정의 이름을 전부 순회
 |      L47 RegisteredBean.of(beanFactory, beanName)
 |             정의와 팩토리를 묶은 분석용 뷰
 |      L48 getBeanDefinitionMethodGenerator(registeredBean)
 |             null 이면 이 빈은 코드로 만들지 않는다
 |               BeanRegistrationExcludeFilter 가 걸렀거나
 |               인프라 빈이라 생성이 불필요한 경우다
 |      L51 만들 수 있으면 Registration 으로 담는다 (별칭도 함께)
 |
 +-- L56 하나도 없으면 null 을 돌려준다
 |        = 기여하지 않는다. 코드도 힌트도 생기지 않는다
 |
 +-- L59 있으면 BeanRegistrationsAotContribution 으로 감싸 돌려준다
```

```text
 무엇이 코드가 되는가

 빈 정의 하나            --> 등록 메서드 하나
   클래스, 스코프, 초기화/소멸 메서드, 프로퍼티 값이 코드로 박힌다
 생성자와 주입 지점      --> InstanceSupplier 코드
   리플렉션 대신 직접 호출문이 된다
 별칭                    --> registerAlias 호출

 결과적으로 애노테이션을 런타임에 읽을 일이 없어진다
```

## 결과가 쓰이는 곳

```text
 반환한 기여
      --> applyTo 때 BeanRegistrationsCode 를 만들고
          빈마다 등록 메서드를 생성한다

 null 반환
      --> 등록할 빈이 하나도 없다는 뜻이다
      --> 빈 팩토리가 비어 있는 특수한 경우에나 나온다

 BeanRegistrationAotProcessor 와의 관계
      --> 이 처리기는 빈 "전체"를 훑는 쪽이다
      --> 빈 하나에 개입하려면 BeanRegistrationAotProcessor 를 구현한다
          그쪽은 BeanDefinitionMethodGeneratorFactory 가 빈마다 호출한다

 제외 필터
      --> BeanRegistrationExcludeFilter 로 특정 빈을 생성에서 뺄 수 있다
      --> 런타임에만 의미 있는 인프라 빈이 그 대상이다
```

빈 정의가 만들어지는 런타임 경로는 [빈 정의 등록](../../../container-refresh/01_AbstractApplicationContext.refresh/04_AbstractApplicationContext.invokeBeanFactoryPostProcessors/01_PostProcessorRegistrationDelegate.invokeBeanFactoryPostProcessors/01_ConfigurationClassPostProcessor.processConfigBeanDefinitions/02_ConfigurationClassBeanDefinitionReader.loadBeanDefinitions/README.md)에 있다.

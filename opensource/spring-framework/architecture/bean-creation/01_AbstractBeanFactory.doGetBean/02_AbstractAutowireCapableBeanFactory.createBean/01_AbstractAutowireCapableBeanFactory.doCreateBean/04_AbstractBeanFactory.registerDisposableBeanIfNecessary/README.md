# AbstractBeanFactory.registerDisposableBeanIfNecessary

상위: [AbstractAutowireCapableBeanFactory.doCreateBean](../README.md)

빈이 소멸 시 할 일이 있으면 어댑터로 감싸 등록한다. 싱글톤은 컨테이너가, 스코프 빈은 그 스코프가 보관한다. 프로토타입은 등록하지 않는다.

## 실제 코드

`spring-beans` / `org.springframework.beans.factory.support` / `AbstractBeanFactory.java` L1935-L1954 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/support/AbstractBeanFactory.java#L1935-L1954))

```java
// AbstractBeanFactory.java L1935-L1954
protected void registerDisposableBeanIfNecessary(String beanName, Object bean, RootBeanDefinition mbd) {
    if (!mbd.isPrototype() && requiresDestruction(bean, mbd)) {
        if (mbd.isSingleton()) {
            // Register a DisposableBean implementation that performs all destruction
            // work for the given bean: DestructionAwareBeanPostProcessors,
            // DisposableBean interface, custom destroy method.
            registerDisposableBean(beanName, new DisposableBeanAdapter(
                    bean, beanName, mbd, getBeanPostProcessorCache().destructionAware));
        }
        else {
            // A bean with a custom scope...
            Scope scope = this.scopes.get(mbd.getScope());
            if (scope == null) {
                throw new IllegalStateException("No Scope registered for scope name '" + mbd.getScope() + "'");
            }
            scope.registerDestructionCallback(beanName, new DisposableBeanAdapter(
                    bean, beanName, mbd, getBeanPostProcessorCache().destructionAware));
        }
    }
}
```

## 동작 흐름

```text
 registerDisposableBeanIfNecessary(beanName, bean, mbd)
 |
 +-- 프로토타입 --> 아무것도 하지 않음
 |     = 컨테이너는 프로토타입의 소멸을 책임지지 않는다 (@PreDestroy 도 호출되지 않음)
 |
 +-- requiresDestruction(bean, mbd) 가 false --> 등록 없음
 |     판정 근거: DisposableBean 구현 / AutoCloseable / 정의의 destroy-method /
 |               DestructionAwareBeanPostProcessor 가 "처리 대상"이라고 답함(@PreDestroy)
 |
 +-- 싱글톤 --> registerDisposableBean(이름, DisposableBeanAdapter)
 |                컨테이너의 disposableBeans 에 보관
 |
 +-- 스코프 빈 --> scope.registerDestructionCallback(이름, DisposableBeanAdapter)
                   예: 세션 스코프면 세션이 끝날 때 호출
```

## 결과가 쓰이는 곳

```text
 DisposableBeanAdapter
      --> 컨테이너 close --> destroySingletons --> 어댑터 실행 순서
            1) DestructionAwareBeanPostProcessor  (@PreDestroy)
            2) DisposableBean.destroy()
            3) 정의의 destroy-method / @Bean(destroyMethod)
      --> 의존 관계 기록을 따라 "나에게 의존하는 빈" 을 먼저 파괴

 등록하지 않은 프로토타입
      --> 소멸 처리는 애플리케이션 코드 책임
          필요하면 컨테이너 밖에서 직접 destroyBean(bean) 호출

 @Bean 의 destroyMethod 기본값
      --> 추론 모드라 close / shutdown 메서드가 있으면 자동으로 소멸 메서드가 된다
```

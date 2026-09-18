# TargetSource

상위: [Spring AOP 프록시](../../README.md) / [spi](../README.md)

프록시가 위임할 실제 객체를 공급한다. 대부분은 싱글톤 하나를 계속 돌려주지만, 호출마다 다른 객체를 주거나 풀에서 빌려줄 수도 있다.

## 실제 코드

`spring-aop` / `org.springframework.aop` / `TargetSource.java` L36-L78 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-aop/src/main/java/org/springframework/aop/TargetSource.java#L36-L78))

```java
// TargetSource.java L36-L78
public interface TargetSource extends TargetClassAware {

    @Override
    @Nullable Class<?> getTargetClass();

    default boolean isStatic() {
        return false;
    }

    @Nullable Object getTarget() throws Exception;

    default void releaseTarget(Object target) throws Exception {
    }

}
```

## 흐름에서 불리는 자리

```text
 프록시 생성
   wrapIfNecessary --> new SingletonTargetSource(bean) 로 감싸 ProxyFactory 에 설정
 호출
   invoke / intercept 가 targetSource.getTarget() 으로 타깃을 얻고
   isStatic() 이 false 면 finally 에서 releaseTarget()
```

- [wrapIfNecessary](../../01_AbstractAutoProxyCreator.postProcessAfterInitialization/01_AbstractAutoProxyCreator.wrapIfNecessary/README.md)
- [JdkDynamicAopProxy.invoke](../../02_JdkDynamicAopProxy.invoke/README.md)

## 구현 계층

```text
 TargetSource
   +-- SingletonTargetSource        항상 같은 객체 (기본)
   +-- SimpleBeanTargetSource       호출마다 beanFactory.getBean (스코프 프록시)
   +-- PrototypeTargetSource        호출마다 새 프로토타입
   +-- CommonsPool2TargetSource     풀에서 빌려주고 반납
   +-- HotSwappableTargetSource     런타임에 타깃 교체
   +-- EmptyTargetSource            타깃 없음 (인터페이스만 있는 프록시)

 isStatic() = true 면 컨테이너가 타깃을 캐시해도 된다는 뜻
```

# AopProxy

상위: [Spring AOP 프록시](../../README.md) / [spi](../README.md)

프록시 객체를 만들어 내는 전략이다. 구현이 둘뿐이고, 어느 쪽을 쓸지는 설정과 타깃 타입이 정한다.

## 실제 코드

`spring-aop` / `org.springframework.aop.framework` / `AopProxy.java` L32-L64 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-aop/src/main/java/org/springframework/aop/framework/AopProxy.java#L32-L64))

```java
// AopProxy.java L32-L64
public interface AopProxy {

    Object getProxy();

    Object getProxy(@Nullable ClassLoader classLoader);

    Class<?> getProxyClass(@Nullable ClassLoader classLoader);

}
```

## 흐름에서 불리는 자리

```text
 buildProxy --> ProxyFactory.getProxy(classLoader)
   --> ProxyCreatorSupport.createAopProxy()
         --> DefaultAopProxyFactory.createAopProxy(config)
               JdkDynamicAopProxy 또는 ObjenesisCglibAopProxy
   --> aopProxy.getProxy(classLoader)  실제 객체 생성
```

- [DefaultAopProxyFactory.createAopProxy](../../01_AbstractAutoProxyCreator.postProcessAfterInitialization/01_AbstractAutoProxyCreator.wrapIfNecessary/02_AbstractAutoProxyCreator.buildProxy/01_DefaultAopProxyFactory.createAopProxy/README.md)
- [buildProxy](../../01_AbstractAutoProxyCreator.postProcessAfterInitialization/01_AbstractAutoProxyCreator.wrapIfNecessary/02_AbstractAutoProxyCreator.buildProxy/README.md)

## 구현 계층

```text
 AopProxy
   +-- JdkDynamicAopProxy        InvocationHandler 겸용. 인터페이스 프록시
   +-- CglibAopProxy             하위 클래스 생성
         +-- ObjenesisCglibAopProxy   생성자 호출 없이 인스턴스화 (기본)

 AdvisedSupport (= ProxyFactory 의 상위)
   프록시가 들고 다니는 설정: 어드바이저 목록, 인터페이스, 타깃 소스, 플래그
   Advised 로 캐스팅해 런타임 조회 가능
```

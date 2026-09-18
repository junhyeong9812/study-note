# DefaultAopProxyFactory.createAopProxy

상위: [AbstractAutoProxyCreator.buildProxy](../README.md)

설정을 보고 JDK 동적 프록시와 CGLIB 하위 클래스 프록시 중 하나를 고른다. 두 구현 모두 [AopProxy](../../../../spi/AopProxy/README.md)이고, `getProxy()`가 실제 객체를 만든다.

## 실제 코드

`spring-aop` / `org.springframework.aop.framework` / `DefaultAopProxyFactory.java` L59-L76 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-aop/src/main/java/org/springframework/aop/framework/DefaultAopProxyFactory.java#L59-L76))

```java
// DefaultAopProxyFactory.java L59-L76
@Override
public AopProxy createAopProxy(AdvisedSupport config) throws AopConfigException {
    if (config.isOptimize() || config.isProxyTargetClass() || !config.hasUserSuppliedInterfaces()) {
        Class<?> targetClass = config.getTargetClass();
        if (targetClass == null && config.getProxiedInterfaces().length == 0) {
            throw new AopConfigException("TargetSource cannot determine target class: " +
                    "Either an interface or a target is required for proxy creation.");
        }
        if (targetClass == null || targetClass.isInterface() ||
                Proxy.isProxyClass(targetClass) || ClassUtils.isLambdaClass(targetClass)) {
            return new JdkDynamicAopProxy(config);
        }
        return new ObjenesisCglibAopProxy(config);
    }
    else {
        return new JdkDynamicAopProxy(config);
    }
}
```

## 동작 흐름

```text
 createAopProxy(config)
 |
 +-- optimize | proxyTargetClass | 사용자가 준 인터페이스가 없음
 |      |
 |      +-- 타깃 클래스도 없고 인터페이스도 없음 --> AopConfigException
 |      |
 |      +-- 타깃이 인터페이스 / 이미 JDK 프록시 / 람다
 |      |     --> JdkDynamicAopProxy
 |      |
 |      +-- 그 밖 (일반 클래스)
 |            --> ObjenesisCglibAopProxy      런타임에 하위 클래스를 생성
 |
 +-- 그 밖 (사용자가 인터페이스를 지정했고 클래스 프록시를 요구하지 않음)
        --> JdkDynamicAopProxy
```

두 방식의 차이는 다음과 같다.

```text
 JDK 동적 프록시
   대상: 인터페이스
   생성: java.lang.reflect.Proxy
   한계: 인터페이스에 선언된 메서드만 가로챈다. 구체 클래스로 주입 불가
   호출: JdkDynamicAopProxy.invoke

 CGLIB 프록시
   대상: 클래스 (하위 클래스를 만들어 메서드를 오버라이드)
   생성: Objenesis 로 생성자 호출 없이 인스턴스화
   한계: final 클래스/메서드는 가로챌 수 없다. private 메서드도 불가
   호출: CglibAopProxy 의 DynamicAdvisedInterceptor.intercept
```

Spring Boot는 기본으로 `proxyTargetClass = true`를 쓰므로 대부분 CGLIB이다.

## 결과가 쓰이는 곳

```text
 AopProxy.getProxy(classLoader)
      --> 실제 프록시 객체 --> wrapIfNecessary 의 반환값 --> 컨테이너의 빈

 선택된 방식
      --> 호출 경로가 갈린다
          JDK   --> JdkDynamicAopProxy.invoke
          CGLIB --> DynamicAdvisedInterceptor.intercept
      --> 두 경로 모두 같은 ReflectiveMethodInvocation.proceed 로 모인다

 CGLIB 프록시의 생성자
      --> Objenesis 사용으로 타깃 생성자가 두 번 호출되지 않는다
          (필드 초기화가 프록시 인스턴스에서는 일어나지 않는다는 뜻)
```

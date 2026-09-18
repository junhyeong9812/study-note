# AbstractAutoProxyCreator.postProcessAfterInitialization

상위: [Spring AOP 프록시](../README.md)

빈 생성의 마지막 확장 지점이다. 초기화까지 끝난 객체를 받아, 적용할 어드바이스가 있으면 프록시로 바꿔 돌려준다. 순환 참조 때문에 이미 조기 참조로 프록시를 만들어 내보냈다면 여기서는 그대로 통과시킨다.

## 실제 코드

`spring-aop` / `org.springframework.aop.framework.autoproxy` / `AbstractAutoProxyCreator.java` L284-L293 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-aop/src/main/java/org/springframework/aop/framework/autoproxy/AbstractAutoProxyCreator.java#L284-L293))

```java
// AbstractAutoProxyCreator.java L284-L293
@Override
public @Nullable Object postProcessAfterInitialization(@Nullable Object bean, String beanName) {
    if (bean != null) {
        Object cacheKey = getCacheKey(bean.getClass(), beanName);
        if (this.earlyBeanReferences.remove(cacheKey) != bean) {
            return wrapIfNecessary(bean, beanName, cacheKey);
        }
    }
    return bean;
}
```

## 동작 흐름

```text
 postProcessAfterInitialization(bean, beanName)
 |
 | L287 cacheKey = (빈 클래스, 빈 이름) 조합
 |
 +-- L288 earlyBeanReferences 에서 이 키를 꺼낸 값이 지금 빈과 같다?
 |      같다  --> 조기 참조 단계에서 이미 프록시를 만들어 내보냈다
 |                --> 그대로 반환 (두 번 감싸지 않는다)
 |      다르다 --> wrapIfNecessary
```

조기 참조 경로는 순환 참조에서 쓰인다. `getEarlyBeanReference`가 먼저 프록시를 만들어 다른 빈에 주입해 두고, 여기서는 중복 래핑을 피한다.

1. 실제 판단과 생성은 [wrapIfNecessary](01_AbstractAutoProxyCreator.wrapIfNecessary/README.md)가 한다.

## 결과가 쓰이는 곳

```text
 반환 객체
      +-- 프록시   --> initializeBean 의 반환값 --> doCreateBean 의 exposedObject
      |                --> 싱글톤 캐시, 다른 빈에 주입되는 것도 이 프록시
      +-- 원본     --> 프록시 없이 그대로 빈이 됨

 advisedBeans 캐시 (키 -> 프록시 대상 여부)
      --> 같은 빈을 다시 검사하지 않게 함

 proxyTypes 캐시 (키 -> 프록시 클래스)
      --> predictBeanType 에서 "이 빈의 최종 타입" 을 미리 답하는 근거
          = 주입 대상 타입 판정이 프록시 타입 기준으로 이뤄진다
```

## 하위 메서드

- [01 AbstractAutoProxyCreator.wrapIfNecessary](01_AbstractAutoProxyCreator.wrapIfNecessary/README.md)

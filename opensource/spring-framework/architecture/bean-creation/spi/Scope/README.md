# Scope

상위: [Spring 빈 생성](../../README.md) / [spi](../README.md)

싱글톤도 프로토타입도 아닌 수명 주기를 정의한다. 빈 인스턴스를 어디에 보관하고 언제 버릴지는 이 구현이 정한다.

## 실제 코드

`spring-beans` / `org.springframework.beans.factory.config` / `Scope.java` L61-L158 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/config/Scope.java#L61-L158))

```java
// Scope.java L61-L158
public interface Scope {

    Object get(String name, ObjectFactory<?> objectFactory);

    @Nullable Object remove(String name);

    void registerDestructionCallback(String name, Runnable callback);

    default @Nullable Object resolveContextualObject(String key) {
        return null;
    }

    default @Nullable String getConversationId() {
        return null;
    }

}
```

## 흐름에서 불리는 자리

```text
 doGetBean L372 기타 스코프 분기
   scopes 에서 이름으로 Scope 조회 (없으면 IllegalStateException)
   scope.get(beanName, () -> createBean(...))
     구현이 보관소에서 찾고, 없으면 팩토리를 호출해 만든 뒤 보관
   비활성 상태면 ScopeNotActiveException
 registerDisposableBeanIfNecessary
   scope.registerDestructionCallback(이름, 어댑터)
```

- [AbstractBeanFactory.doGetBean](../../01_AbstractBeanFactory.doGetBean/README.md)
- [registerDisposableBeanIfNecessary](../../01_AbstractBeanFactory.doGetBean/02_AbstractAutowireCapableBeanFactory.createBean/01_AbstractAutowireCapableBeanFactory.doCreateBean/04_AbstractBeanFactory.registerDisposableBeanIfNecessary/README.md)

## 구현 계층

```text
 Scope
   +-- SimpleThreadScope          스레드별 (spring-context, 직접 등록해서 사용)
   +-- RequestScope               HTTP 요청           (웹 컨텍스트가 등록)
   +-- SessionScope               HTTP 세션
   +-- ServletContextScope        애플리케이션
   +-- (커스텀 Scope 는 CustomScopeConfigurer 로 등록)

 스코프 빈을 싱글톤에 주입할 때
   scoped proxy 가 필요하다 (@Scope(proxyMode = TARGET_CLASS))
   프록시가 호출 시점마다 현재 스코프의 실제 객체를 찾는다
```

# AbstractConfiguredSecurityBuilder.doBuild

상위: [AbstractSecurityBuilder.build](../README.md)

`init` -> `configure` -> `performBuild` 세 단계를 돌린다. 설정 DSL 전체의 뼈대다.

## 위치

`config` / `org.springframework.security.config.annotation` / `AbstractConfiguredSecurityBuilder.java` L328-L342 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/config/src/main/java/org/springframework/security/config/annotation/AbstractConfiguredSecurityBuilder.java#L328-L342))

## 실제 코드

```java
// AbstractConfiguredSecurityBuilder.java L328-L342
@Override
protected final O doBuild() {
    synchronized (this.configurers) {
        this.buildState = BuildState.INITIALIZING;
        beforeInit();
        init();
        this.buildState = BuildState.CONFIGURING;
        beforeConfigure();
        configure();
        this.buildState = BuildState.BUILDING;
        O result = performBuild();
        this.buildState = BuildState.BUILT;
        return result;
    }
}
```

두 단계의 실제 순회는 바로 아래에 있다.

`config` / `org.springframework.security.config.annotation` / `AbstractConfiguredSecurityBuilder.java` L367-L388 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/config/src/main/java/org/springframework/security/config/annotation/AbstractConfiguredSecurityBuilder.java#L367-L388))

```java
// AbstractConfiguredSecurityBuilder.java L367-L388
@SuppressWarnings("unchecked")
private void init() {
    Collection<SecurityConfigurer<O, B>> configurers = getConfigurers();
    for (SecurityConfigurer<O, B> configurer : configurers) {
        configurer.init((B) this);
    }
    while (!this.configurersAddedInInitializing.isEmpty()) {
        List<SecurityConfigurer<O, B>> toInit = this.configurersAddedInInitializing;
        this.configurersAddedInInitializing = new ArrayList<>();
        for (SecurityConfigurer<O, B> configurer : toInit) {
            configurer.init((B) this);
        }
    }
}

@SuppressWarnings("unchecked")
private void configure() {
    Collection<SecurityConfigurer<O, B>> configurers = getConfigurers();
    for (SecurityConfigurer<O, B> configurer : configurers) {
        configurer.configure((B) this);
    }
}
```

## 동작 흐름

```text
 doBuild()
 |
 | L330 synchronized (this.configurers)
 |
 | L331 buildState = INITIALIZING
 | L332 beforeInit()        하위 클래스의 훅 (기본은 빈 메서드)
 | L333 init()
 |        L371 각 설정자의 init(this)
 |        L373 init 중에 추가된 설정자가 있으면
 |               L377 그것들도 init 한다. 없어질 때까지 반복
 |
 | L334 buildState = CONFIGURING
 | L335 beforeConfigure()   HttpSecurity 가 여기서 AuthenticationManager 를 만든다
 | L336 configure()
 |        L386 각 설정자의 configure(this)
 |
 | L337 buildState = BUILDING
 | L338 performBuild()      하위 클래스가 구현한다
 | L339 buildState = BUILT
 +-- L340 반환
```

```text
 init 만 재귀적으로 돈다

 L373-379 configurersAddedInInitializing 가 빌 때까지 반복한다

 설정자가 init 안에서 다른 설정자를 추가할 수 있기 때문이다
 SecurityConfigurer javadoc 이 "설정자는 여기서 적용해야 한다"고 적고 있다
 예) InitializeUserDetailsBeanManagerConfigurer.init 이
     다른 설정자를 apply 한다

 configure 단계에는 이 반복이 없다 (L382-388)
 애초에 그 단계 이후에는 설정자를 추가할 수 없다 --
 add(L203-222)가 buildState.isConfigured() 이면
 IllegalStateException("Cannot apply ... to already built object") 을 던진다
```

```text
 buildState 가 무엇을 막는가

 UNBUILT -> INITIALIZING -> CONFIGURING -> BUILDING -> BUILT

 설정자를 추가하는 add 메서드가 이 상태를 보고
 "지금 추가해도 되는지"를 판단한다 (L208)

 isConfigured() 는 CONFIGURING 이상이면 참이다 (L461-463)
 즉 configure 단계에 들어간 뒤의 추가는 조용히 무시되는 것이 아니라
 즉시 예외로 실패한다
```

```text
 synchronized 가 걸려 있다

 L330 이 configurers 컬렉션에 락을 건다
 빌드 전체가 한 덩어리로 돈다

 add 도 같은 모니터를 쓰므로 (L207)
 빌드 도중에 설정자가 끼어드는 것을 막는 효과가 있다
```

## 결과가 쓰이는 곳

```text
 init 단계의 산출물
      --> 공유 객체(shared object)에 심긴 값들이다
      --> configure 단계가 그것을 꺼내 쓴다

 configure 단계의 산출물
      --> addFilter 로 쌓인 필터 목록이다
      --> performBuild 가 그것을 정렬해 체인으로 만든다

 단계를 나눈 결과
      --> 설정자 등록 순서와 무관하게 서로를 볼 수 있다
      --> DSL 을 어떤 순서로 써도 결과가 같은 이유의 절반이다
          (나머지 절반은 필터 정렬이다)
```

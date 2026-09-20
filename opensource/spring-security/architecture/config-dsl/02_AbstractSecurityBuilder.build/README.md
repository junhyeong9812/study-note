# AbstractSecurityBuilder.build

상위: [설정 DSL](../README.md)

빌드를 한 번만 허용하는 껍데기다. 실제 일은 하위 클래스의 `doBuild` 가 한다.

## 위치

`config` / `org.springframework.security.config.annotation` / `AbstractSecurityBuilder.java` L31-L54 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/config/src/main/java/org/springframework/security/config/annotation/AbstractSecurityBuilder.java#L31-L54))

## 실제 코드

```java
// AbstractSecurityBuilder.java L31-L54 (javadoc 생략)
private AtomicBoolean building = new AtomicBoolean();

private O object;

@Override
public final O build() {
    if (this.building.compareAndSet(false, true)) {
        this.object = doBuild();
        return this.object;
    }
    throw new AlreadyBuiltException("This object has already been built");
}

public final O getObject() {
    if (!this.building.get()) {
        throw new IllegalStateException("This object has not been built");
    }
    return this.object;
}
```

## 동작 흐름

```text
 build()
 |
 +-- L37 building.compareAndSet(false, true)
 |      |
 |      +-- 성공하면 (처음)
 |             L38 doBuild() 를 부르고 결과를 필드에 담는다
 |             L39 그 값을 반환한다
 |      |
 |      +-- 실패하면 (이미 빌드됨)
 |             L41 AlreadyBuiltException
```

```text
 final 메서드다

 L36 public final O build()

 하위 클래스가 이 한 번 제약을 우회할 수 없다
 확장은 doBuild (L61 abstract) 쪽에서 한다
```

```text
 getObject 와 짝이다

 L49-54 getObject()
   L50 building 이 false 면 IllegalStateException
   빌드가 시작되기 전에 꺼내려는 것을 막는다

 다만 CAS 는 doBuild 실행 전에 true 가 되므로 (L37-38)
 빌드 도중에 부르면 예외 없이 아직 null 인 값이 나온다
 그래서 프레임워크 내부는 buildState 를 따로 본다
```

## 결과가 쓰이는 곳

```text
 AlreadyBuiltException
      --> 같은 HttpSecurity 로 체인 두 개를 만들려 할 때 나온다
      --> @Bean 메서드에서 http 를 재사용하면 이 예외를 본다
      --> HttpSecurity 빈이 prototype 인 이유이기도 하다

 담아 둔 결과
      --> getObject() 로 다시 꺼낼 수 있다
      --> main 안의 실사용처는 AuthenticationConfiguration 정도다

 compareAndSet
      --> 동시에 두 스레드가 build() 를 불러도 하나만 통과한다
```

## 하위 메서드

- [01 AbstractConfiguredSecurityBuilder.doBuild](01_AbstractConfiguredSecurityBuilder.doBuild/README.md)

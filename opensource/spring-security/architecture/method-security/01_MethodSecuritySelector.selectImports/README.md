# MethodSecuritySelector.selectImports

상위: [메서드 보안](../README.md)

`@EnableMethodSecurity` 의 속성을 보고 어떤 설정 클래스를 들일지 고른다. 기동 시점에 한 번 도는 코드다.

## 위치

`config` / `org.springframework.security.config.annotation.method.configuration` / `MethodSecuritySelector.java` L53-L81 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/config/src/main/java/org/springframework/security/config/annotation/method/configuration/MethodSecuritySelector.java#L53-L81))

## 실제 코드

```java
// MethodSecuritySelector.java L53-L81
@Override
public String[] selectImports(@NonNull AnnotationMetadata importMetadata) {
    if (!importMetadata.hasAnnotation(EnableMethodSecurity.class.getName())
            && !importMetadata.hasMetaAnnotation(EnableMethodSecurity.class.getName())) {
        return new String[0];
    }
    EnableMethodSecurity annotation = importMetadata.getAnnotations().get(EnableMethodSecurity.class).synthesize();
    List<String> imports = new ArrayList<>(Arrays.asList(this.autoProxy.selectImports(importMetadata)));
    if (annotation.prePostEnabled()) {
        imports.add(PrePostMethodSecurityConfiguration.class.getName());
    }
    if (annotation.securedEnabled()) {
        imports.add(SecuredMethodSecurityConfiguration.class.getName());
    }
    if (annotation.jsr250Enabled()) {
        imports.add(Jsr250MethodSecurityConfiguration.class.getName());
    }
    imports.add(AuthorizationProxyConfiguration.class.getName());
    if (isDataPresent) {
        imports.add(AuthorizationProxyDataConfiguration.class.getName());
    }
    if (isWebPresent) {
        imports.add(AuthorizationProxyWebConfiguration.class.getName());
    }
    if (isObservabilityPresent) {
        imports.add(MethodObservationConfiguration.class.getName());
    }
    return imports.toArray(new String[0]);
}
```

애노테이션의 기본값은 이렇다.

`config` / `org.springframework.security.config.annotation.method.configuration` / `EnableMethodSecurity.java` L43-L65 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/config/src/main/java/org/springframework/security/config/annotation/method/configuration/EnableMethodSecurity.java#L43-L65))

```java
// EnableMethodSecurity.java L43-L65 (javadoc 생략)
@Import(MethodSecuritySelector.class)
public @interface EnableMethodSecurity {

    boolean prePostEnabled() default true;

    boolean securedEnabled() default false;

    boolean jsr250Enabled() default false;
```

## 동작 흐름

```text
 selectImports(importMetadata)
 |
 +-- L55 @EnableMethodSecurity 가 (메타 애노테이션으로도) 없으면
 |        L57 빈 배열 -- 아무것도 들이지 않는다
 |
 | L59 애노테이션을 읽어
 | L60 자동 프록시 설정을 먼저 담는다
 |
 +-- L61 prePostEnabled 이면 (기본 true)
 |        L62 PrePostMethodSecurityConfiguration
 +-- L64 securedEnabled 이면 (기본 false)
 |        L65 SecuredMethodSecurityConfiguration
 +-- L67 jsr250Enabled 이면 (기본 false)
 |        L68 Jsr250MethodSecurityConfiguration
 |
 | L70 AuthorizationProxyConfiguration 은 조건 없이
 |
 +-- L71 클래스패스에 있으면 조건부로 더 담는다
        L72 AuthorizationProxyDataConfiguration   (스프링 데이터)
        L75 AuthorizationProxyWebConfiguration    (웹)
        L78 MethodObservationConfiguration        (관측)
```

```text
 기본값이 하나만 켜져 있다

 prePostEnabled  true    @PreAuthorize, @PostAuthorize, @PreFilter, @PostFilter
 securedEnabled  false   @Secured
 jsr250Enabled   false   @RolesAllowed, @PermitAll, @DenyAll

 즉 @EnableMethodSecurity 만 붙이면 @Secured 는 동작하지 않는다
 필요하면 속성으로 켜야 한다
```

```text
 ImportSelector 라는 점

 이것은 빈이 아니라 "어떤 설정 클래스를 들일지 정하는 선택기"다
 @Configuration 파싱 단계에서 불리고,
 돌려준 클래스 이름들이 설정 클래스로 등록된다

 Spring Framework 의 컨테이너 기동 흐름에서
 ConfigurationClassPostProcessor 가 이것을 처리한다
```

## 결과가 쓰이는 곳

```text
 PrePostMethodSecurityConfiguration
      --> 네 종류의 인터셉터를 @Bean 으로 등록한다
      --> preFilter, preAuthorize, postAuthorize, postFilter

 등록된 인터셉터
      --> AuthorizationAdvisor 라 PointcutAdvisor 이기도 하다
      --> 빈 생성 때 자동 프록시 생성기가 이것을 찾아 프록시를 씌운다

 조건부 임포트
      --> 클래스패스에 무엇이 있느냐로 갈린다
      --> 같은 애노테이션이라도 의존성에 따라 등록되는 빈이 달라진다
```

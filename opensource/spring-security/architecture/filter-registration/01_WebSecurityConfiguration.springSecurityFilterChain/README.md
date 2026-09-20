# WebSecurityConfiguration.springSecurityFilterChain

상위: [필터 등록](../README.md)

이름이 고정된 `@Bean` 이다. 서블릿 쪽의 `DelegatingFilterProxy` 가 이 이름으로 빈을 찾는다.

## 위치

`config` / `org.springframework.security.config.annotation.web.configuration` / `WebSecurityConfiguration.java` L113-L132 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/config/src/main/java/org/springframework/security/config/annotation/web/configuration/WebSecurityConfiguration.java#L113-L132))

## 실제 코드

```java
// WebSecurityConfiguration.java L113-L132
@Bean(name = AbstractSecurityWebApplicationInitializer.DEFAULT_FILTER_NAME)
public Filter springSecurityFilterChain(ObjectProvider<HttpSecurity> provider) throws Exception {
    boolean hasFilterChain = !this.securityFilterChains.isEmpty();
    if (!hasFilterChain) {
        this.webSecurity.addSecurityFilterChainBuilder(() -> {
            HttpSecurity httpSecurity = provider.getObject();
            httpSecurity.authorizeHttpRequests((authorize) -> authorize.anyRequest().authenticated());
            httpSecurity.formLogin(Customizer.withDefaults());
            httpSecurity.httpBasic(Customizer.withDefaults());
            return httpSecurity.build();
        });
    }
    for (SecurityFilterChain securityFilterChain : this.securityFilterChains) {
        this.webSecurity.addSecurityFilterChainBuilder(() -> securityFilterChain);
    }
    for (WebSecurityCustomizer customizer : this.webSecurityCustomizers) {
        customizer.customize(this.webSecurity);
    }
    return this.webSecurity.build();
}
```

빈 이름은 상수로 고정되어 있다.

`web` / `org.springframework.security.web.context` / `AbstractSecurityWebApplicationInitializer.java` L79-L79 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/context/AbstractSecurityWebApplicationInitializer.java#L79-L79))

```java
// AbstractSecurityWebApplicationInitializer.java L79-L79
public static final String DEFAULT_FILTER_NAME = "springSecurityFilterChain";
```

## 동작 흐름

```text
 springSecurityFilterChain(provider)
 |
 +-- L115 securityFilterChains 가 비었는가
 |      |
 |      +-- L116 비었으면
 |             L117 기본 체인 빌더를 하나 넣는다
 |             L118 HttpSecurity 를 새로 받아
 |             L119 anyRequest().authenticated()
 |             L120 formLogin(withDefaults())
 |             L121 httpBasic(withDefaults())
 |             L122 build()
 |
 +-- L125 그 다음 각 체인을 빌더로 감싸 넣는다 (분기 밖이라 항상 실행된다)
 |      L126 addSecurityFilterChainBuilder(() -> securityFilterChain)
 |             이미 만들어진 것이라 그냥 돌려주는 람다다
 |
 | L128 커스터마이저마다
 |      L129 customize(webSecurity)
 |
 +-- L131 webSecurity.build()
```

```text
 두 경로의 빌더가 다르다

 기본 체인    람다가 실제로 HttpSecurity.build() 를 부른다
              즉 빌드 시점에 체인이 만들어진다

 사용자 체인  이미 빈으로 만들어진 것을 그냥 돌려준다
              @Bean 메서드가 먼저 돌아 체인을 완성해 두었다

 둘 다 SecurityBuilder 로 감싸 같은 목록에 들어간다
```

```text
 체인 순서는 주입 순서다

 securityFilterChains 는 @Autowired 로 주입받은 List 다
 이 메서드는 받은 순서대로 넣기만 하고 정렬하지 않는다

 그래서 @Order 가 있으면 그것이, 없으면 빈 등록 순서가 남는다
 필터 체인 흐름에서 "첫 매칭이 이긴다"고 한 그 순서가 여기서 정해진다
```

## 결과가 쓰이는 곳

```text
 반환한 Filter
      --> 보통 FilterChainProxy 다 (debug 를 켜면 DebugFilter 로 감싼다)
      --> 빈 이름이 springSecurityFilterChain 으로 고정된다
      --> 다만 빈 정의 후처리가 이 이름 자리를 CompositeFilterChainProxy 로
          바꿔 끼운다 (WebSecurityConfiguration L218-250)
          FilterChainProxy 를 상속한 타입이라 동작은 이어진다

 기본 체인
      --> 아무 설정도 없을 때 모든 경로를 막고 로그인 폼을 띄운다
      --> @Bean SecurityFilterChain 을 하나라도 만들면 사라진다

 WebSecurityCustomizer
      --> build() 직전에 WebSecurity 를 직접 만질 기회다
      --> ignoring() 을 거는 자리로 흔히 쓰인다

 provider (ObjectProvider<HttpSecurity>)
      --> prototype 빈이라 부를 때마다 새 인스턴스가 온다
      --> 기본 체인 람다가 실행될 때 비로소 하나를 받아 간다
```

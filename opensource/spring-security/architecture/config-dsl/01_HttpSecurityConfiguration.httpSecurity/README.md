# HttpSecurityConfiguration.httpSecurity

상위: [설정 DSL](../README.md)

`@Bean SecurityFilterChain chain(HttpSecurity http)` 의 그 `http` 가 만들어지는 곳이다. 아무것도 설정하지 않아도 이미 열 가지가 켜져 있다.

## 위치

`config` / `org.springframework.security.config.annotation.web.configuration` / `HttpSecurityConfiguration.java` L114-L144 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/config/src/main/java/org/springframework/security/config/annotation/web/configuration/HttpSecurityConfiguration.java#L114-L144))

## 실제 코드

```java
// HttpSecurityConfiguration.java L114-L144
@Bean(HTTPSECURITY_BEAN_NAME)
@Scope("prototype")
HttpSecurity httpSecurity() {
    LazyPasswordEncoder passwordEncoder = new LazyPasswordEncoder(this.context);
    AuthenticationManagerBuilder authenticationBuilder = new DefaultPasswordEncoderAuthenticationManagerBuilder(
            this.objectPostProcessor, passwordEncoder);
    authenticationBuilder.parentAuthenticationManager(authenticationManager());
    authenticationBuilder.authenticationEventPublisher(getAuthenticationEventPublisher());
    HttpSecurity http = new HttpSecurity(this.objectPostProcessor, authenticationBuilder, createSharedObjects());
    WebAsyncManagerIntegrationFilter webAsyncManagerIntegrationFilter = new WebAsyncManagerIntegrationFilter();
    webAsyncManagerIntegrationFilter.setSecurityContextHolderStrategy(this.securityContextHolderStrategy);
    // @formatter:off
    http
        .csrf(withDefaults())
        .addFilter(webAsyncManagerIntegrationFilter)
        .exceptionHandling(withDefaults())
        .headers(withDefaults())
        .sessionManagement(withDefaults())
        .securityContext(withDefaults())
        .requestCache(withDefaults())
        .anonymous(withDefaults())
        .servletApi(withDefaults())
        .with(new DefaultLoginPageConfigurer<>());
    http.logout(withDefaults());
    // @formatter:on
    applyCorsIfAvailable(http);
    applyDefaultConfigurers(http);
    applyHttpSecurityCustomizers(this.context, http);
    applyTopLevelCustomizers(this.context, http);
    return http;
}
```

## 동작 흐름

```text
 httpSecurity()
 |
 | L117 LazyPasswordEncoder
 | L118 DefaultPasswordEncoderAuthenticationManagerBuilder
 | L120 부모 AuthenticationManager 를 연결한다
 | L121 인증 이벤트 발행기를 연결한다
 |
 | L122 new HttpSecurity(objectPostProcessor, authenticationBuilder, 공유객체)
 |
 +-- L126-136 기본 설정자들을 켠다
 |      csrf, addFilter(WebAsyncManagerIntegrationFilter),
 |      exceptionHandling, headers, sessionManagement,
 |      securityContext, requestCache, anonymous, servletApi,
 |      with(DefaultLoginPageConfigurer)
 |
 | L137 logout(withDefaults())   따로 한 줄로 부른다
 |
 | L139 applyCorsIfAvailable(http)      CORS 클래스가 있으면
 | L140 applyDefaultConfigurers(http)   등록 파일에서 찾아 적용
 | L141 applyHttpSecurityCustomizers    빈으로 등록된 커스터마이저
 | L142 applyTopLevelCustomizers
 |
 +-- L143 반환
```

```text
 prototype 스코프다

 L114-115 @Bean(HTTPSECURITY_BEAN_NAME) @Scope("prototype")

 주입받을 때마다 새 인스턴스가 만들어진다

 build() 는 한 번만 부를 수 있으므로
 SecurityFilterChain 빈을 여러 개 만들려면 각자 새 HttpSecurity 가 필요하다
 prototype 이 그 제약과 맞아떨어진다
 (소스와 레퍼런스에 그 이유가 적혀 있지는 않다)
```

```text
 기본으로 켜지는 것들의 의미

 사용자가 @Bean SecurityFilterChain 을 하나만 써도
 CSRF 방어, 세션 관리, 예외 처리, 익명 인증이 이미 들어 있다

 앞의 흐름들에서 본 필터 대부분이 여기서 등록된다
   CsrfFilter               csrf(withDefaults())
   ExceptionTranslationFilter  exceptionHandling(withDefaults())
   SecurityContextHolderFilter securityContext(withDefaults())
   AnonymousAuthenticationFilter anonymous(withDefaults())
   LogoutFilter             logout(withDefaults())

 끄려면 명시적으로 disable() 을 불러야 한다
```

```text
 등록 파일로 확장할 수 있다

 L140 applyDefaultConfigurers 가 등록된 AbstractHttpConfigurer 구현을
 찾아 적용한다

 라이브러리가 자기 보안 설정을 자동으로 끼워 넣는 통로다
```

## 결과가 쓰이는 곳

```text
 돌려준 HttpSecurity
      --> 사용자의 @Bean 메서드가 인자로 받는다
      --> DSL 을 부르면 설정자가 이 인스턴스에 쌓인다

 미리 켜진 설정자들
      --> 사용자가 같은 DSL 을 또 부르면 기존 설정자를 다시 쓴다
      --> 그래서 http.csrf(c -> c.disable()) 이 이미 등록된 것을 끈다

 공유 객체 맵
      --> L122 에서 createSharedObjects() 로 초기값을 넣는다
      --> ApplicationContext 등이 여기 담겨 설정자들이 꺼내 쓴다

 AuthenticationManagerBuilder
      --> 빌드 때 beforeConfigure 가 이것으로 AuthenticationManager 를 만든다
      --> 인증 흐름의 매니저가 여기서 나온다
```

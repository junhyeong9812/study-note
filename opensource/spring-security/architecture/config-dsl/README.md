# 설정 DSL

**이 흐름만 요청 처리 경로가 아니다.** 앞의 일곱 흐름이 "요청이 들어오면 무슨 일이 일어나는가"를 따라간다면, 여기서는 기동 시점에 `HttpSecurity` 설정이 `SecurityFilterChain` 하나로 조립되는 과정을 따라간다. 앞에서 본 필터들이 어디서 어떤 순서로 목록에 들어갔는지가 여기서 드러난다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 빌더와 설정자 계약 모음이다.

기준 커밋: spring-security `main` [`26b6b2a84f`](https://github.com/spring-projects/spring-security/tree/26b6b2a84fa8fa26991ca0f57282720b48db9f91) (2026-09-18). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 @Bean SecurityFilterChain chain(HttpSecurity http) {
     http.authorizeHttpRequests(...).formLogin(...);
     return http.build();
 }
 |
 +-- [01] HttpSecurityConfiguration.httpSecurity
 |        주입받는 HttpSecurity 를 만드는 @Bean 메서드다
 |        prototype 스코프라 체인마다 새 인스턴스를 받는다
 |        csrf, exceptionHandling, headers, sessionManagement,
 |        securityContext, requestCache, anonymous, servletApi,
 |        DefaultLoginPageConfigurer, logout 열 가지를 미리 켠다
 |        CORS 는 관련 빈이 있을 때만 켜진다
 |
 +-- [02] AbstractSecurityBuilder.build
 |        CAS 로 한 번만 허용한다. 두 번 부르면 AlreadyBuiltException
 |
 +-- [02-01] AbstractConfiguredSecurityBuilder.doBuild
 |        init -> configure -> performBuild 세 단계를 돌린다
 |        각 단계 사이에 빌드 상태를 바꾼다
 |
 +-- [03] HttpSecurity.performBuild
          모인 필터를 정렬해 DefaultSecurityFilterChain 을 만든다
```

```text
 DSL 한 줄이 설정자 하나다

 http.formLogin(withDefaults())
   --> FormLoginConfigurer 를 등록한다

 그 설정자가 나중에 두 번 불린다
   init(builder)       공유 객체를 심고 다른 설정자와 조율한다
   configure(builder)  필터를 addFilter 로 목록에 넣는다

 필터 객체 자체는 설정자 생성자에서 먼저 만들어지기도 한다
 (FormLoginConfigurer 생성자가 UsernamePasswordAuthenticationFilter 를 만든다)
 목록에 들어가는 일이 build() 안에서 일어난다
```

```text
 왜 init 과 configure 가 나뉘어 있는가

 설정자끼리 서로를 봐야 하는 경우가 있다

 SecurityConfigurer 의 javadoc 이 역할을 나눈다
   init      공유 상태만 만들고 고친다. 설정자 추가도 여기서 한다
   configure 그 공유 객체를 써서 실제로 만든다

 예) DefaultLoginPageConfigurer.init 이 로그인 페이지 생성 필터를
     공유 객체에 심고, LogoutConfigurer.init 이 그것을 꺼내
     로그아웃 성공 URL 을 건다

 한 단계뿐이라면 나중에 등록된 설정자만 앞의 결과를 볼 수 있다
 두 단계로 나눠 두면 등록 순서와 무관해진다
```

```text
 필터 순서는 DSL 호출 순서가 아니다

 addFilter 가 FilterOrderRegistration 에서 그 필터 클래스의 순번을 찾는다
 못 찾으면 예외를 던진다

 performBuild 가 OrderComparator 로 정렬한다

 그래서 DSL 을 어떤 순서로 쓰든 필터 체인의 순서는 같다
 순서를 바꾸려면 addFilterBefore / addFilterAfter 를 쓴다
```

## 어디에서 쓰이는가

```text
 [필터 등록] 여기서 만든 SecurityFilterChain 들이 FilterChainProxy 에 모인다
 [필터 체인] 이 흐름의 산출물이 곧 그 흐름의 입력이다
 [빈 생성] HttpSecurity 는 prototype 스코프 빈이다
 [모든 런타임 흐름] 앞의 흐름에 나온 필터 대부분이 여기서 목록에 들어간다
```

만들어진 체인이 `FilterChainProxy` 에 모이는 과정은 [필터 등록](../filter-registration/README.md), 그 체인이 요청을 처리하는 과정은 [필터 체인](../filter-chain/README.md)에 있다.

## 단계

1. [HttpSecurityConfiguration.httpSecurity](01_HttpSecurityConfiguration.httpSecurity/README.md)가 기본값을 켠 빌더를 만든다.
2. [AbstractSecurityBuilder.build](02_AbstractSecurityBuilder.build/README.md)가 한 번만 빌드를 허용한다.
3. [AbstractConfiguredSecurityBuilder.doBuild](02_AbstractSecurityBuilder.build/01_AbstractConfiguredSecurityBuilder.doBuild/README.md)가 세 단계를 돌린다.
4. [HttpSecurity.performBuild](03_HttpSecurity.performBuild/README.md)가 필터를 정렬해 체인을 만든다.

## 결과가 쓰이는 곳

```text
 DefaultSecurityFilterChain
      --> 매처 하나와 정렬된 필터 목록을 들고 있다
      --> FilterChainProxy 가 이것들을 모아 요청마다 하나를 고른다

 공유 객체 (shared object)
      --> 설정자끼리 값을 주고받는 통로다
      --> AuthenticationManager, SecurityContextRepository,
          AuthenticationEntryPoint 등이 여기 담긴다

 한 번만 빌드된다는 점
      --> HttpSecurity 인스턴스를 재사용할 수 없다
      --> 체인마다 새 인스턴스가 필요하고, @Bean 이 prototype 인 것이
          그것과 맞아떨어진다

 기본으로 켜지는 설정자들
      --> 아무것도 안 써도 CSRF, 세션 관리, 예외 처리가 들어 있다
      --> 끄려면 명시적으로 disable() 을 불러야 한다
```

## 다루지 않는 것

개별 `SecurityConfigurer` 구현의 세부(`FormLoginConfigurer`, `AuthorizeHttpRequestsConfigurer` 등이 무엇을 심는지), `ObjectPostProcessor` 와 `AuthenticationManagerBuilder` 의 동작, `FilterOrderRegistration` 의 전체 순번표, XML 네임스페이스 설정 경로, `@EnableWebSecurity` 가 임포트하는 나머지 설정 클래스(`SpringWebMvcImportSelector`, `OAuth2ImportSelector`, `ObservationImportSelector`)는 같은 뼈대의 곁가지라 요약만 했다.

## 하위 메서드

- [01 HttpSecurityConfiguration.httpSecurity](01_HttpSecurityConfiguration.httpSecurity/README.md)
- [02 AbstractSecurityBuilder.build](02_AbstractSecurityBuilder.build/README.md)
- [03 HttpSecurity.performBuild](03_HttpSecurity.performBuild/README.md)
- [spi](spi/README.md) — 보안 빌더, 설정자

# 필터 등록

[설정 DSL](../config-dsl/README.md)이 만든 `SecurityFilterChain` 들이 `FilterChainProxy` 하나로 묶여 서블릿 컨테이너에 등록되기까지다. 이것도 요청 처리 경로가 아니라 기동 시점의 조립 과정이다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 등록 계약 모음이다.

기준 커밋: spring-security `main` [`26b6b2a84f`](https://github.com/spring-projects/spring-security/tree/26b6b2a84fa8fa26991ca0f57282720b48db9f91) (2026-09-18). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 @Bean SecurityFilterChain 들이 컨텍스트에 있다
 |
 +-- [01] WebSecurityConfiguration.springSecurityFilterChain
 |        @Bean 이름이 "springSecurityFilterChain" 이다
 |        체인 빈이 하나도 없으면 기본 체인을 하나 만든다
 |        있으면 그것들을 WebSecurity 에 넣는다
 |        WebSecurityCustomizer 를 적용하고 build()
 |
 +-- [02] WebSecurity.performBuild
 |        ignoring() 경로마다 필터 0개짜리 체인을 만든다
 |        각 빌더를 build() 해 체인 목록을 완성한다
 |        FilterChainProxy 를 만들어 방화벽과 검증기를 붙인다
 |
 +-- [03] AbstractSecurityWebApplicationInitializer.onStartup
          서블릿 컨테이너에 DelegatingFilterProxy 를 등록한다
          그 프록시가 같은 이름의 빈을 찾아 위임한다
```

```text
 빈 이름 하나가 두 세계를 잇는다

 "springSecurityFilterChain"

 스프링 쪽   WebSecurityConfiguration 이 이 이름으로 @Bean 을 만든다
 서블릿 쪽   DelegatingFilterProxy 가 이 이름으로 빈을 찾는다

 DelegatingFilterProxy 는 서블릿 필터지만 스스로 일하지 않는다
 컨텍스트에서 그 이름의 빈을 찾아 넘길 뿐이다
 컨테이너는 기동 전에 필터를 등록해야 하는데 스프링 컨텍스트는
 그보다 늦게 뜨기 때문에 이 간접층이 필요하다고 레퍼런스가 밝힌다

 스프링 부트를 쓰면 이 등록을 부트가 대신 해 준다
```

```text
 체인이 하나도 없으면 기본 체인이 생긴다

 L116 hasFilterChain 이 false 면
   anyRequest().authenticated() + formLogin + httpBasic

 그래서 스프링 시큐리티를 의존성에만 추가해도
 모든 경로가 막히고 로그인 폼이 뜬다

 @Bean SecurityFilterChain 을 하나라도 만들면 이 기본값은 사라진다
```

```text
 WebSecurity 와 HttpSecurity 는 같은 뼈대다

 둘 다 AbstractConfiguredSecurityBuilder 를 상속한다
 init -> configure -> performBuild 로 도는 것도 같다

 다른 것은 만드는 물건이다
   HttpSecurity  -> DefaultSecurityFilterChain  (체인 하나)
   WebSecurity   -> Filter (FilterChainProxy)   (체인들을 묶은 필터)

 그래서 WebSecurity.performBuild 안에서
 각 HttpSecurity 의 build() 가 불린다. 빌더가 빌더를 부른다
```

## 어디에서 쓰이는가

```text
 [설정 DSL] 그 흐름의 산출물인 SecurityFilterChain 들이 여기 모인다
 [필터 체인] 여기서 만든 FilterChainProxy 가 그 흐름의 주인공이다
 [인가] ignoring() 경로가 여기서 필터 0개 체인이 된다
 [빈 생성] springSecurityFilterChain 은 이름이 고정된 빈이다
```

체인 하나가 만들어지는 과정은 [설정 DSL](../config-dsl/README.md), 만들어진 프록시가 요청을 처리하는 과정은 [필터 체인](../filter-chain/README.md)에 있다.

## 단계

1. [WebSecurityConfiguration.springSecurityFilterChain](01_WebSecurityConfiguration.springSecurityFilterChain/README.md)이 체인들을 모은다.
2. [WebSecurity.performBuild](02_WebSecurity.performBuild/README.md)가 FilterChainProxy 를 만든다.
3. [AbstractSecurityWebApplicationInitializer.onStartup](03_AbstractSecurityWebApplicationInitializer.onStartup/README.md)이 컨테이너에 등록한다.

## 결과가 쓰이는 곳

```text
 FilterChainProxy
      --> 서블릿 필터 하나로 보이지만 안에 체인 목록을 들고 있다
      --> 요청마다 매칭되는 체인 하나를 골라 그 필터들을 태운다

 WebSecurityFilterChainValidator
      --> 빌드 도중에 체인 목록을 검사한다
      --> 매처 없는 체인 뒤에 다른 체인이 오면 예외를 던진다
      --> XML 네임스페이스 경로는 DefaultFilterChainValidator 를 쓴다

 ignoring() 으로 만든 체인
      --> 필터 0개짜리 DefaultSecurityFilterChain 이다
      --> 매칭은 되지만 보안 필터가 하나도 돌지 않는다
      --> 다만 HttpFirewall 은 체인 선택 전에 적용되므로 여전히 돈다
      --> 코드가 경고 로그를 남기며 permitAll 을 권한다

 등록된 DelegatingFilterProxy
      --> 컨테이너가 아는 Spring Security 필터는 보통 이것 하나다
      --> 다른 필터보다 앞에 매핑되고, 디스패처 타입도 여기서 정해진다
```

## 다루지 않는 것

`WebInvocationPrivilegeEvaluator` 구성(타임리프 등에서 "이 링크를 보여줄까"를 묻는 경로), `DebugFilter` 와 관측 연동, `CompositeFilterChainProxy` 로 교체하는 빈 정의 후처리, `ServletRequestPathFilter`, 스프링 부트의 자동 필터 등록, XML 네임스페이스 경로는 같은 뼈대의 곁가지라 요약만 했다. `DelegatingFilterProxy` 자체의 구현도 Spring Framework 소속이라 범위 밖이다.

## 하위 메서드

- [01 WebSecurityConfiguration.springSecurityFilterChain](01_WebSecurityConfiguration.springSecurityFilterChain/README.md)
- [02 WebSecurity.performBuild](02_WebSecurity.performBuild/README.md)
- [03 AbstractSecurityWebApplicationInitializer.onStartup](03_AbstractSecurityWebApplicationInitializer.onStartup/README.md)
- [spi](spi/README.md) — 웹 보안 커스터마이저, 체인 검증기

# 필터 체인

Spring Security 의 모든 것이 여기서 시작한다. 서블릿 컨테이너가 보기에 Spring Security 는 **필터 하나**다. 그 필터 하나가 요청마다 체인을 골라, 그 안의 필터들을 차례로 태운다. 인증도 인가도 CSRF 도 전부 이 체인 위의 한 칸이다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 체인과 방화벽 계약 모음이다.

기준 커밋: spring-security `main` [`26b6b2a84f`](https://github.com/spring-projects/spring-security/tree/26b6b2a84fa8fa26991ca0f57282720b48db9f91) (2026-09-18). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 서블릿 컨테이너
 |
 +-- DelegatingFilterProxy ("springSecurityFilterChain")
 |        스프링 컨텍스트에서 같은 이름의 빈을 찾아 위임한다
 |        컨테이너의 필터 생명주기와 스프링의 빈 생명주기를 잇는 어댑터다
 |
 +-- [01] FilterChainProxy.doFilter
 |        FILTER_APPLIED 속성으로 중첩 호출을 가려낸다
 |        바깥 호출에서만 finally 로 SecurityContext 를 비운다
 |        RequestRejectedException 을 잡아 핸들러로 넘긴다
 |
 +-- [01-01] FilterChainProxy.doFilterInternal
 |        HttpFirewall 로 요청과 응답을 감싼다
 |        체인을 고르고, 없으면 보안 없이 통과시킨다
 |
 +-- [01-01-01] FilterChainProxy.getFilters
 |        등록된 SecurityFilterChain 을 순서대로 훑어
 |        matches(request) 가 true 인 첫 체인의 필터 목록을 돌려준다
 |        하나도 안 맞으면 null
 |
 +-- [02] VirtualFilterChain.doFilter
          필터 목록을 인덱스로 하나씩 꺼내 자기 자신을 넘기며 호출한다
          끝에 다다르면 원래 컨테이너 체인으로 빠져나간다
```

```text
 체인 선택은 "첫 매칭"이다

 filterChains = [ /api/** 체인, /admin/** 체인, /** 체인 ]

 GET /admin/users  --> /api/** 안 맞음
                   --> /admin/** 맞음  --> 이 체인의 필터 목록 반환, 끝
                   --> /** 는 보지도 않는다

 앞 체인이 넓으면 뒤 체인이 죽는데, 두 경우가 갈린다
   매처를 아예 안 준 체인(AnyRequestMatcher)을 앞에 두면
     WebSecurityFilterChainValidator 가 기동 때 막는다
     UnreachableFilterChainException
   securityMatcher("/**") 처럼 넓지만 AnyRequestMatcher 가 아니면
     기동은 되고, 요청이 와야 가려진 것이 드러난다

 반대로 어느 체인도 안 맞으면 보안 검사 없이 통과한다
```

```text
 요청을 감싸는 이유

 요청 --> FirewalledRequest 로 감싼다
      --> 체인의 필터들이 이 감싼 요청을 본다
      --> 체인을 빠져나갈 때 firewallRequest.reset() 을 부른다

 기본 StrictHttpFirewall 은 "고치지 않고 거부한다"
   비정규화 경로, 금지된 메서드, 이상 문자를 보면 예외를 던진다
   감싼 요청은 헤더와 파라미터 접근 시점에도 같은 검사를 건다
   reset() 은 빈 메서드다. 되돌릴 가공을 하지 않았기 때문이다

 경로를 잘라 정규화하는 쪽은 DefaultHttpFirewall 이다
   그쪽의 래퍼만 reset() 에서 실제로 가공을 되돌린다
```

## 어디에서 쓰이는가

```text
 [설정 DSL] HttpSecurity 가 만든 DefaultSecurityFilterChain 들이 이 목록에 들어온다
 [MVC 요청 처리] 이 체인을 다 통과해야 DispatcherServlet 에 닿는다
   즉 컨트롤러가 호출되기 전에 인증과 인가가 이미 끝나 있다
 [빈 생성] FilterChainProxy 는 springSecurityFilterChain 이라는 이름의 빈이다
```

체인 목록이 어떻게 만들어지는지는 [설정 DSL](../config-dsl/README.md)과 [필터 등록](../filter-registration/README.md)에 있다. 이 체인을 통과한 뒤의 경로는 Spring Framework 쪽 [MVC 요청 처리](../../../spring-framework/architecture/webmvc-request-processing/README.md) 흐름으로 이어진다.

## 단계

1. [FilterChainProxy.doFilter](01_FilterChainProxy.doFilter/README.md)가 요청을 받는다.
2. [FilterChainProxy.doFilterInternal](01_FilterChainProxy.doFilter/01_FilterChainProxy.doFilterInternal/README.md)이 방화벽을 씌우고 체인을 고른다.
3. [FilterChainProxy.getFilters](01_FilterChainProxy.doFilter/01_FilterChainProxy.doFilterInternal/01_FilterChainProxy.getFilters/README.md)가 첫 매칭 체인을 찾는다.
4. [VirtualFilterChain.doFilter](02_VirtualFilterChain.doFilter/README.md)가 필터를 하나씩 태운다.

## 결과가 쓰이는 곳

```text
 고른 필터 목록
      --> 이 요청에 적용될 보안 규칙 전체다
      --> 체인이 다르면 인증 방식도 인가 규칙도 다르다

 VirtualFilterChain 의 커서
      --> 필터가 chain.doFilter 를 부르지 않으면 거기서 요청이 끝난다
      --> 로그인 리다이렉트나 403 응답이 이렇게 만들어진다

 FILTER_APPLIED 속성
      --> 같은 요청에 FilterChainProxy 가 두 번 걸려도
          SecurityContext 를 비우는 일은 가장 바깥에서 한 번만 한다

 finally 의 clearContext
      --> ThreadLocal 에 남은 인증 정보를 지운다
      --> 스레드 풀이 재사용되는 서블릿 환경에서 이것이 없으면
          다음 요청이 앞 사용자의 인증을 물려받는다
```

## 다루지 않는 것

`StrictHttpFirewall`의 차단 규칙 세부, `FilterChainValidator`의 검증 내용, `DebugFilter`와 관측(Observation) 래핑, `DelegatingFilterProxy` 자체의 구현(Spring Framework 소속)은 같은 뼈대의 곁가지라 요약만 했다. 서블릿 필터 명세 자체도 범위 밖이다.

## 하위 메서드

- [01 FilterChainProxy.doFilter](01_FilterChainProxy.doFilter/README.md)
- [02 VirtualFilterChain.doFilter](02_VirtualFilterChain.doFilter/README.md)
- [spi](spi/README.md) — 체인 계약, 체인 데코레이터, 방화벽, 거부 핸들러

# 인가

인증이 "누구인가"라면 인가는 "이 요청을 해도 되는가"다. 필터 체인의 거의 끝에 있고, 여기를 통과해야 `DispatcherServlet` 에 닿는다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 인가 계약 모음이다.

기준 커밋: spring-security `main` [`26b6b2a84f`](https://github.com/spring-projects/spring-security/tree/26b6b2a84fa8fa26991ca0f57282720b48db9f91) (2026-09-18). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 필터 체인의 뒤쪽 (인증 필터들을 지난 뒤)
 |
 +-- [01] AuthorizationFilter.doFilter
 |        인가 매니저에게 물어보고, 거부면 예외를 던진다
 |        허용이면 체인을 계속 태운다
 |
 +-- [01-01] AuthorizationFilter.getAuthentication
 |        SecurityContext 에서 Authentication 을 꺼낸다
 |        null 이면 AuthenticationCredentialsNotFoundException
 |        Supplier 로 넘겨서, 필요 없으면 꺼내지도 않는다
 |
 +-- [02] RequestMatcherDelegatingAuthorizationManager.authorize
 |        등록된 (매처, 매니저) 쌍을 순서대로 본다
 |        처음 매칭되는 쌍의 매니저에게 넘긴다
 |        하나도 안 맞으면 DENY
 |
 +-- [03] AuthoritiesAuthorizationManager.authorize
          권한 목록을 대조해 granted 를 정한다
          RoleHierarchy 를 거쳐 상위 역할을 펼친다
```

```text
 설정이 그대로 자료구조가 된다

 .authorizeHttpRequests(a -> a
     .requestMatchers("/admin/**").hasRole("ADMIN")
     .requestMatchers("/api/**").authenticated()
     .anyRequest().permitAll())

 mappings = [
   (/admin/** , AuthorityAuthorizationManager["ROLE_ADMIN"]),
   (/api/**   , AuthenticatedAuthorizationManager),
   (anyRequest, SingleResultAuthorizationManager.permitAll)
 ]

 위에서부터 훑어 처음 맞는 것 하나만 쓴다
 그래서 넓은 규칙을 위에 쓰면 아래가 죽는다
```

```text
 거부는 예외로 표현된다

 AuthorizationFilter 는 응답을 직접 쓰지 않는다
 AuthorizationDeniedException 을 던질 뿐이다

 그 예외를 앞쪽의 ExceptionTranslationFilter 가 잡아
   익명이거나 remember-me 면  설정된 AuthenticationEntryPoint 로
   그 밖의 인증된 사용자면    AccessDeniedHandler 로 (403)

 remember-me 는 "인증된 사용자"인데도 진입점으로 간다

 진입점이 무엇인지는 설정이 정한다
   formLogin 을 켜면 로그인 페이지로 리다이렉트
   인증 방식을 하나도 구성하지 않으면 기본값이
   Http403ForbiddenEntryPoint 라 그대로 403 이 나간다

 즉 "권한 없음"의 응답 모양은 이 흐름이 아니라 예외 변환이 정한다
```

## 어디에서 쓰이는가

```text
 [필터 체인] 체인의 뒤쪽 칸이다. 여기를 지나야 서블릿에 닿는다
 [보안 컨텍스트] 판정의 입력인 Authentication 을 여기서 꺼낸다
 [예외 변환] 거부 예외를 받아 실제 응답으로 바꾼다
 [메서드 보안] 같은 AuthorizationManager 계약을 메서드 호출에도 쓴다
```

판정의 입력이 어떻게 준비되는지는 [보안 컨텍스트](../security-context/README.md), 거부가 어떤 응답이 되는지는 [예외 변환](../exception-translation/README.md), 같은 계약을 메서드에 적용하는 쪽은 [메서드 보안](../method-security/README.md)에 있다.

## 단계

1. [AuthorizationFilter.doFilter](01_AuthorizationFilter.doFilter/README.md)가 판정을 요청한다.
2. [RequestMatcherDelegatingAuthorizationManager.authorize](02_RequestMatcherDelegatingAuthorizationManager.authorize/README.md)가 규칙을 고른다.
3. [AuthoritiesAuthorizationManager.authorize](03_AuthoritiesAuthorizationManager.authorize/README.md)가 권한을 대조한다.

## 결과가 쓰이는 곳

```text
 AuthorizationResult
      --> isGranted() 하나로 통과 여부가 갈린다
      --> 구현체가 거부 이유를 함께 담을 수 있다
          AuthorityAuthorizationDecision 은 요구한 권한 목록을 들고 있다

 발행되는 인가 이벤트
      --> 허용과 거부 모두 publishAuthorizationEvent 로 나간다
      --> 기본 발행기는 아무것도 하지 않는 NoopAuthorizationEventPublisher 다

 던진 AuthorizationDeniedException
      --> 체인이 거기서 끊긴다. 뒤의 필터도 서블릿도 실행되지 않는다
      --> 컨트롤러가 안 불렸는데 403 이 나가는 이유다

 Supplier 로 넘긴 Authentication
      --> permitAll 처럼 인증이 필요 없는 규칙은 꺼내지 않는다
      --> 그러면 SecurityContext 저장소를 읽지 않는다
          (체인의 다른 필터는 여전히 세션을 볼 수 있다)
```

## 다루지 않는 것

표현식 기반 인가(`WebExpressionAuthorizationManager`와 SpEL 평가), `RoleHierarchy`의 계층 정의 방법, `AuthorizationEventPublisher`의 구현과 관측 연동, `WebInvocationPrivilegeEvaluator`(타임리프 등에서 "이 링크를 보여줄까"를 묻는 경로), 그리고 deprecated 된 옛 `FilterSecurityInterceptor` 경로는 같은 뼈대의 곁가지라 요약만 했다.

## 하위 메서드

- [01 AuthorizationFilter.doFilter](01_AuthorizationFilter.doFilter/README.md)
- [02 RequestMatcherDelegatingAuthorizationManager.authorize](02_RequestMatcherDelegatingAuthorizationManager.authorize/README.md)
- [03 AuthoritiesAuthorizationManager.authorize](03_AuthoritiesAuthorizationManager.authorize/README.md)
- [spi](spi/README.md) — 인가 매니저, 판정 결과, 역할 계층

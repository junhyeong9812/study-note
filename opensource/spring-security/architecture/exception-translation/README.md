# 예외 변환

인가가 던진 예외를 실제 응답으로 바꾼다. 401 이냐 403 이냐, 로그인 페이지로 보낼 것이냐가 전부 여기서 갈린다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 진입점, 거부 핸들러, 신뢰 해석기 계약 모음이다.

기준 커밋: spring-security `main` [`26b6b2a84f`](https://github.com/spring-projects/spring-security/tree/26b6b2a84fa8fa26991ca0f57282720b48db9f91) (2026-09-18). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 이 필터는 자기 뒤의 체인을 try 로 감싸는 것이 전부다
 |
 +-- [01] ExceptionTranslationFilter.doFilter
 |        chain.doFilter 를 try 안에서 부른다
 |        예외가 올라오면 원인 사슬에서 보안 예외를 찾는다
 |        못 찾으면 그대로 다시 던진다
 |
 +-- [01-01] ExceptionTranslationFilter.handleAccessDeniedException
 |        여기가 401 과 403 을 가르는 자리다
 |        익명 토큰이거나 remember-me 토큰이면 --> 인증을 요구한다
 |        그 밖이면                            --> 거부 핸들러 (403)
 |
 +-- [01-02] ExceptionTranslationFilter.sendStartAuthentication
          컨텍스트를 비우고
          원래 가려던 요청을 저장한 뒤
          진입점을 부른다 (로그인 페이지 리다이렉트나 401)
```

```text
 같은 "접근 거부"가 두 응답으로 갈린다

 AccessDeniedException 이 올라왔을 때

 익명 토큰          --> 진입점
 remember-me 토큰   --> 진입점
 그 밖              --> 거부 핸들러 (403)

 앞의 둘은 더 인증하면 풀릴 수 있는 상황이고
 마지막은 더 인증해도 달라지지 않는 상황이다

 단 "그 밖" 에는 authentication 이 null 인 경우도 포함된다
 익명 필터를 빼면 자격 증명을 한 번도 내지 않은 요청이 403 을 받는다
```

```text
 위치가 동작을 정한다

 필터 체인   ... -> ExceptionTranslationFilter -> AuthorizationFilter -> 서블릿
                          |                              |
                          +--- try 로 감싼다 ------------+

 이 필터는 자기보다 뒤에서 난 예외만 잡는다
 앞쪽 필터에서 난 예외는 잡지 못한다

 그래서 인가 필터보다 앞에 있어야 인가 거부를 처리할 수 있다
```

## 어디에서 쓰이는가

```text
 [인가] AuthorizationFilter 가 던진 AuthorizationDeniedException 을 받는다
 [폼 로그인] 진입점이 보낸 로그인 페이지에서 인증이 시작된다
 [보안 컨텍스트] 인증을 요구하기 전에 컨텍스트를 비운다
 [필터 체인] 체인의 한 칸이지만, 뒤쪽 전체를 감싸는 역할이다
```

예외를 던지는 쪽은 [인가](../authorization/README.md), 진입점이 시작시키는 경로는 [폼 로그인](../form-login/README.md)에 있다.

## 단계

1. [ExceptionTranslationFilter.doFilter](01_ExceptionTranslationFilter.doFilter/README.md)가 예외를 가려낸다.
2. [ExceptionTranslationFilter.handleAccessDeniedException](01_ExceptionTranslationFilter.doFilter/01_ExceptionTranslationFilter.handleAccessDeniedException/README.md)이 401 과 403 을 가른다.
3. [ExceptionTranslationFilter.sendStartAuthentication](01_ExceptionTranslationFilter.doFilter/02_ExceptionTranslationFilter.sendStartAuthentication/README.md)이 인증을 요구한다.

## 결과가 쓰이는 곳

```text
 저장된 요청 (RequestCache)
      --> 로그인에 성공하면 원래 가려던 곳으로 되돌려 보낸다
      --> 필터의 기본값은 HttpSessionRequestCache 라 세션에 담는다
      --> 다만 설정 경로의 기본값은 매처가 붙은 것이다
          RequestCacheConfigurer 가 JSON, XMLHttpRequest, multipart,
          SSE, websocket 요청을 저장 대상에서 빼고
          CSRF 가 켜져 있으면 GET 만 저장한다
      --> 아예 끄려면 requestCache().disable() 로 NullRequestCache 를 꽂는다

 비워진 SecurityContext
      --> 인증을 다시 요구하기 전에 기존 인증을 버린다
      --> 코드 주석이 SEC-112 를 들며 "더 이상 유효하지 않다"고 밝힌다

 진입점이 쓴 응답
      --> 폼 로그인이면 로그인 페이지로 리다이렉트
      --> HTTP Basic 이면 401 과 WWW-Authenticate 헤더
      --> 인증 방식을 하나도 구성하지 않으면 기본값이
          Http403ForbiddenEntryPoint 라 진입점으로 가도 403 이 나간다
      --> 인증 방식이 응답 모양을 정한다

 거부 핸들러가 쓴 응답
      --> 기본 구현은 errorPage 가 없으면 sendError(403)
      --> errorPage 를 주면 403 상태로 그 경로에 forward 한다
```

## 다루지 않는 것

`RequestCache` 구현별 저장 규칙과 `SavedRequest` 복원, `AuthenticationEntryPoint` 구현들(`LoginUrlAuthenticationEntryPoint`, `BasicAuthenticationEntryPoint`, `DelegatingAuthenticationEntryPoint`)의 세부, 서블릿 컨테이너의 에러 페이지 디스패치는 같은 뼈대의 곁가지라 요약만 했다. 메서드 보안에서 난 거부가 어떻게 처리되는지도 별도 경로다.

## 하위 메서드

- [01 ExceptionTranslationFilter.doFilter](01_ExceptionTranslationFilter.doFilter/README.md)
- [spi](spi/README.md) — 인증 진입점, 접근 거부 핸들러, 신뢰 해석기

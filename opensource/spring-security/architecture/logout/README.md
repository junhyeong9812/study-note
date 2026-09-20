# 로그아웃

인증을 만드는 [폼 로그인](../form-login/README.md)의 반대편이다. 세션을 무효화하고 컨텍스트를 비운다. 여러 핸들러를 차례로 부르는 구조라 확장 지점이 많다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 로그아웃 핸들러 계약 모음이다.

기준 커밋: spring-security `main` [`26b6b2a84f`](https://github.com/spring-projects/spring-security/tree/26b6b2a84fa8fa26991ca0f57282720b48db9f91) (2026-09-18). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 POST /logout
 |
 +-- [01] LogoutFilter.doFilter
          이 요청이 로그아웃 요청인가부터 본다
          아니면 체인으로 흘린다
          |
          +-- [01-01] CompositeLogoutHandler.logout   (L106)
          |        등록된 LogoutHandler 를 등록 순서대로 전부 부른다
          |        하나가 끝나면 다음 것. 결과를 보지 않는다
          |        |
          |        +-- [01-02] SecurityContextLogoutHandler.logout
          |                 세션 무효화 -> 컨텍스트 비우기 -> 저장소 정리
          |                 실제로 로그아웃을 성립시키는 핵심 핸들러다
          |
          +-- LogoutSuccessHandler.onLogoutSuccess   (L107)
                   응답을 쓴다. 기본은 리다이렉트
```

```text
 로그아웃도 상태를 바꾸는 요청이다

 설정이 CSRF 를 켰으면    POST /logout 만 받는다
 CSRF 를 껐으면           GET, POST, PUT, DELETE 를 다 받는다

 LogoutConfigurer.createLogoutRequestMatcher 가 이 분기를 한다
 그리고 CSRF 는 기본으로 켜져 있다

 그래서 <a href="/logout"> 링크는 로그아웃을 바로 수행하지 못한다
 다만 그냥 지나가는 것도 아니다 --
 기본 구성에는 DefaultLogoutPageGeneratingFilter 가 뒤에 있어 (순서상 L88 < L109)
 GET /logout 을 가로채 CSRF 토큰이 든 POST 폼(확인 페이지)을 렌더한다

 로그인 페이지 생성이 전부 꺼진 구성에서만 체인을 그대로 지나간다
```

```text
 핸들러가 줄지어 있다

 CompositeLogoutHandler 가 등록 순서대로 부른다

 Java 설정(LogoutConfigurer)이 마지막에 두 개를 덧붙인다 (L334-335)
   SecurityContextLogoutHandler             세션과 컨텍스트를 정리
   LogoutSuccessEventPublishingLogoutHandler 이벤트 발행

 그 앞에는 다른 설정이 자동으로 넣은 것과 사용자가 넣은 것이 온다
   CsrfLogoutHandler       CsrfConfigurer L257-260 이 넣는다 (CSRF 가 기본 on)
   remember-me 서비스      RememberMeConfigurer L276-279
   CookieClearingLogoutHandler  deleteCookies(...) 를 쓰면
   직접 만든 것            addLogoutHandler(...)

 즉 아무것도 추가하지 않아도 기본 목록은 셋이다

 순서가 중요하다 -- 세션이 무효화된 뒤에는 getSession(false) 가 null 이라
 세션에서 아무것도 꺼낼 수 없다 (대개 예외가 아니라 조용한 건너뛰기다)
 LogoutFilter javadoc L43-46 도 remember-me 계열을
 SecurityContextLogoutHandler 앞에 두라고 권한다
```

## 어디에서 쓰이는가

```text
 [필터 체인] 체인의 한 칸이다. /logout 이 아니면 그냥 흘려보낸다
 [보안 컨텍스트] 저장소에 빈 컨텍스트를 넘겨 기존 인증을 지운다
 [CSRF 방어] CSRF 설정 여부가 허용 메서드를 정한다
 [폼 로그인] 저장한 인증을 되돌리는 반대 방향의 작업이다
```

인증을 만드는 쪽은 [폼 로그인](../form-login/README.md), 저장소가 그것을 어떻게 다루는지는 [보안 컨텍스트](../security-context/README.md)에 있다.

## 단계

1. [LogoutFilter.doFilter](01_LogoutFilter.doFilter/README.md)가 로그아웃 요청을 가려낸다.
2. [CompositeLogoutHandler.logout](01_LogoutFilter.doFilter/01_CompositeLogoutHandler.logout/README.md)이 핸들러들을 차례로 부른다.
3. [SecurityContextLogoutHandler.logout](01_LogoutFilter.doFilter/02_SecurityContextLogoutHandler.logout/README.md)이 실제로 인증을 지운다.

## 결과가 쓰이는 곳

```text
 무효화된 세션
      --> 세션에 담겨 있던 모든 것이 사라진다
      --> SecurityContext 뿐 아니라 장바구니 같은 애플리케이션 상태도 함께 간다

 저장소에 넘긴 빈 컨텍스트
      --> 기본 저장소는 이것을 저장하지 않고 세션 속성을 지운다
      --> 세션을 이미 무효화했다면 지울 세션도 없어 사실상 no-op 이다
      --> 다음 요청은 읽을 것이 없어 새 빈 컨텍스트로 시작한다
      --> 세션을 무효화하지 않는 설정에서는 이 제거가 실제로 인증을 지운다

 발행되는 LogoutSuccessEvent
      --> LogoutSuccessEventPublishingLogoutHandler 가 발행한다
      --> 감사 로그가 이것을 듣는다

 성공 핸들러가 쓴 응답
      --> 체인이 거기서 끝난다. 뒤의 필터도 컨트롤러도 실행되지 않는다
      --> 기본은 리다이렉트다. REST API 라면 이 자리를 바꾼다
```

## 다루지 않는 것

각 `LogoutHandler` 구현의 세부(`CookieClearingLogoutHandler`, `CsrfLogoutHandler`, `HeaderWriterLogoutHandler`), `LogoutSuccessHandler` 구현별 리다이렉트 규칙, remember-me 토큰 정리, OIDC 백채널 로그아웃과 SAML 로그아웃은 같은 뼈대의 곁가지라 요약만 했다. 세션 레지스트리를 쓰는 동시 세션 제어도 별도 경로다.

## 하위 메서드

- [01 LogoutFilter.doFilter](01_LogoutFilter.doFilter/README.md)
- [spi](spi/README.md) — 로그아웃 핸들러, 성공 핸들러

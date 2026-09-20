# SecurityContextLogoutHandler.logout

상위: [LogoutFilter.doFilter](../README.md)

실제로 로그아웃을 성립시키는 핸들러다. 세션을 무효화하고 컨텍스트를 비운 뒤, 빈 컨텍스트를 저장소에 저장한다.

## 위치

`web` / `org.springframework.security.web.authentication.logout` / `SecurityContextLogoutHandler.java` L67-L87 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/authentication/logout/SecurityContextLogoutHandler.java#L67-L87))

## 실제 코드

```java
// SecurityContextLogoutHandler.java L67-L87
@Override
public void logout(HttpServletRequest request, HttpServletResponse response,
        @Nullable Authentication authentication) {
    Assert.notNull(request, "HttpServletRequest required");
    if (this.invalidateHttpSession) {
        HttpSession session = request.getSession(false);
        if (session != null) {
            session.invalidate();
            if (this.logger.isDebugEnabled()) {
                this.logger.debug(LogMessage.format("Invalidated session %s", session.getId()));
            }
        }
    }
    SecurityContext context = this.securityContextHolderStrategy.getContext();
    this.securityContextHolderStrategy.clearContext();
    if (this.clearAuthentication) {
        context.setAuthentication(null);
    }
    SecurityContext emptyContext = this.securityContextHolderStrategy.createEmptyContext();
    this.securityContextRepository.saveContext(emptyContext, request, response);
}
```

## 동작 흐름

```text
 logout(request, response, authentication)
 |
 +-- L71 invalidateHttpSession 이면
 |      L72 request.getSession(false)   없으면 만들지 않는다
 |      L73 세션이 있으면 L74 session.invalidate()
 |
 | L80 현재 컨텍스트를 꺼내 두고
 | L81 securityContextHolderStrategy.clearContext()
 |
 +-- L82 clearAuthentication 이면
 |      L83 꺼내 둔 컨텍스트의 authentication 을 null 로 만든다
 |
 | L85 createEmptyContext()
 +-- L86 securityContextRepository.saveContext(빈 컨텍스트, request, response)
        기본 저장소는 빈 컨텍스트를 저장하지 않고 세션 속성을 지운다
```

```text
 왜 꺼내 두었다가 다시 건드리는가

 L80 에서 컨텍스트 객체를 붙잡아 둔다
 L81 에서 ThreadLocal 을 비운다 -- 하지만 객체 자체는 살아 있다
 L83 에서 그 객체의 authentication 을 null 로 만든다

 setClearAuthentication 의 javadoc 이 이유를 밝힌다 (L114-119) --
 동시 요청과의 문제를 막기 위해서다
 같은 SecurityContext 인스턴스를 동시 요청이 들고 있을 수 있고,
 ThreadLocal 만 비우면 그쪽은 여전히 인증을 들고 있다
```

```text
 세 가지 정리가 각각 독립이다

 세션 무효화     invalidateHttpSession 플래그. 기본 true (L55)
 참조 무력화     clearAuthentication 플래그. 기본 true (L57)
 저장소 정리     항상 한다 (L85-86)

 앞의 둘은 끌 수 있지만 마지막은 끌 수 없다

 커스텀 로그아웃 엔드포인트를 만들더라도 이 핸들러를 직접 불러야 한다고
 레퍼런스가 못박는다 (servlet/authentication/logout.adoc)
```

```text
 세션을 만들지 않는다

 L72 request.getSession(false)

 false 를 넘겨 없으면 만들지 않는다
 로그아웃하려다 세션을 새로 만드는 일이 없다
```

## 결과가 쓰이는 곳

```text
 무효화된 세션
      --> 세션 ID 가 무효가 된다. 쿠키가 남아 있어도 쓸 수 없다
      --> 세션에 담긴 애플리케이션 데이터도 함께 사라진다

 저장소에 넘긴 빈 컨텍스트
      --> HttpSessionSecurityContextRepository 는 빈 컨텍스트를 받으면
          저장하지 않고 세션의 SPRING_SECURITY_CONTEXT 속성을 지운다 (L161-175)
      --> 세션을 이미 무효화한 기본 경로에서는 지울 세션이 없어 no-op 이다
      --> 다음 요청은 읽을 것이 없어 새 빈 컨텍스트로 시작한다

 설정으로 끄는 경우
      --> invalidateHttpSession(false) 로 세션을 살려 둘 수 있다
      --> 장바구니처럼 로그아웃 뒤에도 남겨야 할 것이 있을 때 쓴다
      --> 이때는 세션이 살아 있으므로 저장소의 속성 제거가 실제로 일을 한다
          그래서 세션을 남겨도 인증은 사라진다
```

이 저장이 다음 요청에 어떻게 복원되는지는 [보안 컨텍스트](../../../security-context/README.md)에 있다.

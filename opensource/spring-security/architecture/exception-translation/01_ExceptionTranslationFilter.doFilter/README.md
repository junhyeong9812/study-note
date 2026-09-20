# ExceptionTranslationFilter.doFilter

상위: [예외 변환](../README.md)

뒤의 체인을 `try` 로 감싸고, 올라온 예외에서 보안 예외를 골라낸다.

## 위치

`web` / `org.springframework.security.web.access` / `ExceptionTranslationFilter.java` L123-L149 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/access/ExceptionTranslationFilter.java#L123-L149))

## 실제 코드

public 진입점은 캐스팅만 한다.

```java
// ExceptionTranslationFilter.java L117-L121
@Override
public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
        throws IOException, ServletException {
    doFilter((HttpServletRequest) request, (HttpServletResponse) response, chain);
}
```

```java
// ExceptionTranslationFilter.java L123-L149
private void doFilter(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
        throws IOException, ServletException {
    try {
        chain.doFilter(request, response);
    }
    catch (IOException ex) {
        throw ex;
    }
    catch (Exception ex) {
        // Try to extract a SpringSecurityException from the stacktrace
        Throwable[] causeChain = this.throwableAnalyzer.determineCauseChain(ex);
        RuntimeException securityException = (AuthenticationException) this.throwableAnalyzer
            .getFirstThrowableOfType(AuthenticationException.class, causeChain);
        if (securityException == null) {
            securityException = (AccessDeniedException) this.throwableAnalyzer
                .getFirstThrowableOfType(AccessDeniedException.class, causeChain);
        }
        if (securityException == null) {
            rethrow(ex);
        }
        if (response.isCommitted()) {
            throw new ServletException("Unable to handle the Spring Security Exception "
                    + "because the response is already committed.", ex);
        }
        handleSpringSecurityException(request, response, chain, securityException);
    }
}
```

보안 예외가 아니면 원래 타입 그대로 다시 던진다.

`web` / `org.springframework.security.web.access` / `ExceptionTranslationFilter.java` L151-L162 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/access/ExceptionTranslationFilter.java#L151-L162))

```java
// ExceptionTranslationFilter.java L151-L162
private void rethrow(Exception ex) throws ServletException {
    // Rethrow ServletExceptions and RuntimeExceptions as-is
    if (ex instanceof ServletException) {
        throw (ServletException) ex;
    }
    if (ex instanceof RuntimeException) {
        throw (RuntimeException) ex;
    }
    // Wrap other Exceptions. This shouldn't actually happen
    // as we've already covered all the possibilities for doFilter
    throw new RuntimeException(ex);
}
```

## 동작 흐름

```text
 doFilter(request, response, chain)
 |
 | L125 try
 |   L126 chain.doFilter(request, response)
 |
 +-- L128 IOException 이면 L129 그대로 던진다
 |        보안과 무관한 I/O 문제라 손대지 않는다
 |
 +-- L131 그 밖의 Exception 이면
        L133 throwableAnalyzer.determineCauseChain(ex)   원인 사슬을 편다
        L134 getFirstThrowableOfType(AuthenticationException.class, ...)
        L136 못 찾았으면
               L137 getFirstThrowableOfType(AccessDeniedException.class, ...)
        |
        +-- L140 둘 다 없으면 L141 rethrow(ex) -- 이 필터의 일이 아니다
        |
        +-- L143 응답이 이미 커밋됐으면
        |        L144 ServletException -- 더 쓸 수가 없다
        |
        +-- L147 handleSpringSecurityException(...)
```

```text
 인증 예외를 먼저 찾는다

 L134 AuthenticationException 을 먼저 보고
 L136 없을 때만 AccessDeniedException 을 본다

 둘 다 사슬에 있으면 인증 예외가 이긴다
 (그 순서의 이유는 소스에 적혀 있지 않다)
```

```text
 원인 사슬을 펴는 이유

 보안 예외는 체인 깊숙한 곳에서 던져지고
 중간의 필터나 서블릿이 다른 예외로 감싸는 일이 흔하다

 determineCauseChain 이 사슬을 배열로 펴고
 getFirstThrowableOfType 이 타입이 맞는 첫 항목을 집는다

 이 필터가 쓰는 것은 DefaultThrowableAnalyzer 다 (L95)
 ServletException 의 rootCause 까지 벗겨 내는 전용 구현이라,
 MVC 가 감싼 예외 속의 보안 예외도 찾아낸다

 FilterChainProxy 도 같은 메서드를 쓰지만 기본 ThrowableAnalyzer 다
 그쪽은 RequestRejectedException 을 찾는다
```

```text
 rethrow 는 타입을 보존한다 (L151-162)

 ServletException 이면 그대로
 RuntimeException 이면 그대로
 그 밖은 RuntimeException 으로 감싼다

 주석이 마지막 경우를 "실제로는 일어나지 않는다"고 적고 있다
 doFilter 가 던질 수 있는 타입을 이미 다 다뤘기 때문이다
```

## 결과가 쓰이는 곳

```text
 IOException 을 먼저 거르는 것
      --> 클라이언트가 연결을 끊은 경우 등이 보안 처리로 새지 않는다

 rethrow 로 올라간 예외
      --> 필터 체인 위쪽(FilterChainProxy)과 서블릿 컨테이너로 올라간다
      --> 컨테이너의 ERROR 디스패치로 처리된다
      --> 반대 방향에 함정이 있다. @ExceptionHandler 는 이 필터보다
          안쪽(DispatcherServlet)에서 돌기 때문에,
          컨트롤러의 AccessDeniedException 을 거기서 먼저 잡으면
          이 필터는 그 예외를 아예 보지 못한다

 응답 커밋 검사
      --> 이미 응답이 나가기 시작했으면 리다이렉트도 상태 코드도 못 바꾼다
      --> 그 상황을 조용히 넘기지 않고 ServletException 으로 드러낸다

 handleSpringSecurityException
      --> L174 인증 예외면 진입점으로
      --> L177 접근 거부면 신뢰 수준을 보고 갈라진다
```

## 하위 메서드

- [01 ExceptionTranslationFilter.handleAccessDeniedException](01_ExceptionTranslationFilter.handleAccessDeniedException/README.md)
- [02 ExceptionTranslationFilter.sendStartAuthentication](02_ExceptionTranslationFilter.sendStartAuthentication/README.md)

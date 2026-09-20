# UsernamePasswordAuthenticationFilter.attemptAuthentication

상위: [AbstractAuthenticationProcessingFilter.doFilter](../README.md)

요청 파라미터를 인증 토큰으로 바꾼다. HTTP 를 아는 마지막 지점이고, 여기서부터는 매니저의 세계다.

## 위치

`web` / `org.springframework.security.web.authentication` / `UsernamePasswordAuthenticationFilter.java` L73-L88 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/authentication/UsernamePasswordAuthenticationFilter.java#L73-L88))

## 실제 코드

```java
// UsernamePasswordAuthenticationFilter.java L73-L88
@Override
public Authentication attemptAuthentication(HttpServletRequest request, HttpServletResponse response)
        throws AuthenticationException {
    if (this.postOnly && !request.getMethod().equals("POST")) {
        throw new AuthenticationServiceException("Authentication method not supported: " + request.getMethod());
    }
    String username = obtainUsername(request);
    username = (username != null) ? username.trim() : "";
    String password = obtainPassword(request);
    password = (password != null) ? password : "";
    UsernamePasswordAuthenticationToken authRequest = UsernamePasswordAuthenticationToken.unauthenticated(username,
            password);
    // Allow subclasses to set the "details" property
    setDetails(request, authRequest);
    return this.getAuthenticationManager().authenticate(authRequest);
}
```

기본 매처와 파라미터 이름의 기본값은 클래스 위쪽에 있다. 앞의 셋은 상수이고, 파라미터 이름과 postOnly 는 setter 로 바꿀 수 있는 필드다.

`web` / `org.springframework.security.web.authentication` / `UsernamePasswordAuthenticationFilter.java` L52-L63 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/authentication/UsernamePasswordAuthenticationFilter.java#L52-L63))

```java
// UsernamePasswordAuthenticationFilter.java L52-L63
public static final String SPRING_SECURITY_FORM_USERNAME_KEY = "username";

public static final String SPRING_SECURITY_FORM_PASSWORD_KEY = "password";

private static final RequestMatcher DEFAULT_PATH_REQUEST_MATCHER = PathPatternRequestMatcher.withDefaults()
    .matcher(HttpMethod.POST, "/login");

private String usernameParameter = SPRING_SECURITY_FORM_USERNAME_KEY;

private String passwordParameter = SPRING_SECURITY_FORM_PASSWORD_KEY;

private boolean postOnly = true;
```

## 동작 흐름

```text
 attemptAuthentication(request, response)
 |
 +-- L76 postOnly 이고 POST 가 아니면
 |        L77 AuthenticationServiceException
 |        postOnly 는 기본 true 다 (L63)
 |
 | L79 obtainUsername(request)   기본은 "username" 파라미터
 | L80 null 이면 빈 문자열, 아니면 trim()
 | L81 obtainPassword(request)   기본은 "password" 파라미터
 | L82 null 이면 빈 문자열 (trim 하지 않는다)
 |
 | L83 UsernamePasswordAuthenticationToken.unauthenticated(username, password)
 |        아직 인증되지 않은 토큰
 |
 | L86 setDetails(request, authRequest)
 |        IP 와 세션 ID 같은 부가 정보를 담는다
 |
 +-- L87 getAuthenticationManager().authenticate(authRequest)
```

```text
 username 만 trim 한다

 L80 username = (username != null) ? username.trim() : ""
 L82 password = (password != null) ? password : ""

 비밀번호는 앞뒤 공백도 값의 일부다
 사용자 이름은 실수로 들어간 공백을 없애 준다
```

```text
 null 을 빈 문자열로 바꾼다

 파라미터가 아예 없으면 null 이 온다
 여기서 빈 문자열로 정규화해, 이후 경로가 null 을 따로 다루지 않게 한다

 결과적으로 "빈 아이디로 로그인 시도"가 되어
 정상적인 인증 실패 경로를 탄다
```

## 결과가 쓰이는 곳

```text
 만들어진 unauthenticated 토큰
      --> principal 은 문자열, credentials 는 평문 비밀번호다
      --> 이 상태로 매니저와 프로바이더를 거친다
      --> 이 토큰 자체는 그대로 남는다
          평문은 createSuccessAuthentication 이 결과 토큰으로 옮기고
          (AbstractUserDetailsAuthenticationProvider L229-230)
          매니저가 그 결과 토큰의 credentials 를 지운다 (ProviderManager L230-233)

 details
      --> WebAuthenticationDetails 가 기본이다. 원격 IP 와 세션 ID 를 담는다
      --> 감사 로그가 이 값을 쓴다

 던진 AuthenticationServiceException
      --> 상위 doFilter 의 catch 로 올라가 실패 처리된다
      --> GET /login 으로 폼을 여는 것과는 무관하다.
          그쪽은 애초에 requiresAuthentication 이 false 다
```

# AccessDeniedHandler

상위: [spi](../README.md)

인증은 됐는데 권한이 없는 경우의 응답을 만든다.

## 위치

`web` / `org.springframework.security.web.access` / `AccessDeniedHandler.java` L33-L46 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/access/AccessDeniedHandler.java#L33-L46))

## 실제 코드

```java
// AccessDeniedHandler.java L33-L46 (javadoc 생략)
public interface AccessDeniedHandler {

    void handle(HttpServletRequest request, HttpServletResponse response, AccessDeniedException accessDeniedException)
            throws IOException, ServletException;

}
```

## 흐름에서 불리는 자리

```text
 ExceptionTranslationFilter.handleAccessDeniedException
   L210 accessDeniedHandler.handle(request, response, exception)
   익명도 기억된 사용자도 아닐 때만 여기로 온다
```

- [ExceptionTranslationFilter.handleAccessDeniedException](../../01_ExceptionTranslationFilter.doFilter/01_ExceptionTranslationFilter.handleAccessDeniedException/README.md)

## 구현 계층

```text
 AccessDeniedHandler
   +-- AccessDeniedHandlerImpl        기본. 403 또는 errorPage 로 forward
   +-- HttpStatusAccessDeniedHandler  상태 코드만. API 서버용
   +-- DelegatingAccessDeniedHandler  예외 타입별로 나눈다
   +-- RequestMatcherDelegatingAccessDeniedHandler  요청별로 나눈다
   +-- CompositeAccessDeniedHandler   여럿을 차례로 부른다
   +-- InvalidSessionAccessDeniedHandler  세션이 만료된 경우를 따로 다룬다
   +-- ObservationMarkingAccessDeniedHandler
   +-- NoOpAccessDeniedHandler
   +-- (사용자 구현)

 CSRF 전용 핸들러는 따로 없다
 CsrfConfigurer 가 위의 것들을 조합해 쓴다
```

## 결과가 쓰이는 곳

```text
 기본 구현의 두 갈래 (AccessDeniedHandlerImpl)
      --> errorPage 가 없으면 sendError(403)
      --> 있으면 상태를 403 으로 세우고 그 경로로 forward 한다
          이때 요청 속성에 예외를 담아 뷰가 쓸 수 있게 한다

 응답이 이미 커밋된 경우
      --> 기본 구현은 아무것도 쓰지 않고 조용히 돌아간다 (trace 로그만)

 sendError 를 쓰는 점
      --> setStatus 가 아니라 sendError 라
          컨테이너의 에러 페이지 디스패치가 발동한다
      --> 그 디스패치도 필터 체인을 다시 탈 수 있다
```

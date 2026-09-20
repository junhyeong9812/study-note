# CsrfTokenRequestHandler

상위: [spi](../README.md)

토큰을 요청 속성에 노출하고, 요청에서 다시 꺼낸다. 내보내는 쪽과 받는 쪽이 한 인터페이스에 있다.

## 위치

`web` / `org.springframework.security.web.csrf` / `CsrfTokenRequestHandler.java` L39-L71 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/csrf/CsrfTokenRequestHandler.java#L39-L71))

## 실제 코드

```java
// CsrfTokenRequestHandler.java L39-L71 (javadoc 생략)
@FunctionalInterface
public interface CsrfTokenRequestHandler extends CsrfTokenRequestResolver {

    void handle(HttpServletRequest request, HttpServletResponse response, Supplier<CsrfToken> csrfToken);

    @Override
    default @Nullable String resolveCsrfTokenValue(HttpServletRequest request, CsrfToken csrfToken) {
        Assert.notNull(request, "request cannot be null");
        Assert.notNull(csrfToken, "csrfToken cannot be null");
        String actualToken = request.getHeader(csrfToken.getHeaderName());
        if (actualToken != null) {
            return actualToken;
        }
        CsrfTokenRequestHandlerLoggerHolder.logger.trace(
                LogMessage.format("Did not find a CSRF token in the [%s] request header", csrfToken.getHeaderName()));

        actualToken = request.getParameter(csrfToken.getParameterName());
        if (actualToken != null) {
            return actualToken;
        }
        CsrfTokenRequestHandlerLoggerHolder.logger.trace(LogMessage
            .format("Did not find a CSRF token in the [%s] request parameter", csrfToken.getParameterName()));

        return null;
    }

}
```

## 흐름에서 불리는 자리

```text
 CsrfFilter.doFilterInternal
   L112 requestHandler.handle(request, response, deferredCsrfToken)
   L122 requestHandler.resolveCsrfTokenValue(request, csrfToken)
```

- [XorCsrfTokenRequestAttributeHandler.handle](../../01_CsrfFilter.doFilterInternal/02_XorCsrfTokenRequestAttributeHandler.handle/README.md)

## 구현 계층

```text
 CsrfTokenRequestResolver
   +-- CsrfTokenRequestHandler (@FunctionalInterface)
         +-- CsrfTokenRequestAttributeHandler      요청 속성에 그대로 심는다
               +-- XorCsrfTokenRequestAttributeHandler  기본. 값을 매번 섞는다
         +-- SpaCsrfTokenRequestHandler            csrf().spa() 가 꽂는다
                                                  CsrfConfigurer 내부 private
                                                  헤더에 값이 있으면 plain,
                                                  없으면 xor 로 갈라 푼다
         +-- (사용자 구현)

 CsrfFilter 의 필드 기본값이 XorCsrfTokenRequestAttributeHandler 다 (L91)
```

## 결과가 쓰이는 곳

```text
 handle
      --> Supplier 를 요청 속성에 심는다. 응답은 건드리지 않는다
      --> 뷰가 실제로 읽을 때 값이 만들어진다

 resolveCsrfTokenValue 의 default 구현
      --> 헤더를 먼저 보고(L54), 없으면 파라미터를 본다(L61)
      --> 둘 다 없으면 null 이라 대조에서 실패한다
      --> XOR 구현은 이것을 super 로 부른 뒤 값을 한 번 더 푼다

 인터페이스를 나눈 모양
      --> 내보내는 handle 과 받는 resolveCsrfTokenValue 가 한 쌍이다
      --> 한쪽만 바꾸면 짝이 맞지 않아 대조가 실패한다
```

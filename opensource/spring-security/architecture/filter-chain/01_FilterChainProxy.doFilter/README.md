# FilterChainProxy.doFilter

상위: [필터 체인](../README.md)

서블릿 컨테이너가 Spring Security 를 부르는 유일한 지점이다. 이 메서드가 하는 일은 셋이다 — 중첩 호출 가려내기, 거부 예외 처리, 그리고 끝난 뒤 컨텍스트 비우기.

## 위치

`web` / `org.springframework.security.web` / `FilterChainProxy.java` L186-L211 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/FilterChainProxy.java#L186-L211))

## 실제 코드

```java
// FilterChainProxy.java L186-L211
public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
        throws IOException, ServletException {
    boolean clearContext = request.getAttribute(FILTER_APPLIED) == null;
    if (!clearContext) {
        doFilterInternal(request, response, chain);
        return;
    }
    try {
        request.setAttribute(FILTER_APPLIED, Boolean.TRUE);
        doFilterInternal(request, response, chain);
    }
    catch (Exception ex) {
        Throwable[] causeChain = this.throwableAnalyzer.determineCauseChain(ex);
        Throwable requestRejectedException = this.throwableAnalyzer
            .getFirstThrowableOfType(RequestRejectedException.class, causeChain);
        if (!(requestRejectedException instanceof RequestRejectedException)) {
            throw ex;
        }
        this.requestRejectedHandler.handle((HttpServletRequest) request, (HttpServletResponse) response,
                (RequestRejectedException) requestRejectedException);
    }
    finally {
        this.securityContextHolderStrategy.clearContext();
        request.removeAttribute(FILTER_APPLIED);
    }
}
```

## 동작 흐름

```text
 doFilter(request, response, chain)
 |
 | L188 clearContext = request.getAttribute(FILTER_APPLIED) == null
 |        이 요청에 FilterChainProxy 가 처음 걸리는가를 본다
 |
 +-- L189 처음이 아니면 (중첩 호출)
 |        L190 doFilterInternal 만 부르고 L191 바로 return
 |        --> 컨텍스트를 비우지 않는다. 그 일은 바깥 호출의 몫이다
 |
 +-- L193 처음이면
        L194 FILTER_APPLIED 속성을 심는다
        L195 doFilterInternal(request, response, chain)
        |
        | catch (L197) 예외가 올라오면
        |   L198 throwableAnalyzer.determineCauseChain(ex)  원인 사슬을 편다
        |   L199-200 getFirstThrowableOfType(RequestRejectedException.class, ...)
        |   L201-202 거부 예외가 아니면 그대로 다시 던진다
        |   L204 맞으면 requestRejectedHandler.handle(...)
        |          기본 구현은 사유를 debug 로 남기고 sendError(400)
        |
        | finally (L207)
        |   L208 securityContextHolderStrategy.clearContext()
        |   L209 request.removeAttribute(FILTER_APPLIED)
```

```text
 왜 원인 사슬을 펴는가

 RequestRejectedException 은 체인 깊숙한 곳에서 던져지고
 중간의 필터나 컨테이너가 다른 예외로 감싸는 일이 흔하다

 ex = ServletException
        cause = RequestRejectedException   <- 이것을 찾아야 한다

 determineCauseChain 이 사슬을 배열로 펴고
 getFirstThrowableOfType 이 그 안에서 타입이 맞는 첫 항목을 집는다
 못 찾으면 원래 예외를 그대로 다시 던진다 (L201-202)
```

```text
 중첩은 언제 일어나는가

 같은 요청이 FilterChainProxy 를 두 번 지나는 경우가 있다
 예: 서블릿이 forward 나 include 를 걸고, 그 디스패치에도 필터가 매핑된 경우

 바깥 호출  FILTER_APPLIED 없음 --> 심고 --> ... --> finally 에서 비운다
 안쪽 호출  FILTER_APPLIED 있음 --> doFilterInternal 만 --> 비우지 않는다

 안쪽에서 비워 버리면 바깥 호출의 나머지 필터들이
 인증 정보를 잃은 채로 돌게 된다
```

## 결과가 쓰이는 곳

```text
 clearContext
      --> ThreadLocal 에 담긴 SecurityContext 를 지운다
      --> 서블릿 컨테이너는 스레드를 재사용하므로,
          지우지 않으면 다음 요청이 앞 사용자로 인증된 채 시작한다

 removeAttribute(FILTER_APPLIED)
      --> finally 에서 속성도 함께 걷는다

 requestRejectedHandler
      --> 방화벽이 거부한 요청의 응답을 정한다
      --> 기본은 HttpStatusRequestRejectedHandler
          사유를 debug 로 남기고 sendError(400) 을 부른다

 다시 던진 예외
      --> 거부 예외가 아니면 컨테이너로 올라간다
      --> 인증/인가 예외는 보통 여기까지 오지 않는다.
          체인 안의 ExceptionTranslationFilter 가 먼저 잡기 때문이다
          단 그 필터보다 앞에서 터진 예외는 그대로 올라온다
```

인증과 인가 예외가 어디서 걸러지는지는 [예외 변환](../../exception-translation/README.md)에 있다.

## 하위 메서드

- [01 FilterChainProxy.doFilterInternal](01_FilterChainProxy.doFilterInternal/README.md)

# HandlerInterceptor

상위: [Spring MVC 요청 처리](../../README.md) / [spi](../README.md)

핸들러 실행 앞뒤에 끼어드는 훅이다. 세 메서드 모두 default라 필요한 것만 구현한다.

## 실제 코드

`spring-webmvc` / `org.springframework.web.servlet` / `HandlerInterceptor.java` L80-L158 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/HandlerInterceptor.java#L80-L158))

```java
// HandlerInterceptor.java L80-L158
public interface HandlerInterceptor {

    default boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler)
            throws Exception {

        return true;
    }

    default void postHandle(HttpServletRequest request, HttpServletResponse response, Object handler,
            @Nullable ModelAndView modelAndView) throws Exception {
    }

    default void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler,
            @Nullable Exception ex) throws Exception {
    }

}
```

## 흐름에서 불리는 자리

```text
 HandlerExecutionChain
   applyPreHandle          preHandle        정순, false면 중단
   applyPostHandle         postHandle       역순, 핸들러 정상 종료 시만
   triggerAfterCompletion  afterCompletion  역순, preHandle 성공한 것만, 예외 나도 호출
```

- [HandlerExecutionChain](../../02_DispatcherServlet.doDispatch/03_HandlerExecutionChain/README.md)
- [AbstractHandlerMapping.getHandler](../../02_DispatcherServlet.doDispatch/02_DispatcherServlet.getHandler/01_AbstractHandlerMapping.getHandler/README.md)

## 구현 계층

```text
 HandlerInterceptor
   +-- AsyncHandlerInterceptor           비동기 시작 시 afterConcurrentHandlingStarted
   +-- MappedInterceptor                 경로 패턴으로 적용 범위 제한 (래퍼)
   +-- LocaleChangeInterceptor           ?locale=ko 로 Locale 변경
   +-- WebContentInterceptor             캐시 헤더
   +-- (내부) CorsInterceptor            AbstractHandlerMapping이 0번에 삽입
```

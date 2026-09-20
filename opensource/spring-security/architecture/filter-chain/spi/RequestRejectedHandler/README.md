# RequestRejectedHandler

상위: [spi](../README.md)

방화벽이 거부한 요청에 어떤 응답을 줄지 정한다.

## 위치

`web` / `org.springframework.security.web.firewall` / `RequestRejectedHandler.java` L32-L45 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/firewall/RequestRejectedHandler.java#L32-L45))

## 실제 코드

```java
// RequestRejectedHandler.java L32-L45 (javadoc 생략)
public interface RequestRejectedHandler {

    void handle(HttpServletRequest request, HttpServletResponse response,
            RequestRejectedException requestRejectedException) throws IOException, ServletException;

}
```

## 흐름에서 불리는 자리

```text
 FilterChainProxy.doFilter 의 catch 블록
   원인 사슬에서 RequestRejectedException 을 찾아냈을 때만 불린다
   못 찾으면 원래 예외를 그대로 다시 던진다
```

- [FilterChainProxy.doFilter](../../01_FilterChainProxy.doFilter/README.md)

## 구현 계층

```text
 RequestRejectedHandler
   +-- HttpStatusRequestRejectedHandler    기본. sendError 로 상태 코드를 보낸다
   +-- DefaultRequestRejectedHandler       예외를 다시 던진다
   +-- CompositeRequestRejectedHandler     여러 핸들러를 묶는다
   +-- ObservationMarkingRequestRejectedHandler  관측에 표시만 남긴다
   +-- (사용자 구현)
```

## 결과가 쓰이는 곳

```text
 쓴 응답
      --> 필터 체인을 타지 않은 응답이다
      --> 그래서 ExceptionTranslationFilter 의 처리 대상이 아니다

 거부 사유를 감추는 이유
      --> 상세한 사유를 돌려주면 우회 방법을 알려 주는 셈이 된다
      --> 기본 구현이 상태 코드만 쓰는 배경이다
```

# CompositeLogoutHandler.logout

상위: [LogoutFilter.doFilter](../README.md)

등록된 핸들러를 순서대로 전부 부른다. 실행문은 두 줄이지만 로그아웃의 확장 구조가 여기 다 있다.

## 위치

`web` / `org.springframework.security.web.authentication.logout` / `CompositeLogoutHandler.java` L52-L58 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/authentication/logout/CompositeLogoutHandler.java#L52-L58))

## 실제 코드

```java
// CompositeLogoutHandler.java L52-L58
@Override
public void logout(HttpServletRequest request, HttpServletResponse response,
        @Nullable Authentication authentication) {
    for (LogoutHandler handler : this.logoutHandlers) {
        handler.logout(request, response, authentication);
    }
}
```

## 동작 흐름

```text
 logout(request, response, authentication)
 |
 +-- L55 for (LogoutHandler handler : this.logoutHandlers)
        L56 handler.logout(request, response, authentication)

 그게 전부다
```

```text
 결과를 보지 않는다

 반환값이 void 라 성공 여부를 알 수 없다
 예외를 잡지도 않는다

 한 핸들러가 예외를 던지면 거기서 멈추고,
 뒤의 핸들러는 실행되지 않으며, 성공 핸들러도 불리지 않는다
 예외는 필터 밖으로 올라간다
```

```text
 순서가 설정에서 정해진다

 LogoutConfigurer.createLogoutFilter 가 목록을 완성한다 (L331-337)
   addLogoutHandler 로 들어온 것들 (설정이 자동으로 넣은 것 + 사용자 것)
   L334 SecurityContextLogoutHandler
   L335 LogoutSuccessEventPublishingLogoutHandler

 앞자리가 사용자 전용이 아니다 --
 CsrfConfigurer 와 RememberMeConfigurer 도 addLogoutHandler 로 끼어든다

 세션을 읽어야 하는 핸들러는 앞에 있어야 한다
 SecurityContextLogoutHandler 가 세션을 무효화한 뒤에는
 getSession(false) 가 null 이라 꺼낼 것이 없다
```

## 결과가 쓰이는 곳

```text
 등록 순서
      --> 그대로 실행 순서다
      --> 정렬하지 않는다

 같은 인자를 모두에게 넘기는 점
      --> 핸들러끼리 값을 주고받는 통로가 없다
      --> 상태를 공유하려면 요청 속성을 써야 한다

 LogoutFilter 생성자
      --> 넘긴 핸들러 배열을 CompositeLogoutHandler 로 감싼다 (L74, L82)
      --> 필터는 언제나 합성 핸들러 하나만 들고 있다
```

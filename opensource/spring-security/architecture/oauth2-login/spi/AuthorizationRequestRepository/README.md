# AuthorizationRequestRepository

상위: [spi](../README.md)

나가는 요청과 돌아오는 콜백을 잇는다. 이 계약이 없으면 콜백의 짝을 맞출 수 없다.

## 위치

`oauth2/oauth2-client` / `org.springframework.security.oauth2.client.web` / `AuthorizationRequestRepository.java` L41-L71 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/oauth2/oauth2-client/src/main/java/org/springframework/security/oauth2/client/web/AuthorizationRequestRepository.java#L41-L71))

## 실제 코드

```java
// AuthorizationRequestRepository.java L41-L71 (javadoc 생략)
public interface AuthorizationRequestRepository<T extends OAuth2AuthorizationRequest> {

    @Nullable T loadAuthorizationRequest(HttpServletRequest request);

    void saveAuthorizationRequest(T authorizationRequest, HttpServletRequest request, HttpServletResponse response);

    @Nullable T removeAuthorizationRequest(HttpServletRequest request, HttpServletResponse response);

}
```

## 흐름에서 불리는 자리

```text
 OAuth2AuthorizationRequestRedirectFilter.sendRedirectForAuthorization
   L234 saveAuthorizationRequest(...)   리다이렉트 직전에 저장

 OAuth2LoginAuthenticationFilter.attemptAuthentication
   L174 removeAuthorizationRequest(...)  콜백에서 꺼내며 지운다
```

- [OAuth2AuthorizationRequestRedirectFilter.doFilterInternal](../../01_OAuth2AuthorizationRequestRedirectFilter.doFilterInternal/README.md)
- [OAuth2LoginAuthenticationFilter.attemptAuthentication](../../02_OAuth2LoginAuthenticationFilter.attemptAuthentication/README.md)

## 구현 계층

```text
 AuthorizationRequestRepository<T>
   +-- HttpSessionOAuth2AuthorizationRequestRepository   세션에 담는다
   +-- (사용자 구현 -- 쿠키에 담는 구현을 직접 만들기도 한다)
```

## 결과가 쓰이는 곳

```text
 메서드가 셋인 이유
      --> load 는 지우지 않고 보기만 한다
      --> remove 는 꺼내면서 지운다. OAuth2 로그인 흐름이 쓰는 것은 이쪽이다
      --> load 는 OAuth2AuthorizationCodeGrantFilter 가 응답 매칭 판정에 쓴다
      --> save 는 리다이렉트 직전에 부른다

 세션에 담는다는 점
      --> 기본 구현이 그렇다
      --> 기본 구현을 그대로 쓰면 OAuth2 로그인이 세션에 기대게 된다
      --> 교체 지점은 열려 있다. 두 필터의 세터와 DSL 로 갈아 끼운다

 제네릭 T
      --> OAuth2AuthorizationRequest 의 하위 타입으로 좁힐 수 있다
      --> 저장할 것을 확장하고 싶을 때 쓰는 여지다
```

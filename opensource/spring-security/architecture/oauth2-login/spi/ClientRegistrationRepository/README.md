# ClientRegistrationRepository

상위: [spi](../README.md)

`registrationId` 로 클라이언트 설정을 찾는다. 메서드 하나뿐이다.

## 위치

`oauth2/oauth2-client` / `org.springframework.security.oauth2.client.registration` / `ClientRegistrationRepository.java` L34-L44 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/oauth2/oauth2-client/src/main/java/org/springframework/security/oauth2/client/registration/ClientRegistrationRepository.java#L34-L44))

## 실제 코드

```java
// ClientRegistrationRepository.java L34-L44 (javadoc 생략)
public interface ClientRegistrationRepository {

    @Nullable ClientRegistration findByRegistrationId(String registrationId);

}
```

## 흐름에서 불리는 자리

```text
 OAuth2LoginAuthenticationFilter.attemptAuthentication
   L182 clientRegistrationRepository.findByRegistrationId(registrationId)
   없으면 client_registration_not_found 로 거부한다
```

- [OAuth2LoginAuthenticationFilter.attemptAuthentication](../../02_OAuth2LoginAuthenticationFilter.attemptAuthentication/README.md)

## 구현 계층

```text
 ClientRegistrationRepository
   +-- InMemoryClientRegistrationRepository   설정을 메모리에 들고 있다
   |     스프링 부트가 프로퍼티로 만들어 주는 것이 이것이다
   +-- SupplierClientRegistrationRepository   다른 저장소를 지연 생성해 감싼다
   +-- (사용자 구현 -- DB 에 두려면 이쪽)
```

## 결과가 쓰이는 곳

```text
 ClientRegistration
      --> 클라이언트 ID, 시크릿, 인가/토큰 엔드포인트, 스코프를 담는다
      --> 두 필터가 같은 registrationId 로 같은 설정을 찾는다

 @Nullable 반환
      --> 없으면 null 이다. 예외를 던지지 않는다
      --> 거부로 바꾸는 것은 호출부의 몫이다

 메서드가 하나뿐인 점
      --> 조회만 계약에 있다. 등록이나 수정은 없다
      --> 설정을 어디에 두는지는 구현이 정한다
```

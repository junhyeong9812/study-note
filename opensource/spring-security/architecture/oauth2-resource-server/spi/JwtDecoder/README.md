# JwtDecoder

상위: [spi](../README.md)

메서드 하나짜리 함수형 인터페이스다. 문자열을 `Jwt` 로 바꾸는 일 전체를 맡는다.

## 위치

`oauth2/oauth2-jose` / `org.springframework.security.oauth2.jwt` / `JwtDecoder.java` L43-L55 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/oauth2/oauth2-jose/src/main/java/org/springframework/security/oauth2/jwt/JwtDecoder.java#L43-L55))

## 실제 코드

```java
// JwtDecoder.java L43-L55 (javadoc 생략)
@FunctionalInterface
public interface JwtDecoder {

    Jwt decode(String token) throws JwtException;

}
```

## 흐름에서 불리는 자리

```text
 JwtAuthenticationProvider.getJwt
   L100 jwtDecoder.decode(bearer.getToken())
```

- [NimbusJwtDecoder.decode](../../02_JwtAuthenticationProvider.authenticate/01_NimbusJwtDecoder.decode/README.md)

## 구현 계층

```text
 JwtDecoder (@FunctionalInterface)
   +-- NimbusJwtDecoder    기본. Nimbus 라이브러리로 파싱과 서명 검증
   +-- SupplierJwtDecoder  다른 디코더를 지연 생성해 감싼다

 main 소스의 구현은 이 둘뿐이다
 OIDC, DPoP, 클라이언트 단언용 팩토리가 따로 있지만
 그것들도 결국 NimbusJwtDecoder 를 조립해 돌려준다
```

## 결과가 쓰이는 곳

```text
 반환한 Jwt
      --> 헤더와 클레임을 그대로 들고 있다
      --> 변환기가 여기서 권한을 뽑아 Authentication 을 만든다

 던지는 JwtException
      --> 인터페이스가 선언한 실패 타입이다
      --> 하위 타입(BadJwtException, JwtValidationException)으로
          원인을 구분한다
      --> 다만 SupplierJwtDecoder 는 초기화 실패 시
          JwtDecoderInitializationException 을 던지는데
          이것은 JwtException 계열이 아니다

 메서드가 하나뿐인 점
      --> 파싱, 서명 검증, 클레임 검증이 전부 이 안에 들어 있다
      --> 호출부는 단계를 알 필요가 없다

 SupplierJwtDecoder
      --> 발급자 정보를 기동 시점에 가져오지 못할 때 쓴다
      --> 첫 호출까지 실제 디코더 생성을 미룬다
```

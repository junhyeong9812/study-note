# OAuth2TokenValidator

상위: [spi](../README.md)

서명이 맞는 토큰의 **내용**을 본다. 디코더 안에서 마지막 단계로 불린다.

## 위치

`oauth2/oauth2-core` / `org.springframework.security.oauth2.core` / `OAuth2TokenValidator.java` L27-L37 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/oauth2/oauth2-core/src/main/java/org/springframework/security/oauth2/core/OAuth2TokenValidator.java#L27-L37))

## 실제 코드

```java
// OAuth2TokenValidator.java L27-L37 (javadoc 생략)
@FunctionalInterface
public interface OAuth2TokenValidator<T extends OAuth2Token> {

    OAuth2TokenValidatorResult validate(T token);

}
```

## 흐름에서 불리는 자리

```text
 NimbusJwtDecoder.validateJwt
   L196 jwtValidator.validate(jwt)
   L197 결과에 오류가 있으면 JwtValidationException
```

- [NimbusJwtDecoder.decode](../../02_JwtAuthenticationProvider.authenticate/01_NimbusJwtDecoder.decode/README.md)

## 구현 계층

```text
 OAuth2TokenValidator<T> (@FunctionalInterface)
   +-- JwtTimestampValidator   만료(exp)와 사용 시작 시각(nbf)
   +-- JwtIssuerValidator      발급자(iss)
   +-- JwtAudienceValidator    대상(aud)
   +-- JwtClaimValidator       임의 클레임에 조건을 건다
   +-- JwtTypeValidator        typ 헤더
   +-- X509CertificateThumbprintValidator  인증서 지문
   +-- JwtIssuedAtValidator    발급 시각(iat)
   +-- DelegatingOAuth2TokenValidator  여럿을 묶는다
   +-- (OIDC, DPoP 전용 구현들)

 JwtValidators.createDefault() 가 만드는 기본 조합은 셋이다
   JwtTypeValidator + JwtTimestampValidator + X509CertificateThumbprintValidator

 JwtIssuerValidator 는 기본에 없다
 issuer-uri 를 준 경우 createDefaultWithIssuer 가 더한다
```

```text
 예외가 아니라 결과를 돌려준다

 validate 는 OAuth2TokenValidatorResult 를 돌려준다
 오류가 있으면 그 안에 담아 준다

 여러 검증기를 묶어 돌릴 때
 첫 실패에서 멈추지 않고 오류를 모을 수 있는 구조다

 예외로 바꾸는 것은 호출부(NimbusJwtDecoder L197-201)의 몫이다
```

## 결과가 쓰이는 곳

```text
 OAuth2TokenValidatorResult
      --> hasErrors() 로 성패를 가른다
      --> getErrors() 에 OAuth2Error 목록이 담긴다

 제네릭 T extends OAuth2Token
      --> 타입은 열려 있지만 main 의 구현은 전부 <Jwt> 다
      --> 불투명 토큰 경로는 이 계약을 쓰지 않는다

 디코더가 들고 있다는 점
      --> 검증기를 바꾸려면 디코더를 만들 때 설정한다
      --> 그래서 "서명 검증"과 "내용 검증"이 한 호출로 묶여 보인다
```

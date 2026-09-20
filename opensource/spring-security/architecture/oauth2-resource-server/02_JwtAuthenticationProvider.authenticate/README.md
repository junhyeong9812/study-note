# JwtAuthenticationProvider.authenticate

상위: [OAuth2 리소스 서버](../README.md)

디코더에 검증을 맡기고, 결과를 권한이 담긴 토큰으로 바꾼다. [폼 로그인](../../form-login/README.md)의 `DaoAuthenticationProvider` 자리에 해당한다.

## 위치

`oauth2/oauth2-resource-server` / `org.springframework.security.oauth2.server.resource.authentication` / `JwtAuthenticationProvider.java` L85-L96 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/oauth2/oauth2-resource-server/src/main/java/org/springframework/security/oauth2/server/resource/authentication/JwtAuthenticationProvider.java#L85-L96))

## 실제 코드

```java
// JwtAuthenticationProvider.java L85-L96
@Override
public Authentication authenticate(Authentication authentication) throws AuthenticationException {
    BearerTokenAuthenticationToken bearer = (BearerTokenAuthenticationToken) authentication;
    Jwt jwt = getJwt(bearer);
    AbstractAuthenticationToken token = this.jwtAuthenticationConverter.convert(jwt);
    Assert.notNull(token, "token cannot be null");
    if (token.getDetails() == null) {
        token.setDetails(bearer.getDetails());
    }
    this.logger.debug("Authenticated token");
    return token;
}
```

디코딩 실패를 예외로 번역하는 부분이 바로 아래 있다.

`oauth2/oauth2-resource-server` / `org.springframework.security.oauth2.server.resource.authentication` / `JwtAuthenticationProvider.java` L98-L116 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/oauth2/oauth2-resource-server/src/main/java/org/springframework/security/oauth2/server/resource/authentication/JwtAuthenticationProvider.java#L98-L116))

```java
// JwtAuthenticationProvider.java L98-L116
private Jwt getJwt(BearerTokenAuthenticationToken bearer) {
    try {
        return this.jwtDecoder.decode(bearer.getToken());
    }
    catch (BadJwtException failed) {
        this.logger.debug("Failed to authenticate since the JWT was invalid");
        throw new InvalidBearerTokenException((failed.getMessage() != null) ? failed.getMessage() : "Invalid token",
                failed);
    }
    catch (JwtException failed) {
        throw new AuthenticationServiceException(
                (failed.getMessage() != null) ? failed.getMessage() : "Invalid token", failed);
    }
}

@Override
public boolean supports(Class<?> authentication) {
    return BearerTokenAuthenticationToken.class.isAssignableFrom(authentication);
}
```

## 동작 흐름

```text
 authenticate(authentication)
 |
 | L87 BearerTokenAuthenticationToken 으로 캐스팅한다
 | L88 getJwt(bearer)
 |      |
 |      +-- L100 jwtDecoder.decode(bearer.getToken())
 |      |
 |      +-- L102 BadJwtException 이면
 |      |      L104 InvalidBearerTokenException 으로 바꿔 던진다
 |      |
 |      +-- L107 그 밖의 JwtException 이면
 |             L108 AuthenticationServiceException 으로 바꿔 던진다
 |
 | L89 jwtAuthenticationConverter.convert(jwt)
 |      Jwt 를 권한이 담긴 토큰으로 바꾼다
 |
 +-- L91 결과에 details 가 없으면 L92 원래 토큰의 것을 옮긴다
 +-- L95 반환
```

```text
 예외를 두 갈래로 번역한다

 BadJwtException      토큰이 잘못됐다 (형식, 서명, 만료)
   -> InvalidBearerTokenException
      AuthenticationException 계열이다. 401 로 이어진다

 그 밖의 JwtException  시스템 문제 (JWK 세트를 못 가져옴 등)
   -> AuthenticationServiceException

 "토큰이 틀렸다"와 "우리 쪽 문제다"를 가른다

 다만 그 구분이 실제로 갈리는 곳은 ProviderManager 가 아니다
 ProviderManager 는 InternalAuthenticationServiceException 만 즉시 던지고
 평범한 AuthenticationServiceException 은 보관했다가 마지막에 던진다

 갈라지는 자리는 필터의 기본 실패 핸들러인
 AuthenticationEntryPointFailureHandler 다 (L54-58)
 AuthenticationServiceException 이면 다시 던져 컨테이너로 올리고(500),
 아니면 진입점으로 보낸다(401)
```

```text
 사용자 조회가 없다

 폼 로그인   UserDetailsService 로 DB 를 친다
 리소스 서버 토큰 안의 클레임이 곧 사용자 정보다

 그래서 이 프로바이더에는 UserDetailsService 가 없다
 필드는 jwtDecoder 와 jwtAuthenticationConverter 둘뿐이다
```

```text
 details 를 옮기는 조건이 있다 (L91-93)

 변환기가 만든 토큰에 details 가 없을 때만 옮긴다
 변환기가 스스로 채웠으면 건드리지 않는다

 ProviderManager 의 copyDetails 도 같은 조건을 쓴다
```

## 결과가 쓰이는 곳

```text
 반환한 토큰
      --> 보통 JwtAuthenticationToken 이다
      --> principal 이 Jwt 객체라 클레임에 그대로 접근할 수 있다

 supports (L113-116)
      --> BearerTokenAuthenticationToken 만 받는다
      --> 다른 토큰 타입은 건너뛴다. ProviderManager 가 그렇게 거른다

 jwtAuthenticationConverter
      --> Jwt 를 Authentication 으로 바꾸는 자리다
      --> 권한을 어떤 클레임에서 뽑을지가 여기서 정해진다
```

## 하위 메서드

- [01 NimbusJwtDecoder.decode](01_NimbusJwtDecoder.decode/README.md)

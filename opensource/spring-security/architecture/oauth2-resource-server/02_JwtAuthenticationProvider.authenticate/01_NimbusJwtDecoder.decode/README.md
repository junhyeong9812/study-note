# NimbusJwtDecoder.decode

상위: [JwtAuthenticationProvider.authenticate](../README.md)

JWT 문자열을 파싱하고, 서명을 확인하고, 클레임을 검증한다. 세 단계가 각각 다른 예외를 던진다.

## 위치

`oauth2/oauth2-jose` / `org.springframework.security.oauth2.jwt` / `NimbusJwtDecoder.java` L138-L147 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/oauth2/oauth2-jose/src/main/java/org/springframework/security/oauth2/jwt/NimbusJwtDecoder.java#L138-L147))

## 실제 코드

```java
// NimbusJwtDecoder.java L138-L147
@Override
public Jwt decode(String token) throws JwtException {
    JWT jwt = parse(token);
    if (jwt instanceof PlainJWT) {
        this.logger.trace("Failed to decode unsigned token");
        throw new BadJwtException("Unsupported algorithm of " + jwt.getHeader().getAlgorithm());
    }
    Jwt createdJwt = createJwt(token, jwt);
    return validateJwt(createdJwt);
}
```

세 단계가 각각 private 메서드로 나뉘어 있다.

`oauth2/oauth2-jose` / `org.springframework.security.oauth2.jwt` / `NimbusJwtDecoder.java` L149-L160 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/oauth2/oauth2-jose/src/main/java/org/springframework/security/oauth2/jwt/NimbusJwtDecoder.java#L149-L160))

```java
// NimbusJwtDecoder.java L149-L160
private JWT parse(String token) {
    try {
        return JWTParser.parse(token);
    }
    catch (Exception ex) {
        this.logger.trace("Failed to parse token", ex);
        if (ex instanceof ParseException) {
            throw new BadJwtException(String.format(DECODING_ERROR_MESSAGE_TEMPLATE, "Malformed token"), ex);
        }
        throw new BadJwtException(String.format(DECODING_ERROR_MESSAGE_TEMPLATE, ex.getMessage()), ex);
    }
}
```

`oauth2/oauth2-jose` / `org.springframework.security.oauth2.jwt` / `NimbusJwtDecoder.java` L195-L203 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/oauth2/oauth2-jose/src/main/java/org/springframework/security/oauth2/jwt/NimbusJwtDecoder.java#L195-L203))

```java
// NimbusJwtDecoder.java L195-L203
private Jwt validateJwt(Jwt jwt) {
    OAuth2TokenValidatorResult result = this.jwtValidator.validate(jwt);
    if (result.hasErrors()) {
        Collection<OAuth2Error> errors = result.getErrors();
        String validationErrorString = getJwtValidationExceptionMessage(errors);
        throw new JwtValidationException(validationErrorString, errors);
    }
    return jwt;
}
```

## 동작 흐름

```text
 decode(token)
 |
 | L140 parse(token)
 |      L151 JWTParser.parse(token)
 |      L155 ParseException 이면 "Malformed token"
 |      L158 그 밖의 예외도 BadJwtException
 |
 +-- L141 결과가 PlainJWT 이면 (서명이 없는 토큰)
 |      L143 BadJwtException -- 서명 없는 토큰은 받지 않는다
 |
 | L145 createJwt(token, jwt)
 |      L165 jwtProcessor.process(parsedJwt, null)   서명 검증이 여기다
 |            키를 어디서 얻을지(JWK 세트 URI, 공개키, 대칭키)가
 |            이 처리기에 설정돼 있다
 |      L167 클레임을 변환한다
 |      L169-172 Jwt 객체로 만든다
 |
 +-- L146 validateJwt(createdJwt)
        L196 jwtValidator.validate(jwt)
        L197 오류가 있으면 L200 JwtValidationException
```

```text
 세 단계가 서로 다른 것을 본다

 parse        문자열이 JWT 구조인가
 createJwt    서명이 맞는가 (jwtProcessor 가 설정된 키로 검증한다)
 validateJwt  내용이 유효한가 (만료, 발급자 등)

 앞의 둘이 통과해도 셋째에서 떨어질 수 있다
 서명은 맞는데 만료된 토큰이 그런 경우다
```

```text
 PlainJWT 를 따로 막는다 (L141-144)

 파싱은 성공하지만 서명이 없는 토큰이 PlainJWT 다
 파싱 직후에 타입으로 걸러 BadJwtException 을 던진다
 메시지는 "Unsupported algorithm of ..." 이고
 로그는 "Failed to decode unsigned token" 이다
```

```text
 예외 타입이 갈리는 지점

 createJwt 의 catch 매핑 (L175-192)
   RemoteKeySourceException  -> JwtException
   JOSEException             -> JwtException
   그 밖의 Exception          -> BadJwtException

 parse 의 실패도 BadJwtException 이다 (L156, L158)
 JwtValidationException 은 BadJwtException 계열이다

 이 구분이 위층에서 401 과 500 을 가르는 입력이 된다
 실제로 가르는 곳은 프로바이더가 아니라 실패 핸들러다
```

## 결과가 쓰이는 곳

```text
 돌려준 Jwt
      --> 헤더와 클레임을 맵으로 들고 있다
      --> 변환기가 여기서 권한을 뽑는다
      --> 최종적으로 Authentication 의 principal 이 된다

 jwtProcessor
      --> Nimbus 라이브러리의 처리기다
      --> 키를 어디서 얻을지가 이 안에 설정돼 있다
          JWK 세트 URI, 공개키, 대칭키 중 무엇으로 만들었느냐에 달렸다

 jwtValidator
      --> OAuth2TokenValidator 다
      --> 기본 조합은 typ, 만료(exp)와 nbf, 인증서 지문 셋이다
          발급자 검증은 issuer-uri 로 만들 때만 더해진다
      --> 추가 검증을 끼우려면 이 자리를 바꾼다

 세 단계를 나눈 구조
      --> 예외 타입만으로는 단계가 갈리지 않는다
          BadJwtException 은 parse 와 createJwt 양쪽에서 나온다
      --> 메시지가 단계를 알려 준다
          Malformed token / Malformed payload / Malformed Jwk set
```

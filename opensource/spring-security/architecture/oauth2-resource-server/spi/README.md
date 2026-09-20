# spi

상위: [OAuth2 리소스 서버](../README.md)

이 흐름이 기대는 계약 둘이다. 인증 매니저와 프로바이더 계약은 [폼 로그인](../../form-login/spi/README.md)과 공유하므로 여기서는 다루지 않는다.

```text
 토큰을 푸는 쪽
   JwtDecoder          문자열을 Jwt 로. 파싱, 서명 검증, 클레임 검증을 모두 품는다

 내용을 보는 쪽
   OAuth2TokenValidator  typ, 만료 같은 클레임을 검증한다
                         디코더 안에서 마지막 단계로 불린다
```

- [JwtDecoder](JwtDecoder/README.md)
- [OAuth2TokenValidator](OAuth2TokenValidator/README.md)

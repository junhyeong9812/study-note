# spi

상위: [CSRF 방어](../README.md)

토큰을 어디에 두고, 어떻게 내보내고 받을지를 가르는 계약 셋이다.

```text
 토큰을 보관하는 쪽
   CsrfTokenRepository    생성, 저장, 조회. 기본은 세션

 토큰을 주고받는 쪽
   CsrfTokenRequestHandler  요청 속성에 노출하고 요청에서 꺼낸다

 토큰 자체
   CsrfToken              헤더 이름, 파라미터 이름, 값
```

- [CsrfTokenRepository](CsrfTokenRepository/README.md)
- [CsrfTokenRequestHandler](CsrfTokenRequestHandler/README.md)
- [CsrfToken](CsrfToken/README.md)

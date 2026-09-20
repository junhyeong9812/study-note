# spi

상위: [OAuth2 로그인](../README.md)

두 필터 사이를 잇는 계약 둘이다. 인증 매니저 계약은 [폼 로그인](../../form-login/spi/README.md)과 공유한다.

```text
 어느 인가 서버인가
   ClientRegistrationRepository   registrationId 로 클라이언트 설정을 찾는다

 두 요청 사이를 잇는 것
   AuthorizationRequestRepository  나갈 때 저장하고 돌아올 때 꺼낸다
                                   이것이 있어야 콜백의 짝을 맞출 수 있다
```

- [ClientRegistrationRepository](ClientRegistrationRepository/README.md)
- [AuthorizationRequestRepository](AuthorizationRequestRepository/README.md)

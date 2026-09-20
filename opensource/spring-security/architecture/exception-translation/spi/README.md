# spi

상위: [예외 변환](../README.md)

거부를 응답으로 바꾸는 계약 셋이다. 어느 쪽으로 갈지는 신뢰 해석기가 정한다.

```text
 갈림길을 정하는 것
   AuthenticationTrustResolver  익명인가, 쿠키로만 들어왔는가, 완전 인증인가

 각 갈래의 출구
   AuthenticationEntryPoint  인증을 시작시킨다 (로그인 페이지, 401)
   AccessDeniedHandler       이미 인증된 사용자를 막는다 (403)
```

- [AuthenticationEntryPoint](AuthenticationEntryPoint/README.md)
- [AccessDeniedHandler](AccessDeniedHandler/README.md)
- [AuthenticationTrustResolver](AuthenticationTrustResolver/README.md)

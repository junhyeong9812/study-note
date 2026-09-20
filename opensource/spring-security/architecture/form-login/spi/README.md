# spi

상위: [폼 로그인](../README.md)

인증 경로가 기대는 계약 넷이다. 위에서 아래로 갈수록 좁은 일을 맡는다.

```text
 AuthenticationManager   인증해 달라는 요청을 받는 입구. 메서드 하나
   +-- AuthenticationProvider  인증 방식 하나를 안다. supports 로 자기 몫을 고른다
         +-- UserDetailsService  사용자를 어디서 가져올지만 안다
         +-- PasswordEncoder     비밀번호를 해시하고 대조한다

 이 분리 덕분에 저장소를 바꿔도 위쪽은 그대로다
```

- [AuthenticationManager](AuthenticationManager/README.md)
- [AuthenticationProvider](AuthenticationProvider/README.md)
- [UserDetailsService](UserDetailsService/README.md)
- [PasswordEncoder](PasswordEncoder/README.md)

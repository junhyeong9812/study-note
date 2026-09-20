# spi

상위: [로그아웃](../README.md)

로그아웃이 기대는 계약 둘이다. 하는 일과 끝내는 일이 나뉘어 있다.

```text
 정리하는 쪽
   LogoutHandler         무언가를 지운다. 여럿이 줄지어 실행된다
                         응답 본문이나 리다이렉트는 만들지 않는다
                         (헤더나 쿠키를 쓰는 구현은 있다)

 끝내는 쪽
   LogoutSuccessHandler  응답을 쓴다. 하나뿐이고 마지막에 불린다
```

- [LogoutHandler](LogoutHandler/README.md)
- [LogoutSuccessHandler](LogoutSuccessHandler/README.md)

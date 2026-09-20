# spi

상위: [메서드 보안](../README.md)

메서드 보안이 기대는 계약 둘이다. 인가 계약(`AuthorizationManager`, `AuthorizationResult`)은 [인가](../../authorization/spi/README.md) 흐름과 공유하므로 여기서는 다루지 않는다.

```text
 프록시에 붙는 쪽
   AuthorizationAdvisor   어드바이저이자 인터셉터. 네 계약을 한꺼번에 상속한다

 거부됐을 때
   MethodAuthorizationDeniedHandler  예외를 던질지, 다른 값을 돌려줄지 정한다
```

- [AuthorizationAdvisor](AuthorizationAdvisor/README.md)
- [MethodAuthorizationDeniedHandler](MethodAuthorizationDeniedHandler/README.md)

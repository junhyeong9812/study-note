# spi

상위: [인가](../README.md)

인가 판정이 기대는 계약 셋이다.

```text
 판정하는 쪽
   AuthorizationManager   "이 주체가 이 대상에 접근해도 되는가"
                          웹 요청과 메서드 호출이 같은 계약을 쓴다

 판정 결과
   AuthorizationResult    isGranted() 하나. 구현이 이유를 덧붙일 수 있다

 대조 전에 끼어드는 것
   RoleHierarchy          상위 역할이 하위를 포함하도록 권한을 펼친다
```

- [AuthorizationManager](AuthorizationManager/README.md)
- [AuthorizationResult](AuthorizationResult/README.md)
- [RoleHierarchy](RoleHierarchy/README.md)

# spi

상위: [Spring AOP 프록시](../README.md)

프록시를 만들고 호출을 가로채는 과정에서 갈아 끼울 수 있는 인터페이스다. 네 가지가 각각 "무엇을 적용할까(Advisor)", "무엇을 할까(MethodInterceptor)", "누구에게 위임할까(TargetSource)", "어떻게 감쌀까(AopProxy)"를 맡는다.

```text
 프록시 생성
   findEligibleAdvisors ......... Advisor (+ Pointcut, MethodMatcher)
   buildProxy ................... TargetSource
     createAopProxy ............. AopProxy
 호출
   getInterceptors... ........... Advisor 의 포인트컷 재평가
   proceed ...................... MethodInterceptor (= Advice)
```

## 하위 인터페이스

- [Advisor](Advisor/README.md)
- [MethodInterceptor](MethodInterceptor/README.md)
- [TargetSource](TargetSource/README.md)
- [AopProxy](AopProxy/README.md)

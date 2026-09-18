# spi

상위: [Spring 트랜잭션](../README.md)

트랜잭션 추상화를 이루는 인터페이스들이다. 다섯이 각각 "무엇을 읽어(TransactionAttributeSource)", "어떻게 열지 정하고(TransactionDefinition)", "누가 여닫으며(PlatformTransactionManager)", "지금 상태는 무엇이고(TransactionStatus)", "경계에 맞춰 무엇을 더 할지(TransactionSynchronization)"를 맡는다.

```text
 TransactionInterceptor.invoke
   getTransactionAttribute ....... TransactionAttributeSource --> TransactionDefinition
   getTransaction ................ PlatformTransactionManager --> TransactionStatus
   proceed (타깃 실행)
   commit / rollback ............. PlatformTransactionManager
        내부에서 ................. TransactionSynchronization 콜백
```

## 하위 인터페이스

- [PlatformTransactionManager](PlatformTransactionManager/README.md)
- [TransactionDefinition](TransactionDefinition/README.md)
- [TransactionStatus](TransactionStatus/README.md)
- [TransactionSynchronization](TransactionSynchronization/README.md)
- [TransactionAttributeSource](TransactionAttributeSource/README.md)

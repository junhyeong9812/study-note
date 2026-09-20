# spi

상위: [보안 컨텍스트](../README.md)

컨텍스트를 어디에 보관하고 어떻게 꺼낼지를 가르는 계약들이다.

```text
 요청을 넘어 보관하는 쪽
   SecurityContextRepository   세션이나 요청 속성에 읽고 쓴다

 요청 안에서 들고 있는 쪽
   SecurityContextHolderStrategy  ThreadLocal 등 보관 방식을 정한다

 둘을 잇는 것
   DeferredSecurityContext     아직 읽지 않은 컨텍스트를 나타낸다
```

- [SecurityContextRepository](SecurityContextRepository/README.md)
- [SecurityContextHolderStrategy](SecurityContextHolderStrategy/README.md)
- [DeferredSecurityContext](DeferredSecurityContext/README.md)

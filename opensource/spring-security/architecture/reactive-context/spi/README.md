# spi

상위: [리액티브 컨텍스트](../README.md)

이 흐름이 기대는 계약은 하나다. 서블릿 판의 `SecurityContextRepository` 에 대응한다.

```text
 요청을 넘어 보관하는 쪽
   ServerSecurityContextRepository   load 와 save 둘. 둘 다 Mono 를 돌려준다

 보관 전략을 정하는 쪽
   서블릿 판의 SecurityContextHolderStrategy 에 해당하는 타입이 없다
   ReactiveSecurityContextHolder 가 final 유틸 클래스이고
   키도 private static final 이라 교체 지점 자체가 없다
```

- [ServerSecurityContextRepository](ServerSecurityContextRepository/README.md)

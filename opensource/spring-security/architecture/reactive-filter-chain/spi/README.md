# spi

상위: [리액티브 필터 체인](../README.md)

서블릿 판의 계약들과 하나씩 대응한다.

```text
 체인을 고르고 태우는 길
   SecurityWebFilterChain   이 요청에 맞는가, 어떤 필터를 태울 것인가
   WebFilterChainDecorator  고른 필터들을 실제 WebFilterChain 으로 만든다

 요청이 들어오는 길
   ServerWebExchangeFirewall  exchange 를 감싸 이상한 요청을 막는다
```

- [SecurityWebFilterChain](SecurityWebFilterChain/README.md)
- [WebFilterChainDecorator](WebFilterChainDecorator/README.md)
- [ServerWebExchangeFirewall](ServerWebExchangeFirewall/README.md)

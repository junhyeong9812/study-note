# spi

상위: [필터 체인](../README.md)

필터 체인 흐름이 기대는 계약들이다. 요청을 받아 체인을 고르고, 그 체인을 실제 `FilterChain` 으로 만들어 태우기까지 네 개가 관여한다.

```text
 요청이 들어오는 길
   HttpFirewall            요청과 응답을 감싸 이상한 경로를 막는다
   RequestRejectedHandler  방화벽이 거부했을 때의 응답을 정한다

 체인을 고르고 태우는 길
   SecurityFilterChain     이 요청에 맞는가, 그리고 어떤 필터를 태울 것인가
   FilterChainDecorator    고른 필터들을 실제 FilterChain 으로 만든다
```

- [SecurityFilterChain](SecurityFilterChain/README.md)
- [FilterChainDecorator](FilterChainDecorator/README.md)
- [HttpFirewall](HttpFirewall/README.md)
- [RequestRejectedHandler](RequestRejectedHandler/README.md)

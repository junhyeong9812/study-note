# spi

상위: [필터 등록](../README.md)

등록 과정에 끼어드는 계약 중 이 폴더에서 다루는 둘이다. 방화벽과 체인 데코레이터 등도 같은 자리에서 갈아 끼운다.

```text
 build 직전에 끼어드는 것
   WebSecurityCustomizer   WebSecurity 를 직접 만진다. ignoring() 을 거는 자리

 build 도중(performBuild 끝자락)에 검사하는 것
   FilterChainValidator    완성된 FilterChainProxy 를 기동 시점에 검증한다
```

- [WebSecurityCustomizer](WebSecurityCustomizer/README.md)
- [FilterChainValidator](FilterChainValidator/README.md)

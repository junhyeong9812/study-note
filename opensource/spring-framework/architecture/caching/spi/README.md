# spi

상위: [Spring 캐시 추상화](../README.md)

캐시 추상화를 이루는 인터페이스다. 어떤 저장소를 쓸지(Cache, CacheManager), 어디에 적용할지(CacheOperationSource), 무엇을 키로 삼을지(KeyGenerator), 실패하면 어떻게 할지(CacheErrorHandler)를 각각 맡는다.

```text
 CacheInterceptor.invoke
   getCacheOperations ....... CacheOperationSource
   캐시 목록 결정 ........... CacheResolver --> CacheManager --> Cache
   키 생성 .................. KeyGenerator (또는 key SpEL)
   get / put / evict ........ Cache
   실패 처리 ................ CacheErrorHandler
```

## 하위 인터페이스

- [Cache](Cache/README.md)
- [CacheManager](CacheManager/README.md)
- [CacheOperationSource](CacheOperationSource/README.md)
- [KeyGenerator](KeyGenerator/README.md)
- [CacheErrorHandler](CacheErrorHandler/README.md)

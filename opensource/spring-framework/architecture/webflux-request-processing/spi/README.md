# spi

상위: [Spring WebFlux 요청 처리](../README.md)

리액티브 요청 처리에서 구현을 갈아 끼우는 자리다. MVC의 같은 이름 인터페이스와 역할은 같지만 반환 타입이 모두 `Mono`라는 점이 다르다.

```text
 HttpWebHandlerAdapter ....... WebHandler (+ WebFilter, WebExceptionHandler)
   DispatcherHandler
     getHandler ............... HandlerMapping
     handle ................... HandlerAdapter
     handleResult ............. HandlerResultHandler
                                  +-- 본문 쓰기: HttpMessageWriter
```

## 하위 인터페이스

- [WebHandler](WebHandler/README.md)
- [HandlerMapping](HandlerMapping/README.md)
- [HandlerAdapter](HandlerAdapter/README.md)
- [HandlerResultHandler](HandlerResultHandler/README.md)
- [HttpMessageWriter](HttpMessageWriter/README.md)

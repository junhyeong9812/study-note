# spi

상위: [Spring MVC 요청 처리](../README.md)

요청 처리 흐름에서 구현을 갈아 끼울 수 있는 자리의 인터페이스다. `DispatcherServlet`과 어댑터는 이 인터페이스들의 목록을 앞에서부터 물어 첫 번째로 답한 구현을 쓴다. 그래서 MVC를 확장한다는 것은 거의 언제나 이 중 하나의 구현을 추가한다는 뜻이다.

```text
 doDispatch
   +-- getHandler ................ HandlerMapping
   +-- applyPreHandle ............ HandlerInterceptor
   +-- getHandlerAdapter ......... HandlerAdapter
   |     +-- getMethodArgumentValues ... HandlerMethodArgumentResolver
   |     |                                 +-- (@RequestBody) HttpMessageConverter
   |     +-- handleReturnValue ......... HandlerMethodReturnValueHandler
   |                                       +-- (@ResponseBody) HttpMessageConverter
   +-- processHandlerException ... HandlerExceptionResolver
   +-- render .................... ViewResolver / View
```

## 하위 인터페이스

- [HandlerMapping](HandlerMapping/README.md)
- [HandlerInterceptor](HandlerInterceptor/README.md)
- [HandlerAdapter](HandlerAdapter/README.md)
- [HandlerMethodArgumentResolver](HandlerMethodArgumentResolver/README.md)
- [HandlerMethodReturnValueHandler](HandlerMethodReturnValueHandler/README.md)
- [HttpMessageConverter](HttpMessageConverter/README.md)
- [HandlerExceptionResolver](HandlerExceptionResolver/README.md)
- [ViewResolver](ViewResolver/README.md)

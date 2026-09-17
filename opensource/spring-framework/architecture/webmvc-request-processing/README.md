# Spring MVC 요청 처리

HTTP 요청 하나가 `DispatcherServlet`에 들어와 응답이 나가기까지의 호출 흐름을 위에서 아래로 따라간다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 흐름 중간에서 구현을 갈아 끼우는 인터페이스 모음이다.

기준 커밋: spring-framework `main` [`c1d4a766929`](https://github.com/spring-projects/spring-framework/tree/c1d4a76692949bdcdebae4b98b104174e4b951cf) (2026-09-10). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 서블릿 컨테이너
      |
      v
 [01] FrameworkServlet.processRequest      스레드에 Locale/Request 바인딩
      |
      v
 [02] DispatcherServlet.doDispatch
      |
      +-- [02-01] checkMultipart            multipart면 요청 래핑
      |
      +-- [02-02] getHandler  ------------> HandlerMapping 목록 순회      (spi)
      |              |
      |              +-- AbstractHandlerMapping.getHandler
      |                     +-- lookupHandlerMethod    URL -> @RequestMapping 메서드
      |              = HandlerExecutionChain (핸들러 + 인터셉터들)
      |
      +-- [02-03] chain.applyPreHandle ----> HandlerInterceptor.preHandle  (spi)
      |
      +-- [02-04] getHandlerAdapter -------> HandlerAdapter.supports       (spi)
      |
      +-- [02-05] ha.handle
      |              +-- RequestMappingHandlerAdapter.invokeHandlerMethod
      |                     +-- ModelFactory.initModel          @ModelAttribute 먼저
      |                     +-- invokeAndHandle
      |                     |      +-- getMethodArgumentValues  --> ArgumentResolver  (spi)
      |                     |      +-- doInvoke                     컨트롤러 메서드 실행
      |                     |      +-- handleReturnValue        --> ReturnValueHandler (spi)
      |                     |             +-- writeWithMessageConverters --> HttpMessageConverter (spi)
      |                     +-- getModelAndView                 본문 썼으면 null
      |              = ModelAndView 또는 null
      |
      +-- chain.applyPostHandle              (역순)
      |
      +-- [02-06] processDispatchResult
                     +-- processHandlerException --> HandlerExceptionResolver (spi)
                     +-- render                  --> ViewResolver / View      (spi)
                     +-- chain.triggerAfterCompletion   (역순)
```

## 단계

1. [FrameworkServlet.processRequest](01_FrameworkServlet.processRequest/README.md)가 요청 문맥을 스레드에 걸고 `doService`를 거쳐 `doDispatch`를 부른다.
2. [DispatcherServlet.doDispatch](02_DispatcherServlet.doDispatch/README.md)가 핸들러 찾기, 인터셉터, 어댑터 호출, 결과 처리를 순서대로 조율한다. 요청 처리의 본체다.

## 기동할 때 준비되는 것

요청을 받기 전, 컨텍스트가 뜰 때 `initStrategies`가 SPI 구현 목록을 채운다. 호출 시점은 [컨테이너 기동](../container-refresh/README.md)의 마지막 단계가 발행하는 `ContextRefreshedEvent`를 `FrameworkServlet`이 받는 순간이다. 각 `init*`는 컨텍스트에서 빈을 찾고, 하나도 없을 때만 아래 기본값 파일을 쓴다.

`spring-webmvc` / `org.springframework.web.servlet` / `DispatcherServlet.java` L441-L450 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/DispatcherServlet.java#L441-L450))

```java
// DispatcherServlet.java L441-L450
protected void initStrategies(ApplicationContext context) {
    initMultipartResolver(context);
    initLocaleResolver(context);
    initHandlerMappings(context);
    initHandlerAdapters(context);
    initHandlerExceptionResolvers(context);
    initRequestToViewNameTranslator(context);
    initViewResolvers(context);
    initFlashMapManager(context);
}
```

```text
 initHandlerMappings(context)
      |
      +-- 컨텍스트에 HandlerMapping 빈이 있나?
      |      yes --> 전부 모아 @Order 순으로 정렬 --> this.handlerMappings
      |      no  --> getDefaultStrategies()  --> DispatcherServlet.properties 값
      |
      = 요청마다 getHandler()가 이 목록을 앞에서부터 순회
```

`spring-webmvc` / `org.springframework.web.servlet` / `DispatcherServlet.properties` L5-L25 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/resources/org/springframework/web/servlet/DispatcherServlet.properties#L5-L25))

```properties
// DispatcherServlet.properties L5-L25
org.springframework.web.servlet.LocaleResolver=org.springframework.web.servlet.i18n.AcceptHeaderLocaleResolver

org.springframework.web.servlet.HandlerMapping=org.springframework.web.servlet.handler.BeanNameUrlHandlerMapping,\
    org.springframework.web.servlet.mvc.method.annotation.RequestMappingHandlerMapping,\
    org.springframework.web.servlet.function.support.RouterFunctionMapping

org.springframework.web.servlet.HandlerAdapter=org.springframework.web.servlet.mvc.HttpRequestHandlerAdapter,\
    org.springframework.web.servlet.mvc.SimpleControllerHandlerAdapter,\
    org.springframework.web.servlet.mvc.method.annotation.RequestMappingHandlerAdapter,\
    org.springframework.web.servlet.function.support.HandlerFunctionAdapter


org.springframework.web.servlet.HandlerExceptionResolver=org.springframework.web.servlet.mvc.method.annotation.ExceptionHandlerExceptionResolver,\
    org.springframework.web.servlet.mvc.annotation.ResponseStatusExceptionResolver,\
    org.springframework.web.servlet.mvc.support.DefaultHandlerExceptionResolver

org.springframework.web.servlet.RequestToViewNameTranslator=org.springframework.web.servlet.view.DefaultRequestToViewNameTranslator

org.springframework.web.servlet.ViewResolver=org.springframework.web.servlet.view.InternalResourceViewResolver

org.springframework.web.servlet.FlashMapManager=org.springframework.web.servlet.support.SessionFlashMapManager
```

실무에서는 `@EnableWebMvc`나 Spring Boot가 이 빈들을 직접 등록하므로 기본값 파일은 "빈이 하나도 없을 때"의 정답이다. 목록 순서가 곧 질의 순서다.

## 이 흐름 위의 기여

- [#37008](../../prs/37008-mimetype-duplicate-parameters/) — [writeWithMessageConverters](02_DispatcherServlet.doDispatch/05_RequestMappingHandlerAdapter.invokeHandlerMethod/02_ServletInvocableHandlerMethod.invokeAndHandle/03_HandlerMethodReturnValueHandlerComposite.handleReturnValue/01_AbstractMessageConverterMethodProcessor.writeWithMessageConverters/README.md)가 파싱하는 `Accept` 헤더의 중복 파라미터 거부.
- [#37268](../../prs/37268-lru-cache-double-decrement/) — 같은 파싱 결과를 담는 `MimeTypeUtils` 캐시와 [processHandlerException](02_DispatcherServlet.doDispatch/06_DispatcherServlet.processDispatchResult/01_DispatcherServlet.processHandlerException/README.md) 경로의 `ExceptionHandlerMethodResolver` 캐시가 쓰는 `ConcurrentLruCache`의 이중 감산 수정.

## 다루지 않는 것

비동기 처리(`Callable`, `DeferredResult`)와 함수형 엔드포인트(`RouterFunction`)는 같은 뼈대 위의 갈래라 이 트리에서 뺐다. 코드에 분기가 보이는 자리에는 "비동기면 여기서 빠진다" 정도만 표시했다.

## 하위 메서드

- [01 FrameworkServlet.processRequest](01_FrameworkServlet.processRequest/README.md)
- [02 DispatcherServlet.doDispatch](02_DispatcherServlet.doDispatch/README.md)
- [spi](spi/README.md) — 흐름 중간의 인터페이스

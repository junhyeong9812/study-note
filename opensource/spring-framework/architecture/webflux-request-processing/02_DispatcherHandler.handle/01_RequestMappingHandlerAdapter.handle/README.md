# RequestMappingHandlerAdapter.handle (WebFlux)

상위: [DispatcherHandler.handle](../README.md)

`@RequestMapping` 메서드를 실행할 파이프라인을 조립한다. 모델 초기화, 인자 해석, 메서드 호출, 예외 복구가 하나의 `Mono<HandlerResult>`로 이어진다.

## 실제 코드

`spring-webflux` / `org.springframework.web.reactive.result.method.annotation` / `RequestMappingHandlerAdapter.java` L247-L250 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webflux/src/main/java/org/springframework/web/reactive/result/method/annotation/RequestMappingHandlerAdapter.java#L247-L250))

```java
// RequestMappingHandlerAdapter.java L247-L250
@Override
public boolean supports(Object handler) {
    return handler instanceof HandlerMethod;
}
```

`spring-webflux` / `org.springframework.web.reactive.result.method.annotation` / `RequestMappingHandlerAdapter.java` L252-L282 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webflux/src/main/java/org/springframework/web/reactive/result/method/annotation/RequestMappingHandlerAdapter.java#L252-L282))

```java
// RequestMappingHandlerAdapter.java L252-L282
@Override
public Mono<HandlerResult> handle(ServerWebExchange exchange, Object handler) {

    Assert.state(this.methodResolver != null &&
            this.modelInitializer != null && this.reactiveAdapterRegistry != null, "Not initialized");

    HandlerMethod handlerMethod = (HandlerMethod) handler;

    InitBinderBindingContext bindingContext = new InitBinderBindingContext(
            this.webBindingInitializer, this.methodResolver.getInitBinderMethods(handlerMethod),
            this.methodResolver.hasMethodValidator() && handlerMethod.shouldValidateArguments(),
            this.reactiveAdapterRegistry);

    InvocableHandlerMethod invocableMethod = this.methodResolver.getRequestMappingMethod(handlerMethod);

    DispatchExceptionHandler exceptionHandler =
            (exchange2, ex) -> handleException(exchange, ex, handlerMethod, bindingContext);

    Mono<HandlerResult> resultMono = this.modelInitializer
            .initModel(handlerMethod, bindingContext, exchange)
            .then(Mono.defer(() -> invocableMethod.invoke(exchange, bindingContext)))
            .doOnNext(result -> result.setExceptionHandler(exceptionHandler))
            .onErrorResume(ex -> exceptionHandler.handleError(exchange, ex));

    Scheduler optionalScheduler = this.methodResolver.getSchedulerFor(handlerMethod);
    if (optionalScheduler != null) {
        return resultMono.subscribeOn(optionalScheduler);
    }

    return resultMono;
}
```

`spring-webflux` / `org.springframework.web.reactive.result.method.annotation` / `RequestMappingHandlerAdapter.java` L284-L330 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webflux/src/main/java/org/springframework/web/reactive/result/method/annotation/RequestMappingHandlerAdapter.java#L284-L330))

```java
// RequestMappingHandlerAdapter.java L284-L330
private Mono<HandlerResult> handleException(
        ServerWebExchange exchange, Throwable exception,
        @Nullable HandlerMethod handlerMethod, @Nullable BindingContext bindingContext) {

    Assert.state(this.methodResolver != null, "Not initialized");

    // Success and error responses may use different content types
    exchange.getAttributes().remove(HandlerMapping.PRODUCIBLE_MEDIA_TYPES_ATTRIBUTE);
    exchange.getResponse().getHeaders().clearContentHeaders();

    InvocableHandlerMethod invocable =
            this.methodResolver.getExceptionHandlerMethod(exception, exchange, handlerMethod);

    if (invocable != null) {
        ArrayList<Throwable> exceptions = new ArrayList<>();
        try {
            if (logger.isDebugEnabled()) {
                logger.debug(exchange.getLogPrefix() + "Using @ExceptionHandler " + invocable);
            }
            if (bindingContext != null) {
                bindingContext.getModel().asMap().clear();
            }
            else {
                bindingContext = new BindingContext();
            }

            // Expose causes as provided arguments as well
            Throwable exToExpose = exception;
            while (exToExpose != null) {
                exceptions.add(exToExpose);
                Throwable cause = exToExpose.getCause();
                exToExpose = (cause != exToExpose ? cause : null);
            }
            @Nullable Object[] arguments = new Object[exceptions.size() + 1];
            exceptions.toArray(arguments);  // efficient arraycopy call in ArrayList
            arguments[arguments.length - 1] = handlerMethod;

            return invocable.invoke(exchange, bindingContext, arguments)
                    .onErrorResume(invocationEx ->
                            handleExceptionHandlerFailure(exchange, exception, invocationEx, exceptions, invocable));
        }
        catch (Throwable invocationEx) {
            return handleExceptionHandlerFailure(exchange, exception, invocationEx, exceptions, invocable);
        }
    }
    return Mono.error(exception);
}
```

## 동작 흐름

```text
 handle(exchange, handler)
 |
 | L260 InitBinderBindingContext 생성
 |        @InitBinder 메서드 목록, 메서드 검증기, 리액티브 어댑터 레지스트리
 | L265 invocableMethod = 이 핸들러 메서드용 InvocableHandlerMethod
 | L267 exceptionHandler = 이 요청 전용 @ExceptionHandler 복구 함수
 |
 +-- L270 파이프라인 조립
       modelInitializer.initModel(...)        @ModelAttribute 메서드 실행 (비동기 가능)
         .then(invocableMethod.invoke(exchange, bindingContext))
         .doOnNext(result -> result.setExceptionHandler(exceptionHandler))
         .onErrorResume(ex -> exceptionHandler.handleError(exchange, ex))
 |
 +-- L276 이 핸들러에 지정된 Scheduler 가 있으면 subscribeOn 으로 옮긴다
        (블로킹 컨트롤러를 별도 스레드에서 돌리는 설정)

 handleException(exchange, ex, handlerMethod, bindingContext)
 |
 | L291 성공 응답용 producible 타입 속성 제거, 응답 헤더 비우기
 | L294 예외에 맞는 @ExceptionHandler 메서드 조회 (컨트롤러 -> @ControllerAdvice)
 +-- L321 찾았으면 예외와 원인들을 인자로 넘겨 호출
          없으면 오류를 그대로 전파 --> 위쪽 WebExceptionHandler 가 처리
```

메서드 호출 자체는 리액티브하게 이뤄진다.

`spring-webflux` / `org.springframework.web.reactive.result.method` / `InvocableHandlerMethod.java` L181-L242 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webflux/src/main/java/org/springframework/web/reactive/result/method/InvocableHandlerMethod.java#L181-L242))

```java
// InvocableHandlerMethod.java L181-L242
public Mono<HandlerResult> invoke(
        ServerWebExchange exchange, BindingContext bindingContext, @Nullable Object... providedArgs) {

    return getMethodArgumentValuesOnScheduler(exchange, bindingContext, providedArgs).flatMap(args -> {
        if (shouldValidateArguments() && this.methodValidator != null) {
            try {
                LocaleContextHolder.setLocaleContext(exchange.getLocaleContext());
                this.methodValidator.applyArgumentValidation(
                        getBean(), getBridgedMethod(), getMethodParameters(), args, getValidationGroups());
            }
            finally {
                LocaleContextHolder.resetLocaleContext();
            }
        }
        Object value;
        boolean isSuspendingFunction;
        Method method = getBridgedMethod();
        try {
            if (KOTLIN_REFLECT_PRESENT && KotlinDetector.isKotlinType(method.getDeclaringClass())) {
                isSuspendingFunction = KotlinDetector.isSuspendingFunction(method);
                value = KotlinDelegate.invokeFunction(method, getBean(), args, isSuspendingFunction, exchange);
            }
            else {
                isSuspendingFunction = false;
                value = method.invoke(getBean(), args);
            }
        }
        catch (IllegalArgumentException ex) {
            assertTargetBean(getBridgedMethod(), getBean(), args);
            String text = (ex.getMessage() != null ? ex.getMessage() : "Illegal argument");
            return Mono.error(new IllegalStateException(formatInvokeError(text, args), ex));
        }
        catch (InvocationTargetException ex) {
            return Mono.error(ex.getTargetException());
        }
        catch (Throwable ex) {
            // Unlikely to ever get here, but it must be handled...
            return Mono.error(new IllegalStateException(formatInvokeError("Invocation failure", args), ex));
        }

        HttpStatusCode status = getResponseStatus();
        if (status != null) {
            exchange.getResponse().setStatusCode(status);
        }

        MethodParameter returnType = getReturnType();
        if (isResponseHandled(args, exchange)) {
            Class<?> parameterType = returnType.getParameterType();
            ReactiveAdapter adapter = this.reactiveAdapterRegistry.getAdapter(parameterType);
            boolean asyncVoid = isAsyncVoidReturnType(returnType, adapter);
            if (value == null || asyncVoid) {
                return (asyncVoid ? Mono.from(adapter.toPublisher(value)) : Mono.empty());
            }
            if (isSuspendingFunction && parameterType == void.class) {
                return (Mono<HandlerResult>) value;
            }
        }

        HandlerResult result = new HandlerResult(this, value, returnType, bindingContext);
        return Mono.just(result);
    });
}
```

```text
 InvocableHandlerMethod.invoke(exchange, bindingContext, providedArgs)
 |
 | L184 getMethodArgumentValuesOnScheduler
 |        파라미터마다 리졸버가 Mono<Object> 를 만든다
 |        @RequestBody 는 본문을 디코딩하는 Mono
 |        --> Mono.zip 으로 모두 모아 Object[] 로
 |
 | L185 메서드 검증 대상이면 인자 검증
 |
 | L198 Kotlin suspend 함수면 코루틴 경로, 아니면 method.invoke
 |        예외는 Mono.error 로 감싼다 (throw 하지 않는다)
 |
 | L221 @ResponseStatus 가 있으면 응답 상태 코드 설정
 |
 +-- L239 HandlerResult(반환값, 반환 타입, 바인딩 컨텍스트) 를 Mono.just 로
```

## 결과가 쓰이는 곳

```text
 HandlerResult
      --> DispatcherHandler.handleResult --> HandlerResultHandler 선택의 입력
      --> 반환값이 Mono/Flux 여도 여기서는 "그 객체" 로만 담긴다
          실제 구독은 결과 처리기가 한다

 result.setExceptionHandler
      --> 결과를 쓰는 도중(인코딩 중) 난 오류도 @ExceptionHandler 로 복구할 수 있게 한다
      --> MVC 에는 없는 단계 (본문 쓰기가 비동기라 생긴 필요)

 Mono.error 로 감싼 호출 예외
      --> onErrorResume 체인을 타고 @ExceptionHandler 로
      --> 아무도 처리하지 못하면 WebExceptionHandler 로 올라간다
```

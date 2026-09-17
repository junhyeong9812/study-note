# InvocableHandlerMethod.getMethodArgumentValues

상위: [ServletInvocableHandlerMethod.invokeAndHandle](../README.md)

컨트롤러 메서드의 파라미터 하나하나에 넣을 값을 만든다. 파라미터마다 [HandlerMethodArgumentResolver](../../../../spi/HandlerMethodArgumentResolver/README.md) 목록에서 처리할 수 있는 리졸버를 찾아 값을 받는다.

## 실제 코드

`spring-web` / `org.springframework.web.method.support` / `InvocableHandlerMethod.java` L200-L238 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-web/src/main/java/org/springframework/web/method/support/InvocableHandlerMethod.java#L200-L238))

```java
// InvocableHandlerMethod.java L200-L238
protected @Nullable Object[] getMethodArgumentValues(NativeWebRequest request, @Nullable ModelAndViewContainer mavContainer,
        @Nullable Object... providedArgs) throws Exception {

    MethodParameter[] parameters = getMethodParameters();
    if (ObjectUtils.isEmpty(parameters)) {
        return EMPTY_ARGS;
    }

    @Nullable Object[] args = new Object[parameters.length];
    for (int i = 0; i < parameters.length; i++) {
        MethodParameter parameter = parameters[i];
        parameter.initParameterNameDiscovery(this.parameterNameDiscoverer);
        args[i] = findProvidedArgument(parameter, providedArgs);
        if (args[i] != null) {
            continue;
        }
        if (parameter.getParameterType().equals(HandlerMethod.class) && parameter.isOptional()) {
            args[i] = null;
            continue;
        }
        if (!this.resolvers.supportsParameter(parameter)) {
            throw new IllegalStateException(formatArgumentError(parameter, "No suitable resolver"));
        }
        try {
            args[i] = this.resolvers.resolveArgument(parameter, mavContainer, request, this.dataBinderFactory);
        }
        catch (Exception ex) {
            // Leave stack trace for later, exception may actually be resolved and handled...
            if (logger.isDebugEnabled()) {
                String exMsg = ex.getMessage();
                if (exMsg != null && !exMsg.contains(parameter.getExecutable().toGenericString())) {
                    logger.debug(formatArgumentError(parameter, exMsg));
                }
            }
            throw ex;
        }
    }
    return args;
}
```

리졸버 목록은 하나의 Composite로 감싸져 있고, "누가 처리하나"의 답을 파라미터별로 캐시한다.

`spring-web` / `org.springframework.web.method.support` / `HandlerMethodArgumentResolverComposite.java` L114-L123 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-web/src/main/java/org/springframework/web/method/support/HandlerMethodArgumentResolverComposite.java#L114-L123))

```java
// HandlerMethodArgumentResolverComposite.java L114-L123
public @Nullable Object resolveArgument(MethodParameter parameter, @Nullable ModelAndViewContainer mavContainer,
        NativeWebRequest webRequest, @Nullable WebDataBinderFactory binderFactory) throws Exception {

    HandlerMethodArgumentResolver resolver = getArgumentResolver(parameter);
    if (resolver == null) {
        throw new IllegalArgumentException("Unsupported parameter type [" +
                parameter.getParameterType().getName() + "]. supportsParameter should be called first.");
    }
    return resolver.resolveArgument(parameter, mavContainer, webRequest, binderFactory);
}
```

`spring-web` / `org.springframework.web.method.support` / `HandlerMethodArgumentResolverComposite.java` L129-L141 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-web/src/main/java/org/springframework/web/method/support/HandlerMethodArgumentResolverComposite.java#L129-L141))

```java
// HandlerMethodArgumentResolverComposite.java L129-L141
public @Nullable HandlerMethodArgumentResolver getArgumentResolver(MethodParameter parameter) {
    HandlerMethodArgumentResolver result = this.argumentResolverCache.get(parameter);
    if (result == null) {
        for (HandlerMethodArgumentResolver resolver : this.argumentResolvers) {
            if (resolver.supportsParameter(parameter)) {
                result = resolver;
                this.argumentResolverCache.put(parameter, result);
                break;
            }
        }
    }
    return result;
}
```

## 동작 흐름

```text
 getMethodArgumentValues(request, mavContainer, providedArgs)
 |
 +-- 파라미터 없음 --> EMPTY_ARGS
 |
 +-- for i, parameter in parameters
       |
       | 1. 파라미터 이름 탐색기 연결       (@RequestParam 이름 생략 시 -parameters 정보 사용)
       |
       | 2. providedArgs 중 타입이 맞는 값이 있으면 --> args[i], continue
       |       (@ExceptionHandler의 예외 객체가 여기서 들어감)
       |
       | 3. HandlerMethod 타입 + Optional --> null, continue
       |
       | 4. resolvers.supportsParameter(parameter) ?
       |       no  --> IllegalStateException("No suitable resolver")
       |
       | 5. args[i] = resolvers.resolveArgument(...)
       |       getArgumentResolver(parameter)
       |         캐시 hit  --> 바로 그 리졸버
       |         캐시 miss --> 목록 순회, supportsParameter가 true인 첫 리졸버를 캐시에 저장
       |       예외 --> 디버그 로그 후 그대로 던짐  (예외 처리기가 해석할 수 있도록)
       |
 +-- return args
```

리졸버 목록의 앞쪽은 어노테이션 기반, 뒤쪽은 타입 기반, 맨 끝은 "무엇이든 받는" 기본 리졸버다.

```text
 @RequestParam String q           --> RequestParamMethodArgumentResolver
 @PathVariable Long id            --> PathVariableMethodArgumentResolver   (URI_TEMPLATE_VARIABLES 속성 읽음)
 @RequestBody UserDto dto         --> RequestResponseBodyMethodProcessor   (HttpMessageConverter로 본문 읽기 + 검증)
 @ModelAttribute UserForm form    --> ServletModelAttributeMethodProcessor (모델 조회 또는 생성 + 바인딩)
 HttpServletRequest req           --> ServletRequestMethodArgumentResolver
 Model model                      --> ModelMethodProcessor                 (mavContainer의 모델)
 어노테이션 없는 String name      --> 맨 끝 RequestParamMethodArgumentResolver(기본 모드) = @RequestParam 취급
 어노테이션 없는 UserForm form    --> 맨 끝 ServletModelAttributeMethodProcessor(기본 모드) = @ModelAttribute 취급
```

## 결과가 쓰이는 곳

```text
 args (Object[])
      +-- invokeForRequest --> methodValidator.applyArgumentValidation(args)
      |                          제약 위반 --> MethodValidationException / HandlerMethodValidationException
      +-- invokeForRequest --> doInvoke(args) --> method.invoke(bean, args)

 resolveArgument가 던진 예외
      MissingServletRequestParameterException  --> 400
      MethodArgumentNotValidException          --> 400   (@RequestBody @Valid 실패)
      HttpMessageNotReadableException          --> 400   (JSON 파싱 실패)
      --> doDispatch의 dispatchException --> HandlerExceptionResolver
```

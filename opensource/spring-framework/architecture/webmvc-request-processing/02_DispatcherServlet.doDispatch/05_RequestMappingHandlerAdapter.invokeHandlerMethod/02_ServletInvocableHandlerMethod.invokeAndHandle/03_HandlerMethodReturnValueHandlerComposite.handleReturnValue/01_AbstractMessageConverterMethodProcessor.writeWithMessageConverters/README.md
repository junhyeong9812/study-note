# AbstractMessageConverterMethodProcessor.writeWithMessageConverters

상위: [HandlerMethodReturnValueHandlerComposite.handleReturnValue](../README.md)

`@ResponseBody`의 반환 객체를 HTTP 응답 본문으로 쓴다. 클라이언트가 받을 수 있는 타입(`Accept`)과 서버가 만들 수 있는 타입을 맞춰 미디어 타입 하나를 고르고, 그 타입을 쓸 수 있는 첫 [HttpMessageConverter](../../../../../spi/HttpMessageConverter/README.md)로 직렬화한다.

## 실제 코드

`spring-webmvc` / `org.springframework.web.servlet.mvc.method.annotation` / `AbstractMessageConverterMethodProcessor.java` L205-L368 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/mvc/method/annotation/AbstractMessageConverterMethodProcessor.java#L205-L368))

```java
// AbstractMessageConverterMethodProcessor.java L205-L368
protected <T> void writeWithMessageConverters(@Nullable T value, MethodParameter returnType,
        ServletServerHttpRequest inputMessage, ServletServerHttpResponse outputMessage)
        throws IOException, HttpMediaTypeNotAcceptableException, HttpMessageNotWritableException {

    Object body;
    Class<?> valueType;
    Type targetType;

    if (value instanceof CharSequence) {
        body = value.toString();
        valueType = String.class;
        targetType = String.class;
    }
    else {
        body = value;
        valueType = getReturnValueType(body, returnType);
        targetType = GenericTypeResolver.resolveType(getGenericType(returnType), returnType.getContainingClass());
    }

    if (isResourceType(value, returnType)) {
        outputMessage.getHeaders().set(HttpHeaders.ACCEPT_RANGES, "bytes");
        if (value != null && inputMessage.getHeaders().getFirst(HttpHeaders.RANGE) != null &&
                outputMessage.getServletResponse().getStatus() == 200) {
            Resource resource = (Resource) value;
            try {
                List<HttpRange> httpRanges = inputMessage.getHeaders().getRange();
                outputMessage.getServletResponse().setStatus(HttpStatus.PARTIAL_CONTENT.value());
                body = HttpRange.toResourceRegions(httpRanges, resource);
                valueType = body.getClass();
                targetType = RESOURCE_REGION_LIST_TYPE;
            }
            catch (IllegalArgumentException ex) {
                outputMessage.getHeaders().set(HttpHeaders.CONTENT_RANGE, "bytes */" + resource.contentLength());
                outputMessage.getServletResponse().setStatus(HttpStatus.REQUESTED_RANGE_NOT_SATISFIABLE.value());
            }
        }
    }

    MediaType selectedMediaType = null;
    MediaType contentType = outputMessage.getHeaders().getContentType();
    boolean isContentTypePreset = contentType != null && contentType.isConcrete();
    if (isContentTypePreset) {
        if (logger.isDebugEnabled()) {
            logger.debug("Found 'Content-Type:" + contentType + "' in response");
        }
        selectedMediaType = contentType;
    }
    else {
        HttpServletRequest request = inputMessage.getServletRequest();
        List<MediaType> acceptableTypes;
        try {
            acceptableTypes = getAcceptableMediaTypes(request);
        }
        catch (HttpMediaTypeNotAcceptableException ex) {
            int series = outputMessage.getServletResponse().getStatus() / 100;
            if (body == null || series == 4 || series == 5) {
                if (logger.isDebugEnabled()) {
                    logger.debug("Ignoring error response content (if any). " + ex);
                }
                return;
            }
            throw ex;
        }

        List<MediaType> producibleTypes = getProducibleMediaTypes(request, valueType, targetType);
        if (body != null && producibleTypes.isEmpty()) {
            throw new HttpMessageNotWritableException(
                    "No converter found for return value of type: " + valueType);
        }

        List<MediaType> compatibleMediaTypes = determineCompatibleMediaTypes(acceptableTypes, producibleTypes);

        // For ProblemDetail, fall back on RFC 9457 format
        if (compatibleMediaTypes.isEmpty() && ProblemDetail.class.isAssignableFrom(valueType)) {
            compatibleMediaTypes = determineCompatibleMediaTypes(PROBLEM_MEDIA_TYPES, producibleTypes);
        }

        if (compatibleMediaTypes.isEmpty()) {
            if (logger.isDebugEnabled()) {
                logger.debug("No match for " + acceptableTypes + ", supported: " + producibleTypes);
            }
            if (body != null) {
                throw new HttpMediaTypeNotAcceptableException(producibleTypes);
            }
            return;
        }

        MimeTypeUtils.sortBySpecificity(compatibleMediaTypes);

        for (MediaType mediaType : compatibleMediaTypes) {
            if (mediaType.isConcrete()) {
                selectedMediaType = mediaType;
                break;
            }
            else if (mediaType.isPresentIn(ALL_APPLICATION_MEDIA_TYPES)) {
                selectedMediaType = MediaType.APPLICATION_OCTET_STREAM;
                break;
            }
        }

        if (logger.isDebugEnabled()) {
            logger.debug("Using '" + selectedMediaType + "', given " +
                    acceptableTypes + " and supported " + producibleTypes);
        }
    }

    if (selectedMediaType != null) {
        selectedMediaType = selectedMediaType.removeQualityValue();

        ResolvableType targetResolvableType = null;
        for (HttpMessageConverter converter : this.messageConverters) {
            ConverterType converterTypeToUse = null;
            if (converter instanceof GenericHttpMessageConverter genericConverter) {
                if (genericConverter.canWrite(targetType, valueType, selectedMediaType)) {
                    converterTypeToUse = ConverterType.GENERIC;
                }
            }
            else if (converter instanceof SmartHttpMessageConverter smartConverter) {
                targetResolvableType = getNestedTypeIfNeeded(ResolvableType.forType(targetType));
                if (smartConverter.canWrite(targetResolvableType, valueType, selectedMediaType)) {
                    converterTypeToUse = ConverterType.SMART;
                }
            }
            else if (converter.canWrite(valueType, selectedMediaType)){
                converterTypeToUse = ConverterType.BASE;
            }
            if (converterTypeToUse != null) {
                body = getAdvice().beforeBodyWrite(body, returnType, selectedMediaType,
                        (Class<? extends HttpMessageConverter<?>>) converter.getClass(), inputMessage, outputMessage);
                if (body != null) {
                    Object theBody = body;
                    LogFormatUtils.traceDebug(logger, traceOn ->
                            "Writing [" + LogFormatUtils.formatValue(theBody, !traceOn) + "]");
                    addContentDispositionHeader(inputMessage, outputMessage);
                    switch (converterTypeToUse) {
                        case BASE -> converter.write(body, selectedMediaType, outputMessage);
                        case GENERIC -> ((GenericHttpMessageConverter) converter).write(body, targetType, selectedMediaType, outputMessage);
                        case SMART -> ((SmartHttpMessageConverter) converter).write(body, targetResolvableType,
                                selectedMediaType, outputMessage, getAdvice().determineWriteHints(body, returnType,
                                        selectedMediaType, (Class<? extends HttpMessageConverter<?>>) converter.getClass()));
                    }
                }
                else {
                    if (logger.isDebugEnabled()) {
                        logger.debug("Nothing to write: null body");
                    }
                }
                return;
            }
        }
    }

    if (body != null) {
        Set<MediaType> producibleMediaTypes =
                (Set<MediaType>) inputMessage.getServletRequest()
                        .getAttribute(HandlerMapping.PRODUCIBLE_MEDIA_TYPES_ATTRIBUTE);

        if (isContentTypePreset || !CollectionUtils.isEmpty(producibleMediaTypes)) {
            throw new HttpMessageNotWritableException(
                    "No converter for [" + valueType + "] with preset Content-Type '" + contentType + "'");
        }
        throw new HttpMediaTypeNotAcceptableException(getSupportedMediaTypes(body.getClass()));
    }
}
```

## 동작 흐름

`GET /users/42`, `Accept: application/json`, 컨트롤러가 `User`를 반환한 경우다.

```text
 writeWithMessageConverters(value=User, returnType, inputMessage, outputMessage)
 |
 | [1] 본문과 타입 결정                                            L209-L222
 |     CharSequence --> body = toString(), valueType = targetType = String
 |     그 밖        --> body = value, valueType = User.class, targetType = 제네릭 해석 타입
 |
 | [2] Resource 반환 + Range 헤더 --> 206 Partial Content, body = ResourceRegion 목록  L224-L241
 |
 | [3] 미디어 타입 결정                                            L243-L309
 |     응답에 이미 구체적인 Content-Type이 있음 --> 그대로 사용 (협상 생략)
 |     없음 -->
 |       acceptableTypes  = getAcceptableMediaTypes(request)     [application/json]
 |                            파싱 실패 + (body null 또는 4xx/5xx) --> 조용히 return
 |       producibleTypes  = getProducibleMediaTypes(...)         [application/json, application/*+json, ...]
 |                            @RequestMapping(produces)가 있으면 그 값
 |                            없으면 User를 쓸 수 있는 컨버터들의 지원 타입 합집합
 |                            body 있는데 비어 있음 --> HttpMessageNotWritableException (500)
 |       compatible       = 두 목록의 교집합 (더 구체적인 쪽으로)
 |                            비어 있고 ProblemDetail --> application/problem+json 계열로 재시도
 |                            그래도 비어 있음 --> HttpMediaTypeNotAcceptableException (406)
 |       sortBySpecificity 후 첫 구체 타입 선택                  application/json
 |                            */* 나 application/* 만 남음 --> application/octet-stream
 |
 | [4] 컨버터 선택과 쓰기                                          L311-L355
 |     for converter in messageConverters     (등록 순서)
 |        GenericHttpMessageConverter --> canWrite(targetType, valueType, mediaType)
 |        SmartHttpMessageConverter   --> canWrite(ResolvableType, valueType, mediaType)
 |        그 밖                       --> canWrite(valueType, mediaType)
 |        처음 true인 컨버터에서
 |          body = ResponseBodyAdvice.beforeBodyWrite(...)   <-- 본문 가공 기회
 |          body != null --> Content-Disposition 보정 후 converter.write(...)
 |          return                                             (다음 컨버터는 보지 않음)
 |
 | [5] 쓸 컨버터가 없음                                            L357-L367
 |     Content-Type이 미리 정해져 있었음 --> HttpMessageNotWritableException (500)
 |     그 밖                             --> HttpMediaTypeNotAcceptableException (406)
```

## Accept 헤더가 파싱되는 길

`[3]`의 `getAcceptableMediaTypes`는 콘텐츠 협상 전략에게 요청을 넘기고, 헤더 전략은 `MediaType.parseMediaTypes`를 부른다.

`spring-webmvc` / `org.springframework.web.servlet.mvc.method.annotation` / `AbstractMessageConverterMethodProcessor.java` L448-L452 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/mvc/method/annotation/AbstractMessageConverterMethodProcessor.java#L448-L452))

```java
// AbstractMessageConverterMethodProcessor.java L448-L452
private List<MediaType> getAcceptableMediaTypes(HttpServletRequest request)
        throws HttpMediaTypeNotAcceptableException {

    return this.contentNegotiationManager.resolveMediaTypes(new ServletWebRequest(request));
}
```

`spring-web` / `org.springframework.web.accept` / `HeaderContentNegotiationStrategy.java` L45-L63 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-web/src/main/java/org/springframework/web/accept/HeaderContentNegotiationStrategy.java#L45-L63))

```java
// HeaderContentNegotiationStrategy.java L45-L63
public List<MediaType> resolveMediaTypes(NativeWebRequest request)
        throws HttpMediaTypeNotAcceptableException {

    String[] headerValueArray = request.getHeaderValues(HttpHeaders.ACCEPT);
    if (headerValueArray == null) {
        return MEDIA_TYPE_ALL_LIST;
    }

    List<String> headerValues = Arrays.asList(headerValueArray);
    try {
        List<MediaType> mediaTypes = MediaType.parseMediaTypes(headerValues);
        MimeTypeUtils.sortBySpecificity(mediaTypes);
        return !CollectionUtils.isEmpty(mediaTypes) ? mediaTypes : MEDIA_TYPE_ALL_LIST;
    }
    catch (InvalidMediaTypeException | InvalidMimeTypeException ex) {
        throw new HttpMediaTypeNotAcceptableException(
                "Could not parse 'Accept' header " + headerValues + ": " + ex.getMessage());
    }
}
```

`spring-core` / `org.springframework.util` / `MimeTypeUtils.java` L194-L203 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-core/src/main/java/org/springframework/util/MimeTypeUtils.java#L194-L203))

```java
// MimeTypeUtils.java L194-L203
public static MimeType parseMimeType(String mimeType) {
    if (!StringUtils.hasLength(mimeType)) {
        throw new InvalidMimeTypeException(mimeType, "'mimeType' must not be empty");
    }
    // do not cache multipart mime types with random boundaries
    if (mimeType.startsWith("multipart")) {
        return parseMimeTypeInternal(mimeType);
    }
    return cachedMimeTypes.get(mimeType);
}
```

```text
 getAcceptableMediaTypes(request)
   --> ContentNegotiationManager.resolveMediaTypes     전략 목록 순회 (기본은 헤더 전략)
     --> HeaderContentNegotiationStrategy.resolveMediaTypes
           Accept 헤더 없음 --> [*/*]
           MediaType.parseMediaTypes(headerValues)      MediaType L732 --> L700
             --> MimeTypeUtils.parseMimeTypes(String)   콤마로 토큰 분리
               --> MimeTypeUtils.parseMimeType(token)   L194
                     --> cachedMimeTypes.get(token)     ConcurrentLruCache(64), L166
                           miss --> parseMimeTypeInternal(token)   실제 파싱
           파싱 실패 --> HttpMediaTypeNotAcceptableException
```

이 길 위에 우리 기여 두 건이 있다.

- [#37008](../../../../../../../prs/37008-mimetype-duplicate-parameters/) — `parseMimeTypeInternal`이 쓰는 파서(`MimeTypeParser.putParameter`, MimeTypeUtils L438)가 `text/plain;dupe="1";DUPE="2"`처럼 대소문자만 다른 중복 파라미터를 거부하도록 고쳤다.
- [#37268](../../../../../../../prs/37268-lru-cache-double-decrement/) — `cachedMimeTypes`의 `ConcurrentLruCache`에서 같은 노드를 두 번 감산하던 결함을 고쳤다. 이 경로는 `remove`를 부르지 않아 실제로 발화하지는 않는다.

## 결과가 쓰이는 곳

```text
 selectedMediaType
      +-- converter.write(body, selectedMediaType, outputMessage)
      |     --> 응답 Content-Type 헤더 = application/json (+ charset)
      +-- ResponseBodyAdvice.beforeBodyWrite 의 인자
            --> 선택된 타입에 따라 본문을 감싸거나 바꿀 수 있음

 선택된 converter (예: JacksonJsonHttpMessageConverter)
      --> User 객체를 JSON 바이트로 outputMessage.getBody()에 기록
      --> 이 순간 응답이 커밋될 수 있음
          = 이후 예외가 나면 오류 응답으로 바꿀 수 없다 (processHandlerException의 resetBuffer 실패)

 던진 예외
      HttpMediaTypeNotAcceptableException --> 406
      HttpMessageNotWritableException     --> 500
      --> doDispatch의 dispatchException --> HandlerExceptionResolver
```

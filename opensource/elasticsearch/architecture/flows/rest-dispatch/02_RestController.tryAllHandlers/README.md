# RestController.tryAllHandlers

상위: [REST 디스패치](../README.md)

경로에 맞는 후보를 하나씩 꺼내 **처음으로 맞는 핸들러**를 고른다. 이 흐름에서 가장 많은 갈래가 여기 있고, 거절하는 길도 셋이 여기서 나간다.

## 위치

`server` / `org.elasticsearch.rest` / `RestController.java` L702-L750 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/rest/RestController.java#L702-L750))

## 실제 코드

```java
// RestController.java L702-L750
    private void tryAllHandlers(final RestRequest request, final RestChannel channel, final ThreadContext threadContext) throws Exception {
        try {
            validateErrorTrace(request, channel);
        } catch (IllegalArgumentException e) {
            startTrace(threadContext, channel);
            channel.sendResponse(RestResponse.createSimpleErrorResponse(channel, BAD_REQUEST, e.getMessage()));
            recordRequestMetric(BAD_REQUEST, requestsCounter);
            return;
        }

        final String rawPath = request.rawPath();
        final String uri = request.uri();
        final RestRequest.Method requestMethod;

        RestApiVersion restApiVersion = request.getRestApiVersion();
        try {
            // Resolves the HTTP method and fails if the method is invalid
            requestMethod = request.method();
            // Loop through all possible handlers, attempting to dispatch the request
            Iterator<MethodHandlers> allHandlers = getAllHandlers(request.params(), rawPath);
            while (allHandlers.hasNext()) {
                final RestHandler handler;
                final MethodHandlers handlers = allHandlers.next();
                if (handlers == null) {
                    handler = null;
                } else {
                    handler = handlers.getHandler(requestMethod, restApiVersion);
                }
                if (handler == null) {
                    if (handleNoHandlerFound(threadContext, rawPath, requestMethod, uri, channel)) {
                        return;
                    }
                } else {
                    startTrace(threadContext, channel, handlers.getPath());
                    var decoratedChannel = new MeteringRestChannelDecorator(channel, requestsCounter, handler.getConcreteRestHandler());
                    maybeAggregateAndDispatchRequest(request, decoratedChannel, handler, handlers, threadContext);
                    return;
                }
            }
        } catch (final IllegalArgumentException e) {
            startTrace(threadContext, channel);
            traceException(channel, e);
            handleUnsupportedHttpMethod(uri, null, channel, getValidHandlerMethodSet(rawPath), e);
            return;
        }
        // If request has not been handled, fallback to a bad request error.
        startTrace(threadContext, channel);
        handleBadRequest(uri, requestMethod, channel);
    }
```

## 동작 흐름

```text
 L704  validateErrorTrace(request, channel)
         error_trace=true 인데 상세 오류가 꺼져 있으면 IAE 를 던진다 (L755-757)
         |
         +-- L705  catch -> L707 400 응답, L708 메트릭, L709 return
                   여기서 끝난다

 L719  requestMethod = request.method()
         주석이 적어 두었다 - "메서드를 해석하고, 잘못됐으면 실패한다" (L718)

 L721  allHandlers = getAllHandlers(request.params(), rawPath)
         매칭 모드 4종에 각각 대응하는 후보를 내놓는 이터레이터다

 L722  while (allHandlers.hasNext())
       |
       +-- L724  handlers = allHandlers.next()
       |
       +-- L725  handlers == null        -> handler = null
       |           경로 자체에 아무것도 없다
       +-- L728  getHandler(requestMethod, restApiVersion)
       |           경로는 있는데 이 메서드 + 이 API 버전 조합이 없으면 역시 null
       |
       +-- L730  handler == null
       |     +-- L731  handleNoHandlerFound(...)
       |           true  -> 여기서 응답을 보내고 끝났다. return
       |           false -> 다음 후보로 간다
       |
       +-- L734  handler != null
             +-- L735  startTrace(threadContext, channel, handlers.getPath())
             +-- L736  new MeteringRestChannelDecorator(channel, ...)
             +-- L737  maybeAggregateAndDispatchRequest(...)
             +-- L738  return

 L741  catch (IllegalArgumentException e)
         L719 의 메서드 해석이나 경로 탐색에서 올라온 것
         L744  handleUnsupportedHttpMethod(uri, null, channel, ..., e)  405

 L748  루프를 다 돌았는데 return 을 못 했다
 L749  handleBadRequest(uri, requestMethod, channel)  400
```

```text
 handleUnsupportedHttpMethod 가 두 군데서 불린다

 L672  handleNoHandlerFound 안에서   method 가 있고, 예외는 없다
 L744  이 메서드의 catch 에서         method 가 null 이고, 예외가 있다

 인자가 달라서 나가는 메시지가 다르다
 같은 405 라도 "이 경로는 GET 만 받는다"와
 "메서드를 알아볼 수 없다"는 다른 상황이다
```

```text
 후보가 여러 개인 이유

 retrieveAll 은 매칭 모드 4종을 차례로 적용한다 (PathTrie L350-352)
   EXPLICIT_NODES_ONLY          변수 없이 정확히 일치하는 것만
   WILDCARD_ROOT_NODES_ALLOWED  첫 칸에만 변수 허용
   WILDCARD_LEAF_NODES_ALLOWED  마지막 칸에만 변수 허용
   WILDCARD_NODES_ALLOWED       변수 전부 허용

 모드 하나가 후보 하나를 내므로 루프는 최대 네 바퀴다
 엄격한 것부터 느슨한 것 순이라 정확히 일치하는 경로가 우선한다

 그래서 "못 찾았다"를 한 번에 판정하지 않는다
 handleNoHandlerFound 가 false 를 돌려주면 다음 모드로 넘어간다
```

## 결과가 쓰이는 곳

```text
 고른 handler
      --> [05] 가 supportsContentStream() 을 물어 본문 처리를 정한다
      --> [06] 의 검사 전부가 이 핸들러에게 묻는다

 MeteringRestChannelDecorator
      --> 응답이 나갈 때 이 핸들러 이름으로 메트릭을 남긴다
      --> handler.getConcreteRestHandler() 를 쓴다 (L736)
          deprecated 라우트는 한 겹 싸여 있어서 벗겨야 원래 이름이 나온다

 restApiVersion
      --> 후보 선택의 입력이다 (L728)
      --> 경로와 메서드가 맞아도 버전이 안 맞으면 핸들러가 없는 것으로 친다
      --> 그 경우 handleNoHandlerFound 가 false 를 주고 결국 L749 의 400 이 된다

 startTrace
      --> 핸들러를 찾은 경우에만 3-arg 로 부른다 (L735)
      --> 거절하는 길들은 2-arg 라 경로 이름이 트레이스에 안 들어간다
```

## 다루지 않는 것

`PathTrie` 의 자료구조와 각 매칭 모드가 노드를 고르는 내부 규칙, `MethodHandlers` 가 메서드와 API 버전으로 핸들러를 고르는 내부, `RestApiVersion` 호환성 정책, `handleBadRequest` 와 `handleUnsupportedHttpMethod` 의 응답 본문 형식, `startTrace` 와 텔레메트리 연동, `MeteringRestChannelDecorator` 의 메트릭 항목은 같은 뼈대의 곁가지라 요약만 했다.

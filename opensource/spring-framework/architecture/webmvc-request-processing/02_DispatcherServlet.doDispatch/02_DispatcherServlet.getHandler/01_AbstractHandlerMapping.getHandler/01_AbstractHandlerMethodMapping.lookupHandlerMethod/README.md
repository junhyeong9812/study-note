# AbstractHandlerMethodMapping.lookupHandlerMethod

상위: [AbstractHandlerMapping.getHandler](../README.md)

요청 경로에 맞는 `@RequestMapping` 메서드를 찾는다. 후보를 모은 뒤 가장 구체적인 하나를 고르고, 1등이 둘이면 예외를 던진다.

## 진입: getHandlerInternal

`spring-webmvc` / `org.springframework.web.servlet.handler` / `AbstractHandlerMethodMapping.java` L372-L382 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/handler/AbstractHandlerMethodMapping.java#L372-L382))

```java
// AbstractHandlerMethodMapping.java L372-L382
protected @Nullable HandlerMethod getHandlerInternal(HttpServletRequest request) throws Exception {
    String lookupPath = initLookupPath(request);
    this.mappingRegistry.acquireReadLock();
    try {
        HandlerMethod handlerMethod = lookupHandlerMethod(lookupPath, request);
        return (handlerMethod != null ? handlerMethod.createWithResolvedBean() : null);
    }
    finally {
        this.mappingRegistry.releaseReadLock();
    }
}
```

## 실제 코드

`spring-webmvc` / `org.springframework.web.servlet.handler` / `AbstractHandlerMethodMapping.java` L393-L434 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/handler/AbstractHandlerMethodMapping.java#L393-L434))

```java
// AbstractHandlerMethodMapping.java L393-L434
protected @Nullable HandlerMethod lookupHandlerMethod(String lookupPath, HttpServletRequest request) throws Exception {
    List<Match> matches = new ArrayList<>();
    List<T> directPathMatches = this.mappingRegistry.getMappingsByDirectPath(lookupPath);
    if (directPathMatches != null) {
        addMatchingMappings(directPathMatches, matches, request);
    }
    if (matches.isEmpty()) {
        addMatchingMappings(this.mappingRegistry.getRegistrations().keySet(), matches, request);
    }
    if (!matches.isEmpty()) {
        Match bestMatch = matches.get(0);
        if (matches.size() > 1) {
            Comparator<Match> comparator = new MatchComparator(getMappingComparator(request));
            matches.sort(comparator);
            bestMatch = matches.get(0);
            if (logger.isTraceEnabled()) {
                logger.trace(matches.size() + " matching mappings: " + matches);
            }
            if (CorsUtils.isPreFlightRequest(request)) {
                if (matches.stream().allMatch(Match::hasCorsConfig)) {
                    return PREFLIGHT_AMBIGUOUS_MATCH;
                }
            }
            else {
                Match secondBestMatch = matches.get(1);
                if (comparator.compare(bestMatch, secondBestMatch) == 0) {
                    Method m1 = bestMatch.getHandlerMethod().getMethod();
                    Method m2 = secondBestMatch.getHandlerMethod().getMethod();
                    String uri = request.getRequestURI();
                    throw new IllegalStateException(
                            "Ambiguous handler methods mapped for '" + uri + "': {" + m1 + ", " + m2 + "}");
                }
            }
        }
        request.setAttribute(BEST_MATCHING_HANDLER_ATTRIBUTE, bestMatch.getHandlerMethod());
        handleMatch(bestMatch.mapping, lookupPath, request);
        return bestMatch.getHandlerMethod();
    }
    else {
        return handleNoMatch(this.mappingRegistry.getRegistrations().keySet(), lookupPath, request);
    }
}
```

`spring-webmvc` / `org.springframework.web.servlet.handler` / `AbstractHandlerMethodMapping.java` L437-L444 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/handler/AbstractHandlerMethodMapping.java#L437-L444))

```java
// AbstractHandlerMethodMapping.java L437-L444
private void addMatchingMappings(Collection<T> mappings, List<Match> matches, HttpServletRequest request) {
    for (T mapping : mappings) {
        T match = getMatchingMapping(mapping, request);
        if (match != null) {
            matches.add(new Match(match, this.mappingRegistry.getRegistrations().get(mapping)));
        }
    }
}
```

## 매칭 조건 판정

`getMatchingMapping`은 `RequestMappingInfo`에게 "이 요청에 맞는 부분만 남긴 조건"을 달라고 한다. 조건 하나라도 안 맞으면 null이다.

`spring-webmvc` / `org.springframework.web.servlet.mvc.method` / `RequestMappingInfoHandlerMapping.java` L103-L105 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/mvc/method/RequestMappingInfoHandlerMapping.java#L103-L105))

```java
// RequestMappingInfoHandlerMapping.java L103-L105
protected @Nullable RequestMappingInfo getMatchingMapping(RequestMappingInfo info, HttpServletRequest request) {
    return info.getMatchingCondition(request);
}
```

## 동작 흐름

```text
 getHandlerInternal(request)
 |  lookupPath = initLookupPath(request)       "/users/42"
 |  mappingRegistry 읽기 락 획득               (등록/해제와 동시 실행 방지)
 |
 +-- lookupHandlerMethod(lookupPath, request)
 |   |
 |   | L395 directPathMatches = registry.getMappingsByDirectPath(lookupPath)
 |   |        패턴 없는 경로("/users")만 Map으로 바로 조회   --> O(1)
 |   |
 |   | L397 있으면 그 후보만 addMatchingMappings
 |   | L400 매치가 없으면 등록된 전부를 addMatchingMappings  --> O(n), 패턴("/users/{id}")은 여기서
 |   |
 |   |      addMatchingMappings: mapping마다 getMatchingMapping(mapping, request)
 |   |          RequestMappingInfo.getMatchingCondition 순서
 |   |          methods -> params -> headers -> consumes -> produces -> version -> path -> custom
 |   |          하나라도 null이면 탈락
 |   |
 |   +-- matches 비어 있음
 |   |      --> handleNoMatch()   (RequestMappingInfoHandlerMapping 재정의)
 |   |            경로는 맞고 메서드만 다름   --> HttpRequestMethodNotSupportedException (405)
 |   |            Content-Type이 안 맞음     --> HttpMediaTypeNotSupportedException   (415)
 |   |            Accept가 안 맞음           --> HttpMediaTypeNotAcceptableException  (406)
 |   |            params 조건이 안 맞음      --> UnsatisfiedServletRequestParameterException (400)
 |   |            경로부터 안 맞음           --> null   (다음 HandlerMapping으로)
 |   |
 |   +-- matches 1개 --> bestMatch
 |   +-- matches 여러 개
 |          MatchComparator로 정렬 (더 구체적인 패턴, 조건이 많은 쪽이 앞)
 |          preflight --> 모두 CORS 설정이 있으면 PREFLIGHT_AMBIGUOUS_MATCH
 |          그 밖     --> 1등과 2등이 동점이면 IllegalStateException("Ambiguous handler methods")
 |
 |   L427 request 속성 BEST_MATCHING_HANDLER_ATTRIBUTE = bestMatch 핸들러
 |   L428 handleMatch()   경로 변수, 매칭 패턴 등을 request 속성에 기록
 |
 +-- handlerMethod.createWithResolvedBean()   빈 이름으로 등록된 컨트롤러를 실제 인스턴스로 교체
 +-- 읽기 락 해제
```

## 결과가 쓰이는 곳

```text
 HandlerMethod (컨트롤러 인스턴스 + java.lang.reflect.Method)
      --> AbstractHandlerMapping.getHandler가 HandlerExecutionChain으로 감쌈
      --> RequestMappingHandlerAdapter.supports(handler)  "HandlerMethod면 내가 처리"
      --> invokeHandlerMethod에서 실행 대상

 handleMatch가 request에 남긴 속성
      +-- URI_TEMPLATE_VARIABLES_ATTRIBUTE  --> @PathVariable 인자 해석의 입력
      +-- MATRIX_VARIABLES_ATTRIBUTE        --> @MatrixVariable 인자 해석의 입력
      +-- PRODUCIBLE_MEDIA_TYPES_ATTRIBUTE  --> writeWithMessageConverters의 응답 타입 후보
      +-- BEST_MATCHING_PATTERN_ATTRIBUTE   --> 로깅, 관측(metrics)의 URI 태그

 handleNoMatch가 던진 예외
      --> getHandler 밖으로 전파 --> doDispatch의 dispatchException
      --> DefaultHandlerExceptionResolver가 405/415/406/400 응답으로 변환
```

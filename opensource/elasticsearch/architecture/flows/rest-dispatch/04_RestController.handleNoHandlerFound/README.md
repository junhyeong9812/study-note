# RestController.handleNoHandlerFound

상위: [REST 디스패치](../README.md)

후보 하나가 안 맞았을 때 **여기서 끝낼지 다음 후보로 넘길지** 정한다. 돌려주는 `boolean` 이 그 판정이다. [tryAllHandlers](../02_RestController.tryAllHandlers/README.md)의 루프가 이 값을 보고 계속 돌지 멈출지 결정한다.

## 위치

`server` / `org.elasticsearch.rest` / `RestController.java` L652-L677 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/rest/RestController.java#L652-L677))

## 실제 코드

```java
// RestController.java L652-L677
    private boolean handleNoHandlerFound(
        ThreadContext threadContext,
        String rawPath,
        RestRequest.Method method,
        String uri,
        RestChannel channel
    ) {
        // Get the map of matching handlers for a request, for the full set of HTTP methods.
        final Set<RestRequest.Method> validMethodSet = getValidHandlerMethodSet(rawPath);
        if (validMethodSet.contains(method) == false) {
            if (method == RestRequest.Method.OPTIONS) {
                startTrace(threadContext, channel);
                handleOptionsRequest(channel, validMethodSet);
                return true;
            }
            if (validMethodSet.isEmpty() == false) {
                // If an alternative handler for an explicit path is registered to a
                // different HTTP method than the one supplied - return a 405 Method
                // Not Allowed error.
                startTrace(threadContext, channel);
                handleUnsupportedHttpMethod(uri, method, channel, validMethodSet, null);
                return true;
            }
        }
        return false;
    }
```

## 동작 흐름

```text
 L660  validMethodSet = getValidHandlerMethodSet(rawPath)
         이 경로에 등록된 메서드가 무엇무엇인지 모은다

 L661  validMethodSet 에 요청 메서드가 없다
       |
       +-- L662  OPTIONS 인가
       |     +-- L664  handleOptionsRequest(channel, validMethodSet)
       |     +-- L665  return true      여기서 끝
       |
       +-- L667  validMethodSet 이 비어 있지 않다
             +-- L672  handleUnsupportedHttpMethod(uri, method, channel, validMethodSet, null)
             +-- L673  return true      405 로 끝

 L676  return false
         다음 후보로 넘긴다
```

```text
 false 가 나오는 경우가 둘이다

 1. validMethodSet 이 비어 있다
      이 경로에 아무 메서드도 등록돼 있지 않다
      다음 매칭 모드가 다른 경로를 찾아 줄 수 있다

 2. validMethodSet 에 이 메서드가 있는데도 handler 가 null 이었다
      L661 의 조건이 거짓이라 if 블록에 들어가지도 않는다
      경로와 메서드는 맞는데 REST API 버전이 안 맞는 경우가 이것이다

 2번은 결국 모드를 다 돌고 tryAllHandlers L749 의 400 이 된다
 405 가 아니라 400 이 나가는 이유다
```

```text
 OPTIONS 를 핸들러가 처리하지 않는다

 등록 단계에서 막아 둔다
   registerHandlerNoWrap L261
   "OPTIONS 메서드로 등록된 핸들러는 없어야 한다"

 그래서 OPTIONS 는 언제나 이 자리로 온다
 handleOptionsRequest 가 Allow 헤더에 가능한 메서드를 담아 돌려준다
```

## 결과가 쓰이는 곳

```text
 true
      --> tryAllHandlers 가 return 한다 (L732)
      --> 응답은 이미 나갔다

 false
      --> 루프가 다음 매칭 모드로 간다
      --> 모드를 다 쓰면 L749 의 400 이다

 validMethodSet
      --> 405 응답의 Allow 헤더에 들어간다 (L816-818)
          이 갈래는 L667 에서 비어 있지 않음을 이미 확인했으므로 언제나 붙는다
      --> OPTIONS 응답에도 같은 방식으로 붙는다 (L839-841)
          다만 OPTIONS 는 비어 있어도 오는 길이라 그때는 Allow 없이 200 만 나간다
      --> getAllHandlers 를 paramsSupplier 없이 부른다 (L872)
          경로 변수는 버리고 메서드 목록만 모은다
```

## 다루지 않는 것

`handleOptionsRequest` 와 `handleUnsupportedHttpMethod` 의 응답 본문과 헤더 구성, `getValidHandlerMethodSet` 이 `PathTrie` 를 다시 훑는 방식, CORS preflight 와 이 OPTIONS 처리의 관계, `RestApiVersion` 호환성 정책은 같은 뼈대의 곁가지라 요약만 했다.

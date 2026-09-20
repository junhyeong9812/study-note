# RestController.getAllHandlers

상위: [REST 디스패치](../README.md)

경로 하나로 후보 이터레이터를 만든다. 짧은 메서드인데 **부작용이 있다** — 후보를 하나 꺼낼 때마다 요청의 파라미터 맵이 원래대로 되감긴다. 그래서 [tryAllHandlers](../02_RestController.tryAllHandlers/README.md)의 루프가 매번 깨끗한 상태에서 시작한다.

## 위치

`server` / `org.elasticsearch.rest` / `RestController.java` L760-L779 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/rest/RestController.java#L760-L779))

## 실제 코드

```java
// RestController.java L760-L779
    Iterator<MethodHandlers> getAllHandlers(@Nullable RequestParams requestParamsRef, String rawPath) {
        final Supplier<Map<String, String>> paramsSupplier;
        if (requestParamsRef == null) {
            paramsSupplier = () -> null;
        } else {
            // Between retrieving the correct path, we need to reset the parameters,
            // otherwise parameters are parsed out of the URI that aren't actually handled.
            final RequestParams originalParams = RequestParams.copyOf(requestParamsRef);
            paramsSupplier = () -> {
                // PathTrie modifies the request, so reset the params between each iteration
                requestParamsRef.clear();
                requestParamsRef.putAll(originalParams);
                return requestParamsRef;
            };
        }
        // we use rawPath since we don't want to decode it while processing the path resolution
        // so we can handle things like:
        // my_index/my_type/http%3A%2F%2Fwww.google.com
        return handlers.retrieveAll(rawPath, paramsSupplier);
    }
```

## 동작 흐름

```text
 L762  requestParamsRef == null 인가
       |
       +-- null 이면  paramsSupplier = () -> null        L763
       |     경로 변수를 받아 갈 곳이 없다는 뜻이다
       |     디스패치 경로에서는 여기 오지 않는다
       |     checkSupported(L476)와 getValidHandlerMethodSet(L872)이 이쪽을 쓴다
       |
       +-- null 이 아니면                                 L765-773
             L767  originalParams = RequestParams.copyOf(requestParamsRef)
                     지금 상태를 사본으로 떠 둔다
             L768  람다를 만든다. 불릴 때마다
                     L770  requestParamsRef.clear()
                     L771  requestParamsRef.putAll(originalParams)
                     L772  return requestParamsRef

 L778  handlers.retrieveAll(rawPath, paramsSupplier)
         PathTrie 가 매칭 모드마다 paramsSupplier 를 한 번씩 부른다
```

```text
 왜 되감아야 하는가

 주석이 직접 적어 두었다 (L769)
   "PathTrie 가 요청을 수정하므로 반복 사이에 params 를 리셋한다"

 PathTrie 는 /{index}/_doc/{id} 같은 경로에서 변수를 뽑아
 넘겨받은 맵에 채워 넣는다
 그 후보가 안 맞아 다음 모드로 넘어가면
 앞 모드가 채워 둔 변수가 그대로 남아 있게 된다

 그래서 꺼낼 때마다 지우고 사본에서 다시 채운다
```

```text
 rawPath 를 쓰는 이유

 L775-777 주석이 예를 들어 두었다
   my_index/my_type/http%3A%2F%2Fwww.google.com

 경로를 먼저 디코드하면 값 안의 슬래시가 경로 구분자로 보인다
 그래서 경로 해석은 인코딩된 상태로 하고
 변수를 뽑을 때 디코드한다
```

## 결과가 쓰이는 곳

```text
 이터레이터
      --> tryAllHandlers 의 while 이 이것을 돈다 (L722)
      --> 원소가 null 일 수 있다. 그 모드로는 맞는 노드가 없다는 뜻이다

 되감기는 params
      --> 최종적으로 선택된 후보가 채운 값만 남는다
      --> 핸들러가 request.param("index") 로 읽는 것이 그 값이다

 null 인 paramsSupplier
      --> 경로 변수를 버린다. 어떤 메서드가 등록돼 있는지만 알면 되는 곳에서 쓴다
```

## 다루지 않는 것

`PathTrie` 의 자료구조와 매칭 모드별 탐색 규칙, `RequestParams` 의 구현, 경로 변수 디코딩(`RestUtils.REST_DECODER`), `checkSupported` 와 `getValidHandlerMethodSet` 이 이 메서드를 쓰는 방식은 같은 뼈대의 곁가지라 요약만 했다.

# spi

상위: [REST 디스패치](../README.md)

이 흐름이 **바깥에 맡기는 계약** 둘이다. 하나는 핸들러, 하나는 인터셉터다. 둘 다 `RestController` 가 붙잡고 있는 것이고, 구현이 무엇이냐에 따라 흐름의 갈래가 바뀐다.

## RestHandler

요청 하나를 처리하는 계약이다. 이 흐름의 검사 대부분이 이 인터페이스에 질문을 던진다.

`server` / `org.elasticsearch.rest` / `RestHandler.java` L36-L60 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/rest/RestHandler.java#L36-L60))

```java
// RestHandler.java L36-L60 (javadoc 생략)
    void handleRequest(RestRequest request, RestChannel channel, NodeClient client) throws Exception;

    default boolean canTripCircuitBreaker() {
        return true;
    }

    default boolean supportsContentStream() {
        return false;
    }

```

```text
 이 흐름이 핸들러에게 묻는 것

 supportsContentStream()              [05] L518  본문을 흘려 받는가
 supportsReadOnlyFormEncodedPostBody()[06] L543  폼 본문을 읽어도 되는가
 mediaTypesValid(request)             [06] L547  이 Content-Type 을 받는가
 getServerlessScope()                 [06] L556  서버리스에 노출되는가
 canTripCircuitBreaker()              [06] L564  서킷브레이커를 걸 수 있는가
 allowSystemIndexAccessByDefault()    [06] L572  시스템 인덱스를 봐도 되는가
 getConcreteRestHandler()             [02] L736, [06] L599  래퍼를 벗긴 진짜 핸들러
 handleRequest(...)                   [06] L605  실제 처리

 전부 default 가 있어 핸들러는 필요한 것만 재정의한다
```

```text
 구현은 사실상 한 줄기다

 BaseRestHandler 를 상속하는 것이 수백 개다
   grep -rn "extends BaseRestHandler" --include=*.java . | grep "/src/main/java/"
   -> 475 (중간 추상 클래스를 거치는 것은 여기 안 잡힌다)

 직접 implements 하는 것은 손에 꼽는다
   BaseRestHandler        추상 골격 자신
   FilterRestHandler      다른 핸들러를 감싸는 추상 클래스
   RestFavIconHandler     /favicon.ico (RestController 안의 내부 클래스)
```

```text
 래퍼가 하나 있다 (FilterRestHandler)

 DeprecationRestHandler 가 유일한 구현이고
 deprecated 라우트를 등록할 때 원래 핸들러를 감싼다 (RestController L175)

 handleRequest 가 경고를 찍고 안쪽으로 넘긴다
   DeprecationRestHandler L79-93  경고 (호환성 여부 x WARN/CRITICAL 네 갈래)
   DeprecationRestHandler L95     getDelegate().handleRequest(...)

 그래서 deprecated 라우트에서는 [06] 과 [07] 사이에 홉이 하나 더 있다

 FilterRestHandler 가 위임하는 것은 여섯 개다 (L26-54)
   getConcreteRestHandler, routes, allowSystemIndexAccessByDefault,
   canTripCircuitBreaker, supportsReadOnlyFormEncodedPostBody, mediaTypesValid

 supportsContentStream 은 여기 없다
 위임하지 않으므로 래퍼는 기본값 false 를 돌려준다
 즉 deprecated 로 등록된 스트리밍 핸들러는 집계 경로로 간다
```

## RestInterceptor

핸들러를 부르기 전에 끼어들 자리다.

`server` / `org.elasticsearch.rest` / `RestInterceptor.java` L18-L40 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/rest/RestInterceptor.java#L18-L40))

```java
// RestInterceptor.java L18-L40 (javadoc 생략)
public interface RestInterceptor {

    void intercept(RestRequest request, RestChannel channel, RestHandler targetHandler, ActionListener<Boolean> listener) throws Exception;

    default boolean allowsBrowserSafelistedContentType(RestRequest request) {
        return false;
    }
}

```

```text
 구현은 하나뿐이다

 SecurityRestFilter (x-pack)

 RestController 생성자의 람다 (L137-139) 는 구현이 아니라 기본값이다
 어떤 플러그인도 인터셉터를 주지 않았을 때만 쓰인다 (ActionModule L512-516)

 보안 플러그인이 있으면 보안을 꺼도 SecurityRestFilter 가 꽂힌다
 Security.getRestHandlerInterceptor 가 enabled 와 무관하게 이것을 돌려주기 때문이다
 꺼져 있을 때의 통과는 SecurityRestFilter 안에서 일어난다
```

```text
 리스너를 받지만 대개 동기다

 intercept 는 ActionListener<Boolean> 을 받는다
 그런데 기본 경로에서는 그 리스너가 같은 스레드에서 바로 불린다

 true   핸들러를 부른다
 false  아무 것도 하지 않는다. 인터셉터가 자기 응답을 이미 보냈다
 실패   sendFailure 로 간다
```

## 결과가 쓰이는 곳

```text
 RestHandler 구현
      --> 핸들러마다 다른 정책이 [06] 의 검사 결과를 바꾼다
      --> prepareRequest 가 이 흐름의 종점이자 다음 흐름의 시작이다

 FilterRestHandler 의 부분 위임
      --> 래핑이 동작을 바꾸는 자리가 생긴다
      --> 위임 목록에 없는 메서드는 래퍼의 기본값이 나간다

 RestInterceptor 구현 유무
      --> 있으면 요청마다 한 번 더 질문이 간다
      --> 없으면 그 자리가 상수 true 다
```

## 다루지 않는 것

`RestHandler.Route` 와 라우트 선언, `RestApiVersion` 과 호환성 라우트, `SecurityRestFilter` 내부의 인증과 감사 로깅, operator privileges, `RestServerActionPlugin` 이 `RestController` 자체를 교체하는 경로, 핸들러 등록 시의 검증(`validateOnlyGetAndPostRoutesAreDeclared` 등)은 같은 뼈대의 곁가지라 요약만 했다.

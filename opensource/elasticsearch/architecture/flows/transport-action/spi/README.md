# spi

상위: [트랜스포트 액션](../README.md)

이 흐름이 **바깥에 맡기는 계약** 둘이다. 필터와 체인. 플러그인이 액션 실행에 끼어드는 유일한 통로다.

## ActionFilter

`server` / `org.elasticsearch.action.support` / `ActionFilter.java` L25-L37 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/support/ActionFilter.java#L25-L37))

```java
// ActionFilter.java L25-L37 (javadoc 생략)
    int order();

    <Request extends ActionRequest, Response extends ActionResponse> void apply(
        Task task,
        String action,
        Request request,
        ActionListener<Response> listener,
        ActionFilterChain<Request, Response> chain
    );
```

```text
 구현이 다섯인데 성격이 다르다

 SecurityActionFilter                     x-pack. 인증과 인가
 SuppressWaitForActiveShardsActionFilter  x-pack. 요청을 변형한다
 MlUpgradeModeActionFilter                x-pack. 업그레이드 중 액션을 막는다
 MappedActionFilters                      프레임워크. 액션별 체인을 또 돌린다
 ActionFilter.Simple                      추상. 체인 호출을 대신해 준다

 Security 와 Ml 은 플러그인이 켜져 있을 때만 등록된다
```

```text
 순서는 order() 오름차순이다 (ActionFilters L27)

 SecurityActionFilter                     Integer.MIN_VALUE   L144
 MappedActionFilters                      0                   L37
 SuppressWaitForActiveShardsActionFilter  0                   L25
 MlUpgradeModeActionFilter                Integer.MAX_VALUE   L187

 보안이 언제나 맨 앞이고 ml 검사가 맨 뒤다

 가운데 둘은 order 가 같다
 ActionFilters 는 Set 을 배열로 바꿔 정렬하므로 (L25-27)
 동률끼리의 상대 순서는 소스만 보고 정할 수 없다
```

```text
 Simple 은 체인을 대신 불러 준다

 ActionFilter.Simple L44-63
   apply(action, request, listener) 가 boolean 을 돌려주고
   true 면 chain.proceed 를 대신 불러 준다 (L53-55)

 그래서 Simple 을 상속하면 체인을 신경 쓰지 않아도 된다
 대신 비동기 필터는 만들 수 없다
 그 경우 ActionFilter 를 직접 구현한다 (SecurityActionFilter 가 그렇다)
```

## ActionFilterChain

필터가 다음으로 넘길 때 쓰는 계약이다.

`server` / `org.elasticsearch.action.support` / `ActionFilterChain.java` L20-L27 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/support/ActionFilterChain.java#L20-L27))

```java
// ActionFilterChain.java L20-L27 (javadoc 생략)
public interface ActionFilterChain<Request extends ActionRequest, Response extends ActionResponse> {

    void proceed(Task task, String action, Request request, ActionListener<Response> listener);
}
```

```text
 구현이 둘이고 성질이 다르다

 RequestFilterChain          TransportAction L105-145
   index 가 AtomicInteger (L111)
   과다 호출을 잡아 IllegalStateException 을 리스너로 보낸다 (L137-138)
   끝에서 releaseRef 를 닫고 액션을 부른다 (L134-135)

 MappedFilterChain           MappedActionFilters L52-74
   index 가 plain int (L58)
   과다 호출 방어가 없다
   끝에서 바깥 체인으로 넘긴다 (L71)
```

## MappedActionFilter

액션 하나에만 붙는 필터다. `MappedActionFilters` 가 이들을 모아 바깥 체인의 한 칸으로 들어간다.

`server` / `org.elasticsearch.action.support` / `MappedActionFilters.java` L40-L50 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/support/MappedActionFilters.java#L40-L50))

```java
// MappedActionFilters.java L40-L50
    @Override
    public <Request extends ActionRequest, Response extends ActionResponse> void apply(
        Task task,
        String action,
        Request request,
        ActionListener<Response> listener,
        ActionFilterChain<Request, Response> outerChain
    ) {
        var chain = new MappedFilterChain<>(this.filtersByAction.getOrDefault(action, List.of()), outerChain);
        chain.proceed(task, action, request, listener);
    }
```

```text
 체인이 두 겹이 되는 자리

 바깥 체인이 MappedActionFilters.apply 를 부른다        L41
   액션 이름으로 붙은 필터들을 고른다                    L48
   없으면 빈 목록이다
   내부 체인을 만들어 돌린다                             L48-49
     다 돌면 바깥 체인으로 넘긴다                        L71

 MappedActionFilter 가 하나도 없으면
 MappedActionFilters 자체가 바깥 체인에 안 들어간다
 (ActionModule L838-840)
```

```text
 구현을 세는 방법이 둘이다

 직접 구현한 타입은 셋이지만 그중 둘이 추상이다
   ApiFilteringActionFilter        추상. 구체 하위가 비테스트에 없다
   DotPrefixValidator              추상. 구체 하위가 셋
   ShardBulkInferenceActionFilter  구체

 실제로 등록될 수 있는 구체 필터는 넷이다
   AutoCreateDotValidator, CreateIndexDotValidator, IndexTemplateDotValidator,
   ShardBulkInferenceActionFilter
```

## 결과가 쓰이는 곳

```text
 필터 구현
      --> 액션 실행 전에 요청을 검사하거나 바꾼다
      --> 응답을 가로채 변형할 수도 있다 (ApiFilteringActionFilter 가 그렇다)
      --> 체인을 안 부르면 액션이 아예 안 돈다

 order
      --> 보안이 맨 앞이라 다른 필터가 인증 결과를 전제할 수 있다

 두 겹 체인
      --> 모든 액션에 붙는 필터와 한 액션에만 붙는 필터를 나눈다
      --> 액션마다 필터 목록을 훑는 비용을 안 치른다
```

## 다루지 않는 것

`SecurityActionFilter` 의 인증·인가 내부와 `SubscribableListener` 사용, `ShardBulkInferenceActionFilter` 의 추론 처리, `DotPrefixValidator` 의 검증 규칙, 플러그인이 필터를 등록하는 경로(`ActionPlugin.getActionFilters`, `getMappedActionFilters`), `ActionModule` 의 조립 순서는 같은 뼈대의 곁가지라 요약만 했다.

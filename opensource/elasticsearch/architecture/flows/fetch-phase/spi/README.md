# spi

상위: [페치 페이즈](../README.md)

이 페이즈가 기대는 **샤드 세기 장치 하나와 검색 컨텍스트 해제 규약 하나**다. 둘 다 이 페이즈 밖에 있고, 두 번째가 특히 까다롭다 — 해제는 보장이 아니라 시도다.

## CountedCollector

`server` / `org.elasticsearch.action.search` / `CountedCollector.java` L22-L32 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/search/CountedCollector.java#L22-L32))

```java
// CountedCollector.java L22-L32
    private final SearchPhaseResults<R> resultConsumer;
    private final CountDown counter;
    private final Runnable onFinish;
    private final AbstractSearchAsyncAction<?> context;

    CountedCollector(SearchPhaseResults<R> resultConsumer, int expectedOps, Runnable onFinish, AbstractSearchAsyncAction<?> context) {
        this.resultConsumer = resultConsumer;
        this.counter = new CountDown(expectedOps);
        this.onFinish = onFinish;
        this.context = context;
    }
```

세고, 0이 되면 끝낸다.

`server` / `org.elasticsearch.action.search` / `CountedCollector.java` L38-L64 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/search/CountedCollector.java#L38-L64))

```java
// CountedCollector.java L38-L64 (javadoc 생략)
    void countDown() {
        assert counter.isCountedDown() == false : "more operations executed than specified";
        if (counter.countDown()) {
            onFinish.run();
        }
    }

    void onResult(R result) {
        // Accumulate the per-shard metrics into the action's merged reference before consuming
        context.accumulateDirectoryMetrics(result.getDirectoryMetrics());
        resultConsumer.consumeResult(result, this::countDown);
    }

    void onFailure(final int shardIndex, @Nullable SearchShardTarget shardTarget, Exception e) {
        try {
            context.onShardFailure(shardIndex, shardTarget, e);
        } finally {
            countDown();
        }
    }
```

```text
 [검색 페이즈] 1회차와 다른 회계다

 1회차     outstandingShards      AtomicInteger
           재시도해도 한 번만 내린다
           4-arg onShardFailure 가 재시도를 판정한다

 이 페이즈 CountedCollector       CountDown
           재시도가 없다
           3-arg onShardFailure 만 부른다 (L60)
           그래서 샤드가 실패하면 그것으로 끝이다

 DfsQueryPhase 의 클래스 주석이 그 사정을 적어 두었다 (L38-40)
   샤드가 실패해도 다른 샤드에서 재시도하지 않는다
```

```text
 세는 기준이 페이즈마다 다르다

 FetchSearchPhase   context.results.getNumShards()   L99 -> L137 -> L141
 RankFeaturePhase   context.getNumShards()           L102, L105

 뒤엣것은 skippedCount 를 더한 값이다
 (AbstractSearchAsyncAction L613)

 can_match 로 걸러진 샤드가 있으면 두 값이 다르다
```

```text
 정확히 expectedOps 번 세는가

 정상 경로는 그렇다
   가져올 것 없는 샤드   countDown 한 번 (L158)
   요청을 보낸 샤드       성공이든 실패든 한 번

 초과는 구조적으로 막혀 있다
   CountDown 이 1->0 전이에서만 true 를 돌려주므로
   onFinish 가 두 번 돌지 않는다
   assert 도 초과를 잡는다 (L39)

 미달은 막혀 있지 않다
   executeFetch 가 리스너 등록 전에 던지면 (L210, L246)
   그 샤드와 남은 샤드가 세어지지 않는다
   onResult 안에서 countDown 전에 던져도 마찬가지다

 다만 그 예외들이 페이즈를 실패로 끝내므로
 검색이 영영 매달리지는 않는다
```

## 검색 컨텍스트 해제

쿼리 페이즈가 끝나면 샤드마다 컨텍스트가 열려 있다. 페치할 문서가 그 안에 있기 때문이다. 상위 N건에 못 든 샤드의 것은 닫아야 한다.

`server` / `org.elasticsearch.action.search` / `SearchPhase.java` L69-L93 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/search/SearchPhase.java#L69-L93))

```java
// SearchPhase.java L69-L93
    protected static void releaseIrrelevantSearchContext(SearchPhaseResult searchPhaseResult, AbstractSearchAsyncAction<?> context) {
        // we only release search context that we did not fetch from, if we are not scrolling
        // or using a PIT and if it has at least one hit that didn't make it to the global topDocs
        if (searchPhaseResult == null) {
            return;
        }
        // phaseResult.getContextId() is the same for query & rank feature results
        SearchPhaseResult phaseResult = searchPhaseResult.queryResult() != null
            ? searchPhaseResult.queryResult()
            : searchPhaseResult.rankFeatureResult();
        if (phaseResult != null
            && (phaseResult.hasSearchContext()
                || (phaseResult instanceof QuerySearchResult q && q.isPartiallyReduced() && q.getContextId() != null))
            && context.getRequest().scroll() == null
            && (context.isPartOfPointInTime(phaseResult.getContextId()) == false)) {
            try {
                context.getLogger().trace("trying to release search context [{}]", phaseResult.getContextId());
                SearchShardTarget shardTarget = phaseResult.getSearchShardTarget();
                Transport.Connection connection = context.getConnection(shardTarget.getClusterAlias(), shardTarget.getNodeId());
                context.sendReleaseSearchContext(phaseResult.getContextId(), connection);
            } catch (Exception e) {
                context.getLogger().trace("failed to release context", e);
            }
        }
    }
```

```text
 게이트가 다섯 겹이다

 L72  결과가 null 이면            그냥 돌아간다
 L79  phaseResult 가 null 이면    아무 일도 안 한다
 L80  컨텍스트가 없으면           (hasSearchContext 도 아니고
                                   부분 리듀스된 쿼리 결과도 아니면)
 L82  스크롤이면                  의도적으로 유지한다
 L83  PIT 에 속하면               의도적으로 유지한다

 다섯을 다 지나야 해제 요청을 보낸다
```

```text
 해제는 보장이 아니라 시도다

 L89  catch 가 실패를 삼킨다. trace 로그만 남긴다
 그리고 sendReleaseSearchContext 는
 connection 이 null 이면 조용히 넘어간다

 즉 "놓아주는 코드를 불렀다"가
 "놓아졌다"를 뜻하지 않는다
```

```text
 해제하는 자리가 넷이다

 코디네이터가 releaseIrrelevantSearchContext 로
   FetchSearchPhase L116   가져올 문서가 0개일 때 전부
   FetchSearchPhase L173   이번에 안 쓸 샤드
   FetchSearchPhase L234   페치가 실패했을 때

 페이즈가 실패하면 일괄로
   AbstractSearchAsyncAction L829-841 raisePhaseFailure
   판정이 다르다. contextId 가 있고 PIT 가 아니면 닫는다
   스크롤 여부를 보지 않는다

 그리고 데이터 노드가 스스로 닫는 경우가 있다
   샤드 1개 최적화 경로는 코디네이터가 한 번도 안 부른다
   데이터 노드가 query+fetch 를 한 컨텍스트에서 끝내고 닫는다
```

```text
 새는 길이 하나 있다

 executeFetch 의 getConnection 이 실패하면 (L241-243)
   finally 가 releaseIrrelevantSearchContext 를 부르는데
   그 안 L87 이 같은 getConnection 을 다시 부른다
   같은 이유로 실패하고 L89 가 삼킨다

 이어서 raisePhaseFailure 도 getConnection 을 쓴다 (L834)
 노드에 닿지 못하면 세 번 다 실패한다

 남은 컨텍스트는 데이터 노드의 keep-alive 만료로 정리된다
```

## 결과가 쓰이는 곳

```text
 CountedCollector
      --> 0이 되는 순간이 페이즈의 끝이다
      --> 그 자리에서 다음 페이즈까지 동기로 이어질 수 있다

 컨텍스트 해제
      --> 샤드의 리더와 메모리를 붙잡고 있는 것을 놓는다
      --> 늦게 놓으면 동시 검색 수가 줄어든다
      --> 못 놓으면 keep-alive 만큼 더 잡고 있는다

 스크롤과 PIT
      --> 일부러 안 닫는다. 다음 요청이 같은 컨텍스트를 쓴다
      --> 그래서 이 판정에 둘이 따로 들어 있다
```

## 다루지 않는 것

`CountDown` 의 구현, `ArraySearchPhaseResults` 의 참조 수 관리, `hasSearchContext` 의 결과 타입별 구현, `sendFreeContext` 와 전송 계층, 데이터 노드 쪽 `SearchService` 의 컨텍스트 수명과 keep-alive, PIT 와 스크롤의 컨텍스트 재사용 규칙은 같은 뼈대의 곁가지라 요약만 했다.

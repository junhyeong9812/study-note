# AbstractSearchAsyncAction.doRun

상위: [검색 페이즈](../README.md)

샤드마다 요청을 거는 루프다. **다만 이것이 기본 경로가 아니다** — `SearchQueryThenFetchAsyncAction` 이 오버라이드하고 그쪽이 기본으로 켜져 있다. 이 메서드는 배치 쿼리를 끈 경우와 dfs 경로에서 돈다.

## 위치

`server` / `org.elasticsearch.action.search` / `AbstractSearchAsyncAction.java` L264-L278 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/search/AbstractSearchAsyncAction.java#L264-L278))

## 실제 코드

```java
// AbstractSearchAsyncAction.java L264-L278
    protected void doRun(Map<SearchShardIterator, Integer> shardIndexMap) {
        doCheckNoMissingShards(getName(), request, shardsIts);
        for (int i = 0; i < shardsIts.size(); i++) {
            final SearchShardIterator shardRoutings = shardsIts.get(i);
            assert shardRoutings.skip() == false;
            assert shardIndexMap.containsKey(shardRoutings);
            int shardIndex = shardIndexMap.get(shardRoutings);
            final SearchShardTarget routing = shardRoutings.nextOrNull();
            if (routing == null) {
                failOnUnavailable(shardIndex, shardRoutings);
            } else {
                performPhaseOnShard(shardIndex, shardRoutings, routing);
            }
        }
    }
```

오버라이드가 먼저 본다. 꺼져 있을 때만 위 코드로 내려온다.

`server` / `org.elasticsearch.action.search` / `SearchQueryThenFetchAsyncAction.java` L509-L512 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/search/SearchQueryThenFetchAsyncAction.java#L509-L512))

```java
// SearchQueryThenFetchAsyncAction.java L509-L512
        if (this.batchQueryPhase == false) {
            super.doRun(shardIndexMap);
            return;
        }
```

## 동작 흐름

```text
 L265  doCheckNoMissingShards(getName(), request, shardsIts)
         부분 결과를 허용하지 않는데 복제본이 하나도 없는 샤드가 있으면
         SearchPhaseExecutionException 을 던진다 (SearchPhase L58-61)
         그 예외는 [02] 의 catch 가 받아 onPhaseFailure 로 간다

 L266  샤드마다
       L271  routing = shardRoutings.nextOrNull()
       L272  null 이면 failOnUnavailable(shardIndex, shardRoutings)   -> [06]
       L275  아니면 performPhaseOnShard(shardIndex, shardRoutings, routing)  -> [05]
```

```text
 기본 경로는 여기가 아니다

 SearchQueryThenFetchAsyncAction L508 이 오버라이드한다
 L509 가 batchQueryPhase 를 보고 false 일 때만 super 로 내려온다

 그 설정의 기본값이 true 다
   SearchService L325-330  search.batched_query_phase = true

 즉 평범한 검색의 query 페이즈는 이 루프를 돌지 않는다
```

```text
 배치 경로가 다르게 하는 것

 로컬 샤드는 그대로 performPhaseOnShard        SQTF L528-529
 원격 샤드는 노드별 NodeQueryRequest 에 묶는다  SQTF L530-550
   노드당 샤드가 하나뿐이면 묶지 않는다          SQTF L554
   구버전 노드면 묶지 않는다                     SQTF L567-571

 묶은 것은 한 번에 보낸다                        SQTF L582
 응답에서 결과를 하나씩 풀어
   성공이면 onShardResult                        SQTF L615
   실패면 onShardFailure (4-arg)                 SQTF L610

 즉 [05] 를 건너뛰고 [06]/[07] 로 바로 들어간다
 노드 하나가 통째로 실패하면 그 노드의 샤드마다
 4-arg onShardFailure 를 돌려 샤드 단위 재시도로 분해한다  SQTF L692
```

```text
 failOnUnavailable 도 실패 경로로 합류한다

 routing 이 null 이라는 것은 쓸 복제본이 없다는 뜻이다

 failOnUnavailable (L321-324) 은
 NoShardAvailableActionException 을 만들어
 4-arg onShardFailure 에 넣는다

 그래서 재시도 판정도 거치고 finishOneShard 도 거친다
 "없는 샤드"와 "실패한 샤드"가 같은 회계를 쓴다
```

## 결과가 쓰이는 곳

```text
 샤드별 요청
      --> 각자 비동기로 응답이 온다
      --> 순서는 보장되지 않는다

 shardIndex
      --> 결과와 실패를 제자리에 넣는 키다
      --> 재시도해도 같은 번호를 쓴다

 doCheckNoMissingShards
      --> 부분 결과를 허용하지 않는 요청의 조기 차단이다
      --> 샤드 하나라도 복제본이 없으면 아예 시작하지 않는다
```

## 다루지 않는 것

배치 쿼리 경로(`SearchQueryThenFetchAsyncAction.doRun`)의 노드별 묶기와 응답 처리, BwC 폴백(`executeWithoutBatching`), `NodeQueryRequest` 와 데이터 노드 쪽 처리, `SearchShardIterator` 가 복제본을 내놓는 순서, `doCheckNoMissingShards` 의 메시지 조립은 같은 뼈대의 곁가지라 요약만 했다.

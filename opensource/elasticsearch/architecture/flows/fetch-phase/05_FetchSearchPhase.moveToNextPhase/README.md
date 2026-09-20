# FetchSearchPhase.moveToNextPhase

상위: [페치 페이즈](../README.md)

**결과를 합쳐 다음 페이즈로 넘긴다.** 열세 줄인데, 병합이 실제로 일어나는 자리가 여기가 아니라 넘기는 람다 안이라는 점이 중요하다.

## 위치

`server` / `org.elasticsearch.action.search` / `FetchSearchPhase.java` L271-L283 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/search/FetchSearchPhase.java#L271-L283))

## 실제 코드

```java
// FetchSearchPhase.java L271-L283
    private void moveToNextPhase(
        AtomicArray<? extends SearchPhaseResult> fetchResultsArr,
        SearchPhaseController.ReducedQueryPhase reducedQueryPhase,
        long phaseStartTimeInNanos
    ) {
        context.getSearchResponseMetrics()
            .recordSearchPhaseDuration(getName(), System.nanoTime() - phaseStartTimeInNanos, context.getSearchRequestAttributes());
        context.executeNextPhase(NAME, () -> {
            var resp = SearchPhaseController.merge(context.getRequest().scroll() != null, reducedQueryPhase, fetchResultsArr);
            context.addReleasable(resp);
            return nextPhase(resp, searchPhaseShardResults);
        });
    }
```

## 동작 흐름

```text
 L276  페이즈 소요시간을 기록한다
 L278  context.executeNextPhase(NAME, 서플라이어)
         서플라이어 안에서
           L279  resp = SearchPhaseController.merge(...)
           L280  context.addReleasable(resp)
           L281  return nextPhase(resp, searchPhaseShardResults)
                   = new ExpandSearchPhase(...)   L75
```

```text
 들어오는 길이 셋이다

 L109  샤드 1개 최적화. 페치를 안 했다
 L117  가져올 문서가 0개. 빈 배열을 넘긴다
 L142  카운터가 0이 됐다. 페치 결과를 넘긴다

 셋 다 같은 메서드로 모이고
 차이는 첫 인자로 넘기는 결과 배열뿐이다
```

```text
 병합이 여기서 안 일어난다

 merge 는 L279 에 있고 그것은 람다 안이다
 그 람다는 executeNextPhase 의 L413 에서야 실행된다

 그런데 executeNextPhase 는 람다를 부르기 전에
 실패 판정을 먼저 한다 (AbstractSearchAsyncAction L349-396)
   전 샤드 실패
   부분 결과를 허용하지 않는데 성공 수가 모자람
   전부 내부 취소

 그 넷 중 하나에 걸리면 람다가 아예 안 불린다
 merge 도, ExpandSearchPhase 생성도 일어나지 않는다

 즉 "다음은 언제나 ExpandSearchPhase" 는 반만 맞다
 nextPhase 자체에는 분기가 없지만, 거기까지 못 갈 수 있다
```

```text
 merge 의 예외는 누가 받는가

 L413 은 executePhase 의 try 밖이다
 그 try 는 phase.run() 만 감싸는데 (L430-439)
 이 페이즈의 run 은 포크만 하고 즉시 반환했다

 그래서 [검색 페이즈]의 그 catch 는 못 받는다
 대신 마지막 countDown 이 어디서 났느냐에 따라
   innerRun 스택이면    [01] 의 onFailure        L88
   페치 응답 스택이면   innerOnResponse 의 catch  L220

 어느 쪽이든 onPhaseFailure 로 간다
```

```text
 addReleasable 이 지금 푸는 것이 아니다

 L280 이 등록하는 resp 는
 doneFuture 가 완료될 때 닫힌다 (AbstractSearchAsyncAction L213-220)

 그 doneFuture 는 최종 리스너 직전에 완료된다 (L173)
 즉 검색 요청 전체가 응답을 내는 순간이다

 페이즈가 끝날 때가 아니다
```

## 결과가 쓰이는 곳

```text
 SearchResponseSections
      --> 히트, 집계, 제안이 합쳐진 것이다
      --> ExpandSearchPhase 가 이것을 받아 collapse 를 펼친다

 페이즈 소요시간
      --> 페치가 전체 지연에서 차지하는 몫이 보인다
      --> 쿼리는 빠른데 페치가 느리면 문서가 큰 것이다

 searchPhaseShardResults
      --> 다음 페이즈에도 그대로 넘어간다
      --> ExpandSearchPhase 가 컨텍스트 해제에 쓸 수 있게
```

## 다루지 않는 것

`SearchPhaseController.merge` 의 히트 병합과 제안 병합, `SearchResponseSections` 의 구조, `ExpandSearchPhase` 의 collapse 처리, `executeNextPhase` 의 실패 판정(자세한 것은 [검색 페이즈](../../search-phases/08_AbstractSearchAsyncAction.executeNextPhase/README.md)에 있다), `addReleasable` 의 등록 순서는 같은 뼈대의 곁가지라 요약만 했다.

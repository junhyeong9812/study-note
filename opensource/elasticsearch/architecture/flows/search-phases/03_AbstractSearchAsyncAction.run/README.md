# AbstractSearchAsyncAction.run

상위: [검색 페이즈](../README.md)

첫 페이즈의 본문이다. **`final` 이라 액션 서브클래스가 바꿀 수 없고**, 두 번째 페이즈부터는 다른 클래스의 `run()` 이 돈다. 즉 이 문서는 체인의 첫 칸에만 해당한다.

## 위치

`server` / `org.elasticsearch.action.search` / `AbstractSearchAsyncAction.java` L251-L262 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/search/AbstractSearchAsyncAction.java#L251-L262))

## 실제 코드

```java
// AbstractSearchAsyncAction.java L251-L262
    protected final void run() {
        phaseStartTimeInNanos = System.nanoTime();
        if (outstandingShards.get() == 0) {
            onPhaseDone();
            return;
        }
        final Map<SearchShardIterator, Integer> shardIndexMap = Maps.newHashMapWithExpectedSize(shardIterators.length);
        for (int i = 0; i < shardIterators.length; i++) {
            shardIndexMap.put(shardIterators[i], i);
        }
        doRun(shardIndexMap);
    }
```

## 동작 흐름

```text
 L252  phaseStartTimeInNanos = System.nanoTime()
         페이즈 소요시간의 기준. onPhaseDone 이 여기서 잰다

 L253  outstandingShards.get() == 0
       +-- L254  onPhaseDone()   샤드 작업 없이 바로 다음 페이즈로
       +-- L255  return

 L257  shardIndexMap 을 만든다
         SearchShardIterator -> 인덱스 번호
 L261  doRun(shardIndexMap)
```

```text
 시작하자마자 0인 경우가 있다

 outstandingShards 의 초기값은 shardsIts.size() 다 (L156)
 getNumShards() 와 다르다 — 그쪽은 results.getNumShards() + skippedCount (L613)

 can_match 단계에서 샤드가 전부 걸러지면
 shardsIts 는 비지만 skippedCount 는 0이 아니다
 그때 이 갈래로 온다

 검색할 것이 없지만 "볼 것이 없었다"는 응답은 만들어야 하므로
 페이즈는 그대로 진행한다
```

```text
 final 인 이유

 액션 서브클래스는 셋이다
   SearchQueryThenFetchAsyncAction
   SearchDfsQueryThenFetchAsyncAction
   TransportOpenPointInTimeAction 의 익명 액션

 셋 다 run 을 못 바꾼다
 대신 doRun 을 바꿀 수 있고 (L264 는 final 이 아니다)
 실제로 SearchQueryThenFetchAsyncAction L508 이 바꾼다

 즉 "페이즈 시작 의례"는 고정이고
 "샤드에 어떻게 뿌리는가"만 갈아끼운다
```

```text
 shardIndexMap 이 왜 필요한가

 shardsIts 는 리스트이고 순서가 있다
 그런데 doRun 이 그 순서대로만 도는 것이 아니다
   배치 경로는 노드별로 다시 묶는다

 결과를 제자리에 넣으려면 이터레이터마다 원래 번호를 알아야 한다
 그 번호가 results 배열의 인덱스가 된다
```

## 결과가 쓰이는 곳

```text
 phaseStartTimeInNanos
      --> onPhaseDone 이 이 값으로 페이즈 소요시간을 기록한다 (L865)
      --> 페이즈마다 새로 잡힌다. 누적이 아니다

 shardIndexMap
      --> doRun 이 샤드마다 번호를 붙이는 데 쓴다
      --> 그 번호로 onShardResult 가 결과를 제자리에 넣는다

 onPhaseDone 직행
      --> 샤드 작업을 건너뛴다
      --> 그래도 executeNextPhase 의 실패 판정은 거친다
```

## 다루지 않는 것

`outstandingShards` 와 `skippedCount` 가 정해지는 생성자 단계, `can_match` 사전 필터링, `SearchShardIterator` 의 구조, 두 번째 이후 페이즈들의 `run()` 구현은 같은 뼈대의 곁가지라 요약만 했다.

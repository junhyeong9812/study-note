# AbstractSearchAsyncAction.start

상위: [검색 페이즈](../README.md)

체인의 **첫 칸을 띄운다**. 하는 일은 둘뿐이다. 검색할 샤드가 하나도 없으면 빈 응답으로 끝내고, 있으면 자기 자신을 첫 페이즈로 실행한다.

## 위치

`server` / `org.elasticsearch.action.search` / `AbstractSearchAsyncAction.java` L232-L248 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/search/AbstractSearchAsyncAction.java#L232-L248))

## 실제 코드

```java
// AbstractSearchAsyncAction.java L232-L248
    public final void start() {
        if (getNumShards() == 0) {
            // no search shards to search on, bail with empty response
            // (it happens with search across _all with no indices around and consistent with broadcast operations)
            int trackTotalHitsUpTo = request.source() == null ? SearchContext.DEFAULT_TRACK_TOTAL_HITS_UP_TO
                : request.source().trackTotalHitsUpTo() == null ? SearchContext.DEFAULT_TRACK_TOTAL_HITS_UP_TO
                : request.source().trackTotalHitsUpTo();
            // total hits is null in the response if the tracking of total hits is disabled
            boolean withTotalHits = trackTotalHitsUpTo != SearchContext.TRACK_TOTAL_HITS_DISABLED;
            sendSearchResponse(
                withTotalHits ? SearchResponseSections.EMPTY_WITH_TOTAL_HITS : SearchResponseSections.EMPTY_WITHOUT_TOTAL_HITS,
                new AtomicArray<>(0)
            );
            return;
        }
        executePhase(this);
    }
```

## 동작 흐름

```text
 L233  getNumShards() == 0
       +-- L236  trackTotalHitsUpTo 를 셋 중에서 고른다
       |           source 가 null 이면 기본값
       |           trackTotalHitsUpTo() 가 null 이면 기본값
       |           아니면 그 값
       +-- L240  withTotalHits = DISABLED 가 아닌가
       +-- L241  sendSearchResponse(빈 결과, 빈 배열)
       +-- L245  return

 L247  executePhase(this)
```

```text
 자기 자신을 넘긴다

 AbstractSearchAsyncAction 이 SearchPhase 를 상속한다 (L79)
 그래서 executePhase(this) 가 성립한다

 즉 첫 페이즈는 별도 객체가 아니라 액션 자신이다
 그 페이즈의 run() 이 [03] 이고
 샤드에 흩어지는 [04], [05] 도 액션 안에 있다

 두 번째 페이즈부터는 다른 클래스의 객체가 온다
```

```text
 샤드 0개가 왜 따로 있는가

 주석이 이유를 적어 두었다 (L234-235)
   인덱스가 없는 상태에서 _all 을 검색하면 이렇게 된다
   브로드캐스트 연산과 일관되게 빈 응답을 준다

 이 길은 페이즈를 하나도 거치지 않는다
 체인 길이가 0인 유일한 경우다
```

```text
 total hits 를 세 갈래로 고른다

 요청이 아무 말도 안 했으면 기본값
 명시적으로 껐으면 응답의 total 이 null 이 된다

 빈 응답조차 그 설정을 따른다
 EMPTY_WITH_TOTAL_HITS 와 EMPTY_WITHOUT_TOTAL_HITS 가 따로 있는 이유다
```

## 결과가 쓰이는 곳

```text
 executePhase(this)
      --> 체인의 첫 칸이다
      --> 그 안에서 run() 이 불리고 샤드로 흩어진다

 빈 응답
      --> 페이즈를 거치지 않으므로 집계도 정렬도 없다
      --> sendSearchResponse 가 바로 리스너를 완료시킨다

 getNumShards()
      --> results.getNumShards() + skippedCount 다 (L613)
      --> can_match 로 걸러진 샤드도 센다
      --> 그래서 이 값이 0이라는 것은 정말 볼 것이 없다는 뜻이다
```

## 다루지 않는 것

`sendSearchResponse` 가 응답을 조립하고 실패를 판정하는 내부, `SearchResponseSections` 의 빈 인스턴스, `trackTotalHitsUpTo` 의 의미와 기본값, `CanMatchPreFilterSearchPhase` 가 이 앞에서 샤드를 걸러내는 과정은 같은 뼈대의 곁가지라 요약만 했다.

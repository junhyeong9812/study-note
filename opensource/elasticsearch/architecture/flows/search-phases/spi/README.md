# spi

상위: [검색 페이즈](../README.md)

페이즈 계약 하나와 **전이 표**다. 계약은 단순한데(이름 하나와 `run()` 하나) 전이 표가 이 흐름의 실체다 — 체인이 몇 칸이고 어디서 끝나는지가 거기 있다.

## SearchPhase

`server` / `org.elasticsearch.action.search` / `SearchPhase.java` L23-L36 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/search/SearchPhase.java#L23-L36))

```java
// SearchPhase.java L23-L36 (javadoc 생략)
    private final String name;

    protected SearchPhase(String name) {
        this.name = Objects.requireNonNull(name, "name must not be null");
    }

    protected abstract void run();

    public String getName() {
        return name;
    }
```

```text
 계약이 둘뿐이다

 name  실패 응답과 메트릭에 실리는 이름
 run   그 페이즈가 하는 일

 다음 페이즈를 누구에게 넘길지는 계약에 없다
 각 구현이 알아서 context.executeNextPhase 를 부른다
```

```text
 구현이 열이다

 명명 클래스 여섯
   AbstractSearchAsyncAction   L79   액션 자신. 체인의 첫 칸
   DfsQueryPhase               L43
   RankFeaturePhase            L41
   FetchSearchPhase            L37
   ExpandSearchPhase           L35
   FetchLookupFieldsPhase      L35

 익명 넷
   TransportOpenPointInTimeAction L458   이 체인 안에 실제로 들어온다
   SearchScrollQueryThenFetchAsyncAction L66, L123   스크롤. 별도 계층
   SearchScrollAsyncAction L243                      스크롤. 별도 계층

 스크롤 셋은 AbstractSearchAsyncAction 을 상속하지 않는다
 이름만 SearchPhase 를 공유할 뿐 이 흐름 밖이다
```

## 전이 표

```text
 현재 페이즈            다음               조건
 ------------------------------------------------------------
 query (액션)           fetch              rankBuilder 없음
 query (액션)           rank-feature       rankBuilder 있음
 dfs (액션)             dfs_query          무조건
 open_pit (액션)        익명 페이즈         무조건
 ------------------------------------------------------------
 익명 (open_pit)        없음               sendSearchResponse 로 종료
 dfs_query              fetch              rankBuilder 없음
 dfs_query              rank-feature       rankBuilder 있음
 rank-feature           fetch              정상, 또는 점수 계산이 실패했지만
                                           failuresAllowed 인 경우
 rank-feature           없음               failuresAllowed 가 아니면 onPhaseFailure
 fetch                  expand             세 갈래 모두 같은 곳으로
                                             샤드 1개 최적화 / 문서 0개 / 일반
 expand                 fetch_lookup_fields collapse 가 아니거나 히트 0개면 즉시
                                             아니면 하위 검색 뒤에
 fetch_lookup_fields    없음               sendSearchResponse 로 종료
```

```text
 체인 길이

 query,  rank 없음 : query → fetch → expand → lookup                    4칸
 query,  rank 있음 : query → rank-feature → fetch → expand → lookup     5칸
 dfs,    rank 없음 : dfs → dfs_query → fetch → expand → lookup          5칸
 dfs,    rank 있음 : dfs → dfs_query → rank-feature → fetch → … → lookup 6칸
 open_pit          : open_pit → 익명                                     2칸
 샤드 0개          : 없음                                                0칸

 같은 페이즈로 돌아오는 전이가 없어 상한이 여섯이다
 그래서 사이클이 아니라 체인이다
```

```text
 끝나는 길

 성공 종료는 둘
   FetchLookupFieldsPhase L147   보통의 검색
   open_pit 익명 페이즈 L461     PIT 열기

 실패 종료는 열 곳이 넘는다
   executeNextPhase 의 네 갈래     L355, L369, L375, L394
   executePhase 의 catch            L437
   각 페이즈가 직접 부르는 곳
     DfsQueryPhase L111
     RankFeaturePhase L92, L147, L228
     FetchSearchPhase L89, L220
     ExpandSearchPhase L142
     FetchLookupFieldsPhase L141
     배치 경로 SQTF L667
   sendSearchResponse 안에서도 실패로 끝날 수 있다  L697

 즉 "실패로 끝나는 길"이 "성공으로 끝나는 길"보다 훨씬 많다
```

```text
 스레드가 갈리는 자리

 포크해서 스택을 푸는 곳
   FetchSearchPhase.run L80      context.execute
   RankFeaturePhase.run L80      context.execute
   RankFeaturePhase L193         ThreadedActionListener

 전송 응답을 기다리는 곳
   DfsQueryPhase L100, RankFeaturePhase L174, FetchSearchPhase L251
   ExpandSearchPhase L114, FetchLookupFieldsPhase L100

 스택을 안 푸는 곳
   ExpandSearchPhase.run L71     collapse 가 아니면 그 자리에서 다음으로
                                 그래서 expand 와 lookup 이 한 스택에 겹친다
```

## 결과가 쓰이는 곳

```text
 페이즈 이름
      --> 실패 응답의 phase 필드
      --> 페이즈별 소요시간과 바이트 메트릭의 키

 전이 규칙
      --> 요청 내용이 체인 길이를 정한다
          rankBuilder 가 있으면 한 칸 늘고
          dfs 를 쓰면 한 칸 더 는다
      --> collapse 가 없으면 expand 는 그냥 통과한다

 종료 지점
      --> 성공은 둘, 실패는 열 곳 넘는다
      --> 어느 페이즈에서 죽었는지가 응답에 실린다
```

## 다루지 않는 것

각 페이즈 구현의 내부(`DfsQueryPhase` 의 분산 빈도 수집, `RankFeaturePhase` 의 재점수, `FetchSearchPhase` 의 문서 가져오기, `ExpandSearchPhase` 의 collapse 펼치기, `FetchLookupFieldsPhase` 의 참조 필드 채우기), `CountedCollector` 가 뒤 페이즈의 샤드를 세는 방식, 스크롤 검색 계열, `SearchPhaseController.merge` 의 결과 병합은 같은 뼈대의 곁가지라 요약만 했다.

# InternalEngine.indexingStrategyForOperation

상위: [엔진 쓰기](../README.md)

여덟 줄짜리 메서드인데 **이 흐름의 갈림길**이다. origin 하나로 계획 경로가 갈리고, 플러그인이 갈아끼울 수 있는 유일한 자리이기도 하다.

## 위치

`server` / `org.elasticsearch.index.engine` / `InternalEngine.java` L1910-L1917 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/engine/InternalEngine.java#L1910-L1917))

## 실제 코드

```java
// InternalEngine.java L1910-L1917
    protected IndexingStrategy indexingStrategyForOperation(final Index index) throws IOException {
        if (index.origin() == Operation.Origin.PRIMARY) {
            return planIndexingAsPrimary(index);
        } else {
            // non-primary mode (i.e., replica or recovery)
            return planIndexingAsNonPrimary(index);
        }
    }
```

## 동작 흐름

```text
 L1911  origin == PRIMARY
        +-- 맞으면 planIndexingAsPrimary          L1912
        +-- 아니면 planIndexingAsNonPrimary       L1915
              주석이 "레플리카 또는 복구"라고 적어 두었다 (L1914)
```

```text
 왜 둘로 나뉘는가

 프라이머리는 아직 정해지지 않은 것을 정해야 한다
   이 요청이 버전 충돌인가
   새 문서인가 덮어쓰기인가
   seqNo 를 몇 번으로 줄 것인가

 레플리카와 복구는 이미 정해진 것을 재생한다
   seqNo 는 받아 온다
   충돌 판정도 프라이머리가 이미 했다
   대신 "이미 적용한 연산인가"를 봐야 한다

 그래서 프라이머리 쪽은 충돌 검사가 다섯 갈래이고
 비프라이머리 쪽은 중복 검사가 세 갈래다
```

```text
 protected 인 이유

 CCR 의 FollowingEngine 이 이것을 오버라이드한다 (L71)
 유일한 오버라이드다

 그런데 거기서는 PRIMARY 라도 planIndexingAsPrimary 를 타지 않는다
   preFlight 로 seqNo 가 없으면 거절하고
   이미 처리한 seqNo 면 충돌로 건너뛰고
   그 외에는 planIndexingAsNonPrimary 로 보낸다 (FollowingEngine L89)

 팔로워는 리더가 이미 정한 것을 따라가는 쪽이기 때문이다
 즉 CCR 에서는 [03] 의 프라이머리 경로가 통째로 죽는다
```

```text
 배치는 이 메서드를 부르지 않는다

 indexBatch 경로는 planPrimarySubBatch 나
 planIndexingAsNonPrimary 를 직접 부른다

 그래서 FollowingEngine 의 오버라이드가 배치에서는 적용되지 않는다
 소스에도 그 점이 TODO 로 남아 있다 (FollowingEngine L185)
```

## 결과가 쓰이는 곳

```text
 IndexingStrategy
      --> [01] 이 이것으로 Lucene 에 쓸지, seqNo 를 어떻게 다룰지 정한다
      --> preflight 실패를 들고 있으면 거기서 끝난다

 origin
      --> 이 판정 말고도 여러 곳에서 쓰인다
          스로틀 여부 (L1263), translog 기록 여부 (L1346),
          문서 실패를 치명적으로 볼지 (L2114-2118)
```

## 다루지 않는 것

`FollowingEngine` 의 `preFlight` 와 CCR 버전 규칙, 배치 경로의 계획 메서드(`planPrimarySubBatch`), `Operation.Origin` 이 정해지는 앞 단계는 같은 뼈대의 곁가지라 요약만 했다. 계획 메서드들의 내부는 [03](../03_InternalEngine.planIndexing/README.md)에서 다룬다.

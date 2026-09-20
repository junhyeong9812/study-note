# spi

상위: [문서 색인](../README.md)

이 흐름이 기대는 **계약 하나와 상태 기계 하나**다. 계약은 매핑 갱신이고, 상태 기계는 항목 하나가 지나는 다섯 상태다. 상태 기계 쪽이 훨씬 중요하다 — 이 흐름의 재시도와 재진입이 전부 거기서 나온다.

## MappingUpdatePerformer

`server` / `org.elasticsearch.action.bulk` / `MappingUpdatePerformer.java` L21-L21 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/bulk/MappingUpdatePerformer.java#L21-L21))

```java
// MappingUpdatePerformer.java L21-L21
    void updateMappings(CompressedXContent update, ShardId shardId, ActionListener<Void> listener);
```

```text
 구현 클래스가 없다

 운영 경로의 구현은 performSequentialOnPrimary L281-284 의 람다다
   mappingUpdatedAction.updateMappingOnMaster(shardId.getIndex(), update, listener)

 인터페이스로 뽑아 둔 이유는 테스트다
 매핑 갱신을 안 하거나 항상 실패하는 구현을 끼워
 performOnPrimary 를 마스터 없이 돌릴 수 있다
```

## ItemProcessingState

항목 하나가 지나는 상태다. 이 흐름의 모든 재시도가 이 다섯 칸 사이를 오간다.

`server` / `org.elasticsearch.action.bulk` / `BulkPrimaryExecutionContext.java` L37-L58 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/bulk/BulkPrimaryExecutionContext.java#L37-L58))

```java
// BulkPrimaryExecutionContext.java L37-L58 (javadoc 생략)
    enum ItemProcessingState {
        INITIAL,
        TRANSLATED,
        WAIT_FOR_MAPPING_UPDATE,
        EXECUTED,
        COMPLETED
    }
```

```text
 정상 경로

 INITIAL
   setRequestToExecute      L196
 TRANSLATED
   markOperationAsExecuted  L320   translog 위치를 접는다
 EXECUTED
   markAsCompleted          L390   항목 배열을 번역본으로 갈아끼우고
 COMPLETED                         advance 로 다음 항목 INITIAL
```

```text
 옆길이 넷이다

 1. NOOP  update 가 바꿀 것이 없었다
      markOperationAsNoOp  L287   INITIAL -> EXECUTED 직행
      TRANSLATED 를 건너뛴다. 실행할 요청이 없기 때문이다

 2. 매핑 대기
      markAsRequiringMappingUpdate  L229   TRANSLATED -> WAIT_FOR_MAPPING_UPDATE
      requestToExecute 를 비운다. 새 매핑으로 다시 번역해야 한다
      resetForMappingUpdateRetry    L242   WAIT -> INITIAL

 3. 매핑 대기 실패
      failOnMappingUpdate  L295   WAIT -> EXECUTED -> markAsCompleted -> COMPLETED
      재시도가 아니라 종결이다. 그 항목은 실패로 끝난다

 4. 충돌 재시도
      resetForUpdateRetry  L236   EXECUTED -> INITIAL
      retryCounter 를 올리고 확장 바이트를 되돌린다
```

```text
 재시도 셋의 성격이 다르다

 resetForNoopMappingUpdateRetry  L254  TRANSLATED -> INITIAL
   같은 매핑 버전으로 두 번째면 IllegalStateException 을 던진다 (L256-268)
   가드가 없으면 살아 있는 무한 루프가 된다

 resetForMappingUpdateRetry      L242  WAIT -> INITIAL
   여기만 스레드를 갈아탄다. 매핑이 실제로 바뀐 뒤이기 때문이다

 resetForUpdateRetry             L236  EXECUTED -> INITIAL
   retryOnConflict 로 횟수가 제한된다

 셋 다 resetForExecutionRetry(L275)로 모인다
 거기서 requestToExecute 와 executionResult 를 비운다
```

```text
 advance 가 두 가지 일을 한다

 BulkPrimaryExecutionContext L112-122
   currentIndex 를 올리고
   findNextNonAborted 로 abort 된 항목을 건너뛴다 (L99-105)

 생성자도 advance 를 부르므로 (L96)
 첫 항목부터 건너뛸 수 있다

 abort 는 코디네이터가 샤드에 보내기 전에 이미 실패시킨 항목이다
 그런 것은 여기까지 와도 다시 실행하지 않는다
```

```text
 배치 경로도 같은 상태 기계를 쓴다

 ShardBatchIndexer L143-145
   setRequestToExecute -> markBatchOperationAsExecuted -> markAsCompleted

 markBatchOperationAsExecuted 는 L315 다
 markOperationAsExecuted 와 같은 구현을 isBatch=true 로 부른다
 translog 위치를 접는 방식이 달라진다

 그래서 배치가 일부만 처리하고 넘겨도
 순차 경로가 같은 context 를 이어받아 계속할 수 있다
```

## 결과가 쓰이는 곳

```text
 상태 전이
      --> assertInvariants 가 매 전이마다 상태를 확인한다
      --> 순서를 어기면 assert 로 잡힌다

 currentIndex
      --> hasMoreOperationsToExecute 가 이것으로 루프 종료를 정한다
      --> 재진입해도 이 값이 남아 있어 이어서 돈다

 locationToSync
      --> 항목마다 접어 모은 translog 위치다
      --> WritePrimaryResult 에 실려 fsync 와 복제에 쓰인다

 items 배열
      --> markAsCompleted 가 번역본으로 갈아끼운다
      --> 레플리카가 받는 것이 이 배열이다
```

## 다루지 않는 것

`BulkPrimaryExecutionContext` 의 인덱싱 압력 회계(`addExpandedBytes` / `removeExpandedBytes`)와 서버리스 분기, `PreResolvedUpdates` 의 슬롯 관리, `markOperationAsExecuted` 의 결과 타입별 응답 생성, `MappingUpdatedAction` 의 마스터 요청 경로, `ShardBatchIndexer` 의 색인 내부는 같은 뼈대의 곁가지라 요약만 했다.

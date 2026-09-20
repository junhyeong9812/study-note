# 문서 색인

상위: [Elasticsearch 아키텍처 지도](../../README.md)

`PUT /my-index/_doc/1` 의 문서 하나가 **프라이머리 샤드에 실제로 쓰이기까지**의 길이다. 단건 요청도 내부에서는 bulk 로 감싸여 이 경로를 지난다. [트랜스포트 액션](../transport-action/README.md)의 `doExecute` 뒤가 여기다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 매핑 갱신 계약과 항목 상태 기계다.

기준 커밋: elasticsearch `main` [`60bb239edb`](https://github.com/elastic/elasticsearch/tree/60bb239edb99f0e002eb620e4e82a6f2b15a49b0) (2026-09-19). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 shardOperationOnPrimary                              L166
   +-- primary.ensureMutable(...)                     L171
   |     게이트가 없으면 호출 스레드에서 바로 이어진다 (IndexShard L5240-5241)
   |     hollow 샤드일 때만 나중에 이어받는다
   +-- [01] doExecuteShardOperationOnPrimary          L173

 [01] doExecuteShardOperationOnPrimary                L194
      배치로 처리할지 한 건씩 처리할지 정한다
      |
      +-- 배치 가능하면 performBatchIndexOnPrimary    L228  (동기다)
      |     남은 것이 없으면 => 여기서 응답
      |     남았으면 아래로 떨어진다. 같은 context 를 이어받는다
      |
 [02] performSequentialOnPrimary                      L268
      매핑 갱신을 기다리는 방법 두 개를 엮어 넘긴다
      |
 [03] performOnPrimary (private 12-arg)               L379
      러너블 하나를 만들어 항목을 while 로 돈다
      |
      +-- [04] executeBulkItemRequest                 L400  항목 하나
            |
            +-- update 면 index/delete 로 번역한다
            +-- primary.applyIndexOperationOnPrimary  L561
            +-- primary.applyDeleteOperationOnPrimary L538
            |
            +-- 매핑이 모자라면
            |     [05] handleMappingUpdateRequired    L571  -> false, 루프 탈출
            |
            +-- [06] onComplete                       L583  -> true, 다음 항목

 update 번역이 실패하거나 NOOP 이면 [06] 을 거치지 않는다
 L513-515, L519-520 이 직접 완료 처리한다
 그래서 그 두 경우에는 충돌 재시도도 update 응답 변환도 없다
```

```text
 항목에 닿기도 전에 끝나는 길

 L204  indexingPressure.trackPrimaryOperationExpansion
         메모리 한계를 넘으면 EsRejectedExecutionException 을 던진다
         (IndexingPressure L420-444)
       => L174 catch 가 받아 요청 전체를 실패시킨다

 이 예외는 L216 의 리스너 래핑보다 먼저 나온다
 그래서 그 catch 가 유일한 회수 지점이다
```

```text
 루프가 나갔다가 돌아온다

 매핑이 모자라면 [05] 가 false 를 돌려주고
 [03] 의 while 이 return 으로 빠져나간다 (L408-411)

 그 뒤 마스터에 매핑 갱신을 요청하고 기다린다
 끝나면 itemDoneListener.onResponse 가 불리는데
 그 실체가 L395 다

   onMappingUpdateDone = ActionListener.wrap(v -> executor.execute(this), ...)

 ~~> 같은 러너블을 큐에 다시 넣는다
     doRun 이 다른 스레드에서 처음부터 돈다
     어디까지 했는지는 context 가 들고 있다

 즉 이 흐름은 한 번에 끝나지 않을 수 있다
 매핑이 바뀌는 문서가 섞여 있으면 여러 번 나눠 돈다
```

```text
 같은 항목을 다시 도는 경우가 셋이다

 L601  resetForNoopMappingUpdateRetry   매핑 갱신이 사실 필요 없었다
 L619  resetForMappingUpdateRetry       매핑이 갱신됐으니 다시
 L657  resetForUpdateRetry              update 가 버전 충돌로 실패했다

 스레드를 갈아타는 것은 L619 하나뿐이다
 나머지 둘은 그 자리에서 이어서 돈다

 L601 에는 무한 루프 가드가 있다 (BulkPrimaryExecutionContext L256-268)
 같은 매핑 버전으로 또 no-op 이 나오면 IllegalStateException 을 던진다
 그 예외는 L604 catch 가 받아 그 항목만 실패로 끝낸다
```

```text
 실행 경로가 둘이다

 배치      performBatchIndexOnPrimary   executeBulkItemRequest 를 타지 않는다
 순차      executeBulkItemRequest       항목을 하나씩

 배치가 되는 조건은 셋이다 (ShardBatchIndexer L62-70)
   배치 인덱싱 설정이 켜져 있고
   요청에 배치가 실려 있고
   모든 항목이 INDEX 나 CREATE 다. delete 나 update 가 하나라도 있으면 안 된다

 배치가 일부만 처리하고 나머지를 남기는 이유도 여럿이다
   abort 된 항목이 있다, 매퍼를 못 고른다, 5000개 청크 경계다

 남은 것은 순차로 떨어지고 같은 context 를 이어받는다 (L253)
 그래서 "모든 문서가 executeBulkItemRequest 를 지난다"는 틀린 말이다
```

## 어디에서 쓰이는가

```text
 [트랜스포트 액션] doExecute 뒤가 이 흐름이다
 [구조: 쓰기 복제] 여기가 끝나면 레플리카로 같은 연산이 간다
 [구조: 지속성] applyIndexOperationOnPrimary 안에서 Lucene 과 translog 에 쓴다
 [구조: 샤드 모델] 어느 프라이머리인지는 이미 정해진 뒤다
```

앞 흐름은 [트랜스포트 액션](../transport-action/README.md), 복제 순서는 [쓰기 복제](../../structure/write-replication/README.md), 디스크에 놓이는 모양은 [지속성](../../structure/durability/README.md)에 있다.

## 단계

1. [doExecuteShardOperationOnPrimary](01_TransportShardBulkAction.doExecuteShardOperationOnPrimary/README.md)가 배치와 순차를 가른다.
2. [performSequentialOnPrimary](02_TransportShardBulkAction.performSequentialOnPrimary/README.md)가 매핑 갱신 콜백을 엮는다.
3. [performOnPrimary](03_TransportShardBulkAction.performOnPrimary/README.md)가 항목을 while 로 돈다.
4. [executeBulkItemRequest](04_TransportShardBulkAction.executeBulkItemRequest/README.md)가 항목 하나를 샤드에 적용한다.
5. [handleMappingUpdateRequired](05_TransportShardBulkAction.handleMappingUpdateRequired/README.md)가 매핑을 갱신하고 재시도를 예약한다.
6. [onComplete](06_TransportShardBulkAction.onComplete/README.md)가 결과를 응답으로 바꾼다.

## 결과가 쓰이는 곳

```text
 WritePrimaryResult
      --> 프라이머리 결과와 translog 위치를 담는다
      --> 그 위치는 항목마다 markOperationAsExecuted 가 접어 만든다
          (BulkPrimaryExecutionContext L365, 실패 결과도 L381 에서 접는다)
      --> 이것이 레플리카로 보낼 요청의 근거가 된다

 번역된 요청
      --> update 가 index/delete 로 바뀌면 markAsCompleted 가
          원본 항목 배열을 그 번역본으로 갈아끼운다 (L406-408)
      --> 레플리카는 번역된 쪽을 받는다

 항목별 BulkItemResponse
      --> 하나가 실패해도 나머지는 계속 간다
      --> abort 로 표시된 항목은 advance 가 아예 건너뛴다 (L101-104)
      --> bulk 응답의 errors 플래그가 여기서 정해진다

 매핑 갱신
      --> 마스터를 거친다. 클러스터 상태가 바뀐다
      --> 그동안 이 샤드의 다른 항목도 기다린다

 seqNo 와 primary term
      --> applyIndexOperationOnPrimary 안에서 붙는다
      --> 레플리카가 같은 순서로 적용하는 근거다
```

## 다루지 않는 것

`TransportBulkAction` 이 요청을 샤드별로 쪼개는 앞 단계, `IndexShard.applyIndexOperationOnPrimary` 안쪽(`InternalEngine.index` 까지), 배치 인덱싱(`ShardBatchIndexer`)의 내부, `UpdateHelper` 가 update 를 index/delete 로 번역하는 규칙, `processUpdateResponse` 가 update 응답을 만드는 세부, 인덱싱 압력(`indexingPressure`)과 그 한계, 레플리카 쪽 실행(`shardOperationOnReplica`), 동적 매핑이 마스터에서 병합되는 경로는 같은 뼈대의 곁가지라 요약만 했다.

## 하위 메서드

- [01 doExecuteShardOperationOnPrimary](01_TransportShardBulkAction.doExecuteShardOperationOnPrimary/README.md)
- [02 performSequentialOnPrimary](02_TransportShardBulkAction.performSequentialOnPrimary/README.md)
- [03 performOnPrimary (private 12-arg)](03_TransportShardBulkAction.performOnPrimary/README.md)
- [04 executeBulkItemRequest](04_TransportShardBulkAction.executeBulkItemRequest/README.md)
- [05 handleMappingUpdateRequired](05_TransportShardBulkAction.handleMappingUpdateRequired/README.md)
- [06 onComplete](06_TransportShardBulkAction.onComplete/README.md)
- [spi](spi/README.md) — 매핑 갱신 계약, 항목 상태 기계

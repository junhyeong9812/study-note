# TransportShardBulkAction.onComplete

상위: [문서 색인](../README.md)

엔진 결과를 **사용자에게 나갈 응답으로 바꾸고 항목을 끝낸다**. update 가 충돌로 실패했으면 여기서 다시 돌릴지 정한다. 들어오는 길이 넷이다.

## 위치

`server` / `org.elasticsearch.action.bulk` / `TransportShardBulkAction.java` L645-L699 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/bulk/TransportShardBulkAction.java#L645-L699))

## 실제 코드

충돌 재시도 판정까지다.

`server` / `org.elasticsearch.action.bulk` / `TransportShardBulkAction.java` L647-L659 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/bulk/TransportShardBulkAction.java#L647-L659))

```java
// TransportShardBulkAction.java L647-L659
        context.markOperationAsExecuted(r);
        final DocWriteRequest<?> docWriteRequest = context.getCurrent();
        final DocWriteRequest.OpType opType = docWriteRequest.opType();
        final boolean isUpdate = opType == DocWriteRequest.OpType.UPDATE;
        final BulkItemResponse executionResult = context.getExecutionResult();
        final boolean isFailed = executionResult.isFailed();
        if (isUpdate
            && isFailed
            && isConflictException(executionResult.getFailure().getCause())
            && context.getUpdateRetryCounter() < ((UpdateRequest) docWriteRequest).retryOnConflict()) {
            context.resetForUpdateRetry();
            return;
        }
```

응답으로 바꾸고 항목을 끝낸다.

`server` / `org.elasticsearch.action.bulk` / `TransportShardBulkAction.java` L660-L698 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/bulk/TransportShardBulkAction.java#L660-L698))

```java
// TransportShardBulkAction.java L660-L698
        final BulkItemResponse response;
        if (isUpdate) {
            assert context.getPrimary().mapperService() != null;
            final MappingLookup mappingLookup = context.getPrimary().mapperService().mappingLookup();
            assert mappingLookup != null;

            response = processUpdateResponse(
                (UpdateRequest) docWriteRequest,
                context.getConcreteIndex(),
                mappingLookup,
                executionResult,
                updateResult
            );
        } else {
            if (isFailed) {
                final Exception failure = executionResult.getFailure().getCause();
                Level level;
                if (TransportShardBulkAction.isConflictException(failure)) {
                    level = Level.TRACE;
                } else {
                    level = Level.DEBUG;
                }
                logger.log(
                    level,
                    () -> Strings.format(
                        "%s failed to execute bulk item (%s) %s",
                        context.getPrimary().shardId(),
                        opType.getLowercase(),
                        docWriteRequest
                    ),
                    failure
                );

            }
            response = executionResult;
        }

        context.markAsCompleted(response);
        assert context.isInitial();
```

## 동작 흐름

```text
 L647  context.markOperationAsExecuted(r)
         TRANSLATED -> EXECUTED
         여기서 translog 위치가 접힌다 (아래 참조)

 L653  update 이고 실패했고 충돌이고 재시도 횟수가 남았으면
       L657  resetForUpdateRetry()      EXECUTED -> INITIAL
       L658  return                     같은 항목을 그 자리에서 다시

 L661  update 이면
       L666  processUpdateResponse(...)   UpdateResponse 로 바꾼다
 아니면
       L674  실패면 로그 레벨만 정한다
             L677  충돌이면 TRACE, 아니면 DEBUG
       L694  결과를 그대로 쓴다

 L697  context.markAsCompleted(response)
         EXECUTED -> COMPLETED -> advance -> 다음 항목 INITIAL
```

```text
 들어오는 길이 넷이다

 L583  정상 경로. 엔진 결과를 받아서
 L432  onRejection 이 남은 항목을 실패로 적을 때 (updateResult = null)
 L607  매핑 갱신이 프라이머리에서 거절됐을 때
 L631  매핑 갱신 요청 자체가 실패했을 때

 뒤의 셋은 전부 exceptionToResult 로 만든 실패 결과를 넣는다
```

```text
 translog 위치가 여기서 모인다

 markOperationAsExecuted 안에서 접는다
   BulkPrimaryExecutionContext L365  성공일 때
   BulkPrimaryExecutionContext L380-382  실패인데 위치가 있을 때

 두 번째가 있는 이유를 주석이 적어 두었다
   "A FAILURE result can still carry a translog location
    when InternalEngine converts it into a no-op."

 즉 실패한 연산도 translog 에 no-op 으로 남을 수 있고
 그러면 레플리카도 그 no-op 을 받아야 한다
 seqNo 에 구멍이 나면 안 되기 때문이다
```

```text
 markAsCompleted 가 항목을 갈아끼운다

 BulkPrimaryExecutionContext L406-408
   실패하지 않았고, 번역된 요청이 있고, 원본과 다르면
   request.items()[currentIndex] 를 번역본으로 바꾼다

 그래서 레플리카는 update 가 아니라
 프라이머리가 만든 index 나 delete 를 받는다

 레플리카가 스크립트를 다시 돌리지 않는 이유가 이것이다
```

```text
 advance 가 abort 된 항목을 건너뛴다

 BulkPrimaryExecutionContext L101-104
   currentIndex 를 올린 뒤
   primaryResponse 가 abort 로 표시된 항목은 계속 넘긴다

 코디네이터가 미리 실패시킨 항목은
 executeBulkItemRequest 에 아예 들어오지 않는다
```

```text
 충돌 재시도만 그 자리에서 돈다

 L657 resetForUpdateRetry 는 EXECUTED 를 INITIAL 로 되돌리고
 retryCounter 를 올린다

 return 이라 markAsCompleted 를 안 부르므로 advance 도 없다
 그래서 while 이 같은 항목을 다시 집는다

 retryOnConflict 로 횟수가 제한된다
```

## 결과가 쓰이는 곳

```text
 BulkItemResponse
      --> 항목마다 하나씩 쌓인다
      --> buildShardResponse 가 모아 응답을 만든다
      --> 실패해도 다른 항목은 계속 간다

 locationToSync
      --> WritePrimaryResult 에 실려 레플리카와 fsync 결정에 쓰인다
      --> 접는 규칙은 isBatch 여부에 따라 다르다

 갈아끼운 items 배열
      --> 레플리카로 가는 요청의 내용이 된다

 currentIndex
      --> advance 가 다음 항목으로 옮긴다
      --> hasMoreOperationsToExecute 가 이 값으로 루프 종료를 정한다
```

## 다루지 않는 것

`processUpdateResponse` 가 `UpdateResponse` 를 만들고 `_source` 를 붙이는 세부, `BulkPrimaryExecutionContext.markOperationAsExecuted` 의 결과 타입별 분기, `TransportWriteAction.locationToSync` 의 접는 규칙, `isConflictException` 이 예외를 푸는 방식, 인덱싱 압력 회계의 되돌림은 같은 뼈대의 곁가지라 요약만 했다.

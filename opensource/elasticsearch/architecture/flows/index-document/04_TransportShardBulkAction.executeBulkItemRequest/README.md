# TransportShardBulkAction.executeBulkItemRequest

상위: [문서 색인](../README.md)

항목 하나를 **샤드에 실제로 적용한다**. update 면 먼저 index 나 delete 로 번역하고, 그 다음 엔진을 부른다. 돌려주는 `boolean` 이 [performOnPrimary](../03_TransportShardBulkAction.performOnPrimary/README.md)의 루프를 계속 돌릴지 정한다.

## 위치

`server` / `org.elasticsearch.action.bulk` / `TransportShardBulkAction.java` L475-L585 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/bulk/TransportShardBulkAction.java#L475-L585))

## 실제 코드

update 를 index 나 delete 로 번역한다. 이 구간에서만 try 로 감싼다.

`server` / `org.elasticsearch.action.bulk` / `TransportShardBulkAction.java` L491-L505 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/bulk/TransportShardBulkAction.java#L491-L505))

```java
// TransportShardBulkAction.java L491-L505
                final UpdateHelper.PreResolvedUpdate preResolvedUpdate = context.takePreResolvedUpdate();
                if (preResolvedUpdate != null) {
                    // releases the acquired searcher if complete() throws before consuming the get; a no-op otherwise
                    try (preResolvedUpdate) {
                        updateResult = preResolvedUpdate.complete();
                    }
                } else {
                    updateResult = updateHelper.prepare(
                        updateRequest,
                        context.getPrimary(),
                        nowInMillisSupplier,
                        UPDATE_FETCH_SOURCE_CONTEXT,
                        context.getBulkShardRequest().splitShardCountSummary()
                    );
                }
```

번역이 실패하면 그 자리에서 항목을 끝낸다.

`server` / `org.elasticsearch.action.bulk` / `TransportShardBulkAction.java` L512-L516 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/bulk/TransportShardBulkAction.java#L512-L516))

```java
// TransportShardBulkAction.java L512-L516
                final Engine.Result result = new Engine.IndexResult(failure, updateRequest.version(), updateRequest.id());
                context.setRequestToExecute(updateRequest);
                context.markOperationAsExecuted(result);
                context.markAsCompleted(context.getExecutionResult());
                return true;
```

바꿀 것이 없어도 마찬가지다.

`server` / `org.elasticsearch.action.bulk` / `TransportShardBulkAction.java` L518-L523 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/bulk/TransportShardBulkAction.java#L518-L523))

```java
// TransportShardBulkAction.java L518-L523
            if (updateResult.getResponseResult() == DocWriteResponse.Result.NOOP) {
                context.markOperationAsNoOp(updateResult.action());
                context.markAsCompleted(context.getExecutionResult());
                context.getPrimary().noopUpdate();
                return true;
            }
```

삭제는 바로 엔진으로 간다. 여기는 try 가 없다.

`server` / `org.elasticsearch.action.bulk` / `TransportShardBulkAction.java` L538-L545 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/bulk/TransportShardBulkAction.java#L538-L545))

```java
// TransportShardBulkAction.java L538-L545
            result = primary.applyDeleteOperationOnPrimary(
                version,
                request.id(),
                request.routing(),
                request.versionType(),
                request.ifSeqNo(),
                request.ifPrimaryTerm()
            );
```

색인이면 파싱할 소스를 만들어 넘긴다. 매핑이 모자라면 여기서 갈린다.

`server` / `org.elasticsearch.action.bulk` / `TransportShardBulkAction.java` L547-L581 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/bulk/TransportShardBulkAction.java#L547-L581))

```java
// TransportShardBulkAction.java L547-L581
            final IndexRequest request = context.getRequestToExecute();

            XContentMeteringParserDecorator meteringParserDecorator = documentParsingProvider.newMeteringParserDecorator(request);
            final SourceToParse sourceToParse = new SourceToParse(
                request.id(),
                request.source(),
                request.getContentType(),
                request.routing(),
                request.getDynamicTemplates(),
                request.getDynamicTemplateParams(),
                request.getIncludeSourceOnError(),
                meteringParserDecorator,
                request.tsid()
            );
            result = primary.applyIndexOperationOnPrimary(
                version,
                request.versionType(),
                sourceToParse,
                request.ifSeqNo(),
                request.ifPrimaryTerm(),
                request.getAutoGeneratedTimestamp(),
                request.isRetry()
            );
            if (result.getResultType() == Engine.Result.Type.MAPPING_UPDATE_REQUIRED) {
                return handleMappingUpdateRequired(
                    context,
                    mappingUpdater,
                    waitForMappingUpdate,
                    itemDoneListener,
                    primary,
                    result,
                    version,
                    updateResult
                );
            }
```

## 동작 흐름

```text
 L488  opType == UPDATE
       |
       +-- L491  takePreResolvedUpdate()
       |     있으면 L495  preResolvedUpdate.complete()
       |     없으면 L498  updateHelper.prepare(...)
       |            (재시도 때는 이미 소비돼 null 이라 여기로 온다)
       |
       +-- L506  NOOP 이 아니면 확장 바이트를 회계에 더한다
       |
       +-- L509  catch (번역 실패)
       |     L512  Engine.IndexResult(failure, ...)
       |     L513-515  setRequestToExecute -> markOperationAsExecuted -> markAsCompleted
       |     L516  return true
       |     => onComplete 를 거치지 않는다
       |
       +-- L518  NOOP 이면
       |     L519-521  markOperationAsNoOp -> markAsCompleted -> noopUpdate
       |     L522  return true
       |     => 역시 onComplete 를 거치지 않는다
       |
       +-- L524  setRequestToExecute(updateResult.action())

 L526  update 가 아니면 setRequestToExecute(getCurrent())

 L534  isDelete 는 번역된 요청 기준이다
       update 가 delete 로 번역됐으면 여기서 delete 갈래로 간다

 L536  isDelete
       +-- L538  primary.applyDeleteOperationOnPrimary(6-arg)
 아니면
       +-- L550  new SourceToParse(...)
       +-- L561  primary.applyIndexOperationOnPrimary(...)
       +-- L570  MAPPING_UPDATE_REQUIRED 이면
             L571  return handleMappingUpdateRequired(...)

 L583  onComplete(result, context, updateResult)
 L584  return true
```

```text
 onComplete 를 건너뛰는 길이 둘이다

 L513-516  update 번역이 실패했다
 L519-522  update 가 NOOP 이었다

 둘 다 markOperationAsExecuted 와 markAsCompleted 를 직접 부른다

 그래서 이 둘은
   충돌 재시도(retryOnConflict)를 받지 않고
   processUpdateResponse 로 응답을 다듬지도 않는다

 번역 실패는 애초에 실행된 적이 없으니 재시도할 것도 없고
 NOOP 은 바꿀 것이 없으니 다듬을 것도 없다
```

```text
 try 가 번역 구간에만 있다

 L490-517  update 번역만 감싼다
 L536-582  엔진 호출에는 try 가 없다

 applyDeleteOperationOnPrimary 와 applyIndexOperationOnPrimary 는
 둘 다 throws IOException 이다

 그래서 엔진 IO 예외는 이 메서드를 뚫고 나가
 doRun 밖에서 잡히고 요청 전체가 실패한다
 항목 하나의 실패로 기록되지 않는다
```

```text
 delete 에는 매핑 검사가 없다

 MAPPING_UPDATE_REQUIRED 검사는 index 갈래에만 있다 (L570)
 지울 문서에 새 필드를 만들 일이 없기 때문이다
```

## 결과가 쓰이는 곳

```text
 돌려주는 boolean
      --> true 면 루프가 다음 항목으로 간다
      --> false 는 handleMappingUpdateRequired 에서만 나온다 (L637)

 번역된 요청 (requestToExecute)
      --> markAsCompleted 가 원본 배열을 이것으로 갈아끼운다
      --> 레플리카는 update 가 아니라 번역본을 받는다

 Engine.Result
      --> seqNo, primary term, translog 위치를 담는다
      --> onComplete 가 이것을 응답으로 바꾸고 위치를 접는다

 확장 바이트 회계 (L507)
      --> update 가 커지면 메모리를 더 잡았다고 기록한다
      --> markAsCompleted 나 재시도 때 되돌린다
```

## 다루지 않는 것

`UpdateHelper.prepare` 와 `PreResolvedUpdate.complete` 가 update 를 푸는 규칙, `IndexShard.applyIndexOperationOnPrimary` 안쪽(매핑 필요 판정과 `InternalEngine.index`), `SourceToParse` 와 문서 파싱, `DocumentParsingProvider` 의 계량, 인덱싱 압력 회계의 계산식은 같은 뼈대의 곁가지라 요약만 했다.

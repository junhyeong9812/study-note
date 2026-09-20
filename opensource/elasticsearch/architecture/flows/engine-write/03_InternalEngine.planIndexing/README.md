# planIndexingAsPrimary / …WithVersion / …AsNonPrimary

상위: [엔진 쓰기](../README.md)

**무엇을 할지 정하기만 하고 아무것도 쓰지 않는다.** 결과는 [전략 객체](../spi/README.md) 하나다. 거절할 요청은 여기서 거절되고, Lucene 에 쓸 방식도 여기서 정해진다.

## 위치

`server` / `org.elasticsearch.index.engine` / `InternalEngine.java` L1919-L2048 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/engine/InternalEngine.java#L1919-L2048))

## 실제 코드

프라이머리는 먼저 현재 버전을 찾는다.

`server` / `org.elasticsearch.index.engine` / `InternalEngine.java` L1919-L1931 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/engine/InternalEngine.java#L1919-L1931))

```java
// InternalEngine.java L1919-L1931
    private IndexingStrategy planIndexingAsPrimary(final Index index) throws IOException {
        assert index.origin() == Operation.Origin.PRIMARY : "planing as primary but origin isn't. got " + index.origin();
        final boolean optimizeAppendOnly = canOptimizeAddDocument(index) && mayHaveBeenIndexedBefore(index) == false;
        VersionValue versionValue = null;
        if (optimizeAppendOnly == false
            && (sequenceNumbersAreDisabled() == false
                || index.getIfSeqNo() == UNASSIGNED_SEQ_NO
                || index.getIfPrimaryTerm() == UNASSIGNED_PRIMARY_TERM)) {
            versionMap.enforceSafeAccess();
            versionValue = resolveDocVersion(index, index.getIfSeqNo() != UNASSIGNED_SEQ_NO);
        }
        return planIndexingAsPrimaryWithVersion(index, versionValue, optimizeAppendOnly, index.parsedDoc().docs().size());
    }
```

append 전용 최적화와 미지원 조합을 먼저 걸러낸다.

`server` / `org.elasticsearch.index.engine` / `InternalEngine.java` L1950-L1963 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/engine/InternalEngine.java#L1950-L1963))

```java
// InternalEngine.java L1950-L1963
        if (optimizeAppendOnly) {
            final Exception reserveError = tryAcquireInFlightDocs(index, reservingDocs);
            if (reserveError != null) {
                return IndexingStrategy.failAsTooManyDocs(reserveError, index.id());
            } else {
                return IndexingStrategy.optimizedAppendOnly(1L, reservingDocs);
            }
        }

        if (sequenceNumbersAreDisabled()
            && index.getIfSeqNo() != UNASSIGNED_SEQ_NO
            && index.getIfPrimaryTerm() != UNASSIGNED_PRIMARY_TERM) {
            return IndexingStrategy.optimisticConcurrencyControlNotSupported(index.id(), shardId);
        }
```

그 다음은 충돌 검사 셋이고, 먼저 걸리는 것이 이긴다.

`server` / `org.elasticsearch.index.engine` / `InternalEngine.java` L1965-L2011 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/engine/InternalEngine.java#L1965-L2011))

```java
// InternalEngine.java L1965-L2011
        final long currentVersion = versionValue == null ? Versions.NOT_FOUND : versionValue.version;
        final boolean currentNotFoundOrDeleted = versionValue == null || versionValue.isDelete();

        if (index.getIfSeqNo() != UNASSIGNED_SEQ_NO && currentNotFoundOrDeleted) {
            final VersionConflictEngineException e = new VersionConflictEngineException(
                shardId,
                index.id(),
                index.getIfSeqNo(),
                index.getIfPrimaryTerm(),
                UNASSIGNED_SEQ_NO,
                UNASSIGNED_PRIMARY_TERM
            );
            return IndexingStrategy.skipDueToVersionConflict(e, true, currentVersion, index.id());
        }

        if (index.getIfSeqNo() != UNASSIGNED_SEQ_NO
            && (versionValue.seqNo != index.getIfSeqNo() || versionValue.term != index.getIfPrimaryTerm())) {
            final VersionConflictEngineException e = new VersionConflictEngineException(
                shardId,
                index.id(),
                index.getIfSeqNo(),
                index.getIfPrimaryTerm(),
                versionValue.seqNo,
                versionValue.term
            );
            return IndexingStrategy.skipDueToVersionConflict(e, currentNotFoundOrDeleted, currentVersion, index.id());
        }

        if (index.versionType().isVersionConflictForWrites(currentVersion, index.version(), currentNotFoundOrDeleted)) {
            final VersionConflictEngineException e = new VersionConflictEngineException(
                shardId,
                index.parsedDoc().documentDescription(),
                index.versionType().explainConflictForWrites(currentVersion, index.version(), true)
            );
            return IndexingStrategy.skipDueToVersionConflict(e, currentNotFoundOrDeleted, currentVersion, index.id());
        }

        final Exception reserveError = tryAcquireInFlightDocs(index, reservingDocs);
        if (reserveError != null) {
            return IndexingStrategy.failAsTooManyDocs(reserveError, index.id());
        } else {
            return IndexingStrategy.processNormally(
                currentNotFoundOrDeleted,
                canOptimizeAddDocument(index) ? 1L : index.versionType().updateVersion(currentVersion, index.version()),
                reservingDocs
            );
        }
```

비프라이머리는 "이미 적용했나"를 먼저 본다.

`server` / `org.elasticsearch.index.engine` / `InternalEngine.java` L2017-L2047 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/engine/InternalEngine.java#L2017-L2047))

```java
// InternalEngine.java L2017-L2047
        if (canOptimizeAddDocument(index)) {
            mayHaveBeenIndexedBefore(index);
        }
        final IndexingStrategy plan;
        // unlike the primary, replicas don't really care to about creation status of documents
        // this allows to ignore the case where a document was found in the live version maps in
        // a delete state and return false for the created flag in favor of code simplicity
        final long maxSeqNoOfUpdatesOrDeletes = getMaxSeqNoOfUpdatesOrDeletes();
        if (hasBeenProcessedBefore(index)) {
            // the operation seq# was processed and thus the same operation was already put into lucene
            // this can happen during recovery where older operations are sent from the translog that are already
            // part of the lucene commit (either from a peer recovery or a local translog)
            // or due to concurrent indexing & recovery. For the former it is important to skip lucene as the operation in
            // question may have been deleted in an out of order op that is not replayed.
            // See testRecoverFromStoreWithOutOfOrderDelete for an example of local recovery
            // See testRecoveryWithOutOfOrderDelete for an example of peer recovery
            plan = IndexingStrategy.processButSkipLucene(false, index.version());
        } else if (maxSeqNoOfUpdatesOrDeletes <= localCheckpointTracker.getProcessedCheckpoint()) {
            // see Engine#getMaxSeqNoOfUpdatesOrDeletes for the explanation of the optimization using sequence numbers
            assert maxSeqNoOfUpdatesOrDeletes < index.seqNo() : index.seqNo() + ">=" + maxSeqNoOfUpdatesOrDeletes;
            plan = IndexingStrategy.optimizedAppendOnly(index.version(), 0);
        } else {
            versionMap.enforceSafeAccess();
            final OpVsLuceneDocStatus opVsLucene = compareOpToLuceneDocBasedOnSeqNo(index);
            if (opVsLucene == OpVsLuceneDocStatus.OP_STALE_OR_EQUAL) {
                plan = IndexingStrategy.processAsStaleOp(index.version(), 0);
            } else {
                plan = IndexingStrategy.processNormally(opVsLucene == OpVsLuceneDocStatus.LUCENE_DOC_NOT_FOUND, index.version(), 0);
            }
        }
        return plan;
```

## 동작 흐름

```text
 planIndexingAsPrimary                                    L1919
   L1921  optimizeAppendOnly = canOptimizeAddDocument && mayHaveBeenIndexedBefore == false
            뒤엣것은 반환값만 쓰는 것이 아니라
            auto-id 타임스탬프를 갱신하는 부작용이 있다 (L2127-2140)
   L1923  최적화가 아니고 조건이 맞으면
            enforceSafeAccess 후 resolveDocVersion
   L1930  planIndexingAsPrimaryWithVersion(..., docs().size())
            예약할 문서 수는 nested 를 포함한 개수다

 planIndexingAsPrimaryWithVersion                         L1943
   L1950  optimizeAppendOnly 면
            예약 실패 => failAsTooManyDocs
            아니면    => optimizedAppendOnly
   L1959  seqNo 가 꺼져 있는데 조건부 요청이면
            => optimisticConcurrencyControlNotSupported
   L1965  currentVersion = versionValue == null ? NOT_FOUND : version
   L1966  currentNotFoundOrDeleted = versionValue == null || isDelete()
            삭제 tombstone 은 "없음"으로 친다
   L1968  ifSeqNo 를 줬는데 문서가 없으면 => 충돌
   L1980  ifSeqNo/term 이 안 맞으면       => 충돌
   L1993  versionType 규칙에 걸리면       => 충돌
   L2002  예약 실패                       => failAsTooManyDocs
   L2006  => processNormally(cNFoD, 버전, 예약수)
            버전은 append 최적화면 1L, 아니면 versionType 이 계산한다 (L2008)

 planIndexingAsNonPrimary                                 L2014
   L2017  append 최적화 가능하면 mayHaveBeenIndexedBefore 를 부른다
            반환값은 버린다. 타임스탬프 갱신만 목적이다
   L2025  hasBeenProcessedBefore 면 => processButSkipLucene
            이미 Lucene 에 들어간 연산이다
   L2034  maxSeqNoOfUpdatesOrDeletes <= 처리 체크포인트면
            => optimizedAppendOnly
   L2039  enforceSafeAccess
   L2040  compareOpToLuceneDocBasedOnSeqNo 는 세 값이다
            OP_STALE_OR_EQUAL     => processAsStaleOp
            LUCENE_DOC_NOT_FOUND  => processNormally(cNFoD=true)  -> addDocs
            OP_NEWER              => processNormally(cNFoD=false) -> updateDocs
```

```text
 버전 조회에 부작용이 있다

 resolveDocVersion 은 이름과 달리 읽기만 하지 않는다

 getVersionFromMap (L1159-1176)
   versionMap 이 unsafe 상태이면
   refreshInternalSearcher 로 강제 refresh 를 한다
   그리고 safe-access 를 켠다

 즉 쓰기 경로 한가운데에서 refresh 가 일어날 수 있다
 versionMap 에 없는 것을 Lucene 에서 찾아야 하는데
 아직 안 보이는 세그먼트가 있으면 못 찾기 때문이다

 또 하나
   map 에서 찾은 것이 삭제 tombstone 인데
   GC 만료 시간이 지났으면 null 로 강등한다 (L1150-1154)
   "삭제된 적 있음"을 잊고 "없음"으로 취급한다
```

```text
 충돌 검사는 먼저 걸리는 것이 이긴다

 순서가 의미를 갖는다
   1. ifSeqNo 를 줬는데 문서가 없다        L1968
   2. ifSeqNo/term 이 현재와 다르다        L1980
   3. versionType 규칙 위반                L1993

 1번은 cNFoD 를 상수 true 로 넘기고 (L1977)
 2번과 3번은 계산된 값을 넘긴다

 세 경우 다 skipDueToVersionConflict 인데
 그 팩터리는 preflight 실패를 들고 있어
 [01] L1302 에서 바로 잡힌다
```

```text
 예약이 두 군데 있다

 L1951  append 최적화 경로
 L2002  일반 경로

 tryAcquireInFlightDocs 는 실패하면 자기가 되돌린다 (L2373)
 성공하면 [01] 의 finally 가 돌려준다

 예약량이 경로마다 다르다
   단건은 index.parsedDoc().docs().size()  nested 문서 수만큼
   배치는 상수 1
```

## 결과가 쓰이는 곳

```text
 전략 객체
      --> [01] 이 이것만 보고 나머지를 정한다
      --> 필드 조합이 [05] 의 Lucene 쓰기 방식을 고른다

 cNFoD (currentNotFoundOrDeleted)
      --> processNormally 가 이것을 뒤집어 useLuceneUpdateDocument 로 쓴다 (L2214)
      --> 즉 "문서가 있었다"가 updateDocument 의 유일한 근거다
      --> IndexResult 의 created 플래그도 이 값이다

 versionForIndexing
      --> Lucene 문서의 _version 필드에 들어간다
      --> translog 에도 결과의 version 이 실린다

 enforceSafeAccess
      --> 프라이머리와 비프라이머리 양쪽에 있다 (L1927, L2039)
      --> 다음 조회가 versionMap 을 믿을 수 있게 만든다
```

## 다루지 않는 것

`resolveDocVersion` 과 `compareOpToLuceneDocBasedOnSeqNo` 의 Lucene 조회 내부, `VersionType` 별 충돌 규칙, `canOptimizeAddDocument` 와 auto-id 타임스탬프 규칙, `LiveVersionMap` 의 safe/unsafe 모드가 바뀌는 조건, in-flight 문서 한도와 `maxDocs`, 배치 경로의 `planPrimarySubBatch` 는 같은 뼈대의 곁가지라 요약만 했다.

# 엔진 쓰기

문서 하나가 **Lucene 과 translog 에 실제로 닿는** 자리다. [문서 색인](../index-document/README.md)의 `applyIndexOperationOnPrimary` 안쪽이 여기다. 이 흐름은 처음부터 끝까지 **한 스레드로 간다** — 콜백 경계가 하나도 없다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 전략 객체와 origin 이다.

기준 커밋: elasticsearch `main` [`60bb239edb`](https://github.com/elastic/elasticsearch/tree/60bb239edb99f0e002eb620e4e82a6f2b15a49b0) (2026-09-19). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 [01] InternalEngine.index                                L1262
      +-- acquireEnsureOpenRef                            L1264  닫히는 중이면 예외
      +-- versionMap.acquireLock(uid)                      L1268  문서 단위 락. 기다릴 수 있다
      +-- 복구가 아니면 throttle.acquireThrottle            L1269  여기서 무기한 멈출 수 있다
      |
      +-- [02] indexingStrategyForOperation               L1298  무엇을 할지 정한다
      |     +-- PRIMARY 면 [03] planIndexingAsPrimary     L1912
      |     +-- 아니면 planIndexingAsNonPrimary            L1915
      |
      +-- 전략에 preflight 실패가 들어 있으면              L1302
      |     그 결과를 쓰고 Lucene 을 건너뛴다              L1304
      |     (하지만 아래 단계는 계속 지난다)
      |
      +-- PRIMARY 면 seqNo 를 새로 부여한다                L1312
      +-- 아니면 받은 seqNo 로 advanceMaxSeqNo             L1329
      |
      +-- Lucene 에 쓸 전략이면 [04] indexIntoLucene       L1335
      |     +-- [05] writeLuceneDocuments                 L2061
      |
      +-- translog 에서 온 것이 아니면                      L1346
      |     성공이면 translog.add                          L1349
      |     실패인데 seqNo 가 있으면 innerNoOp 으로 no-op     L1359
      |
      +-- versionMap 갱신 / 체크포인트 갱신                 L1367, L1377
      +-- finally releaseInFlightDocs                      L1387
      +-- catch -> 엔진을 죽일지 정하고 다시 던진다         L1389
```

```text
 전략 일곱 개가 이 흐름의 상태 공간이다 (IndexingStrategy L2197-2239)

 팩터리                                   Lucene  update  stale  preflight실패
 optimizedAppendOnly                       O       X       X      -
 processNormally                           O    cNFoD==false X     -
 processAsStaleOp                          X       X       O      -
 processButSkipLucene                      X       X       X      -
 skipDueToVersionConflict                  X       X       X      있음
 failAsTooManyDocs                         X       X       X      있음
 optimisticConcurrencyControlNotSupported  X       X       X      있음

 이 표에서 바로 나오는 사실 넷

 1. updateDocument 을 쓰는 것은 processNormally 에 cNFoD=false 로 들어갈 때뿐이다
      즉 "문서가 이미 살아 있었다"가 update 의 유일한 근거다

 2. 프라이머리에서는 addStaleOpToLucene 이 절대 true 가 안 된다
      processAsStaleOp 를 만드는 곳이 planIndexingAsNonPrimary L2042 하나뿐이다

 3. L1337 의 "Lucene 건너뛰고 결과만" 에 실제로 도달하는 것은
      processButSkipLucene 하나뿐이다
      나머지 셋은 preflight 실패를 들고 있어 L1302 에서 먼저 잡힌다
      생성자 불변식이 그것을 보장한다 (L2178 둘을 동시에 가질 수 없다)

 4. stale op 은 Lucene 에는 쓰이되 versionMap 에는 안 들어간다
      L1365 가 plan.indexIntoLucene 을 보는데 processAsStaleOp 는 false 다
```

```text
 문서 실패와 엔진 사망의 경계

 treatDocumentFailureAsTragicError (L2114-2118)
   REPLICA, PEER_RECOVERY, LOCAL_RESET 에서 true

 주의할 것이 둘이다

 1. LOCAL_TRANSLOG_RECOVERY 는 isRecovery() 는 true 인데 (Engine L1892)
    이 목록에는 없다. 즉 "복구면 엔진이 죽는다"는 틀린 말이다

 2. 프라이머리라고 안전한 것도 아니다
    no-op tombstone 쓰기가 실패하면 origin 과 무관하게 엔진을 죽인다
      주석이 이유를 적어 두었다 (L2721-2725)
      "이미 시퀀스 번호를 발급했으므로 이건 치명적이다"
    translog.add 가 tragic 으로 닫히거나 (Translog L660-666)
    인덱스가 부패해도 마찬가지다 (maybeFailEngine L3333-3352)

 판정을 두 군데서 하는데 조건이 다르다
   writeLuceneDocuments L2078-2080  ACE 아님 + IW tragic 없음 + treat 아님
   index L1391                      ACE 아님 + treat 임
```

```text
 배치는 여기로 오지 않는다

 indexBatch (L1404) 가 별도 진입점이다
 [문서 색인]의 배치 경로가 그리로 간다

 계획과 Lucene 쓰기 일부는 공유하지만
   indexingStrategyForOperation 을 안 부른다 (planPrimarySubBatch 를 직접 쓴다)
   seqNo 를 하나씩이 아니라 범위로 예약한다 (doGenerateSeqNos L1666)
   컬럼 경로는 indexWriter.addBatch 를 쓴다 (L1539)
   translog 에 배치당 한 번만 쓴다 (L1762)
```

## 어디에서 쓰이는가

```text
 [문서 색인] applyIndexOperationOnPrimary 안쪽이 이 흐름이다
 [구조: 지속성] Lucene 버퍼와 translog 에 쓰는 순서가 여기서 정해진다
 [구조: 쓰기 복제] 여기서 붙은 seqNo 로 레플리카가 같은 순서를 만든다
```

앞 흐름은 [문서 색인](../index-document/README.md), 디스크에 놓이는 모양은 [지속성](../../structure/durability/README.md)에 있다.

## 단계

1. [InternalEngine.index](01_InternalEngine.index/README.md)가 락을 잡고 전체를 지휘한다.
2. [indexingStrategyForOperation](02_InternalEngine.indexingStrategyForOperation/README.md)이 origin 으로 계획 경로를 가른다.
3. [planIndexing 세 메서드](03_InternalEngine.planIndexing/README.md)가 전략 객체를 만든다.
4. [indexIntoLucene](04_InternalEngine.indexIntoLucene/README.md)이 문서에 seqNo 를 새긴다.
5. [writeLuceneDocuments](05_InternalEngine.writeLuceneDocuments/README.md)가 IndexWriter 를 부른다.

## 결과가 쓰이는 곳

```text
 IndexResult
      --> seqNo, version, translog 위치, created 플래그를 담는다
      --> 위 흐름의 onComplete 가 이것을 응답으로 바꾼다

 translog 위치
      --> WritePrimaryResult 에 실려 fsync 와 복제에 쓰인다
      --> 실패한 연산도 no-op 으로 위치를 가질 수 있다

 versionMap
      --> 다음 요청이 이 문서의 버전을 찾을 때 본다
      --> safe-access 모드가 아니면 넣지 않고 unsafe 표시만 한다 (LiveVersionMap L358-371)
      --> unsafe 인 채로 조회가 오면 강제 refresh 가 일어난다 (L1159-1176)

 localCheckpointTracker
      --> 어디까지 처리했고 어디까지 디스크에 있는지를 센다
      --> 글로벌 체크포인트와 복구 범위의 근거다
```

## 다루지 않는 것

`indexBatch` 와 배치 경로의 내부(`planPrimarySubBatch`, 컬럼 경로, 배치 translog 레코드), Lucene `IndexWriter` 의 동작과 세그먼트 생성, `LiveVersionMap` 의 자료구조와 safe-access 모드가 바뀌는 조건, `LocalCheckpointTracker` 의 구현, `Translog.add` 안쪽, 삭제 경로(`delete`/`planDeletionAs*`), refresh 와 flush, CCR `FollowingEngine` 의 전체 동작은 같은 뼈대의 곁가지라 요약만 했다.

## 하위 메서드

- [01 InternalEngine.index](01_InternalEngine.index/README.md)
- [02 indexingStrategyForOperation](02_InternalEngine.indexingStrategyForOperation/README.md)
- [03 planIndexing 세 메서드](03_InternalEngine.planIndexing/README.md)
- [04 indexIntoLucene](04_InternalEngine.indexIntoLucene/README.md)
- [05 writeLuceneDocuments](05_InternalEngine.writeLuceneDocuments/README.md)
- [spi](spi/README.md) — 전략 객체, origin 다섯

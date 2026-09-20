# InternalEngine.writeLuceneDocuments

상위: [엔진 쓰기](../README.md)

**IndexWriter 를 실제로 부르는 자리**다. 세 갈래 중 하나를 고르고, 실패하면 그것이 문서 하나의 문제인지 엔진 전체의 문제인지 판정한다. 단건 경로와 배치의 행 폴백 경로가 공유한다.

## 위치

`server` / `org.elasticsearch.index.engine` / `InternalEngine.java` L2064-L2099 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/engine/InternalEngine.java#L2064-L2099))

## 실제 코드

```java
// InternalEngine.java L2064-L2099 (javadoc 생략)
    private IndexResult writeLuceneDocuments(Engine.Index op, IndexingStrategy plan, List<LuceneDocument> docs) throws IOException {
        try {
            if (plan.addStaleOpToLucene) {
                addStaleDocs(docs, indexWriter);
            } else if (plan.useLuceneUpdateDocument) {
                assert assertMaxSeqNoOfUpdatesIsAdvanced(op.uid(), op.seqNo(), true, true);
                updateDocs(op.uid(), docs, indexWriter);
            } else {
                // document does not exist, we can optimize for create, but double check if assertions are running
                assert assertDocDoesNotExist(op, canOptimizeAddDocument(op) == false);
                addDocs(docs, indexWriter);
            }
            return new IndexResult(plan.versionForIndexing, op.primaryTerm(), op.seqNo(), plan.currentNotFoundOrDeleted, op.id());
        } catch (Exception ex) {
            if (ex instanceof AlreadyClosedException == false
                && indexWriter.getTragicException() == null
                && treatDocumentFailureAsTragicError(op) == false) {
                /* There is no tragic event recorded so this must be a document failure.
                return new IndexResult(ex, Versions.MATCH_ANY, op.primaryTerm(), op.seqNo(), op.id());
            } else {
                throw ex;
            }
        }
    }
```

## 동작 흐름

```text
 L2066  plan.addStaleOpToLucene 이면 addStaleDocs        L2067
 L2068  plan.useLuceneUpdateDocument 이면 updateDocs     L2070
 L2071  아니면 addDocs                                    L2074
 L2076  성공하면 IndexResult
          created 플래그가 plan.currentNotFoundOrDeleted 다

 L2077  catch (Exception ex)
          세 조건을 다 만족하면 문서 실패로 본다           L2078-2080
            AlreadyClosedException 이 아니다
            indexWriter.getTragicException() 이 null 이다
            treatDocumentFailureAsTragicError 가 false 다
          L2094  실패 IndexResult 를 돌려준다. seqNo 는 그대로 담는다
          L2096  아니면 다시 던진다
```

```text
 세 갈래가 하는 일이 다르다

 addDocs        L2142  indexWriter.addDocuments   그냥 추가한다
 updateDocs     L2270  softUpdateDocument(s)      기존 것을 soft-delete 하고 추가
 addStaleDocs   L2147  softDeletesField 를 먼저 붙이고 추가
                       즉 처음부터 삭제된 상태로 들어간다

 셋 다 안에서 docs.size() > 1 인지로 단수/복수 API 를 또 가른다
 nested 문서는 한 요청에 여러 LuceneDocument 가 되기 때문이다

 addDocs 와 updateDocs 는 메트릭을 올리는데 (L2144, L2277)
 addStaleDocs 는 올리지 않는다
```

```text
 어느 갈래가 언제 오는가

 addStaleDocs   processAsStaleOp 하나에서만 온다
                그것은 planIndexingAsNonPrimary 에서만 만들어진다
                즉 프라이머리에서는 이 갈래가 절대 안 온다

 updateDocs     processNormally 에 cNFoD=false 로 들어갈 때만 온다
                "문서가 이미 살아 있었다"가 유일한 근거다

 addDocs        optimizedAppendOnly, 또는 processNormally 에 cNFoD=true
```

```text
 왜 stale op 을 삭제된 상태로 쓰는가

 stale 은 "이미 더 새로운 연산이 적용됐다"는 뜻이다
 그런데 그냥 버리면 안 된다

 그 seqNo 가 Lucene 에 있어야
 복구할 때 "이 번호는 처리됐다"를 알 수 있다

 그래서 검색에는 안 보이게 soft-delete 상태로 넣되
 번호는 남긴다
```

```text
 문서 실패 판정이 [01] 의 것과 다르다

 여기 L2078-2080  ACE 아님 + IW tragic 없음 + treat 아님
 [01] L1391       ACE 아님 + treat 임

 IndexWriter 의 tragic 검사가 여기에만 있다
 주석이 이유를 길게 적어 두었다 (L2081-2093)
   IndexWriter 안에서 여러 예외가 동시에 abort 를 일으키면
   그중 하나만 tragicEventException 이 된다
   그래서 "tragic 이 null 이면 문서 실패"라는 것만 믿을 수 있다
```

## 결과가 쓰이는 곳

```text
 IndexResult
      --> [01] 이 받아 translog 처리로 넘어간다
      --> 실패 결과도 seqNo 를 담는다
          그래서 [01] L1350 이 no-op 을 만들 수 있다

 created 플래그
      --> plan.currentNotFoundOrDeleted 를 그대로 쓴다
      --> REST 응답의 result 가 created 인지 updated 인지가 이 값이다

 soft-delete 필드
      --> updateDocs 와 addStaleDocs 가 붙인다
      --> 머지 때 실제로 지워질 때까지 세그먼트에 남는다
      --> 복구가 이 기록으로 연산 이력을 읽는다
```

## 다루지 않는 것

Lucene `IndexWriter` 의 `addDocuments` / `softUpdateDocuments` 동작과 세그먼트 생성, soft-delete 필드가 머지에서 정리되는 규칙, nested 문서가 여러 `LuceneDocument` 가 되는 파싱 단계, `assertDocDoesNotExist` 가 assert 모드에서 하는 검증, 배치 컬럼 경로의 `indexWriter.addBatch` 는 같은 뼈대의 곁가지라 요약만 했다.

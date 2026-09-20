# InternalEngine.indexIntoLucene

상위: [엔진 쓰기](../README.md)

네 줄짜리 메서드다. 하는 일은 **문서에 seqNo 와 버전을 새기고** [writeLuceneDocuments](../05_InternalEngine.writeLuceneDocuments/README.md)로 넘기는 것뿐이다. 실행 분기가 하나도 없다.

## 위치

`server` / `org.elasticsearch.index.engine` / `InternalEngine.java` L2050-L2062 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/engine/InternalEngine.java#L2050-L2062))

## 실제 코드

```java
// InternalEngine.java L2050-L2062 (javadoc 생략)
    private IndexResult indexIntoLucene(Index index, IndexingStrategy plan) throws IOException {
        assert index.seqNo() >= 0 : "ops should have an assigned seq no.; origin: " + index.origin();
        assert plan.versionForIndexing >= 0 : "version must be set. got " + plan.versionForIndexing;
        assert plan.indexIntoLucene || plan.addStaleOpToLucene;
        /* Update the document's sequence number and primary term; the sequence number here is derived here from either the sequence
        index.parsedDoc().updateSeqID(index.seqNo(), index.primaryTerm());
        index.parsedDoc().version().setLongValue(plan.versionForIndexing);
        logDocumentsDetails(index.docs(), index.id(), index.uid());
        return writeLuceneDocuments(index, plan, index.docs());
    }
```

## 동작 흐름

```text
 L2051-2053  assert 셋
               seqNo 가 배정됐는지
               버전이 설정됐는지
               Lucene 에 쓸 전략이 맞는지

 L2058  index.parsedDoc().updateSeqID(seqNo, primaryTerm)
          파싱해 둔 문서에 번호를 새긴다
 L2059  version 필드에 versionForIndexing 을 넣는다
 L2060  logDocumentsDetails   tsdb + trace 로그일 때만 찍는다
 L2061  writeLuceneDocuments(index, plan, index.docs())
```

```text
 왜 여기서 새기는가

 주석이 적어 두었다 (L2054-2057)
   seqNo 는 프라이머리면 시퀀스 번호 서비스에서,
   레플리카면 기존 문서의 번호에서 온다
   primary term 은 이미 설정돼 있다 (IndexShard#prepareIndex 에서)

 즉 문서는 파싱될 때 만들어지고
 번호는 계획이 끝난 뒤에야 정해지므로
 쓰기 직전인 여기서 합쳐진다
```

```text
 배치는 이 메서드를 안 쓴다

 컬럼 경로는 updateSeqID 대신
 컬럼 버퍼에 직접 스탬프한다 (L1700-1705)

 행 폴백 경로는 [05] 를 직접 부른다 (L1601)
 그래서 [05] 는 단건과 배치가 공유하는 노드다
```

## 결과가 쓰이는 곳

```text
 새겨진 seqNo 와 primary term
      --> Lucene 문서의 필드로 저장된다
      --> 레플리카가 같은 번호로 같은 문서를 만든다
      --> 복구 때 어디까지 적용됐는지 판정하는 근거다

 version 필드
      --> 다음 요청의 버전 충돌 판정에 쓰인다
      --> versionMap 에 없으면 Lucene 에서 이 필드를 읽는다
```

## 다루지 않는 것

`ParsedDocument` 와 `LuceneDocument` 의 구조, `updateSeqID` 가 필드를 채우는 방식, tsdb synthetic id 와 `logDocumentsDetails` 의 조건, 배치 경로의 컬럼 스탬핑은 같은 뼈대의 곁가지라 요약만 했다.

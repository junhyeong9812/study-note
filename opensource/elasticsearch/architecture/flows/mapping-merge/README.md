# 매핑 병합

상위: [Elasticsearch 아키텍처 지도](../../README.md)

매핑을 바꾸는 요청이 들어왔을 때 **`MapperService.mapper` 필드가 새 것으로 갈리기까지**다. 전 구간이 한 스레드에서 동기로 돌고 콜백 경계가 하나도 없다. 대신 갈래를 만드는 것이 **둘**이다 — 누가 부르느냐(마스터냐 데이터 노드냐)와 무엇 때문에 부르느냐(`MergeReason`). 폴더 하나가 메서드 하나이고, [spi](spi/README.md)에 `MergeReason` 계약표가 있다.

기준 커밋: elasticsearch `main` [`60bb239edb`](https://github.com/elastic/elasticsearch/tree/60bb239edb99f0e002eb620e4e82a6f2b15a49b0) (2026-09-19). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 축이 둘이다

 (가) 마스터 쪽 - 병합한다
      [01] merge 세 오버로드          L426 / L438 / L572
           +-- [02] 원시 병합          L503   여러 소스를 합칠 때만
           +-- [03] doMerge            L604
                 +-- [04] mergeBuilders   L623 -> L627
                 |     +-- [05] getBudget L704
                 +-- [06] newDocumentMapper L666
                 +-- this.mapper = newMapper  L617

 (나) 데이터 노드 쪽 - 교체한다
      [07] updateMapping              L395
           +-- buildMapping            L411
           +-- newDocumentMapper       L412
           +-- this.mapper = ...       L412
           예산도 병합도 거치지 않는다

 (다) 대입하지 않는 갈래
      isNoOpUpdate                    L586
           +-- mergeBuilders(static)   L596   계산은 다 하고 버린다
```

```text
 this.mapper 를 쓰는 자리는 정확히 셋이다

 L313  생성자
 L412  updateMapping     데이터 노드
 L617  doMerge           마스터

 필드 선언은 L225 - private volatile DocumentMapper mapper
 읽기는 락 밖에서도 일어난다 (L439, L573)
 쓰기는 L412 와 L617 둘 다 synchronized (this) 안이다
```

```text
 두 축이 왜 갈리는가 - javadoc 이 말한다

 updateMapping L392-394
   "Update local mapping by applying the incoming mapping that have already
    been merged with the current one on the master"

 즉 데이터 노드가 받는 것은 이미 병합이 끝난 결과다
 그래서 한도를 다시 볼 이유가 없다

 실제로 updateMapping 은 한 메서드 안에서 reason 을 바꾼다
   L407  파싱은 MAPPING_UPDATE 로
   L411  빌드는 MAPPING_RECOVERY 로
   L412  검증도 MAPPING_RECOVERY 로

 (주석은 없다. 두 줄을 나란히 놓고 내가 판단한 것이다 -
  마스터가 이미 같은 한도로 걸렀으니 여기서 또 막을 이유가 없다)
```

```text
 콜백 경계가 없다

 MapperService 파일 전체에 ActionListener, Executor, ThreadPool,
 CompletableFuture 가 한 번도 안 나온다

 그래서 이 흐름의 어려움은 "언제 돌아오는가" 가 아니라
 "같은 코드가 이유에 따라 무엇을 다르게 하는가" 다

 다만 부르는 쪽에는 경계가 있다
   TimestampFieldMapperService L132-147 은 executor 에 넣고 나서 merge 를 부른다
   MetadataMappingService 는 마스터의 클러스터 상태 갱신 큐에서 돈다
```

```text
 병합은 두 층에서 일어난다

 원시 층   Map<String,Object> 끼리 합친다        [02]
           소스가 여럿일 때만 (L460)
           파싱을 한 번만 하려고 - javadoc L434-437

 빌더 층   MappingBuilder 끼리 합친다             [04]
           언제나 (기존 매퍼가 있으면 L648)

 아래층은 타입을 모른다. 문자열 키와 맵만 본다
 위층은 파싱된 매퍼 트리를 본다
```

## 어디에서 쓰이는가

```text
 [문서 색인] 동적 매핑이 새 필드를 만나면 마스터에 갱신을 요청한다
      --> 그 요청이 MAPPING_AUTO_UPDATE 로 이 흐름에 들어온다
      --> 보내기 전에 isNoOpUpdate 로 걸러본다

 [구조: 클러스터 상태] 마스터가 병합한 결과가 상태에 실려 퍼진다
      --> 데이터 노드가 그것을 updateMapping 으로 받는다

 [구조: 샤드 복구] 디스크에서 인덱스를 다시 열 때
      --> MAPPING_RECOVERY 로 들어온다. 한도를 안 본다
```

문서를 색인하다 매핑이 바뀌는 쪽은 [문서 색인](../index-document/README.md)에 있다.

## 단계

1. [merge](01_MapperService.merge/README.md) 세 오버로드가 진입점이고, 소스가 여럿이면 먼저 원시 형태로 합친다.
2. [RawFieldMappingMerge](02_RawFieldMappingMerge.merge/README.md)가 그 원시 병합의 규칙이다.
3. [doMerge](03_MapperService.doMerge/README.md)가 파싱하고 잠그고 대입한다.
4. [mergeBuilders](04_MapperService.mergeBuilders/README.md)가 예산을 받아 빌더를 합친다.
5. [getBudget](05_MapperService.getBudget/README.md)이 `MergeReason` 으로 한도 모드를 고른다.
6. [newDocumentMapper](06_MapperService.newDocumentMapper/README.md)가 만들고 검증한다.
7. [updateMapping](07_MapperService.updateMapping/README.md)이 데이터 노드 쪽 교체 경로다.

## 결과가 쓰이는 곳

```text
 this.mapper
      --> 문서 파싱이 이것을 본다 (documentMapper())
      --> 검색의 필드 타입 조회도 이것을 본다 (mappingLookup())
      --> volatile 이라 대입 즉시 다른 스레드에 보인다

 this.mappingVersion
      --> updateMapping 만 갱신한다 (L413)
      --> 다음 클러스터 상태에서 같은 버전이면 그냥 돌아간다 (L399-401)

 doMerge 가 돌려주는 DocumentMapper
      --> 마스터가 그 mappingSource() 를 클러스터 상태에 싣는다

 isNoOpUpdate 의 boolean
      --> 참이면 마스터에 갱신 요청을 아예 안 보낸다
```

## 다루지 않는 것

`RootObjectMapper.Builder.merge` 가 필드 트리를 실제로 합치는 방식과 예산을 소비하는 지점, `MapperMergeContext` 의 자식 컨텍스트 생성, `ObjectMapper`/`NestedObjectMapper` 의 타입별 병합 규칙, `MappingLookup.fromMapping` 이 조회 구조를 만드는 과정, `DocumentMapper.validate` 가 부르는 개별 검사들의 내용, 매핑 갱신 요청이 마스터까지 가는 클러스터 상태 경로(`MetadataMappingService`)는 같은 뼈대의 곁가지라 요약만 했다. `MergeReason` 별 동작 차이는 [spi](spi/README.md)에 표로 모았다.

## 하위 메서드

- [01 merge](01_MapperService.merge/README.md)
- [02 RawFieldMappingMerge.merge](02_RawFieldMappingMerge.merge/README.md)
- [03 doMerge](03_MapperService.doMerge/README.md)
- [04 mergeBuilders](04_MapperService.mergeBuilders/README.md)
- [05 getBudget](05_MapperService.getBudget/README.md)
- [06 newDocumentMapper](06_MapperService.newDocumentMapper/README.md)
- [07 updateMapping](07_MapperService.updateMapping/README.md)
- [spi](spi/README.md) — `MergeReason` 계약표

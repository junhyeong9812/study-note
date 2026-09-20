# MapperService.updateMapping

상위: [매핑 병합](../README.md)

**데이터 노드 쪽 진입점이다.** 이름에 merge 가 없고 실제로도 병합하지 않는다 — 마스터가 이미 합쳐 놓은 매핑을 받아 통째로 갈아끼운다. 예산도 `mergeBuilders` 도 거치지 않는 유일한 경로다.

## 위치

`server` / `org.elasticsearch.index.mapper` / `MapperService.java` L392-L424 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/mapper/MapperService.java#L392-L424))

## 실제 코드

javadoc 이 정체를 한 문장으로 말한다.

> Update local mapping by applying the incoming mapping that have already been merged with the current one on the master

버전이 같으면 아무것도 안 한다.

```java
// MapperService.java L399-L401
        if (currentIndexMetadata != null && currentIndexMetadata.getMappingVersion() == newIndexMetadata.getMappingVersion()) {
            return;
        }
```

파싱하고 잠그고 대입한다.

`server` / `org.elasticsearch.index.mapper` / `MapperService.java` L407-L414 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/mapper/MapperService.java#L407-L414))

```java
// MapperService.java L407-L414
            MappingBuilder incomingBuilder = mappingParser.parseToBuilder(type, MergeReason.MAPPING_UPDATE, incomingMappingSource);
            DocumentMapper previousMapper;
            synchronized (this) {
                previousMapper = this.mapper;
                Mapping incomingMapping = buildMapping(incomingBuilder, MergeReason.MAPPING_RECOVERY);
                this.mapper = newDocumentMapper(incomingMapping, MergeReason.MAPPING_RECOVERY, incomingMappingSource);
                this.mappingVersion = newIndexMetadata.getMappingVersion();
            }
```

그리고 로그를 남긴다.

```java
// MapperService.java L415-L422
            String op = previousMapper != null ? "updated" : "added";
            if (logger.isDebugEnabled() && incomingMappingSource.compressed().length < 512) {
                logger.debug("[{}] {} mapping, source [{}]", index(), op, incomingMappingSource.string());
            } else if (logger.isTraceEnabled()) {
                logger.trace("[{}] {} mapping, source [{}]", index(), op, incomingMappingSource.string());
            } else {
                logger.debug("[{}] {} mapping (source suppressed due to length, use TRACE level if needed)", index(), op);
            }
```

## 동작 흐름

```text
 L396  assert 인덱스가 맞는지
 L399  이전 메타데이터가 있고 mappingVersion 이 같으면 => return
 L403  새 매핑 메타데이터
 L404  null 이면 아무것도 안 한다
 L407  parseToBuilder(type, MAPPING_UPDATE, source)
 L409  synchronized (this)
 L410    previousMapper = this.mapper
 L411    incomingMapping = buildMapping(incomingBuilder, MAPPING_RECOVERY)
 L412    this.mapper = newDocumentMapper(incomingMapping, MAPPING_RECOVERY, source)
 L413    this.mappingVersion = newIndexMetadata.getMappingVersion()
 L415  op = previousMapper != null ? "updated" : "added"
 L416  디버그 켜져 있고 소스가 512바이트 미만이면 소스까지 찍는다
 L418  트레이스면 길이 무관하게 소스를 찍는다
 L420  아니면 소스를 생략하고 찍는다
```

```text
 한 메서드 안에서 reason 이 바뀐다

 L407  파싱은  MAPPING_UPDATE
 L411  빌드는  MAPPING_RECOVERY
 L412  검증도  MAPPING_RECOVERY

 결과가 이렇게 갈린다
   파싱 시점 한도는 걸린다
     ParseFieldLimits.parseFieldLimits(MAPPING_UPDATE, …) L50-51
     => throwing(totalLimit, totalLimit)
   병합 시점 예산은 아예 없다 - mergeBuilders 를 안 타니까
   checkLimits 는 false - RECOVERY 라서 (L676)

 (주석은 없다. 세 줄의 인자를 나란히 놓고 내가 판단한 것이다.
  마스터가 이미 같은 한도로 걸렀으니 여기서 또 막을 이유가 없다는 뜻으로 읽었다)
```

```text
 병합이 없다는 것이 무슨 뜻인가

 doMerge 경로
   기존 매퍼를 다시 파싱하고 (L647)
   들어온 것을 거기에 합치고 (L648)
   결과를 빌드한다 (L649)

 updateMapping 경로
   들어온 것만 파싱하고 (L407)
   그대로 빌드한다 (L411)

 기존 매퍼를 읽는 유일한 자리가 L410 인데
 그것도 로그 문구를 고르는 데만 쓴다 (L415 의 "updated" / "added")
```

```text
 mappingVersion 이 여기서만 움직인다

 필드 선언 L226  private volatile long mappingVersion;
 대입     L413   여기 한 곳
 읽기     L399   여기 한 곳

 즉 이 필드는 updateMapping 의 자기 중복 방지용이다
 클러스터 상태는 바뀌지 않아도 여러 번 적용될 수 있는데
 매핑이 그대로면 재파싱과 재빌드를 건너뛰는 것이다
```

```text
 호출처가 셋이다

 IndexService L916
 IndicesClusterStateService L791   첫 인자에 null 을 넘긴다
 IndicesClusterStateService L851

 L791 이 null 을 넘기면 L399 의 조건이 거짓이 되어
 버전이 같아도 건너뛰지 않는다
 (그 자리가 왜 null 인지는 IndicesClusterStateService 를 끝까지 읽지 않아
  확인하지 못했다)
```

```text
 this.mapper 를 쓰는 자리는 통틀어 셋이다

 L313  생성자
 L412  여기
 L617  doMerge

 L412 와 L617 은 둘 다 synchronized (this) 안이다
 서로 다른 메서드지만 같은 객체를 잠그므로 배타적이다
```

## 결과가 쓰이는 곳

```text
 this.mapper
      --> 이 노드의 문서 파싱과 검색이 즉시 새 매핑을 쓴다
      --> volatile 이라 락 밖 읽기도 최신을 본다

 this.mappingVersion
      --> 다음 클러스터 상태 적용에서 같은 버전이면 통째로 건너뛴다

 로그
      --> "added" 면 이 노드에서 처음 만들어진 매핑이다
      --> 512바이트 기준으로 소스를 찍을지 정한다
```

## 다루지 않는 것

`IndicesClusterStateService` 가 클러스터 상태를 적용하며 이 메서드를 부르는 조건과 순서, `IndexService.updateMetadata` 의 나머지 갱신, 마스터가 병합 결과를 클러스터 상태에 싣는 경로(`MetadataMappingService`), `IndexMetadata.getMappingVersion` 이 증가하는 시점은 같은 뼈대의 곁가지라 요약만 했다.

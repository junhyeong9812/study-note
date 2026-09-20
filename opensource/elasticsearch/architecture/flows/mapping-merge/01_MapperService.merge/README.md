# MapperService.merge

상위: [매핑 병합](../README.md)

**마스터 쪽 진입점이다.** 같은 이름의 오버로드가 셋인데, 하나는 나머지로 위임하고 둘은 각자 `doMerge` 로 간다. 리스트 판만 원시 병합을 거친다.

## 위치

`server` / `org.elasticsearch.index.mapper` / `MapperService.java` L426-L467 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/mapper/MapperService.java#L426-L467))

## 실제 코드

메타데이터 판은 껍데기다.

```java
// MapperService.java L426-L432
    public void merge(IndexMetadata indexMetadata, MergeReason reason) {
        assert reason != MergeReason.MAPPING_AUTO_UPDATE_PREFLIGHT;
        MappingMetadata mappingMetadata = indexMetadata.mapping();
        if (mappingMetadata != null) {
            merge(mappingMetadata.type(), mappingMetadata.source(), reason);
        }
    }
```

단일 소스 판은 같으면 그대로 돌려준다.

`server` / `org.elasticsearch.index.mapper` / `MapperService.java` L573-L576 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/mapper/MapperService.java#L573-L576))

```java
// MapperService.java L573-L576
        final DocumentMapper currentMapper = this.mapper;
        if (currentMapper != null && currentMapper.mappingSource().equals(mappingSource)) {
            return currentMapper;
        }
```

리스트 판은 javadoc 이 존재 이유를 적어 두었다.

`server` / `org.elasticsearch.index.mapper` / `MapperService.java` L434-L437 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/mapper/MapperService.java#L434-L437))

> Merging the provided mappings. Actual merging is done in the raw, non-parsed, form of the mappings. This allows to do a proper bulk merge, where parsing is done only when all raw mapping settings are already merged.

루트를 하나로 맞춘다.

`server` / `org.elasticsearch.index.mapper` / `MapperService.java` L449-L455 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/mapper/MapperService.java#L449-L455))

```java
// MapperService.java L449-L455
            if (rawMapping.containsKey(type)) {
                if (rawMapping.size() > 1) {
                    throw new MapperParsingException("cannot merge a map with multiple roots, one of which is [" + type + "]");
                }
            } else {
                rawMapping = Map.of(type, rawMapping);
            }
```

그리고 두 번째부터 합친다.

```java
// MapperService.java L457-L461
            if (mergedRawMapping == null) {
                mergedRawMapping = rawMapping;
            } else {
                XContentHelper.merge(type, mergedRawMapping, rawMapping, RawFieldMappingMerge.INSTANCE);
            }
```

## 동작 흐름

```text
 [01] merge(IndexMetadata, MergeReason)              L426
      L427  assert reason != MAPPING_AUTO_UPDATE_PREFLIGHT
      L428  indexMetadata.mapping()
      L429  null 이 아니면
      L430    merge(type, source, reason)  <- 단일 소스 판으로
      null 이면 아무것도 안 한다. 반환형도 void 다

 [02] merge(String, CompressedXContent, MergeReason) L572
      L573  final DocumentMapper currentMapper = this.mapper
      L574  현재 소스와 같으면 => 그대로 돌려준다
      L577  convertToMap
      L578  doMerge(type, reason, map)

 [03] merge(String, List<CompressedXContent>, …)     L438
      L439  final DocumentMapper currentMapper = this.mapper
      L440  소스가 하나이고 현재와 같으면 => 그대로 돌려준다
      L445  소스마다
      L446    convertToMap
      L449    type 키가 있는데 다른 키도 있으면 => 예외 (L451)
      L453    type 키가 없으면 Map.of(type, raw) 로 씌운다 (L454)
      L457    첫 번째면 그대로 받고
      L459    아니면 XContentHelper.merge 로 합친다 (L460)
      L463  합친 결과의 루트가 여럿이면 => 예외 (L464)
      L466  doMerge(...) 또는 null
```

```text
 L439 와 L573 이 같은 일을 한다

 final DocumentMapper currentMapper = this.mapper;

 필드는 volatile 이다 (L225)
 그리고 이 읽기는 synchronized 밖이다

 그래서 여기서 "같다"고 판정해 돌려준 매퍼가
 반환된 순간에는 이미 낡았을 수 있다

 (주석은 없다. volatile 선언과 락의 위치를 보고 내가 판단한 것이다)
```

```text
 빈 리스트를 주면 null 이 나온다

 L445 의 루프가 한 번도 안 돌면
 mergedRawMapping 이 null 로 남고
 L466 의 삼항이 null 을 고른다

 현재 매퍼를 돌려주는 것이 아니다
 호출자가 바로 .mappingSource() 를 부르면 NPE 다
```

```text
 루트 정규화가 하는 일

 들어오는 원시 맵의 모양이 두 가지다
   { "_doc": { "properties": ... } }    루트가 이미 있다
   { "properties": ... }                 루트가 없다

 L449  type 키가 있으면 - 다른 키가 더 있으면 예외
         "cannot merge a map with multiple roots, one of which is [_doc]"
 L453  없으면 Map.of(type, raw) 로 씌운다

 이걸 먼저 해야 L460 의 병합이 같은 깊이끼리 만난다
```

```text
 원시 병합은 리스트 판에만 있다

 XContentHelper.merge 를 부르는 곳은 이 파일에 둘뿐이다
   L460  이 루프
   L525  RawFieldMappingMerge 자신의 재귀

 단일 소스 판(L572)은 원시 병합을 아예 안 탄다
 그래서 [02] 의 규칙은 [01]·[03] 과 다르다
```

## 결과가 쓰이는 곳

```text
 합쳐진 원시 맵
      --> doMerge 가 이것을 파싱한다
      --> 파싱이 한 번만 일어나는 이유다 (javadoc L434-437)

 early return 이 돌려주는 현재 매퍼
      --> 같은 매핑을 다시 넣는 요청이 잠금을 안 거친다
      --> 클러스터 상태가 재전송될 때 흔한 경로다

 [01] 의 void 반환
      --> 호출자가 결과를 안 본다는 뜻이다
      --> 복구 경로가 주로 이것을 쓴다
```

## 다루지 않는 것

`XContentHelper.merge` 의 기본 병합 규칙(리스트 결합, 재귀 진입 조건)과 `CompressedXContent` 의 압축·비교, `MappingParser.convertToMap` 의 JSON 변환, 이 오버로드들을 부르는 클러스터 상태 쪽 코드(`MetadataMappingService`, `MetadataCreateIndexService`, `MetadataIndexTemplateService`)의 사정은 같은 뼈대의 곁가지라 요약만 했다. 원시 병합 규칙 자체는 [RawFieldMappingMerge](../02_RawFieldMappingMerge.merge/README.md)에 있다.

# MapperService.newDocumentMapper

상위: [매핑 병합](../README.md)

`Mapping` 을 `DocumentMapper` 로 만들고 **검증한다.** 열세 줄인데 흥미로운 것은 마지막 두 번째 줄 하나다 — `reason` 이 `boolean` 하나로 줄어드는 자리.

## 위치

`server` / `org.elasticsearch.index.mapper` / `MapperService.java` L666-L678 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/mapper/MapperService.java#L666-L678))

## 실제 코드

```java
// MapperService.java L667-L677
        DocumentMapper newMapper = new DocumentMapper(
            documentParser,
            mapping,
            mappingSource,
            indexVersionCreated,
            mapperMetrics,
            index().getName(),
            indexMode
        );
        newMapper.validate(indexSettings, reason != MergeReason.MAPPING_RECOVERY);
        return newMapper;
```

## 동작 흐름

```text
 L667  new DocumentMapper(documentParser, mapping, mappingSource,
                          indexVersionCreated, mapperMetrics,
                          index().getName(), indexMode)
 L676  newMapper.validate(indexSettings, reason != MergeReason.MAPPING_RECOVERY)
 L677  return newMapper
```

```text
 L676 의 둘째 인자가 끄는 것은 한 줄뿐이다

 DocumentMapper.validate(settings, checkLimits) 의 마지막 블록이다 (L220-222)

   if (checkLimits) {
       this.mappingLookup.checkLimits(settings);
   }

 그 앞의 검사는 reason 과 무관하게 전부 돈다
   L137      mapping().validate(mappingLookup)
   L138-149  routing partitioned index 면 _routing.required 가 있어야 한다
   L150-160  slice 가 켜져 있으면 _routing 을 건드리면 안 된다
   L162      인덱스 모드별 매핑 검사
   L167-172  빈 소스 로더를 만들어 소스 전략과 호환되는지 본다
   L174-187  index sort 와 nested 필드는 같이 못 쓴다
   L188-203  runtime field 가 sort field 를 가리면 안 된다
   L204-219  routing_path 에 오브젝트 타입이 오면 안 된다

 즉 복구도 검증을 받는다. 한도 검사만 면제다
```

```text
 면제되는 한도 검사가 무엇인가

 MappingLookup.checkLimits (L417-420)
   checkNestedParentsLimit(settings.getMappingNestedParentsLimit())
   checkDimensionFieldLimit(settings.getMappingDimensionFieldsLimit())

 둘뿐이다. 총 필드 수는 여기 없다

 총 필드 수는 예산이 본다 - 그리고 예산도 RECOVERY 면 무제한이다 (L705)
 그래서 복구 경로는 한도 전체를 빠져나간다
```

```text
 복구가 한도를 면제받는 이유를 주석이 말한다

 getBudget L706
   "Recovery re-loads a mapping that was already validated when first written;
    no limit needed."

 처음 쓸 때 이미 검증했으니 다시 안 본다는 것이다
 한도 설정을 나중에 낮췄더라도 기존 인덱스는 열려야 하기 때문이다
 (뒷문장은 주석에 없다. 면제의 범위를 보고 내가 붙인 것이다)
```

```text
 이 메서드에 대입이 없다는 것이 중요하다

 validate 는 void 다. 실패를 예외로만 알린다
 그리고 this.mapper 대입은 호출자 쪽 다음 줄이다 (L617)

 즉 검증 실패 -> 예외 -> L617 에 도달 못 함 -> 기존 매핑 유지

 updateMapping 쪽은 반대다 (L412)
   this.mapper = newDocumentMapper(...)
 한 줄에 붙어 있지만 순서는 같다 - 메서드가 끝나야 대입이 된다
```

```text
 호출자가 둘이다

 L616  doMerge            reason 이 그대로 온다
 L412  updateMapping      MAPPING_RECOVERY 로 하드코딩돼 온다

 그래서 데이터 노드 경로는 언제나 checkLimits=false 다
```

## 결과가 쓰이는 곳

```text
 DocumentMapper
      --> doMerge L617 또는 updateMapping L412 가 this.mapper 에 넣는다
      --> 그 안의 MappingLookup 이 필드 타입 조회의 실체다
      --> mappingSource() 가 다음 병합의 early return 비교 대상이 된다

 validate 가 던진 예외
      --> 대입 전이라 기존 매핑이 살아남는다
      --> 마스터 쪽이면 클러스터 상태 갱신이 실패로 끝난다
```

## 다루지 않는 것

`DocumentMapper` 생성자가 `MappingLookup.fromMapping` 으로 조회 구조를 만드는 과정, `Mapping.validate` 의 내용, `validate` 가 부르는 개별 검사들(소스 로더 호환성, index sort 와 nested 의 충돌, routing_path 검사)의 사정, `MapperMetrics` 의 지표 수집은 같은 뼈대의 곁가지라 요약만 했다.

# MapperService.getBudget

상위: [매핑 병합](../README.md)

**`MergeReason` 이 한도 정책으로 바뀌는 자리다.** 열여덟 줄짜리 메서드인데 이 흐름에서 이유가 가장 직접적으로 동작을 가르는 곳이다. 주석 셋이 각 갈래의 이유를 적어 두었다.

## 위치

`server` / `org.elasticsearch.index.mapper` / `MapperService.java` L704-L722 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/mapper/MapperService.java#L704-L722))

## 실제 코드

복구는 한도가 없다.

```java
// MapperService.java L705-L708
        if (reason == MergeReason.MAPPING_RECOVERY) {
            // Recovery re-loads a mapping that was already validated when first written; no limit needed.
            return NewFieldsBudget.unlimited();
        }
```

> Recovery re-loads a mapping that was already validated when first written; no limit needed.

나머지는 남은 용량을 세어 두 갈래로 간다.

```java
// MapperService.java L709-L721
        long totalFieldsLimit = indexSettings.getMappingTotalFieldsLimit();
        long remaining = Optional.ofNullable(currentMapper)
            .map(DocumentMapper::mappers)
            .map(ml -> ml.remainingFieldsUntilLimit(totalFieldsLimit))
            .orElse(totalFieldsLimit);
        if (reason.isAutoUpdate() && indexSettings.isIgnoreDynamicFieldsBeyondLimit()) {
            // Auto-updates with ignore_dynamic_beyond_limit silently drop fields once the limit is hit.
            // Concurrent updates from data nodes may race; the master trims to the actual remaining capacity.
            return NewFieldsBudget.dropping(remaining);
        }
        // Explicit mapping updates (MAPPING_UPDATE, INDEX_TEMPLATE) and auto-updates without
        // ignore_dynamic_beyond_limit must reject mappings that exceed the limit.
        return NewFieldsBudget.throwing(remaining, totalFieldsLimit);
```

> Auto-updates with ignore_dynamic_beyond_limit silently drop fields once the limit is hit.
>
> Concurrent updates from data nodes may race; the master trims to the actual remaining capacity.

> Explicit mapping updates (MAPPING_UPDATE, INDEX_TEMPLATE) and auto-updates without ignore_dynamic_beyond_limit must reject mappings that exceed the limit.

## 동작 흐름

```text
 L705  reason == MAPPING_RECOVERY
         => NewFieldsBudget.unlimited()

 L709  totalFieldsLimit = 설정값
 L710  remaining =
         현재 매퍼가 있으면  mappers().remainingFieldsUntilLimit(totalFieldsLimit)
         없으면              totalFieldsLimit

 L714  reason.isAutoUpdate() && indexSettings.isIgnoreDynamicFieldsBeyondLimit()
         => NewFieldsBudget.dropping(remaining)

 L721  그 외
         => NewFieldsBudget.throwing(remaining, totalFieldsLimit)
```

```text
 세 모드의 차이가 실제로는 한 줄이다 (NewFieldsBudget)

 Unlimited  L65-73    hasCapacityFor 도 decrementIfPossible 도 언제나 true
 Limited    L84-96    가능하면 빼고 true, 아니면 false
 Throwing   L109-121  가능하면 빼고 true, 아니면 예외

 Limited 와 Throwing 의 hasCapacityFor 는 완전히 같다 (L85-87, L110-112)
 다른 것은 decrementIfPossible 뿐이고
 그 안에서도 다른 줄은 하나다

   Limited  L95   return false
   Throwing L120  throw new IllegalArgumentException(...)

 즉 "조용히 버린다"와 "거절한다"의 차이가 한 줄이다
```

```text
 dropping 이 unlimited 로 접히는 경우가 있다

 NewFieldsBudget L33-38
   static NewFieldsBudget dropping(long fieldsBudget) {
       if (fieldsBudget == Long.MAX_VALUE) {
           return Unlimited.INSTANCE;
       }
       return new Limited(fieldsBudget);
   }

 remaining 이 Long.MAX_VALUE 로 들어오면 모드가 바뀐다
 팩터리 셋과 구현 클래스 셋이 1:1 이 아니다
```

```text
 remaining 은 음수가 될 수 있다

 MappingLookup L422-424
   long remainingFieldsUntilLimit(long mappingTotalFieldsLimit) {
       return mappingTotalFieldsLimit - totalFieldsCount;
   }

 이미 한도를 넘긴 상태면 음수가 나온다
 음수로 Throwing 을 만들면 첫 필드부터 예외다

 한도 설정을 낮춘 뒤 매핑을 건드리면 이 상태가 된다
 (주석은 없다. 뺄셈 한 줄과 Throwing 의 조건을 보고 내가 판단한 것이다)
```

```text
 주석 L716 이 왜 저 말을 하는가

   "Concurrent updates from data nodes may race;
    the master trims to the actual remaining capacity."

 동적 매핑은 데이터 노드가 문서를 색인하다 발견한다
 여러 샤드가 동시에 새 필드를 발견하면 갱신 요청이 여러 개 온다

 각 요청은 자기가 볼 때의 남은 용량을 근거로 만들어진다
 그런데 마스터에 도착할 때쯤이면 앞선 요청이 이미 용량을 썼을 수 있다

 그래서 마스터가 여기서 다시 센다 - remaining 을 그 시점에 계산한다
```

```text
 이 판단이 유일하지 않다

 같은 3갈래가 파싱 시점에 한 번 더 있다
   ParseFieldLimits.parseFieldLimits(reason, indexSettings)  L41-52

 셋째 갈래가 다르다
   파싱  throwing(totalLimit, totalLimit)    전체 한도
   병합  throwing(remaining, totalLimit)      남은 용량

 표는 spi 에 있다
```

## 결과가 쓰이는 곳

```text
 NewFieldsBudget
      --> 기존 매퍼가 없으면 applyFieldsBudget 을 거쳐 들어간다 (L637, L654)
      --> 있으면 ParseFieldLimits.forMerge 에 실려 들어간다 (L646)
      --> 필드 트리를 만들며 decrementIfPossible 로 소비된다

 dropping 을 골랐을 때
      --> 초과분이 결과 매핑에서 그냥 빠진다
      --> 요청은 성공한다. 사용자는 필드가 없다는 것만 나중에 안다

 throwing 을 골랐을 때
      --> IllegalArgumentException
      --> 기존 매퍼가 없는 경로에서만 MapperParsingException 으로 포장된다
```

## 다루지 않는 것

`IndexSettings` 의 한도 설정들(`index.mapping.total_fields.limit`, `index.mapping.total_fields.ignore_dynamic_beyond_limit`, `index.mapping.nested_fields.limit`)의 기본값과 동적 갱신, `MappingLookup.totalFieldsCount` 가 무엇을 세는지, 예산이 실제로 소비되는 지점(`RootObjectMapper.Builder.merge` 아래), `MapperMergeContext` 가 형제 오브젝트끼리 예산을 공유하는 방식은 같은 뼈대의 곁가지라 요약만 했다. 이유별 표는 [spi](../spi/README.md)에 있다.

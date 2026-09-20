# MapperService.mergeBuilders

상위: [매핑 병합](../README.md)

빌더 층의 병합이다. **기존 매퍼가 있느냐 없느냐로 코드가 완전히 갈린다** — 예산을 먹이는 방법도, 예외 타입도, try/catch 유무도 다르다.

## 위치

`server` / `org.elasticsearch.index.mapper` / `MapperService.java` L627-L650 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/mapper/MapperService.java#L627-L650))

## 실제 코드

기존 매퍼가 없으면.

`server` / `org.elasticsearch.index.mapper` / `MapperService.java` L634-L642 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/mapper/MapperService.java#L634-L642))

```java
// MapperService.java L635-L643
        if (currentMapper == null) {
            try {
                return buildMapping(applyFieldsBudget(incomingBuilder, budget, reason), reason);
            } catch (MapperParsingException e) {
                throw e;
            } catch (Exception e) {
                throw new MapperParsingException("Failed to parse mapping: {}", e, e.getMessage());
            }
        }
```

있으면.

```java
// MapperService.java L644-L649
        long nestedFieldsLimit = reason == MergeReason.MAPPING_RECOVERY ? Long.MAX_VALUE : indexSettings.getMappingNestedFieldsLimit();
        long existingNestedCount = currentMapper.mappers().nestedLookup().getNestedMappers().size();
        ParseFieldLimits fieldLimits = ParseFieldLimits.forMerge(nestedFieldsLimit, existingNestedCount, budget);
        MappingBuilder existingBuilder = mappingParser.parseToBuilder(currentMapper.type(), reason, currentMapper.mappingSource());
        existingBuilder.merge(incomingBuilder, reason, fieldLimits);
        return buildMapping(existingBuilder, reason);
```

예산을 먹이는 우회로.

`server` / `org.elasticsearch.index.mapper` / `MapperService.java` L652-L656 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/mapper/MapperService.java#L652-L656))

```java
// MapperService.java L652-L656
    private static MappingBuilder applyFieldsBudget(MappingBuilder builder, NewFieldsBudget budget, MergeReason reason) {
        MappingBuilder shallowBuilder = builder.withoutMappers();
        shallowBuilder.merge(builder, reason, ParseFieldLimits.withBudget(budget));
        return shallowBuilder;
    }
```

## 동작 흐름

```text
 L634  budget = getBudget(currentMapper, indexSettings, reason)
         기존 매퍼가 있든 없든 먼저 부른다

 L635  currentMapper == null 인가

 예 (새 인덱스)
   L637  buildMapping(applyFieldsBudget(incomingBuilder, budget, reason), reason)
   L638  catch (MapperParsingException) => 그대로 다시 던진다
   L640  catch (Exception)              => MapperParsingException 으로 감싼다

 아니오 (기존 매핑이 있다)
   L644  nestedFieldsLimit = RECOVERY 면 Long.MAX_VALUE, 아니면 설정값
   L645  existingNestedCount = 현재 매퍼의 nested 개수
   L646  fieldLimits = ParseFieldLimits.forMerge(nested, existingCount, budget)
   L647  existingBuilder = parseToBuilder(현재 매퍼의 소스)
   L648  existingBuilder.merge(incomingBuilder, reason, fieldLimits)
   L649  buildMapping(existingBuilder, reason)
         try/catch 가 없다
```

```text
 applyFieldsBudget 이 이상하게 생긴 이유

 L653  shallowBuilder = builder.withoutMappers()
 L654  shallowBuilder.merge(builder, reason, withBudget(budget))
 L655  return shallowBuilder

 빈 껍데기를 만들고 원본을 **자기 자신에게 다시 병합**한다

 withoutMappers 의 javadoc 이 용도를 말한다 (MappingBuilder L52-53)
   "Creates a new MappingBuilder with the same root settings and metadata but no
    child mappers in the root. Useful for applying field budget constraints
    without decomposing a built mapping."

 즉 예산을 먹일 수 있는 코드 경로가 merge 하나뿐이라
 기존 매퍼가 없을 때도 merge 를 한 번 통과시키는 것이다
 (뒷문장은 주석에 없다. 두 경로를 비교하고 내가 판단한 것이다)
```

```text
 그래서 예산이 도착하는 길이 둘이다

 기존 매퍼 없음  applyFieldsBudget -> ParseFieldLimits.withBudget(budget)   L654
 기존 매퍼 있음  ParseFieldLimits.forMerge(nested, count, budget)           L646

 그런데 둘이 끄는 한도가 다르다 (ParseFieldLimits L65-67, L73-75)

   forMerge     필드명 길이 한도를 끈다. nested 한도는 건다
   withBudget   필드명 길이도 nested 도 둘 다 끈다

 즉 새 인덱스 경로에서는 병합 단계의 nested 한도가 적용되지 않는다
 파싱 단계의 한도가 대신 막는다
```

```text
 예외 타입이 비대칭이다

 예산이 바닥나면 Throwing.decrementIfPossible 이 던진다 (NewFieldsBudget L120)
   IllegalArgumentException("Limit of total fields [N] has been exceeded")

 기존 매퍼 없음  L636-642 의 try/catch 가 잡아 MapperParsingException 으로 감싼다
 기존 매퍼 있음  L644-649 에 try/catch 가 없다. IAE 가 그대로 올라간다

 같은 사건인데 새 인덱스냐 기존 인덱스냐에 따라 타입이 다르다
 (주석은 없다. 두 갈래의 try/catch 유무를 보고 내가 판단한 것이다)
```

```text
 L638-639 의 catch 가 비어 보이는 이유

 catch (MapperParsingException e) { throw e; }

 buildMapping(L658-663)이 이미 MapperParsingException 으로 감싼다
 이 catch 가 없으면 L640-642 가 그것을 한 번 더 감쌀 것이다

 즉 이중 포장을 막는 장치다
```

```text
 L647 이 매번 하는 일

 parseToBuilder(currentMapper.type(), reason, currentMapper.mappingSource())

 **기존 매핑 전체를 매 병합마다 다시 파싱한다**

 기존 매퍼는 이미 파싱된 트리를 들고 있는데도 그렇다
 병합이 빌더 층에서 일어나고 매퍼에서 빌더로 되돌리는 길이 없기 때문이다
 (주석은 없다. MappingBuilder 에 매퍼를 받는 생성자가 없는 것을 보고 판단했다)
```

```text
 다른 호출자가 하나 더 있다

 isNoOpUpdate(L586-598)가 static 판을 직접 부른다 (L596)

   mergeBuilders(mappingParser, indexSettings, updateBuilder,
                 MAPPING_AUTO_UPDATE_PREFLIGHT, existing)

 여기서 다섯째 인자가 this.mapper 가 아니다
 그리고 결과를 대입하지 않고 바이트로 비교만 한다 (L597)

 static 으로 뽑아 둔 것이 그래서다
```

## 결과가 쓰이는 곳

```text
 돌려준 Mapping
      --> doMerge L616 이 DocumentMapper 로 만든다
      --> isNoOpUpdate L597 은 직렬화해 비교하고 버린다

 소진된 예산
      --> dropping 이면 초과분 필드가 결과에서 빠진다
      --> throwing 이면 여기서 끝난다

 existingBuilder
      --> 제자리에서 바뀐다 (MappingBuilder javadoc L68-69 "mutating this builder in place")
      --> 그래서 L649 가 그것을 그대로 빌드한다
```

## 다루지 않는 것

`MappingBuilder.mergeWith` 가 루트 오브젝트와 메타데이터 필드를 합치는 규칙(`INDEX_TEMPLATE` 분기 둘은 [spi](../spi/README.md)에 있다), `RootObjectMapper.Builder.merge` 가 필드 트리를 순회하며 예산을 소비하는 지점, `MapperMergeContext` 가 자식 컨텍스트로 예산을 나르는 방식, `MappingBuilder.build` 의 빌드 순서는 같은 뼈대의 곁가지라 요약만 했다. 예산 모드 선택은 [getBudget](../05_MapperService.getBudget/README.md)에 있다.

# RawFieldMappingMerge.merge

상위: [매핑 병합](../README.md)

매핑 소스를 **파싱하기 전에** 맵끼리 합칠 때 쓰는 규칙이다. `XContentHelper` 의 기본 병합은 "먼저 것이 이긴다"인데, 이 구현이 그걸 뒤집는다. 필드 매핑에서는 나중 것이 이겨야 하기 때문이다.

## 위치

`server` / `org.elasticsearch.index.mapper` / `MapperService.java` L494-L546 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/mapper/MapperService.java#L494-L546))

## 실제 코드

기본 병합이 무엇인지 javadoc 이 먼저 적는다.

`server` / `org.elasticsearch.index.mapper` / `MapperService.java` L471-L475 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/mapper/MapperService.java#L471-L475))

> The default raw map merge algorithm doesn't override values - if there are multiple values for a key, then: if the values are of map type, the old and new values will be merged recursively; otherwise, the original value will be maintained

그리고 무엇을 다르게 할지 적는다.

`server` / `org.elasticsearch.index.mapper` / `MapperService.java` L486-L491 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/mapper/MapperService.java#L486-L491))

> otherwise, for any couple of non-mergeable types ((e.g `object -> long`, `long -> long`) - we just want to replace the entire mappings subtree, let the last one win

> any non-map values - override the value of the base map with the value of the merged map

합칠 수 있는 타입이면 둘만 남긴다.

`server` / `org.elasticsearch.index.mapper` / `MapperService.java` L512-L526 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/mapper/MapperService.java#L512-L526))

```java
// MapperService.java L512-L526
                        Map<String, Object> mergedMappings = new HashMap<>();
                        // we must keep the "properties" node, otherwise our merge has no point
                        if (baseMap.containsKey("properties")) {
                            mergedMappings.put("properties", new HashMap<>((Map<String, Object>) baseMap.get("properties")));
                        }
                        // the "subobjects" setting affects an entire subtree and not only locally where it is configured
                        if (baseMap.containsKey("subobjects")) {
                            mergedMappings.put("subobjects", baseMap.get("subobjects"));
                        }
                        // Recursively merge these two field mappings.
                        // Since "key" is an arbitrary field name, for which we only need plain mapping subtrees merge, no need to pass it
                        // to the recursion as it shouldn't affect the merge logic. Specifically, passing a parent may cause merge
                        // failures of fields named "properties". See https://github.com/elastic/elasticsearch/issues/108866
                        XContentHelper.merge(mergedMappings, mapToMerge, INSTANCE);
                        return mergedMappings;
```

아니면 통째로 바꾼다.

```java
// MapperService.java L528-L529
                        // non-mergeable types - replace the entire mapping subtree for this field
                        return mapToMerge;
```

`properties` 아래가 아니면 손대지 않는다.

```java
// MapperService.java L532-L534
                // anything else (e.g. "_doc", "_meta", "properties") - no custom merge, rely on caller merge logic
                // field mapping entries of Map type (like "fields" and "meta") are handled above and should never reach here
                return null;
```

맵이 아닌 값은 나중 것이 이긴다. 예외가 하나 있다.

`server` / `org.elasticsearch.index.mapper` / `MapperService.java` L536-L544 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/mapper/MapperService.java#L536-L544))

```java
// MapperService.java L536-L544
                if (key.equals("required")) {
                    // we look for explicit `_routing.required` settings because we use them to detect contradictions of this setting
                    // that comes from mappings with such that comes from the optional `data_stream` configuration of composable index
                    // templates
                    if ("_routing".equals(parent) && oldValue != newValue) {
                        throw new MapperParsingException("contradicting `_routing.required` settings");
                    }
                }
                return newValue;
```

## 동작 흐름

```text
 merge(parent, key, oldValue, newValue)           L503

 둘 다 Map 인가                                   L504
   예 → parent 가 "properties" 인가               L505
          예 → 합칠 수 있는 타입인가              L509
                 예 → properties 와 subobjects 만 남기고 재귀   L512-526
                 아니오 → 서브트리를 통째로 교체              L529
          아니오 → null 을 돌려준다                L534
   아니오 → key 가 "required" 인가                L536
              예 → parent 가 "_routing" 이고 값이 다르면 예외  L540-541
            newValue 를 돌려준다                   L544
```

```text
 불리는 조건 자체가 좁다 (XContentHelper L450-521)

 L451-453  양쪽 맵에 같은 키가 있을 때만 불린다
           없으면 그냥 복사하고 끝이다

 L477-513  List 와 List 를 만나면 **절대 안 불린다**
           주석 L504: "custom merge is not applicable here"

 즉 dynamic_templates 처럼 리스트로 쓰는 것은 이 규칙 밖이다
```

```text
 null 을 돌려주는 것이 "안 한다"가 아니다

 L534 가 null 을 돌려주면
 XContentHelper 가 L470-475 로 간다

   merge(toMergeEntry.getKey(), baseValue, toMergeEntry.getValue(), customMerge)

 즉 **키를 새 parent 로 삼아** 한 단계 내려가 다시 부른다
 그래서 "_doc" 아래 "properties" 를 지나면
 다음 레벨의 parent 가 "properties" 가 되고
 그때부터 L505 의 특별 처리가 걸린다

 parent 가 "properties" 인지 보는 것으로
 "지금 보고 있는 키가 필드 이름인가" 를 판정하는 셈이다
```

```text
 재귀는 parent 를 일부러 버린다

 L525  XContentHelper.merge(mergedMappings, mapToMerge, INSTANCE)

 인자가 셋인 오버로드다. 그 판은 parent 에 null 을 넣는다 (XContentHelper L430)

 주석이 이유를 적어 두었다 (L522-524)
   "Since "key" is an arbitrary field name, for which we only need plain mapping
    subtrees merge, no need to pass it to the recursion as it shouldn't affect the
    merge logic. Specifically, passing a parent may cause merge failures of fields
    named "properties"."

 즉 "properties" 라는 이름의 필드가 있으면
 parent 가 "properties" 가 되어 필드 이름인 척하게 된다
 이슈 번호까지 적혀 있다 - 108866
```

```text
 남기는 둘이 왜 그 둘인가

 L513 주석  "we must keep the "properties" node, otherwise our merge has no point"
 L517 주석  "the "subobjects" setting affects an entire subtree and not only
             locally where it is configured"

 properties 는 재귀할 대상이라서
 subobjects 는 효력 범위가 자기 자리를 넘어서라서다

 나머지는 전부 새 것이 덮는다
 L512 가 빈 HashMap 으로 시작하는 것이 그 뜻이다
```

```text
 _routing.required 검사가 사는 자리

 이 검사는 원시 병합 중에만 돈다
 그리고 원시 병합은 소스가 여럿일 때만 일어난다 ([01] L460)

 그래서 단일 소스 merge(L572)로 들어온 요청은 이 검사를 안 탄다
 주석이 composable index template 을 언급하는 이유가 이것이다

 비교가 == 가 아니라 != 다 (L540)
   if ("_routing".equals(parent) && oldValue != newValue)
 값 비교가 아니라 참조 비교다
```

## 결과가 쓰이는 곳

```text
 돌려준 Map
      --> XContentHelper 가 base 맵의 그 키에 넣는다 (L467, L517)
      --> 루프가 끝나면 [01] L466 이 doMerge 로 넘긴다

 돌려준 null
      --> 기본 재귀로 넘어간다. parent 가 한 단계 내려간다

 던진 MapperParsingException
      --> 파싱 전에 터진다. 매퍼를 만들지도 않는다
```

## 다루지 않는 것

`XContentHelper.merge` 의 리스트 병합 규칙(키 기준 병합과 단순 결합), `shouldMergeFieldMappings` 가 타입을 판정하는 기준(`MERGEABLE_OBJECT_TYPES`), `CompressedXContent` 와 JSON 변환, `subobjects` 설정이 실제로 매퍼 트리에 미치는 영향은 같은 뼈대의 곁가지라 요약만 했다.

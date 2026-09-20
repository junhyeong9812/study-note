# spi

상위: [매핑 병합](../README.md)

이 흐름의 계약은 `MergeReason` 하나다. 같은 코드가 이 값에 따라 한도를 무제한으로 풀거나, 초과분을 조용히 버리거나, 예외를 던진다. 인용은 주석 원문이고, 그 아래 설명은 원문이 이유를 말하지 않을 때 내가 붙인 것이다.

기준 커밋: elasticsearch `main` [`60bb239edb`](https://github.com/elastic/elasticsearch/tree/60bb239edb99f0e002eb620e4e82a6f2b15a49b0) (2026-09-19).

## 다섯 값

`server` / `org.elasticsearch.index.mapper` / `MapperService.java` L63-L100 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/mapper/MapperService.java#L63-L100))

```java
// MapperService.java L63-L100
    public enum MergeReason {
        /**
         * Pre-flight check before sending a dynamic mapping update to the master
         */
        MAPPING_AUTO_UPDATE_PREFLIGHT {
            @Override
            public boolean isAutoUpdate() {
                return true;
            }
        },
        /**
         * Dynamic mapping updates
         */
        MAPPING_AUTO_UPDATE {
            @Override
            public boolean isAutoUpdate() {
                return true;
            }
        },
        /**
         * Create or update a mapping.
         */
        MAPPING_UPDATE,
        /**
         * Merge mappings from a composable index template.
         */
        INDEX_TEMPLATE,
        /**
         * Recovery of an existing mapping, for instance because of a restart,
         * if a shard was moved to a different node or for administrative
         * purposes.
         */
        MAPPING_RECOVERY;

        public boolean isAutoUpdate() {
            return false;
        }
    }
```

각 값의 javadoc 이 정체를 말한다.

```text
 MAPPING_AUTO_UPDATE_PREFLIGHT  L65
   "Pre-flight check before sending a dynamic mapping update to the master"

 MAPPING_AUTO_UPDATE            L74
   "Dynamic mapping updates"

 MAPPING_UPDATE                 L83
   "Create or update a mapping."

 INDEX_TEMPLATE                 L87
   "Merge mappings from a composable index template."

 MAPPING_RECOVERY               L91-94
   "Recovery of an existing mapping, for instance because of a restart,
    if a shard was moved to a different node or for administrative purposes."
```

`isAutoUpdate()` 를 참으로 덮어쓰는 것은 앞의 **둘뿐**이다(L67-72, L76-81). 나머지 셋은 기본 구현 L97-99 의 `false` 를 그대로 쓴다.

## 이유별 동작표

```text
 예산 모드 = getBudget(L704) 이 고르는 NewFieldsBudget
 nested 한도 = mergeBuilders L644
 checkLimits = newDocumentMapper L676 의 둘째 인자

 IDBL = index.mapping.total_fields.ignore_dynamic_beyond_limit
```

| MergeReason | 예산 모드 | nested 한도 | checkLimits | doMerge 진입 |
|---|---|---|---|---|
| `MAPPING_AUTO_UPDATE_PREFLIGHT` | IDBL 이면 `dropping`, 아니면 `throwing` | 설정값 | 해당 없음 | **불가** |
| `MAPPING_AUTO_UPDATE` | IDBL 이면 `dropping`, 아니면 `throwing` | 설정값 | `true` | 가능 |
| `MAPPING_UPDATE` | 언제나 `throwing` | 설정값 | `true` | 가능 |
| `INDEX_TEMPLATE` | 언제나 `throwing` | 설정값 | `true` | 가능 |
| `MAPPING_RECOVERY` | `unlimited` | `Long.MAX_VALUE` | `false` | 가능 |

```text
 PREFLIGHT 가 doMerge 에 못 들어오는 이유

 assert 가 둘 있다 (L427, L605)
 그런데 assert 는 -ea 없이는 아무것도 안 한다
 실제 보장은 그 값을 doMerge 쪽으로 넘기는 호출처가 없다는 것이다

 PREFLIGHT 를 쓰는 프로덕션 코드는 isNoOpUpdate(L586) 하나뿐이고
 그것은 doMerge 를 우회해 static mergeBuilders 를 직접 부른다 (L596)

 그래서 "예산 모드" 칸은 PREFLIGHT 에도 적용되지만
 "checkLimits" 칸은 적용되지 않는다 - newDocumentMapper 까지 안 가기 때문이다
```

## 이유가 갈라지는 자리들

```text
 MAPPING_RECOVERY 가 특별한 곳 (MapperService 안에서)

 L296  ParseFieldLimits.parseFieldLimits 에서 파싱 시점 한도를 전부 끈다
 L300  documentParser 를 RECOVERY 컨텍스트로 고정 생성
 L326  parserContext() 도 RECOVERY 고정
 L411  updateMapping 이 빌드 reason 을 RECOVERY 로 하드코딩
 L412  updateMapping 이 검증 reason 도 RECOVERY 로
 L644  nested 한도를 Long.MAX_VALUE 로
 L676  checkLimits 를 false 로
 L705  예산을 unlimited 로
```

```text
 INDEX_TEMPLATE 이 특별한 곳

 MappingBuilder L89-90    메타데이터 필드 빌더를 무조건 덮어쓴다
 MappingBuilder L102-108  _meta 를 깊은 병합한다 (다른 이유는 통째 교체)
 MappingParser  L178-183  _source.mode 가 있으면 deprecation 경고
```

`_meta` 쪽은 주석이 직접 말한다.

```text
 MappingBuilder L99-100
   "Merge _meta: for INDEX_TEMPLATE, deep-merge incoming over existing.
    For other reasons, incoming replaces existing entirely."
```

## 예산 결정이 두 층이다

같은 3갈래 판단이 **파싱 시점과 병합 시점에 각각 한 번씩** 있다. 모양은 같은데 내용이 다르다.

| | 파싱 시점 `ParseFieldLimits.parseFieldLimits` L41-52 | 병합 시점 `getBudget` L704-722 |
|---|---|---|
| `MAPPING_RECOVERY` | `UNLIMITED` (한도 전체를 끈다) | `unlimited()` |
| auto-update + IDBL | 예산은 `unlimited`, 이름·nested 한도만 건다 | `dropping(remaining)` |
| 그 외 | `throwing(totalLimit, totalLimit)` | `throwing(remaining, totalLimit)` |

셋째 줄이 핵심이다 — 파싱 시점은 **전체 한도**를 쓰고 병합 시점은 **남은 용량**을 쓴다.

```text
 ParseFieldLimits javadoc L36-39 이 이유를 적어 두었다

   "Recovery re-uses a mapping that was already validated, so no limits are
    enforced. Auto-updates in drop-mode use per-field name/nested limits but
    leave total-fields counting to the merge-time budget. All other updates
    additionally enforce a parse-time total-fields throwing budget."

 즉 파싱 시점은 들어온 매핑 하나만 보므로 전체 한도가 맞고
 병합 시점은 기존 것과 합친 뒤를 보므로 남은 용량이 맞다
 (뒤 문장은 주석에 없다. 두 수식을 비교하고 내가 붙인 것이다)
```

## 한도를 거는 주체가 셋이다

```text
 총 필드 수     NewFieldsBudget     예산이 본다
 nested 개수    ParseFieldLimits    checkNestedFieldCount L85-90
 필드명 길이    ParseFieldLimits    checkFieldNameLength L77-83

 그런데 병합 시점에 만드는 한도는 앞의 둘만 건다

   forMerge(nested, existingCount, budget)  L65-67
       fieldNameLengthLimit = Long.MAX_VALUE     이름 길이를 끈다
   withBudget(budget)                       L73-75
       이름도 nested 도 둘 다 끈다

 즉 필드명 길이 검사는 파싱 단계 전담이다

 그리고 checkLimits(MappingLookup L417-420)가 보는 것은 또 다르다
   checkNestedParentsLimit
   checkDimensionFieldLimit
 총 필드 수는 여기 없다
```

## 결과가 쓰이는 곳

```text
 MergeReason
      --> 파서 컨텍스트로 들어간다 (L296 의 supplier)
      --> 예산 모드를 고른다 (L704)
      --> nested 한도를 고른다 (L644)
      --> checkLimits 를 고른다 (L676)
      --> 빌더 병합의 메타데이터·_meta 규칙을 고른다 (MappingBuilder L89, L102)

 예산이 소진됐을 때
      --> dropping 이면 필드가 조용히 사라진다. 요청은 성공한다
      --> throwing 이면 IllegalArgumentException
      --> unlimited 면 아무 일도 없다
```

## 다루지 않는 것

`RootObjectMapper.Builder.merge` 가 예산을 실제로 소비하는 지점, `MapperMergeContext` 가 자식 컨텍스트로 예산을 나르는 방식, `IndexSettings` 의 한도 설정들(`index.mapping.total_fields.limit` 등)의 기본값과 갱신 경로, `MappingLookup` 의 `totalFieldsCount` 계산, `SemanticFieldMapper` 가 `MAPPING_RECOVERY` 를 쓰는 사정은 같은 뼈대의 곁가지라 요약만 했다.

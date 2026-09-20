# MapperService.doMerge

상위: [매핑 병합](../README.md)

세 오버로드가 모두 여기로 모인다. **파싱은 락 밖에서, 병합과 대입은 락 안에서** 한다. 이 흐름에서 잠금이 나오는 곳은 여기와 [updateMapping](../07_MapperService.updateMapping/README.md) 둘뿐이다.

## 위치

`server` / `org.elasticsearch.index.mapper` / `MapperService.java` L604-L621 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/mapper/MapperService.java#L604-L621))

## 실제 코드

파싱은 락 밖이다.

```java
// MapperService.java L606-L611
        MappingBuilder incomingBuilder;
        try {
            incomingBuilder = mappingParser.parseToBuilder(type, reason, mappingSourceAsMap);
        } catch (Exception e) {
            throw new MapperParsingException("Failed to parse mapping: {}", e, e.getMessage());
        }
```

병합과 대입은 락 안이다.

`server` / `org.elasticsearch.index.mapper` / `MapperService.java` L612-L620 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/mapper/MapperService.java#L612-L620))

```java
// MapperService.java L614-L620
        synchronized (this) {
            Mapping mapping = mergeBuilders(incomingBuilder, reason);
            DocumentMapper newMapper = newDocumentMapper(mapping, reason, mapping.toCompressedXContent());
            this.mapper = newMapper;
            assert assertSerialization(newMapper, reason);
            return newMapper;
        }
```

주석이 락의 목적을 말한다.

> synchronized concurrent mapper updates are guaranteed to set merged mappers derived from the mapper value previously read
>
> TODO: can we even have concurrent updates here?

## 동작 흐름

```text
 L605  assert reason != MAPPING_AUTO_UPDATE_PREFLIGHT
 L607  try
 L608    incomingBuilder = mappingParser.parseToBuilder(type, reason, map)
 L609  catch (Exception)
 L610    throw new MapperParsingException("Failed to parse mapping: {}", ...)
 L614  synchronized (this)
 L615    mapping = mergeBuilders(incomingBuilder, reason)
 L616    newMapper = newDocumentMapper(mapping, reason, mapping.toCompressedXContent())
 L617    this.mapper = newMapper
 L618    assert assertSerialization(newMapper, reason)
 L619    return newMapper
```

```text
 락 안에 들어가는 것이 정확히 무엇인가

 밖   파싱 (L608)             들어온 소스만 본다. 기존 매퍼와 무관하다
 안   기존 매퍼 읽기 (L624)    mergeBuilders 인스턴스 판이 this.mapper 를 읽는다
 안   병합 (L627 이하)
 안   검증 (L676)
 안   대입 (L617)

 주석이 말하는 "the mapper value previously read" 가 L624 의 읽기다
 읽기와 대입이 같은 락 안이라야
 두 스레드가 각자 낡은 값에서 출발해 서로를 덮어쓰는 일이 없다
```

```text
 그런데 락 밖에도 읽기가 있다

 L439  final DocumentMapper currentMapper = this.mapper;   merge 리스트 판
 L573  final DocumentMapper currentMapper = this.mapper;   merge 단일 판

 둘 다 "같으면 그대로 돌려준다" 판정에만 쓴다
 여기서 낡은 값을 봐도 손해가 없다 - 한 번 더 병합할 뿐이다

 (주석은 없다. 그 읽기가 쓰이는 두 자리를 보고 내가 판단한 것이다)
```

```text
 L615 와 L627 사이에 한 칸이 더 있다

 L615  mergeBuilders(incomingBuilder, reason)      인스턴스 2-arg
 L623-625 가 그 본문이다
   return mergeBuilders(mappingParser, indexSettings, incomingBuilder, reason, this.mapper);
 L627  static 5-arg

 static 판을 따로 둔 이유는 isNoOpUpdate(L596)가
 this.mapper 대신 다른 매퍼를 넘겨 같은 계산을 돌리기 때문이다
 (주석은 없다. 두 호출처를 비교하고 내가 판단한 것이다)
```

```java
// MapperService.java L623-L625
    private Mapping mergeBuilders(MappingBuilder incomingBuilder, MergeReason reason) {
        return mergeBuilders(mappingParser, indexSettings, incomingBuilder, reason, this.mapper);
    }
```

```text
 L616 과 L617 의 순서에 뜻이 있다

 newDocumentMapper 안에서 validate 가 돈다 (L676)
 그것이 예외를 던지면 L617 의 대입에 도달하지 못한다

 즉 검증에 실패한 매퍼는 this.mapper 에 들어가지 않는다
 실패해도 기존 매핑이 그대로 남는다
```

```text
 L616 의 셋째 인자가 일을 한 번 더 한다

 mapping.toCompressedXContent()

 방금 만든 Mapping 을 다시 직렬화해서 압축한다
 매 병합마다 일어난다

 그 결과가 DocumentMapper 의 mappingSource 가 되고
 다음 병합의 early return 비교 대상이 된다 (L440, L574)
```

```text
 L618 의 assert 는 가볍지 않다

 assertSerialization(L736-750)이 하는 일
   L739  parseMapping(type, reason, mappingSource)   전체를 다시 파싱한다
   L740  다시 직렬화해서 바이트로 비교한다
   L741  다르면 AssertionError

 assert 문 안이라 -ea 일 때만 돈다

 L737 주석: "capture the source now, it may change due to concurrent parsing"

 왜 이런 검사가 있는지는 MappingParser 쪽 주석이 말한다 (L196-199)
   "we rely on consistent serialization order since we do byte-level checks on
    the mapping between what we receive from the master and what we have locally"
```

```text
 예외를 감싸는 자리가 경로마다 다르다

 L608 은 Map 을 받는 parseToBuilder 를 부른다 (MappingParser L129)
       그 판은 try/catch 가 없다. 그래서 L609-611 이 감싼다

 L647 은 CompressedXContent 를 받는 판을 부른다 (MappingParser L95)
       그 판은 자체 try/catch 를 가진다 (L99-101)

 메시지는 양쪽 다 "Failed to parse mapping: {}" 로 같다
```

## 결과가 쓰이는 곳

```text
 this.mapper
      --> volatile 이라 대입 즉시 다른 스레드가 본다
      --> 문서 파싱과 검색이 이것을 읽는다

 돌려준 DocumentMapper
      --> 마스터가 mappingSource() 를 클러스터 상태에 싣는다
      --> 그것이 데이터 노드로 가서 updateMapping 의 입력이 된다

 던진 MapperParsingException
      --> 락을 잡기 전이면 아무것도 안 바뀐 상태다
      --> 락 안이면 L617 전이므로 역시 안 바뀐다
```

## 다루지 않는 것

`MappingParser.parseToBuilder` 가 매핑 소스를 빌더로 바꾸는 과정(메타데이터 필드 파싱, `_meta` 분리, 남은 필드 검사), `Mapping.toCompressedXContent` 의 직렬화, `DocumentMapper` 가 `MappingLookup` 을 만드는 과정은 같은 뼈대의 곁가지라 요약만 했다. 예산과 빌더 병합은 [mergeBuilders](../04_MapperService.mergeBuilders/README.md)에 있다.

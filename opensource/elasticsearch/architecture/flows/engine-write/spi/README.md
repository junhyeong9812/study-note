# spi

상위: [엔진 쓰기](../README.md)

이 흐름의 **상태 공간을 정하는 두 가지**다. 전략 객체가 "무엇을 할지"를, origin 이 "누가 시켰는지"를 담는다. 둘의 조합이 이 흐름의 모든 갈래다.

## IndexingStrategy

`server` / `org.elasticsearch.index.engine` / `InternalEngine.java` L2159-L2165 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/engine/InternalEngine.java#L2159-L2165))

```java
// InternalEngine.java L2159-L2165
        final boolean currentNotFoundOrDeleted;
        final boolean useLuceneUpdateDocument;
        final long versionForIndexing;
        final boolean indexIntoLucene;
        final boolean addStaleOpToLucene;
        final int reservedDocs;
        final Optional<IndexResult> earlyResultOnPreflightError;
```

필드는 정확히 일곱이고 생성자는 private 하나다. 만드는 길은 팩터리 일곱 개뿐이다.

`server` / `org.elasticsearch.index.engine` / `InternalEngine.java` L2176-L2185 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/engine/InternalEngine.java#L2176-L2185))

```java
// InternalEngine.java L2176-L2185
            assert useLuceneUpdateDocument == false || indexIntoLucene
                : "use lucene update is set to true, but we're not indexing into lucene";
            assert (indexIntoLucene && earlyResultOnPreflightError != null) == false
                : Strings.format(
                    "can only index into lucene or have a preflight result but not both."
                        + " indexIntoLucene: %s, earlyResultOnPreflightError: %s",
                    indexIntoLucene,
                    earlyResultOnPreflightError
                );
            assert reservedDocs == 0 || indexIntoLucene || addStaleOpToLucene : reservedDocs;
```

```text
 생성자 불변식 셋이 조합을 제한한다

 L2176  useLuceneUpdateDocument 이면 반드시 indexIntoLucene 이다
 L2178  indexIntoLucene 과 preflight 실패를 동시에 가질 수 없다
 L2185  reservedDocs 가 있으면 Lucene 에 쓰는 전략이어야 한다

 두 번째가 중요하다
 preflight 실패를 들고 있으면 Lucene 에 안 간다는 뜻이고
 그래서 [01] L1302 가 그것부터 본다
```

```text
 팩터리 일곱과 필드 조합

                                          Lucene  update  stale  preflight
 optimizedAppendOnly        L2197           O       X       X       -
 processNormally            L2211           O    !cNFoD     X       -
 processAsStaleOp           L2227           X       X       O       -
 processButSkipLucene       L2223           X       X       X       -
 skipDueToVersionConflict   L2201           X       X       X      있음
 failAsTooManyDocs          L2231           X       X       X      있음
 optimisticConcurrency...   L2236           X       X       X      있음

 만들어지는 곳
   optimizedAppendOnly        L1955 프라이머리 / L2037 비프라이머리
   processNormally            L2006 프라이머리 / L2044 비프라이머리
   processAsStaleOp           L2042 비프라이머리만
   processButSkipLucene       L2033 비프라이머리만
   skipDueToVersionConflict   L1977, L1990, L1999 프라이머리 / CCR L87
   failAsTooManyDocs          L1953, L2004 프라이머리만
   optimisticConcurrency...   L1962 프라이머리만
```

```text
 표에서 바로 나오는 사실 넷

 1. updateDocument 을 쓰는 유일한 길은
      processNormally 에 cNFoD=false 로 들어가는 것이다 (L2214)

 2. 프라이머리에서는 stale 이 절대 안 나온다
      processAsStaleOp 를 만드는 곳이 L2042 하나뿐이다

 3. [01] L1337 의 "Lucene 건너뛰고 결과만" 에 도달하는 것은
      processButSkipLucene 하나뿐이다
      나머지 셋은 preflight 실패를 들고 있어 L1302 가 먼저 잡는다

 4. stale op 은 Lucene 에는 쓰이되 versionMap 에는 안 들어간다
      L1365 가 indexIntoLucene 을 보는데 processAsStaleOp 는 false 다
```

## Operation.Origin

`server` / `org.elasticsearch.index.engine` / `Engine.java` L1885-L1897 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/engine/Engine.java#L1885-L1897))

```java
// Engine.java L1885-L1897
            PRIMARY,
            REPLICA,
            PEER_RECOVERY,
            LOCAL_TRANSLOG_RECOVERY,
            LOCAL_RESET;

            public boolean isRecovery() {
                return this == PEER_RECOVERY || this == LOCAL_TRANSLOG_RECOVERY;
            }

            boolean isFromTranslog() {
                return this == LOCAL_TRANSLOG_RECOVERY || this == LOCAL_RESET;
            }
```

```text
 다섯인데 판정 집합이 셋이다

                            isRecovery  isFromTranslog  문서실패=치명적
 PRIMARY                        X            X               X
 REPLICA                        X            X               O
 PEER_RECOVERY                  O            X               O
 LOCAL_TRANSLOG_RECOVERY        O            O               X
 LOCAL_RESET                    X            O               O

 세 집합이 서로 다르다. 이름만 보고 묶으면 틀린다

 특히 LOCAL_TRANSLOG_RECOVERY 는
 isRecovery 이면서 치명적 목록에는 없다
 그래서 "복구면 엔진이 죽는다"는 거짓이다
```

```text
 각 판정이 쓰이는 곳

 isRecovery       L1263  복구 중에는 스로틀을 안 건다
 isFromTranslog   L1346  translog 에서 재생 중이면 다시 안 쓴다
 치명적 목록      L1391, L2080  문서 실패를 엔진 실패로 볼지

 마지막 것의 이름이 treatDocumentFailureAsTragicError 이고
 javadoc 이 의도를 적어 두었다 (L2110-2112)
   레플리카에서 실패하면 치명적으로 본다
   프라이머리에서는 샤드 대신 요청 하나만 실패시키는 쪽을 택한다
```

```text
 그래도 프라이머리가 안전한 것은 아니다

 no-op tombstone 쓰기 실패     L2726-2727  origin 무관
 translog 의 tragic 예외        Translog L660-666
 인덱스 부패                    maybeFailEngine L3333-3352

 앞의 것은 주석이 이유를 적어 두었다
   "이미 시퀀스 번호를 발급했으므로 이건 치명적이다"
 번호를 내주고 그 자리를 못 채우면 복제가 영영 막히기 때문이다
```

## 결과가 쓰이는 곳

```text
 전략 객체
      --> [01] 의 모든 분기가 이 필드들을 본다
      --> [05] 의 Lucene 쓰기 방식도 이것이 고른다
      --> preflight 실패를 담은 채로 결과가 되기도 한다

 origin
      --> 계획 경로를 가른다 ([02])
      --> 스로틀, translog 기록, 엔진 사망 판정에 각각 다르게 쓰인다
      --> 세 판정의 집합이 달라서 하나로 묶어 생각하면 안 된다
```

## 다루지 않는 것

`IndexResult` 와 `Engine.Result` 의 구조, 삭제 쪽 전략(`DeletionStrategy`)과 그 팩터리, origin 이 어디서 정해지는지(`IndexShard.prepareIndex` 와 복구 경로), CCR 이 `skipDueToVersionConflict` 를 쓰는 맥락, 배치 경로가 만드는 전략 조합은 같은 뼈대의 곁가지라 요약만 했다.

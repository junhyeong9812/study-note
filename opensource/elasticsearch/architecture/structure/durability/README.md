# 지속성

색인한 문서가 **언제부터 검색되고, 언제부터 안전한가**. 이 둘은 다른 시점이고, 그래서 [디스크 배치](../disk-layout/README.md)에 `index/` 와 `translog/` 두 디렉터리가 따로 있다.

기준 커밋: elasticsearch `main` [`60bb239edb`](https://github.com/elastic/elasticsearch/tree/60bb239edb99f0e002eb620e4e82a6f2b15a49b0) (2026-09-19). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 문서 하나가 지나는 단계

 1. 메모리 버퍼        Lucene IndexWriter 에 들어간다
                       아직 검색되지 않는다
                       단 _id 로 직접 GET 하면 이 전에도 읽힌다

 2. translog 버퍼      translog 연산이 힙 버퍼에 append 된다
                       (TranslogWriter L264-295)
                       아직 파일에 안 내려갔다. 여기서 죽으면 잃는다

 3. translog fsync     버퍼를 채널로 내려쓰고 fsync 한다
                       여기까지 와야 노드가 죽어도 복구할 수 있다
                       언제 하는지는 아래 durability 설정이 정한다

 4. refresh            버퍼가 세그먼트가 되어 검색 대상이 된다
                       기본 1초마다 (IndexSettings L326)
                       아직 디스크 커밋은 아니다
                       검색이 30초 이상 없으면 건너뛴다 (IndexShard L4654-4665)

 5. flush              Lucene commit 이 일어나고 translog 를 비운다
                       이제 세그먼트가 확정된다

 1 과 2 의 순서는 코드가 정한 것이다
 InternalEngine.index 는 Lucene 에 먼저 쓰고 (L1334-1335)
 성공했을 때만 translog 에 넣는다 (L1348-1349)
```

```text
 "검색된다"와 "안전하다"는 다른 축이다

 refresh  검색 가능해진다.   디스크 커밋은 아직이다
 flush    디스크에 확정된다. 검색 여부와는 무관하다

 그래서 색인 직후 바로 검색하면 안 나오는 일이 생긴다
 기본 refresh 간격이 1초이기 때문이다
```

```text
 안전해지는 시점은 설정이 정한다 (Translog.Durability L1856-1867)

 REQUEST  요청마다 translog 를 fsync 한다. 기본값이다
          (IndexSettings L118-124)
 ASYNC    시간 간격으로 fsync 한다

 REQUEST 면 색인 응답을 받은 시점에 이미 디스크에 있다
 ASYNC 면 응답을 받아도 아직 메모리에만 있을 수 있다
 대신 빠르다
```

```text
 왜 translog 가 따로 필요한가

 Lucene commit 은 비싸다. 매 문서마다 할 수 없다
 그렇다고 커밋 전에 노드가 죽으면 데이터를 잃는다

 그래서 커밋과 별개로 연산을 append 로 기록해 둔다
 노드가 죽으면 마지막 커밋 이후의 translog 를 다시 재생한다

 flush 가 끝나면 그 구간의 translog 는 더 필요 없어진다
```

## 실제 코드

지속성 설정 두 가지.

`server` / `org.elasticsearch.index.translog` / `Translog.java` L1856-L1867 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/translog/Translog.java#L1856-L1867))

```java
// Translog.java L1856-L1867
    public enum Durability {

        /**
         * Async durability - translogs are synced based on a time interval.
         */
        ASYNC,
        /**
         * Request durability - translogs are synced for each high level request (bulk, index, delete)
         */
        REQUEST

    }
```

기본값은 요청 단위 fsync 다.

`server` / `org.elasticsearch.index` / `IndexSettings.java` L118-L124 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/IndexSettings.java#L118-L124))

```java
// IndexSettings.java L118-L124
    public static final Setting<Translog.Durability> INDEX_TRANSLOG_DURABILITY_SETTING = Setting.enumSetting(
        Translog.Durability.class,
        "index.translog.durability",
        Translog.Durability.REQUEST,
        Property.Dynamic,
        Property.IndexScope
    );
```

refresh 기본 간격.

`server` / `org.elasticsearch.index` / `IndexSettings.java` L326-L326 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/IndexSettings.java#L326-L326))

```java
// IndexSettings.java L326-L326
    public static final TimeValue DEFAULT_REFRESH_INTERVAL = new TimeValue(1, TimeUnit.SECONDS);
```

## 어디에서 쓰이는가

```text
 [디스크 배치] index/ 와 translog/ 가 이 단계들에 대응한다
 [엔진 쓰기] InternalEngine 이 Lucene 과 translog 양쪽에 쓴다
 [쓰기 복제] 레플리카도 같은 단계를 밟는다
 [샤드 모델] 복구는 translog 재생으로 이루어진다
```

디스크 모양은 [디스크 배치](../disk-layout/README.md), 복제 순서는 [쓰기 복제](../write-replication/README.md)에 있다.

## 결과가 쓰이는 곳

```text
 refresh 간격
      --> 기본 1초. 늘리면 색인이 빨라지고 검색 지연이 커진다
      --> 대량 색인 때 -1 로 꺼 두는 방법이 흔히 쓰인다
      --> 1초 스케줄이 돌아도 search idle 이면 건너뛴다

 translog durability
      --> REQUEST 가 기본이라 응답 = 디스크 기록이 보장된다
      --> ASYNC 로 바꾸면 그 보장이 사라진다

 flush 시점
      --> 크기나 시간 조건으로 자동으로 일어난다
      --> 수동 _flush API 도 있지만 보통 쓸 일이 없다

 세 단계가 독립적이라는 점
      --> refresh 했다고 안전해지는 것이 아니다
      --> flush 했다고 검색되는 것도 아니다 (refresh 가 먼저여야 한다)
```

## 다루지 않는 것

Lucene 세그먼트 머지와 그 정책, translog 세대(generation) 롤링 규칙과 보존 조건, `_refresh` / `_flush` API 의 파라미터, `index.translog.sync_interval` 과 `flush_threshold_size` 의 기본값, 스테이트리스 구성의 다른 refresh 기본값, 글로벌 체크포인트와 시퀀스 번호가 복구 범위를 정하는 방식, 검색 가능 스냅샷의 다른 지속성 모델은 같은 뼈대의 곁가지라 요약만 했다.

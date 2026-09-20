# 디스크 배치

`PUT /my-index/_doc/1` 이 끝난 뒤, 그 문서는 디스크의 **어느 경로에 어떤 파일로** 놓이는가. 경로 규약이 코드에 상수로 박혀 있어 한 줄씩 따라갈 수 있다.

기준 커밋: elasticsearch `main` [`60bb239edb`](https://github.com/elastic/elasticsearch/tree/60bb239edb99f0e002eb620e4e82a6f2b15a49b0) (2026-09-19). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 ${path.data}                        노드 하나가 쓰는 데이터 루트
 |
 +-- node.lock                       이 디렉터리를 한 노드가 점유한다는 표시
 |
 +-- _state/                         노드 메타데이터 + 클러스터 상태
 |                                   (PersistedClusterStateService 가 쓰는 Lucene 인덱스)
 |
 +-- indices/                        NodeEnvironment.INDICES_FOLDER
      |
      +-- {index.uuid}/              인덱스 이름이 아니라 UUID 다
           |
           +-- _state/               인덱스 메타데이터 (이름, 매핑, 설정)
           |
           +-- 0/                    샤드 번호
           |    +-- index/           Lucene 세그먼트  (ShardPath.INDEX_FOLDER_NAME)
           |    +-- translog/        트랜스로그       (ShardPath.TRANSLOG_FOLDER_NAME)
           |    +-- _state/          샤드 메타데이터 (프라이머리 여부, allocation id)
           |
           +-- 1/                    샤드 번호 1
           +-- 2/                    ...

 노드 루트 바로 아래에 오는 폴더는 셋이다
 _state, indices, 그리고 검색 가능 스냅샷 캐시 (NodeEnvironment L424-435)
```

`_state` 라는 이름은 세 층위에서 반복해서 쓰인다. 같은 상수(`MetadataStateFormat.STATE_DIR_NAME`) 하나가 노드·인덱스·샤드 세 곳에 쓰이기 때문이다. 층위마다 들어 있는 내용은 다르다.

```text
 경로를 만드는 코드가 곧 규약이다

 NodeEnvironment.DataPath
   L111  indicesPath = path.resolve("indices")
   L126  resolve(ShardId)  -> resolve(index).resolve(샤드번호)
   L134  resolve(Index)    -> resolve(index.getUUID())

 주석이 경로 모양을 직접 적어 두었다
   L101  ${data.paths}/indices
   L124  ${data.paths}/indices/{index.uuid}/{shard.id}
   L132  ${data.paths}/indices/{index.uuid}

 ShardPath
   L58-60  resolveTranslog() -> path/translog
   L62-64  resolveIndex()    -> path/index
```

```text
 왜 인덱스 이름이 아니라 UUID 인가

 경로에 들어가는 것은 index.getUUID() 다 (L135)

 UUID 는 인덱스를 만들 때 난수로 한 번 부여된다
   MetadataCreateIndexService L1509  put(SETTING_INDEX_UUID, randomBase64UUID())

 그래서 인덱스를 지웠다 같은 이름으로 다시 만들면
 이름은 같아도 UUID 가 달라 디렉터리가 갈린다

 이름은 재사용될 수 있지만 UUID 는 재사용되지 않는다
```

```text
 한 샤드 안에 세 종류의 디렉터리가 있다

 index/     Lucene 세그먼트. refresh 하면 검색에 보인다
 translog/  Lucene 커밋에 아직 들어가지 않은 연산 기록
 _state/    이 복제본이 프라이머리인지 등 (ShardStateMetadata)

 파일 이름 규약 (Translog L118-121, 조립은 L969-976)
   translog-{generation}.tlog   연산 로그
   translog-{generation}.ckp    그 로그의 체크포인트
   translog.ckp                 현재 체크포인트

 index/ 와 translog/ 가 함께 있어야 "쓰기가 안전하다"가 성립한다
 그 이유는 [지속성](../durability/README.md)에서 다룬다
```

## 실제 코드

노드 데이터 루트 아래에서 인덱스와 샤드 경로가 갈리는 곳이다.

`server` / `org.elasticsearch.env` / `NodeEnvironment.java` L122-L140 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/env/NodeEnvironment.java#L122-L140))

```java
// NodeEnvironment.java L122-L140
        /**
         * Resolves the given shards directory against this DataPath
         * ${data.paths}/indices/{index.uuid}/{shard.id}
         */
        public Path resolve(ShardId shardId) {
            return resolve(shardId.getIndex()).resolve(Integer.toString(shardId.id()));
        }

        /**
         * Resolves index directory against this DataPath
         * ${data.paths}/indices/{index.uuid}
         */
        public Path resolve(Index index) {
            return resolve(index.getUUID());
        }

        Path resolve(String uuid) {
            return indicesPath.resolve(uuid);
        }
```

샤드 하나 안의 두 디렉터리는 여기서 갈린다.

`server` / `org.elasticsearch.index.shard` / `ShardPath.java` L32-L33 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/shard/ShardPath.java#L32-L33))

```java
// ShardPath.java L32-L33
    public static final String INDEX_FOLDER_NAME = "index";
    public static final String TRANSLOG_FOLDER_NAME = "translog";
```

`server` / `org.elasticsearch.index.shard` / `ShardPath.java` L58-L64 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/shard/ShardPath.java#L58-L64))

```java
// ShardPath.java L58-L64
    public Path resolveTranslog() {
        return path.resolve(TRANSLOG_FOLDER_NAME);
    }

    public Path resolveIndex() {
        return path.resolve(INDEX_FOLDER_NAME);
    }
```

`_state` 라는 이름 하나가 세 층위에서 쓰인다.

`server` / `org.elasticsearch.gateway` / `MetadataStateFormat.java` L61-L62 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/gateway/MetadataStateFormat.java#L61-L62))

```java
// MetadataStateFormat.java L61-L62
    public static final String STATE_DIR_NAME = "_state";
    public static final String STATE_FILE_EXTENSION = ".st";
```

인덱스 메타데이터를 인덱스 디렉터리 아래에 남기는 곳이다. 이것이 있어 클러스터 상태를 잃어도 디스크만으로 인덱스를 되살릴 수 있다.

`server` / `org.elasticsearch.index` / `IndexService.java` L438-L448 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/IndexService.java#L438-L448))

```java
// IndexService.java L438-L448
    // method is synchronized so that IndexService can't be closed while we're writing out dangling indices information
    public synchronized void writeDanglingIndicesInfo() {
        if (closed.get()) {
            return;
        }
        try {
            IndexMetadata.FORMAT.writeAndCleanup(getMetadata(), nodeEnv.indexPaths(index()));
        } catch (WriteStateException e) {
            logger.warn(() -> format("failed to write dangling indices state for index %s", index()), e);
        }
    }
```

샤드 `_state/` 에 남는 내용이다.

`server` / `org.elasticsearch.index.shard` / `ShardStateMetadata.java` L27-L33 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/index/shard/ShardStateMetadata.java#L27-L33))

```java
// ShardStateMetadata.java L27-L33
    private static final String SHARD_STATE_FILE_PREFIX = "state-";
    private static final String PRIMARY_KEY = "primary";
    private static final String INDEX_UUID_KEY = "index_uuid";
    private static final String ALLOCATION_ID_KEY = "allocation_id";

    public final String indexUUID;
    public final boolean primary;
```

## 어디에서 쓰이는가

```text
 [샤드 모델] 샤드 번호가 그대로 디렉터리 이름이 된다
 [지속성] index/ 와 translog/ 가 왜 나뉘어 있는지
 [클러스터 상태] 노드 _state/ 에 저장되는 것이 곧 클러스터 상태다
 [노드 역할] data 역할이 없는 노드에는 indices/ 아래가 비어 있다
```

샤드가 무엇인지는 [샤드 모델](../shard-model/README.md), 두 디렉터리가 협력하는 방식은 [지속성](../durability/README.md), 노드 `_state/` 의 내용은 [클러스터 상태](../cluster-state/README.md)에 있다.

## 결과가 쓰이는 곳

```text
 node.lock
      --> 같은 데이터 디렉터리를 두 노드가 쓰는 것을 막는다
      --> Lucene 의 디렉터리 락으로 구현돼 있다 (NodeEnvironment L228-230)

 UUID 기반 경로
      --> 같은 이름의 인덱스를 지웠다 만들어도 데이터가 섞이지 않는다
      --> 디렉터리 이름만으로는 어느 인덱스인지 알 수 없지만
          그 아래 _state/ 를 읽으면 이름과 매핑이 나온다

 샤드 번호 디렉터리
      --> 한 노드가 같은 인덱스의 여러 샤드를 가질 수 있다
      --> 경로 이름에는 프라이머리 여부가 나타나지 않는다
          그 샤드의 _state/ 에는 기록되지만 (ShardStateMetadata L33)
          권위 있는 출처는 클러스터 상태의 라우팅 테이블이다

 index/ 와 translog/ 의 분리
      --> 질의는 Lucene 서처를 거친다
          단 실시간 GET 은 translog 를 직접 읽는다 (InternalEngine L1030-1032)
      --> 기존 디렉터리에서 복구할 때 translog 를 다시 재생한다
          (InternalEngine L642 recoverFromTranslog)
```

## 다루지 않는 것

`Store` 의 파일 무결성 검사와 `corrupted_` 마커, 여러 `path.data` 를 쓰는 다중 경로 배치, `index.data_path` 로 데이터와 상태를 다른 트리에 두는 커스텀 경로(deprecated), 검색 가능 스냅샷의 `snapshot_cache` 디렉터리, `_state/` 안의 `.st` 파일 포맷, Lucene 세그먼트 파일의 내부 구조(`.cfs`, `.fdt`, `.tim` 등)는 같은 뼈대의 곁가지라 요약만 했다. Lucene 자체의 색인 포맷도 범위 밖이다. 피어 복구와 스냅샷 복구는 로컬 복구와 경로가 달라 여기서 다루지 않는다.

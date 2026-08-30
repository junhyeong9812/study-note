# data-structure/24-lsm-tree — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — KeyValueStore (`src/main/java/com/datastructure/lsm/KeyValueStore.java`)

- `void put(K key, V value)` — 15번과 달리 옛 값을 반환하지 않는다
- `V get(K key)`
- `void delete(K key)`
- `boolean containsKey(K key)`
- `int size()`
- `boolean isEmpty()`
- `List<K> keys()`
- `void flush()`
- `void compact()`
- `int sstableCount()`
- `long diskReads()`
- `long sequentialBytesWritten()`
- `long storedEntryCount()`
- `double spaceAmplification()`

## 구현 — Tombstone (`src/main/java/com/datastructure/lsm/Tombstone.java`)

TODO 없음. 삭제 표식.

### `필드`

- `static final Tombstone MARKER` 역할(값 자리에 `null` 을 쓰지 않는 이유 — 삭제와 부재를 구별하지 못하면 무엇이 되살아나는가):

### `public static boolean is(Object value)` / `public String toString()`

- 하는 일:
- 논리(동일성(`==`)으로 판별하는 이유):
- 비용(왜):

## 구현 — MemTable (`src/main/java/com/datastructure/lsm/MemTable.java`)

### `필드`

- `TreeMap<K, Object> entries` 역할 — 값 자리에 `Object` 를 쓰는 이유:
- 실무가 여기에 12번 스킵 리스트를 쓰는 이유:

### `public void put(K key, Object value)`

- 하는 일:
- 논리(같은 키가 오면 덮어쓰는 것 — 삭제도 쓰기라는 것):
- 비용(왜):

### `public Object get(K key)`

- 하는 일:
- 논리(없음 / 값 / MARKER 셋을 구별하는 책임이 부르는 쪽에 있는 이유):
- 비용(왜):

### `public List<Map.Entry<K, Object>> entriesInOrder()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `public boolean containsKey(K key)` / `public int size()` / `public boolean isEmpty()` / `public void clear()`

- 하는 일:
- 비용(왜):

## 구현 — TinyBloomFilter (`src/main/java/com/datastructure/lsm/TinyBloomFilter.java`)

### `필드`

- `int bits` 역할:
- `int hashCount` 역할:
- `long[] words` 역할:

### `public TinyBloomFilter(int expectedInsertions, double falsePositiveRate)`

- 하는 일:
- 비용(왜):

### `static int optimalBits(int n, double p)` / `static int optimalHashCount(int m, int n)` / `static long mix64(long z)`

- 하는 일:
- 논리:
- 비용(왜):

### `int[] indexes(Object item)` (TODO)

- 하는 일:
- 논리(이중 해싱 · `h2 == 0` 방어가 테스트에 안 잡히는 것):
- 비용(왜):

### `public void add(Object item)` / `public boolean mightContain(Object item)`

- 하는 일:
- 논리(비대칭 — 아는 것은 "없다" 한쪽뿐):
- 비용(왜):

### `public int hashCount()` / `public long bitSize()`

- 하는 일:
- 비용(왜):

## 구현 — SSTable (`src/main/java/com/datastructure/lsm/SSTable.java`)

> 구조 테스트가 "제자리를 안 고친다"를 못 박는다 — 필드가 전부 `final`, 클래스도 `final`,
> `set`/`add`/`put` 으로 시작하는 메서드가 없다. **필드 이름 자체가 계약이다.**

### `필드`

- `static final int HEADER_BYTES = 8` 역할:
- `Object[] keys` 역할:
- `Object[] values` 역할:
- `long bytes` 역할:
- `TinyBloomFilter bloom` 역할:

### `public SSTable(List<Map.Entry<K, Object>> sortedEntries, boolean withBloom)` (TODO)

- 하는 일:
- 논리(목록을 두 배열로 굳히고, 바이트를 세고, 블룸을 채우는 것 · 정렬 전제 검사가 정상 경로에서는 도달 불가인데도 남기는 이유):
- 비용(왜):

### `int indexOf(K key)` (TODO)

- 하는 일:
- 논리(정렬된 배열이라 이진 탐색이 되는 것):
- 비용(왜):

### `private static int compare(Object a, Object b)` / `public static long entryBytes(Object key, Object value)` / `public static <K> Map.Entry<K, Object> cell(K key, Object value)`

- 하는 일:
- 비용(왜):

### `public Object rawValue(K key)` / `public boolean mightContain(K key)` / `public boolean hasBloom()`

- 하는 일:
- 논리(블룸을 먼저 묻는 순서가 읽기 증폭을 어떻게 줄이는가):
- 비용(왜):

### `public int size()` / `public long byteSize()` / `public K keyAt(int index)` / `public Object valueAt(int index)` / `public boolean isTombstoneAt(int index)`

- 하는 일:
- 비용(왜):

### `public List<Map.Entry<K, Object>> entries()` / `public int tombstoneCount()`

- 하는 일:
- 비용(왜):

## 구현 — Compactor (`src/main/java/com/datastructure/lsm/Compactor.java`)

### `public static <K, V> List<Map.Entry<K, Object>> mergeEntries(List<SSTable<K,V>> newestFirst, boolean dropTombstones)` (TODO)

- 하는 일:
- 논리(k-way 병합 · 같은 키면 **가장 최신** 것을 채택 · `dropTombstones` 가 맨 아래층까지 합칠 때만 true 여야 하는 이유):
- 비용(왜):

### `public static <K, V> SSTable<K,V> compact(List<SSTable<K,V>> newestFirst, boolean dropTombstones, boolean withBloom)`

- 하는 일:
- 논리:
- 비용(왜):

## 구현 — LsmTree (`src/main/java/com/datastructure/lsm/LsmTree.java`)

### `필드`

- `int memtableThreshold` 역할:
- `boolean bloomEnabled` 역할:
- `MemTable<K,V> memtable` 역할:
- `List<SSTable<K,V>> sstables` 역할 — **0번이 가장 최신**이라는 순서가 정확성을 만드는 이유:
- `long diskReads` / `long sequentialBytesWritten` / `long flushCount` / `long compactionCount` 역할(읽기·쓰기·공간 증폭을 재는 계수기):

### `public LsmTree(int memtableThreshold)` / `public LsmTree(int memtableThreshold, boolean bloomEnabled)`

- 하는 일:
- 비용(왜):

### `private void write(K key, Object value)` (TODO)

- 하는 일:
- 논리(디스크를 안 건드리는 것 · 꽉 차면 쏟는 것):
- 비용(왜):

### `public V get(K key)` (TODO)

- 하는 일:
- 논리(최신 층부터 차례로 뒤져 **처음 만난 것**을 답으로 삼는 것 · tombstone 을 만나면 무엇을 답하는가 · 층 순서를 뒤집으면 왜 예외 없이 옛 값이 나오는가):
- 비용(왜):

### `public void flush()` (TODO)

- 하는 일:
- 논리(memtable 을 SSTable 로 굳히는 것 · 순차 쓰기 바이트가 여기서 늘어나는 것):
- 비용(왜):

### `public void compactNewest(int count)` (TODO)

- 하는 일:
- 논리(앞에서 count 장만 합치는 **부분 compaction** 에서 tombstone 을 지우면 안 되는 이유):
- 비용(왜):

### `private List<Map.Entry<K, V>> mergedLive(K from, K to)` (TODO)

- 하는 일:
- 논리(층을 최신부터 훑어 같은 키는 처음 본 것만 채택):
- 비용(왜):

### `public void put(K key, V value)` / `public void delete(K key)`

- 하는 일:
- 논리(`put` 이 옛 값을 반환하지 않는 이유 — 읽지 않는 것이 이 구조의 전부):
- 비용(왜):

### `public void compact()`

- 하는 일:
- 논리(전체 compaction 이라 tombstone 을 버려도 되는 이유):
- 비용(왜):

### `public List<Map.Entry<K,V>> rangeScan(K from, K to)` / `public List<K> keys()`

- 하는 일:
- 비용(왜):

### `public boolean containsKey(K key)` / `public int size()` / `public boolean isEmpty()`

- 하는 일:
- 논리(`size()` 가 O(전체)인 이유 — 실제 LSM 저장소가 정확한 count API 를 잘 안 주는 이유):
- 비용(왜):

### `public int sstableCount()` / `public long diskReads()` / `public long sequentialBytesWritten()` / `public long storedEntryCount()` / `public double spaceAmplification()`

- 하는 일:
- 논리(증폭 셋을 각각 어떤 수로 재는가):
- 비용(왜):

### `public int memtableSize()` / `public long flushCount()` / `public long compactionCount()` / `public boolean bloomEnabled()` / `public SSTable<K,V> sstableAt(int index)` / `public void resetDiskReads()`

- 하는 일:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| 15번 B+트리 (제자리 갱신) | | | |
| LSM 트리 — 블룸 필터 없이 | | | |
| LSM 트리 — 블룸 필터 켜고 | | | |
| 전체 compaction (`compact()`) | | | |
| 부분 compaction (`compactNewest(k)`) | | | |

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

<!-- 원본 문서·코드 경로. 기준 소스는 문서가 아니라 코드/원전이다. -->

- README: `/home/jun/project/myway/data-structure/24-lsm-tree/README.md`
- 구현: `/home/jun/project/myway/data-structure/24-lsm-tree/src/main/java/com/datastructure/lsm/`
- 테스트: `/home/jun/project/myway/data-structure/24-lsm-tree/src/test/java/com/datastructure/lsm/`
- 정답 구현: `/home/jun/project/myway/data-structure/24-lsm-tree/impl/`

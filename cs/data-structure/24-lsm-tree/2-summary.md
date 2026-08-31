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

### 구조

```
값 자리에 들어갈 수 있는 것이 셋이고, 셋이 서로 다른 뜻이다

    값 자리     의미
    "2"        살아 있는 값
    MARKER     이 키는 지워졌다 (tombstone). 하나뿐인 인스턴스라 == 로 판별한다
    null       이 층에는 그 키가 아예 없다 (아래 층을 더 봐야 한다)

    delete(k)   ->   put(k, Tombstone.MARKER)
    지우는 것이 아니라 "지웠다는 표식을 새로 쓰는" 것이다. 그래서 삭제 비용 = 쓰기 비용
    지웠는데 저장량이 줄지 않고 오히려 는다. 그 대가는 compaction 이 나중에 치른다

null 을 표식으로 쓰면 안 되는 이유
    get 이 null 을 받았을 때 "지워졌다" 인지 "이 층에 없다" 인지 구별할 수 없다
        MemTable { b -> null }  ==  b 를 지웠다?  b 를 넣은 적 없다?
    구별을 못 하면 위층에서 멈추지 못하고 아래로 내려가서, 아래 SSTable 의 옛 값이 되살아난다
```

### `필드`

- `static final Tombstone MARKER` 역할(값 자리에 `null` 을 쓰지 않는 이유 — 삭제와 부재를 구별하지 못하면 무엇이 되살아나는가):

### `public static boolean is(Object value)` / `public String toString()`

- 하는 일:
- 논리(동일성(`==`)으로 판별하는 이유):
- 비용(왜):

## 구현 — MemTable (`src/main/java/com/datastructure/lsm/MemTable.java`)

### 구조

```
MemTable = TreeMap<K, Object> 한 개. 메모리에 있는 "쓰기를 받는 층"

    put 순서 :  c=3,  a=1,  b=2,  a=9,  delete(b)
                                   |      |
                              같은 키 갱신  값 자리에 MARKER 를 쓴다

    TreeMap 안 (항상 키 정렬 상태)
        +-------+-------+-------+
        | a=9   | b=MARK| c=3   |      a=1 은 덮어써져 사라졌다
        +-------+-------+-------+      메모리 안에서는 갱신이 그냥 갱신이다
             ^  키 오름차순으로 유지됨 (넣은 순서와 무관)

    값 타입이 V 가 아니라 Object 인 이유 : 같은 자리에 V 와 Tombstone.MARKER 가 함께 산다

    entriesInOrder()  ->  [ a=9, b=MARK, c=3 ]     정렬된 리스트
                |
                v  flush
        SSTable 생성자는 "정렬된 입력만" 받는다 (어긋나면 예외를 던진다)

정렬 상태로 들고 있는 것이 이 층의 전부다
    쓰기는 임의 순서로 들어오는데, 파일은 정렬되어 있어야 이진 탐색과 머지가 가능하다
    그 정렬을 디스크가 아니라 메모리에서 해치우려고 TreeMap 을 쓴다
    -> flush 는 정렬할 것이 없다. 앞에서부터 그대로 흘려 쓰기만 하면 된다 (순차 쓰기)
```

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

### 구조

```
SSTable 한 장 = flush 한 순간의 MemTable 을 얼려 놓은 것. 만들어진 뒤에는 절대 고치지 않는다

    index       0        1        2        3
    keys    [   a   ][   c   ][   f   ][   k   ]      오름차순 (생성자가 검사한다)
    values  [  "1"  ][ MARKER][  "6"  ][  "9"  ]      MARKER 도 값 자리에 그대로 산다
                         ^ tombstone 도 "엔트리" 로 자리를 차지한다

    bloom   : TinyBloomFilter (withBloom 일 때만 만든다). 이 장의 모든 키를 넣어 둔다
    bytes   : 엔트리마다 HEADER_BYTES(8) + 키 길이 + 값 길이 의 합
              tombstone 은 값 길이를 0 으로 친다 (표식이라 값 본문이 없다)

indexOf(key) : 정렬되어 있으니 이진 탐색
    찾는 키 f
    lo=0                  hi=3
    [ a ][ c ][ f ][ k ]        mid=1 : c < f  ->  lo = 2
              lo   hi
    [ a ][ c ][ f ][ k ]        mid=2 : f == f ->  index 2 반환
    없으면 -1.  O(log n)

mightContain(key) : 블룸 필터에게 먼저 물어본다
    false -> 이 장에 확실히 없다. 이진 탐색조차 하지 않는다 (파일을 안 읽는다)
    true  -> 있을 수도 있다. 이진 탐색을 해 보면 결국 null 일 수도 있다 (오탐)
    bloom 이 없으면(withBloom = false) 항상 true 를 돌려준다 = 필터가 없는 것과 같다

불변이라는 성질이 값싸게 만들어 주는 것들
    배열 두 개로 충분하다 (빈 자리, 이동, 재배치가 없다)
    한 번 쓰고 안 고치니 순차 쓰기 한 번으로 끝난다
    여러 장을 동시에 읽어도 서로 간섭하지 않는다 -> compaction 이 그냥 훑기가 된다
```

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

### 동작 — 병합

```
mergeEntries(newestFirst, dropTombstones) : 정렬된 장 여러 개를 동시에 훑는 k-way 머지
장마다 커서 하나. 커서가 가리키는 키들 중 가장 작은 키를 골라 하나씩 뽑아 낸다

입력 (newestFirst - 앞이 최신)                    dropTombstones = true 인 경우
    SST0 (최신)   b=MARKER
    SST1          a=9      c=3
    SST2 (가장 옛) a=1      b=2

step 1   커서    v         v         v
         SST0 [ b=MARK ]                   가리키는 키 : b,  a,  a
         SST1 [ a=9  ][ c=3 ]              가장 작은 키 = a
         SST2 [ a=1  ][ b=2 ]              같은 키가 여러 장에 있으면 index 가 가장 작은 장
                                           (= 가장 최신)의 값을 채택 -> a=9
         a 를 가리키던 커서(SST1, SST2)를 모두 한 칸 민다   <- 옛 a=1 은 읽히지도 않고 버려진다
         출력 : a=9

step 2   커서    v                  v
         SST0 [ b=MARK ]                   가리키는 키 : b,  c,  b
         SST1 [ a=9  ][ c=3 ]              가장 작은 키 = b,  최신 값 = MARKER
         SST2 [ a=1  ][ b=2 ]              b 를 가리키던 커서(SST0, SST2)를 민다
         dropTombstones 이므로 출력하지 않는다  <- tombstone 과 옛 b=2 가 함께 증발한다

step 3   남은 것은 SST1 의 c=3 뿐            출력 : c=3

출력 [ a=9, c=3 ] 은 뽑아 낸 순서가 곧 키 오름차순이라 그대로 새 SSTable 생성자에 넣는다

모든 입력을 앞에서 뒤로 한 번씩만 훑는다 (되돌아가지 않는다)
    -> O(전체 엔트리 수), 임의 읽기 0, 쓰기도 새 파일 하나에 순차로 한 번
    LSM 이 정렬을 고집하는 이유가 여기다. 정렬되어 있으면 병합이 "훑기" 로 끝난다
```

### `public static <K, V> List<Map.Entry<K, Object>> mergeEntries(List<SSTable<K,V>> newestFirst, boolean dropTombstones)` (TODO)

- 하는 일:
- 논리(k-way 병합 · 같은 키면 **가장 최신** 것을 채택 · `dropTombstones` 가 맨 아래층까지 합칠 때만 true 여야 하는 이유):
- 비용(왜):

### `public static <K, V> SSTable<K,V> compact(List<SSTable<K,V>> newestFirst, boolean dropTombstones, boolean withBloom)`

- 하는 일:
- 논리:
- 비용(왜):

## 구현 — LsmTree (`src/main/java/com/datastructure/lsm/LsmTree.java`)

### 구조

```
쓰기는 항상 맨 위 한 곳으로만 들어가고, 아래로는 통째로 흘러내리기만 한다

            put(k,v) / delete(k)
                   |
                   v
    +--------------------------------------+
    |  MemTable   (메모리, TreeMap)         |   삭제도 여기에 "쓰기" 로 들어온다
    |     a=9    b=MARKER    c=3           |   항상 키 정렬 상태
    +--------------------------------------+
                   |
                   |  size >= memtableThreshold  ->  flush()
                   |  정렬된 채로 통째로 순차 기록. MemTable 은 비운다
                   v
    +--------------------------------------+
    |  SSTable  (불변 파일 한 장)            |   태어난 뒤로는 절대 안 고친다
    +--------------------------------------+
                   |
                   |  flush 할 때마다 새 장이 "맨 앞" 에 쌓인다   sstables.add(0, frozen)
                   v
        index    0          1          2                 (index 0 = 가장 최신)
              +--------+ +--------+ +--------+
              | SST #3 | | SST #2 | | SST #1 |
              |  최신  | |        | | 가장 옛 |
              +--------+ +--------+ +--------+
              |<----- 같은 키가 여러 장에 남아 있을 수 있다 ----->|
              |<----- 장 수가 늘수록 읽기가 느려진다 ------------>|
                   |
                   |  compaction : 여러 장을 훑어 합치고 같은 키는 최신 것만 남긴다
                   v
              +----------------+
              | SST (합쳐진 것) |     합친 결과도 맨 앞(index 0)에 놓는다
              +----------------+

이 구조가 사는 이유
    디스크에서 비싼 것은 "제자리 고치기(임의 쓰기)" 다. LSM 은 그걸 아예 안 한다
    고치는 대신 새로 쓴다 -> 쓰기는 전부 순차 (sequentialBytesWritten 이 그것을 센다)
    대신 같은 키의 옛 판본들이 쌓인다 -> 읽기가 여러 장을 봐야 하고 공간도 부풀어 오른다
        spaceAmplification = 저장된 엔트리 수 / 살아 있는 키 수
    그 빚을 나중에 몰아서 갚는 것이 compaction 이다
```

### 동작 — 읽기

```
get(k) : 위에서 아래로, 최신에서 옛것으로. 처음 만난 값에서 멈춘다

    [1] MemTable.get(k)
            |
            +-- null 아님  ->  여기서 끝. MARKER 면 null 로 풀어서 돌려준다
            |
            +-- null (이 층에 없다)
                    v
    [2] for (SSTable t : sstables)        index 0 -> 끝,  즉 최신 -> 옛것 순서
            |
            +-- t.mightContain(k) == false  ->  이 장은 건너뛴다
            |       (블룸 필터. 디스크를 안 읽는다. diskReads 도 안 오른다)
            |
            +-- true  ->  diskReads++ ;  t.rawValue(k)   (이진 탐색)
                    |
                    +-- null 아님  ->  여기서 멈춘다. MARKER 면 null 로 풀어서 돌려준다
                    +-- null       ->  다음(더 옛) 장으로
    [3] 끝까지 못 찾으면 null

왜 반드시 최신부터인가
    같은 키의 새 값이 항상 더 앞(작은 index)에 있다. 뒤에 있는 것은 이미 죽은 옛 판본이다
    첫 히트에서 멈추는 규칙과 "앞이 최신" 이라는 순서가 맞물려야 옛 값이 안 되살아난다

    a 를 1 로 넣었다가 9 로 고친 뒤            get("a")
        MemTable  { }                        비었다 -> 아래로
        index 0   SST { a=9, c=3 }   최신     찾았다 -> 9 를 돌려주고 멈춘다
        index 1   SST { a=1, b=2 }           a=1 은 아직 파일에 남아 있지만 가려져 있다
                                             (지운 것이 아니라 덮인 것이다)

읽기 비용의 모양
    최악 = MemTable 1 + SSTable 장 수 x O(log 엔트리수).  장 수가 늘수록 나빠진다
    블룸 필터는 "이 장에 없다" 를 확실히 알려 주어 없는 키의 헛읽기를 잘라낸다
        false = 확실히 없다 (건너뛰어도 안전)
        true  = 있을 수도 있다 -> 읽어 보니 null 일 수 있다 (오탐. 정확성은 안 깨진다)
    장 수 자체를 줄이는 것은 compaction 의 몫이다
```

### 동작 — 삭제와 compaction

```
delete("b") 는 b 를 찾아가 지우는 것이 아니라, MemTable 에 MARKER 를 쓰는 것이다
flush 까지 하고 나면

    index 0   SST { b=MARKER }      <- 최신. get("b") 는 여기서 멈추고 null 을 준다
    index 1   SST { a=9, c=3  }
    index 2   SST { a=1, b=2  }     <- 옛 b=2 가 그대로 남아 있다

    tombstone 은 옛 값을 지운 것이 아니라 위에서 가리고 있는 것이다
    가리개를 함부로 치우면 아래 값이 그대로 되살아난다

compaction : 가리개와 그 아래 옛 값을 함께 없앤다

    before                                  after
    +-------------------+
    | SST { b=MARKER }  |  index 0
    +-------------------+
    | SST { a=9, c=3 }  |  index 1   ->     +-------------------+
    +-------------------+                   | SST { a=9, c=3 }  |
    | SST { a=1, b=2 }  |  index 2          +-------------------+
    +-------------------+
      b 의 tombstone 과 그 아래 b=2 가 같이 사라진다
      a=1 도 더 최신인 a=9 에 밀려 사라진다 -> 저장 엔트리 5개가 2개로 줄었다

    tombstone 을 버려도 되는 조건 : 합치는 대상이 "가장 아래까지" 를 포함할 때만 (bottommost)
        compactNewest(count) 는 count == sstables.size() 일 때만 dropTombstones = true
        아래에 안 합친 장이 남아 있는데 표식을 버리면, 그 아래 옛 값이 되살아난다
        그럴 때는 tombstone 을 결과에 그대로 들고 내려간다

        index 0,1 만 합치는 경우                  아래 층에 b 가 아직 있을지 모른다
        +-------------------+                    +-------------------+
        | SST { b=MARKER }  |                    | SST { b=MARKER,   |   <- 표식을 남긴다
        +-------------------+       ->           |       a=9, c=3 }  |
        | SST { a=9, c=3 }  |                    +-------------------+
        +-------------------+                    | SST { a=1, b=2 }  |   합치지 않은 채로
        | SST { a=1, b=2 }  |  (대상 밖)          +-------------------+
        +-------------------+

    compact() 는 flush() 를 먼저 하고 전부를 한 번에 합친다 -> 항상 bottommost
    합친 결과가 0 개면 (전부 tombstone 이었으면) 새 장을 만들지 않고 그냥 없앤다
```

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

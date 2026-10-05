# 웹 독립 교차 표본 — 자료구조·알고리즘 잔여 17편

- 일시: 2026-10-05
- 대상: ds 01·02·19·25·26·29, alg 01·02·03·09·11·12·33·34·39·40·41의 `2-summary.md`. 종합 4편(ds 43·44, alg 42·43)은 제외.
- 방법
  - 편마다 URL·1차 출처가 붙은 주장 2~8개를 골랐다. 소스 상수·기본값·RFC 수치·예외 문구·논문 인용 문장·날짜를 우선했다.
  - log.md 사실 점검 packet에 이미 있는 웹 표본은 피했다.
  - 출처는 curl(일반 UA)로 직접 받았다. HTML은 텍스트를 추출했고, PDF는 pdftotext로 읽었다. 소스는 raw.githubusercontent.com(OpenJDK = openjdk/jdk21u master)에서 받았다.
  - 받은 원문은 세션 scratchpad `dsa/web/`에만 두었다.
- 결과: 76건 — 일치 75 · 불일치 1 · 확인 불가 0
  - 1차 페이지 접근이 막힌 2건은 대체 1차 출처로 확인했다.
    - JDK 버그 트래커 → openjdk/jdk 커밋
    - IACR eprint → Google Security Blog 공지
- 비고
  - 표의 "원문 인용"은 받은 원문에서 그대로 옮겼다(공백만 정리).
  - 줄 번호는 2026-10-05 작업 트리 기준이다.

| # | 노트 (:줄) | 주장 | 출처 | 원문 인용 | 판정 |
|---|---|---|---|---|---|
| 1 | ds/01 :75 | ArrayList get/set/size 상수, add 분할상환 상수, 나머지 대략 선형 · LinkedList 인덱스 연산은 가까운 끝에서 순회 | jdk21u `ArrayList.java`·`LinkedList.java` 클래스 주석 | "The size, isEmpty, get, set, iterator, and listIterator operations run in constant time. The add operation runs in amortized constant time … All of the other operations run in linear time (roughly speaking)." / "Operations that index into the list will traverse the list from the beginning or the end, whichever is closer" | 일치 |
| 2 | ds/01 :222, :289 | ArrayDeque는 null 불가, 스택·큐로 Stack·LinkedList보다 빠를 가능성이 높다 | jdk21u `ArrayDeque.java` 47~49행 | "Null elements are prohibited. This class is likely to be faster than Stack when used as a stack, and faster than LinkedList when used as a queue." | 일치 |
| 3 | ds/02 :60 | ArrayDeque 대부분 분할상환 상수, remove(Object)·contains·iterator.remove()·대량 연산은 선형 | `ArrayDeque.java` 51~58행 | "Most ArrayDeque operations run in amortized constant time. Exceptions include remove … contains … iterator.remove(), and the bulk operations, all of which run in linear time." | 일치 |
| 4 | ds/02 :61~62 | HashMap 상수는 해시 분산 가정 · TreeMap은 containsKey/get/put/remove에 log(n) 보장 | `HashMap.java` 50~51행, `TreeMap.java` 40~41행 | "assuming the hash function disperses the elements properly among the buckets" / "guaranteed log(n) time cost for the containsKey, get, put and remove operations" | 일치 |
| 5 | ds/02 :64 | CopyOnWriteArrayList 변경 연산은 배열 새 복사 | `CopyOnWriteArrayList.java` 64~65행 | "operations (add, set, and so on) are implemented by making a fresh copy of the underlying array." | 일치 |
| 6 | ds/02 :99 | Collections.binarySearch: 비 RandomAccess·대형이면 "O(n) link traversals and O(log n) element comparisons" | `Collections.java` 193~195행 | "this method will do an iterator-based binary search that performs O(n) link traversals and O(log n) element comparisons." | 일치 |
| 7 | ds/02 :100 | shuffle은 비 RandomAccess·대형이면 배열로 옮겨 섞고 되돌린다(제곱 동작 회피) | `Collections.java` 420~424행 | "dumps the specified list into an array before shuffling it, and dumps the shuffled array back into the list. This avoids the quadratic behavior that would result from shuffling a "sequential access" list in place." | 일치 |
| 8 | ds/02 :264 | Stack Javadoc이 Deque를 권한다 | `Stack.java` 39~43행 | "A more complete and consistent set of LIFO stack operations is provided by the Deque interface and its implementations, which should be used in preference to this class." | 일치 (관찰 1) |
| 9 | ds/19 :42 | RocksDB `max_bytes_for_level_multiplier` 기본 10 · Cassandra LCS `fanout_size` 기본 10 | rocksdb main `include/rocksdb/advanced_options.h`, Cassandra 문서 LCS | "// Default: 10. … double max_bytes_for_level_multiplier = 10;" / "fanout_size The target size of levels increases by this fanout_size multiplier. … Default: 10" | 일치 |
| 10 | ds/19 :59 | 고전 레벨 방식은 읽기·쓰기 증폭을 대가로 공간 증폭 최소화 | RocksDB wiki Compaction | "Classic Leveled compaction, introduced by LSM-tree paper by O'Neil et al, minimizes space amplification at the cost of read and write amplification." | 일치 |
| 11 | ds/19 :109 | RocksDB 기본 Level = Tiered+Leveled, "레벨보다 WA 작고 티어보다 SA 작다" | RocksDB wiki Compaction | "Rocksdb implements Tiered+Leveled (termed Level Compaction in the code)" / "Tiered+Leveled has less write amplification than leveled and less space amplification than tiered." | 일치 |
| 12 | ds/19 :111 | UCS는 대부분 워크로드에 좋고 새 워크로드에 권장 · 기본은 STCS(폴백으로 유용) | Cassandra 문서 Compaction overview(latest) | "UCS is a good choice for most workloads and is recommended for new workloads." / "STCS is the default compaction strategy, because it is useful as a fallback when other strategies don't fit the workload." | 일치 |
| 13 | ds/19 :220 | dynamic level bytes → 약 90% 마지막 레벨, 9% 그 앞 | RocksDB wiki Leveled-Compaction.md 83행 | "We can guarantee 90% of data is stored in the last level, 9% data in the second last level." | 일치 |
| 14 | ds/19 :229 | LCS `sstable_size_in_mb` 160·`fanout_size` 10, 쓰기 위주에 좋은 선택 아님 | Cassandra 문서 LCS | "sstable_size_in_mb … Default: 160" / "It is not a good choice for write-heavy workloads, though, because it will cause a lot of disk IO and CPU usage." | 일치 |
| 15 | ds/25 :51 | ABQ는 `if (++putIndex == items.length) putIndex = 0;`로 되감는다 | jdk21u `ArrayBlockingQueue.java` 185행 | "if (++putIndex == items.length) putIndex = 0;" | 일치 |
| 16 | ds/25 :115 | Disruptor: 나머지 연산 비용을 줄이려 링 크기 2의 거듭제곱 + "size minus one" 마스크 | Disruptor 논문(lmax-exchange.github.io) | "This cost can be greatly reduced by making the ring size a power of 2. A bit mask of size minus one can be used to perform the remainder operation efficiently." | 일치 |
| 17 | ds/25 :209 | MS96이 Lamport 큐를 단일 enqueuer·단일 dequeuer로 제한한 wait-free 알고리즘으로 소개 | Michael & Scott PODC 1996 PDF | "Lamport [9] presents a wait-free algorithm that restricts concurrency to a single enqueuer and a single dequeuer." | 일치 |
| 18 | ds/25 :211 | Disruptor: 독립적이지만 동시에 쓰이는 변수는 같은 캐시 라인을 공유하지 않게 | Disruptor 논문 | "it is important to ensure that independent, but concurrently written, variables do not share the same cache-line if contention is to be minimised." | 일치 |
| 19 | ds/25 :287 | ForkJoinPool 주석: Chase–Lev 2005와 "roughly similar" | jdk21u `ForkJoinPool.java` 226~228행 | "The main work-stealing queue design is roughly similar to those in the papers "Dynamic Circular Work-Stealing Deque" by Chase and Lev, SPAA 2005" | 일치 |
| 20 | ds/26 :30, :344 | Linux 4.8 타이머 휠 재작성(cascading 등 해결) | kernelnewbies Linux_4.8 | "Rework of the timer wheel which addresses the shortcomings of the current wheel (cascading, slow search for next expiring timer, etc)." | 일치 |
| 21 | ds/26 :51 | PriorityQueue enqueue/dequeue O(log(n)), remove(Object)·contains(Object) 선형 | jdk21u `PriorityQueue.java` 72~76행 | "linear time for the remove(Object) and contains(Object) methods; and constant time for the retrieval methods" | 일치 |
| 22 | ds/26 :52 | DelayedWorkQueue `heapIndex`로 취소 제거 "down from O(n) to O(log n)" | jdk21u `ScheduledThreadPoolExecutor.java` 904~908행 | "every ScheduledFutureTask also records its index into the heap array. … greatly speeding up removal (down from O(n) to O(log n))" | 일치 |
| 23 | ds/26 :103 | Netty 기본 틱 100 ms·512칸, 칸 수는 다음 2의 거듭제곱(`createWheel`) | netty 4.1 `HashedWheelTimer.java` 169·185·335~336행 | "this(threadFactory, 100, TimeUnit.MILLISECONDS);" / "this(threadFactory, tickDuration, unit, 512);" / "ticksPerWheel = MathUtil.findNextPositivePowerOfTwo(ticksPerWheel);" | 일치 |
| 24 | ds/26 :171 | VL87 Scheme 7 예: 100일까지 100+24+60+60 = 244칸 | Varghese–Lauck SOSP 1987 PDF | "locations to store timers up to 100 days, we need only 100 + 24 + 60 + 60 = 244 locations." | 일치 |
| 25 | ds/26 :185 | Kafka 옛 purgatory: 끝난 요청을 즉시 지우지 않아 "may exhaust JVM heap and cause OutOfMemoryError" (2015) | Confluent 블로그(Matsuda, Oct 28, 2015) | "When the deletion does not keep up, the server may exhaust JVM heap and cause OutOfMemoryError." | 일치 |
| 26 | ds/26 :197, :202 | LVL_BITS 6·LVL_CLK_SHIFT 3·(HZ>100) LVL_DEPTH 9 · 마지막 레벨 초과는 강제 만료, 관측 최대 5일(연결 추적) | torvalds/linux master `kernel/time/timer.c` 92~97·153·167·172~174행 | "#define LVL_CLK_SHIFT 3" / "#define LVL_BITS 6" / "#if HZ > 100 # define LVL_DEPTH 9" / "the maximum value observed is 5 days (network connection tracking)" | 일치 |
| 27 | ds/26 :257 | java.util.Timer: 이진 힙, "thousands should present no problem" | jdk21u `Timer.java` 79~80행 | "(thousands should present no problem). Internally, it uses a binary heap to represent its task queue" | 일치 |
| 28 | ds/26 :282~283 | 틱마다 대기 큐→칸 최대 10만 개(`transferTimeoutsToBuckets`) · `INSTANCE_COUNT_LIMIT` 64 · "too many … instances" 오류 로그 | netty 4.1 `HashedWheelTimer.java` 92·483·535~538행 | "private static final int INSTANCE_COUNT_LIMIT = 64;" / "transfer only max. 100000 timeouts per tick" / "You are creating too many " + resourceType + " instances." | 일치 |
| 29 | ds/29 :65 | OSTEP 29.3: Michael–Scott 큐는 머리·꼬리 락 두 개 + dummy 노드 | OSTEP `threads-locks-usage.pdf` §29.3 | "you'll notice that there are two locks" / "One trick used by Michael and Scott is to add a dummy node" | 일치 |
| 30 | ds/29 :66 | LinkedBlockingQueue 주석 "A variant of the 'two lock queue' algorithm" | jdk21u `LinkedBlockingQueue.java` 86행 | "A variant of the "two lock queue" algorithm. The putLock gates" | 일치 |
| 31 | ds/29 :68 | OSTEP 29.2: hand-over-hand는 개념상 동시성이 높지만, 락 비용 때문에 큰 락보다 빠르게 만들기 어렵다 | OSTEP PDF §29.2 | "in practice, it is hard to make such a structure faster than the simple single lock approach, as the overheads of acquiring and releasing locks for each node of a list traversal is prohibitive." | 일치 |
| 32 | ds/29 :87 | CHM 옛 Segment는 직렬화 호환용 unused 클래스로만 남음 | jdk21u `ConcurrentHashMap.java` 484행 | "unused "Segment" class that is instantiated in minimal form" | 일치 |
| 33 | ds/29 :219 | AtomicStampedReference는 [참조, int] 쌍을 내부 객체로 만들어 교체(Implementation note) | jdk21u `AtomicStampedReference.java` 45~47행 | "Implementation note: This implementation maintains stamped references by creating internal objects representing "boxed" [reference, integer] pairs." | 일치 |
| 34 | ds/29 :255 | ArrayList fail-fast는 "cannot be guaranteed", CME는 "best-effort" | jdk21u `ArrayList.java` 87~90행 | "Note that the fail-fast behavior of an iterator cannot be guaranteed … throw ConcurrentModificationException on a best-effort basis." | 일치 |
| 35 | alg/01 :83 | 이미 정렬된 입력이면 CPython 정렬이 n−1번 비교로 끝남 | CPython 3.12 `Objects/listsort.txt` 3~6행 | "(less than lg(N!) comparisons needed, and as few as N-1)" | 일치 |
| 36 | alg/01 :225 | 고침: `lo + (hi - lo) / 2` 또는 `(lo + hi) >>> 1` | Bloch, Google Research 블로그 | "6: int mid = low + ((high - low) / 2);" / "6: int mid = (low + high) >>> 1;" | 일치 |
| 37 | alg/01 :252 | Bloch 글 날짜 2006-06-02 | 같은 블로그 | "June 2, 2006" | 일치 |
| 38 | alg/02 :50 | COS226 1.4 슬라이드: Θ = 분류, O = 상한, Ω = 하한 | Princeton COS226 Fall 2015 14AnalysisOfAlgorithms.pdf | "Big Theta … classify algorithms" / "Big O … develop upper bounds" / "Big Omega … develop lower bounds" | 일치 |
| 39 | alg/02 :53 | Sedgewick 1.4 물결 표기: 비가 1로 수렴 | algs4.cs.princeton.edu/14analysis | "We write g(N) ~ f(N) to indicate that g(N) / f(N) approaches 1 as N grows." | 일치 |
| 40 | alg/02 :286 | 28C3 발표 제목 "Efficient Denial of Service Attacks on Web Application Platforms" | media.ccc.de 28c3-4680 / SipHash 논문 참고문헌 [24] | (media.ccc.de 제목) "Effective Denial of Service attacks against web application platforms" | **불일치** |
| 41 | alg/03 :23 | PR #943: StackOverflowError는 jackson-databind 쪽에서 나고, core 변경이 이를 막는다 | jackson-core PR #943 | "StackoverflowError issue happens in jackson-databind but this change in jackson-core stops it from happening unless you increase the StreamReadConstraints" | 일치 |
| 42 | alg/03 :373 | 예외 문구: 2.15.0 "Depth (1001) exceeds the maximum allowed nesting depth (1000)", 2.16.0+ "Document nesting depth (…) exceeds the maximum allowed (…, from `StreamReadConstraints.getMaxNestingDepth()`)" | jackson-core 태그 2.15.0·2.16.0 `StreamReadConstraints.java` | 2.15.0: "Depth (%d) exceeds the maximum allowed nesting depth (%d)" / 2.16.0: "Document nesting depth (%d) exceeds the maximum allowed (%d, from %s)", `_constrainRef` = "`StreamReadConstraints."+method+"()`" | 일치 |
| 43 | alg/03 :417 | `maxNestingDepth` 기본 1000(2.15 브랜치) | PR #943 제목, 태그 2.15.0 소스 33행 | "Add StreamReadConstraints.maxNestingDepth() to constraint max nesting depth (default: 1000) [CVE-2025-52999]" / "public static final int DEFAULT_MAX_DEPTH = 1000;" | 일치 |
| 44 | alg/09 :48~50 | Comparator 계약: sgn 대칭 · 추이 · 0의 일관성 | jdk21u `Comparator.java` 122~134행 | "signum(compare(x, y)) == -signum(compare(y, x))" / "the relation is transitive" / "compare(x, y)==0 implies that signum(compare(x, z))==signum(compare(y, z)) for all z." | 일치 |
| 45 | alg/09 :108 | JDK-8072909(JDK 9): run 스택 40 → 49 · JDK-8203864(JDK 11)에서 mergeCollapse 수정 | openjdk/jdk 커밋 892b06056c(2015-02-12), 8203864 커밋(2018-06-25) | diff "- len < 119151 ? 24 : 40); + len < 119151 ? 24 : 49);" / "8203864: Execution error in Java's Timsort" | 일치 (관찰 2) |
| 46 | alg/09 :109 | CPython 3.11부터 powersort 병합 순서(bpo-34561) | docs.python.org 3.11 changelog, 3.11.0 alpha 1 절 | "bpo-34561: List sorting now uses the merge-ordering strategy from Munro and Wild's powersort()." | 일치 (관찰 3) |
| 47 | alg/09 :151 | useLegacyMergeSort 소스 주석 "향후 릴리스에서 제거 예정" | jdk21u `Arrays.java` 986·1045행 | "To be removed in a future release." | 일치 |
| 48 | alg/09 :194 | V8 v7.0부터 TimSort(안정), ES2019부터 명세가 안정성 요구 | v8.dev "Getting things sorted in V8"(2018-09-28), "Stable Array.prototype.sort"(2019-07-02, ES2019 태그) | "finally make it stable in V8 v7.0 / Chrome 70" / "Although stability is now required per spec … V8 uses Timsort" | 일치 |
| 49 | alg/11 :26 | PostgreSQL 17 `work_mem` 기본 4MB | PG 17 문서 19.4 | "The default value is four megabytes (4MB)." | 일치 |
| 50 | alg/11 :28 | Hadoop `mapreduce.task.io.sort.mb` 기본 100(MB) | `mapred-default.xml` | value 100 — "The total amount of buffer memory to use while sorting files, in megabytes." | 일치 |
| 51 | alg/11 :63~64 | 일반 외부 병합 정렬: 총 패스 1 + ⌈log_(B−1)⌈N/B⌉⌉, I/O 2N × 패스 · 2-way는 1 + ⌈log₂ N⌉ | CMU 15-445 Fall 2024 notes #11 | "The algorithm makes 1 + ⌈log2 N⌉ total passes … The total I/O cost is 2N × (# of passes)" / "the algorithm performs 1 + ⌈logB−1 ⌈N/B⌉⌉ passes" | 일치 |
| 52 | alg/12 :26 | Klink–Wälde: 500 KB POST로 PHP5 서버 CPU 1분 | SipHash 논문 7절 | "Wälde reported 500 KB of carefully chosen POST data occupying a PHP5 server for a full minute of CPU time." | 일치 |
| 53 | alg/12 :197 | CPython 3.4~ SipHash-2-4(PEP 456) | PEP 456 머리말 | "Python-Version: 3.4" / "siphash24 is the recommend variant" | 일치 |
| 54 | alg/12 :198 | CPython 3.11+ SipHash-1-3, bpo-29410 | What's New 3.11 | "siphash13 is added as a new internal hashing algorithm. … (Contributed by Inada Naoki in bpo-29410.)" | 일치 |
| 55 | alg/12 :199 | Rust HashMap 기본 SipHash 1-3, "currently", 바뀔 수 있음 | doc.rust-lang.org std HashMap | "The default hashing algorithm is currently SipHash 1-3, though this is subject to change at any point in the future." | 일치 |
| 56 | alg/12 :241 | SHA-1 첫 충돌 2017년 2월 공개(Stevens 외) | Google Security Blog 2017-02-23 (eprint 대체) | "Announcing the first SHA1 collision February 23, 2017 Posted by Marc Stevens (CWI Amsterdam), Elie Bursztein (Google) …" | 일치 (관찰 4) |
| 57 | alg/33 :61, :63 | 거리 32K·길이 258 제한(§2) · 길이 3..258, 거리 1..32,768(§3.2.5) | RFC 1951 | "limits distances to 32K bytes and lengths to 258 bytes" / "the length is drawn from (3..258) and the distance is drawn from (1..32,768)" | 일치 |
| 58 | alg/33 :97 | 게으른 매칭: 길이 N 일치 뒤 다음 바이트에서 더 긴 일치를 보면 앞 일치를 리터럴 1개로 줄임 | RFC 1951 §4 | "after a match of length N has been found, the compressor searches for a longer match starting at the next input byte. If it finds a longer match, it truncates the previous match to a length of one (thus producing a single literal byte)" | 일치 |
| 59 | alg/33 :145 | 부호 길이 0~15(§3.2.7) | RFC 1951 701행 | "0 - 15: Represent code lengths of 0 - 15" | 일치 |
| 60 | alg/33 :165 | zlib = 2바이트 헤더 + Adler-32 4바이트 꼬리 | RFC 1950 §2.2 | "\|CMF\|FLG\| … \|...compressed data...\| ADLER32 \|" | 일치 |
| 61 | alg/33 :409 | GZIPOutputStream `syncFlush` 기본 false | jdk21u `java/util/zip/GZIPOutputStream.java` 69~70행 | "public GZIPOutputStream(OutputStream out, int size) … { this(out, size, false); }" | 일치 |
| 62 | alg/34 :55~66, :69 | clevels.h(256KB 초과) 레벨 1·3·5·9·13·16·19·22의 W/C/S/전략 · S가 레벨 12의 6 → 13의 4 | zstd v1.5.5 `lib/compress/clevels.h` 29~50행 | "{ 19, 13, 14, 1, 7, 0, ZSTD_fast }, /* level 1 */" … "{ 22, 22, 23, 6, 5, 32, ZSTD_lazy2 }, /* level 12 */" "{ 22, 22, 22, 4, 5, 32, ZSTD_btlazy2 }, /* level 13 */" … "{ 27, 27, 25, 9, 3,999, ZSTD_btultra2}, /* level 22 */" | 일치 |
| 63 | alg/34 :74 | CLI 기본 3, 범위 1~19, `--ultra`로 22 | zstd v1.5.5 `programs/zstd.1.md` 108~110행 | "selects # compression level [1-19] (default: 3)" / "--ultra: unlocks high compression levels 20+ (maximum 22)" | 일치 |
| 64 | alg/34 :92 | LZ4 최소 매치 4, 마지막 5바이트 리터럴, 마지막 매치는 블록 끝 12바이트 전 시작 | lz4 dev `doc/lz4_Block_format.md` 91·116·122행 | "The minimum length of a match, called minmatch, is 4." / "The last 5 bytes of input are always literals." / "The last match must start at least 12 bytes before the end of block." | 일치 |
| 65 | alg/34 :94 | LZ4 프레임 매직 0x184D2204, 블록 최대 64KB·256KB·1MB·4MB | `lz4_Frame_format.md` 71·196행 | "Value : 0x184D2204" / "\| 64 KB \| 256 KB \| 1 MB \| 4 MB \|" | 일치 |
| 66 | alg/34 :95, :97 | LZ4_HC 모든 버전 같은 해제 속도 · lzbench: LZ4 1.9.0 2.101, 780MB/s, 4970MB/s, Core i7-9700K | lz4 dev README 15·31·41행 | "All versions feature the same decompression speed." / "Core i7-9700K CPU @ 4.9GHz" / "LZ4 default (v1.9.0) \| 2.101 \| 780 MB/s \| 4970 MB/s" | 일치 |
| 67 | alg/34 :107, :112, :116 | 블록 ≤ min(Window_Size, 128KB) · 첫 블록 repeat offset 초기값 1·4·8 · 매직 0xFD2FB528 | RFC 8878 §3.1.1.2.4·§3.1.1.5·§3.1.1 | "the smallest of: Window_Size, 128 KB" / "Repeated_Offset1 (1), Repeated_Offset2 (4), and Repeated_Offset3 (8), unless a dictionary is used" / "Value: 0xFD2FB528" | 일치 |
| 68 | alg/34 :165 | Brotli 윈도 2^WBITS − 16, WBITS 10~24 | RFC 7932 §9.1 | "WBITS, a value in the range 10..24" / "window size = (1 << WBITS) - 16" | 일치 |
| 69 | alg/34 :380 | zstd CLI 해제 메모리 기본 한도 128MiB | zstd v1.5.5 man `--memory` | "By default, zstd uses 128 MiB for decompression as the maximum amount of memory the decompressor is allowed to use" | 일치 |
| 70 | alg/39 :99, :332 | Sedgewick 2.3 "~2 N ln N compares … on the average" · "~N²/2 … random shuffling protects" | algs4.cs.princeton.edu/23quicksort | "Quicksort uses ~2 N ln N compares (and one-sixth that many exchanges) on the average" / "Quicksort uses ~N2/2 compares in the worst case, but random shuffling protects against this case." | 일치 |
| 71 | alg/39 :126 | McIlroy: 무작위화한 구현을 포함해 "very mild and realistic assumptions"를 만족하는 퀵정렬에 통한다 | McIlroy 1999 mdmspe.pdf 초록 | "The general method works against any implementation of quicksort–even a randomizing one–that satisfies certain very mild and realistic assumptions." | 일치 |
| 72 | alg/39 :164 | 홀수 합성수의 MR 거짓말쟁이 밑 ≤ 1/4 (Rabin–Monier 1980) | K. Conrad, "The Miller–Rabin Test" 정리 2.9·참고문헌 | "the proportion of integers from 2 to n − 2 that are Miller–Rabin nonwitnesses for n is less than 25%. Theorem 2.9, due independently to Monier [10] and Rabin [11]" — [10] TCS 12 (1980), [11] J. Number Theory 12 (1980) | 일치 |
| 73 | alg/40 :46 | P = NP는 Clay 밀레니엄 문제 | claymath.org/millennium-problems | 문제 목록: "Birch and Swinnerton-Dyer Conjecture Hodge Conjecture Navier-Stokes Equation P vs NP Poincaré Conjecture …" | 일치 |
| 74 | alg/40 :79, :290 | Cook 1971 STOC "The Complexity of Theorem-Proving Procedures" | Wikipedia Cook–Levin theorem 참고문헌 | "Cook, Stephen (1971). "The complexity of theorem proving procedures". Proceedings of the Third Annual ACM Symposium on Theory of Computing. pp. 151–158." | 일치 |
| 75 | alg/41 :220 | `missing return statement`·`unreachable statement`는 같은 계열의 보수적 흐름 분석(JLS 14.22) | JLS SE 21 §14.22, §8.4.7 | "It is a compile-time error if a statement cannot be executed because it is unreachable." / (§8.4.7) "a compile-time error occurs if the body of the method can complete normally (§14.1)" | 일치 (관찰 5) |
| 76 | alg/41 :274 | Rice, "Classes of Recursively Enumerable Sets and Their Decision Problems", Trans. AMS, 1953 | ams.org 논문 페이지 | "Classes of recursively enumerable sets and their decision problems H. G. Rice Trans. Amer. Math. Soc. 74 (1953), 358-366" | 일치 |

## 불일치 상세

### #40 — alg/02 :286 28C3 발표 제목
- 노트 문구: `- JEP 180 <https://openjdk.org/jeps/180> · 28C3 "Efficient Denial of Service Attacks on Web Application Platforms"(Klink·Wälde, 2011)`
- 원문
  - media.ccc.de `28c3-4680-en-effective_dos_attacks_against_web_application_platforms`의 `<title>`: "Effective Denial of Service attacks against web application platforms"
- 원인 추정
  - SipHash 논문(Aumasson–Bernstein 2012) 참고문헌 [24]가 "Alexander Klink, Julian Wälde, Efficient denial of service attacks on web application platforms (2011)"로 잘못 인용한다.
  - 이 2차 인용이 그대로 옮겨진 것으로 보인다. alg/12 :386은 제목을 적지 않아 해당 없다.
- 제안 문구: `28C3 "Effective Denial of Service attacks against web application platforms"(Klink·Wälde, 2011) <https://media.ccc.de/v/28c3-4680-en-effective_dos_attacks_against_web_application_platforms>`
- 참고: log에 기록된 "커리큘럼 28C3 제목 'Efficient'→실제 'Effective'"와 같은 오류다. 이 노트의 참고 줄은 아직 남아 있다.

## 확인 불가·관찰 상세

1. **#8 ds/02 :264** — Javadoc이 Deque를 권한다는 점은 일치한다.
   - 다만 "동기화 오버헤드가 있는 옛 클래스"는 Stack Javadoc에 없다.
   - 이는 Stack이 Vector(synchronized 메서드)를 상속한다는 데서 나온 해석이다.
   - 노트가 이것을 Javadoc의 말처럼 읽히게 두지 않으려면 "(해석)"을 붙이는 정도가 적당하다. 필수는 아니다.
2. **#45 alg/09 :108** — `bugs.openjdk.org/browse/JDK-8203864`·`JDK-8072909`는 HTML과 REST API(`/rest/api/2/issue/…`) 모두 "OpenJDK Error" 페이지를 돌려줘 열 수 없었다. 대신 openjdk/jdk GitHub 커밋으로 확인했다.
   - 8072909 = 커밋 892b06056c(2015-02-12)
     - TimSort.java diff에서 `40 → 49`
     - JDK 9 개발 기간
   - 8203864 = 2018-06-25 커밋 "8203864: Execution error in Java's Timsort"
     - JDK 11 rampdown(2018-06-28) 직전 mainline이다.
     - "JDK 11에서 해결"과 정합한다. 단, 이슈 페이지의 Fix Version 필드 자체는 보지 못했다.
   - jdk21u `mergeCollapse`(442행)의 `runLen[n-2] <= runLen[n] + runLen[n-1]` 검사도 확인했다.
3. **#46 alg/09 :109** — bugs.python.org/issue34561 페이지의 Versions 필드는 "Python 3.8"이다(이슈 등록 당시 값). PR 28108 병합은 2021-09-01이다.
   - 3.11 여부는 3.11 changelog의 "Python 3.11.0 alpha 1" 절에 이 항목이 있는 것으로 확인했다.
   - 노트의 "3.11부터"는 맞다. 이슈 페이지만 보면 3.8로 오독할 수 있다.
4. **#56 alg/12 :241** — 노트가 링크한 `eprint.iacr.org/2017/190.pdf`는 Cloudflare 확인 페이지("Just a moment...")를 돌려줘 PDF를 받지 못했다.
   - 공개 시점과 저자는 Google Security Blog 공지(2017-02-23, Marc Stevens 외)로 확인했다.
   - `shattered.io`는 현재 뉴스 사이트로 바뀌어 근거로 쓰지 않았다.
   - 논문 본문(CRYPTO 2017 게재 정보)은 열지 못했다.
5. **#75 alg/41 :220** — `unreachable statement`는 JLS 14.22 그대로다.
   - `missing return statement`의 오류 규칙 자체는 §8.4.7("body of the method can complete normally")에 있다.
   - 14.22는 그 "can complete normally"를 정의하는 절이다. 그래서 "같은 계열의 보수적 흐름 분석(JLS 14.22)"이라는 서술은 맞다.
   - 정밀하게 쓰려면 `(JLS 14.22, missing return은 8.4.7)`로 써도 된다.
6. 시점 의존 값(조회일 2026-10-05)
   - RocksDB `advanced_options.h`·wiki, Cassandra latest 문서(페이지 표기 5.0), lz4 dev README, timer.c master는 브랜치 HEAD 기준이다. 이후 바뀔 수 있다.

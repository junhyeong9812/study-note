# 웹 독립 교차 표본 — CS 수학 01~15

- 일시: 2026-10-07(노트 줄 번호는 08:27 KST에 다시 grep한 값 — 판정이 진행 중이라 이후 바뀔 수 있다)
- 방법: 15편의 `2-summary.md`마다 URL이나 1차 출처가 붙은 주장을 2~5개 골랐다(총 55개). 사실 점검과 codex 2차가 이미 대조한 표본은 피했다. 피한 것은 MCS 장·절·정리 번호 전수, `Random` 상수와 주기, `getDefault()`, Python `random` 주기, HashMap 포아송 표 수치, Paxson·Breslau·Axelsson·Bose 서지, OpenIntro 장 구성, Spring Boot 2.6 노트, CLRS 번호, Flajolet II.10, JLS §14.10·§15.7.3·§15.17, `Math`·Python 6.7 문서, `DoubleStream.sum` 문구, Python 3.12 `sum()`, Goldberg 정리, Little 1961 조건, pgvector 연산자·권장 문구다. 출처는 모두 curl GET(일반 브라우저 UA, 개인 식별 정보 없음)으로 받았다. OpenJDK는 `raw.githubusercontent.com/openjdk/jdk21u/master`, 서지는 `api.crossref.org/works/<DOI>`, HTML은 텍스트로 추출하고 PDF는 pdftotext로 변환했다. MCS는 scratchpad 사본 `math/01/mcs.txt`(2018-06-06판)를 썼다. 원문 사본은 `scratchpad/math/web/`에 있다.
- 결과: 55건 중 일치 54, 불일치 1(경미, 표현), 확인 불가 0. 관찰 4건은 일치로 판정했고 아래에 적었다(53번은 서지 세 개를 한 행에서 판정했다).
- 비고: 이 패스는 노트를 고치지 않았다. Debian wiki는 429였지만 표본으로 쓰지 않았다. Spring Boot 위키 raw는 404였고 사실 점검 표본이라 쓰지 않았다. Crossref는 처음에 429였고 몇 초 뒤 다시 받아 200이었다.

| # | 노트 (:줄) | 주장 | 출처 | 원문 인용 | 판정 |
|---|---|---|---|---|---|
| 1 | 01 :75 | `Stream.allMatch`는 스트림이 비면 `true`를 돌려주고 술어를 평가하지 않는다 | jdk21u `java/util/stream/Stream.java` | "If the stream is empty then {@code true} is returned and the predicate is not evaluated." | 일치 |
| 2 | 01 :285 | `allMatch`·`noneMatch` apiNote의 "vacuously satisfied" | 같은 파일 :1300, :1323 | "the stream is empty, the quantification is said to be vacuously satisfied and is always {@code true}" (두 메서드 모두) | 일치 |
| 3 | 01 :238 | 변수 이름은 디버그 정보(`javac -g`)가 있을 때만 나오고, 없으면 `<parameterN>`으로 나온다 | JEP 358 <https://openjdk.org/jeps/358> | "the variable name if a local variable table is available, otherwise "<parameter i >" or "<local i >"" · "if debug information is included in the class file (via javac -g), then local variable names are printed" | 일치 |
| 4 | 01 :90 | §15.24의 문법 `ConditionalOrExpression \|\| ConditionalAndExpression`(`&&`가 먼저 묶인다) | JLS SE 21 §15.24 | "ConditionalOrExpression: ConditionalAndExpression · ConditionalOrExpression \|\| ConditionalAndExpression" | 일치 |
| 5 | 02 :215 | Maven Surefire `enableAssertions` 기본값 `true` | surefire test-mojo | "By default, Surefire enables JVM assertions for the execution of your test cases. … Default: true" | 일치 |
| 6 | 02 :215 | Gradle `Test.enableAssertions`는 `java` 플러그인에서 기본 `true` | Gradle DSL Test | "boolean enableAssertions — Returns true if assertions are enabled for the process. Default with java plugin: true" | 일치 |
| 7 | 02 :252 | `Arrays.binarySearch`는 중복 키에서 어느 자리를 돌려줄지 보장하지 않는다 | jdk21u `java/util/Arrays.java` :1564 | "If the array contains multiple elements with the specified value, there is no guarantee which one will be found." | 일치 |
| 8 | 02 :281 | CLRS 2.1 루프 불변식의 초기화·유지·종료(강의 자료로 교차 확인) | Stanford CS161 lecture1.pdf | "Initialization: The loop invariant is satisfied at the beginning … Maintenance: … Termination: When the loop terminates, the invariant gives us a useful property" | 일치 |
| 9 | 03 :270 | `Object.java`: "equivalence relation partitions … into equivalence classes" | jdk21u `java/lang/Object.java` :134 | "An equivalence relation partitions the elements it operates on into <i>equivalence classes</i>" | 일치 |
| 10 | 03 :109 | consistent with equals = `compare(e1,e2)==0`과 `e1.equals(e2)`가 같은 값. 일관되지 않으면 정렬 컬렉션이 `Set`·`Map` 계약을 어긴다 | jdk21u `java/util/Comparator.java` :47–60 | "consistent with equals if and only if c.compare(e1, e2)==0 has the same boolean value as e1.equals(e2) … will violate the general contract for set (or map)" | 일치 |
| 11 | 03 :147 | `BigDecimal.equals`는 스케일까지 비교하고, Javadoc은 natural ordering이 equals와 일관되지 않다고 적는다 | jdk21u `java/math/BigDecimal.java` :3117, :3200 | "Note: this class has a natural ordering that is inconsistent with equals." · "Therefore 2.0 is not equal to 2.00 when compared by this method" | 일치 |
| 12 | 03 :90 | `record`의 `equals`는 컴포넌트 값으로 비교한다 | jdk21u `java/lang/Record.java` :116–126 | "the component is considered equal if and only if Objects.equals(this.c, r.c) would return true" (원시형은 `PW.compare(this.c, r.c)` 0) | 일치 |
| 13 | 03 :146 | `HashMap`은 넣거나 찾는 키 쪽에서 `key.equals(k)`(k = 이미 있는 키)를 부른다 | jdk21u `java/util/HashMap.java` :578, :641 | `((k = first.key) == key \|\| (key != null && key.equals(k)))` (`getNode`·`putVal`) | 일치 |
| 14 | 04 :285 | CLRS Lemma 22.11 "A directed graph G is acyclic if and only if a DFS of G yields no back edges" | Grinnell CSC 301 페이지 | "Lemma 22.11 A directed graph G is acyclic if and only if a depth-first search of G yields no back edges." | 일치 |
| 15 | 04 :286 | Kahn, "Topological sorting of large networks", CACM 5(11), 1962 | Crossref 10.1145/368996.369025 | title "Topological sorting of large networks", Communications of the ACM 5(11) pp. 558–562, 1962-11, A. B. Kahn | 일치 |
| 16 | 04 :250, :290 | jstack 출력 `Found one Java-level deadlock:` | jdk21u `src/hotspot/share/services/threadService.cpp` :1006 | `st->print_cr("Found one Java-level deadlock:");` | 일치 |
| 17 | 05 :34–35, :43 | Snowflake 시각 41비트(README "69 years"), machine 10비트, sequence 12비트 | twitter-archive/snowflake `snowflake-2010` README.mkd | "time - 41 bits (millisecond precision w/ a custom epoch gives us 69 years) · configured machine id - 10 bits - gives us up to 1024 machines · sequence number - 12 bits - rolls over every 4096 per machine" | 일치(관찰 1) |
| 18 | 05 :186, :290 | `core.abbrev`가 없으면 객체 수로 길이를 정해 "당분간" 유일하게 유지하려 하고, 최소 4다 | git-config 문서 | "computed based on the approximate number of packed objects in your repository, which hopefully is enough for abbreviated object names to stay unique for some time. … The minimum length is 4." | 일치 |
| 19 | 05 :178, :246 | git 오류 `short object ID … is ambiguous` | git v2.43.0 `object-name.c` :580 | `error(_("short object ID %s is ambiguous"), ds.hex_pfx);` | 일치 |
| 20 | 06 :36 | `ln n + 1/n ≤ H_n ≤ ln n + 1` (MCS 식 14.21) | MCS 2018-06-06판 14.4.2 | "Theorem 14.3.2 means that ln(n) + 1/n ≤ Hn ≤ ln(n) + 1. (14.21)" | 일치 |
| 21 | 06 :59–60 | MCS 22.5 경험칙: 상수만큼 작은 부분 문제면 대개 지수, 비율만큼 작으면 대개 다항식. 성능은 대개 부분 문제의 크기와 개수가 정한다 | MCS 22.5 | "The performance of a recursive procedure is usually dictated by the size and number of subproblems … if subproblems are smaller than the original by an additive factor, the solution is most often exponential. But if … only a fraction the size … typically bounded by a polynomial." | 일치 |
| 22 | 06 :60 | 하노이의 +1을 +n으로 바꿔도 해는 두 배쯤만 커진다 | MCS 22.5 | "shifting to the variation of Towers of Hanoi increased the last term from +1 to +n, but the solution only doubled." | 일치 |
| 23 | 07 :200 | Graham(2002-08): 가장 두드러진 단어 15개를 결합식으로 합치고, 0.9를 넘으면 스팸 | paulgraham.com/spam.html | "August 2002" · "the most interesting fifteen tokens … are used to calculate the probability" · "I treat mail as spam if the algorithm above gives it a probability of more than .9" | 일치 |
| 24 | 07 :298 | Guava `BloomFilter.create(Funnel, expectedInsertions, fpp)` Javadoc(기본 fpp 3%) | Guava BloomFilter Javadoc(snapshot-jre) | 3인자: "Creates a BloomFilter with the expected number of insertions and expected false positive probability." · 2인자 `create(Funnel, int/long expectedInsertions)`: "… and a default expected false positive probability of 3%." | **불일치(경미)** |
| 25 | 08 :59 | "Linearity of Expectation and Theorem 19.5.4 do not assume any independence" (19.5) | MCS p.885 | "the answer is still pn because Linearity of Expectation and Theorem 19.5.4 do not assume any independence." | 일치 |
| 26 | 08 :46 | 큰수의 법칙 MCS 따름정리 20.4.2 — 쌍별 독립, 분산 유한 전제 | MCS 20.4 | "Corollary 20.4.2. [Weak Law of Large Numbers] Let G1, …, Gn be pairwise independent variables with the same mean μ, and the same finite deviation" | 일치 |
| 27 | 08 :102 | 분산 덧셈은 쌍별 독립이면 충분하다(MCS 정리 20.3.8) | MCS 20.3 | "Theorem 20.3.8. [Pairwise Independent Additivity of Variance] If R1, R2, …, Rn …" | 일치 |
| 28 | 08 :295 | Dean·Barroso, "The Tail at Scale", CACM 56(2), 2013 | Crossref 10.1145/2408776.2408794 | "The tail at scale", Communications of the ACM 56(2) pp. 74–80, 2013-02, Jeffrey Dean · Luiz André Barroso | 일치 |
| 29 | 09 :64 | 트리화는 이미 8개인 칸에 9번째가 들어올 때 시도된다(`binCount >= TREEIFY_THRESHOLD - 1`) | jdk21u `HashMap.java` :260, :649 | `static final int TREEIFY_THRESHOLD = 8;` · `if (binCount >= TREEIFY_THRESHOLD - 1) // -1 for 1st` (binCount 0 = 첫 노드 뒤 → binCount 7에서 새 노드가 9번째) | 일치 |
| 30 | 09 :64 | 테이블이 64칸(`MIN_TREEIFY_CAPACITY`) 미만이면 트리화 대신 리사이즈 | 같은 파일 :275, :763 | `MIN_TREEIFY_CAPACITY = 64;` · `if (tab == null \|\| (n = tab.length) < MIN_TREEIFY_CAPACITY) resize();` | 일치 |
| 31 | 09 :64 | "tree bins are rarely used", 리사이즈 임계 0.75 기준이며 리사이즈 단위 때문에 분산이 크다 | 같은 파일 :181–187 | "In usages with well-distributed user hashCodes, tree bins are rarely used. … parameter of about 0.5 on average for the default resizing threshold of 0.75, although with a large variance because of resizing granularity." | 일치 |
| 32 | 09 :322 | `random.expovariate`의 인자 lambd = 1/원하는 평균 | Python 3 `random` 문서 | "lambd is 1.0 divided by the desired mean." | 일치 |
| 33 | 10 :336 | Little, "A Proof for the Queuing Formula: L = λW", OR 9(3), pp. 383–387, 1961 | Crossref 10.1287/opre.9.3.383 | Operations Research 9(3) pp. 383–387, 1961-06, John D. C. Little | 일치 |
| 34 | 10 :337 | Little, "Little's Law as Viewed on Its 50th Anniversary", OR 59(3), pp. 536–549, 2011 | Crossref 10.1287/opre.1110.0940 | "OR FORUM—Little's Law as Viewed on Its 50th Anniversary", Operations Research 59(3) pp. 536–549, 2011-06 | 일치 |
| 35 | 10 :339 | Harchol-Balter 2013, 3부 운영 법칙·4부 마르코프 사슬→단순 큐·5부 서버 팜·6부 높은 변동성(Cambridge Core 목차) | Cambridge Core 목차 페이지 | "III The Predictive Power of Simple Operational Laws … IV From Markov Chains to Simple Queues · V Server Farms and Networks: Multi-server, Multi-queue Systems · VI Real-World Workloads: High Variability and Heavy Tails" · "Published online … 05 February 2013" | 일치(관찰 2) |
| 36 | 11 :309 | `BigInteger.modInverse`는 서로소가 아니면 `ArithmeticException` | jdk21u `java/math/BigInteger.java` :3415–3417 | "@throws ArithmeticException m ≤ 0, or this BigInteger has no multiplicative inverse mod m (that is, this BigInteger is not relatively prime to m)." | 일치 |
| 37 | 11 :165 | `absExact` 예외 메시지 "Overflow to represent absolute value of Integer.MIN_VALUE" | jdk21u `java/lang/Math.java` :1904 | `"Overflow to represent absolute value of Integer.MIN_VALUE"` | 일치 |
| 38 | 11 :128, :269 | `Math.absExact`는 Java 15+ | 같은 파일 :1897–1899 | "@throws ArithmeticException if the argument is Integer#MIN_VALUE … @since 15" | 일치 |
| 39 | 11 :310 | 내장 `pow(base, -1, mod)`는 3.8+ | Python 3 내장 함수 문서 | "Changed in version 3.8: For int operands, the three-argument form of pow now allows the second argument to be negative, permitting computation of modular inverses." | 일치 |
| 40 | 12 :169 | `Collections.shuffle` 구현 `for (int i=size; i>1; i--) swap(list, i-1, rnd.nextInt(i));`, Javadoc "All permutations occur with equal likelihood assuming that the source of randomness is fair." | jdk21u `java/util/Collections.java` :459, :485–486 | 코드와 문구가 그대로 있다 | 일치 |
| 41 | 12 :78 | `SplittableRandom`·`ThreadLocalRandom` Javadoc: 주기 2^64, 둘 다 "not cryptographically secure" | jdk21u `SplittableRandom.java` :39, :79 · `ThreadLocalRandom.java` :61, :82 | "(with period 2<sup>64</sup>)" · "Instances of … are not cryptographically secure" (두 클래스 모두) | 일치 |
| 42 | 12 :90 | `ThreadLocalRandom` `seeder`: 기본은 시간 기반 mix, `java.util.secureRandomSeed=true`면 `SecureRandom.getSeed(8)` | jdk21u `ThreadLocalRandom.java` :400–421 | `new AtomicLong(RandomSupport.mixMurmur64(System.currentTimeMillis()) ^ RandomSupport.mixMurmur64(System.nanoTime()))` · `if (Boolean.parseBoolean(sec)) { byte[] seedBytes = java.security.SecureRandom.getSeed(8);` | 일치 |
| 43 | 12 :77, :329 | Marsaglia, "Xorshift RNGs", JSS 8(14), 2003 | Crossref 10.18637/jss.v008.i14 | "Xorshift RNGs", Journal of Statistical Software vol 8 issue 14, 2003, George Marsaglia | 일치 |
| 44 | 12 :79 | JEP 356은 JDK 17 | JEP 356 페이지 | "Release 17" | 일치 |
| 45 | 13 :259 | `vector_norm`은 pgvector 함수 | pgvector README(master) | "vector_norm(vector) → double precision \| Euclidean norm" | 일치 |
| 46 | 13 :261 | 정규화는 `l2_normalize(vector)`(README 함수 표) | 같은 README | "l2_normalize(vector) → vector \| normalize with Euclidean norm \| 0.7.0" | 일치(관찰 3) |
| 47 | 13 :328 | MIT OCW 18.06 Linear Algebra, Spring 2010, Gilbert Strang | OCW 강의 페이지 | "18.06 \| Spring 2010 \| Undergraduate" · "Prof. Gilbert Strang" | 일치 |
| 48 | 14 :307 | 커널 RAS 문서: CE는 앞으로 올 UE의 예측 신호일 수 있지만 반드시 그렇지는 않다. CE를 보이는 모듈을 미리 교체하면 UE 가능성이 준다 | docs.kernel.org RAS | "can but must not necessarily be a predictor of future UE events" · "preventive maintenance and proactive part replacement of memory modules exhibiting CEs can reduce the likelihood of the dreaded UE events and system panics." | 일치 |
| 49 | 14 :307 | EDAC가 `/sys/devices/system/edac/mc/mcX/ce_count`·`ue_count`를 낸다 | 같은 문서 | "Starting in directory /sys/devices/system/edac/mc, each memory controller will be represented by its own mcX directory" · 트리 `mc0 ├── ce_count … ├── ue_count` | 일치 |
| 50 | 14 :344 | Hamming, BSTJ 29(2), pp. 147–160, 1950 | Crossref 10.1002/j.1538-7305.1950.tb00463.x | "Error Detecting and Error Correcting Codes", Bell System Technical Journal 29(2) pp. 147–160, 1950-04 | 일치 |
| 51 | 14 :343 | Shannon, BSTJ 27, pp. 379–423, 623–656, 1948 | Crossref 10.1002/j.1538-7305.1948.tb01338.x · …tb00917.x | 27(3) pp. 379–423, 1948-07 · 27(4) pp. 623–656, 1948-10 | 일치 |
| 52 | 14 :242, :350 | pgvector `<~>` = 해밍 거리(이진 벡터) | pgvector README | "`<~>` - Hamming distance (binary vectors)" | 일치 |
| 53 | 15 :364–366 | Goldberg는 ACM Computing Surveys 1991년 3월, Kahan은 CACM 8(1) p. 40 1965, Higham은 2판 SIAM 2002 | Crossref 10.1145/103162.103163 · 10.1145/363707.363723 · 10.1137/1.9780898718027 | Goldberg: ACM Computing Surveys 23(1) pp. 5–48, 1991-03 · Kahan: "Pracniques: further remarks on reducing truncation errors", CACM 8(1) p. 40, 1965-01 · Higham: SIAM, edition "Second", 2002 | 일치 |
| 54 | 15 :128, :369 | `math.fsum`은 부분합 여러 개를 추적하고, 반올림 half-even을 전제한다 | Python 3 `math` 문서 | "Avoids loss of precision by tracking multiple intermediate partial sums. The algorithm's accuracy depends on IEEE-754 arithmetic guarantees and the typical case where the rounding mode is half-even." | 일치 |
| 55 | 15 :167 | 이 JDK의 `DoubleStream.sum()`은 보상 합으로 동작했다(구현 세부) | jdk21u `java/util/stream/DoublePipeline.java` :441–453 | "index 1 holds the negated low-order bits of the sum computed via compensated summation" · `Collectors.sumWithCompensation(ll, d);` | 일치 |

## 불일치 상세

### 24 — 07 :298 Guava 기본 fpp(경미, 표현)
- 노트: "Guava `BloomFilter.create(Funnel, expectedInsertions, fpp)` Javadoc(기본 fpp 3%)"
- 원문: fpp를 받는 3인자 `create`는 "Creates a BloomFilter with the expected number of insertions and expected false positive probability."라고만 적는다. 3%는 fpp를 받지 않는 2인자 오버로드 `create(Funnel, int/long expectedInsertions)`의 기본값이다("… and a default expected false positive probability of 3%."). `toBloomFilter(Funnel, long)` Collector도 같다.
- 제안 문구: "Guava `BloomFilter.create(Funnel, expectedInsertions, fpp)` Javadoc — fpp를 생략한 `create(Funnel, expectedInsertions)`의 기본 fpp는 3%"

## 확인 불가·관찰 상세

- 확인 불가: 0건.
- 관찰 1(17, 05 :34): 그림의 `[ 부호 1 ]` 칸은 README에 없다. README는 41·10·12비트만 적는다. 1비트는 64 − 63에서 나온 값이다. 노트가 그림 전체를 "(twitter-archive/snowflake README, 2010)"로 달았으므로, 원하면 "부호 1비트는 64 − (41+10+12)에서 나온 값" 같은 한 줄을 붙일 수 있다. 판정은 일치로 했다(수치 셋이 맞고 2^41 ms ≈ 69.7년도 계산상 맞다).
- 관찰 2(35, 10 :339): Cambridge Core에 보이는 것은 부 제목뿐이다. "3부 운영 법칙(Little)"처럼 결과를 부에 대응시킨 것은 부 제목에서 한 추론이다. 노트도 "장 번호와 각 결과가 실린 장은 확인하지 못했다 `[?]`"라고 이미 한정하고 있어 일치로 판정했다. 목차에는 7부 "Smart Scheduling in the M/G/1"도 있는데, 노트는 이를 적지 않았다(누락이지 오류는 아니다).
- 관찰 3(46, 13 :261): `l2_normalize`는 pgvector 0.7.0부터 있다(README 함수 표의 버전 열). 예전 버전을 쓰는 환경에서는 없을 수 있다. 버전 표기를 붙일지는 선택이다.
- 관찰 4(53, 15 :365): Crossref의 Kahan 1965 제목에는 CACM 칼럼 접두어 "Pracniques:"가 붙어 있다. 노트의 제목은 접두어를 뺀 통용 표기라 일치로 판정했다.
- 참고: 01 :238의 `<parameter1>` 표기는 JEP 원문에서 `"<parameter i >"`(HTML 추출로 공백이 생김)로 나온다. 실제 출력 형식과는 실험이 근거이고 모순되지 않는다.

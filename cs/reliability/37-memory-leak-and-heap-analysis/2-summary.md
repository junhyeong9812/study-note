# reliability/37-memory-leak-and-heap-analysis — 힙 덤프·지배자 트리·힙 밖 누수 — 정리 (힌트)

## 해결하는 문제

GC가 있는 언어에도 메모리 누수가 있다. GC는 **아무도 가리키지 않는** 객체만 치운다. 필요 없는데 누군가 계속 가리키면 영원히 남는다.

```text
 GC 직후 사용 힙(바닥선)
  │                                   ╱  ← 누수: 바닥선이 계속 올라간다 → 결국 OutOfMemoryError
  │                    ╱╲  ╱╲  ╱╲ ╱
  │         ╱╲  ╱╲  ╱╲╱  ╲╱  ╲╱
  │  ╱╲  ╱╲╱  ╲╱  ╲╱                    정상: 톱니가 생겨도 바닥선은 평평하다
  └────────────────────────────────▶ 시간
```

- *누수(leak)*: 더 쓰지 않을 객체가 도달 가능한 채로 남아 회수되지 않는 것.
- *바닥선*: 매 GC 직후의 사용량. 톱니의 꼭대기가 아니라 **바닥**을 봐야 누수가 보인다.

쉬운 예: 사무실 사물함이다.
- 퇴사자 사물함은 비워야 한다. 그런데 명부에 이름이 남아 있으면 청소부(GC)가 손대지 못한다.
- 명부(static Map)에서 지우지 않는 한, 사물함은 계속 늘어난다.

똑같은 구조다.\
실무 예: 세션을 넣기만 하는 static Map, 해제하지 않은 이벤트 리스너, 스레드 풀 스레드에 남은 ThreadLocal, 크기 제한 없는 캐시. 그리고 힙 밖의 누수(direct buffer·native 라이브러리) — 이때는 힙 그래프가 평평한데 컨테이너가 죽는다.

## 동작·원리

### 1. 도달 가능성 — GC가 남기는 기준

```text
 GC 루트들 (스레드 스택의 지역 변수, static 필드, JNI 참조 …)
   │
   ├─▶ class Leak ──static SESSIONS──▶ HashMap ──▶ Node[] ──▶ Node ──▶ Session ──▶ byte[2048]
   │                                                                    │
   └─▶ Thread worker-1 ───────────────────────────────────────────────▶ Config(공유)
```

- *GC 루트*: 힙 밖에서 접근할 수 있는 객체. Eclipse MAT 문서의 분류: System Class(부트스트랩·시스템 클래스로더가 올린 클래스), Java Local(스택의 지역 변수), Thread, JNI Global, Busy Monitor 등.
- 루트에서 **강한 참조**를 따라 닿는 객체(그래프 탐색 — DFS·BFS)는 살아 있다(약한 참조로만 닿으면 GC가 치울 수 있다 — 아래 「쓰이는 자료구조·알고리즘」). 이것이 누수의 정의를 정한다: **누수 = 루트에서 강한 참조로 닿지만 쓰지 않는 객체**.

### 2. 히스토그램만으로 부족한 이유 — shallow vs retained

- *shallow size*: 객체 자체의 크기.
- *retained size*: 그 객체가 사라지면 함께 회수될 객체들(retained set)의 shallow 합(MAT 문서).
- 히스토그램은 클래스별 shallow 합이다. 누수의 피해자(`byte[]`)는 크게 보이지만, **누가 쥐고 있나**(원인)는 안 보인다.

### 3. 지배자 트리 — "누가 쥐고 있나"를 한 그림으로

```text
 객체 그래프                               지배자 트리
 루트 ─▶ A ─▶ C                             루트
  │      └──▶ D ◀─┐                          ├── A ── C        (C는 A를 통해서만 닿는다)
  └──▶ B ─────────┘                          ├── B
                                             └── D             (D는 A로도 B로도 닿는다 → 루트가 지배)
```

- *지배(dominate)*: 루트에서 y로 가는 **모든** 경로가 x를 지나면 x가 y를 지배한다(MAT 문서).
- *직접 지배자(immediate dominator)*: y의 지배자 중 y에 가장 가까운 것. 이것을 부모로 삼은 트리가 지배자 트리다.
- 성질: x의 서브트리 = x의 retained set. 그래서 **서브트리 크기 합 = retained size**다.
- 지배자 트리의 간선은 원래 참조와 1:1로 대응하지 않는다(MAT 문서).
- 계산: Lengauer–Tarjan(1979)이 거의 선형 시간에 구한다(단순판 O(E log N)). MAT 소스 `DominatorTree.java`에도 그 알고리즘의 반지배자(`semi`)·`bucket` 배열이 있다.

### 4. 실험 A: 무제한 캐시 누수 — 바닥선, 히스토그램, 힙 덤프, OOM

```java
static final Map<String, Session> SESSIONS = new HashMap<>();   // 누수 지점: 넣기만 한다
record Session(String id, byte[] payload, List<String> tags) {}

for (int step = 1; ; step++) {
    for (int i = 0; i < 5_000; i++, id++) {
        SESSIONS.put("s" + id, new Session("s" + id, new byte[2048], List.of("web", "kr")));
        if (i % 2 == 0) garbage = new byte[4096];     // 금방 버려지는 쓰레기
    }
    System.gc();                                       // 실험용: 바닥선을 보려고 GC를 강제
    long used = mem.getHeapMemoryUsage().getUsed() / (1024 * 1024);
    System.out.printf("step %2d: 세션 %6d개, GC 직후 사용 힙 %4d MiB%n", step, SESSIONS.size(), used);
    if (step == 2 || step == 6) jcmd(pid, "GC.class_histogram", 6);
    if (step == 6) jcmd(pid, "GC.heap_dump /tmp/leak.hprof", 99);
}
```

(실험, JDK 21.0.12 temurin 컨테이너 `--cpus=2 --memory=512m`, `-Xmx128m`, GC는 JVM 자동 선택 = Serial(GC 로그 첫 줄 `Using Serial` — 메모리 512m 컨테이너는 JDK 21 `os::is_server_class_machine`의 기준(프로세서 2개 이상 + 메모리 2G−256M 이상)에 못 미쳐 G1이 아니다), 2026-10-01 — `...`는 생략한 줄)

```text
step  1: 세션   5000개, GC 직후 사용 힙   12 MiB
step  2: 세션  10000개, GC 직후 사용 힙   22 MiB
  $ jcmd <pid> GC.class_histogram
   num     #instances         #bytes  class name (module)
  -------------------------------------------------------
     1:         39810       21582392  [B (java.base@21.0.12)
     2:         29694         712656  java.lang.String (java.base@21.0.12)
     3:         12463         398816  java.util.HashMap$Node (java.base@21.0.12)
     4:         10070         241680  java.util.ImmutableCollections$List12 (java.base@21.0.12)
step  3: 세션  15000개, GC 직후 사용 힙   33 MiB
...
step  6: 세션  30000개, GC 직후 사용 힙   65 MiB
  $ jcmd <pid> GC.class_histogram
   num     #instances         #bytes  class name (module)
  -------------------------------------------------------
     1:         99832       63823304  [B (java.base@21.0.12)
     2:         69716        1673184  java.lang.String (java.base@21.0.12)
     3:         32463        1038816  java.util.HashMap$Node (java.base@21.0.12)
     4:         30070         721680  java.util.ImmutableCollections$List12 (java.base@21.0.12)
  $ jcmd <pid> GC.heap_dump /tmp/leak.hprof
  Dumping heap to /tmp/leak.hprof ...
  Heap dump file created [74980681 bytes in 0.147 secs]
...
step 11: 세션  55000개, GC 직후 사용 힙  119 MiB
Exception in thread "main" java.lang.OutOfMemoryError: Java heap space
	at Leak.main(Leak.java:20)
```

같은 실행의 GC 로그(`-Xlog:gc`):

```text
[1.906s][info][gc] GC(20) Pause Full (Heap Dump Initiated GC) 66M->65M(123M) 46.454ms
[3.914s][info][gc] GC(45) Pause Full (Allocation Failure) 123M->123M(123M) 70.429ms
[3.987s][info][gc] GC(46) Pause Full (Allocation Failure) 123M->123M(123M) 71.956ms
[4.065s][info][gc] GC(47) Pause Full (Allocation Failure) 123M->123M(123M) 76.891ms
```

- 관찰 1 — 바닥선: 5,000개마다 약 10~11 MiB씩 올라 11단계에서 OOM. 세션 하나 ≈ 2 KiB 배열 + 객체 몇 개.
- 관찰 2 — 히스토그램 1위는 `[B`(byte[])다. 원인(`SESSIONS`)은 표에 없다. 같은 클래스의 개수가 단계마다 비례해 느는 것은 보이지만, 누가 쥐는지는 지배자 트리가 답한다.
- 관찰 3 — 힙 덤프는 **Full GC를 먼저 한 뒤**(`Heap Dump Initiated GC`, 46ms) 65 MiB 힙을 75 MB 파일로 0.147초에 썼다(재실행: 43ms, 0.196초 — 실행마다 다르다). 히스토그램도 같은 GC 로그에 `Pause Full (Heap Inspection Initiated GC)`를 남겼다(재실행 로그 확인). JDK 21 `jcmd` 문서도 `GC.heap_dump`를 Impact: High, 기본으로 full GC를 요청한다고 적는다. 해석: 멈춤과 파일 크기는 살아 있는 힙 크기에 따라 커진다. 수 GB 힙에서의 실제 시간은 이 실험으로 재지 않았다.
- 관찰 4 — OOM 직전에는 Full GC가 연달아 돌며 하나도 회수하지 못한다(`123M->123M`). Full GC마다 약 70ms씩 애플리케이션 실행이 반복해서 멈췄다(이 실험은 요청·응답을 재지 않았다).

### 5. 실험 B: 지배자 트리와 retained size (장난감 그래프)

위 실험의 모양을 작은 그래프로 만들어 직접 계산했다. 크기(바이트)는 예시 값이다. 알고리즘은 Cooper–Harvey–Kennedy 반복법(2001)으로, Lengauer–Tarjan과 같은 트리를 더 짧은 코드로 구한다.

```java
// idom 반복: 역후위 순서로 돌며 "이미 계산된 선행자들의 공통 지배자"를 구한다
while (changed) {
    changed = false;
    for (int k = order.size() - 1; k >= 0; k--) {
        int b = order.get(k); if (b == root) continue;
        int nd = -1;
        for (int p : pred.get(b)) if (idom[p] != -1) nd = (nd == -1) ? p : intersect(p, nd, idom, po);
        if (idom[b] != nd) { idom[b] = nd; changed = true; }
    }
}
// retained = 지배자 트리에서 자기 서브트리의 shallow 합 (후위 순서 = 자식 먼저)
for (int b : order) { ret[b] += shallow.get(b); if (b != root) ret[idom[b]] += ret[b]; }
```

(실험, JDK 21.0.12, 2026-10-01 — `...`는 생략한 줄)

```text
지배자 트리 (shallow / retained 바이트)
<GC 루트들>  0 / 6664
  class Leak (static SESSIONS)  16 / 6504
    HashMap  48 / 6488
      HashMap$Node[]  80 / 6440
        HashMap$Node#1  32 / 2120
          Session#1  24 / 2088
            byte[2048]#1  2064 / 2064
        ... (#2, #3 같은 모양)
  Thread worker-1 (스택 지역 변수)  120 / 120
  Config (공유)  40 / 40
클래스별 히스토그램(shallow 합): {Config (공유)=40, HashMap=48, HashMap$Node=96, HashMap$Node[]=80, Session=72, Thread worker-1 (스택 지역 변수)=120, byte[2048]=6192, class Leak (static SESSIONS)=16}
```

- 관찰 1 — 히스토그램 1위는 `byte[2048]`(6192)지만, 지배자 트리 꼭대기에서 retained가 가장 큰 것은 `class Leak (static SESSIONS)`(6504)다. **고칠 곳은 여기다.**
- 관찰 2 — `Config`는 세션들과 스레드가 함께 가리킨다. 어느 Session도 단독으로 지배하지 않아 직접 지배자가 루트다. Session의 retained(2088)에 Config가 들어가지 않는다. "Session을 지우면 얼마나 줄어드나"의 정답이 retained다.

### 6. 실험 C: 힙 밖 누수 — 힙은 1 MiB인데 RSS만 오른다

```java
for (int i = 0; i < 16; i++) {
    ByteBuffer b = ByteBuffer.allocateDirect(1024 * 1024);
    for (int j = 0; j < b.capacity(); j += 4096) b.put(j, (byte) 1);   // 페이지를 건드려 RSS에 잡히게
    HELD.add(b);                                                         // 놓지 않는다
}
```

(실험, JDK 21.0.12 temurin 컨테이너 `--cpus=2`, `-Xmx64m`, 2026-10-01 — `...`는 생략한 줄, `##` 줄은 실행 스크립트의 echo 문구 그대로. A는 `-XX:MaxDirectMemorySize=96m -XX:NativeMemoryTracking=summary`, B는 `-XX:MaxDirectMemorySize=1g`에 컨테이너 `--memory=256m --memory-swap=256m`)

```text
## A: MaxDirectMemorySize=96m
step  1: direct   16 MiB, 힙 사용   1 MiB, RSS   56 MiB
step  4: direct   64 MiB, 힙 사용   1 MiB, RSS  105 MiB
  NMT Total: reserved=1526990KB, committed=100954KB
  NMT -                 Java Heap (reserved=65536KB, committed=8320KB)
  NMT -                     Class (reserved=1048702KB, committed=382KB)
  NMT -                    Thread (reserved=13492KB, committed=908KB)
  NMT -                     Other (reserved=65546KB, committed=65546KB)
step  5: direct   80 MiB, 힙 사용   1 MiB, RSS  122 MiB
Exception in thread "main" java.lang.OutOfMemoryError: Cannot reserve 1048576 bytes of direct buffer memory (allocated: 99622912, limit: 100663296)
## B: 상한 없음(기본=최대 힙?) 대신 1g, 컨테이너 256m
step  1: direct   16 MiB, 힙 사용   1 MiB, RSS   55 MiB
...
step 14: direct  224 MiB, 힙 사용   1 MiB, RSS  265 MiB
State: OOMKilled=true ExitCode=137
```

- 관찰 1 — 힙은 끝까지 1 MiB다. 힙 그래프만 보는 대시보드에는 아무 일도 없다.
- 관찰 2 — A: JVM 안의 한도(`MaxDirectMemorySize`)에 먼저 닿으면 JVM이 `OutOfMemoryError: Cannot reserve ... direct buffer memory`를 던진다. 로그가 남는다. NMT에서는 direct buffer가 `Other`(64 MiB committed)로 잡혔다.
- 관찰 3 — B: JVM 한도가 컨테이너 한도보다 크면 커널이 먼저 죽인다. JVM 로그 없이 `OOMKilled=true`, 종료 코드 137(SIGKILL) → [os/13-oom-and-memory-limits](../../os/13-oom-and-memory-limits/2-summary.md).
- 관찰 4 — 마지막 줄 RSS(265 MiB)가 한도 256 MiB보다 크게 찍혔다. RSS는 파일 매핑 페이지(공유 라이브러리 등)도 세므로 cgroup 메모리 집계와 정확히 같지 않다.
- `MaxDirectMemorySize`를 주지 않으면 JVM이 자동으로 정한다(JDK 21 `java` 문서). OpenJDK 소스상 기본값은 최대 힙 크기다(os/13 5절).

## 쓰이는 자료구조·알고리즘

- **객체 그래프 도달성 = 그래프 탐색** — 루트에서 DFS·BFS로 닿는 정점이 살아 있다 → [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md).
- **지배자 트리** — Lengauer–Tarjan(TOPLAS 1979, 반지배자 + 경로 압축) 또는 Cooper–Harvey–Kennedy 반복법. 원래 컴파일러가 제어 흐름 그래프(flowgraph)를 분석하려고 만든 알고리즘을 객체 그래프에 쓴 것이다.
- **후위 순서 합산** — retained = 서브트리 합. 자식을 먼저 처리하면 한 번 훑기로 끝난다.
- **해시맵** — 누수의 단골 그릇. 키를 지우지 않으면 엔트리·값이 모두 남는다 → [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md). 크기 상한 캐시는 LRU → [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md).
- **약한 참조(WeakReference)** — 루트에서 약한 참조로만 닿으면 GC가 치울 수 있다. 리스너·캐시 누수의 한 처방(남용하면 원치 않을 때 사라진다).

## 적용 — 풀어나가는 법

### 1. 순서

```text
 메모리가 오른다
   ├─ 안정된 부하에서 힙 바닥선(old까지 수거한 GC 직후)이 계속 오른다? ── 예 ──▶ 누수 의심: 히스토그램 2회 비교 → 힙 덤프 → 지배자 트리
   └─ 아니오, 힙 used·committed는 평평한데 RSS만 오른다 ─▶ 힙 밖: NMT → direct buffer·thread·metaspace → 그래도 아니면 native(malloc)
```

1. **바닥선을 본다.** GC 로그의 `A->B(C)`에서 B(GC 후)의 추세 — young GC는 old를 보통 치우지 않으므로 Full GC 뒤 값을 본다(G1 mixed GC는 old 일부만 치운다) —, 또는 `jvm_memory_used_bytes{area="heap"}`의 GC 직후 값.
2. 힙이면 히스토그램을 **시간 간격을 두고 두 번** 떠서 늘어난 클래스를 본다(실험 A의 2단계 vs 6단계).
3. 힙 덤프를 떠 MAT로 연다: Dominator Tree → retained 상위 → "Path to GC Roots"로 누가 쥐나.
4. 힙 밖이면 NMT를 켜고 기준점(baseline) 대비 증가를 본다. 그래도 설명 안 되는 RSS는 JVM 밖 `malloc`(native 라이브러리)일 수 있다 — async-profiler `nativemem` 모드로 free 짝이 없는 할당(누수 후보 — 아직 쓰는 정상 할당일 수도 있다. 그래서 `--leak`은 기본으로 마지막 10% 구간의 할당을 뺀다)을 본다.

### 2. 명령

```bash
jcmd <pid> GC.heap_info                          # 힙 영역 요약 (Impact: Medium)
jcmd <pid> GC.class_histogram | head -20         # 클래스별 개수·바이트 (Impact: High — 실험 GC 로그에 Heap Inspection Initiated full GC)
jcmd <pid> GC.heap_dump /data/dump.hprof         # 힙 덤프 (Impact: High — 기본 full GC, 디스크 = 살아 있는 힙 크기)
# 시작 옵션: OOM 순간 자동 덤프
java -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/data/ ...
# 힙 밖: NMT (시작 옵션 필요, summary 모드)
java -XX:NativeMemoryTracking=summary ...
jcmd <pid> VM.native_memory baseline
jcmd <pid> VM.native_memory summary.diff
grep -E 'VmRSS|RssAnon|RssFile' /proc/<pid>/status
# native malloc 누수 (async-profiler 4.x)
asprof start -e nativemem -f app.jfr <pid>   # … 시간이 지난 뒤
asprof stop <pid>; jfrconv --total --nativemem --leak app.jfr leak.html
```

- PromQL(Micrometer의 JVM 지표 이름 예):

```promql
# 힙 사용량의 1시간 최솟값 추세 — 바닥선이 오르는지
min_over_time(jvm_memory_used_bytes{area="heap"}[1h])
# 컨테이너 메모리(cAdvisor) — 힙 그래프와 나란히 놓고 간격이 벌어지는지 본다
sum by (pod) (container_memory_working_set_bytes{container!=""})
```

### 3. 누수 패턴과 처방 (Java)

```java
// 1) static 컬렉션 — 넣기만 한다 → 크기 상한 + 만료가 있는 캐시로 (예: LinkedHashMap LRU)
static final Map<String, Session> SESSIONS = Collections.synchronizedMap(new LinkedHashMap<>(16, 0.75f, true) {
    @Override protected boolean removeEldestEntry(Map.Entry<String, Session> e) { return size() > 10_000; }
});

// 2) 리스너 — 등록만 하고 해제하지 않는다 → 해제를 수명에 묶는다
AutoCloseable sub = bus.subscribe(this::onEvent);   // close() 시 해제
try (sub) { … }

// 3) ThreadLocal — 스레드 풀 스레드는 죽지 않는다 → 요청 끝에 remove()
private static final ThreadLocal<RequestCtx> CTX = new ThreadLocal<>();
try { CTX.set(ctx); handle(); } finally { CTX.remove(); }
```

- ThreadLocal: 스레드가 살아 있고 ThreadLocal 인스턴스에 닿을 수 있는 동안 각 스레드는 자기 사본을 암묵적으로 참조한다(JDK 21 `ThreadLocal` 문서). 풀 스레드는 오래 살므로 `remove()`가 없으면 마지막 요청의 값이 남는다.

### 4. 운영 중 힙 덤프의 비용을 줄이기

- 트래픽을 빼고(LB에서 제외, readiness false) 뜬다. 다른 인스턴스가 받는 동안 한 대만.
- 덤프 경로의 디스크 여유를 확인한다(덤프 ≈ 살아 있는 힙. 실험: 65 MiB 힙 → 75 MB 파일).
- 덤프 파일에는 개인정보·비밀이 그대로 있다. 접근 권한·보관 기한을 정한다.

## 장애 시나리오와 대처

### 1. ⚠ GC 후 바닥선이 계속 올라가는 톱니 → `OutOfMemoryError: Java heap space`

- 현상: 배포 후 며칠마다 서버가 OOM으로 재시작한다. 재시작 직후에는 멀쩡하다.
- 보이는 형태: 힙 그래프의 바닥선 우상향, OOM 직전 Full GC 연속(실험 A: `123M->123M` 반복), 응답 정지, `java.lang.OutOfMemoryError: Java heap space`.
- 원인: 루트(static·장수 스레드·싱글턴 빈)에서 닿는 컬렉션이 계속 커진다.
- 대처: `HeapDumpOnOutOfMemoryError`로 OOM 순간을 잡는다. MAT 지배자 트리 retained 상위 → GC 루트 경로. 컬렉션에 상한·만료를 두고, 바닥선 추세에 경보를 건다.

### 2. ⚠ 힙은 정상인데 RSS만 우상향 → `OOMKilled`

- 현상: 컨테이너가 137로 재시작한다. 애플리케이션 로그에는 OOM이 없다. 힙 대시보드는 평평하다.
- 보이는 형태: 실험 C의 B — 힙 1 MiB, RSS 55 → 265 MiB, `OOMKilled=true ExitCode=137`.
- 원인: direct buffer(NIO·Netty), 스레드 스택(스레드 수 증가), metaspace(클래스로더 누수), JNI·native 라이브러리 `malloc`.
- 대처: NMT baseline/diff로 영역을 좁힌다(direct buffer는 `Other`에 잡혔다). JVM 한도(`MaxDirectMemorySize`)를 컨테이너 한도 안쪽으로 두면, direct buffer가 그 한도에 먼저 닿는 경우 커널 kill 대신 **JVM 예외**(로그가 남는다)가 난다. 이 한도는 direct buffer만 묶으므로 힙·스레드·다른 native 메모리 몫의 여유는 따로 남겨야 한다. NMT에 안 잡히는 증가는 `nativemem` 프로파일.

### 3. ⚠ 운영 중 힙 덤프 → 긴 STW와 디스크 풀

- 현상: 원인을 찾으려고 큰 힙에서 덤프를 떴더니 서비스가 오래 멈추고, 로그 디스크가 차서 다른 프로세스도 쓰기 실패.
- 보이는 형태: GC 로그의 `Pause Full (Heap Dump Initiated GC)`, 헬스체크 실패, `No space left on device`.
- 원인: `GC.heap_dump`는 기본으로 full GC를 요청하고 살아 있는 힙 전체를 쓴다(jcmd 문서 Impact: High). 실험에서는 65 MiB에서 46ms + 0.147초(재실행 43ms + 0.196초)였고, 비용은 힙 크기에 따라 커진다(큰 힙의 수치는 재지 않음).
- 대처: 트래픽을 뺀 한 대에서, 여유 있는 별도 볼륨에 뜬다. 먼저 히스토그램 2회 비교로 충분한지 본다. OOM 자동 덤프 경로도 별도 볼륨으로.

### 4. ThreadLocal·리스너 누수 — 재배포할수록 metaspace가 찬다

- 현상: 같은 JVM에 앱을 재배포(핫 리로드)할 때마다 메모리가 늘고, 결국 `OutOfMemoryError: Metaspace`.
- 보이는 형태: 덤프에 같은 클래스 이름이 클래스로더별로 여러 벌. 옛 클래스로더가 GC 루트(풀 스레드의 ThreadLocal, 전역 레지스트리의 리스너)에서 닿는다.
- 원인: 장수 객체가 옛 앱 객체를 하나라도 쥐면, 그 객체의 클래스 → 클래스로더 → 그 로더가 올린 클래스들이 줄줄이 도달 가능해져 남는다.
- 대처: 요청 끝 `ThreadLocal.remove()`, 종료 훅에서 리스너 해제. 지배자 트리에서 옛 클래스로더의 GC 루트 경로를 본다.

## 핵심 문장

- GC는 강한 참조로 도달할 수 없는 객체만 치운다. 누수 = 루트에서 강한 참조로 닿지만 쓰지 않는 객체다.
- 누수는 톱니의 꼭대기가 아니라 GC 직후 바닥선의 추세로 본다. 실험에서는 5,000건마다 약 10 MiB씩 올라 11단계에서 OOM이 났다.
- 히스토그램은 피해자(`byte[]`)를, 지배자 트리의 retained size는 범인(`static SESSIONS`)을 보여 준다.
- retained size = 지배자 트리의 서브트리 합이다. 여럿이 공유하는 객체는 어느 한쪽의 retained에도 들어가지 않는다.
- 힙 used와 committed가 다 평평한데 RSS가 오르면 힙 밖이다. JVM 한도에 먼저 닿으면 예외와 로그가 남고, 컨테이너 한도에 먼저 닿으면 로그 없이 137로 죽는다.
- 힙 덤프는 full GC와 힙 크기만큼의 디스크를 쓴다. 트래픽을 뺀 한 대에서 뜬다.

## 관련 주제·근거

- 선행
  - [36-profiling](../36-profiling/2-summary.md) — 할당 프로파일(`alloc`), `nativemem`
  - language/10 `garbage-collection` — mark-sweep·세대·G1 (영역 표 [../../language/README.md](../../language/README.md)에서 "미작성")
  - [os/13-oom-and-memory-limits](../../os/13-oom-and-memory-limits/2-summary.md) — cgroup 한도, OOM killer, JVM 힙 < limit인데 죽는 이유(5절), NMT
- 후속·연결
  - [52-reliability-symptom-index](../52-reliability-symptom-index/2-summary.md)의 "RSS만 우상향"
  - [26-incident-response-and-postmortem](../26-incident-response-and-postmortem/2-summary.md) — 재시작 전 증거(덤프) 보존
  - [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md) — 도달성 탐색
- 논문·문서
  - Lengauer, Tarjan, "A fast algorithm for finding dominators in a flowgraph", ACM TOPLAS 1(1):121–141, 1979
  - Cooper, Harvey, Kennedy, "A Simple, Fast Dominance Algorithm", Rice University, 2001 — 실험 B의 반복법(초록: O(N²)이지만 실제로는 Lengauer–Tarjan보다 빠르다) <https://www.cs.tufts.edu/~nr/cs257/archive/keith-cooper/dom14.pdf>
  - Eclipse MAT 도움말 "Dominator Tree", "Shallow vs. Retained Heap", "Garbage Collection Roots" <https://help.eclipse.org/latest/topic/org.eclipse.mat.ui.help/concepts/dominatortree.html>
  - Eclipse MAT 소스 `plugins/org.eclipse.mat.parser/src/org/eclipse/mat/parser/internal/DominatorTree.java`(semi·bucket)
  - JDK 21 `jcmd` 매뉴얼(GC.class_histogram·GC.heap_dump Impact: High, VM.native_memory), `java` 매뉴얼(`HeapDumpOnOutOfMemoryError`, `HeapDumpPath`, `NativeMemoryTracking`, `MaxDirectMemorySize`), `ThreadLocal` API 문서
  - async-profiler v4.5 `docs/ProfilingModes.md` "Native memory leaks"(`nativemem`, `jfrconv --leak`)
- 실험 목록
  - A 무제한 캐시 누수: `Leak.java`, `-Xmx128m -Xlog:gc`(Serial GC 자동 선택), 5,000건마다 GC 후 사용 힙, 2·6단계 `jcmd GC.class_histogram`, 6단계 `GC.heap_dump`, OOM까지. JDK 21.0.12 temurin 컨테이너 `--cpus=2 --memory=512m`
  - B 지배자 트리: `Dominators.java`, 장난감 그래프(크기 예시)에서 Cooper–Harvey–Kennedy 반복 + 후위 합산으로 retained, 히스토그램과 비교
  - C 힙 밖 누수: `DirectLeak.java`, `-Xmx64m`, 16 MiB씩 direct buffer 보유. (A) `MaxDirectMemorySize=96m` + NMT summary → JVM OOM, (B) `MaxDirectMemorySize=1g` + 컨테이너 `--memory=256m` → `OOMKilled=true`, 137

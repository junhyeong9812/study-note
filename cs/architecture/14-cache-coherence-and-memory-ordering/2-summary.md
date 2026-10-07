# architecture/14-cache-coherence-and-memory-ordering — 캐시 일관성과 메모리 순서: MESI·저장 버퍼·배리어·CAS — 정리 (힌트)

## 해결하는 문제

코어마다 자기 캐시(L1·L2)와 자기 저장 버퍼가 있다. 그래서 두 가지가 저절로 맞지 않는다.

```text
           코어 0                         코어 1
   [레지스터] [저장 버퍼] [L1/L2]     [레지스터] [저장 버퍼] [L1/L2]
                     \                   /
                      [   공유 L3 · DRAM   ]

  문제 1 (일관성): 같은 주소 x의 사본이 코어 0 캐시와 코어 1 캐시에 따로 있다.
                  코어 0이 x를 바꾸면 코어 1의 사본은?
  문제 2 (순서):   코어 0이 "data를 쓰고 → flag를 쓴다". 코어 1은 flag를 먼저 보고 data는 옛 값을 볼 수 있나?
```

- *캐시 일관성(cache coherence)*: **한 주소**에 대해 모든 코어가 같은 쓰기 순서를 보게 하는 성질. 하드웨어 프로토콜(MESI 등)이 맡는다.
- *메모리 일관성 모델 / 메모리 순서(memory consistency model)*: **서로 다른 주소들**에 대한 읽기·쓰기가 다른 코어에 어떤 순서로 보일 수 있는지에 대한 규칙. CPU 아키텍처와 언어(JMM)가 각각 정한다.
  - 흔한 오해: "캐시가 일관되니까(MESI) 다른 스레드는 내가 쓴 순서대로 본다." 이 호스트에서 x86 저장 버퍼 때문에 "둘 다 상대의 쓰기를 못 본" 결과가 200만 번 중 최대 4905번 나왔다(아래 실험 1).

쉬운 예: 팀 공유 문서와 각자의 "보낼 편지함"이다.
- 공유 문서는 누가 고치면 다른 사람 화면의 사본이 즉시 "낡음"으로 표시된다(일관성).
- 그런데 나는 수정 사항을 바로 반영하지 않고 편지함에 넣어 두었다가 보낸다. 그 사이 남의 문서를 읽는다.
- 둘이 동시에 그러면, 둘 다 "상대는 아직 안 고쳤네"라고 본다.

똑같은 구조다.\
공유 문서의 낡음 표시 = MESI의 무효화, 보낼 편지함 = 저장 버퍼다.

실무에서 보이는 두 증상(⚠ 칸):
- 종료 플래그를 바꿨는데 작업 스레드가 영영 안 멈춘다(실험 2: 일반 `boolean` 10회 중 9회 안 멈춤).
- double-checked locking 싱글턴이 생성자가 덜 끝난 객체를 내준다(DCL 선언문).

## 동작·원리

### 1. MESI — 라인마다 상태 네 개

Drepper 2007 §3.3.4(그림 3.18)의 설명을 그림으로:

```text
  상태           뜻                                       이 코어가 써도 되나
  M Modified    내가 고쳤고, 사본은 나만 있다(메모리는 낡음)   예 (알릴 필요 없음)
  E Exclusive   안 고쳤고, 사본은 나만 있다                  예 (조용히 M으로)
  S Shared      안 고쳤고, 다른 코어에도 사본이 있을 수 있다  먼저 다른 사본을 무효화(RFO)
  I Invalid     쓸 수 없는 칸                               읽어 와야 한다

  주요 전이 (코어 0 기준)
   I ──로컬 읽기, 다른 사본 없음──> E ──로컬 쓰기(버스 알림 없음)──> M
   I ──로컬 읽기, 다른 사본 있음──> S ──로컬 쓰기 + RFO────────────> M   (다른 코어의 사본은 I)
   M ──다른 코어가 읽음──> 내용을 보내 주고 S
   M/E/S ──다른 코어가 쓰려 함(RFO)──> I
```

- *RFO(Request For Ownership)*: "이 라인을 쓰려 하니 다른 사본을 무효화하라"는 메시지. Drepper는 RFO가 필요한 두 경우로 스레드가 다른 코어로 옮겨 갈 때와 **라인이 정말로 두 코어에 필요할 때**를 든다.
- *스누핑(snooping)*: 다른 코어의 버스 동작을 엿들어 자기 라인 상태를 바꾸는 방식. 전이는 모든 코어가 응답할 기회를 가진 뒤에야 끝난다(Drepper §3.3.4).
- E 상태가 있는 이유: 혼자 가진 라인에 쓸 때 알림이 필요 없다. S → M은 RFO가 필요해서 E → M보다 훨씬 느리다.
- 12번의 false sharing은 바로 이 전이가 두 코어 사이에서 끝없이 반복되는 것이다. 원자적 증가마다 라인을 M으로 가져와야 한다.
- 실제 CPU는 MESI를 확장한 변형(MESIF·MOESI 등)을 쓴다고 알려져 있다 [?]. 이 CPU의 정확한 프로토콜은 공개 문서로 확인하지 못했다.

### 2. 일관성이 있어도 순서는 어긋난다 — 저장 버퍼

```text
  Store Buffering(SB) 리트머스 테스트   (x = y = 0)
     스레드 0           스레드 1
     x = 1              y = 1
     r0 = y             r1 = x
  순차적으로 끼워 넣으면 r0 == 0 && r1 == 0 은 불가능해 보인다 (누군가는 먼저 썼을 테니)

  x86에서 실제로 일어나는 일
   코어 0: x=1 → [저장 버퍼]에 대기     코어 1: y=1 → [저장 버퍼]에 대기
   코어 0: r0 = y → 캐시에서 0           코어 1: r1 = x → 캐시에서 0
   그 뒤에 두 저장 버퍼가 비워진다      → r0 == 0 && r1 == 0
```

- *저장 버퍼(store buffer)*: 쓰기가 캐시에 반영되기를 기다리지 않고 다음 명령을 실행하려고 쓰기를 잠시 담아 두는 FIFO. 자기 쓰기는 자기 저장 버퍼에서 읽을 수 있다.
- Sewell 외(CACM 2010) "x86-TSO"는 이 SB 결과를 최신 Intel·AMD x86에서 **허용되는 최종 상태**로 제시하고, 각 하드웨어 스레드에 FIFO 저장 버퍼가 있는 추상 기계로 설명한다. `MFENCE`는 그 스레드의 저장 버퍼를 비운다.
  - *TSO(Total Store Order)*: 쓰기끼리의 순서, 읽기끼리의 순서는 지키지만 "앞의 쓰기 → 뒤의 다른 주소 읽기" 순서만 어긋날 수 있는 모델. x86이 이것에 가깝다(JSR-133 Cookbook: 현재 x86 명세는 "nearly identical to TSO").

### 실험 1: SB 리트머스 (C, x86-64)

```c
// 스레드 0                                         // 스레드 1
atomic_store_explicit(&x, 1, memory_order_relaxed);  atomic_store_explicit(&y, 1, memory_order_relaxed);
FENCE;                                               FENCE;
r0 = atomic_load_explicit(&y, memory_order_relaxed); r1 = atomic_load_explicit(&x, memory_order_relaxed);
// FENCE = atomic_signal_fence(seq_cst) (컴파일러 재정렬만 막음) 또는 atomic_thread_fence(seq_cst)
```

- 매 회 x=y=0으로 되돌리고 두 스레드를 거의 동시에 출발시킨다. 200만 회 중 `r0==0 && r1==0` 횟수를 센다.
- gcc 13.3.0 `-O2`는 `atomic_thread_fence(seq_cst)`를 `lock orq $0x0,(%rsp)`로 냈다(`objdump`). 잠금 명령은 x86에서 완전 배리어로 쓰인다(Cookbook 표: x86 StoreLoad = "mfence or cpuid or locked insn").

```text
  (각 실행 200만 회)                         r0==0 && r1==0
  다른 P코어 cpu2·cpu4, 컴파일러 펜스만         9 ~ 4905 회  (15번 실행)
  다른 P코어 cpu2·cpu4, seq_cst 펜스(lock or)   0 회        (8번 실행)
  같은 코어의 두 하드웨어 스레드 cpu2·cpu3       0 회        (3번 실행, 컴파일러 펜스만)
```

- 컴파일러 재정렬을 막았는데도 일어났다. **하드웨어(저장 버퍼)가 만든 재정렬**이다.
- 빈도는 실행마다 수백 배 달랐다. 드물고 들쭉날쭉한 것이 이런 버그를 테스트로 잡기 어려운 이유다.
- 같은 코어의 하드웨어 스레드 쌍에서 0회였던 것은 관찰일 뿐 보장으로 읽지 않는다.

### 3. 배리어 — 어긋남을 막는 명령

```text
  JSR-133 Cookbook의 네 종류: "앞 X가 뒤 Y보다 먼저 보이게"
  LoadLoad    읽기 → 읽기
  LoadStore   읽기 → 쓰기
  StoreStore  쓰기 → 쓰기
  StoreLoad   쓰기 → 읽기   ← 가장 비싸다. 저장 버퍼를 비워야 할 수 있다

  아키텍처별 (Cookbook 표)
              LoadLoad  LoadStore  StoreStore  StoreLoad                 CAS
  x86         no-op     no-op      no-op       mfence / locked 명령       lock cmpxchg
  arm (v7+)   dmb       dmb        dmb-st      dmb                       ldrex/strex (LL/SC)
```

- x86(TSO)에서는 일반 프로그램 메모리(write-back 캐시 모드) 기준으로 네 가지 중 StoreLoad만 실제 명령이 필요하다. 그래서 x86에서 "잘 돌던" 코드가 ARM에서 깨질 수 있다. ARM은 나머지 순서도 보장하지 않는다.
  - 예외(Cookbook 표 아래 Notes): write-combining 모드에서는 StoreStore에 `sfence`, SSE2 streaming 명령에는 LoadLoad에 `lfence`가 필요하다.
- Cookbook의 ARM 행은 v7 기준이다("Version 7+", 문서 마지막 수정 2011). ARMv8(AArch64)의 `ldar`·`stlr` 같은 획득·해제 명령은 이 표에 없다.
- 같은 호스트에서 C11 원자 연산이 어떤 명령이 되는지(`gcc -O2`, `objdump -d`):

```text
  atomic_store(release)      →  mov    %rdi, v          (x86에서는 그냥 저장)
  atomic_store(seq_cst)      →  xchg   %rdi, v          (잠금 의미가 있는 교환 = StoreLoad 포함)
  atomic_load(acquire)       →  mov    v, %rax
  atomic_fetch_add           →  lock xadd %rax, v
  atomic_compare_exchange    →  lock cmpxchg %rsi, v
```

### 4. 컴파일러도 순서를 바꾼다 — JIT가 루프 밖으로 읽기를 뺀다

```text
  소스                          JIT가 해도 되는 변환 (JLS 17.3이 비슷한 예를 든다)
  while (running) { n++; }  →   if (running) { while (true) { n++; } }
                                "running을 한 번만 읽고 재사용" → 다른 스레드가 false로 바꿔도 영영 못 본다
```

- JLS SE21 §17.3: `this.done`이 `volatile`이 아니면 `while (!this.done) Thread.sleep(1000);`에서 컴파일러가 필드를 한 번만 읽어 재사용해도 되고, 그러면 루프가 끝나지 않을 수 있다고 적는다. `Thread.sleep`·`yield`에는 동기화 의미가 없다.
- 이것은 하드웨어 캐시 문제가 아니다. 값이 **레지스터**에 머문다. 코어 캐시는 MESI로 일관되다(Drepper §3.3.3: 일관성은 사용자 수준 코드에 투명해야 한다).
  - 흔한 오해: "`volatile`은 캐시를 메인 메모리로 플러시한다." JSR-133 FAQ도 이렇게 비유하지만, x86에서 HotSpot이 실제로 넣는 것은 캐시 플러시가 아니라 잠금 명령(`lock addl`, 아래 5절)이다. `volatile`이 하는 일은 컴파일러 최적화와 재정렬을 제한하고 필요한 배리어를 넣는 것이다.

### 실험 2: 종료 플래그 (Java 21)

```java
static boolean plain = true;            // 일반 필드
static volatile boolean vol = true;     // volatile 필드
Thread t = new Thread(() -> { long n = 0; while (plain) n++; });
t.setDaemon(true); t.start(); Thread.sleep(300); plain = false; t.join(1000);   // 1초 안에 끝났나
```

`eclipse-temurin:21-jdk`(21.0.12), `--cpus=2 --cpuset-cpus=2,4`, 한 번 실행에 각 5회, 2번 실행(2번째는 사실 점검 재실행):

```text
  1번째 실행
  일반 boolean    : 안끝남 안끝남 안끝남 안끝남 안끝남
  volatile boolean: 끝남   끝남   끝남   끝남   끝남
  2번째 실행
  일반 boolean    : 끝남   안끝남 안끝남 안끝남 안끝남
  volatile boolean: 끝남   끝남   끝남   끝남   끝남
```

- 같은 실험의 `-Xint`(인터프리터) 비교와 JDK 17·21·25 결과는 [languages/java/syntax/33](../../../languages/java/syntax/33-synchronized-and-volatile/2-summary.md) (3)에 있다. 거기서는 `-Xint`면 일반 필드도 멈췄다. 최적화가 원인이라는 증거다.
- 2번째 실행의 첫 회는 일반 필드인데도 멈췄다. 루프가 아직 JIT 컴파일되기 전(인터프리터)이었다는 해석이다.
- **관찰이지 보장이 아니다.** JMM은 "안 멈춰도 된다"고 허용할 뿐, 반드시 안 멈춘다고 하지 않는다.

### 5. JMM — 언어가 약속하는 순서 (happens-before)

```text
  스레드 A                              스레드 B
  data = 42;                            
  ready = true;   (volatile 쓰기) ──synchronizes-with──> if (ready)   (같은 변수 volatile 읽기, 그 쓰기를 봄)
                                         r = data;     → 42가 보장된다

  happens-before = 프로그램 순서 + synchronizes-with 를 이어 붙인 것 (+ 생성자 끝 → finalizer 간선, §17.4.5)
```

- JLS SE21 §17.4.4: volatile 변수 v에 대한 쓰기는 이후의 모든 v 읽기와 synchronizes-with다. 모니터 해제는 같은 모니터의 이후 획득과 synchronizes-with다. 스레드 시작·종료 감지(`join`)도 포함된다.
- §17.4.5 happens-before 순서로 정렬되지 않은 충돌 접근이 data race다. §17.4 예제 17.4-1은 컴파일러가 한 스레드 안의 독립 문장을 바꿔도 되기 때문에 `r2 == 2 && r1 == 1` 같은 "불가능해 보이는" 결과가 나올 수 있음을 보인다.
- **표준 요구 vs 구현**: JMM은 결과만 정한다. HotSpot은 x86에서 필요한 StoreLoad를 `lock add [esp-C], 0`으로 구현한다(OpenJDK 21 `src/hotspot/cpu/x86/assembler_x86.cpp` `Assembler::membar` 주석: "We only have to handle StoreLoad", locked 명령이 cpuid보다 훨씬 빠르다). 다른 세 배리어는 x86에서 명령이 필요 없다(Cookbook 표와 일치).

### 6. CAS — 일관성 위에 세운 원자적 갱신

```text
  CAS(addr, expected, new):  [addr == expected] ? (addr = new, 성공) : 실패      — 한 덩어리로
  x86:  lock cmpxchg  — 라인을 M 상태로 잡은 채 비교·교체를 끝낸다 (그동안 다른 코어는 이 라인을 못 가져감)

  재시도 루프
   do { old = load(c); } while (!CAS(c, old, old + 1));
```

- *CAS(compare-and-swap)*: 값이 기대값과 같을 때만 새 값으로 바꾸는 원자 명령. 락·락 없는 자료구조의 재료다. 자세한 쓰임은 [os/16-locks-and-spinlocks](../../os/16-locks-and-spinlocks/2-summary.md)·[data-structure/29-concurrent-data-structures](../../data-structure/29-concurrent-data-structures/2-summary.md).
- 원자 명령도 라인 소유권(RFO)을 거친다. 여러 코어가 같은 라인에 CAS를 하면 라인이 오가며 느려진다(12번 실험 3: 같은 라인 원자적 증가 3~5배).

### 실험 3: 갱신 유실 (Java 21)

스레드 2개가 각 1천만 번 증가, 기대값 20,000,000, 한 번 실행에 3회, 2번 실행(2번째는 사실 점검 재실행):

```text
  volatile int++   17,905,111 / 19,578,627 / 18,178,681 | 15,928,396 / 18,009,539 / 17,904,710   ← 유실
  AtomicInteger    20,000,000 (6회 모두)
  LongAdder        20,000,000 (6회 모두)
  int++(일반)       20,000,000 ×3 | 19,995,088 / 20,000,000 / 20,000,000   ← 유실이 날 때도, 안 날 때도 있다
```

- `volatile`은 읽기·쓰기 각각이 보이게 할 뿐, `읽기 → 더하기 → 쓰기` 세 단계를 한 덩어리로 묶지 않는다.
- 일반 `int++`은 6회 중 5회 맞게 나왔고, 재실행 첫 회(JIT 전, 41ms)에 4,912개가 유실됐다. 나머지가 맞은 것은 JIT가 루프를 통째로 최적화해 두 스레드가 거의 겹치지 않았기 때문이라는 해석이다(최적화 뒤 6~7ms). 같은 현상과 그 분석이 [languages/java/syntax/33](../../../languages/java/syntax/33-synchronized-and-volatile/2-summary.md) (1)에 있다.
- `AtomicInteger.incrementAndGet`·`LongAdder`는 원자 명령으로 유실이 없었다.

### 7. DCL — 재정렬로 반쯤 만들어진 객체가 보인다

```java
private static Singleton instance;                 // volatile 없음
public static Singleton get() {
    if (instance == null) {                          // ① 락 없이 확인
        synchronized (Singleton.class) {
            if (instance == null) instance = new Singleton();   // ②
        }
    }
    return instance;
}
```

`javac`·`javap -c`(JDK 21)로 본 ②:

```text
  17: new           #8   // class Singleton       ← 메모리 할당 (필드는 기본값 0)
  20: dup
  21: invokespecial #17  // Method "<init>":()V   ← 생성자: port = 8080
  24: putstatic     #13  // Field instance        ← 참조 공개
```

```text
  바이트코드 순서는 할당 → 생성자 → 공개다. 하지만
  스레드 A (락 안)                               스레드 B (① 락 없이 읽음)
  할당
  instance = 참조     ← 공개가 생성자 쓰기보다 먼저 보이면
                                                  instance != null → 락 없이 반환
                                                  b.port 읽기 → 0 (생성자가 아직)
  port = 8080
```

- DCL 선언문("The 'Double-Checked Locking is Broken' Declaration", Bacon·Bloch·Lea·Pugh 외 서명): 생성자 안의 쓰기와 참조 공개를 컴파일러가 바꿀 수 있고, 바꾸지 않아도 멀티프로세서에서는 프로세서·메모리 시스템이 바꿀 수 있다. 실제 Symantec JIT가 그렇게 컴파일한 예를 든다.
- 고치는 법(같은 선언문 "Under the new Java Memory Model"): JDK5 이후에는 `instance`를 `volatile`로 선언하면 동작한다. JDK4 이하에서는 안 된다. 모든 필드가 `final`인 불변 객체라면 `volatile` 없이도 된다(선언문 "Double-Checked Locking Immutable Objects", JLS §17.5 final 필드 의미). 단 락 밖에서 `instance`를 **한 번만 읽어 지역 변수로 반환**해야 한다. 위 코드처럼 ①과 `return`에서 두 번 읽으면, 두 경쟁 읽기는 JMM상 따로 값을 고를 수 있어 ①이 참조를 봐도 `return`이 초기값 `null`을 볼 수 있다(JLS §17.4.4 기본값 쓰기·§17.4.5 happens-before 일관성).
- **이 호스트에서는 재현하지 못했다(시도하지 않음).** x86(TSO)은 쓰기끼리의 순서를 하드웨어가 바꾸지 않아, 남는 것은 컴파일러 재정렬뿐이다. 실패 증거는 위 선언문과 JLS로 대신한다. ARM 같은 약한 순서 CPU에서는 하드웨어도 바꿀 수 있다(Cookbook 표).

## 쓰이는 자료구조·알고리즘

- **MESI 상태 기계**(🔧): 라인마다 4상태, 로컬·원격 읽기/쓰기 이벤트로 전이하는 유한 상태 기계. 순차 논리·FSM은 [08-sequential-logic-clock](../08-sequential-logic-clock/2-summary.md)(원고 [foundations/hardware-basics](../../foundations/hardware-basics/README.md)).
- **CAS**(🔧): 재시도 루프, lock-free 스택·큐, ABA 문제. [os/16-locks-and-spinlocks](../../os/16-locks-and-spinlocks/2-summary.md) · [data-structure/29-concurrent-data-structures](../../data-structure/29-concurrent-data-structures/2-summary.md)
- **release/acquire로 만든 SPSC 링 버퍼**: 락 없이 순서만으로 생산자·소비자를 잇는다. [data-structure/25-ring-buffer](../../data-structure/25-ring-buffer/2-summary.md)
- **happens-before = 부분 순서**: 프로그램 순서와 synchronizes-with(+ 생성자 끝 → finalizer 시작 간선, JLS §17.4.5)의 추이적 폐포. [math/03-sets-relations-orders](../../math/03-sets-relations-orders/2-summary.md) · 분산판 [distributed/05-logical-clocks](../../distributed/05-logical-clocks/2-summary.md) · [distributed/07-consistency-models](../../distributed/07-consistency-models/2-summary.md)

## 적용 — 풀어나가는 법

1. **증상 → 공유 변수 찾기.** "가끔", "부하 때만", "ARM 서버에서만" 틀리면 스레드 사이에 공유되는 가변 상태를 먼저 의심한다.
2. **그 변수의 모든 읽기·쓰기 쌍에 happens-before가 있는지 확인한다.** 같은 락, `volatile`, `Atomic*`, `Thread.start`·`join`, `java.util.concurrent` 도구 중 하나가 있어야 한다. `final` 필드는 happens-before 간선을 만들지 않고 별도의 final 필드 의미론(JLS §17.5)으로 생성자가 쓴 값을 보장한다.
3. **도구로 본다.**

```bash
jcmd <pid> Thread.print | grep -A5 '"worker'     # 멈춰야 할 스레드가 RUNNABLE로 같은 줄에서 돌고 있나
```

   - 종료 플래그 무한 루프는 `RUNNABLE` 상태, 락 대기 없음, CPU 한 개 100%로 보인다.
4. **고친다 — 목적에 맞는 가장 단순한 도구.**

```java
// 종료 플래그: 한 스레드가 쓰고 다른 스레드가 읽기만 → volatile
private volatile boolean running = true;

// 카운터: 읽고-고치고-쓰기 → 원자 연산 (경합이 심하면 LongAdder)
private final AtomicLong count = new AtomicLong();

// 지연 초기화 싱글턴: 홀더 클래스 (클래스 초기화가 스레드 안전 — JLS 12.4.2의 초기화 락 LC)
private static final class Holder { static final Service INSTANCE = new Service(); }
public static Service get() { return Holder.INSTANCE; }

// 꼭 DCL이라면 volatile (JDK5+)
private static volatile Service instance;
```

5. **테스트로 "안 깨짐"을 증명할 수 없다.** 실험 1처럼 200만 번 중 9번일 수도 있다. 동시성 스트레스 도구(OpenJDK jcstress <https://github.com/openjdk/jcstress>)나 ARM 기계에서의 실행으로 보강하고, 무엇보다 코드 리뷰에서 2번의 확인을 한다.

## 장애 시나리오와 대처

### 1. graceful shutdown이 끝나지 않는다 — 종료 플래그 무한 루프

- **현상**: 배포 때 이전 인스턴스가 종료 신호를 받고도 안 내려가 강제 종료(SIGKILL)된다.
- **보이는 형태**: 종료 대기 시간 초과 로그, 쿠버네티스 `terminationGracePeriodSeconds` 만료. 스레드 덤프에서 워커가 `RUNNABLE`로 같은 루프에, CPU 한 코어 100%.
- **원인**: `while (running)`의 `running`이 일반 필드다. JIT가 읽기를 루프 밖으로 빼 값이 레지스터에 고정됐다(JLS §17.3, 실험 2에서 10회 중 9회 안 멈춤).
- **대처**: `volatile` 또는 `AtomicBoolean`, 또는 인터럽트(`Thread.interrupt` + `isInterrupted`) 기반으로 바꾼다. [reliability/14-graceful-shutdown](../../reliability/14-graceful-shutdown/2-summary.md)

### 2. 싱글턴이 가끔 설정값 0·null을 내준다 — DCL

- **현상**: 기동 직후 드물게 포트 0, 설정 `null`로 동작하는 요청이 생긴다. 재현이 안 된다.
- **보이는 형태**: 드문 `NullPointerException`, 기본값으로 동작한 흔적. 특정 CPU(ARM)·특정 JIT 상태에서만.
- **원인**: `volatile` 없는 DCL에서 참조 공개가 생성자 안 쓰기보다 먼저 보였다(DCL 선언문).
- **대처**: 홀더 클래스 관용구, `enum` 싱글턴, `volatile` DCL, 또는 필드를 전부 `final`로 한 불변 객체(락 밖 읽기는 지역 변수로 한 번만).

### 3. 통계 수치가 조금씩 모자란다 — `volatile` 카운터

- **현상**: 처리 건수 카운터가 로그 건수보다 몇 % 적다.
- **보이는 형태**: 부하가 클수록 차이가 커진다. 예외는 없다.
- **원인**: `volatile int++`은 원자적이지 않다. 두 스레드가 같은 값을 읽고 같은 값을 쓴다(실험 3: 2천만 중 42만~407만 유실).
- **대처**: `AtomicLong`·`LongAdder`, 또는 락. [os/15-race-conditions](../../os/15-race-conditions/2-summary.md)

### 4. x86에서 통과, ARM에서 실패

- **현상**: 같은 코드가 x86 서버·개발 PC에서는 문제없고, ARM 인스턴스(Graviton 등)·Apple Silicon에서 간헐적으로 틀린다.
- **보이는 형태**: 아키텍처별로 테스트 결과가 다르다. 락 없이 플래그 + 데이터를 주고받는 코드에서 옛 데이터를 본다.
- **원인**: x86은 TSO라 LoadLoad·LoadStore·StoreStore 재정렬을 하드웨어가 하지 않는다. ARM은 한다(Cookbook 표에서 x86은 no-op, ARM은 `dmb`). data race가 있는 코드가 x86에서는 우연히 맞았다.
- **대처**: happens-before를 언어 수준에서 만든다(`volatile`·락·`Atomic*`). CI에 ARM 실행을 넣는다. 아키텍처 차이는 [09-isa-and-machine-code](../09-isa-and-machine-code/2-summary.md).

## 핵심 문장

- 캐시 일관성(MESI)은 한 주소의 사본들을 맞춘다. 서로 다른 주소들 사이의 순서는 메모리 모델이 따로 정한다.
- MESI는 라인마다 M·E·S·I 상태를 두고, 쓰기 전에 RFO로 다른 사본을 무효화한다. false sharing과 경합 CAS가 느린 이유가 이 전이의 반복이다.
- x86(TSO)에서도 저장 버퍼 때문에 "쓰기 → 다른 주소 읽기" 순서가 어긋난다. 이 호스트에서 SB 테스트 200만 회 중 9~4905회, 펜스를 넣으면 0회였다.
- 컴파일러·JIT도 순서를 바꾼다. 일반 필드 종료 플래그는 레지스터에 고정돼 영영 안 보일 수 있다(JLS §17.3).
- Java에서는 `volatile`·락·`Atomic*`로 happens-before를 만들거나 `final` 필드 의미론(JLS §17.5)에 기대야 보장된다. HotSpot은 x86에서 StoreLoad만 잠금 명령으로 구현한다.
- `volatile`은 가시성과 순서를 주지만 `++` 같은 읽고-고치고-쓰기를 원자적으로 만들지 않는다. 그것은 CAS(`lock cmpxchg`)·원자 연산의 몫이다.

## 관련 주제·근거

- 선행: [12-cache-organization](../12-cache-organization/2-summary.md)(라인·write-back·false sharing) · [11-memory-hierarchy-and-locality](../11-memory-hierarchy-and-locality/2-summary.md)
- 후속·연결
  - [20-multicore-and-numa](../20-multicore-and-numa/2-summary.md) · [19-out-of-order-and-speculation](../19-out-of-order-and-speculation/2-summary.md)
  - [os/15-race-conditions](../../os/15-race-conditions/2-summary.md) · [os/16-locks-and-spinlocks](../../os/16-locks-and-spinlocks/2-summary.md) · [os/20-concurrency-bugs](../../os/20-concurrency-bugs/2-summary.md)
  - language "언어 메모리 모델"([language/13-language-memory-model](../../language/13-language-memory-model/2-summary.md)) · [languages/java/syntax/33-synchronized-and-volatile](../../../languages/java/syntax/33-synchronized-and-volatile/2-summary.md)
  - [data-structure/25-ring-buffer](../../data-structure/25-ring-buffer/2-summary.md) · [data-structure/29-concurrent-data-structures](../../data-structure/29-concurrent-data-structures/2-summary.md)
  - [distributed/07-consistency-models](../../distributed/07-consistency-models/2-summary.md) — 같은 질문의 분산판
  - [reliability/14-graceful-shutdown](../../reliability/14-graceful-shutdown/2-summary.md)
- 문서·논문·소스
  - Drepper 2007 §3.3.3 Write Behavior(일관성은 사용자 코드에 투명), §3.3.4 Multi-Processor Support(MESI 4상태, 그림 3.18 전이, RFO, 스누핑), §6.4.1·§6.4.2(false sharing, 원자 연산) <https://people.freebsd.org/~lstewart/articles/cpumemory.pdf>
  - P. Sewell, S. Sarkar, S. Owens, F. Zappa Nardelli, M. O. Myreen, "x86-TSO: A Rigorous and Usable Programmer's Model for x86 Multiprocessors", CACM Research Highlights 2010 — SB 예와 허용 최종 상태, FIFO 저장 버퍼 추상 기계, MFENCE <https://www.cl.cam.ac.uk/~pes20/weakmemory/cacm.pdf>
  - D. Lea, "The JSR-133 Cookbook for Compiler Writers" — 네 배리어, StoreLoad 비용, 프로세서별 표(x86 = TSO에 가까움, StoreLoad = mfence/locked 명령, CAS = cmpxchg / ARM = dmb, ldrex/strex) <https://gee.cs.oswego.edu/dl/jmm/cookbook.html>
  - J. Manson, B. Goetz, "JSR 133 (Java Memory Model) FAQ", 2004 — "What does volatile do?" <https://www.cs.umd.edu/~pugh/java/memoryModel/jsr-133-faq.html>
  - "The 'Double-Checked Locking is Broken' Declaration" — 재정렬 원인, Symantec JIT 예, JDK5+ volatile 해법, 불변 객체 <https://www.cs.umd.edu/~pugh/java/memoryModel/DoubleCheckedLocking.html>
  - JLS SE21 17장 — §17.3 Sleep and Yield(`this.done` 예), §17.4 예제 17.4-1(표 17.4-A·B), §17.4.4 Synchronization Order(synchronizes-with 목록), §17.4.5 Happens-before Order, §17.5 final Field Semantics <https://docs.oracle.com/javase/specs/jls/se21/html/jls-17.html>
  - OpenJDK 21 `src/hotspot/cpu/x86/assembler_x86.cpp` `Assembler::membar`(StoreLoad만 처리, locked add) <https://github.com/openjdk/jdk21u>
  - D. Sorin, M. Hill, D. Wood, 『A Primer on Memory Consistency and Cache Coherence』 [?] (열지 못함 — 커리큘럼 📚 칸)
  - CS:APP 3판 목차 확인 결과: 12.4.1 "Threads Memory Model", 12.5 "Synchronizing Threads with Semaphores"(커리큘럼의 "CS:APP 12.5"는 세마포어 절이며 MESI·재정렬을 다루는 절이 아니다 — 목차 기준)
- 실험 목록(환경: i7-13700HX, Linux 7.0.0-34, gcc 13.3.0 `-O2 -pthread`, JDK 21.0.12 컨테이너 `--network none --cpus=2 --cpuset-cpus=2,4`)
  - 실험 1 `sb.c`: SB 리트머스 200만 회, 컴파일러 펜스 vs seq_cst 펜스(`lock orq`), cpu2·4(15+8회)·cpu2·3(3회) — 각 4·2·1회는 사실 점검 재실행
  - 실험 2 `Visibility.java` (1): 일반 vs `volatile` 종료 플래그, 각 5회 × 2번 실행, 1초 대기
  - 실험 3 `Visibility.java` (2): `int++`·`volatile int++`·`AtomicInteger`·`LongAdder`, 2스레드 × 1천만, 3회 × 2번 실행
  - `atom.c` + `objdump -d`: C11 원자 연산의 x86 명령 / `dcl/Singleton.java` + `javap -c`: DCL 바이트코드
  - DCL 실패는 재현하지 않음(문서 근거)

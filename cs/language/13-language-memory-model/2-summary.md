# language/13-language-memory-model — 언어 메모리 모델: happens-before·data race·volatile·final — 정리 (힌트)

## 해결하는 문제

두 스레드가 같은 변수를 쓰고 읽을 때 "읽는 쪽이 무엇을 볼 수 있나"를 정하지 않으면, 코드만 보고 동작을 말할 수 없다.

```text
  스레드 A              스레드 B
  x = 1;                y = 1;
  r1 = y;               r2 = x;
  → 둘 다 0을 읽는 (r1, r2) = (0, 0)이 나올 수 있나?
    "한 줄씩 번갈아 실행"만 생각하면 불가능해 보인다. 실제로는 나온다(아래 실험 1: 2백만 번 중 15만~26만 번).
```

- 순서를 바꾸는 주체가 셋이다: 컴파일러(javac는 거의 안 바꾸지만 JIT·C 컴파일러는 바꾼다), CPU(저장 버퍼 — [architecture/14](../../architecture/14-cache-coherence-and-memory-ordering/2-summary.md)), 그리고 둘의 조합.
- *언어 메모리 모델*: 이 모든 재정렬 위에서 "프로그램이 어떤 결과를 낼 수 있는지"를 언어 차원에서 정한 계약. 프로그래머는 하드웨어 대신 이 계약을 보고 코드를 쓴다.

쉬운 예: 단체 대화방 메시지 순서다.
- 내 화면에서 A가 "회의 취소"를 보낸 뒤 "장소 변경"을 보냈어도, 다른 사람 화면에는 순서가 바뀌거나 하나가 늦게 보일 수 있다.
- "공지(고정 메시지)"로 올린 것은 모두에게 순서대로 보인다고 약속하면, 중요한 것만 공지로 올리면 된다.

똑같은 구조다. 공지 = `volatile`·락 같은 동기화다.\
실무 예:
- graceful shutdown의 `running = false`를 워커 스레드가 영영 못 본다([architecture/14 장애 1](../../architecture/14-cache-coherence-and-memory-ordering/2-summary.md)).
- DCL 싱글턴이 가끔 필드가 0·`null`인 객체를 내준다.
- C 서버에서 `-O0`로는 되던 대기 루프가 `-O2` 빌드에서 무한 루프가 된다(아래 실험 2).

## 동작·원리

### 1. 층 나누기 — 이 노트가 다루는 자리

```text
  [ 언어 계약 ]   JLS 17.4 (Java) · C11 5.1.2.4 · C++ · Go memory model   ← 이 노트
        ↑ 구현이 지켜야 한다
  [ 컴파일러 ]    JIT·gcc·clang: 계약이 허용하는 범위에서 재정렬·레지스터 캐싱
  [ 하드웨어 ]    저장 버퍼·캐시 일관성(MESI)·배리어 명령                     ← architecture/14
```

- 하드웨어 쪽(MESI, 저장 버퍼, x86 `lock` 명령, C로 짠 SB 리트머스)은 [architecture/14](../../architecture/14-cache-coherence-and-memory-ordering/2-summary.md)에 실험과 함께 있다. 같은 노트에 Java 종료 플래그·`volatile int++` 유실·DCL 바이트코드 분석도 있다. 여기서는 되풀이하지 않고 **언어 계약 쪽**을 본다.

### 2. happens-before — 누가 누구를 "보는 게 보장"되나

```text
  스레드 A                                스레드 B
  data = 42;          ─┐ 프로그램 순서
  ready = true;  (volatile 쓰기) ──synchronizes-with──>  if (ready)  (같은 변수 volatile 읽기, 그 쓰기를 봄)
                                                    │ 프로그램 순서
                                                    └> r = data;   → 42가 보장된다 (hb 간선을 따라 이어짐)

  synchronizes-with 간선의 종류 (JLS 17.4.4)
   · 모니터 unlock  → 같은 모니터의 이후 lock
   · volatile 변수 쓰기 → 그 변수의 이후 읽기
   · Thread.start() → 시작된 스레드의 첫 동작
   · 스레드의 마지막 동작 → 다른 스레드가 그 종료를 감지(join·isAlive)
   · 기본값(0·false·null) 쓰기 → 모든 스레드의 첫 동작
   · interrupt → 인터럽트 감지
```

- *happens-before(hb)*: JLS 17.4.5. 같은 스레드의 프로그램 순서, synchronizes-with 간선, 그리고 이들의 **추이적 폐포**. `hb(x, y)`면 x의 결과가 y에 보이고 순서도 앞선다.
  - 흔한 오해: "hb면 실제로 그 순서로 실행된다." JLS 17.4.5: 결과가 합법적 실행과 같다면 구현이 순서를 바꿔도 된다. hb는 실행 순서가 아니라 **보임의 약속**이다.
- *data race*: 같은 변수에 대한 충돌 접근(적어도 하나가 쓰기) 두 개가 hb로 정렬되지 않은 것(JLS 17.4.5).
- *올바르게 동기화된 프로그램*: 순차 일관 실행 어디에도 data race가 없는 프로그램. 그러면 모든 실행이 순차 일관적으로 보인다(JLS 17.4.5 — "an extremely strong guarantee for programmers"). 이것을 흔히 **DRF-SC**(data-race-free ⇒ sequentially consistent)라고 부른다(Manson·Pugh·Adve POPL 2005 초록: "it guarantees sequential consistency to data-race-free programs").
  - *순차 일관성(sequential consistency)*: 모든 스레드의 동작이 하나의 전체 순서로 끼워 넣어진 것처럼 보이는 것. 위 SB 예에서 (0, 0)이 불가능한 세계.

### 3. race가 있을 때 — Java와 C의 갈림

| | Java (JLS 17) | C11 (N1570) |
|---|---|---|
| data race의 정의 | hb로 정렬 안 된 충돌 접근 | 다른 스레드의 충돌 동작, 하나 이상이 비원자적, 서로 hb 아님 (5.1.2.4 ¶25) |
| race가 있으면 | 여전히 정의된 의미가 있다(이상한 값은 볼 수 있음) | **정의되지 않은 동작(UB)** — "Any such data race results in undefined behavior" |
| 이유 | 안전·보안: 틀린 코드도 배열 길이를 잘못 돌려주는 등 타입 안전을 깨지 않아야 한다(JLS 17.4.5, POPL 2005) | 단일 스레드 최적화를 거의 다 허용하기 위해(5.1.2.4 ¶26 NOTE 12) |

- JLS 17.4.5: "a data race cannot cause incorrect behavior such as returning the wrong length for an array."
- POPL 2005 Figure 2 "An Out Of Thin Air Result": `r1 = x; y = r1;` ∥ `r2 = y; x = r2;`에서 `r1 == r2 == 42`가 나오면 안 된다. 값이 허공에서 생기는 것을 막는 것이 JMM 인과성 규칙(17.4.8)의 목적이다.
- C에서 race는 "이상한 값"이 아니라 **프로그램 전체가 무엇이든 해도 되는** 상태다. 실험 2의 무한 루프가 그 예다.

### 4. 접근 모드의 사다리 — Java `VarHandle`

```text
  약함 ─────────────────────────────────────────────────────────> 강함
  plain           opaque              acquire/release          volatile
  (일반 필드)      같은 변수 안에서만      release 쓰기 앞의 접근은       모든 volatile 동작이
  순서 약속 없음    일관된 순서           acquire 읽기 뒤에 보인다       하나의 전체 순서
                                       (메시지 전달 OK)             (+ 저장 후 읽기 순서까지)
```

- Java API `VarHandle` 클래스 설명의 접근 모드 부분("Access modes control atomicity and consistency properties"): plain은 다른 스레드에 대해 순서 제약이 없고, opaque는 같은 변수 접근끼리 일관되게 정렬되며, acquire 읽기와 그 뒤 접근은 짝이 맞는 release 쓰기와 그 앞 접근 뒤에 정렬되고, volatile 동작은 서로 전체 순서를 이룬다.
- 메시지 전달(위 2절 `data`·`ready`)은 release/acquire로 충분하다. 그런데 **"내가 쓰고 나서 상대 변수를 읽는다"**(SB 패턴, Dekker류 상호 배제)는 release/acquire로 막히지 않는다. 저장 → 읽기 순서는 volatile(또는 전체 펜스)만 약속한다. 실험 1이 이것을 보여 준다.

### 실험 1: SB 리트머스 — 접근 모드별로 (0, 0)이 나오나 (Java 21)

```java
// T1: x = 1; r1 = y      T2: y = 1; r2 = x      — 2백만 회, 회마다 새 Cell, 두 스레드가 volatile 카운터로 보조를 맞춘다
case "plain"    -> { c.x = 1; r1[i] = c.y; }
case "volatile" -> { c.vx = 1; r1[i] = c.vy; }
case "acqrel"   -> { X.setRelease(c, 1); r1[i] = (int) Y.getAcquire(c); }
case "opaque"   -> { X.setOpaque(c, 1);  r1[i] = (int) Y.getOpaque(c); }
case "fence"    -> { X.setRelease(c, 1); VarHandle.fullFence(); r1[i] = (int) Y.getAcquire(c); }
```

`eclipse-temurin:21-jdk`(21.0.12), 호스트 x86-64(i7-13700HX), `--cpus=2`, 3회 + 사실 점검 재실행 2회(`|` 뒤):

```text
  모드        (0,0)                                       (0,1)/(1,0)/(1,1)은 생략 — 합 2,000,000
  plain      210,209 / 207,429 / 150,683 | 264,441 / 225,785
  volatile         0 /       0 /       0 |       0 /       0
  acqrel     354,723 / 197,998 / 325,782 | 212,295 / 117,611     ← release/acquire로는 막히지 않는다
  opaque     199,860 / 158,671 / 152,516 | 124,715 / 180,839
  fence            0 /       0 /       0 |       0 /       0     ← 저장과 읽기 사이 전체 펜스
  (-Xint로 plain 20만 회: 27,772 | 24,164)
```

- volatile은 5회 모두 0이었다. JMM이 volatile 동작에 전체 순서를 약속하므로 (0, 0)은 금지다. 실험은 그 금지를 깨지 않았다는 관찰이다.
- acquire/release와 opaque는 (0, 0)을 허용하고, 실제로 6~18% 나왔다. "volatile 대신 acquire/release면 같은 효과에 더 싸다"는 SB 패턴에서는 틀리다.
- `-Xint`(인터프리터, JIT 없음)에서도 plain이 (0, 0)을 냈다. 두 스레드의 문장을 어떤 순서로 끼워 넣어도 (0, 0)은 안 나오고, 바이트코드도 저장(`putfield`) → 읽기(`getfield`) 순서 그대로이니(`javap -c`, 판정 때 확인), `-Xint` 실행의 (0, 0)은 **CPU 저장 버퍼**가 원인이라는 해석이다. JIT 실행의 (0, 0)에 컴파일러 재정렬이 섞였는지는 이 실험으로 가르지 못했다(x86에서 허용되는 유일한 재정렬이 저장 → 읽기다 — [architecture/14 §2](../../architecture/14-cache-coherence-and-memory-ordering/2-summary.md)).
- 0이 아닌 값은 "나올 수 있다"의 증거지만, 0이라는 결과는 이 실행에서의 관찰일 뿐이다. 금지 근거는 명세다.

### 5. final 필드 — 불변 객체는 race로 넘겨도 안전하다

```text
  생성자 안에서 final 필드 설정 → 생성자 끝 ("freeze")
  그 뒤에 참조를 공개하면, 다른 스레드는 race로 참조를 받아도 final 필드의 올바른 값을 본다
  단, 생성자 안에서 this를 밖으로 흘리면(리스너 등록 등) 약속이 깨진다
```

- JLS 17.5: "A thread that can only see a reference to an object after that object has been completely initialized is guaranteed to see the correctly initialized values for that object's final fields." final 필드가 참조하는 객체·배열도 그 시점 버전이 보인다.
- 그래서 모든 필드가 `final`인 불변 객체는 `volatile` 없이 공유할 수 있다. DCL에서 이것을 쓰는 형태와 한 번만 읽어야 하는 함정은 [architecture/14 §7](../../architecture/14-cache-coherence-and-memory-ordering/2-summary.md), 패턴으로서의 DCL은 [16-concurrency-design-patterns](../16-concurrency-design-patterns/2-summary.md).

### 6. `long`·`double`은 반으로 찢길 수 있다 (명세상)

- JLS 17.7: non-volatile `long`·`double` 쓰기 하나를 32비트 두 번으로 다뤄도 된다. 다른 스레드가 위 32비트는 한 쓰기에서, 아래 32비트는 다른 쓰기에서 볼 수 있다. `volatile` `long`·`double`과 참조 읽기·쓰기는 항상 원자적이다.
- 구현이 64비트를 한 번에 써도 된다(명세가 구현에 맡김). 이 노트는 찢김을 실험하지 않았다. 64비트 HotSpot에서 실제로 찢기는지는 [?].

### 실험 2: C의 data race — TSan 보고와 `-O2` 무한 루프

```c
static int data; static int ready;            /* USE_ATOMIC이면 atomic_int + release/acquire */
static void *producer(void *arg) { data = 42; STORE(ready, 1); return NULL; }
int main(void) {
    pthread_create(&t, NULL, producer, NULL);
    while (!LOAD(ready)) ;                    /* 깃발을 기다린다 */
    printf("data=%d\n", (int)data);
}
```

호스트 gcc 13.3.0·clang 18.1.3, x86-64:

```text
  clang -O1 -g -fsanitize=thread (plain)
  WARNING: ThreadSanitizer: data race
    Read of size 1 at ... by main thread:        #0 main race.c
    Previous write of size 1 at ... by thread T1: #0 producer race.c:13:47
    Location is global 'ready' of size 1
  SUMMARY: ThreadSanitizer: data race race.c in main        exit=66 (data=42은 출력됨)
  clang -O1 -fsanitize=thread -DUSE_ATOMIC   → 보고 없음, exit=0

  gcc -O0 (plain)        → data=42, exit 0
  gcc -O2 (plain)        → timeout 3초 (exit 124), 3회 모두
  gcc -O2 -DUSE_ATOMIC   → data=42, exit 0

  gcc -O2 plain의 main (objdump -d)
    10eb: mov    0x2f23(%rip),%eax     # ready  ← 한 번만 읽는다
    10f1: test   %eax,%eax
    10f3: jne    1100 <main+0x40>
    10f5: jmp    10f5 <main+0x35>      ← 자기 자신으로 점프: 무한 루프
```

- 같은 소스가 `-O0`에서는 끝나고 `-O2`에서는 무한 루프였다. race가 UB이므로 컴파일러는 "다른 스레드가 `ready`를 바꾸지 않는다"고 보고 읽기를 루프 밖으로 뺐다. 이 컴파일러·옵션에서 관찰된 결과다.
- TSan은 race를 실행 중에 잡아 보고했다(exit 66). `ready`가 1바이트로 보고된 것은 clang `-O1`이 0·1만 저장되는 `int`를 1바이트로 줄인 결과라는 해석이다.
- 원자 변수 + release/acquire로 바꾸면 TSan 보고가 없고 `-O2`에서도 끝났다. Java 종료 플래그의 같은 현상(JIT 버전)은 [architecture/14 실험 2](../../architecture/14-cache-coherence-and-memory-ordering/2-summary.md).

## 쓰이는 자료구조·알고리즘

- **happens-before 부분 순서** — 동작이 정점, 프로그램 순서·synchronizes-with가 간선인 DAG의 추이적 폐포. 같은 변수에 대한 두 접근 중 적어도 하나가 쓰기(충돌 접근, JLS §17.4.1)인데 이 순서에서 비교 불가능하면 data race다(JLS §17.4.5). 읽기끼리는 race가 아니다. 그래프는 [data-structure/08-graph](../../data-structure/08-graph/2-summary.md), 도달 가능성(폐포)은 [algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md).
- **리트머스 테스트** — SB(저장 버퍼링), MP(메시지 전달) 같은 2~4줄 프로그램으로 모델이 허용하는 결과를 열거해 확인하는 방법(실험 1).
- **CAS·원자 변수** — 동기화 동작을 제공하는 기본 재료. 하드웨어 쪽은 [architecture/14 §6](../../architecture/14-cache-coherence-and-memory-ordering/2-summary.md), 자료구조는 [data-structure/29-concurrent-data-structures](../../data-structure/29-concurrent-data-structures/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 공유 변수마다 한 줄로 답한다

```text
  이 변수는 여러 스레드가 접근하나?
   ├─ 아니오 → 끝 (스레드 한정)
   └─ 예 → 쓰기가 있나?
        ├─ 없음(생성 후 불변) → 모든 필드 final로, 생성자에서 this를 흘리지 않는다
        └─ 있음 → 무엇으로 hb 간선을 만드나?
             ├─ 상태 플래그·설정 교체 하나       → volatile (또는 AtomicReference)
             ├─ 읽고-고치고-쓰기(카운터)          → Atomic*·LongAdder (volatile만으로는 유실 — architecture/14 실험 3)
             ├─ 여러 변수를 함께 바꾼다            → 락 (synchronized·ReentrantLock)
             └─ 성능 때문에 acquire/release      → SB 패턴이 없는지 증명할 수 있을 때만 (실험 1)
```

- `Thread.start()`·`join()`·`ExecutorService` 제출·`Future.get()`·동시성 컬렉션도 hb 간선을 만든다(앞의 둘은 JLS 17.4.4·17.4.5. 나머지는 `ExecutorService` API 문서의 "Memory consistency effects"와 `java.util.concurrent` 패키지 문서의 "Memory Consistency Properties" — 예: "Actions in a thread prior to placing an object into any concurrent collection happen-before actions subsequent to the access or removal of that element"). "그냥 스레드 풀에 넘기면 보인다"는 이 간선 덕이다.

### 2. 도구로 확인한다

```bash
# C/C++: 실행 중 race 탐지
clang -O1 -g -fsanitize=thread app.c && ./app
# Java: 바이트코드에서 volatile 표시 확인 (필드 플래그 ACC_VOLATILE)
javap -v -p Holder.class | grep -A2 "ready"
```

- 테스트가 통과했다고 race가 없는 것은 아니다. 실험 1에서도 모드별로 (0, 0)의 빈도가 실행마다 달랐다. Java는 OpenJDK jcstress 같은 동시성 테스트 하네스가 있다(이 노트에서는 쓰지 않음).
- ARM 같은 약한 순서 CPU는 x86보다 많은 재정렬을 허용한다. x86에서 통과한 race 코드가 다른 CPU에서 실패할 수 있다([architecture/14 장애 4](../../architecture/14-cache-coherence-and-memory-ordering/2-summary.md)).

## 장애 시나리오와 대처

### 1. ⚠ `volatile` 누락 → 종료 플래그를 못 봄

- **현상**: 종료 신호 뒤에도 워커가 끝나지 않아 배포가 멈춘다. C에서는 `-O2` 빌드만 멈춘다.
- **보이는 형태**: 스레드 덤프에서 워커가 같은 루프에 `RUNNABLE`. C는 objdump에서 자기 자신으로 점프하는 명령(실험 2 `jmp 10f5`).
- **원인**: 플래그 읽기와 쓰기 사이에 hb 간선이 없다(race). Java는 JIT가 읽기를 루프 밖으로 빼도 되고(JLS 17.3), C는 race 자체가 UB다.
- **대처**: Java `volatile boolean`·`AtomicBoolean`, C `atomic_int` + release/acquire. 인터럽트·`ExecutorService.shutdownNow` 같은 표준 취소 경로를 쓴다.

### 2. ⚠ DCL 부분 초기화 객체

- **현상**: 싱글턴 설정 객체의 필드가 드물게 0·`null`로 읽힌다.
- **원인**: 참조 공개가 생성자 안 쓰기보다 먼저 보일 수 있다(락 없이 읽는 첫 검사가 hb 간선 밖).
- **대처**: `volatile` 참조, 또는 모든 필드 `final` + 한 번만 읽기(5절), 또는 클래스 초기화를 쓰는 holder 관용구. 분석과 바이트코드는 [architecture/14 §7](../../architecture/14-cache-coherence-and-memory-ordering/2-summary.md), 패턴 선택은 [16-concurrency-design-patterns](../16-concurrency-design-patterns/2-summary.md).

### 3. acquire/release로 "최적화" → 상호 배제가 깨짐

- **현상**: `volatile`을 `setRelease`·`getAcquire`로 바꾼 뒤, 두 스레드가 동시에 임계 구역에 들어가는 일이 드물게 생긴다.
- **보이는 형태**: 재현이 드물고 부하·CPU에 따라 다르다. 리트머스로 보면 (0, 0)이 나온다(실험 1 acquire/release: 2백만 회 중 12만~35만).
- **원인**: "내 깃발을 세우고 상대 깃발을 본다"(Dekker·Peterson류)는 저장 → 읽기 순서가 필요하다. release/acquire는 이것을 약속하지 않는다(`VarHandle` 문서의 모드 정의).
- **대처**: volatile 또는 저장과 읽기 사이 `VarHandle.fullFence()`(실험 1 `fence` 0회). 직접 만든 상호 배제 대신 락을 쓴다.

### 4. C data race → 최적화 수준에 따라 다른 동작

- **현상**: 디버그 빌드는 되고 릴리스 빌드만 멈추거나 엉뚱한 값을 낸다.
- **보이는 형태**: TSan `WARNING: ThreadSanitizer: data race`(실험 2).
- **원인**: C11 5.1.2.4 ¶25 — race는 UB다. 컴파일러는 race가 없다고 가정하고 최적화한다.
- **대처**: 공유 변수는 `_Atomic`/`<stdatomic.h>` 또는 뮤텍스로. TSan을 CI 테스트에 건다. 같은 경계의 일반 UB 논의는 [20-undefined-behavior-and-memory-safety](../20-undefined-behavior-and-memory-safety/2-summary.md).

### 5. 공유 `long` 카운터·타임스탬프의 찢김 (명세상 허용)

- **현상(가능성)**: non-volatile `long` 필드를 여러 스레드가 쓰고 읽을 때 두 값의 반쪽이 섞인 값.
- **원인**: JLS 17.7은 non-volatile `long`·`double` 쓰기를 32비트 두 번으로 나눠도 된다고 허용한다.
- **대처**: `volatile long`·`AtomicLong`. 64비트 JVM에서 실제로 찢기는지는 구현에 달렸고 이 노트에서 확인하지 않았다 [?]. 명세에 기대지 않는 코드를 쓴다.

## 핵심 문장

- 언어 메모리 모델은 컴파일러·CPU의 재정렬 위에서 "어떤 결과가 가능한가"를 정한 계약이다. 프로그래머는 하드웨어 대신 이 계약을 본다.
- happens-before는 프로그램 순서와 synchronizes-with(락·volatile·start·join 등)의 추이적 폐포다. 실행 순서가 아니라 보임의 약속이다.
- data race가 없는 Java 프로그램은 순차 일관적으로 보인다(DRF-SC). C11은 race 없이 뮤텍스와 `memory_order_seq_cst`만 쓰는 프로그램에 같은 약속을 한다. race가 있어도 Java는 의미를 정의하지만, C11에서 race는 UB다.
- release/acquire는 메시지 전달에는 충분하지만 "쓰고 나서 남의 것을 읽는" 패턴은 막지 못한다. 그 순서는 volatile이나 전체 펜스만 약속한다.
- 모든 필드가 final인 불변 객체는 생성자 밖으로 this를 흘리지 않는 한 race로 넘겨도 올바르게 보인다.
- 테스트 통과는 race가 없다는 증거가 아니다. TSan·리트머스·명세로 확인한다.

## 관련 주제·근거

- 선행
  - [10-garbage-collection](../10-garbage-collection/2-summary.md) — 커리큘럼 선행(동시 GC의 장벽도 순서 문제다)
  - [architecture/14-cache-coherence-and-memory-ordering](../../architecture/14-cache-coherence-and-memory-ordering/2-summary.md) — MESI·저장 버퍼·배리어, Java 종료 플래그·갱신 유실·DCL 실험
- 후속·연결
  - [14-concurrency-models](../14-concurrency-models/2-summary.md) · [16-concurrency-design-patterns](../16-concurrency-design-patterns/2-summary.md)(DCL·불변 스냅샷 + 원자 참조 교체) · [20-undefined-behavior-and-memory-safety](../20-undefined-behavior-and-memory-safety/2-summary.md)
  - [os/15-race-conditions](../../os/15-race-conditions/2-summary.md) · [os/16-locks-and-spinlocks](../../os/16-locks-and-spinlocks/2-summary.md) · [data-structure/29-concurrent-data-structures](../../data-structure/29-concurrent-data-structures/2-summary.md)
  - [languages/java/syntax/33-synchronized-and-volatile](../../../languages/java/syntax/33-synchronized-and-volatile/2-summary.md) — 문법과 보장이 끝나는 자리, 분포로 본 실험
  - [languages/java/언어-특성 §9](../../../languages/java/언어-특성/README.md) — 메모리 모델의 위치
- 명세·논문
  - JLS SE21 17장 — 17.3 Sleep and Yield, 17.4.4 Synchronization Order(synchronizes-with 목록), 17.4.5 Happens-before Order(data race 정의, 올바른 동기화 ⇒ 순차 일관, "wrong length for an array"), 17.4.8 인과성, 17.5 final Field Semantics, 17.7 Non-Atomic Treatment of double and long <https://docs.oracle.com/javase/specs/jls/se21/html/jls-17.html>
  - Java API `VarHandle`(JDK 21) — 클래스 설명의 접근 모드(plain·opaque·acquire/release·volatile) 순서 효과 <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/invoke/VarHandle.html>
  - Manson, Pugh, Adve, "The Java Memory Model", POPL 2005 — DRF 프로그램에 순차 일관성 보장, 안전·보안 요구, Figure 2 Out Of Thin Air <https://rsim.cs.uiuc.edu/Pubs/popl05.pdf>
  - JSR-133 FAQ(Manson·Goetz) — volatile·final·DCL 문답 <https://www.cs.umd.edu/~pugh/java/memoryModel/jsr-133-faq.html>
  - C11 초안 N1570 5.1.2.4 Multi-threaded executions and data races — ¶25(race = UB), ¶26 NOTE 12(뮤텍스와 `memory_order_seq_cst`만 쓰는 race 없는 프로그램 ⇒ 순차 일관) <https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf>
  - Java API `ExecutorService`·`java.util.concurrent` 패키지 문서(JDK 21) — Memory consistency effects / Memory Consistency Properties <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/package-summary.html>
- 실험(호스트 i7-13700HX x86-64)
  - 실험 1: Java SB 리트머스 — `eclipse-temurin:21-jdk` 21.0.12, `--cpus=2 --network none`, 모드 5가지 × 2백만 회 × 3회 + 사실 점검 재실행 2회, plain `-Xint` 20만 회 1회 + 재실행 1회
  - 실험 2: C race — 호스트 clang 18.1.3 `-O1 -fsanitize=thread`(plain/atomic), gcc 13.3.0 `-O0`/`-O2`(plain, `timeout 3` 3회)/`-O2 -DUSE_ATOMIC`, `objdump -d`(사실 점검 재실행에서 exit 코드·objdump 주소까지 동일)
